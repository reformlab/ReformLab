<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 9 -->
<!-- Story: 3 -->
<!-- Phase: validate-story-synthesis -->
<!-- Timestamp: 20260301T193918Z -->
<compiled-workflow>
<mission><![CDATA[

Master Synthesis: Story 9.3

You are synthesizing 2 independent validator reviews.

Your mission:
1. VERIFY each issue raised by validators
   - Cross-reference with story content
   - Identify false positives (issues that aren't real problems)
   - Confirm valid issues with evidence

2. PRIORITIZE real issues by severity
   - Critical: Blocks implementation or causes major problems
   - High: Significant gaps or ambiguities
   - Medium: Improvements that would help
   - Low: Nice-to-have suggestions

3. SYNTHESIZE findings
   - Merge duplicate issues from different validators
   - Note validator consensus (if 3+ agree, high confidence)
   - Highlight unique insights from individual validators

4. APPLY changes to story file
   - You have WRITE PERMISSION to modify the story
   - CRITICAL: Before using Edit tool, ALWAYS Read the target file first
   - Use EXACT content from Read tool output as old_string, NOT content from this prompt
   - If Read output is truncated, use offset/limit parameters to locate the target section
   - Apply fixes for verified issues
   - Document what you changed and why

Output format:
## Synthesis Summary
## Issues Verified (by severity)
## Issues Dismissed (false positives with reasoning)
## Changes Applied

]]></mission>
<context>
<file id="b5c6fe32" path="_bmad-output/project-context.md" label="PROJECT CONTEXT"><![CDATA[

---
project_name: 'ReformLab'
user_name: 'Lucas'
date: '2026-02-27'
status: 'complete'
sections_completed: ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'code_quality', 'workflow_rules', 'critical_rules']
rule_count: 38
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

- **Python 3.13+** — `target-version = "py313"` (ruff), `python_version = "3.13"` (mypy strict)
- **uv** — package manager, **hatchling** — build backend
- **pyarrow >= 18.0.0** — canonical data type (`pa.Table`), CSV/Parquet I/O
- **pyyaml >= 6.0.2** — YAML template/config loading
- **jsonschema >= 4.23.0** — JSON Schema validation for templates
- **openfisca-core >= 44.0.0** — optional dependency (`[openfisca]` extra); never import outside adapter modules
- **pytest >= 8.3.3, ruff >= 0.15.0, mypy >= 1.19.0** — dev tooling
- **Planned frontend:** React 18+ / TypeScript / Vite / Shadcn/ui / Tailwind v4
- **Planned backend API:** FastAPI + uvicorn
- **Planned deployment:** Kamal 2 on Hetzner CX22

### Version Constraints

- mypy runs in **strict mode** with explicit `ignore_missing_imports` overrides for openfisca, pyarrow, jsonschema, yaml
- OpenFisca is optional — core library must function without it installed

## Critical Implementation Rules

### Python Language Rules

- **Every file starts with** `from __future__ import annotations` — no exceptions
- **Use `if TYPE_CHECKING:` guards** for imports that are only needed for annotations or would create circular dependencies; do the runtime import locally where needed
- **Frozen dataclasses are the default** — all domain types use `@dataclass(frozen=True)`; mutate via `dataclasses.replace()`, never by assignment
- **Protocols, not ABCs** — interfaces are `Protocol` + `@runtime_checkable`; no abstract base classes; structural (duck) typing only
- **Subsystem-specific exceptions** — each module defines its own error hierarchy; never raise bare `Exception` or `ValueError` for domain errors
- **Metadata bags** use `dict[str, Any]` with **stable string-constant keys** defined at module level (e.g., `STEP_EXECUTION_LOG_KEY`)
- **Union syntax** — use `X | None` not `Optional[X]`; use `dict[str, int]` not `Dict[str, int]` (modern generics, no `typing` aliases)
- **`tuple[...]` for immutable sequences** — function parameters and return types that are ordered-and-fixed use `tuple`, not `list`

### Architecture & Framework Rules

- **Adapter isolation is absolute** — only `computation/openfisca_adapter.py` and `openfisca_api_adapter.py` may import OpenFisca; all other code uses the `ComputationAdapter` protocol
- **Step pipeline contract** — steps implement `OrchestratorStep` protocol (`name` + `execute(year, state) -> YearState`); bare callables accepted via `adapt_callable()`; registration via `StepRegistry` with topological sort on `depends_on`
- **Template packs are YAML** — live in `src/reformlab/templates/packs/{policy_type}/`; validated against JSON Schemas in `templates/schema/`; each policy type has its own subpackage with `compute.py` + `compare.py`
- **Data flows through PyArrow** — `PopulationData` (dict of `pa.Table` by entity) → adapter → `ComputationResult` (`pa.Table`) → `YearState.data` → `PanelOutput` (stacked table) → indicators
- **`YearState` is the state token** — passed between steps and years; immutable (frozen dataclass); updated via `replace()`
- **Orchestrator is the core product** — never build custom policy engines, formula compilers, or entity graph engines; OpenFisca handles computation, this project handles orchestration

### Testing Rules

- **Mirror source structure** — `tests/{subsystem}/` matches `src/reformlab/{subsystem}/`; each has `__init__.py` and `conftest.py`
- **Class-based test grouping** — group tests by feature or acceptance criterion (e.g., `TestOrchestratorBasicExecution`); reference story/AC IDs in comments and docstrings
- **Fixtures in conftest.py** — subsystem-specific fixtures per `conftest.py`; build PyArrow tables inline, use `tmp_path` for I/O, golden YAML files in `tests/fixtures/`
- **Direct assertions** — use plain `assert`; no custom assertion helpers; use `pytest.raises(ExceptionClass, match=...)` for errors
- **Test helpers are explicit** — import shared callables from conftest directly (`from tests.orchestrator.conftest import ...`); no hidden magic
- **Golden file tests** — YAML fixtures in `tests/fixtures/templates/`; test load → validate → round-trip cycle
- **MockAdapter for unit tests** — never use real OpenFisca in orchestrator/template/indicator unit tests; `MockAdapter` is the standard test double

### Code Quality & Style Rules

- **ruff** enforces `E`, `F`, `I`, `W` rule sets; `src = ["src"]`; target Python 3.13
- **mypy strict** — all code must pass `mypy --strict`; new modules need `ignore_missing_imports` overrides in `pyproject.toml` only for third-party libs without stubs
- **File naming** — `snake_case.py` throughout; no PascalCase or kebab-case files
- **Class naming** — PascalCase for classes (`OrchestratorStep`, `CarbonTaxParameters`); no suffixes like `Impl` or `Base`
- **Module-level docstrings** — every module has a docstring explaining its role, referencing relevant story/FR
- **Section separators** — use `# ====...====` comment blocks to separate major sections within longer modules (see `step.py`)
- **No wildcard imports** — always import specific names; `from reformlab.orchestrator import Orchestrator, OrchestratorConfig`
- **Logging** — use `logging.getLogger(__name__)`; structured key=value format for parseable log lines (e.g., `year=%d seed=%s event=year_start`)

### Development Workflow Rules

- **Package manager is uv** — use `uv pip install`, `uv run pytest`, etc.; not `pip` directly
- **Test command** — `uv run pytest tests/` (or specific subsystem path)
- **Lint command** — `uv run ruff check src/ tests/` and `uv run mypy src/`
- **Source layout** — `src/reformlab/` is the installable package; `tests/` is separate; `pythonpath = ["src"]` in pytest config
- **Build system** — hatchling with `packages = ["src/reformlab"]`
- **No auto-formatting on save assumed** — agents must produce ruff-compliant code; run `ruff check --fix` if needed

### Critical Don't-Miss Rules

- **Never import OpenFisca outside adapter modules** — this is the single most important architectural boundary; violation couples the entire codebase to one backend
- **All domain types are frozen** — never add a mutable dataclass; if you need mutation, use `dataclasses.replace()` and return a new instance
- **Determinism is non-negotiable** — every run must be reproducible; seeds are explicit, logged in manifests, derived deterministically (`master_seed XOR year`)
- **Data contracts fail loudly** — contract validation at ingestion boundaries is field-level and blocking; never silently coerce or drop data
- **Assumption transparency** — every run produces a manifest (JSON); assumptions, versions, seeds, data hashes are all recorded
- **PyArrow is the canonical data type** — do not use pandas DataFrames in core logic; `pa.Table` is the standard; pandas only at display/export boundaries if needed
- **No custom formula compiler** — environmental policy logic is Python code in template `compute.py` modules, not YAML formula strings or DSLs
- **France/Europe first** — initial scenarios use French policy parameters (EUR, INSEE deciles, French carbon tax rates); European data sources (Eurostat, EU-SILC)

---

## Usage Guidelines

**For AI Agents:**

- Read this file before implementing any code
- Follow ALL rules exactly as documented
- When in doubt, prefer the more restrictive option
- Update this file if new patterns emerge

**For Humans:**

- Keep this file lean and focused on agent needs
- Update when technology stack changes
- Review quarterly for outdated rules
- Remove rules that become obvious over time

Last Updated: 2026-02-27


]]></file>
<file id="ccd1eda3" path="_bmad-output/implementation-artifacts/9-3-add-variable-periodicity-handling.md" label="STORY FILE"><![CDATA[

# Story 9.3: Add Variable Periodicity Handling

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **platform developer integrating OpenFisca-France**,
I want the adapter to automatically detect variable periodicities and use the correct OpenFisca calculation method (`calculate()` vs `calculate_add()`),
so that monthly variables (e.g., `salaire_net`) are correctly summed over yearly periods without crashing, and yearly/eternity variables continue to work as before.

## Context & Motivation

OpenFisca variables have a `definition_period` attribute that specifies the temporal granularity at which they are computed. In OpenFisca-France:

| Periodicity | `definition_period` | Example Variables | `calculate("var", "2024")` behavior |
|---|---|---|---|
| Monthly | `DateUnit.MONTH` ("month") | `salaire_net`, `salaire_de_base` | **Raises `ValueError`** — period mismatch |
| Yearly | `DateUnit.YEAR` ("year") | `impot_revenu_restant_a_payer`, `revenu_disponible` | Works — period matches |
| Eternal | `DateUnit.ETERNITY` ("eternity") | `date_naissance`, `sexe` | Works — any period accepted |

**The current adapter uses `simulation.calculate()` for ALL variables** (line 503 of `openfisca_api_adapter.py`). This crashes with a `ValueError` for monthly variables like `salaire_net` when the period is yearly (e.g., `"2024"`).

**The fix:** Detect each variable's `definition_period` from the TBS and dispatch to the correct calculation method:
- `MONTH`/`DAY`/`WEEK`/`WEEKDAY` → `simulation.calculate_add(var, period)` — sums sub-period values over the requested period
- `YEAR` → `simulation.calculate(var, period)` — direct calculation (current behavior)
- `ETERNITY` → `simulation.calculate(var, period)` — always accepted by OpenFisca

**Source:** Spike 8-1 findings, Gap 4. [Source: `_bmad-output/implementation-artifacts/spike-findings-8-1-openfisca-integration.md`, lines 71-77]

## Acceptance Criteria

1. **AC-1: Periodicity-aware calculation dispatch** — Given variables with different periodicities (monthly, yearly), when `compute()` is called with a yearly period, then the adapter uses `calculate_add()` for monthly variables and `calculate()` for yearly/eternity variables — producing correct results without `ValueError`.

2. **AC-2: Monthly variable yearly aggregation** — Given a monthly variable (e.g., `salaire_net`) requested for a yearly period, when computed, then the adapter automatically sums the 12 monthly values via `calculate_add()` according to OpenFisca conventions.

3. **AC-3: Invalid period format rejection** — Given an invalid period value (non-positive integer, zero, or unreasonable year), when passed to the adapter's `compute()`, then a clear `ApiMappingError` is raised identifying the expected format.

4. **AC-4: Backward compatibility** — Given output variables that are all yearly (the existing common case), when `compute()` is called, then behavior is identical to the pre-change implementation — no regression in results, metadata, or `entity_tables`.

5. **AC-5: Periodicity metadata** — Given a completed `compute()` call, when the result metadata is inspected, then it includes `"variable_periodicities"` mapping each output variable to its detected periodicity and the calculation method used.

6. **AC-6: Eternity variable handling** — Given an ETERNITY-period variable as an output variable, when `compute()` is called, then `simulation.calculate()` is used (NOT `calculate_add()`, which rejects eternity variables) and the value is returned correctly.

## Tasks / Subtasks

- [ ] Task 1: Add `_resolve_variable_periodicities()` method (AC: #1, #2, #6)
  - [ ] 1.1 Add method to `OpenFiscaApiAdapter` that queries `tbs.variables[var_name].definition_period` for each output variable
  - [ ] 1.2 Return `dict[str, str]` mapping variable name to periodicity string (`"month"`, `"year"`, `"eternity"`, `"day"`, `"week"`, `"weekday"`)
  - [ ] 1.3 Handle edge case where `definition_period` attribute is missing or has unexpected value — raise `ApiMappingError`
  - [ ] 1.4 Unit tests with mock TBS: verify periodicity detection for month/year/eternity variables, error on missing attribute

- [ ] Task 2: Add `_calculate_variable()` dispatch method (AC: #1, #2, #6)
  - [ ] 2.1 Add private method `_calculate_variable(simulation, var_name, period_str, periodicity) -> numpy.ndarray`
  - [ ] 2.2 Dispatch logic: `"month"`, `"day"`, `"week"`, `"weekday"` → `simulation.calculate_add(var, period_str)`; `"year"`, `"eternity"` → `simulation.calculate(var, period_str)`
  - [ ] 2.3 Log calculation method used per variable at DEBUG level
  - [ ] 2.4 Unit tests with mock simulation: verify correct method called based on periodicity

- [ ] Task 3: Refactor `_extract_results_by_entity()` to use periodicity-aware calculation (AC: #1, #2, #4, #6)
  - [ ] 3.1 Add `variable_periodicities: dict[str, str]` parameter to `_extract_results_by_entity()`
  - [ ] 3.2 Replace `simulation.calculate(var_name, period_str)` with `self._calculate_variable(simulation, var_name, period_str, variable_periodicities[var_name])`
  - [ ] 3.3 Unit tests: verify multi-entity extraction with mixed periodicities

- [ ] Task 4: Wire periodicity resolution into `compute()` (AC: #1, #2, #4, #5)
  - [ ] 4.1 Call `_resolve_variable_periodicities(tbs)` in `compute()` after `_resolve_variable_entities()` (fail-fast pattern — resolve both before building simulation)
  - [ ] 4.2 Pass `variable_periodicities` to `_extract_results_by_entity()`
  - [ ] 4.3 Add `"variable_periodicities"` and `"calculation_methods"` to result metadata
  - [ ] 4.4 Unit tests: verify metadata populated correctly in compute() result

- [ ] Task 5: Add period validation (AC: #3)
  - [ ] 5.1 Add validation at the top of `compute()`: period must be a positive integer in range [1000, 9999] (4-digit year)
  - [ ] 5.2 Raise `ApiMappingError` with summary "Invalid period", reason showing actual value, fix showing expected format
  - [ ] 5.3 Unit tests: invalid periods (0, -1, 99, 99999) raise `ApiMappingError`; valid periods (2024, 2025) pass

- [ ] Task 6: Verify backward compatibility (AC: #4)
  - [ ] 6.1 Run existing unit tests in `test_openfisca_api_adapter.py` — ensure all pass unchanged
  - [ ] 6.2 Run existing integration tests in `test_openfisca_integration.py` — ensure all pass unchanged
  - [ ] 6.3 Verify `MockAdapter` still produces valid `ComputationResult` (no new required fields)
  - [ ] 6.4 Verify `ComputationStep` in orchestrator still works (`result.output_fields.num_rows`)

- [ ] Task 7: Integration tests with real OpenFisca-France (AC: #1, #2, #6)
  - [ ] 7.1 Test: `salaire_net` (MONTH) with yearly period → verify `calculate_add()` is used and returns correct yearly sum
  - [ ] 7.2 Test: `impot_revenu_restant_a_payer` (YEAR) with yearly period → verify `calculate()` is used (unchanged)
  - [ ] 7.3 Test: mixed periodicity output variables in single `compute()` call → verify correct method per variable
  - [ ] 7.4 Test: `adapter.compute()` end-to-end with monthly output variable produces correct values
  - [ ] 7.5 Test: verify `variable_periodicities` metadata in integration test result
  - [ ] 7.6 Mark integration tests with `@pytest.mark.integration`

- [ ] Task 8: Run quality gates (all ACs)
  - [ ] 8.1 `uv run ruff check src/ tests/`
  - [ ] 8.2 `uv run mypy src/`
  - [ ] 8.3 `uv run pytest tests/computation/ tests/orchestrator/`

## Dev Notes

### Architecture Constraints

- **Adapter isolation is absolute**: Only `computation/openfisca_adapter.py` and `openfisca_api_adapter.py` may import OpenFisca. All OpenFisca imports must be lazy (inside methods, not at module level).
- **Frozen dataclasses**: `ComputationResult` is `@dataclass(frozen=True)`. No new fields are added in this story — only metadata entries.
- **Protocol compatibility**: `ComputationAdapter` protocol (`period: int`) is unchanged. The periodicity handling is internal to `OpenFiscaApiAdapter`.
- **PyArrow is canonical**: All data containers use `pa.Table`. No pandas.
- **`from __future__ import annotations`** at top of every file.
- **No bare `Exception` or `ValueError`**: Use subsystem-specific exceptions (`ApiMappingError`).

### OpenFisca Periodicity System — Complete Reference

**`DateUnit` is a `StrEnum`** (from `openfisca_core.periods.date_unit`):

```python
class DateUnit(StrEnum, metaclass=DateUnitMeta):
    WEEKDAY = "weekday"    # weight: 100
    WEEK = "week"          # weight: 200
    DAY = "day"            # weight: 100
    MONTH = "month"        # weight: 200
    YEAR = "year"          # weight: 300
    ETERNITY = "eternity"  # weight: 400
```

Since `DateUnit` extends `StrEnum`:
```python
variable.definition_period == "month"   # True (StrEnum comparison)
str(variable.definition_period)          # "month"
variable.definition_period.value         # "month"
variable.definition_period.name          # "MONTH"
```

**Accessing a variable's periodicity:**
```python
variable = tbs.variables["salaire_net"]
periodicity = variable.definition_period  # DateUnit.MONTH (a StrEnum)
# Since it's StrEnum, string comparison works directly:
if periodicity == "month":
    ...
```

### OpenFisca Calculation Method Dispatch

**`simulation.calculate(var, period)`:**
- Calls `_check_period_consistency()` which raises `ValueError` if `definition_period` doesn't match the period's unit
- ETERNITY: always accepted (any period)
- YEAR: requires yearly period
- MONTH: requires monthly period → **fails with yearly period**
- DAY: requires daily period

**`simulation.calculate_add(var, period)`:**
- Sums sub-period values: `sum(calculate(var, sub_period) for sub_period in period.get_subperiods(definition_period))`
- For MONTH variable with "2024" period → sums 12 monthly calculations
- REJECTS ETERNITY variables explicitly: "eternal variables can't be summed over time"
- Rejects if `unit_weight(definition_period) > unit_weight(period.unit)` (can't sum larger into smaller)

**`simulation.calculate_divide(var, period)`:**
- Divides a larger-period variable into smaller periods (e.g., yearly / 12 for monthly)
- Not needed for this story (we only have yearly periods as input)

### Dispatch Table (for yearly period input)

| `definition_period` | Method to use | Rationale |
|---|---|---|
| `"month"` | `calculate_add()` | Sum 12 monthly values to yearly |
| `"year"` | `calculate()` | Period matches directly |
| `"eternity"` | `calculate()` | Any period accepted; `calculate_add()` rejects eternity |
| `"day"` | `calculate_add()` | Sum ~365 daily values to yearly |
| `"week"` | `calculate_add()` | Sum ~52 weekly values to yearly |
| `"weekday"` | `calculate_add()` | Sum weekday values to yearly |

**Simplified rule:** Use `calculate()` for `"year"` and `"eternity"`, `calculate_add()` for everything else.

### Files to Modify

| File | Change |
|------|--------|
| `src/reformlab/computation/openfisca_api_adapter.py` | Add `_resolve_variable_periodicities()`, `_calculate_variable()`, refactor `_extract_results_by_entity()`, add period validation in `compute()` |
| `tests/computation/test_openfisca_api_adapter.py` | Add unit tests for periodicity detection, calculation dispatch, period validation |
| `tests/computation/test_openfisca_integration.py` | Add integration tests with monthly variables (`salaire_net`) |

### Files to Verify (No Changes Expected)

| File | Why |
|------|-----|
| `src/reformlab/computation/adapter.py` | Protocol unchanged (`period: int`) |
| `src/reformlab/computation/types.py` | `ComputationResult` unchanged — no new fields |
| `src/reformlab/computation/types.pyi` | Type stub unchanged |
| `src/reformlab/computation/mock_adapter.py` | Unaffected — no periodicity logic needed |
| `src/reformlab/computation/exceptions.py` | Reuse existing `ApiMappingError` — no new exception types |
| `src/reformlab/orchestrator/computation_step.py` | Passes `period=year` (int) to adapter — unchanged |
| `src/reformlab/orchestrator/panel.py` | Accesses `comp_result.output_fields` — unchanged |

### Backward Compatibility Strategy

This story is purely **internal to `OpenFiscaApiAdapter`** — no external interface changes:

1. `ComputationAdapter` protocol is unchanged (`period: int`).
2. `ComputationResult` is unchanged (no new fields; periodicity info goes in existing `metadata` dict).
3. `MockAdapter` is unaffected — it never calls OpenFisca.
4. Existing unit tests with mock TBS continue to work because `_make_mock_tbs()` creates variables with a default entity that (now) also needs a default `definition_period`. The existing mock assigns all variables to the person entity; Story 9.3 must ensure that mocks also set `definition_period` (default to `"year"` for backward compatibility).
5. `_extract_results_by_entity()` signature changes (new `variable_periodicities` parameter) — this is a private method, no external consumers.

### Mock TBS Extension for Unit Tests

Extend existing `_make_mock_tbs()` and `_make_mock_tbs_with_entities()` in the test file to include `definition_period`:

```python
# Existing _make_mock_tbs() — add default definition_period
def _make_mock_tbs(...):
    ...
    for name in variable_names:
        var_mock = MagicMock()
        var_mock.entity = default_entity
        var_mock.definition_period = "year"  # Default for backward compat
        variables[name] = var_mock
    ...

# New helper or extend _make_mock_tbs_with_entities()
def _make_mock_tbs_with_periodicities(
    variable_entities: dict[str, str],
    variable_periodicities: dict[str, str],
    ...
) -> MagicMock:
    """Create a mock TBS with both entity and periodicity info."""
    ...
    for var_name in variable_entities:
        var_mock = MagicMock()
        var_mock.entity = entities_by_key[variable_entities[var_name]]
        var_mock.definition_period = variable_periodicities.get(var_name, "year")
        variables[var_name] = var_mock
    ...
```

### Mock Simulation Extension for Unit Tests

The existing `_make_mock_simulation()` returns results keyed by variable name. For periodicity dispatch tests, extend to track which method was called:

```python
def _make_mock_simulation_with_methods(
    results: dict[str, numpy.ndarray],
) -> MagicMock:
    """Mock simulation that tracks calculate vs calculate_add calls."""
    sim = MagicMock()
    sim.calculate.side_effect = lambda var, period: results[var]
    sim.calculate_add.side_effect = lambda var, period: results[var]
    return sim
```

Then assert: `sim.calculate.assert_called_with("irpp", "2024")` and `sim.calculate_add.assert_called_with("salaire_net", "2024")`.

### Integration Test Reference Data

**Monthly variable test case — `salaire_net` for single person with 30k base salary:**

```python
# Input: salaire_de_base = 30000.0 (yearly salary base)
# Output: salaire_net = sum of 12 monthly net salary values
# Expected: salaire_net should be positive and in range [20000, 30000]
# (net salary is less than gross due to social contributions)

population = PopulationData(
    tables={
        "individu": pa.table({
            "salaire_de_base": pa.array([30000.0]),
            "age": pa.array([30]),
        }),
    },
)
```

**Mixed periodicity test case — `salaire_net` (MONTH) + `impot_revenu_restant_a_payer` (YEAR):**

```python
# Using multi-entity adapter with mixed periodicities:
adapter = OpenFiscaApiAdapter(
    country_package="openfisca_france",
    output_variables=(
        "salaire_net",                      # individu, MONTH → calculate_add
        "impot_revenu_restant_a_payer",      # foyer_fiscal, YEAR → calculate
    ),
)
# Both variables should return correct values without ValueError
```

### Existing Integration Test Fix Required

The existing integration test `test_multi_entity_variable_array_lengths` (line 305 in `test_openfisca_integration.py`) already uses `calculate_add` for `salaire_net` manually:

```python
salaire_net = simulation.calculate_add("salaire_net", "2024")
```

This test calls OpenFisca directly (not through the adapter). After Story 9.3, new integration tests should verify that the **adapter** itself correctly dispatches to `calculate_add()` for monthly variables.

### What This Story Does NOT Cover

- **Input variable period assignment** — `_population_to_entity_dict()` wraps all input values in `{period_str: value}`. Some input variables may need monthly period format (e.g., `"2024-01"` instead of `"2024"` for `age`). This is a separate concern for future work (potentially Story 9.4 or a follow-up).
- **Sub-yearly period support in the protocol** — `ComputationAdapter.compute(period: int)` remains yearly. Supporting monthly computation periods would require protocol changes.
- **`calculate_divide()` support** — Not needed since the adapter only handles yearly periods (the largest common unit).
- **PopulationData 4-entity format** — That is Story 9.4.
- **Entity broadcasting** — Broadcasting group-level values to person level is not in scope.
- **Modifying `MockAdapter`** — It never calls OpenFisca and doesn't need periodicity logic.

### Project Structure Notes

- Source layout: `src/reformlab/` is the installable package
- Tests mirror source: `tests/computation/` matches `src/reformlab/computation/`
- Each test subdirectory has `__init__.py` and `conftest.py`
- Class-based test grouping with AC references in docstrings
- Integration tests require `openfisca-france` optional dependency: `uv sync --extra openfisca`
- Run unit tests: `uv run pytest tests/computation/ -m "not integration"`
- Run integration tests: `uv run pytest tests/computation/ -m integration`
- Quality gates: `uv run ruff check src/ tests/` and `uv run mypy src/`

### References

- [Source: `_bmad-output/implementation-artifacts/spike-findings-8-1-openfisca-integration.md` — Gap 4: Monthly vs yearly variable periodicity]
- [Source: `src/reformlab/computation/openfisca_api_adapter.py` — `_extract_results_by_entity()` method, line 503: `simulation.calculate(var_name, period_str)`]
- [Source: `.venv/.../openfisca_core/periods/date_unit.py` — `DateUnit(StrEnum)` definition with MONTH, YEAR, ETERNITY values]
- [Source: `.venv/.../openfisca_core/simulations/simulation.py` — `_check_period_consistency()` lines 353-374: raises ValueError for period mismatch]
- [Source: `.venv/.../openfisca_core/simulations/simulation.py` — `calculate_add()` lines 180-223: sums sub-periods, rejects ETERNITY]
- [Source: `.venv/.../openfisca_core/variables/variable.py` — `definition_period` attribute, line 144: required, allowed_values=DateUnit]
- [Source: `src/reformlab/computation/adapter.py` — `ComputationAdapter` protocol, `period: int` parameter]
- [Source: `src/reformlab/computation/exceptions.py` — `ApiMappingError` structured error pattern]
- [Source: `src/reformlab/orchestrator/computation_step.py` — downstream consumer, passes `period=year` to adapter]
- [Source: `_bmad-output/implementation-artifacts/9-2-handle-multi-entity-output-arrays.md` — predecessor story, explicitly excludes periodicity handling]
- [Source: `_bmad-output/planning-artifacts/epics.md` — Epic 9, Story 9.3 acceptance criteria]
- [Source: `tests/computation/test_openfisca_integration.py` — lines 305-314: `calculate_add("salaire_net", "2024")` used manually in existing test]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (via create-story workflow)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed — comprehensive developer guide created
- All 3 acceptance criteria from epics file expanded to 6 ACs with backward compatibility, metadata, and eternity variable coverage
- Spike 8-1 findings Gap 4 fully integrated as context with root cause analysis
- OpenFisca periodicity system documented from source code inspection:
  - `DateUnit` is a `StrEnum` — string comparison works directly
  - `calculate()` raises `ValueError` for MONTH variables with yearly periods
  - `calculate_add()` sums sub-periods but REJECTS ETERNITY variables
  - Complete dispatch table documented for all 6 `DateUnit` values
- `_check_period_consistency()` source code analyzed (simulation.py lines 353-374) to understand exact failure mode
- `calculate_add()` source code analyzed (simulation.py lines 180-223) to understand ETERNITY rejection and sub-period iteration
- Backward compatibility strategy: purely internal changes to `OpenFiscaApiAdapter`, no protocol/type/mock changes
- Mock TBS extension patterns documented for unit tests (add `definition_period` to variable mocks)
- Integration test reference data documented (salaire_net monthly, mixed periodicity cases)
- Story 9.2 predecessor analysis: confirms explicit exclusion of periodicity ("What This Story Does NOT Cover")

### File List

- `src/reformlab/computation/openfisca_api_adapter.py` — modify (add `_resolve_variable_periodicities()`, `_calculate_variable()`, refactor `_extract_results_by_entity()`, add period validation)
- `tests/computation/test_openfisca_api_adapter.py` — modify (add periodicity unit tests, extend mock TBS with `definition_period`)
- `tests/computation/test_openfisca_integration.py` — modify (add monthly variable integration tests)


]]></file>
<file id="65375f24" path="src/reformlab/computation/openfisca_api_adapter.py" label="SOURCE CODE"><![CDATA[

"""Adapter that executes OpenFisca computations via the Python API.

Unlike ``OpenFiscaAdapter`` (pre-computed file mode), this adapter
runs live tax-benefit calculations using OpenFisca's ``SimulationBuilder``.

All OpenFisca imports are lazy since ``openfisca-core`` is an optional
dependency.

Story 9.2: Added entity-aware result extraction to correctly handle
output variables belonging to different entity types (individu, menage,
famille, foyer_fiscal).
"""

from __future__ import annotations

import difflib
import logging
import time
from typing import Any

import pyarrow as pa

from reformlab.computation.exceptions import ApiMappingError, CompatibilityError
from reformlab.computation.openfisca_common import (
    _check_version,
    _detect_openfisca_version,
)
from reformlab.computation.types import ComputationResult, PolicyConfig, PopulationData

logger = logging.getLogger(__name__)


class OpenFiscaApiAdapter:
    """Adapter that executes OpenFisca computations via the Python API.

    Unlike ``OpenFiscaAdapter`` (pre-computed file mode), this adapter
    runs live tax-benefit calculations using OpenFisca's ``SimulationBuilder``.
    """

    def __init__(
        self,
        *,
        country_package: str = "openfisca_france",
        output_variables: tuple[str, ...],
        skip_version_check: bool = False,
    ) -> None:
        if not output_variables:
            raise ApiMappingError(
                summary="Empty output_variables",
                reason="output_variables tuple is empty — no variables to compute",
                fix="Provide at least one valid output variable name.",
                invalid_names=(),
                valid_names=(),
            )
        self._country_package = country_package
        self._output_variables = output_variables

        if not skip_version_check:
            self._version = _detect_openfisca_version()
            _check_version(self._version)
        else:
            self._version = "unknown"

        self._tax_benefit_system: Any = None

    def version(self) -> str:
        """Return the detected OpenFisca-Core version string."""
        return self._version

    def compute(
        self,
        population: PopulationData,
        policy: PolicyConfig,
        period: int,
    ) -> ComputationResult:
        """Run a live OpenFisca computation for the given inputs.

        Args:
            population: Input population data with entity tables.
            policy: Scenario parameters (applied as input-variable values).
            period: Computation period (integer year, e.g. 2025).

        Returns:
            A ``ComputationResult`` with output variables as a PyArrow Table.
            When output variables span multiple entities, ``entity_tables``
            contains per-entity tables keyed by entity plural name.
        """
        start = time.monotonic()

        tbs = self._get_tax_benefit_system()
        self._validate_output_variables(tbs)

        # Story 9.2: Resolve entity grouping before building simulation (fail fast —
        # avoid expensive SimulationBuilder.build_from_entities() if entity
        # resolution fails due to incompatible country package).
        vars_by_entity = self._resolve_variable_entities(tbs)

        simulation = self._build_simulation(population, policy, period, tbs)
        entity_tables = self._extract_results_by_entity(
            simulation, period, vars_by_entity
        )

        # Determine primary output_fields table for backward compatibility:
        # - Single entity → that entity's table
        # - Multiple entities → person-entity table (or first entity's table)
        output_fields = self._select_primary_output(entity_tables, tbs)

        elapsed = time.monotonic() - start

        # Only expose entity_tables for multi-entity results — keeps metadata
        # consistent with entity_tables (single-entity uses {} for backward compat).
        result_entity_tables = entity_tables if len(entity_tables) > 1 else {}
        output_entities = sorted(result_entity_tables.keys())
        entity_row_counts = {
            entity: table.num_rows for entity, table in result_entity_tables.items()
        }

        return ComputationResult(
            output_fields=output_fields,
            adapter_version=self._version,
            period=period,
            metadata={
                "timing_seconds": round(elapsed, 4),
                "row_count": output_fields.num_rows,
                "source": "api",
                "policy_name": policy.name,
                "country_package": self._country_package,
                "output_variables": list(self._output_variables),
                "output_entities": output_entities,
                "entity_row_counts": entity_row_counts,
            },
            entity_tables=result_entity_tables,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_tax_benefit_system(self) -> Any:
        """Lazily import the country package and cache the TaxBenefitSystem."""
        if self._tax_benefit_system is not None:
            return self._tax_benefit_system

        try:
            import importlib

            module = importlib.import_module(self._country_package)
        except ImportError:
            raise CompatibilityError(
                expected=self._country_package,
                actual="not-installed",
                details=(
                    f"Country package '{self._country_package}' is not installed. "
                    f"Install it with: uv add '{self._country_package}'. "
                    "See https://openfisca.org/doc/ for available country packages."
                ),
            )

        # Country packages expose the TBS via a conventional attribute.
        # openfisca_france → FranceTaxBenefitSystem (via CountryTaxBenefitSystem)
        tbs_class = getattr(module, "CountryTaxBenefitSystem", None)
        if tbs_class is None:
            # Fallback: try the generic TaxBenefitSystem attribute
            tbs_class = getattr(module, "TaxBenefitSystem", None)
        if tbs_class is None:
            raise CompatibilityError(
                expected=f"TaxBenefitSystem in {self._country_package}",
                actual="not found",
                details=(
                    f"Package '{self._country_package}' does not expose "
                    "'CountryTaxBenefitSystem' or 'TaxBenefitSystem'. "
                    "Verify the package is a valid OpenFisca country package."
                ),
            )

        self._tax_benefit_system = tbs_class()
        return self._tax_benefit_system

    def _validate_output_variables(self, tbs: Any) -> None:
        """Check that all requested output variables exist in the TBS."""
        known_variables = set(tbs.variables.keys())
        invalid = [v for v in self._output_variables if v not in known_variables]

        if not invalid:
            return

        suggestions: dict[str, list[str]] = {}
        known_list = sorted(known_variables)
        for name in invalid:
            matches = difflib.get_close_matches(name, known_list, n=3, cutoff=0.6)
            if matches:
                suggestions[name] = matches

        suggestion_lines = []
        for name in invalid:
            if name in suggestions:
                suggestion_lines.append(
                    f"  '{name}' → did you mean: {', '.join(suggestions[name])}?"
                )
            else:
                suggestion_lines.append(f"  '{name}' → no close matches found")

        raise ApiMappingError(
            summary="Unknown output variables",
            reason=(
                f"{len(invalid)} variable(s) not found in "
                f"{self._country_package} TaxBenefitSystem: "
                f"{', '.join(invalid)}"
            ),
            fix=(
                "Check variable names against the country package. "
                "Suggestions:\n" + "\n".join(suggestion_lines)
            ),
            invalid_names=tuple(invalid),
            valid_names=tuple(sorted(known_variables)),
            suggestions=suggestions,
        )

    def _validate_policy_parameters(self, policy: PolicyConfig, tbs: Any) -> None:
        """Check that all policy parameter keys are valid input variables."""
        if not policy.parameters:
            return

        known_variables = set(tbs.variables.keys())
        invalid = [k for k in policy.parameters if k not in known_variables]

        if not invalid:
            return

        suggestions: dict[str, list[str]] = {}
        known_list = sorted(known_variables)
        for name in invalid:
            matches = difflib.get_close_matches(name, known_list, n=3, cutoff=0.6)
            if matches:
                suggestions[name] = matches

        suggestion_lines = []
        for name in invalid:
            if name in suggestions:
                suggestion_lines.append(
                    f"  '{name}' → did you mean: {', '.join(suggestions[name])}?"
                )
            else:
                suggestion_lines.append(f"  '{name}' → no close matches found")

        raise ApiMappingError(
            summary="Unknown policy parameter keys",
            reason=(
                f"{len(invalid)} parameter key(s) not found as variables in "
                f"{self._country_package} TaxBenefitSystem: "
                f"{', '.join(invalid)}"
            ),
            fix=(
                "PolicyConfig.parameters keys must be valid OpenFisca variable names. "
                "Suggestions:\n" + "\n".join(suggestion_lines)
            ),
            invalid_names=tuple(invalid),
            valid_names=tuple(sorted(known_variables)),
            suggestions=suggestions,
        )

    def _build_simulation(
        self,
        population: PopulationData,
        policy: PolicyConfig,
        period: int,
        tbs: Any,
    ) -> Any:
        """Construct an OpenFisca Simulation from population and policy data."""
        from openfisca_core.simulation_builder import SimulationBuilder

        # Validate entity keys against TBS (accept both singular and plural)
        tbs_entity_keys = {entity.key for entity in tbs.entities}
        tbs_entity_plurals = {entity.plural for entity in tbs.entities}
        valid_names = tbs_entity_keys | tbs_entity_plurals
        unknown_entities = [
            key for key in population.tables if key not in valid_names
        ]
        if unknown_entities:
            raise ApiMappingError(
                summary="Unknown entity keys in population data",
                reason=(
                    f"Entity key(s) {', '.join(unknown_entities)} not found in "
                    f"{self._country_package} TaxBenefitSystem"
                ),
                fix=(
                    f"Population entity keys must be one of: "
                    f"{', '.join(sorted(tbs_entity_keys))}. "
                    "Check PopulationData.tables keys."
                ),
                invalid_names=tuple(unknown_entities),
                valid_names=tuple(sorted(tbs_entity_keys)),
            )

        # Validate policy parameters
        self._validate_policy_parameters(policy, tbs)

        # Build entity dict for SimulationBuilder.build_from_entities
        period_str = str(period)
        entities_dict = self._population_to_entity_dict(
            population, policy, period_str, tbs
        )

        builder = SimulationBuilder()
        simulation = builder.build_from_entities(tbs, entities_dict)

        return simulation

    def _population_to_entity_dict(
        self,
        population: PopulationData,
        policy: PolicyConfig,
        period_str: str,
        tbs: Any,
    ) -> dict[str, Any]:
        """Convert PopulationData tables to the dict format expected by OpenFisca.

        OpenFisca's ``build_from_entities`` expects **plural** entity keys::

            {
                "individus": {
                    "person_0": {"salaire_de_base": {"2024": 30000.0}},
                    ...
                },
                "menages": {
                    "menage_0": {"personne_de_reference": ["person_0"]},
                    ...
                }
            }

        PopulationData tables may use either singular (entity.key) or plural
        (entity.plural) keys.  This method normalises to plural.
        """
        result: dict[str, Any] = {}

        # Build key→plural mapping for normalisation
        key_to_plural = {entity.key: entity.plural for entity in tbs.entities}
        plural_set = set(key_to_plural.values())

        # Identify the person entity (singular entity in OpenFisca)
        person_entity_plural: str | None = None
        for entity in tbs.entities:
            if not getattr(entity, "is_person", False):
                continue
            person_entity_plural = entity.plural
            break

        for entity_key, table in population.tables.items():
            # Normalise to plural key
            plural_key = key_to_plural.get(entity_key, entity_key)
            if entity_key in plural_set:
                plural_key = entity_key

            entity_dict: dict[str, Any] = {}
            columns = table.column_names
            num_rows = table.num_rows

            for i in range(num_rows):
                instance_id = f"{entity_key}_{i}"
                instance_data: dict[str, Any] = {}

                for col in columns:
                    value = table.column(col)[i].as_py()
                    # Wrap scalar values in period dict for variable assignments
                    instance_data[col] = {period_str: value}

                entity_dict[instance_id] = instance_data

            result[plural_key] = entity_dict

        # Inject policy parameters as input-variable values on the person entity
        if policy.parameters and person_entity_plural and person_entity_plural in result:
            for instance_id in result[person_entity_plural]:
                for param_key, param_value in policy.parameters.items():
                    result[person_entity_plural][instance_id][param_key] = {
                        period_str: param_value
                    }

        return result

    # ------------------------------------------------------------------
    # Story 9.2: Entity-aware result extraction
    # ------------------------------------------------------------------

    def _resolve_variable_entities(
        self, tbs: Any
    ) -> dict[str, list[str]]:
        """Group output variables by their entity's plural name.

        Queries ``tbs.variables[var_name].entity`` to determine which entity
        each output variable belongs to, then groups them.

        Args:
            tbs: The loaded TaxBenefitSystem.

        Returns:
            Dict mapping entity plural name to list of variable names.
            E.g. ``{"individus": ["salaire_net"], "foyers_fiscaux": ["irpp"]}``.

        Raises:
            ApiMappingError: If a variable's entity cannot be determined.
        """
        vars_by_entity: dict[str, list[str]] = {}

        for var_name in self._output_variables:
            variable = tbs.variables.get(var_name)
            if variable is None:
                # Should not happen — _validate_output_variables runs first.
                # Defensive guard for edge cases.
                raise ApiMappingError(
                    summary="Cannot resolve variable entity",
                    reason=(
                        f"Variable '{var_name}' not found in "
                        f"{self._country_package} TaxBenefitSystem"
                    ),
                    fix=(
                        "Ensure the variable exists in the country package. "
                        "This may indicate the TBS was modified after validation."
                    ),
                    invalid_names=(var_name,),
                    valid_names=tuple(sorted(tbs.variables.keys())),
                )

            entity = getattr(variable, "entity", None)
            if entity is None:
                raise ApiMappingError(
                    summary="Cannot determine entity for variable",
                    reason=(
                        f"Variable '{var_name}' has no .entity attribute in "
                        f"{self._country_package} TaxBenefitSystem"
                    ),
                    fix=(
                        "This variable may not be properly defined in the "
                        "country package. Check the variable definition."
                    ),
                    invalid_names=(var_name,),
                    valid_names=tuple(sorted(tbs.variables.keys())),
                )

            entity_plural = getattr(entity, "plural", None)
            if entity_plural is None:
                # entity.plural is required — silently falling back to entity.key
                # would produce wrong plural keys (e.g. "foyer_fiscal" instead of
                # "foyers_fiscaux") causing subtle downstream lookup failures.
                # This path only occurs with a malformed/incompatible TBS.
                entity_key = getattr(entity, "key", None)
                raise ApiMappingError(
                    summary="Cannot determine entity plural name for variable",
                    reason=(
                        f"Variable '{var_name}' entity has no .plural attribute"
                        + (
                            f" (entity.key={entity_key!r})"
                            if entity_key
                            else ", no .key attribute either"
                        )
                    ),
                    fix=(
                        "This may indicate an incompatible OpenFisca version. "
                        "Check the OpenFisca compatibility matrix."
                    ),
                    invalid_names=(var_name,),
                    valid_names=tuple(sorted(tbs.variables.keys())),
                )

            vars_by_entity.setdefault(entity_plural, []).append(var_name)

        logger.debug(
            "entity_variable_mapping=%s output_variables=%s",
            {k: v for k, v in vars_by_entity.items()},
            list(self._output_variables),
        )

        return vars_by_entity

    def _extract_results_by_entity(
        self,
        simulation: Any,
        period: int,
        vars_by_entity: dict[str, list[str]],
    ) -> dict[str, pa.Table]:
        """Extract output variables grouped by entity into per-entity tables.

        For each entity group, calls ``simulation.calculate()`` for its
        variables and builds a ``pa.Table`` per entity. Arrays within an
        entity group share the same length (entity instance count).

        Args:
            simulation: The completed OpenFisca simulation.
            period: Computation period (integer year).
            vars_by_entity: Output variables grouped by entity plural name
                (from ``_resolve_variable_entities``).

        Returns:
            Dict mapping entity plural name to a PyArrow Table containing
            that entity's output variables.
        """
        period_str = str(period)
        entity_tables: dict[str, pa.Table] = {}

        for entity_plural, var_names in vars_by_entity.items():
            arrays: dict[str, pa.Array] = {}
            for var_name in var_names:
                numpy_array = simulation.calculate(var_name, period_str)
                arrays[var_name] = pa.array(numpy_array)
            entity_tables[entity_plural] = pa.table(arrays)

        return entity_tables

    def _select_primary_output(
        self,
        entity_tables: dict[str, pa.Table],
        tbs: Any,
    ) -> pa.Table:
        """Select the primary output_fields table for backward compatibility.

        When all variables belong to one entity, returns that entity's table.
        When variables span multiple entities, returns the person-entity table
        (or the first entity's table if no person entity is present).

        Args:
            entity_tables: Per-entity output tables.
            tbs: The loaded TaxBenefitSystem.

        Returns:
            A single PyArrow Table to use as ``output_fields``.
        """
        if len(entity_tables) == 1:
            return next(iter(entity_tables.values()))

        # Find the person entity plural name
        for entity in tbs.entities:
            if getattr(entity, "is_person", False):
                person_plural = entity.plural
                if person_plural in entity_tables:
                    return entity_tables[person_plural]

        # Fallback: return the first entity's table
        return next(iter(entity_tables.values()))


]]></file>
<file id="e38c6079" path="tests/computation/test_openfisca_api_adapter.py" label="SOURCE CODE"><![CDATA[

"""Tests for OpenFiscaApiAdapter (Story 1.6: Direct OpenFisca API mode).

All OpenFisca internals are mocked since openfisca-core is an optional
dependency and may not be installed in CI.

Story 9.2: Added tests for multi-entity output array handling — entity-aware
result extraction, per-entity tables, and backward compatibility.
"""

from __future__ import annotations

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pyarrow as pa
import pytest

np = pytest.importorskip("numpy")

from reformlab.computation.adapter import ComputationAdapter
from reformlab.computation.exceptions import ApiMappingError, CompatibilityError
from reformlab.computation.openfisca_api_adapter import OpenFiscaApiAdapter
from reformlab.computation.types import ComputationResult, PolicyConfig, PopulationData

# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------

# Install a fake openfisca_core.simulation_builder module so that
# `from openfisca_core.simulation_builder import SimulationBuilder`
# inside _build_simulation can be patched. We register it once in
# sys.modules so the import succeeds, then individual tests patch
# the SimulationBuilder attribute.

_mock_sim_builder_module = MagicMock()
sys.modules.setdefault("openfisca_core", MagicMock())
sys.modules.setdefault("openfisca_core.simulation_builder", _mock_sim_builder_module)


def _make_mock_tbs(
    entity_keys: tuple[str, ...] = ("persons", "households"),
    variable_names: tuple[str, ...] = ("income_tax", "carbon_tax", "salary"),
    person_entity: str = "persons",
) -> MagicMock:
    """Create a mock TaxBenefitSystem with configurable entities and variables."""
    tbs = MagicMock()

    entities = []
    entities_by_key: dict[str, SimpleNamespace] = {}
    for key in entity_keys:
        entity = SimpleNamespace(key=key, plural=key, is_person=(key == person_entity))
        entities.append(entity)
        entities_by_key[key] = entity
    tbs.entities = entities

    # Variables get a default entity (the person entity) for backward compatibility
    # with existing tests that don't need entity-aware behavior.
    default_entity = entities_by_key.get(person_entity, entities[0])
    variables: dict[str, Any] = {}
    for name in variable_names:
        var_mock = MagicMock()
        var_mock.entity = default_entity
        variables[name] = var_mock
    tbs.variables = variables

    return tbs


def _make_mock_tbs_with_entities(
    entity_keys: tuple[str, ...] = ("individu", "foyer_fiscal", "menage"),
    entity_plurals: dict[str, str] | None = None,
    variable_entities: dict[str, str] | None = None,
    person_entity: str = "individu",
) -> MagicMock:
    """Create a mock TBS where variables know their entity.

    Story 9.2: Extended mock for entity-aware extraction tests.

    Args:
        entity_keys: Entity singular keys.
        entity_plurals: Mapping of singular key to plural form.
            Defaults to appending "s" (with special cases).
        variable_entities: Mapping of variable name to entity key.
        person_entity: Which entity key is the person entity.

    Returns:
        Mock TBS with entity-aware variables.
    """
    tbs = MagicMock()

    # Default plurals for French entities
    default_plurals = {
        "individu": "individus",
        "famille": "familles",
        "foyer_fiscal": "foyers_fiscaux",
        "menage": "menages",
    }
    if entity_plurals is None:
        entity_plurals = {}

    entities_by_key: dict[str, SimpleNamespace] = {}
    entities = []
    for key in entity_keys:
        plural = entity_plurals.get(key) or default_plurals.get(key) or key + "s"
        entity = SimpleNamespace(
            key=key,
            plural=plural,
            is_person=(key == person_entity),
        )
        entities.append(entity)
        entities_by_key[key] = entity
    tbs.entities = entities

    # Build variables with entity references
    if variable_entities is None:
        variable_entities = {}
    variables: dict[str, Any] = {}
    for var_name, entity_key in variable_entities.items():
        var_mock = MagicMock()
        var_mock.entity = entities_by_key[entity_key]
        variables[var_name] = var_mock
    tbs.variables = variables

    return tbs


def _make_mock_simulation(
    results: dict[str, np.ndarray],
) -> MagicMock:
    """Create a mock Simulation that returns given arrays for calculate()."""
    sim = MagicMock()
    sim.calculate.side_effect = lambda var, period: results[var]
    return sim


def _patch_simulation_builder(mock_builder_instance: MagicMock):  # type: ignore[no-untyped-def]
    """Patch SimulationBuilder in the fake openfisca_core.simulation_builder module."""
    return patch.object(
        _mock_sim_builder_module,
        "SimulationBuilder",
        return_value=mock_builder_instance,
    )


@pytest.fixture()
def sample_population() -> PopulationData:
    return PopulationData(
        tables={
            "persons": pa.table(
                {
                    "person_id": pa.array([1, 2, 3]),
                    "salary": pa.array([30000.0, 45000.0, 60000.0]),
                }
            ),
        },
        metadata={"source": "test"},
    )


@pytest.fixture()
def sample_policy() -> PolicyConfig:
    return PolicyConfig(
        parameters={"salary": 35000.0},
        name="test-policy",
    )


@pytest.fixture()
def empty_policy() -> PolicyConfig:
    return PolicyConfig(parameters={}, name="no-params")


# ---------------------------------------------------------------------------
# AC-7: Protocol compliance
# ---------------------------------------------------------------------------


class TestProtocolCompliance:
    """AC-7: isinstance(OpenFiscaApiAdapter(...), ComputationAdapter) returns True."""

    def test_isinstance_check(self) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        assert isinstance(adapter, ComputationAdapter)

    def test_has_compute_method(self) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        assert callable(getattr(adapter, "compute", None))

    def test_has_version_method(self) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        assert callable(getattr(adapter, "version", None))


# ---------------------------------------------------------------------------
# AC-2: Version-pinned execution
# ---------------------------------------------------------------------------


class TestVersionChecking:
    """AC-2: Version validation reuses shared logic from openfisca_common."""

    def test_supported_version_passes(self) -> None:
        with patch(
            "reformlab.computation.openfisca_api_adapter._detect_openfisca_version",
            return_value="44.2.2",
        ):
            adapter = OpenFiscaApiAdapter(output_variables=("income_tax",))
            assert adapter.version() == "44.2.2"

    def test_unsupported_version_raises(self) -> None:
        with patch(
            "reformlab.computation.openfisca_api_adapter._detect_openfisca_version",
            return_value="30.0.0",
        ):
            with pytest.raises(CompatibilityError) as exc_info:
                OpenFiscaApiAdapter(output_variables=("income_tax",))
            assert "30.0.0" in str(exc_info.value)

    def test_skip_version_check(self) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        assert adapter.version() == "unknown"


# ---------------------------------------------------------------------------
# AC-8: Graceful degradation when OpenFisca not installed
# ---------------------------------------------------------------------------


class TestGracefulDegradation:
    """AC-8: Missing openfisca-core raises CompatibilityError, not ImportError."""

    def test_not_installed_raises_compatibility_error(self) -> None:
        with patch(
            "reformlab.computation.openfisca_api_adapter._detect_openfisca_version",
            return_value="not-installed",
        ):
            with pytest.raises(CompatibilityError) as exc_info:
                OpenFiscaApiAdapter(output_variables=("income_tax",))
            assert "not installed" in str(exc_info.value).lower()
            assert exc_info.value.actual == "not-installed"

    def test_not_installed_is_not_import_error(self) -> None:
        """Verify the error type is CompatibilityError, NOT ImportError."""
        with patch(
            "reformlab.computation.openfisca_api_adapter._detect_openfisca_version",
            return_value="not-installed",
        ):
            with pytest.raises(CompatibilityError):
                OpenFiscaApiAdapter(output_variables=("income_tax",))


# ---------------------------------------------------------------------------
# AC-3: TaxBenefitSystem configuration (lazy loading + caching)
# ---------------------------------------------------------------------------


class TestTaxBenefitSystemLoading:
    """AC-3: Country package is imported, TBS is instantiated and cached."""

    def test_missing_country_package_raises_compatibility_error(self) -> None:
        adapter = OpenFiscaApiAdapter(
            country_package="openfisca_nonexistent",
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        with patch(
            "importlib.import_module",
            side_effect=ImportError("No module named 'openfisca_nonexistent'"),
        ):
            with pytest.raises(CompatibilityError) as exc_info:
                adapter._get_tax_benefit_system()
            assert "openfisca_nonexistent" in str(exc_info.value)
            assert "not-installed" == exc_info.value.actual

    def test_tbs_is_cached_after_first_load(self) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs()
        mock_module = MagicMock()
        mock_module.CountryTaxBenefitSystem.return_value = mock_tbs

        with patch(
            "importlib.import_module",
            return_value=mock_module,
        ) as mock_import:
            tbs1 = adapter._get_tax_benefit_system()
            tbs2 = adapter._get_tax_benefit_system()

            assert tbs1 is tbs2
            mock_import.assert_called_once()


# ---------------------------------------------------------------------------
# AC-1: Live computation via OpenFisca Python API
# ---------------------------------------------------------------------------


class TestCompute:
    """AC-1: compute() invokes SimulationBuilder and Simulation.calculate()."""

    def test_compute_returns_computation_result(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 2025)

        assert isinstance(result, ComputationResult)
        assert isinstance(result.output_fields, pa.Table)
        assert result.period == 2025
        assert result.output_fields.num_rows == 3
        assert result.output_fields.column_names == ["income_tax"]

    def test_compute_with_policy_parameters(
        self, sample_population: PopulationData, sample_policy: PolicyConfig
    ) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3500.0, 3500.0, 3500.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, sample_policy, 2025)

        assert isinstance(result, ComputationResult)
        call_args = mock_builder_instance.build_from_entities.call_args
        entities_dict = call_args[0][1]
        for instance_data in entities_dict["persons"].values():
            assert "salary" in instance_data

    def test_compute_multiple_output_variables(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax", "carbon_tax"),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {
                "income_tax": np.array([3000.0, 6750.0, 12000.0]),
                "carbon_tax": np.array([134.0, 200.0, 267.0]),
            }
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 2025)

        assert result.output_fields.column_names == ["income_tax", "carbon_tax"]
        assert result.output_fields.num_rows == 3


# ---------------------------------------------------------------------------
# AC-4: Variable selection — unknown variables raise structured error
# ---------------------------------------------------------------------------


class TestOutputVariableValidation:
    """AC-4: Unknown variable names raise a clear error before computation."""

    def test_unknown_variable_raises_api_mapping_error(self) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax", "nonexistent_var"),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs(variable_names=("income_tax", "carbon_tax", "salary"))

        with pytest.raises(ApiMappingError) as exc_info:
            adapter._validate_output_variables(mock_tbs)

        assert "nonexistent_var" in str(exc_info.value)
        assert exc_info.value.invalid_names == ("nonexistent_var",)

    def test_valid_variables_pass_validation(self) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs(variable_names=("income_tax", "carbon_tax"))
        adapter._validate_output_variables(mock_tbs)

    def test_suggestions_for_close_matches(self) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("incme_tax",),  # typo
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs(variable_names=("income_tax", "carbon_tax", "salary"))

        with pytest.raises(ApiMappingError) as exc_info:
            adapter._validate_output_variables(mock_tbs)

        assert "incme_tax" in exc_info.value.invalid_names
        assert len(exc_info.value.suggestions) > 0


# ---------------------------------------------------------------------------
# AC-5: Period mapping
# ---------------------------------------------------------------------------


class TestPeriodFormatting:
    """AC-5: Integer period is correctly passed as OpenFisca period string."""

    def test_period_passed_as_string(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            adapter.compute(sample_population, empty_policy, 2025)

        mock_simulation.calculate.assert_called_once_with("income_tax", "2025")


# ---------------------------------------------------------------------------
# AC-6: ComputationResult compatibility
# ---------------------------------------------------------------------------


class TestComputationResultStructure:
    """AC-6: Result has correct metadata and structure."""

    def test_metadata_source_is_api(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 2025)

        assert result.metadata["source"] == "api"

    def test_adapter_version_in_result(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        with patch(
            "reformlab.computation.openfisca_api_adapter._detect_openfisca_version",
            return_value="44.2.2",
        ):
            adapter = OpenFiscaApiAdapter(output_variables=("income_tax",))

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 2025)

        assert result.adapter_version == "44.2.2"

    def test_output_fields_is_pyarrow_table(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 2025)

        assert isinstance(result.output_fields, pa.Table)

    def test_metadata_includes_required_fields(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 2025)

        assert "timing_seconds" in result.metadata
        assert "row_count" in result.metadata
        assert "source" in result.metadata
        assert "policy_name" in result.metadata
        assert "country_package" in result.metadata
        assert "output_variables" in result.metadata
        assert result.metadata["row_count"] == 3
        assert result.metadata["country_package"] == "openfisca_france"
        assert result.metadata["output_variables"] == ["income_tax"]

    def test_period_is_correct(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 2025)

        assert result.period == 2025


# ---------------------------------------------------------------------------
# AC-9: Coexistence with pre-computed mode
# ---------------------------------------------------------------------------


class TestCoexistence:
    """AC-9: Both adapters instantiate independently."""

    def test_both_adapters_instantiate(self, tmp_path: object) -> None:
        from reformlab.computation.openfisca_adapter import OpenFiscaAdapter

        pre_computed = OpenFiscaAdapter(data_dir=str(tmp_path), skip_version_check=True)
        api_adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        assert isinstance(pre_computed, ComputationAdapter)
        assert isinstance(api_adapter, ComputationAdapter)
        assert type(pre_computed) is not type(api_adapter)

    def test_adapters_do_not_share_state(self, tmp_path: object) -> None:
        from reformlab.computation.openfisca_adapter import OpenFiscaAdapter

        pre_computed = OpenFiscaAdapter(data_dir=str(tmp_path), skip_version_check=True)
        api_adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        # Both return "unknown" when skip_version_check=True
        assert pre_computed.version() == "unknown"
        assert api_adapter.version() == "unknown"
        # They are distinct objects with no shared mutable state
        assert pre_computed is not api_adapter


# ---------------------------------------------------------------------------
# Entity mapping errors
# ---------------------------------------------------------------------------


class TestEntityMapping:
    """Entity keys in PopulationData must match TBS entity names."""

    def test_unknown_entity_raises_api_mapping_error(
        self, sample_policy: PolicyConfig
    ) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs(entity_keys=("persons", "households"))
        adapter._tax_benefit_system = mock_tbs

        bad_population = PopulationData(
            tables={
                "unknown_entity": pa.table({"x": pa.array([1])}),
            },
        )

        mock_builder_instance = MagicMock()
        with _patch_simulation_builder(mock_builder_instance):
            with pytest.raises(ApiMappingError) as exc_info:
                adapter.compute(bad_population, sample_policy, 2025)

        assert "unknown_entity" in str(exc_info.value)
        assert exc_info.value.invalid_names == ("unknown_entity",)

    def test_unknown_policy_parameter_raises_api_mapping_error(self) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs(variable_names=("income_tax", "salary"))
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "persons": pa.table({"salary": pa.array([30000.0])}),
            },
        )
        bad_policy = PolicyConfig(
            parameters={"nonexistent_param": 100.0},
            name="bad-policy",
        )

        mock_builder_instance = MagicMock()
        with _patch_simulation_builder(mock_builder_instance):
            with pytest.raises(ApiMappingError) as exc_info:
                adapter.compute(population, bad_policy, 2025)

        assert "nonexistent_param" in str(exc_info.value)


# ===========================================================================
# Story 9.2: Multi-entity output array handling
# ===========================================================================


class TestResolveVariableEntities:
    """Story 9.2 AC-1, AC-2, AC-5: Variable-to-entity mapping from TBS."""

    def test_groups_variables_by_entity(self) -> None:
        """AC-1: Variables are correctly grouped by their entity."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "irpp", "revenu_disponible"),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={
                "salaire_net": "individu",
                "irpp": "foyer_fiscal",
                "revenu_disponible": "menage",
            },
        )
        adapter._tax_benefit_system = mock_tbs

        result = adapter._resolve_variable_entities(mock_tbs)

        assert "individus" in result
        assert "foyers_fiscaux" in result
        assert "menages" in result
        assert result["individus"] == ["salaire_net"]
        assert result["foyers_fiscaux"] == ["irpp"]
        assert result["menages"] == ["revenu_disponible"]

    def test_multiple_variables_same_entity(self) -> None:
        """AC-1: Multiple variables on the same entity are grouped together."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "age"),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={
                "salaire_net": "individu",
                "age": "individu",
            },
        )
        adapter._tax_benefit_system = mock_tbs

        result = adapter._resolve_variable_entities(mock_tbs)

        assert len(result) == 1
        assert "individus" in result
        assert result["individus"] == ["salaire_net", "age"]

    def test_variable_without_entity_raises_error(self) -> None:
        """AC-5: Variable with no .entity attribute raises ApiMappingError."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("broken_var",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={},
        )
        # Add a variable without entity attribute
        var_mock = MagicMock()
        var_mock.entity = None
        mock_tbs.variables["broken_var"] = var_mock

        with pytest.raises(ApiMappingError, match="Cannot determine entity"):
            adapter._resolve_variable_entities(mock_tbs)

    def test_variable_not_in_tbs_raises_error(self) -> None:
        """AC-5: Variable not in TBS raises ApiMappingError."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("nonexistent_var",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={},
        )
        # TBS has no variables at all

        with pytest.raises(ApiMappingError, match="Cannot resolve variable entity"):
            adapter._resolve_variable_entities(mock_tbs)


class TestExtractResultsByEntity:
    """Story 9.2 AC-1, AC-2, AC-3: Per-entity result extraction."""

    def test_single_entity_extraction(self) -> None:
        """AC-1: Single entity produces one table."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net",),
            skip_version_check=True,
        )
        mock_simulation = _make_mock_simulation(
            {"salaire_net": np.array([20000.0, 35000.0])}
        )
        vars_by_entity = {"individus": ["salaire_net"]}

        result = adapter._extract_results_by_entity(mock_simulation, 2024, vars_by_entity)

        assert "individus" in result
        assert result["individus"].num_rows == 2
        assert result["individus"].column_names == ["salaire_net"]

    def test_multi_entity_extraction(self) -> None:
        """AC-2, AC-3: Different entities produce separate tables with correct lengths."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "irpp", "revenu_disponible"),
            skip_version_check=True,
        )
        mock_simulation = _make_mock_simulation({
            "salaire_net": np.array([20000.0, 35000.0]),
            "irpp": np.array([-1500.0]),
            "revenu_disponible": np.array([40000.0]),
        })
        vars_by_entity = {
            "individus": ["salaire_net"],
            "foyers_fiscaux": ["irpp"],
            "menages": ["revenu_disponible"],
        }

        result = adapter._extract_results_by_entity(mock_simulation, 2024, vars_by_entity)

        assert len(result) == 3
        assert result["individus"].num_rows == 2
        assert result["foyers_fiscaux"].num_rows == 1
        assert result["menages"].num_rows == 1

    def test_multiple_variables_per_entity(self) -> None:
        """AC-3: Multiple variables on same entity are in the same table."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "age"),
            skip_version_check=True,
        )
        mock_simulation = _make_mock_simulation({
            "salaire_net": np.array([20000.0, 35000.0]),
            "age": np.array([30.0, 45.0]),
        })
        vars_by_entity = {"individus": ["salaire_net", "age"]}

        result = adapter._extract_results_by_entity(mock_simulation, 2024, vars_by_entity)

        assert result["individus"].num_rows == 2
        assert set(result["individus"].column_names) == {"salaire_net", "age"}


class TestSelectPrimaryOutput:
    """Story 9.2 AC-4: Primary output_fields selection for backward compatibility."""

    def test_single_entity_returns_that_table(self) -> None:
        """AC-4: With one entity, output_fields is that entity's table."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net",),
            skip_version_check=True,
        )
        person_table = pa.table({"salaire_net": pa.array([20000.0, 35000.0])})
        mock_tbs = _make_mock_tbs_with_entities()

        result = adapter._select_primary_output({"individus": person_table}, mock_tbs)

        assert result is person_table

    def test_multi_entity_returns_person_table(self) -> None:
        """AC-4: With multiple entities, output_fields is the person-entity table."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "irpp"),
            skip_version_check=True,
        )
        person_table = pa.table({"salaire_net": pa.array([20000.0, 35000.0])})
        foyer_table = pa.table({"irpp": pa.array([-1500.0])})
        mock_tbs = _make_mock_tbs_with_entities()

        result = adapter._select_primary_output(
            {"individus": person_table, "foyers_fiscaux": foyer_table},
            mock_tbs,
        )

        assert result is person_table

    def test_multi_entity_without_person_returns_first(self) -> None:
        """AC-4: Without person entity in results, returns first entity's table."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("irpp", "revenu_disponible"),
            skip_version_check=True,
        )
        foyer_table = pa.table({"irpp": pa.array([-1500.0])})
        menage_table = pa.table({"revenu_disponible": pa.array([40000.0])})
        mock_tbs = _make_mock_tbs_with_entities()

        result = adapter._select_primary_output(
            {"foyers_fiscaux": foyer_table, "menages": menage_table},
            mock_tbs,
        )

        assert result is foyer_table


class TestComputeMultiEntity:
    """Story 9.2 AC-1, AC-2, AC-3, AC-4: End-to-end multi-entity compute()."""

    def test_compute_single_entity_backward_compatible(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-4: Single-entity output produces empty entity_tables (backward compat)."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 2025)

        # Single entity: entity_tables should be empty for backward compatibility
        assert result.entity_tables == {}
        # Metadata must be consistent with entity_tables — both empty for single-entity
        # (regression guard for the bug where output_entities was non-empty while
        # entity_tables was {}, causing consumers to see contradictory state).
        assert result.metadata["output_entities"] == []
        assert result.metadata["entity_row_counts"] == {}
        # output_fields still works
        assert result.output_fields.num_rows == 3
        assert result.output_fields.column_names == ["income_tax"]

    def test_compute_multi_entity_populates_entity_tables(self) -> None:
        """AC-1, AC-3: Multi-entity output populates entity_tables."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "irpp", "revenu_disponible"),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={
                "salaire_net": "individu",
                "irpp": "foyer_fiscal",
                "revenu_disponible": "menage",
            },
        )
        mock_simulation = _make_mock_simulation({
            "salaire_net": np.array([20000.0, 35000.0]),
            "irpp": np.array([-1500.0]),
            "revenu_disponible": np.array([40000.0]),
        })
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0, 50000.0]),
                }),
            },
        )

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(
                population, PolicyConfig(parameters={}, name="test"), 2024
            )

        # Multi-entity: entity_tables populated
        assert len(result.entity_tables) == 3
        assert "individus" in result.entity_tables
        assert "foyers_fiscaux" in result.entity_tables
        assert "menages" in result.entity_tables

        # Correct array lengths per entity
        assert result.entity_tables["individus"].num_rows == 2
        assert result.entity_tables["foyers_fiscaux"].num_rows == 1
        assert result.entity_tables["menages"].num_rows == 1

        # output_fields is the person entity table
        assert result.output_fields.num_rows == 2
        assert "salaire_net" in result.output_fields.column_names

    def test_compute_multi_entity_metadata(self) -> None:
        """AC-1: Metadata includes output_entities and entity_row_counts."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "irpp"),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={
                "salaire_net": "individu",
                "irpp": "foyer_fiscal",
            },
        )
        mock_simulation = _make_mock_simulation({
            "salaire_net": np.array([20000.0, 35000.0]),
            "irpp": np.array([-1500.0]),
        })
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0, 50000.0]),
                }),
            },
        )

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(
                population, PolicyConfig(parameters={}, name="test"), 2024
            )

        assert "output_entities" in result.metadata
        assert sorted(result.metadata["output_entities"]) == [
            "foyers_fiscaux", "individus"
        ]
        assert "entity_row_counts" in result.metadata
        assert result.metadata["entity_row_counts"]["individus"] == 2
        assert result.metadata["entity_row_counts"]["foyers_fiscaux"] == 1

    def test_compute_entity_detection_error(self) -> None:
        """AC-5: Variable with no entity raises ApiMappingError during compute."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("broken_var",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs_with_entities(variable_entities={})
        # Add variable with no entity
        var_mock = MagicMock()
        var_mock.entity = None
        mock_tbs.variables["broken_var"] = var_mock
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({"x": pa.array([1.0])}),
            },
        )

        mock_builder_instance = MagicMock()
        mock_simulation = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            with pytest.raises(ApiMappingError, match="Cannot determine entity"):
                adapter.compute(
                    population, PolicyConfig(parameters={}, name="test"), 2024
                )


]]></file>
<file id="895c54dc" path="tests/computation/test_openfisca_integration.py" label="SOURCE CODE"><![CDATA[

from __future__ import annotations
from 

]]></file>
<file id="1d910d88" path="[Validator A]" label="VALIDATION OUTPUT"><![CDATA[

# 🎯 Story Context Validation Report

I'll perform a comprehensive adversarial validation of Story 9.3 to identify issues the original LLM may have missed. Let me work through the workflow systematically.I'll start with a systematic analysis of Story 9.3 against the source documents provided. Let me check the predecessor story and epics file for context.Now let me examine the current state of the source code to understand what's already implemented:Now let me create a comprehensive validation report by analyzing the story systematically:Now let me compile my detailed validation findings. I'll create a comprehensive report:Based on my exhaustive analysis of Story 9.3 and the related artifacts, here is my comprehensive validation report:

---

## 🎯 Story Context Validation Report

**Story:** 9-3-add-variable-periodicity-handling
**Story File:** _bmad-output/implementation-artifacts/9-3-add-variable-periodicity-handling.md
**Validated:** 2026-03-01
**Validation Methodology:** Adversarial peer review against Project Context, Architecture, predecessor Story 9.2, and source code

---

## Executive Summary

### Issues Overview

| Category | Found | Severity |
|----------|-------|----------|
| 🚨 **Critical Issues** | 6 | **BLOCKING** |
| ⚡ **Enhancement Gaps** | 5 | **IMPORTANT** |
| ✨ **Optimizations** | 4 | **NICE-TO-HAVE** |
| 🤖 **LLM Improvements** | 5 | **TOKEN-EFFICIENCY** |

**Overall Assessment:** **MAJOR REWORK REQUIRED** — The story has significant clarity gaps that could cause developer mistakes and implementation delays. Critical issues around period validation placement, method integration with Story 9.2, and metadata specification need addressing before development starts.

**Evidence Score:** **24.7 → MAJOR REWORK** (6 CRITICAL @ +3 pts = +18, 5 IMPORTANT @ +1 pt = +5, 4 OPTIMIZATIONS @ +0.3 pts = +1.2, 5 LLM OPTS @ +0.3 pts = +1.5, minus clean passes = -1.0)

---

## 🚨 Critical Issues (Must Fix)

These issues could cause implementation disasters, regressions, or developer confusion.

### **Critical-1: Period Validation Placement and Scope Ambiguous**

**Impact:** Developer may place validation in wrong location or implement incorrect range checks, causing acceptance test failures.

**Problem:**
- AC-3 states "Invalid period format rejection" but doesn't specify WHERE this validation occurs or WHAT constitutes "invalid"
- Task 5.1 buries the specification: "Add validation at the top of `compute()`: period must be a positive integer in range [1000, 9999]"
- The range [1000, 9999] appears arbitrary with no justification for why these bounds were chosen
- No guidance on whether validation should occur BEFORE or AFTER other checks (entity resolution, periodicity resolution)
- The "fail-fast pattern" mentioned in Task 4.1 suggests validation before simulation build, but this isn't explicit in AC-3

**Recommended Fix:**
- Update AC-3 to explicitly state: "Given an invalid period value (non-positive integer, zero, or outside the range 1000-9999), when passed to `compute()`, then a clear `ApiMappingError` is raised at the method's entry point (before any TBS operations)"
- Add a "Period Validation Rules" subsection in Dev Notes explaining:
  - Valid range: [1000, 9999] (4-digit years) with rationale (OpenFisca convention, supported year range)
  - Invalid examples: -1, 0, 999, 10000, null
  - Placement: First operation in `compute()` before TBS.load or variable validation
- Example error message format in task 5.2

---

### **Critical-2: `_calculate_variable()` Method Specification Incomplete**

**Impact:** Developer may miss implementation details, place method in wrong location, or implement incorrect dispatch logic.

**Problem:**
- Task 2.1 specifies the method signature but doesn't show it in context
- Task 2.2 gives dispatch logic but assumes `periodicity` parameter is available
- Task 3.2 says "Replace `simulation.calculate(...)` with `self._calculate_variable(...)`" but:
  - No clear signature shown
  - No guidance on what `_calculate_variable()` returns (numpy array?)
  - No guidance on error handling if periodicity is unmapped
  - Existing code at line 503 shows `simulation.calculate()` — developer needs clear find-and-replace instructions
- Current source code doesn't show where this method should be added relative to existing methods

**Recommended Fix:**
- Show complete method signature with docstring:
  ```python
  def _calculate_variable(
      self,
      simulation: Any,
      var_name: str,
      period_str: str,
      periodicity: str,
  ) -> numpy.ndarray:
      """Dispatch to correct calculation method based on variable periodicity."""
  ```
- Specify return type: `numpy.ndarray` (not pa.Array, not dict)
- Add guidance: "Place this method immediately after `_extract_results_by_entity()` for logical grouping"
- Specify error handling: "If `periodicity` is unmapped (not in dispatch table), raise `ApiMappingError` — this should not happen if `_resolve_variable_periodicities()` is called first"

---

### **Critical-3: Story 9.2 Integration Not Explicitly Documented**

**Impact:** Developer may not realize this story DEPENDS on Story 9.2 implementation, or may make changes incompatible with Story 9.2's `_extract_results_by_entity()` signature.

**Problem:**
- Story 9.3 assumes `_resolve_variable_entities()` exists (from 9.2)
- Story 9.3 refactors `_extract_results_by_entity()` which was introduced in 9.2
- Current `_extract_results_by_entity()` signature in source code shows NO `variable_periodicities` parameter
- Task 3.1 says "Add `variable_periodicities: dict[str, str]` parameter" but doesn't explain how this parameter is passed or computed
- Task 4.1 says "Call `_resolve_variable_periodicities(tbs)` after `_resolve_variable_entities()`" but doesn't show the integration with `compute()`
- The current `compute()` method implementation isn't shown — developer must infer where both resolve methods fit

**Recommended Fix:**
- Add explicit "Prerequisites" section: "This story builds on Story 9.2 completion. Requires: `_resolve_variable_entities()` method and `_extract_results_by_entity()` implementation"
- Show the call chain in `compute()` pseudocode:
  ```
  1. Validate output variables
  2. Resolve entities: vars_by_entity = _resolve_variable_entities(tbs)
  3. Resolve periodicities: var_periodicities = _resolve_variable_periodicities(tbs)  [NEW]
  4. Build simulation
  5. Extract results: _extract_results_by_entity(simulation, period, vars_by_entity, var_periodicities)  [MODIFIED]
  ```
- Clarify: "Pass both `variable_periodicities` dict to `_extract_results_by_entity()` — it uses this to dispatch to correct calculation method for each variable"

---

### **Critical-4: Fail-Fast Pattern and Method Call Order Not Clearly Specified**

**Impact:** Developer may build expensive simulation before detecting periodicity resolution errors, causing performance issues and confusing error messages.

**Problem:**
- Task 4.1 says "fail-fast pattern — resolve both before building simulation" but:
  - This implication isn't explicit
  - No guidance on why order matters (entity resolution vs periodicity resolution)
  - Current source code shows `_resolve_variable_entities()` is called AFTER `_validate_output_variables()` and BEFORE `_build_simulation()` — periodicity resolution order unclear
  - Task 1.3 and Task 1.4 mention error handling but don't connect to fail-fast pattern
- Why not resolve both in a single pass since they both iterate over `_output_variables` and query the same TBS?

**Recommended Fix:**
- Document explicit call order in Task 4.1:
  ```
  # Fail-fast pattern: resolve all metadata before expensive operations
  1. _validate_output_variables(tbs)
  2. _resolve_variable_entities(tbs)         # Story 9.2
  3. _resolve_variable_periodicities(tbs)    # Story 9.3
  4. _build_simulation(population, policy, period, tbs)  # Expensive!
  ```
- Explain rationale: "Both resolution methods validate inputs and raise errors. By completing them before `_build_simulation()`, we avoid expensive simulation construction when input is invalid. This pattern follows Story 9.2."
- Add note: "Both methods could be combined into single loop for optimization (future work) but are kept separate for clarity"

---

### **Critical-5: Metadata Field Names Partially Specified in AC vs Tasks**

**Impact:** Developer may implement incorrect metadata structure, causing downstream consumers to fail or require rework.

**Problem:**
- AC-5 states: "`'variable_periodicities'` mapping each output variable to its detected periodicity and the calculation method used"
  - This single field supposedly contains BOTH periodicity AND calculation method
  - But the value type isn't specified (string? dict? tuple?)
- Task 4.3 says: "Add `'variable_periodicities'` and `'calculation_methods'` to result metadata"
  - This shows TWO separate metadata keys, not one
  - The distinction between them is unclear
  - No format specified for either field

**Example ambiguity:**
```python
# Does AC-5 expect this structure?
metadata["variable_periodicities"] = "month + calculate_add"  # Single string?

# Or this?
metadata["variable_periodicities"] = {"salaire_net": "month"}
metadata["calculation_methods"] = {"salaire_net": "calculate_add"}

# Or this?
metadata["variable_periodicities"] = {
    "salaire_net": {"periodicity": "month", "method": "calculate_add"}
}
```

**Recommended Fix:**
- Clarify AC-5: "`'variable_periodicities'` is a `dict[str, str]` mapping each output variable name to its periodicity (`'month'`, `'year'`, etc.). Calculation method is inferred from periodicity via the dispatch table."
- Update Task 4.3: "Add `'variable_periodicities'` metadata as `dict[str, str]` (variable_name → periodicity_string). Remove the `'calculation_methods'` field — it's redundant."
- Show example in Task 4.3:
  ```python
  metadata["variable_periodicities"] = {
      "salaire_net": "month",
      "impot_revenu_restant_a_payer": "year",
      "date_naissance": "eternity",
  }
  ```

---

### **Critical-6: AC-6 (Eternity Variable Handling) Vague and Lacks Test Guidance**

**Impact:** Developer may implement `calculate_add()` for eternity variables, causing crashes, or may not understand why eternity is special.

**Problem:**
- AC-6: "Given an ETERNITY-period variable as an output variable, when `compute()` is called, then `simulation.calculate()` is used (NOT `calculate_add()`, which rejects eternity variables) and the value is returned correctly."
  - This explains what SHOULD happen but not WHY
  - No test guidance for verifying this behavior
  - No example variable (e.g., `date_naissance`, `sexe`)
  - No explanation of what "rejects eternity" means (raises error? returns None?)
- Dev Notes explain that `calculate_add()` raises: "eternal variables can't be summed over time" — but this is buried in line 149

**Recommended Fix:**
- Expand AC-6 with rationale: "Eternity variables (e.g., `date_naissance`, `sexe`) have no temporal dimension. They cannot be summed or aggregated. Use `calculate()` (which accepts any period) instead of `calculate_add()` (which explicitly rejects eternity)."
- Add to Task 7 (integration tests): "7.7 Test: variable with `definition_period='eternity'` (e.g., `sexe` if available) → verify `calculate()` is used and returns correct value"
- Add mock test case in Task 2.4: "Verify `_calculate_variable(..., periodicity='eternity')` calls `simulation.calculate()` not `calculate_add()`"

---

## ⚡ Enhancement Opportunities

These gaps don't block development but provide valuable guidance that prevents mistakes.

### **Enhancement-1: Fail-Fast Pattern Rationale Missing**

The story mentions "fail-fast pattern" 3 times but never explains why it matters:
- **Gap:** Task 4.1 assumes developer understands the cost of `SimulationBuilder.build_from_entities()` and why validation should precede it
- **Suggestion:** Add Dev Notes subsection explaining:
  - `_build_simulation()` is expensive (~100-500ms for typical populations)
  - Validating inputs first avoids wasting compute on invalid data
  - This pattern is consistent with Story 9.2's entity resolution

### **Enhancement-2: DateUnit/StrEnum Comparison Details**

The Dev Notes explain `StrEnum` behavior but don't highlight the implementation implication:
- **Gap:** Line 132 shows `if periodicity == "month":` but doesn't explain this works BECAUSE of StrEnum
- **Suggestion:** Add explicit note:
  ```python
  # ✓ String comparison works directly (StrEnum inherits from str)
  if periodicity == "month":
      use_calculate_add = True
  
  # ✓ Also valid (accessing the string value)
  if str(periodicity) == "month":
      use_calculate_add = True
  
  # ✗ DON'T do this (works but unnecessary)
  if periodicity.value == "month":
      ...
  ```

### **Enhancement-3: Logging Pattern Not Specified**

Task 2.3 says "Log calculation method used per variable at DEBUG level" but provides no example:
- **Gap:** Project context (project-context.md) specifies "structured key=value format" but no example shown
- **Suggestion:** Add to Task 2.3:
  ```python
  # Per-variable logging at DEBUG level:
  logger.debug(
      "calculate_dispatch var=%s periodicity=%s method=%s",
      var_name,
      periodicity,
      "calculate_add" if periodicity in ("month", "day", "week") else "calculate",
  )
  ```

### **Enhancement-4: Integration Test Expected Values Incomplete**

Task 7 reference data mentions `salaire_net` but gives only a range:
- **Gap:** Line 254 says "should be positive and in range [20000, 30000]" — too vague for a test assertion
- **Suggestion:** Provide more specific expected behavior:
  ```python
  # Test case: Single person, 30000 EUR base salary
  # Expected: salaire_net ≈ 23400 (78% of gross, typical French deductions)
  # Tolerance: ±500 EUR (floating point, social contribution changes)
  assert 22900 < result["salaire_net"][0] < 23900
  ```

### **Enhancement-5: Backward Compatibility Validation Specifics Missing**

Task 6 (Verify backward compatibility) lists 4 generic subtasks with no concrete assertions:
- **Gap:** No guidance on what assertions to add in unit tests
- **Suggestion:** Add concrete test expectations:
  ```
  6.1 For single-entity (all yearly variables):
      - entity_tables == {} (empty dict for backward compat)
      - metadata["output_entities"] == [] (empty list)
      - output_fields contains all variables
  
  6.2 Verify MockAdapter still works:
      - MockAdapter.compute() doesn't call periodicity resolution
      - MockAdapter results match pre-Story 9.3 format
  ```

---

## ✨ Optimizations

### **Optimization-1: Dev Notes "OpenFisca Periodicity System" is Verbose**

The section explaining `DateUnit` (lines 108-167) repeats the same concept 3 times:
- Lines 108-118: Shows DateUnit class definition
- Lines 120-126: Explains StrEnum behavior with examples
- Lines 128-135: Shows how to access periodicity with example
- **Token waste:** ~40 lines for ~20 lines of essential information

**Suggestion:** Consolidate:
```markdown
### OpenFisca Periodicity System

`DateUnit` is a `StrEnum` from `openfisca_core.periods.date_unit`. You can access and compare periodicities as strings:

```python
variable = tbs.variables["salaire_net"]
periodicity = variable.definition_period  # DateUnit.MONTH, which == "month"
if periodicity == "month":  # String comparison works directly
    use_calculate_add = True
```

All possible values: `"month"`, `"year"`, `"eternity"`, `"day"`, `"week"`, `"weekday"`.
```

### **Optimization-2: Dispatch Table Wording Inconsistent**

Line 167 says "Simplified rule: Use `calculate()` for `'year'` and `'eternity'`, `calculate_add()` for everything else."

But the dispatch table (lines 158-165) shows more specific details. Pick one approach:
- **Option A:** Keep detailed table, remove "Simplified rule" (current approach is fine)
- **Option B:** Show only simplified rule, move detailed table to implementation comments

### **Optimization-3: Files to Modify Table Lacks File Paths**

Lines 169-175 show file changes but don't include full paths:
- **Current:** `src/reformlab/computation/openfisca_api_adapter.py`
- **Helpful:** `src/reformlab/computation/openfisca_api_adapter.py` (lines 475-507 for `_extract_results_by_entity()`, add new methods after line 508)

### **Optimization-4: Line Number References Incomplete**

Dev Notes reference line numbers for some code but not all:
- Line 23 mentions "line 503 of `openfisca_api_adapter.py`" ✓ Good
- Line 314 mentions same line ✓ Good
- But Task 2.1 doesn't say where to add `_calculate_variable()` method
- **Suggestion:** Add location hints in each task section

---

## 🤖 LLM Optimization Improvements

Token efficiency and clarity improvements for better developer agent processing:

### **LLM-Opt-1: Tasks Section is Overly Verbose**

Tasks 1-8 use extensive subtasks that could be condensed:

**Current (line 48-52, Task 1):**
```
- [ ] Task 1: Add `_resolve_variable_periodicities()` method (AC: #1, #2, #6)
  - [ ] 1.1 Add method to `OpenFiscaApiAdapter` that queries `tbs.variables[var_name].definition_period`...
  - [ ] 1.2 Return `dict[str, str]` mapping variable name to periodicity string...
  - [ ] 1.3 Handle edge case where `definition_period` attribute is missing...
  - [ ] 1.4 Unit tests with mock TBS...
```

**Optimized (~3 lines instead of 8):**
```
- [ ] Task 1: Add `_resolve_variable_periodicities()` method
  - Queries `tbs.variables[var_name].definition_period` for each output variable
  - Returns `dict[str, str]` with variable→periodicity mapping
  - Raises `ApiMappingError` if variable entity not found; unit tests with mock TBS
```

**Token savings:** ~50 tokens per story

### **LLM-Opt-2: Repetitive Subtask Patterns**

Tasks 1-7 follow identical patterns:
- "Add method..." → "Return X..."  → "Handle error..." → "Add unit tests..."
- "Refactor method..." → "Add parameter..." → "Update calls..." → "Unit tests..."

**Suggestion:** Use templated language instead of full sentences:
```
1. ✓ Method signature: _resolve_variable_periodicities(tbs: Any) -> dict[str, str]
   ✓ Returns: Variable→periodicity mapping
   ✓ Errors: ApiMappingError if definition_period missing
   ✓ Tests: Mock TBS with variable entities
```

### **LLM-Opt-3: Dev Notes Section Could Separate Critical from Reference**

Current structure mixes critical understanding with reference material:
- **Critical:** Architecture Constraints, Dispatch Logic, Period Validation Rules
- **Reference:** DateUnit details, Method signatures, Mock patterns

**Suggestion:** Reorganize:
```
### Critical Understanding
- Fail-fast pattern explanation
- Period validation range and placement
- Entity + periodicity resolution order

### Reference Material
- OpenFisca API details
- Mock patterns for testing
- File locations and existing code
```

### **LLM-Opt-4: AC Text is Overly Wordy**

AC-1 (line 34) uses 41 words:
```
"Given variables with different periodicities (monthly, yearly), when `compute()` is called with a yearly period, then the adapter uses `calculate_add()` for monthly variables and `calculate()` for yearly/eternity variables — producing correct results without `ValueError`."
```

**More concise version (18 words):**
```
"Adapter dispatches to `calculate_add()` for monthly and `calculate()` for yearly/eternity variables without `ValueError`."
```

Move example to separate "Example Scenarios" section.

### **LLM-Opt-5: "What This Story Does NOT Cover" Placement**

Currently at end (lines 291-298), mixed with other content.

**Better location:** After Acceptance Criteria (before Tasks), as "Scope Boundaries" section.

Developers need to know WHAT NOT to do immediately, not after reading 300 lines.

---

## Hidden Dependencies & Risks

1. **Story 9.2 Prerequisite Not Called Out** — This story requires Story 9.2 completion. No explicit dependency statement in story header.

2. **test_openfisca_integration.py File Incomplete** — The integration test file reference in Task 7 and line 175 shows truncated content (ending with `from `). Need to verify file exists and is readable.

3. **OpenFisca-France Optional Dependency** — Integration tests require `openfisca-france` installed. Should explicitly state in Task 7: "Run `uv sync --extra openfisca` before running integration tests"

---

## Technical Alignment Assessment

**Status:** ✅ Generally Aligned with Architecture, with minor clarifications needed

- ✅ Adapter isolation maintained (only in `openfisca_api_adapter.py`)
- ✅ No protocol changes required
- ✅ Frozen dataclass pattern respected
- ✅ PyArrow as canonical data type maintained
- ⚠️ Period validation range [1000, 9999] needs justification (OpenFisca docs reference?)
- ⚠️ Method call order implications with Story 9.2 not fully explained

---

## INVEST Criteria Assessment

| Criterion | Status | Issues |
|-----------|--------|--------|
| **I**ndependent | ⚠️ CONCERN | Depends on Story 9.2 completion; dependency not explicit |
| **N**egotiable | ✅ OK | Leaves implementation flexibility |
| **V**aluable | ✅ OK | Clear business value (fixes crashes) |
| **E**stimable | ⚠️ CONCERN | 8 tasks with 30+ subtasks; hard to estimate accurately |
| **S**mall | ⚠️ CONCERN | Could split into "periodicity detection" + "calculation dispatch" |
| **T**estable | ✅ OK | Good acceptance criteria, though some lack specificity |

---

## Validation Summary

### What the Original Story Does Well

✅ **Comprehensive context** — Spike 8-1 findings, OpenFisca API details, integration examples all included
✅ **Good AC structure** — 6 acceptance criteria cover main scenarios
✅ **Reference material** — Dev Notes include mock patterns, file locations, source code references
✅ **Backward compatibility focus** — Explicitly addresses non-breaking changes
✅ **Architecture alignment** — Respects adapter isolation, frozen dataclasses, exceptions

### What Needs Improvement Before Dev Starts

🔴 **Period validation placement** — Must specify WHERE and WHEN validation occurs
🔴 **Method integration** — Must clarify how `_resolve_variable_periodicities()` wires into existing code
🔴 **Story 9.2 dependency** — Must explicitly state prerequisite
🔴 **Metadata structure** — Must clarify exactly what goes in `variable_periodicities` metadata
🔴 **Eternity handling** — Must explain WHY eternity is special and how to test it

---

## Recommendations for Next Steps

1. **Add explicit "Prerequisites" section** stating this story builds on Story 9.2
2. **Create "Period Validation Specification" subsection** in Dev Notes with:
   - Valid range: [1000, 9999] with RFC/OpenFisca reference
   - Placement: First operation in `compute()`
   - Example: error message format
3. **Expand AC-5 and AC-6** with metadata examples and test guidance
4. **Show `compute()` pseudocode** illustrating how all pieces fit together
5. **Add `_calculate_variable()` signature** in a code block with docstring
6. **Consolidate Dev Notes "Periodicity System"** from 3 explanations to 1 clear example

---

**Report Generated:** 2026-03-01
**Evidence Score:** 24.7 (MAJOR REWORK REQUIRED)
**Validation Complete**

Would you like me to:
1. **Generate specific text improvements** for the critical issues?
2. **Create a revised story file** incorporating these fixes?
3. **Focus deeper analysis** on any specific issue area?

]]></file>
<file id="557aedd2" path="[Validator B]" label="VALIDATION OUTPUT"><![CDATA[

# 🎯 Story Context Validation Report

**Story:** `9-3-add-variable-periodicity-handling`
**Story File:** `_bmad-output/implementation-artifacts/9-3-add-variable-periodicity-handling.md`
**Validated:** 2026-03-01
**Validator:** Quality Competition Engine

---

## Executive Summary

| Category | Found | Applied |
|----------|-------|---------|
| 🚨 Critical Issues | 2 | 0 (read-only validator) |
| ⚡ Enhancements | 4 | 0 |
| ✨ Optimizations | 3 | 0 |
| 🤖 LLM Optimizations | 2 | 0 |

**Overall Assessment:** The story is well-researched and the OpenFisca internals are documented with impressive depth. However, two concrete critical gaps will cause test failures during implementation: (1) the method signature change to `_extract_results_by_entity()` breaks 3 existing unit tests that call it directly, and (2) the required `_make_mock_tbs()` update is described only in prose Dev Notes rather than as an explicit subtask, leaving the existing `TestPeriodFormatting` test silently producing wrong dispatch. Neither gap would be caught by reading the story alone.

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🔴 CRITICAL | Existing `TestExtractResultsByEntity` unit tests will fail with TypeError when `_extract_results_by_entity()` gains a new required `variable_periodicities` parameter — 3 existing test methods call this private method without the new arg, and no task covers updating them | Tasks 3.1 / existing test file | +3 |
| 🔴 CRITICAL | `_make_mock_tbs()` must be updated with `definition_period = "year"` for all variables, but this is only a Dev Notes prose remark — no explicit subtask; consequence: `TestPeriodFormatting.test_period_passed_as_string` silently dispatches to `calculate_add` instead of `calculate`, breaking an existing passing test with a confusing assertion failure | Dev Notes / Backward Compat Strategy | +3 |
| 🟠 IMPORTANT | Story 9.2 integration test `test_married_couple_multi_entity_extraction` is already failing in a real OpenFisca environment (calls `_extract_results_by_entity()` with `salaire_net`, a monthly variable, using `simulation.calculate()` which raises `ValueError`). Story 9.3 fixes this implicitly but Task 6.2 ("Run existing integration tests") does not acknowledge it — the developer will be confused by a "pre-existing" test failure | `test_openfisca_integration.py` lines 685–750 | +1 |
| 🟠 IMPORTANT | Integration test verification strategy for `calculate_add` dispatch is not specified — real OpenFisca `Simulation` objects cannot have `assert_called_with()` asserted on them. Task 7.1 says "verify `calculate_add()` is used" without specifying HOW (hint: via `result.metadata["calculation_methods"]` + value range check) | Task 7.1 / Dev Notes | +1 |
| 🟡 MINOR | Exact wire format for `"variable_periodicities"` and `"calculation_methods"` metadata dict values not specified (dict[str, str] shapes implied but never shown) | AC-5 / Task 4.3 | +0.3 |
| 🟡 MINOR | `_calculate_variable()` return type annotation specified as `numpy.ndarray` in dev notes pseudocode, but `openfisca_api_adapter.py` currently has no numpy import; mypy --strict guidance absent | Dev Notes | +0.3 |
| 🟡 MINOR | Module-level docstring update for `openfisca_api_adapter.py` not mentioned (project rule: every module references its story) | Project Context rules | +0.3 |
| 🟢 CLEAN PASS | INVEST: Independent — story can be developed without waiting for any other work (9.2 is already done) | — | -0.5 |
| 🟢 CLEAN PASS | INVEST: Negotiable — story does not over-specify HOW vs WHAT at the protocol level | — | -0.5 |
| 🟢 CLEAN PASS | INVEST: Valuable — directly unblocks real French tax-benefit computations (`salaire_net`) from crashing | — | -0.5 |
| 🟢 CLEAN PASS | INVEST: Estimable — 5 SP estimate is reasonable; well-scoped single concern | — | -0.5 |
| 🟢 CLEAN PASS | INVEST: Small — purely internal to `OpenFiscaApiAdapter`; no protocol/type changes | — | -0.5 |
| 🟢 CLEAN PASS | INVEST: Testable — ACs are specific and verifiable | — | -0.5 |
| 🟢 CLEAN PASS | AC Coverage vs Epics — all 3 epics ACs are covered and meaningfully expanded (to 6) | epics.md Story 9.3 | -0.5 |

### Evidence Score: **5.4** → **MAJOR REWORK**

| Score | Verdict |
|-------|---------|
| **5.4** | **MAJOR REWORK** |

---

## 🎯 Ruthless Story Validation 9.3

### INVEST Criteria Assessment

| Criterion | Status | Severity | Details |
|-----------|--------|----------|---------|
| **I**ndependent | ✅ PASS | 0/10 | Story 9.2 is marked `done`; no blocking external work |
| **N**egotiable | ✅ PASS | 1/10 | Method names are prescriptive but appropriate for an internal refactor story |
| **V**aluable | ✅ PASS | 0/10 | Fixes a real crash (`ValueError`) in production use of French tax variables |
| **E**stimable | ✅ PASS | 2/10 | Slightly underestimated — existing test updates add ~0.5 SP not captured |
| **S**mall | ✅ PASS | 1/10 | Well-scoped; purely internal adapter change |
| **T**estable | ✅ PASS | 1/10 | ACs are concrete; AC-5 metadata format could be more specific |

### INVEST Violations

✅ No significant INVEST violations detected.

### Acceptance Criteria Issues

- **Missing specificity:** AC-5 states "result metadata includes `'variable_periodicities'` mapping each output variable to its detected periodicity and the calculation method used" — a single key cannot hold both the periodicity and the method. The story uses two keys elsewhere (`"variable_periodicities"` + `"calculation_methods"`). AC-5 is self-contradictory about whether this is one dict or two.
  - *Quote:* "it includes `'variable_periodicities'` mapping each output variable to its detected periodicity and the calculation method used"
  - *Recommendation:* Split into two explicit keys with example values: `"variable_periodicities": {"salaire_net": "month", "irpp": "year"}` and `"calculation_methods": {"salaire_net": "calculate_add", "irpp": "calculate"}`

### Hidden Risks and Dependencies

- **Hidden breakage:** The private method signature change to `_extract_results_by_entity()` is a breaking API change within the test file itself. Tests were written in Story 9.2 to call this method directly, and they will fail at import/call time, not at assertion time.
  - *Impact:* Developer may interpret these failures as their implementation being wrong, wasting debugging time
  - *Mitigation:* Add explicit subtask to update the three existing callers in `TestExtractResultsByEntity`

- **Hidden state in mock TBS:** `_make_mock_tbs()` returns variables as `MagicMock()` objects. `MagicMock().definition_period` is another MagicMock, not a string. The new dispatch comparison `periodicity in ("year", "eternity")` evaluates False for MagicMock (MagicMock != "year"). This causes `calculate_add` to be invoked for ALL variables in all `compute()` unit tests — an incorrect dispatch that only manifests as a broken assertion in `TestPeriodFormatting`.
  - *Impact:* `TestPeriodFormatting.test_period_passed_as_string` fails with `AssertionError: Expected call: calculate('income_tax', '2025')` — a confusing regression in a previously-passing test
  - *Mitigation:* Explicit subtask to add `var_mock.definition_period = "year"` in `_make_mock_tbs()`

- **Pre-existing integration test failure (Story 9.2 debt):** `TestMultiEntityOutputArrays.test_married_couple_multi_entity_extraction` in `test_openfisca_integration.py` currently fails with `ValueError: Period mismatch` when run against real OpenFisca-France. Story 9.3's fix to `_extract_results_by_entity()` will also fix this test. The developer needs to know this test is already red (not broken by Story 9.3).
  - *Impact:* Developer may think Story 9.3 introduced a regression it actually fixed
  - *Mitigation:* Add note in Task 6.2 ("Run existing integration tests")

### Estimation Reality-Check

**Assessment:** Slightly underestimated (5 SP is correct for the core work; the untracked test update work adds ~0.5–1 SP)

The periodicity detection and dispatch logic is genuinely simple (two methods + a parameter thread-through). The story's SP estimate is reasonable. However, the undocumented work of updating 3 existing `TestExtractResultsByEntity` tests and `_make_mock_tbs()` adds real time — especially since the failures are non-obvious. A careful developer familiar with the codebase would handle this in the same sprint.

### Technical Alignment

**Status:** ✅ Well-aligned

- Correctly reuses `ApiMappingError` subsystem exception (no bare `ValueError`)
- Correctly keeps changes purely internal to `OpenFiscaApiAdapter` (no protocol changes)
- Correctly places periodicity metadata in existing `metadata: dict[str, Any]` (no new `ComputationResult` fields)
- Correctly uses lazy imports for OpenFisca internals
- Fail-fast ordering (resolve entities → resolve periodicities → build simulation) matches Story 9.2 pattern

✅ No technical alignment mismatches with architecture.md.

---

## 🚨 Critical Issues (Must Fix)

### 1. `_extract_results_by_entity()` Signature Change Breaks 3 Existing Unit Tests

**Impact:** Developer adds the new required `variable_periodicities` parameter to `_extract_results_by_entity()`, then runs `pytest` and sees 3 previously-passing tests fail with `TypeError: _extract_results_by_entity() missing 1 required positional argument: 'variable_periodicities'`. Story gives no warning this will happen.

**Source:** `tests/computation/test_openfisca_api_adapter.py` — `TestExtractResultsByEntity` class (tests added in Story 9.2)

**Problem:**

Task 3.1 says to add `variable_periodicities: dict[str, str]` as a new parameter to `_extract_results_by_entity()`. The story's "Files to Modify" entry says "add periodicity unit tests, extend mock TBS with `definition_period`" — but does NOT say to update existing tests that call this method. The three existing callers in `TestExtractResultsByEntity` are:

```python
# These three calls will TypeError after Task 3.1:
result = adapter._extract_results_by_entity(mock_simulation, 2024, vars_by_entity)
# ↑ Missing required 'variable_periodicities' argument
```

- `test_single_entity_extraction` (line ~520)
- `test_multi_entity_extraction` (line ~540)
- `test_multiple_variables_per_entity` (line ~560)

Plus, `test_married_couple_multi_entity_extraction` in `test_openfisca_integration.py` (line ~738):
```python
entity_tables = multi_entity_adapter._extract_results_by_entity(
    simulation, 2024, vars_by_entity
)  # ← Also needs variable_periodicities
```

**Recommended Fix:**

Add explicit subtask **1.5** (or **3.1b**):

> **Update all existing direct callers of `_extract_results_by_entity()` with the new `variable_periodicities` argument:**
> - `TestExtractResultsByEntity.test_single_entity_extraction`: pass `variable_periodicities={"salaire_net": "year"}` (or whatever the test var is)
> - `TestExtractResultsByEntity.test_multi_entity_extraction`: pass `variable_periodicities={"salaire_net": "year", "irpp": "year", "revenu_disponible": "year"}`
> - `TestExtractResultsByEntity.test_multiple_variables_per_entity`: pass `variable_periodicities={"salaire_net": "year", "age": "year"}`
> - `TestMultiEntityOutputArrays.test_married_couple_multi_entity_extraction` in integration tests: pass real periodicities resolved from TBS

---

### 2. `_make_mock_tbs()` Needs `definition_period = "year"` — Omitted from Tasks, Causing Silent Dispatch Regression

**Impact:** The dispatch logic correctly returns False for `MagicMock() in ("year", "eternity")`, causing `calculate_add()` to be called instead of `calculate()` for all variables in all existing `compute()` unit tests. The specific broken test is `TestPeriodFormatting.test_period_passed_as_string` which asserts:

```python
mock_simulation.calculate.assert_called_once_with("income_tax", "2025")
```

This assertion fails because `calculate_add` was called, not `calculate`. The failure message is misleading (`AssertionError: Expected call not found`) rather than a clear "mock is misconfigured" message.

**Source:** Dev Notes ("Backward Compatibility Strategy") — acknowledged in prose but absent from Tasks

**Problem:**

The story's backward compatibility strategy section says:
> "Story 9.3 must ensure that mocks also set `definition_period` (default to `'year'` for backward compatibility)."

This is written as a general obligation but **is not a Task or subtask**. The "Mock TBS Extension for Unit Tests" dev note shows code for the new `_make_mock_tbs_with_periodicities()` helper, but says nothing about updating `_make_mock_tbs()` (which is used by ALL pre-existing tests including `TestCompute`, `TestPeriodFormatting`, `TestComputeMultiEntity`, etc.).

The fix is one line in `_make_mock_tbs()`:
```python
for name in variable_names:
    var_mock = MagicMock()
    var_mock.entity = default_entity
    var_mock.definition_period = "year"  # ← ADD THIS LINE
    variables[name] = var_mock
```

Without it, every test that creates an adapter with `_make_mock_tbs()` and calls `compute()` will invoke `_resolve_variable_periodicities()` → get `MagicMock` → dispatch to `calculate_add` → break assertions.

**Recommended Fix:**

Add as an **explicit subtask** (e.g., Task 1.5 or a new Task 0 "Prepare existing test infrastructure"):

> **0.1 Add `var_mock.definition_period = "year"` to the variable-building loop inside `_make_mock_tbs()` in `test_openfisca_api_adapter.py`.** This is required because `_resolve_variable_periodicities()` now accesses `variable.definition_period` during every `compute()` call. Without this fix, all existing `compute()` unit tests dispatch to `calculate_add()` instead of `calculate()`, breaking `TestPeriodFormatting.test_period_passed_as_string`.

---

## ⚡ Enhancement Opportunities (Should Add)

### 1. Story 9.2 Integration Test Is Currently Failing — Acknowledge It in Task 6.2

**Benefit:** Developer understands the pre-existing test failure state, doesn't interpret red integration tests as a bug they introduced.
**Source:** `tests/computation/test_openfisca_integration.py`, `TestMultiEntityOutputArrays.test_married_couple_multi_entity_extraction` lines 685–750

**Current Gap:**

`test_married_couple_multi_entity_extraction` calls `_extract_results_by_entity()` with a real simulation that includes `salaire_net`. The current implementation uses `simulation.calculate("salaire_net", "2024")` which raises `ValueError: Period mismatch` in real OpenFisca-France (salaire_net is a monthly variable). This integration test is **currently failing** in any environment where openfisca-france is installed.

Story 9.3's fix to `_extract_results_by_entity()` will dispatch to `simulation.calculate_add("salaire_net", "2024")` and the test will pass. But Task 6.2 says "Run existing integration tests in `test_openfisca_integration.py` — ensure all pass unchanged" — this is wrong. The test was red before Story 9.3 and will be green after.

**Suggested Addition:**

Update Task 6.2 to:
> **6.2 Run integration tests in `test_openfisca_integration.py`. Note: `TestMultiEntityOutputArrays.test_married_couple_multi_entity_extraction` is currently FAILING (ValueError from `calculate("salaire_net", "2024")`) because Story 9.2 added this test before Story 9.3 fixed the dispatch. Story 9.3 is expected to make this test GREEN. Verify that all other integration tests continue to pass.**

---

### 2. Integration Test Verification Strategy for `calculate_add` Dispatch

**Benefit:** Developer knows HOW to write integration test assertions — avoids a wasted attempt to mock `calculate_add` on a real simulation object.
**Source:** Task 7.1 / Dev Notes

**Current Gap:**

Task 7.1 says "Test: `salaire_net` (MONTH) with yearly period → verify `calculate_add()` is used and returns correct yearly sum." A developer new to this codebase might try `simulation.calculate_add.assert_called_with(...)` on a real OpenFisca simulation object, which is impossible (no mock patching). The story doesn't say how to actually verify method dispatch in integration tests.

**Suggested Addition:**

Add to Dev Notes or Task 7.1:

> **Verifying dispatch in integration tests:** Real `Simulation` objects cannot be mocked/spied on with `assert_called_with`. Instead, verify dispatch via:
> 1. **Metadata:** `assert result.metadata["calculation_methods"]["salaire_net"] == "calculate_add"`
> 2. **Value correctness:** `salaire_net_val = result.entity_tables["individus"].column("salaire_net")[0].as_py(); assert 20000 < salaire_net_val < 30000` (yearly net salary for 30k gross base is in this range)
>
> Unit tests (with mock simulation) use `mock_simulation.calculate_add.assert_called_with("salaire_net", "2025")` for dispatch verification.

---

### 3. Exact Metadata Format for AC-5

**Benefit:** Developer knows the expected dict structure; removes ambiguity from AC-5 and Task 4.3.
**Source:** AC-5, Task 4.3

**Current Gap:**

AC-5 says "it includes `'variable_periodicities'` mapping each output variable to its detected periodicity **and the calculation method used**" — this conflates two things into one key. Task 4.3 says "Add `'variable_periodicities'` and `'calculation_methods'` to result metadata" — but gives no format.

**Suggested Addition:**

Specify in AC-5 and Task 4.3:

```python
# After compute() with output_variables=("salaire_net", "impot_revenu_restant_a_payer"):
result.metadata["variable_periodicities"] == {
    "salaire_net": "month",
    "impot_revenu_restant_a_payer": "year",
}
result.metadata["calculation_methods"] == {
    "salaire_net": "calculate_add",
    "impot_revenu_restant_a_payer": "calculate",
}
```

Also fix AC-5 wording: split into two keys rather than "periodicity **and** method" in one key.

---

### 4. Explicit `_make_mock_tbs_with_periodicities()` vs Extending `_make_mock_tbs_with_entities()`

**Benefit:** Avoids proliferating 3 nearly-identical mock TBS helpers; keeps test infrastructure navigable.
**Source:** Dev Notes — "Mock TBS Extension for Unit Tests"

**Current Gap:**

The story proposes a third mock TBS helper `_make_mock_tbs_with_periodicities()`. After Stories 9.2 and 9.3, tests would have:
- `_make_mock_tbs()` — base, all vars on person entity, no periodicity
- `_make_mock_tbs_with_entities()` — Story 9.2, entity-aware, no periodicity  
- `_make_mock_tbs_with_periodicities()` — Story 9.3, entity + periodicity

**Suggested Addition:**

Instead of creating a third helper, extend `_make_mock_tbs_with_entities()` to accept `variable_periodicities: dict[str, str] | None = None` with default `"year"` for all variables. This would let Story 9.3 tests call:

```python
mock_tbs = _make_mock_tbs_with_entities(
    variable_entities={"salaire_net": "individu", "irpp": "foyer_fiscal"},
    variable_periodicities={"salaire_net": "month", "irpp": "year"},
)
```

This consolidation should be mentioned in the Dev Notes as the recommended approach.

---

## ✨ Optimizations (Nice to Have)

### 1. Module Docstring Update

**Value:** Project rules require story/FR references in every module docstring; keeps the `openfisca_api_adapter.py` docstring current.

**Suggestion:**

Add to `openfisca_api_adapter.py` module docstring:

```python
"""Adapter that executes OpenFisca computations via the Python API.
...
Story 9.2: Added entity-aware result extraction to correctly handle
output variables belonging to different entity types (individu, menage,
famille, foyer_fiscal).
Story 9.3: Added variable periodicity handling — dispatches to
calculate_add() for monthly variables and calculate() for yearly/eternity
variables when a yearly period is requested.
"""
```

---

### 2. Pinned Reference Value for `salaire_net` in Integration Tests

**Value:** Consistency with `TestOpenFiscaFranceReferenceCases` pattern (which uses `ABSOLUTE_ERROR_MARGIN = 0.5`); makes the integration test a genuine regression guard rather than just a range check.

**Suggestion:**

Add a pinned expected value for `salaire_net` (30k EUR base salary, 2024):

```python
# Run once with openfisca-france 175.0.18 to get the reference value,
# then pin it (same pattern as TestOpenFiscaFranceReferenceCases):
ABSOLUTE_ERROR_MARGIN = 0.5
expected_salaire_net_yearly = 24000.0  # Approximate; pin after first run
assert abs(salaire_net_val - expected_salaire_net_yearly) <= ABSOLUTE_ERROR_MARGIN * 12
```

The story gives a range `[20000, 30000]` which is too wide to catch regressions.

---

### 3. Performance Note for `"day"/"week"/"weekday"` Variables

**Value:** Developers choosing output variables in future won't be surprised by extremely slow computations.

**Suggestion:**

Add a brief note to the dispatch table section:

> ⚠️ For `"day"` and `"weekday"` variables with a yearly period, `calculate_add()` sums ~260–365 sub-period computations. This may be significantly slower than yearly/monthly variables. Consider whether daily-period output variables are actually needed in yearly simulation runs.

---

## 🤖 LLM Optimization Improvements

### 1. Task 3 Subtask Description Hides Breaking Change

**Issue:** Missing specificity — "Unit tests: verify multi-entity extraction with mixed periodicities" implies ADDING tests, not UPDATING 3 existing ones that will TypeError.
**Token Impact:** Developer adds new tests, misses updating existing ones → runtime failures

**Current:**
```
- [ ] Task 3: Refactor `_extract_results_by_entity()` to use periodicity-aware calculation
  - [ ] 3.1 Add `variable_periodicities: dict[str, str]` parameter to `_extract_results_by_entity()`
  - [ ] 3.3 Unit tests: verify multi-entity extraction with mixed periodicities
```

**Optimized:**
```
- [ ] Task 3: Refactor `_extract_results_by_entity()` to use periodicity-aware calculation
  - [ ] 3.1 Add `variable_periodicities: dict[str, str]` parameter (⚠️ BREAKING: update
        the 3 existing callers in TestExtractResultsByEntity + integration test caller)
  - [ ] 3.2b Update existing tests: pass `variable_periodicities={"var": "year"}` to
        test_single_entity_extraction, test_multi_entity_extraction, test_multiple_variables_per_entity
  - [ ] 3.3 Add new tests: verify correct method dispatch for month/year/eternity vars
```

**Rationale:** "Update existing tests" and "add new tests" are different actions that a dev agent must not confuse.

---

### 2. "Files to Modify" Table Entry for Test File Is Incomplete

**Issue:** Describes only additions; hides the existing-test-update work.
**Token Impact:** Dev agent reads "add periodicity unit tests" and skips updating existing test callers

**Current:**
```
| `tests/computation/test_openfisca_api_adapter.py` | modify (add periodicity unit tests, extend mock TBS with `definition_period`) |
```

**Optimized:**
```
| `tests/computation/test_openfisca_api_adapter.py` | modify — 3 changes required: |
|  | (1) Update `_make_mock_tbs()` to add `var_mock.definition_period = "year"` |
|  | (2) Update existing `TestExtractResultsByEntity` tests (3 methods) with new `variable_periodicities` parameter |
|  | (3) Add new `TestResolveVariablePeriodicities` and `TestCalculateVariableDispatch` test classes |
```

**Rationale:** Separating the 3 distinct changes prevents the most common implementation mistake in this story.

---

## 📝 Changes Applied

No changes were applied to the story file. This report serves as documentation only (read-only validator mode).

---

## 🏆 Competition Results

### Quality Metrics

| Metric | Score |
|--------|-------|
| Requirements Coverage (vs epics.md ACs) | 95% |
| Architecture Alignment | 98% |
| Previous Story Integration (9.2 findings) | 85% |
| LLM Optimization Score | 78% |
| **Overall Quality Score** | **89%** |

### Disaster Prevention Assessment

- **Wheel Reinvention:** ✅ No risks — story correctly reuses `ApiMappingError`, existing mock infrastructure, and spike 8-1 findings
- **Wrong Libraries:** ✅ No risks — OpenFisca `DateUnit` API correctly documented from source
- **File Location Issues:** ✅ No risks — correct file paths throughout
- **Regression Risk:** 🔴 HIGH — 2 concrete regressions in existing passing tests if critical gaps are not addressed
- **Vague Implementations:** ✅ Minor risk only — dispatch logic fully documented
- **Completion Lie Risk:** ✅ Low — Task 8 quality gates (ruff, mypy, pytest) would surface the test failures

### Competition Outcome

🔍 **Validator identified 11 issues** (2 critical, 4 enhancements, 3 optimizations, 2 LLM optimizations) that should be addressed before handing off to a dev agent.

The original `create-story` workflow produced an exceptionally well-researched story. The OpenFisca API internals are documented with source-code-level accuracy, the backward compatibility strategy is correct, and the AC expansion from 3 → 6 is well-justified. The two critical gaps are subtle but concrete: they both stem from the same root cause — the story correctly describes what needs to change but does not translate that description into explicit task line items for the dev agent to execute.

---

**Report Generated:** 2026-03-01
**Validation Engine:** BMAD Method Quality Competition v1.0

]]></file>
</context>
<variables>
<var name="author">BMad</var>
<var name="communication_language">English</var>
<var name="date">2026-03-01</var>
<var name="description">Master synthesizes validator findings and applies changes to story file</var>
<var name="document_output_language">English</var>
<var name="epic_num">9</var>
<var name="implementation_artifacts">_bmad-output/implementation-artifacts</var>
<var name="installed_path">_bmad/bmm/workflows/4-implementation/validate-story-synthesis</var>
<var name="instructions">/Users/lucas/Workspace/bmad-assist/src/bmad_assist/workflows/validate-story-synthesis/instructions.xml</var>
<var name="name">validate-story-synthesis</var>
<var name="output_folder">_bmad-output</var>
<var name="planning_artifacts">_bmad-output/planning-artifacts</var>
<var name="project_context" file_id="b5c6fe32" load_strategy="EMBEDDED" token_approx="2024">embedded in prompt, file id: b5c6fe32</var>
<var name="project_knowledge">docs</var>
<var name="project_name">ReformLab</var>
<var name="session_id">706eb977-79bc-4f7b-9892-57944bbf735b</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_file" file_id="ccd1eda3">embedded in prompt, file id: ccd1eda3</var>
<var name="story_id">9.3</var>
<var name="story_key">9-3-add-variable-periodicity-handling</var>
<var name="story_num">3</var>
<var name="story_title">add-variable-periodicity-handling</var>
<var name="template">False</var>
<var name="timestamp">20260301_2039</var>
<var name="user_name">Lucas</var>
<var name="user_skill_level">expert</var>
<var name="validator_count">2</var>
</variables>
<instructions><workflow>
  <critical>Communicate all responses in English and generate all documents in English</critical>

  <critical>You are the MASTER SYNTHESIS agent. Your role is to evaluate validator findings
    and produce a definitive synthesis with applied fixes.</critical>
  <critical>You have WRITE PERMISSION to modify the story file being validated.</critical>
  <critical>All context (project_context.md, story file, anonymized validations) is EMBEDDED below - do NOT attempt to read files.</critical>
  <critical>Apply changes to story file directly using atomic write pattern (temp file + rename).</critical>

  <step n="1" goal="Analyze validator findings">
    <action>Read all anonymized validator outputs (Validator A, B, C, D, etc.)</action>
    <action>For each issue raised:
      - Cross-reference with story content and project_context.md
      - Determine if issue is valid or false positive
      - Note validator consensus (if 3+ validators agree, high confidence issue)
    </action>
    <action>Issues with low validator agreement (1-2 validators) require extra scrutiny</action>
  </step>

  <step n="1.5" goal="Review Deep Verify technical findings" conditional="[Deep Verify Findings] section present">
    <critical>Deep Verify provides automated technical analysis that complements validator reviews.
      DV findings focus on: patterns, boundary cases, assumptions, temporal issues, security, and worst-case scenarios.</critical>

    <action>Review each DV finding:
      - CRITICAL findings: Must be addressed - these indicate serious technical issues
      - ERROR findings: Should be addressed unless clearly false positive
      - WARNING findings: Consider addressing, document if dismissed
    </action>

    <action>Cross-reference DV findings with validator findings:
      - If validators AND DV flag same issue: High confidence, prioritize fix
      - If only DV flags issue: Verify technically valid, may be edge case validators missed
      - If only validators flag issue: Normal processing per step 1
    </action>

    <action>For each DV finding, determine:
      - Is this a genuine issue in the story specification?
      - Does the story need to address this edge case/scenario?
      - Is this already covered but DV missed it? (false positive)
    </action>

    <action>DV findings with patterns (CC-*, SEC-*, DB-*, DT-*, GEN-*) reference known antipatterns.
      Treat pattern-matched findings as higher confidence.</action>
  </step>

  <step n="2" goal="Verify and prioritize issues">
    <action>For verified issues, assign severity:
      - Critical: Blocks implementation or causes major problems
      - High: Significant gaps or ambiguities that need attention
      - Medium: Improvements that would help quality
      - Low: Nice-to-have suggestions
    </action>
    <action>Document false positives with clear reasoning for dismissal:
      - Why the validator was wrong
      - What evidence contradicts the finding
      - Reference specific story content or project_context.md
    </action>
  </step>

  <step n="3" goal="Apply changes to story file">
    <action>For each verified issue (starting with Critical, then High), apply fix directly to story file</action>
    <action>Changes should be natural improvements:
      - DO NOT add review metadata or synthesis comments to story
      - DO NOT reference the synthesis or validation process
      - Preserve story structure, formatting, and style
      - Make changes look like they were always there
    </action>
    <action>For each change, log in synthesis output:
      - File path modified
      - Section/line reference (e.g., "AC4", "Task 2.3")
      - Brief description of change
      - Before snippet (2-3 lines context)
      - After snippet (2-3 lines context)
    </action>
    <action>Use atomic write pattern for story modifications to prevent corruption</action>
  </step>

  <step n="4" goal="Generate synthesis report">
    <critical>Your synthesis report MUST be wrapped in HTML comment markers for extraction:</critical>
    <action>Produce structured output in this exact format (including the markers):</action>
    <output-format>
&lt;!-- VALIDATION_SYNTHESIS_START --&gt;
## Synthesis Summary
[Brief overview: X issues verified, Y false positives dismissed, Z changes applied to story file]

## Validations Quality
[For each validator: name, score, comments]
[Summary of validation quality - 1-10 scale]

## Issues Verified (by severity)

### Critical
[Issues that block implementation - list with evidence and fixes applied]
[Format: "- **Issue**: Description | **Source**: Validator(s) | **Fix**: What was changed"]

### High
[Significant gaps requiring attention]

### Medium
[Quality improvements]

### Low
[Nice-to-have suggestions - may be deferred]

## Issues Dismissed
[False positives with reasoning for each dismissal]
[Format: "- **Claimed Issue**: Description | **Raised by**: Validator(s) | **Dismissal Reason**: Why this is incorrect"]

## Deep Verify Integration
[If DV findings were present, document how they were handled]

### DV Findings Addressed
[List DV findings that resulted in story changes]
[Format: "- **{ID}** [{SEVERITY}]: {Title} | **Action**: {What was changed}"]

### DV Findings Dismissed
[List DV findings determined to be false positives or not applicable]
[Format: "- **{ID}** [{SEVERITY}]: {Title} | **Reason**: {Why dismissed}"]

### DV-Validator Overlap
[Note any findings flagged by both DV and validators - these are high confidence]
[If no DV findings: "Deep Verify did not produce findings for this story."]

## Changes Applied
[Complete list of modifications made to story file]
[Format for each change:
  **Location**: [File path] - [Section/line]
  **Change**: [Brief description]
  **Before**:
  ```
  [2-3 lines of original content]
  ```
  **After**:
  ```
  [2-3 lines of updated content]
  ```
]
&lt;!-- VALIDATION_SYNTHESIS_END --&gt;
    </output-format>

  </step>

  <step n="5" goal="Final verification">
    <action>Verify all Critical and High issues have been addressed</action>
    <action>Confirm story file changes are coherent and preserve structure</action>
    <action>Ensure synthesis report is complete with all sections populated</action>
  </step>
</workflow></instructions>
<output-template></output-template>
</compiled-workflow>