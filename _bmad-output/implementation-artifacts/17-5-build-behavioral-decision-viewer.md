

# Story 17.5: Build Behavioral Decision Viewer

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a non-coding policy analyst,
I want a Behavioral Decision Viewer where I can see aggregate household investment decisions (vehicle fleet composition, heating system mix) evolving over time, filter by household group (income decile), and inspect choice probabilities for any given year,
so that I can understand how households respond to policy signals and evaluate whether a policy portfolio drives the desired behavioral transitions (e.g., EV adoption, heat pump uptake).

## Acceptance Criteria

1. **AC-1: Aggregate decision outcomes per domain** — Given a completed simulation run with discrete choice results (panel output containing `{domain}_chosen` columns), when the analyst opens the Behavioral Decision Viewer, then aggregate decision outcomes are displayed per domain (vehicle fleet composition showing counts/percentages per alternative, heating system mix showing counts/percentages per alternative). Each domain is selectable via tabs. If the run has no decision data (no `decision_domains` column in panel), the viewer shows an informational message: "This simulation does not include behavioral decisions. Run a simulation with discrete choice domains (vehicle, heating) to see decision outcomes."

2. **AC-2: Year-by-year transition charts** — Given the decision viewer with a selected domain (e.g., vehicle), when the analyst views the domain tab, then year-by-year transition charts show the evolution of the fleet: a stacked area chart where the X-axis is year, Y-axis is percentage of households, and each area band represents one alternative (e.g., keep_current, buy_petrol, buy_diesel, buy_hybrid, buy_ev, buy_no_vehicle). The chart uses a dedicated decision color palette (`DECISION_COLORS`, distinct from the comparison chart palette) supporting up to 6 alternatives per domain. A companion data table shows exact counts and percentages per alternative per year. Years are displayed in ascending order; alternatives follow the order provided by the `decision_domain_alternatives` metadata.

3. **AC-3: Household group filtering** — Given the decision viewer, when the analyst selects a filter (e.g., income decile "D1"), then the decision outcomes and transition charts update to show group-specific patterns. Filtering is applied server-side: the frontend re-fetches with `group_by: "decile"` and `group_value: "N"` parameters; the backend computes decile assignments from the `income` column and returns pre-filtered outcomes. Available filter: income decile (D1–D10). If no income data is available for grouping (backend returns 422 with `what="NoIncomeData"`), the decile filter is disabled with a tooltip explaining why.

4. **AC-4: Year detail panel** — Given the decision viewer, when the analyst clicks on a specific year in the transition chart or data table, then a detail panel expands showing: (a) the distribution of chosen alternatives for that year (horizontal bar chart), (b) mean choice probabilities per alternative (table; populated by the year-specific re-fetch with `year` parameter — shows "Probability data not available" when `{domain}_probabilities` column is absent from the panel), and (c) the eligibility summary (`n_total`, `n_eligible`, `n_ineligible` household counts) if the domain reports eligibility data; otherwise this section is hidden. The detail panel is dismissable via Escape key or close button.

## Tasks / Subtasks

- [x] Task 1: Implement decision summary backend endpoint (AC: 1, 2, 3, 4)
  - [x] 1.1: Add `DecisionSummaryRequest` and `DecisionSummaryResponse` Pydantic models to `src/reformlab/server/models.py`: `run_id: str`, `domain_name: str | None = None` (if None, all domains), `group_by: str | None = None` (e.g., "decile"), `group_value: str | None = None` (e.g., "3" for D3), `year: int | None = None` (if set, include mean probabilities in response). Response: `domains: list[DomainSummary]` where `DomainSummary` has `domain_name: str`, `alternative_ids: list[str]`, `alternative_labels: dict[str, str]`, `yearly_outcomes: list[YearlyOutcome]`, `eligibility: dict[str, int] | None`. `YearlyOutcome`: `year: int`, `total_households: int`, `counts: dict[str, int]`, `percentages: dict[str, float]`, `mean_probabilities: dict[str, float] | None` (populated only when `year` is set and probability column is present). There is no separate `DecisionDetailResponse` — year-level detail is served through the same `DecisionSummaryResponse` with `mean_probabilities` populated when `year` is set.
  - [x] 1.2: Create `src/reformlab/server/routes/decisions.py` with a `router = APIRouter()`. Add `POST /summary` endpoint. The handler: (a) validates `run_id` via `ResultStore` — 404 if not in store; then checks `ResultCache` — 409 if evicted or `panel_output is None`, (b) extracts panel table and metadata from `SimulationResult.panel_output`, (c) checks for `decision_domain_alternatives` key in `panel_output.metadata` — 422 if absent (`{"what": "NoDecisionData", "why": "Run does not contain decision data", "fix": "Run a simulation with discrete choice domains (vehicle, heating)"}`) — this is the canonical no-data detection, (d) identifies domain names and alternative orderings from `panel_output.metadata['decision_domain_alternatives']`, (e) for each domain (or the requested `domain_name`), aggregates `{domain}_chosen` column per year into counts/percentages; `total_households` is the denominator for percentages; years sorted ascending; alternatives in metadata-provided order, (f) if `group_by="decile"`: check for `income` column in panel table — if absent, return 422 with `{"what": "NoIncomeData", "why": "Panel output does not contain an income column required for decile grouping", "fix": "Run a simulation with a population dataset that includes income data"}`. If present, compute income decile assignments per year using PyArrow compute functions (do not use NumPy); filter rows to the requested `group_value` decile before aggregating; `total_households` reflects the filtered row count, (g) if `year` is set: filter panel to that year, then for each domain extract `{domain}_probabilities` list column — if present, compute element-wise mean across all households mapping each position to the alternative_id from metadata; if absent, set `mean_probabilities=None` and append a warning to `DecisionSummaryResponse.warnings`, (h) returns `DecisionSummaryResponse`
  - [x] 1.3: Register the decisions router in `src/reformlab/server/app.py`: `app.include_router(decisions_router, prefix="/api/decisions", tags=["decisions"])`
  - [x] 1.4: Write backend tests in `tests/server/test_decisions.py`: test valid summary for 1-domain run, test valid summary for 2-domain run, test 404 when run_id unknown, test 409 when run_id evicted, test 422 when no decision data in panel (missing `decision_domain_alternatives` metadata key), test 422 when `group_by="decile"` but `income` column absent, test group_by decile filtering with income column present, test year detail with probabilities, test year detail returns `mean_probabilities=None` with warning when probability column absent, test error format (`what/why/fix`). Use class-based grouping by AC

