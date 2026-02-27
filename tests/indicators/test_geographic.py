"""Tests for geographic indicator computation.

Story 4.2: Implement Geographic Aggregation Indicators
"""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.indicators.geographic import (
    aggregate_by_region,
    assign_regions,
    compute_geographic_indicators,
)
from reformlab.indicators.types import GeographicConfig, RegionIndicators
from reformlab.orchestrator.panel import PanelOutput


@pytest.fixture
def simple_regional_panel() -> PanelOutput:
    """Create a simple panel with 100 households across 4 regions.

    Region distribution:
    - "11" (Île-de-France): 40 households
    - "44" (Grand Est): 30 households
    - "75" (Nouvelle-Aquitaine): 20 households
    - "84" (Auvergne-Rhône-Alpes): 10 households
    """
    num_households = 100
    household_ids = list(range(num_households))
    years = [2020] * num_households

    # Assign regions
    regions = []
    incomes = []
    taxes = []

    for i in range(num_households):
        if i < 40:
            regions.append("11")  # Île-de-France
            incomes.append(50000.0 + i * 1000.0)
            taxes.append(5000.0 + i * 100.0)
        elif i < 70:
            regions.append("44")  # Grand Est
            incomes.append(40000.0 + (i - 40) * 800.0)
            taxes.append(4000.0 + (i - 40) * 80.0)
        elif i < 90:
            regions.append("75")  # Nouvelle-Aquitaine
            incomes.append(35000.0 + (i - 70) * 600.0)
            taxes.append(3500.0 + (i - 70) * 60.0)
        else:
            regions.append("84")  # Auvergne-Rhône-Alpes
            incomes.append(45000.0 + (i - 90) * 900.0)
            taxes.append(4500.0 + (i - 90) * 90.0)

    table = pa.table(
        {
            "household_id": pa.array(household_ids, type=pa.int64()),
            "year": pa.array(years, type=pa.int64()),
            "region_code": pa.array(regions, type=pa.utf8()),
            "income": pa.array(incomes, type=pa.float64()),
            "tax": pa.array(taxes, type=pa.float64()),
        }
    )

    metadata = {
        "start_year": 2020,
        "end_year": 2020,
        "seed": 42,
    }

    return PanelOutput(table=table, metadata=metadata)


@pytest.fixture
def multi_year_regional_panel() -> PanelOutput:
    """Create a multi-year panel with 2 regions and 2 years."""
    household_ids = []
    years = []
    regions = []
    incomes = []
    taxes = []

    # 20 households, 2 years = 40 rows
    for year in [2020, 2021]:
        for hh_id in range(20):
            household_ids.append(hh_id)
            years.append(year)
            regions.append("11" if hh_id < 10 else "44")
            base_income = 30000.0 + hh_id * 2000.0
            year_adj = (year - 2020) * 1000.0
            incomes.append(base_income + year_adj)
            taxes.append(base_income * 0.1)

    table = pa.table(
        {
            "household_id": pa.array(household_ids, type=pa.int64()),
            "year": pa.array(years, type=pa.int64()),
            "region_code": pa.array(regions, type=pa.utf8()),
            "income": pa.array(incomes, type=pa.float64()),
            "tax": pa.array(taxes, type=pa.float64()),
        }
    )

    metadata = {
        "start_year": 2020,
        "end_year": 2021,
        "seed": 42,
    }

    return PanelOutput(table=table, metadata=metadata)


@pytest.fixture
def panel_with_missing_regions() -> PanelOutput:
    """Create a panel where 20% of households have null region codes."""
    num_households = 50
    household_ids = list(range(num_households))
    years = [2020] * num_households

    # Every 5th household has null region
    regions = []
    for i in range(num_households):
        if i % 5 == 0:
            regions.append(None)
        else:
            regions.append("11" if i % 2 == 0 else "44")

    incomes = [30000.0 + i * 1000.0 for i in range(num_households)]
    taxes = [3000.0 + i * 100.0 for i in range(num_households)]

    table = pa.table(
        {
            "household_id": pa.array(household_ids, type=pa.int64()),
            "year": pa.array(years, type=pa.int64()),
            "region_code": pa.array(regions, type=pa.utf8()),
            "income": pa.array(incomes, type=pa.float64()),
            "tax": pa.array(taxes, type=pa.float64()),
        }
    )

    metadata = {
        "start_year": 2020,
        "end_year": 2020,
        "seed": 42,
    }

    return PanelOutput(table=table, metadata=metadata)


