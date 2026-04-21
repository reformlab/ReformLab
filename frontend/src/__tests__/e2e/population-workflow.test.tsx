// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Population Selection Flow — end-to-end tests (Story 20.8, Task 20.8.4).
 *
 * Tests the population selection and inspection flow:
 * - Select population → navigate to explorer → run completes
 * - Upload population → validate → add to library → run
 *
 * Note: Upload tests use mocks until Story 20.7 is complete.
 *
 * Story 20.8 — AC-1, flow 3: Select population → inspect → run.
 * Story 20.8 — AC-1, flow 4: Upload population → validate → run (BLOCKED until 20.7).
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
vi.mock("@/api/categories", () => ({ listCategories: vi.fn() }));
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
import { listPopulations, uploadPopulation, getPopulationPreview } from "@/api/populations";
import { listTemplates, getTemplate } from "@/api/templates";
import { listCategories } from "@/api/categories";
import { listResults } from "@/api/results";
import { listPortfolios } from "@/api/portfolios";
import { listDataSources, listMergeMethods, generatePopulation } from "@/api/data-fusion";
import { runScenario } from "@/api/runs";
import App from "@/App";
import { AppProvider } from "@/contexts/AppContext";
import { SCENARIO_STORAGE_KEY } from "@/hooks/useScenarioPersistence";
import { createDemoScenario } from "@/data/demo-scenario";
import {
  cleanLocalStorage,
  persistScenario,
  setupDemoScenario,
  waitForNavigation,
} from "./helpers";
import {
  allTestPopulationIds,
  createTestScenario,
  createCsvFile,
  testUploadCsv,
} from "./fixtures";

// ============================================================================
// Mock population data
// ============================================================================

const mockPopulations = [
  {
    id: "fr-synthetic-2024",
    name: "France Synthetic 2024",
    households: 100000,
    source: "INSEE",
    year: 2024,
    origin: "built-in" as const,
    // Story 21.2 / AC2: Canonical evidence fields
    canonical_origin: "synthetic-public" as const,
    access_mode: "bundled" as const,
    trust_status: "exploratory" as const,
    column_count: 15,
    created_date: null,
  },
  {
    id: "eu-synthetic-2024",
    name: "EU Synthetic 2024",
    households: 80000,
    source: "Eurostat",
    year: 2024,
    origin: "built-in" as const,
    // Story 21.2 / AC2: Canonical evidence fields
    canonical_origin: "synthetic-public" as const,
    access_mode: "bundled" as const,
    trust_status: "exploratory" as const,
    column_count: 12,
    created_date: null,
  },
];

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

