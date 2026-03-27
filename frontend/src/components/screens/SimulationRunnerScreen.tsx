// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Simulation Runner Screen — Story 20.6, AC-2.
 *
 * Refactored to use WorkspaceScenario from AppContext instead of legacy props.
 *
 * Three internal sub-views:
 *   1. Pre-run summary — Configure and start a simulation run.
 *   2. Progress     — Client-side year-by-year progress simulation.
 *   3. Post-run     — ResultDetailView + ResultsListPanel.
 */

import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ErrorAlert, type ErrorState } from "@/components/simulation/ErrorAlert";
import { RunProgressBar } from "@/components/simulation/RunProgressBar";
import { ResultDetailView } from "@/components/simulation/ResultDetailView";
import { ResultsListPanel } from "@/components/simulation/ResultsListPanel";
import { runScenario } from "@/api/runs";
import { listResults, exportResultCsv, exportResultParquet } from "@/api/results";
import type { ResultDetailResponse, ResultListItem } from "@/api/types";
import { useAppState } from "@/contexts/AppContext";

// ============================================================================
// Types
// ============================================================================

type SubView = "configure" | "progress" | "post-run";

interface SimulationRunnerScreenProps {
  onCancel: () => void;
}

// ============================================================================
// SimulationRunnerScreen
// ============================================================================

