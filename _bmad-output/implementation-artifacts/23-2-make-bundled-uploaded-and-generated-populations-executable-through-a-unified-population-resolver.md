# Story 23.2: Make bundled, uploaded, and generated populations executable through a unified population resolver

Status: ready-for-dev

## Story

As a platform developer,
I want a unified population resolver that can load bundled, uploaded, and generated populations by their identifiers,
so that any population discoverable in the workspace is executable through the same run path without separate code paths leaking into user behavior.

**Epic:** Epic 23 — Live OpenFisca Runtime and Executable Population Alignment
**Priority:** P0
**Estimate:** 5 SP
**Dependencies:** Story 23.1

## Acceptance Criteria

1. Given a bundled population selected in the workspace, when a run starts, then that dataset is loaded as the actual execution input.
2. Given an uploaded population selected in the workspace, when a run starts, then the uploaded dataset is resolved and executed through the same run path.
3. Given a generated population selected in the workspace, when a run starts, then the generated dataset is resolved and executed through the same run path.
4. Given a population ID that cannot be resolved to an executable dataset, when the run is requested, then execution is blocked with a precise population-resolution error.
5. Given completed run metadata, when reviewed, then it points back to the resolved population identifier and source class used for execution.

## Tasks / Subtasks

### Backend: Create PopulationResolver module

- [ ] **Create `src/reformlab/server/population_resolver.py`** (AC: 1, 2, 3, 4)
  - [ ] Create `PopulationResolutionError` exception class with `{"what", "why", "fix"}` pattern
  - [ ] Create `PopulationSource` literal type: `Literal["bundled", "uploaded", "generated"]`
  - [ ] Create `ResolvedPopulation` dataclass (frozen) with:
    - `population_id: str`
    - `source: PopulationSource`
    - `data_path: Path | PopulationData` (path for file-based, loaded data for in-memory)
    - `row_count: int | None`
    - `metadata: dict[str, Any]`
  - [ ] Implement `PopulationResolver` class with:
    - `__init__(self, data_dir: Path, uploaded_dir: Path, generated_dir: Path)`
    - `resolve(self, population_id: str) -> ResolvedPopulation`
    - `_resolve_bundled(self, population_id: str) -> ResolvedPopulation | None`
    - `_resolve_uploaded(self, population_id: str) -> ResolvedPopulation | None`
    - `_resolve_generated(self, population_id: str) -> ResolvedPopulation | None`
    - `_load_folder_population(self, folder_path: Path) -> ResolvedPopulation | None`
  - [ ] Reuse patterns from `populations.py`:
    - `_DATA_EXTENSIONS = {".csv", ".parquet"}`
    - Environment variables for directories (`REFORMLAB_DATA_DIR`, `REFORMLAB_UPLOADED_POPULATIONS_DIR`)
    - Manifest/sidecar file detection (`.manifest.json`, `.meta.json`)

- [ ] **Implement resolution order** (AC: 1, 2, 3)
  - [ ] Check bundled populations first (`data/populations/`)
  - [ ] Then uploaded populations (`~/.reformlab/uploaded-populations/`)
  - [ ] Then generated populations (with manifest files)
  - [ ] For folder-based populations: read `descriptor.json` to find the actual data file
  - [ ] Return `ResolvedPopulation` with correct source classification

- [ ] **Implement error handling** (AC: 4)
  - [ ] Raise `PopulationResolutionError` with clear messages:
    - `"Population '{population_id}' not found in bundled, uploaded, or generated sources"`
    - `"Population '{population_id}' exists but has no readable data file"`
    - `"Population '{population_id}' file format is not supported: {suffix}"`
  - [ ] Include available population IDs in error when listing is possible

### Backend: Integrate resolver into run route

- [ ] **Create dependency function** (AC: 1, 2, 3)
  - [ ] Add `get_population_resolver() -> PopulationResolver` in `src/reformlab/server/dependencies.py`
  - [ ] Lazy-initialize singleton like other dependencies
  - [ ] Read directory paths from environment variables

- [ ] **Replace `_resolve_population_path` in runs.py** (AC: 1, 2, 3, 5)
  - [ ] Update `run_simulation()` to use `PopulationResolver.resolve()`
  - [ ] Update `_run_portfolio()` to use `PopulationResolver.resolve()`
  - [ ] Store `ResolvedPopulation.source` in run metadata
  - [ ] Store population source in `ResultMetadata` (new field: `population_source: str | None`)

