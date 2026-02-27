import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ComparisonView } from "@/components/simulation/ComparisonView";
import { mockDecileData, mockScenarios } from "@/data/mock-data";

describe("ComparisonView", () => {
  it("renders side-by-side table and supports tab switching", async () => {
    render(
      <ComparisonView
        scenarios={mockScenarios}
        selectedScenarioIds={["baseline", "reform-a"]}
        onChangeSelectedScenarioIds={vi.fn()}
        decileData={mockDecileData}
      />,
    );

    expect(screen.getByText(/Side-by-side/i)).toBeInTheDocument();
    expect(screen.getByRole("cell", { name: /^D1$/ })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("tab", { name: /Delta/i }));
    expect(
      await screen.findByRole("columnheader", {
        name: /Delta \(Reform - Baseline\)/i,
      }),
    ).toBeInTheDocument();
  });
});
