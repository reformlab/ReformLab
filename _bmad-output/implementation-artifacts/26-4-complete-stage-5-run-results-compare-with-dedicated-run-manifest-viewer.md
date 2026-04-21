# Story 26.4: Complete Stage 5 Run / Results / Compare with dedicated Run Manifest Viewer

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an analyst using the ReformLab workspace,
I want Stage 5 (Run / Results / Compare) to include a dedicated Run Manifest Viewer that shows per-run assumptions, mappings, lineage, hashes, versions, population reference, and runtime mode,
so that I can inspect the complete reproducibility metadata for any run, understand what assumptions and data sources were used, and trust that my results are documented and defensible.

## Acceptance Criteria

1. Given Stage 5 renders before any runs exist, then it shows a run queue empty state under Run / Results / Compare (with a "No runs yet" message and navigation to Scenario stage).
2. Given a completed run exists, when the analyst opens its manifest, then a dedicated manifest viewer shows assumptions, mappings, lineage (parent/child manifests), versions (engine, OpenFisca, adapter), hashes (data_hashes, output_hashes, integrity_hash), population reference (population_id, population_source), runtime mode, and reproducibility metadata (seeds, warnings, step_pipeline).
3. Given a comparison view is active, when a run is selected, then its manifest is reachable via a "View Manifest" button without leaving Stage 5 (opens manifest sub-view).
4. Given a manifest is incomplete or unavailable (e.g., cache miss, missing panel data), then the viewer shows a clear missing-metadata state rather than failing silently (explains that panel data was evicted and manifest is from metadata only).
5. Given existing results and comparison views render, then adding manifest access does not change their visible indicator semantics (charts, tables, and KPIs remain unchanged).
6. Given the manifest viewer renders, then it displays manifest data in organized sections: Overview (run_id, manifest_id, timestamps, status), Execution (seeds, step_pipeline, runtime_mode, population), Policy (assumptions, mappings), Data Provenance (data_hashes, output_hashes, integrity_hash), Lineage (parent_manifest_id, child_manifests), Evidence (evidence_assets, calibration_assets, validation_assets, evidence_summary), Warnings (warnings list).

## Tasks / Subtasks

