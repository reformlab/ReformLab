# Story 20.7: Extend backend APIs for population explorer and execution-contract validation

Status: ready-for-dev
**Epic**: EPIC-20 (Phase 3 Canonical Scenario Model)
**Story Type**: Backend API Implementation
**Points**: 5
**Dependencies**: Story 20.1 (canonical scenario model)

---

## Story

As a policy analyst using the ReformLab workspace,
I want backend APIs that expose population explorer functionality (preview, profile, crosstab, upload) and an extensible validation/preflight contract for execution,
so that the Population Library and Engine stages can operate on real data instead of mock data and the validation gate can perform runtime/memory checks before execution.

---

## Acceptance Criteria

### AC-1: Population API Endpoints Exist and Match Frontend Contracts

**Given** the API surface is inspected,
**When** a caller requests population data,
**Then** all endpoints exist and return typed responses matching the frontend model contracts:
- `GET /api/populations` — list all populations (already exists, needs origin/tag enhancement)
- `GET /api/populations/{id}/preview` — paginated row preview with sort/filter
- `GET /api/populations/{id}/profile` — per-column statistics (numeric/categorical/boolean)
- `GET /api/populations/{id}/crosstab` — cross-tabulation of two columns
- `POST /api/populations/upload` — CSV/Parquet file upload with validation feedback

### AC-2: Validation/Preflight Endpoint Returns Pass/Fail with Check-Level Detail

**Given** the Engine stage calls the validation endpoint,
**When** the endpoint processes a validation request,
**Then** it returns:
- `passed: boolean` — overall pass/fail
- `checks: ValidationCheckResult[]` — individual check results with `id`, `label`, `passed`, `severity`, `message`
- `warnings: string[]` — non-blocking warnings

The endpoint must use an extensible check registry pattern so EPIC-21 Story 21.5 can add trust-status rules without replacing the validation infrastructure.

### AC-3: All New Endpoints Return Typed Responses Matching Frontend Model Contracts

**Given** any new endpoint is called,
**When** the response is deserialized in the frontend,
**Then** the response matches the TypeScript interfaces defined in `frontend/src/api/types.ts`:
- `PopulationPreviewResponse` — preview rows with column metadata
- `PopulationProfileResponse` — column profiles (numeric/categorical/boolean)
- `PopulationCrosstabResponse` — cross-tabulated data
- `PopulationUploadResponse` — upload validation feedback
- `ValidationResponse` — validation check results
- `PopulationLibraryItem` — extends `PopulationItem` with `origin`, `column_count`, `created_date`

---

## Tasks / Subtasks

### 20.7.1: Extend `GET /api/populations` to Return PopulationLibraryItem with Origin Tags (AC: #1)

**Subtasks**:
- [ ] Add `origin: Literal["built-in", "generated", "uploaded"]` field to `PopulationLibraryItem` model in `src/reformlab/server/models.py`
- [ ] Add `column_count: int` field to `PopulationLibraryItem` model
- [ ] Add `created_date: str | None` field to `PopulationLibraryItem` model (ISO 8601 UTC)
- [ ] Extend `_scan_populations()` in `populations.py` to detect origin:
  - Built-in: files in `data/populations/` at server startup
  - Generated: populations created via data fusion (check for metadata file)
  - Uploaded: populations in `~/.reformlab/uploaded-populations/` directory
- [ ] Update `list_populations()` response to return `PopulationLibraryItem[]` instead of `PopulationItem[]`
- [ ] Add filesystem scan for uploaded populations directory (create if not exists)
- [ ] Add tests for origin detection and library item metadata

**Dev Notes**:
- Origin detection: check for `manifest.json` alongside data file for generated populations
- Uploaded populations directory: `~/.reformlab/uploaded-populations/` (create on init)
- Use `pathlib.Path` for filesystem operations; handle missing directories gracefully
- For built-in populations: set `created_date = None`, `origin = "built-in"`
- For generated populations: read `created_date` from manifest metadata
- For uploaded populations: set `created_date` from file mtime (`datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()`)

### 20.7.2: Implement `GET /api/populations/{id}/preview` Endpoint (AC: #1, #3)

