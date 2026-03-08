

# Story 17.3: Build Simulation Runner with Progress and Persistent Results

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a non-coding policy analyst,
I want a Simulation Runner screen where I can start a simulation from a configured population and policy portfolio, see year-by-year progress and ETA, have results automatically saved to persistent storage, browse all my past runs even after closing the browser, and click any completed run to see its full indicators, panel data summary, and run manifest,
so that I can execute policy simulations with confidence, track execution progress, and return to my results at any time without needing to re-run simulations.

## Acceptance Criteria

1. **AC-1: Run initiation with progress** — Given a configured population and policy portfolio (or single-policy scenario from existing configuration flow), when the analyst clicks "Run Simulation", then the simulation starts and a progress indicator shows: current year being computed (e.g., "Computing year 2027..."), completion percentage (computed as `years_completed / total_years * 100`), and estimated remaining time based on elapsed time per year. The run is synchronous (single HTTP request); progress is simulated client-side based on the year range (start_year to end_year) with a timed interval. The progress bar uses the existing `RunProgressBar` component with enriched step labels. If the API call fails, the progress view transitions to an error state showing structured `what/why/fix` fields. Cancel navigates back to configuration (does not abort the HTTP request for MVP — true abort is out of scope).

2. **AC-2: Automatic persistent save** — Given a running simulation, when it completes (successfully or with a failure), then metadata is automatically saved to persistent storage on the server with a unique run ID (UUID v4, server-generated), timestamp (ISO 8601 UTC), configuration summary (run kind, template name or portfolio name, policy type, year range, population ID, seed), simulation start/end timestamps, adapter version, and final status (`"completed"` or `"failed"`). Full result artifacts (indicators recomputed from cached `SimulationResult`) are available only for completed runs while the result remains in the in-memory cache. The persistent store is a structured directory under `~/.reformlab/results/{run_id}/` containing a `metadata.json` file with run metadata. The existing `ResultCache` continues to hold the full `SimulationResult`; the persistent metadata layer enables listing and browsing across server restarts. On server restart, previously saved metadata files are discoverable but full `SimulationResult` objects are not recoverable (re-run required for full data — documented limitation for MVP). Failed-run metadata is saved with `row_count=0`; the metadata save is wrapped in a try/except so a storage failure does not mask the run error response.

3. **AC-3: Persistent results listing** — Given persistent results, when the analyst opens the Simulation Runner screen (or returns to the application after closing the browser), then all previously completed runs are listed in reverse chronological order showing: run ID (truncated), timestamp, template/portfolio name, year range, row count, and status badge (completed/failed). The list is fetched from `GET /api/results` which reads metadata files from the persistent store. Each run entry is clickable.

4. **AC-4: Run detail view** — Given a completed run in the results list, when the analyst clicks it, then the full result detail view opens showing: distributional indicators chart (reusing `DistributionalChart`), summary statistics cards (reusing `SummaryStatCard`), panel data summary (row count, column count, year range), and run manifest details (manifest ID, scenario ID, adapter version, seed, timestamps). Export buttons (CSV, Parquet) are available if the `SimulationResult` is still in the in-memory cache. If the result has been evicted from cache (server restart), the detail view shows metadata only with a "Re-run to access full data" prompt.

## Tasks / Subtasks

- [x] Task 1: Implement persistent result metadata storage (AC: 2, 3)
  - [x] 1.1: Create `src/reformlab/server/result_store.py` with `ResultStore` class that manages a structured directory at `~/.reformlab/results/`
  - [x] 1.2: Define `ResultMetadata` frozen dataclass with fields: `run_id: str`, `timestamp: str` (ISO 8601 UTC — submission time), `run_kind: str` (`"scenario"` or `"portfolio"`), `start_year: int`, `end_year: int`, `population_id: str | None`, `seed: int | None`, `row_count: int` (0 for failed runs), `manifest_id: str`, `scenario_id: str`, `adapter_version: str`, `started_at: str` (ISO 8601 UTC — simulation start), `finished_at: str` (ISO 8601 UTC — simulation end), `status: str` (`"completed"` or `"failed"`), `template_name: str | None = None` (scenario runs only), `policy_type: str | None = None` (scenario runs only), `portfolio_name: str | None = None` (portfolio runs only). Define a `ResultStoreError` base exception and `ResultNotFound(ResultStoreError)` subclass in `result_store.py` for consistent error propagation
  - [x] 1.3: Implement `ResultStore.save_metadata(run_id, metadata)` — writes `metadata.json` to `~/.reformlab/results/{run_id}/metadata.json` using atomic write (write to `.metadata.json.tmp` then `os.replace()`) to prevent corrupt files on crash
  - [x] 1.4: Implement `ResultStore.list_results()` — scans results directory, loads all `metadata.json` files, returns list sorted by `timestamp` descending (parse as `datetime` for correct ordering, not string comparison); skip and log a warning for corrupt or missing entries rather than raising
  - [x] 1.5: Implement `ResultStore.get_metadata(run_id)` — loads single metadata file by run_id; raises `ResultNotFound` if the directory or file does not exist
  - [x] 1.6: Implement `ResultStore.delete_result(run_id)` — removes the run directory
  - [x] 1.7: Add `get_result_store()` dependency function to `src/reformlab/server/dependencies.py`
  - [x] 1.8: Write tests in `tests/server/test_result_store.py`

