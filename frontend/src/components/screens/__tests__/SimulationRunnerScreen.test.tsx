/** Tests for SimulationRunnerScreen — Story 17.3, AC-1. */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

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
    population_id: null,
    seed: null,
    row_count: 1000,
    status: "completed",
    data_available: true,
    template_name: "Carbon Tax",
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

import { SimulationRunnerScreen } from "@/components/screens/SimulationRunnerScreen";

const defaultProps = {
  selectedPopulationId: "fr-synthetic-2024",
  selectedPortfolioName: null,
  selectedTemplateName: "carbon-tax-flat",
  onCancel: vi.fn(),
};

describe("SimulationRunnerScreen", () => {
  describe("pre-run configure view", () => {
    it("renders the configure sub-view by default", () => {
      render(<SimulationRunnerScreen {...defaultProps} />);
      expect(screen.getByRole("button", { name: /Run Simulation/i })).toBeInTheDocument();
    });

    it("shows selected population ID", () => {
      render(<SimulationRunnerScreen {...defaultProps} />);
      expect(screen.getByText("fr-synthetic-2024")).toBeInTheDocument();
    });

    it("shows policy label when template is selected", () => {
      render(<SimulationRunnerScreen {...defaultProps} />);
      expect(screen.getByText("carbon-tax-flat")).toBeInTheDocument();
    });

    it("shows warning when population not selected", () => {
      render(<SimulationRunnerScreen {...defaultProps} selectedPopulationId={null} />);
      expect(screen.getByText("not selected")).toBeInTheDocument();
    });

    it("calls onCancel when cancel button clicked", async () => {
      const onCancel = vi.fn();
      render(<SimulationRunnerScreen {...defaultProps} onCancel={onCancel} />);
      await userEvent.click(screen.getByRole("button", { name: /Cancel/i }));
      expect(onCancel).toHaveBeenCalledOnce();
    });

    it("renders year range inputs", () => {
      render(<SimulationRunnerScreen {...defaultProps} />);
      expect(screen.getByLabelText("Start year")).toBeInTheDocument();
      expect(screen.getByLabelText("End year")).toBeInTheDocument();
    });

    it("renders seed input", () => {
      render(<SimulationRunnerScreen {...defaultProps} />);
      expect(screen.getByLabelText("Random seed")).toBeInTheDocument();
    });
  });

  describe("portfolio runs", () => {
    it("shows portfolio name when portfolioName is set", () => {
      render(
        <SimulationRunnerScreen
          {...defaultProps}
          selectedTemplateName={null}
          selectedPortfolioName="green-transition-2030"
        />,
      );
      expect(screen.getByText("green-transition-2030")).toBeInTheDocument();
    });
  });
});
