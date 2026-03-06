"""Population expansion logic for discrete choice evaluation.

Expands a population of N households by M alternatives, creating N×M
virtual households with alternative-specific attribute overrides and
tracking columns for deterministic reshape.

Story 14-1: DiscreteChoiceStep with population expansion pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pyarrow as pa

from reformlab.computation.types import PopulationData
from reformlab.discrete_choice.errors import ExpansionError
from reformlab.discrete_choice.types import ChoiceSet, ExpansionResult

if TYPE_CHECKING:
    from reformlab.discrete_choice.domain import DecisionDomain


# Tracking column names added to expanded entity tables
TRACKING_COL_ALTERNATIVE_ID = "_alternative_id"
TRACKING_COL_ORIGINAL_INDEX = "_original_household_index"


def expand_population(
    population: PopulationData,
    choice_set: ChoiceSet,
    domain: DecisionDomain,
) -> ExpansionResult:
    """Expand population by alternatives for discrete choice evaluation.

    For each entity table in the population, creates M copies of each row
    (one per alternative), applies alternative-specific attribute overrides,
    and adds tracking columns for deterministic reshape.

    Args:
        population: Original population with N households.
        choice_set: Validated set of M alternatives (M >= 1).
        domain: Decision domain providing attribute override logic.

    Returns:
        ExpansionResult with expanded N×M population and metadata.

    Raises:
        ExpansionError: If expansion logic fails.
    """
    m = choice_set.size
    alternatives = choice_set.alternatives

    expanded_tables: dict[str, pa.Table] = {}

    for entity_key, table in sorted(population.tables.items()):
        n = table.num_rows

        if n == 0:
            # Empty table: add tracking columns with correct types, 0 rows
            expanded = table.append_column(
                TRACKING_COL_ALTERNATIVE_ID,
                pa.array([], type=pa.int32()),
            ).append_column(
                TRACKING_COL_ORIGINAL_INDEX,
                pa.array([], type=pa.int32()),
            )
            expanded_tables[entity_key] = expanded
            continue

        # Build M segments, one per alternative
        segments: list[pa.Table] = []
        for alt_idx, alternative in enumerate(alternatives):
            # Apply attribute overrides for this alternative
            try:
                modified = domain.apply_alternative(table, alternative)
            except Exception as exc:
                raise ExpansionError(
                    f"Failed to apply alternative '{alternative.id}' "
                    f"to entity '{entity_key}': {exc}",
                    domain_name=domain.name,
                    original_error=exc if isinstance(exc, Exception) else None,
                ) from exc

            # Add tracking columns
            alt_id_col = pa.array([alt_idx] * n, type=pa.int32())
            orig_idx_col = pa.array(list(range(n)), type=pa.int32())

            modified = modified.append_column(
                TRACKING_COL_ALTERNATIVE_ID, alt_id_col
            )
            modified = modified.append_column(
                TRACKING_COL_ORIGINAL_INDEX, orig_idx_col
            )
            segments.append(modified)

        # Concatenate all segments into one expanded table
        expanded_tables[entity_key] = pa.concat_tables(segments)

    # Determine N from the first entity table (or 0 if no tables)
    n_households = 0
    if population.tables:
        first_key = sorted(population.tables.keys())[0]
        n_households = population.tables[first_key].num_rows

    expanded_population = PopulationData(
        tables=expanded_tables,
        metadata={
            **population.metadata,
            "expansion_n": n_households,
            "expansion_m": m,
        },
    )

    return ExpansionResult(
        population=expanded_population,
        n_households=n_households,
        n_alternatives=m,
        alternative_ids=choice_set.alternative_ids,
    )