- [x] Task 2: Implement FastAPI endpoints for result listing and retrieval (AC: 3, 4)
  - [x] 2.1: Create `src/reformlab/server/routes/results.py` with router
  - [x] 2.2: Add `GET /results` endpoint (full path: `GET /api/results`) — list all saved results with metadata
  - [x] 2.3: Add `GET /results/{run_id}` endpoint (full path: `GET /api/results/{run_id}`) — return result detail; if `SimulationResult` in cache, include indicators summary; if not, return metadata only with `data_available: false`
  - [x] 2.4: Add `DELETE /results/{run_id}` endpoint (full path: `DELETE /api/results/{run_id}`) — remove from both persistent store and cache
  - [x] 2.5: Add Pydantic v2 request/response models to `src/reformlab/server/models.py`: `ResultMetadataResponse`, `ResultDetailResponse`, `ResultListItem`
  - [x] 2.6: Register results router in `src/reformlab/server/app.py`
  - [x] 2.7: Modify `POST /api/runs` in `src/reformlab/server/routes/runs.py` to auto-save metadata after every run (success and failure). Record `started_at` before invoking the simulation pipeline; record `finished_at` in a `finally` block. Save metadata with `status="completed"` on success and `status="failed"` on exception (`row_count=0`, `manifest_id=""`, `adapter_version="unknown"` when result is unavailable). Wrap the `save_metadata()` call in its own try/except so a storage failure does not prevent the run response from being returned. Add regression tests to `tests/server/test_runs.py` verifying that metadata is saved on both success and failure paths
  - [x] 2.8: Write backend tests in `tests/server/test_results.py`
  - [x] 2.9: Add `GET /results/{run_id}/export/csv` endpoint (full path: `GET /api/results/{run_id}/export/csv`) — retrieve `SimulationResult` from `ResultCache` and stream the panel data `pa.Table` as a CSV file download (`Content-Disposition: attachment; filename="{run_id}.csv"`). Return 404 if run_id not found in persistent store; return 409 if result has been evicted from cache (`data_available: false`)
  - [x] 2.10: Add `GET /results/{run_id}/export/parquet` endpoint (full path: `GET /api/results/{run_id}/export/parquet`) — same as 2.9 but stream as Parquet. Use `pyarrow.parquet.write_table()` to an in-memory buffer and return with `Content-Type: application/octet-stream`

- [x] Task 3: Define frontend TypeScript types and API client layer (AC: 3, 4)
  - [x] 3.1: Add TypeScript interfaces to `frontend/src/api/types.ts`: `ResultListItem`, `ResultDetailResponse`, `ResultMetadata`
  - [x] 3.2: Create `frontend/src/api/results.ts` with API functions: `listResults()`, `getResult()`, `deleteResult()`
  - [x] 3.3: Add `useResults()` hook to `frontend/src/hooks/useApi.ts` following existing mock-data-fallback pattern
  - [x] 3.4: Add mock data for results in `frontend/src/data/mock-data.ts`: `MockResultItem`, `mockResults`

- [x] Task 4: Build SimulationRunnerScreen with progress (AC: 1)
  - [x] 4.1: Create `frontend/src/components/screens/SimulationRunnerScreen.tsx` — orchestration container with three sub-views: Configure (pre-run summary), Progress (running), Results (post-run). Uses existing `RunProgressBar` for progress display
  - [x] 4.2: Implement client-side progress simulation: given `start_year` and `end_year`, tick through years at a timed interval (total run time / year count), updating `currentStep` ("Computing year YYYY...") and `progress` percentage. On API completion, jump to 100% and transition to results sub-view
  - [x] 4.3: Implement error state: on API failure, show `PopulationGenerationProgress`-style error display with what/why/fix fields
  - [x] 4.4: Add unit tests for SimulationRunnerScreen

- [x] Task 5: Build ResultsListPanel for persistent results browsing (AC: 3)
  - [x] 5.1: Create `frontend/src/components/simulation/ResultsListPanel.tsx` — reverse-chronological list of completed runs with: truncated run ID (first 8 chars), formatted timestamp, template/portfolio name, year range badge, row count, status badge, click-to-select, delete button
  - [x] 5.2: Add unit tests for ResultsListPanel

- [x] Task 6: Build ResultDetailView for run inspection (AC: 4)
  - [x] 6.1: Create `frontend/src/components/simulation/ResultDetailView.tsx` — tabbed detail view with: "Indicators" tab (DistributionalChart + SummaryStatCard grid), "Data Summary" tab (row/column count, year range, columns list), "Manifest" tab (manifest ID, scenario ID, adapter version, seed, timestamps). If `data_available: false`, show metadata-only view with "Re-run to access full data" prompt
  - [x] 6.2: Add export buttons (CSV, Parquet) in "Data Summary" tab, disabled when `data_available: false`
  - [x] 6.3: Add unit tests for ResultDetailView

