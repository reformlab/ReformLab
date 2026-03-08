

# Story 17.8: Build End-to-End GUI Workflow Tests

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a non-coding analyst,
I want the GUI to be covered by workflow-level integration tests,
so that regressions in the multi-step analyst workflows (data fusion → portfolio → simulation → results → comparison) are caught before they reach production.

## Context

The frontend currently has **211+ component-level unit tests** across 30 test files. Each screen and component is individually tested for rendering, props, and isolated user interactions. However, **no tests verify the multi-step workflows** that define the core analyst experience:

1. **Data Fusion**: Select sources → review overlap → choose merge method → generate → preview
2. **Portfolio Design**: Select templates → compose & configure → validate → save
3. **Simulation**: Configure run → execute → view results → export
4. **Results Browsing**: List past runs → select → view detail → export
5. **Comparison**: Select runs → compare → toggle views → inspect detail
6. **Cross-screen Navigation**: Moving between the above workflows via left panel navigation

Story 17.8 fills this gap by adding **workflow-level integration tests** that exercise complete user journeys within each screen and verify cross-screen navigation through the App component.

### What Already Exists

- **30 test files** in `frontend/src/components/{screens,simulation,layout,ui}/__tests__/`
- **App.test.tsx** — 2 tests covering only the auth gate (password prompt renders, heading renders)
- **Vitest + @testing-library/react** — test framework with jsdom, user-event, jest-dom matchers
- **Mock data** in `frontend/src/data/mock-data.ts` — exports `mockDataSources`, `mockMergeMethods`, `mockPopulations`, `mockTemplates`, `mockParameters`, etc.
- **API module pattern** — `vi.mock("@/api/module")` with `vi.fn()` for each exported function
- **ResizeObserver polyfill** — required for Recharts-based chart components (MultiRunChart, TransitionChart, DistributionalChart)
- **Screen components** tested individually:
  - `DataFusionWorkbench.test.tsx` — 7 tests (rendering, step navigation, source selection guards)
  - `PortfolioDesignerScreen.test.tsx` — 14 tests (step nav, template selection, save dialog, name validation)
  - `SimulationRunnerScreen.test.tsx` — 8 tests (configure view, props display, cancel)
  - `ComparisonDashboardScreen.test.tsx` — 14 tests (run selection, compare, tabs, toggle, export)
  - `BehavioralDecisionViewerScreen.test.tsx` — 9 tests (domain tabs, decile filter, year detail)

### What Does NOT Exist Yet

- No workflow tests that exercise **complete multi-step user journeys** (source selection → generation → preview in one test)
- No tests that verify **API call sequences** through a workflow (mock API called in correct order with correct arguments)
- No tests that verify **state transitions** between workflow steps after API responses
- No tests that verify **cross-screen navigation** via App component (left panel buttons, view mode transitions)
- No tests that verify **error recovery workflows** (API fails → user sees error → adjusts → retries)

## Acceptance Criteria

1. **AC-1: Core analyst workflow coverage** — Given the frontend test suite, when run, then it covers the core analyst workflow: open Data Fusion Workbench → configure and generate population → open Portfolio Designer → compose portfolio → run simulation → view results → compare two runs. Each step verifies the correct API call and resulting UI state.

2. **AC-2: CI passing** — Given the test suite, when run in CI (`npm test`), then all tests pass including the new workflow tests. Zero regressions in existing 211+ tests.

3. **AC-3: Regression detection** — Given the test suite, when a GUI component changes (e.g., button text, step flow, API call signature), then relevant workflow tests fail and identify the broken workflow step by test name and assertion.

4. **AC-4: Area coverage** — Given the test suite, when inspected, then it covers all five workflow areas: data fusion (source selection, merge method, generation), portfolio design (template selection, parameter configuration, save), simulation (run, progress, completion), results (persistence, retrieval, browsing), and comparison (multi-run selection, side-by-side display).

5. **AC-5: All quality checks pass** — `npm run typecheck`, `npm run lint`, and `npm test` all pass with zero errors. Backend quality checks (`uv run ruff check`, `uv run mypy`, `uv run pytest`) remain clean (no regressions).

## Tasks / Subtasks

