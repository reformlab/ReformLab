# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Portfolio CRUD routes — Story 17.2.

Endpoints wrap the Epic 12 portfolio composition library and the
ScenarioRegistry for persistence. All endpoints require authentication
via the shared bearer token.
"""

from __future__ import annotations

import json
import logging
import re
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from fastapi import APIRouter, HTTPException

if TYPE_CHECKING:
    from reformlab.templates.portfolios.portfolio import PolicyPortfolio

from reformlab.server.dependencies import get_registry
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
from reformlab.templates.registry import RegistryError

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
# Metadata storage helpers — Story 25.4
# ---------------------------------------------------------------------------


def _get_portfolio_metadata_path(registry: Any, name: str) -> Path:
    """Get the path to a portfolio's metadata.json file."""
    return Path(registry.path) / name / "metadata.json"


def _load_portfolio_metadata(registry: Any, name: str) -> dict[str, Any]:
    """Load UI-layer metadata for a portfolio.

    Returns empty dict if no metadata file exists.
    """
    metadata_path = _get_portfolio_metadata_path(registry, name)
    if metadata_path.exists():
        try:
            with open(metadata_path) as f:
                return json.load(f)  # type: ignore[no-any-return]
        except (json.JSONDecodeError, IOError) as exc:
            logger.warning("event=metadata_load_failed name=%s error=%s", name, str(exc))
            return {}
    return {}


def _save_portfolio_metadata(registry: Any, name: str, metadata: dict[str, Any]) -> None:
    """Save UI-layer metadata for a portfolio.

    Stores editable_parameter_groups, category_id, and parameter_groups
    for each policy (Story 25.3/25.4).
    """
    metadata_path = _get_portfolio_metadata_path(registry, name)
    try:
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
    except IOError as exc:
        logger.warning("event=metadata_save_failed name=%s error=%s", name, str(exc))


def _delete_portfolio_metadata(registry: Any, name: str) -> None:
    """Delete UI-layer metadata for a portfolio.

    Story 25.5: Removes stale metadata when all UI-layer fields are removed.
    """
    metadata_path = _get_portfolio_metadata_path(registry, name)
    if metadata_path.exists():
        try:
            metadata_path.unlink()
            logger.info("event=metadata_deleted name=%s", name)
        except OSError as exc:
            logger.warning("event=metadata_delete_failed name=%s error=%s", name, str(exc))


def _extract_metadata_from_policies(policies: list[PortfolioPolicyRequest]) -> dict[str, Any]:
    """Extract UI-layer metadata from portfolio policies (Story 25.4).

    Returns a metadata dict with editable_parameter_groups, category_id,
    and parameter_groups for each policy that has them.
    """
    policies_metadata = []
    for policy in policies:
        policy_meta: dict[str, Any] = {"name": policy.name}
        if policy.category_id:
            policy_meta["category_id"] = policy.category_id
        if policy.parameter_groups:
            policy_meta["parameter_groups"] = policy.parameter_groups
        if policy.editable_parameter_groups:
            policy_meta["editable_parameter_groups"] = policy.editable_parameter_groups

        # Only include policies that have UI-layer metadata
        if len(policy_meta) > 1:
            policies_metadata.append(policy_meta)

    return {"policies": policies_metadata} if policies_metadata else {}


# ---------------------------------------------------------------------------
# Domain object builder
# ---------------------------------------------------------------------------


