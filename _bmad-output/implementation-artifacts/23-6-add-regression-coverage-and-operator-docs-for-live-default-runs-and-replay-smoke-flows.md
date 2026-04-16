# Story 23.6: Add regression coverage and operator docs for live default runs and replay smoke flows

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an operator or developer,
I want comprehensive regression coverage and concise operator guidance for live-default execution and replay paths,
so that I can confidently verify the runtime change works end-to-end with all population types, and I can diagnose failed runs using documented runtime, population, and mapping diagnostics.

**Epic:** Epic 23 — Live OpenFisca Runtime and Executable Population Alignment
**Priority:** P1
**Estimate:** 5 SP
**Dependencies:** Story 23.2 (population resolver), Story 23.3 (normalization), Story 23.4 (default live execution), Story 23.5 (preflight and provenance)

## Acceptance Criteria

1. Given the automated regression suite, when it runs, then it covers live-default execution with bundled, uploaded, and generated populations plus an explicit replay smoke path.
2. Given existing results and indicator workflows, when exercised by regression tests, then they pass on normalized live outputs.
3. Given operator-facing documentation for runtime support, when reviewed, then it describes live as the default and replay as explicit/manual.
4. Given this epic is complete, when a developer or operator investigates a failed run, then the docs and tests point to the relevant runtime, population, and mapping diagnostics.

## Tasks / Subtasks

### Task 1: Add end-to-end regression tests for bundled populations (AC: 1)

- [ ] **Extend `tests/server/test_regression.py`** (new file for Epic 23 regression suite)
  - [ ] `TestBundledPopulationLiveExecution`:
    - `test_bundled_population_live_run_succeeds()` — POST /api/runs with bundled population_id and runtime_mode="live" returns 200 with valid result
    - `test_bundled_population_manifest_records_provenance()` — manifest.json contains runtime_mode="live", population_id matches bundled ID, population_source="bundled"
    - `test_bundled_population_metadata_matches_manifest()` — ResultMetadata.runtime_mode and population_source match manifest values
  - [ ] Use existing bundled population ID (e.g., "fr-synthetic-2024") for test realism
  - [ ] Verify no preflight warnings for valid bundled population in live mode

### Task 2: Add regression tests for uploaded populations (AC: 1)

- [ ] **Extend `tests/server/test_regression.py`** (AC: 1)
  - [ ] `TestUploadedPopulationLiveExecution`:
    - `test_uploaded_population_live_run_succeeds()` — Create uploaded CSV population in tmp_path, POST /api/runs with runtime_mode="live", verify 200 response
    - `test_uploaded_population_manifest_records_source()` — manifest.json contains population_source="uploaded" and correct population_id
    - `test_uploaded_population_schema_validation_passes()` — Uploaded population with valid schema (household_id, income, disposable_income, carbon_tax) passes preflight and executes
    - `test_uploaded_population_missing_columns_fails_preflight()` — Uploaded population missing required columns fails preflight with actionable error

### Task 3: Add regression tests for generated populations (AC: 1)

- [ ] **Extend `tests/server/test_regression.py`** (AC: 1)
  - [ ] `TestGeneratedPopulationLiveExecution`:
    - `test_generated_population_live_run_succeeds()` — Create generated synthetic population via data fusion or generator, POST /api/runs, verify execution
    - `test_generated_population_manifest_records_source()` — manifest.json contains population_source="generated" and references generation metadata
    - `test_generated_population_with_seed_reproducibility()` — Same seed produces identical results across multiple runs (determinism invariant)

### Task 4: Add explicit replay smoke tests (AC: 1)

