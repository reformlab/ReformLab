# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for POST /api/comparison/portfolios — Story 17.4, AC-1, AC-2, AC-5.

Verifies:
- Valid 2-run and 3-run comparison returns correct response shape (AC-2)
- 404 when run_id not in ResultStore metadata (completely unknown)
- 409 when run_id in store but not in ResultCache (evicted)
- 409 when panel_output is None
- 422 when <2 or >5 run_ids provided (AC-1)
- 422 when duplicate run_ids provided (AC-1)
- 422 when derived label matches reserved column name
- Label deduplication when two runs share the same template_name
- Error response format (what/why/fix)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pyarrow as pa
import pytest
from fastapi.testclient import TestClient

from reformlab.interfaces.api import SimulationResult
from reformlab.orchestrator.panel import PanelOutput
from reformlab.server.dependencies import ResultCache, get_result_cache, get_result_store
from reformlab.server.result_store import ResultMetadata, ResultStore

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_panel(seed: int = 0) -> PanelOutput:
    """Create a minimal PanelOutput with 100 households and income data."""
    n = 100
    incomes = [10000.0 + i * 1000.0 + seed * 500.0 for i in range(n)]
    table = pa.table(
        {
            "household_id": pa.array(list(range(n)), type=pa.int64()),
            "year": pa.array([2025] * n, type=pa.int64()),
            "income": pa.array(incomes, type=pa.float64()),
            "disposable_income": pa.array(incomes, type=pa.float64()),
            "tax_revenue": pa.array([inc * 0.1 for inc in incomes], type=pa.float64()),
        }
    )
    return PanelOutput(table=table, metadata={"start_year": 2025, "end_year": 2025, "seed": seed})


def _make_sim_result(
    panel: PanelOutput | None = None,
) -> SimulationResult:
    """Build a minimal SimulationResult for injection into ResultCache."""
    if panel is None:
        panel = _make_panel()

    manifest = MagicMock()
    manifest.manifest_id = "manifest-test"

    return SimulationResult(
        success=True,
        scenario_id="sc-test",
        yearly_states={},
        panel_output=panel,
        manifest=manifest,
        metadata={},
    )


