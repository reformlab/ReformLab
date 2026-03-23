# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for fiscal indicator computation.

Story 4.4: Implement Fiscal Indicators
"""

import pyarrow as pa
import pytest

from reformlab.indicators import (
    FiscalConfig,
    FiscalIndicators,
    IndicatorResult,
    compute_fiscal_indicators,
)
from reformlab.orchestrator.panel import PanelOutput


@pytest.fixture
def simple_panel():
    """Create a simple single-year panel with fiscal fields."""
    table = pa.table(
        {
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "year": pa.array([2020, 2020, 2020], type=pa.int64()),
            "carbon_tax_collected": pa.array([100.0, 200.0, 150.0], type=pa.float64()),
            "subsidy_paid": pa.array([50.0, 75.0, 60.0], type=pa.float64()),
            "income": pa.array([30000.0, 40000.0, 35000.0], type=pa.float64()),
        }
    )
    metadata = {"start_year": 2020, "end_year": 2020}
    return PanelOutput(table=table, metadata=metadata)


@pytest.fixture
def multi_year_panel():
    """Create a multi-year panel with fiscal fields."""
    table = pa.table(
        {
            "household_id": pa.array([1, 2, 3, 1, 2, 3], type=pa.int64()),
            "year": pa.array([2020, 2020, 2020, 2021, 2021, 2021], type=pa.int64()),
            "carbon_tax_collected": pa.array(
                [100.0, 200.0, 150.0, 110.0, 210.0, 160.0], type=pa.float64()
            ),
            "subsidy_paid": pa.array(
                [50.0, 75.0, 60.0, 55.0, 80.0, 65.0], type=pa.float64()
            ),
            "rebate_paid": pa.array(
                [10.0, 15.0, 12.0, 11.0, 16.0, 13.0], type=pa.float64()
            ),
            "income": pa.array(
                [30000.0, 40000.0, 35000.0, 31000.0, 41000.0, 36000.0],
                type=pa.float64(),
            ),
        }
    )
    metadata = {"start_year": 2020, "end_year": 2021}
    return PanelOutput(table=table, metadata=metadata)


@pytest.fixture
def panel_with_nulls():
    """Create a panel with null values in fiscal fields."""
    table = pa.table(
        {
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "year": pa.array([2020, 2020, 2020], type=pa.int64()),
            "carbon_tax_collected": pa.array([100.0, None, 150.0], type=pa.float64()),
            "subsidy_paid": pa.array([50.0, 75.0, None], type=pa.float64()),
        }
    )
    metadata = {"start_year": 2020, "end_year": 2020}
    return PanelOutput(table=table, metadata=metadata)


@pytest.fixture
def panel_with_integer_nulls():
    """Create a panel with integer fiscal fields containing null values."""
    table = pa.table(
        {
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "year": pa.array([2020, 2020, 2020], type=pa.int64()),
            "carbon_tax_collected": pa.array([100, None, 150], type=pa.int64()),
            "subsidy_paid": pa.array([50, 75, None], type=pa.int64()),
        }
    )
    metadata = {"start_year": 2020, "end_year": 2020}
    return PanelOutput(table=table, metadata=metadata)


@pytest.fixture
def empty_panel():
    """Create an empty panel."""
    table = pa.table(
        {
            "household_id": pa.array([], type=pa.int64()),
            "year": pa.array([], type=pa.int64()),
        }
    )
    metadata = {"start_year": 2020, "end_year": 2020}
    return PanelOutput(table=table, metadata=metadata)


class TestAnnualFiscalComputation:
    """Test annual fiscal indicator computation."""

    def test_basic_annual_computation(self, simple_panel):
        """Test basic annual fiscal computation with revenue and cost fields."""
        config = FiscalConfig(
            revenue_fields=["carbon_tax_collected"],
            cost_fields=["subsidy_paid"],
            by_year=True,
            cumulative=False,
        )

        result = compute_fiscal_indicators(simple_panel, config)

        assert isinstance(result, IndicatorResult)
        assert len(result.indicators) == 1
        assert isinstance(result.indicators[0], FiscalIndicators)

        indicator = result.indicators[0]
        assert indicator.field_name == "fiscal_summary"
        assert indicator.year == 2020
        assert indicator.revenue == pytest.approx(450.0)  # 100 + 200 + 150
        assert indicator.cost == pytest.approx(185.0)  # 50 + 75 + 60
        assert indicator.balance == pytest.approx(265.0)  # 450 - 185

    def test_multi_year_annual_computation(self, multi_year_panel):
        """Test annual computation across multiple years."""
        config = FiscalConfig(
            revenue_fields=["carbon_tax_collected"],
            cost_fields=["subsidy_paid", "rebate_paid"],
            by_year=True,
            cumulative=False,
        )

        result = compute_fiscal_indicators(multi_year_panel, config)

        assert len(result.indicators) == 2

        # Year 2020
        ind_2020 = result.indicators[0]
        assert ind_2020.year == 2020
        assert ind_2020.revenue == pytest.approx(450.0)
        assert ind_2020.cost == pytest.approx(222.0)  # (50+75+60) + (10+15+12)
        assert ind_2020.balance == pytest.approx(228.0)

        # Year 2021
        ind_2021 = result.indicators[1]
        assert ind_2021.year == 2021
        assert ind_2021.revenue == pytest.approx(480.0)  # 110 + 210 + 160
        assert ind_2021.cost == pytest.approx(240.0)  # (55+80+65) + (11+16+13)
        assert ind_2021.balance == pytest.approx(240.0)

    def test_revenue_only(self, simple_panel):
        """Test computation with only revenue fields (no cost)."""
        config = FiscalConfig(
            revenue_fields=["carbon_tax_collected"],
            cost_fields=[],
            by_year=True,
            cumulative=False,
        )

        result = compute_fiscal_indicators(simple_panel, config)

        assert len(result.indicators) == 1
        indicator = result.indicators[0]
        assert indicator.revenue == pytest.approx(450.0)
        assert indicator.cost == pytest.approx(0.0)
        assert indicator.balance == pytest.approx(450.0)

    def test_cost_only(self, simple_panel):
        """Test computation with only cost fields (no revenue)."""
        config = FiscalConfig(
            revenue_fields=[],
            cost_fields=["subsidy_paid"],
            by_year=True,
            cumulative=False,
        )

        result = compute_fiscal_indicators(simple_panel, config)

        assert len(result.indicators) == 1
        indicator = result.indicators[0]
        assert indicator.revenue == pytest.approx(0.0)
        assert indicator.cost == pytest.approx(185.0)
        assert indicator.balance == pytest.approx(-185.0)


class TestCumulativeFiscalComputation:
    """Test cumulative fiscal totals computation."""

    def test_cumulative_computation(self, multi_year_panel):
        """Test cumulative totals computation across years."""
        config = FiscalConfig(
            revenue_fields=["carbon_tax_collected"],
            cost_fields=["subsidy_paid"],
            by_year=True,
            cumulative=True,
        )

        result = compute_fiscal_indicators(multi_year_panel, config)

        assert len(result.indicators) == 2

        # Year 2020
        ind_2020 = result.indicators[0]
        assert ind_2020.cumulative_revenue == pytest.approx(450.0)
        assert ind_2020.cumulative_cost == pytest.approx(185.0)
        assert ind_2020.cumulative_balance == pytest.approx(265.0)

        # Year 2021
        ind_2021 = result.indicators[1]
        assert ind_2021.cumulative_revenue == pytest.approx(930.0)  # 450 + 480
        assert ind_2021.cumulative_cost == pytest.approx(385.0)  # 185 + 200
        assert ind_2021.cumulative_balance == pytest.approx(545.0)  # 265 + 280

    def test_cumulative_not_computed_when_disabled(self, multi_year_panel):
        """Test that cumulative totals are not computed when disabled."""
        config = FiscalConfig(
            revenue_fields=["carbon_tax_collected"],
            cost_fields=["subsidy_paid"],
            by_year=True,
            cumulative=False,
        )

        result = compute_fiscal_indicators(multi_year_panel, config)

        for indicator in result.indicators:
            assert indicator.cumulative_revenue is None
            assert indicator.cumulative_cost is None
            assert indicator.cumulative_balance is None

    def test_cumulative_single_year(self, simple_panel):
        """Test cumulative computation with single year (equals annual)."""
        config = FiscalConfig(
            revenue_fields=["carbon_tax_collected"],
            cost_fields=["subsidy_paid"],
            by_year=True,
            cumulative=True,
        )

        result = compute_fiscal_indicators(simple_panel, config)

        indicator = result.indicators[0]
        assert indicator.cumulative_revenue == indicator.revenue
        assert indicator.cumulative_cost == indicator.cost
        assert indicator.cumulative_balance == indicator.balance


class TestMultiYearModes:
    """Test different multi-year aggregation modes."""

    def test_by_year_true(self, multi_year_panel):
        """Test by_year=True produces one indicator per year."""
        config = FiscalConfig(
            revenue_fields=["carbon_tax_collected"],
            cost_fields=["subsidy_paid"],
            by_year=True,
            cumulative=False,
        )

        result = compute_fiscal_indicators(multi_year_panel, config)

        assert len(result.indicators) == 2
        assert result.indicators[0].year == 2020
        assert result.indicators[1].year == 2021

    def test_by_year_false_aggregate_years_true(self, multi_year_panel):
        """Test aggregation across all years into single total."""
        config = FiscalConfig(
            revenue_fields=["carbon_tax_collected"],
            cost_fields=["subsidy_paid"],
            by_year=False,
            aggregate_years=True,
            cumulative=False,
        )

        result = compute_fiscal_indicators(multi_year_panel, config)

        assert len(result.indicators) == 1
        indicator = result.indicators[0]
        assert indicator.year is None
        assert indicator.revenue == pytest.approx(930.0)  # 450 + 480
        assert indicator.cost == pytest.approx(385.0)  # 185 + 200
        assert indicator.balance == pytest.approx(545.0)
        # No cumulative when no year detail
        assert indicator.cumulative_revenue is None

    def test_by_year_false_aggregate_years_false(self, multi_year_panel):
        """Test preserving annual detail when by_year=False, aggregate_years=False."""
        config = FiscalConfig(
            revenue_fields=["carbon_tax_collected"],
            cost_fields=["subsidy_paid"],
            by_year=False,
            aggregate_years=False,
            cumulative=True,
        )

        result = compute_fiscal_indicators(multi_year_panel, config)

        # Should preserve annual detail
        assert len(result.indicators) == 2
        assert result.indicators[0].year == 2020
        assert result.indicators[1].year == 2021
        # Cumulative should be computed
        assert result.indicators[1].cumulative_revenue is not None


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_panel(self, empty_panel):
        """Test handling of empty panel."""
        config = FiscalConfig(
            revenue_fields=["carbon_tax_collected"],
            cost_fields=["subsidy_paid"],
        )

        result = compute_fiscal_indicators(empty_panel, config)

        assert len(result.indicators) == 0
        assert len(result.warnings) > 0
        assert "empty" in result.warnings[0].lower()

    def test_missing_fiscal_fields(self, simple_panel):
        """Test handling when configured fields don't exist in panel."""
        config = FiscalConfig(
            revenue_fields=["nonexistent_revenue"],
            cost_fields=["nonexistent_cost"],
        )

        result = compute_fiscal_indicators(simple_panel, config)

        assert len(result.indicators) == 0
        assert len(result.warnings) > 0
        assert "no fiscal fields found" in result.warnings[0].lower()

    def test_null_value_handling(self, panel_with_nulls):
        """Test that null values are treated as zero with warning."""
        config = FiscalConfig(
            revenue_fields=["carbon_tax_collected"],
            cost_fields=["subsidy_paid"],
            by_year=True,
            cumulative=False,
        )

        result = compute_fiscal_indicators(panel_with_nulls, config)

        # Should compute successfully
        assert len(result.indicators) == 1
        indicator = result.indicators[0]
        # Nulls treated as 0: 100 + 0 + 150 = 250
        assert indicator.revenue == pytest.approx(250.0)
        # Nulls treated as 0: 50 + 75 + 0 = 125
        assert indicator.cost == pytest.approx(125.0)

        # Should have warnings about null values
        assert len(result.warnings) > 0
        assert any("null" in w.lower() for w in result.warnings)

    def test_integer_fields_with_nulls(self, panel_with_integer_nulls):
        """Test null-as-zero handling for integer fiscal fields."""
        config = FiscalConfig(
            revenue_fields=["carbon_tax_collected"],
            cost_fields=["subsidy_paid"],
            by_year=True,
            cumulative=False,
        )

        result = compute_fiscal_indicators(panel_with_integer_nulls, config)

        assert len(result.indicators) == 1
        indicator = result.indicators[0]
        assert indicator.revenue == pytest.approx(250.0)
        assert indicator.cost == pytest.approx(125.0)
        assert indicator.balance == pytest.approx(125.0)
        assert any("null value(s)" in warning for warning in result.warnings)

    def test_no_revenue_or_cost_fields_configured(self, simple_panel):
        """Test error when no fields are configured."""
        config = FiscalConfig(
            revenue_fields=[],
            cost_fields=[],
        )

        with pytest.raises(
            ValueError,
            match="At least one revenue field or cost field must be configured",
        ):
            compute_fiscal_indicators(simple_panel, config)

    def test_partial_field_match(self, simple_panel):
        """Test when only some configured fields exist in panel."""
        config = FiscalConfig(
            revenue_fields=["carbon_tax_collected", "nonexistent_field"],
            cost_fields=["subsidy_paid"],
        )

        result = compute_fiscal_indicators(simple_panel, config)

        # Should compute successfully with available fields
        assert len(result.indicators) == 1
        # Only carbon_tax_collected should be included
        assert result.indicators[0].revenue == pytest.approx(450.0)

    def test_non_numeric_fiscal_field_raises(self, simple_panel):
        """Test configured fiscal fields must be numeric."""
        table_with_text = simple_panel.table.append_column(
            "policy_label",
            pa.array(["a", "b", "c"], type=pa.utf8()),
        )
        text_panel = PanelOutput(table=table_with_text, metadata=simple_panel.metadata)
        config = FiscalConfig(
            revenue_fields=["policy_label"],
            cost_fields=["subsidy_paid"],
        )

        with pytest.raises(ValueError, match="Fiscal fields must be numeric"):
            compute_fiscal_indicators(text_panel, config)


