# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for the manifest endpoint — Story 26.4, AC-2, AC-4.

Verifies:
- GET /api/results/{run_id}/manifest — returns 200 with full manifest
- 200 with metadata_only=True when only manifest.json exists (no panel.parquet)
- 404 when run_id not found
- 409 when both SimulationResult and manifest.json are unavailable
- All manifest fields are correctly serialized
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from reformlab.governance.manifest import RunManifest
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


def _make_manifest() -> RunManifest:
    """Create a RunManifest with all fields populated for testing."""
    return RunManifest(
        manifest_id="550e8400-e29b-41d4-a716-446655440001",
        created_at="2026-03-07T22:00:00+00:00",
        engine_version="1.0.0",
        openfisca_version="44.0.0",
        adapter_version="1.0.0",
        scenario_version="1.0.0",
        data_hashes={
            "population.csv": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        },
        output_hashes={
            "panel.parquet": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        },
        integrity_hash="cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        seeds={"master": 42, "2025": 42, "2026": 43},
        policy={"carbon_tax_rate": 100},
        assumptions=[
            {"key": "carbon_tax_rate", "value": 100, "source": "user", "is_default": False},
        ],
        mappings=[
            {
                "openfisca_name": "carbon_tax",
                "project_name": "carbon_tax_rate",
                "direction": "input",
            },
        ],
        warnings=["Warning message"],
        step_pipeline=["preprocess", "compute", "aggregate"],
        parent_manifest_id="",
        child_manifests={2026: "660e8400-e29b-41d4-a716-446655440002"},
        exogenous_series=("co2_price",),
        taste_parameters={"price_sensitivity": -1.5},
        evidence_assets=[{"type": "official", "source": "INSEE"}],
        calibration_assets=[],
        validation_assets=[],
        evidence_summary={"trust_level": "high"},
        runtime_mode="live",
        population_id="fr-synthetic-2024",
        population_source="bundled",
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
# GET /api/results/{run_id}/manifest
# ---------------------------------------------------------------------------


class TestGetManifest:
    """Story 26.4, AC-2, AC-4: manifest endpoint."""

    def test_returns_404_for_unknown_run_id(
        self, client_with_store: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Return 404 when run_id not found in persistent store."""
        response = client_with_store.get(
            "/api/results/unknown-run/manifest",
            headers=auth_headers,
        )
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert "not found" in detail["what"].lower()

    def test_returns_404_for_invalid_run_id(
        self, client_with_store: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Return 404 for invalid run_id with path traversal (treated as unknown run)."""
        response = client_with_store.get(
            "/api/results/../etc/passwd/manifest",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_returns_full_manifest_from_cache(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
    ) -> None:
        """Return 200 with full manifest when SimulationResult is in cache."""
        from reformlab.interfaces.api import SimulationResult
        from reformlab.orchestrator.panel import PanelOutput
        from reformlab.server.dependencies import get_result_cache

        # Set up store with metadata and manifest
        run_id = "cached-run"
        manifest = _make_manifest()
        tmp_store.save_metadata(run_id, _make_metadata(run_id))
        tmp_store.save_manifest(run_id, manifest.to_json())

        # Create a SimulationResult with panel and put it in cache
        import pyarrow as pa

        table = pa.table({"person_id": [1, 2], "income": [1000, 2000]})
        panel = PanelOutput(table=table, metadata={})
        sim_result = SimulationResult(
            success=True,
            scenario_id="scenario-001",
            yearly_states={},
            panel_output=panel,
            manifest=manifest,
            metadata={},
        )

        cache = get_result_cache()
        cache.store(run_id, sim_result)

        # Request manifest
        response = client_with_store.get(
            f"/api/results/{run_id}/manifest",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        # Verify all core fields
        assert data["run_id"] == run_id
        assert data["manifest_id"] == "550e8400-e29b-41d4-a716-446655440001"
        assert data["status"] == "completed"
        assert data["metadata_only"] is False

        # Verify version fields
        assert data["engine_version"] == "1.0.0"
        assert data["openfisca_version"] == "44.0.0"
        assert data["adapter_version"] == "1.0.0"

        # Verify hashes
        assert data["data_hashes"]["population.csv"] == "a" * 64
        assert data["integrity_hash"] == "c" * 64

        # Verify execution metadata
        assert data["seeds"]["master"] == 42
        assert data["policy"]["carbon_tax_rate"] == 100
        assert len(data["assumptions"]) == 1
        assert data["assumptions"][0]["key"] == "carbon_tax_rate"
        assert len(data["mappings"]) == 1
        assert data["mappings"][0]["openfisca_name"] == "carbon_tax"
        assert data["warnings"] == ["Warning message"]
        assert data["step_pipeline"] == ["preprocess", "compute", "aggregate"]

        # Verify lineage
        assert data["parent_manifest_id"] == ""
        assert data["child_manifests"]["2026"] == "660e8400-e29b-41d4-a716-446655440002"

        # Verify optional fields
        assert data["exogenous_series"] == ["co2_price"]
        assert data["taste_parameters"]["price_sensitivity"] == -1.5
        assert len(data["evidence_assets"]) == 1
        assert data["evidence_summary"]["trust_level"] == "high"

        # Verify runtime mode and population
        assert data["runtime_mode"] == "live"
        assert data["population_id"] == "fr-synthetic-2024"
        assert data["population_source"] == "bundled"

    def test_returns_metadata_only_manifest_from_disk(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
    ) -> None:
        """Return 200 with metadata_only=True when only manifest.json exists."""
        run_id = "metadata-only-run"
        manifest = _make_manifest()
        tmp_store.save_metadata(run_id, _make_metadata(run_id))
        tmp_store.save_manifest(run_id, manifest.to_json())
        # No panel.parquet and no cache entry

        response = client_with_store.get(
            f"/api/results/{run_id}/manifest",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert data["run_id"] == run_id
        assert data["manifest_id"] == "550e8400-e29b-41d4-a716-446655440001"
        assert data["status"] == "metadata_only"
        assert data["metadata_only"] is True
        # Should include warning about missing panel data
        assert any("Panel data not available" in w for w in data["warnings"])

    def test_returns_409_when_no_manifest_or_panel(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
    ) -> None:
        """Return 409 when neither SimulationResult nor manifest.json exist."""
        run_id = "no-manifest-run"
        tmp_store.save_metadata(run_id, _make_metadata(run_id))
        # No manifest.json, no panel.parquet, no cache entry

        response = client_with_store.get(
            f"/api/results/{run_id}/manifest",
            headers=auth_headers,
        )
        assert response.status_code == 409
        detail = response.json()["detail"]
        assert "not available" in detail["what"].lower()

    def test_exogenous_series_converted_from_tuple_to_list(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
    ) -> None:
        """Convert exogenous_series tuple to list for JSON serialization."""
        from reformlab.interfaces.api import SimulationResult
        from reformlab.orchestrator.panel import PanelOutput
        from reformlab.server.dependencies import get_result_cache

        run_id = "exogenous-run"
        manifest = RunManifest(
            manifest_id="770e8400-e29b-41d4-a716-446655440003",
            created_at="2026-03-07T22:00:00+00:00",
            engine_version="1.0.0",
            openfisca_version="44.0.0",
            adapter_version="1.0.0",
            scenario_version="1.0.0",
            exogenous_series=("series1", "series2", "series3"),
            runtime_mode="live",
        )
        tmp_store.save_metadata(run_id, _make_metadata(run_id))
        tmp_store.save_manifest(run_id, manifest.to_json())

        import pyarrow as pa

        table = pa.table({"person_id": [1]})
        panel = PanelOutput(table=table, metadata={})
        sim_result = SimulationResult(
            success=True,
            scenario_id="scenario-001",
            yearly_states={},
            panel_output=panel,
            manifest=manifest,
            metadata={},
        )

        cache = get_result_cache()
        cache.store(run_id, sim_result)

        response = client_with_store.get(
            f"/api/results/{run_id}/manifest",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["exogenous_series"], list)
        assert data["exogenous_series"] == ["series1", "series2", "series3"]

    def test_includes_metadata_timestamps(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
    ) -> None:
        """Include started_at and finished_at from ResultMetadata."""
        from reformlab.interfaces.api import SimulationResult
        from reformlab.orchestrator.panel import PanelOutput
        from reformlab.server.dependencies import get_result_cache

        run_id = "timestamps-run"
        manifest = RunManifest(
            manifest_id="880e8400-e29b-41d4-a716-446655440004",
            created_at="2026-03-07T22:00:00+00:00",
            engine_version="1.0.0",
            openfisca_version="44.0.0",
            adapter_version="1.0.0",
            scenario_version="1.0.0",
            runtime_mode="live",
        )
        metadata = _make_metadata(run_id)
        tmp_store.save_metadata(run_id, metadata)
        tmp_store.save_manifest(run_id, manifest.to_json())

        import pyarrow as pa

        table = pa.table({"person_id": [1]})
        panel = PanelOutput(table=table, metadata={})
        sim_result = SimulationResult(
            success=True,
            scenario_id="scenario-001",
            yearly_states={},
            panel_output=panel,
            manifest=manifest,
            metadata={},
        )

        cache = get_result_cache()
        cache.store(run_id, sim_result)

        response = client_with_store.get(
            f"/api/results/{run_id}/manifest",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["started_at"] == "2026-03-07T22:00:00+00:00"
        assert data["finished_at"] == "2026-03-07T22:00:05+00:00"

    def test_population_source_null_for_missing(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
    ) -> None:
        """Return null population_source when not in metadata (legacy runs)."""
        from reformlab.interfaces.api import SimulationResult
        from reformlab.orchestrator.panel import PanelOutput
        from reformlab.server.dependencies import get_result_cache

        run_id = "legacy-run"
        manifest = RunManifest(
            manifest_id="990e8400-e29b-41d4-a716-446655440005",
            created_at="2026-03-07T22:00:00+00:00",
            engine_version="1.0.0",
            openfisca_version="44.0.0",
            adapter_version="1.0.0",
            scenario_version="1.0.0",
            runtime_mode="live",
            population_id="",
            population_source="",  # Empty for legacy runs
        )
        metadata = ResultMetadata(
            run_id=run_id,
            timestamp="2026-03-07T22:00:00+00:00",
            run_kind="scenario",
            start_year=2025,
            end_year=2030,
            population_id=None,
            seed=42,
            row_count=1000,
            manifest_id="990e8400-e29b-41d4-a716-446655440005",
            scenario_id="scenario-001",
            adapter_version="1.0.0",
            started_at="2026-03-07T22:00:00+00:00",
            finished_at="2026-03-07T22:00:05+00:00",
            status="completed",
            template_name="Carbon Tax",
            policy_type="carbon_tax",
            population_source=None,  # Legacy run with no population_source
        )
        tmp_store.save_metadata(run_id, metadata)
        tmp_store.save_manifest(run_id, manifest.to_json())

        import pyarrow as pa

        table = pa.table({"person_id": [1]})
        panel = PanelOutput(table=table, metadata={})
        sim_result = SimulationResult(
            success=True,
            scenario_id="scenario-001",
            yearly_states={},
            panel_output=panel,
            manifest=manifest,
            metadata={},
        )

        cache = get_result_cache()
        cache.store(run_id, sim_result)

        response = client_with_store.get(
            f"/api/results/{run_id}/manifest",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["population_source"] is None

    def test_child_manifests_converted_to_dict_with_string_keys(
        self,
        client_with_store: TestClient,
        auth_headers: dict[str, str],
        tmp_store: ResultStore,
    ) -> None:
        """Convert child_manifests dict with int keys to dict with string keys for JSON."""
        from reformlab.interfaces.api import SimulationResult
        from reformlab.orchestrator.panel import PanelOutput
        from reformlab.server.dependencies import get_result_cache

        run_id = "lineage-run"
        manifest = RunManifest(
            manifest_id="aa0e8400-e29b-41d4-a716-446655440006",
            created_at="2026-03-07T22:00:00+00:00",
            engine_version="1.0.0",
            openfisca_version="44.0.0",
            adapter_version="1.0.0",
            scenario_version="1.0.0",
            child_manifests={
                2025: "bb0e8400-e29b-41d4-a716-446655440007",
                2026: "cc0e8400-e29b-41d4-a716-446655440008",
                2027: "dd0e8400-e29b-41d4-a716-446655440009",
            },
            runtime_mode="live",
        )
        tmp_store.save_metadata(run_id, _make_metadata(run_id))
        tmp_store.save_manifest(run_id, manifest.to_json())

        import pyarrow as pa

        table = pa.table({"person_id": [1]})
        panel = PanelOutput(table=table, metadata={})
        sim_result = SimulationResult(
            success=True,
            scenario_id="scenario-001",
            yearly_states={},
            panel_output=panel,
            manifest=manifest,
            metadata={},
        )

        cache = get_result_cache()
        cache.store(run_id, sim_result)

        response = client_with_store.get(
            f"/api/results/{run_id}/manifest",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        # JSON serialization converts int keys to strings
        assert "2025" in data["child_manifests"]
        assert data["child_manifests"]["2025"] == "bb0e8400-e29b-41d4-a716-446655440007"

    def test_unauthenticated_returns_401(self, client_with_store: TestClient) -> None:
        response = client_with_store.get("/api/results/run-001/manifest")
        assert response.status_code == 401
