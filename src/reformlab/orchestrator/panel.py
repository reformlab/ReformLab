"""Panel output generation from orchestrator results.

Story 3-7: Produce Scenario-Year Panel Output
Story 14-6: Extend panel with decision record columns

This module provides:
- PanelOutput: Dataclass representing a household-by-year panel dataset
- compare_panels: Helper to compare baseline and reform panels

The panel is built from yearly computation outputs stored in YearState.data
under COMPUTATION_RESULT_KEY, with each row containing household_id, year,
and computed output fields. When decision records are present in yearly states,
domain-prefixed decision columns are injected per year.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.csv as pa_csv
import pyarrow.parquet as pq

from reformlab.discrete_choice.decision_record import DECISION_LOG_KEY
from reformlab.discrete_choice.errors import DiscreteChoiceError
from reformlab.orchestrator.computation_step import COMPUTATION_RESULT_KEY
from reformlab.orchestrator.runner import SEED_LOG_KEY, STEP_EXECUTION_LOG_KEY

if TYPE_CHECKING:
    from reformlab.discrete_choice.decision_record import DecisionRecord
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
        all_domain_alternatives: dict[str, list[str]] = {}
        has_any_decision_columns = False

        # Process years in sorted order for deterministic output
        for year in sorted(result.yearly_states.keys()):
            year_state = result.yearly_states[year]

            # Extract computation result from year state
            comp_result = year_state.data.get(COMPUTATION_RESULT_KEY)
            if comp_result is None:
                continue

            output_table = comp_result.output_fields

            # Story 14-6: Decision record columns
            decision_log = year_state.data.get(DECISION_LOG_KEY)
            if isinstance(decision_log, tuple) and decision_log:
                output_table, year_domain_alts = _build_decision_columns(
                    output_table, decision_log
                )
                all_domain_alternatives.update(year_domain_alts)
                has_any_decision_columns = True

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
        elif has_any_decision_columns:
            # Use promote_options for schema flexibility when some years
            # have decision columns and others don't
            panel_table = pa.concat_tables(
                yearly_tables, promote_options="permissive"
            )
        else:
            # Concatenate all yearly tables
            panel_table = pa.concat_tables(yearly_tables)

        # Build metadata from orchestrator result
        metadata = _build_panel_metadata(result)
        if all_domain_alternatives:
            metadata["decision_domain_alternatives"] = all_domain_alternatives

        return cls(table=panel_table, metadata=metadata)

    def to_csv(self, path: str | Path) -> Path:
        """Export panel to CSV file.

        List columns (e.g., probabilities, utilities) are cast to string
        before writing since PyArrow CSV does not support list types.

        Args:
            path: Path for output CSV file.

        Returns:
            Path to the written CSV file.
        """
        path = Path(path)
        table = _cast_list_columns_to_string(self.table)
        pa_csv.write_csv(table, path)
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


def _build_decision_columns(
    output_table: pa.Table,
    decision_log: tuple[DecisionRecord, ...],
) -> tuple[pa.Table, dict[str, list[str]]]:
    """Add decision columns from the decision log to the output table.

    For each DecisionRecord, appends domain-prefixed columns for chosen
    alternative, probabilities (as list<float64>), and utilities
    (as list<float64>). Also adds a decision_domains list column.

    Args:
        output_table: Yearly output table to extend.
        decision_log: Tuple of DecisionRecords for this year.

    Returns:
        Extended table and domain→alternative_ids mapping for metadata.

    Raises:
        DiscreteChoiceError: If duplicate domain names detected.
    """
    # Validate unique domain names
    domain_names_seen = [r.domain_name for r in decision_log]
    duplicates = {n for n in domain_names_seen if domain_names_seen.count(n) > 1}
    if duplicates:
        raise DiscreteChoiceError(
            f"Duplicate domain_name(s) in decision log: {sorted(duplicates)}. "
            "Each domain must appear at most once per year."
        )

    domain_alternatives: dict[str, list[str]] = {}

    for record in decision_log:
        domain = record.domain_name
        alt_ids = record.alternative_ids
        domain_alternatives[domain] = list(alt_ids)
        n = len(record.chosen)

        # Invariant: decision record must match table row count
        if n != output_table.num_rows:
            raise DiscreteChoiceError(
                f"Domain '{domain}': chosen array length ({n}) does not match "
                f"output table row count ({output_table.num_rows}). "
                "Row counts must match for panel column injection."
            )

        # Validate column presence upfront to catch misconfigured DecisionRecord
        for table_name, tbl in [
            ("probabilities", record.probabilities),
            ("utilities", record.utilities),
        ]:
            missing = [aid for aid in alt_ids if aid not in tbl.column_names]
            if missing:
                raise DiscreteChoiceError(
                    f"Domain '{domain}': {table_name} table missing columns "
                    f"for alternative_ids {missing}. "
                    f"Available: {tbl.column_names}"
                )

        # {domain}_chosen: string column
        output_table = output_table.append_column(
            f"{domain}_chosen", record.chosen
        )

        # Vectorized extraction: convert each column to Python list once,
        # then zip rows — avoids per-cell Arrow bridge crossings (O(M) calls, not O(N*M))
        prob_col_data = [record.probabilities.column(aid).to_pylist() for aid in alt_ids]
        prob_lists: list[list[float]] = [
            [prob_col_data[j][i] for j in range(len(alt_ids))]
            for i in range(n)
        ]
        output_table = output_table.append_column(
            f"{domain}_probabilities",
            pa.array(prob_lists, type=pa.list_(pa.float64())),
        )

        util_col_data = [record.utilities.column(aid).to_pylist() for aid in alt_ids]
        util_lists: list[list[float]] = [
            [util_col_data[j][i] for j in range(len(alt_ids))]
            for i in range(n)
        ]
        output_table = output_table.append_column(
            f"{domain}_utilities",
            pa.array(util_lists, type=pa.list_(pa.float64())),
        )

    # decision_domains: list<string> column (same value for all rows)
    domain_names = [r.domain_name for r in decision_log]
    n_rows = output_table.num_rows
    output_table = output_table.append_column(
        "decision_domains",
        pa.array([domain_names] * n_rows, type=pa.list_(pa.string())),
    )

    return output_table, domain_alternatives


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


def _cast_list_columns_to_string(table: pa.Table) -> pa.Table:
    """Serialize list-typed columns to string for CSV export compatibility.

    PyArrow CSV writer does not support list types. Each list value
    is serialized as a bracket-delimited string (e.g., "[0.5, 0.3, 0.2]").
    """
    for i, field in enumerate(table.schema):
        if pa.types.is_list(field.type):
            string_values = [
                str(v) if v is not None else None
                for v in table.column(i).to_pylist()
            ]
            table = table.set_column(
                i, field.name, pa.array(string_values, type=pa.string())
            )
    return table


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
