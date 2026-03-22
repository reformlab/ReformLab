
# Story 18.4: Restructure Results View with Tabs and Hierarchy

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a policy analyst who has just run a simulation,
I want the results view to be organized into clear sections with a metadata header, tabbed content, and proper action hierarchy,
so that I can quickly find key outcomes, explore detailed indicators, and access export/comparison actions without scanning a flat list of undifferentiated buttons.

## Acceptance Criteria

1. **AC-1: Run metadata header** — Given the results view (`App.tsx` viewMode="results"), when displayed after a completed simulation run, then a header section shows: run ID (first 8 chars, monospace), policy label (template name or portfolio name), year range badge, and status badge. The header uses the same `policyLabel()` derivation pattern as `ResultDetailView.tsx:47-51` (portfolio_name > template_name > fallback). When `runResult` is null (legacy/mock mode), the header shows the selected scenario name with a "mock data" badge.
   - **Year range badge**: derived from `runResult.years` array as `${years[0]}–${years[years.length - 1]}`; shows "—" when `runResult` is null or `years` is empty.
   - **Status badge mapping**: `runResult.success === true` → `variant="success"` label "completed"; `runResult.success === false` → `variant="destructive"` label "failed"; `runResult === null` → `variant="default"` label "mock data".

2. **AC-2: Tabbed results layout** — Given the results view, when displayed, then content is organized into shadcn `Tabs` with three tabs:
   - **Overview** (default): `DistributionalChart` + summary stat cards grid (3 columns on xl)
   - **Data & Export**: CSV and Parquet export buttons with format descriptions; disabled with "Run a simulation first" message when no `runResult`
   - **Detail**: Embeds `ResultDetailView` when a `ResultDetailResponse` is available; shows "Run a simulation to see detailed results" placeholder otherwise
   The tab styling follows the ComparisonDashboardScreen pattern: `TabsList className="w-full justify-start border-b border-slate-200 bg-white"` with content inside a `rounded-lg border border-slate-200 bg-white` wrapper.

3. **AC-3: Action hierarchy** — Given the results view, when action buttons are displayed, then:
   - "Compare Runs" is a **primary** button (default variant) — placed in the header row, right-aligned
   - "Behavioral Decisions" is **secondary** (outline variant) — placed in the header row, right-aligned, only visible when `runResult?.run_id` exists
   - "Run Again" is **tertiary** (ghost variant) — placed in the header row, right-aligned
   - Export buttons (CSV, Parquet) appear **only** in the "Data & Export" tab, not in the header action bar. This eliminates the current flat row of 5 undifferentiated buttons.

4. **AC-4: Real summary statistics** — Given a completed simulation run with indicator data available in `decileData`, when the Overview tab is displayed, then:
   - Summary stat cards show **computed values derived from `decileData`**: mean delta across deciles, max positive impact (decile + value), max negative impact (decile + value)
   - These replace the hardcoded `mockSummaryStats` import in the results view
   - If `decileData` is empty or all-zero, show placeholder cards with "—" values and "No indicator data" note
   - The `mockSummaryStats` import is removed from `App.tsx` only if no longer used anywhere in the file (check the "run" view at lines 333-348 which also uses `mockSummaryStats`; if still used there, keep the import)

5. **AC-5: Results as standalone screen component** — Given the current inline results rendering in `App.tsx:360-381`, when this story is complete, then:
   - Results are rendered by a dedicated `ResultsOverviewScreen` component in `components/screens/`
   - `App.tsx` passes props and renders `<ResultsOverviewScreen>` in the `viewMode === "results"` block
   - The new component is consistent with the screen component pattern used by `ComparisonDashboardScreen`, `BehavioralDecisionViewerScreen`, etc.

## Tasks / Subtasks

