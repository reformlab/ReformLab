"""Indicator computation routes."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException

from reformlab.server.dependencies import ResultCache, get_result_cache, get_result_store
from reformlab.server.models import (
    ComparisonData,
    ComparisonRequest,
    CrossMetricItem,
    IndicatorRequest,
    IndicatorResponse,
    PortfolioComparisonRequest,
    PortfolioComparisonResponse,
)
from reformlab.server.result_store import ResultNotFound

if TYPE_CHECKING:
    from reformlab.server.result_store import ResultStore

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
    store: ResultStore = Depends(get_result_store),
) -> IndicatorResponse:
    """Compute an indicator from a cached simulation result."""
    if indicator_type not in VALID_INDICATOR_TYPES:
        raise HTTPException(
            status_code=422,
            detail={
                "what": f"Invalid indicator type '{indicator_type}'",
                "why": f"Must be one of: {sorted(VALID_INDICATOR_TYPES)}",
                "fix": "Use a valid indicator type from the list",
            },
        )

    if indicator_type == "welfare":
        raise HTTPException(
            status_code=422,
            detail={
                "what": "Welfare indicator requires two simulation runs",
                "why": "Welfare compares a baseline and reform run; a single run_id is insufficient",
                "fix": "Use POST /api/comparison with baseline_run_id and reform_run_id instead",
            },
        )

    # Step 1: Check ResultStore metadata (404 if completely unknown)
    try:
        store.get_metadata(body.run_id)
    except ResultNotFound:
        raise HTTPException(
            status_code=404,
            detail={
                "what": f"Run '{body.run_id}' not found",
                "why": "No metadata record exists for this run_id",
                "fix": "Check the run_id and ensure the simulation has been executed",
            },
        )

    # Step 2: Check ResultCache (409 if in store but evicted or panel_output is None)
    result = cache.get(body.run_id)
    if result is None or result.panel_output is None:
        raise HTTPException(
            status_code=409,
            detail={
                "what": f"Run '{body.run_id}' data is not available",
                "why": "The simulation result has been evicted from the in-memory cache",
                "fix": "Re-run the simulation or select runs with data_available=true",
            },
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

# ---------------------------------------------------------------------------
# Reserved label validation helpers
# ---------------------------------------------------------------------------

_RESERVED_LABEL_NAMES = frozenset(
    {"field_name", "decile", "year", "metric", "value", "region"}
)
_RESERVED_LABEL_PREFIXES = ("delta_", "pct_delta_")


def _is_safe_label(label: str) -> bool:
    """Return False if label conflicts with reserved column names/prefixes."""
    if label in _RESERVED_LABEL_NAMES:
        return False
    for prefix in _RESERVED_LABEL_PREFIXES:
        if label.startswith(prefix):
            return False
    return True


def _derive_label(run_id: str, store: ResultStore) -> str:
    """Derive a human-readable label for a run from its stored metadata."""
    try:
        meta = store.get_metadata(run_id)
        if meta.portfolio_name:
            return meta.portfolio_name
        if meta.template_name:
            return meta.template_name
        return run_id[:8]
    except ResultNotFound:
        return run_id[:8]


def _deduplicate_labels(labels: list[str]) -> list[str]:
    """Append _2, _3, ... suffixes to resolve duplicate labels."""
    seen: dict[str, int] = {}
    result: list[str] = []
    for label in labels:
        count = seen.get(label, 0)
        seen[label] = count + 1
        if count == 0:
            result.append(label)
        else:
            result.append(f"{label}_{count + 1}")
    return result


@comparison_router.post("/portfolios", response_model=PortfolioComparisonResponse)
async def compare_portfolio_runs(
    body: PortfolioComparisonRequest,
    cache: ResultCache = Depends(get_result_cache),
    store: ResultStore = Depends(get_result_store),
) -> PortfolioComparisonResponse:
    """Compare indicator results across multiple portfolio simulation runs.

    AC-1: validates 2–5 run IDs, rejects duplicates
    AC-2: returns per-indicator comparison data for all selected runs
    AC-5: returns cross-comparison aggregate metrics
    """
    from reformlab.indicators.portfolio_comparison import (
        PortfolioComparisonConfig,
        PortfolioComparisonInput,
        compare_portfolios,
    )

    # 1. Validate run count
    if len(body.run_ids) < 2 or len(body.run_ids) > 5:
        raise HTTPException(
            status_code=422,
            detail={
                "what": f"Invalid number of run_ids: {len(body.run_ids)}",
                "why": "Comparison requires 2–5 run IDs",
                "fix": "Provide between 2 and 5 run_ids in the request body",
            },
        )

    # 1b. Validate baseline_run_id is in run_ids (if provided)
    if body.baseline_run_id is not None and body.baseline_run_id not in body.run_ids:
        raise HTTPException(
            status_code=422,
            detail={
                "what": f"baseline_run_id '{body.baseline_run_id}' is not in run_ids",
                "why": "The baseline run must be one of the selected run_ids",
                "fix": "Set baseline_run_id to one of the provided run_ids, or omit it to use the first run",
            },
        )

    # 1c. Validate no duplicates
    if len(body.run_ids) != len(set(body.run_ids)):
        seen: set[str] = set()
        dupes = [r for r in body.run_ids if r in seen or seen.add(r)]  # type: ignore[func-returns-value]
        raise HTTPException(
            status_code=422,
            detail={
                "what": f"Duplicate run_ids detected: {dupes}",
                "why": "Each run_id must be unique in the comparison request",
                "fix": "Remove duplicate run_ids from the request body",
            },
        )

    # 2. Resolve each run from store and cache
    sim_results = []
    for run_id in body.run_ids:
        # Check store first (404 if completely unknown)
        try:
            store.get_metadata(run_id)
        except ResultNotFound:
            raise HTTPException(
                status_code=404,
                detail={
                    "what": f"Run '{run_id}' not found",
                    "why": "No metadata record exists for this run_id",
                    "fix": "Check the run_id and ensure the simulation has been executed",
                },
            )

        # Check cache (409 if in store but evicted from cache)
        sim_result = cache.get(run_id)
        if sim_result is None or sim_result.panel_output is None:
            raise HTTPException(
                status_code=409,
                detail={
                    "what": f"Run '{run_id}' data is not available",
                    "why": "The simulation result has been evicted from the in-memory cache",
                    "fix": "Re-run the simulation or select runs with data_available=true",
                },
            )
        sim_results.append((run_id, sim_result))

    # 3. Derive labels
    raw_labels = [_derive_label(run_id, store) for run_id, _ in sim_results]
    labels = _deduplicate_labels(raw_labels)

    # 4. Validate labels (reserved names/prefixes)
    unsafe = [label for label in labels if not _is_safe_label(label)]
    if unsafe:
        raise HTTPException(
            status_code=422,
            detail={
                "what": f"Derived portfolio labels conflict with reserved names: {unsafe}",
                "why": "Labels cannot match reserved column names or use delta_/pct_delta_ prefixes",
                "fix": "Rename the portfolio or scenario so its derived label is not reserved",
            },
        )

    # 5. Build PortfolioComparisonInput list
    inputs = [
        PortfolioComparisonInput(label=label, panel=sim_result.panel_output)  # type: ignore[arg-type]
        for label, (_, sim_result) in zip(labels, sim_results)
    ]

    # 6. Resolve baseline label
    baseline_label: str | None = None
    if body.baseline_run_id is not None:
        idx = next(
            (i for i, (run_id, _) in enumerate(sim_results) if run_id == body.baseline_run_id),
            None,
        )
        if idx is not None:
            baseline_label = labels[idx]

    # 7. Run comparison
    indicator_types_tuple = tuple(body.indicator_types)
    # Remove "welfare" from indicator_types since it's controlled by include_welfare
    filtered_types = tuple(t for t in indicator_types_tuple if t != "welfare")

    config = PortfolioComparisonConfig(
        baseline_label=baseline_label,
        indicator_types=filtered_types,
        include_welfare=body.include_welfare,
        include_deltas=body.include_deltas,
        include_pct_deltas=body.include_pct_deltas,
    )

    try:
        result = compare_portfolios(inputs, config)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "what": "Portfolio comparison failed",
                "why": str(exc),
                "fix": "Check run_ids and ensure all runs completed successfully",
            },
        ) from exc

    # 8. Serialize result
    comparison_data: dict[str, ComparisonData] = {}
    for ind_type, comp_result in result.comparisons.items():
        table_dict: dict[str, list[Any]] = {
            k: list(v) for k, v in comp_result.table.to_pydict().items()
        }
        comparison_data[ind_type] = ComparisonData(
            columns=comp_result.table.schema.names,
            data=table_dict,
        )

    cross_metrics_list = [
        CrossMetricItem(
            criterion=m.criterion,
            best_portfolio=m.best_portfolio,
            value=m.value,
            all_values=dict(m.all_values),
        )
        for m in result.cross_metrics
    ]

    return PortfolioComparisonResponse(
        comparisons=comparison_data,
        cross_metrics=cross_metrics_list,
        portfolio_labels=list(result.portfolio_labels),
        metadata=result.metadata,
        warnings=result.warnings,
    )


@comparison_router.post("", response_model=IndicatorResponse)
async def compute_comparison(
    body: ComparisonRequest,
    cache: ResultCache = Depends(get_result_cache),
    store: ResultStore = Depends(get_result_store),
) -> IndicatorResponse:
    """Compute welfare comparison between baseline and reform runs."""
    # Two-step lookup for baseline
    try:
        store.get_metadata(body.baseline_run_id)
    except ResultNotFound:
        raise HTTPException(
            status_code=404,
            detail={
                "what": f"Baseline run '{body.baseline_run_id}' not found",
                "why": "No metadata record exists for this run_id",
                "fix": "Check the baseline_run_id and ensure the simulation has been executed",
            },
        )

    baseline = cache.get(body.baseline_run_id)
    if baseline is None or baseline.panel_output is None:
        raise HTTPException(
            status_code=409,
            detail={
                "what": f"Baseline run '{body.baseline_run_id}' data is not available",
                "why": "The simulation result has been evicted from the in-memory cache",
                "fix": "Re-run the simulation or select runs with data_available=true",
            },
        )

    # Two-step lookup for reform
    try:
        store.get_metadata(body.reform_run_id)
    except ResultNotFound:
        raise HTTPException(
            status_code=404,
            detail={
                "what": f"Reform run '{body.reform_run_id}' not found",
                "why": "No metadata record exists for this run_id",
                "fix": "Check the reform_run_id and ensure the simulation has been executed",
            },
        )

    reform = cache.get(body.reform_run_id)
    if reform is None or reform.panel_output is None:
        raise HTTPException(
            status_code=409,
            detail={
                "what": f"Reform run '{body.reform_run_id}' data is not available",
                "why": "The simulation result has been evicted from the in-memory cache",
                "fix": "Re-run the simulation or select runs with data_available=true",
            },
        )

    indicator_result = baseline.indicators(
        "welfare",
        reform_result=reform,
        welfare_field=body.welfare_field,
        threshold=body.threshold,
    )
    return _indicator_result_to_response("welfare", indicator_result)
