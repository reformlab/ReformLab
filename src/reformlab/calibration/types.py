# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Calibration target domain types.

Defines CalibrationTarget and CalibrationTargetSet as immutable frozen
dataclasses representing observed real-world transition rates (e.g., vehicle
adoption from ADEME/SDES) used to calibrate discrete choice taste parameters.

Also provides CalibrationConfig, CalibrationResult, RateComparison, FitMetrics,
and HoldoutValidationResult used by the calibration engine and validation module.

Story 15.1 / FR52 — Define calibration target format and load observed transition rates.
Story 15.2 / FR52 — CalibrationEngine with objective function optimization.
Story 15.3 / FR53 — Calibration validation against holdout data.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import pyarrow as pa

from reformlab.calibration.errors import (
    CalibrationOptimizationError,
    CalibrationTargetLoadError,
    CalibrationTargetValidationError,
)

if TYPE_CHECKING:
    from reformlab.discrete_choice.types import CostMatrix, TasteParameters

logger = logging.getLogger(__name__)

# ============================== Target Dataclass ==============================


@dataclass(frozen=True)
class CalibrationTarget:
    """A single observed transition rate from real-world institutional data.

    Attributes:
        domain: Decision domain (e.g., ``'vehicle'``, ``'heating'``).
        period: Reference year (e.g., ``2022``).
        from_state: Origin state (e.g., ``'petrol'``, ``'gas'``).
        to_state: Destination alternative (e.g., ``'buy_electric'``, ``'heat_pump'``).
        observed_rate: Fraction of households in ``from_state`` that chose ``to_state``.
            Must be in [0.0, 1.0].
        source_label: Human-readable data source identifier (e.g., ``'SDES vehicle fleet 2022'``).
        source_metadata: Optional key-value metadata (dataset id, URL, vintage year, etc.).
        weight: Non-negative weight for this target in the objective function.
            Defaults to 1.0. A weight of 0.0 effectively excludes the target.
    """

    domain: str
    period: int
    from_state: str
    to_state: str
    observed_rate: float
    source_label: str
    source_metadata: dict[str, str] = field(default_factory=dict)
    weight: float = 1.0

    def __post_init__(self) -> None:
        if not self.domain:
            raise CalibrationTargetValidationError("domain must be non-empty")
        if not self.from_state:
            raise CalibrationTargetValidationError("from_state must be non-empty")
        if not self.to_state:
            raise CalibrationTargetValidationError("to_state must be non-empty")
        if not (0.0 <= self.observed_rate <= 1.0):
            raise CalibrationTargetValidationError(
                f"observed_rate={self.observed_rate!r} is out of range; must be in [0.0, 1.0]"
            )
        if not math.isfinite(self.weight) or self.weight < 0.0:
            raise CalibrationTargetValidationError(
                f"weight={self.weight!r} must be a finite non-negative number"
            )


# ============================== Target Set ==============================


@dataclass(frozen=True)
class CalibrationTargetSet:
    """Immutable, validated collection of calibration targets across domains and periods.

    Attributes:
        targets: All calibration targets held in this set.
    """

    targets: tuple[CalibrationTarget, ...]

    def by_domain(self, domain: str) -> CalibrationTargetSet:
        """Return a new CalibrationTargetSet containing only targets for ``domain``.

        Given a domain name, when called on a multi-domain set, returns a filtered
        set with only that domain's targets. Returns an empty set if no match.
        """
        filtered = tuple(t for t in self.targets if t.domain == domain)
        return CalibrationTargetSet(targets=filtered)

    def validate_consistency(self) -> None:
        """Assert semantic consistency of the target collection.

        Checks performed (in order):

        1. **Duplicate detection** — ``(domain, period, from_state, to_state)`` must be
           unique. Raises :class:`CalibrationTargetLoadError` immediately.

        2. **Rate sum constraint** — For each ``(domain, period, from_state)`` group,
           the sum of ``observed_rate`` values must be ≤ 1.0 + 1e-9.
           Raises :class:`CalibrationTargetValidationError` on violation.

        Raises:
            CalibrationTargetLoadError: Duplicate ``(domain, period, from_state, to_state)`` row.
            CalibrationTargetValidationError: Rate sum exceeds ``1.0 + 1e-9`` for any group.
        """
        # --- Duplicate detection (always a hard error) ---
        seen: set[tuple[str, int, str, str]] = set()
        for t in self.targets:
            key = (t.domain, t.period, t.from_state, t.to_state)
            if key in seen:
                raise CalibrationTargetLoadError(
                    f"duplicate row detected: domain={t.domain!r} period={t.period!r} "
                    f"from_state={t.from_state!r} to_state={t.to_state!r} — "
                    "deduplicate before loading"
                )
            seen.add(key)

        # --- Rate sum constraint ---
        group_sums: dict[tuple[str, int, str], float] = {}
        for t in self.targets:
            group_key = (t.domain, t.period, t.from_state)
            group_sums[group_key] = group_sums.get(group_key, 0.0) + t.observed_rate

        for (domain, period, from_state), total in group_sums.items():
            if total > 1.0 + 1e-9:
                raise CalibrationTargetValidationError(
                    f"rates sum to {total:.10f} > 1.0 for group "
                    f"domain={domain!r} period={period!r} from_state={from_state!r}"
                )

        logger.debug(
            "event=consistency_validated n_groups=%d n_targets=%d",
            len(group_sums),
            len(self.targets),
        )

    def to_governance_entry(self, *, source_label: str = "calibration_targets") -> dict[str, Any]:
        """Return an AssumptionEntry-compatible dict for governance manifests.

        Given a CalibrationTargetSet, when called, returns a dict with
        ``key``, ``value``, ``source``, and ``is_default`` fields compatible
        with the governance manifest format (Story 15.4).
        """
        return {
            "key": "calibration_targets",
            "value": {
                "domains": sorted({t.domain for t in self.targets}),
                "n_targets": len(self.targets),
                "periods": sorted({t.period for t in self.targets}),
                "sources": sorted({t.source_label for t in self.targets}),
            },
            "source": source_label,
            "is_default": False,
        }


