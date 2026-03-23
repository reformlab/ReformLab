// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { render, screen } from "@testing-library/react";

import { PopulationDistributionChart } from "@/components/simulation/PopulationDistributionChart";

// Recharts uses ResizeObserver which jsdom doesn't support
beforeAll(() => {
  globalThis.ResizeObserver ??= class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

const mockData = [
  { name: "D1", value: 120 },
  { name: "D2", value: 340 },
  { name: "D3", value: 210 },
];

describe("PopulationDistributionChart", () => {
  it("renders the chart title (AC-2)", () => {
    render(<PopulationDistributionChart title="Age Distribution" data={mockData} />);
    expect(screen.getByText("Age Distribution")).toBeInTheDocument();
  });

  it("returns null for empty data", () => {
    const { container } = render(
      <PopulationDistributionChart title="Empty" data={[]} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("container has rounded-lg class (AC-3)", () => {
    const { container } = render(
      <PopulationDistributionChart title="Age Distribution" data={mockData} />,
    );
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveClass("rounded-lg");
  });
});