**Subtasks**:
- [ ] Add `PopulationPreviewResponse` model to `src/reformlab/server/models.py`:
  ```python
  class ColumnInfo(BaseModel):
      name: str
      type: str  # "integer" | "float" | "string" | "boolean"
      description: str

  class PopulationPreviewResponse(BaseModel):
      id: str
      name: str
      rows: list[dict[str, Any]]  # max 100 rows
      columns: list[ColumnInfo]
      total_rows: int
  ```
- [ ] Add `PopulationPreviewRequest` query parameters model:
  ```python
  class PopulationPreviewRequest(BaseModel):
      offset: int = 0
      limit: int = 10
      sort_by: str | None = None
      order: Literal["asc", "desc"] = "asc"
  ```
- [ ] Implement `preview_population(id: str, params: PopulationPreviewRequest)` endpoint
- [ ] Use PyArrow to load population file (auto-detect CSV vs Parquet via extension)
- [ ] Apply pagination and sorting using PyArrow operations:
  - `table.slice(offset, limit)` for pagination
  - `table.sort_by(sort_by, order=[(sort_by, "ascending" if order=="asc" else "descending")])`
- [ ] Extract column schema to build `ColumnInfo` list (map PyArrow types to strings)
- [ ] Return 404 with error response if population not found
- [ ] Add tests for preview endpoint with CSV and Parquet files

**Dev Notes**:
- File location pattern: first check `data/populations/{id}.csv` or `.parquet`, then `~/.reformlab/uploaded-populations/{id}.csv` or `.parquet`
- PyArrow type mapping: `pa.int64() → "integer"`, `pa.float64() → "float"`, `pa.string() → "string"`, `pa.bool_() → "boolean"`
- Maximum rows: 100 (enforced in endpoint even if client requests more)
- Sorting: only valid for numeric and string columns; return error for unsupported types

### 20.7.3: Implement `GET /api/populations/{id}/profile` Endpoint (AC: #1, #3)

**Subtasks**:
- [ ] Add column profile models to `src/reformlab/server/models.py`:
  ```python
  class ColumnProfileNumeric(BaseModel):
      type: Literal["numeric"]
      count: int
      nulls: int
      null_pct: float
      min: float
      max: float
      mean: float
      median: float
      std: float
      percentiles: dict[str, float]  # p1, p5, p25, p50, p75, p95, p99

  class ColumnProfileCategorical(BaseModel):
      type: Literal["categorical"]
      count: int
      nulls: int
      null_pct: float
      cardinality: int
      value_counts: list[dict[str, Any]]  # [{"value": "x", "count": 123}, ...]

  class ColumnProfileBoolean(BaseModel):
      type: Literal["boolean"]
      count: int
      nulls: int
      null_pct: float
      true_count: int
      false_count: int

  ColumnProfile = ColumnProfileNumeric | ColumnProfileCategorical | ColumnProfileBoolean

  class ColumnProfileEntry(BaseModel):
      name: str
      profile: ColumnProfile

  class PopulationProfileResponse(BaseModel):
      id: str
      columns: list[ColumnProfileEntry]
  ```
- [ ] Implement `profile_population(id: str)` endpoint
- [ ] Load population file via PyArrow
- [ ] Compute per-column statistics:
  - Numeric: compute all statistics using PyArrow compute functions
  - Categorical: compute value counts (top 50 values by frequency)
  - Boolean: compute true/false/null counts
- [ ] Return 404 if population not found
- [ ] Add tests for profile endpoint with various column types

**Dev Notes**:
- Use PyArrow compute functions: `pc.mean()`, `pc.stddev()`, `pc.min_max()`, `pc.quantile()`, `pc.value_counts()`
- For categorical columns with high cardinality (>1000), limit value_counts to top 50
- Median: use `pc.quantile(table, q=0.5)` for approximation
- Percentiles: compute p1, p5, p25, p50, p75, p95, p99 using `pc.quantiles()`
- Null percentage: `(null_count / total_rows) * 100`

### 20.7.4: Implement `GET /api/populations/{id}/crosstab` Endpoint (AC: #1, #3)

**Subtasks**:
- [ ] Add `PopulationCrosstabResponse` model to `src/reformlab/server/models.py`:
  ```python
  class PopulationCrosstabResponse(BaseModel):
      col_a: str
      col_b: str
      data: list[dict[str, Any]]  # flattened crosstab with col_a, col_b, count columns
  ```