- [ ] **Update ResultMetadata model** (AC: 5)
  - [ ] Add `population_source: Literal["bundled", "uploaded", "generated"] | None` to `ResultMetadata`
  - [ ] Update `_dict_to_metadata()` in `result_store.py` to extract `population_source`
  - [ ] Update `save_metadata()` to persist `population_source`

### Backend: Update API contracts

- [ ] **Extend RunResponse with population source** (AC: 5)
  - [ ] Add `population_source: Literal["bundled", "uploaded", "generated"] | None` to `RunResponse`
  - [ ] Return `population_source` in run response

- [ ] **Update server models** (AC: 5)
  - [ ] Update `ResultDetailResponse` to include `population_source`
  - [ ] Update any response types that include run metadata

### Tests: Unit tests

- [ ] **Test PopulationResolver module** (AC: 1, 2, 3, 4)
  - [ ] Add `tests/server/test_population_resolver.py`
  - [ ] `test_resolve_bundled_population()`: bundled population resolves correctly
  - [ ] `test_resolve_uploaded_population()`: uploaded population resolves correctly
  - [ ] `test_resolve_generated_population()`: generated population with manifest resolves correctly
  - [ ] `test_resolve_folder_based_population()`: folder with descriptor.json resolves
  - [ ] `test_resolve_missing_population_raises()`: missing ID raises with clear error
  - [ ] `test_resolve_unreadable_file_raises()`: exists but unreadable raises
  - [ ] `test_resolve_unsupported_format_raises()`: wrong extension raises
  - [ ] `test_resolution_order_bundled_first()`: bundled shadows uploaded if duplicate IDs
  - [ ] `test_resolved_population_fields()`: verify all fields are populated correctly

- [ ] **Test dependency function** (AC: 1, 2, 3)
  - [ ] Add `test_get_population_resolver_singleton()` in `tests/server/test_dependencies.py`
  - [ ] Add `test_population_resolver_uses_env_vars()` in `tests/server/test_dependencies.py`

### Tests: Integration tests

- [ ] **Test run route integration** (AC: 1, 2, 3, 5)
  - [ ] Add `test_run_with_bundled_population()` in `tests/server/test_routes_runs.py`
  - [ ] Add `test_run_with_uploaded_population()` in `tests/server/test_routes_runs.py`
  - [ ] Add `test_run_with_generated_population()` in `tests/server/test_routes_runs.py`
  - [ ] Add `test_run_with_folder_population()` in `tests/server/test_routes_runs.py`
  - [ ] Add `test_run_response_includes_population_source()` in `tests/server/test_routes_runs.py`
  - [ ] Add `test_run_metadata_includes_population_source()` in `tests/server/test_routes_runs.py`

- [ ] **Test negative paths** (AC: 4)
  - [ ] Add `test_run_with_missing_population_fails_with_clear_error()` in `tests/server/test_routes_runs.py`
  - [ ] Add `test_run_with_deleted_population_file_fails()` in `tests/server/test_routes_runs.py`

- [ ] **Test portfolio execution with resolved populations** (AC: 1, 2, 3)
  - [ ] Add `test_portfolio_run_with_uploaded_population()` in `tests/server/test_routes_runs.py`
  - [ ] Add `test_portfolio_run_with_generated_population()` in `tests/server/test_routes_runs.py`

## Dev Notes

### Architecture Patterns

**Current Population Resolution Gap**

The existing `_resolve_population_path()` in `runs.py` (lines 41-54) only scans the data directory:
```python
def _resolve_population_path(population_id: str | None) -> Path | None:
    """Resolve a population_id to a file path by scanning the data directory."""
    data_dir = Path(os.environ.get("REFORMLAB_DATA_DIR", "data")) / "populations"
    # Only checks bundled data directory - doesn't check uploaded or generated!
```

This means:
- **Bundled populations** (in `data/populations/`) work
- **Uploaded populations** (in `~/.reformlab/uploaded-populations/`) are listed but NOT executable
- **Generated populations** (with `.manifest.json` files) are NOT executable

**Existing Patterns to Reuse**

The `populations.py` route module already has resolution logic that we should extract:

1. **`_find_population_file(population_id: str)`** (lines 102-119): Checks both directories with proper extension handling
2. **`_get_population_origin()`** (lines 122-142): Determines source classification
3. **Folder-based population support**: Lines 259-273 show reading `descriptor.json` from folders
4. **Environment variable patterns**: `_get_data_dir()`, `_get_uploaded_dir()` (lines 91-94, 84-88)

**Resolution Strategy**

Create a unified `PopulationResolver` service that:

1. **Centralizes population lookup logic** (currently split between runs.py and populations.py)
2. **Supports three sources** in priority order:
   - Bundled: `data/populations/{id}.{ext}` or `data/populations/{id}/data.{ext}`
   - Uploaded: `~/.reformlab/uploaded-populations/{id}.{ext}`
   - Generated: `data/populations/{id}.{ext}` with `{id}.manifest.json` present
3. **Returns rich metadata** (source, row_count, metadata) not just file paths
4. **Provides clear error messages** following the `{"what", "why", "fix"}` pattern

### Source Tree Components

**New files to create:**

| File Path | Purpose | Key Changes |
|-----------|---------|-------------|
| `src/reformlab/server/population_resolver.py` | Population resolver service | `PopulationResolver` class, `ResolvedPopulation` dataclass, `PopulationResolutionError` |

**Files to modify:**

| File Path | Purpose | Key Changes |
|-----------|---------|-------------|
| `src/reformlab/server/dependencies.py` | Dependency injection | Add `get_population_resolver()` function |
| `src/reformlab/server/routes/runs.py` | Execution route | Replace `_resolve_population_path()` with `PopulationResolver.resolve()`, store `population_source` |
| `src/reformlab/server/models.py` | Pydantic models | Add `population_source` to `RunResponse` and `ResultDetailResponse` |
| `src/reformlab/server/result_store.py` | Result persistence | Add `population_source` to `ResultMetadata`, update save/load logic |

**Test files to create:**

| File Path | Purpose |
|-----------|---------|
| `tests/server/test_population_resolver.py` | Resolver unit tests |

**Test files to modify:**

| File Path | Purpose |
|-----------|---------|
| `tests/server/test_routes_runs.py` | Add integration tests for uploaded/generated populations |
| `tests/server/test_dependencies.py` | Add resolver dependency tests |

### Implementation Notes

**PopulationResolver Class Design**

