// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * PopulationStageScreen — stateful coordinator for Stage 2 (Population).
 *
 * Reads activeSubView from AppContext and renders:
 *   - null/undefined: PopulationLibraryScreen (default)
 *   - "data-fusion":  DataFusionWorkbench (existing)
 *   - "population-explorer": PopulationExplorer (new)
 *
 * Also manages local state: Quick Preview overlay, explorer population, uploaded populations.
 *
 * Story 20.4 — AC-1 through AC-6.
 */

import { useMemo, useState, useEffect, useRef } from "react";
import { toast } from "sonner";

import { useAppState } from "@/contexts/AppContext";
import { DataFusionWorkbench } from "@/components/screens/DataFusionWorkbench";
import { PopulationLibraryScreen } from "@/components/screens/PopulationLibraryScreen";
import { PopulationQuickPreview } from "@/components/population/PopulationQuickPreview";
import { PopulationExplorer } from "@/components/population/PopulationExplorer";
import { PopulationUploadZone } from "@/components/population/PopulationUploadZone";
import type { PopulationLibraryItem } from "@/api/types";
import { deletePopulation, getPopulationPreview } from "@/api/populations";

// ============================================================================
// Helpers
// ============================================================================

/** Map API populations to PopulationLibraryItem.

Story 21.2 / AC2: Preserves all evidence fields from API response.
The API returns PopulationLibraryItem with dual-field design (legacy + canonical).
*/
function toLibraryItem(p: PopulationLibraryItem): PopulationLibraryItem {
  return p;
}

// ============================================================================
// Module-level cache for uploaded populations
// ============================================================================

// Uploaded populations are cached at module level so they survive stage switches
// (PopulationStageScreen unmounts when the user navigates to another stage).
// The cache is cleared when the page reloads, matching the "session only" contract.
let _uploadedPopulationsCache: PopulationLibraryItem[] = [];

// ============================================================================
// Types
// ============================================================================

export interface PopulationStageScreenProps {
  /** Story 22.4: Callback when explorer population ID changes */
  onExplorerPopulationChange?: (populationId: string | null) => void;
}

// ============================================================================
// Main component
// ============================================================================

