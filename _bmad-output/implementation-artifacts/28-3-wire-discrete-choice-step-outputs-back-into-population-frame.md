# Story 28.3: Wire DiscreteChoiceStep outputs back into population frame

Status: ready-for-dev

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

## Tasks / Subtasks

- [ ] Task 1: Extend `apply_choices_to_population()` to write incumbent columns (AC: #1, #2, #3, #4, #7)
  - [ ] 1.1 Add `domain_key: str` parameter to `apply_choices_to_population()` signature
  - [ ] 1.2 After existing attribute column loop, add incumbent column writeback logic
  - [ ] 1.3 Use dictionary encoding: `pa.dictionary(pa.int32(), pa.utf8())` for new columns
  - [ ] 1.4 Preserve existing dictionary type when column already exists (use `set_column` not `append_column`)
  - [ ] 1.5 Create new column if it doesn't exist (backward compatibility for populations without incumbents)
  - [ ] 1.6 Handle multi-domain safety: domain-prefixed column names (`incumbent_heating`, `incumbent_vehicle`)
  - [ ] 1.7 Update all call sites in `vehicle.py` and `heating.py` to pass `domain_key` parameter
  - [ ] 1.8 Add module-level docstring update referencing Story 28.3

- [ ] Task 2: Add TransitionRecord type and emission in StateUpdateSteps (AC: #3, #5)
  - [ ] 2.1 Create `TransitionRecord` frozen dataclass in `decision_record.py`
  - [ ] 2.2 Add fields: `domain_name: str`, `year: int`, `household_ids: pa.Array`, `from_alternative_ids: pa.Array`, `to_alternative_ids: pa.Array`
  - [ ] 2.3 Add `TRANSITION_LOG_KEY = "discrete_choice_transitions"` constant
  - [ ] 2.4 In `VehicleStateUpdateStep.execute()`, read `incumbent_vehicle` before calling `apply_choices_to_population()`
  - [ ] 2.5 After choice application, create `TransitionRecord` with from/to arrays
  - [ ] 2.6 Store in `state.data[TRANSITION_LOG_KEY]` using tuple-append pattern for multi-domain safety
  - [ ] 2.7 Apply same pattern to `HeatingStateUpdateStep.execute()`
  - [ ] 2.8 Handle case where incumbent column doesn't exist (from_alternative_ids = None, skip record emission)

- [ ] Task 3: Extend panel output to show transition columns (AC: #5)
  - [ ] 3.1 In `panel.py::_build_decision_columns()`, add logic to read `TRANSITION_LOG_KEY` from yearly states
  - [ ] 3.2 For each transition record, extract from/to arrays and join to household index
  - [ ] 3.3 Append `{domain}_from` and `{domain}_to` columns to output table
  - [ ] 3.4 Handle missing transition records for years where domain wasn't enabled
  - [ ] 3.5 Update panel schema documentation to include new columns

- [ ] Task 4: Add technology_set field to manifest capture (AC: #6)
  - [ ] 4.1 Add `capture_technology_set()` function in `governance/capture.py`
  - [ ] 4.2 Serialize `TechnologySet` to dict with domains, alternatives, reference IDs
  - [ ] 4.3 Call `capture_technology_set()` in `runner.py::_capture_manifest_fields()`
  - [ ] 4.4 Add `technology_set` field to `RunManifest` type in `governance/manifest.py`
  - [ ] 4.5 Handle case where `technology_set is None` (empty dict in manifest)

- [ ] Task 5: Backend tests (AC: #1, #2, #3, #4, #5, #6, #7)
  - [ ] 5.1 Create `tests/discrete_choice/test_domain_utils_writeback.py`
  - [ ] 5.2 Add test for incumbent column writeback with existing column (set_column path)
  - [ ] 5.3 Add test for incumbent column creation when missing (append_column path)
  - [ ] 5.4 Add test for multi-year execution verifying incumbents carry forward
  - [ ] 5.5 Add test for multi-domain writeback (heating + vehicle) without clobbering
  - [ ] 5.6 Add test for eligibility invariance (ineligible households keep original incumbents)
  - [ ] 5.7 Add integration test with `VehicleStateUpdateStep` and `HeatingStateUpdateStep`
  - [ ] 5.8 Add panel output test verifying `{domain}_from` and `{domain}_to` columns
  - [ ] 5.9 Add manifest test verifying `technology_set` field is captured

- [ ] Task 6: Quality gates
  - [ ] 6.1 Run `uv run ruff check src/reformlab/discrete_choice/ tests/discrete_choice/`
  - [ ] 6.2 Run `uv run mypy src/reformlab/discrete_choice/`
  - [ ] 6.3 Run `uv run pytest tests/discrete_choice/test_domain_utils_writeback.py`
  - [ ] 6.4 Run `uv run pytest tests/orchestrator/ -k "panel or manifest"`
  - [ ] 6.5 Verify existing discrete-choice tests still pass (regression check)

## Dev Notes

### Critical Architecture Constraints (Source: project-context.md)

**Python Language Rules** (MUST follow — no exceptions):
- **Every file starts with** `from __future__ import annotations` — this is non-negotiable
- **Use `if TYPE_CHECKING:` guards** for imports only needed for annotations or would create circular dependencies
- **Frozen dataclasses are the default** — all domain types use `@dataclass(frozen=True)`
- **Union syntax** — use `X | None` not `Optional[X]`
- **Subsystem-specific exceptions** — each module defines its own error hierarchy; use `DiscreteChoiceError` for validation failures
- **PopulationData immutability** — always return new instances via `dataclasses.replace()`, never mutate in place

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
    domain_key: str,  # NEW: Story 28.3 parameter
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

    Returns:
        New PopulationData with incumbent_<domain> column written.
    """
```

**Incumbent Writeback Logic** (to add after line 168 in `domain_utils.py`):
```python
# Story 28.3 / AC-1, AC-3: Write incumbent_<domain> column
# After the existing attribute column loop (line 168)

incumbent_col_name = f"incumbent_{domain_key}"

if incumbent_col_name in table.column_names:
    # Column exists: preserve dictionary encoding (set_column path)
    existing_type = table.column(incumbent_col_name).type
    incumbent_col = pa.array(chosen_list, type=existing_type)
    col_idx = table.column_names.index(incumbent_col_name)
    table = table.set_column(col_idx, incumbent_col_name, incumbent_col)
else:
    # Column missing: create with dictionary encoding (append_column path)
    incumbent_col = pa.array(
        chosen_list,
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
def _build_decision_columns(
    self,
    yearly_states: dict[int, YearState],
    entity_key: str,
) -> pa.Table:
    """Build decision-related columns for panel output.

    Story 28.3 / AC-5: Extended to include {domain}_from and {domain}_to columns.
    """
    # ... existing decision column logic ...

    # Story 28.3 / AC-5: Add transition columns
    transition_records_by_year: dict[int, list[TransitionRecord]] = {}
    for year, year_state in yearly_states.items():
        transitions = year_state.data.get(TRANSITION_LOG_KEY, ())
        if transitions:
            transition_records_by_year[year] = list(transitions)

    # Build {domain}_from and {domain}_to columns per year
    for year in sorted(yearly_states.keys()):
        year_prefix = f"y{year}_"

        if year not in transition_records_by_year:
            continue  # No transitions this year (domain not enabled)

        for record in transition_records_by_year[year]:
            domain = record.domain_name

            # {domain}_from: incumbent technology before choice
            from_col_name = f"{year_prefix}{domain}_from"
            from_col = record.from_alternative_ids
            if from_col_name not in output_table.column_names:
                output_table = output_table.append_column(from_col_name, from_col)

            # {domain}_to: chosen technology after choice
            to_col_name = f"{year_prefix}{domain}_to"
            to_col = record.to_alternative_ids
            if to_col_name not in output_table.column_names:
                output_table = output_table.append_column(to_col_name, to_col)
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

**Critical**: When eligibility filtering is active, `DiscreteChoiceStep` only computes choices for eligible households. Ineligible households are excluded from the choice computation and must retain their original `incumbent_<domain>` values.

**How it works** (from eligibility.py:232-251):
```python
# DiscreteChoiceStep.execute() applies filtering before compute
if self._eligibility_filter is not None:
    eligible_mask = evaluate_eligibility(...)
    filtered_pop, eligible_indices = filter_population_by_eligibility(
        population, eligible_mask, entity_key
    )
    # filtered_pop.tables[entity_key] only contains eligible rows
    population = filtered_pop  # Used for expansion and compute

# StateUpdateStep receives full population (not filtered)
# but ChoiceResult.chosen only has values for eligible households

# apply_choices_to_population() must handle this:
# - eligible_indices maps choice_result positions to population positions
# - ineligible households keep their original incumbent values
```

**Implementation Note**: The existing `apply_choices_to_population()` already handles this correctly via the `choice_result.chosen` alignment with `eligible_indices`. Story 28.3's incumbent writeback follows the same pattern — only eligible households receive new incumbent values.

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
    eligible_mask = pa.array([True, True, False, True, False, True, True, False, True, True])
    ineligible_indices = [2, 4, 7]  # Keep original incumbents

    population = PopulationData(tables={
        "menage": pa.table({
            "household_id": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            "incumbent_heating": ["condensing_boiler"] * 10,
        })
    }, metadata={})

    # Choice result only has 6 values (eligible households)
    choice_result = ChoiceResult(chosen=pa.array(["heat_pump_air"] * 6))

    # Apply with eligible_indices mapping
    updated = apply_choices_to_population_with_eligibility(
        population, choice_result, eligible_indices, alternatives, "menage", domain_key="heating"
    )

    incumbents = updated.tables["menage"].column("incumbent_heating").to_pylist()
    assert incumbents[0] == "heat_pump_air"  # Eligible, changed
    assert incumbents[2] == "condensing_boiler"  # Ineligible, unchanged
    assert incumbents[4] == "condensing_boiler"  # Ineligible, unchanged
    assert incumbents[7] == "condensing_boiler"  # Ineligible, unchanged
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
- `tests/discrete_choice/test_domain_utils_writeback.py` — Writeback tests (9+ test cases)

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

Story 28.3 specification completed with comprehensive developer context:

- **Analysis completed**: Two parallel research agents analyzed discrete-choice writeback patterns and orchestrator state management
- **Integration points identified**: 8 specific files with line-level guidance for implementation
- **Multi-year flow documented**: Complete end-to-end flow showing how incumbents carry forward between years
- **Code patterns provided**: Ready-to-use implementations for incumbent writeback, TransitionRecord emission, panel output, and manifest capture
- **Testing strategy defined**: 9+ test cases covering all acceptance criteria
- **Quality gates specified**: Ruff, mypy, pytest commands for validation
- **Dependencies mapped**: Clear dependency chain from Story 28.0 → 28.1 → 28.2 → 28.3 (this story)

**Key Implementation Guidance**:
- Extend `apply_choices_to_population()` with `domain_key` parameter — preserves existing behavior, adds incumbent writeback
- Use `set_column` when incumbent column exists (preserve dictionary encoding), `append_column` when missing
- StateUpdateSteps emit `TransitionRecord` with from/to arrays before/after `apply_choices_to_population()`
- Panel output gains `{domain}_from` and `{domain}_to` columns from `TRANSITION_LOG_KEY`
- Manifest gains `technology_set` field via new `capture_technology_set()` function
- Multi-domain safety via tuple-append pattern: `(*existing_transitions, new_record)`
- Eligibility invariance handled automatically by existing `eligible_indices` mapping

### File List

**Story File:**
- `_bmad-output/implementation-artifacts/28-3-wire-discrete-choice-step-outputs-back-into-population-frame.md` (status: ready-for-dev)

**Files to Create:**
- `tests/discrete_choice/test_domain_utils_writeback.py` — Writeback tests (9+ test cases)

**Files to Modify:**
- `src/reformlab/discrete_choice/domain_utils.py` — Extend apply_choices_to_population() with domain_key parameter and incumbent writeback
- `src/reformlab/discrete_choice/decision_record.py` — Add TransitionRecord type and TRANSITION_LOG_KEY constant
- `src/reformlab/discrete_choice/vehicle.py` — Update call site, add TransitionRecord emission in execute()
- `src/reformlab/discrete_choice/heating.py` — Update call site, add TransitionRecord emission in execute()
- `src/reformlab/orchestrator/panel.py` — Extend _build_decision_columns() for transition columns
- `src/reformlab/governance/capture.py` — Add capture_technology_set() function
- `src/reformlab/governance/manifest.py` — Add technology_set field to RunManifest
- `src/reformlab/orchestrator/runner.py` — Call capture_technology_set() in _capture_manifest_fields()