- [x] Task 7: Integrate SimulationRunnerScreen into workspace (AC: 1, 2, 3, 4)
  - [x] 7.1: Add `"runner"` view mode to `App.tsx` ViewMode type
  - [x] 7.2: Wire `SimulationRunnerScreen` into `App.tsx` main content area
  - [x] 7.3: Add "Simulation" navigation button to left panel (between "Portfolio" and "Configure Policy")
  - [x] 7.4: Update `AppContext.tsx` — add `results: ResultListItem[]`, `resultsLoading: boolean`, `refetchResults: () => Promise<void>`. Verify that `AppContext` already exposes (or add) `selectedPopulationId: string | null` (set by DataFusionWorkbench in Story 17.1) and `selectedPortfolioName: string | null` (set by PortfolioDesignerScreen in Story 17.2), as `SimulationRunnerScreen` reads these to populate the pre-run summary and builds the `POST /api/runs` request body. The pre-run summary sub-view should also expose local state for `startYear`, `endYear`, and `seed` editable by the analyst before submitting
  - [x] 7.5: Wire run completion to auto-refetch results list
  - [x] 7.6: Verify non-regression: existing view modes (configuration, data-fusion, portfolio, run, progress, results, comparison), left panel navigation, and `Cmd+[`/`Cmd+]` keyboard shortcuts remain functional

- [x] Task 8: Run quality checks (AC: all)
  - [x] 8.1: Run `uv run ruff check src/ tests/` and fix any lint issues
  - [x] 8.2: Run `uv run mypy src/` and fix any type errors
  - [x] 8.3: Run `cd frontend && npm run typecheck && npm run lint` and fix any issues
  - [x] 8.4: Run `uv run pytest tests/` — all tests pass
  - [x] 8.5: Run `cd frontend && npm test` — all tests pass

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**Backend — Canonical endpoint table:**

| Method | Full URL | Router-relative path | Purpose |
|---|---|---|---|
| GET | `/api/results` | `/` | List all saved results (metadata only) |
| GET | `/api/results/{run_id}` | `/{run_id}` | Get result detail (metadata + indicators if cached) |
| DELETE | `/api/results/{run_id}` | `/{run_id}` | Delete result from persistent store and cache |
| GET | `/api/results/{run_id}/export/csv` | `/{run_id}/export/csv` | Download panel data as CSV (requires cache hit) |
| GET | `/api/results/{run_id}/export/parquet` | `/{run_id}/export/parquet` | Download panel data as Parquet (requires cache hit) |

**Backend — HTTP status code matrix:**

| Endpoint | Success | Client Error |
|---|---|---|
| `GET /api/results` | 200 | — |
| `GET /api/results/{run_id}` | 200 | 404 (not found) |
| `DELETE /api/results/{run_id}` | 204 | 404 (not found) |
| `GET /api/results/{run_id}/export/csv` | 200 (streaming) | 404 (not found), 409 (data evicted from cache) |
| `GET /api/results/{run_id}/export/parquet` | 200 (streaming) | 404 (not found), 409 (data evicted from cache) |

All error responses use `{"what": str, "why": str, "fix": str}` structure.

**Backend — FastAPI route pattern:**
- Router created with `APIRouter()`, registered in `app.py` via `app.include_router(router, prefix="/api/results", tags=["results"])`
- Use lazy imports inside route handlers (same pattern as `scenarios.py`, `portfolios.py`)
- Pydantic v2 models in `models.py` — use `BaseModel` with `Field(...)`
- Structured error responses with `what`, `why`, `fix` fields
- `from __future__ import annotations` on every Python file
- Logging: `logging.getLogger(__name__)`, structured `key=value` format

**Backend — ResultStore persistence architecture:**

The persistent result store is a lightweight metadata layer on top of the existing `ResultCache`:

```
~/.reformlab/results/
  {run_id}/
    metadata.json     ← Run metadata (config, timestamps, IDs)
```

- `ResultStore` does NOT store the full `SimulationResult` (which contains large PyArrow tables)
- `ResultStore` stores only lightweight metadata that enables listing and identification
- The full `SimulationResult` remains in the `ResultCache` (in-memory LRU, max 10)
- On `GET /api/results/{run_id}`, the route handler checks both: metadata from `ResultStore` + full data from `ResultCache`
- If the `ResultCache` has the result → return full detail with indicators
- If only metadata exists → return metadata with `data_available: false`

**ResultStore write safety:**
- All metadata writes use atomic rename: write to `{run_id}/.metadata.json.tmp`, then `os.replace()` to `{run_id}/metadata.json`
- `list_results()` wraps each file load in try/except and skips corrupt entries (logs `level=WARNING event=corrupt_metadata run_id=...`)
- `get_metadata()` raises `ResultNotFound` for missing directories/files; route handlers convert to 404
- Route handlers for export endpoints return 409 (Conflict) when the run_id is found in persistent store but the `SimulationResult` has been evicted from the `ResultCache`

