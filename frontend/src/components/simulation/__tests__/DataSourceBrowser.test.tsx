import { render, screen, fireEvent } from "@testing-library/react";

import { DataSourceBrowser } from "@/components/simulation/DataSourceBrowser";
import { mockDataSources } from "@/data/mock-data";

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
});