def _build_policy_config(req: PortfolioPolicyRequest) -> Any:
    """Build a PolicyConfig from a request object.

    Story 24.3: Extended to handle CustomPolicyType for vehicle_malus
    and energy_poverty_aid policies.

    Returns a PolicyConfig frozen dataclass.

    Raises HTTPException(422) on bad policy_type or unknown parameters.
    """
    from reformlab.templates.portfolios import PolicyConfig
    from reformlab.templates.schema import (
        CarbonTaxParameters,
        CustomPolicyType,
        FeebateParameters,
        PolicyParameters,
        PolicyType,
        RebateParameters,
        SubsidyParameters,
        get_policy_type,
    )

    # Story 24.3: Try PolicyType enum first, then CustomPolicyType
    policy_type: PolicyType | CustomPolicyType
    try:
        policy_type = PolicyType(req.policy_type)
    except ValueError:
        # Fall back to CustomPolicyType via public registry API
        from reformlab.templates.exceptions import TemplateError

        try:
            policy_type = get_policy_type(req.policy_type)
        except TemplateError:
            raise HTTPException(
                status_code=422,
                detail={
                    "what": f"Invalid policy_type: '{req.policy_type}'",
                    "why": "Policy type not found in built-in or custom registries",
                    "fix": (
                        "Use a valid policy type: carbon_tax, subsidy, rebate, "
                        "feebate, vehicle_malus, energy_poverty_aid"
                    ),
                },
            )

    # Get parameters class from registry
    # Story 24.3: Built-in types
    _POLICY_TYPE_TO_PARAMS: dict[PolicyType, type[PolicyParameters]] = {
        PolicyType.CARBON_TAX: CarbonTaxParameters,
        PolicyType.SUBSIDY: SubsidyParameters,
        PolicyType.REBATE: RebateParameters,
        PolicyType.FEEBATE: FeebateParameters,
    }

    # Story 24.3: Handle CustomPolicyType parameter class lookup
    params_cls: type[PolicyParameters]
    if isinstance(policy_type, PolicyType):
        builtin_params_cls = _POLICY_TYPE_TO_PARAMS.get(policy_type)
        if builtin_params_cls is None:
            raise HTTPException(
                status_code=422,
                detail={
                    "what": f"Parameters class not found for policy type: '{req.policy_type}'",
                    "why": "No parameters mapping registered for this built-in type",
                    "fix": "Use one of: carbon_tax, subsidy, rebate, feebate",
                },
            )
        params_cls = builtin_params_cls
    else:
        # CustomPolicyType: look up via public registry API
        from reformlab.templates.schema import list_custom_registrations

        custom_registrations = list_custom_registrations()
        custom_params_cls = custom_registrations.get(policy_type.value)

        if custom_params_cls is None:
            raise HTTPException(
                status_code=422,
                detail={
                    "what": f"Parameters class not found for policy type: '{req.policy_type}'",
                    "why": "No parameters mapping registered for this custom policy type",
                    "fix": "Register the parameters class for this custom policy type",
                },
            )
        params_cls = custom_params_cls

    # Convert string keys to int for rate_schedule
    try:
        rate_schedule = {int(k): v for k, v in req.rate_schedule.items()}
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "what": "Invalid rate_schedule key",
                "why": f"Rate schedule keys must be integer years: {exc}",
                "fix": "Use integer year strings as keys, e.g. '2025', '2026'",
            },
        ) from exc

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

    # Story 24.3 code review fix: removed runtime availability check from
    # portfolio create/update. Availability is enforced at execution time
    # via the preflight validation check, allowing replay-only portfolios
    # to reference any policy type.

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


def _portfolio_to_detail(name: str, portfolio: Any, version_id: str, metadata: dict[str, Any] | None = None) -> PortfolioDetailResponse:
    """Convert a PolicyPortfolio domain object to a PortfolioDetailResponse.

    Story 25.4: Accepts optional metadata dict containing UI-layer fields
    (editable_parameter_groups, category_id, parameter_groups) for each policy.
    """
    # Build metadata lookup by policy name for efficient access
    metadata_by_policy: dict[str, dict[str, Any]] = {}
    if metadata and "policies" in metadata:
        for policy_meta in metadata["policies"]:
            policy_name = policy_meta.get("name")
            if policy_name:
                metadata_by_policy[policy_name] = policy_meta

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
            if val is not None and val != () and val != {}:  # Skip empty collections, not zeros
                # Convert tuples/frozensets to lists for JSON
                if isinstance(val, (tuple, frozenset)):
                    params[field_name] = list(val)
                elif isinstance(val, dict):
                    params[field_name] = dict(val)
                else:
                    params[field_name] = val

        # Get UI-layer metadata for this policy (Story 25.4)
        policy_metadata = metadata_by_policy.get(config.name, {})

        policy_items.append(PortfolioPolicyItem(
            name=config.name,
            policy_type=config.policy_type.value,
            rate_schedule=rate_schedule,
            parameters=params,
            category_id=policy_metadata.get("category_id"),  # Story 25.3
            parameter_groups=policy_metadata.get("parameter_groups", []),  # Story 25.3
            editable_parameter_groups=policy_metadata.get("editable_parameter_groups"),  # Story 25.4
        ))

    return PortfolioDetailResponse(
        name=name,
        description=portfolio.description,
        version_id=version_id,
        policies=policy_items,
        resolution_strategy=portfolio.resolution_strategy,
        policy_count=portfolio.policy_count,
    )



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
    except (ValueError, TypeError) as exc:
        logger.error("event=validate_compatibility_error error=%s", str(exc))
        raise HTTPException(
            status_code=500,
            detail={
                "what": "Conflict validation failed unexpectedly",
                "why": str(exc),
                "fix": "Check server logs and retry",
            },
        ) from exc

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
    registry = get_registry()
    names = registry.list_portfolios()
    result = []
    for name in names:
        try:
            portfolio = cast("PolicyPortfolio", registry.get(name))
            entry = registry.get_entry(name)
            result.append(PortfolioListItem(
                name=name,
                description=portfolio.description,
                version_id=entry.latest_version,
                policy_count=portfolio.policy_count,
            ))
        except (KeyError, FileNotFoundError, ValueError, RegistryError):
            logger.warning("event=list_portfolios_skip name=%s reason=load_error", name)
            continue
    return result


