

# Story 17.7: Implement Persistent Result Storage and Retrieval

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a non-coding analyst,
I want simulation results (panel data, manifest, configuration) to persist across server restarts,
so that I can browse, export, and compare past simulation runs without having to re-run them.

## Context

Currently, the ReformLab server has a **two-layer result system** with a critical gap:

1. **ResultStore** (disk): Persists only lightweight `metadata.json` per run — config, timestamps, IDs, status.
2. **ResultCache** (in-memory LRU, max 10): Holds full `SimulationResult` objects including `PanelOutput` (PyArrow tables).

**The gap:** When the server restarts or the cache evicts a run, all panel data is lost. The GUI shows `data_available: false` and exports return 409. The analyst must re-run the simulation — unacceptable for a showcase product.

Story 17.7 closes this gap by **persisting panel data (Parquet) and manifest (JSON) to disk** alongside the existing metadata, and **loading them back on demand** when the cache doesn't have them.

### What Already Exists

- `ResultStore` at `src/reformlab/server/result_store.py` — saves/loads `metadata.json` under `~/.reformlab/results/{run_id}/`
- `ResultCache` at `src/reformlab/server/dependencies.py` — in-memory LRU with `store()`, `get()`, `delete()`
- `PanelOutput.to_parquet(path)` and `PanelOutput.to_csv(path)` — already implemented in `src/reformlab/orchestrator/panel.py`
- `RunManifest.to_json()` — canonical JSON serialization in `src/reformlab/governance/manifest.py`
- Routes in `src/reformlab/server/routes/results.py` — CRUD + export endpoints with store/cache two-step lookup
- Routes in `src/reformlab/server/routes/runs.py` — `POST /api/runs` with auto-save metadata in `finally` block
- Frontend `ResultDetailView` already shows `data_available` flag and disables exports when false
- 15 existing tests in `tests/server/test_results.py` covering metadata-only paths
- 30+ tests in `tests/server/test_exports_integration.py` covering export endpoints

### What Does NOT Exist Yet

- No panel Parquet file written to disk during run
- No manifest JSON file written to disk during run
- No loading of panel/manifest from disk when cache misses
- No `data_available: true` after server restart

## Acceptance Criteria

1. **AC-1: Panel data persisted on run completion** — Given a completed simulation, when results are stored, then the panel data table is written as a Parquet file to `~/.reformlab/results/{run_id}/panel.parquet` alongside the existing `metadata.json`. Failed runs (no panel_output) do NOT write a panel file. Persistence failures (I/O errors writing panel or manifest) must NOT propagate to the API response — the simulation result is returned to the client successfully regardless of whether disk persistence succeeds.

2. **AC-2: Manifest persisted on run completion** — Given a completed simulation with a manifest, when results are stored, then the run manifest is written as JSON to `~/.reformlab/results/{run_id}/manifest.json`.

3. **AC-3: Disk-backed result loading on cache miss** — Given stored results with panel and manifest on disk, when the result is requested and the in-memory cache does not contain it, then the panel is loaded from disk into a `PanelOutput`, wrapped in a `SimulationResult`, cached, and served with `data_available: true`. Endpoints that previously returned 409 (evicted) now return 200 with data.

4. **AC-4: Results survive server restart** — Given stored results, when the application restarts, then all previously stored results are listed with `data_available: true` (for completed runs with panel files) and all data operations (indicators, exports, comparison) work without re-running.

5. **AC-5: Listing includes data availability from disk** — Given stored results, when listed via `GET /api/results`, then `data_available` is `true` for any run that has a `panel.parquet` file on disk, regardless of cache state.

6. **AC-6: Delete removes all artifacts** — Given a stored result with panel and manifest files, when deleted via `DELETE /api/results/{run_id}`, then all files (metadata.json, panel.parquet, manifest.json) are removed. (Already works — `shutil.rmtree()` removes the entire directory.)

7. **AC-7: All tests pass** — New tests pass alongside existing 3100+ backend tests and 211+ frontend tests with zero regressions.

## Tasks / Subtasks

