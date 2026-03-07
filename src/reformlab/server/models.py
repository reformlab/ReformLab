"""Pydantic v2 request/response models for the ReformLab API.

All HTTP serialization models live here. Domain layer uses frozen dataclasses;
the server layer creates parallel Pydantic models for wire format translation.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    password: str


class RunRequest(BaseModel):
    template_name: str
    policy: dict[str, Any]
    start_year: int
    end_year: int
    population_id: str | None = None
    seed: int | None = None
    baseline_id: str | None = None


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
