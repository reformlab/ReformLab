"""Pydantic v2 request/response models for the ReformLab API.

All HTTP serialization models live here. Domain layer uses frozen dataclasses;
the server layer creates parallel Pydantic models for wire format translation.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

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


class TemplateDetailResponse(TemplateListItem):
    default_policy: dict[str, Any]


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
    """Metadata for a single data source dataset."""

    id: str
    provider: str
    name: str
    description: str
    variable_count: int
    record_count: int | None = None
    source_url: str


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
