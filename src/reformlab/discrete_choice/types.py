# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Frozen dataclasses for the discrete choice subsystem.

Provides core value types for alternatives, choice sets, cost matrices,
expansion results, taste parameters, and choice results. All types are
immutable (frozen dataclasses).

Story 14-1: DiscreteChoiceStep with population expansion pattern.
Story 14-2: Conditional logit model types (TasteParameters, ChoiceResult).
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


# ============================================================================
# Story 14-2: Logit model types
# ============================================================================


@dataclass(frozen=True)
class TasteParameters:
    """Taste parameters for the conditional logit model.

    Single β coefficient applied to the cost matrix to compute
    deterministic utilities: V_ij = beta_cost × cost_ij.

    Attributes:
        beta_cost: Coefficient for cost in utility function.
    """

    beta_cost: float


@dataclass(frozen=True)
class ChoiceResult:
    """Result of logit choice model: probabilities and drawn choices.

    Contains chosen alternatives, probability and utility matrices,
    and the seed used for draws. Validates probability normalization,
    column consistency, and chosen array length at construction.

    Attributes:
        chosen: PyArrow Array of string alternative IDs (length N).
        probabilities: N×M PyArrow Table of choice probabilities.
        utilities: N×M PyArrow Table of deterministic utilities.
        alternative_ids: Tuple of alternative IDs matching column order.
        seed: Random seed used for draws (None if unseeded).
    """

    chosen: pa.Array
    probabilities: pa.Table
    utilities: pa.Table
    alternative_ids: tuple[str, ...]
    seed: int | None

    def __post_init__(self) -> None:
        """Validate choice result invariants (AC-5, AC-6)."""
        from reformlab.discrete_choice.errors import LogitError

        n = self.probabilities.num_rows

        # Validate column names match alternative_ids
        prob_cols = tuple(self.probabilities.column_names)
        if prob_cols != self.alternative_ids:
            raise LogitError(
                f"ChoiceResult probability column names {prob_cols} do not match "
                f"alternative_ids {self.alternative_ids}"
            )

        util_cols = tuple(self.utilities.column_names)
        if util_cols != self.alternative_ids:
            raise LogitError(
                f"ChoiceResult utility column names {util_cols} do not match "
                f"alternative_ids {self.alternative_ids}"
            )

        # Validate chosen length matches N
        if len(self.chosen) != n:
            raise LogitError(
                f"ChoiceResult chosen length ({len(self.chosen)}) does not match "
                f"probability row count ({n})"
            )

        # Validate probability row sums within tolerance (AC-5)
        tolerance = 1e-10
        for i in range(n):
            row_sum = 0.0
            for col_name in self.alternative_ids:
                row_sum += self.probabilities.column(col_name)[i].as_py()
            if abs(row_sum - 1.0) >= tolerance:
                raise LogitError(
                    f"ChoiceResult probability row {i} sums to {row_sum}, "
                    f"expected 1.0 within tolerance {tolerance}"
                )
