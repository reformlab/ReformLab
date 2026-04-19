// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { render, screen, waitFor } from "@testing-library/react";

import { PopulationDistributionChart } from "@/components/simulation/PopulationDistributionChart";
import {
  renderedBarShapes,
  setupRechartsResponsiveContainerMock,
} from "./recharts-test-utils";

setupRechartsResponsiveContainerMock();

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

  it("renders one SVG bar per data point", async () => {
    const { container } = render(
      <PopulationDistributionChart title="Age Distribution" data={mockData} />,
    );

    await waitFor(() => {
      const bars = renderedBarShapes(container);
      expect(bars.length).toBeGreaterThanOrEqual(mockData.length);
    });
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