export function SimulationRunnerScreen({ onCancel }: SimulationRunnerScreenProps) {
  const {
    activeScenario,
    updateExecutionCell,
    updateScenarioField,
  } = useAppState();

  const [subView, setSubView] = useState<SubView>("configure");
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState("Preparing...");
  const [eta, setEta] = useState("calculating...");
  const [error, setError] = useState<ErrorState | null>(null);
  const [currentPopulationId, setCurrentPopulationId] = useState<string | null>(null);

  // Post-run state
  const [lastRunId, setLastRunId] = useState<string | null>(null);
  const [lastRunDetail, setLastRunDetail] = useState<ResultDetailResponse | null>(null);
  const [results, setResults] = useState<ResultListItem[]>([]);
  const [selectedResultId, setSelectedResultId] = useState<string | null>(null);
  const [selectedDetail, setSelectedDetail] = useState<ResultDetailResponse | null>(null);

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const fetchResults = useCallback(async () => {
    try {
      const data = await listResults();
      setResults(data);
    } catch {
      // Non-fatal — list just won't update
    }
  }, []);

  const handleStartRun = useCallback(async () => {
    if (!activeScenario) {
      setError({
        what: "No scenario selected",
        why: "Please create or select a scenario before running",
        fix: "Go to the Policies stage to create a scenario",
      });
      return;
    }

    if (activeScenario.populationIds.length === 0) {
      setError({
        what: "No population selected",
        why: "Please select at least one population before running",
        fix: "Go to the Population stage to select a population",
      });
      return;
    }

    // Use the first population ID for now (multi-population support in future stories)
    const populationId = currentPopulationId ?? activeScenario.populationIds[0] ?? null;

    setError(null);
    setSubView("progress");
    setProgress(0);
    setCurrentStep(`Computing year ${activeScenario.engineConfig.startYear}...`);

    const totalYears = activeScenario.engineConfig.endYear - activeScenario.engineConfig.startYear + 1;
    const estimatedMs = totalYears * 1500;
    const tickMs = estimatedMs / totalYears;
    let currentYear = activeScenario.engineConfig.startYear;

    // Update matrix cell to RUNNING
    updateExecutionCell(activeScenario.id, populationId, {
      status: "RUNNING",
      startedAt: new Date().toISOString(),
    });

    timerRef.current = setInterval(() => {
      currentYear++;
      if (currentYear <= activeScenario.engineConfig.endYear) {
        const pct = Math.round(((currentYear - activeScenario.engineConfig.startYear) / totalYears) * 90);
        setProgress(pct);
        setCurrentStep(`Computing year ${currentYear}...`);
        const remaining = activeScenario.engineConfig.endYear - currentYear;
        setEta(`~${Math.ceil((remaining * tickMs) / 1000)}s`);
      }
    }, tickMs);

    try {
      const result = await runScenario({
        template_name: activeScenario.portfolioName ?? activeScenario.policyType ?? "carbon_tax",
        policy: {},
        start_year: activeScenario.engineConfig.startYear,
        end_year: activeScenario.engineConfig.endYear,
        population_id: populationId,
        seed: activeScenario.engineConfig.seed ?? undefined,
      });

      clearTimer();
      setProgress(100);
      setCurrentStep("Complete");
      setLastRunId(result.run_id);

      // Update matrix cell to COMPLETED
      updateExecutionCell(activeScenario.id, populationId, {
        status: "COMPLETED",
        runId: result.run_id,
        finishedAt: new Date().toISOString(),
      });

      // Update activeScenario.lastRunId
      if (activeScenario) {
        updateScenarioField("lastRunId", result.run_id);
      }

      // Brief pause then switch to post-run
      await new Promise((resolve) => setTimeout(resolve, 500));

      // Load full detail for the just-completed run
      const { getResult } = await import("@/api/results");
      try {
        const detail = await getResult(result.run_id);
        setLastRunDetail(detail);
        setSelectedDetail(detail);
        setSelectedResultId(result.run_id);
      } catch {
        // Fallback — show without detail
      }

      await fetchResults();
      setSubView("post-run");
    } catch (err: unknown) {
      clearTimer();

      // Update matrix cell to FAILED
      updateExecutionCell(activeScenario.id, populationId, {
        status: "FAILED",
        error: err instanceof Error ? err.message : String(err),
      });

      if (err && typeof err === "object" && "what" in err) {
        const apiErr = err as { what: string; why: string; fix: string };
        setError({ what: apiErr.what, why: apiErr.why, fix: apiErr.fix });
      } else {
        const msg = err instanceof Error ? err.message : String(err);
        setError({ what: "Simulation failed", why: msg, fix: "Check the server logs for details" });
      }
    }
  }, [
    activeScenario,
    currentPopulationId,
    updateExecutionCell,
    clearTimer,
    fetchResults,
  ]);

  // Load initial results list on mount
  useEffect(() => {
    void fetchResults();
  }, [fetchResults]);

  // Cleanup timer on unmount
  useEffect(() => clearTimer, [clearTimer]);

  // Sync currentPopulationId with activeScenario.populationIds
  useEffect(() => {
    if (activeScenario && activeScenario.populationIds.length > 0) {
      if (!currentPopulationId || !activeScenario.populationIds.includes(currentPopulationId)) {
        setCurrentPopulationId(activeScenario.populationIds[0]);
      }
    }
  }, [activeScenario, currentPopulationId]);

  const handleSelectResult = useCallback(async (runId: string) => {
    setSelectedResultId(runId);
    try {
      const { getResult } = await import("@/api/results");
      const detail = await getResult(runId);
      setSelectedDetail(detail);
    } catch {
      setSelectedDetail(null);
    }
  }, []);

  const handleDeleteResult = useCallback(async (runId: string) => {
    const { deleteResult } = await import("@/api/results");
    await deleteResult(runId);
    if (selectedResultId === runId) {
      setSelectedResultId(null);
      setSelectedDetail(null);
    }
    await fetchResults();
  }, [selectedResultId, fetchResults]);

  // -------------------------------------------------------------------------
  // Sub-view: Configure
  // -------------------------------------------------------------------------

  if (subView === "configure") {
    return (
      <section className="space-y-3" aria-label="Simulation runner configuration">
        <div className="rounded-lg border border-slate-200 bg-white p-3">
          <h2 className="text-base font-semibold text-slate-900">Run Simulation</h2>
          <p className="mt-1 text-xs text-slate-500">
            Configure and execute a full multi-year simulation run.
          </p>
        </div>

        {/* Scenario summary */}
        {activeScenario ? (
          <div className="rounded-lg border border-slate-200 bg-white p-3 space-y-2">
            <p className="text-xs font-semibold uppercase text-slate-500 mb-2">Scenario</p>

            <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
              <span className="text-slate-500">Name</span>
              <span className="font-medium text-slate-800">{activeScenario.name}</span>

              <span className="text-slate-500">Portfolio</span>
              <span className="font-medium text-slate-800">
                {activeScenario.portfolioName ?? (
                  <span className="text-amber-600">no portfolio selected</span>
                )}
              </span>

              <span className="text-slate-500">Population</span>
              <span className="font-medium text-slate-800">
                {activeScenario.populationIds.length > 0
                  ? `${activeScenario.populationIds.length} population(s) selected`
                  : <span className="text-amber-600">no population selected</span>
                }
              </span>
            </div>
          </div>
        ) : (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
            <p className="text-xs text-amber-800">
              No scenario selected. Please create or select a scenario first.
            </p>
          </div>
        )}

        {/* Configuration summary */}
        <div className="rounded-lg border border-slate-200 bg-white p-3 space-y-2">
          <p className="text-xs font-semibold uppercase text-slate-500 mb-2">Run Configuration</p>

          <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
            <span className="text-slate-500">Start year</span>
            <Input
              type="number"
              value={activeScenario?.engineConfig.startYear ?? 2025}
              min={2020}
              max={activeScenario?.engineConfig.endYear ? activeScenario.engineConfig.endYear - 1 : 2049}
              onChange={(e) => {
                if (activeScenario) {
                  updateScenarioField("engineConfig", {
                    ...activeScenario.engineConfig,
                    startYear: Number(e.target.value),
                  });
                }
              }}
              className="w-24 h-auto py-0.5 text-xs font-mono"
              aria-label="Start year"
            />

            <span className="text-slate-500">End year</span>
            <Input
              type="number"
              value={activeScenario?.engineConfig.endYear ?? 2030}
              min={activeScenario?.engineConfig.startYear ? activeScenario.engineConfig.startYear + 1 : 2021}
              max={2050}
              onChange={(e) => {
                if (activeScenario) {
                  updateScenarioField("engineConfig", {
                    ...activeScenario.engineConfig,
                    endYear: Number(e.target.value),
                  });
                }
              }}
              className="w-24 h-auto py-0.5 text-xs font-mono"
              aria-label="End year"
            />

            <span className="text-slate-500">Seed</span>
            <Input
              type="number"
              value={activeScenario?.engineConfig.seed ?? ""}
              placeholder="random"
              onChange={(e) => {
                if (activeScenario) {
                  updateScenarioField("engineConfig", {
                    ...activeScenario.engineConfig,
                    seed: e.target.value === "" ? null : Number(e.target.value),
                  });
                }
              }}
              className="w-24 h-auto py-0.5 text-xs font-mono"
              aria-label="Random seed"
            />
          </div>
        </div>

        <div className="flex gap-2">
          <Button
            onClick={() => void handleStartRun()}
            aria-label="Run simulation"
            disabled={!activeScenario || activeScenario.populationIds.length === 0}
          >
            Run Simulation
          </Button>
          <Button variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        </div>

        {/* Past results list on configure view */}
        {results.length > 0 ? (
          <ResultsListPanel
            results={results}
            selectedRunId={selectedResultId}
            onSelect={(id) => void handleSelectResult(id)}
            onDelete={(id) => void handleDeleteResult(id)}
          />
        ) : null}

        {selectedDetail !== null ? (
          <ResultDetailView
            detail={selectedDetail}
            onExportCsv={() => void exportResultCsv(selectedDetail.run_id)}
            onExportParquet={() => void exportResultParquet(selectedDetail.run_id)}
          />
        ) : null}
      </section>
    );
  }

  // -------------------------------------------------------------------------
  // Sub-view: Progress
  // -------------------------------------------------------------------------

  if (subView === "progress") {
    if (error !== null) {
      return (
        <section aria-label="Simulation error" className="space-y-3">
          <ErrorAlert what={error.what} why={error.why} fix={error.fix} />
          <Button variant="outline" onClick={() => { setSubView("configure"); setError(null); }}>
            Back to Configuration
          </Button>
        </section>
      );
    }

    return (
      <RunProgressBar
        progress={progress}
        currentStep={currentStep}
        eta={eta}
        onCancel={() => { clearTimer(); setSubView("configure"); }}
      />
    );
  }

  // -------------------------------------------------------------------------
  // Sub-view: Post-run
  // -------------------------------------------------------------------------

  return (
    <section className="space-y-3" aria-label="Simulation results">
      {lastRunId !== null ? (
        <div className="border border-emerald-200 bg-emerald-50 p-2">
          <p className="text-xs text-emerald-800">
            Run <span className="data-mono font-medium">{lastRunId.slice(0, 8)}</span> completed.
          </p>
        </div>
      ) : null}

      {lastRunDetail !== null || selectedDetail !== null ? (
        <ResultDetailView
          detail={(selectedDetail ?? lastRunDetail)!}
          onExportCsv={() => { const d = selectedDetail ?? lastRunDetail; if (d) void exportResultCsv(d.run_id); }}
          onExportParquet={() => { const d = selectedDetail ?? lastRunDetail; if (d) void exportResultParquet(d.run_id); }}
        />
      ) : null}

      <ResultsListPanel
        results={results}
        selectedRunId={selectedResultId}
        onSelect={(id) => void handleSelectResult(id)}
        onDelete={(id) => void handleDeleteResult(id)}
      />

      <div className="flex gap-2">
        <Button variant="outline" onClick={() => setSubView("configure")}>
          New Run
        </Button>
        <Button variant="outline" onClick={onCancel}>
          Back
        </Button>
      </div>
    </section>
  );
}
