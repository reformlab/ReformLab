// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** TypeScript interfaces matching the backend Pydantic response models. */

import type { ReactNode } from "react";

// ============================================================================
// Request types
// ============================================================================

export interface LoginRequest {
  password: string;
}

export interface RunRequest {
  template_name: string;
  policy: Record<string, unknown>;
  start_year: number;
  end_year: number;
  population_id?: string | null;
  seed?: number | null;
  baseline_id?: string | null;
}

export interface MemoryCheckRequest {
  template_name: string;
  policy?: Record<string, unknown>;
  start_year: number;
  end_year: number;
  population_id?: string | null;
}

export interface IndicatorRequest {
  run_id: string;
  income_field?: string;
  by_year?: boolean;
}

export interface ComparisonRequest {
  baseline_run_id: string;
  reform_run_id: string;
  welfare_field?: string;
  threshold?: number;
}

export interface ExportRequest {
  run_id: string;
}

export interface CreateScenarioRequest {
  name: string;
  policy_type: string;
  policy: Record<string, unknown>;
  start_year: number;
  end_year: number;
  description?: string;
  baseline_ref?: string | null;
}

export interface CloneRequest {
  new_name: string;
}

// ============================================================================
// Response types
// ============================================================================

export interface LoginResponse {
  token: string;
}

export interface RunResponse {
  run_id: string;
  success: boolean;
  scenario_id: string;
  years: number[];
  row_count: number;
  manifest_id: string;
}

export interface MemoryCheckResponse {
  should_warn: boolean;
  estimated_gb: number;
  available_gb: number;
  message: string;
}

export interface IndicatorResponse {
  indicator_type: string;
  data: Record<string, unknown[]>;
  metadata: Record<string, unknown>;
  warnings: string[];
  excluded_count: number;
}

export interface ScenarioResponse {
  name: string;
  policy_type: string;
  description: string;
  version: string;
  policy: Record<string, unknown>;
  year_schedule: Record<string, number>;
  baseline_ref?: string | null;
}

export interface TemplateListItem {
  id: string;
  name: string;
  type: string;
  parameter_count: number;
  description: string;
  parameter_groups: string[];
  is_custom: boolean;
}

export interface TemplateDetailResponse extends TemplateListItem {
  default_policy: Record<string, unknown>;
}

export interface CustomTemplateParameterSpec {
  name: string;
  type: string;
  default?: number | string | null;
  unit?: string;
  min?: number | null;
  max?: number | null;
}

export interface CreateCustomTemplateRequest {
  name: string;
  description?: string;
  parameters: CustomTemplateParameterSpec[];
}

export interface CustomTemplateResponse {
  name: string;
  description: string;
  parameter_count: number;
  is_custom: boolean;
}

export interface PopulationItem {
  id: string;
  name: string;
  households: number;
  source: string;
  year: number;
}

export interface ErrorResponse {
  error: string;
  what: string;
  why: string;
  fix: string;
  status_code: number;
}

export type IndicatorType = "distributional" | "geographic" | "welfare" | "fiscal";

// ============================================================================
// Data fusion types — Story 17.1
// ============================================================================

export interface DataSourceItem {
  id: string;
  provider: string;
  name: string;
  description: string;
  variable_count: number;
  record_count: number | null;
  source_url: string;
  // Story 21.2 / AC5, AC6: Evidence classification fields for data fusion sources
  origin: "open-official" | "synthetic-public";
  access_mode: "bundled" | "fetched";
  trust_status:
    | "production-safe"
    | "exploratory"
    | "demo-only"
    | "validation-pending"
    | "not-for-public-inference";
  data_class: "structural";
}

export interface ColumnInfo {
  name: string;
  type: string;
  description: string;
}

export interface DataSourceDetail extends DataSourceItem {
  columns: ColumnInfo[];
}

export interface VariableInfo {
  name: string;
  description: string;
  present_in: string[];
}

export interface MergeMethodParam {
  name: string;
  type: string;
  description: string;
  required: boolean;
}

export interface MergeMethodInfo {
  id: string;
  name: string;
  what_it_does: string;
  assumption: string;
  when_appropriate: string;
  tradeoff: string;
  parameters: MergeMethodParam[];
}

export interface IPFConstraintRequest {
  dimension: string;
  targets: Record<string, number>;
}

export interface GenerationRequest {
  sources: Array<{ provider: string; dataset_id: string }>;
  merge_method: string;
  seed: number;
  ipf_constraints?: IPFConstraintRequest[];
  strata_columns?: string[];
}

export interface StepLogItem {
  step_index: number;
  step_type: string;
  label: string;
  input_labels: string[];
  output_rows: number;
  output_columns: string[];
  method_name: string | null;
  duration_ms: number;
}

