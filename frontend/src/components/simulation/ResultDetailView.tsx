/** Result detail view — Story 17.3, AC-4.
 *
 * Tabbed view with:
 *   - Indicators tab: distributional chart + KPI cards
 *   - Data Summary tab: row/column count, year range, columns list
 *   - Manifest tab: manifest ID, scenario ID, adapter version, seed, timestamps
 *
 * When data_available=false, shows metadata-only with "Re-run" prompt.
 */

import { useState } from "react";

import { Download, RefreshCcw } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { ResultDetailResponse } from "@/api/types";

// ============================================================================
// Types
// ============================================================================

type Tab = "indicators" | "data" | "manifest";

interface ResultDetailViewProps {
  detail: ResultDetailResponse;
  onExportCsv?: () => void;
  onExportParquet?: () => void;
}

// ============================================================================
// Helpers
// ============================================================================

function formatTs(ts: string): string {
  try {
    return new Date(ts).toLocaleString(undefined, {
      year: "numeric", month: "short", day: "2-digit",
      hour: "2-digit", minute: "2-digit", second: "2-digit",
    });
  } catch {
    return ts;
  }
}

function policyLabel(detail: ResultDetailResponse): string {
  if (detail.portfolio_name) return detail.portfolio_name;
  if (detail.template_name) return detail.template_name;
  return detail.run_kind === "portfolio" ? "Portfolio run" : "Scenario run";
}

function statusVariant(status: string): "success" | "destructive" | "warning" | "default" {
  if (status === "completed") return "success";
  if (status === "failed") return "destructive";
  return "default";
}

// ============================================================================
// Indicators tab content
// ============================================================================

