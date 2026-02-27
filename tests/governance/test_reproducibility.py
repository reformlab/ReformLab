"""Tests for reproducibility check harness."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from reformlab.governance import (
    ReproducibilityResult,
    ReproducibilityValidationError,
    RunManifest,
    check_reproducibility,
)


class TestReproducibilityResult:
    """Test suite for ReproducibilityResult dataclass."""

    def test_immutability(self) -> None:
        """Result should be immutable frozen dataclass."""
        result = ReproducibilityResult(
            passed=True,
            hash_mismatches=[],
            missing_artifacts=[],
            rerun_seeds={"master": 42},
            original_seeds={"master": 42},
            year_range=(2025, 2027),
            tolerance_used=0.0,
        )

        with pytest.raises(FrozenInstanceError):
            result.passed = False  # type: ignore[misc]

    def test_details_passed(self) -> None:
        """Details should format PASSED result."""
        result = ReproducibilityResult(
            passed=True,
            hash_mismatches=[],
            missing_artifacts=[],
            rerun_seeds={"master": 42},
            original_seeds={"master": 42},
            year_range=(2025, 2027),
            tolerance_used=0.0,
        )

        details = result.details()
        assert "PASSED" in details
        assert "2025-2027" in details
        assert "Tolerance: 0.0" in details

    def test_details_failed_with_mismatches(self) -> None:
        """Details should format FAILED result with mismatches."""
        result = ReproducibilityResult(
            passed=False,
            hash_mismatches=["output_2025.csv", "output_2026.parquet"],
            missing_artifacts=[],
            rerun_seeds={"master": 42},
            original_seeds={"master": 42},
            year_range=(2025, 2027),
            tolerance_used=0.0,
        )

        details = result.details()
        assert "FAILED" in details
        assert "output_2025.csv" in details
        assert "output_2026.parquet" in details
        assert "Hash mismatches (2)" in details

    def test_details_failed_with_missing(self) -> None:
        """Details should format FAILED result with missing artifacts."""
        result = ReproducibilityResult(
            passed=False,
            hash_mismatches=[],
            missing_artifacts=["output_2027.csv"],
            rerun_seeds={"master": 42},
            original_seeds={"master": 42},
            year_range=(2025, 2027),
            tolerance_used=0.0,
        )

        details = result.details()
        assert "FAILED" in details
        assert "output_2027.csv" in details
        assert "Missing artifacts (1)" in details

    def test_details_includes_seeds(self) -> None:
        """Details should include seed information."""
        result = ReproducibilityResult(
            passed=True,
            hash_mismatches=[],
            missing_artifacts=[],
            rerun_seeds={"master": 42, "year_2025": 1001},
            original_seeds={"master": 42, "year_2025": 1001},
            year_range=(2025, 2027),
            tolerance_used=0.0,
        )

        details = result.details()
        assert "Original seeds:" in details
        assert "Rerun seeds:" in details
        assert "42" in details


class TestCheckReproducibility:
    """Test suite for check_reproducibility function."""

    def test_strict_comparison_passed(self, tmp_path: Path) -> None:
        """Check should pass when outputs match exactly."""
        # Create manifest with output hashes
        output_file = tmp_path / "output_2025.csv"
        output_file.write_text("year,value\n2025,100\n")

        # Compute actual hash
        from reformlab.governance.hashing import hash_file

        actual_hash = hash_file(output_file)

        manifest = RunManifest(
            manifest_id="12345678-1234-1234-1234-123456789abc",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            output_hashes={"output_2025.csv": actual_hash},
            seeds={"master": 42},
            child_manifests={2025: "22345678-1234-1234-1234-123456789abc"},
        )

        # Create rerun callable that does nothing (outputs already exist)
        def rerun_callable(**_: object) -> None:
            pass

        # Run reproducibility check
        result = check_reproducibility(
            manifest=manifest,
            input_paths={},
            output_paths={"output_2025.csv": output_file},
            rerun_callable=rerun_callable,
        )

        assert result.passed
        assert result.hash_mismatches == []
        assert result.missing_artifacts == []
        assert result.year_range == (2025, 2025)
        assert result.tolerance_used == 0.0

    def test_strict_comparison_failed_mismatch(self, tmp_path: Path) -> None:
        """Check should fail when output hash does not match."""
        # Create original output
        output_file = tmp_path / "output_2025.csv"
        output_file.write_text("year,value\n2025,100\n")

        manifest = RunManifest(
            manifest_id="12345678-1234-1234-1234-123456789abc",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            output_hashes={
                "output_2025.csv": "0" * 64  # Wrong hash
            },
            seeds={"master": 42},
            child_manifests={2025: "22345678-1234-1234-1234-123456789abc"},
        )

        def rerun_callable(**_: object) -> None:
            pass

        result = check_reproducibility(
            manifest=manifest,
            input_paths={},
            output_paths={"output_2025.csv": output_file},
            rerun_callable=rerun_callable,
        )

        assert not result.passed
        assert "output_2025.csv" in result.hash_mismatches
        assert result.missing_artifacts == []

    def test_strict_comparison_failed_missing(self, tmp_path: Path) -> None:
        """Check should fail when output file is missing."""
        manifest = RunManifest(
            manifest_id="12345678-1234-1234-1234-123456789abc",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            output_hashes={"output_2025.csv": "a" * 64},
            seeds={"master": 42},
            child_manifests={2025: "22345678-1234-1234-1234-123456789abc"},
        )

        def rerun_callable(**_: object) -> None:
            pass

        missing_file = tmp_path / "nonexistent.csv"

        result = check_reproducibility(
            manifest=manifest,
            input_paths={},
            output_paths={"output_2025.csv": missing_file},
            rerun_callable=rerun_callable,
        )

        assert not result.passed
        assert result.hash_mismatches == []
        assert "output_2025.csv" in result.missing_artifacts

    def test_tolerance_validation_negative(self, tmp_path: Path) -> None:
        """Check should reject negative tolerance."""
        manifest = RunManifest(
            manifest_id="12345678-1234-1234-1234-123456789abc",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            output_hashes={},
            seeds={"master": 42},
            child_manifests={2025: "22345678-1234-1234-1234-123456789abc"},
        )

        def rerun_callable(**_: object) -> None:
            pass

        with pytest.raises(
            ReproducibilityValidationError, match="tolerance must be >= 0"
        ):
            check_reproducibility(
                manifest=manifest,
                input_paths={},
                output_paths={},
                rerun_callable=rerun_callable,
                tolerance=-0.1,
            )

    def test_tolerance_validation_requires_reference(self, tmp_path: Path) -> None:
        """Check should require reference_output_paths when tolerance > 0."""
        manifest = RunManifest(
            manifest_id="12345678-1234-1234-1234-123456789abc",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            output_hashes={},
            seeds={"master": 42},
            child_manifests={2025: "22345678-1234-1234-1234-123456789abc"},
        )

        def rerun_callable(**_: object) -> None:
            pass

        with pytest.raises(
            ReproducibilityValidationError,
            match="reference_output_paths is required when tolerance > 0",
        ):
            check_reproducibility(
                manifest=manifest,
                input_paths={},
                output_paths={},
                rerun_callable=rerun_callable,
                tolerance=0.01,
            )

    def test_rerun_callable_receives_manifest_context(self, tmp_path: Path) -> None:
        """Harness should pass manifest-derived rerun context to callable."""
        from reformlab.governance.hashing import hash_file

        input_file = tmp_path / "input.csv"
        input_file.write_text("id,value\n1,10\n")
        output_file = tmp_path / "output.csv"
        output_file.write_text("year,value\n2025,100\n")

        manifest = RunManifest(
            manifest_id="12345678-1234-1234-1234-123456789abc",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="scenario-v1",
            data_hashes={"input.csv": hash_file(input_file)},
            output_hashes={"output.csv": hash_file(output_file)},
            seeds={"master": 42, "year_2025": 2047},
            parameters={"population": 1000},
            step_pipeline=["prepare", "compute"],
            child_manifests={2025: "22345678-1234-1234-1234-123456789abc"},
        )

        captured_context: dict[str, object] = {}

        def rerun_callable(**context: object) -> None:
            captured_context.update(context)

        result = check_reproducibility(
            manifest=manifest,
            input_paths={"input.csv": input_file},
            output_paths={"output.csv": output_file},
            rerun_callable=rerun_callable,
        )

        assert result.passed
        assert captured_context["seeds"] == {"master": 42, "year_2025": 2047}
        assert captured_context["parameters"] == {"population": 1000}
        assert captured_context["scenario_version"] == "scenario-v1"
        assert captured_context["step_pipeline"] == ["prepare", "compute"]
        assert captured_context["year_range"] == (2025, 2025)
        assert captured_context["input_paths"] == {"input.csv": input_file}

    def test_missing_required_input_path_keys_raise(self, tmp_path: Path) -> None:
        """Missing manifest data_hash keys in input_paths should fail fast."""
        manifest = RunManifest(
            manifest_id="12345678-1234-1234-1234-123456789abc",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            data_hashes={"required-input": "a" * 64},
            output_hashes={},
            seeds={"master": 42},
            child_manifests={2025: "22345678-1234-1234-1234-123456789abc"},
        )

        def rerun_callable(**_: object) -> None:
            pytest.fail("rerun_callable should not be invoked when inputs are invalid")

        with pytest.raises(
            ReproducibilityValidationError,
            match="Missing input_paths keys required by manifest.data_hashes",
        ):
            check_reproducibility(
                manifest=manifest,
                input_paths={},
                output_paths={},
                rerun_callable=rerun_callable,
            )

    def test_tolerance_comparison_parquet(self, tmp_path: Path) -> None:
        """Check should pass when parquet outputs match within tolerance."""
        # Create reference output with original values
        reference_file = tmp_path / "reference_2025.parquet"
        reference_table = pa.table(
            {
                "year": pa.array([2025, 2025, 2025]),
                "value": pa.array([100.0, 200.0, 300.0]),
            }
        )
        pq.write_table(reference_table, reference_file)

        # Create rerun output with slightly different values
        rerun_file = tmp_path / "rerun_2025.parquet"
        rerun_table = pa.table(
            {
                "year": pa.array([2025, 2025, 2025]),
                "value": pa.array([100.001, 200.002, 300.003]),
            }
        )
        pq.write_table(rerun_table, rerun_file)

        # Hash files
        from reformlab.governance.hashing import hash_file

        reference_hash = hash_file(reference_file)
        rerun_hash = hash_file(rerun_file)

        # Hashes should differ
        assert reference_hash != rerun_hash

        manifest = RunManifest(
            manifest_id="12345678-1234-1234-1234-123456789abc",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            output_hashes={"output_2025.parquet": reference_hash},
            seeds={"master": 42},
            child_manifests={2025: "22345678-1234-1234-1234-123456789abc"},
        )

        def rerun_callable(**_: object) -> None:
            pass

        # Check should pass with tolerance 0.01
        result = check_reproducibility(
            manifest=manifest,
            input_paths={},
            output_paths={"output_2025.parquet": rerun_file},
            rerun_callable=rerun_callable,
            tolerance=0.01,
            reference_output_paths={"output_2025.parquet": reference_file},
        )

        assert result.passed
        assert result.hash_mismatches == []
        assert result.tolerance_used == 0.01

    def test_tolerance_comparison_csv(self, tmp_path: Path) -> None:
        """Check should pass when CSV outputs match within tolerance."""
        # Create reference CSV
        reference_file = tmp_path / "reference_2025.csv"
        reference_file.write_text("year,value\n2025,100.0\n2025,200.0\n")

        # Create rerun CSV with slightly different values
        rerun_file = tmp_path / "rerun_2025.csv"
        rerun_file.write_text("year,value\n2025,100.001\n2025,200.002\n")

        # Hash files
        from reformlab.governance.hashing import hash_file

        reference_hash = hash_file(reference_file)
        rerun_hash = hash_file(rerun_file)

        # Hashes should differ
        assert reference_hash != rerun_hash

        manifest = RunManifest(
            manifest_id="12345678-1234-1234-1234-123456789abc",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            output_hashes={"output_2025.csv": reference_hash},
            seeds={"master": 42},
            child_manifests={2025: "22345678-1234-1234-1234-123456789abc"},
        )

        def rerun_callable(**_: object) -> None:
            pass

        # Check should pass with tolerance 0.01
        result = check_reproducibility(
            manifest=manifest,
            input_paths={},
            output_paths={"output_2025.csv": rerun_file},
            rerun_callable=rerun_callable,
            tolerance=0.01,
            reference_output_paths={"output_2025.csv": reference_file},
        )

        assert result.passed
        assert result.hash_mismatches == []
        assert result.tolerance_used == 0.01

    def test_tolerance_comparison_fails_outside_tolerance(self, tmp_path: Path) -> None:
        """Check should fail when differences exceed tolerance."""
        # Create reference output
        reference_file = tmp_path / "reference_2025.parquet"
        reference_table = pa.table(
            {
                "year": pa.array([2025]),
                "value": pa.array([100.0]),
            }
        )
        pq.write_table(reference_table, reference_file)

        # Create rerun output with large difference
        rerun_file = tmp_path / "rerun_2025.parquet"
        rerun_table = pa.table(
            {
                "year": pa.array([2025]),
                "value": pa.array([110.0]),
            }
        )
        pq.write_table(rerun_table, rerun_file)

        # Hash files
        from reformlab.governance.hashing import hash_file

        reference_hash = hash_file(reference_file)

        manifest = RunManifest(
            manifest_id="12345678-1234-1234-1234-123456789abc",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            output_hashes={"output_2025.parquet": reference_hash},
            seeds={"master": 42},
            child_manifests={2025: "22345678-1234-1234-1234-123456789abc"},
        )

        def rerun_callable(**_: object) -> None:
            pass

        # Check should fail with small tolerance
        result = check_reproducibility(
            manifest=manifest,
            input_paths={},
            output_paths={"output_2025.parquet": rerun_file},
            rerun_callable=rerun_callable,
            tolerance=0.01,
            reference_output_paths={"output_2025.parquet": reference_file},
        )

        assert not result.passed
        assert "output_2025.parquet" in result.hash_mismatches

    def test_tolerance_incomplete_reference_outputs_are_explicit(
        self, tmp_path: Path
    ) -> None:
        """Missing tolerance reference artifacts should be explicit diagnostics."""
        from reformlab.governance.hashing import hash_file

        reference_file = tmp_path / "reference_2025.parquet"
        rerun_file = tmp_path / "rerun_2025.parquet"
        pq.write_table(
            pa.table({"year": pa.array([2025]), "value": pa.array([100.0])}),
            reference_file,
        )
        pq.write_table(
            pa.table({"year": pa.array([2025]), "value": pa.array([100.2])}),
            rerun_file,
        )

        manifest = RunManifest(
            manifest_id="12345678-1234-1234-1234-123456789abc",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            output_hashes={"output_2025.parquet": hash_file(reference_file)},
            seeds={"master": 42},
            child_manifests={2025: "22345678-1234-1234-1234-123456789abc"},
        )

        def rerun_callable(**_: object) -> None:
            pass

        result = check_reproducibility(
            manifest=manifest,
            input_paths={},
            output_paths={"output_2025.parquet": rerun_file},
            rerun_callable=rerun_callable,
            tolerance=0.5,
            reference_output_paths={},
        )

        assert not result.passed
        assert "output_2025.parquet" in result.hash_mismatches
        assert "reference:output_2025.parquet" in result.missing_artifacts

    def test_tolerance_comparison_requires_exact_non_numeric(
        self, tmp_path: Path
    ) -> None:
        """Check should fail when non-numeric columns differ."""
        # Create reference output
        reference_file = tmp_path / "reference_2025.parquet"
        reference_table = pa.table(
            {
                "year": pa.array([2025]),
                "label": pa.array(["A"]),
                "value": pa.array([100.0]),
            }
        )
        pq.write_table(reference_table, reference_file)

        # Create rerun output with different label
        rerun_file = tmp_path / "rerun_2025.parquet"
        rerun_table = pa.table(
            {
                "year": pa.array([2025]),
                "label": pa.array(["B"]),
                "value": pa.array([100.0]),
            }
        )
        pq.write_table(rerun_table, rerun_file)

        # Hash files
        from reformlab.governance.hashing import hash_file

        reference_hash = hash_file(reference_file)

        manifest = RunManifest(
            manifest_id="12345678-1234-1234-1234-123456789abc",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            output_hashes={"output_2025.parquet": reference_hash},
            seeds={"master": 42},
            child_manifests={2025: "22345678-1234-1234-1234-123456789abc"},
        )

        def rerun_callable(**_: object) -> None:
            pass

        # Check should fail even with tolerance
        result = check_reproducibility(
            manifest=manifest,
            input_paths={},
            output_paths={"output_2025.parquet": rerun_file},
            rerun_callable=rerun_callable,
            tolerance=0.01,
            reference_output_paths={"output_2025.parquet": reference_file},
        )

        assert not result.passed
        assert "output_2025.parquet" in result.hash_mismatches

    def test_year_range_extraction(self, tmp_path: Path) -> None:
        """Check should extract year range from child_manifests."""
        manifest = RunManifest(
            manifest_id="12345678-1234-1234-1234-123456789abc",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            output_hashes={},
            seeds={"master": 42},
            child_manifests={
                2025: "22345678-1234-1234-1234-123456789abc",
                2026: "32345678-1234-1234-1234-123456789abc",
                2027: "42345678-1234-1234-1234-123456789abc",
            },
        )

        def rerun_callable(**_: object) -> None:
            pass

        result = check_reproducibility(
            manifest=manifest,
            input_paths={},
            output_paths={},
            rerun_callable=rerun_callable,
        )

        assert result.year_range == (2025, 2027)

    def test_year_range_empty_child_manifests(self, tmp_path: Path) -> None:
        """Check should handle empty child_manifests."""
        manifest = RunManifest(
            manifest_id="12345678-1234-1234-1234-123456789abc",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            output_hashes={},
            seeds={"master": 42},
            child_manifests={},
        )

        def rerun_callable(**_: object) -> None:
            pass

        result = check_reproducibility(
            manifest=manifest,
            input_paths={},
            output_paths={},
            rerun_callable=rerun_callable,
        )

        assert result.year_range == (0, 0)


class TestReproducibilityIntegration:
    """Integration tests for full reproducibility cycle."""

    def test_full_reproducibility_cycle_with_orchestrator(self, tmp_path: Path) -> None:
        """Demonstrate complete reproducibility cycle with orchestrator.

        This test shows:
        1. Run orchestrator with fixed seed
        2. Capture manifest with input/output hashes
        3. Re-execute via harness
        4. Verify bit-identical outputs
        """
        from reformlab.governance.hashing import hash_output_artifacts
        from reformlab.orchestrator.runner import Orchestrator
        from reformlab.orchestrator.types import OrchestratorConfig, YearState

        # Create a simple step that produces deterministic outputs
        def simple_step(year: int, state: YearState) -> YearState:
            """Simple step that stores year and seed in data."""
            new_data = dict(state.data)
            new_data["year"] = year
            new_data["seed"] = state.seed
            return YearState(
                year=year,
                data=new_data,
                seed=state.seed,
                metadata=state.metadata,
            )

        # Create orchestrator config with fixed seed
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2026,
            initial_state={},
            seed=42,
            step_pipeline=[simple_step],
        )

        # Run orchestrator first time
        orchestrator = Orchestrator(config)
        result1 = orchestrator.run()
        assert result1.success

        # Write outputs to files
        output_paths: dict[str, Path] = {}
        for year in [2025, 2026]:
            output_file = tmp_path / f"original_output_{year}.parquet"
            year_state = result1.yearly_states[year]

            # Create simple output table from year state
            table = pa.table(
                {
                    "year": pa.array([year]),
                    "seed": pa.array([year_state.seed or 0]),
                }
            )
            pq.write_table(table, output_file)
            output_paths[f"output_{year}.parquet"] = output_file

        # Hash outputs
        output_hashes = hash_output_artifacts(output_paths)

        # Create manifest
        manifest = RunManifest(
            manifest_id="12345678-1234-1234-1234-123456789abc",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            output_hashes=output_hashes,
            seeds={"master": 42},
            child_manifests={
                2025: "22345678-1234-1234-1234-123456789abc",
                2026: "32345678-1234-1234-1234-123456789abc",
            },
            step_pipeline=["simple_step"],
        )

        # Create rerun callable that re-executes orchestrator
        rerun_output_paths: dict[str, Path] = {}

        def rerun_callable(**_: object) -> None:
            # Re-run orchestrator with same config
            rerun_orchestrator = Orchestrator(config)
            rerun_result = rerun_orchestrator.run()
            assert rerun_result.success

            # Write rerun outputs
            for year in [2025, 2026]:
                rerun_file = tmp_path / f"rerun_output_{year}.parquet"
                year_state = rerun_result.yearly_states[year]

                table = pa.table(
                    {
                        "year": pa.array([year]),
                        "seed": pa.array([year_state.seed or 0]),
                    }
                )
                pq.write_table(table, rerun_file)
                rerun_output_paths[f"output_{year}.parquet"] = rerun_file

        # Run reproducibility check
        result = check_reproducibility(
            manifest=manifest,
            input_paths={},
            output_paths=rerun_output_paths,
            rerun_callable=rerun_callable,
        )

        # Verify bit-identical outputs
        assert result.passed
        assert result.hash_mismatches == []
        assert result.missing_artifacts == []
        assert result.year_range == (2025, 2026)
        assert result.original_seeds == {"master": 42}
        assert result.rerun_seeds == {"master": 42}