- [x] Task 1: Create ResultsOverviewScreen component (AC: 1, 2, 3, 5)
  - [x] 1.1: Create `frontend/src/components/screens/ResultsOverviewScreen.tsx` with props interface matching what App.tsx currently passes to the inline results JSX
  - [x] 1.2: Implement run metadata header with run_id, policy label, year range badge, status badge, and right-aligned action buttons (Compare / Decisions / Run Again)
  - [x] 1.3: Implement tabbed layout with Overview / Data & Export / Detail tabs using shadcn Tabs
  - [x] 1.4: Overview tab: DistributionalChart + summary stats grid
  - [x] 1.5: Data & Export tab: CSV/Parquet export buttons with format descriptions, disabled state when no run data
  - [x] 1.6: Detail tab: embed ResultDetailView when detail available, placeholder otherwise

- [x] Task 2: Compute real summary statistics from decileData (AC: 4)
  - [x] 2.1: Create `computeSummaryStats(decileData: DecileData[]): SummaryStatistic[]` helper inside `ResultsOverviewScreen.tsx` — derives 3 stats: mean delta, max positive impact decile, max negative impact decile
  - [x] 2.2: Handle empty/zero data gracefully with placeholder cards

- [x] Task 3: Wire into App.tsx (AC: 5)
  - [x] 3.1: Import `ResultsOverviewScreen` and replace the inline `viewMode === "results"` JSX block (lines 360-381) with `<ResultsOverviewScreen ... />`
  - [x] 3.2: Pass required props: `decileData`, `runResult`, scenario label, action callbacks
  - [x] 3.3: Remove the `mockSummaryStats` import from App.tsx only if no longer used in the file (the "run" view at lines 333-348 also uses `mockSummaryStats` — if still used there, keep the import)

- [x] Task 4: Fetch result detail for Detail tab (AC: 2)
  - [x] 4.1: In `ResultsOverviewScreen`, when `runResult?.run_id` is available and Detail tab is selected, call `getResult(runResult.run_id)` to load `ResultDetailResponse` (same pattern as `SimulationRunnerScreen.tsx:118-123`)
  - [x] 4.2: Cache the detail in local state to avoid re-fetching on tab switch; reset the cached detail (and any error state) when `runResult?.run_id` changes so stale data from a previous run is never shown

- [x] Task 5: Tests (AC: all)
  - [x] 5.1: Create `frontend/src/components/screens/__tests__/ResultsOverviewScreen.test.tsx`
  - [x] 5.2: Test: renders metadata header with run_id and policy label
  - [x] 5.3: Test: renders three tabs (Overview, Data & Export, Detail)
  - [x] 5.4: Test: Overview tab shows DistributionalChart and summary stat cards
  - [x] 5.5: Test: Data & Export tab shows export buttons, disabled when no run result
  - [x] 5.6: Test: action button hierarchy (Compare=default, Decisions=outline, Run Again=ghost)
  - [x] 5.7: Test: computed summary stats from decileData (mean delta, max impact)
  - [x] 5.8: Test: Detail tab fetch is lazy (getResult is NOT called before Detail tab is selected)
  - [x] 5.9: Test: Detail tab does not re-fetch on repeated tab switches (getResult called exactly once per run_id)
  - [x] 5.10: Test: cached detail is cleared when runResult changes to a different run_id (stale data prevention)
  - [x] 5.11: Run `npm test` — all pre-existing tests pass; new tests pass
  - [x] 5.12: Run `npm run typecheck` — 0 errors
  - [x] 5.13: Run `npm run lint` — 0 errors (pre-existing fast-refresh warnings OK)

## Dev Notes

### ResultsOverviewScreen — Props Interface

```tsx
// frontend/src/components/screens/ResultsOverviewScreen.tsx

interface ResultsOverviewScreenProps {
  decileData: DecileData[];
  runResult: RunResponse | null;             // from AppContext — has run_id, status
  reformLabel: string;                       // derived from selectedScenario in App.tsx
  onCompare: () => void;
  onViewDecisions: () => void;
  onRunAgain: () => void;
  onExportCsv: () => void;
  onExportParquet: () => void;
}
```

**Key design decisions:**
- Props are callbacks, not navigation state — the screen doesn't manage viewMode, App.tsx does
- `reformLabel` is pre-computed by the caller (matches existing pattern: `selectedScenario?.templateName ?? selectedScenario?.name ?? "Reform"`)
- `runResult` is nullable — when null, show mock/placeholder mode

