/** Population preview with tabbed summary view (Story 17.1, AC-5). */

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { PopulationDistributionChart } from "./PopulationDistributionChart";
import type { GenerationResult } from "@/api/types";

interface PopulationPreviewProps {
  result: GenerationResult;
}

export function PopulationPreview({ result }: PopulationPreviewProps) {
  const { summary, assumption_chain } = result;

  // Build mock distribution data from column names for display
  // Real values require downloading the population data — not in scope for 17.1
  const columnChartData = summary.columns.slice(0, 8).map((col, i) => ({
    name: col.length > 10 ? col.slice(0, 10) + "…" : col,
    value: 100 - i * 8, // placeholder counts
  }));

  return (
    <section aria-label="Population preview" className="border border-slate-200 bg-white p-3">
      <div className="mb-3 flex items-center justify-between">
        <p className="text-sm font-semibold text-slate-900">Population Preview</p>
        <div className="flex gap-2">
          <Badge variant="success">{summary.record_count.toLocaleString()} records</Badge>
          <Badge variant="default">{summary.column_count} columns</Badge>
        </div>
      </div>

      <Tabs defaultValue="summary">
        <TabsList>
          <TabsTrigger value="summary">Summary</TabsTrigger>
          <TabsTrigger value="distributions">Distributions</TabsTrigger>
          <TabsTrigger value="assumptions">Assumptions</TabsTrigger>
        </TabsList>

        <TabsContent value="summary">
          <div className="mt-3 space-y-3">
            <div className="grid gap-2 xl:grid-cols-3">
              <div className="border border-slate-200 p-2">
                <p className="text-xs text-slate-500">Records</p>
                <p className="data-mono text-lg font-semibold text-slate-900">
                  {summary.record_count.toLocaleString()}
                </p>
              </div>
              <div className="border border-slate-200 p-2">
                <p className="text-xs text-slate-500">Columns</p>
                <p className="data-mono text-lg font-semibold text-slate-900">
                  {summary.column_count}
                </p>
              </div>
              <div className="border border-slate-200 p-2">
                <p className="text-xs text-slate-500">Assumptions</p>
                <p className="data-mono text-lg font-semibold text-slate-900">
                  {assumption_chain.length}
                </p>
              </div>
            </div>

            <div>
              <p className="mb-1 text-xs font-semibold text-slate-600">Columns</p>
              <div className="flex flex-wrap gap-1">
                {summary.columns.map((col) => (
                  <Badge key={col} variant="default" className="data-mono text-xs">
                    {col}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="distributions">
          <div className="mt-3 space-y-3">
            <p className="text-xs text-slate-500">
              Distribution charts show the relative presence of columns in the population.
              Full statistical distributions require running an indicator pass (Story 17.6).
            </p>
            {columnChartData.length > 0 ? (
              <PopulationDistributionChart
                title="Column coverage (placeholder)"
                data={columnChartData}
                valueLabel="Relative weight"
              />
            ) : (
              <p className="text-xs text-slate-400">No columns available to visualize.</p>
            )}
          </div>
        </TabsContent>

        <TabsContent value="assumptions">
          <div className="mt-3 space-y-2">
            {assumption_chain.length === 0 ? (
              <p className="text-xs text-slate-500">No assumptions recorded.</p>
            ) : (
              assumption_chain.map((record, i) => (
                <div key={i} className="border border-slate-200 p-2">
                  <p className="text-xs font-semibold text-slate-700">
                    Step {record.step_index}: {record.step_label}
                  </p>
                  <p className="text-xs text-slate-600">
                    <span className="font-medium">Method:</span>{" "}
                    <span className="data-mono">{record.method}</span>
                  </p>
                  {record.description ? (
                    <p className="mt-0.5 text-xs text-slate-500">{record.description}</p>
                  ) : null}
                </div>
              ))
            )}
          </div>
        </TabsContent>
      </Tabs>
    </section>
  );
}
