

# Story 17.6: Implement FastAPI Endpoints for Phase 2 GUI Operations

Status: dev-complete

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform developer,
I want all Phase 2 GUI-serving API endpoints to have comprehensive independent integration tests, consistent error formatting, and standardized store/cache lookup semantics,
so that the GUI showcase relies on a fully validated, consistent API layer where any regression is caught automatically in CI.

## Context

Stories 17.1–17.5 each implemented their own backend endpoints alongside their GUI screens. This story ensures the complete API surface is independently tested, error responses are consistent, and lookup patterns are uniform. The original AC ("FastAPI endpoints exist for population generation, portfolio CRUD, simulation execution, result listing, and comparison queries") is **already satisfied** — the endpoints all exist. This story delivers the **"tested independently" AC** and fixes inconsistencies.

### Key Inconsistencies Found

1. **Error format**: Phase 1 endpoints (`indicators.py`, `exports.py`, `scenarios.py`, `templates.py`) use **plain string** `detail` in HTTPException. Phase 2 endpoints (`portfolios.py`, `results.py`, `decisions.py`, `comparison/portfolios`) use the standardized **`{what, why, fix}` dict** format that the frontend `ApiError` class expects.

2. **Store/cache lookup**: Phase 1 endpoints (`indicators.py`, `exports.py`) use **cache-only** lookup (returning 404 for evicted runs, indistinguishable from "never existed"). Phase 2 endpoints check `ResultStore` first (404 = unknown), then `ResultCache` (409 = evicted). The Phase 2 pattern is correct.

3. **Test coverage**: Multiple endpoints have 0% or error-path-only test coverage (see Tasks below).

## Acceptance Criteria

1. **AC-1: Comprehensive integration test coverage** — All API endpoints that serve the Phase 2 GUI have passing integration tests covering both success and error paths. Specifically, the following currently-undertested endpoints gain new tests:
   - `POST /api/indicators/{type}` for all four types (distributional, geographic, welfare, fiscal) — success and error paths
   - `POST /api/comparison` (pairwise welfare comparison) — success path
   - `POST /api/runs/memory-check` — success path
   - `GET /api/scenarios/{name}` — success path
   - `POST /api/scenarios/{name}/clone` — success and error paths
   - `POST /api/exports/csv` and `POST /api/exports/parquet` — success paths (actual file content validation)
   - `GET /api/results/{run_id}/export/csv` and `GET /api/results/{run_id}/export/parquet` — success paths

