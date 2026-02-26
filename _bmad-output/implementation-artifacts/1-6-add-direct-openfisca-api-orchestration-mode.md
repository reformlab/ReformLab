# Story 1.6: Add Direct OpenFisca API Orchestration Mode

Status: done

<!-- Story context created on 2026-02-26 using backlog BKL-106, architecture, PRD (FR2, NFR15), previous stories 1.1-1.5, current codebase, git history, and OpenFisca Python API docs. -->

## Story

As a **policy analyst**,
I want **the system to execute OpenFisca tax-benefit computations directly through the Python API instead of requiring pre-computed CSV/Parquet files**,
so that **I can run live scenario analyses with arbitrary policy configurations and population data without an offline file-preparation step**.

## Acceptance Criteria

1. **AC-1: Live computation via OpenFisca Python API**
   Given a `PopulationData` input and a `PolicyConfig` with tax-benefit parameters, when `compute()` is called on the direct API adapter, then OpenFisca's `SimulationBuilder` and `Simulation.calculate()` are invoked and the results are returned as a `ComputationResult` with a PyArrow output table. `PolicyConfig.parameters` is applied as OpenFisca input-variable values only (no Reform object construction in this story).

2. **AC-2: Version-pinned execution**
   Given an installed `openfisca-core` version, when the direct API adapter is initialized, then it validates the version against `SUPPORTED_VERSIONS` (reusing the existing `_check_version` logic) and raises `CompatibilityError` for unsupported versions.

3. **AC-3: TaxBenefitSystem configuration**
   Given a country package name (e.g. `"openfisca_france"`), when the direct API adapter executes its first `compute()`, then it imports and initializes the corresponding `TaxBenefitSystem`, caches it, and reuses it across subsequent `compute()` calls.

4. **AC-4: Variable selection**
   Given a list of output variable names in the adapter configuration, when `compute()` runs, then only those variables are calculated and returned as columns in the output table. Unknown variable names raise a clear error before computation.

5. **AC-5: Period mapping**
   Given a `period` integer (e.g. `2025`), when `compute()` is called, then the adapter formats the period into OpenFisca's expected period format (e.g. `"2025"` for yearly variables) and passes it to `Simulation.calculate()`.

6. **AC-6: ComputationResult compatibility**
   Given a successful live computation, when the result is returned, then it is a standard `ComputationResult` with `output_fields` as a `pa.Table`, `adapter_version` set to the detected `openfisca-core` version, `period` set correctly, and `metadata["source"]` set to `"api"` (distinguishing it from `"pre-computed"` and `"mock"`).

7. **AC-7: Protocol compliance**
   Given the new direct API adapter class, when checked with `isinstance(adapter, ComputationAdapter)`, then it returns `True` (structural typing compliance with the existing protocol).

8. **AC-8: Graceful degradation when OpenFisca not installed**
   Given that `openfisca-core` is not installed, when the direct API adapter is instantiated, then it raises `CompatibilityError` with an actionable message including install instructions — not an `ImportError`.

9. **AC-9: Coexistence with pre-computed mode**
   Given both the existing `OpenFiscaAdapter` (pre-computed) and the new direct API adapter, when used in the same project, then they are independent classes satisfying the same `ComputationAdapter` protocol. Neither modifies or depends on the other's internal state.

## Tasks / Subtasks

- [x] Task 1: Create `OpenFiscaApiAdapter` class (AC: 1, 2, 3, 6, 7, 8)
  - [x] 1.1 Create `src/reformlab/computation/openfisca_api_adapter.py`
  - [x] 1.2 Implement `__init__(self, *, country_package: str, output_variables: tuple[str, ...], skip_version_check: bool = False)` with version validation reusing `_detect_openfisca_version` and `_check_version`
  - [x] 1.3 Implement lazy `TaxBenefitSystem` loading: import country package, instantiate system, cache on first use
  - [x] 1.4 Implement `version(self) -> str` returning the detected `openfisca-core` version
  - [x] 1.5 Implement `compute(self, population, policy, period) -> ComputationResult`
  - [x] 1.6 Handle `ImportError` for missing country packages with a structured `CompatibilityError`