@pytest.fixture
def panel_with_unmatched_regions() -> PanelOutput:
    """Create a panel with some region codes not in reference table."""
    num_households = 60
    household_ids = list(range(num_households))
    years = [2020] * num_households

    # Mix of valid and invalid region codes
    regions = []
    for i in range(num_households):
        if i < 20:
            regions.append("11")  # Valid
        elif i < 40:
            regions.append("44")  # Valid
        else:
            regions.append("99")  # Invalid (not in reference)

    incomes = [30000.0 + i * 1000.0 for i in range(num_households)]
    taxes = [3000.0 + i * 100.0 for i in range(num_households)]

    table = pa.table(
        {
            "household_id": pa.array(household_ids, type=pa.int64()),
            "year": pa.array(years, type=pa.int64()),
            "region_code": pa.array(regions, type=pa.utf8()),
            "income": pa.array(incomes, type=pa.float64()),
            "tax": pa.array(taxes, type=pa.float64()),
        }
    )

    metadata = {
        "start_year": 2020,
        "end_year": 2020,
        "seed": 42,
    }

    return PanelOutput(table=table, metadata=metadata)


@pytest.fixture
def reference_region_table() -> pa.Table:
    """Create a reference table with valid region codes."""
    return pa.table(
        {
            "region_code": pa.array(["11", "44", "75", "84"], type=pa.utf8()),
            "region_name": pa.array(
                [
                    "Île-de-France",
                    "Grand Est",
                    "Nouvelle-Aquitaine",
                    "Auvergne-Rhône-Alpes",
                ],
                type=pa.utf8(),
            ),
        }
    )


def test_assign_regions_basic(simple_regional_panel: PanelOutput) -> None:
    """Test basic region assignment without reference table."""
    table, excluded_count, unmatched_count = assign_regions(
        simple_regional_panel.table,
        "region_code",
    )

    assert table.num_rows == 100
    assert excluded_count == 0
    assert unmatched_count == 0
    assert "region_code" in table.column_names


def test_assign_regions_with_missing(panel_with_missing_regions: PanelOutput) -> None:
    """Test region assignment with missing region codes."""
    with pytest.warns(
        UserWarning, match="Excluded 10 household.*missing/blank region"
    ):
        table, excluded_count, unmatched_count = assign_regions(
            panel_with_missing_regions.table,
            "region_code",
        )

    assert table.num_rows == 40  # 50 - 10 missing
    assert excluded_count == 10
    assert unmatched_count == 0


def test_assign_regions_with_reference_table(
    panel_with_unmatched_regions: PanelOutput,
    reference_region_table: pa.Table,
) -> None:
    """Test region assignment with reference table validation."""
    with pytest.warns(UserWarning, match="Found 20 household.*unmatched region"):
        table, excluded_count, unmatched_count = assign_regions(
            panel_with_unmatched_regions.table,
            "region_code",
            reference_region_table,
        )

    assert table.num_rows == 60
    assert excluded_count == 0
    assert unmatched_count == 20

    # Check that unmatched codes are replaced with "_UNMATCHED"
    region_col = table.column("region_code").to_pylist()
    assert region_col.count("_UNMATCHED") == 20
    assert region_col.count("11") == 20
    assert region_col.count("44") == 20
    assert region_col.count("99") == 0


def test_assign_regions_missing_field_error(simple_regional_panel: PanelOutput) -> None:
    """Test that missing region field raises ValueError."""
    with pytest.raises(ValueError, match="Region field 'nonexistent' not found"):
        assign_regions(simple_regional_panel.table, "nonexistent")


def test_assign_regions_all_null_error(panel_with_missing_regions: PanelOutput) -> None:
    """Test that all-null region codes raises ValueError."""
    # Create a panel where all regions are null
    table = pa.table(
        {
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "year": pa.array([2020, 2020, 2020], type=pa.int64()),
            "region_code": pa.array([None, None, None], type=pa.utf8()),
            "income": pa.array([10000.0, 20000.0, 30000.0], type=pa.float64()),
        }
    )

    with pytest.raises(ValueError, match="No households with valid region codes"):
        assign_regions(table, "region_code")


def test_assign_regions_with_blank_codes() -> None:
    """Test that blank/whitespace region codes are treated as missing."""
    table = pa.table(
        {
            "household_id": pa.array([1, 2, 3, 4], type=pa.int64()),
            "year": pa.array([2020, 2020, 2020, 2020], type=pa.int64()),
            "region_code": pa.array(["11", "", "  ", "44"], type=pa.utf8()),
            "income": pa.array([10000.0, 20000.0, 30000.0, 40000.0], type=pa.float64()),
        }
    )

    with pytest.warns(UserWarning, match="Excluded 2 household.*missing/blank region"):
        filtered, excluded_count, unmatched_count = assign_regions(table, "region_code")

    assert filtered.num_rows == 2
    assert excluded_count == 2
    assert unmatched_count == 0
    assert filtered.column("region_code").to_pylist() == ["11", "44"]