### Summary Stats Computation

Derive 3 stats from `decileData` instead of using `mockSummaryStats`:

```tsx
function computeSummaryStats(data: DecileData[]): SummaryStatistic[] {
  if (data.length === 0) return placeholderStats();

  const deltas = data.map((d) => d.delta);
  const meanDelta = deltas.reduce((a, b) => a + b, 0) / deltas.length;
  const maxPos = data.reduce((best, d) => d.delta > best.delta ? d : best, data[0]);
  const maxNeg = data.reduce((best, d) => d.delta < best.delta ? d : best, data[0]);

  return [
    {
      id: "mean-impact",
      label: "Mean impact",
      value: `€${Math.round(meanDelta).toLocaleString()}/yr`,
      trend: meanDelta > 0 ? "up" : meanDelta < 0 ? "down" : "neutral",
      trendValue: `${meanDelta >= 0 ? "+" : ""}${Math.round(meanDelta).toLocaleString()}`,
    },
    {
      id: "most-benefit",
      label: "Most benefit",
      value: maxPos.decile,
      trend: maxPos.delta > 0 ? "up" : "neutral",
      trendValue: `€${Math.round(maxPos.delta).toLocaleString()}/yr`,
    },
    {
      id: "most-cost",
      label: "Most cost",
      value: maxNeg.decile,
      trend: maxNeg.delta < 0 ? "down" : "neutral",
      trendValue: `€${Math.round(maxNeg.delta).toLocaleString()}/yr`,
    },
  ];
}

function placeholderStats(): SummaryStatistic[] {
  return [
    { id: "mean-impact", label: "Mean impact", value: "—", trend: "neutral", trendValue: "—" },
    { id: "most-benefit", label: "Most benefit", value: "—", trend: "neutral", trendValue: "—" },
    { id: "most-cost", label: "Most cost", value: "—", trend: "neutral", trendValue: "—" },
  ];
}
```

### Tab Styling — Follow ComparisonDashboardScreen Pattern

Use the same wrapper + tab styling as `ComparisonDashboardScreen.tsx:729-762`:

```tsx
<Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabValue)}>
  <div className="rounded-lg border border-slate-200 bg-white">
    <TabsList className="w-full justify-start border-b border-slate-200 bg-white">
      <TabsTrigger value="overview">Overview</TabsTrigger>
      <TabsTrigger value="export">Data & Export</TabsTrigger>
      <TabsTrigger value="detail">Detail</TabsTrigger>
    </TabsList>
    <div className="p-3">
      <TabsContent value="overview">...</TabsContent>
      <TabsContent value="export">...</TabsContent>
      <TabsContent value="detail">...</TabsContent>
    </div>
  </div>
</Tabs>
```

Do **NOT** use the ResultDetailView's underline-style tabs (`border-b-2 border-transparent`). Use the boxed style from ComparisonDashboardScreen for consistency across screen-level tabs.

### Result Detail Loading Pattern

Fetch `ResultDetailResponse` lazily when the Detail tab is first selected:

```tsx
const [resultDetail, setResultDetail] = useState<ResultDetailResponse | null>(null);
const [detailLoading, setDetailLoading] = useState(false);
const [detailError, setDetailError] = useState(false);

// Reset cached detail when the active run changes
useEffect(() => {
  setResultDetail(null);
  setDetailError(false);
}, [runResult?.run_id]);

const loadDetail = useCallback(async () => {
  if (!runResult?.run_id || resultDetail || detailLoading) return;
  setDetailLoading(true);
  setDetailError(false);
  try {
    const detail = await getResult(runResult.run_id);
    setResultDetail(detail);
  } catch {
    setDetailError(true); // Detail tab shows "unavailable" message
  } finally {
    setDetailLoading(false);
  }
}, [runResult, resultDetail, detailLoading]);
```

When `detailError` is true, the Detail tab shows a "Detail unavailable" message instead of a blank state. The `detailLoading` guard prevents duplicate in-flight requests on rapid tab switches.

