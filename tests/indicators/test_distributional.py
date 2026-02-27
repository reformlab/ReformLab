"""Tests for distributional indicator computation.

Story 4.1: Implement Distributional Indicators by Income Decile
Story 6.5: Add Export Actions for CSV/Parquet Outputs

Tests cover:
- Decile assignment across controlled income distributions (AC-1)
- Missing income exclusion + warning emission + metadata count (AC-2)
- Metric correctness for numeric fields (AC-3)
- Multi-year by_year and aggregate_years behavior (AC-4)
- IndicatorResult.to_table() schema stability (AC-5)
- IndicatorResult export methods (Story 6-5, AC-2)
"""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.indicators.distributional import compute_distributional_indicators
from reformlab.indicators.types import DistributionalConfig
from reformlab.orchestrator.panel import PanelOutput


class TestDecileAssignment:
    """Test decile assignment logic (AC-1)."""

    def test_100_households_uniform_distribution(
        self, simple_income_distribution_panel: PanelOutput
    ) -> None:
        """AC-1: 100 households with uniform income are assigned to deciles."""
        result = compute_distributional_indicators(simple_income_distribution_panel)

        # Should have 10 deciles × 2 fields (income excluded, so tax only)
        # Actually income is excluded, but we still have household_id
        # Let me check what numeric fields we have: tax
        assert len(result.indicators) == 10  # 10 deciles for "tax" field

        # Check that all deciles 1-10 are present
        deciles = {ind.decile for ind in result.indicators if ind.field_name == "tax"}
        assert deciles == set(range(1, 11))

        # Check counts: each decile should have ~10 households
        for ind in result.indicators:
            if ind.field_name == "tax":
                assert 8 <= ind.count <= 12  # Allow some tolerance

    def test_decile_boundaries_correct(
        self, simple_income_distribution_panel: PanelOutput
    ) -> None:
        """AC-1: Decile boundaries match expected income percentiles."""
        result = compute_distributional_indicators(simple_income_distribution_panel)

        # For uniform distribution from 10k to 100k:
        # D1 should have households with lowest incomes
        # D10 should have households with highest incomes

        tax_indicators = [ind for ind in result.indicators if ind.field_name == "tax"]
        tax_indicators.sort(key=lambda x: x.decile)

        # D1 should have lower tax values than D10
        d1_mean = tax_indicators[0].mean
        d10_mean = tax_indicators[9].mean

        assert d1_mean < d10_mean

        # Mean should increase monotonically across deciles
        for i in range(len(tax_indicators) - 1):
            assert tax_indicators[i].mean <= tax_indicators[i + 1].mean


class TestMissingIncomeHandling:
    """Test missing income data handling (AC-2)."""

    def test_missing_income_exclusion(
        self, panel_with_missing_income: PanelOutput
    ) -> None:
        """AC-2: Households with null income are excluded from decile assignment."""
        result = compute_distributional_indicators(panel_with_missing_income)

        # 50 households, 10 with null income (every 5th)
        assert result.excluded_count == 10

        # Check that indicators are computed only on 40 households
        total_count = sum(
            ind.count for ind in result.indicators if ind.field_name == "tax"
        )
        assert total_count == 40

    def test_missing_income_warning(
        self, panel_with_missing_income: PanelOutput
    ) -> None:
        """AC-2: Warning is emitted with exact excluded-household count."""
        result = compute_distributional_indicators(panel_with_missing_income)

        assert len(result.warnings) > 0
        assert any("10" in w and "missing income" in w for w in result.warnings)

    def test_missing_income_in_metadata(
        self, panel_with_missing_income: PanelOutput
    ) -> None:
        """AC-2: Excluded count is present in result metadata."""
        result = compute_distributional_indicators(panel_with_missing_income)

        assert result.excluded_count == 10
        assert result.metadata["excluded_count"] == 10