**Why this design:**
- Story 17.7 will implement full persistent storage (Parquet serialization of panel data, manifest persistence)
- This story focuses on the **GUI experience** of persistent results: listing, browsing, detail viewing
- The metadata layer is sufficient for the GUI showcase while keeping implementation focused

**ResultMetadata schema:**

```python
@dataclass(frozen=True)
class ResultMetadata:
    run_id: str
    timestamp: str        # ISO 8601 UTC — submission time
    run_kind: str         # "scenario" | "portfolio"
    start_year: int
    end_year: int
    population_id: str | None
    seed: int | None
    row_count: int        # 0 for failed runs
    manifest_id: str      # empty string for failed runs
    scenario_id: str      # empty string for failed runs
    adapter_version: str  # "unknown" for failed runs
    started_at: str       # ISO 8601 UTC — simulation start
    finished_at: str      # ISO 8601 UTC — simulation end
    status: str           # "completed" | "failed"
    template_name: str | None = None   # scenario runs; None for portfolio-only runs
    policy_type: str | None = None     # scenario runs; None for portfolio-only runs
    portfolio_name: str | None = None  # portfolio runs; None for scenario-only runs
```

**ResultStore exceptions:**

```python
class ResultStoreError(Exception):
    """Base exception for ResultStore operations."""

class ResultNotFound(ResultStoreError):
    """Raised when a run_id does not exist in the persistent store."""
```

Route handlers catch `ResultNotFound` and convert it to `HTTPException(status_code=404, detail={"what": ..., "why": ..., "fix": ...})`.

**Auto-save integration in `POST /api/runs`:**

The existing `run_simulation()` route handler must save metadata for both success and failure. Wrap the simulation call with timestamp capture and a `finally` block:

```python
# In runs.py — save metadata for both success and failure:
started_at = datetime.now(timezone.utc).isoformat()
result = None
status = "failed"
row_count = 0
try:
    result = run_simulation_pipeline(body, adapter, cache)
    cache.store(run_id, result)
    status = "completed" if result.success else "failed"
    row_count = result.panel_data.num_rows if result.success else 0
finally:
    finished_at = datetime.now(timezone.utc).isoformat()
    store = get_result_store()
    try:
        run_kind = "portfolio" if body.portfolio_name else "scenario"
        store.save_metadata(run_id, ResultMetadata(
            run_id=run_id,
            timestamp=started_at,
            run_kind=run_kind,
            template_name=body.template_name,
            policy_type=body.policy_type,
            portfolio_name=body.portfolio_name,
            start_year=body.start_year,
            end_year=body.end_year,
            population_id=body.population_id,
            seed=body.seed,
            row_count=row_count,
            manifest_id=result.manifest.manifest_id if result else "",
            scenario_id=result.scenario_id if result else "",
            adapter_version=result.adapter_version if result else "unknown",
            started_at=started_at,
            finished_at=finished_at,
            status=status,
        ))
    except Exception:
        logger.exception("event=metadata_save_failed run_id=%s", run_id)
        # Do not propagate — metadata save failure should not mask run result
```

**Backend — Dependencies pattern:**

Add to `src/reformlab/server/dependencies.py`:

```python
from reformlab.server.result_store import ResultStore

_result_store: ResultStore | None = None

def get_result_store() -> ResultStore:
    global _result_store
    if _result_store is None:
        _result_store = ResultStore()
    return _result_store
```

### Frontend Patterns (MUST FOLLOW)

**Frontend — Component pattern:**
- Components in `frontend/src/components/simulation/` (domain components) and `frontend/src/components/screens/` (full-width screens)
- Single `.tsx` file per component, props via TypeScript interface
- Tailwind-only styling, NO CSS modules/styled-components
- Use `cn()` from `@/lib/utils` for class merging
- Dense Terminal style: hard 1px `border-slate-200`, `p-3` padding, no shadows on static elements, square corners
- Color tokens: `emerald` = completed/pass, `red` = error/fail, `amber` = warning/running, `blue` = selection/active, `slate` = neutral
- React 19 — NO `forwardRef`, ref is regular prop
- Icons from `lucide-react`
- `cva` (class-variance-authority) for component variants
- Semantic HTML: `<button>` not `<div onClick>`, `<section>`, `<nav>`

**Frontend — State management pattern:**
- React Context via `AppContext.tsx` → `useAppState()` hook
- API hooks in `useApi.ts` with mock data fallback pattern
- API client layer in `frontend/src/api/` — `apiFetch<T>()` with auth token injection

**Frontend — SimulationRunnerScreen design:**

The screen has three internal sub-views:

1. **Pre-run summary** — Shows selected population, portfolio/template, year range, seed. "Run Simulation" button.
2. **Progress** — `RunProgressBar` with simulated year-by-year progress. Client-side timer ticks through `[start_year, ..., end_year]` at even intervals. On API completion: snap to 100%, pause 500ms, transition to results.
3. **Post-run** — Shows `ResultDetailView` for the just-completed run, plus `ResultsListPanel` for browsing past runs.

**Client-side progress simulation strategy:**

The existing `POST /api/runs` is synchronous — it blocks until the simulation completes. The frontend cannot get real server-side progress. Instead:

```typescript
// Start API call and progress timer concurrently
const totalYears = endYear - startYear + 1;
const estimatedMs = totalYears * 1500; // ~1.5s per year estimate
const tickMs = estimatedMs / totalYears;
let currentYear = startYear;

const timer = setInterval(() => {
  currentYear++;
  if (currentYear <= endYear) {
    setProgress(((currentYear - startYear) / totalYears) * 90); // Cap at 90%
    setCurrentStep(`Computing year ${currentYear}...`);
    setEta(`~${Math.ceil((endYear - currentYear) * tickMs / 1000)}s`);
  }
}, tickMs);

try {
  const result = await runScenario(request);
  clearInterval(timer);
  setProgress(100);
  setCurrentStep("Complete");
  // Transition to results after brief pause
} catch (err) {
  clearInterval(timer);
  // Show error state
}
```

Cap simulated progress at 90% to avoid showing "done" before the API actually returns.

**Frontend — ViewMode integration:**

```typescript
type ViewMode = "configuration" | "run" | "progress" | "results" | "comparison"
  | "data-fusion" | "portfolio" | "runner";  // Add "runner"
```

Add `"Simulation"` button to left panel navigation between "Portfolio" and "Configure Policy".

### Pydantic Request/Response Models

Add these models to `src/reformlab/server/models.py`:

```python
class ResultListItem(BaseModel):
    """Summary of a saved simulation result."""
    model_config = {"from_attributes": True}
    run_id: str
    timestamp: str
    run_kind: str           # "scenario" | "portfolio"
    start_year: int
    end_year: int
    row_count: int
    status: str
    data_available: bool    # True if SimulationResult is in cache
    template_name: str | None = None   # scenario runs only
    policy_type: str | None = None     # scenario runs only
    portfolio_name: str | None = None  # portfolio runs only

class ResultDetailResponse(BaseModel):
    """Full detail for a single simulation result."""
    model_config = {"from_attributes": True}
    run_id: str
    timestamp: str
    run_kind: str
    start_year: int
    end_year: int
    population_id: str | None
    seed: int | None
    row_count: int
    manifest_id: str
    scenario_id: str
    adapter_version: str
    started_at: str
    finished_at: str
    status: str
    data_available: bool
    template_name: str | None = None
    policy_type: str | None = None
    portfolio_name: str | None = None
    # Populated only when data_available is True:
    indicators: dict[str, Any] | None = None
    columns: list[str] | None = None
    column_count: int | None = None
```

### TypeScript Types

Add to `frontend/src/api/types.ts`:

```typescript
// Result types — Story 17.3
export interface ResultListItem {
  run_id: string;
  timestamp: string;
  run_kind: string;              // "scenario" | "portfolio"
  start_year: number;
  end_year: number;
  row_count: number;
  status: string;
  data_available: boolean;
  template_name: string | null;  // scenario runs only
  policy_type: string | null;    // scenario runs only
  portfolio_name: string | null; // portfolio runs only
}

export interface ResultDetailResponse extends ResultListItem {
  population_id: string | null;
  seed: number | null;
  manifest_id: string;
  scenario_id: string;
  adapter_version: string;
  started_at: string;
  finished_at: string;
  indicators: Record<string, unknown> | null;
  columns: string[] | null;
  column_count: number | null;
}
```

### Mock Data for Results

```typescript
export interface MockResultItem {
  run_id: string;
  timestamp: string;
  run_kind: string;
  template_name: string | null;
  policy_type: string | null;
  portfolio_name: string | null;
  start_year: number;
  end_year: number;
  row_count: number;
  status: string;
  data_available: boolean;
}

export const mockResults: MockResultItem[] = [
  {
    run_id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    timestamp: "2026-03-07T22:15:30Z",
    run_kind: "scenario",
    template_name: "Carbon Tax — With Dividend",
    policy_type: "carbon_tax",
    portfolio_name: null,
    start_year: 2025,
    end_year: 2030,
    row_count: 600000,
    status: "completed",
    data_available: true,
  },
  {
    run_id: "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    timestamp: "2026-03-07T21:45:12Z",
    run_kind: "portfolio",
    template_name: null,
    policy_type: null,
    portfolio_name: "green-transition-2030",
    start_year: 2025,
    end_year: 2035,
    row_count: 1100000,
    status: "completed",
    data_available: false,
  },
  {
    run_id: "c3d4e5f6-a7b8-9012-cdef-123456789012",
    timestamp: "2026-03-07T20:30:00Z",
    run_kind: "scenario",
    template_name: "Carbon Tax — Uniform Rate",
    policy_type: "carbon_tax",
    portfolio_name: null,
    start_year: 2025,
    end_year: 2027,
    row_count: 0,
    status: "failed",
    data_available: false,
  },
];
```

### Source Tree Components to Touch

