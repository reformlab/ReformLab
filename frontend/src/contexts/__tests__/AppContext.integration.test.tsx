// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * AppContext integration tests — Story 27.13: AppContext naming-state hardening.
 *
 * Tests the four edge cases from Story 26.7 review:
 * 1. selectedPortfolioName reset on createNewScenario()
 * 2. selectedPortfolioName reset on cloneCurrentScenario()
 * 3. Manual-edit lock clearing on portfolioName changes
 * 4. Empty populationIds restore protection
 *
 * Uses the E2E test pattern from first-launch-flow.test.tsx.
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

// Mock all API modules before imports (same pattern as first-launch-flow.test.tsx)
vi.mock("@/api/auth", () => ({ login: vi.fn(), logout: vi.fn() }));
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

// Mock useScenarioPersistence to avoid localStorage
vi.mock("@/hooks/useScenarioPersistence", () => ({
  isFirstLaunch: () => false,
  markLaunched: () => {},
  saveScenario: () => {},
  loadScenario: () => null,
  saveStage: () => {},
  loadStage: () => null,
  getSavedScenarios: () => [],
  saveScenarioToList: () => {},
  getManuallyEditedNames: () => new Set(),
  saveManuallyEditedNames: () => {},
  HAS_LAUNCHED_KEY: "reformlab-has-launched",
  SCENARIO_STORAGE_KEY: "reformlab-active-scenario",
  STAGE_STORAGE_KEY: "reformlab-active-stage",
  SAVED_SCENARIOS_KEY: "reformlab-saved-scenarios",
  MANUALLY_EDITED_NAMES_KEY: "reformlab-manually-edited-names",
}));

// Imports after vi.mock hoisting
import { login } from "@/api/auth";
import { listPopulations } from "@/api/populations";
import { listTemplates, getTemplate } from "@/api/templates";
import { listResults } from "@/api/results";
import { listPortfolios } from "@/api/portfolios";
import { listDataSources, listMergeMethods } from "@/api/data-fusion";
import App from "@/App";
import { AppProvider, useAppState } from "@/contexts/AppContext";
import type { WorkspaceScenario } from "@/types/workspace";
import {
  cleanLocalStorage,
} from "@/__tests__/e2e/helpers";

// ============================================================================
// Test helpers
// ============================================================================

/** Test component that renders App and provides access to app state */
function TestAppWithStateAccess({
  onStateReady,
}: {
  onStateReady: (state: ReturnType<typeof useAppState>) => void;
}) {
  const state = useAppState();
  // Call the callback with state once it's ready
  onStateReady(state);
  return null;
}

function renderAppWithStateAccess() {
  let stateRef: ReturnType<typeof useAppState> | null = null;

  const renderResult = render(
    <AppProvider>
      <App />
      <TestAppWithStateAccess
        onStateReady={(state) => {
          stateRef = state;
        }}
      />
    </AppProvider>,
  );

  const getState = () => {
    if (!stateRef) throw new Error("State not ready");
    return stateRef;
  };

  return { ...renderResult, getState };
}

// Set up default mock responses
function setupDefaultMocks() {
  vi.mocked(login).mockResolvedValue({ token: "test-token" });
  vi.mocked(listPopulations).mockResolvedValue([
    { id: "fr-synthetic-2024", name: "FR Synthetic 2024", shortName: "FR Synthetic 2024" },
    { id: "fr-household-2023", name: "FR Household 2023", shortName: "FR Household 2023" },
  ]);
  vi.mocked(listTemplates).mockResolvedValue([
    { id: "carbon-tax", name: "Carbon Tax", type: "carbon-tax", category_id: "carbon" },
  ]);
  vi.mocked(getTemplate).mockResolvedValue({
    parameters: [],
    defaultValues: {},
    default_policy: {},
    policy_types: [],
    policy_schema: {},
  });
  vi.mocked(listResults).mockResolvedValue([]);
  vi.mocked(listPortfolios).mockResolvedValue([]);
  vi.mocked(listDataSources).mockResolvedValue({});
  vi.mocked(listMergeMethods).mockResolvedValue([]);
}

// ============================================================================
// Tests
// ============================================================================

