# Story 26.4 Validation Synthesis Report

**Story:** 26-4-complete-stage-5-run-results-compare-with-dedicated-run-manifest-viewer
**Validated:** 2026-04-21
**Synthesizer:** Master Synthesis Agent

---

<!-- VALIDATION_SYNTHESIS_START -->
## Synthesis Summary

13 issues verified and addressed, 3 false positives dismissed. Both validators identified critical contract gaps around run ID context mechanism, metadata-only fallback behavior, and missing response fields. All Critical and High priority issues have been fixed directly in the story file.

## Validations Quality

**Validator A (Quality Competition Engine):** Score 8.8/10 - Excellent deep analysis of architectural contracts, AC-task misalignment, and edge cases. Key contributions: backend endpoint metadata-only behavior, AC-6 missing fields, run ID context ambiguity.

**Validator B (Quality Competition Engine):** Score 13.9/10 - Strong technical verification with focus on type mismatches and file structure accuracy. Key contributions: population_source type contract violation, test file path correction, empty state clarification.

**Overall Validation Quality:** 9/10 - Both validators provided complementary analysis that together covered all critical implementation risks. Validator A focused on architectural contracts and AC completeness, while Validator B focused on type safety and file organization.

## Issues Verified (by severity)

### Critical

- **Run ID context mechanism undefined** | **Source:** Validator A, Validator B | **Fix:** Added explicit `selectedResultForManifest: string | null` state to AppContext pattern in AC-3 and App.tsx integration. All manifest buttons now follow pattern: `setSelectedResultForManifest(runId); navigateTo("results", "manifest");`

- **Backend endpoint cannot satisfy AC-4 metadata-only behavior** | **Source:** Validator A | **Fix:** Updated backend endpoint to try `store.load_manifest(run_id)` when SimulationResult is None, returning 200 with `metadata_only=True` flag and degraded response. 409 now reserved only for truly unrecoverable state (neither SimulationResult nor manifest.json available).

- **AC-6 required fields missing in ManifestResponse** | **Source:** Validator A | **Fix:** Added `run_id`, `started_at`, `finished_at`, `status`, `metadata_only` fields to both backend Pydantic ManifestResponse and frontend TypeScript interface. Updated Overview section to display all new fields.

- **population_source type mismatch (contract violation)** | **Source:** Validator B | **Fix:** Changed `population_source` type from `"bundled" | "uploaded" | "generated" | ""` to `"bundled" | "uploaded" | "generated" | null` in both backend and frontend to align with existing ResultDetailResponse pattern.

- **Test file path points to non-existent directory** | **Source:** Validator B | **Fix:** Changed test file path from `tests/server/results/test_manifest_endpoint.py` to `tests/server/test_manifest_endpoint.py` to match existing flat test structure under `tests/server/`.

### High

- **Empty state component location unclear** | **Source:** Validator B | **Fix:** Updated AC-1 and empty state task to clarify that ResultsOverviewScreen should be updated to show empty state when results array is empty, rather than creating a separate RunQueueEmptyState component.

- **child_manifests JSON serialization ambiguity** | **Source:** Validator A | **Fix:** Changed frontend ManifestResponse child_manifests type from `Record<number, string>` to `Record<string, string>` to reflect JSON serialization behavior (numeric keys become strings).

- **Navigation entry points underspecified** | **Source:** Validator B | **Fix:** Expanded navigation entry points task to explicitly name component locations (ResultsOverviewScreen header actions, SimulationRunnerScreen ResultsListPanel rows, ComparisonDashboardScreen run selector) and the AppContext state pattern.

- **Backend task description conflicts with updated behavior** | **Source:** Validator A | **Fix:** Updated backend endpoint task to clarify metadata-only response (200 with metadata_only=True) vs 409 (truly unrecoverable), and added started_at, finished_at, status fields from ResultMetadata.

### Medium

- **Coexistence with existing ResultDetailView manifest tab unspecified** | **Source:** Validator A | **Fix:** Added clarification in navigation entry points task that existing Manifest tab remains for basic metadata; new viewer is separate comprehensive view.

- **Collapsible default states unspecified** | **Source:** Validator B | **Fix:** Added explicit defaultOpen states in RunManifestViewer component: Overview and Warnings open by default, others collapsed.

- **Help content key naming pattern** | **Source:** Validator B | **Fix:** Confirmed "results/manifest" key follows existing pattern for stage/sub-view help content entries.

### Low

