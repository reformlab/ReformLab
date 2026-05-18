# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Population validation for incumbent technology columns.

Validates that incumbent technology columns in population data match
the alternatives defined in a TechnologySet. Returns warnings for
missing columns and raises errors for unknown alternative IDs.

Story 28.2 / AC-2: Validation function for incumbent technology columns.
"""

from __future__ import annotations

import logging

import pyarrow as pa

from reformlab.computation.types import PopulationData
from reformlab.discrete_choice.errors import DiscreteChoiceError
from reformlab.discrete_choice.technology_set import TechnologySet

logger = logging.getLogger(__name__)


# ============================================================================
# Module-level constants for incumbent column migration
# ============================================================================

# Story 28.2 / AC-3: Migration mapping for existing attribute columns
HEATING_TYPE_TO_INCUMBENT: dict[str, str] = {
    "gas": "condensing_boiler",      # Modern gas boiler
    "oil": "condensing_boiler",      # Fallback (oil banned in new installs)
    "electric": "heat_pump_air",     # Assumed heat pump
    "heat_pump": "heat_pump_air",    # Explicit heat pump
    "district": "district_heating",  # District heating
}

VEHICLE_TYPE_TO_INCUMBENT: dict[str, str] = {
    "petrol": "petrol",
    "diesel": "diesel",
    "hybrid": "hybrid",
    "electric": "ev",
    "plug_in_hybrid": "plug_in_hybrid",
    "none": "keep_current",  # No vehicle
}


def validate_population_for_technology_set(
    population: PopulationData,
    technology_set: TechnologySet | None,
    *,
    entity_key: str = "menage",
) -> list[str]:
    """Return a list of human-readable warnings; raise on hard schema errors.

    Validates incumbent technology columns (e.g., ``incumbent_heating``,
    ``incumbent_vehicle``) in the population data against the alternatives
    defined in the technology set.

    Story 28.2 / AC-2: Validation function for incumbent technology columns.

    Args:
        population: Population data to validate.
        technology_set: Technology set with domain alternatives. If None,
            returns empty warnings (short-circuit for disabled decisions).
        entity_key: Entity table key to validate (default: "menage").

    Returns:
        List of warning messages (empty if no warnings). Warnings are
        non-blocking — the orchestrator records them in the manifest
        but proceeds with execution.

    Raises:
        DiscreteChoiceError: If incumbent column contains unknown
            alternative IDs (fail-loud data contract violation).
    """
    warnings: list[str] = []

    # Story 28.2 / AC-8: Short-circuit if technology_set is None
    if technology_set is None:
        return warnings

    # Check each enabled domain
    for domain_name, domain_config in technology_set.domains.items():
        if not domain_config.enabled:
            continue

        incumbent_col_name = f"incumbent_{domain_name}"

        # Get entity table
        if entity_key not in population.tables:
            warnings.append(
                f"Entity key '{entity_key}' not found in population. "
                f"Cannot validate {incumbent_col_name}."
            )
            continue

        table = population.tables[entity_key]

        # Check if incumbent column exists
        if incumbent_col_name not in table.column_names:
            warnings.append(
                f"Column '{incumbent_col_name}' not found. "
                f"All households will start at reference alternative "
                f"'{domain_config.reference_alternative_id}'."
            )
            continue

        # Validate all distinct values are known alternatives
        incumbent_col = table.column(incumbent_col_name)

        # Extract unique values from dictionary or plain string column
        if isinstance(incumbent_col.type, pa.DictionaryType):
            # ChunkedArray doesn't have .dictionary directly; use combine_chunks
            combined = incumbent_col.combine_chunks()
            unique_values = set(combined.dictionary.to_pylist())
        else:
            # Fallback for non-dictionary encoding (e.g., plain utf8)
            unique_values = set(incumbent_col.unique().to_pylist())

        # Get valid alternative IDs from technology set
        valid_ids = {alt.id for alt in domain_config.alternatives}

        # Check for unknown IDs
        unknown_ids = unique_values - valid_ids
        if unknown_ids:
            raise DiscreteChoiceError(
                f"Population contains unknown incumbent technology IDs "
                f"in column '{incumbent_col_name}': {sorted(unknown_ids)}. "
                f"Valid alternatives for domain '{domain_name}': {sorted(valid_ids)}."
            )

    return warnings


# ============================================================================
# Incumbent column migration utility
# ============================================================================


def add_incumbent_columns_to_population(
    population: PopulationData,
    *,
    entity_key: str = "menage",
    heating_type_col: str = "heating_type",
    vehicle_type_col: str = "vehicle_type",
) -> PopulationData:
    """Add incumbent_heating and incumbent_vehicle columns to population.

    Story 28.2 / AC-3: Shared utility for bundled populations and data-fusion output.

    NOTE: Bundled populations (fr-synthetic-2024) do NOT have heating_type or
    vehicle_type columns. This function defaults all households to "keep_current"
    when source columns are absent.

    This function is idempotent: if incumbent columns already exist, they are
    preserved and not re-added (prevents duplicate column corruption).

    Args:
        population: Population data to modify.
        entity_key: Entity table key (default: "menage").
        heating_type_col: Source column name for heating type (if exists).
        vehicle_type_col: Source column name for vehicle type (if exists).

    Returns:
        New PopulationData with incumbent columns added. Does not
        modify the original (PopulationData is frozen).
    """
    if entity_key not in population.tables:
        logger.warning(
            "Entity key '%s' not found, skipping incumbent column migration",
            entity_key,
        )
        return population

    table = population.tables[entity_key]
    n = table.num_rows

    # Migrate heating incumbent (skip if already present — idempotent)
    if "incumbent_heating" in table.column_names:
        # Column already exists, preserve it
        pass
    elif heating_type_col in table.column_names:
        heating_types = table.column(heating_type_col).to_pylist()
        heating_incumbents = [
            HEATING_TYPE_TO_INCUMBENT.get(ht, "keep_current")
            for ht in heating_types
        ]
        heating_col = pa.array(
            heating_incumbents,
            type=pa.dictionary(pa.int32(), pa.utf8()),
        )
        table = table.append_column("incumbent_heating", heating_col)
    else:
        # No source column: default all households to keep_current
        default_col = pa.array(
            ["keep_current"] * n,
            type=pa.dictionary(pa.int32(), pa.utf8()),
        )
        table = table.append_column("incumbent_heating", default_col)

    # Migrate vehicle incumbent (skip if already present — idempotent)
    if "incumbent_vehicle" in table.column_names:
        # Column already exists, preserve it
        pass
    elif vehicle_type_col in table.column_names:
        vehicle_types = table.column(vehicle_type_col).to_pylist()
        vehicle_incumbents = [
            VEHICLE_TYPE_TO_INCUMBENT.get(vt, "keep_current")
            for vt in vehicle_types
        ]
        vehicle_col = pa.array(
            vehicle_incumbents,
            type=pa.dictionary(pa.int32(), pa.utf8()),
        )
        table = table.append_column("incumbent_vehicle", vehicle_col)
    else:
        # No source column: default all households to keep_current
        default_col = pa.array(
            ["keep_current"] * n,
            type=pa.dictionary(pa.int32(), pa.utf8()),
        )
        table = table.append_column("incumbent_vehicle", default_col)

    new_tables = dict(population.tables)
    new_tables[entity_key] = table

    return PopulationData(
        tables=new_tables,
        metadata=dict(population.metadata),
    )


__all__ = [
    "HEATING_TYPE_TO_INCUMBENT",
    "VEHICLE_TYPE_TO_INCUMBENT",
    "validate_population_for_technology_set",
    "add_incumbent_columns_to_population",
]
