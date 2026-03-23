# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Integration tests for export endpoints — Story 17.6.

Covers AC-1 (success + error paths), AC-2 (what/why/fix error format),
AC-3 (store/cache two-step lookup) for:
  - POST /api/exports/csv
  - POST /api/exports/parquet
  - GET  /api/results/{run_id}/export/csv
  - GET  /api/results/{run_id}/export/parquet
"""

from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import MagicMock

import pyarrow as pa
import pyarrow.parquet as pq
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
    """Minimal PanelOutput for export tests."""
    n = 50
    incomes = [10000.0 + i * 500.0 + seed * 100.0 for i in range(n)]
    table = pa.table(
        {
            "household_id": pa.array(list(range(n)), type=pa.int64()),
            "year": pa.array([2025] * n, type=pa.int64()),
            "income": pa.array(incomes, type=pa.float64()),
            "disposable_income": pa.array(incomes, type=pa.float64()),
            "tax_revenue": pa.array([inc * 0.1 for inc in incomes], type=pa.float64()),
            "region": pa.array([f"R{i % 3}" for i in range(n)], type=pa.string()),
        }
    )
    return PanelOutput(table=table, metadata={"start_year": 2025, "end_year": 2025})


def _make_sim_result(panel: PanelOutput | None = None) -> SimulationResult:
    manifest = MagicMock()
    manifest.manifest_id = "manifest-export-test"
    return SimulationResult(
        success=True,
        scenario_id="sc-export",
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
        row_count=50,
        manifest_id="manifest-export",
        scenario_id="sc-export",
        adapter_version="1.0.0",
        started_at="2026-03-08T00:00:00+00:00",
        finished_at="2026-03-08T00:00:03+00:00",
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
# POST /api/exports/csv
# ---------------------------------------------------------------------------


class TestExportCsvSuccess:
    """POST /api/exports/csv — success path with content validation."""

    def test_returns_200_with_csv_content_type(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        _seed(tmp_store, empty_cache, "export-csv-01")
        response = client_with_deps.post(
            "/api/exports/csv",
            headers=auth_headers,
            json={"run_id": "export-csv-01"},
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")

    def test_response_has_content_disposition_header(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        _seed(tmp_store, empty_cache, "export-csv-02")
        response = client_with_deps.post(
            "/api/exports/csv",
            headers=auth_headers,
            json={"run_id": "export-csv-02"},
        )
        assert response.status_code == 200
        disposition = response.headers.get("content-disposition", "")
        assert "attachment" in disposition
        assert ".csv" in disposition

    def test_csv_body_is_parseable_with_correct_columns(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        _seed(tmp_store, empty_cache, "export-csv-03")
        response = client_with_deps.post(
            "/api/exports/csv",
            headers=auth_headers,
            json={"run_id": "export-csv-03"},
        )
        assert response.status_code == 200
        # Parse CSV body — first line is headers
        lines = response.content.decode("utf-8").splitlines()
        assert len(lines) >= 2  # header + at least one data row
        headers_line = lines[0]
        assert "household_id" in headers_line
        assert "income" in headers_line


# ---------------------------------------------------------------------------
# POST /api/exports/parquet
# ---------------------------------------------------------------------------


class TestExportParquetSuccess:
    """POST /api/exports/parquet — success path with content validation."""

    def test_returns_200_with_octet_stream_content_type(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        _seed(tmp_store, empty_cache, "export-pq-01")
        response = client_with_deps.post(
            "/api/exports/parquet",
            headers=auth_headers,
            json={"run_id": "export-pq-01"},
        )
        assert response.status_code == 200
        assert "application/octet-stream" in response.headers.get("content-type", "")

    def test_response_has_content_disposition_header(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        _seed(tmp_store, empty_cache, "export-pq-02")
        response = client_with_deps.post(
            "/api/exports/parquet",
            headers=auth_headers,
            json={"run_id": "export-pq-02"},
        )
        assert response.status_code == 200
        disposition = response.headers.get("content-disposition", "")
        assert "attachment" in disposition
        assert ".parquet" in disposition

    def test_parquet_body_is_readable_by_pyarrow(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        _seed(tmp_store, empty_cache, "export-pq-03")
        response = client_with_deps.post(
            "/api/exports/parquet",
            headers=auth_headers,
            json={"run_id": "export-pq-03"},
        )
        assert response.status_code == 200
        table = pq.read_table(io.BytesIO(response.content))
        assert "household_id" in table.schema.names
        assert "income" in table.schema.names
        assert table.num_rows == 50


# ---------------------------------------------------------------------------
# POST /api/exports/* — error paths
# ---------------------------------------------------------------------------


class TestExportErrors:
    """POST /api/exports/* — 404 (unknown) and 409 (evicted) error paths."""

    def test_unknown_run_id_csv_returns_404_with_structured_error(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = client_with_deps.post(
            "/api/exports/csv",
            headers=auth_headers,
            json={"run_id": "no-such-run"},
        )
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert set(detail.keys()) >= {"what", "why", "fix"}

    def test_unknown_run_id_parquet_returns_404_with_structured_error(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = client_with_deps.post(
            "/api/exports/parquet",
            headers=auth_headers,
            json={"run_id": "no-such-run"},
        )
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert set(detail.keys()) >= {"what", "why", "fix"}

    def test_evicted_run_csv_returns_409_with_structured_error(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        # Metadata in store, but not in cache
        tmp_store.save_metadata("evicted-csv", _make_metadata("evicted-csv"))
        response = client_with_deps.post(
            "/api/exports/csv",
            headers=auth_headers,
            json={"run_id": "evicted-csv"},
        )
        assert response.status_code == 409
        detail = response.json()["detail"]
        assert set(detail.keys()) >= {"what", "why", "fix"}

    def test_evicted_run_parquet_returns_409_with_structured_error(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        tmp_store.save_metadata("evicted-pq", _make_metadata("evicted-pq"))
        response = client_with_deps.post(
            "/api/exports/parquet",
            headers=auth_headers,
            json={"run_id": "evicted-pq"},
        )
        assert response.status_code == 409
        detail = response.json()["detail"]
        assert set(detail.keys()) >= {"what", "why", "fix"}


# ---------------------------------------------------------------------------
# GET /api/results/{run_id}/export/csv
# ---------------------------------------------------------------------------


class TestResultExportCsv:
    """GET /api/results/{run_id}/export/csv — success path."""

    def test_success_returns_200_with_csv_content(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        _seed(tmp_store, empty_cache, "res-csv-01")
        response = client_with_deps.get(
            "/api/results/res-csv-01/export/csv",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        lines = response.content.decode("utf-8").splitlines()
        assert len(lines) >= 2


# ---------------------------------------------------------------------------
# GET /api/results/{run_id}/export/parquet
# ---------------------------------------------------------------------------


class TestResultExportParquet:
    """GET /api/results/{run_id}/export/parquet — success path."""

    def test_success_returns_200_with_parquet_content(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        _seed(tmp_store, empty_cache, "res-pq-01")
        response = client_with_deps.get(
            "/api/results/res-pq-01/export/parquet",
            headers=auth_headers,
        )
        assert response.status_code == 200
        table = pq.read_table(io.BytesIO(response.content))
        assert table.num_rows == 50


# ---------------------------------------------------------------------------
# GET /api/results/{run_id}/export/* — error paths
# ---------------------------------------------------------------------------


class TestResultExportErrors:
    """GET /api/results/{run_id}/export/* — 404 and 409 error paths."""

    def test_unknown_run_returns_404(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = client_with_deps.get(
            "/api/results/unknown-res/export/csv",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_evicted_run_returns_409(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        empty_cache: ResultCache,
    ) -> None:
        tmp_store.save_metadata("evicted-res", _make_metadata("evicted-res"))
        response = client_with_deps.get(
            "/api/results/evicted-res/export/csv",
            headers=auth_headers,
        )
        assert response.status_code == 409
