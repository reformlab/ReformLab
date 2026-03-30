// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Tests for ContextualHelpPanel (Story 20.1 update).
 *
 * Now takes activeStage: StageKey and activeSubView: SubView | null
 * instead of viewMode: string and activeStep?: string.
 */
import { fireEvent, render, screen } from "@testing-library/react";

import { ContextualHelpPanel } from "@/components/help/ContextualHelpPanel";

describe("ContextualHelpPanel", () => {
  it("renders Policies & Portfolio title for policies stage", () => {
    render(<ContextualHelpPanel activeStage="policies" activeSubView={null} />);
    expect(screen.getByText("Policies & Portfolio")).toBeInTheDocument();
  });

  it("renders Population Library title for population stage (Story 20.4)", () => {
    render(<ContextualHelpPanel activeStage="population" activeSubView={null} />);
    expect(screen.getByText("Population Library")).toBeInTheDocument();
  });

  it("renders Engine Configuration title for engine stage", () => {
    render(<ContextualHelpPanel activeStage="engine" activeSubView={null} />);
    expect(screen.getByText("Scenario Configuration")).toBeInTheDocument();
  });

  it("renders Results Overview title for results stage", () => {
    render(<ContextualHelpPanel activeStage="results" activeSubView={null} />);
    expect(screen.getByText("Results Overview")).toBeInTheDocument();
  });

  it("renders Simulation Runner title for results/runner sub-view", () => {
    render(<ContextualHelpPanel activeStage="results" activeSubView="runner" />);
    expect(screen.getByText("Simulation Runner")).toBeInTheDocument();
  });

  it("renders Comparison Dashboard title for results/comparison sub-view", () => {
    render(<ContextualHelpPanel activeStage="results" activeSubView="comparison" />);
    expect(screen.getByText("Comparison Dashboard")).toBeInTheDocument();
  });

  it("renders Behavioral Decisions title for results/decisions sub-view", () => {
    render(<ContextualHelpPanel activeStage="results" activeSubView="decisions" />);
    expect(screen.getByText("Behavioral Decisions")).toBeInTheDocument();
  });

  it("falls back to policies for unrecognized stage", () => {
    render(<ContextualHelpPanel activeStage={"unknown" as never} activeSubView={null} />);
    expect(screen.getByText("Policies & Portfolio")).toBeInTheDocument();
  });

  it("renders tips as list items", () => {
    const { container } = render(<ContextualHelpPanel activeStage="results" activeSubView={null} />);
    const listItems = container.querySelectorAll("ul > li");
    expect(listItems.length).toBeGreaterThanOrEqual(3);
  });

  it("renders Key Concepts trigger for entries with concepts", () => {
    render(<ContextualHelpPanel activeStage="policies" activeSubView={null} />);
    expect(screen.getByText("Key Concepts")).toBeInTheDocument();
  });

  it("Key Concepts section is collapsed by default (AC-3)", () => {
    render(<ContextualHelpPanel activeStage="policies" activeSubView={null} />);
    const trigger = screen.getByText("Key Concepts").closest("button");
    expect(trigger).toHaveAttribute("aria-expanded", "false");
  });

  it("Key Concepts section expands when trigger is clicked (AC-3)", () => {
    render(<ContextualHelpPanel activeStage="policies" activeSubView={null} />);
    const trigger = screen.getByText("Key Concepts");
    fireEvent.click(trigger);
    expect(trigger.closest("button")).toHaveAttribute("aria-expanded", "true");
  });

  it("resets Key Concepts to collapsed when navigating to a new stage (AC-3)", () => {
    const { rerender } = render(<ContextualHelpPanel activeStage="policies" activeSubView={null} />);
    fireEvent.click(screen.getByText("Key Concepts"));
    expect(screen.getByText("Key Concepts").closest("button")).toHaveAttribute("aria-expanded", "true");
    rerender(<ContextualHelpPanel activeStage="results" activeSubView="comparison" />);
    expect(screen.getByText("Key Concepts").closest("button")).toHaveAttribute("aria-expanded", "false");
  });

  it("updates content automatically when stage changes (AC-1)", () => {
    const { rerender } = render(<ContextualHelpPanel activeStage="policies" activeSubView={null} />);
    expect(screen.getByText("Policies & Portfolio")).toBeInTheDocument();
    rerender(<ContextualHelpPanel activeStage="results" activeSubView={null} />);
    expect(screen.getByText("Results Overview")).toBeInTheDocument();
    expect(screen.queryByText("Policies & Portfolio")).not.toBeInTheDocument();
  });
});
