// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * WorkflowNavRail — vertical stepper navigation for the left panel.
 *
 * Displays the four canonical workflow stages (Policies & Portfolio → Population →
 * Engine → Run / Results / Compare) with completion indicators, summary lines,
 * and connecting lines between steps.
 * Supports a collapsed variant that shows only step indicator icons.
 *
 * Story 20.1 — AC-1, refactored from Story 18.1.
 */

import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import type { GenerationResult, PortfolioListItem, ResultListItem, PopulationItem } from "@/api/types";
import type { StageKey, WorkspaceScenario } from "@/types/workspace";
import { STAGES } from "@/types/workspace";

// ============================================================================
// Types
// ============================================================================

export interface WorkflowNavRailProps {
  activeStage: StageKey;
  navigateTo: (stage: StageKey) => void;
  collapsed: boolean;
  selectedPopulationId: string;
  dataFusionResult: GenerationResult | null;
  portfolios: PortfolioListItem[];
  results: ResultListItem[];
  activeScenario: WorkspaceScenario | null;
  populations: PopulationItem[];
}

// ============================================================================
// Completion logic
// ============================================================================

function isComplete(
  key: StageKey,
  selectedPopulationId: string,
  dataFusionResult: GenerationResult | null,
  portfolios: PortfolioListItem[],
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
  portfolios: PortfolioListItem[],
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
                {!isLast && (
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
                </div>
              )}
            </div>
          </div>
        );
      })}
    </nav>
  );
}
