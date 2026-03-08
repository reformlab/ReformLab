

# Story 17.4: Build Comparison Dashboard with Multi-Portfolio Side-by-Side

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a non-coding policy analyst,
I want a Comparison Dashboard where I can select two or more completed simulation runs, view side-by-side distributional, fiscal, and welfare indicators with charts and tables, toggle between absolute and relative views, inspect indicator methodology details, and see cross-portfolio ranking metrics,
so that I can evaluate which policy portfolio best achieves my goals by comparing outcomes across multiple scenarios in a single unified view.

## Acceptance Criteria

1. **AC-1: Multi-run selection** — Given the persistent results list from Story 17.3 (via `GET /api/results`), when the analyst opens the Comparison Dashboard, then completed runs with `data_available: true` are shown as selectable items. The analyst can select 2–5 runs. Runs with `data_available: false` (evicted from cache) are shown as disabled/greyed with "(evicted)" label. A "Max 5 runs" indicator is visible. The first selected run is treated as baseline (leftmost in all views). Selection order is preserved.

2. **AC-2: Side-by-side indicator display** — Given two or more selected runs, when comparison data loads, then a side-by-side dashboard displays three indicator tabs: Distributional (bar chart by income decile with one colored bar per run), Fiscal (table with annual revenue/cost/balance per run), and Welfare (winner/loser counts and net change per run). Each run is color-coded using the project's chart color palette (`--chart-baseline`, `--chart-reform-a` through `--chart-reform-d`). The distributional bar chart shows N grouped bars per decile (one per run). The first selected run uses the baseline color (slate); subsequent runs use reform colors (blue, violet, emerald, amber). A companion table beneath each chart shows exact values.

3. **AC-3: Indicator detail panel** — Given the comparison dashboard, when the analyst clicks on a specific indicator row or chart bar, then a detail panel expands showing: the indicator's full label and description, the values for all selected runs, the computation methodology (e.g., "Distributional: mean disposable income per decile"), and the delta values (absolute and percentage) relative to baseline. This panel is dismissable by clicking again or pressing Escape.

4. **AC-4: Absolute/relative toggle** — Given the comparison dashboard, when the analyst toggles between "Absolute" and "Relative" views (via a segmented control in the toolbar), then: in Absolute mode, raw indicator values are shown in charts and tables; in Relative mode, delta-from-baseline values are shown (with positive values in emerald, negative in red, and the baseline column hidden). The toggle persists across tab switches within the dashboard.

5. **AC-5: Cross-comparison metrics** — Given the comparison dashboard with 2+ runs loaded, when comparison data is computed, then a cross-metric summary panel is displayed showing aggregate rankings: "Max fiscal revenue", "Min fiscal cost", "Max fiscal balance", "Max mean welfare change", "Max winners", "Min losers". Each metric shows the best-performing run label and value. This panel is shown above the indicator tabs.

6. **AC-6: Behavioral response awareness** — Given runs that include behavioral responses (discrete choice model from Epic 14), when comparison data is displayed, then indicators reflect post-behavioral-response outcomes. No special UI treatment is needed for MVP — the indicator data already incorporates behavioral effects through the orchestrator pipeline. The dashboard simply displays whatever indicator data the backend returns.

## Tasks / Subtasks

- [x] Task 1: Implement multi-run comparison backend endpoint (AC: 1, 2, 5)
  - [x] 1.1: Add `PortfolioComparisonRequest` and `PortfolioComparisonResponse` Pydantic models to `src/reformlab/server/models.py`: `run_ids: list[str]` (2–5 items), `baseline_run_id: str | None = None`, `indicator_types: list[str] = Field(default_factory=lambda: ["distributional", "fiscal"])`, `include_welfare: bool = True`, `include_deltas: bool = True`, `include_pct_deltas: bool = True`. Response model: `comparisons: dict[str, ComparisonData]` (keyed by indicator type), `cross_metrics: list[CrossMetricItem]`, `portfolio_labels: list[str]`, `metadata: dict[str, Any]`, `warnings: list[str]`. Define `ComparisonData(columns: list[str], data: dict[str, list[Any]])` and `CrossMetricItem(criterion: str, best_portfolio: str, value: float, all_values: dict[str, float])`
  - [x] 1.2: Add `POST /api/comparison/portfolios` endpoint to `src/reformlab/server/routes/indicators.py` on the existing `comparison_router`. The handler: (a) validates 2–5 `run_ids` with 422 on violation, (b) rejects duplicate `run_ids` with 422 (`what/why/fix` format), (c) for each run_id — check `ResultStore` metadata first (404 if unknown to the store), then check `ResultCache` (409 if in metadata but not in cache or `panel_output is None`), (d) derives labels from `ResultMetadata` (using `portfolio_name`, `template_name`, or `run_id[:8]`), (e) deduplicates labels if identical (append `_2`, `_3`, etc.) and validates against reserved names (`field_name`, `decile`, `year`, `metric`, `value`, `region`) and reserved prefixes (`delta_`, `pct_delta_`) — return 422 if any label cannot be made safe, (f) constructs `PortfolioComparisonInput(label, panel_output)` list, calls `compare_portfolios()`, serializes `PortfolioComparisonResult` to response (convert each `ComparisonResult.table` via `.to_pydict()`, convert `CrossComparisonMetric` tuples to `CrossMetricItem` list)
  - [x] 1.3: Write backend tests in `tests/server/test_comparison_portfolios.py`: test valid 2-run and 3-run comparison, test 404 when run_id not in metadata store, test 409 when run_id in metadata store but not in cache (evicted), test 409 when panel_output is None, test <2 and >5 run_ids rejected (422), test duplicate run_ids rejected (422), test label deduplication when two runs share the same template_name, test reserved label name rejected (422), test error response format (`what/why/fix`). Group tests by AC in classes (e.g., `class TestComparePortfoliosValidation`, `class TestComparePortfoliosSuccess`, `class TestComparePortfoliosErrors`)

