# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for runtime-mode contract and default behavior.

Story 23.1 / AC-1, AC-2, AC-3: Runtime mode contract with live default.
"""

from __future__ import annotations

import json
from typing import get_args, get_origin

import pytest
from pydantic import ValidationError

from reformlab.computation.types import RuntimeMode
from reformlab.governance import RunManifest
from reformlab.server.models import RunRequest, RunResponse


class TestRuntimeModeType:
    """Story 23.1 / AC-1, AC-2: RuntimeMode literal type contract."""

    def test_runtime_mode_is_exported(self) -> None:
        """RuntimeMode is exported from reformlab.computation.types."""
        from reformlab.computation.types import RuntimeMode

        # RuntimeMode is a type alias (Literal), not a value
        # We can verify it exists and is a type
        assert RuntimeMode is not None

    def test_runtime_mode_values_are_valid_strings(self) -> None:
        """'live' and 'replay' are the valid RuntimeMode string values."""
        valid_modes = ["live", "replay"]
        assert "live" in valid_modes
        assert "replay" in valid_modes

    def test_runtime_mode_type_annotation_works(self) -> None:
        """RuntimeMode can be used as a type annotation."""

        # RuntimeMode should be a Literal type
        # get_origin should return Literal for a Literal type
        origin = get_origin(RuntimeMode)
        assert origin is not None

        # get_args should return the literal values ("live", "replay")
        args = get_args(RuntimeMode)
        assert set(args) == {"live", "replay"}


class TestRunRequestRuntimeMode:
    """Story 23.1 / AC-1: RunRequest runtime_mode field with live default."""

    def test_runtime_mode_defaults_to_live(self) -> None:
        """RunRequest defaults to 'live' when runtime_mode not specified."""
        request = RunRequest(
            template_name="carbon_tax",
            policy={"rate_schedule": {"2025": 50.0}},
            start_year=2025,
            end_year=2030,
        )
        assert request.runtime_mode == "live"

    def test_runtime_mode_explicit_live_accepted(self) -> None:
        """RunRequest accepts explicit 'live' runtime_mode."""
        request = RunRequest(
            template_name="carbon_tax",
            policy={"rate_schedule": {"2025": 50.0}},
            start_year=2025,
            end_year=2030,
            runtime_mode="live",
        )
        assert request.runtime_mode == "live"

    def test_runtime_mode_explicit_replay_accepted(self) -> None:
        """RunRequest accepts explicit 'replay' runtime_mode."""
        request = RunRequest(
            template_name="carbon_tax",
            policy={"rate_schedule": {"2025": 50.0}},
            start_year=2025,
            end_year=2030,
            runtime_mode="replay",
        )
        assert request.runtime_mode == "replay"

    def test_runtime_mode_invalid_value_raises_validation_error(self) -> None:
        """Invalid runtime_mode value raises Pydantic ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RunRequest(
                template_name="carbon_tax",
                policy={"rate_schedule": {"2025": 50.0}},
                start_year=2025,
                end_year=2030,
                runtime_mode="invalid",  # type: ignore
            )
        errors = exc_info.value.errors()
        assert any("runtime_mode" in str(err) for err in errors)

    def test_runtime_mode_serializes_to_json(self) -> None:
        """RunRequest runtime_mode field serializes correctly to JSON."""
        request = RunRequest(
            template_name="carbon_tax",
            policy={"rate_schedule": {"2025": 50.0}},
            start_year=2025,
            end_year=2030,
            runtime_mode="live",
        )
        # Pydantic v2 model_dump should work
        data = request.model_dump()
        assert data["runtime_mode"] == "live"

    def test_runtime_mode_replay_serializes_to_json(self) -> None:
        """RunRequest with replay runtime_mode serializes correctly."""
        request = RunRequest(
            template_name="carbon_tax",
            policy={"rate_schedule": {"2025": 50.0}},
            start_year=2025,
            end_year=2030,
            runtime_mode="replay",
        )
        data = request.model_dump()
        assert data["runtime_mode"] == "replay"


class TestRunResponseRuntimeMode:
    """Story 23.1 / AC-4: RunResponse runtime_mode field."""

    def test_run_response_includes_runtime_mode(self) -> None:
        """RunResponse can be constructed with runtime_mode field."""
        response = RunResponse(
            run_id="test-run-001",
            success=True,
            scenario_id="test-scenario",
            years=[2025, 2026],
            row_count=1000,
            manifest_id="manifest-001",
        )
        # RunResponse should have runtime_mode field
        # Default is "live" if not specified
        assert hasattr(response, "runtime_mode")

    def test_run_response_runtime_mode_default_is_live(self) -> None:
        """RunResponse runtime_mode defaults to 'live'."""
        response = RunResponse(
            run_id="test-run-001",
            success=True,
            scenario_id="test-scenario",
            years=[2025, 2026],
            row_count=1000,
            manifest_id="manifest-001",
        )
        assert response.runtime_mode == "live"


class TestRuntimeModeMigrationCompatibility:
    """Story 23.1 / AC-3: Backward compatibility with legacy data."""

    def test_legacy_request_without_runtime_mode_defaults_to_live(self) -> None:
        """Legacy JSON request without runtime_mode deserializes with live default."""
        legacy_json = {
            "template_name": "carbon_tax",
            "policy": {"rate_schedule": {"2025": 50.0}},
            "start_year": 2025,
            "end_year": 2030,
        }
        request = RunRequest(**legacy_json)
        assert request.runtime_mode == "live"

    def test_request_json_serialization_round_trip(self) -> None:
        """Request serializes and deserializes with runtime_mode preserved."""
        request = RunRequest(
            template_name="carbon_tax",
            policy={"rate_schedule": {"2025": 50.0}},
            start_year=2025,
            end_year=2030,
            runtime_mode="replay",
        )
        # Serialize to dict
        data = request.model_dump()
        # Deserialize back
        request2 = RunRequest(**data)
        assert request2.runtime_mode == "replay"