- [ ] Implement `crosstab_population(id: str, col_a: str, col_b: str)` endpoint with query parameters
- [ ] Validate both columns exist in the population (return 400 with error message if not)
- [ ] Load population file via PyArrow
- [ ] Compute cross-tabulation:
  - Group by col_a and col_b
  - Count occurrences of each combination
  - Return as list of dictionaries with col_a, col_b, count keys
- [ ] Limit to top 1000 combinations by count (warn if truncated)
- [ ] Return 404 if population not found
- [ ] Add tests for crosstab endpoint

**Dev Notes**:
- Use PyArrow `table.group_by([col_a, col_b]).aggregate([("count", "count")])`
- Sort by count descending before limiting
- Return format: `[{col_a: "value1", col_b: "value2", count: 123}, ...]`
- Query parameter format: `?col_a=column_name&col_b=other_column`
- Column validation: check if column names exist in `table.column_names`

### 20.7.5: Implement `POST /api/populations/upload` Endpoint (AC: #1, #3)

**Subtasks**:
- [ ] Add `PopulationUploadResponse` model to `src/reformlab/server/models.py`:
  ```python
  class PopulationUploadResponse(BaseModel):
      id: str
      name: str
      row_count: int
      column_count: int
      matched_columns: list[str]
      unrecognized_columns: list[str]
      missing_required: list[str]
      valid: bool
  ```
- [ ] Implement `upload_population(file: UploadFile)` endpoint
- [ ] Validate uploaded file is CSV or Parquet (check extension and content type)
- [ ] Save file to `~/.reformlab/uploaded-populations/{original_filename}` with UUID prefix
- [ ] Load file via PyArrow to validate structure
- [ ] Perform column validation:
  - Match against known ReformLab columns (household_id, person_id, income, etc.)
  - Report unrecognized columns
  - Report missing required columns (household_id is required)
- [ ] Generate unique population ID: `uploaded-{uuid}`
- [ ] Return validation response with `valid=True` if basic structure is valid
- [ ] Add tests for upload endpoint with valid and invalid files

**Dev Notes**:
- Required columns: `household_id` (minimum for execution)
- Known columns (from `reformlab.population` schemas): check against expected names
- File size limit: 100 MB (enforced via FastAPI `UploadFile.spool_max_size`)
- Virus/security: basic validation only; assume trusted environment for Story 20.7
- Uploaded directory: create `~/.reformlab/uploaded-populations/` if not exists
- File naming: `{uuid}-{original_filename}` to avoid collisions
- Origin tag: uploaded populations get `origin="uploaded"`

### 20.7.6: Implement `POST /api/validation/preflight` Endpoint with Extensible Check Registry (AC: #2)

**Subtasks**:
- [ ] Add validation models to `src/reformlab/server/models.py`:
  ```python
  class PreflightRequest(BaseModel):
      scenario: dict[str, Any]  # WorkspaceScenario serialized as dict
      population_id: str | None = None
      template_name: str | None = None

  class ValidationCheckResult(BaseModel):
      id: str
      label: str
      passed: bool
      severity: Literal["error", "warning"]
      message: str

  class PreflightResponse(BaseModel):
      passed: bool
      checks: list[ValidationCheckResult]
      warnings: list[str]
  ```
- [ ] Create `src/reformlab/server/validation.py` module with check registry:
  ```python
  from typing import Protocol

  class ValidationCheck(Protocol):
      id: str
      label: str
      severity: Literal["error", "warning"]
      def __call__(self, request: PreflightRequest) -> ValidationCheckResult: ...

  _VALIDATION_CHECKS: list[ValidationCheck] = []

  def register_check(check: ValidationCheck) -> None:
      _VALIDATION_CHECKS.append(check)

  def run_checks(request: PreflightRequest) -> PreflightResponse:
      results = [check(request) for check in _VALIDATION_CHECKS]
      passed = all(r.passed for r in results if r.severity == "error")
      warnings = [r.message for r in results if r.severity == "warning" and not r.passed]
      return PreflightResponse(passed=passed, checks=results, warnings=warnings)
  ```
- [ ] Implement built-in validation checks:
  - `portfolio-selected`: error if `scenario["portfolioName"]` is null/empty
  - `population-selected`: error if `scenario["populationIds"]` is empty
  - `time-horizon-valid`: error if `startYear >= endYear` or `endYear - startYear > 50`
  - `memory-preflight`: calls existing `check_memory_requirements()` (reuse from `/api/runs/memory-check`)
