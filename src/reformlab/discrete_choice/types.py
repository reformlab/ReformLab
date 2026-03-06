"""Frozen dataclasses for the discrete choice subsystem.

Provides core value types for alternatives, choice sets, cost matrices,
and expansion results. All types are immutable (frozen dataclasses).

Story 14-1: DiscreteChoiceStep with population expansion pattern.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import pyarrow as pa

if TYPE_CHECKING:
    from reformlab.computation.types import PopulationData


@dataclass(frozen=True)
class Alternative:
    """A single alternative in a decision domain.

    Attributes:
        id: Unique identifier for this alternative (e.g., "ev", "gas", "heat_pump").
        name: Human-readable name for display.
        attributes: Attribute overrides to apply when expanding population
            for this alternative (e.g., {"vehicle_type": "ev", "fuel_cost": 0.15}).
    """

    id: str
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ChoiceSet:
    """An ordered set of alternatives for a decision domain.

    Validates uniqueness of alternative IDs and non-empty set at construction.

    Attributes:
        alternatives: Tuple of alternatives in deterministic order.
    """

    alternatives: tuple[Alternative, ...]

    def __post_init__(self) -> None:
        """Validate choice set constraints."""
        from reformlab.discrete_choice.errors import ExpansionError

        if len(self.alternatives) < 1:
            raise ExpansionError(
                "Choice set must have at least 1 alternative (M >= 1)"
            )
        ids = [alt.id for alt in self.alternatives]
        if len(ids) != len(set(ids)):
            duplicates = [aid for aid in ids if ids.count(aid) > 1]
            raise ExpansionError(
                f"Duplicate alternative IDs in choice set: {sorted(set(duplicates))}"
            )

    @property
    def size(self) -> int:
        """Number of alternatives (M)."""
        return len(self.alternatives)

    @property
    def alternative_ids(self) -> tuple[str, ...]:
        """Alternative IDs in deterministic order."""
        return tuple(alt.id for alt in self.alternatives)


@dataclass(frozen=True)
class CostMatrix:
    """N×M cost matrix mapping households to alternative costs.

    Wraps a PyArrow Table with N rows (households) and M named columns
    (one per alternative). Each cell [i, j] = cost for household i
    choosing alternative j.

    Attributes:
        table: PyArrow Table with N rows and M columns named by alternative ID.
        alternative_ids: Tuple of alternative IDs matching column order.
    """

    table: pa.Table
    alternative_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate cost matrix invariants."""
        from reformlab.discrete_choice.errors import ReshapeError

        col_names = tuple(self.table.column_names)
        if col_names != self.alternative_ids:
            raise ReshapeError(
                f"CostMatrix column names {col_names} do not match "
                f"alternative_ids {self.alternative_ids}"
            )

    @property
    def n_households(self) -> int:
        """Number of households (N)."""
        return int(self.table.num_rows)

    @property
    def n_alternatives(self) -> int:
        """Number of alternatives (M)."""
        return len(self.alternative_ids)


@dataclass(frozen=True)
class ExpansionResult:
    """Result of population expansion for discrete choice evaluation.

    Contains the expanded population (N×M rows) and metadata needed
    for cost matrix reshape.

    Attributes:
        population: Expanded PopulationData with N×M rows per entity table.
        n_households: Original number of households (N).
        n_alternatives: Number of alternatives (M).
        alternative_ids: Tuple of alternative IDs in deterministic order.
    """

    population: PopulationData
    n_households: int
    n_alternatives: int
    alternative_ids: tuple[str, ...]