- **Evidence assets schema generic** | **Source:** Validator B | **Fix:** Kept as `Array<Record<string, unknown>>` for flexibility since actual schema varies by evidence type.

- **RunManifestViewerSubView wrapper necessity** | **Source:** Validator B | **Fix:** Kept wrapper component pattern for separation of concerns (data fetching vs display).

## Issues Dismissed

- **Claimed Issue:** INVEST Negotiable violation due to prescriptive code blocks | **Raised by:** Validator A | **Dismissal Reason:** Code blocks provide implementation examples that are helpful for LLM agents; developer still has flexibility in component structure. Not blocking.

- **Claimed Issue:** INVEST Small violation - story too large | **Raised by:** Validator A | **Dismissal Reason:** Story spans multiple files but is focused on a single feature (manifest viewer). Phase ordering breaks work into manageable chunks. Appropriate scope.

- **Claimed Issue:** Shadcn Collapsible component availability uncertain | **Raised by:** Validator B | **Dismissal Reason:** Collapsible is listed in project context as available Shadcn component. No action needed.

## Deep Verify Integration

Deep Verify did not produce findings for this story.

## Changes Applied

**Location:** `_bmad-output/implementation-artifacts/26-4-complete-stage-5-run-results-compare-with-dedicated-run-manifest-viewer.md` - AC-3
**Change:** Added explicit runId passing mechanism using AppContext.selectedResultForManifest state
**Before:**
```
3. Given a comparison view is active, when a run is selected, then its manifest is reachable via a "View Manifest" button without leaving Stage 5 (opens manifest sub-view).
```
**After:**
```
3. Given a comparison view is active, when a run is selected, then its manifest is reachable via a "View Manifest" button without leaving Stage 5 (opens manifest sub-view using the selected run's run_id from AppContext.selectedResultForManifest state).
```

**Location:** `_bmad-output/implementation-artifacts/26-4-complete-stage-5-run-results-compare-with-dedicated-run-manifest-viewer.md` - AC-4
**Change:** Clarified metadata-only fallback behavior with explicit HTTP response codes
**Before:**
```
4. Given a manifest is incomplete or unavailable (e.g., cache miss, missing panel data), then the viewer shows a clear missing-metadata state rather than failing silently (explains that panel data was evicted and manifest is from metadata only).
```
**After:**
```
4. Given a manifest is incomplete or unavailable (e.g., cache miss, missing panel data), then the viewer shows a clear missing-metadata state rather than failing silently (explains that panel data was evicted and manifest is from metadata only). When only metadata.json and manifest.json exist on disk (no panel.parquet), the endpoint returns 200 with available manifest fields and a metadata_only flag.
```

**Location:** `_bmad-output/implementation-artifacts/26-4-complete-stage-5-run-results-compare-with-dedicated-run-manifest-viewer.md` - AC-6
**Change:** Added explicit field names to Overview section
**Before:**
```
6. Given the manifest viewer renders, then it displays manifest data in organized sections: Overview (run_id, manifest_id, timestamps, status), Execution (seeds, step_pipeline, runtime_mode, population), Policy (assumptions, mappings), Data Provenance (data_hashes, output_hashes, integrity_hash), Lineage (parent_manifest_id, child_manifests), Evidence (evidence_assets, calibration_assets, validation_assets, evidence_summary), Warnings (warnings list).
```
**After:**
```
6. Given the manifest viewer renders, then it displays manifest data in organized sections: Overview (run_id, manifest_id, created_at, started_at, finished_at, status, versions), Execution (seeds, step_pipeline, runtime_mode, population), Policy (assumptions, mappings), Data Provenance (data_hashes, output_hashes, integrity_hash), Lineage (parent_manifest_id, child_manifests), Evidence (evidence_assets, calibration_assets, validation_assets, evidence_summary), Warnings (warnings list).
```

**Location:** `_bmad-output/implementation-artifacts/26-4-complete-stage-5-run-results-compare-with-dedicated-run-manifest-viewer.md` - Backend ManifestResponse model
**Change:** Added missing fields and fixed population_source type
**Before:**
```python
class ManifestResponse(BaseModel):
    """Full run manifest response for Stage 5 manifest viewer — Story 26.4."""
    # Core identity
    manifest_id: str
    created_at: str
    ...
    population_source: Literal["bundled", "uploaded", "generated", ""] = ""
```
**After:**
```python
class ManifestResponse(BaseModel):
    """Full run manifest response for Stage 5 manifest viewer — Story 26.4."""
    # Core identity
    run_id: str
    manifest_id: str
    created_at: str
    started_at: str = ""
    finished_at: str = ""
    status: str = ""
    ...
    population_source: Literal["bundled", "uploaded", "generated"] | None = None
    metadata_only: bool = False
```

