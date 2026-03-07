"""Portfolio CRUD routes — Story 17.2.

Endpoints wrap the Epic 12 portfolio composition library and the
ScenarioRegistry for persistence. All endpoints require authentication
via the shared bearer token.
"""

from __future__ import annotations

import logging
import re
import shutil
from typing import Any

from fastapi import APIRouter, HTTPException

from reformlab.server.models import (
    ClonePortfolioRequest,
    CreatePortfolioRequest,
    PortfolioConflict,
    PortfolioDetailResponse,
    PortfolioListItem,
    PortfolioPolicyItem,
    PortfolioPolicyRequest,
    UpdatePortfolioRequest,
    ValidatePortfolioRequest,
    ValidatePortfolioResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

_NAME_RE = re.compile(r"^(?:[a-z0-9]{1,64}|[a-z0-9][a-z0-9-]{0,62}[a-z0-9])$")
_RESERVED_NAMES = frozenset({"validate", "clone"})
_VALID_RESOLUTION_STRATEGIES = frozenset({"error", "sum", "first_wins", "last_wins", "max"})


def _validate_portfolio_name(name: str) -> None:
    """Validate a portfolio name is a lowercase slug.

    Raises HTTPException(422) on violation.
    """
    if name in _RESERVED_NAMES:
        raise HTTPException(
            status_code=422,
            detail={
                "what": f"Reserved portfolio name: '{name}'",
                "why": f"'{name}' is a reserved route segment and cannot be used as a portfolio name",
                "fix": "Choose a different name that does not conflict with reserved paths: validate, clone",
            },
        )
    if not _NAME_RE.match(name):
        raise HTTPException(
            status_code=422,
            detail={
                "what": f"Invalid portfolio name: '{name}'",
                "why": "Portfolio name must match ^[a-z0-9][a-z0-9-]{0,62}[a-z0-9]$ or ^[a-z0-9]{1,64}$",
                "fix": "Use only lowercase letters, digits, and hyphens (max 64 chars)",
            },
        )


def _validate_resolution_strategy(strategy: str) -> None:
    """Raise HTTPException(422) if strategy is not valid."""
    if strategy not in _VALID_RESOLUTION_STRATEGIES:
        raise HTTPException(
            status_code=422,
            detail={
                "what": f"Invalid resolution_strategy: '{strategy}'",
                "why": f"Must be one of: {sorted(_VALID_RESOLUTION_STRATEGIES)}",
                "fix": "Use one of: error, sum, first_wins, last_wins, max",
            },
        )


# ---------------------------------------------------------------------------
# Domain object builder
# ---------------------------------------------------------------------------


def _build_policy_config(req: PortfolioPolicyRequest) -> Any:
    """Build a PolicyConfig from a request object.

    Returns a PolicyConfig frozen dataclass.

    Raises HTTPException(422) on bad policy_type or unknown parameters.
    """
    from reformlab.templates.portfolios import PolicyConfig
    from reformlab.templates.schema import (
        CarbonTaxParameters,
        FeebateParameters,
        PolicyParameters,
        PolicyType,
        RebateParameters,
        SubsidyParameters,
    )

    try:
        policy_type = PolicyType(req.policy_type)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail={
                "what": f"Invalid policy_type: '{req.policy_type}'",
                "why": f"Must be one of: {[e.value for e in PolicyType]}",
                "fix": "Use one of: carbon_tax, subsidy, rebate, feebate",
            },
        )

    params_cls: type[PolicyParameters] = {
        PolicyType.CARBON_TAX: CarbonTaxParameters,
        PolicyType.SUBSIDY: SubsidyParameters,
        PolicyType.REBATE: RebateParameters,
        PolicyType.FEEBATE: FeebateParameters,
    }.get(policy_type, PolicyParameters)

    # Convert string keys to int for rate_schedule
    rate_schedule = {int(k): v for k, v in req.rate_schedule.items()}

    # Build extra kwargs from extra_params (policy-specific fields)
    extra: dict[str, Any] = {}
    if hasattr(params_cls, "__dataclass_fields__"):
        allowed = {f for f in params_cls.__dataclass_fields__ if not f.startswith("_")}
        allowed -= {"rate_schedule", "exemptions", "thresholds", "covered_categories"}
        for k, v in req.extra_params.items():
            if k in allowed:
                extra[k] = v

    policy = params_cls(
        rate_schedule=rate_schedule,
        exemptions=tuple(req.exemptions),  # type: ignore[arg-type]
        thresholds=tuple(req.thresholds),  # type: ignore[arg-type]
        covered_categories=tuple(req.covered_categories),
        **extra,
    )

    return PolicyConfig(policy_type=policy_type, policy=policy, name=req.name)


