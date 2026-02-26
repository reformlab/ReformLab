# Story 1.4: Implement Open-Data Ingestion Pipeline (Synthetic Population, Emission Factors)

Status: done

<!-- Story context created by create-story workflow on 2026-02-25. Analyzed against backlog (BKL-104), architecture, PRD (FR5, FR6), UX spec, previous stories (1.1, 1.2, 1.3), and current codebase (125 passing tests). -->

## Story

As a **policy analyst**,
I want to **load synthetic population datasets and environmental emission factor datasets through a validated pipeline that records data source metadata and hashes**,
so that **I can use public open-data sources (INSEE, Eurostat, ADEME) as inputs for carbon-tax and environmental policy simulations — with full provenance tracking for reproducibility**.

## Acceptance Criteria

Scope note: AC-1 through AC-3 are the required BKL-104 baseline. AC-4 through AC-6 are approved hardening/extensions that can be sequenced after baseline delivery if sprint capacity tightens.

1. **AC-1: Synthetic population load** — Given a synthetic population dataset in CSV or Parquet format, when loaded through the pipeline, then data source metadata (name, version, download URL, description) and SHA-256 content hash are recorded alongside the loaded `pa.Table`.

2. **AC-2: Emission factor load** — Given an emission factor dataset (e.g., ADEME Base Carbone CSV), when loaded through the pipeline, then factors are accessible by category and year for template computations, with source metadata and hash recorded.

3. **AC-3: Corrupted/incomplete dataset error** — Given a corrupted or incomplete dataset (missing required columns, invalid data, truncated file), when loaded, then the pipeline fails with a specific, actionable error before any computation begins — following the established `IngestionError` pattern.

4. **AC-4: Data source registry** — Given multiple loaded datasets, when queried, then each dataset's metadata (source name, version, hash, load timestamp, row count, column names) is retrievable for manifest inclusion, including multiple versions/files from the same source without silent overwrite.

5. **AC-5: Format auto-detection** — Given a dataset file, when loaded through the unified pipeline entry point, then the format (CSV, Parquet) is auto-detected from the file extension and the correct loader is used — reusing the existing `ingestion.ingest()` dispatcher.

6. **AC-6: Schema contract enforcement** — Given a dataset with a declared schema contract, when loaded, then required columns are validated and type mismatches produce structured errors — reusing the existing `DataSchema` + `IngestionError` infrastructure from Story 1.2.

## Tasks / Subtasks

- [x] Task 1: Define open-data pipeline types (AC: 1, 2, 4)
  - [x] 1.1 Create `DataSourceMetadata` frozen dataclass: `name: str`, `version: str`, `url: str`, `description: str`, `license: str = ""`
  - [x] 1.2 Create `DatasetManifest` frozen dataclass: `source: DataSourceMetadata`, `content_hash: str` (SHA-256 hex), `file_path: Path`, `format: IngestionFormat`, `row_count: int`, `column_names: tuple[str, ...]`, `loaded_at: str` (ISO 8601)
  - [x] 1.3 Create `DatasetRegistry` class: stores loaded `DatasetManifest` entries keyed by `dataset_key = "{source.name}@{source.version}:{content_hash[:12]}"`, with `register(manifest)`, `get(dataset_key) -> DatasetManifest | None`, `all() -> tuple[DatasetManifest, ...]`, `to_dict() -> dict[str, Any]` for manifest serialization
  - [x] 1.4 Add `find_by_source(source_name: str) -> tuple[DatasetManifest, ...]` helper and deterministic conflict behavior (`register()` is append-only by unique `dataset_key`; duplicate key raises `ValueError`)

- [x] Task 2: Implement content hashing utility (AC: 1, 2)
  - [x] 2.1 Implement `hash_file(path: Path) -> str` using `hashlib.sha256` with chunked file reading (8 KB chunks to handle large files without loading into memory)
  - [x] 2.2 Ensure hash is deterministic — same file always produces same hash regardless of OS

- [x] Task 3: Implement `load_dataset()` pipeline entry point (AC: 1, 2, 3, 5, 6)
  - [x] 3.1 Implement `load_dataset(path: str | Path, schema: DataSchema, source: DataSourceMetadata) -> tuple[pa.Table, DatasetManifest]`
  - [x] 3.2 Internally call `ingestion.ingest(path, schema)` for format detection + schema validation + loading
  - [x] 3.3 Call `hash_file()` on the source file
  - [x] 3.4 Build `DatasetManifest` from `IngestionResult` metadata + hash + source metadata
  - [x] 3.5 Return `(table, manifest)` tuple
  - [x] 3.6 Enforce path-safety policy before ingestion: resolve path, require existing regular file, reject files outside allowed roots

