# Story 7.3: Enforce CI Quality Gates

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer or contributor**,
I want **CI to enforce lint, test, and coverage quality gates on every pull request**,
so that **only code meeting project quality standards can be merged, preventing regressions and maintaining code health**.

## Acceptance Criteria

From backlog (BKL-703), aligned with NFR18 and NFR20.

1. **AC-1: Lint failures block merge**
   - Given a pull request with failing ruff lint checks
   - When CI runs
   - Then the merge is blocked with specific lint errors listed in the CI output

2. **AC-2: Test failures block merge**
   - Given a pull request with failing pytest tests
   - When CI runs
   - Then the merge is blocked with test failure details in the CI output

3. **AC-3: Coverage threshold enforcement**
   - Given a pull request with test coverage below the configured threshold
   - When CI runs
   - Then the merge is blocked with a coverage report showing current vs required coverage

4. **AC-4: Type check failures block merge**
   - Given a pull request with mypy type errors
   - When CI runs
   - Then the merge is blocked with specific type errors listed in the CI output

5. **AC-5: Notebook validation continues to pass**
   - Given shipped example notebooks (quickstart.ipynb, advanced.ipynb)
   - When CI runs
   - Then notebook execution tests pass, ensuring documentation does not drift from code

6. **AC-6: Clear failure messages guide developers**
   - Given any quality gate failure
   - When a developer views CI output
   - Then the error message clearly identifies: what failed, where it failed, and how to fix it locally

## Dependencies

Dependency gate: if any hard dependency below is not `done`, set this story to `blocked`.

- **Hard dependencies (from backlog BKL-703):**
  - Story 1-8 (BKL-108): Project scaffold with CI smoke pipeline (DONE) — establishes baseline CI

- **Integration dependencies:**
  - All prior stories in EPIC-1 through EPIC-7 up to 7-2 (DONE) — codebase exists to validate

- **Follow-on stories (not in scope here):**
  - Story 7-4 (BKL-704): External pilot run carbon-tax workflow
  - Story 7-5 (BKL-705): Define Phase 1 exit checklist and pilot sign-off criteria

## Tasks / Subtasks

- [ ] **Task 1: Assess current CI configuration and gaps** (AC: 1, 2, 4, 5)
  - [ ] Review `.github/workflows/ci.yml` current state
  - [ ] Verify ruff, mypy, pytest, nbmake are all running
  - [ ] Identify missing quality gates (coverage threshold enforcement)
  - [ ] Document current CI behavior vs required behavior

- [ ] **Task 2: Add pytest-cov for coverage measurement** (AC: 3)
  - [ ] Add `pytest-cov>=4.1.0` to dev dependencies in `pyproject.toml`
  - [ ] Run `uv sync --locked --all-extras --dev` to update lockfile
  - [ ] Verify pytest-cov works locally: `uv run pytest --cov=src/reformlab tests/`

- [ ] **Task 3: Configure coverage threshold in pyproject.toml** (AC: 3)
  - [ ] Add `[tool.coverage.run]` section with `source = ["src/reformlab"]`, `branch = true`
  - [ ] Add `[tool.coverage.report]` section with `fail_under = 80` (80% threshold for Phase 1)
  - [ ] Add `exclude_lines` for standard exclusions (`pragma: no cover`, `if TYPE_CHECKING:`, etc.)
  - [ ] Verify threshold enforcement: `uv run pytest --cov=src/reformlab --cov-fail-under=80 tests/`

- [ ] **Task 4: Update CI workflow with coverage enforcement** (AC: 1, 2, 3, 4, 5, 6)
  - [ ] Modify `.github/workflows/ci.yml` to add coverage flag to pytest
  - [ ] Ensure all quality steps produce clear failure output
  - [ ] Add summary output step for coverage report visibility
  - [ ] Ensure CI blocks on any failure (lint, type, test, coverage)

