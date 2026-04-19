// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * PopulationLibraryScreen — default entry point for Stage 2 (Population).
 *
 * Displays a grid of population cards (built-in, generated, uploaded) with
 * action buttons for preview, explore, select, upload, and build-new.
 *
 * Story 20.4 — AC-1, AC-5, AC-6.
 */

import { useState } from "react";
import {
  Eye,
  BarChart3,
  CheckCircle2,
  Trash2,
  Pencil,
  Upload,
  Plus,
  Zap,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Collapsible, CollapsibleContent } from "@/components/ui/collapsible";
import { OriginBadge } from "@/components/population/OriginBadge";
import { TrustStatusBadge } from "@/components/population/TrustStatusBadge";
import { SyntheticBadge } from "@/components/population/SyntheticBadge";
import type { PopulationLibraryItem } from "@/api/types";
import { QUICK_TEST_POPULATION_ID } from "@/data/quick-test-population";

// ============================================================================
// Types
// ============================================================================

export interface PopulationLibraryScreenProps {
  populations: PopulationLibraryItem[];
  populationPreviewMeta?: Record<string, { totalRows: number; columns: string[] }>;
  selectedPopulationId: string;
  loading: boolean;
  onPreview: (id: string) => void;
  onExplore: (id: string) => void;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onUpload: () => void;
  onBuildNew: () => void;
}

// ============================================================================
// Population card
// ============================================================================

interface PopulationCardProps {
  population: PopulationLibraryItem;
  previewMeta?: { totalRows: number; columns: string[] };
  isSelected: boolean;
  onPreview: () => void;
  onExplore: () => void;
  onSelect: () => void;
  onDelete: () => void;
  onEdit?: () => void;
}

