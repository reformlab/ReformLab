# Story 1.5: Add Data-Quality Checks with Blocking Field-Level Errors at Adapter Boundary

Status: review

<!-- Story context refreshed on 2026-02-25 using backlog BKL-105, architecture, PRD, UX error-handling standards, previous stories 1.1-1.4, current codebase, local test baseline, and current package/version checks. -->

## Story

As a **policy analyst**,
I want **the system to validate computation adapter output for null values in required fields and type mismatches, with exact field-level and row-level diagnostics**,
so that **corrupted or incomplete computation results never silently propagate into orchestration, indicators, or governance outputs**.

## Acceptance Criteria

1. **AC-1: Null detection in required fields**
   Given adapter output (`ComputationResult.output_fields`) with a null value in a required field, when validated, then a blocking error identifies the exact field name and row indices containing nulls.

2. **AC-2: Type mismatch detection**
   Given adapter output with columns whose types do not match the expected schema, when validated, then each mismatch is reported with column name, expected type, and actual type.

3. **AC-3: Missing required column detection**
   Given adapter output missing one or more required columns declared in `DataSchema.required_columns`, when validated, then a blocking error identifies all missing columns in one result.

4. **AC-4: Silent pass for valid output**
   Given valid adapter output (required columns present, no nulls in required fields, matching types), when validated, then checks pass silently and the validated result is returned for downstream use.

5. **AC-5: Multi-error aggregation**
   Given adapter output with multiple issues (nulls and type mismatches and/or missing required columns), when validated, then all blocking issues are reported together in a single `DataQualityError` (not fail-on-first).

6. **AC-6: Value range warnings (non-blocking extension)**
   Given adapter output with anomalous values (for example negative income, tax rates above 100%), when validated with range rules, then warnings are emitted without blocking execution. Warnings include field name, violated bound, and affected row count.

## Tasks / Subtasks

- [x] Task 1: Create quality-check domain types and exception (AC: 1, 2, 3, 5, 6)
  - [x] 1.1 Add `QualityIssue` frozen dataclass with fields: `field`, `issue_type`, `message`, `row_indices`, `expected`, `actual`
  - [x] 1.2 Add `QualityCheckResult` frozen dataclass with fields: `passed`, `errors`, `warnings`, `checked_columns`, `row_count`
  - [x] 1.3 Add `RangeRule` frozen dataclass with fields: `field`, `min_value`, `max_value`, `description`
  - [x] 1.4 Add `DataQualityError(Exception)` carrying a `QualityCheckResult` and formatting a concise multi-line summary

- [x] Task 2: Implement null and missing-column checks (AC: 1, 3, 5)
  - [x] 2.1 Implement `_check_missing_required_columns(table, schema)` returning blocking `QualityIssue` entries
  - [x] 2.2 Implement `_check_nulls(table, required_columns)` using `pyarrow.compute.is_null`
  - [x] 2.3 Return capped row index samples (`<= 10`) plus total affected counts in the issue message

- [x] Task 3: Implement type check (AC: 2, 5)
  - [x] 3.1 Implement `_check_types(table, expected_schema, columns)`
  - [x] 3.2 Compare with `pa.DataType.equals()` (never string-only comparison)
  - [x] 3.3 Report one issue per mismatched column with expected/actual values

- [x] Task 4: Implement optional range-warning check (AC: 6)
  - [x] 4.1 Implement `_check_ranges(table, range_rules)` using `pc.less` / `pc.greater`
  - [x] 4.2 Emit warnings only; do not convert range anomalies into blocking errors
  - [x] 4.3 Handle nullable numeric columns safely (nulls ignored by range comparisons)