Import `getResult` from `@/api/results`. This follows the same pattern as `SimulationRunnerScreen.tsx:118-123` (dynamic import not needed here since it's a direct screen dependency).

### Header Layout

```tsx
{/* Header — metadata left, actions right */}
<div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white p-3">
  <div className="flex items-center gap-3 min-w-0">
    {runResult ? (
      <>
        <span className="font-mono text-xs text-slate-500">{runResult.run_id.slice(0, 8)}</span>
        <span className="text-sm font-semibold text-slate-900 truncate">{reformLabel}</span>
        {runResult.years.length > 0 ? (
          <Badge variant="secondary" className="text-xs">
            {runResult.years[0]}–{runResult.years[runResult.years.length - 1]}
          </Badge>
        ) : null}
        <Badge variant={runResult.success ? "success" : "destructive"} className="text-xs">
          {runResult.success ? "completed" : "failed"}
        </Badge>
      </>
    ) : (
      <>
        <span className="text-sm font-semibold text-slate-900">Results</span>
        <Badge variant="default" className="text-xs">mock data</Badge>
      </>
    )}
  </div>
  <div className="flex items-center gap-2 shrink-0">
    <Button size="sm" onClick={onCompare}>Compare Runs</Button>
    {runResult?.run_id ? (
      <Button variant="outline" size="sm" onClick={onViewDecisions}>Behavioral Decisions</Button>
    ) : null}
    <Button variant="ghost" size="sm" onClick={onRunAgain}>Run Again</Button>
  </div>
</div>
```

### Data & Export Tab Content

```tsx
<div className="space-y-3">
  <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
    <p className="text-sm font-semibold text-slate-900 mb-2">Export Results</p>
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-medium text-slate-700">CSV</p>
          <p className="text-xs text-slate-500">Tabular data for spreadsheets</p>
        </div>
        <Button variant="outline" size="sm" onClick={onExportCsv} disabled={!runResult?.success}>
          <Download className="h-3.5 w-3.5 mr-1" /> Export CSV
        </Button>
      </div>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-medium text-slate-700">Parquet</p>
          <p className="text-xs text-slate-500">Columnar format for programmatic analysis</p>
        </div>
        <Button variant="outline" size="sm" onClick={onExportParquet} disabled={!runResult?.success}>
          <Download className="h-3.5 w-3.5 mr-1" /> Export Parquet
        </Button>
      </div>
    </div>
    {!runResult?.success ? (
      <p className="mt-2 text-xs text-slate-400">Run a simulation first to enable exports.</p>
    ) : null}
  </div>
</div>
```

### What NOT to Change

- **`SimulationRunnerScreen.tsx`** — Has its own post-run results view with `ResultDetailView` + `ResultsListPanel`. This is the runner-specific flow and stays independent. Do NOT merge these two views.
- **`ResultDetailView.tsx`** — Embedded as-is inside the Detail tab. Do NOT modify its internal structure.
- **`DistributionalChart.tsx`** — Used as-is in the Overview tab. Do NOT modify.
- **`SummaryStatCard.tsx`** — Used as-is in the Overview tab. Do NOT modify the component; only change the data source (computed vs mock).
- **Backend files** — Frontend-only story.
- **`mockSummaryStats` definition** in `mock-data.ts` — Keep it; only remove the import from `App.tsx` if unused after changes. Other files or the "run" view may reference it.
- **`mockDecileData` definition** in `mock-data.ts` — Keep it; AppContext still falls back to it.

### mockSummaryStats Usage Check

`mockSummaryStats` is used in two places in `App.tsx`:
1. **Results view** (line 367-369): `mockSummaryStats.map(...)` — **REPLACE** with computed stats inside `ResultsOverviewScreen`
2. **Run view** (line 338-340): `mockSummaryStats.map(...)` — **KEEP** this usage (it's a pre-run summary showing example KPIs)

Since the "run" view still uses `mockSummaryStats`, **keep the import in App.tsx**. Only remove the usage in the results section by replacing it with the new `ResultsOverviewScreen` component.

### Type Imports

The component needs these types (all already exported):
- `DecileData` from `@/data/mock-data` — for chart data and stat computation
- `SummaryStatistic` from `@/data/mock-data` — for computed stat cards
- `RunResponse` from `@/api/types` — for run result metadata
- `ResultDetailResponse` from `@/api/types` — for detail tab embedding
- `getResult` from `@/api/results` — for fetching detail data

### Test Patterns

Follow existing screen test patterns (see `ComparisonDashboardScreen.test.tsx`, `BehavioralDecisionViewerScreen.test.tsx`):

```tsx
// Mock API
vi.mock("@/api/results", () => ({
  getResult: vi.fn(),
}));

// Mock Recharts ResponsiveContainer (needs ResizeObserver)
beforeAll(() => {
  global.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} };
});

// Mock data factories
function mockDecileData(): DecileData[] {
  return [
    { decile: "D1", baseline: -120, reform: -80, delta: 40 },
    { decile: "D2", baseline: -180, reform: -150, delta: 30 },
    { decile: "D10", baseline: -1800, reform: -1950, delta: -150 },
  ];
}

function mockRunResult(): RunResponse {
  return {
    run_id: "abcd1234-5678-90ab-cdef-123456789012",
    status: "completed",
  };
}
```

### Project Structure Notes

- New file: `frontend/src/components/screens/ResultsOverviewScreen.tsx` — follows the `components/screens/` convention for full-page view components
- New test: `frontend/src/components/screens/__tests__/ResultsOverviewScreen.test.tsx` — follows existing `__tests__/` convention
- No new `components/simulation/` files — all sub-components already exist
- No new `components/ui/` files — uses existing shadcn components (Tabs, Badge, Button)
- No new API endpoints or types — uses existing `getResult`, `ResultDetailResponse`, `DecileData`, `SummaryStatistic`

### Files to Modify (Complete List)

**New files (2):**
- `frontend/src/components/screens/ResultsOverviewScreen.tsx`
- `frontend/src/components/screens/__tests__/ResultsOverviewScreen.test.tsx`

**Files to modify (1):**
- `frontend/src/App.tsx` — replace inline results JSX with `<ResultsOverviewScreen>`, add import

**Files NOT to modify:**
- `frontend/src/components/simulation/ResultDetailView.tsx` — embedded as-is
- `frontend/src/components/simulation/DistributionalChart.tsx` — used as-is
- `frontend/src/components/simulation/SummaryStatCard.tsx` — used as-is
- `frontend/src/components/simulation/ResultsListPanel.tsx` — not used in this view (stays in SimulationRunnerScreen)
- `frontend/src/components/screens/SimulationRunnerScreen.tsx` — independent results flow
- `frontend/src/data/mock-data.ts` — keep mockSummaryStats definition
- `frontend/src/contexts/AppContext.tsx` — no state changes needed
- Any backend files

### References

- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 18.4 BDD: "Given results view, when refactored, then organized into tabbed layout with clear information hierarchy"]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Journey 3 "Scenario Workspace": results stream in as computed, full results: charts + tables + indicators]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Information Hierarchy lines 360-430: distributional bar chart, delta indicators, confidence signal]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Journey 5 "Export Flow" lines 831-875: one-action export, format selection, preview before write]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Action Hierarchy lines 1152-1171: comparison view primary="Export", secondary="Clone/Compare"]
- [Source: `frontend/src/App.tsx:360-381` — Current inline results view (to be replaced)]
- [Source: `frontend/src/App.tsx:333-348` — "Run" view uses mockSummaryStats (keep this usage)]
- [Source: `frontend/src/components/simulation/ResultDetailView.tsx` — 286-line tabbed detail viewer to embed]
- [Source: `frontend/src/components/screens/ComparisonDashboardScreen.tsx:729-762` — Tab styling pattern to follow]
- [Source: `frontend/src/components/screens/SimulationRunnerScreen.tsx:118-123` — getResult() fetch pattern to follow]
- [Source: `frontend/src/api/types.ts:340-365` — ResultListItem, ResultDetailResponse type definitions]
- [Source: `frontend/src/data/mock-data.ts:245-267` — mockSummaryStats definition (3 static stats)]
- [Source: `frontend/src/contexts/AppContext.tsx:248-263` — decileData flow and mapIndicatorToDecileData]
- [Source: `_bmad-output/implementation-artifacts/18-3-extract-shared-components.md` — Story 18.3 done: 271 tests passing baseline]
- [Source: `_bmad-output/implementation-artifacts/epic-18-ux-polish-and-aesthetic-overhaul.md` — Epic exit criteria: "Results view has clear information hierarchy with tabs"]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None.

