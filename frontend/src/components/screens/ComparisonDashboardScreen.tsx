/** Comparison Dashboard Screen — Story 17.4, AC-1 through AC-6.
 *
 * Multi-portfolio side-by-side comparison with:
 * - Multi-run selection (2–5 runs, AC-1)
 * - Distributional / Fiscal / Welfare indicator tabs (AC-2)
 * - Indicator detail panel on click (AC-3)
 * - Absolute / Relative view toggle (AC-4)
 * - Cross-portfolio ranking metrics (AC-5)
 * - Behavioral response awareness via indicator data (AC-6)
 *
 * Sub-components extracted to frontend/src/components/comparison/ — Story 18.5, AC-2.
 */

import { useCallback, useState } from "react";

import { Download } from "lucide-react";
import { ErrorAlert, type ErrorState } from "@/components/simulation/ErrorAlert";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CrossMetricPanel } from "@/components/simulation/CrossMetricPanel";
import {
  MultiRunChart,
  columnarToRows,
} from "@/components/simulation/MultiRunChart";
import { comparePortfolios } from "@/api/indicators";
import type {
  PortfolioComparisonResponse,
  ResultListItem,
} from "@/api/types";
import { RunSelector } from "@/components/comparison/RunSelector";
import { FiscalTab } from "@/components/comparison/FiscalTab";
import { WelfareTab } from "@/components/comparison/WelfareTab";
import { DetailPanel } from "@/components/comparison/DetailPanel";
import {
  type ViewMode,
  type ActiveTab,
  type DetailTarget,
  buildSeries,
  exportComparisonCsv,
  METHODOLOGY_DESCRIPTIONS,
  MAX_RUNS,
} from "@/components/comparison/comparison-helpers";

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
  const distSeries = comparisonData
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
        <ErrorAlert what={error.what} why={error.why} fix={error.fix} />
      ) : null}

      {/* Loading */}
      {loading ? (
        <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-6">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-1/2" />
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
