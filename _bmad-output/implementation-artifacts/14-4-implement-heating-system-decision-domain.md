

# Story 14.4: Implement Heating System Decision Domain

Status: ready-for-dev

## Story

As a **platform developer**,
I want a heating system decision domain that defines heating alternatives, applies attribute overrides during population expansion, and updates household state after choice draws,
so that multi-year simulations model realistic household heating system investment decisions with vintage tracking integration, and both vehicle and heating domains can execute sequentially within a single orchestrator year.

## Acceptance Criteria

1. **AC-1: DecisionDomain protocol compliance** — `HeatingInvestmentDomain` satisfies the `DecisionDomain` protocol (`isinstance(domain, DecisionDomain)` returns `True`). The implementation is stateless — all domain-specific logic is encoded in the alternatives and `apply_alternative` method. Uses `__slots__` for memory efficiency.
2. **AC-2: Heating choice set** — Given the heating decision domain, when configured with `default_heating_domain_config()`, then the choice set includes exactly 5 alternatives in this order:
   | ID | Name | heating_type | heating_age | heating_emissions_kgco2_kwh |
   |---|---|---|---|---|
   | `keep_current` | Keep Current Heating | _(no override)_ | _(no override)_ | _(no override)_ |
   | `gas_boiler` | Install Gas Boiler | `"gas"` | `0` | `0.227` |
   | `heat_pump` | Install Heat Pump | `"heat_pump"` | `0` | `0.057` |
   | `electric` | Install Electric Heating | `"electric"` | `0` | `0.057` |
   | `wood_pellet` | Install Wood/Pellet Stove | `"wood"` | `0` | `0.030` |

   `keep_current` has `attributes={}` (empty dict). All other alternatives have attributes overriding `heating_type` (str), `heating_age` (int), and `heating_emissions_kgco2_kwh` (float). Alternative order is stable and deterministic.
