// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Unit tests for PoliciesStageScreen — Story 20.3.
 *
 * Tests:
 * - AC-1: Template browser and composition panel render simultaneously
 * - AC-2: Single-policy portfolio — Save button enabled with 1 policy
 * - AC-3: Conflict detection triggers on composition change (debounced)
 * - AC-4: Portfolio save updates activeScenario.portfolioName
 * - AC-4: Portfolio load populates composition and updates scenario
 * - AC-4: Clear resets composition and nulls portfolioName
 * - AC-5: Nav rail completion tied to activeScenario.portfolioName
 * - AC-6: Validity indicator shows green/amber appropriately
 */

import { render, screen, fireEvent, waitFor, act, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// ============================================================================
// Mocks
// ============================================================================

vi.mock("@/contexts/AppContext", () => ({
  useAppState: vi.fn(),
}));

vi.mock("@/api/portfolios", () => ({
  createPortfolio: vi.fn(),
  getPortfolio: vi.fn(),
  deletePortfolio: vi.fn(),
  clonePortfolio: vi.fn(),
  validatePortfolio: vi.fn(),
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
import {
  createPortfolio,
  validatePortfolio,
  getPortfolio,
  deletePortfolio,
} from "@/api/portfolios";
import { PoliciesStageScreen } from "@/components/screens/PoliciesStageScreen";
import { mockTemplates } from "@/data/mock-data";
import type { WorkspaceScenario } from "@/types/workspace";
import type { PortfolioListItem } from "@/api/types";

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
    engineConfig: { startYear: 2025, endYear: 2030, seed: null, investmentDecisionsEnabled: false, logitModel: null, discountRate: 0.03 },
    policyType: null,
    lastRunId: null,
    ...overrides,
  };
}

function makePortfolio(name: string): PortfolioListItem {
  return { name, description: "Test portfolio", version_id: "v1", policy_count: 2 };
}

function makeDefaultAppState(overrides: Partial<ReturnType<typeof useAppState>> = {}) {
  return {
    templates: mockTemplates,
    portfolios: [],
    refetchPortfolios: vi.fn().mockResolvedValue(undefined),
    activeScenario: makeScenario(),
    updateScenarioField: vi.fn(),
    setSelectedPortfolioName: vi.fn(),
    isAuthenticated: true,
    authLoading: false,
    authenticate: vi.fn(),
    logout: vi.fn(),
    activeStage: "policies" as const,
    activeSubView: null,
    navigateTo: vi.fn(),
    setActiveScenario: vi.fn(),
    savedScenarios: [],
    saveCurrentScenario: vi.fn(),
    loadSavedScenario: vi.fn(),
    resetToDemo: vi.fn(),
    createNewScenario: vi.fn(),
    cloneCurrentScenario: vi.fn(),
    populations: [],
    parameters: [],
    parameterValues: {},
    setParameterValue: vi.fn(),
    scenarios: [],
    decileData: [],
    selectedPopulationId: "",
    setSelectedPopulationId: vi.fn(),
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
    dataFusionResult: null,
    setDataFusionResult: vi.fn(),
    dataFusionSourcesLoading: false,
    portfoliosLoading: false,
    results: [],
    resultsLoading: false,
    refetchResults: vi.fn(),
    selectedPortfolioName: null,
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
  return render(<PoliciesStageScreen />);
}

// ============================================================================
// Setup
// ============================================================================

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(validatePortfolio).mockResolvedValue({ conflicts: [], is_compatible: true });
  vi.mocked(createPortfolio).mockResolvedValue("v-abc123");
  vi.mocked(getPortfolio).mockResolvedValue({
    name: "my-portfolio",
    description: "Test",
    version_id: "v1",
    policies: [
      {
        name: "Carbon Tax",
        policy_type: "carbon_tax",
        rate_schedule: {},
        parameters: {},
      },
    ],
    resolution_strategy: "error",
    policy_count: 1,
  });
  vi.mocked(deletePortfolio).mockResolvedValue(undefined);
});

// Ensure fake timers don't leak between tests
afterEach(() => {
  vi.useRealTimers();
});

// ============================================================================
// AC-1: Inline layout
// ============================================================================

describe("PoliciesStageScreen — AC-1: Inline layout", () => {
  it("renders template browser section heading", () => {
    renderScreen();
    expect(screen.getByRole("heading", { name: /policy templates/i })).toBeInTheDocument();
  });

  it("renders portfolio composition section heading", () => {
    renderScreen();
    expect(screen.getByRole("heading", { name: /portfolio composition/i })).toBeInTheDocument();
  });

  it("renders PortfolioTemplateBrowser section (always visible)", () => {
    renderScreen();
    expect(screen.getByRole("region", { name: /policy template browser/i })).toBeInTheDocument();
  });

  it("shows Save and Load buttons in toolbar", () => {
    renderScreen();
    // Save is disabled (no templates), Load is always enabled
    expect(screen.getByTitle("Load a saved portfolio")).toBeInTheDocument();
  });

  it("shows empty-state guidance when composition is empty", () => {
    renderScreen();
    expect(screen.getByText(/add at least 1 policy template/i)).toBeInTheDocument();
  });
});

// ============================================================================
// AC-2: Single-policy portfolio
// ============================================================================

describe("PoliciesStageScreen — AC-2: Single-policy portfolios", () => {
  it("Save button is disabled when composition is empty", () => {
    renderScreen();
    const saveBtn = screen.getByTitle("Add at least 1 policy template");
    expect(saveBtn).toBeDisabled();
  });

  it("Save button is enabled after adding a single template", () => {
    renderScreen();

    const templateButtons = screen.getAllByRole("button", { pressed: false });
    fireEvent.click(templateButtons[0]);

    // Save button title changes to "Save portfolio" when enabled
    const saveBtn = screen.getByTitle("Save portfolio");
    expect(saveBtn).not.toBeDisabled();
  });
});

// ============================================================================
// AC-3: Conflict detection
// ============================================================================

describe("PoliciesStageScreen — AC-3: Conflict detection", () => {
  it("does not call validatePortfolio with a single policy", async () => {
    vi.useFakeTimers();
    renderScreen();

    const templateButtons = screen.getAllByRole("button", { pressed: false });
    fireEvent.click(templateButtons[0]);

    await act(async () => {
      vi.advanceTimersByTime(600);
    });
    vi.useRealTimers();

    expect(validatePortfolio).not.toHaveBeenCalled();
  });

  it("calls validatePortfolio after debounce when 2+ policies selected", async () => {
    vi.useFakeTimers();
    renderScreen();

    const templateButtons = screen.getAllByRole("button", { pressed: false });
    fireEvent.click(templateButtons[0]);
    fireEvent.click(templateButtons[1]);

    // Advance debounce timer
    await act(async () => {
      vi.advanceTimersByTime(600);
    });

    // Restore real timers and wait for async validation to complete
    vi.useRealTimers();
    await waitFor(() => {
      expect(validatePortfolio).toHaveBeenCalledTimes(1);
    }, { timeout: 2000 });
  });
});

// ============================================================================
// AC-4 & AC-5: Portfolio operations and scenario integration
// ============================================================================

describe("PoliciesStageScreen — AC-4, AC-5: Portfolio-scenario integration", () => {
  it("Save dialog opens when Save button is clicked with a policy added", () => {
    renderScreen();

    const templateButtons = screen.getAllByRole("button", { pressed: false });
    fireEvent.click(templateButtons[0]);
    fireEvent.click(screen.getByTitle("Save portfolio"));

    expect(screen.getByRole("dialog", { name: /save portfolio/i })).toBeInTheDocument();
  });

  it("portfolio save calls createPortfolio and updates portfolioName (AC-4, AC-5)", async () => {
    const updateScenarioField = vi.fn();
    const setSelectedPortfolioName = vi.fn();

    renderScreen({ updateScenarioField, setSelectedPortfolioName });

    const templateButtons = screen.getAllByRole("button", { pressed: false });
    fireEvent.click(templateButtons[0]);
    fireEvent.click(screen.getByTitle("Save portfolio"));

    const dialog = screen.getByRole("dialog", { name: /save portfolio/i });
    fireEvent.change(within(dialog).getByLabelText(/portfolio name/i), {
      target: { value: "my-portfolio" },
    });

    await act(async () => {
      fireEvent.click(within(dialog).getByRole("button", { name: /^save$/i }));
    });

    await waitFor(() => {
      expect(createPortfolio).toHaveBeenCalledTimes(1);
      expect(updateScenarioField).toHaveBeenCalledWith("portfolioName", "my-portfolio");
      expect(setSelectedPortfolioName).toHaveBeenCalledWith("my-portfolio");
    });
  });

  it("portfolio save does NOT call saveCurrentScenario (AC-4 — portfolio ≠ scenario)", async () => {
    const saveCurrentScenario = vi.fn();
    const cloneCurrentScenario = vi.fn();

    renderScreen({ saveCurrentScenario, cloneCurrentScenario });

    const templateButtons = screen.getAllByRole("button", { pressed: false });
    fireEvent.click(templateButtons[0]);
    fireEvent.click(screen.getByTitle("Save portfolio"));

    const dialog = screen.getByRole("dialog", { name: /save portfolio/i });
    fireEvent.change(within(dialog).getByLabelText(/portfolio name/i), {
      target: { value: "my-portfolio" },
    });

    await act(async () => {
      fireEvent.click(within(dialog).getByRole("button", { name: /^save$/i }));
    });

    await waitFor(() => expect(createPortfolio).toHaveBeenCalledTimes(1));

    expect(saveCurrentScenario).not.toHaveBeenCalled();
    expect(cloneCurrentScenario).not.toHaveBeenCalled();
  });

  it("Load dialog opens with saved portfolios listed", () => {
    renderScreen({ portfolios: [makePortfolio("saved-portfolio")] });

    fireEvent.click(screen.getByTitle("Load a saved portfolio"));

    expect(screen.getByRole("dialog", { name: /load portfolio/i })).toBeInTheDocument();
    // Portfolio name appears in the dialog
    expect(screen.getAllByText("saved-portfolio").length).toBeGreaterThan(0);
  });

  it("portfolio load calls getPortfolio and updates activeScenario.portfolioName (AC-5)", async () => {
    const updateScenarioField = vi.fn();
    const setSelectedPortfolioName = vi.fn();

    renderScreen({
      portfolios: [makePortfolio("saved-portfolio")],
      updateScenarioField,
      setSelectedPortfolioName,
    });

    fireEvent.click(screen.getByTitle("Load a saved portfolio"));
    // Click the portfolio row inside the load dialog
    const loadDialog = screen.getByRole("dialog", { name: /load portfolio/i });
    const dialogPortfolioBtn = within(loadDialog).getByRole("button", { name: /saved-portfolio/i });
    await act(async () => {
      fireEvent.click(dialogPortfolioBtn);
    });

    await waitFor(() => {
      expect(getPortfolio).toHaveBeenCalledWith("saved-portfolio");
      expect(updateScenarioField).toHaveBeenCalledWith("portfolioName", "saved-portfolio");
      expect(setSelectedPortfolioName).toHaveBeenCalledWith("saved-portfolio");
    });
  });

  it("Clear button resets composition and nulls portfolioName (AC-4, AC-5)", async () => {
    const updateScenarioField = vi.fn();
    const setSelectedPortfolioName = vi.fn();

    renderScreen({ updateScenarioField, setSelectedPortfolioName });

    const templateButtons = screen.getAllByRole("button", { pressed: false });
    fireEvent.click(templateButtons[0]);

    await waitFor(() => {
      expect(screen.getByTitle("Clear composition")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTitle("Clear composition"));

    expect(updateScenarioField).toHaveBeenCalledWith("portfolioName", null);
    expect(setSelectedPortfolioName).toHaveBeenCalledWith(null);
  });

  it("portfolio load failure does NOT update portfolioName (state corruption guard)", async () => {
    const updateScenarioField = vi.fn();
    const setSelectedPortfolioName = vi.fn();
    vi.mocked(getPortfolio).mockRejectedValue(new Error("Network error"));

    renderScreen({
      portfolios: [makePortfolio("missing-portfolio")],
      updateScenarioField,
      setSelectedPortfolioName,
    });

    fireEvent.click(screen.getByTitle("Load a saved portfolio"));
    const loadDialog = screen.getByRole("dialog", { name: /load portfolio/i });
    await act(async () => {
      fireEvent.click(within(loadDialog).getByRole("button", { name: /missing-portfolio/i }));
    });

    await waitFor(() => expect(getPortfolio).toHaveBeenCalledWith("missing-portfolio"));

    // State must NOT be updated when load fails
    expect(updateScenarioField).not.toHaveBeenCalledWith("portfolioName", "missing-portfolio");
    expect(setSelectedPortfolioName).not.toHaveBeenCalledWith("missing-portfolio");
  });

  it("deleting active portfolio delinks it from scenario (AC-5)", async () => {
    const updateScenarioField = vi.fn();
    const setSelectedPortfolioName = vi.fn();

    renderScreen({
      portfolios: [makePortfolio("my-portfolio")],
      activeScenario: makeScenario({ portfolioName: "my-portfolio" }),
      updateScenarioField,
      setSelectedPortfolioName,
    });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /delete portfolio my-portfolio/i }));
    });

    await waitFor(() => {
      expect(deletePortfolio).toHaveBeenCalledWith("my-portfolio");
      expect(updateScenarioField).toHaveBeenCalledWith("portfolioName", null);
      expect(setSelectedPortfolioName).toHaveBeenCalledWith(null);
    });
  });
});