- [x] Task 1: Extend ResultStore with panel and manifest persistence (AC: 1, 2)
  - [x] 1.1: Add `save_panel(run_id, panel_output)` method to `ResultStore` — writes `panel.parquet` atomically (write to `.panel.parquet.tmp`, then `os.replace()`). Uses `PanelOutput.to_parquet()`.
  - [x] 1.2: Add `save_manifest(run_id, manifest_json)` method to `ResultStore` — writes `manifest.json` atomically. Accepts the JSON string from `RunManifest.to_json()`.
  - [x] 1.3: Add `has_panel(run_id)` method — returns `bool` indicating whether `panel.parquet` exists.
  - [x] 1.4: Add `load_panel(run_id)` method — reads `panel.parquet` via `pyarrow.parquet.read_table()`, returns `PanelOutput` with metadata from `panel_output.metadata` (stored in Parquet schema metadata). Raises `ResultNotFound` if file missing. Raises `ResultStoreError` if the file is corrupt or unreadable (PyArrow I/O error).
  - [x] 1.5: Add `load_manifest(run_id)` method — reads `manifest.json` as a string and calls `RunManifest.from_json()` to return a `RunManifest` instance. Raises `ResultNotFound` if file missing. Raises `ResultStoreError` if the file is unreadable or `RunManifest.from_json()` fails (e.g., corrupt JSON or schema mismatch).

- [x] Task 2: Persist panel and manifest during simulation run (AC: 1, 2)
  - [x] 2.1: In `runs.py` `run_simulation()`, after `cache.store(run_id, result)` succeeds and `result.panel_output` is not None, call `store.save_panel(run_id, result.panel_output)` and `store.save_manifest(run_id, result.manifest.to_json())`. Wrap in try/except like metadata save — failure must not mask run result.
  - [x] 2.2: Add `store` dependency to `run_simulation()` via `Depends(get_result_store)` (currently only accessed via `get_result_store()` in the finally block — refactor to use consistent DI pattern).

- [x] Task 3: Implement disk-backed loading on cache miss (AC: 3, 4)
  - [x] 3.1: Add `load_from_disk(run_id)` method to `ResultStore` — combines `load_panel()` and `load_manifest()` to reconstruct a minimal `SimulationResult` (with `panel_output` and manifest, `yearly_states={}`, `success=True`). Returns `None` if panel file doesn't exist. If `load_panel()` raises `ResultStoreError` (corrupt file), log a warning (`event=panel_load_corrupt`) and return `None` — treat corrupt disk artifacts the same as missing.
  - [x] 3.2: Add `get_or_load(run_id, store)` method to `ResultCache` — checks cache first; on miss, calls `store.load_from_disk(run_id)`, stores in cache, and returns the result. Returns `None` only if neither cache nor disk has the data.
  - [x] 3.3: Update `results.py` `_metadata_to_detail()` — replace `cache.get(meta.run_id)` with `cache.get_or_load(meta.run_id, store)` so detail view loads from disk on cache miss.
  - [x] 3.4: Update `results.py` `export_csv()` and `export_parquet()` — replace `cache.get(run_id)` with `cache.get_or_load(run_id, store)`. The 409 branch remains for runs that truly have no panel data (failed runs).
  - [x] 3.5: Update `indicators.py` `compute_indicator()` and `compute_comparison()` — replace `cache.get()` with `cache.get_or_load()`. Pass `store` dependency (already injected via `Depends`).
  - [x] 3.6: Update `exports.py` `_lookup_run()` — replace `cache.get()` with `cache.get_or_load()`.
  - [x] 3.7: Update `decisions.py` — replace `cache.get()` with `cache.get_or_load()`.
  - [x] 3.8: Update `indicators.py` `compare_portfolio_runs()` — replace `cache.get()` with `cache.get_or_load()`.

- [x] Task 4: Update listing to reflect disk availability (AC: 5)
  - [x] 4.1: Update `results.py` `list_results()` — for each result, compute `data_available` as `store.has_panel(meta.run_id) or (cache_result is not None and cache_result.panel_output is not None)` where `cache_result = cache.get(meta.run_id)`. This avoids loading every panel into memory just for listing, and correctly handles failed runs whose cache entry has `panel_output=None`.

