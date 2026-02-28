/** TypeScript interfaces matching the backend Pydantic response models. */

// ============================================================================
// Request types
// ============================================================================

export interface LoginRequest {
  password: string;
}

export interface RunRequest {
  template_name: string;
  parameters: Record<string, unknown>;
  start_year: number;
  end_year: number;
  population_id?: string | null;
  seed?: number | null;
  baseline_id?: string | null;
}

export interface MemoryCheckRequest {
  template_name: string;
  parameters?: Record<string, unknown>;
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
  parameters: Record<string, unknown>;
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
  parameters: Record<string, unknown>;
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
}

export interface TemplateDetailResponse extends TemplateListItem {
  default_parameters: Record<string, unknown>;
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
