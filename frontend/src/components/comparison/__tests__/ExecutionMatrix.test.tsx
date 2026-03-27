// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * ExecutionMatrix tests — Story 20.6, AC-1.
 */

import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";

import { ExecutionMatrix } from "@/components/comparison/ExecutionMatrix";
import type { ExecutionMatrixCell } from "@/api/types";
import type { WorkspaceScenario } from "@/types/workspace";


describe("ExecutionMatrix", () => {
  const mockScenarios: WorkspaceScenario[] = [
    {
      id: "scenario-1",
      name: "Carbon Tax 50€/t",
      version: "1.0",
      status: "ready",
      isBaseline: false,
      baselineRef: null,
      portfolioName: "carbon-50",
      populationIds: ["fr-synthetic-2024"],
      engineConfig: { startYear: 2025, endYear: 2030, seed: 42, investmentDecisionsEnabled: false, logitModel: "multinomial_logit", discountRate: 0.03 },
      policyType: "carbon_tax",
      lastRunId: null,
    },
    {
      id: "scenario-2",
      name: "Universal Dividend",
      version: "1.0",
      status: "ready",
      isBaseline: false,
      baselineRef: null,
      portfolioName: "dividend-100",
      populationIds: ["fr-synthetic-2024", "data-fusion-result"],
      engineConfig: { startYear: 2025, endYear: 2030, seed: null, investmentDecisionsEnabled: false, logitModel: "multinomial_logit", discountRate: 0.03 },
      policyType: "subsidy",
      lastRunId: null,
    },
  ];

  const mockPopulations = [
    { id: "fr-synthetic-2024", name: "France Synthetic 2024", source: "built-in" },
    { id: "data-fusion-result", name: "Data Fusion Result", source: "generated" },
  ];

  const mockMatrix: Record<string, Record<string, ExecutionMatrixCell>> = {
    "scenario-1": {
      "fr-synthetic-2024": {
        scenarioId: "scenario-1",
        populationId: "fr-synthetic-2024",
        status: "COMPLETED",
        runId: "run-abc123",
        startedAt: "2026-03-27T10:00:00Z",
        finishedAt: "2026-03-27T10:01:30Z",
      },
      "data-fusion-result": {
        scenarioId: "scenario-1",
        populationId: "data-fusion-result",
        status: "NOT_EXECUTED",
      },
    },
    "scenario-2": {
      "fr-synthetic-2024": {
        scenarioId: "scenario-2",
        populationId: "fr-synthetic-2024",
        status: "FAILED",
        runId: "run-def456",
        error: "Out of memory",
        startedAt: "2026-03-27T09:00:00Z",
        finishedAt: "2026-03-27T09:00:45Z",
      },
      "data-fusion-result": {
        scenarioId: "scenario-2",
        populationId: "data-fusion-result",
        status: "RUNNING",
        runId: "run-ghi789",
        startedAt: "2026-03-27T11:00:00Z",
      },
    },
  };

  const mockOnCellClick = vi.fn();
  const mockOnNavigateTo = vi.fn();
  const mockOnCloneScenario = vi.fn();
  const mockOnViewResults = vi.fn();
  const mockOnDeleteRun = vi.fn();
  const mockOnExportRun = vi.fn();
  const mockOnRetryRun = vi.fn();

  it("displays scenario-by-population matrix", () => {
    render(
      <ExecutionMatrix
        scenarios={mockScenarios}
        populations={mockPopulations}
        matrix={mockMatrix}
        onCellClick={mockOnCellClick}
        onNavigateTo={mockOnNavigateTo}
        onCloneScenario={mockOnCloneScenario}
        onViewResults={mockOnViewResults}
        onDeleteRun={mockOnDeleteRun}
        onExportRun={mockOnExportRun}
        onRetryRun={mockOnRetryRun}
      />
    );

    // Check scenario names in rows
    expect(screen.getByText("Carbon Tax 50€/t")).toBeInTheDocument();
    expect(screen.getByText("Universal Dividend")).toBeInTheDocument();

    // Check population names in headers
    expect(screen.getByText("France Synthetic 2024")).toBeInTheDocument();
    expect(screen.getByText("Data Fusion Result")).toBeInTheDocument();

    // Check status badges
    expect(screen.getByText("Done")).toBeInTheDocument(); // COMPLETED
    expect(screen.getByText("Failed")).toBeInTheDocument(); // FAILED
    expect(screen.getByText("Running")).toBeInTheDocument(); // RUNNING
  });

  it("navigates to results on completed cell click", () => {
    render(
      <ExecutionMatrix
        scenarios={mockScenarios}
        populations={mockPopulations}
        matrix={mockMatrix}
        onCellClick={mockOnCellClick}
        onNavigateTo={mockOnNavigateTo}
        onCloneScenario={mockOnCloneScenario}
        onViewResults={mockOnViewResults}
        onDeleteRun={mockOnDeleteRun}
        onExportRun={mockOnExportRun}
        onRetryRun={mockOnRetryRun}
      />
    );

    // Find the COMPLETED cell and click it
    const completedCells = screen.getAllByText("Done");
    expect(completedCells.length).toBeGreaterThan(0);
    fireEvent.click(completedCells[0].closest("td")!);

    expect(mockOnCellClick).toHaveBeenCalledWith(
      expect.objectContaining({
        scenarioId: "scenario-1",
        status: "COMPLETED",
      })
    );
  });

  it("displays empty state when no scenarios", () => {
    render(
      <ExecutionMatrix
        scenarios={[]}
        populations={mockPopulations}
        matrix={{}}
        onCellClick={mockOnCellClick}
        onNavigateTo={mockOnNavigateTo}
        onCloneScenario={mockOnCloneScenario}
        onViewResults={mockOnViewResults}
        onDeleteRun={mockOnDeleteRun}
        onExportRun={mockOnExportRun}
        onRetryRun={mockOnRetryRun}
      />
    );

    expect(screen.getByText(/No scenarios defined yet/)).toBeInTheDocument();
    expect(screen.getByText("Go to Policies Stage")).toBeInTheDocument();
  });

  it("displays empty state when no populations", () => {
    render(
      <ExecutionMatrix
        scenarios={mockScenarios}
        populations={[]}
        matrix={{}}
        onCellClick={mockOnCellClick}
        onNavigateTo={mockOnNavigateTo}
        onCloneScenario={mockOnCloneScenario}
        onViewResults={mockOnViewResults}
        onDeleteRun={mockOnDeleteRun}
        onExportRun={mockOnExportRun}
        onRetryRun={mockOnRetryRun}
      />
    );

    expect(screen.getByText(/No populations available/)).toBeInTheDocument();
    expect(screen.getByText("Go to Population Stage")).toBeInTheDocument();
  });

  it("displays empty state when no executions", () => {
    const emptyMatrix: Record<string, Record<string, ExecutionMatrixCell>> = {
      "scenario-1": {
        "fr-synthetic-2024": {
          scenarioId: "scenario-1",
          populationId: "fr-synthetic-2024",
          status: "NOT_EXECUTED",
        },
      },
    };

    render(
      <ExecutionMatrix
        scenarios={mockScenarios}
        populations={mockPopulations}
        matrix={emptyMatrix}
        onCellClick={mockOnCellClick}
        onNavigateTo={mockOnNavigateTo}
        onCloneScenario={mockOnCloneScenario}
        onViewResults={mockOnViewResults}
        onDeleteRun={mockOnDeleteRun}
        onExportRun={mockOnExportRun}
        onRetryRun={mockOnRetryRun}
      />
    );

    expect(screen.getByText(/No simulations run yet/)).toBeInTheDocument();
    expect(screen.getByText("Run Simulation")).toBeInTheDocument();
  });

  it("displays loading skeleton", () => {
    render(
      <ExecutionMatrix
        scenarios={mockScenarios}
        populations={mockPopulations}
        matrix={mockMatrix}
        loading={true}
        onCellClick={mockOnCellClick}
        onNavigateTo={mockOnNavigateTo}
        onCloneScenario={mockOnCloneScenario}
        onViewResults={mockOnViewResults}
        onDeleteRun={mockOnDeleteRun}
        onExportRun={mockOnExportRun}
        onRetryRun={mockOnRetryRun}
      />
    );

    // Check for skeleton elements
    const skeleton = document.querySelector(".animate-pulse");
    expect(skeleton).toBeInTheDocument();
  });
});