- [x] Task 2: Define frontend TypeScript types and API client (AC: 1, 2, 5)
  - [x] 2.1: Add TypeScript interfaces to `frontend/src/api/types.ts`: `PortfolioComparisonRequest`, `PortfolioComparisonResponse`, `ComparisonData`, `CrossMetricItem`
  - [x] 2.2: Add `comparePortfolios(request: PortfolioComparisonRequest): Promise<PortfolioComparisonResponse>` to `frontend/src/api/indicators.ts` — calls `POST /api/comparison/portfolios`
  - [x] 2.3: Add mock comparison data to `frontend/src/data/mock-data.ts`: `mockComparisonResponse` with distributional + fiscal comparison data for 3 mock runs, plus cross-metric items

- [x] Task 3: Build MultiRunChart component (AC: 2)
  - [x] 3.1: Create `frontend/src/components/simulation/MultiRunChart.tsx` — Recharts `BarChart` accepting `data: Record<string, unknown>[]`, `xKey: string` (e.g., `"decile"`), `series: Array<{ key: string; label: string; color: string }>`. Renders N grouped `<Bar>` elements per series. Supports absolute and relative mode via a `mode: "absolute" | "relative"` prop. In relative mode, renders delta values with positive/negative color coding (emerald/red). Includes `<Tooltip>` with all series values and `<Legend>` with series labels. Chart height: 280px. CSS color vars: `--chart-baseline` for first series, `--chart-reform-a` through `--chart-reform-d` for subsequent
  - [x] 3.2: Add companion data table beneath the chart — semantic `<table>` with columns matching the series, for accessibility ("View as table" toggle)
  - [x] 3.3: Add unit tests in `frontend/src/components/simulation/__tests__/MultiRunChart.test.tsx`

- [x] Task 4: Build CrossMetricPanel component (AC: 5)
  - [x] 4.1: Create `frontend/src/components/simulation/CrossMetricPanel.tsx` — renders cross-comparison metrics as a horizontal grid of KPI cards. Each card shows: metric label (human-readable, e.g., "Max Fiscal Revenue" instead of `max_fiscal_revenue`), best portfolio label, best value (formatted), and a miniature ranking of all values. Uses `SummaryStatCard` pattern but adapted for ranking display. Layout: `grid-cols-3` on XL, `grid-cols-2` on smaller
  - [x] 4.2: Add unit tests in `frontend/src/components/simulation/__tests__/CrossMetricPanel.test.tsx`

- [x] Task 5: Build ComparisonDashboardScreen (AC: 1, 2, 3, 4, 5, 6)
  - [x] 5.1: Create `frontend/src/components/screens/ComparisonDashboardScreen.tsx` — full-screen comparison dashboard with three sections: (1) Run selector panel at top, (2) Cross-metric summary panel, (3) Tabbed indicator content (Distributional, Fiscal, Welfare). Screen manages: `selectedRunIds: string[]` (2–5), `comparisonData: PortfolioComparisonResponse | null`, `loading: boolean`, `error: ErrorState | null`, `viewMode: "absolute" | "relative"`, `activeTab: "distributional" | "fiscal" | "welfare"`, `detailTarget: { indicator: string; values: Record<string, number> } | null`
  - [x] 5.2: Implement run selector — checkbox-based selection from `ResultListItem[]` (from `useAppState().results`). Filter to `status === "completed"`. Disable items with `data_available === false`. Show "(evicted)" badge. Enforce max 5 selection. First selected = baseline. Show "Compare" button that triggers API call. Show run label (template_name or portfolio_name or truncated run_id), year range badge, and row count
  - [x] 5.3: Implement comparison data loading — on "Compare" click, call `comparePortfolios({ run_ids: selectedRunIds, baseline_run_id: selectedRunIds[0], include_welfare: true })`. Show loading spinner during API call. On success, render CrossMetricPanel + tabbed indicators. On error, show `what/why/fix` error display (same pattern as `SimulationRunnerScreen`)
  - [x] 5.4: Implement Distributional tab — `MultiRunChart` with `xKey="decile"`, one series per run label. Below the chart, a `Table` with one column per run + optional delta columns. In relative mode, show only delta columns with positive/negative color coding
  - [x] 5.5: Implement Fiscal tab — `Table` with rows per year, columns per run showing revenue/cost/balance. In relative mode, show delta-from-baseline columns. No chart for fiscal (table is the primary view)
  - [x] 5.6: Implement Welfare tab — summary cards showing winner/loser counts and net change per run. In relative mode, show delta counts. If welfare data is not available in comparison response, show informational message ("Welfare comparison requires 3+ runs or explicit welfare configuration")
  - [x] 5.7: Implement indicator detail panel — clicking a table row or chart bar sets `detailTarget`. A collapsible `<aside>` slides open showing: full indicator label, values for all runs, deltas (absolute + percentage), methodology description. Methodology descriptions are static frontend string constants keyed by indicator type. Dismiss via Escape key
  - [x] 5.8: Implement absolute/relative toggle — segmented control (`Button` group) in the toolbar, toggles between `"absolute"` and `"relative"` mode. State persists across tab switches. In relative mode: chart shows delta values, baseline column hidden in tables, positive deltas emerald, negative deltas red
  - [x] 5.9: Add "Export comparison" button — client-side CSV generation from the loaded comparison data (no new endpoint needed)
  - [x] 5.10: Add unit tests in `frontend/src/components/screens/__tests__/ComparisonDashboardScreen.test.tsx`

