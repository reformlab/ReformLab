# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Simulation execution routes."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Literal, cast

from fastapi import APIRouter, Depends, HTTPException

from reformlab.server.dependencies import (
    ResultCache,
    get_adapter,
    get_population_resolver,
    get_registry,
    get_result_cache,
    get_result_store,
)
from reformlab.server.models import (
    MemoryCheckRequest,
    MemoryCheckResponse,
    RunRequest,
    RunResponse,
)

if TYPE_CHECKING:
    from reformlab.computation.adapter import ComputationAdapter
    from reformlab.interfaces.api import SimulationResult
    from reformlab.server.result_store import ResultStore
    from reformlab.templates.registry import ScenarioRegistry

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=RunResponse)
async def run_simulation(
    body: RunRequest,
    cache: ResultCache = Depends(get_result_cache),
    store: ResultStore = Depends(get_result_store),
    registry: ScenarioRegistry = Depends(get_registry),
) -> RunResponse:
    """Execute a simulation synchronously and return the result.

    MVP: Blocks until simulation completes (<10s for 100k households).
    Auto-saves run metadata to persistent store on both success and failure.

    Dispatch logic:
    - ``portfolio_name`` provided → load portfolio from registry, execute
      all policies via PortfolioComputationStep
    - ``template_name`` provided → existing single-policy path
    - Both provided → 422 error
    """
    _validate_run_dispatch(body)

    if body.portfolio_name and body.runtime_mode == "live":
        _ensure_portfolio_live_ready(body.portfolio_name, registry)

    adapter = _select_adapter(body)
    population_path, population_source = _resolve_population(body.population_id)
    template_name = body.template_name or ""

    run_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()
    result: SimulationResult | None = None
    status = "failed"
    row_count = 0
    portfolio_policy_count: int | None = None
    portfolio_resolution_strategy: str | None = None

    try:
        if body.portfolio_name:
            result, portfolio_policy_count, portfolio_resolution_strategy = _run_portfolio(
                body=body,
                adapter=adapter,
                registry=registry,
                population_path=population_path,
                population_id=body.population_id,  # Story 23.3 / AC-2
                population_source=population_source,  # Story 23.3 / AC-2
            )
        else:
            result = _run_single_scenario(
                body=body,
                adapter=adapter,
                template_name=template_name,
                population_path=population_path,
                population_source=population_source,
            )

        _log_runtime_mode_mismatch(result, body.runtime_mode, run_id)
        result = _with_population_provenance(
            result,
            population_id=body.population_id,
            population_source=population_source,
        )

        cache.store(run_id, result)
        status = "completed" if result.success else "failed"
        row_count = result.panel_output.table.num_rows if result.panel_output else 0
    finally:
        finished_at = datetime.now(timezone.utc).isoformat()
        _persist_run_outputs(
            store=store,
            body=body,
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            template_name=template_name,
            result=result,
            status=status,
            row_count=row_count,
            population_source=population_source,
            portfolio_policy_count=portfolio_policy_count,
            portfolio_resolution_strategy=portfolio_resolution_strategy,
        )

    if result is None:
        # Re-raise will have already propagated; this branch is unreachable
        # but satisfies type checker
        raise RuntimeError("Simulation failed with no result")  # pragma: no cover

    return _build_run_response(run_id, result, row_count, population_source)


def _validate_run_dispatch(body: RunRequest) -> None:
    """Validate request fields that depend on route-level dispatch semantics."""
    if body.portfolio_name and body.template_name:
        raise HTTPException(
            status_code=422,
            detail={
                "what": "Ambiguous run request",
                "why": "Both portfolio_name and template_name provided",
                "fix": "Specify portfolio_name or template_name, not both",
            },
        )


def _select_adapter(body: RunRequest) -> ComputationAdapter:
    """Select the computation adapter for live or replay execution."""
    if body.runtime_mode != "replay":
        # Story 23.4 / AC-1: Default live adapter via global singleton
        return get_adapter()

    # Story 23.4 / AC-2: Replay mode creates its own precomputed adapter
    try:
        from reformlab.server.dependencies import _create_replay_adapter

        return _create_replay_adapter()
    except (FileNotFoundError, ValueError, OSError) as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "what": "Replay mode unavailable",
                "why": f"No precomputed output files found: {str(exc)}",
                "fix": (
                    "Run in live mode (default) or ensure "
                    "precomputed data files exist in the data directory"
                ),
            },
        ) from exc


