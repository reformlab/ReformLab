"""Geographic indicator computation over panel outputs.

Story 4.2: Implement Geographic Aggregation Indicators

This module provides:
- assign_regions: Validate and handle region codes with optional reference table
- aggregate_by_region: Compute aggregation metrics for each region
- compute_geographic_indicators: Main API for computing region-based indicators
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import pyarrow as pa
import pyarrow.compute as pc

from reformlab.indicators.types import (
    GeographicConfig,
    IndicatorResult,
    RegionIndicators,
)

if TYPE_CHECKING:
    from reformlab.orchestrator.panel import PanelOutput


def assign_regions(
    table: pa.Table,
    region_field: str,
    reference_table: pa.Table | None = None,
) -> tuple[pa.Table, int, int]:
    """Validate region codes and handle missing/unmatched values.

    Filters out households with null/missing region codes, and optionally
    validates region codes against a reference table. Unmatched region codes
    are reassigned to "_UNMATCHED" category when a reference table is provided.

    Args:
        table: PyArrow table containing household data with region field.
        region_field: Name of the region code column.
        reference_table: Optional table with valid region codes. If provided,
            must contain a column matching region_field name.

    Returns:
        Tuple of (validated_table, excluded_count, unmatched_count):
        - validated_table: Table with valid-region households. Region codes are
            validated (if reference provided) with unmatched codes set to "_UNMATCHED".
        - excluded_count: Number of households excluded due to null region codes.
        - unmatched_count: Number of households with unmatched region codes
            (0 if no reference table provided).

    Raises:
        ValueError: If region_field is not in the table.
        ValueError: If reference_table does not contain region_field column.
        ValueError: If no households have valid region codes.
    """
    if region_field not in table.column_names:
        raise ValueError(
            f"Region field '{region_field}' not found in table. "
            f"Available columns: {table.column_names}"
        )

    region_col = table.column(region_field)

    # Filter out null region values
    valid_region_mask = pc.invert(pc.is_null(region_col))
    valid_table = table.filter(valid_region_mask)
    excluded_count = table.num_rows - valid_table.num_rows

    if excluded_count > 0:
        warnings.warn(
            f"Excluded {excluded_count} household(s) with missing region codes "
            f"from geographic grouping.",
            stacklevel=2,
        )

    if valid_table.num_rows == 0:
        raise ValueError(
            f"No households with valid region codes in field '{region_field}'. "
            "Cannot compute geographic indicators."
        )

    # Handle unmatched region codes if reference table provided
    unmatched_count = 0
    if reference_table is not None:
        if region_field not in reference_table.column_names:
            raise ValueError(
                f"Reference table does not contain region field '{region_field}'. "
                f"Available columns: {reference_table.column_names}"
            )

        # Get valid region codes from reference table
        valid_regions = reference_table.column(region_field)
        valid_region_set = set(valid_regions.to_pylist())

        # Identify unmatched region codes
        panel_regions = valid_table.column(region_field)
        is_matched = pc.is_in(panel_regions, value_set=pa.array(list(valid_region_set)))
        unmatched_mask = pc.invert(is_matched)
        unmatched_count = pc.sum(pc.cast(unmatched_mask, pa.int64())).as_py()

        if unmatched_count > 0:
            warnings.warn(
                f"Found {unmatched_count} household(s) with unmatched region codes. "
                f"Grouping into '_UNMATCHED' category.",
                stacklevel=2,
            )

            # Replace unmatched region codes with "_UNMATCHED"
            updated_regions = pc.if_else(
                unmatched_mask,
                pa.scalar("_UNMATCHED"),
                panel_regions,
            )

            # Replace region column in table
            region_idx = valid_table.schema.get_field_index(region_field)
            valid_table = valid_table.set_column(
                region_idx, region_field, updated_regions
            )

    return valid_table, excluded_count, unmatched_count


def aggregate_by_region(
    table: pa.Table,
    numeric_fields: list[str],
    region_field: str,
    group_by_year: bool = False,
) -> pa.Table:
    """Compute aggregation metrics for each region and numeric field.

    For each numeric field and each region, computes: count, mean, median,
    sum, min, max. Optionally groups by year as well.

    Args:
        table: PyArrow table with region column (optionally "year" column).
        numeric_fields: List of numeric field names to aggregate.
        region_field: Name of the region code column.
        group_by_year: If True, group by (region, year). Otherwise by region.

    Returns:
        PyArrow table with aggregated metrics. Columns depend on group_by_year:
        - group_by_year=False: region, field_name, count, mean, median,
            sum, min, max
        - group_by_year=True: region, year, field_name, count, mean, median,
            sum, min, max

    Raises:
        ValueError: If table does not have region_field column.
        ValueError: If group_by_year=True but table does not have "year" column.
    """
    if region_field not in table.column_names:
        raise ValueError(
            f"Table must have '{region_field}' column for aggregation."
        )

    if group_by_year and "year" not in table.column_names:
        raise ValueError("Table must have 'year' column when group_by_year=True.")

    group_keys = [region_field, "year"] if group_by_year else [region_field]
    grouped = table.group_by(group_keys)
    result_tables: list[pa.Table] = []

    for field_name in numeric_fields:
        if field_name not in table.column_names:
            continue

        field_type = table.schema.field(field_name).type

        # Only aggregate numeric fields
        if not (pa.types.is_floating(field_type) or pa.types.is_integer(field_type)):
            continue

        # Compute aggregations (including grouped approximate median) in one pass.
        agg_result = grouped.aggregate([
            (field_name, "count"),
            (field_name, "sum"),
            (field_name, "mean"),
            (field_name, "approximate_median"),
            (field_name, "min"),
            (field_name, "max"),
        ])

        # Build one normalized result table per field.
        column_dict: dict[str, pa.Array] = {
            "field_name": pa.array(
                [field_name] * agg_result.num_rows,
                type=pa.utf8(),
            ),
            "region": agg_result.column(region_field),
            "count": agg_result.column(f"{field_name}_count"),
            "mean": agg_result.column(f"{field_name}_mean"),
            "median": agg_result.column(f"{field_name}_approximate_median"),
            "sum": agg_result.column(f"{field_name}_sum"),
            "min": agg_result.column(f"{field_name}_min"),
            "max": agg_result.column(f"{field_name}_max"),
        }
        if group_by_year:
            column_dict["year"] = agg_result.column("year")

        result_table = pa.table(column_dict)
        ordered_columns = ["field_name", "region"]
        if group_by_year:
            ordered_columns.append("year")
        ordered_columns.extend(["count", "mean", "median", "sum", "min", "max"])
        result_tables.append(result_table.select(ordered_columns))

    if not result_tables:
        return _empty_aggregation_table(group_by_year)

    combined = pa.concat_tables(result_tables)
    sort_keys: list[tuple[str, str]] = [("field_name", "ascending")]
    if group_by_year:
        sort_keys.extend([("year", "ascending"), ("region", "ascending")])
    else:
        sort_keys.append(("region", "ascending"))
    return combined.sort_by(sort_keys)


def _empty_aggregation_table(group_by_year: bool) -> pa.Table:
    """Return an empty aggregation table with the stable output schema."""
    schema_dict = {
        "field_name": pa.array([], type=pa.utf8()),
        "region": pa.array([], type=pa.utf8()),
    }
    if group_by_year:
        schema_dict["year"] = pa.array([], type=pa.int64())
    schema_dict.update({
        "count": pa.array([], type=pa.int64()),
        "mean": pa.array([], type=pa.float64()),
        "median": pa.array([], type=pa.float64()),
        "sum": pa.array([], type=pa.float64()),
        "min": pa.array([], type=pa.float64()),
        "max": pa.array([], type=pa.float64()),
    })
    return pa.table(schema_dict)


def compute_geographic_indicators(
    panel: PanelOutput,
    config: GeographicConfig | None = None,
) -> IndicatorResult:
    """Compute geographic indicators by region from panel output.

    Validates region codes, optionally checking against a reference table,
    then computes aggregation metrics (count, mean, median, sum, min, max) for
    each numeric field in the panel, grouped by region.

    Supports three modes:
    1. Single-year or aggregate across years (default): groups by region only
    2. by_year=True: groups by (region, year) for year-by-year analysis
    3. aggregate_years=False (with by_year=False): groups by (region, year)

    Args:
        panel: PanelOutput from orchestrator run containing household-year data.
        config: Configuration for geographic computation. If None, uses
            default config (region_field="region_code", aggregate_years=True).

    Returns:
        IndicatorResult containing:
        - List of RegionIndicators for each (field, region, year) combination
        - Metadata with configuration and panel info
        - Warnings list (e.g., for excluded/unmatched households)
        - Excluded count (households with null region codes)
        - Unmatched count (households with region codes not in reference table)

    Raises:
        ValueError: If region field is not in panel table.
        ValueError: If no households have valid region codes.
        ValueError: If reference_table provided but lacks region_field column.
    """
    if config is None:
        config = GeographicConfig()

    # Capture warnings
    captured_warnings: list[str] = []

    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")

        # Assign and validate regions
        table_with_regions, excluded_count, unmatched_count = assign_regions(
            panel.table,
            config.region_field,
            config.reference_table,
        )

        # Capture warning messages
        for w in warning_list:
            captured_warnings.append(str(w.message))

    # Identify numeric fields (exclude household_id, year, region_field)
    numeric_fields = []
    exclude_fields = {"household_id", "year", config.region_field}

    for field_name in table_with_regions.column_names:
        if field_name in exclude_fields:
            continue

        field_type = table_with_regions.schema.field(field_name).type
        if pa.types.is_floating(field_type) or pa.types.is_integer(field_type):
            numeric_fields.append(field_name)

    # Compute aggregations
    # by_year has precedence. If by_year=False and aggregate_years=False,
    # keep annual detail instead of collapsing across years.
    group_by_year = config.by_year or not config.aggregate_years
    agg_table = aggregate_by_region(
        table_with_regions,
        numeric_fields,
        config.region_field,
        group_by_year=group_by_year,
    )

    # Convert aggregation table to RegionIndicators list
    indicators: list[RegionIndicators] = []

    for i in range(agg_table.num_rows):
        field_name = agg_table.column("field_name")[i].as_py()
        region = agg_table.column("region")[i].as_py()
        count = agg_table.column("count")[i].as_py()
        mean = agg_table.column("mean")[i].as_py()
        median = agg_table.column("median")[i].as_py()
        sum_val = agg_table.column("sum")[i].as_py()
        min_val = agg_table.column("min")[i].as_py()
        max_val = agg_table.column("max")[i].as_py()

        year = None
        if group_by_year:
            year = agg_table.column("year")[i].as_py()

        indicator = RegionIndicators(
            field_name=field_name,
            region=region,
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
        "region_field": config.region_field,
        "by_year": config.by_year,
        "aggregate_years": config.aggregate_years,
        "group_by_year": group_by_year,
        "panel_shape": panel.shape,
        "panel_metadata": panel.metadata,
        "numeric_fields": numeric_fields,
        "excluded_count": excluded_count,
        "unmatched_count": unmatched_count,
        "has_reference_table": config.reference_table is not None,
    }

    return IndicatorResult(
        indicators=indicators,
        metadata=metadata,
        warnings=captured_warnings,
        excluded_count=excluded_count,
        unmatched_count=unmatched_count,
    )