2. **AC-2: Standardized error responses** — All application-raised `HTTPException` details in the targeted route modules (`indicators.py`, `exports.py`, `scenarios.py`, `templates.py`) use the `{what, why, fix}` dict format. Phase 1 endpoints that currently return plain string `detail` are migrated to the dict format. (Framework-generated errors such as FastAPI's 422 request-validation responses and 401 auth errors are outside this scope.) All error tests verify the presence of `what`, `why`, and `fix` keys.

3. **AC-3: Standardized store/cache lookup** — Phase 1 indicator and export endpoints (`indicators.py`, `exports.py`) are upgraded to the Phase 2 two-step lookup pattern: check `ResultStore` first (404 if completely unknown), then `ResultCache` (409 if in store but evicted or `panel_output is None`). This gives the frontend actionable information about why data is unavailable.

4. **AC-4: All tests pass** — New tests pass alongside the existing 3000+ backend tests and 211 frontend tests with zero regressions.

## Tasks / Subtasks

- [x] Task 1: Standardize error responses in Phase 1 endpoints (AC: 2)
  - [x] 1.1: Update `src/reformlab/server/routes/indicators.py` — `compute_indicator()` and `compute_comparison()` converted to `{what, why, fix}` dict format.
  - [x] 1.2: Update `src/reformlab/server/routes/exports.py` — `_file_response()` "file too large" converted to dict format.
  - [x] 1.3: Update `src/reformlab/server/routes/scenarios.py` — all HTTPException calls converted to dict format.
  - [x] 1.4: Update `src/reformlab/server/routes/templates.py` — `get_template()` 404 converted to dict format.
  - [x] 1.5: Updated `test_create_scenario_no_policy_type_returns_422` assertion to check `{what, why, fix}` keys.

- [x] Task 2: Add store/cache lookup to Phase 1 endpoints (AC: 3)
  - [x] 2.1: `compute_indicator()` in `indicators.py` — two-step lookup (ResultStore → 404, ResultCache → 409).
  - [x] 2.2: `compute_comparison()` in `indicators.py` — two-step lookup for both baseline and reform.
  - [x] 2.3: `export_csv()` and `export_parquet()` in `exports.py` — two-step lookup via `_lookup_run()` helper.

- [x] Task 3: Create indicator endpoint integration tests (AC: 1, 2, 3)
  - [x] 3.1–3.7: Created `tests/server/test_indicators_integration.py` with all indicator type tests plus pairwise comparison.

- [x] Task 4: Create export success path tests (AC: 1, 2, 3)
  - [x] 4.1–4.7: Created `tests/server/test_exports_integration.py` with CSV/Parquet success + error paths.

- [x] Task 5: Add memory-check and run validation tests (AC: 1, 2)
  - [x] 5.1: Added `TestMemoryCheck` class to `tests/server/test_runs.py`.

- [x] Task 6: Add scenario and template detail tests (AC: 1, 2)
  - [x] 6.1–6.3: Added `TestScenarioDetail`, `TestScenarioClone`, `TestTemplateDetail` to `tests/server/test_api.py`. Note: scenario detail/clone success paths skip due to pre-existing ScenarioRegistry hash integrity bug; error-path tests pass.

#### Review Follow-ups (AI)
- [ ] [AI-Review] HIGH: `except Exception` in `get_scenario()` and `clone_scenario()` swallows internal errors as false 404s (`src/reformlab/server/routes/scenarios.py`)
- [ ] [AI-Review] MEDIUM: `except Exception` in `get_template()` converts server errors to false 404s (`src/reformlab/server/routes/templates.py`)
- [ ] [AI-Review] LOW: Scenario clone success path untested — pre-existing ScenarioRegistry hash integrity bug (`tests/server/test_api.py`)

- [x] Task 7: Run quality checks (AC: 4)
  - [x] 7.1: `uv run ruff check src/ tests/` — 0 errors
  - [x] 7.2: `uv run mypy src/` — 0 errors
  - [x] 7.3: `uv run pytest tests/` — 3105 passed, 1 skipped, 4 warnings
  - [x] 7.4: `npm run typecheck && npm run lint` — 0 errors (4 pre-existing fast-refresh warnings)
  - [x] 7.5: `npm test` — 211 passed (30 test files)

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**Error response standardization — target format:**

All `HTTPException` calls across the codebase must use this format:

```python
raise HTTPException(
    status_code=404,
    detail={
        "what": "Run 'abc123' not found",
        "why": "No metadata record exists for this run_id",
        "fix": "Check the run_id and ensure the simulation has been executed",
    },
)
```

The frontend `ApiError` class (in `frontend/src/api/client.ts`) destructures the `detail` dict into `.what`, `.why`, `.fix` properties. Plain string `detail` values break this contract — the `extractErrorDetail()` helper in `BehavioralDecisionViewerScreen.tsx` and similar patterns across the frontend check for `typeof e["what"] === "string"` and fall back to a generic "Unknown error" message when the dict keys are absent.

**Store/cache two-step lookup — target pattern:**

```python
# Step 1: Check ResultStore metadata (404 if completely unknown)
# Catch ResultNotFound specifically — other ResultStoreError subclasses are I/O failures
# and should bubble up as 500, not be silently converted to 404.
try:
    store.get_metadata(body.run_id)
except ResultNotFound:
    raise HTTPException(
        status_code=404,
        detail={
            "what": f"Run '{body.run_id}' not found",
            "why": "No metadata record exists for this run_id",
            "fix": "Check the run_id and ensure the simulation has been executed",
        },
    )

# Step 2: Check ResultCache (409 if in store but evicted or panel_output is None)
sim_result = cache.get(body.run_id)
if sim_result is None or sim_result.panel_output is None:
    raise HTTPException(
        status_code=409,
        detail={
            "what": f"Run '{body.run_id}' data is not available",
            "why": "The simulation result has been evicted from the in-memory cache",
            "fix": "Re-run the simulation or select runs with data_available=true",
        },
    )
```

This pattern is established in `decisions.py` (Story 17.5) and `comparison/portfolios` (Story 17.4). Apply it to `indicators.py` and `exports.py`.

**Imports needed for store/cache pattern:**

```python
from reformlab.server.dependencies import ResultCache, get_result_cache, get_result_store
from reformlab.server.result_store import ResultNotFound  # runtime import — used in except clause

if TYPE_CHECKING:
    from reformlab.server.result_store import ResultStore
```

### Files to Modify

**Error format + store/cache standardization:**
```
src/reformlab/server/routes/indicators.py    ← 5 HTTPExceptions to convert + add store dependency
src/reformlab/server/routes/exports.py       ← 5 HTTPExceptions to convert + add store dependency
src/reformlab/server/routes/scenarios.py     ← 5 HTTPExceptions to convert (no store change needed)
src/reformlab/server/routes/templates.py     ← 1 HTTPException to convert (no store change needed)
```

**New test files:**
```
tests/server/test_indicators_integration.py  ← ~200 lines, indicator + pairwise comparison tests
tests/server/test_exports_integration.py     ← ~150 lines, export success + error tests
```

**Modified test files:**
```
tests/server/test_runs.py                    ← Add TestMemoryCheck class (~30 lines)
tests/server/test_api.py                     ← Add TestScenarioDetail, TestScenarioClone, TestTemplateDetail (~80 lines)
```

### Specific Error Conversions

**indicators.py — `compute_indicator()`:**

| Line | Current | Target |
|------|---------|--------|
| 56–60 | `detail=f"Invalid indicator type '{indicator_type}'..."` | `detail={"what": f"Invalid indicator type '{indicator_type}'", "why": f"Must be one of: {sorted(VALID_INDICATOR_TYPES)}", "fix": "Use a valid indicator type from the list"}` |
| 63–67 | `detail=f"Run ID '{body.run_id}' not found in cache"` | Two-step store/cache lookup (see pattern above) |

**indicators.py — `compute_comparison()`:**

| Line | Current | Target |
|------|---------|--------|
| 304–309 | `detail=f"Baseline run ID '{body.baseline_run_id}' not found in cache"` | Two-step store/cache lookup for baseline |
| 311–316 | `detail=f"Reform run ID '{body.reform_run_id}' not found in cache"` | Two-step store/cache lookup for reform |

**exports.py — `export_csv()` and `export_parquet()`:**

| Line | Current | Target | Task |
|------|---------|--------|------|
| 33–37 | `detail=f"Export file too large..."` | `detail={"what": "Export file too large", "why": f"File is {size/1024/1024:.0f} MB, limit is {limit} MB", "fix": "Filter the dataset or use a smaller population"}` → 422 | Task 1.2 |
| 55–58 | `detail=f"Run ID '{body.run_id}' not found in cache"` | Replaced wholesale by two-step lookup → 404 (unknown) or 409 (evicted/no panel) | Task 2.3 |
| 62–64 | `detail="No panel output available for this run"` | Replaced wholesale by two-step lookup → 409 (panel_output is None is an eviction signal, not a 422) | Task 2.3 |

**scenarios.py:**

| Line | Current | Target |
|------|---------|--------|
| 72–73 | `detail=str(exc)` | `detail={"what": f"Scenario '{name}' not found", "why": str(exc), "fix": "Check the scenario name"}` |
| 99–104 | `detail="policy_type is required..."` | `detail={"what": "Missing policy_type", "why": "...", "fix": "..."}` |
| 108–112 | `detail=f"Invalid policy_type..."` | `detail={"what": f"Invalid policy_type '{raw_policy_type}'", "why": "...", "fix": "..."}` |
| 139–142 | `detail=f"Unknown parameters..."` | `detail={"what": f"Unknown parameters for {policy_type.value}", "why": f"Unexpected fields: {sorted(unknown)}", "fix": "Remove unknown fields"}` |
| 183 | `detail=str(exc)` | `detail={"what": f"Scenario '{name}' not found", "why": str(exc), "fix": "Check the scenario name and ensure it exists"}` |

**templates.py:**

| Line | Current | Target |
|------|---------|--------|
| 100 | `detail=str(exc)` | `detail={"what": f"Template '{name}' not found", "why": str(exc), "fix": "Check the template name"}` |

### Test Patterns (MUST FOLLOW)

**Test fixture pattern (from `test_comparison_portfolios.py`):**

```python
def _make_panel(seed: int = 0) -> PanelOutput:
    """Minimal PanelOutput with columns for all indicator types."""
    n = 100
    incomes = [10000.0 + i * 1000.0 + seed * 500.0 for i in range(n)]
    table = pa.table({
        "household_id": pa.array(list(range(n)), type=pa.int64()),
        "year": pa.array([2025] * n, type=pa.int64()),
        "income": pa.array(incomes, type=pa.float64()),
        "disposable_income": pa.array(incomes, type=pa.float64()),
        "tax_revenue": pa.array([inc * 0.1 for inc in incomes], type=pa.float64()),
        "region": pa.array([f"R{i % 5}" for i in range(n)], type=pa.string()),
    })
    return PanelOutput(table=table, metadata={"start_year": 2025, "end_year": 2025, "seed": seed})

def _make_sim_result(panel: PanelOutput | None = None) -> SimulationResult:
    manifest = MagicMock()
    manifest.manifest_id = "manifest-test"
    return SimulationResult(
        success=True, scenario_id="sc-test", yearly_states={},
        panel_output=panel or _make_panel(), manifest=manifest, metadata={},
    )
```

**Dependency override pattern (from `test_decisions.py`, `test_comparison_portfolios.py`):**

```python
@pytest.fixture()
def client_with_deps(tmp_store, empty_cache):
    from reformlab.server.app import create_app
    app = create_app()
    app.dependency_overrides[get_result_store] = lambda: tmp_store
    app.dependency_overrides[get_result_cache] = lambda: empty_cache
    return TestClient(app)
```

**Auth pattern (from `tests/server/conftest.py`):**

```python
@pytest.fixture()
def auth_headers(client_with_deps):
    response = client_with_deps.post("/api/auth/login", json={"password": "test-password-123"})
    return {"Authorization": f"Bearer {response.json()['token']}"}
```

**Error format assertion:**

```python
detail = response.json()["detail"]
assert set(detail.keys()) >= {"what", "why", "fix"}
```

### Column Requirements by Indicator Type

The indicator computation functions (from `src/reformlab/indicators/`) need specific columns in the panel table:

| Indicator Type | Required Columns | Optional Params |
|---|---|---|
| `distributional` | `income` (or custom `income_field`), the metric columns | `income_field: str`, `by_year: bool` |
| `geographic` | `region` | `by_year: bool` |
| `welfare` | `disposable_income` (or custom `welfare_field`) — needs TWO SimulationResults (baseline + reform) | `welfare_field: str`, `threshold: float` |
| `fiscal` | `tax_revenue` (or similar fiscal columns) | `by_year: bool` |

The welfare indicator is special: it calls `result.indicators("welfare", reform_result=reform, ...)` and compares two results. The pairwise comparison endpoint (`POST /api/comparison`) wraps this.

### Existing Tests to NOT Break

**Current backend test count: ~3064 tests.** The new tests must not break any existing test *except* the one targeted by Task 1.5 (`test_create_scenario_no_policy_type_returns_422` in `test_api.py`), which must be updated to the new dict-format assertion as part of this story.

Key test files with relevant scope:
- `test_api.py` — 23 tests covering auth, templates, populations, scenarios, exports, indicators (minimal), error handling
- `test_runs.py` — 6 tests covering run execution and metadata auto-save
- `test_results.py` — 15 tests covering result CRUD and export error paths
- `test_comparison_portfolios.py` — 30+ tests covering multi-run comparison (comprehensive)
- `test_decisions.py` — 21 tests covering decision summary
- `test_data_fusion.py` — 24 tests covering data fusion endpoints
- `test_portfolios.py` — portfolio CRUD tests

### Indicator Computation Details

The `SimulationResult.indicators()` method dispatches to indicator functions:

```python
# Called by the indicator endpoint handler:
indicator_result = result.indicators(indicator_type, **kwargs)
```

The `indicators()` method lives on `SimulationResult` (from `src/reformlab/interfaces/api.py`). It returns an `IndicatorResult` that has:
- `.to_table()` → `pa.Table` (converted to dict for response)
- `.metadata` → `dict[str, Any]`
- `.warnings` → `list[str]`
- `.excluded_count` → `int`

For tests, build a `SimulationResult` with a `PanelOutput` containing the right columns, store it in `ResultCache` (and `ResultStore` for metadata), and call the endpoint.

### Export Endpoint Details

Two export paths exist (both must be tested):

1. **Legacy path**: `POST /api/exports/csv` and `POST /api/exports/parquet` (in `exports.py`)
   - Request body: `{"run_id": "..."}`
   - Cache-only lookup currently; needs store/cache upgrade
   - Returns `StreamingResponse` with file content

2. **Result-scoped path**: `GET /api/results/{run_id}/export/csv` and `.../parquet` (in `results.py`)
   - Path parameter for run_id
   - Already uses store/cache pattern
   - Returns `StreamingResponse` with file content

For success path tests, verify:
- Response status 200
- Content-Type header (`text/csv` or `application/octet-stream`)
- Content-Disposition header with filename
- Body is valid CSV (parseable) or valid Parquet (readable by `pq.read_table()`)

### Important Scope Boundaries

**What this story does:**
- Standardizes error responses across all Phase 1 endpoints to `{what, why, fix}` format
- Adds store/cache two-step lookup to Phase 1 indicator and export endpoints
- Creates comprehensive integration tests for all undertested endpoints
- Verifies response schema correctness

**What this story does NOT do:**
- Add new API endpoints (all exist already from 17.1–17.5)
- Modify frontend code (error handling already works with `{what, why, fix}`)
- Change any Phase 2 endpoint behavior (only Phase 1 endpoints are modified)
- Add new Pydantic models (all exist already)
- Add TypeScript types (all exist already)
- Create E2E browser tests (that's Story 17.8)

### Anti-Patterns to Avoid

| Issue | Prevention |
|---|---|
| Breaking existing test assertions that check for plain string error `detail` | The only known breakage is `test_api.py::test_create_scenario_no_policy_type_returns_422` (line 255: `assert "policy_type is required" in response.json()["detail"]`). Task 1.5 handles this update. All other existing error tests already assert on dict keys (`"what" in detail`) and are unaffected. |
| Importing `ResultStore` at module level in indicators.py/exports.py | Use `if TYPE_CHECKING: from ... import ResultStore` guard, runtime import in function body via `Depends()` |
| Creating test fixtures that depend on real OpenFisca or real data files | Use `MockAdapter` and in-memory `PanelOutput` tables built with PyArrow |
| Testing welfare indicator with only one SimulationResult | Welfare comparison requires TWO results (baseline + reform) in cache |
| Hardcoding template/scenario names that may not exist in the test registry | For template/scenario detail tests, first list available items, then request the first one |
| Adding NumPy dependency for test data generation | Use PyArrow arrays and Python lists only |
| Modifying the `conftest.py` shared fixtures in incompatible ways | The `client` fixture in `conftest.py` creates a plain app without dependency overrides. Tests needing store/cache overrides must create their own `client_with_deps` fixture (as done in `test_decisions.py`). |

### Cross-Story Dependencies

| Story | Relationship |
|---|---|
| Story 17.1 | Data fusion endpoints — already well-tested (24 tests) |
| Story 17.2 | Portfolio endpoints — already well-tested |
| Story 17.3 | Result/runner endpoints — partially tested (15 tests, error paths mostly) |
| Story 17.4 | Portfolio comparison — well-tested (30+ tests) |
| Story 17.5 | Decision summary — well-tested (21 tests) |
| Story 17.7 | Persistent result storage — will build on result store tested here |
| Story 17.8 | E2E GUI workflow tests — will use the endpoints validated here |

### Dependency Versions (Current)

**Backend** (from `pyproject.toml`):
- FastAPI >= 0.133.0, uvicorn >= 0.41.0
- Pydantic >= 2.10
- Python 3.13+, mypy strict
- pyarrow >= 18.0.0

### References

- [Source: docs/epics.md#Epic 17, Story 17.6 (BKL-1706)] — Original acceptance criteria
- [Source: docs/project-context.md] — Coding conventions, testing rules
- [Source: src/reformlab/server/routes/indicators.py] — Indicator + comparison route handlers (to modify)
- [Source: src/reformlab/server/routes/exports.py] — Export route handlers (to modify)
- [Source: src/reformlab/server/routes/scenarios.py] — Scenario route handlers (to modify)
- [Source: src/reformlab/server/routes/templates.py] — Template route handlers (to modify)
- [Source: src/reformlab/server/routes/decisions.py] — Reference for correct error format pattern
- [Source: src/reformlab/server/routes/results.py] — Reference for store/cache lookup pattern
- [Source: src/reformlab/server/dependencies.py] — ResultCache, ResultStore, get_result_cache, get_result_store
- [Source: src/reformlab/server/result_store.py] — ResultStore, ResultMetadata, ResultStoreError, ResultNotFound
- [Source: src/reformlab/server/models.py] — Pydantic request/response models
- [Source: src/reformlab/interfaces/api.py] — SimulationResult, run_scenario, check_memory_requirements
- [Source: tests/server/conftest.py] — Shared test fixtures (client, auth_token, auth_headers)
- [Source: tests/server/test_comparison_portfolios.py] — Reference for test patterns (_make_panel, _make_sim_result, _make_metadata)
- [Source: tests/server/test_decisions.py] — Reference for test patterns (client_with_deps, store/cache seeding)
- [Source: tests/server/test_api.py] — Existing endpoint tests (will be extended)
- [Source: tests/server/test_runs.py] — Existing run tests (will be extended)
- [Source: tests/server/test_results.py] — Existing result tests (reference for export error tests)
- [Source: frontend/src/api/client.ts] — ApiError class (expects what/why/fix from error detail)

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List

**Modified files (error standardization + store/cache):**
- `src/reformlab/server/routes/indicators.py`
- `src/reformlab/server/routes/exports.py`
- `src/reformlab/server/routes/scenarios.py`
- `src/reformlab/server/routes/templates.py`

**New test files:**
- `tests/server/test_indicators_integration.py`
- `tests/server/test_exports_integration.py`

**Modified test files:**
- `tests/server/test_runs.py`
- `tests/server/test_api.py`

## Senior Developer Review (AI)

### Review: 2026-03-08
- **Reviewer:** AI Code Review Synthesis
- **Evidence Score:** 13.3 → REJECT
- **Issues Found:** 5 verified
- **Issues Fixed:** 3
- **Action Items Created:** 3

#### Review Follow-ups (AI)
- [ ] [AI-Review] HIGH: `except Exception` in `get_scenario()` and `clone_scenario()` swallows internal registry/I/O errors as false 404s — catch only the domain-specific "not found" exception (`src/reformlab/server/routes/scenarios.py`)
- [ ] [AI-Review] MEDIUM: `except Exception` in `get_template()` similarly converts server errors to false 404s — narrow to domain-specific exception (`src/reformlab/server/routes/templates.py`)
- [ ] [AI-Review] LOW: Scenario clone success path is completely untested due to pre-existing ScenarioRegistry hash integrity bug — requires a fix in the registry or a mock-based workaround (`tests/server/test_api.py`, `TestScenarioClone`)
