# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Story 23.4: Server integration tests for default live execution.

Verifies that:
- Default run mode uses live OpenFisca execution
- Replay mode is isolated to explicit opt-in
- Result persistence works with live mode
- No silent fallback occurs
"""

from __future__ import annotations

import logging
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
    """TestClient with ResultStore and MockAdapter injected."""
    import reformlab.server.dependencies as deps

    # Inject MockAdapter so runs.py does not try to use real OpenFisca adapter
    monkeypatch.setattr(deps, "_adapter", MockAdapter())
    # Inject tmp_store so runs.py saves metadata to test directory
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
# TestDefaultLiveExecution
# ---------------------------------------------------------------------------


class TestDefaultLiveExecution:
    """Story 23.4 / AC-1: Default run uses live mode."""

    def test_default_run_uses_live_mode(
        self, client_with_store: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """POST /api/runs without runtime_mode uses live mode."""
        response = client_with_store.post(
            "/api/runs",
            headers=auth_headers,
            json=_SIMPLE_RUN_BODY,
        )
        assert response.status_code == 200
        data = response.json()
        # RunResponse.runtime_mode should be "live" (default)
        assert data.get("runtime_mode") == "live"

    def test_explicit_live_run_uses_live_mode(
        self, client_with_store: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """POST with runtime_mode='live' explicitly works."""
        response = client_with_store.post(
            "/api/runs",
            headers=auth_headers,
            json={**_SIMPLE_RUN_BODY, "runtime_mode": "live"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("runtime_mode") == "live"

    def test_run_response_includes_runtime_mode(
        self, client_with_store: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """RunResponse includes runtime_mode field."""
        response = client_with_store.post(
            "/api/runs",
            headers=auth_headers,
            json=_SIMPLE_RUN_BODY,
        )
        assert response.status_code == 200
        data = response.json()
        assert "runtime_mode" in data
        # runtime_mode should be "live" or "replay"
        assert data["runtime_mode"] in ("live", "replay")


# ---------------------------------------------------------------------------
# TestReplayExecutionIsExplicit
# ---------------------------------------------------------------------------


class TestReplayExecutionIsExplicit:
    """Story 23.4 / AC-2: Replay mode is explicit opt-in."""

    def test_explicit_replay_run_uses_replay_mode(
        self,
        tmp_store: ResultStore,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """POST with runtime_mode='replay' produces replay mode."""
        import reformlab.server.dependencies as deps

        # Set up a temporary data directory for replay mode with dummy data files
        data_dir = tmp_path / "openfisca"
        data_dir.mkdir()
        # Create a dummy precomputed file with all required columns
        # DEFAULT_OPENFISCA_OUTPUT_SCHEMA requires: income_tax, carbon_tax
        (data_dir / "2025.csv").write_text(
            "household_id,income_tax,carbon_tax\n1,1000,50\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("REFORMLAB_OPENFISCA_DATA_DIR", str(data_dir))
        # Clear adapter singleton to pick up env var change
        monkeypatch.setattr(deps, "_adapter", None)

        # Create a fresh client with the new adapter singleton
        monkeypatch.setattr(deps, "_result_store", tmp_store)
        from reformlab.server.app import create_app
        from reformlab.server.dependencies import get_result_store

        app = create_app()
        app.dependency_overrides[get_result_store] = lambda: tmp_store
        client = TestClient(app)

        login = client.post("/api/auth/login", json={"password": "test-password-123"})
        headers = {"Authorization": f"Bearer {login.json()['token']}"}

        response = client.post(
            "/api/runs",
            headers=headers,
            json={**_SIMPLE_RUN_BODY, "runtime_mode": "replay"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("runtime_mode") == "replay"

    def test_replay_without_precomputed_data_returns_422(
        self,
        tmp_store: ResultStore,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Replay mode with no precomputed data returns 422."""
        import reformlab.server.dependencies as deps

        # Point to non-existent data directory
        # Since the error occurs during run_scenario() not during adapter
        # creation, we verify the 422 error path is covered by testing
        # that _create_replay_adapter() raises FileNotFoundError for missing data
        data_dir = tmp_path / "openfisca"
        # Don't create the directory - simulate missing data

        monkeypatch.setenv("REFORMLAB_OPENFISCA_DATA_DIR", str(data_dir))
        # Clear adapter singleton to pick up env var change
        monkeypatch.setattr(deps, "_adapter", None)

        # Create a fresh client with the new adapter singleton
        monkeypatch.setattr(deps, "_result_store", tmp_store)
        from reformlab.server.app import create_app
        from reformlab.server.dependencies import get_result_store

        app = create_app()
        app.dependency_overrides[get_result_store] = lambda: tmp_store
        client = TestClient(app)

        login = client.post("/api/auth/login", json={"password": "test-password-123"})
        headers = {"Authorization": f"Bearer {login.json()['token']}"}

        response = client.post(
            "/api/runs",
            headers=headers,
            json={**_SIMPLE_RUN_BODY, "runtime_mode": "replay"},
        )
        # _create_replay_adapter() now validates data_dir eagerly,
        # so the 422 handler in runs.py catches FileNotFoundError.
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert detail["what"] == "Replay mode unavailable"


