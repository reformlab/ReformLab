"""Tests for panel output generation and export.

Story 3-7: Produce Scenario-Year Panel Output
Tests cover:
- Panel from successful multi-year run (AC-1)
- Panel from partial run (AC-1, AC-6)
- Panel from empty run (AC-6)
- CSV export and reload (AC-2)
- Parquet export and reload (AC-3)
- Panel metadata (AC-5)
- Panel comparison (AC-4)
"""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa

from reformlab.computation.types import ComputationResult
from reformlab.orchestrator.computation_step import COMPUTATION_RESULT_KEY
from reformlab.orchestrator.panel import PanelOutput, compare_panels
from reformlab.orchestrator.runner import SEED_LOG_KEY, STEP_EXECUTION_LOG_KEY
from reformlab.orchestrator.types import OrchestratorResult, YearState


def make_computation_result(
    year: int,
    num_households: int = 5,
    include_household_id: bool = True,
    include_person_id: bool = False,
) -> ComputationResult:
    """Create a test ComputationResult with output_fields table."""
    arrays: dict[str, pa.Array] = {}
    if include_household_id:
        arrays["household_id"] = pa.array(range(num_households))
    if include_person_id:
        arrays["person_id"] = pa.array(range(1000, 1000 + num_households))
    arrays["income"] = pa.array([50000.0 + i * 1000 for i in range(num_households)])
    arrays["tax"] = pa.array([5000.0 + i * 100 for i in range(num_households)])

    return ComputationResult(
        output_fields=pa.table(arrays),
        adapter_version="test-adapter-1.0.0",
        period=year,
    )


def make_orchestrator_result(
    years: list[int],
    num_households: int = 5,
    failed_year: int | None = None,
    seed: int | None = 42,
    include_household_id: bool = True,
    include_person_id: bool = False,
) -> OrchestratorResult:
    """Create a test OrchestratorResult with computation results for each year."""
    yearly_states: dict[int, YearState] = {}
    for year in years:
        comp_result = make_computation_result(
            year,
            num_households,
            include_household_id,
            include_person_id,
        )
        yearly_states[year] = YearState(
            year=year,
            data={COMPUTATION_RESULT_KEY: comp_result},
            seed=seed + year if seed else None,
            metadata={},
        )

    metadata = {
        "start_year": min(years) if years else 2020,
        "end_year": max(years) if years else 2029,
        "seed": seed,
        "step_pipeline": ["step1", "computation"],
        SEED_LOG_KEY: {y: seed + y if seed else None for y in years},
        STEP_EXECUTION_LOG_KEY: {y: ["step1", "computation"] for y in years},
    }

    errors = []
    if failed_year:
        errors = [f"Failure at year {failed_year}"]

    return OrchestratorResult(
        success=failed_year is None,
        yearly_states=yearly_states,
        errors=errors,
        failed_year=failed_year,
        metadata=metadata,
    )


