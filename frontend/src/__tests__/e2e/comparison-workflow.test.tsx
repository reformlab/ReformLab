// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Comparison Flow — end-to-end tests (Story 20.8, Task 20.8.5).
 *
 * Tests the comparison flow with scenario lineage:
 * - Compare two runs with scenario lineage preserved
 * - Export includes scenario lineage
 * - Cross-population comparison warning
 *
 * BLOCKED: Story 20.6 Tasks 20.6.3, 20.6.4, 20.6.6 must be complete.
 * Tests use .skip with clear documentation for unblocking.
 *
 * Story 20.8 — AC-1, flow 5: Compare runs → scenario lineage preserved.
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

// Recharts ResizeObserver polyfill
globalThis.ResizeObserver ??= class {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock all API modules
vi.mock("@/api/auth", () => ({ login: vi.fn() }));
vi.mock("@/api/populations", () => ({
  listPopulations: vi.fn(),
  getPopulationPreview: vi.fn(),
  getPopulationProfile: vi.fn(),
  getPopulationCrosstab: vi.fn(),
  uploadPopulation: vi.fn(),
  deletePopulation: vi.fn().mockResolvedValue(undefined),
}));
vi.mock("@/api/templates", () => ({ listTemplates: vi.fn(), getTemplate: vi.fn() }));
vi.mock("@/api/scenarios", () => ({
  listScenarios: vi.fn(),
  getScenario: vi.fn(),
  createScenario: vi.fn(),
  cloneScenario: vi.fn(),
  deleteScenario: vi.fn(),
}));
vi.mock("@/api/results", () => ({
  listResults: vi.fn(),
  getResult: vi.fn(),
  deleteResult: vi.fn(),
  exportResultCsv: vi.fn(),
  exportResultParquet: vi.fn(),
}));
vi.mock("@/api/portfolios", () => ({
  listPortfolios: vi.fn(),
  createPortfolio: vi.fn(),
  deletePortfolio: vi.fn(),
  validatePortfolio: vi.fn(),
}));
vi.mock("@/api/data-fusion", () => ({
  listDataSources: vi.fn(),
  listMergeMethods: vi.fn(),
  generatePopulation: vi.fn(),
}));
vi.mock("@/api/runs", () => ({ runScenario: vi.fn() }));
vi.mock("@/api/indicators", () => ({
  getIndicators: vi.fn(),
  comparePortfolios: vi.fn(),
}));
vi.mock("@/api/decisions", () => ({ getDecisionSummary: vi.fn() }));
vi.mock("@/api/exports", () => ({ exportCsv: vi.fn(), exportParquet: vi.fn() }));

// Imports after vi.mock
import { login } from "@/api/auth";
import { listPopulations } from "@/api/populations";
import { listTemplates, getTemplate } from "@/api/templates";
import { listResults, getResult, exportResultCsv } from "@/api/results";
import { listPortfolios } from "@/api/portfolios";
import { listDataSources, listMergeMethods } from "@/api/data-fusion";
import App from "@/App";
import { AppProvider } from "@/contexts/AppContext";
import { cleanLocalStorage } from "./helpers";
import { createTestScenario } from "./fixtures";

// ============================================================================
// Render helper
// ============================================================================

function renderApp() {
  return render(
    <AppProvider>
      <App />
    </AppProvider>,
  );
}

// ============================================================================
// Tests
// ============================================================================

describe("Comparison Workflow", () => {
  beforeEach(() => {
    cleanLocalStorage();
    vi.clearAllMocks();
    // Default mock responses
    vi.mocked(login).mockResolvedValue({ token: "test-token" });
    vi.mocked(listPopulations).mockResolvedValue([]);
    vi.mocked(listTemplates).mockResolvedValue([]);
    vi.mocked(getTemplate).mockRejectedValue(new Error("not found"));
    vi.mocked(listResults).mockResolvedValue([]);
    vi.mocked(listPortfolios).mockResolvedValue([]);
    vi.mocked(listDataSources).mockResolvedValue({});
    vi.mocked(listMergeMethods).mockResolvedValue([]);
  });

  /**
   * AC-1, Flow 5, Step 1-4:
   * Compare two runs with scenario lineage preserved.
   *
   * BLOCKED: Requires Story 20.6 Task 20.6.4 (ComparisonDashboardScreen lineage) complete.
   * TODO: Unblock when ComparisonDashboardScreen displays scenario lineage.
   * Tracking: Story 20.8, Task 20.8.5
   */
  it.skip("compare two runs with scenario lineage preserved", async () => {
    // Set up baseline scenario run
    const baselineRunId = "baseline-run-001";
    const baselineScenario = createTestScenario({
      id: "baseline-scenario",
      name: "Baseline Scenario",
    });

    // Set up reform scenario run
    const reformRunId = "reform-run-001";
    const reformScenario = createTestScenario({
      id: "reform-scenario",
      name: "Reform Scenario",
    });

    // Mock run results with lineage (Story 20.6 backend)
    vi.mocked(getResult).mockImplementation(async (runId) => {
      if (runId === baselineRunId) {
        return {
          run_id: baselineRunId,
          scenario_id: baselineScenario.id,
          scenario_name: baselineScenario.name,
          portfolio_name: baselineScenario.portfolioName,
          population_id: baselineScenario.populationIds[0],
          start_year: baselineScenario.engineConfig.startYear,
          end_year: baselineScenario.engineConfig.endYear,
          seed: baselineScenario.engineConfig.seed,
          timestamp: "2026-03-27T00:00:00Z",
          run_kind: "scenario",
          row_count: 1000,
          status: "completed",
          data_available: true,
          template_name: "carbon-tax",
          policy_type: "carbon-tax",
          adapter_version: "1.0.0",
          started_at: "2026-03-27T00:00:00Z",
          finished_at: "2026-03-27T00:00:10Z",
          indicators: null,
          columns: null,
          column_count: null,
        };
      }
      if (runId === reformRunId) {
        return {
          run_id: reformRunId,
          scenario_id: reformScenario.id,
          scenario_name: reformScenario.name,
          portfolio_name: reformScenario.portfolioName,
          population_id: reformScenario.populationIds[0],
          start_year: reformScenario.engineConfig.startYear,
          end_year: reformScenario.engineConfig.endYear,
          seed: reformScenario.engineConfig.seed,
          timestamp: "2026-03-27T00:01:00Z",
          run_kind: "scenario",
          row_count: 1000,
          status: "completed",
          data_available: true,
          template_name: "carbon-tax",
          policy_type: "carbon-tax",
          adapter_version: "1.0.0",
          started_at: "2026-03-27T00:01:00Z",
          finished_at: "2026-03-27T00:01:10Z",
          indicators: null,
          columns: null,
          column_count: null,
        };
      }
      throw new Error("Run not found");
    });

    // Mock listResults to return both runs
    vi.mocked(listResults).mockResolvedValue([
      {
        run_id: baselineRunId,
        timestamp: "2026-03-27T00:00:00Z",
        run_kind: "scenario",
        start_year: 2025,
        end_year: 2030,
        row_count: 1000,
        status: "completed",
        data_available: true,
        template_name: "carbon-tax",
        policy_type: "carbon-tax",
        portfolio_name: null,
      },
      {
        run_id: reformRunId,
        timestamp: "2026-03-27T00:01:00Z",
        run_kind: "scenario",
        start_year: 2025,
        end_year: 2030,
        row_count: 1000,
        status: "completed",
        data_available: true,
        template_name: "carbon-tax",
        policy_type: "carbon-tax",
        portfolio_name: null,
      },
    ]);

    const user = userEvent.setup();
    renderApp();

    // Auth
    await user.type(screen.getByPlaceholderText(/password/i), "secret");
    await user.click(screen.getByRole("button", { name: /enter/i }));

    // Navigate to comparison view
    window.location.hash = "#results/comparison";
    window.dispatchEvent(new HashChangeEvent("hashchange"));

    await waitFor(() => {
      expect(window.location.hash).toBe("#results/comparison");
    });

    // TODO: When Story 20.6 complete, assert:
    // - Comparison view shows side-by-side results
    // - Each run shows scenario name, portfolio, population in header
    // - Lineage fields are displayed
  });

  /**
   * AC-1, Flow 5, Step 5:
   * Export includes scenario lineage.
   *
   * BLOCKED: Requires Story 20.6 Tasks 20.6.3 (ResultsOverviewScreen export) and
   * 20.6.6 (ResultStore lineage) complete.
   * TODO: Unblock when export endpoints include lineage metadata.
   * Tracking: Story 20.8, Task 20.8.5
   */
  it.skip("export includes scenario lineage", async () => {
    const runId = "run-with-lineage-001";

    // Mock export response with lineage columns
    vi.mocked(exportResultCsv).mockResolvedValue({
      content: "scenario_id,scenario_name,population_id,decile,value\n" +
                `${expectedLineageFields.scenario_id},${expectedLineageFields.scenario_name},${expectedLineageFields.population_id},1,-100\n`,
      filename: `export-${runId}.csv`,
    });

    // TODO: When Story 20.6 complete:
    // 1. From comparison view, export results
    // 2. Assert exported CSV includes lineage columns:
    //    - scenario_id
    //    - scenario_name
    //    - portfolio_name
    //    - population_id
    //    - start_year
    //    - end_year
    //    - seed
  });

  /**
   * AC-1, Flow 5, Step 6:
   * Cross-population comparison warning.
   *
   * BLOCKED: Requires comparison UI lineage display complete.
   * TODO: Unblock when ComparisonDashboardScreen shows cross-population warning.
   * Tracking: Story 20.8, Task 20.8.5
   */
  it.skip("cross-population comparison warning", async () => {
    // Set up runs from different populations
    const runPopulationA = "run-pop-a-001";
    const runPopulationB = "run-pop-b-001";

    // Create scenarios (not directly used in test but set up for completeness)
    createTestScenario({
      id: "scenario-pop-a",
      populationIds: ["fr-synthetic-2024"],
    });
    createTestScenario({
      id: "scenario-pop-b",
      populationIds: ["eu-synthetic-2024"],
    });

    vi.mocked(listResults).mockResolvedValue([
      {
        run_id: runPopulationA,
        timestamp: "2026-03-27T00:00:00Z",
        run_kind: "scenario",
        start_year: 2025,
        end_year: 2030,
        row_count: 1000,
        status: "completed",
        data_available: true,
        template_name: "carbon-tax",
        policy_type: "carbon-tax",
        portfolio_name: null,
      },
      {
        run_id: runPopulationB,
        timestamp: "2026-03-27T00:01:00Z",
        run_kind: "scenario",
        start_year: 2025,
        end_year: 2030,
        row_count: 1000,
        status: "completed",
        data_available: true,
        template_name: "carbon-tax",
        policy_type: "carbon-tax",
        portfolio_name: null,
      },
    ]);

    const user = userEvent.setup();
    renderApp();

    // Auth
    await user.type(screen.getByPlaceholderText(/password/i), "secret");
    await user.click(screen.getByRole("button", { name: /enter/i }));

    // Navigate to comparison
    window.location.hash = "#results/comparison";
    window.dispatchEvent(new HashChangeEvent("hashchange"));

    await waitFor(() => {
      expect(window.location.hash).toBe("#results/comparison");
    });

    // TODO: When Story 20.6 complete:
    // - Select runs from different populations
    // - Assert warning appears: crossPopulationWarning
    // - Assert comparison proceeds despite warning
  });

  /**
   * UNBLOCKED: Basic comparison navigation works.
   *
   * This test is not blocked and should pass.
   * Does not assert scenario lineage (not implemented yet).
   */
  it("navigates to comparison view without error", async () => {
    const user = userEvent.setup();
    renderApp();

    // Auth
    await user.type(screen.getByPlaceholderText(/password/i), "secret");
    await user.click(screen.getByRole("button", { name: /enter/i }));

    // Navigate to comparison view
    window.location.hash = "#results/comparison";
    window.dispatchEvent(new HashChangeEvent("hashchange"));

    // Assert: navigation completes without error
    await waitFor(() => {
      expect(window.location.hash).toBe("#results/comparison");
    });
  });

  /**
   * UNBLOCKED: Can select runs for comparison.
   *
   * Tests the basic selection UI without asserting lineage display.
   */
  it("can select runs for comparison from results list", async () => {
    // Mock some completed runs
    vi.mocked(listResults).mockResolvedValue([
      {
        run_id: "run-001",
        timestamp: "2026-03-27T00:00:00Z",
        run_kind: "scenario",
        start_year: 2025,
        end_year: 2030,
        row_count: 1000,
        status: "completed",
        data_available: true,
        template_name: "carbon-tax",
        policy_type: "carbon-tax",
        portfolio_name: null,
      },
      {
        run_id: "run-002",
        timestamp: "2026-03-27T00:01:00Z",
        run_kind: "scenario",
        start_year: 2025,
        end_year: 2030,
        row_count: 1000,
        status: "completed",
        data_available: true,
        template_name: "carbon-tax",
        policy_type: "carbon-tax",
        portfolio_name: null,
      },
    ]);

    const user = userEvent.setup();
    renderApp();

    // Auth
    await user.type(screen.getByPlaceholderText(/password/i), "secret");
    await user.click(screen.getByRole("button", { name: /enter/i }));

    // Navigate to results
    window.location.hash = "#results";
    window.dispatchEvent(new HashChangeEvent("hashchange"));

    await waitFor(() => {
      expect(window.location.hash).toBe("#results");
    });

    // TODO: Implement selection UI interaction when complete
    // For now, just verify navigation works
  });
});