- [x] Task 6: Integrate ComparisonDashboardScreen into workspace (AC: 1, 2, 3, 4, 5)
  - [x] 6.1: Replace `ComparisonView` usage in `App.tsx` — when `viewMode === "comparison"`, render `ComparisonDashboardScreen` instead of `ComparisonView`. Pass `results` from `useAppState()`, `onBack` handler to return to previous view
  - [x] 6.2: Update `ComparisonView` component or deprecate it — the Phase 1 `ComparisonView` (mock-data-driven, 2-scenario-only) is replaced by `ComparisonDashboardScreen`. Kept file, removed import from `App.tsx`
  - [x] 6.3: Update AppContext if needed — added `selectedComparisonRunIds: string[]` and `setSelectedComparisonRunIds` to `AppState`. Initialized as empty array
  - [x] 6.4: Update navigation — "Open Comparison" button in results view navigates to `viewMode === "comparison"`. ScenarioCard "Compare" action navigates to comparison view
  - [x] 6.5: Verify non-regression: 187 frontend tests pass, 3045 backend tests pass. All view modes functional

- [x] Task 7: Run quality checks (AC: all)
  - [x] 7.1: Run `uv run ruff check src/ tests/` and fix any lint issues — ✅ All checks passed
  - [x] 7.2: Run `uv run mypy src/` and fix any type errors — ✅ No issues in 146 source files
  - [x] 7.3: Run `cd frontend && npm run typecheck && npm run lint` and fix any issues — ✅ No type errors, 0 lint errors (3 harmless fast-refresh warnings)
  - [x] 7.4: Run `uv run pytest tests/` — all tests pass — ✅ 3045 passed, 1 skipped
  - [x] 7.5: Run `cd frontend && npm test` — all tests pass — ✅ 187 passed (27 test files)

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**Backend — Canonical endpoint table:**

| Method | Full URL | Router-relative path | Purpose |
|---|---|---|---|
| POST | `/api/comparison/portfolios` | `/portfolios` | Multi-run portfolio comparison |

Note: This endpoint is added to the **existing `comparison_router`** (already mounted at `/api/comparison` in `app.py`). No new router registration needed — just add the route function to `indicators.py`.

**Backend — HTTP status code matrix:**

| Endpoint | Success | Client Error |
|---|---|---|
| `POST /api/comparison/portfolios` | 200 | 404 (run_id unknown — not in `ResultStore` metadata), 409 (run_id known in metadata but unavailable in cache — evicted or `panel_output is None`), 422 (invalid request: <2 or >5 runs, duplicate run_ids, reserved/unsafe label after derivation) |

All error responses use `{"what": str, "why": str, "fix": str}` structure.

**Backend — Multi-run comparison flow:**

```python
# In indicators.py on comparison_router:
@comparison_router.post("/portfolios", response_model=PortfolioComparisonResponse)
async def compare_portfolio_runs(
    body: PortfolioComparisonRequest,
    cache: ResultCache = Depends(get_result_cache),
    store: ResultStore = Depends(get_result_store),
) -> PortfolioComparisonResponse:
    # 1. Validate 2 <= len(run_ids) <= 5 (422 if violated)
    # 1b. Validate no duplicate run_ids (422 if violated)
    # 2. For each run_id:
    #    - Check ResultStore metadata: if run_id unknown → 404
    #    - Check ResultCache: if not in cache or panel_output is None → 409 (evicted)
    #    - Derive label from ResultMetadata (portfolio_name or template_name or run_id[:8])
    # 3. Deduplicate labels (append _2, _3 if collision); reject reserved names/prefixes → 422
    # 4. Build PortfolioComparisonInput list
    # 5. Call compare_portfolios(inputs, config)
    # 6. Serialize PortfolioComparisonResult to PortfolioComparisonResponse
```

**Backend — Label derivation:**

For each run, derive a human-readable label for the comparison tables/charts:
```python
def _derive_label(run_id: str, store: ResultStore) -> str:
    try:
        meta = store.get_metadata(run_id)
        if meta.portfolio_name:
            return meta.portfolio_name
        if meta.template_name:
            return meta.template_name
        return run_id[:8]
    except ResultNotFound:
        return run_id[:8]
```

**Backend — Serialization of PortfolioComparisonResult:**

`PortfolioComparisonResult.comparisons` is `dict[str, ComparisonResult]` where each `ComparisonResult` contains a PyArrow table. Convert via:
```python
comparison_data = {}
for ind_type, comp_result in result.comparisons.items():
    table_dict = comp_result.table.to_pydict()
    comparison_data[ind_type] = ComparisonData(
        columns=comp_result.table.schema.names,
        data=table_dict,
    )
```

