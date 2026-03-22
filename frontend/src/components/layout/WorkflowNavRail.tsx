/**
 * WorkflowNavRail — vertical stepper navigation for the left panel.
 *
 * Displays the four workflow stages (Population → Portfolio → Simulation → Results)
 * with completion indicators, summary lines, and connecting lines between steps.
 * Supports a collapsed variant that shows only step indicator icons.
 *
 * Story 18.1 — AC-1 through AC-6.
 */

import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import type { GenerationResult, PortfolioListItem, ResultListItem } from "@/api/types";

// ============================================================================
// Types
// ============================================================================

type WorkflowViewMode =
  | "configuration"
  | "run"
  | "progress"
  | "results"
  | "comparison"
  | "decisions"
  | "data-fusion"
  | "portfolio"
  | "runner";

export interface WorkflowNavRailProps {
  viewMode: WorkflowViewMode;
  setViewMode: (mode: WorkflowViewMode) => void;
  collapsed: boolean;
  selectedPopulationId: string;
  dataFusionResult: GenerationResult | null;
  portfolios: PortfolioListItem[];
  results: ResultListItem[];
}

// ============================================================================
// Stage definitions
// ============================================================================

type StageKey = "data-fusion" | "portfolio" | "runner" | "results";

interface Stage {
  key: StageKey;
  summaryKey: string;
  label: string;
  targetMode: WorkflowViewMode;
  activeFor: WorkflowViewMode[];
}

const STAGES: Stage[] = [
  {
    key: "data-fusion",
    summaryKey: "population",
    label: "Population",
    targetMode: "data-fusion",
    activeFor: ["data-fusion"],
  },
  {
    key: "portfolio",
    summaryKey: "portfolio",
    label: "Portfolio",
    targetMode: "portfolio",
    activeFor: ["portfolio"],
  },
  {
    key: "runner",
    summaryKey: "simulation",
    label: "Simulation",
    targetMode: "runner",
    activeFor: ["runner", "configuration", "run", "progress"],
  },
  {
    key: "results",
    summaryKey: "results",
    label: "Results",
    targetMode: "results",
    activeFor: ["results", "comparison", "decisions"],
  },
];

// ============================================================================
// Helpers
// ============================================================================

function isPopulationComplete(
  selectedPopulationId: string,
  dataFusionResult: GenerationResult | null,
): boolean {
  return !!selectedPopulationId || dataFusionResult !== null;
}

function getSummary(
  key: StageKey,
  selectedPopulationId: string,
  dataFusionResult: GenerationResult | null,
  portfolios: PortfolioListItem[],
  results: ResultListItem[],
): string | null {
  switch (key) {
    case "data-fusion": {
      if (dataFusionResult) {
        const count = dataFusionResult.summary.record_count.toLocaleString();
        return `${count} records`;
      }
      if (selectedPopulationId) {
        return selectedPopulationId;
      }
      return null;
    }
    case "portfolio": {
      if (portfolios.length === 0) return null;
      const n = portfolios.length;
      return `${n} portfolio${n !== 1 ? "s" : ""}`;
    }
    case "runner": {
      if (results.length === 0) return null;
      const n = results.length;
      return `${n} run${n !== 1 ? "s" : ""}`;
    }
    case "results": {
      const completed = results.filter((r) => r.data_available);
      if (completed.length === 0) return null;
      return `${completed.length} completed`;
    }
  }
}

function isComplete(
  key: StageKey,
  selectedPopulationId: string,
  dataFusionResult: GenerationResult | null,
  portfolios: PortfolioListItem[],
  results: ResultListItem[],
): boolean {
  switch (key) {
    case "data-fusion":
      return isPopulationComplete(selectedPopulationId, dataFusionResult);
    case "portfolio":
      return portfolios.length > 0;
    case "runner":
      return results.length > 0;
    case "results":
      return results.some((r) => r.data_available);
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
  viewMode,
  setViewMode,
  collapsed,
  selectedPopulationId,
  dataFusionResult,
  portfolios,
  results,
}: WorkflowNavRailProps) {
  return (
    <nav aria-label="Workflow navigation" className="flex flex-col gap-0">
      {STAGES.map((stage, index) => {
        const active = (stage.activeFor as string[]).includes(viewMode);
        const complete = isComplete(stage.key, selectedPopulationId, dataFusionResult, portfolios, results);
        const summary = collapsed
          ? null
          : getSummary(stage.key, selectedPopulationId, dataFusionResult, portfolios, results);
        const summaryTestId = `summary-${stage.summaryKey}`;
        const isLast = index === STAGES.length - 1;

        return (
          <div key={stage.key} className="flex flex-col">
            <div className="flex items-start gap-3">
              {/* Indicator column: circle + connecting line */}
              <div className="flex flex-col items-center">
                <button
                  type="button"
                  aria-label={stage.label}
                  onClick={() => setViewMode(stage.targetMode)}
                  className="flex cursor-pointer items-center focus:outline-none"
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
                      data-testid={summaryTestId}
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