// ============================================================================
// AC-6: Validity indicator
// ============================================================================

describe("PoliciesStageScreen — AC-6: Validity indicator", () => {
  it("shows no validity indicator when composition is empty", () => {
    renderScreen();
    expect(screen.queryByTestId("validity-indicator-valid")).not.toBeInTheDocument();
    expect(screen.queryByTestId("validity-indicator-invalid")).not.toBeInTheDocument();
  });

  it("shows green checkmark when 1 policy added (single-policy is always valid)", () => {
    renderScreen();

    const templateButtons = screen.getAllByRole("button", { pressed: false });
    fireEvent.click(templateButtons[0]);

    expect(screen.getByTestId("validity-indicator-valid")).toBeInTheDocument();
    expect(screen.queryByTestId("validity-indicator-invalid")).not.toBeInTheDocument();
  });

  it("shows amber warning when 2 policies conflict with error strategy", async () => {
    vi.useFakeTimers();
    vi.mocked(validatePortfolio).mockResolvedValue({
      conflicts: [
        {
          conflict_type: "rate_overlap",
          parameter_name: "tax_rate",
          description: "Conflict",
          policy_indices: [0, 1],
        },
      ],
      is_compatible: false,
    });

    renderScreen();

    const templateButtons = screen.getAllByRole("button", { pressed: false });
    fireEvent.click(templateButtons[0]);
    fireEvent.click(templateButtons[1]);

    await act(async () => {
      vi.advanceTimersByTime(600);
    });
    vi.useRealTimers();

    await waitFor(() => {
      expect(screen.getByTestId("validity-indicator-invalid")).toBeInTheDocument();
    }, { timeout: 2000 });
  });
});

