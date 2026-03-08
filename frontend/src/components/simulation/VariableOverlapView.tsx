/** Variable overlap display for the Data Fusion Workbench (Story 17.1, AC-2). */

import { Badge } from "@/components/ui/badge";
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
  if (selectedSources.length < 2) {
    return null;
  }

  const datasets = selectedSources
    .map((s) => getDataset(sources, s.provider, s.dataset_id))
    .filter((ds): ds is MockDataSource => ds !== undefined);

  if (datasets.length < 2) return null;

  // For UI purposes, check if any two selected sources share an overlap.
  // Real column intersection is only available after fetching detail endpoints
  // (GET /sources/{provider}/{dataset_id}). Column names are not stored in the
  // catalog metadata used here — only variable_count is available.
  const hasKnownOverlap = false;

  return (
    <section
      aria-label="Variable overlap"
      className="border border-slate-200 bg-white p-3 space-y-3"
    >
      <p className="text-sm font-semibold text-slate-900">Variable Overlap</p>

      {hasKnownOverlap ? null : (
        <p className="text-xs text-slate-600">
          The selected sources may share overlapping columns (e.g. region code, income decile).
          Overlapping variables can be used as stratification keys for Conditional Sampling.
          Column-level details are available in each dataset's detail view.
        </p>
      )}

      <div className="grid gap-2 xl:grid-cols-2">
        {datasets.map((ds) => (
          <div key={`${ds.provider}-${ds.id}`} className="border border-slate-200 p-2">
            <p className="text-xs font-semibold text-slate-700">{ds.name}</p>
            <p className="text-xs text-slate-500">{ds.variable_count} variables</p>
            <div className="mt-1.5 flex flex-wrap gap-1">
              <Badge variant="info" className="text-xs">
                {ds.provider.toUpperCase()}
              </Badge>
            </div>
          </div>
        ))}
      </div>

      {selectedSources.length >= 2 ? (
        <p className="text-xs text-slate-500">
          {selectedSources.length} sources selected. Proceed to choose a merge method.
        </p>
      ) : null}
    </section>
  );
}