- [x] Task 5: Write comprehensive tests (AC: 7)
  - [x] 5.1: Create `tests/server/test_result_store_persistence.py` — unit tests for new `ResultStore` methods:
    - `save_panel()` + `load_panel()` round-trip (Parquet content intact)
    - `save_manifest()` + `load_manifest()` round-trip (JSON content intact)
    - `has_panel()` returns `True`/`False` correctly
    - `load_from_disk()` returns `SimulationResult` with correct panel data
    - `load_panel()` raises `ResultNotFound` when file missing
    - `load_panel()` raises `ResultStoreError` when file is corrupt (write invalid bytes, then call `load_panel()`)
    - `load_from_disk()` returns `None` when `panel.parquet` is corrupt (does not propagate exception)
    - Atomic write safety (`.tmp` file cleaned up)
  - [x] 5.2: Create `tests/server/test_cache_disk_loading.py` — integration tests for disk-backed cache:
    - `get_or_load()` returns cached result when in cache
    - `get_or_load()` loads from disk when not in cache
    - `get_or_load()` returns `None` when neither cache nor disk has data
    - Disk-loaded result is subsequently cached (second call hits cache)
    - Result listing shows `data_available: true` for disk-backed runs
  - [x] 5.3: Add to `tests/server/test_results.py` or new file — API integration tests:
    - `GET /api/results/{run_id}` returns `data_available: true` for disk-backed run
    - `GET /api/results/{run_id}/export/csv` returns 200 for disk-backed run
    - `GET /api/results/{run_id}/export/parquet` returns 200 for disk-backed run
    - `POST /api/indicators/distributional` returns 200 for disk-backed run
    - `POST /api/comparison` returns 200 for disk-backed runs
    - `GET /api/results` listing shows `data_available: true` for runs with panel on disk
  - [x] 5.4: Regression tests — existing tests in `test_results.py`, `test_indicators_integration.py`, `test_exports_integration.py`, `test_runs.py` must continue to pass unchanged.

- [x] Task 6: Run quality checks (AC: 7)
  - [x] 6.1: `uv run ruff check src/ tests/` — 0 errors
  - [x] 6.2: `uv run mypy src/` — 0 errors
  - [x] 6.3: `uv run pytest tests/` — all pass (3143 passed, 1 skipped)
  - [x] 6.4: `npm run typecheck && npm run lint` — 0 errors (4 pre-existing fast-refresh warnings)
  - [x] 6.5: `npm test` — 211 passed

#### Review Follow-ups (AI)
- [ ] [AI-Review] MEDIUM: Add integration tests for `POST /api/runs` panel+manifest persistence path — verify panel.parquet written on success and that save failures don't alter API response (`tests/server/test_runs.py`)

## Dev Notes

### Architecture — Disk Layout After This Story

```
~/.reformlab/results/{run_id}/
├── metadata.json       ← Already exists (Story 17.3)
├── panel.parquet       ← NEW: Full panel data (PyArrow Table)
└── manifest.json       ← NEW: Run manifest (canonical JSON)
```

### ResultStore — New Methods

Add these to `src/reformlab/server/result_store.py`:

```python
def save_panel(self, run_id: str, panel_output: PanelOutput) -> None:
    """Atomically persist panel data as Parquet.

    Writes to a temp file then renames — prevents a crash mid-write from
    leaving a corrupt panel.parquet that would be silently served on reload.
    """
    run_dir = self._resolve_safe(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    target = run_dir / "panel.parquet"
    tmp = run_dir / ".panel.parquet.tmp"
    panel_output.to_parquet(tmp)
    os.replace(tmp, target)

def save_manifest(self, run_id: str, manifest_json: str) -> None:
    """Atomically persist manifest as JSON."""
    run_dir = self._resolve_safe(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    target = run_dir / "manifest.json"
    tmp = run_dir / ".manifest.json.tmp"
    tmp.write_text(manifest_json, encoding="utf-8")
    os.replace(tmp, target)

def has_panel(self, run_id: str) -> bool:
    """Check if panel.parquet exists for a run."""
    run_dir = self._resolve_safe(run_id)
    return (run_dir / "panel.parquet").exists()

def load_panel(self, run_id: str) -> PanelOutput:
    """Load panel data from disk. Raises ResultNotFound if missing."""
    ...

def load_manifest(self, run_id: str) -> RunManifest:
    """Load manifest from disk as RunManifest. Raises ResultNotFound if missing, ResultStoreError if corrupt."""
    ...

def load_from_disk(self, run_id: str) -> SimulationResult | None:
    """Reconstruct a SimulationResult from disk artifacts. Returns None if no panel."""
    ...
```