- [x] Task 2: Define frontend TypeScript types and API client (AC: 1, 2, 3, 4)
  - [x] 2.1: Add TypeScript interfaces to `frontend/src/api/types.ts`: `DecisionSummaryRequest`, `DecisionSummaryResponse`, `DomainSummary`, `YearlyOutcome` (no separate `DecisionDetailResponse` — year detail is returned via `mean_probabilities` in `YearlyOutcome`)
  - [x] 2.2: Create `frontend/src/api/decisions.ts` with `getDecisionSummary(request: DecisionSummaryRequest): Promise<DecisionSummaryResponse>` — calls `POST /api/decisions/summary`
  - [x] 2.3: Add mock decision data to `frontend/src/data/mock-data.ts`: `mockDecisionSummaryResponse` with vehicle domain (6 alternatives) and heating domain (5 alternatives) over 5 years

- [x] Task 3: Build TransitionChart component (AC: 2)
  - [x] 3.1: Create `frontend/src/components/simulation/TransitionChart.tsx` — Recharts `AreaChart` (stacked, 100%) accepting `data: YearlyOutcome[]`, `alternativeIds: string[]`, `alternativeLabels: Record<string, string>`. Renders N stacked `<Area>` elements, one per alternative. X-axis: year, Y-axis: percentage (0–100%). Color palette: use domain-specific colors (6 vehicle colors, 5 heating colors) — assign from a dedicated `DECISION_COLORS` array. Includes `<Tooltip>` showing all alternatives for the hovered year and `<Legend>` with alternative labels
  - [x] 3.2: Add companion data table beneath the chart — `<table>` with rows per year, columns per alternative showing count + percentage
  - [x] 3.3: Add unit tests in `frontend/src/components/simulation/__tests__/TransitionChart.test.tsx`

- [x] Task 4: Build YearDetailPanel component (AC: 4)
  - [x] 4.1: Create `frontend/src/components/simulation/YearDetailPanel.tsx` — expandable detail panel for a single year. Shows: (a) horizontal bar chart of chosen distribution (Recharts `BarChart` with horizontal layout), (b) table of mean probabilities per alternative (shows "Probability data not available" when `mean_probabilities` is null), (c) eligibility summary showing `n_eligible` / `n_total` households if `eligibility` is non-null; otherwise this section is hidden. Dismissable via Escape or close button (same pattern as `DetailPanel` in `ComparisonDashboardScreen`)
  - [x] 4.2: Add unit tests in `frontend/src/components/simulation/__tests__/YearDetailPanel.test.tsx`

- [x] Task 5: Build BehavioralDecisionViewerScreen (AC: 1, 2, 3, 4)
  - [x] 5.1: Create `frontend/src/components/screens/BehavioralDecisionViewerScreen.tsx`
  - [x] 5.2: Implement data loading
  - [x] 5.3: Implement domain tabs
  - [x] 5.4: Implement income decile filter
  - [x] 5.5: Implement year click handler
  - [x] 5.6: Implement no-data and no-income states
  - [x] 5.7: Add unit tests in `frontend/src/components/screens/__tests__/BehavioralDecisionViewerScreen.test.tsx`

