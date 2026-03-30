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
    ParameterDiagnostics,
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
    utility_attributes: dict[str, pa.Table] | None = None,
) -> dict[tuple[str, str], float]:
    """Compute mean simulated transition rates per (from_state, to_state) pair.

    Uses expected probabilities (not stochastic draws) so the result is
    deterministic and differentiable — suitable for gradient-based optimization.

    Args:
        cost_matrix: N×M CostMatrix for the decision domain.
        taste_parameters: TasteParameters with ASCs and betas (generalized) or beta_cost (legacy).
        from_states: Length-N PyArrow array of household origin states.
        alternative_ids: Tuple of to_state (alternative) IDs.
        utility_attributes: Optional mapping from beta name to N×M attribute table.

    Returns:
        Dict mapping (from_state, to_state) → mean probability across households
        in the from_state group.

    Story 15.2 / FR52 — Original single-parameter implementation.
    Story 21.7 / AC-5 — Extended for vector optimization with utility_attributes.
    """
    n = cost_matrix.n_households
    if n == 0:
        return {}

    utilities = compute_utilities(cost_matrix, taste_parameters, utility_attributes)
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


def _build_generalized_taste_parameters(
    target_parameters: TasteParameters,
    calibrate: frozenset[str],
    x: object,
) -> TasteParameters:
    """Map an optimizer vector back to a normalized TasteParameters instance."""
    optimized_asc = dict(target_parameters.asc)
    optimized_betas = dict(target_parameters.betas)
    param_order = tuple(sorted(calibrate))
    reference_alternative = target_parameters.reference_alternative

    for i, param_name in enumerate(param_order):
        value = float(x[i])  # type: ignore[index]
        if param_name == reference_alternative:
            value = 0.0
        if param_name in optimized_asc:
            optimized_asc[param_name] = value
        elif param_name in optimized_betas:
            optimized_betas[param_name] = value

    if reference_alternative is not None and reference_alternative in optimized_asc:
        optimized_asc[reference_alternative] = 0.0

    return TasteParameters(
        beta_cost=0.0,  # unused in generalized mode
        asc=optimized_asc,
        betas=optimized_betas,
        calibrate=calibrate,
        fixed=target_parameters.fixed,
        reference_alternative=reference_alternative,
        literature_sources=target_parameters.literature_sources,
    )


