# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Pydantic v2 request/response models for the ReformLab API.

All HTTP serialization models live here. Domain layer uses frozen dataclasses;
the server layer creates parallel Pydantic models for wire format translation.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, computed_field

# Story 21.2 / AC7: Import canonical evidence literal types from reformlab.data
from reformlab.data import (  # type: ignore[attr-defined]
    DataAssetAccessMode,
    DataAssetOrigin,
    DataAssetTrustStatus,
)

# Story 24.1 / AC-1: Runtime availability literal type
RuntimeAvailability = Literal["live_ready", "live_unavailable"]

# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    password: str


class RunRequest(BaseModel):
    template_name: str | None = None
    policy: dict[str, Any] = {}
    start_year: int = 2025
    end_year: int = 2030
    population_id: str | None = None
    seed: int | None = None
    baseline_id: str | None = None
    portfolio_name: str | None = None  # set for portfolio runs
    policy_type: str | None = None  # for metadata recording
    exogenous_series: list[str] | None = None  # Story 21.6 / AC2: exogenous series names for scenario
    # Story 23.1 / AC-1, AC-2: Runtime mode with live default
    runtime_mode: Literal["live", "replay"] = "live"


class MemoryCheckRequest(BaseModel):
    template_name: str
    policy: dict[str, Any] = {}
    start_year: int
    end_year: int
    population_id: str | None = None


class IndicatorRequest(BaseModel):
    run_id: str
    income_field: str = "income"
    by_year: bool = False


class ComparisonRequest(BaseModel):
    baseline_run_id: str
    reform_run_id: str
    welfare_field: str = "disposable_income"
    threshold: float = 0.0


class ExportRequest(BaseModel):
    run_id: str


class CreateScenarioRequest(BaseModel):
    name: str
    policy_type: str | None = None  # carbon_tax | subsidy | rebate | feebate
    policy: dict[str, Any]
    start_year: int
    end_year: int
    description: str = ""
    baseline_ref: str | None = None


class CloneRequest(BaseModel):
    new_name: str


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class LoginResponse(BaseModel):
    token: str


class RunResponse(BaseModel):
    run_id: str
    success: bool
    scenario_id: str
    years: list[int]
    row_count: int
    manifest_id: str
    # Story 21.8 / AC7: Trust warnings for exploratory data usage
    trust_warnings: list[str] = []
    # Story 23.1 / AC-4: Runtime mode of the executed run
    runtime_mode: Literal["live", "replay"] = "live"
    # Story 23.2 / AC-5: Population source classification from resolver
    population_source: Literal["bundled", "uploaded", "generated"] | None = None


class MemoryCheckResponse(BaseModel):
    should_warn: bool
    estimated_gb: float
    available_gb: float
    message: str


class IndicatorResponse(BaseModel):
    indicator_type: str
    data: dict[str, list[Any]]
    metadata: dict[str, Any]
    warnings: list[str]
    excluded_count: int


class ScenarioResponse(BaseModel):
    name: str
    policy_type: str
    description: str
    version: str
    policy: dict[str, Any]
    year_schedule: dict[str, int]
    baseline_ref: str | None = None


class TemplateListItem(BaseModel):
    id: str
    name: str
    type: str
    parameter_count: int
    description: str
    parameter_groups: list[str]
    is_custom: bool = False
    # Story 24.1 / AC-1: Runtime availability metadata
    runtime_availability: RuntimeAvailability = "live_unavailable"
    availability_reason: str | None = None


class TemplateDetailResponse(TemplateListItem):
    default_policy: dict[str, Any]


class CustomTemplateParameterSpec(BaseModel):
    """Specification for a single parameter of a custom template."""

    name: str
    type: str = "float"  # float | int | str
    default: float | int | str | None = None
    unit: str = ""
    min: float | None = None
    max: float | None = None


class CreateCustomTemplateRequest(BaseModel):
    """Request body for POST /api/templates/custom."""

    name: str
    description: str = ""
    parameters: list[CustomTemplateParameterSpec]


class CustomTemplateResponse(BaseModel):
    """Response for custom template creation."""

    name: str
    description: str
    parameter_count: int
    is_custom: bool = True
    # Story 24.1 / AC-1: Runtime availability metadata for custom templates
    runtime_availability: RuntimeAvailability = "live_unavailable"
    availability_reason: str | None = None


class PopulationItem(BaseModel):
    id: str
    name: str
    households: int
    source: str
    year: int


