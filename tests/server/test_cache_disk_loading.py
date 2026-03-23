# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Integration tests for disk-backed ResultCache loading — Story 17.7.

Covers:
- get_or_load() returns cached result when in cache
- get_or_load() loads from disk when not in cache
- get_or_load() returns None when neither cache nor disk has data
- Disk-loaded result is subsequently cached (second call hits cache)
- Result listing shows data_available=True for disk-backed runs
- API: GET /api/results/{run_id} returns data_available=True for disk-backed run
- API: GET /api/results/{run_id}/export/csv returns 200 for disk-backed run
- API: GET /api/results/{run_id}/export/parquet returns 200 for disk-backed run
- API: POST /api/indicators/distributional returns 200 for disk-backed run
- API: POST /api/comparison returns 200 for disk-backed runs
- API: GET /api/results listing shows data_available=True for disk-backed runs
"""

from __future__ import annotations

from pathlib import Path
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
    """Minimal PanelOutput with columns for all indicator types."""
    n = 100
    incomes = [10000.0 + i * 1000.0 + seed * 500.0 for i in range(n)]
    table = pa.table(
        {
            "household_id": pa.array(list(range(n)), type=pa.int64()),
            "year": pa.array([2025] * n, type=pa.int64()),
            "income": pa.array(incomes, type=pa.float64()),
            "disposable_income": pa.array(incomes, type=pa.float64()),
            "tax_revenue": pa.array([inc * 0.1 for inc in incomes], type=pa.float64()),
            "region_code": pa.array([f"R{i % 5}" for i in range(n)], type=pa.string()),
        }
    )
    return PanelOutput(
        table=table,
        metadata={"start_year": 2025, "end_year": 2025, "seed": seed},
    )


def _make_sim_result(panel: PanelOutput | None = None) -> SimulationResult:
    manifest = MagicMock()
    manifest.manifest_id = "manifest-disk-test"
    manifest.to_json.return_value = '{"manifest_id": "manifest-disk-test"}'
    return SimulationResult(
        success=True,
        scenario_id="sc-disk",
        yearly_states={},
        panel_output=panel or _make_panel(),
        manifest=manifest,
        metadata={},
    )


def _make_metadata(run_id: str) -> ResultMetadata:
    return ResultMetadata(
        run_id=run_id,
        timestamp="2026-03-08T00:00:00+00:00",
        run_kind="scenario",
        start_year=2025,
        end_year=2025,
        population_id=None,
        seed=42,
        row_count=100,
        manifest_id="manifest-disk-test",
        scenario_id="sc-disk",
        adapter_version="1.0.0",
        started_at="2026-03-08T00:00:00+00:00",
        finished_at="2026-03-08T00:00:05+00:00",
        status="completed",
        template_name="carbon_tax",
        portfolio_name=None,
        policy_type="carbon_tax",
    )


def _seed_disk_only(store: ResultStore, run_id: str, panel: PanelOutput | None = None) -> None:
    """Save metadata and panel to disk, but NOT to cache."""
    p = panel or _make_panel()
    store.save_metadata(run_id, _make_metadata(run_id))
    store.save_panel(run_id, p)
    # No manifest needed for basic disk loading tests


def _make_manifest_json() -> str:
    """Return a valid RunManifest JSON string for persistence tests."""
    from reformlab.governance.manifest import RunManifest

    manifest = RunManifest(
        manifest_id="manifest-disk-test",
        created_at="2026-03-08T00:00:00+00:00",
        engine_version="0.1.0",
        openfisca_version="44.0.0",
        adapter_version="1.0.0",
        scenario_version="1.0.0",
    )
    return manifest.to_json()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_store(tmp_path: Path) -> ResultStore:
    return ResultStore(base_dir=tmp_path)


@pytest.fixture()
def empty_cache() -> ResultCache:
    return ResultCache(max_size=20)


@pytest.fixture()
def client_with_deps(
    tmp_store: ResultStore,
    empty_cache: ResultCache,
) -> TestClient:
    """TestClient with ResultStore and ResultCache overridden."""
    from reformlab.server.app import create_app

    app = create_app()
    app.dependency_overrides[get_result_store] = lambda: tmp_store
    app.dependency_overrides[get_result_cache] = lambda: empty_cache
    return TestClient(app)


@pytest.fixture()
def auth_headers(client_with_deps: TestClient) -> dict[str, str]:
    response = client_with_deps.post(
        "/api/auth/login",
        json={"password": "test-password-123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


# ---------------------------------------------------------------------------
# get_or_load unit tests
# ---------------------------------------------------------------------------


class TestGetOrLoad:
    """ResultCache.get_or_load() behaviour."""

    def test_returns_cached_result_when_in_cache(
        self, tmp_store: ResultStore, empty_cache: ResultCache
    ) -> None:
        run_id = "cache-hit-run"
        sim_result = _make_sim_result()
        empty_cache.store(run_id, sim_result)
        result = empty_cache.get_or_load(run_id, tmp_store)
        assert result is sim_result

    def test_loads_from_disk_on_cache_miss(
        self, tmp_store: ResultStore, empty_cache: ResultCache
    ) -> None:
        run_id = "disk-load-run"
        _seed_disk_only(tmp_store, run_id)
        result = empty_cache.get_or_load(run_id, tmp_store)
        assert result is not None
        assert result.panel_output is not None

    def test_returns_none_when_no_cache_no_disk(
        self, tmp_store: ResultStore, empty_cache: ResultCache
    ) -> None:
        # metadata in store but no panel on disk
        tmp_store.save_metadata("no-panel", _make_metadata("no-panel"))
        result = empty_cache.get_or_load("no-panel", tmp_store)
        assert result is None

    def test_returns_none_when_unknown_run(
        self, tmp_store: ResultStore, empty_cache: ResultCache
    ) -> None:
        result = empty_cache.get_or_load("completely-unknown", tmp_store)
        assert result is None

    def test_disk_loaded_result_is_cached(
        self, tmp_store: ResultStore, empty_cache: ResultCache
    ) -> None:
        """After first disk load, second call should hit cache (not disk)."""
        run_id = "cache-after-disk"
        _seed_disk_only(tmp_store, run_id)
        first = empty_cache.get_or_load(run_id, tmp_store)
        # Delete the disk file to prove second call comes from cache
        (tmp_store._base_dir / run_id / "panel.parquet").unlink()
        second = empty_cache.get_or_load(run_id, tmp_store)
        assert first is second  # same object from cache

    def test_disk_loaded_result_has_panel(
        self, tmp_store: ResultStore, empty_cache: ResultCache
    ) -> None:
        run_id = "disk-panel-check"
        panel = _make_panel(seed=7)
        _seed_disk_only(tmp_store, run_id, panel)
        result = empty_cache.get_or_load(run_id, tmp_store)
        assert result is not None
        assert result.panel_output is not None
        assert result.panel_output.table.num_rows == panel.table.num_rows


# ---------------------------------------------------------------------------
# Listing shows data_available=True for disk-backed runs
# ---------------------------------------------------------------------------


class TestListingDiskAvailability:
    """data_available reflects disk presence, not just cache state."""

    def test_data_available_true_for_disk_backed_run(
        self, tmp_store: ResultStore, empty_cache: ResultCache
    ) -> None:
        """has_panel() should drive data_available in listing."""
        _seed_disk_only(tmp_store, "disk-run-1")
        assert tmp_store.has_panel("disk-run-1")

    def test_data_available_false_for_failed_run_with_no_panel(
        self, tmp_store: ResultStore
    ) -> None:
        tmp_store.save_metadata("failed-r", _make_metadata("failed-r"))
        assert not tmp_store.has_panel("failed-r")


# ---------------------------------------------------------------------------
# API integration tests — disk-backed results
# ---------------------------------------------------------------------------


class TestApiDiskBacked:
    """API endpoints return correct data for disk-backed runs (cache miss)."""

    def test_get_result_detail_data_available_true(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        run_id = "api-disk-detail"
        _seed_disk_only(tmp_store, run_id)
        response = client_with_deps.get(
            f"/api/results/{run_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["data_available"] is True

    def test_export_csv_returns_200_for_disk_backed_run(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        run_id = "api-disk-csv"
        _seed_disk_only(tmp_store, run_id)
        response = client_with_deps.get(
            f"/api/results/{run_id}/export/csv",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")

    def test_export_parquet_returns_200_for_disk_backed_run(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        run_id = "api-disk-parquet"
        _seed_disk_only(tmp_store, run_id)
        response = client_with_deps.get(
            f"/api/results/{run_id}/export/parquet",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "application/octet-stream" in response.headers.get("content-type", "")

    def test_distributional_indicator_returns_200_for_disk_backed_run(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        run_id = "api-disk-indicator"
        _seed_disk_only(tmp_store, run_id)
        response = client_with_deps.post(
            "/api/indicators/distributional",
            headers=auth_headers,
            json={"run_id": run_id},
        )
        assert response.status_code == 200

    def test_listing_shows_data_available_true_for_disk_backed_run(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        run_id = "api-disk-list"
        _seed_disk_only(tmp_store, run_id)
        response = client_with_deps.get("/api/results", headers=auth_headers)
        assert response.status_code == 200
        items = response.json()
        match = next((i for i in items if i["run_id"] == run_id), None)
        assert match is not None
        assert match["data_available"] is True

    def test_listing_shows_data_available_false_for_failed_run(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        run_id = "api-no-panel"
        tmp_store.save_metadata(run_id, _make_metadata(run_id))
        # No panel saved
        response = client_with_deps.get("/api/results", headers=auth_headers)
        assert response.status_code == 200
        items = response.json()
        match = next((i for i in items if i["run_id"] == run_id), None)
        assert match is not None
        assert match["data_available"] is False

    def test_comparison_returns_200_for_disk_backed_runs(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        """POST /api/comparison uses disk-backed results (welfare comparison)."""
        baseline_id = "api-disk-baseline"
        reform_id = "api-disk-reform"
        _seed_disk_only(tmp_store, baseline_id, _make_panel(seed=0))
        _seed_disk_only(tmp_store, reform_id, _make_panel(seed=1))
        response = client_with_deps.post(
            "/api/comparison",
            headers=auth_headers,
            json={
                "baseline_run_id": baseline_id,
                "reform_run_id": reform_id,
            },
        )
        assert response.status_code == 200
