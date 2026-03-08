"""Integration tests for indicator and comparison endpoints — Story 17.6.

Covers AC-1 (success + error paths), AC-2 (what/why/fix error format),
AC-3 (store/cache two-step lookup) for:
  - POST /api/indicators/{type}    (distributional, geographic, fiscal, welfare)
  - POST /api/comparison           (pairwise welfare comparison)
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
    """Minimal PanelOutput with columns for all indicator types.

    Column naming follows GeographicConfig defaults (region_code)
    and fiscal auto-detection (_revenue suffix → tax_revenue).
    """
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
    return PanelOutput(table=table, metadata={"start_year": 2025, "end_year": 2025, "seed": seed})


def _make_sim_result(panel: PanelOutput | None = None) -> SimulationResult:
    manifest = MagicMock()
    manifest.manifest_id = "manifest-test"
    return SimulationResult(
        success=True,
        scenario_id="sc-test",
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
        manifest_id="manifest-001",
        scenario_id="sc-001",
        adapter_version="1.0.0",
        started_at="2026-03-08T00:00:00+00:00",
        finished_at="2026-03-08T00:00:05+00:00",
        status="completed",
        template_name="carbon_tax",
        portfolio_name=None,
        policy_type="carbon_tax",
    )


def _seed(
    store: ResultStore,
    cache: ResultCache,
    run_id: str,
    panel: PanelOutput | None = None,
    in_cache: bool = True,
) -> None:
    """Add metadata to store and optionally a result to cache."""
    store.save_metadata(run_id, _make_metadata(run_id))
    if in_cache:
        cache.store(run_id, _make_sim_result(panel))


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
# AC-1, AC-2, AC-3: Distributional indicator tests
# ---------------------------------------------------------------------------


class TestIndicatorDistributional:
    """POST /api/indicators/distributional — success + option paths."""

    def test_success_returns_200_with_data(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        _seed(tmp_store, empty_cache, "run-dist-01")
        response = client_with_deps.post(
            "/api/indicators/distributional",
            headers=auth_headers,
            json={"run_id": "run-dist-01"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["indicator_type"] == "distributional"
        assert isinstance(data["data"], dict)
        assert "metadata" in data

    def test_by_year_param_accepted(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        _seed(tmp_store, empty_cache, "run-dist-02")
        response = client_with_deps.post(
            "/api/indicators/distributional",
            headers=auth_headers,
            json={"run_id": "run-dist-02", "by_year": True},
        )
        assert response.status_code == 200

    def test_custom_income_field_accepted(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        _seed(tmp_store, empty_cache, "run-dist-03")
        response = client_with_deps.post(
            "/api/indicators/distributional",
            headers=auth_headers,
            json={"run_id": "run-dist-03", "income_field": "disposable_income"},
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# AC-1, AC-2, AC-3: Geographic indicator tests
# ---------------------------------------------------------------------------


class TestIndicatorGeographic:
    """POST /api/indicators/geographic — success + option paths."""

    def test_success_returns_200_with_data(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        _seed(tmp_store, empty_cache, "run-geo-01")
        response = client_with_deps.post(
            "/api/indicators/geographic",
            headers=auth_headers,
            json={"run_id": "run-geo-01"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["indicator_type"] == "geographic"
        assert isinstance(data["data"], dict)

    def test_by_year_param_accepted(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        _seed(tmp_store, empty_cache, "run-geo-02")
        response = client_with_deps.post(
            "/api/indicators/geographic",
            headers=auth_headers,
            json={"run_id": "run-geo-02", "by_year": True},
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# AC-1, AC-2, AC-3: Fiscal indicator tests
# ---------------------------------------------------------------------------


class TestIndicatorFiscal:
    """POST /api/indicators/fiscal — success + option paths."""

    def test_success_returns_200_with_data(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        _seed(tmp_store, empty_cache, "run-fisc-01")
        response = client_with_deps.post(
            "/api/indicators/fiscal",
            headers=auth_headers,
            json={"run_id": "run-fisc-01"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["indicator_type"] == "fiscal"
        assert isinstance(data["data"], dict)

    def test_by_year_param_accepted(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        _seed(tmp_store, empty_cache, "run-fisc-02")
        response = client_with_deps.post(
            "/api/indicators/fiscal",
            headers=auth_headers,
            json={"run_id": "run-fisc-02", "by_year": True},
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# AC-1, AC-2, AC-3: Welfare indicator store/cache error path tests
# Note: POST /api/indicators/welfare with a single run_id is an infrastructure
# test only — the underlying welfare indicator requires a reform panel and will
# error at the computation layer. Pairwise welfare success is tested in
# TestPairwiseComparison below (POST /api/comparison).
# ---------------------------------------------------------------------------


class TestIndicatorWelfare:
    """POST /api/indicators/welfare — store/cache error paths (AC-2, AC-3)."""

    def test_unknown_run_id_returns_404_with_structured_error(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = client_with_deps.post(
            "/api/indicators/welfare",
            headers=auth_headers,
            json={"run_id": "no-such-run"},
        )
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert set(detail.keys()) >= {"what", "why", "fix"}

    def test_evicted_run_returns_409_with_structured_error(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        # Metadata in store but nothing in cache
        tmp_store.save_metadata("evicted-welfare", _make_metadata("evicted-welfare"))
        response = client_with_deps.post(
            "/api/indicators/welfare",
            headers=auth_headers,
            json={"run_id": "evicted-welfare"},
        )
        assert response.status_code == 409
        detail = response.json()["detail"]
        assert set(detail.keys()) >= {"what", "why", "fix"}


# ---------------------------------------------------------------------------
# AC-1, AC-2, AC-3: General error tests
# ---------------------------------------------------------------------------


class TestIndicatorErrors:
    """Error paths: invalid type (422), unknown run (404), evicted run (409)."""

    def test_invalid_type_returns_422_with_structured_error(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = client_with_deps.post(
            "/api/indicators/bogus_type",
            headers=auth_headers,
            json={"run_id": "any-run"},
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert set(detail.keys()) >= {"what", "why", "fix"}

    def test_unknown_run_id_returns_404_with_structured_error(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = client_with_deps.post(
            "/api/indicators/distributional",
            headers=auth_headers,
            json={"run_id": "completely-unknown"},
        )
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert set(detail.keys()) >= {"what", "why", "fix"}

    def test_evicted_run_returns_409_with_structured_error(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        # Metadata in store but no cache entry
        tmp_store.save_metadata("evicted-dist", _make_metadata("evicted-dist"))
        response = client_with_deps.post(
            "/api/indicators/distributional",
            headers=auth_headers,
            json={"run_id": "evicted-dist"},
        )
        assert response.status_code == 409
        detail = response.json()["detail"]
        assert set(detail.keys()) >= {"what", "why", "fix"}


# ---------------------------------------------------------------------------
# AC-1, AC-2, AC-3: Pairwise welfare comparison tests
# ---------------------------------------------------------------------------


class TestPairwiseComparison:
    """POST /api/comparison — welfare comparison between baseline and reform."""

    def test_success_returns_200_with_welfare_data(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        _seed(tmp_store, empty_cache, "baseline-01", panel=_make_panel(seed=0))
        _seed(tmp_store, empty_cache, "reform-01", panel=_make_panel(seed=1))
        response = client_with_deps.post(
            "/api/comparison",
            headers=auth_headers,
            json={"baseline_run_id": "baseline-01", "reform_run_id": "reform-01"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["indicator_type"] == "welfare"
        assert isinstance(data["data"], dict)

    def test_baseline_not_found_returns_404(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        _seed(tmp_store, empty_cache, "reform-02")
        response = client_with_deps.post(
            "/api/comparison",
            headers=auth_headers,
            json={"baseline_run_id": "no-such-baseline", "reform_run_id": "reform-02"},
        )
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert set(detail.keys()) >= {"what", "why", "fix"}

    def test_reform_not_found_returns_404(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        _seed(tmp_store, empty_cache, "baseline-03")
        response = client_with_deps.post(
            "/api/comparison",
            headers=auth_headers,
            json={"baseline_run_id": "baseline-03", "reform_run_id": "no-such-reform"},
        )
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert set(detail.keys()) >= {"what", "why", "fix"}

    def test_evicted_baseline_returns_409(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        # Baseline in store but not in cache
        tmp_store.save_metadata("evicted-base", _make_metadata("evicted-base"))
        _seed(tmp_store, empty_cache, "reform-04")
        response = client_with_deps.post(
            "/api/comparison",
            headers=auth_headers,
            json={"baseline_run_id": "evicted-base", "reform_run_id": "reform-04"},
        )
        assert response.status_code == 409
        detail = response.json()["detail"]
        assert set(detail.keys()) >= {"what", "why", "fix"}

    def test_evicted_reform_returns_409(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        _seed(tmp_store, empty_cache, "baseline-05")
        # Reform in store but not in cache
        tmp_store.save_metadata("evicted-reform", _make_metadata("evicted-reform"))
        response = client_with_deps.post(
            "/api/comparison",
            headers=auth_headers,
            json={"baseline_run_id": "baseline-05", "reform_run_id": "evicted-reform"},
        )
        assert response.status_code == 409
        detail = response.json()["detail"]
        assert set(detail.keys()) >= {"what", "why", "fix"}
