# Story 23.5: Extend preflight, manifests, and result metadata with runtime and population provenance

Status: ready-for-dev

## Story

As an analyst,
I want preflight checks to validate runtime support and population executability before my run starts, and I want completed runs to record which runtime executed and which population was used in their manifest and result metadata,
so that I can trust the run outputs, understand exactly how each result was produced, and get clear guidance when my configuration is unsupported.

**Epic:** Epic 23 — Live OpenFisca Runtime and Executable Population Alignment
**Priority:** P0
**Estimate:** 5 SP
**Dependencies:** Story 23.1 (runtime-mode contract), Story 23.4 (default live execution wired)

## Acceptance Criteria

1. Given a run request that specifies a population_id which cannot be resolved to an executable dataset, when preflight validation runs, then execution is blocked with an actionable error identifying the missing population and suggesting available alternatives.
2. Given a completed run, when its manifest is inspected, then `runtime_mode` and `population_id`/`population_source` are visible as first-class manifest fields.
3. Given a completed run, when its result metadata is inspected, then `runtime_mode` and `population_source` are present and populated (extending the fields already added by Stories 23.1/23.2).
4. Given a run request where the selected population is resolved but has a schema incompatible with live execution, when preflight runs, then the validation output identifies the missing or incompatible fields clearly.
5. Given a supported live run with only non-blocking informational caveats (e.g., MockAdapter fallback in dev), when preflight runs, then the analyst receives an explicit warning without any replay fallback implication.
6. Given a supported live run, when preflight passes cleanly, then the analyst receives no false replay warnings.

## Tasks / Subtasks

### Task 1: Add population provenance fields to RunManifest (AC: 2)

- [ ] **Extend `RunManifest` in `src/reformlab/governance/manifest.py`** (AC: 2)
  - [ ] Add `population_id: str = ""` field — the population identifier used for execution (empty string for runs without a population, matching the existing pattern for optional manifest fields)
  - [ ] Add `population_source: str = ""` field — "bundled", "uploaded", or "generated" (empty string for runs without a population)
  - [ ] Add validation in `_validate()`: when `population_id` is non-empty, `population_source` must be one of "bundled", "uploaded", "generated"
  - [ ] Update `to_json()` serialization: include these fields (they have non-None defaults so will always serialize)
  - [ ] Update `from_json()` deserialization: read these fields with empty-string defaults for backward compatibility with existing manifests on disk
  - [ ] Update the docstring to reference Story 23.5 / AC-2

### Task 2: Thread population provenance through the run route into manifest and metadata (AC: 2, 3)

- [ ] **Update `run_simulation()` in `src/reformlab/server/routes/runs.py`** (AC: 2, 3)
  - [ ] After population resolution (where `population_source` is already obtained), pass `population_id` and `population_source` through to `ScenarioConfig` (already done for `population_id`/`population_source` since Story 23.3)
  - [ ] Ensure `_run_portfolio()` also threads `population_id`/`population_source` through (already done since Story 23.3)
  - [ ] After `run_scenario()` returns, propagate `population_id` and `population_source` from the resolver into the stored `ResultMetadata` (already done since Story 23.2)
  - [ ] **New**: After `run_scenario()` returns, update the manifest's `population_id` and `population_source` fields using `dataclasses.replace()` on `result.manifest` before saving to disk and cache. The manifest currently lacks these fields (Task 1 adds them), so this threading is the critical connection
  - [ ] Store the updated manifest (with population provenance) via `store.save_manifest()` and use the updated manifest when caching the result

- [ ] **Update `_run_direct_scenario()` in `src/reformlab/interfaces/api.py`** (AC: 2)
  - [ ] Thread `population_id` and `population_source` from `ScenarioConfig` into the `RunManifest` constructor when building the direct-scenario manifest (currently hardcodes `runtime_mode="live"` but has no population fields)
  - [ ] Note: `ScenarioConfig.population_id` and `ScenarioConfig.population_source` already exist from Story 23.3

### Task 3: Add runtime-population preflight validation checks (AC: 1, 4, 5, 6)

