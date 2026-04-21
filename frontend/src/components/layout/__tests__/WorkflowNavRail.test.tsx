// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Tests for WorkflowNavRail component (Story 20.1, AC-1).
 *
 * Validates the five canonical stages:
 *   Policies → Population → Investment Decisions → Scenario → Run / Results / Compare
 *
 * AC-1: nav rail with stage indicators and connecting lines
 * AC-2: completion indicators (checkmark=emerald, active=blue, pending=slate)
 * AC-3: stage summary lines in muted text
 * AC-4: clickable navigation always available
 * AC-6: collapsed state shows icons only
 *
 * Story 26.1 — Migrate from four-stage to five-stage workspace.
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { WorkflowNavRail, type WorkflowNavRailProps } from "@/components/layout/WorkflowNavRail";

// ============================================================================
// Helpers
// ============================================================================

function baseProps(overrides: Partial<WorkflowNavRailProps> = {}): WorkflowNavRailProps {
  return {
    activeStage: "policies",
    navigateTo: vi.fn(),
    collapsed: false,
    selectedPopulationId: "",
    dataFusionResult: null,
    portfolios: [],
    results: [],
    activeScenario: null,
    populations: [],
    explorerPopulationId: null,
    activeSubView: null,
    ...overrides,
  };
}

// ============================================================================
// AC-1: Navigation rail renders all five canonical workflow stages
// ============================================================================

describe("WorkflowNavRail - stage rendering", () => {
  it("renders all five stage labels when expanded", () => {
    render(<WorkflowNavRail {...baseProps()} />);
    expect(screen.getByText("Policies")).toBeInTheDocument();
    expect(screen.getByText("Population")).toBeInTheDocument();
    expect(screen.getByText("Investment Decisions")).toBeInTheDocument();
    expect(screen.getByText("Scenario")).toBeInTheDocument();
    expect(screen.getByText("Run / Results / Compare")).toBeInTheDocument();
  });
});

// ============================================================================
// AC-2: Completion indicators
// ============================================================================

describe("WorkflowNavRail - completion state", () => {
  it("shows stage numbers for all incomplete stages", () => {
    render(<WorkflowNavRail {...baseProps()} />);
    // investment-decisions is complete when no active scenario (Story 26.1 logic)
    // Stages 1, 2, 4, 5 are incomplete → stage numbers 1, 2, 4, 5 appear
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
    // investment-decisions (stage 3) shows checkmark instead of number
    expect(screen.queryByText("3")).not.toBeInTheDocument();
  });

  it("shows checkmark for Population stage when selectedPopulationId is set", () => {
    render(<WorkflowNavRail {...baseProps({ selectedPopulationId: "fr-synthetic-2024" })} />);
    // Population (stage 2) is complete → no "2" text
    expect(screen.queryByText("2")).not.toBeInTheDocument();
    // Policies (stage 1) still incomplete
    expect(screen.getByText("1")).toBeInTheDocument();
  });

  it("shows checkmark for Population stage when dataFusionResult exists", () => {
    const result = { success: true, summary: { record_count: 1000, column_count: 10, columns: [] }, step_log: [], assumption_chain: [], validation_result: null };
    render(<WorkflowNavRail {...baseProps({ dataFusionResult: result })} />);
    expect(screen.queryByText("2")).not.toBeInTheDocument();
  });

  it("shows checkmark for Policies stage when activeScenario.portfolioName is set (Story 20.3)", () => {
    const activeScenario = {
      id: "s1", name: "S", version: "1.0", status: "ready", isBaseline: false,
      baselineRef: null, portfolioName: "p1", populationIds: [],
      engineConfig: { startYear: 2025, endYear: 2030, seed: null, investmentDecisionsEnabled: false, logitModel: null as null, discountRate: 0.03 },
      policyType: null, lastRunId: null,
    };
    render(<WorkflowNavRail {...baseProps({ activeScenario })} />);
    // Policies (stage 1) is complete → no "1" text
    expect(screen.queryByText("1")).not.toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument(); // Population still pending
  });

  it("does NOT show checkmark for Policies stage when portfolios exist but portfolioName is null (Story 20.3)", () => {
    const portfolios = [{ name: "p1", description: "", version_id: "v1", policy_count: 2 }];
    render(<WorkflowNavRail {...baseProps({ portfolios })} />);
    // portfolioName is null → policies stage still incomplete
    expect(screen.getByText("1")).toBeInTheDocument();
  });

  it("shows checkmark for Results stage when results exist", () => {
    const results = [{ run_id: "r1", timestamp: "2026-01-01T00:00:00Z", run_kind: "scenario" as const, start_year: 2025, end_year: 2030, row_count: 1000, status: "completed" as const, data_available: true, template_name: "carbon_tax", policy_type: "carbon_tax", portfolio_name: null }];
    render(<WorkflowNavRail {...baseProps({ results })} />);
    // Results (stage 5) is complete → no "5" text
    expect(screen.queryByText("5")).not.toBeInTheDocument();
  });

  it("marks active stage with data-active attribute", () => {
    render(<WorkflowNavRail {...baseProps({ activeStage: "population" })} />);
    const activeIndicator = screen.getByTestId("step-indicator-population");
    expect(activeIndicator).toHaveAttribute("data-active", "true");
  });
});

