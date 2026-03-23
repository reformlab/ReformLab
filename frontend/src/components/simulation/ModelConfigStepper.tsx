// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { CheckCircle2, Circle, CircleAlert } from "lucide-react";

import { cn } from "@/lib/utils";

export type ConfigStepKey =
  | "population"
  | "template"
  | "parameters"
  | "assumptions";

export interface ConfigStep {
  key: ConfigStepKey;
  label: string;
  status: "incomplete" | "complete" | "error";
}

interface ModelConfigStepperProps {
  activeStep: ConfigStepKey;
  steps: ConfigStep[];
  onStepSelect: (step: ConfigStepKey) => void;
}

export function ModelConfigStepper({
  activeStep,
  steps,
  onStepSelect,
}: ModelConfigStepperProps) {
  return (
    <nav aria-label="Model configuration steps" className="border-b border-slate-200 bg-white p-3">
      <ol className="grid grid-cols-4 gap-2">
        {steps.map((step) => {
          const isActive = step.key === activeStep;
          const Icon =
            step.status === "complete"
              ? CheckCircle2
              : step.status === "error"
                ? CircleAlert
                : Circle;

          return (
            <li key={step.key}>
              <button
                type="button"
                onClick={() => onStepSelect(step.key)}
                className={cn(
                  "flex w-full items-center gap-2 border px-2 py-2 text-left text-xs",
                  isActive
                    ? "border-blue-500 bg-blue-50 text-blue-700"
                    : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50",
                )}
              >
                <Icon className="h-4 w-4" />
                <span>{step.label}</span>
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
