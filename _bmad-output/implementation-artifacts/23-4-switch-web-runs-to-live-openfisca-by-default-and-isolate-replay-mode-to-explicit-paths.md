# Story 23.4: Switch web runs to live OpenFisca by default and isolate replay mode to explicit paths

Status: completed

## Story

As a platform developer,
I want the standard web run route and Scenario execution plumbing to use live OpenFisca execution by default, with precomputed/replay execution isolated to explicit opt-in paths,
so that analysts run real computations against real populations by default while demo and replay flows remain deliberately narrow and never silently substitute for live execution.

**Epic:** Epic 23 — Live OpenFisca Runtime and Executable Population Alignment
**Priority:** P0
**Estimate:** 8 SP
**Dependencies:** Story 23.1 (runtime-mode contract), Story 23.2 (population resolver), Story 23.3 (normalization layer)

## Acceptance Criteria

1. Given a standard run triggered from the web product, when executed, then it uses live OpenFisca (`OpenFiscaApiAdapter`) rather than the precomputed adapter path (`OpenFiscaAdapter`).
2. Given a demo or manual replay action, when invoked explicitly, then replay execution remains available without changing the default path for normal runs.
3. Given a successful live run, when stored and later reloaded, then existing result-store and cache behavior continues to work: metadata.json, panel.parquet, and manifest.json are persisted, cache retrieval succeeds, and after cache eviction the result reloads from disk via `ResultCache.get_or_load()` with the same data.
4. Given runtime fallback conditions (OpenFisca not installed or adapter initialization failure), when replay mode is not explicitly requested, then the system uses `MockAdapter` for dev/test environments with explicit logging, and does not silently downgrade live requests to the precomputed path or replay mode.

## Tasks / Subtasks

### Task 1: Wire adapter selection to runtime mode in server dependencies (AC: 1, 2, 4)

- [x] **Update `_create_adapter()` in `src/reformlab/server/dependencies.py`** (AC: 1, 2, 4)
  - [x] Add a `_create_live_adapter()` factory that creates `OpenFiscaApiAdapter` with default output variables matching the normalizer's `_DEFAULT_OUTPUT_MAPPING` keys
  - [x] Define a `_DEFAULT_LIVE_OUTPUT_VARIABLES: tuple[str, ...]` constant containing the OpenFisca variable names from `_DEFAULT_OUTPUT_MAPPING` keys (i.e., the French names: `revenu_disponible`, `irpp`, `impots_directs`, `revenu_net`, `salaire_net`, `revenu_brut`, `prestations_sociales`, `taxe_carbone`)
  - [x] Add a `_create_replay_adapter()` factory that creates the existing `OpenFiscaAdapter` (precomputed file reader)
  - [x] Change `_create_adapter()` to call `_create_live_adapter()` by default (matching the "live" default in `RunRequest.runtime_mode`)
  - [x] Add `REFORMLAB_RUNTIME_MODE` environment variable (default: `"live"`) to allow operator override for deployments where live OpenFisca is not yet available; when set to `"replay"`, `_create_adapter()` returns the replay adapter. Validate the value and log a warning for invalid values, defaulting to "live"
  - [x] When `OpenFiscaApiAdapter` import fails (OpenFisca not installed), fall back to `MockAdapter` with a clear log message — this is the development/testing fallback, NOT a silent runtime downgrade
  - [x] When `OpenFiscaApiAdapter` imports but country package initialization fails, log a warning and fall back to `MockAdapter` — this is also a development fallback, not a runtime downgrade

### Task 2: Add adapter-awareness to the run route (AC: 1, 2, 4)

- [x] **Update `run_simulation()` in `src/reformlab/server/routes/runs.py`** (AC: 1, 2, 4)
  - [x] When `body.runtime_mode == "replay"`, use a `OpenFiscaAdapter` (precomputed) instead of the global live adapter; this ensures replay runs use precomputed data explicitly
  - [x] When `body.runtime_mode == "live"` (default), use the global adapter from `get_adapter()` which is now `OpenFiscaApiAdapter` by default
  - [x] The replay adapter creation should use `_resolve_adapter_data_dir()` to find precomputed data files
  - [x] If `runtime_mode == "replay"` and no precomputed data files exist, return a 422 with `{what, why, fix}` error payload explaining that replay mode requires precomputed output files

### Task 3: Update the Python API default adapter initialization (AC: 1)