class ErrorResponse(BaseModel):
    error: str
    what: str
    why: str
    fix: str
    status_code: int


# ---------------------------------------------------------------------------
# Data fusion models — Story 17.1
# ---------------------------------------------------------------------------


class DataFusionSourceSelection(BaseModel):
    """A single data source selection for a fusion request."""

    provider: str  # "insee" | "eurostat" | "ademe" | "sdes"
    dataset_id: str


class IPFConstraintRequest(BaseModel):
    """An IPF marginal constraint specification."""

    dimension: str
    targets: dict[str, float]


class GeneratePopulationRequest(BaseModel):
    """Request body for POST /api/data-fusion/generate."""

    sources: list[DataFusionSourceSelection]
    merge_method: str = "uniform"  # "uniform" | "ipf" | "conditional"
    seed: int = 42
    ipf_constraints: list[IPFConstraintRequest] = []
    strata_columns: list[str] = []


class ColumnInfo(BaseModel):
    """Column metadata for a data source."""

    name: str
    type: str = ""
    description: str


class DataSourceItem(BaseModel):
    """Metadata for a single data source dataset.

    Story 21.2 / AC5: Includes evidence classification fields for data fusion sources.
    """

    id: str
    provider: str
    name: str
    description: str
    variable_count: int
    record_count: int | None = None
    source_url: str
    # Story 21.2 / AC5, AC7: Evidence classification fields using canonical Literal types
    # Story 21.2 code review fix: Removed defaults for Literal types - must be explicit
    origin: DataAssetOrigin  # All current providers are open-official
    access_mode: DataAssetAccessMode  # All current providers are fetched
    trust_status: DataAssetTrustStatus  # Official sources are production-safe
    data_class: Literal["structural"] = "structural"  # All fusion sources are structural in current phase


class DataSourceDetail(DataSourceItem):
    """Extended dataset metadata including column schema."""

    columns: list[ColumnInfo]


class MergeMethodParamSpec(BaseModel):
    """Parameter specification for a merge method."""

    name: str
    type: str
    description: str
    required: bool = False


class MergeMethodInfo(BaseModel):
    """Merge method metadata with plain-language descriptions."""

    id: str
    name: str
    what_it_does: str
    assumption: str
    when_appropriate: str
    tradeoff: str
    parameters: list[MergeMethodParamSpec]


class StepLogItem(BaseModel):
    """Log entry for one pipeline step."""

    step_index: int
    step_type: str
    label: str
    input_labels: list[str]
    output_rows: int
    output_columns: list[str]
    method_name: str | None = None
    duration_ms: float


class AssumptionRecordItem(BaseModel):
    """A single assumption from the pipeline assumption chain."""

    step_index: int
    step_label: str
    method: str
    description: str


class MarginalResultItem(BaseModel):
    """Validation result for a single marginal constraint."""

    dimension: str
    passed: bool
    max_deviation: float
    tolerance: float
    observed: dict[str, float]
    expected: dict[str, float]
    deviations: dict[str, float]


class ValidationResultResponse(BaseModel):
    """Overall population validation result."""

    all_passed: bool
    total_constraints: int
    failed_count: int
    marginal_results: list[MarginalResultItem]


class PopulationSummary(BaseModel):
    """Summary statistics for a generated population."""

    record_count: int
    column_count: int
    columns: list[str]


class GeneratePopulationResponse(BaseModel):
    """Response for POST /api/data-fusion/generate."""

    success: bool
    summary: PopulationSummary
    step_log: list[StepLogItem]
    assumption_chain: list[AssumptionRecordItem]
    validation_result: ValidationResultResponse | None = None


# ---------------------------------------------------------------------------
# Portfolio models — Story 17.2
# ---------------------------------------------------------------------------


class PortfolioPolicyRequest(BaseModel):
    """A single policy entry in a portfolio create/update request."""

    model_config = {"from_attributes": True}
    name: str
    policy_type: str
    rate_schedule: dict[str, float] = {}
    exemptions: list[str] = []
    thresholds: list[float] = []
    covered_categories: list[str] = []
    extra_params: dict[str, Any] = {}


class CreatePortfolioRequest(BaseModel):
    model_config = {"from_attributes": True}
    name: str
    description: str = ""
    policies: list[PortfolioPolicyRequest]
    resolution_strategy: str = "error"


class UpdatePortfolioRequest(BaseModel):
    model_config = {"from_attributes": True}
    description: str | None = None
    policies: list[PortfolioPolicyRequest]
    resolution_strategy: str | None = None