# ============================== Story 15.2: Engine Types ==============================


@dataclass(frozen=True)
class RateComparison:
    """Per-target comparison of observed vs simulated transition rates.

    Attributes:
        from_state: Origin state for this comparison.
        to_state: Destination alternative for this comparison.
        observed_rate: The target observed rate from institutional data.
        simulated_rate: The rate produced by the optimized model.
        absolute_error: Absolute difference |simulated_rate - observed_rate|.
        within_tolerance: True if absolute_error <= CalibrationConfig.rate_tolerance.
    """

    from_state: str
    to_state: str
    observed_rate: float
    simulated_rate: float
    absolute_error: float
    within_tolerance: bool


@dataclass(frozen=True)
class FitMetrics:
    """Aggregate fit metrics for a set of rate comparisons.

    Used to summarize both in-sample (training) and out-of-sample (holdout)
    fit quality for side-by-side comparison.

    Attributes:
        mse: Mean Squared Error across all rate comparisons.
        mae: Mean Absolute Error across all rate comparisons.
        n_targets: Number of rate comparisons summarized.
        all_within_tolerance: True if all comparisons are within tolerance.

    Story 15.3 / FR53 — Calibration validation against holdout data.
    """

    mse: float
    mae: float
    n_targets: int
    all_within_tolerance: bool

    def __post_init__(self) -> None:
        if self.n_targets <= 0:
            raise CalibrationOptimizationError(
                f"n_targets={self.n_targets!r} must be > 0"
            )
        if not math.isfinite(self.mse) or self.mse < 0.0:
            raise CalibrationOptimizationError(
                f"mse={self.mse!r} must be a finite non-negative number"
            )
        if not math.isfinite(self.mae) or self.mae < 0.0:
            raise CalibrationOptimizationError(
                f"mae={self.mae!r} must be a finite non-negative number"
            )


@dataclass(frozen=True)
class CalibrationResult:
    """Result of a calibration optimization run.

    Contains the optimized β coefficient, diagnostics, and per-target
    rate comparisons for governance and audit purposes.

    Attributes:
        optimized_parameters: TasteParameters with the calibrated beta_cost.
        domain: The calibrated decision domain.
        objective_type: ``'mse'`` or ``'log_likelihood'``.
        objective_value: Final objective function value at the optimized point.
        convergence_flag: True if the optimizer converged successfully.
        iterations: Number of optimizer iterations performed.
        gradient_norm: Absolute gradient norm at convergence, or None for
            gradient-free methods (e.g., Nelder-Mead).
        method: scipy optimizer method used (e.g., ``'L-BFGS-B'``).
        rate_comparisons: Per-target observed vs simulated rate comparisons.
        all_within_tolerance: True if all rate_comparisons are within_tolerance.
    """

    optimized_parameters: TasteParameters
    domain: str
    objective_type: str
    objective_value: float
    convergence_flag: bool
    iterations: int
    gradient_norm: float | None
    method: str
    rate_comparisons: tuple[RateComparison, ...]
    all_within_tolerance: bool

    def to_governance_entry(self, *, source_label: str = "calibration_engine") -> dict[str, Any]:
        """Return an AssumptionEntry-compatible dict for governance manifests.

        Given a CalibrationResult, when called, returns a dict compatible
        with the governance manifest format (Story 15.4).
        """
        return {
            "key": "calibration_result",
            "value": {
                "domain": self.domain,
                "optimized_beta_cost": self.optimized_parameters.beta_cost,
                "objective_type": self.objective_type,
                "final_objective_value": self.objective_value,
                "convergence_flag": self.convergence_flag,
                "iterations": self.iterations,
                "gradient_norm": self.gradient_norm,
                "method": self.method,
                "all_within_tolerance": self.all_within_tolerance,
                "n_targets": len(self.rate_comparisons),
            },
            "source": source_label,
            "is_default": False,
        }


