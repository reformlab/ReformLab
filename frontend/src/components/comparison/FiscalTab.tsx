// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Fiscal tab sub-component for ComparisonDashboardScreen.
 * Extracted from ComparisonDashboardScreen.tsx lines 244-332 — Story 18.5, AC-2.
 * Story 27.12, AC-3: Added unit labels to column headers and formatLargeNumber for values.
 */

import { columnarToRows } from "@/components/simulation/MultiRunChart";
import type { ComparisonData } from "@/api/types";
import type { ViewMode } from "./comparison-helpers";
import { formatLargeNumber } from "@/utils/formatters";

export function FiscalTab({
  data,
  portfolioLabels,
  viewMode,
  onDetailClick,
}: {
  data: ComparisonData | undefined;
  portfolioLabels: string[];
  viewMode: ViewMode;
  onDetailClick: (label: string, row: Record<string, unknown>) => void;
}) {
  if (!data) {
    return (
      <p className="text-xs text-slate-400">No fiscal comparison data available.</p>
    );
  }

  const rows = columnarToRows(data.data);

  // Determine which columns to show
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

  const displayCols = [...metaCols, ...valueCols];

  // Story 27.12, AC-3: Map column names to unit labels
  // Non-monetary meta columns that should NOT get (€) suffix
  const NON_MONETARY_META = new Set(["year", "metric", "category", "decile", "name", "type", "label"]);

  const getColumnLabel = (col: string): string => {
    // Meta columns typically describe the metric type (e.g., "revenue", "cost", "balance")
    if (metaCols.includes(col)) {
      return NON_MONETARY_META.has(col) ? col : `${col} (€)`;
    }
    // Portfolio value columns
    if (viewMode === "absolute") {
      return `${col} (€)`;
    }
    // Delta columns
    if (col.startsWith("delta_")) {
      return `${col.replace("delta_", "")} (€)`;
    }
    // Percentage delta columns
    if (col.startsWith("pct_delta_")) {
      return `${col.replace("pct_delta_", "")} (%)`;
    }
    return col;
  };

  // Story 27.12, AC-3: Format value for display
  const formatValue = (val: unknown, col: string): string => {
    if (typeof val !== "number") return String(val ?? "");
    if (!Number.isFinite(val)) return "—"; // AC-5: NaN/Infinity guard

    // Use formatLargeNumber for absolute monetary values
    if (viewMode === "absolute" || col.startsWith("delta_")) {
      return formatLargeNumber(val);
    }
    // Percentage deltas - keep as formatted percentage
    if (col.startsWith("pct_delta_")) {
      return `${val.toFixed(1)}%`;
    }
    return formatLargeNumber(val);
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse border border-slate-200 text-xs">
        <thead>
          <tr className="bg-slate-50">
            {displayCols.map((col) => (
              <th
                key={col}
                className="border border-slate-200 px-2 py-1 text-left font-medium"
              >
                {getColumnLabel(col)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr
              key={idx}
              className={`cursor-pointer hover:bg-slate-50 ${idx % 2 === 0 ? "bg-white" : "bg-slate-50"}`}
              onClick={() =>
                onDetailClick("fiscal", row)
              }
            >
              {displayCols.map((col) => {
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
                    {formatValue(val, col)}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
