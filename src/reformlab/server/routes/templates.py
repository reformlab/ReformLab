# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Template listing and custom template CRUD routes."""

from __future__ import annotations

import logging
import re
from typing import Any

from fastapi import APIRouter, HTTPException

from reformlab.server.dependencies import get_registry
from reformlab.server.models import (
    BlankPolicyResponse,
    CreateBlankPolicyRequest,
    CreateCustomTemplateRequest,
    CustomTemplateResponse,
    RuntimeAvailability,
    TemplateDetailResponse,
    TemplateListItem,
)
from reformlab.templates.exceptions import ScenarioError, TemplateError
from reformlab.templates.portfolios.exceptions import PortfolioValidationError
from reformlab.templates.registry import RegistryError

logger = logging.getLogger(__name__)

router = APIRouter()

# Story 25.1 / Task 1.6: Type-to-category mapping for templates
TYPE_TO_CATEGORY: dict[str, str | None] = {
    "carbon-tax": "carbon_emissions",
    "carbon_tax": "carbon_emissions",  # API uses underscore format
    "vehicle_malus": "vehicle_emissions",
    "energy_poverty_aid": "income",
    # subsidy, rebate, feebate → None intentionally (may apply to multiple categories)
    # These will appear in "Other" group until proper metadata is added in 25.2-25.3
}


# Story 24.1 / AC-1: Live-ready policy types (from Epic 23)
# Story 24.2: Added vehicle_malus and energy_poverty_aid to live-ready types
LIVE_READY_TYPES = {
    "carbon_tax",
    "subsidy",
    "rebate",
    "feebate",
    "vehicle_malus",       # Story 24.2 — now live-ready
    "energy_poverty_aid",  # Story 24.2 — now live-ready
}


def _classify_runtime_availability(
    policy_type: str,
    is_builtin: bool,
) -> tuple[RuntimeAvailability, str | None]:
    """Classify runtime availability for a template based on its origin and type.

    Story 24.1 / AC-1, #2: Determines live_ready vs live_unavailable status.

    Args:
        policy_type: The policy type name (e.g., "carbon_tax").
        is_builtin: True if loaded from built-in YAML packs.

    Returns:
        Tuple of (runtime_availability, availability_reason).
    """
    # Story 24.2: All listed types are now live-ready
    if policy_type in LIVE_READY_TYPES:
        return "live_ready", None

    # Non-built-in templates: user-saved scenarios or user-created custom types
    if not is_builtin:
        return "live_unavailable", None

    # Fallback for unknown built-in types (safe default)
    return "live_unavailable", None


def _template_to_list_item(
    name: str,
    template: Any,
    is_builtin: bool = False,
) -> TemplateListItem:
    """Convert a domain template to a TemplateListItem."""
    from reformlab.templates.schema import CustomPolicyType

    pt = template.policy_type
    policy_type = pt.value if hasattr(pt, "value") else str(pt)
    is_custom = isinstance(pt, CustomPolicyType)

    # Story 24.1 / AC-1: Classify runtime availability
    runtime_availability, availability_reason = _classify_runtime_availability(
        policy_type, is_builtin
    )

    # Count policy fields
    params = template.policy
    param_count = 0
    param_groups: list[str] = []
    if hasattr(params, "__dataclass_fields__"):
        param_count = len(params.__dataclass_fields__)
        param_groups = list(params.__dataclass_fields__.keys())
    elif isinstance(params, dict):
        param_count = len(params)
        param_groups = list(params.keys())

    # Story 25.1 / Task 1.6: Map policy type to category
    category_id = TYPE_TO_CATEGORY.get(policy_type)

    return TemplateListItem(
        id=name,
        name=getattr(template, "name", name),
        type=policy_type,
        parameter_count=param_count,
        description=getattr(template, "description", ""),
        parameter_groups=param_groups,
        is_custom=is_custom,
        runtime_availability=runtime_availability,
        availability_reason=availability_reason,
        category_id=category_id,
    )


def _template_to_detail(
    name: str, template: Any, is_builtin: bool = False
) -> TemplateDetailResponse:
    """Convert a domain template to a TemplateDetailResponse."""
    # Story 24.1 / AC-1: Pass is_builtin for correct availability classification
    list_item = _template_to_list_item(name, template, is_builtin=is_builtin)

    # Extract default policy as dict
    params = template.policy
    default_params: dict[str, Any] = {}
    if hasattr(params, "__dataclass_fields__"):
        from dataclasses import asdict

        default_params = asdict(params)
    elif isinstance(params, dict):
        default_params = dict(params)

    return TemplateDetailResponse(
        **list_item.model_dump(),
        default_policy=default_params,
    )