class TestResultTableConversion:
    """Test IndicatorResult.to_table() for fiscal indicators."""

    def test_to_table_schema(self, simple_panel):
        """Test that to_table() produces stable schema for fiscal indicators."""
        config = FiscalConfig(
            revenue_fields=["carbon_tax_collected"],
            cost_fields=["subsidy_paid"],
            by_year=True,
            cumulative=False,
        )

        result = compute_fiscal_indicators(simple_panel, config)
        table = result.to_table()

        # Check schema
        assert set(table.column_names) == {"field_name", "year", "metric", "value"}
        assert table.schema.field("field_name").type == pa.utf8()
        assert table.schema.field("year").type == pa.int64()
        assert table.schema.field("metric").type == pa.utf8()
        assert table.schema.field("value").type == pa.float64()

    def test_to_table_content(self, simple_panel):
        """Test that to_table() contains correct fiscal metrics."""
        config = FiscalConfig(
            revenue_fields=["carbon_tax_collected"],
            cost_fields=["subsidy_paid"],
            by_year=True,
            cumulative=False,
        )

        result = compute_fiscal_indicators(simple_panel, config)
        table = result.to_table()

        # Should have 3 rows per indicator (revenue, cost, balance)
        assert table.num_rows == 3

        # Extract metrics
        metrics = table.column("metric").to_pylist()
        assert set(metrics) == {"revenue", "cost", "balance"}

        # Check values
        values_dict = dict(
            zip(metrics, table.column("value").to_pylist(), strict=False)
        )
        assert values_dict["revenue"] == pytest.approx(450.0)
        assert values_dict["cost"] == pytest.approx(185.0)
        assert values_dict["balance"] == pytest.approx(265.0)

    def test_to_table_cumulative(self, multi_year_panel):
        """Test that to_table() includes cumulative metrics when present."""
        config = FiscalConfig(
            revenue_fields=["carbon_tax_collected"],
            cost_fields=["subsidy_paid"],
            by_year=True,
            cumulative=True,
        )

        result = compute_fiscal_indicators(multi_year_panel, config)
        table = result.to_table()

        # Should have 6 metrics per year: revenue, cost, balance,
        # cumulative_revenue, cumulative_cost, cumulative_balance
        # 2 years * 6 metrics = 12 rows
        assert table.num_rows == 12

        metrics = table.column("metric").to_pylist()
        assert "cumulative_revenue" in metrics
        assert "cumulative_cost" in metrics
        assert "cumulative_balance" in metrics

    def test_to_table_empty_result(self, empty_panel):
        """Test to_table() with empty fiscal indicators."""
        config = FiscalConfig(
            revenue_fields=["carbon_tax_collected"],
            cost_fields=["subsidy_paid"],
        )

        result = compute_fiscal_indicators(empty_panel, config)
        table = result.to_table()

        # Should return empty table with correct schema
        assert table.num_rows == 0
        assert set(table.column_names) == {"field_name", "year", "metric", "value"}


