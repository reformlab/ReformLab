// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Data Fusion Workbench screen (Story 17.1, AC-1 through AC-6).
 *
 * Orchestrates a step-flow: Source Selection → Variable Review →
 * Method Selection → Generation → Population Preview.
 */

import { useState, useCallback } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { DataSourceBrowser } from "@/components/simulation/DataSourceBrowser";
import { VariableOverlapView } from "@/components/simulation/VariableOverlapView";
import { MergeMethodSelector } from "@/components/simulation/MergeMethodSelector";
import { MergeParametersPanel } from "@/components/simulation/MergeParametersPanel";
import { PopulationGenerationProgress } from "@/components/simulation/PopulationGenerationProgress";
import { PopulationPreview } from "@/components/simulation/PopulationPreview";
import { PopulationValidationPanel } from "@/components/simulation/PopulationValidationPanel";
import { PopulationQuickPreview } from "@/components/population/PopulationQuickPreview";
import { PopulationExplorer } from "@/components/population/PopulationExplorer";
import { generatePopulation } from "@/api/data-fusion";
import { ApiError } from "@/api/client";
import { WorkbenchStepper } from "@/components/simulation/WorkbenchStepper";
import { useDataSourcePreview, useDataSourceProfile } from "@/hooks/useApi";
import type { MockDataSource, MockMergeMethod } from "@/data/mock-data";
import type { GenerationResult } from "@/api/types";

// ============================================================================
// Step definitions
// ============================================================================

type WorkbenchStep = "sources" | "overlap" | "method" | "generate" | "preview";

const STEPS: Array<{ key: WorkbenchStep; label: string }> = [
  { key: "sources", label: "1. Sources" },
  { key: "overlap", label: "2. Variables" },
  { key: "method", label: "3. Method" },
  { key: "generate", label: "4. Generate" },
  { key: "preview", label: "5. Preview" },
];

interface SelectedSource {
  provider: string;
  dataset_id: string;
}

// ============================================================================
// Main workbench component
// ============================================================================

interface DataFusionWorkbenchProps {
  sources: Record<string, MockDataSource[]>;
  methods: MockMergeMethod[];
  initialResult?: GenerationResult | null;
  onPopulationGenerated?: (result: GenerationResult) => void;
}