- [ ] **Add two new validation checks in `src/reformlab/server/validation.py`** (AC: 1, 4, 5, 6)
  - [ ] `runtime-support` check (severity: "error"):
    - Validate that the runtime mode is supported for the given configuration
    - For `runtime_mode == "replay"`, verify precomputed data files exist (reuse `_create_replay_adapter()` logic or check data dir)
    - For `runtime_mode == "live"` (default), always passes — live is the default and always supported
    - Error message format: `"Runtime mode '{mode}' is not available: {reason}. {fix}"`
  - [ ] `population-executable` check (severity: "error"):
    - Validate that the selected `population_id` resolves to an executable dataset
    - Use `PopulationResolver.resolve()` to attempt resolution
    - If `population_id` is not provided, pass with info message (not all runs require populations)
    - If resolution fails, fail with available population IDs listed
    - If resolution succeeds, optionally validate that the data file is readable (quick file-exists check)
    - Error message format: `"Population '{id}' is not executable: {reason}. Available: {ids}"`

- [ ] **Register new checks in `_register_builtin_checks()`** (AC: 1, 4)
  - [ ] Add `runtime-support` check with severity "error"
  - [ ] Add `population-executable` check with severity "error"

- [ ] **Extend `PreflightRequest` in `src/reformlab/server/models.py`** (AC: 1, 4)
  - [ ] Add `runtime_mode: Literal["live", "replay"] = "live"` field to `PreflightRequest` so the runtime-support check can validate the requested mode
  - [ ] The existing `population_id` field is already present and can be used by the population-executable check

- [ ] **Add runtime-mode informational warning check** (AC: 5, 6)
  - [ ] `runtime-info` check (severity: "warning"):
    - When the adapter is MockAdapter (dev fallback), emit a non-blocking warning: "Running with MockAdapter — results use synthetic data, not live OpenFisca computation"
    - When the adapter is a real live adapter and runtime_mode is "live", pass cleanly with no warning
    - When runtime_mode is "replay", pass with info message "Using replay mode — results come from precomputed outputs"
    - This check must NOT imply that replay is being silently substituted for live (AC: 6)

### Task 4: Add preflight validation tests (AC: 1, 4, 5, 6)

- [ ] **Create `tests/server/test_preflight_runtime.py`** (AC: 1, 4, 5, 6)
  - [ ] `TestRuntimeSupportCheck`:
    - `test_live_mode_passes()` — runtime_mode="live" passes runtime-support check
    - `test_replay_mode_passes_when_data_exists()` — runtime_mode="replay" passes when precomputed data exists
    - `test_replay_mode_fails_when_no_data()` — runtime_mode="replay" fails when no precomputed data
    - `test_default_live_mode_passes()` — no runtime_mode specified defaults to "live" and passes
  - [ ] `TestPopulationExecutableCheck`:
    - `test_valid_bundled_population_passes()` — existing bundled population resolves and passes
    - `test_missing_population_fails_with_available_ids()` — unknown population_id fails with actionable error listing available IDs
    - `test_no_population_passes()` — no population_id provided passes (not all runs need populations)
    - `test_uploaded_population_passes()` — uploaded population resolves and passes
  - [ ] `TestRuntimeInfoWarning`:
    - `test_mock_adapter_emits_warning()` — MockAdapter produces non-blocking warning
    - `test_live_adapter_no_warning()` — real live adapter produces no warning
    - `test_replay_mode_info_message()` — replay mode shows info, not a replay-fallback warning
    - `test_clean_live_run_no_false_warnings()` — supported live run produces zero false replay warnings

### Task 5: Add manifest and metadata provenance tests (AC: 2, 3)

- [ ] **Extend `tests/server/test_runs.py`** (AC: 2, 3)
  - [ ] `TestManifestPopulationProvenance`:
    - `test_manifest_records_population_id()` — after a run with population_id, manifest.json on disk contains the population_id
    - `test_manifest_records_population_source()` — after a run, manifest.json contains population_source ("bundled"/"uploaded"/"generated")
    - `test_manifest_records_runtime_mode()` — manifest.json contains runtime_mode (already tested in 23.4, verify with population)
    - `test_manifest_without_population_has_empty_fields()` — run without population_id has empty string population_id and population_source in manifest
  - [ ] `TestMetadataPopulationProvenance`:
    - `test_metadata_population_source_matches_resolver()` — ResultMetadata.population_source matches what the resolver returned
    - `test_metadata_runtime_mode_matches_manifest()` — ResultMetadata.runtime_mode matches manifest.runtime_mode

- [ ] **Add manifest backward-compatibility test** (AC: 2)
  - [ ] `test_from_json_handles_missing_population_fields()` — loading an old manifest without population_id/population_source defaults to empty strings

### Task 6: Add negative-path and edge-case tests (AC: 4)

