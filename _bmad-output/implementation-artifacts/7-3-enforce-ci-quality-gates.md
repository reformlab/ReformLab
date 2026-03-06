# Story 7.3: Enforce CI Quality Gates

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer or contributor**,
I want **CI to enforce lint, test, and coverage quality gates on every pull request**,
so that **only code meeting project quality standards can be merged, preventing regressions and maintaining code health**.

## Acceptance Criteria

From backlog (BKL-703), aligned with NFR18, NFR19, and NFR20.

1. **AC-1: Lint failures block merge**
   - Given a pull request with failing ruff lint checks
   - When CI runs
   - Then the merge is blocked with specific lint errors listed in the CI output

2. **AC-2: Test failures block merge**
   - Given a pull request with failing pytest tests
   - When CI runs
   - Then the merge is blocked with test failure details in the CI output

3. **AC-3: Coverage threshold enforcement**
   - Given a pull request with test coverage below the configured Phase 1 threshold (`fail_under = 80`)
   - When CI runs
   - Then the merge is blocked with a coverage report showing current vs required coverage

4. **AC-4: Type check failures block merge**
   - Given a pull request with mypy type errors
   - When CI runs
   - Then the merge is blocked with specific type errors listed in the CI output

5. **AC-5: Shipped examples remain CI-validated**
   - Given shipped examples (workflow YAML examples and quickstart/advanced notebooks)
   - When CI runs
   - Then example validation checks pass, preventing documentation/configuration drift from executable behavior

6. **AC-6: Clear failure messages guide developers**
   - Given any quality gate failure
   - When a developer views CI output
   - Then the error message clearly identifies: what failed, where it failed, and how to fix it locally

## Dependencies

Dependency gate: if any hard dependency below is not `done`, set this story to `blocked`.

- **Hard dependencies (from backlog BKL-703):**
  - Story 1-1 (BKL-101): ComputationAdapter/OpenFiscaAdapter foundation (DONE)

- **Integration dependencies (required for complete CI gate coverage):**
  - Story 1-8 (BKL-108): Project scaffold and CI smoke pipeline baseline (DONE)
  - Story 2-7 (BKL-207): YAML/JSON workflow configuration and validation (DONE)
  - Story 6-2 (BKL-602): Quickstart notebook (DONE)
  - Story 6-3 (BKL-603): Advanced notebook (DONE)
  - Story 7-1 (BKL-701): Benchmark suite integrated into test corpus (DONE)
  - Story 7-2 (BKL-702): Memory warning behavior covered by tests (DONE)

- **Follow-on stories (not in scope here):**
  - Story 7-4 (BKL-704): External pilot run carbon-tax workflow
  - Story 7-5 (BKL-705): Define Phase 1 exit checklist and pilot sign-off criteria

## Tasks / Subtasks

- [ ] **Task 0: Confirm dependency status and current CI baseline** (AC: dependency check)
  - [ ] Confirm dependencies in `_bmad-output/implementation-artifacts/sprint-status.yaml`
  - [ ] Review `.github/workflows/ci.yml` current state and blocking behavior
  - [ ] Confirm existing example-validation surface (pytest suite + notebook execution)

- [ ] **Task 1: Assess current CI configuration and gaps** (AC: 1, 2, 4, 5)
  - [ ] Verify ruff, mypy, pytest, and notebook execution checks are running in CI
  - [ ] Verify YAML example coverage is enforced through existing pytest tests
  - [ ] Identify missing quality gate behavior (coverage threshold enforcement)
  - [ ] Document current CI behavior vs required behavior

- [ ] **Task 2: Add pytest-cov for coverage measurement** (AC: 3)
  - [ ] Add `pytest-cov>=4.1.0` to dev dependencies in `pyproject.toml`
  - [ ] Run `uv sync --locked --all-extras --dev` to update lockfile
  - [ ] Verify pytest-cov works locally: `uv run pytest --cov=src/reformlab tests/`

- [ ] **Task 3: Configure coverage threshold in pyproject.toml** (AC: 3)
  - [ ] Add `[tool.coverage.run]` section with `source = ["src/reformlab"]`, `branch = true`
  - [ ] Add `[tool.coverage.report]` section with `fail_under = 80` (Phase 1 threshold)
  - [ ] Add `exclude_lines` for standard exclusions (`pragma: no cover`, `if TYPE_CHECKING:`, etc.)
  - [ ] Verify threshold enforcement: `uv run pytest --cov=src/reformlab --cov-fail-under=80 tests/`