def test_assign_regions_with_empty_reference_table(
    simple_regional_panel: PanelOutput,
) -> None:
    """Test that an empty reference table groups all codes as unmatched."""
    empty_reference = pa.table({"region_code": pa.array([], type=pa.utf8())})

    with pytest.warns(UserWarning, match="Found 100 household.*unmatched region"):
        table, excluded_count, unmatched_count = assign_regions(
            simple_regional_panel.table,
            "region_code",
            empty_reference,
        )

    assert excluded_count == 0
    assert unmatched_count == 100
    assert set(table.column("region_code").to_pylist()) == {"_UNMATCHED"}


def test_aggregate_by_region_basic(simple_regional_panel: PanelOutput) -> None:
    """Test basic region aggregation."""
    table, _, _ = assign_regions(simple_regional_panel.table, "region_code")
    agg_table = aggregate_by_region(
        table,
        ["income", "tax"],
        "region_code",
        group_by_year=False,
    )

    # Should have 4 regions × 2 fields = 8 rows
    assert agg_table.num_rows == 8

    # Check schema
    assert set(agg_table.column_names) == {
        "field_name",
        "region",
        "count",
        "mean",
        "median",
        "sum",
        "min",
        "max",
    }

    # Check region 11 (Île-de-France) income stats
    region_11_income = agg_table.filter(
        pa.compute.and_(
            pa.compute.equal(agg_table.column("region"), pa.scalar("11")),
            pa.compute.equal(agg_table.column("field_name"), pa.scalar("income")),
        )
    )
    assert region_11_income.num_rows == 1
    assert region_11_income.column("count")[0].as_py() == 40


def test_aggregate_by_region_with_year(multi_year_regional_panel: PanelOutput) -> None:
    """Test region aggregation grouped by year."""
    table, _, _ = assign_regions(multi_year_regional_panel.table, "region_code")
    agg_table = aggregate_by_region(
        table,
        ["income", "tax"],
        "region_code",
        group_by_year=True,
    )

    # Should have 2 regions × 2 years × 2 fields = 8 rows
    assert agg_table.num_rows == 8

    # Check schema includes year
    assert "year" in agg_table.column_names

    # Check region 11, year 2020 income stats
    region_11_2020_income = agg_table.filter(
        pa.compute.and_(
            pa.compute.and_(
                pa.compute.equal(agg_table.column("region"), pa.scalar("11")),
                pa.compute.equal(agg_table.column("year"), pa.scalar(2020)),
            ),
            pa.compute.equal(agg_table.column("field_name"), pa.scalar("income")),
        )
    )
    assert region_11_2020_income.num_rows == 1
    assert region_11_2020_income.column("count")[0].as_py() == 10


def test_compute_geographic_indicators_basic(
    simple_regional_panel: PanelOutput,
) -> None:
    """Test basic geographic indicator computation."""
    result = compute_geographic_indicators(simple_regional_panel)

    assert len(result.indicators) == 8  # 4 regions × 2 fields
    assert result.excluded_count == 0
    assert result.unmatched_count == 0
    assert len(result.warnings) == 0

    # Check metadata
    assert result.metadata["region_field"] == "region_code"
    assert result.metadata["aggregate_years"] is True
    assert result.metadata["excluded_count"] == 0
    assert result.metadata["unmatched_count"] == 0

    # Check indicator types
    for ind in result.indicators:
        assert isinstance(ind, RegionIndicators)
        assert ind.region in ["11", "44", "75", "84"]
        assert ind.field_name in ["income", "tax"]


def test_compute_geographic_indicators_with_config(
    simple_regional_panel: PanelOutput,
) -> None:
    """Test geographic indicators with custom config."""
    config = GeographicConfig(
        region_field="region_code",
        by_year=False,
        aggregate_years=True,
    )

    result = compute_geographic_indicators(simple_regional_panel, config)

    assert len(result.indicators) == 8
    assert all(ind.year is None for ind in result.indicators)


