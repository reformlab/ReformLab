/** Simulation Runner Screen — Story 17.3, AC-1, AC-2, AC-3, AC-4.
 *
 * Three internal sub-views:
 *   1. Pre-run summary — Configure and start a simulation run.
 *   2. Progress     — Client-side year-by-year progress simulation.
 *   3. Post-run     — ResultDetailView + ResultsListPanel.
 */

import { useCallback, useEffect, useRef, useState } from "react";

import { AlertCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { RunProgressBar } from "@/components/simulation/RunProgressBar";
import { ResultDetailView } from "@/components/simulation/ResultDetailView";
import { ResultsListPanel } from "@/components/simulation/ResultsListPanel";
import { runScenario } from "@/api/runs";
import { listResults, exportResultCsv, exportResultParquet } from "@/api/results";
import type { ResultDetailResponse, ResultListItem } from "@/api/types";

// ============================================================================
// Types
// ============================================================================

type SubView = "configure" | "progress" | "post-run";

interface ErrorState {
  what: string;
  why: string;
  fix: string;
}

interface SimulationRunnerScreenProps {
  selectedPopulationId: string | null;
  selectedPortfolioName: string | null;
  selectedTemplateName: string | null;
  onCancel: () => void;
}

// ============================================================================
// SimulationRunnerScreen
// ============================================================================

export function SimulationRunnerScreen({
  selectedPopulationId,
  selectedPortfolioName,
  selectedTemplateName,
  onCancel,
}: SimulationRunnerScreenProps) {
  const [subView, setSubView] = useState<SubView>("configure");
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState("Preparing...");
  const [eta, setEta] = useState("calculating...");
  const [error, setError] = useState<ErrorState | null>(null);

  // Pre-run config local state
  const [startYear, setStartYear] = useState(2025);
  const [endYear, setEndYear] = useState(2030);
  const [seed, setSeed] = useState<number | null>(null);

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
    setError(null);
    setSubView("progress");
    setProgress(0);
    setCurrentStep(`Computing year ${startYear}...`);

    const totalYears = endYear - startYear + 1;
    const estimatedMs = totalYears * 1500;
    const tickMs = estimatedMs / totalYears;
    let currentYear = startYear;

    timerRef.current = setInterval(() => {
      currentYear++;
      if (currentYear <= endYear) {
        const pct = Math.round(((currentYear - startYear) / totalYears) * 90);
        setProgress(pct);
        setCurrentStep(`Computing year ${currentYear}...`);
        const remaining = endYear - currentYear;
        setEta(`~${Math.ceil((remaining * tickMs) / 1000)}s`);
      }
    }, tickMs);

    try {
      const result = await runScenario({
        template_name: selectedTemplateName ?? selectedPortfolioName ?? "carbon_tax",
        parameters: {},
        start_year: startYear,
        end_year: endYear,
        population_id: selectedPopulationId,
        seed: seed ?? undefined,
      });

      clearTimer();
      setProgress(100);
      setCurrentStep("Complete");
      setLastRunId(result.run_id);

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
      if (err && typeof err === "object" && "what" in err) {
        const apiErr = err as { what: string; why: string; fix: string };
        setError({ what: apiErr.what, why: apiErr.why, fix: apiErr.fix });
      } else {
        const msg = err instanceof Error ? err.message : String(err);
        setError({ what: "Simulation failed", why: msg, fix: "Check the server logs for details" });
      }
    }
  }, [
    startYear, endYear, seed,
    selectedPopulationId, selectedPortfolioName, selectedTemplateName,
    clearTimer, fetchResults,
  ]);

  // Load initial results list on mount
  useEffect(() => {
    void fetchResults();
  }, [fetchResults]);

  // Cleanup timer on unmount
  useEffect(() => clearTimer, [clearTimer]);

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
        <div className="border border-slate-200 bg-white p-3">
          <h2 className="text-base font-semibold text-slate-900">Run Simulation</h2>
          <p className="mt-1 text-xs text-slate-500">
            Configure and execute a full multi-year simulation run.
          </p>
        </div>

        {/* Configuration summary */}
        <div className="border border-slate-200 bg-white p-3 space-y-2">
          <p className="text-xs font-semibold uppercase text-slate-500 mb-2">Run Configuration</p>

          <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
            <span className="text-slate-500">Population</span>
            <span className="font-medium text-slate-800 data-mono">
              {selectedPopulationId ?? <span className="text-amber-600">not selected</span>}
            </span>

            <span className="text-slate-500">Policy</span>
            <span className="font-medium text-slate-800 data-mono">
              {selectedPortfolioName ?? selectedTemplateName ?? (
                <span className="text-amber-600">not selected</span>
              )}
            </span>

            <span className="text-slate-500">Start year</span>
            <input
              type="number"
              value={startYear}
              min={2020}
              max={endYear - 1}
              onChange={(e) => setStartYear(Number(e.target.value))}
              className="w-24 border border-slate-200 px-1.5 py-0.5 text-xs font-mono"
              aria-label="Start year"
            />

            <span className="text-slate-500">End year</span>
            <input
              type="number"
              value={endYear}
              min={startYear + 1}
              max={2050}
              onChange={(e) => setEndYear(Number(e.target.value))}
              className="w-24 border border-slate-200 px-1.5 py-0.5 text-xs font-mono"
              aria-label="End year"
            />

            <span className="text-slate-500">Seed</span>
            <input
              type="number"
              value={seed ?? ""}
              placeholder="random"
              onChange={(e) => setSeed(e.target.value === "" ? null : Number(e.target.value))}
              className="w-24 border border-slate-200 px-1.5 py-0.5 text-xs font-mono"
              aria-label="Random seed"
            />
          </div>
        </div>

        <div className="flex gap-2">
          <Button onClick={() => void handleStartRun()} aria-label="Run simulation">
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
        <section className="border border-red-200 bg-red-50 p-3" aria-label="Simulation error">
          <div className="flex items-start gap-2">
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-500" />
            <div className="space-y-1">
              <p className="text-sm font-semibold text-red-900">{error.what}</p>
              <p className="text-xs text-red-700"><span className="font-medium">Why:</span> {error.why}</p>
              <p className="text-xs text-red-700"><span className="font-medium">Fix:</span> {error.fix}</p>
            </div>
          </div>
          <div className="mt-3">
            <Button variant="outline" onClick={() => { setSubView("configure"); setError(null); }}>
              Back to Configuration
            </Button>
          </div>
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