- [x] Task 1: Create workflow test utilities (AC: 1, 3)
  - [x] 1.1: Create `frontend/src/__tests__/workflows/` directory
  - [x] 1.2: Create `frontend/src/__tests__/workflows/helpers.ts` — shared mock factories for API responses (`mockGenerationResult`, `mockRunResponse`, `mockResultListItem`, `mockResultDetail`, `mockComparisonResponse`, `mockDecisionSummary`), shared `ResizeObserver` polyfill setup, and shared render helpers

- [x] Task 2: Data Fusion workflow test (AC: 1, 4)
  - [x] 2.1: Create `frontend/src/__tests__/workflows/data-fusion-workflow.test.tsx`
  - [x] 2.2: Test: "completes full data fusion workflow: sources → overlap → method → generate → preview"
    - Render `DataFusionWorkbench` with `mockDataSources` (2+ providers) and `mockMergeMethods`
    - Select 2 sources → click Next → verify overlap step
    - Select merge method → click Next → verify method config step
    - Set seed → click Generate Population
    - Mock `generatePopulation()` resolves with success result
    - Verify preview step shows summary stats (record count, variable count)
    - Verify `onPopulationGenerated` callback was called
  - [x] 2.3: Test: "shows error when generation fails"
    - Select sources → advance → generate
    - Mock `generatePopulation()` rejects with `ApiError`
    - Verify error message displayed with what/why/fix content
  - [x] 2.4: Test: "enforces minimum 2 source selection before advancing"
    - Select only 1 source → verify Next disabled/blocked
    - Select 2nd source → verify Next enabled → advance
  - [x] 2.5: Test: "allows navigating back through completed steps"
    - Advance to method step → click Back → verify overlap step
    - Click Back again → verify sources step (selections preserved)

- [x] Task 3: Portfolio Designer workflow test (AC: 1, 4)
  - [x] 3.1: Create `frontend/src/__tests__/workflows/portfolio-workflow.test.tsx`
  - [x] 3.2: Test: "completes full portfolio workflow: select → compose → validate → save"
    - Render `PortfolioDesignerScreen` with mock templates (3+)
    - Select 2 templates → click Next → verify composition step
    - Verify selected templates appear in composition panel
    - Advance to review step → click "Check Conflicts"
    - Mock `validatePortfolio()` resolves with `{ conflicts: [], is_compatible: true }`
    - Click "Save Portfolio" → enter valid name → confirm
    - Mock `createPortfolio()` resolves with version_id
    - Verify `onSaved` callback was called
  - [x] 3.3: Test: "shows conflict validation errors"
    - Select 2 conflicting templates → advance to review
    - Mock `validatePortfolio()` resolves with conflicts
    - Verify conflict details displayed
  - [x] 3.4: Test: "rejects invalid portfolio name on save"
    - Advance to review → click Save → enter name with uppercase/spaces
    - Verify validation error message appears
    - Enter valid slug name → verify error clears
  - [x] 3.5: Test: "enforces minimum 2 template selection"
    - Select only 1 template → verify Next disabled
    - Select 2nd template → verify Next enabled

- [x] Task 4: Simulation Runner workflow test (AC: 1, 4)
  - [x] 4.1: Create `frontend/src/__tests__/workflows/simulation-workflow.test.tsx`
  - [x] 4.2: Test: "completes full simulation workflow: configure → run → results → detail"
    - Render `SimulationRunnerScreen` with population/template/portfolio props
    - Verify configure sub-view shows year range inputs and Run button
    - Click "Run Simulation"
    - Mock `runScenario()` resolves with success
    - Mock `listResults()` resolves with 1 completed result
    - Mock `getResult()` resolves with full detail
    - Verify results sub-view shows completed run in list
    - Click on result → verify detail view shows indicators tab, data summary, manifest
  - [x] 4.3: Test: "handles simulation failure gracefully"
    - Click Run → mock `runScenario()` rejects with `ApiError`
    - Verify error toast/message displayed
    - Verify configure sub-view is restored (can retry)
  - [x] 4.4: Test: "deletes a result from the list"
    - Seed results list with 2 items via `listResults()` mock
    - Click delete on first result → mock `deleteResult()` resolves
    - Verify result removed from list
  - [x] 4.5: Test: "exports result as CSV and Parquet"
    - Run simulation → view results → select result
    - Click export CSV → mock `exportResultCsv()` resolves
    - Click export Parquet → mock `exportResultParquet()` resolves
    - Verify both export functions called with correct run_id