```python
# src/reformlab/server/population_resolver.py

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Any

PopulationSource = Literal["bundled", "uploaded", "generated"]

@dataclass(frozen=True)
class ResolvedPopulation:
    """Result of successful population resolution."""
    population_id: str
    source: PopulationSource
    data_path: Path  # Path to CSV/Parquet file
    row_count: int | None = None  # None if not yet loaded
    metadata: dict[str, Any] = None

class PopulationResolutionError(Exception):
    """Raised when a population_id cannot be resolved to an executable dataset."""

    def __init__(self, population_id: str, available_ids: list[str] | None = None):
        self.population_id = population_id
        self.available_ids = available_ids or []

        # Build clear error message
        what = f"Population '{population_id}' not found"
        why = f"Checked bundled, uploaded, and generated sources. Available: {', '.join(self.available_ids[:10])}"
        if len(self.available_ids) > 10:
            why += f" ... and {len(self.available_ids) - 10} more"
        fix = "Select a valid population ID from the available populations"

        super().__init__({"what": what, "why": why, "fix": fix})

class PopulationResolver:
    """Resolve population IDs to executable datasets across all sources."""

    _DATA_EXTENSIONS = {".csv", ".parquet"}

    def __init__(self, data_dir: Path, uploaded_dir: Path):
        self.data_dir = data_dir
        self.uploaded_dir = uploaded_dir

    def resolve(self, population_id: str) -> ResolvedPopulation:
        """Resolve a population ID to its executable dataset.

        Checks sources in priority order: bundled → uploaded → generated.
        Raises PopulationResolutionError if not found in any source.
        """
        # Try bundled first
        if resolved := self._resolve_bundled(population_id):
            return resolved

        # Then uploaded
        if resolved := self._resolve_uploaded(population_id):
            return resolved

        # Then generated (checked via manifest file presence)
        if resolved := self._resolve_generated(population_id):
            return resolved

        # Not found - gather available IDs for error message
        available = self._list_available_ids()
        raise PopulationResolutionError(population_id, available)

    def _resolve_bundled(self, population_id: str) -> ResolvedPopulation | None:
        """Check data/populations/ for bundled populations."""
        # Check single-file format: data/populations/{id}.csv
        for ext in self._DATA_EXTENSIONS:
            path = self.data_dir / f"{population_id}{ext}"
            if path.exists():
                return ResolvedPopulation(
                    population_id=population_id,
                    source="bundled",
                    data_path=path,
                )

        # Check folder format: data/populations/{id}/data.csv
        folder_path = self.data_dir / population_id
        if folder_path.is_dir():
            if resolved := self._load_folder_population(folder_path, population_id, "bundled"):
                return resolved

        return None

    def _resolve_uploaded(self, population_id: str) -> ResolvedPopulation | None:
        """Check uploaded populations directory."""
        for ext in self._DATA_EXTENSIONS:
            path = self.uploaded_dir / f"{population_id}{ext}"
            if path.exists():
                return ResolvedPopulation(
                    population_id=population_id,
                    source="uploaded",
                    data_path=path,
                )
        return None

    def _resolve_generated(self, population_id: str) -> ResolvedPopulation | None:
        """Check for generated populations (have manifest.json)."""
        manifest_path = self.data_dir / f"{population_id}.manifest.json"
        if manifest_path.exists():
            # Generated populations are stored like bundled populations
            # The manifest file indicates this is a generated population
            return self._resolve_bundled(population_id)
        return None

    def _load_folder_population(
        self, folder_path: Path, population_id: str, source: PopulationSource
    ) -> ResolvedPopulation | None:
        """Load a folder-based population with descriptor.json."""
        import json

        descriptor_path = folder_path / "descriptor.json"
        if not descriptor_path.exists():
            return None

        try:
            descriptor = json.loads(descriptor_path.read_text())
            data_file = descriptor.get("data_file")
            if not data_file:
                return None

            data_path = folder_path / data_file
            if not data_path.exists():
                return None

            return ResolvedPopulation(
                population_id=population_id,
                source=source,
                data_path=data_path,
                metadata=descriptor,
            )
        except (json.JSONDecodeError, OSError):
            return None

    def _list_available_ids(self) -> list[str]:
        """List all available population IDs for error messages."""
        ids = set()

        # Scan bundled
        if self.data_dir.exists():
            for path in self.data_dir.iterdir():
                if path.suffix in self._DATA_EXTENSIONS:
                    ids.add(path.stem)
                elif path.is_dir():
                    ids.add(path.name)

        # Scan uploaded
        if self.uploaded_dir.exists():
            for path in self.uploaded_dir.iterdir():
                if path.suffix in self._DATA_EXTENSIONS:
                    ids.add(path.stem)

        return sorted(ids)
```

**Dependency Integration**

```python
# src/reformlab/server/dependencies.py

_population_resolver: PopulationResolver | None = None

def get_population_resolver() -> PopulationResolver:
    """Return the global population resolver (lazy-initialized)."""
    global _population_resolver
    if _population_resolver is None:
        from pathlib import Path
        import os

        data_dir = Path(os.environ.get("REFORMLAB_DATA_DIR", "data")) / "populations"
        uploaded_dir = Path(os.environ.get(
            "REFORMLAB_UPLOADED_POPULATIONS_DIR",
            "~/.reformlab/uploaded-populations"
        )).expanduser()

        from reformlab.server.population_resolver import PopulationResolver
        _population_resolver = PopulationResolver(data_dir, uploaded_dir)
    return _population_resolver
```

**Run Route Integration**

```python
# src/reformlab/server/routes/runs.py

@router.post("", response_model=RunResponse)
async def run_simulation(
    body: RunRequest,
    cache: ResultCache = Depends(get_result_cache),
    store: ResultStore = Depends(get_result_store),
    registry: ScenarioRegistry = Depends(get_registry),
    resolver: PopulationResolver = Depends(get_population_resolver),  # NEW
) -> RunResponse:
    """Execute a simulation synchronously and return the result."""
    # ... validation code ...

    # OLD: population_path = _resolve_population_path(body.population_id)
    # NEW:
    try:
        resolved = resolver.resolve(body.population_id) if body.population_id else None
        population_path = resolved.data_path if resolved else None
        population_source = resolved.source if resolved else None
    except PopulationResolutionError as exc:
        raise HTTPException(
            status_code=404,
            detail=exc.args[0],  # Already in {"what", "why", "fix"} format
        )

    # ... rest of run logic ...

    # Store population_source in metadata
    store.save_metadata(
        run_id,
        ResultMetadata(
            # ... existing fields ...
            population_source=population_source,  # NEW
        ),
    )

    # Return in response
    return RunResponse(
        # ... existing fields ...
        population_source=population_source,  # NEW
    )
```