def _build_portfolio(name: str, description: str, resolution_strategy: str,
                     policies: list[PortfolioPolicyRequest]) -> Any:
    """Build a PolicyPortfolio from request data.

    Raises HTTPException on validation errors.
    """
    from reformlab.templates.portfolios import PolicyPortfolio
    from reformlab.templates.portfolios.exceptions import PortfolioValidationError

    if len(policies) < 2:
        raise HTTPException(
            status_code=400,
            detail={
                "what": "Insufficient policies",
                "why": f"Portfolio requires at least 2 policies, got {len(policies)}",
                "fix": "Add at least 2 policies to the portfolio",
            },
        )

    _validate_resolution_strategy(resolution_strategy)

    configs = []
    for req_policy in policies:
        configs.append(_build_policy_config(req_policy))

    try:
        portfolio = PolicyPortfolio(
            name=name,
            description=description,
            policies=tuple(configs),
            resolution_strategy=resolution_strategy,
        )
    except PortfolioValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "what": exc.summary,
                "why": exc.reason,
                "fix": exc.fix,
            },
        ) from exc

    return portfolio


def _portfolio_to_detail(name: str, portfolio: Any, version_id: str) -> PortfolioDetailResponse:
    """Convert a PolicyPortfolio domain object to a PortfolioDetailResponse."""
    policy_items = []
    for config in portfolio.policies:
        raw = config.policy
        # Extract rate_schedule with string keys for JSON wire format
        rate_schedule: dict[str, float] = {
            str(k): float(v) for k, v in raw.rate_schedule.items()
        }
        # Build parameters dict from all policy fields except rate_schedule
        from dataclasses import fields

        all_fields = {f.name for f in fields(raw)}
        params: dict[str, Any] = {}
        for field_name in all_fields:
            if field_name == "rate_schedule":
                continue
            val = getattr(raw, field_name)
            if val:  # Skip empty tuples/dicts
                # Convert tuples/frozensets to lists for JSON
                if isinstance(val, (tuple, frozenset)):
                    params[field_name] = list(val)
                elif isinstance(val, dict):
                    params[field_name] = dict(val)
                else:
                    params[field_name] = val

        policy_items.append(PortfolioPolicyItem(
            name=config.name,
            policy_type=config.policy_type.value,
            rate_schedule=rate_schedule,
            parameters=params,
        ))

    return PortfolioDetailResponse(
        name=name,
        description=portfolio.description,
        version_id=version_id,
        policies=policy_items,
        resolution_strategy=portfolio.resolution_strategy,
        policy_count=portfolio.policy_count,
    )


def _get_registry() -> Any:
    """Return a ScenarioRegistry instance."""
    from reformlab.templates.registry import ScenarioRegistry
    return ScenarioRegistry()


# ---------------------------------------------------------------------------
# Routes — NOTE: /validate must be declared before /{name}
# ---------------------------------------------------------------------------


