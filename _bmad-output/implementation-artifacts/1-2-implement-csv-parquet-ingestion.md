# Story 1.2: Implement CSV/Parquet Ingestion for OpenFisca Outputs and Population Data

Status: done

<!-- Story context validated on 2026-02-25 against backlog, architecture, prior story, codebase, and latest primary-source docs. -->

## Story

As a **policy analyst**,
I want to **ingest OpenFisca household-level outputs from CSV or Parquet files into the internal schema with validated types and clear error reporting**,
so that **population data is reliably available for downstream orchestration, mapping, and indicator computation**.

## Acceptance Criteria

1. **AC-1: CSV ingestion with correct types** — Given a valid CSV file with OpenFisca household outputs, when ingested through the adapter ingestion path, then population data is loaded into the internal schema (`pa.Table`) with correct types matching the declared schema.

2. **AC-2: Parquet ingestion parity** — Given a valid Parquet file containing the same data as a CSV, when ingested, then the resulting `pa.Table` is identical to the CSV ingestion result (same schema, same values, same row count).

3. **AC-3: Missing column error reporting** — Given a CSV or Parquet file with missing required columns, when ingested, then a clear error lists all missing column names in a single message (not one-at-a-time).

4. **AC-4: Type mismatch detection** — Given a CSV file where a column's values cannot be cast to the declared schema type, when ingested, then an error identifies the column name, expected type, and actual type.

5. **AC-5: Schema declaration** — Given an ingestion request, when a schema is provided, then only declared columns are loaded and type conversion is deterministic (no type inference).

6. **AC-6: Adapter path uses validated ingestion layer** — Given `OpenFiscaAdapter.compute()` for a period backed by CSV/Parquet files, when loading period files, then it uses the shared ingestion module with schema validation and preserves existing `ComputationResult` behavior/metadata.

## Tasks / Subtasks

- [x] Task 1: Define data ingestion types and schema contract (AC: 5)
  - [x] 1.1 Create `DataSchema` type wrapping `pa.Schema` with required/optional column metadata
  - [x] 1.2 Create `IngestionResult` type (table: `pa.Table`, source_path, format, row_count, metadata)
  - [x] 1.3 Create `IngestionError` exception with structured fields (missing_columns, type_mismatches, file_path)
  - [x] 1.4 Define default OpenFisca household output schema (household_id, income_tax, carbon_tax, etc.)

- [x] Task 2: Implement CSV ingestion (AC: 1, 3, 4, 5)
  - [x] 2.1 Implement `ingest_csv(path, schema) -> IngestionResult` function
  - [x] 2.2 Use `pyarrow.csv.read_csv()` with `ConvertOptions(column_types=..., include_columns=..., include_missing_columns=False)`
  - [x] 2.3 Validate required columns before reading (pre-flight check via header scan or ConvertOptions enforcement)
  - [x] 2.4 Report all missing columns in a single error (not fail-on-first)
  - [x] 2.5 Handle type conversion failures with actionable error messages

- [x] Task 3: Implement Parquet ingestion (AC: 2, 3, 4, 5)
  - [x] 3.1 Implement `ingest_parquet(path, schema) -> IngestionResult` function
  - [x] 3.2 Use `pyarrow.parquet.read_schema()` for pre-flight schema validation
  - [x] 3.3 Use `pyarrow.parquet.read_table()` with explicit schema
  - [x] 3.4 Validate column presence and types against declared schema
  - [x] 3.5 Ensure output is identical to CSV ingestion for the same data

- [x] Task 4: Implement unified ingestion entry point (AC: 1, 2)
  - [x] 4.1 Implement `ingest(path, schema) -> IngestionResult` that auto-detects format from file extension
  - [x] 4.2 Support `.csv`, `.csv.gz` (compressed CSV), `.parquet`, `.pq` extensions
  - [x] 4.3 Raise clear error for unsupported file extensions

- [x] Task 5: Write tests (AC: 1, 2, 3, 4, 5)
  - [x] 5.1 CSV round-trip test: write fixture data to CSV, ingest, verify schema and values
  - [x] 5.2 Parquet round-trip test: write fixture data to Parquet, ingest, verify schema and values
  - [x] 5.3 CSV/Parquet parity test: same data in both formats produces identical `pa.Table`
  - [x] 5.4 Missing columns test: CSV missing required columns raises `IngestionError` listing all missing
  - [x] 5.5 Missing columns test (Parquet): same as 5.4 for Parquet
  - [x] 5.6 Type mismatch test: CSV with wrong types raises error with column name + expected vs actual
  - [x] 5.7 Schema enforcement test: extra columns in file are excluded from result
  - [x] 5.8 Empty file test: CSV/Parquet with headers but no rows produces empty table with correct schema
  - [x] 5.9 Unsupported format test: `.xlsx` raises clear error
  - [x] 5.10 IngestionResult metadata test: verify source_path, format, row_count populated
  - [x] 5.11 Compressed CSV test: `.csv.gz` is read and produces identical output to `.csv`
  - [x] 5.12 Adapter integration regression: `OpenFiscaAdapter.compute()` still passes existing CSV/Parquet tests while using ingestion module

