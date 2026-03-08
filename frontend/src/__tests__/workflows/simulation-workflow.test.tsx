/**
 * Simulation Runner Screen — workflow integration tests (Story 17.8, AC-1, AC-4).
 *
 * Tests:
 *   4.2 — configure view → click Run → progress view appears immediately, runScenario called
 *   4.3 — runScenario failure → error state → back to configure
 *   4.4 — delete result from list
 *   4.5 — export CSV/Parquet from a result selected in the configure view
 *
 * Note: SimulationRunnerScreen.handleStartRun() has a deliberate 500ms UX delay
 * before transitioning to post-run view. Tests 4.2 and 4.5 test behaviour that
 * is observable without waiting for that delay (progress view, API call args,
 * and selecting a pre-existing result for export). This keeps the tests fast
 * and avoids fake-timer / act() incompatibility issues with React 18.
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/api/runs", () => ({
  runScenario: vi.fn(),
}));

vi.mock("@/api/results", () => ({
  listResults: vi.fn(),
  getResult: vi.fn(),
  deleteResult: vi.fn(),
  exportResultCsv: vi.fn(),
  exportResultParquet: vi.fn(),
}));

import { runScenario } from "@/api/runs";
import { deleteResult, exportResultCsv, exportResultParquet, getResult, listResults } from "@/api/results";
import { SimulationRunnerScreen } from "@/components/screens/SimulationRunnerScreen";
import { mockResultDetailResponse, mockResultListItem, mockRunResponse, setupExportMocks } from "./helpers";

// ============================================================================
// Constants
// ============================================================================

const DEFAULT_PROPS = {
  selectedPopulationId: "fr-synthetic-2024",
  selectedPortfolioName: null,
  selectedTemplateName: "carbon-tax-flat",
  onCancel: vi.fn(),
} as const;

// ============================================================================
// Setup
// ============================================================================

beforeAll(() => {
  setupExportMocks();
  // Stub anchor.click() to prevent jsdom navigation errors during export tests
  vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
});

// ============================================================================
// Tests
// ============================================================================

describe("Simulation Runner workflow", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Default: empty results list on configure view
    vi.mocked(listResults).mockResolvedValue([]);
  });

  describe("Task 4.2 — initiates run from configure view", () => {
    it("shows progress view immediately and calls runScenario with correct config", async () => {
      vi.mocked(runScenario).mockResolvedValueOnce(mockRunResponse({ run_id: "run-test-001" }));
      vi.mocked(getResult).mockResolvedValue(mockResultDetailResponse({ run_id: "run-test-001" }));

      const user = userEvent.setup();
      render(<SimulationRunnerScreen {...DEFAULT_PROPS} />);

      // Configure view: verify initial UI
      expect(screen.getByRole("button", { name: /run simulation/i })).toBeInTheDocument();
      expect(screen.getByLabelText("Start year")).toBeInTheDocument();
      expect(screen.getByLabelText("End year")).toBeInTheDocument();
      expect(screen.getByLabelText("Random seed")).toBeInTheDocument();

      // Trigger the simulation
      await user.click(screen.getByRole("button", { name: /run simulation/i }));

      // Progress view appears immediately — "Run Simulation" button is gone
      expect(screen.queryByRole("button", { name: /^run simulation$/i })).not.toBeInTheDocument();

      // runScenario was called with the configured values
      await waitFor(() => {
        expect(runScenario).toHaveBeenCalledOnce();
      });
      expect(runScenario).toHaveBeenCalledWith(
        expect.objectContaining({
          template_name: "carbon-tax-flat",
          population_id: "fr-synthetic-2024",
          start_year: 2025,
          end_year: 2030,
        }),
      );
    });
  });

  describe("Task 4.3 — handles simulation failure gracefully", () => {
    it("shows error state and allows reconfiguration", async () => {
      vi.mocked(runScenario).mockRejectedValueOnce({
        what: "Simulation failed",
        why: "Population data not found",
        fix: "Select a valid population",
      });

      const user = userEvent.setup();
      render(<SimulationRunnerScreen {...DEFAULT_PROPS} />);

      await user.click(screen.getByRole("button", { name: /run simulation/i }));

      // Wait for error state (progress view shows error panel)
      await waitFor(() => {
        expect(screen.getByText("Simulation failed")).toBeInTheDocument();
      });

      expect(screen.getByText("Population data not found")).toBeInTheDocument();

      // Can navigate back to configure view
      await user.click(screen.getByRole("button", { name: /back to configuration/i }));
      expect(screen.getByRole("button", { name: /run simulation/i })).toBeInTheDocument();
    });
  });

  describe("Task 4.4 — deletes a result from the list", () => {
    it("removes the result after deletion", async () => {
      const runIdA = "run-delete-a";
      const runIdB = "run-delete-b";

      // Configure view initially shows 2 past results
      vi.mocked(listResults)
        .mockResolvedValueOnce([
          mockResultListItem({ run_id: runIdA, template_name: "Policy A" }),
          mockResultListItem({ run_id: runIdB, template_name: "Policy B" }),
        ])
        .mockResolvedValueOnce([
          mockResultListItem({ run_id: runIdB, template_name: "Policy B" }),
        ]);
      vi.mocked(deleteResult).mockResolvedValueOnce(undefined);

      render(<SimulationRunnerScreen {...DEFAULT_PROPS} />);

      // Wait for results list to render
      await waitFor(() => {
        expect(screen.getByText("Policy A")).toBeInTheDocument();
      });
      expect(screen.getByText("Policy B")).toBeInTheDocument();

      // Delete the first result
      const deleteButtons = screen.getAllByRole("button", { name: /delete/i });
      const user = userEvent.setup();
      await user.click(deleteButtons[0]);

      // After deletion, list refreshes: Policy A gone
      await waitFor(() => {
        expect(screen.queryByText("Policy A")).not.toBeInTheDocument();
      });
      expect(deleteResult).toHaveBeenCalledWith(runIdA);
    });
  });

  describe("Task 4.5 — exports result as CSV and Parquet", () => {
    it("calls export functions after selecting a pre-existing result in the configure view", async () => {
      // Pre-populate the results list shown in the configure view on mount.
      // Selecting the result calls getResult() (dynamic import, still mocked),
      // which loads the detail and reveals the export buttons.
      const runId = "run-export-001";
      vi.mocked(listResults).mockResolvedValue([mockResultListItem({ run_id: runId })]);
      vi.mocked(getResult).mockResolvedValue(mockResultDetailResponse({ run_id: runId }));
      vi.mocked(exportResultCsv).mockResolvedValueOnce(undefined);
      vi.mocked(exportResultParquet).mockResolvedValueOnce(undefined);

      const user = userEvent.setup();
      render(<SimulationRunnerScreen {...DEFAULT_PROPS} />);

      // Wait for the results list to load in the configure view
      await waitFor(() => {
        expect(screen.getByRole("button", { name: new RegExp(`Select run ${runId.slice(0, 8)}`, "i") })).toBeInTheDocument();
      });

      // Select the result — triggers handleSelectResult → getResult → setSelectedDetail
      await user.click(screen.getByRole("button", { name: new RegExp(`Select run ${runId.slice(0, 8)}`, "i") }));

      // Wait for the detail to load — ResultDetailView shows tabs when loaded.
      // Export buttons live in the "Data Summary" tab (not the default "Indicators" tab).
      await waitFor(() => {
        expect(screen.getByRole("tab", { name: /data summary/i })).toBeInTheDocument();
      });

      // Navigate to Data Summary tab to reveal export buttons
      await user.click(screen.getByRole("tab", { name: /data summary/i }));

      // Export buttons have aria-label="Export as CSV" / "Export as Parquet"
      await waitFor(() => {
        expect(screen.getByRole("button", { name: /export as csv/i })).toBeInTheDocument();
      });

      // Click Export CSV
      await user.click(screen.getByRole("button", { name: /export as csv/i }));
      await waitFor(() => {
        expect(exportResultCsv).toHaveBeenCalledWith(runId);
      });

      // Click Export Parquet
      await user.click(screen.getByRole("button", { name: /export as parquet/i }));
      await waitFor(() => {
        expect(exportResultParquet).toHaveBeenCalledWith(runId);
      });
    });
  });
});
