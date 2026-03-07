
# Story 14.3: Implement Vehicle Investment Decision Domain

Status: ready-for-dev

## Story

As a **platform developer**,
I want a vehicle investment decision domain that defines vehicle alternatives, applies attribute overrides during population expansion, and updates household state after choice draws,
so that multi-year simulations model realistic household vehicle purchase decisions with vintage tracking integration.

## Acceptance Criteria

1. **AC-1: DecisionDomain protocol compliance** — `VehicleInvestmentDomain` satisfies the `DecisionDomain` protocol (`isinstance(domain, DecisionDomain)` returns `True`). The implementation is stateless — all domain-specific logic is encoded in the alternatives and `apply_alternative` method. Uses `__slots__` for memory efficiency.
2. **AC-2: Vehicle choice set** — Given the vehicle decision domain, when configured with `default_vehicle_domain_config()`, then the choice set includes exactly 6 alternatives in this order:
   | ID | Name | vehicle_type | vehicle_age | vehicle_emissions_gkm |
   |---|---|---|---|---|
   | `keep_current` | Keep Current Vehicle | _(no override)_ | _(no override)_ | _(no override)_ |
   | `buy_petrol` | Buy Petrol Vehicle | `"petrol"` | `0` | `120.0` |
   | `buy_diesel` | Buy Diesel Vehicle | `"diesel"` | `0` | `110.0` |
   | `buy_hybrid` | Buy Hybrid Vehicle | `"hybrid"` | `0` | `50.0` |
   | `buy_ev` | Buy Electric Vehicle | `"ev"` | `0` | `0.0` |
   | `buy_no_vehicle` | Give Up Vehicle | `"none"` | `0` | `0.0` |

   `keep_current` has `attributes={}` (empty dict). All other alternatives have attributes overriding `vehicle_type` (str), `vehicle_age` (int), and `vehicle_emissions_gkm` (float). Alternative order is stable and deterministic.
