"""Tests for feebate batch execution and comparison utilities."""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.templates.feebate.compare import (
    ComparisonResult,
    compare_feebate_decile_impacts,
    feebate_decile_results_to_table,
    run_feebate_batch,
)
from reformlab.templates.feebate.compute import (
    FeebateDecileResults,
    FeebateResult,
)
from reformlab.templates.packs import load_feebate_template
from reformlab.templates.schema import (
    BaselineScenario,
    FeebateParameters,
    PolicyType,
    YearSchedule,
)


@pytest.fixture()
def sample_population() -> pa.Table:
    """Create a sample population with income and vehicle emissions data."""
    return pa.table(
        {
            "household_id": pa.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], type=pa.int64()),
            "income": pa.array(
                [
                    15000.0,
                    25000.0,
                    35000.0,
                    45000.0,
                    55000.0,
                    65000.0,
                    75000.0,
                    90000.0,
                    120000.0,
                    40000.0,
                ],
                type=pa.float64(),
            ),
            "vehicle_emissions_gkm": pa.array(
                [80.0, 100.0, 120.0, 140.0, 160.0, 90.0, 130.0, 150.0, 200.0, 110.0],
                type=pa.float64(),
            ),
        }
    )


class TestRunFeebateBatch:
    """Tests for batch feebate execution."""

    def test_run_batch_with_single_scenario(self, sample_population: pa.Table) -> None:
        """Batch run with single scenario returns dict with one result."""
        scenario = load_feebate_template("feebate-vehicle-emissions")
        results = run_feebate_batch(
            sample_population, [scenario], "vehicle_emissions_gkm", 2026
        )

        assert len(results) == 1
        assert scenario.name in results
        assert isinstance(results[scenario.name], FeebateResult)

    def test_run_batch_with_multiple_scenarios(
        self, sample_population: pa.Table
    ) -> None:
        """Batch run with multiple scenarios returns dict with all results."""
        scenario1 = BaselineScenario(
            name="Feebate Low Rates",
            policy_type=PolicyType.FEEBATE,
            year_schedule=YearSchedule(2026, 2036),
            parameters=FeebateParameters(
                rate_schedule={2026: 0.0},
                pivot_point=120.0,
                fee_rate=25.0,
                rebate_rate=25.0,
            ),
        )
        scenario2 = BaselineScenario(
            name="Feebate High Rates",
            policy_type=PolicyType.FEEBATE,
            year_schedule=YearSchedule(2026, 2036),
            parameters=FeebateParameters(
                rate_schedule={2026: 0.0},
                pivot_point=120.0,
                fee_rate=100.0,
                rebate_rate=100.0,
            ),
        )

        results = run_feebate_batch(
            sample_population, [scenario1, scenario2], "vehicle_emissions_gkm", 2026
        )

        assert len(results) == 2
        assert "Feebate Low Rates" in results
        assert "Feebate High Rates" in results


class TestCompareFeebateDecileImpacts:
    """Tests for feebate comparison by decile."""

    def test_compare_produces_comparison_result(
        self, sample_population: pa.Table
    ) -> None:
        """Comparison returns ComparisonResult with all components."""
        scenario = load_feebate_template("feebate-vehicle-emissions")
        results = run_feebate_batch(
            sample_population, [scenario], "vehicle_emissions_gkm", 2026
        )
        comparison = compare_feebate_decile_impacts(results)

        assert isinstance(comparison, ComparisonResult)
        assert len(comparison.scenarios) == 1
        assert comparison.comparison_table is not None

    def test_compare_table_has_decile_column(self, sample_population: pa.Table) -> None:
        """Comparison table has decile column with 1-10."""
        scenario = load_feebate_template("feebate-vehicle-emissions")
        results = run_feebate_batch(
            sample_population, [scenario], "vehicle_emissions_gkm", 2026
        )
        comparison = compare_feebate_decile_impacts(results)

        table = comparison.comparison_table
        assert "decile" in table.column_names
        deciles = table.column("decile").to_pylist()
        assert deciles == list(range(1, 11))

    def test_compare_table_includes_policy_specific_metrics_for_each_scenario(
        self, sample_population: pa.Table
    ) -> None:
        """Comparison exposes fee/rebate/net metrics by scenario."""
        scenario_low = BaselineScenario(
            name="Feebate Low Rates",
            policy_type=PolicyType.FEEBATE,
            year_schedule=YearSchedule(2026, 2036),
            parameters=FeebateParameters(
                rate_schedule={2026: 0.0},
                pivot_point=120.0,
                fee_rate=25.0,
                rebate_rate=25.0,
            ),
        )
        scenario_high = BaselineScenario(
            name="Feebate High Rates",
            policy_type=PolicyType.FEEBATE,
            year_schedule=YearSchedule(2026, 2036),
            parameters=FeebateParameters(
                rate_schedule={2026: 0.0},
                pivot_point=120.0,
                fee_rate=100.0,
                rebate_rate=100.0,
            ),
        )
        results = run_feebate_batch(
            sample_population,
            [scenario_low, scenario_high],
            "vehicle_emissions_gkm",
            2026,
        )
        comparison = compare_feebate_decile_impacts(results)
        columns = set(comparison.comparison_table.column_names)

        assert "Feebate_Low_Rates_mean_fee" in columns
        assert "Feebate_Low_Rates_mean_rebate" in columns
        assert "Feebate_Low_Rates_mean_net_impact" in columns
        assert "Feebate_High_Rates_mean_fee" in columns
        assert "Feebate_High_Rates_mean_rebate" in columns
        assert "Feebate_High_Rates_mean_net_impact" in columns


class TestFeebateDecileResultsToTable:
    """Tests for decile results conversion to table."""

    def test_to_table_has_expected_columns(self) -> None:
        """Table has all expected columns."""
        decile_results = FeebateDecileResults(
            decile=tuple(range(1, 11)),
            household_count=(10,) * 10,
            mean_fee=(500.0,) * 10,
            mean_rebate=(500.0,) * 10,
            mean_net_impact=(0.0,) * 10,
            total_fee=(5000.0,) * 10,
            total_rebate=(5000.0,) * 10,
            total_net_impact=(0.0,) * 10,
        )

        table = feebate_decile_results_to_table(decile_results)

        assert "decile" in table.column_names
        assert "household_count" in table.column_names
        assert "mean_fee" in table.column_names
        assert "mean_rebate" in table.column_names
        assert "mean_net_impact" in table.column_names
        assert table.num_rows == 10
