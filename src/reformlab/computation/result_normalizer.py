# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Result normalization from OpenFisca output to app-facing schema.

Story 23.3: Normalize live OpenFisca results into the stable app-facing output schema

This module provides:
- NormalizationError: Structured error for normalization failures
- normalize_computation_result: Renames OpenFisca variables to project schema names
- create_live_normalizer: Factory returning a normalizer callable
- normalize_entity_tables: Stub for multi-entity aggregation (future story)

The normalization boundary is at ComputationResult → PanelOutput, mapping French
variable names (e.g., revenu_disponible) to English schema names (e.g., disposable_income).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import pyarrow as pa

from reformlab.computation.types import ComputationResult

if TYPE_CHECKING:
    from reformlab.computation.mapping import MappingConfig


# ============================================================================
# Metadata key constants
# ============================================================================

NORMALIZED_KEY: str = "normalized"
MAPPING_APPLIED_KEY: str = "mapping_applied"


# ============================================================================
# Default output mapping from OpenFisca to project schema
# ============================================================================

# Mapping from common OpenFisca-France variable names to project schema names.
# Used as fallback when no MappingConfig YAML file is provided.
# Only output-direction mappings are included.
#
# Mapping precedence: explicit run config MappingConfig > _DEFAULT_OUTPUT_MAPPING
_DEFAULT_OUTPUT_MAPPING: dict[str, str] = {
    "revenu_disponible": "disposable_income",
    "irpp": "income_tax",
    "impots_directs": "direct_taxes",
    "revenu_net": "net_income",
    "salaire_net": "income",
    "revenu_brut": "gross_income",
    "prestations_sociales": "social_benefits",
    "taxe_carbone": "carbon_tax",
}

# Minimum required columns for normalization to succeed.
# At least one of these must be present after normalization.
_MINIMUM_REQUIRED_COLUMNS: frozenset[str] = frozenset({
    "household_id", "income", "disposable_income", "carbon_tax",
})


# ============================================================================
# Error types
# ============================================================================


class NormalizationError(Exception):
    """Structured normalization error following project error pattern.

    Attributes:
        what: High-level description of what failed.
        why: Detailed reason for the failure.
        fix: Actionable guidance to resolve the issue.
    """

    def __init__(self, *, what: str, why: str, fix: str) -> None:
        self.what = what
        self.why = why
        self.fix = fix
        message = f"{what} — {why} — {fix}"
        super().__init__(message)


# ============================================================================
# Normalization functions
# ============================================================================


def _ensure_household_id_column(table: pa.Table) -> pa.Table:
    """Ensure table has a stable household_id column for panel joins.

    This is a local copy of the function from panel.py to avoid circular imports.
    The implementation is identical to maintain consistency.

    Args:
        table: PyArrow table to ensure household_id in.

    Returns:
        Table with household_id column added if needed.
    """
    if "household_id" in table.column_names:
        return table

    if "person_id" in table.column_names:
        return table.append_column("household_id", table.column("person_id"))

    # Fallback: create deterministic row index
    fallback_ids = pa.array(range(table.num_rows), type=pa.int64())
    return table.append_column("household_id", fallback_ids)


def _apply_default_mapping(table: pa.Table) -> pa.Table:
    """Apply default OpenFisca-to-project mapping to a table.

    Renames columns according to _DEFAULT_OUTPUT_MAPPING.
    Columns not in the mapping are passed through unchanged.

    Args:
        table: PyArrow table to normalize.

    Returns:
        Table with renamed columns.
    """
    rename_map: dict[str, str] = {}
    for col_name in table.column_names:
        new_name = _DEFAULT_OUTPUT_MAPPING.get(col_name, col_name)
        if new_name != col_name:
            rename_map[col_name] = new_name

    if not rename_map:
        return table

    new_names = [
        rename_map.get(name, name)
        for name in table.column_names
    ]
    return table.rename_columns(new_names)


def normalize_computation_result(
    comp_result: ComputationResult,
    mapping_config: MappingConfig | None = None,
) -> pa.Table:
    """Normalize a ComputationResult's output_fields to app-facing schema.

    If mapping_config is provided, uses apply_output_mapping from mapping.py.
    If no mapping_config, applies _DEFAULT_OUTPUT_MAPPING.

    Ensures household_id column exists. Validates that at least one column
    from _MINIMUM_REQUIRED_COLUMNS (excluding household_id fallback) is present.

    Args:
        comp_result: ComputationResult to normalize.
        mapping_config: Optional explicit mapping configuration.

    Returns:
        Normalized PyArrow table.

    Raises:
        NormalizationError: If schema is incompatible (no required columns).
    """
    table = comp_result.output_fields

    # Apply mapping
    if mapping_config is not None:
        from reformlab.computation.mapping import apply_output_mapping

        table = apply_output_mapping(table, mapping_config)
    else:
        table = _apply_default_mapping(table)

    # Validate minimum required columns BEFORE adding household_id fallback
    # We check for meaningful data columns (income, disposable_income, carbon_tax)
    # not just household_id, which might be added as a fallback.
    table_columns = set(table.column_names)
    # Exclude household_id from validation if it would be added as fallback
    meaningful_required = _MINIMUM_REQUIRED_COLUMNS - {"household_id"}
    matching_required = table_columns & meaningful_required

    if not matching_required:
        available = sorted(table_columns)
        expected = sorted(list(_MINIMUM_REQUIRED_COLUMNS))
        raise NormalizationError(
            what="Output normalization failed",
            why=(
                f"Live OpenFisca result has no recognizable output columns. "
                f"Available: [{', '.join(available)}]. "
                f"Expected at least one of: [{', '.join(expected)}]."
            ),
            fix=(
                "Provide a MappingConfig YAML file that maps OpenFisca variable "
                "names to project schema fields, or verify that the adapter's "
                "output_variables configuration includes the expected variables."
            ),
        )

    # Ensure household_id column exists (after validation)
    table = _ensure_household_id_column(table)

    return table


def create_live_normalizer(
    mapping_config: MappingConfig | None = None,
) -> Callable[[ComputationResult], pa.Table]:
    """Factory that returns a normalizer callable.

    The returned callable wraps normalize_computation_result() and is designed
    to be passed to PanelOutput.from_orchestrator_result() as the normalizer
    parameter.

    Args:
        mapping_config: Optional explicit mapping configuration.

    Returns:
        A callable that accepts ComputationResult and returns normalized pa.Table.
    """
    def _normalizer(comp_result: ComputationResult) -> pa.Table:
        return normalize_computation_result(comp_result, mapping_config)

    return _normalizer


def normalize_entity_tables(
    comp_result: ComputationResult,
    mapping_config: MappingConfig | None = None,
) -> pa.Table:
    """Normalize multi-entity output tables to household-level.

    TODO: multi-entity merge to household-level (future story)

    First-slice stub: returns comp_result.output_fields directly.
    Multi-entity aggregation is deferred to a future story.

    Args:
        comp_result: ComputationResult with entity_tables.
        mapping_config: Optional explicit mapping configuration.

    Returns:
        Currently returns output_fields directly (no aggregation yet).
    """
    # TODO: multi-entity merge to household-level (future story)
    return comp_result.output_fields
