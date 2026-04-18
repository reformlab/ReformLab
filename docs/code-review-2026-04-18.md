# ReformLab — Full Codebase Review

**Date:** 2026-04-18  
**Scope:** ~53K lines Python backend, ~33K lines TypeScript/React frontend  
**Branch:** `epic-24`  
**Context:** Code was largely produced via automated planning (BMAD framework) + autonomous loop execution. This review checks whether the code is genuinely well-written and whether the test suite actually catches bugs or creates false confidence.

---

## 1. Backend Domain Layer

**Overall verdict: GOOD — clean layering, meaningful types, proper error handling.**

### Orchestrator (`src/reformlab/orchestrator/`)

The core product layer. Well-structured: `OrchestratorConfig` validates bounds in `__post_init__`, `Orchestrator.run()` has a clear year-loop with proper error propagation via `OrchestratorError`, and `OrchestratorRunner` handles workflow-to-orchestrator translation. Types are meaningful — `YearState` is frozen, `PipelineStep` is a proper union type.

Minor smell: `_capture_manifest_fields` at ~100 lines in the runner is doing too much governance plumbing and could be extracted. The `hasattr`-based duck typing for step dispatch is reasonable but slightly fragile.

Tests verify **behavioral outcomes** (year ordering, state propagation with specific data values like population incrementing by 100/year). Strong test quality.

### Indicators (`src/reformlab/indicators/`)

Compact and focused. Clean flow in `distributional.py`: assign deciles, identify numeric fields, aggregate, convert to typed `DecileIndicators`. Types are meaningful (`DistributionalConfig`, `IndicatorResult`, `DecileIndicators`). No concerns.

### Calibration (`src/reformlab/calibration/`)

Solid. The `calibrate()` method in `engine.py` is long (~290 lines) but follows a clear numbered sequence (validate, build objective, optimize, extract results, build diagnostics). The dual legacy/generalized mode adds complexity but is well-documented. Types are rich and meaningful (`CalibrationResult`, `ParameterDiagnostics`, `RateComparison`).

Tests verify **exact hand-computed values** against known beta coefficients (e.g., `pytest.approx(0.5543, abs=1e-3)`). Excellent — tests encode domain knowledge, not implementation details.

### Population Pipeline (`src/reformlab/population/`)

Clean builder pattern with fluent API. Error hierarchy with summary/reason/fix is excellent for user-facing diagnostics. Validation is thorough (duplicate labels, missing references, self-merge). `PipelineResult` is immutable with assumption chain for governance traceability.

### Discrete Choice (`src/reformlab/discrete_choice/`)

Mostly good, but has **one significant issue:**

**`step.py` fuel price injection block** — A 50-line fuel price injection block is embedded mid-method. It mixes infrastructure concerns (exogenous context lookup, `PopulationData` reconstruction) into the step's core expand/compute/reshape flow. Worse, it **silently swallows exceptions** in the broad `except Exception` handler — a fuel price injection failure is logged and ignored. **No test covers this error path.** This code should be extracted to a helper and have explicit test coverage for the failure case.

---

## 2. Server / API Layer

**Overall verdict: MEDIUM CONCERNS — functional but has god functions, missing validation, and test gaps.**

### High Severity

#### `run_simulation` is a 300-line god function

**File:** `src/reformlab/server/routes/runs.py` — `run_simulation`

This single handler does: UUID generation, population resolution, adapter selection, scenario config construction, simulation execution, manifest patching via `dataclasses.replace`, metadata persistence, panel/manifest disk save, exogenous hash computation, trust warning generation, and response construction — all inline. This is where most bugs will cluster and it is hard to reason about for correctness (especially the `finally` block that catches all exceptions at line 186). Should be decomposed into at least 3–4 helper functions.

#### Auth session memory leak

**File:** `src/reformlab/server/auth.py`

`_active_sessions` dict grows unboundedly. Expired sessions are only evicted on the next request with that token. No background pruning. `_login_attempts` also never prunes IPs that haven't retried. Over time with many logins, this leaks memory.

### Medium Severity

#### `populations.py` is 1,357 lines of mixed concerns

**File:** `src/reformlab/server/routes/populations.py`

Contains file I/O, profiling statistics (histograms, percentiles), evidence classification mapping, upload handling, and comparison logic. `_scan_populations_with_origin` alone is ~230 lines with duplicated parsing logic for folder-based and file-based populations (lines 294–517). Domain logic that belongs in the data layer, not in route handlers.

#### Inconsistent error format

The project convention is `{"what": str, "why": str, "fix": str}` via `HTTPException(detail={...})`. However:

- `data_fusion.py` has multiple bare string `detail=` responses for validation failures
- `data_fusion.py` returns `JSONResponse` directly with a non-standard `"error"` key for pipeline failures
- `populations.py` line 168 (`_map_to_canonical_evidence`) returns a bare string detail

#### Missing input validation on Pydantic models

- `RunRequest.start_year` / `end_year` have no bounds validation — `start_year=9999, end_year=1` is accepted
- `population_id` is not validated for path-traversal characters at the Pydantic level (the resolver does it later, but validation should happen at the boundary)
- `ExportRequest.run_id` has no format validation

#### Global mutable singleton pattern is fragile

**File:** `src/reformlab/server/dependencies.py`

Uses module-level `_adapter`, `_result_store`, etc. with `global` statements. Tests must monkeypatch these AND override DI at the same time (see `test_runs.py` lines 43–51 doing both `monkeypatch.setattr` and `app.dependency_overrides`). This dual-injection is a maintenance trap.

### Server Test Gaps

- **`test_api.py` — weak assertions:** Tests for `TestTemplateRoutes::test_list_templates` (lines 83–89), `TestPopulationRoutes::test_list_populations` (lines 117–124), and `TestScenarioRoutes::test_list_scenarios` (lines 143–149) only check `status == 200` and field presence. An empty `{"templates": []}` would pass.
- **Conditional logic hides failures:** `test_api.py::TestScenarioDetail::test_get_scenario_after_create_returns_scenario_response` (lines 367–411) accepts `200 OR 404 OR 422`. The test never actually validates the success path.
- **Remaining error path test gaps:** `_check_memory_preflight` still lacks a warning-path test. Direct `run_id` path-parameter traversal coverage is still thin, although POST export body validation now rejects traversal-style run IDs and auth rate limiting now has explicit 5-failures-then-429 coverage.
- **Export route tests are split:** `tests/server/test_results.py` mostly covers export error paths, while `tests/server/test_exports_integration.py` does cover CSV/Parquet success paths with actual `PanelOutput` data. Keep both suites in sync when export behavior changes.
- **Over-mocking:** Several server integration tests create `SimulationResult` with a loose `MagicMock()` manifest. `test_indicators_integration.py` is one example; the same pattern also appears in export, cache/disk loading, decisions, and portfolio comparison tests. Any access to an unexpected manifest attribute silently returns a new `MagicMock`, masking bugs.

---

## 3. Frontend

**Overall verdict: MODERATE CONCERNS — no blockers, but persistent patterns that will compound as the codebase grows.**

### Architecture Issues

#### AppContext is a god object

**File:** `frontend/src/contexts/AppContext.tsx` — ~880 lines, ~50 fields on `AppState`

Holds auth, routing, scenario lifecycle, data fetching, simulation execution, data fusion, portfolios, results, comparison, and execution matrix state in a single context. Every consumer re-renders on any change because `useMemo` depends on ~40 values. Should be split into at least AuthContext, RoutingContext, ScenarioContext, and DataContext.

#### PoliciesStageScreen is 878 lines

**File:** `frontend/src/components/screens/PoliciesStageScreen.tsx`

Manages save/load/clone/delete dialogs, conflict validation with debounce, composition state, resolution strategy, and auto-load logic all inline. The dialog state alone (lines 94–99: six `useState` calls for save dialog) should be extracted into a custom hook or sub-component.

#### Dual scenario systems coexist

AppContext maintains both `activeScenario: WorkspaceScenario` (new) AND legacy `scenarios: Scenario[]` + `selectedScenarioId` + `cloneScenario`/`deleteScenario` (old). The `startRun` callback still operates on the legacy system. This dual state is a source of subtle sync bugs and should be consolidated.

#### Dead/redundant code

- `formatTimestamp()` is defined inside the component body but is a pure function — should be module-level
- `selectedScenarioId` initial value `"reform-a"` is hardcoded and only meaningful for the legacy system
- The `template` variable is declared twice in `startRun` — the inner one shadows the outer

### Frontend Test Issues

#### Tests that assert on CSS classes instead of behavior

- `PoliciesStageScreen.test.tsx` lines 537–549: asserts `toHaveClass("lg:grid-cols-2")` and `grid-cols-1`. Breaks on any Tailwind refactor, verifies nothing about user experience.
- `mobile-layouts.test.tsx` lines 110–112: `expect(grid!.className).toContain("grid-cols-1")`
- `ScenarioCard.test.tsx` lines 113–122: asserts `toHaveClass("bg-amber-50")` and `bg-red-50` for status badges. Should test accessible text or role instead.

#### Chart tests are "renders without crashing"

