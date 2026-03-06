# Story 1.8: Set Up Project Scaffold, Dev Environment, and CI Smoke Pipeline

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer contributing to ReformLab**,
I want **a complete project scaffold with all architecture subsystem directories, reproducible dev environment, and a CI pipeline running lint + tests on every push**,
so that **new contributors can clone, install, and start developing immediately with quality gates enforced from day one**.

## Acceptance Criteria

1. Given a fresh clone of the repository, when `uv sync` is run, then all dependencies install and `pytest` runs successfully (207+ existing tests pass).
2. Given a push to the repository, when CI triggers, then ruff lint, mypy type checking, and pytest unit tests execute and report pass/fail.
3. Given the project directory structure, when inspected, then it matches the architecture subsystem layout with all 8 packages present: `computation/`, `data/`, `templates/`, `orchestrator/`, `vintage/`, `indicators/`, `governance/`, `interfaces/`.

## Tasks / Subtasks

- [x] Task 1: Create missing subsystem package directories (AC: #3)
  - [x] 1.1 Create `src/reformlab/templates/__init__.py`
  - [x] 1.2 Create `src/reformlab/orchestrator/__init__.py`
  - [x] 1.3 Create `src/reformlab/vintage/__init__.py`
  - [x] 1.4 Create `src/reformlab/indicators/__init__.py`
  - [x] 1.5 Create `src/reformlab/governance/__init__.py`
  - [x] 1.6 Create `src/reformlab/interfaces/__init__.py`
  - [x] 1.7 Create corresponding `tests/templates/__init__.py`, `tests/orchestrator/__init__.py`, etc.
- [x] Task 2: Verify dev environment reproducibility (AC: #1)
  - [x] 2.1 Run `uv sync` from clean state and confirm all deps install
  - [x] 2.2 Run `pytest` and confirm all 207+ existing tests pass
  - [x] 2.3 Run `ruff check src tests` and confirm zero errors
  - [x] 2.4 Run `mypy src` and confirm zero errors
- [x] Task 3: Create GitHub Actions CI workflow (AC: #2)
  - [x] 3.1 Create `.github/workflows/ci.yml` with lint + type-check + test jobs
  - [x] 3.2 Use `astral-sh/setup-uv@v7` for uv installation with caching
  - [x] 3.3 Target Python 3.13 matching `pyproject.toml` `requires-python`
  - [x] 3.4 Run `ruff check src tests` as lint step
  - [x] 3.5 Run `mypy src` as type-check step
  - [x] 3.6 Run `pytest tests` as test step
- [x] Task 4: Add scaffold smoke test (AC: #3)
  - [x] 4.1 Create `tests/test_scaffold.py` that imports all 8 subsystem packages
  - [x] 4.2 Verify each package is importable and the directory structure is correct

## Dev Notes

### Current State Analysis

The project already has significant infrastructure in place from stories 1-1 through 1-7:

**Already exists (DO NOT recreate):**
- `pyproject.toml` — fully configured with hatchling build, ruff, mypy, pytest settings
- `src/reformlab/__init__.py` — package root
- `src/reformlab/computation/` — 12 modules (adapter, types, ingestion, mapping, quality, compat_matrix, openfisca_adapter, openfisca_api_adapter, openfisca_common, mock_adapter, exceptions, plus YAML data file)
- `src/reformlab/data/` — 3 modules (pipeline, schemas, emission_factors)
- `src/reformlab/py.typed` — PEP 561 marker
- `.pyi` stub files for all existing modules
- `tests/computation/` — 14 test files with 207+ tests
- `tests/data/` — 2 test files plus conftest
- `tests/test_overnight_build.sh` — overnight build script
- `README.md`, `LICENSE`, `.gitignore`

**Missing (MUST create):**
- `src/reformlab/templates/` — empty package placeholder
- `src/reformlab/orchestrator/` — empty package placeholder
- `src/reformlab/vintage/` — empty package placeholder
- `src/reformlab/indicators/` — empty package placeholder
- `src/reformlab/governance/` — empty package placeholder
- `src/reformlab/interfaces/` — empty package placeholder
- `.github/workflows/ci.yml` — CI pipeline (no `.github/` directory exists yet)
- Corresponding `tests/` subdirectories for new packages

### Architecture Compliance

The 8-subsystem layout is defined in `_bmad-output/planning-artifacts/architecture.md`:

```
src/reformlab/
  computation/    # Adapter interface + OpenFiscaAdapter [EXISTS]
  data/           # Open data ingestion, synthetic population [EXISTS]
  templates/      # Environmental policy templates and scenario registry [CREATE]
  orchestrator/   # Dynamic yearly loop with step-pluggable pipeline [CREATE]
  vintage/        # Cohort/vintage state management [CREATE]
  indicators/     # Distributional, welfare, fiscal, custom indicators [CREATE]
  governance/     # Run manifests, assumption logs, lineage [CREATE]
  interfaces/     # Python API, notebooks, no-code GUI [CREATE]
```

### CI Pipeline Requirements

**GitHub Actions with uv** (per latest astral-sh docs):
- Action: `astral-sh/setup-uv@v7` (latest stable)
- Checkout: `actions/checkout@v6`
- Python: install via `uv python install 3.13` (matches pyproject.toml `requires-python = ">=3.13"`)
- Dependencies: `uv sync --locked --all-extras --dev`
  - NOTE: This requires a `uv.lock` file. If none exists, use `uv sync --all-extras --dev` (without `--locked`) or generate the lockfile first with `uv lock`.
- Caching: `enable-cache: true` in setup-uv action
- Steps: ruff check, mypy, pytest (in that order — fail fast on lint)
- Trigger: `on: [push, pull_request]` on all branches

**Ruff config** (already in pyproject.toml):
```toml
[tool.ruff]
src = ["src"]
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "W"]
```

**Mypy config** (already in pyproject.toml):
```toml
[tool.mypy]
python_version = "3.13"
mypy_path = "src"
strict = true
```

### Empty Package `__init__.py` Convention

Follow the existing pattern from `src/reformlab/data/__init__.py` — keep `__init__.py` files minimal. For placeholder packages, an empty file or a single-line docstring is appropriate. Do NOT add any code that doesn't exist yet — these are scaffolding placeholders for future epics.

### Testing Convention

Follow existing test structure:
- `tests/<subsystem>/__init__.py` — empty
- `tests/<subsystem>/conftest.py` — only if fixtures are needed (not needed for scaffold)
- Test naming: `test_<module>.py`
- The scaffold smoke test should be `tests/test_scaffold.py` at the root test level

### Critical Anti-Patterns to Avoid

1. **DO NOT modify any existing code** — stories 1-1 through 1-7 are done and working. This is additive only.
2. **DO NOT add stub implementations** in the new subsystem packages — they are placeholders only. Content comes in Epics 2-7.
3. **DO NOT add dependencies** to pyproject.toml — all needed deps are already listed.
4. **DO NOT create `.pyi` stub files** for empty packages — stubs follow implementation.
5. **DO NOT modify `pyproject.toml`** unless strictly necessary for CI (e.g., a missing tool config).
6. **DO NOT use `pip` or `pip install`** — this project uses `uv` exclusively.
7. **DO NOT use `--locked` flag if no `uv.lock` exists** — check first, generate if needed.

### Previous Story Patterns

From stories 1-5, 1-6, 1-7:
- **Frozen dataclasses** for all domain models
- **PyArrow-first** data handling (no pandas/polaris in production code)
- **Red-green-refactor TDD** — write failing tests first
- **Structured error messages** following `[summary] - [reason] - [fix]` pattern
- **Backward-compatible re-exports** to avoid import breakage
- **Hatchling packaging** with `packages = ["src/reformlab"]` in pyproject.toml

### Git Intelligence

Recent commits show the codebase is stable after 7 completed stories:
- `163cb01` — README, LICENSE, repo hygiene
- `0f61267` — Build test improvements
- `482d02b` — Story 1-7 completion
- `38bcbbc` — Compat matrix URL fix
- `d922d95` — Sprint status update

All tests pass. No known regressions. The codebase is ready for scaffolding.

### Project Structure Notes

- The `src/` layout with `src/reformlab/` is a standard src-layout Python project
- Hatchling builds from `packages = ["src/reformlab"]` — new subdirectories under `src/reformlab/` are automatically included
- Test discovery uses `testpaths = ["tests"]` with `pythonpath = ["src"]`
- New test subdirectories need `__init__.py` files for pytest discovery

### References

- [Source: _bmad-output/planning-artifacts/architecture.md] — 8 subsystem layout, layered architecture
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-108] — Story acceptance criteria, NFR18/NFR19 refs
- [Source: pyproject.toml] — Build system, tool configs, dependency list
- [Source: _bmad-output/implementation-artifacts/1-7-create-compatibility-matrix.md] — Latest patterns and conventions
- [Source: _bmad-output/implementation-artifacts/1-6-add-direct-openfisca-api-orchestration-mode.md] — Testing patterns
- [Source: _bmad-output/implementation-artifacts/1-5-add-data-quality-checks.md] — Quality and validation patterns
- [Source: https://docs.astral.sh/uv/guides/integration/github/] — uv GitHub Actions setup guide
- [Source: https://github.com/astral-sh/setup-uv] — setup-uv@v7 action

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- 2026-02-26: Confirmed missing scaffold packages via failing import probe (`ModuleNotFoundError` for `reformlab.templates`).
- 2026-02-26: Created six missing package directories and six matching test package directories with placeholder `__init__.py`.
- 2026-02-26: Ran environment and quality checks: `uv sync`, `uv run pytest`, `uv run ruff check src tests`, and `uv run mypy src`.
- 2026-02-26: Added CI workflow at `.github/workflows/ci.yml` and validated YAML parsing.
- 2026-02-26: Added scaffold smoke tests and validated with full regression run (`209 passed`), `ruff`, and `mypy`.

### Completion Notes List

- Implemented full project scaffold for six missing subsystem packages under `src/reformlab/` and matching `tests/` package folders.
- Added GitHub Actions CI pipeline using `actions/checkout@v6` and `astral-sh/setup-uv@v7` with cache enabled.
- Configured CI to install Python 3.13, sync dependencies with `uv sync --locked --all-extras --dev`, and run lint/type/test quality gates.
- Added smoke coverage in `tests/test_scaffold.py` for package importability and required eight-package directory structure.
- Verified acceptance criteria with successful local validation: `uv run pytest` (209 passed), `uv run ruff check src tests`, and `uv run mypy src`.

### File List

- .github/workflows/ci.yml
- src/reformlab/templates/__init__.py
- src/reformlab/orchestrator/__init__.py
- src/reformlab/vintage/__init__.py
- src/reformlab/indicators/__init__.py
- src/reformlab/governance/__init__.py
- src/reformlab/interfaces/__init__.py
- tests/templates/__init__.py
- tests/orchestrator/__init__.py
- tests/vintage/__init__.py
- tests/indicators/__init__.py
- tests/governance/__init__.py
- tests/interfaces/__init__.py
- tests/test_scaffold.py

### Change Log

- 2026-02-26: Added scaffold package/test directories, introduced CI workflow, and added scaffold smoke tests with full validation pass.
- 2026-02-26: [Code Review] Fixed CI trigger to fire on all branches (was master-only). Consolidated 3 CI jobs into 1 to eliminate redundant setup. Added empty-placeholder assertion to scaffold smoke tests. Removed non-deliverable files from File List. (210 tests pass, ruff clean, mypy clean)

## Code Review (AI)

**Reviewer:** Claude Opus 4.6
**Date:** 2026-02-26
**Outcome:** Changes Requested (fixed in-place)

### Findings Addressed

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| H1 | HIGH | Scaffold files not committed to git | Committed in review fix |
| H2 | HIGH | `overnight-build.sh` modified but not in File List | Out-of-scope for this story; left unstaged |
| H3 | HIGH | CI triggers only on master push, not all branches per spec | Fixed: `on: [push, pull_request]` |
| M1 | MEDIUM | Sprint status change not committed | Committed in review fix |
| M2 | MEDIUM | Scaffold tests lack empty-placeholder assertion | Added `test_scaffold_packages_are_empty_placeholders` |
| M3 | MEDIUM | CI has 3 redundant jobs with duplicated setup | Consolidated into single `check` job |
| L1 | LOW | File List included tracking artifacts | Removed from File List |
