# Story 1.1: Define ComputationAdapter Interface and OpenFiscaAdapter Implementation

Status: done

## Story

As a developer building the ReformLab platform,
I want a clean ComputationAdapter protocol interface and a working OpenFiscaAdapter implementation,
so that the orchestrator can call tax-benefit computations through a stable, mockable, version-pinned contract without coupling to OpenFisca internals.

## Acceptance Criteria

1. **AC-1: CSV/Parquet compute path** - Given an OpenFisca output dataset (CSV or Parquet), when the adapter's `compute()` method is called, then it returns a `ComputationResult` with mapped output fields matching the input data.

2. **AC-2: Mock adapter for testing** - Given a mock adapter implementing the `ComputationAdapter` protocol, when the orchestrator calls `compute()`, then it receives valid `ComputationResult` objects without requiring OpenFisca installed.

3. **AC-3: Version compatibility check** - Given an unsupported OpenFisca version, when the adapter is initialized, then it raises an explicit `CompatibilityError` with version mismatch details (expected vs. actual, link to compatibility matrix).

4. **AC-4: Protocol structural typing** - Given any class implementing `compute()` and `version()` with correct signatures, when used as a `ComputationAdapter`, then mypy accepts it without explicit inheritance.

5. **AC-5: ComputationResult contract** - Given a successful `compute()` call, then the returned `ComputationResult` contains: mapped output fields as a dict or DataFrame, the adapter version string, the computation period, and metadata (timing, row count).

## Tasks / Subtasks

- [x] Task 1: Define core data types (AC: 4, 5)
  - [x] 1.1 Create `PopulationData` type (wraps DataFrame with metadata)
  - [x] 1.2 Create `PolicyConfig` type (scenario parameters for a period)
  - [x] 1.3 Create `ComputationResult` type (output fields, version, period, metadata)
  - [x] 1.4 Create `CompatibilityError` exception class
- [x] Task 2: Define `ComputationAdapter` protocol (AC: 2, 4)
  - [x] 2.1 Define `compute(population, policy, period) -> ComputationResult` method signature
  - [x] 2.2 Define `version() -> str` method signature
  - [x] 2.3 Mark protocol as `@runtime_checkable`
  - [x] 2.4 Add type stubs and docstrings
- [x] Task 3: Implement `OpenFiscaAdapter` (AC: 1, 3, 5)
  - [x] 3.1 Implement constructor with OpenFisca version validation
  - [x] 3.2 Implement `version()` returning OpenFisca-Core version string
  - [x] 3.3 Implement `compute()` for CSV/Parquet pre-computed outputs mode
  - [x] 3.4 Add supported version list and compatibility check logic
- [x] Task 4: Implement `MockAdapter` for testing (AC: 2)
  - [x] 4.1 Create `MockAdapter` returning configurable fixed results
  - [x] 4.2 Verify `MockAdapter` satisfies `ComputationAdapter` protocol
- [x] Task 5: Write tests (AC: 1, 2, 3, 4, 5)
  - [x] 5.1 Protocol compliance tests (structural typing verification)
  - [x] 5.2 OpenFiscaAdapter version check tests (supported + unsupported)
  - [x] 5.3 CSV ingestion round-trip test with fixture data
  - [x] 5.4 Parquet ingestion round-trip test with fixture data
  - [x] 5.5 MockAdapter contract test
  - [x] 5.6 ComputationResult field completeness test
- [x] Review Follow-ups (AI)
  - [x] [AI-Review][HIGH] AC-4 static typing validation fixed: configured mypy overrides for `pyarrow*`, corrected protocol test `tmp_path` typing, and confirmed `mypy src tests` passes.
  - [x] [AI-Review][HIGH] Version pinning fixed: `_check_version()` now enforces `SUPPORTED_VERSIONS`, and tests now reject unlisted future versions.
  - [x] [AI-Review][MEDIUM] `CompatibilityError` details fixed: not-installed branch now includes compatibility matrix link.
  - [x] [AI-Review][MEDIUM] Type stubs added for public computation contracts (`.pyi` files plus `py.typed` marker).
  - [x] [AI-Review][MEDIUM] `ComputationResult` contract consistency fixed: type and docs now both define `output_fields` as a PyArrow table (`OutputFields` alias).
  - [x] [AI-Review][MEDIUM] Story File List/update transparency fixed: file inventory updated to reflect new stub files and current sprint-status tracking.

