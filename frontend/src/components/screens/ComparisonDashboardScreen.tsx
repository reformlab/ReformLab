/** Comparison Dashboard Screen — Story 17.4, AC-1 through AC-6.
 *
 * Multi-portfolio side-by-side comparison with:
 * - Multi-run selection (2–5 runs, AC-1)
 * - Distributional / Fiscal / Welfare indicator tabs (AC-2)
 * - Indicator detail panel on click (AC-3)
 * - Absolute / Relative view toggle (AC-4)
 * - Cross-portfolio ranking metrics (AC-5)
 * - Behavioral response awareness via indicator data (AC-6)
 */

import { useCallback, useEffect, useRef, useState } from "react";

import { AlertCircle, Download, X } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CrossMetricPanel } from "@/components/simulation/CrossMetricPanel";
import {
  MultiRunChart,
  columnarToRows,
  CHART_COLORS,
  type SeriesSpec,
} from "@/components/simulation/MultiRunChart";
import { comparePortfolios } from "@/api/indicators";
import type {
  ComparisonData,
  PortfolioComparisonResponse,
  ResultListItem,
} from "@/api/types";

// ============================================================================
// Types
// ============================================================================

type ViewMode = "absolute" | "relative";
type ActiveTab = "distributional" | "fiscal" | "welfare";

interface ErrorState {
  what: string;
  why: string;
  fix: string;
}

interface DetailTarget {
  indicator: string;
  label: string;
  values: Record<string, unknown>;
  methodology: string;
}

// ============================================================================
// Constants
// ============================================================================

const MAX_RUNS = 5;