def build_mse_objective(
    domain_targets: CalibrationTargetSet,
    cost_matrix: CostMatrix,
    from_states: pa.Array,
    target_parameters: TasteParameters | None = None,
    calibrate: frozenset[str] = frozenset(),
    initial_values: dict[str, float] | None = None,
    utility_attributes: dict[str, pa.Table] | None = None,
) -> Callable[[object], float]:
    """Build a weighted MSE objective closure for scipy.optimize.minimize.

    Supports both legacy single-parameter mode and generalized vector optimization.

    Args:
        domain_targets: Calibration targets for the domain being calibrated.
        cost_matrix: N×M CostMatrix (captured in closure).
        from_states: Length-N PyArrow array of household origin states.
        target_parameters: Base TasteParameters with ASCs and betas structure (generalized mode).
        calibrate: Set of parameter names to optimize (generalized mode).
        initial_values: Initial values for calibrated parameters (generalized mode).
        utility_attributes: Optional mapping from beta name to N×M attribute table.

    Returns:
        Callable suitable for scipy.optimize.minimize.

    Story 15.2 / FR52 — Original single-parameter implementation.
    Story 21.7 / AC-5 — Extended for vector optimization.
    """
    alternative_ids = cost_matrix.alternative_ids
    targets = domain_targets.targets

    # Detect mode: legacy if target_parameters is None or if calibrate is empty/single "cost"
    is_legacy = target_parameters is None or not calibrate or (
        len(calibrate) == 1 and "cost" in calibrate and not target_parameters.asc
    )
    def objective(x: object) -> float:
        # x is a numpy ndarray from scipy
        if is_legacy:
            # Legacy mode: x is shape-(1,) array with beta_cost
            beta = float(x[0])  # type: ignore[index]
            taste = TasteParameters(beta_cost=beta)
            utility_attrs = None
        else:
            # Generalized mode: build TasteParameters from vector x
            taste = _build_generalized_taste_parameters(
                target_parameters,  # type: ignore[arg-type]
                calibrate,
                x,
            )
            utility_attrs = utility_attributes

        simulated = compute_simulated_rates(cost_matrix, taste, from_states, alternative_ids, utility_attrs)

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
    target_parameters: TasteParameters | None = None,
    calibrate: frozenset[str] = frozenset(),
    initial_values: dict[str, float] | None = None,
    utility_attributes: dict[str, pa.Table] | None = None,
) -> Callable[[object], float]:
    """Build a negative log-likelihood objective closure for scipy.optimize.minimize.

    Supports both legacy single-parameter mode and generalized vector optimization.
    Simulated rates are clamped to [1e-15, 1-1e-15] to avoid log(0).

    Args:
        domain_targets: Calibration targets for the domain being calibrated.
        cost_matrix: N×M CostMatrix (captured in closure).
        from_states: Length-N PyArrow array of household origin states.
        target_parameters: Base TasteParameters with ASCs and betas structure (generalized mode).
        calibrate: Set of parameter names to optimize (generalized mode).
        initial_values: Initial values for calibrated parameters (generalized mode).
        utility_attributes: Optional mapping from beta name to N×M attribute table.

    Returns:
        Callable suitable for scipy.optimize.minimize.

    Story 15.2 / FR52 — Original single-parameter implementation.
    Story 21.7 / AC-5 — Extended for vector optimization.
    """
    alternative_ids = cost_matrix.alternative_ids
    targets = domain_targets.targets
    eps = 1e-15

    # Detect mode: legacy if target_parameters is None or if calibrate is empty/single "cost"
    is_legacy = target_parameters is None or not calibrate or (
        len(calibrate) == 1 and "cost" in calibrate and not target_parameters.asc
    )
    def objective(x: object) -> float:
        if is_legacy:
            # Legacy mode: x is shape-(1,) array with beta_cost
            beta = float(x[0])  # type: ignore[index]
            taste = TasteParameters(beta_cost=beta)
            utility_attrs = None
        else:
            # Generalized mode: build TasteParameters from vector x
            taste = _build_generalized_taste_parameters(
                target_parameters,  # type: ignore[arg-type]
                calibrate,
                x,
            )
            utility_attrs = utility_attributes

        simulated = compute_simulated_rates(cost_matrix, taste, from_states, alternative_ids, utility_attrs)

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
        """Optimize taste parameters to minimize distance between simulated and observed rates.

        Supports both legacy single-parameter mode (beta_cost only) and generalized
        vector optimization (multiple ASCs and betas).

        Returns:
            CalibrationResult with the optimized parameters, convergence diagnostics, and
            per-target rate comparisons.

        Raises:
            CalibrationOptimizationError: If inputs are invalid or scipy fails.

        Story 15.2 / FR52 — Original single-parameter implementation.
        Story 21.7 / AC-5, AC-6 — Extended for vector optimization with diagnostics.
        """
        from scipy.optimize import minimize

        domain = self.config.domain
        method = self.config.method
        is_legacy = self.config.is_legacy_mode

        # 1. Filter targets to domain
        domain_targets = self.config.targets.by_domain(domain)

        # 2. Validate inputs before constructing optimizer vectors
        self._validate_inputs(domain_targets)

        # Detect mode and prepare parameters
        if is_legacy:
            # Legacy mode: use deprecated scalar fields
            initial_beta = self.config.initial_beta
            calibrate = frozenset(["cost"])
            param_order = ("cost",)
            x0 = [initial_beta]
            bounds = [(self.config.beta_bounds[0], self.config.beta_bounds[1])]
            target_params = TasteParameters.from_beta_cost(initial_beta)
            utility_attrs = None
            logger.info(
                "event=calibration_start domain=%s initial_beta=%f method=%s objective=%s mode=legacy",
                domain,
                initial_beta,
                method,
                self.config.objective_type,
            )
        else:
            # Generalized mode: use vector optimization
            calibrate = self.config.target_parameters.calibrate
            param_order = tuple(sorted(calibrate))
            x0 = [self.config.initial_values[p] for p in param_order]
            bounds = [self.config.bounds[p] for p in param_order]
            target_params = self.config.target_parameters
            utility_attrs = None  # TODO: pass from config if available
            logger.info(
                "event=calibration_start domain=%s n_params=%d params=%s "
                "method=%s objective=%s mode=generalized",
                domain,
                len(param_order),
                param_order,
                method,
                self.config.objective_type,
            )

        # 3. Build objective function
        if self.config.objective_type == "mse":
            objective = build_mse_objective(
                domain_targets,
                self.config.cost_matrix,
                self.config.from_states,
                target_params,
                calibrate,
                self.config.initial_values if not is_legacy else {},
                utility_attrs,
            )
        else:  # "log_likelihood"
            objective = build_log_likelihood_objective(
                domain_targets,
                self.config.cost_matrix,
                self.config.from_states,
                target_params,
                calibrate,
                self.config.initial_values if not is_legacy else {},
                utility_attrs,
            )

        # 4. Run scipy.optimize.minimize
        try:
            result = minimize(
                objective,
                x0=x0,
                method=method,
                bounds=bounds,
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

        # 5. Check convergence status (log warning, don't raise for backward compatibility)
        if not result.success:
            logger.warning(
                "event=calibration_no_convergence domain=%s iterations=%d "
                "message=%s",
                domain,
                int(result.nit),
                result.message,
            )
            # Note: We return result with convergence_flag=False for backward compatibility.
            # If scipy raised an exception (not just non-convergence), it would have been
            # caught in the try/except block above and raised as CalibrationOptimizationError.

        # 6. Extract gradient info
        gradient_norm: float | None = None
        if hasattr(result, "jac") and result.jac is not None:
            if is_legacy:
                gradient_norm = float(abs(result.jac[0]))
            else:
                # Compute L2 norm of gradient vector
                gradient_norm = float(math.sqrt(sum(g**2 for g in result.jac)))  # type: ignore[arg-type]

            # Warn if gradient is large after convergence (possible local minimum)
            if gradient_norm > 0.1:
                logger.warning(
                    "event=large_gradient domain=%s gradient_norm=%f "
                    "msg=Large gradient after convergence - possible local minimum",
                    domain,
                    gradient_norm,
                )

        # 7. Build optimized TasteParameters
        if is_legacy:
            optimized_taste = TasteParameters(beta_cost=float(result.x[0]))
            param_diags: dict[str, ParameterDiagnostics] = {}

            # Add legacy beta_cost diagnostics if gradient available
            if hasattr(result, "jac") and result.jac is not None:
                grad_val = float(abs(result.jac[0]))
                param_diags["beta_cost"] = ParameterDiagnostics(
                    optimized_value=float(result.x[0]),
                    initial_value=initial_beta,
                    absolute_change=abs(float(result.x[0]) - initial_beta),
                    relative_change_pct=(
                        abs(float(result.x[0]) - initial_beta)
                        / max(abs(initial_beta), 1e-10)
                        * 100
                    ),
                    at_lower_bound=abs(float(result.x[0]) - self.config.beta_bounds[0]) < 1e-10,
                    at_upper_bound=abs(float(result.x[0]) - self.config.beta_bounds[1]) < 1e-10,
                    gradient_component=grad_val,
                )
        else:
            optimized_taste = _build_generalized_taste_parameters(
                target_params,
                calibrate,
                result.x,
            )

            # Build ParameterDiagnostics for each calibrated parameter
            param_diags = {}
            for i, param_name in enumerate(param_order):
                if param_name in optimized_taste.asc:
                    optimized_value = optimized_taste.asc[param_name]
                else:
                    optimized_value = optimized_taste.betas[param_name]
                initial_value = self.config.initial_values[param_name]
                lower_bound, upper_bound = self.config.bounds[param_name]

                grad_val: float | None = None
                if hasattr(result, "jac") and result.jac is not None:
                    grad_val = float(result.jac[i])

                param_diags[param_name] = ParameterDiagnostics(
                    optimized_value=optimized_value,
                    initial_value=initial_value,
                    absolute_change=abs(optimized_value - initial_value),
                    relative_change_pct=(
                        abs(optimized_value - initial_value)
                        / max(abs(initial_value), 1e-10)
                        * 100
                    ),
                    at_lower_bound=abs(optimized_value - lower_bound) < 1e-10,
                    at_upper_bound=abs(optimized_value - upper_bound) < 1e-10,
                    gradient_component=grad_val,
                )

        # 8. Compute final simulated rates for comparison
        final_rates = compute_simulated_rates(
            self.config.cost_matrix,
            optimized_taste,
            self.config.from_states,
            self.config.cost_matrix.alternative_ids,
            utility_attrs,
        )

        # 9. Build per-target rate comparisons
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

        # 10. Build convergence warnings
        convergence_warnings: list[str] = []
        for param_name, diag in param_diags.items():
            if diag.at_lower_bound:
                convergence_warnings.append(f"{param_name} hit lower bound")
            elif diag.at_upper_bound:
                convergence_warnings.append(f"{param_name} hit upper bound")

        # 11. Build identifiability flags (low sensitivity detection)
        identifiability_flags: dict[str, str] = {}
        for param_name, diag in param_diags.items():
            if diag.gradient_component is not None:
                if diag.gradient_component < 1e-6 and not diag.at_lower_bound and not diag.at_upper_bound:
                    identifiability_flags[param_name] = "low_sensitivity"

        # TODO: Hessian-based correlation detection (requires scipy method with hess_inv)

        logger.info(
            "event=calibration_complete domain=%s optimized_params=%s iterations=%d "
            "converged=%s all_within_tolerance=%s objective_value=%f",
            domain,
            param_order if not is_legacy else ("beta_cost",),
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
            parameter_diagnostics=param_diags,
            convergence_warnings=convergence_warnings,
            identifiability_flags=identifiability_flags,
        )

    def _validate_inputs(self, domain_targets: CalibrationTargetSet) -> None:
        """Validate inputs before running optimization.

        Checks:
        1. Non-empty domain targets.
        2. All target to_state values exist in cost_matrix.alternative_ids.
        3. All target from_state values exist in from_states array.
        4. Consistency (duplicate check) via domain_targets.validate_consistency().
        5. Total weight sum > 0.0.
        6. Generalized mode: all calibrate params have initial_values and bounds.

        Raises:
            CalibrationOptimizationError: On any validation failure with a clear message.

        Story 15.2 / FR52 — Original validation.
        Story 21.7 / AC-5 — Extended validation for generalized mode.
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

        # 6. Generalized mode validation
        if not self.config.is_legacy_mode:
            # Validate all calibrate params have initial_values
            calibrate = self.config.target_parameters.calibrate
            missing_initial = calibrate - set(self.config.initial_values.keys())
            if missing_initial:
                raise CalibrationOptimizationError(
                    f"Missing initial_values for calibrated parameters {sorted(missing_initial)} "
                    f"in domain={domain!r}"
                )

            # Validate all calibrate params have bounds
            missing_bounds = calibrate - set(self.config.bounds.keys())
            if missing_bounds:
                raise CalibrationOptimizationError(
                    f"Missing bounds for calibrated parameters {sorted(missing_bounds)} "
                    f"in domain={domain!r}"
                )