describe("Story 27.13: AppContext naming-state hardening", () => {
  beforeEach(() => {
    cleanLocalStorage();
    vi.clearAllMocks();
    setupDefaultMocks();
  });

  /**
   * Task 1.1-1.2: AC-1 - createNewScenario() resets selectedPortfolioName
   *
   * Given: selectedPortfolioName is "Test Portfolio"
   * When: User calls createNewScenario()
   * Then: selectedPortfolioName is null and name doesn't include "Test Portfolio"
   */
  it("AC-1: createNewScenario() resets selectedPortfolioName and generates correct name", async () => {
    const user = userEvent.setup();
    const { getState } = renderAppWithStateAccess();

    // Auth and wait for app to initialize
    await user.type(screen.getByPlaceholderText(/password/i), "secret");
    await user.click(screen.getByRole("button", { name: /enter/i }));

    await waitFor(() => {
      expect(getState().isAuthenticated).toBe(true);
    });

    // Set selectedPortfolioName
    getState().setSelectedPortfolioName("Test Portfolio");

    // Verify it's set
    await waitFor(() => {
      expect(getState().selectedPortfolioName).toBe("Test Portfolio");
    });

    // Call createNewScenario()
    getState().createNewScenario();

    // Assert: selectedPortfolioName is null
    await waitFor(() => {
      expect(getState().selectedPortfolioName).toBeNull();
    });

    // Assert: new scenario name doesn't include "Test Portfolio"
    await waitFor(() => {
      expect(getState().activeScenario?.name).not.toContain("Test Portfolio");
      // Should be generic "Untitled (FR Synthetic 2024)" since no portfolio but population is selected
      expect(getState().activeScenario?.name).toContain("Untitled");
    });
  });

  /**
   * Task 1.3: AC-2 - cloneCurrentScenario() resets selectedPortfolioName
   *
   * Given: A scenario exists and selectedPortfolioName is "Test Portfolio"
   * When: User calls cloneCurrentScenario()
   * Then: selectedPortfolioName is null and clone uses clone naming pattern
   */
  it("AC-2: cloneCurrentScenario() resets selectedPortfolioName and uses clone naming", async () => {
    const user = userEvent.setup();
    const { getState } = renderAppWithStateAccess();

    // Auth and wait for app to initialize
    await user.type(screen.getByPlaceholderText(/password/i), "secret");
    await user.click(screen.getByRole("button", { name: /enter/i }));

    await waitFor(() => {
      expect(getState().isAuthenticated).toBe(true);
    });

    // Create a test scenario with the expected auto-name to avoid race condition
    // When we set selectedPortfolioName and selectedPopulationId, the auto-name effect
    // will generate "Test Portfolio (FR Synthetic 2024)"
    const testScenario: WorkspaceScenario = {
      id: "test-scenario-1",
      name: "Test Portfolio (FR Synthetic 2024)", // Pre-set to expected auto-name
      version: "1.0",
      status: "draft",
      isBaseline: false,
      baselineRef: null,
      portfolioName: null,
      populationIds: ["fr-synthetic-2024"],
      engineConfig: {
        startYear: 2025,
        endYear: 2030,
        seed: 42,
        investmentDecisionsEnabled: null,
        logitModel: null,
        discountRate: 0.03,
        tasteParameters: null,
        calibrationState: "not_configured",
      },
      policyType: "carbon-tax",
      lastRunId: null,
      stageTouched: {},
    };

    // Set it as active
    getState().setActiveScenario(testScenario);

    // Wait for activeScenario to be set
    await waitFor(() => {
      expect(getState().activeScenario?.id).toBe("test-scenario-1");
    });

    // Now manually edit the name to "Test Scenario" - this marks it as manually edited
    // and prevents auto-renaming
    getState().updateScenarioField("name", "Test Scenario");

    await waitFor(() => {
      expect(getState().activeScenario?.name).toBe("Test Scenario");
    });

    // Set selectedPortfolioName
    getState().setSelectedPortfolioName("Test Portfolio");

    // Verify it's set
    await waitFor(() => {
      expect(getState().selectedPortfolioName).toBe("Test Portfolio");
    });

    // Clone the scenario
    getState().cloneCurrentScenario();

    // Assert: selectedPortfolioName is null
    await waitFor(() => {
      expect(getState().selectedPortfolioName).toBeNull();
    });

    // Assert: clone uses clone naming pattern
    await waitFor(() => {
      expect(getState().activeScenario?.name).toBe("Test Scenario (copy)");
    });
  });

  /**
   * Task 2.1-2.4: AC-3 - updateScenarioField("portfolioName", ...) clears manual-edit lock
   *
   * Given: A scenario with manually edited name "Custom Name"
   * When: User calls updateScenarioField("portfolioName", "Portfolio B")
   * Then: Scenario ID is removed from manuallyEditedScenarioNames and name updates
   */
  it("AC-3: updateScenarioField('portfolioName') clears manual-edit lock and triggers rename", async () => {
    const user = userEvent.setup();
    const { getState } = renderAppWithStateAccess();

    // Auth and wait for app to initialize
    await user.type(screen.getByPlaceholderText(/password/i), "secret");
    await user.click(screen.getByRole("button", { name: /enter/i }));

    await waitFor(() => {
      expect(getState().isAuthenticated).toBe(true);
    });

    // Create a test scenario with portfolioName
    const testScenario: WorkspaceScenario = {
      id: "test-scenario-portfolio",
      name: "Portfolio A (FR Synthetic 2024)",
      version: "1.0",
      status: "draft",
      isBaseline: false,
      baselineRef: null,
      portfolioName: "Portfolio A",
      populationIds: ["fr-synthetic-2024"],
      engineConfig: {
        startYear: 2025,
        endYear: 2030,
        seed: 42,
        investmentDecisionsEnabled: null,
        logitModel: null,
        discountRate: 0.03,
        tasteParameters: null,
        calibrationState: "not_configured",
      },
      policyType: "carbon-tax",
      lastRunId: null,
      stageTouched: {},
    };

    getState().setActiveScenario(testScenario);

    await waitFor(() => {
      expect(getState().activeScenario?.id).toBe("test-scenario-portfolio");
    });

    // Set selectedPopulationId for auto-name effect
    getState().setSelectedPopulationId("fr-synthetic-2024");

    await waitFor(() => {
      expect(getState().selectedPopulationId).toBe("fr-synthetic-2024");
    });

    // Manually edit the name - this marks it as manually edited
    getState().updateScenarioField("name", "Custom Name");

    await waitFor(() => {
      expect(getState().activeScenario?.name).toBe("Custom Name");
    });

    // Verify scenario ID is in manuallyEditedScenarioNames
    // We need to access the state's manuallyEditedScenarioNames set
    // This is private to AppContext, so we verify by checking that auto-rename was prevented

    // Now change portfolioName via updateScenarioField
    // This should clear the manual-edit lock and trigger a rename
    getState().updateScenarioField("portfolioName", "Portfolio B");

    // Also set selectedPortfolioName (UI state) which is what the auto-name effect uses
    getState().setSelectedPortfolioName("Portfolio B");

    // Assert: Name is updated to the new auto-suggestion
    await waitFor(() => {
      // The auto-name effect should now run and rename based on new portfolio
      expect(getState().activeScenario?.name).toBe("Portfolio B (FR Synthetic 2024)");
    });
  });

  /**
   * Task 2.4: AC-3 regression - updateScenarioField("populationIds", ...) preserves manual-edit lock
   *
   * Given: A scenario with manually edited name "Custom Name"
   * When: User calls updateScenarioField("populationIds", ["new-pop"])
   * Then: Name stays "Custom Name" (lock NOT cleared)
   */
  it("AC-3 (regression): updateScenarioField('populationIds') preserves manual-edit lock", async () => {
    const user = userEvent.setup();
    const { getState } = renderAppWithStateAccess();

    // Auth and wait for app to initialize
    await user.type(screen.getByPlaceholderText(/password/i), "secret");
    await user.click(screen.getByRole("button", { name: /enter/i }));

    await waitFor(() => {
      expect(getState().isAuthenticated).toBe(true);
    });

    // Create a test scenario
    const testScenario: WorkspaceScenario = {
      id: "test-scenario-population",
      name: "Untitled (FR Synthetic 2024)",
      version: "1.0",
      status: "draft",
      isBaseline: false,
      baselineRef: null,
      portfolioName: null,
      populationIds: ["fr-synthetic-2024"],
      engineConfig: {
        startYear: 2025,
        endYear: 2030,
        seed: 42,
        investmentDecisionsEnabled: null,
        logitModel: null,
        discountRate: 0.03,
        tasteParameters: null,
        calibrationState: "not_configured",
      },
      policyType: "carbon-tax",
      lastRunId: null,
      stageTouched: {},
    };

    getState().setActiveScenario(testScenario);

    await waitFor(() => {
      expect(getState().activeScenario?.id).toBe("test-scenario-population");
    });

    // Set selectedPopulationId for auto-name effect
    getState().setSelectedPopulationId("fr-synthetic-2024");

    await waitFor(() => {
      expect(getState().selectedPopulationId).toBe("fr-synthetic-2024");
    });

    // Manually edit the name - this marks it as manually edited
    getState().updateScenarioField("name", "Custom Name");

    await waitFor(() => {
      expect(getState().activeScenario?.name).toBe("Custom Name");
    });

    // Change populationIds via updateScenarioField
    // This should NOT clear the manual-edit lock
    getState().updateScenarioField("populationIds", ["fr-household-2023"]);

    await waitFor(() => {
      expect(getState().activeScenario?.populationIds).toEqual(["fr-household-2023"]);
    });

    // Also need to change the selectedPopulationId to trigger auto-name effect
    getState().setSelectedPopulationId("fr-household-2023");

    // Wait a bit to ensure auto-name effect had time to run
    await waitFor(() => {
      // The name should stay "Custom Name" because the manual-edit lock is preserved
      expect(getState().activeScenario?.name).toBe("Custom Name");
    });
  });

  /**
   * Task 3.1-3.5: AC-4 - Restored scenario with empty populationIds keeps its name
   *
   * Given: A restored scenario with populationIds: [] and name "My Scenario"
   * When: The default-selection effect later sets selectedPopulationId
   * Then: The scenario name stays "My Scenario" (not auto-renamed)
   */
  it("AC-4: Restored scenario with empty populationIds keeps its name after default selection", async () => {
    const user = userEvent.setup();
    const { getState } = renderAppWithStateAccess();

    // Auth and wait for app to initialize
    await user.type(screen.getByPlaceholderText(/password/i), "secret");
    await user.click(screen.getByRole("button", { name: /enter/i }));

    await waitFor(() => {
      expect(getState().isAuthenticated).toBe(true);
    });

    // Create a scenario with empty populationIds
    const testScenario: WorkspaceScenario = {
      id: "test-scenario-empty-pop",
      name: "My Scenario",
      version: "1.0",
      status: "draft",
      isBaseline: false,
      baselineRef: null,
      portfolioName: null,
      populationIds: [], // Empty - user hasn't picked a population yet
      engineConfig: {
        startYear: 2025,
        endYear: 2030,
        seed: 42,
        investmentDecisionsEnabled: null,
        logitModel: null,
        discountRate: 0.03,
        tasteParameters: null,
        calibrationState: "not_configured",
      },
      policyType: "carbon-tax",
      lastRunId: null,
      stageTouched: {},
    };

    // Set it as active (simulating restore)
    getState().setActiveScenario(testScenario);

    await waitFor(() => {
      expect(getState().activeScenario?.id).toBe("test-scenario-empty-pop");
      expect(getState().activeScenario?.name).toBe("My Scenario");
    });

    // The default-selection effect will set selectedPopulationId to populations[0].id
    // This should NOT trigger a rename because it's an implicit selection
    await waitFor(() => {
      // Verify default selection happened
      expect(getState().selectedPopulationId).toBe("fr-synthetic-2024");
    });

    // Assert: Name is still "My Scenario" (not auto-renamed)
    expect(getState().activeScenario?.name).toBe("My Scenario");
  });

  /**
   * Task 3.5: AC-4 - Explicit population change after restore DOES trigger rename
   *
   * Given: A restored scenario with empty populationIds and name "My Scenario"
   * When: User explicitly changes population to "Population B"
   * Then: Name updates to include "Population B"
   */
  it("AC-4: Explicit population change after restore DOES trigger rename", async () => {
    const user = userEvent.setup();
    const { getState } = renderAppWithStateAccess();

    // Auth and wait for app to initialize
    await user.type(screen.getByPlaceholderText(/password/i), "secret");
    await user.click(screen.getByRole("button", { name: /enter/i }));

    await waitFor(() => {
      expect(getState().isAuthenticated).toBe(true);
    });

    // Create a scenario with empty populationIds
    const testScenario: WorkspaceScenario = {
      id: "test-scenario-explicit-pop",
      name: "My Scenario",
      version: "1.0",
      status: "draft",
      isBaseline: false,
      baselineRef: null,
      portfolioName: null,
      populationIds: [], // Empty - user hasn't picked a population yet
      engineConfig: {
        startYear: 2025,
        endYear: 2030,
        seed: 42,
        investmentDecisionsEnabled: null,
        logitModel: null,
        discountRate: 0.03,
        tasteParameters: null,
        calibrationState: "not_configured",
      },
      policyType: "carbon-tax",
      lastRunId: null,
      stageTouched: {},
    };

    // Set it as active (simulating restore)
    getState().setActiveScenario(testScenario);

    await waitFor(() => {
      expect(getState().activeScenario?.id).toBe("test-scenario-explicit-pop");
    });

    // Wait for default selection to complete
    await waitFor(() => {
      expect(getState().selectedPopulationId).toBe("fr-synthetic-2024");
    });

    // Verify name is still "My Scenario" after default selection
    expect(getState().activeScenario?.name).toBe("My Scenario");

    // Now user explicitly changes population to "fr-household-2023"
    // This should trigger a rename
    getState().setSelectedPopulationId("fr-household-2023");

    // Assert: Name is updated to include the new population
    await waitFor(() => {
      expect(getState().activeScenario?.name).toBe("Untitled (FR Household 2023)");
    });
  });
});