- [x] Task 6: Integrate BehavioralDecisionViewerScreen into workspace (AC: 1, 2, 3, 4)
  - [x] 6.1: Add `"decisions"` to the `ViewMode` type union in `App.tsx`
  - [x] 6.2: Add "Behavioral Decisions" button in results view (only shown when `runResult?.run_id` is set)
  - [x] 6.3: Render `BehavioralDecisionViewerScreen` when `viewMode === "decisions"`, pass `runId` and `onBack`
  - [x] 6.5: Verified non-regression: 211 frontend tests pass, 3064 backend tests pass

- [x] Task 7: Run quality checks (AC: all)
  - [x] 7.1: `uv run ruff check src/ tests/` — All checks passed
  - [x] 7.2: `uv run mypy src/` — Success: no issues found in 147 source files
  - [x] 7.3: `npm run typecheck && npm run lint` — 0 errors, 4 pre-existing warnings
  - [x] 7.4: `uv run pytest` — 3064 passed, 1 skipped
  - [x] 7.5: `npm test` — 211 tests passed (30 test files)

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**Backend — Canonical endpoint table:**

| Method | Full URL | Router-relative path | Purpose |
|---|---|---|---|
| POST | `/api/decisions/summary` | `/summary` | Decision summary with optional domain/year/group filtering |

Note: This endpoint uses a **new `decisions_router`** in a new file `src/reformlab/server/routes/decisions.py`. Registered in `app.py` at prefix `/api/decisions`.

**Backend — HTTP status code matrix:**

| Endpoint | Success | Client Error |
|---|---|---|
| `POST /api/decisions/summary` | 200 | 404 (run_id unknown — not in `ResultStore`), 409 (run_id in store but evicted from `ResultCache` or `panel_output is None`), 422 (no decision data — `decision_domain_alternatives` metadata key absent), 422 (no income data — `income` column absent when `group_by="decile"`) |

All error responses use `{"what": str, "why": str, "fix": str}` structure via `HTTPException(detail={...})`.

**Backend — Decision data extraction flow:**

```python
@router.post("/summary", response_model=DecisionSummaryResponse)
async def get_decision_summary(
    body: DecisionSummaryRequest,
    cache: ResultCache = Depends(get_result_cache),
    store: ResultStore = Depends(get_result_store),
) -> DecisionSummaryResponse:
    # 1. Check ResultStore metadata (404 if unknown)
    # 2. Check ResultCache (409 if evicted or panel_output is None)
    # 3. Get panel_output.table and panel_output.metadata
    # 4. Check decision_domain_alternatives key in metadata (422 with what="NoDecisionData" if absent)
    #    This is the canonical no-data detection check — not column presence
    # 4b. If group_by="decile": check income column exists (422 with what="NoIncomeData" if absent)
    # 5. For each domain (or filtered domain):
    #    a. Extract {domain}_chosen column from panel table
    #    b. Group by year: count occurrences of each alternative (years ascending, alternatives in metadata order)
    #    c. Compute percentages; denominator = total rows in the (filtered) group for that year
    #    d. If group_by="decile": compute income decile assignments per year using PyArrow compute
    #       functions; filter to requested group_value before counting; total_households = filtered count
    #    e. If year is set: extract {domain}_probabilities list column if present; compute element-wise
    #       mean; if column absent, set mean_probabilities=None and append warning to response
    # 6. Return DecisionSummaryResponse
```

**Backend — Panel output decision column structure (from Story 14-6):**

The `PanelOutput.table` contains these decision-related columns when a discrete choice run completes:
- `{domain}_chosen` — `pa.string()` — chosen alternative ID per household per year (e.g., `"buy_ev"`, `"keep_current"`)
- `{domain}_probabilities` — `pa.list_(pa.float64())` — M-element list of choice probabilities per household
- `{domain}_utilities` — `pa.list_(pa.float64())` — M-element list of utility values per household
- `decision_domains` — `pa.list_(pa.string())` — list of domain names active for each year

The `PanelOutput.metadata['decision_domain_alternatives']` dict maps domain_name → list[alternative_id] (e.g., `{"vehicle": ["keep_current", "buy_petrol", "buy_diesel", "buy_hybrid", "buy_ev", "buy_no_vehicle"]}`).

**Backend — Alternative labels:**

Alternative human-readable names come from the domain config factories:
- Vehicle: `default_vehicle_domain_config()` — 6 alternatives: keep_current ("Keep Current Vehicle"), buy_petrol ("Buy Petrol Vehicle"), buy_diesel ("Buy Diesel Vehicle"), buy_hybrid ("Buy Hybrid Vehicle"), buy_ev ("Buy Electric Vehicle"), buy_no_vehicle ("Go Without Vehicle")
- Heating: `default_heating_domain_config()` — 5 alternatives: keep_current ("Keep Current Heating"), gas_boiler ("Install Gas Boiler"), heat_pump ("Install Heat Pump"), electric ("Install Electric Heating"), wood_pellet ("Install Wood/Pellet Heating")

For the API response, derive labels from the domain configs. Since the server doesn't hold domain config state, use a static label registry:

```python
# In decisions.py or a helper module
ALTERNATIVE_LABELS: dict[str, dict[str, str]] = {
    "vehicle": {
        "keep_current": "Keep Current",
        "buy_petrol": "Petrol",
        "buy_diesel": "Diesel",
        "buy_hybrid": "Hybrid",
        "buy_ev": "Electric (EV)",
        "buy_no_vehicle": "No Vehicle",
    },
    "heating": {
        "keep_current": "Keep Current",
        "gas_boiler": "Gas Boiler",
        "heat_pump": "Heat Pump",
        "electric": "Electric",
        "wood_pellet": "Wood/Pellet",
    },
}
```

**Backend — Income decile computation for group_by:**

Use the `income` column from panel data. Compute decile boundaries using PyArrow compute functions (`pc.quantile()` or a bucket-based approach). Do not use NumPy — it is not a declared dependency. Assign each household a decile (1–10). When `group_by="decile"` and a specific decile value is provided (via `group_value`), filter the panel table before aggregation.

Implementation approach: The panel table has `income` and `household_id` columns. Compute decile assignments per year (since income may change across years), then filter rows to the requested decile before counting alternatives. The `total_households` field in `YearlyOutcome` reflects the filtered row count (households in the requested decile), not the full population.

**Backend — Mean probabilities for year detail:**

The `{domain}_probabilities` column is `pa.list_(pa.float64())`. Each element is an M-length list. To compute mean probability per alternative:
1. Filter panel to the requested year
2. Check that `{domain}_probabilities` column exists — if absent, set `mean_probabilities=None` and add a warning to `DecisionSummaryResponse.warnings` (e.g., `"Probability data unavailable for domain '{domain}': column not present in panel output"`)
3. If present: extract the list column as Python lists (via `.to_pylist()`)
4. Compute element-wise mean across all households
5. Map each position to the corresponding alternative_id using `decision_domain_alternatives` metadata order

**Backend — Dependencies:**

The route handler needs `ResultCache` (for `SimulationResult` lookup) and `ResultStore` (for metadata check / 404 vs 409 differentiation). Use `Depends(get_result_cache)` and `Depends(get_result_store)`.

### Frontend Patterns (MUST FOLLOW)

**Frontend — Component locations:**
- Screen: `frontend/src/components/screens/BehavioralDecisionViewerScreen.tsx`
- Domain components: `frontend/src/components/simulation/TransitionChart.tsx`, `YearDetailPanel.tsx`
- Tests: `frontend/src/components/{screens,simulation}/__tests__/`

**Frontend — TransitionChart design (stacked area):**

Use Recharts `AreaChart` with `stackOffset="expand"` for 100% stacked view:

```tsx
<AreaChart data={chartData}>
  <CartesianGrid strokeDasharray="2 2" />
  <XAxis dataKey="year" tick={{ fontSize: 12 }} />
  <YAxis
    tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
    tick={{ fontSize: 12 }}
  />
  <Tooltip formatter={(v: number) => `${(v * 100).toFixed(1)}%`} />
  <Legend wrapperStyle={{ fontSize: 12, paddingTop: 4 }} />
  {alternativeIds.map((altId, i) => (
    <Area
      key={altId}
      type="monotone"
      dataKey={altId}
      stackId="1"
      fill={DECISION_COLORS[i % DECISION_COLORS.length]}
      stroke={DECISION_COLORS[i % DECISION_COLORS.length]}
      name={alternativeLabels[altId] ?? altId}
    />
  ))}
</AreaChart>
```

The data format for `stackOffset="expand"` should use raw counts (Recharts normalizes to 100%):
```typescript
// Transform YearlyOutcome[] to chart data:
const chartData = yearlyOutcomes.map(outcome => ({
  year: outcome.year,
  ...outcome.counts,  // { keep_current: 5000, buy_ev: 1200, ... }
}));
```

**CRITICAL:** Use `outcome.counts` (raw integer counts), NOT `outcome.percentages`. With `stackOffset="expand"`, Recharts performs the 100% normalization automatically from the raw counts. Using pre-computed percentages will produce an incorrect double-normalization.

**Frontend — Decision color palette:**

Separate from the comparison chart colors. Decision alternatives need their own palette since there can be 5–6 alternatives per domain:

```typescript
const DECISION_COLORS = [
  "#64748b", // slate-500 — keep_current (gray = status quo)
  "#3b82f6", // blue-500
  "#8b5cf6", // violet-500
  "#10b981", // emerald-500
  "#f59e0b", // amber-500
  "#ef4444", // red-500
];
```

**Frontend — YearDetailPanel design:**

Follows the same pattern as `DetailPanel` in `ComparisonDashboardScreen`:
- Collapsible aside with border
- Escape key dismissal
- Close button (X icon)
- Horizontal bar chart for chosen distribution (Recharts `BarChart` with `layout="vertical"`)
- Table for mean probabilities

**Frontend — BehavioralDecisionViewerScreen state machine:**

