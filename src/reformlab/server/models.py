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