class TestPanelOutputFromOrchestratorResult:
    """Test PanelOutput.from_orchestrator_result factory (AC-1, AC-5, AC-6)."""

    def test_panel_from_successful_10_year_run(self) -> None:
        """AC-1: Panel contains one row per household per completed year."""
        years = list(range(2020, 2030))  # 10 years
        num_households = 5
        result = make_orchestrator_result(years, num_households)

        panel = PanelOutput.from_orchestrator_result(result)

        # Total rows = N * 10
        assert panel.table.num_rows == num_households * len(years)
        assert panel.shape == (num_households * len(years), panel.table.num_columns)

        # Each row includes year and household_id columns
        assert "year" in panel.table.column_names
        assert "household_id" in panel.table.column_names

        # Verify all years are present
        year_values = panel.table.column("year").to_pylist()
        for year in years:
            assert year_values.count(year) == num_households

        # Verify household_id present for each year
        for year in years:
            year_mask = pa.compute.equal(panel.table.column("year"), year)
            year_rows = panel.table.filter(year_mask)
            household_ids = sorted(year_rows.column("household_id").to_pylist())
            assert household_ids == list(range(num_households))

    def test_panel_from_partial_run(self) -> None:
        """AC-1, AC-6: Partial run includes completed years only."""
        completed_years = [2020, 2021, 2022]
        num_households = 3
        result = make_orchestrator_result(
            completed_years,
            num_households,
            failed_year=2023,
        )

        panel = PanelOutput.from_orchestrator_result(result)

        # Row count equals sum of rows across completed years only
        assert panel.table.num_rows == num_households * len(completed_years)

        # Metadata indicates partial completion
        assert panel.metadata.get("partial") is True
        assert "errors" in panel.metadata
        assert len(panel.metadata["errors"]) > 0

    def test_panel_from_empty_run(self) -> None:
        """AC-6: Empty run produces zero rows with key columns."""
        result = OrchestratorResult(
            success=False,
            yearly_states={},
            errors=["Failed on first year"],
            failed_year=2020,
            metadata={
                "start_year": 2020,
                "end_year": 2029,
            },
        )

        panel = PanelOutput.from_orchestrator_result(result)

        # Zero rows
        assert panel.table.num_rows == 0

        # Key columns present
        assert "year" in panel.table.column_names
        assert "household_id" in panel.table.column_names

        # Error information preserved
        assert panel.metadata.get("partial") is True
        assert "errors" in panel.metadata

    def test_panel_metadata_includes_orchestrator_metadata(self) -> None:
        """AC-5: Panel metadata includes orchestrator run metadata."""
        years = [2020, 2021]
        result = make_orchestrator_result(years, seed=12345)

        panel = PanelOutput.from_orchestrator_result(result)

        # Check required metadata fields
        assert panel.metadata["start_year"] == 2020
        # end_year from fixture is max(years) = 2021
        assert panel.metadata["end_year"] == 2021
        assert panel.metadata["seed"] == 12345
        assert panel.metadata["step_pipeline"] == ["step1", "computation"]

        # Check Story 3-6 trace keys are carried forward
        assert SEED_LOG_KEY in panel.metadata
        assert STEP_EXECUTION_LOG_KEY in panel.metadata

    def test_panel_shape_property(self) -> None:
        """PanelOutput.shape returns (rows, columns)."""
        result = make_orchestrator_result([2020], num_households=10)
        panel = PanelOutput.from_orchestrator_result(result)

        assert panel.shape == (10, panel.table.num_columns)

    def test_panel_maps_person_id_to_household_id_when_missing(self) -> None:
        """AC-1: person_id can be normalized to household_id when needed."""
        result = make_orchestrator_result(
            [2020],
            num_households=3,
            include_household_id=False,
            include_person_id=True,
        )

        panel = PanelOutput.from_orchestrator_result(result)

        assert "household_id" in panel.table.column_names
        assert panel.table.column("household_id").to_pylist() == [1000, 1001, 1002]

    def test_panel_builds_fallback_household_id_when_no_id_columns(self) -> None:
        """AC-1: household_id is synthesized when no ID columns are provided."""
        result = make_orchestrator_result(
            [2020],
            num_households=3,
            include_household_id=False,
            include_person_id=False,
        )

        panel = PanelOutput.from_orchestrator_result(result)

        assert "household_id" in panel.table.column_names
        assert panel.table.column("household_id").to_pylist() == [0, 1, 2]


