/** Tests for BehavioralDecisionViewerScreen — Story 17.5, AC-1 through AC-4. */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

// Mock the decisions API module
vi.mock("@/api/decisions", () => ({
  getDecisionSummary: vi.fn(),
}));

import { getDecisionSummary } from "@/api/decisions";
import { ApiError } from "@/api/client";
import { BehavioralDecisionViewerScreen } from "@/components/screens/BehavioralDecisionViewerScreen";
import type { DecisionSummaryResponse } from "@/api/types";

// Recharts ResizeObserver polyfill
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

const mockResponse: DecisionSummaryResponse = {
  run_id: "run-001",
  domains: [
    {
      domain_name: "vehicle",
      alternative_ids: ["keep_current", "buy_ev"],
      alternative_labels: { keep_current: "Keep Current", buy_ev: "Electric (EV)" },
      yearly_outcomes: [
        {
          year: 2025,
          total_households: 100,
          counts: { keep_current: 80, buy_ev: 20 },
          percentages: { keep_current: 80, buy_ev: 20 },
          mean_probabilities: null,
        },
        {
          year: 2026,
          total_households: 100,
          counts: { keep_current: 60, buy_ev: 40 },
          percentages: { keep_current: 60, buy_ev: 40 },
          mean_probabilities: null,
        },
      ],
      eligibility: { n_total: 100, n_eligible: 70, n_ineligible: 30 },
    },
    {
      domain_name: "heating",
      alternative_ids: ["keep_current", "heat_pump"],
      alternative_labels: { keep_current: "Keep Current", heat_pump: "Heat Pump" },
      yearly_outcomes: [
        {
          year: 2025,
          total_households: 100,
          counts: { keep_current: 90, heat_pump: 10 },
          percentages: { keep_current: 90, heat_pump: 10 },
          mean_probabilities: null,
        },
      ],
      eligibility: null,
    },
  ],
  metadata: { start_year: 2025, end_year: 2026 },
  warnings: [],
};

const mockResponseWithProbabilities: DecisionSummaryResponse = {
  ...mockResponse,
  domains: [
    {
      ...mockResponse.domains[0],
      yearly_outcomes: mockResponse.domains[0].yearly_outcomes.map((o) =>
        o.year === 2025
          ? { ...o, mean_probabilities: { keep_current: 0.72, buy_ev: 0.28 } }
          : o,
      ),
    },
    mockResponse.domains[1],
  ],
};

const noDecisionError = new ApiError({
  what: "NoDecisionData",
  why: "No decision data",
  fix: "Run with decisions",
  error: "NoDecisionData",
  status_code: 422,
});

const noIncomeError = new ApiError({
  what: "NoIncomeData",
  why: "No income column",
  fix: "Use income data",
  error: "NoIncomeData",
  status_code: 422,
});

// ============================================================================
// Tests
// ============================================================================

const mockGetDecisionSummary = vi.mocked(getDecisionSummary);

