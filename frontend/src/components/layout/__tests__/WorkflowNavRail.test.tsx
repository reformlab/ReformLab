// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Tests for WorkflowNavRail component (Story 18.1).
 *
 * AC-1: nav rail with stage indicators and connecting lines
 * AC-2: completion indicators (checkmark=emerald, active=blue, pending=slate)
 * AC-3: stage summary lines in muted text
 * AC-4: clickable navigation always available
 * AC-6: collapsed state shows icons only
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { WorkflowNavRail, type WorkflowNavRailProps } from "@/components/layout/WorkflowNavRail";

// ============================================================================
// Helpers
// ============================================================================

function baseProps(overrides: Partial<WorkflowNavRailProps> = {}): WorkflowNavRailProps {
  return {
    viewMode: "data-fusion",
    setViewMode: vi.fn(),
    collapsed: false,
    selectedPopulationId: "",
    dataFusionResult: null,
    portfolios: [],
    results: [],
    ...overrides,
  };
}

// ============================================================================
// AC-1: Navigation rail renders all four workflow stages
// ============================================================================

describe("WorkflowNavRail - stage rendering", () => {
  it("renders all four stage labels when expanded", () => {
    render(<WorkflowNavRail {...baseProps()} />);
    expect(screen.getByText("Population")).toBeInTheDocument();
    expect(screen.getByText("Portfolio")).toBeInTheDocument();
    expect(screen.getByText("Simulation")).toBeInTheDocument();
    expect(screen.getByText("Results")).toBeInTheDocument();
  });
});

// ============================================================================
// AC-2: Completion indicators
// ============================================================================

