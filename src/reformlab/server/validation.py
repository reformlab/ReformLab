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

    # Collect warnings from warning-severity checks that actively report a caveat.
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
        # Resolve population path so memory estimate uses actual row count
        population_path = None
        if request.population_id:
            try:
                from reformlab.server.dependencies import get_population_resolver

                resolver = get_population_resolver()
                resolved = resolver.resolve(request.population_id)
                population_path = resolved.data_path
            except Exception:
                pass  # Fall back to default estimate

        # Build scenario config from request
        scenario_config = ScenarioConfig(
            template_name=request.template_name or "",
            policy={},
            start_year=engine_config.get("startYear", 2025),
            end_year=engine_config.get("endYear", 2030),
            population_path=population_path,
        )

        memory_result = check_memory_requirements(scenario_config)

        if memory_result.should_warn:
            return ValidationCheckResult(
                id="memory-preflight",
                label="Memory requirements",
                passed=False,
                severity="warning",
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


def _check_trust_status(request: PreflightRequest) -> ValidationCheckResult:
    """Preflight check for evidence asset trust status.

    Story 21.5: Evaluates trust status of all scenario assets (exogenous series)
    and warns if any are non-production-safe. Warning-severity only — never blocks.
    """
    from reformlab.data.exogenous_loader import load_exogenous_asset
    from reformlab.data.trust_rules import (
        TrustCheckResult,
        check_asset_trust,
        summarize_trust_warnings,
    )

    engine_config = request.scenario.get("engineConfig", {})

    if not isinstance(engine_config, dict):
        return ValidationCheckResult(
            id="trust-status",
            label="Evidence trust status",
            passed=True,
            severity="warning",
            message="Engine configuration missing — cannot verify trust status",
        )

    exogenous_series = engine_config.get("exogenousSeries")
    if not exogenous_series or not isinstance(exogenous_series, list):
        return ValidationCheckResult(
            id="trust-status",
            label="Evidence trust status",
            passed=True,
            severity="warning",
            message="No exogenous series configured — nothing to check",
        )

    trust_results: list[TrustCheckResult] = []
    for series_name in exogenous_series:
        if not isinstance(series_name, str):
            continue
        try:
            asset = load_exogenous_asset(series_name)
            trust_results.append(check_asset_trust(asset.descriptor))
        except Exception:
            logger.debug("Could not load asset '%s' for trust check", series_name)

    if not trust_results:
        return ValidationCheckResult(
            id="trust-status",
            label="Evidence trust status",
            passed=True,
            severity="warning",
            message="Could not verify trust status — no assets loaded",
        )

    summary = summarize_trust_warnings(tuple(trust_results))

    if summary is not None:
        return ValidationCheckResult(
            id="trust-status",
            label="Evidence trust status",
            passed=False,
            severity="warning",
            message=summary,
        )

    return ValidationCheckResult(
        id="trust-status",
        label="Evidence trust status",
        passed=True,
        severity="warning",
        message="All evidence assets are production-safe",
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
# Story 23.5: Runtime and population validation checks
# =============================================================================


def _check_runtime_support(request: PreflightRequest) -> ValidationCheckResult:
    """Story 23.5 / AC-1: Validate runtime mode is available.

    Live always passes; replay requires precomputed data.
    """
    runtime_mode = request.runtime_mode  # New field on PreflightRequest

    if runtime_mode == "replay":
        # Verify precomputed data exists
        try:
            from reformlab.server.dependencies import _create_replay_adapter
            _create_replay_adapter()  # Raises if no data files
        except (FileNotFoundError, ValueError, OSError):
            return ValidationCheckResult(
                id="runtime-support",
                label="Runtime support",
                passed=False,
                severity="error",
                message=(
                    "Replay mode requires precomputed output files, "
                    "but none were found in the data directory. "
                    "Run in live mode (default) or ensure precomputed data exists."
                ),
            )
        return ValidationCheckResult(
            id="runtime-support",
            label="Runtime support",
            passed=True,
            severity="error",
            message="Replay mode available with precomputed data",
        )

    # Default: live mode always supported
    return ValidationCheckResult(
        id="runtime-support",
        label="Runtime support",
        passed=True,
        severity="error",
        message="Live execution mode (default)",
    )


def _check_population_executable(request: PreflightRequest) -> ValidationCheckResult:
    """Story 23.5 / AC-1, AC-4: Validate population is executable.

    Validates that the selected population_id resolves to an executable dataset
    and has minimum required columns for live execution.
    """
    if not request.population_id:
        return ValidationCheckResult(
            id="population-executable",
            label="Population executable",
            passed=True,
            severity="error",
            message="No population selected — run will use default data",
        )

    import pyarrow as pa
    import pyarrow.csv as pa_csv
    import pyarrow.parquet as pq

    from reformlab.server.dependencies import get_population_resolver
    from reformlab.server.population_resolver import PopulationResolutionError

    resolver = get_population_resolver()
    try:
        resolved = resolver.resolve(request.population_id)

        # AC-4: Lightweight schema validation — check for minimum required columns
        # Required columns for live execution (minimum viable schema):
        #   - household_id: entity identifier
        #   - income: pre-tax household income
        #   - disposable_income: post-tax household income (needed for redistribution)
        #   - carbon_tax: carbon tax liability (needed for policy scenarios)
        required_columns = {"household_id", "income", "disposable_income", "carbon_tax"}
        try:
            suffixes = tuple(part.lower() for part in resolved.data_path.suffixes)
            if suffixes[-2:] == (".csv", ".gz") or suffixes[-1:] == (".csv",):
                reader = pa_csv.open_csv(resolved.data_path)
                try:
                    schema = reader.schema
                finally:
                    reader.close()
            elif suffixes[-1:] in ((".parquet",), (".pq",)):
                # Read only schema, not full data (for performance)
                schema = pq.read_schema(resolved.data_path)
            else:
                return ValidationCheckResult(
                    id="population-executable",
                    label="Population executable",
                    passed=False,
                    severity="error",
                    message=(
                        f"Population '{request.population_id}' uses unsupported file format: "
                        f"{resolved.data_path.suffix or '(none)'}"
                    ),
                )
            existing_columns = set(schema.names)
            missing_columns = required_columns - existing_columns

            if missing_columns:
                missing_str = ", ".join(sorted(missing_columns))
                return ValidationCheckResult(
                    id="population-executable",
                    label="Population executable",
                    passed=False,
                    severity="error",
                    message=(
                        f"Population '{request.population_id}' is incompatible with live execution. "
                        f"Missing required columns: {missing_str}"
                    ),
                )
        except (FileNotFoundError, OSError, pa.ArrowException) as e:
            return ValidationCheckResult(
                id="population-executable",
                label="Population executable",
                passed=False,
                severity="error",
                message=(
                    f"Population '{request.population_id}' cannot be read: {e}"
                ),
            )

        return ValidationCheckResult(
            id="population-executable",
            label="Population executable",
            passed=True,
            severity="error",
            message=(
                f"Population '{request.population_id}' resolved "
                f"({resolved.source}, {resolved.row_count or '?'} rows)"
            ),
        )
    except PopulationResolutionError as exc:
        available = getattr(exc, "available_ids", [])
        available_str = ", ".join(available[:5]) if available else "none"
        return ValidationCheckResult(
            id="population-executable",
            label="Population executable",
            passed=False,
            severity="error",
            message=(
                f"Population '{request.population_id}' cannot be resolved. "
                f"Available populations: {available_str}"
            ),
        )


def _check_runtime_info(request: PreflightRequest) -> ValidationCheckResult:
    """Story 23.5 / AC-6, AC-7: Informational runtime status.

    Returns warning-severity check results in warnings[].
    """
    from reformlab.computation.mock_adapter import MockAdapter
    from reformlab.server.dependencies import get_adapter

    if request.runtime_mode == "replay":
        return ValidationCheckResult(
            id="runtime-info",
            label="Runtime status",
            passed=False,  # Warning, not error
            severity="warning",
            message="Using replay mode — results come from precomputed outputs",
        )

    adapter = get_adapter()

    if isinstance(adapter, MockAdapter):
        return ValidationCheckResult(
            id="runtime-info",
            label="Runtime status",
            passed=False,  # Warning, not error
            severity="warning",
            message=(
                "Running with MockAdapter — results use synthetic data, "
                "not live OpenFisca computation. Install OpenFisca for live runs."
            ),
        )

    # Live mode with real adapter: clean pass, no false warnings
    return ValidationCheckResult(
        id="runtime-info",
        label="Runtime status",
        passed=True,
        severity="warning",
        message="Live OpenFisca execution",
    )


# =============================================================================
# Story 24.3: Portfolio runtime availability validation
# =============================================================================


def _check_portfolio_runtime_availability(request: PreflightRequest) -> ValidationCheckResult:
    """Story 24.3 / AC-1, AC-4: Validate portfolio policies are live-ready.

    Checks that all policies in the selected portfolio have runtime_availability='live_ready'.
    Blocks execution if any policy is unavailable for live execution.

    NOTE: This check only applies to runtime_mode=live. For runtime_mode=replay,
    availability is bypassed.
    """
    # Story 24.3 code review fix: bypass availability check for replay mode
    if request.runtime_mode == "replay":
        return ValidationCheckResult(
            id="portfolio-runtime-availability",
            label="Portfolio runtime availability",
            passed=True,
            severity="error",
            message="Replay mode: runtime availability bypassed",
        )

    from reformlab.server.dependencies import get_registry
    from reformlab.templates.portfolios.portfolio import PolicyPortfolio
    from reformlab.templates.registry import RegistryError, ScenarioNotFoundError

    portfolio_name = request.scenario.get("portfolioName")
    if not portfolio_name:
        return ValidationCheckResult(
            id="portfolio-runtime-availability",
            label="Portfolio runtime availability",
            passed=True,
            severity="error",
            message="No portfolio selected",
        )

    registry = get_registry()
    try:
        entry = registry.get(portfolio_name)
    except (KeyError, ScenarioNotFoundError, RegistryError):
        return ValidationCheckResult(
            id="portfolio-runtime-availability",
            label="Portfolio runtime availability",
            passed=False,
            severity="error",
            message=f"Portfolio '{portfolio_name}' not found in registry",
        )

    if not isinstance(entry, PolicyPortfolio):
        return ValidationCheckResult(
            id="portfolio-runtime-availability",
            label="Portfolio runtime availability",
            passed=True,
            severity="error",
            message=f"'{portfolio_name}' is not a portfolio",
        )

    # Check runtime availability for each policy
    # Runtime availability is determined by policy type
    # Story 24.2: subsidy, vehicle_malus, energy_poverty_aid are now live_ready
    from reformlab.server.routes.templates import LIVE_READY_TYPES

    unavailable_policies = []
    for i, policy_cfg in enumerate(entry.policies):
        if policy_cfg.policy_type is None:
            # Story 24.3 code review fix: flag None policy_type as error
            policy_name = policy_cfg.name or f"policy_{i}"
            unavailable_policies.append(
                f"  - policy[{i}]: '{policy_name}' (policy_type is None — malformed portfolio entry)"
            )
            continue
        policy_type_str = policy_cfg.policy_type.value
        if policy_type_str not in LIVE_READY_TYPES:
            policy_name = policy_cfg.name or policy_type_str
            unavailable_policies.append(f"  - policy[{i}]: '{policy_name}' ({policy_type_str})")

    if unavailable_policies:
        unavailable_list = "\n".join(unavailable_policies)
        return ValidationCheckResult(
            id="portfolio-runtime-availability",
            label="Portfolio runtime availability",
            passed=False,
            severity="error",
            message=(
                f"Portfolio '{portfolio_name}' contains policies unavailable for live execution:\n"
                f"{unavailable_list}\n"
                f"Supported types for live execution: {', '.join(sorted(LIVE_READY_TYPES))}"
            ),
        )

    policy_count = entry.policy_count
    return ValidationCheckResult(
        id="portfolio-runtime-availability",
        label="Portfolio runtime availability",
        passed=True,
        severity="error",
        message=f"All {policy_count} policies in portfolio are live-ready",
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
        ValidationCheck(
            check_id="trust-status",
            label="Evidence trust status",
            severity="warning",
            check_fn=_check_trust_status,
        ),
        # Story 23.5 / AC-1, AC-4, AC-6, AC-7: Runtime and population validation checks
        ValidationCheck(
            check_id="runtime-support",
            label="Runtime support",
            severity="error",
            check_fn=_check_runtime_support,
        ),
        ValidationCheck(
            check_id="population-executable",
            label="Population executable",
            severity="error",
            check_fn=_check_population_executable,
        ),
        ValidationCheck(
            check_id="runtime-info",
            label="Runtime status",
            severity="warning",
            check_fn=_check_runtime_info,
        ),
        # Story 24.3 / AC-1, AC-4: Portfolio runtime availability validation
        ValidationCheck(
            check_id="portfolio-runtime-availability",
            label="Portfolio runtime availability",
            severity="error",
            check_fn=_check_portfolio_runtime_availability,
        ),
    ]

    for check in checks:
        register_check(check)


# Auto-register on module import
_register_builtin_checks()