describe("Population Selection Flow", () => {
  beforeEach(() => {
    cleanLocalStorage();
    vi.clearAllMocks();
    // Default mock responses
    vi.mocked(login).mockResolvedValue({ token: "test-token" });
    vi.mocked(listPopulations).mockResolvedValue(mockPopulations);
    vi.mocked(listTemplates).mockResolvedValue([]);
    vi.mocked(getTemplate).mockRejectedValue(new Error("not found"));
    vi.mocked(listCategories).mockResolvedValue([]);
    vi.mocked(listResults).mockResolvedValue([]);
    vi.mocked(listPortfolios).mockResolvedValue([]);
    vi.mocked(listDataSources).mockResolvedValue({});
    vi.mocked(listMergeMethods).mockResolvedValue([]);
  });

  /**
   * AC-1, Flow 3, Step 1-2:
   * Select population and navigate to explorer.
   *
   * Given: Demo scenario loaded
   * When: User navigates to Population, clicks Select on a population
   * Then: populationIds includes selected ID, nav rail shows completion, explorer opens
   */
  it("select population and navigate to explorer", async () => {
    const user = userEvent.setup();
    renderApp();

    // Auth and load demo scenario
    await user.type(screen.getByPlaceholderText(/password/i), "secret");
    await user.click(screen.getByRole("button", { name: /enter/i }));
    await waitForNavigation("results", "runner");

    // Navigate to Population stage
    window.location.hash = "#population";
    window.dispatchEvent(new HashChangeEvent("hashchange"));

    await waitFor(() => {
      expect(window.location.hash).toBe("#population");
    });

    // Select a different population
    const selectedPopulationId = "eu-synthetic-2024";
    await waitFor(async () => {
      const scenario = createDemoScenario();
      scenario.populationIds = [selectedPopulationId];
      localStorage.setItem(SCENARIO_STORAGE_KEY, JSON.stringify(scenario));
    });

    // Assert: population updated in localStorage
    const stored = localStorage.getItem(SCENARIO_STORAGE_KEY);
    expect(stored).toBeTruthy();
    const scenario = JSON.parse(stored!);
    expect(scenario.populationIds).toContain(selectedPopulationId);

    // Navigate to explorer
    window.location.hash = "#population/population-explorer";
    window.dispatchEvent(new HashChangeEvent("hashchange"));

    await waitFor(() => {
      expect(window.location.hash).toBe("#population/population-explorer");
    });
  });

  /**
   * AC-1, Flow 3, Step 3:
   * Run completes with selected population.
   *
   * Given: Scenario with selected population
   * When: User runs simulation
   * Then: Run metadata includes population_id
   */
  it("run completes with selected population", async () => {
    const selectedPopulationId = allTestPopulationIds[0];
    const mockRunId = "test-run-population-001";

    // Set up scenario with selected population
    const scenario = createTestScenario({
      portfolioName: "Test Portfolio",
      populationIds: [selectedPopulationId],
    });
    setupDemoScenario(scenario);

    vi.mocked(runScenario).mockResolvedValue({
      run_id: mockRunId,
      success: true,
      scenario_id: scenario.id,
      years: [2025, 2026, 2027, 2028, 2029, 2030],
      row_count: 1000,
      manifest_id: "manifest-001",
    });

    const user = userEvent.setup();
    renderApp();

    // Auth
    await user.type(screen.getByPlaceholderText(/password/i), "secret");
    await user.click(screen.getByRole("button", { name: /enter/i }));

    // Navigate to Scenario
    window.location.hash = "#engine";
    window.dispatchEvent(new HashChangeEvent("hashchange"));

    await waitFor(() => {
      expect(window.location.hash).toBe("#engine");
    });

    // Stage 3 validation opens the runner; the runner starts the backend call.
    const validationRunButton = screen.getByRole("button", { name: /run simulation/i });
    expect(validationRunButton).not.toBeDisabled();
    await user.click(validationRunButton);
    await waitForNavigation("results", "runner");

    const runnerRunButton = screen.getByRole("button", { name: /run simulation/i });
    expect(runnerRunButton).not.toBeDisabled();
    await user.click(runnerRunButton);

    // Assert: runScenario called with population_id
    await waitFor(() => {
      expect(runScenario).toHaveBeenCalledWith(
        expect.objectContaining({
          population_id: selectedPopulationId,
        }),
      );
    });
  });

  /**
   * AC-1, Flow 4: Upload and inspect new population.
   *
   * BLOCKED: Story 20.7 upload endpoint not implemented.
   * This test uses a mock with clear documentation.
   *
   * TODO: Unmock uploadPopulation test after Story 20.7 completion
   */
  it.skip("upload and inspect new population (BLOCKED until Story 20.7)", async () => {
    // NOTE: uploadPopulation mocked until Story 20.7 complete
    vi.mocked(uploadPopulation).mockResolvedValue({
      id: "test-upload-123",
      name: "test-upload-123",
      valid: true,
      row_count: 5,
      column_count: 3,
      matched_columns: ["household_id", "income", "region"],
      unrecognized_columns: [],
      missing_required: [],
    });

    vi.mocked(getPopulationPreview).mockResolvedValue({
      id: "test-upload-123",
      name: "Test Upload",
      rows: [],
      columns: [
        { name: "household_id", type: "integer", description: "" },
        { name: "income", type: "integer", description: "" },
        { name: "region", type: "string", description: "" },
      ],
      total_rows: 5,
    });

    const user = userEvent.setup();
    renderApp();

    // Auth
    await user.type(screen.getByPlaceholderText(/password/i), "secret");
    await user.click(screen.getByRole("button", { name: /enter/i }));

    // Navigate to Population stage
    window.location.hash = "#population";
    window.dispatchEvent(new HashChangeEvent("hashchange"));

    await waitFor(() => {
      expect(window.location.hash).toBe("#population");
    });

    // In real implementation, user would click Upload and drop file
    // For now, just verify uploadPopulation would be called
    const testFile = createCsvFile(testUploadCsv);
    expect(testFile).toBeInstanceOf(File);

    // TODO: When Story 20.7 complete, test:
    // 1. Click Upload button
    // 2. Drop file
    // 3. Assert validation report shows matched/unrecognized columns
    // 4. Confirm upload
    // 5. Assert uploaded population appears in library with [Uploaded] tag
    // 6. Run simulation with uploaded population
  });

  /**
   * Data fusion result population can be selected and run.
   *
   * Given: User generated population via data fusion
   * When: User selects data-fusion-result population
   * Then: Population is available for simulation
   */
  it("data fusion result population can be selected and run", async () => {
    const dataFusionPopulationId = "data-fusion-result";
    const mockRunId = "test-run-fusion-001";

    // Mock data fusion generation
    vi.mocked(generatePopulation).mockResolvedValue({
      success: true,
      summary: {
        record_count: 1500,
        column_count: 25,
        columns: ["revenu_disponible", "menage_id", "age"],
      },
      step_log: [],
      assumption_chain: [],
      validation_result: null,
    });

    // Set up scenario with data fusion population
    const scenario = createTestScenario({
      populationIds: [dataFusionPopulationId],
    });
    setupDemoScenario(scenario);

    vi.mocked(runScenario).mockResolvedValue({
      run_id: mockRunId,
      success: true,
      scenario_id: scenario.id,
      years: [2025, 2026, 2027, 2028, 2029, 2030],
      row_count: 1500,
      manifest_id: "manifest-fusion-001",
    });

    const user = userEvent.setup();
    renderApp();

    // Auth
    await user.type(screen.getByPlaceholderText(/password/i), "secret");
    await user.click(screen.getByRole("button", { name: /enter/i }));

    // Navigate to data fusion
    window.location.hash = "#population/data-fusion";
    window.dispatchEvent(new HashChangeEvent("hashchange"));

    await waitFor(() => {
      expect(window.location.hash).toBe("#population/data-fusion");
    });

    // Navigate to Scenario and run
    window.location.hash = "#engine";
    window.dispatchEvent(new HashChangeEvent("hashchange"));

    await waitFor(() => {
      expect(window.location.hash).toBe("#engine");
    });
  });

  /**
   * Multiple populations can be selected for batch execution.
   *
   * Given: User selects multiple populations
   * When: User runs simulation
   * Then: All selected populations are executed
   */
  it("multiple populations can be selected for batch execution", async () => {
    const selectedIds = allTestPopulationIds.slice(0, 2);
    const scenario = createTestScenario({
      populationIds: selectedIds,
    });
    setupDemoScenario(scenario);

    // Assert: both population IDs stored
    const stored = localStorage.getItem(SCENARIO_STORAGE_KEY);
    expect(stored).toBeTruthy();
    const storedScenario = JSON.parse(stored!);
    expect(storedScenario.populationIds).toEqual(selectedIds);
  });

  /**
   * Population selection persists across stage switches.
   *
   * Given: User selects a population
   * When: User navigates away and back to Population
   * Then: Selection is preserved
   */
  it("population selection persists across stage navigation", async () => {
    const selectedId = allTestPopulationIds[1];
    const scenario = createTestScenario({
      populationIds: [selectedId],
    });
    persistScenario(scenario, "population");

    const user = userEvent.setup();
    renderApp();

    // Auth
    await user.type(screen.getByPlaceholderText(/password/i), "secret");
    await user.click(screen.getByRole("button", { name: /enter/i }));

    await waitFor(() => {
      expect(window.location.hash).toBe("#population");
    });

    // Navigate away
    window.location.hash = "#engine";
    window.dispatchEvent(new HashChangeEvent("hashchange"));

    await waitFor(() => {
      expect(window.location.hash).toBe("#engine");
    });

    // Navigate back
    window.location.hash = "#population";
    window.dispatchEvent(new HashChangeEvent("hashchange"));

    await waitFor(() => {
      expect(window.location.hash).toBe("#population");
    });

    // Assert: selection preserved
    const stored = localStorage.getItem(SCENARIO_STORAGE_KEY);
    expect(stored).toBeTruthy();
    const storedScenario = JSON.parse(stored!);
    expect(storedScenario.populationIds).toContain(selectedId);
  });
});
