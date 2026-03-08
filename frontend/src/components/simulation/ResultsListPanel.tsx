/** Persistent results listing panel — Story 17.3, AC-3.
 *
 * Displays all past simulation runs in reverse chronological order.
 * Clicking a run selects it; the delete button removes it from storage.
 */

import { Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ResultListItem } from "@/api/types";

// ============================================================================
// Helpers
// ============================================================================

function statusVariant(status: string): "success" | "destructive" | "warning" | "default" {
  if (status === "completed") return "success";
  if (status === "failed") return "destructive";
  return "warning";
}

function formatTimestamp(ts: string): string {
  try {
    const d = new Date(ts);
    return d.toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return ts;
  }
}

function policyLabel(item: ResultListItem): string {
  if (item.portfolio_name) return item.portfolio_name;
  if (item.template_name) return item.template_name;
  return item.run_kind === "portfolio" ? "Portfolio" : "Scenario";
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
                aria-label={`Select run ${item.run_id.slice(0, 8)}`}
              >
                {/* Run ID */}
                <span className="data-mono text-xs text-slate-500 shrink-0 w-16">
                  {item.run_id.slice(0, 8)}
                </span>

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
                    {item.row_count.toLocaleString()}
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
                aria-label={`Delete run ${item.run_id.slice(0, 8)}`}
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
