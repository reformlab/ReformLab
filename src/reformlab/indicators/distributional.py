"""Distributional indicator computation over panel outputs.

Story 4.1: Implement Distributional Indicators by Income Decile

This module provides:
- compute_distributional_indicators: Main API for computing decile-based
    distributional indicators from PanelOutput.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import pyarrow as pa

from reformlab.indicators.deciles import aggregate_by_decile, assign_deciles
from reformlab.indicators.types import (
    DecileIndicators,
    DistributionalConfig,
    IndicatorResult,
)

if TYPE_CHECKING:
    from reformlab.orchestrator.panel import PanelOutput


def compute_distributional_indicators(
    panel: PanelOutput,
    config: DistributionalConfig | None = None,
) -> IndicatorResult:
    """Compute distributional indicators by income decile from panel output.

    Assigns households to income deciles based on the configured income field,
    then computes aggregation metrics (count, mean, median, sum, min, max) for
    each numeric field in the panel.

    Supports three modes:
    1. Single-year or aggregate across years (default): Groups by decile only
    2. by_year=True: Groups by (decile, year) for year-by-year analysis
    3. aggregate_years=True: Explicitly aggregates across all years by decile

    Args:
        panel: PanelOutput from orchestrator run containing household-year data.
        config: Configuration for distributional computation. If None, uses
            default config (income field="income", aggregate_years=True).

    Returns:
        IndicatorResult containing:
        - List of DecileIndicators for each (field, decile, year) combination
        - Metadata with configuration and panel info
        - Warnings list (e.g., for excluded households)
        - Excluded count (households with null income)

    Raises:
        ValueError: If income field is not in panel table.
        ValueError: If no households have valid income.
    """
    if config is None:
        config = DistributionalConfig()

    # Capture warnings
    captured_warnings: list[str] = []

    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")

        # Assign deciles
        table_with_deciles, excluded_count = assign_deciles(
            panel.table,
            config.income_field,
        )

        # Capture warning messages
        for w in warning_list:
            captured_warnings.append(str(w.message))

    # Identify numeric fields (exclude household_id, year, decile, and income_field)
    numeric_fields = []
    exclude_fields = {"household_id", "year", "decile", config.income_field}

    for field_name in table_with_deciles.column_names:
        if field_name in exclude_fields:
            continue

        field_type = table_with_deciles.schema.field(field_name).type
        if pa.types.is_floating(field_type) or pa.types.is_integer(field_type):
            numeric_fields.append(field_name)

    # Compute aggregations
    group_by_year = config.by_year
    agg_table = aggregate_by_decile(
        table_with_deciles,
        numeric_fields,
        group_by_year=group_by_year,
    )

    # Convert aggregation table to DecileIndicators list
    indicators: list[DecileIndicators] = []

    for i in range(agg_table.num_rows):
        field_name = agg_table.column("field_name")[i].as_py()
        decile = agg_table.column("decile")[i].as_py()
        count = agg_table.column("count")[i].as_py()
        mean = agg_table.column("mean")[i].as_py()
        median = agg_table.column("median")[i].as_py()
        sum_val = agg_table.column("sum")[i].as_py()
        min_val = agg_table.column("min")[i].as_py()
        max_val = agg_table.column("max")[i].as_py()

        year = None
        if group_by_year:
            year = agg_table.column("year")[i].as_py()

        indicator = DecileIndicators(
            field_name=field_name,
            decile=decile,
            year=year,
            count=count,
            mean=mean,
            median=median,
            sum=sum_val,
            min=min_val,
            max=max_val,
        )
        indicators.append(indicator)

    # Build metadata
    metadata = {
        "income_field": config.income_field,
        "by_year": config.by_year,
        "aggregate_years": config.aggregate_years,
        "panel_shape": panel.shape,
        "panel_metadata": panel.metadata,
        "numeric_fields": numeric_fields,
    }

    return IndicatorResult(
        indicators=indicators,
        metadata=metadata,
        warnings=captured_warnings,
        excluded_count=excluded_count,
    )
