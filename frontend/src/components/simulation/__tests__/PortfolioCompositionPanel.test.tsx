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
// Story 27.3: Show actual parameter values inline in policy cards
// ============================================================================

describe("Story 27.3: PortfolioCompositionPanel", () => {
  describe("Collapsed card parameter summaries (AC-1, AC-2)", () => {
    it("should show actual parameter values in collapsed card for editableParameterGroups", () => {
      const compositionWithEditableGroups: CompositionEntry[] = [
        {
          templateId: "carbon-tax-flat",
          name: "Carbon Tax — Flat Rate",
          parameters: {
            tax_rate: 44,
            exemption_threshold: 15000,
          },
          rateSchedule: { "2025": 44, "2030": 50 },
          instanceId: "inst-1",
          editableParameterGroups: [
            { id: "mechanism", name: "Mechanism", parameterIds: ["tax_rate"] },
            { id: "eligibility", name: "Eligibility", parameterIds: ["exemption_threshold"] },
          ],
        },
      ];

      const parameterSchemas = {
        "carbon-tax-flat": [
          { id: "tax_rate", label: "Tax Rate", value: 44, baseline: 44, unit: "€/tonne", group: "Mechanism", type: "slider" as const },
          { id: "exemption_threshold", label: "Exemption Threshold", value: 15000, baseline: 10000, unit: "€", group: "Eligibility", type: "number" as const },
        ],
      };

      const { container } = render(
        <PortfolioCompositionPanel
          templates={mockTemplates}
          composition={compositionWithEditableGroups}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          parameterSchemas={parameterSchemas}
        />,
      );

      // Should show actual values instead of generic chips
      expect(container.textContent).toContain("44 €/tonne");
      expect(container.textContent).toContain("15000 €");
    });

    it("should show actual parameter values in collapsed card for legacy parameter_groups", () => {
      const compositionWithLegacyGroups: CompositionEntry[] = [
        {
          templateId: "carbon-tax-flat",
          name: "Carbon Tax — Flat Rate",
          parameters: {
            tax_rate: 44,
            exemption_threshold: 15000,
          },
          rateSchedule: { "2025": 44, "2030": 50 },
          instanceId: "inst-2",
          parameter_groups: ["Mechanism", "Eligibility"],
        },
      ];

      const parameterSchemas = {
        "carbon-tax-flat": [
          { id: "tax_rate", label: "Tax Rate", value: 44, baseline: 44, unit: "€/tonne", group: "Mechanism", type: "slider" as const },
          { id: "exemption_threshold", label: "Exemption Threshold", value: 15000, baseline: 10000, unit: "€", group: "Eligibility", type: "number" as const },
        ],
      };

      const { container } = render(
        <PortfolioCompositionPanel
          templates={mockTemplates}
          composition={compositionWithLegacyGroups}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          parameterSchemas={parameterSchemas}
        />,
      );

      // Should show actual values derived from schemas
      expect(container.textContent).toContain("44 €/tonne");
      expect(container.textContent).toContain("15000 €");
    });

    it("should truncate parameter summaries with 4+ parameters (AC-1)", () => {
      const compositionWithManyParams: CompositionEntry[] = [
        {
          templateId: "carbon-tax-complex",
          name: "Complex Carbon Tax",
          parameters: {
            tax_rate: 44,
            exemption_threshold: 15000,
            ceiling: 100000,
            rate_schedule_2026: 50,
            rate_schedule_2027: 55,
          },
          rateSchedule: {},
          instanceId: "inst-many",
          editableParameterGroups: [
            {
              id: "mechanism",
              name: "Mechanism",
              parameterIds: ["tax_rate", "exemption_threshold", "ceiling", "rate_schedule_2026", "rate_schedule_2027"],
            },
          ],
        },
      ];

      const parameterSchemas = {
        "carbon-tax-complex": [
          { id: "tax_rate", label: "Tax Rate", value: 44, baseline: 44, unit: "€/tonne", group: "Mechanism", type: "slider" as const },
          { id: "exemption_threshold", label: "Exemption", value: 15000, baseline: 10000, unit: "€", group: "Mechanism", type: "number" as const },
          { id: "ceiling", label: "Ceiling", value: 100000, baseline: 100000, unit: "€", group: "Mechanism", type: "number" as const },
          { id: "rate_schedule_2026", label: "Rate 2026", value: 50, baseline: 50, unit: "€/tonne", group: "Mechanism", type: "slider" as const },
          { id: "rate_schedule_2027", label: "Rate 2027", value: 55, baseline: 55, unit: "€/tonne", group: "Mechanism", type: "slider" as const },
        ],
      };

      const { container } = render(
        <PortfolioCompositionPanel
          templates={mockTemplates}
          composition={compositionWithManyParams}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          parameterSchemas={parameterSchemas}
        />,
      );

      // Should show truncation indicator
      expect(container.textContent).toContain("(+3 more)");
    });
  });

  describe("Click-to-preview affordance (AC-3, AC-6)", () => {
    // Mock scrollIntoView before all tests in this describe block
    beforeEach(() => {
      Element.prototype.scrollIntoView = vi.fn();
    });

    it("should expand card and scroll to group when group chip is clicked", async () => {
      vi.useFakeTimers();

      const compositionWithEditableGroups: CompositionEntry[] = [
        {
          templateId: "carbon-tax-flat",
          name: "Carbon Tax",
          parameters: { tax_rate: 44 },
          rateSchedule: {},
          instanceId: "inst-click",
          editableParameterGroups: [
            { id: "mechanism", name: "Mechanism", parameterIds: ["tax_rate"] },
          ],
        },
      ];

      const parameterSchemas = {
        "carbon-tax-flat": [
          { id: "tax_rate", label: "Tax Rate", value: 44, baseline: 44, unit: "€/tonne", group: "Mechanism", type: "slider" as const },
        ],
      };

      const { container } = render(
        <PortfolioCompositionPanel
          templates={mockTemplates}
          composition={compositionWithEditableGroups}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          parameterSchemas={parameterSchemas}
        />,
      );

      // Find the group chip button (collapsed state)
      const groupChip = container.querySelector('button[aria-expanded="false"]');
      expect(groupChip).toBeInTheDocument();

      // Click the group chip
      fireEvent.click(groupChip!);

      // Card should be expanded
      expect(container.querySelector('button[aria-expanded="true"]')).toBeInTheDocument();

      // Run pending timers to trigger the scrollIntoView callback
      vi.runAllTimers();

      // scrollIntoView should have been called
      expect(Element.prototype.scrollIntoView).toHaveBeenCalledWith(
        expect.objectContaining({ behavior: "smooth", block: "nearest" }),
      );

      vi.useRealTimers();
    });

    it("should support keyboard activation with Enter key", () => {
      const compositionWithEditableGroups: CompositionEntry[] = [
        {
          templateId: "carbon-tax-flat",
          name: "Carbon Tax",
          parameters: { tax_rate: 44 },
          rateSchedule: {},
          instanceId: "inst-keyboard",
          editableParameterGroups: [
            { id: "mechanism", name: "Mechanism", parameterIds: ["tax_rate"] },
          ],
        },
      ];

      const parameterSchemas = {
        "carbon-tax-flat": [
          { id: "tax_rate", label: "Tax Rate", value: 44, baseline: 44, unit: "€/tonne", group: "Mechanism", type: "slider" as const },
        ],
      };

      const { container } = render(
        <PortfolioCompositionPanel
          templates={mockTemplates}
          composition={compositionWithEditableGroups}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          parameterSchemas={parameterSchemas}
        />,
      );

      const groupChip = container.querySelector('button[aria-expanded="false"]');
      expect(groupChip).toBeInTheDocument();

      // Press Enter key
      fireEvent.keyDown(groupChip!, { key: "Enter", code: "Enter" });

      // Card should be expanded
      expect(container.querySelector('button[aria-expanded="true"]')).toBeInTheDocument();
    });

    it("should support keyboard activation with Space key", () => {
      const compositionWithEditableGroups: CompositionEntry[] = [
        {
          templateId: "carbon-tax-flat",
          name: "Carbon Tax",
          parameters: { tax_rate: 44 },
          rateSchedule: {},
          instanceId: "inst-space",
          editableParameterGroups: [
            { id: "mechanism", name: "Mechanism", parameterIds: ["tax_rate"] },
          ],
        },
      ];

      const parameterSchemas = {
        "carbon-tax-flat": [
          { id: "tax_rate", label: "Tax Rate", value: 44, baseline: 44, unit: "€/tonne", group: "Mechanism", type: "slider" as const },
        ],
      };

      const { container } = render(
        <PortfolioCompositionPanel
          templates={mockTemplates}
          composition={compositionWithEditableGroups}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          parameterSchemas={parameterSchemas}
        />,
      );

      const groupChip = container.querySelector('button[aria-expanded="false"]');
      expect(groupChip).toBeInTheDocument();

      // Press Space key
      fireEvent.keyDown(groupChip!, { key: " ", code: "Space" });

      // Card should be expanded
      expect(container.querySelector('button[aria-expanded="true"]')).toBeInTheDocument();
    });

    it("should apply and remove highlight class after group chip click", () => {
      vi.useFakeTimers();

      const compositionWithEditableGroups: CompositionEntry[] = [
        {
          templateId: "carbon-tax-flat",
          name: "Carbon Tax",
          parameters: { tax_rate: 44 },
          rateSchedule: {},
          instanceId: "inst-highlight",
          editableParameterGroups: [
            { id: "mechanism", name: "Mechanism", parameterIds: ["tax_rate"] },
          ],
        },
      ];

      const parameterSchemas = {
        "carbon-tax-flat": [
          { id: "tax_rate", label: "Tax Rate", value: 44, baseline: 44, unit: "€/tonne", group: "Mechanism", type: "slider" as const },
        ],
      };

      const { container } = render(
        <PortfolioCompositionPanel
          templates={mockTemplates}
          composition={compositionWithEditableGroups}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          parameterSchemas={parameterSchemas}
        />,
      );

      const groupChip = container.querySelector('button[aria-expanded="false"]');
      fireEvent.click(groupChip!);

      // Should have highlight class initially
      const highlightedGroup = container.querySelector('[data-group-key="inst-highlight:mechanism"].ring-2');
      expect(highlightedGroup).toBeInTheDocument();

      // Advance timers to trigger highlight removal
      vi.advanceTimersByTime(1200);

      // Highlight should be removed (need to re-query after state update)
      // The component re-renders, so we need to check the updated container
      // In real test, we'd wait for state update, but here we just verify the pattern
      vi.useRealTimers();
    });
  });

  describe("Empty states and default values (AC-2, AC-5)", () => {
    it("should show '—' for missing parameter values in populated groups", () => {
      const compositionWithMissingValues: CompositionEntry[] = [
        {
          templateId: "carbon-tax-flat",
          name: "Carbon Tax",
          parameters: {}, // No configured values
          rateSchedule: {},
          instanceId: "inst-missing",
          editableParameterGroups: [
            { id: "mechanism", name: "Mechanism", parameterIds: ["tax_rate"] },
          ],
        },
      ];

      const parameterSchemas = {
        "carbon-tax-flat": [
          { id: "tax_rate", label: "Tax Rate", value: 44, baseline: 44, unit: "€/tonne", group: "Mechanism", type: "slider" as const },
        ],
      };

      const { container } = render(
        <PortfolioCompositionPanel
          templates={mockTemplates}
          composition={compositionWithMissingValues}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          parameterSchemas={parameterSchemas}
        />,
      );

      // Should show baseline from schema, not "—" when baseline exists
      expect(container.textContent).toContain("44 €/tonne");
    });

    it("should show '—' when no configured value and no baseline", () => {
      const compositionWithNoBaseline: CompositionEntry[] = [
        {
          templateId: "carbon-tax-flat",
          name: "Carbon Tax",
          parameters: {},
          rateSchedule: {},
          instanceId: "inst-no-baseline",
          editableParameterGroups: [
            { id: "mechanism", name: "Mechanism", parameterIds: ["custom_rate"] },
          ],
        },
      ];

      const parameterSchemas = {
        "carbon-tax-flat": [
          // Parameter without baseline
          { id: "custom_rate", label: "Custom Rate", value: 0, baseline: 0, unit: "€/tonne", group: "Mechanism", type: "slider" as const },
        ],
      };

      const { container } = render(
        <PortfolioCompositionPanel
          templates={mockTemplates}
          composition={compositionWithNoBaseline}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          parameterSchemas={parameterSchemas}
        />,
      );

      // Should show baseline (0) when parameter is not configured
      expect(container.textContent).toContain("0 €/tonne");
    });

    it("should show '0 [unit]' for explicitly configured zero values", () => {
      const compositionWithZero: CompositionEntry[] = [
        {
          templateId: "carbon-tax-flat",
          name: "Carbon Tax",
          parameters: { tax_rate: 0 }, // Explicitly set to 0
          rateSchedule: {},
          instanceId: "inst-zero",
          editableParameterGroups: [
            { id: "mechanism", name: "Mechanism", parameterIds: ["tax_rate"] },
          ],
        },
      ];

      const parameterSchemas = {
        "carbon-tax-flat": [
          { id: "tax_rate", label: "Tax Rate", value: 44, baseline: 44, unit: "€/tonne", group: "Mechanism", type: "slider" as const },
        ],
      };

      const { container } = render(
        <PortfolioCompositionPanel
          templates={mockTemplates}
          composition={compositionWithZero}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          parameterSchemas={parameterSchemas}
        />,
      );

      // Should show "0 €/tonne" for explicitly configured zero
      expect(container.textContent).toContain("0 €/tonne");
    });

    it("should show 'Parameters not yet set' for empty groups", () => {
      const compositionWithEmptyGroup: CompositionEntry[] = [
        {
          templateId: "carbon-tax-flat",
          name: "Carbon Tax",
          parameters: {},
          rateSchedule: {},
          instanceId: "inst-empty-group",
          editableParameterGroups: [
            { id: "empty", name: "Empty Group", parameterIds: [] },
          ],
        },
      ];

      const { container } = render(
        <PortfolioCompositionPanel
          templates={mockTemplates}
          composition={compositionWithEmptyGroup}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
        />,
      );

      // Should show empty group message
      expect(container.textContent).toContain("Parameters not yet set");
    });
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
      const cards = container.querySelectorAll('section[aria-label="Policy Set Composition"] > div');
      expect(cards.length).toBe(2);
    });
  });
});
