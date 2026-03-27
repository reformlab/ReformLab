// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Unit tests for ScenarioEntryDialog component.
 * Story 20.2 — Task 4, Task 7.5.
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

// Mock AppContext to control state
vi.mock("@/contexts/AppContext", () => ({
  useAppState: vi.fn(),
}));

import { useAppState } from "@/contexts/AppContext";
import { ScenarioEntryDialog } from "@/components/scenario/ScenarioEntryDialog";
import type { WorkspaceScenario } from "@/types/workspace";

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
    populationIds: ["fr-synthetic-2024"],
    engineConfig: { startYear: 2025, endYear: 2030, seed: 42, investmentDecisionsEnabled: false, logitModel: null, discountRate: 0.03 },
    policyType: "carbon-tax",
    lastRunId: null,
    ...overrides,
  };
}

function makeDefaultAppState(overrides: Partial<ReturnType<typeof useAppState>> = {}) {
  return {
    activeScenario: makeScenario(),
    savedScenarios: [],
    createNewScenario: vi.fn(),
    cloneCurrentScenario: vi.fn(),
    loadSavedScenario: vi.fn(),
    resetToDemo: vi.fn(),
    // Minimal other required fields
    isAuthenticated: true,
    authLoading: false,
    authenticate: vi.fn(),
    logout: vi.fn(),
    activeStage: "policies" as const,
    activeSubView: null,
    navigateTo: vi.fn(),
    setActiveScenario: vi.fn(),
    updateScenarioField: vi.fn(),
    saveCurrentScenario: vi.fn(),
    populations: [],
    templates: [],
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

function renderDialog(open = true, onOpenChange = vi.fn()) {
  vi.mocked(useAppState).mockReturnValue(makeDefaultAppState() as ReturnType<typeof useAppState>);
  return render(<ScenarioEntryDialog open={open} onOpenChange={onOpenChange} />);
}

// ============================================================================
// Setup
// ============================================================================

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
});

// ============================================================================
// Tests
// ============================================================================

describe("ScenarioEntryDialog", () => {
  it("renders 4 action cards when open", () => {
    renderDialog();

    expect(screen.getByText("New Scenario")).toBeInTheDocument();
    expect(screen.getByText("Open Saved")).toBeInTheDocument();
    expect(screen.getByText("Clone Current")).toBeInTheDocument();
    expect(screen.getByText("Demo Scenario")).toBeInTheDocument();
  });

  it("renders dialog header with 'Switch Scenario' title", () => {
    renderDialog();
    expect(screen.getByText("Switch Scenario")).toBeInTheDocument();
  });

  it("shows current scenario name in subtitle", () => {
    renderDialog();
    expect(screen.getByText(/Current: Test Scenario/)).toBeInTheDocument();
  });

  it("does not render when open is false", () => {
    renderDialog(false);
    expect(screen.queryByText("Switch Scenario")).not.toBeInTheDocument();
  });

  it("clicking 'New Scenario' calls createNewScenario and closes dialog", async () => {
    const onOpenChange = vi.fn();
    const createNewScenario = vi.fn();
    vi.mocked(useAppState).mockReturnValue(
      makeDefaultAppState({ createNewScenario }) as ReturnType<typeof useAppState>,
    );
    render(<ScenarioEntryDialog open={true} onOpenChange={onOpenChange} />);

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /new scenario/i }));

    expect(createNewScenario).toHaveBeenCalledTimes(1);
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("clicking 'Demo Scenario' calls resetToDemo and closes dialog", async () => {
    const onOpenChange = vi.fn();
    const resetToDemo = vi.fn();
    vi.mocked(useAppState).mockReturnValue(
      makeDefaultAppState({ resetToDemo }) as ReturnType<typeof useAppState>,
    );
    render(<ScenarioEntryDialog open={true} onOpenChange={onOpenChange} />);

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /demo scenario/i }));

    expect(resetToDemo).toHaveBeenCalledTimes(1);
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("clicking 'Clone Current' calls cloneCurrentScenario and closes dialog", async () => {
    const onOpenChange = vi.fn();
    const cloneCurrentScenario = vi.fn();
    vi.mocked(useAppState).mockReturnValue(
      makeDefaultAppState({ cloneCurrentScenario }) as ReturnType<typeof useAppState>,
    );
    render(<ScenarioEntryDialog open={true} onOpenChange={onOpenChange} />);

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /clone current/i }));

    expect(cloneCurrentScenario).toHaveBeenCalledTimes(1);
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("'Clone Current' is disabled when activeScenario is null", () => {
    vi.mocked(useAppState).mockReturnValue(
      makeDefaultAppState({ activeScenario: null }) as ReturnType<typeof useAppState>,
    );
    render(<ScenarioEntryDialog open={true} onOpenChange={vi.fn()} />);

    const cloneBtn = screen.getByRole("button", { name: /clone current/i });
    expect(cloneBtn).toBeDisabled();
  });

  it("'Open Saved' expands saved list when clicked", async () => {
    const savedScenario = makeScenario({ id: "saved-1", name: "My Saved Scenario" });
    vi.mocked(useAppState).mockReturnValue(
      makeDefaultAppState({ savedScenarios: [savedScenario] }) as ReturnType<typeof useAppState>,
    );
    render(<ScenarioEntryDialog open={true} onOpenChange={vi.fn()} />);

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /open saved/i }));

    await waitFor(() => {
      expect(screen.getByText("My Saved Scenario")).toBeInTheDocument();
    });
  });

  it("shows 'No saved scenarios yet' when saved list is empty", async () => {
    vi.mocked(useAppState).mockReturnValue(
      makeDefaultAppState({ savedScenarios: [] }) as ReturnType<typeof useAppState>,
    );
    render(<ScenarioEntryDialog open={true} onOpenChange={vi.fn()} />);

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /open saved/i }));

    await waitFor(() => {
      expect(screen.getByText(/no saved scenarios yet/i)).toBeInTheDocument();
    });
  });

  it("clicking a saved scenario calls loadSavedScenario and closes dialog", async () => {
    const onOpenChange = vi.fn();
    const loadSavedScenario = vi.fn();
    const savedScenario = makeScenario({ id: "saved-1", name: "My Saved Scenario" });
    vi.mocked(useAppState).mockReturnValue(
      makeDefaultAppState({ savedScenarios: [savedScenario], loadSavedScenario }) as ReturnType<typeof useAppState>,
    );
    render(<ScenarioEntryDialog open={true} onOpenChange={onOpenChange} />);

    const user = userEvent.setup();
    // First expand the saved list
    await user.click(screen.getByRole("button", { name: /open saved/i }));

    await waitFor(() => {
      expect(screen.getByText("My Saved Scenario")).toBeInTheDocument();
    });

    // Click the saved scenario
    await user.click(screen.getByText("My Saved Scenario"));

    expect(loadSavedScenario).toHaveBeenCalledWith("saved-1");
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });
});
