# Story 1.3: Build Input/Output Mapping Configuration for OpenFisca Variable Names

Status: done

<!-- Story context created by create-story workflow on 2026-02-25. Validated against backlog, architecture, PRD, UX spec, previous stories (1.1, 1.2), and current codebase (52 passing tests). -->

## Story

As a **policy analyst**,
I want to **map OpenFisca variable names to project schema field names through a YAML configuration file with validation and actionable error reporting**,
so that **adapter output fields are reliably translated to the internal schema used by downstream orchestration, indicators, and comparison workflows — without hardcoding variable names in application code**.

## Acceptance Criteria

Scope note: AC-1 through AC-3 are the required BKL-103 baseline. AC-4 through AC-7 are approved hardening/extensions that can be sequenced after baseline delivery if sprint capacity tightens.

1. **AC-1: YAML mapping load** — Given a YAML mapping configuration file, when loaded, then OpenFisca variable names are mapped to project schema field names with direction (input/output) and type information preserved.

2. **AC-2: Unknown variable error** — Given a mapping referencing an OpenFisca variable that does not exist in the adapter output, when validated against actual adapter output columns, then an error identifies the exact field name and suggests corrections (e.g., closest match from available columns).

3. **AC-3: Mapped field presence** — Given a valid mapping applied to adapter output, then all mapped fields are present in the result with correct values and renamed according to the mapping.

4. **AC-4: Bidirectional mapping** — Given a mapping configuration, when used for input preparation or output translation, then field names are correctly translated in both directions (OpenFisca → project schema for outputs, project schema → OpenFisca for inputs).

5. **AC-5: Schema validation on load** — Given a YAML mapping file, when loaded, then the file structure is validated against a defined schema with field-level errors identifying exact problems (missing required keys, invalid types, duplicate mappings).

6. **AC-6: Mapping composition** — Given multiple mapping files (e.g., base + extension), when loaded together, then mappings are merged with later files overriding earlier ones and conflicts reported explicitly.

7. **AC-7: Integration with existing adapter** — Given a mapping configuration, when `OpenFiscaAdapter.compute()` returns results, then mapping can be applied to rename output columns without breaking existing `ComputationResult` behavior or metadata.

## Tasks / Subtasks

- [x] Task 1: Define mapping data types (AC: 1, 5)
  - [x] 1.1 Create `FieldMapping` frozen dataclass: `openfisca_name: str`, `project_name: str`, `direction: Literal["input", "output", "both"]`, `pa_type: pa.DataType`, `description: str = ""`
  - [x] 1.2 Create `MappingConfig` frozen dataclass wrapping `tuple[FieldMapping, ...]` with lookup methods: `by_openfisca_name(name) -> FieldMapping | None`, `by_project_name(name) -> FieldMapping | None`, `input_mappings -> tuple[FieldMapping, ...]`, `output_mappings -> tuple[FieldMapping, ...]`
  - [x] 1.3 Create `MappingError` exception with structured fields: `file_path`, `summary`, `reason`, `fix`, `invalid_fields: tuple[str, ...]` — follow `IngestionError` pattern from Story 1.2
  - [x] 1.4 Define `MappingValidationResult` frozen dataclass: `warnings: tuple[str, ...]`, `errors: tuple[str, ...]`

- [x] Task 2: Implement YAML mapping loader (AC: 1, 5)
  - [x] 2.1 Implement `load_mapping(path: str | Path) -> MappingConfig` that reads YAML and returns validated config
  - [x] 2.2 Define YAML schema structure (see Dev Notes for expected format)
  - [x] 2.3 Validate on load: required keys (`version`, `mappings`), each mapping has `openfisca_name`, `project_name`, `direction`; `pa_type` string maps to valid `pa.DataType`
  - [x] 2.4 Detect duplicate mappings (same `openfisca_name` or same `project_name` mapped twice) and report all duplicates in one error
  - [x] 2.5 Report all validation errors at once (not fail-on-first), following Story 1.2 error aggregation pattern

