# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for the results API routes — Story 17.3, AC-2, AC-3, AC-4.

Verifies:
- GET /api/results — list all saved results
- GET /api/results/{run_id} — detail view (metadata + cache enrichment)
- DELETE /api/results/{run_id} — remove result
- GET /api/results/{run_id}/export/csv — 200 with cached result, 409 without
- GET /api/results/{run_id}/export/parquet — 200 with cached result, 409 without
- 404 for unknown run_ids
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from reformlab.server.result_store import ResultMetadata, ResultStore

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_metadata(
    run_id: str = "run-001",
    status: str = "completed",
    timestamp: str = "2026-03-07T22:00:00+00:00",
    row_count: int = 1000,
    run_kind: str = "scenario",
) -> ResultMetadata:
    return ResultMetadata(
        run_id=run_id,
        timestamp=timestamp,
        run_kind=run_kind,
        start_year=2025,
        end_year=2030,
        population_id="fr-synthetic-2024",
        seed=42,
        row_count=row_count,
        manifest_id="manifest-001" if status == "completed" else "",
        scenario_id="scenario-001" if status == "completed" else "",
        adapter_version="1.0.0" if status == "completed" else "unknown",
        started_at="2026-03-07T22:00:00+00:00",
        finished_at="2026-03-07T22:00:05+00:00",
        status=status,
        template_name="Carbon Tax" if run_kind == "scenario" else None,
        policy_type="carbon_tax" if run_kind == "scenario" else None,
        portfolio_name="green-transition" if run_kind == "portfolio" else None,
    )


@pytest.fixture()
def tmp_store(tmp_path: Path) -> ResultStore:
    """ResultStore backed by tmp_path (no pollution of real ~/.reformlab)."""
    return ResultStore(base_dir=tmp_path)


@pytest.fixture()
def client_with_store(tmp_store: ResultStore) -> TestClient:
    """TestClient with ResultStore dependency overridden to use tmp_path."""
    from reformlab.server.app import create_app
    from reformlab.server.dependencies import get_result_store

    app = create_app()
    app.dependency_overrides[get_result_store] = lambda: tmp_store
    return TestClient(app)


@pytest.fixture()
def auth_headers(client_with_store: TestClient) -> dict[str, str]:
    response = client_with_store.post(
        "/api/auth/login",
        json={"password": "test-password-123"},
    )
    assert response.status_code == 200
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# GET /api/results
# ---------------------------------------------------------------------------