- [x] Task 6: Integrate ingestion into adapter path safely (AC: 6)
  - [x] 6.1 Update `OpenFiscaAdapter._load_period_file()` to delegate file reads to `ingestion.ingest()`/`ingestion.ingest_*()`
  - [x] 6.2 Preserve period-based file discovery (`{period}.csv`, `{period}.parquet`) and existing metadata contract
  - [x] 6.3 Update `openfisca_adapter.pyi` signatures/types if needed
  - [x] 6.4 Keep backward compatibility with all existing Story 1.1 tests

## Dev Notes

### Architecture Compliance

- **Module location:** `src/reformlab/computation/` — ingestion is part of the computation subsystem per architecture doc. The architecture places CSV/Parquet ingestion in `computation/` ("Handles CSV/Parquet ingestion of OpenFisca outputs"), not in `data/` (which is for open-data pipelines, Story 1.4).
- **Core data type:** `pa.Table` (PyArrow) — established in Story 1.1. Do NOT introduce pandas or polars as dependencies. Convert at interface boundaries only if needed.
- **Immutable data:** Follow Story 1.1 pattern — use `@dataclass(frozen=True)` for all new types.
- **Structural typing:** Follow `@runtime_checkable Protocol` pattern if defining any interfaces.
- **Type stubs:** Create `.pyi` files for all new public modules (PEP 561, established in Story 1.1).
- **Package exports:** Add new public types to `src/reformlab/computation/__init__.py` with `__all__`.

### Existing Code to Build On (from Story 1.1)

**DO NOT recreate these — they already exist:**
- `ComputationAdapter` protocol in `adapter.py`
- `OpenFiscaAdapter` in `openfisca_adapter.py` — already reads CSV/Parquet via `_load_period_file()` using `pyarrow.csv.read_csv()` and `pyarrow.parquet.read_table()`
- `PopulationData` (frozen dataclass, wraps `dict[str, pa.Table]`)
- `ComputationResult` (frozen dataclass with `output_fields: pa.Table`)
- `PolicyConfig`, `CompatibilityError`, `OutputFields` type alias
- `MockAdapter` with call logging

**Relationship to OpenFiscaAdapter._load_period_file():**
Story 1.1's `OpenFiscaAdapter._load_period_file(period)` currently does basic CSV/Parquet loading by period number (`{period}.csv` or `{period}.parquet`). In this story, integrate that path with the new ingestion module so BKL-102's "ingested through the adapter" acceptance criteria is actually met. Keep behavior backward-compatible and do NOT break existing tests (37 tests passing).

### Technical Requirements

- **Python 3.13+** — use modern syntax (`str | Path`, `dict[str, Any]`, no `Optional[]`)
- **PyArrow >= 18.0.0** — use `pyarrow.csv.ConvertOptions` for schema enforcement:
  - `column_types={field.name: field.type for field in schema}` — disables type inference
  - `include_columns=[field.name for field in schema]` — excludes extra columns
  - `include_missing_columns=False` — raises error on missing columns
- **Parquet schema validation:** Use `pq.read_schema(path)` for pre-flight check before `pq.read_table()`
- **Deterministic types:** Never rely on type inference. Always pass explicit schema.
- **No pandas/polars:** Core types are `pa.Table`. No DataFrame conversions.
- **Dependency alignment:** Update `pyproject.toml` minimum `pyarrow` version to `>=18.0.0` so runtime constraints match implementation requirements.

### Library Versions (Latest Stable as of 2026-02-25)

| Library | Version | Notes |
|---------|---------|-------|
| PyArrow | 23.0.1 | Latest on PyPI as of 2026-02-25. Pin `>=18.0.0` in this project for compatibility + security floor. |
| Python | 3.14.3 latest; project target `>=3.13` | Keep project compatibility target from `pyproject.toml` while allowing newer runtimes. |

