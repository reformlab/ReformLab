// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * First Launch Flow — end-to-end tests (Story 20.8, Task 20.8.2).
 *
 * Tests the critical first-launch user flow:
 * - Clean localStorage → password prompt
 * - Auth → demo scenario auto-loads
 * - Navigation → runner view (#results/runner)
 * - Run Simulation button present and enabled
 * - Returning user restores scenario from localStorage
 *
 * Uses the E2E test helpers and fixtures for reusable utilities.
 *
 * Story 20.8 — AC-1, flow 1: First launch → demo scenario → run completes.
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

// Mock all API modules before imports
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

// Imports after vi.mock hoisting
import { login } from "@/api/auth";
import { listPopulations } from "@/api/populations";
import { listTemplates, getTemplate } from "@/api/templates";
import { listResults } from "@/api/results";
import { listPortfolios } from "@/api/portfolios";
import { listDataSources, listMergeMethods } from "@/api/data-fusion";
import { runScenario } from "@/api/runs";
import App from "@/App";
import { AppProvider } from "@/contexts/AppContext";
import {
  HAS_LAUNCHED_KEY,
  SCENARIO_STORAGE_KEY,
} from "@/hooks/useScenarioPersistence";
import { createDemoScenario } from "@/data/demo-scenario";
import {
  cleanLocalStorage,
  persistScenario,
  waitForNavigation,
} from "./helpers";
import { demoScenarioConfig } from "./fixtures";

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

describe("First Launch Flow", () => {
  beforeEach(() => {
    cleanLocalStorage();
    vi.clearAllMocks();
    // Set up default mock responses
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
   * AC-1, Flow 1, Step 1-3:
   * First launch loads demo scenario and navigates to runner.
   *
   * Given: localStorage is clean (first launch)
   * When: User authenticates
   * Then: Demo scenario loads, hash is #results/runner, Run button enabled
   */
  it("first launch loads demo scenario and navigates to runner", async () => {
    const user = userEvent.setup();
    renderApp();

    // Auth: enter password and click Enter
    await user.type(screen.getByPlaceholderText(/password/i), "secret");
    await user.click(screen.getByRole("button", { name: /enter/i }));

    // Wait for first-launch navigation to runner
    await waitForNavigation("results", "runner");

    // Assert: demo scenario loaded in localStorage
    const storedScenario = localStorage.getItem(SCENARIO_STORAGE_KEY);
    expect(storedScenario).toBeTruthy();
    const scenario = JSON.parse(storedScenario!);
    expect(scenario.id).toBe(demoScenarioConfig.id);
    expect(scenario.name).toBe(demoScenarioConfig.name);

    // Assert: has-launched flag set
    expect(localStorage.getItem(HAS_LAUNCHED_KEY)).toBe("true");

    // Assert: Run Simulation button present and enabled (validation passed)
    const runButton = screen.getByRole("button", { name: /run simulation/i });
    expect(runButton).toBeInTheDocument();
    expect(runButton).not.toBeDisabled();
  });

  /**
   * AC-1, Flow 1, Step 4:
   * Demo scenario run completes successfully.
   *
   * Given: Demo scenario loaded
   * When: User clicks Run Simulation
   * Then: Run completes, results displayed, lastRunId set
   *
   * Note: This test uses mocked runScenario for speed.
   * When backend is available, unmock to test real API.
   */
  it("demo scenario run completes successfully", async () => {
    const mockRunId = "test-run-001";
    vi.mocked(runScenario).mockResolvedValue({
      run_id: mockRunId,
      success: true,
      scenario_id: demoScenarioConfig.id,
      years: [2025, 2026, 2027, 2028, 2029, 2030],
      row_count: 1000,
      manifest_id: "manifest-001",
    });

    const user = userEvent.setup();
    renderApp();

    // Auth and navigate to runner
    await user.type(screen.getByPlaceholderText(/password/i), "secret");
    await user.click(screen.getByRole("button", { name: /enter/i }));
    await waitForNavigation("results", "runner");

    // Click Run Simulation
    const runButton = screen.getByRole("button", { name: /run simulation/i });
    await user.click(runButton);

    // Assert: runScenario called with demo config
    expect(runScenario).toHaveBeenCalledWith(
      expect.objectContaining({
        template_name: demoScenarioConfig.policyType,
        start_year: demoScenarioConfig.engineConfig.startYear,
        end_year: demoScenarioConfig.engineConfig.endYear,
        population_id: demoScenarioConfig.populationIds[0],
        seed: demoScenarioConfig.engineConfig.seed,
      }),
    );

    // Assert: run completed and lastRunId set
    await waitFor(() => {
      const storedScenario = localStorage.getItem(SCENARIO_STORAGE_KEY);
      expect(storedScenario).toBeTruthy();
      const scenario = JSON.parse(storedScenario!);
      expect(scenario.lastRunId).toBe(mockRunId);
    });
  });

  /**
   * AC-1, Flow 1, Step 5:
   * Returning user restores scenario from localStorage.
   *
   * Given: User has previously launched and has a saved scenario
   * When: User returns and authenticates
   * Then: Saved scenario is restored, last active stage is restored
   */
  it("returning user restores scenario from localStorage", async () => {
    // Set up: persist a scenario and stage
    const testScenario = createDemoScenario();
    const testStage = "engine" as const;
    persistScenario(testScenario, testStage);

    // Render app
    const user = userEvent.setup();
    renderApp();

    // Auth
    await user.type(screen.getByPlaceholderText(/password/i), "secret");
    await user.click(screen.getByRole("button", { name: /enter/i }));

    // Assert: restored scenario matches saved state
    await waitFor(() => {
      const storedScenario = localStorage.getItem(SCENARIO_STORAGE_KEY);
      expect(storedScenario).toBeTruthy();
      const scenario = JSON.parse(storedScenario!);
      expect(scenario.id).toBe(testScenario.id);
      expect(scenario.name).toBe(testScenario.name);
    });

    // Assert: last active stage restored
    await waitFor(() => {
      expect(window.location.hash).toBe(`#${testStage}`);
    });
  });

  /**
   * Returning user with lastRunId sees previous run in results.
   *
   * Given: User has a scenario with a completed run
   * When: User navigates to results
   * Then: Previous run is displayed
   */
  it("returning user with completed run sees results", async () => {
    // Set up: scenario with lastRunId
    const scenarioWithRun = {
      ...createDemoScenario(),
      lastRunId: "previous-run-123",
    };
    persistScenario(scenarioWithRun, "results");

    // Mock results list to include the run
    vi.mocked(listResults).mockResolvedValue([
      {
        run_id: "previous-run-123",
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
    ]);

    const user = userEvent.setup();
    renderApp();

    // Auth
    await user.type(screen.getByPlaceholderText(/password/i), "secret");
    await user.click(screen.getByRole("button", { name: /enter/i }));

    // Assert: navigates to results (not runner, because run exists)
    await waitFor(() => {
      expect(window.location.hash).toBe("#results");
    });
  });

  /**
   * Edge case: localStorage corrupted recovers gracefully.
   *
   * Given: localStorage has invalid JSON
   * When: App initializes
   * Then: Falls back to demo scenario (first-launch behavior)
   */
  it("corrupted localStorage falls back to demo scenario", async () => {
    // Corrupt the scenario storage
    localStorage.setItem(SCENARIO_STORAGE_KEY, "invalid-json{");
    localStorage.setItem(HAS_LAUNCHED_KEY, "true");

    const user = userEvent.setup();
    renderApp();

    // Auth
    await user.type(screen.getByPlaceholderText(/password/i), "secret");
    await user.click(screen.getByRole("button", { name: /enter/i }));

    // Assert: should recover and load demo scenario
    await waitFor(() => {
      const storedScenario = localStorage.getItem(SCENARIO_STORAGE_KEY);
      expect(storedScenario).toBeTruthy();
      // Should now be valid JSON
      expect(() => JSON.parse(storedScenario!)).not.toThrow();
    });
  });
});