// ============================================================================
// AC-3: Stage summary lines
// ============================================================================

describe("WorkflowNavRail - summary lines", () => {
  it("shows population summary when population is selected", () => {
    render(<WorkflowNavRail {...baseProps({ selectedPopulationId: "fr-synthetic-2024" })} />);
    expect(screen.getByTestId("summary-population")).toBeInTheDocument();
  });

  it("shows active portfolio name as summary when activeScenario.portfolioName is set (Story 20.3)", () => {
    const activeScenario = {
      id: "s1", name: "S", version: "1.0", status: "ready", isBaseline: false,
      baselineRef: null, portfolioName: "carbon-transition", populationIds: [],
      engineConfig: { startYear: 2025, endYear: 2030, seed: null, investmentDecisionsEnabled: false, logitModel: null as null, discountRate: 0.03 },
      policyType: null, lastRunId: null,
    };
    render(<WorkflowNavRail {...baseProps({ activeScenario })} />);
    const summary = screen.getByTestId("summary-policies");
    expect(summary).toHaveTextContent("carbon-transition");
  });

  it("shows results count summary when results exist", () => {
    const results = [
      { run_id: "r1", timestamp: "2026-01-01T00:00:00Z", run_kind: "scenario" as const, start_year: 2025, end_year: 2030, row_count: 1000, status: "completed" as const, data_available: true, template_name: "carbon_tax", policy_type: "carbon_tax", portfolio_name: null },
      { run_id: "r2", timestamp: "2026-01-02T00:00:00Z", run_kind: "scenario" as const, start_year: 2025, end_year: 2030, row_count: 1000, status: "completed" as const, data_available: true, template_name: "carbon_tax", policy_type: "carbon_tax", portfolio_name: null },
    ];
    render(<WorkflowNavRail {...baseProps({ results })} />);
    const summary = screen.getByTestId("summary-results");
    expect(summary).toHaveTextContent("2 runs");
  });

  it("shows no summary text when stage has no data", () => {
    render(<WorkflowNavRail {...baseProps()} />);
    expect(screen.queryByTestId("summary-policies")).not.toBeInTheDocument();
    expect(screen.queryByTestId("summary-population")).not.toBeInTheDocument();
    // investment-decisions shows "Disabled" when no active scenario (Story 26.1 behavior)
    expect(screen.getByTestId("summary-investment-decisions")).toBeInTheDocument();
    expect(screen.getByTestId("summary-investment-decisions")).toHaveTextContent("Disabled");
    expect(screen.queryByTestId("summary-scenario")).not.toBeInTheDocument();
    expect(screen.queryByTestId("summary-results")).not.toBeInTheDocument();
  });
});

// ============================================================================
// AC-4: Clickable navigation
// ============================================================================

