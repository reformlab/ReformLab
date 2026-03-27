// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Unit tests for EngineStageScreen — Story 20.5.
 *
 * Tests:
 * - AC-1: Engine configuration form (time horizon, population, seed, investment decisions, discount rate)
 * - AC-2: Scenario save and clone toolbar actions
 * - AC-3: Cross-stage validation gate displayed in right panel
 * - AC-4: Run button state depends on validation
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
import { EngineStageScreen } from "@/components/screens/EngineStageScreen";
import type { WorkspaceScenario } from "@/types/workspace";
import type { GenerationResult } from "@/api/types";

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
    populations: [{ id: "fr-synthetic-2024", name: "FR 2024", households: 100000, source: "INSEE", year: 2024 }],
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
    activeStage: "engine" as const,
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
  return render(<EngineStageScreen />);
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

describe("EngineStageScreen — Story 20.5", () => {
  describe("AC-1: Engine configuration form", () => {
    it("renders 'Engine Configuration' heading", () => {
      renderScreen();
      expect(screen.getByRole("heading", { name: /engine configuration/i })).toBeInTheDocument();
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
          engineConfig: { startYear: 2030, endYear: 2025, seed: null, investmentDecisionsEnabled: false, logitModel: null, discountRate: 0.03 },
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

    it("population dropdown lists all populations from AppContext", () => {
      renderScreen();
      expect(screen.getByRole("option", { name: /fr 2024/i })).toBeInTheDocument();
    });

    it("selecting population calls updateScenarioField and setSelectedPopulationId", async () => {
      renderScreen({
        populations: [
          { id: "fr-synthetic-2024", name: "FR 2024", households: 100000, source: "INSEE", year: 2024 },
          { id: "eu-silc-2023", name: "EU-SILC 2023", households: 80000, source: "Eurostat", year: 2023 },
        ],
      });
      const select = screen.getByRole("combobox", { name: /primary population/i });
      fireEvent.change(select, { target: { value: "eu-silc-2023" } });
      expect(mockUpdateScenarioField).toHaveBeenCalledWith("populationIds", ["eu-silc-2023"]);
      expect(mockSetSelectedPopulationId).toHaveBeenCalledWith("eu-silc-2023");
    });

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

    it("investment decisions toggle shows accordion when clicked", async () => {
      renderScreen();
      // The Switch component renders as a checkbox input with the aria-label
      const toggle = screen.getByRole("checkbox", { name: /toggle investment decisions/i });
      fireEvent.click(toggle);
      await waitFor(() => {
        expect(mockUpdateScenarioField).toHaveBeenCalledWith(
          "engineConfig",
          expect.objectContaining({ investmentDecisionsEnabled: true }),
        );
      });
    });

    it("when accordion visible, logit model dropdown renders with 3 options", async () => {
      renderScreen({
        activeScenario: makeScenario({
          engineConfig: { startYear: 2025, endYear: 2030, seed: null, investmentDecisionsEnabled: true, logitModel: "multinomial_logit", discountRate: 0.03 },
        }),
      });
      await waitFor(() => {
        expect(screen.getByRole("combobox", { name: /logit model/i })).toBeInTheDocument();
      });
      expect(screen.getByRole("option", { name: /multinomial logit/i })).toBeInTheDocument();
      expect(screen.getByRole("option", { name: /nested logit/i })).toBeInTheDocument();
      expect(screen.getByRole("option", { name: /mixed logit/i })).toBeInTheDocument();
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
      // Validation section heading
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
