# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Regression tests for POST /api/runs — Story 17.3 + Integration hardening Story 1.

Verifies that the metadata auto-save integration does not break the existing
run endpoint response shape, and that metadata is saved for both success and
failure paths.

Story 1 additions: portfolio execution via portfolio_name field.

MockAdapter is injected by patching the global _adapter singleton so that
OpenFisca data files are not required.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from reformlab.computation.mock_adapter import MockAdapter
from reformlab.server.result_store import ResultStore

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_store(tmp_path: Path) -> ResultStore:
    """ResultStore backed by tmp_path — no pollution of ~/.reformlab."""
    return ResultStore(base_dir=tmp_path)


@pytest.fixture()
def client_with_store(tmp_store: ResultStore, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """TestClient with ResultStore and MockAdapter injected via module patching."""
    import reformlab.server.dependencies as deps

    # Inject MockAdapter so runs.py does not try to use the real OpenFisca adapter
    monkeypatch.setattr(deps, "_adapter", MockAdapter())
    # Inject tmp_store so runs.py saves metadata to the test directory
    monkeypatch.setattr(deps, "_result_store", tmp_store)

    from reformlab.server.app import create_app
    from reformlab.server.dependencies import get_result_store

    app = create_app()
    # Also override Depends(get_result_store) used in results router
    app.dependency_overrides[get_result_store] = lambda: tmp_store
    return TestClient(app)


@pytest.fixture()
def auth_headers(client_with_store: TestClient) -> dict[str, str]:
    response = client_with_store.post(
        "/api/auth/login",
        json={"password": "test-password-123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SIMPLE_RUN_BODY = {
    "template_name": "carbon_tax",
    "policy": {"rate_schedule": {"2025": 44}},
    "start_year": 2025,
    "end_year": 2025,
}

# ---------------------------------------------------------------------------
# Run response shape (regression)
# ---------------------------------------------------------------------------


class TestRunResponseShape:
    """Existing response shape must not change after metadata auto-save."""

    def test_run_returns_expected_fields(
        self, client_with_store: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client_with_store.post(
            "/api/runs",
            headers=auth_headers,
            json=_SIMPLE_RUN_BODY,
        )
        assert response.status_code == 200
        data = response.json()
        for field in ["run_id", "success", "scenario_id", "years", "row_count", "manifest_id"]:
            assert field in data, f"Missing field: {field}"

    def test_run_id_is_uuid(
        self, client_with_store: TestClient, auth_headers: dict[str, str]
    ) -> None:
        import uuid

        response = client_with_store.post(
            "/api/runs",
            headers=auth_headers,
            json=_SIMPLE_RUN_BODY,
        )
        assert response.status_code == 200
        run_id = response.json()["run_id"]
        uuid.UUID(run_id)


# ---------------------------------------------------------------------------
# Metadata auto-save on success
# ---------------------------------------------------------------------------


class TestRunMetadataAutoSaveSuccess:
    """Verify metadata is saved to the store after a successful run."""

    def test_metadata_saved_after_run(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
    ) -> None:
        response = client_with_store.post(
            "/api/runs",
            headers=auth_headers,
            json=_SIMPLE_RUN_BODY,
        )
        assert response.status_code == 200
        run_id = response.json()["run_id"]

        # Verify metadata was persisted
        results = tmp_store.list_results()
        assert len(results) == 1
        assert results[0].run_id == run_id
        assert results[0].status == "completed"

    def test_saved_metadata_has_correct_fields(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
    ) -> None:
        response = client_with_store.post(
            "/api/runs",
            headers=auth_headers,
            json={
                "template_name": "carbon_tax",
                "policy": {"rate_schedule": {"2025": 44}},
                "start_year": 2025,
                "end_year": 2027,
                "seed": 99,
            },
        )
        assert response.status_code == 200
        results = tmp_store.list_results()
        assert len(results) == 1
        meta = results[0]
        assert meta.start_year == 2025
        assert meta.end_year == 2027
        assert meta.seed == 99
        assert meta.run_kind == "scenario"
        assert meta.started_at != ""
        assert meta.finished_at != ""


# ---------------------------------------------------------------------------
# Metadata save failure does not mask run result
# ---------------------------------------------------------------------------


class TestRunMetadataAutoSaveFailurePath:
    """Verify metadata is saved with status=failed when simulation raises."""

    def test_metadata_saved_on_simulation_exception(
        self,
        tmp_store: ResultStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When run_scenario raises, metadata must still be saved with status='failed'."""
        import reformlab.server.dependencies as deps

        monkeypatch.setattr(deps, "_adapter", MockAdapter())
        monkeypatch.setattr(deps, "_result_store", tmp_store)

        def failing_sim(*args: object, **kwargs: object) -> None:
            raise RuntimeError("Simulated simulation failure")

        monkeypatch.setattr("reformlab.interfaces.api.run_scenario", failing_sim)

        from reformlab.server.app import create_app
        from reformlab.server.dependencies import get_result_store

        app = create_app()
        app.dependency_overrides[get_result_store] = lambda: tmp_store

        # raise_server_exceptions=False: get the 500 response instead of re-raising
        with TestClient(app, raise_server_exceptions=False) as client:
            login_response = client.post("/api/auth/login", json={"password": "test-password-123"})
            token = login_response.json()["token"]
            headers = {"Authorization": f"Bearer {token}"}

            response = client.post("/api/runs", headers=headers, json=_SIMPLE_RUN_BODY)
            assert response.status_code == 500

        # Metadata must still be saved with failed status despite the exception
        results = tmp_store.list_results()
        assert len(results) == 1
        assert results[0].status == "failed"
        assert results[0].row_count == 0
        assert results[0].started_at != ""
        assert results[0].finished_at != ""


class TestRunMetadataSaveFailureDoesNotMaskRunResult:
    """If metadata save fails, the run response must still be returned."""

    def test_storage_failure_does_not_error_run_endpoint(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
    ) -> None:
        """Simulate save_metadata raising an exception; run must still return 200."""

        def failing_save(*args: object, **kwargs: object) -> None:
            raise OSError("Disk full")

        tmp_store.save_metadata = failing_save  # type: ignore[method-assign]

        response = client_with_store.post(
            "/api/runs",
            headers=auth_headers,
            json=_SIMPLE_RUN_BODY,
        )
        # Run endpoint must succeed even though metadata save failed
        assert response.status_code == 200
        assert "run_id" in response.json()


# ---------------------------------------------------------------------------
# POST /api/runs/memory-check — Story 17.6, AC-1
# ---------------------------------------------------------------------------


class TestMemoryCheck:
    """POST /api/runs/memory-check — success path and response schema."""

    def test_memory_check_returns_200(
        self, client_with_store: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client_with_store.post(
            "/api/runs/memory-check",
            headers=auth_headers,
            json={
                "template_name": "carbon_tax",
                "policy": {"rate_schedule": {"2025": 44}},
                "start_year": 2025,
                "end_year": 2025,
            },
        )
        assert response.status_code == 200

    def test_memory_check_response_has_expected_fields(
        self, client_with_store: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client_with_store.post(
            "/api/runs/memory-check",
            headers=auth_headers,
            json={
                "template_name": "carbon_tax",
                "policy": {},
                "start_year": 2025,
                "end_year": 2030,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "should_warn" in data
        assert "estimated_gb" in data
        assert "available_gb" in data
        assert "message" in data
        assert isinstance(data["should_warn"], bool)
        assert isinstance(data["estimated_gb"], float)
        assert isinstance(data["available_gb"], float)
        assert isinstance(data["message"], str)


# ---------------------------------------------------------------------------
# Story 1: Portfolio execution via POST /api/runs
# ---------------------------------------------------------------------------


class TestPortfolioExecution:
    """Story 1: Wire portfolio execution into run endpoint."""

    def test_422_when_both_portfolio_and_template(
        self, client_with_store: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """422 when both portfolio_name and template_name provided."""
        response = client_with_store.post(
            "/api/runs",
            headers=auth_headers,
            json={
                "portfolio_name": "test-portfolio",
                "template_name": "carbon_tax",
                "start_year": 2025,
                "end_year": 2025,
            },
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert "portfolio_name" in detail["why"]
        assert "template_name" in detail["why"]

    def test_404_when_portfolio_not_found(
        self,
        tmp_store: ResultStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """404 when portfolio_name not in registry."""
        import reformlab.server.dependencies as deps

        monkeypatch.setattr(deps, "_adapter", MockAdapter())
        monkeypatch.setattr(deps, "_result_store", tmp_store)

        # Create an empty registry backed by tmp_path
        from reformlab.templates.registry import ScenarioRegistry

        empty_registry = ScenarioRegistry(registry_path=tmp_store._base_dir / "empty_registry")
        monkeypatch.setattr(deps, "_registry", empty_registry)

        from reformlab.server.app import create_app
        from reformlab.server.dependencies import get_registry, get_result_store

        app = create_app()
        app.dependency_overrides[get_result_store] = lambda: tmp_store
        app.dependency_overrides[get_registry] = lambda: empty_registry

        client = TestClient(app)
        login = client.post("/api/auth/login", json={"password": "test-password-123"})
        headers = {"Authorization": f"Bearer {login.json()['token']}"}

        response = client.post(
            "/api/runs",
            headers=headers,
            json={
                "portfolio_name": "nonexistent-portfolio",
                "start_year": 2025,
                "end_year": 2025,
            },
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]["what"].lower()

    def test_existing_template_runs_unchanged(
        self, client_with_store: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Existing template_name-based runs still work (regression)."""
        response = client_with_store.post(
            "/api/runs",
            headers=auth_headers,
            json=_SIMPLE_RUN_BODY,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


# ---------------------------------------------------------------------------
# Story 23.2: Unified population resolver integration tests
# ---------------------------------------------------------------------------


def _make_client_with_resolver(
    tmp_store: ResultStore,
    monkeypatch: pytest.MonkeyPatch,
    data_dir: Path,
    uploaded_dir: Path,
) -> tuple[TestClient, dict[str, str]]:
    """Create a TestClient with injected store, adapter, and population resolver."""
    import reformlab.server.dependencies as deps
    from reformlab.server.population_resolver import PopulationResolver

    monkeypatch.setattr(deps, "_adapter", MockAdapter())
    monkeypatch.setattr(deps, "_result_store", tmp_store)
    # Inject resolver pointing at our temp directories
    monkeypatch.setattr(deps, "_population_resolver", PopulationResolver(data_dir, uploaded_dir))

    from reformlab.server.app import create_app
    from reformlab.server.dependencies import get_result_store

    app = create_app()
    app.dependency_overrides[get_result_store] = lambda: tmp_store
    client = TestClient(app)

    login = client.post("/api/auth/login", json={"password": "test-password-123"})
    headers = {"Authorization": f"Bearer {login.json()['token']}"}
    return client, headers


class TestRunWithBundledPopulation:
    """Story 23.2 / AC-1: Bundled populations are resolved and executable."""

    def test_run_with_bundled_population_succeeds(
        self, tmp_store: ResultStore, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        data_dir = tmp_path / "populations"
        data_dir.mkdir()
        (data_dir / "fr-synthetic-2024.csv").write_text(
            "household_id,income\n1,50000\n", encoding="utf-8"
        )
        uploaded_dir = tmp_path / "uploaded"
        uploaded_dir.mkdir()

        client, headers = _make_client_with_resolver(
            tmp_store, monkeypatch, data_dir, uploaded_dir
        )
        response = client.post(
            "/api/runs",
            headers=headers,
            json={
                **_SIMPLE_RUN_BODY,
                "population_id": "fr-synthetic-2024",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # AC-5: population_source in response
        assert data["population_source"] == "bundled"

    def test_bundled_population_source_persisted_in_metadata(
        self, tmp_store: ResultStore, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        data_dir = tmp_path / "populations"
        data_dir.mkdir()
        (data_dir / "test-bundled.csv").write_text(
            "household_id,income\n1,50000\n", encoding="utf-8"
        )
        uploaded_dir = tmp_path / "uploaded"
        uploaded_dir.mkdir()

        client, headers = _make_client_with_resolver(
            tmp_store, monkeypatch, data_dir, uploaded_dir
        )
        client.post(
            "/api/runs",
            headers=headers,
            json={**_SIMPLE_RUN_BODY, "population_id": "test-bundled"},
        )

        results = tmp_store.list_results()
        assert len(results) == 1
        assert results[0].population_source == "bundled"


class TestRunWithUploadedPopulation:
    """Story 23.2 / AC-2: Uploaded populations are resolved and executable."""

    def test_run_with_uploaded_population_succeeds(
        self, tmp_store: ResultStore, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        data_dir = tmp_path / "populations"
        data_dir.mkdir()
        uploaded_dir = tmp_path / "uploaded"
        uploaded_dir.mkdir()
        (uploaded_dir / "my-upload.csv").write_text(
            "household_id,income\n2,60000\n", encoding="utf-8"
        )

        client, headers = _make_client_with_resolver(
            tmp_store, monkeypatch, data_dir, uploaded_dir
        )
        response = client.post(
            "/api/runs",
            headers=headers,
            json={**_SIMPLE_RUN_BODY, "population_id": "my-upload"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["population_source"] == "uploaded"

    def test_uploaded_population_source_persisted_in_metadata(
        self, tmp_store: ResultStore, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        data_dir = tmp_path / "populations"
        data_dir.mkdir()
        uploaded_dir = tmp_path / "uploaded"
        uploaded_dir.mkdir()
        (uploaded_dir / "my-upload.csv").write_text(
            "household_id,income\n2,60000\n", encoding="utf-8"
        )

        client, headers = _make_client_with_resolver(
            tmp_store, monkeypatch, data_dir, uploaded_dir
        )
        client.post(
            "/api/runs",
            headers=headers,
            json={**_SIMPLE_RUN_BODY, "population_id": "my-upload"},
        )

        results = tmp_store.list_results()
        assert len(results) == 1
        assert results[0].population_source == "uploaded"


class TestRunWithGeneratedPopulation:
    """Story 23.2 / AC-3: Generated populations are resolved and executable."""

    def test_run_with_generated_population_succeeds(
        self, tmp_store: ResultStore, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        import json as json_lib

        data_dir = tmp_path / "populations"
        data_dir.mkdir()
        (data_dir / "gen-pop-2024.csv").write_text(
            "household_id,income\n3,70000\n", encoding="utf-8"
        )
        (data_dir / "gen-pop-2024.manifest.json").write_text(
            json_lib.dumps({"seed": 42, "method": "uniform"}), encoding="utf-8"
        )
        uploaded_dir = tmp_path / "uploaded"
        uploaded_dir.mkdir()

        client, headers = _make_client_with_resolver(
            tmp_store, monkeypatch, data_dir, uploaded_dir
        )
        response = client.post(
            "/api/runs",
            headers=headers,
            json={**_SIMPLE_RUN_BODY, "population_id": "gen-pop-2024"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["population_source"] == "generated"

    def test_generated_population_source_persisted_in_metadata(
        self, tmp_store: ResultStore, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        import json as json_lib

        data_dir = tmp_path / "populations"
        data_dir.mkdir()
        (data_dir / "gen-pop.csv").write_text(
            "household_id,income\n3,70000\n", encoding="utf-8"
        )
        (data_dir / "gen-pop.manifest.json").write_text(
            json_lib.dumps({"seed": 42}), encoding="utf-8"
        )
        uploaded_dir = tmp_path / "uploaded"
        uploaded_dir.mkdir()

        client, headers = _make_client_with_resolver(
            tmp_store, monkeypatch, data_dir, uploaded_dir
        )
        client.post(
            "/api/runs",
            headers=headers,
            json={**_SIMPLE_RUN_BODY, "population_id": "gen-pop"},
        )

        results = tmp_store.list_results()
        assert len(results) == 1
        assert results[0].population_source == "generated"


class TestRunWithMissingPopulation:
    """Story 23.2 / AC-4: Missing population blocks run with clear error."""

    def test_run_with_missing_population_returns_404(
        self, tmp_store: ResultStore, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        data_dir = tmp_path / "populations"
        data_dir.mkdir()
        uploaded_dir = tmp_path / "uploaded"
        uploaded_dir.mkdir()

        client, headers = _make_client_with_resolver(
            tmp_store, monkeypatch, data_dir, uploaded_dir
        )
        response = client.post(
            "/api/runs",
            headers=headers,
            json={**_SIMPLE_RUN_BODY, "population_id": "nonexistent-pop"},
        )

        assert response.status_code == 404
        detail = response.json()["detail"]
        assert "what" in detail
        assert "why" in detail
        assert "fix" in detail
        assert "nonexistent-pop" in detail["what"]

    def test_run_without_population_id_succeeds(
        self, client_with_store: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """No population_id → population_source is None, run still works."""
        response = client_with_store.post(
            "/api/runs",
            headers=auth_headers,
            json=_SIMPLE_RUN_BODY,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["population_source"] is None


class TestRunResponseIncludesPopulationSource:
    """Story 23.2 / AC-5: Run response and metadata include population_source."""

    def test_no_population_id_gives_null_source(
        self, client_with_store: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client_with_store.post(
            "/api/runs",
            headers=auth_headers,
            json=_SIMPLE_RUN_BODY,
        )
        assert response.status_code == 200
        assert response.json()["population_source"] is None

    def test_population_source_field_present_in_response(
        self, client_with_store: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client_with_store.post(
            "/api/runs",
            headers=auth_headers,
            json=_SIMPLE_RUN_BODY,
        )
        assert response.status_code == 200
        assert "population_source" in response.json()
