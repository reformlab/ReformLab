// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Configuration screen — Story 18.5, AC-1 and AC-3.
 *
 * Extracted from inline App.tsx configuration JSX (lines 281-335) into a
 * dedicated screen component. Manages step navigation internally; activeStep
 * state remains in App.tsx because the right panel workspace badge needs it.
 */

import { useMemo } from "react";

import { AssumptionsReviewScreen } from "@/components/screens/AssumptionsReviewScreen";
import { ParameterEditingScreen } from "@/components/screens/ParameterEditingScreen";
import { PopulationSelectionScreen } from "@/components/screens/PopulationSelectionScreen";
import { TemplateSelectionScreen } from "@/components/screens/TemplateSelectionScreen";
import {
  type ConfigStep,
  type ConfigStepKey,
  ModelConfigStepper,
} from "@/components/simulation/ModelConfigStepper";
import { Button } from "@/components/ui/button";
import type { Parameter, Population, Template } from "@/data/mock-data";

// ============================================================================
// Constants
// ============================================================================

const STEP_ORDER: ConfigStepKey[] = [
  "population",
  "template",
  "parameters",
  "assumptions",
];

// ============================================================================
// Helpers
// ============================================================================

function getConfigSteps(activeStep: ConfigStepKey): ConfigStep[] {
  return [
    { key: "population", label: "Population", status: activeStep === "population" ? "incomplete" : "complete" },
    { key: "template", label: "Policy", status: activeStep === "template" ? "incomplete" : "complete" },
    { key: "parameters", label: "Parameters", status: activeStep === "parameters" ? "incomplete" : "complete" },
    { key: "assumptions", label: "Validation", status: activeStep === "assumptions" ? "incomplete" : "complete" },
  ];
}

// ============================================================================
// Props interface
// ============================================================================

export interface ConfigurationScreenProps {
  activeStep: ConfigStepKey;
  onStepSelect: (step: ConfigStepKey) => void;
  populations: Population[];
  selectedPopulationId: string;
  onSelectPopulation: (id: string) => void;
  templates: Template[];
  selectedTemplateId: string;
  onSelectTemplate: (id: string) => void;
  onTemplatesChanged: () => void;
  parameters: Parameter[];
  parameterValues: Record<string, number>;
  onParameterChange: (id: string, value: number) => void;
  onGoToSimulation: () => void;
}

// ============================================================================
// Component
// ============================================================================

export function ConfigurationScreen({
  activeStep,
  onStepSelect,
  populations,
  selectedPopulationId,
  onSelectPopulation,
  templates,
  selectedTemplateId,
  onSelectTemplate,
  onTemplatesChanged,
  parameters,
  parameterValues,
  onParameterChange,
  onGoToSimulation,
}: ConfigurationScreenProps) {
  const configSteps = useMemo(() => getConfigSteps(activeStep), [activeStep]);

  const selectedPopulation = useMemo(
    () => populations.find((p) => p.id === selectedPopulationId),
    [populations, selectedPopulationId],
  );

  const selectedTemplate = useMemo(
    () => templates.find((t) => t.id === selectedTemplateId),
    [templates, selectedTemplateId],
  );

  const filteredParameters = useMemo(() => {
    if (!selectedTemplate) return parameters;
    return parameters.filter((p) => selectedTemplate.parameterGroups.includes(p.group));
  }, [selectedTemplate, parameters]);

  const isLastStep = activeStep === STEP_ORDER[STEP_ORDER.length - 1];

  const nextStep = () => {
    const currentIndex = STEP_ORDER.indexOf(activeStep);
    if (currentIndex >= STEP_ORDER.length - 1) {
      onGoToSimulation();
      return;
    }
    const next = STEP_ORDER[currentIndex + 1] ?? activeStep;
    onStepSelect(next);
  };

  return (
    <section className="space-y-3">
      <ModelConfigStepper activeStep={activeStep} steps={configSteps} onStepSelect={onStepSelect} />

      {activeStep === "population" ? (
        <PopulationSelectionScreen
          populations={populations}
          selectedPopulationId={selectedPopulationId}
          onSelectPopulation={onSelectPopulation}
        />
      ) : null}

      {activeStep === "template" ? (
        <TemplateSelectionScreen
          templates={templates}
          selectedTemplateId={selectedTemplateId}
          onSelectTemplate={onSelectTemplate}
          onTemplatesChanged={onTemplatesChanged}
        />
      ) : null}

      {activeStep === "parameters" ? (
        <ParameterEditingScreen
          parameters={filteredParameters}
          parameterValues={parameterValues}
          onParameterChange={onParameterChange}
        />
      ) : null}

      {activeStep === "assumptions" ? (
        <AssumptionsReviewScreen
          population={selectedPopulation}
          template={selectedTemplate}
          parameters={filteredParameters}
          parameterValues={parameterValues}
        />
      ) : null}

      <div className="flex justify-end">
        <Button onClick={nextStep}>
          {isLastStep ? "Go to Simulation" : "Next Step"}
        </Button>
      </div>
    </section>
  );
}
