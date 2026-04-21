// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Unit tests for ScenarioStageScreen — Story 20.5, Story 26.3.
 *
 * Tests:
 * - AC-1: Scenario configuration form (time horizon, seed, discount rate)
 * - AC-2: Scenario save and clone toolbar actions
 * - AC-3: Cross-stage validation gate displayed in right panel
 * - AC-4: Run button state depends on validation
 * - Story 26.2 — AC-3: Investment decisions moved to dedicated Stage 3, summary shown here.
 * - Story 26.3 — AC-1: Inherited primary population displayed as read-only context.
 * - Story 26.3 — AC-2, AC-3: Runtime summary shows Live OpenFisca with optional Replay badge.
 * - Story 26.3 — AC-5: Validation messages include clickable stage-fix links.
 * - Story 26.3 — AC-7: Renamed from EngineStageScreen to ScenarioStageScreen.
 */

import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { setupResizeObserver } from "@/__tests__/workflows/helpers";

// ============================================================================
// Mocks
// ============================================================================

vi.mock("@/contexts/AppContext", () => ({
  useAppState: vi.fn(),
}));

vi.mock("@/api/runs", () => ({
  checkMemory: vi.fn().mockResolvedValue({
    should_warn: false,
    estimated_gb: 2.0,
    available_gb: 16.0,
    message: "",
  }),
}));

vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
  },
}));

// ============================================================================
// Imports after mocks
// ============================================================================

import { useAppState } from "@/contexts/AppContext";
import { ScenarioStageScreen } from "@/components/screens/ScenarioStageScreen";
import type { WorkspaceScenario } from "@/types/workspace";
import type { GenerationResult } from "@/api/types";
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
const mockSaveCurrentScenario = vi.fn();
const mockCloneCurrentScenario = vi.fn();
const mockSetSelectedPopulationId = vi.fn();
const mockCreateNewScenario = vi.fn();

function makeDefaultAppState(overrides: Partial<ReturnType<typeof useAppState>> = {}) {
  return {
    activeScenario: makeScenario(),
    populations: [
      {
        id: "fr-synthetic-2024",
        name: "FR 2024",
        households: 100000,
        source: "INSEE",
        year: 2024,
        origin: "built-in" as const,
        canonical_origin: "open-official" as const,
        access_mode: "bundled" as const,
        trust_status: "production-safe" as const,
        column_count: 10,
        created_date: null,
        is_synthetic: false,
      },
    ],
    dataFusionResult: null as GenerationResult | null,
    portfolios: [{ name: "Test Portfolio", description: "", version_id: "v1", policy_count: 1 }],
    updateScenarioField: mockUpdateScenarioField,
    navigateTo: mockNavigateTo,
    saveCurrentScenario: mockSaveCurrentScenario,
    cloneCurrentScenario: mockCloneCurrentScenario,
    setSelectedPopulationId: mockSetSelectedPopulationId,
    createNewScenario: mockCreateNewScenario,
    // Misc required
    isAuthenticated: true,
    authLoading: false,
    authenticate: vi.fn(),
    logout: vi.fn(),
    activeStage: "scenario" as const,
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
    selectedPopulationId: "",
    selectedTemplateId: "",
    selectTemplate: vi.fn(),
    selectedScenarioId: "",
    setSelectedScenarioId: vi.fn(),
    startRun: vi.fn(),
    runLoading: false,
    runResult: null,
    cloneScenario: vi.fn(),
    deleteScenario: vi.fn(),
    populationsLoading: false,
    templatesLoading: false,
    parametersLoading: false,
    refetchPopulations: vi.fn(),
    refetchTemplates: vi.fn(),
    dataFusionSources: {},
    dataFusionMethods: [],
    setDataFusionResult: vi.fn(),
    dataFusionSourcesLoading: false,
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
    ...overrides,
  };
}

function renderScreen(overrides: Partial<ReturnType<typeof useAppState>> = {}) {
  vi.mocked(useAppState).mockReturnValue(
    makeDefaultAppState(overrides) as ReturnType<typeof useAppState>,
  );
  return render(<ScenarioStageScreen />);
}

// ============================================================================
// Setup
// ============================================================================

beforeAll(() => {
  setupResizeObserver();
});

beforeEach(() => {
  vi.clearAllMocks();
});

// ============================================================================
// Tests
// ============================================================================

