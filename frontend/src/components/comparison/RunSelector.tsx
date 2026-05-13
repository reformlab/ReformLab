// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Run selector sub-component for ComparisonDashboardScreen.
 * Extracted from ComparisonDashboardScreen.tsx lines 135-239 — Story 18.5, AC-2.
 * Story 27.12, AC-4: Shows ≥12 chars of run-id with copy-to-clipboard button.
 */

import { Copy, Check } from "lucide-react";
import { useState, useCallback } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { CHART_COLORS } from "@/components/simulation/MultiRunChart";
import type { ResultListItem } from "@/api/types";
import { MAX_RUNS, runLabel, statusVariant } from "./comparison-helpers";
import { toast } from "sonner";
import { formatNumber } from "@/utils/formatters";

// ============================================================================
// RunIdDisplay sub-component with copy button (Story 27.12, AC-4)
// ============================================================================

interface RunIdDisplayProps {
  runId: string;
}

function RunIdDisplay({ runId }: RunIdDisplayProps) {
  const [copied, setCopied] = useState(false);

  // Show at least 12 characters of the run-id
  const displayId = runId.slice(0, 12);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(runId);
      setCopied(true);
      toast.success("Run ID copied");
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Failed to copy");
    }
  }, [runId]);

  return (
    <div className="flex items-center gap-1 shrink-0">
      <span
        className="font-mono text-xs text-slate-500 tabular-nums"
        title={runId} // Full ID available via tooltip
      >
        {displayId}
      </span>
      <span
        role="button"
        tabIndex={0}
        onClick={handleCopy}
        aria-label={`Copy full run ID: ${runId}`}
        className="text-slate-400 hover:text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 rounded p-0.5 cursor-pointer"
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            handleCopy();
          }
        }}
      >
        {copied ? (
          <Check className="h-3 w-3 text-emerald-500" />
        ) : (
          <Copy className="h-3 w-3" />
        )}
      </span>
    </div>
  );
}

export interface RunSelectorProps {
  results: ResultListItem[];
  selectedIds: string[];
  onToggle: (runId: string) => void;
  onCompare: () => void;
  loading: boolean;
}

export function RunSelector({
  results,
  selectedIds,
  onToggle,
  onCompare,
  loading,
}: RunSelectorProps) {
  const completed = results.filter((r) => r.status === "completed");

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-3" aria-label="Run selector">
      <div className="mb-2 flex items-center justify-between">
        <p className="text-xs font-semibold uppercase text-slate-500">
          Select Runs to Compare
        </p>
        <span className="text-xs text-slate-400">
          {selectedIds.length}/{MAX_RUNS} selected · Max {MAX_RUNS} runs
        </span>
      </div>

      {completed.length === 0 ? (
        <p className="text-xs text-slate-400">
          No completed runs available. Run simulations first.
        </p>
      ) : (
        <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200">
          {completed.map((item) => {
            const isSelected = selectedIds.includes(item.run_id);
            const isEvicted = !item.data_available;
            const isDisabled = loading || isEvicted || (!isSelected && selectedIds.length >= MAX_RUNS);
            const isBaseline = isSelected && selectedIds[0] === item.run_id;

            return (
              <li key={item.run_id} className="flex items-center gap-2 px-3 py-2">
                <Checkbox
                  checked={isSelected}
                  disabled={isDisabled}
                  onChange={() => !isDisabled && onToggle(item.run_id)}
                  aria-label={`Select run ${item.run_id.slice(0, 12)}`}
                  className="h-3.5 w-3.5"
                />
                {/* Run ID with copy button (Story 27.12, AC-4) */}
                <RunIdDisplay runId={item.run_id} />
                <span
                  className={`min-w-0 flex-1 truncate text-xs font-medium ${isDisabled ? "text-slate-400" : "text-slate-800"}`}
                >
                  {runLabel(item)}
                </span>
                <Badge variant="info" className="shrink-0 text-xs">
                  {item.start_year}–{item.end_year}
                </Badge>
                {item.row_count > 0 ? (
                  <span className="data-mono shrink-0 text-xs text-slate-500">
                    {formatNumber(item.row_count)}
                  </span>
                ) : null}
                <Badge variant={statusVariant(item.status)} className="shrink-0 text-xs">
                  {item.status}
                </Badge>
                {isEvicted ? (
                  <span className="shrink-0 text-xs text-slate-400">(evicted)</span>
                ) : null}
                {isBaseline ? (
                  <Badge variant="default" className="shrink-0 text-xs">
                    baseline
                  </Badge>
                ) : null}
                {isSelected && !isBaseline ? (
                  <span
                    className="shrink-0 text-xs font-medium"
                    style={{ color: CHART_COLORS[selectedIds.indexOf(item.run_id)] }}
                  >
                    ●
                  </span>
                ) : null}
              </li>
            );
          })}
        </ul>
      )}

      <div className="mt-3">
        <Button
          onClick={onCompare}
          disabled={selectedIds.length < 2 || loading}
          size="sm"
        >
          {loading ? "Loading..." : `Compare ${selectedIds.length} Runs`}
        </Button>
      </div>
    </section>
  );
}