- [x] Task 3: Implement mapping application functions (AC: 3, 4)
  - [x] 3.1 Implement `apply_output_mapping(table: pa.Table, config: MappingConfig) -> pa.Table` — renames columns from OpenFisca names to project names for output-direction mappings
  - [x] 3.2 Implement `apply_input_mapping(table: pa.Table, config: MappingConfig) -> pa.Table` — renames columns from project names to OpenFisca names for input-direction mappings
  - [x] 3.3 Both functions preserve columns not in the mapping (pass-through)
  - [x] 3.4 Both functions preserve table metadata and row count

- [x] Task 4: Implement mapping validation against actual data (AC: 2)
  - [x] 4.1 Implement `validate_mapping(config: MappingConfig, available_columns: tuple[str, ...]) -> MappingValidationResult` that checks output-direction mapped OpenFisca names exist in available columns
  - [x] 4.2 For unknown variables: compute closest match using `difflib.get_close_matches()` from stdlib and include suggestion in error
  - [x] 4.3 Report all unknown variables at once (not fail-on-first)

- [x] Task 5: Implement mapping composition (AC: 6)
  - [x] 5.1 Implement `merge_mappings(*configs: MappingConfig) -> MappingConfig` — later configs override earlier ones by `openfisca_name`
  - [x] 5.2 Log merge conflicts (same `openfisca_name` in multiple configs) as warnings with source file info
  - [x] 5.3 Implement `load_mappings(*paths: str | Path) -> MappingConfig` convenience function that loads multiple files and merges

- [x] Task 6: Write tests (AC: 1-7)
  - [x] 6.1 YAML load test: valid mapping file loads correctly with all fields
  - [x] 6.2 YAML validation test: missing required keys, invalid types, duplicate mappings all produce structured errors
  - [x] 6.3 Unknown variable test: mapping referencing nonexistent column produces error with closest-match suggestion
  - [x] 6.4 Output mapping test: `apply_output_mapping()` renames columns correctly, preserves unmapped columns
  - [x] 6.5 Input mapping test: `apply_input_mapping()` renames in reverse direction
  - [x] 6.6 Bidirectional test: round-trip mapping (apply output then input) restores original column names
  - [x] 6.7 Merge test: two mapping files merge with later overriding earlier
  - [x] 6.8 Merge conflict test: overlapping keys produce explicit warnings
  - [x] 6.9 Adapter integration test: `OpenFiscaAdapter.compute()` result + `apply_output_mapping()` produces correctly renamed table without breaking metadata
  - [x] 6.10 Empty mapping test: empty mapping config passes through all columns unchanged
  - [x] 6.11 Type coercion test: `pa_type` in mapping is respected when present
  - [x] 6.12 All 52 existing tests must continue to pass

- [x] Task 7: Package integration (AC: 7)
  - [x] 7.1 Add `pyyaml>=6.0.2` to `pyproject.toml` dependencies
  - [x] 7.2 Create `.pyi` type stubs for new module(s)
  - [x] 7.3 Add new public types to `src/reformlab/computation/__init__.py` with `__all__`
  - [x] 7.4 Update `src/reformlab/computation/__init__.pyi` stubs

## Dev Notes

### Architecture Compliance

- **Module location:** `src/reformlab/computation/` — mapping is part of the computation subsystem. The architecture doc (line 153) places variable name mapping alongside the adapter: "Handles CSV/Parquet ingestion of OpenFisca outputs and optional direct API orchestration. **Version-pinned contracts.**" Mapping configuration is the contract definition layer.
- **Core data type:** `pa.Table` (PyArrow) — established in Stories 1.1 and 1.2. All mapping operations input and output `pa.Table`. Do NOT introduce pandas or polars.
- **Immutable data:** Follow `@dataclass(frozen=True)` pattern from `types.py`, `ingestion.py`.
- **Type stubs:** Create `.pyi` files for all new public modules (PEP 561, established in Story 1.1).
- **Package exports:** Add new public types to `src/reformlab/computation/__init__.py` with `__all__`.

