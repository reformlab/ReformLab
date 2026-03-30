// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Pre-flight scenario summary card for Stage 3 (Scenario).
 *
 * Compact read-only summary of what will be computed: scenario name, portfolio,
 * population(s), time horizon, investment decisions, seed, and estimated runs.
 *
 * Story 20.5 — AC-3.
 */

import type { WorkspaceScenario } from "@/types/workspace";
import type { PortfolioListItem } from "@/api/types";
import type { Population } from "@/data/mock-data";
import type { GenerationResult } from "@/api/types";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

// ============================================================================
// Types
// ============================================================================

interface RunSummaryPanelProps {
  scenario: WorkspaceScenario | null;
  populations: Population[];
  portfolios: PortfolioListItem[];
  dataFusionResult: GenerationResult | null;
}

// ============================================================================
// Component
// ============================================================================

export function RunSummaryPanel({ scenario, populations, portfolios, dataFusionResult }: RunSummaryPanelProps) {
  if (!scenario) {
    return (
      <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
        No active scenario.
      </div>
    );
  }

  const { engineConfig, populationIds, portfolioName, isBaseline, baselineRef, name, status } = scenario;
  const { startYear, endYear, seed, investmentDecisionsEnabled, logitModel } = engineConfig;

  // Status badge variant
  const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
    draft: "secondary",
    ready: "default",
    running: "outline",
    completed: "default",
    failed: "destructive",
  };

  // Portfolio info
  const portfolio = portfolioName ? portfolios.find((p) => p.name === portfolioName) : null;

  // Population names
  const allPopulations: { id: string; name: string; households: number }[] = [
    ...populations.map((p) => ({ id: p.id, name: p.name, households: p.households })),
    ...(dataFusionResult ? [{ id: "data-fusion-result", name: "Fused Population", households: dataFusionResult.summary.record_count }] : []),
  ];

  const selectedPops = populationIds.map((id) => allPopulations.find((p) => p.id === id)).filter(Boolean);

  // Time horizon
  const horizonYears = endYear - startYear;
  const horizonValid = startYear < endYear && horizonYears <= 50;

  // Investment decisions label
  const investmentLabel = investmentDecisionsEnabled
    ? `Enabled (${logitModel?.replace(/_/g, " ") ?? "logit model"})`
    : "Disabled";

  // Total runs — 0 when no population selected (not "1 run")
  const totalRuns = populationIds.filter((id) => id.trim().length > 0).length;

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between gap-2">
        <span className="font-medium text-slate-900 truncate">{name}</span>
        <Badge variant={statusVariant[status] ?? "secondary"}>{status}</Badge>
      </div>

      <Separator />

      {/* Baseline indicator */}
      <div className="flex justify-between text-slate-600">
        <span className="text-slate-500">Type</span>
        <span>{isBaseline ? "[Baseline]" : `[Reform${baselineRef ? ` vs ${baselineRef}` : ""}]`}</span>
      </div>

      {/* Portfolio */}
      <div className="flex justify-between">
        <span className="text-slate-500">Portfolio</span>
        {portfolioName ? (
          <span className="text-slate-700">
            {portfolioName}
            {portfolio ? ` (${portfolio.policy_count} policies)` : ""}
          </span>
        ) : (
          <span className="text-red-500">— no portfolio</span>
        )}
      </div>

      {/* Population(s) */}
      <div className="flex justify-between">
        <span className="text-slate-500">Population</span>
        {selectedPops.length > 0 ? (
          <span className="text-slate-700 text-right">
            {selectedPops.map((p, i) => (
              <span key={p!.id}>
                {p!.name} ({p!.households.toLocaleString()})
                {i < selectedPops.length - 1 ? ", " : ""}
              </span>
            ))}
          </span>
        ) : (
          <span className="text-red-500">— no population</span>
        )}
      </div>

      {/* Time horizon */}
      <div className="flex justify-between">
        <span className="text-slate-500">Time horizon</span>
        {horizonValid ? (
          <span className="text-slate-700">
            {startYear} – {endYear} ({horizonYears} years)
          </span>
        ) : (
          <span className="text-red-500">
            {startYear >= endYear ? "Invalid range" : "Range too large (>50yr)"}
          </span>
        )}
      </div>

      {/* Investment decisions */}
      <div className="flex justify-between">
        <span className="text-slate-500">Inv. decisions</span>
        <span className="text-slate-700">{investmentLabel}</span>
      </div>

      {/* Seed */}
      <div className="flex justify-between">
        <span className="text-slate-500">Seed</span>
        <span className="text-slate-700">
          {seed !== null ? `Fixed (seed: ${seed})` : "Random"}
        </span>
      </div>

      <Separator />

      {/* Estimated runs */}
      <div className="flex justify-between font-medium">
        <span className="text-slate-600">Estimated runs</span>
        <span className={totalRuns === 0 ? "text-red-500" : "text-slate-900"}>
          {totalRuns === 0 ? "— no population" : `${totalRuns} ${totalRuns === 1 ? "run" : "runs"}`}
        </span>
      </div>
    </div>
  );
}