- [ ] Add backend GET /api/results/{run_id}/manifest endpoint (AC: #2, #4)
  - [ ] Create new Pydantic response model `ManifestResponse` in `src/reformlab/server/models.py`
  - [ ] Add `get_manifest` route function in `src/reformlab/server/routes/results.py`
  - [ ] Load SimulationResult from cache or disk using `cache.get_or_load(run_id, store)`
  - [ ] Return 404 if run_id not found in store
  - [ ] Return 409 if SimulationResult is None (cache miss, no disk data) with helpful message
  - [ ] Extract all manifest fields from `sim_result.manifest` (RunManifest dataclass)
  - [ ] Include population metadata from ResultMetadata (population_id, population_source)
  - [ ] Include runtime_mode from ResultMetadata
  - [ ] Serialize nested structures (assumptions, mappings, evidence_assets, etc.) as JSON-compatible dicts
  - [ ] Add backend tests for manifest endpoint (success, 404, 409, field serialization)

- [ ] Add frontend API wrapper for manifest endpoint (AC: #2, #4)
  - [ ] Add `getManifest(runId: string): Promise<ManifestResponse>` function in `frontend/src/api/results.ts`
  - [ ] Add `ManifestResponse` type in `frontend/src/api/types.ts`
  - [ ] Include all manifest fields: manifest_id, created_at, engine_version, openfisca_version, adapter_version, scenario_version, data_hashes, output_hashes, seeds, policy, assumptions, mappings, warnings, step_pipeline, parent_manifest_id, child_manifests, exogenous_series, taste_parameters, evidence_assets, calibration_assets, validation_assets, evidence_summary, runtime_mode, population_id, population_source, integrity_hash

- [ ] Create RunManifestViewer component (AC: #2, #4, #6)
  - [ ] Create `frontend/src/components/results/RunManifestViewer.tsx`
  - [ ] Component props: `manifest: ManifestResponse`, `onClose?: () => void`, `loading?: boolean`, `error?: string`
  - [ ] Use collapsible sections (Shadcn Collapsible or similar) for organized display
  - [ ] Overview section: run_id (8 char), manifest_id, created_at, started_at, finished_at, status badge
  - [ ] Execution section: seeds (master + per-year), step_pipeline (ordered list), runtime_mode badge (live/replay), population_id + population_source badge
  - [ ] Policy section: assumptions (table with key/value/source/is_default), mappings (table with openfisca_name/project_name/direction)
  - [ ] Data Provenance section: data_hashes (key-value pairs), output_hashes, integrity_hash (truncate to 16 chars with tooltip)
  - [ ] Lineage section: parent_manifest_id (link to parent if exists), child_manifests (year → manifest_id mapping)
  - [ ] Evidence section: evidence_assets, calibration_assets, validation_assets, evidence_summary (render as nested key-value lists)
  - [ ] Warnings section: warnings array (render as bullet list with amber icon)
  - [ ] Empty state: "No manifest data available" message when manifest is null or error is set
  - [ ] Loading state: Skeleton loaders while fetching manifest

- [ ] Add "manifest" sub-view to Stage 5 routing (AC: #3)
  - [ ] Add "manifest" to SubView type in `frontend/src/types/workspace.ts`
  - [ ] Update STAGES array to include "manifest" in results.activeFor
  - [ ] Update App.tsx resultsContent to handle `activeSubView === "manifest"`
  - [ ] Pass runId from navigation or selected result to manifest viewer

- [ ] Add manifest viewer navigation entry points (AC: #2, #3, #5)
  - [ ] Add "View Manifest" button to ResultDetailView component (in header or actions)
  - [ ] Add manifest button to SimulationRunnerScreen ResultsListPanel row actions
  - [ ] Add manifest button to ComparisonDashboardScreen run selector items
  - [ ] All manifest buttons call `navigateTo("results", "manifest") with runId context

- [ ] Update help content for Stage 5 manifest viewer (AC: #2)
  - [ ] Add "results/manifest" entry to `frontend/src/components/help/help-content.ts`
  - [ ] Include tips about interpreting manifest fields, hash verification, lineage tracing
  - [ ] Add concepts: Run Manifest, Data Hash, Integrity Hash, Lineage, Assumptions, Mappings

- [ ] Add tests for RunManifestViewer (AC: #2, #4, #6)
  - [ ] Create `frontend/src/components/results/__tests__/RunManifestViewer.test.tsx`
  - [ ] Test rendering with complete manifest (all sections present)
  - [ ] Test rendering with partial manifest (missing optional fields)
  - [ ] Test loading state (skeleton renders)
  - [ ] Test error state (missing metadata message)
  - [ ] Test collapsible sections toggle behavior
  - [ ] Test hash truncation with tooltip
  - [ ] Test parent_manifest_id linking
  - [ ] Test warnings list rendering
  - [ ] Test empty assumptions/mappings arrays
  - [ ] Test population_source badge display (bundled/uploaded/generated)

- [ ] Add Stage 5 empty state component (AC: #1)
  - [ ] Create `frontend/src/components/results/RunQueueEmptyState.tsx` or integrate into existing stage layout
  - [ ] Show "No runs yet" message with illustration
  - [ ] Show "Go to Scenario stage to run a simulation" button
  - [ ] Include helpful tips about what Stage 5 will show after first run

- [ ] Non-regression: verify existing Stage 5 functionality preserved (AC: #5)
  - [ ] Verify ResultsOverviewScreen renders unchanged
  - [ ] Verify ComparisonDashboardScreen renders unchanged
  - [ ] Verify SimulationRunnerScreen renders unchanged
  - [ ] Verify BehavioralDecisionViewerScreen renders unchanged
  - [ ] Verify run queue list still shows past runs
  - [ ] Verify export buttons still work (CSV/Parquet)
  - [ ] Verify result detail tabs still work (Indicators, Data Summary, Manifest)
  - [ ] Verify comparison view still works (run selection, baseline, charts)

## Dev Notes

### Architecture Context

**UX-DR13 (from epics.md):** "Stage 5 (Run / Results / Compare) must include run queue, results, comparison sub-views, and a dedicated Run Manifest Viewer component for assumptions, mappings, lineage, and reproducibility metadata."

**Key Design Decision:** This story completes Stage 5 by adding a dedicated manifest viewer accessible from multiple entry points. The existing ResultDetailView already has a "Manifest" tab showing basic metadata; this new viewer provides comprehensive drill-down into all manifest fields.

**Current Stage 5 State:**
- Stage 5 exists as `results` stage key with sub-views: `runner`, `comparison`, `decisions`
- ResultsOverviewScreen shows distributional charts, summary stats, and Data & Export tabs
- ComparisonDashboardScreen shows multi-run side-by-side comparison
- SimulationRunnerScreen shows pre-run summary, progress, and post-run results list
- ResultDetailView has a Manifest tab showing basic metadata (run_id, manifest_id, scenario_id, adapter_version, seed, timestamps)

**What This Story Adds:**
- Backend endpoint: `GET /api/results/{run_id}/manifest` returning full RunManifest data
- Frontend component: `RunManifestViewer` with organized, collapsible sections
- New sub-view: `manifest` under Stage 5
- Navigation entry points: "View Manifest" buttons in result lists, detail views, comparison selector

### Backend Implementation

**File: `src/reformlab/server/models.py`**

Add `ManifestResponse` Pydantic model:

```python
class ManifestResponse(BaseModel):
    """Full run manifest response for Stage 5 manifest viewer — Story 26.4."""
    # Core identity
    manifest_id: str
    created_at: str
    # Version fields
    engine_version: str
    openfisca_version: str
    adapter_version: str
    scenario_version: str
    # Hashes
    data_hashes: dict[str, str] = {}
    output_hashes: dict[str, str] = {}
    integrity_hash: str = ""
    # Execution metadata
    seeds: dict[str, int] = {}
    policy: dict[str, Any] = {}
    assumptions: list[dict[str, Any]] = []
    mappings: list[dict[str, Any]] = []
    warnings: list[str] = []
    step_pipeline: list[str] = []
    # Lineage
    parent_manifest_id: str = ""
    child_manifests: dict[int, str] = {}
    # Optional fields (Story 21.6, 21.7, 21.8, 23.1, 23.5)
    exogenous_series: list[str] = []
    taste_parameters: dict[str, Any] = {}
    evidence_assets: list[dict[str, Any]] = []
    calibration_assets: list[dict[str, Any]] = []
    validation_assets: list[dict[str, Any]] = []
    evidence_summary: dict[str, Any] = {}
    runtime_mode: Literal["live", "replay"] = "live"
    population_id: str = ""
    population_source: Literal["bundled", "uploaded", "generated", ""] = ""
```

**File: `src/reformlab/server/routes/results.py`**

Add manifest endpoint:

```python
# ---------------------------------------------------------------------------
# GET /api/results/{run_id}/manifest — Story 26.4
# ---------------------------------------------------------------------------


@router.get("/{run_id}/manifest", response_model=ManifestResponse)
async def get_manifest(
    run_id: str,
    cache: ResultCache = Depends(get_result_cache),
    store: ResultStore = Depends(get_result_store),
) -> ManifestResponse:
    """Return the full RunManifest for a single simulation result.

    Returns 404 if run_id not found in persistent store.
    Returns 409 if SimulationResult is not available (cache miss, no disk data).

    The manifest includes all assumptions, mappings, hashes, lineage, and
    reproducibility metadata needed for the Stage 5 Run Manifest Viewer.
    """
    # Verify run exists in persistent store
    try:
        meta = store.get_metadata(run_id)
    except ResultNotFound:
        raise HTTPException(
            status_code=404,
            detail={
                "what": f"Result not found: {run_id!r}",
                "why": "No metadata file exists for this run ID",
                "fix": "Check the run ID or re-run the simulation",
            },
        )
    except ResultStoreError:
        raise HTTPException(
            status_code=400,
            detail={
                "what": f"Invalid run_id: {run_id!r}",
                "why": "run_id contains disallowed characters",
                "fix": "Use a valid run ID obtained from POST /api/runs",
            },
        )

    # Load SimulationResult (from cache or disk)
    sim_result = cache.get_or_load(run_id, store)
    if sim_result is None:
        raise HTTPException(
            status_code=409,
            detail={
                "what": "Full manifest data is not available",
                "why": "The simulation result has been evicted from the in-memory cache and panel.parquet is missing",
                "fix": "Re-run the simulation to access the full manifest",
            },
        )

    # Extract manifest from SimulationResult
    manifest = sim_result.manifest

    # Convert RunManifest dataclass to ManifestResponse Pydantic model
    # RunManifest uses tuples for exogenous_series; convert to list
    # RunManifest uses frozen dataclasses; convert to dicts for JSON serialization
    return ManifestResponse(
        manifest_id=manifest.manifest_id,
        created_at=manifest.created_at,
        engine_version=manifest.engine_version,
        openfisca_version=manifest.openfisca_version,
        adapter_version=manifest.adapter_version,
        scenario_version=manifest.scenario_version,
        data_hashes=manifest.data_hashes,
        output_hashes=manifest.output_hashes,
        integrity_hash=manifest.integrity_hash,
        seeds=manifest.seeds,
        policy=manifest.policy,
        assumptions=[dict(a) for a in manifest.assumptions],
        mappings=[dict(m) for m in manifest.mappings],
        warnings=list(manifest.warnings),
        step_pipeline=list(manifest.step_pipeline),
        parent_manifest_id=manifest.parent_manifest_id,
        child_manifests=dict(manifest.child_manifests),
        exogenous_series=list(manifest.exogenous_series),
        taste_parameters=dict(manifest.taste_parameters),
        evidence_assets=[dict(e) for e in manifest.evidence_assets],
        calibration_assets=[dict(c) for c in manifest.calibration_assets],
        validation_assets=[dict(v) for v in manifest.validation_assets],
        evidence_summary=dict(manifest.evidence_summary),
        runtime_mode=cast(Literal["live", "replay"], manifest.runtime_mode),
        population_id=manifest.population_id,
        population_source=manifest.population_source,
    )
```

### Frontend Implementation

**File: `frontend/src/types/workspace.ts`**

Add "manifest" to SubView type:

```typescript
export type SubView =
  | "data-fusion"
  | "population-explorer"
  | "comparison"
  | "decisions"
  | "runner"
  | "manifest";  // Story 26.4
```

Update STAGES array:

```typescript
export const STAGES = [
  { key: "policies", label: "Policies", activeFor: ["policies"] },
  { key: "population", label: "Population", activeFor: ["population", "data-fusion", "population-explorer"] },
  { key: "investment-decisions", label: "Investment Decisions", activeFor: ["investment-decisions"] },
  { key: "scenario", label: "Scenario", activeFor: ["scenario"] },
  { key: "results", label: "Run / Results / Compare", activeFor: ["results", "comparison", "decisions", "runner", "manifest"] },  // Story 26.4: added "manifest"
];
```

**File: `frontend/src/api/types.ts`**

Add ManifestResponse type:

```typescript
// Story 26.4: Full run manifest response
export interface ManifestResponse {
  // Core identity
  manifest_id: string;
  created_at: string;
  // Version fields
  engine_version: string;
  openfisca_version: string;
  adapter_version: string;
  scenario_version: string;
  // Hashes
  data_hashes: Record<string, string>;
  output_hashes: Record<string, string>;
  integrity_hash: string;
  // Execution metadata
  seeds: Record<string, number>;
  policy: Record<string, unknown>;
  assumptions: Array<{ key: string; value: unknown; source: string; is_default: boolean }>;
  mappings: Array<{ openfisca_name: string; project_name: string; direction: string; source_file?: string; transform?: string }>;
  warnings: string[];
  step_pipeline: string[];
  // Lineage
  parent_manifest_id: string;
  child_manifests: Record<number, string>;
  // Optional fields (Story 21.6, 21.7, 21.8, 23.1, 23.5)
  exogenous_series: string[];
  taste_parameters: Record<string, unknown>;
  evidence_assets: Array<Record<string, unknown>>;
  calibration_assets: Array<Record<string, unknown>>;
  validation_assets: Array<Record<string, unknown>>;
  evidence_summary: Record<string, unknown>;
  runtime_mode: "live" | "replay";
  population_id: string;
  population_source: "bundled" | "uploaded" | "generated" | "";
}
```

**File: `frontend/src/api/results.ts`**

Add getManifest function:

```typescript
/** Get the full manifest for a single simulation result — Story 26.4. */
export async function getManifest(runId: string): Promise<ManifestResponse> {
  return apiFetch<ManifestResponse>(`/api/results/${runId}/manifest`);
}
```

**File: `frontend/src/components/results/RunManifestViewer.tsx`** (NEW)

```typescript
// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Run Manifest Viewer — Story 26.4, AC-2, AC-4, AC-6.
 *
 * Comprehensive display of run reproducibility metadata organized into
 * collapsible sections: Overview, Execution, Policy, Data Provenance,
 * Lineage, Evidence, Warnings.
 */

import { FileText, Hash, AlertTriangle, ChevronDown, ChevronRight } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Skeleton } from "@/components/ui/skeleton";
import type { ManifestResponse } from "@/api/types";

// ============================================================================
// Types
// ============================================================================

export interface RunManifestViewerProps {
  manifest: ManifestResponse | null;
  loading?: boolean;
  error?: string | null;
  onClose?: () => void;
}

// ============================================================================
// Helpers
// ============================================================================

function formatTs(ts: string): string {
  try {
    return new Date(ts).toLocaleString(undefined, {
      year: "numeric", month: "short", day: "2-digit",
      hour: "2-digit", minute: "2-digit", second: "2-digit",
    });
  } catch {
    return ts;
  }
}

function truncateHash(hash: string): string {
  return hash.length > 16 ? `${hash.slice(0, 8)}...${hash.slice(-8)}` : hash;
}

function runtimeModeBadge(mode: "live" | "replay" | "") {
  if (!mode) return null;
  const variant = mode === "live" ? "success" : "warning";
  const label = mode === "live" ? "Live OpenFisca" : "Replay";
  return <Badge variant={variant} className="text-xs">{label}</Badge>;
}

function populationSourceBadge(source: "bundled" | "uploaded" | "generated" | "") {
  if (!source) return null;
  const colors = {
    bundled: "bg-blue-100 text-blue-800 border-blue-200",
    uploaded: "bg-amber-100 text-amber-800 border-amber-200",
    generated: "bg-purple-100 text-purple-800 border-purple-200",
  };
  return (
    <Badge variant="outline" className={`text-xs ${colors[source] || ""}`}>
      {source}
    </Badge>
  );
}

// ============================================================================
// Section Components
// ============================================================================

interface ManifestSectionProps {
  title: string;
  icon: React.ReactNode;
  defaultOpen?: boolean;
  children: React.ReactNode;
}

function ManifestSection({ title, icon, defaultOpen = true, children }: ManifestSectionProps) {
  const [open, setOpen] = React.useState(defaultOpen);

  return (
    <Collapsible open={open} onOpenChange={setOpen} className="border border-slate-200 rounded-lg bg-white">
      <CollapsibleTrigger className="flex items-center justify-between w-full px-3 py-2 hover:bg-slate-50 transition-colors">
        <div className="flex items-center gap-2">
          {icon}
          <span className="text-sm font-semibold text-slate-900">{title}</span>
        </div>
        {open ? <ChevronDown className="h-4 w-4 text-slate-400" /> : <ChevronRight className="h-4 w-4 text-slate-400" />}
      </CollapsibleTrigger>
      <CollapsibleContent className="px-3 pb-3">
        {children}
      </CollapsibleContent>
    </Collapsible>
  );
}

// ============================================================================
// RunManifestViewer
// ============================================================================

export function RunManifestViewer({ manifest, loading, error, onClose }: RunManifestViewerProps) {
  if (loading) {
    return (
      <section className="space-y-3" aria-label="Loading manifest">
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-32 w-full" />
      </section>
    );
  }

  if (error || !manifest) {
    return (
      <section className="rounded-lg border border-amber-200 bg-amber-50 p-4" aria-label="Manifest error">
        <AlertTriangle className="h-6 w-6 text-amber-600 mb-2" />
        <p className="text-sm font-semibold text-amber-900">Manifest data unavailable</p>
        <p className="text-xs text-amber-700 mt-1">
          {error || "The full manifest could not be loaded. The result may have been evicted from cache."}
        </p>
        {onClose && (
          <Button variant="outline" size="sm" className="mt-3" onClick={onClose}>
            Close
          </Button>
        )}
      </section>
    );
  }

  return (
    <section className="space-y-3" aria-label="Run manifest viewer">
      {/* Header with close button */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-slate-900">Run Manifest</h2>
          <p className="text-xs text-slate-500 data-mono">{manifest.manifest_id.slice(0, 8)}</p>
        </div>
        {onClose && (
          <Button variant="outline" size="sm" onClick={onClose}>
            Close
          </Button>
        )}
      </div>

      {/* Overview Section */}
      <ManifestSection title="Overview" icon={<FileText className="h-4 w-4 text-slate-500" />} defaultOpen={true}>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
          <span className="text-slate-500">Run ID</span>
          <span className="data-mono font-medium text-slate-800">{manifest.manifest_id.slice(0, 16)}...</span>

          <span className="text-slate-500">Created</span>
          <span className="font-medium text-slate-800">{formatTs(manifest.created_at)}</span>

          <span className="text-slate-500">Engine Version</span>
          <span className="data-mono font-medium text-slate-800">{manifest.engine_version}</span>

          <span className="text-slate-500">OpenFisca Version</span>
          <span className="data-mono font-medium text-slate-800">{manifest.openfisca_version}</span>

          <span className="text-slate-500">Adapter Version</span>
          <span className="data-mono font-medium text-slate-800">{manifest.adapter_version}</span>

          <span className="text-slate-500">Runtime Mode</span>
          <div className="flex items-center gap-2">
            {runtimeModeBadge(manifest.runtime_mode)}
            {populationSourceBadge(manifest.population_source)}
          </div>
        </div>
      </ManifestSection>

      {/* Execution Section */}
      <ManifestSection title="Execution" icon={<FileText className="h-4 w-4 text-slate-500" />} defaultOpen={false}>
        <div className="space-y-3">
          {/* Seeds */}
          {Object.keys(manifest.seeds).length > 0 && (
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Seeds</p>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                {Object.entries(manifest.seeds).map(([key, value]) => (
                  <React.Fragment key={key}>
                    <dt className="text-slate-500">{key}</dt>
                    <dd className="data-mono font-medium text-slate-800">{value}</dd>
                  </React.Fragment>
                ))}
              </dl>
            </div>
          )}

          {/* Step Pipeline */}
          {manifest.step_pipeline.length > 0 && (
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Step Pipeline</p>
              <ol className="text-xs text-slate-700 space-y-0.5">
                {manifest.step_pipeline.map((step, i) => (
                  <li key={i} className="flex items-center gap-2">
                    <span className="text-slate-400">{i + 1}.</span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Population Reference */}
          {manifest.population_id && (
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Population</p>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                <dt className="text-slate-500">Population ID</dt>
                <dd className="data-mono font-medium text-slate-800">{manifest.population_id}</dd>
                {manifest.population_source && (
                  <>
                    <dt className="text-slate-500">Source</dt>
                    <dd className="font-medium text-slate-800">{manifest.population_source}</dd>
                  </>
                )}
              </dl>
            </div>
          )}
        </div>
      </ManifestSection>

      {/* Policy Section */}
      <ManifestSection title="Policy & Assumptions" icon={<FileText className="h-4 w-4 text-slate-500" />} defaultOpen={false}>
        <div className="space-y-3">
          {/* Assumptions */}
          {manifest.assumptions.length > 0 && (
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Assumptions</p>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-slate-200">
                      <th className="text-left py-1 text-slate-500">Key</th>
                      <th className="text-left py-1 text-slate-500">Value</th>
                      <th className="text-left py-1 text-slate-500">Source</th>
                      <th className="text-left py-1 text-slate-500">Default</th>
                    </tr>
                  </thead>
                  <tbody>
                    {manifest.assumptions.map((a, i) => (
                      <tr key={i} className="border-b border-slate-100">
                        <td className="py-1 text-slate-700">{a.key}</td>
                        <td className="py-1 data-mono text-slate-800">{JSON.stringify(a.value)}</td>
                        <td className="py-1 text-slate-600">{a.source}</td>
                        <td className="py-1 text-slate-600">{a.is_default ? "Yes" : "No"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Mappings */}
          {manifest.mappings.length > 0 && (
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Variable Mappings</p>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-slate-200">
                      <th className="text-left py-1 text-slate-500">OpenFisca Name</th>
                      <th className="text-left py-1 text-slate-500">Project Name</th>
                      <th className="text-left py-1 text-slate-500">Direction</th>
                    </tr>
                  </thead>
                  <tbody>
                    {manifest.mappings.map((m, i) => (
                      <tr key={i} className="border-b border-slate-100">
                        <td className="py-1 data-mono text-slate-800">{m.openfisca_name}</td>
                        <td className="py-1 text-slate-700">{m.project_name}</td>
                        <td className="py-1 text-slate-600">{m.direction}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </ManifestSection>

      {/* Data Provenance Section */}
      <ManifestSection title="Data Provenance" icon={<Hash className="h-4 w-4 text-slate-500" />} defaultOpen={false}>
        <div className="space-y-3">
          {/* Data Hashes */}
          {Object.keys(manifest.data_hashes).length > 0 && (
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Input Hashes (SHA-256)</p>
              <dl className="grid grid-cols-1 gap-1 text-xs">
                {Object.entries(manifest.data_hashes).map(([key, hash]) => (
                  <div key={key}>
                    <dt className="text-slate-500">{key}</dt>
                    <dd className="data-mono text-slate-800 break-all" title={hash}>{truncateHash(hash)}</dd>
                  </div>
                ))}
              </dl>
            </div>
          )}

          {/* Output Hashes */}
          {Object.keys(manifest.output_hashes).length > 0 && (
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Output Hashes (SHA-256)</p>
              <dl className="grid grid-cols-1 gap-1 text-xs">
                {Object.entries(manifest.output_hashes).map(([key, hash]) => (
                  <div key={key}>
                    <dt className="text-slate-500">{key}</dt>
                    <dd className="data-mono text-slate-800 break-all" title={hash}>{truncateHash(hash)}</dd>
                  </div>
                ))}
              </dl>
            </div>
          )}

          {/* Integrity Hash */}
          {manifest.integrity_hash && (
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Integrity Hash</p>
              <p className="data-mono text-xs text-slate-800 break-all" title={manifest.integrity_hash}>
                {truncateHash(manifest.integrity_hash)}
              </p>
            </div>
          )}
        </div>
      </ManifestSection>

      {/* Lineage Section */}
      <ManifestSection title="Lineage" icon={<FileText className="h-4 w-4 text-slate-500" />} defaultOpen={false}>
        <div className="space-y-3">
          {/* Parent Manifest */}
          {manifest.parent_manifest_id && (
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Parent Manifest</p>
              <p className="data-mono text-xs text-slate-800">{manifest.parent_manifest_id}</p>
            </div>
          )}

          {/* Child Manifests */}
          {Object.keys(manifest.child_manifests).length > 0 && (
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Child Manifests (by year)</p>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                {Object.entries(manifest.child_manifests).map(([year, id]) => (
                  <React.Fragment key={year}>
                    <dt className="text-slate-500">Year {year}</dt>
                    <dd className="data-mono text-slate-800">{id}</dd>
                  </React.Fragment>
                ))}
              </dl>
            </div>
          )}

          {!manifest.parent_manifest_id && Object.keys(manifest.child_manifests).length === 0 && (
            <p className="text-xs text-slate-400">No lineage information available.</p>
          )}
        </div>
      </ManifestSection>

      {/* Evidence Section */}
      {(manifest.evidence_assets.length > 0 || manifest.calibration_assets.length > 0 || manifest.validation_assets.length > 0) && (
        <ManifestSection title="Evidence & Assets" icon={<FileText className="h-4 w-4 text-slate-500" />} defaultOpen={false}>
          <div className="space-y-3">
            {manifest.evidence_assets.length > 0 && (
              <div>
                <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Evidence Assets</p>
                <ul className="text-xs text-slate-700 space-y-0.5">
                  {manifest.evidence_assets.map((asset, i) => (
                    <li key={i} className="data-mono">{JSON.stringify(asset)}</li>
                  ))}
                </ul>
              </div>
            )}
            {manifest.calibration_assets.length > 0 && (
              <div>
                <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Calibration Assets</p>
                <ul className="text-xs text-slate-700 space-y-0.5">
                  {manifest.calibration_assets.map((asset, i) => (
                    <li key={i} className="data-mono">{JSON.stringify(asset)}</li>
                  ))}
                </ul>
              </div>
            )}
            {manifest.validation_assets.length > 0 && (
              <div>
                <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Validation Assets</p>
                <ul className="text-xs text-slate-700 space-y-0.5">
                  {manifest.validation_assets.map((asset, i) => (
                    <li key={i} className="data-mono">{JSON.stringify(asset)}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </ManifestSection>
      )}

      {/* Warnings Section */}
      {manifest.warnings.length > 0 && (
        <ManifestSection title="Warnings" icon={<AlertTriangle className="h-4 w-4 text-amber-500" />} defaultOpen={true}>
          <ul className="text-xs text-slate-700 space-y-1">
            {manifest.warnings.map((warning, i) => (
              <li key={i} className="flex items-start gap-2">
                <AlertTriangle className="h-3 w-3 text-amber-500 mt-0.5 shrink-0" />
                <span>{warning}</span>
              </li>
            ))}
          </ul>
        </ManifestSection>
      )}
    </section>
  );
}
```

**File: `frontend/src/App.tsx`**

Add manifest sub-view to resultsContent:

```typescript
// Stage 5 sub-view content
const resultsContent = (() => {
  // ... existing sub-views (runner, comparison, decisions) ...

  // Story 26.4: Manifest viewer sub-view
  if (activeSubView === "manifest") {
    const manifestRunId = /* derive from URL hash or selected result */ runResult?.run_id;
    return (
      <RunManifestViewerSubView
        runId={manifestRunId}
        onBack={() => { navigateTo("results"); }}
      />
    );
  }

  // Default results overview
  return (
    <ResultsOverviewScreen
      decileData={decileData}
      runResult={runResult}
      reformLabel={selectedScenario?.template_name ?? "Reform"}
      onCompare={() => { navigateTo("results", "comparison"); }}
      onViewDecisions={() => { navigateTo("results", "decisions"); }}
      onViewManifest={() => { navigateTo("results", "manifest"); }}
      onRunAgain={handleStartRun}
      onExportCsv={handleExportCsv}
      onExportParquet={handleExportParquet}
    />
  );
})();
```

**File: `frontend/src/components/help/help-content.ts`**

Add manifest help entry:

```typescript
"results/manifest": {
  title: "Run Manifest Viewer",
  summary: "Inspect the complete reproducibility metadata for a simulation run, including assumptions, mappings, hashes, versions, and lineage.",
  tips: [
    "The manifest documents every parameter, data source, assumption, and execution configuration used in the run.",
    "Hashes (SHA-256) allow you to verify data integrity and reproduce the exact same results.",
    "Lineage information shows parent-child relationships between runs for multi-year scenarios.",
    "Assumptions and mappings reveal how policy parameters translate to OpenFisca variables.",
    "Warnings highlight potential issues or limitations discovered during execution.",
    "Use the Evidence section to understand what data sources underpin your results.",
  ],
  concepts: [
    { term: "Run Manifest", definition: "An immutable document recording all parameters, data sources, assumptions, hashes, versions, and execution metadata for a simulation run. Enables reproducibility and audit." },
    { term: "Data Hash", definition: "SHA-256 hash of input data files, ensuring data integrity and detecting changes between runs." },
    { term: "Integrity Hash", definition: "SHA-256 hash of the entire manifest content, used to detect tampering or corruption of stored manifests." },
    { term: "Lineage", definition: "Parent-child relationships between manifests, showing how multi-year scenarios build on previous years' results." },
    { term: "Assumptions", definition: "Parameter values and configuration choices made during scenario setup, distinguished from default values." },
    { term: "Mappings", definition: "Variable name translations between project schema and OpenFisca variables, with direction (input/output/both)." },
  ],
},
```

### Testing Strategy

**Backend Tests:** `tests/server/results/test_manifest_endpoint.py` (NEW)

Required test coverage for Story 26.4:
- Test GET /api/results/{run_id}/manifest returns 200 with full manifest
- Test 404 response when run_id not found
- Test 409 response when SimulationResult is None (cache miss, no disk)
- Test all manifest fields are correctly serialized (assumptions, mappings, hashes, etc.)
- Test exogenous_series tuple converted to list
- Test nested structures converted to JSON-compatible dicts
- Test population_id and population_source included
- Test runtime_mode included

**Frontend Component Tests:** `frontend/src/components/results/__tests__/RunManifestViewer.test.tsx` (NEW)

Required test coverage:
- Test rendering with complete manifest (all sections present)
- Test Overview section renders run_id, manifest_id, timestamps, versions
- Test Execution section renders seeds, step_pipeline, population info
- Test Policy section renders assumptions table, mappings table
- Test Data Provenance section renders data_hashes, output_hashes, integrity_hash
- Test Lineage section renders parent_manifest_id, child_manifests
- Test Evidence section renders evidence_assets, calibration_assets, validation_assets
- Test Warnings section renders warnings list with icon
- Test rendering with partial manifest (empty assumptions, empty mappings)
- Test hash truncation with full hash in title attribute
- Test collapsible sections toggle open/close
- Test loading state renders Skeleton components
- Test error state renders friendly message
- Test onClose callback called when Close button clicked
- Test runtime mode badge (Live OpenFisca vs Replay)
- Test population source badge (bundled/uploaded/generated)

**Frontend Integration Tests:** `frontend/src/components/__tests__/App.test.tsx` (MODIFY)

Added test coverage:
- Test navigating to "results/manifest" sub-view
- Test RunManifestViewerSubView receives correct runId
- Test manifest navigation entry point from ResultsOverviewScreen
- Test manifest navigation entry point from SimulationRunnerScreen
- Test manifest navigation entry point from ComparisonDashboardScreen
- Test back button returns to default results view

### Project Structure Notes

**Frontend Files to Create:**
- `frontend/src/components/results/RunManifestViewer.tsx` — Main manifest viewer component
- `frontend/src/components/results/RunManifestViewerSubView.tsx` — Sub-view wrapper for App.tsx integration
- `frontend/src/components/results/__tests__/RunManifestViewer.test.tsx` — Component tests

**Frontend Files to Modify:**
- `frontend/src/types/workspace.ts` — Add "manifest" to SubView type, update STAGES array
- `frontend/src/api/types.ts` — Add ManifestResponse type
- `frontend/src/api/results.ts` — Add getManifest() function
- `frontend/src/App.tsx` — Add manifest sub-view to resultsContent, add manifest navigation buttons
- `frontend/src/components/screens/ResultsOverviewScreen.tsx` — Add "View Manifest" button
- `frontend/src/components/screens/SimulationRunnerScreen.tsx` — Add "View Manifest" button to result rows
- `frontend/src/components/screens/ComparisonDashboardScreen.tsx` — Add "View Manifest" button to run selector
- `frontend/src/components/help/help-content.ts` — Add "results/manifest" help entry

**Backend Files to Modify:**
- `src/reformlab/server/models.py` — Add ManifestResponse Pydantic model
- `src/reformlab/server/routes/results.py` — Add GET /api/results/{run_id}/manifest endpoint

**Backend Test Files to Create:**
- `tests/server/results/test_manifest_endpoint.py` — Manifest endpoint tests

### Implementation Order Recommendation

1. **Phase 1: Backend Foundation** (AC: #2, #4)
   - Add ManifestResponse model to models.py
   - Add GET /api/results/{run_id}/manifest endpoint
   - Add backend tests for manifest endpoint
   - Verify endpoint returns correct data for existing runs

2. **Phase 2: Frontend API and Types** (AC: #2, #4)
   - Add ManifestResponse type to api/types.ts
   - Add getManifest() function to api/results.ts
   - Add "manifest" to SubView type in workspace.ts
   - Update STAGES array to include "manifest"

3. **Phase 3: RunManifestViewer Component** (AC: #2, #4, #6)
   - Create RunManifestViewer component with all sections
   - Add collapsible sections for organized display
   - Implement loading, error, and empty states
   - Add component tests

4. **Phase 4: App Integration** (AC: #3)
   - Create RunManifestViewerSubView wrapper
   - Add manifest sub-view handling to App.tsx resultsContent
   - Add manifest navigation entry points (buttons in existing screens)
   - Add integration tests

5. **Phase 5: Help Content** (AC: #2)
   - Add "results/manifest" help entry
   - Add tips and concepts for manifest interpretation

6. **Phase 6: Empty State** (AC: #1)
   - Add run queue empty state component or integrate into existing layout
   - Verify empty state shows navigation to Scenario stage

7. **Phase 7: Integration and Regression** (Validation)
   - Test full manifest viewer flow from multiple entry points
   - Verify existing results screens still render unchanged
   - Verify comparison view still works
   - Non-regression testing for all existing Stage 5 functionality

### Key Implementation Decisions

**Manifest API Design:**
- New GET /api/results/{run_id}/manifest endpoint (separate from GET /api/results/{run_id})
- Returns 409 when SimulationResult is None (cache miss + no disk data) with helpful message
- Returns full RunManifest data including all optional fields
- Converts frozen dataclasses and tuples to JSON-compatible structures

**Frontend Component Structure:**
- RunManifestViewer is a pure display component (receives manifest prop)
- RunManifestViewerSubView handles data fetching and error states
- Collapsible sections organized by theme (Overview, Execution, Policy, Data Provenance, Lineage, Evidence, Warnings)
- Hashes truncated to 16 chars with full hash in title attribute for readability

**Navigation Pattern:**
- Manifest viewer is a sub-view under Stage 5 (not a separate stage)
- Entry points: "View Manifest" buttons in ResultsOverviewScreen, SimulationRunnerScreen, ComparisonDashboardScreen
- Back button returns to default results view
- Hash routing: `#results/manifest` with runId context from selected result

**Empty State Design:**
- Shows "No runs yet" message when results array is empty
- Navigation button to Scenario stage to encourage first run
- Helpful tips about what Stage 5 will show after first run

**Non-Regression Strategy:**
- All existing Stage 5 screens remain unchanged
- Manifest viewer is additive only (doesn't modify existing components)
- ResultDetailView's existing Manifest tab remains for basic metadata
- New viewer provides comprehensive drill-down beyond what Manifest tab shows

### Out of Scope

To avoid scope creep and conflicts with future stories:
- **Manifest editing** — manifests are immutable; no editing allowed
- **Manifest comparison/diff** — comparing two manifests side-by-side is future work
- **Manifest search/filter** — searching within manifest fields is future work
- **Manifest export** — downloading manifest as JSON is future work
- **Manifest visualization** — graphical lineage trees or hash visualizations are future work
- **Backend manifest storage changes** — no changes to ResultStore or manifest persistence
- **Live manifest updates** — manifests are write-only after run completion

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic-26] - Epic 26 requirements
- [Source: _bmad-output/planning-artifacts/epics.md#Story-26.4] - Story 26.4 requirements and AC
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md] - UX design specification (Stage 5, Run Manifest Viewer)
- [Source: src/reformlab/governance/manifest.py] - RunManifest dataclass definition
- [Source: src/reformlab/server/routes/results.py] - Existing results endpoints
- [Source: frontend/src/components/simulation/ResultDetailView.tsx] - Existing manifest tab (basic metadata)
- [Source: frontend/src/types/workspace.ts] - StageKey, SubView, STAGES types
- [Source: frontend/src/api/types.ts] - ResultDetailResponse type
- [Source: frontend/src/components/screens/ResultsOverviewScreen.tsx] - Results overview screen
- [Source: frontend/src/components/screens/ComparisonDashboardScreen.tsx] - Comparison dashboard

## Dev Agent Record

### Agent Model Used

claude-opus-4-6

### Debug Log References

None - This is the initial story creation.

### Completion Notes List

Story 26.4 created with comprehensive developer context:

**Context Sources Analyzed:**
- Epic 26 requirements and Story 26.4 acceptance criteria
- Backend RunManifest dataclass (governance/manifest.py) — comprehensive manifest schema
- Backend results routes (server/routes/results.py) — existing result endpoints
- Frontend ResultDetailView (simulation/ResultDetailView.tsx) — existing manifest tab
- Frontend types (types/workspace.ts) — StageKey, SubView, STAGES definitions
- Frontend screens (ResultsOverviewScreen, ComparisonDashboardScreen, SimulationRunnerScreen) — existing Stage 5 screens
- App.tsx routing structure — current Stage 5 sub-view handling

**Key Design Decisions Documented:**
- New backend GET /api/results/{run_id}/manifest endpoint for full manifest data
- RunManifestViewer component with collapsible sections organized by theme
- Manifest viewer as Stage 5 sub-view (not separate stage)
- Multiple navigation entry points (result rows, detail view, comparison selector)
- Clear empty state for no runs, helpful error states for missing data
- Hash truncation for readability with full hash in tooltip

**Testing Strategy:**
- Backend endpoint tests (success, 404, 409, field serialization)
- Frontend component tests (all sections, loading, error, empty states)
- Integration tests (navigation, back button, entry points)

**Implementation Order:**
1. Backend foundation (endpoint + tests)
2. Frontend API and types
3. RunManifestViewer component + tests
4. App integration (sub-view + entry points)
5. Help content
6. Empty state
7. Integration and regression testing

Status set to: ready-for-dev
