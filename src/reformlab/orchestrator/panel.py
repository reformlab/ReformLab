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
        configured_household_id_field = _household_id_field_from_metadata(
            result.metadata
        )

        # Process years in sorted order for deterministic output
        for year in sorted(result.yearly_states.keys()):
            year_state = result.yearly_states[year]

            # Extract computation result from year state
            comp_result = year_state.data.get(COMPUTATION_RESULT_KEY)
            if comp_result is None:
                continue

            output_table = comp_result.output_fields
            output_table = _ensure_household_id_column(
                output_table,
                configured_household_id_field,
            )
            output_table = _set_year_column(output_table, year)

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

    def to_parquet(
        self,
        path: str | Path,
        schema_metadata: dict[str, str | bytes] | None = None,
    ) -> Path:
        """Export panel to Parquet file with schema preservation.

        The Parquet file includes panel format metadata for version tracking.
        Additional metadata can be attached for provenance traceability.

        Args:
            path: Path for output Parquet file.
            schema_metadata: Optional key/value metadata to merge into the
                written Parquet schema metadata.

        Returns:
            Path to the written Parquet file.
        """
        path = Path(path)

        # Add panel version to schema metadata, preserving existing keys.
        existing_metadata = dict(self.table.schema.metadata or {})
        new_metadata: dict[bytes, bytes] = {
            **existing_metadata,
            b"reformlab_panel_version": PANEL_VERSION.encode(),
        }

        if schema_metadata:
            for key, value in schema_metadata.items():
                key_bytes = key if isinstance(key, bytes) else str(key).encode()
                value_bytes = (
                    value if isinstance(value, bytes) else str(value).encode()
                )
                new_metadata[key_bytes] = value_bytes

        table_with_metadata = self.table.replace_schema_metadata(new_metadata)

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


def _household_id_field_from_metadata(metadata: dict[str, Any]) -> str | None:
    """Read optional configured household id field from run metadata."""
    field_name = metadata.get("household_id_field")
    if field_name is None:
        return None
    if not isinstance(field_name, str) or not field_name:
        raise TypeError(
            "metadata['household_id_field'] must be a non-empty string when provided"
        )
    return field_name


def _ensure_household_id_column(
    table: pa.Table, configured_field: str | None
) -> pa.Table:
    """Ensure table has a stable household_id column for panel joins."""
    if "household_id" in table.column_names:
        return table

    if configured_field is not None:
        if configured_field not in table.column_names:
            raise ValueError(
                "Configured household id field was not found in output_fields: "
                f"{configured_field!r}"
            )
        return table.append_column("household_id", table.column(configured_field))

    if "person_id" in table.column_names:
        return table.append_column("household_id", table.column("person_id"))

    # Fallback: create deterministic row index for downstream panel shape guarantees.
    fallback_ids = pa.array(range(table.num_rows), type=pa.int64())
    return table.append_column("household_id", fallback_ids)


def _set_year_column(table: pa.Table, year: int) -> pa.Table:
    """Set the panel year column to the orchestrator year."""
    year_array = pa.array([year] * table.num_rows, type=pa.int64())
    if "year" in table.column_names:
        year_idx = table.schema.get_field_index("year")
        return table.set_column(year_idx, "year", year_array)
    return table.append_column("year", year_array)


def _ensure_join_keys_present(
    table: pa.Table, table_name: str, join_keys: list[str]
) -> None:
    """Validate required join keys exist in the panel table."""
    missing = [key for key in join_keys if key not in table.column_names]
    if missing:
        missing_str = ", ".join(missing)
        raise ValueError(
            f"{table_name} panel missing required join key columns: {missing_str}"
        )


def _resolve_unique_marker(base_name: str, existing_columns: set[str]) -> str:
    """Return a marker column name that does not collide with real data columns."""
    marker = base_name
    suffix = 1
    while marker in existing_columns:
        marker = f"{base_name}_{suffix}"
        suffix += 1
    existing_columns.add(marker)
    return marker


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
    _ensure_join_keys_present(baseline.table, "baseline", join_keys)
    _ensure_join_keys_present(reform.table, "reform", join_keys)

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
            new_name if i == idx else c for i, c in enumerate(reform_table.column_names)
        ]
        reform_table = reform_table.rename_columns(new_names)

    marker_pool = set(baseline_table.column_names) | set(reform_table.column_names)
    baseline_marker = _resolve_unique_marker("_baseline_present", marker_pool)
    reform_marker = _resolve_unique_marker("_reform_present", marker_pool)
    baseline_table = baseline_table.append_column(
        baseline_marker,
        pa.array([True] * baseline_table.num_rows, type=pa.bool_()),
    )
    reform_table = reform_table.append_column(
        reform_marker,
        pa.array([True] * reform_table.num_rows, type=pa.bool_()),
    )

    # Use PyArrow's join with full outer join
    # PyArrow join doesn't have an indicator column, so we compute origin manually
    merged = baseline_table.join(
        reform_table,
        keys=join_keys,
        join_type="full outer",
        left_suffix="",
        right_suffix="_r",
    )

    # Determine origin from explicit side markers (robust to null data values).
    baseline_missing = pc.is_null(merged.column(baseline_marker))
    reform_missing = pc.is_null(merged.column(reform_marker))
    origin_array = pc.if_else(
        pc.and_(baseline_missing, pc.invert(reform_missing)),
        pa.scalar("reform_only"),
        pc.if_else(
            pc.and_(reform_missing, pc.invert(baseline_missing)),
            pa.scalar("baseline_only"),
            pa.scalar("both"),
        ),
    )

    merged = merged.append_column("_origin", origin_array)
    merged = merged.drop_columns([baseline_marker, reform_marker])

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
