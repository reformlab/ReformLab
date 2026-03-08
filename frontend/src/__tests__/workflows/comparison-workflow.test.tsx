/**
 * Comparison Dashboard Screen — workflow integration tests (Story 17.8, AC-1, AC-4).
 *
 * Exercises the complete multi-step comparison journey:
 *   Run Selection → Compare → Tabs (Distributional / Fiscal / Welfare) →
 *   Absolute/Relative Toggle → Cross-Portfolio Rankings → Export CSV
 *
 * Complements existing component unit tests by verifying the full sequential
 * workflow including API call sequence and cross-tab navigation.
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/api/indicators", () => ({
  comparePortfolios: vi.fn(),
}));

import { comparePortfolios } from "@/api/indicators";
import { ApiError } from "@/api/client";
import { ComparisonDashboardScreen } from "@/components/screens/ComparisonDashboardScreen";
import {
  mockComparisonResponse,
  mockResultListItem,
  setupExportMocks,
  setupResizeObserver,
} from "./helpers";

// ============================================================================
// Setup
// ============================================================================

beforeAll(() => {
  setupResizeObserver();
  setupExportMocks();
  vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
});

// ============================================================================
// Fixtures
// ============================================================================

const THREE_RESULTS = [
  mockResultListItem({ run_id: "run-a", template_name: "Policy A" }),
  mockResultListItem({ run_id: "run-b", template_name: "Policy B" }),
  mockResultListItem({ run_id: "run-c", template_name: "Policy C" }),
];

// ============================================================================
// Tests
// ============================================================================

describe("Comparison Dashboard workflow", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Task 5.2 — completes full comparison workflow: select → compare → inspect", () => {
    it("loads comparison data and shows distributional tab by default", async () => {
      vi.mocked(comparePortfolios).mockResolvedValueOnce(mockComparisonResponse());
      const user = userEvent.setup();

      render(<ComparisonDashboardScreen results={THREE_RESULTS} onBack={vi.fn()} />);

      // Select 2 runs
      const checkboxes = screen.getAllByRole("checkbox");
      await user.click(checkboxes[0]);
      await user.click(checkboxes[1]);

      // Click Compare
      const compareBtn = screen.getByRole("button", { name: /compare/i });
      expect(compareBtn).not.toBeDisabled();
      await user.click(compareBtn);

      // Distributional tab should render
      await waitFor(() => {
        expect(screen.getByText("Distributional")).toBeInTheDocument();
        expect(screen.getByText("Fiscal")).toBeInTheDocument();
        expect(screen.getByText("Welfare")).toBeInTheDocument();
      });

      // Income Decile Impact chart heading (distributional tab default)
      await waitFor(() => {
        expect(screen.getByText("Income Decile Impact")).toBeInTheDocument();
      });

      // Cross-Portfolio Rankings visible
      expect(screen.getByText("Cross-Portfolio Rankings")).toBeInTheDocument();
      expect(comparePortfolios).toHaveBeenCalledOnce();
    });

    it("switches between distributional, fiscal, and welfare tabs", async () => {
      vi.mocked(comparePortfolios).mockResolvedValueOnce(mockComparisonResponse());
      const user = userEvent.setup();

      render(<ComparisonDashboardScreen results={THREE_RESULTS} onBack={vi.fn()} />);

      const checkboxes = screen.getAllByRole("checkbox");
      await user.click(checkboxes[0]);
      await user.click(checkboxes[1]);
      await user.click(screen.getByRole("button", { name: /compare/i }));

      await waitFor(() => {
        expect(screen.getByText("Fiscal")).toBeInTheDocument();
      });

      // Switch to Fiscal tab
      await user.click(screen.getByRole("tab", { name: /fiscal/i }));

      // Fiscal tab content: look for fiscal data columns
      await waitFor(() => {
        expect(screen.getAllByText(/Policy A|Policy B|revenue/i).length).toBeGreaterThan(0);
      });

      // Switch to Welfare tab
      await user.click(screen.getByRole("tab", { name: /welfare/i }));
      // Welfare tab renders (no error)
      expect(screen.getByRole("tab", { name: /welfare/i })).toBeInTheDocument();
    });

    it("toggles between absolute and relative views", async () => {
      vi.mocked(comparePortfolios).mockResolvedValueOnce(mockComparisonResponse());
      const user = userEvent.setup();

      render(<ComparisonDashboardScreen results={THREE_RESULTS} onBack={vi.fn()} />);

      const checkboxes = screen.getAllByRole("checkbox");
      await user.click(checkboxes[0]);
      await user.click(checkboxes[1]);
      await user.click(screen.getByRole("button", { name: /compare/i }));

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /relative/i })).toBeInTheDocument();
      });

      // Toggle to Relative view
      await user.click(screen.getByRole("button", { name: /relative/i }));
      expect(screen.getByRole("button", { name: /relative/i })).toHaveAttribute("aria-pressed", "true");

      // Toggle back to Absolute
      await user.click(screen.getByRole("button", { name: /absolute/i }));
      expect(screen.getByRole("button", { name: /absolute/i })).toHaveAttribute("aria-pressed", "true");
    });
  });

  describe("Task 5.3 — shows error when comparison fails", () => {
    it("shows structured error alert when comparePortfolios rejects", async () => {
      vi.mocked(comparePortfolios).mockRejectedValueOnce(
        new ApiError({
          error: "run_evicted",
          what: "Run data unavailable",
          why: "The result has been evicted from the store",
          fix: "Re-run the simulation to restore data",
          status_code: 409,
        }),
      );
      const user = userEvent.setup();

      render(<ComparisonDashboardScreen results={THREE_RESULTS} onBack={vi.fn()} />);

      const checkboxes = screen.getAllByRole("checkbox");
      await user.click(checkboxes[0]);
      await user.click(checkboxes[1]);
      await user.click(screen.getByRole("button", { name: /compare/i }));

      await waitFor(() => {
        expect(screen.getByRole("alert")).toBeInTheDocument();
        expect(screen.getByText("Run data unavailable")).toBeInTheDocument();
      });
    });
  });

  describe("Task 5.4 — shows evicted badge for unavailable runs", () => {
    it("marks evicted run and does not allow it to block the UI", () => {
      const resultsWithEvicted = [
        mockResultListItem({ run_id: "run-live", template_name: "Live Policy" }),
        mockResultListItem({
          run_id: "run-evicted",
          template_name: "Evicted Policy",
          data_available: false,
        }),
      ];

      render(<ComparisonDashboardScreen results={resultsWithEvicted} onBack={vi.fn()} />);

      expect(screen.getByText("(evicted)")).toBeInTheDocument();
      expect(screen.getByText("Evicted Policy")).toBeInTheDocument();
    });
  });

  describe("Task 5.5 — exports comparison data as CSV", () => {
    it("shows Export CSV button after comparison loads and responds to click", async () => {
      vi.mocked(comparePortfolios).mockResolvedValueOnce(mockComparisonResponse());
      const user = userEvent.setup();

      render(<ComparisonDashboardScreen results={THREE_RESULTS} onBack={vi.fn()} />);

      const checkboxes = screen.getAllByRole("checkbox");
      await user.click(checkboxes[0]);
      await user.click(checkboxes[1]);
      await user.click(screen.getByRole("button", { name: /compare/i }));

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /export csv/i })).toBeInTheDocument();
      });

      // Button is clickable (no error thrown)
      await user.click(screen.getByRole("button", { name: /export csv/i }));
    });
  });
});
