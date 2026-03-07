"""Calibration validation against holdout data.

Implements holdout validation for calibrated discrete choice taste parameters.
Given calibrated β parameters, executes the model on a holdout dataset (different
time period or population subset) and computes gap metrics (MSE, MAE) for both
in-sample (training) and out-of-sample (holdout) comparisons side by side.

The validation is non-blocking: poor holdout fit does NOT raise an exception.
A HoldoutValidationResult is always returned; callers inspect all_within_tolerance
to decide whether to treat poor fit as an error.

Story 15.3 / FR53 — Calibration validation against holdout data.
"""

from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

import pyarrow as pa
import pyarrow.compute as pc

from reformlab.calibration.engine import compute_simulated_rates
from reformlab.calibration.errors import (
    CalibrationOptimizationError,
    CalibrationTargetLoadError,
    CalibrationTargetValidationError,
)
from reformlab.calibration.types import (
    CalibrationResult,
    CalibrationTargetSet,
    FitMetrics,
    HoldoutValidationResult,
    RateComparison,
)

if TYPE_CHECKING:
    from reformlab.discrete_choice.types import CostMatrix

logger = logging.getLogger(__name__)


# ============================== Public Functions ==============================


def compute_fit_metrics(
    rate_comparisons: tuple[RateComparison, ...],
) -> FitMetrics:
    """Compute unweighted aggregate fit metrics (MSE, MAE) from rate comparisons.

    Metrics are computed without applying CalibrationTarget.weight — all
    comparisons contribute equally regardless of their source weight.

    Args:
        rate_comparisons: Per-target observed vs simulated rate comparisons.

    Returns:
        FitMetrics with unweighted MSE, MAE, and tolerance summary.

    Raises:
        CalibrationOptimizationError: If rate_comparisons is empty.
    """
    n = len(rate_comparisons)
    if n == 0:
        raise CalibrationOptimizationError(
            "Cannot compute fit metrics from empty rate comparisons"
        )

    mse = sum(rc.absolute_error**2 for rc in rate_comparisons) / n
    mae = sum(rc.absolute_error for rc in rate_comparisons) / n
    all_within = all(rc.within_tolerance for rc in rate_comparisons)

    return FitMetrics(mse=mse, mae=mae, n_targets=n, all_within_tolerance=all_within)


def validate_holdout(
    calibration_result: CalibrationResult,
    holdout_targets: CalibrationTargetSet,
    holdout_cost_matrix: CostMatrix,
    holdout_from_states: pa.Array,
    *,
    rate_tolerance: float = 0.05,
) -> HoldoutValidationResult:
    """Validate calibrated parameters against holdout data.

    Executes the discrete choice model with the calibrated β parameters
    on a holdout dataset (different time period or population subset),
    computes gap metrics (MSE, MAE), and returns both training and holdout
    fit metrics side by side.

    Args:
        calibration_result: Result from CalibrationEngine.calibrate() containing
            the optimized TasteParameters and training rate comparisons.
        holdout_targets: Calibration targets for the holdout dataset (same format
            as training targets, loaded via load_calibration_targets()).
        holdout_cost_matrix: Pre-computed N×M CostMatrix for the holdout population.
        holdout_from_states: Length-N PyArrow array of household origin states
            for the holdout population.
        rate_tolerance: Maximum acceptable |simulated - observed| per target.
            Defaults to 0.05. Must be finite and > 0. Note: this tolerance
            applies only to holdout comparisons. training_fit.all_within_tolerance
            reflects the original calibration tolerance from CalibrationConfig,
            which may differ.

    Returns:
        HoldoutValidationResult with training_fit and holdout_fit side by side.

    Raises:
        CalibrationOptimizationError: If holdout inputs are invalid (non-positive
            rate_tolerance, empty targets, duplicate targets, unknown to_state,
            missing from_state, dimension mismatch).
    """
    domain = calibration_result.domain

    # 0. Validate rate_tolerance immediately (before any other logic)
    if not math.isfinite(rate_tolerance) or rate_tolerance <= 0.0:
        raise CalibrationOptimizationError(
            f"rate_tolerance={rate_tolerance!r} must be a finite positive number"
        )

    # 1. Filter holdout targets to domain
    holdout_domain_targets = holdout_targets.by_domain(domain)
    n_targets = len(holdout_domain_targets.targets)
    n_households = holdout_cost_matrix.n_households

    # 2. Log start
    logger.info(
        "event=holdout_validation_start domain=%s n_holdout_targets=%d n_households=%d",
        domain,
        n_targets,
        n_households,
    )

    # 3. Validate holdout inputs
    _validate_holdout_inputs(
        holdout_domain_targets,
        holdout_cost_matrix,
        holdout_from_states,
        domain,
    )

    # 4. Compute simulated rates on holdout data using calibrated β
    optimized_taste = calibration_result.optimized_parameters
    holdout_rates = compute_simulated_rates(
        holdout_cost_matrix,
        optimized_taste,
        holdout_from_states,
        holdout_cost_matrix.alternative_ids,
    )

    # 5. Build holdout rate comparisons
    holdout_comparisons_list: list[RateComparison] = []
    for t in holdout_domain_targets.targets:
        key = (t.from_state, t.to_state)
        sim_rate = holdout_rates.get(key, 0.0)
        abs_err = abs(sim_rate - t.observed_rate)
        holdout_comparisons_list.append(
            RateComparison(
                from_state=t.from_state,
                to_state=t.to_state,
                observed_rate=t.observed_rate,
                simulated_rate=sim_rate,
                absolute_error=abs_err,
                within_tolerance=abs_err <= rate_tolerance,
            )
        )
    holdout_comparisons = tuple(
        sorted(holdout_comparisons_list, key=lambda rc: (rc.from_state, rc.to_state))
    )

    # 6. Compute holdout fit metrics
    holdout_fit = compute_fit_metrics(holdout_comparisons)

    # 7. Compute training fit metrics from calibration result
    training_fit = compute_fit_metrics(calibration_result.rate_comparisons)

    # 8. Log completion
    logger.info(
        "event=holdout_validation_complete domain=%s holdout_mse=%f holdout_mae=%f "
        "training_mse=%f training_mae=%f all_within_tolerance=%s",
        domain,
        holdout_fit.mse,
        holdout_fit.mae,
        training_fit.mse,
        training_fit.mae,
        holdout_fit.all_within_tolerance,
    )

    return HoldoutValidationResult(
        domain=domain,
        training_fit=training_fit,
        holdout_fit=holdout_fit,
        holdout_rate_comparisons=holdout_comparisons,
        rate_tolerance=rate_tolerance,
    )


