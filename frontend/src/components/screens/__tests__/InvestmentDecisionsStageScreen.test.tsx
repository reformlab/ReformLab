// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Unit tests for InvestmentDecisionsStageScreen — Story 26.2.
 *
 * Tests:
 * - AC-1: Disabled state shows enable toggle and Continue to Scenario button
 * - AC-2: Enabled state shows full InvestmentDecisionsWizard
 * - AC-7: Navigation buttons work correctly, wizard state resets appropriately
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

// ============================================================================
// Mocks
// ============================================================================

vi.mock("@/contexts/AppContext", () => ({
  useAppState: vi.fn(),
}));

// ============================================================================
// Imports after mocks
// ============================================================================

import { useAppState } from "@/contexts/AppContext";
import { InvestmentDecisionsStageScreen } from "@/components/screens/InvestmentDecisionsStageScreen";
import type { WorkspaceScenario } from "@/types/workspace";
import { DEFAULT_TASTE_PARAMETERS } from "@/types/workspace";

// ============================================================================
// Helpers
// ============================================================================

function makeScenario(overrides: Partial<WorkspaceScenario> = {}): WorkspaceScenario {
  return {
    id: "test-id",
    name: "Test Scenario",
    version: "1.0",
    status: "draft",
    isBaseline: false,
    baselineRef: null,
    portfolioName: "Test Portfolio",
    populationIds: ["fr-synthetic-2024"],
    engineConfig: {
      startYear: 2025,
      endYear: 2030,
      seed: null,
      investmentDecisionsEnabled: false,
      logitModel: null,
      discountRate: 0.03,
      tasteParameters: DEFAULT_TASTE_PARAMETERS,
      calibrationState: "not_configured",
    },
    policyType: "carbon-tax",
    lastRunId: null,
    ...overrides,
  };
}

const mockUpdateScenarioField = vi.fn();
const mockNavigateTo = vi.fn();

function makeDefaultAppState(overrides: Partial<ReturnType<typeof useAppState>> = {}) {
  return {
    activeScenario: makeScenario(),
    updateScenarioField: mockUpdateScenarioField,
    navigateTo: mockNavigateTo,
    // Misc required
    isAuthenticated: true,
    authLoading: false,
    authenticate: vi.fn(),
    logout: vi.fn(),
    activeStage: "investment-decisions" as const,
    activeSubView: null,
    setActiveScenario: vi.fn(),
    savedScenarios: [],
    loadSavedScenario: vi.fn(),
    resetToDemo: vi.fn(),
    templates: [],
    parameters: [],
    parameterValues: {},
    setParameterValue: vi.fn(),
    scenarios: [],
    decileData: [],
    selectedTemplateId: "",
    selectTemplate: vi.fn(),
    selectedScenarioId: "",
    setSelectedScenarioId: vi.fn(),
    startRun: vi.fn(),
    runLoading: false,
    runResult: null,
    cloneScenario: vi.fn(),
    deleteScenario: vi.fn(),
    populations: [],
    populationsLoading: false,
    selectedPopulationId: "",
    templatesLoading: false,
    parametersLoading: false,
    refetchPopulations: vi.fn(),
    refetchTemplates: vi.fn(),
    dataFusionSources: {},
    dataFusionMethods: [],
    dataFusionResult: null,
    setDataFusionResult: vi.fn(),
    dataFusionSourcesLoading: false,
    portfolios: [],
    portfoliosLoading: false,
    refetchPortfolios: vi.fn(),
    results: [],
    resultsLoading: false,
    refetchResults: vi.fn(),
    selectedPortfolioName: null,
    setSelectedPortfolioName: vi.fn(),
    selectedComparisonRunIds: [],
    setSelectedComparisonRunIds: vi.fn(),
    apiConnected: false,
    createNewScenario: vi.fn(),
    cloneCurrentScenario: vi.fn(),
    saveCurrentScenario: vi.fn(),
    ...overrides,
  };
}

function renderScreen(overrides: Partial<ReturnType<typeof useAppState>> = {}) {
  vi.mocked(useAppState).mockReturnValue(
    makeDefaultAppState(overrides) as ReturnType<typeof useAppState>,
  );
  return render(<InvestmentDecisionsStageScreen />);
}

// ============================================================================
// Setup
// ============================================================================

beforeAll(() => {
  // No ResizeObserver needed for this component
});

beforeEach(() => {
  vi.clearAllMocks();
});

// ============================================================================
// Tests
// ============================================================================