- [x] Task 2: Implement population-to-simulation translation (AC: 1, 5)
  - [x] 2.1 Implement `_build_simulation(self, population: PopulationData, policy: PolicyConfig, period: int) -> Simulation` that constructs an OpenFisca Simulation from `PopulationData.tables` using `SimulationBuilder`
  - [x] 2.2 Resolve `PopulationData` entity keys against `TaxBenefitSystem` entity names; unknown entity keys must raise structured `ApiMappingError` with expected entity names
  - [x] 2.3 Inject `PolicyConfig.parameters` as OpenFisca input-variable values only (no OpenFisca Reform API usage in this story)
  - [x] 2.4 Format `period` integer into OpenFisca period string (yearly: `"2025"`)

- [x] Task 3: Implement result extraction (AC: 1, 4, 6)
  - [x] 3.1 Implement `_extract_results(self, simulation: Simulation, period: int) -> pa.Table` that calls `simulation.calculate(var, period)` for each output variable
  - [x] 3.2 Convert NumPy arrays returned by `calculate()` into PyArrow arrays and assemble into a `pa.Table`
  - [x] 3.3 Validate that all requested output variables exist in the `TaxBenefitSystem` before calculation; raise structured error for unknowns

- [x] Task 4: Implement output variable validation (AC: 4)
  - [x] 4.1 Add `_validate_output_variables(self)` method called during `compute()` before calculation
  - [x] 4.2 Check each variable in `output_variables` exists in `tax_benefit_system.variables`
  - [x] 4.3 On unknown variable, raise `ApiMappingError` listing invalid names and suggesting close matches via `difflib.get_close_matches`

- [x] Task 5: Create type stub (AC: 7)
  - [x] 5.1 Create `src/reformlab/computation/openfisca_api_adapter.pyi`
  - [x] 5.2 Export new public API from `src/reformlab/computation/__init__.py`
  - [x] 5.3 Export stubs in `src/reformlab/computation/__init__.pyi`

- [x] Task 6: Tests (AC: 1-9)
  - [x] 6.1 Create `tests/computation/test_openfisca_api_adapter.py`
  - [x] 6.2 Test protocol compliance: `isinstance(OpenFiscaApiAdapter(...), ComputationAdapter)` returns `True`
  - [x] 6.3 Test version checking reuse: unsupported version raises `CompatibilityError`
  - [x] 6.4 Test graceful degradation: missing `openfisca-core` raises `CompatibilityError` (not `ImportError`)
  - [x] 6.5 Test `compute()` with mocked OpenFisca internals (patch `TaxBenefitSystem`, `SimulationBuilder`, `Simulation.calculate`)
  - [x] 6.6 Test output variable validation: unknown variables raise structured error with suggestions
  - [x] 6.7 Test period formatting: integer year correctly passed as OpenFisca period string
  - [x] 6.8 Test `ComputationResult` structure: `source` metadata is `"api"`, `adapter_version` is correct, `output_fields` is a `pa.Table`
  - [x] 6.9 Test coexistence: both `OpenFiscaAdapter` and `OpenFiscaApiAdapter` instantiate independently
  - [x] 6.10 Ensure all existing tests remain green (`uv run pytest -q`) — 167 passed

- [x] Task 7: Quality gates (AC: all)
  - [x] 7.1 `uv run ruff check src tests` — All checks passed
  - [x] 7.2 `uv run mypy src` — Success: no issues found in 16 source files
  - [x] 7.3 `uv run pytest -q` — 167 passed

## Dev Notes

### Scope Boundaries (Critical)

