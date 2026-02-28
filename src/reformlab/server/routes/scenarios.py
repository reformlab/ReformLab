"""Scenario CRUD routes."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from reformlab.server.models import (
    CloneRequest,
    CreateScenarioRequest,
    ScenarioResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _scenario_to_response(name: str, scenario: Any) -> ScenarioResponse:
    """Convert a domain scenario object to a ScenarioResponse."""
    # Handle both BaselineScenario and ReformScenario
    pt = scenario.policy_type
    policy_type = pt.value if hasattr(pt, "value") else str(pt)
    description = getattr(scenario, "description", "")
    version = getattr(scenario, "version", "1.0")
    baseline_ref = getattr(scenario, "baseline_ref", None)

    # Extract parameters as dict
    params = scenario.parameters
    if hasattr(params, "__dataclass_fields__"):
        from dataclasses import asdict

        params = asdict(params)
    elif not isinstance(params, dict):
        params = {}

    # Extract year schedule
    year_schedule: dict[str, int] = {}
    ys = getattr(scenario, "year_schedule", None)
    if ys is not None:
        year_schedule = {"start_year": ys.start_year, "end_year": ys.end_year}

    return ScenarioResponse(
        name=name,
        policy_type=policy_type,
        description=description,
        version=version,
        parameters=params,
        year_schedule=year_schedule,
        baseline_ref=baseline_ref,
    )


@router.get("", response_model=dict[str, list[str]])
async def list_scenarios() -> dict[str, list[str]]:
    """List all registered scenario names."""
    from reformlab.interfaces.api import list_scenarios as _list_scenarios

    scenarios = _list_scenarios()
    return {"scenarios": scenarios}


@router.get("/{name}", response_model=ScenarioResponse)
async def get_scenario(name: str) -> ScenarioResponse:
    """Get a scenario by name."""
    from reformlab.interfaces.api import get_scenario as _get_scenario

    try:
        scenario = _get_scenario(name)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return _scenario_to_response(name, scenario)


@router.post("", response_model=dict[str, str], status_code=201)
async def create_scenario(body: CreateScenarioRequest) -> dict[str, str]:
    """Create and register a new scenario."""
    from reformlab.interfaces.api import create_scenario as _create_scenario
    from reformlab.templates.schema import (
        BaselineScenario,
        CarbonTaxParameters,
        FeebateParameters,
        PolicyParameters,
        PolicyType,
        RebateParameters,
        ReformScenario,
        SubsidyParameters,
        YearSchedule,
    )

    policy_type = PolicyType(body.policy_type)
    year_schedule = YearSchedule(body.start_year, body.end_year)

    # Build typed parameters based on policy type
    params_cls: type[PolicyParameters] = {
        PolicyType.CARBON_TAX: CarbonTaxParameters,
        PolicyType.SUBSIDY: SubsidyParameters,
        PolicyType.REBATE: RebateParameters,
        PolicyType.FEEBATE: FeebateParameters,
    }.get(policy_type, PolicyParameters)

    # Extract common fields and policy-specific fields
    raw = dict(body.parameters)
    rate_schedule = raw.pop("rate_schedule", {})
    exemptions = tuple(raw.pop("exemptions", ()))
    thresholds = tuple(raw.pop("thresholds", ()))
    covered_categories = tuple(raw.pop("covered_categories", ()))

    params = params_cls(
        rate_schedule=rate_schedule,
        exemptions=exemptions,
        thresholds=thresholds,
        covered_categories=covered_categories,
        **raw,
    )

    if body.baseline_ref:
        scenario = ReformScenario(
            name=body.name,
            policy_type=policy_type,
            baseline_ref=body.baseline_ref,
            parameters=params,
            description=body.description,
            year_schedule=year_schedule,
        )
    else:
        scenario = BaselineScenario(  # type: ignore[assignment]
            name=body.name,
            policy_type=policy_type,
            year_schedule=year_schedule,
            parameters=params,
            description=body.description,
        )

    version_id = _create_scenario(scenario, body.name, register=True)
    return {"version_id": str(version_id)}


@router.post("/{name}/clone", response_model=ScenarioResponse, status_code=201)
async def clone_scenario(name: str, body: CloneRequest) -> ScenarioResponse:
    """Clone an existing scenario with a new name."""
    from reformlab.interfaces.api import clone_scenario as _clone_scenario

    try:
        cloned = _clone_scenario(name, new_name=body.new_name)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return _scenario_to_response(body.new_name, cloned)