describe("ScenarioStageScreen — Story 20.5, Story 26.3", () => {
  describe("AC-1: Scenario configuration form", () => {
    it("renders 'Scenario Configuration' heading", () => {
      renderScreen();
      expect(screen.getByRole("heading", { name: /scenario configuration/i })).toBeInTheDocument();
    });

    it("renders time horizon inputs with values from activeScenario.engineConfig", () => {
      renderScreen();
      const startInput = screen.getByRole("spinbutton", { name: /start year/i });
      const endInput = screen.getByRole("spinbutton", { name: /end year/i });
      expect(startInput).toHaveValue(2025);
      expect(endInput).toHaveValue(2030);
    });

    it("shows 'N-year projection' label when endYear > startYear", () => {
      renderScreen();
      expect(screen.getByText(/5-year projection/i)).toBeInTheDocument();
    });

    it("shows 'End year must be after start year' error when startYear >= endYear", () => {
      renderScreen({
        activeScenario: makeScenario({
          engineConfig: {
            startYear: 2030,
            endYear: 2025,
            seed: null,
            investmentDecisionsEnabled: false,
            logitModel: null,
            discountRate: 0.03,
            tasteParameters: DEFAULT_TASTE_PARAMETERS,
            calibrationState: "not_configured",
          },
        }),
      });
      expect(screen.getByText(/end year must be after start year/i)).toBeInTheDocument();
    });

    it("start year input change calls updateScenarioField", () => {
      renderScreen();
      const input = screen.getByRole("spinbutton", { name: /start year/i });
      fireEvent.change(input, { target: { value: "2026" } });
      expect(mockUpdateScenarioField).toHaveBeenCalledWith(
        "engineConfig",
        expect.objectContaining({ startYear: 2026 }),
      );
    });

    it("end year input change calls updateScenarioField", () => {
      renderScreen();
      const input = screen.getByRole("spinbutton", { name: /end year/i });
      fireEvent.change(input, { target: { value: "2035" } });
      expect(mockUpdateScenarioField).toHaveBeenCalledWith(
        "engineConfig",
        expect.objectContaining({ endYear: 2035 }),
      );
    });
  });

  describe("Story 26.3 — AC-1: Inherited Primary Population", () => {
    it("renders inherited population section with population name", () => {
      renderScreen();
      expect(screen.getByText("Primary Population")).toBeInTheDocument();
      expect(screen.getByText("FR 2024")).toBeInTheDocument();
      expect(screen.getByText("Inherited from Stage 2")).toBeInTheDocument();
    });

    it("shows origin badge for built-in population", () => {
      renderScreen();
      expect(screen.getByText("[Built-in]")).toBeInTheDocument();
    });

    it("shows household count", () => {
      renderScreen();
      expect(screen.getByText(/100,000 households/i)).toBeInTheDocument();
    });

    it("'Change in Stage 2' link navigates to population stage", async () => {
      const user = userEvent.setup();
      renderScreen();
      await user.click(screen.getByRole("button", { name: /change in stage 2/i }));
      expect(mockNavigateTo).toHaveBeenCalledWith("population");
    });

    it("shows 'No population selected' when primary population is null", () => {
      renderScreen({
        activeScenario: makeScenario({ populationIds: [] }),
      });
      const messages = screen.getAllByText(/no population selected/i);
      expect(messages.length).toBeGreaterThanOrEqual(1);
      expect(screen.getByRole("button", { name: /go to stage 2 to select a population/i })).toBeInTheDocument();
    });

    it("shows data fusion result as 'Generated' origin", () => {
      renderScreen({
        activeScenario: makeScenario({ populationIds: ["data-fusion-result"] }),
        dataFusionResult: {
          summary: { record_count: 50000, households: 50000, persons: 120000, columns: 15 },
          population_id: "data-fusion-result",
          sources: ["insee", "eurostat"],
          method: "conditional_sampling",
        } as GenerationResult,
      });
      expect(screen.getByText("Fused Population")).toBeInTheDocument();
      expect(screen.getByText("[Generated]")).toBeInTheDocument();
      expect(screen.getByText(/50,000 households/i)).toBeInTheDocument();
    });
  });

  describe("Story 26.3 — AC-2, AC-3: Runtime Summary", () => {
    it("shows 'Runtime' section heading", () => {
      renderScreen();
      // Runtime heading appears in the left panel
      const runtimeHeadings = screen.getAllByText("Runtime");
      expect(runtimeHeadings.length).toBeGreaterThanOrEqual(1);
    });

    it("shows 'Live OpenFisca' badge (always shown)", () => {
      renderScreen();
      const liveBadges = screen.getAllByText("Live OpenFisca");
      expect(liveBadges.length).toBeGreaterThanOrEqual(1);
    });

    it("does not show 'Replay' badge when lastRunRuntimeMode is null", () => {
      renderScreen();
      // Live OpenFisca badge should be present (in both Runtime section and RunSummaryPanel), but Replay badge should not
      const liveBadges = screen.getAllByText("Live OpenFisca");
      expect(liveBadges.length).toBeGreaterThanOrEqual(1);
      expect(screen.queryByText("Replay")).not.toBeInTheDocument();
    });

    it("shows 'Replay' badge when lastRunId exists AND lastRunRuntimeMode is 'replay'", () => {
      renderScreen({
        activeScenario: makeScenario({ lastRunId: "run-123", lastRunRuntimeMode: "replay" }),
      });
      // Replay badge should appear in both Runtime section and RunSummaryPanel
      const replayBadges = screen.getAllByText("Replay");
      expect(replayBadges.length).toBeGreaterThanOrEqual(1);
    });

    it("shows runtime helper text", () => {
      renderScreen();
      expect(screen.getByText(/live execution uses openfisca engine/i)).toBeInTheDocument();
    });
  });

  describe("Sensitivity Population (Optional)", () => {
    it("'+ Add population for sensitivity' appears and shows second dropdown on click", async () => {
      const user = userEvent.setup();
      renderScreen();
      const addBtn = screen.getByText(/add population for sensitivity/i);
      expect(addBtn).toBeInTheDocument();
      await user.click(addBtn);
      await waitFor(() => {
        expect(screen.getByRole("combobox", { name: /secondary population/i })).toBeInTheDocument();
      });
    });

    it("shows 'Sensitivity Population (Optional)' heading", () => {
      renderScreen();
      expect(screen.getByText("Sensitivity Population (Optional)")).toBeInTheDocument();
    });
  });

  describe("Story 26.2: Investment decisions summary", () => {
    it("investment decisions summary shows 'Disabled' when investmentDecisionsEnabled is false", () => {
      renderScreen();
      const heading = screen.getByText("Investment Decisions");
      const parent = heading.closest("section");
      expect(parent).toHaveTextContent("Disabled");
    });

    it("investment decisions summary shows model name when enabled", () => {
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
      expect(screen.getByText(/enabled — Multinomial Logit/i)).toBeInTheDocument();
    });

    it("investment decisions summary shows 'no model selected' when enabled but no model", () => {
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
      expect(screen.getByText(/enabled — no model selected/i)).toBeInTheDocument();
    });

    it("'Configure in Stage 3' link navigates to investment-decisions stage", async () => {
      const user = userEvent.setup();
      renderScreen();
      await user.click(screen.getByRole("button", { name: /configure in stage 3/i }));
      expect(mockNavigateTo).toHaveBeenCalledWith("investment-decisions");
    });
  });

  describe("AC-2: Scenario save and clone", () => {
    it("Save Scenario button calls saveCurrentScenario", async () => {
      const user = userEvent.setup();
      renderScreen();
      await user.click(screen.getByRole("button", { name: /save scenario/i }));
      expect(mockSaveCurrentScenario).toHaveBeenCalledTimes(1);
    });

    it("Clone Scenario button calls cloneCurrentScenario", async () => {
      const user = userEvent.setup();
      renderScreen();
      await user.click(screen.getByRole("button", { name: /clone scenario/i }));
      expect(mockCloneCurrentScenario).toHaveBeenCalledTimes(1);
    });

    it("Scenario name input shows activeScenario.name", () => {
      renderScreen();
      const nameInput = screen.getByRole("textbox", { name: /scenario name/i });
      expect(nameInput).toHaveValue("Test Scenario");
    });

    it("Scenario name input update on blur calls updateScenarioField", async () => {
      const user = userEvent.setup();
      renderScreen();
      const nameInput = screen.getByRole("textbox", { name: /scenario name/i });
      await user.clear(nameInput);
      await user.type(nameInput, "My New Name");
      fireEvent.blur(nameInput);
      expect(mockUpdateScenarioField).toHaveBeenCalledWith("name", "My New Name");
    });
  });

  describe("AC-3: Cross-stage validation gate", () => {
    it("renders ValidationGate (checklist) in right panel", () => {
      renderScreen();
      expect(screen.getByText("Validation")).toBeInTheDocument();
    });

    it("shows Run Simulation button", () => {
      renderScreen();
      expect(screen.getByRole("button", { name: /run simulation/i })).toBeInTheDocument();
    });

    it("Run button is disabled when portfolioName is null", () => {
      renderScreen({
        activeScenario: makeScenario({ portfolioName: null }),
      });
      expect(screen.getByRole("button", { name: /run simulation/i })).toBeDisabled();
    });

    it("Story 26.3 — AC-5: validation message includes clickable 'Stage 1' link", () => {
      renderScreen({
        activeScenario: makeScenario({ portfolioName: null }),
      });
      // Should show validation error with clickable stage link
      expect(screen.getByText(/no portfolio selected/i)).toBeInTheDocument();
      // Verify the stage link button is rendered
      expect(screen.getByRole("button", { name: /stage 1/i })).toBeInTheDocument();
    });

    it("Story 26.3 — AC-5: clicking stage link in validation message calls navigateTo", async () => {
      const user = userEvent.setup();
      renderScreen({
        activeScenario: makeScenario({ portfolioName: null }),
      });
      // Click the Stage 1 link in the validation message
      await user.click(screen.getByRole("button", { name: /stage 1/i }));
      expect(mockNavigateTo).toHaveBeenCalledWith("policies");
    });
  });

  describe("Null state", () => {
    it("renders 'No active scenario' message when activeScenario is null", () => {
      renderScreen({ activeScenario: null });
      expect(screen.getByText(/no active scenario/i)).toBeInTheDocument();
    });

    it("renders 'Start a new scenario' button when activeScenario is null", () => {
      renderScreen({ activeScenario: null });
      expect(screen.getByRole("button", { name: /start a new scenario/i })).toBeInTheDocument();
    });

    it("'Start a new scenario' calls createNewScenario()", async () => {
      const user = userEvent.setup();
      renderScreen({ activeScenario: null });
      await user.click(screen.getByRole("button", { name: /start a new scenario/i }));
      expect(mockCreateNewScenario).toHaveBeenCalledTimes(1);
    });
  });
});