- [x] Task 5: Comparison Dashboard workflow test (AC: 1, 4)
  - [x] 5.1: Create `frontend/src/__tests__/workflows/comparison-workflow.test.tsx`
  - [x] 5.2: Test: "completes full comparison workflow: select → compare → inspect"
    - Render `ComparisonDashboardScreen` with 3+ completed results (all `data_available: true`)
    - Select 2 runs via checkboxes → click "Compare"
    - Mock `comparePortfolios()` resolves with distributional + fiscal + welfare data
    - Verify distributional tab active by default with chart content
    - Click "Fiscal" tab → verify fiscal table rendered
    - Click "Welfare" tab → verify welfare data rendered
    - Toggle to Relative view → verify mode switch reflected
    - Verify Cross-Portfolio Rankings panel shows metrics
  - [x] 5.3: Test: "shows error when comparison fails"
    - Select 2 runs → click Compare
    - Mock `comparePortfolios()` rejects with `ApiError`
    - Verify error alert displayed with structured message
  - [x] 5.4: Test: "prevents comparison with evicted runs"
    - Include run with `data_available: false` in results
    - Verify evicted badge shown on that run
  - [x] 5.5: Test: "exports comparison data as CSV"
    - Complete comparison → click Export CSV
    - Verify CSV download triggered (button present and clickable)

- [x] Task 6: Cross-screen navigation workflow test (AC: 1, 3)
  - [ ] 6.1: Create `frontend/src/__tests__/workflows/analyst-journey.test.tsx`
  - [ ] 6.2: Mock all API modules used by `AppContext`:
    - `@/api/auth` → `login()` resolves with `{ token: "test-token" }`
    - `@/api/populations` → `listPopulations()` resolves with mock populations
    - `@/api/templates` → `listTemplates()`, `getTemplate()` resolve with mock data
    - `@/api/scenarios` → `listScenarios()` resolves with mock scenarios
    - `@/api/results` → `listResults()` resolves with mock results
    - `@/api/portfolios` → `listPortfolios()` resolves with mock portfolios
    - `@/api/data-fusion` → `listDataSources()`, `listMergeMethods()` resolve with mock data
    - `@/api/runs` → `runScenario()` resolves with mock run response
    - `@/api/indicators` → `getIndicators()`, `comparePortfolios()` resolve with mock data
    - `@/api/decisions` → `getDecisionSummary()` resolves with mock data
  - [ ] 6.3: Test: "authenticates and navigates through workspace views"
    - Render `<AppProvider><App /></AppProvider>`
    - Verify password prompt shown
    - Enter password → submit → mock login succeeds
    - Verify workspace loads with "ReformLab" heading
    - Click "Population" button → verify Data Fusion Workbench rendered
    - Click "Portfolio" button → verify Portfolio Designer rendered
    - Click "Simulation" button → verify Simulation Runner rendered
    - Click "Configure Policy" button → verify configuration view with ModelConfigStepper
  - [x] 6.4: Test: "navigates configuration steps and proceeds to simulation"
    - Authenticate → verify configuration view
    - Verify Population step active → click "Next Step"
    - Verify Policy step active → click "Next Step"
    - Verify Parameters step active → click "Next Step"
    - Verify Validation step active → click "Go to Simulation"
    - Verify Run Simulation view with "Run Simulation" button
  - [x] 6.5: Test: "navigates to comparison and back"
    - Authenticate → advance through configuration → run simulation (mock)
    - Wait for results view → click "Open Comparison"
    - Verify ComparisonDashboardScreen rendered
    - Click "Back to Results" → verify results view restored

- [x] Task 7: Run quality checks (AC: 2, 5)
  - [x] 7.1: `npm run typecheck` — 0 errors
  - [x] 7.2: `npm run lint` — 0 errors (4 pre-existing fast-refresh warnings OK)
  - [x] 7.3: `npm test` — all pass (237 tests, 35 test files including 26 new workflow tests)
  - [x] 7.4: `uv run ruff check src/ tests/` — 0 errors (no backend changes)
  - [x] 7.5: `uv run mypy src/` — 0 errors (no backend changes)
  - [x] 7.6: `uv run pytest tests/` — 3143 passed, 1 skipped (no backend changes)

