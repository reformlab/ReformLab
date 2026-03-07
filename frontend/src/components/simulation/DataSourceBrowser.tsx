/** Data source browser for the Data Fusion Workbench (Story 17.1, AC-1, AC-2). */

import { useState } from "react";
import { Search, ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import type { MockDataSource } from "@/data/mock-data";

const PROVIDER_LABELS: Record<string, string> = {
  insee: "INSEE",
  eurostat: "Eurostat",
  ademe: "ADEME",
  sdes: "SDES",
};

interface DataSourceBrowserProps {
  sources: Record<string, MockDataSource[]>;
  selectedIds: Array<{ provider: string; dataset_id: string }>;
  onToggleSource: (provider: string, datasetId: string) => void;
}

function isSelected(
  selected: Array<{ provider: string; dataset_id: string }>,
  provider: string,
  datasetId: string,
): boolean {
  return selected.some((s) => s.provider === provider && s.dataset_id === datasetId);
}

export function DataSourceBrowser({
  sources,
  selectedIds,
  onToggleSource,
}: DataSourceBrowserProps) {
  const [query, setQuery] = useState("");

  return (
    <section aria-label="Data source browser" className="space-y-3">
      <div className="relative">
        <Search className="absolute left-2 top-2.5 h-4 w-4 text-slate-400" />
        <Input
          placeholder="Filter datasets..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="pl-8"
          aria-label="Filter data sources"
        />
      </div>

      {Object.entries(sources).map(([provider, datasets]) => {
        const filtered = query
          ? datasets.filter(
              (ds) =>
                ds.name.toLowerCase().includes(query.toLowerCase()) ||
                ds.description.toLowerCase().includes(query.toLowerCase()),
            )
          : datasets;

        if (filtered.length === 0) return null;

        return (
          <section key={provider} aria-label={`${PROVIDER_LABELS[provider] ?? provider} datasets`}>
            <p className="mb-1 text-xs font-semibold uppercase text-slate-500">
              {PROVIDER_LABELS[provider] ?? provider}
            </p>
            <div className="grid gap-2 xl:grid-cols-2">
              {filtered.map((ds) => {
                const selected = isSelected(selectedIds, provider, ds.id);
                return (
                  <button
                    key={ds.id}
                    type="button"
                    onClick={() => onToggleSource(provider, ds.id)}
                    className={cn(
                      "border p-3 text-left transition-colors",
                      selected
                        ? "border-blue-500 bg-blue-50"
                        : "border-slate-200 bg-white hover:bg-slate-50",
                    )}
                    aria-pressed={selected}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-slate-900">{ds.name}</p>
                        <p className="mt-0.5 text-xs text-slate-600 line-clamp-2">
                          {ds.description}
                        </p>
                        <div className="mt-1.5 flex flex-wrap gap-1.5">
                          <Badge variant="default" className="text-xs">
                            {ds.variable_count} variables
                          </Badge>
                          {ds.record_count != null ? (
                            <Badge variant="default" className="text-xs">
                              {ds.record_count.toLocaleString()} records
                            </Badge>
                          ) : null}
                        </div>
                      </div>
                      <input
                        type="checkbox"
                        readOnly
                        checked={selected}
                        tabIndex={-1}
                        aria-hidden="true"
                        className="mt-0.5 h-4 w-4 shrink-0 accent-blue-500"
                      />
                    </div>
                    <a
                      href={ds.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="mt-1.5 flex items-center gap-1 text-xs text-blue-600 hover:underline"
                    >
                      <ExternalLink className="h-3 w-3" />
                      Source
                    </a>
                  </button>
                );
              })}
            </div>
          </section>
        );
      })}
    </section>
  );
}