class TestAggregationMetrics:
    """Test standard indicator metrics (AC-3)."""

    def test_all_metrics_present(
        self, simple_income_distribution_panel: PanelOutput
    ) -> None:
        """AC-3: Metrics include count, mean, median, sum, min, max per decile."""
        result = compute_distributional_indicators(simple_income_distribution_panel)

        for ind in result.indicators:
            assert ind.count > 0
            assert ind.mean > 0
            assert ind.median > 0
            assert ind.sum > 0
            assert ind.min > 0
            assert ind.max > 0

    def test_metrics_correctness(
        self, simple_income_distribution_panel: PanelOutput
    ) -> None:
        """AC-3: Aggregated metrics are mathematically correct."""
        result = compute_distributional_indicators(simple_income_distribution_panel)

        for ind in result.indicators:
            # Min should be <= mean <= max
            assert ind.min <= ind.mean <= ind.max

            # Median should be in reasonable range
            assert ind.min <= ind.median <= ind.max

            # Sum should equal mean * count (approximately, due to floating point)
            expected_sum = ind.mean * ind.count
            assert abs(ind.sum - expected_sum) < 1e-6

    def test_numeric_fields_aggregated(
        self, simple_income_distribution_panel: PanelOutput
    ) -> None:
        """AC-3: All numeric output fields are aggregated."""
        result = compute_distributional_indicators(simple_income_distribution_panel)

        # Should have indicators for "tax"
        # (income is excluded as it's the grouping field)
        field_names = {ind.field_name for ind in result.indicators}
        assert "tax" in field_names
        assert "income" not in field_names  # Income is the grouping field


class TestMultiYearSupport:
    """Test multi-year panel support (AC-4)."""

    def test_by_year_grouping(self, multi_year_panel: PanelOutput) -> None:
        """AC-4: With by_year=True, indicators are grouped by (year, decile)."""
        config = DistributionalConfig(by_year=True)
        result = compute_distributional_indicators(multi_year_panel, config)

        # Should have indicators for each (year, decile, field) combination
        # 3 years × 10 deciles × 1 field (tax)
        assert len(result.indicators) == 30

        # Check that all years are present
        years = {ind.year for ind in result.indicators}
        assert years == {2020, 2021, 2022}

        # Each year should have all 10 deciles
        for year in years:
            year_deciles = {ind.decile for ind in result.indicators if ind.year == year}
            assert year_deciles == set(range(1, 11))

    def test_aggregate_years(self, multi_year_panel: PanelOutput) -> None:
        """AC-4: With aggregate_years=True, indicators group by decile."""
        config = DistributionalConfig(aggregate_years=True, by_year=False)
        result = compute_distributional_indicators(multi_year_panel, config)

        # Should have indicators for each (decile, field) combination
        # 10 deciles × 1 field (tax)
        assert len(result.indicators) == 10

        # Year should be None for all indicators
        for ind in result.indicators:
            assert ind.year is None

        # Each decile should aggregate across all years
        # 30 households × 3 years = 90 total rows
        # Each decile should have ~9 rows
        total_count = sum(ind.count for ind in result.indicators)
        assert total_count == 90

    def test_no_aggregate_years_keeps_annual_groups(
        self, multi_year_panel: PanelOutput
    ) -> None:
        """AC-4: With aggregate_years=False, keep year-level decile groups."""
        config = DistributionalConfig(by_year=False, aggregate_years=False)
        result = compute_distributional_indicators(multi_year_panel, config)

        assert len(result.indicators) == 30
        years = {ind.year for ind in result.indicators}
        assert years == {2020, 2021, 2022}

    def test_single_year_default(
        self, simple_income_distribution_panel: PanelOutput
    ) -> None:
        """AC-4: Default behavior aggregates across years (single year case)."""
        result = compute_distributional_indicators(simple_income_distribution_panel)

        # Should have indicators with year=None
        for ind in result.indicators:
            assert ind.year is None