## Dev Notes

### Architecture — Test File Organization

```
frontend/src/__tests__/
├── App.test.tsx                          ← Existing (2 tests, auth gate)
└── workflows/                            ← NEW directory
    ├── helpers.ts                         ← Shared mock factories, polyfills
    ├── data-fusion-workflow.test.tsx       ← Data Fusion Workbench workflow
    ├── portfolio-workflow.test.tsx         ← Portfolio Designer workflow
    ├── simulation-workflow.test.tsx        ← Simulation Runner workflow
    ├── comparison-workflow.test.tsx        ← Comparison Dashboard workflow
    └── analyst-journey.test.tsx           ← Cross-screen App navigation
```

### Testing Framework and Patterns

- **Vitest** (not Playwright/Cypress) — these are component integration tests using `@testing-library/react` in jsdom
- **Render pattern**: Use `render()` from `@testing-library/react`, query via `screen.getByRole()`, `screen.getByText()`
- **User interactions**: Use `userEvent.setup()` + `user.click()`, `user.type()` (preferred over `fireEvent`)
- **Async**: Use `waitFor()` for assertions after API calls resolve
- **API mocking**: `vi.mock("@/api/module")` at top level, `vi.mocked(fn).mockResolvedValueOnce()` per test

### ResizeObserver Polyfill

Required for any test that renders Recharts components (MultiRunChart, DistributionalChart, TransitionChart). Place in `helpers.ts`:

```typescript
export function setupResizeObserver(): void {
  globalThis.ResizeObserver ??= class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}
```

Call `setupResizeObserver()` in `beforeAll()` of tests that render charts.

### Browser API Polyfills for Export Tests

Tests that trigger CSV/Parquet exports (Tasks 4.5, 5.5) invoke browser APIs (`URL.createObjectURL`, `Blob`, anchor `click`) that are unavailable or incomplete in jsdom. Add to `helpers.ts` and call in `beforeAll()` of export-related test suites:

```typescript
export function setupExportMocks(): void {
  globalThis.URL.createObjectURL ??= vi.fn(() => "blob:mock-url");
  globalThis.URL.revokeObjectURL ??= vi.fn();
}
```

If a test creates a download anchor and calls `.click()`, stub it via `vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {})` to prevent jsdom navigation errors.

### Mock Factory Pattern (helpers.ts)

Follow the existing pattern from `test_exports_integration.py` / screen test files — factory functions with overrides:

```typescript
export function mockResultListItem(overrides: Partial<ResultListItem> = {}): ResultListItem {
  return {
    run_id: "run-001",
    timestamp: "2026-03-08T00:00:00Z",
    run_kind: "scenario",
    start_year: 2025,
    end_year: 2035,
    row_count: 1000,
    status: "completed",
    data_available: true,
    template_name: "carbon_tax",
    policy_type: "carbon_tax",
    portfolio_name: null,
    ...overrides,
  };
}
```

### API Mock Setup Pattern for Screen-Level Workflow Tests

Each screen workflow test mocks only the APIs that screen uses:

```typescript
// data-fusion-workflow.test.tsx
vi.mock("@/api/data-fusion", () => ({
  generatePopulation: vi.fn(),
}));

// portfolio-workflow.test.tsx
vi.mock("@/api/portfolios", () => ({
  validatePortfolio: vi.fn(),
  createPortfolio: vi.fn(),
  deletePortfolio: vi.fn(),
}));
```

### API Mock Setup for App-Level Tests (analyst-journey.test.tsx)

The `analyst-journey.test.tsx` renders `<AppProvider><App /></AppProvider>`, which triggers data fetching on mount. **All API modules** must be mocked:

```typescript
vi.mock("@/api/auth", () => ({ login: vi.fn() }));
vi.mock("@/api/populations", () => ({ listPopulations: vi.fn() }));
vi.mock("@/api/templates", () => ({ listTemplates: vi.fn(), getTemplate: vi.fn() }));
vi.mock("@/api/scenarios", () => ({ listScenarios: vi.fn(), getScenario: vi.fn(), createScenario: vi.fn(), cloneScenario: vi.fn() }));
vi.mock("@/api/results", () => ({ listResults: vi.fn(), getResult: vi.fn(), deleteResult: vi.fn(), exportResultCsv: vi.fn(), exportResultParquet: vi.fn() }));
vi.mock("@/api/portfolios", () => ({ listPortfolios: vi.fn() }));
vi.mock("@/api/data-fusion", () => ({ listDataSources: vi.fn(), listMergeMethods: vi.fn() }));
vi.mock("@/api/runs", () => ({ runScenario: vi.fn() }));
vi.mock("@/api/indicators", () => ({ getIndicators: vi.fn(), comparePortfolios: vi.fn() }));
vi.mock("@/api/decisions", () => ({ getDecisionSummary: vi.fn() }));
vi.mock("@/api/exports", () => ({ exportCsv: vi.fn(), exportParquet: vi.fn() }));
```

The `beforeEach` must configure default mock return values for the auto-fetch hooks:

```typescript
beforeEach(() => {
  sessionStorage.clear();
  vi.mocked(listPopulations).mockResolvedValue([mockPopulationItem()]);
  vi.mocked(listTemplates).mockResolvedValue([mockTemplateListItem()]);
  vi.mocked(getTemplate).mockResolvedValue(mockTemplateDetail());
  vi.mocked(listScenarios).mockResolvedValue([]);
  vi.mocked(listResults).mockResolvedValue([]);
  vi.mocked(listPortfolios).mockResolvedValue([]);
  vi.mocked(listDataSources).mockResolvedValue({ insee: [mockDataSourceItem()] });
  vi.mocked(listMergeMethods).mockResolvedValue([mockMergeMethodItem()]);
});
```

### Auth in App-Level Tests

`AppContext` requires authentication before showing the Workspace. The test must:
1. Mock `login()` to resolve with `{ token: "test-token" }`
2. Enter password in PasswordPrompt
3. Click "Enter" button
4. `waitFor()` workspace heading to appear

```typescript
vi.mocked(login).mockResolvedValueOnce({ token: "test-token" });
const user = userEvent.setup();
render(<AppProvider><App /></AppProvider>);
await user.type(screen.getByPlaceholderText(/password/i), "test-password");
await user.click(screen.getByRole("button", { name: /enter/i }));
await waitFor(() => {
  expect(screen.getByText("ReformLab")).toBeInTheDocument();
});
```

### Screen Component Props (for screen-level workflow tests)

**DataFusionWorkbench:**
```typescript
<DataFusionWorkbench
  sources={mockDataSources}        // from mock-data.ts
  methods={mockMergeMethods}        // from mock-data.ts
  initialResult={null}
  onPopulationGenerated={vi.fn()}
/>
```

**PortfolioDesignerScreen:**
```typescript
<PortfolioDesignerScreen
  templates={mockTemplates}           // array of TemplateListItem
  savedPortfolios={[]}
  onSaved={vi.fn()}
  onDeleted={vi.fn()}
/>
```

**SimulationRunnerScreen:**
```typescript
<SimulationRunnerScreen
  selectedPopulationId="pop-001"
  selectedPortfolioName={null}
  selectedTemplateName="carbon_tax"
  onCancel={vi.fn()}
/>
```

**ComparisonDashboardScreen:**
```typescript
<ComparisonDashboardScreen
  results={[mockResultListItem({ run_id: "r1" }), mockResultListItem({ run_id: "r2" })]}
  onBack={vi.fn()}
/>
```

### Navigation Flow Through App

The `Workspace` component (inside App) uses `viewMode` state to switch screens:

| Left Panel Button | Sets viewMode to | Renders |
|---|---|---|
| "Population" | `data-fusion` | `DataFusionWorkbench` |
| "Portfolio" | `portfolio` | `PortfolioDesignerScreen` |
| "Simulation" | `runner` | `SimulationRunnerScreen` |
| "Configure Policy" | `configuration` | ModelConfigStepper + step screens |