3. **AC-3: apply_alternative** — Given a population entity table and an alternative, when `apply_alternative` is called, then it returns a **new** `pa.Table` with the alternative's attribute overrides applied. Columns present in the table are replaced (preserving the existing column's PyArrow type). Columns absent from the table are appended with type inferred from the Python value (`str` → `pa.utf8()`, `int` → `pa.int64()`, `float` → `pa.float64()`). The input table is **not modified**. If `alternative.attributes` is empty (e.g., `keep_current`), the table is returned unchanged.
4. **AC-4: Configurable domain** — `VehicleDomainConfig` is a frozen dataclass with fields: `alternatives: tuple[Alternative, ...]`, `cost_column: str` (default `"total_vehicle_cost"`), `entity_key: str` (default `"menage"`), `non_purchase_ids: frozenset[str]` (default `frozenset({"keep_current", "buy_no_vehicle"})`). `default_vehicle_domain_config()` factory returns a config with French market defaults (AC-2 values). `VehicleInvestmentDomain.__init__` takes a `VehicleDomainConfig`.
5. **AC-5: VehicleStateUpdateStep protocol** — `VehicleStateUpdateStep` implements the `OrchestratorStep` protocol. Default `name="vehicle_state_update"`, `depends_on=("logit_choice",)`. Constructor takes `domain: VehicleInvestmentDomain`, optional `population_key: str` (default `"population_data"`), optional `vintage_key: str` (default `"vintage_vehicle"`).
6. **AC-6: State update — new vehicle purchase** — Given a `ChoiceResult` where household _i_ chose a new vehicle alternative (ID not in `config.non_purchase_ids`), when `VehicleStateUpdateStep.execute()` runs, then:
   - The household's columns in the population entity table (`config.entity_key`) are updated with the chosen alternative's attribute overrides (`vehicle_type`, `vehicle_age`, `vehicle_emissions_gkm`).
   - For columns that the chosen alternative does NOT override, the household's existing value is preserved.
   - The update is applied per-household (row _i_ gets alternative _i_'s attributes, not a uniform value across all rows).
7. **AC-7: State update — keep current** — Given a `ChoiceResult` where household _i_ chose `keep_current`, when the state update runs, then all of household _i_'s columns are unchanged.
8. **AC-8: Vintage integration** — Given households that chose purchase alternatives (IDs not in `config.non_purchase_ids`), when the state update runs, then:
   - New `VintageCohort(age=0, count=N, attributes={"vehicle_type": <type>})` entries are created, one per distinct `vehicle_type` among switchers.
   - If `YearState.data[vintage_key]` contains an existing `VintageState`, new cohorts are appended to its cohorts tuple.
   - If no `VintageState` exists, a new `VintageState(asset_class="vehicle", cohorts=<new_cohorts>)` is created.
   - The updated `VintageState` is stored under `vintage_key` in the returned `YearState`.
   - `buy_no_vehicle` does NOT create a vintage entry (it's in `non_purchase_ids`).
9. **AC-9: State storage and immutability** — `VehicleStateUpdateStep.execute()` returns a new `YearState` via `dataclasses.replace()`. The original state is not modified. Updated population is stored under `population_key`. Vintage state under `vintage_key`. Metadata is extended under `DISCRETE_CHOICE_METADATA_KEY` with keys `vehicle_n_switchers` (int), `vehicle_n_keepers` (int), and `vehicle_per_alternative_counts` (dict[str, int]).
10. **AC-10: No interface changes** — No modifications to `DiscreteChoiceStep`, `LogitChoiceStep`, `domain.py`, `expansion.py`, `reshape.py`, `logit.py`, `types.py`, `errors.py`, `step.py`, or any orchestrator/computation files. The vehicle domain is purely additive.

## Tasks / Subtasks

- [ ] Task 1: Create `vehicle.py` with config types (AC: 4)
  - [ ] 1.1: Add `VehicleDomainConfig` frozen dataclass with fields: `alternatives`, `cost_column`, `entity_key`, `non_purchase_ids`
  - [ ] 1.2: Implement `default_vehicle_domain_config()` factory returning French market defaults (6 alternatives per AC-2)
  - [ ] 1.3: Add module docstring referencing Story 14-3 and FR47/FR50

- [ ] Task 2: Implement `VehicleInvestmentDomain` in `vehicle.py` (AC: 1, 2, 3)
  - [ ] 2.1: Class with `__slots__`, constructor taking `VehicleDomainConfig`
  - [ ] 2.2: `name` property returning `"vehicle"`
  - [ ] 2.3: `alternatives` property returning config alternatives as `tuple[Alternative, ...]`
  - [ ] 2.4: `cost_column` property from config
  - [ ] 2.5: `apply_alternative(table, alternative)` — iterate over `alternative.attributes`, replace existing columns (using existing type) or append new columns (with inferred type). Return new table. Empty attributes → return table unchanged.
  - [ ] 2.6: Private helper `_infer_pa_type(value)` for `str→utf8`, `int→int64`, `float→float64`, unsupported → `DiscreteChoiceError`

- [ ] Task 3: Implement `apply_choices_to_population` function in `vehicle.py` (AC: 6, 7)
  - [ ] 3.1: Function signature: `apply_choices_to_population(population: PopulationData, choice_result: ChoiceResult, alternatives: tuple[Alternative, ...], entity_key: str) -> PopulationData`
  - [ ] 3.2: Build alternative lookup dict `{id: Alternative}`
  - [ ] 3.3: Collect all attribute keys from all alternatives (sorted for determinism)
  - [ ] 3.4: For each attribute key, build per-row values: if chosen alternative overrides it, use override; else keep existing column value
  - [ ] 3.5: Type inference: if column exists, use existing type; else infer from first non-None value
  - [ ] 3.6: Replace or append columns on entity table
  - [ ] 3.7: Return new `PopulationData` with updated entity table
  - [ ] 3.8: Validate `len(choice_result.chosen) == table.num_rows`, raise `DiscreteChoiceError` on mismatch

- [ ] Task 4: Implement `VehicleStateUpdateStep` in `vehicle.py` (AC: 5, 8, 9)
  - [ ] 4.1: Class with `__slots__` implementing `OrchestratorStep` protocol
  - [ ] 4.2: Constructor: `domain: VehicleInvestmentDomain`, `population_key`, `vintage_key`, `name`, `depends_on`, `description`
  - [ ] 4.3: `execute(year, state)`:
    - Read `ChoiceResult` from `state.data[DISCRETE_CHOICE_RESULT_KEY]`; raise `DiscreteChoiceError` if missing
    - Read `PopulationData` from `state.data[population_key]`; raise `DiscreteChoiceError` if missing
    - Call `apply_choices_to_population()` to update population
    - Call `_create_vintage_entries()` for new vehicle purchases
    - Merge vintage entries with existing `VintageState` (or create new)
    - Extend metadata with switch counts
    - Return new `YearState` via `replace()`
  - [ ] 4.4: Private `_create_vintage_entries(choice_result, alternatives, non_purchase_ids) -> tuple[VintageCohort, ...]` — count switchers per vehicle_type, return cohort entries with `age=0`
  - [ ] 4.5: Structured key=value logging: `year`, `step_name`, `n_households`, `n_switchers`, `n_keepers`, `event=step_start/step_complete`

- [ ] Task 5: Update `__init__.py` with new exports (AC: 10)
  - [ ] 5.1: Export `VehicleInvestmentDomain`, `VehicleStateUpdateStep`, `VehicleDomainConfig`, `default_vehicle_domain_config`, `apply_choices_to_population`

- [ ] Task 6: Write tests (AC: all)
  - [ ] 6.1: Add vehicle domain fixtures to `conftest.py`: `vehicle_domain_config`, `vehicle_domain`, `vehicle_population` (with vehicle_type, vehicle_age, vehicle_emissions_gkm columns), `vehicle_mock_adapter` (compute function returning total_vehicle_cost)
  - [ ] 6.2: `test_vehicle.py` — `TestVehicleDomainConfig`: default config has 6 alternatives, correct IDs and order, non_purchase_ids, cost_column, immutability
  - [ ] 6.3: `test_vehicle.py` — `TestVehicleInvestmentDomain`: protocol compliance (`isinstance(domain, DecisionDomain)`, `is_protocol_step` not applicable here), name="vehicle", alternatives match config, cost_column, apply_alternative for each alternative type (keep_current no-op, buy_ev overrides 3 columns, buy_no_vehicle sets "none")
  - [ ] 6.4: `test_vehicle.py` — `TestApplyAlternative`: type preservation (existing column type used), new column type inference (str→utf8, int→int64, float→float64), empty attributes no-op, multiple attributes applied, column append for new attributes
  - [ ] 6.5: `test_vehicle.py` — `TestApplyChoicesToPopulation`: per-household attribute application, keep_current unchanged, mixed choices (some keep, some switch), empty population, length mismatch error
  - [ ] 6.6: `test_vehicle.py` — `TestVehicleStateUpdateStep`: protocol compliance, StepRegistry registration, full execute cycle (reads ChoiceResult + population, updates population + vintage), keep_current no-op, vintage cohort creation (counts per type), no vintage for non_purchase_ids, missing ChoiceResult error, missing population error, metadata extension
  - [ ] 6.7: `test_vehicle.py` — `TestVintageIntegration`: new cohorts appended to existing VintageState, new VintageState created when none exists, correct age=0 and counts, buy_no_vehicle excluded from vintage
  - [ ] 6.8: Integration test: `DiscreteChoiceStep` → `LogitChoiceStep` → `VehicleStateUpdateStep` full pipeline with MockAdapter

- [ ] Task 7: Lint, type-check, regression (AC: all)
  - [ ] 7.1: `uv run ruff check src/reformlab/discrete_choice/ tests/discrete_choice/`
  - [ ] 7.2: `uv run mypy src/reformlab/discrete_choice/`
  - [ ] 7.3: `uv run mypy src/`
  - [ ] 7.4: `uv run pytest tests/` — full regression suite passes

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**DecisionDomain protocol** (from `src/reformlab/discrete_choice/domain.py`):
```python
@runtime_checkable
class DecisionDomain(Protocol):
    @property
    def name(self) -> str: ...
    @property
    def alternatives(self) -> tuple[Alternative, ...]: ...
    @property
    def cost_column(self) -> str: ...
    def apply_alternative(self, table: pa.Table, alternative: Alternative) -> pa.Table: ...
```

The protocol is structural (duck-typed). Implementations do NOT inherit from `DecisionDomain`. The docstring explicitly states: "Stories 14.3/14.4 implement this protocol for specific domains."

**OrchestratorStep protocol** (from `src/reformlab/orchestrator/step.py`):
```python
@runtime_checkable
class OrchestratorStep(Protocol):
    @property
    def name(self) -> str: ...
    def execute(self, year: int, state: YearState) -> YearState: ...
```

Optional: `depends_on: tuple[str, ...]` and `description: str`.

**Data flow through the pipeline:**
```
DiscreteChoiceStep (14.1)
  reads: PopulationData from state["population_data"]
  uses:  VehicleInvestmentDomain.apply_alternative() for expansion
  uses:  VehicleInvestmentDomain.cost_column for reshape
  stores: CostMatrix → state["discrete_choice_cost_matrix"]
          ExpansionResult → state["discrete_choice_expansion"]
          metadata dict → state["discrete_choice_metadata"]
    ↓
LogitChoiceStep (14.2)
  reads: CostMatrix from state["discrete_choice_cost_matrix"]
  stores: ChoiceResult → state["discrete_choice_result"]
          extends metadata with beta_cost, choice_seed
    ↓
VehicleStateUpdateStep (14.3) ← THIS STORY
  reads: ChoiceResult from state["discrete_choice_result"]
         PopulationData from state["population_data"]
         VintageState from state["vintage_vehicle"] (optional)
  stores: Updated PopulationData → state["population_data"]
          Updated VintageState → state["vintage_vehicle"]
          extends metadata with switch counts
```

**Immutable state updates:** Always use `dataclasses.replace(state, data=new_data)`. Never mutate `state.data` in-place. Create a new dict: `new_data = dict(state.data)`, modify `new_data`, then `replace(state, data=new_data)`.

### Key Design Decisions

1. **VehicleDomainConfig is the single source of truth** for alternative definitions. All alternative attributes (vehicle_type, vehicle_age, emissions) are configured, not hardcoded. `default_vehicle_domain_config()` provides French market sensible defaults.

2. **apply_alternative follows the MockDomain pattern** from tests/conftest.py — iterates over `alternative.attributes`, replaces existing columns, appends missing ones. The vehicle domain adds **type inference** for new columns (MockDomain hardcodes `pa.float64()`).

3. **apply_choices_to_population is a public function** (not a method on the step) for testability. It handles per-household attribute application: each row gets the attributes of its chosen alternative.

4. **VehicleStateUpdateStep is a separate step** from DiscreteChoiceStep and LogitChoiceStep. It runs after logit draws and updates population + vintage state. This follows the design note's orchestrator loop (section 3.b.vi: "Update household attributes + create new vintage entries").

5. **non_purchase_ids distinguishes purchase from non-purchase alternatives** — alternatives in `non_purchase_ids` (default: `{"keep_current", "buy_no_vehicle"}`) do NOT create VintageCohort entries. This is configurable via `VehicleDomainConfig`.

6. **Vintage integration is additive** — new VintageCohort entries are appended to the existing `VintageState.cohorts` tuple. The existing `VintageTransitionStep` (which handles aging and retirement) is not modified. Multiple age=0 cohorts for the same vehicle_type in the same year are valid (they can be aggregated downstream).

7. **Entity key is configurable** — `config.entity_key` defaults to `"menage"` (French household entity). This avoids the fragile "first sorted entity key" heuristic flagged in the Story 14.1 review.

8. **French default emissions values** — Based on average new vehicle emissions for the French market:
   - Petrol: ~120 gCO2/km (average new petrol car, WLTP)
   - Diesel: ~110 gCO2/km (average new diesel car, WLTP)
   - Hybrid: ~50 gCO2/km (average new PHEV, WLTP)
   - EV: 0 gCO2/km (zero tailpipe)
   - None: 0 gCO2/km

### State Key Integration

Reads from state (set by Stories 14.1 and 14.2):
```python
DISCRETE_CHOICE_RESULT_KEY = "discrete_choice_result"       # ChoiceResult (from logit.py)
DISCRETE_CHOICE_METADATA_KEY = "discrete_choice_metadata"   # dict (from step.py)
```

Reads/writes to state (existing conventions):
```python
population_key = "population_data"   # PopulationData (configurable)
vintage_key = "vintage_vehicle"      # VintageState (configurable)
```

Extends `DISCRETE_CHOICE_METADATA_KEY` dict with:
```python
"vehicle_n_switchers": int           # Households that chose a new vehicle
"vehicle_n_keepers": int             # Households that kept current / gave up vehicle
"vehicle_per_alternative_counts": dict[str, int]  # Count per alternative ID
```

### apply_alternative — Type Inference Rules

```python
# When column EXISTS in table: use existing column's PyArrow type
existing_type = table.column(col_name).type
new_col = pa.array([value] * n, type=existing_type)

# When column is NEW (not in table): infer from Python type
if isinstance(value, str):    → pa.utf8()
elif isinstance(value, int):  → pa.int64()
elif isinstance(value, float): → pa.float64()
else: raise DiscreteChoiceError("Unsupported attribute type: ...")
```

### apply_choices_to_population — Core Algorithm

```python
def apply_choices_to_population(population, choice_result, alternatives, entity_key):
    table = population.tables[entity_key]
    n = table.num_rows
    alt_map = {alt.id: alt for alt in alternatives}
    chosen_list = choice_result.chosen.to_pylist()

    # Validate dimensions
    if len(chosen_list) != n:
        raise DiscreteChoiceError(...)

    # Collect all attribute keys across all alternatives
    all_attr_keys = sorted({k for alt in alternatives for k in alt.attributes})

    # Build per-column values based on each household's chosen alternative
    for attr_key in all_attr_keys:
        values = []
        for i in range(n):
            alt = alt_map[chosen_list[i]]
            if attr_key in alt.attributes:
                values.append(alt.attributes[attr_key])
            elif attr_key in table.column_names:
                values.append(table.column(attr_key)[i].as_py())
            else:
                values.append(None)
        # Infer type, build array, replace or append column
    ...
```

**CRITICAL:** This is per-household application. Row 0 gets the attributes of household 0's chosen alternative, row 1 gets household 1's, etc. This is fundamentally different from `apply_alternative` (which applies the same override to ALL rows).

### Edge Case Handling

| Scenario | Expected Behavior |
|----------|-------------------|
| Empty population (N=0) | State update is a no-op. Return state unchanged. No vintage entries. |
| All households keep current | Population unchanged. No vintage entries. `n_switchers=0`. |
| All households switch to EV | All rows get EV attributes. Single VintageCohort(age=0, count=N, attributes={"vehicle_type": "ev"}). |
| Mixed choices | Each row updated per its chosen alternative. Vintage entries created per vehicle_type. |
| buy_no_vehicle chosen | Population updated (vehicle_type="none", age=0, emissions=0). No vintage entry (in non_purchase_ids). |
| No VintageState in YearState | New VintageState created with just the new purchase cohorts. |
| Existing VintageState in YearState | New cohorts appended to existing cohorts tuple. |
| Population missing vehicle columns | Columns appended with inferred types (not an error). |
| ChoiceResult missing from state | DiscreteChoiceError raised with available keys listed. |
| PopulationData missing from state | DiscreteChoiceError raised with available keys listed. |
| ChoiceResult.chosen length != population rows | DiscreteChoiceError raised with length mismatch details. |
| Custom config with different alternatives | Domain works with any valid Alternative set (not hardcoded to 6). |

### VintageState Integration Pattern

```python
from reformlab.vintage.types import VintageCohort, VintageState

# Count new purchases by vehicle_type
switcher_counts: dict[str, int] = {}
for i, chosen_id in enumerate(chosen_list):
    if chosen_id not in config.non_purchase_ids:
        alt = alt_map[chosen_id]
        vtype = alt.attributes.get("vehicle_type", chosen_id)
        switcher_counts[vtype] = switcher_counts.get(vtype, 0) + 1

# Create new cohorts
new_cohorts = tuple(
    VintageCohort(age=0, count=count, attributes={"vehicle_type": vtype})
    for vtype, count in sorted(switcher_counts.items())  # sorted for determinism
)

# Merge with existing vintage state
existing = state.data.get(vintage_key)
if isinstance(existing, VintageState):
    merged = VintageState(
        asset_class="vehicle",
        cohorts=existing.cohorts + new_cohorts,
        metadata={**existing.metadata, "last_choice_year": year},
    )
else:
    merged = VintageState(
        asset_class="vehicle",
        cohorts=new_cohorts,
        metadata={"last_choice_year": year},
    )
```

### Testing Standards

- **Mirror structure:** Tests in `tests/discrete_choice/test_vehicle.py`
- **Class-based grouping:** `TestVehicleDomainConfig`, `TestVehicleInvestmentDomain`, `TestApplyAlternative`, `TestApplyChoicesToPopulation`, `TestVehicleStateUpdateStep`, `TestVintageIntegration`
- **Protocol compliance test:** `assert isinstance(domain, DecisionDomain)` and `assert is_protocol_step(step)`
- **StepRegistry test:** Register and retrieve VehicleStateUpdateStep
- **Golden value test:** Hand-build a 3-household population with known choices, verify exact column values after state update
- **Determinism test:** Same inputs → identical output population and vintage state
- **Integration test:** Full pipeline `DiscreteChoiceStep` → `LogitChoiceStep` → `VehicleStateUpdateStep` with MockAdapter
- **MockAdapter for tests:** Compute function that returns `total_vehicle_cost` based on vehicle attributes (e.g., `vehicle_emissions_gkm * 100 + vehicle_age * 50`). Must preserve tracking columns.
- **Fixtures in conftest.py:** Vehicle-specific population with `household_id`, `income`, `vehicle_type`, `vehicle_age`, `vehicle_emissions_gkm`, `fuel_cost` columns

### Project Structure Notes

```
src/reformlab/discrete_choice/
├── __init__.py       # Updated: add new exports
├── types.py          # UNCHANGED
├── errors.py         # UNCHANGED
├── domain.py         # UNCHANGED
├── expansion.py      # UNCHANGED
├── reshape.py        # UNCHANGED
├── step.py           # UNCHANGED (DiscreteChoiceStep from 14.1)
├── logit.py          # UNCHANGED (LogitChoiceStep from 14.2)
└── vehicle.py        # NEW — VehicleDomainConfig, VehicleInvestmentDomain,
                      #        VehicleStateUpdateStep, apply_choices_to_population,
                      #        default_vehicle_domain_config

tests/discrete_choice/
├── __init__.py       # UNCHANGED
├── conftest.py       # Updated: add vehicle domain fixtures
├── test_types.py     # UNCHANGED
├── test_expansion.py # UNCHANGED
├── test_reshape.py   # UNCHANGED
├── test_step.py      # UNCHANGED
├── test_logit.py     # UNCHANGED
└── test_vehicle.py   # NEW — Vehicle domain and state update tests
```

No new dependencies required — uses only existing `pyarrow`, `random` (stdlib), `dataclasses` (stdlib), and types from `reformlab.vintage.types`, `reformlab.discrete_choice.types`, `reformlab.computation.types`.

### Cross-Story Dependencies

| Story | Relationship | Notes |
|-------|-------------|-------|
| 14.1 | Depends on | `DiscreteChoiceStep` calls `VehicleInvestmentDomain.apply_alternative()` and `.cost_column` |
| 14.2 | Depends on | `LogitChoiceStep` produces `ChoiceResult` consumed by `VehicleStateUpdateStep` |
| 14.4 | Related | Heating domain follows same pattern. AC from 14.4: "domains execute sequentially (vehicle first, then heating) and the second domain sees the state updated by the first" |
| 14.5 | Uses | Eligibility filtering wraps expansion before logit; vehicle domain works with or without filtering |
| 14.6 | Blocks | Panel output records decision fields from `ChoiceResult` (chosen, probabilities, utilities) |
| 15.1 | Blocks | Calibration targets reference vehicle transition rates produced by this domain |

### Out of Scope Guardrails

- **DO NOT** implement the heating system decision domain (Story 14.4)
- **DO NOT** implement eligibility filtering (Story 14.5)
- **DO NOT** implement panel output extensions (Story 14.6)
- **DO NOT** implement calibration of taste parameters (Epic 15)
- **DO NOT** implement nested logit (conditional logit only)
- **DO NOT** implement multi-component utilities (multiple beta coefficients) — single `beta_cost` via `TasteParameters` only
- **DO NOT** modify `DiscreteChoiceStep`, `LogitChoiceStep`, `domain.py`, `expansion.py`, `reshape.py`, `logit.py`, `types.py`, `errors.py`, or `step.py`
- **DO NOT** modify any orchestrator files (`runner.py`, `step.py`, `types.py`)
- **DO NOT** modify `ComputationAdapter` protocol or `MockAdapter`
- **DO NOT** add numpy or any new dependency
- **DO NOT** implement actual OpenFisca cost computation logic — the adapter handles that; this story provides the domain definition and state update mechanics
- **DO NOT** prematurely extract `apply_choices_to_population` into a shared module — keep it in `vehicle.py`; Story 14.4 can extract if needed

### References

- [Source: `src/reformlab/discrete_choice/domain.py` — DecisionDomain protocol definition]
- [Source: `src/reformlab/discrete_choice/step.py` — DiscreteChoiceStep, state keys, execute pattern]
- [Source: `src/reformlab/discrete_choice/logit.py` — LogitChoiceStep, DISCRETE_CHOICE_RESULT_KEY, ChoiceResult storage]
- [Source: `src/reformlab/discrete_choice/types.py` — Alternative, ChoiceSet, CostMatrix, ChoiceResult, TasteParameters]
- [Source: `src/reformlab/discrete_choice/errors.py` — DiscreteChoiceError hierarchy]
- [Source: `src/reformlab/discrete_choice/__init__.py` — Public API exports]
- [Source: `src/reformlab/vintage/types.py` — VintageCohort (age, count, attributes), VintageState (asset_class, cohorts)]
- [Source: `src/reformlab/vintage/config.py` — _SUPPORTED_ASSET_CLASSES = ("vehicle",)]
- [Source: `src/reformlab/orchestrator/types.py` — YearState (data, seed, metadata)]
- [Source: `src/reformlab/orchestrator/step.py` — OrchestratorStep protocol, StepRegistry, is_protocol_step]
- [Source: `src/reformlab/computation/types.py` — PopulationData (tables, metadata), PolicyConfig]
- [Source: `src/reformlab/computation/mock_adapter.py` — MockAdapter (compute_fn, version_string, call_log)]
- [Source: `tests/discrete_choice/conftest.py` — MockDomain apply_alternative pattern, _discrete_choice_compute_fn]
- [Source: `_bmad-output/planning-artifacts/phase-2-design-note-discrete-choice-household-decisions.md` — Vehicle choice set, utility inputs, vintage integration, orchestrator loop]
- [Source: `docs/epics.md` — Epic 14 acceptance criteria, BKL-1403]
- [Source: `docs/project-context.md` — Project rules: PyArrow-first, frozen dataclasses, no numpy, adapter isolation]
- [Source: `src/reformlab/population/loaders/sdes.py` — SDES vehicle fleet schema: fuel_type, vehicle_age, critair_sticker]
- [Source: `src/reformlab/templates/vehicle_malus/compute.py` — vehicle_emissions_gkm column usage pattern]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Implementation Plan

### Completion Notes List

- Ultimate context engine analysis completed — comprehensive developer guide created
- All architecture patterns extracted from existing codebase (DecisionDomain, OrchestratorStep, VintageState, YearState)
- Design note vehicle domain specification fully integrated (choice set, utility inputs, vintage integration)
- Cross-story dependencies mapped (14.1/14.2 inputs, 14.4/14.5/14.6/15.1 outputs)
- Antipatterns from 14.1/14.2 addressed: explicit entity_key (not first-sorted), single representation for config, clear type inference rules, non_purchase_ids for vintage exclusion
- Population column analysis completed: vehicle_type (utf8), vehicle_age (int64), vehicle_emissions_gkm (float64) are the key columns
- Vintage integration pattern documented with VintageCohort/VintageState types from vintage subsystem
- Edge cases comprehensively defined (empty population, all-keep, all-switch, missing state, length mismatch)
- Out-of-scope guardrails explicitly defined (no heating, no eligibility, no calibration, no nested logit)

### File List

#### New Files
- `src/reformlab/discrete_choice/vehicle.py` — VehicleDomainConfig, VehicleInvestmentDomain, VehicleStateUpdateStep, apply_choices_to_population, default_vehicle_domain_config
- `tests/discrete_choice/test_vehicle.py` — Vehicle domain and state update tests

#### Modified Files
- `src/reformlab/discrete_choice/__init__.py` — Export new public API
- `tests/discrete_choice/conftest.py` — Add vehicle domain test fixtures