### YAML Mapping File Format

The mapping configuration uses this YAML structure:

```yaml
# reformlab-mapping.yaml
version: "1"
description: "Default OpenFisca-France to ReformLab mapping"

mappings:
  - openfisca_name: "impot_revenu_net"
    project_name: "income_tax"
    direction: "output"       # "input", "output", or "both"
    type: "float64"           # PyArrow type string
    description: "Net income tax per household"

  - openfisca_name: "taxe_carbone"
    project_name: "carbon_tax"
    direction: "output"
    type: "float64"
    description: "Carbon tax amount per household"

  - openfisca_name: "menage_id"
    project_name: "household_id"
    direction: "both"
    type: "int64"
    description: "Household identifier"
```

**Required keys per mapping entry:** `openfisca_name`, `project_name`, `direction`
**Optional keys:** `type` (defaults to `pa.utf8()` if omitted), `description`
**Top-level required keys:** `version`, `mappings`
**Top-level optional keys:** `description`

### Existing Code to Build On (from Stories 1.1 and 1.2)

**DO NOT recreate these — they already exist:**
- `ComputationAdapter` protocol in `adapter.py`
- `OpenFiscaAdapter` in `openfisca_adapter.py` — reads CSV/Parquet via `_load_period_file()` using the ingestion module
- `ComputationResult` (frozen dataclass with `output_fields: pa.Table`) in `types.py`
- `DataSchema`, `IngestionError`, `IngestionResult`, `TypeMismatch` in `ingestion.py`
- `DEFAULT_OPENFISCA_OUTPUT_SCHEMA` in `ingestion.py` — currently hardcoded schema with `income_tax`, `carbon_tax`, `household_id`, `person_id`
- `MockAdapter` with call logging in `mock_adapter.py`

**Key relationship:** `DEFAULT_OPENFISCA_OUTPUT_SCHEMA` in `ingestion.py` (lines 98-109) currently hardcodes the project-side field names. This story creates the configuration layer that makes these names configurable. The default schema remains as a fallback; the mapping layer sits on top of it to translate between OpenFisca's actual variable names and the project schema names.

**DO NOT modify `OpenFiscaAdapter.compute()` internals** for this story. The mapping layer is a separate concern that operates on the `ComputationResult.output_fields` table after compute returns. Integration with the adapter is done by composing `compute()` + `apply_output_mapping()`, not by embedding mapping logic inside the adapter.

### Technical Requirements

- **Python 3.13+** — use modern syntax (`str | Path`, `dict[str, Any]`, `Literal["input", "output", "both"]`)
- **PyYAML >= 6.0.2** — use `yaml.safe_load()` only (never `yaml.load()` with unsafe Loader)
- **PyArrow >= 18.0.0** — column renaming via `table.rename_columns(new_names)` or `table.drop(col).append_column(new_name, col_data)`; prefer `rename_columns()` for batch operations
- **No Pydantic** — keep validation logic simple with manual checks and structured error reporting. Pydantic adds a heavy dependency for a simple schema.
- **No pandas/polars** — all data stays as `pa.Table`
- **difflib** (stdlib) — use `difflib.get_close_matches()` for "did you mean?" suggestions on unknown variables

### PyArrow Column Renaming API

```python
import pyarrow as pa

# Batch rename (preferred — returns new table, immutable)
new_names = [mapping.get(name, name) for name in table.column_names]
renamed_table = table.rename_columns(new_names)

# Single column rename alternative
idx = table.schema.get_field_index("old_name")
renamed = table.set_column(idx, "new_name", table.column(idx))
```

**Use `rename_columns()`** — it's the idiomatic PyArrow batch rename. It takes a list of names positionally matching existing columns.

### PyYAML Safe Loading API

```python
import yaml
from pathlib import Path

def load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise MappingError(...)
    return data
```

