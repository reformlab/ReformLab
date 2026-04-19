// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Tests for Story 25.4: Editable parameter groups within policy cards.
 */

import { render, screen, fireEvent } from "@testing-library/react";
import { vi } from "vitest";

import { PortfolioCompositionPanel } from "@/components/simulation/PortfolioCompositionPanel";
import type { CompositionEntry } from "@/components/simulation/PortfolioCompositionPanel";
import { mockTemplates } from "@/data/mock-data";

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

const baseEntry = (id: string): CompositionEntry => ({
  templateId: id,
  name: mockTemplates.find((t) => t.id === id)?.name ?? id,
  parameters: {},
  rateSchedule: {},
  instanceId: `${id}-ins0`,
});

describe("Story 25.4: Editable Parameter Groups", () => {
  describe("Edit groups mode toggle (AC-1)", () => {
    it("should show 'Edit groups' button in card header", () => {
      const entry = baseEntry("carbon-tax-flat");
      entry.editableParameterGroups = [
        { id: "group-0", name: "Mechanism", parameterIds: ["rate", "unit"] },
        { id: "group-1", name: "Eligibility", parameterIds: [] },
      ];

      render(
        <PortfolioCompositionPanel
          templates={mockTemplates}
          composition={[entry]}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          categories={mockCategories}
          editGroupsIndex={null}
          onToggleEditGroups={() => {}}
        />,
      );

      const editButton = screen.getByLabelText(/Edit parameter groups/i);
      expect(editButton).toBeInTheDocument();
    });

    it("should activate edit-groups mode when button clicked", () => {
      const onToggleEditGroups = vi.fn();
      const entry = baseEntry("carbon-tax-flat");
      entry.editableParameterGroups = [
        { id: "group-0", name: "Mechanism", parameterIds: [] },
      ];

      render(
        <PortfolioCompositionPanel
          templates={mockTemplates}
          composition={[entry]}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          categories={mockCategories}
          editGroupsIndex={null}
          onToggleEditGroups={onToggleEditGroups}
        />,
      );

      const editButton = screen.getByLabelText(/Edit parameter groups/i);
      fireEvent.click(editButton);
      expect(onToggleEditGroups).toHaveBeenCalledWith(0);
    });

    it("should show blue border and 'Editing' badge when in edit-groups mode", () => {
      const entry = baseEntry("carbon-tax-flat");
      entry.editableParameterGroups = [
        { id: "group-0", name: "Mechanism", parameterIds: [] },
      ];

      const { container } = render(
        <PortfolioCompositionPanel
          templates={mockTemplates}
          composition={[entry]}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          categories={mockCategories}
          editGroupsIndex={0}
          onToggleEditGroups={() => {}}
        />,
      );

      // Blue border
      const card = container.querySelector(".border-blue-500");
      expect(card).toBeInTheDocument();

      // Editing badge
      expect(screen.getByText("Editing")).toBeInTheDocument();
    });

    it("should only affect specific card when editGroupsIndex is set", () => {
      const entry1 = baseEntry("carbon-tax-flat");
      entry1.instanceId = "carbon-tax-flat-ins0";
      entry1.editableParameterGroups = [
        { id: "group-0", name: "Mechanism", parameterIds: [] },
      ];

      const entry2 = baseEntry("subsidy-energy");
      entry2.instanceId = "subsidy-energy-ins0";
      entry2.editableParameterGroups = [
        { id: "group-0", name: "Mechanism", parameterIds: [] },
      ];

      const { container } = render(
        <PortfolioCompositionPanel
          templates={mockTemplates}
          composition={[entry1, entry2]}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          categories={mockCategories}
          editGroupsIndex={0}
          onToggleEditGroups={() => {}}
        />,
      );

      // Check that only the first card has blue border AND white background
      // (edit buttons and badges have different styling)
      const blueBorderCards = container.querySelectorAll(".border.bg-white.border-blue-500");
      expect(blueBorderCards.length).toBe(1);

      // Check that "Editing" badge appears only once
      const editingBadges = screen.getAllByText("Editing");
      expect(editingBadges.length).toBe(1);
    });
  });

  describe("Group rename (AC-2)", () => {
    it("should show editable input for group name in edit mode", () => {
      const onGroupRename = vi.fn();
      const entry = baseEntry("carbon-tax-flat");
      entry.editableParameterGroups = [
        { id: "group-0", name: "Mechanism", parameterIds: [] },
      ];

      render(
        <PortfolioCompositionPanel
          templates={mockTemplates}
          composition={[entry]}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          categories={mockCategories}
          editGroupsIndex={0}
          onToggleEditGroups={() => {}}
          onGroupRename={onGroupRename}
        />,
      );

      // Expand the card to see edit controls
      const expandButton = screen.getByLabelText(/Expand parameters/i);
      fireEvent.click(expandButton);

      const input = screen.getByDisplayValue("Mechanism");
      expect(input).toBeInTheDocument();
      expect(input.tagName.toLowerCase()).toBe("input");
    });

    it("should call onGroupRename when input value changes", () => {
      const onGroupRename = vi.fn();
      const entry = baseEntry("carbon-tax-flat");
      entry.editableParameterGroups = [
        { id: "group-0", name: "Mechanism", parameterIds: [] },
      ];

      render(
        <PortfolioCompositionPanel
          templates={mockTemplates}
          composition={[entry]}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          categories={mockCategories}
          editGroupsIndex={0}
          onToggleEditGroups={() => {}}
          onGroupRename={onGroupRename}
        />,
      );

      const expandButton = screen.getByLabelText(/Expand parameters/i);
      fireEvent.click(expandButton);

      const input = screen.getByDisplayValue("Mechanism");
      fireEvent.change(input, { target: { value: "Pricing Mechanism" } });
      fireEvent.blur(input);

      expect(onGroupRename).toHaveBeenCalledWith(0, "group-0", "Pricing Mechanism");
    });

    it("should show editable groups when not in edit mode", () => {
      const entry = baseEntry("carbon-tax-flat");
      entry.editableParameterGroups = [
        { id: "group-0", name: "Custom Group", parameterIds: [] },
      ];

      render(
        <PortfolioCompositionPanel
          templates={mockTemplates}
          composition={[entry]}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          categories={mockCategories}
          editGroupsIndex={null}
          onToggleEditGroups={() => {}}
        />,
      );

      const expandButton = screen.getByLabelText(/Expand parameters/i);
      fireEvent.click(expandButton);

      expect(screen.getByText("Custom Group")).toBeInTheDocument();
    });
  });

  describe("Add new group (AC-3)", () => {
    it("should show '+ Add group' button in edit mode", () => {
      const onAddGroup = vi.fn();
      const entry = baseEntry("carbon-tax-flat");
      entry.editableParameterGroups = [
        { id: "group-0", name: "Mechanism", parameterIds: [] },
      ];

      render(
        <PortfolioCompositionPanel
          templates={mockTemplates}
          composition={[entry]}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          categories={mockCategories}
          editGroupsIndex={0}
          onToggleEditGroups={() => {}}
          onAddGroup={onAddGroup}
        />,
      );

      const expandButton = screen.getByLabelText(/Expand parameters/i);
      fireEvent.click(expandButton);

      const addButton = screen.getByText(/Add group/i);
      expect(addButton).toBeInTheDocument();
    });

    it("should call onAddGroup when button clicked", () => {
      const onAddGroup = vi.fn();
      const entry = baseEntry("carbon-tax-flat");
      entry.editableParameterGroups = [
        { id: "group-0", name: "Mechanism", parameterIds: [] },
      ];

      render(
        <PortfolioCompositionPanel
          templates={mockTemplates}
          composition={[entry]}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          categories={mockCategories}
          editGroupsIndex={0}
          onToggleEditGroups={() => {}}
          onAddGroup={onAddGroup}
        />,
      );

      const expandButton = screen.getByLabelText(/Expand parameters/i);
      fireEvent.click(expandButton);

      const addButton = screen.getByText(/Add group/i);
      fireEvent.click(addButton);

      expect(onAddGroup).toHaveBeenCalledWith(0);
    });
  });

  describe("Delete group (AC-4, AC-5)", () => {
    it("should show delete button for each group in edit mode", () => {
      const onDeleteGroup = vi.fn();
      const entry = baseEntry("carbon-tax-flat");
      entry.editableParameterGroups = [
        { id: "group-0", name: "Mechanism", parameterIds: [] },
      ];

      render(
        <PortfolioCompositionPanel
          templates={mockTemplates}
          composition={[entry]}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          categories={mockCategories}
          editGroupsIndex={0}
          onToggleEditGroups={() => {}}
          onDeleteGroup={onDeleteGroup}
        />,
      );

      const expandButton = screen.getByLabelText(/Expand parameters/i);
      fireEvent.click(expandButton);

      const deleteButton = screen.getByLabelText(/Delete group/i);
      expect(deleteButton).toBeInTheDocument();
    });

    it("should disable delete for non-empty groups", () => {
      const onDeleteGroup = vi.fn();
      const entry = baseEntry("carbon-tax-flat");
      entry.editableParameterGroups = [
        { id: "group-0", name: "Mechanism", parameterIds: ["rate", "unit"] },
      ];

      render(
        <PortfolioCompositionPanel
          templates={mockTemplates}
          composition={[entry]}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          categories={mockCategories}
          editGroupsIndex={0}
          onToggleEditGroups={() => {}}
          onDeleteGroup={onDeleteGroup}
        />,
      );

      const expandButton = screen.getByLabelText(/Expand parameters/i);
      fireEvent.click(expandButton);

      const deleteButton = screen.getByLabelText(/Delete group/i);
      expect(deleteButton).toBeDisabled();
    });

    it("should disable delete when only one group remains", () => {
      const onDeleteGroup = vi.fn();
      const entry = baseEntry("carbon-tax-flat");
      entry.editableParameterGroups = [
        { id: "group-0", name: "Mechanism", parameterIds: [] },
      ];

      render(
        <PortfolioCompositionPanel
          templates={mockTemplates}
          composition={[entry]}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          categories={mockCategories}
          editGroupsIndex={0}
          onToggleEditGroups={() => {}}
          onDeleteGroup={onDeleteGroup}
        />,
      );

      const expandButton = screen.getByLabelText(/Expand parameters/i);
      fireEvent.click(expandButton);

      const deleteButton = screen.getByLabelText(/Delete group/i);
      expect(deleteButton).toBeDisabled();
    });

    it("should enable delete for empty group when multiple groups exist", () => {
      const onDeleteGroup = vi.fn();
      const entry = baseEntry("carbon-tax-flat");
      entry.editableParameterGroups = [
        { id: "group-0", name: "Mechanism", parameterIds: [] },
        { id: "group-1", name: "Eligibility", parameterIds: [] },
      ];

      render(
        <PortfolioCompositionPanel
          templates={mockTemplates}
          composition={[entry]}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          categories={mockCategories}
          editGroupsIndex={0}
          onToggleEditGroups={() => {}}
          onDeleteGroup={onDeleteGroup}
        />,
      );

      const expandButton = screen.getByLabelText(/Expand parameters/i);
      fireEvent.click(expandButton);

      const deleteButtons = screen.getAllByLabelText(/Delete group/i);
      expect(deleteButtons[0]).not.toBeDisabled();
    });
  });

  describe("Parameter move between groups (AC-6)", () => {
    it("should show move dropdown for parameters in edit mode", () => {
      const onMoveParameter = vi.fn();
      const entry = baseEntry("carbon-tax-flat");
      entry.editableParameterGroups = [
        { id: "group-0", name: "Mechanism", parameterIds: ["rate"] },
        { id: "group-1", name: "Eligibility", parameterIds: [] },
      ];

      render(
        <PortfolioCompositionPanel
          templates={mockTemplates}
          composition={[entry]}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          categories={mockCategories}
          editGroupsIndex={0}
          onToggleEditGroups={() => {}}
          onMoveParameter={onMoveParameter}
        />,
      );

      const expandButton = screen.getByLabelText(/Expand parameters/i);
      fireEvent.click(expandButton);

      // Find the select dropdown for moving parameters (specific label includes parameter ID)
      const select = screen.getByLabelText(/Move parameter rate to/i);
      expect(select).toBeInTheDocument();
      expect(select.tagName.toLowerCase()).toBe("select");
    });
  });

  describe("Edit groups mode persists across collapse/expand (AC-7)", () => {
    it("should maintain edit mode state when collapsing and expanding", () => {
      const entry = baseEntry("carbon-tax-flat");
      entry.editableParameterGroups = [
        { id: "group-0", name: "Mechanism", parameterIds: [] },
      ];

      const { container } = render(
        <PortfolioCompositionPanel
          templates={mockTemplates}
          composition={[entry]}
          onReorder={() => {}}
          onRemove={() => {}}
          onParameterChange={() => {}}
          onRateScheduleChange={() => {}}
          categories={mockCategories}
          editGroupsIndex={0}
          onToggleEditGroups={() => {}}
        />,
      );

      // Card should have blue border initially
      let card = container.querySelector(".border.bg-white.border-blue-500");
      expect(card).toBeInTheDocument();

      // Expand first (card starts collapsed)
      const expandButton = screen.getByLabelText(/Expand parameters/i);
      fireEvent.click(expandButton);

      // Blue border should still be there
      card = container.querySelector(".border.bg-white.border-blue-500");
      expect(card).toBeInTheDocument();

      // Collapse
      const collapseButton = screen.getByLabelText(/Collapse parameters/i);
      fireEvent.click(collapseButton);

      // Blue border should remain
      card = container.querySelector(".border.bg-white.border-blue-500");
      expect(card).toBeInTheDocument();

      // Expand again
      const expandButton2 = screen.getByLabelText(/Expand parameters/i);
      fireEvent.click(expandButton2);

      // Blue border should still be there
      card = container.querySelector(".border.bg-white.border-blue-500");
      expect(card).toBeInTheDocument();
    });
  });
});
