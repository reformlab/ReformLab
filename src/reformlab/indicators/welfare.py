"""Welfare indicator computation for baseline vs reform scenario comparison.

Story 4.3: Implement Welfare Indicators

This module provides:
- compare_households: Join baseline and reform panels and compute net changes
- aggregate_welfare_by_decile: Aggregate welfare metrics by income decile
- aggregate_welfare_by_region: Aggregate welfare metrics by region
- compute_welfare_indicators: Main API for computing welfare indicators
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Sequence

import pyarrow as pa
import pyarrow.compute as pc

from reformlab.indicators.deciles import assign_deciles
from reformlab.indicators.types import (
    IndicatorResult,
    WelfareConfig,
    WelfareIndicators,
)

if TYPE_CHECKING:
    from reformlab.orchestrator.panel import PanelOutput


def compare_households(
    baseline: PanelOutput,
    reform: PanelOutput,
    welfare_field: str,
    join_on_year: bool = True,
    carry_fields: Sequence[str] | None = None,
) -> tuple[pa.Table, int]:
    """Join baseline and reform panels and compute household-level net changes.

    Performs inner join on (household_id, year) to match households, then computes
    net change (reform - baseline) for the welfare field.

    Args:
        baseline: Baseline scenario panel output.
        reform: Reform scenario panel output.
        welfare_field: Name of the welfare field to compare.
        join_on_year: If True, join on (household_id, year). If False, join
            on household_id only.
        carry_fields: Additional baseline fields to carry into the joined
            output (for downstream grouping).

    Returns:
        Tuple of (comparison_table, unmatched_count):
        - comparison_table: Table with household_id, year (if join_on_year), welfare
            fields from both scenarios, and net_change column.
        - unmatched_count: Number of households present in only one panel.

    Raises:
        ValueError: If welfare_field is not in baseline or reform panels.
        ValueError: If required join keys (household_id, year) are missing.
    """
    # Validate welfare field exists in both panels
    if welfare_field not in baseline.table.column_names:
        raise ValueError(
            f"Welfare field '{welfare_field}' not found in baseline panel. "
            f"Available columns: {baseline.table.column_names}"
        )
    if welfare_field not in reform.table.column_names:
        raise ValueError(
            f"Welfare field '{welfare_field}' not found in reform panel. "
            f"Available columns: {reform.table.column_names}"
        )

    # Validate join keys
    join_keys = ["household_id"]
    if join_on_year:
        join_keys.append("year")

    for key in join_keys:
        if key not in baseline.table.column_names:
            raise ValueError(
                f"Join key '{key}' not found in baseline panel. "
                f"Available columns: {baseline.table.column_names}"
            )
        if key not in reform.table.column_names:
            raise ValueError(
                f"Join key '{key}' not found in reform panel. "
                f"Available columns: {reform.table.column_names}"
            )

    # Prepare tables for join: select only needed columns
    baseline_select = join_keys + [welfare_field]
    reform_select = join_keys + [welfare_field]

    # Add additional baseline fields needed for downstream grouping.
    for field in carry_fields or ():
        if field not in baseline.table.column_names:
            raise ValueError(
                f"Field '{field}' not found in baseline panel. "
                f"Available columns: {baseline.table.column_names}"
            )
        if field not in baseline_select:
            baseline_select.append(field)

    baseline_table = baseline.table.select(baseline_select)
    reform_table = reform.table.select(reform_select)

    # Rename welfare field to avoid collision
    baseline_welfare_col = f"_baseline_{welfare_field}"
    reform_welfare_col = f"_reform_{welfare_field}"

    baseline_table = baseline_table.rename_columns([
        baseline_welfare_col if c == welfare_field else c
        for c in baseline_table.column_names
    ])
    reform_table = reform_table.rename_columns([
        reform_welfare_col if c == welfare_field else c
        for c in reform_table.column_names
    ])

    # Inner join to match households
    joined = baseline_table.join(
        reform_table,
        keys=join_keys,
        join_type="inner",
    )

    # Calculate exact unmatched count from both sides using anti-joins.
    baseline_keys = baseline.table.select(join_keys)
    reform_keys = reform.table.select(join_keys)
    unmatched_baseline = baseline_keys.join(
        reform_keys,
        keys=join_keys,
        join_type="left anti",
    ).num_rows
    unmatched_reform = reform_keys.join(
        baseline_keys,
        keys=join_keys,
        join_type="left anti",
    ).num_rows
    unmatched_count = unmatched_baseline + unmatched_reform

    if unmatched_count > 0:
        unit_label = "household-year pair(s)" if join_on_year else "household(s)"
        warnings.warn(
            f"Excluded {unmatched_count} unmatched {unit_label} from welfare comparison.",
            stacklevel=2,
        )

    # Compute net change: reform - baseline
    baseline_values = joined.column(baseline_welfare_col)
    reform_values = joined.column(reform_welfare_col)
    net_change = pc.subtract(reform_values, baseline_values)

    # Add net_change column
    result_table = joined.append_column("net_change", net_change)

    return result_table, unmatched_count


def _classify_welfare(
    net_change: pa.ChunkedArray,
    threshold: float,
) -> tuple[pa.ChunkedArray, pa.ChunkedArray, pa.ChunkedArray]:
    """Classify households as winners, losers, or neutral based on net change.

    Args:
        net_change: Array of net welfare changes.
        threshold: Classification threshold.

    Returns:
        Tuple of (winner_mask, loser_mask, neutral_mask).
    """
    winner_mask = pc.greater(net_change, pa.scalar(threshold))
    loser_mask = pc.less(net_change, pa.scalar(-threshold))
    neutral_mask = pc.and_(
        pc.greater_equal(net_change, pa.scalar(-threshold)),
        pc.less_equal(net_change, pa.scalar(threshold)),
    )
    return winner_mask, loser_mask, neutral_mask


def aggregate_welfare_by_decile(
    table: pa.Table,
    welfare_field: str,
    income_field: str,
    threshold: float,
    group_by_year: bool = False,
) -> tuple[pa.Table, int]:
    """Aggregate welfare metrics by income decile.

    Assigns households to deciles based on baseline income, then computes
    welfare metrics (winner/loser counts, mean/median changes) per decile.

    Args:
        table: Comparison table with net_change column.
        welfare_field: Name of the welfare field (for output metadata).
        income_field: Name of income field for decile assignment.
        threshold: Classification threshold for winner/loser determination.
        group_by_year: If True, group by (decile, year). Otherwise by decile.

    Returns:
        Tuple of (aggregation_table, excluded_count):
        - aggregation_table: Table with welfare metrics per decile (and year if grouped).
        - excluded_count: Number of households excluded from decile assignment.

    Raises:
        ValueError: If income_field is not in table.
        ValueError: If net_change column is not in table.
    """
    if "net_change" not in table.column_names:
        raise ValueError("Table must have 'net_change' column for welfare aggregation.")

    # Assign deciles based on income
    # Note: We use baseline income for decile assignment
    # The income field should already be in the table (from baseline, without prefix)
    if income_field not in table.column_names:
        raise ValueError(
            f"Income field '{income_field}' not found in table. "
            f"Available columns: {table.column_names}"
        )

    table_with_deciles, excluded_count = assign_deciles(table, income_field)

    if excluded_count > 0:
        warnings.warn(
            f"Excluded {excluded_count} household(s) from welfare decile aggregation "
            "due to missing income.",
            stacklevel=2,
        )

    # Classify winners/losers/neutral
    net_change = table_with_deciles.column("net_change")
    winner_mask, loser_mask, neutral_mask = _classify_welfare(net_change, threshold)

    # Add classification columns
    table_with_deciles = table_with_deciles.append_column("is_winner", winner_mask)
    table_with_deciles = table_with_deciles.append_column("is_loser", loser_mask)
    table_with_deciles = table_with_deciles.append_column("is_neutral", neutral_mask)

    # Group and aggregate
    group_keys = ["decile", "year"] if group_by_year else ["decile"]
    grouped = table_with_deciles.group_by(group_keys)

    # Compute aggregations
    agg_result = grouped.aggregate([
        ("is_winner", "sum"),
        ("is_loser", "sum"),
        ("is_neutral", "sum"),
        ("net_change", "mean"),
        ("net_change", "approximate_median"),
        ("net_change", "sum"),
    ])

    # Compute mean_gain and mean_loss separately (requires filtering)
    result_rows: list[dict[str, int | float | str | None]] = []

    for i in range(agg_result.num_rows):
        decile = agg_result.column("decile")[i].as_py()
        winner_count = agg_result.column("is_winner_sum")[i].as_py()
        loser_count = agg_result.column("is_loser_sum")[i].as_py()
        neutral_count = agg_result.column("is_neutral_sum")[i].as_py()
        mean_change = agg_result.column("net_change_mean")[i].as_py()
        median_change = agg_result.column("net_change_approximate_median")[i].as_py()
        total_change = agg_result.column("net_change_sum")[i].as_py()

        year = None
        if group_by_year:
            year = agg_result.column("year")[i].as_py()

        # Filter for this group to compute mean_gain and mean_loss
        if group_by_year:
            group_mask = pc.and_(
                pc.equal(table_with_deciles.column("decile"), pa.scalar(decile)),
                pc.equal(table_with_deciles.column("year"), pa.scalar(year)),
            )
        else:
            group_mask = pc.equal(table_with_deciles.column("decile"), pa.scalar(decile))

        group_table = table_with_deciles.filter(group_mask)
        group_changes = group_table.column("net_change")

        # Compute mean_gain (mean of positive changes)
        positive_mask = pc.greater(group_changes, pa.scalar(0.0))
        positive_changes = pc.filter(group_changes, positive_mask)
        mean_gain = pc.mean(positive_changes).as_py() if positive_changes.length() > 0 else 0.0

        # Compute mean_loss (mean of negative changes, absolute value)
        negative_mask = pc.less(group_changes, pa.scalar(0.0))
        negative_changes = pc.filter(group_changes, negative_mask)
        if negative_changes.length() > 0:
            abs_negative = pc.abs(negative_changes)
            mean_loss = pc.mean(abs_negative).as_py()
        else:
            mean_loss = 0.0

        # Compute total_gain and total_loss
        total_gain = pc.sum(positive_changes).as_py() if positive_changes.length() > 0 else 0.0
        total_loss = pc.sum(pc.abs(negative_changes)).as_py() if negative_changes.length() > 0 else 0.0

        # Net change
        net_change_val = total_gain - total_loss

        row = {
            "field_name": welfare_field,
            "decile": decile,
            "winner_count": winner_count,
            "loser_count": loser_count,
            "neutral_count": neutral_count,
            "mean_gain": mean_gain,
            "mean_loss": mean_loss,
            "median_change": median_change,
            "total_gain": total_gain,
            "total_loss": total_loss,
            "net_change": net_change_val,
        }

        if group_by_year:
            row["year"] = year

        result_rows.append(row)

    # Convert to PyArrow table
    if not result_rows:
        return _empty_welfare_aggregation_table(group_by_year, group_type="decile"), excluded_count

    # Build schema
    schema_dict = {
        "field_name": pa.array([r["field_name"] for r in result_rows], type=pa.utf8()),
        "decile": pa.array([r["decile"] for r in result_rows], type=pa.int64()),
    }
    if group_by_year:
        schema_dict["year"] = pa.array([r["year"] for r in result_rows], type=pa.int64())

    schema_dict.update({
        "winner_count": pa.array([r["winner_count"] for r in result_rows], type=pa.int64()),
        "loser_count": pa.array([r["loser_count"] for r in result_rows], type=pa.int64()),
        "neutral_count": pa.array([r["neutral_count"] for r in result_rows], type=pa.int64()),
        "mean_gain": pa.array([r["mean_gain"] for r in result_rows], type=pa.float64()),
        "mean_loss": pa.array([r["mean_loss"] for r in result_rows], type=pa.float64()),
        "median_change": pa.array([r["median_change"] for r in result_rows], type=pa.float64()),
        "total_gain": pa.array([r["total_gain"] for r in result_rows], type=pa.float64()),
        "total_loss": pa.array([r["total_loss"] for r in result_rows], type=pa.float64()),
        "net_change": pa.array([r["net_change"] for r in result_rows], type=pa.float64()),
    })

    result_table = pa.table(schema_dict)

    # Sort by field_name, year (if present), decile
    sort_keys: list[tuple[str, str]] = [("field_name", "ascending")]
    if group_by_year:
        sort_keys.extend([("year", "ascending"), ("decile", "ascending")])
    else:
        sort_keys.append(("decile", "ascending"))

    return result_table.sort_by(sort_keys), excluded_count


def aggregate_welfare_by_region(
    table: pa.Table,
    welfare_field: str,
    region_field: str,
    threshold: float,
    group_by_year: bool = False,
) -> tuple[pa.Table, int]:
    """Aggregate welfare metrics by region.

    Groups households by region code, then computes welfare metrics
    (winner/loser counts, mean/median changes) per region.

    Args:
        table: Comparison table with net_change column.
        welfare_field: Name of the welfare field (for output metadata).
        region_field: Name of region field for grouping.
        threshold: Classification threshold for winner/loser determination.
        group_by_year: If True, group by (region, year). Otherwise by region.

    Returns:
        Tuple of (aggregation_table, excluded_count):
        - aggregation_table: Table with welfare metrics per region (and year if grouped).
        - excluded_count: Number of households excluded from region grouping.

    Raises:
        ValueError: If region_field is not in table.
        ValueError: If net_change column is not in table.
    """
    if "net_change" not in table.column_names:
        raise ValueError("Table must have 'net_change' column for welfare aggregation.")

    # Use baseline region code for grouping
    # The region field should already be in the table (from baseline, without prefix)
    if region_field not in table.column_names:
        raise ValueError(
            f"Region field '{region_field}' not found in table. "
            f"Available columns: {table.column_names}"
        )

    # Filter out null/missing region codes
    region_col = table.column(region_field)
    valid_region_mask = pc.invert(pc.is_null(region_col))
    valid_table = table.filter(valid_region_mask)
    excluded_count = table.num_rows - valid_table.num_rows

    if excluded_count > 0:
        warnings.warn(
            f"Excluded {excluded_count} household(s) from welfare region aggregation "
            "due to missing region codes.",
            stacklevel=2,
        )

    if valid_table.num_rows == 0:
        return _empty_welfare_aggregation_table(group_by_year, group_type="region"), excluded_count

    # Classify winners/losers/neutral
    net_change = valid_table.column("net_change")
    winner_mask, loser_mask, neutral_mask = _classify_welfare(net_change, threshold)

    # Add classification columns
    valid_table = valid_table.append_column("is_winner", winner_mask)
    valid_table = valid_table.append_column("is_loser", loser_mask)
    valid_table = valid_table.append_column("is_neutral", neutral_mask)

    # Rename region_field to "region" for consistent aggregation (if needed)
    if region_field != "region":
        col_names = [
            "region" if c == region_field else c
            for c in valid_table.column_names
        ]
        valid_table = valid_table.rename_columns(col_names)

    # Group and aggregate
    group_keys = ["region", "year"] if group_by_year else ["region"]
    grouped = valid_table.group_by(group_keys)

    # Compute aggregations
    agg_result = grouped.aggregate([
        ("is_winner", "sum"),
        ("is_loser", "sum"),
        ("is_neutral", "sum"),
        ("net_change", "mean"),
        ("net_change", "approximate_median"),
        ("net_change", "sum"),
    ])

    # Compute mean_gain and mean_loss separately
    result_rows: list[dict[str, int | float | str | None]] = []

    for i in range(agg_result.num_rows):
        region = agg_result.column("region")[i].as_py()
        winner_count = agg_result.column("is_winner_sum")[i].as_py()
        loser_count = agg_result.column("is_loser_sum")[i].as_py()
        neutral_count = agg_result.column("is_neutral_sum")[i].as_py()
        mean_change = agg_result.column("net_change_mean")[i].as_py()
        median_change = agg_result.column("net_change_approximate_median")[i].as_py()
        total_change = agg_result.column("net_change_sum")[i].as_py()

        year = None
        if group_by_year:
            year = agg_result.column("year")[i].as_py()

        # Filter for this group
        if group_by_year:
            group_mask = pc.and_(
                pc.equal(valid_table.column("region"), pa.scalar(region)),
                pc.equal(valid_table.column("year"), pa.scalar(year)),
            )
        else:
            group_mask = pc.equal(valid_table.column("region"), pa.scalar(region))

        group_table = valid_table.filter(group_mask)
        group_changes = group_table.column("net_change")

        # Compute mean_gain (mean of positive changes)
        positive_mask = pc.greater(group_changes, pa.scalar(0.0))
        positive_changes = pc.filter(group_changes, positive_mask)
        mean_gain = pc.mean(positive_changes).as_py() if positive_changes.length() > 0 else 0.0

        # Compute mean_loss (mean of negative changes, absolute value)
        negative_mask = pc.less(group_changes, pa.scalar(0.0))
        negative_changes = pc.filter(group_changes, negative_mask)
        if negative_changes.length() > 0:
            abs_negative = pc.abs(negative_changes)
            mean_loss = pc.mean(abs_negative).as_py()
        else:
            mean_loss = 0.0

        # Compute total_gain and total_loss
        total_gain = pc.sum(positive_changes).as_py() if positive_changes.length() > 0 else 0.0
        total_loss = pc.sum(pc.abs(negative_changes)).as_py() if negative_changes.length() > 0 else 0.0

        # Net change
        net_change_val = total_gain - total_loss

        row = {
            "field_name": welfare_field,
            "region": str(region),
            "winner_count": winner_count,
            "loser_count": loser_count,
            "neutral_count": neutral_count,
            "mean_gain": mean_gain,
            "mean_loss": mean_loss,
            "median_change": median_change,
            "total_gain": total_gain,
            "total_loss": total_loss,
            "net_change": net_change_val,
        }

        if group_by_year:
            row["year"] = year

        result_rows.append(row)

    # Convert to PyArrow table
    if not result_rows:
        return _empty_welfare_aggregation_table(group_by_year, group_type="region"), excluded_count

    # Build schema
    schema_dict = {
        "field_name": pa.array([r["field_name"] for r in result_rows], type=pa.utf8()),
        "region": pa.array([r["region"] for r in result_rows], type=pa.utf8()),
    }
    if group_by_year:
        schema_dict["year"] = pa.array([r["year"] for r in result_rows], type=pa.int64())

    schema_dict.update({
        "winner_count": pa.array([r["winner_count"] for r in result_rows], type=pa.int64()),
        "loser_count": pa.array([r["loser_count"] for r in result_rows], type=pa.int64()),
        "neutral_count": pa.array([r["neutral_count"] for r in result_rows], type=pa.int64()),
        "mean_gain": pa.array([r["mean_gain"] for r in result_rows], type=pa.float64()),
        "mean_loss": pa.array([r["mean_loss"] for r in result_rows], type=pa.float64()),
        "median_change": pa.array([r["median_change"] for r in result_rows], type=pa.float64()),
        "total_gain": pa.array([r["total_gain"] for r in result_rows], type=pa.float64()),
        "total_loss": pa.array([r["total_loss"] for r in result_rows], type=pa.float64()),
        "net_change": pa.array([r["net_change"] for r in result_rows], type=pa.float64()),
    })

    result_table = pa.table(schema_dict)

    # Sort by field_name, year (if present), region
    sort_keys: list[tuple[str, str]] = [("field_name", "ascending")]
    if group_by_year:
        sort_keys.extend([("year", "ascending"), ("region", "ascending")])
    else:
        sort_keys.append(("region", "ascending"))

    return result_table.sort_by(sort_keys), excluded_count


def _empty_welfare_aggregation_table(
    group_by_year: bool,
    group_type: str,
) -> pa.Table:
    """Return an empty welfare aggregation table with the stable output schema."""
    schema_dict = {
        "field_name": pa.array([], type=pa.utf8()),
    }

    if group_type == "decile":
        schema_dict["decile"] = pa.array([], type=pa.int64())
    else:
        schema_dict["region"] = pa.array([], type=pa.utf8())

    if group_by_year:
        schema_dict["year"] = pa.array([], type=pa.int64())

    schema_dict.update({
        "winner_count": pa.array([], type=pa.int64()),
        "loser_count": pa.array([], type=pa.int64()),
        "neutral_count": pa.array([], type=pa.int64()),
        "mean_gain": pa.array([], type=pa.float64()),
        "mean_loss": pa.array([], type=pa.float64()),
        "median_change": pa.array([], type=pa.float64()),
        "total_gain": pa.array([], type=pa.float64()),
        "total_loss": pa.array([], type=pa.float64()),
        "net_change": pa.array([], type=pa.float64()),
    })

    return pa.table(schema_dict)


def compute_welfare_indicators(
    baseline: PanelOutput,
    reform: PanelOutput,
    config: WelfareConfig | None = None,
) -> IndicatorResult:
    """Compute welfare indicators comparing baseline and reform scenarios.

    Joins baseline and reform panels on (household_id, year),
    computes net welfare changes, classifies households as winners/losers/neutral,
    and aggregates metrics by income decile or region.

    Args:
        baseline: Baseline scenario panel output.
        reform: Reform scenario panel output.
        config: Configuration for welfare computation. If None, uses default
            config (welfare_field="disposable_income", threshold=0.0,
            group_by_decile=True).

    Returns:
        IndicatorResult containing:
        - List of WelfareIndicators for each (field, group, year) combination
        - Metadata with configuration and panel info
        - Warnings list (e.g., for unmatched households)
        - Unmatched count (households present in only one panel)

    Raises:
        ValueError: If welfare field is not in baseline or reform panels.
        ValueError: If required join keys are missing.
        ValueError: If both group_by_decile and group_by_region are False.
    """
    if config is None:
        config = WelfareConfig()

    # Validate grouping configuration
    if not config.group_by_decile and not config.group_by_region:
        raise ValueError(
            "At least one of group_by_decile or group_by_region must be True."
        )

    # Capture warnings
    captured_warnings: list[str] = []

    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")

        # Determine year grouping
        # by_year has precedence. If by_year=False and aggregate_years=False,
        # keep annual detail instead of collapsing across years.
        group_by_year = config.by_year or not config.aggregate_years

        # Compare households and compute net changes.
        # Keep join aligned on year even when aggregating across years to
        # avoid cross-year cartesian matches in multi-year panels.
        carry_fields = (
            [config.income_field]
            if config.group_by_decile
            else [config.region_field]
        )
        comparison_table, unmatched_count = compare_households(
            baseline,
            reform,
            config.welfare_field,
            join_on_year=True,
            carry_fields=carry_fields,
        )

        # Aggregate by chosen grouping dimension
        # Decile takes precedence if both are True
        if config.group_by_decile:
            agg_table, excluded_count = aggregate_welfare_by_decile(
                comparison_table,
                config.welfare_field,
                config.income_field,
                config.threshold,
                group_by_year=group_by_year,
            )
            group_type = "decile"
        else:
            agg_table, excluded_count = aggregate_welfare_by_region(
                comparison_table,
                config.welfare_field,
                config.region_field,
                config.threshold,
                group_by_year=group_by_year,
            )
            group_type = "region"

        # Capture warning messages
        for w in warning_list:
            captured_warnings.append(str(w.message))

    # Convert aggregation table to WelfareIndicators list
    indicators: list[WelfareIndicators] = []

    for i in range(agg_table.num_rows):
        field_name = agg_table.column("field_name")[i].as_py()
        winner_count = agg_table.column("winner_count")[i].as_py()
        loser_count = agg_table.column("loser_count")[i].as_py()
        neutral_count = agg_table.column("neutral_count")[i].as_py()
        mean_gain = agg_table.column("mean_gain")[i].as_py()
        mean_loss = agg_table.column("mean_loss")[i].as_py()
        median_change = agg_table.column("median_change")[i].as_py()
        total_gain = agg_table.column("total_gain")[i].as_py()
        total_loss = agg_table.column("total_loss")[i].as_py()
        net_change = agg_table.column("net_change")[i].as_py()

        if group_type == "decile":
            group_value = agg_table.column("decile")[i].as_py()
        else:
            group_value = agg_table.column("region")[i].as_py()

        year = None
        if group_by_year:
            year = agg_table.column("year")[i].as_py()

        indicator = WelfareIndicators(
            field_name=field_name,
            group_type=group_type,
            group_value=group_value,
            year=year,
            winner_count=winner_count,
            loser_count=loser_count,
            neutral_count=neutral_count,
            mean_gain=mean_gain,
            mean_loss=mean_loss,
            median_change=median_change,
            total_gain=total_gain,
            total_loss=total_loss,
            net_change=net_change,
        )
        indicators.append(indicator)

    # Build metadata
    metadata = {
        "welfare_field": config.welfare_field,
        "threshold": config.threshold,
        "by_year": config.by_year,
        "aggregate_years": config.aggregate_years,
        "group_by_year": group_by_year,
        "group_by_decile": config.group_by_decile,
        "group_by_region": config.group_by_region,
        "group_type": group_type,
        "baseline_panel_shape": baseline.shape,
        "reform_panel_shape": reform.shape,
        "baseline_metadata": baseline.metadata,
        "reform_metadata": reform.metadata,
        "unmatched_count": unmatched_count,
        "excluded_count": excluded_count,
    }

    if config.group_by_decile:
        metadata["income_field"] = config.income_field
    if config.group_by_region:
        metadata["region_field"] = config.region_field

    return IndicatorResult(
        indicators=indicators,
        metadata=metadata,
        warnings=captured_warnings,
        excluded_count=excluded_count,
        unmatched_count=unmatched_count,
    )