describe("WorkflowNavRail - completion state", () => {
  it("shows stage numbers for all incomplete stages", () => {
    render(<WorkflowNavRail {...baseProps()} />);
    // All stages are incomplete → stage numbers 1-4 appear
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
  });

  it("shows checkmark for Population stage when selectedPopulationId is set", () => {
    render(<WorkflowNavRail {...baseProps({ selectedPopulationId: "fr-synthetic-2024" })} />);
    // Population is complete → check icon should render (no "1" text)
    expect(screen.queryByText("1")).not.toBeInTheDocument();
    // Other stages still show numbers
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("shows checkmark for Population stage when dataFusionResult exists", () => {
    const result = { success: true, summary: { record_count: 1000, column_count: 10, columns: [] }, step_log: [], assumption_chain: [], validation_result: null };
    render(<WorkflowNavRail {...baseProps({ dataFusionResult: result })} />);
    expect(screen.queryByText("1")).not.toBeInTheDocument();
  });

  it("shows checkmark for Portfolio stage when portfolios exist", () => {
    const portfolios = [{ name: "p1", description: "", version_id: "v1", policy_count: 2 }];
    render(<WorkflowNavRail {...baseProps({ portfolios })} />);
    expect(screen.queryByText("2")).not.toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument(); // Population still pending
  });

  it("shows checkmark for Simulation stage when results exist", () => {
    const results = [{ run_id: "r1", timestamp: "2026-01-01T00:00:00Z", run_kind: "scenario" as const, start_year: 2025, end_year: 2030, row_count: 1000, status: "completed" as const, data_available: true, template_name: "carbon_tax", policy_type: "carbon_tax", portfolio_name: null }];
    render(<WorkflowNavRail {...baseProps({ results })} />);
    expect(screen.queryByText("3")).not.toBeInTheDocument();
  });

  it("marks active stage with data-active attribute", () => {
    render(<WorkflowNavRail {...baseProps({ viewMode: "portfolio" })} />);
    const activeIndicator = screen.getByTestId("step-indicator-portfolio");
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

  it("shows portfolio count summary when portfolios exist", () => {
    const portfolios = [
      { name: "carbon-transition", description: "", version_id: "v1", policy_count: 3 },
    ];
    render(<WorkflowNavRail {...baseProps({ portfolios })} />);
    const summary = screen.getByTestId("summary-portfolio");
    expect(summary).toHaveTextContent("1 portfolio");
  });

  it("shows results count summary when results exist", () => {
    const results = [
      { run_id: "r1", timestamp: "2026-01-01T00:00:00Z", run_kind: "scenario" as const, start_year: 2025, end_year: 2030, row_count: 1000, status: "completed" as const, data_available: true, template_name: "carbon_tax", policy_type: "carbon_tax", portfolio_name: null },
      { run_id: "r2", timestamp: "2026-01-02T00:00:00Z", run_kind: "scenario" as const, start_year: 2025, end_year: 2030, row_count: 1000, status: "completed" as const, data_available: true, template_name: "carbon_tax", policy_type: "carbon_tax", portfolio_name: null },
    ];
    render(<WorkflowNavRail {...baseProps({ results })} />);
    const summary = screen.getByTestId("summary-simulation");
    expect(summary).toHaveTextContent("2 runs");
  });

  it("shows no summary text when stage has no data", () => {
    render(<WorkflowNavRail {...baseProps()} />);
    expect(screen.queryByTestId("summary-population")).not.toBeInTheDocument();
    expect(screen.queryByTestId("summary-portfolio")).not.toBeInTheDocument();
    expect(screen.queryByTestId("summary-simulation")).not.toBeInTheDocument();
  });
});

// ============================================================================
// AC-4: Clickable navigation
// ============================================================================

describe("WorkflowNavRail - navigation", () => {
  it("calls setViewMode with data-fusion when Population stage is clicked", async () => {
    const setViewMode = vi.fn();
    render(<WorkflowNavRail {...baseProps({ setViewMode })} />);
    await userEvent.click(screen.getByRole("button", { name: /population/i }));
    expect(setViewMode).toHaveBeenCalledWith("data-fusion");
  });

  it("calls setViewMode with portfolio when Portfolio stage is clicked", async () => {
    const setViewMode = vi.fn();
    render(<WorkflowNavRail {...baseProps({ setViewMode })} />);
    await userEvent.click(screen.getByRole("button", { name: /portfolio/i }));
    expect(setViewMode).toHaveBeenCalledWith("portfolio");
  });

  it("calls setViewMode with runner when Simulation stage is clicked", async () => {
    const setViewMode = vi.fn();
    render(<WorkflowNavRail {...baseProps({ setViewMode })} />);
    await userEvent.click(screen.getByRole("button", { name: /simulation/i }));
    expect(setViewMode).toHaveBeenCalledWith("runner");
  });

  it("calls setViewMode with results when Results stage is clicked", async () => {
    const setViewMode = vi.fn();
    render(<WorkflowNavRail {...baseProps({ setViewMode })} />);
    await userEvent.click(screen.getByRole("button", { name: /results/i }));
    expect(setViewMode).toHaveBeenCalledWith("results");
  });
});

// ============================================================================
// AC-6: Collapsed state
// ============================================================================

describe("WorkflowNavRail - collapsed state", () => {
  it("does not show stage labels when collapsed", () => {
    render(<WorkflowNavRail {...baseProps({ collapsed: true })} />);
    expect(screen.queryByText("Population")).not.toBeInTheDocument();
    expect(screen.queryByText("Portfolio")).not.toBeInTheDocument();
    expect(screen.queryByText("Simulation")).not.toBeInTheDocument();
    expect(screen.queryByText("Results")).not.toBeInTheDocument();
  });

  it("does not show summary lines when collapsed", () => {
    const portfolios = [{ name: "p1", description: "", version_id: "v1", policy_count: 2 }];
    render(<WorkflowNavRail {...baseProps({ collapsed: true, portfolios })} />);
    expect(screen.queryByTestId("summary-portfolio")).not.toBeInTheDocument();
  });

  it("still shows step indicator icons when collapsed", () => {
    render(<WorkflowNavRail {...baseProps({ collapsed: true })} />);
    // Step indicators (numbers or check icons) should still be present
    expect(screen.getByTestId("step-indicator-data-fusion")).toBeInTheDocument();
    expect(screen.getByTestId("step-indicator-portfolio")).toBeInTheDocument();
    expect(screen.getByTestId("step-indicator-runner")).toBeInTheDocument();
    expect(screen.getByTestId("step-indicator-results")).toBeInTheDocument();
  });
});
