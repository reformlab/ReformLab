"""Fiscal indicator computation for single-scenario budgetary analysis.

Story 4.4: Implement Fiscal Indicators

This module provides:
- _compute_annual_totals: Compute annual revenue, cost, and balance from panel
- _compute_cumulative_totals: Compute running cumulative totals across years
- compute_fiscal_indicators: Main API for computing fiscal indicators
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import pyarrow as pa
import pyarrow.compute as pc

from reformlab.indicators.types import FiscalConfig, FiscalIndicators, IndicatorResult

if TYPE_CHECKING:
    from reformlab.orchestrator.panel import PanelOutput


def _compute_annual_totals(
    panel: pa.Table,
    revenue_fields: list[str],
    cost_fields: list[str],
    by_year: bool,
) -> tuple[pa.Table, list[str]]:
    """Compute annual fiscal totals (revenue, cost, balance) from panel.

    Args:
        panel: PyArrow table with fiscal fields.
        revenue_fields: List of column names to sum into revenue.
        cost_fields: List of column names to sum into cost.
        by_year: If True, group by year. If False, aggregate all years.

    Returns:
        Tuple of (result_table, warnings):
        - result_table: Table with columns [field_name, year (optional),
          revenue, cost, balance]
        - warnings: List of warning messages for null values.

    Raises:
        ValueError: If no fiscal fields are found in the panel.
    """
    captured_warnings: list[str] = []

    # Validate that at least one fiscal field exists
    revenue_fields_present = [f for f in revenue_fields if f in panel.column_names]
    cost_fields_present = [f for f in cost_fields if f in panel.column_names]

    if not revenue_fields_present and not cost_fields_present:
        raise ValueError(
            "No fiscal fields found in panel. "
            f"Requested revenue fields: {revenue_fields}, cost fields: {cost_fields}. "
            f"Available columns: {panel.column_names}"
        )

    # Handle null values: fill with 0.0 and emit warnings
    for field in revenue_fields_present + cost_fields_present:
        col = panel.column(field)
        null_count = pc.sum(pc.is_null(col)).as_py()
        if null_count > 0:
            captured_warnings.append(
                f"Field '{field}' has {null_count} null value(s). "
                "Treating as zero for fiscal aggregation."
            )

    # Group by year if requested, otherwise aggregate all
    if by_year:
        if "year" not in panel.column_names:
            raise ValueError("Cannot group by year: 'year' column not found in panel.")
        group_keys = ["year"]
    else:
        group_keys = []

    # Compute revenue total
    revenue_total = pa.array([0.0] * panel.num_rows, type=pa.float64())
    for field in revenue_fields_present:
        col = panel.column(field)
        # Fill nulls with 0.0
        col_filled = pc.fill_null(col, pa.scalar(0.0))
        # Cast to float64 if needed
        if not pa.types.is_floating(col_filled.type):
            col_filled = pc.cast(col_filled, pa.float64())
        revenue_total = pc.add(revenue_total, col_filled)

    # Compute cost total
    cost_total = pa.array([0.0] * panel.num_rows, type=pa.float64())
    for field in cost_fields_present:
        col = panel.column(field)
        # Fill nulls with 0.0
        col_filled = pc.fill_null(col, pa.scalar(0.0))
        # Cast to float64 if needed
        if not pa.types.is_floating(col_filled.type):
            col_filled = pc.cast(col_filled, pa.float64())
        cost_total = pc.add(cost_total, col_filled)

    # Add totals to panel
    panel_with_totals = panel.append_column("_revenue", revenue_total)
    panel_with_totals = panel_with_totals.append_column("_cost", cost_total)

    # Group and aggregate
    if group_keys:
        grouped = panel_with_totals.group_by(group_keys)
        agg_result = grouped.aggregate([
            ("_revenue", "sum"),
            ("_cost", "sum"),
        ])
        # Extract results
        years = agg_result.column("year").to_pylist()
        revenues = agg_result.column("_revenue_sum").to_pylist()
        costs = agg_result.column("_cost_sum").to_pylist()
    else:
        # Aggregate all years into single total
        total_revenue = pc.sum(panel_with_totals.column("_revenue")).as_py()
        total_cost = pc.sum(panel_with_totals.column("_cost")).as_py()
        years = [None]
        revenues = [total_revenue]
        costs = [total_cost]

    # Compute balance
    balances = [r - c for r, c in zip(revenues, costs, strict=True)]

    # Build result table
    result_data = {
        "field_name": pa.array(["fiscal_summary"] * len(years), type=pa.utf8()),
        "revenue": pa.array(revenues, type=pa.float64()),
        "cost": pa.array(costs, type=pa.float64()),
        "balance": pa.array(balances, type=pa.float64()),
    }

    if group_keys:
        result_data["year"] = pa.array(years, type=pa.int64())

    result_table = pa.table(result_data)

    # Sort by year if present
    if "year" in result_table.column_names:
        result_table = result_table.sort_by([("year", "ascending")])

    return result_table, captured_warnings


def _compute_cumulative_totals(annual_table: pa.Table) -> pa.Table:
    """Compute cumulative totals from annual fiscal data.

    Args:
        annual_table: Table with annual fiscal metrics (must have year,
            revenue, cost, balance).

    Returns:
        Table with added cumulative_revenue, cumulative_cost,
        cumulative_balance columns.

    Raises:
        ValueError: If required columns are missing.
    """
    required_cols = ["year", "revenue", "cost", "balance"]
    for col in required_cols:
        if col not in annual_table.column_names:
            raise ValueError(
                f"Cannot compute cumulative totals: '{col}' column not found in table."
            )

    # Sort by year to ensure correct cumulative order
    sorted_table = annual_table.sort_by([("year", "ascending")])

    revenues = sorted_table.column("revenue").to_pylist()
    costs = sorted_table.column("cost").to_pylist()
    balances = sorted_table.column("balance").to_pylist()

    # Compute running cumulative sums
    cumulative_revenues: list[float] = []
    cumulative_costs: list[float] = []
    cumulative_balances: list[float] = []

    running_revenue = 0.0
    running_cost = 0.0
    running_balance = 0.0

    for revenue, cost, balance in zip(revenues, costs, balances, strict=True):
        running_revenue += revenue
        running_cost += cost
        running_balance += balance
        cumulative_revenues.append(running_revenue)
        cumulative_costs.append(running_cost)
        cumulative_balances.append(running_balance)

    # Add cumulative columns
    result = sorted_table.append_column(
        "cumulative_revenue",
        pa.array(cumulative_revenues, type=pa.float64()),
    )
    result = result.append_column(
        "cumulative_cost",
        pa.array(cumulative_costs, type=pa.float64()),
    )
    result = result.append_column(
        "cumulative_balance",
        pa.array(cumulative_balances, type=pa.float64()),
    )

    return result


def compute_fiscal_indicators(
    panel: PanelOutput,
    config: FiscalConfig | None = None,
) -> IndicatorResult:
    """Compute fiscal indicators from a single scenario panel.

    Aggregates revenue and cost fields from the panel, computes fiscal balance,
    and optionally calculates cumulative totals across years.

    Args:
        panel: Panel output from orchestrator run.
        config: Configuration for fiscal computation. If None, uses default
            config (empty revenue/cost fields, by_year=True, cumulative=True).

    Returns:
        IndicatorResult containing:
        - List of FiscalIndicators for each year (or single aggregate)
        - Metadata with configuration and panel info
        - Warnings list (e.g., for null values, missing fields)
        - Excluded count (always 0 for fiscal indicators)

    Raises:
        ValueError: If no revenue or cost fields are configured.
        ValueError: If no configured fiscal fields exist in the panel.
    """
    if config is None:
        config = FiscalConfig()

    # Validate configuration
    if not config.revenue_fields and not config.cost_fields:
        raise ValueError(
            "At least one revenue field or cost field must be configured. "
            "Received empty revenue_fields and cost_fields lists."
        )

    # Handle empty panel
    if panel.table.num_rows == 0:
        warnings.warn(
            "Panel is empty (0 rows). Returning empty fiscal indicators.",
            stacklevel=2,
        )
        metadata = {
            "revenue_fields": config.revenue_fields,
            "cost_fields": config.cost_fields,
            "by_year": config.by_year,
            "aggregate_years": config.aggregate_years,
            "cumulative": config.cumulative,
            "panel_shape": panel.shape,
            "panel_metadata": panel.metadata,
        }
        return IndicatorResult(
            indicators=[],
            metadata=metadata,
            warnings=["Panel is empty (0 rows). Returning empty fiscal indicators."],
        )

    # Capture warnings during computation
    captured_warnings: list[str] = []

    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")

        # Determine year grouping
        # by_year has precedence. If by_year=False and aggregate_years=False,
        # keep annual detail instead of collapsing across years.
        group_by_year = config.by_year or not config.aggregate_years

        try:
            # Compute annual totals
            annual_table, null_warnings = _compute_annual_totals(
                panel.table,
                config.revenue_fields,
                config.cost_fields,
                by_year=group_by_year,
            )
            captured_warnings.extend(null_warnings)
        except ValueError as e:
            # No fiscal fields found in panel
            warnings.warn(str(e), stacklevel=2)
            metadata = {
                "revenue_fields": config.revenue_fields,
                "cost_fields": config.cost_fields,
                "by_year": config.by_year,
                "aggregate_years": config.aggregate_years,
                "cumulative": config.cumulative,
                "panel_shape": panel.shape,
                "panel_metadata": panel.metadata,
            }
            return IndicatorResult(
                indicators=[],
                metadata=metadata,
                warnings=[str(e)],
            )

        # Compute cumulative totals if requested and year detail is present
        has_year_detail = "year" in annual_table.column_names
        if config.cumulative and has_year_detail:
            annual_table = _compute_cumulative_totals(annual_table)

        # Capture warning messages
        for w in warning_list:
            captured_warnings.append(str(w.message))

    # Convert table to FiscalIndicators list
    indicators: list[FiscalIndicators] = []

    for i in range(annual_table.num_rows):
        field_name = annual_table.column("field_name")[i].as_py()
        revenue = annual_table.column("revenue")[i].as_py()
        cost = annual_table.column("cost")[i].as_py()
        balance = annual_table.column("balance")[i].as_py()

        year = None
        if "year" in annual_table.column_names:
            year = annual_table.column("year")[i].as_py()

        cumulative_revenue = None
        cumulative_cost = None
        cumulative_balance = None
        if "cumulative_revenue" in annual_table.column_names:
            cumulative_revenue = annual_table.column("cumulative_revenue")[i].as_py()
            cumulative_cost = annual_table.column("cumulative_cost")[i].as_py()
            cumulative_balance = annual_table.column("cumulative_balance")[i].as_py()

        indicator = FiscalIndicators(
            field_name=field_name,
            year=year,
            revenue=revenue,
            cost=cost,
            balance=balance,
            cumulative_revenue=cumulative_revenue,
            cumulative_cost=cumulative_cost,
            cumulative_balance=cumulative_balance,
        )
        indicators.append(indicator)

    # Build metadata
    metadata = {
        "revenue_fields": config.revenue_fields,
        "cost_fields": config.cost_fields,
        "by_year": config.by_year,
        "aggregate_years": config.aggregate_years,
        "cumulative": config.cumulative,
        "group_by_year": group_by_year,
        "panel_shape": panel.shape,
        "panel_metadata": panel.metadata,
    }

    return IndicatorResult(
        indicators=indicators,
        metadata=metadata,
        warnings=captured_warnings,
    )
