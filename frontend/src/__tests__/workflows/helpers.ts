/**
 * Shared utilities for workflow integration tests (Story 17.8).
 *
 * Provides: ResizeObserver + export browser-API polyfills, and mock factories
 * for all major response types used across workflow test files.
 */

import { vi } from "vitest";

import type {
  GenerationResult,
  PortfolioComparisonResponse,
  ResultDetailResponse,
  ResultListItem,
  RunResponse,
} from "@/api/types";

// ============================================================================
// Browser API polyfills
// ============================================================================

/** Install ResizeObserver stub required by Recharts components. */
export function setupResizeObserver(): void {
  globalThis.ResizeObserver ??= class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}

/** Stub URL.createObjectURL / revokeObjectURL used by CSV/Parquet export flows. */
export function setupExportMocks(): void {
  if (!globalThis.URL.createObjectURL) {
    globalThis.URL.createObjectURL = vi.fn(() => "blob:mock-url");
  }
  if (!globalThis.URL.revokeObjectURL) {
    globalThis.URL.revokeObjectURL = vi.fn();
  }
}

// ============================================================================
// Mock factories
// ============================================================================

export function mockResultListItem(overrides: Partial<ResultListItem> = {}): ResultListItem {
  return {
    run_id: "run-001",
    timestamp: "2026-03-08T00:00:00Z",
    run_kind: "scenario",
    start_year: 2025,
    end_year: 2030,
    row_count: 1000,
    status: "completed",
    data_available: true,
    template_name: "carbon_tax",
    policy_type: "carbon_tax",
    portfolio_name: null,
    ...overrides,
  };
}

export function mockResultDetailResponse(overrides: Partial<ResultDetailResponse> = {}): ResultDetailResponse {
  return {
    run_id: "run-001",
    timestamp: "2026-03-08T00:00:00Z",
    run_kind: "scenario",
    start_year: 2025,
    end_year: 2030,
    row_count: 1000,
    status: "completed",
    data_available: true,
    template_name: "carbon_tax",
    policy_type: "carbon_tax",
    portfolio_name: null,
    population_id: "fr-synthetic-2024",
    seed: 42,
    manifest_id: "manifest-001",
    scenario_id: "scenario-001",
    adapter_version: "1.0.0",
    started_at: "2026-03-08T00:00:00Z",
    finished_at: "2026-03-08T00:00:10Z",
    indicators: null,
    columns: null,
    column_count: null,
    ...overrides,
  };
}

export function mockRunResponse(overrides: Partial<RunResponse> = {}): RunResponse {
  return {
    run_id: "run-001",
    success: true,
    scenario_id: "scenario-001",
    years: [2025, 2026, 2027, 2028, 2029, 2030],
    row_count: 1000,
    manifest_id: "manifest-001",
    ...overrides,
  };
}

export function mockGenerationResult(overrides: Partial<GenerationResult> = {}): GenerationResult {
  return {
    success: true,
    summary: {
      record_count: 1500,
      column_count: 25,
      columns: ["revenu_disponible", "menage_id", "age"],
    },
    step_log: [],
    assumption_chain: [],
    validation_result: null,
    ...overrides,
  };
}

export function mockComparisonResponse(): PortfolioComparisonResponse {
  return {
    comparisons: {
      distributional: {
        columns: ["decile", "Policy A", "Policy B", "delta_Policy B"],
        data: {
          decile: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
          "Policy A": [-120, -180, -240, -310, -400, -520, -680, -890, -1200, -1800],
          "Policy B": [-80, -150, -210, -290, -390, -520, -690, -920, -1260, -1950],
          "delta_Policy B": [40, 30, 30, 20, 10, 0, -10, -30, -60, -150],
        },
      },
      fiscal: {
        columns: ["year", "metric", "Policy A", "Policy B"],
        data: {
          year: [2025, 2026],
          metric: ["revenue", "revenue"],
          "Policy A": [2100000000, 2300000000],
          "Policy B": [1800000000, 2000000000],
        },
      },
    },
    cross_metrics: [
      {
        criterion: "max_fiscal_revenue",
        best_portfolio: "Policy A",
        value: 4400000000,
        all_values: { "Policy A": 4400000000, "Policy B": 3800000000 },
      },
    ],
    portfolio_labels: ["Policy A", "Policy B"],
    metadata: { baseline_label: "Policy A" },
    warnings: [],
  };
}