### ResultCache — New Method

Add to `src/reformlab/server/dependencies.py`:

```python
def get_or_load(self, run_id: str, store: ResultStore) -> SimulationResult | None:
    """Check cache first, then load from disk if available."""
    result = self.get(run_id)
    if result is not None:
        return result
    # Try disk
    disk_result = store.load_from_disk(run_id)
    if disk_result is not None:
        logger.info("event=cache_miss_disk_load run_id=%s", run_id)
        self.store(run_id, disk_result)
    else:
        logger.debug("event=disk_load_miss run_id=%s", run_id)
    return disk_result
```

### Panel Metadata Preservation

`PanelOutput.metadata` (a `dict[str, Any]`) contains runtime metadata like `start_year`, `end_year`, `seed`, `step_pipeline`, decision domain alternatives, etc. This metadata must survive the Parquet round-trip.

**Strategy**: Store `PanelOutput.metadata` as a JSON-encoded string in the Parquet schema metadata under key `reformlab_panel_metadata`. On load, parse it back.

```python
# In save_panel:
schema_metadata = {"reformlab_panel_metadata": json.dumps(panel_output.metadata)}
panel_output.to_parquet(tmp, schema_metadata=schema_metadata)

# In load_panel:
table = pq.read_table(panel_path)
raw_meta = table.schema.metadata or {}
panel_meta_bytes = raw_meta.get(b"reformlab_panel_metadata", b"{}")
panel_metadata = json.loads(panel_meta_bytes)
return PanelOutput(table=table, metadata=panel_metadata)
```

### SimulationResult Reconstruction from Disk

When loading from disk, we can't reconstruct the full `SimulationResult` (which has `yearly_states`, etc.). We create a **minimal reconstruction**:

```python
def load_from_disk(self, run_id: str) -> SimulationResult | None:
    if not self.has_panel(run_id):
        return None
    panel = self.load_panel(run_id)

    # Load manifest if available, otherwise fall back to a minimal mock manifest
    try:
        manifest = self.load_manifest(run_id)
    except (ResultNotFound, ResultStoreError):
        manifest = _make_minimal_manifest(metadata)  # fallback for pre-17.7 runs or corrupt manifest

    metadata = self.get_metadata(run_id)

    return SimulationResult(
        success=True,
        scenario_id=metadata.scenario_id,
        yearly_states={},  # Not persisted — empty for disk-loaded results
        panel_output=panel,
        manifest=manifest,
        metadata={},
    )
```

**CRITICAL**: `SimulationResult` is a frozen dataclass. The constructor signature is:
```python
SimulationResult(success, scenario_id, yearly_states, panel_output, manifest, metadata)
```

The `manifest` field expects a `RunManifest` instance. `load_manifest()` returns a `RunManifest` directly via `RunManifest.from_json()` (class method at `manifest.py:372`). For old runs (pre-17.7) without `manifest.json`, or if the file is corrupt, `load_from_disk()` falls back to `_make_minimal_manifest(metadata)` — a module-level helper that constructs a minimal `RunManifest` from the `ResultMetadata` fields. Define this helper alongside `load_from_disk`.

### runs.py — Saving Panel and Manifest

In `src/reformlab/server/routes/runs.py`, the `finally` block already saves metadata. Add panel+manifest saving in the success path:

```python
try:
    result = run_scenario(run_config, adapter=adapter)
    cache.store(run_id, result)
    status = "completed" if result.success else "failed"
    row_count = result.panel_output.table.num_rows if result.panel_output else 0

    # NEW: Persist panel and manifest to disk
    if result.panel_output is not None:
        try:
            store.save_panel(run_id, result.panel_output)
        except Exception:
            logger.exception("event=panel_save_failed run_id=%s", run_id)
    try:
        store.save_manifest(run_id, result.manifest.to_json())
    except Exception:
        logger.exception("event=manifest_save_failed run_id=%s", run_id)
finally:
    # ... existing metadata save ...
```

**CRITICAL**: Panel/manifest save failures must NOT propagate or mask the run result. Wrap each in its own try/except, same pattern as metadata save.

### Route Updates — get_or_load Pattern

All routes that currently do `cache.get(run_id)` and check for `None` need updating to `cache.get_or_load(run_id, store)`. The 409 branch still triggers when a run has metadata but NO panel on disk (e.g., failed runs, or runs from before this story).

**Files to update:**
- `src/reformlab/server/routes/results.py` — `_metadata_to_detail()`, `export_csv()`, `export_parquet()`, `list_results()`
- `src/reformlab/server/routes/indicators.py` — `compute_indicator()`, `compute_comparison()`, `compare_portfolio_runs()`
- `src/reformlab/server/routes/exports.py` — `_lookup_run()`
- `src/reformlab/server/routes/decisions.py` — wherever `cache.get()` is used

**Pattern:**
```python
# BEFORE:
result = cache.get(body.run_id)
if result is None or result.panel_output is None:
    raise HTTPException(status_code=409, ...)

# AFTER:
result = cache.get_or_load(body.run_id, store)
if result is None or result.panel_output is None:
    raise HTTPException(status_code=409, ...)
```

### Import Guards

`ResultStore` methods that reference `PanelOutput` and `SimulationResult` must use `TYPE_CHECKING` guards to avoid circular imports:

```python
if TYPE_CHECKING:
    from reformlab.interfaces.api import SimulationResult
    from reformlab.orchestrator.panel import PanelOutput
```

Runtime imports go inside method bodies:
```python
def load_panel(self, run_id: str) -> PanelOutput:
    from reformlab.orchestrator.panel import PanelOutput
    import pyarrow.parquet as pq
    ...
```

### Frontend — No Changes Required

The frontend already:
- Uses `data_available` flag to gate exports and indicators
- Shows "Re-run the simulation" message when `data_available: false`
- Calls `GET /api/results` on startup to populate the results list

After this story, `data_available` will be `true` after restart, so the existing UI works correctly. No frontend changes needed.

### Files to Modify

```
src/reformlab/server/result_store.py         ← Add save_panel, save_manifest, has_panel, load_panel, load_manifest, load_from_disk
src/reformlab/server/dependencies.py         ← Add get_or_load() to ResultCache
src/reformlab/server/routes/runs.py          ← Add panel+manifest persistence in run_simulation()
src/reformlab/server/routes/results.py       ← Update to use get_or_load(), update list_results()
src/reformlab/server/routes/indicators.py    ← Update to use get_or_load()
src/reformlab/server/routes/exports.py       ← Update to use get_or_load()
src/reformlab/server/routes/decisions.py     ← Update to use get_or_load()
```

### New Test Files

```
tests/server/test_result_store_persistence.py  ← ~200 lines, unit tests for new ResultStore methods
tests/server/test_cache_disk_loading.py        ← ~200 lines, integration tests for disk-backed cache
```

### Test Patterns (MUST FOLLOW)

**Fixture pattern (from existing `test_results.py`):**
```python
@pytest.fixture()
def tmp_store(tmp_path: Path) -> ResultStore:
    return ResultStore(base_dir=tmp_path)

@pytest.fixture()
def empty_cache() -> ResultCache:
    return ResultCache(max_size=20)
```

**Seeding store + cache (from `test_exports_integration.py`):**
```python
def _seed(store, cache, run_id, panel=None, in_cache=True):
    store.save_metadata(run_id, _make_metadata(run_id))
    if in_cache:
        cache.store(run_id, _make_sim_result(panel))
```

