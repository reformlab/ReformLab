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
    from reformlab.interfaces.api import RunConfig, ScenarioConfig, run_scenario
    from reformlab.server.result_store import ResultMetadata

    # Mutual exclusion: portfolio_name XOR template_name
    if body.portfolio_name and body.template_name:
        raise HTTPException(
            status_code=422,
            detail={
                "what": "Ambiguous run request",
                "why": "Both portfolio_name and template_name provided",
                "fix": "Specify portfolio_name or template_name, not both",
            },
        )

    from reformlab.server.population_resolver import PopulationResolutionError

    adapter = get_adapter()

    # Story 23.4 / AC-2: Replay mode creates its own precomputed adapter
    if body.runtime_mode == "replay":
        try:
            from reformlab.server.dependencies import _create_replay_adapter

            adapter = _create_replay_adapter()
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
    # Story 23.4 / AC-1: When runtime_mode is "live" (default),
    # use global adapter which is now OpenFiscaApiAdapter by default

    resolver = get_population_resolver()

    # Story 23.2 / AC-1, AC-2, AC-3, AC-4: Unified population resolver
    population_path: Path | None = None
    population_source: str | None = None
    if body.population_id:
        try:
            resolved = resolver.resolve(body.population_id)
            population_path = resolved.data_path
            population_source = resolved.source
        except PopulationResolutionError as exc:
            raise HTTPException(
                status_code=404,
                detail=exc.args[0],  # Already {"what", "why", "fix"} format
            ) from exc

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
            # Story 23.3 / AC-2: Pass population_id and population_source from resolver
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
            # Story 23.1 / AC-1, AC-2: Pass runtime_mode from request to RunConfig
            run_config = RunConfig(
                scenario=scenario_config,
                seed=body.seed,
                runtime_mode=body.runtime_mode,
            )
            result = run_scenario(run_config, adapter=adapter)

        # Story 23.4 / AC-4: Guard against silent runtime mode downgrade
        if result and result.metadata.get("runtime_mode") != body.runtime_mode:
            logger.error(
                "event=runtime_mode_mismatch requested=%s actual=%s run_id=%s",
                body.runtime_mode,
                result.metadata.get("runtime_mode"),
                run_id,
            )

        cache.store(run_id, result)
        status = "completed" if result.success else "failed"
        row_count = result.panel_output.table.num_rows if result.panel_output else 0
    finally:
        finished_at = datetime.now(timezone.utc).isoformat()
        # Story 21.6 / AC6: Extract exogenous series info from manifest
        exog_hash = None
        exog_names = None
        if result and result.manifest.exogenous_series:
            exog_names = list(result.manifest.exogenous_series)
            # Compute hash from sorted series names
            import hashlib

            hash_input = "|".join(sorted(exog_names))
            exog_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

        try:
            run_kind = "portfolio" if body.portfolio_name else "scenario"
            # Story 23.1 / AC-4: Extract runtime_mode from manifest
            runtime_mode_from_manifest = result.manifest.runtime_mode if result else "live"
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
                    # Story 23.1 / AC-4: Runtime mode from manifest
                    runtime_mode=runtime_mode_from_manifest,
                    started_at=started_at,
                    finished_at=finished_at,
                    status=status,
                    portfolio_policy_count=portfolio_policy_count,
                    portfolio_resolution_strategy=portfolio_resolution_strategy,
                    # Story 21.6 / AC6: Exogenous series fields
                    exogenous_series_hash=exog_hash,
                    exogenous_series_names=exog_names,
                    # Story 23.2 / AC-5: Population source from resolver
                    population_source=population_source,
                ),
            )
        except Exception:
            logger.exception("event=metadata_save_failed run_id=%s", run_id)
            # Do not propagate — metadata save failure should not mask run result

        # Persist panel and manifest to disk (Story 17.7 — AC-1, AC-2)
        # Each save is independent; failure must NOT propagate or mask run result.
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

    if result is None:
        # Re-raise will have already propagated; this branch is unreachable
        # but satisfies type checker
        raise RuntimeError("Simulation failed with no result")  # pragma: no cover

    years = sorted(result.yearly_states.keys())

    # Story 21.8 / AC7: Generate trust warnings for exploratory data
    trust_warnings: list[str] = []
    if result.manifest.evidence_assets:
        exploratory_assets = [
            asset.get("name", asset.get("asset_id", "unknown"))
            for asset in result.manifest.evidence_assets
            if asset.get("trust_status") in ("exploratory", "demo-only", "validation-pending")
        ]
        if exploratory_assets:
            trust_warnings.append(
                f"Run uses exploratory data sources: {', '.join(exploratory_assets)}. "
                "Results should not be used for production decision support."
            )

    return RunResponse(
        run_id=run_id,
        success=result.success,
        scenario_id=result.scenario_id,
        years=years,
        row_count=row_count,
        manifest_id=result.manifest.manifest_id,
        trust_warnings=trust_warnings,
        # Story 23.1 / AC-4: Runtime mode from manifest
        runtime_mode=cast(Literal["live", "replay"], result.manifest.runtime_mode),
        # Story 23.2 / AC-5: Population source from resolver
        population_source=cast(
            "Literal['bundled', 'uploaded', 'generated'] | None", population_source
        ),
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

    scenario_config = ScenarioConfig(
        template_name=body.template_name,
        policy=body.policy,
        start_year=body.start_year,
        end_year=body.end_year,
    )

    result = check_memory_requirements(scenario_config)

    return MemoryCheckResponse(
        should_warn=result.should_warn,
        estimated_gb=result.estimate.estimated_gb,
        available_gb=result.estimate.available_gb,
        message=result.message,
    )
