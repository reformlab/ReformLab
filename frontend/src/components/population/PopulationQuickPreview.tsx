// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * PopulationQuickPreview — right-side slide-over panel for quick row preview.
 *
 * Shows the first 100 rows in a sortable table with per-column filter inputs.
 * Closes on backdrop click, Escape key, or X button.
 *
 * Story 20.4 — AC-2.
 */

import { useEffect, useRef, useState } from "react";
import { X, ArrowUp, ArrowDown, ArrowUpDown, ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { mockPopulationPreview } from "@/data/mock-population-explorer";
import type { ColumnInfo, PopulationPreviewResponse } from "@/api/types";

// ============================================================================
// Types
// ============================================================================

export interface PopulationQuickPreviewProps {
  populationId: string;
  populationName: string;
  onClose: () => void;
  onOpenFullView: (id: string) => void;
}

type SortDirection = "asc" | "desc" | null;

// ============================================================================
// Helpers
// ============================================================================

function buildPreviewData(id: string): PopulationPreviewResponse {
  // In Story 20.4 we use mock data; Story 20.7 replaces with real API call.
  if (id === mockPopulationPreview.id) return mockPopulationPreview;
  // Generic fallback: return mock with adapted id/name
  return { ...mockPopulationPreview, id, name: id };
}

function sortRows(
  rows: Record<string, unknown>[],
  col: string | null,
  dir: SortDirection,
): Record<string, unknown>[] {
  if (!col || !dir) return rows;
  return [...rows].sort((a, b) => {
    const av = a[col];
    const bv = b[col];
    if (av === null || av === undefined) return 1;
    if (bv === null || bv === undefined) return -1;
    const cmp = av < bv ? -1 : av > bv ? 1 : 0;
    return dir === "asc" ? cmp : -cmp;
  });
}

function filterRows(
  rows: Record<string, unknown>[],
  filters: Record<string, string>,
): Record<string, unknown>[] {
  return rows.filter((row) =>
    Object.entries(filters).every(([col, term]) => {
      if (!term) return true;
      const val = row[col];
      return String(val ?? "").toLowerCase().includes(term.toLowerCase());
    }),
  );
}

// ============================================================================
// Column header with sort indicator
// ============================================================================

interface ColHeaderProps {
  col: ColumnInfo;
  sortCol: string | null;
  sortDir: SortDirection;
  onSort: (col: string) => void;
}

function ColHeader({ col, sortCol, sortDir, onSort }: ColHeaderProps) {
  const isActive = sortCol === col.name;
  const icon =
    isActive && sortDir === "asc" ? (
      <ArrowUp className="h-3 w-3" />
    ) : isActive && sortDir === "desc" ? (
      <ArrowDown className="h-3 w-3" />
    ) : (
      <ArrowUpDown className="h-3 w-3 opacity-30" />
    );

  return (
    <th
      className="cursor-pointer select-none whitespace-nowrap bg-slate-50 px-2 py-1.5 text-left text-xs font-semibold text-slate-700 first:pl-3"
      onClick={() => { onSort(col.name); }}
    >
      <div className="flex items-center gap-1">
        {col.name}
        {icon}
      </div>
    </th>
  );
}

// ============================================================================
// Main component
// ============================================================================

export function PopulationQuickPreview({
  populationId,
  populationName,
  onClose,
  onOpenFullView,
}: PopulationQuickPreviewProps) {
  const [preview] = useState<PopulationPreviewResponse>(() => buildPreviewData(populationId));
  const [sortCol, setSortCol] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<SortDirection>(null);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const panelRef = useRef<HTMLDivElement>(null);

  // Escape key close
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  function handleSort(col: string) {
    if (sortCol !== col) {
      setSortCol(col);
      setSortDir("asc");
    } else if (sortDir === "asc") {
      setSortDir("desc");
    } else {
      setSortCol(null);
      setSortDir(null);
    }
  }

  function handleFilter(col: string, value: string) {
    setFilters((prev) => ({ ...prev, [col]: value }));
  }

  const visibleRows = sortRows(filterRows(preview.rows, filters), sortCol, sortDir);

  return (
    <div
      className="fixed inset-0 z-50 flex"
      role="dialog"
      aria-label={`Quick preview: ${populationName}`}
    >
      {/* Backdrop */}
      <div
        data-testid="quick-preview-backdrop"
        className="flex-1 bg-black/30"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Slide-over panel */}
      <div
        ref={panelRef}
        className="flex h-full w-full max-w-xl flex-col overflow-hidden bg-white shadow-2xl"
      >
        {/* Header */}
        <div className="flex shrink-0 items-center gap-3 border-b border-slate-200 px-4 py-3">
          <div className="flex-1 truncate">
            <h2 className="truncate text-sm font-semibold text-slate-900">{populationName}</h2>
          </div>
          <Badge variant="secondary" className="shrink-0 text-xs">
            {preview.total_rows.toLocaleString()} rows
          </Badge>
          <button
            type="button"
            onClick={onClose}
            className="shrink-0 rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
            aria-label="Close preview"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Table */}
        <div className="flex-1 overflow-auto">
          <table className="w-full border-collapse text-xs">
            <thead className="sticky top-0 z-10">
              <tr>
                {preview.columns.map((col) => (
                  <ColHeader
                    key={col.name}
                    col={col}
                    sortCol={sortCol}
                    sortDir={sortDir}
                    onSort={handleSort}
                  />
                ))}
              </tr>
              <tr className="border-b border-slate-200 bg-white">
                {preview.columns.map((col) => (
                  <th key={col.name} className="px-1 py-1 first:pl-3">
                    <Input
                      className="h-6 text-xs"
                      placeholder="filter…"
                      value={filters[col.name] ?? ""}
                      onChange={(e) => { handleFilter(col.name, e.target.value); }}
                    />
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visibleRows.map((row, i) => (
                <tr key={i} className="border-b border-slate-100 hover:bg-slate-50">
                  {preview.columns.map((col) => (
                    <td
                      key={col.name}
                      className="px-2 py-1 font-mono text-xs text-slate-700 first:pl-3"
                    >
                      {row[col.name] === null || row[col.name] === undefined
                        ? <span className="text-slate-300">—</span>
                        : String(row[col.name])}
                    </td>
                  ))}
                </tr>
              ))}
              {visibleRows.length === 0 && (
                <tr>
                  <td colSpan={preview.columns.length} className="py-8 text-center text-slate-400">
                    No rows match the current filters
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div className="flex shrink-0 items-center justify-between border-t border-slate-200 px-4 py-2">
          <span className="text-xs text-slate-400">
            Showing {visibleRows.length} of {preview.rows.length} preview rows
          </span>
          <Button
            size="sm"
            variant="ghost"
            className="h-7 gap-1 text-xs text-blue-600 hover:text-blue-700"
            onClick={() => { onOpenFullView(populationId); }}
          >
            Open full view
            <ExternalLink className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>
    </div>
  );
}
