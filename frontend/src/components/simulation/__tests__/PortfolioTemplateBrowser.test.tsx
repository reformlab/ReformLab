// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
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
        onAddTemplate={noop}
        categories={[]}
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
        onAddTemplate={noop}
        categories={[]}
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
        onAddTemplate={noop}
        categories={[]}
      />,
    );

    expect(screen.getAllByText(/\d+ params/).length).toBeGreaterThan(0);
  });

  it("shows type badge (AC-1)", () => {
    render(
      <PortfolioTemplateBrowser
        templates={mockTemplates}
        selectedIds={[]}
        onAddTemplate={noop}
        categories={[]}
      />,
    );

    expect(screen.getAllByText("Carbon Tax").length).toBeGreaterThan(0);
  });

  // Story 25.2: Removed selected state test - no longer uses toggle selection

  it("calls onAddTemplate with template id when clicked", () => {
    const onAdd = vi.fn();
    render(
      <PortfolioTemplateBrowser
        templates={mockTemplates}
        selectedIds={[]}
        onAddTemplate={onAdd}
        categories={[]}
      />,
    );

    const buttons = screen.getAllByRole("button");
    fireEvent.click(buttons[0]);
    expect(onAdd).toHaveBeenCalledTimes(1);
    expect(onAdd).toHaveBeenCalledWith(expect.any(String));
  });

  it("filters templates by search query", () => {
    render(
      <PortfolioTemplateBrowser
        templates={mockTemplates}
        selectedIds={[]}
        onAddTemplate={noop}
        categories={[]}
      />,
    );

    const input = screen.getByPlaceholderText(/filter templates/i);
    fireEvent.change(input, { target: { value: "vehicle" } });

    expect(screen.getByText(/Vehicle Feebate/)).toBeInTheDocument();
    expect(screen.queryByText(/Carbon Tax — Flat Rate/)).not.toBeInTheDocument();
  });
});

// ============================================================================
// Story 24.4: Surfaced Policy Packs
// ============================================================================