export interface AssumptionRecordItem {
  step_index: number;
  step_label: string;
  method: string;
  description: string;
}

export interface MarginalResultResponse {
  dimension: string;
  passed: boolean;
  max_deviation: number;
  tolerance: number;
  observed: Record<string, number>;
  expected: Record<string, number>;
  deviations: Record<string, number>;
}

export interface ValidationResultResponse {
  all_passed: boolean;
  total_constraints: number;
  failed_count: number;
  marginal_results: MarginalResultResponse[];
}

export interface PopulationSummary {
  record_count: number;
  column_count: number;
  columns: string[];
}

export interface GenerationResult {
  success: boolean;
  summary: PopulationSummary;
  step_log: StepLogItem[];
  assumption_chain: AssumptionRecordItem[];
  validation_result: ValidationResultResponse | null;
}

// ============================================================================
// Portfolio types — Story 17.2
// ============================================================================

export interface PortfolioPolicyRequest {
  name: string;
  policy_type: string;
  rate_schedule: Record<string, number>;
  exemptions: string[];
  thresholds: number[];
  covered_categories: string[];
  extra_params: Record<string, unknown>;
}

export interface CreatePortfolioRequest {
  name: string;
  description?: string;
  policies: PortfolioPolicyRequest[];
  resolution_strategy?: string;
}

export interface UpdatePortfolioRequest {
  description?: string;
  policies: PortfolioPolicyRequest[];
  resolution_strategy?: string;
}

export interface ClonePortfolioRequest {
  new_name: string;
}

export interface PortfolioConflict {
  conflict_type: string;
  policy_indices: number[];
  parameter_name: string;
  description: string;
}

export interface ValidatePortfolioRequest {
  policies: PortfolioPolicyRequest[];
  resolution_strategy?: string;
}

export interface ValidatePortfolioResponse {
  conflicts: PortfolioConflict[];
  is_compatible: boolean;
}

export interface PortfolioPolicyItem {
  name: string;
  policy_type: string;
  rate_schedule: Record<string, number>;
  parameters: Record<string, unknown>;
}

export interface PortfolioDetailResponse {
  name: string;
  description: string;
  version_id: string;
  policies: PortfolioPolicyItem[];
  resolution_strategy: string;
  policy_count: number;
}

export interface PortfolioListItem {
  name: string;
  description: string;
  version_id: string;
  policy_count: number;
}

// ============================================================================
// Result types — Story 17.3
// ============================================================================

export interface ResultListItem {
  run_id: string;
  timestamp: string;
  run_kind: string;              // "scenario" | "portfolio"
  start_year: number;
  end_year: number;
  row_count: number;
  status: string;
  data_available: boolean;
  template_name: string | null;  // scenario runs only
  policy_type: string | null;    // scenario runs only
  portfolio_name: string | null; // portfolio runs only
}

export interface ResultDetailResponse extends ResultListItem {
  population_id: string | null;
  seed: number | null;
  manifest_id: string;
  scenario_id: string;
  adapter_version: string;
  started_at: string;
  finished_at: string;
  indicators: Record<string, unknown> | null;
  columns: string[] | null;
  column_count: number | null;
}

// ============================================================================
// Multi-run comparison types — Story 17.4
// ============================================================================

export interface PortfolioComparisonRequest {
  run_ids: string[];
  baseline_run_id?: string | null;
  indicator_types?: string[];
  include_welfare?: boolean;
  include_deltas?: boolean;
  include_pct_deltas?: boolean;
}

export interface ComparisonData {
  columns: string[];
  data: Record<string, unknown[]>;
}

export interface CrossMetricItem {
  criterion: string;
  best_portfolio: string;
  value: number;
  all_values: Record<string, number>;
}

export interface PortfolioComparisonResponse {
  comparisons: Record<string, ComparisonData>;
  cross_metrics: CrossMetricItem[];
  portfolio_labels: string[];
  metadata: Record<string, unknown>;
  warnings: string[];
}


// ============================================================================
// Population explorer types — Story 20.4
// ============================================================================

export interface PopulationPreviewResponse {
  id: string;
  name: string;
  rows: Record<string, unknown>[];
  columns: ColumnInfo[];
  total_rows: number;
}

export interface ColumnProfileNumeric {
  type: "numeric";
  count: number;
  nulls: number;
  null_pct: number;
  min: number;
  max: number;
  mean: number;
  median: number;
  std: number;
  percentiles: Record<string, number>;
  histogram_buckets: Array<{ bin_start: number; bin_end: number; count: number }>;
}

export interface ColumnProfileCategorical {
  type: "categorical";
  count: number;
  nulls: number;
  null_pct: number;
  cardinality: number;
  value_counts: Array<{ value: string; count: number }>;
}

