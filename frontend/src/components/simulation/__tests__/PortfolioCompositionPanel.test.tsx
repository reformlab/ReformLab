// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { render, screen, fireEvent } from "@testing-library/react";

import { PortfolioCompositionPanel } from "@/components/simulation/PortfolioCompositionPanel";
import type { CompositionEntry } from "@/components/simulation/PortfolioCompositionPanel";
import { mockTemplates } from "@/data/mock-data";
import type { Category } from "@/api/types";

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

  it("does not show minimum-policies hint when 1 policy is present (default minimumPolicies=1)", () => {
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

    expect(screen.queryByText(/at least/i)).not.toBeInTheDocument();
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

// ============================================================================
// Story 25.2: Category badges and duplicate instances
// ============================================================================

describe("Story 25.2: PortfolioCompositionPanel", () => {
  describe("Category badges in composition panel (AC-4)", () => {
    const mockCategories = [
      {
        id: "carbon",
        label: "Carbon Pricing",
        columns: ["carbon_tax"],
        compatible_types: ["carbon_tax"],
        formula_explanation: "carbon_emissions × rate",
        description: "Carbon-based pricing policies",
      },
    ];

    it("should display category badge when categories prop provided", () => {
      const templatesWithCategory = [
        {
          id: "carbon-tax-with-category",
          name: "Carbon Tax — With Category",
          type: "carbon-tax",
          parameterCount: 4,
          description: "Carbon tax with category",
          parameterGroups: ["Tax Rates"],
          is_custom: false,
          runtime_availability: "live_ready" as const,
          availability_reason: null,
          category_id: "carbon",
        },
      ];

      const { container } = render(
        <PortfolioCompositionPanel
          templates={templatesWithCategory}
          composition={[baseEntry("carbon-tax-with-category")]}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          categories={mockCategories}
        />,
      );

      // Category badge should appear with neutral slate color
      const categoryBadge = container.querySelector('.bg-slate-100.text-slate-800');
      expect(categoryBadge).toBeInTheDocument();
      expect(categoryBadge).toHaveTextContent("Carbon Pricing");
    });

    it("should hide category badge when template has no category_id", () => {
      const templatesWithoutCategory = [
        {
          id: "carbon-tax-no-category",
          name: "Carbon Tax — No Category",
          type: "carbon-tax",
          parameterCount: 4,
          description: "Carbon tax without category",
          parameterGroups: ["Tax Rates"],
          is_custom: false,
          runtime_availability: "live_ready" as const,
          availability_reason: null,
        },
      ];

      const { container } = render(
        <PortfolioCompositionPanel
          templates={templatesWithoutCategory}
          composition={[baseEntry("carbon-tax-no-category")]}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          categories={mockCategories}
        />,
      );

      // No category badge should be rendered
      const categoryBadges = container.querySelectorAll('.bg-slate-100.text-slate-800');
      expect(categoryBadges.length).toBe(0);
    });

    it("should hide category badge when categories prop is null", () => {
      const templatesWithCategory = [
        {
          id: "carbon-tax-with-category",
          name: "Carbon Tax — With Category",
          type: "carbon-tax",
          parameterCount: 4,
          description: "Carbon tax with category",
          parameterGroups: ["Tax Rates"],
          is_custom: false,
          runtime_availability: "live_ready" as const,
          availability_reason: null,
          category_id: "carbon",
        },
      ];

      const { container } = render(
        <PortfolioCompositionPanel
          templates={templatesWithCategory}
          composition={[baseEntry("carbon-tax-with-category")]}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          categories={null}
        />,
      );

      // No category badge should be rendered
      const categoryBadges = container.querySelectorAll('.bg-slate-100.text-slate-800');
      expect(categoryBadges.length).toBe(0);
    });

    it("should show formula help icon when category exists", () => {
      const templatesWithCategory = [
        {
          id: "carbon-tax-with-category",
          name: "Carbon Tax — With Category",
          type: "carbon-tax",
          parameterCount: 4,
          description: "Carbon tax with category",
          parameterGroups: ["Tax Rates"],
          is_custom: false,
          runtime_availability: "live_ready" as const,
          availability_reason: null,
          category_id: "carbon",
        },
      ];

      const { container } = render(
        <PortfolioCompositionPanel
          templates={templatesWithCategory}
          composition={[baseEntry("carbon-tax-with-category")]}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          categories={mockCategories}
        />,
      );

      // CircleHelp icon should be present
      const helpIcon = container.querySelector('button[aria-label*="Formula help"]');
      expect(helpIcon).toBeInTheDocument();
    });
  });

  describe("instanceId support (AC-5, AC-6)", () => {
    it("should support instanceId in CompositionEntry", () => {
      const entryWithInstanceId: CompositionEntry = {
        templateId: "carbon-tax-flat",
        name: "Carbon Tax",
        parameters: {},
        rateSchedule: {},
        instanceId: "carbon-tax-flat-ins0",
      };

      const { container } = render(
        <PortfolioCompositionPanel
          templates={mockTemplates}
          composition={[entryWithInstanceId]}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
        />,
      );

      // Verify the card is rendered using instanceId
      const card = container.querySelector('.border-slate-200');
      expect(card).toBeInTheDocument();
      expect(container.textContent).toContain("8 params");
    });

    it("should use instanceId as key when provided", () => {
      const entriesWithSameTemplate: CompositionEntry[] = [
        {
          templateId: "carbon-tax-flat",
          name: "Carbon Tax 1",
          parameters: {},
          rateSchedule: {},
          instanceId: "carbon-tax-flat-ins0",
        },
        {
          templateId: "carbon-tax-flat",
          name: "Carbon Tax 2",
          parameters: {},
          rateSchedule: {},
          instanceId: "carbon-tax-flat-ins1",
        },
      ];

      const { container } = render(
        <PortfolioCompositionPanel
          templates={mockTemplates}
          composition={entriesWithSameTemplate}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
        />,
      );

      // Both entries should be rendered
      expect(screen.getByText("Carbon Tax 1")).toBeInTheDocument();
      expect(screen.getByText("Carbon Tax 2")).toBeInTheDocument();

      // Should have 2 cards
      const cards = container.querySelectorAll('section[aria-label="Portfolio composition"] > div');
      expect(cards.length).toBe(2);
    });
  });
});
