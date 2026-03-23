# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Scenario comparison module for ReformLab.

Story 4.5: Implement Scenario Comparison Tables

This module provides functions to compare indicator results from multiple
scenarios side-by-side, compute deltas, and export comparison tables in
CSV and Parquet formats.

Main API:
    - compare_scenarios: Compare indicator results from multiple scenarios
    - ComparisonConfig: Configuration for comparison operations
    - ComparisonResult: Container for comparison results with export methods
    - ScenarioInput: Wrapper for scenario label and indicator results
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as csv
import pyarrow.parquet as pq

from reformlab.indicators.types import IndicatorResult

_NULL_STRING_SENTINEL = "__reformlab_null_join_key__"


@dataclass
class ScenarioInput:
    """Wrapper for scenario label and indicator results.

    Associates an IndicatorResult with a human-readable scenario label for
    comparison operations.

    Attributes:
        label: Scenario label (e.g., "baseline", "reform_a", "reform_b").
        indicators: Computed indicator results for this scenario.
    """

    label: str
    indicators: IndicatorResult


@dataclass
class ComparisonConfig:
    """Configuration for scenario comparison operations.

    Attributes:
        baseline_label: Label of the baseline scenario for delta computation.
            If None, the first scenario in the input list is used as baseline.
            Defaults to None.
        include_deltas: If True, compute absolute delta columns
            (delta_scenario = scenario - baseline). Defaults to True.
        include_pct_deltas: If True, compute percentage delta columns
            (pct_delta_scenario = delta / baseline * 100). Defaults to True.
    """

    baseline_label: str | None = None
    include_deltas: bool = True
    include_pct_deltas: bool = True


@dataclass
class ComparisonResult:
    """Container for scenario comparison results.

    Holds the comparison table with side-by-side scenario values, optional
    delta columns, metadata, and warnings.

    Attributes:
        table: PyArrow table with comparison results. Column schema varies by
            indicator type but always includes: field_name, grouping dimension(s),
            year, metric, and one value column per scenario.
        metadata: Dictionary containing scenario labels, indicator types, config,
            and other comparison metadata.
        warnings: List of warning messages emitted during comparison (e.g.,
            mismatched dimensions, missing values).
    """

    table: pa.Table
    metadata: dict[str, Any]
    warnings: list[str] = field(default_factory=list)

    def to_table(self) -> pa.Table:
        """Return the comparison table as a PyArrow Table.

        Returns:
            PyArrow table with stable column schema.
        """
        return self.table

    def export_csv(self, path: str | Path) -> Path:
        """Export comparison table to CSV file.

        Args:
            path: Destination file path.

        Returns:
            Path to the written CSV file.
        """
        path = Path(path)
        csv.write_csv(self.table, str(path))
        return path

    def export_parquet(self, path: str | Path) -> Path:
        """Export comparison table to Parquet file.

        Args:
            path: Destination file path.

        Returns:
            Path to the written Parquet file.
        """
        path = Path(path)
        pq.write_table(self.table, str(path))
        return path


def _detect_indicator_schema(result: IndicatorResult) -> str:
    """Detect the indicator schema type from an IndicatorResult.

    Args:
        result: IndicatorResult to inspect.

    Returns:
        Schema identifier: "decile", "region", "fiscal".

    Raises:
        ValueError: If schema cannot be determined.
    """
    if "revenue_fields" in result.metadata or "cost_fields" in result.metadata:
        return "fiscal"
    if "welfare_field" in result.metadata:
        group_type = result.metadata.get("group_type", "decile")
        if group_type == "region":
            return "region"
        return "decile"
    if "region_field" in result.metadata:
        return "region"
    # Default to decile for distributional indicators
    return "decile"


def _resolve_join_keys(schema: str) -> list[str]:
    """Resolve join keys for a given indicator schema.

    Args:
        schema: Schema identifier ("decile", "region", "fiscal").

    Returns:
        List of column names to use as join keys.
    """
    if schema == "fiscal":
        return ["field_name", "year", "metric"]
    if schema == "region":
        return ["field_name", "region", "year", "metric"]
    # "decile" schema
    return ["field_name", "decile", "year", "metric"]