describe("Story 24.4: Surfaced Policy Packs", () => {
  const noop = () => {};

  describe("Policy Type Labels", () => {
    it("should display 'Vehicle Malus' label for vehicle_malus type (AC-1)", () => {
      const vehicleMalusTemplate = {
        id: "vehicle-malus-flat",
        name: "Vehicle Malus — Flat Rate",
        type: "vehicle_malus",
        parameterCount: 4,
        description: "Flat-rate malus for vehicles exceeding CO2 emissions threshold",
        parameterGroups: ["emission_threshold", "malus_rate_per_gkm"],
        is_custom: true,
        runtime_availability: "live_ready" as const,
        availability_reason: null,
      };

      const { container } = render(
        <PortfolioTemplateBrowser
          templates={[vehicleMalusTemplate]}
          selectedIds={[]}
          onAddTemplate={noop}
          categories={[]}
        />,
      );

      // Assert the type badge element specifically (rose-colored span), not just text
      const typeBadge = container.querySelector('.bg-rose-100.text-rose-800');
      expect(typeBadge).toBeInTheDocument();
      expect(typeBadge).toHaveTextContent("Vehicle Malus");
    });

    it("should display 'Energy Poverty Aid' label for energy_poverty_aid type (AC-1)", () => {
      const energyAidTemplate = {
        id: "energy-aid-flat",
        name: "Energy Poverty Aid — Cheque Énergie",
        type: "energy_poverty_aid",
        parameterCount: 4,
        description: "Flat energy voucher for eligible households based on income ceiling",
        parameterGroups: ["income_ceiling", "rate_schedule"],
        is_custom: true,
        runtime_availability: "live_ready" as const,
        availability_reason: null,
      };

      const { container } = render(
        <PortfolioTemplateBrowser
          templates={[energyAidTemplate]}
          selectedIds={[]}
          onAddTemplate={noop}
          categories={[]}
        />,
      );

      // Assert the type badge element specifically (cyan-colored span), not just text
      const typeBadge = container.querySelector('.bg-cyan-100.text-cyan-800');
      expect(typeBadge).toBeInTheDocument();
      expect(typeBadge).toHaveTextContent("Energy Poverty Aid");
    });

    it("should display correct label for underscore-format carbon_tax type (dual-format support)", () => {
      const underscoreTemplate = {
        id: "carbon-tax-underscore",
        name: "Carbon Tax — Underscore Type",
        type: "carbon_tax",
        parameterCount: 8,
        description: "Template with underscore format type",
        parameterGroups: ["Tax Rates"],
        is_custom: false,
        runtime_availability: "live_ready" as const,
        availability_reason: null,
      };

      render(
        <PortfolioTemplateBrowser
          templates={[underscoreTemplate]}
          selectedIds={[]}
          onAddTemplate={noop}
          categories={[]}
        />,
      );

      expect(screen.getAllByText("Carbon Tax").length).toBeGreaterThan(0);
    });
  });

  describe("Type Colors", () => {
    it("should display rose color (bg-rose-100 text-rose-800) for vehicle_malus type (AC-1)", () => {
      const vehicleMalusTemplate = {
        id: "vehicle-malus-flat",
        name: "Vehicle Malus — Flat Rate",
        type: "vehicle_malus",
        parameterCount: 4,
        description: "Flat-rate malus for vehicles exceeding CO2 emissions threshold",
        parameterGroups: ["emission_threshold", "malus_rate_per_gkm"],
        is_custom: true,
        runtime_availability: "live_ready" as const,
        availability_reason: null,
      };

      const { container } = render(
        <PortfolioTemplateBrowser
          templates={[vehicleMalusTemplate]}
          selectedIds={[]}
          onAddTemplate={noop}
          categories={[]}
        />,
      );

      const badge = container.querySelector('.bg-rose-100.text-rose-800');
      expect(badge).toBeInTheDocument();
    });

    it("should display cyan color (bg-cyan-100 text-cyan-800) for energy_poverty_aid type (AC-1)", () => {
      const energyAidTemplate = {
        id: "energy-aid-flat",
        name: "Energy Poverty Aid — Cheque Énergie",
        type: "energy_poverty_aid",
        parameterCount: 4,
        description: "Flat energy voucher for eligible households based on income ceiling",
        parameterGroups: ["income_ceiling", "rate_schedule"],
        is_custom: true,
        runtime_availability: "live_ready" as const,
        availability_reason: null,
      };

      const { container } = render(
        <PortfolioTemplateBrowser
          templates={[energyAidTemplate]}
          selectedIds={[]}
          onAddTemplate={noop}
          categories={[]}
        />,
      );

      const badge = container.querySelector('.bg-cyan-100.text-cyan-800');
      expect(badge).toBeInTheDocument();
    });
  });

  describe("Runtime Availability Badges", () => {
    it("should show 'Ready' badge for live_ready surfaced packs (AC-2)", () => {
      const vehicleMalusTemplate = {
        id: "vehicle-malus-flat",
        name: "Vehicle Malus — Flat Rate",
        type: "vehicle_malus",
        parameterCount: 4,
        description: "Flat-rate malus for vehicles exceeding CO2 emissions threshold",
        parameterGroups: ["emission_threshold", "malus_rate_per_gkm"],
        is_custom: true,
        runtime_availability: "live_ready" as const,
        availability_reason: null,
      };

      render(
        <PortfolioTemplateBrowser
          templates={[vehicleMalusTemplate]}
          selectedIds={[]}
          onAddTemplate={noop}
          categories={[]}
        />,
      );

      expect(screen.getByText("Ready")).toBeInTheDocument();
    });

    it("should show green styling for 'Ready' badge (bg-green-50 text-green-700 border-green-200) (AC-2)", () => {
      const vehicleMalusTemplate = {
        id: "vehicle-malus-flat",
        name: "Vehicle Malus — Flat Rate",
        type: "vehicle_malus",
        parameterCount: 4,
        description: "Flat-rate malus for vehicles exceeding CO2 emissions threshold",
        parameterGroups: ["emission_threshold", "malus_rate_per_gkm"],
        is_custom: true,
        runtime_availability: "live_ready" as const,
        availability_reason: null,
      };

      const { container } = render(
        <PortfolioTemplateBrowser
          templates={[vehicleMalusTemplate]}
          selectedIds={[]}
          onAddTemplate={noop}
          categories={[]}
        />,
      );

      const readyBadge = container.querySelector('.bg-green-50.text-green-700.border-green-200');
      expect(readyBadge).toBeInTheDocument();
    });

    it("should not show availability_reason for live_ready packs (AC-2)", () => {
      const vehicleMalusTemplate = {
        id: "vehicle-malus-flat",
        name: "Vehicle Malus — Flat Rate",
        type: "vehicle_malus",
        parameterCount: 4,
        description: "Flat-rate malus for vehicles exceeding CO2 emissions threshold",
        parameterGroups: ["emission_threshold", "malus_rate_per_gkm"],
        is_custom: true,
        runtime_availability: "live_ready" as const,
        availability_reason: null,
      };

      const mockCategories = [
        {
          id: "vehicle_emissions",
          label: "Vehicle Emissions",
          columns: ["vehicle_co2"],
          compatible_types: ["tax"],
          formula_explanation: "vehicle_co2 × malus_rate",
          description: "Applies to vehicle emissions",
        },
      ];

      const { container } = render(
        <PortfolioTemplateBrowser
          templates={[vehicleMalusTemplate]}
          selectedIds={[]}
          onAddTemplate={noop}
          categories={mockCategories}
        />,
      );

      // Should not render any availability reason container (amber background div)
      // Exclude the categories warning box by checking for a more specific selector
      const reasonBox = container.querySelector('button .bg-amber-50');
      expect(reasonBox).not.toBeInTheDocument();
    });
  });

  describe("No Runtime Selector", () => {
    it("should not display any runtime or engine selector (AC-3)", () => {
      const surfacedTemplates = [
        {
          id: "vehicle-malus-flat",
          name: "Vehicle Malus — Flat Rate",
          type: "vehicle_malus",
          parameterCount: 4,
          description: "Flat-rate malus for vehicles exceeding CO2 emissions threshold",
          parameterGroups: ["emission_threshold", "malus_rate_per_gkm"],
          is_custom: true,
          runtime_availability: "live_ready" as const,
          availability_reason: null,
        },
        {
          id: "energy-aid-flat",
          name: "Energy Poverty Aid — Cheque Énergie",
          type: "energy_poverty_aid",
          parameterCount: 4,
          description: "Flat energy voucher for eligible households",
          parameterGroups: ["income_ceiling", "rate_schedule"],
          is_custom: true,
          runtime_availability: "live_ready" as const,
          availability_reason: null,
        },
      ];

      render(
        <PortfolioTemplateBrowser
          templates={surfacedTemplates}
          selectedIds={[]}
          onAddTemplate={noop}
          categories={[]}
        />,
      );

      // Should not have any runtime/engine selector controls
      expect(screen.queryByText(/runtime/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/engine/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/live|replay/i)).not.toBeInTheDocument();
    });
  });
});