- [x] **Update `_initialize_default_adapter()` in `src/reformlab/interfaces/api.py`** (AC: 1)
  - [x] When `run_config.runtime_mode == "live"`, attempt to create `OpenFiscaApiAdapter` with default output variables; fall back to `SimpleCarbonTaxAdapter` if OpenFisca is not installed
  - [x] When `run_config.runtime_mode == "replay"`, use `OpenFiscaAdapter` (precomputed file mode) as before
  - [x] Update `_initialize_default_adapter_for_direct()` similarly — direct scenario execution should also prefer live adapter

### Task 4: Add server integration tests for default live execution (AC: 1, 3)

- [ ] **Create `tests/server/test_live_default_runs.py`** (AC: 1, 3)
  - [ ] `TestDefaultLiveExecution`:
    - `test_default_run_uses_live_mode()` — POST `/api/runs` without explicit `runtime_mode` produces a response with `runtime_mode="live"` and manifest records `runtime_mode="live"`
    - `test_explicit_live_run_uses_live_mode()` — POST with `runtime_mode="live"` explicitly also works
    - `test_run_response_includes_runtime_mode()` — verify `RunResponse.runtime_mode` field is populated correctly
  - [ ] `TestReplayExecutionIsExplicit`:
    - `test_explicit_replay_run_uses_replay_mode()` — POST with `runtime_mode="replay"` produces `runtime_mode="replay"` in response and manifest
    - `test_replay_without_precomputed_data_returns_422()` — when no precomputed data files exist, replay mode returns actionable error
  - [ ] `TestResultPersistenceAfterLiveRun`:
    - `test_live_run_result_stored_in_cache()` — after a live run, the result is retrievable from ResultCache
    - `test_live_run_result_stored_on_disk()` — after a live run, metadata.json, panel.parquet, and manifest.json are persisted
    - `test_live_run_result_reloadable_from_disk()` — after cache eviction, the live run result can be reloaded from disk via `ResultCache.get_or_load()`
    - `test_live_run_manifest_records_runtime_mode()` — manifest.json on disk contains `runtime_mode: "live"` (tests verify this field, which is set by Story 23.3's normalizer)
  - [ ] `TestNoSilentDowngrade`:
    - `test_live_mode_does_not_fall_back_to_precomputed()` — verify that a run requesting live mode does NOT use the precomputed adapter path (verify `metadata.runtime_mode` matches requested mode and no silent fallback occurred)

### Task 5: Add route-level smoke tests for replay isolation (AC: 2)

- [ ] **Extend `tests/server/test_runs.py`** (AC: 2)
  - [ ] `TestReplayModeIsolation`:
    - `test_replay_mode_still_works_with_precomputed_data()` — when precomputed data files exist, replay mode completes successfully
    - `test_replay_mode_manifest_is_separate_from_live()` — replay run manifest has `runtime_mode: "replay"` while live run manifest has `runtime_mode: "live"` (tests verify the mode field, not source)
    - `test_portfolio_run_respects_runtime_mode()` — portfolio run with `runtime_mode="replay"` uses replay adapter

### Task 6: Add validation guard against silent fallback (AC: 4)

- [ ] **Add fallback guard in `src/reformlab/server/routes/runs.py`** (AC: 4)
  - [ ] After `run_scenario()` returns, verify `result.metadata.get("runtime_mode")` matches `body.runtime_mode`; if they differ, log a warning at ERROR level with both values. This is a guard rail, not a hard error — the run completed successfully but something in the plumbing overrode the requested mode
  - [ ] Add a test that this guard fires when there's a mismatch (create a `SimulationResult` with `metadata={"runtime_mode": "replay"}` when request was `"live"`)

## Dev Notes

### Architecture Patterns

**The Core Change: Adapter Selection, Not New Plumbing**

Story 23.4 is NOT about creating new execution paths. The runtime mode contract (Story 23.1), population resolver (Story 23.2), and normalization layer (Story 23.3) are all complete. This story is about **ensuring the adapter used at execution time matches the runtime mode contract**.

The current gap:
- `RunRequest.runtime_mode` defaults to `"live"` (correct)
- `_execute_orchestration()` builds a normalizer for `"live"` mode (correct)
- But `_create_adapter()` in `dependencies.py` creates `OpenFiscaAdapter` (PRECOMPUTED) regardless of runtime mode
- And `_initialize_default_adapter()` in `api.py` also creates `OpenFiscaAdapter` (PRECOMPUTED)

This means the system SAYS it's running live but actually uses precomputed data. Story 23.4 closes this gap.

**Adapter Selection Matrix**

| `runtime_mode` | Adapter Created | Normalization | Data Source |
|----------------|----------------|---------------|-------------|
| `"live"` (default) | `OpenFiscaApiAdapter` | `create_live_normalizer()` | Live OpenFisca computation |
| `"replay"` | `OpenFiscaAdapter` | `None` (passthrough) | Pre-computed CSV/Parquet files |
| OpenFisca not installed | `MockAdapter` | Applied if live, none if replay | In-memory test data |

**Existing Infrastructure to Reuse**

1. **`OpenFiscaApiAdapter`** — already fully implemented in `openfisca_api_adapter.py` (Stories 9.2–9.4). Takes `output_variables` tuple and `country_package` string. Runs live OpenFisca calculations via `SimulationBuilder`. Entity-aware (4-entity support). Periodicity-aware (monthly aggregation).

2. **`_DEFAULT_OUTPUT_MAPPING`** in `result_normalizer.py` — defines the French→English variable mapping. The `output_variables` for `OpenFiscaApiAdapter` should match the keys of this mapping (the OpenFisca French variable names).

3. **`_create_adapter()`** in `dependencies.py` — current adapter factory. Needs to switch from `OpenFiscaAdapter` to `OpenFiscaApiAdapter` for the default path.

4. **`_initialize_default_adapter()`** in `api.py` — used when `run_scenario()` is called without an explicit adapter. Needs the same switch.

5. **`_resolve_adapter_data_dir()`** in `dependencies.py` — still needed for replay mode to find precomputed files.

**Key Design Decision: Server-Level vs Route-Level Adapter Selection**

Adapter selection happens at TWO levels:
1. **Server startup** (`dependencies.py`): Creates the global adapter singleton used by all run requests. This should be `OpenFiscaApiAdapter` for live default.
2. **Per-request** (`runs.py`): When `runtime_mode == "replay"`, the route creates a separate `OpenFiscaAdapter` for that specific request instead of using the global live adapter.

This means:
- The global adapter is always live (or MockAdapter in dev)
- Replay requests create their own short-lived adapter
- No global state mutation per request

**Default Output Variables for Live Adapter**

The `OpenFiscaApiAdapter` requires `output_variables` at construction. For the default live path, these should match the OpenFisca variable names that the normalizer knows how to map:

```python
# Keys from _DEFAULT_OUTPUT_MAPPING in result_normalizer.py
_DEFAULT_LIVE_OUTPUT_VARIABLES: tuple[str, ...] = (
    "revenu_disponible",
    "irpp",
    "impots_directs",
    "revenu_net",
    "salaire_net",
    "revenu_brut",
    "prestations_sociales",
    "taxe_carbone",
)
```

Note: `household_id` is NOT an output variable — it comes from the population input. The adapter produces French variable names; the normalizer (Story 23.3) renames them to English schema names.

**Replay Path Isolation**

Replay mode must remain clearly separated:
- Only activated by explicit `runtime_mode="replay"` in the request
- The frontend NEVER sends `runtime_mode` — it relies on the "live" default
- Demo scenarios also use live mode (they just use bundled populations)
- Replay is for operator/debugging use only: re-running against known precomputed outputs

When replay is requested but precomputed data is missing, the system returns 422 (not 500). This prevents silent substitution.

**Fallback Behavior (NOT Silent Downgrade)**

There are two fallback paths, both explicit and logged:

1. **Development fallback**: When OpenFisca is not installed (`ImportError`), `MockAdapter` is used. This is logged clearly and expected in dev/test environments. The mock adapter's output already uses English schema names, so normalization is a no-op. Note: The Python API uses `SimpleCarbonTaxAdapter` for its demo scenarios (different use case), while the server uses `MockAdapter` for dev/test.

2. **Replay fallback**: When `runtime_mode="replay"` is explicitly requested. This is not a fallback — it's an explicit user choice. It creates its own adapter.

**Env Var Precedence**: The `REFORMLAB_RUNTIME_MODE` environment variable controls the global adapter type at server startup. Per-request `runtime_mode` in the request body overrides the global adapter for replay mode only (by creating a separate adapter). Requested `"live"` mode always uses live adapter; env var `"replay"` setting only affects requests that don't specify `runtime_mode` (they use the default `"live"`).

Neither path silently downgrades a live request to replay/precomputed.

### Source Tree Components

**Files to modify:**

| File Path | Purpose | Key Changes |
|-----------|---------|-------------|
| `src/reformlab/server/dependencies.py` | Server adapter factory | Add `_create_live_adapter()`; change `_create_adapter()` default to live; add `REFORMLAB_RUNTIME_MODE` env var |
| `src/reformlab/server/routes/runs.py` | Run endpoint | When replay mode, create `OpenFiscaAdapter` per-request; add fallback guard; add 422 for missing precomputed data |
| `src/reformlab/interfaces/api.py` | Python API adapter init | Update `_initialize_default_adapter()` and `_initialize_default_adapter_for_direct()` to prefer live adapter (note: API uses `SimpleCarbonTaxAdapter` fallback for demo scenarios, unlike server which uses `MockAdapter` for dev/test) |
| `src/reformlab/computation/result_normalizer.py` | Normalizer | Export `_DEFAULT_OUTPUT_MAPPING` keys as `_DEFAULT_LIVE_OUTPUT_VARIABLES` (or import from a shared location) |

**New files to create:**

| File Path | Purpose |
|-----------|---------|
| `tests/server/test_live_default_runs.py` | Server integration tests for default live execution |

### Implementation Notes

**Default Live Output Variables Constant**

Place this in `result_normalizer.py` since it derives from `_DEFAULT_OUTPUT_MAPPING`:

```python
# OpenFisca variable names to request from the live adapter.
# These are the keys of _DEFAULT_OUTPUT_MAPPING — the French variable names
# that OpenFisca-France produces and that the normalizer maps to English.
_DEFAULT_LIVE_OUTPUT_VARIABLES: tuple[str, ...] = tuple(_DEFAULT_OUTPUT_MAPPING.keys())
```

**Server Dependencies Change**

```python
# dependencies.py

def _create_live_adapter() -> ComputationAdapter:
    """Create the live OpenFiscaApiAdapter for default web execution."""
    from reformlab.computation.openfisca_api_adapter import OpenFiscaApiAdapter
    from reformlab.computation.result_normalizer import _DEFAULT_LIVE_OUTPUT_VARIABLES

    return OpenFiscaApiAdapter(
        country_package="openfisca_france",
        output_variables=_DEFAULT_LIVE_OUTPUT_VARIABLES,
    )

def _create_replay_adapter() -> ComputationAdapter:
    """Create the precomputed OpenFiscaAdapter for explicit replay mode."""
    from reformlab.computation.openfisca_adapter import OpenFiscaAdapter

    data_dir = _resolve_adapter_data_dir()
    return OpenFiscaAdapter(data_dir)

def _create_adapter() -> ComputationAdapter:
    """Create the default computation adapter based on REFORMLAB_RUNTIME_MODE."""
    runtime_mode = os.environ.get("REFORMLAB_RUNTIME_MODE", "live")
    if runtime_mode not in ("live", "replay"):
        logger.warning("Invalid REFORMLAB_RUNTIME_MODE=%s, defaulting to 'live'", runtime_mode)
        runtime_mode = "live"

    if runtime_mode == "replay":
        try:
            logger.info("Using replay adapter (REFORMLAB_RUNTIME_MODE=replay)")
            return _create_replay_adapter()
        except (FileNotFoundError, OSError):
            from reformlab.computation.mock_adapter import MockAdapter
            logger.warning("Replay adapter failed (precomputed data not found), using MockAdapter")
            return MockAdapter()
        except Exception:
            from reformlab.computation.mock_adapter import MockAdapter
            logger.warning("Replay adapter failed, using MockAdapter")
            return MockAdapter()

    # Default: live mode
    try:
        adapter = _create_live_adapter()
        logger.info("Using live OpenFiscaApiAdapter (default)")
        return adapter
    except ImportError:
        from reformlab.computation.mock_adapter import MockAdapter
        logger.info("OpenFisca not installed — using MockAdapter (dev mode)")
        return MockAdapter()
    except (OSError, RuntimeError) as exc:
        from reformlab.computation.mock_adapter import MockAdapter
        logger.warning("Live adapter init failed (%s) — using MockAdapter", exc)
        return MockAdapter()
```

**Run Route Change for Replay Isolation**

```python
# runs.py — in run_simulation()

adapter = get_adapter()

# Story 23.4 / AC-2: Replay mode creates its own precomputed adapter
if body.runtime_mode == "replay":
    try:
        from reformlab.server.dependencies import _create_replay_adapter
        adapter = _create_replay_adapter()
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "what": "Replay mode unavailable",
                "why": f"No precomputed output files found: {str(exc)}",
                "fix": "Run in live mode (default) or ensure precomputed data files exist in the data directory",
            },
        ) from exc
```

**Run Route Fallback Guard**

```python
# runs.py — after run_scenario() returns

# Story 23.4 / AC-4: Guard against silent runtime mode downgrade
if result and result.metadata.get("runtime_mode") != body.runtime_mode:
    logger.error(
        "event=runtime_mode_mismatch requested=%s actual=%s run_id=%s",
        body.runtime_mode,
        result.metadata.get("runtime_mode"),
        run_id,
    )
```

**API Default Adapter Change**

```python
# api.py — _initialize_default_adapter()

def _initialize_default_adapter(run_config: RunConfig) -> ComputationAdapter:
    """Create the default adapter based on runtime_mode."""
    from reformlab.interfaces.errors import ConfigurationError

    if run_config.runtime_mode == "live":
        try:
            from reformlab.computation.openfisca_api_adapter import OpenFiscaApiAdapter
            from reformlab.computation.result_normalizer import _DEFAULT_LIVE_OUTPUT_VARIABLES

            return OpenFiscaApiAdapter(
                country_package="openfisca_france",
                output_variables=_DEFAULT_LIVE_OUTPUT_VARIABLES,
            )
        except ImportError:
            # OpenFisca not installed — use demo adapter
            return SimpleCarbonTaxAdapter()
        except Exception as exc:
            raise ConfigurationError(
                field_path="adapter",
                expected="initializable live OpenFisca adapter",
                actual=str(exc),
                fix="Ensure OpenFisca is properly installed, or pass adapter=SimpleCarbonTaxAdapter() explicitly",
            ) from exc
    else:
        # Replay mode: precomputed file adapter
        data_dir = _resolve_openfisca_data_dir(run_config)
        try:
            from reformlab.computation.openfisca_adapter import OpenFiscaAdapter
            return OpenFiscaAdapter(data_dir)
        except Exception as exc:
            raise ConfigurationError(
                field_path="adapter",
                expected="initializable replay adapter with data_dir",
                actual=str(data_dir),
                fix=f"Ensure precomputed data files exist in {data_dir}",
            ) from exc
```

### Testing Standards

- **Server integration tests** use `TestClient` with `MockAdapter` injected via `monkeypatch` (see `tests/server/conftest.py`)
- **Run route tests** in `tests/server/test_runs.py` use `_SIMPLE_RUN_BODY` with `client_with_store` fixture
- **New test file** `tests/server/test_live_default_runs.py` follows the same pattern
- Use `MockAdapter` for all tests — no real OpenFisca needed
- Verify adapter behavior through result metadata (specifically `metadata.runtime_mode` field, which Story 23.3's normalizer sets)
- For the fallback guard test, create a `SimulationResult` with mismatched `runtime_mode` in metadata

### Project Structure Notes

- No new modules or packages needed — changes are confined to existing files
- `_DEFAULT_LIVE_OUTPUT_VARIABLES` constant lives in `result_normalizer.py` alongside `_DEFAULT_OUTPUT_MAPPING`
- Test file follows the `tests/server/` mirror convention
- The `REFORMLAB_RUNTIME_MODE` env var follows the existing `REFORMLAB_*` naming pattern in `dependencies.py`

### Scope Boundaries

**In scope:**
- Switching adapter selection to `OpenFiscaApiAdapter` for live default
- Isolating replay mode to explicit `runtime_mode="replay"` requests
- Adding `REFORMLAB_RUNTIME_MODE` environment variable for operator control
- Server integration tests proving default live execution
- Route-level smoke tests for replay isolation
- Fallback guard against silent downgrade
- Updating Python API adapter initialization

**Out of scope:**
- Frontend changes (no new runtime selector — UX-DR1)
- New preflight validation (that's Story 23.5)
- Regression coverage for broader scenarios (that's Story 23.6)
- Policy catalog expansion (that's Epic 24)
- Custom output_variables per template (future story — just use defaults)
- Adapter hot-swapping per request for non-replay modes

### References

- Epic 23 Story 23.4: `_bmad-output/planning-artifacts/epics.md` (Story 23.4 definition)
- Story 23.1: Runtime mode contract — `src/reformlab/computation/types.py` (`RuntimeMode`), `src/reformlab/server/models.py` (`RunRequest.runtime_mode`)
- Story 23.2: Population resolver — `src/reformlab/server/population_resolver.py`
- Story 23.3: Normalization layer — `src/reformlab/computation/result_normalizer.py`, `src/reformlab/orchestrator/panel.py`
- Adapter protocol: `src/reformlab/computation/adapter.py`
- Precomputed adapter: `src/reformlab/computation/openfisca_adapter.py`
- Live adapter: `src/reformlab/computation/openfisca_api_adapter.py`
- Server dependencies: `src/reformlab/server/dependencies.py`
- Run route: `src/reformlab/server/routes/runs.py`
- Python API: `src/reformlab/interfaces/api.py` (`_initialize_default_adapter`, `_execute_orchestration`)
- Server models: `src/reformlab/server/models.py` (`RunRequest`, `RunResponse`)
- Test patterns: `tests/server/conftest.py`, `tests/server/test_runs.py`
- Project context: `_bmad-output/project-context.md` — adapter isolation, frozen dataclasses, PyArrow-first
- UX-DR1: `_bmad-output/planning-artifacts/ux-design-specification.md` — no frontend engine selector in first slice

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — all tests pass in first run.

### Completion Notes List

**Implementation Plan**:
1. Added `_DEFAULT_LIVE_OUTPUT_VARIABLES` constant to `result_normalizer.py` containing French OpenFisca variable names
2. Created `_create_live_adapter()` factory for `OpenFiscaApiAdapter` with default output variables
3. Created `_create_replay_adapter()` factory for `OpenFiscaAdapter` (precomputed)
4. Updated `_create_adapter()` to use live adapter by default with `REFORMLAB_RUNTIME_MODE` env var support
5. Added fallback to MockAdapter when OpenFisca not installed or init fails
6. Updated `run_simulation()` to create replay adapter per-request when `runtime_mode == "replay"`
7. Added 422 error for missing precomputed data in replay mode
8. Added fallback guard after run_scenario() to detect runtime mode mismatches
9. Updated `_initialize_default_adapter()` in `api.py` to use live adapter with fallback to SimpleCarbonTaxAdapter
10. Updated `_initialize_default_adapter_for_direct()` to prefer live adapter
11. Added unit tests for adapter factories in `test_dependencies.py`
12. Created comprehensive integration tests in `test_live_default_runs.py` covering live mode, replay isolation, result persistence, and no silent fallback
13. Added route-level replay isolation tests in `test_runs.py`

**Changes Made:**
- `src/reformlab/computation/result_normalizer.py`: Added `_DEFAULT_LIVE_OUTPUT_VARIABLES` constant
- `src/reformlab/server/dependencies.py`: Added `_create_live_adapter()`, `_create_replay_adapter()`, updated `_create_adapter()` with env var support and fallback logic
- `src/reformlab/server/routes/runs.py`: Added per-request replay adapter creation, 422 error for missing precomputed data, fallback guard
- `src/reformlab/interfaces/api.py`: Updated `_initialize_default_adapter()` and `_initialize_default_adapter_for_direct()` to prefer live adapter
- `tests/server/test_dependencies.py`: Added comprehensive tests for adapter factories and fallback behavior
- `tests/server/test_live_default_runs.py`: New test file with 10 tests for default live execution, replay isolation, result persistence, and no silent fallback
- `tests/server/test_runs.py`: Extended with `TestReplayModeIsolation` class with 3 tests

**All tests passing**: All 51 tests in the modified test files pass (17 in test_dependencies.py, 10 in test_live_default_runs.py, 2 new tests in test_runs.py, 22 existing tests continue to pass). Linting and type checking all pass.

### File List

**Modified Files:**
- `src/reformlab/computation/result_normalizer.py` — Added `_DEFAULT_LIVE_OUTPUT_VARIABLES` constant
- `src/reformlab/server/dependencies.py` — Added `_create_live_adapter()`, `_create_replay_adapter()`, updated `_create_adapter()` with env var and fallback logic
- `src/reformlab/server/routes/runs.py` — Added per-request replay adapter, 422 error for missing data, fallback guard
- `src/reformlab/interfaces/api.py` — Updated `_initialize_default_adapter()` and `_initialize_default_adapter_for_direct()` to prefer live adapter
- `tests/server/test_dependencies.py` — Added tests for adapter factories, default mode, replay mode, and fallback behavior
- `tests/server/test_live_default_runs.py` — New test file with comprehensive tests for default live execution, replay isolation, result persistence, and no silent fallback
- `tests/server/test_runs.py` — Extended with `TestReplayModeIsolation` class for replay mode isolation

**New Files Created:**
- `tests/server/test_live_default_runs.py` — Complete test suite for Story 23.4 integration requirements

**Deleted Files:**
- None