- [x] Task 5: Implement orchestration function (AC: 1-6)
  - [x] 5.1 Implement `validate_output(result: ComputationResult, schema: DataSchema, *, range_rules: tuple[RangeRule, ...] = ()) -> QualityCheckResult`
  - [x] 5.2 Run checks in this order: missing required columns -> nulls -> types -> ranges
  - [x] 5.3 Aggregate all blocking issues and all warnings
  - [x] 5.4 Raise `DataQualityError` when blocking issues exist; otherwise return `QualityCheckResult(passed=True, ...)`

- [x] Task 6: Package integration (AC: all)
  - [x] 6.1 Create `src/reformlab/computation/quality.py`
  - [x] 6.2 Create `src/reformlab/computation/quality.pyi`
  - [x] 6.3 Export new public API from `src/reformlab/computation/__init__.py`
  - [x] 6.4 Export stubs in `src/reformlab/computation/__init__.pyi`

- [x] Task 7: Tests and regression safety (AC: 1-6)
  - [x] 7.1 Add `tests/computation/test_quality.py` with dedicated unit tests for each AC
  - [x] 7.2 Cover multi-error aggregation and missing-required-column behavior
  - [x] 7.3 Cover range-warning-only path and mixed warning+error path
  - [x] 7.4 Verify empty-table behavior and bounded row-index diagnostics
  - [x] 7.5 Ensure all existing tests remain green (`uv run pytest -q`)

## Dev Notes

### Scope Boundaries (Critical)

- This story introduces **adapter-output validation utilities** only.
- Do **not** wire quality checks into orchestrator runtime here; integration call sites are deferred to later orchestration stories.
- Do **not** modify existing ingestion behavior (`ingest_*`) beyond public exports.

### Architecture Compliance

- Implement in `src/reformlab/computation/quality.py` (adapter contract boundary).
- Keep data model immutable with `@dataclass(frozen=True)`.
- Use PyArrow tables and compute kernels only; no pandas/polars.
- Keep error messages actionable in the project’s structured error style: `[summary] - [reason] - [fix]`.

### Reuse Existing Implementation Patterns

- Reuse `DataSchema` and `TypeMismatch` concepts from `computation.ingestion`.
- Reuse `ComputationResult` from `computation.types` as validator input.
- Follow export and stub conventions from `computation/__init__.py` and `.pyi`.
- Follow test style and fixture conventions used in `tests/computation/`.

### Required Behavior Details

- **Missing required columns:** return one blocking issue per missing field or a consolidated issue with all missing names; either is acceptable if deterministic and fully test-covered.
- **Null checks:** only required columns are blocking; optional-column nulls are non-blocking.
- **Type checks:** compare declared vs actual PyArrow data types with `.equals()`.
- **Aggregation:** never stop at first error.
- **Diagnostics:** include field names and row-index samples, but cap index list at 10 to avoid oversized errors.
- **Warnings:** range warnings are informational/non-blocking and must still appear in `QualityCheckResult.warnings`.

### Suggested Public API

```python
@dataclass(frozen=True)
class QualityIssue: ...

@dataclass(frozen=True)
class QualityCheckResult: ...

@dataclass(frozen=True)
class RangeRule: ...

class DataQualityError(Exception):
    result: QualityCheckResult


def validate_output(
    result: ComputationResult,
    schema: DataSchema,
    *,
    range_rules: tuple[RangeRule, ...] = (),
) -> QualityCheckResult: ...
```

### Testing Requirements

- Add targeted tests for AC-1 through AC-6.
- Add regression tests for mixed-failure aggregation and missing-column detection.
- Validate that error payloads are programmatically inspectable (not string-only assertions).
- Run full quality gates after implementation:
  - `uv run ruff check src tests`
  - `uv run mypy src`
  - `uv run pytest -q`

### Project Structure Notes

Create:

- `src/reformlab/computation/quality.py`
- `src/reformlab/computation/quality.pyi`
- `tests/computation/test_quality.py`

Modify:

- `src/reformlab/computation/__init__.py` (exports)
- `src/reformlab/computation/__init__.pyi` (stub exports)

