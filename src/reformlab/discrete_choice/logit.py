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
) -> pa.Table:
    """Compute deterministic utilities V_ij = beta_cost × cost_ij.

    Validates that cost matrix contains no NaN or Inf values before
    computation. Returns N×M PyArrow Table with same column names.

    Args:
        cost_matrix: N×M cost matrix (households × alternatives).
        taste_parameters: Taste parameters with beta_cost coefficient.

    Returns:
        N×M PyArrow Table of utility values.

    Raises:
        LogitError: If cost matrix contains NaN or Inf values.
    """
    beta = taste_parameters.beta_cost
    n = cost_matrix.n_households

    if n == 0:
        return pa.table({
            aid: pa.array([], type=pa.float64())
            for aid in cost_matrix.alternative_ids
        })

    # Validate: no NaN or Inf in cost matrix (AC-1)
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

    # Compute V_ij = beta_cost × cost_ij
    utility_columns: dict[str, pa.Array] = {}
    for aid in cost_matrix.alternative_ids:
        costs = cost_matrix.table.column(aid).to_pylist()
        utilities = [beta * c for c in costs]
        utility_columns[aid] = pa.array(utilities)

    return pa.table(utility_columns)


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
    """

    __slots__ = (
        "_taste_parameters",
        "_cost_matrix_key",
        "_name",
        "_depends_on",
        "_description",
    )

    def __init__(
        self,
        taste_parameters: TasteParameters,
        cost_matrix_key: str = DISCRETE_CHOICE_COST_MATRIX_KEY,
        name: str = "logit_choice",
        depends_on: tuple[str, ...] = ("discrete_choice",),
        description: str | None = None,
    ) -> None:
        self._taste_parameters = taste_parameters
        self._cost_matrix_key = cost_matrix_key
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
            DiscreteChoiceError: If CostMatrix not found in state.
            LogitError: If computation fails (NaN/Inf costs).
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

        n = cost_matrix.n_households
        m = cost_matrix.n_alternatives

        logger.info(
            "year=%d step_name=%s n_households=%d n_alternatives=%d "
            "beta_cost=%f seed=%s event=step_start",
            year,
            self._name,
            n,
            m,
            beta,
            seed,
        )

        # Compute utilities → probabilities → draws (AC-1, AC-2)
        utilities = compute_utilities(cost_matrix, self._taste_parameters)
        probabilities = compute_probabilities(utilities)
        choice_result = draw_choices(
            probabilities, utilities, cost_matrix.alternative_ids, seed
        )

        # Store result and extend metadata (AC-8)
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