export interface ColumnProfileBoolean {
  type: "boolean";
  count: number;
  nulls: number;
  null_pct: number;
  true_count: number;
  false_count: number;
}

export type ColumnProfile = ColumnProfileNumeric | ColumnProfileCategorical | ColumnProfileBoolean;

export interface PopulationProfileResponse {
  id: string;
  columns: Array<{ name: string; profile: ColumnProfile }>;
}

export interface PopulationCrosstabResponse {
  col_a: string;
  col_b: string;
  data: Array<Record<string, unknown>>;
  truncated: boolean;
}

export interface PopulationUploadResponse {
  id: string;
  name: string;
  row_count: number;
  column_count: number;
  matched_columns: string[];
  unrecognized_columns: string[];
  missing_required: string[];
  valid: boolean;
}

export interface PopulationLibraryItem extends PopulationItem {
  // Legacy field preserved for UI behavior (edit/delete button visibility)
  origin: "built-in" | "generated" | "uploaded";
  // Story 21.2 / AC1, AC2: New canonical fields for evidence governance
  canonical_origin: "open-official" | "synthetic-public";
  access_mode: "bundled" | "fetched";
  trust_status:
    | "production-safe"
    | "exploratory"
    | "demo-only"
    | "validation-pending"
    | "not-for-public-inference";
  column_count: number;
  created_date: string | null;
  // Story 21.4 / AC5: Computed field for easier UI filtering
  is_synthetic: boolean;
}

export interface PopulationSummaryData {
  record_count: number;
  column_count: number;
  estimated_memory_mb: number;
  columns: Array<{
    name: string;
    type: "numeric" | "categorical" | "boolean" | "string";
    null_pct: number;
    cardinality: number | null;
  }>;
}

// ============================================================================
// Decision viewer types — Story 17.5
// ============================================================================

export interface DecisionSummaryRequest {
  run_id: string;
  domain_name?: string | null;
  group_by?: string | null;
  group_value?: string | null;
  year?: number | null;
}

export interface YearlyOutcome {
  year: number;
  total_households: number;
  counts: Record<string, number>;
  percentages: Record<string, number>;
  mean_probabilities: Record<string, number> | null;
}

export interface DomainSummary {
  domain_name: string;
  alternative_ids: string[];
  alternative_labels: Record<string, string>;
  yearly_outcomes: YearlyOutcome[];
  /** Keys: n_total, n_eligible, n_ineligible. Null when domain has no eligibility concept. */
  eligibility: { n_total: number; n_eligible: number; n_ineligible: number } | null;
}

export interface DecisionSummaryResponse {
  run_id: string;
  domains: DomainSummary[];
  metadata: Record<string, unknown>;
  warnings: string[];
}

// ============================================================================
// Execution matrix types — Story 20.6
// ============================================================================

export type ExecutionStatus = "NOT_EXECUTED" | "QUEUED" | "RUNNING" | "COMPLETED" | "FAILED";

export interface ExecutionMatrixCell {
  scenarioId: string;
  populationId: string;
  status: ExecutionStatus;
  runId?: string;
  error?: string;
  startedAt?: string;
  finishedAt?: string;
}

export interface ScenarioSummary {
  id: string;
  name: string;
  portfolioName: string | null;
  populationIds: string[];
  status: string;
  lastRunId: string | null;
}

// ============================================================================
// Comparison dimension types — Story 20.6
// ============================================================================

export interface ComparisonDimension<T = unknown> {
  id: string;
  label: string;
  description: string;
  getValue(runResult: ResultDetailResponse): T | null;
  render?(value: T): ReactNode;
}

export interface DimensionFilter {
  dimensionId: string;
  operator: "equals" | "contains" | "in";
  values: unknown[];
}

// ============================================================================
// Population comparison types — Story 21.4
// ============================================================================

export interface NumericColumnComparison {
  column_name: string;
  observed_mean: number;
  synthetic_mean: number;
  relative_diff_pct: number;
  observed_median: number;
  synthetic_median: number;
  observed_std: number;
  synthetic_std: number;
  observed_p10: number;
  synthetic_p10: number;
  observed_p50: number;
  synthetic_p50: number;
  observed_p90: number;
  synthetic_p90: number;
}

export interface PopulationComparisonResponse {
  observed_asset_id: string;
  synthetic_asset_id: string;
  row_counts: {
    observed: number;
    synthetic: number;
  };
  column_counts: {
    observed: number;
    synthetic: number;
  };
  common_numeric_columns: string[];
  numeric_comparison: Record<string, NumericColumnComparison>;
  trust_labels: {
    observed: {
      origin: string;
      access_mode: string;
      trust_status: string;
    };
    synthetic: {
      origin: string;
      access_mode: string;
      trust_status: string;
    };
  };
}
