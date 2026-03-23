// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ParameterRow } from "@/components/simulation/ParameterRow";
import type { Parameter } from "@/data/mock-data";

const sliderParam: Parameter = {
  id: "tax_rate",
  label: "Carbon tax rate",
  value: 44,
  baseline: 44,
  unit: "EUR/tCO2",
  group: "Tax Rates",
  type: "slider",
  min: 0,
  max: 200,
};

const percentParam: Parameter = {
  id: "rebate_rate",
  label: "Rebate rate",
  value: 0.15,
  baseline: 0.15,
  unit: "%",
  group: "Redistribution",
  type: "slider",
  min: 0,
  max: 1,
};

const numberParam: Parameter = {
  id: "tax_rate_growth",
  label: "Annual rate increase",
  value: 10,
  baseline: 10,
  unit: "EUR/yr",
  group: "Tax Rates",
  type: "number",
};

// Radix Slider uses ResizeObserver internally
beforeAll(() => {
  globalThis.ResizeObserver ??= class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

describe("ParameterRow", () => {
  it("renders parameter label and baseline value", () => {
    render(<ParameterRow parameter={sliderParam} value={44} onChange={vi.fn()} />);

    expect(screen.getByText("Carbon tax rate")).toBeInTheDocument();
    expect(screen.getByText(/Baseline/)).toBeInTheDocument();
    expect(screen.getAllByText("44 EUR/tCO2")).toHaveLength(2); // baseline label + current value
  });

  it("shows 'Unchanged' badge when value equals baseline", () => {
    render(<ParameterRow parameter={sliderParam} value={44} onChange={vi.fn()} />);
    expect(screen.getByText("Unchanged")).toBeInTheDocument();
  });

  it("shows delta badge when value differs from baseline", () => {
    render(<ParameterRow parameter={sliderParam} value={60} onChange={vi.fn()} />);
    expect(screen.getByText("+16")).toBeInTheDocument();
    expect(screen.queryByText("Unchanged")).not.toBeInTheDocument();
  });

  it("formats percentage values correctly", () => {
    render(<ParameterRow parameter={percentParam} value={0.25} onChange={vi.fn()} />);
    expect(screen.getByText("25%")).toBeInTheDocument();
    expect(screen.getByText("+10%")).toBeInTheDocument();
  });

  it("toggles edit mode and shows input when Edit is clicked", async () => {
    render(<ParameterRow parameter={sliderParam} value={44} onChange={vi.fn()} />);

    expect(screen.queryByLabelText(/Input Carbon tax rate/i)).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /Edit/i }));
    expect(screen.getByLabelText(/Input Carbon tax rate/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Done/i })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /Done/i }));
    expect(screen.queryByLabelText(/Input Carbon tax rate/i)).not.toBeInTheDocument();
  });

  it("does not render slider for number-type parameters in edit mode", async () => {
    render(<ParameterRow parameter={numberParam} value={10} onChange={vi.fn()} />);

    await userEvent.click(screen.getByRole("button", { name: /Edit/i }));
    expect(screen.getByLabelText(/Input Annual rate increase/i)).toBeInTheDocument();
    expect(screen.queryByRole("slider")).not.toBeInTheDocument();
  });

  it("calls onChange when input value changes", async () => {
    const onChange = vi.fn();
    render(<ParameterRow parameter={numberParam} value={10} onChange={onChange} />);

    await userEvent.click(screen.getByRole("button", { name: /Edit/i }));
    const input = screen.getByLabelText(/Input Annual rate increase/i);
    await userEvent.clear(input);
    await userEvent.type(input, "20");
    expect(onChange).toHaveBeenCalled();
  });

  it("shows negative delta for percentage parameters", () => {
    render(<ParameterRow parameter={percentParam} value={0.05} onChange={vi.fn()} />);
    expect(screen.getByText("5%")).toBeInTheDocument();
    expect(screen.getByText("-10%")).toBeInTheDocument();
  });
});
