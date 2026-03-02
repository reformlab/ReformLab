"""Template listing routes."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from reformlab.server.models import TemplateDetailResponse, TemplateListItem

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
    pt = template.policy_type
    policy_type = pt.value if hasattr(pt, "value") else str(pt)

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
    for name in names:
        try:
            template = registry.get(name)
            items.append(_template_to_list_item(name, template))
        except Exception:
            logger.warning("Failed to load template '%s', skipping", name)

    return {"templates": items}


@router.get("/{name}", response_model=TemplateDetailResponse)
async def get_template(name: str) -> TemplateDetailResponse:
    """Get a template with full parameter details."""
    registry = _get_registry()
    try:
        template = registry.get(name)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return _template_to_detail(name, template)
