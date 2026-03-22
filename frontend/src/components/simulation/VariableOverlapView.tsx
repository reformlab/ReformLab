/** Variable overlap display for the Data Fusion Workbench (Story 17.1, AC-2). */

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { getDataSourceDetail } from "@/api/data-fusion";
import type { MockDataSource } from "@/data/mock-data";

interface SelectedSource {
  provider: string;
  dataset_id: string;
}

interface VariableOverlapViewProps {
  sources: Record<string, MockDataSource[]>;
  selectedSources: SelectedSource[];
}

function getDataset(
  sources: Record<string, MockDataSource[]>,
  provider: string,
  datasetId: string,
): MockDataSource | undefined {
  return sources[provider]?.find((ds) => ds.id === datasetId);
}

export function VariableOverlapView({ sources, selectedSources }: VariableOverlapViewProps) {
  const [columnsBySource, setColumnsBySource] = useState<Record<string, string[]>>({});
  const [loading, setLoading] = useState(false);

  // Fetch column details for each selected source
  useEffect(() => {
    if (selectedSources.length < 2) return;

    let cancelled = false;
    setLoading(true);

    async function fetchColumns() {
      const results: Record<string, string[]> = {};
      for (const src of selectedSources) {
        const key = `${src.provider}/${src.dataset_id}`;
        try {
          const detail = await getDataSourceDetail(src.provider, src.dataset_id);
          results[key] = detail.columns.map((c) => c.name);
        } catch {
          // Non-fatal — source detail may not be available
          results[key] = [];
        }
      }
      if (!cancelled) {
        setColumnsBySource(results);
        setLoading(false);
      }
    }

    void fetchColumns();
    return () => { cancelled = true; };
  }, [selectedSources]);

  if (selectedSources.length < 2) {
    return null;
  }

  const datasets = selectedSources
    .map((s) => getDataset(sources, s.provider, s.dataset_id))
    .filter((ds): ds is MockDataSource => ds !== undefined);

  if (datasets.length < 2) return null;

  // Compute column intersection across all selected sources
  const allColumnSets = selectedSources.map((s) => {
    const key = `${s.provider}/${s.dataset_id}`;
    return new Set(columnsBySource[key] ?? []);
  });

  const overlappingColumns = allColumnSets.length > 0
    ? [...allColumnSets[0]!].filter((col) => allColumnSets.every((set) => set.has(col)))
    : [];

  const hasColumns = Object.values(columnsBySource).some((cols) => cols.length > 0);
  const hasOverlap = overlappingColumns.length > 0;

  return (
    <section
      aria-label="Variable overlap"
      className="border border-slate-200 bg-white p-3 space-y-3"
    >
      <p className="text-sm font-semibold text-slate-900">Variable Overlap</p>

      {loading ? (
        <div aria-busy="true" role="status" className="space-y-2">
          <span className="sr-only">Loading column details</span>
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-3/4" />
        </div>
      ) : hasOverlap ? (
        <div className="space-y-2">
          <p className="text-xs text-emerald-700">
            {overlappingColumns.length} shared variable{overlappingColumns.length !== 1 ? "s" : ""} found
            across all selected sources. These can be used as stratification keys for Conditional Sampling.
          </p>
          <div className="flex flex-wrap gap-1">
            {overlappingColumns.map((col) => (
              <Badge key={col} variant="success" className="data-mono text-xs">
                {col}
              </Badge>
            ))}
          </div>
        </div>
      ) : hasColumns ? (
        <p className="text-xs text-amber-600">
          No overlapping variables found across all selected sources.
          You can still merge using Uniform Distribution (no shared key required).
        </p>
      ) : (
        <p className="text-xs text-slate-600">
          The selected sources may share overlapping columns (e.g. region code, income decile).
          Overlapping variables can be used as stratification keys for Conditional Sampling.
          Column-level details are available in each dataset's detail view.
        </p>
      )}

      <div className="grid gap-2 xl:grid-cols-2">
        {datasets.map((ds) => {
          const key = `${ds.provider}/${ds.id}`;
          const cols = columnsBySource[key] ?? [];
          return (
            <div key={key} className="border border-slate-200 p-2">
              <p className="text-xs font-semibold text-slate-700">{ds.name}</p>
              <p className="text-xs text-slate-500">{ds.variable_count} variables</p>
              <div className="mt-1.5 flex flex-wrap gap-1">
                <Badge variant="info" className="text-xs">
                  {ds.provider.toUpperCase()}
                </Badge>
                {cols.length > 0 ? cols.map((c) => (
                  <Badge
                    key={c}
                    variant={hasOverlap && overlappingColumns.includes(c) ? "success" : "default"}
                    className="data-mono text-xs"
                  >
                    {c}
                  </Badge>
                )) : null}
              </div>
            </div>
          );
        })}
      </div>

      <p className="text-xs text-slate-500">
        {selectedSources.length} sources selected. Proceed to choose a merge method.
      </p>
    </section>
  );
}
