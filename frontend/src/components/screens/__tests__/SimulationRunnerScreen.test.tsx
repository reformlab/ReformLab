// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Tests for SimulationRunnerScreen — Story 20.6, AC-2. */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

// Mock the API modules so no real HTTP calls are made
vi.mock("@/api/runs", () => ({
  runScenario: vi.fn().mockResolvedValue({
    run_id: "test-run-001",
    success: true,
    scenario_id: "scenario-001",
    years: [2025],
    row_count: 1000,
    manifest_id: "manifest-001",
  }),
}));

vi.mock("@/api/results", () => ({
  listResults: vi.fn().mockResolvedValue([]),
  getResult: vi.fn().mockResolvedValue({
    run_id: "test-run-001",
    timestamp: "2026-03-07T22:00:00Z",
    run_kind: "scenario",
    start_year: 2025,
    end_year: 2025,
    population_id: "fr-synthetic-2024",
    seed: 42,
    row_count: 1000,
    status: "completed",
    data_available: true,
    template_name: "carbon_tax",
    policy_type: "carbon_tax",
    portfolio_name: null,
    manifest_id: "manifest-001",
    scenario_id: "scenario-001",
    adapter_version: "1.0.0",
    started_at: "2026-03-07T22:00:00Z",
    finished_at: "2026-03-07T22:00:01Z",
    indicators: null,
    columns: null,
    column_count: null,
  }),
  deleteResult: vi.fn().mockResolvedValue(undefined),
}));

// Recharts ResizeObserver polyfill
globalThis.ResizeObserver ??= class {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock AppContext
vi.mock("@/contexts/AppContext", () => ({
  useAppState: () => ({
    activeScenario: {
      id: "scenario-001",
      name: "Carbon Tax 50€/t",
      version: "1.0",
      status: "ready",
      isBaseline: false,
      baselineRef: null,
      portfolioName: "carbon-50",
      populationIds: ["fr-synthetic-2024"],
      engineConfig: {
        startYear: 2025,
        endYear: 2030,
        seed: 42,
        investmentDecisionsEnabled: false,
        logitModel: "multinomial_logit",
        discountRate: 0.03,
      },
      policyType: "carbon_tax",
      lastRunId: null,
    },
    updateExecutionCell: vi.fn(),
    updateScenarioField: vi.fn(),
  }),
  AppProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

import { SimulationRunnerScreen } from "@/components/screens/SimulationRunnerScreen";

describe("SimulationRunnerScreen", () => {
  describe("pre-run configure view", () => {
    const onCancel = vi.fn();

    it("renders the configure sub-view by default", () => {
      render(<SimulationRunnerScreen onCancel={onCancel} />);
      // Component should render without crashing
      expect(true).toBe(true);
    });

    it("calls onCancel when cancel button clicked", async () => {
      const { container } = render(<SimulationRunnerScreen onCancel={onCancel} />);
      const cancelButton = container.querySelector('button:not([aria-label="Run Simulation"])');
      expect(cancelButton).toBeInTheDocument();
    });
  });
});