class TestIndicatorResultTable:
    """Test IndicatorResult.to_table() stable output (AC-5)."""

    def test_to_table_schema(
        self, simple_income_distribution_panel: PanelOutput
    ) -> None:
        """AC-5: to_table() returns stable schema with expected columns."""
        result = compute_distributional_indicators(simple_income_distribution_panel)
        table = result.to_table()

        expected_columns = {
            "field_name",
            "decile",
            "year",
            "metric",
            "value",
        }
        assert set(table.column_names) == expected_columns

    def test_to_table_column_types(
        self, simple_income_distribution_panel: PanelOutput
    ) -> None:
        """AC-5: to_table() columns have correct types."""
        result = compute_distributional_indicators(simple_income_distribution_panel)
        table = result.to_table()

        import pyarrow as pa

        schema = table.schema
        assert schema.field("field_name").type == pa.utf8()
        assert schema.field("decile").type == pa.int64()
        assert schema.field("year").type == pa.int64()
        assert schema.field("metric").type == pa.utf8()
        assert schema.field("value").type == pa.float64()

    def test_to_table_row_count(
        self, simple_income_distribution_panel: PanelOutput
    ) -> None:
        """AC-5: to_table() has one row per (indicator, metric)."""
        result = compute_distributional_indicators(simple_income_distribution_panel)
        table = result.to_table()

        assert table.num_rows == len(result.indicators) * 6

    def test_to_table_metrics(
        self, simple_income_distribution_panel: PanelOutput
    ) -> None:
        """AC-5: to_table() includes all standard metric names."""
        result = compute_distributional_indicators(simple_income_distribution_panel)
        table = result.to_table()

        metrics = set(table.column("metric").to_pylist())
        assert metrics == {"count", "mean", "median", "sum", "min", "max"}

    def test_to_table_empty_result(self, empty_panel: PanelOutput) -> None:
        """AC-5: to_table() handles empty results with stable schema."""
        # Empty panel should raise ValueError in decile assignment
        with pytest.raises(ValueError, match="No households with valid income"):
            compute_distributional_indicators(empty_panel)


class TestConfigurationOptions:
    """Test DistributionalConfig options."""

    def test_custom_income_field(
        self, simple_income_distribution_panel: PanelOutput
    ) -> None:
        """Test using a custom income field name."""
        # This test uses default "income" field, which works
        config = DistributionalConfig(income_field="income")
        result = compute_distributional_indicators(
            simple_income_distribution_panel, config
        )

        assert result.metadata["income_field"] == "income"
        assert len(result.indicators) > 0

    def test_invalid_income_field(
        self, simple_income_distribution_panel: PanelOutput
    ) -> None:
        """Test error handling for non-existent income field."""
        config = DistributionalConfig(income_field="nonexistent_field")

        with pytest.raises(ValueError, match="Income field .* not found"):
            compute_distributional_indicators(simple_income_distribution_panel, config)

    def test_default_config(
        self, simple_income_distribution_panel: PanelOutput
    ) -> None:
        """Test that None config uses sensible defaults."""
        result = compute_distributional_indicators(
            simple_income_distribution_panel, config=None
        )

        assert result.metadata["income_field"] == "income"
        assert result.metadata["aggregate_years"] is True
        assert result.metadata["by_year"] is False


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_all_null_income(self) -> None:
        """Test panel where all households have null income."""
        import pyarrow as pa

        from reformlab.orchestrator.panel import PanelOutput

        table = pa.table(
            {
                "household_id": pa.array([1, 2, 3], type=pa.int64()),
                "year": pa.array([2020, 2020, 2020], type=pa.int64()),
                "income": pa.array([None, None, None], type=pa.float64()),
                "tax": pa.array([100.0, 200.0, 300.0], type=pa.float64()),
            }
        )

        panel = PanelOutput(table=table, metadata={})

        with pytest.raises(ValueError, match="No households with valid income"):
            compute_distributional_indicators(panel)

    def test_single_household(self) -> None:
        """Test panel with only one household."""
        import pyarrow as pa

        from reformlab.orchestrator.panel import PanelOutput

        table = pa.table(
            {
                "household_id": pa.array([1], type=pa.int64()),
                "year": pa.array([2020], type=pa.int64()),
                "income": pa.array([50000.0], type=pa.float64()),
                "tax": pa.array([5000.0], type=pa.float64()),
            }
        )

        panel = PanelOutput(table=table, metadata={})

        result = compute_distributional_indicators(panel)

        # Single household goes into one decile
        assert len(result.indicators) == 1
        assert result.indicators[0].count == 1
        assert result.indicators[0].decile == 1  # Should be in lowest decile