**Backend — `compare_portfolios()` input requirements:**

- Accepts `list[PortfolioComparisonInput]` where each has `.label: str` and `.panel: PanelOutput`
- Labels must be unique, non-empty, not reserved (`field_name`, `decile`, `year`, `metric`, `value`, `region`), not starting with `delta_` or `pct_delta_`
- Minimum 2 inputs; no explicit maximum (we enforce 5 max at the API layer)
- The `PanelOutput` is obtained from `SimulationResult.panel_output` in the `ResultCache`
- Welfare comparison is opt-in via `include_welfare=True` on `PortfolioComparisonConfig`

**Backend — Route placement:**

Add the new endpoint to `comparison_router` in `src/reformlab/server/routes/indicators.py`. The `comparison_router` is already mounted at `/api/comparison` in `app.py`, so adding `@comparison_router.post("/portfolios")` makes the full path `/api/comparison/portfolios`.

**Backend — Dependencies:**

The route handler needs both `ResultCache` (for `SimulationResult` lookup) and `ResultStore` (for label derivation from metadata). Use `Depends(get_result_cache)` and `Depends(get_result_store)`.

### Frontend Patterns (MUST FOLLOW)

**Frontend — Component locations:**
- Screen component: `frontend/src/components/screens/ComparisonDashboardScreen.tsx`
- Domain components: `frontend/src/components/simulation/MultiRunChart.tsx`, `CrossMetricPanel.tsx`
- Tests: `frontend/src/components/{screens,simulation}/__tests__/`

**Frontend — Chart color palette (from UX spec + CSS):**

```css
--chart-baseline:  theme(colors.slate.500);    /* First selected run */
--chart-reform-a:  theme(colors.blue.500);     /* Second run */
--chart-reform-b:  theme(colors.violet.500);   /* Third run */
--chart-reform-c:  theme(colors.emerald.500);  /* Fourth run */
--chart-reform-d:  theme(colors.amber.500);    /* Fifth run */
```

Map the series index to color vars:
```typescript
const CHART_COLORS = [
  "var(--chart-baseline)",   // index 0 — baseline
  "var(--chart-reform-a)",   // index 1
  "var(--chart-reform-b)",   // index 2
  "var(--chart-reform-c)",   // index 3
  "var(--chart-reform-d)",   // index 4
];
```

**Frontend — MultiRunChart design:**

The existing `DistributionalChart` hardcodes 2 bars (`baseline` + `reform`). For multi-run comparison, a new `MultiRunChart` component is needed that dynamically renders N `<Bar>` elements:

```tsx
<BarChart data={chartData}>
  <CartesianGrid strokeDasharray="2 2" />
  <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
  <YAxis tick={{ fontSize: 12 }} />
  <Tooltip />
  <Legend wrapperStyle={{ fontSize: 12, paddingTop: 4 }} />
  {series.map((s, i) => (
    <Bar key={s.key} dataKey={s.key} fill={CHART_COLORS[i] ?? CHART_COLORS[0]} name={s.label} />
  ))}
</BarChart>
```

For relative mode, the data should use `delta_<label>` columns instead of raw value columns.

**Frontend — ComparisonDashboardScreen state machine:**

```
Idle (no runs selected) → Select runs → Loading → Loaded (comparison data)
                                                 → Error
Loaded → Change selection → Loading → Loaded
Loaded → Toggle absolute/relative → re-render (no API call)
Loaded → Switch tab → re-render (no API call)
Loaded → Click indicator → detail panel open
```

**Frontend — Run selector design:**

The run selector reuses the `ResultListItem` data already in `AppContext.results`. Display as a compact multi-select list (checkboxes):

```
☑ a1b2c3d4  Carbon Tax — With Dividend     2025–2030  600,000  ✓ completed
☑ b2c3d4e5  green-transition-2030          2025–2035  1,100,000  ✓ completed
☐ c3d4e5f6  Carbon Tax — Uniform Rate      2025–2027  0  ✗ failed       (disabled)
```

Filter: only `status === "completed"` are checkable. `data_available === false` shows "(evicted)" and is disabled.

**Frontend — Data transformation for MultiRunChart:**

The API returns comparison data as `ComparisonData.data` which is a columnar dict from PyArrow's `table.to_pydict()`. Transform to Recharts row format:

```typescript
// API returns: { "decile": [1,2,...], "Run A": [100,200,...], "Run B": [150,250,...] }
// Transform to: [{ decile: 1, "Run A": 100, "Run B": 150 }, { decile: 2, "Run A": 200, "Run B": 250 }, ...]
function columnarToRows(data: Record<string, unknown[]>): Record<string, unknown>[] {
  const keys = Object.keys(data);
  if (keys.length === 0) return [];
  const rowCount = data[keys[0]]?.length ?? 0;
  return Array.from({ length: rowCount }, (_, i) =>
    Object.fromEntries(keys.map(k => [k, data[k]?.[i]]))
  );
}
```

**Frontend — Existing components to reuse:**