@router.post("/validate", response_model=ValidatePortfolioResponse)
async def validate_portfolio(body: ValidatePortfolioRequest) -> ValidatePortfolioResponse:
    """Validate a draft portfolio for policy conflicts (no save)."""
    from reformlab.templates.portfolios import validate_compatibility
    from reformlab.templates.portfolios.exceptions import PortfolioValidationError

    if len(body.policies) < 2:
        raise HTTPException(
            status_code=400,
            detail={
                "what": "Insufficient policies",
                "why": f"Validation requires at least 2 policies, got {len(body.policies)}",
                "fix": "Add at least 2 policies before validating",
            },
        )

    _validate_resolution_strategy(body.resolution_strategy)

    try:
        portfolio = _build_portfolio(
            name="__validate__",
            description="",
            resolution_strategy=body.resolution_strategy,
            policies=body.policies,
        )
    except HTTPException:
        raise
    except PortfolioValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={"what": exc.summary, "why": exc.reason, "fix": exc.fix},
        ) from exc

    try:
        conflicts_raw = validate_compatibility(portfolio)
    except Exception as exc:
        logger.error("event=validate_compatibility_error error=%s", str(exc))
        conflicts_raw = ()

    conflicts = [
        PortfolioConflict(
            conflict_type=c.conflict_type.value,
            policy_indices=list(c.policy_indices),
            parameter_name=c.parameter_name,
            description=c.description,
        )
        for c in conflicts_raw
    ]

    return ValidatePortfolioResponse(
        conflicts=conflicts,
        is_compatible=len(conflicts) == 0,
    )


@router.get("", response_model=list[PortfolioListItem])
async def list_portfolios() -> list[PortfolioListItem]:
    """List all saved portfolios."""
    registry = _get_registry()
    names = registry.list_portfolios()
    result = []
    for name in names:
        try:
            portfolio = registry.get(name)
            entry = registry.get_entry(name)
            result.append(PortfolioListItem(
                name=name,
                description=portfolio.description,
                version_id=entry.latest_version,
                policy_count=portfolio.policy_count,
            ))
        except Exception:
            logger.warning("event=list_portfolios_skip name=%s reason=load_error", name)
            continue
    return result


@router.get("/{name}", response_model=PortfolioDetailResponse)
async def get_portfolio(name: str) -> PortfolioDetailResponse:
    """Get portfolio detail including all policies."""
    registry = _get_registry()
    try:
        portfolio = registry.get(name)
    except Exception as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "what": f"Portfolio '{name}' not found",
                "why": str(exc),
                "fix": "Check the portfolio name",
            },
        ) from exc

    # Confirm it's actually a portfolio
    try:
        entry_type = registry.get_entry_type(name)
    except Exception:
        entry_type = "portfolio"

    if entry_type != "portfolio":
        raise HTTPException(
            status_code=404,
            detail={
                "what": f"Portfolio '{name}' not found",
                "why": f"Entry '{name}' exists but is a {entry_type}, not a portfolio",
                "fix": "Use /api/scenarios for scenario lookups",
            },
        )

    entry = registry.get_entry(name)
    return _portfolio_to_detail(name, portfolio, entry.latest_version)


@router.post("", response_model=dict[str, str], status_code=201)
async def create_portfolio(body: CreatePortfolioRequest) -> dict[str, str]:
    """Create and save a new portfolio."""
    _validate_portfolio_name(body.name)

    registry = _get_registry()

    # Check for name collision
    if registry.exists(body.name):
        # Suggest an alternative
        alt = f"{body.name}-2"
        raise HTTPException(
            status_code=409,
            detail={
                "what": f"Portfolio name '{body.name}' already exists",
                "why": "A portfolio (or scenario) with this name is already registered",
                "fix": f"Choose a different name, e.g. '{alt}'",
            },
        )

    portfolio = _build_portfolio(
        name=body.name,
        description=body.description,
        resolution_strategy=body.resolution_strategy,
        policies=body.policies,
    )

    version_id = registry.save(portfolio, body.name)
    logger.info("event=portfolio_created name=%s version_id=%s", body.name, version_id)
    return {"version_id": version_id}