const METHODOLOGY_DESCRIPTIONS: Record<string, string> = {
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

function runLabel(item: ResultListItem): string {
  if (item.portfolio_name) return item.portfolio_name;
  if (item.template_name) return item.template_name;
  return item.run_id.slice(0, 8);
}

function statusVariant(
  status: string,
): "success" | "destructive" | "warning" | "default" {
  if (status === "completed") return "success";
  if (status === "failed") return "destructive";
  return "warning";
}

/** Build series specs for a given ordered list of portfolio labels. */
function buildSeries(labels: string[]): SeriesSpec[] {
  return labels.map((label, i) => ({
    key: label,
    label,
    color: CHART_COLORS[i] ?? CHART_COLORS[0],
  }));
}

/** Escape a CSV field: quote if it contains commas/quotes/newlines; prefix formula characters. */
function escapeCsvField(val: unknown): string {
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
function exportComparisonCsv(
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

// ============================================================================
// Sub-components
// ============================================================================

interface RunSelectorProps {
  results: ResultListItem[];
  selectedIds: string[];
  onToggle: (runId: string) => void;
  onCompare: () => void;
  loading: boolean;
}

function RunSelector({
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
        <ul className="divide-y divide-slate-100 border border-slate-200">
          {completed.map((item) => {
            const isSelected = selectedIds.includes(item.run_id);
            const isEvicted = !item.data_available;
            const isDisabled = isEvicted || (!isSelected && selectedIds.length >= MAX_RUNS);
            const isBaseline = isSelected && selectedIds[0] === item.run_id;

            return (
              <li key={item.run_id} className="flex items-center gap-2 px-3 py-2">
                <input
                  type="checkbox"
                  checked={isSelected}
                  disabled={isDisabled}
                  onChange={() => !isDisabled && onToggle(item.run_id)}
                  aria-label={`Select run ${item.run_id.slice(0, 8)}`}
                  className="h-3.5 w-3.5 cursor-pointer"
                />
                <span
                  className={`data-mono w-16 shrink-0 text-xs ${isDisabled ? "text-slate-400" : "text-slate-500"}`}
                >
                  {item.run_id.slice(0, 8)}
                </span>
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
                    {item.row_count.toLocaleString()}
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

// ============================================================================
// Fiscal tab (table-only)
// ============================================================================

function FiscalTab({
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

// ============================================================================
// Welfare tab
// ============================================================================

function WelfareTab({
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

// ============================================================================
// Detail panel (AC-3)
// ============================================================================

function DetailPanel({
  target,
  onDismiss,
}: {
  target: DetailTarget;
  onDismiss: () => void;
}) {
  const panelRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onDismiss();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onDismiss]);

  return (
    <aside
      ref={panelRef}
      className="rounded-lg border border-slate-200 bg-slate-50 p-3"
      aria-label="Indicator detail panel"
    >
      <div className="mb-2 flex items-center justify-between">
        <p className="text-sm font-semibold text-slate-800">{target.label}</p>
        <button
          type="button"
          onClick={onDismiss}
          aria-label="Close detail panel"
          className="text-slate-400 hover:text-slate-700"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <p className="mb-3 text-xs text-slate-500">{target.methodology}</p>
      <div className="space-y-1">
        {Object.entries(target.values).map(([k, v]) => {
          if (k === "decile" || k === "year" || k === "field_name" || k === "metric") return null;
          const numVal = typeof v === "number" ? v : null;
          const isDelta = k.startsWith("delta_") || k.startsWith("pct_delta_");
          const isNeg = isDelta && numVal !== null && numVal < 0;
          const isPos = isDelta && numVal !== null && numVal > 0;
          const valueClass = isNeg
            ? "text-red-600 font-medium"
            : isPos
              ? "text-emerald-600 font-medium"
              : "text-slate-800";
          return (
            <div key={k} className="flex justify-between text-xs">
              <span className="text-slate-500">{k}</span>
              <span className={valueClass}>
                {typeof v === "number" ? v.toLocaleString() : String(v ?? "")}
              </span>
            </div>
          );
        })}
      </div>
    </aside>
  );
}

// ============================================================================
// ComparisonDashboardScreen
// ============================================================================

interface ComparisonDashboardScreenProps {
  results: ResultListItem[];
  onBack: () => void;
}

export function ComparisonDashboardScreen({
  results,
  onBack,
}: ComparisonDashboardScreenProps) {
  const [selectedRunIds, setSelectedRunIds] = useState<string[]>([]);
  const [comparisonData, setComparisonData] =
    useState<PortfolioComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ErrorState | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("absolute");
  const [activeTab, setActiveTab] = useState<ActiveTab>("distributional");
  const [detailTarget, setDetailTarget] = useState<DetailTarget | null>(null);

  const toggleRun = useCallback((runId: string) => {
    setSelectedRunIds((prev) => {
      if (prev.includes(runId)) return prev.filter((id) => id !== runId);
      if (prev.length >= MAX_RUNS) return prev;
      return [...prev, runId];
    });
  }, []);

  const handleCompare = useCallback(async () => {
    if (selectedRunIds.length < 2) return;
    setLoading(true);
    setError(null);
    setComparisonData(null);

    try {
      const response = await comparePortfolios({
        run_ids: selectedRunIds,
        baseline_run_id: selectedRunIds[0],
        include_welfare: true,
        include_deltas: true,
        include_pct_deltas: true,
      });
      setComparisonData(response);
    } catch (err: unknown) {
      if (
        err !== null &&
        typeof err === "object" &&
        "what" in err &&
        "why" in err &&
        "fix" in err
      ) {
        setError(err as ErrorState);
      } else {
        setError({
          what: "Comparison failed",
          why: err instanceof Error ? err.message : "Unknown error",
          fix: "Check server logs or re-run the simulations",
        });
      }
    } finally {
      setLoading(false);
    }
  }, [selectedRunIds]);

  const handleDetailClick = useCallback(
    (indicatorType: string, row: Record<string, unknown>) => {
      const methodology =
        METHODOLOGY_DESCRIPTIONS[indicatorType] ?? indicatorType;
      const label =
        indicatorType.charAt(0).toUpperCase() + indicatorType.slice(1);
      setDetailTarget((prev) => {
        // Toggle if same row clicked again
        if (
          prev?.indicator === indicatorType &&
          JSON.stringify(prev.values) === JSON.stringify(row)
        ) {
          return null;
        }
        return { indicator: indicatorType, label, values: row, methodology };
      });
    },
    [],
  );

  const handleExport = useCallback(() => {
    if (!comparisonData) return;
    exportComparisonCsv(comparisonData, activeTab);
  }, [comparisonData, activeTab]);

  // Build series for distributional tab
  const distSeries: SeriesSpec[] = comparisonData
    ? buildSeries(comparisonData.portfolio_labels)
    : [];

  const distData = comparisonData?.comparisons.distributional;
  const distRows = distData ? columnarToRows(distData.data) : [];
  const fiscalData = comparisonData?.comparisons.fiscal;
  const welfareData = comparisonData?.comparisons.welfare;

  return (
    <section className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white p-3">
        <div>
          <h2 className="text-base font-semibold text-slate-900">
            Comparison Dashboard
          </h2>
          <p className="text-xs text-slate-500">
            Compare up to {MAX_RUNS} simulation runs side-by-side
          </p>
        </div>
        <div className="flex items-center gap-2">
          {comparisonData ? (
            <Button variant="outline" size="sm" onClick={handleExport}>
              <Download className="mr-1 h-3.5 w-3.5" />
              Export CSV
            </Button>
          ) : null}
          <Button variant="outline" size="sm" onClick={onBack}>
            Back
          </Button>
        </div>
      </div>

      {/* Run Selector */}
      <RunSelector
        results={results}
        selectedIds={selectedRunIds}
        onToggle={toggleRun}
        onCompare={() => void handleCompare()}
        loading={loading}
      />

      {/* Error display */}
      {error ? (
        <div
          className="flex items-start gap-2 border border-red-200 bg-red-50 p-3"
          role="alert"
        >
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-600" />
          <div className="space-y-0.5 text-xs">
            <p className="font-semibold text-red-800">{error.what}</p>
            <p className="text-red-700">{error.why}</p>
            <p className="text-red-600">{error.fix}</p>
          </div>
        </div>
      ) : null}

      {/* Loading */}
      {loading ? (
        <div className="rounded-lg border border-slate-200 bg-white p-6 text-center">
          <p className="text-sm text-slate-500">Loading comparison data…</p>
        </div>
      ) : null}

      {/* Comparison results */}
      {comparisonData && !loading ? (
        <div className="space-y-3">
          {/* AC-5: Cross-metric summary */}
          {comparisonData.cross_metrics.length > 0 ? (
            <div className="rounded-lg border border-slate-200 bg-white p-3">
              <CrossMetricPanel metrics={comparisonData.cross_metrics} />
            </div>
          ) : null}

          {/* Toolbar: absolute/relative toggle */}
          <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-3 py-2">
            <p className="text-xs text-slate-500">
              Comparing {comparisonData.portfolio_labels.length} runs ·{" "}
              {comparisonData.warnings.length > 0
                ? `${comparisonData.warnings.length} warning(s)`
                : "No warnings"}
            </p>
            {/* AC-4: Absolute/relative toggle */}
            <div className="flex overflow-hidden border border-slate-200">
              <Button
                variant={viewMode === "absolute" ? "default" : "ghost"}
                size="sm"
                className="rounded-none border-none text-xs"
                onClick={() => setViewMode("absolute")}
                aria-pressed={viewMode === "absolute"}
              >
                Absolute
              </Button>
              <Button
                variant={viewMode === "relative" ? "default" : "ghost"}
                size="sm"
                className="rounded-none border-none text-xs"
                onClick={() => setViewMode("relative")}
                aria-pressed={viewMode === "relative"}>
                Relative
              </Button>
            </div>
          </div>

          {/* Detail panel (AC-3) */}
          {detailTarget ? (
            <DetailPanel
              target={detailTarget}
              onDismiss={() => setDetailTarget(null)}
            />
          ) : null}

          {/* Indicator tabs (AC-2) */}
          <Tabs
            value={activeTab}
            onValueChange={(v) => setActiveTab(v as ActiveTab)}
          >
            <div className="rounded-lg border border-slate-200 bg-white">
              <TabsList className="w-full justify-start border-b border-slate-200 bg-white">
                <TabsTrigger value="distributional">Distributional</TabsTrigger>
                <TabsTrigger value="fiscal">Fiscal</TabsTrigger>
                <TabsTrigger value="welfare">Welfare</TabsTrigger>
              </TabsList>

              <div className="p-3">
                <TabsContent value="distributional">
                  {distData ? (
                    <MultiRunChart
                      data={distRows}
                      xKey="decile"
                      series={distSeries}
                      mode={viewMode}
                      title="Income Decile Impact"
                      showTable
                      onBarClick={(row) =>
                        handleDetailClick("distributional", row)
                      }
                    />
                  ) : (
                    <p className="text-xs text-slate-400">
                      No distributional data available.
                    </p>
                  )}
                </TabsContent>

                <TabsContent value="fiscal">
                  <FiscalTab
                    data={fiscalData}
                    portfolioLabels={comparisonData.portfolio_labels}
                    viewMode={viewMode}
                    onDetailClick={(_label, row) =>
                      handleDetailClick("fiscal", row)
                    }
                  />
                </TabsContent>

                <TabsContent value="welfare">
                  <WelfareTab
                    data={welfareData}
                    portfolioLabels={comparisonData.portfolio_labels}
                    viewMode={viewMode}
                  />
                </TabsContent>
              </div>
            </div>
          </Tabs>
        </div>
      ) : null}

      {/* Idle state: no comparison run yet */}
      {!comparisonData && !loading && !error ? (
        <div className="rounded-lg border border-slate-200 bg-white p-6 text-center">
          <p className="text-sm text-slate-500">
            Select 2–5 completed runs above and click Compare to see
            side-by-side indicator analysis.
          </p>
        </div>
      ) : null}
    </section>
  );
}
