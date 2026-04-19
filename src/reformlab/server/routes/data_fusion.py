# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Data fusion API routes for Story 17.1 — Data Fusion Workbench GUI.

Provides endpoints for browsing available data sources, querying merge method
descriptions, and executing the population generation pipeline.

All endpoints wrap the Epic 11 population generation library without importing
OpenFisca — computation stays inside the population module.

References:
    Story 17.1 — AC-1 (data source browsing), AC-2 (variable overlap),
    AC-3 (merge method explanation), AC-4 (generation feedback),
    AC-5 (population preview and validation).
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from reformlab.server.models import (
    AssumptionRecordItem,
    ColumnInfo,
    DataSourceDetail,
    DataSourceItem,
    GeneratePopulationRequest,
    GeneratePopulationResponse,
    MarginalResultItem,
    MergeMethodInfo,
    MergeMethodParamSpec,
    PopulationPreviewColumnInfo,
    PopulationPreviewResponse,
    PopulationProfileResponse,
    PopulationSummary,
    StepLogItem,
    ValidationResultResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================================
# Provider → catalog mapping (built at import time, no network required)
# ============================================================================

_VALID_PROVIDERS = frozenset({"insee", "eurostat", "ademe", "sdes"})
_VALID_MERGE_METHODS = frozenset({"uniform", "ipf", "conditional"})

# ============================================================================
# Provider evidence mapping (Story 21.2 / AC6)
# ============================================================================
# All current providers are open-official/fetched/production-safe with structural data class
_PROVIDER_EVIDENCE: dict[str, dict[str, str]] = {
    "insee": {
        "origin": "open-official",
        "access_mode": "fetched",
        "trust_status": "production-safe",
        "data_class": "structural",
    },
    "eurostat": {
        "origin": "open-official",
        "access_mode": "fetched",
        "trust_status": "production-safe",
        "data_class": "structural",
    },
    "ademe": {
        "origin": "open-official",
        "access_mode": "fetched",
        "trust_status": "production-safe",
        "data_class": "structural",
    },
    "sdes": {
        "origin": "open-official",
        "access_mode": "fetched",
        "trust_status": "production-safe",
        "data_class": "structural",
    },
}


def _problem_detail(what: str, why: str, fix: str) -> dict[str, str]:
    """Build the standard API error detail payload."""
    return {"what": what, "why": why, "fix": fix}


def _build_source_item(provider: str, dataset_id: str, dataset: Any) -> DataSourceItem:
    """Convert a catalog dataset entry to a DataSourceItem response model.

    Story 21.2 / AC6: Populates evidence metadata from provider catalog.
    """
    col_count = len(dataset.columns) if hasattr(dataset, "columns") else 0

    # Story 21.2 code review fix: Fail-fast for unknown providers instead of silent INSEE fallback
    if provider not in _PROVIDER_EVIDENCE:
        raise HTTPException(
            status_code=422,
            detail=_problem_detail(
                "Unknown provider evidence mapping",
                f"Provider {provider!r} has no evidence classification mapping",
                f"Use one of: {sorted(_VALID_PROVIDERS)}",
            ),
        )

    evidence = _PROVIDER_EVIDENCE[provider]
    return DataSourceItem(
        id=dataset_id,
        provider=provider,
        name=dataset_id.replace("_", " ").title(),
        description=dataset.description,
        variable_count=col_count,
        record_count=None,
        source_url=dataset.url,
        # Story 21.2 / AC6: Evidence fields from provider mapping
        origin=evidence["origin"],
        access_mode=evidence["access_mode"],
        trust_status=evidence["trust_status"],
        data_class="structural",  # All fusion sources are structural in current phase
    )


def _build_source_detail(provider: str, dataset_id: str, dataset: Any) -> DataSourceDetail:
    """Convert a catalog dataset entry to a DataSourceDetail response model."""
    item = _build_source_item(provider, dataset_id, dataset)
    columns: list[ColumnInfo] = []
    if hasattr(dataset, "columns"):
        for _raw, project_name in dataset.columns:
            columns.append(ColumnInfo(name=project_name, description=project_name.replace("_", " ").title()))
    return DataSourceDetail(**item.model_dump(), columns=columns)


def _get_catalog_for_provider(provider: str) -> dict[str, Any] | None:
    """Return the catalog dict for a given provider, or None if unknown."""
    from reformlab.population import (
        ADEME_CATALOG,
        EUROSTAT_CATALOG,
        INSEE_CATALOG,
        SDES_CATALOG,
    )

    catalogs: dict[str, dict[str, Any]] = {
        "insee": INSEE_CATALOG,
        "eurostat": EUROSTAT_CATALOG,
        "ademe": ADEME_CATALOG,
        "sdes": SDES_CATALOG,
    }
    return catalogs.get(provider)


# ============================================================================
# Merge method static definitions (plain-language descriptions from Dev Notes)
# ============================================================================

_MERGE_METHODS: list[MergeMethodInfo] = [
    MergeMethodInfo(
        id="uniform",
        name="Uniform Distribution",
        what_it_does=(
            "Matches each household from one source to a randomly chosen "
            "household from another source, with equal probability."
        ),
        assumption=(
            "Variables in the two sources are statistically independent — "
            "knowing a household's income tells you nothing about their vehicle type."
        ),
        when_appropriate=(
            "Quick baseline when no better information is available about correlations between sources."
        ),
        tradeoff=(
            "Fast and simple, but may produce unrealistic combinations "
            "(e.g., low-income household paired with luxury vehicle)."
        ),
        parameters=[
            MergeMethodParamSpec(
                name="seed",
                type="int",
                description="Random seed for deterministic results (default: 42)",
                required=False,
            ),
        ],
    ),
    MergeMethodInfo(
        id="ipf",
        name="Iterative Proportional Fitting (IPF)",
        what_it_does=(
            "Adjusts matching weights so that the final population matches "
            "known aggregate statistics (marginals) from official sources."
        ),
        assumption=(
            "The population matches known distribution totals — if INSEE says "
            "10% of households are in decile 1, the result respects that."
        ),
        when_appropriate=("You have reliable census or administrative marginals to calibrate against."),
        tradeoff=(
            "More accurate aggregates, but requires knowing the target marginals "
            "upfront; may not converge if constraints are contradictory."
        ),
        parameters=[
            MergeMethodParamSpec(
                name="seed",
                type="int",
                description="Random seed for deterministic results (default: 42)",
                required=False,
            ),
            MergeMethodParamSpec(
                name="ipf_constraints",
                type="list[constraint]",
                description="List of {dimension, targets} marginal constraints to satisfy",
                required=False,
            ),
        ],
    ),
    MergeMethodInfo(
        id="conditional",
        name="Conditional Sampling",
        what_it_does=(
            "Groups households by a shared variable (e.g., income bracket), "
            "then matches randomly only within the same group."
        ),
        assumption=(
            "Given the grouping variable, remaining variables are independent — "
            "within the same income bracket, vehicle and heating choices are uncorrelated."
        ),
        when_appropriate=(
            "You know that some variable (like income or region) correlates with variables in both sources."
        ),
        tradeoff=(
            "Preserves known correlations through the grouping variable, "
            "but assumes independence within groups."
        ),
        parameters=[
            MergeMethodParamSpec(
                name="seed",
                type="int",
                description="Random seed for deterministic results (default: 42)",
                required=False,
            ),
            MergeMethodParamSpec(
                name="strata_columns",
                type="list[str]",
                description="Shared column names to use for stratification",
                required=False,
            ),
        ],
    ),
]


# ============================================================================
# Pipeline execution helper (extracted for testability via monkeypatch)
# ============================================================================


def _execute_pipeline(request: GeneratePopulationRequest) -> Any:
    """Build and execute a PopulationPipeline from the given request.

    Extracted as a top-level function so tests can monkeypatch it without
    patching deep into the population library.

    Args:
        request: Validated generation request with source selections and merge config.

    Returns:
        PipelineResult with table, step_log, and assumption_chain.

    Raises:
        PipelineConfigError: Invalid pipeline configuration.
        PipelineExecutionError: A pipeline step failed at runtime.
        DataSourceError: A data source loader encountered an error.
        HTTPException (422): Unknown provider or dataset_id.
    """
    from reformlab.population import (
        ConditionalSamplingMethod,
        IPFConstraint,
        IPFMergeMethod,
        MergeConfig,
        PopulationPipeline,
        SourceCache,
        UniformMergeMethod,
        get_ademe_loader,
        get_eurostat_loader,
        get_insee_loader,
        get_sdes_loader,
        make_ademe_config,
        make_eurostat_config,
        make_insee_config,
        make_sdes_config,
    )

    cache = SourceCache()
    pipeline = PopulationPipeline(description="User-generated population via Data Fusion Workbench")

    # --- Add source loading steps ---
    loader_factories = {
        "insee": (get_insee_loader, make_insee_config),
        "eurostat": (get_eurostat_loader, make_eurostat_config),
        "ademe": (get_ademe_loader, make_ademe_config),
        "sdes": (get_sdes_loader, make_sdes_config),
    }

    for i, src in enumerate(request.sources):
        provider = src.provider
        dataset_id = src.dataset_id
        label = f"source_{i}"

        if provider not in loader_factories:
            raise HTTPException(
                status_code=422,
                detail=_problem_detail(
                    "Unknown data provider",
                    f"Provider {provider!r} is not registered",
                    f"Use one of: {sorted(_VALID_PROVIDERS)}",
                ),
            )

        catalog = _get_catalog_for_provider(provider)
        if catalog is None or dataset_id not in catalog:
            raise HTTPException(
                status_code=422,
                detail=_problem_detail(
                    "Unknown data source dataset",
                    f"Dataset {dataset_id!r} is not available for provider {provider!r}",
                    "Choose a dataset returned by the data source listing endpoint",
                ),
            )

        get_loader_fn, make_config_fn = loader_factories[provider]
        loader = get_loader_fn(dataset_id, cache=cache)
        config = make_config_fn(dataset_id)

        pipeline.add_source(label, loader=loader, config=config)

    # --- Add merge step (chain left-to-right for 2+ sources) ---
    merge_config = MergeConfig(seed=request.seed)

    if request.merge_method == "uniform":
        method: Any = UniformMergeMethod()
    elif request.merge_method == "ipf":
        constraints = tuple(
            IPFConstraint(dimension=c.dimension, targets=c.targets) for c in request.ipf_constraints
        )
        method = IPFMergeMethod(constraints=constraints)
    elif request.merge_method == "conditional":
        method = ConditionalSamplingMethod(strata_columns=tuple(request.strata_columns))
    else:
        raise HTTPException(
            status_code=422,
            detail=_problem_detail(
                "Unknown merge method",
                f"Merge method {request.merge_method!r} is not supported",
                f"Use one of: {sorted(_VALID_MERGE_METHODS)}",
            ),
        )

    # Chain merges: source_0 + source_1 → merged_0, merged_0 + source_2 → merged_1, …
    left_label = "source_0"
    for i in range(1, len(request.sources)):
        right_label = f"source_{i}"
        merge_label = f"merged_{i - 1}"
        pipeline.add_merge(
            merge_label,
            left=left_label,
            right=right_label,
            method=method,
            config=merge_config,
        )
        left_label = merge_label

    return pipeline.execute()


# ============================================================================
# Routes
# ============================================================================


@router.get("/sources")
async def list_sources() -> dict[str, dict[str, list[DataSourceItem]]]:
    """List all available data sources grouped by provider.

    AC-1: Returns datasets from INSEE, Eurostat, ADEME, and SDES with
    metadata (name, description, variable count, source URL).
    """
    from reformlab.population import (
        ADEME_CATALOG,
        EUROSTAT_CATALOG,
        INSEE_CATALOG,
        SDES_CATALOG,
    )

    provider_catalogs: dict[str, dict[str, Any]] = {
        "insee": INSEE_CATALOG,
        "eurostat": EUROSTAT_CATALOG,
        "ademe": ADEME_CATALOG,
        "sdes": SDES_CATALOG,
    }

    result: dict[str, list[DataSourceItem]] = {}
    for provider, catalog in provider_catalogs.items():
        items: list[DataSourceItem] = []
        for dataset_id, dataset in catalog.items():
            try:
                items.append(_build_source_item(provider, dataset_id, dataset))
            except (AttributeError, KeyError) as exc:
                logger.error(
                    "event=catalog_item_malformed provider=%s dataset_id=%s error=%s",
                    provider,
                    dataset_id,
                    exc,
                )
        result[provider] = items

    return {"sources": result}


@router.get("/sources/{provider}/{dataset_id}", response_model=DataSourceDetail)
async def get_source_detail(provider: str, dataset_id: str) -> DataSourceDetail:
    """Return dataset detail including column schema.

    AC-1/AC-2: Column names, types, and descriptions for a specific dataset.
    """
    if provider not in _VALID_PROVIDERS:
        raise HTTPException(
            status_code=404,
            detail=_problem_detail(
                "Unknown data provider",
                f"Provider {provider!r} is not registered",
                f"Use one of: {sorted(_VALID_PROVIDERS)}",
            ),
        )

    catalog = _get_catalog_for_provider(provider)
    if catalog is None or dataset_id not in catalog:
        raise HTTPException(
            status_code=404,
            detail=_problem_detail(
                "Data source dataset not found",
                f"Dataset {dataset_id!r} was not found for provider {provider!r}",
                "Choose a dataset returned by the data source listing endpoint",
            ),
        )

    dataset = catalog[dataset_id]
    return _build_source_detail(provider, dataset_id, dataset)


def _load_data_source_table(provider: str, dataset_id: str) -> Any:
    """Load a data source as a PyArrow table via the loader infrastructure."""
    from reformlab.population import (
        SourceCache,
        get_ademe_loader,
        get_eurostat_loader,
        get_insee_loader,
        get_sdes_loader,
        make_ademe_config,
        make_eurostat_config,
        make_insee_config,
        make_sdes_config,
    )

    loader_factories: dict[str, tuple[Any, Any]] = {
        "insee": (get_insee_loader, make_insee_config),
        "eurostat": (get_eurostat_loader, make_eurostat_config),
        "ademe": (get_ademe_loader, make_ademe_config),
        "sdes": (get_sdes_loader, make_sdes_config),
    }

    if provider not in loader_factories:
        raise HTTPException(
            status_code=404,
            detail=_problem_detail(
                "Unknown data provider",
                f"Provider {provider!r} is not registered",
                f"Use one of: {sorted(_VALID_PROVIDERS)}",
            ),
        )

    catalog = _get_catalog_for_provider(provider)
    if catalog is None or dataset_id not in catalog:
        raise HTTPException(
            status_code=404,
            detail=_problem_detail(
                "Data source dataset not found",
                f"Dataset {dataset_id!r} was not found for provider {provider!r}",
                "Choose a dataset returned by the data source listing endpoint",
            ),
        )

    cache = SourceCache()
    get_loader_fn, make_config_fn = loader_factories[provider]
    loader = get_loader_fn(dataset_id, cache=cache)
    config = make_config_fn(dataset_id)
    pop_data, _manifest = loader.download(config)
    return pop_data.primary_table


@router.get(
    "/sources/{provider}/{dataset_id}/preview",
    response_model=PopulationPreviewResponse,
)
async def preview_data_source(
    provider: str,
    dataset_id: str,
    offset: int = 0,
    limit: int = 100,
    sort_by: str | None = None,
    order: str = "asc",
) -> PopulationPreviewResponse:
    """Get a paginated preview of data source rows."""
    import pyarrow as pa

    limit = min(limit, 100)

    try:
        table = _load_data_source_table(provider, dataset_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to load data source %s/%s", provider, dataset_id)
        raise HTTPException(
            status_code=500,
            detail={
                "what": f"Failed to load data source {provider}/{dataset_id}",
                "why": str(exc),
                "fix": "Ensure the data has been cached or check network connectivity",
            },
        )

    if sort_by and sort_by in table.column_names:
        sort_order = "ascending" if order == "asc" else "descending"
        table = table.sort_by([(sort_by, sort_order)])

    total_rows = table.num_rows
    end_idx = min(offset + limit, total_rows)
    sliced = table.slice(offset, end_idx - offset)
    rows = sliced.to_pylist()

    columns = []
    for i, name in enumerate(sliced.column_names):
        arrow_type = sliced.schema[i].type
        if pa.types.is_integer(arrow_type):
            type_str = "integer"
        elif pa.types.is_floating(arrow_type):
            type_str = "float"
        elif pa.types.is_boolean(arrow_type):
            type_str = "boolean"
        else:
            type_str = "string"
        columns.append(PopulationPreviewColumnInfo(name=name, type=type_str, description=""))

    source_name = dataset_id.replace("_", " ").title()
    return PopulationPreviewResponse(
        id=f"{provider}/{dataset_id}",
        name=source_name,
        rows=rows,
        columns=columns,
        total_rows=total_rows,
    )


@router.get(
    "/sources/{provider}/{dataset_id}/profile",
    response_model=PopulationProfileResponse,
)
async def profile_data_source(provider: str, dataset_id: str) -> PopulationProfileResponse:
    """Get per-column profile statistics for a data source."""
    import pyarrow as pa

    from reformlab.server.models import ColumnProfile, ColumnProfileEntry
    from reformlab.server.routes.populations import (
        _compute_boolean_profile,
        _compute_categorical_profile,
        _compute_numeric_profile,
    )

    try:
        table = _load_data_source_table(provider, dataset_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to load data source %s/%s for profiling", provider, dataset_id)
        raise HTTPException(
            status_code=500,
            detail={
                "what": f"Failed to profile data source {provider}/{dataset_id}",
                "why": str(exc),
                "fix": "Ensure the data has been cached or check network connectivity",
            },
        )

    columns = []
    for col_name in table.column_names:
        arrow_type = table.column(col_name).type
        profile: ColumnProfile
        if pa.types.is_integer(arrow_type) or pa.types.is_floating(arrow_type):
            profile = _compute_numeric_profile(table, col_name)
        elif pa.types.is_boolean(arrow_type):
            profile = _compute_boolean_profile(table, col_name)
        else:
            profile = _compute_categorical_profile(table, col_name)
        columns.append(ColumnProfileEntry(name=col_name, profile=profile))

    return PopulationProfileResponse(
        id=f"{provider}/{dataset_id}",
        columns=columns,
    )


@router.get("/merge-methods")
async def list_merge_methods() -> dict[str, list[MergeMethodInfo]]:
    """Return available merge methods with plain-language descriptions.

    AC-3: Each method includes assumption statements, trade-off descriptions,
    and configurable parameter specifications.
    """
    return {"methods": _MERGE_METHODS}


@router.post("/generate", response_model=GeneratePopulationResponse)
async def generate_population(request: GeneratePopulationRequest) -> GeneratePopulationResponse:
    """Execute the population generation pipeline and return results.

    AC-4/AC-5: Runs synchronously. Returns step log, assumption chain,
    population summary, and validation results on success; structured
    error (what/why/fix) on failure.

    AC-6: Same seed + configuration → bit-for-bit identical results.
    """
    from reformlab.population import (
        DataSourceError,
        PipelineConfigError,
        PipelineError,
    )

    # Validate at least 2 sources for a merge
    if len(request.sources) < 2:
        raise HTTPException(
            status_code=422,
            detail=_problem_detail(
                "Not enough data sources",
                "Population generation requires at least two sources to merge",
                "Select at least two data sources before generating a population",
            ),
        )

    # Validate provider names upfront
    for src in request.sources:
        if src.provider not in _VALID_PROVIDERS:
            raise HTTPException(
                status_code=422,
                detail=_problem_detail(
                    "Unknown data provider",
                    f"Provider {src.provider!r} is not registered",
                    f"Use one of: {sorted(_VALID_PROVIDERS)}",
                ),
            )

    # Validate merge method upfront
    if request.merge_method not in _VALID_MERGE_METHODS:
        raise HTTPException(
            status_code=422,
            detail=_problem_detail(
                "Unknown merge method",
                f"Merge method {request.merge_method!r} is not supported",
                f"Use one of: {sorted(_VALID_MERGE_METHODS)}",
            ),
        )

    try:
        result = _execute_pipeline(request)
    except HTTPException:
        raise
    except PipelineConfigError as exc:
        logger.error("Pipeline config error: %s", exc)
        raise HTTPException(
            status_code=422,
            detail=_problem_detail(exc.summary, exc.reason, exc.fix),
        ) from exc
    except PipelineError as exc:
        logger.error("Pipeline execution error: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=_problem_detail(exc.summary, exc.reason, exc.fix),
        ) from exc
    except DataSourceError as exc:
        logger.error("Data source error: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=_problem_detail(
                str(exc),
                "The data source could not be loaded (network or cache issue)",
                "Ensure the data has been cached or check network connectivity",
            ),
        ) from exc

    # Serialize step log
    step_log = [
        StepLogItem(
            step_index=entry.step_index,
            step_type=entry.step_type,
            label=entry.label,
            input_labels=list(entry.input_labels),
            output_rows=entry.output_rows,
            output_columns=list(entry.output_columns),
            method_name=entry.method_name,
            duration_ms=entry.duration_ms,
        )
        for entry in result.step_log
    ]

    # Serialize assumption chain
    assumption_chain = [
        AssumptionRecordItem(
            step_index=record.step_index,
            step_label=record.step_label,
            method=getattr(record.assumption, "method", "unknown"),
            description=getattr(record.assumption, "description", ""),
        )
        for record in result.assumption_chain.records
    ]

    # Build population summary from the result table
    table = result.table
    summary = PopulationSummary(
        record_count=table.num_rows,
        column_count=table.num_columns,
        columns=list(table.column_names),
    )

    logger.info(
        "event=population_generated method=%s sources=%d rows=%d columns=%d",
        request.merge_method,
        len(request.sources),
        table.num_rows,
        table.num_columns,
    )

    # Run population validation if IPF constraints were provided
    validation_result_response: ValidationResultResponse | None = None
    if request.ipf_constraints:
        try:
            from reformlab.population.validation import (
                MarginalConstraint,
                PopulationValidator,
            )

            constraints = [
                MarginalConstraint(
                    dimension=c.dimension,
                    distribution=c.targets,
                    tolerance=0.05,
                )
                for c in request.ipf_constraints
            ]
            validator = PopulationValidator(constraints)
            validation = validator.validate(table)
            validation_result_response = ValidationResultResponse(
                all_passed=validation.all_passed,
                total_constraints=validation.total_constraints,
                failed_count=validation.failed_count,
                marginal_results=[
                    MarginalResultItem(
                        dimension=mr.constraint.dimension,
                        passed=mr.passed,
                        max_deviation=mr.max_deviation,
                        tolerance=mr.constraint.tolerance,
                        observed=dict(mr.observed),
                        expected=dict(mr.constraint.distribution),
                        deviations=dict(mr.deviations),
                    )
                    for mr in validation.marginal_results
                ],
            )
        except (KeyError, ValueError) as exc:
            logger.warning("event=validation_skipped reason=%s", str(exc))

    return GeneratePopulationResponse(
        success=True,
        summary=summary,
        step_log=step_log,
        assumption_chain=assumption_chain,
        validation_result=validation_result_response,
    )
