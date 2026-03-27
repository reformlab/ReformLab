# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Validation check registry and preflight checks — Story 20.7.

This module implements an extensible check registry pattern for pre-execution
validation. Built-in checks are registered at import time, allowing EPIC-21
Story 21.5 to add trust-status rules without modifying core code.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Callable, Literal

from reformlab.server.models import (
    PreflightRequest,
    PreflightResponse,
    ValidationCheckResult,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable

logger = logging.getLogger(__name__)

# Registry of validation checks
_VALIDATION_CHECKS: list[ValidationCheck] = []

# Track registered check IDs to prevent duplicates
_REGISTERED_CHECK_IDS: set[str] = set()


# =============================================================================
# Validation check protocol
# =============================================================================


class ValidationCheck:
    """A validation check that can be registered and executed.

    Extensibility pattern: EPIC-21 Story 21.5 can add checks by creating
    ValidationCheck instances and calling register_check().
    """

    def __init__(
        self,
        check_id: str,
        label: str,
        severity: Literal["error", "warning"],
        check_fn: Callable[[PreflightRequest], ValidationCheckResult | Awaitable[ValidationCheckResult]],
    ) -> None:
        """Initialize a validation check.

        Args:
            check_id: Unique identifier for this check
            label: Human-readable label for the check
            severity: "error" checks block execution; "warning" checks do not
            check_fn: Function that executes the check and returns a result
        """
        self.id = check_id
        self.label = label
        self.severity = severity
        self._check_fn = check_fn

    async def __call__(self, request: PreflightRequest) -> ValidationCheckResult:
        """Execute the check and return the result."""
        result = self._check_fn(request)
        # Handle both sync and async check functions
        if hasattr(result, "__await__"):
            return await result
        return result


def register_check(check: ValidationCheck) -> None:
    """Register a validation check in the global registry.

    Raises:
        ValueError: If a check with the same ID is already registered
    """
    if check.id in _REGISTERED_CHECK_IDS:
        raise ValueError(f"Validation check '{check.id}' is already registered")

    _VALIDATION_CHECKS.append(check)
    _REGISTERED_CHECK_IDS.add(check.id)
    logger.debug("Registered validation check: %s", check.id)


async def run_checks(request: PreflightRequest) -> PreflightResponse:
    """Run all registered validation checks and return aggregated results.

    AC-2: Returns passed, checks[], and warnings[] with check-level detail.
    """
    results = []

    for check in _VALIDATION_CHECKS:
        try:
            result = await check(request)
            results.append(result)
        except Exception as e:
            logger.exception("Validation check '%s' failed", check.id)
            # Treat check failure as a failed check result
            results.append(
                ValidationCheckResult(
                    id=check.id,
                    label=check.label,
                    passed=False,
                    severity=check.severity,
                    message=f"Check execution failed: {e}",
                )
            )

    # Determine overall pass status (only error-severity checks block execution)
    error_checks = [r for r in results if r.severity == "error"]
    passed = all(r.passed for r in error_checks)

    # Collect warnings from non-passing warning-severity checks
    warnings = [r.message for r in results if r.severity == "warning" and not r.passed]

    return PreflightResponse(
        passed=passed,
        checks=results,
        warnings=warnings,
    )


# =============================================================================
# Built-in validation checks
# =============================================================================


def _check_portfolio_selected(request: PreflightRequest) -> ValidationCheckResult:
    """Check that a portfolio is selected."""
    portfolio_name = request.scenario.get("portfolioName")

    if not portfolio_name or not isinstance(portfolio_name, str) or portfolio_name.strip() == "":
        return ValidationCheckResult(
            id="portfolio-selected",
            label="Portfolio selected",
            passed=False,
            severity="error",
            message="No portfolio selected",
        )

    return ValidationCheckResult(
        id="portfolio-selected",
        label="Portfolio selected",
        passed=True,
        severity="error",
        message=f"Portfolio '{portfolio_name}' selected",
    )


def _check_population_selected(request: PreflightRequest) -> ValidationCheckResult:
    """Check that at least one population is selected."""
    population_ids = request.scenario.get("populationIds")

    if not population_ids or not isinstance(population_ids, list):
        return ValidationCheckResult(
            id="population-selected",
            label="Population selected",
            passed=False,
            severity="error",
            message="No population selected",
        )

    # Check that at least one non-empty population ID is present
    has_valid_id = any(isinstance(pid, str) and pid.strip() for pid in population_ids)

    if not has_valid_id:
        return ValidationCheckResult(
            id="population-selected",
            label="Population selected",
            passed=False,
            severity="error",
            message="No valid population ID provided",
        )

    return ValidationCheckResult(
        id="population-selected",
        label="Population selected",
        passed=True,
        severity="error",
        message=f"{len(population_ids)} population(s) selected",
    )


def _check_time_horizon_valid(request: PreflightRequest) -> ValidationCheckResult:
    """Check that the time horizon is valid."""
    engine_config = request.scenario.get("engineConfig", {})

    if not isinstance(engine_config, dict):
        return ValidationCheckResult(
            id="time-horizon-valid",
            label="Time horizon valid",
            passed=False,
            severity="error",
            message="Engine configuration missing or invalid",
        )

    start_year = engine_config.get("startYear")
    end_year = engine_config.get("endYear")

    if not isinstance(start_year, int) or not isinstance(end_year, int):
        return ValidationCheckResult(
            id="time-horizon-valid",
            label="Time horizon valid",
            passed=False,
            severity="error",
            message="Start year and end year must be integers",
        )

    current_year = datetime.now(timezone.utc).year

    if start_year >= end_year:
        return ValidationCheckResult(
            id="time-horizon-valid",
            label="Time horizon valid",
            passed=False,
            severity="error",
            message=f"Start year ({start_year}) must be before end year ({end_year})",
        )

    if end_year - start_year > 50:
        return ValidationCheckResult(
            id="time-horizon-valid",
            label="Time horizon valid",
            passed=False,
            severity="error",
            message=f"Time horizon too long ({end_year - start_year} years), maximum is 50 years",
        )

    if start_year < current_year - 10:
        return ValidationCheckResult(
            id="time-horizon-valid",
            label="Time horizon valid",
            passed=False,
            severity="error",
            message=f"Start year ({start_year}) is too far in the past (current year: {current_year})",
        )

    return ValidationCheckResult(
        id="time-horizon-valid",
        label="Time horizon valid",
        passed=True,
        severity="error",
        message=f"Valid time horizon: {start_year} to {end_year} ({end_year - start_year} years)",
    )


def _check_investment_decisions_calibrated(request: PreflightRequest) -> ValidationCheckResult:
    """Check that investment decisions are calibrated (if enabled)."""
    engine_config = request.scenario.get("engineConfig", {})

    if not isinstance(engine_config, dict):
        return ValidationCheckResult(
            id="investment-decisions-calibrated",
            label="Investment decisions calibrated",
            passed=True,
            severity="warning",
            message="Engine configuration missing",
        )

    investment_enabled = engine_config.get("investmentDecisionsEnabled", False)

    if not investment_enabled:
        return ValidationCheckResult(
            id="investment-decisions-calibrated",
            label="Investment decisions calibrated",
            passed=True,
            severity="warning",
            message="Investment decisions not enabled",
        )

    # Check for calibration data placeholder
    # In a full implementation, this would check for actual calibration files
    logit_model = engine_config.get("logitModel")

    if not logit_model:
        return ValidationCheckResult(
            id="investment-decisions-calibrated",
            label="Investment decisions calibrated",
            passed=False,
            severity="warning",
            message="Investment decisions enabled but no logit model specified",
        )

    return ValidationCheckResult(
        id="investment-decisions-calibrated",
        label="Investment decisions calibrated",
        passed=True,
        severity="warning",
        message=f"Logit model configured: {logit_model}",
    )


def _check_memory_preflight(request: PreflightRequest) -> ValidationCheckResult:
    """Check memory requirements for the simulation.

    Reuses the existing check_memory_requirements() function from the runs module.
    """
    from reformlab.interfaces.api import ScenarioConfig, check_memory_requirements

    engine_config = request.scenario.get("engineConfig", {})

    if not isinstance(engine_config, dict):
        return ValidationCheckResult(
            id="memory-preflight",
            label="Memory requirements",
            passed=False,
            severity="error",
            message="Engine configuration missing",
        )

    try:
        # Build scenario config from request
        scenario_config = ScenarioConfig(
            template_name=request.template_name or "",
            policy={},
            start_year=engine_config.get("startYear", 2025),
            end_year=engine_config.get("endYear", 2030),
        )

        memory_result = check_memory_requirements(scenario_config)

        if memory_result.should_warn:
            return ValidationCheckResult(
                id="memory-preflight",
                label="Memory requirements",
                passed=True,  # Warning doesn't block execution
                severity="error",
                message=f"Memory warning: {memory_result.message}",
            )

        return ValidationCheckResult(
            id="memory-preflight",
            label="Memory requirements",
            passed=True,
            severity="error",
            message=f"Memory OK: {memory_result.estimate.available_gb:.1f} GB available",
        )

    except Exception as e:
        logger.exception("Memory check failed")
        return ValidationCheckResult(
            id="memory-preflight",
            label="Memory requirements",
            passed=False,
            severity="error",
            message=f"Memory check failed: {e}",
        )


def _check_exogenous_coverage(request: PreflightRequest) -> ValidationCheckResult:
    """Preflight check for exogenous time series coverage.

    Story 21.6 / AC3: Validates that exogenous series (if specified) have
    coverage for the scenario's year range.

    This check only executes if exogenous series are specified in the
    scenario configuration. Scenarios without exogenous inputs pass
    automatically (backward compatibility).
    """
    from reformlab.data.exogenous_loader import load_exogenous_asset
    from reformlab.orchestrator.exogenous import ExogenousContext

    engine_config = request.scenario.get("engineConfig", {})

    if not isinstance(engine_config, dict):
        return ValidationCheckResult(
            id="exogenous-coverage",
            label="Exogenous series coverage",
            passed=True,
            severity="warning",
            message="Engine configuration missing - cannot validate exogenous coverage",
        )

    # Check if exogenous series are specified
    exogenous_series = engine_config.get("exogenousSeries")
    if not exogenous_series:
        # No exogenous series configured - check passes
        return ValidationCheckResult(
            id="exogenous-coverage",
            label="Exogenous series coverage",
            passed=True,
            severity="warning",
            message="No exogenous series configured",
        )

    if not isinstance(exogenous_series, list):
        return ValidationCheckResult(
            id="exogenous-coverage",
            label="Exogenous series coverage",
            passed=False,
            severity="error",
            message="exogenousSeries must be a list of series names",
        )

    # Get year range
    start_year = engine_config.get("startYear")
    end_year = engine_config.get("endYear")

    if not isinstance(start_year, int) or not isinstance(end_year, int):
        return ValidationCheckResult(
            id="exogenous-coverage",
            label="Exogenous series coverage",
            passed=False,
            severity="error",
            message="Cannot validate exogenous coverage: startYear and endYear required",
        )

    # Load assets and validate actual coverage
    try:
        assets = []
        for series_name in exogenous_series:
            if not isinstance(series_name, str):
                return ValidationCheckResult(
                    id="exogenous-coverage",
                    label="Exogenous series coverage",
                    passed=False,
                    severity="error",
                    message=f"Invalid series name: {series_name!r} (must be string)",
                )
            assets.append(load_exogenous_asset(series_name))

        context = ExogenousContext.from_assets(tuple(assets))
        context.validate_coverage(start_year, end_year)

        series_count = len(exogenous_series)
        series_list = ", ".join(exogenous_series[:3])  # Show first 3
        if series_count > 3:
            series_list += f", ... ({series_count} total)"

        return ValidationCheckResult(
            id="exogenous-coverage",
            label="Exogenous series coverage",
            passed=True,
            severity="warning",
            message=f"All {series_count} series have coverage {start_year}-{end_year} ({series_list})",
        )
    except Exception as exc:
        return ValidationCheckResult(
            id="exogenous-coverage",
            label="Exogenous series coverage",
            passed=False,
            severity="error",
            message=f"Coverage validation failed: {exc}",
        )


# =============================================================================
# Register built-in checks at import time
# =============================================================================


def _register_builtin_checks() -> None:
    """Register all built-in validation checks."""
    checks = [
        ValidationCheck(
            check_id="portfolio-selected",
            label="Portfolio selected",
            severity="error",
            check_fn=_check_portfolio_selected,
        ),
        ValidationCheck(
            check_id="population-selected",
            label="Population selected",
            severity="error",
            check_fn=_check_population_selected,
        ),
        ValidationCheck(
            check_id="time-horizon-valid",
            label="Time horizon valid",
            severity="error",
            check_fn=_check_time_horizon_valid,
        ),
        ValidationCheck(
            check_id="investment-decisions-calibrated",
            label="Investment decisions calibrated",
            severity="warning",
            check_fn=_check_investment_decisions_calibrated,
        ),
        ValidationCheck(
            check_id="memory-preflight",
            label="Memory requirements",
            severity="error",
            check_fn=_check_memory_preflight,
        ),
        ValidationCheck(
            check_id="exogenous-coverage",
            label="Exogenous series coverage",
            severity="error",  # Changed to error since we now do actual validation
            check_fn=_check_exogenous_coverage,
        ),
    ]

    for check in checks:
        register_check(check)


# Auto-register on module import
_register_builtin_checks()
