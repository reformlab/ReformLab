"""Scenario CRUD routes."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from reformlab.interfaces.errors import ConfigurationError
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

    # Extract policy as dict
    params = scenario.policy
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
        policy=params,
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
    except (KeyError, FileNotFoundError, ValueError, ConfigurationError) as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "what": f"Scenario '{name}' not found",
                "why": str(exc),
                "fix": "Check the scenario name",
            },
        ) from exc

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

    # Resolve policy_type: explicit value or infer from policy._type discriminator
    raw_policy_type = body.policy_type
    if raw_policy_type is None:
        raw_policy_type = body.policy.get("_type")
    if raw_policy_type is None:
        valid_types = [e.value for e in PolicyType]
        raise HTTPException(
            status_code=422,
            detail={
                "what": "Missing policy_type",
                "why": "policy_type is required but was not provided",
                "fix": (
                    "Provide policy_type as a top-level field or as a '_type' key "
                    f"inside the policy dict. Must be one of: {valid_types}"
                ),
            },
        )
    try:
        policy_type = PolicyType(raw_policy_type)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail={
                "what": f"Invalid policy_type '{raw_policy_type}'",
                "why": f"'{raw_policy_type}' is not a recognized policy type",
                "fix": f"Must be one of: {[e.value for e in PolicyType]}",
            },
        )
    year_schedule = YearSchedule(body.start_year, body.end_year)

    # Build typed policy based on policy type
    params_cls: type[PolicyParameters] = {
        PolicyType.CARBON_TAX: CarbonTaxParameters,
        PolicyType.SUBSIDY: SubsidyParameters,
        PolicyType.REBATE: RebateParameters,
        PolicyType.FEEBATE: FeebateParameters,
    }.get(policy_type, PolicyParameters)

    # Extract common fields and policy-specific fields
    raw = dict(body.policy)
    raw.pop("_type", None)  # Remove discriminator field if present
    rate_schedule = raw.pop("rate_schedule", {})
    exemptions = tuple(raw.pop("exemptions", ()))
    thresholds = tuple(raw.pop("thresholds", ()))
    covered_categories = tuple(raw.pop("covered_categories", ()))

    # Validate remaining keys against the dataclass fields
    if hasattr(params_cls, "__dataclass_fields__"):
        # Exclude private implementation fields (e.g. _pivot_point_set) and
        # common fields that were already extracted above.
        allowed = {f for f in params_cls.__dataclass_fields__ if not f.startswith("_")}
        allowed -= {"rate_schedule", "exemptions", "thresholds", "covered_categories"}
        unknown = set(raw) - allowed
        if unknown:
            raise HTTPException(
                status_code=422,
                detail={
                    "what": f"Unknown parameters for {policy_type.value}",
                    "why": f"Unexpected fields: {sorted(unknown)}",
                    "fix": "Remove unknown fields",
                },
            )

    params = params_cls(
        rate_schedule=rate_schedule,
        exemptions=exemptions,
        thresholds=thresholds,
        covered_categories=covered_categories,
        **raw,
    )

    scenario: BaselineScenario | ReformScenario
    if body.baseline_ref:
        scenario = ReformScenario(
            name=body.name,
            policy_type=policy_type,
            baseline_ref=body.baseline_ref,
            policy=params,
            description=body.description,
            year_schedule=year_schedule,
        )
    else:
        scenario = BaselineScenario(
            name=body.name,
            policy_type=policy_type,
            year_schedule=year_schedule,
            policy=params,
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
    except (KeyError, FileNotFoundError, ValueError, ConfigurationError) as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "what": f"Scenario '{name}' not found",
                "why": str(exc),
                "fix": "Check the scenario name and ensure it exists",
            },
        ) from exc

    return _scenario_to_response(body.new_name, cloned)
