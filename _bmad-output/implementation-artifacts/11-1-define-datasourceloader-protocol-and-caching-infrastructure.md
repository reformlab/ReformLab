# Story 11.1: Define DataSourceLoader protocol and caching infrastructure

Status: dev-complete

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform developer building institutional data source loaders,
I want a `DataSourceLoader` protocol and disk-based caching infrastructure with offline-first semantics,
so that all subsequent loader implementations (INSEE, Eurostat, ADEME, SDES) share a consistent contract, cache downloaded data locally, and work offline after first download.

## Acceptance Criteria

1. Given the `DataSourceLoader` protocol, when a new loader is implemented, then it must provide `download()`, `status()`, and `schema()` methods.
2. Given a dataset downloaded for the first time, when cached, then the cache stores a schema-validated Parquet file with SHA-256 hash in `~/.reformlab/cache/sources/{provider}/{dataset_id}/`.
3. Given a previously cached dataset, when the loader is called again, then the cache is used without network access.
4. Given a network failure with an existing cache, when the loader is called, then the stale cache is used with a governance warning logged.
5. Given `REFORMLAB_OFFLINE=1` environment variable, when a loader is called and cache misses, then it fails explicitly without attempting network access.
6. Given the cache, when `status()` is called, then it returns `CacheStatus` with cached flag, path, download timestamp, hash, and staleness indicator.

## Tasks / Subtasks

- [x] Task 1: Create population subsystem package scaffold (AC: all — foundational)
  - [x] 1.1 Create `src/reformlab/population/__init__.py` with module docstring and public API exports
  - [x] 1.2 Create `src/reformlab/population/loaders/__init__.py` with public API exports
  - [x] 1.3 Create `src/reformlab/population/loaders/errors.py` with subsystem-specific exceptions
  - [x] 1.4 Create `tests/population/__init__.py` and `tests/population/conftest.py`
  - [x] 1.5 Create `tests/population/loaders/__init__.py` and `tests/population/loaders/conftest.py`

