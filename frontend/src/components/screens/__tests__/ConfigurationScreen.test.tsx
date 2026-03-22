/** Tests for ConfigurationScreen — Story 18.5, AC-5. */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

// Mock the template API (TemplateSelectionScreen calls createCustomTemplate)
vi.mock("@/api/templates", () => ({
  createCustomTemplate: vi.fn(),
}));

import { ConfigurationScreen } from "@/components/screens/ConfigurationScreen";
import type { Parameter, Population, Template } from "@/data/mock-data";
import type { ConfigStepKey } from "@/components/simulation/ModelConfigStepper";

// ============================================================================
// Fixtures
// ============================================================================

function mockPopulations(): Population[] {
  return [
    { id: "pop-1", name: "France 2024", households: 30000000, source: "INSEE", year: 2024 },
  ];
}

function mockTemplates(): Template[] {
  return [
    {
      id: "tpl-1",
      name: "Carbon Tax",
      type: "carbon_tax",
      parameterCount: 3,
      description: "Standard carbon tax",
      parameterGroups: ["carbon"],
      is_custom: false,
    },
  ];
}

function mockParameters(): Parameter[] {
  return [
    { id: "p1", label: "Tax Rate", value: 44, baseline: 44, unit: "€/tCO2", group: "carbon", type: "slider", min: 0, max: 200 },
    { id: "p2", label: "Other Param", value: 10, baseline: 10, unit: "%", group: "other", type: "number" },
  ];
}

function makeDefaultProps(overrides: Partial<{
  activeStep: ConfigStepKey;
  onStepSelect: ReturnType<typeof vi.fn>;
  onGoToSimulation: ReturnType<typeof vi.fn>;
}> = {}) {
  return {
    activeStep: "population" as ConfigStepKey,
    onStepSelect: vi.fn(),
    populations: mockPopulations(),
    selectedPopulationId: "pop-1",
    onSelectPopulation: vi.fn(),
    templates: mockTemplates(),
    selectedTemplateId: "tpl-1",
    onSelectTemplate: vi.fn(),
    onTemplatesChanged: vi.fn(),
    parameters: mockParameters(),
    parameterValues: { p1: 44, p2: 10 },
    onParameterChange: vi.fn(),
    onGoToSimulation: vi.fn(),
    ...overrides,
  };
}

// ============================================================================
// Tests
// ============================================================================

describe("ConfigurationScreen", () => {
  // AC-5: Test 4.2 — renders PopulationSelectionScreen by default (activeStep="population")
  it("renders PopulationSelectionScreen when activeStep is population", () => {
    render(<ConfigurationScreen {...makeDefaultProps({ activeStep: "population" })} />);
    // PopulationSelectionScreen renders each population's name
    expect(screen.getByText("France 2024")).toBeInTheDocument();
  });

  // AC-5: Test 4.3 — renders TemplateSelectionScreen when activeStep="template"
  it("renders TemplateSelectionScreen when activeStep is template", () => {
    render(<ConfigurationScreen {...makeDefaultProps({ activeStep: "template" })} />);
    // TemplateSelectionScreen renders each template's name in the grid
    expect(screen.getByText("Carbon Tax")).toBeInTheDocument();
  });

  // AC-5: Test 4.4 — renders ParameterEditingScreen when activeStep="parameters"
  it("renders ParameterEditingScreen when activeStep is parameters", () => {
    render(<ConfigurationScreen {...makeDefaultProps({ activeStep: "parameters" })} />);
    // ParameterEditingScreen renders the group name as a heading
    // Both parameters are from "carbon" and "other" groups
    expect(screen.getByText("carbon")).toBeInTheDocument();
  });

  // AC-5: Test 4.5 — renders AssumptionsReviewScreen when activeStep="assumptions"
  it("renders AssumptionsReviewScreen when activeStep is assumptions", () => {
    render(<ConfigurationScreen {...makeDefaultProps({ activeStep: "assumptions" })} />);
    // AssumptionsReviewScreen renders "Configuration Summary"
    expect(screen.getByText("Configuration Summary")).toBeInTheDocument();
  });

  // AC-5: Test 4.6 — "Next Step" button advances step via onStepSelect callback
  it("clicking Next Step advances to next step via onStepSelect", async () => {
    const onStepSelect = vi.fn();
    const onGoToSimulation = vi.fn();
    render(<ConfigurationScreen {...makeDefaultProps({ activeStep: "population", onStepSelect, onGoToSimulation })} />);

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Next Step" }));

    expect(onStepSelect).toHaveBeenCalledWith("template");
    expect(onStepSelect).toHaveBeenCalledTimes(1);
    // onGoToSimulation must NOT fire on intermediate steps
    expect(onGoToSimulation).not.toHaveBeenCalled();
  });

  // AC-5: Test 4.7 — shows "Go to Simulation" on last step (assumptions)
  it('shows "Go to Simulation" button on last step (assumptions)', () => {
    render(<ConfigurationScreen {...makeDefaultProps({ activeStep: "assumptions" })} />);
    expect(screen.getByRole("button", { name: "Go to Simulation" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Next Step" })).not.toBeInTheDocument();
  });

  // AC-5: Test 4.8 — clicking "Go to Simulation" calls onGoToSimulation
  it("clicking Go to Simulation calls onGoToSimulation", async () => {
    const onGoToSimulation = vi.fn();
    const onStepSelect = vi.fn();
    render(<ConfigurationScreen {...makeDefaultProps({ activeStep: "assumptions", onGoToSimulation, onStepSelect })} />);

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Go to Simulation" }));

    expect(onGoToSimulation).toHaveBeenCalledTimes(1);
    // onStepSelect must NOT fire on the last step (no next step to advance to)
    expect(onStepSelect).not.toHaveBeenCalled();
  });

  // AC-5: Test 4.9 — clicking stepper step calls onStepSelect (non-blocking navigation)
  it("clicking a stepper step calls onStepSelect directly", async () => {
    const onStepSelect = vi.fn();
    render(<ConfigurationScreen {...makeDefaultProps({ activeStep: "population", onStepSelect })} />);

    const user = userEvent.setup();
    // The stepper renders step buttons; click "Parameters" step
    await user.click(screen.getByRole("button", { name: /Parameters/i }));

    expect(onStepSelect).toHaveBeenCalledWith("parameters");
  });

  // AC-5: Test 4.10 — filters parameters by selected template's parameterGroups
  it("filters parameters by selected template parameterGroups in parameters step", () => {
    // Template has parameterGroups: ["carbon"], so only "carbon" group params should appear
    // "Other Param" (group: "other") should NOT be rendered
    render(
      <ConfigurationScreen
        {...makeDefaultProps({ activeStep: "parameters" })}
      />
    );
    // "carbon" group heading should appear
    expect(screen.getByText("carbon")).toBeInTheDocument();
    // "other" group heading should NOT appear (filtered out)
    expect(screen.queryByText("other")).not.toBeInTheDocument();
  });
});
