import { render, screen } from "@testing-library/react";

import { DistributionalChart } from "@/components/simulation/DistributionalChart";
import { mockDecileData } from "@/data/mock-data";

// Recharts uses ResizeObserver which jsdom doesn't support
beforeAll(() => {
  globalThis.ResizeObserver ??= class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

describe("DistributionalChart", () => {
  it("renders the chart title", () => {
    render(<DistributionalChart data={mockDecileData} />);
    expect(screen.getByText("Income Decile Impact (EUR/year)")).toBeInTheDocument();
  });

  it("renders with a custom reform label without crashing", () => {
    // Recharts Legend text isn't reliably queryable in jsdom,
    // so we verify the component accepts the prop and renders without error
    render(<DistributionalChart data={mockDecileData} reformLabel="Carbon Tax" />);
    expect(screen.getByText("Income Decile Impact (EUR/year)")).toBeInTheDocument();
  });

  it("renders with empty data without crashing", () => {
    render(<DistributionalChart data={[]} />);
    expect(screen.getByText("Income Decile Impact (EUR/year)")).toBeInTheDocument();
  });
});