**PyArrow CSV API (key parameters):**
```python
import pyarrow.csv as pcsv

table = pcsv.read_csv(
    path,
    read_options=pcsv.ReadOptions(use_threads=True),
    convert_options=pcsv.ConvertOptions(
        column_types=schema_dict,          # Explicit types, no inference
        include_columns=column_names,      # Only declared columns
        include_missing_columns=False,     # Error on missing columns
        check_utf8=True,                   # Validate string encoding
    ),
)
```

**PyArrow Parquet API (key parameters):**
```python
import pyarrow.parquet as pq

# Pre-flight schema check
file_schema = pq.read_schema(path)
# Compare against expected schema

# Read with explicit schema
table = pq.read_table(path, schema=expected_schema, columns=column_names)
```

### Performance Requirements

- 500k households on 16GB RAM must not crash
- 100k households in seconds (PyArrow single-shot `read_csv()` handles this easily — ~100 MB/s per core)
- Use `use_threads=True` for CSV reading (default)
- For files > 1GB, consider `pyarrow.csv.open_csv()` streaming reader (but not required for MVP scope)

### Testing Standards

- **Framework:** pytest with fixtures in `conftest.py`
- **Pattern:** Given/When/Then style docstrings (established in Story 1.1)
- **Fixtures:** Use `tmp_path` for temporary test files, `pa.table()` for fixture data
- **Mocking:** `unittest.mock.patch` for internal functions
- **Class-based test organization:** Group related tests in test classes
- **Test location:** `tests/computation/` (alongside existing tests)
- **All 37 existing tests must continue to pass**

### Error Design Principles (from Architecture & UX)

- Errors are **field-level and blocking** — contract failures stop processing
- Error format: **"[What failed] — [Why] — [How to fix]"**
- Report **all** validation failures at once, not one-at-a-time
- Missing columns: list all missing column names in a single error
- Type mismatches: report column name, expected type, actual type
- Never show raw exceptions or stack traces to the user
- Errors name the exact file path and issue

### Import Style (from Story 1.1)

```python
from __future__ import annotations      # Always first (PEP 563)

import time                              # stdlib
from pathlib import Path                 # stdlib

import pyarrow as pa                     # third-party
import pyarrow.csv as pcsv               # third-party
import pyarrow.parquet as pq             # third-party

from reformlab.computation.types import ComputationResult  # local
```

### Security Considerations

- CSV is inherently safe (no deserialization of binary objects)
- For Parquet: use `thrift_string_size_limit` and `thrift_container_size_limit` params as defense-in-depth
- Always validate schema before processing data
- Use `check_utf8=True` (default) in CSV ConvertOptions
- Never use IPC/Feather format for untrusted data
- Apache Arrow CVE-2023-47248 affected versions before 14.0.1; keep project floor at or above safe versions.

### Project Structure Notes

New files to create:
```
src/reformlab/computation/
  ingestion.py            # Core ingestion functions (ingest_csv, ingest_parquet, ingest)
  ingestion.pyi           # Type stubs

tests/computation/
  test_ingestion.py       # All ingestion tests
```

Files to modify:
```
src/reformlab/computation/__init__.py    # Add new exports
src/reformlab/computation/__init__.pyi   # Add new type stubs
src/reformlab/computation/openfisca_adapter.py  # Integrate ingestion path (backward compatible)
src/reformlab/computation/openfisca_adapter.pyi # Keep stubs aligned
pyproject.toml                           # Align pyarrow minimum version with story requirements
```

**DO NOT modify:**
- `types.py` — extend with new types if needed, but do not change existing types
- Any existing test files — all 37 tests must continue passing

### Cross-Story Dependencies

**This story blocks:**
- **Story 1.3** (input/output mapping) — needs validated ingestion to map OpenFisca variables
- **Story 1.4** (open-data pipeline) — directly depends on CSV/Parquet ingestion working
- **Story 1.5** (data quality checks) — extends validation at adapter boundary

**This story depends on:**
- **Story 1.1** (ComputationAdapter interface) — DONE. Provides types, patterns, and project structure.

### References

- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md — BKL-102, lines 82-85]
- [Source: _bmad-output/planning-artifacts/architecture.md — Data Contracts, lines 169-174]
- [Source: _bmad-output/planning-artifacts/architecture.md — Computation subsystem, line 153]
- [Source: _bmad-output/planning-artifacts/architecture.md — Technical Constraints, lines 66-72]
- [Source: _bmad-output/planning-artifacts/prd.md — FR1, FR3, NFR14]
- [Source: _bmad-output/planning-artifacts/prd.md — Memory management, line 311]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md — Error Handling, Data Errors section]
- [Source: _bmad-output/implementation-artifacts/1-1-define-computationadapter-interface-and-openfiscaadapter-implementation.md — All patterns]
- [Source: https://pypi.org/project/pyarrow/ — latest release metadata]
- [Source: https://docs.python.org/3/ — Python 3.14 docs landing page]
- [Source: https://www.apache.org/security/cve-2023-47248/ — Arrow security advisory]
- [Source: https://arrow.apache.org/docs/python/generated/pyarrow.csv.read_csv.html — `.csv.gz` support and CSV options]

### Git Intelligence Summary

- Recent commits indicate Story 1.1 established strict typing, stubs, and version-compatibility guardrails; keep the same rigor for ingestion.
- Current repo state shows Story 1.2 file already exists while sprint status still marks it backlog; this validation run synchronizes status to `ready-for-dev`.

### Project Context Reference

- No `project-context.md` file detected in repository search; fallback context sources used: PRD, architecture, backlog, UX spec, Story 1.1, and current codebase.

### Previous Story Intelligence (Story 1.1)

**Patterns to follow:**
- `@dataclass(frozen=True)` for immutable data types
- `@runtime_checkable Protocol` for interfaces (if any new ones needed)
- Explicit `__all__` in `__init__.py` for public API
- `.pyi` type stubs + `py.typed` marker (already exists)
- Given/When/Then docstrings in tests
- Fixtures with dependency injection in `conftest.py`
- `from __future__ import annotations` as first import

**Anti-patterns to avoid:**
- Do NOT use pandas or polars — `pa.Table` is the data type
- Do NOT use type inference — always pass explicit schemas
- Do NOT use permissive/unbounded version ranges for compatibility-sensitive contracts (e.g., OpenFisca adapter support); keep explicit allowlists where required
- Do NOT add OpenFisca as a hard dependency — it's optional
- Do NOT break the 37 existing tests

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Added `tests/computation/test_ingestion.py` first and confirmed red state (`ModuleNotFoundError` for missing ingestion module).
- Implemented ingestion module and adapter integration, then iterated on failures (Parquet API keyword support and output column ordering).
- Validation runs:
  - `pytest -q tests/computation/test_ingestion.py` -> 13 passed
  - `pytest -q` -> 50 passed
  - `mypy src` -> Success
  - `uv run ruff check` on changed files -> All checks passed
- Repository-wide `uv run ruff check .` still reports extensive pre-existing lint debt in generated `_bmad-output/presentations/` content unrelated to this story.

### Completion Notes List

- Implemented `src/reformlab/computation/ingestion.py` with:
  - `DataSchema`, `IngestionResult`, `TypeMismatch`, `IngestionError`
  - `DEFAULT_OPENFISCA_OUTPUT_SCHEMA`
  - `ingest_csv`, `ingest_parquet`, and unified `ingest` entry point
  - Required-column preflight checks, deterministic typed loading, missing-column aggregation, and structured type mismatch reporting
- Added type stubs in `src/reformlab/computation/ingestion.pyi`.
- Integrated `OpenFiscaAdapter._load_period_file()` to use shared ingestion path while preserving existing compute metadata/behavior.
- Updated package exports (`__init__.py` and `__init__.pyi`) and bumped `pyarrow` floor to `>=18.0.0` in `pyproject.toml`.
- Added comprehensive ingestion test coverage (12 ingestion cases + adapter integration regression) in `tests/computation/test_ingestion.py`.
- All acceptance criteria for Story 1.2 validated by passing test suite and static typing checks.

### File List

- pyproject.toml
- src/reformlab/computation/__init__.py
- src/reformlab/computation/__init__.pyi
- src/reformlab/computation/ingestion.py
- src/reformlab/computation/ingestion.pyi
- src/reformlab/computation/openfisca_adapter.py
- src/reformlab/computation/openfisca_adapter.pyi
- tests/computation/test_ingestion.py
- _bmad-output/implementation-artifacts/1-2-implement-csv-parquet-ingestion.md
- _bmad-output/implementation-artifacts/sprint-status.yaml

### Change Log

- 2026-02-25: Implemented Story 1.2 ingestion module, adapter integration, tests, and dependency floor alignment; story moved to `review`.
- 2026-02-25: Code review (Claude Opus 4.6) — Fixed 6 issues: H-1 Parquet thrift security limits added, H-2 CSV type mismatch false positives eliminated, M-1 __init__.pyi converted to proper stub, M-3 Parquet type mismatch test added, M-4 corrupt gzip handling added. M-2 (metadata mutability) deferred for consistency with Story 1.1. 2 new tests added (52 total). Story moved to `done`.