def _join_key_sentinel(field_type: pa.DataType) -> pa.Scalar:
    """Return a type-compatible sentinel used to align null join keys."""
    if pa.types.is_signed_integer(field_type):
        min_value = -(1 << (field_type.bit_width - 1))
        return pa.scalar(min_value, type=field_type)
    if pa.types.is_unsigned_integer(field_type):
        max_value = (1 << field_type.bit_width) - 1
        return pa.scalar(max_value, type=field_type)
    if pa.types.is_string(field_type) or pa.types.is_large_string(field_type):
        return pa.scalar(_NULL_STRING_SENTINEL, type=field_type)
    msg = f"Join keys must be integer or string columns. Unsupported type: {field_type}"
    raise ValueError(msg)


def _prepare_scenario_table(
    scenario: ScenarioInput,
    join_keys: list[str],
) -> pa.Table:
    """Convert indicator result to join-ready table with scenario value column."""
    table = scenario.indicators.to_table()
    if "value" not in table.column_names:
        msg = (
            f"Scenario '{scenario.label}' table is missing required 'value' column. "
            "Expected IndicatorResult.to_table() contract."
        )
        raise ValueError(msg)

    missing_keys = [key for key in join_keys if key not in table.column_names]
    if missing_keys:
        msg = (
            f"Scenario '{scenario.label}' is missing required join key columns: {missing_keys}. "
            f"Available columns: {table.column_names}"
        )
        raise ValueError(msg)

    renamed = table.rename_columns(
        [scenario.label if col == "value" else col for col in table.column_names]
    )
    return renamed.select(join_keys + [scenario.label])


def _fill_null_join_keys(
    table: pa.Table,
    join_keys: list[str],
) -> pa.Table:
    """Replace null join key values with deterministic sentinels for joining."""
    result = table
    for key in join_keys:
        field = result.schema.field(key)
        sentinel = _join_key_sentinel(field.type)
        # Guard against sentinel collisions with actual values.
        has_collision = pc.any(pc.equal(result[key], sentinel)).as_py()
        if bool(has_collision):
            msg = (
                f"Join key column '{key}' already contains reserved sentinel value "
                f"{sentinel.as_py()!r}. Cannot safely align null join keys."
            )
            raise ValueError(msg)
        filled = pc.fill_null(result[key], sentinel)
        result = result.set_column(
            result.schema.get_field_index(key),
            key,
            filled,
        )
    return result


def _restore_null_join_keys(
    table: pa.Table,
    join_keys: list[str],
) -> pa.Table:
    """Restore sentinel values in join keys back to null after joins."""
    result = table
    for key in join_keys:
        field = result.schema.field(key)
        sentinel = _join_key_sentinel(field.type)
        is_sentinel = pc.equal(result[key], sentinel)
        restored = pc.if_else(
            is_sentinel, pa.scalar(None, type=field.type), result[key]
        )
        result = result.set_column(
            result.schema.get_field_index(key),
            key,
            restored,
        )
    return result


def _format_key_samples(
    table: pa.Table,
    join_keys: list[str],
    limit: int = 3,
) -> str:
    """Format up to ``limit`` missing key combinations for warning messages."""
    if table.num_rows == 0:
        return "none"

    key_table = table.select(join_keys).slice(0, limit)
    rows = key_table.to_pylist()
    samples: list[str] = []
    for row in rows:
        parts = [f"{key}={row.get(key)!r}" for key in join_keys]
        samples.append("{" + ", ".join(parts) + "}")
    return ", ".join(samples)


