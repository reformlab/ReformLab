# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Shared utility functions for discrete choice decision domains.

Provides common functions used by multiple decision domains (vehicle, heating):
- infer_pa_type: Infer PyArrow type from Python value
- apply_choices_to_population: Apply per-household choice results to population
- create_vintage_entries: Create vintage cohort entries from choice results

Extracted from vehicle.py per Story 14-3 authorization.
Story 14-3/14-4: Shared utilities for decision domain implementations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pyarrow as pa

from reformlab.discrete_choice.errors import DiscreteChoiceError

if TYPE_CHECKING:
    from reformlab.computation.types import PopulationData
    from reformlab.discrete_choice.types import Alternative, ChoiceResult
    from reformlab.vintage.types import VintageCohort


# ============================================================================
# Type inference helper
# ============================================================================


def infer_pa_type(value: object) -> pa.DataType:
    """Infer PyArrow type from Python value.

    Args:
        value: Python value to infer type from.

    Returns:
        PyArrow DataType.

    Raises:
        DiscreteChoiceError: If type is unsupported (bool, list, etc.).
    """
    if isinstance(value, str):
        return pa.utf8()
    if isinstance(value, bool):
        raise DiscreteChoiceError(
            f"Unsupported attribute type: {type(value).__name__} ({value!r})"
        )
    if isinstance(value, int):
        return pa.int64()
    if isinstance(value, float):
        return pa.float64()
    raise DiscreteChoiceError(
        f"Unsupported attribute type: {type(value).__name__} ({value!r})"
    )


# ============================================================================
# apply_choices_to_population
# ============================================================================


def apply_choices_to_population(
    population: PopulationData,
    choice_result: ChoiceResult,
    alternatives: tuple[Alternative, ...],
    entity_key: str,
    domain_key: str | None = None,
) -> PopulationData:
    """Apply per-household choice results to population entity table.

    Each row gets the attributes of its chosen alternative.
    Columns present in the table are replaced (preserving existing type).
    Columns absent from the table are appended with inferred type.

    Story 28.3 / AC-1: Extended to write incumbent_<domain> columns
    for multi-year technology transition tracking.

    Args:
        population: Current population data.
        choice_result: Logit choice result with chosen alternatives.
        alternatives: Tuple of all alternatives in the domain.
        entity_key: Key in population.tables to update.
        domain_key: Domain name for incumbent column (e.g., "heating", "vehicle").
            If None, skips incumbent writeback (backward compatible with legacy call sites).

    Returns:
        New PopulationData with incumbent_<domain> column written (if domain_key provided),
        otherwise unchanged population data.

    Raises:
        DiscreteChoiceError: On length mismatch or unknown alternative IDs.
    """
    from reformlab.computation.types import PopulationData as _PopulationData

    if entity_key not in population.tables:
        raise DiscreteChoiceError(
            f"Entity key '{entity_key}' not found in population tables. "
            f"Available keys: {sorted(population.tables.keys())}"
        )

    table = population.tables[entity_key]
    n = table.num_rows
    chosen_list: list[Any] = choice_result.chosen.to_pylist()

    # Validate dimensions
    if len(chosen_list) != n:
        raise DiscreteChoiceError(
            f"ChoiceResult chosen length ({len(chosen_list)}) does not match "
            f"entity table row count ({n})"
        )

    alt_map = {alt.id: alt for alt in alternatives}

    # Validate all chosen IDs are known
    unknown_ids = set(chosen_list) - set(alt_map)
    if unknown_ids:
        raise DiscreteChoiceError(
            f"Unknown alternative IDs in chosen: {sorted(str(x) for x in unknown_ids)}, "
            f"valid: {sorted(alt_map)}"
        )

    if n == 0:
        return population

    # Collect all attribute keys across all alternatives (sorted for determinism)
    all_attr_keys = sorted({k for alt in alternatives for k in alt.attributes})

    if not all_attr_keys:
        return population

    # Precompute per-household chosen alternative objects (avoids repeated map lookups)
    chosen_alts = [alt_map[cid] for cid in chosen_list]

    # Build per-column values based on each household's chosen alternative
    for attr_key in all_attr_keys:
        # Precompute existing column as Python list to avoid per-cell scalar extraction
        existing_col_list: list[Any] | None = None
        if attr_key in table.column_names:
            existing_col_list = table.column(attr_key).to_pylist()

        values: list[Any] = []
        for i in range(n):
            alt = chosen_alts[i]
            if attr_key in alt.attributes:
                values.append(alt.attributes[attr_key])
            elif existing_col_list is not None:
                values.append(existing_col_list[i])
            else:
                values.append(None)

        # Determine type
        if attr_key in table.column_names:
            col_type = table.column(attr_key).type
        else:
            # Infer from first non-None value
            first_val = next((v for v in values if v is not None), None)
            if first_val is None:
                continue
            col_type = infer_pa_type(first_val)

        try:
            new_col = pa.array(values, type=col_type)
        except (pa.ArrowInvalid, pa.ArrowTypeError) as exc:
            raise DiscreteChoiceError(
                f"Cannot cast values for '{attr_key}' to {col_type}: {exc}"
            ) from exc

        if attr_key in table.column_names:
            idx = table.column_names.index(attr_key)
            table = table.set_column(idx, attr_key, new_col)
        else:
            table = table.append_column(attr_key, new_col)

    # Story 28.3 / AC-1, AC-2, AC-3, AC-7, AC-8: Write incumbent_<domain> column
    # Only perform writeback if domain_key is provided (backward compatibility)
    if domain_key is not None:
        incumbent_col_name = f"incumbent_{domain_key}"
        n_table = table.num_rows

        # Type validation: if column exists, must be dictionary-encoded string
        if incumbent_col_name in table.column_names:
            incumbent_col = table.column(incumbent_col_name)
            if not isinstance(incumbent_col.type, pa.DictionaryType):
                raise DiscreteChoiceError(
                    f"Incumbent column '{incumbent_col_name}' has wrong type: "
                    f"{incumbent_col.type}. Expected pa.dictionary() for efficiency.",
                )
            # Validate index type is int32 (not int8, int16, uint32)
            if incumbent_col.type.index_type != pa.int32():
                raise DiscreteChoiceError(
                    f"Incumbent column '{incumbent_col_name}' has wrong dictionary index type: "
                    f"{incumbent_col.type.index_type}. Expected pa.int32().",
                )

        # Build incumbent values: skip writeback for "keep_current" to preserve actual technology
        # For AC-2: ensures year 2 sees actual technology from year 1
        # For AC-7: ensures ineligible households keep their original technology
        incumbent_values = []
        existing_incumbents = (
            table.column(incumbent_col_name).to_pylist()
            if incumbent_col_name in table.column_names
            else [None] * n_table
        )

        for i in range(n_table):
            chosen = chosen_list[i]
            if chosen == "keep_current":
                # Retain existing incumbent (don't overwrite with "keep_current" string)
                incumbent_values.append(
                    existing_incumbents[i]
                    if existing_incumbents[i] is not None
                    else "keep_current"
                )
            else:
                incumbent_values.append(chosen)

        if incumbent_col_name in table.column_names:
            # Column exists: preserve dictionary encoding (set_column path)
            existing_type = table.column(incumbent_col_name).type
            incumbent_col = pa.array(incumbent_values, type=existing_type)
            col_idx = table.column_names.index(incumbent_col_name)
            table = table.set_column(col_idx, incumbent_col_name, incumbent_col)
        else:
            # Column missing: create with dictionary encoding (append_column path)
            incumbent_col = pa.array(
                incumbent_values,
                type=pa.dictionary(pa.int32(), pa.utf8()),
            )
            table = table.append_column(incumbent_col_name, incumbent_col)

    new_tables = dict(population.tables)
    new_tables[entity_key] = table
    return _PopulationData(tables=new_tables, metadata=dict(population.metadata))


