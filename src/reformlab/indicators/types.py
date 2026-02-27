"""Types and configuration models for indicator computation.

Story 4.1: Implement Distributional Indicators by Income Decile
Story 4.2: Implement Geographic Aggregation Indicators
Story 4.3: Implement Welfare Indicators
Story 4.4: Implement Fiscal Indicators

This module provides:
- DecileIndicators: Dataclass for decile-level metric results
- RegionIndicators: Dataclass for region-level metric results
- WelfareIndicators: Dataclass for welfare metric results (winner/loser analysis)
- FiscalIndicators: Dataclass for fiscal metric results (revenue, cost, balance)
- IndicatorResult: Container for indicator results with metadata and warnings
- DistributionalConfig: Configuration for distributional indicator computation
- GeographicConfig: Configuration for geographic indicator computation
- WelfareConfig: Configuration for welfare indicator computation
- FiscalConfig: Configuration for fiscal indicator computation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

import pyarrow as pa


@dataclass
class DecileIndicators:
    """Decile-level indicator metrics for a single numeric field.

    Contains aggregated statistics (count, mean, median, sum, min, max)
    computed for each income decile.

    Attributes:
        field_name: Name of the numeric field being aggregated.
        decile: Decile number (1-10) or None for cross-decile aggregations.
        year: Year of the data, or None for cross-year aggregations.
        count: Number of households in this decile.
        mean: Mean value across households in this decile.
        median: Median value across households in this decile.
        sum: Sum of values across households in this decile.
        min: Minimum value in this decile.
        max: Maximum value in this decile.
    """

    field_name: str
    decile: int | None
    year: int | None
    count: int
    mean: float
    median: float
    sum: float
    min: float
    max: float


@dataclass
class RegionIndicators:
    """Region-level indicator metrics for a single numeric field.

    Contains aggregated statistics (count, mean, median, sum, min, max)
    computed for each geographic region.

    Attributes:
        field_name: Name of the numeric field being aggregated.
        region: Region code (e.g., "11" for Île-de-France) or "_UNMATCHED" for
            unmatched region codes.
        year: Year of the data, or None for cross-year aggregations.
        count: Number of households in this region.
        mean: Mean value across households in this region.
        median: Median value across households in this region.
        sum: Sum of values across households in this region.
        min: Minimum value in this region.
        max: Maximum value in this region.
    """

    field_name: str
    region: str
    year: int | None
    count: int
    mean: float
    median: float
    sum: float
    min: float
    max: float


@dataclass
class WelfareIndicators:
    """Welfare indicator metrics for baseline vs reform comparison.

    Contains winner/loser counts and welfare metrics for a single field and group.

    Attributes:
        field_name: Name of the welfare field being analyzed (e.g., "disposable_income").
        group_type: Type of grouping ("decile" or "region").
        group_value: Value of the grouping dimension (decile number 1-10 or region code).
        year: Year of the data, or None for cross-year aggregations.
        winner_count: Number of households with positive net change (change > threshold).
        loser_count: Number of households with negative net change (change < -threshold).
        neutral_count: Number of households with negligible change (-threshold <= change <= threshold).
        mean_gain: Mean value of positive changes (winners only).
        mean_loss: Mean absolute value of negative changes (losers only).
        median_change: Median net change across all households in group.
        total_gain: Sum of all positive changes.
        total_loss: Absolute sum of all negative changes.
        net_change: Net welfare change (total_gain - total_loss).
    """

    field_name: str
    group_type: str  # "decile" or "region"
    group_value: int | str  # decile number or region code
    year: int | None
    winner_count: int
    loser_count: int
    neutral_count: int
    mean_gain: float
    mean_loss: float
    median_change: float
    total_gain: float
    total_loss: float
    net_change: float


@dataclass
class FiscalIndicators:
    """Fiscal indicator metrics for a single scenario panel.

    Contains revenue, cost, and balance metrics computed from fiscal fields
    in a PanelOutput, with optional cumulative totals.

    Attributes:
        field_name: Stable label for the fiscal summary (e.g., "fiscal_summary").
        year: Year of the data, or None for cross-year aggregations.
        revenue: Total revenue (sum of all revenue_fields).
        cost: Total cost (sum of all cost_fields).
        balance: Net fiscal balance (revenue - cost).
        cumulative_revenue: Running cumulative revenue from start_year
            through this year.
        cumulative_cost: Running cumulative cost from start_year
            through this year.
        cumulative_balance: Running cumulative balance from start_year
            through this year.
    """

    field_name: str
    year: int | None
    revenue: float
    cost: float
    balance: float
    cumulative_revenue: float | None = None
    cumulative_cost: float | None = None
    cumulative_balance: float | None = None


@dataclass
class IndicatorResult:
    """Container for computed indicator results with metadata and warnings.

    Holds computed indicators (decile-based or region-based) along with run metadata,
    warning messages, and exclusion counts for transparency.

    Attributes:
        indicators: Sequence of indicator objects (DecileIndicators or RegionIndicators),
            one per (field, group, year) combination.
        metadata: Dictionary containing configuration and run information.
        warnings: List of warning messages emitted during computation.
        excluded_count: Number of households excluded due to missing values.
        unmatched_count: Number of unmatched records between compared inputs
            (used by geographic and welfare indicators).
    """

    indicators: Sequence[
        DecileIndicators | RegionIndicators | WelfareIndicators | FiscalIndicators
    ]
    metadata: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    excluded_count: int = 0
    unmatched_count: int = 0

    def export_csv(self, path: str | Path) -> Path:
        """Export indicator results to CSV file.

        Args:
            path: Destination file path for CSV export.

        Returns:
            Path to the written CSV file.

        Example:
            >>> indicators = result.indicators("distributional")
            >>> output_path = indicators.export_csv("output/indicators.csv")
        """
        import pyarrow.csv as pa_csv

        path = Path(path)
        table = self.to_table()
        pa_csv.write_csv(table, path)
        return path

    def export_parquet(self, path: str | Path) -> Path:
        """Export indicator results to Parquet file.

        Args:
            path: Destination file path for Parquet export.

        Returns:
            Path to the written Parquet file.

        Example:
            >>> indicators = result.indicators("distributional")
            >>> output_path = indicators.export_parquet("output/indicators.parquet")
        """
        import pyarrow.parquet as pq

        path = Path(path)
        table = self.to_table()
        pq.write_table(table, path)
        return path

    def to_table(self) -> pa.Table:
        """Convert indicator results to a stable PyArrow table.

        Returns a long-form table with one row per metric.

        For DecileIndicators: field_name, decile, year, metric, value
        For RegionIndicators: field_name, region, year, metric, value
        For WelfareIndicators: field_name, decile|region, year, metric, value

        This table is suitable for downstream CSV/Parquet export workflows
        and scenario comparison operations.

        Returns:
            PyArrow Table with stable column schema.
        """
        if not self.indicators:
            # Detect indicator type from metadata to determine schema
            if "revenue_fields" in self.metadata or "cost_fields" in self.metadata:
                # Fiscal indicators
                return pa.table(
                    {
                        "field_name": pa.array([], type=pa.utf8()),
                        "year": pa.array([], type=pa.int64()),
                        "metric": pa.array([], type=pa.utf8()),
                        "value": pa.array([], type=pa.float64()),
                    }
                )
            elif "welfare_field" in self.metadata:
                # Welfare indicators
                group_type = str(self.metadata.get("group_type", "decile"))
                if group_type == "region":
                    return pa.table(
                        {
                            "field_name": pa.array([], type=pa.utf8()),
                            "region": pa.array([], type=pa.utf8()),
                            "year": pa.array([], type=pa.int64()),
                            "metric": pa.array([], type=pa.utf8()),
                            "value": pa.array([], type=pa.float64()),
                        }
                    )
                return pa.table(
                    {
                        "field_name": pa.array([], type=pa.utf8()),
                        "decile": pa.array([], type=pa.int64()),
                        "year": pa.array([], type=pa.int64()),
                        "metric": pa.array([], type=pa.utf8()),
                        "value": pa.array([], type=pa.float64()),
                    }
                )
            elif "region_field" in self.metadata:
                # Geographic indicators
                return pa.table(
                    {
                        "field_name": pa.array([], type=pa.utf8()),
                        "region": pa.array([], type=pa.utf8()),
                        "year": pa.array([], type=pa.int64()),
                        "metric": pa.array([], type=pa.utf8()),
                        "value": pa.array([], type=pa.float64()),
                    }
                )
            else:
                # Distributional indicators (default)
                return pa.table(
                    {
                        "field_name": pa.array([], type=pa.utf8()),
                        "decile": pa.array([], type=pa.int64()),
                        "year": pa.array([], type=pa.int64()),
                        "metric": pa.array([], type=pa.utf8()),
                        "value": pa.array([], type=pa.float64()),
                    }
                )

        # Detect indicator type from first indicator
        first_indicator = self.indicators[0]
        is_geographic = isinstance(first_indicator, RegionIndicators)
        is_welfare = isinstance(first_indicator, WelfareIndicators)
        is_fiscal = isinstance(first_indicator, FiscalIndicators)

        if is_fiscal:
            # Fiscal indicators have revenue, cost, balance, and optional
            # cumulative metrics
            field_names_fiscal: list[str] = []
            years_fiscal: list[int | None] = []
            metrics_fiscal: list[str] = []
            values_fiscal: list[float] = []

            for ind in self.indicators:
                assert isinstance(ind, FiscalIndicators)
                # Annual metrics
                fiscal_metric_names = ["revenue", "cost", "balance"]
                fiscal_metric_values = [ind.revenue, ind.cost, ind.balance]

                # Add cumulative metrics if present
                if ind.cumulative_revenue is not None:
                    fiscal_metric_names.extend(
                        [
                            "cumulative_revenue",
                            "cumulative_cost",
                            "cumulative_balance",
                        ]
                    )
                    fiscal_metric_values.extend(
                        [
                            ind.cumulative_revenue,
                            ind.cumulative_cost or 0.0,
                            ind.cumulative_balance or 0.0,
                        ]
                    )

                for metric_name, metric_value in zip(
                    fiscal_metric_names, fiscal_metric_values, strict=True
                ):
                    field_names_fiscal.append(ind.field_name)
                    years_fiscal.append(ind.year)
                    metrics_fiscal.append(metric_name)
                    values_fiscal.append(metric_value)

            return pa.table(
                {
                    "field_name": pa.array(field_names_fiscal, type=pa.utf8()),
                    "year": pa.array(years_fiscal, type=pa.int64()),
                    "metric": pa.array(metrics_fiscal, type=pa.utf8()),
                    "value": pa.array(values_fiscal, type=pa.float64()),
                }
            )

        if is_welfare:
            # Welfare indicators have different metrics
            assert isinstance(first_indicator, WelfareIndicators)
            welfare_group_type = first_indicator.group_type
            field_names_welfare: list[str] = []
            groups_welfare: list[int | str] = []
            years_welfare: list[int | None] = []
            metrics_welfare: list[str] = []
            values_welfare: list[float] = []

            for ind in self.indicators:
                assert isinstance(ind, WelfareIndicators)
                welfare_metric_names = [
                    "winner_count",
                    "loser_count",
                    "neutral_count",
                    "mean_gain",
                    "mean_loss",
                    "median_change",
                    "total_gain",
                    "total_loss",
                    "net_change",
                ]
                welfare_metric_values = [
                    float(ind.winner_count),
                    float(ind.loser_count),
                    float(ind.neutral_count),
                    ind.mean_gain,
                    ind.mean_loss,
                    ind.median_change,
                    ind.total_gain,
                    ind.total_loss,
                    ind.net_change,
                ]
                for metric_name, metric_value in zip(
                    welfare_metric_names, welfare_metric_values, strict=True
                ):
                    field_names_welfare.append(ind.field_name)
                    groups_welfare.append(ind.group_value)
                    years_welfare.append(ind.year)
                    metrics_welfare.append(metric_name)
                    values_welfare.append(metric_value)

            if welfare_group_type == "region":
                return pa.table(
                    {
                        "field_name": pa.array(field_names_welfare, type=pa.utf8()),
                        "region": pa.array(
                            [str(group) for group in groups_welfare],
                            type=pa.utf8(),
                        ),
                        "year": pa.array(years_welfare, type=pa.int64()),
                        "metric": pa.array(metrics_welfare, type=pa.utf8()),
                        "value": pa.array(values_welfare, type=pa.float64()),
                    }
                )
            return pa.table(
                {
                    "field_name": pa.array(field_names_welfare, type=pa.utf8()),
                    "decile": pa.array(
                        [int(group) for group in groups_welfare],
                        type=pa.int64(),
                    ),
                    "year": pa.array(years_welfare, type=pa.int64()),
                    "metric": pa.array(metrics_welfare, type=pa.utf8()),
                    "value": pa.array(values_welfare, type=pa.float64()),
                }
            )

        # Build arrays in long format: one row per metric.
        # This branch handles DecileIndicators and RegionIndicators only
        metric_names = ("count", "mean", "median", "sum", "min", "max")
        field_names_dist: list[str] = []
        groups: list[str | int | None] = []  # region or decile
        years_dist: list[int | None] = []
        metrics_dist: list[str] = []
        values_dist: list[float] = []

        for ind in self.indicators:
            if isinstance(ind, (WelfareIndicators, FiscalIndicators)):
                # This should not happen in this branch, but mypy needs the check
                continue

            metric_values = (
                float(ind.count),
                ind.mean,
                ind.median,
                ind.sum,
                ind.min,
                ind.max,
            )
            for metric_name, metric_value in zip(
                metric_names, metric_values, strict=True
            ):
                field_names_dist.append(ind.field_name)
                if is_geographic:
                    assert isinstance(ind, RegionIndicators)
                    groups.append(ind.region)
                else:
                    assert isinstance(ind, DecileIndicators)
                    groups.append(ind.decile)
                years_dist.append(ind.year)
                metrics_dist.append(metric_name)
                values_dist.append(metric_value)

        if is_geographic:
            return pa.table(
                {
                    "field_name": pa.array(field_names_dist, type=pa.utf8()),
                    "region": pa.array(groups, type=pa.utf8()),
                    "year": pa.array(years_dist, type=pa.int64()),
                    "metric": pa.array(metrics_dist, type=pa.utf8()),
                    "value": pa.array(values_dist, type=pa.float64()),
                }
            )
        else:
            return pa.table(
                {
                    "field_name": pa.array(field_names_dist, type=pa.utf8()),
                    "decile": pa.array(groups, type=pa.int64()),
                    "year": pa.array(years_dist, type=pa.int64()),
                    "metric": pa.array(metrics_dist, type=pa.utf8()),
                    "value": pa.array(values_dist, type=pa.float64()),
                }
            )


@dataclass
class DistributionalConfig:
    """Configuration for distributional indicator computation.

    Specifies which field to use for income decile assignment and
    how to handle multi-year panels.

    Attributes:
        income_field: Name of the income column in the panel for decile assignment.
            Defaults to "income".
        by_year: If True, compute indicators separately for each year.
            Defaults to False (aggregate across all years).
        aggregate_years: If True, aggregate indicators across all years
            (group by decile only). Only used when by_year=False.
            Defaults to True.
        weight_field: Optional name of weight column for weighted aggregations.
            Not implemented in MVP. Defaults to None.
    """

    income_field: str = "income"
    by_year: bool = False
    aggregate_years: bool = True
    weight_field: str | None = None


@dataclass
class GeographicConfig:
    """Configuration for geographic indicator computation.

    Specifies which field to use for region grouping and how to handle
    multi-year panels and unmatched regions.

    Attributes:
        region_field: Name of the region code column in the panel.
            Defaults to "region_code".
        by_year: If True, compute indicators separately for each year.
            Defaults to False (aggregate across all years).
        aggregate_years: If True, aggregate indicators across all years
            (group by region only). Only used when by_year=False.
            Defaults to True.
        reference_table: Optional PyArrow table with valid region codes.
            If provided, unmatched region codes are grouped into "_UNMATCHED" category.
            Table must have a column matching region_field name.
            Defaults to None (no validation).
    """

    region_field: str = "region_code"
    by_year: bool = False
    aggregate_years: bool = True
    reference_table: pa.Table | None = None


@dataclass
class WelfareConfig:
    """Configuration for welfare indicator computation.

    Specifies which field to use for welfare comparison, classification threshold,
    grouping dimension, and multi-year handling.

    Attributes:
        welfare_field: Name of the welfare field for net change computation.
            Defaults to "disposable_income".
        threshold: Classification threshold for winner/loser determination.
            Households with change > threshold are winners, change < -threshold are losers.
            Defaults to 0.0 (any positive change is a winner).
        by_year: If True, compute indicators separately for each year.
            Defaults to False (aggregate across all years).
        aggregate_years: If True, aggregate indicators across all years
            (group by dimension only). Only used when by_year=False.
            Defaults to True.
        group_by_decile: If True, group welfare indicators by income decile.
            Defaults to True.
        group_by_region: If True, group welfare indicators by region.
            Mutually exclusive with group_by_decile. If both are True, decile takes precedence.
            Defaults to False.
        income_field: Name of income column for decile assignment (when group_by_decile=True).
            Defaults to "income".
        region_field: Name of region column for region grouping (when group_by_region=True).
            Defaults to "region_code".
    """

    welfare_field: str = "disposable_income"
    threshold: float = 0.0
    by_year: bool = False
    aggregate_years: bool = True
    group_by_decile: bool = True
    group_by_region: bool = False
    income_field: str = "income"
    region_field: str = "region_code"


@dataclass
class FiscalConfig:
    """Configuration for fiscal indicator computation.

    Specifies which fields to aggregate as revenue and cost,
    and how to handle multi-year panels and cumulative totals.

    Attributes:
        revenue_fields: List of field names to sum into total revenue.
            Defaults to empty list.
        cost_fields: List of field names to sum into total cost.
            Defaults to empty list.
        by_year: If True, compute indicators separately for each year.
            Defaults to True.
        aggregate_years: If True, aggregate indicators across all years
            (single total). Only used when by_year=False.
            Defaults to False.
        cumulative: If True, compute cumulative totals from start year
            through each year. Only applies when year detail is present.
            Defaults to True.
    """

    revenue_fields: list[str] = field(default_factory=list)
    cost_fields: list[str] = field(default_factory=list)
    by_year: bool = True
    aggregate_years: bool = False
    cumulative: bool = True
