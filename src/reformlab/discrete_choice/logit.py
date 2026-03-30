# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Conditional logit model with seed-controlled draws.

Implements the conditional logit choice model as pure functions
(compute_utilities, compute_probabilities, draw_choices) and a
LogitChoiceStep that integrates with the orchestrator pipeline.

Story 14-2: Conditional logit model with seed-controlled draws.
"""

from __future__ import annotations

import logging
import math
import random
from dataclasses import replace
from typing import TYPE_CHECKING

import pyarrow as pa

from reformlab.discrete_choice.errors import DiscreteChoiceError, LogitError
from reformlab.discrete_choice.step import (
    DISCRETE_CHOICE_COST_MATRIX_KEY,
    DISCRETE_CHOICE_METADATA_KEY,
)
from reformlab.discrete_choice.types import ChoiceResult, CostMatrix, TasteParameters

if TYPE_CHECKING:
    from reformlab.orchestrator.types import YearState

logger = logging.getLogger(__name__)


# ============================================================================
# Stable state key for logit choice result
# ============================================================================

DISCRETE_CHOICE_RESULT_KEY = "discrete_choice_result"


# ============================================================================
# Pure functions
# ============================================================================


def compute_utilities(
    cost_matrix: CostMatrix,
    taste_parameters: TasteParameters,
    utility_attributes: dict[str, pa.Table] | None = None,
) -> pa.Table:
    """Compute deterministic utilities for the conditional logit model.

    Legacy mode (is_legacy_mode=True): V_ij = beta_cost × cost_ij
    Generalized mode: V_ij = ASC_j + Σ_k(β_k × attribute_kij)

    Args:
        cost_matrix: N×M cost matrix (households × alternatives).
        taste_parameters: Taste parameters with ASCs and/or betas.
        utility_attributes: Optional mapping from beta name to N×M attribute tables.
            If None and legacy mode, uses cost_matrix.table for "cost" beta.
            If None and generalized mode with multiple betas, raises error.

    Returns:
        N×M PyArrow Table of utility values.

    Raises:
        LogitError: If cost matrix contains NaN or Inf values.
        DiscreteChoiceError: If utility_attributes validation fails.

    Story 14-2: Original single-beta implementation.
    Story 21.7 / AC2: Generalized utility with ASCs and multiple betas.
    """
    n = cost_matrix.n_households

    if n == 0:
        return pa.table({
            aid: pa.array([], type=pa.float64())
            for aid in cost_matrix.alternative_ids
        })

    # === Legacy mode detection ===
    is_legacy = taste_parameters.is_legacy_mode

    # === Validate cost matrix ===
    invalid_cells: list[str] = []
    for col_idx, aid in enumerate(cost_matrix.alternative_ids):
        col = cost_matrix.table.column(aid)
        for row_idx in range(n):
            val = col[row_idx].as_py()
            if val is None or math.isnan(val):
                invalid_cells.append(f"NaN at [{row_idx}, {col_idx}] ({aid})")
            elif math.isinf(val):
                invalid_cells.append(f"Inf at [{row_idx}, {col_idx}] ({aid})")

    if invalid_cells:
        raise LogitError(
            f"Cost matrix contains invalid values: {', '.join(invalid_cells)}"
        )

    # === Legacy mode: V_ij = beta_cost × cost_ij ===
    if is_legacy:
        beta = taste_parameters.beta_cost
        utility_columns: dict[str, pa.Array] = {}
        for aid in cost_matrix.alternative_ids:
            costs = cost_matrix.table.column(aid).to_pylist()
            utilities = [beta * c for c in costs]
            utility_columns[aid] = pa.array(utilities)
        return pa.table(utility_columns)

    # === Generalized mode: V_ij = ASC_j + Σ_k(β_k × attribute_kij) ===
    # Validate utility_attributes if provided
    if utility_attributes is not None:
        _validate_utility_attributes(
            utility_attributes, cost_matrix, taste_parameters
        )
    elif len(taste_parameters.betas) > 1 or (
        len(taste_parameters.betas) == 1
        and list(taste_parameters.betas.keys()) != ["cost"]
    ):
        # Multiple betas without explicit attributes raises error
        # Note: empty betas (legacy mode construction) falls through to use beta_cost
        raise DiscreteChoiceError(
            f"Multi-beta mode requires utility_attributes; "
            f"found betas: {list(taste_parameters.betas.keys())}"
        )

    # Handle empty betas case (legacy construction TasteParameters(beta_cost=-0.01))
    # In this case, use beta_cost field as the single beta
    if len(taste_parameters.betas) == 0:
        beta = taste_parameters.beta_cost
        utility_columns: dict[str, pa.Array] = {}
        for aid in cost_matrix.alternative_ids:
            costs = cost_matrix.table.column(aid).to_pylist()
            utilities = [beta * c for c in costs]
            utility_columns[aid] = pa.array(utilities)
        return pa.table(utility_columns)

    # Initialize utility columns with ASCs
    utility_columns: dict[str, pa.Array] = {}
    for aid in cost_matrix.alternative_ids:
        asc_val = taste_parameters.asc.get(aid, 0.0)
        utility_columns[aid] = [asc_val] * n

    # Add beta-weighted attributes
    # If utility_attributes is None but we have single "cost" beta, use cost_matrix.table
    attrs_to_use = utility_attributes
    if attrs_to_use is None and "cost" in taste_parameters.betas:
        attrs_to_use = {"cost": cost_matrix.table}

    if attrs_to_use:
        for beta_name, beta_value in taste_parameters.betas.items():
            if beta_name not in attrs_to_use:
                continue  # Skip if attribute not provided (should have been validated above)

            attr_table = attrs_to_use[beta_name]
            for aid in cost_matrix.alternative_ids:
                attr_col = attr_table.column(aid).to_pylist()
                # Add beta * attribute to utility
                for i in range(n):
                    utility_columns[aid][i] += beta_value * attr_col[i]

    # Convert to PyArrow arrays
    for aid in cost_matrix.alternative_ids:
        utility_columns[aid] = pa.array(utility_columns[aid], type=pa.float64())

    return pa.table(utility_columns)


def _validate_utility_attributes(
    utility_attributes: dict[str, pa.Table],
    cost_matrix: CostMatrix,
    taste_parameters: TasteParameters,
) -> None:
    """Validate utility attributes table structure and values.

    Args:
        utility_attributes: Mapping from beta name to attribute table.
        cost_matrix: Reference cost matrix for shape validation.
        taste_parameters: TasteParameters for beta validation.

    Raises:
        DiscreteChoiceError: If validation fails.
    """
    # Validate all betas have corresponding attributes
    for beta_name in taste_parameters.betas:
        if beta_name not in utility_attributes:
            raise DiscreteChoiceError(
                f"Missing utility attribute for beta '{beta_name}'; "
                f"available: {list(utility_attributes.keys())}"
            )

    # Validate each attribute table
    n = cost_matrix.n_households
    expected_cols = set(cost_matrix.alternative_ids)

    for beta_name, attr_table in utility_attributes.items():
        # Check shape: n_rows must match cost_matrix
        if attr_table.num_rows != n:
            raise DiscreteChoiceError(
                f"Utility attribute '{beta_name}' has {attr_table.num_rows} rows, "
                f"expected {n} (matching cost_matrix)"
            )

        # Check columns: must match cost_matrix.alternative_ids
        actual_cols = set(attr_table.column_names)
        if actual_cols != expected_cols:
            raise DiscreteChoiceError(
                f"Utility attribute '{beta_name}' has columns {sorted(actual_cols)}, "
                f"expected {sorted(expected_cols)} (matching cost_matrix.alternative_ids)"
            )

        # Check type: must be float64
        for col_name in attr_table.column_names:
            if attr_table.column(col_name).type != pa.float64():
                raise DiscreteChoiceError(
                    f"Utility attribute '{beta_name}' column '{col_name}' "
                    f"has type {attr_table.column(col_name).type}, "
                    f"expected float64"
                )

        # Check for NaN/Inf values
        for col_idx, col_name in enumerate(attr_table.column_names):
            col = attr_table.column(col_name)
            for row_idx in range(n):
                val = col[row_idx].as_py()
                if val is None or math.isnan(val):
                    raise DiscreteChoiceError(
                        f"Utility attribute '{beta_name}' contains NaN at [{row_idx}, {col_idx}]"
                    )
                elif math.isinf(val):
                    raise DiscreteChoiceError(
                        f"Utility attribute '{beta_name}' contains Inf at [{row_idx}, {col_idx}]"
                    )


def compute_probabilities(utilities: pa.Table) -> pa.Table:
    """Apply softmax per row using log-sum-exp trick for numerical stability.

    P(j|C_i) = exp(V_ij - V_max_i) / Σ_k exp(V_ik - V_max_i)

    Args:
        utilities: N×M PyArrow Table of utility values.

    Returns:
        N×M PyArrow Table of choice probabilities.
    """
    n = utilities.num_rows
    col_names = utilities.column_names

    if n == 0:
        return pa.table({
            col: pa.array([], type=pa.float64()) for col in col_names
        })

    m = len(col_names)

    # Extract all utility values to Python lists for computation
    util_cols: list[list[float]] = [
        utilities.column(col).to_pylist() for col in col_names
    ]

    # Compute probabilities row by row with log-sum-exp trick
    prob_cols: list[list[float]] = [[] for _ in range(m)]

    for i in range(n):
        row_vals = [util_cols[j][i] for j in range(m)]
        v_max = max(row_vals)

        # exp(V_ij - V_max) for each alternative
        exp_shifted = [math.exp(v - v_max) for v in row_vals]
        total = sum(exp_shifted)

        for j in range(m):
            prob_cols[j].append(exp_shifted[j] / total)

    return pa.table({
        col_names[j]: pa.array(prob_cols[j]) for j in range(m)
    })


def draw_choices(
    probabilities: pa.Table,
    utilities: pa.Table,
    alternative_ids: tuple[str, ...],
    seed: int | None,
) -> ChoiceResult:
    """Make seed-controlled random draws using inverse CDF sampling.

    Each household is assigned exactly one alternative. Draws use
    random.Random(seed) for isolation and reproducibility.

    Args:
        probabilities: N×M PyArrow Table of choice probabilities.
        utilities: N×M PyArrow Table of deterministic utilities.
        alternative_ids: Tuple of alternative IDs matching column order.
        seed: Random seed (None for non-deterministic draws).

    Returns:
        ChoiceResult with chosen alternatives, probabilities, utilities,
        and seed.
    """
    n = probabilities.num_rows
    m = len(alternative_ids)

    if seed is None:
        logger.warning(
            "step_name=draw_choices event=null_seed "
            "msg=No seed provided; draws are non-deterministic",
        )

    if n == 0:
        return ChoiceResult(
            chosen=pa.array([], type=pa.string()),
            probabilities=probabilities,
            utilities=utilities,
            alternative_ids=alternative_ids,
            seed=seed,
        )

    # Extract probability values
    prob_cols: list[list[float]] = [
        probabilities.column(aid).to_pylist() for aid in alternative_ids
    ]

    # Inverse CDF sampling with isolated RNG (AC-2)
    rng = random.Random(seed)
    chosen_list: list[str] = []

    for i in range(n):
        u = rng.random()
        cumulative = 0.0
        chosen_alt = alternative_ids[-1]  # numerical safety fallback
        for j in range(m):
            cumulative += prob_cols[j][i]
            if u < cumulative:
                chosen_alt = alternative_ids[j]
                break
        chosen_list.append(chosen_alt)

    return ChoiceResult(
        chosen=pa.array(chosen_list),
        probabilities=probabilities,
        utilities=utilities,
        alternative_ids=alternative_ids,
        seed=seed,
    )


# ============================================================================
# LogitChoiceStep (OrchestratorStep protocol)
# ============================================================================


class LogitChoiceStep:
    """Orchestrator step for conditional logit choice model.

    Reads CostMatrix from YearState, computes utilities and probabilities,
    makes seed-controlled draws, and stores ChoiceResult in state.

    Implements the OrchestratorStep protocol.

    Story 14-2, AC-7: Step integration.
    Story 21.7, AC-3: Extended with utility_attributes_key for generalized taste parameters.
    """

    __slots__ = (
        "_taste_parameters",
        "_cost_matrix_key",
        "_utility_attributes_key",
        "_name",
        "_depends_on",
        "_description",
    )

    def __init__(
        self,
        taste_parameters: TasteParameters,
        cost_matrix_key: str = DISCRETE_CHOICE_COST_MATRIX_KEY,
        utility_attributes_key: str | None = None,
        name: str = "logit_choice",
        depends_on: tuple[str, ...] = ("discrete_choice",),
        description: str | None = None,
    ) -> None:
        self._taste_parameters = taste_parameters
        self._cost_matrix_key = cost_matrix_key
        self._utility_attributes_key = utility_attributes_key
        self._name = name
        self._depends_on = depends_on
        self._description = (
            description or "Logit choice step: probability computation and draws"
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def depends_on(self) -> tuple[str, ...]:
        return self._depends_on

    @property
    def description(self) -> str:
        return self._description

    def execute(self, year: int, state: YearState) -> YearState:
        """Execute logit choice model for a given year.

        Reads CostMatrix from state, computes utilities → probabilities →
        draws, stores ChoiceResult and extends metadata.

        Args:
            year: Current simulation year.
            state: Current year state (must contain CostMatrix).

        Returns:
            New YearState with ChoiceResult and extended metadata.

        Raises:
            DiscreteChoiceError: If CostMatrix not found in state or utility_attributes is invalid.
            LogitError: If computation fails (NaN/Inf costs).

        Story 14-2, AC-7: Step integration.
        Story 21.7, AC-3: Extended with utility_attributes_key for generalized taste parameters.
        """
        beta = self._taste_parameters.beta_cost
        seed = state.seed

        # Warn if seed is None (AC-9)
        if seed is None:
            logger.warning(
                "year=%d step_name=%s event=null_seed "
                "msg=No seed provided; draws are non-deterministic",
                year,
                self._name,
            )

        # Read CostMatrix from state (AC-7)
        cost_matrix = state.data.get(self._cost_matrix_key)
        if not isinstance(cost_matrix, CostMatrix):
            raise DiscreteChoiceError(
                f"CostMatrix not found in YearState.data['{self._cost_matrix_key}']. "
                f"Available keys: {list(state.data.keys())}",
                year=year,
                step_name=self._name,
            )

        # Read utility attributes from state if utility_attributes_key is provided (AC-3)
        utility_attributes = None
        if self._utility_attributes_key is not None:
            utility_attributes = state.data.get(self._utility_attributes_key)
            if utility_attributes is not None and not isinstance(utility_attributes, dict):
                raise DiscreteChoiceError(
                    f"Expected dict[str, pa.Table] for YearState.data['{self._utility_attributes_key}'], "
                    f"got {type(utility_attributes).__name__}",
                    year=year,
                    step_name=self._name,
                )

        n = cost_matrix.n_households
        m = cost_matrix.n_alternatives

        # Log with taste parameter info (AC-3)
        asc_count = len(self._taste_parameters.asc)
        beta_count = len(self._taste_parameters.betas)
        is_legacy = self._taste_parameters.is_legacy_mode
        logger.info(
            "year=%d step_name=%s n_households=%d n_alternatives=%d "
            "asc_count=%d beta_count=%d is_legacy_mode=%s seed=%s event=step_start",
            year,
            self._name,
            n,
            m,
            asc_count,
            beta_count,
            is_legacy,
            seed,
        )

        # Compute utilities → probabilities → draws (AC-1, AC-2)
        utilities = compute_utilities(cost_matrix, self._taste_parameters, utility_attributes)
        probabilities = compute_probabilities(utilities)
        choice_result = draw_choices(
            probabilities, utilities, cost_matrix.alternative_ids, seed
        )

        # Store result and extend metadata (AC-8, AC-3)
        new_data = dict(state.data)
        new_data[DISCRETE_CHOICE_RESULT_KEY] = choice_result

        # Extend metadata: create new dict from existing + logit fields
        existing_metadata = state.data.get(DISCRETE_CHOICE_METADATA_KEY, {})
        if not isinstance(existing_metadata, dict):
            raise DiscreteChoiceError(
                f"Expected dict for metadata key '{DISCRETE_CHOICE_METADATA_KEY}', "
                f"got {type(existing_metadata).__name__}",
                year=year,
                step_name=self._name,
            )
        extended_metadata = dict(existing_metadata)
        extended_metadata["beta_cost"] = beta
        extended_metadata["choice_seed"] = seed
        # Extended metadata for taste parameters (AC-3)
        extended_metadata["taste_parameters_asc_count"] = asc_count
        extended_metadata["taste_parameters_beta_count"] = beta_count
        extended_metadata["taste_parameters_calibrated"] = sorted(self._taste_parameters.calibrate)
        extended_metadata["taste_parameters_fixed"] = sorted(self._taste_parameters.fixed)
        extended_metadata["taste_parameters_reference_alternative"] = (
            self._taste_parameters.reference_alternative
        )
        extended_metadata["taste_parameters_is_legacy_mode"] = is_legacy
        new_data[DISCRETE_CHOICE_METADATA_KEY] = extended_metadata

        logger.info(
            "year=%d step_name=%s n_households=%d n_alternatives=%d "
            "event=step_complete",
            year,
            self._name,
            n,
            m,
        )

        return replace(state, data=new_data)