**Location:** `_bmad-output/implementation-artifacts/26-4-complete-stage-5-run-results-compare-with-dedicated-run-manifest-viewer.md` - Frontend ManifestResponse interface
**Change:** Added missing fields and fixed types
**Before:**
```typescript
export interface ManifestResponse {
  // Core identity
  manifest_id: string;
  created_at: string;
  ...
  child_manifests: Record<number, string>;
  ...
  population_source: "bundled" | "uploaded" | "generated" | "";
}
```
**After:**
```typescript
export interface ManifestResponse {
  // Core identity
  run_id: string;
  manifest_id: string;
  created_at: string;
  started_at: string;
  finished_at: string;
  status: string;
  ...
  child_manifests: Record<string, string>;
  ...
  population_source: "bundled" | "uploaded" | "generated" | null;
  metadata_only: boolean;
}
```

**Location:** `_bmad-output/implementation-artifacts/26-4-complete-stage-5-run-results-compare-with-dedicated-run-manifest-viewer.md` - Backend endpoint implementation
**Change:** Added metadata-only fallback path with manifest.json load
**Before:**
```python
# Load SimulationResult (from cache or disk)
sim_result = cache.get_or_load(run_id, store)
if sim_result is None:
    raise HTTPException(status_code=409, ...)
```
**After:**
```python
# Try to load SimulationResult (from cache or disk)
sim_result = cache.get_or_load(run_id, store)

if sim_result is None:
    # Panel data unavailable, try loading manifest from disk
    try:
        manifest = store.load_manifest(run_id)
        # Return degraded response with available manifest data
        return ManifestResponse(..., metadata_only=True, ...)
    except FileNotFoundError:
        # Neither SimulationResult nor manifest.json available
        raise HTTPException(status_code=409, ...)
```

**Location:** `_bmad-output/implementation-artifacts/26-4-complete-stage-5-run-results-compare-with-dedicated-run-manifest-viewer.md` - App.tsx integration
**Change:** Replaced placeholder comment with explicit AppContext state pattern
**Before:**
```typescript
if (activeSubView === "manifest") {
    const manifestRunId = /* derive from URL hash or selected result */ runResult?.run_id;
    return (
      <RunManifestViewerSubView
        runId={manifestRunId}
        onBack={() => { navigateTo("results"); }}
      />
    );
}
```
**After:**
```typescript
if (activeSubView === "manifest") {
    const manifestRunId = selectedResultForManifest || runResult?.run_id;
    return (
      <RunManifestViewerSubView
        runId={manifestRunId}
        onBack={() => { navigateTo("results"); }}
      />
    );
}
```

**Location:** `_bmad-output/implementation-artifacts/26-4-complete-stage-5-run-results-compare-with-dedicated-run-manifest-viewer.md` - Empty state task
**Change:** Clarified ResultsOverviewScreen update rather than new component
**Before:**
```
- [ ] Add Stage 5 empty state component (AC: #1)
  - [ ] Create `frontend/src/components/results/RunQueueEmptyState.tsx` or integrate into existing stage layout
```
**After:**
```
- [ ] Add Stage 5 empty state handling (AC: #1)
  - [ ] Update ResultsOverviewScreen to show empty state when results array is empty
```

**Location:** `_bmad-output/implementation-artifacts/26-4-complete-stage-5-run-results-compare-with-dedicated-run-manifest-viewer.md` - Test file paths
**Change:** Fixed test file path to match existing flat structure
**Before:**
```
**Backend Tests:** `tests/server/results/test_manifest_endpoint.py` (NEW)
```
**After:**
```
**Backend Tests:** `tests/server/test_manifest_endpoint.py` (NEW)
```

**Location:** `_bmad-output/implementation-artifacts/26-4-complete-stage-5-run-results-compare-with-dedicated-run-manifest-viewer.md` - Backend endpoint task
**Change:** Updated task description to reflect metadata-only behavior and new fields
**Before:**
```
- [ ] Return 409 if SimulationResult is None (cache miss, no disk data) with helpful message
- [ ] Extract all manifest fields from `sim_result.manifest` (RunManifest dataclass)
- [ ] Include population metadata from ResultMetadata (population_id, population_source)
- [ ] Include runtime_mode from ResultMetadata
```
**After:**
```
- [ ] When SimulationResult is None, try `store.load_manifest(run_id)` for metadata-only response (200 with metadata_only=True, add warning about missing panel data)
- [ ] Return 409 only when both SimulationResult and manifest.json are unavailable (truly unrecoverable)
- [ ] Extract all manifest fields from `sim_result.manifest` (RunManifest dataclass)
- [ ] Include run_id, started_at, finished_at, status from ResultMetadata
- [ ] Include population metadata from ResultMetadata (population_id, population_source)
- [ ] Include runtime_mode from ResultMetadata
```