- This story adds a **new adapter class** (`OpenFiscaApiAdapter`) for live OpenFisca computation. It does **not** modify the existing `OpenFiscaAdapter` (pre-computed file mode).
- Do **not** wire this adapter into the orchestrator runtime; the orchestrator will select adapters via configuration in EPIC-3.
- Do **not** implement OpenFisca Reform API logic in this story. `PolicyConfig.parameters` is applied only as OpenFisca input-variable values.
- Do **not** add `openfisca-core` or any country package to the mandatory `[project.dependencies]`. Keep them in `[project.optional-dependencies].openfisca`.

### Architecture Compliance

- New file: `src/reformlab/computation/openfisca_api_adapter.py` — same subsystem as the existing adapter.
- Class name: `OpenFiscaApiAdapter` to distinguish from `OpenFiscaAdapter` (pre-computed mode).
- Must satisfy `ComputationAdapter` protocol via structural typing (duck typing) — no inheritance from the Protocol class.
- Keep data model immutable: `ComputationResult` is `@dataclass(frozen=True)`.
- All OpenFisca imports must be lazy (inside methods or guarded by try/except) since `openfisca-core` is an optional dependency.
- Error messages follow project structured style: `[summary] - [reason] - [fix]`.

### Reuse Existing Implementation Patterns

- **Reuse `_detect_openfisca_version()` and `_check_version()`** from `openfisca_adapter.py`. Consider extracting to a shared helper or importing directly. Do not duplicate.
- **Reuse `SUPPORTED_VERSIONS`, `MIN_SUPPORTED`, `COMPAT_MATRIX_URL`** from `openfisca_adapter.py`.
- **Reuse `CompatibilityError`** from `computation.exceptions`.
- **Reuse `ComputationResult`, `PopulationData`, `PolicyConfig`** from `computation.types`.
- Follow export and stub conventions from `computation/__init__.py` and `.pyi`.
- Follow test style and fixture conventions from `tests/computation/conftest.py`.
- Use `unittest.mock.patch` for OpenFisca internals in tests (same pattern as `test_version.py`).

### Required Behavior Details

- **Lazy loading:** The `TaxBenefitSystem` is expensive to create. Initialize it lazily on first `compute()` call, then cache for subsequent calls.
- **Population translation:** `PopulationData.tables` contains PyArrow tables keyed by entity type. The adapter must convert these into the dict format OpenFisca's `SimulationBuilder.build_from_entities()` expects. This means converting `pa.Table` → Python dicts/lists per entity.
- **Entity mapping contract:** `PopulationData.tables` keys must resolve to entity names exposed by the loaded `TaxBenefitSystem`. Start with exact-match resolution against the country package entity names. If any key cannot be resolved, raise `MappingError` before simulation build with: unknown keys, allowed keys, and fix guidance.
- **Policy parameter contract:** `PolicyConfig.parameters` values are treated as input-variable assignments for the target period only. Unknown parameter keys must raise `MappingError` before computation. Reform object construction is explicitly out of scope for this story.
- **Output extraction:** `Simulation.calculate(variable, period)` returns NumPy arrays. Convert to `pa.array()` and assemble into a `pa.Table`.
- **Period format:** OpenFisca uses string periods. Yearly variables use `"YYYY"` format. The adapter converts the integer `period` parameter to this format. Monthly/quarterly support is out of scope for this story.
- **Metadata:** `ComputationResult.metadata` must include: `timing_seconds`, `row_count`, `source: "api"`, `policy_name`, `country_package`, `output_variables`.

### Suggested Public API

```python
class OpenFiscaApiAdapter:
    """Adapter that executes OpenFisca computations via the Python API.

    Unlike OpenFiscaAdapter (pre-computed file mode), this adapter
    runs live tax-benefit calculations using OpenFisca's SimulationBuilder.
    """

    def __init__(
        self,
        *,
        country_package: str = "openfisca_france",
        output_variables: tuple[str, ...],
        skip_version_check: bool = False,
    ) -> None: ...

    def version(self) -> str: ...

    def compute(
        self,
        population: PopulationData,
        policy: PolicyConfig,
        period: int,
    ) -> ComputationResult: ...
```

### Testing Requirements