def _align_indicator_tables(
    scenarios: list[ScenarioInput],
    join_keys: list[str],
    warnings: list[str],
) -> pa.Table:
    """Align indicator tables from multiple scenarios into a side-by-side table.

    Performs outer joins on common dimensions (join_keys), renames value columns
    by scenario label, and handles non-overlapping grouping key values with nulls.

    Args:
        scenarios: List of scenario inputs with labels and indicator results.
        join_keys: Column names to use as join keys.
        warnings: Mutable list to collect warning messages.

    Returns:
        PyArrow table with side-by-side scenario columns.
    """
    if not scenarios:
        msg = "No scenarios provided for alignment"
        raise ValueError(msg)

    tables = [
        _fill_null_join_keys(_prepare_scenario_table(scenario, join_keys), join_keys)
        for scenario in scenarios
    ]

    # Start with the first table.
    result = tables[0]

    # Progressively join remaining tables.
    for scenario, table in zip(scenarios[1:], tables[1:], strict=True):
        existing_keys = result.select(join_keys)
        new_keys = table.select(join_keys)

        missing_in_new = existing_keys.join(
            new_keys,
            keys=join_keys,
            join_type="left anti",
        )
        missing_in_existing = new_keys.join(
            existing_keys,
            keys=join_keys,
            join_type="left anti",
        )

        if missing_in_new.num_rows > 0 or missing_in_existing.num_rows > 0:
            warnings.append(
                f"Scenario '{scenario.label}' has non-overlapping comparison keys: "
                f"{missing_in_new.num_rows} key(s) missing in '{scenario.label}' "
                f"(sample: {_format_key_samples(missing_in_new, join_keys)}); "
                f"{missing_in_existing.num_rows} key(s) only in '{scenario.label}' "
                f"(sample: {_format_key_samples(missing_in_existing, join_keys)}). "
                "Rows for these keys will contain null values in scenario columns."
            )

        # Perform outer join on all join keys.
        result = result.join(
            table,
            keys=join_keys,
            join_type="full outer",
        )

    return _restore_null_join_keys(result, join_keys)


def _compute_deltas(
    table: pa.Table,
    baseline_label: str,
    scenario_labels: list[str],
    config: ComparisonConfig,
) -> pa.Table:
    """Compute delta columns (absolute and percentage) relative to baseline.

    Args:
        table: Side-by-side comparison table with scenario value columns.
        baseline_label: Label of the baseline scenario column.
        scenario_labels: List of all scenario labels (excluding baseline).
        config: Comparison configuration.

    Returns:
        PyArrow table with added delta columns.
    """
    if baseline_label not in table.column_names:
        # No baseline column, cannot compute deltas
        return table

    baseline_col = table[baseline_label]
    new_columns = {name: table[name] for name in table.column_names}

    for label in scenario_labels:
        if label == baseline_label or label not in table.column_names:
            continue

        scenario_col = table[label]

        # Compute absolute delta
        if config.include_deltas:
            delta_col = pc.subtract(scenario_col, baseline_col)
            new_columns[f"delta_{label}"] = delta_col

        # Compute percentage delta (guard against division by zero)
        if config.include_pct_deltas:
            is_zero = pc.equal(baseline_col, 0.0)
            delta = pc.subtract(scenario_col, baseline_col)
            pct_delta = pc.if_else(
                is_zero,
                pa.scalar(None, type=pa.float64()),
                pc.multiply(pc.divide(delta, baseline_col), 100.0),
            )
            new_columns[f"pct_delta_{label}"] = pct_delta

    # Reconstruct table with new columns in logical order:
    # join_keys, scenario values, delta columns, pct_delta columns
    join_key_cols = [
        name
        for name in table.column_names
        if name not in [baseline_label] + scenario_labels
    ]
    scenario_value_cols = [baseline_label] + [
        label for label in scenario_labels if label in table.column_names
    ]
    delta_cols = [
        f"delta_{label}" for label in scenario_labels if f"delta_{label}" in new_columns
    ]
    pct_delta_cols = [
        f"pct_delta_{label}"
        for label in scenario_labels
        if f"pct_delta_{label}" in new_columns
    ]

    ordered_cols = join_key_cols + scenario_value_cols + delta_cols + pct_delta_cols
    return pa.table({col: new_columns[col] for col in ordered_cols})


