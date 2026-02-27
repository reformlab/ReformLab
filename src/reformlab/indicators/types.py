"""Types and configuration models for indicator computation.

Story 4.1: Implement Distributional Indicators by Income Decile
Story 4.2: Implement Geographic Aggregation Indicators

This module provides:
- DecileIndicators: Dataclass for decile-level metric results
- RegionIndicators: Dataclass for region-level metric results
- IndicatorResult: Container for indicator results with metadata and warnings
- DistributionalConfig: Configuration for distributional indicator computation
- GeographicConfig: Configuration for geographic indicator computation
"""

from __future__ import annotations

from dataclasses import dataclass, field
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
        unmatched_count: Number of households with unmatched region codes
            (only for geographic indicators).
    """

    indicators: Sequence[DecileIndicators | RegionIndicators]
    metadata: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    excluded_count: int = 0
    unmatched_count: int = 0

    def to_table(self) -> pa.Table:
        """Convert indicator results to a stable PyArrow table.

        Returns a long-form table with one row per metric.

        For DecileIndicators: field_name, decile, year, metric, value
        For RegionIndicators: field_name, region, year, metric, value

        This table is suitable for downstream CSV/Parquet export workflows
        and scenario comparison operations.

        Returns:
            PyArrow Table with stable column schema.
        """
        if not self.indicators:
            # Detect indicator type from metadata to determine schema
            if "region_field" in self.metadata:
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

        # Build arrays in long format: one row per metric.
        metric_names = ("count", "mean", "median", "sum", "min", "max")
        field_names: list[str] = []
        groups: list[str | int | None] = []  # region or decile
        years: list[int | None] = []
        metrics: list[str] = []
        values: list[float] = []

        for ind in self.indicators:
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
                field_names.append(ind.field_name)
                if is_geographic:
                    assert isinstance(ind, RegionIndicators)
                    groups.append(ind.region)
                else:
                    assert isinstance(ind, DecileIndicators)
                    groups.append(ind.decile)
                years.append(ind.year)
                metrics.append(metric_name)
                values.append(metric_value)

        if is_geographic:
            return pa.table(
                {
                    "field_name": pa.array(field_names, type=pa.utf8()),
                    "region": pa.array(groups, type=pa.utf8()),
                    "year": pa.array(years, type=pa.int64()),
                    "metric": pa.array(metrics, type=pa.utf8()),
                    "value": pa.array(values, type=pa.float64()),
                }
            )
        else:
            return pa.table(
                {
                    "field_name": pa.array(field_names, type=pa.utf8()),
                    "decile": pa.array(groups, type=pa.int64()),
                    "year": pa.array(years, type=pa.int64()),
                    "metric": pa.array(metrics, type=pa.utf8()),
                    "value": pa.array(values, type=pa.float64()),
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
