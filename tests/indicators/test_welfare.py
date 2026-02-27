"""Tests for welfare indicator computation.

Story 4.3: Implement Welfare Indicators

Tests cover:
- Household-level net change computation
- Winner/loser/neutral classification with various thresholds
- Unmatched household handling
- All-neutral scenario (AC-7)
- Welfare metrics correctness
- Grouping by decile and region
- Multi-year support (by_year and aggregate_years)
- IndicatorResult.to_table() schema stability
"""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.indicators import (
    IndicatorResult,
    WelfareConfig,
    WelfareIndicators,
    compute_welfare_indicators,
)
from reformlab.orchestrator.panel import PanelOutput


@pytest.fixture
def baseline_panel() -> PanelOutput:
    """Create a baseline panel with disposable income, income for deciles, and region."""
    table = pa.table(
        {
            "household_id": pa.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], type=pa.int64()),
            "year": pa.array([2025] * 10, type=pa.int64()),
            "disposable_income": pa.array(
                [
                    10000.0,
                    20000.0,
                    30000.0,
                    40000.0,
                    50000.0,
                    60000.0,
                    70000.0,
                    80000.0,
                    90000.0,
                    100000.0,
                ],
                type=pa.float64(),
            ),
            "income": pa.array(
                [
                    15000.0,
                    25000.0,
                    35000.0,
                    45000.0,
                    55000.0,
                    65000.0,
                    75000.0,
                    85000.0,
                    95000.0,
                    105000.0,
                ],
                type=pa.float64(),
            ),
            "region_code": pa.array(
                ["11", "11", "11", "11", "11", "75", "75", "75", "75", "75"],
                type=pa.utf8(),
            ),
        }
    )
    return PanelOutput(table=table, metadata={"scenario": "baseline"})


@pytest.fixture
def reform_panel() -> PanelOutput:
    """Create a reform panel with different disposable income (some winners, some losers)."""
    table = pa.table(
        {
            "household_id": pa.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], type=pa.int64()),
            "year": pa.array([2025] * 10, type=pa.int64()),
            "disposable_income": pa.array(
                [
                    12000.0,
                    18000.0,
                    30000.0,
                    42000.0,
                    50000.0,
                    65000.0,
                    75000.0,
                    85000.0,
                    95000.0,
                    105000.0,
                ],
                type=pa.float64(),
            ),
            "income": pa.array(
                [
                    15000.0,
                    25000.0,
                    35000.0,
                    45000.0,
                    55000.0,
                    65000.0,
                    75000.0,
                    85000.0,
                    95000.0,
                    105000.0,
                ],
                type=pa.float64(),
            ),
            "region_code": pa.array(
                ["11", "11", "11", "11", "11", "75", "75", "75", "75", "75"],
                type=pa.utf8(),
            ),
        }
    )
    return PanelOutput(table=table, metadata={"scenario": "reform"})


@pytest.fixture
def identical_reform_panel(baseline_panel: PanelOutput) -> PanelOutput:
    """Create a reform panel identical to baseline (all neutral scenario)."""
    return PanelOutput(
        table=baseline_panel.table,
        metadata={"scenario": "identical_reform"},
    )


def test_welfare_indicators_basic(
    baseline_panel: PanelOutput,
    reform_panel: PanelOutput,
) -> None:
    """Test basic welfare indicator computation with default config."""
    config = WelfareConfig()
    result = compute_welfare_indicators(baseline_panel, reform_panel, config)

    assert isinstance(result, IndicatorResult)
    assert len(result.indicators) == 10  # 10 deciles
    assert result.metadata["welfare_field"] == "disposable_income"
    assert result.metadata["threshold"] == 0.0
    assert result.metadata["group_type"] == "decile"

    # Check first indicator
    first_ind = result.indicators[0]
    assert isinstance(first_ind, WelfareIndicators)
    assert first_ind.group_type == "decile"
    assert first_ind.year is None  # aggregate_years=True by default


def test_winner_loser_classification(
    baseline_panel: PanelOutput,
    reform_panel: PanelOutput,
) -> None:
    """Test winner/loser/neutral classification correctness."""
    # Expected net changes:
    # HH1: 12000 - 10000 = +2000 (winner)
    # HH2: 18000 - 20000 = -2000 (loser)
    # HH3: 30000 - 30000 = 0 (neutral)
    # HH4: 42000 - 40000 = +2000 (winner)
    # HH5: 50000 - 50000 = 0 (neutral)
    # HH6: 65000 - 60000 = +5000 (winner)
    # HH7: 75000 - 70000 = +5000 (winner)
    # HH8: 85000 - 80000 = +5000 (winner)
    # HH9: 95000 - 90000 = +5000 (winner)
    # HH10: 105000 - 100000 = +5000 (winner)

    config = WelfareConfig(threshold=0.0)
    result = compute_welfare_indicators(baseline_panel, reform_panel, config)

    # Total across all deciles
    total_winners = sum(ind.winner_count for ind in result.indicators)
    total_losers = sum(ind.loser_count for ind in result.indicators)
    total_neutral = sum(ind.neutral_count for ind in result.indicators)

    assert total_winners == 7
    assert total_losers == 1
    assert total_neutral == 2


