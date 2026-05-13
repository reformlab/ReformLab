// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Persistent results listing panel — Story 17.3, AC-3.
 *
 * Displays all past simulation runs in reverse chronological order.
 * Clicking a run selects it; the delete button removes it from storage.
 * Story 27.12, AC-4: Shows ≥12 chars of run-id with copy-to-clipboard button.
 */

import { Copy, Trash2, Check } from "lucide-react";
import { useState, useCallback } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ResultListItem } from "@/api/types";
import { statusVariant } from "@/lib/status-variants";
import { formatTimestamp, formatNumber } from "@/utils/formatters";
import { policyLabel } from "@/utils/run-labels";
import { toast } from "sonner";

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
      toast.success("Run ID copied", { description: "Full run ID copied to clipboard" });
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Failed to copy run ID");
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

// ============================================================================
// ResultsListPanel
// ============================================================================

interface ResultsListPanelProps {
  results: ResultListItem[];
  selectedRunId: string | null;
  onSelect: (runId: string) => void;
  onDelete: (runId: string) => void;
}

export function ResultsListPanel({
  results,
  selectedRunId,
  onSelect,
  onDelete,
}: ResultsListPanelProps) {
  if (results.length === 0) {
    return (
      <section
        className="border border-slate-200 bg-white p-3"
        aria-label="Past simulation runs"
      >
        <p className="text-xs font-semibold uppercase text-slate-500 mb-2">Past Runs</p>
        <p className="text-xs text-slate-400">No simulation runs yet. Start a new run above.</p>
      </section>
    );
  }

  return (
    <section
      className="border border-slate-200 bg-white"
      aria-label="Past simulation runs"
    >
      <div className="border-b border-slate-100 px-3 py-2">
        <p className="text-xs font-semibold uppercase text-slate-500">
          Past Runs ({results.length})
        </p>
      </div>

      <ul className="divide-y divide-slate-100">
        {results.map((item) => {
          const isSelected = item.run_id === selectedRunId;
          return (
            <li
              key={item.run_id}
              className={`flex items-center gap-2 px-3 py-2 hover:bg-slate-50 ${
                isSelected ? "bg-blue-50 border-l-2 border-blue-500" : ""
              }`}
            >
              {/* Clickable area */}
              <button
                type="button"
                className="flex flex-1 items-center gap-3 min-w-0 text-left"
                onClick={() => onSelect(item.run_id)}
                aria-pressed={isSelected}
                aria-label={`Select run ${item.run_id.slice(0, 12)}`}
              >
                {/* Run ID with copy button (Story 27.12, AC-4) */}
                <RunIdDisplay runId={item.run_id} />

                {/* Policy label */}
                <span className="flex-1 min-w-0 truncate text-xs font-medium text-slate-800">
                  {policyLabel(item)}
                </span>

                {/* Year range */}
                <Badge variant="info" className="shrink-0 text-xs">
                  {item.start_year}–{item.end_year}
                </Badge>

                {/* Row count */}
                {item.row_count > 0 ? (
                  <span className="text-xs text-slate-500 shrink-0 data-mono">
                    {formatNumber(item.row_count)}
                  </span>
                ) : null}

                {/* Status badge */}
                <Badge variant={statusVariant(item.status)} className="shrink-0 text-xs">
                  {item.status}
                </Badge>

                {/* Cache indicator */}
                {!item.data_available && item.status === "completed" ? (
                  <span className="text-xs text-slate-400 shrink-0">(evicted)</span>
                ) : null}
              </button>

              {/* Timestamp */}
              <span className="text-xs text-slate-400 shrink-0 hidden xl:block">
                {formatTimestamp(item.timestamp)}
              </span>

              {/* Delete button */}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onDelete(item.run_id)}
                aria-label={`Delete run ${item.run_id.slice(0, 12)}`}
                className="h-6 w-6 p-0 shrink-0 text-slate-400 hover:text-red-500"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
