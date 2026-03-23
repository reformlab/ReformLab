// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { render, screen, fireEvent } from "@testing-library/react";

import { YearScheduleEditor } from "@/components/simulation/YearScheduleEditor";

describe("YearScheduleEditor", () => {
  it("renders existing schedule rows (AC-4)", () => {
    render(
      <YearScheduleEditor
        schedule={{ 2025: 50, 2026: 60 }}
        onChange={() => {}}
      />,
    );

    expect(screen.getByDisplayValue("2025")).toBeInTheDocument();
    expect(screen.getByDisplayValue("50")).toBeInTheDocument();
    expect(screen.getByDisplayValue("2026")).toBeInTheDocument();
    expect(screen.getByDisplayValue("60")).toBeInTheDocument();
  });

  it("shows Add Year button (AC-4)", () => {
    render(<YearScheduleEditor schedule={{}} onChange={() => {}} />);
    expect(screen.getByText(/Add Year/i)).toBeInTheDocument();
  });

  it("adds a new year row when Add Year clicked (AC-4)", () => {
    render(<YearScheduleEditor schedule={{ 2025: 50 }} onChange={() => {}} />);

    const before = screen.getAllByRole("textbox").length;
    fireEvent.click(screen.getByText(/Add Year/i));
    const after = screen.getAllByRole("textbox").length;
    expect(after).toBeGreaterThan(before);
  });

  it("removes a year row when remove button clicked (AC-4)", () => {
    render(
      <YearScheduleEditor
        schedule={{ 2025: 50, 2026: 60 }}
        onChange={() => {}}
      />,
    );

    const removeButtons = screen.getAllByTitle("Remove row");
    expect(removeButtons.length).toBe(2);
    fireEvent.click(removeButtons[0]);
    expect(screen.getAllByTitle("Remove row").length).toBe(1);
  });

  it("shows inline error for duplicate year (AC-4)", () => {
    render(
      <YearScheduleEditor
        schedule={{ 2025: 50, 2026: 60 }}
        onChange={() => {}}
      />,
    );

    // Change second row year to match first
    const yearInputs = screen.getAllByPlaceholderText("2025");
    fireEvent.change(yearInputs[1], { target: { value: "2025" } });
    expect(screen.getAllByText(/Duplicate year/i).length).toBeGreaterThan(0);
  });

  it("shows inline error for non-numeric value (AC-4)", () => {
    render(
      <YearScheduleEditor
        schedule={{ 2025: 50 }}
        onChange={() => {}}
      />,
    );

    const valueInput = screen.getByDisplayValue("50");
    fireEvent.change(valueInput, { target: { value: "abc" } });
    expect(screen.getByText(/Must be a number/i)).toBeInTheDocument();
  });

  it("calls onChange with updated schedule when valid values entered (AC-4)", () => {
    const onChange = vi.fn();
    render(
      <YearScheduleEditor
        schedule={{ 2025: 50 }}
        onChange={onChange}
      />,
    );

    const valueInput = screen.getByDisplayValue("50");
    fireEvent.change(valueInput, { target: { value: "75" } });
    expect(onChange).toHaveBeenCalledWith({ 2025: 75 });
  });

  it("shows unit in column header when provided (AC-4)", () => {
    render(
      <YearScheduleEditor
        schedule={{ 2025: 50 }}
        onChange={() => {}}
        unit="EUR/tCO2"
      />,
    );

    expect(screen.getByText(/EUR\/tCO2/)).toBeInTheDocument();
  });
});