**For disk-backed tests, seed store + save panel to disk but do NOT put in cache:**
```python
def _seed_disk_only(store, run_id, panel=None):
    """Save metadata and panel to disk, but NOT in cache."""
    p = panel or _make_panel()
    store.save_metadata(run_id, _make_metadata(run_id))
    store.save_panel(run_id, p)
    store.save_manifest(run_id, '{"manifest_id": "test"}')
```

**Auth + client pattern (from test files):**
```python
@pytest.fixture()
def client_with_deps(tmp_store, empty_cache):
    from reformlab.server.app import create_app
    app = create_app()
    app.dependency_overrides[get_result_store] = lambda: tmp_store
    app.dependency_overrides[get_result_cache] = lambda: empty_cache
    return TestClient(app)
```

### Anti-Patterns to Avoid

| Issue | Prevention |
|---|---|
| Loading all panels into memory on `list_results()` | Use `has_panel()` (filesystem check only) for listing — do NOT call `load_panel()` |
| Circular import between `result_store.py` and `api.py` | Use `TYPE_CHECKING` guard for type hints; runtime imports inside method bodies |
| Breaking existing tests that mock `cache.get()` | `get_or_load()` calls `cache.get()` first — tests that seed the cache still work |
| Panel save failure masking run result | Wrap each save in its own try/except, same as metadata save |
| Writing panel for failed runs (no panel_output) | Guard: `if result.panel_output is not None` before calling `save_panel()` |
| Storing panel metadata loss through Parquet round-trip | Encode `PanelOutput.metadata` as JSON string in Parquet schema metadata |
| `get_or_load` causing LRU eviction storm on listing | Only call `get_or_load()` for detail/export/indicator requests — listing uses `has_panel()` |
| Importing `ResultStore` at top level in `dependencies.py` for `get_or_load` | Pass `store` as parameter to `get_or_load()` rather than importing directly |
| Unhandled `ResultStoreError` (corrupt Parquet/JSON) propagating as 500 | Catch `ResultStoreError` in `load_from_disk()` — log `event=panel_load_corrupt` warning, return `None` |

### Existing Tests to NOT Break

Current test counts (must all pass after changes):
- `tests/server/test_results.py` — 15 tests
- `tests/server/test_result_store.py` — unit tests for metadata operations
- `tests/server/test_exports_integration.py` — 15 tests
- `tests/server/test_indicators_integration.py` — 17 tests
- `tests/server/test_runs.py` — 9 tests
- `tests/server/test_comparison_portfolios.py` — 30+ tests
- `tests/server/test_decisions.py` — 21 tests

All existing tests that seed the `ResultCache` directly will continue to work because `get_or_load()` checks cache first.

### Cross-Story Dependencies

| Story | Relationship |
|---|---|
| Story 17.3 | Created ResultStore, metadata persistence, results routes — this story extends it |
| Story 17.6 | Standardized error format and store/cache lookup — this story builds on that pattern |
| Story 17.8 | E2E GUI workflow tests — will use persistent results validated here |
| Epic 16 | Replication package export — `SimulationResult.export_replication_package()` already handles full serialization; this story brings similar persistence to the server layer |

### Scope Boundaries

**What this story does:**
- Persists panel data (Parquet) and manifest (JSON) to disk during runs
- Loads panel/manifest from disk when cache misses
- Updates all routes to use disk-backed loading
- Ensures `data_available: true` after server restart for completed runs

**What this story does NOT do:**
- Persist `yearly_states` (too complex, not needed for GUI operations)
- Add new API endpoints (all exist)
- Modify frontend code (existing UI handles `data_available` correctly)
- Add Parquet compression options (default compression is fine)
- Migrate old runs (runs from before this story will have `data_available: false` — acceptable)

### References