describe("InvestmentDecisionsStageScreen — Story 26.2", () => {
  describe("Null state (no active scenario)", () => {
    it("renders 'No active scenario' message when activeScenario is null", () => {
      renderScreen({ activeScenario: null });
      expect(screen.getByText(/no active scenario/i)).toBeInTheDocument();
    });

    it("renders 'Go to Stage 1 to create a scenario' button when activeScenario is null", () => {
      renderScreen({ activeScenario: null });
      expect(screen.getByRole("button", { name: /go to stage 1 to create a scenario/i })).toBeInTheDocument();
    });

    it("'Go to Stage 1' button navigates to policies stage", async () => {
      const user = userEvent.setup();
      renderScreen({ activeScenario: null });
      await user.click(screen.getByRole("button", { name: /go to stage 1 to create a scenario/i }));
      expect(mockNavigateTo).toHaveBeenCalledWith("policies");
    });
  });

  describe("AC-1: Disabled state", () => {
    it("renders 'Investment Decisions' heading in toolbar", () => {
      renderScreen();
      expect(screen.getByRole("heading", { level: 1, name: "Investment Decisions" })).toBeInTheDocument();
    });

    it("renders 'Enable investment decisions' toggle", () => {
      renderScreen();
      expect(screen.getByRole("checkbox", { name: /toggle investment decisions/i })).toBeInTheDocument();
    });

    it("shows toggle as unchecked when investmentDecisionsEnabled is false", () => {
      renderScreen({
        activeScenario: makeScenario({
          engineConfig: {
            startYear: 2025,
            endYear: 2030,
            seed: null,
            investmentDecisionsEnabled: false,
            logitModel: null,
            discountRate: 0.03,
            tasteParameters: DEFAULT_TASTE_PARAMETERS,
            calibrationState: "not_configured",
          },
        }),
      });
      const toggle = screen.getByRole("checkbox", { name: /toggle investment decisions/i });
      expect(toggle).not.toBeChecked();
    });

    it("shows explanatory copy about investment decisions being optional", () => {
      renderScreen();
      expect(screen.getByText(/investment decisions model household technology adoption choices/i)).toBeInTheDocument();
      expect(screen.getByText(/this is an optional advanced feature/i)).toBeInTheDocument();
    });

    it("renders 'Continue to Scenario' button", () => {
      renderScreen();
      expect(screen.getByRole("button", { name: /continue to scenario/i })).toBeInTheDocument();
    });

    it("renders 'Skip to Scenario' button in disabled state section", () => {
      renderScreen();
      expect(screen.getByRole("button", { name: /skip to scenario/i })).toBeInTheDocument();
    });

    it("'Continue to Scenario' button navigates to scenario stage", async () => {
      const user = userEvent.setup();
      renderScreen();
      await user.click(screen.getByRole("button", { name: /continue to scenario/i }));
      expect(mockNavigateTo).toHaveBeenCalledWith("scenario");
    });

    it("'Skip to Scenario' button navigates to scenario stage", async () => {
      const user = userEvent.setup();
      renderScreen();
      await user.click(screen.getByRole("button", { name: /skip to scenario/i }));
      expect(mockNavigateTo).toHaveBeenCalledWith("scenario");
    });

    it("enable toggle calls updateScenarioField with enabled state and default model", async () => {
      const user = userEvent.setup();
      renderScreen();
      const toggle = screen.getByRole("checkbox", { name: /toggle investment decisions/i });
      await user.click(toggle);
      await waitFor(() => {
        expect(mockUpdateScenarioField).toHaveBeenCalledWith(
          "engineConfig",
          expect.objectContaining({
            investmentDecisionsEnabled: true,
            logitModel: "multinomial_logit",
          }),
        );
      });
    });
  });

  describe("AC-2: Enabled state (wizard)", () => {
    it("renders InvestmentDecisionsWizard when investmentDecisionsEnabled is true", () => {
      renderScreen({
        activeScenario: makeScenario({
          engineConfig: {
            startYear: 2025,
            endYear: 2030,
            seed: null,
            investmentDecisionsEnabled: true,
            logitModel: "multinomial_logit",
            discountRate: 0.03,
            tasteParameters: DEFAULT_TASTE_PARAMETERS,
            calibrationState: "not_configured",
          },
        }),
      });
      // Wizard renders - when enabled, it auto-advances to Model step
      expect(screen.getByText("Choose Logit Model")).toBeInTheDocument();
    });

    it("wizard shows 'Choose Logit Model' step when enabled without model", () => {
      renderScreen({
        activeScenario: makeScenario({
          engineConfig: {
            startYear: 2025,
            endYear: 2030,
            seed: null,
            investmentDecisionsEnabled: true,
            logitModel: null,
            discountRate: 0.03,
            tasteParameters: DEFAULT_TASTE_PARAMETERS,
            calibrationState: "not_configured",
          },
        }),
      });
      // When enabled without a model, wizard shows Model step
      expect(screen.getByText("Choose Logit Model")).toBeInTheDocument();
    });
  });

  describe("AC-7: Navigation buttons", () => {
    it("'Back to Population' button navigates to population stage", async () => {
      const user = userEvent.setup();
      renderScreen();
      await user.click(screen.getByRole("button", { name: /back to population/i }));
      expect(mockNavigateTo).toHaveBeenCalledWith("population");
    });

    it("'Continue to Scenario' button navigates to scenario stage when enabled", async () => {
      const user = userEvent.setup();
      renderScreen({
        activeScenario: makeScenario({
          engineConfig: {
            startYear: 2025,
            endYear: 2030,
            seed: null,
            investmentDecisionsEnabled: true,
            logitModel: "multinomial_logit",
            discountRate: 0.03,
            tasteParameters: DEFAULT_TASTE_PARAMETERS,
            calibrationState: "not_configured",
          },
        }),
      });
      await user.click(screen.getByRole("button", { name: /continue to scenario/i }));
      expect(mockNavigateTo).toHaveBeenCalledWith("scenario");
    });

    it("navigation buttons are visible in both disabled and enabled states", () => {
      // Disabled state
      const { rerender } = renderScreen();
      expect(screen.getByRole("button", { name: /back to population/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /continue to scenario/i })).toBeInTheDocument();

      // Enabled state
      vi.mocked(useAppState).mockReturnValue(
        makeDefaultAppState({
          activeScenario: makeScenario({
            engineConfig: {
              startYear: 2025,
              endYear: 2030,
              seed: null,
              investmentDecisionsEnabled: true,
              logitModel: "multinomial_logit",
              discountRate: 0.03,
              tasteParameters: DEFAULT_TASTE_PARAMETERS,
              calibrationState: "not_configured",
            },
          }),
        }) as ReturnType<typeof useAppState>,
      );
      rerender(<InvestmentDecisionsStageScreen />);
      expect(screen.getByRole("button", { name: /back to population/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /continue to scenario/i })).toBeInTheDocument();
    });
  });

  describe("Wizard state recovery (AC-7)", () => {
    // The InvestmentDecisionsWizard component has its own useEffect that handles
    // step recovery based on engineConfig state. This test verifies that
    // when the component renders with different states, the wizard shows
    // appropriate content (the wizard handles internal state recovery).

    it("shows Enable step (disabled state summary) when investmentDecisionsEnabled is false", () => {
      renderScreen({
        activeScenario: makeScenario({
          engineConfig: {
            startYear: 2025,
            endYear: 2030,
            seed: null,
            investmentDecisionsEnabled: false,
            logitModel: null,
            discountRate: 0.03,
            tasteParameters: DEFAULT_TASTE_PARAMETERS,
            calibrationState: "not_configured",
          },
        }),
      });
      // Should show disabled state summary, not wizard steps
      expect(screen.getByText(/enable investment decisions/i)).toBeInTheDocument();
      expect(screen.getByText(/this is an optional advanced feature/i)).toBeInTheDocument();
    });

    it("shows wizard Model step when investmentDecisionsEnabled is true (with or without model)", () => {
      renderScreen({
        activeScenario: makeScenario({
          engineConfig: {
            startYear: 2025,
            endYear: 2030,
            seed: null,
            investmentDecisionsEnabled: true,
            logitModel: "multinomial_logit",
            discountRate: 0.03,
            tasteParameters: DEFAULT_TASTE_PARAMETERS,
            calibrationState: "not_configured",
          },
        }),
      });
      // When enabled, wizard auto-advances to Model step (step 1)
      expect(screen.getByText("Choose Logit Model")).toBeInTheDocument();
    });
  });

  describe("What are investment decisions? section", () => {
    it("shows explanatory content in disabled state", () => {
      renderScreen();
      expect(screen.getByText(/what are investment decisions\?/i)).toBeInTheDocument();
      expect(screen.getByText(/discrete choice models \(logit\)/i)).toBeInTheDocument();
    });

    it("does not show explanatory content in enabled state (wizard takes full space)", () => {
      renderScreen({
        activeScenario: makeScenario({
          engineConfig: {
            startYear: 2025,
            endYear: 2030,
            seed: null,
            investmentDecisionsEnabled: true,
            logitModel: "multinomial_logit",
            discountRate: 0.03,
            tasteParameters: DEFAULT_TASTE_PARAMETERS,
            calibrationState: "not_configured",
          },
        }),
      });
      expect(screen.queryByText(/what are investment decisions\?/i)).not.toBeInTheDocument();
    });
  });
});