**New files:**
```
src/reformlab/server/result_store.py                    ← Persistent metadata storage
src/reformlab/server/routes/results.py                  ← API routes for results
tests/server/test_result_store.py                       ← ResultStore unit tests
tests/server/test_results.py                            ← Results endpoint tests
frontend/src/api/results.ts                             ← API client functions
frontend/src/components/screens/SimulationRunnerScreen.tsx
frontend/src/components/simulation/ResultsListPanel.tsx
frontend/src/components/simulation/ResultDetailView.tsx
frontend/src/components/screens/__tests__/SimulationRunnerScreen.test.tsx
frontend/src/components/simulation/__tests__/ResultsListPanel.test.tsx
frontend/src/components/simulation/__tests__/ResultDetailView.test.tsx
```

**Modified files:**
```
src/reformlab/server/models.py                          ← Add result Pydantic models
src/reformlab/server/app.py                             ← Register results router
src/reformlab/server/dependencies.py                    ← Add get_result_store()
src/reformlab/server/routes/runs.py                     ← Auto-save metadata after run (success + failure)
tests/server/test_runs.py                               ← Regression tests for modified runs.py
frontend/src/api/types.ts                               ← Add result TypeScript interfaces
frontend/src/data/mock-data.ts                          ← Add mock result data (run_kind, failed run)
frontend/src/hooks/useApi.ts                            ← Add useResults hook
frontend/src/contexts/AppContext.tsx                     ← Add results state + verify run config state
frontend/src/App.tsx                                    ← Add "runner" view mode, wire screen
```

### Frontend Existing Components to Reuse

| Existing Component | Reuse in 17.3 |
|---|---|
| `RunProgressBar.tsx` | Use directly for progress display in SimulationRunnerScreen |
| `PopulationGenerationProgress.tsx` | Pattern for error display (what/why/fix) |
| `DistributionalChart.tsx` | Use directly in ResultDetailView for indicator charts |
| `SummaryStatCard.tsx` | Use directly in ResultDetailView for KPI cards |
| `ScenarioCard.tsx` | Pattern for ResultsListPanel run entry cards |
| `DataFusionWorkbench.tsx` | Pattern for multi-sub-view screen with internal state machine |
| `PortfolioDesignerScreen.tsx` | Pattern for step-based screen with WorkbenchStepper |
| `Badge` | Status badge rendering (completed=success, failed=destructive, running=warning) |

### Shadcn/ui Components Available

Already installed: Badge, Button, Card, Collapsible, Dialog, Input, Popover, ScrollArea, Select, Separator, Sheet, Slider, Switch, Table, Tabs, Tooltip, Sonner (toast).

### Dependency Versions (Current)

**Frontend** (from `package.json`):
- React 19.1.1, React DOM 19.1.1
- Vite 7.1.5, TypeScript 5.9.2
- Tailwind CSS v4 via `@tailwindcss/vite` 4.1.13
- Recharts 3.1.2
- lucide-react 0.542.0
- Vitest 3.2.4, @testing-library/react 16.3.0

**Backend** (from `pyproject.toml`):
- FastAPI >= 0.133.0, uvicorn >= 0.41.0
- Pydantic >= 2.10
- Python 3.13+, mypy strict

### Important Scope Boundaries

**What this story does:**
- Builds the Simulation Runner GUI screen (pre-run, progress, post-run)
- Implements client-side progress simulation (not real server-side streaming)
- Creates lightweight persistent metadata storage for results (`ResultStore`)
- Adds API endpoints for listing and retrieving saved results
- Modifies `POST /api/runs` to auto-save metadata
- Builds results list panel for browsing past runs
- Builds result detail view with indicators, data summary, and manifest
- Integrates into the workspace as a new `"runner"` view mode

**What this story does NOT do:**
- Full `SimulationResult` serialization to disk (Story 17.7 — only metadata is persisted)
- Real server-side progress streaming via WebSocket/SSE (simulated client-side for MVP)
- Multi-portfolio comparison dashboard (Story 17.4)
- Behavioral decision viewer (Story 17.5)
- Additional Phase 2 backend endpoints beyond results (Story 17.6)
- E2E browser tests with Playwright/Cypress (Story 17.8)
- Abort/cancel running simulations on the server (out of scope for synchronous model)

### Relationship Between Story 17.3 and Story 17.7

Story 17.7 ("Implement persistent result storage and retrieval") is the **full backend persistence** story. It covers:
- Serializing `SimulationResult` (including PyArrow panel data) to disk
- Loading full results from disk after server restart
- Hash-verified integrity checks

Story 17.3 implements the **GUI layer and lightweight metadata persistence**. This allows:
- Results listing and browsing to work immediately
- Full data access while the result is in the in-memory cache (max 10 recent runs)
- Metadata-only view for older evicted results (with "re-run" prompt)
- Story 17.7 can later enhance `ResultStore` to serialize full data without changing the GUI

### Anti-Patterns to Avoid