Do not modify unrelated modules (`mapping.py`, `mock_adapter.py`, `openfisca_adapter.py`, `data/*`) for this story.

### Dependencies and Sequencing

- Depends on completed stories 1.1 to 1.4.
- Unblocks tighter runtime guardrails in future orchestration and governance stories.

## References

- `_bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md` (BKL-105)
- `_bmad-output/planning-artifacts/architecture.md` (Subsystems, Data Contracts)
- `_bmad-output/planning-artifacts/prd.md` (FR4, FR27)
- `_bmad-output/planning-artifacts/ux-design-specification.md` (Error handling principles)
- `src/reformlab/computation/ingestion.py`
- `src/reformlab/computation/types.py`
- `src/reformlab/computation/__init__.py`
- `src/reformlab/computation/__init__.pyi`
- `_bmad-output/implementation-artifacts/1-4-implement-open-data-ingestion-pipeline.md`

## Latest Tech Information

- **PyArrow**
  - Local environment (`uv run python`): `23.0.1`
  - Project requirement: `pyarrow>=18.0.0`
  - PyPI latest checked on 2026-02-25: `23.0.1` (release date 2026-02-16)

- **Python**
  - Project requirement: `>=3.13`
  - Local `uv` interpreter: `3.13.0`
  - Python.org version index checked on 2026-02-25: latest 3.13 bugfix is `3.13.12` (released 2026-02-03)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Story refresh and issue remediation pass completed on 2026-02-25.
- Implementation completed on 2026-02-26. Fixed PyArrow segfault on empty tables by guarding `pc.is_null`/`pc.indices_nonzero` with `num_rows == 0` early return.

### Implementation Plan

- Created `quality.py` with four frozen dataclasses (`QualityIssue`, `QualityCheckResult`, `RangeRule`, `DataQualityError`) and four internal check functions (`_check_missing_required_columns`, `_check_nulls`, `_check_types`, `_check_ranges`), orchestrated by the public `validate_output()` function.
- Followed red-green-refactor: wrote 15 failing tests first, then implemented minimal code to pass, then refined empty-table guard.
- Used PyArrow compute kernels exclusively (`pc.is_null`, `pc.indices_nonzero`, `pc.less`, `pc.greater`, `pc.or_`, `pc.if_else`) — no pandas/polars.
- Error messages follow project structured style: `[summary] - [reason] - [fix]`.
- Row index samples capped at 10 to avoid oversized diagnostics.
- Null checks in `_check_ranges` safely handled via `pc.if_else(pc.is_null(...), False, ...)`.

### Completion Notes List

- Story guidance compressed for higher signal-to-token ratio.
- Acceptance criteria aligned with required-column behavior already implied by tests/tasks.
- Scope boundaries made explicit to prevent accidental orchestrator/ingestion refactors.
- Placeholder values removed and replaced with concrete values.
- All 7 tasks and 26 subtasks completed. 16 new tests added covering AC-1 through AC-6 plus edge cases.
- Full quality gates passed: ruff (0 errors), mypy (0 issues in 14 files), pytest (141 passed, 0 regressions).

### File List

- `src/reformlab/computation/quality.py` (created)
- `src/reformlab/computation/quality.pyi` (created)
- `src/reformlab/computation/__init__.py` (modified — added quality exports)
- `src/reformlab/computation/__init__.pyi` (modified — added quality stub exports)
- `tests/computation/test_quality.py` (created)
- `_bmad-output/implementation-artifacts/1-5-add-data-quality-checks.md` (updated)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (updated)

## Change Log

- 2026-02-26: Implemented data-quality validation module with null detection, type mismatch detection, missing column detection, multi-error aggregation, and range-warning checks. Added 15 unit tests. All quality gates pass.
- 2026-02-26: Hardened range-rule handling so non-numeric/incompatible bounds emit structured non-blocking warnings (`range_rule_invalid`) instead of raw Arrow exceptions; added regression test coverage.
