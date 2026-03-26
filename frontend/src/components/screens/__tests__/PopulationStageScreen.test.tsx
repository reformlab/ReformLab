// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Unit tests for PopulationStageScreen — Story 20.4.
 *
 * Tests:
 * - AC-1: Default view renders PopulationLibraryScreen with population cards
 * - AC-2: Quick Preview opens on Preview button click and shows rows
 * - AC-2: Quick Preview closes on backdrop click and Escape
 * - AC-3: Data Explorer opens on Explore button click with three tabs
 * - AC-4: Upload overlay opens and shows drag-and-drop zone
 * - AC-5: Select button updates activeScenario.populationIds and selectedPopulationId
 * - AC-5: Delete clears selection when deleting selected population
 * - AC-6: Population cards show correct origin tags
 */

import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { setupResizeObserver } from "@/__tests__/workflows/helpers";

// ============================================================================
// Mocks
// ============================================================================

vi.mock("@/contexts/AppContext", () => ({
  useAppState: vi.fn(),
}));

vi.mock("@/api/populations", () => ({
  listPopulations: vi.fn(),
  getPopulationPreview: vi.fn(),
  getPopulationProfile: vi.fn(),
  getPopulationCrosstab: vi.fn(),
  uploadPopulation: vi.fn(),
  deletePopulation: vi.fn().mockResolvedValue(undefined),
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
import { PopulationStageScreen } from "@/components/screens/PopulationStageScreen";
import { PopulationExplorer } from "@/components/population/PopulationExplorer";
import { mockPopulations } from "@/data/mock-data";
import type { WorkspaceScenario } from "@/types/workspace";
import type { GenerationResult } from "@/api/types";

// ============================================================================
// Helpers
// ============================================================================

function makeScenario(overrides: Partial<WorkspaceScenario> = {}): WorkspaceScenario {
  return {
    id: "test-1",
    name: "Test Scenario",
    version: "1.0",
    status: "ready",
    isBaseline: false,
    baselineRef: null,
    portfolioName: null,
    populationIds: [],
    engineConfig: { startYear: 2025, endYear: 2030, seed: null, investmentDecisionsEnabled: false },
    policyType: null,
    lastRunId: null,
    ...overrides,
  };
}

function makeDefaultAppState(overrides: Partial<ReturnType<typeof useAppState>> = {}) {
  return {
    populations: mockPopulations.map((p) => ({ id: p.id, name: p.name, households: p.households, source: p.source, year: p.year })),
    populationsLoading: false,
    dataFusionSources: {},
    dataFusionMethods: [],
    dataFusionResult: null as GenerationResult | null,
    setDataFusionResult: vi.fn(),
    activeSubView: null,
    navigateTo: vi.fn(),
    activeScenario: makeScenario(),
    updateScenarioField: vi.fn(),
    selectedPopulationId: "",
    setSelectedPopulationId: vi.fn(),
    // Misc required by context shape
    isAuthenticated: true,
    authLoading: false,
    authenticate: vi.fn(),
    logout: vi.fn(),
    activeStage: "population" as const,
    setActiveScenario: vi.fn(),
    savedScenarios: [],
    saveCurrentScenario: vi.fn(),
    loadSavedScenario: vi.fn(),
    resetToDemo: vi.fn(),
    createNewScenario: vi.fn(),
    cloneCurrentScenario: vi.fn(),
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
    templatesLoading: false,
    parametersLoading: false,
    refetchPopulations: vi.fn(),
    refetchTemplates: vi.fn(),
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
    ...overrides,
  };
}

function renderScreen(overrides: Partial<ReturnType<typeof useAppState>> = {}) {
  vi.mocked(useAppState).mockReturnValue(
    makeDefaultAppState(overrides) as ReturnType<typeof useAppState>,
  );
  return render(<PopulationStageScreen />);
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

describe("PopulationStageScreen — Story 20.4", () => {
  describe("AC-1: Population Library as default entry point", () => {
    it("renders Population Library heading with population cards by default", () => {
      renderScreen();
      expect(screen.getByText("Population Library")).toBeInTheDocument();
      // Each mock population should appear as a card
      expect(screen.getByText(mockPopulations[0].name)).toBeInTheDocument();
    });

    it("shows built-in origin tags on pre-loaded populations", () => {
      renderScreen();
      const builtInBadges = screen.getAllByText("[Built-in]");
      expect(builtInBadges.length).toBeGreaterThanOrEqual(1);
    });

    it("renders Upload and Build New buttons in toolbar", () => {
      renderScreen();
      expect(screen.getByRole("button", { name: /upload/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /build new/i })).toBeInTheDocument();
    });

    it("renders DataFusionWorkbench when activeSubView is data-fusion", () => {
      renderScreen({ activeSubView: "data-fusion" });
      expect(screen.getByText("Data Fusion Workbench")).toBeInTheDocument();
    });

    it("renders PopulationExplorer with empty state when activeSubView is population-explorer but no id set", () => {
      renderScreen({ activeSubView: "population-explorer" });
      expect(screen.getByText(/select a population from the library/i)).toBeInTheDocument();
    });
  });

  describe("AC-2: Quick Preview slide-over", () => {
    it("opens Quick Preview on Preview button click", async () => {
      const user = userEvent.setup();
      renderScreen();
      const previewButtons = screen.getAllByTitle(/quick preview/i);
      await user.click(previewButtons[0]);
      await waitFor(() => {
        expect(screen.getByRole("dialog", { name: /quick preview/i })).toBeInTheDocument();
      });
    });

    it("Quick Preview shows table rows", async () => {
      const user = userEvent.setup();
      renderScreen();
      const previewButtons = screen.getAllByTitle(/quick preview/i);
      await user.click(previewButtons[0]);
      await waitFor(() => {
        // The preview shows row data from mock (household_id column header should be visible)
        expect(screen.getByText("household_id")).toBeInTheDocument();
      });
    });

    it("Quick Preview closes on X button click", async () => {
      const user = userEvent.setup();
      renderScreen();
      const previewButtons = screen.getAllByTitle(/quick preview/i);
      await user.click(previewButtons[0]);
      await waitFor(() => {
        expect(screen.getByRole("dialog", { name: /quick preview/i })).toBeInTheDocument();
      });
      await user.click(screen.getByRole("button", { name: /close preview/i }));
      await waitFor(() => {
        expect(screen.queryByRole("dialog", { name: /quick preview/i })).not.toBeInTheDocument();
      });
    });

    it("Quick Preview closes on Escape key", async () => {
      const user = userEvent.setup();
      renderScreen();
      const previewButtons = screen.getAllByTitle(/quick preview/i);
      await user.click(previewButtons[0]);
      await waitFor(() => {
        expect(screen.getByRole("dialog", { name: /quick preview/i })).toBeInTheDocument();
      });
      fireEvent.keyDown(document, { key: "Escape" });
      await waitFor(() => {
        expect(screen.queryByRole("dialog", { name: /quick preview/i })).not.toBeInTheDocument();
      });
    });

    it("Quick Preview closes on backdrop click", async () => {
      const user = userEvent.setup();
      renderScreen();
      const previewButtons = screen.getAllByTitle(/quick preview/i);
      await user.click(previewButtons[0]);
      await waitFor(() => {
        expect(screen.getByRole("dialog", { name: /quick preview/i })).toBeInTheDocument();
      });
      // Click the backdrop
      const backdrop = document.querySelector('[data-testid="quick-preview-backdrop"]');
      if (backdrop) await user.click(backdrop as HTMLElement);
      await waitFor(() => {
        expect(screen.queryByRole("dialog", { name: /quick preview/i })).not.toBeInTheDocument();
      });
    });
  });

  describe("AC-3: Full Data Explorer opens with three tabs", () => {
    it("opens PopulationExplorer on Explore button click", async () => {
      const navigateTo = vi.fn();
      const user = userEvent.setup();
      renderScreen({ navigateTo });
      const exploreButtons = screen.getAllByTitle(/full data explorer/i);
      await user.click(exploreButtons[0]);
      expect(navigateTo).toHaveBeenCalledWith("population", "population-explorer");
    });

    it("PopulationExplorer shows empty state when no population id is set (integration)", () => {
      // With no explorerPopulationId in local state, the explorer shows the empty state message.
      // The three-tabs contract is verified by the standalone PopulationExplorer test below.
      renderScreen({ activeSubView: "population-explorer" });
      expect(screen.getByText(/select a population from the library/i)).toBeInTheDocument();
    });
  });

  describe("AC-3: PopulationExplorer standalone — three tabs (AC-3)", () => {
    it("renders Table, Profile, and Summary tabs when a populationId is provided", () => {
      render(<PopulationExplorer populationId="fr-synthetic-2024" onBack={vi.fn()} />);
      expect(screen.getByRole("tab", { name: /table/i })).toBeInTheDocument();
      expect(screen.getByRole("tab", { name: /profile/i })).toBeInTheDocument();
      expect(screen.getByRole("tab", { name: /summary/i })).toBeInTheDocument();
    });
  });

  describe("AC-4: Upload flow overlay", () => {
    it("opens Upload overlay on Upload button click", async () => {
      const user = userEvent.setup();
      renderScreen();
      await user.click(screen.getByRole("button", { name: /upload/i }));
      await waitFor(() => {
        expect(screen.getByRole("dialog", { name: /upload population/i })).toBeInTheDocument();
      });
    });

    it("Upload overlay shows drag-and-drop zone", async () => {
      const user = userEvent.setup();
      renderScreen();
      await user.click(screen.getByRole("button", { name: /upload/i }));
      await waitFor(() => {
        expect(screen.getByLabelText(/drop zone/i)).toBeInTheDocument();
      });
    });

    it("Upload overlay closes on X button", async () => {
      const user = userEvent.setup();
      renderScreen();
      await user.click(screen.getByRole("button", { name: /upload/i }));
      await waitFor(() => {
        expect(screen.getByRole("dialog", { name: /upload population/i })).toBeInTheDocument();
      });
      await user.click(screen.getByRole("button", { name: /close upload/i }));
      await waitFor(() => {
        expect(screen.queryByRole("dialog", { name: /upload population/i })).not.toBeInTheDocument();
      });
    });
  });

  describe("AC-5: Scenario integration", () => {
    it("Select button calls updateScenarioField and setSelectedPopulationId", async () => {
      const updateScenarioField = vi.fn();
      const setSelectedPopulationId = vi.fn();
      const user = userEvent.setup();
      renderScreen({ updateScenarioField, setSelectedPopulationId });
      const selectButtons = screen.getAllByTitle(/select for scenario/i);
      await user.click(selectButtons[0]);
      expect(updateScenarioField).toHaveBeenCalledWith("populationIds", [mockPopulations[0].id]);
      expect(setSelectedPopulationId).toHaveBeenCalledWith(mockPopulations[0].id);
    });

    it("clicking Select on already-selected population deselects it", async () => {
      const updateScenarioField = vi.fn();
      const setSelectedPopulationId = vi.fn();
      const user = userEvent.setup();
      renderScreen({
        updateScenarioField,
        setSelectedPopulationId,
        activeScenario: makeScenario({ populationIds: [mockPopulations[0].id] }),
      });
      // The first population is selected — clicking Select should deselect
      const selectedButtons = screen.getAllByTitle(/deselect population/i);
      await user.click(selectedButtons[0]);
      expect(updateScenarioField).toHaveBeenCalledWith("populationIds", []);
      expect(setSelectedPopulationId).toHaveBeenCalledWith("");
    });

    it("Delete clears selection when deleting the selected population", async () => {
      const updateScenarioField = vi.fn();
      const setSelectedPopulationId = vi.fn();
      const setDataFusionResult = vi.fn();
      const user = userEvent.setup();

      // Set up with an uploaded population (so it has a Delete button)
      // Mock the state by first generating an uploaded population via direct render trick
      // We test the delete behaviour through the generated population path
      renderScreen({
        updateScenarioField,
        setSelectedPopulationId,
        setDataFusionResult,
        activeScenario: makeScenario({ populationIds: ["data-fusion-result"] }),
        dataFusionResult: {
          success: true,
          summary: { record_count: 5000, column_count: 10, columns: [] },
          step_log: [],
          assumption_chain: [],
          validation_result: null,
        },
      });

      await waitFor(() => {
        expect(screen.getAllByText("Fused Population").length).toBeGreaterThanOrEqual(1);
      });

      // Delete the generated population
      const deleteButton = screen.getByTitle(/delete population/i);
      await user.click(deleteButton);

      expect(setDataFusionResult).toHaveBeenCalledWith(null);
      expect(updateScenarioField).toHaveBeenCalledWith("populationIds", []);
      expect(setSelectedPopulationId).toHaveBeenCalledWith("");
    });

    it("shows selected population name in toolbar when one is selected", () => {
      renderScreen({
        activeScenario: makeScenario({ populationIds: [mockPopulations[0].id] }),
        selectedPopulationId: mockPopulations[0].id,
      });
      expect(screen.getByText(/selected:/i)).toBeInTheDocument();
      expect(screen.getAllByText(mockPopulations[0].name).length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("AC-6: Evidence placeholder tags", () => {
    it("shows [Built-in] tag for pre-loaded populations", () => {
      renderScreen();
      const builtInTags = screen.getAllByText("[Built-in]");
      expect(builtInTags.length).toBeGreaterThanOrEqual(mockPopulations.length);
    });

    it("shows [Generated] tag for Data Fusion result", () => {
      renderScreen({
        dataFusionResult: {
          success: true,
          summary: { record_count: 5000, column_count: 10, columns: [] },
          step_log: [],
          assumption_chain: [],
          validation_result: null,
        },
      });
      expect(screen.getByText("[Generated]")).toBeInTheDocument();
    });
  });
});