def _load_builtin_packs() -> list[TemplateListItem]:
    """Discover and load all built-in template packs shipped with ReformLab."""
    from reformlab.templates.loader import load_scenario_template
    from reformlab.templates.packs import _PACKS_DIR

    items: list[TemplateListItem] = []
    if not _PACKS_DIR.exists():
        return items

    for pack_dir in sorted(_PACKS_DIR.iterdir()):
        if not pack_dir.is_dir() or pack_dir.name.startswith("_"):
            continue
        for yaml_file in sorted(pack_dir.glob("*.yaml")):
            try:
                template = load_scenario_template(yaml_file)
                # Story 24.1 / AC-1: Built-in templates have is_builtin=True
                items.append(
                    _template_to_list_item(yaml_file.stem, template, is_builtin=True)
                )
            except (TemplateError, ScenarioError, OSError):
                logger.warning("Failed to load pack template '%s', skipping", yaml_file)

    return items


def _load_builtin_template(name: str) -> Any | None:
    """Load a single built-in template by name (YAML stem), or return None."""
    from reformlab.templates.loader import load_scenario_template
    from reformlab.templates.packs import _PACKS_DIR

    if not _PACKS_DIR.exists():
        return None

    for pack_dir in sorted(_PACKS_DIR.iterdir()):
        if not pack_dir.is_dir() or pack_dir.name.startswith("_"):
            continue
        yaml_file = pack_dir / f"{name}.yaml"
        if yaml_file.exists():
            try:
                return load_scenario_template(yaml_file)
            except (TemplateError, ScenarioError, OSError):
                return None
    return None


@router.get("", response_model=dict[str, list[TemplateListItem]])
async def list_templates() -> dict[str, list[TemplateListItem]]:
    """List available policy templates."""
    items: list[TemplateListItem] = []
    seen_names: set[str] = set()

    # 1. Built-in template packs (YAML files shipped with ReformLab)
    for item in _load_builtin_packs():
        if item.id not in seen_names:
            items.append(item)
            seen_names.add(item.id)

    # 2. User-saved scenarios from the registry
    registry = get_registry()
    for name in registry.list_scenarios():
        if name in seen_names:
            continue
        try:
            template = registry.get(name)
            # Story 24.1 / AC-1: User-saved scenarios have is_builtin=False
            items.append(_template_to_list_item(name, template, is_builtin=False))
            seen_names.add(name)
        except (
            KeyError,
            FileNotFoundError,
            ValueError,
            AttributeError,
            RegistryError,
            PortfolioValidationError,
        ):
            logger.warning("Failed to load template '%s', skipping", name)

    # 3. In-memory custom registrations not already listed
    from reformlab.templates.schema import list_custom_registrations

    for type_name, params_class in list_custom_registrations().items():
        if type_name in seen_names:
            continue
        param_count = 0
        param_groups: list[str] = []
        if hasattr(params_class, "__dataclass_fields__"):
            param_count = len(params_class.__dataclass_fields__)
            param_groups = list(params_class.__dataclass_fields__.keys())
        # Story 24.2: Built-in custom types (vehicle_malus, energy_poverty_aid)
        # are shipped with the package and should be classified as built-in
        # for runtime availability purposes.
        is_builtin_custom = type_name in LIVE_READY_TYPES
        runtime_availability, availability_reason = _classify_runtime_availability(
            type_name, is_builtin=is_builtin_custom
        )
        # Story 25.1 / Task 1.6: Map policy type to category
        category_id = TYPE_TO_CATEGORY.get(type_name)

        items.append(
            TemplateListItem(
                id=type_name,
                name=type_name,
                type=type_name,
                parameter_count=param_count,
                description="",
                parameter_groups=param_groups,
                is_custom=True,
                runtime_availability=runtime_availability,
                availability_reason=availability_reason,
                category_id=category_id,
            )
        )

    # Story 24.1 / Code Review: Enforce deterministic ordering (group by type, sort by id)
    items.sort(key=lambda t: (t.type, t.id))

    return {"templates": items}