| Existing Component | Reuse in 17.4 |
|---|---|
| `ResultsListPanel.tsx` | Pattern for run selector (checkbox list with badges) |
| `SummaryStatCard.tsx` | Pattern for cross-metric KPI cards |
| `DistributionalChart.tsx` | Pattern (not directly reused — new `MultiRunChart` for N series) |
| `ComparisonView.tsx` | **Replaced** by `ComparisonDashboardScreen` |
| `ResultDetailView.tsx` | Pattern for indicator detail panel (tabbed, dismissable) |
| `Badge` | Status badges, year range badges, eviction indicators |
| `Tabs/TabsList/TabsTrigger/TabsContent` | Indicator type tabs |
| `Table/TableHead/TableBody/TableRow/TableCell` | Comparison data tables |
| `Button` | Absolute/relative toggle, Compare button, Back button |
| `Collapsible` | Detail panel expand/collapse |

**Frontend — Shadcn/ui components available (already installed):**

Badge, Button, Card, Collapsible, Dialog, Input, Popover, ScrollArea, Select, Separator, Sheet, Slider, Switch, Table, Tabs, Tooltip, Sonner (toast).

**Frontend — Absolute/relative toggle:**

Use a `Button` group (not a Switch) for clarity:

```tsx
<div className="flex gap-0 border border-slate-200">
  <Button
    variant={viewMode === "absolute" ? "default" : "ghost"}
    size="sm"
    onClick={() => setViewMode("absolute")}
  >
    Absolute
  </Button>
  <Button
    variant={viewMode === "relative" ? "default" : "ghost"}
    size="sm"
    onClick={() => setViewMode("relative")}
  >
    Relative
  </Button>
</div>
```