export function DataFusionWorkbench({
  sources,
  methods,
  initialResult = null,
  onPopulationGenerated,
}: DataFusionWorkbenchProps) {
  // Step state
  const [activeStep, setActiveStep] = useState<WorkbenchStep>("sources");

  // Source selection state (AC-1, AC-2)
  const [selectedSources, setSelectedSources] = useState<SelectedSource[]>([]);

  // Method + parameters state (AC-3)
  const [selectedMethodId, setSelectedMethodId] = useState("uniform");
  const [seed, setSeed] = useState(42);
  const [strataColumns, setStrataColumns] = useState("");

  // Data source preview/explore state
  const [previewSource, setPreviewSource] = useState<{ provider: string; datasetId: string } | null>(null);
  const [explorerSource, setExplorerSource] = useState<{ provider: string; datasetId: string } | null>(null);

  // Data source hooks (active only when a source is being previewed/explored)
  const previewHook = useDataSourcePreview(
    previewSource?.provider ?? null,
    previewSource?.datasetId ?? null,
  );
  const explorerPreviewHook = useDataSourcePreview(
    explorerSource?.provider ?? null,
    explorerSource?.datasetId ?? null,
  );
  const explorerProfileHook = useDataSourceProfile(
    explorerSource?.provider ?? null,
    explorerSource?.datasetId ?? null,
  );

  // Generation state (AC-4)
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<GenerationResult | null>(initialResult);
  const [genError, setGenError] = useState<string | null>(null);
  const [genErrorDetail, setGenErrorDetail] = useState<{
    what: string;
    why: string;
    fix: string;
  } | null>(null);

  // Source toggle
  const handleToggleSource = useCallback((provider: string, datasetId: string) => {
    setSelectedSources((prev) => {
      const exists = prev.some((s) => s.provider === provider && s.dataset_id === datasetId);
      if (exists) {
        return prev.filter((s) => !(s.provider === provider && s.dataset_id === datasetId));
      }
      return [...prev, { provider, dataset_id: datasetId }];
    });
  }, []);

  // Generation handler (AC-4, AC-6)
  const handleGenerate = useCallback(async () => {
    if (selectedSources.length < 2) {
      toast.error("Select at least 2 data sources before generating");
      return;
    }

    setGenerating(true);
    setGenError(null);
    setGenErrorDetail(null);
    setResult(null);
    setActiveStep("generate");

    try {
      const strataList = strataColumns
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);

      const generated = await generatePopulation({
        sources: selectedSources,
        merge_method: selectedMethodId,
        seed,
        strata_columns: strataList,
      });

      setResult(generated);
      onPopulationGenerated?.(generated);
      setActiveStep("preview");
      toast.success("Population generated successfully");
    } catch (err) {
      if (err instanceof ApiError) {
        setGenErrorDetail({ what: err.what, why: err.why, fix: err.fix });
        toast.error(`${err.what} — ${err.why}`, { description: err.fix });
      } else if (err instanceof Error) {
        setGenError(err.message);
        toast.error("Generation failed", { description: err.message });
      }
    } finally {
      setGenerating(false);
    }
  }, [selectedSources, selectedMethodId, seed, strataColumns, onPopulationGenerated]);

  // Step navigation helpers
  const stepIndex = STEPS.findIndex((s) => s.key === activeStep);
  const canGoBack = stepIndex > 0;
  const isLastStep = activeStep === "preview";

  const goBack = () => {
    const prev = STEPS[stepIndex - 1];
    if (prev) setActiveStep(prev.key);
  };

  const goNext = () => {
    if (activeStep === "sources") {
      if (selectedSources.length < 2) {
        toast.error("Select at least 2 data sources to proceed");
        return;
      }
      setActiveStep("overlap");
    } else if (activeStep === "overlap") {
      setActiveStep("method");
    } else if (activeStep === "method") {
      void handleGenerate();
    } else if (activeStep === "generate" && result) {
      setActiveStep("preview");
    }
  };

  const canProceed =
    (activeStep === "sources" && selectedSources.length >= 2) ||
    activeStep === "overlap" ||
    activeStep === "method" ||
    (activeStep === "generate" && result !== null) ||
    activeStep === "preview";

  // When exploring a data source, show the explorer full-screen
  if (explorerSource) {
    return (
      <PopulationExplorer
        populationId={`${explorerSource.provider}/${explorerSource.datasetId}`}
        onBack={() => { setExplorerSource(null); }}
        backLabel="Back to Sources"
        externalData={{
          preview: explorerPreviewHook.data,
          profile: explorerProfileHook.data,
        }}
      />
    );
  }

  return (
    <section aria-label="Data Fusion Workbench" className="space-y-3">
      <div className="rounded-lg border border-slate-200 bg-white p-3">
        <h2 className="text-sm font-semibold text-slate-900">Data Fusion Workbench</h2>
        <p className="text-xs text-slate-600">
          Browse institutional data sources, select datasets, choose a merge method, and generate
          a synthetic population for policy simulation.
        </p>
      </div>

      <WorkbenchStepper steps={STEPS} activeStep={activeStep} onStepSelect={(key) => setActiveStep(key as WorkbenchStep)} ariaLabel="Workbench steps" />

      <div className="space-y-3">
        {/* Step 1: Source Browser */}
        {activeStep === "sources" ? (
          <div className="space-y-2">
            <p className="text-xs text-slate-500">
              Select 2 or more datasets to merge into a synthetic population.{" "}
              <span className="font-medium">{selectedSources.length} selected.</span>
            </p>
            <DataSourceBrowser
              sources={sources}
              selectedIds={selectedSources}
              onToggleSource={handleToggleSource}
              onPreview={(provider, datasetId) => { setPreviewSource({ provider, datasetId }); }}
              onExplore={(provider, datasetId) => { setExplorerSource({ provider, datasetId }); }}
            />
          </div>
        ) : null}

        {/* Step 2: Variable Overlap */}
        {activeStep === "overlap" ? (
          <div className="space-y-2">
            {selectedSources.length >= 2 ? (
              <VariableOverlapView sources={sources} selectedSources={selectedSources} />
            ) : (
              <p className="text-xs text-slate-500">
                Select 2 or more datasets to see variable overlap.
              </p>
            )}
          </div>
        ) : null}

        {/* Step 3: Merge Method + Parameters */}
        {activeStep === "method" ? (
          <div className="space-y-3">
            <MergeMethodSelector
              methods={methods}
              selectedMethodId={selectedMethodId}
              onSelectMethod={setSelectedMethodId}
            />
            <MergeParametersPanel
              methodId={selectedMethodId}
              seed={seed}
              strataColumns={strataColumns}
              onSeedChange={setSeed}
              onStrataColumnsChange={setStrataColumns}
            />
          </div>
        ) : null}

        {/* Step 4: Generation Progress */}
        {activeStep === "generate" ? (
          <PopulationGenerationProgress
            loading={generating}
            result={result}
            error={genError}
            errorDetail={genErrorDetail}
          />
        ) : null}

        {/* Step 5: Preview + Validation */}
        {activeStep === "preview" && result ? (
          <div className="space-y-3">
            <PopulationPreview result={result} />
            {result.validation_result ? (
              <PopulationValidationPanel validation={result.validation_result} />
            ) : (
              <div className="rounded-lg border border-slate-200 bg-white p-3">
                <p className="text-xs text-slate-500">
                  No marginal validation was performed. Catalog marginals will be applied
                  automatically when the pipeline has marginals configured.
                </p>
              </div>
            )}
          </div>
        ) : null}

        {/* Navigation */}
        {!isLastStep ? (
          <div className="flex justify-between">
            <Button
              variant="outline"
              size="sm"
              onClick={goBack}
              disabled={!canGoBack}
            >
              <ChevronLeft className="h-4 w-4" />
              Back
            </Button>
            <Button
              size="sm"
              onClick={goNext}
              disabled={generating || !canProceed}
            >
              {activeStep === "method" ? "Generate Population" : "Next"}
              {activeStep !== "method" ? <ChevronRight className="h-4 w-4" /> : null}
            </Button>
          </div>
        ) : (
          <div className="flex justify-between">
            <Button variant="outline" size="sm" onClick={() => setActiveStep("method")}>
              <ChevronLeft className="h-4 w-4" />
              Adjust Parameters
            </Button>
            <Button
              size="sm"
              onClick={() => void handleGenerate()}
              disabled={generating}
            >
              Regenerate
            </Button>
          </div>
        )}
      </div>

      {/* Data source quick preview slide-over */}
      {previewSource && (
        <PopulationQuickPreview
          populationId={`${previewSource.provider}/${previewSource.datasetId}`}
          populationName={previewSource.datasetId.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
          onClose={() => { setPreviewSource(null); }}
          onOpenFullView={() => {
            setPreviewSource(null);
            setExplorerSource(previewSource);
          }}
          externalPreview={previewHook}
        />
      )}
    </section>
  );
}