| Issue | Prevention |
|---|---|
| Implementing full SimulationResult serialization | Only persist metadata.json — leave full serialization for Story 17.7 |
| WebSocket/SSE for real-time progress | Use client-side progress simulation — synchronous HTTP is sufficient for MVP |
| Adding new npm dependencies | All needed dependencies already installed (Recharts, lucide-react, etc.) |
| Mobile-responsive layouts | Desktop-only (min 1280px) |
| Shadows on static layout elements | Shadows reserved for floating elements only |
| Using `forwardRef` | React 19: ref is a regular prop |
| Creating separate state management | Follow existing React Context pattern |
| Importing OpenFisca in server routes | Use adapter interface only |
| Storing large data in localStorage | Result data stays server-side; only metadata persisted on server filesystem |
| Progress bar reaching 100% before API returns | Cap simulated progress at 90%; only set 100% when API response arrives |
| Creating a new results database | Use filesystem-based structured directories (same pattern as ScenarioRegistry) |
| Breaking existing run/progress/results flow | New "runner" view mode coexists with existing view modes; existing flow continues to work |

### Testing Standards Summary

**Backend tests:**
- Files: `tests/server/test_result_store.py`, `tests/server/test_results.py`
- Use `tmp_path` fixture for ResultStore tests (don't pollute real `~/.reformlab/results/`)
- Use FastAPI `TestClient` pattern from `tests/server/test_api.py`
- Test each endpoint: valid input → expected response, invalid input → error
- Test metadata round-trip: save → list → get → verify all fields including `run_kind`, `adapter_version`, `started_at`, `finished_at`
- Test cache interaction: result in cache → `data_available: true`; evicted → `data_available: false`
- Test failed-run metadata persistence: simulate run failure, verify `status="failed"`, `row_count=0` saved; metadata appears in list endpoint
- Test `list_results()` skips corrupt/malformed JSON entries and continues loading others
- Test export endpoints: 200 with valid cached result; 409 when result evicted; 404 when run_id unknown
- Test `runs.py` regression: verify existing run response shape is unchanged after auto-save addition; verify metadata save failure does not cause run endpoint to error

**Frontend tests:**
- Use Vitest + @testing-library/react (already configured)
- Test SimulationRunnerScreen: render, run initiation, progress display, error state
- Test ResultsListPanel: render with mock data, click selection, delete
- Test ResultDetailView: render with data_available=true (full view), data_available=false (metadata only)
- Follow existing test patterns in `frontend/src/__tests__/` and `frontend/src/components/simulation/__tests__/`

### Cross-Story Dependencies

| Story | Relationship |
|---|---|
| Story 17.1 | **Predecessor** — Data Fusion Workbench produces populations consumed by runner |
| Story 17.2 | **Predecessor** — Portfolio Designer produces portfolios consumed by runner |
| EPIC-3 (orchestrator) | **Produces** the `Orchestrator.run()` pipeline that executes simulations |
| EPIC-4 (indicators) | **Produces** the indicator computation used in result detail view |
| EPIC-5 (governance) | **Produces** `RunManifest` captured in run metadata |
| Story 6.4b | **Established** existing run endpoints (`POST /api/runs`) and `ResultCache` |
| Story 17.4 | **Consumer** — Comparison Dashboard uses persistent results for multi-run comparison |
| Story 17.7 | **Extension** — Full persistent storage replaces metadata-only persistence |
| Story 17.8 | **Extension** — E2E browser tests for the runner flow |

### Project Structure Notes

- Backend routes align with `src/reformlab/server/routes/` convention
- ResultStore aligns with `src/reformlab/server/` (server infrastructure, not domain layer)
- Frontend components align with `frontend/src/components/{simulation,screens}/` convention
- API client aligns with `frontend/src/api/` convention with typed fetch wrappers
- No new npm or Python dependencies required
- TypeScript path aliases (`@/`) already configured in `tsconfig.json`
- Results stored under `~/.reformlab/results/` (similar to registry at `~/.reformlab/registry/`)

### References

- [Source: docs/epics.md#Epic 17, Story 17.3] — Acceptance criteria
- [Source: docs/epics.md#Epic 17, Story 17.7] — Persistent storage AC (for scoping)
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#RunProgressBar] — Progress bar design
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Simulation Execution] — "Effortless" run UX
- [Source: _bmad-output/planning-artifacts/architecture.md] — Tech stack, layered architecture
- [Source: docs/project-context.md] — Coding conventions, testing rules
- [Source: src/reformlab/server/routes/runs.py] — Existing run endpoint
- [Source: src/reformlab/server/dependencies.py] — ResultCache and adapter injection
- [Source: src/reformlab/interfaces/api.py] — SimulationResult, ScenarioConfig, RunConfig
- [Source: src/reformlab/governance/manifest.py] — RunManifest schema
- [Source: src/reformlab/templates/registry.py] — ScenarioRegistry filesystem pattern
- [Source: src/reformlab/server/routes/portfolios.py] — CRUD route pattern reference
- [Source: src/reformlab/server/routes/scenarios.py] — CRUD route pattern reference
- [Source: src/reformlab/server/models.py] — Pydantic model pattern reference
- [Source: src/reformlab/server/app.py] — Router registration pattern
- [Source: frontend/src/App.tsx] — Workspace orchestration, view modes
- [Source: frontend/src/contexts/AppContext.tsx] — State management pattern
- [Source: frontend/src/hooks/useApi.ts] — Data fetching hook pattern
- [Source: frontend/src/api/client.ts] — API client with error handling
- [Source: frontend/src/api/runs.ts] — Run API pattern reference
- [Source: frontend/src/api/indicators.ts] — Indicator API pattern reference
- [Source: frontend/src/api/exports.ts] — Export API pattern reference
- [Source: frontend/src/components/simulation/RunProgressBar.tsx] — Existing progress component
- [Source: frontend/src/components/simulation/PopulationGenerationProgress.tsx] — Error display pattern
- [Source: frontend/src/components/simulation/DistributionalChart.tsx] — Chart component
- [Source: frontend/src/components/simulation/SummaryStatCard.tsx] — KPI card component
- [Source: frontend/src/components/simulation/ScenarioCard.tsx] — Card with status pattern
- [Source: frontend/src/components/screens/DataFusionWorkbench.tsx] — Step-flow screen pattern
- [Source: frontend/src/components/screens/PortfolioDesignerScreen.tsx] — Step-flow + save pattern
- [Source: frontend/src/data/mock-data.ts] — Mock data structure reference
- [Source: _bmad-output/implementation-artifacts/17-1-build-data-fusion-workbench-gui.md] — Story 17.1 patterns
- [Source: _bmad-output/implementation-artifacts/17-2-build-policy-portfolio-designer-gui.md] — Story 17.2 patterns

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — all issues resolved inline during implementation.

### Completion Notes List

- `get_adapter()` and `get_result_store()` are called as plain functions in `runs.py` (not via FastAPI `Depends()`), so test isolation requires `monkeypatch.setattr(deps, "_adapter", MockAdapter())` and `monkeypatch.setattr(deps, "_result_store", tmp_store)` rather than `app.dependency_overrides`.
- `_dict_to_metadata()` uses `int(str(value))` coercion pattern to satisfy mypy strict mode when deserializing `dict[str, object]` from JSON.
- Client-side progress is capped at 90% until API response arrives; jumps to 100% on success.
- Export endpoints return HTTP 409 (Conflict) when run_id exists in persistent store but `SimulationResult` has been evicted from `ResultCache`.
- `refetchResults()` is called once on auth in `AppContext.tsx` (duplicate call removed during lint pass).
- All 3028 pytest tests pass; all 154 frontend Vitest tests pass.
- Code review synthesis (2026-03-08): fixed path traversal vulnerability in ResultStore, fixed naive/aware datetime sort bug in _parse_timestamp, added ResultCache.delete() and wired it in DELETE route, added simulation failure metadata test, wired export callbacks in SimulationRunnerScreen.

### File List

**New files:**
- `src/reformlab/server/result_store.py`
- `src/reformlab/server/routes/results.py`
- `tests/server/test_result_store.py`
- `tests/server/test_results.py`
- `tests/server/test_runs.py`
- `frontend/src/api/results.ts`
- `frontend/src/components/screens/SimulationRunnerScreen.tsx`
- `frontend/src/components/simulation/ResultsListPanel.tsx`
- `frontend/src/components/simulation/ResultDetailView.tsx`
- `frontend/src/components/screens/__tests__/SimulationRunnerScreen.test.tsx`
- `frontend/src/components/simulation/__tests__/ResultsListPanel.test.tsx`
- `frontend/src/components/simulation/__tests__/ResultDetailView.test.tsx`

**Modified files:**
- `src/reformlab/server/models.py`
- `src/reformlab/server/app.py`
- `src/reformlab/server/dependencies.py`
- `src/reformlab/server/routes/runs.py`
- `frontend/src/api/types.ts`
- `frontend/src/data/mock-data.ts`
- `frontend/src/hooks/useApi.ts`
- `frontend/src/contexts/AppContext.tsx`
- `frontend/src/App.tsx`

## Senior Developer Review (AI)

### Review: 2026-03-08
- **Reviewer:** AI Code Review Synthesis
- **Evidence Score:** 16.0 (Reviewer A) / 7.6 (Reviewer B) → REJECT
- **Issues Found:** 8 verified (4 fixed, 4 deferred)
- **Issues Fixed:** 4
- **Action Items Created:** 4

#### Review Follow-ups (AI)
- [ ] [AI-Review] IMPORTANT: `frontend/src/api/types.ts` `RunRequest.parameters` does not match backend `RunRequest.policy` field — simulation runs from runner always use empty policy config (`frontend/src/components/screens/SimulationRunnerScreen.tsx:111`)
- [ ] [AI-Review] IMPORTANT: `ResultDetailView` Indicators tab does not reuse `DistributionalChart` or `SummaryStatCard` as specified in AC-4; backend returns `{columns, row_count}` dict rather than distributional data shape (`frontend/src/components/simulation/ResultDetailView.tsx:63`)
- [ ] [AI-Review] IMPORTANT: Export tests only cover 404 and 409 paths; success (200) path with cached `SimulationResult` is untested (`tests/server/test_results.py:290`)
- [ ] [AI-Review] LOW: `exportResultCsv`/`exportResultParquet` in `results.ts` duplicate auth/error-handling logic — extract shared download helper (`frontend/src/api/results.ts:23`)