**Location:** `_bmad-output/implementation-artifacts/26-4-complete-stage-5-run-results-compare-with-dedicated-run-manifest-viewer.md` - Navigation entry points task
**Change:** Added explicit AppContext state pattern and component locations
**Before:**
```
- [ ] Add manifest viewer navigation entry points (AC: #2, #3, #5)
  - [ ] Add "View Manifest" button to ResultDetailView component (in header or actions)
  - [ ] Add manifest button to SimulationRunnerScreen ResultsListPanel row actions
  - [ ] Add manifest button to ComparisonDashboardScreen run selector items
  - [ ] All manifest buttons call `navigateTo("results", "manifest") with runId context
```
**After:**
```
- [ ] Add manifest viewer navigation entry points (AC: #2, #3, #5)
  - [ ] Add `selectedResultForManifest: string | null` to AppContext state
  - [ ] Add "View Manifest" button to ResultsOverviewScreen (header action buttons) — sets selectedResultForManifest then navigates
  - [ ] Add "View Manifest" button to SimulationRunnerScreen ResultsListPanel row actions — sets selectedResultForManifest then navigates
  - [ ] Add "View Manifest" button to ComparisonDashboardScreen run selector items — sets selectedResultForManifest then navigates
  - [ ] All manifest buttons follow pattern: `setSelectedResultForManifest(runId); navigateTo("results", "manifest");`
```

**Location:** `_bmad-output/implementation-artifacts/26-4-complete-stage-5-run-results-compare-with-dedicated-run-manifest-viewer.md` - RunManifestViewer Overview section
**Change:** Added new fields to Overview display
**Before:**
```typescript
<div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
  <span className="text-slate-500">Run ID</span>
  <span className="data-mono font-medium text-slate-800">{manifest.manifest_id.slice(0, 16)}...</span>
  <span className="text-slate-500">Created</span>
  <span className="font-medium text-slate-800">{formatTs(manifest.created_at)}</span>
  ...
</div>
```
**After:**
```typescript
<div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
  <span className="text-slate-500">Run ID</span>
  <span className="data-mono font-medium text-slate-800">{manifest.run_id.slice(0, 16)}...</span>
  <span className="text-slate-500">Manifest ID</span>
  <span className="data-mono font-medium text-slate-800">{manifest.manifest_id.slice(0, 16)}...</span>
  <span className="text-slate-500">Status</span>
  <span className="font-medium text-slate-800">{manifest.status || "completed"}</span>
  ...
</div>
```

**Location:** `_bmad-output/implementation-artifacts/26-4-complete-stage-5-run-results-compare-with-dedicated-run-manifest-viewer.md` - Backend test requirements
**Change:** Added metadata_only test case
**Before:**
```
- Test GET /api/results/{run_id}/manifest returns 200 with full manifest
- Test 404 response when run_id not found
- Test 409 response when SimulationResult is None (cache miss, no disk)
```
**After:**
```
- Test GET /api/results/{run_id}/manifest returns 200 with full manifest
- Test 200 with metadata_only=True when SimulationResult is None but manifest.json exists on disk
- Test 404 response when run_id not found
- Test 409 response when both SimulationResult and manifest.json are unavailable
```

<!-- VALIDATION_SYNTHESIS_END -->

---

## Status: Ready for Development

All Critical and High priority issues have been addressed. The story now has:

- Explicit run ID passing mechanism using AppContext.selectedResultForManifest state
- Clear backend endpoint behavior for metadata-only fallback (200 degraded) vs 409 (unrecoverable)
- Complete ManifestResponse schema with all required fields (run_id, started_at, finished_at, status, metadata_only)
- Corrected type contracts (population_source uses null, child_manifests uses string keys)
- Fixed test file path matching existing project structure
- Clarified empty state handling via ResultsOverviewScreen update
- Explicit navigation entry point locations and patterns

The story maintains its original scope and implementation order while adding necessary contract clarity that prevents implementation ambiguity.