3. **AC-3: apply_alternative** — Given a population entity table and an alternative, when `apply_alternative` is called, then it returns a **new** `pa.Table` with the alternative's attribute overrides applied. Columns present in the table are replaced (preserving the existing column's PyArrow type — PyArrow casts the value; if the cast is incompatible, wrap the resulting `ArrowInvalid` in `DiscreteChoiceError`). Columns absent from the table are appended with type inferred from the Python value (`str` → `pa.utf8()`, `int` → `pa.int64()`, `float` → `pa.float64()`; unsupported types raise `DiscreteChoiceError`). The input table is **not modified**. If `alternative.attributes` is empty (e.g., `keep_current`), the table is returned unchanged.
4. **AC-4: Configurable domain** — `HeatingDomainConfig` is a frozen dataclass with fields: `alternatives: tuple[Alternative, ...]`, `cost_column: str` (default `"total_heating_cost"`), `entity_key: str` (default `"menage"`), `non_purchase_ids: frozenset[str]` (default `frozenset({"keep_current"})`). `default_heating_domain_config()` factory returns a config with French market defaults (AC-2 values). `HeatingInvestmentDomain.__init__` takes a `HeatingDomainConfig`.
5. **AC-5: HeatingStateUpdateStep protocol** — `HeatingStateUpdateStep` implements the `OrchestratorStep` protocol. Default `name="heating_state_update"`, `depends_on=("logit_choice",)`. Constructor takes `domain: HeatingInvestmentDomain`, optional `population_key: str` (default `"population_data"`), optional `vintage_key: str` (default `"vintage_heating"`).
6. **AC-6: State update — heating switch** — Given a `ChoiceResult` where household _i_ chose a new heating alternative (ID not in `config.non_purchase_ids`), when `HeatingStateUpdateStep.execute()` runs, then:
   - The household's columns in the population entity table (`config.entity_key`) are updated with the chosen alternative's attribute overrides (`heating_type`, `heating_age`, `heating_emissions_kgco2_kwh`).
   - For columns that the chosen alternative does NOT override, the household's existing value is preserved.
   - The update is applied per-household (row _i_ gets alternative _i_'s attributes, not a uniform value across all rows). Positional alignment between `ChoiceResult.chosen[i]` and entity table row _i_ is guaranteed by the upstream pipeline (expansion preserves row order, logit produces one choice per original household). Length equality is validated; unknown alternative IDs in `chosen` raise `DiscreteChoiceError`.
7. **AC-7: State update — keep current** — Given a `ChoiceResult` where household _i_ chose `keep_current`, when the state update runs, then all of household _i_'s columns are unchanged.
8. **AC-8: Vintage integration** — Given households that chose non-keep alternatives (IDs not in `config.non_purchase_ids`), when the state update runs, then:
   - New `VintageCohort(age=0, count=N, attributes={"heating_type": <type>})` entries are created, one per distinct `heating_type` among switchers.
   - If `YearState.data[vintage_key]` contains an existing `VintageState`, new cohorts are appended to its cohorts tuple.
   - If no `VintageState` exists, a new `VintageState(asset_class="heating", cohorts=<new_cohorts>)` is created.
   - The updated `VintageState` is stored under `vintage_key` in the returned `YearState`.
9. **AC-9: State storage and immutability** — `HeatingStateUpdateStep.execute()` returns a new `YearState` via `dataclasses.replace()`. The original state is not modified. Updated population is stored under `population_key`. Vintage state under `vintage_key`. Metadata is extended under `DISCRETE_CHOICE_METADATA_KEY` with keys `heating_n_switchers` (int), `heating_n_keepers` (int), and `heating_per_alternative_counts` (dict[str, int]).
10. **AC-10: Extract shared utilities from vehicle.py** — `apply_choices_to_population` and `_infer_pa_type` are extracted from `vehicle.py` into a new `domain_utils.py` module within the `discrete_choice` package. `vehicle.py` is updated to import from `domain_utils.py`. `heating.py` imports from `domain_utils.py`. The public API (`__init__.py`) still exports `apply_choices_to_population`. All existing vehicle tests must pass without modification after extraction.
11. **AC-11: Sequential domain execution** — Given both vehicle and heating domains configured in the orchestrator pipeline, when a year executes, then the heating domain's `DiscreteChoiceStep` receives the population **after** `VehicleStateUpdateStep` has applied vehicle choice updates. An integration test demonstrates this sequential dependency.

## Tasks / Subtasks

- [ ] Task 1: Extract shared utilities to `domain_utils.py` (AC: 10)
  - [ ] 1.1: Create `domain_utils.py` with `infer_pa_type(value) -> pa.DataType` (renamed from `_infer_pa_type`, now module-level public within package)
  - [ ] 1.2: Move `apply_choices_to_population()` from `vehicle.py` to `domain_utils.py`
  - [ ] 1.3: Add `create_vintage_entries(choice_result, alternatives, non_purchase_ids, asset_type_key) -> tuple[VintageCohort, ...]` — parameterized version of vehicle's `_create_vintage_entries`, with `asset_type_key` specifying which attribute to group by (e.g., `"vehicle_type"` or `"heating_type"`)
  - [ ] 1.4: Update `vehicle.py` to import `infer_pa_type`, `apply_choices_to_population`, `create_vintage_entries` from `domain_utils`; remove local definitions; update `_create_vintage_entries` call to use `create_vintage_entries(..., asset_type_key="vehicle_type")`
  - [ ] 1.5: Update `vehicle.py`'s `VehicleInvestmentDomain.apply_alternative` to use `infer_pa_type` from `domain_utils` instead of local `_infer_pa_type`
  - [ ] 1.6: Run all existing vehicle tests — must pass without modification
  - [ ] 1.7: Add module docstring to `domain_utils.py` referencing Stories 14.3/14.4

- [ ] Task 2: Create `heating.py` with config types (AC: 4)
  - [ ] 2.1: Add `HeatingDomainConfig` frozen dataclass with fields: `alternatives`, `cost_column`, `entity_key`, `non_purchase_ids`
  - [ ] 2.2: Implement `default_heating_domain_config()` factory returning French market defaults (5 alternatives per AC-2)
  - [ ] 2.3: Add module docstring referencing Story 14-4 and FR47/FR50

- [ ] Task 3: Implement `HeatingInvestmentDomain` in `heating.py` (AC: 1, 2, 3)
  - [ ] 3.1: Class with `__slots__`, constructor taking `HeatingDomainConfig`
  - [ ] 3.2: `name` property returning `"heating"`
  - [ ] 3.3: `alternatives` property returning config alternatives as `tuple[Alternative, ...]`
  - [ ] 3.4: `cost_column` property from config
  - [ ] 3.5: `apply_alternative(table, alternative)` — iterate over `alternative.attributes`, replace existing columns (using existing type) or append new columns (with inferred type via `infer_pa_type` from `domain_utils`). Return new table. Empty attributes → return table unchanged.

- [ ] Task 4: Implement `HeatingStateUpdateStep` in `heating.py` (AC: 5, 6, 7, 8, 9)
  - [ ] 4.1: Class with `__slots__` implementing `OrchestratorStep` protocol
  - [ ] 4.2: Constructor: `domain: HeatingInvestmentDomain`, `population_key`, `vintage_key`, `name`, `depends_on`, `description`
  - [ ] 4.3: `execute(year, state)`:
    - Read `ChoiceResult` from `state.data[DISCRETE_CHOICE_RESULT_KEY]`; raise `DiscreteChoiceError` if missing
    - Read `PopulationData` from `state.data[population_key]`; raise `DiscreteChoiceError` if missing
    - Call `apply_choices_to_population()` from `domain_utils` to update population
    - Call `create_vintage_entries(..., asset_type_key="heating_type")` from `domain_utils` for new heating installations
    - Merge vintage entries with existing `VintageState` (or create new with `asset_class="heating"`)
    - Validate existing `VintageState.asset_class == "heating"` if present; raise `DiscreteChoiceError` on mismatch
    - Extend metadata with heating switch counts
    - Return new `YearState` via `replace()`
  - [ ] 4.4: Structured key=value logging: `year`, `step_name`, `n_households`, `n_switchers`, `n_keepers`, `event=step_start/step_complete`

- [ ] Task 5: Update `__init__.py` with new exports (AC: 10)
  - [ ] 5.1: Export `HeatingInvestmentDomain`, `HeatingStateUpdateStep`, `HeatingDomainConfig`, `default_heating_domain_config`
  - [ ] 5.2: Export `infer_pa_type` and `create_vintage_entries` from `domain_utils`
  - [ ] 5.3: Update `apply_choices_to_population` import to source from `domain_utils` (backward-compatible)

- [ ] Task 6: Write tests (AC: all)
  - [ ] 6.1: `test_domain_utils.py` — Tests for extracted shared functions: `infer_pa_type` (str→utf8, int→int64, float→float64, bool→error, unsupported→error), `apply_choices_to_population` (per-household application, keep_current no-op, length mismatch, unknown ID, entity key validation, empty population), `create_vintage_entries` (parameterized by asset_type_key, non_purchase_ids exclusion, sorted output)
  - [ ] 6.2: `test_heating.py` — `TestHeatingDomainConfig`: default config has 5 alternatives, correct IDs and order, non_purchase_ids={"keep_current"}, cost_column="total_heating_cost", entity_key="menage", immutability
  - [ ] 6.3: `test_heating.py` — `TestHeatingInvestmentDomain`: protocol compliance (`isinstance(domain, DecisionDomain)`), name="heating", alternatives match config, cost_column, `__slots__`
  - [ ] 6.4: `test_heating.py` — `TestApplyAlternative`: type preservation (existing column type used), new column type inference (str→utf8, int→int64, float→float64), empty attributes no-op, multiple attributes applied, column append for new attributes, incompatible cast error, unsupported type error
  - [ ] 6.5: `test_heating.py` — `TestHeatingStateUpdateStep`: protocol compliance, StepRegistry registration, full execute cycle (reads ChoiceResult + population, updates population + vintage), keep_current no-op, vintage cohort creation (counts per heating_type), missing ChoiceResult error, missing PopulationData error, entity_key validation, non-dict metadata error, vintage asset_class mismatch error, metadata extension, state immutability
  - [ ] 6.6: `test_heating.py` — `TestVintageIntegration`: new VintageState created when none exists with asset_class="heating", correct age=0 and counts, cohorts appended to existing VintageState
  - [ ] 6.7: `test_heating.py` — Integration test: `DiscreteChoiceStep` → `LogitChoiceStep` → `HeatingStateUpdateStep` full pipeline with MockAdapter
  - [ ] 6.8: `test_heating.py` — Sequential domain test (AC-11): Vehicle pipeline followed by heating pipeline; verify heating step receives vehicle-updated population

- [ ] Task 7: Lint, type-check, regression (AC: all)
  - [ ] 7.1: `uv run ruff check src/reformlab/discrete_choice/ tests/discrete_choice/`
  - [ ] 7.2: `uv run mypy src/reformlab/discrete_choice/`
  - [ ] 7.3: `uv run mypy src/`
  - [ ] 7.4: `uv run pytest tests/` — full regression, 0 failures

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

The protocol is structural (duck-typed). Implementations do NOT inherit from `DecisionDomain`. The domain docstring explicitly states: "Stories 14.3/14.4 implement this protocol for specific domains."

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
  uses:  HeatingInvestmentDomain.apply_alternative() for expansion
  uses:  HeatingInvestmentDomain.cost_column for reshape
  stores: CostMatrix → state["discrete_choice_cost_matrix"]
          ExpansionResult → state["discrete_choice_expansion"]
          metadata dict → state["discrete_choice_metadata"]
    ↓
LogitChoiceStep (14.2)
  reads: CostMatrix from state["discrete_choice_cost_matrix"]
  stores: ChoiceResult → state["discrete_choice_result"]
          extends metadata with beta_cost, choice_seed
    ↓
HeatingStateUpdateStep (14.4) ← THIS STORY
  reads: ChoiceResult from state["discrete_choice_result"]
         PopulationData from state["population_data"]
         VintageState from state["vintage_heating"] (optional)
  stores: Updated PopulationData → state["population_data"]
          Updated VintageState → state["vintage_heating"]
          extends metadata with heating switch counts
```

**Immutable state updates:** Always use `dataclasses.replace(state, data=new_data)`. Never mutate `state.data` in-place. Create a new dict: `new_data = dict(state.data)`, modify `new_data`, then `replace(state, data=new_data)`.

### Key Design Decisions

1. **HeatingDomainConfig is the single source of truth** for alternative definitions. All alternative attributes are configured, not hardcoded. `default_heating_domain_config()` provides French market defaults.

2. **No "give up heating" alternative** — Unlike the vehicle domain which has `buy_no_vehicle`, every dwelling needs heating. The only non-purchase alternative is `keep_current`. Therefore `non_purchase_ids = frozenset({"keep_current"})`.

3. **Shared utility extraction (AC-10)** — Story 14.3 explicitly authorized extraction: "Story 14.4 can extract if needed". The following functions move from `vehicle.py` to `domain_utils.py`:
   - `_infer_pa_type` → `infer_pa_type` (renamed, now module-level)
   - `apply_choices_to_population` (unchanged signature)
   - `_create_vintage_entries` → `create_vintage_entries` (renamed, parameterized with `asset_type_key`)

   `vehicle.py` imports from `domain_utils.py` after extraction. All existing vehicle tests must pass unchanged.

4. **HeatingStateUpdateStep is a separate step** from DiscreteChoiceStep and LogitChoiceStep. It runs after logit draws and updates population + vintage state. This follows the design note's orchestrator loop (section 3.b.vi: "Update household attributes + create new vintage entries").

5. **Entity key is configurable** — `config.entity_key` defaults to `"menage"` (French household entity), consistent with the vehicle domain.

6. **French default emission values** — Based on ADEME Base Carbone V23.6:
   - Gas boiler: 0.227 kgCO2e/kWh PCI (natural gas combustion)
   - Heat pump: 0.057 kgCO2e/kWh (French electricity grid; COP effect reduces consumption, not per-kWh emissions)
   - Electric resistance: 0.057 kgCO2e/kWh (same French grid factor)
   - Wood/pellet: 0.030 kgCO2e/kWh PCI (near carbon-neutral biogenic)

7. **Oil heating is NOT an alternative** — New oil boiler installations are banned in France since July 2022 (RE2020 regulation). Households with existing oil heating can only `keep_current` or switch to another system. This is correctly modeled by the choice set.

8. **Sequential domain execution (AC-11)** — When both vehicle and heating domains run in the same year, they share the same state keys (`DISCRETE_CHOICE_COST_MATRIX_KEY`, `DISCRETE_CHOICE_RESULT_KEY`). The second domain overwrites the first domain's intermediate results, which is correct since the first domain's results are consumed by its state update step before the second domain starts. Each step instance needs a unique `name` for the pipeline (e.g., `"discrete_choice_heating"`, `"logit_choice_heating"`, `"heating_state_update"`).

9. **Vintage integration is additive** — New `VintageCohort` entries are appended to the existing `VintageState.cohorts` tuple. The vehicle vintage (`vintage_vehicle`) and heating vintage (`vintage_heating`) are stored under **separate keys** — they do not interact.

10. **VintageState validates asset_class** — The `VintageState` type accepts any non-empty `asset_class` string (no MVP restriction like `VintageConfig`). So `VintageState(asset_class="heating", ...)` is valid without modifying `vintage/config.py`.

### State Key Integration

Reads from state (set by Stories 14.1 and 14.2):
```python
DISCRETE_CHOICE_RESULT_KEY = "discrete_choice_result"       # ChoiceResult (from logit.py)
DISCRETE_CHOICE_METADATA_KEY = "discrete_choice_metadata"   # dict (from step.py)
```

Reads/writes to state (existing conventions):
```python
population_key = "population_data"   # PopulationData (configurable)
vintage_key = "vintage_heating"      # VintageState (configurable)
```

Extends `DISCRETE_CHOICE_METADATA_KEY` dict with:
```python
"heating_n_switchers": int              # Households that chose a new heating system
"heating_n_keepers": int                # Households that kept current heating
"heating_per_alternative_counts": dict[str, int]  # Count per alternative ID
```

### apply_alternative — Type Inference Rules

Uses `infer_pa_type` from `domain_utils.py`:

```python
# When column EXISTS in table: use existing column's PyArrow type
existing_type = table.column(col_name).type
try:
    new_col = pa.array([value] * n, type=existing_type)
except (pa.ArrowInvalid, pa.ArrowTypeError) as exc:
    raise DiscreteChoiceError(f"Cannot cast {value!r} to {existing_type}: {exc}") from exc

# When column is NEW (not in table): infer from Python type
if isinstance(value, str):    → pa.utf8()
elif isinstance(value, int):  → pa.int64()
elif isinstance(value, float): → pa.float64()
else: raise DiscreteChoiceError("Unsupported attribute type: ...")
```

### apply_choices_to_population — Core Algorithm

Extracted to `domain_utils.py`, identical to vehicle.py implementation:

```python
def apply_choices_to_population(population, choice_result, alternatives, entity_key):
    table = population.tables[entity_key]
    n = table.num_rows
    alt_map = {alt.id: alt for alt in alternatives}
    chosen_list = choice_result.chosen.to_pylist()

    # Validate dimensions
    if len(chosen_list) != n:
        raise DiscreteChoiceError(...)

    # Validate all chosen IDs are known alternatives
    unknown_ids = set(chosen_list) - set(alt_map)
    if unknown_ids:
        raise DiscreteChoiceError(...)

    # Collect all attribute keys across all alternatives (sorted for determinism)
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

### create_vintage_entries — Parameterized Version

Extracted to `domain_utils.py` with `asset_type_key` parameter:

```python
def create_vintage_entries(
    choice_result: ChoiceResult,
    alternatives: tuple[Alternative, ...],
    non_purchase_ids: frozenset[str],
    asset_type_key: str,  # "vehicle_type" for vehicle, "heating_type" for heating
) -> tuple[VintageCohort, ...]:
    alt_map = {alt.id: alt for alt in alternatives}
    chosen_list: list[str] = choice_result.chosen.to_pylist()

    switcher_counts: dict[str, int] = {}
    for chosen_id in chosen_list:
        if chosen_id not in non_purchase_ids:
            alt = alt_map[chosen_id]
            asset_type = str(alt.attributes.get(asset_type_key, chosen_id))
            switcher_counts[asset_type] = switcher_counts.get(asset_type, 0) + 1

    return tuple(
        VintageCohort(age=0, count=count, attributes={asset_type_key: asset_type})
        for asset_type, count in sorted(switcher_counts.items())
    )
```

Vehicle domain calls: `create_vintage_entries(..., asset_type_key="vehicle_type")`
Heating domain calls: `create_vintage_entries(..., asset_type_key="heating_type")`

### Edge Case Handling

| Scenario | Expected Behavior |
|----------|-------------------|
| Empty population (N=0) | Population and vintage unchanged. Metadata still extended with `n_switchers=0`, `n_keepers=0`, empty `per_alternative_counts`. |
| All households keep current | Population unchanged. No vintage entries. `heating_n_switchers=0`. |
| All households switch to heat pump | All rows get heat_pump attributes. Single VintageCohort(age=0, count=N, attributes={"heating_type": "heat_pump"}). |
| Mixed choices | Each row updated per its chosen alternative. Vintage entries created per heating_type. |
| No VintageState in YearState | New VintageState created with asset_class="heating" and just the new cohorts. |
| Existing VintageState (heating) | New cohorts appended to existing cohorts tuple. |
| Existing VintageState with wrong asset_class | `DiscreteChoiceError` raised with asset_class mismatch details. |
| Population missing heating columns | Columns appended with inferred types (not an error). |
| ChoiceResult missing from state | `DiscreteChoiceError` raised with available keys listed. |
| PopulationData missing from state | `DiscreteChoiceError` raised with available keys listed. |
| Entity key not in population | `DiscreteChoiceError` raised with available keys listed. |
| ChoiceResult.chosen length != population rows | `DiscreteChoiceError` raised with length mismatch details. |
| Unknown alternative ID in ChoiceResult.chosen | `DiscreteChoiceError` raised listing the unknown IDs and valid set. |
| Type-incompatible attribute override | `DiscreteChoiceError` raised wrapping the PyArrow `ArrowInvalid` cast error. |
| Non-dict metadata in state | `DiscreteChoiceError` raised with type mismatch details. |
| Custom config with different alternatives | Domain works with any valid Alternative set (not hardcoded to 5). |
| Vehicle then heating sequential | Heating step receives population with vehicle updates already applied. |

### VintageState Integration Pattern

```python
from reformlab.discrete_choice.domain_utils import create_vintage_entries
from reformlab.vintage.types import VintageState

# Create new cohorts (parameterized by asset_type_key)
new_cohorts = create_vintage_entries(
    choice_result, config.alternatives, config.non_purchase_ids,
    asset_type_key="heating_type",
)

# Merge with existing vintage state
existing = state.data.get(vintage_key)
if isinstance(existing, VintageState):
    if existing.asset_class != "heating":
        raise DiscreteChoiceError(...)
    merged = VintageState(
        asset_class="heating",
        cohorts=existing.cohorts + new_cohorts,
        metadata={**existing.metadata, "last_choice_year": year},
    )
elif new_cohorts:
    merged = VintageState(
        asset_class="heating",
        cohorts=new_cohorts,
        metadata={"last_choice_year": year},
    )
else:
    merged = None
```

### Testing Standards

- **Mirror structure:** Tests in `tests/discrete_choice/test_heating.py` and `tests/discrete_choice/test_domain_utils.py`
- **Self-contained helpers:** Test classes use private `_make_population`/`_make_state` helpers (no conftest fixtures needed — follows test_vehicle.py pattern)
- **Class-based grouping:** `TestHeatingDomainConfig`, `TestHeatingInvestmentDomain`, `TestApplyAlternative`, `TestHeatingStateUpdateStep`, `TestVintageIntegration`, `TestSequentialDomainExecution`
- **Protocol compliance test:** `assert isinstance(domain, DecisionDomain)` and `assert is_protocol_step(step)`
- **StepRegistry test:** Register and retrieve HeatingStateUpdateStep
- **Golden value test:** Hand-build a 3-household population with known choices, verify exact column values after state update
- **Determinism test:** Same inputs → identical output population and vintage state
- **Integration test:** Full pipeline `DiscreteChoiceStep` → `LogitChoiceStep` → `HeatingStateUpdateStep` with MockAdapter
- **Sequential test (AC-11):** Vehicle pipeline → Heating pipeline, verify heating receives vehicle-updated population
- **MockAdapter for tests:** Compute function that returns `total_heating_cost` based on heating attributes (e.g., `heating_emissions_kgco2_kwh * 1000 + heating_age * 200`). Must preserve tracking columns.
- **Shared utils tests:** `test_domain_utils.py` covers `infer_pa_type`, `apply_choices_to_population`, `create_vintage_entries` independently

### Project Structure Notes

```
src/reformlab/discrete_choice/
├── __init__.py       # Updated: add heating exports, update apply_choices import
├── types.py          # UNCHANGED
├── errors.py         # UNCHANGED
├── domain.py         # UNCHANGED
├── expansion.py      # UNCHANGED
├── reshape.py        # UNCHANGED
├── step.py           # UNCHANGED (DiscreteChoiceStep from 14.1)
├── logit.py          # UNCHANGED (LogitChoiceStep from 14.2)
├── domain_utils.py   # NEW — infer_pa_type, apply_choices_to_population,
│                     #        create_vintage_entries (extracted from vehicle.py)
├── vehicle.py        # MODIFIED — imports shared functions from domain_utils.py,
│                     #            removes local definitions
└── heating.py        # NEW — HeatingDomainConfig, HeatingInvestmentDomain,
                      #        HeatingStateUpdateStep, default_heating_domain_config

tests/discrete_choice/
├── __init__.py       # UNCHANGED
├── conftest.py       # UNCHANGED
├── test_types.py     # UNCHANGED
├── test_expansion.py # UNCHANGED
├── test_reshape.py   # UNCHANGED
├── test_step.py      # UNCHANGED
├── test_logit.py     # UNCHANGED
├── test_vehicle.py   # UNCHANGED (existing tests validate extraction didn't break anything)
├── test_domain_utils.py # NEW — Shared utility function tests
└── test_heating.py   # NEW — Heating domain and state update tests
```

No new dependencies required — uses only existing `pyarrow`, `dataclasses` (stdlib), and types from `reformlab.vintage.types`, `reformlab.discrete_choice.types`, `reformlab.computation.types`.

### Cross-Story Dependencies

| Story | Relationship | Notes |
|-------|-------------|-------|
| 14.1 | Depends on | `DiscreteChoiceStep` calls `HeatingInvestmentDomain.apply_alternative()` and `.cost_column` |
| 14.2 | Depends on | `LogitChoiceStep` produces `ChoiceResult` consumed by `HeatingStateUpdateStep` |
| 14.3 | Related | Vehicle domain follows same pattern. Shared utilities extracted from vehicle.py. |
| 14.5 | Uses | Eligibility filtering wraps expansion before logit; heating domain works with or without filtering |
| 14.6 | Blocks | Panel output records decision fields from `ChoiceResult` (chosen, probabilities, utilities) |
| 15.1 | Blocks | Calibration targets reference heating transition rates produced by this domain |

### Out of Scope Guardrails

- **DO NOT** implement the energy renovation decision domain (stretch goal per design note)
- **DO NOT** implement eligibility filtering (Story 14.5)
- **DO NOT** implement panel output extensions (Story 14.6)
- **DO NOT** implement calibration of taste parameters (Epic 15)
- **DO NOT** implement nested logit (conditional logit only)
- **DO NOT** implement multi-component utilities (multiple beta coefficients) — single `beta_cost` via `TasteParameters` only
- **DO NOT** modify `DiscreteChoiceStep`, `LogitChoiceStep`, `domain.py`, `expansion.py`, `reshape.py`, `logit.py`, `types.py`, `errors.py`, or `step.py`
- **DO NOT** modify any orchestrator files (`runner.py`, `step.py`, `types.py`)
- **DO NOT** modify `ComputationAdapter` protocol or `MockAdapter`
- **DO NOT** modify `vintage/config.py` or `vintage/types.py` — `VintageState(asset_class="heating")` works already
- **DO NOT** add numpy or any new dependency
- **DO NOT** implement actual OpenFisca cost computation logic — the adapter handles that
- **DO NOT** modify existing test files (test_vehicle.py etc.) — only add new test files

### References

- [Source: `src/reformlab/discrete_choice/domain.py` — DecisionDomain protocol definition]
- [Source: `src/reformlab/discrete_choice/step.py` — DiscreteChoiceStep, state keys, execute pattern]
- [Source: `src/reformlab/discrete_choice/logit.py` — LogitChoiceStep, DISCRETE_CHOICE_RESULT_KEY, ChoiceResult storage]
- [Source: `src/reformlab/discrete_choice/types.py` — Alternative, ChoiceSet, CostMatrix, ChoiceResult, TasteParameters]
- [Source: `src/reformlab/discrete_choice/errors.py` — DiscreteChoiceError hierarchy]
- [Source: `src/reformlab/discrete_choice/vehicle.py` — Vehicle domain reference implementation (source for extraction)]
- [Source: `src/reformlab/discrete_choice/__init__.py` — Public API exports]
- [Source: `src/reformlab/vintage/types.py` — VintageCohort (age, count, attributes), VintageState (asset_class, cohorts)]
- [Source: `src/reformlab/vintage/config.py` — _SUPPORTED_ASSET_CLASSES = ("vehicle",) — does NOT restrict VintageState creation]
- [Source: `src/reformlab/orchestrator/types.py` — YearState (data, seed, metadata)]
- [Source: `src/reformlab/orchestrator/step.py` — OrchestratorStep protocol, StepRegistry, is_protocol_step]
- [Source: `src/reformlab/computation/types.py` — PopulationData (tables, metadata), PolicyConfig]
- [Source: `src/reformlab/computation/mock_adapter.py` — MockAdapter (compute_fn, version_string, call_log)]
- [Source: `tests/discrete_choice/conftest.py` — MockDomain apply_alternative pattern, _discrete_choice_compute_fn]
- [Source: `tests/discrete_choice/test_vehicle.py` — Vehicle domain test patterns (reference for heating tests)]
- [Source: `_bmad-output/planning-artifacts/phase-2-design-note-discrete-choice-household-decisions.md` — Heating choice set, utility inputs, vintage integration, orchestrator loop]
- [Source: `docs/epics.md` — Epic 14 acceptance criteria, BKL-1404]
- [Source: `docs/project-context.md` — Project rules: PyArrow-first, frozen dataclasses, no numpy, adapter isolation]
- [Source: `examples/populations/french_household_pipeline.py` — Heating type values: "gas", "oil", "electric", "wood", "heat_pump"]
- [Source: `src/reformlab/data/schemas.py` — energy_heating_fuel column definition]
- [Source: `tests/fixtures/ademe/base_carbone.csv` — ADEME emission factors for heating fuels]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Implementation Plan

### Completion Notes List

- Ultimate context engine analysis completed — comprehensive developer guide created
- All architecture patterns extracted from existing codebase (DecisionDomain, OrchestratorStep, VintageState, YearState)
- Design note heating domain specification fully integrated (choice set, utility inputs, vintage integration)
- Vehicle domain reference implementation analyzed as template for heating domain
- Shared utility extraction planned (apply_choices_to_population, infer_pa_type, create_vintage_entries) per Story 14.3 authorization
- Cross-story dependencies mapped (14.1/14.2 inputs, 14.3 shared extraction, 14.5/14.6/15.1 outputs)
- French heating market context integrated: ADEME emission factors, RE2020 oil ban, INSEE/Eurostat heating type classifications
- Antipatterns from Stories 14.1/14.2/14.3 addressed: explicit entity_key, single representation, clear type inference, unknown ID validation, non-dict metadata validation, vintage asset_class validation
- Population column analysis completed: heating_type (utf8), heating_age (int64), heating_emissions_kgco2_kwh (float64)
- Sequential domain execution pattern documented (AC-11) with state key sharing explanation
- Edge cases comprehensively defined (empty population, all-keep, all-switch, missing state, length mismatch, wrong vintage asset_class)
- Out-of-scope guardrails explicitly defined (no renovation, no eligibility, no calibration, no nested logit)

### File List

#### New Files
- `src/reformlab/discrete_choice/domain_utils.py` — infer_pa_type, apply_choices_to_population, create_vintage_entries (extracted from vehicle.py)
- `src/reformlab/discrete_choice/heating.py` — HeatingDomainConfig, HeatingInvestmentDomain, HeatingStateUpdateStep, default_heating_domain_config
- `tests/discrete_choice/test_domain_utils.py` — Shared utility function tests
- `tests/discrete_choice/test_heating.py` — Heating domain and state update tests

#### Modified Files
- `src/reformlab/discrete_choice/vehicle.py` — Import shared functions from domain_utils.py, remove local definitions
- `src/reformlab/discrete_choice/__init__.py` — Add heating exports, update apply_choices_to_population import path, export shared utilities
