// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { render, screen, fireEvent } from "@testing-library/react";

import { PortfolioCompositionPanel } from "@/components/simulation/PortfolioCompositionPanel";
import type { CompositionEntry } from "@/components/simulation/PortfolioCompositionPanel";
import { mockTemplates } from "@/data/mock-data";

const baseEntry = (id: string): CompositionEntry => ({
  templateId: id,
  name: mockTemplates.find((t) => t.id === id)?.name ?? id,
  parameters: {},
  rateSchedule: {},
});

describe("PortfolioCompositionPanel", () => {
  it("shows empty state when no templates selected (AC-2)", () => {
    render(
      <PortfolioCompositionPanel
        templates={mockTemplates}
        composition={[]}
        onReorder={() => {}}
        onRemove={() => {}}
        onParameterChange={() => {}}
        onRateScheduleChange={() => {}}
      />,
    );

    expect(screen.getByText(/Select templates/)).toBeInTheDocument();
  });

  it("shows 'at least 2 policies' hint when fewer than 2 selected (AC-2)", () => {
    render(
      <PortfolioCompositionPanel
        templates={mockTemplates}
        composition={[baseEntry("carbon-tax-flat")]}
        onReorder={() => {}}
        onRemove={() => {}}
        onParameterChange={() => {}}
        onRateScheduleChange={() => {}}
      />,
    );

    expect(screen.getAllByText(/at least 2 policies/i).length).toBeGreaterThan(0);
  });

  it("renders each composition entry as a card (AC-2)", () => {
    render(
      <PortfolioCompositionPanel
        templates={mockTemplates}
        composition={[
          baseEntry("carbon-tax-flat"),
          baseEntry("subsidy-energy"),
        ]}
        onReorder={() => {}}
        onRemove={() => {}}
        onParameterChange={() => {}}
        onRateScheduleChange={() => {}}
      />,
    );

    expect(screen.getByText(/Carbon Tax — Flat Rate/)).toBeInTheDocument();
    expect(screen.getByText(/Energy Efficiency Subsidy/)).toBeInTheDocument();
  });

  it("move-up disabled for first item (AC-3)", () => {
    render(
      <PortfolioCompositionPanel
        templates={mockTemplates}
        composition={[
          baseEntry("carbon-tax-flat"),
          baseEntry("subsidy-energy"),
        ]}
        onReorder={() => {}}
        onRemove={() => {}}
        onParameterChange={() => {}}
        onRateScheduleChange={() => {}}
      />,
    );

    const moveUpButtons = screen.getAllByLabelText("Move up");
    expect(moveUpButtons[0]).toBeDisabled();
    expect(moveUpButtons[1]).not.toBeDisabled();
  });

  it("move-down disabled for last item (AC-3)", () => {
    render(
      <PortfolioCompositionPanel
        templates={mockTemplates}
        composition={[
          baseEntry("carbon-tax-flat"),
          baseEntry("subsidy-energy"),
        ]}
        onReorder={() => {}}
        onRemove={() => {}}
        onParameterChange={() => {}}
        onRateScheduleChange={() => {}}
      />,
    );

    const moveDownButtons = screen.getAllByLabelText("Move down");
    expect(moveDownButtons[0]).not.toBeDisabled();
    expect(moveDownButtons[1]).toBeDisabled();
  });

  it("calls onReorder when move-down clicked (AC-3)", () => {
    const onReorder = vi.fn();
    render(
      <PortfolioCompositionPanel
        templates={mockTemplates}
        composition={[
          baseEntry("carbon-tax-flat"),
          baseEntry("subsidy-energy"),
        ]}
        onReorder={onReorder}
        onRemove={() => {}}
        onParameterChange={() => {}}
        onRateScheduleChange={() => {}}
      />,
    );

    const moveDownButtons = screen.getAllByLabelText("Move down");
    fireEvent.click(moveDownButtons[0]);
    expect(onReorder).toHaveBeenCalledWith(0, 1);
  });

  it("calls onRemove when remove button clicked (AC-3)", () => {
    const onRemove = vi.fn();
    render(
      <PortfolioCompositionPanel
        templates={mockTemplates}
        composition={[
          baseEntry("carbon-tax-flat"),
          baseEntry("subsidy-energy"),
        ]}
        onReorder={() => {}}
        onRemove={onRemove}
        onParameterChange={() => {}}
        onRateScheduleChange={() => {}}
      />,
    );

    const removeButtons = screen.getAllByLabelText("Remove policy");
    fireEvent.click(removeButtons[0]);
    expect(onRemove).toHaveBeenCalledWith(0);
  });

  it("expands parameter editor when expand button clicked (AC-2)", () => {
    render(
      <PortfolioCompositionPanel
        templates={mockTemplates}
        composition={[
          baseEntry("carbon-tax-flat"),
          baseEntry("subsidy-energy"),
        ]}
        onReorder={() => {}}
        onRemove={() => {}}
        onParameterChange={() => {}}
        onRateScheduleChange={() => {}}
        parameterSchemas={{
          "carbon-tax-flat": [
            { id: "tax_rate", label: "Tax Rate", value: 44, baseline: 44, unit: "%", group: "Tax Rates", type: "slider", min: 0, max: 200 },
          ],
        }}
      />,
    );

    const expandButtons = screen.getAllByLabelText("Expand parameters");
    fireEvent.click(expandButtons[0]);
    expect(screen.getByText("Tax Rate")).toBeInTheDocument();
  });
});