- [Source: src/reformlab/server/result_store.py] — ResultStore, ResultMetadata, ResultNotFound, atomic write pattern
- [Source: src/reformlab/server/dependencies.py] — ResultCache (LRU), get_result_store, get_result_cache
- [Source: src/reformlab/server/routes/results.py] — Result CRUD + export endpoints, _metadata_to_detail()
- [Source: src/reformlab/server/routes/runs.py] — Simulation execution, metadata auto-save in finally block
- [Source: src/reformlab/orchestrator/panel.py] — PanelOutput, to_parquet(), to_csv(), metadata structure
- [Source: src/reformlab/governance/manifest.py] — RunManifest, to_json(), from_json(), integrity hashing
- [Source: src/reformlab/interfaces/api.py] — SimulationResult frozen dataclass, export methods
- [Source: src/reformlab/server/models.py:371-413] — ResultListItem, ResultDetailResponse Pydantic models
- [Source: src/reformlab/server/routes/indicators.py] — Indicator endpoints with store/cache lookup
- [Source: src/reformlab/server/routes/exports.py] — Export endpoints with _lookup_run() helper
- [Source: tests/server/test_results.py] — Existing result tests (15 tests)
- [Source: tests/server/test_exports_integration.py] — Export tests with store/cache seeding patterns
- [Source: tests/server/test_indicators_integration.py] — Indicator tests with _make_panel(), _make_sim_result()
- [Source: docs/epics.md#Story 17.7 (BKL-1707)] — Original acceptance criteria
- [Source: docs/project-context.md] — Coding conventions, frozen dataclasses, PyArrow canonical type

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — implementation was straightforward with no blocking issues.

### Completion Notes List

- AC-1/AC-2: Panel and manifest written atomically (`.tmp` → rename) in `runs.py` `finally` block, guarded by `if result.panel_output is not None`. Each save wrapped in independent `try/except` to prevent masking run result.
- AC-3/AC-4: `ResultCache.get_or_load()` checks cache first, then calls `ResultStore.load_from_disk()` on miss. All 7 routes updated (results, exports, indicators×4, decisions).
- AC-5: `list_results()` uses `store.has_panel()` (filesystem check only — no panel loaded into memory) OR cache hit with non-None panel_output.
- AC-6: Already satisfied by `shutil.rmtree()` which removes the entire run directory including panel.parquet and manifest.json.
- `PanelOutput.metadata` preserved through Parquet round-trip via Parquet schema metadata key `reformlab_panel_metadata` (JSON-encoded).
- Missing/corrupt `manifest.json` handled gracefully via `_make_minimal_manifest()` fallback — disk-loaded results always have a valid `RunManifest` instance.
- Corrupt `panel.parquet` handled in `load_from_disk()` — catches `ResultStoreError`, logs `event=panel_load_corrupt`, returns `None`.
- mypy type annotation fix: `schema_metadata: dict[str, str | bytes]` instead of inferred `dict[str, str]`.
- 39 new tests added (24 unit + 15 integration); 3143 total passing; 0 regressions.
- Code review synthesis fixes (2026-03-08): (1) `runs.py` — `store` now injected via `Depends(get_result_store)` instead of direct call; (2) `exports.py` `_lookup_run()` — added `ResultStoreError` → 400 handler for invalid run_ids; (3) `result_store.py` `load_from_disk()` — `success` now derived from `metadata.status == "completed"` instead of hardcoded `True`; (4) `result_store.py` `save_panel/save_manifest` — `.tmp` files cleaned up on write failure via try/except+unlink; (5) `result_store.py` `load_panel()` — corrupt Parquet metadata now logs warning instead of silently coercing; (6) `dependencies.py` `ResultCache.store()` — LRU eviction skipped when run_id already in cache. 3143 tests pass; ruff+mypy clean.

### File List

**Modified files:**
- `src/reformlab/server/result_store.py`
- `src/reformlab/server/dependencies.py`
- `src/reformlab/server/routes/runs.py`
- `src/reformlab/server/routes/results.py`
- `src/reformlab/server/routes/indicators.py`
- `src/reformlab/server/routes/exports.py`
- `src/reformlab/server/routes/decisions.py`

**New test files:**
- `tests/server/test_result_store_persistence.py`
- `tests/server/test_cache_disk_loading.py`

## Senior Developer Review (AI)

### Review: 2026-03-08
- **Reviewer:** AI Code Review Synthesis
- **Evidence Score:** 8.8 (Reviewer A) / 2.9 (Reviewer B) → weighted consensus → Changes Requested
- **Issues Found:** 7 verified (1 false positive dismissed)
- **Issues Fixed:** 6
- **Action Items Created:** 1
