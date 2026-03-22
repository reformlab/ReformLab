/** Results overview screen — Story 18.4, AC-1 through AC-5.
 *
 * Extracted from inline App.tsx results JSX (lines 360-381) into a dedicated
 * screen component following the ComparisonDashboardScreen pattern.
 *
 * Layout:
 *   - Metadata header: run_id (8 chars), policy label, year range badge, status badge, action buttons
 *   - Tabbed content: Overview | Data & Export | Detail
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { Download } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DistributionalChart } from "@/components/simulation/DistributionalChart";
import { SummaryStatCard } from "@/components/simulation/SummaryStatCard";
import { ResultDetailView } from "@/components/simulation/ResultDetailView";
import type { DecileData, SummaryStatistic } from "@/data/mock-data";
import type { ResultDetailResponse, RunResponse } from "@/api/types";
import { getResult } from "@/api/results";

// ============================================================================
// Types
// ============================================================================

type TabValue = "overview" | "export" | "detail";

export interface ResultsOverviewScreenProps {
  decileData: DecileData[];
  runResult: RunResponse | null;
  reformLabel: string;
  onCompare: () => void;
  onViewDecisions: () => void;
  onRunAgain: () => void;
  onExportCsv: () => void;
  onExportParquet: () => void;
}

// ============================================================================
// Summary stats computation
// ============================================================================

function placeholderStats(): SummaryStatistic[] {
  return [
    { id: "mean-impact", label: "Mean impact", value: "—", trend: "neutral", trendValue: "—" },
    { id: "most-benefit", label: "Most benefit", value: "—", trend: "neutral", trendValue: "—" },
    { id: "most-cost", label: "Most cost", value: "—", trend: "neutral", trendValue: "—" },
  ];
}

function computeSummaryStats(data: DecileData[]): SummaryStatistic[] {
  if (data.length === 0) return placeholderStats();

  const deltas = data.map((d) => d.delta);
  const allZero = deltas.every((d) => d === 0);
  if (allZero) return placeholderStats();

  const meanDelta = deltas.reduce((a, b) => a + b, 0) / deltas.length;
  const roundedMean = Math.round(meanDelta);
  const maxPos = data.reduce((best, d) => (d.delta > best.delta ? d : best), data[0]);
  const maxNeg = data.reduce((best, d) => (d.delta < best.delta ? d : best), data[0]);

  return [
    {
      id: "mean-impact",
      label: "Mean impact",
      value: `€${roundedMean.toLocaleString()}/yr`,
      trend: meanDelta > 0 ? "up" : meanDelta < 0 ? "down" : "neutral",
      trendValue: roundedMean === 0 ? "0" : `${roundedMean > 0 ? "+" : ""}${roundedMean.toLocaleString()}`,
    },
    {
      id: "most-benefit",
      label: "Most benefit",
      value: maxPos.decile,
      trend: maxPos.delta > 0 ? "up" : "neutral",
      trendValue: `€${Math.round(maxPos.delta).toLocaleString()}/yr`,
    },
    {
      id: "most-cost",
      label: "Most cost",
      value: maxNeg.decile,
      trend: maxNeg.delta < 0 ? "down" : "neutral",
      trendValue: `€${Math.round(maxNeg.delta).toLocaleString()}/yr`,
    },
  ];
}

// ============================================================================
// Component
// ============================================================================

export function ResultsOverviewScreen({
  decileData,
  runResult,
  reformLabel,
  onCompare,
  onViewDecisions,
  onRunAgain,
  onExportCsv,
  onExportParquet,
}: ResultsOverviewScreenProps) {
  const [activeTab, setActiveTab] = useState<TabValue>("overview");
  const [resultDetail, setResultDetail] = useState<ResultDetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState(false);
  // Tracks the most recent run_id to discard stale in-flight responses after a run switch.
  const activeRunIdRef = useRef<string | null>(null);

  // Reset cached detail when the active run changes; update ref so async callbacks
  // can guard against committing results for a superseded run.
  useEffect(() => {
    activeRunIdRef.current = runResult?.run_id ?? null;
    setResultDetail(null);
    setDetailError(false);
  }, [runResult?.run_id]);

  const loadDetail = useCallback(async () => {
    if (!runResult?.run_id || resultDetail !== null || detailLoading) return;
    const capturedRunId = runResult.run_id;
    setDetailLoading(true);
    setDetailError(false);
    try {
      const detail = await getResult(capturedRunId);
      // Guard: discard if the user switched to a different run while this was in-flight.
      if (activeRunIdRef.current === capturedRunId) {
        setResultDetail(detail);
      }
    } catch {
      if (activeRunIdRef.current === capturedRunId) {
        setDetailError(true);
      }
    } finally {
      if (activeRunIdRef.current === capturedRunId) {
        setDetailLoading(false);
      }
    }
  }, [runResult, resultDetail, detailLoading]);

  const handleTabChange = (value: string) => {
    const tab = value as TabValue;
    setActiveTab(tab);
    if (tab === "detail") {
      void loadDetail();
    }
  };

  const summaryStats = computeSummaryStats(decileData);
  const isPlaceholder = decileData.length === 0 || decileData.every((d) => d.delta === 0);

  // Year range badge label
  const yearRange =
    runResult && runResult.years.length > 0
      ? `${runResult.years[0]}–${runResult.years[runResult.years.length - 1]}`
      : null;

  // Status badge
  const statusVariant =
    runResult === null ? "default" : runResult.success ? "success" : "destructive";
  const statusLabel =
    runResult === null ? "mock data" : runResult.success ? "completed" : "failed";

  return (
    <section className="space-y-3">
      {/* Header — metadata left, actions right */}
      <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white p-3">
        <div className="flex min-w-0 items-center gap-3">
          {runResult !== null ? (
            <>
              <span className="font-mono text-xs text-slate-500">
                {runResult.run_id.slice(0, 8)}
              </span>
              <span className="truncate text-sm font-semibold text-slate-900">{reformLabel}</span>
              <Badge variant="secondary" className="text-xs">
                {yearRange ?? "—"}
              </Badge>
              <Badge variant={statusVariant} className="text-xs">
                {statusLabel}
              </Badge>
            </>
          ) : (
            <>
              <span className="text-sm font-semibold text-slate-900">{reformLabel}</span>
              <Badge variant="secondary" className="text-xs">—</Badge>
              <Badge variant="default" className="text-xs">
                mock data
              </Badge>
            </>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Button size="sm" onClick={onCompare}>
            Compare Runs
          </Button>
          {runResult?.run_id ? (
            <Button variant="outline" size="sm" onClick={onViewDecisions}>
              Behavioral Decisions
            </Button>
          ) : null}
          <Button variant="ghost" size="sm" onClick={onRunAgain}>
            Run Again
          </Button>
        </div>
      </div>

      {/* Tabbed content */}
      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <div className="rounded-lg border border-slate-200 bg-white">
          <TabsList className="w-full justify-start border-b border-slate-200 bg-white">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="export">Data &amp; Export</TabsTrigger>
            <TabsTrigger value="detail">Detail</TabsTrigger>
          </TabsList>

          <div className="p-3">
            {/* Overview tab */}
            <TabsContent value="overview">
              <div className="space-y-3">
                <DistributionalChart data={decileData} reformLabel={reformLabel} />
                <div className="grid gap-2 xl:grid-cols-3">
                  {summaryStats.map((stat) => (
                    <SummaryStatCard key={stat.id} stat={stat} />
                  ))}
                </div>
                {isPlaceholder ? (
                  <p className="text-xs text-slate-400">No indicator data available.</p>
                ) : null}
              </div>
            </TabsContent>

            {/* Data & Export tab */}
            <TabsContent value="export">
              <div className="space-y-3">
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                  <p className="mb-2 text-sm font-semibold text-slate-900">Export Results</p>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs font-medium text-slate-700">CSV</p>
                        <p className="text-xs text-slate-500">Tabular data for spreadsheets</p>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={onExportCsv}
                        disabled={!runResult?.success}
                      >
                        <Download className="mr-1 h-3.5 w-3.5" /> Export CSV
                      </Button>
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs font-medium text-slate-700">Parquet</p>
                        <p className="text-xs text-slate-500">
                          Columnar format for programmatic analysis
                        </p>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={onExportParquet}
                        disabled={!runResult?.success}
                      >
                        <Download className="mr-1 h-3.5 w-3.5" /> Export Parquet
                      </Button>
                    </div>
                  </div>
                  {!runResult?.success ? (
                    <p className="mt-2 text-xs text-slate-400">
                      Run a simulation first to enable exports.
                    </p>
                  ) : null}
                </div>
              </div>
            </TabsContent>

            {/* Detail tab */}
            <TabsContent value="detail">
              {detailLoading ? (
                <div aria-busy="true" role="status" className="space-y-2">
                  <span className="sr-only">Loading detail</span>
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-3 w-5/6" />
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-3 w-2/3" />
                </div>
              ) : detailError ? (
                <p className="text-xs text-slate-400">Detail unavailable.</p>
              ) : resultDetail !== null ? (
                <ResultDetailView detail={resultDetail} />
              ) : (
                <p className="text-xs text-slate-400">
                  Run a simulation to see detailed results.
                </p>
              )}
            </TabsContent>
          </div>
        </div>
      </Tabs>
    </section>
  );
}
