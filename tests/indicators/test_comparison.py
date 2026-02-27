"""Tests for scenario comparison functionality.

Story 4.5: Implement Scenario Comparison Tables

Tests cover:
- Side-by-side comparison with 2 scenarios (AC-1)
- Side-by-side comparison with 3+ scenarios (AC-1)
- Delta computation correctness (absolute and percentage) (AC-2)
- Input contract validation (AC-3)
- CSV export and round-trip (AC-4)
- Parquet export and round-trip (AC-5)
- Metadata preservation (AC-6)
- Mismatched dimension handling (AC-7)
- Stable PyArrow table contract (AC-8)
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pyarrow as pa
import pyarrow.csv as pa_csv
import pyarrow.parquet as pq
import pytest

from reformlab.indicators.comparison import (
    ComparisonConfig,
    ScenarioInput,
    compare_scenarios,
)
from reformlab.indicators.distributional import compute_distributional_indicators
from reformlab.indicators.fiscal import compute_fiscal_indicators
from reformlab.indicators.types import (
    DistributionalConfig,
    FiscalConfig,
    IndicatorResult,
)
from reformlab.orchestrator.panel import PanelOutput


@pytest.fixture
def baseline_scenario_distributional(
    simple_income_distribution_panel: PanelOutput,
) -> IndicatorResult:
    """Baseline scenario with distributional indicators."""
    return compute_distributional_indicators(simple_income_distribution_panel)


@pytest.fixture
def reform_scenario_distributional() -> IndicatorResult:
    """Reform scenario with distributional indicators (higher tax)."""
    num_households = 100
    household_ids = list(range(num_households))
    incomes = [10000.0 + i * 1000.0 for i in range(num_households)]
    # Higher taxes in reform scenario
    taxes = [1500.0 + i * 120.0 for i in range(num_households)]
    years = [2020] * num_households

    table = pa.table(
        {
            "household_id": pa.array(household_ids, type=pa.int64()),
            "year": pa.array(years, type=pa.int64()),
            "income": pa.array(incomes, type=pa.float64()),
            "tax": pa.array(taxes, type=pa.float64()),
        }
    )

    panel = PanelOutput(
        table=table,
        metadata={"start_year": 2020, "end_year": 2020, "seed": 43},
    )
    return compute_distributional_indicators(panel)


@pytest.fixture
def reform_b_scenario_distributional() -> IndicatorResult:
    """Second reform scenario with distributional indicators (even higher tax)."""
    num_households = 100
    household_ids = list(range(num_households))
    incomes = [10000.0 + i * 1000.0 for i in range(num_households)]
    # Even higher taxes in reform_b scenario
    taxes = [2000.0 + i * 150.0 for i in range(num_households)]
    years = [2020] * num_households

    table = pa.table(
        {
            "household_id": pa.array(household_ids, type=pa.int64()),
            "year": pa.array(years, type=pa.int64()),
            "income": pa.array(incomes, type=pa.float64()),
            "tax": pa.array(taxes, type=pa.float64()),
        }
    )

    panel = PanelOutput(
        table=table,
        metadata={"start_year": 2020, "end_year": 2020, "seed": 44},
    )
    return compute_distributional_indicators(panel)


@pytest.fixture
def baseline_scenario_fiscal() -> IndicatorResult:
    """Baseline scenario with fiscal indicators."""
    num_households = 100
    household_ids = list(range(num_households))
    years = [2020, 2021]

    # Create multi-year panel
    all_ids = []
    all_years = []
    all_revenues = []
    all_costs = []

    for year in years:
        for hh_id in household_ids:
            all_ids.append(hh_id)
            all_years.append(year)
            all_revenues.append(1000.0 + hh_id * 10.0)
            all_costs.append(500.0 + hh_id * 5.0)

    table = pa.table(
        {
            "household_id": pa.array(all_ids, type=pa.int64()),
            "year": pa.array(all_years, type=pa.int64()),
            "revenue": pa.array(all_revenues, type=pa.float64()),
            "cost": pa.array(all_costs, type=pa.float64()),
        }
    )

    panel = PanelOutput(
        table=table,
        metadata={"start_year": 2020, "end_year": 2021, "seed": 42},
    )

    config = FiscalConfig(
        revenue_fields=["revenue"],
        cost_fields=["cost"],
        by_year=True,
        cumulative=True,
    )
    return compute_fiscal_indicators(panel, config)


@pytest.fixture
def reform_scenario_fiscal() -> IndicatorResult:
    """Reform scenario with fiscal indicators (higher revenue)."""
    num_households = 100
    household_ids = list(range(num_households))
    years = [2020, 2021]

    all_ids = []
    all_years = []
    all_revenues = []
    all_costs = []

    for year in years:
        for hh_id in household_ids:
            all_ids.append(hh_id)
            all_years.append(year)
            # Higher revenue in reform
            all_revenues.append(1500.0 + hh_id * 15.0)
            all_costs.append(500.0 + hh_id * 5.0)

    table = pa.table(
        {
            "household_id": pa.array(all_ids, type=pa.int64()),
            "year": pa.array(all_years, type=pa.int64()),
            "revenue": pa.array(all_revenues, type=pa.float64()),
            "cost": pa.array(all_costs, type=pa.float64()),
        }
    )

    panel = PanelOutput(
        table=table,
        metadata={"start_year": 2020, "end_year": 2021, "seed": 43},
    )

    config = FiscalConfig(
        revenue_fields=["revenue"],
        cost_fields=["cost"],
        by_year=True,
        cumulative=True,
    )
    return compute_fiscal_indicators(panel, config)


class TestSideBySideComparison:
    """Test side-by-side comparison table generation (AC-1)."""

    def test_two_scenario_comparison(
        self,
        baseline_scenario_distributional: IndicatorResult,
        reform_scenario_distributional: IndicatorResult,
    ) -> None:
        """AC-1: Two-scenario comparison produces side-by-side table."""
        scenarios = [
            ScenarioInput(
                label="baseline", indicators=baseline_scenario_distributional
            ),
            ScenarioInput(label="reform_a", indicators=reform_scenario_distributional),
        ]

        result = compare_scenarios(scenarios)

        # Check table has correct columns
        assert "field_name" in result.table.column_names
        assert "decile" in result.table.column_names
        assert "year" in result.table.column_names
        assert "metric" in result.table.column_names
        assert "baseline" in result.table.column_names
        assert "reform_a" in result.table.column_names

        # Check metadata
        assert result.metadata["scenario_labels"] == ["baseline", "reform_a"]
        assert result.metadata["baseline_label"] == "baseline"
        assert result.metadata["indicator_schema"] == "decile"

    def test_three_scenario_comparison(
        self,
        baseline_scenario_distributional: IndicatorResult,
        reform_scenario_distributional: IndicatorResult,
        reform_b_scenario_distributional: IndicatorResult,
    ) -> None:
        """AC-1: Three-scenario comparison includes all scenario columns."""
        scenarios = [
            ScenarioInput(
                label="baseline", indicators=baseline_scenario_distributional
            ),
            ScenarioInput(label="reform_a", indicators=reform_scenario_distributional),
            ScenarioInput(
                label="reform_b", indicators=reform_b_scenario_distributional
            ),
        ]

        result = compare_scenarios(scenarios)

        # Check all scenario columns present
        assert "baseline" in result.table.column_names
        assert "reform_a" in result.table.column_names
        assert "reform_b" in result.table.column_names

        # Check metadata
        assert result.metadata["scenario_labels"] == [
            "baseline",
            "reform_a",
            "reform_b",
        ]

    def test_fiscal_comparison(
        self,
        baseline_scenario_fiscal: IndicatorResult,
        reform_scenario_fiscal: IndicatorResult,
    ) -> None:
        """AC-1: Fiscal indicator comparison uses correct join keys."""
        scenarios = [
            ScenarioInput(label="baseline", indicators=baseline_scenario_fiscal),
            ScenarioInput(label="reform", indicators=reform_scenario_fiscal),
        ]

        result = compare_scenarios(scenarios)

        # Fiscal schema should not have decile/region columns
        assert "decile" not in result.table.column_names
        assert "region" not in result.table.column_names
        assert "field_name" in result.table.column_names
        assert "year" in result.table.column_names
        assert "metric" in result.table.column_names
        assert "baseline" in result.table.column_names
        assert "reform" in result.table.column_names


class TestDeltaComputation:
    """Test delta computation (absolute and percentage) (AC-2)."""

    def test_absolute_delta_computation(
        self,
        baseline_scenario_distributional: IndicatorResult,
        reform_scenario_distributional: IndicatorResult,
    ) -> None:
        """AC-2: Absolute delta columns are computed correctly."""
        scenarios = [
            ScenarioInput(
                label="baseline", indicators=baseline_scenario_distributional
            ),
            ScenarioInput(label="reform_a", indicators=reform_scenario_distributional),
        ]

        config = ComparisonConfig(include_deltas=True, include_pct_deltas=False)
        result = compare_scenarios(scenarios, config)

        # Check delta column exists
        assert "delta_reform_a" in result.table.column_names

        # Verify delta values: delta = reform_a - baseline
        table_dict = result.table.to_pydict()
        for i in range(len(table_dict["baseline"])):
            baseline_val = table_dict["baseline"][i]
            reform_val = table_dict["reform_a"][i]
            delta_val = table_dict["delta_reform_a"][i]

            if baseline_val is not None and reform_val is not None:
                expected_delta = reform_val - baseline_val
                assert abs(delta_val - expected_delta) < 1e-6

    def test_percentage_delta_computation(
        self,
        baseline_scenario_distributional: IndicatorResult,
        reform_scenario_distributional: IndicatorResult,
    ) -> None:
        """AC-2: Percentage delta columns are computed correctly."""
        scenarios = [
            ScenarioInput(
                label="baseline", indicators=baseline_scenario_distributional
            ),
            ScenarioInput(label="reform_a", indicators=reform_scenario_distributional),
        ]

        config = ComparisonConfig(include_deltas=False, include_pct_deltas=True)
        result = compare_scenarios(scenarios, config)

        # Check pct_delta column exists
        assert "pct_delta_reform_a" in result.table.column_names

        # Verify percentage delta values: pct_delta = (reform_a - baseline) / baseline * 100
        table_dict = result.table.to_pydict()
        for i in range(len(table_dict["baseline"])):
            baseline_val = table_dict["baseline"][i]
            reform_val = table_dict["reform_a"][i]
            pct_delta_val = table_dict["pct_delta_reform_a"][i]

            if baseline_val is not None and reform_val is not None:
                if baseline_val == 0.0:
                    # Division by zero should result in null
                    assert pct_delta_val is None
                else:
                    expected_pct_delta = (
                        (reform_val - baseline_val) / baseline_val * 100.0
                    )
                    assert abs(pct_delta_val - expected_pct_delta) < 1e-6

    def test_both_delta_types(
        self,
        baseline_scenario_distributional: IndicatorResult,
        reform_scenario_distributional: IndicatorResult,
    ) -> None:
        """AC-2: Both absolute and percentage deltas can be computed together."""
        scenarios = [
            ScenarioInput(
                label="baseline", indicators=baseline_scenario_distributional
            ),
            ScenarioInput(label="reform_a", indicators=reform_scenario_distributional),
        ]

        config = ComparisonConfig(include_deltas=True, include_pct_deltas=True)
        result = compare_scenarios(scenarios, config)

        # Check both delta columns exist
        assert "delta_reform_a" in result.table.column_names
        assert "pct_delta_reform_a" in result.table.column_names

    def test_deltas_align_rows_when_year_is_null(
        self,
        baseline_scenario_distributional: IndicatorResult,
        reform_scenario_distributional: IndicatorResult,
    ) -> None:
        """AC-2: Delta values compute on overlapping keys with null years."""
        scenarios = [
            ScenarioInput(
                label="baseline", indicators=baseline_scenario_distributional
            ),
            ScenarioInput(label="reform_a", indicators=reform_scenario_distributional),
        ]

        config = ComparisonConfig(include_deltas=True, include_pct_deltas=False)
        result = compare_scenarios(scenarios, config)

        rows = result.table.to_pylist()
        rows_with_both_values = [
            row
            for row in rows
            if row["baseline"] is not None and row["reform_a"] is not None
        ]
        assert rows_with_both_values, (
            "Expected overlapping rows with both scenario values"
        )

        for row in rows_with_both_values:
            assert row["delta_reform_a"] == pytest.approx(
                row["reform_a"] - row["baseline"]
            )


class TestInputValidation:
    """Test input contract validation (AC-3)."""

    def test_single_scenario_error(
        self, baseline_scenario_distributional: IndicatorResult
    ) -> None:
        """AC-3: Single scenario input raises clear validation error."""
        scenarios = [
            ScenarioInput(
                label="baseline", indicators=baseline_scenario_distributional
            ),
        ]

        with pytest.raises(ValueError, match="at least 2 scenarios"):
            compare_scenarios(scenarios)

    def test_duplicate_labels_error(
        self,
        baseline_scenario_distributional: IndicatorResult,
        reform_scenario_distributional: IndicatorResult,
    ) -> None:
        """AC-3: Duplicate scenario labels raise clear validation error."""
        scenarios = [
            ScenarioInput(
                label="baseline", indicators=baseline_scenario_distributional
            ),
            ScenarioInput(label="baseline", indicators=reform_scenario_distributional),
        ]

        with pytest.raises(ValueError, match="Duplicate scenario labels"):
            compare_scenarios(scenarios)

    def test_mixed_schema_error(
        self,
        baseline_scenario_distributional: IndicatorResult,
        baseline_scenario_fiscal: IndicatorResult,
    ) -> None:
        """AC-3: Mixed indicator schemas raise clear validation error."""
        scenarios = [
            ScenarioInput(
                label="baseline", indicators=baseline_scenario_distributional
            ),
            ScenarioInput(label="reform", indicators=baseline_scenario_fiscal),
        ]

        with pytest.raises(ValueError, match="Mixed indicator schemas"):
            compare_scenarios(scenarios)

    def test_reserved_label_error(
        self,
        baseline_scenario_distributional: IndicatorResult,
        reform_scenario_distributional: IndicatorResult,
    ) -> None:
        """Labels conflicting with reserved columns should fail fast."""
        scenarios = [
            ScenarioInput(
                label="field_name", indicators=baseline_scenario_distributional
            ),
            ScenarioInput(label="reform", indicators=reform_scenario_distributional),
        ]

        with pytest.raises(ValueError, match="cannot match reserved table columns"):
            compare_scenarios(scenarios)


class TestCSVExport:
    """Test CSV export functionality (AC-4)."""

    def test_csv_export_creates_file(
        self,
        baseline_scenario_distributional: IndicatorResult,
        reform_scenario_distributional: IndicatorResult,
    ) -> None:
        """AC-4: CSV export creates a valid file."""
        scenarios = [
            ScenarioInput(
                label="baseline", indicators=baseline_scenario_distributional
            ),
            ScenarioInput(label="reform_a", indicators=reform_scenario_distributional),
        ]

        result = compare_scenarios(scenarios)

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "comparison.csv"
            result.export_csv(csv_path)

            # Check file exists
            assert csv_path.exists()

            # Check file is readable by PyArrow
            read_table = pa_csv.read_csv(csv_path)
            assert read_table.num_rows > 0
            assert "field_name" in read_table.column_names
            assert "baseline" in read_table.column_names
            assert "reform_a" in read_table.column_names

    def test_csv_round_trip(
        self,
        baseline_scenario_distributional: IndicatorResult,
        reform_scenario_distributional: IndicatorResult,
    ) -> None:
        """AC-4: CSV export preserves data through round-trip."""
        scenarios = [
            ScenarioInput(
                label="baseline", indicators=baseline_scenario_distributional
            ),
            ScenarioInput(label="reform_a", indicators=reform_scenario_distributional),
        ]

        result = compare_scenarios(scenarios)

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "comparison.csv"
            result.export_csv(csv_path)

            # Read back and compare
            read_table = pa_csv.read_csv(csv_path)
            original_dict = result.table.to_pydict()

            # Check row count
            assert len(read_table) == len(original_dict["field_name"])

            # Check key columns present
            assert set(read_table.column_names).issuperset(
                {"field_name", "baseline", "reform_a"}
            )


class TestParquetExport:
    """Test Parquet export functionality (AC-5)."""

    def test_parquet_export_creates_file(
        self,
        baseline_scenario_distributional: IndicatorResult,
        reform_scenario_distributional: IndicatorResult,
    ) -> None:
        """AC-5: Parquet export creates a valid file."""
        scenarios = [
            ScenarioInput(
                label="baseline", indicators=baseline_scenario_distributional
            ),
            ScenarioInput(label="reform_a", indicators=reform_scenario_distributional),
        ]

        result = compare_scenarios(scenarios)

        with tempfile.TemporaryDirectory() as tmpdir:
            parquet_path = Path(tmpdir) / "comparison.parquet"
            result.export_parquet(parquet_path)

            # Check file exists
            assert parquet_path.exists()

            # Check file is readable by PyArrow
            read_table = pq.read_table(parquet_path)
            assert read_table.num_rows > 0
            assert "field_name" in read_table.column_names
            assert "baseline" in read_table.column_names
            assert "reform_a" in read_table.column_names

    def test_parquet_round_trip_preserves_types(
        self,
        baseline_scenario_distributional: IndicatorResult,
        reform_scenario_distributional: IndicatorResult,
    ) -> None:
        """AC-5: Parquet export preserves column types through round-trip."""
        scenarios = [
            ScenarioInput(
                label="baseline", indicators=baseline_scenario_distributional
            ),
            ScenarioInput(label="reform_a", indicators=reform_scenario_distributional),
        ]

        result = compare_scenarios(scenarios)

        with tempfile.TemporaryDirectory() as tmpdir:
            parquet_path = Path(tmpdir) / "comparison.parquet"
            result.export_parquet(parquet_path)

            # Read back with pyarrow to check schema preservation
            read_table = pq.read_table(parquet_path)

            # Check schema matches
            assert read_table.schema.equals(result.table.schema, check_metadata=False)

            # Check row count
            assert len(read_table) == len(result.table)


class TestMetadataPreservation:
    """Test metadata preservation (AC-6)."""

    def test_metadata_contains_scenario_labels(
        self,
        baseline_scenario_distributional: IndicatorResult,
        reform_scenario_distributional: IndicatorResult,
    ) -> None:
        """AC-6: Metadata contains scenario labels."""
        scenarios = [
            ScenarioInput(
                label="baseline", indicators=baseline_scenario_distributional
            ),
            ScenarioInput(label="reform_a", indicators=reform_scenario_distributional),
        ]

        result = compare_scenarios(scenarios)

        assert "scenario_labels" in result.metadata
        assert result.metadata["scenario_labels"] == ["baseline", "reform_a"]

    def test_metadata_contains_indicator_type(
        self,
        baseline_scenario_distributional: IndicatorResult,
        reform_scenario_distributional: IndicatorResult,
    ) -> None:
        """AC-6: Metadata contains indicator schema type."""
        scenarios = [
            ScenarioInput(
                label="baseline", indicators=baseline_scenario_distributional
            ),
            ScenarioInput(label="reform_a", indicators=reform_scenario_distributional),
        ]

        result = compare_scenarios(scenarios)

        assert "indicator_schema" in result.metadata
        assert result.metadata["indicator_schema"] == "decile"

    def test_metadata_contains_source_metadata(
        self,
        baseline_scenario_distributional: IndicatorResult,
        reform_scenario_distributional: IndicatorResult,
    ) -> None:
        """AC-6: Metadata preserves source indicator metadata."""
        scenarios = [
            ScenarioInput(
                label="baseline", indicators=baseline_scenario_distributional
            ),
            ScenarioInput(label="reform_a", indicators=reform_scenario_distributional),
        ]

        result = compare_scenarios(scenarios)

        assert "source_metadata" in result.metadata
        assert len(result.metadata["source_metadata"]) == 2

    def test_metadata_contains_field_mappings(
        self,
        baseline_scenario_distributional: IndicatorResult,
        reform_scenario_distributional: IndicatorResult,
    ) -> None:
        """AC-6: Metadata includes field mappings for governance consumers."""
        scenarios = [
            ScenarioInput(
                label="baseline", indicators=baseline_scenario_distributional
            ),
            ScenarioInput(label="reform_a", indicators=reform_scenario_distributional),
        ]

        result = compare_scenarios(scenarios)

        assert "field_mappings" in result.metadata
        mappings = result.metadata["field_mappings"]
        assert mappings["scenario_value_columns"] == {
            "baseline": "baseline",
            "reform_a": "reform_a",
        }
        assert mappings["join_keys"] == ["field_name", "decile", "year", "metric"]


class TestMismatchedInputHandling:
    """Test mismatched dimension handling (AC-7)."""

    def test_non_overlapping_years_warning(self) -> None:
        """AC-7: Non-overlapping years emit warning."""
        # Create baseline with year 2020
        baseline_table = pa.table(
            {
                "household_id": pa.array(
                    [
                        0,
                        1,
                        2,
                        3,
                        4,
                        5,
                        6,
                        7,
                        8,
                        9,
                        10,
                        11,
                        12,
                        13,
                        14,
                        15,
                        16,
                        17,
                        18,
                        19,
                    ],
                    type=pa.int64(),
                ),
                "year": pa.array([2020] * 20, type=pa.int64()),
                "income": pa.array(
                    [10000.0 + i * 1000.0 for i in range(20)], type=pa.float64()
                ),
                "tax": pa.array(
                    [1000.0 + i * 100.0 for i in range(20)], type=pa.float64()
                ),
            }
        )
        baseline_panel = PanelOutput(
            table=baseline_table,
            metadata={"start_year": 2020, "end_year": 2020, "seed": 42},
        )
        baseline_indicators = compute_distributional_indicators(
            baseline_panel, config=DistributionalConfig(by_year=True)
        )

        # Create reform with year 2021 (non-overlapping)
        reform_table = pa.table(
            {
                "household_id": pa.array(
                    [
                        0,
                        1,
                        2,
                        3,
                        4,
                        5,
                        6,
                        7,
                        8,
                        9,
                        10,
                        11,
                        12,
                        13,
                        14,
                        15,
                        16,
                        17,
                        18,
                        19,
                    ],
                    type=pa.int64(),
                ),
                "year": pa.array([2021] * 20, type=pa.int64()),
                "income": pa.array(
                    [10000.0 + i * 1000.0 for i in range(20)], type=pa.float64()
                ),
                "tax": pa.array(
                    [1500.0 + i * 120.0 for i in range(20)], type=pa.float64()
                ),
            }
        )
        reform_panel = PanelOutput(
            table=reform_table,
            metadata={"start_year": 2021, "end_year": 2021, "seed": 43},
        )
        reform_indicators = compute_distributional_indicators(
            reform_panel, config=DistributionalConfig(by_year=True)
        )

        scenarios = [
            ScenarioInput(label="baseline", indicators=baseline_indicators),
            ScenarioInput(label="reform", indicators=reform_indicators),
        ]

        result = compare_scenarios(scenarios)

        # Should emit warning about non-overlapping dimensions
        assert len(result.warnings) > 0
        assert any("non-overlapping comparison keys" in w for w in result.warnings)
        assert any("year" in w for w in result.warnings)

        rows = result.table.to_pylist()
        assert any(row["baseline"] is None for row in rows)
        assert any(row["reform"] is None for row in rows)


class TestEmptyInputHandling:
    """Test empty scenario handling."""

    def test_all_empty_scenarios_return_stable_schema(self) -> None:
        """AC-7/AC-8: Empty comparisons keep stable schema and metadata."""
        empty_a = IndicatorResult(
            indicators=[],
            metadata={"income_field": "income", "group_by_year": True},
        )
        empty_b = IndicatorResult(
            indicators=[],
            metadata={"income_field": "income", "group_by_year": True},
        )

        scenarios = [
            ScenarioInput(label="baseline", indicators=empty_a),
            ScenarioInput(label="reform_a", indicators=empty_b),
        ]
        result = compare_scenarios(scenarios)

        assert result.table.num_rows == 0
        assert "value" not in result.table.column_names
        assert "baseline" in result.table.column_names
        assert "reform_a" in result.table.column_names
        assert "delta_reform_a" in result.table.column_names
        assert "pct_delta_reform_a" in result.table.column_names
        assert result.metadata["baseline_label"] == "baseline"
        assert result.metadata["join_keys"] == [
            "field_name",
            "decile",
            "year",
            "metric",
        ]
        assert any("empty indicator results" in warning for warning in result.warnings)


class TestStableTableContract:
    """Test stable PyArrow table contract (AC-8)."""

    def test_to_table_returns_pyarrow_table(
        self,
        baseline_scenario_distributional: IndicatorResult,
        reform_scenario_distributional: IndicatorResult,
    ) -> None:
        """AC-8: to_table() returns a PyArrow Table."""
        scenarios = [
            ScenarioInput(
                label="baseline", indicators=baseline_scenario_distributional
            ),
            ScenarioInput(label="reform_a", indicators=reform_scenario_distributional),
        ]

        result = compare_scenarios(scenarios)
        table = result.to_table()

        assert isinstance(table, pa.Table)

    def test_table_schema_is_stable(
        self,
        baseline_scenario_distributional: IndicatorResult,
        reform_scenario_distributional: IndicatorResult,
    ) -> None:
        """AC-8: Table schema is stable and predictable."""
        scenarios = [
            ScenarioInput(
                label="baseline", indicators=baseline_scenario_distributional
            ),
            ScenarioInput(label="reform_a", indicators=reform_scenario_distributional),
        ]

        result = compare_scenarios(scenarios)
        table = result.to_table()

        # Check schema has expected columns
        expected_base_cols = {
            "field_name",
            "decile",
            "year",
            "metric",
            "baseline",
            "reform_a",
        }
        assert expected_base_cols.issubset(set(table.column_names))

        # Check column types
        assert table.schema.field("field_name").type == pa.utf8()
        assert table.schema.field("decile").type == pa.int64()
        assert table.schema.field("year").type == pa.int64()
        assert table.schema.field("metric").type == pa.utf8()
        assert table.schema.field("baseline").type == pa.float64()
        assert table.schema.field("reform_a").type == pa.float64()
