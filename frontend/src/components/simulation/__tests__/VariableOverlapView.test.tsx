import { render, screen } from "@testing-library/react";

import { VariableOverlapView } from "@/components/simulation/VariableOverlapView";
import { mockDataSources } from "@/data/mock-data";

describe("VariableOverlapView", () => {
  it("renders nothing when fewer than 2 sources selected (AC-2)", () => {
    const { container } = render(
      <VariableOverlapView
        sources={mockDataSources}
        selectedSources={[{ provider: "insee", dataset_id: "filosofi_2021_commune" }]}
      />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("renders when 2 or more sources are selected (AC-2)", () => {
    render(
      <VariableOverlapView
        sources={mockDataSources}
        selectedSources={[
          { provider: "insee", dataset_id: "filosofi_2021_commune" },
          { provider: "sdes", dataset_id: "vehicle_fleet" },
        ]}
      />,
    );

    expect(screen.getByRole("region", { name: /variable overlap/i })).toBeInTheDocument();
  });

  it("shows both dataset names when 2 sources are selected (AC-2)", () => {
    render(
      <VariableOverlapView
        sources={mockDataSources}
        selectedSources={[
          { provider: "insee", dataset_id: "filosofi_2021_commune" },
          { provider: "sdes", dataset_id: "vehicle_fleet" },
        ]}
      />,
    );

    expect(screen.getByText(/Filosofi 2021 Commune/)).toBeInTheDocument();
    expect(screen.getByText(/Vehicle Fleet/)).toBeInTheDocument();
  });

  it("shows informational message about merge method selection (AC-2)", () => {
    render(
      <VariableOverlapView
        sources={mockDataSources}
        selectedSources={[
          { provider: "insee", dataset_id: "filosofi_2021_commune" },
          { provider: "sdes", dataset_id: "vehicle_fleet" },
        ]}
      />,
    );

    expect(screen.getByText(/2 sources selected/)).toBeInTheDocument();
  });
});