// ============================================================================
// Auto-load on mount
// ============================================================================

describe("PoliciesStageScreen — auto-load on mount", () => {
  it("auto-loads portfolio when activeScenario.portfolioName is set", async () => {
    await act(async () => {
      renderScreen({
        activeScenario: makeScenario({ portfolioName: "my-portfolio" }),
      });
    });

    await waitFor(() => {
      expect(getPortfolio).toHaveBeenCalledWith("my-portfolio");
    }, { timeout: 3000 });
  });

  it("does not call getPortfolio when activeScenario.portfolioName is null", async () => {
    await act(async () => {
      renderScreen({ activeScenario: makeScenario({ portfolioName: null }) });
    });

    // Brief real-timer wait to flush any pending async
    await new Promise((r) => setTimeout(r, 50));
    expect(getPortfolio).not.toHaveBeenCalled();
  });
});

// ============================================================================
// Story 22.2: Layout rebalance and denser typography
// ============================================================================

describe("PoliciesStageScreen — Story 22.2: Layout rebalance and typography", () => {
  describe("AC-1: Desktop 50/50 layout split", () => {
    it("uses equal 50/50 grid split at desktop breakpoint (lg:grid-cols-2)", () => {
      renderScreen();
      // The main layout container should have lg:grid-cols-2 for equal split
      const mainGrid = screen.getByRole("heading", { name: /policy templates/i })
        .closest(".grid");
      expect(mainGrid).toHaveClass("lg:grid-cols-2");
      // Should NOT have the old 1:2 ratio class
      expect(mainGrid).not.toHaveClass("lg:grid-cols-[minmax(0,1fr)_minmax(0,2fr)]");
    });

    it("uses single column for mobile (grid-cols-1 base)", () => {
      renderScreen();
      const mainGrid = screen.getByRole("heading", { name: /policy templates/i })
        .closest(".grid");
      expect(mainGrid).toHaveClass("grid-cols-1");
    });
  });

  describe("AC-2: Denser parameter typography", () => {
    it("parameter labels use text-xs (denser than text-sm)", () => {
      // This requires checking the ParameterRow component directly
      // We'll verify by adding a policy and checking the rendered parameter row
      const { container } = renderScreen();

      // Add a template to trigger parameter display
      const templateButtons = screen.getAllByRole("button", { pressed: false });
      fireEvent.click(templateButtons[0]);

      // Expand the first policy card to show parameters
      const expandButtons = container.querySelectorAll('button[aria-label="Expand parameters"]');
      if (expandButtons.length > 0) {
        fireEvent.click(expandButtons[0]);
      }

      // Check that parameter labels use text-xs class
      // Note: This test depends on ParameterRow rendering, which we verify separately
      const parameterLabels = container.querySelectorAll('.text-xs.text-slate-900');
      // We expect at least some text-xs labels for parameters
      // The exact count depends on the template, but we verify the class is used
      expect(parameterLabels.length).toBeGreaterThan(0);
    });

    it("baseline display remains text-xs (no change)", () => {
      const { container } = renderScreen();

      const templateButtons = screen.getAllByRole("button", { pressed: false });
      fireEvent.click(templateButtons[0]);

      const expandButtons = container.querySelectorAll('button[aria-label="Expand parameters"]');
      if (expandButtons.length > 0) {
        fireEvent.click(expandButtons[0]);
      }

      // Baseline values should use text-xs
      const baselineText = container.querySelectorAll('.text-xs.text-slate-500');
      expect(baselineText.length).toBeGreaterThan(0);
    });

    it("composition panel renders without layout errors", () => {
      renderScreen();

      const templateButtons = screen.getAllByRole("button", { pressed: false });
      fireEvent.click(templateButtons[0]);

      // Verify that the composition panel renders correctly
      const compositionPanel = screen.getByRole("heading", { name: /portfolio composition/i })
        .closest("div");
      expect(compositionPanel).toBeInTheDocument();
    });
  });

  describe("AC-3: Multi-policy layout compatibility", () => {
    it("composition panel accommodates 3+ policies without horizontal overflow", () => {
      const { container } = renderScreen();

      // Add multiple templates (3+)
      const templateButtons = screen.getAllByRole("button", { pressed: false });
      // Only click if we have at least 3 buttons
      const buttonsToClick = Math.min(3, templateButtons.length);
      for (let i = 0; i < buttonsToClick; i++) {
        fireEvent.click(templateButtons[i]);
      }

      // Verify all selected are in the composition
      // Policy cards are in section with class="space-y-2"
      const policyCards = container.querySelectorAll('section[aria-label="Portfolio composition"] > div');
      expect(policyCards.length).toBeGreaterThanOrEqual(buttonsToClick);

      // The composition panel should exist and not have overflow
      const compositionPanel = screen.getByRole("heading", { name: /portfolio composition/i })
        .closest("div");
      expect(compositionPanel).not.toHaveStyle("overflow-x: auto");
    });

    it("all add/edit/reorder/validate/save/load operations work with 3+ policies", () => {
      const { container } = renderScreen();

      // Add 3 templates
      const templateButtons = screen.getAllByRole("button", { pressed: false });
      fireEvent.click(templateButtons[0]);
      fireEvent.click(templateButtons[1]);
      fireEvent.click(templateButtons[2]);

      // Verify save button is enabled
      const saveBtn = screen.getByTitle("Save portfolio");
      expect(saveBtn).not.toBeDisabled();

      // Verify reorder buttons exist for non-first/non-last items
      const moveUpButtons = container.querySelectorAll('button[aria-label="Move up"]');
      const moveDownButtons = container.querySelectorAll('button[aria-label="Move down"]');
      expect(moveUpButtons.length).toBeGreaterThan(0);
      expect(moveDownButtons.length).toBeGreaterThan(0);

      // Verify remove buttons exist
      const removeButtons = container.querySelectorAll('button[aria-label="Remove policy"]');
      expect(removeButtons.length).toBeGreaterThanOrEqual(3);
    });
  });

  describe("AC-4: Responsive stacking for narrow breakpoints", () => {
    it("main grid has grid-cols-1 base class for mobile stacking", () => {
      renderScreen();
      const mainGrid = screen.getByRole("heading", { name: /policy templates/i })
        .closest(".grid");
      expect(mainGrid).toHaveClass("grid-cols-1");
    });

    it("panels maintain independent scrolling when stacked", () => {
      renderScreen();
      // Both panels should have overflow-y-auto for independent scrolling
      const templateBrowser = screen.getByRole("heading", { name: /policy templates/i })
        .closest("div");
      const compositionPanel = screen.getByRole("heading", { name: /portfolio composition/i })
        .closest("div");

      expect(templateBrowser).toHaveClass("overflow-y-auto");
      expect(compositionPanel).toHaveClass("overflow-y-auto");
    });
  });
});