## Dev Notes

### Critical Context: Greenfield Project

**No code exists yet.** This is the very first implementation story. There is no `src/` directory, no `pyproject.toml`, no dependencies installed. Story 1-8 (project scaffold) should ideally run before or concurrently with this story. If the scaffold does not exist when you start:

1. Create minimal project structure under `src/reformlab/` following the architecture subsystem layout
2. Set up `pyproject.toml` with `uv` as package manager
3. Coordinate with BKL-108 scope to avoid duplication

### Architecture Compliance

**Layered architecture** - This story implements the bottom layer: `Computation Adapter Interface`.

```
src/reformlab/
  computation/           <-- THIS STORY
    __init__.py
    adapter.py           # ComputationAdapter protocol
    openfisca_adapter.py # OpenFiscaAdapter implementation
    mock_adapter.py      # MockAdapter for testing
    types.py             # PopulationData, PolicyConfig, ComputationResult
    exceptions.py        # CompatibilityError
  data/                  # Future: Story 1.2+
  templates/             # Future: Epic 2
  orchestrator/          # Future: Epic 3
  vintage/               # Future: Epic 3
  indicators/            # Future: Epic 4
  governance/            # Future: Epic 5
  interfaces/            # Future: Epic 6
```

### Adapter Pattern Design

The architecture mandates the adapter pattern for computation backends:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class ComputationAdapter(Protocol):
    """Interface for tax-benefit computation backends.

    The orchestrator NEVER calls OpenFisca directly. All computation
    goes through this interface, enabling:
    - Backend swapping (OpenFisca -> PolicyEngine -> custom)
    - Mocking for orchestrator unit tests
    - Version-pinning without core coupling
    """
    def compute(
        self,
        population: PopulationData,
        policy: PolicyConfig,
        period: int
    ) -> ComputationResult: ...

    def version(self) -> str: ...
```

### OpenFisca Integration Specifics

**OpenFisca-Core v44.2.2** (latest stable, supports Python 3.13):

Key API patterns for the adapter:
```python
from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_core.taxbenefitsystems import TaxBenefitSystem

# For CSV/Parquet pre-computed output mode (Phase 1 primary path):
# The adapter reads pre-computed OpenFisca outputs from CSV/Parquet files
# and maps them to the internal schema. No live OpenFisca execution needed.