# ============================== Private Helpers ==============================


def _validate_holdout_inputs(
    holdout_domain_targets: CalibrationTargetSet,
    holdout_cost_matrix: CostMatrix,
    holdout_from_states: pa.Array,
    domain: str,
) -> None:
    """Validate holdout inputs before running validation.

    Raises:
        CalibrationOptimizationError: On any validation failure.
    """
    # 1. Non-empty holdout targets
    if len(holdout_domain_targets.targets) == 0:
        raise CalibrationOptimizationError(
            f"No holdout calibration targets for domain={domain!r}"
        )

    # 1b. Semantic consistency (duplicate rows, rate sums) — fail loudly
    try:
        holdout_domain_targets.validate_consistency()
    except (CalibrationTargetLoadError, CalibrationTargetValidationError) as exc:
        raise CalibrationOptimizationError(
            f"Holdout target consistency check failed for domain={domain!r}: {exc}"
        ) from exc

    # 1c. Reject null from_states — data contracts fail loudly
    if pc.any(pc.is_null(holdout_from_states)).as_py():
        raise CalibrationOptimizationError(
            f"holdout_from_states contains null values for domain={domain!r}; "
            "all household origin states must be non-null"
        )

    # 2. Dimension match
    if len(holdout_from_states) != holdout_cost_matrix.n_households:
        raise CalibrationOptimizationError(
            f"holdout from_states length ({len(holdout_from_states)}) must equal "
            f"holdout cost_matrix.n_households ({holdout_cost_matrix.n_households})"
        )

    # 3. All to_state values exist in holdout cost_matrix alternatives
    available_alts = set(holdout_cost_matrix.alternative_ids)
    unknown_alts = {t.to_state for t in holdout_domain_targets.targets} - available_alts
    if unknown_alts:
        raise CalibrationOptimizationError(
            f"Unknown holdout to_state values {sorted(unknown_alts)!r} in domain={domain!r}; "
            f"expected one of {sorted(available_alts)!r}"
        )

    # 4. All from_state values exist in holdout from_states array
    available_from: set[str] = set(pc.unique(holdout_from_states).to_pylist())
    target_from = {t.from_state for t in holdout_domain_targets.targets}
    missing_from = target_from - available_from
    if missing_from:
        raise CalibrationOptimizationError(
            f"Missing holdout from_state values {sorted(missing_from)!r} "
            f"from provided holdout_from_states in domain={domain!r}"
        )