**Always `yaml.safe_load()`** — never `yaml.load()` without SafeLoader. PyYAML 6.0+ defaults to SafeLoader but be explicit.

### PyArrow Type String Resolution

Map YAML `type` strings to PyArrow types:

```python
_PA_TYPE_MAP: dict[str, pa.DataType] = {
    "int8": pa.int8(),
    "int16": pa.int16(),
    "int32": pa.int32(),
    "int64": pa.int64(),
    "float16": pa.float16(),
    "float32": pa.float32(),
    "float64": pa.float64(),
    "string": pa.utf8(),
    "utf8": pa.utf8(),
    "bool": pa.bool_(),
    "boolean": pa.bool_(),
}
```

### Error Design Principles (from Architecture & UX)

- Errors are **field-level and blocking** — contract failures stop processing
- Error format: **"[What failed] — [Why] — [How to fix]"** (same as `IngestionError`)
- Report **all** validation failures at once, not one-at-a-time
- Unknown variables: suggest closest match from available columns
- Duplicate mappings: list all duplicate field names in a single error
- Never show raw exceptions or stack traces to the user
- Errors name the exact file path and issue

### Performance Requirements

- Mapping load and validation: < 100ms for typical files (10-100 mappings)
- `apply_output_mapping()`: zero-copy column rename via PyArrow (< 1ms for any table size)
- `validate_mapping()`: O(n*m) where n = mappings, m = available columns; acceptable for < 1000 mappings

### Testing Standards

- **Framework:** pytest with fixtures in `conftest.py`
- **Pattern:** Given/When/Then style docstrings (established in Story 1.1)
- **Fixtures:** Use `tmp_path` for temporary YAML files, `pa.table()` for fixture data
- **Test location:** `tests/computation/test_mapping.py`
- **All 52 existing tests must continue to pass**

### Import Style (from Story 1.1)

```python
from __future__ import annotations      # Always first (PEP 563)

import difflib                           # stdlib
from dataclasses import dataclass        # stdlib
from pathlib import Path                 # stdlib
from typing import Literal               # stdlib

import pyarrow as pa                     # third-party
import yaml                              # third-party

from reformlab.computation.types import ComputationResult  # local
```

### Security Considerations

- **YAML safety:** Always use `yaml.safe_load()` — never `yaml.load()` with arbitrary Loader. This prevents arbitrary code execution via YAML deserialization.
- **Path traversal:** Validate that mapping file paths are within expected directories before loading.
- **Type string injection:** Only accept type strings from the `_PA_TYPE_MAP` allowlist. Reject unknown type strings with a clear error listing valid options.

### Project Structure Notes

New files to create:
```
src/reformlab/computation/
  mapping.py              # Core mapping types and functions
  mapping.pyi             # Type stubs

tests/computation/
  test_mapping.py         # All mapping tests
```

Files to modify:
```
src/reformlab/computation/__init__.py    # Add new exports
src/reformlab/computation/__init__.pyi   # Add new type stubs
pyproject.toml                           # Add pyyaml dependency
```

**DO NOT modify:**
- `ingestion.py` — mapping is a separate concern layered on top of ingestion
- `openfisca_adapter.py` — mapping is applied after compute(), not inside it
- `types.py` — existing types are sufficient; add new types in `mapping.py`
- Any existing test files — all 52 tests must continue passing

### Cross-Story Dependencies

**This story blocks:**
- **Story 1.4** (open-data pipeline) — needs mapping to translate external dataset field names
- **Story 1.5** (data quality checks) — mapping errors are a form of data quality validation
- **Story 2.1** (scenario template schema) — templates reference mapped field names, not raw OpenFisca names

**This story depends on:**
- **Story 1.1** (ComputationAdapter interface) — DONE. Provides `ComputationResult`, `pa.Table` types.
- **Story 1.2** (CSV/Parquet ingestion) — DONE. Provides ingestion layer, `DataSchema`, error patterns.

