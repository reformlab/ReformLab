# Story 1.7: Create Compatibility Matrix for Supported OpenFisca Versions

Status: review

<!-- Story context reviewed and corrected on 2026-02-26 against backlog BKL-107, PRD (NFR15, NFR21), architecture constraints, current codebase, test baseline, and PyPI release metadata. -->

## Story

As a platform developer/analyst,
I want a machine-readable compatibility matrix documenting which OpenFisca-Core versions are supported,
so that version-checking logic has a single authoritative source and users get clear guidance for supported, unsupported, and untested versions.

## Acceptance Criteria

1. Given the compatibility matrix, when a caller queries a specific OpenFisca version, then the system returns structured compatibility info with status (`supported`, `untested`, or `unsupported`) and guidance.
2. Given an installed OpenFisca version that is not `supported` in the matrix, when an adapter is initialized with version checks enabled, then `CompatibilityError` is raised with actionable guidance and a link to the compatibility matrix.
3. The matrix is stored as a structured YAML file (`src/reformlab/computation/compat_matrix.yaml`) and is the single source of truth for supported-version policy.
4. `openfisca_common.py` no longer hardcodes a static `SUPPORTED_VERSIONS` list; it derives compatibility data from the matrix loader while preserving `_detect_openfisca_version()` and `_check_version(actual: str)` behavior and signatures.
5. A public function `get_compatibility_info(version: str) -> CompatibilityInfo` returns structured compatibility details (status, tested modes, known issues, tested date, guidance).
6. Matrix entries include per-version metadata: adapter modes tested (`pre-computed`, `api`), known issues, tested date.
7. Existing behavior and external import expectations are preserved: current adapter/tests that import compatibility symbols from `openfisca_adapter.py` continue to work.
8. All existing tests remain green with no regressions, and new matrix tests pass (`uv run pytest -q` currently reports 170 passing tests before this story).
9. `COMPAT_MATRIX_URL` points to project-owned compatibility documentation (repo/docs) instead of the upstream OpenFisca changelog.

## Tasks / Subtasks

- [x] Task 1: Create compatibility matrix data model and YAML file (AC: 1, 3, 6)
  - [x] 1.1 Create `src/reformlab/computation/compat_matrix.yaml` with top-level keys: `schema_version`, `matrix_url`, `min_supported`, `versions`.
  - [x] 1.2 Add explicit entries for currently supported versions in code (`44.0.0`, `44.0.1`, `44.1.0`, `44.2.0`, `44.2.1`, `44.2.2`) as `supported`.
  - [x] 1.3 Add known newer-but-unlisted 44.x releases (for example `44.0.3`, `44.0.4`) as `untested` unless validated during implementation.
  - [x] 1.4 Add clear guidance for unsupported 43.x usage and missing/unlisted versions.

- [x] Task 2: Implement matrix loader and query API (AC: 1, 3, 5, 6)
  - [x] 2.1 Create `src/reformlab/computation/compat_matrix.py` with cached YAML loading.
  - [x] 2.2 Define frozen dataclass `CompatibilityInfo` with required structured fields.
  - [x] 2.3 Implement `get_compatibility_info(version: str) -> CompatibilityInfo`.
  - [x] 2.4 Implement defensive validation for malformed YAML or missing required keys.

- [x] Task 3: Refactor OpenFisca version checks to matrix source of truth (AC: 2, 4, 7, 9)
  - [x] 3.1 Update `src/reformlab/computation/openfisca_common.py` to read supported policy from matrix loader.
  - [x] 3.2 Keep `_check_version()` strict (non-supported versions fail with `CompatibilityError`) to preserve version-pinned adapter behavior.
  - [x] 3.3 Update `COMPAT_MATRIX_URL` to project docs/repository path for matrix reference.
  - [x] 3.4 Ensure backward-compatible symbol access from `openfisca_adapter.py` remains intact for existing tests/importers.

- [x] Task 4: Update public API and stubs (AC: 5, 7)
  - [x] 4.1 Export `CompatibilityInfo`, `get_compatibility_info`, and loader helpers via `src/reformlab/computation/__init__.py` as appropriate.
  - [x] 4.2 Add/update stubs in `src/reformlab/computation/__init__.pyi`.
  - [x] 4.3 Create `src/reformlab/computation/compat_matrix.pyi`.