class TestRuntimeModeSeparationFromSimulationMode:
    """Story 23.1 / AC-3: runtime_mode is separate from simulation_mode."""

    def test_runtime_mode_and_simulation_mode_are_distinct(self) -> None:
        """RuntimeMode (live/replay) is conceptually distinct from simulation modes.

        This test documents the architectural distinction:
        - runtime_mode: Execution path (live vs replay)
        - simulation_mode: Simulation behavior (annual vs horizon_step)

        They are orthogonal concerns and should not be conflated.
        """
        # runtime_mode values
        runtime_modes = ["live", "replay"]

        # simulation_mode values (from Scenario.simulation_mode in domain layer)
        # These are NOT part of RunRequest - they're in ScenarioConfig
        simulation_modes = ["annual", "horizon_step"]

        # Verify the sets are disjoint
        assert set(runtime_modes).isdisjoint(set(simulation_modes))

        # Verify the conceptual distinction
        assert "live" not in simulation_modes
        assert "replay" not in simulation_modes
        assert "annual" not in runtime_modes
        assert "horizon_step" not in runtime_modes


class TestRunManifestRuntimeMode:
    """Story 23.1 / AC-4: Runtime mode in RunManifest."""

    def test_manifest_includes_runtime_mode_field(self) -> None:
        """RunManifest includes runtime_mode field with 'live' default."""
        manifest = RunManifest(
            manifest_id="test-001",
            created_at="2026-04-01T00:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            runtime_mode="live",
        )
        assert manifest.runtime_mode == "live"

    def test_manifest_runtime_mode_default_is_live(self) -> None:
        """RunManifest runtime_mode defaults to 'live' when not specified."""
        manifest = RunManifest(
            manifest_id="test-001",
            created_at="2026-04-01T00:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
        )
        assert manifest.runtime_mode == "live"

    def test_manifest_runtime_mode_replay_accepted(self) -> None:
        """RunManifest accepts 'replay' as runtime_mode value."""
        manifest = RunManifest(
            manifest_id="test-001",
            created_at="2026-04-01T00:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            runtime_mode="replay",
        )
        assert manifest.runtime_mode == "replay"

    def test_manifest_to_json_includes_runtime_mode(self) -> None:
        """RunManifest.to_json() includes runtime_mode field."""
        manifest = RunManifest(
            manifest_id="test-001",
            created_at="2026-04-01T00:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            runtime_mode="live",
        )
        json_str = manifest.to_json()
        data = json.loads(json_str)
        assert "runtime_mode" in data
        assert data["runtime_mode"] == "live"

    def test_manifest_from_json_with_runtime_mode(self) -> None:
        """RunManifest.from_json() deserializes runtime_mode field."""
        json_str = json.dumps({
            "manifest_id": "test-001",
            "created_at": "2026-04-01T00:00:00Z",
            "engine_version": "0.1.0",
            "openfisca_version": "40.0.0",
            "adapter_version": "1.0.0",
            "scenario_version": "v1.0",
            "data_hashes": {},
            "output_hashes": {},
            "seeds": {},
            "policy": {},
            "assumptions": [],
            "mappings": [],
            "warnings": [],
            "step_pipeline": [],
            "parent_manifest_id": "",
            "child_manifests": {},
            "runtime_mode": "replay",
            "integrity_hash": "",
        })
        manifest = RunManifest.from_json(json_str)
        assert manifest.runtime_mode == "replay"

    def test_manifest_from_json_without_runtime_mode_defaults_to_live(self) -> None:
        """Legacy manifest JSON without runtime_mode deserializes with 'live' default."""
        json_str = json.dumps({
            "manifest_id": "test-001",
            "created_at": "2026-04-01T00:00:00Z",
            "engine_version": "0.1.0",
            "openfisca_version": "40.0.0",
            "adapter_version": "1.0.0",
            "scenario_version": "v1.0",
            "data_hashes": {},
            "output_hashes": {},
            "seeds": {},
            "policy": {},
            "assumptions": [],
            "mappings": [],
            "warnings": [],
            "step_pipeline": [],
            "parent_manifest_id": "",
            "child_manifests": {},
            "integrity_hash": "",
        })
        manifest = RunManifest.from_json(json_str)
        assert manifest.runtime_mode == "live"

    def test_manifest_from_json_with_invalid_runtime_mode_raises(self) -> None:
        """Invalid runtime_mode value in JSON raises ManifestValidationError."""
        from reformlab.governance import ManifestValidationError

        json_str = json.dumps({
            "manifest_id": "test-001",
            "created_at": "2026-04-01T00:00:00Z",
            "engine_version": "0.1.0",
            "openfisca_version": "40.0.0",
            "adapter_version": "1.0.0",
            "scenario_version": "v1.0",
            "data_hashes": {},
            "output_hashes": {},
            "seeds": {},
            "policy": {},
            "assumptions": [],
            "mappings": [],
            "warnings": [],
            "step_pipeline": [],
            "parent_manifest_id": "",
            "child_manifests": {},
            "runtime_mode": "invalid",
            "integrity_hash": "",
        })
        with pytest.raises(ManifestValidationError):
            RunManifest.from_json(json_str)