class ClonePortfolioRequest(BaseModel):
    model_config = {"from_attributes": True}
    new_name: str


class PortfolioConflict(BaseModel):
    model_config = {"from_attributes": True}
    conflict_type: str
    policy_indices: list[int]
    parameter_name: str
    description: str


class ValidatePortfolioRequest(BaseModel):
    model_config = {"from_attributes": True}
    policies: list[PortfolioPolicyRequest]
    resolution_strategy: str = "error"


class ValidatePortfolioResponse(BaseModel):
    model_config = {"from_attributes": True}
    conflicts: list[PortfolioConflict]
    is_compatible: bool


class PortfolioPolicyItem(BaseModel):
    model_config = {"from_attributes": True}
    name: str
    policy_type: str
    rate_schedule: dict[str, float]
    parameters: dict[str, Any]


class PortfolioDetailResponse(BaseModel):
    model_config = {"from_attributes": True}
    name: str
    description: str
    version_id: str
    policies: list[PortfolioPolicyItem]
    resolution_strategy: str
    policy_count: int


class PortfolioListItem(BaseModel):
    model_config = {"from_attributes": True}
    name: str
    description: str
    version_id: str
    policy_count: int


# ---------------------------------------------------------------------------
# Result models — Story 17.3
# ---------------------------------------------------------------------------


class ResultListItem(BaseModel):
    """Summary of a saved simulation result."""

    model_config = {"from_attributes": True}
    run_id: str
    timestamp: str
    run_kind: str  # "scenario" | "portfolio"
    start_year: int
    end_year: int
    row_count: int
    status: str
    data_available: bool  # True if SimulationResult is in cache
    template_name: str | None = None  # scenario runs only
    policy_type: str | None = None  # scenario runs only
    portfolio_name: str | None = None  # portfolio runs only


class ResultDetailResponse(BaseModel):
    """Full detail for a single simulation result."""

    model_config = {"from_attributes": True}
    run_id: str
    timestamp: str
    run_kind: str
    start_year: int
    end_year: int
    population_id: str | None
    seed: int | None
    row_count: int
    manifest_id: str
    scenario_id: str
    adapter_version: str
    started_at: str
    finished_at: str
    status: str
    data_available: bool
    template_name: str | None = None
    policy_type: str | None = None
    portfolio_name: str | None = None
    # Story 21.6 / AC6: Exogenous series fields for comparison dimension
    exogenous_series_hash: str | None = None
    exogenous_series_names: list[str] | None = None
    # Story 21.8 / AC4: Evidence assets from manifest (populated from RunManifest)
    evidence_assets: list[dict[str, Any]] | None = None
    # Story 23.1 / AC-4: Runtime mode from manifest
    runtime_mode: Literal["live", "replay"] = "live"
    # Story 23.2 / AC-5: Population source classification from resolver
    population_source: Literal["bundled", "uploaded", "generated"] | None = None
    # Populated only when data_available is True:
    indicators: dict[str, Any] | None = None
    columns: list[str] | None = None
    column_count: int | None = None


# ---------------------------------------------------------------------------
# Portfolio comparison models — Story 17.4
# ---------------------------------------------------------------------------


class PortfolioComparisonRequest(BaseModel):
    """Request for multi-run portfolio comparison."""

    run_ids: list[str]  # 2-5 run IDs; duplicates rejected
    baseline_run_id: str | None = None  # defaults to first run_id
    indicator_types: list[str] = Field(
        default_factory=lambda: ["distributional", "fiscal"]
    )
    include_welfare: bool = True
    include_deltas: bool = True
    include_pct_deltas: bool = True


class ComparisonData(BaseModel):
    """Comparison result for a single indicator type."""

    columns: list[str]
    data: dict[str, list[Any]]


class CrossMetricItem(BaseModel):
    """Single cross-comparison metric ranking portfolios."""

    criterion: str
    best_portfolio: str
    value: float
    all_values: dict[str, float]


class PortfolioComparisonResponse(BaseModel):
    """Response for multi-run portfolio comparison."""

    comparisons: dict[str, ComparisonData]  # keyed by indicator type
    cross_metrics: list[CrossMetricItem]
    portfolio_labels: list[str]
    metadata: dict[str, Any]
    warnings: list[str]


# ---------------------------------------------------------------------------
# Decision viewer models — Story 17.5
# ---------------------------------------------------------------------------


