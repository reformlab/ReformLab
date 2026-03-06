"""Tests for energy poverty aid batch execution and comparison.

Story 13.3 — AC #5.
"""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.templates.energy_poverty_aid.compare import (
    ComparisonResult,
    compare_energy_poverty_aid_decile_impacts,
    energy_poverty_aid_decile_results_to_table,
    run_energy_poverty_aid_batch,
)
from reformlab.templates.energy_poverty_aid.compute import (
    EnergyPovertyAidDecileResults,
    EnergyPovertyAidParameters,
    EnergyPovertyAidResult,
    compute_energy_poverty_aid,
)
from reformlab.templates.exceptions import TemplateError
from reformlab.templates.schema import (
    BaselineScenario,
    CarbonTaxParameters,
    YearSchedule,
)


class TestRunEnergyPovertyAidBatch:
    """AC #5: Batch execution."""

    def test_single_scenario(
        self,
        sample_population: pa.Table,
        cheque_energie_params: EnergyPovertyAidParameters,
    ) -> None:
        scenario = BaselineScenario(
            name="cheque-energie",
            year_schedule=YearSchedule(start_year=2026, end_year=2036),
            policy=cheque_energie_params,
        )
        results = run_energy_poverty_aid_batch(
            sample_population, [scenario], year=2026
        )
        assert len(results) == 1
        assert "cheque-energie" in results
        assert isinstance(results["cheque-energie"], EnergyPovertyAidResult)

    def test_multiple_scenarios(
        self,
        sample_population: pa.Table,
        cheque_energie_params: EnergyPovertyAidParameters,
        generous_params: EnergyPovertyAidParameters,
    ) -> None:
        scenarios = [
            BaselineScenario(
                name="standard",
                year_schedule=YearSchedule(start_year=2026, end_year=2036),
                policy=cheque_energie_params,
            ),
            BaselineScenario(
                name="generous",
                year_schedule=YearSchedule(start_year=2026, end_year=2036),
                policy=generous_params,
            ),
        ]
        results = run_energy_poverty_aid_batch(
            sample_population, scenarios, year=2026
        )
        assert len(results) == 2
        assert "standard" in results
        assert "generous" in results

    def test_wrong_policy_type_raises(
        self,
        sample_population: pa.Table,
    ) -> None:
        """Scenario with CarbonTaxParameters raises TypeError."""
        wrong_scenario = BaselineScenario(
            name="wrong",
            year_schedule=YearSchedule(start_year=2026, end_year=2036),
            policy=CarbonTaxParameters(rate_schedule={2026: 44.6}),
        )
        with pytest.raises(TypeError, match="EnergyPovertyAidParameters"):
            run_energy_poverty_aid_batch(
                sample_population, [wrong_scenario], year=2026
            )

    def test_duplicate_scenario_names_raises(
        self,
        sample_population: pa.Table,
        cheque_energie_params: EnergyPovertyAidParameters,
    ) -> None:
        """Duplicate scenario names raise ValueError."""
        scenarios = [
            BaselineScenario(
                name="same-name",
                year_schedule=YearSchedule(start_year=2026, end_year=2036),
                policy=cheque_energie_params,
            ),
            BaselineScenario(
                name="same-name",
                year_schedule=YearSchedule(start_year=2026, end_year=2036),
                policy=cheque_energie_params,
            ),
        ]
        with pytest.raises(TemplateError, match="Duplicate scenario name"):
            run_energy_poverty_aid_batch(
                sample_population, scenarios, year=2026
            )


class TestCompareEnergyPovertyAidDecileImpacts:
    """AC #5: Comparison results."""

    def test_comparison_result_structure(
        self,
        sample_population: pa.Table,
        cheque_energie_params: EnergyPovertyAidParameters,
        generous_params: EnergyPovertyAidParameters,
    ) -> None:
        r1 = compute_energy_poverty_aid(
            sample_population, cheque_energie_params, year=2026, template_name="std"
        )
        r2 = compute_energy_poverty_aid(
            sample_population, generous_params, year=2026, template_name="gen"
        )
        comparison = compare_energy_poverty_aid_decile_impacts(
            {"std": r1, "gen": r2}
        )
        assert isinstance(comparison, ComparisonResult)
        assert comparison.scenarios == ("std", "gen")
        assert "std" in comparison.decile_results
        assert "gen" in comparison.decile_results
        assert isinstance(comparison.decile_results["std"], EnergyPovertyAidDecileResults)

    def test_wide_format_table_columns(
        self,
        sample_population: pa.Table,
        cheque_energie_params: EnergyPovertyAidParameters,
    ) -> None:
        result = compute_energy_poverty_aid(
            sample_population, cheque_energie_params, year=2026, template_name="test"
        )
        comparison = compare_energy_poverty_aid_decile_impacts({"test": result})
        table = comparison.comparison_table
        assert "decile" in table.column_names
        assert "test_mean_aid" in table.column_names
        assert "test_total_aid" in table.column_names
        assert "test_household_count" in table.column_names
        assert "test_eligible_count" in table.column_names
        assert table.num_rows == 10


class TestEnergyPovertyAidDecileResultsToTable:
    """Conversion utility test."""

    def test_converts_to_table(
        self,
        sample_population: pa.Table,
        cheque_energie_params: EnergyPovertyAidParameters,
    ) -> None:
        result = compute_energy_poverty_aid(
            sample_population, cheque_energie_params, year=2026
        )
        from reformlab.templates.energy_poverty_aid.compute import (
            aggregate_energy_poverty_aid_by_decile,
        )

        decile_results = aggregate_energy_poverty_aid_by_decile(result)
        table = energy_poverty_aid_decile_results_to_table(decile_results)
        assert isinstance(table, pa.Table)
        assert table.num_rows == 10
        assert "decile" in table.column_names
        assert "household_count" in table.column_names
        assert "eligible_count" in table.column_names
        assert "mean_aid" in table.column_names
        assert "total_aid" in table.column_names
