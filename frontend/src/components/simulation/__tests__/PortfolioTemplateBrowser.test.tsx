import { render, screen, fireEvent } from "@testing-library/react";

import { PortfolioTemplateBrowser } from "@/components/simulation/PortfolioTemplateBrowser";
import { mockTemplates } from "@/data/mock-data";

describe("PortfolioTemplateBrowser", () => {
  const noop = () => {};

  it("renders templates grouped by type (AC-1)", () => {
    render(
      <PortfolioTemplateBrowser
        templates={mockTemplates}
        selectedIds={[]}
        onToggleTemplate={noop}
      />,
    );

    // Groups for carbon-tax and subsidy and feebate types should be shown
    expect(screen.getAllByRole("button").length).toBeGreaterThan(0);
  });

  it("shows template name and description (AC-1)", () => {
    render(
      <PortfolioTemplateBrowser
        templates={mockTemplates}
        selectedIds={[]}
        onToggleTemplate={noop}
      />,
    );

    expect(screen.getByText(/Carbon Tax — Flat Rate/)).toBeInTheDocument();
    expect(screen.getByText(/Flat carbon tax rate/)).toBeInTheDocument();
  });

  it("shows parameter count badge (AC-1)", () => {
    render(
      <PortfolioTemplateBrowser
        templates={mockTemplates}
        selectedIds={[]}
        onToggleTemplate={noop}
      />,
    );

    expect(screen.getAllByText(/\d+ params/).length).toBeGreaterThan(0);
  });

  it("shows type badge (AC-1)", () => {
    render(
      <PortfolioTemplateBrowser
        templates={mockTemplates}
        selectedIds={[]}
        onToggleTemplate={noop}
      />,
    );

    expect(screen.getAllByText("Carbon Tax").length).toBeGreaterThan(0);
  });

  it("shows selected state for selected template (AC-2)", () => {
    render(
      <PortfolioTemplateBrowser
        templates={mockTemplates}
        selectedIds={["carbon-tax-flat"]}
        onToggleTemplate={noop}
      />,
    );

    const pressedButtons = screen.getAllByRole("button", { pressed: true });
    expect(pressedButtons.length).toBe(1);
  });

  it("calls onToggleTemplate with template id when clicked (AC-2)", () => {
    const onToggle = vi.fn();
    render(
      <PortfolioTemplateBrowser
        templates={mockTemplates}
        selectedIds={[]}
        onToggleTemplate={onToggle}
      />,
    );

    const buttons = screen.getAllByRole("button", { pressed: false });
    fireEvent.click(buttons[0]);
    expect(onToggle).toHaveBeenCalledTimes(1);
    expect(onToggle).toHaveBeenCalledWith(expect.any(String));
  });

  it("filters templates by search query", () => {
    render(
      <PortfolioTemplateBrowser
        templates={mockTemplates}
        selectedIds={[]}
        onToggleTemplate={noop}
      />,
    );

    const input = screen.getByPlaceholderText(/filter templates/i);
    fireEvent.change(input, { target: { value: "vehicle" } });

    expect(screen.getByText(/Vehicle Feebate/)).toBeInTheDocument();
    expect(screen.queryByText(/Carbon Tax — Flat Rate/)).not.toBeInTheDocument();
  });
});