- [ ] **Task 4: Update CI workflow with coverage enforcement** (AC: 1, 2, 3, 4, 5, 6)
  - [ ] Modify `.github/workflows/ci.yml` to add coverage flags to the pytest test run
  - [ ] Keep CI gate behavior consistent with architecture/tooling decisions (no topology redesign in this story)
  - [ ] Ensure quality steps produce actionable failure output
  - [ ] Ensure CI blocks on any failure (lint, type, test, coverage, example checks)

- [ ] **Task 5: Add branch protection rule documentation** (AC: 1, 2, 3, 4)
  - [ ] Document required GitHub branch protection settings for `master`:
    - Require status checks to pass before merging
    - Require branches to be up to date before merging
    - Status checks: `check` job from CI workflow
  - [ ] Add note to CONTRIBUTING.md or README about CI requirements

- [ ] **Task 6: Verify CI gates locally and in CI** (AC: all)
  - [ ] Run full CI gate simulation locally: `uv run ruff check src tests && uv run mypy src && uv run pytest --cov=src/reformlab --cov-fail-under=80 tests/`
  - [ ] Verify notebooks still execute in CI parity mode: `uv run pytest --nbmake notebooks/quickstart.ipynb notebooks/advanced.ipynb -v`
  - [ ] Create a test PR to verify CI blocks on intentional gate failures

## Dev Notes

### Architecture Alignment

This story implements CI quality enforcement from PRD NFR18/NFR19/NFR20, directly addressing BKL-703 acceptance criteria.

**NFR18:** "pytest test suite with high coverage on adapters, orchestration, template logic, and simulation runner"
**NFR19:** "All shipped examples run end-to-end without modification on a fresh install (tested in CI)"
**NFR20:** "YAML examples are tested in CI to prevent documentation drift"

The architecture specifies Python quality tooling (`pytest`, `ruff`, `mypy`) and CI-enforced quality gates, with a broader CI strategy that can separate fast and slower checks. This story hardens merge-blocking quality gates in the existing `check` pipeline without broad workflow-topology redesign.

The existing CI workflow (`.github/workflows/ci.yml`) already runs:
- `ruff check src tests` — lint checking
- `mypy src` — type checking
- `pytest tests` — test execution (including YAML/workflow validation tests)
- `pytest --nbmake notebooks/*.ipynb` — notebook validation

**Missing component:** Coverage threshold enforcement. This story adds pytest-cov with a `fail_under` threshold.

### Current CI Configuration

From `.github/workflows/ci.yml`:
```yaml
name: CI

on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true
      - run: uv python install 3.13
      - run: uv sync --locked --all-extras --dev
      - run: uv run ruff check src tests
      - run: uv run mypy src
      - run: uv run pytest tests
      - run: uv run pytest --nbmake notebooks/quickstart.ipynb -v
      - run: uv run pytest --nbmake notebooks/advanced.ipynb -v
```

**What works:** Lint, type checks, tests, and notebook validation all run and block on failure.

**What's missing:**
1. Coverage measurement and threshold enforcement
2. Coverage report visibility in CI output

### Implementation Approach

**Minimal changes principle:** Keep the current CI workflow topology and add the missing coverage gate.

**Coverage threshold rationale:** 80% is a reasonable Phase 1 target that enforces meaningful coverage without blocking legitimate edge cases. This can be increased in future phases.

**pyproject.toml additions:**
```toml
[tool.coverage.run]
source = ["src/reformlab"]
branch = true

[tool.coverage.report]
fail_under = 80
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
    "@overload",
    "\\.\\.\\.",
]
show_missing = true
```

**CI update (single-line test gate enhancement):**
```yaml
- run: uv run pytest --cov=src/reformlab --cov-report=term-missing tests/
```

### File Structure Requirements

```
pyproject.toml                    # Add pytest-cov dependency, coverage config
.github/workflows/ci.yml          # Add --cov flags to pytest
```

No new files needed - this story enhances existing configuration.

### Testing Standards

**Local validation before push:**
```bash
# Full CI simulation
uv run ruff check src tests
uv run mypy src
uv run pytest --cov=src/reformlab --cov-report=term-missing --cov-fail-under=80 tests/
uv run pytest --nbmake notebooks/quickstart.ipynb notebooks/advanced.ipynb -v
```

**Coverage verification:**
```bash
# Check current coverage
uv run pytest --cov=src/reformlab --cov-report=term-missing tests/

# Verify threshold enforcement (should pass if coverage >= 80%)
uv run pytest --cov=src/reformlab --cov-fail-under=80 tests/
```