**Error Response Example**

When a population ID cannot be resolved:
```json
{
  "what": "Population 'my-uploaded-pop' not found",
  "why": "Checked bundled, uploaded, and generated sources. Available: fr-synthetic-2024, quick-test, uploaded-2024-01",
  "fix": "Select a valid population ID from the available populations"
}
```

### Testing Standards

**Unit Tests: `tests/server/test_population_resolver.py`**

```python
import pytest
from pathlib import Path
from reformlab.server.population_resolver import (
    PopulationResolver,
    PopulationResolutionError,
    ResolvedPopulation,
)

class TestPopulationResolver:
    """Story 23.2 / AC-1, AC-2, AC-3, AC-4: Population resolver tests."""

    @pytest.fixture
    def temp_data_dir(self, tmp_path: Path) -> Path:
        """Create a temporary data directory with test populations."""
        data_dir = tmp_path / "populations"
        data_dir.mkdir()

        # Create bundled population
        (data_dir / "bundled.csv").write_text("household_id,income\n1,50000\n")

        # Create uploaded directory
        uploaded_dir = tmp_path / "uploaded"
        uploaded_dir.mkdir()
        (uploaded_dir / "uploaded.csv").write_text("household_id,income\n2,60000\n")

        # Create generated population with manifest
        (data_dir / "generated.csv").write_text("household_id,income\n3,70000\n")
        (data_dir / "generated.manifest.json").write_text('{"generated": true}')

        # Create folder-based population
        folder_dir = data_dir / "folder-pop"
        folder_dir.mkdir()
        (folder_dir / "descriptor.json").write_text(
            '{"data_file": "data.csv", "description": "Test folder population"}'
        )
        (folder_dir / "data.csv").write_text("household_id,income\n4,80000\n")

        return data_dir, uploaded_dir

    def test_resolve_bundled_population(self, temp_data_dir: tuple[Path, Path]) -> None:
        """Bundled population resolves correctly."""
        data_dir, uploaded_dir = temp_data_dir
        resolver = PopulationResolver(data_dir, uploaded_dir)

        result = resolver.resolve("bundled")

        assert result.population_id == "bundled"
        assert result.source == "bundled"
        assert result.data_path.name == "bundled.csv"

    def test_resolve_uploaded_population(self, temp_data_dir: tuple[Path, Path]) -> None:
        """Uploaded population resolves correctly."""
        data_dir, uploaded_dir = temp_data_dir
        resolver = PopulationResolver(data_dir, uploaded_dir)

        result = resolver.resolve("uploaded")

        assert result.population_id == "uploaded"
        assert result.source == "uploaded"
        assert result.data_path.name == "uploaded.csv"

    def test_resolve_generated_population(self, temp_data_dir: tuple[Path, Path]) -> None:
        """Generated population with manifest resolves correctly."""
        data_dir, uploaded_dir = temp_data_dir
        resolver = PopulationResolver(data_dir, uploaded_dir)

        result = resolver.resolve("generated")

        assert result.population_id == "generated"
        assert result.source == "generated"
        assert result.data_path.name == "generated.csv"

    def test_resolve_folder_based_population(self, temp_data_dir: tuple[Path, Path]) -> None:
        """Folder-based population with descriptor.json resolves."""
        data_dir, uploaded_dir = temp_data_dir
        resolver = PopulationResolver(data_dir, uploaded_dir)

        result = resolver.resolve("folder-pop")

        assert result.population_id == "folder-pop"
        assert result.source == "bundled"
        assert result.data_path.name == "data.csv"
        assert result.metadata["description"] == "Test folder population"

    def test_resolve_missing_population_raises(self, temp_data_dir: tuple[Path, Path]) -> None:
        """Missing population ID raises with clear error."""
        data_dir, uploaded_dir = temp_data_dir
        resolver = PopulationResolver(data_dir, uploaded_dir)

        with pytest.raises(PopulationResolutionError) as exc_info:
            resolver.resolve("does-not-exist")

        error = exc_info.value
        assert error.population_id == "does-not-exist"
        assert "bundled" in str(error)
        assert "uploaded" in str(error)
        # Check available IDs are listed
        assert len(error.available_ids) > 0
```

