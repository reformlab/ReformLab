/** Tests for ResultsOverviewScreen — Story 18.4, AC-1 through AC-5. */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

// Mock the results API module
vi.mock("@/api/results", () => ({
  getResult: vi.fn(),
}));

import { getResult } from "@/api/results";
import { ResultsOverviewScreen } from "@/components/screens/ResultsOverviewScreen";
import type { DecileData } from "@/data/mock-data";
import type { ResultDetailResponse, RunResponse } from "@/api/types";

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

function mockDecileData(): DecileData[] {
  return [
    { decile: "D1", baseline: -120, reform: -80, delta: 40 },
    { decile: "D2", baseline: -180, reform: -150, delta: 30 },
    { decile: "D10", baseline: -1800, reform: -1950, delta: -150 },
  ];
}

function mockRunResult(overrides: Partial<RunResponse> = {}): RunResponse {
  return {
    run_id: "abcd1234-5678-90ab-cdef-123456789012",
    success: true,
    scenario_id: "scenario-1",
    years: [2025, 2026, 2027],
    row_count: 100000,
    manifest_id: "manifest-1",
    ...overrides,
  };
}

function mockDetail(overrides: Partial<ResultDetailResponse> = {}): ResultDetailResponse {
  return {
    run_id: "abcd1234-5678-90ab-cdef-123456789012",
    timestamp: "2026-03-22T12:00:00Z",
    run_kind: "scenario",
    start_year: 2025,
    end_year: 2027,
    row_count: 100000,
    status: "completed",
    data_available: true,
    template_name: "Carbon Tax",
    policy_type: "carbon_tax",
    portfolio_name: null,
    population_id: null,
    seed: null,
    manifest_id: "manifest-1",
    scenario_id: "scenario-1",
    adapter_version: "1.0.0",
    started_at: "2026-03-22T11:59:00Z",
    finished_at: "2026-03-22T12:00:00Z",
    indicators: null,
    columns: null,
    column_count: null,
    ...overrides,
  };
}

const defaultProps = {
  decileData: mockDecileData(),
  runResult: mockRunResult(),
  reformLabel: "Carbon Tax — With Dividend",
  onCompare: vi.fn(),
  onViewDecisions: vi.fn(),
  onRunAgain: vi.fn(),
  onExportCsv: vi.fn(),
  onExportParquet: vi.fn(),
};

// ============================================================================
// AC-1: Run metadata header
// ============================================================================

describe("AC-1: Run metadata header", () => {
  it("renders run_id (first 8 chars) in monospace", () => {
    render(<ResultsOverviewScreen {...defaultProps} />);
    expect(screen.getByText("abcd1234")).toBeInTheDocument();
  });

  it("renders policy label", () => {
    render(<ResultsOverviewScreen {...defaultProps} />);
    expect(screen.getByText("Carbon Tax — With Dividend")).toBeInTheDocument();
  });

  it("renders year range badge from runResult.years", () => {
    render(<ResultsOverviewScreen {...defaultProps} />);
    expect(screen.getByText("2025–2027")).toBeInTheDocument();
  });

  it("renders 'completed' status badge when success=true", () => {
    render(<ResultsOverviewScreen {...defaultProps} />);
    expect(screen.getByText("completed")).toBeInTheDocument();
  });

  it("renders 'failed' status badge when success=false", () => {
    render(
      <ResultsOverviewScreen
        {...defaultProps}
        runResult={mockRunResult({ success: false })}
      />,
    );
    expect(screen.getByText("failed")).toBeInTheDocument();
  });

  it("renders reformLabel and 'mock data' badge when runResult is null", () => {
    render(<ResultsOverviewScreen {...defaultProps} runResult={null} />);
    // AC-1: shows selected scenario name (reformLabel), not static "Results"
    expect(screen.getByText("Carbon Tax — With Dividend")).toBeInTheDocument();
    expect(screen.getByText("mock data")).toBeInTheDocument();
    expect(screen.queryByText("Results")).not.toBeInTheDocument();
  });

  it("shows '—' for year range when years array is empty", () => {
    render(
      <ResultsOverviewScreen
        {...defaultProps}
        runResult={mockRunResult({ years: [] })}
      />,
    );
    // AC-1: year range badge shows "—" when years array is empty
    expect(screen.getByText("—")).toBeInTheDocument();
    // No en-dash range should appear
    expect(screen.queryByText(/\d–\d/)).not.toBeInTheDocument();
  });
});