class DecisionSummaryRequest(BaseModel):
    """Request for decision outcome summary."""

    run_id: str
    domain_name: str | None = None  # None = all domains
    group_by: str | None = None  # "decile" or None
    group_value: str | None = None  # e.g., "3" for D3; None = all
    year: int | None = None  # If set, include mean probabilities in response


class YearlyOutcome(BaseModel):
    """Decision outcomes for a single year."""

    year: int
    total_households: int
    counts: dict[str, int]  # alternative_id → count
    percentages: dict[str, float]  # alternative_id → percentage (0–100)
    mean_probabilities: dict[str, float] | None = None  # only when year detail requested


class DomainSummary(BaseModel):
    """Summary of decision outcomes for a single domain across years."""

    domain_name: str
    alternative_ids: list[str]
    alternative_labels: dict[str, str]
    yearly_outcomes: list[YearlyOutcome]
    eligibility: dict[str, int] | None = None  # keys: n_total, n_eligible, n_ineligible


class DecisionSummaryResponse(BaseModel):
    """Response for decision outcome summary."""

    run_id: str
    domains: list[DomainSummary]
    metadata: dict[str, Any]
    warnings: list[str]


# ---------------------------------------------------------------------------
# Population explorer models — Story 20.7
# ---------------------------------------------------------------------------


class PopulationLibraryItem(BaseModel):
    """Extended population item with dual-field evidence classification.

    Story 21.2 / AC1: Preserves legacy origin for UI behavior compatibility
    while adding canonical evidence governance from Story 21.1.

    Dual-field design:
    - Legacy origin field: Preserved for edit/delete button visibility and backward compatibility
    - Canonical fields: Added for evidence governance (canonical_origin, access_mode, trust_status)

    Story 21.4 / AC5: Added is_synthetic boolean field for easier UI filtering.
    """

    id: str
    name: str
    households: int
    source: str
    year: int
    # Legacy field preserved for UI compatibility (edit/delete button logic)
    origin: Literal["built-in", "generated", "uploaded"]
    # Story 21.2 / AC1, AC7: New canonical fields for evidence governance
    canonical_origin: DataAssetOrigin  # "open-official" | "synthetic-public"
    access_mode: DataAssetAccessMode  # "bundled" | "fetched"
    trust_status: DataAssetTrustStatus  # "production-safe" | "exploratory" | ...
    column_count: int
    created_date: str | None = None  # ISO 8601 UTC for generated/uploaded, null for built-in

    @computed_field
    def is_synthetic(self) -> bool:
        """Story 21.4 / AC5: Computed field - True if canonical_origin is synthetic-public."""
        return bool(self.canonical_origin == "synthetic-public")


class PopulationPreviewColumnInfo(BaseModel):
    """Column metadata for population preview."""

    name: str
    type: str  # "integer" | "float" | "string" | "boolean"
    description: str


class PopulationPreviewResponse(BaseModel):
    """Paginated row preview with column metadata."""

    id: str
    name: str
    rows: list[dict[str, Any]]  # max 100 rows
    columns: list[PopulationPreviewColumnInfo]
    total_rows: int


class ColumnProfileNumeric(BaseModel):
    """Numeric column profile with statistics and histogram."""

    type: Literal["numeric"]
    count: int
    nulls: int
    null_pct: float
    min: float
    max: float
    mean: float
    median: float
    std: float
    percentiles: dict[str, float]  # p1, p5, p25, p50, p75, p95, p99
    histogram_buckets: list[dict[str, Any]]  # [{"bin_start": 0, "bin_end": 10, "count": 123}, ...]


class ColumnProfileCategorical(BaseModel):
    """Categorical column profile with value counts."""

    type: Literal["categorical"]
    count: int
    nulls: int
    null_pct: float
    cardinality: int
    value_counts: list[dict[str, Any]]  # [{"value": "x", "count": 123}, ...]


class ColumnProfileBoolean(BaseModel):
    """Boolean column profile with true/false counts."""

    type: Literal["boolean"]
    count: int
    nulls: int
    null_pct: float
    true_count: int
    false_count: int


ColumnProfile = ColumnProfileNumeric | ColumnProfileCategorical | ColumnProfileBoolean


class ColumnProfileEntry(BaseModel):
    """Single column profile entry."""

    name: str
    profile: ColumnProfile


class PopulationProfileResponse(BaseModel):
    """Per-column profile statistics for a population."""

    id: str
    columns: list[ColumnProfileEntry]