def test_welfare_metrics_correctness(
    baseline_panel: PanelOutput,
    reform_panel: PanelOutput,
) -> None:
    """Test welfare metric calculations (mean_gain, mean_loss, total_gain, total_loss, net_change)."""
    config = WelfareConfig(threshold=0.0)
    result = compute_welfare_indicators(baseline_panel, reform_panel, config)

    # Aggregate across all deciles
    total_gain = sum(ind.total_gain for ind in result.indicators)
    total_loss = sum(ind.total_loss for ind in result.indicators)
    net_change = sum(ind.net_change for ind in result.indicators)

    # Expected: +2000 (HH1) + 0 (HH3) + 2000 (HH4) + 0 (HH5) + 5000 (HH6) + ... + 5000 (HH10)
    # Winners: HH1 (+2000), HH4 (+2000), HH6-10 (5*5000 = +25000) = +29000
    # Losers: HH2 (-2000) = -2000
    # Net: 29000 - 2000 = 27000

    assert total_gain == pytest.approx(29000.0)
    assert total_loss == pytest.approx(2000.0)
    assert net_change == pytest.approx(27000.0)


def test_welfare_with_threshold(
    baseline_panel: PanelOutput,
    reform_panel: PanelOutput,
) -> None:
    """Test winner/loser classification with non-zero threshold."""
    # With threshold=1000, changes within [-1000, +1000] are neutral
    config = WelfareConfig(threshold=1000.0)
    result = compute_welfare_indicators(baseline_panel, reform_panel, config)

    # Expected:
    # HH3, HH5: 0 (neutral)
    # All others have |change| >= 2000, so winners/losers

    total_winners = sum(ind.winner_count for ind in result.indicators)
    total_losers = sum(ind.loser_count for ind in result.indicators)
    total_neutral = sum(ind.neutral_count for ind in result.indicators)

    assert total_winners == 7
    assert total_losers == 1
    assert total_neutral == 2


def test_all_neutral_scenario(
    baseline_panel: PanelOutput,
    identical_reform_panel: PanelOutput,
) -> None:
    """Test AC-7: scenario where all households are neutral."""
    config = WelfareConfig(threshold=0.0)
    result = compute_welfare_indicators(baseline_panel, identical_reform_panel, config)

    total_winners = sum(ind.winner_count for ind in result.indicators)
    total_losers = sum(ind.loser_count for ind in result.indicators)
    total_neutral = sum(ind.neutral_count for ind in result.indicators)

    assert total_winners == 0
    assert total_losers == 0
    assert total_neutral == 10


def test_unmatched_households_handling() -> None:
    """Test handling of unmatched households (present in only one panel)."""
    # Baseline has households 1-5
    baseline_table = pa.table(
        {
            "household_id": pa.array([1, 2, 3, 4, 5], type=pa.int64()),
            "year": pa.array([2025] * 5, type=pa.int64()),
            "disposable_income": pa.array(
                [10000.0, 20000.0, 30000.0, 40000.0, 50000.0], type=pa.float64()
            ),
            "income": pa.array(
                [15000.0, 25000.0, 35000.0, 45000.0, 55000.0], type=pa.float64()
            ),
        }
    )
    baseline = PanelOutput(table=baseline_table, metadata={})

    # Reform has households 3-7 (1,2 missing, 6,7 new)
    reform_table = pa.table(
        {
            "household_id": pa.array([3, 4, 5, 6, 7], type=pa.int64()),
            "year": pa.array([2025] * 5, type=pa.int64()),
            "disposable_income": pa.array(
                [32000.0, 42000.0, 52000.0, 62000.0, 72000.0], type=pa.float64()
            ),
            "income": pa.array(
                [35000.0, 45000.0, 55000.0, 65000.0, 75000.0], type=pa.float64()
            ),
        }
    )
    reform = PanelOutput(table=reform_table, metadata={})

    config = WelfareConfig()
    result = compute_welfare_indicators(baseline, reform, config)

    # Only households 3,4,5 are matched
    assert result.unmatched_count == 4  # 2 from baseline + 2 from reform
    assert len(result.warnings) > 0
    assert "unmatched" in result.warnings[0].lower()

    # Check that only matched households contribute to counts
    total_count = sum(
        ind.winner_count + ind.loser_count + ind.neutral_count
        for ind in result.indicators
    )
    assert total_count == 3  # Only 3 matched households


