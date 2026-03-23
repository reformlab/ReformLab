// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { VariableOverlapView } from "@/components/simulation/VariableOverlapView";
import { mockDataSources } from "@/data/mock-data";

vi.mock("@/api/data-fusion", () => ({
  getDataSourceDetail: vi.fn().mockResolvedValue({
    id: "test",
    provider: "insee",
    name: "Test",
    description: "Test",
    variable_count: 2,
    record_count: null,
    source_url: "",
    columns: [],
  }),
}));

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

  it("renders when 2 or more sources are selected (AC-2)", async () => {
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
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
  });

  it("shows both dataset names when 2 sources are selected (AC-2)", async () => {
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
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
  });

  it("shows informational message about merge method selection (AC-2)", async () => {
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
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
  });

  it("shows overlapping columns when sources share variables (AC-2)", async () => {
    const { getDataSourceDetail } = await import("@/api/data-fusion");
    const mockFn = vi.mocked(getDataSourceDetail);
    mockFn.mockImplementation(async (_provider, datasetId) => ({
      id: datasetId,
      provider: _provider,
      name: datasetId,
      description: "",
      variable_count: 2,
      record_count: null,
      source_url: "",
      columns: [
        { name: "commune_code", type: "string", description: "Commune code" },
        { name: datasetId === "filosofi_2021_commune" ? "median_income" : "fleet_count", type: "float", description: "" },
      ],
    }));

    render(
      <VariableOverlapView
        sources={mockDataSources}
        selectedSources={[
          { provider: "insee", dataset_id: "filosofi_2021_commune" },
          { provider: "sdes", dataset_id: "vehicle_fleet" },
        ]}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText(/1 shared variable/)).toBeInTheDocument();
    });
    // commune_code appears in both overlap badge and source cards
    expect(screen.getAllByText("commune_code").length).toBeGreaterThanOrEqual(1);
  });
});
