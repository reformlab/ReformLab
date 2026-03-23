# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for subsidy batch execution and comparison utilities."""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.templates.packs import load_subsidy_template
from reformlab.templates.schema import (
    BaselineScenario,
    PolicyType,
    SubsidyParameters,
    YearSchedule,
)
from reformlab.templates.subsidy.compare import (
    ComparisonResult,
    compare_subsidy_decile_impacts,
    run_subsidy_batch,
    subsidy_decile_results_to_table,
)
from reformlab.templates.subsidy.compute import (
    SubsidyDecileResults,
    SubsidyResult,
)


@pytest.fixture()
def sample_population() -> pa.Table:
    """Create a sample population with income and category data."""
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
            "owner_occupier": pa.array(
                [True, False, True, True, False, True, False, True, True, False],
                type=pa.bool_(),
            ),
            "low_efficiency_home": pa.array(
                [True, True, False, True, False, False, True, False, True, True],
                type=pa.bool_(),
            ),
        }
    )


class TestRunSubsidyBatch:
    """Tests for batch subsidy execution."""

    def test_run_batch_with_single_scenario(self, sample_population: pa.Table) -> None:
        """Batch run with single scenario returns dict with one result."""
        scenario = load_subsidy_template("subsidy-energy-retrofit")
        results = run_subsidy_batch(sample_population, [scenario], 2026)

        assert len(results) == 1
        assert scenario.name in results
        assert isinstance(results[scenario.name], SubsidyResult)

    def test_run_batch_with_multiple_scenarios(
        self, sample_population: pa.Table
    ) -> None:
        """Batch run with multiple scenarios returns dict with all results."""
        # Create two variants with different policy
        scenario1 = BaselineScenario(
            name="Subsidy A",
            policy_type=PolicyType.SUBSIDY,
            year_schedule=YearSchedule(2026, 2036),
            policy=SubsidyParameters(
                rate_schedule={2026: 5000.0},
                income_caps={2026: 45000.0},
            ),
        )
        scenario2 = BaselineScenario(
            name="Subsidy B",
            policy_type=PolicyType.SUBSIDY,
            year_schedule=YearSchedule(2026, 2036),
            policy=SubsidyParameters(
                rate_schedule={2026: 3000.0},
                income_caps={2026: 60000.0},
            ),
        )

        results = run_subsidy_batch(sample_population, [scenario1, scenario2], 2026)

        assert len(results) == 2
        assert "Subsidy A" in results
        assert "Subsidy B" in results


class TestCompareSubsidyDecileImpacts:
    """Tests for subsidy comparison by decile."""

    def test_compare_produces_comparison_result(
        self, sample_population: pa.Table
    ) -> None:
        """Comparison returns ComparisonResult with all components."""
        scenario = load_subsidy_template("subsidy-energy-retrofit")
        results = run_subsidy_batch(sample_population, [scenario], 2026)
        comparison = compare_subsidy_decile_impacts(results)

        assert isinstance(comparison, ComparisonResult)
        assert len(comparison.scenarios) == 1
        assert comparison.comparison_table is not None

    def test_compare_table_has_decile_column(self, sample_population: pa.Table) -> None:
        """Comparison table has decile column with 1-10."""
        scenario = load_subsidy_template("subsidy-energy-retrofit")
        results = run_subsidy_batch(sample_population, [scenario], 2026)
        comparison = compare_subsidy_decile_impacts(results)

        table = comparison.comparison_table
        assert "decile" in table.column_names
        deciles = table.column("decile").to_pylist()
        assert deciles == list(range(1, 11))

    def test_compare_table_includes_policy_specific_metrics_for_each_scenario(
        self, sample_population: pa.Table
    ) -> None:
        """Comparison exposes subsidy means/totals and eligibility counts by scenario."""
        scenario_a = BaselineScenario(
            name="Subsidy A",
            policy_type=PolicyType.SUBSIDY,
            year_schedule=YearSchedule(2026, 2036),
            policy=SubsidyParameters(
                rate_schedule={2026: 5000.0},
                income_caps={2026: 45000.0},
            ),
        )
        scenario_b = BaselineScenario(
            name="Subsidy B",
            policy_type=PolicyType.SUBSIDY,
            year_schedule=YearSchedule(2026, 2036),
            policy=SubsidyParameters(
                rate_schedule={2026: 3000.0},
                income_caps={2026: 60000.0},
            ),
        )
        results = run_subsidy_batch(sample_population, [scenario_a, scenario_b], 2026)
        comparison = compare_subsidy_decile_impacts(results)
        columns = set(comparison.comparison_table.column_names)

        assert "Subsidy_A_mean_subsidy" in columns
        assert "Subsidy_A_total_subsidy" in columns
        assert "Subsidy_A_eligible_count" in columns
        assert "Subsidy_B_mean_subsidy" in columns
        assert "Subsidy_B_total_subsidy" in columns
        assert "Subsidy_B_eligible_count" in columns


class TestSubsidyDecileResultsToTable:
    """Tests for decile results conversion to table."""

    def test_to_table_has_expected_columns(self) -> None:
        """Table has all expected columns."""
        decile_results = SubsidyDecileResults(
            decile=tuple(range(1, 11)),
            household_count=(10,) * 10,
            eligible_count=(5,) * 10,
            mean_subsidy=(2500.0,) * 10,
            total_subsidy=(25000.0,) * 10,
        )

        table = subsidy_decile_results_to_table(decile_results)

        assert "decile" in table.column_names
        assert "household_count" in table.column_names
        assert "eligible_count" in table.column_names
        assert "mean_subsidy" in table.column_names
        assert "total_subsidy" in table.column_names
        assert table.num_rows == 10
