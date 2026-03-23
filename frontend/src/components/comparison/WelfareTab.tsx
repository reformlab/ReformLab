// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Welfare tab sub-component for ComparisonDashboardScreen.
 * Extracted from ComparisonDashboardScreen.tsx lines 337-459 — Story 18.5, AC-2.
 */

import { columnarToRows } from "@/components/simulation/MultiRunChart";
import type { ComparisonData } from "@/api/types";
import type { ViewMode } from "./comparison-helpers";

export function WelfareTab({
  data,
  portfolioLabels,
  viewMode,
}: {
  data: ComparisonData | undefined;
  portfolioLabels: string[];
  viewMode: ViewMode;
}) {
  if (!data) {
    return (
      <p className="text-xs text-slate-500">
        Welfare comparison requires behavioral response data or 3+ runs with
        welfare configuration.
      </p>
    );
  }

  const rows = columnarToRows(data.data);
  const valueCols =
    viewMode === "relative"
      ? data.columns.filter(
          (c) => c.startsWith("delta_") || c.startsWith("pct_delta_"),
        )
      : portfolioLabels.filter((l) => data.columns.includes(l));

  const metaCols = data.columns.filter(
    (c) =>
      !portfolioLabels.includes(c) &&
      !c.startsWith("delta_") &&
      !c.startsWith("pct_delta_"),
  );

  // Compute summary stats from delta columns
  const deltaCols = data.columns.filter((c) => c.startsWith("delta_") && !c.startsWith("pct_delta_"));
  let winners = 0;
  let losers = 0;
  let netChange = 0;
  if (deltaCols.length > 0) {
    const col = deltaCols[0]!;
    const vals = data.data[col];
    if (Array.isArray(vals)) {
      for (const v of vals) {
        if (typeof v === "number") {
          if (v > 0) winners++;
          else if (v < 0) losers++;
          netChange += v;
        }
      }
    }
  }
  const hasSummary = deltaCols.length > 0;

  return (
    <div className="space-y-3">
      {/* Summary cards */}
      {hasSummary ? (
        <div className="grid gap-2 sm:grid-cols-3">
          <div className="border border-emerald-200 bg-emerald-50 p-2">
            <p className="text-xs text-emerald-600">Winners</p>
            <p className="text-lg font-semibold text-emerald-700 data-mono">{winners}</p>
          </div>
          <div className="border border-red-200 bg-red-50 p-2">
            <p className="text-xs text-red-600">Losers</p>
            <p className="text-lg font-semibold text-red-700 data-mono">{losers}</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-white p-2">
            <p className="text-xs text-slate-500">Net Change</p>
            <p className={`text-lg font-semibold data-mono ${netChange >= 0 ? "text-emerald-700" : "text-red-700"}`}>
              {netChange >= 0 ? "+" : ""}{netChange.toLocaleString()}
            </p>
          </div>
        </div>
      ) : null}

      {/* Data table */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse border border-slate-200 text-xs">
          <thead>
            <tr className="bg-slate-50">
              {[...metaCols, ...valueCols].map((col) => (
                <th
                  key={col}
                  className="border border-slate-200 px-2 py-1 text-left font-medium"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, idx) => (
              <tr key={idx} className={idx % 2 === 0 ? "bg-white" : "bg-slate-50"}>
                {[...metaCols, ...valueCols].map((col) => {
                  const val = row[col];
                  const numVal = typeof val === "number" ? val : null;
                  const isNeg = viewMode === "relative" && numVal !== null && numVal < 0;
                  const isPos = viewMode === "relative" && numVal !== null && numVal > 0;
                  const cellClass = isNeg
                    ? "text-red-600"
                    : isPos
                      ? "text-emerald-600"
                      : "";
                  return (
                    <td
                      key={col}
                      className={`border border-slate-200 px-2 py-1 ${cellClass}`}
                    >
                      {typeof val === "number"
                        ? val.toLocaleString()
                        : String(val ?? "")}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