- [ ] **Task 5: Add branch protection rule documentation** (AC: 1, 2, 3, 4)
  - [ ] Document required GitHub branch protection settings for `master`:
    - Require status checks to pass before merging
    - Require branches to be up to date before merging
    - Status checks: `check` job from CI workflow
  - [ ] Add note to CONTRIBUTING.md or README about CI requirements

- [ ] **Task 6: Verify CI gates locally and in CI** (AC: all)
  - [ ] Run full CI check locally: `uv run ruff check src tests && uv run mypy src && uv run pytest --cov=src/reformlab --cov-fail-under=80 tests/`
  - [ ] Create test PR to verify CI blocks on intentional failure
  - [ ] Verify all shipped notebooks pass: `uv run pytest --nbmake notebooks/*.ipynb -v`

- [ ] **Task 7: Run final quality checks** (AC: all)
  - [ ] Run `ruff check src tests`
  - [ ] Run `mypy src`
  - [ ] Run `pytest --cov=src/reformlab --cov-fail-under=80 tests/`
  - [ ] Verify no regressions from existing test suite

## Dev Notes

### Architecture Alignment

This story implements CI quality enforcement from PRD NFR18 and NFR20, directly addressing BKL-703 acceptance criteria.

**NFR18:** "pytest test suite with high coverage on adapters, orchestration, template logic, and simulation runner"
**NFR20:** "YAML examples are tested in CI to prevent documentation drift"

The existing CI workflow (`.github/workflows/ci.yml`) already runs:
- `ruff check src tests` — lint checking
- `mypy src` — type checking
- `pytest tests` — test execution
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

**Minimal changes principle:** The existing CI workflow structure is correct. We add coverage without restructuring.

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

**CI update (single line change):**
```yaml
- run: uv run pytest --cov=src/reformlab --cov-report=term-missing tests/
```

### File Structure Requirements

```
pyproject.toml                    # Add pytest-cov dependency, coverage config
.github/workflows/ci.yml          # Add --cov flags to pytest
```

No new files needed — this story enhances existing configuration.

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
  - Update CI to run coverage with threshold enforcement
  - Ensure clear failure messages for all quality gates
  - Document branch protection recommendations

- **Out of scope:**
  - Changing coverage threshold (80% is fixed for Phase 1)
  - Adding additional linting rules beyond current ruff configuration
  - Adding pre-commit hooks (optional enhancement, not required for this story)
  - Security scanning (SAST tools) — future consideration
  - Performance benchmarks in CI — covered by story 7-1 separately

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
- `0c3f27c` overnight-build: 7-2-warn-before-exceeding-memory-limits — mark done
- `46e404a` overnight-build: 7-2-warn-before-exceeding-memory-limits — code review
- `de6a3e7` overnight-build: 7-2-warn-before-exceeding-memory-limits — dev story

Pattern: CI already runs on every push. Quality gates enforce code health. This story hardens the gates.

### Project Structure Notes

- No new source code files — configuration changes only
- `pyproject.toml` modification for coverage config
- `.github/workflows/ci.yml` modification for coverage in pytest command
- All changes are additive and non-breaking

### Branch Protection Recommendations

For GitHub repository settings → Branches → Branch protection rules for `master`:

1. **Require status checks to pass before merging:** Yes
2. **Require branches to be up to date before merging:** Yes
3. **Status checks that are required:**
   - `check` (the CI job name from `ci.yml`)
4. **Require a pull request before merging:** Recommended
5. **Require approvals:** Optional (solo developer can skip)

These settings ensure CI gates actually block merges.

### References

- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-703] - Story requirements
- [Source: _bmad-output/planning-artifacts/prd.md#NFR18] - Test suite coverage requirement
- [Source: _bmad-output/planning-artifacts/prd.md#NFR20] - YAML/notebook testing in CI requirement
- [Source: .github/workflows/ci.yml] - Current CI configuration
- [Source: pyproject.toml] - Project configuration and dependencies
- [Source: _bmad-output/implementation-artifacts/7-2-warn-before-exceeding-memory-limits.md] - Previous story patterns

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