- [x] Task 2: Define `SourceConfig` frozen dataclass (AC: #1, #2, #3)
  - [x] 2.1 Define `SourceConfig` in `src/reformlab/population/loaders/base.py` as `@dataclass(frozen=True)` with fields: `provider: str`, `dataset_id: str`, `url: str`, `params: dict[str, str]` (default empty), `description: str` (default empty)
  - [x] 2.2 Add `__post_init__` validation: `provider` and `dataset_id` must be non-empty strings; normalize `params` via `object.__setattr__` for deep-copy protection

- [x] Task 3: Define `CacheStatus` frozen dataclass (AC: #6)
  - [x] 3.1 Define `CacheStatus` in `src/reformlab/population/loaders/base.py` as `@dataclass(frozen=True)` with fields: `cached: bool`, `path: Path | None`, `downloaded_at: datetime | None`, `hash: str | None`, `stale: bool`
  - [x] 3.2 Ensure `path` uses `Path` from `pathlib`, `downloaded_at` uses `datetime` from `datetime`

- [x] Task 4: Define `DataSourceLoader` protocol (AC: #1)
  - [x] 4.1 Define `DataSourceLoader` in `src/reformlab/population/loaders/base.py` as `@runtime_checkable class DataSourceLoader(Protocol)` with three methods:
    - `def download(self, config: SourceConfig) -> pa.Table: ...`
    - `def status(self, config: SourceConfig) -> CacheStatus: ...`
    - `def schema(self) -> pa.Schema: ...`
  - [x] 4.2 Add comprehensive docstring explaining structural typing, protocol purpose, and downstream loader expectations
  - [x] 4.3 Verify `isinstance()` check works at runtime (unit test)

- [x] Task 5: Implement `SourceCache` — disk-based caching infrastructure (AC: #2, #3, #4, #5)
  - [x] 5.1 Create `src/reformlab/population/loaders/cache.py` with `SourceCache` class
  - [x] 5.2 Constructor takes `cache_root: Path | None = None` (defaults to `~/.reformlab/cache/sources`)
  - [x] 5.3 Implement `cache_key(config: SourceConfig) -> str` — deterministic SHA-256 of `url + sorted(params) + date_prefix` (see Dev Notes for hash design)
  - [x] 5.4 Implement `cache_path(config: SourceConfig) -> Path` — returns `{cache_root}/{provider}/{dataset_id}/{cache_key}.parquet`
  - [x] 5.5 Implement `metadata_path(config: SourceConfig) -> Path` — returns `{cache_path}.meta.json` (stores download timestamp, hash, URL, params)
  - [x] 5.6 Implement `get(config: SourceConfig) -> tuple[pa.Table, CacheStatus] | None` — returns cached table + status if cache hit, `None` if miss
  - [x] 5.7 Implement `put(config: SourceConfig, table: pa.Table) -> CacheStatus` — write schema-validated Parquet + metadata JSON, compute SHA-256 of written file, return `CacheStatus`
  - [x] 5.8 Implement `status(config: SourceConfig) -> CacheStatus` — read metadata without loading table
  - [x] 5.9 Implement `is_offline() -> bool` — check `REFORMLAB_OFFLINE` env var (truthy: `"1"`, `"true"`, `"yes"`)
  - [x] 5.10 Ensure `cache_root` directory is created on first write (not on init — no side effects in constructor)
  - [x] 5.11 Use `pyarrow.parquet.write_table()` for cache writes and `pyarrow.parquet.read_table()` for reads

- [x] Task 6: Implement `CachedLoader` — base class wrapping protocol + cache (AC: #2, #3, #4, #5)
  - [x] 6.1 Create `CachedLoader` in `src/reformlab/population/loaders/base.py` (concrete class, not protocol) that wraps cache logic around the download lifecycle:
    - Constructor: `cache: SourceCache`, `logger: logging.Logger`
    - Abstract-ish method: `_fetch(config: SourceConfig) -> pa.Table` (subclasses override to do real HTTP download)
    - `download(config: SourceConfig) -> pa.Table` — orchestrates: check cache → if miss, check offline → fetch → validate schema → cache → return
    - `status(config: SourceConfig) -> CacheStatus` — delegates to `cache.status()`
    - `schema(self) -> pa.Schema` — abstract, subclasses must implement
  - [x] 6.2 In `download()`: on network failure (any `OSError`, `urllib.error.URLError`) with existing cache, use stale cache and log governance warning via `logging.getLogger(__name__).warning()`
  - [x] 6.3 In `download()`: when `REFORMLAB_OFFLINE=1` and cache miss, raise `DataSourceOfflineError` with clear message
  - [x] 6.4 In `download()`: when cache hit (not stale), return cached table directly without network
  - [x] 6.5 Governance warning format: `"WARNING: Using stale cache for %s/%s — network unavailable. Downloaded at %s, hash %s"` (provider, dataset_id, timestamp, hash)

- [x] Task 7: Define subsystem-specific exceptions (AC: #4, #5)
  - [x] 7.1 In `src/reformlab/population/loaders/errors.py`, define:
    - `DataSourceError(Exception)` — base exception with `*, summary: str, reason: str, fix: str` kwargs following project pattern
    - `DataSourceOfflineError(DataSourceError)` — raised when offline mode prevents download
    - `DataSourceDownloadError(DataSourceError)` — raised on network/download failures (without cache fallback)
    - `DataSourceValidationError(DataSourceError)` — raised when downloaded data fails schema validation
  - [x] 7.2 Message format: `f"{summary} - {reason} - {fix}"` (matches `IngestionError` pattern)

- [x] Task 8: Add `network` pytest marker to pyproject.toml (AC: CI fixture pattern)
  - [x] 8.1 Add `"network: marks tests requiring real network access to institutional APIs (opt-in with '-m network')"` to `[tool.pytest.ini_options].markers`
  - [x] 8.2 Update `addopts` to exclude `network`: `"-m 'not integration and not scale and not network'"`

- [x] Task 9: Write comprehensive tests (AC: all)
  - [x] 9.1 `tests/population/loaders/test_base.py` — Protocol compliance: verify `isinstance()` check, verify minimal conforming class satisfies protocol
  - [x] 9.2 `tests/population/loaders/test_base.py` — `SourceConfig`: construction, validation (empty provider/dataset_id rejected), frozen immutability, params deep-copy
  - [x] 9.3 `tests/population/loaders/test_base.py` — `CacheStatus`: construction with all fields, `None` defaults
  - [x] 9.4 `tests/population/loaders/test_cache.py` — `SourceCache.put()` + `get()` round-trip: write table, read back, verify content identical
  - [x] 9.5 `tests/population/loaders/test_cache.py` — Cache miss returns `None`
  - [x] 9.6 `tests/population/loaders/test_cache.py` — `status()` returns correct `CacheStatus` for cached and uncached datasets
  - [x] 9.7 `tests/population/loaders/test_cache.py` — Cache directory structure: verify `{provider}/{dataset_id}/{hash}.parquet` layout
  - [x] 9.8 `tests/population/loaders/test_cache.py` — Metadata JSON contains download timestamp, hash, URL, params
  - [x] 9.9 `tests/population/loaders/test_cache.py` — `is_offline()` respects `REFORMLAB_OFFLINE` env var (use `monkeypatch.setenv`)
  - [x] 9.10 `tests/population/loaders/test_cached_loader.py` — Cache hit: `_fetch()` is NOT called, cached table returned
  - [x] 9.11 `tests/population/loaders/test_cached_loader.py` — Cache miss: `_fetch()` IS called, result cached, table returned
  - [x] 9.12 `tests/population/loaders/test_cached_loader.py` — Network failure + existing cache: stale cache used, warning logged
  - [x] 9.13 `tests/population/loaders/test_cached_loader.py` — Network failure + no cache: `DataSourceDownloadError` raised
  - [x] 9.14 `tests/population/loaders/test_cached_loader.py` — Offline mode + cache hit: cached table returned
  - [x] 9.15 `tests/population/loaders/test_cached_loader.py` — Offline mode + cache miss: `DataSourceOfflineError` raised
  - [x] 9.16 `tests/population/loaders/test_cached_loader.py` — Schema validation: downloaded table that fails schema check raises `DataSourceValidationError`
  - [x] 9.17 `tests/population/loaders/test_errors.py` — Exception message format follows `[summary] - [reason] - [fix]` pattern

- [x] Task 10: Run full test suite and lint (AC: all)
  - [x] 10.1 `uv run pytest tests/` — all tests pass (52 new, 1589 total; 1 pre-existing memory assertion failure unrelated)
  - [x] 10.2 `uv run ruff check src/ tests/` — no lint errors
  - [x] 10.3 `uv run mypy src/reformlab/population/` — no mypy errors (strict mode, 5 source files)

## Dev Notes

### Architecture Context: First Phase 2 Story

This is the **first story of Phase 2** and the first story in EPIC-11 (Realistic Population Generation Library). It creates a new subsystem (`population/`) that does not yet exist in the codebase. All subsequent EPIC-11 stories (11.2–11.8) depend on the protocol and caching infrastructure delivered here.

**Key architectural decision:** Phase 2 introduces the project's first optional network dependencies. Phase 1 had zero network calls at runtime. The caching infrastructure must ensure offline-first operation — network access is entirely opt-in and degradable.

### Protocol Design: Follow `ComputationAdapter` Pattern Exactly

The existing `ComputationAdapter` protocol in `src/reformlab/computation/adapter.py` is the reference implementation:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class DataSourceLoader(Protocol):
    """Interface for institutional data source loaders.

    Structural (duck-typed) protocol: any class that implements download(),
    status(), and schema() with correct signatures satisfies the contract.
    No explicit inheritance required.

    Each loader handles one institutional data source (e.g., INSEE, Eurostat).
    The loader downloads, schema-validates, caches, and returns pa.Table data.
    """

    def download(self, config: SourceConfig) -> pa.Table: ...
    def status(self, config: SourceConfig) -> CacheStatus: ...
    def schema(self) -> pa.Schema: ...
```

**Critical:** Use `@runtime_checkable` — same as `ComputationAdapter` and `OrchestratorStep`. This enables `isinstance(loader, DataSourceLoader)` checks at registration time.

### Cache Key Design: Hash-Based Freshness

The architecture specifies "Hash-based freshness (SHA256 of URL + params + date)." The `date` component should be a date prefix (e.g., `"2026-03"`) — not the full timestamp — to provide monthly freshness windows. This means:

```python
import hashlib

def cache_key(config: SourceConfig) -> str:
    """Deterministic cache key from source config + date prefix."""
    # Monthly granularity: data that's >1 month old is considered stale
    date_prefix = datetime.now(UTC).strftime("%Y-%m")
    raw = f"{config.url}|{'|'.join(f'{k}={v}' for k, v in sorted(config.params.items()))}|{date_prefix}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
```

**Stale detection:** If a cache file exists but its metadata `date_prefix` differs from the current month's prefix, the cache is considered "stale but usable." The `CacheStatus.stale` field reflects this.

### Cache Directory Layout

```
~/.reformlab/cache/
  sources/
    insee/
      household_income/
        a1b2c3d4e5f6g7h8.parquet       ← cached data
        a1b2c3d4e5f6g7h8.parquet.meta.json  ← metadata
      household_composition/
        ...
    eurostat/
      ...
    ademe/
      ...
    sdes/
      ...
```

**Metadata JSON schema:**
```json
{
  "url": "https://example.com/dataset",
  "params": {"year": "2024"},
  "downloaded_at": "2026-03-03T10:30:00+00:00",
  "content_hash": "sha256hexstring...",
  "date_prefix": "2026-03",
  "provider": "insee",
  "dataset_id": "household_income"
}
```

### No New Dependencies Required

The caching infrastructure uses only stdlib and existing dependencies:
- **`pathlib.Path`** — directory management, file paths
- **`hashlib`** — SHA-256 for cache keys and content hashes
- **`json`** — metadata files
- **`datetime`** — timestamps
- **`os.environ`** — `REFORMLAB_OFFLINE` check
- **`pyarrow.parquet`** — read/write cached Parquet files
- **`logging`** — governance warnings

No HTTP client library is needed in this story — `CachedLoader._fetch()` is an abstract method that concrete loaders (Stories 11.2, 11.3) will implement. Those stories may introduce `urllib.request` (stdlib) or a new dependency.

### `CachedLoader` — Not a Protocol, Not an ABC

The codebase rule is "Protocols, not ABCs." However, `CachedLoader` is neither — it's a **concrete base class** that provides shared cache-orchestration logic. Concrete loaders (INSEELoader, EurostatLoader) will subclass it and override `_fetch()` and `schema()`. This is acceptable because:

1. `DataSourceLoader` remains the Protocol (the interface contract)
2. `CachedLoader` is an implementation convenience, not an interface
3. Concrete loaders satisfy `DataSourceLoader` protocol via duck typing (they have `download()`, `status()`, `schema()`)

Pattern: `CachedLoader` is to `DataSourceLoader` what `OpenFiscaAdapter` is to `ComputationAdapter` — a concrete implementation that satisfies the protocol.

### Frozen Dataclass Conventions

Follow existing patterns exactly:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

@dataclass(frozen=True)
class SourceConfig:
    """Immutable configuration for a data source download."""
    provider: str
    dataset_id: str
    url: str
    params: dict[str, str] = field(default_factory=dict)
    description: str = ""

    def __post_init__(self) -> None:
        if not self.provider.strip():
            raise ValueError("provider must be a non-empty string")
        if not self.dataset_id.strip():
            raise ValueError("dataset_id must be a non-empty string")
        # Deep-copy mutable container (frozen dataclass pattern)
        object.__setattr__(self, "params", dict(self.params))
```

### Exception Hierarchy

Follow the `[summary] - [reason] - [fix]` pattern from `IngestionError`:

```python
class DataSourceError(Exception):
    """Base exception for data source operations."""
    def __init__(self, *, summary: str, reason: str, fix: str) -> None:
        self.summary = summary
        self.reason = reason
        self.fix = fix
        super().__init__(f"{summary} - {reason} - {fix}")
```

### Governance Integration Point

When stale cache is used, the warning string should be compatible with the existing `capture_warnings(additional_warnings=...)` pattern in `governance/capture.py`. The loader logs via `logging.getLogger(__name__).warning()` at runtime, and downstream callers (PopulationPipeline in Story 11.6) will collect these warnings for manifest inclusion.

### `from __future__ import annotations` — Every File

Per project rules, every Python file starts with this import. No exceptions.

### Logging Convention

```python
import logging
logger = logging.getLogger(__name__)
# Structured key=value format:
logger.warning("event=stale_cache_used provider=%s dataset_id=%s downloaded_at=%s hash=%s", ...)
```

### Test Structure

Mirror source layout per project rules:
```
tests/
  population/
    __init__.py
    conftest.py              ← shared fixtures (SourceConfig instances, tmp cache dirs)
    loaders/
      __init__.py
      conftest.py            ← loader-specific fixtures (mock tables, mock CachedLoader)
      test_base.py           ← Protocol, SourceConfig, CacheStatus tests
      test_cache.py          ← SourceCache tests (uses tmp_path)
      test_cached_loader.py  ← CachedLoader lifecycle tests (uses monkeypatch)
      test_errors.py         ← Exception tests
```

**Fixture patterns:**
- Use `tmp_path` for cache directories (no real `~/.reformlab` writes in tests)
- Use `monkeypatch.setenv("REFORMLAB_OFFLINE", "1")` for offline mode tests
- Build `pa.Table` fixtures inline (same as `tests/data/conftest.py`)
- Use class-based test grouping with Given/When/Then docstrings

**Mock CachedLoader for tests:**
```python
class MockCachedLoader(CachedLoader):
    """Test double that simulates network fetch."""
    def _fetch(self, config: SourceConfig) -> pa.Table:
        return self._mock_table  # set in test setup

    def schema(self) -> pa.Schema:
        return self._mock_schema
```

### mypy Configuration

Add a new override in `pyproject.toml` only if needed. Since the story only uses `pyarrow` (already has `ignore_missing_imports`) and stdlib, no new mypy overrides should be necessary.

### Project Structure Notes

- **New subsystem:** `src/reformlab/population/` — does not exist yet, must be created from scratch
- **Nested package:** `src/reformlab/population/loaders/` — follows architecture specification exactly
- **Alignment:** Directory structure matches `_bmad-output/planning-artifacts/architecture.md` "New Subsystem: Population Generation" section
- **No conflicts:** No existing code needs modification (except `pyproject.toml` for the `network` marker)
- **Build system:** No changes to `[tool.hatch.build.targets.wheel]` needed — `packages = ["src/reformlab"]` already covers all sub-packages

### Files Created (Expected)

**Source files:**
- `src/reformlab/population/__init__.py`
- `src/reformlab/population/loaders/__init__.py`
- `src/reformlab/population/loaders/base.py` — `DataSourceLoader` Protocol, `SourceConfig`, `CacheStatus`, `CachedLoader`
- `src/reformlab/population/loaders/cache.py` — `SourceCache` class
- `src/reformlab/population/loaders/errors.py` — `DataSourceError`, `DataSourceOfflineError`, `DataSourceDownloadError`, `DataSourceValidationError`

**Test files:**
- `tests/population/__init__.py`
- `tests/population/conftest.py`
- `tests/population/loaders/__init__.py`
- `tests/population/loaders/conftest.py`
- `tests/population/loaders/test_base.py`
- `tests/population/loaders/test_cache.py`
- `tests/population/loaders/test_cached_loader.py`
- `tests/population/loaders/test_errors.py`

**Modified files:**
- `pyproject.toml` — add `network` marker, update `addopts`

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#External-Data-Caching-&-Offline-Strategy] — Cache architecture, CacheStatus/DataSourceLoader protocol specifications, two-layer cache design
- [Source: _bmad-output/planning-artifacts/architecture.md#New-Subsystem-Population-Generation] — Directory structure, design principles
- [Source: _bmad-output/planning-artifacts/architecture.md#Populations-Phase-2-API] — Server-side `CacheStatusResponse` Pydantic model (future, not this story)
- [Source: _bmad-output/planning-artifacts/epics.md#BKL-1101] — Story definition and acceptance criteria
- [Source: _bmad-output/planning-artifacts/prd.md#FR36] — "Analyst can download and cache public datasets from institutional sources"
- [Source: _bmad-output/project-context.md#Python-Language-Rules] — Frozen dataclasses, Protocols, `from __future__ import annotations`
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules] — Subsystem-specific exceptions, structured logging
- [Source: src/reformlab/computation/adapter.py] — `ComputationAdapter` Protocol reference (pattern to follow)
- [Source: src/reformlab/orchestrator/step.py] — `OrchestratorStep` Protocol reference (pattern to follow)
- [Source: src/reformlab/data/pipeline.py] — `DataSourceMetadata`, `DatasetManifest`, `hash_file()` (existing data layer patterns)
- [Source: src/reformlab/governance/capture.py] — `capture_warnings(additional_warnings=...)` (governance warning integration point)
- [Source: src/reformlab/governance/hashing.py] — `hash_file()` with 64KB chunked SHA-256 (hashing pattern reference)
- [Source: src/reformlab/computation/ingestion.py] — `IngestionError` (exception message format reference)
- [Source: src/reformlab/server/dependencies.py] — `ResultCache` (LRU cache pattern reference)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

No issues encountered during implementation. All code passed on first attempt.

### Completion Notes List

- All 6 acceptance criteria satisfied and tested
- AC1: `DataSourceLoader` protocol is `@runtime_checkable` with `download()`, `status()`, `schema()` — tested with conforming and non-conforming classes
- AC2: `SourceCache.put()` writes schema-validated Parquet + metadata JSON with SHA-256 hash to `{provider}/{dataset_id}/` layout
- AC3: `CachedLoader.download()` returns cached table on fresh cache hit without calling `_fetch()`
- AC4: `CachedLoader.download()` falls back to stale cache on `OSError` and logs structured governance warning
- AC5: `CachedLoader.download()` raises `DataSourceOfflineError` when `REFORMLAB_OFFLINE=1` and cache miss
- AC6: `SourceCache.status()` returns `CacheStatus` with all required fields (cached, path, downloaded_at, hash, stale)
- 52 tests across 4 test files, all passing
- ruff clean, mypy strict clean (5 source files)
- No new dependencies required — uses stdlib + pyarrow only
- Follows existing codebase patterns: `ComputationAdapter` (protocol), `IngestionError` (exceptions), `hash_file()` (hashing)

### File List

**New source files:**
- `src/reformlab/population/__init__.py`
- `src/reformlab/population/loaders/__init__.py`
- `src/reformlab/population/loaders/base.py`
- `src/reformlab/population/loaders/cache.py`
- `src/reformlab/population/loaders/errors.py`

**New test files:**
- `tests/population/__init__.py`
- `tests/population/conftest.py`
- `tests/population/loaders/__init__.py`
- `tests/population/loaders/conftest.py`
- `tests/population/loaders/test_base.py`
- `tests/population/loaders/test_cache.py`
- `tests/population/loaders/test_cached_loader.py`
- `tests/population/loaders/test_errors.py`

**Modified files:**
- `pyproject.toml` — added `network` pytest marker and updated `addopts`

## Change Log

- 2026-03-03: Story created by create-story workflow — comprehensive developer context with caching architecture, protocol patterns, and testing strategy.
- 2026-03-03: Story implemented — all 10 tasks complete, 52 tests passing, ruff clean, mypy strict clean.