# ============================================================================
# create_vintage_entries
# ============================================================================


def create_vintage_entries(
    choice_result: ChoiceResult,
    alternatives: tuple[Alternative, ...],
    non_purchase_ids: frozenset[str],
    asset_type_key: str,
) -> tuple[VintageCohort, ...]:
    """Create vintage cohort entries for new purchases/installations.

    Parameterized version supporting multiple domains: vehicle uses
    asset_type_key="vehicle_type", heating uses asset_type_key="heating_type".

    Args:
        choice_result: Logit choice result.
        alternatives: Domain alternatives.
        non_purchase_ids: Alternative IDs excluded from vintage tracking.
        asset_type_key: Attribute key to group cohorts by (e.g., "vehicle_type").

    Returns:
        Tuple of VintageCohort entries sorted by asset type.
    """
    from reformlab.vintage.types import VintageCohort as _VintageCohort

    alt_map = {alt.id: alt for alt in alternatives}
    chosen_list: list[str] = choice_result.chosen.to_pylist()

    # Validate all chosen IDs are known alternatives
    unknown_ids = set(chosen_list) - set(alt_map)
    if unknown_ids:
        raise DiscreteChoiceError(
            f"Unknown alternative IDs in chosen: {sorted(str(x) for x in unknown_ids)}, "
            f"valid: {sorted(alt_map)}"
        )

    switcher_counts: dict[str, int] = {}
    for chosen_id in chosen_list:
        if chosen_id not in non_purchase_ids:
            alt = alt_map[chosen_id]
            asset_type = str(alt.attributes.get(asset_type_key, chosen_id))
            switcher_counts[asset_type] = switcher_counts.get(asset_type, 0) + 1

    return tuple(
        _VintageCohort(age=0, count=count, attributes={asset_type_key: asset_type})
        for asset_type, count in sorted(switcher_counts.items())
    )