- [x] Task 4: Define built-in schema contracts for open datasets (AC: 2, 6)
  - [x] 4.1 Define `SYNTHETIC_POPULATION_SCHEMA` — `DataSchema` with required columns: `household_id: int64`, `person_id: int64`, `age: int64`, `income: float64`; optional columns: `region_code: utf8`, `housing_status: utf8`, `household_size: int64`
  - [x] 4.2 Define `EMISSION_FACTOR_SCHEMA` — `DataSchema` with required columns: `category: utf8`, `factor_value: float64`, `unit: utf8`; optional columns: `year: int64`, `subcategory: utf8`, `source: utf8`, `co2_equivalent: float64`
  - [x] 4.3 Both schemas are exported as module-level constants following `DEFAULT_OPENFISCA_OUTPUT_SCHEMA` pattern

- [x] Task 5: Implement emission factor access helpers (AC: 2)
  - [x] 5.1 Implement `EmissionFactorIndex` frozen dataclass wrapping a `pa.Table` with lookup methods: `by_category(category: str) -> pa.Table`, `by_category_and_year(category: str, year: int) -> pa.Table`, `categories() -> tuple[str, ...]`
  - [x] 5.2 Implement `build_emission_factor_index(table: pa.Table) -> EmissionFactorIndex` factory function

- [x] Task 6: Write tests (AC: 1-6)
  - [x] 6.1 Synthetic population CSV load test: valid CSV loads correctly with metadata and hash recorded
  - [x] 6.2 Synthetic population Parquet load test: valid Parquet loads with same contract as CSV
  - [x] 6.3 Emission factor CSV load test: valid emission factor dataset loads with category/year access
  - [x] 6.4 Missing columns test: dataset missing required columns produces structured `IngestionError`
  - [x] 6.5 Corrupted file test: truncated/invalid file produces actionable error before computation
  - [x] 6.6 Hash determinism test: same file hashed twice produces identical SHA-256
  - [x] 6.7 Hash uniqueness test: different files produce different hashes
  - [x] 6.8 Dataset registry test: register + retrieve + list manifests
  - [x] 6.8a Dataset registry collision test: duplicate `dataset_key` raises explicit `ValueError`
  - [x] 6.8b Dataset registry same-source multi-version test: manifests are preserved and retrievable via `find_by_source()`
  - [x] 6.9 Registry serialization test: `to_dict()` produces JSON-serializable dict for manifest inclusion
  - [x] 6.10 EmissionFactorIndex test: `by_category()` and `by_category_and_year()` return correct subsets
  - [x] 6.11 EmissionFactorIndex categories test: `categories()` returns sorted unique category names
  - [x] 6.12 Schema validation test: type mismatches produce structured errors with expected/actual types
  - [x] 6.13 All 94 existing tests must continue to pass
  - [x] 6.14 Path policy test: path outside allowed roots fails with actionable `IngestionError`

- [x] Task 7: Package integration (AC: all)
  - [x] 7.1 Create `src/reformlab/data/__init__.py` with `__all__` exports
  - [x] 7.2 Create `src/reformlab/data/__init__.pyi` type stubs
  - [x] 7.3 Create `.pyi` type stubs for new modules
  - [x] 7.4 Update `src/reformlab/__init__.py` if needed for top-level re-exports

## Dev Notes

### Architecture Compliance

- **Module location:** `src/reformlab/data/` — this is a NEW subsystem. The architecture doc (line 154) defines: `data/: Open data ingestion, synthetic population generation, data transformation pipelines. Prepares inputs for the computation adapter.` This is separate from `computation/` which handles the adapter interface.
- **Reuse `computation.ingestion`:** The `data/` module should import and reuse `ingest()`, `ingest_csv()`, `ingest_parquet()`, `DataSchema`, `IngestionError`, `IngestionResult` from `reformlab.computation.ingestion`. Do NOT duplicate ingestion logic.
- **Core data type:** `pa.Table` (PyArrow) — established in Stories 1.1-1.3. All pipeline operations return `pa.Table`. Do NOT introduce pandas or polars.
- **Immutable data:** Follow `@dataclass(frozen=True)` pattern from `types.py`, `ingestion.py`, `mapping.py`.
- **Type stubs:** Create `.pyi` files for all new public modules (PEP 561, established in Story 1.1).
- **Package exports:** Add new public types to `src/reformlab/data/__init__.py` with `__all__`.