function IndicatorsTab({ detail }: { detail: ResultDetailResponse }) {
  if (!detail.data_available) {
    return (
      <div className="border border-slate-200 bg-slate-50 p-4 text-center">
        <RefreshCcw className="mx-auto mb-2 h-6 w-6 text-slate-400" />
        <p className="text-sm font-medium text-slate-700">Full data not available</p>
        <p className="text-xs text-slate-500 mt-1">
          The simulation result was evicted from the in-memory cache.
          Re-run the simulation to access indicators and export data.
        </p>
      </div>
    );
  }

  const indicators = detail.indicators as Record<string, unknown> | null;

  return (
    <div className="space-y-2">
      {indicators ? (
        <div className="border border-slate-200 bg-white p-3">
          <p className="text-xs font-semibold uppercase text-slate-500 mb-2">Summary</p>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
            {Object.entries(indicators).map(([key, val]) => (
              <div key={key} className="contents">
                <span className="text-slate-500">{key}</span>
                <span className="data-mono font-medium text-slate-800">
                  {typeof val === "number" ? val.toLocaleString() : String(val)}
                </span>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <p className="text-xs text-slate-400">No indicator data available.</p>
      )}
    </div>
  );
}

// ============================================================================
// Data Summary tab content
// ============================================================================

function DataSummaryTab({
  detail,
  onExportCsv,
  onExportParquet,
}: {
  detail: ResultDetailResponse;
  onExportCsv?: () => void;
  onExportParquet?: () => void;
}) {
  return (
    <div className="space-y-3">
      <div className="border border-slate-200 bg-white p-3">
        <p className="text-xs font-semibold uppercase text-slate-500 mb-2">Panel Data</p>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
          <span className="text-slate-500">Rows</span>
          <span className="data-mono font-medium text-slate-800">
            {detail.row_count.toLocaleString()}
          </span>
          <span className="text-slate-500">Columns</span>
          <span className="data-mono font-medium text-slate-800">
            {detail.column_count ?? detail.columns?.length ?? "—"}
          </span>
          <span className="text-slate-500">Year range</span>
          <span className="data-mono font-medium text-slate-800">
            {detail.start_year}–{detail.end_year}
          </span>
        </div>
      </div>

      {detail.columns && detail.columns.length > 0 ? (
        <div className="border border-slate-200 bg-white p-3">
          <p className="text-xs font-semibold uppercase text-slate-500 mb-2">Columns</p>
          <div className="flex flex-wrap gap-1">
            {detail.columns.map((col) => (
              <Badge key={col} variant="info" className="text-xs">
                {col}
              </Badge>
            ))}
          </div>
        </div>
      ) : null}

      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          disabled={!detail.data_available}
          onClick={onExportCsv}
          aria-label="Export as CSV"
        >
          <Download className="h-3.5 w-3.5 mr-1" />
          CSV
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={!detail.data_available}
          onClick={onExportParquet}
          aria-label="Export as Parquet"
        >
          <Download className="h-3.5 w-3.5 mr-1" />
          Parquet
        </Button>
        {!detail.data_available ? (
          <p className="text-xs text-slate-400 self-center">Re-run to access exports</p>
        ) : null}
      </div>
    </div>
  );
}

// ============================================================================
// Manifest tab content
// ============================================================================

function ManifestTab({ detail }: { detail: ResultDetailResponse }) {
  const rows: [string, string][] = [
    ["Run ID", detail.run_id],
    ["Manifest ID", detail.manifest_id || "—"],
    ["Scenario ID", detail.scenario_id || "—"],
    ["Adapter version", detail.adapter_version || "—"],
    ["Seed", detail.seed !== null && detail.seed !== undefined ? String(detail.seed) : "random"],
    ["Population ID", detail.population_id ?? "—"],
    ["Started", formatTs(detail.started_at)],
    ["Finished", formatTs(detail.finished_at)],
    ["Status", detail.status],
  ];

  return (
    <div className="border border-slate-200 bg-white p-3">
      <p className="text-xs font-semibold uppercase text-slate-500 mb-2">Run Manifest</p>
      <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-xs">
        {rows.map(([label, value]) => (
          <>
            <dt key={`${label}-dt`} className="text-slate-500">{label}</dt>
            <dd key={`${label}-dd`} className="data-mono font-medium text-slate-800 break-all">{value}</dd>
          </>
        ))}
      </dl>
    </div>
  );
}

// ============================================================================
// ResultDetailView
// ============================================================================

export function ResultDetailView({
  detail,
  onExportCsv,
  onExportParquet,
}: ResultDetailViewProps) {
  const [activeTab, setActiveTab] = useState<Tab>("indicators");

  return (
    <section
      className="border border-slate-200 bg-white"
      aria-label={`Result detail for run ${detail.run_id.slice(0, 8)}`}
    >
      {/* Header */}
      <div className="border-b border-slate-100 px-3 py-2 flex items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-semibold text-slate-900 truncate">{policyLabel(detail)}</p>
          <p className="text-xs text-slate-500 data-mono">{detail.run_id.slice(0, 8)}</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Badge variant={statusVariant(detail.status)} className="text-xs">
            {detail.status}
          </Badge>
          {!detail.data_available ? (
            <Badge variant="default" className="text-xs">metadata only</Badge>
          ) : null}
          <Badge variant="info" className="text-xs">
            {detail.start_year}–{detail.end_year}
          </Badge>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as Tab)}>
        <TabsList className="w-full justify-start rounded-none border-b border-slate-100 bg-transparent p-0">
          <TabsTrigger
            value="indicators"
            className="rounded-none border-b-2 border-transparent px-3 py-2 text-xs data-[state=active]:border-blue-500"
          >
            Indicators
          </TabsTrigger>
          <TabsTrigger
            value="data"
            className="rounded-none border-b-2 border-transparent px-3 py-2 text-xs data-[state=active]:border-blue-500"
          >
            Data Summary
          </TabsTrigger>
          <TabsTrigger
            value="manifest"
            className="rounded-none border-b-2 border-transparent px-3 py-2 text-xs data-[state=active]:border-blue-500"
          >
            Manifest
          </TabsTrigger>
        </TabsList>

        <TabsContent value="indicators" className="p-3">
          <IndicatorsTab detail={detail} />
        </TabsContent>

        <TabsContent value="data" className="p-3">
          <DataSummaryTab
            detail={detail}
            onExportCsv={onExportCsv}
            onExportParquet={onExportParquet}
          />
        </TabsContent>

        <TabsContent value="manifest" className="p-3">
          <ManifestTab detail={detail} />
        </TabsContent>
      </Tabs>
    </section>
  );
}