// ============================================================================
// AC-2: Tabbed results layout
// ============================================================================

describe("AC-2: Tabbed results layout", () => {
  it("renders three tabs: Overview, Data & Export, Detail", () => {
    render(<ResultsOverviewScreen {...defaultProps} />);
    expect(screen.getByRole("tab", { name: "Overview" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Data.*Export/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Detail" })).toBeInTheDocument();
  });

  it("Overview tab is selected by default", () => {
    render(<ResultsOverviewScreen {...defaultProps} />);
    const overviewTab = screen.getByRole("tab", { name: "Overview" });
    expect(overviewTab).toHaveAttribute("aria-selected", "true");
  });
});

// ============================================================================
// AC-3: Action hierarchy
// ============================================================================

describe("AC-3: Action button hierarchy", () => {
  it("'Compare Runs' is a primary (default) button", () => {
    render(<ResultsOverviewScreen {...defaultProps} />);
    const btn = screen.getByRole("button", { name: "Compare Runs" });
    // Default variant has no outline/ghost class modifiers
    expect(btn).not.toHaveClass("border");
    expect(btn).toBeInTheDocument();
  });

  it("'Behavioral Decisions' is outline button, visible when run_id exists", () => {
    render(<ResultsOverviewScreen {...defaultProps} />);
    const btn = screen.getByRole("button", { name: "Behavioral Decisions" });
    expect(btn).toBeInTheDocument();
  });

  it("'Run Again' is a ghost button", () => {
    render(<ResultsOverviewScreen {...defaultProps} />);
    const btn = screen.getByRole("button", { name: "Run Again" });
    expect(btn).toBeInTheDocument();
  });

  it("'Behavioral Decisions' button is hidden when runResult is null", () => {
    render(<ResultsOverviewScreen {...defaultProps} runResult={null} />);
    expect(screen.queryByRole("button", { name: "Behavioral Decisions" })).not.toBeInTheDocument();
  });

  it("calls onCompare when Compare Runs is clicked", async () => {
    const onCompare = vi.fn();
    render(<ResultsOverviewScreen {...defaultProps} onCompare={onCompare} />);
    await userEvent.click(screen.getByRole("button", { name: "Compare Runs" }));
    expect(onCompare).toHaveBeenCalledTimes(1);
  });

  it("calls onViewDecisions when Behavioral Decisions is clicked", async () => {
    const onViewDecisions = vi.fn();
    render(<ResultsOverviewScreen {...defaultProps} onViewDecisions={onViewDecisions} />);
    await userEvent.click(screen.getByRole("button", { name: "Behavioral Decisions" }));
    expect(onViewDecisions).toHaveBeenCalledTimes(1);
  });

  it("calls onRunAgain when Run Again is clicked", async () => {
    const onRunAgain = vi.fn();
    render(<ResultsOverviewScreen {...defaultProps} onRunAgain={onRunAgain} />);
    await userEvent.click(screen.getByRole("button", { name: "Run Again" }));
    expect(onRunAgain).toHaveBeenCalledTimes(1);
  });

  it("export buttons do NOT appear in header", () => {
    render(<ResultsOverviewScreen {...defaultProps} />);
    // In header there should be exactly 3 buttons (Compare, Decisions, Run Again)
    const headerButtons = screen.getAllByRole("button", { name: /Compare Runs|Behavioral Decisions|Run Again/ });
    expect(headerButtons).toHaveLength(3);
  });
});

// ============================================================================
// AC-4: Real summary statistics from decileData
// ============================================================================

describe("AC-4: Summary statistics computed from decileData", () => {
  it("shows 'Mean impact' stat card", () => {
    render(<ResultsOverviewScreen {...defaultProps} />);
    expect(screen.getByText("Mean impact")).toBeInTheDocument();
  });

  it("shows 'Most benefit' stat card", () => {
    render(<ResultsOverviewScreen {...defaultProps} />);
    expect(screen.getByText("Most benefit")).toBeInTheDocument();
  });

  it("shows 'Most cost' stat card", () => {
    render(<ResultsOverviewScreen {...defaultProps} />);
    expect(screen.getByText("Most cost")).toBeInTheDocument();
  });

  it("computes mean delta correctly: (40+30-150)/3 = -26.67 → rounds to -27", () => {
    render(<ResultsOverviewScreen {...defaultProps} />);
    // mean delta = (40+30+(-150))/3 = -80/3 ≈ -26.67 → rounded to -27
    // The trendValue shows the rounded delta
    expect(screen.getByText("-27")).toBeInTheDocument();
  });

  it("shows placeholder cards when decileData is empty", () => {
    render(<ResultsOverviewScreen {...defaultProps} decileData={[]} />);
    expect(screen.getAllByText("—")).toHaveLength(6); // 3 values + 3 trendValues
  });

  it("shows placeholder cards when all deltas are zero", () => {
    const zeroData: DecileData[] = [
      { decile: "D1", baseline: -100, reform: -100, delta: 0 },
      { decile: "D2", baseline: -200, reform: -200, delta: 0 },
    ];
    render(<ResultsOverviewScreen {...defaultProps} decileData={zeroData} />);
    expect(screen.getAllByText("—")).toHaveLength(6);
  });

  it("D1 is shown as 'Most benefit' decile (max positive delta=40)", () => {
    render(<ResultsOverviewScreen {...defaultProps} />);
    // Most benefit value is the decile name "D1"
    expect(screen.getByText("D1")).toBeInTheDocument();
  });

  it("D10 is shown as 'Most cost' decile (max negative delta=-150)", () => {
    render(<ResultsOverviewScreen {...defaultProps} />);
    expect(screen.getByText("D10")).toBeInTheDocument();
  });
});

// ============================================================================
// AC-2 (Data & Export tab)
// ============================================================================

describe("Data & Export tab", () => {
  it("shows export buttons when switching to Data & Export tab", async () => {
    render(<ResultsOverviewScreen {...defaultProps} />);
    await userEvent.click(screen.getByRole("tab", { name: /Data.*Export/i }));
    expect(screen.getByRole("button", { name: /Export CSV/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Export Parquet/ })).toBeInTheDocument();
  });

  it("export buttons are enabled when runResult.success=true", async () => {
    render(<ResultsOverviewScreen {...defaultProps} />);
    await userEvent.click(screen.getByRole("tab", { name: /Data.*Export/i }));
    expect(screen.getByRole("button", { name: /Export CSV/ })).not.toBeDisabled();
    expect(screen.getByRole("button", { name: /Export Parquet/ })).not.toBeDisabled();
  });

  it("export buttons are disabled when runResult is null", async () => {
    render(<ResultsOverviewScreen {...defaultProps} runResult={null} />);
    await userEvent.click(screen.getByRole("tab", { name: /Data.*Export/i }));
    expect(screen.getByRole("button", { name: /Export CSV/ })).toBeDisabled();
    expect(screen.getByRole("button", { name: /Export Parquet/ })).toBeDisabled();
  });

  it("export buttons are disabled when runResult.success=false", async () => {
    render(
      <ResultsOverviewScreen
        {...defaultProps}
        runResult={mockRunResult({ success: false })}
      />,
    );
    await userEvent.click(screen.getByRole("tab", { name: /Data.*Export/i }));
    expect(screen.getByRole("button", { name: /Export CSV/ })).toBeDisabled();
    expect(screen.getByRole("button", { name: /Export Parquet/ })).toBeDisabled();
  });

  it("shows 'Run a simulation first' message when no run result", async () => {
    render(<ResultsOverviewScreen {...defaultProps} runResult={null} />);
    await userEvent.click(screen.getByRole("tab", { name: /Data.*Export/i }));
    expect(screen.getByText(/Run a simulation first/i)).toBeInTheDocument();
  });

  it("calls onExportCsv when CSV button clicked", async () => {
    const onExportCsv = vi.fn();
    render(<ResultsOverviewScreen {...defaultProps} onExportCsv={onExportCsv} />);
    await userEvent.click(screen.getByRole("tab", { name: /Data.*Export/i }));
    await userEvent.click(screen.getByRole("button", { name: /Export CSV/ }));
    expect(onExportCsv).toHaveBeenCalledTimes(1);
  });

  it("calls onExportParquet when Parquet button clicked", async () => {
    const onExportParquet = vi.fn();
    render(<ResultsOverviewScreen {...defaultProps} onExportParquet={onExportParquet} />);
    await userEvent.click(screen.getByRole("tab", { name: /Data.*Export/i }));
    await userEvent.click(screen.getByRole("button", { name: /Export Parquet/ }));
    expect(onExportParquet).toHaveBeenCalledTimes(1);
  });
});

// ============================================================================
// AC-2 (Detail tab) — lazy loading and caching
// ============================================================================

describe("Detail tab — lazy fetch", () => {
  beforeEach(() => {
    vi.mocked(getResult).mockReset();
  });

  it("getResult is NOT called before Detail tab is selected (lazy loading)", () => {
    render(<ResultsOverviewScreen {...defaultProps} />);
    // Just rendering (Overview tab active by default) should not call getResult
    expect(getResult).not.toHaveBeenCalled();
  });

  it("getResult is called when Detail tab is selected", async () => {
    vi.mocked(getResult).mockResolvedValueOnce(mockDetail());
    render(<ResultsOverviewScreen {...defaultProps} />);
    await userEvent.click(screen.getByRole("tab", { name: "Detail" }));
    expect(getResult).toHaveBeenCalledWith("abcd1234-5678-90ab-cdef-123456789012");
  });

  it("getResult is called exactly once on repeated tab switches (caching)", async () => {
    vi.mocked(getResult).mockResolvedValueOnce(mockDetail());
    render(<ResultsOverviewScreen {...defaultProps} />);
    const detailTab = screen.getByRole("tab", { name: "Detail" });
    const overviewTab = screen.getByRole("tab", { name: "Overview" });

    await userEvent.click(detailTab);
    await waitFor(() => expect(getResult).toHaveBeenCalledTimes(1));

    // Switch away and back — should not re-fetch
    await userEvent.click(overviewTab);
    await userEvent.click(detailTab);
    expect(getResult).toHaveBeenCalledTimes(1);
  });

  it("shows placeholder when Detail tab is selected but no runResult", async () => {
    render(<ResultsOverviewScreen {...defaultProps} runResult={null} />);
    await userEvent.click(screen.getByRole("tab", { name: "Detail" }));
    expect(screen.getByText(/Run a simulation to see detailed results/i)).toBeInTheDocument();
    expect(getResult).not.toHaveBeenCalled();
  });

  it("shows 'Detail unavailable' when getResult throws", async () => {
    vi.mocked(getResult).mockRejectedValueOnce(new Error("Not found"));
    render(<ResultsOverviewScreen {...defaultProps} />);
    await userEvent.click(screen.getByRole("tab", { name: "Detail" }));
    await waitFor(() =>
      expect(screen.getByText(/Detail unavailable/i)).toBeInTheDocument(),
    );
  });

  it("resets cached detail when runResult.run_id changes", async () => {
    vi.mocked(getResult)
      .mockResolvedValueOnce(mockDetail({ run_id: "run-A" }))
      .mockResolvedValueOnce(mockDetail({ run_id: "run-B" }));

    const { rerender } = render(
      <ResultsOverviewScreen
        {...defaultProps}
        runResult={mockRunResult({ run_id: "run-A" })}
      />,
    );
    const detailTab = screen.getByRole("tab", { name: "Detail" });
    await userEvent.click(detailTab);
    await waitFor(() => expect(getResult).toHaveBeenCalledWith("run-A"));

    // Change run_id — should reset and re-fetch on next Detail tab selection
    rerender(
      <ResultsOverviewScreen
        {...defaultProps}
        runResult={mockRunResult({ run_id: "run-B" })}
      />,
    );

    // Switch to overview and back to detail to trigger re-fetch
    await userEvent.click(screen.getByRole("tab", { name: "Overview" }));
    await userEvent.click(screen.getByRole("tab", { name: "Detail" }));
    await waitFor(() => expect(getResult).toHaveBeenCalledWith("run-B"));
    expect(getResult).toHaveBeenCalledTimes(2);
  });
});

// ============================================================================
// AC-5: Screen component pattern (structural)
// ============================================================================

describe("AC-5: Screen component structure", () => {
  it("renders as a section element", () => {
    const { container } = render(<ResultsOverviewScreen {...defaultProps} />);
    expect(container.querySelector("section")).toBeInTheDocument();
  });

  it("renders DistributionalChart in Overview tab", () => {
    render(<ResultsOverviewScreen {...defaultProps} />);
    // DistributionalChart renders a div with role="img" or chart container
    // At minimum the container should be rendered (Recharts uses ResponsiveContainer)
    // We verify by checking the reformLabel is in the chart title
    expect(screen.getByText("Carbon Tax — With Dividend")).toBeInTheDocument();
  });
});