class TestPanelOutputCsvExport:
    """Test CSV export functionality (AC-2)."""

    def test_export_to_csv_creates_file(self, tmp_path: Path) -> None:
        """CSV export creates a readable file."""
        result = make_orchestrator_result([2020, 2021], num_households=3)
        panel = PanelOutput.from_orchestrator_result(result)

        csv_path = tmp_path / "panel.csv"
        returned_path = panel.to_csv(csv_path)

        assert returned_path == csv_path
        assert csv_path.exists()

    def test_csv_roundtrip_preserves_data(self, tmp_path: Path) -> None:
        """AC-2: CSV roundtrip preserves column names and row counts."""
        result = make_orchestrator_result([2020, 2021, 2022], num_households=5)
        panel = PanelOutput.from_orchestrator_result(result)

        csv_path = tmp_path / "panel.csv"
        panel.to_csv(csv_path)

        # Read back with pyarrow
        import pyarrow.csv as pa_csv

        imported_table = pa_csv.read_csv(csv_path)

        # Column names match
        assert imported_table.column_names == panel.table.column_names

        # Row count matches
        assert imported_table.num_rows == panel.table.num_rows

    def test_csv_numeric_values_roundtrip(self, tmp_path: Path) -> None:
        """AC-2: Numeric values round-trip without corruption."""
        result = make_orchestrator_result([2020], num_households=3)
        panel = PanelOutput.from_orchestrator_result(result)

        csv_path = tmp_path / "panel.csv"
        panel.to_csv(csv_path)

        import pyarrow.csv as pa_csv

        imported_table = pa_csv.read_csv(csv_path)

        # Check numeric values are preserved
        original_income = panel.table.column("income").to_pylist()
        imported_income = imported_table.column("income").to_pylist()
        assert imported_income == original_income

    def test_csv_string_values_roundtrip(self, tmp_path: Path) -> None:
        """AC-2: UTF-8 strings round-trip without corruption."""
        panel = PanelOutput(
            table=pa.table(
                {
                    "household_id": pa.array([1, 2], type=pa.int64()),
                    "year": pa.array([2020, 2020], type=pa.int64()),
                    "segment": pa.array(["ménage_1", "ménage_2"]),
                }
            ),
            metadata={},
        )

        csv_path = tmp_path / "panel.csv"
        panel.to_csv(csv_path)

        import pyarrow.csv as pa_csv

        imported_table = pa_csv.read_csv(csv_path)
        assert imported_table.column("segment").to_pylist() == ["ménage_1", "ménage_2"]


class TestPanelOutputParquetExport:
    """Test Parquet export functionality (AC-3)."""

    def test_export_to_parquet_creates_file(self, tmp_path: Path) -> None:
        """Parquet export creates a readable file."""
        result = make_orchestrator_result([2020, 2021], num_households=3)
        panel = PanelOutput.from_orchestrator_result(result)

        parquet_path = tmp_path / "panel.parquet"
        returned_path = panel.to_parquet(parquet_path)

        assert returned_path == parquet_path
        assert parquet_path.exists()

    def test_parquet_roundtrip_preserves_schema(self, tmp_path: Path) -> None:
        """AC-3: Parquet roundtrip preserves Arrow schema/types."""
        result = make_orchestrator_result([2020, 2021], num_households=5)
        panel = PanelOutput.from_orchestrator_result(result)

        parquet_path = tmp_path / "panel.parquet"
        panel.to_parquet(parquet_path)

        # Read back with pyarrow
        imported_table = pa.parquet.read_table(parquet_path)

        # Schema matches (column names and types)
        assert imported_table.schema == panel.table.schema

        # Row count matches
        assert imported_table.num_rows == panel.table.num_rows

    def test_parquet_includes_metadata(self, tmp_path: Path) -> None:
        """AC-3: Parquet file includes panel format metadata."""
        result = make_orchestrator_result([2020], num_households=3)
        panel = PanelOutput.from_orchestrator_result(result)

        parquet_path = tmp_path / "panel.parquet"
        panel.to_parquet(parquet_path)

        # Read parquet metadata
        pq_file = pa.parquet.ParquetFile(parquet_path)
        metadata = pq_file.schema_arrow.metadata

        # Check for panel format version
        assert metadata is not None
        assert b"reformlab_panel_version" in metadata


