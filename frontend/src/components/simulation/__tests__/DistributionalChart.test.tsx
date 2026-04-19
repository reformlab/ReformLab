// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { render, screen, waitFor } from "@testing-library/react";

import { DistributionalChart } from "@/components/simulation/DistributionalChart";
import { mockDecileData } from "@/data/mock-data";
import {
  renderedBarShapes,
  setupRechartsResponsiveContainerMock,
} from "./recharts-test-utils";

setupRechartsResponsiveContainerMock();

describe("DistributionalChart", () => {
  it("renders the chart title", () => {
    render(<DistributionalChart data={mockDecileData} />);
    expect(screen.getByText("Income Decile Impact (EUR/year)")).toBeInTheDocument();
  });

  it("renders SVG bars for the baseline and reform series", async () => {
    const { container } = render(<DistributionalChart data={mockDecileData} />);

    await waitFor(() => {
      const bars = renderedBarShapes(container);
      expect(bars.length).toBeGreaterThanOrEqual(mockDecileData.length * 2);
    });
  });

  it("renders decile labels on the X axis", async () => {
    const { container } = render(<DistributionalChart data={mockDecileData} />);

    await waitFor(() => {
      const labels = Array.from(container.querySelectorAll("svg text")).map(
        (node) => node.textContent,
      );

      expect(labels).toContain("D1");
      expect(labels).toContain("D10");
    });
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
