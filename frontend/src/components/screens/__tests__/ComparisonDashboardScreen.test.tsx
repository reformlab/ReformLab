// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Tests for ComparisonDashboardScreen — Story 17.4, AC-1 through AC-5. */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

// Mock comparePortfolios API
vi.mock("@/api/indicators", () => ({
  comparePortfolios: vi.fn(),
}));

import { comparePortfolios } from "@/api/indicators";
import { ComparisonDashboardScreen } from "@/components/screens/ComparisonDashboardScreen";
import type { PortfolioComparisonResponse, ResultListItem } from "@/api/types";

// Recharts ResizeObserver
beforeAll(() => {
  globalThis.ResizeObserver ??= class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

// ============================================================================
// Fixtures
// ============================================================================

function makeResult(
  overrides: Partial<ResultListItem> = {},
): ResultListItem {
  return {
    run_id: "run-test-001",
    timestamp: "2026-03-07T22:00:00+00:00",
    run_kind: "scenario",
    start_year: 2025,
    end_year: 2030,
    row_count: 1000,
    status: "completed",
    data_available: true,
    template_name: "Carbon Tax",
    policy_type: "carbon_tax",
    portfolio_name: null,
    ...overrides,
  };
}

const mockResults: ResultListItem[] = [
  makeResult({ run_id: "run-a", template_name: "Policy A" }),
  makeResult({ run_id: "run-b", template_name: "Policy B" }),
  makeResult({ run_id: "run-c", template_name: "Policy C" }),
];

const mockComparisonResponse: PortfolioComparisonResponse = {
  comparisons: {
    distributional: {
      columns: ["decile", "Policy A", "Policy B", "delta_Policy B"],
      data: {
        decile: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "Policy A": [-120, -180, -240, -310, -400, -520, -680, -890, -1200, -1800],
        "Policy B": [-80, -150, -210, -290, -390, -520, -690, -920, -1260, -1950],
        "delta_Policy B": [40, 30, 30, 20, 10, 0, -10, -30, -60, -150],
      },
    },
    fiscal: {
      columns: ["year", "metric", "Policy A", "Policy B"],
      data: {
        year: [2025, 2026],
        metric: ["revenue", "revenue"],
        "Policy A": [2100000000, 2300000000],
        "Policy B": [1800000000, 2000000000],
      },
    },
  },
  cross_metrics: [
    {
      criterion: "max_fiscal_revenue",
      best_portfolio: "Policy A",
      value: 4400000000,
      all_values: { "Policy A": 4400000000, "Policy B": 3800000000 },
    },
  ],
  portfolio_labels: ["Policy A", "Policy B"],
  metadata: { baseline_label: "Policy A" },
  warnings: [],
};

const defaultProps = {
  results: mockResults,
  onBack: vi.fn(),
};

// ============================================================================
// Tests
// ============================================================================

describe("ComparisonDashboardScreen", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("AC-1: Multi-run selection", () => {
    it("renders run selector with completed results", () => {
      render(<ComparisonDashboardScreen {...defaultProps} />);
      // Completed runs should be displayed
      expect(screen.getByText("Policy A")).toBeInTheDocument();
      expect(screen.getByText("Policy B")).toBeInTheDocument();
    });

    it("shows max-5 indicator", () => {
      render(<ComparisonDashboardScreen {...defaultProps} />);
      expect(screen.getByText(/Max 5 runs|max 5 runs|0\/5/i)).toBeInTheDocument();
    });

    it("enables Compare button when 2+ runs selected", async () => {
      const user = userEvent.setup();
      render(<ComparisonDashboardScreen {...defaultProps} />);

      const checkboxes = screen.getAllByRole("checkbox");
      await user.click(checkboxes[0]);
      await user.click(checkboxes[1]);

      const compareBtn = screen.getByRole("button", { name: /Compare/i });
      expect(compareBtn).not.toBeDisabled();
    });

    it("disables Compare button when <2 runs selected", () => {
      render(<ComparisonDashboardScreen {...defaultProps} />);
      // No selections made
      const compareBtn = screen.getByRole("button", { name: /Compare/i });
      expect(compareBtn).toBeDisabled();
    });

    it("shows evicted badge for runs with data_available=false", () => {
      const resultsWithEvicted: ResultListItem[] = [
        makeResult({ run_id: "run-live" }),
        makeResult({
          run_id: "run-evicted",
          data_available: false,
          template_name: "Evicted Policy",
        }),
      ];
      render(
        <ComparisonDashboardScreen results={resultsWithEvicted} onBack={vi.fn()} />,
      );
      expect(screen.getByText("(evicted)")).toBeInTheDocument();
    });

    it("shows empty state when no completed results", () => {
      render(<ComparisonDashboardScreen results={[]} onBack={vi.fn()} />);
      expect(
        screen.getByText(/No completed runs/i),
      ).toBeInTheDocument();
    });
  });

  describe("AC-2: Side-by-side indicator display", () => {
    it("shows comparison data after successful compare", async () => {
      vi.mocked(comparePortfolios).mockResolvedValueOnce(mockComparisonResponse);
      const user = userEvent.setup();
      render(<ComparisonDashboardScreen {...defaultProps} />);

      const checkboxes = screen.getAllByRole("checkbox");
      await user.click(checkboxes[0]);
      await user.click(checkboxes[1]);
      await user.click(screen.getByRole("button", { name: /Compare/i }));

      await waitFor(() => {
        expect(screen.getByText("Distributional")).toBeInTheDocument();
        expect(screen.getByText("Fiscal")).toBeInTheDocument();
        expect(screen.getByText("Welfare")).toBeInTheDocument();
      });
    });

    it("shows distributional tab by default", async () => {
      vi.mocked(comparePortfolios).mockResolvedValueOnce(mockComparisonResponse);
      const user = userEvent.setup();
      render(<ComparisonDashboardScreen {...defaultProps} />);

      const checkboxes = screen.getAllByRole("checkbox");
      await user.click(checkboxes[0]);
      await user.click(checkboxes[1]);
      await user.click(screen.getByRole("button", { name: /Compare/i }));

      await waitFor(() => {
        expect(screen.getByText("Income Decile Impact")).toBeInTheDocument();
      });
    });
  });

  describe("AC-4: Absolute/relative toggle", () => {
    it("renders absolute/relative buttons after data loads", async () => {
      vi.mocked(comparePortfolios).mockResolvedValueOnce(mockComparisonResponse);
      const user = userEvent.setup();
      render(<ComparisonDashboardScreen {...defaultProps} />);

      const checkboxes = screen.getAllByRole("checkbox");
      await user.click(checkboxes[0]);
      await user.click(checkboxes[1]);
      await user.click(screen.getByRole("button", { name: /Compare/i }));

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /Absolute/i })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: /Relative/i })).toBeInTheDocument();
      });
    });

    it("switches to relative view on toggle", async () => {
      vi.mocked(comparePortfolios).mockResolvedValueOnce(mockComparisonResponse);
      const user = userEvent.setup();
      render(<ComparisonDashboardScreen {...defaultProps} />);

      const checkboxes = screen.getAllByRole("checkbox");
      await user.click(checkboxes[0]);
      await user.click(checkboxes[1]);
      await user.click(screen.getByRole("button", { name: /Compare/i }));

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /Relative/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole("button", { name: /Relative/i }));

      // Toggle should now show Relative as pressed
      const relativeBtn = screen.getByRole("button", { name: /Relative/i });
      expect(relativeBtn).toHaveAttribute("aria-pressed", "true");
    });
  });

  describe("AC-5: Cross-comparison metrics", () => {
    it("shows cross-metric panel when data loads", async () => {
      vi.mocked(comparePortfolios).mockResolvedValueOnce(mockComparisonResponse);
      const user = userEvent.setup();
      render(<ComparisonDashboardScreen {...defaultProps} />);

      const checkboxes = screen.getAllByRole("checkbox");
      await user.click(checkboxes[0]);
      await user.click(checkboxes[1]);
      await user.click(screen.getByRole("button", { name: /Compare/i }));

      await waitFor(() => {
        expect(screen.getByText("Cross-Portfolio Rankings")).toBeInTheDocument();
        expect(screen.getByText("Max Fiscal Revenue")).toBeInTheDocument();
      });
    });
  });

  describe("error handling", () => {
    it("shows error state on API failure", async () => {
      vi.mocked(comparePortfolios).mockRejectedValueOnce({
        what: "Run data unavailable",
        why: "The result has been evicted from cache",
        fix: "Re-run the simulation",
      });
      const user = userEvent.setup();
      render(<ComparisonDashboardScreen {...defaultProps} />);

      const checkboxes = screen.getAllByRole("checkbox");
      await user.click(checkboxes[0]);
      await user.click(checkboxes[1]);
      await user.click(screen.getByRole("button", { name: /Compare/i }));

      await waitFor(() => {
        expect(screen.getByRole("alert")).toBeInTheDocument();
        expect(screen.getByText("Run data unavailable")).toBeInTheDocument();
      });
    });
  });

  describe("navigation", () => {
    it("calls onBack when Back button is clicked", async () => {
      const onBack = vi.fn();
      const user = userEvent.setup();
      render(<ComparisonDashboardScreen results={mockResults} onBack={onBack} />);
      await user.click(screen.getByRole("button", { name: /Back/i }));
      expect(onBack).toHaveBeenCalledOnce();
    });
  });

  describe("export", () => {
    it("shows Export CSV button after data loads", async () => {
      vi.mocked(comparePortfolios).mockResolvedValueOnce(mockComparisonResponse);
      const user = userEvent.setup();
      render(<ComparisonDashboardScreen {...defaultProps} />);

      const checkboxes = screen.getAllByRole("checkbox");
      await user.click(checkboxes[0]);
      await user.click(checkboxes[1]);
      await user.click(screen.getByRole("button", { name: /Compare/i }));

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /Export CSV/i })).toBeInTheDocument();
      });
    });
  });
});
