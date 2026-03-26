
# Story 20.4: Build Population Library and Data Explorer stage

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a policy analyst,
I want to browse available population datasets in a library, quickly preview their contents, explore columns with profile charts, upload custom datasets, and select populations for my scenario,
so that I can understand and choose the right population data for my policy analysis without leaving the workspace.

## Acceptance Criteria

1. **AC-1: Population Library as Stage 2 entry point** — Given Stage 2 (Population) is open, when the user views the screen, then a Population Library lists all available datasets (built-in, generated, uploaded) with per-population metadata (name, source tag, row count, column count, created date) and action buttons (Preview, Explore, Select, and Delete for non-built-in populations). The library is the default view when no sub-view is active.
2. **AC-2: Quick Preview slide-over** — Given a population in the library, when the user clicks Preview, then a right-side slide-over panel opens showing the first 100 rows in a sortable table with column headers, per-column filter inputs, a row count indicator, and an "Open full view" link that navigates to the Full Data Explorer. The slide-over closes on backdrop click or Escape.
3. **AC-3: Full Data Explorer with three tabs** — Given the user opens the Full Data Explorer (via "Explore" button or "Open full view" link), then the main content area shows a tab-based explorer with: (a) **Table View** — paginated data table with sortable columns, per-column filters, and row count; (b) **Profile View** — column list (left) with column profiler (right) showing histograms for numeric columns, value counts for categorical, and cross-tab selector; (c) **Summary View** — dataset overview with row/column counts, column type breakdown, and completeness table.
4. **AC-4: Upload flow with schema validation** — Given the Upload action, when the user drops or selects a CSV/Parquet file, then the system shows a schema validation report (row count, matched columns, unrecognized columns, missing required columns). Missing required columns block the upload. **Story 20.4 acceptance mode:** because the Story 20.7 upload endpoint is not yet available, the validation report is simulated from the file's client-side schema, and on confirm the population is added to the local library as an uploaded entry with a generated ID. The real upload path (POST `/api/populations/upload`) is implemented in Story 20.7.
5. **AC-5: Scenario integration** — Given the user clicks Select on a population, when the selection completes, then `activeScenario.populationIds` is updated with the selected population's ID, `selectedPopulationId` (legacy) is synced, and the nav rail Population stage shows a completion checkmark. Clearing the selection sets `populationIds` to `[]` and `selectedPopulationId` to `""`.
6. **AC-6: Evidence placeholder tags** — Given a population in the library list, when its metadata is displayed, then it shows a source classification tag: `[Built-in]` for pre-loaded datasets, `[Generated]` for Data Fusion outputs, `[Uploaded]` for user-provided files. These are placeholder display tags — canonical evidence contracts come in EPIC-21 Story 21.2.

## Tasks / Subtasks

- [ ] Task 1: Add TanStack Table dependency and create population API types + client stubs (AC: all)
  - [ ] 1.1: Install `@tanstack/react-table` via `npm install @tanstack/react-table` in `frontend/`. This is the headless table library required by the UX spec for paginated, sortable, filterable data tables.
  - [ ] 1.2: Add new types to `frontend/src/api/types.ts` for population explorer responses:
    - ⚠️ **`ColumnInfo` already exists** at `api/types.ts:172` as `{ name: string; type: string; description: string }`. Do NOT re-declare it — reuse the existing type. The `description` field may be left as `""` in mock data where not applicable.
    - `PopulationPreviewResponse`: `{ id: string; name: string; rows: Record<string, unknown>[]; columns: ColumnInfo[]; total_rows: number; }` (uses existing `ColumnInfo`)
    - `ColumnProfileNumeric`: `{ type: "numeric"; count: number; nulls: number; null_pct: number; min: number; max: number; mean: number; median: number; std: number; percentiles: Record<string, number>; histogram_buckets: Array<{ bin_start: number; bin_end: number; count: number }>; }`
    - `ColumnProfileCategorical`: `{ type: "categorical"; count: number; nulls: number; null_pct: number; cardinality: number; value_counts: Array<{ value: string; count: number }>; }`
    - `ColumnProfileBoolean`: `{ type: "boolean"; count: number; nulls: number; null_pct: number; true_count: number; false_count: number; }`
    - `ColumnProfile`: `ColumnProfileNumeric | ColumnProfileCategorical | ColumnProfileBoolean`
    - `PopulationProfileResponse`: `{ id: string; columns: Array<{ name: string; profile: ColumnProfile }>; }`
    - `PopulationCrosstabResponse`: `{ col_a: string; col_b: string; data: Array<Record<string, unknown>>; }`
    - `PopulationUploadResponse`: `{ id: string; name: string; row_count: number; column_count: number; matched_columns: string[]; unrecognized_columns: string[]; missing_required: string[]; valid: boolean; }`
    - `PopulationLibraryItem`: extends `PopulationItem` with `{ origin: "built-in" | "generated" | "uploaded"; column_count: number; created_date: string | null; }`
  - [ ] 1.3: Add new API client functions to `frontend/src/api/populations.ts`:
    - `getPopulationPreview(id: string, params?: { offset?: number; limit?: number; sort_by?: string; order?: "asc" | "desc" }): Promise<PopulationPreviewResponse>`
    - `getPopulationProfile(id: string): Promise<PopulationProfileResponse>`
    - `getPopulationCrosstab(id: string, colA: string, colB: string): Promise<PopulationCrosstabResponse>`
    - `uploadPopulation(file: File): Promise<PopulationUploadResponse>`
    - `deletePopulation(id: string): Promise<void>`
    - These call the endpoints defined in Story 20.7 (`/api/populations/{id}/preview`, `/api/populations/{id}/profile`, `/api/populations/{id}/crosstab`, `/api/populations/upload`). Until Story 20.7 lands, the hooks will fall back to mock data.
    - `deletePopulation(id)` endpoint is also in Story 20.7. Until then: use **optimistic deletion** — remove from local state first, fire the API call, and on failure show a toast warning but do NOT revert local state. Built-in populations have no Delete button (see Task 3.2).
