// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { DataSourceBrowser } from "@/components/simulation/DataSourceBrowser";
import { mockDataSources } from "@/data/mock-data";

vi.mock("@/api/data-fusion", () => ({
  getDataSourceDetail: vi.fn().mockResolvedValue({
    id: "filosofi_2021_commune",
    provider: "insee",
    name: "Filosofi 2021 Commune",
    description: "detail",
    variable_count: 3,
    record_count: 95_000,
    source_url: "",
    origin: "open-official",
    access_mode: "bundled",
    trust_status: "production-safe",
    data_class: "structural",
    columns: [
      { name: "commune_code", type: "string", description: "Commune code" },
      { name: "income_decile", type: "integer", description: "Income decile" },
      { name: "disposable_income", type: "float", description: "Disposable income" },
    ],
  }),
}));

describe("DataSourceBrowser", () => {
  const noop = () => {};

  it("renders datasets grouped by provider (AC-1)", () => {
    render(
      <DataSourceBrowser sources={mockDataSources} selectedIds={[]} onToggleSource={noop} />,
    );

    expect(screen.getByText("INSEE")).toBeInTheDocument();
    expect(screen.getByText("Eurostat")).toBeInTheDocument();
    expect(screen.getByText("ADEME")).toBeInTheDocument();
    expect(screen.getByText("SDES")).toBeInTheDocument();
  });

  it("shows dataset name and description for each dataset (AC-1)", () => {
    render(
      <DataSourceBrowser sources={mockDataSources} selectedIds={[]} onToggleSource={noop} />,
    );

    expect(screen.getByText(/Filosofi 2021 Commune/)).toBeInTheDocument();
    expect(screen.getByText(/Vehicle Fleet/)).toBeInTheDocument();
  });

  it("shows variable count badge for datasets (AC-1)", () => {
    render(
      <DataSourceBrowser sources={mockDataSources} selectedIds={[]} onToggleSource={noop} />,
    );

    expect(screen.getAllByText(/\d+ variables/).length).toBeGreaterThan(0);
  });

  it("shows selected state when a dataset is in selectedIds (AC-2)", () => {
    render(
      <DataSourceBrowser
        sources={mockDataSources}
        selectedIds={[{ provider: "insee", dataset_id: "filosofi_2021_commune" }]}
        onToggleSource={noop}
      />,
    );

    const selectedButton = screen.getByRole("button", { pressed: true });
    expect(selectedButton).toBeInTheDocument();
  });

  it("calls onToggleSource with provider and dataset_id when clicked (AC-2)", () => {
    const onToggle = vi.fn();
    render(
      <DataSourceBrowser sources={mockDataSources} selectedIds={[]} onToggleSource={onToggle} />,
    );

    const buttons = screen.getAllByRole("button", { pressed: false });
    fireEvent.click(buttons[0]);
    expect(onToggle).toHaveBeenCalledTimes(1);
    expect(onToggle).toHaveBeenCalledWith(expect.any(String), expect.any(String));
  });

  it("filters datasets by search query", () => {
    render(
      <DataSourceBrowser sources={mockDataSources} selectedIds={[]} onToggleSource={noop} />,
    );

    const input = screen.getByPlaceholderText(/filter datasets/i);
    fireEvent.change(input, { target: { value: "vehicle" } });

    expect(screen.getByText(/Vehicle Fleet/)).toBeInTheDocument();
    expect(screen.queryByText(/Filosofi 2021 Commune/)).not.toBeInTheDocument();
  });

  it("shows source row counts and columns inside Inspect panel", async () => {
    const user = userEvent.setup();
    render(
      <DataSourceBrowser sources={mockDataSources} selectedIds={[]} onToggleSource={noop} />,
    );

    const inspectButtons = screen.getAllByRole("button", { name: /inspect columns/i });
    await user.click(inspectButtons[0]);

    await waitFor(() => {
      expect(screen.getByText("95,000 rows")).toBeInTheDocument();
    });
    expect(screen.getByText("3 columns")).toBeInTheDocument();
    expect(screen.getByText("commune_code")).toBeInTheDocument();
    expect(screen.getByText("income_decile")).toBeInTheDocument();
  });
});