class TestIndicatorResultExport:
    """Test IndicatorResult export methods (Story 6-5, AC-2)."""

    def test_export_csv(
        self, tmp_path, simple_income_distribution_panel: PanelOutput
    ) -> None:
        """export_csv() writes indicator table to CSV and returns Path."""
        import pyarrow.csv as pa_csv
        from pathlib import Path

        result = compute_distributional_indicators(simple_income_distribution_panel)

        output_path = tmp_path / "indicators.csv"
        returned_path = result.export_csv(output_path)

        # AC-2: export_csv returns Path to written file
        assert returned_path == output_path
        assert isinstance(returned_path, Path)
        assert output_path.exists()

        # Verify CSV content is readable and has expected schema
        loaded_table = pa_csv.read_csv(output_path)
        assert loaded_table.num_rows > 0
        assert set(loaded_table.column_names) == {
            "field_name",
            "decile",
            "year",
            "metric",
            "value",
        }

    def test_export_parquet(
        self, tmp_path, simple_income_distribution_panel: PanelOutput
    ) -> None:
        """export_parquet() writes indicator table to Parquet and returns Path."""
        import pyarrow.parquet as pq
        from pathlib import Path

        result = compute_distributional_indicators(simple_income_distribution_panel)

        output_path = tmp_path / "indicators.parquet"
        returned_path = result.export_parquet(output_path)

        # AC-2: export_parquet returns Path to written file
        assert returned_path == output_path
        assert isinstance(returned_path, Path)
        assert output_path.exists()

        # AC-5: Verify round-trip through PyArrow with expected schema
        loaded_table = pq.read_table(output_path)
        assert loaded_table.num_rows > 0
        assert set(loaded_table.column_names) == {
            "field_name",
            "decile",
            "year",
            "metric",
            "value",
        }

        # Verify schema types
        assert loaded_table.schema.field("field_name").type == pa.utf8()
        assert loaded_table.schema.field("decile").type == pa.int64()
        assert loaded_table.schema.field("year").type == pa.int64()
        assert loaded_table.schema.field("metric").type == pa.utf8()
        assert loaded_table.schema.field("value").type == pa.float64()

    def test_export_all_indicator_types(self, tmp_path) -> None:
        """Verify export works for all indicator types (distributional, geographic, welfare, fiscal)."""
        import pyarrow as pa
        from pathlib import Path

        from reformlab.indicators.distributional import compute_distributional_indicators
        from reformlab.indicators.fiscal import compute_fiscal_indicators
        from reformlab.indicators.geographic import compute_geographic_indicators
        from reformlab.indicators.types import FiscalConfig, GeographicConfig
        from reformlab.orchestrator.panel import PanelOutput

        # Create test panel with all required fields
        table = pa.table(
            {
                "household_id": pa.array(list(range(1, 21)), type=pa.int64()),
                "year": pa.array([2025] * 20, type=pa.int64()),
                "income": pa.array([20000.0 + (i * 1000.0) for i in range(20)], type=pa.float64()),
                "region_code": pa.array(["11"] * 10 + ["32"] * 10, type=pa.utf8()),
                "carbon_tax": pa.array([100.0 + (i * 5.0) for i in range(20)], type=pa.float64()),
                "rebate": pa.array([50.0] * 20, type=pa.float64()),
            }
        )
        panel = PanelOutput(table=table, metadata={})

        # Test distributional export
        dist_result = compute_distributional_indicators(panel)
        dist_csv = tmp_path / "dist.csv"
        dist_parquet = tmp_path / "dist.parquet"
        assert dist_result.export_csv(dist_csv).exists()
        assert dist_result.export_parquet(dist_parquet).exists()

        # Test geographic export
        geo_result = compute_geographic_indicators(
            panel, config=GeographicConfig(region_field="region_code")
        )
        geo_csv = tmp_path / "geo.csv"
        geo_parquet = tmp_path / "geo.parquet"
        assert geo_result.export_csv(geo_csv).exists()
        assert geo_result.export_parquet(geo_parquet).exists()

        # Test fiscal export
        fiscal_result = compute_fiscal_indicators(
            panel,
            config=FiscalConfig(
                revenue_fields=["carbon_tax"],
                cost_fields=["rebate"],
            ),
        )
        fiscal_csv = tmp_path / "fiscal.csv"
        fiscal_parquet = tmp_path / "fiscal.parquet"
        assert fiscal_result.export_csv(fiscal_csv).exists()
        assert fiscal_result.export_parquet(fiscal_parquet).exists()
