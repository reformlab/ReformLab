// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Shared step-navigation bar for workbench-style screens (Story 18.3, AC-1). */

import { cn } from "@/lib/utils";

export interface StepDef {
  key: string;
  label: string;
}

interface WorkbenchStepperProps {
  steps: StepDef[];
  activeStep: string;
  onStepSelect: (key: string) => void;
  ariaLabel?: string;
}

export function WorkbenchStepper({
  steps,
  activeStep,
  onStepSelect,
  ariaLabel = "Steps",
}: WorkbenchStepperProps) {
  return (
    <nav aria-label={ariaLabel} className="border-b border-slate-200 bg-white p-3">
      <ol className="flex gap-1 overflow-x-auto">
        {steps.map((step) => {
          const isActive = step.key === activeStep;
          return (
            <li key={step.key} className="shrink-0">
              <button
                type="button"
                aria-current={isActive ? "step" : undefined}
                onClick={() => onStepSelect(step.key)}
                className={cn(
                  "border px-3 py-1.5 text-xs focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2",
                  isActive
                    ? "border-blue-500 bg-blue-50 text-blue-700 font-medium"
                    : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50",
                )}
              >
                {step.label}
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