export function PopulationStageScreen({ onExplorerPopulationChange }: PopulationStageScreenProps) {
  const {
    populations,
    populationsLoading,
    dataFusionSources,
    dataFusionMethods,
    dataFusionResult,
    setDataFusionResult,
    activeSubView,
    navigateTo,
    activeScenario,
    updateScenarioField,
    selectedPopulationId,
    setSelectedPopulationId,
  } = useAppState();

  // Local state
  const [previewPopulationId, setPreviewPopulationId] = useState<string | null>(null);
  const [explorerPopulationId, setExplorerPopulationId] = useState<string | null>(null);
  const [uploadedPopulations, setUploadedPopulations] = useState<PopulationLibraryItem[]>(() => _uploadedPopulationsCache);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [populationPreviewMeta, setPopulationPreviewMeta] = useState<
    Record<string, { totalRows: number; columns: string[] }>
  >({});
  const requestedPreviewMetaRef = useRef<Set<string>>(new Set());

  // Merge all population sources
  const mergedPopulations = useMemo((): PopulationLibraryItem[] => {
    const builtIn: PopulationLibraryItem[] = populations.map(toLibraryItem);

    const generated: PopulationLibraryItem[] = dataFusionResult
      ? [
          {
            id: "data-fusion-result",
            name: "Fused Population",
            households: dataFusionResult.summary.record_count,
            source: "Data Fusion",
            year: new Date().getFullYear(),
            origin: "generated",
            // Story 21.2 / AC4: Canonical evidence fields for generated populations
            canonical_origin: "synthetic-public",
            access_mode: "bundled",
            trust_status: "exploratory",
            column_count: dataFusionResult.summary.column_count,
            created_date: new Date().toISOString(),
            is_synthetic: true,
          },
        ]
      : [];

    return [...builtIn, ...generated, ...uploadedPopulations];
  }, [populations, dataFusionResult, uploadedPopulations]);

  useEffect(() => {
    const localMeta: Record<string, { totalRows: number; columns: string[] }> = {};

    if (dataFusionResult) {
      localMeta["data-fusion-result"] = {
        totalRows: dataFusionResult.summary.record_count,
        columns: dataFusionResult.summary.columns,
      };
    }

    if (Object.keys(localMeta).length > 0) {
      setPopulationPreviewMeta((prev) => ({ ...prev, ...localMeta }));
    }

    const populationsToFetch = mergedPopulations.filter(
      (population) =>
        population.id !== "data-fusion-result" &&
        !requestedPreviewMetaRef.current.has(population.id),
    );

    if (populationsToFetch.length === 0) {
      return;
    }

    populationsToFetch.forEach((population) => {
      requestedPreviewMetaRef.current.add(population.id);
    });

    let cancelled = false;

    void Promise.allSettled(
      populationsToFetch.map(async (population) => {
        const preview = await getPopulationPreview(population.id, { limit: 1 });
        return [
          population.id,
          {
            totalRows: preview.total_rows,
            columns: preview.columns.map((column) => column.name),
          },
        ] as const;
      }),
    ).then((results) => {
      if (cancelled) {
        return;
      }

      const nextMeta: Record<string, { totalRows: number; columns: string[] }> = {};
      for (const result of results) {
        if (result.status === "fulfilled") {
          const [id, meta] = result.value;
          nextMeta[id] = meta;
        }
      }

      if (Object.keys(nextMeta).length > 0) {
        setPopulationPreviewMeta((prev) => ({ ...prev, ...nextMeta }));
      }
    });

    return () => {
      cancelled = true;
    };
  }, [mergedPopulations, dataFusionResult]);

  // Resolve the preview population name
  const previewPopulationName = useMemo(() => {
    if (!previewPopulationId) return "";
    return mergedPopulations.find((p) => p.id === previewPopulationId)?.name ?? previewPopulationId;
  }, [previewPopulationId, mergedPopulations]);

  // Story 22.4: Notify parent when explorer population ID changes
  useEffect(() => {
    onExplorerPopulationChange?.(explorerPopulationId);
  }, [explorerPopulationId, onExplorerPopulationChange]);

  // ============================================================================
  // Callbacks
  // ============================================================================

  function handlePreview(id: string) {
    setPreviewPopulationId(id);
  }

  function handleExplore(id: string) {
    setExplorerPopulationId(id);
    navigateTo("population", "population-explorer");
  }

  function handleSelect(id: string) {
    const isDeselecting = activeScenario?.populationIds.includes(id) ?? false;
    if (isDeselecting) {
      updateScenarioField("populationIds", []);
      setSelectedPopulationId("");
    } else {
      updateScenarioField("populationIds", [id]);
      setSelectedPopulationId(id);
    }
  }

  function handleDelete(id: string) {
    // If the deleted population is the selected one, clear selection
    if (
      (activeScenario?.populationIds.includes(id) ?? false) ||
      selectedPopulationId === id
    ) {
      updateScenarioField("populationIds", []);
      setSelectedPopulationId("");
    }

    if (id === "data-fusion-result") {
      setDataFusionResult(null);
      return;
    }

    // For uploaded populations: optimistic delete (no revert on failure per story spec)
    setUploadedPopulations((prev) => {
      const next = prev.filter((p) => p.id !== id);
      _uploadedPopulationsCache = next;
      return next;
    });

    // Fire API call (Story 20.7 endpoint) and warn on failure
    void deletePopulation(id).catch(() => {
      toast.warning("Population deleted locally", {
        description: "Backend sync failed — the population will reappear on next reload.",
      });
    });
  }

  function handleUploadConfirm(population: PopulationLibraryItem) {
    setUploadedPopulations((prev) => {
      const next = [population, ...prev];
      _uploadedPopulationsCache = next;
      return next;
    });
    setUploadDialogOpen(false);
    toast.success(`"${population.name}" added to library`);
  }

  function handleOpenFullView(id: string) {
    setPreviewPopulationId(null);
    setExplorerPopulationId(id);
    navigateTo("population", "population-explorer");
  }

  function handleBackToLibrary() {
    navigateTo("population");
  }

  function handleDataFusionGenerated(result: Parameters<typeof setDataFusionResult>[0]) {
    setDataFusionResult(result);
    // Navigate back to library to show the new generated population
    navigateTo("population");
  }

  // ============================================================================
  // Compute selected ID (canonical first, then legacy fallback)
  // ============================================================================

  const effectiveSelectedId =
    (activeScenario?.populationIds?.[0] ?? "") || selectedPopulationId;

  // ============================================================================
  // Sub-view routing
  // ============================================================================

  const content = (() => {
    if (activeSubView === "data-fusion") {
      return (
        <DataFusionWorkbench
          sources={dataFusionSources}
          methods={dataFusionMethods}
          initialResult={dataFusionResult}
          onPopulationGenerated={handleDataFusionGenerated}
        />
      );
    }

    if (activeSubView === "population-explorer") {
      return (
        <PopulationExplorer
          populationId={explorerPopulationId}
          onBack={handleBackToLibrary}
        />
      );
    }

    // Default: Population Library
    return (
      <PopulationLibraryScreen
        populations={mergedPopulations}
        populationPreviewMeta={populationPreviewMeta}
        selectedPopulationId={effectiveSelectedId}
        loading={populationsLoading}
        onPreview={handlePreview}
        onExplore={handleExplore}
        onSelect={handleSelect}
        onDelete={handleDelete}
        onUpload={() => { setUploadDialogOpen(true); }}
        onBuildNew={() => { navigateTo("population", "data-fusion"); }}
      />
    );
  })();

  return (
    <div className="flex h-full flex-col">
      {content}

      {/* Quick Preview slide-over (above library content) */}
      {previewPopulationId && (
        <PopulationQuickPreview
          populationId={previewPopulationId}
          populationName={previewPopulationName}
          onClose={() => { setPreviewPopulationId(null); }}
          onOpenFullView={handleOpenFullView}
        />
      )}

      {/* Upload overlay */}
      {uploadDialogOpen && (
        <PopulationUploadZone
          onClose={() => { setUploadDialogOpen(false); }}
          onConfirm={handleUploadConfirm}
        />
      )}
    </div>
  );
}