- [x] Task 5: Add tests for matrix behavior and regressions (AC: 1, 2, 5, 7, 8)
  - [x] 5.1 Add `tests/computation/test_compat_matrix.py` for loader, schema validation, and query behavior.
  - [x] 5.2 Extend/adjust `tests/computation/test_version.py` to verify matrix-driven behavior and unchanged error contract.
  - [x] 5.3 Test unknown/unlisted versions and unsupported versions produce expected guidance and matrix URL.
  - [x] 5.4 Add regression test that existing import path expectations (`openfisca_adapter` exports) still hold.

- [x] Task 6: Packaging and distribution safety (AC: 3)
  - [x] 6.1 Ensure `compat_matrix.yaml` is included in built distributions for Hatchling-based packaging.
  - [x] 6.2 Add a packaging/resource-access test (for example via `importlib.resources`) so missing data files fail CI.

- [x] Task 7: Quality gates (AC: 8)
  - [x] 7.1 `uv run ruff check src tests`
  - [x] 7.2 `uv run mypy src`
  - [x] 7.3 `uv run pytest -q`

## Dev Notes

### Critical Consistency Rules

- Current code has strict version validation in `openfisca_common.py` and adapters rely on that contract. Keep strict behavior for runtime adapter initialization.
- Do not introduce network calls for version checks. Compatibility resolution must be local-file based to preserve offline operation expectations.
- Do not change signatures of `_detect_openfisca_version()` or `_check_version()`.
- Do not change `CompatibilityError(expected, actual, details)` constructor contract.

### Architecture and Structure Constraints

- Keep compatibility logic in `src/reformlab/computation/`.
- Keep data model immutable (`@dataclass(frozen=True)` pattern) for public result objects.
- Keep stubs aligned with Python modules (`.pyi` parity).
- Avoid circular imports between `openfisca_common.py`, `openfisca_adapter.py`, and `compat_matrix.py`.

### Implementation Guidance

- Matrix file should be parsed once and cached; provide explicit cache invalidation helper for tests.
- Normalize version strings before lookup when practical (trim whitespace; reject clearly invalid semantic version strings with explicit guidance).
- For versions absent from matrix, return `untested` in query API, but keep runtime adapter checks strict unless explicitly configured otherwise.
- Keep guidance messages concise and actionable: expected range/list, detected version, and link to matrix docs.

### Files Expected to Change

Create:

- `src/reformlab/computation/compat_matrix.yaml`
- `src/reformlab/computation/compat_matrix.py`
- `src/reformlab/computation/compat_matrix.pyi`
- `tests/computation/test_compat_matrix.py`

Modify:

- `src/reformlab/computation/openfisca_common.py`
- `src/reformlab/computation/openfisca_adapter.py` (only as needed for compatibility exports)
- `src/reformlab/computation/__init__.py`
- `src/reformlab/computation/__init__.pyi`
- `tests/computation/test_version.py`
- `pyproject.toml` (only if explicit Hatchling include settings are required after verification)

### Anti-Patterns to Avoid

- Do not keep duplicate hardcoded version lists in multiple modules.
- Do not silently treat unknown runtime versions as supported.
- Do not make compatibility behavior depend on OpenFisca being importable at module-import time.
- Do not break existing `openfisca_adapter` import surface used by tests and downstream code.

### Previous Story Intelligence (1-6)

Story 1-6 centralized version checks into `openfisca_common.py` and both adapters now depend on that shared module. The key continuity requirement is to keep one compatibility policy source while preserving the existing strict runtime contract and import paths.

### Project Context Reference

No `project-context.md` file was found in the repository during this review; story context is derived from planning artifacts, implementation artifacts, and current source code.

### References

- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-107]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR15]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR21]
- [Source: _bmad-output/planning-artifacts/prd.md#Technical-Risks]
- [Source: _bmad-output/planning-artifacts/architecture.md#Subsystems]
- [Source: src/reformlab/computation/openfisca_common.py]
- [Source: src/reformlab/computation/openfisca_adapter.py]
- [Source: src/reformlab/computation/exceptions.py]
- [Source: tests/computation/test_version.py]
- [Source: _bmad-output/implementation-artifacts/1-6-add-direct-openfisca-api-orchestration-mode.md]

### Latest Technical Information (Verified 2026-02-26)

- OpenFisca-Core latest on PyPI: `44.2.2` (release timestamp: 2026-02-19T15:55:40Z)
- Recent OpenFisca-Core releases include: `44.0.3`, `44.0.4`, `44.1.0`, `44.2.0`, `44.2.1`, `44.2.2`
- Project optional dependency remains `openfisca-core>=44.0.0`
- Project dependencies include `pyyaml>=6.0.2` (latest on PyPI: `6.0.3`) and `pyarrow>=18.0.0` (latest on PyPI: `23.0.1`)
- Current local baseline test suite before this story implementation: `170 passed`

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Story review pass completed in-place with artifact and codebase consistency checks.
- Implementation completed in single session with red-green-refactor cycle.

### Implementation Plan

1. Created YAML compatibility matrix with schema_version, matrix_url, min_supported, and per-version entries (supported/untested status, modes_tested, known_issues, tested_date, guidance).
2. Implemented `compat_matrix.py` with `CompatibilityInfo` frozen dataclass, cached `load_matrix()`, and `get_compatibility_info()` query API with semver comparison for unlisted versions.
3. Refactored `openfisca_common.py` to derive `SUPPORTED_VERSIONS`, `MIN_SUPPORTED`, and `COMPAT_MATRIX_URL` from the matrix loader instead of hardcoded constants. Preserved `_check_version()` and `_detect_openfisca_version()` signatures.
4. Exported new symbols via `__init__.py` and created matching `.pyi` stubs.
5. Added comprehensive tests: 25 in `test_compat_matrix.py` (loader, query, malformed YAML, packaging resource access) and 10 new in `test_version.py` (matrix-driven checks, import path regressions).

### Completion Notes List

- Resolved AC contradictions around warning vs strict version checks.
- Updated test baseline references from 167 to 170 current passing tests.
- Corrected packaging guidance for this Hatchling-based project.
- Added explicit backward-compatibility requirement for `openfisca_adapter` compatibility symbol imports.
- Added verified latest-version metadata timestamped to 2026-02-26.
- Implementation: YAML matrix is single source of truth; `openfisca_common.py` no longer hardcodes version list.
- All 9 acceptance criteria satisfied. Quality gates: ruff clean, mypy clean (17 files), 205 tests pass (170 baseline + 35 new).
- `openfisca_adapter.py` re-exports (`SUPPORTED_VERSIONS`, `MIN_SUPPORTED`, `COMPAT_MATRIX_URL`, `_check_version`, `_detect_openfisca_version`) preserved — no downstream breakage.
- `COMPAT_MATRIX_URL` now points to project-owned docs URL instead of upstream OpenFisca changelog.
- Untested versions (44.0.3, 44.0.4) included in matrix; unlisted versions >= min_supported return "untested" from query API but are rejected by strict runtime `_check_version()`.

### File List

- `src/reformlab/computation/compat_matrix.yaml` (created)
- `src/reformlab/computation/compat_matrix.py` (created)
- `src/reformlab/computation/compat_matrix.pyi` (created)
- `src/reformlab/computation/openfisca_common.py` (modified)
- `src/reformlab/computation/__init__.py` (modified)
- `src/reformlab/computation/__init__.pyi` (modified)
- `tests/computation/test_compat_matrix.py` (created)
- `tests/computation/test_version.py` (modified)
- `_bmad-output/implementation-artifacts/1-7-create-compatibility-matrix.md` (updated)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (updated)

## Change Log

- 2026-02-26: Implemented compatibility matrix (Story 1-7). Created YAML matrix as single source of truth for supported OpenFisca versions. Added `compat_matrix.py` with `CompatibilityInfo` dataclass and query API. Refactored `openfisca_common.py` to derive version policy from matrix. Added 35 new tests (25 matrix + 10 version). All quality gates pass (ruff, mypy, 205 pytest).