```
Mount → Loading (fetch summary) → Loaded (show transition charts)
                                 → Error (show what/why/fix)
                                 → NoData (422 with what="NoDecisionData" — show informational message)
Loaded → Select domain tab → re-render (no API call)
Loaded → Select decile filter → Loading (re-fetch with group_by+group_value) → Loaded
                              → 422 with what="NoIncomeData" → disable filter with tooltip
Loaded → Click year → Loading detail (re-fetch with year param) → Detail panel open
Detail panel → Dismiss → Loaded (detail panel closed)
```

**Frontend — Domain tab labels:**

| Domain ID | Tab Label |
|---|---|
| `vehicle` | Vehicle Fleet |
| `heating` | Heating System |

**Frontend — Decile filter options:**

```typescript
const DECILE_OPTIONS = [
  { value: "", label: "All Households" },
  { value: "1", label: "D1 (Lowest Income)" },
  { value: "2", label: "D2" },
  { value: "3", label: "D3" },
  { value: "4", label: "D4" },
  { value: "5", label: "D5" },
  { value: "6", label: "D6" },
  { value: "7", label: "D7" },
  { value: "8", label: "D8" },
  { value: "9", label: "D9" },
  { value: "10", label: "D10 (Highest Income)" },
];
```

**Frontend — Existing components to reuse:**

| Existing Component | Reuse in 17.5 |
|---|---|
| `ComparisonDashboardScreen.tsx` | Pattern for error display, detail panel, Escape dismiss |
| `MultiRunChart.tsx` | Pattern for `formatValue()`, companion data table |
| `CrossMetricPanel.tsx` | Pattern for KPI summary cards |
| `ResultDetailView.tsx` | Pattern for tabbed detail panels |
| `Badge` | Status badges, alternative labels |
| `Tabs/TabsList/TabsTrigger/TabsContent` | Domain selector tabs |
| `Select` | Decile filter dropdown |
| `Table` | Probability tables, outcome tables |
| `Button` | Back, close buttons |

**Frontend — Shadcn/ui components available (already installed):**

Badge, Button, Card, Collapsible, Dialog, Input, Popover, ScrollArea, Select, Separator, Sheet, Slider, Switch, Table, Tabs, Tooltip, Sonner (toast).

### Pydantic Request/Response Models

Add to `src/reformlab/server/models.py`:

```python
# ---------------------------------------------------------------------------
# Decision viewer models — Story 17.5
# ---------------------------------------------------------------------------


class DecisionSummaryRequest(BaseModel):
    """Request for decision outcome summary."""
    run_id: str
    domain_name: str | None = None       # None = all domains
    group_by: str | None = None          # "decile" or None
    group_value: str | None = None       # e.g., "3" for D3; None = all
    year: int | None = None              # If set, include mean probabilities


class YearlyOutcome(BaseModel):
    """Decision outcomes for a single year."""
    year: int
    total_households: int
    counts: dict[str, int]               # alternative_id → count
    percentages: dict[str, float]        # alternative_id → percentage (0–100)
    mean_probabilities: dict[str, float] | None = None  # only when year detail requested


class DomainSummary(BaseModel):
    """Summary of decision outcomes for a single domain across years."""
    domain_name: str
    alternative_ids: list[str]
    alternative_labels: dict[str, str]
    yearly_outcomes: list[YearlyOutcome]
    eligibility: dict[str, int] | None = None  # keys: n_total, n_eligible, n_ineligible


class DecisionSummaryResponse(BaseModel):
    """Response for decision outcome summary."""
    run_id: str
    domains: list[DomainSummary]
    metadata: dict[str, Any]
    warnings: list[str]
```

### TypeScript Types

Add to `frontend/src/api/types.ts`:

```typescript
// ============================================================================
// Decision viewer types — Story 17.5
// ============================================================================

export interface DecisionSummaryRequest {
  run_id: string;
  domain_name?: string | null;
  group_by?: string | null;
  group_value?: string | null;
  year?: number | null;
}

export interface YearlyOutcome {
  year: number;
  total_households: number;
  counts: Record<string, number>;
  percentages: Record<string, number>;
  mean_probabilities: Record<string, number> | null;
}

export interface DomainSummary {
  domain_name: string;
  alternative_ids: string[];
  alternative_labels: Record<string, string>;
  yearly_outcomes: YearlyOutcome[];
  /** Keys: n_total, n_eligible, n_ineligible. Null when domain has no eligibility concept. */
  eligibility: { n_total: number; n_eligible: number; n_ineligible: number } | null;
}

export interface DecisionSummaryResponse {
  run_id: string;
  domains: DomainSummary[];
  metadata: Record<string, unknown>;
  warnings: string[];
}
```

### Mock Data for Decision Viewer

