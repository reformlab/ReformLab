# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Calibration engine for discrete choice taste parameter optimization.

Implements the CalibrationEngine that optimizes β_cost (beta_cost) against
observed household transition rates by minimizing an objective function
(MSE or negative log-likelihood) using scipy.optimize.minimize.

Key design decisions:
- Uses expected probabilities (not stochastic draws) → smooth, differentiable objective
- Optimization is deterministic by construction: same inputs → same result
- Public API exposes CalibrationEngine.calibrate() → CalibrationResult

Story 15.2 / FR52 — CalibrationEngine with objective function optimization.
"""

from __future__ import annotations

import logging
import math
from collections.abc import Callable
from dataclasses import dataclass

import pyarrow as pa
import pyarrow.compute as pc

from reformlab.calibration.errors import (
    CalibrationOptimizationError,
    CalibrationTargetLoadError,
    CalibrationTargetValidationError,
)
from reformlab.calibration.types import (
    CalibrationConfig,
    CalibrationResult,
    CalibrationTargetSet,
    RateComparison,
)
from reformlab.discrete_choice.logit import compute_probabilities, compute_utilities
from reformlab.discrete_choice.types import CostMatrix, TasteParameters

logger = logging.getLogger(__name__)


# ============================== Rate Computation ==============================


def compute_simulated_rates(
    cost_matrix: CostMatrix,
    taste_parameters: TasteParameters,
    from_states: pa.Array,
    alternative_ids: tuple[str, ...],
) -> dict[tuple[str, str], float]:
    """Compute mean simulated transition rates per (from_state, to_state) pair.

    Uses expected probabilities (not stochastic draws) so the result is
    deterministic and differentiable — suitable for gradient-based optimization.

    Args:
        cost_matrix: N×M CostMatrix for the decision domain.
        taste_parameters: TasteParameters with the candidate beta_cost.
        from_states: Length-N PyArrow array of household origin states.
        alternative_ids: Tuple of to_state (alternative) IDs.

    Returns:
        Dict mapping (from_state, to_state) → mean probability across households
        in the from_state group.
    """
    n = cost_matrix.n_households
    if n == 0:
        return {}

    utilities = compute_utilities(cost_matrix, taste_parameters)
    probabilities = compute_probabilities(utilities)

    # Get unique from_state values present in from_states
    unique_from_states: list[str] = pc.unique(from_states).to_pylist()

    rates: dict[tuple[str, str], float] = {}
    for from_state_val in unique_from_states:
        mask = pc.equal(from_states, pa.scalar(from_state_val, type=pa.utf8()))
        for alt_id in alternative_ids:
            prob_col = probabilities.column(alt_id)
            group_probs = pc.filter(prob_col, mask)
            n_group = len(group_probs)
            if n_group == 0:
                continue
            simulated_rate = pc.mean(group_probs).as_py()
            rates[(from_state_val, alt_id)] = float(simulated_rate)

    return rates


# ============================== Objective Functions ==============================


def build_mse_objective(
    domain_targets: CalibrationTargetSet,
    cost_matrix: CostMatrix,
    from_states: pa.Array,
) -> Callable[[object], float]:
    """Build a weighted MSE objective closure for scipy.optimize.minimize.

    The returned function takes a shape-(1,) numpy array (scipy convention)
    and returns the weighted mean squared error between simulated and observed
    transition rates.

    Args:
        domain_targets: Calibration targets for the domain being calibrated.
        cost_matrix: N×M CostMatrix (captured in closure).
        from_states: Length-N PyArrow array of household origin states.

    Returns:
        Callable suitable for scipy.optimize.minimize.
    """
    alternative_ids = cost_matrix.alternative_ids
    targets = domain_targets.targets

    def objective(x: object) -> float:
        # x is a numpy ndarray of shape (1,) from scipy — extract scalar
        beta = float(x[0])  # type: ignore[index]
        taste = TasteParameters(beta_cost=beta)
        simulated = compute_simulated_rates(cost_matrix, taste, from_states, alternative_ids)

        total_weighted_error = 0.0
        total_weight = 0.0
        for t in targets:
            key = (t.from_state, t.to_state)
            sim_rate = simulated.get(key, 0.0)
            total_weighted_error += t.weight * (sim_rate - t.observed_rate) ** 2
            total_weight += t.weight

        if total_weight == 0.0:
            return 0.0
        return total_weighted_error / total_weight

    return objective


def build_log_likelihood_objective(
    domain_targets: CalibrationTargetSet,
    cost_matrix: CostMatrix,
    from_states: pa.Array,
) -> Callable[[object], float]:
    """Build a negative log-likelihood objective closure for scipy.optimize.minimize.

    The returned function takes a shape-(1,) numpy array and returns the
    weighted negative log-likelihood. Simulated rates are clamped to
    [1e-15, 1-1e-15] to avoid log(0).

    Args:
        domain_targets: Calibration targets for the domain being calibrated.
        cost_matrix: N×M CostMatrix (captured in closure).
        from_states: Length-N PyArrow array of household origin states.

    Returns:
        Callable suitable for scipy.optimize.minimize.
    """
    alternative_ids = cost_matrix.alternative_ids
    targets = domain_targets.targets
    eps = 1e-15

    def objective(x: object) -> float:
        beta = float(x[0])  # type: ignore[index]
        taste = TasteParameters(beta_cost=beta)
        simulated = compute_simulated_rates(cost_matrix, taste, from_states, alternative_ids)

        total_ll = 0.0
        for t in targets:
            key = (t.from_state, t.to_state)
            sim_rate = simulated.get(key, 0.0)
            sim_clamped = max(eps, min(1.0 - eps, sim_rate))
            obs = t.observed_rate
            total_ll += t.weight * (
                obs * math.log(sim_clamped) + (1.0 - obs) * math.log(1.0 - sim_clamped)
            )

        return -total_ll

    return objective


# ============================== CalibrationEngine ==============================


@dataclass(frozen=True)
class CalibrationEngine:
    """Engine that optimizes discrete choice β coefficients against observed transition rates.

    Wraps a CalibrationConfig and exposes a single ``calibrate()`` method that
    runs scipy.optimize.minimize and returns a CalibrationResult with the
    optimized parameters and convergence diagnostics.

    Story 15.2 / AC-1 through AC-5.
    """

    config: CalibrationConfig

    def calibrate(self) -> CalibrationResult:
        """Optimize β_cost to minimize distance between simulated and observed rates.

        Given the config's targets, cost matrix, and from_states, runs
        scipy.optimize.minimize on the specified objective function and returns
        a CalibrationResult with optimized parameters, diagnostics, and per-target
        rate comparisons.

        Returns:
            CalibrationResult with the optimized β, convergence diagnostics, and
            per-target rate comparisons.

        Raises:
            CalibrationOptimizationError: If inputs are invalid or scipy fails.
        """
        from scipy.optimize import minimize

        domain = self.config.domain
        initial_beta = self.config.initial_beta
        method = self.config.method

        logger.info(
            "event=calibration_start domain=%s initial_beta=%f method=%s objective=%s",
            domain,
            initial_beta,
            method,
            self.config.objective_type,
        )

        # 1. Filter targets to domain
        domain_targets = self.config.targets.by_domain(domain)

        # 2. Validate inputs
        self._validate_inputs(domain_targets)

        # 3. Build objective function
        if self.config.objective_type == "mse":
            objective = build_mse_objective(
                domain_targets, self.config.cost_matrix, self.config.from_states
            )
        else:  # "log_likelihood"
            objective = build_log_likelihood_objective(
                domain_targets, self.config.cost_matrix, self.config.from_states
            )

        # 4. Run scipy.optimize.minimize
        try:
            result = minimize(
                objective,
                x0=[initial_beta],
                method=method,
                bounds=[(self.config.beta_bounds[0], self.config.beta_bounds[1])],
                options={
                    "maxiter": self.config.max_iterations,
                    "ftol": self.config.tolerance,
                },
            )
        except Exception as exc:
            logger.error(
                "event=calibration_failed domain=%s error=%s",
                domain,
                exc,
            )
            raise CalibrationOptimizationError(
                f"scipy optimization failed for domain={domain!r}: {exc}"
            ) from exc

        # 5. Extract results
        optimized_beta = float(result.x[0])
        gradient_norm: float | None = None
        if hasattr(result, "jac") and result.jac is not None:
            gradient_norm = float(abs(result.jac[0]))

        # 6. Compute final simulated rates for comparison
        optimized_taste = TasteParameters(beta_cost=optimized_beta)
        final_rates = compute_simulated_rates(
            self.config.cost_matrix,
            optimized_taste,
            self.config.from_states,
            self.config.cost_matrix.alternative_ids,
        )

        # 7. Build per-target rate comparisons
        rate_comparisons_list: list[RateComparison] = []
        for t in domain_targets.targets:
            key = (t.from_state, t.to_state)
            sim_rate = final_rates.get(key, 0.0)
            abs_err = abs(sim_rate - t.observed_rate)
            rate_comparisons_list.append(
                RateComparison(
                    from_state=t.from_state,
                    to_state=t.to_state,
                    observed_rate=t.observed_rate,
                    simulated_rate=sim_rate,
                    absolute_error=abs_err,
                    within_tolerance=abs_err <= self.config.rate_tolerance,
                )
            )

        rate_comparisons = tuple(rate_comparisons_list)
        all_within_tolerance = all(rc.within_tolerance for rc in rate_comparisons)

        logger.info(
            "event=calibration_complete domain=%s optimized_beta=%f iterations=%d "
            "converged=%s all_within_tolerance=%s objective_value=%f",
            domain,
            optimized_beta,
            int(result.nit),
            bool(result.success),
            all_within_tolerance,
            float(result.fun),
        )

        return CalibrationResult(
            optimized_parameters=optimized_taste,
            domain=domain,
            objective_type=self.config.objective_type,
            objective_value=float(result.fun),
            convergence_flag=bool(result.success),
            iterations=int(result.nit),
            gradient_norm=gradient_norm,
            method=method,
            rate_comparisons=rate_comparisons,
            all_within_tolerance=all_within_tolerance,
        )

    def _validate_inputs(self, domain_targets: CalibrationTargetSet) -> None:
        """Validate inputs before running optimization.

        Checks:
        1. Non-empty domain targets.
        2. All target to_state values exist in cost_matrix.alternative_ids.
        3. All target from_state values exist in from_states array.
        4. Consistency (duplicate check) via domain_targets.validate_consistency().
        5. Total weight sum > 0.0.

        Raises:
            CalibrationOptimizationError: On any validation failure with a clear message.
        """
        domain = self.config.domain

        # 1. Non-empty targets
        if len(domain_targets.targets) == 0:
            raise CalibrationOptimizationError(
                f"No calibration targets for domain={domain!r}"
            )

        # 2. All to_state values must exist in cost_matrix.alternative_ids
        available_alts = set(self.config.cost_matrix.alternative_ids)
        unknown_alts = {t.to_state for t in domain_targets.targets} - available_alts
        if unknown_alts:
            raise CalibrationOptimizationError(
                f"Unknown to_state values {sorted(unknown_alts)!r} in domain={domain!r}; "
                f"expected one of {sorted(available_alts)!r}"
            )

        # 3. All from_state values must exist in from_states array
        available_from: set[str] = set(pc.unique(self.config.from_states).to_pylist())
        target_from = {t.from_state for t in domain_targets.targets}
        missing_from = target_from - available_from
        if missing_from:
            raise CalibrationOptimizationError(
                f"Missing from_state values {sorted(missing_from)!r} from provided from_states "
                f"in domain={domain!r}"
            )

        # 4. Consistency (duplicate detection) — re-raise as CalibrationOptimizationError
        # to enforce the single exception boundary documented in Task 5.7.
        try:
            domain_targets.validate_consistency()
        except (CalibrationTargetLoadError, CalibrationTargetValidationError) as exc:
            raise CalibrationOptimizationError(
                f"Calibration targets consistency check failed for domain={domain!r}: {exc}"
            ) from exc

        # 5. Non-zero total weight
        total_weight = sum(t.weight for t in domain_targets.targets)
        if total_weight <= 0.0:
            raise CalibrationOptimizationError(
                f"All calibration targets have weight=0.0 for domain={domain!r}; "
                "at least one positive weight is required"
            )