- All OpenFisca internals (`TaxBenefitSystem`, `SimulationBuilder`, `Simulation`) must be **mocked** in tests since `openfisca-core` is optional and may not be installed in CI.
- Test using `unittest.mock.patch` on module-level imports (same pattern as `test_version.py`).
- Test both happy path (mocked successful computation) and error paths (missing package, unsupported version, unknown variables).
- Validate `ComputationResult` structure programmatically (not string-only assertions).
- Run full quality gates after implementation.

### Project Structure Notes

Create:

- `src/reformlab/computation/openfisca_api_adapter.py`
- `src/reformlab/computation/openfisca_api_adapter.pyi`
- `tests/computation/test_openfisca_api_adapter.py`

Modify:

- `src/reformlab/computation/__init__.py` (add `OpenFiscaApiAdapter` export)
- `src/reformlab/computation/__init__.pyi` (add `OpenFiscaApiAdapter` stub export)

Do not modify:

- `openfisca_adapter.py` (existing pre-computed mode) — unless extracting shared helpers to a new shared module
- `mock_adapter.py`, `mapping.py`, `ingestion.py`, `quality.py`
- `data/*` modules

Acceptable shared helper extraction (optional):

- If extracting `_detect_openfisca_version`, `_check_version`, `SUPPORTED_VERSIONS` to a shared location (e.g. `openfisca_common.py`), update imports in `openfisca_adapter.py` accordingly and ensure all existing tests pass.

### Dependencies and Sequencing

- Depends on completed story 1.1 (ComputationAdapter protocol, types, exceptions).
- `openfisca-core` remains optional. The adapter must handle its absence gracefully.
- Country packages (e.g. `openfisca-france`) are also optional. Missing country package → structured error, not ImportError.
- This story is P1 (post-MVP) per backlog. It unblocks future orchestrator stories that need live computation instead of pre-computed files.

### OpenFisca Python API Reference

The adapter interacts with these OpenFisca classes:

```python
# TaxBenefitSystem — loaded from country package
from openfisca_france import FranceTaxBenefitSystem
tax_benefit_system = FranceTaxBenefitSystem()

# SimulationBuilder — constructs simulations
from openfisca_core.simulation_builder import SimulationBuilder
builder = SimulationBuilder()
simulation = builder.build_from_entities(tax_benefit_system, params_dict)

# Simulation — runs calculations
result_array = simulation.calculate("income_tax", "2025")  # Returns numpy array
```

Entity dict format expected by `build_from_entities`:
```python
{
    "persons": {"person_0": {"salary": {"2025": 30000.0}}, ...},
    "households": {"household_0": {"parents": ["person_0"], ...}}
}
```

## References

