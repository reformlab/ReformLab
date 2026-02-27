"""Types and configuration models for indicator computation.

Story 4.1: Implement Distributional Indicators by Income Decile

This module provides:
- DecileIndicators: Dataclass for decile-level metric results
- IndicatorResult: Container for indicator results with metadata and warnings
- DistributionalConfig: Configuration for distributional indicator computation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

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
class IndicatorResult:
    """Container for computed indicator results with metadata and warnings.

    Holds the computed decile indicators along with run metadata,
    warning messages, and exclusion counts for transparency.

    Attributes:
        indicators: List of DecileIndicators, one per (field, decile, year) combination.
        metadata: Dictionary containing configuration and run information.
        warnings: List of warning messages emitted during computation.
        excluded_count: Number of households excluded due to missing income.
    """

    indicators: list[DecileIndicators]
    metadata: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    excluded_count: int = 0

    def to_table(self) -> pa.Table:
        """Convert indicator results to a stable PyArrow table.

        Returns a table with columns for field_name, decile, year, and
        all metric values (count, mean, median, sum, min, max).

        This table is suitable for downstream CSV/Parquet export workflows
        and scenario comparison operations.

        Returns:
            PyArrow Table with stable column schema.
        """
        if not self.indicators:
            # Return empty table with stable schema
            return pa.table(
                {
                    "field_name": pa.array([], type=pa.utf8()),
                    "decile": pa.array([], type=pa.int64()),
                    "year": pa.array([], type=pa.int64()),
                    "count": pa.array([], type=pa.int64()),
                    "mean": pa.array([], type=pa.float64()),
                    "median": pa.array([], type=pa.float64()),
                    "sum": pa.array([], type=pa.float64()),
                    "min": pa.array([], type=pa.float64()),
                    "max": pa.array([], type=pa.float64()),
                }
            )

        # Build arrays from indicators
        field_names: list[str] = []
        deciles: list[int | None] = []
        years: list[int | None] = []
        counts: list[int] = []
        means: list[float] = []
        medians: list[float] = []
        sums: list[float] = []
        mins: list[float] = []
        maxs: list[float] = []

        for ind in self.indicators:
            field_names.append(ind.field_name)
            deciles.append(ind.decile)
            years.append(ind.year)
            counts.append(ind.count)
            means.append(ind.mean)
            medians.append(ind.median)
            sums.append(ind.sum)
            mins.append(ind.min)
            maxs.append(ind.max)

        return pa.table(
            {
                "field_name": pa.array(field_names, type=pa.utf8()),
                "decile": pa.array(deciles, type=pa.int64()),
                "year": pa.array(years, type=pa.int64()),
                "count": pa.array(counts, type=pa.int64()),
                "mean": pa.array(means, type=pa.float64()),
                "median": pa.array(medians, type=pa.float64()),
                "sum": pa.array(sums, type=pa.float64()),
                "min": pa.array(mins, type=pa.float64()),
                "max": pa.array(maxs, type=pa.float64()),
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