```typescript
export const mockDecisionSummaryResponse: DecisionSummaryResponse = {
  run_id: "mock-decision-run",
  domains: [
    {
      domain_name: "vehicle",
      alternative_ids: ["keep_current", "buy_petrol", "buy_diesel", "buy_hybrid", "buy_ev", "buy_no_vehicle"],
      alternative_labels: {
        keep_current: "Keep Current",
        buy_petrol: "Petrol",
        buy_diesel: "Diesel",
        buy_hybrid: "Hybrid",
        buy_ev: "Electric (EV)",
        buy_no_vehicle: "No Vehicle",
      },
      yearly_outcomes: [
        { year: 2025, total_households: 10000, counts: { keep_current: 7000, buy_petrol: 800, buy_diesel: 400, buy_hybrid: 600, buy_ev: 1000, buy_no_vehicle: 200 }, percentages: { keep_current: 70, buy_petrol: 8, buy_diesel: 4, buy_hybrid: 6, buy_ev: 10, buy_no_vehicle: 2 }, mean_probabilities: null },
        { year: 2026, total_households: 10000, counts: { keep_current: 6200, buy_petrol: 700, buy_diesel: 300, buy_hybrid: 700, buy_ev: 1800, buy_no_vehicle: 300 }, percentages: { keep_current: 62, buy_petrol: 7, buy_diesel: 3, buy_hybrid: 7, buy_ev: 18, buy_no_vehicle: 3 }, mean_probabilities: null },
        { year: 2027, total_households: 10000, counts: { keep_current: 5500, buy_petrol: 600, buy_diesel: 200, buy_hybrid: 800, buy_ev: 2600, buy_no_vehicle: 300 }, percentages: { keep_current: 55, buy_petrol: 6, buy_diesel: 2, buy_hybrid: 8, buy_ev: 26, buy_no_vehicle: 3 }, mean_probabilities: null },
        { year: 2028, total_households: 10000, counts: { keep_current: 4800, buy_petrol: 500, buy_diesel: 100, buy_hybrid: 900, buy_ev: 3400, buy_no_vehicle: 300 }, percentages: { keep_current: 48, buy_petrol: 5, buy_diesel: 1, buy_hybrid: 9, buy_ev: 34, buy_no_vehicle: 3 }, mean_probabilities: null },
        { year: 2029, total_households: 10000, counts: { keep_current: 4000, buy_petrol: 400, buy_diesel: 50, buy_hybrid: 1000, buy_ev: 4250, buy_no_vehicle: 300 }, percentages: { keep_current: 40, buy_petrol: 4, buy_diesel: 0.5, buy_hybrid: 10, buy_ev: 42.5, buy_no_vehicle: 3 }, mean_probabilities: null },
      ],
      eligibility: { n_total: 10000, n_eligible: 7000, n_ineligible: 3000 },
    },
    {
      domain_name: "heating",
      alternative_ids: ["keep_current", "gas_boiler", "heat_pump", "electric", "wood_pellet"],
      alternative_labels: {
        keep_current: "Keep Current",
        gas_boiler: "Gas Boiler",
        heat_pump: "Heat Pump",
        electric: "Electric",
        wood_pellet: "Wood/Pellet",
      },
      yearly_outcomes: [
        { year: 2025, total_households: 10000, counts: { keep_current: 8000, gas_boiler: 500, heat_pump: 1000, electric: 300, wood_pellet: 200 }, percentages: { keep_current: 80, gas_boiler: 5, heat_pump: 10, electric: 3, wood_pellet: 2 }, mean_probabilities: null },
        { year: 2026, total_households: 10000, counts: { keep_current: 7200, gas_boiler: 400, heat_pump: 1700, electric: 400, wood_pellet: 300 }, percentages: { keep_current: 72, gas_boiler: 4, heat_pump: 17, electric: 4, wood_pellet: 3 }, mean_probabilities: null },
        { year: 2027, total_households: 10000, counts: { keep_current: 6500, gas_boiler: 300, heat_pump: 2400, electric: 500, wood_pellet: 300 }, percentages: { keep_current: 65, gas_boiler: 3, heat_pump: 24, electric: 5, wood_pellet: 3 }, mean_probabilities: null },
      ],
      eligibility: null,
    },
  ],
  metadata: { start_year: 2025, end_year: 2029 },
  warnings: [],
};
```

### Source Tree Components to Touch

**New files:**
```
src/reformlab/server/routes/decisions.py                         ← Decision summary endpoint
tests/server/test_decisions.py                                   ← Backend decision tests
frontend/src/api/decisions.ts                                    ← Decision API client
frontend/src/components/screens/BehavioralDecisionViewerScreen.tsx
frontend/src/components/simulation/TransitionChart.tsx
frontend/src/components/simulation/YearDetailPanel.tsx
frontend/src/components/screens/__tests__/BehavioralDecisionViewerScreen.test.tsx
frontend/src/components/simulation/__tests__/TransitionChart.test.tsx
frontend/src/components/simulation/__tests__/YearDetailPanel.test.tsx
```