@router.get("/{name}", response_model=TemplateDetailResponse)
async def get_template(name: str) -> TemplateDetailResponse:
    """Get a template with full parameter details."""
    # 1. Try the scenario registry (user-saved scenarios)
    registry = get_registry()
    try:
        template = registry.get(name)
        # Story 24.1 / AC-1: User-saved scenarios have is_builtin=False
        return _template_to_detail(name, template, is_builtin=False)
    except (KeyError, FileNotFoundError, ValueError, RegistryError, PortfolioValidationError):
        pass

    # 2. Try built-in template packs (YAML files)
    builtin_template = _load_builtin_template(name)
    if builtin_template is not None:
        # Story 24.1 / AC-1: Built-in templates have is_builtin=True
        return _template_to_detail(name, builtin_template, is_builtin=True)

    # 3. Try in-memory custom registrations
    from reformlab.templates.schema import list_custom_registrations

    custom = list_custom_registrations()
    if name in custom:
        params_class = custom[name]
        param_count = 0
        param_groups: list[str] = []
        default_policy: dict[str, Any] = {}
        if hasattr(params_class, "__dataclass_fields__"):
            param_count = len(params_class.__dataclass_fields__)
            param_groups = list(params_class.__dataclass_fields__.keys())
        # Story 24.2: Built-in custom types (vehicle_malus, energy_poverty_aid)
        # are shipped with the package and should be classified as built-in
        # for runtime availability purposes.
        is_builtin_custom = name in LIVE_READY_TYPES
        runtime_availability, availability_reason = _classify_runtime_availability(
            name, is_builtin=is_builtin_custom
        )
        # Story 25.1 / Task 1.6: Map policy type to category
        category_id = TYPE_TO_CATEGORY.get(name)
        return TemplateDetailResponse(
            id=name,
            name=name,
            type=name,
            parameter_count=param_count,
            description="",
            parameter_groups=param_groups,
            is_custom=True,
            runtime_availability=runtime_availability,
            availability_reason=availability_reason,
            category_id=category_id,
            default_policy=default_policy,
        )

    raise HTTPException(
        status_code=404,
        detail={
            "what": f"Template '{name}' not found",
            "why": f"No built-in, saved, or custom template named '{name}'",
            "fix": "Check the template name",
        },
    )


_SNAKE_CASE_RE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")


@router.post("/custom", response_model=CustomTemplateResponse, status_code=201)
async def create_custom_template(body: CreateCustomTemplateRequest) -> CustomTemplateResponse:
    """Register a custom template with a parameter schema.

    Dynamically creates a frozen dataclass from the provided parameter specs
    and registers it as a custom policy type.
    """
    import dataclasses

    from reformlab.templates.schema import (
        PolicyParameters,
        PolicyType,
        register_custom_template,
        register_policy_type,
    )

    # Validate name is snake_case
    if not _SNAKE_CASE_RE.match(body.name):
        raise HTTPException(
            status_code=422,
            detail={
                "what": "Invalid template name",
                "why": f"Name must be snake_case: {body.name!r}",
                "fix": "Use lowercase letters, digits, and underscores (e.g. 'my_template')",
            },
        )

    # Reject collision with built-in types
    builtin_values = {pt.value for pt in PolicyType}
    if body.name in builtin_values:
        raise HTTPException(
            status_code=409,
            detail={
                "what": "Name collision",
                "why": f"'{body.name}' is a built-in policy type",
                "fix": "Choose a different name",
            },
        )

    if not body.parameters:
        raise HTTPException(
            status_code=422,
            detail={
                "what": "No parameters",
                "why": "Custom templates must define at least one parameter",
                "fix": "Add parameters to the request body",
            },
        )

    # Build dataclass fields from parameter specs
    type_map = {"float": float, "int": int, "str": str}
    fields: list[tuple[str, type, Any]] = []
    for param in body.parameters:
        field_type = type_map.get(param.type, float)
        if param.default is not None:
            default = param.default
        elif field_type is float:
            default = 0.0
        elif field_type is int:
            default = 0
        else:
            default = ""
        fields.append((param.name, field_type, dataclasses.field(default=default)))

    # Create frozen dataclass dynamically
    cls_name = "".join(word.capitalize() for word in body.name.split("_")) + "Parameters"
    params_class = dataclasses.make_dataclass(
        cls_name,
        fields,
        bases=(PolicyParameters,),
        frozen=True,
    )

    try:
        custom_type = register_policy_type(body.name)
        register_custom_template(custom_type, params_class)
    except TemplateError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "what": "Registration failed",
                "why": str(exc),
                "fix": "Choose a different name or check existing registrations",
            },
        ) from exc

    return CustomTemplateResponse(
        name=body.name,
        description=body.description,
        parameter_count=len(body.parameters),
    )


@router.delete("/custom/{name}", status_code=204)
async def delete_custom_template(name: str) -> None:
    """Unregister a custom template.

    Built-in templates cannot be deleted (403). Returns 404 if the custom
    template is not found.
    """
    from reformlab.templates.schema import PolicyType, unregister_policy_type

    # Check if it's a built-in type
    builtin_values = {pt.value for pt in PolicyType}
    if name in builtin_values:
        raise HTTPException(
            status_code=403,
            detail={
                "what": "Cannot delete built-in template",
                "why": f"'{name}' is a built-in policy type",
                "fix": "Only custom templates can be deleted",
            },
        )

    try:
        unregister_policy_type(name)
    except TemplateError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "what": f"Custom template '{name}' not found",
                "why": str(exc),
                "fix": "Check the template name",
            },
        ) from exc