@router.put("/{name}", response_model=PortfolioDetailResponse)
async def update_portfolio(name: str, body: UpdatePortfolioRequest) -> PortfolioDetailResponse:
    """Update an existing portfolio's policies/parameters/order."""
    registry = _get_registry()

    # Verify portfolio exists and is a portfolio type
    if not registry.exists(name):
        raise HTTPException(
            status_code=404,
            detail={
                "what": f"Portfolio '{name}' not found",
                "why": f"No entry named '{name}' exists in the registry",
                "fix": "Create the portfolio first via POST /api/portfolios",
            },
        )

    try:
        entry_type = registry.get_entry_type(name)
    except Exception:
        entry_type = "portfolio"

    if entry_type != "portfolio":
        raise HTTPException(
            status_code=404,
            detail={
                "what": f"Portfolio '{name}' not found",
                "why": f"Entry '{name}' is a {entry_type}, not a portfolio",
                "fix": "Use /api/scenarios for scenario updates",
            },
        )

    # Get existing to preserve fields not in the update request
    existing = registry.get(name)

    resolution_strategy = body.resolution_strategy or existing.resolution_strategy
    description = body.description if body.description is not None else existing.description

    portfolio = _build_portfolio(
        name=name,
        description=description,
        resolution_strategy=resolution_strategy,
        policies=body.policies,
    )

    version_id = registry.save(portfolio, name)
    logger.info("event=portfolio_updated name=%s version_id=%s", name, version_id)
    return _portfolio_to_detail(name, portfolio, version_id)


@router.delete("/{name}", status_code=204)
async def delete_portfolio(name: str) -> None:
    """Delete a portfolio from the registry."""
    registry = _get_registry()
    entry_path = registry.path / name

    if not entry_path.exists():
        raise HTTPException(
            status_code=404,
            detail={
                "what": f"Portfolio '{name}' not found",
                "why": f"No entry named '{name}' exists in the registry",
                "fix": "Check the portfolio name",
            },
        )

    # Confirm it's a portfolio before deleting
    try:
        entry_type = registry.get_entry_type(name)
    except Exception:
        entry_type = "portfolio"

    if entry_type != "portfolio":
        raise HTTPException(
            status_code=404,
            detail={
                "what": f"Portfolio '{name}' not found",
                "why": f"Entry '{name}' is a {entry_type}, not a portfolio",
                "fix": "This endpoint only deletes portfolios",
            },
        )

    shutil.rmtree(entry_path)
    logger.info("event=portfolio_deleted name=%s", name)


@router.post("/{name}/clone", response_model=PortfolioDetailResponse, status_code=201)
async def clone_portfolio(name: str, body: ClonePortfolioRequest) -> PortfolioDetailResponse:
    """Clone a portfolio with a new name."""
    _validate_portfolio_name(body.new_name)

    registry = _get_registry()

    # Verify source exists
    if not registry.exists(name):
        raise HTTPException(
            status_code=404,
            detail={
                "what": f"Portfolio '{name}' not found",
                "why": f"No portfolio named '{name}' exists in the registry",
                "fix": "Check the source portfolio name",
            },
        )

    # Verify source is a portfolio
    try:
        entry_type = registry.get_entry_type(name)
    except Exception:
        entry_type = "portfolio"

    if entry_type != "portfolio":
        raise HTTPException(
            status_code=404,
            detail={
                "what": f"Portfolio '{name}' not found",
                "why": f"Entry '{name}' is a {entry_type}, not a portfolio",
                "fix": "This endpoint only clones portfolios",
            },
        )

    # Check for name collision on target
    if registry.exists(body.new_name):
        alt = f"{body.new_name}-2"
        raise HTTPException(
            status_code=409,
            detail={
                "what": f"Target name '{body.new_name}' already exists",
                "why": "A portfolio or scenario with this name is already registered",
                "fix": f"Choose a different name, e.g. '{alt}'",
            },
        )

    # Clone in memory and save
    cloned = registry.clone(name, new_name=body.new_name)
    version_id = registry.save(cloned, body.new_name)
    logger.info("event=portfolio_cloned source=%s target=%s version_id=%s", name, body.new_name, version_id)
    return _portfolio_to_detail(body.new_name, cloned, version_id)
