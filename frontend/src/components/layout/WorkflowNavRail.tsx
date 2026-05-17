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
  activeSubView: SubView | null; // Story 27.8 - for active sub-step indication
}

// ============================================================================
// Completion logic (Story 27.6: four-state model with stageTouched)
// ============================================================================

type StageStatus = "not-started" | "active" | "complete" | "incomplete";

/**
 * Get the completion status for a stage.
 *
 * Story 27.6: A stage is "complete" (green) only when:
 * - It has data satisfied AND
 * - The user has explicitly touched it (stageTouched[key] === true)
 *
 * For backward compatibility with legacy scenarios (no stageTouched):
 * - Falls back to old completion logic (data satisfied = complete)
 *
 * Otherwise:
 * - "not-started": no data, not touched
 * - "incomplete": has some data but not satisfied, or touched but not complete
 * - "active": currently active stage
 */
function getStageStatus(
  key: StageKey,
  selectedPopulationId: string,
  dataFusionResult: GenerationResult | null,
  _portfolios: PortfolioListItem[],
  results: ResultListItem[],
  activeScenario: WorkspaceScenario | null,
  activeStage: StageKey,
): StageStatus {
  const isActive = key === activeStage;
  const hasStageTouched = activeScenario?.stageTouched !== undefined;
  const isTouched = activeScenario?.stageTouched?.[key] === true;

  // Check if data requirements are satisfied
  let dataSatisfied = false;
  switch (key) {
    case "policies":
      // AC-5 (Story 20.3): completion requires an active portfolio linked to the scenario
      dataSatisfied = typeof activeScenario?.portfolioName === "string" && activeScenario.portfolioName.length > 0;
      break;
    case "population":
      // AC-5 (Story 20.4): primary signal is activeScenario.populationIds
      // Story 27.6: For new scenarios (with stageTouched), only use durable state,
      // not transient UI selector. For legacy scenarios, keep selector fallback.
      if (hasStageTouched) {
        // New path: only durable scenario state
        dataSatisfied = (
          (activeScenario?.populationIds?.length ?? 0) > 0 ||
          dataFusionResult !== null
        );
      } else {
        // Legacy path: include UI selector fallback
        dataSatisfied = (
          (activeScenario?.populationIds?.length ?? 0) > 0 ||
          !!selectedPopulationId ||
          dataFusionResult !== null
        );
      }
      break;
    case "engine":
      // Story 27.6: engine is complete when scenario exists AND
      // investmentDecisionsEnabled is explicitly set (true or false)
      if (activeScenario !== null) {
        const { investmentDecisionsEnabled } = activeScenario.engineConfig;
        // null = not started, false/true = explicitly decided
        dataSatisfied = investmentDecisionsEnabled !== null;
      }
      break;
    case "results":
      dataSatisfied = results.length > 0;
      break;
  }

  // Backward compatibility: legacy scenarios (no stageTouched) use old logic
  if (!hasStageTouched) {
    // Complete takes precedence over active for legacy scenarios too
    if (dataSatisfied) {
      return "complete";
    }
    if (isActive) {
      return "active";
    }
    return "incomplete";
  }

  // Complete: data satisfied AND touched (complete takes precedence over active)
  if (dataSatisfied && isTouched) {
    return "complete";
  }

  // Active stage gets "active" status if not complete
  if (isActive) {
    return "active";
  }

  // Not started: no data, not touched
  if (!dataSatisfied && !isTouched) {
    return "not-started";
  }

  // Incomplete: has some data but not satisfied, or touched but not complete
  return "incomplete";
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
  status: StageStatus;
}

function StepIndicator({ stageKey, index, status }: StepIndicatorProps) {
  return (
    <div
      data-testid={`step-indicator-${stageKey}`}
      data-active={status === "active" ? "true" : "false"}
      className={cn(
        "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-semibold",
        // Complete: green with checkmark
        status === "complete" && "bg-emerald-500 text-white",
        // Active: blue
        status === "active" && "bg-blue-500 text-white",
        // Incomplete: gray border, white background
        status === "incomplete" && "border-2 border-slate-300 bg-white text-slate-500",
        // Not started (Story 27.6): dashed border, no fill, smaller dot
        status === "not-started" && "border border-dashed border-slate-200 bg-transparent text-slate-400",
      )}
    >
      {status === "complete" ? <Check className="h-4 w-4" /> : <span className={status === "not-started" ? "text-xs" : ""}>{index + 1}</span>}
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
      disabled={disabled}
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
  activeSubView,
}: WorkflowNavRailProps) {
  return (
    <nav aria-label="Workflow navigation" className="flex flex-col gap-0">
      {STAGES.map((stage, index) => {
        const active = stage.activeFor.includes(activeStage);
        const status = getStageStatus(stage.key, selectedPopulationId, dataFusionResult, portfolios, results, activeScenario, activeStage);
        const summary = collapsed
          ? null
          : getSummary(stage.key, selectedPopulationId, dataFusionResult, portfolios, results, activeScenario, populations);
        const isLast = index === STAGES.length - 1;

        // Story 27.8: Population sub-steps (Source, Inspect)
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
                    status={status}
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
                  {/* Story 27.8: Population sub-steps rendered under main stage label */}
                  {showPopulationSubSteps && (
                    <div className="mt-2 flex flex-col gap-1 pl-6">
                      {POPULATION_SUB_STEPS.map((subStep) => {
                        // Source is active when activeSubView is null, "data-fusion", or "source"
                        // Inspect is active when activeSubView is "inspect" or "population-explorer" (legacy)
                        const isActive =
                          subStep.key === "source"
                            ? activeSubView === null || activeSubView === "data-fusion" || activeSubView === "source"
                            : activeSubView === "inspect" || activeSubView === "population-explorer";

                        // Inspect is disabled when no population is selected
                        const hasPopulation = (
                          (activeScenario?.populationIds?.length ?? 0) > 0 ||
                          !!selectedPopulationId ||
                          dataFusionResult !== null
                        );
                        const isDisabled = subStep.key === "inspect" && !hasPopulation;

                        return (
                          <SubStepIndicator
                            key={subStep.key}
                            label={subStep.label}
                            active={isActive}
                            disabled={isDisabled}
                            disabledTooltip={isDisabled ? "Select or build a population first" : undefined}
                            onClick={() => {
                              // Source navigates to null (Library default), Inspect navigates to "inspect"
                              const subView = subStep.key === "source" ? null : "inspect" as const;
                              navigateTo("population", subView);
                            }}
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
