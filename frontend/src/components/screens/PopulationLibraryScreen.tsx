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

import { Eye, BarChart3, CheckCircle2, Trash2, Pencil, Upload, Plus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import type { PopulationLibraryItem } from "@/api/types";

// ============================================================================
// Types
// ============================================================================

export interface PopulationLibraryScreenProps {
  populations: PopulationLibraryItem[];
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
// Origin and trust status badges
// ============================================================================

function OriginBadge({ origin }: { origin: PopulationLibraryItem["origin"] }) {
  const label = origin === "built-in" ? "[Built-in]" : origin === "generated" ? "[Generated]" : "[Uploaded]";
  const variant = origin === "built-in" ? "secondary" : origin === "generated" ? "default" : "outline";
  return <Badge variant={variant} className="text-xs">{label}</Badge>;
}

/** Trust status badge component.

Story 21.2 / AC8: Display trust status using canonical evidence field.
*/
function TrustStatusBadge({ trustStatus }: { trustStatus: PopulationLibraryItem["trust_status"] }) {
  switch (trustStatus) {
    case "production-safe":
      return <Badge className="bg-green-100 text-green-800 text-xs">Production-Safe</Badge>;
    case "exploratory":
      return <Badge className="bg-yellow-100 text-yellow-800 text-xs">Exploratory</Badge>;
    case "demo-only":
      return <Badge className="bg-gray-100 text-gray-800 text-xs">Demo Only</Badge>;
    case "validation-pending":
      return <Badge className="bg-orange-100 text-orange-800 text-xs">Validation Pending</Badge>;
    case "not-for-public-inference":
      return <Badge className="bg-red-100 text-red-800 text-xs">Internal Use Only</Badge>;
    default:
      return <Badge variant="outline" className="text-xs">{trustStatus}</Badge>;
  }
}

// ============================================================================
// Population card
// ============================================================================

interface PopulationCardProps {
  population: PopulationLibraryItem;
  isSelected: boolean;
  onPreview: () => void;
  onExplore: () => void;
  onSelect: () => void;
  onDelete: () => void;
  onEdit?: () => void;
}

function PopulationCard({
  population,
  isSelected,
  onPreview,
  onExplore,
  onSelect,
  onDelete,
  onEdit,
}: PopulationCardProps) {
  return (
    <div
      className={`relative flex flex-col gap-3 rounded-lg border bg-white p-4 shadow-sm transition-all ${
        isSelected ? "border-blue-500 ring-2 ring-blue-200" : "border-slate-200 hover:border-slate-300"
      }`}
    >
      {/* Selection indicator */}
      {isSelected && (
        <div className="absolute right-2 top-2">
          <CheckCircle2 className="h-5 w-5 text-blue-500" />
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col gap-1 pr-6">
        <span className="text-sm font-semibold text-slate-900 leading-tight">{population.name}</span>
        {/* Story 21.2 / AC8: Display both origin badge (legacy) and trust status badge (canonical) */}
        <div className="flex flex-wrap gap-1">
          <OriginBadge origin={population.origin} />
          <TrustStatusBadge trustStatus={population.trust_status} />
        </div>
      </div>

      {/* Metadata */}
      <div className="flex flex-col gap-0.5">
        <span className="text-xs text-slate-500">
          {population.households.toLocaleString()} rows · {population.column_count} cols
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
    </div>
  );
}

// ============================================================================
// Main component
// ============================================================================

export function PopulationLibraryScreen({
  populations,
  selectedPopulationId,
  loading,
  onPreview,
  onExplore,
  onSelect,
  onDelete,
  onUpload,
  onBuildNew,
}: PopulationLibraryScreenProps) {
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
        ) : populations.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 py-16">
            <p className="text-sm text-slate-500">No populations available.</p>
            <Button size="sm" onClick={onBuildNew}>Build New Population</Button>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4 xl:grid-cols-3 2xl:grid-cols-4">
            {populations.map((pop) => (
              <PopulationCard
                key={pop.id}
                population={pop}
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