**Integration Tests: `tests/server/test_routes_runs.py` additions**

```python
class TestRunWithUploadedPopulation:
    """Story 23.2 / AC-2: Uploaded populations are executable."""

    def test_run_with_uploaded_population(
        self, client: TestClient, auth_headers: dict[str, str], tmp_path: Path
    ) -> None:
        """Run simulation with an uploaded population executes successfully."""
        # Create uploaded population
        uploaded_dir = tmp_path / "uploaded"
        uploaded_dir.mkdir()
        pop_file = uploaded_dir / "test-uploaded.csv"
        pop_file.write_text("household_id,income\n1,50000\n")

        # Monkey-patch the resolver to use temp directory
        # ... (set up resolver with temp directories)

        response = client.post(
            "/api/runs",
            headers=auth_headers,
            json={
                "template_name": "carbon_tax",
                "policy": {"rate_schedule": {"2025": 50.0}},
                "population_id": "test-uploaded",
                "start_year": 2025,
                "end_year": 2025,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["population_source"] == "uploaded"
```

### Project Structure Notes

**Follow established patterns:**

- **Error responses**: Use the `{"what": str, "why": str, "fix": str}` pattern (see `runs.py` line 80-86)
- **Frozen dataclasses**: Use `@dataclass(frozen=True)` for `ResolvedPopulation`
- **Literal types**: Use `Literal["bundled", "uploaded", "generated"]` for closed enum
- **Environment variables**: Read directories from `REFORMLAB_DATA_DIR`, `REFORMLAB_UPLOADED_POPULATIONS_DIR`
- **Path expansion**: Use `.expanduser()` for home directory paths
- **Dependency injection**: Follow the singleton pattern in `dependencies.py`
- **Test fixtures**: Use `tmp_path` pytest fixture for temporary directories

**Do NOT duplicate logic:**

- The `_find_population_file()` logic in `populations.py` should be migrated into the resolver
- After this story, `populations.py` should use `PopulationResolver` for listing too
- The old `_resolve_population_path()` in `runs.py` should be removed

### References

- **Epic 23 Story 23.2**: `_bmad-output/planning-artifacts/epics.md` (Story 23.2 definition)
- **Architecture Section 5.9**: Server dependencies and mode ownership
- **Current populations route**: `src/reformlab/server/routes/populations.py` (lines 102-172 for resolution patterns)
- **Current runs route**: `src/reformlab/server/routes/runs.py` (lines 41-54 for current `_resolve_population_path`)
- **Story 23.1**: Runtime mode contract (completed prerequisite)
- **Project Context**: `_bmad-output/project-context.md` — Error response pattern, frozen dataclasses, testing rules

## Dev Agent Record

### Agent Model Used

glm-4.7 (Claude Opus 4.6 equivalent)

### Debug Log References

None created during story generation.

### Completion Notes List

- Analyzed existing population resolution code in `runs.py` and `populations.py`
- Identified the gap: uploaded/generated populations are listed but not executable
- Designed unified `PopulationResolver` service to consolidate resolution logic
- Specified clear error messages following project's `{"what", "why", "fix"}` pattern
- Created comprehensive test plan covering unit and integration tests
- Ready for dev-story execution with all necessary context

### File List

**New files:**
- `src/reformlab/server/population_resolver.py` — Population resolver service

**Modified files:**
- `src/reformlab/server/dependencies.py` — Add `get_population_resolver()`
- `src/reformlab/server/routes/runs.py` — Replace `_resolve_population_path()` with resolver
- `src/reformlab/server/models.py` — Add `population_source` to responses
- `src/reformlab/server/result_store.py` — Add `population_source` to `ResultMetadata`

**New test files:**
- `tests/server/test_population_resolver.py` — Resolver unit tests

**Modified test files:**
- `tests/server/test_routes_runs.py` — Add integration tests
- `tests/server/test_dependencies.py` — Add resolver dependency tests

**Planning artifacts referenced:**
1. `_bmad-output/planning-artifacts/epics.md` — Epic 23 Story 23.2
2. `_bmad-output/planning-artifacts/architecture.md` — Section 5.9
3. `_bmad-output/project-context.md` — Project patterns and rules
