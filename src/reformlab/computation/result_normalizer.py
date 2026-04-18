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
    # Story 24.2: Subsidy-family output variable mappings
    "montant_subvention": "subsidy_amount",
    "eligible_subvention": "subsidy_eligible",
    "malus_ecologique": "vehicle_malus",
    "aide_energie": "energy_poverty_aid",
}

# OpenFisca variable names to request from the live adapter.
# These are the keys of _DEFAULT_OUTPUT_MAPPING — the French variable names
# that OpenFisca-France produces and that the normalizer maps to English.
# Story 23.4: Default output variables for live OpenFisca execution.
_DEFAULT_LIVE_OUTPUT_VARIABLES: tuple[str, ...] = tuple(_DEFAULT_OUTPUT_MAPPING.keys())

# Minimum required indicator columns for normalization to succeed.
# At least one of these must be present after normalization.
# household_id is excluded because the panel builder guarantees it via fallback;
# this set validates that meaningful data columns survived the mapping.
_MINIMUM_REQUIRED_COLUMNS: frozenset[str] = frozenset({
    "income", "disposable_income", "carbon_tax",
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



def _apply_default_mapping(table: pa.Table) -> pa.Table:
    """Apply default OpenFisca-to-project mapping to a table.

    Renames columns according to _DEFAULT_OUTPUT_MAPPING.
    Columns not in the mapping are passed through unchanged.

    Args:
        table: PyArrow table to normalize.

    Returns:
        Table with renamed columns.

    Raises:
        NormalizationError: If renaming would produce duplicate column names.
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

    # Guard against duplicate column names after rename
    seen: set[str] = set()
    for name in new_names:
        if name in seen:
            conflicting_sources = [
                old for old, new in rename_map.items() if new == name
            ]
            existing_col = name
            raise NormalizationError(
                what="Output normalization failed",
                why=(
                    f"Column rename produces duplicate '{name}'. "
                    f"Sources: existing column '{existing_col}' + "
                    f"renamed column(s) {conflicting_sources}."
                ),
                fix=(
                    "Remove the conflicting column from the adapter output, "
                    "or provide a MappingConfig that resolves the collision."
                ),
            )
        seen.add(name)

    return table.rename_columns(new_names)


def normalize_computation_result(
    comp_result: ComputationResult,
    mapping_config: MappingConfig | None = None,
) -> pa.Table:
    """Normalize a ComputationResult's output_fields to app-facing schema.

    If mapping_config is provided, uses apply_output_mapping from mapping.py.
    If no mapping_config, applies _DEFAULT_OUTPUT_MAPPING.

    Story 24.3: For portfolio results (source="portfolio"), normalization is
    applied per-policy after prefixing. Each prefixed column (e.g., subsidy_0_subsidy_amount)
    has its base name normalized (e.g., subsidy_amount) and the prefix reapplied.

    Validates that at least one column from _MINIMUM_REQUIRED_COLUMNS is present.
    Does NOT add household_id — that is the panel builder's responsibility.

    Args:
        comp_result: ComputationResult to normalize.
        mapping_config: Optional explicit mapping configuration.

    Returns:
        Normalized PyArrow table.

    Raises:
        NormalizationError: If schema is incompatible (no required columns).
    """
    table = comp_result.output_fields

    # Story 24.3: Handle portfolio results with prefixed columns
    is_portfolio = comp_result.metadata.get("source") == "portfolio"

    if is_portfolio:
        # For portfolio results, normalize each prefixed column individually.
        # Prefix format (from portfolio_step._merge_policy_results):
        #   - No prefix (first policy, no duplicate types)
        #   - {policy_type}_{column_name} (non-first policy, no duplicates)
        #   - {policy_type}_{index}_{column_name} (any policy when duplicates exist)
        #
        # Policy type names may contain underscores (e.g. vehicle_malus,
        # energy_poverty_aid), so naive split("_", 2) is ambiguous.
        # We match against known policy type names (longest-first) to
        # correctly separate prefix from base column name.
        #
        # Story 24.3 code review fix: robust prefix parsing for
        # underscore-containing policy types.
        # Known policy types sorted longest-first so that multi-word
        # types (energy_poverty_aid) match before shorter prefixes.
        _KNOWN_POLICY_TYPES = [
            "energy_poverty_aid",
            "vehicle_malus",
            "carbon_tax",
            "subsidy",
            "rebate",
            "feebate",
        ]

        rename_map: dict[str, str] = {}
        for col_name in table.column_names:
            if col_name == "household_id":
                continue

            # Try to match a known policy type prefix (longest first)
            prefix = ""
            base_name = col_name
            matched = False
            for ptype in _KNOWN_POLICY_TYPES:
                if col_name.startswith(f"{ptype}_"):
                    remainder = col_name[len(ptype) + 1 :]  # skip past "{ptype}_"
                    # Check if remainder starts with a digit (index marker)
                    remainder_parts = remainder.split("_", 1)
                    if remainder_parts[0].isdigit():
                        # Format: {type}_{index}_{name}
                        prefix = f"{ptype}_{remainder_parts[0]}_"
                        base_name = remainder_parts[1] if len(remainder_parts) > 1 else ""
                    else:
                        # Format: {type}_{name} (no index)
                        prefix = f"{ptype}_"
                        base_name = remainder
                    matched = True
                    break

            if not matched:
                # No known prefix — first policy with no prefix, or
                # unrecognized column. Treat entire name as base.
                prefix = ""
                base_name = col_name

            # Apply normalization to the base column name
            if mapping_config is not None:
                from reformlab.computation.mapping import apply_output_mapping_to_name

                normalized_base = apply_output_mapping_to_name(base_name, mapping_config)
            else:
                normalized_base = _DEFAULT_OUTPUT_MAPPING.get(base_name, base_name)

            # Reapply the prefix to get the final normalized column name
            new_name = f"{prefix}{normalized_base}"
            if new_name != col_name:
                rename_map[col_name] = new_name

        if rename_map:
            new_names = [
                rename_map.get(name, name)
                for name in table.column_names
            ]

            # Guard against duplicate column names after rename
            seen: set[str] = set()
            dupes: list[str] = []
            for new_name in new_names:
                if new_name in seen:
                    dupes.append(new_name)
                seen.add(new_name)

            if dupes:
                raise NormalizationError(
                    what="Output normalization failed",
                    why=(
                        f"Renaming would produce duplicate column names: {dupes}. "
                        f"This can happen if policy outputs have conflicting base names "
                        f"that normalize to the same value."
                    ),
                    fix="Check output mapping configuration for conflicting column mappings",
                )

            table = table.rename_columns(new_names)
    elif mapping_config is not None:
        from reformlab.computation.mapping import apply_output_mapping

        table = apply_output_mapping(table, mapping_config)
    else:
        table = _apply_default_mapping(table)

    # Validate minimum required columns: at least one indicator column must
    # survive normalization for downstream compatibility.
    table_columns = set(table.column_names)
    matching_required = table_columns & _MINIMUM_REQUIRED_COLUMNS

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

    # Note: household_id column is ensured by PanelOutput.from_orchestrator_result()
    # AFTER normalization, which also handles configured_household_id_field.
    # Do NOT call _ensure_household_id_column here — doing so would bypass
    # the configured field mapping in panel.py.

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


def normalize_entity_tables(comp_result: ComputationResult) -> pa.Table:
    """Normalize multi-entity output tables to household-level.

    TODO: multi-entity merge to household-level (future story)

    First-slice stub: returns comp_result.output_fields directly.
    Multi-entity aggregation is deferred to a future story.

    Args:
        comp_result: ComputationResult with entity_tables.

    Returns:
        Currently returns output_fields directly (no aggregation yet).
    """
    # TODO: multi-entity merge to household-level (future story)
    return comp_result.output_fields