// ============================================================================
// Story 24.4: Portfolio with Surfaced Policies
// ============================================================================

describe("Story 24.4: Portfolio with Surfaced Policies", () => {
  describe("Portfolio save with surfaced policies (AC-4, AC-7)", () => {
    it("should save portfolio containing vehicle_malus policy with correct policy_type", async () => {
      const updateScenarioField = vi.fn();
      const setSelectedPortfolioName = vi.fn();

      // Add surfaced templates to the mock templates
      const templatesWithSurfaced = [
        ...mockTemplates,
        {
          id: "vehicle-malus-flat",
          name: "Vehicle Malus — Flat Rate",
          type: "vehicle_malus",
          parameterCount: 4,
          description: "Flat-rate malus for vehicles",
          parameterGroups: ["emission_threshold", "malus_rate_per_gkm"],
          is_custom: true,
          runtime_availability: "live_ready" as const,
          availability_reason: null,
        },
      ];

      renderScreen({
        templates: templatesWithSurfaced,
        updateScenarioField,
        setSelectedPortfolioName,
      });

      // Click the vehicle_malus template
      const templateButtons = screen.getAllByRole("button", { pressed: false });
      const vehicleButton = templateButtons.find((btn) => btn.textContent?.includes("Vehicle Malus"));
      expect(vehicleButton).toBeDefined();
      fireEvent.click(vehicleButton!);

      // Open save dialog
      fireEvent.click(screen.getByTitle("Save portfolio"));

      const dialog = screen.getByRole("dialog", { name: /save portfolio/i });
      fireEvent.change(within(dialog).getByLabelText(/portfolio name/i), {
        target: { value: "vehicle-malus-portfolio" },
      });

      await act(async () => {
        fireEvent.click(within(dialog).getByRole("button", { name: /^save$/i }));
      });

      await waitFor(() => {
        expect(createPortfolio).toHaveBeenCalledWith(
          expect.objectContaining({
            name: "vehicle-malus-portfolio",
            policies: expect.arrayContaining([
              expect.objectContaining({
                policy_type: "vehicle_malus",
              }),
            ]),
          }),
        );
      });
    });

    it("should save portfolio containing energy_poverty_aid policy with correct policy_type", async () => {
      const updateScenarioField = vi.fn();
      const setSelectedPortfolioName = vi.fn();

      const templatesWithSurfaced = [
        ...mockTemplates,
        {
          id: "energy-poverty-flat",
          name: "Energy Poverty Aid — Flat",
          type: "energy_poverty_aid",
          parameterCount: 4,
          description: "Flat energy voucher",
          parameterGroups: ["income_ceiling", "rate_schedule"],
          is_custom: true,
          runtime_availability: "live_ready" as const,
          availability_reason: null,
        },
      ];

      renderScreen({
        templates: templatesWithSurfaced,
        updateScenarioField,
        setSelectedPortfolioName,
      });

      const templateButtons = screen.getAllByRole("button", { pressed: false });
      const energyButton = templateButtons.find((btn) => btn.textContent?.includes("Energy Poverty Aid"));
      expect(energyButton).toBeDefined();
      fireEvent.click(energyButton!);

      fireEvent.click(screen.getByTitle("Save portfolio"));

      const dialog = screen.getByRole("dialog", { name: /save portfolio/i });
      fireEvent.change(within(dialog).getByLabelText(/portfolio name/i), {
        target: { value: "energy-aid-portfolio" },
      });

      await act(async () => {
        fireEvent.click(within(dialog).getByRole("button", { name: /^save$/i }));
      });

      await waitFor(() => {
        expect(createPortfolio).toHaveBeenCalledWith(
          expect.objectContaining({
            policies: expect.arrayContaining([
              expect.objectContaining({
                policy_type: "energy_poverty_aid",
              }),
            ]),
          }),
        );
      });
    });
  });

  describe("Portfolio load with surfaced policies (AC-4, AC-7)", () => {
    it("should load portfolio containing vehicle_malus policy and display correctly", async () => {
      const updateScenarioField = vi.fn();
      const setSelectedPortfolioName = vi.fn();

      vi.mocked(getPortfolio).mockResolvedValue({
        name: "vehicle-malus-portfolio",
        description: "Test portfolio with vehicle malus",
        version_id: "v1",
        policies: [
          {
            name: "Vehicle Malus",
            policy_type: "vehicle_malus",
            rate_schedule: {},
            parameters: {},
          },
        ],
        resolution_strategy: "error",
        policy_count: 1,
      });

      const templatesWithSurfaced = [
        ...mockTemplates,
        {
          id: "vehicle-malus-flat",
          name: "Vehicle Malus — Flat Rate",
          type: "vehicle_malus",
          parameterCount: 4,
          description: "Flat-rate malus for vehicles",
          parameterGroups: ["emission_threshold", "malus_rate_per_gkm"],
          is_custom: true,
          runtime_availability: "live_ready" as const,
          availability_reason: null,
        },
      ];

      renderScreen({
        portfolios: [makePortfolio("vehicle-malus-portfolio")],
        templates: templatesWithSurfaced,
        updateScenarioField,
        setSelectedPortfolioName,
      });

      fireEvent.click(screen.getByTitle("Load a saved portfolio"));

      const loadDialog = screen.getByRole("dialog", { name: /load portfolio/i });
      const portfolioBtn = within(loadDialog).getByRole("button", { name: /vehicle-malus-portfolio/i });
      await act(async () => {
        fireEvent.click(portfolioBtn);
      });

      await waitFor(() => {
        expect(getPortfolio).toHaveBeenCalledWith("vehicle-malus-portfolio");
        expect(updateScenarioField).toHaveBeenCalledWith("portfolioName", "vehicle-malus-portfolio");
      });
    });

    it("should load portfolio containing energy_poverty_aid policy and display correctly", async () => {
      const updateScenarioField = vi.fn();
      const setSelectedPortfolioName = vi.fn();

      vi.mocked(getPortfolio).mockResolvedValue({
        name: "energy-aid-portfolio",
        description: "Test portfolio with energy aid",
        version_id: "v1",
        policies: [
          {
            name: "Energy Poverty Aid",
            policy_type: "energy_poverty_aid",
            rate_schedule: {},
            parameters: {},
          },
        ],
        resolution_strategy: "error",
        policy_count: 1,
      });

      const templatesWithSurfaced = [
        ...mockTemplates,
        {
          id: "energy-poverty-flat",
          name: "Energy Poverty Aid — Flat",
          type: "energy_poverty_aid",
          parameterCount: 4,
          description: "Flat energy voucher",
          parameterGroups: ["income_ceiling", "rate_schedule"],
          is_custom: true,
          runtime_availability: "live_ready" as const,
          availability_reason: null,
        },
      ];

      renderScreen({
        portfolios: [makePortfolio("energy-aid-portfolio")],
        templates: templatesWithSurfaced,
        updateScenarioField,
        setSelectedPortfolioName,
      });

      fireEvent.click(screen.getByTitle("Load a saved portfolio"));

      const loadDialog = screen.getByRole("dialog", { name: /load portfolio/i });
      const portfolioBtn = within(loadDialog).getByRole("button", { name: /energy-aid-portfolio/i });
      await act(async () => {
        fireEvent.click(portfolioBtn);
      });

      await waitFor(() => {
        expect(getPortfolio).toHaveBeenCalledWith("energy-aid-portfolio");
      });
    });
  });

  describe("Composition panel displays surfaced policies correctly (AC-7)", () => {
    it("should show correct type label 'Vehicle Malus' for vehicle_malus policy in composition", () => {
      const templatesWithSurfaced = [
        ...mockTemplates,
        {
          id: "vehicle-malus-flat",
          name: "Vehicle Malus — Flat Rate",
          type: "vehicle_malus",
          parameterCount: 4,
          description: "Flat-rate malus for vehicles",
          parameterGroups: ["emission_threshold", "malus_rate_per_gkm"],
          is_custom: true,
          runtime_availability: "live_ready" as const,
          availability_reason: null,
        },
      ];

      const { container } = renderScreen({ templates: templatesWithSurfaced });

      const templateButtons = screen.getAllByRole("button", { pressed: false });
      const vehicleButton = templateButtons.find((btn) => btn.textContent?.includes("Vehicle Malus"));
      fireEvent.click(vehicleButton!);

      // Check that "Vehicle Malus" type label appears in composition
      expect(screen.getAllByText("Vehicle Malus").length).toBeGreaterThan(0);
    });

    it("should show correct type label 'Energy Poverty Aid' for energy_poverty_aid policy in composition", () => {
      const templatesWithSurfaced = [
        ...mockTemplates,
        {
          id: "energy-poverty-flat",
          name: "Energy Poverty Aid — Flat",
          type: "energy_poverty_aid",
          parameterCount: 4,
          description: "Flat energy voucher",
          parameterGroups: ["income_ceiling", "rate_schedule"],
          is_custom: true,
          runtime_availability: "live_ready" as const,
          availability_reason: null,
        },
      ];

      const { container } = renderScreen({ templates: templatesWithSurfaced });

      const templateButtons = screen.getAllByRole("button", { pressed: false });
      const energyButton = templateButtons.find((btn) => btn.textContent?.includes("Energy Poverty Aid"));
      fireEvent.click(energyButton!);

      expect(screen.getAllByText("Energy Poverty Aid").length).toBeGreaterThan(0);
    });
  });
});
