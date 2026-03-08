import { render, screen } from "@testing-library/react";

import {
  MultiRunChart,
  columnarToRows,
  type SeriesSpec,
} from "@/components/simulation/MultiRunChart";

// Recharts uses ResizeObserver which jsdom doesn't support
beforeAll(() => {
  globalThis.ResizeObserver ??= class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

const mockSeries: SeriesSpec[] = [
  { key: "Run A", label: "Run A" },
  { key: "Run B", label: "Run B" },
];

const mockData = [
  { decile: 1, "Run A": -120, "Run B": -80, "delta_Run B": 40 },
  { decile: 2, "Run A": -180, "Run B": -150, "delta_Run B": 30 },
  { decile: 3, "Run A": -240, "Run B": -210, "delta_Run B": 30 },
];

describe("MultiRunChart", () => {
  describe("rendering", () => {
    it("renders with 2 series without crashing", () => {
      render(<MultiRunChart data={mockData} xKey="decile" series={mockSeries} />);
      // Table should appear
      expect(screen.getByRole("table")).toBeInTheDocument();
    });

    it("renders with 5 series without crashing", () => {
      const fiveSeries: SeriesSpec[] = [
        { key: "A", label: "Run A" },
        { key: "B", label: "Run B" },
        { key: "C", label: "Run C" },
        { key: "D", label: "Run D" },
        { key: "E", label: "Run E" },
      ];
      const data = [{ decile: 1, A: 10, B: 20, C: 30, D: 40, E: 50 }];
      render(<MultiRunChart data={data} xKey="decile" series={fiveSeries} />);
      expect(screen.getByRole("table")).toBeInTheDocument();
    });

    it("renders with empty data without crashing", () => {
      render(<MultiRunChart data={[]} xKey="decile" series={mockSeries} />);
      // Table is hidden when data is empty
      expect(screen.queryByRole("table")).not.toBeInTheDocument();
    });

    it("renders title when provided", () => {
      render(
        <MultiRunChart
          data={mockData}
          xKey="decile"
          series={mockSeries}
          title="Distributional Impact"
        />,
      );
      expect(screen.getByText("Distributional Impact")).toBeInTheDocument();
    });

    it("hides table when showTable is false", () => {
      render(
        <MultiRunChart
          data={mockData}
          xKey="decile"
          series={mockSeries}
          showTable={false}
        />,
      );
      expect(screen.queryByRole("table")).not.toBeInTheDocument();
    });
  });

  describe("absolute mode (default)", () => {
    it("shows xKey column header in table", () => {
      render(<MultiRunChart data={mockData} xKey="decile" series={mockSeries} />);
      expect(screen.getByText("decile")).toBeInTheDocument();
    });

    it("shows series label headers", () => {
      render(<MultiRunChart data={mockData} xKey="decile" series={mockSeries} />);
      const headers = screen.getAllByText("Run A");
      // At least one occurrence (table header)
      expect(headers.length).toBeGreaterThan(0);
    });
  });

  describe("relative mode", () => {
    it("renders without crashing in relative mode", () => {
      const seriesWithDelta: SeriesSpec[] = [
        { key: "Run A", label: "Run A" },
        { key: "Run B", label: "Run B" },
      ];
      render(
        <MultiRunChart
          data={mockData}
          xKey="decile"
          series={seriesWithDelta}
          mode="relative"
        />,
      );
      // Table should render (non-empty data)
      expect(screen.getByRole("table")).toBeInTheDocument();
    });

    it("skips baseline column in relative mode", () => {
      const series: SeriesSpec[] = [
        { key: "Run A", label: "Baseline" },
        { key: "Run B", label: "Reform" },
      ];
      render(
        <MultiRunChart
          data={mockData}
          xKey="decile"
          series={series}
          mode="relative"
        />,
      );
      // In relative mode, baseline column header ("Baseline") should not appear
      expect(screen.queryByText("Baseline")).not.toBeInTheDocument();
    });
  });
});

describe("columnarToRows", () => {
  it("transforms columnar dict to row array", () => {
    const columnar = {
      decile: [1, 2, 3],
      "Run A": [100, 200, 300],
      "Run B": [150, 250, 350],
    };
    const rows = columnarToRows(columnar);
    expect(rows).toHaveLength(3);
    expect(rows[0]).toEqual({ decile: 1, "Run A": 100, "Run B": 150 });
    expect(rows[2]).toEqual({ decile: 3, "Run A": 300, "Run B": 350 });
  });

  it("returns empty array for empty input", () => {
    expect(columnarToRows({})).toEqual([]);
  });

  it("handles single-column input", () => {
    const rows = columnarToRows({ x: [1, 2] });
    expect(rows).toEqual([{ x: 1 }, { x: 2 }]);
  });
});