def _make_metadata(
    run_id: str,
    template_name: str | None = "carbon_tax",
    portfolio_name: str | None = None,
    run_kind: str = "scenario",
) -> ResultMetadata:
    return ResultMetadata(
        run_id=run_id,
        timestamp="2026-03-07T22:00:00+00:00",
        run_kind=run_kind,
        start_year=2025,
        end_year=2025,
        population_id=None,
        seed=42,
        row_count=100,
        manifest_id="manifest-001",
        scenario_id="sc-001",
        adapter_version="1.0.0",
        started_at="2026-03-07T22:00:00+00:00",
        finished_at="2026-03-07T22:00:05+00:00",
        status="completed",
        template_name=template_name,
        portfolio_name=portfolio_name,
        policy_type="carbon_tax" if run_kind == "scenario" else None,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_store(tmp_path: Path) -> ResultStore:
    """ResultStore backed by tmp_path — no pollution of ~/.reformlab."""
    return ResultStore(base_dir=tmp_path)


@pytest.fixture()
def populated_cache() -> ResultCache:
    """ResultCache pre-populated with test simulation results."""
    cache = ResultCache(max_size=20)
    cache.store("run-a", _make_sim_result(_make_panel(seed=0)))
    cache.store("run-b", _make_sim_result(_make_panel(seed=1)))
    cache.store("run-c", _make_sim_result(_make_panel(seed=2)))
    return cache


@pytest.fixture()
def client_with_store_and_cache(
    tmp_store: ResultStore,
    populated_cache: ResultCache,
) -> TestClient:
    """TestClient with both ResultStore and ResultCache overridden."""
    from reformlab.server.app import create_app

    app = create_app()
    app.dependency_overrides[get_result_store] = lambda: tmp_store
    app.dependency_overrides[get_result_cache] = lambda: populated_cache
    return TestClient(app)


@pytest.fixture()
def auth_headers(client_with_store_and_cache: TestClient) -> dict[str, str]:
    response = client_with_store_and_cache.post(
        "/api/auth/login",
        json={"password": "test-password-123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


def _seed_store_and_cache(
    store: ResultStore,
    cache: ResultCache,
    run_id: str,
    template_name: str | None = "carbon_tax",
    portfolio_name: str | None = None,
    run_kind: str = "scenario",
    with_panel: bool = True,
) -> None:
    """Add metadata to store and optionally a SimulationResult to cache."""
    store.save_metadata(
        run_id,
        _make_metadata(
            run_id,
            template_name=template_name,
            portfolio_name=portfolio_name,
            run_kind=run_kind,
        ),
    )
    if with_panel:
        cache.store(run_id, _make_sim_result(_make_panel()))


# ---------------------------------------------------------------------------
# AC-1 — Validation
# ---------------------------------------------------------------------------


class TestComparePortfoliosValidation:
    """AC-1: multi-run selection validation."""

    def test_fewer_than_2_run_ids_returns_422(
        self,
        client_with_store_and_cache: TestClient,
        tmp_store: ResultStore,
        populated_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        _seed_store_and_cache(tmp_store, populated_cache, "run-a")
        response = client_with_store_and_cache.post(
            "/api/comparison/portfolios",
            json={"run_ids": ["run-a"]},
            headers=auth_headers,
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert "what" in detail
        assert "why" in detail
        assert "fix" in detail

    def test_more_than_5_run_ids_returns_422(
        self,
        client_with_store_and_cache: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = client_with_store_and_cache.post(
            "/api/comparison/portfolios",
            json={"run_ids": ["a", "b", "c", "d", "e", "f"]},
            headers=auth_headers,
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert "what" in detail

    def test_empty_run_ids_returns_422(
        self,
        client_with_store_and_cache: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = client_with_store_and_cache.post(
            "/api/comparison/portfolios",
            json={"run_ids": []},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_duplicate_run_ids_returns_422(
        self,
        client_with_store_and_cache: TestClient,
        tmp_store: ResultStore,
        populated_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        _seed_store_and_cache(tmp_store, populated_cache, "run-dup")
        response = client_with_store_and_cache.post(
            "/api/comparison/portfolios",
            json={"run_ids": ["run-dup", "run-dup"]},
            headers=auth_headers,
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert "what" in detail
        assert "why" in detail
        assert "fix" in detail

    def test_baseline_run_id_not_in_run_ids_returns_422(
        self,
        client_with_store_and_cache: TestClient,
        tmp_store: ResultStore,
        populated_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        _seed_store_and_cache(tmp_store, populated_cache, "run-bl-a")
        _seed_store_and_cache(tmp_store, populated_cache, "run-bl-b")
        response = client_with_store_and_cache.post(
            "/api/comparison/portfolios",
            json={
                "run_ids": ["run-bl-a", "run-bl-b"],
                "baseline_run_id": "run-not-in-list",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert "what" in detail
        assert "baseline_run_id" in detail["what"]
        assert "why" in detail
        assert "fix" in detail

    def test_reserved_label_returns_422(
        self,
        client_with_store_and_cache: TestClient,
        tmp_store: ResultStore,
        populated_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        # "decile" is a reserved column name; if template_name is "decile"
        # the derived label will be "decile" and should be rejected
        _seed_store_and_cache(
            tmp_store, populated_cache, "run-reserved", template_name="decile"
        )
        _seed_store_and_cache(
            tmp_store, populated_cache, "run-ok", template_name="carbon_tax"
        )
        response = client_with_store_and_cache.post(
            "/api/comparison/portfolios",
            json={"run_ids": ["run-reserved", "run-ok"]},
            headers=auth_headers,
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert "what" in detail


# ---------------------------------------------------------------------------
# AC-2 — 404 / 409 error cases
# ---------------------------------------------------------------------------


class TestComparePortfoliosErrors:
    """Error cases: 404 for unknown run_id, 409 for evicted run."""

    def test_unknown_run_id_returns_404(
        self,
        client_with_store_and_cache: TestClient,
        tmp_store: ResultStore,
        populated_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        # Only register run-known, not run-unknown
        _seed_store_and_cache(tmp_store, populated_cache, "run-known")
        response = client_with_store_and_cache.post(
            "/api/comparison/portfolios",
            json={"run_ids": ["run-known", "run-unknown"]},
            headers=auth_headers,
        )
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert "what" in detail
        assert "why" in detail
        assert "fix" in detail

    def test_evicted_run_id_returns_409(
        self,
        client_with_store_and_cache: TestClient,
        tmp_store: ResultStore,
        populated_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        # Metadata in store but NOT in cache → evicted
        tmp_store.save_metadata("evicted", _make_metadata("evicted"))
        _seed_store_and_cache(tmp_store, populated_cache, "run-live")
        response = client_with_store_and_cache.post(
            "/api/comparison/portfolios",
            json={"run_ids": ["run-live", "evicted"]},
            headers=auth_headers,
        )
        assert response.status_code == 409
        detail = response.json()["detail"]
        assert "what" in detail
        assert "why" in detail
        assert "fix" in detail

    def test_run_with_none_panel_output_returns_409(
        self,
        client_with_store_and_cache: TestClient,
        tmp_store: ResultStore,
        populated_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        # Store a SimulationResult with panel_output=None
        manifest = MagicMock()
        manifest.manifest_id = "manifest-no-panel"
        no_panel_result = SimulationResult(
            success=False,
            scenario_id="sc-no-panel",
            yearly_states={},
            panel_output=None,
            manifest=manifest,
            metadata={},
        )
        tmp_store.save_metadata("no-panel", _make_metadata("no-panel"))
        populated_cache.store("no-panel", no_panel_result)
        _seed_store_and_cache(tmp_store, populated_cache, "run-live-2")

        response = client_with_store_and_cache.post(
            "/api/comparison/portfolios",
            json={"run_ids": ["run-live-2", "no-panel"]},
            headers=auth_headers,
        )
        assert response.status_code == 409
        detail = response.json()["detail"]
        assert "what" in detail


# ---------------------------------------------------------------------------
# AC-2, AC-5 — Success cases
# ---------------------------------------------------------------------------


class TestComparePortfoliosSuccess:
    """Success cases: 2-run and 3-run comparison response shape."""

    def test_2_run_comparison_returns_200(
        self,
        client_with_store_and_cache: TestClient,
        tmp_store: ResultStore,
        populated_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        _seed_store_and_cache(
            tmp_store, populated_cache, "run-a2", template_name="Green Transition"
        )
        _seed_store_and_cache(
            tmp_store, populated_cache, "run-b2", template_name="Carbon Floor"
        )
        response = client_with_store_and_cache.post(
            "/api/comparison/portfolios",
            json={"run_ids": ["run-a2", "run-b2"]},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        assert "comparisons" in data
        assert "cross_metrics" in data
        assert "portfolio_labels" in data
        assert "metadata" in data
        assert "warnings" in data

    def test_response_has_correct_portfolio_labels(
        self,
        client_with_store_and_cache: TestClient,
        tmp_store: ResultStore,
        populated_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        _seed_store_and_cache(
            tmp_store, populated_cache, "run-label-a", template_name="Alpha"
        )
        _seed_store_and_cache(
            tmp_store, populated_cache, "run-label-b", template_name="Beta"
        )
        response = client_with_store_and_cache.post(
            "/api/comparison/portfolios",
            json={"run_ids": ["run-label-a", "run-label-b"]},
            headers=auth_headers,
        )
        assert response.status_code == 200
        labels = response.json()["portfolio_labels"]
        assert "Alpha" in labels
        assert "Beta" in labels

    def test_2_run_comparison_has_distributional_data(
        self,
        client_with_store_and_cache: TestClient,
        tmp_store: ResultStore,
        populated_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        _seed_store_and_cache(tmp_store, populated_cache, "run-dist-a", template_name="Policy A")
        _seed_store_and_cache(tmp_store, populated_cache, "run-dist-b", template_name="Policy B")
        response = client_with_store_and_cache.post(
            "/api/comparison/portfolios",
            json={"run_ids": ["run-dist-a", "run-dist-b"], "include_welfare": False},
            headers=auth_headers,
        )
        assert response.status_code == 200
        comparisons = response.json()["comparisons"]
        assert "distributional" in comparisons
        dist = comparisons["distributional"]
        assert "columns" in dist
        assert "data" in dist
        assert isinstance(dist["columns"], list)
        assert isinstance(dist["data"], dict)

    def test_3_run_comparison_returns_200(
        self,
        client_with_store_and_cache: TestClient,
        tmp_store: ResultStore,
        populated_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        for label in ["run-3a", "run-3b", "run-3c"]:
            policy_name = f"Policy {label[-1].upper()}"
            _seed_store_and_cache(tmp_store, populated_cache, label, template_name=policy_name)
        response = client_with_store_and_cache.post(
            "/api/comparison/portfolios",
            json={"run_ids": ["run-3a", "run-3b", "run-3c"], "include_welfare": False},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["portfolio_labels"]) == 3

    def test_cross_metrics_returned(
        self,
        client_with_store_and_cache: TestClient,
        tmp_store: ResultStore,
        populated_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        _seed_store_and_cache(tmp_store, populated_cache, "run-cm-a", template_name="High Tax")
        _seed_store_and_cache(tmp_store, populated_cache, "run-cm-b", template_name="Low Tax")
        response = client_with_store_and_cache.post(
            "/api/comparison/portfolios",
            json={"run_ids": ["run-cm-a", "run-cm-b"], "include_welfare": False},
            headers=auth_headers,
        )
        assert response.status_code == 200
        cross_metrics = response.json()["cross_metrics"]
        assert isinstance(cross_metrics, list)
        # Fiscal cross-metrics should be present when fiscal indicators are computed
        for metric in cross_metrics:
            assert "criterion" in metric
            assert "best_portfolio" in metric
            assert "value" in metric
            assert "all_values" in metric

    def test_label_deduplication_when_same_template_name(
        self,
        client_with_store_and_cache: TestClient,
        tmp_store: ResultStore,
        populated_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        # Both runs derive the same template_name label — dedup should append _2
        _seed_store_and_cache(
            tmp_store, populated_cache, "run-dup-a", template_name="Carbon Tax"
        )
        _seed_store_and_cache(
            tmp_store, populated_cache, "run-dup-b", template_name="Carbon Tax"
        )
        response = client_with_store_and_cache.post(
            "/api/comparison/portfolios",
            json={"run_ids": ["run-dup-a", "run-dup-b"]},
            headers=auth_headers,
        )
        assert response.status_code == 200
        labels = response.json()["portfolio_labels"]
        assert len(set(labels)) == 2  # deduplication produced unique labels

    def test_portfolio_name_preferred_over_template_name(
        self,
        client_with_store_and_cache: TestClient,
        tmp_store: ResultStore,
        populated_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        _seed_store_and_cache(
            tmp_store,
            populated_cache,
            "run-port-a",
            portfolio_name="Green Portfolio",
            run_kind="portfolio",
            template_name=None,
        )
        _seed_store_and_cache(
            tmp_store, populated_cache, "run-port-b", template_name="Other Policy"
        )
        response = client_with_store_and_cache.post(
            "/api/comparison/portfolios",
            json={"run_ids": ["run-port-a", "run-port-b"]},
            headers=auth_headers,
        )
        assert response.status_code == 200
        labels = response.json()["portfolio_labels"]
        assert "Green Portfolio" in labels

    def test_unauthenticated_returns_401(
        self,
        client_with_store_and_cache: TestClient,
    ) -> None:
        response = client_with_store_and_cache.post(
            "/api/comparison/portfolios",
            json={"run_ids": ["run-a", "run-b"]},
        )
        assert response.status_code == 401
