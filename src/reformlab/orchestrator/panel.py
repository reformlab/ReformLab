"""Panel output generation from orchestrator results.

Story 3-7: Produce Scenario-Year Panel Output

This module provides:
- PanelOutput: Dataclass representing a household-by-year panel dataset
- compare_panels: Helper to compare baseline and reform panels

The panel is built from yearly computation outputs stored in YearState.data
under COMPUTATION_RESULT_KEY, with each row containing household_id, year,
and computed output fields.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.csv as pa_csv
import pyarrow.parquet as pq

from reformlab.orchestrator.computation_step import COMPUTATION_RESULT_KEY
from reformlab.orchestrator.runner import SEED_LOG_KEY, STEP_EXECUTION_LOG_KEY

if TYPE_CHECKING:
    from reformlab.orchestrator.types import OrchestratorResult


# Panel format version for metadata
PANEL_VERSION = "1.0.0"


@dataclass
class PanelOutput:
    """Household-by-year panel dataset from orchestrator run.

    The panel contains one row per household per completed year, with columns
    for household_id, year, and all computed output fields from
    ComputationResult.output_fields.

    Attributes:
        table: PyArrow Table containing the panel data.
        metadata: Run metadata including start_year, end_year, seed,
            step_pipeline, seed_log, step_execution_log, and error info.
    """

    table: pa.Table
    metadata: dict[str, Any]

    @property
    def shape(self) -> tuple[int, int]:
        """Return (rows, columns) of the panel table."""
        return (self.table.num_rows, self.table.num_columns)

    @classmethod
    def from_orchestrator_result(cls, result: OrchestratorResult) -> PanelOutput:
        """Create a PanelOutput from an OrchestratorResult.

        Iterates through completed yearly states, extracts computation results,
        and concatenates them into a single panel table.

        Args:
            result: OrchestratorResult containing yearly_states with
                computation results.

        Returns:
            PanelOutput with concatenated yearly data and run metadata.
        """
        yearly_tables: list[pa.Table] = []
        schema: pa.Schema | None = None

        # Process years in sorted order for deterministic output
        for year in sorted(result.yearly_states.keys()):
            year_state = result.yearly_states[year]

            # Extract computation result from year state
            comp_result = year_state.data.get(COMPUTATION_RESULT_KEY)
            if comp_result is None:
                continue

            output_table = comp_result.output_fields

            # Capture schema from first table for empty result case
            if schema is None:
                schema = output_table.schema

            # Add year column if not present
            if "year" not in output_table.column_names:
                year_array = pa.array([year] * output_table.num_rows, type=pa.int64())
                output_table = output_table.append_column("year", year_array)

            yearly_tables.append(output_table)

        # Handle empty results (no completed years)
        if not yearly_tables:
            # Create empty table with key columns
            panel_table = pa.table(
                {
                    "household_id": pa.array([], type=pa.int64()),
                    "year": pa.array([], type=pa.int64()),
                }
            )
        else:
            # Concatenate all yearly tables
            panel_table = pa.concat_tables(yearly_tables)

        # Build metadata from orchestrator result
        metadata = _build_panel_metadata(result)

        return cls(table=panel_table, metadata=metadata)

    def to_csv(self, path: str | Path) -> Path:
        """Export panel to CSV file.

        Args:
            path: Path for output CSV file.

        Returns:
            Path to the written CSV file.
        """
        path = Path(path)
        pa_csv.write_csv(self.table, path)
        return path

    def to_parquet(self, path: str | Path) -> Path:
        """Export panel to Parquet file with schema preservation.

        The Parquet file includes panel format metadata for version tracking.

        Args:
            path: Path for output Parquet file.

        Returns:
            Path to the written Parquet file.
        """
        path = Path(path)

        # Add panel version to schema metadata
        existing_metadata = self.table.schema.metadata or {}
        new_metadata = {
            **existing_metadata,
            b"reformlab_panel_version": PANEL_VERSION.encode(),
        }
        schema_with_metadata = self.table.schema.with_metadata(new_metadata)
        table_with_metadata = self.table.cast(schema_with_metadata)

        pq.write_table(table_with_metadata, path)
        return path


def _build_panel_metadata(result: OrchestratorResult) -> dict[str, Any]:
    """Build panel metadata from orchestrator result.

    Extracts relevant metadata from result.metadata and adds
    partial/error information for failed runs.

    Args:
        result: OrchestratorResult to extract metadata from.

    Returns:
        Dictionary containing panel metadata.
    """
    metadata: dict[str, Any] = {}

    # Copy orchestrator config metadata
    for key in ("start_year", "end_year", "seed", "step_pipeline", "scenario_version"):
        if key in result.metadata:
            metadata[key] = result.metadata[key]

    # Copy Story 3-6 trace keys
    if SEED_LOG_KEY in result.metadata:
        metadata[SEED_LOG_KEY] = result.metadata[SEED_LOG_KEY]
    if STEP_EXECUTION_LOG_KEY in result.metadata:
        metadata[STEP_EXECUTION_LOG_KEY] = result.metadata[STEP_EXECUTION_LOG_KEY]

    # Mark partial completion and errors
    if not result.success or result.failed_year is not None:
        metadata["partial"] = True
        metadata["failed_year"] = result.failed_year
        metadata["failed_step"] = result.failed_step
        metadata["errors"] = result.errors
    else:
        metadata["partial"] = False

    return metadata


def compare_panels(baseline: PanelOutput, reform: PanelOutput) -> PanelOutput:
    """Compare baseline and reform panels with alignment and deltas.

    Performs an outer join on (household_id, year) to capture all combinations,
    adds origin markers and numeric delta columns for shared fields.

    Args:
        baseline: Panel from baseline run.
        reform: Panel from reform run.

    Returns:
        PanelOutput with comparison data including origin markers and deltas.
    """
    import pyarrow.compute as pc

    join_keys = ["household_id", "year"]

    # Rename non-key columns to avoid collision
    baseline_table = baseline.table
    reform_table = reform.table

    baseline_renames: dict[str, str] = {}
    reform_renames: dict[str, str] = {}

    for col in baseline_table.column_names:
        if col not in join_keys:
            baseline_renames[col] = f"_baseline_{col}"

    for col in reform_table.column_names:
        if col not in join_keys:
            reform_renames[col] = f"_reform_{col}"

    # Rename columns
    for old_name, new_name in baseline_renames.items():
        idx = baseline_table.schema.get_field_index(old_name)
        new_names = [
            new_name if i == idx else c
            for i, c in enumerate(baseline_table.column_names)
        ]
        baseline_table = baseline_table.rename_columns(new_names)

    for old_name, new_name in reform_renames.items():
        idx = reform_table.schema.get_field_index(old_name)
        new_names = [
            new_name if i == idx else c
            for i, c in enumerate(reform_table.column_names)
        ]
        reform_table = reform_table.rename_columns(new_names)

    # Use PyArrow's join with full outer join
    # PyArrow join doesn't have an indicator column, so we compute origin manually
    merged = baseline_table.join(
        reform_table,
        keys=join_keys,
        join_type="full outer",
        left_suffix="",
        right_suffix="_r",
    )

    # Determine origin by checking which values are null
    # If baseline-specific column is null -> reform_only
    # If reform-specific column is null -> baseline_only
    # If neither -> both
    baseline_indicator_col = next(
        (c for c in merged.column_names if c.startswith("_baseline_")), None
    )
    reform_indicator_col = next(
        (c for c in merged.column_names if c.startswith("_reform_")), None
    )

    if baseline_indicator_col and reform_indicator_col:
        baseline_nulls = pc.is_null(merged.column(baseline_indicator_col))
        reform_nulls = pc.is_null(merged.column(reform_indicator_col))

        # Build origin array
        origins = []
        for b_null, r_null in zip(
            baseline_nulls.to_pylist(), reform_nulls.to_pylist()
        ):
            if b_null and not r_null:
                origins.append("reform_only")
            elif r_null and not b_null:
                origins.append("baseline_only")
            else:
                origins.append("both")

        origin_array = pa.array(origins, type=pa.string())
    else:
        # Fallback: all rows are "both" if no indicator columns
        origin_array = pa.array(["both"] * merged.num_rows, type=pa.string())

    merged = merged.append_column("_origin", origin_array)

    # Calculate numeric deltas for shared numeric fields
    numeric_fields = []
    for col in baseline.table.column_names:
        if col in join_keys:
            continue
        field_type = baseline.table.schema.field(col).type
        if pa.types.is_floating(field_type) or pa.types.is_integer(field_type):
            numeric_fields.append(col)

    for field in numeric_fields:
        baseline_col = f"_baseline_{field}"
        reform_col = f"_reform_{field}"
        if baseline_col in merged.column_names and reform_col in merged.column_names:
            delta = pc.subtract(
                merged.column(reform_col),
                merged.column(baseline_col),
            )
            merged = merged.append_column(f"_delta_{field}", delta)

    # Build comparison metadata
    comparison_metadata = {
        "baseline_metadata": baseline.metadata,
        "reform_metadata": reform.metadata,
        "comparison_type": "outer_join",
        "join_keys": join_keys,
    }

    return PanelOutput(table=merged, metadata=comparison_metadata)