- [ ] **Extend `tests/server/test_regression.py`** (AC: 1)
  - [ ] `TestReplaySmokeExecution`:
    - `test_explicit_replay_mode_executes()` — POST /api/runs with runtime_mode="replay" and precomputed data present returns 200 with replay runtime_mode in metadata
    - `test_replay_mode_without_data_fails()` — POST with runtime_mode="replay" and no precomputed data returns 422 with actionable error
    - `test_replay_manifest_records_mode_correctly()` — manifest.json contains runtime_mode="replay" (not live)
    - `test_replay_and_live_mode_produce_different_manifests()` — Same scenario run with live vs replay produces manifest.runtime_mode values matching requested modes

### Task 5: Add regression tests for indicator workflows on live outputs (AC: 2)

- [ ] **Extend `tests/server/test_regression.py`** (AC: 2)
  - [ ] `TestIndicatorWorkflowsOnLiveOutputs`:
    - `test_distributional_indicators_work_with_live_output()` — POST /api/indicators/compute on live run result returns valid distributional indicators
    - `test_fiscal_indicators_work_with_live_output()` — Fiscal indicators compute correctly on normalized live output (carbon_tax, income fields present)
    - `test_geographic_indicators_work_with_live_output()` — Geographic indicators work when live output has region metadata
    - `test_welfare_indicators_require_baseline_and_reform()` — Welfare indicators work with both live baseline and live reform outputs
    - `test_indicator_comparison_across_runs_preserves_semantics()` — Comparing indicators from live vs live runs produces meaningful comparison (no runtime-specific code paths)

### Task 6: Add regression tests for comparison workflows on live outputs (AC: 2)

- [ ] **Extend `tests/server/test_regression.py`** (AC: 2)
  - [ ] `TestComparisonWorkflowsOnLiveOutputs`:
    - `test_compare_two_live_runs()` — POST /api/results/compare with two live run IDs returns valid comparison data
    - `test_compare_live_vs_replay()` — Comparing live run result with replay run result produces valid comparison (schema invariance is normalized)
    - `test_comparison_preserves_runtime_provenance()` — Comparison result includes runtime_mode and population_source from both runs for transparency

### Task 7: Add regression tests for export workflows on live outputs (AC: 2)

- [ ] **Extend `tests/server/test_regression.py`** (AC: 2)
  - [ ] `TestExportWorkflowsOnLiveOutputs`:
    - `test_export_parquet_preserves_live_provenance()` — POST /api/exports/parquet on live run produces Parquet with manifest metadata in schema
    - `test_export_csv_preserves_live_provenance()` — CSV export includes metadata or references manifest file
    - `test_replication_package_includes_runtime_info()` — Replication package export includes manifest.json with runtime_mode and population_source

### Task 8: Create operator-facing runtime diagnostics documentation (AC: 3, AC: 4)

- [ ] **Create `docs/operator/runtime-diagnostics.md`** (new documentation file)
  - [ ] **Runtime Mode Diagnostics** section:
    - Document that live OpenFisca is the default web runtime (no user-facing selector needed)
    - Document that replay mode is explicit/manual-only (opt-in via API, not fallback)
    - Describe how to verify which runtime was used (manifest.runtime_mode, ResultMetadata.runtime_mode)
    - Explain runtime mode preflight errors and their fixes
  - [ ] **Population Resolution Diagnostics** section:
    - Document bundled vs uploaded vs generated population sources and their executability
    - Describe how to check if a population_id resolves to an executable dataset (use preflight endpoint or inspect manifest)
    - Document population schema requirements (minimum columns: household_id, income, disposable_income, carbon_tax)
    - Explain population resolution errors and how to fix them
  - [ ] **Mapping and Normalization Diagnostics** section:
    - Document the normalization layer (result_normalizer.py) and how to inspect mapping configuration
    - Describe common mapping errors (missing columns, incompatible schemas) and how to debug them
    - Explain _DEFAULT_OUTPUT_MAPPING and how to provide custom MappingConfig if defaults don't match adapter output
    - Document NormalizationError messages and their resolution paths
  - [ ] **Failed Run Investigation Checklist** section:
    - Step-by-step checklist for investigating failed runs: check manifest, check metadata, check logs, validate population, verify adapter
    - Reference specific log locations and API endpoints for each diagnostic step
    - Include examples of common failure modes and their resolution