describe("WorkflowNavRail - navigation", () => {
  it("calls navigateTo with policies when Policies stage is clicked", async () => {
    const navigateTo = vi.fn();
    render(<WorkflowNavRail {...baseProps({ navigateTo })} />);
    await userEvent.click(screen.getByRole("button", { name: /^policies$/i }));
    expect(navigateTo).toHaveBeenCalledWith("policies");
  });

  it("calls navigateTo with population when Population stage is clicked", async () => {
    const navigateTo = vi.fn();
    render(<WorkflowNavRail {...baseProps({ navigateTo })} />);
    await userEvent.click(screen.getByRole("button", { name: /^population$/i }));
    expect(navigateTo).toHaveBeenCalledWith("population");
  });

  it("calls navigateTo with scenario when Scenario stage is clicked", async () => {
    const navigateTo = vi.fn();
    render(<WorkflowNavRail {...baseProps({ navigateTo })} />);
    await userEvent.click(screen.getByRole("button", { name: /^scenario$/i }));
    expect(navigateTo).toHaveBeenCalledWith("scenario");
  });

  it("calls navigateTo with results when Run / Results / Compare stage is clicked", async () => {
    const navigateTo = vi.fn();
    render(<WorkflowNavRail {...baseProps({ navigateTo })} />);
    await userEvent.click(screen.getByRole("button", { name: /run.*results.*compare/i }));
    expect(navigateTo).toHaveBeenCalledWith("results");
  });
});

// ============================================================================
// AC-6: Collapsed state
// ============================================================================

describe("WorkflowNavRail - collapsed state", () => {
  it("does not show stage labels when collapsed", () => {
    render(<WorkflowNavRail {...baseProps({ collapsed: true })} />);
    expect(screen.queryByText("Policies")).not.toBeInTheDocument();
    expect(screen.queryByText("Population")).not.toBeInTheDocument();
    expect(screen.queryByText("Investment Decisions")).not.toBeInTheDocument();
    expect(screen.queryByText("Scenario")).not.toBeInTheDocument();
    expect(screen.queryByText("Run / Results / Compare")).not.toBeInTheDocument();
  });

  it("does not show summary lines when collapsed", () => {
    const portfolios = [{ name: "p1", description: "", version_id: "v1", policy_count: 2 }];
    render(<WorkflowNavRail {...baseProps({ collapsed: true, portfolios })} />);
    expect(screen.queryByTestId("summary-policies")).not.toBeInTheDocument();
  });

  it("still shows step indicator icons when collapsed", () => {
    render(<WorkflowNavRail {...baseProps({ collapsed: true })} />);
    // Step indicators (numbers or check icons) should still be present
    expect(screen.getByTestId("step-indicator-policies")).toBeInTheDocument();
    expect(screen.getByTestId("step-indicator-population")).toBeInTheDocument();
    expect(screen.getByTestId("step-indicator-investment-decisions")).toBeInTheDocument();
    expect(screen.getByTestId("step-indicator-scenario")).toBeInTheDocument();
    expect(screen.getByTestId("step-indicator-results")).toBeInTheDocument();
  });
});

// ============================================================================
// Story 22.4: Population sub-steps
// ============================================================================