- [ ] Implement `preflight_validation(request: PreflightRequest)` endpoint
- [ ] Register built-in checks at module import time
- [ ] Add tests for preflight endpoint and check registry

**Dev Notes**:
- Check registry design: module-level list + `register_check()` function allows EPIC-21 Story 21.5 to append checks without modifying core code
- Memory check integration: reuse `check_memory_requirements()` from `reformlab.interfaces.api`
- Scenario serialization: frontend sends `WorkspaceScenario` as dict; backend validates structure
- Severity handling: "warning" checks don't block execution, "error" checks do
- Extensibility: import-time registration pattern means new checks are registered on server startup

### 20.7.7: Wire New Endpoints into FastAPI App (AC: #1)

**Subtasks**:
- [ ] Update `src/reformlab/server/routes/populations.py` to export the extended router
- [ ] Create new validation router in `src/reformlab/server/routes/validation.py`
- [ ] Update `src/reformlab/server/app.py` to import and register routers:
  ```python
  from reformlab.server.routes.validation import router as validation_router
  app.include_router(validation_router, prefix="/api/validation", tags=["validation"])
  ```
- [ ] Ensure populations router prefix is `/api/populations` (already registered)
- [ ] Add OpenAPI tags and descriptions for documentation
- [ ] Verify all endpoints appear in `/docs` (FastAPI auto-generated docs)

### 20.7.8: Add Comprehensive Tests for All Endpoints (AC: #1, #2, #3)

**Subtasks**:
- [ ] Create `tests/server/test_populations_api.py` with test fixtures:
  - Sample CSV population file in `tests/fixtures/populations/test-population.csv`
  - Sample Parquet population file in `tests/fixtures/populations/test-population.parquet`
- [ ] Test `GET /api/populations` returns PopulationLibraryItem list with origin tags
- [ ] Test `GET /api/populations/{id}/preview` with pagination and sorting
- [ ] Test `GET /api/populations/{id}/preview` returns 404 for missing population
- [ ] Test `GET /api/populations/{id}/profile` for numeric, categorical, boolean columns
- [ ] Test `GET /api/populations/{id}/crosstab` with valid and invalid column names
- [ ] Test `POST /api/populations/upload` with valid CSV/Parquet files
- [ ] Test `POST /api/populations/upload` rejects non-CSV/Parquet files
- [ ] Test `POST /api/validation/preflight` with valid and invalid scenarios
- [ ] Test `POST /api/validation/preflight` includes all built-in check results
- [ ] Test check registry extensibility (register custom check and verify it runs)

**Dev Notes**:
- Use `pytest` and FastAPI `TestClient` for all API tests
- Mock PyArrow file operations for unit tests where appropriate
- Test fixtures should be minimal but realistic (100 rows, 5-10 columns)
- Test error responses follow the `ErrorResponse` model (what/why/fix pattern)

---

## Dev Notes

### Architecture Patterns and Constraints

- **PyArrow-First**: All population data operations use PyArrow Tables — no pandas conversions except at display/export boundaries
- **Error Response Pattern**: All errors follow `{"what": str, "why": str, "fix": str}` format (see `ErrorResponse` model in `models.py`)
- **File Storage Patterns**:
  - Built-in: `data/populations/{id}.{csv|parquet}`
  - Uploaded: `~/.reformlab/uploaded-populations/{uuid}-{original_filename}`
  - Use `pathlib.Path` for all filesystem operations
- **Type Safety**: Backend Pydantic models must match frontend TypeScript interfaces exactly
- **Validation Registry**: Module-level registration pattern allows extensibility without core code changes

### Source Tree Components

| File | Modification |
|------|--------------|
| `src/reformlab/server/models.py` | Add PopulationPreviewResponse, PopulationProfileResponse, PopulationCrosstabResponse, PopulationUploadResponse, PopulationLibraryItem, PreflightRequest, PreflightResponse, ValidationCheckResult |
| `src/reformlab/server/routes/populations.py` | Extend list_populations, add preview/profile/crosstab/upload endpoints |
| `src/reformlab/server/routes/validation.py` | NEW: preflight endpoint with check registry |
| `src/reformlab/server/validation.py` | NEW: check registry and built-in checks |
| `src/reformlab/server/app.py` | Register validation router |
| `tests/server/test_populations_api.py` | NEW: comprehensive API tests |
| `tests/fixtures/populations/` | NEW: test data files |