### Task 9: Add regression test for operator documentation smoke (AC: 4)

- [ ] **Extend `tests/server/test_regression.py`** (AC: 4)
  - [ ] `TestOperatorDocumentationSmoke`:
    - `test_operator_docs_exist()` — Verify docs/operator/runtime-diagnostics.md exists and is readable
    - `test_docs_describe_live_as_default()` — Documentation states live is default, replay is explicit
    - `test_docs_include_population_diagnostics()` — Documentation includes population resolution and schema troubleshooting
    - `test_docs_include_mapping_diagnostics()` — Documentation covers normalization and mapping error resolution

### Task 10: Add integration test for full workflow regression (AC: 1, AC: 2)

- [ ] **Extend `tests/server/test_regression.py`** (AC: 1, AC: 2)
  - [ ] `TestFullWorkflowRegression`:
    - `test_end_to_end_workflow_with_bundled_population()` — Create scenario, select bundled population, run live, compute indicators, export, verify all steps succeed
    - `test_end_to_end_workflow_with_uploaded_population()` — Upload CSV, create scenario, run live, compare against baseline, verify complete workflow
    - `test_workflow_with_generated_population_and_comparisons()` — Generate population, run multiple portfolios, compare results, verify normalized outputs work throughout

## Dev Notes

### Architecture Patterns

**Story 23.6 Scope: Regression and Documentation, Not New Features**

This story does NOT add new functionality. It validates that existing Stories 23.1–23.5 work correctly together. The focus is:

1. **Regression Coverage**: End-to-end tests that verify the complete runtime change doesn't break existing workflows
2. **Operator Documentation**: Self-contained diagnostic guide for investigating failed runs
3. **Smoke Tests**: Minimal viable paths that prove live and replay modes work in isolation

**Existing Infrastructure to Reuse and Test**

1. **Test patterns from Stories 23.4 and 23.5**:
   - `TestClient` with `MockAdapter` injection via `monkeypatch` (see `tests/server/conftest.py`)
   - `tmp_store` fixture for isolated test directories (no pollution of ~/.reformlab)
   - `auth_headers` fixture for authenticated requests
   - Manifest assertions: read `manifest.json` from disk and assert field values
   - Metadata assertions: use `ResultStore.list_results()` or `ResultStore.get_metadata()`
   - Preflight tests: call `POST /api/validation/preflight` with `PreflightRequest`

2. **Population fixtures** from Story 23.5:
   - CSV population creation in `tmp_path` with required columns
   - `PopulationResolver` injection for testing uploaded/generated populations
   - Schema validation at preflight time (lightweight column check via PyArrow schema read)

3. **Result normalizer** (Story 23.3):
   - `normalize_computation_result()` maps OpenFisca outputs to project schema
   - `_DEFAULT_OUTPUT_MAPPING` provides French-to-English variable mapping
   - `_MINIMUM_REQUIRED_COLUMNS` validates indicator columns survive normalization
   - Tests must verify that normalized outputs contain expected columns for indicator/comparison workflows

4. **Runtime mode contract** (Story 23.1):
   - `runtime_mode` field on `RunRequest`, `PreflightRequest`, `RunMetadata`
   - Literal type: `Literal["live", "replay"]`
   - Manifest records `runtime_mode` for provenance
   - Tests should verify `manifest.runtime_mode` matches requested mode

**Key Design Decisions**

**Regression test organization by feature rather than by story**: Tests are grouped into test classes by feature area (bundled populations, uploaded populations, generated populations, replay smoke, indicators, comparisons, exports, documentation smoke). This mirrors the test organization in Stories 23.4 and 23.5.

**Generated population tests use data fusion or generator**: Tests for generated populations should create synthetic data using existing infrastructure (data fusion or population generator). Do NOT hardcode synthetic data in tests.