`DistributionalChart.test.tsx`: all three tests just check the title text exists. They would pass if the chart rendered nothing but the title. No assertion on data bars, axes, or interaction.

#### Mock data doesn't match real types

`mobile-layouts.test.tsx` lines 43–44: `canonical_origin: "official"` and `trust_status: "canonical"`. The actual `PopulationLibraryItem` type defines `canonical_origin: "open-official" | "synthetic-public"` and `trust_status: "production-safe" | "exploratory" | ...`. Tests pass with data that could never exist at runtime.

### Frontend Bright Spots

- `api/types.ts` is clean with proper discriminated unions (`ColumnProfile`) and string literal types. Strongest part of the frontend.
- `ResultsOverviewScreen.test.tsx` is genuinely good — tests lazy loading, caching, error states, and user interactions.
- `PoliciesStageScreen.test.tsx` AC-3/AC-4 tests are thorough on behavior.

---

## 4. Test Suite Effectiveness

### Assertion Quality

| Metric | Python | TypeScript |
|--------|--------|------------|
| Weak sole assertions | Low — 19 `is not None` (used as preconditions before real assertions) | High — 594 `toBeInTheDocument()`, many as sole assertion |
| `isinstance` checks | ~110 (decorative but harmless) | N/A |
| `toBeDefined()`/`toBeTruthy()` | N/A | 26 total (low, acceptable) |
| Hand-computed value checks | Yes (calibration, orchestrator) | Rare |
| Bare `assert result` with no comparison | 0 | N/A |

### Mock Usage

- **Python:** No cases found where the module under test was mocked instead of its dependencies. Mocks target external deps (OpenFisca adapter) correctly. Loose `MagicMock()` manifests in server integration tests are the main exception because they can mask unexpected manifest attribute access.
- **TypeScript:** Some loose typing in mock data allows impossible enum values to pass through tests.

### Coverage Gaps

- `discrete_choice/step.py` silent exception handler — no test coverage
- Direct route-parameter traversal coverage for `run_id` endpoints is still thin
- Frontend chart components — presence-only tests, no behavioral assertions
- `_check_memory_preflight` — no test for the warning path

### Overall Assessment

**Python tests actually catch bugs.** They use hand-computed values, verify behavioral outcomes, and mock only external dependencies.

**Frontend tests mostly verify the app doesn't crash.** The heavy reliance on `toBeInTheDocument()` as sole assertions means many tests would pass even if the component rendered incomplete or incorrect content.

---

## Priority Fix List

### Production Risk

| Priority | Issue | Location | Status | Impact |
|----------|-------|----------|--------|--------|
| 1 | Add input validation to `RunRequest` and export run IDs | `src/reformlab/server/models.py` | Started | Rejects nonsensical years and traversal-style IDs at the boundary |
| 2 | Fix auth session and login-attempt pruning | `src/reformlab/server/auth.py` | Started | Prevents unbounded in-memory growth under repeated login traffic |
| 3 | Decompose `run_simulation` persistence/execution branches | `src/reformlab/server/routes/runs.py` | Started | Reduces bug risk around run metadata, manifests, and response construction |
| 4 | Consistent error format across routes | `data_fusion.py`, `populations.py` | Open | Preserves API error contract for frontend handling |
| 5 | Extract + test fuel price injection | `src/reformlab/discrete_choice/step.py` | Open | Avoids silent domain behavior changes when exogenous data injection fails |

### Maintainability

| Priority | Issue | Location | Status | Impact |
|----------|-------|----------|--------|--------|
| 6 | Split AppContext into focused contexts | `frontend/src/contexts/AppContext.tsx` | Open | Reduces broad re-renders and state coupling |
| 7 | Consolidate dual scenario systems | `frontend/src/contexts/AppContext.tsx` | Open | Removes sync bugs between old/new scenario state |
| 8 | Extract `populations.py` domain logic to data layer | `src/reformlab/server/routes/populations.py` | Open | Separates file scanning, evidence mapping, profiling, and route concerns |

### Test Quality

| Priority | Issue | Location | Status | Impact |
|----------|-------|----------|--------|--------|
| 9 | Add auth rate-limit, run-ID traversal, and memory-warning tests | Server tests | Started | Covers the highest-risk untested API branches |
| 10 | Replace CSS class assertions with behavioral tests | Frontend test files | Open | Reduces false coverage and Tailwind-coupled tests |
| 11 | Fix mock data type mismatches | `mobile-layouts.test.tsx` | Open | Prevents impossible population metadata from passing tests |
| 12 | Add behavioral assertions to chart tests | `DistributionalChart.test.tsx` etc. | Open | Ensures charts render data, not only headings |