### References

- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md — BKL-103, lines 54, 87-90]
- [Source: _bmad-output/planning-artifacts/architecture.md — Computation subsystem, line 153]
- [Source: _bmad-output/planning-artifacts/architecture.md — Data Contracts, lines 169-174]
- [Source: _bmad-output/planning-artifacts/architecture.md — Computation Adapter Pattern, lines 112-131]
- [Source: _bmad-output/planning-artifacts/prd.md — FR3: Map OpenFisca variables to project schema, line 490]
- [Source: _bmad-output/planning-artifacts/prd.md — FR4: Validate mapping/schema contracts, line 491]
- [Source: _bmad-output/planning-artifacts/prd.md — NFR4: YAML loading < 1 second, line 549]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md — Error Handling, Data Errors section]
- [Source: src/reformlab/computation/ingestion.py — IngestionError pattern, lines 77-95]
- [Source: src/reformlab/computation/openfisca_adapter.py — _load_period_file, lines 123-137]
- [Source: src/reformlab/computation/types.py — ComputationResult, lines 39-52]

### Previous Story Intelligence (Stories 1.1 and 1.2)

**Patterns to follow:**
- `@dataclass(frozen=True)` for all immutable data types
- Structured error class with `file_path`, `summary`, `reason`, `fix` fields (from `IngestionError`)
- Aggregate all errors before raising (never fail-on-first)
- Explicit `__all__` in `__init__.py` for public API
- `.pyi` type stubs + `py.typed` marker (already exists)
- Given/When/Then docstrings in tests
- `from __future__ import annotations` as first import

**Anti-patterns to avoid:**
- Do NOT use pandas or polars — `pa.Table` is the core data type
- Do NOT embed mapping logic inside `OpenFiscaAdapter` — keep it as a composable layer
- Do NOT use `yaml.load()` without SafeLoader
- Do NOT use Pydantic for validation — keep it lightweight with manual checks
- Do NOT hardcode OpenFisca variable names in application code — that's exactly what this story eliminates
- Do NOT break the 52 existing tests
- Do NOT modify `DEFAULT_OPENFISCA_OUTPUT_SCHEMA` — it remains as the fallback schema; mapping sits above it

**Lessons from Story 1.2 code review:**
- H-1: Add security limits on external data (applied Parquet thrift limits) — same principle: validate all YAML input strictly
- H-2: Eliminated false positive type mismatches by using proper type detection — apply same rigor to type string resolution in mapping
- M-1: Type stubs must be proper stubs (not full implementations) — `.pyi` files should only contain signatures

### Git Intelligence Summary

- 2 commits in repo: initial BMAD setup + BMAD in-progress
- Story 1.1 established project scaffold, `pyproject.toml`, src layout, `py.typed` marker
- Story 1.2 added ingestion module with structured errors, type stubs, and security limits
- Current test count: 52 passing tests (37 from 1.1 + 15 from 1.2 including adapter integration regression)
- Linting: `ruff check` passes on all src/tests files
- Static typing: `mypy src` passes in strict mode

### Project Context Reference

- No `project-context.md` file in repository; context sourced from PRD, architecture, backlog, UX spec, Stories 1.1/1.2, and current codebase.

### Latest Tech Information

| Library | Latest Stable | Project Pin | Notes |
|---------|--------------|-------------|-------|
| PyYAML | 6.0.3 (Sep 2025) | `>=6.0.2` | Python 3.14 support. No security advisories. Always use `safe_load()`. |
| PyArrow | 23.0.1 | `>=18.0.0` | `rename_columns()` available since v1.0. No breaking changes relevant to mapping. |
| Python | 3.14.3 latest | `>=3.13` | Project targets 3.13+. |

