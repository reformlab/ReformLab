// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ScenarioCard } from "@/components/simulation/ScenarioCard";
import type { Scenario } from "@/data/mock-data";

const baseScenario: Scenario = {
  id: "baseline",
  name: "Baseline (No Policy)",
  status: "completed",
  isBaseline: true,
  parameterChanges: 0,
  lastRun: "2026-02-27 14:32",
};

const reformScenario: Scenario = {
  id: "reform-a",
  name: "Carbon Tax + Dividend",
  status: "draft",
  isBaseline: false,
  parameterChanges: 3,
  lastRun: "2026-02-27 14:35",
};

const handlers = () => ({
  onSelect: vi.fn(),
  onRun: vi.fn(),
  onCompare: vi.fn(),
  onClone: vi.fn(),
  onDelete: vi.fn(),
});

describe("ScenarioCard", () => {
  it("renders scenario name and status badge", () => {
    const h = handlers();
    render(<ScenarioCard scenario={baseScenario} selected={false} {...h} />);

    expect(screen.getByText("Baseline (No Policy)")).toBeInTheDocument();
    expect(screen.getByText("completed")).toBeInTheDocument();
  });

  it("shows plural parameter change count", () => {
    const h = handlers();
    render(<ScenarioCard scenario={reformScenario} selected={false} {...h} />);
    expect(screen.getByText("3 parameters changed")).toBeInTheDocument();
  });

  it("shows singular parameter change count", () => {
    const h = handlers();
    render(
      <ScenarioCard scenario={{ ...reformScenario, parameterChanges: 1 }} selected={false} {...h} />,
    );
    expect(screen.getByText("1 parameter changed")).toBeInTheDocument();
  });

  it("shows last run timestamp", () => {
    const h = handlers();
    render(<ScenarioCard scenario={baseScenario} selected={false} {...h} />);
    expect(screen.getByText("2026-02-27 14:32")).toBeInTheDocument();
  });

  it("shows 'Not run yet' when lastRun is undefined", () => {
    const h = handlers();
    const scenario: Scenario = { ...reformScenario, lastRun: undefined };
    render(<ScenarioCard scenario={scenario} selected={false} {...h} />);
    expect(screen.getByText("Not run yet")).toBeInTheDocument();
  });

  it("calls onSelect when card is clicked", async () => {
    const h = handlers();
    render(<ScenarioCard scenario={baseScenario} selected={false} {...h} />);

    await userEvent.click(screen.getByText("Baseline (No Policy)"));
    expect(h.onSelect).toHaveBeenCalledWith("baseline");
  });

  it("calls onRun, onCompare, and onClone when action buttons are clicked", async () => {
    const h = handlers();
    render(<ScenarioCard scenario={reformScenario} selected={false} {...h} />);

    await userEvent.click(screen.getByRole("button", { name: /^Run$/i }));
    expect(h.onRun).toHaveBeenCalledWith("reform-a");

    await userEvent.click(screen.getByRole("button", { name: /^Compare$/i }));
    expect(h.onCompare).toHaveBeenCalledWith("reform-a");

    await userEvent.click(screen.getByRole("button", { name: /Clone scenario/i }));
    expect(h.onClone).toHaveBeenCalledWith("reform-a");
  });

  it("shows delete button for non-baseline scenarios", async () => {
    const h = handlers();
    render(<ScenarioCard scenario={reformScenario} selected={false} {...h} />);

    const deleteBtn = screen.getByRole("button", { name: /Delete scenario/i });
    await userEvent.click(deleteBtn);
    expect(h.onDelete).toHaveBeenCalledWith("reform-a");
  });

  it("hides delete button for baseline scenarios", () => {
    const h = handlers();
    render(<ScenarioCard scenario={baseScenario} selected={false} {...h} />);
    expect(screen.queryByRole("button", { name: /Delete scenario/i })).not.toBeInTheDocument();
  });

  it("maps 'running' status to warning badge variant", () => {
    const h = handlers();
    const scenario: Scenario = { ...reformScenario, status: "running" };
    render(<ScenarioCard scenario={scenario} selected={false} {...h} />);
    const badge = screen.getByText("running");
    expect(badge).toHaveAttribute("data-variant", "warning");
  });

  it("maps 'failed' status to destructive badge variant", () => {
    const h = handlers();
    const scenario: Scenario = { ...reformScenario, status: "failed" };
    render(<ScenarioCard scenario={scenario} selected={false} {...h} />);
    const badge = screen.getByText("failed");
    expect(badge).toHaveAttribute("data-variant", "destructive");
  });
});
