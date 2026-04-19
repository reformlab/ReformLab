// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Data source browser for the Data Fusion Workbench (Story 17.1, AC-1, AC-2). */

import { useState } from "react";
import { Search, ExternalLink, ChevronDown, ChevronUp, Eye, BarChart3 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent } from "@/components/ui/collapsible";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { getDataSourceDetail } from "@/api/data-fusion";
import type { MockDataSource } from "@/data/mock-data";
import type { DataSourceDetail } from "@/api/types";

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
  onPreview?: (provider: string, datasetId: string) => void;
  onExplore?: (provider: string, datasetId: string) => void;
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
  onPreview,
  onExplore,
}: DataSourceBrowserProps) {
  const [query, setQuery] = useState("");
  const [inspectedKey, setInspectedKey] = useState<string | null>(null);
  const [detailCache, setDetailCache] = useState<Record<string, DataSourceDetail>>({});
  const [loadingDetailKey, setLoadingDetailKey] = useState<string | null>(null);

  async function handleInspect(provider: string, datasetId: string) {
    const key = `${provider}/${datasetId}`;
    const nextOpen = inspectedKey === key ? null : key;
    setInspectedKey(nextOpen);

    if (nextOpen === null || detailCache[key]) {
      return;
    }

    setLoadingDetailKey(key);
    try {
      const detail = await getDataSourceDetail(provider, datasetId);
      setDetailCache((prev) => ({ ...prev, [key]: detail }));
    } catch {
      // Non-fatal. The card still exposes row and variable counts from the list response.
    } finally {
      setLoadingDetailKey((current) => (current === key ? null : current));
    }
  }

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
                const detailKey = `${provider}/${ds.id}`;
                const detail = detailCache[detailKey];
                const inspectOpen = inspectedKey === detailKey;
                const recordCount = detail?.record_count ?? ds.record_count;
                const columnCount = detail?.columns.length ?? ds.variable_count;
                return (
                  <div
                    key={ds.id}
                    className={cn(
                      "border transition-colors",
                      selected ? "border-blue-500 bg-blue-50" : "border-slate-200 bg-white",
                    )}
                  >
                    <button
                      type="button"
                      onClick={() => onToggleSource(provider, ds.id)}
                      className="w-full p-3 text-left hover:bg-slate-50/50"
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
                    </button>
                    <div className="flex items-center gap-1 border-t border-slate-100 px-3 py-1.5">
                      {onPreview && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="h-7 gap-1 px-2 text-xs text-slate-600"
                          onClick={(e) => { e.stopPropagation(); onPreview(provider, ds.id); }}
                          title="Quick Preview"
                        >
                          <Eye className="h-3 w-3" />
                          Preview
                        </Button>
                      )}
                      {onExplore && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="h-7 gap-1 px-2 text-xs text-slate-600"
                          onClick={(e) => { e.stopPropagation(); onExplore(provider, ds.id); }}
                          title="Full Data Explorer"
                        >
                          <BarChart3 className="h-3 w-3" />
                          Explore
                        </Button>
                      )}
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="h-7 gap-1 px-2 text-xs text-slate-600"
                        onClick={() => { void handleInspect(provider, ds.id); }}
                        aria-expanded={inspectOpen}
                      >
                        {inspectOpen ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                        Inspect
                      </Button>
                      <div className="flex-1" />
                      <a
                        href={ds.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-xs text-blue-600 hover:underline"
                      >
                        <ExternalLink className="h-3 w-3" />
                        Source
                      </a>
                    </div>
                    <Collapsible open={inspectOpen}>
                      <CollapsibleContent className="border-t border-slate-100 bg-slate-50 px-3 py-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge variant="info" className="text-xs">
                            {columnCount} columns
                          </Badge>
                          {recordCount != null ? (
                            <Badge variant="default" className="text-xs">
                              {recordCount.toLocaleString()} rows
                            </Badge>
                          ) : null}
                        </div>
                        {loadingDetailKey === detailKey ? (
                          <p className="mt-2 text-xs text-slate-500">Loading column metadata…</p>
                        ) : detail?.columns.length ? (
                          <div className="mt-2 flex max-h-28 flex-wrap gap-1 overflow-y-auto pr-1">
                            {detail.columns.map((column) => (
                              <span
                                key={column.name}
                                className="rounded-full border border-slate-200 bg-white px-2 py-0.5 font-mono text-[11px] text-slate-600"
                                title={column.description || column.type}
                              >
                                {column.name}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <p className="mt-2 text-xs text-slate-500">
                            Column metadata is not available for this source.
                          </p>
                        )}
                      </CollapsibleContent>
                    </Collapsible>
                  </div>
                );
              })}
            </div>
          </section>
        );
      })}
    </section>
  );
}