class TestListResults:
    """AC-3: persistent results listing."""

    def test_empty_store_returns_empty_list(
        self, client_with_store: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client_with_store.get("/api/results", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_single_result_returned(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
    ) -> None:
        tmp_store.save_metadata("run-001", _make_metadata("run-001"))
        response = client_with_store.get("/api/results", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["run_id"] == "run-001"
        assert data[0]["status"] == "completed"

    def test_multiple_results_sorted_newest_first(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
    ) -> None:
        tmp_store.save_metadata("run-old", _make_metadata("run-old", timestamp="2026-03-06T10:00:00+00:00"))
        tmp_store.save_metadata("run-new", _make_metadata("run-new", timestamp="2026-03-07T10:00:00+00:00"))
        response = client_with_store.get("/api/results", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["run_id"] == "run-new"
        assert data[1]["run_id"] == "run-old"

    def test_data_available_false_when_not_in_cache(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
    ) -> None:
        tmp_store.save_metadata("evicted-run", _make_metadata("evicted-run"))
        response = client_with_store.get("/api/results", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data[0]["data_available"] is False

    def test_failed_run_appears_in_list(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
    ) -> None:
        tmp_store.save_metadata(
            "failed-run",
            _make_metadata("failed-run", status="failed", row_count=0),
        )
        response = client_with_store.get("/api/results", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "failed"
        assert data[0]["row_count"] == 0

    def test_response_shape_includes_required_fields(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
    ) -> None:
        tmp_store.save_metadata("run-shape", _make_metadata("run-shape"))
        response = client_with_store.get("/api/results", headers=auth_headers)
        item = response.json()[0]
        for field in [
            "run_id", "timestamp", "run_kind", "start_year", "end_year",
            "row_count", "status", "data_available",
        ]:
            assert field in item, f"Missing field: {field}"

    def test_unauthenticated_returns_401(self, client_with_store: TestClient) -> None:
        response = client_with_store.get("/api/results")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/results/{run_id}
# ---------------------------------------------------------------------------


class TestGetResult:
    """AC-4: run detail view."""

    def test_get_existing_result_metadata_only(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
    ) -> None:
        tmp_store.save_metadata("detail-run", _make_metadata("detail-run"))
        response = client_with_store.get("/api/results/detail-run", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["run_id"] == "detail-run"
        assert data["data_available"] is False
        assert data["indicators"] is None
        assert data["columns"] is None
        assert data["column_count"] is None

    def test_get_unknown_run_returns_404(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = client_with_store.get("/api/results/nonexistent", headers=auth_headers)
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert "what" in detail
        assert "why" in detail
        assert "fix" in detail

    def test_detail_includes_all_metadata_fields(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
    ) -> None:
        tmp_store.save_metadata("full-run", _make_metadata("full-run"))
        response = client_with_store.get("/api/results/full-run", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        for field in [
            "run_id", "timestamp", "run_kind", "start_year", "end_year",
            "population_id", "seed", "row_count", "manifest_id", "scenario_id",
            "adapter_version", "started_at", "finished_at", "status", "data_available",
        ]:
            assert field in data, f"Missing field: {field}"

    def test_portfolio_run_detail(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
    ) -> None:
        tmp_store.save_metadata(
            "port-run",
            _make_metadata("port-run", run_kind="portfolio"),
        )
        response = client_with_store.get("/api/results/port-run", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["run_kind"] == "portfolio"
        assert data["portfolio_name"] == "green-transition"
        assert data["template_name"] is None


# ---------------------------------------------------------------------------
# DELETE /api/results/{run_id}
# ---------------------------------------------------------------------------


class TestDeleteResult:
    """DELETE /api/results/{run_id}."""

    def test_delete_existing_result(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
    ) -> None:
        tmp_store.save_metadata("to-delete", _make_metadata("to-delete"))
        response = client_with_store.delete("/api/results/to-delete", headers=auth_headers)
        assert response.status_code == 204

    def test_delete_removes_from_store(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
    ) -> None:
        tmp_store.save_metadata("gone", _make_metadata("gone"))
        client_with_store.delete("/api/results/gone", headers=auth_headers)
        # Should now be missing
        response = client_with_store.get("/api/results/gone", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_unknown_run_returns_404(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = client_with_store.delete("/api/results/nonexistent", headers=auth_headers)
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/results/{run_id}/export/csv
# ---------------------------------------------------------------------------


class TestExportCsv:
    """Export CSV endpoint: 200 when cached, 409 when evicted, 404 when unknown."""

    def test_csv_export_unknown_run_returns_404(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = client_with_store.get("/api/results/unknown/export/csv", headers=auth_headers)
        assert response.status_code == 404

    def test_csv_export_evicted_result_returns_409(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
    ) -> None:
        # Save metadata but don't put result in cache
        tmp_store.save_metadata("evicted", _make_metadata("evicted"))
        response = client_with_store.get("/api/results/evicted/export/csv", headers=auth_headers)
        assert response.status_code == 409
        detail = response.json()["detail"]
        assert "what" in detail
        assert "fix" in detail


# ---------------------------------------------------------------------------
# GET /api/results/{run_id}/export/parquet
# ---------------------------------------------------------------------------


class TestExportParquet:
    """Export Parquet endpoint: 200 when cached, 409 when evicted, 404 when unknown."""

    def test_parquet_export_unknown_run_returns_404(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = client_with_store.get("/api/results/unknown/export/parquet", headers=auth_headers)
        assert response.status_code == 404

    def test_parquet_export_evicted_result_returns_409(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
    ) -> None:
        tmp_store.save_metadata("evicted", _make_metadata("evicted"))
        response = client_with_store.get("/api/results/evicted/export/parquet", headers=auth_headers)
        assert response.status_code == 409
