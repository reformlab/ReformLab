# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Template listing and custom template CRUD routes."""

from __future__ import annotations

import logging
import re
from typing import Any

from fastapi import APIRouter, HTTPException

from reformlab.server.models import (
    CreateCustomTemplateRequest,
    CustomTemplateResponse,
    TemplateDetailResponse,
    TemplateListItem,
)
from reformlab.templates.exceptions import TemplateError
from reformlab.templates.registry import RegistryError

logger = logging.getLogger(__name__)

router = APIRouter()

# Module-level singleton to avoid re-scanning on every request
_registry: Any = None


def _get_registry() -> Any:
    """Return a lazily-initialized ScenarioRegistry singleton."""
    global _registry  # noqa: PLW0603
    if _registry is None:
        from reformlab.templates.registry import ScenarioRegistry

        _registry = ScenarioRegistry()
    return _registry


def _template_to_list_item(name: str, template: Any) -> TemplateListItem:
    """Convert a domain template to a TemplateListItem."""
    from reformlab.templates.schema import CustomPolicyType

    pt = template.policy_type
    policy_type = pt.value if hasattr(pt, "value") else str(pt)
    is_custom = isinstance(pt, CustomPolicyType)

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

    return TemplateListItem(
        id=name,
        name=getattr(template, "name", name),
        type=policy_type,
        parameter_count=param_count,
        description=getattr(template, "description", ""),
        parameter_groups=param_groups,
        is_custom=is_custom,
    )


def _template_to_detail(name: str, template: Any) -> TemplateDetailResponse:
    """Convert a domain template to a TemplateDetailResponse."""
    list_item = _template_to_list_item(name, template)

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


@router.get("", response_model=dict[str, list[TemplateListItem]])
async def list_templates() -> dict[str, list[TemplateListItem]]:
    """List available policy templates."""
    registry = _get_registry()
    names = registry.list_scenarios()

    items: list[TemplateListItem] = []
    seen_names: set[str] = set()
    for name in names:
        try:
            template = registry.get(name)
            items.append(_template_to_list_item(name, template))
            seen_names.add(name)
        except (KeyError, FileNotFoundError, ValueError, AttributeError, RegistryError):
            logger.warning("Failed to load template '%s', skipping", name)

    # Include in-memory custom registrations not already in the registry
    from reformlab.templates.schema import list_custom_registrations

    for type_name, params_class in list_custom_registrations().items():
        if type_name in seen_names:
            continue
        param_count = 0
        param_groups: list[str] = []
        if hasattr(params_class, "__dataclass_fields__"):
            param_count = len(params_class.__dataclass_fields__)
            param_groups = list(params_class.__dataclass_fields__.keys())
        items.append(
            TemplateListItem(
                id=type_name,
                name=type_name,
                type=type_name,
                parameter_count=param_count,
                description="",
                parameter_groups=param_groups,
                is_custom=True,
            )
        )

    return {"templates": items}


@router.get("/{name}", response_model=TemplateDetailResponse)
async def get_template(name: str) -> TemplateDetailResponse:
    """Get a template with full parameter details."""
    registry = _get_registry()
    try:
        template = registry.get(name)
    except (KeyError, FileNotFoundError, ValueError, RegistryError) as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "what": f"Template '{name}' not found",
                "why": str(exc),
                "fix": "Check the template name",
            },
        ) from exc

    return _template_to_detail(name, template)


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