### Completion Notes

- Created `ResultsOverviewScreen` component with metadata header (run_id, policy label, year range badge, status badge), tabbed layout (Overview/Data & Export/Detail), and proper action hierarchy
- `computeSummaryStats()` derives 3 KPIs from `decileData`: mean delta, most-benefit decile, most-cost decile; falls back to placeholder "—" cards for empty/all-zero data
- Detail tab lazily fetches `ResultDetailResponse` on first selection; caches in component state; resets when `runResult.run_id` changes to prevent stale data
- Replaced inline results JSX in `App.tsx:360-381` with `<ResultsOverviewScreen>`; removed unused `DistributionalChart` import; kept `mockSummaryStats` import (still used in "run" view)
- Updated `analyst-journey.test.tsx` to use new button label "Compare Runs" (was "Open Comparison")
- 40 new tests added; all 311 tests pass (271 baseline + 40 new); typecheck 0 errors; lint 0 errors (pre-existing fast-refresh warnings only)
- **[Code Review Synthesis 2026-03-22]** Fixed stale detail race: `activeRunIdRef` added to guard `setResultDetail`/`setDetailError`/`setDetailLoading` commits after run switches
- **[Code Review Synthesis 2026-03-22]** Fixed AC-1 mock mode label: now shows `{reformLabel}` instead of hardcoded "Results"; added year badge "—" in mock branch
- **[Code Review Synthesis 2026-03-22]** Fixed AC-1 year range badge: always rendered with "—" fallback when `runResult.years` is empty
- **[Code Review Synthesis 2026-03-22]** Fixed AC-4: added "No indicator data available." note below stat cards in placeholder state
- **[Code Review Synthesis 2026-03-22]** Fixed `+0` display: trendValue uses `roundedMean` variable; shows "0" (not "+0") for zero mean
- **[Code Review Synthesis 2026-03-22]** Fixed two tests encoding wrong behavior (mock label, year range) to match AC-1
- **[Code Review Synthesis 2026-03-22]** Added `aria-pressed={active}` to WorkflowNavRail nav buttons (recurring accessibility antipattern)
- All 311 tests pass post-review; typecheck 0 errors; lint 0 errors

