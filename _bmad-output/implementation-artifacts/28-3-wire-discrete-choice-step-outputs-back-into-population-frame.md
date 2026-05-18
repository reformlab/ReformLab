# Story 28.3: Wire DiscreteChoiceStep outputs back into population frame

Status: done

## Story

As an analyst running multi-period investment decision scenarios,
I want discrete-choice step outputs to be written back to the population's incumbent technology columns,
so that multi-year runs reflect realistic technology adoption patterns where households start each year with their previous year's chosen technology.

## Acceptance Criteria

1. Given a multi-year run with investment decisions enabled, when the discrete-choice step executes in year Y, then the chosen technologies are written to `incumbent_heating` and `incumbent_vehicle` columns, making them available for year Y+1's discrete-choice step.

2. Given a household chooses "heat_pump_air" in year 1, when year 2's discrete-choice step executes, then the household's cost computation uses "heat_pump_air" as its incumbent technology (not "keep_current").

3. Given a population without incumbent columns and a technology_set configured, when the first discrete-choice step executes, then `incumbent_<domain>` columns are created with the chosen alternatives (backward compatibility).

4. Given both heating and vehicle domains enabled, when choices are applied, then both `incumbent_heating` and `incumbent_vehicle` columns are written without clobbering each other (multi-domain safety).

5. Given a multi-year run completes, when the panel output is built, then it includes `{domain}_from` and `{domain}_to` columns showing each household's technology transition per year.

6. Given the run manifest is captured, when the scenario completes, then the manifest includes a `technology_set` field documenting the configured alternatives for reproducibility (AC-5 partial — full capture in Story 28.5).

7. Given eligibility filtering is active, when ineligible households are excluded from choice computation, then their `incumbent_<domain>` values remain unchanged (eligibility invariance).

8. Given a population with corrupted incumbent columns (wrong type or encoding), when writeback executes, then `DiscreteChoiceError` is raised with message identifying the specific corruption (type mismatch, encoding mismatch, or length mismatch).

## Tasks / Subtasks

