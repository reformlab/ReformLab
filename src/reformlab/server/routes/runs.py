"""Simulation execution routes."""

from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends

from reformlab.server.dependencies import ResultCache, get_adapter, get_result_cache
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
    """
    from reformlab.interfaces.api import RunConfig, ScenarioConfig, run_scenario

    adapter = get_adapter()

    population_path = _resolve_population_path(body.population_id)

    scenario_config = ScenarioConfig(
        template_name=body.template_name,
        parameters=body.parameters,
        start_year=body.start_year,
        end_year=body.end_year,
        population_path=population_path,
        seed=body.seed,
    )

    run_config = RunConfig(scenario=scenario_config, seed=body.seed)

    result = run_scenario(run_config, adapter=adapter)

    run_id = str(uuid.uuid4())
    cache.store(run_id, result)

    years = sorted(result.yearly_states.keys())
    row_count = result.panel_output.table.num_rows if result.panel_output else 0

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
        parameters=body.parameters,
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