- [ ] Task 2: Create population mock/fixture data for explorer (AC: #2, #3, #4)
  - [ ] 2.1: Create `frontend/src/data/mock-population-explorer.ts` with:
    - `mockPopulationPreview`: 100 rows of realistic French household data (household_id, income, region, housing_type, heating_type, vehicle_type, vehicle_age, energy_consumption, carbon_emissions, household_size) with proper column metadata.
    - `mockPopulationProfile`: per-column profile data (histogram for income with 20 bins, value counts for region/housing_type/heating_type, boolean for has_vehicle).
    - `mockPopulationSummary`: dataset overview (record_count, column_count, columns with types, completeness percentages).
    - `mockCrosstabData`: cross-tabulation of region × housing_type for stacked bar chart.
  - [ ] 2.2: Add `usePopulationPreview(id)`, `usePopulationProfile(id)`, `usePopulationCrosstab(id, colA, colB)` hooks to `frontend/src/hooks/useApi.ts` following the existing pattern (try API, fall back to mock).
- [ ] Task 3: Build PopulationLibraryScreen (AC: #1, #5, #6)
  - [ ] 3.1: Create `frontend/src/components/screens/PopulationLibraryScreen.tsx` as the main Stage 2 default view. Layout: top toolbar row (title "Population Library", Upload button, selected population indicator) + population card grid below.
  - [ ] 3.2: Each population card shows: name, source tag (`[Built-in]`/`[Generated]`/`[Uploaded]` via Badge component, AC-6), row count, column count, year. Action buttons:
    - Preview (Eye icon) — all populations
    - Explore (BarChart3 icon) — all populations
    - Select (CheckCircle2 icon, highlighted when selected) — all populations
    - Edit (Pencil icon, generated only) — calls `navigateTo("population", "data-fusion")` to return to DataFusionWorkbench. Navigation shortcut only; pre-population of the workbench with saved parameters is deferred to a future story.
    - Delete (Trash2 icon, uploaded/generated only) — not shown for built-in populations.
  - [ ] 3.3: The library merges three sources into one list:
    - Built-in: `populations` from AppContext (mock or API), tagged `origin: "built-in"`
    - Generated: if `dataFusionResult` exists in AppContext, synthesize a `PopulationLibraryItem` from it, tagged `origin: "generated"`
    - Uploaded: local state `uploadedPopulations`, tagged `origin: "uploaded"`
  - [ ] 3.4: Select button updates both `activeScenario.populationIds` (via `updateScenarioField("populationIds", [id])`) and legacy `selectedPopulationId` (via `setSelectedPopulationId(id)`). Visual: selected population card gets a blue border + checkmark overlay.
  - [ ] 3.5: An "active population" indicator in the toolbar shows the currently selected population name (from `activeScenario.populationIds[0]` → look up in merged list).
  - [ ] 3.6: Delete for generated populations clears `dataFusionResult` (via `setDataFusionResult(null)`). Delete for uploaded populations removes from local state. If the deleted population is the selected one, clear selection (set `populationIds` to `[]`, `selectedPopulationId` to `""`).
- [ ] Task 4: Build Quick Preview slide-over (AC: #2)
  - [ ] 4.1: Create `frontend/src/components/population/PopulationQuickPreview.tsx`. This is a right-side slide-over overlay (same fixed-position pattern as `ScenarioEntryDialog.tsx`): backdrop (bg-black/30) + panel (right-aligned, max-w-xl, full height, overflow-y-auto).
  - [ ] 4.2: Content: header with population name + close button (X), row count badge, then a table of first 100 rows. Use a basic `<table>` with sticky header row, monospace data cells (`font-mono text-xs`), sortable column headers (click to toggle asc/desc via local state), and a per-column filter row (one `<Input>` per column in a `<tr>` immediately below the header row). Client-side text filtering against the 100 preview rows; clearing a filter input restores all visible rows.
  - [ ] 4.3: "Open full view" link at the bottom → calls `navigateTo("population", "population-explorer")` and passes the population ID via a local state or URL parameter approach. The simplest approach: PopulationStageScreen tracks `explorerPopulationId` in local state and passes it down.
  - [ ] 4.4: Close on backdrop click, Escape key, or X button.
  - [ ] 4.5: Data source: call `usePopulationPreview(id)` hook. Shows loading spinner while fetching. Falls back to mock data if API unavailable.
- [ ] Task 5: Build Full Data Explorer components (AC: #3)
  - [ ] 5.1: Create `frontend/src/components/population/PopulationExplorer.tsx` as the full-screen explorer shell. Uses the existing `Tabs` component (Radix UI) with three tabs: "Table", "Profile", "Summary". Header shows population name, "Back to library" button (calls `navigateTo("population")` — not `navigateTo("population", undefined)` or direct state mutation). **Empty state:** if `populationId` prop is `null` or `undefined` (e.g., direct hash navigation to `#population/population-explorer` without selecting a population first), render a centered message: "Select a population from the library to explore" with a "Back to Library" button calling `navigateTo("population")`.
  - [ ] 5.2: Create `frontend/src/components/population/PopulationDataTable.tsx` — Table View tab. Uses TanStack Table (`@tanstack/react-table`) for:
    - Column definitions auto-generated from data columns
    - Client-side sorting (click column header toggles asc/desc/none) — use `getSortedRowModel()`
    - Client-side filtering (text input per column header) — use `getFilteredRowModel()`
    - Pagination (50 rows per page, prev/next buttons, page indicator) — use `getPaginationRowModel()`
    - Monospace data values (`font-mono text-xs`)
    - Total row count display ("Showing 1–50 of 100,000")
    - Column types rendered as Badge in header (numeric/categorical/boolean)
    - **Pagination strategy for Story 20.4:** all row models are client-side because the explorer data is at most 100 rows from the preview endpoint mock. The UX spec notes "server-side pagination for 500K rows" — this migration happens in Story 20.7 by switching to TanStack Table `manualPagination` mode and wiring `offset`/`limit` params to `getPopulationPreview`. Do not attempt server-side pagination in this story.
  - [ ] 5.3: Create `frontend/src/components/population/PopulationProfiler.tsx` — Profile View tab. Two-column layout: column list sidebar (left, scrollable) + profile panel (right).
    - Column list: clickable items showing column name + type badge. First column selected by default.
    - Profile panel content varies by type:
      - **Numeric**: Histogram (Recharts BarChart, 20 bins, Slate 400 fill), percentile bar (P10/P25/P50/P75/P90 as a horizontal stacked bar), stats card (min, max, mean, median, std, null count), cross-tab selector dropdown.
      - **Categorical**: Horizontal bar chart of value counts (top 20, Recharts BarChart layout="vertical"), cardinality badge, cross-tab selector.
      - **Boolean**: True/False proportion bar with counts.
    - Cross-tab: when a second column is selected, show a stacked bar chart using `<BarChart>` with `<Bar stackId="cross-tab">` for each category of the second column (Recharts has no `StackedBarChart` export — stacking is done via the `stackId` prop on regular `<Bar>` elements). See `TransitionChart.tsx:121-125` for the established pattern.
  - [ ] 5.4: Create `frontend/src/components/population/PopulationSummaryView.tsx` — Summary View tab.
    - Dataset overview: row count, column count, estimated memory size
    - Column type breakdown: "N numeric, M categorical, K boolean" as Badge pills
    - Completeness table: columns × null percentage, rendered as a compact table. Columns with >10% nulls highlighted amber, >50% highlighted red.
    - Top-level stats per column in a compact card grid
  - [ ] 5.5: Chart colors: Slate 400 (`#94a3b8`) primary, Blue 500 (`#3b82f6`) secondary, Violet 500 (`#8b5cf6`) tertiary. Use CSS custom properties or direct hex values consistent with existing chart-theme.ts.
- [ ] Task 6: Build PopulationUploadZone component (AC: #4)
  - [ ] 6.1: Create `frontend/src/components/population/PopulationUploadZone.tsx`. Drop zone: `border-2 border-dashed border-slate-300` idle, `border-blue-500 bg-blue-50` on drag-over (per UX spec). Accepts `.csv` and `.parquet` files only (via `accept` attribute and drag event filtering).
  - [ ] 6.2: On file drop/select: call `uploadPopulation(file)` API. Show loading state. On response, display schema validation report:
    - ✓ Row count, column count (green badges)
    - ✓ Matched columns (green list items)
    - ⚠ Unrecognized columns (amber list items, with note "will be kept but not used")
    - ✗ Missing required columns (red list items, blocks confirmation)
  - [ ] 6.3: Confirm button (disabled if `missing_required.length > 0`). On confirm: add population to local `uploadedPopulations` state in PopulationStageScreen, close the upload overlay, show success toast.
  - [ ] 6.4: **Story 20.4 upload mode (no backend):** do not call `uploadPopulation(file)` API in this story. Instead, simulate the schema validation client-side by reading the file header (first line of CSV, or Parquet schema if parseable). Build the `PopulationUploadResponse`-shaped object with `matched_columns` (columns whose names appear in the known schema) and `unrecognized_columns`. Required columns to validate against: `["household_id", "income", "region", "household_size"]` (minimum required schema for ReformLab scenarios). Show the validation report UI as specified in Task 6.2. On confirm, generate a local ID (`"uploaded-${Date.now()}"`) and add to `uploadedPopulations` state. Story 20.7 replaces this with the real `POST /api/populations/upload` endpoint.
  - [ ] 6.5: The upload flow opens as a fixed-position overlay (same pattern as save/load dialogs in PoliciesStageScreen).
- [ ] Task 7: Rewrite PopulationStageScreen with sub-view routing (AC: #1, #2, #3)
  - [ ] 7.1: Replace the thin wrapper in `PopulationStageScreen.tsx` with a stateful coordinator that reads `activeSubView` from AppContext and renders the appropriate sub-view:
    - `activeSubView === null` or `activeSubView === undefined`: Render `PopulationLibraryScreen` (default)
    - `activeSubView === "data-fusion"`: Render existing `DataFusionWorkbench` (unchanged)
    - `activeSubView === "population-explorer"`: Render `PopulationExplorer`
  - [ ] 7.2: Track local state for: `previewPopulationId` (which population's Quick Preview is open), `explorerPopulationId` (which population the explorer is showing), `uploadedPopulations` (populations added via upload).
  - [ ] 7.3: Pass callbacks down to PopulationLibraryScreen: `onPreview(id)`, `onExplore(id)`, `onSelect(id)`, `onDelete(id)`, `onUpload()`, `onBuildNew()` (navigates to data-fusion sub-view).
  - [ ] 7.4: The Quick Preview slide-over renders at the PopulationStageScreen level (above the library content), controlled by `previewPopulationId`.
  - [ ] 7.5: When Data Fusion completes (onPopulationGenerated fires), auto-navigate back to the library by calling `navigateTo("population")` (not by directly mutating state) and show the newly generated population with `origin: "generated"`.
- [ ] Task 8: Update nav rail completion, help content, and routing (AC: #5, #6)
  - [ ] 8.1: In `WorkflowNavRail.tsx`, the Population completion check already works via `selectedPopulationId || dataFusionResult !== null`. Update it to also check `activeScenario?.populationIds?.length > 0` as the primary signal (with fallback to legacy). To show the selected population **name** (instead of raw ID) in the summary line: add `populations: PopulationItem[]` to `WorkflowNavRailProps` and update `getSummary` for `"population"` to: `populations.find(p => p.id === selectedPopulationId)?.name ?? selectedPopulationId ?? null`. Update the `WorkflowNavRail` call site in `LeftPanel.tsx` (or wherever it is rendered) to pass `populations={populations}` from `useAppState()`.
  - [ ] 8.2: In `help-content.ts`, update the `"population"` entry to describe the new Population Library, Quick Preview, Data Explorer, and Upload flows. Add a `"population-explorer"` entry for the Full Data Explorer help.
  - [ ] 8.3: In `App.tsx`, no changes needed — `PopulationStageScreen` handles sub-view routing internally (reads `activeSubView` from `useAppState()`). The existing `{activeStage === "population" ? <PopulationStageScreen /> : null}` line continues to work.
- [ ] Task 9: Add tests (AC: all)
  - [ ] 9.1: Create `frontend/src/components/screens/__tests__/PopulationStageScreen.test.tsx` with tests for:
    - Default view renders PopulationLibraryScreen with population cards (AC-1)
    - Quick Preview opens on Preview button click and shows table rows (AC-2)
    - Quick Preview closes on backdrop click and Escape (AC-2)
    - Data Explorer opens on Explore button click with three tabs (AC-3)
    - Data Explorer Profile tab shows histogram for numeric column (AC-3)
    - Upload overlay opens and shows drag-and-drop zone (AC-4)
    - Select button updates `activeScenario.populationIds` and `selectedPopulationId` (AC-5)
    - Population cards show correct origin tags ([Built-in]/[Generated]/[Uploaded]) (AC-6)
    - Delete clears selection when deleting the selected population (AC-5)
  - [ ] 9.2: Create `frontend/src/components/population/__tests__/PopulationDataTable.test.tsx` with tests for:
    - Renders rows and column headers from mock data
    - Sorting toggles on column header click
    - Pagination shows correct page range
    - Filter input narrows visible rows
  - [ ] 9.3: Create `frontend/src/components/population/__tests__/PopulationProfiler.test.tsx` with tests for:
    - Column list renders all columns from profile data
    - Selecting a numeric column shows histogram and stats
    - Selecting a categorical column shows value counts bar chart
    - Cross-tab selector triggers crosstab data fetch
  - [ ] 9.4: Add a Story 20.4 section to `frontend/src/__tests__/workflows/analyst-journey.test.tsx` with:
    - Navigate to `#population`, verify library list is visible with population cards
    - Click "Build New Population" opens Data Fusion Workbench (data-fusion sub-view)
    - Navigate to `#population/population-explorer`, verify explorer tabs render
    - Select a population, verify nav rail shows completion checkmark
  - [ ] 9.5: Verify existing tests pass — no regressions in:
    - `DataFusionWorkbench` tests (component unchanged, still renders when sub-view is "data-fusion")
    - `WorkflowNavRail` tests (population completion logic extended but backward-compatible)
    - All Story 20.3 tests (PoliciesStageScreen, analyst-journey)
  - [ ] 9.6: Mock patterns for tests:
    - Mock `@/api/populations` with all new functions
    - Mock `@/contexts/AppContext` with `useAppState` returning mock state
    - Use `vi.mock("@/hooks/useApi")` for preview/profile/crosstab hooks
    - Use `setupResizeObserver()` for Recharts tests (existing helper)
- [ ] Task 10: Run quality gates (AC: all)
  - [ ] 10.1: `npm run typecheck` — 0 errors
  - [ ] 10.2: `npm run lint` — 0 errors (pre-existing fast-refresh warnings OK)
  - [ ] 10.3: `npm test` — all tests pass, 0 failures, 0 regressions
  - [ ] 10.4: `uv run ruff check src/ tests/` — 0 errors
  - [ ] 10.5: `uv run mypy src/` — passes

## Dev Notes

### Architecture Constraints

- **No backend changes in this story.** Backend population explorer endpoints (`/api/populations/{id}/preview`, `/api/populations/{id}/profile`, `/api/populations/{id}/crosstab`, `POST /api/populations/upload`) are delivered in Story 20.7. This story builds the frontend UI with mock data fallbacks.
- **No router library.** Continue using hash-based routing via `window.location.hash`. Stage 2 is `#population`. Sub-views: `#population/data-fusion` (existing), `#population/population-explorer` (new).
- **Dual state model persists.** `activeScenario.populationIds` (new canonical, array) coexists with `selectedPopulationId` (legacy, single string). This story sets both on population select/clear. Full migration to `activeScenario`-only is deferred to Story 20.5–20.6.
- **Dialog/Sheet stubs.** shadcn `Sheet` component is a minimal stub (hidden div). The Quick Preview slide-over uses the inline fixed-position overlay pattern established in `ScenarioEntryDialog.tsx` — right-side positioned panel with backdrop.
- **Population ≠ Scenario.** Population select/delete are population operations. Scenario save/clone are separate (via `saveCurrentScenario`, `cloneCurrentScenario` in AppContext). These must remain separate.
- **Immutable scenario updates.** `WorkspaceScenario` is treated as immutable — update via `updateScenarioField()` which internally does `{ ...current, [field]: value }`.
- **Mock data fallback pattern.** The existing `useApi.ts` hooks try the real API first and fall back to mock data if the API is unavailable. New hooks (`usePopulationPreview`, `usePopulationProfile`, `usePopulationCrosstab`) follow this same pattern.

### Key Design Decision: Population Library as Entry Point

The UX specification (§ Stage 2: POPULATION, lines 1422–1543) requires:
- "Population Library is the entry point. The user sees all available populations first, then chooses to explore, build, or upload."
- "Quick Preview (slide-over) for spot-checks. 10-second interaction: open, scan, close."
- "Full Data Explorer for deep investigation. Tab-based: Table, Profile, Summary."

The current `PopulationStageScreen` renders only `DataFusionWorkbench`. This story replaces it with a population workspace:

```
┌────────────────────────────────────────────────────────────────┐
│ Toolbar: Population Library  [Upload] [Build New]  Selected: █ │
├────────────────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│ │FR-2024   │ │FR-2023   │ │EU-SILC   │ │My Upload │          │
│ │[Built-in]│ │[Built-in]│ │[Built-in]│ │[Uploaded]│          │
│ │100K rows │ │100K rows │ │50K rows  │ │10K rows  │          │
│ │14 cols   │ │14 cols   │ │12 cols   │ │8 cols    │          │
│ │          │ │          │ │          │ │          │          │
│ │[👁][📊]  │ │[👁][📊]  │ │[👁][📊]  │ │[👁][📊]  │          │
│ │[✓][🗑]  │ │[✓]      │ │[✓]      │ │[✓][🗑]  │          │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│                                                                │
│ ┌──────────────┐                                               │
│ │ [Generated]  │  ← appears when dataFusionResult is set       │
│ │ Fused Pop.   │                                               │
│ │ 75K rows     │                                               │
│ │ [👁][📊][✓]  │                                               │
│ └──────────────┘                                               │
└────────────────────────────────────────────────────────────────┘

Quick Preview (slide-over, right side):
┌──────────────────────────────────────────────────────────┐
│ ┌───────────────────────────────────────┐                │
│ │ FR-2024                      [Close]  │                │
│ │ 100,000 rows                          │                │
│ ├─────┬──────────┬────────┬─────────────┤                │
│ │ ID  │ income   │ region │ housing_type│                │
│ ├─────┼──────────┼────────┼─────────────┤                │
│ │ 1   │ 24,500   │ IDF    │ apartment   │                │
│ │ 2   │ 31,200   │ PACA   │ house       │                │
│ │ ... │          │        │             │                │
│ ├─────┴──────────┴────────┴─────────────┤                │
│ │          [Open full view →]           │                │
│ └───────────────────────────────────────┘                │
└──────────────────────────────────────────────────────────┘

Full Data Explorer (replaces library content):
┌──────────────────────────────────────────────────────────┐
│ ← Back to Library    FR-2024 (100K rows, 14 cols)        │
├──────────────────────────────────────────────────────────┤
│ [Table] [Profile] [Summary]                              │
│──────────────────────────────────────────────────────────│
│ Table tab:                                               │
│ ┌─────┬──────────┬────────┬─────────────┬──────────────┐ │
│ │ ID  │ income ▲ │ region │ housing_type│ heating_type │ │
│ │ [f] │ [filter] │ [f]    │ [f]         │ [f]          │ │
│ ├─────┼──────────┼────────┼─────────────┼──────────────┤ │
│ │ ... │          │        │             │              │ │
│ ├─────┴──────────┴────────┴─────────────┴──────────────┤ │
│ │ Showing 1–50 of 100,000        [< Prev] [Next >]     │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                          │
│ Profile tab:                                             │
│ ┌──────────┬─────────────────────────────────────────┐   │
│ │ Columns  │ income (numeric)                        │   │
│ │ ───────  │ ┌───────────────────────────────┐       │   │
│ │ > income │ │ ██████████████████████         │       │   │
│ │   region │ │ ███████████████████████████    │       │   │
│ │   housing│ │ █████████████████████████████  │       │   │
│ │   heating│ │ ██████████████████████         │       │   │
│ │   vehicle│ │ ████████████████               │       │   │
│ │          │ └───────────────────────────────┘       │   │
│ │          │ min: 0  max: 120K  mean: 28.5K         │   │
│ │          │ median: 25K  std: 15.2K  nulls: 0      │   │
│ │          │ Cross-tab: [Select column ▾]            │   │
│ └──────────┴─────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

### Sub-View Routing Within PopulationStageScreen

PopulationStageScreen reads `activeSubView` from AppContext (via `useAppState()`) and renders:

| `activeSubView` | Component | Description |
|---|---|---|
| `null` / `undefined` | `PopulationLibraryScreen` | Default: population library list |
| `"data-fusion"` | `DataFusionWorkbench` | Existing data fusion flow (unchanged) |
| `"population-explorer"` | `PopulationExplorer` | Full data explorer with tabs |

Navigation between sub-views uses `navigateTo("population", subView)` from AppContext. This updates `window.location.hash` (e.g., `#population/population-explorer`). The hash routing infrastructure from Story 20.1 already handles this.

### Component Architecture

```
PopulationStageScreen (stateful coordinator)
├─ PopulationLibraryScreen (default view)
│   ├─ Population cards (built-in + generated + uploaded)
│   ├─ Toolbar (Upload button, Build New button, selection indicator)
│   └─ Action callbacks (preview, explore, select, delete, upload)
├─ PopulationQuickPreview (slide-over overlay, controlled by previewPopulationId)
│   ├─ Sortable table of first 100 rows
│   └─ "Open full view" link
├─ PopulationExplorer (full-screen, subView === "population-explorer")
│   ├─ PopulationDataTable (Table tab — TanStack Table)
│   ├─ PopulationProfiler (Profile tab — column profiler with charts)
│   │   ├─ Histogram (Recharts BarChart, numeric columns)
│   │   ├─ ValueCountsChart (Recharts BarChart layout="vertical", categorical)
│   │   ├─ CrosstabChart (Recharts BarChart + Bar with stackId, see TransitionChart.tsx)
│   │   └─ PercentileBar (custom component)
│   └─ PopulationSummaryView (Summary tab)
├─ PopulationUploadZone (overlay, triggered from toolbar)
├─ DataFusionWorkbench (subView === "data-fusion", existing component)
```

### New Dependencies

| Package | Version | Why |
|---|---|---|
| `@tanstack/react-table` | `^8.x` (latest stable) | Headless table library for paginated, sortable, filterable data table. Required by UX spec for Table View. |

No other new dependencies. Recharts (charts), Radix Tabs (tab navigation), and all Shadcn/ui components are already installed.

### Current Component Reuse Strategy

| Existing Component | Reuse in 20.4 | Changes Required |
|---|---|---|
| `DataFusionWorkbench` | ✅ Reused as-is | None — renders when sub-view is "data-fusion" |
| `PopulationPreview` | ⚠️ Reference only | Not reused directly; it shows Data Fusion result summary, not raw data rows. PopulationQuickPreview is a different component (raw row table). |
| `PopulationDistributionChart` | ✅ Can reuse for histograms | None — already renders bar charts from data array |
| `PopulationValidationPanel` | ❌ Not used in this story | It's for Data Fusion validation results, not schema validation on upload |
| `WorkbenchStepper` | ❌ Not used | Still used by DataFusionWorkbench |
| `Tabs` / `TabsList` / `TabsTrigger` / `TabsContent` | ✅ Reused for explorer tabs | None |
| `Badge` | ✅ Reused for origin tags, type badges | None |
| `Button` | ✅ Reused for actions | None |
| `Input` | ✅ Reused for column filters | None |

### State Management in PopulationStageScreen

PopulationStageScreen becomes the stateful coordinator for Stage 2. State owned locally:

| State | Type | Source |
|---|---|---|
| `previewPopulationId` | `string \| null` | Local — which population's Quick Preview is open |
| `explorerPopulationId` | `string \| null` | Local — which population the explorer is showing |
| `uploadedPopulations` | `PopulationLibraryItem[]` | Local — populations added via upload (persists in session only) |
| `uploadDialogOpen` | `boolean` | Local — upload overlay state |

State consumed from AppContext (via `useAppState()`):

| State | Usage |
|---|---|
| `populations` | Built-in population list |
| `populationsLoading` | Loading indicator |
| `dataFusionSources` | Passed to DataFusionWorkbench |
| `dataFusionMethods` | Passed to DataFusionWorkbench |
| `dataFusionResult` | Synthesized into library as "generated" entry |
| `setDataFusionResult` | Clear generated population on delete |
| `activeSubView` | Determines which sub-view to render |
| `navigateTo` | Navigate between sub-views |
| `activeScenario` | Read `populationIds` for selection state |
| `updateScenarioField` | Write `populationIds` on select/clear |
| `selectedPopulationId` | Legacy sync for SimulationRunnerScreen |
| `setSelectedPopulationId` | Legacy sync setter |

### Population Library Merge Logic

The library shows a unified list from three sources:

```tsx
const mergedPopulations = useMemo((): PopulationLibraryItem[] => {
  // 1. Built-in populations from API/mock
  const builtIn: PopulationLibraryItem[] = populations.map((p) => ({
    ...p,
    origin: "built-in" as const,
    column_count: 14, // Placeholder: Story 20.7 returns real column_count from API
    created_date: null,
  }));

  // 2. Generated population from Data Fusion (if any)
  // Known limitation: "data-fusion-result" is an in-memory ID that does not survive
  // page reload. If activeScenario.populationIds contains "data-fusion-result" after
  // a reload (restored from localStorage) but dataFusionResult is null, treat it as
  // an empty selection — do not crash or show a missing population.
  const generated: PopulationLibraryItem[] = dataFusionResult
    ? [{
        id: "data-fusion-result",
        name: "Fused Population",
        households: dataFusionResult.summary.record_count,
        source: "Data Fusion",
        year: new Date().getFullYear(),
        origin: "generated" as const,
        column_count: dataFusionResult.summary.column_count,
        created_date: new Date().toISOString(),
      }]
    : [];

  // 3. Uploaded populations (local state)
  return [...builtIn, ...generated, ...uploadedPopulations];
}, [populations, dataFusionResult, uploadedPopulations]);
```

### TanStack Table Integration Pattern

TanStack Table is headless — it provides logic, we provide the UI. Pattern:

```tsx
import { useReactTable, getCoreRowModel, getSortedRowModel, getFilteredRowModel, getPaginationRowModel, flexRender, type ColumnDef, type SortingState } from "@tanstack/react-table";

const columns: ColumnDef<Record<string, unknown>>[] = columnInfos.map((col) => ({
  accessorKey: col.name,
  header: col.name,
  cell: (info) => <span className="font-mono text-xs">{String(info.getValue() ?? "")}</span>,
}));

const table = useReactTable({
  data: rows,
  columns,
  getCoreRowModel: getCoreRowModel(),
  getSortedRowModel: getSortedRowModel(),
  getFilteredRowModel: getFilteredRowModel(),
  getPaginationRowModel: getPaginationRowModel(),
  state: { sorting, columnFilters, pagination },
  onSortingChange: setSorting,
  onColumnFiltersChange: setColumnFilters,
  onPaginationChange: setPagination,
});
```

### Interaction with Legacy State

| New State | Legacy State (synced alongside) | Why |
|---|---|---|
| `activeScenario.populationIds` | `selectedPopulationId` | `SimulationRunnerScreen` reads `selectedPopulationId` in the runner header. Migration deferred to 20.6. |
| `activeSubView` | ⚠️ No legacy equivalent | Sub-view routing is new (Story 20.1 infrastructure). |
| `dataFusionResult` | ⚠️ Used directly | Data Fusion result is shown as a "generated" entry in the library. |

### Nav Rail Completion After Population Selection

After population is selected:
- **Policies** (unchanged): Depends on `activeScenario?.portfolioName`
- **Population** (`activeScenario?.populationIds?.length > 0 || selectedPopulationId || dataFusionResult`): **Complete** ✅
- **Engine** (unchanged): Depends on `activeScenario !== null`
- **Results** (unchanged): Depends on `results.length > 0`

After clear:
- **Population**: **Incomplete** (populationIds is empty, selectedPopulationId is empty)

### Error Handling Pattern

Follow the established pattern from `PoliciesStageScreen`:

```tsx
try {
  const preview = await getPopulationPreview(id);
  // use preview data
} catch (err) {
  if (err instanceof ApiError) {
    toast.error(`${err.what} — ${err.why}`, { description: err.fix });
  } else if (err instanceof Error) {
    toast.warning("Preview unavailable", { description: err.message });
  }
}
```

### Chart Colors (from UX spec)

| Usage | Color | Tailwind Class / CSS Var |
|---|---|---|
| Primary histogram bars | Slate 400 (`#94a3b8`) | `fill: #94a3b8` or `var(--chart-baseline)` |
| Secondary (cross-tab) | Blue 500 (`#3b82f6`) | `fill: #3b82f6` or `var(--chart-reform-a)` |
| Tertiary (cross-tab) | Violet 500 (`#8b5cf6`) | `fill: #8b5cf6` or `var(--chart-reform-b)` |

These match the existing `chart-theme.ts` CSS variables.

### Files to Create

| File | Purpose |
|---|---|
| `frontend/src/components/population/PopulationDataTable.tsx` | TanStack Table for paginated, sortable, filterable population data (Table View tab) |
| `frontend/src/components/population/PopulationProfiler.tsx` | Visual column profiler: histograms, value counts, cross-tabs, stats (Profile View tab) |
| `frontend/src/components/population/PopulationSummaryView.tsx` | Dataset-level overview: row/column counts, type breakdown, completeness (Summary View tab) |
| `frontend/src/components/population/PopulationUploadZone.tsx` | Drag-and-drop file upload with schema validation report |
| `frontend/src/components/population/PopulationQuickPreview.tsx` | Right-side slide-over panel showing first 100 rows |
| `frontend/src/components/population/PopulationExplorer.tsx` | Full-screen data explorer shell with Tab navigation |
| `frontend/src/components/screens/PopulationLibraryScreen.tsx` | Population library list with cards and action buttons |
| `frontend/src/data/mock-population-explorer.ts` | Mock data for population preview, profile, summary, crosstab |
| `frontend/src/components/screens/__tests__/PopulationStageScreen.test.tsx` | Unit tests for population stage |
| `frontend/src/components/population/__tests__/PopulationDataTable.test.tsx` | Unit tests for data table |
| `frontend/src/components/population/__tests__/PopulationProfiler.test.tsx` | Unit tests for profiler |

### Files to Modify

| File | Changes |
|---|---|
| `frontend/package.json` | Add `@tanstack/react-table` dependency |
| `frontend/src/api/types.ts` | Add population explorer response types (PopulationPreviewResponse, ColumnProfile, PopulationProfileResponse, PopulationCrosstabResponse, PopulationUploadResponse, PopulationLibraryItem) |
| `frontend/src/api/populations.ts` | Add `getPopulationPreview`, `getPopulationProfile`, `getPopulationCrosstab`, `uploadPopulation`, `deletePopulation` functions |
| `frontend/src/hooks/useApi.ts` | Add `usePopulationPreview(id)`, `usePopulationProfile(id)`, `usePopulationCrosstab(id, colA, colB)` hooks with mock data fallback |
| `frontend/src/components/screens/PopulationStageScreen.tsx` | Replace thin wrapper with stateful coordinator: sub-view routing, library + explorer + upload + data fusion switching, Quick Preview overlay, scenario integration |
| `frontend/src/components/layout/WorkflowNavRail.tsx` | Extend Population completion check to use `activeScenario?.populationIds?.length > 0` as primary signal. Add `populations: PopulationItem[]` to `WorkflowNavRailProps`. Update `getSummary` for `"population"` to look up name from populations list. |
| `frontend/src/App.tsx` | Pass `populations={populations}` from `useAppState()` to `<WorkflowNavRail>` call site (needed for population name display in nav rail). |
| `frontend/src/components/help/help-content.ts` | Update `"population"` entry, add `"population-explorer"` entry for Full Data Explorer help |
| `frontend/src/__tests__/workflows/analyst-journey.test.tsx` | Add Story 20.4 section: navigate to population, verify library, verify explorer tabs, verify selection updates nav rail |

### Files NOT Modified

| File | Why |
|---|---|
| `frontend/src/contexts/AppContext.tsx` | All needed actions exist: `updateScenarioField`, `setSelectedPopulationId`, `setDataFusionResult`, `navigateTo`. No new state or actions required. |
| `frontend/src/types/workspace.ts` | SubView already includes `"data-fusion"` and `"population-explorer"`. STAGES already maps population to both sub-views. |
| `frontend/src/components/screens/DataFusionWorkbench.tsx` | Reused as-is — same props interface, rendered when sub-view is "data-fusion". |
| `frontend/src/components/simulation/PopulationPreview.tsx` | Different purpose (Data Fusion result summary). Not modified. |
| `frontend/src/components/simulation/PopulationDistributionChart.tsx` | Can be reused for histograms in PopulationProfiler. Not modified. |
| Any backend files (`src/reformlab/`) | Backend endpoints are in Story 20.7. |

### Shadcn Components Used

From the available component library:
- `Badge` — origin tags, type badges, count badges
- `Button` — action buttons, toolbar buttons
- `Input` — column filters in data table, file name input
- `Tabs` / `TabsList` / `TabsTrigger` / `TabsContent` — explorer tab navigation
- `Separator` — visual separator in toolbar
- `Tooltip` — column header tooltips in data table
- `ScrollArea` — scrollable column list in profiler

Lucide icons used: `Eye`, `BarChart3`, `CheckCircle2`, `Trash2`, `Pencil`, `Upload`, `Plus`, `X`, `ArrowUp`, `ArrowDown`, `ArrowUpDown`, `ChevronLeft`, `ChevronRight`, `FileSpreadsheet`, `AlertTriangle`, `Search`

### Project Structure Notes

- New `components/population/` directory — a departure from putting everything in `components/simulation/`. Justified because the population components are a self-contained subsystem with 6+ files. The `simulation/` directory already has 15+ files.
- `PopulationLibraryScreen.tsx` in `components/screens/` — matches existing screen naming convention.
- Test files mirror source structure: `components/population/__tests__/` and `components/screens/__tests__/`.
- Mock data in `data/mock-population-explorer.ts` — follows `data/mock-data.ts` pattern.

### EPIC-21 Extensibility Note

Story 20.4 does not implement EPIC-21 features, but the population library design accommodates future extensions:
- `PopulationLibraryItem.origin` uses simple string values (`"built-in"`, `"generated"`, `"uploaded"`) — EPIC-21 Story 21.2 will replace these with canonical `origin`/`access_mode`/`trust_status` contracts from the `EvidenceAssetDescriptor` type.
- The population card metadata section has space for additional metadata fields. EPIC-21 adds `access_mode` and `trust_status` badges alongside the existing origin tag.
- The profile and summary views accept extensible metadata — new fields from EPIC-21 can be added without restructuring the component hierarchy.
- **Do NOT invent ad-hoc label systems** for data provenance. Use exactly `[Built-in]`, `[Generated]`, `[Uploaded]` as display text until EPIC-21 delivers the canonical evidence asset descriptor.

### Testing Patterns

**Mocking AppContext for PopulationStageScreen tests:**
```tsx
vi.mock("@/contexts/AppContext", () => ({
  useAppState: vi.fn(),
}));
```

**Mocking population API:**
```tsx
vi.mock("@/api/populations", () => ({
  listPopulations: vi.fn(),
  getPopulationPreview: vi.fn(),
  getPopulationProfile: vi.fn(),
  getPopulationCrosstab: vi.fn(),
  uploadPopulation: vi.fn(),
  deletePopulation: vi.fn(),
}));
```

**Testing TanStack Table:** TanStack Table renders real DOM elements (no canvas/SVG). Test sorting by clicking column headers and asserting row order changes. Test pagination by asserting "Showing X–Y of Z" text updates.

**Testing Recharts charts:** Use `setupResizeObserver()` polyfill (from `helpers.ts`). Assert chart container renders with correct `aria-label`. Do not assert specific SVG path values (brittle).

### References

- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Stage 2: POPULATION, lines 1422–1543]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Population Library entry point, line 1425]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Quick Preview slide-over, lines 1460–1467]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Full Data Explorer tabs, lines 1469–1499]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Upload flow, lines 1446–1457]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — TanStack Table decision, line 1527]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Chart colors, line 1497]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — New components list, lines 1693–1708]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Backend support endpoints, lines 1500–1520]
- [Source: `_bmad-output/planning-artifacts/prd.md` — FR36–FR42 population requirements]
- [Source: `_bmad-output/planning-artifacts/prd.md` — NFR1 performance target (100K households)]
- [Source: `_bmad-output/planning-artifacts/prd.md` — NFR3 memory management (500K households)]
- [Source: `_bmad-output/planning-artifacts/architecture.md` — Section 5.6 Population subsystem]
- [Source: `_bmad-output/planning-artifacts/architecture.md` — API endpoints table]
- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 20.4 BKL-2004, lines 2072–2090]
- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 20.7 backend APIs, lines 2135–2150]
- [Source: `_bmad-output/planning-artifacts/epics.md` — EPIC-21 coordination note, line 2014]
- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 21.2 evidence contracts, lines 2219–2252]
- [Source: `frontend/src/types/workspace.ts` — SubView includes "data-fusion" and "population-explorer", line 19–23]
- [Source: `frontend/src/types/workspace.ts` — STAGES population activeFor, line 61]
- [Source: `frontend/src/types/workspace.ts` — WorkspaceScenario.populationIds, line 48]
- [Source: `frontend/src/components/screens/PopulationStageScreen.tsx` — Current thin wrapper, 24 lines]
- [Source: `frontend/src/components/screens/DataFusionWorkbench.tsx` — DataFusion 5-step flow]
- [Source: `frontend/src/components/simulation/PopulationDistributionChart.tsx` — Reusable bar chart]
- [Source: `frontend/src/components/simulation/PopulationPreview.tsx` — Data Fusion result summary]
- [Source: `frontend/src/api/populations.ts` — Current listPopulations() only]
- [Source: `frontend/src/api/types.ts` — PopulationItem, lines 140–146]
- [Source: `frontend/src/hooks/useApi.ts` — usePopulations() with mock fallback, lines 42–78]
- [Source: `frontend/src/contexts/AppContext.tsx` — selectedPopulationId, dataFusionResult, updateScenarioField]
- [Source: `frontend/src/data/mock-data.ts` — mockPopulations, lines 63–85]
- [Source: `frontend/src/components/ui/tabs.tsx` — Radix Tabs component]
- [Source: `frontend/src/components/ui/sheet.tsx` — Minimal stub (not used)]
- [Source: `frontend/src/App.tsx` — Stage routing, line 207]
- [Source: `frontend/src/components/layout/WorkflowNavRail.tsx` — Population completion logic, lines 52–53]
- [Source: `frontend/src/components/screens/PoliciesStageScreen.tsx` — Pattern reference for stateful stage screen]
- [Source: `frontend/src/components/scenario/ScenarioEntryDialog.tsx` — Fixed overlay dialog pattern]
- [Source: `_bmad-output/implementation-artifacts/20-3-build-policies-and-portfolio-stage-with-inline-composition.md` — Story 20.3 patterns for inline layout, dialog overlays, scenario integration]
- [Source: `_bmad-output/implementation-artifacts/20-1-implement-canonical-scenario-model-and-stage-aware-routing-shell.md` — Stage routing, activeSubView, navigateTo]

## Dev Agent Record

### Agent Model Used

_To be filled by dev agent_

### Debug Log References

_To be filled by dev agent_

### Completion Notes List

_To be filled by dev agent_

### File List

_To be filled by dev agent_