- [ ] **Extend `tests/server/test_preflight_runtime.py`** (AC: 4)
  - [ ] `TestPopulationSchemaCompatibility`:
    - `test_schema_incompatible_population_fails()` — population with incompatible schema (e.g., missing required columns) produces clear validation error identifying the missing fields
  - [ ] Note: Full schema validation at preflight time is lightweight (column-name check via PyArrow schema read). Deep validation happens at execution time via the normalizer (Story 23.3). The preflight check just verifies the file is readable and has the minimum expected structure.

## Dev Notes

### Architecture Patterns

**The Core Gap This Story Closes**

Stories 23.1–23.4 built the runtime mode contract, population resolver, normalization layer, and live-default adapter wiring. But the provenance chain has two gaps:

1. **RunManifest lacks population provenance**: `ResultMetadata` has `population_id` and `population_source` (Story 23.2), but `RunManifest` does not. Manifests are the audit/reproducibility artifact — they MUST contain population provenance.

2. **No preflight validation for runtime/population**: The existing preflight registry (`validation.py`) has 7 checks (portfolio-selected, population-selected, time-horizon-valid, investment-decisions-calibrated, memory-preflight, exogenous-coverage, trust-status) but NONE validate runtime mode support or population executability. A run with an unresolvable population currently fails deep in execution with a less actionable error than preflight would provide.

**Existing Infrastructure to Reuse**

1. **Validation check registry** (`validation.py`): Extensible pattern with `ValidationCheck` class, `register_check()`, and `_register_builtin_checks()`. New checks follow the exact same pattern. Each check is a function `(PreflightRequest) -> ValidationCheckResult`, registered at import time.

2. **PopulationResolver** (`population_resolver.py`): Already resolves `population_id` → `ResolvedPopulation(source, data_path, row_count)`. Already handles bundled/uploaded/generated classification. Already raises `PopulationResolutionError` with `{what, why, fix}` detail and `available_ids`. The preflight check wraps this resolver.

3. **RunManifest** (`manifest.py`): Frozen dataclass with `__post_init__` validation, `to_json()`/`from_json()` serialization, and integrity hashing. New fields follow the exact same pattern as `runtime_mode` (added in Story 23.1).

4. **ResultMetadata** (`result_store.py`): Already has `runtime_mode` and `population_source` fields from Stories 23.1/23.2. No changes needed to this dataclass.

5. **Run route** (`runs.py`): Already resolves population, captures `population_source`, and builds `ResultMetadata` with both fields. The threading of population provenance into the manifest is the missing piece.

**Key Design Decisions**

**Manifest population fields use empty-string defaults** (not Optional/None): Following the established pattern in `RunManifest` where optional fields use empty string defaults (e.g., `parent_manifest_id: str = ""`). This keeps the manifest's type contract simple and avoids Optional handling in serialization/deserialization. The `_validate()` method only validates when the field is non-empty.

**Preflight population check does NOT do deep schema validation**: The preflight check verifies resolution (can we find the file?) and basic readability. Deep schema validation (column names, types) happens at execution time via the normalizer (Story 23.3). This keeps preflight fast and avoids duplicating normalization logic.

**Runtime-info warning uses severity "warning"**: Per AC-5, non-blocking caveats use warning severity. Per AC-6, clean live runs produce no false warnings. The warning check detects MockAdapter fallback (dev mode) and replay mode without implying silent substitution.

**The check determines MockAdapter by checking the global adapter type**: The `runtime-info` check reads `get_adapter().__class__.__name__` to determine if it's `MockAdapter`. This is lightweight and doesn't require new infrastructure.

### Source Tree Components

**Files to modify:**

| File Path | Purpose | Key Changes |
|-----------|---------|-------------|
| `src/reformlab/governance/manifest.py` | RunManifest dataclass | Add `population_id: str = ""` and `population_source: str = ""` fields; add validation; update to_json/from_json |
| `src/reformlab/server/validation.py` | Validation check registry | Add `runtime-support`, `population-executable`, and `runtime-info` checks; register in `_register_builtin_checks()` |
| `src/reformlab/server/models.py` | PreflightRequest model | Add `runtime_mode: Literal["live", "replay"] = "live"` field |
| `src/reformlab/server/routes/runs.py` | Run endpoint | Thread `population_id`/`population_source` into manifest via `dataclasses.replace()` before save |
| `src/reformlab/interfaces/api.py` | Python API | Thread `population_id`/`population_source` into direct-scenario manifest constructor |

**New files to create:**