### File List

**New files:**
- `frontend/src/components/screens/ResultsOverviewScreen.tsx`
- `frontend/src/components/screens/__tests__/ResultsOverviewScreen.test.tsx`

**Modified files:**
- `frontend/src/App.tsx` — replaced inline results JSX with `<ResultsOverviewScreen>`, removed unused `DistributionalChart` import
- `frontend/src/__tests__/workflows/analyst-journey.test.tsx` — updated button label from "Open Comparison" to "Compare Runs"
- `frontend/src/components/layout/WorkflowNavRail.tsx` — added `aria-pressed={active}` to nav buttons [code review synthesis]

#### Review Follow-ups (AI)
_(none — all verified issues addressed)_

## Senior Developer Review (AI)

### Review: 2026-03-22
- **Reviewer:** AI Code Review Synthesis
- **Evidence Score:** 8.5 (Reviewer B REJECT) / -0.2 (Reviewer A APPROVED) → Composite: **Changes Requested** (real issues confirmed)
- **Issues Found:** 7 verified (1 HIGH race condition, 3 MEDIUM AC gaps, 2 MEDIUM test defects, 1 MEDIUM accessibility, 1 LOW display bug, 1 LOW missing note)
- **Issues Fixed:** 7 (all)
- **Action Items Created:** 0 (all resolved in synthesis)