describe("BehavioralDecisionViewerScreen", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("AC-1: Aggregate decision outcomes per domain", () => {
    it("renders domain tabs after successful load", async () => {
      mockGetDecisionSummary.mockResolvedValueOnce(mockResponse);
      render(
        <BehavioralDecisionViewerScreen runId="run-001" onBack={vi.fn()} />,
      );
      await waitFor(() => {
        expect(screen.getByText("Vehicle Fleet")).toBeInTheDocument();
      });
      expect(screen.getByText("Heating System")).toBeInTheDocument();
    });

    it("shows no-data message when 422 NoDecisionData returned", async () => {
      mockGetDecisionSummary.mockRejectedValueOnce(noDecisionError);
      render(
        <BehavioralDecisionViewerScreen runId="run-001" onBack={vi.fn()} />,
      );
      await waitFor(() => {
        expect(
          screen.getByText(/This simulation does not include behavioral decisions/i),
        ).toBeInTheDocument();
      });
    });

    it("shows error state for generic errors", async () => {
      mockGetDecisionSummary.mockRejectedValueOnce(
        new ApiError({ what: "ServerError", why: "Internal", fix: "Retry", error: "ServerError", status_code: 500 }),
      );
      render(
        <BehavioralDecisionViewerScreen runId="run-001" onBack={vi.fn()} />,
      );
      await waitFor(() => {
        expect(screen.getByText("ServerError")).toBeInTheDocument();
      });
    });

    it("calls onBack when Back button clicked", async () => {
      mockGetDecisionSummary.mockResolvedValueOnce(mockResponse);
      const onBack = vi.fn();
      render(<BehavioralDecisionViewerScreen runId="run-001" onBack={onBack} />);
      await waitFor(() => screen.getByText("Vehicle Fleet"));
      await userEvent.click(screen.getByRole("button", { name: /Back/i }));
      expect(onBack).toHaveBeenCalledOnce();
    });
  });

  describe("AC-2: Domain tab switching", () => {
    it("switches to heating tab when clicked", async () => {
      mockGetDecisionSummary.mockResolvedValue(mockResponse);
      const user = userEvent.setup();
      render(
        <BehavioralDecisionViewerScreen runId="run-001" onBack={vi.fn()} />,
      );
      await waitFor(() => screen.getByText("Vehicle Fleet"));
      await user.click(screen.getByText("Heating System"));
      // The heating domain content should now be active — heating has heat_pump alternative
      expect(screen.getByText("Heat Pump")).toBeInTheDocument();
    });
  });

  describe("AC-3: Decile filtering", () => {
    it("renders decile filter select dropdown", async () => {
      mockGetDecisionSummary.mockResolvedValue(mockResponse);
      render(
        <BehavioralDecisionViewerScreen runId="run-001" onBack={vi.fn()} />,
      );
      await waitFor(() => screen.getByText("Vehicle Fleet"));
      // The combobox should be present
      expect(screen.getByRole("combobox")).toBeInTheDocument();
    });

    it("disables decile filter when NoIncomeData error received on filter change", async () => {
      // Initial load succeeds; decile filter triggers NoIncomeData
      mockGetDecisionSummary
        .mockResolvedValueOnce(mockResponse)         // initial load
        .mockRejectedValueOnce(noIncomeError)        // decile fetch fails
        .mockResolvedValueOnce(mockResponse);        // re-fetch without decile
      const user = userEvent.setup();
      render(
        <BehavioralDecisionViewerScreen runId="run-001" onBack={vi.fn()} />,
      );
      await waitFor(() => screen.getByText("Vehicle Fleet"));
      // Use selectOptions for native <select> element
      const select = screen.getByRole("combobox");
      await user.selectOptions(select, "1");
      await waitFor(() => {
        expect(screen.getByRole("combobox")).toBeDisabled();
      });
    });
  });

  describe("AC-4: Year detail panel", () => {
    it("opens year detail panel when year clicked in table", async () => {
      mockGetDecisionSummary
        .mockResolvedValueOnce(mockResponse)
        .mockResolvedValueOnce(mockResponseWithProbabilities);
      const user = userEvent.setup();
      render(
        <BehavioralDecisionViewerScreen runId="run-001" onBack={vi.fn()} />,
      );
      // Wait for both the tab trigger and companion table content to be ready
      await waitFor(() => {
        expect(screen.getByText("Vehicle Fleet")).toBeInTheDocument();
        expect(screen.getAllByText("2025").length).toBeGreaterThan(0);
      });
      const yearCells = screen.getAllByText("2025");
      await user.click(yearCells[0]);
      await waitFor(() => {
        expect(screen.getByText(/Year 2025 — Decision Detail/)).toBeInTheDocument();
      });
    });

    it("closes year detail panel on close button click", async () => {
      mockGetDecisionSummary
        .mockResolvedValueOnce(mockResponse)
        .mockResolvedValueOnce(mockResponseWithProbabilities);
      const user = userEvent.setup();
      render(
        <BehavioralDecisionViewerScreen runId="run-001" onBack={vi.fn()} />,
      );
      // Wait for both the tab trigger and companion table content to be ready
      await waitFor(() => {
        expect(screen.getByText("Vehicle Fleet")).toBeInTheDocument();
        expect(screen.getAllByText("2025").length).toBeGreaterThan(0);
      });
      const yearCells = screen.getAllByText("2025");
      await user.click(yearCells[0]);
      await waitFor(() => screen.getByText(/Year 2025 — Decision Detail/));
      await user.click(screen.getByRole("button", { name: /close year detail/i }));
      await waitFor(() => {
        expect(screen.queryByText(/Year 2025 — Decision Detail/)).not.toBeInTheDocument();
      });
    });
  });
});