| Action | viewMode transition |
|---|---|
| Config "Go to Simulation" | `configuration` → `run` |
| "Run Simulation" button | `run` → `progress` → `results` |
| "Open Comparison" button | `results` → `comparison` |
| "Behavioral Decisions" button | `results` → `decisions` |
| "Back to Results" (comparison) | `comparison` → `results` |

### Existing Mock Data (from `frontend/src/data/mock-data.ts`)

Available for reuse in tests without creating new factories:
- `mockDataSources` — `Record<string, MockDataSource[]>` with 4 providers
- `mockMergeMethods` — `MockMergeMethod[]` with 3 methods
- `mockPopulations` — `Population[]` with 3 populations
- `mockTemplates` — `Template[]` with 4 templates
- `mockParameters` — `Parameter[]` with policy parameters
- `mockScenarios` — `Scenario[]` with 3 scenarios
- `mockSummaryStats` — `SummaryStatistic[]` with 3 stats

**CRITICAL**: The `mockTemplates` from `mock-data.ts` use the `Template` type (camelCase fields: `id, name, type, description, parameterCount, parameterGroups`) which is consumed directly by workspace component props. API mocks for `listTemplates()` / `getTemplate()` must return `TemplateListItem` (snake_case fields from `api/types.ts`). These are different types — always verify the prop type expected by each screen component and use the matching shape in API mocks vs direct props.

### Workflow vs Component Test Distinction

| Aspect | Existing Component Tests | New Workflow Tests |
|---|---|---|
| Scope | Single component rendering | Multi-step journey through a screen |
| API calls | One mock per test | Sequence of mocks in order |
| State | Initial → one action → assert | Initial → N actions → intermediate + final asserts |
| User actions | 1-2 interactions | 5-10+ interactions per test |
| Regressions | Catches prop/render breaks | Catches flow/integration breaks |

### Anti-Patterns to Avoid

| Issue | Prevention |
|---|---|
| Testing implementation details (CSS classes, internal state) | Query by role/text/label, assert user-visible outcomes |
| Fragile selectors on controls whose text may change (Export, Compare) | Prefer `getByRole("button", { name: /export/i })` with regex, or add stable `aria-label` to critical journey controls |
| Forgetting ResizeObserver polyfill in chart tests | Import `setupResizeObserver` from helpers.ts, call in beforeAll |
| Not clearing mocks between tests | Use `vi.clearAllMocks()` in `beforeEach` or `afterEach` |
| Hardcoding mock data instead of using factories | Use `mockResultListItem(overrides)` pattern for maintainability |
| Testing the same thing as existing component tests | Focus on MULTI-STEP flows, not individual renders |
| Rendering full App when testing a single screen | Use screen component directly for workflow tests; App only for navigation tests |
| Forgetting async/await on user interactions | All `user.click()`, `user.type()` are async — always await them |
| Not using `waitFor` after API calls | API mocks resolve asynchronously — wrap post-call assertions in `waitFor()` |
| Mocking too much of AppContext for screen tests | Screen-level tests don't need AppContext — pass props directly |
| Testing error message exact strings | Assert error presence, not exact text (which may change) |
| Missing `sessionStorage.clear()` between App tests | Always clear in `beforeEach` to reset auth state |

### Existing Tests to NOT Break

Current frontend test counts (must all pass after changes):
- `frontend/src/__tests__/App.test.tsx` — 2 tests
- `frontend/src/components/screens/__tests__/` — 52 tests across 5 files
- `frontend/src/components/simulation/__tests__/` — ~150 tests across 18 files
- `frontend/src/components/layout/__tests__/` — 6 tests
- `frontend/src/components/ui/__tests__/` — 4 tests

No existing test files are modified. New tests are additive only.

### Expected Test Count

New tests: ~20-25 tests across 5 test files + 1 helpers file.

### Cross-Story Dependencies

| Story | Relationship |
|---|---|
| Story 17.1 | Built DataFusionWorkbench — workflow test exercises its 5-step flow |
| Story 17.2 | Built PortfolioDesignerScreen — workflow test exercises its 3-step flow |
| Story 17.3 | Built SimulationRunnerScreen, ResultStore — workflow test exercises configure→run→results |
| Story 17.4 | Built ComparisonDashboardScreen — workflow test exercises multi-run comparison |
| Story 17.5 | Built BehavioralDecisionViewerScreen — covered indirectly via navigation test |
| Story 17.6 | Standardized error format — workflow tests verify structured error display |
| Story 17.7 | Persistent results — workflow tests use `data_available: true` mock data |

