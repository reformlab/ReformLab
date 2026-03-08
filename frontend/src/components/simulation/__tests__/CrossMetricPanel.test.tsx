import { render, screen } from "@testing-library/react";

import { CrossMetricPanel } from "@/components/simulation/CrossMetricPanel";
import type { CrossMetricItem } from "@/api/types";

const mockMetrics: CrossMetricItem[] = [
  {
    criterion: "max_fiscal_revenue",
    best_portfolio: "Run A",
    value: 6900000000,
    all_values: { "Run A": 6900000000, "Run B": 6000000000 },
  },
  {
    criterion: "min_fiscal_cost",
    best_portfolio: "Run B",
    value: 0,
    all_values: { "Run A": 0, "Run B": 0 },
  },
  {
    criterion: "max_fiscal_balance",
    best_portfolio: "Run A",
    value: 6900000000,
    all_values: { "Run A": 6900000000, "Run B": 6000000000 },
  },
];

describe("CrossMetricPanel", () => {
  it("renders panel title", () => {
    render(<CrossMetricPanel metrics={mockMetrics} />);
    expect(screen.getByText("Cross-Portfolio Rankings")).toBeInTheDocument();
  });

  it("renders human-readable criterion labels", () => {
    render(<CrossMetricPanel metrics={mockMetrics} />);
    expect(screen.getByText("Max Fiscal Revenue")).toBeInTheDocument();
    expect(screen.getByText("Min Fiscal Cost")).toBeInTheDocument();
    expect(screen.getByText("Max Fiscal Balance")).toBeInTheDocument();
  });

  it("shows best portfolio name for each metric", () => {
    render(<CrossMetricPanel metrics={mockMetrics} />);
    // Run A is best for max_fiscal_revenue and max_fiscal_balance
    const runAOccurrences = screen.getAllByText("Run A");
    expect(runAOccurrences.length).toBeGreaterThan(0);
  });

  it("renders nothing when metrics is empty", () => {
    const { container } = render(<CrossMetricPanel metrics={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it("formats large values with suffix", () => {
    render(<CrossMetricPanel metrics={mockMetrics} />);
    // 6900000000 → "6.9B"
    const formatted = screen.getAllByText("6.9B");
    expect(formatted.length).toBeGreaterThan(0);
  });

  it("renders all metric cards", () => {
    render(<CrossMetricPanel metrics={mockMetrics} />);
    // Each metric contributes its human-readable label
    expect(screen.getByText("Max Fiscal Revenue")).toBeInTheDocument();
    expect(screen.getByText("Min Fiscal Cost")).toBeInTheDocument();
    expect(screen.getByText("Max Fiscal Balance")).toBeInTheDocument();
  });

  it("falls back to raw criterion name for unknown keys", () => {
    const unknown: CrossMetricItem[] = [
      {
        criterion: "some_custom_metric",
        best_portfolio: "X",
        value: 42,
        all_values: { X: 42 },
      },
    ];
    render(<CrossMetricPanel metrics={unknown} />);
    expect(screen.getByText("some_custom_metric")).toBeInTheDocument();
  });
});