### Existing Code to Build On (from Stories 1.1-1.3)

**DO NOT recreate these — they already exist and MUST be reused:**
- `ingest(path, schema) -> IngestionResult` in `computation/ingestion.py` — format auto-detection (CSV/Parquet) and schema-validated loading
- `ingest_csv(path, schema) -> IngestionResult` — CSV-specific loader with gzip support
- `ingest_parquet(path, schema) -> IngestionResult` — Parquet-specific loader with thrift limits
- `DataSchema(schema, required_columns, optional_columns)` — schema contract definition
- `IngestionError(file_path, summary, reason, fix, missing_columns, type_mismatches)` — structured error
- `IngestionResult(table, source_path, format, row_count, metadata)` — ingestion output
- `TypeMismatch(column, expected_type, actual_type)` — type mismatch descriptor
- `DEFAULT_OPENFISCA_OUTPUT_SCHEMA` — example of a schema constant (follow this pattern)
- `MappingConfig`, `apply_output_mapping()` in `computation/mapping.py` — mapping layer (Story 1.3); the data pipeline may need to rename columns from external dataset naming to project schema

**Key relationship:** The `data/` module sits ABOVE the `computation/` module in the architecture stack. It uses the computation layer's ingestion infrastructure to load and validate files, then adds metadata tracking and hash computation on top. The data pipeline prepares inputs that eventually flow into the computation adapter.

**DO NOT:**
- Duplicate `ingest()` / `ingest_csv()` / `ingest_parquet()` logic — import and call them
- Modify any existing `computation/` module files (unless adding to `__init__.py` exports)
- Create a custom CSV/Parquet reader — use the existing ingestion functions
- Add new dependencies for file hashing — use `hashlib` (stdlib)

### Technical Requirements

- **Python 3.13+** — use modern syntax (`str | Path`, `dict[str, Any]`, `tuple[str, ...]`)
- **hashlib** (stdlib) — use `hashlib.sha256()` for content hashing; chunked reads for memory efficiency
- **PyArrow >= 18.0.0** — table filtering via `pa.compute.filter()` or boolean masking for emission factor lookups; use `pa.compute.equal()` for category matching
- **No new dependencies required** — this story uses only `pyarrow` (already installed) and `hashlib` (stdlib)
- **No pandas/polars** — all data stays as `pa.Table`
- **datetime** (stdlib) — use `datetime.now(UTC).isoformat(timespec="seconds")` for timestamps (pattern from `ingestion.py` line 339)

### PyArrow Table Filtering API

```python
import pyarrow as pa
import pyarrow.compute as pc

# Filter rows by column value
mask = pc.equal(table.column("category"), "transport")
filtered = table.filter(mask)

# Filter by multiple conditions
mask = pc.and_(
    pc.equal(table.column("category"), "transport"),
    pc.equal(table.column("year"), 2025),
)
filtered = table.filter(mask)

# Get unique values from a column
unique_categories = pc.unique(table.column("category")).to_pylist()
```

### SHA-256 File Hashing Pattern

```python
import hashlib
from pathlib import Path

def hash_file(path: Path) -> str:
    """Compute SHA-256 hex digest of a file using chunked reads."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()
```

Use 8 KB chunks — balances memory usage and I/O performance. This handles files of any size without loading into memory.

### Error Design Principles (from Architecture & UX)

- Errors are **field-level and blocking** — contract failures stop processing
- Error format: **"[What failed] — [Why] — [How to fix]"** (same as `IngestionError`)
- Report **all** validation failures at once (not fail-on-first)
- Errors name the exact file path and issue
- Never show raw exceptions or stack traces to the user
- Reuse `IngestionError` for all data loading errors — do NOT create a new exception class for the data module (the ingestion errors are generic enough)

### Performance Requirements

- Dataset loading: bounded by I/O (CSV/Parquet read); no additional overhead beyond hash computation
- SHA-256 hashing: ~400 MB/s on modern hardware; negligible for expected dataset sizes (< 100 MB)
- EmissionFactorIndex lookups: O(n) filter on `pa.Table`; acceptable for datasets with < 100K rows
- Total pipeline latency for a typical dataset (10 MB CSV): < 2 seconds including hash

