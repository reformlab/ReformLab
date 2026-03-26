// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * PopulationSummaryView — dataset-level overview tab.
 *
 * Shows row/column counts, type breakdown, and completeness table.
 * Summary View tab within the Full Data Explorer.
 *
 * Story 20.4 — AC-3(c).
 */

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { PopulationSummaryData } from "@/api/types";

// ============================================================================
// Types
// ============================================================================

export interface PopulationSummaryViewProps {
  summary: PopulationSummaryData;
}

// ============================================================================
// Type breakdown counts
// ============================================================================

function typeCount(summary: PopulationSummaryData, type: string): number {
  return summary.columns.filter((c) => c.type === type).length;
}

// ============================================================================
// Main component
// ============================================================================

export function PopulationSummaryView({ summary }: PopulationSummaryViewProps) {
  const numericCount = typeCount(summary, "numeric");
  const categoricalCount = typeCount(summary, "categorical");
  const booleanCount = typeCount(summary, "boolean");
  const stringCount = typeCount(summary, "string");

  return (
    <div className="flex flex-col gap-6 p-4">
      {/* Overview cards */}
      <div>
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Dataset Overview
        </h3>
        <div className="grid grid-cols-3 gap-3">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-center">
            <p className="text-2xl font-bold text-slate-900">
              {summary.record_count.toLocaleString()}
            </p>
            <p className="text-xs text-slate-500">rows</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-center">
            <p className="text-2xl font-bold text-slate-900">{summary.column_count}</p>
            <p className="text-xs text-slate-500">columns</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-center">
            <p className="text-2xl font-bold text-slate-900">
              {summary.estimated_memory_mb.toFixed(1)}
            </p>
            <p className="text-xs text-slate-500">MB (estimated)</p>
          </div>
        </div>
      </div>

      {/* Column type breakdown */}
      <div>
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Column Types
        </h3>
        <div className="flex flex-wrap gap-2">
          {numericCount > 0 && (
            <Badge variant="secondary">{numericCount} numeric</Badge>
          )}
          {categoricalCount > 0 && (
            <Badge variant="outline">{categoricalCount} categorical</Badge>
          )}
          {booleanCount > 0 && (
            <Badge variant="default">{booleanCount} boolean</Badge>
          )}
          {stringCount > 0 && (
            <Badge variant="secondary">{stringCount} string</Badge>
          )}
        </div>
      </div>

      {/* Completeness table */}
      <div>
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Completeness
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50">
                <th className="px-3 py-2 text-left font-semibold text-slate-700">Column</th>
                <th className="px-3 py-2 text-left font-semibold text-slate-700">Type</th>
                <th className="px-3 py-2 text-right font-semibold text-slate-700">
                  Null %
                </th>
                <th className="px-3 py-2 text-right font-semibold text-slate-700">
                  Cardinality
                </th>
              </tr>
            </thead>
            <tbody>
              {summary.columns.map((col) => (
                <tr
                  key={col.name}
                  className={cn(
                    "border-b border-slate-100",
                    col.null_pct > 50 && "bg-red-50",
                    col.null_pct > 10 && col.null_pct <= 50 && "bg-amber-50",
                  )}
                >
                  <td className="px-3 py-1.5 font-medium text-slate-800">{col.name}</td>
                  <td className="px-3 py-1.5">
                    <Badge variant="secondary" className="text-[10px]">
                      {col.type}
                    </Badge>
                  </td>
                  <td
                    className={cn(
                      "px-3 py-1.5 text-right font-mono",
                      col.null_pct > 50 && "font-semibold text-red-700",
                      col.null_pct > 10 && col.null_pct <= 50 && "font-semibold text-amber-700",
                      col.null_pct === 0 && "text-slate-400",
                    )}
                  >
                    {col.null_pct.toFixed(1)}%
                  </td>
                  <td className="px-3 py-1.5 text-right font-mono text-slate-500">
                    {col.cardinality !== null ? col.cardinality.toLocaleString() : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