def _resolve_population(population_id: str | None) -> tuple[Path | None, str | None]:
    """Resolve a request population ID into an executable data path and source."""
    if not population_id:
        return None, None

    from reformlab.server.population_resolver import PopulationResolutionError

    resolver = get_population_resolver()
    try:
        resolved = resolver.resolve(population_id)
    except PopulationResolutionError as exc:
        raise HTTPException(
            status_code=404,
            detail=exc.args[0],  # Already {"what", "why", "fix"} format
        ) from exc
    return resolved.data_path, resolved.source


def _run_single_scenario(
    *,
    body: RunRequest,
    adapter: ComputationAdapter,
    template_name: str,
    population_path: Path | None,
    population_source: str | None,
) -> SimulationResult:
    """Execute the single-policy scenario path."""
    from reformlab.interfaces.api import RunConfig, ScenarioConfig, run_scenario

    scenario_config = ScenarioConfig(
        template_name=template_name,
        policy=body.policy,
        start_year=body.start_year,
        end_year=body.end_year,
        population_path=population_path,
        seed=body.seed,
        exogenous_series=body.exogenous_series,  # Story 21.6 / AC2
        population_id=body.population_id,  # Story 23.3 / AC-2
        population_source=population_source,  # Story 23.3 / AC-2
    )
    run_config = RunConfig(
        scenario=scenario_config,
        seed=body.seed,
        runtime_mode=body.runtime_mode,
    )
    return run_scenario(run_config, adapter=adapter)


def _log_runtime_mode_mismatch(
    result: SimulationResult,
    requested_mode: Literal["live", "replay"],
    run_id: str,
) -> None:
    """Log when execution silently downgraded or changed runtime mode."""
    actual_mode = result.metadata.get("runtime_mode")
    if actual_mode is not None and actual_mode != requested_mode:
        logger.error(
            "event=runtime_mode_mismatch requested=%s actual=%s run_id=%s",
            requested_mode,
            actual_mode,
            run_id,
        )


def _with_population_provenance(
    result: SimulationResult,
    *,
    population_id: str | None,
    population_source: str | None,
) -> SimulationResult:
    """Patch population provenance into the manifest before cache/disk writes."""
    from dataclasses import replace as _dc_replace

    updated_manifest = _dc_replace(
        result.manifest,
        population_id=population_id or "",
        population_source=population_source or "",
    )
    return _dc_replace(result, manifest=updated_manifest)


def _exogenous_series_summary(
    result: SimulationResult | None,
) -> tuple[str | None, list[str] | None]:
    """Return deterministic exogenous-series hash fields for run metadata."""
    if result is None or not result.manifest.exogenous_series:
        return None, None

    import hashlib

    exog_names = list(result.manifest.exogenous_series)
    hash_input = "|".join(sorted(exog_names))
    exog_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()
    return exog_hash, exog_names