| File Path | Purpose |
|-----------|---------|
| `tests/server/test_preflight_runtime.py` | Tests for runtime/population preflight checks and provenance |

### Implementation Notes

**RunManifest Extension**

```python
# manifest.py — new fields after runtime_mode

# Story 23.5 / AC-2: Population provenance for audit and comparison flows
population_id: str = ""  # empty when run has no population
population_source: str = ""  # "bundled" | "uploaded" | "generated" | ""
```

Validation in `_validate()`:
```python
# Story 23.5 / AC-2: Validate population provenance when present
if self.population_id:
    valid_sources = ("bundled", "uploaded", "generated")
    if self.population_source not in valid_sources:
        raise ManifestValidationError(
            f"Invalid population_source: expected one of {valid_sources}, "
            f"got {self.population_source!r}"
        )
```

from_json() backward compatibility:
```python
# Story 23.5: Backward-compatible deserialization
population_id=data.get("population_id", ""),
population_source=data.get("population_source", ""),
```

**Threading Population Provenance into Manifest (Run Route)**

The run route already has `population_id` (from `body.population_id`) and `population_source` (from the resolver). After `run_scenario()` returns, the manifest needs these fields:

```python
# runs.py — after result is obtained, before save
from dataclasses import replace as _dc_replace

# Story 23.5 / AC-2: Add population provenance to manifest
updated_manifest = _dc_replace(
    result.manifest,
    population_id=body.population_id or "",
    population_source=population_source or "",
)
# Use updated_manifest for save_manifest, cache store, and response
```

Important: The `RunManifest` is frozen, so `dataclasses.replace()` creates a new instance. The integrity hash will be recomputed when `with_integrity_hash()` is called (if applicable), but the manifest saved to disk does not require integrity hash — that's optional.

**Preflight Runtime-Support Check**

```python
def _check_runtime_support(request: PreflightRequest) -> ValidationCheckResult:
    """Story 23.5 / AC-1: Validate runtime mode is available."""
    runtime_mode = request.runtime_mode  # New field on PreflightRequest

    if runtime_mode == "replay":
        # Verify precomputed data exists
        try:
            from reformlab.server.dependencies import _create_replay_adapter
            _create_replay_adapter()  # Raises if no data files
        except (FileNotFoundError, ValueError, OSError):
            return ValidationCheckResult(
                id="runtime-support",
                label="Runtime support",
                passed=False,
                severity="error",
                message=(
                    "Replay mode requires precomputed output files, "
                    "but none were found in the data directory. "
                    "Run in live mode (default) or ensure precomputed data exists."
                ),
            )
        return ValidationCheckResult(
            id="runtime-support",
            label="Runtime support",
            passed=True,
            severity="error",
            message="Replay mode available with precomputed data",
        )

    # Default: live mode always supported
    return ValidationCheckResult(
        id="runtime-support",
        label="Runtime support",
        passed=True,
        severity="error",
        message="Live execution mode (default)",
    )
```

**Preflight Population-Executable Check**

```python
def _check_population_executable(request: PreflightRequest) -> ValidationCheckResult:
    """Story 23.5 / AC-1, AC-4: Validate population is executable."""
    if not request.population_id:
        return ValidationCheckResult(
            id="population-executable",
            label="Population executable",
            passed=True,
            severity="error",
            message="No population selected — run will use default data",
        )

    from reformlab.server.dependencies import get_population_resolver
    from reformlab.server.population_resolver import PopulationResolutionError

    resolver = get_population_resolver()
    try:
        resolved = resolver.resolve(request.population_id)
        return ValidationCheckResult(
            id="population-executable",
            label="Population executable",
            passed=True,
            severity="error",
            message=(
                f"Population '{request.population_id}' resolved "
                f"({resolved.source}, {resolved.row_count or '?'} rows)"
            ),
        )
    except PopulationResolutionError as exc:
        available = getattr(exc, "available_ids", [])
        available_str = ", ".join(available[:5]) if available else "none"
        return ValidationCheckResult(
            id="population-executable",
            label="Population executable",
            passed=False,
            severity="error",
            message=(
                f"Population '{request.population_id}' cannot be resolved. "
                f"Available populations: {available_str}"
            ),
        )
```

**PreflightRequest Extension**

```python
# models.py
class PreflightRequest(BaseModel):
    """Request for pre-execution validation."""
    scenario: dict[str, Any]
    population_id: str | None = None
    template_name: str | None = None
    runtime_mode: Literal["live", "replay"] = "live"  # Story 23.5
```

