"""Tests for vehicle malus batch execution and comparison.

Story 13.2 — AC #5.
"""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.templates.schema import (
    BaselineScenario,
    CarbonTaxParameters,
    YearSchedule,
)
from reformlab.templates.vehicle_malus.compare import (
    ComparisonResult,
    compare_vehicle_malus_decile_impacts,
    run_vehicle_malus_batch,
    vehicle_malus_decile_results_to_table,
)
from reformlab.templates.vehicle_malus.compute import (
    VehicleMalusParameters,
    VehicleMalusResult,
    aggregate_vehicle_malus_by_decile,
    compute_vehicle_malus,
)


class TestRunVehicleMalusBatch:
    """AC #5: Batch execution."""

    def test_single_scenario(
        self, sample_population: pa.Table, flat_rate_params: VehicleMalusParameters
    ) -> None:
        scenario = BaselineScenario(
            name="flat-rate",
            year_schedule=YearSchedule(start_year=2026, end_year=2036),
            policy=flat_rate_params,
        )
        results = run_vehicle_malus_batch(
            sample_population, [scenario], year=2026
        )
        assert len(results) == 1
        assert "flat-rate" in results
        assert isinstance(results["flat-rate"], VehicleMalusResult)

    def test_multiple_scenarios(
        self, sample_population: pa.Table
    ) -> None:
        params_a = VehicleMalusParameters(
            rate_schedule={}, emission_threshold=120.0, malus_rate_per_gkm=50.0
        )
        params_b = VehicleMalusParameters(
            rate_schedule={}, emission_threshold=100.0, malus_rate_per_gkm=75.0
        )
        scenario_a = BaselineScenario(
            name="scenario-a",
            year_schedule=YearSchedule(start_year=2026, end_year=2036),
            policy=params_a,
        )
        scenario_b = BaselineScenario(
            name="scenario-b",
            year_schedule=YearSchedule(start_year=2026, end_year=2036),
            policy=params_b,
        )
        results = run_vehicle_malus_batch(
            sample_population, [scenario_a, scenario_b], year=2026
        )
        assert len(results) == 2
        assert "scenario-a" in results
        assert "scenario-b" in results
        # Scenario B with lower threshold and higher rate should have more revenue
        assert results["scenario-b"].total_revenue > results["scenario-a"].total_revenue

    def test_wrong_policy_type_raises(
        self, sample_population: pa.Table
    ) -> None:
        wrong_scenario = BaselineScenario(
            name="carbon-tax",
            year_schedule=YearSchedule(start_year=2026, end_year=2036),
            policy=CarbonTaxParameters(rate_schedule={2026: 44.0}),
        )
        with pytest.raises(TypeError, match="does not have VehicleMalusParameters"):
            run_vehicle_malus_batch(
                sample_population, [wrong_scenario], year=2026
            )


class TestCompareVehicleMalusDecileImpacts:
    """AC #5: Comparison result structure."""

    def test_comparison_result_structure(
        self, sample_population: pa.Table
    ) -> None:
        params_a = VehicleMalusParameters(
            rate_schedule={}, emission_threshold=120.0, malus_rate_per_gkm=50.0
        )
        params_b = VehicleMalusParameters(
            rate_schedule={}, emission_threshold=100.0, malus_rate_per_gkm=75.0
        )
        result_a = compute_vehicle_malus(
            sample_population, params_a, year=2026, template_name="a"
        )
        result_b = compute_vehicle_malus(
            sample_population, params_b, year=2026, template_name="b"
        )
        comparison = compare_vehicle_malus_decile_impacts(
            {"scenario-a": result_a, "scenario-b": result_b}
        )
        assert isinstance(comparison, ComparisonResult)
        assert comparison.scenarios == ("scenario-a", "scenario-b")
        assert len(comparison.decile_results) == 2
        assert isinstance(comparison.comparison_table, pa.Table)

    def test_wide_format_table_columns(
        self, sample_population: pa.Table, flat_rate_params: VehicleMalusParameters
    ) -> None:
        result = compute_vehicle_malus(
            sample_population, flat_rate_params, year=2026, template_name="test"
        )
        comparison = compare_vehicle_malus_decile_impacts({"flat_rate": result})
        table = comparison.comparison_table
        assert "decile" in table.column_names
        assert "flat_rate_mean_malus" in table.column_names
        assert "flat_rate_total_malus" in table.column_names
        assert "flat_rate_household_count" in table.column_names
        assert table.num_rows == 10


class TestVehicleMalusDecileResultsToTable:
    """Conversion utility test."""

    def test_converts_to_table(
        self, sample_population: pa.Table, flat_rate_params: VehicleMalusParameters
    ) -> None:
        result = compute_vehicle_malus(
            sample_population, flat_rate_params, year=2026
        )
        decile_results = aggregate_vehicle_malus_by_decile(result)
        table = vehicle_malus_decile_results_to_table(decile_results)
        assert isinstance(table, pa.Table)
        assert table.num_rows == 10
        assert set(table.column_names) == {
            "decile", "household_count", "mean_malus", "total_malus"
        }