class PopulationCrosstabResponse(BaseModel):
    """Cross-tabulation of two columns."""

    col_a: str
    col_b: str
    data: list[dict[str, Any]]  # flattened crosstab with col_a, col_b, count columns
    truncated: bool = False  # true if results limited to top 1000 combinations


class PopulationUploadResponse(BaseModel):
    """Upload validation feedback."""

    id: str
    name: str
    row_count: int
    column_count: int
    matched_columns: list[str]
    unrecognized_columns: list[str]
    missing_required: list[str]
    valid: bool


# ---------------------------------------------------------------------------
# Population comparison models — Story 21.4
# ---------------------------------------------------------------------------


class NumericColumnComparison(BaseModel):
    """Comparison of a single numeric column between observed and synthetic populations.

    Story 21.4 / AC3, AC8.
    """

    column_name: str
    observed_mean: float
    synthetic_mean: float
    relative_diff_pct: float
    observed_median: float
    synthetic_median: float
    observed_std: float
    synthetic_std: float
    observed_p10: float
    synthetic_p10: float
    observed_p50: float
    synthetic_p50: float
    observed_p90: float
    synthetic_p90: float


class PopulationComparisonResponse(BaseModel):
    """Response for GET /api/populations/compare.

    Story 21.4 / AC4, AC8.
    """

    observed_asset_id: str
    synthetic_asset_id: str
    row_counts: dict[str, int]  # {"observed": N, "synthetic": M}
    column_counts: dict[str, int]
    common_numeric_columns: list[str]
    numeric_comparison: dict[str, NumericColumnComparison]
    trust_labels: dict[str, dict[str, str]]  # Per-asset governance fields


# ---------------------------------------------------------------------------
# Validation/preflight models — Story 20.7
# ---------------------------------------------------------------------------


class PreflightRequest(BaseModel):
    """Request for pre-execution validation."""

    scenario: dict[str, Any]  # WorkspaceScenario serialized as dict
    population_id: str | None = None
    template_name: str | None = None
    # Story 23.5 / AC-1, AC-4: Runtime mode for validation
    runtime_mode: Literal["live", "replay"] = "live"


class ValidationCheckResult(BaseModel):
    """Result of a single validation check."""

    id: str
    label: str
    passed: bool
    severity: Literal["error", "warning"]
    message: str


class PreflightResponse(BaseModel):
    """Response for pre-execution validation."""

    passed: bool
    checks: list[ValidationCheckResult]
    warnings: list[str]


# ---------------------------------------------------------------------------
# Exogenous asset models — Story 21.6
# ---------------------------------------------------------------------------


class ExogenousAssetRequest(BaseModel):
    """Request body for creating an exogenous time series asset.

    Story 21.6 / AC8.
    """

    name: str
    description: str
    origin: Literal["open-official", "open-third-party", "proprietary"]
    access_mode: Literal["bundled", "fetched", "uploaded"]
    trust_status: Literal["production-safe", "exploratory", "deprecated"]
    source_url: str = ""
    license: str = ""
    version: str = ""
    geographic_coverage: list[str] = []
    years: list[int] = []
    intended_use: str = ""
    redistribution_allowed: bool = True
    redistribution_notes: str = ""
    update_cadence: str = ""
    quality_notes: str = ""
    references: list[str] = []
    # Exogenous-specific fields
    unit: str
    values: dict[str, float]  # Year (string key) → value mapping
    frequency: str = "annual"
    source: str = ""
    vintage: str = ""
    interpolation_method: Literal["linear", "step", "none"] = "linear"
    aggregation_method: str = "mean"
    revision_policy: str = ""


class ExogenousAssetResponse(BaseModel):
    """Response for exogenous asset listing and retrieval.

    Story 21.6 / AC8.
    """

    # Descriptor fields
    asset_id: str
    name: str
    description: str
    data_class: Literal["exogenous"]
    origin: Literal["open-official", "open-third-party", "proprietary"]
    access_mode: Literal["bundled", "fetched", "uploaded"]
    trust_status: Literal["production-safe", "exploratory", "deprecated"]
    source_url: str
    license: str
    version: str
    geographic_coverage: list[str]
    years: list[int]
    intended_use: str
    redistribution_allowed: bool
    redistribution_notes: str
    update_cadence: str
    quality_notes: str
    references: list[str]
    # Exogenous-specific fields
    unit: str
    values: dict[int, float]  # Year → value mapping
    frequency: str
    source: str
    vintage: str
    interpolation_method: str
    aggregation_method: str
    revision_policy: str
