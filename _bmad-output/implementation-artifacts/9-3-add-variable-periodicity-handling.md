# Story 9.3: Add Variable Periodicity Handling

Status: in-progress

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

3. **AC-3: Invalid period format rejection** — Given an invalid period value (non-positive integer, zero, or outside the 4-digit year range 1000–9999), when passed to the adapter's `compute()` as the very first check before any TBS operations, then a clear `ApiMappingError` is raised with summary `"Invalid period"`, the actual value, and the expected format (`"positive integer year in range [1000, 9999], e.g. 2024"`).

4. **AC-4: Backward compatibility** — Given output variables that are all yearly (the existing common case), when `compute()` is called, then behavior is identical to the pre-change implementation — no regression in results, metadata, or `entity_tables`.

5. **AC-5: Periodicity metadata** — Given a completed `compute()` call, when the result metadata is inspected, then it includes two entries: `"variable_periodicities"` (a `dict[str, str]` mapping each output variable to its detected periodicity string, e.g., `{"salaire_net": "month", "irpp": "year"}`) and `"calculation_methods"` (a `dict[str, str]` mapping each output variable to the method invoked, e.g., `{"salaire_net": "calculate_add", "irpp": "calculate"}`).

6. **AC-6: Eternity variable handling** — Given an ETERNITY-period variable (e.g., `date_naissance`, `sexe`) as an output variable, when `compute()` is called, then `simulation.calculate()` is used (NOT `calculate_add()`, which explicitly raises `"eternal variables can't be summed over time"`) and the value is returned correctly. Verified by unit test with mock simulation asserting `simulation.calculate` is called and `simulation.calculate_add` is NOT called when `periodicity == "eternity"`.

## Tasks / Subtasks