class TestComparePanels:
    """Test panel comparison functionality (AC-4)."""

    def test_compare_identical_panels(self) -> None:
        """Comparing identical panels produces all 'both' markers."""
        result = make_orchestrator_result([2020, 2021], num_households=3)
        baseline = PanelOutput.from_orchestrator_result(result)
        reform = PanelOutput.from_orchestrator_result(result)

        comparison = compare_panels(baseline, reform)

        # All rows should have origin 'both'
        origins = comparison.table.column("_origin").to_pylist()
        assert all(o == "both" for o in origins)

        # Row count matches original
        assert comparison.table.num_rows == baseline.table.num_rows

    def test_compare_disjoint_panels(self) -> None:
        """Comparing disjoint panels marks origin correctly."""
        baseline_result = make_orchestrator_result([2020], num_households=2)
        reform_result = make_orchestrator_result([2021], num_households=2)

        baseline = PanelOutput.from_orchestrator_result(baseline_result)
        reform = PanelOutput.from_orchestrator_result(reform_result)

        comparison = compare_panels(baseline, reform)

        # Should have rows from both with correct origin markers
        origins = comparison.table.column("_origin").to_pylist()
        assert "baseline_only" in origins or "reform_only" in origins

    def test_compare_overlapping_panels(self) -> None:
        """Comparing overlapping panels handles all cases."""
        # Baseline has years 2020, 2021
        baseline_result = make_orchestrator_result([2020, 2021], num_households=2)
        # Reform has years 2021, 2022
        reform_result = make_orchestrator_result([2021, 2022], num_households=2)

        baseline = PanelOutput.from_orchestrator_result(baseline_result)
        reform = PanelOutput.from_orchestrator_result(reform_result)

        comparison = compare_panels(baseline, reform)

        origins = comparison.table.column("_origin").to_pylist()

        # Should have all three types
        assert "baseline_only" in origins  # 2020 only in baseline
        assert "reform_only" in origins  # 2022 only in reform
        assert "both" in origins  # 2021 in both

    def test_compare_produces_numeric_deltas(self) -> None:
        """AC-4: Numeric deltas are computable for shared numeric fields."""
        baseline_result = make_orchestrator_result([2020], num_households=3, seed=42)
        reform_result = make_orchestrator_result([2020], num_households=3, seed=42)

        baseline = PanelOutput.from_orchestrator_result(baseline_result)
        reform = PanelOutput.from_orchestrator_result(reform_result)

        comparison = compare_panels(baseline, reform)

        # Delta columns should exist for numeric fields
        assert "_delta_income" in comparison.table.column_names
        assert "_delta_tax" in comparison.table.column_names

    def test_compare_metadata_preserves_provenance(self) -> None:
        """AC-4: Comparison metadata preserves baseline/reform provenance."""
        baseline_result = make_orchestrator_result([2020], seed=100)
        reform_result = make_orchestrator_result([2020], seed=200)

        baseline = PanelOutput.from_orchestrator_result(baseline_result)
        reform = PanelOutput.from_orchestrator_result(reform_result)

        comparison = compare_panels(baseline, reform)

        # Metadata should include baseline and reform info
        assert "baseline_metadata" in comparison.metadata
        assert "reform_metadata" in comparison.metadata
        assert comparison.metadata["baseline_metadata"]["seed"] == 100
        assert comparison.metadata["reform_metadata"]["seed"] == 200

    def test_compare_handles_key_only_tables(self) -> None:
        """AC-4: Missing household-years are flagged even with key-only tables."""
        baseline = PanelOutput(
            table=pa.table(
                {
                    "household_id": pa.array([1], type=pa.int64()),
                    "year": pa.array([2020], type=pa.int64()),
                }
            ),
            metadata={},
        )
        reform = PanelOutput(
            table=pa.table(
                {
                    "household_id": pa.array([1], type=pa.int64()),
                    "year": pa.array([2021], type=pa.int64()),
                }
            ),
            metadata={},
        )

        comparison = compare_panels(baseline, reform)
        origins = sorted(comparison.table.column("_origin").to_pylist())

        assert origins == ["baseline_only", "reform_only"]

    def test_compare_origin_is_not_derived_from_null_data_values(self) -> None:
        """AC-4: Null values in compared fields do not alter origin markers."""
        baseline = PanelOutput(
            table=pa.table(
                {
                    "household_id": pa.array([1], type=pa.int64()),
                    "year": pa.array([2020], type=pa.int64()),
                    "income": pa.array([None], type=pa.float64()),
                }
            ),
            metadata={},
        )
        reform = PanelOutput(
            table=pa.table(
                {
                    "household_id": pa.array([1], type=pa.int64()),
                    "year": pa.array([2020], type=pa.int64()),
                    "income": pa.array([100.0], type=pa.float64()),
                }
            ),
            metadata={},
        )

        comparison = compare_panels(baseline, reform)
        origins = comparison.table.column("_origin").to_pylist()

        assert origins == ["both"]
