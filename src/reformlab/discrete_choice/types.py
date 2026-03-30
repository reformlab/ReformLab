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
    """Generalized taste parameters for the conditional logit model.

    Supports Alternative-Specific Constants (ASCs) and named beta
    coefficients. Each parameter can be marked as calibrated (optimized
    by CalibrationEngine) or fixed (from literature).

    The utility function is:
        V_ij = ASC_j + Σ_k(β_k × attribute_kij)

    Where j indexes alternatives and k indexes beta coefficients.

    Attributes:
        beta_cost: DEPRECATED — Legacy single cost coefficient.
            Use betas["cost"] instead.
        asc: Per-alternative constants (ASC_j). One alternative's
            ASC is normalized to zero (reference_alternative).
        betas: Named taste coefficients (e.g., "cost", "time", "comfort").
        calibrate: Parameter names to optimize during calibration.
            These are the actual dictionary keys from asc and betas,
            not prefixed versions like "asc_*" or "beta_*".
        fixed: Parameter names held constant (literature values).
            These are the actual dictionary keys from asc and betas.
        reference_alternative: Alternative whose ASC is normalized to zero.
        literature_sources: Citation/reference for each fixed parameter.

    Story 14-2: Original single-beta implementation.
    Story 21.7 / AC1: Generalized structure with ASCs and named betas.
    """

    # Legacy field (deprecated but retained for backward compatibility)
    beta_cost: float

    # Generalized fields
    asc: dict[str, float] = field(default_factory=dict)
    betas: dict[str, float] = field(default_factory=dict)
    calibrate: frozenset[str] = frozenset()
    fixed: frozenset[str] = frozenset()
    reference_alternative: str | None = None
    literature_sources: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate taste parameter constraints."""
        from reformlab.discrete_choice.errors import DiscreteChoiceError

        # Determine if in legacy mode before other validations
        # Legacy mode: empty asc, betas has only "cost" key (or empty with empty calibrate/fixed)
        _is_legacy = len(self.asc) == 0 and (
            list(self.betas.keys()) == ["cost"] or
            (len(self.betas) == 0 and len(self.calibrate) == 0 and len(self.fixed) == 0)
        )

        # Validate calibrate and fixed are disjoint
        if self.calibrate & self.fixed:
            raise DiscreteChoiceError(
                f"calibrate and fixed sets must be disjoint, "
                f"found overlap: {self.calibrate & self.fixed}"
            )

        # Validate calibrate and fixed are subsets of available parameters
        available_params = set(self.asc.keys()) | set(self.betas.keys())
        invalid_calibrate = self.calibrate - available_params
        invalid_fixed = self.fixed - available_params
        if invalid_calibrate or invalid_fixed:
            raise DiscreteChoiceError(
                f"calibrate/fixed must be subsets of asc/beta keys. "
                f"Invalid in calibrate: {invalid_calibrate}, "
                f"Invalid in fixed: {invalid_fixed}"
            )

        # Special case: non-empty asc with only "cost" beta is invalid (conflicting legacy/generalized)
        if (
            len(self.asc) > 0
            and list(self.betas.keys()) == ["cost"]
            and len(self.calibrate) == 0
            and len(self.fixed) == 0
        ):
            raise DiscreteChoiceError(
                f"is_legacy_mode=True but asc is non-empty: {list(self.asc.keys())}"
            )

        # Validate legacy mode consistency (before reference_alternative validation)
        if _is_legacy:
            if self.reference_alternative is not None:
                raise DiscreteChoiceError(
                    f"is_legacy_mode=True but reference_alternative='{self.reference_alternative}' "
                    f"(must be None for legacy mode)"
                )

        # Validate reference_alternative (only in non-legacy mode)
        if self.reference_alternative is not None:
            if self.reference_alternative not in self.asc:
                raise DiscreteChoiceError(
                    f"reference_alternative '{self.reference_alternative}' "
                    f"not found in asc keys: {list(self.asc.keys())}"
                )
            # The reference alternative's ASC must be exactly 0.0
            if self.asc[self.reference_alternative] != 0.0:
                raise DiscreteChoiceError(
                    f"reference_alternative '{self.reference_alternative}' "
                    f"must have ASC=0.0, got {self.asc[self.reference_alternative]}"
                )

    @property
    def is_legacy_mode(self) -> bool:
        """True if structurally in legacy mode (empty asc, betas has only 'cost' key).

        This property checks the structure of the data, not how the object
        was created. Both TasteParameters.from_beta_cost(-0.01) and direct
        construction TasteParameters(beta_cost=-0.01, asc={}, betas={"cost": -0.01})
        return True for is_legacy_mode.
        """
        return len(self.asc) == 0 and list(self.betas.keys()) == ["cost"]

    @classmethod
    def from_beta_cost(cls, beta_cost: float) -> TasteParameters:
        """Create generalized TasteParameters from legacy single beta_cost.

        Returns instance with asc={}, betas={"cost": beta_cost},
        calibrate=frozenset(["cost"]), fixed=frozenset().

        Story 21.7 / AC1.
        """
        return cls(
            beta_cost=beta_cost,
            asc={},
            betas={"cost": beta_cost},
            calibrate=frozenset(["cost"]),
            fixed=frozenset(),
        )

    def to_governance_entry(self, *, source_label: str = "taste_parameters") -> dict[str, object]:
        """Return an AssumptionEntry-compatible dict for governance manifests.

        Returns a dict with key, value, source, and is_default fields compatible
        with the governance manifest format. The value field contains all taste
        parameter metadata including ASCs, betas, calibration status, and
        literature sources.

        Args:
            source_label: Human-readable source identifier.

        Returns:
            Dict with AssumptionEntry structure.

        Story 21.7 / AC-8.
        """
        # Separate ASC and beta names from calibrate/fixed sets
        asc_in_calibrate = sorted(set(self.asc.keys()) & self.calibrate)
        asc_in_fixed = sorted(set(self.asc.keys()) & self.fixed)
        betas_in_calibrate = sorted(set(self.betas.keys()) & self.calibrate)
        betas_in_fixed = sorted(set(self.betas.keys()) & self.fixed)

        return {
            "key": "taste_parameters",
            "value": {
                "asc_names": sorted(self.asc.keys()),
                "asc_values": self.asc,
                "beta_names": sorted(self.betas.keys()),
                "beta_values": self.betas,
                "calibrated_asc_names": asc_in_calibrate,
                "calibrated_beta_names": betas_in_calibrate,
                "fixed_asc_names": asc_in_fixed,
                "fixed_beta_names": betas_in_fixed,
                "reference_alternative": self.reference_alternative,
                "literature_sources": self.literature_sources,
                "is_legacy_mode": self.is_legacy_mode,
                "n_calibrated": len(self.calibrate),
                "n_fixed": len(self.fixed),
            },
            "source": source_label,
            "is_default": False,
        }


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