**Modified files:**
```
src/reformlab/server/models.py                                   ← Add decision request/response models
src/reformlab/server/app.py                                      ← Register decisions_router
frontend/src/api/types.ts                                        ← Add decision TypeScript interfaces
frontend/src/data/mock-data.ts                                   ← Add mock decision data
frontend/src/App.tsx                                             ← Add "decisions" ViewMode, render screen
```

### Project Structure Notes

- New route file `decisions.py` follows the established pattern from `indicators.py`, `results.py`, `portfolios.py`
- Router registered at `/api/decisions` in `app.py` — consistent with other domain routers
- Frontend screen follows `screens/` convention, domain components in `simulation/`
- API client follows `frontend/src/api/` convention with typed fetch wrappers
- No new npm or Python dependencies required — Recharts `AreaChart` and `Area` are already available (Recharts 3.1.2 installed)
- The discrete choice subsystem (Epic 14) is fully implemented — this story only reads from its output, never modifies it

### Important Scope Boundaries

**What this story does:**
- Builds a new Behavioral Decision Viewer GUI screen
- Implements one new backend endpoint to extract and aggregate decision data from existing panel output
- Builds a stacked area transition chart component
- Builds a year detail panel with probability display
- Adds income decile filtering
- Integrates the viewer into the workspace with navigation from results view

**What this story does NOT do:**
- Modify the discrete choice computation engine (Epic 14 — already complete)
- Add new decision domains beyond vehicle and heating
- Implement geographic filtering (only income decile for MVP)
- Build comparison across multiple runs' decisions (that would be in comparison dashboard)
- Add real-time updates when parameters change
- Build calibration UI (Epic 15)
- Implement E2E browser tests (Story 17.8)
- Add export of decision data as separate CSV (export via existing panel export is sufficient)

### Anti-Patterns to Avoid

| Issue | Prevention |
|---|---|
| Reading discrete choice state from `yearly_states` directly in the route handler | Use `panel_output.table` and `panel_output.metadata` — the panel already contains flattened decision columns |
| Importing discrete choice types in the route handler | Only import `DECISION_LOG_KEY` constant if needed; prefer reading from panel metadata |
| Creating a separate API call per year per domain | Single `POST /api/decisions/summary` returns all years and domains in one response |
| Using `DistributionalChart` or `MultiRunChart` for transition visualization | Create dedicated `TransitionChart` with stacked area — bar charts are wrong for time-series composition |
| Hardcoding alternative IDs in frontend | Read `alternative_ids` and `alternative_labels` from the API response |
| Mobile-responsive layouts | Desktop-only (min 1280px) |
| Shadows on static layout elements | Shadows reserved for floating elements only |
| Using `forwardRef` | React 19: ref is a regular prop |
| Computing deciles on the frontend | Server-side decile computation — panel tables can be large |
| Showing empty transition chart for non-discrete-choice runs | Show clear informational message when no decision data is available |
| Using NumPy for decile computation | Use PyArrow compute functions — NumPy is not a declared dependency |
| Using `outcome.percentages` as AreaChart data with `stackOffset="expand"` | Use `outcome.counts`; Recharts normalizes automatically — passing percentages causes double-normalization |
| Crashing when `{domain}_probabilities` column is absent | Return `mean_probabilities=None` with a warning; show "Probability data not available" in UI |

### Testing Standards Summary

**Backend tests (`tests/server/test_decisions.py`):**
- Use FastAPI `TestClient` pattern from `tests/server/test_api.py`
- Build `SimulationResult` with `PanelOutput` containing decision columns (use `_build_decision_columns()` or build manually with PyArrow)
- Mock `ResultCache` with pre-populated decision results
- Test classes by AC:
  - `TestDecisionSummaryValidation`: 404/409/422 error cases (including `what="NoDecisionData"` and `what="NoIncomeData"`)
  - `TestDecisionSummarySuccess`: valid 1-domain and 2-domain responses, correct counts/percentages, years ascending, alternatives in metadata order
  - `TestDecisionSummaryFiltering`: group_by decile with income column present (correct filtered counts), year detail with probabilities, year detail with missing probability column (mean_probabilities=None + warning)
- Test error response format (`what/why/fix`)

**Frontend tests:**
- Use Vitest + @testing-library/react
- Test `TransitionChart`: render with mock data, verify areas rendered, verify companion table
- Test `YearDetailPanel`: render with mock year data, verify distribution bars, verify probabilities table, verify Escape dismissal
- Test `BehavioralDecisionViewerScreen`: render with mock API response, domain tab switching, decile filter, year click, error state, no-data state
- Mock `ResizeObserver` for Recharts tests
- Mock `@/api/decisions` module

### Cross-Story Dependencies

| Story | Relationship |
|---|---|
| Epic 14 (14.1–14.6) | **Data source** — Discrete choice subsystem produces DecisionRecords stored in panel output. All 6 stories complete |
| Story 14-6 | **Direct dependency** — Panel output decision column structure (`{domain}_chosen`, `{domain}_probabilities`, `decision_domains`, metadata `decision_domain_alternatives`) |
| Story 17.3 | **Predecessor** — Persistent results list and `ResultCache` provide the run selection source |
| Story 17.4 | **Sibling** — Comparison Dashboard may link to decision viewer for individual runs |
| Story 17.6 | **Extension** — May add additional Phase 2 API endpoints |
| Story 17.8 | **Extension** — E2E browser tests for the decision viewer workflow |