def test_welfare_by_year() -> None:
    """Test multi-year welfare indicators with by_year=True."""
    # Create multi-year baseline
    baseline_table = pa.table(
        {
            "household_id": pa.array([1, 2, 1, 2], type=pa.int64()),
            "year": pa.array([2025, 2025, 2026, 2026], type=pa.int64()),
            "disposable_income": pa.array(
                [10000.0, 20000.0, 11000.0, 21000.0], type=pa.float64()
            ),
            "income": pa.array([15000.0, 25000.0, 16000.0, 26000.0], type=pa.float64()),
        }
    )
    baseline = PanelOutput(table=baseline_table, metadata={})

    # Create multi-year reform
    reform_table = pa.table(
        {
            "household_id": pa.array([1, 2, 1, 2], type=pa.int64()),
            "year": pa.array([2025, 2025, 2026, 2026], type=pa.int64()),
            "disposable_income": pa.array(
                [12000.0, 18000.0, 13000.0, 19000.0], type=pa.float64()
            ),
            "income": pa.array([15000.0, 25000.0, 16000.0, 26000.0], type=pa.float64()),
        }
    )
    reform = PanelOutput(table=reform_table, metadata={})

    config = WelfareConfig(by_year=True)
    result = compute_welfare_indicators(baseline, reform, config)

    # Should have indicators for each year
    years = {ind.year for ind in result.indicators}
    assert 2025 in years
    assert 2026 in years

    # Check year-specific counts
    indicators_2025 = [ind for ind in result.indicators if ind.year == 2025]
    indicators_2026 = [ind for ind in result.indicators if ind.year == 2026]

    assert len(indicators_2025) > 0
    assert len(indicators_2026) > 0


def test_welfare_aggregate_years() -> None:
    """Test multi-year welfare indicators with aggregate_years=True."""
    # Create multi-year baseline
    baseline_table = pa.table(
        {
            "household_id": pa.array([1, 2, 1, 2], type=pa.int64()),
            "year": pa.array([2025, 2025, 2026, 2026], type=pa.int64()),
            "disposable_income": pa.array(
                [10000.0, 20000.0, 11000.0, 21000.0], type=pa.float64()
            ),
            "income": pa.array([15000.0, 25000.0, 16000.0, 26000.0], type=pa.float64()),
        }
    )
    baseline = PanelOutput(table=baseline_table, metadata={})

    # Create multi-year reform
    reform_table = pa.table(
        {
            "household_id": pa.array([1, 2, 1, 2], type=pa.int64()),
            "year": pa.array([2025, 2025, 2026, 2026], type=pa.int64()),
            "disposable_income": pa.array(
                [12000.0, 18000.0, 13000.0, 19000.0], type=pa.float64()
            ),
            "income": pa.array([15000.0, 25000.0, 16000.0, 26000.0], type=pa.float64()),
        }
    )
    reform = PanelOutput(table=reform_table, metadata={})

    config = WelfareConfig(by_year=False, aggregate_years=True)
    result = compute_welfare_indicators(baseline, reform, config)

    # All indicators should have year=None (aggregated)
    assert all(ind.year is None for ind in result.indicators)

    # Ensure we matched each household-year pair exactly once (no cross-year cartesian joins)
    total_count = sum(
        ind.winner_count + ind.loser_count + ind.neutral_count
        for ind in result.indicators
    )
    assert total_count == 4


def test_welfare_preserve_year_detail_without_by_year() -> None:
    """Test AC-6 branch: by_year=False and aggregate_years=False keeps year detail."""
    baseline_table = pa.table(
        {
            "household_id": pa.array([1, 2, 1, 2], type=pa.int64()),
            "year": pa.array([2025, 2025, 2026, 2026], type=pa.int64()),
            "disposable_income": pa.array(
                [10000.0, 20000.0, 11000.0, 21000.0], type=pa.float64()
            ),
            "income": pa.array([15000.0, 25000.0, 16000.0, 26000.0], type=pa.float64()),
        }
    )
    baseline = PanelOutput(table=baseline_table, metadata={})

    reform_table = pa.table(
        {
            "household_id": pa.array([1, 2, 1, 2], type=pa.int64()),
            "year": pa.array([2025, 2025, 2026, 2026], type=pa.int64()),
            "disposable_income": pa.array(
                [12000.0, 18000.0, 13000.0, 19000.0], type=pa.float64()
            ),
            "income": pa.array([15000.0, 25000.0, 16000.0, 26000.0], type=pa.float64()),
        }
    )
    reform = PanelOutput(table=reform_table, metadata={})

    config = WelfareConfig(by_year=False, aggregate_years=False)
    result = compute_welfare_indicators(baseline, reform, config)

    years = {ind.year for ind in result.indicators}
    assert years == {2025, 2026}