def _persist_run_outputs(
    *,
    store: ResultStore,
    body: RunRequest,
    run_id: str,
    started_at: str,
    finished_at: str,
    template_name: str,
    result: SimulationResult | None,
    status: str,
    row_count: int,
    population_source: str | None,
    portfolio_policy_count: int | None,
    portfolio_resolution_strategy: str | None,
) -> None:
    """Persist run metadata and available artifacts without masking execution errors."""
    from reformlab.server.result_store import ResultMetadata

    exog_hash, exog_names = _exogenous_series_summary(result)

    try:
        run_kind = "portfolio" if body.portfolio_name else "scenario"
        runtime_mode = result.manifest.runtime_mode if result else "live"
        store.save_metadata(
            run_id,
            ResultMetadata(
                run_id=run_id,
                timestamp=started_at,
                run_kind=run_kind,
                template_name=template_name or None,
                policy_type=body.policy_type,
                portfolio_name=body.portfolio_name,
                start_year=body.start_year,
                end_year=body.end_year,
                population_id=body.population_id,
                seed=body.seed,
                row_count=row_count,
                manifest_id=result.manifest.manifest_id if result else "",
                scenario_id=result.scenario_id if result else "",
                adapter_version=result.manifest.adapter_version if result else "unknown",
                runtime_mode=runtime_mode,
                started_at=started_at,
                finished_at=finished_at,
                status=status,
                portfolio_policy_count=portfolio_policy_count,
                portfolio_resolution_strategy=portfolio_resolution_strategy,
                exogenous_series_hash=exog_hash,
                exogenous_series_names=exog_names,
                population_source=population_source,
            ),
        )
    except Exception:
        logger.exception("event=metadata_save_failed run_id=%s", run_id)

    if result is not None and result.panel_output is not None:
        try:
            store.save_panel(run_id, result.panel_output)
        except Exception:
            logger.exception("event=panel_save_failed run_id=%s", run_id)
    if result is not None:
        try:
            store.save_manifest(run_id, result.manifest.to_json())
        except Exception:
            logger.exception("event=manifest_save_failed run_id=%s", run_id)


def _trust_warnings(result: SimulationResult) -> list[str]:
    """Generate trust warnings for exploratory evidence assets."""
    if not result.manifest.evidence_assets:
        return []

    exploratory_assets = [
        asset.get("name", asset.get("asset_id", "unknown"))
        for asset in result.manifest.evidence_assets
        if asset.get("trust_status") in ("exploratory", "demo-only", "validation-pending")
    ]
    if not exploratory_assets:
        return []
    return [
        f"Run uses exploratory data sources: {', '.join(exploratory_assets)}. "
        "Results should not be used for production decision support."
    ]


def _build_run_response(
    run_id: str,
    result: SimulationResult,
    row_count: int,
    population_source: str | None,
) -> RunResponse:
    """Build the stable API response for a completed run."""
    return RunResponse(
        run_id=run_id,
        success=result.success,
        scenario_id=result.scenario_id,
        years=sorted(result.yearly_states.keys()),
        row_count=row_count,
        manifest_id=result.manifest.manifest_id,
        trust_warnings=_trust_warnings(result),
        # Story 23.1 / AC-4: Runtime mode from manifest
        runtime_mode=cast(Literal["live", "replay"], result.manifest.runtime_mode),
        # Story 23.2 / AC-5: Population source from resolver
        population_source=cast(
            "Literal['bundled', 'uploaded', 'generated'] | None", population_source
        ),
    )


def _ensure_portfolio_live_ready(
    portfolio_name: str,
    registry: ScenarioRegistry,
) -> None:
    """Reject live portfolio runs containing replay-only policy types."""
    from reformlab.server.routes.templates import LIVE_READY_TYPES
    from reformlab.templates.portfolios.portfolio import PolicyPortfolio
    from reformlab.templates.registry import RegistryError, ScenarioNotFoundError

    try:
        entry = registry.get(portfolio_name)
    except (KeyError, ScenarioNotFoundError, RegistryError):
        return

    if not isinstance(entry, PolicyPortfolio):
        return

    unavailable: list[str] = []
    for index, policy_cfg in enumerate(entry.policies):
        if policy_cfg.policy_type is None:
            policy_name = policy_cfg.name or f"policy_{index}"
            unavailable.append(
                f"policy[{index}] '{policy_name}' (missing policy_type)"
            )
            continue

        policy_type = policy_cfg.policy_type.value
        if policy_type not in LIVE_READY_TYPES:
            policy_name = policy_cfg.name or policy_type
            unavailable.append(f"policy[{index}] '{policy_name}' ({policy_type})")

    if unavailable:
        raise HTTPException(
            status_code=422,
            detail={
                "what": "Portfolio contains policies unavailable for live execution",
                "why": (
                    f"Portfolio '{portfolio_name}' contains policies unavailable "
                    f"for live execution: {', '.join(unavailable)}"
                ),
                "fix": (
                    "Use runtime_mode='replay' or remove replay-only policies. "
                    f"Live-ready policy types: {', '.join(sorted(LIVE_READY_TYPES))}"
                ),
            },
        )