def test_compute_geographic_indicators_by_year(
    multi_year_regional_panel: PanelOutput,
) -> None:
    """Test geographic indicators grouped by year."""
    config = GeographicConfig(by_year=True)

    result = compute_geographic_indicators(multi_year_regional_panel, config)

    # 2 regions × 2 years × 2 fields = 8 indicators
    assert len(result.indicators) == 8

    # Check that year is populated
    years = {ind.year for ind in result.indicators}
    assert years == {2020, 2021}


def test_compute_geographic_indicators_aggregate_years(
    multi_year_regional_panel: PanelOutput,
) -> None:
    """Test geographic indicators aggregated across all years."""
    config = GeographicConfig(by_year=False, aggregate_years=True)

    result = compute_geographic_indicators(multi_year_regional_panel, config)

    # 2 regions × 2 fields = 4 indicators (years collapsed)
    assert len(result.indicators) == 4
    assert all(ind.year is None for ind in result.indicators)

    # Region 11 has 10 households/year across 2 years.
    income_r11 = next(
        ind
        for ind in result.indicators
        if ind.field_name == "income" and ind.region == "11"
    )
    assert income_r11.count == 20


def test_compute_geographic_indicators_with_missing_regions(
    panel_with_missing_regions: PanelOutput,
) -> None:
    """Test geographic indicators with missing region codes."""
    result = compute_geographic_indicators(panel_with_missing_regions)

    assert result.excluded_count == 10
    assert len(result.warnings) == 1
    assert "Excluded 10 household" in result.warnings[0]


def test_compute_geographic_indicators_with_reference_table(
    panel_with_unmatched_regions: PanelOutput,
    reference_region_table: pa.Table,
) -> None:
    """Test geographic indicators with reference table validation."""
    config = GeographicConfig(reference_table=reference_region_table)

    result = compute_geographic_indicators(panel_with_unmatched_regions, config)

    assert result.unmatched_count == 20
    assert len(result.warnings) == 1
    assert "Found 20 household" in result.warnings[0]

    # Check that _UNMATCHED category appears in results
    unmatched_indicators = [
        ind for ind in result.indicators if ind.region == "_UNMATCHED"
    ]
    assert len(unmatched_indicators) == 2  # income and tax


def test_indicator_result_to_table_geographic(
    simple_regional_panel: PanelOutput,
) -> None:
    """Test that IndicatorResult.to_table() works for geographic indicators."""
    result = compute_geographic_indicators(simple_regional_panel)
    table = result.to_table()

    # Check schema
    assert set(table.column_names) == {
        "field_name",
        "region",
        "year",
        "metric",
        "value",
    }

    # Should have 8 indicators × 6 metrics = 48 rows
    assert table.num_rows == 48

    # Check that region column is present and has correct type
    region_col = table.column("region")
    assert region_col.type == pa.utf8()

    # Check metric names
    metrics = set(table.column("metric").to_pylist())
    assert metrics == {"count", "mean", "median", "sum", "min", "max"}


def test_indicator_result_to_table_empty_geographic() -> None:
    """Test that empty geographic result produces stable schema."""
    from reformlab.indicators.types import IndicatorResult

    result = IndicatorResult(
        indicators=[],
        metadata={"region_field": "region_code"},  # Signal geographic type
        warnings=[],
        excluded_count=0,
        unmatched_count=0,
    )

    table = result.to_table()

    # Check empty table has correct schema
    assert set(table.column_names) == {
        "field_name",
        "region",
        "year",
        "metric",
        "value",
    }
    assert table.num_rows == 0


def test_aggregate_by_region_metric_correctness(
    simple_regional_panel: PanelOutput,
) -> None:
    """Test that aggregation metrics are computed correctly."""
    table, _, _ = assign_regions(simple_regional_panel.table, "region_code")
    agg_table = aggregate_by_region(
        table,
        ["income"],
        "region_code",
        group_by_year=False,
    )

    # Get region 11 income stats (40 households, incomes from 50000 to 89000)
    region_11 = agg_table.filter(
        pa.compute.and_(
            pa.compute.equal(agg_table.column("region"), pa.scalar("11")),
            pa.compute.equal(agg_table.column("field_name"), pa.scalar("income")),
        )
    )

    assert region_11.num_rows == 1
    count = region_11.column("count")[0].as_py()
    mean = region_11.column("mean")[0].as_py()
    min_val = region_11.column("min")[0].as_py()
    max_val = region_11.column("max")[0].as_py()
    sum_val = region_11.column("sum")[0].as_py()

    assert count == 40
    assert min_val == 50000.0
    assert max_val == 89000.0
    assert abs(mean - 69500.0) < 1.0  # (50000 + 89000) / 2
    assert abs(sum_val - (40 * 69500.0)) < 100.0
