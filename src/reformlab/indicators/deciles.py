# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Income decile assignment and aggregation functions.

Story 4.1: Implement Distributional Indicators by Income Decile

This module provides:
- assign_deciles: Assign households to income deciles based on quantile boundaries
- aggregate_by_decile: Compute aggregation metrics for each decile
"""

from __future__ import annotations

import warnings

import pyarrow as pa
import pyarrow.compute as pc


def assign_deciles(
    table: pa.Table,
    income_field: str,
) -> tuple[pa.Table, int]:
    """Assign income deciles to households based on income distribution.

    Uses quantile-based boundaries to assign each household to decile 1-10
    (D1 = lowest 10%, D10 = highest 10%). Households with null/missing income
    are excluded from decile assignment.

    Args:
        table: PyArrow table containing household data with income field.
        income_field: Name of the income column to use for decile assignment.

    Returns:
        Tuple of (table_with_deciles, excluded_count):
        - table_with_deciles: Table with valid-income households and a "decile"
            column (int64, values 1-10).
        - excluded_count: Number of households excluded due to null income.

    Raises:
        ValueError: If income_field is not in the table.
        ValueError: If no households have valid income.
    """
    if income_field not in table.column_names:
        raise ValueError(
            f"Income field '{income_field}' not found in table. "
            f"Available columns: {table.column_names}"
        )

    income_col = table.column(income_field)
    income_type = table.schema.field(income_field).type

    # Filter out null income values (and NaN/Inf for floating-point income).
    valid_income_mask = pc.invert(pc.is_null(income_col))
    if pa.types.is_floating(income_type):
        valid_income_mask = pc.and_(valid_income_mask, pc.is_finite(income_col))

    valid_table = table.filter(valid_income_mask)
    excluded_count = table.num_rows - valid_table.num_rows

    if excluded_count > 0:
        warnings.warn(
            f"Excluded {excluded_count} household(s) with missing income "
            f"from decile assignment.",
            stacklevel=2,
        )

    if valid_table.num_rows == 0:
        raise ValueError(
            f"No households with valid income in field '{income_field}'. "
            "Cannot compute deciles."
        )

    # Compute decile boundaries (0.1, 0.2, ..., 0.9)
    valid_income = valid_table.column(income_field)
    quantiles = [i / 10.0 for i in range(1, 10)]

    # Compute quantile boundaries
    # pc.quantile returns an array with one element per quantile
    boundaries_array = pc.quantile(valid_income, q=quantiles)
    # Extract scalar values from the result array
    boundaries = [boundaries_array[i].as_py() for i in range(len(quantiles))]

    # Assign deciles based on boundaries
    # Decile 1: income <= boundaries[0]
    # Decile 2: boundaries[0] < income <= boundaries[1]
    # ...
    # Decile 10: income > boundaries[8]

    decile_array = pa.array([10] * valid_table.num_rows, type=pa.int64())

    # Build decile assignment from boundaries
    # Start from highest to avoid overwriting
    for decile_num in range(9, 0, -1):
        threshold = boundaries[decile_num - 1]
        mask = pc.less_equal(valid_income, pa.scalar(threshold))
        decile_array = pc.if_else(
            mask, pa.scalar(decile_num, type=pa.int64()), decile_array
        )

    # Append decile column to table
    result_table = valid_table.append_column("decile", decile_array)

    return result_table, excluded_count


def aggregate_by_decile(
    table: pa.Table,
    numeric_fields: list[str],
    group_by_year: bool = False,
) -> pa.Table:
    """Compute aggregation metrics for each decile and numeric field.

    For each numeric field and each decile, computes: count, mean, median,
    sum, min, max. Optionally groups by year as well.

    Args:
        table: PyArrow table with "decile" column (optionally "year" column).
        numeric_fields: List of numeric field names to aggregate.
        group_by_year: If True, group by (decile, year). Otherwise by decile.

    Returns:
        PyArrow table with aggregated metrics. Columns depend on group_by_year:
        - group_by_year=False: decile, field_name, count, mean, median,
            sum, min, max
        - group_by_year=True: decile, year, field_name, count, mean, median,
            sum, min, max

    Raises:
        ValueError: If table does not have "decile" column.
        ValueError: If group_by_year=True but table does not have "year" column.
    """
    if "decile" not in table.column_names:
        raise ValueError("Table must have 'decile' column for aggregation.")

    if group_by_year and "year" not in table.column_names:
        raise ValueError("Table must have 'year' column when group_by_year=True.")

    group_keys = ["decile", "year"] if group_by_year else ["decile"]
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
        agg_result = grouped.aggregate(
            [
                (field_name, "count"),
                (field_name, "sum"),
                (field_name, "mean"),
                (field_name, "approximate_median"),
                (field_name, "min"),
                (field_name, "max"),
            ]
        )
        # Build one normalized result table per field.
        column_dict: dict[str, pa.Array] = {
            "field_name": pa.array(
                [field_name] * agg_result.num_rows,
                type=pa.utf8(),
            ),
            "decile": agg_result.column("decile"),
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
        ordered_columns = ["field_name", "decile"]
        if group_by_year:
            ordered_columns.append("year")
        ordered_columns.extend(["count", "mean", "median", "sum", "min", "max"])
        result_tables.append(result_table.select(ordered_columns))

    if not result_tables:
        return _empty_aggregation_table(group_by_year)

    combined = pa.concat_tables(result_tables)
    sort_keys: list[tuple[str, str]] = [("field_name", "ascending")]
    if group_by_year:
        sort_keys.extend([("year", "ascending"), ("decile", "ascending")])
    else:
        sort_keys.append(("decile", "ascending"))
    return combined.sort_by(sort_keys)


def _empty_aggregation_table(group_by_year: bool) -> pa.Table:
    """Return an empty aggregation table with the stable output schema."""
    schema_dict = {
        "field_name": pa.array([], type=pa.utf8()),
        "decile": pa.array([], type=pa.int64()),
    }
    if group_by_year:
        schema_dict["year"] = pa.array([], type=pa.int64())
    schema_dict.update(
        {
            "count": pa.array([], type=pa.int64()),
            "mean": pa.array([], type=pa.float64()),
            "median": pa.array([], type=pa.float64()),
            "sum": pa.array([], type=pa.float64()),
            "min": pa.array([], type=pa.float64()),
            "max": pa.array([], type=pa.float64()),
        }
    )
    return pa.table(schema_dict)
