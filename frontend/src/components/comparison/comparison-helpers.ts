/** Shared types, constants, and helpers for ComparisonDashboardScreen sub-components.
 * Extracted from ComparisonDashboardScreen.tsx — Story 18.5, AC-2.
 */

import type { ResultListItem, PortfolioComparisonResponse } from "@/api/types";
import { CHART_COLORS } from "@/components/simulation/MultiRunChart";
import type { SeriesSpec } from "@/components/simulation/MultiRunChart";

// ============================================================================
// Types
// ============================================================================

export type ViewMode = "absolute" | "relative";
export type ActiveTab = "distributional" | "fiscal" | "welfare";

export interface DetailTarget {
  indicator: string;
  label: string;
  values: Record<string, unknown>;
  methodology: string;
}

// ============================================================================
// Constants
// ============================================================================

export const MAX_RUNS = 5;

export const METHODOLOGY_DESCRIPTIONS: Record<string, string> = {
  distributional:
    "Mean disposable income per decile after applying the policy reform. Households are sorted by pre-reform income and grouped into 10 equal-sized deciles.",
  fiscal:
    "Annual fiscal revenue/cost/balance aggregated across all households. Revenue: taxes collected. Cost: transfers paid. Balance: revenue minus cost.",
  welfare:
    "Winner/loser household counts and net welfare change. A household is a winner if disposable income increases post-reform.",
};

// ============================================================================
// Helpers
// ============================================================================

export function runLabel(item: ResultListItem): string {
  if (item.portfolio_name) return item.portfolio_name;
  if (item.template_name) return item.template_name;
  return item.run_id.slice(0, 8);
}

export function statusVariant(
  status: string,
): "success" | "destructive" | "warning" | "default" {
  if (status === "completed") return "success";
  if (status === "failed") return "destructive";
  return "warning";
}

/** Build series specs for a given ordered list of portfolio labels. */
export function buildSeries(labels: string[]): SeriesSpec[] {
  return labels.map((label, i) => ({
    key: label,
    label,
    color: CHART_COLORS[i] ?? CHART_COLORS[0],
  }));
}

/** Escape a CSV field: quote if it contains commas/quotes/newlines; prefix formula characters. */
export function escapeCsvField(val: unknown): string {
  let s = String(val ?? "");
  // Prefix formula-injection characters to prevent spreadsheet formula execution
  if (s.length > 0 && "=+-@".includes(s[0])) {
    s = `'${s}`;
  }
  // Wrap in double-quotes if the value contains commas, quotes, or newlines
  if (s.includes(",") || s.includes('"') || s.includes("\n") || s.includes("\r")) {
    s = `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

/** Export comparison data as CSV client-side. */
export function exportComparisonCsv(
  response: PortfolioComparisonResponse,
  indicatorType: string,
) {
  const compData = response.comparisons[indicatorType];
  if (!compData) return;

  const { columns, data } = compData;
  const rowCount = data[columns[0]]?.length ?? 0;

  const rows: string[] = [columns.map(escapeCsvField).join(",")];
  for (let i = 0; i < rowCount; i++) {
    const row = columns.map((col) => escapeCsvField(data[col]?.[i]));
    rows.push(row.join(","));
  }

  const csv = rows.join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `comparison_${indicatorType}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