**Runtime-Info Warning Check**

```python
def _check_runtime_info(request: PreflightRequest) -> ValidationCheckResult:
    """Story 23.5 / AC-5, AC-6: Informational runtime status."""
    from reformlab.server.dependencies import get_adapter

    adapter = get_adapter()
    adapter_class = adapter.__class__.__name__

    if adapter_class == "MockAdapter":
        return ValidationCheckResult(
            id="runtime-info",
            label="Runtime status",
            passed=True,  # Warning, not error
            severity="warning",
            message=(
                "Running with MockAdapter — results use synthetic data, "
                "not live OpenFisca computation. Install OpenFisca for live runs."
            ),
        )

    if request.runtime_mode == "replay":
        return ValidationCheckResult(
            id="runtime-info",
            label="Runtime status",
            passed=True,
            severity="warning",
            message="Using replay mode — results come from precomputed outputs",
        )

    # Live mode with real adapter: clean pass, no false warnings
    return ValidationCheckResult(
        id="runtime-info",
        label="Runtime status",
        passed=True,
        severity="warning",
        message="Live OpenFisca execution",
    )
```

### Testing Standards

- **Server integration tests** use `TestClient` with `MockAdapter` injected via `monkeypatch` (see `tests/server/conftest.py`)
- **Preflight tests** call `POST /api/validation/preflight` with `PreflightRequest` body, asserting `PreflightResponse.passed`, `checks[]`, and `warnings[]`
- **Manifest tests** read `manifest.json` from disk after run and assert field presence and values
- **Metadata tests** use `ResultStore.list_results()` or `ResultStore.get_metadata()` to inspect persisted metadata
- **Population tests** create population files in `tmp_path` and inject a `PopulationResolver` scoped to that directory
- All tests use `MockAdapter` — no real OpenFisca needed
- Use `caplog` for logging assertions where applicable

### Scope Boundaries

**In scope:**
- Adding `population_id` and `population_source` fields to `RunManifest`
- Threading population provenance into manifest in both run route and Python API
- Adding `runtime-support`, `population-executable`, and `runtime-info` preflight checks
- Adding `runtime_mode` field to `PreflightRequest`
- Tests for all new checks and provenance fields
- Backward compatibility for existing manifests without population fields

**Out of scope:**
- Frontend changes (preflight checks are backend-only; frontend calls the same endpoint)
- Deep schema validation at preflight time (that's the normalizer's job, Story 23.3)
- New API endpoints (extending existing preflight and run endpoints)
- Result cache changes (cache stores `SimulationResult` which includes the manifest)
- Portfolio-specific population handling (portfolios already thread population_id/source since Story 23.3)

### References

- Story 23.5 definition: `_bmad-output/planning-artifacts/epics.md` (Story BKL-2305)
- Story 23.1 (runtime-mode contract): `src/reformlab/computation/types.py` (`RuntimeMode`), `src/reformlab/server/models.py` (`RunRequest.runtime_mode`)
- Story 23.2 (population resolver): `src/reformlab/server/population_resolver.py`, `src/reformlab/server/result_store.py` (`ResultMetadata.population_source`)
- Story 23.3 (normalization): `src/reformlab/computation/result_normalizer.py`
- Story 23.4 (live default): `src/reformlab/server/dependencies.py` (`_create_live_adapter`, `_create_replay_adapter`), `src/reformlab/server/routes/runs.py`
- Validation registry: `src/reformlab/server/validation.py` (extensible check pattern with `ValidationCheck`, `register_check()`, `run_checks()`)
- Preflight route: `src/reformlab/server/routes/validation.py` (`POST /api/validation/preflight`)
- Preflight models: `src/reformlab/server/models.py` (`PreflightRequest`, `PreflightResponse`, `ValidationCheckResult`)
- RunManifest: `src/reformlab/governance/manifest.py` (frozen dataclass, `_validate()`, `to_json()`/`from_json()`)
- ResultMetadata: `src/reformlab/server/result_store.py` (already has `runtime_mode` and `population_source`)
- Run route metadata assembly: `src/reformlab/server/routes/runs.py:180-214`
- Test patterns: `tests/server/test_runs.py`, `tests/server/test_live_default_runs.py`, `tests/server/test_dependencies.py`
- Project context: `_bmad-output/project-context.md` — frozen dataclasses, adapter isolation, PyArrow-first, determinism, assumption transparency
- Error style: `{"what": str, "why": str, "fix": str}` via `HTTPException(detail={...})`

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