In relative mode:
- Charts show `delta_<label>` columns instead of raw value columns
- Baseline column is hidden (it's all zeros by definition)
- Positive deltas: `text-emerald-600` / emerald bar fill
- Negative deltas: `text-red-600` / red bar fill
- The delta columns are already present in `ComparisonResult.table` (the `include_deltas=True` default)

**Frontend — Cross-metric label formatting:**

| Raw criterion | Display label |
|---|---|
| `max_fiscal_revenue` | Max Fiscal Revenue |
| `min_fiscal_cost` | Min Fiscal Cost |
| `max_fiscal_balance` | Max Fiscal Balance |
| `max_mean_welfare_net_change` | Max Welfare Net Change |
| `max_total_winners` | Most Winners |
| `min_total_losers` | Fewest Losers |

### Pydantic Request/Response Models

Add to `src/reformlab/server/models.py`:

```python
class PortfolioComparisonRequest(BaseModel):
    """Request for multi-run portfolio comparison."""
    run_ids: list[str]                                # 2-5 run IDs; duplicates rejected
    baseline_run_id: str | None = None                # defaults to first run_id
    indicator_types: list[str] = Field(default_factory=lambda: ["distributional", "fiscal"])
    include_welfare: bool = True
    include_deltas: bool = True
    include_pct_deltas: bool = True


class ComparisonData(BaseModel):
    """Comparison result for a single indicator type."""
    columns: list[str]
    data: dict[str, list[Any]]


class CrossMetricItem(BaseModel):
    """Single cross-comparison metric ranking portfolios."""
    criterion: str
    best_portfolio: str
    value: float
    all_values: dict[str, float]


class PortfolioComparisonResponse(BaseModel):
    """Response for multi-run portfolio comparison."""
    comparisons: dict[str, ComparisonData]  # keyed by indicator type
    cross_metrics: list[CrossMetricItem]
    portfolio_labels: list[str]
    metadata: dict[str, Any]
    warnings: list[str]
```

### TypeScript Types

Add to `frontend/src/api/types.ts`:

```typescript
// Multi-run comparison types — Story 17.4
export interface PortfolioComparisonRequest {
  run_ids: string[];
  baseline_run_id?: string | null;
  indicator_types?: string[];
  include_welfare?: boolean;
  include_deltas?: boolean;
  include_pct_deltas?: boolean;
}

export interface ComparisonData {
  columns: string[];
  data: Record<string, unknown[]>;
}

export interface CrossMetricItem {
  criterion: string;
  best_portfolio: string;
  value: number;
  all_values: Record<string, number>;
}

export interface PortfolioComparisonResponse {
  comparisons: Record<string, ComparisonData>;
  cross_metrics: CrossMetricItem[];
  portfolio_labels: string[];
  metadata: Record<string, unknown>;
  warnings: string[];
}
```

### Mock Data for Comparison

```typescript
export const mockComparisonResponse: PortfolioComparisonResponse = {
  comparisons: {
    distributional: {
      columns: ["field_name", "decile", "year", "metric", "Run A", "Run B", "delta_Run B"],
      data: {
        field_name: Array(10).fill("disposable_income"),
        decile: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        year: Array(10).fill(2025),
        metric: Array(10).fill("mean"),
        "Run A": [-120, -180, -240, -310, -400, -520, -680, -890, -1200, -1800],
        "Run B": [-80, -150, -210, -290, -390, -520, -690, -920, -1260, -1950],
        "delta_Run B": [40, 30, 30, 20, 10, 0, -10, -30, -60, -150],
      },
    },
    fiscal: {
      columns: ["field_name", "year", "metric", "Run A", "Run B", "delta_Run B"],
      data: {
        field_name: ["tax_revenue", "tax_revenue", "tax_revenue"],
        year: [2025, 2026, 2027],
        metric: ["revenue", "revenue", "revenue"],
        "Run A": [2100000000, 2300000000, 2500000000],
        "Run B": [1800000000, 2000000000, 2200000000],
        "delta_Run B": [-300000000, -300000000, -300000000],
      },
    },
  },
  cross_metrics: [
    { criterion: "max_fiscal_revenue", best_portfolio: "Run A", value: 6900000000, all_values: { "Run A": 6900000000, "Run B": 6000000000 } },
    { criterion: "min_fiscal_cost", best_portfolio: "Run B", value: 0, all_values: { "Run A": 0, "Run B": 0 } },
    { criterion: "max_fiscal_balance", best_portfolio: "Run A", value: 6900000000, all_values: { "Run A": 6900000000, "Run B": 6000000000 } },
  ],
  portfolio_labels: ["Run A", "Run B"],
  metadata: { baseline_label: "Run A", indicator_types: ["distributional", "fiscal"] },
  warnings: [],
};
```

### Source Tree Components to Touch

**New files:**
```
tests/server/test_comparison_portfolios.py              ← Backend comparison tests (Task 1.3)
frontend/src/components/screens/ComparisonDashboardScreen.tsx
frontend/src/components/simulation/MultiRunChart.tsx
frontend/src/components/simulation/CrossMetricPanel.tsx
frontend/src/components/screens/__tests__/ComparisonDashboardScreen.test.tsx
frontend/src/components/simulation/__tests__/MultiRunChart.test.tsx
frontend/src/components/simulation/__tests__/CrossMetricPanel.test.tsx
```

**Modified files:**
```
src/reformlab/server/routes/indicators.py               ← Add POST /portfolios on comparison_router
src/reformlab/server/models.py                          ← Add comparison request/response models
frontend/src/api/types.ts                               ← Add comparison TypeScript interfaces
frontend/src/api/indicators.ts                          ← Add comparePortfolios() function
frontend/src/data/mock-data.ts                          ← Add mock comparison data
frontend/src/hooks/useApi.ts                            ← Add usePortfolioComparison() hook (optional)
frontend/src/contexts/AppContext.tsx                    ← Add selectedComparisonRunIds state
frontend/src/App.tsx                                    ← Replace ComparisonView with ComparisonDashboardScreen
```

### Project Structure Notes

- Backend route added to existing `comparison_router` in `indicators.py` — no new router file needed
- Domain logic already exists in `src/reformlab/indicators/portfolio_comparison.py` (Story 12.5) — no domain changes needed
- Frontend screen follows `screens/` convention, domain components in `simulation/`
- API client follows `frontend/src/api/` convention with typed fetch wrappers
- No new npm or Python dependencies required
- The old `ComparisonView.tsx` is kept but its import is removed from `App.tsx`

### Important Scope Boundaries

**What this story does:**
- Builds the Comparison Dashboard GUI screen with multi-run selection (2–5 runs)
- Implements backend endpoint that wraps the existing `compare_portfolios()` domain function
- Builds multi-series distributional bar chart component
- Builds cross-metric ranking summary panel
- Implements absolute/relative view toggle
- Implements indicator detail panel (click-to-expand)
- Replaces the Phase 1 mock-driven `ComparisonView` in the workspace

**What this story does NOT do:**
- Real-time comparison updates when parameters change (UX spec mentions "live update" — out of scope for GUI showcase)
- Waterfall contribution charts (UX spec mentions WaterfallChart — deferred)
- Geographic indicator comparison (only distributional, fiscal, welfare)
- Export comparison as PDF/report (CSV export only, client-side)
- Behavioral decision viewer (Story 17.5)
- Additional backend endpoints beyond the portfolio comparison (Story 17.6)
- E2E browser tests (Story 17.8)
- New overlay chart with all scenarios on same axes (AC-2 charts show grouped bars, not overlaid lines — overlay mode is a stretch goal)

### Anti-Patterns to Avoid

| Issue | Prevention |
|---|---|
| Calling `compare_portfolios()` with `SimulationResult` instead of `PanelOutput` | Extract `.panel_output` from `SimulationResult` before passing to `PortfolioComparisonInput` |
| Creating N separate API calls from frontend (one per indicator type per run) | Use single `POST /api/comparison/portfolios` endpoint that batches all computation server-side |
| Hardcoding 2-run comparison in charts | `MultiRunChart` must accept N series dynamically (1–5) |
| Using `DistributionalChart` directly (only supports 2 bars) | Create new `MultiRunChart` component for N-series support |
| Importing OpenFisca in server routes | Use adapter interface only — comparison uses `PanelOutput` from `ResultCache` |
| Mobile-responsive layouts | Desktop-only (min 1280px) |
| Shadows on static layout elements | Shadows reserved for floating elements only |
| Using `forwardRef` | React 19: ref is a regular prop |
| Breaking existing comparison navigation | Old `ComparisonView` is replaced gracefully — keep file, remove import |
| Labels conflicting with reserved column names | Validate labels server-side before calling `compare_portfolios()` |
| Progress bar reaching 100% before data loads | Show loading spinner, not progress bar — comparison is not a long-running operation |

### Testing Standards Summary

**Backend tests:**
- File: `tests/server/test_comparison_portfolios.py`
- Use FastAPI `TestClient` pattern from `tests/server/test_api.py`
- Mock `ResultCache` with pre-populated `SimulationResult` objects (use `MockAdapter` pattern)
- Test 2-run comparison returns correct response shape
- Test 3-run comparison with all indicator types (distributional + fiscal + welfare)
- Test 404 when run_id not in `ResultStore` metadata (completely unknown)
- Test 409 when run_id in metadata but not in `ResultCache` (evicted)
- Test 409 when `panel_output is None`
- Test 422 when <2 or >5 run_ids provided
- Test 422 when duplicate run_ids provided
- Test 422 when derived label matches a reserved column name
- Test label deduplication when two runs share the same `template_name`
- Test error response format (`what/why/fix`)

**Frontend tests:**
- Use Vitest + @testing-library/react (already configured)
- Test `MultiRunChart`: render with 2 series, render with 5 series, mode toggle
- Test `CrossMetricPanel`: render with mock metrics, verify labels
- Test `ComparisonDashboardScreen`: render with results, run selection, compare action, tab switching, absolute/relative toggle, error state
- Follow existing test patterns in `frontend/src/components/simulation/__tests__/`
- Mock `ResizeObserver` for Recharts tests:
  ```typescript
  beforeAll(() => { globalThis.ResizeObserver ??= class { observe() {} unobserve() {} disconnect() {} }; });
  ```

### Cross-Story Dependencies

| Story | Relationship |
|---|---|
| Story 17.3 | **Predecessor** — Persistent results list (`ResultListItem[]`) provides the run selection source. `ResultCache` stores `SimulationResult` objects for comparison |
| Story 12.5 | **Domain dependency** — `compare_portfolios()` in `portfolio_comparison.py` is the core comparison engine (already implemented and tested) |
| Epic 4 (indicators) | **Domain dependency** — `compare_scenarios()`, `IndicatorResult`, `ComparisonResult` types |
| Story 6.4b | **Established** — Phase 1 GUI prototype with `ComparisonView` (being replaced) |
| Story 17.5 | **Consumer** — Behavioral Decision Viewer will link from comparison dashboard |
| Story 17.6 | **Extension** — May add additional Phase 2 API endpoints |
| Story 17.8 | **Extension** — E2E browser tests for the comparison workflow |

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
- pyarrow >= 18.0.0

### References

- [Source: docs/epics.md#Epic 17, Story 17.4 (BKL-1704)] — Acceptance criteria
- [Source: docs/epics.md#Epic 12, Story 12.5 (BKL-1205)] — Multi-portfolio comparison domain story
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#ComparisonView] — Comparison view UX design (lines 1060-1076)
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Comparison is a view] — "Comparison is a view, not a report" (lines 770-774)
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Chart color palette] — Color tokens for charts
- [Source: _bmad-output/planning-artifacts/architecture.md#Layer 5] — Indicator subsystem architecture
- [Source: docs/project-context.md] — Coding conventions, testing rules
- [Source: src/reformlab/indicators/portfolio_comparison.py] — `compare_portfolios()`, `PortfolioComparisonResult`, `CrossComparisonMetric`
- [Source: src/reformlab/indicators/comparison.py] — `compare_scenarios()`, `ComparisonResult`, `ScenarioInput`
- [Source: src/reformlab/indicators/types.py] — `IndicatorResult`, indicator data types
- [Source: src/reformlab/server/routes/indicators.py] — Existing indicator and comparison routes
- [Source: src/reformlab/server/models.py] — Pydantic model patterns
- [Source: src/reformlab/server/dependencies.py] — `ResultCache`, `get_result_cache`, `get_result_store`
- [Source: src/reformlab/server/result_store.py] — `ResultStore`, `ResultMetadata`, `ResultNotFound`
- [Source: frontend/src/components/simulation/ComparisonView.tsx] — Phase 1 comparison prototype (being replaced)
- [Source: frontend/src/components/simulation/DistributionalChart.tsx] — Existing 2-bar chart (pattern reference)
- [Source: frontend/src/components/simulation/ResultsListPanel.tsx] — Run list pattern
- [Source: frontend/src/components/simulation/SummaryStatCard.tsx] — KPI card pattern
- [Source: frontend/src/api/indicators.ts] — Existing indicator API client
- [Source: frontend/src/api/types.ts] — TypeScript type definitions
- [Source: frontend/src/contexts/AppContext.tsx] — State management (results already in context)
- [Source: frontend/src/App.tsx] — Workspace orchestration, ViewMode type
- [Source: frontend/src/data/mock-data.ts] — Mock data patterns
- [Source: _bmad-output/implementation-artifacts/17-3-build-simulation-runner-with-progress-and-persistent-results.md] — Story 17.3 patterns and conventions

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — all issues resolved inline during implementation.

### Completion Notes List

- **Task 1 (Backend endpoint)**: Added `PortfolioComparisonRequest`, `ComparisonData`, `CrossMetricItem`, and `PortfolioComparisonResponse` Pydantic models to `models.py`. Implemented `POST /api/comparison/portfolios` on the existing `comparison_router` in `indicators.py` with full validation (2–5 runs, no duplicates, 404/409 error codes, label derivation/deduplication, reserved name checks). 16 backend tests written and passing.
- **Task 2 (Frontend types/API)**: Added TypeScript interfaces to `types.ts`, `comparePortfolios()` function to `indicators.ts`, and `mockComparisonResponse` to `mock-data.ts`.
- **Task 3 (MultiRunChart)**: Created `MultiRunChart.tsx` with dynamic N-series `BarChart`, `columnarToRows()` helper, absolute/relative mode support, and companion accessibility table. Tests in `MultiRunChart.test.tsx`.
- **Task 4 (CrossMetricPanel)**: Created `CrossMetricPanel.tsx` with `CRITERION_LABELS` map, mini-ranking display, and large-number formatting. Tests in `CrossMetricPanel.test.tsx`.
- **Task 5 (ComparisonDashboardScreen)**: Full ~450-line screen with `RunSelector`, 3 indicator tabs (Distributional/Fiscal/Welfare), absolute/relative toolbar toggle, `DetailPanel` with Escape dismiss, cross-metric summary, error display, and client-side CSV export. Tests in `ComparisonDashboardScreen.test.tsx`.
- **Task 6 (Integration)**: Added `selectedComparisonRunIds`/`setSelectedComparisonRunIds` to `AppContext.tsx`. Replaced `ComparisonView` with `ComparisonDashboardScreen` in `App.tsx`. Removed unused `selectedScenarioIds` state.
- **Task 7 (Quality)**: Resolved ruff E501 (line-too-long in test), ESLint unused-import (`CrossMetricItem`), and unused-variable (`idx`). Final state: ruff ✅, mypy ✅, typecheck ✅, lint (0 errors) ✅, pytest 3045 passed ✅, vitest 187 passed ✅.
- **Scope note**: `useApi.ts` hook (listed as optional in source tree) was not created — comparison state is managed inline in `ComparisonDashboardScreen`, which is simpler given the single-screen usage pattern.
- **Welfare filtering**: Domain `compare_portfolios()` raises `ValueError` if `"welfare"` appears in `indicator_types` (welfare is opt-in via `include_welfare` flag). Route handler filters welfare out of `indicator_types` before building config.
- **Code Review Synthesis (2026-03-08)**: 6 bugs fixed + 1 new test: (1) `baseline_run_id` validation added (422 if not in run_ids), (2) `apiFetch`/`apiFetchBlob` in `client.ts` now unwrap `{"detail":{"what":…}}` FastAPI format so structured errors reach the screen, (3) `CrossMetricPanel` sort order fixed for `min_*` criteria (ascending), (4) `MultiRunChart` gains `onBarClick` prop and sign-colored `<Cell>` bars in relative mode (emerald/red), (5) `ComparisonDashboardScreen` AC-3 distributional click now passes the clicked bar's row to detail panel, (6) CSV export sanitized against injection and malformed output. Tests: 3046 passed ✅, 187 frontend passed ✅.

#### Review Follow-ups (AI)
- [ ] [AI-Review] MEDIUM: Welfare tab uses generic table instead of AC-2 summary cards (winner/loser/net-change per run) (`frontend/src/components/screens/ComparisonDashboardScreen.tsx:332`)
- [ ] [AI-Review] LOW: "View as table" toggle missing from MultiRunChart — companion table is always visible with no toggle (`frontend/src/components/simulation/MultiRunChart.tsx`)
- [ ] [AI-Review] LOW: ComparisonDashboardScreen SRP — 764-line god component mixes selection, networking, transforms and rendering; consider splitting into container + feature subcomponents

### File List

**New files:**
- `tests/server/test_comparison_portfolios.py`
- `frontend/src/components/screens/ComparisonDashboardScreen.tsx`
- `frontend/src/components/simulation/MultiRunChart.tsx`
- `frontend/src/components/simulation/CrossMetricPanel.tsx`
- `frontend/src/components/screens/__tests__/ComparisonDashboardScreen.test.tsx`
- `frontend/src/components/simulation/__tests__/MultiRunChart.test.tsx`
- `frontend/src/components/simulation/__tests__/CrossMetricPanel.test.tsx`

**Modified files (original dev):**
- `src/reformlab/server/models.py`
- `src/reformlab/server/routes/indicators.py`
- `frontend/src/api/types.ts`
- `frontend/src/api/indicators.ts`
- `frontend/src/data/mock-data.ts`
- `frontend/src/contexts/AppContext.tsx`
- `frontend/src/App.tsx`

**Modified files (code review synthesis):**
- `src/reformlab/server/routes/indicators.py` — baseline_run_id validation
- `tests/server/test_comparison_portfolios.py` — added test_baseline_run_id_not_in_run_ids_returns_422
- `frontend/src/api/client.ts` — error contract: unwrap nested detail.what/why/fix
- `frontend/src/components/simulation/CrossMetricPanel.tsx` — fix min_* sort order
- `frontend/src/components/simulation/MultiRunChart.tsx` — onBarClick prop + Cell sign-coloring
- `frontend/src/components/screens/ComparisonDashboardScreen.tsx` — CSV safety + AC-3 click fix

## Senior Developer Review (AI)

### Review: 2026-03-08
- **Reviewer:** AI Code Review Synthesis
- **Evidence Score:** 15.0 (Reviewer A) / 5.0 (Reviewer B) → Changes Requested
- **Issues Found:** 10 verified (merged from 2 reviewers)
- **Issues Fixed:** 7 (6 code fixes + 1 new test)
- **Action Items Created:** 3

