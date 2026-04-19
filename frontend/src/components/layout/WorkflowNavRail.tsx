// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * WorkflowNavRail — vertical stepper navigation for the left panel.
 *
 * Displays the four canonical workflow stages (Policy → Population →
 * Scenario → Run / Results / Compare) with completion indicators, summary lines,
 * and connecting lines between steps.
 * Supports a collapsed variant that shows only step indicator icons.
 *
 * Story 20.1 — AC-1, refactored from Story 18.1.
 */

import { Check, Circle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { GenerationResult, PortfolioListItem, ResultListItem, PopulationItem } from "@/api/types";
import type { StageKey, WorkspaceScenario, SubView } from "@/types/workspace";
import { STAGES, POPULATION_SUB_STEPS } from "@/types/workspace";

// ============================================================================
// Types
// ============================================================================

export interface WorkflowNavRailProps {
  activeStage: StageKey;
  navigateTo: (stage: StageKey, subView?: SubView | null) => void;
  collapsed: boolean;
  selectedPopulationId: string;
  dataFusionResult: GenerationResult | null;
  portfolios: PortfolioListItem[];
  results: ResultListItem[];
  activeScenario: WorkspaceScenario | null;
  populations: PopulationItem[];
  explorerPopulationId: string | null; // Story 22.4 - for Explorer sub-step disabled state
  activeSubView: SubView | null; // Story 22.4 - for active sub-step indication
}

// ============================================================================
// Completion logic
// ============================================================================

function isComplete(
  key: StageKey,
  selectedPopulationId: string,
  dataFusionResult: GenerationResult | null,
  _portfolios: PortfolioListItem[],
  results: ResultListItem[],
  activeScenario: WorkspaceScenario | null,
): boolean {
  switch (key) {
    case "policies":
      // AC-5 (Story 20.3): completion requires an active portfolio linked to the scenario,
      // not just any portfolio existing in the library.
      return typeof activeScenario?.portfolioName === "string" && activeScenario.portfolioName.length > 0;
    case "population":
      // AC-5 (Story 20.4): primary signal is activeScenario.populationIds; legacy fallback.
      return (
        (activeScenario?.populationIds?.length ?? 0) > 0 ||
        !!selectedPopulationId ||
        dataFusionResult !== null
      );
    case "engine":
      return activeScenario !== null;
    case "results":
      return results.length > 0;
  }
}

// ============================================================================
// Summary lines
// ============================================================================

function getSummary(
  key: StageKey,
  selectedPopulationId: string,
  dataFusionResult: GenerationResult | null,
  _portfolios: PortfolioListItem[],
  results: ResultListItem[],
  activeScenario: WorkspaceScenario | null,
  populations: PopulationItem[],
): string | null {
  switch (key) {
    case "policies": {
      // AC-5 (Story 20.3): summary shows the active portfolio name, not aggregate policy count.
      return activeScenario?.portfolioName ?? null;
    }
    case "population": {
      // Prefer the explicitly selected population (canonical + legacy) over data fusion result
      const popId = activeScenario?.populationIds?.[0] ?? selectedPopulationId;
      if (popId) {
        return populations.find((p) => p.id === popId)?.name ?? popId;
      }
      if (dataFusionResult) {
        const count = dataFusionResult.summary.record_count.toLocaleString();
        return `${count} records`;
      }
      return null;
    }
    case "engine": {
      if (!activeScenario) return null;
      const { startYear, endYear } = activeScenario.engineConfig;
      return `${startYear}–${endYear}`;
    }
    case "results": {
      if (results.length === 0) return null;
      const n = results.length;
      return `${n} run${n !== 1 ? "s" : ""}`;
    }
  }
}

// ============================================================================
// StepIndicator sub-component
// ============================================================================

interface StepIndicatorProps {
  stageKey: StageKey;
  index: number;
  active: boolean;
  complete: boolean;
}

function StepIndicator({ stageKey, index, active, complete }: StepIndicatorProps) {
  return (
    <div
      data-testid={`step-indicator-${stageKey}`}
      data-active={active ? "true" : "false"}
      className={cn(
        "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-semibold",
        complete && "bg-emerald-500 text-white",
        active && !complete && "bg-blue-500 text-white",
        !active && !complete && "border-2 border-slate-300 bg-white text-slate-500",
      )}
    >
      {complete ? <Check className="h-4 w-4" /> : <span>{index + 1}</span>}
    </div>
  );
}

// ============================================================================
// SubStepIndicator sub-component — Story 22.4
// ============================================================================

interface SubStepIndicatorProps {
  label: string;
  active: boolean;
  disabled: boolean;
  onClick: () => void;
  testId: string;
  disabledTooltip?: string; // Story 22.4: Tooltip text for disabled state
}

function SubStepIndicator({ label, active, disabled, onClick, testId, disabledTooltip }: SubStepIndicatorProps) {
  return (
    <button
      type="button"
      data-testid={testId}
      aria-disabled={disabled ? "true" : undefined}
      title={disabled ? disabledTooltip : undefined}
      onClick={disabled ? undefined : onClick}
      className={cn(
        "flex items-center gap-2 rounded px-2 py-1 text-xs transition-colors",
        "hover:bg-slate-50",
        disabled && "cursor-not-allowed opacity-50 hover:bg-transparent",
        !disabled && "cursor-pointer",
      )}
    >
      <Circle
        className={cn(
          "h-2 w-2 shrink-0 fill-current",
          active && "bg-blue-500 text-blue-500",
          !active && "bg-slate-300 text-slate-300",
        )}
      />
      <span
        className={cn(
          "font-normal leading-none",
          active ? "text-slate-900" : "text-slate-600",
        )}
      >
        {label}
      </span>
    </button>
  );
}

// ============================================================================
// Main component
// ============================================================================

export function WorkflowNavRail({
  activeStage,
  navigateTo,
  collapsed,
  selectedPopulationId,
  dataFusionResult,
  portfolios,
  results,
  activeScenario,
  populations,
  explorerPopulationId,
  activeSubView,
}: WorkflowNavRailProps) {
  return (
    <nav aria-label="Workflow navigation" className="flex flex-col gap-0">
      {STAGES.map((stage, index) => {
        const active = stage.activeFor.includes(activeStage);
        const complete = isComplete(stage.key, selectedPopulationId, dataFusionResult, portfolios, results, activeScenario);
        const summary = collapsed
          ? null
          : getSummary(stage.key, selectedPopulationId, dataFusionResult, portfolios, results, activeScenario, populations);
        const isLast = index === STAGES.length - 1;

        // Story 22.4: Population sub-steps (Library, Build, Explorer)
        const showPopulationSubSteps = !collapsed && stage.key === "population" && active;

        return (
          <div key={stage.key} className="flex flex-col">
            <div className="flex items-start gap-3">
              {/* Indicator column: circle + connecting line */}
              <div className="flex flex-col items-center">
                <button
                  type="button"
                  aria-label={stage.label}
                  aria-pressed={active}
                  onClick={() => { navigateTo(stage.key); }}
                  className="flex cursor-pointer items-center focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                >
                  <StepIndicator
                    stageKey={stage.key}
                    index={index}
                    active={active}
                    complete={complete}
                  />
                </button>
                {!isLast && !showPopulationSubSteps && (
                  <div className="my-1 w-0.5 flex-1 self-stretch border-l-2 border-slate-200" style={{ minHeight: "1.5rem" }} />
                )}
              </div>

              {/* Label + summary column (hidden when collapsed) */}
              {!collapsed && (
                <div className="flex flex-col pb-4 pt-1.5">
                  <span
                    className={cn(
                      "text-sm font-medium leading-none",
                      active ? "text-slate-900" : "text-slate-600",
                    )}
                  >
                    {stage.label}
                  </span>
                  {summary !== null && (
                    <span
                      data-testid={`summary-${stage.key}`}
                      className="mt-0.5 text-xs text-slate-400"
                    >
                      {summary}
                    </span>
                  )}
                  {/* Story 22.4: Population sub-steps rendered under main stage label */}
                  {showPopulationSubSteps && (
                    <div className="mt-2 flex flex-col gap-1 pl-6">
                      {POPULATION_SUB_STEPS.map((subStep) => {
                        const isActive = subStep.subView === activeSubView;
                        const isDisabled = subStep.key === "explorer" && !explorerPopulationId;

                        return (
                          <SubStepIndicator
                            key={subStep.key}
                            label={subStep.label}
                            active={isActive}
                            disabled={isDisabled}
                            disabledTooltip={isDisabled ? "Select a population to explore" : undefined}
                            onClick={() => { navigateTo("population", subStep.subView); }}
                            testId={`substep-population-${subStep.key}`}
                          />
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Story 22.4: Connecting line after Population stage with sub-steps */}
            {showPopulationSubSteps && !isLast && (
              <div className="ml-[3.5rem] mt-1 w-0.5 flex-1 border-l-2 border-slate-200" style={{ minHeight: "1rem" }} />
            )}
          </div>
        );
      })}
    </nav>
  );
}
