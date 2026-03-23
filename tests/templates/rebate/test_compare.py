# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for rebate batch execution and comparison utilities."""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.templates.packs import load_rebate_template
from reformlab.templates.rebate.compare import (
    ComparisonResult,
    compare_rebate_decile_impacts,
    rebate_decile_results_to_table,
    run_rebate_batch,
)
from reformlab.templates.rebate.compute import (
    RebateDecileResults,
    RebateResult,
)
from reformlab.templates.schema import (
    BaselineScenario,
    PolicyType,
    RebateParameters,
    YearSchedule,
)


@pytest.fixture()
def sample_population() -> pa.Table:
    """Create a sample population with income data."""
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
        }
    )


class TestRunRebateBatch:
    """Tests for batch rebate execution."""

    def test_run_batch_with_single_scenario(self, sample_population: pa.Table) -> None:
        """Batch run with single scenario returns dict with one result."""
        scenario = load_rebate_template("rebate-progressive-income")
        rebate_pools = {scenario.name: 10000.0}
        results = run_rebate_batch(sample_population, [scenario], rebate_pools, 2026)

        assert len(results) == 1
        assert scenario.name in results
        assert isinstance(results[scenario.name], RebateResult)

    def test_run_batch_with_multiple_scenarios(
        self, sample_population: pa.Table
    ) -> None:
        """Batch run with multiple scenarios returns dict with all results."""
        scenario1 = BaselineScenario(
            name="Rebate Lump Sum",
            policy_type=PolicyType.REBATE,
            year_schedule=YearSchedule(2026, 2036),
            policy=RebateParameters(
                rate_schedule={2026: 100.0},
                rebate_type="lump_sum",
            ),
        )
        scenario2 = BaselineScenario(
            name="Rebate Progressive",
            policy_type=PolicyType.REBATE,
            year_schedule=YearSchedule(2026, 2036),
            policy=RebateParameters(
                rate_schedule={2026: 100.0},
                rebate_type="progressive_dividend",
                income_weights={"decile_1": 2.0, "decile_10": 0.5},
            ),
        )

        rebate_pools = {"Rebate Lump Sum": 10000.0, "Rebate Progressive": 10000.0}
        results = run_rebate_batch(
            sample_population, [scenario1, scenario2], rebate_pools, 2026
        )

        assert len(results) == 2
        assert "Rebate Lump Sum" in results
        assert "Rebate Progressive" in results


class TestCompareRebateDecileImpacts:
    """Tests for rebate comparison by decile."""

    def test_compare_produces_comparison_result(
        self, sample_population: pa.Table
    ) -> None:
        """Comparison returns ComparisonResult with all components."""
        scenario = load_rebate_template("rebate-progressive-income")
        rebate_pools = {scenario.name: 10000.0}
        results = run_rebate_batch(sample_population, [scenario], rebate_pools, 2026)
        comparison = compare_rebate_decile_impacts(results)

        assert isinstance(comparison, ComparisonResult)
        assert len(comparison.scenarios) == 1
        assert comparison.comparison_table is not None

    def test_compare_table_has_decile_column(self, sample_population: pa.Table) -> None:
        """Comparison table has decile column with 1-10."""
        scenario = load_rebate_template("rebate-progressive-income")
        rebate_pools = {scenario.name: 10000.0}
        results = run_rebate_batch(sample_population, [scenario], rebate_pools, 2026)
        comparison = compare_rebate_decile_impacts(results)

        table = comparison.comparison_table
        assert "decile" in table.column_names
        deciles = table.column("decile").to_pylist()
        assert deciles == list(range(1, 11))

    def test_compare_table_includes_policy_specific_metrics_for_each_scenario(
        self, sample_population: pa.Table
    ) -> None:
        """Comparison exposes rebate means/totals by scenario."""
        scenario_lump = BaselineScenario(
            name="Rebate Lump Sum",
            policy_type=PolicyType.REBATE,
            year_schedule=YearSchedule(2026, 2036),
            policy=RebateParameters(
                rate_schedule={2026: 100.0},
                rebate_type="lump_sum",
            ),
        )
        scenario_prog = BaselineScenario(
            name="Rebate Progressive",
            policy_type=PolicyType.REBATE,
            year_schedule=YearSchedule(2026, 2036),
            policy=RebateParameters(
                rate_schedule={2026: 100.0},
                rebate_type="progressive_dividend",
                income_weights={"decile_1": 2.0, "decile_10": 0.5},
            ),
        )
        rebate_pools = {"Rebate Lump Sum": 10000.0, "Rebate Progressive": 10000.0}
        results = run_rebate_batch(
            sample_population, [scenario_lump, scenario_prog], rebate_pools, 2026
        )
        comparison = compare_rebate_decile_impacts(results)
        columns = set(comparison.comparison_table.column_names)

        assert "Rebate_Lump_Sum_mean_rebate" in columns
        assert "Rebate_Lump_Sum_total_rebate" in columns
        assert "Rebate_Progressive_mean_rebate" in columns
        assert "Rebate_Progressive_total_rebate" in columns


class TestRebateDecileResultsToTable:
    """Tests for decile results conversion to table."""

    def test_to_table_has_expected_columns(self) -> None:
        """Table has all expected columns."""
        decile_results = RebateDecileResults(
            decile=tuple(range(1, 11)),
            household_count=(10,) * 10,
            mean_rebate=(1000.0,) * 10,
            total_rebate=(10000.0,) * 10,
        )

        table = rebate_decile_results_to_table(decile_results)

        assert "decile" in table.column_names
        assert "household_count" in table.column_names
        assert "mean_rebate" in table.column_names
        assert "total_rebate" in table.column_names
        assert table.num_rows == 10