- [x] Task 1: Add `_resolve_variable_periodicities()` method (AC: #1, #2, #6)
  - [x] 1.1 Add method to `OpenFiscaApiAdapter` that queries `tbs.variables[var_name].definition_period` for each output variable
  - [x] 1.2 Return `dict[str, str]` mapping variable name to periodicity string (`"month"`, `"year"`, `"eternity"`, `"day"`, `"week"`, `"weekday"`)
  - [x] 1.3 Handle edge case where `definition_period` attribute is missing or has unexpected value — raise `ApiMappingError`
  - [x] 1.4 Unit tests with mock TBS: verify periodicity detection for month/year/eternity variables, error on missing attribute
  - [x] 1.5 Update `_make_mock_tbs()` in `tests/computation/test_openfisca_api_adapter.py` to add `var_mock.definition_period = "year"` in the variable-building loop — required because `_resolve_variable_periodicities()` now accesses `variable.definition_period` during every `compute()` call; without this fix, `MagicMock().definition_period` returns a MagicMock (not `"year"`), causing all existing `compute()` unit tests to dispatch to `calculate_add()` instead of `calculate()`, breaking `TestPeriodFormatting.test_period_passed_as_string`

- [x] Task 2: Add `_calculate_variable()` dispatch method (AC: #1, #2, #6)
  - [x] 2.1 Add private method `_calculate_variable(simulation, var_name, period_str, periodicity) -> numpy.ndarray`
  - [x] 2.2 Dispatch logic: `"month"`, `"day"`, `"week"`, `"weekday"` → `simulation.calculate_add(var, period_str)`; `"year"`, `"eternity"` → `simulation.calculate(var, period_str)`
  - [x] 2.3 Log calculation method used per variable at DEBUG level
  - [x] 2.4 Unit tests with mock simulation: verify correct method called based on periodicity

- [x] Task 3: Refactor `_extract_results_by_entity()` to use periodicity-aware calculation (AC: #1, #2, #4, #6)
  - [x] 3.1 Add `variable_periodicities: dict[str, str]` parameter to `_extract_results_by_entity()` — ⚠️ this is a breaking change to a private method used directly by 3 existing unit tests; update all 3 callers in `TestExtractResultsByEntity` (`test_single_entity_extraction`, `test_multi_entity_extraction`, `test_multiple_variables_per_entity`) to pass `variable_periodicities` with `"year"` for each test variable (e.g., `variable_periodicities={"salaire_net": "year", "irpp": "year"}`)
  - [x] 3.2 Replace `simulation.calculate(var_name, period_str)` with `self._calculate_variable(simulation, var_name, period_str, variable_periodicities[var_name])`
  - [x] 3.3 Unit tests: verify multi-entity extraction with mixed periodicities

- [x] Task 4: Wire periodicity resolution into `compute()` (AC: #1, #2, #4, #5)
  - [x] 4.1 Call `_resolve_variable_periodicities(tbs)` in `compute()` using this explicit call order (fail-fast — all validation before expensive simulation construction):
        1. `_validate_output_variables(tbs)`
        2. `vars_by_entity = _resolve_variable_entities(tbs)`          # Story 9.2
        3. `var_periodicities = _resolve_variable_periodicities(tbs)`  # Story 9.3 (NEW)
        4. `simulation = _build_simulation(population, policy, period, tbs)` # Expensive
        5. `entity_tables = _extract_results_by_entity(simulation, period, vars_by_entity, var_periodicities)` # Modified
  - [x] 4.2 Pass `variable_periodicities` to `_extract_results_by_entity()`
  - [x] 4.3 Add `"variable_periodicities"` and `"calculation_methods"` to result metadata as two separate `dict[str, str]` entries. Example for a mixed-periodicity compute: `"variable_periodicities": {"salaire_net": "month", "irpp": "year"}` and `"calculation_methods": {"salaire_net": "calculate_add", "irpp": "calculate"}`
  - [x] 4.4 Unit tests: verify metadata populated correctly in compute() result

- [x] Task 5: Add period validation (AC: #3)
  - [x] 5.1 Add validation as the FIRST operation in `compute()`, before `_get_tax_benefit_system()` or any TBS queries: period must be a positive integer in range [1000, 9999] (4-digit year; this is OpenFisca's practical supported temporal range — sub-period summation via `calculate_add()` is undefined outside plausible year values)
  - [x] 5.2 Raise `ApiMappingError` with summary "Invalid period", reason showing actual value, fix showing expected format
  - [x] 5.3 Unit tests: invalid periods (0, -1, 99, 99999) raise `ApiMappingError`; valid periods (2024, 2025) pass

- [ ] Task 6: Verify backward compatibility (AC: #4)
  - [ ] 6.1 Run existing unit tests in `test_openfisca_api_adapter.py` — ensure all pass unchanged
  - [ ] 6.2 Run existing integration tests in `test_openfisca_integration.py` — note: any Story 9.2 integration test using `salaire_net` (a monthly variable) that is already failing with `ValueError: Period mismatch` is a pre-existing failure this story fixes as a side-effect (Story 9.2 added the test before the dispatch fix existed); Story 9.3 is expected to make it green; verify all other pre-existing integration tests remain green
  - [ ] 6.3 Verify `MockAdapter` still produces valid `ComputationResult` (no new required fields)
  - [ ] 6.4 Verify `ComputationStep` in orchestrator still works (`result.output_fields.num_rows`)

- [x] Task 7: Integration tests with real OpenFisca-France (AC: #1, #2, #6)
  - [x] 7.1 Test: `salaire_net` (MONTH) with yearly period → verify `calculate_add()` is used and returns correct yearly sum. Since real `Simulation` objects cannot be mock-asserted, verify dispatch via metadata: `assert result.metadata["calculation_methods"]["salaire_net"] == "calculate_add"`, and verify value correctness: `assert 20000 < result.entity_tables["individus"].column("salaire_net")[0].as_py() < 30000`
  - [x] 7.2 Test: `impot_revenu_restant_a_payer` (YEAR) with yearly period → verify `calculate()` is used (unchanged)
  - [x] 7.3 Test: mixed periodicity output variables in single `compute()` call → verify correct method per variable
  - [x] 7.4 Test: `adapter.compute()` end-to-end with monthly output variable produces correct values
  - [x] 7.5 Test: verify `variable_periodicities` metadata in integration test result
  - [x] 7.6 Mark integration tests with `@pytest.mark.integration`

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
| `tests/computation/test_openfisca_api_adapter.py` | Three required changes: (1) update `_make_mock_tbs()` to add `var_mock.definition_period = "year"` in the variable-building loop; (2) update existing `TestExtractResultsByEntity` tests (3 methods) to pass new `variable_periodicities` argument; (3) add new test classes for periodicity detection, calculation dispatch, and period validation |
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
