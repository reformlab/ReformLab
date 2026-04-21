// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Cross-stage validation gate for Stage 4 (Scenario).
 *
 * Renders all registered ValidationCheck results. Sync checks run on every
 * render (useMemo). The async memory preflight check runs only when the user
 * clicks "Run Simulation". Execution is blocked when any "error"-severity
 * check fails.
 *
 * Story 20.5 — AC-3, AC-4, AC-5.
 * Story 26.3 — AC-5, AC-6: Added stage navigation support.
 */

import { useMemo, useState } from "react";
import { CheckCircle2, XCircle, AlertTriangle, Loader2, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  VALIDATION_CHECKS,
  memoryPreflightCheck,
  type ValidationContext,
  type ValidationCheckResult,
} from "./validationChecks";
import type { StageKey } from "@/types/workspace";

// ============================================================================
// Types
// ============================================================================

interface ValidationGateProps {
  context: ValidationContext;
  onRun: () => void;
  runLoading: boolean;
  onStageNavigate?: (stage: StageKey) => void;  // Story 26.3
}

// Stage mapping for navigation — Story 26.3
const STAGE_KEY_MAP: Record<number, StageKey> = {
  1: "policies",
  2: "population",
  3: "investment-decisions",
  4: "scenario",
  5: "results",
};

// Parse stage references from messages and wrap in clickable links — Story 26.3
function parseStageLinks(message: string, onStageNavigate?: (stage: StageKey) => void): React.ReactNode {
  if (!onStageNavigate) return message;

  // Match "Stage 1", "Stage 2", etc. and wrap in clickable links
  const parts = message.split(/(Stage \d)/g);
  return parts.map((part, i) => {
    const match = part.match(/Stage (\d)/);
    if (match) {
      const stageNum = parseInt(match[1], 10);
      const stageKey = STAGE_KEY_MAP[stageNum];
      if (stageKey) {
        return (
          <button
            key={i}
            className="text-blue-600 underline hover:text-blue-700"
            onClick={() => onStageNavigate(stageKey)}
          >
            {part}
          </button>
        );
      }
    }
    return part;
  });
}

// ============================================================================
// Component
// ============================================================================

export function ValidationGate({ context, onRun, runLoading, onStageNavigate }: ValidationGateProps) {
  const [memoryCheckResult, setMemoryCheckResult] = useState<ValidationCheckResult | null>(null);
  const [memoryLoading, setMemoryLoading] = useState(false);

  // Sync checks (all except memoryPreflightCheck) — re-evaluated on every context change
  const syncChecks = useMemo(
    () => VALIDATION_CHECKS.filter((c) => c.id !== "memory-preflight"),
    [],
  );

  const syncResults = useMemo(
    () => syncChecks.map((check) => {
      const result = check.fn(context);
      // fn is sync for all non-memory checks — cast away Promise
      return result as ValidationCheckResult;
    }),
    [syncChecks, context],
  );

  // Combined results for display (include memory result if available)
  const allResults = useMemo(() => {
    const results: Array<{ id: string; label: string; result: ValidationCheckResult }> = syncChecks.map(
      (check, i) => ({ id: check.id, label: check.label, result: syncResults[i]! }),
    );
    // Append memory check row
    results.push({
      id: "memory-preflight",
      label: "Memory preflight",
      result: memoryCheckResult ?? { passed: true, message: "", severity: "error" },
    });
    return results;
  }, [syncChecks, syncResults, memoryCheckResult]);

  const syncHasErrors = syncResults.some((r, i) => syncChecks[i]!.severity === "error" && !r.passed);

  const handleRun = async () => {
    if (syncHasErrors) return;
    setMemoryLoading(true);
    try {
      const result = await memoryPreflightCheck.fn(context) as ValidationCheckResult;
      setMemoryCheckResult(result);
      if (result.severity === "error" && !result.passed) {
        return; // Block run
      }
    } finally {
      setMemoryLoading(false);
    }
    onRun();
  };

  const memoryFailed = memoryCheckResult !== null && !memoryCheckResult.passed && memoryCheckResult.severity === "error";
  const isDisabled = syncHasErrors || runLoading || memoryLoading || memoryFailed;

  const failingCheckLabels = [
    ...syncChecks
      .filter((c, i) => c.severity === "error" && !syncResults[i]!.passed)
      .map((c) => c.label),
    ...(memoryCheckResult && !memoryCheckResult.passed && memoryCheckResult.severity === "error"
      ? ["Memory preflight"]
      : []),
  ];

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-3">
      <h3 className="text-sm font-semibold text-slate-900">Validation</h3>

      {/* Check list */}
      <ul className="space-y-2">
        {allResults.map(({ id, label, result }) => {
          const isMemory = id === "memory-preflight";
          const isPending = isMemory && memoryCheckResult === null;
          const isLoading = isMemory && memoryLoading;

          return (
            <li key={id} className="flex items-start gap-2 text-sm">
              {/* Status icon */}
              <span className="mt-0.5 flex-shrink-0">
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin text-slate-400" />
                ) : isPending ? (
                  <span className="h-4 w-4 rounded-full border border-slate-300 inline-block" />
                ) : result.passed ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                ) : result.severity === "error" ? (
                  <XCircle className="h-4 w-4 text-red-500" />
                ) : (
                  <AlertTriangle className="h-4 w-4 text-amber-500" />
                )}
              </span>
              {/* Label + message */}
              <div className="flex-1">
                <span className={result.passed || isPending ? "text-slate-700" : result.severity === "error" ? "text-red-700" : "text-amber-700"}>
                  {label}
                </span>
                {!result.passed && !isPending && result.message && (
                  <p className={`text-xs mt-0.5 ${result.severity === "error" ? "text-red-600" : "text-amber-600"}`}>
                    {parseStageLinks(result.message, onStageNavigate)}
                  </p>
                )}
                {isPending && (
                  <p className="text-xs mt-0.5 text-slate-400">
                    Runs when you click Run Simulation
                  </p>
                )}
              </div>
            </li>
          );
        })}
      </ul>

      {/* Run button */}
      <div className="pt-2 space-y-1">
        <Button
          className="w-full"
          disabled={isDisabled}
          title={isDisabled && !memoryLoading && failingCheckLabels.length > 0 ? `Resolve: ${failingCheckLabels.join(", ")}` : undefined}
          onClick={handleRun}
        >
          {memoryLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Checking memory…
            </>
          ) : (
            <>
              <Play className="mr-2 h-4 w-4" />
              Run Simulation
            </>
          )}
        </Button>
        {isDisabled && !memoryLoading && failingCheckLabels.length > 0 && (
          <p className="text-xs text-slate-500">Resolve: {failingCheckLabels.join(", ")}</p>
        )}
      </div>
    </div>
  );
}