@router.get("/{name}", response_model=PortfolioDetailResponse)
async def get_portfolio(name: str) -> PortfolioDetailResponse:
    """Get portfolio detail including all policies.

    Story 25.4: Loads UI-layer metadata from sidecar metadata.json file.
    """
    registry = get_registry()
    try:
        portfolio = registry.get(name)
    except (KeyError, FileNotFoundError, ValueError, RegistryError) as exc:
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
    except (KeyError, FileNotFoundError, ValueError, RegistryError):
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

    # Story 25.4: Load UI-layer metadata from sidecar file
    metadata = _load_portfolio_metadata(registry, name)

    entry = registry.get_entry(name)
    return _portfolio_to_detail(name, portfolio, entry.latest_version, metadata)


@router.post("", response_model=dict[str, str], status_code=201)
async def create_portfolio(body: CreatePortfolioRequest) -> dict[str, str]:
    """Create and save a new portfolio.

    Story 25.4: Saves UI-layer metadata (editable_parameter_groups, etc.)
    to a sidecar metadata.json file.
    """
    _validate_portfolio_name(body.name)

    registry = get_registry()

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

    # Story 25.4: Save UI-layer metadata to sidecar file
    metadata = _extract_metadata_from_policies(body.policies)
    if metadata:
        _save_portfolio_metadata(registry, body.name, metadata)

    logger.info("event=portfolio_created name=%s version_id=%s", body.name, version_id)
    return {"version_id": version_id}


@router.put("/{name}", response_model=PortfolioDetailResponse)
async def update_portfolio(name: str, body: UpdatePortfolioRequest) -> PortfolioDetailResponse:
    """Update an existing portfolio's policies/parameters/order.

    Story 25.4: Saves UI-layer metadata to sidecar metadata.json file.
    """
    registry = get_registry()

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
    except (KeyError, FileNotFoundError, ValueError, RegistryError):
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
    existing = cast("PolicyPortfolio", registry.get(name))

    resolution_strategy = body.resolution_strategy or existing.resolution_strategy
    description = body.description if body.description is not None else existing.description

    portfolio = _build_portfolio(
        name=name,
        description=description,
        resolution_strategy=resolution_strategy,
        policies=body.policies,
    )

    version_id = registry.save(portfolio, name)

    # Story 25.4/25.5: Save UI-layer metadata to sidecar file
    # Story 25.5: Delete stale metadata when all UI-layer fields are removed
    metadata = _extract_metadata_from_policies(body.policies)
    if metadata:
        _save_portfolio_metadata(registry, name, metadata)
    else:
        _delete_portfolio_metadata(registry, name)

    logger.info("event=portfolio_updated name=%s version_id=%s", name, version_id)
    return _portfolio_to_detail(name, portfolio, version_id)


@router.delete("/{name}", status_code=204)
async def delete_portfolio(name: str) -> None:
    """Delete a portfolio from the registry."""
    registry = get_registry()
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

    # Confirm it's a portfolio before deleting — fail-closed on registry error
    try:
        entry_type = registry.get_entry_type(name)
    except (KeyError, FileNotFoundError, ValueError, RegistryError):
        entry_type = "unknown"

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

    registry = get_registry()

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
    except (KeyError, FileNotFoundError, ValueError, RegistryError):
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

    # Story 25.4: Clone metadata file if it exists
    source_metadata = _load_portfolio_metadata(registry, name)
    if source_metadata:
        _save_portfolio_metadata(registry, body.new_name, source_metadata)

    logger.info("event=portfolio_cloned source=%s target=%s version_id=%s", name, body.new_name, version_id)

    # Load metadata for the response
    cloned_metadata = _load_portfolio_metadata(registry, body.new_name)
    return _portfolio_to_detail(body.new_name, cloned, version_id, cloned_metadata)