**Indicator tests verify schema compatibility, not business logic**: The regression tests verify that indicator endpoints accept live-normalized outputs and return valid results. They do NOT test indicator computation correctness (that's covered by `tests/indicators/` unit tests).

**Replay smoke tests use precomputed data from fixtures**: Create minimal precomputed CSV files in `tmp_path` for replay mode testing. Do NOT depend on production precomputed data.

**Documentation is operator-facing, not user-facing**: The runtime-diagnostics.md file is for operators and developers investigating failed runs. It should NOT duplicate user-facing help content. Focus on diagnostics, troubleshooting, and investigation workflows.

**Documentation references concrete paths and endpoints**: Each diagnostic section should reference specific file paths (e.g., `~/.reformlab/results/{run_id}/manifest.json`), log locations, and API endpoints (e.g., `GET /api/results/{run_id}/metadata`).

**Smoke test is minimal but complete**: Each smoke test should cover: request → execution → persistence → retrieval → verify. This proves the path works end-to-end without testing every edge case.

### Source Tree Components

**New files to create:**

| File Path | Purpose |
|-----------|---------|
| `tests/server/test_regression.py` | End-to-end regression tests for Epic 23 |
| `docs/operator/runtime-diagnostics.md` | Operator-facing runtime diagnostics and troubleshooting guide |

**Existing files referenced in tests:**

| File Path | Purpose |
|-----------|---------|
| `tests/server/conftest.py` | Test fixtures (tmp_store, auth_headers, client, MockAdapter) |
| `tests/server/test_live_default_runs.py` | Default live execution tests (Story 23.4) |
| `tests/server/test_preflight_runtime.py` | Runtime/population preflight tests (Story 23.5) |
| `tests/server/test_indicators_integration.py` | Indicator integration tests (reference for workflow regression) |
| `tests/server/test_results.py` | Results API tests (reference for retrieval and comparison) |
| `tests/server/test_exports_integration.py` | Export API tests (reference for Parquet/CSV export) |
| `src/reformlab/computation/result_normalizer.py` | Normalization layer (for mapping diagnostics) |
| `src/reformlab/server/population_resolver.py` | Population resolver (for population diagnostics) |
| `src/reformlab/server/validation.py` | Preflight validation (for runtime/population diagnostics) |
| `src/reformlab/governance/manifest.py` | Manifest schema (for provenance inspection) |
| `src/reformlab/server/result_store.py` | Result persistence (for metadata retrieval) |

### Testing Standards

- **Regression test organization**: Group tests by feature area with descriptive class names
  - `TestBundledPopulationLiveExecution` — bundled population live runs
  - `TestUploadedPopulationLiveExecution` — uploaded population live runs
  - `TestGeneratedPopulationLiveExecution` — generated population live runs
  - `TestReplaySmokeExecution` — replay mode smoke tests
  - `TestIndicatorWorkflowsOnLiveOutputs` — indicator workflows on live outputs
  - `TestComparisonWorkflowsOnLiveOutputs` — comparison workflows on live outputs
  - `TestExportWorkflowsOnLiveOutputs` — export workflows on live outputs
  - `TestOperatorDocumentationSmoke` — documentation existence and content verification
  - `TestFullWorkflowRegression` — end-to-end workflow tests

- **Test invariants for regression** (must be explicit):
  - For bundled population tests: manifest.runtime_mode == "live", population_source == "bundled", panel data has expected columns
  - For uploaded population tests: manifest.population_source == "uploaded", preflight validation ran before execution
  - For generated population tests: manifest.population_source == "generated", results are deterministic with same seed
  - For replay tests: manifest.runtime_mode == "replay", precomputed data was required for success
  - For indicator tests: indicator endpoints return 200 with valid JSON containing expected fields
  - For comparison tests: comparison endpoint returns 200 with comparison data referencing both run IDs
  - For export tests: export produces downloadable file with correct format and metadata

- **Documentation test invariants** (must be explicit):
  - Documentation file exists at expected path and is readable
  - Documentation contains sections for runtime diagnostics, population diagnostics, mapping diagnostics
  - Documentation states live is default and replay is explicit (not fallback)
  - Documentation includes checklist or step-by-step investigation guide

- **Full workflow tests**: Verify complete scenario lifecycle
  - Population selection → scenario configuration → preflight → run execution → indicator computation → comparison → export
  - Each step must succeed (non-2xx status codes)
  - Final output must be retrievable and have correct provenance fields

### Implementation Notes

**Regression Test Fixture Pattern**

```python
# test_regression.py — fixture setup

@pytest.fixture()
def client_with_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """TestClient with ResultStore and MockAdapter injected."""
    from reformlab.server.app import create_app
    from reformlab.server.dependencies import get_result_store

    tmp_store = ResultStore(base_dir=tmp_path)

    monkeypatch.setattr(deps, "_adapter", MockAdapter())
    monkeypatch.setattr(deps, "_result_store", tmp_store)

    app = create_app()
    app.dependency_overrides[get_result_store] = lambda: tmp_store
    return TestClient(app)

@pytest.fixture()
def auth_headers(client_with_store: TestClient) -> dict[str, str]:
    response = client_with_store.post(
        "/api/auth/login",
        json={"password": "test-password-123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}
```

**Bundled Population Test Pattern**

```python
def test_bundled_population_live_run_succeeds(
    self, client_with_store: TestClient, auth_headers: dict[str, str]
) -> None:
    """POST /api/runs with bundled population and runtime_mode='live' returns 200."""
    run_body = {
        "template_name": "carbon_tax",
        "policy": {"rate_schedule": {2025: 44.0}},
        "start_year": 2025,
        "end_year": 2025,
        "population_id": "fr-synthetic-2024",  # bundled population
        "runtime_mode": "live",
    }

    response = client_with_store.post(
        "/api/runs",
        headers=auth_headers,
        json=run_body,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["runtime_mode"] == "live"
    assert data["population_id"] == "fr-synthetic-2024"
```

**Uploaded Population Test Pattern**

```python
def test_uploaded_population_live_run_succeeds(
    self, tmp_path: Path, client_with_store: TestClient, auth_headers: dict[str, str]
) -> None:
    """Create uploaded CSV and run live execution."""
    from reformlab.server.population_resolver import PopulationResolver

    data_dir = tmp_path / "populations"
    uploaded_dir = tmp_path / "uploaded"
    data_dir.mkdir()
    uploaded_dir.mkdir()

    # Create valid CSV population with required columns
    (data_dir / "uploaded-pop.csv").write_text(
        "household_id,income,disposable_income,carbon_tax\n"
        "1,50000,45000,50\n"
    )

    run_body = {
        "template_name": "carbon_tax",
        "policy": {"rate_schedule": {2025: 44.0}},
        "start_year": 2025,
        "end_year": 2025,
        "population_id": "uploaded-pop",
        "runtime_mode": "live",
    }

    response = client_with_store.post(
        "/api/runs",
        headers=auth_headers,
        json=run_body,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["population_source"] == "uploaded"
```

**Replay Smoke Test Pattern**

```python
def test_explicit_replay_mode_executes(
    self, tmp_path: Path, client_with_store: TestClient, auth_headers: dict[str, str]
) -> None:
    """POST /api/runs with runtime_mode='replay' uses replay adapter."""
    # Create minimal precomputed data
    data_dir = tmp_path / "openfisca"
    data_dir.mkdir()
    (data_dir / "2025.csv").write_text(
        "household_id,income_tax,carbon_tax\n"
        "1,1000,50\n"
    )
    monkeypatch.setenv("REFORMLAB_OPENFISCA_DATA_DIR", str(data_dir))

    run_body = {
        "template_name": "carbon_tax",
        "policy": {"rate_schedule": {2025: 44.0}},
        "start_year": 2025,
        "end_year": 2025,
        "runtime_mode": "replay",
    }

    response = client_with_store.post(
        "/api/runs",
        headers=auth_headers,
        json=run_body,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["runtime_mode"] == "replay"
```

**Indicator Workflow Test Pattern**

```python
def test_distributional_indicators_work_with_live_output(
    self, client_with_store: TestClient, auth_headers: dict[str, str]
) -> None:
    """Distributional indicators compute correctly on normalized live output."""
    # First run a simulation to get a live result
    run_response = client_with_store.post(
        "/api/runs",
        headers=auth_headers,
        json={
            "template_name": "carbon_tax",
            "policy": {"rate_schedule": {2025: 44.0}},
            "start_year": 2025,
            "end_year": 2025,
            "runtime_mode": "live",
        },
    )
    assert run_response.status_code == 200
    run_id = run_response.json()["run_id"]

    # Then compute indicators on that result
    indicator_response = client_with_store.post(
        f"/api/indicators/compute",
        headers=auth_headers,
        json={
            "run_id": run_id,
            "indicator_type": "distributional",
        },
    )
    assert indicator_response.status_code == 200
    data = indicator_response.json()
    assert "result" in data
    assert "deciles" in data["result"]
```

**Documentation Structure (runtime-diagnostics.md)**

```markdown
# Runtime Diagnostics and Troubleshooting

## Overview

This guide helps operators and developers investigate failed runs and understand runtime mode behavior.

## Runtime Mode Diagnostics

### Live Mode (Default)

Live OpenFisca is the default runtime for web runs. When no `runtime_mode` is specified in a run request, the system automatically uses live execution.

**Verification:**
- Check `manifest.runtime_mode` field in the run's manifest.json
- Verify `ResultMetadata.runtime_mode` via GET /api/results/{run_id}/metadata
- Value should be `"live"` for default web runs

### Replay Mode (Explicit)

Replay mode is an explicit, manual opt-in path. It is NOT a fallback and is never invoked automatically. Replay mode requires precomputed output files to exist.

**Verification:**
- Check `manifest.runtime_mode` field in the run's manifest.json
- Verify `ResultMetadata.runtime_mode` via GET /api/results/{run_id}/metadata
- Value should be `"replay"` only when explicitly requested

**Common Replay Errors:**

- `422 Unprocessable Entity: Replay mode unavailable` — No precomputed data files found
  - **Fix**: Ensure precomputed data exists in REFORMLAB_OPENFISCA_DATA_DIR or use live mode

## Population Resolution Diagnostics

### Population Sources

Populations can be:
- **Bundled**: Distributed with the product in `data/populations/`
- **Uploaded**: User-uploaded files in `.reformlab/uploaded-populations/`
- **Generated**: Synthetic populations created via data fusion or population generator

### Population Executability

All populations must be executable, meaning they contain minimum required columns for live execution.

**Required Columns:**
- `household_id`: Unique identifier for each household/entity
- `income`: Pre-tax household income
- `disposable_income`: Post-tax household income (needed for redistribution)
- `carbon_tax`: Carbon tax liability (needed for policy scenarios)

**Verification:**
- Check preflight output via POST /api/validation/preflight with `population_id`
- Inspect `manifest.population_id` and `manifest.population_source` in manifest.json
- Verify the population file exists and is readable

**Common Population Errors:**

- `Population '{id}' cannot be resolved` — Unknown population ID
  - **Fix**: Check available populations via GET /api/populations, use a valid ID
- `Population '{id}' is incompatible with live execution. Missing required columns: {columns}` — Schema validation failed
  - **Fix**: Ensure population file contains all required columns, regenerate population if needed

## Mapping and Normalization Diagnostics

### Normalization Layer

Live OpenFisca outputs are normalized to the app-facing schema via `result_normalizer.py`. The normalizer:

1. Maps French OpenFisca variable names to English project schema names
2. Validates that minimum required indicator columns are present
3. Returns a normalized `pa.Table` for downstream consumption

### Default Output Mapping

When no explicit `MappingConfig` is provided, the normalizer uses `_DEFAULT_OUTPUT_MAPPING`:

```python
{
    "revenu_disponible": "disposable_income",
    "irpp": "income_tax",
    "impots_directs": "direct_taxes",
    "revenu_net": "net_income",
    "salaire_net": "income",
    "revenu_brut": "gross_income",
    "prestations_sociales": "social_benefits",
    "taxe_carbone": "carbon_tax",
}
```

### Custom Mapping

If the default mapping doesn't match your adapter's output, provide a `MappingConfig` YAML file:

```yaml
output_mapping:
  your_french_variable: "your_project_field"
```

**Verification:**
- Check normalized output columns match expected project schema
- Verify indicator columns (income, disposable_income, carbon_tax) are present
- Use GET /api/results/{run_id}/panel to inspect normalized data

**Common Normalization Errors:**

- `Output normalization failed` — No recognizable OpenFisca columns found
  - **Fix**: Verify adapter output includes expected variables, provide MappingConfig if needed
- `Column rename produces duplicate '{name}'` — Mapping creates duplicate column name
  - **Fix**: Adjust MappingConfig to resolve naming conflict

## Failed Run Investigation Checklist

When a run fails, follow this step-by-step investigation:

### Step 1: Check Manifest

- Path: `{result_store}/{run_id}/manifest.json`
- Verify: `runtime_mode` is as expected ("live" or "replay")
- Verify: `population_id` and `population_source` are populated (if population was used)
- Check: `integrity_hash` matches content (tamper detection)

### Step 2: Check Metadata

- Endpoint: `GET /api/results/{run_id}/metadata`
- Verify: `runtime_mode`, `population_source`, and other metadata fields are present
- Check: Timestamps indicate expected execution order

### Step 3: Check Logs

- Location: `{logs_directory}` (container or local)
- Look for: ERROR or CRITICAL level messages around run timestamp
- Check: Adapter initialization logs (live vs replay selection)
- Check: Population resolution logs (file path, row count)

### Step 4: Validate Population

- Endpoint: `POST /api/validation/preflight` with `population_id`
- Verify: Preflight passes for requested population
- Check: Population file exists and is readable
- Verify: Schema contains required columns (household_id, income, disposable_income, carbon_tax)

### Step 5: Verify Adapter

- Check: Which adapter initialized (MockAdapter, OpenFiscaAdapter, OpenFiscaApiAdapter)
- Verify: Adapter version matches expected version
- Check: Any adapter-specific warnings in logs

### Step 6: Inspect Normalization

- Check: Normalization succeeded (no NormalizationError in logs)
- Verify: Normalized output contains expected columns
- Check: Mapping configuration was applied (if custom)

### Step 7: Test Indicators and Exports

- Endpoint: `POST /api/indicators/compute` with `run_id`
- Verify: Indicator computation returns 200 with valid result
- Endpoint: `POST /api/exports/parquet` with `run_id`
- Verify: Export succeeds and file is downloadable

## Additional Resources

- API Documentation: `/api/docs` — Full API reference
- Preflight Validation: `POST /api/validation/preflight` — Validate configuration before running
- Results API: `GET /api/results/{run_id}/*` — Retrieve run results and metadata
- Source Code: `src/reformlab/computation/result_normalizer.py` — Normalization implementation
```

### Scope Boundaries

**In scope:**
- Creating `tests/server/test_regression.py` with end-to-end regression tests
- Creating `docs/operator/runtime-diagnostics.md` with runtime troubleshooting guide
- Tests for bundled populations (live execution)
- Tests for uploaded populations (live execution)
- Tests for generated populations (live execution)
- Tests for explicit replay mode (smoke path)
- Tests verifying indicator, comparison, and export workflows work with live outputs
- Documentation for runtime, population, and mapping diagnostics

**Out of scope:**
- New features or functionality beyond testing and documentation
- Frontend changes (tests are backend-only)
- Indicator/comparison/export implementation correctness tests (those are unit tests in `tests/indicators/` or similar)
- Population generation implementation details (tests verify generated populations work, not how they're created)
- Comprehensive documentation of all error codes (focus on runtime/population/mapping-specific diagnostics)

### References

- Story 23.6 definition: `_bmad-output/planning-artifacts/epics.md` (Story BKL-2306)
- Story 23.2 (population resolver): `src/reformlab/server/population_resolver.py`
- Story 23.3 (normalization): `src/reformlab/computation/result_normalizer.py`
- Story 23.4 (live default): `src/reformlab/server/dependencies.py` (`_create_live_adapter`, `_create_replay_adapter`), `tests/server/test_live_default_runs.py`
- Story 23.5 (preflight and provenance): `src/reformlab/server/validation.py`, `tests/server/test_preflight_runtime.py`
- Validation registry: `src/reformlab/server/validation.py` (extensible check pattern)
- Preflight route: `src/reformlab/server/routes/validation.py` (`POST /api/validation/preflight`)
- Run route: `src/reformlab/server/routes/runs.py` (`POST /api/runs`)
- Results routes: `src/reformlab/server/routes/results.py`, `src/reformlab/server/routes/indicators.py`, `src/reformlab/server/routes/exports.py`
- RunManifest: `src/reformlab/governance/manifest.py` (provenance fields)
- ResultMetadata: `src/reformlab/server/result_store.py` (runtime_mode, population_source)
- Test fixtures: `tests/server/conftest.py`
- Project context: `_bmad-output/project-context.md` — frozen dataclasses, PyArrow-first, determinism
- Error style: `{"what": str, "why": str, "fix": str}` via `HTTPException(detail={...})`

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — this is a planning story, no debug logs required.

### Completion Notes List

- ✅ Story 23.6 comprehensive context analysis completed
- ✅ Tasks 1-10 defined covering all acceptance criteria
- ✅ Dev notes include architecture patterns, design decisions, test invariants, implementation patterns
- ✅ Documentation structure defined with runtime, population, and mapping diagnostics
- ✅ Test patterns defined following Stories 23.4 and 23.5 conventions
- ✅ Scope boundaries clearly delineated (in scope: regression tests and docs, out of scope: new features)
- ✅ References section cites all relevant source files and previous stories

### File List

**To be created:**
- `tests/server/test_regression.py` — End-to-end regression tests for Epic 23
- `docs/operator/runtime-diagnostics.md` — Operator-facing runtime diagnostics and troubleshooting guide

**Referenced (not modified):**
- `tests/server/conftest.py`
- `tests/server/test_live_default_runs.py`
- `tests/server/test_preflight_runtime.py`
- `src/reformlab/computation/result_normalizer.py`
- `src/reformlab/server/population_resolver.py`
- `src/reformlab/server/validation.py`
- `src/reformlab/governance/manifest.py`
- `src/reformlab/server/result_store.py`
- `src/reformlab/server/routes/runs.py`
- `src/reformlab/server/routes/validation.py`
- `src/reformlab/server/routes/results.py`
- `src/reformlab/server/routes/indicators.py`
- `src/reformlab/server/routes/exports.py`

## Change Log

- Story 23.6 ready for dev (Date: 2026-04-16)
  - Comprehensive regression test plan defined for bundled, uploaded, generated populations
  - Replay smoke tests defined for explicit replay mode
  - Indicator, comparison, and export workflow regression tests defined
  - Operator documentation structure defined for runtime, population, and mapping diagnostics
  - All acceptance criteria (1-4) mapped to tasks 1-10