def compare_scenarios(
    scenarios: list[ScenarioInput],
    config: ComparisonConfig | None = None,
) -> ComparisonResult:
    """Compare indicator results from multiple scenarios side-by-side.

    Produces a side-by-side comparison table with one value column per scenario,
    optional delta columns, and metadata for governance.

    Args:
        scenarios: List of ScenarioInput objects with labels and indicator results.
            Must contain at least 2 scenarios.
        config: Comparison configuration. If None, uses default configuration.

    Returns:
        ComparisonResult with comparison table, metadata, and warnings.

    Raises:
        ValueError: If input validation fails (fewer than 2 scenarios, duplicate
            labels, mixed indicator schemas, or empty indicator results).
    """
    if config is None:
        config = ComparisonConfig()

    warnings: list[str] = []

    # Validate minimum scenario count
    if len(scenarios) < 2:
        msg = (
            f"Comparison requires at least 2 scenarios, got {len(scenarios)}. "
            f"Provide at least two ScenarioInput objects."
        )
        raise ValueError(msg)

    # Validate unique scenario labels
    labels = [s.label for s in scenarios]
    if any(not label.strip() for label in labels):
        msg = "Scenario labels must be non-empty strings."
        raise ValueError(msg)
    if len(labels) != len(set(labels)):
        duplicate_labels = [label for label in set(labels) if labels.count(label) > 1]
        msg = (
            f"Duplicate scenario labels detected: {duplicate_labels}. "
            f"Each scenario must have a unique label."
        )
        raise ValueError(msg)

    # Detect indicator schemas for all scenarios
    schemas = [_detect_indicator_schema(s.indicators) for s in scenarios]

    # Validate compatible schemas (all must be the same)
    if len(set(schemas)) > 1:
        schema_map = {
            s.label: schema for s, schema in zip(scenarios, schemas, strict=True)
        }
        msg = (
            f"Mixed indicator schemas detected across scenarios: {schema_map}. "
            f"All scenarios must use the same indicator schema (all decile, all region, or all fiscal). "
            f"Comparison across different indicator types (e.g., decile + region) is not supported."
        )
        raise ValueError(msg)

    schema = schemas[0]
    join_keys = _resolve_join_keys(schema)

    reserved_labels = set(join_keys) | {"value"}
    invalid_labels = [label for label in labels if label in reserved_labels]
    if invalid_labels:
        msg = (
            f"Invalid scenario labels: {invalid_labels}. "
            f"Scenario labels cannot match reserved table columns: {sorted(reserved_labels)}."
        )
        raise ValueError(msg)
    prefix_conflicts = [
        label
        for label in labels
        if label.startswith("delta_") or label.startswith("pct_delta_")
    ]
    if prefix_conflicts:
        msg = (
            f"Invalid scenario labels: {prefix_conflicts}. "
            "Scenario labels cannot start with 'delta_' or 'pct_delta_' because "
            "these prefixes are reserved for computed columns."
        )
        raise ValueError(msg)

    # Resolve baseline label (first scenario if not specified)
    baseline_label = config.baseline_label or labels[0]
    if baseline_label not in labels:
        msg = (
            f"Baseline label '{baseline_label}' not found in scenario labels: {labels}. "
            f"Ensure the baseline_label matches one of the provided scenario labels."
        )
        raise ValueError(msg)

    if all(len(s.indicators.indicators) == 0 for s in scenarios):
        warnings.append(
            "All scenarios have empty indicator results. Returning empty comparison table."
        )

    # Align indicator tables into side-by-side format
    comparison_table = _align_indicator_tables(scenarios, join_keys, warnings)

    # Compute delta columns if requested
    if config.include_deltas or config.include_pct_deltas:
        comparison_table = _compute_deltas(
            comparison_table,
            baseline_label,
            labels,
            config,
        )
    if comparison_table.num_rows > 0:
        comparison_table = comparison_table.sort_by(
            [(key, "ascending") for key in join_keys]
        )

    delta_columns = {
        label: f"delta_{label}"
        for label in labels
        if label != baseline_label and config.include_deltas
    }
    pct_delta_columns = {
        label: f"pct_delta_{label}"
        for label in labels
        if label != baseline_label and config.include_pct_deltas
    }

    # Build metadata
    metadata = {
        "scenario_labels": labels,
        "baseline_label": baseline_label,
        "indicator_schema": schema,
        "join_keys": join_keys,
        "config": {
            "baseline_label": config.baseline_label,
            "include_deltas": config.include_deltas,
            "include_pct_deltas": config.include_pct_deltas,
        },
        "field_mappings": {
            "join_keys": join_keys,
            "scenario_value_columns": {label: label for label in labels},
            "delta_columns": delta_columns,
            "pct_delta_columns": pct_delta_columns,
        },
        "source_metadata": [s.indicators.metadata for s in scenarios],
    }

    return ComparisonResult(
        table=comparison_table,
        metadata=metadata,
        warnings=warnings,
    )