describe("WorkflowNavRail - Population sub-steps (Story 22.4)", () => {
  it("does NOT show sub-steps when Population stage is NOT active", () => {
    render(<WorkflowNavRail {...baseProps({ activeStage: "policies" })} />);
    expect(screen.queryByTestId("substep-population-library")).not.toBeInTheDocument();
    expect(screen.queryByTestId("substep-population-build")).not.toBeInTheDocument();
    expect(screen.queryByTestId("substep-population-explorer")).not.toBeInTheDocument();
  });

  it("shows sub-steps when Population stage is active and rail is NOT collapsed", () => {
    render(<WorkflowNavRail {...baseProps({ activeStage: "population", collapsed: false })} />);
    expect(screen.getByTestId("substep-population-library")).toBeInTheDocument();
    expect(screen.getByTestId("substep-population-build")).toBeInTheDocument();
    expect(screen.getByTestId("substep-population-explorer")).toBeInTheDocument();
  });

  it("does NOT show sub-steps when rail is collapsed", () => {
    render(<WorkflowNavRail {...baseProps({ activeStage: "population", collapsed: true })} />);
    expect(screen.queryByTestId("substep-population-library")).not.toBeInTheDocument();
    expect(screen.queryByTestId("substep-population-build")).not.toBeInTheDocument();
    expect(screen.queryByTestId("substep-population-explorer")).not.toBeInTheDocument();
  });

  it("shows all three sub-step labels: Library, Build, Explorer", () => {
    render(<WorkflowNavRail {...baseProps({ activeStage: "population" })} />);
    expect(screen.getByText("Library")).toBeInTheDocument();
    expect(screen.getByText("Build")).toBeInTheDocument();
    expect(screen.getByText("Explorer")).toBeInTheDocument();
  });

  it("calls navigateTo with population and null subView when Library is clicked", async () => {
    const navigateTo = vi.fn();
    render(<WorkflowNavRail {...baseProps({ activeStage: "population", navigateTo })} />);
    await userEvent.click(screen.getByTestId("substep-population-library"));
    expect(navigateTo).toHaveBeenCalledWith("population", null);
  });

  it("calls navigateTo with population and data-fusion when Build is clicked", async () => {
    const navigateTo = vi.fn();
    render(<WorkflowNavRail {...baseProps({ activeStage: "population", navigateTo })} />);
    await userEvent.click(screen.getByTestId("substep-population-build"));
    expect(navigateTo).toHaveBeenCalledWith("population", "data-fusion");
  });

  it("Explorer sub-step is disabled when explorerPopulationId is null", () => {
    render(<WorkflowNavRail {...baseProps({ activeStage: "population", explorerPopulationId: null })} />);
    const explorerButton = screen.getByTestId("substep-population-explorer");
    expect(explorerButton).toHaveAttribute("aria-disabled", "true");
    expect(explorerButton).toHaveClass("cursor-not-allowed", "opacity-50");
  });

  it("Explorer sub-step shows tooltip when disabled", () => {
    render(<WorkflowNavRail {...baseProps({ activeStage: "population", explorerPopulationId: null })} />);
    const explorerButton = screen.getByTestId("substep-population-explorer");
    expect(explorerButton).toHaveAttribute("title", "Select a population to explore");
  });

  it("Explorer sub-step is NOT disabled when explorerPopulationId is set", () => {
    render(<WorkflowNavRail {...baseProps({ activeStage: "population", explorerPopulationId: "fr-synthetic-2024" })} />);
    const explorerButton = screen.getByTestId("substep-population-explorer");
    expect(explorerButton).not.toHaveAttribute("aria-disabled", "true");
    expect(explorerButton).not.toHaveClass("cursor-not-allowed");
  });

  it("does NOT call navigateTo when Explorer is clicked with no explorerPopulationId (disabled)", async () => {
    const navigateTo = vi.fn();
    render(<WorkflowNavRail {...baseProps({ activeStage: "population", explorerPopulationId: null, navigateTo })} />);
    await userEvent.click(screen.getByTestId("substep-population-explorer"));
    expect(navigateTo).not.toHaveBeenCalled();
  });

  it("calls navigateTo with population and population-explorer when Explorer is clicked with explorerPopulationId set", async () => {
    const navigateTo = vi.fn();
    render(<WorkflowNavRail {...baseProps({ activeStage: "population", explorerPopulationId: "fr-synthetic-2024", navigateTo })} />);
    await userEvent.click(screen.getByTestId("substep-population-explorer"));
    expect(navigateTo).toHaveBeenCalledWith("population", "population-explorer");
  });

  it("marks Library sub-step as active when activeSubView is null", () => {
    render(<WorkflowNavRail {...baseProps({ activeStage: "population", activeSubView: null })} />);
    const libraryButton = screen.getByTestId("substep-population-library");
    // Active sub-step should have text-slate-900 on the span element
    expect(libraryButton.querySelector("span")).toHaveClass("text-slate-900");
  });

  it("marks Build sub-step as active when activeSubView is data-fusion", () => {
    render(<WorkflowNavRail {...baseProps({ activeStage: "population", activeSubView: "data-fusion" })} />);
    const buildButton = screen.getByTestId("substep-population-build");
    expect(buildButton.querySelector("span")).toHaveClass("text-slate-900");
  });

  it("marks Explorer sub-step as active when activeSubView is population-explorer", () => {
    render(<WorkflowNavRail {...baseProps({ activeStage: "population", activeSubView: "population-explorer" })} />);
    const explorerButton = screen.getByTestId("substep-population-explorer");
    expect(explorerButton.querySelector("span")).toHaveClass("text-slate-900");
  });
});