class TestMetadata:
    """Test metadata capture in IndicatorResult."""

    def test_metadata_content(self, simple_panel):
        """Test that metadata captures configuration and panel info."""
        config = FiscalConfig(
            revenue_fields=["carbon_tax_collected"],
            cost_fields=["subsidy_paid"],
            by_year=True,
            cumulative=True,
        )

        result = compute_fiscal_indicators(simple_panel, config)

        assert "revenue_fields" in result.metadata
        assert "cost_fields" in result.metadata
        assert "by_year" in result.metadata
        assert "cumulative" in result.metadata
        assert "panel_shape" in result.metadata

        assert result.metadata["revenue_fields"] == ["carbon_tax_collected"]
        assert result.metadata["cost_fields"] == ["subsidy_paid"]
        assert result.metadata["by_year"] is True
        assert result.metadata["cumulative"] is True


class TestDefaultConfig:
    """Test default configuration behavior."""

    def test_default_config(self, simple_panel):
        """Test that default config is applied when config=None."""
        # This should raise an error because default has empty revenue/cost fields
        with pytest.raises(
            ValueError,
            match="At least one revenue field or cost field must be configured",
        ):
            compute_fiscal_indicators(simple_panel, config=None)

    def test_minimal_valid_config(self, simple_panel):
        """Test minimal valid configuration."""
        config = FiscalConfig(revenue_fields=["carbon_tax_collected"])

        result = compute_fiscal_indicators(simple_panel, config)

        assert len(result.indicators) == 1
        assert result.indicators[0].revenue == pytest.approx(450.0)
        assert result.indicators[0].cost == pytest.approx(0.0)