# For direct API mode (Phase 1 P1 / Story 1-6):
# tax_benefit_system = FranceTaxBenefitSystem()
# simulation = SimulationBuilder().build_default_simulation(tax_benefit_system, pop_size)
# simulation.set_input('salary', period, numpy.array(salaries))
# result = simulation.calculate('income_tax', period)
```

**Phase 1 primary mode:** CSV/Parquet ingestion of pre-computed OpenFisca outputs. The `compute()` method in this story reads pre-computed results, NOT runs OpenFisca live. Direct API orchestration is Story 1-6 (P1 priority).

**Version detection:** Use `importlib.metadata.version('openfisca-core')` for version checks (preferred over `openfisca_core.__version__`).

**OpenFisca-France entities (for reference):** The French model defines 4 entities: `Individu` (person), `Famille`, `FoyerFiscal` (tax household), `Menage` (dwelling). Each has roles (e.g., `parent`/`enfant` in Famille). The adapter does not need to model these — it consumes pre-computed outputs — but the `PopulationData` type should accommodate household-level data keyed by these entity types.

**Python 3.13 Protocol introspection:** Use `typing.get_protocol_members(ComputationAdapter)` and `typing.is_protocol(ComputationAdapter)` for runtime validation (new in 3.13).

### Data Handling

- **CSV/Parquet I/O:** Use `pyarrow` for Parquet, standard `csv` module or `pyarrow.csv` for CSV
- **Internal representation:** Use `pyarrow.Table` or dict-of-arrays for vectorized operations (NumPy arrays)
- **Do NOT use pandas as a required dependency** - prefer pyarrow-native operations. pandas/polars are optional for user-facing convenience
- **Type safety:** All data types should be explicit (no implicit type coercion)

### Testing Standards

- **Framework:** pytest
- **Fixtures:** Create CSV and Parquet test fixtures in `tests/fixtures/`
- **Pattern:** Given/When/Then style matching acceptance criteria
- **Coverage focus:** Adapter contracts, version checks, data mapping
- **Mock strategy:** `MockAdapter` is a real class (not unittest.mock), implementing the protocol

### Library Versions (as of 2026-02-25)

| Library | Version | Notes |
|---------|---------|-------|
| Python | >= 3.13 | Required |
| OpenFisca-Core | >= 44.0.0 (latest: 44.2.2) | Supports Python 3.13; requires NumPy 2.x on 3.13 |
| OpenFisca-France | >= 175.0.0 (latest: 175.0.18) | French country package |
| NumPy | >= 2.0.0 | Required for Python 3.13 compatibility |
| PyArrow | >= 17.0.0 (latest: 23.x) | For Parquet read/write |
| pytest | >= 9.0.0 (latest: 9.0.2) | Test framework |
| ruff | >= 0.15.0 (latest: 0.15.2) | Linter + formatter |
| mypy | >= 1.19.0 (latest: 1.19.1) | Type checker; needs `ignore_missing_imports` for OpenFisca |
| uv | 0.10.6 | Package manager (not a Python dependency) |

**mypy note:** OpenFisca packages do not ship type stubs. Add to `pyproject.toml`:

```toml
[[tool.mypy.overrides]]
module = ["openfisca_core.*", "openfisca_france.*"]
ignore_missing_imports = true
```

### Type Hinting Conventions

- Use `from __future__ import annotations` for forward references
- Use modern union syntax: `str | None` not `Optional[str]`
- Use lowercase generics: `list[str]` not `List[str]`
- Use `Protocol` with `@runtime_checkable` for structural typing
- All public functions must have complete type annotations

### Anti-Patterns to Avoid

1. **Do NOT build a custom formula engine** - OpenFisca handles all policy calculations
2. **Do NOT import `openfisca_france` directly** in the adapter - keep it behind configuration
3. **Do NOT use pandas as a required dependency** - use pyarrow for data contracts
4. **Do NOT hardcode OpenFisca variable names** - mapping is Story 1-3's responsibility
5. **Do NOT implement direct API orchestration** - that's Story 1-6
6. **Do NOT create entity graph or relationship models** - out of scope entirely
7. **Do NOT add behavioral response logic** - that's Phase 2

### Cross-Story Dependencies

- **This story depends on:** Nothing (first story)
- **Stories depending on this:**
  - 1-2 (CSV/Parquet ingestion) builds on data types defined here
  - 1-3 (input/output mapping) extends the adapter contract
  - 1-5 (data quality checks) validates adapter output
  - 1-6 (direct API mode) adds live OpenFisca execution
  - 3-5 (orchestrator integration) calls `compute()` in the yearly loop
- **Design for extension:** Keep types generic enough for stories 1-2 through 1-6 to build on

### Project Structure Notes

- All source code under `src/reformlab/` (src layout)
- Tests under `tests/` mirroring source structure: `tests/computation/`
- Test fixtures under `tests/fixtures/`
- Package managed by `uv` with `pyproject.toml`
- Subsystem layout: `computation/`, `data/`, `templates/`, `orchestrator/`, `vintage/`, `indicators/`, `governance/`, `interfaces/`

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Computation Adapter Pattern]
- [Source: _bmad-output/planning-artifacts/architecture.md#Subsystems]
- [Source: _bmad-output/planning-artifacts/architecture.md#Layered Architecture]
- [Source: _bmad-output/planning-artifacts/prd.md#FR1-FR3]
- [Source: _bmad-output/planning-artifacts/prd.md#OpenFisca Integration & Data Foundation]
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-101]
- [Source: _bmad-output/planning-artifacts/prd.md#Developer Tool Specific Requirements]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

- pytest version constraint adjusted from >=9.0.0 to >=8.3.3 due to openfisca-core pinning pytest<9.0
- Installed uv via Homebrew (was not pre-installed on system)
- Two minor ruff lint/format issues fixed (unused import, import ordering)

### Completion Notes List

- **Task 1:** Created frozen dataclasses `PopulationData` (multi-entity table wrapper with row_count property), `PolicyConfig` (scenario parameters), `ComputationResult` (output fields as PyArrow Table, version, period, metadata), and `CompatibilityError` exception with expected/actual/details attributes.
- **Task 2:** Defined `ComputationAdapter` as a `@runtime_checkable` Protocol with `compute()` and `version()` methods. Structural typing verified — no inheritance required.
- **Task 3:** Implemented `OpenFiscaAdapter` that reads pre-computed CSV/Parquet files by period. Constructor validates OpenFisca-Core version via `importlib.metadata`. Supports `skip_version_check` for environments without OpenFisca installed. Records timing, row count, and source metadata.
- **Task 4:** Implemented `MockAdapter` returning configurable fixed results with a call_log for test assertions. Verified it satisfies the protocol via structural typing.
- **Task 5:** 37 tests across 6 test files covering all acceptance criteria. Tests use Given/When/Then style with PyArrow fixtures generated in tmp_path.
- **Project scaffold:** Created `pyproject.toml` (uv, hatchling, ruff, mypy, pytest config), `src/reformlab/` package structure, and `tests/` mirror structure. This partially addresses Story 1-8's scope.

### File List

- `pyproject.toml` (new) — Project configuration with dependencies, tool settings
- `src/reformlab/__init__.py` (new) — Package root
- `src/reformlab/computation/__init__.py` (new) — Computation subpackage exports
- `src/reformlab/computation/types.py` (new) — PopulationData, PolicyConfig, ComputationResult
- `src/reformlab/computation/exceptions.py` (new) — CompatibilityError
- `src/reformlab/computation/adapter.py` (new) — ComputationAdapter protocol
- `src/reformlab/computation/openfisca_adapter.py` (new) — OpenFiscaAdapter implementation
- `src/reformlab/computation/mock_adapter.py` (new) — MockAdapter for testing
- `src/reformlab/py.typed` (new) — PEP 561 typed package marker
- `src/reformlab/computation/__init__.pyi` (new) — Type stubs for computation exports
- `src/reformlab/computation/adapter.pyi` (new) — Type stub for ComputationAdapter protocol
- `src/reformlab/computation/exceptions.pyi` (new) — Type stub for CompatibilityError
- `src/reformlab/computation/types.pyi` (new) — Type stubs for core data types
- `src/reformlab/computation/openfisca_adapter.pyi` (new) — Type stubs for OpenFiscaAdapter
- `src/reformlab/computation/mock_adapter.pyi` (new) — Type stubs for MockAdapter
- `tests/__init__.py` (new) — Tests root
- `tests/computation/__init__.py` (new) — Computation tests package
- `tests/computation/conftest.py` (new) — Shared fixtures (sample tables, population, policy, fixture files)
- `tests/computation/test_protocol.py` (new) — Protocol compliance tests (4 tests)
- `tests/computation/test_version.py` (new) — Version check tests (9 tests)
- `tests/computation/test_csv_roundtrip.py` (new) — CSV ingestion round-trip tests (4 tests)
- `tests/computation/test_parquet_roundtrip.py` (new) — Parquet ingestion round-trip tests (4 tests)
- `tests/computation/test_mock_adapter.py` (new) — MockAdapter contract tests (5 tests)
- `tests/computation/test_result.py` (new) — ComputationResult/types field completeness tests (11 tests)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (new) — Story status updated

## Senior Developer Review (AI)

### Reviewer

Lucas

### Date

2026-02-25

### Outcome

Approved

### Summary

All HIGH/MEDIUM review findings were remediated in code and tests. Validation now passes for linting, static typing, and runtime tests.

### Resolved Findings

1. **HIGH** - AC-4 strict typing gap fixed (`mypy src tests` clean).
2. **HIGH** - Version compatibility pinning fixed (explicit supported-version enforcement).
3. **MEDIUM** - Compatibility matrix link added to not-installed error details.
4. **MEDIUM** - Public `.pyi` stubs and typed package marker added.
5. **MEDIUM** - ComputationResult contract consistency fixed (table type + aligned docs).
6. **MEDIUM** - Story file list/status tracking corrected and synchronized.

### Validation Evidence

- `pytest -q`: 37 passed
- `uv run ruff check .`: all checks passed
- `mypy src tests`: no issues found

## Change Log

- 2026-02-25: Implemented Story 1.1 — ComputationAdapter protocol, OpenFiscaAdapter (CSV/Parquet pre-computed mode), MockAdapter, and comprehensive test suite (37 tests). Created project scaffold (pyproject.toml, src layout, test structure).
- 2026-02-25: Senior Developer Review (AI) completed; outcome set to Changes Requested with 6 follow-up items. Story status moved to in-progress and sprint tracking synced.
- 2026-02-25: Auto-remediated all HIGH/MEDIUM review findings: strict mypy pass restored, version pinning enforced, compatibility error details improved, type stubs added, contracts/docs aligned, and sprint/story status moved to done.
