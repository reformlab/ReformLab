"""Integration tests for orchestrator with WorkflowConfig (AC-5)."""

from __future__ import annotations

import uuid
from dataclasses import replace
from pathlib import Path

import pyarrow as pa
import pytest

from reformlab.computation.mapping import FieldMapping, MappingConfig
from reformlab.governance import hash_file
from reformlab.orchestrator import (
    OrchestratorConfig,
    OrchestratorRunner,
    YearState,
    from_workflow_config,
)
from reformlab.templates.workflow import (
    DataSourceConfig,
    RunConfig,
    ScenarioRef,
    WorkflowConfig,
    WorkflowResult,
    prepare_workflow_request,
    run_workflow,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def workflow_config() -> WorkflowConfig:
    """Return a valid WorkflowConfig for testing."""
    return WorkflowConfig(
        name="test_orchestrator",
        version="1.0",
        data_sources=DataSourceConfig(
            population="synthetic_french_2024",
            emission_factors="default",
        ),
        scenarios=(
            ScenarioRef(role="baseline", reference="carbon_tax_flat"),
            ScenarioRef(role="reform", reference="carbon_tax_progressive"),
        ),
        run_config=RunConfig(
            projection_years=10,
            start_year=2025,
            output_format="csv",
        ),
    )


@pytest.fixture
def short_workflow_config() -> WorkflowConfig:
    """Return a short projection WorkflowConfig for testing."""
    return WorkflowConfig(
        name="short_test",
        version="1.0",
        data_sources=DataSourceConfig(emission_factors="default"),
        scenarios=(ScenarioRef(role="scenario", reference="test"),),
        run_config=RunConfig(
            projection_years=3,
            start_year=2025,
            output_format="csv",
        ),
    )


def counting_step(year: int, state: YearState) -> YearState:
    """Test step that counts executions."""
    new_data = dict(state.data)
    new_data["count"] = new_data.get("count", 0) + 1
    return replace(state, data=new_data)


# ============================================================================
# Test: from_workflow_config factory (AC-5)
# ============================================================================


class TestFromWorkflowConfig:
    """Tests for from_workflow_config factory function (AC-5)."""

    def test_creates_valid_orchestrator_config(self, workflow_config: WorkflowConfig):
        """from_workflow_config creates valid OrchestratorConfig (AC-5)."""
        config = from_workflow_config(workflow_config)

        assert isinstance(config, OrchestratorConfig)
        assert config.start_year == 2025
        assert config.end_year == 2034  # 2025 + 10 - 1

    def test_maps_projection_years(self, workflow_config: WorkflowConfig):
        """projection_years correctly maps to end_year (AC-5)."""
        config = from_workflow_config(workflow_config)

        # 10 years from 2025 = 2025-2034 (inclusive)
        expected_end = (
            workflow_config.run_config.start_year
            + workflow_config.run_config.projection_years
            - 1
        )
        assert config.end_year == expected_end

    def test_maps_start_year(self, workflow_config: WorkflowConfig):
        """start_year correctly maps from run_config (AC-5)."""
        config = from_workflow_config(workflow_config)

        assert config.start_year == workflow_config.run_config.start_year

    def test_different_projection_values(self):
        """Different projection values map correctly."""
        wf_config = WorkflowConfig(
            name="test",
            version="1.0",
            data_sources=DataSourceConfig(emission_factors="default"),
            scenarios=(ScenarioRef(role="scenario", reference="test"),),
            run_config=RunConfig(
                projection_years=5,
                start_year=2030,
                output_format="csv",
            ),
        )

        config = from_workflow_config(wf_config)

        assert config.start_year == 2030
        assert config.end_year == 2034  # 2030 + 5 - 1

    def test_defaults_for_step_pipeline(self, workflow_config: WorkflowConfig):
        """from_workflow_config defaults to empty step pipeline."""
        config = from_workflow_config(workflow_config)

        assert config.step_pipeline == ()

    def test_defaults_for_seed(self, workflow_config: WorkflowConfig):
        """from_workflow_config defaults to no seed."""
        config = from_workflow_config(workflow_config)

        assert config.seed is None

    def test_rejects_non_positive_projection_years(self):
        """from_workflow_config rejects projection_years < 1."""
        wf_config = WorkflowConfig(
            name="invalid_projection",
            version="1.0",
            data_sources=DataSourceConfig(emission_factors="default"),
            scenarios=(ScenarioRef(role="scenario", reference="test"),),
            run_config=RunConfig(
                projection_years=0,
                start_year=2025,
                output_format="csv",
            ),
        )

        with pytest.raises(ValueError, match="projection_years"):
            from_workflow_config(wf_config)


# ============================================================================
# Test: OrchestratorRunner integration (AC-5)
# ============================================================================


class TestOrchestratorRunner:
    """Tests for OrchestratorRunner integration with run_workflow (AC-5)."""

    def test_runner_executes_workflow(self, short_workflow_config: WorkflowConfig):
        """OrchestratorRunner executes workflow through run_workflow (AC-5)."""
        runner = OrchestratorRunner()
        result = run_workflow(short_workflow_config, runner=runner)

        assert isinstance(result, WorkflowResult)
        assert result.success is True

    def test_runner_uses_workflow_bounds(self, short_workflow_config: WorkflowConfig):
        """OrchestratorRunner uses projection bounds from WorkflowConfig (AC-5)."""
        runner = OrchestratorRunner(step_pipeline=(counting_step,))
        result = run_workflow(short_workflow_config, runner=runner)

        assert result.success is True
        yearly_states = result.outputs.get("yearly_states", {})
        # Should have 3 years (2025, 2026, 2027)
        assert len(yearly_states) == 3
        assert 2025 in yearly_states
        assert 2026 in yearly_states
        assert 2027 in yearly_states

    def test_runner_executes_step_pipeline(self, short_workflow_config: WorkflowConfig):
        """OrchestratorRunner executes provided step pipeline (AC-5)."""
        runner = OrchestratorRunner(step_pipeline=(counting_step,))
        result = run_workflow(short_workflow_config, runner=runner)

        # Each year should increment count
        yearly_states = result.outputs.get("yearly_states", {})
        assert yearly_states[2025]["data"]["count"] == 1
        assert yearly_states[2026]["data"]["count"] == 2
        assert yearly_states[2027]["data"]["count"] == 3

    def test_runner_uses_provided_seed(self, short_workflow_config: WorkflowConfig):
        """OrchestratorRunner uses provided seed for determinism (AC-5)."""
        runner = OrchestratorRunner(seed=42)
        result = run_workflow(short_workflow_config, runner=runner)

        yearly_states = result.outputs.get("yearly_states", {})
        # Verify seeds are present and derived from master seed
        assert yearly_states[2025]["seed"] is not None
        assert yearly_states[2026]["seed"] is not None

    def test_runner_uses_initial_state(self, short_workflow_config: WorkflowConfig):
        """OrchestratorRunner uses provided initial state (AC-5)."""
        runner = OrchestratorRunner(
            initial_state={"starting_value": 100},
            step_pipeline=(counting_step,),
        )
        result = run_workflow(short_workflow_config, runner=runner)

        # Initial state should be carried forward
        yearly_states = result.outputs.get("yearly_states", {})
        assert yearly_states[2025]["data"]["starting_value"] == 100

    def test_runner_returns_workflow_result(
        self, short_workflow_config: WorkflowConfig
    ):
        """OrchestratorRunner returns proper WorkflowResult (AC-5)."""
        runner = OrchestratorRunner()
        result = run_workflow(short_workflow_config, runner=runner)

        assert isinstance(result, WorkflowResult)
        assert "yearly_states" in result.outputs
        assert "start_year" in result.metadata
        assert "end_year" in result.metadata

    def test_runner_handles_step_failure(self):
        """OrchestratorRunner handles step failures gracefully."""

        def failing_step(year: int, state: YearState) -> YearState:
            if year == 2026:
                raise RuntimeError("Intentional failure")
            return state

        config = WorkflowConfig(
            name="fail_test",
            version="1.0",
            data_sources=DataSourceConfig(emission_factors="default"),
            scenarios=(ScenarioRef(role="scenario", reference="test"),),
            run_config=RunConfig(projection_years=3, start_year=2025),
        )

        runner = OrchestratorRunner(step_pipeline=(failing_step,))
        result = run_workflow(config, runner=runner)

        assert result.success is False
        assert result.metadata.get("failed_year") == 2026
        assert len(result.errors) >= 1

    def test_runner_rejects_missing_run_config(self):
        """OrchestratorRunner rejects malformed requests."""
        runner = OrchestratorRunner()
        result = runner.run({})

        assert result.success is False
        assert "run_config" in result.errors[0]

    def test_runner_captures_manifest_fields_automatically(
        self, short_workflow_config: WorkflowConfig
    ):
        """Manifest capture fields are auto-populated at orchestrator boundary."""
        mapping_config = MappingConfig(
            mappings=(
                FieldMapping(
                    openfisca_name="income",
                    project_name="household_income",
                    direction="input",
                    pa_type=pa.float64(),
                ),
            ),
        )
        runner = OrchestratorRunner(
            assumption_defaults={"discount_rate": 0.03, "inflation": 0.02},
            assumption_overrides={"discount_rate": 0.04},
            policy={"tax": {"rate": 0.2}},
            mapping_config=mapping_config,
        )

        result = run_workflow(short_workflow_config, runner=runner)

        assert result.success is True
        assert "assumptions" in result.metadata
        assert "mappings" in result.metadata
        assert "policy" in result.metadata
        assert "warnings" in result.metadata
        assert len(result.metadata["assumptions"]) == 2
        assert result.metadata["mappings"][0]["openfisca_name"] == "income"
        assert result.metadata["policy"]["tax"]["rate"] == 0.2
        assert any("not marked as validated" in w for w in result.metadata["warnings"])

    def test_runner_captures_artifact_hashes_when_paths_provided(
        self,
        short_workflow_config: WorkflowConfig,
        tmp_path: Path,
    ) -> None:
        """Runner captures data/output hashes when artifact paths are provided."""
        input_file = tmp_path / "population.csv"
        output_file = tmp_path / "results.csv"
        input_file.write_text("id,income\n1,50000\n")
        output_file.write_text("id,tax\n1,5000\n")

        request = prepare_workflow_request(short_workflow_config)
        request["input_paths"] = {"population": str(input_file)}
        request["output_paths"] = {"results": str(output_file)}

        runner = OrchestratorRunner()
        result = runner.run(request)

        assert result.success is True
        assert result.metadata["data_hashes"] == {"population": hash_file(input_file)}
        assert result.metadata["output_hashes"] == {"results": hash_file(output_file)}

    def test_runner_rejects_invalid_artifact_paths_payload(self) -> None:
        """Runner rejects malformed input/output artifact path maps."""
        runner = OrchestratorRunner()
        result = runner.run(
            {
                "run_config": {"start_year": 2025, "projection_years": 1},
                "input_paths": ["not", "a", "mapping"],
            }
        )

        assert result.success is False
        assert "Invalid artifact paths" in result.errors[0]

    def test_runner_capture_payload_is_detached_from_mutations(
        self, short_workflow_config: WorkflowConfig
    ):
        """Captured metadata snapshots are detached from source payloads."""
        defaults = {"nested": {"value": 10}}
        overrides = {"nested": {"value": 20}}
        policy_params = {"policy": {"rate": 0.15}}

        runner = OrchestratorRunner(
            assumption_defaults=defaults,
            assumption_overrides=overrides,
            policy=policy_params,
        )
        result = run_workflow(short_workflow_config, runner=runner)

        defaults["nested"]["value"] = 999
        overrides["nested"]["value"] = 777
        policy_params["policy"]["rate"] = 0.99

        assumption_entry = result.metadata["assumptions"][0]
        assert assumption_entry["value"] == {"value": 20}
        assert result.metadata["policy"]["policy"]["rate"] == 0.15

    def test_runner_captures_lineage_metadata_automatically(
        self, short_workflow_config: WorkflowConfig
    ) -> None:
        """Lineage metadata is captured automatically for completed years."""
        runner = OrchestratorRunner(step_pipeline=(counting_step,))
        result = run_workflow(short_workflow_config, runner=runner)

        assert result.success is True
        parent_manifest_id = result.metadata["parent_manifest_id"]
        child_manifests = result.metadata["child_manifests"]

        assert isinstance(parent_manifest_id, str)
        uuid.UUID(parent_manifest_id)
        assert set(child_manifests) == {2025, 2026, 2027}
        assert len(child_manifests) == 3
        assert len(set(child_manifests.values())) == 3
        for child_id in child_manifests.values():
            uuid.UUID(child_id)

    def test_runner_lineage_for_ten_year_projection(
        self, workflow_config: WorkflowConfig
    ) -> None:
        """Lineage metadata contains all 10 yearly child links."""
        runner = OrchestratorRunner()
        result = run_workflow(workflow_config, runner=runner)

        assert result.success is True
        child_manifests = result.metadata["child_manifests"]
        assert len(child_manifests) == 10
        assert set(child_manifests) == set(range(2025, 2035))
        for child_id in child_manifests.values():
            uuid.UUID(child_id)

    def test_runner_lineage_on_failure_tracks_completed_years_only(self) -> None:
        """Failure path lineage metadata includes only completed years."""

        def failing_step(year: int, state: YearState) -> YearState:
            if year == 2026:
                raise RuntimeError("Intentional failure for lineage test")
            return state

        config = WorkflowConfig(
            name="lineage_fail_test",
            version="1.0",
            data_sources=DataSourceConfig(emission_factors="default"),
            scenarios=(ScenarioRef(role="scenario", reference="test"),),
            run_config=RunConfig(projection_years=3, start_year=2025),
        )
        runner = OrchestratorRunner(step_pipeline=(failing_step,))
        result = run_workflow(config, runner=runner)

        assert result.success is False
        uuid.UUID(result.metadata["parent_manifest_id"])
        child_manifests = result.metadata["child_manifests"]
        assert set(child_manifests) == {2025}
        uuid.UUID(child_manifests[2025])


# ============================================================================
# Test: Determinism across workflows (AC-4 + AC-5)
# ============================================================================


class TestDeterminismWithWorkflow:
    """Tests for deterministic execution through workflow API."""

    def test_same_workflow_same_result(self, short_workflow_config: WorkflowConfig):
        """Same workflow produces same result (AC-4)."""
        runner1 = OrchestratorRunner(seed=42, step_pipeline=(counting_step,))
        result1 = run_workflow(short_workflow_config, runner=runner1)

        runner2 = OrchestratorRunner(seed=42, step_pipeline=(counting_step,))
        result2 = run_workflow(short_workflow_config, runner=runner2)

        # Results should be identical
        assert result1.success == result2.success
        states1 = result1.outputs["yearly_states"]
        states2 = result2.outputs["yearly_states"]

        for year in states1:
            assert states1[year]["data"] == states2[year]["data"]
            assert states1[year]["seed"] == states2[year]["seed"]


# ============================================================================
# Test: End-to-end orchestrator through workflow
# ============================================================================


class TestEndToEndWorkflow:
    """End-to-end tests for orchestrator through workflow API."""

    def test_full_10_year_projection(self, workflow_config: WorkflowConfig):
        """Full 10-year projection completes successfully."""
        runner = OrchestratorRunner(step_pipeline=(counting_step,))
        result = run_workflow(workflow_config, runner=runner)

        assert result.success is True
        yearly_states = result.outputs["yearly_states"]
        assert len(yearly_states) == 10

        # Verify progression
        for i, year in enumerate(range(2025, 2035)):
            assert yearly_states[year]["data"]["count"] == i + 1

    def test_workflow_metadata_preserved(self, workflow_config: WorkflowConfig):
        """Workflow metadata is preserved in result."""
        runner = OrchestratorRunner(seed=12345)
        result = run_workflow(workflow_config, runner=runner)

        assert result.metadata["start_year"] == 2025
        assert result.metadata["end_year"] == 2034
        assert "seed" in result.metadata

    def test_prepare_workflow_request_integration(
        self, workflow_config: WorkflowConfig
    ):
        """prepare_workflow_request works with orchestrator."""
        request = prepare_workflow_request(workflow_config)

        # Request should have expected structure
        assert request["run_config"]["projection_years"] == 10
        assert request["run_config"]["start_year"] == 2025

        # Can use request with orchestrator
        runner = OrchestratorRunner()
        result = runner.run(request)

        assert result.success is True


# ============================================================================
# Test: Warning integration (Story 5-6, AC-7)
# ============================================================================


class TestOrchestratorWarningIntegration:
    """Integration tests for warning collection in OrchestratorRunner (Story 5-6)."""

    def test_unvalidated_scenario_produces_warning_in_manifest(self) -> None:
        """Run with unvalidated scenario produces warning in manifest metadata."""
        runner = OrchestratorRunner(
            scenario_name="test-unvalidated",
            scenario_version="v1",
            scenario_validated=False,
        )
        request = {
            "run_config": {
                "start_year": 2025,
                "projection_years": 1,
            },
        }
        result = runner.run(request)

        assert result.success is True
        warnings = result.metadata["warnings"]
        assert len(warnings) >= 1
        assert any("test-unvalidated" in w for w in warnings)
        assert any("not marked as validated" in w for w in warnings)

    def test_unvalidated_mapping_produces_warning_in_manifest(self) -> None:
        """Run with unvalidated mapping config produces warning in manifest."""
        mapping_config = MappingConfig(
            mappings=(),
            source_path=Path("/tmp/test-mapping.yaml"),
            is_validated=False,
        )
        runner = OrchestratorRunner(
            mapping_config=mapping_config,
            scenario_name="test",
            scenario_version="v1",
            scenario_validated=True,
        )
        request = {
            "run_config": {
                "start_year": 2025,
                "projection_years": 1,
            },
        }
        result = runner.run(request)

        assert result.success is True
        warnings = result.metadata["warnings"]
        assert any("test-mapping.yaml" in w for w in warnings)

    def test_unsupported_horizon_produces_warning_in_manifest(self) -> None:
        """Run with horizon > 20 years produces warning in manifest."""
        runner = OrchestratorRunner(
            scenario_name="test",
            scenario_version="v1",
            scenario_validated=True,
        )
        request = {
            "run_config": {
                "start_year": 2025,
                "projection_years": 25,
            },
        }
        result = runner.run(request)

        assert result.success is True
        warnings = result.metadata["warnings"]
        assert any("25 years" in w and "exceeds tested range" in w for w in warnings)

    def test_unsupported_population_produces_warning_in_manifest(self) -> None:
        """Run with large population produces warning in manifest."""
        runner = OrchestratorRunner(
            scenario_name="test",
            scenario_version="v1",
            scenario_validated=True,
        )
        request = {
            "run_config": {
                "start_year": 2025,
                "projection_years": 1,
                "population_size": 200_000,
            },
        }
        result = runner.run(request)

        assert result.success is True
        warnings = result.metadata["warnings"]
        assert any(
            "200,000" in w and "exceeds standard test coverage" in w for w in warnings
        )

    def test_multiple_warning_sources_all_appear(self) -> None:
        """Warnings from template, mapping, and config all appear in manifest."""
        mapping_config = MappingConfig(
            mappings=(),
            source_path=Path("/tmp/mapping.yaml"),
            is_validated=False,
        )
        runner = OrchestratorRunner(
            mapping_config=mapping_config,
            scenario_name="unvalidated-scenario",
            scenario_version="v1",
            scenario_validated=False,
            additional_warnings=["Custom warning from user"],
        )
        request = {
            "run_config": {
                "start_year": 2025,
                "projection_years": 25,
                "population_size": 200_000,
            },
        }
        result = runner.run(request)

        assert result.success is True
        warnings = result.metadata["warnings"]
        # Template warning
        assert any("unvalidated-scenario" in w for w in warnings)
        # Mapping warning
        assert any("mapping.yaml" in w for w in warnings)
        # Horizon warning
        assert any("25 years" in w for w in warnings)
        # Population warning
        assert any("200,000" in w for w in warnings)
        # Custom warning
        assert any("Custom warning from user" in w for w in warnings)

    def test_validated_scenario_no_template_warning(self) -> None:
        """Run with validated scenario produces no template warning."""
        runner = OrchestratorRunner(
            scenario_name="validated-scenario",
            scenario_version="v1",
            scenario_validated=True,
        )
        request = {
            "run_config": {
                "start_year": 2025,
                "projection_years": 1,
            },
        }
        result = runner.run(request)

        assert result.success is True
        warnings = result.metadata["warnings"]
        assert not any("not marked as validated" in w for w in warnings)

    def test_duplicate_warnings_are_deduplicated(self) -> None:
        """Duplicate warning strings appear only once in manifest (AC-4)."""
        duplicate_warning = "WARNING: Duplicate test warning"
        runner = OrchestratorRunner(
            scenario_name="test",
            scenario_version="v1",
            scenario_validated=True,
            additional_warnings=[duplicate_warning, duplicate_warning, duplicate_warning],
        )
        request = {
            "run_config": {
                "start_year": 2025,
                "projection_years": 1,
            },
        }
        result = runner.run(request)

        assert result.success is True
        warnings = result.metadata["warnings"]
        assert warnings.count(duplicate_warning) == 1