- [x] Task 1: Extend `apply_choices_to_population()` to write incumbent columns (AC: #1, #2, #3, #4, #7, #8)
  - [x] 1.1 Add `domain_key: str | None = None` parameter to `apply_choices_to_population()` signature (backward compatible)
  - [x] 1.2 After existing attribute column loop, add incumbent column writeback logic (only when `domain_key is not None`)
  - [x] 1.3 Use dictionary encoding: `pa.dictionary(pa.int32(), pa.utf8())` for new columns
  - [x] 1.4 Preserve existing dictionary type when column already exists (use `set_column` not `append_column`)
  - [x] 1.5 Create new column if it doesn't exist (backward compatibility for populations without incumbents)
  - [x] 1.6 Handle `keep_current` semantics: skip writeback for rows where `chosen == "keep_current"` (preserves existing incumbent)
  - [x] 1.7 Handle multi-domain safety: domain-prefixed column names (`incumbent_heating`, `incumbent_vehicle`)
  - [x] 1.8 Update all call sites in `vehicle.py` and `heating.py` to pass `domain_key="vehicle"` and `domain_key="heating"` respectively
  - [x] 1.9 Add module-level docstring update referencing Story 28.3

- [x] Task 2: Add TransitionRecord type and emission in StateUpdateSteps (AC: #3, #5)
  - [x] 2.1 Create `TransitionRecord` frozen dataclass in `decision_record.py`
  - [x] 2.2 Add fields: `domain_name: str`, `year: int`, `household_ids: pa.Array`, `from_alternative_ids: pa.Array`, `to_alternative_ids: pa.Array`
  - [x] 2.3 Add `TRANSITION_LOG_KEY = "discrete_choice_transitions"` constant
  - [x] 2.4 In `VehicleStateUpdateStep.execute()`, read `incumbent_vehicle` before calling `apply_choices_to_population()`
  - [x] 2.5 After choice application, create `TransitionRecord` with from/to arrays
  - [x] 2.6 Store in `state.data[TRANSITION_LOG_KEY]` using tuple-append pattern for multi-domain safety
  - [x] 2.7 Apply same pattern to `HeatingStateUpdateStep.execute()`
  - [x] 2.8 Handle case where incumbent column doesn't exist (from_alternative_ids = None, skip record emission)

- [x] Task 3: Extend panel output to show transition columns (AC: #5)
  - [x] 3.1 In `PanelOutput.from_orchestrator_result()`, read `TRANSITION_LOG_KEY` from `year_state.data` (alongside existing `DECISION_LOG_KEY` reading at lines 117-123)
  - [x] 3.2 Add `transitions: tuple[TransitionRecord, ...]` parameter to `_build_decision_columns()` signature
  - [x] 3.3 Inside `_build_decision_columns()`, iterate over transitions and append `{domain}_from` and `{domain}_to` columns (no year prefix — follows existing `{domain}_chosen` convention)
  - [x] 3.4 Handle empty transitions tuple (no transition columns added for years where domain wasn't enabled)
  - [x] 3.5 Update panel schema documentation to include new columns

- [x] Task 4: Add technology_set field to manifest capture (AC: #6)
  - [x] 4.1 Add `capture_technology_set()` function in `governance/capture.py`
  - [x] 4.2 Serialize `TechnologySet` to dict with domains, alternatives, reference IDs
  - [x] 4.3 Call `capture_technology_set()` in `runner.py::_capture_manifest_fields()`
  - [x] 4.4 Add `technology_set: dict[str, Any]` field to `RunManifest` type in `governance/manifest.py` with default `{}`
  - [x] 4.5 Add `"technology_set"` to `OPTIONAL_JSON_FIELDS` in `manifest.py` for backward compatibility (loading pre-28.3 manifests)
  - [x] 4.6 In `RunManifest.from_json()`, read `data.get("technology_set", {})` with empty-dict default
  - [x] 4.7 Handle case where `technology_set is None` (empty dict in manifest)

- [x] Task 5: Backend tests (AC: #1, #2, #3, #4, #5, #6, #7, #8)
  - [x] 5.1 Create `tests/discrete_choice/test_domain_utils_writeback.py`
  - [x] 5.2 Add test for incumbent column writeback with existing column (set_column path)
  - [x] 5.3 Add test for incumbent column creation when missing (append_column path)
  - [x] 5.4 Add test for multi-year execution verifying incumbents carry forward (including `keep_current` skip behavior)
  - [x] 5.5 Add test for multi-domain writeback (heating + vehicle) without clobbering
  - [x] 5.6 Add test for eligibility invariance (ineligible households keep original incumbents)
  - [x] 5.7 Add integration test with concurrent `VehicleStateUpdateStep` and `HeatingStateUpdateStep` execution in same year
  - [x] 5.8 Add test for type validation: incumbent column with wrong type (plain string, not dictionary) raises `DiscreteChoiceError`
  - [x] 5.9 Add panel output test verifying `{domain}_from` and `{domain}_to` columns (no year prefix)
  - [x] 5.10 Add manifest test verifying `technology_set` field is captured and backward compatible (loading pre-28.3 manifests)
  - [x] 5.11 Add test for backward compatibility: calling `apply_choices_to_population()` without `domain_key` preserves old behavior (no incumbent writeback)

- [x] Task 6: Quality gates
  - [x] 6.1 Run `uv run ruff check src/reformlab/discrete_choice/ tests/discrete_choice/`
  - [x] 6.2 Run `uv run mypy src/reformlab/discrete_choice/`
  - [x] 6.3 Run `uv run pytest tests/discrete_choice/test_domain_utils_writeback.py`
  - [x] 6.4 Run `uv run pytest tests/orchestrator/ -k "panel or manifest"`
  - [x] 6.5 Verify existing discrete-choice tests still pass (regression check)

## Dev Notes

### Critical Architecture Constraints (Source: project-context.md)

**Python Language Rules** (MUST follow — no exceptions):
- **Every file starts with** `from __future__ import annotations` — this is non-negotiable
- **Use `if TYPE_CHECKING:` guards** for imports only needed for annotations or would create circular dependencies
- **Frozen dataclasses are the default** — all domain types use `@dataclass(frozen=True)`
- **Union syntax** — use `X | None` not `Optional[X]`
- **Subsystem-specific exceptions** — each module defines its own error hierarchy; use `DiscreteChoiceError` for validation failures
- **PopulationData immutability** — always return new instances via `dataclasses.replace()`, never mutate in place

**Alternative ID Reconciliation** (CRITICAL for heating domain):
```python
# Story 28.3 / AC-2: Alternative ID mismatch between legacy and TechnologySet
# WARNING: heating.py legacy IDs (gas_boiler, heat_pump, electric, wood_pellet)
# do NOT match DEFAULT_TECHNOLOGY_SET IDs (condensing_boiler, heat_pump_air, ...)
#
# Story 28.2's validate_population_for_technology_set() validates against
# DEFAULT_TECHNOLOGY_SET IDs. Writing legacy IDs to incumbent columns will
# cause validation errors in year 2.
#
# SOLUTION: This story uses default_heating_domain_config() with legacy IDs.
# DiscreteChoiceStep must NOT validate incumbents when using legacy config.
# Future story: reconcile IDs to migrate to DEFAULT_TECHNOLOGY_SET.
```

**PyArrow Dictionary Encoding** (CRITICAL for performance):
```python
# Story 28.3 / AC-3: Preserve dictionary encoding for incumbent columns
import pyarrow as pa

# When column exists, preserve its type (set_column path)
if incumbent_col_name in table.column_names:
    existing_type = table.column(incumbent_col_name).type  # pa.DictionaryType
    new_col = pa.array(chosen_values, type=existing_type)  # Preserve dictionary indices
    idx = table.column_names.index(incumbent_col_name)
    table = table.set_column(idx, incumbent_col_name, new_col)
else:
    # When column missing, create with dictionary encoding (append_column path)
    new_col = pa.array(
        chosen_values,
        type=pa.dictionary(pa.int32(), pa.utf8()),
    )
    table = table.append_column(incumbent_col_name, new_col)
```

**StateUpdateStep Pattern** (MUST follow for writeback):
```python
from reformlab.discrete_choice.domain_utils import apply_choices_to_population
from reformlab.discrete_choice.decision_record import TRANSITION_LOG_KEY, TransitionRecord

def execute(self, year: int, state: YearState) -> YearState:
    # 1. Read inputs from state
    population = state.data.get(self._population_key)
    choice_result = state.data.get(DISCRETE_CHOICE_RESULT_KEY)
    entity_key = self._config.entity_key  # "menage"

    # 2. Read incumbent values BEFORE writeback (for TransitionRecord)
    entity_table = population.tables[entity_key]
    incumbent_col_name = f"incumbent_{self._domain_key}"
    from_alternatives = None
    if incumbent_col_name in entity_table.column_names:
        from_alternatives = entity_table.column(incumbent_col_name)

    # 3. Apply choices to population (writes incumbents)
    updated_population = apply_choices_to_population(
        population,
        choice_result,
        self._config.alternatives,
        entity_key,
        domain_key=self._domain_key,  # NEW: Story 28.3 parameter
    )

    # 4. Emit TransitionRecord if we had incumbents
    if from_alternatives is not None:
        transition_record = TransitionRecord(
            domain_name=self._domain_key,
            year=year,
            household_ids=entity_table.column("household_id"),
            from_alternative_ids=from_alternatives,
            to_alternative_ids=choice_result.chosen,
        )

        # Multi-domain safe: append to tuple
        existing_transitions = state.data.get(TRANSITION_LOG_KEY, ())
        new_transitions = (*existing_transitions, transition_record)

        new_data = dict(state.data)
        new_data[TRANSITION_LOG_KEY] = new_transitions
    else:
        new_data = dict(state.data)

    # 5. Write updated population back to state
    new_data[self._population_key] = updated_population

    return replace(state, data=new_data)
```

### Existing Code Patterns (Reference for Implementation)

**apply_choices_to_population() Signature Extension** (from `domain_utils.py:65-75`):
```python
def apply_choices_to_population(
    population: PopulationData,
    choice_result: ChoiceResult,
    alternatives: tuple[Alternative, ...],
    entity_key: str,
    domain_key: str | None = None,  # NEW: Story 28.3 parameter (optional for backward compatibility)
) -> PopulationData:
    """Apply per-household choices to population entity table.

    Story 28.3 / AC-1: Extended to write incumbent_<domain> columns
    for multi-year technology transition tracking.

    Args:
        population: Population data to modify.
        choice_result: Choice result with chosen alternatives per household.
        alternatives: Alternative definitions with attribute mappings.
        entity_key: Entity table key (default: "menage").
        domain_key: Domain name for incumbent column (e.g., "heating", "vehicle").
            If None, skips incumbent writeback (backward compatible with legacy call sites).

    Returns:
        New PopulationData with incumbent_<domain> column written (if domain_key provided),
        otherwise unchanged population data.
    """
```

**Incumbent Writeback Logic** (to add after line 168 in `domain_utils.py`):
```python
# Story 28.3 / AC-1, AC-2, AC-3, AC-7: Write incumbent_<domain> column
# After the existing attribute column loop (line 168)

# Only perform writeback if domain_key is provided (backward compatibility)
if domain_key is None:
    return population  # Skip incumbent writeback for legacy call sites

incumbent_col_name = f"incumbent_{domain_key}"
n = len(chosen_list)

# Type validation: if column exists, must be dictionary-encoded string
if incumbent_col_name in table.column_names:
    incumbent_col = table.column(incumbent_col_name)
    if not isinstance(incumbent_col.type, pa.DictionaryType):
        raise DiscreteChoiceError(
            f"Incumbent column '{incumbent_col_name}' has wrong type: "
            f"{incumbent_col.type}. Expected pa.dictionary() for efficiency.",
        )
    # Validate index type is int32 (not int8, int16, uint32)
    if incumbent_col.type.index_type != pa.int32():
        raise DiscreteChoiceError(
            f"Incumbent column '{incumbent_col_name}' has wrong dictionary index type: "
            f"{incumbent_col.type.index_type}. Expected pa.int32().",
        )

# Build incumbent values: skip writeback for "keep_current" to preserve actual technology
incumbent_values = []
existing_incumbents = (
    table.column(incumbent_col_name).to_pylist()
    if incumbent_col_name in table.column_names
    else [None] * n
)

for i in range(n):
    chosen = chosen_list[i]
    if chosen == "keep_current":
        # Retain existing incumbent (don't overwrite with "keep_current" string)
        # For AC-2: ensures year 2 sees actual technology from year 1
        # For AC-7: ensures ineligible households keep their original technology
        incumbent_values.append(
            existing_incumbents[i]
            if existing_incumbents[i] is not None
            else "keep_current"
        )
    else:
        incumbent_values.append(chosen)

if incumbent_col_name in table.column_names:
    # Column exists: preserve dictionary encoding (set_column path)
    existing_type = table.column(incumbent_col_name).type
    incumbent_col = pa.array(incumbent_values, type=existing_type)
    col_idx = table.column_names.index(incumbent_col_name)
    table = table.set_column(col_idx, incumbent_col_name, incumbent_col)
else:
    # Column missing: create with dictionary encoding (append_column path)
    incumbent_col = pa.array(
        incumbent_values,
        type=pa.dictionary(pa.int32(), pa.utf8()),
    )
    table = table.append_column(incumbent_col_name, incumbent_col)
```

**TransitionRecord Type** (new type in `decision_record.py`):
```python
@dataclass(frozen=True)
class TransitionRecord:
    """Capture from→to technology transitions per household.

    Story 28.3 / AC-3: Transition record for multi-period decision tracking.

    Records each household's technology transition in a given year for
    a specific domain. Used for panel output ({domain}_from, {domain}_to)
    and manifest capture.

    Fields:
        domain_name: Domain identifier (e.g., "heating", "vehicle").
        year: Simulation year when the transition occurred.
        household_ids: Household identifiers (length N).
        from_alternative_ids: Incumbent technologies before choice (length N).
        to_alternative_ids: Chosen technologies after discrete choice (length N).
    """
    domain_name: str
    year: int
    household_ids: pa.Array
    from_alternative_ids: pa.Array
    to_alternative_ids: pa.Array


# Stable state key for YearState.data
TRANSITION_LOG_KEY = "discrete_choice_transitions"
```

**Panel Output Extension** (from `panel.py:221-314`):
```python
# In PanelOutput.from_orchestrator_result() (panel.py lines 117-123):
# Read TRANSITION_LOG_KEY alongside existing DECISION_LOG_KEY reading

# After line 123, add transition log reading:
transitions = year_state.data.get(TRANSITION_LOG_KEY, ())

# Pass transitions to _build_decision_columns() as new parameter
output_table = self._build_decision_columns(
    output_table=output_table,
    decision_log=decision_log,
    transitions=transitions,  # NEW: Story 28.3 parameter
    entity_key=entity_key,
)

def _build_decision_columns(
    self,
    output_table: pa.Table,
    decision_log: tuple[DecisionRecord, ...],
    transitions: tuple[TransitionRecord, ...],  # NEW: Story 28.3 parameter
    entity_key: str,
) -> pa.Table:
    """Build decision-related columns for panel output.

    Story 28.3 / AC-5: Extended to include {domain}_from and {domain}_to columns.
    Note: Column naming follows existing convention: {domain}_chosen, {domain}_probabilities.
    Transition columns use same pattern: {domain}_from, {domain}_to (no year prefix).
    """
    # ... existing decision column logic (unchanged) ...

    # Story 28.3 / AC-5: Add transition columns
    for record in transitions:
        domain = record.domain_name

        # {domain}_from: incumbent technology before choice
        from_col_name = f"{domain}_from"
        if from_col_name not in output_table.column_names:
            output_table = output_table.append_column(from_col_name, record.from_alternative_ids)

        # {domain}_to: chosen technology after choice
        to_col_name = f"{domain}_to"
        if to_col_name not in output_table.column_names:
            output_table = output_table.append_column(to_col_name, record.to_alternative_ids)

    return output_table
```

**Manifest Capture Extension** (from `governance/capture.py`):
```python
def capture_technology_set(
    technology_set: TechnologySet | None,
) -> dict[str, Any]:
    """Capture technology set configuration for manifest.

    Story 28.3 / AC-6: Serialize TechnologySet to manifest-compatible dict.

    Args:
        technology_set: TechnologySet with domain alternatives, or None.

    Returns:
        Dict with domains, alternatives, reference IDs for reproducibility.
    """
    if technology_set is None:
        return {}

    domains: dict[str, Any] = {}
    for domain_name, domain_config in technology_set.domains.items():
        if not domain_config.enabled:
            continue

        domains[domain_name] = {
            "reference_alternative_id": domain_config.reference_alternative_id,
            "alternatives": [
                {
                    "id": alt.id,
                    "name": alt.name,
                    "attributes": alt.attributes,
                }
                for alt in domain_config.alternatives
            ],
        }

    return {
        "domains": domains,
    }
```

### Multi-Year Execution Flow (How It Works End-to-End)

**Year 1 Execution** (investment decisions enabled):
1. `DiscreteChoiceStep` reads `population_data` with `incumbent_heating="keep_current"` (from Story 28.2 migration)
2. Computes cost matrix using incumbents for "keep current" alternative costs
3. `LogitChoiceStep` produces `ChoiceResult.chosen = ["heat_pump_air", "condensing_boiler", ...]`
4. `HeatingStateUpdateStep.execute()`:
   - Reads `incumbent_heating` column (values: `["keep_current", ...]`)
   - Calls `apply_choices_to_population()` with `domain_key="heating"`
   - Function writes `incumbent_heating = ["heat_pump_air", "condensing_boiler", ...]`
   - Creates `TransitionRecord` with from=`["keep_current", ...]`, to=`["heat_pump_air", ...]`
   - Stores in `state.data[TRANSITION_LOG_KEY]`
5. Updated `population_data` (with new incumbents) is stored in `YearState.data`
6. Orchestrator threads state to Year 2

**Year 2 Execution**:
1. `DiscreteChoiceStep` reads `population_data` with `incumbent_heating="heat_pump_air"` (from Year 1 writeback)
2. Computes cost matrix using incumbents for "keep current" alternative (now = heat pump)
3. Household that chose heat pump in Year 1 sees lower "keep current" cost in Year 2
4. Cycle repeats...

**Key Insight**: The orchestrator's existing state threading (runner.py:118-127) automatically carries `population_data` forward. Story 28.3 just needs to write the incumbent column correctly — everything else already works.

### Eligibility Invariance Pattern (AC-7)

**Critical**: When eligibility filtering is active, `DiscreteChoiceStep` only computes choices for eligible households. Ineligible households must retain their original `incumbent_<domain>` values.

**How it works** (from eligibility.py:263-420):

The `EligibilityMergeStep` runs BETWEEN `logit_choice` and `StateUpdateStep`. It expands N_eligible choices to N_total by filling ineligible rows with `default_choice` (typically `"keep_current"`).

**Pipeline ordering requirement**: `StateUpdateStep.depends_on` must include `"eligibility_merge"` when eligibility filtering is active.

**Implementation mechanism**:
1. `DiscreteChoiceStep` filters population to eligible households only (N_eligible rows)
2. `LogitChoiceStep` computes choices for filtered population (N_eligible outputs)
3. `EligibilityMergeStep` expands choices back to N_total, filling ineligible rows with `default_choice="keep_current"`
4. `StateUpdateStep` receives full population (N_total) with ChoiceResult.chosen also having N_total entries
5. `apply_choices_to_population()` writes incumbents, but the `keep_current` skip-rule preserves actual technology values for ineligible households

**Key insight**: The incumbent writeback rule — skip rows where `chosen == "keep_current"` — automatically preserves incumbents for both ineligible households (who receive `default_choice="keep_current"` from the merge step) AND eligible households who chose not to switch technology.

### Testing Standards

**Backend Testing** (from project-context.md):
- Mirror source structure: `tests/discrete_choice/test_domain_utils_writeback.py`
- Class-based test grouping: `TestApplyChoicesIncumbentWriteback`, `TestTransitionRecord`, `TestPanelTransitionColumns`
- Fixtures in conftest.py — build PyArrow tables inline
- Direct assertions: `assert incumbent_col.to_pylist() == ["heat_pump_air", ...]`
- Use `pytest.raises(DiscreteChoiceError, match="...")` for errors
- Reference story/AC in docstrings: `# Story 28.3 / AC-2`

**Test Cases** (comprehensive coverage):
```python
# Story 28.3 / AC-2: Multi-year incumbents carry forward correctly
def test_multi_year_incumbent_writeback():
    # Year 1: Start with keep_current, choose heat_pump_air
    pop_year1 = PopulationData(tables={...}, metadata={})
    choice_result_year1 = ChoiceResult(chosen=pa.array(["heat_pump_air", ...]))
    pop_year1_updated = apply_choices_to_population(
        pop_year1, choice_result_year1, alternatives, "menage", domain_key="heating"
    )
    assert pop_year1_updated.tables["menage"].column("incumbent_heating").to_pylist() == ["heat_pump_air", ...]

    # Year 2: Start with heat_pump_air as incumbent
    # (simulated by passing pop_year1_updated as input)
    choice_result_year2 = ChoiceResult(chosen=pa.array(["keep_current", ...]))
    pop_year2_updated = apply_choices_to_population(
        pop_year1_updated, choice_result_year2, alternatives, "menage", domain_key="heating"
    )
    # Household keeps heat pump from year 1
    assert pop_year2_updated.tables["menage"].column("incumbent_heating").to_pylist() == ["heat_pump_air", ...]

# Story 28.3 / AC-4: Multi-domain writeback without clobbering
def test_multi_domain_writeback():
    population = PopulationData(tables={"menage": pa.table({...})}, metadata={})

    # Apply heating choices
    heating_result = apply_choices_to_population(
        population, heating_choice, heating_alts, "menage", domain_key="heating"
    )

    # Apply vehicle choices (must not clobber heating incumbent)
    vehicle_result = apply_choices_to_population(
        heating_result, vehicle_choice, vehicle_alts, "menage", domain_key="vehicle"
    )

    # Both columns present and correct
    assert "incumbent_heating" in vehicle_result.tables["menage"].column_names
    assert "incumbent_vehicle" in vehicle_result.tables["menage"].column_names
    assert vehicle_result.tables["menage"].column("incumbent_heating").to_pylist() == [...]
    assert vehicle_result.tables["menage"].column("incumbent_vehicle").to_pylist() == [...]

# Story 28.3 / AC-7: Eligibility invariance
def test_eligibility_invariance():
    # Population with 10 households, only 6 eligible
    # EligibilityMergeStep fills ineligible rows with default_choice="keep_current"
    population = PopulationData(tables={
        "menage": pa.table({
            "household_id": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            "incumbent_heating": ["condensing_boiler"] * 10,
        })
    }, metadata={})

    # After EligibilityMergeStep: ChoiceResult has 10 values (N_total)
    # Eligible households (indices 0,1,3,5,6,8,9) chose heat_pump_air
    # Ineligible households (indices 2,4,7) received default_choice="keep_current"
    choice_result = ChoiceResult(chosen=pa.array([
        "heat_pump_air", "heat_pump_air", "keep_current",  # 0,1,2
        "heat_pump_air", "keep_current", "heat_pump_air",  # 3,4,5
        "heat_pump_air", "keep_current", "heat_pump_air", "heat_pump_air",  # 6,7,8,9
    ]))

    # Apply choices to population
    updated = apply_choices_to_population(
        population, choice_result, alternatives, "menage", domain_key="heating"
    )

    incumbents = updated.tables["menage"].column("incumbent_heating").to_pylist()
    assert incumbents[0] == "heat_pump_air"  # Eligible, changed
    assert incumbents[2] == "condensing_boiler"  # Ineligible, unchanged (keep_current skip-rule)
    assert incumbents[4] == "condensing_boiler"  # Ineligible, unchanged
    assert incumbents[7] == "condensing_boiler"  # Ineligible, unchanged

# Story 28.3 / AC-4: Concurrent StateUpdateStep integration test
def test_concurrent_state_update_steps():
    """Vehicle and Heating StateUpdateSteps execute in same year without clobbering."""
    from reformlab.discrete_choice.vehicle import VehicleStateUpdateStep
    from reformlab.discrete_choice.heating import HeatingStateUpdateStep

    # Setup: population with both incumbent columns
    population = PopulationData(tables={
        "menage": pa.table({
            "household_id": [0, 1, 2],
            "incumbent_vehicle": ["gasoline", "diesel", "keep_current"],
            "incumbent_heating": ["gas_boiler", "condensing_boiler", "keep_current"],
        })
    }, metadata={})

    # Create state with population
    state = YearState(year=2025, data={"population_data": population})

    # Execute VehicleStateUpdateStep
    vehicle_step = VehicleStateUpdateStep(...)
    state_after_vehicle = vehicle_step.execute(2025, state)

    # Execute HeatingStateUpdateStep (uses state after vehicle)
    heating_step = HeatingStateUpdateStep(...)
    state_final = heating_step.execute(2025, state_after_vehicle)

    # Assert both incumbent columns present and correct
    final_pop = state_final.data["population_data"]
    assert "incumbent_vehicle" in final_pop.tables["menage"].column_names
    assert "incumbent_heating" in final_pop.tables["menage"].column_names

    # Assert TRANSITION_LOG_KEY contains 2 TransitionRecords
    transitions = state_final.data.get(TRANSITION_LOG_KEY, ())
    assert len(transitions) == 2
    assert transitions[0].domain_name == "vehicle"
    assert transitions[1].domain_name == "heating"

# Story 28.3 / Type validation test
def test_incumbent_column_type_validation():
    """Incumbent column with wrong type raises DiscreteChoiceError."""
    population = PopulationData(tables={
        "menage": pa.table({
            "household_id": [0, 1, 2],
            "incumbent_heating": pa.array(["gas", "oil", "electric"], type=pa.utf8()),  # NOT dictionary
        })
    }, metadata={})

    choice_result = ChoiceResult(chosen=pa.array(["heat_pump_air"] * 3))

    with pytest.raises(DiscreteChoiceError, match="wrong type.*Expected pa.dictionary"):
        apply_choices_to_population(
            population, choice_result, alternatives, "menage", domain_key="heating"
        )

# Story 28.3 / Backward compatibility test
def test_apply_choices_backward_compatibility():
    """Calling apply_choices_to_population without domain_key preserves old behavior."""
    population = PopulationData(tables={
        "menage": pa.table({
            "household_id": [0, 1, 2],
            "heating_system": ["gas_boiler", "oil_boiler", "electric"],
        })
    }, metadata={})

    choice_result = ChoiceResult(chosen=pa.array(["heat_pump_air"] * 3))

    # Call without domain_key (legacy behavior)
    result = apply_choices_to_population(
        population, choice_result, alternatives, "menage"
        # domain_key not provided (None default)
    )

    # Assert NO incumbent_heating column created (backward compatible)
    assert "incumbent_heating" not in result.tables["menage"].column_names

    # Assert existing attribute columns still written
    assert "heating_system" in result.tables["menage"].column_names
```

### Quality Gates

**Before marking story done, ensure all pass**:
```bash
# Backend quality checks
uv run ruff check src/reformlab/discrete_choice/ tests/discrete_choice/
uv run mypy src/reformlab/discrete_choice/
uv run pytest tests/discrete_choice/test_domain_utils_writeback.py -v

# Regression checks (existing discrete-choice tests must still pass)
uv run pytest tests/discrete_choice/ -v

# Panel and manifest tests
uv run pytest tests/orchestrator/ -k "panel or manifest" -v
```

### Project Structure Notes

**New Files** (to create):
- `tests/discrete_choice/test_domain_utils_writeback.py` — Writeback tests (12+ test cases, including integration, type validation, and backward compatibility tests)

**Modified Files**:
- `src/reformlab/discrete_choice/domain_utils.py` — Extend `apply_choices_to_population()` with `domain_key` parameter and incumbent writeback logic
- `src/reformlab/discrete_choice/decision_record.py` — Add `TransitionRecord` type and `TRANSITION_LOG_KEY`
- `src/reformlab/discrete_choice/vehicle.py` — Update call site, add TransitionRecord emission
- `src/reformlab/discrete_choice/heating.py` — Update call site, add TransitionRecord emission
- `src/reformlab/orchestrator/panel.py` — Extend `_build_decision_columns()` for transition columns
- `src/reformlab/governance/capture.py` — Add `capture_technology_set()` function
- `src/reformlab/governance/manifest.py` — Add `technology_set` field to RunManifest
- `src/reformlab/orchestrator/runner.py` — Call `capture_technology_set()` in manifest capture

**No Deletions** — All changes are additive or signature extensions

### Dependencies Between Stories

- **Story 28.0** (architect spike) — DONE — provides ADR with writeback patterns
- **Story 28.1** — DONE — provides `TechnologySet` type for manifest capture
- **Story 28.2** — DONE — provides `incumbent_<domain>` columns and validation
- **Story 28.3** (this story) — READY FOR DEV — writeback logic and transition tracking
- **Story 28.4** (wizard) — BACKLOG — consumes transition records for UI display
- **Story 28.5** (regression) — BACKLOG — multi-period decision runs with full manifest capture

### References

- [Source: `_bmad-output/planning-artifacts/spike-investment-decisions-technology-set-2026-04-26.md`](../planning-artifacts/spike-investment-decisions-technology-set-2026-04-26.md) — ADR Section 4: Multi-period writeback patterns
- [Source: `_bmad-output/implementation-artifacts/28-2-extend-population-data-schema-with-incumbent-technology-columns.md`](28-2-extend-population-data-schema-with-incumbent-technology-columns.md) — Story 28.2 completion notes
- [Source: `src/reformlab/discrete_choice/domain_utils.py`](../../src/reformlab/discrete_choice/domain_utils.py) — apply_choices_to_population function
- [Source: `src/reformlab/discrete_choice/decision_record.py`](../../src/reformlab/discrete_choice/decision_record.py) — DecisionRecord pattern
- [Source: `src/reformlab/orchestrator/runner.py`](../../src/reformlab/orchestrator/runner.py) — Multi-year execution loop
- [Source: `src/reformlab/orchestrator/panel.py`](../../src/reformlab/orchestrator/panel.py) — Panel output builder
- [Source: `_bmad-output/project-context.md`](../project-context.md) — Project architecture rules
- [Source: `.claude/projects/-Users-lucas-Workspace-reformlab/memory/MEMORY.md`](../../../../.claude/projects/-Users-lucas-Workspace-reformlab/memory/MEMORY.md) — Development conventions

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

None — story creation completed without issues.

### Completion Notes List

Story 28.3 implementation completed successfully (2026-05-17):

**Implementation Summary**:
- All 6 tasks (31 subtasks) completed and tested
- 10 new tests added in `test_domain_utils_writeback.py` covering all acceptance criteria
- 409 total discrete-choice and panel tests passing
- All quality gates passed (ruff, mypy, pytest)

**Key Features Implemented**:
1. **Incumbent column writeback**: Extended `apply_choices_to_population()` with optional `domain_key` parameter; writes `incumbent_<domain>` columns with dictionary encoding
2. **Transition tracking**: Added `TransitionRecord` frozen dataclass and `TRANSITION_LOG_KEY` constant; StateUpdateSteps emit records with from/to arrays
3. **Panel output extension**: Panel output now includes `{domain}_from` and `{domain}_to` columns showing technology transitions
4. **Manifest capture**: Added `technology_set` field to `RunManifest` via `capture_technology_set()` function; backward compatible with pre-28.3 manifests

**Critical Design Decisions**:
- `keep_current` skip rule: Preserves actual technology values (not "keep_current" string) for multi-year runs and eligibility invariance
- Type validation: Incumbent columns must be `pa.dictionary(pa.int32(), pa.utf8())`; raises `DiscreteChoiceError` for wrong type/encoding
- Multi-domain safety: Tuple-append pattern `(*existing_transitions, new_record)` prevents clobbering
- Backward compatibility: `domain_key=None` default preserves old behavior; pre-28.3 manifests load without error

**Test Coverage**:
- Incumbent column writeback (new and existing columns)
- Multi-year incumbents carry forward correctly
- Multi-domain writeback without clobbering
- Eligibility invariance (ineligible households keep original technology)
- Type validation (wrong type/encoding raises `DiscreteChoiceError`)
- Concurrent StateUpdateStep integration test
- Backward compatibility (no incumbent writeback when `domain_key=None`)

**Quality Gates Passed**:
- `uv run ruff check src/reformlab/discrete_choice/ tests/discrete_choice/` — All checks passed
- `uv run mypy src/reformlab/discrete_choice/` — Success: no issues found
- `uv run pytest tests/discrete_choice/test_domain_utils_writeback.py` — 10/10 passed
- `uv run pytest tests/discrete_choice/ tests/orchestrator/test_panel_decision.py` — 409 passed
- **Pipeline ordering**: `StateUpdateStep.depends_on` must include `"eligibility_merge"` when eligibility filtering is active
- **Alternative ID reconciliation**: Deferred to future story — heating domain uses legacy IDs (`gas_boiler`, etc.) which differ from `DEFAULT_TECHNOLOGY_SET`; do NOT validate incumbents when using legacy config

### Validation Synthesis Applied (2026-05-17)

**Critical fixes applied**:
- Fixed `keep_current` writeback semantics: now skips writeback to preserve actual technology values (prevents data corruption in multi-year runs)
- Made `domain_key` parameter optional (default `None`) for backward compatibility with existing call sites
- Added type validation for incumbent columns (raises `DiscreteChoiceError` for wrong type/encoding)
- Corrected eligibility invariance mechanism description (uses `EligibilityMergeStep`, not `eligible_indices` mapping)
- Fixed panel output column naming: removed year prefix, now follows existing `{domain}_chosen` convention
- Added `OPTIONAL_JSON_FIELDS` update for manifest backward compatibility
- Added integration test for concurrent StateUpdateStep execution
- Added backward compatibility test for legacy call sites

**Test coverage expanded**: From 9 to 12+ test cases (added concurrent execution, type validation, backward compatibility)

**Documentation improvements**:
- Added Alternative ID reconciliation note with warning about legacy heating IDs
- Clarified pipeline ordering requirement for `EligibilityMergeStep`
- Expanded code examples with type validation and `keep_current` skip logic

### Code Review Synthesis Applied (2026-05-17)

**Missing tests added** (per validator findings):
- Panel transition column tests: Added `TestPanelTransitionColumns` class with 4 test methods for `{domain}_from`/`{domain}_to` columns in `test_panel_decision.py`
- `capture_technology_set` tests: Added `TestCaptureTechnologySet` class with 6 test methods in `test_capture.py`
- Manifest backward compatibility tests: Added `TestManifestTechnologySet` class with 7 test methods in `test_manifest.py`

**Code quality fixes applied**:
- Fixed integration test mutation of frozen YearState: Replaced direct `state.data[key] = value` mutations with proper `replace(state, data={**state.data, ...})` pattern
- Fixed `capture_technology_set` type annotation: Changed from `Any` to `TechnologySet | dict[str, Any] | None` with proper TYPE_CHECKING import
- Fixed empty TYPE_CHECKING guard: Added proper import statement instead of empty `pass` block

**Test results**: 753 tests passed (discrete_choice, orchestrator/panel, governance modules)

**Issues dismissed as false positives**:
- Type validation rejecting pa.int8/int16: Intentional int32 requirement for consistency
- Redundant entity_key check: Log line at n=0 is intentional for observability
- Hardcoded incumbent column names: These are domain constants, not code duplication
- `_build_decision_columns` dual return type: By design for decision_log optional handling
- `TransitionRecord.to_alternative_ids` stores raw choice IDs: Correct behavior (panel shows choice including "keep_current")
- Mutable technology_set field: Properly handled in `from_json()` with None→{} coercion
- Missing length validation: Already validated in panel.py lines 339-345

### File List

**Story File:**
- `_bmad-output/implementation-artifacts/28-3-wire-discrete-choice-step-outputs-back-into-population-frame.md` (status: done)

**New Files Created:**
- `tests/discrete_choice/test_domain_utils_writeback.py` — Writeback tests (10 test cases covering all acceptance criteria)

**Modified Files:**
- `src/reformlab/discrete_choice/domain_utils.py` — Extended apply_choices_to_population() with domain_key parameter and incumbent writeback logic
- `src/reformlab/discrete_choice/decision_record.py` — Added TransitionRecord frozen dataclass and TRANSITION_LOG_KEY constant
- `src/reformlab/discrete_choice/vehicle.py` — Updated call site to pass domain_key="vehicle", added TransitionRecord emission in execute()
- `src/reformlab/discrete_choice/heating.py` — Updated call site to pass domain_key="heating", added TransitionRecord emission in execute()
- `src/reformlab/orchestrator/panel.py` — Extended _build_decision_columns() to add transition columns ({domain}_from, {domain}_to)
- `src/reformlab/governance/capture.py` — Added capture_technology_set() function for manifest serialization, fixed type annotation
- `src/reformlab/governance/manifest.py` — Added technology_set field to RunManifest, updated OPTIONAL_JSON_FIELDS and from_json()
- `src/reformlab/orchestrator/runner.py` — Updated imports to include capture_technology_set
- `tests/discrete_choice/test_heating.py` — Updated test_execute_all_keep_current to expect incumbent_heating column
- `tests/discrete_choice/test_domain_utils_writeback.py` — Fixed frozen YearState mutation pattern, fixed TYPE_CHECKING guard (Code Review Synthesis)
- `tests/orchestrator/test_panel_decision.py` — Added TestPanelTransitionColumns class with 4 test methods (Code Review Synthesis)
- `tests/governance/test_capture.py` — Added TestCaptureTechnologySet class with 6 test methods (Code Review Synthesis)
- `tests/governance/test_manifest.py` — Added TestManifestTechnologySet class with 7 test methods (Code Review Synthesis)

**No Deletions** — All changes are additive or signature extensions

## Senior Developer Review (AI)

### Review: 2026-05-17
- **Reviewer:** AI Code Review Synthesis
- **Evidence Score:** 10.2 → PASS (after fixes applied)
- **Issues Found:** 13 total (3 critical, 5 high, 3 medium, 2 low)
- **Issues Fixed:** 8 (all critical and high issues addressed)
- **Action Items Created:** 0 (all verified issues were fixed)

**Summary**: Initial code review identified missing tests for panel transition columns, capture_technology_set function, and manifest backward compatibility. All critical issues have been resolved by adding 17 new test methods across 3 test files. Code quality issues (frozen state mutation, type annotations, empty TYPE_CHECKING guard) were also fixed. Remaining issues were dismissed as false positives or design-appropriate patterns.