- [_bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md](/_bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md) (BKL-106)
- [_bmad-output/planning-artifacts/architecture.md](/_bmad-output/planning-artifacts/architecture.md) (Computation Adapter Pattern, Subsystems)
- [_bmad-output/planning-artifacts/prd.md](/_bmad-output/planning-artifacts/prd.md) (FR2, NFR15)
- [/src/reformlab/computation/adapter.py](/src/reformlab/computation/adapter.py) (ComputationAdapter protocol)
- [/src/reformlab/computation/openfisca_adapter.py](/src/reformlab/computation/openfisca_adapter.py) (existing pre-computed adapter, version checking logic)
- [/src/reformlab/computation/types.py](/src/reformlab/computation/types.py) (ComputationResult, PopulationData, PolicyConfig)
- [/src/reformlab/computation/exceptions.py](/src/reformlab/computation/exceptions.py) (CompatibilityError)
- [/src/reformlab/computation/mock_adapter.py](/src/reformlab/computation/mock_adapter.py) (test adapter pattern reference)
- [/src/reformlab/computation/__init__.py](/src/reformlab/computation/__init__.py) (export conventions)
- [_bmad-output/implementation-artifacts/1-5-add-data-quality-checks.md](/_bmad-output/implementation-artifacts/1-5-add-data-quality-checks.md) (previous story)
- [OpenFisca Simulations API](https://openfisca.org/doc/openfisca-python-api/simulations.html)
- [OpenFisca SimulationBuilder API](https://openfisca.org/doc/openfisca-python-api/simulation_generator.html)

## Latest Tech Information

- **OpenFisca-Core**
  - Project requirement: `openfisca-core>=44.0.0` (optional dependency)
  - Supported versions in adapter: `44.0.0` through `44.2.2`
  - Key API classes: `TaxBenefitSystem`, `SimulationBuilder`, `Simulation`
  - `SimulationBuilder.build_from_entities()` accepts nested dict with entity/variable/period structure
  - `Simulation.calculate()` returns NumPy arrays

- **PyArrow**
  - Project requirement: `pyarrow>=18.0.0`
  - Local environment: `23.0.1`
  - Used for all internal data representation. NumPy arrays from OpenFisca must be converted via `pa.array(numpy_array)`.

- **Python**
  - Project requirement: `>=3.13`
  - Local interpreter: `3.13.0`

- **NumPy** (transitive via OpenFisca)
  - OpenFisca returns NumPy arrays from `Simulation.calculate()`.
  - PyArrow's `pa.array()` accepts NumPy arrays directly — zero-copy when dtype is compatible.
  - Do not add NumPy as a direct dependency; it comes transitively through openfisca-core.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (Claude Code CLI)

### Debug Log References

- Initial test run had 13 failures due to patching `from` imports inside methods. Fixed by injecting fake `openfisca_core.simulation_builder` module into `sys.modules` and using `patch.object` instead of string-based `patch`.

### Completion Notes List

- Extracted shared version-checking logic (`_detect_openfisca_version`, `_check_version`, `SUPPORTED_VERSIONS`, `MIN_SUPPORTED`, `COMPAT_MATRIX_URL`) to new `openfisca_common.py` module. Updated `openfisca_adapter.py` to re-export these for backward compatibility.
- Created `ApiMappingError` in `exceptions.py` as a structured error for entity/variable mapping failures in API mode (the existing `MappingError` requires `file_path` which doesn't apply to API operations). Follows project `[summary] - [reason] - [fix]` pattern.
- `OpenFiscaApiAdapter` satisfies `ComputationAdapter` protocol via structural typing (no inheritance).
- All OpenFisca imports are lazy (inside methods) since `openfisca-core` is optional.
- TaxBenefitSystem is lazily loaded on first `compute()` and cached.
- Output variable validation uses `difflib.get_close_matches` for helpful suggestions.
- Policy parameters are validated against TBS variables before simulation build.
- Entity keys in `PopulationData.tables` are validated against TBS entity names.
- 26 new tests cover all 9 acceptance criteria with mocked OpenFisca internals.
- All 167 tests pass (141 existing + 26 new). No regressions.

### File List

New files:

- `src/reformlab/computation/openfisca_api_adapter.py`
- `src/reformlab/computation/openfisca_api_adapter.pyi`
- `src/reformlab/computation/openfisca_common.py`
- `tests/computation/test_openfisca_api_adapter.py`

Modified files:

- `src/reformlab/computation/__init__.py` (added `OpenFiscaApiAdapter`, `ApiMappingError` exports)
- `src/reformlab/computation/__init__.pyi` (added `OpenFiscaApiAdapter`, `ApiMappingError` stub exports)
- `src/reformlab/computation/exceptions.py` (added `ApiMappingError` class)
- `src/reformlab/computation/exceptions.pyi` (added `ApiMappingError` stub)
- `src/reformlab/computation/openfisca_adapter.py` (replaced inline version logic with imports from `openfisca_common.py`)

## Change Log

- 2026-02-26: Implemented Story 1.6 — Added `OpenFiscaApiAdapter` for live OpenFisca computation via Python API. Extracted shared version-checking to `openfisca_common.py`. Added `ApiMappingError` for structured mapping errors. 26 new tests, all quality gates pass.
