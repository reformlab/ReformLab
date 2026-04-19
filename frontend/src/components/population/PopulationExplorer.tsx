// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * PopulationExplorer — full-screen data explorer with Table, Profile, and Summary tabs.
 *
 * Renders when activeSubView === "population-explorer". Shows a tab-based explorer
 * for deep investigation of a population dataset.
 *
 * Story 20.4 — AC-3.
 */

import { useState, useEffect } from "react";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { PopulationDataTable } from "./PopulationDataTable";
import { PopulationProfiler } from "./PopulationProfiler";
import { PopulationSummaryView } from "./PopulationSummaryView";
import { usePopulationPreview, usePopulationProfile } from "@/hooks/useApi";
import { mockPopulationSummary, mockCrosstabData } from "@/data/mock-population-explorer";
import type { PopulationCrosstabResponse, PopulationPreviewResponse, PopulationProfileResponse } from "@/api/types";

// ============================================================================
// Types
// ============================================================================

export interface PopulationExplorerProps {
  populationId: string | null;
  onBack: () => void;
  onCrosstabRequest?: (id: string, colA: string, colB: string) => void;
  /** When provided, uses this data instead of fetching via hooks. */
  externalData?: {
    preview: PopulationPreviewResponse;
    profile: PopulationProfileResponse;
  };
  /** Label for the back button (defaults to "Back to Library"). */
  backLabel?: string;
}

// ============================================================================
// Main component
// ============================================================================

export function PopulationExplorer({
  populationId,
  onBack,
  onCrosstabRequest,
  externalData,
  backLabel = "Back to Library",
}: PopulationExplorerProps) {
  const [crosstabData, setCrosstabData] = useState<PopulationCrosstabResponse | null>(null);
  const populationPreviewHook = usePopulationPreview(externalData ? null : populationId);
  const populationProfileHook = usePopulationProfile(externalData ? null : populationId);
  const preview = externalData?.preview ?? populationPreviewHook.data;
  const profile = externalData?.profile ?? populationProfileHook.data;

  // Reset crosstab when population changes
  useEffect(() => {
    setCrosstabData(null);
  }, [populationId]);

  // Empty state — no population selected
  if (!populationId) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
        <p className="text-sm text-slate-500">
          Select a population from the library to explore
        </p>
        <Button size="sm" variant="outline" onClick={onBack}>
          Back to Library
        </Button>
      </div>
    );
  }

  function handleCrosstabRequest(colA: string, colB: string) {
    // Use mock data for Story 20.4; Story 20.7 wires real API
    setCrosstabData({ ...mockCrosstabData, col_a: colA, col_b: colB });
    onCrosstabRequest?.(populationId!, colA, colB);
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex shrink-0 items-center gap-3 border-b border-slate-200 bg-white px-6 py-3">
        <Button
          size="sm"
          variant="ghost"
          className="h-8 gap-1.5 text-xs"
          onClick={onBack}
          aria-label={backLabel}
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          {backLabel}
        </Button>
        <span className="text-slate-300">|</span>
        <span className="text-sm font-semibold text-slate-900">{preview.name}</span>
        <Badge variant="secondary" className="text-xs">
          {preview.total_rows.toLocaleString()} rows
        </Badge>
        <Badge variant="outline" className="text-xs">
          {preview.columns.length} cols
        </Badge>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="table" className="flex flex-1 flex-col overflow-hidden">
        <div className="shrink-0 border-b border-slate-200 bg-white px-6 py-2">
          <TabsList>
            <TabsTrigger value="table">Table</TabsTrigger>
            <TabsTrigger value="profile">Profile</TabsTrigger>
            <TabsTrigger value="summary">Summary</TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="table" className="flex-1 overflow-hidden m-0">
          <PopulationDataTable
            rows={preview.rows}
            columns={preview.columns}
            totalRows={preview.total_rows}
          />
        </TabsContent>

        <TabsContent value="profile" className="flex-1 overflow-hidden m-0">
          <PopulationProfiler
            profile={profile}
            crosstabData={crosstabData}
            onCrosstabRequest={handleCrosstabRequest}
          />
        </TabsContent>

        <TabsContent value="summary" className="flex-1 overflow-y-auto m-0">
          <PopulationSummaryView summary={mockPopulationSummary} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