### Testing Standards

- **Framework:** pytest with fixtures in `conftest.py`
- **Pattern:** Given/When/Then style docstrings (established in Story 1.1)
- **Fixtures:** Use `tmp_path` for temporary CSV/Parquet files; create small fixture datasets (5-20 rows)
- **Test location:** `tests/data/test_pipeline.py` (new test directory)
- **All 94 existing tests must continue to pass**

### Import Style (from Story 1.1)

```python
from __future__ import annotations      # Always first (PEP 563)

import hashlib                           # stdlib
from dataclasses import dataclass, field # stdlib
from datetime import UTC, datetime       # stdlib
from pathlib import Path                 # stdlib
from typing import Any                   # stdlib

import pyarrow as pa                     # third-party
import pyarrow.compute as pc             # third-party

from reformlab.computation.ingestion import (  # local — reuse, don't duplicate
    DataSchema,
    IngestionError,
    IngestionFormat,
    ingest,
)
```

### Security Considerations

- **Hash verification:** SHA-256 content hashes enable downstream consumers to verify data integrity
- **No network I/O in this story:** This story loads local files only. Network download of open-data sources is a future enhancement (Phase 2). The pipeline takes a local file path, not a URL.
- **Path safety policy (explicit):** Before ingestion, normalize with `expanduser().resolve(strict=False)`, require `path.exists()` and `path.is_file()`, then enforce allowed roots. Default allowed roots: `Path.cwd()` and `Path(gettempdir())` (matching Story 1.3 hardening pattern), with optional override for integration callers.
- **Large file protection:** The existing Parquet thrift limits (from Story 1.2) are inherited via `ingest_parquet()`; for CSV files, PyArrow handles memory management internally

### Project Structure Notes

New files to create:
```
src/reformlab/data/
  __init__.py              # Package init with __all__ exports
  __init__.pyi             # Type stubs for package
  pipeline.py              # Core pipeline: load_dataset(), hash_file(), DataSourceMetadata, DatasetManifest, DatasetRegistry
  pipeline.pyi             # Type stubs
  schemas.py               # Built-in schema constants: SYNTHETIC_POPULATION_SCHEMA, EMISSION_FACTOR_SCHEMA
  schemas.pyi              # Type stubs
  emission_factors.py      # EmissionFactorIndex class with category/year lookups
  emission_factors.pyi     # Type stubs

tests/data/
  __init__.py              # Test package init
  conftest.py              # Shared fixtures (sample CSV/Parquet files, DataSourceMetadata instances)
  test_pipeline.py         # Tests for load_dataset(), hash_file(), DatasetRegistry
  test_emission_factors.py # Tests for EmissionFactorIndex
```

**DO NOT modify:**
- Any existing `computation/` source files — the data module imports from computation, not vice versa
- Any existing test files — all 94 tests must continue passing

### Cross-Story Dependencies

**This story blocks:**
- **Story 1.5** (data quality checks) — needs loaded datasets with manifests for quality validation
- **Story 2.2** (carbon-tax template pack) — templates use emission factors loaded by this pipeline
- **Story 2.3** (subsidy/rebate/feebate template pack) — same emission factor dependency
- **Story 3.5** (integrate ComputationAdapter into orchestrator) — orchestrator needs population data loaded by this pipeline
- **Story 5.1** (immutable run manifest) — manifests include dataset hashes and metadata from this pipeline

**This story depends on:**
- **Story 1.1** (ComputationAdapter interface) — DONE. Provides `PopulationData`, `pa.Table` types.
- **Story 1.2** (CSV/Parquet ingestion) — DONE. Provides `ingest()`, `DataSchema`, `IngestionError`.
- **Story 1.3** (mapping configuration) — DONE. Provides `MappingConfig` for optional column renaming.

### References

- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md — BKL-104, lines 55, 92-95]
- [Source: _bmad-output/planning-artifacts/architecture.md — Data subsystem, line 154]
- [Source: _bmad-output/planning-artifacts/architecture.md — Data Contracts, lines 169-174]
- [Source: _bmad-output/planning-artifacts/architecture.md — Reproducibility & Governance, lines 186-189]
- [Source: _bmad-output/planning-artifacts/prd.md — FR5: Load synthetic populations and environmental datasets, line 492]
- [Source: _bmad-output/planning-artifacts/prd.md — FR6: Record data source metadata and hashes, line 493]
- [Source: _bmad-output/planning-artifacts/prd.md — NFR6: Bit-identical outputs, line 554]
- [Source: _bmad-output/planning-artifacts/prd.md — NFR9: Automatic manifest generation, line 557]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md — Error Handling, Data Errors section]
- [Source: src/reformlab/computation/ingestion.py — ingest() dispatcher, lines 205-220]
- [Source: src/reformlab/computation/ingestion.py — DataSchema, lines 17-55]
- [Source: src/reformlab/computation/ingestion.py — IngestionError, lines 77-95]
- [Source: src/reformlab/computation/ingestion.py — IngestionResult, lines 67-74]
- [Source: src/reformlab/computation/types.py — PopulationData, lines 12-27]

### Previous Story Intelligence (Stories 1.1, 1.2, 1.3)

**Patterns to follow:**
- `@dataclass(frozen=True)` for all immutable data types (DataSourceMetadata, DatasetManifest)
- `DatasetRegistry` is the one mutable class — use a `dict[str, DatasetManifest]` internally
- Structured error class with `file_path`, `summary`, `reason`, `fix` fields (reuse `IngestionError`)
- Aggregate all errors before raising (never fail-on-first)
- Explicit `__all__` in `__init__.py` for public API
- `.pyi` type stubs + `py.typed` marker (already exists at `src/reformlab/py.typed`)
- Given/When/Then docstrings in tests
- `from __future__ import annotations` as first import

**Anti-patterns to avoid:**
- Do NOT use pandas or polars — `pa.Table` is the core data type
- Do NOT duplicate ingestion logic from `computation/ingestion.py` — import and reuse
- Do NOT add network download dependencies (httpx, requests, pooch) — this story handles local files only; network fetching is a future story
- Do NOT create a new exception class — reuse `IngestionError` for all data loading errors
- Do NOT hardcode file paths or dataset URLs — all paths come from function parameters
- Do NOT break the 94 existing tests

**Lessons from Story 1.3 code review:**
- H-1: Validate all external input strictly — apply same rigor to dataset schema validation
- H-2: Proper type detection avoids false positives — use PyArrow type system for schema enforcement
- M-1: Type stubs must be proper stubs (not full implementations) — `.pyi` files should only contain signatures
- Source-aware metadata: Include file paths and source info in all error messages

### Git Intelligence Summary

- 2 commits in repo: initial BMAD setup + BMAD in-progress
- Stories 1.1-1.3 implemented in `src/reformlab/computation/` with 94 passing tests
- Current modules: `adapter.py`, `exceptions.py`, `ingestion.py`, `mapping.py`, `mock_adapter.py`, `openfisca_adapter.py`, `types.py` — all with `.pyi` stubs
- `pyproject.toml` has `pyarrow>=18.0.0`, `pyyaml>=6.0.2` as deps; `pytest>=8.3.3`, `ruff>=0.15.0`, `mypy>=1.19.0` as dev deps
- Linting: `ruff check` passes on all src/tests files
- Static typing: `mypy src` passes in strict mode
- `py.typed` marker present at `src/reformlab/py.typed`

### Project Context Reference

- No `project-context.md` file in repository; context sourced from PRD, architecture, backlog, UX spec, Stories 1.1-1.3, and current codebase.

### Open Data Context (for developer awareness)

This story creates the pipeline infrastructure for loading local open-data files. Typical target datasets include:

| Dataset | Source | Format | Typical Size | Use Case |
|---------|--------|--------|-------------|----------|
| Synthetic population | INSEE census (fichiers detail) | CSV | 10-100 MB | Household-level microsimulation input |
| ADEME Base Carbone | data.gouv.fr | CSV (~10 MB) | ~10 MB | Emission factors by category |
| Eurostat GHG emissions | Eurostat API export | CSV/TSV | 1-5 MB | Cross-country emission benchmarks |
| EU-SILC public use files | Eurostat | CSV | 2-10 MB per file | Income/living conditions for validation |

All datasets fit within the 16GB RAM single-machine target. The pipeline handles local files only — download/caching functionality is a future enhancement.

### Latest Tech Information

| Library | Latest Stable | Project Pin | Notes |
|---------|--------------|-------------|-------|
| PyArrow | 23.0.1 (Feb 2026) | `>=18.0.0` | `pc.equal()`, `pc.filter()`, `pc.unique()` available since v1.0. No breaking changes. |
| Python | 3.14.3 latest | `>=3.13` | `hashlib.sha256` is stable across versions. |
| hashlib | stdlib | N/A | SHA-256 is FIPS 180-4 compliant; `file_digest()` available in 3.11+ but chunked manual approach is more explicit. |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

