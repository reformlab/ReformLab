"""Simulation execution routes."""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends

from reformlab.server.dependencies import ResultCache, get_adapter, get_result_cache, get_result_store
from reformlab.server.models import (
    MemoryCheckRequest,
    MemoryCheckResponse,
    RunRequest,
    RunResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _resolve_population_path(population_id: str | None) -> Path | None:
    """Resolve a population_id to a file path by scanning the data directory."""
    if not population_id:
        return None

    data_dir = Path(os.environ.get("REFORMLAB_DATA_DIR", "data")) / "populations"
    if not data_dir.exists():
        return None

    for path in data_dir.iterdir():
        if path.stem == population_id and path.suffix.lower() in {".csv", ".parquet"}:
            return path

    return None


@router.post("", response_model=RunResponse)
async def run_simulation(
    body: RunRequest,
    cache: ResultCache = Depends(get_result_cache),
) -> RunResponse:
    """Execute a simulation synchronously and return the result.

    MVP: Blocks until simulation completes (<10s for 100k households).
    Auto-saves run metadata to persistent store on both success and failure.
    """
    from reformlab.interfaces.api import RunConfig, ScenarioConfig, run_scenario
    from reformlab.server.result_store import ResultMetadata

    adapter = get_adapter()

    population_path = _resolve_population_path(body.population_id)

    template_name = body.template_name or ""

    scenario_config = ScenarioConfig(
        template_name=template_name,
        policy=body.policy,
        start_year=body.start_year,
        end_year=body.end_year,
        population_path=population_path,
        seed=body.seed,
    )

    run_config = RunConfig(scenario=scenario_config, seed=body.seed)

    run_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()
    result = None
    status = "failed"
    row_count = 0

    try:
        result = run_scenario(run_config, adapter=adapter)
        cache.store(run_id, result)
        status = "completed" if result.success else "failed"
        row_count = result.panel_output.table.num_rows if result.panel_output else 0
    finally:
        finished_at = datetime.now(timezone.utc).isoformat()
        store = get_result_store()
        try:
            run_kind = "portfolio" if body.portfolio_name else "scenario"
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
                    started_at=started_at,
                    finished_at=finished_at,
                    status=status,
                ),
            )
        except Exception:
            logger.exception("event=metadata_save_failed run_id=%s", run_id)
            # Do not propagate — metadata save failure should not mask run result

    if result is None:
        # Re-raise will have already propagated; this branch is unreachable
        # but satisfies type checker
        raise RuntimeError("Simulation failed with no result")  # pragma: no cover

    years = sorted(result.yearly_states.keys())

    return RunResponse(
        run_id=run_id,
        success=result.success,
        scenario_id=result.scenario_id,
        years=years,
        row_count=row_count,
        manifest_id=result.manifest.manifest_id,
    )


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
