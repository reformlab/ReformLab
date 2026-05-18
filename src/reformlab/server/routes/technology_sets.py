# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Technology sets API routes — Story 28.1."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from reformlab.discrete_choice import (
    DEFAULT_HEATING_TECHNOLOGY_SET,
    DEFAULT_TECHNOLOGY_SET,
    DEFAULT_VEHICLE_TECHNOLOGY_SET,
    DomainTechnologySet,
)
from reformlab.server.models import (
    DomainTechnologySetResponse,
    TechnologyAlternativeModel,
    TechnologySetResponse,
)

router = APIRouter()

_VALID_DOMAINS = frozenset({"heating", "vehicle"})


def _domain_to_response(
    domain: str, domain_set: DomainTechnologySet | None = None
) -> DomainTechnologySetResponse:
    """Convert internal DomainTechnologySet to API response.

    Args:
        domain: Domain name ("heating" | "vehicle").
        domain_set: Optional pre-built domain set for testing.

    Returns:
        DomainTechnologySetResponse with camelCase keys.

    Story 28.1 / AC-3: DomainTechnologySet serialization.
    """
    if domain == "heating":
        internal = domain_set or DEFAULT_HEATING_TECHNOLOGY_SET
    elif domain == "vehicle":
        internal = domain_set or DEFAULT_VEHICLE_TECHNOLOGY_SET
    else:
        # Should never happen due to query validation
        raise HTTPException(
            status_code=422,
            detail={
                "what": "Invalid technology_set configuration",
                "why": f"Unknown domain: {domain}",
                "fix": f"Use one of: {', '.join(sorted(_VALID_DOMAINS))}",
            },
        )

    return DomainTechnologySetResponse(
        domain=internal.domain,
        enabled=internal.enabled,
        alternatives=[
            TechnologyAlternativeModel(
                id=alt.id,
                name=alt.name,
                attributes=alt.attributes,
            )
            for alt in internal.alternatives
        ],
        referenceAlternativeId=internal.reference_alternative_id,
        costColumn=internal.cost_column,
    )


@router.get("/default", response_model=DomainTechnologySetResponse)
async def get_default_technology_set(
    domain: Literal["heating", "vehicle"] = Query(..., description="Domain name"),
) -> DomainTechnologySetResponse:
    """Return the canonical default technology set for a domain.

    Args:
        domain: Decision domain name ("heating" or "vehicle").

    Returns:
        DomainTechnologySetResponse with alternatives and metadata.

    Raises:
        HTTPException 422: If domain is not "heating" or "vehicle".

    Story 28.1 / AC-3: GET /api/discrete-choice/technology-sets/default?domain=heating
    """
    return _domain_to_response(domain)


@router.get("/default/all", response_model=TechnologySetResponse)
async def get_all_default_technology_sets() -> TechnologySetResponse:
    """Return all canonical default technology sets.

    Returns a TechnologySetResponse with both heating and vehicle domains
    populated with the canonical French market defaults.

    Story 28.1 / AC-3: GET /api/discrete-choice/technology-sets/default/all
    """
    return TechnologySetResponse(
        version=DEFAULT_TECHNOLOGY_SET.version,
        domains={
            "heating": _domain_to_response("heating"),
            "vehicle": _domain_to_response("vehicle"),
        },
    )