No debug issues encountered.

### Completion Notes List

- Implemented `DataSourceMetadata`, `DatasetManifest` (frozen dataclasses) and `DatasetRegistry` (mutable, append-only by unique key) in `pipeline.py`
- `DatasetManifest.dataset_key` property generates `{name}@{version}:{hash[:12]}` keys for registry lookups
- `hash_file()` uses `hashlib.sha256` with 8KB chunked reads for memory-efficient hashing
- `load_dataset()` orchestrates: path safety check → hash computation → `ingest()` delegation → manifest construction
- Path safety policy enforces allowed roots (defaults to cwd + tempdir), matching Story 1.3 hardening pattern
- All ingestion logic reuses `computation.ingestion` — no duplication
- `SYNTHETIC_POPULATION_SCHEMA` and `EMISSION_FACTOR_SCHEMA` defined as module-level constants in `schemas.py`
- `EmissionFactorIndex` provides `by_category()`, `by_category_and_year()`, `categories()` lookups using PyArrow compute
- Added code-review remediations:
  - wrapped hash read failures in `load_dataset()` as structured `IngestionError`
  - added explicit year-column guard in `EmissionFactorIndex.by_category_and_year()`
  - made `categories()` null-safe by excluding null category values
  - strengthened AC-3 coverage with actionable error-format assertions
- 31 new tests added (all pass), 94 existing tests continue to pass (125 total)
- All quality gates pass: ruff lint, mypy strict mode, pytest 125/125
- `.pyi` type stubs created for all new public modules
- No existing computation/ files were modified
- No new dependencies were needed (only `hashlib` stdlib + existing `pyarrow`)
- Task 7.4 (update `src/reformlab/__init__.py`): not needed — the `data` subpackage is a separate import path (`reformlab.data`), consistent with how `reformlab.computation` works

### Senior Developer Review (AI)

- Reviewer: GPT-5 Codex
- Date: 2026-02-25
- Outcome: Changes Requested → Fixed → Approved
- Findings resolved:
  - Hash read failures now return structured `IngestionError` instead of leaking raw `PermissionError`
  - Emission factor year lookups now fail with actionable error if `year` column is missing
  - Emission factor category listing is null-safe
  - Corrupted-file tests now validate actionable error formatting
  - Story file list now documents git workspace context vs. story-specific files
- Verification run:
  - `uv run ruff check src tests`
  - `mypy src`
  - `pytest -q` (125 passed)

### Change Log

- 2026-02-25: Implemented Story 1.4 — open-data ingestion pipeline with types, hashing, schemas, emission factor index, registry, tests, and type stubs
- 2026-02-25: Senior code-review remediation applied; fixed structured error handling and emission-factor edge cases, expanded regression coverage, and approved story as done.

### File List

New files:
- src/reformlab/data/__init__.py
- src/reformlab/data/__init__.pyi
- src/reformlab/data/pipeline.py
- src/reformlab/data/pipeline.pyi
- src/reformlab/data/schemas.py
- src/reformlab/data/schemas.pyi
- src/reformlab/data/emission_factors.py
- src/reformlab/data/emission_factors.pyi
- tests/data/__init__.py
- tests/data/conftest.py
- tests/data/test_pipeline.py
- tests/data/test_emission_factors.py

Modified files:
- src/reformlab/data/pipeline.py (review remediation: hash read errors wrapped as `IngestionError`)
- src/reformlab/data/emission_factors.py (review remediation: year-column guard + null-safe categories)
- tests/data/test_pipeline.py (review remediation tests for actionable error formatting and hash read failures)
- tests/data/test_emission_factors.py (review remediation tests for missing-year and null-category edge cases)
- _bmad-output/implementation-artifacts/sprint-status.yaml (status update)
- _bmad-output/implementation-artifacts/1-4-implement-open-data-ingestion-pipeline.md (this file)

Git workspace context (not Story 1.4 changes):
- Additional pre-existing source/test files are present in git status from prior story work:
  - `src/reformlab/computation/*`
  - `src/reformlab/__init__.py`
  - `src/reformlab/py.typed`
  - `tests/computation/*`
  - `tests/__init__.py`