def _run_portfolio(
    body: RunRequest,
    adapter: ComputationAdapter,
    registry: ScenarioRegistry,
    population_path: Path | None,
    population_id: str | None,  # Story 23.3 / AC-2
    population_source: str | None,  # Story 23.3 / AC-2
) -> tuple[SimulationResult, int, str]:
    """Load a portfolio from the registry and execute via PortfolioComputationStep.

    The portfolio step is appended after the default ComputationStep (which runs
    the first policy as a baseline). The portfolio step then overwrites
    COMPUTATION_RESULT_KEY with the merged multi-policy result.

    Returns (SimulationResult, policy_count, resolution_strategy).
    """
    from reformlab.interfaces.api import (
        RunConfig,
        ScenarioConfig,
        _load_population_data,
        run_scenario,
    )
    from reformlab.orchestrator.portfolio_step import PortfolioComputationStep
    from reformlab.templates.portfolios.portfolio import PolicyPortfolio
    from reformlab.templates.registry import ScenarioNotFoundError

    assert body.portfolio_name is not None  # guaranteed by caller

    try:
        entry = registry.get(body.portfolio_name)
    except ScenarioNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "what": "Portfolio not found",
                "why": f"No portfolio named '{body.portfolio_name}' in registry",
                "fix": "Check portfolio name or create the portfolio first via POST /api/portfolios",
            },
        )

    if not isinstance(entry, PolicyPortfolio):
        raise HTTPException(
            status_code=422,
            detail={
                "what": "Not a portfolio",
                "why": f"Registry entry '{body.portfolio_name}' is a scenario, not a portfolio",
                "fix": "Use template_name for single-policy scenarios",
            },
        )

    population = _load_population_data(population_path)

    portfolio_step = PortfolioComputationStep(
        adapter=adapter,
        population=population,
        portfolio=entry,
        runtime_mode=body.runtime_mode,
    )

    # Use the first policy's type as the template_name for the scenario config.
    # The default ComputationStep runs this single policy, then the portfolio
    # step overwrites results with the full multi-policy merge.
    first_policy = entry.policies[0]
    pt = first_policy.policy_type
    template_name = pt.value if pt is not None else "portfolio"

    from reformlab.computation.types import serialize_policy

    first_policy_dict = serialize_policy(first_policy.policy)

    # Story 23.3 / AC-2: Pass population_id and population_source
    scenario_config = ScenarioConfig(
        template_name=template_name,
        policy=first_policy_dict,
        start_year=body.start_year,
        end_year=body.end_year,
        population_path=population_path,
        seed=body.seed,
        population_id=population_id,  # Story 23.3 / AC-2
        population_source=population_source,  # Story 23.3 / AC-2
    )
    run_config = RunConfig(scenario=scenario_config, seed=body.seed, runtime_mode=body.runtime_mode)

    sim_result = run_scenario(
        run_config,
        adapter=adapter,
        steps=(portfolio_step,),
    )
    return sim_result, entry.policy_count, entry.resolution_strategy


@router.post("/memory-check", response_model=MemoryCheckResponse)
async def memory_check(body: MemoryCheckRequest) -> MemoryCheckResponse:
    """Pre-flight memory estimation for a simulation configuration."""
    from reformlab.interfaces.api import ScenarioConfig, check_memory_requirements

    # Resolve population path from population_id so memory estimate uses
    # the actual row count instead of the 100k default.
    population_path = None
    if body.population_id:
        try:
            resolver = get_population_resolver()
            resolved = resolver.resolve(body.population_id)
            population_path = resolved.data_path
        except Exception:
            pass  # Fall back to default estimate

    scenario_config = ScenarioConfig(
        template_name=body.template_name,
        policy=body.policy,
        start_year=body.start_year,
        end_year=body.end_year,
        population_path=population_path,
    )

    result = check_memory_requirements(scenario_config)

    return MemoryCheckResponse(
        should_warn=result.should_warn,
        estimated_gb=result.estimate.estimated_gb,
        available_gb=result.estimate.available_gb,
        message=result.message,
    )