@dataclass(frozen=True)
class CalibrationConfig:
    """Configuration for a single-domain calibration run.

    Attributes:
        targets: All available calibration targets (may be multi-domain;
            engine filters by ``domain``).
        cost_matrix: Pre-computed N×M CostMatrix for the domain.
        from_states: Length-N PyArrow array of household origin states.
        domain: Decision domain to calibrate (e.g., ``'vehicle'``).
        initial_beta: Starting β_cost value for the optimizer.
        objective_type: ``'mse'`` or ``'log_likelihood'``.
        method: scipy optimizer method (e.g., ``'L-BFGS-B'``, ``'Nelder-Mead'``).
        max_iterations: Maximum optimizer iterations.
        tolerance: Optimizer convergence tolerance (ftol).
        beta_bounds: (lower, upper) bounds on beta_cost; both exclusive ends.
        rate_tolerance: Maximum acceptable |simulated - observed| per target.
    """

    targets: CalibrationTargetSet
    cost_matrix: CostMatrix
    from_states: pa.Array
    domain: str
    initial_beta: float = -0.01
    objective_type: str = "mse"
    method: str = "L-BFGS-B"
    max_iterations: int = 100
    tolerance: float = 1e-8
    beta_bounds: tuple[float, float] = (-1.0, 0.0)
    rate_tolerance: float = 0.05

    def __post_init__(self) -> None:
        if self.objective_type not in ("mse", "log_likelihood"):
            raise CalibrationOptimizationError(
                f"objective_type={self.objective_type!r} must be 'mse' or 'log_likelihood'"
            )
        if self.max_iterations <= 0:
            raise CalibrationOptimizationError(
                f"max_iterations={self.max_iterations!r} must be > 0"
            )
        if self.beta_bounds[0] >= self.beta_bounds[1]:
            raise CalibrationOptimizationError(
                f"beta_bounds={self.beta_bounds!r}: lower bound must be < upper bound"
            )
        if self.rate_tolerance <= 0.0:
            raise CalibrationOptimizationError(
                f"rate_tolerance={self.rate_tolerance!r} must be > 0.0"
            )
        if len(self.from_states) != self.cost_matrix.n_households:
            raise CalibrationOptimizationError(
                f"from_states length ({len(self.from_states)}) must equal "
                f"cost_matrix.n_households ({self.cost_matrix.n_households})"
            )


# ============================== Story 15.3: Holdout Validation Types ==============================


@dataclass(frozen=True)
class HoldoutValidationResult:
    """Result of holdout validation with side-by-side training/holdout metrics.

    Provides both in-sample (training) and out-of-sample (holdout) fit
    metrics so the analyst can assess whether calibrated parameters
    generalize beyond the training data.

    Attributes:
        domain: Decision domain that was validated.
        training_fit: In-sample aggregate fit metrics from calibration.
        holdout_fit: Out-of-sample aggregate fit metrics from holdout validation.
        holdout_rate_comparisons: Per-target observed vs simulated comparisons on holdout.
        rate_tolerance: Tolerance threshold used for holdout within_tolerance checks.
            Note: training_fit.all_within_tolerance reflects the original calibration
            tolerance from CalibrationConfig, which may differ. For a fair side-by-side
            comparison, use the same tolerance here as in CalibrationConfig.

    Story 15.3 / FR53 — Calibration validation against holdout data.
    """

    domain: str
    training_fit: FitMetrics
    holdout_fit: FitMetrics
    holdout_rate_comparisons: tuple[RateComparison, ...]
    rate_tolerance: float

    def to_governance_entry(self, *, source_label: str = "holdout_validation") -> dict[str, Any]:
        """Return an AssumptionEntry-compatible dict for governance manifests.

        Given a HoldoutValidationResult, when called, returns a dict compatible
        with the governance manifest format (Story 15.4).
        """
        return {
            "key": "holdout_validation",
            "value": {
                "domain": self.domain,
                "holdout_rate_tolerance": self.rate_tolerance,
                "training": {
                    "mse": self.training_fit.mse,
                    "mae": self.training_fit.mae,
                    "n_targets": self.training_fit.n_targets,
                    "all_within_tolerance": self.training_fit.all_within_tolerance,
                },
                "holdout": {
                    "mse": self.holdout_fit.mse,
                    "mae": self.holdout_fit.mae,
                    "n_targets": self.holdout_fit.n_targets,
                    "all_within_tolerance": self.holdout_fit.all_within_tolerance,
                },
            },
            "source": source_label,
            "is_default": False,
        }