### Scope Guardrails

- **In scope:**
  - Add pytest-cov to dev dependencies
  - Configure coverage settings in pyproject.toml
  - Update existing CI gate execution to enforce coverage threshold
  - Ensure clear failure messages for all quality gates
  - Document branch protection recommendations

- **Out of scope:**
  - CI workflow topology redesign (fast/slow split redesign)
  - Changing coverage threshold (80% is fixed for Phase 1)
  - Adding additional linting rules beyond current ruff configuration
  - Adding pre-commit hooks (optional enhancement, not required for this story)
  - Security scanning (SAST tools) - future consideration
  - Performance benchmarks in CI - covered by story 7-1 separately

### Previous Story Intelligence

From Story 7-2 (warn-before-exceeding-memory-limits):
- Story completed successfully with all tests passing
- Memory module added to governance layer with clean exports
- Tests follow existing patterns in `tests/governance/` and `tests/interfaces/`

From Story 7-1 (verify-simulation-outputs-against-benchmarks):
- Benchmark suite established with custom pytest marker `@pytest.mark.benchmark`
- Deterministic fixtures in `tests/benchmarks/`
- Pattern for structured result dataclasses

Apply learnings:
- Keep changes minimal and focused
- Test locally before pushing
- Follow existing patterns in CI workflow
- Ensure backward compatibility with all existing tests

### Git Intelligence

Recent commits:
- `0c3f27c` overnight-build: 7-2-warn-before-exceeding-memory-limits - mark done
- `46e404a` overnight-build: 7-2-warn-before-exceeding-memory-limits - code review
- `de6a3e7` overnight-build: 7-2-warn-before-exceeding-memory-limits - dev story

Pattern: CI already runs on every push. Quality gates enforce code health. This story hardens the gates.

### Project Structure Notes

- No new source code files - configuration changes only
- `pyproject.toml` modification for coverage config
- `.github/workflows/ci.yml` modification for coverage in pytest command
- All changes are additive and non-breaking

### Branch Protection Recommendations

For GitHub repository settings -> Branches -> Branch protection rules for `master`:

1. **Require status checks to pass before merging:** Yes
2. **Require branches to be up to date before merging:** Yes
3. **Status checks that are required:**
   - `check` (the CI job name from `ci.yml`)
4. **Require a pull request before merging:** Recommended
5. **Require approvals:** Optional (solo developer can skip)

These settings ensure CI gates actually block merges.

### References

- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-703] - Story requirements and dependency
- [Source: _bmad-output/planning-artifacts/prd.md#NFR18] - Test suite coverage requirement
- [Source: _bmad-output/planning-artifacts/prd.md#NFR19] - Shipped examples tested in CI
- [Source: _bmad-output/planning-artifacts/prd.md#NFR20] - YAML examples tested in CI
- [Source: _bmad-output/planning-artifacts/architecture.md] - CI quality and tooling direction
- [Source: .github/workflows/ci.yml] - Current CI configuration
- [Source: pyproject.toml] - Project configuration and dependencies
- [Source: _bmad-output/implementation-artifacts/sprint-status.yaml] - Dependency completion status
- [Source: _bmad-output/implementation-artifacts/7-2-warn-before-exceeding-memory-limits.md] - Previous story patterns

## Dev Agent Record

### Agent Model Used

Unknown (record not captured during implementation)

### Debug Log References

- Dev Agent Record backfilled during Phase 1 retro cleanup. Original debug logs were not recorded.

### Completion Notes List

- Dev Agent Record backfilled during Phase 1 retro cleanup. Original implementation agent and debug details were not recorded.

### File List

- `src/reformlab/governance/benchmarking.py` (modified) — benchmarking module used by CI gates
- `src/reformlab/interfaces/api.py` (modified) — API updates for quality gate compliance
- `tests/indicators/test_distributional.py` (modified) — test adjustments for CI compliance
- `tests/interfaces/test_api.py` (modified) — API test adjustments
- `tests/notebooks/test_advanced_notebook.py` (modified) — notebook test adjustments
- `tests/notebooks/test_quickstart_notebook.py` (modified) — notebook test adjustments
- `tests/test_ci_quality_gates.py` (new) — dedicated CI quality gate tests
- `.github/workflows/ci.yml` (modified) — CI workflow quality gate enforcement
- `pyproject.toml` (modified) — config/dependency changes