# ---------------------------------------------------------------------------
# TestResultPersistenceAfterLiveRun
# ---------------------------------------------------------------------------


class TestResultPersistenceAfterLiveRun:
    """Story 23.4 / AC-3: Result persistence works with live mode."""

    def test_live_run_result_stored_in_cache(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
    ) -> None:
        """Live run result is retrievable from ResultCache."""
        from reformlab.server.dependencies import get_result_cache

        response = client_with_store.post(
            "/api/runs",
            headers=auth_headers,
            json=_SIMPLE_RUN_BODY,
        )
        assert response.status_code == 200
        run_id = response.json()["run_id"]

        # Result should be in cache
        cache = get_result_cache()
        cached_result = cache.get(run_id)
        assert cached_result is not None

    def test_live_run_result_stored_on_disk(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
    ) -> None:
        """Live run creates metadata.json, panel.parquet, and manifest.json."""
        response = client_with_store.post(
            "/api/runs",
            headers=auth_headers,
            json=_SIMPLE_RUN_BODY,
        )
        assert response.status_code == 200
        run_id = response.json()["run_id"]

        # Verify files exist on disk
        metadata_path = tmp_store._base_dir / run_id / "metadata.json"
        panel_path = tmp_store._base_dir / run_id / "panel.parquet"
        manifest_path = tmp_store._base_dir / run_id / "manifest.json"

        assert metadata_path.exists()
        assert panel_path.exists()
        assert manifest_path.exists()

    def test_live_run_result_reloadable_from_disk(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
    ) -> None:
        """Live run result can be reloaded from disk after cache eviction."""
        from reformlab.server.dependencies import get_result_cache

        response = client_with_store.post(
            "/api/runs",
            headers=auth_headers,
            json=_SIMPLE_RUN_BODY,
        )
        assert response.status_code == 200
        run_id = response.json()["run_id"]

        # Evict from cache
        cache = get_result_cache()
        cache.delete(run_id)

        # Result should still be loadable from disk
        reloaded = cache.get_or_load(run_id, tmp_store)
        assert reloaded is not None

    def test_live_run_manifest_records_runtime_mode(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
    ) -> None:
        """manifest.json on disk contains runtime_mode='live'."""
        import json

        response = client_with_store.post(
            "/api/runs",
            headers=auth_headers,
            json=_SIMPLE_RUN_BODY,
        )
        assert response.status_code == 200
        run_id = response.json()["run_id"]

        # Load manifest from disk
        manifest_path = tmp_store._base_dir / run_id / "manifest.json"
        manifest_content = json.loads(manifest_path.read_text())

        # Story 23.4 / AC-3: Manifest records runtime_mode
        assert manifest_content.get("runtime_mode") == "live"


# ---------------------------------------------------------------------------
# TestNoSilentDowngrade
# ---------------------------------------------------------------------------


class TestNoSilentDowngrade:
    """Story 23.4 / AC-4: No silent fallback from live to replay."""

    def test_live_mode_does_not_fall_back_to_precomputed(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Live request does not silently fall back to replay mode."""

        # Enable logging capture at ERROR level
        caplog.set_level(logging.ERROR, logger="reformlab.server.routes.runs")

        response = client_with_store.post(
            "/api/runs",
            headers=auth_headers,
            json={**_SIMPLE_RUN_BODY, "runtime_mode": "live"},
        )
        assert response.status_code == 200
        run_id = response.json()["run_id"]

        # Verify manifest has correct runtime_mode
        results = tmp_store.list_results()
        assert len(results) >= 1
        metadata = next((m for m in results if m.run_id == run_id), None)
        assert metadata is not None
        # AC-4: metadata.runtime_mode matches requested mode
        assert metadata.runtime_mode == "live"

        # Guard should NOT have fired (no ERROR log about mismatch)
        assert "runtime_mode_mismatch" not in caplog.text

    def test_guard_fires_on_runtime_mode_mismatch(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Guard logs ERROR when result runtime_mode differs from request."""
        from reformlab.interfaces import api as api_module

        caplog.set_level(logging.ERROR, logger="reformlab.server.routes.runs")

        # Patch run_scenario to return a result with mismatched runtime_mode
        original_run_scenario = api_module.run_scenario

        def patched_run_scenario(*args: object, **kwargs: object) -> object:
            result = original_run_scenario(*args, **kwargs)
            # Inject a mismatched runtime_mode into metadata
            result.metadata["runtime_mode"] = "replay"
            return result

        monkeypatch.setattr(api_module, "run_scenario", patched_run_scenario)

        response = client_with_store.post(
            "/api/runs",
            headers=auth_headers,
            json={**_SIMPLE_RUN_BODY, "runtime_mode": "live"},
        )
        assert response.status_code == 200

        # Guard SHOULD have fired
        assert "runtime_mode_mismatch" in caplog.text
        assert "requested=live" in caplog.text
        assert "actual=replay" in caplog.text