### Scope Boundaries

**What this story does:**
- Creates 5 new workflow test files + 1 shared helpers file
- Tests multi-step user journeys within each major screen
- Tests cross-screen navigation via App component
- Tests API call sequences and error handling in workflow context

**What this story does NOT do:**
- Modify any source code (frontend or backend)
- Add browser-level E2E tests (Playwright, Cypress)
- Add visual regression tests
- Add performance/load tests
- Test backend API directly (backend has its own test suite)
- Duplicate existing component-level test coverage

### References

- [Source: frontend/src/App.tsx] — Workspace component, ViewMode type, navigation flow, screen mounting
- [Source: frontend/src/contexts/AppContext.tsx] — AppState interface, auto-fetch hooks, auth flow
- [Source: frontend/src/api/] — All API client modules (13 files, 24 exported functions)
- [Source: frontend/src/api/types.ts] — TypeScript interfaces for all API request/response types
- [Source: frontend/src/api/client.ts] — apiFetch wrapper, ApiError class, auth token management
- [Source: frontend/src/data/mock-data.ts] — Mock data exports for populations, templates, parameters, data sources
- [Source: frontend/src/components/screens/DataFusionWorkbench.tsx] — 5-step wizard, generatePopulation() call
- [Source: frontend/src/components/screens/PortfolioDesignerScreen.tsx] — 3-step wizard, validatePortfolio(), createPortfolio() calls
- [Source: frontend/src/components/screens/SimulationRunnerScreen.tsx] — 3 sub-views, runScenario(), listResults(), getResult() calls
- [Source: frontend/src/components/screens/ComparisonDashboardScreen.tsx] — Run selector, comparePortfolios() call, tabs, toggle
- [Source: frontend/src/components/screens/BehavioralDecisionViewerScreen.tsx] — Domain tabs, getDecisionSummary() call
- [Source: frontend/src/__tests__/App.test.tsx] — Existing App test pattern (AppProvider wrap, sessionStorage clear)
- [Source: frontend/vite.config.ts:21-26] — Vitest config (jsdom, setup file, globals)
- [Source: frontend/src/test/setup.ts] — Jest-dom matchers import
- [Source: docs/epics.md#Story 17.8 (BKL-1708)] — Original acceptance criteria

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6 (dev) + claude-sonnet-4-6 (code-review-synthesis)

### Debug Log References

### Completion Notes List

- Created `frontend/src/__tests__/workflows/` directory with 5 workflow test files + helpers
- 26 new workflow tests across 5 test files; all 237 frontend tests pass
- Code-review-synthesis fixes applied: error UI assertion added to data-fusion error test (Task 2.3); download trigger assertion added to comparison export test (Task 5.5); `mockDecisionSummary` factory added to helpers.ts per Task 1.2 spec

### File List

- `frontend/src/__tests__/workflows/helpers.ts` — shared mock factories + polyfills
- `frontend/src/__tests__/workflows/data-fusion-workflow.test.tsx` — Tasks 2.2–2.5
- `frontend/src/__tests__/workflows/portfolio-workflow.test.tsx` — Tasks 3.2–3.5
- `frontend/src/__tests__/workflows/simulation-workflow.test.tsx` — Tasks 4.2–4.5
- `frontend/src/__tests__/workflows/comparison-workflow.test.tsx` — Tasks 5.2–5.5
- `frontend/src/__tests__/workflows/analyst-journey.test.tsx` — Tasks 6.3–6.5


## Senior Developer Review (AI)

### Review: 2026-03-08
- **Reviewer:** AI Code Review Synthesis
- **Evidence Score:** 8.0 (Reviewer A) / 22.0 (Reviewer B) → REJECT (pre-fix)
- **Issues Found:** 4 verified (2 medium, 2 governance)
- **Issues Fixed:** 4
- **Action Items Created:** 0

#### Review Follow-ups (AI)

*(All verified code issues were fixed during synthesis. No deferred items.)*