function PopulationCard({
  population,
  previewMeta,
  isSelected,
  onPreview,
  onExplore,
  onSelect,
  onDelete,
  onEdit,
}: PopulationCardProps) {
  // Story 22.4: Special treatment for Quick Test Population
  const isQuickTest = population.id === QUICK_TEST_POPULATION_ID;
  const [inspectOpen, setInspectOpen] = useState(false);
  const totalRows = previewMeta?.totalRows ?? population.households;
  const columnNames = previewMeta?.columns ?? [];
  const hasSchemaPreview = columnNames.length > 0;

  return (
    <div
      className={`relative flex flex-col gap-3 rounded-lg border bg-white p-4 shadow-sm transition-all ${
        isSelected ? "border-blue-500 ring-2 ring-blue-200" : "border-slate-200 hover:border-slate-300"
      } ${isQuickTest ? "border-amber-200 bg-amber-50/30" : ""}`}
      title={isQuickTest ? "For fast demos and smoke testing only — not for substantive analysis" : undefined}
    >
      {/* Selection indicator */}
      {isSelected && (
        <div className="absolute right-2 top-2">
          <CheckCircle2 className="h-5 w-5 text-blue-500" />
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col gap-1 pr-6">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-slate-900 leading-tight">{population.name}</span>
          {/* Story 22.4: Quick Test Population indicator */}
          {isQuickTest && (
            <div
              className="flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800"
              title="For fast demos and smoke testing only — not for substantive analysis"
            >
              <Zap className="h-3 w-3" />
              Fast demo / smoke test
            </div>
          )}
        </div>
        {/* Story 21.2 / AC8: Display trust status badge (canonical) */}
        {/* Story 21.4 / AC6, AC10: Display synthetic indicator badge for observed/synthetic populations */}
        <div className="flex flex-wrap gap-1">
          <OriginBadge origin={population.origin} />
          <TrustStatusBadge trustStatus={population.trust_status} />
          {/* Show SyntheticBadge for populations with clear origin (open-official or synthetic-public) */}
          {(population.canonical_origin === "open-official" ||
            population.canonical_origin === "synthetic-public") && (
            <SyntheticBadge
              canonicalOrigin={population.canonical_origin}
              isSynthetic={population.is_synthetic}
            />
          )}
        </div>
      </div>

      {/* Metadata */}
      <div className="flex flex-col gap-0.5">
        <span className="text-xs text-slate-500">
          {totalRows.toLocaleString()} rows · {population.column_count} cols
        </span>
        {population.year > 0 && (
          <span className="text-xs text-slate-400">{population.year}</span>
        )}
        {population.created_date && (
          <span className="text-xs text-slate-400">
            {new Date(population.created_date).toLocaleDateString()}
          </span>
        )}
      </div>

      <Separator />

      {/* Action buttons */}
      <div className="flex flex-wrap gap-1.5">
        <Button
          size="sm"
          variant="ghost"
          className="h-7 gap-1 px-2 text-xs"
          onClick={onPreview}
          title="Quick Preview"
        >
          <Eye className="h-3.5 w-3.5" />
          Preview
        </Button>
        <Button
          size="sm"
          variant="ghost"
          className="h-7 gap-1 px-2 text-xs"
          onClick={onExplore}
          title="Full Data Explorer"
        >
          <BarChart3 className="h-3.5 w-3.5" />
          Explore
        </Button>
        <Button
          size="sm"
          variant="ghost"
          className="h-7 gap-1 px-2 text-xs"
          onClick={() => { setInspectOpen((open) => !open); }}
          title="Inspect row count and columns"
          aria-expanded={inspectOpen}
        >
          {inspectOpen ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          Inspect
        </Button>
        <Button
          size="sm"
          variant={isSelected ? "default" : "ghost"}
          className="h-7 gap-1 px-2 text-xs"
          onClick={onSelect}
          title={isSelected ? "Deselect population" : "Select for scenario"}
        >
          <CheckCircle2 className="h-3.5 w-3.5" />
          {isSelected ? "Selected" : "Select"}
        </Button>
        {population.origin === "generated" && onEdit && (
          <Button
            size="sm"
            variant="ghost"
            className="h-7 gap-1 px-2 text-xs"
            onClick={onEdit}
            title="Edit in Data Fusion Workbench"
          >
            <Pencil className="h-3.5 w-3.5" />
            Edit
          </Button>
        )}
        {population.origin !== "built-in" && (
          <Button
            size="sm"
            variant="ghost"
            className="h-7 gap-1 px-2 text-xs text-red-600 hover:bg-red-50 hover:text-red-700"
            onClick={onDelete}
            title="Delete population"
          >
            <Trash2 className="h-3.5 w-3.5" />
            Delete
          </Button>
        )}
      </div>

      <Collapsible open={inspectOpen} onOpenChange={setInspectOpen}>
        <CollapsibleContent className="space-y-2 rounded-md border border-slate-200 bg-slate-50 p-3">
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs font-semibold text-slate-700">Dataset snapshot</p>
            <span className="text-xs text-slate-500">
              {totalRows.toLocaleString()} rows · {population.column_count} columns
            </span>
          </div>
          {hasSchemaPreview ? (
            <div className="flex max-h-28 flex-wrap gap-1 overflow-y-auto pr-1">
              {columnNames.map((column) => (
                <span
                  key={column}
                  className="rounded-full border border-slate-200 bg-white px-2 py-0.5 font-mono text-[11px] text-slate-600"
                >
                  {column}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500">
              Column metadata is not available for this dataset yet. Use Preview for sample rows or Explore for the full table.
            </p>
          )}
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
}

// ============================================================================
// Main component
// ============================================================================

export function PopulationLibraryScreen({
  populations,
  populationPreviewMeta = {},
  selectedPopulationId,
  loading,
  onPreview,
  onExplore,
  onSelect,
  onDelete,
  onUpload,
  onBuildNew,
}: PopulationLibraryScreenProps) {
  // Story 22.4: Ensure Quick Test Population is always displayed first
  // Use explicit filtering and spreading for guaranteed stable ordering
  const quickTestPop = populations.find((p) => p.id === QUICK_TEST_POPULATION_ID);
  const otherPops = populations.filter((p) => p.id !== QUICK_TEST_POPULATION_ID);
  const sortedPopulations = quickTestPop ? [quickTestPop, ...otherPops] : populations;

  const selectedPopulation = populations.find((p) => p.id === selectedPopulationId);

  return (
    <div className="flex h-full flex-col">
      {/* Toolbar */}
      <div className="flex shrink-0 items-center gap-3 border-b border-slate-200 bg-white px-6 py-3">
        <h1 className="text-base font-semibold text-slate-900">Population Library</h1>
        <div className="flex-1" />
        {selectedPopulation && (
          <span className="text-xs text-slate-500">
            Selected: <span className="font-medium text-slate-700">{selectedPopulation.name}</span>
          </span>
        )}
        <Button size="sm" variant="outline" className="h-8 gap-1.5" onClick={onUpload}>
          <Upload className="h-3.5 w-3.5" />
          Upload
        </Button>
        <Button size="sm" variant="outline" className="h-8 gap-1.5" onClick={onBuildNew}>
          <Plus className="h-3.5 w-3.5" />
          Build New
        </Button>
      </div>

      {/* Library grid */}
      <div className="flex-1 overflow-y-auto p-6">
        {loading ? (
          <div className="flex items-center justify-center py-16 text-sm text-slate-400">
            Loading populations…
          </div>
        ) : sortedPopulations.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 py-16">
            <p className="text-sm text-slate-500">No populations available.</p>
            <Button size="sm" onClick={onBuildNew}>Build New Population</Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"> {/* Story 22.7: Mobile-first grid */}
            {sortedPopulations.map((pop) => (
              <PopulationCard
                key={pop.id}
                population={pop}
                previewMeta={populationPreviewMeta[pop.id]}
                isSelected={pop.id === selectedPopulationId}
                onPreview={() => { onPreview(pop.id); }}
                onExplore={() => { onExplore(pop.id); }}
                onSelect={() => { onSelect(pop.id); }}
                onDelete={() => { onDelete(pop.id); }}
                onEdit={pop.origin === "generated" ? onBuildNew : undefined}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