**PyYAML notes:**
- `yaml.safe_load()` is the only safe parsing function — avoids arbitrary object instantiation
- Returns `dict`, `list`, `str`, `int`, `float`, `bool`, `None` only
- No schema validation built-in — validation must be done manually after loading

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Story context generated and validated on 2026-02-25 (GPT-5 Codex).
- Re-validation pass completed on 2026-02-25 after story content was populated.
- Implementation started on 2026-02-25 (Claude Opus 4.6).
- Fixed `rename_columns()` not preserving schema metadata — added `_rename_table()` helper that re-applies metadata after rename.

### Implementation Plan

- Created `mapping.py` module with all data types, YAML loader, mapping application functions, validation, and composition in a single cohesive module.
- Followed red-green-refactor cycle: wrote 38 failing tests first, then implemented to make them pass, then refactored for lint/type compliance.
- Used `_PA_TYPE_MAP` allowlist for type string resolution (security: rejects unknown types).
- Used `yaml.safe_load()` exclusively (security: no arbitrary code execution).
- Used `difflib.get_close_matches()` for "did you mean?" suggestions on unknown variables.
- Used `rename_columns()` with metadata preservation for zero-copy column renaming.
- Error aggregation: all validation errors collected and reported at once (not fail-on-first).

### Completion Notes List

- All 7 tasks and 30 subtasks completed and verified.
- All 7 acceptance criteria satisfied (AC-1 through AC-7).
- 42 new tests added in `tests/computation/test_mapping.py` (including post-review remediation tests).
- All 94 tests pass (52 existing + 42 new) — zero regressions.
- `uv run ruff check src tests` passes on all source and test files.
- `mypy src/` passes in strict mode (9 source files).
- Post-review remediation fixed AC-2 validation scope, type coercion behavior, source-aware merge warnings, and mapping path safety checks.

### File List

New files:

- `src/reformlab/computation/mapping.py` — Core mapping types, YAML loader, application functions, validation, composition
- `src/reformlab/computation/mapping.pyi` — Type stubs for mapping module
- `tests/computation/test_mapping.py` — 42 tests covering all acceptance criteria and review regressions

Modified files:

- `src/reformlab/computation/__init__.py` — Added mapping exports to `__all__`
- `src/reformlab/computation/__init__.pyi` — Added mapping type stub re-exports
- `pyproject.toml` — Added `pyyaml>=6.0.2` to dependencies
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — Status updated to done
- `_bmad-output/implementation-artifacts/1-3-build-input-output-mapping-configuration.md` — This story file

### Senior Developer Review (AI)

- Reviewer: GPT-5 Codex
- Date: 2026-02-25
- Outcome: Changes Requested → Fixed → Approved
- Findings resolved:
  - `validate_mapping()` now validates only output-direction mappings against adapter output columns (fixes AC-2 false positives).
  - `apply_output_mapping()` and `apply_input_mapping()` now enforce configured `pa_type` via safe column casting.
  - `merge_mappings()` conflict warnings now include source file paths from loaded mapping configs.
  - `load_mapping()` now resolves and validates mapping file paths against allowed roots to reduce path traversal risk.
  - Story/task claims aligned with implementation and regression tests.
- Verification run:
  - `uv run ruff check src tests`
  - `mypy src`
  - `pytest -q` (94 passed)

## Change Log

- 2026-02-25: Implemented Story 1.3 — YAML-based input/output mapping configuration for OpenFisca variable names. Added `mapping.py` module with `FieldMapping`, `MappingConfig`, `MappingError`, `MappingValidationResult` types; `load_mapping()`, `load_mappings()` YAML loaders with schema validation and error aggregation; `apply_output_mapping()`, `apply_input_mapping()` column rename functions preserving metadata; `validate_mapping()` with closest-match suggestions; `merge_mappings()` for mapping composition. 38 new tests, all 90 tests passing.
- 2026-02-25: Post-review remediation pass. Fixed `validate_mapping()` direction scope (output mappings only), implemented mapped-column type coercion, added merge-conflict source path reporting, enforced mapping-path safety checks, and added regression tests. Validation: Ruff + mypy + pytest (94 passed).