def test_welfare_group_by_region(
    baseline_panel: PanelOutput,
    reform_panel: PanelOutput,
) -> None:
    """Test welfare indicators grouped by region instead of decile."""
    config = WelfareConfig(group_by_decile=False, group_by_region=True)
    result = compute_welfare_indicators(baseline_panel, reform_panel, config)

    assert result.metadata["group_type"] == "region"
    assert result.metadata["group_by_region"] is True
    assert result.metadata["group_by_decile"] is False

    # Should have indicators for each region
    regions = {ind.group_value for ind in result.indicators}
    assert "11" in regions
    assert "75" in regions

    # Check that group_type is "region"
    for ind in result.indicators:
        assert ind.group_type == "region"


def test_welfare_to_table_schema(
    baseline_panel: PanelOutput,
    reform_panel: PanelOutput,
) -> None:
    """Test IndicatorResult.to_table() schema stability for welfare indicators."""
    config = WelfareConfig()
    result = compute_welfare_indicators(baseline_panel, reform_panel, config)

    table = result.to_table()

    # Verify column schema
    expected_columns = ["field_name", "decile", "year", "metric", "value"]
    assert table.column_names == expected_columns

    # Verify column types
    assert table.schema.field("field_name").type == pa.utf8()
    assert table.schema.field("decile").type == pa.int64()
    assert table.schema.field("year").type == pa.int64()
    assert table.schema.field("metric").type == pa.utf8()
    assert table.schema.field("value").type == pa.float64()

    # Verify metrics are present
    metrics = set(table.column("metric").to_pylist())
    expected_metrics = {
        "winner_count",
        "loser_count",
        "neutral_count",
        "mean_gain",
        "mean_loss",
        "median_change",
        "total_gain",
        "total_loss",
        "net_change",
    }
    assert expected_metrics.issubset(metrics)


def test_welfare_to_table_region_schema(
    baseline_panel: PanelOutput,
    reform_panel: PanelOutput,
) -> None:
    """Test welfare to_table() uses region column when grouped by region."""
    config = WelfareConfig(group_by_decile=False, group_by_region=True)
    result = compute_welfare_indicators(baseline_panel, reform_panel, config)

    table = result.to_table()
    assert table.column_names == ["field_name", "region", "year", "metric", "value"]
    assert table.schema.field("region").type == pa.utf8()


def test_welfare_custom_income_field() -> None:
    """Test custom income_field is carried through household comparison for deciles."""
    baseline_table = pa.table(
        {
            "household_id": pa.array([1, 2], type=pa.int64()),
            "year": pa.array([2025, 2025], type=pa.int64()),
            "disposable_income": pa.array([10000.0, 20000.0], type=pa.float64()),
            "income_alt": pa.array([15000.0, 25000.0], type=pa.float64()),
        }
    )
    reform_table = pa.table(
        {
            "household_id": pa.array([1, 2], type=pa.int64()),
            "year": pa.array([2025, 2025], type=pa.int64()),
            "disposable_income": pa.array([12000.0, 18000.0], type=pa.float64()),
            "income_alt": pa.array([15000.0, 25000.0], type=pa.float64()),
        }
    )
    baseline = PanelOutput(table=baseline_table, metadata={})
    reform = PanelOutput(table=reform_table, metadata={})

    result = compute_welfare_indicators(
        baseline,
        reform,
        WelfareConfig(income_field="income_alt"),
    )

    total_count = sum(
        ind.winner_count + ind.loser_count + ind.neutral_count
        for ind in result.indicators
    )
    assert total_count == 2


def test_welfare_empty_result() -> None:
    """Test welfare indicators with empty panels."""
    empty_table = pa.table(
        {
            "household_id": pa.array([], type=pa.int64()),
            "year": pa.array([], type=pa.int64()),
            "disposable_income": pa.array([], type=pa.float64()),
            "income": pa.array([], type=pa.float64()),
        }
    )
    baseline = PanelOutput(table=empty_table, metadata={})
    reform = PanelOutput(table=empty_table, metadata={})

    config = WelfareConfig()

    # Should raise error because no households to compare
    with pytest.raises(ValueError, match="No households with valid income"):
        compute_welfare_indicators(baseline, reform, config)


