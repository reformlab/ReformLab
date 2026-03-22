/** Fiscal tab sub-component for ComparisonDashboardScreen.
 * Extracted from ComparisonDashboardScreen.tsx lines 244-332 — Story 18.5, AC-2.
 */

import { columnarToRows } from "@/components/simulation/MultiRunChart";
import type { ComparisonData } from "@/api/types";
import type { ViewMode } from "./comparison-helpers";

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
                {col}
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
  );
}
