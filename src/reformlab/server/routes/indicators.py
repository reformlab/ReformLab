"""Indicator computation routes."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from reformlab.server.dependencies import ResultCache, get_result_cache
from reformlab.server.models import (
    ComparisonRequest,
    IndicatorRequest,
    IndicatorResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

VALID_INDICATOR_TYPES = {"distributional", "geographic", "welfare", "fiscal"}


def _indicator_result_to_response(
    indicator_type: str, result: Any
) -> IndicatorResponse:
    """Convert an IndicatorResult to an IndicatorResponse."""
    table = result.to_table()
    data: dict[str, list[Any]] = table.to_pydict()

    return IndicatorResponse(
        indicator_type=indicator_type,
        data=data,
        metadata=result.metadata,
        warnings=result.warnings,
        excluded_count=result.excluded_count,
    )


@router.post("/{indicator_type}", response_model=IndicatorResponse)
async def compute_indicator(
    indicator_type: str,
    body: IndicatorRequest,
    cache: ResultCache = Depends(get_result_cache),
) -> IndicatorResponse:
    """Compute an indicator from a cached simulation result."""
    if indicator_type not in VALID_INDICATOR_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid indicator type '{indicator_type}'. "
            f"Must be one of: {', '.join(sorted(VALID_INDICATOR_TYPES))}",
        )

    result = cache.get(body.run_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Run ID '{body.run_id}' not found in cache",
        )

    kwargs: dict[str, Any] = {}
    if indicator_type == "distributional":
        kwargs["income_field"] = body.income_field
        kwargs["by_year"] = body.by_year
    elif indicator_type in ("geographic", "fiscal"):
        kwargs["by_year"] = body.by_year

    indicator_result = result.indicators(indicator_type, **kwargs)
    return _indicator_result_to_response(indicator_type, indicator_result)


comparison_router = APIRouter()


@comparison_router.post("", response_model=IndicatorResponse)
async def compute_comparison(
    body: ComparisonRequest,
    cache: ResultCache = Depends(get_result_cache),
) -> IndicatorResponse:
    """Compute welfare comparison between baseline and reform runs."""
    baseline = cache.get(body.baseline_run_id)
    if baseline is None:
        raise HTTPException(
            status_code=404,
            detail=f"Baseline run ID '{body.baseline_run_id}' not found in cache",
        )

    reform = cache.get(body.reform_run_id)
    if reform is None:
        raise HTTPException(
            status_code=404,
            detail=f"Reform run ID '{body.reform_run_id}' not found in cache",
        )

    indicator_result = baseline.indicators(
        "welfare",
        reform_result=reform,
        welfare_field=body.welfare_field,
        threshold=body.threshold,
    )
    return _indicator_result_to_response("welfare", indicator_result)
