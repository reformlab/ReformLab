// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** ScenarioStageScreen — Stage 4: Scenario Configuration.
 *
 * Two-column layout: left config form (inherited population, time horizon,
 * seed, discount rate) + right panel (RunSummaryPanel + ValidationGate).
 * Toolbar shows scenario name (editable), Save, and Clone.
 *
 * Story 20.5 — AC-1, AC-2, AC-3, AC-4.
 * Story 26.2 — AC-3: Investment decisions moved to dedicated Stage 3.
 * Story 26.3 — AC-1, AC-2, AC-3, AC-7: Renamed from EngineStageScreen,
 * added inherited population summary and runtime summary.
 */

import { useEffect, useMemo, useState } from "react";
import { Save, Copy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { useAppState } from "@/contexts/AppContext";
import { RunSummaryPanel } from "@/components/engine/RunSummaryPanel";
import { ValidationGate } from "@/components/engine/ValidationGate";
import { OriginBadge } from "@/components/population/OriginBadge";
import { formatLogitModelLabel } from "@/lib/utils";
import type { EngineConfig } from "@/types/workspace";

// ============================================================================
// Component
// ============================================================================

export function ScenarioStageScreen() {
  const {
    activeScenario,
    updateScenarioField,
    saveCurrentScenario,
    cloneCurrentScenario,
    createNewScenario,
    navigateTo,
    populations,
    dataFusionResult,
    portfolios,
  } = useAppState();

  // Local state — initialize from scenario (handles reload when scenario already has 2 populations)
  const [hasSecondary, setHasSecondary] = useState(() => (activeScenario?.populationIds?.length ?? 0) > 1);

  // Sync hasSecondary when the active scenario changes (e.g. after clone or load).
  // Depends only on scenario identity — not on populationIds.length — to avoid
  // resetting state while the user is interacting with the secondary dropdown.
  useEffect(() => {
    setHasSecondary((activeScenario?.populationIds?.length ?? 0) > 1);
  }, [activeScenario?.id]);

  // ============================================================================
  // Population list — hook must be before early return
  // ============================================================================

  const allPopulations = useMemo(() => [
    ...populations.map((p) => ({ id: p.id, name: p.name, households: p.households })),
    ...(dataFusionResult ? [{ id: "data-fusion-result", name: "Fused Population", households: dataFusionResult.summary.record_count }] : []),
  ], [populations, dataFusionResult]);

  // ============================================================================
  // Validation context — hook must be before early return
  // ============================================================================

  const validationContext = useMemo(() => ({
    scenario: activeScenario,
    populations,
    dataFusionResult,
    portfolios,
  }), [activeScenario, populations, dataFusionResult, portfolios]);

  // ============================================================================
  // Primary population helper — Story 26.3
  // ============================================================================

  const primaryPopulation = useMemo(() => {
    const primaryId = activeScenario?.populationIds?.[0];
    // Guard: no ID or empty string
    if (!primaryId || primaryId.trim() === "") return null;

    // Check dataFusionResult first (synthetic origin)
    if (primaryId === "data-fusion-result" && dataFusionResult) {
      return {
        id: "data-fusion-result",
        name: "Fused Population",
        households: dataFusionResult.summary.record_count,
        origin: "generated" as const,
      };
    }

    // Check built-in/uploaded populations
    return populations.find((p) => p.id === primaryId) ?? null;
  }, [activeScenario?.populationIds, populations, dataFusionResult]);

  // ============================================================================
  // Runtime mode helper — Story 26.3
  // ============================================================================

  const lastRuntimeMode = useMemo(() => {
    // Story 26.3 AC-3: Show Replay badge only when BOTH lastRunId exists AND
    // lastRunRuntimeMode is "replay". The badge indicates historical metadata,
    // not the current execution mode (which is always Live OpenFisca).
    const hasLastRun = activeScenario?.lastRunId !== null && activeScenario?.lastRunId !== undefined;
    if (hasLastRun && activeScenario?.lastRunRuntimeMode === "replay") {
      return "replay";
    }
    // Fallback: null means no historical replay badge
    return null;
  }, [activeScenario?.lastRunId, activeScenario?.lastRunRuntimeMode]);

  // ============================================================================
  // Null state
  // ============================================================================

  if (!activeScenario) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 p-12 text-center">
        <p className="text-slate-500">No active scenario.</p>
        <Button onClick={() => createNewScenario()}>Start a new scenario</Button>
      </div>
    );
  }

  const engineConfig = activeScenario.engineConfig;
  const { startYear, endYear, seed, discountRate } = engineConfig;

  // Computed helpers
  const horizonValid = startYear < endYear && endYear - startYear <= 50;
  const horizonLabel = horizonValid
    ? `${endYear - startYear}-year projection`
    : startYear >= endYear
      ? "End year must be after start year"
      : "Range too large (max 50 years)";

  const updateEngineConfig = (cfg: EngineConfig) => {
    updateScenarioField("engineConfig", cfg);
  };

  const primaryId = activeScenario.populationIds[0] ?? "";
  const secondaryId = activeScenario.populationIds[1] ?? "";

  const handleSecondaryPopChange = (id: string) => {
    updateScenarioField("populationIds", [primaryId, id]);
  };

  const handleRemoveSecondary = () => {
    setHasSecondary(false);
    updateScenarioField("populationIds", primaryId ? [primaryId] : []);
  };

  // ============================================================================
  // Seed
  // ============================================================================

  const seedEnabled = seed !== null;

  const handleSeedToggle = (enabled: boolean) => {
    updateEngineConfig({ ...engineConfig, seed: enabled ? 42 : null });
  };

  const handleSeedValue = (value: number) => {
    updateEngineConfig({ ...engineConfig, seed: value });
  };

  // ============================================================================
  // Discount rate
  // ============================================================================

  const discountRatePct = Math.round(discountRate * 100 * 10) / 10;

  const handleDiscountRateSlider = (value: number) => {
    updateEngineConfig({ ...engineConfig, discountRate: value / 100 });
  };

  // ============================================================================
  // Render
  // ============================================================================

  return (
    <div className="flex flex-col h-full">
      {/* ─── Toolbar ─────────────────────────────────────────────────────── */}
      <div className="flex items-center gap-3 px-6 py-3 border-b border-slate-200 bg-white">
        <Input
          key={activeScenario.id}
          className="max-w-xs font-medium"
          defaultValue={activeScenario.name}
          maxLength={80}
          aria-label="Scenario name"
          onBlur={(e) => {
            const v = e.target.value.trim();
            if (v && v !== activeScenario.name) updateScenarioField("name", v);
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              const v = (e.target as HTMLInputElement).value.trim();
              if (v && v !== activeScenario.name) updateScenarioField("name", v);
              (e.target as HTMLInputElement).blur();
            }
          }}
        />
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            saveCurrentScenario();
          }}
        >
          <Save className="h-4 w-4 mr-1" />
          Save Scenario
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={cloneCurrentScenario}
        >
          <Copy className="h-4 w-4 mr-1" />
          Clone Scenario
        </Button>
      </div>

      {/* ─── Body ────────────────────────────────────────────────────────── */}
      {/* Story 22.7: Stack vertically on mobile, side-by-side on desktop */}
      <div className="flex flex-1 overflow-auto flex-col lg:flex-row">
        {/* Left: configuration form */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 min-w-0">
          <h2 className="text-xl font-semibold text-slate-900">Scenario Configuration</h2>

          {/* Inherited Primary Population — Story 26.3 */}
          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-700">Primary Population</h3>
              <span className="text-xs text-slate-400">Inherited from Stage 2</span>
            </div>

            {primaryPopulation ? (
              <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg border border-slate-200">
                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-slate-900">{primaryPopulation.name}</span>
                    <OriginBadge origin={primaryPopulation.origin} />
                  </div>
                  <p className="text-xs text-slate-600">
                    {primaryPopulation.households.toLocaleString()} households
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 text-xs text-blue-600 hover:text-blue-700 px-2"
                  onClick={() => navigateTo("population")}
                >
                  Change in Stage 2
                </Button>
              </div>
            ) : (
              <div className="p-3 bg-amber-50 rounded-lg border border-amber-200">
                <p className="text-sm text-amber-800">No population selected.</p>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-2 h-7 text-xs"
                  onClick={() => navigateTo("population")}
                >
                  Go to Stage 2 to select a population
                </Button>
              </div>
            )}
          </section>

          <Separator />

          {/* Runtime — Story 26.3 */}
          <section className="space-y-3">
            <h3 className="text-sm font-semibold text-slate-700">Runtime</h3>
            <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg border border-slate-200">
              {/* Always show Live OpenFisca - this is the current execution mode */}
              <Badge variant="outline" className="text-xs border-emerald-600 text-emerald-700">
                Live OpenFisca
              </Badge>
              <p className="text-xs text-slate-600 flex-1">
                Live execution uses OpenFisca engine for real-time policy calculations.
              </p>
              {/* Optional: Replay badge indicates historical mode of last run */}
              {lastRuntimeMode === "replay" && (
                <Badge variant="outline" className="text-xs border-amber-600 text-amber-700">
                  Replay
                </Badge>
              )}
            </div>
          </section>

          <Separator />

          {/* Time Horizon */}
          <section className="space-y-3">
            <h3 className="text-sm font-semibold text-slate-700">Time Horizon</h3>
            <div className="flex items-center gap-3">
              <div className="space-y-1">
                <label className="text-xs text-slate-500">Start year</label>
                <Input
                  type="number"
                  min={1990}
                  max={2100}
                  value={startYear}
                  className="w-28"
                  aria-label="Start year"
                  onChange={(e) => {
                    const v = parseInt(e.target.value, 10);
                    if (!isNaN(v)) updateEngineConfig({ ...engineConfig, startYear: v });
                  }}
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs text-slate-500">End year</label>
                <Input
                  type="number"
                  min={1990}
                  max={2100}
                  value={endYear}
                  className="w-28"
                  aria-label="End year"
                  onChange={(e) => {
                    const v = parseInt(e.target.value, 10);
                    if (!isNaN(v)) updateEngineConfig({ ...engineConfig, endYear: v });
                  }}
                />
              </div>
            </div>
            <p className={`text-xs ${horizonValid ? "text-slate-500" : "text-red-600"}`}>
              {horizonLabel}
            </p>
          </section>

          <Separator />

          {/* Sensitivity Population (Optional) — Story 26.3 */}
          <section className="space-y-3">
            <h3 className="text-sm font-semibold text-slate-700">Sensitivity Population (Optional)</h3>
            <div className="space-y-2">
              {hasSecondary && (
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <label className="text-xs text-slate-500">Secondary population (sensitivity)</label>
                    <button
                      type="button"
                      className="text-xs text-slate-400 hover:text-slate-600"
                      onClick={handleRemoveSecondary}
                    >
                      × Remove
                    </button>
                  </div>
                  <select
                    className="w-full rounded border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-400"
                    value={secondaryId}
                    aria-label="Secondary population"
                    onChange={(e) => handleSecondaryPopChange(e.target.value)}
                  >
                    <option value="">— Select population —</option>
                    {allPopulations.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({p.households.toLocaleString()})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {!hasSecondary && (
                <button
                  type="button"
                  className="text-sm text-blue-600 underline"
                  onClick={() => setHasSecondary(true)}
                >
                  + Add population for sensitivity
                </button>
              )}
            </div>
          </section>

          <Separator />

          {/* Random Seed */}
          <section className="space-y-3">
            <h3 className="text-sm font-semibold text-slate-700">Random Seed</h3>
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="seed-enabled"
                className="rounded border-slate-300"
                checked={seedEnabled}
                onChange={(e) => handleSeedToggle(e.target.checked)}
                aria-label="Use deterministic seed"
              />
              <label htmlFor="seed-enabled" className="text-sm text-slate-700">
                Use deterministic seed
              </label>
              {seedEnabled && (
                <Input
                  type="number"
                  min={0}
                  className="w-28"
                  value={seed ?? 42}
                  aria-label="Seed value"
                  onChange={(e) => {
                    const v = parseInt(e.target.value, 10);
                    if (!isNaN(v)) handleSeedValue(v);
                  }}
                />
              )}
            </div>
          </section>

          <Separator />

          {/* Investment Decisions Summary */}
          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-700">Investment Decisions</h3>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 text-xs text-blue-600 hover:text-blue-700 px-2"
                onClick={() => navigateTo("investment-decisions")}
              >
                Configure in Stage 3
              </Button>
            </div>
            <div className="text-xs text-slate-600">
              {engineConfig.investmentDecisionsEnabled ? (
                <span>
                  Enabled — {engineConfig.logitModel ? formatLogitModelLabel(engineConfig.logitModel) : "no model selected"}
                </span>
              ) : (
                <span>Disabled</span>
              )}
            </div>
          </section>

          <Separator />

          {/* Discount Rate */}
          <section className="space-y-3">
            <h3 className="text-sm font-semibold text-slate-700">Discount Rate</h3>
            <div className="flex items-center gap-4">
              <Slider
                min={0}
                max={10}
                step={0.5}
                value={[discountRatePct]}
                onValueChange={([v]) => handleDiscountRateSlider(v!)}
                className="flex-1"
                aria-label="Discount rate"
              />
              <Input
                type="number"
                min={0}
                max={10}
                step={0.5}
                className="w-20"
                value={discountRatePct}
                aria-label="Discount rate value"
                onChange={(e) => {
                  const v = parseFloat(e.target.value);
                  if (!isNaN(v) && v >= 0 && v <= 10) handleDiscountRateSlider(v);
                }}
              />
              <span className="text-sm text-slate-600 whitespace-nowrap">{discountRatePct}%</span>
            </div>
          </section>
        </div>

        {/* Right: summary + validation */}
        {/* Story 22.7: Full width on mobile, fixed width on desktop */}
        <div className="w-full lg:w-80 flex-shrink-0 border-l border-slate-200 p-4 space-y-4 overflow-y-auto bg-slate-50">
          <RunSummaryPanel
            scenario={activeScenario}
            populations={populations}
            portfolios={portfolios}
            dataFusionResult={dataFusionResult}
            runtime_mode={lastRuntimeMode}
          />
          <ValidationGate
            context={validationContext}
            onRun={() => navigateTo("results", "runner")}
            onStageNavigate={(stage) => navigateTo(stage)}
            runLoading={false}
          />
        </div>
      </div>
    </div>
  );
}