# ============================================================================
# Story 25.3: POST /api/templates/from-scratch
# ============================================================================

_VALID_POLICY_TYPES = {"tax", "subsidy", "transfer"}

_TYPE_TO_LABELS = {
    "tax": "Tax",
    "subsidy": "Subsidy",
    "transfer": "Transfer",
}

# Default parameter groups by policy type (Story 25.3, AC-4, AC-5, AC-6)
_DEFAULT_PARAMETER_GROUPS: dict[str, list[str]] = {
    "tax": ["Mechanism", "Eligibility", "Schedule", "Redistribution"],
    "subsidy": ["Mechanism", "Eligibility", "Schedule"],
    "transfer": ["Mechanism", "Eligibility", "Schedule"],
}


def _get_category_label(category_id: str) -> str:
    """Get human-readable label for a category ID."""
    from reformlab.server.routes.categories import _CATEGORY_DEFINITIONS

    for cat in _CATEGORY_DEFINITIONS:
        if cat.id == category_id:
            return cat.label
    # Fallback: convert snake_case to Title Case
    return category_id.replace("_", " ").title()


def _validate_category_exists(category_id: str) -> None:
    """Validate that a category ID exists in the registry.

    Raises:
        HTTPException: 400 if category_id not found
    """
    from reformlab.server.routes.categories import _CATEGORY_DEFINITIONS

    category_ids = {cat.id for cat in _CATEGORY_DEFINITIONS}
    if category_id not in category_ids:
        raise HTTPException(
            status_code=400,
            detail={
                "what": f"Category '{category_id}' not found",
                "why": f"Category must be one of: {', '.join(sorted(category_ids))}",
                "fix": "Select a valid category ID",
            },
        )


def _validate_category_compatible(category_id: str, policy_type: str) -> None:
    """Validate that a category is compatible with the requested policy type.

    Raises:
        HTTPException: 400 if category is not compatible with policy_type
    """
    from reformlab.server.routes.categories import _CATEGORY_DEFINITIONS

    for cat in _CATEGORY_DEFINITIONS:
        if cat.id == category_id:
            if policy_type not in cat.compatible_types:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "what": f"Category '{category_id}' is not compatible with '{policy_type}'",
                        "why": f"Category only supports: {', '.join(cat.compatible_types)}",
                        "fix": "Select a compatible category or change policy type",
                    },
                )
            return

    # Should not reach here if _validate_category_exists was called first
    raise HTTPException(
        status_code=400,
        detail={
            "what": f"Category '{category_id}' not found",
            "why": "Category does not exist",
            "fix": "Select a valid category ID",
        },
    )


@router.post("/from-scratch", response_model=BlankPolicyResponse, status_code=201)
async def create_blank_policy(body: CreateBlankPolicyRequest) -> BlankPolicyResponse:
    """Create a blank policy from scratch with default parameter groups.

    Story 25.3: Allows users to create policies by selecting a type and category,
    rather than starting from a template.

    Args:
        body: Request with policy_type and category_id

    Returns:
        BlankPolicyResponse with auto-generated name and default parameters

    Raises:
        HTTPException: 400 if validation fails
    """
    # Validate policy_type is in closed set (lowercase)
    if body.policy_type not in _VALID_POLICY_TYPES:
        raise HTTPException(
            status_code=400,
            detail={
                "what": f"Invalid policy type '{body.policy_type}'",
                "why": f"Policy type must be one of: {', '.join(sorted(_VALID_POLICY_TYPES))}",
                "fix": "Select a valid policy type (tax, subsidy, or transfer)",
            },
        )

    # Validate category exists
    _validate_category_exists(body.category_id)

    # Validate category is compatible with policy type
    _validate_category_compatible(body.category_id, body.policy_type)

    # Generate auto-generated name: "{Type} — {Category}"
    type_label = _TYPE_TO_LABELS[body.policy_type]
    category_label = _get_category_label(body.category_id)
    name = f"{type_label} — {category_label}"

    # Default placeholder parameters
    parameters: dict[str, Any] = {
        "rate": 0,
        "unit": "EUR",
        "threshold": 0,
        "ceiling": None,
    }

    # Get default parameter groups for the policy type
    parameter_groups = _DEFAULT_PARAMETER_GROUPS.get(body.policy_type, [])

    return BlankPolicyResponse(
        name=name,
        policy_type=body.policy_type,
        category_id=body.category_id,
        parameters=parameters,
        parameter_groups=parameter_groups,
        rate_schedule={},
    )