def test_welfare_missing_field_error(baseline_panel: PanelOutput) -> None:
    """Test error when welfare field is missing from panel."""
    # Create reform panel without disposable_income
    reform_table = pa.table(
        {
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "year": pa.array([2025] * 3, type=pa.int64()),
            "income": pa.array([15000.0, 25000.0, 35000.0], type=pa.float64()),
        }
    )
    reform = PanelOutput(table=reform_table, metadata={})

    config = WelfareConfig(welfare_field="disposable_income")

    with pytest.raises(
        ValueError, match="Welfare field 'disposable_income' not found in reform panel"
    ):
        compute_welfare_indicators(baseline_panel, reform, config)


def test_welfare_invalid_grouping_config() -> None:
    """Test error when both group_by_decile and group_by_region are False."""
    baseline_table = pa.table(
        {
            "household_id": pa.array([1, 2], type=pa.int64()),
            "year": pa.array([2025, 2025], type=pa.int64()),
            "disposable_income": pa.array([10000.0, 20000.0], type=pa.float64()),
        }
    )
    baseline = PanelOutput(table=baseline_table, metadata={})
    reform = PanelOutput(table=baseline_table, metadata={})

    config = WelfareConfig(group_by_decile=False, group_by_region=False)

    with pytest.raises(
        ValueError,
        match="At least one of group_by_decile or group_by_region must be True",
    ):
        compute_welfare_indicators(baseline, reform, config)


def test_welfare_decile_precedence(
    baseline_panel: PanelOutput,
    reform_panel: PanelOutput,
) -> None:
    """Test that decile grouping takes precedence when both are True."""
    config = WelfareConfig(group_by_decile=True, group_by_region=True)
    result = compute_welfare_indicators(baseline_panel, reform_panel, config)

    # Should use decile grouping (takes precedence)
    assert result.metadata["group_type"] == "decile"
    for ind in result.indicators:
        assert ind.group_type == "decile"


def test_welfare_mean_gain_losers_only() -> None:
    """Test mean_gain and mean_loss calculations with all winners or all losers."""
    # All winners
    baseline_table = pa.table(
        {
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "year": pa.array([2025] * 3, type=pa.int64()),
            "disposable_income": pa.array(
                [10000.0, 20000.0, 30000.0], type=pa.float64()
            ),
            "income": pa.array([15000.0, 25000.0, 35000.0], type=pa.float64()),
        }
    )
    baseline = PanelOutput(table=baseline_table, metadata={})

    reform_table = pa.table(
        {
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "year": pa.array([2025] * 3, type=pa.int64()),
            "disposable_income": pa.array(
                [12000.0, 22000.0, 32000.0], type=pa.float64()
            ),
            "income": pa.array([15000.0, 25000.0, 35000.0], type=pa.float64()),
        }
    )
    reform = PanelOutput(table=reform_table, metadata={})

    config = WelfareConfig()
    result = compute_welfare_indicators(baseline, reform, config)

    # All households are winners
    assert sum(ind.winner_count for ind in result.indicators) == 3
    assert sum(ind.loser_count for ind in result.indicators) == 0

    # mean_loss should be 0.0 (no losers)
    for ind in result.indicators:
        assert ind.mean_loss == 0.0


def test_welfare_metadata_completeness(
    baseline_panel: PanelOutput,
    reform_panel: PanelOutput,
) -> None:
    """Test that metadata contains all expected fields."""
    config = WelfareConfig(
        welfare_field="disposable_income",
        threshold=100.0,
        by_year=True,
        group_by_decile=True,
    )
    result = compute_welfare_indicators(baseline_panel, reform_panel, config)

    # Check metadata keys
    assert "welfare_field" in result.metadata
    assert "threshold" in result.metadata
    assert "by_year" in result.metadata
    assert "aggregate_years" in result.metadata
    assert "group_by_year" in result.metadata
    assert "group_by_decile" in result.metadata
    assert "group_by_region" in result.metadata
    assert "group_type" in result.metadata
    assert "baseline_panel_shape" in result.metadata
    assert "reform_panel_shape" in result.metadata
    assert "baseline_metadata" in result.metadata
    assert "reform_metadata" in result.metadata
    assert "unmatched_count" in result.metadata
    assert "excluded_count" in result.metadata

    # Check values
    assert result.metadata["welfare_field"] == "disposable_income"
    assert result.metadata["threshold"] == 100.0
    assert result.metadata["by_year"] is True