### Testing Standards Summary

- **Backend Tests**: Use pytest with FastAPI TestClient
- **Test Structure**: Mirror source structure in `tests/` directory
- **Fixtures**: Use `conftest.py` for shared test data and utilities
- **Coverage**: All new endpoints must have unit tests with >80% coverage
- **Error Cases**: Test both success and failure paths (404, 400, 500 scenarios)

### Project Structure Notes

- Alignment with unified project structure: Server code lives in `src/reformlab/server/`
- Routes are organized by domain: `populations.py`, `validation.py`, `runs.py`, etc.
- Pydantic models for all HTTP serialization live in `models.py`
- Domain logic (population loading) stays in `src/reformlab/population/` — server routes are thin wrappers

### Detected Conflicts or Variances

- **Frontend expects**: `PopulationLibraryItem` with `origin` field — backend currently returns `PopulationItem` without it (Task 20.7.1 resolves this)
- **Frontend mock data**: Story 20.4 uses mock data for preview/profile — this story replaces mocks with real endpoints
- **Memory check duplication**: `/api/runs/memory-check` exists; preflight endpoint should reuse the same underlying function, not duplicate code

---

## References

- **Epic 20**: `_bmad-output/planning-artifacts/epics.md` (lines 2135-2150)
- **Story 20.4**: `_bmad-output/implementation-artifacts/20-4-build-population-library-and-data-explorer-stage.md` — Population Library UI that consumes these endpoints
- **Story 20.5**: `_bmad-output/implementation-artifacts/20-5-build-engine-stage-with-scenario-save-clone-and-cross-stage-validation-gate.md` — Validation gate that calls preflight endpoint
- **Frontend API types**: `frontend/src/api/types.ts` — TypeScript interfaces for PopulationPreviewResponse, PopulationProfileResponse, PopulationCrosstabResponse, PopulationUploadResponse
- **Frontend API client**: `frontend/src/api/populations.ts` — Functions that call these endpoints
- **Existing populations route**: `src/reformlab/server/routes/populations.py` — Current list endpoint implementation
- **Existing models**: `src/reformlab/server/models.py` — Pydantic models for request/response
- **Memory check pattern**: `src/reformlab/server/routes/runs.py` line 271 — `/api/runs/memory-check` endpoint to reuse
- **Architecture**: `_bmad-output/planning-artifacts/architecture.md` — API layer design, error response pattern

---

## Dev Agent Record

**Created**: 2026-03-27
**Author**: Claude (Opus 4.6) via create-story workflow
**Context Enhancement**: Ultimate context engine analysis performed
**Ready for Dev**: Yes — all tasks defined with acceptance criteria, dev notes, and type specifications

**Dependencies Status**:
- Story 20.1 (canonical scenario model): **DONE** — WorkspaceScenario type available for preflight validation

**Implementation Notes**:
- Story 20.4 frontend uses mock data — these endpoints will replace mocks with real data
- Story 20.5 validation gate calls `/api/validation/preflight` — this story implements that endpoint
- Memory check reuses existing `check_memory_requirements()` function — no duplication needed

**EPIC-21 Coordination**:
- Validation check registry design enables Story 21.5 to add trust-status rules
- Population origin tags (`built-in`/`generated`/`uploaded`) prepare for Story 21.2 evidence asset descriptor

---

## File List

**Backend**:
- `src/reformlab/server/models.py` — extend with new response models
- `src/reformlab/server/routes/populations.py` — extend with preview/profile/crosstab/upload
- `src/reformlab/server/routes/validation.py` — NEW: preflight endpoint
- `src/reformlab/server/validation.py` — NEW: check registry
- `src/reformlab/server/app.py` — register validation router
- `tests/server/test_populations_api.py` — NEW: API tests

**Frontend** (reference only, no changes in this story):
- `frontend/src/api/types.ts` — TypeScript interfaces (already defined)
- `frontend/src/api/populations.ts` — API client functions (already defined)

**Fixtures**:
- `tests/fixtures/populations/test-population.csv` — NEW: test data
- `tests/fixtures/populations/test-population.parquet` — NEW: test data

---

## Change Log

- 2026-03-27: Story created with comprehensive task breakdown and acceptance criteria