### Dependency Versions (Current)

**Frontend** (from `package.json`):
- React 19.1.1, React DOM 19.1.1
- Vite 7.1.5, TypeScript 5.9.2
- Tailwind CSS v4 via `@tailwindcss/vite` 4.1.13
- Recharts 3.1.2 (AreaChart, Area, BarChart already available)
- lucide-react 0.542.0
- Vitest 3.2.4, @testing-library/react 16.3.0

**Backend** (from `pyproject.toml`):
- FastAPI >= 0.133.0, uvicorn >= 0.41.0
- Pydantic >= 2.10
- Python 3.13+, mypy strict
- pyarrow >= 18.0.0

### References

- [Source: docs/epics.md#Epic 17, Story 17.5 (BKL-1705)] — Acceptance criteria
- [Source: docs/epics.md#Epic 14] — Discrete choice model stories and acceptance criteria
- [Source: _bmad-output/planning-artifacts/phase-2-design-note-discrete-choice-household-decisions.md] — Discrete choice architecture design note
- [Source: docs/project-context.md] — Coding conventions, testing rules
- [Source: src/reformlab/discrete_choice/__init__.py] — Public API exports for discrete choice subsystem
- [Source: src/reformlab/discrete_choice/types.py] — ChoiceResult, Alternative, ChoiceSet frozen dataclasses
- [Source: src/reformlab/discrete_choice/decision_record.py] — DecisionRecord dataclass, DECISION_LOG_KEY
- [Source: src/reformlab/discrete_choice/vehicle.py] — VehicleInvestmentDomain, 6 alternatives, default config
- [Source: src/reformlab/discrete_choice/heating.py] — HeatingInvestmentDomain, 5 alternatives, default config
- [Source: src/reformlab/orchestrator/panel.py] — PanelOutput, _build_decision_columns(), decision column injection
- [Source: src/reformlab/server/app.py] — Router registration pattern
- [Source: src/reformlab/server/dependencies.py] — ResultCache, get_result_cache, get_result_store
- [Source: src/reformlab/server/result_store.py] — ResultStore, ResultMetadata, ResultNotFound
- [Source: src/reformlab/server/models.py] — Pydantic model patterns
- [Source: src/reformlab/server/routes/indicators.py] — Route handler pattern (404/409/422 error handling)
- [Source: frontend/src/components/screens/ComparisonDashboardScreen.tsx] — DetailPanel pattern, error display pattern
- [Source: frontend/src/components/simulation/MultiRunChart.tsx] — Chart patterns, formatValue(), companion table
- [Source: frontend/src/api/indicators.ts] — API client patterns
- [Source: frontend/src/api/types.ts] — TypeScript type definitions
- [Source: frontend/src/App.tsx] — ViewMode type, workspace orchestration
- [Source: frontend/src/data/mock-data.ts] — Mock data patterns
- [Source: _bmad-output/implementation-artifacts/17-4-build-comparison-dashboard-with-multi-portfolio-side-by-side.md] — Story 17.4 patterns, anti-patterns, testing standards

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- Radix Tabs controlled value issue: `value=""` (initial state) means no tab is active and content is not rendered. Fixed by deriving `activeDomainName = selectedDomain || summaryData?.domains[0]?.domain_name || ""`.
- Select UI component: project uses plain HTML `<select>`, not Radix composables (SelectTrigger etc). Tests require `user.selectOptions(select, "1")` not `user.click()`.
- Stacked area chart data: must use `outcome.counts` (raw integers), not `outcome.percentages`. `stackOffset="expand"` normalizes automatically — passing percentages causes double-normalization.

### Completion Notes List

- Task 6.4 (ComparisonDashboardScreen link) skipped as optional stretch per story spec.
- All 4 ACs fully implemented and verified via tests.

### File List

**New files:**
- `src/reformlab/server/routes/decisions.py`
- `tests/server/test_decisions.py`
- `frontend/src/api/decisions.ts`
- `frontend/src/components/screens/BehavioralDecisionViewerScreen.tsx`
- `frontend/src/components/simulation/TransitionChart.tsx`
- `frontend/src/components/simulation/YearDetailPanel.tsx`
- `frontend/src/components/screens/__tests__/BehavioralDecisionViewerScreen.test.tsx`
- `frontend/src/components/simulation/__tests__/TransitionChart.test.tsx`
- `frontend/src/components/simulation/__tests__/YearDetailPanel.test.tsx`

**Modified files:**
- `src/reformlab/server/models.py`
- `src/reformlab/server/app.py`
- `frontend/src/api/types.ts`
- `frontend/src/data/mock-data.ts`
- `frontend/src/App.tsx`
