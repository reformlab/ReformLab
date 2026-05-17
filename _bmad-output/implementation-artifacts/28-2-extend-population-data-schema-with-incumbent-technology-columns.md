# Story 28.2: Extend `PopulationData` schema with optional incumbent-technology columns

Status: ready-for-dev

## Story

As an analyst running multi-period investment decision scenarios,
I want the population to carry incumbent technology state per household (e.g., `incumbent_heating`, `incumbent_vehicle`),
so that discrete-choice transitions can reflect realistic technology adoption patterns across years without defaulting all households to the same starting alternative.

## Acceptance Criteria

1. Given a population with `incumbent_heating` column in the `menage` entity table, when the discrete-choice step executes, then households retain their incumbent technology when they choose the "keep current" alternative.
2. Given a population with `incumbent_heating` column, when `validate_population_for_technology_set` is called with a `TechnologySet` for heating, then the function validates that all distinct values in the column match alternative IDs in the technology set.
3. Given a population with `incumbent_heating` column containing unknown alternative IDs, when validation runs, then the function raises `DiscreteChoiceError` with a clear message listing the unknown IDs and valid alternatives.
4. Given a population without `incumbent_heating` column and investment decisions enabled, when validation runs, then the function returns a warning message explaining that all households will start at the reference alternative.
5. Given the bundled `fr-synthetic-2024` population, when loaded, then it includes `incumbent_heating` and `incumbent_vehicle` columns derived from existing `heating_type` and `vehicle_type` attribute columns.
6. Given the Quick Test Population, when loaded, then it includes `incumbent_heating` and `incumbent_vehicle` columns defaulted from attribute columns.
7. Given a user-uploaded population without incumbent columns, when the user enables investment decisions, then the scenario can still run with a manifest warning recorded (no blocking error).
8. Given `investmentDecisionsEnabled === false`, when any scenario runs, then the presence or absence of incumbent columns does not affect execution (short-circuit, no validation).

## Tasks / Subtasks

- [ ] Task 1: Create population validation module (AC: #2, #3, #4, #8)
  - [ ] 1.1 Create `src/reformlab/discrete_choice/population_validation.py`
  - [ ] 1.2 Implement `validate_population_for_technology_set(population, technology_set, *, entity_key="menage") -> list[str]`
  - [ ] 1.3 Add check: if `technology_set` is None or no domains enabled, return empty list
  - [ ] 1.4 Add check: for each enabled domain, verify `incumbent_<domain>` column exists in entity table
  - [ ] 1.5 Add check: if column exists, validate all distinct values are in `technology_set.domains[domain].alternatives`
  - [ ] 1.6 Add check: if column missing, return warning message (not an error)
  - [ ] 1.7 Add check: if column has unknown IDs, raise `DiscreteChoiceError` with clear message
  - [ ] 1.8 Add module-level docstring referencing Story 28.2
  - [ ] 1.9 Re-export validation function from `src/reformlab/discrete_choice/__init__.py`
- [ ] Task 2: Migrate bundled populations (AC: #5, #6)
  - [ ] 2.1 Locate bundled population generation for `fr-synthetic-2024`
  - [ ] 2.2 Add `incumbent_heating` column to `menage` table with dictionary encoding `pa.dictionary(pa.int32(), pa.utf8())`
  - [ ] 2.3 Derive incumbent values from existing `heating_type` attribute column (map known types to alternative IDs)
  - [ ] 2.4 Add `incumbent_vehicle` column with same encoding
  - [ ] 2.5 Derive incumbent values from existing `vehicle_type` attribute column
  - [ ] 2.6 Update Quick Test Population generation with same migration
  - [ ] 2.7 Verify row counts and seeds remain unchanged (non-breaking data migration)
- [ ] Task 3: Update data-fusion pipeline (AC: #7)
  - [ ] 3.1 Locate data-fusion pipeline endpoint for generated populations
  - [ ] 3.2 Add incumbent column derivation step at end of fusion pipeline
  - [ ] 3.3 Map fused attribute columns to incumbent alternative IDs
  - [ ] 3.4 Handle case where fused data lacks `heating_type` or `vehicle_type` columns (graceful skip)
- [ ] Task 4: Integration with discrete-choice step (AC: #1, #8)
  - [ ] 4.1 Add import of `validate_population_for_technology_set` in `DiscreteChoiceStep`
  - [ ] 4.2 Call validation at start of `DiscreteChoiceStep.execute()` when `investment_decisions_enabled === true`
  - [ ] 4.3 Log warnings (non-blocking) for missing incumbent columns
  - [ ] 4.4 Ensure short-circuit when `investment_decisions_enabled === false` (already implemented in Story 28.1)
  - [ ] 4.5 Document that incumbent columns are read-only at step start (existing writeback happens in `*StateUpdateStep`)
- [ ] Task 5: Backend tests (AC: #2, #3, #4, #8)
  - [ ] 5.1 Create `tests/discrete_choice/test_population_validation.py`
  - [ ] 5.2 Add tests for valid population with incumbents
  - [ ] 5.3 Add tests for unknown alternative IDs (raises error)
  - [ ] 5.4 Add tests for missing incumbent column (returns warning)
  - [ ] 5.5 Add tests for disabled investment decisions (short-circuit, no validation)
  - [ ] 5.6 Add tests for multiple enabled domains (heating + vehicle)
  - [ ] 5.7 Add integration test with `DiscreteChoiceStep`
- [ ] Task 6: Quality gates
  - [ ] 6.1 Run `uv run ruff check src/reformlab/discrete_choice/ tests/discrete_choice/`
  - [ ] 6.2 Run `uv run mypy src/reformlab/discrete_choice/`
  - [ ] 6.3 Run `uv run pytest tests/discrete_choice/test_population_validation.py`
  - [ ] 6.4 Verify existing discrete-choice tests still pass (regression check)

## Dev Notes

### Critical Architecture Constraints (Source: project-context.md)

**Python Language Rules** (MUST follow — no exceptions):
- **Every file starts with** `from __future__ import annotations` — this is non-negotiable
- **Use `if TYPE_CHECKING:` guards** for imports only needed for annotations or would create circular dependencies
- **Frozen dataclasses are the default** — all domain types use `@dataclass(frozen=True)`
- **Union syntax** — use `X | None` not `Optional[X]`
- **Subsystem-specific exceptions** — each module defines its own error hierarchy; use `DiscreteChoiceError` for validation failures

**PyArrow Dictionary Encoding** (CRITICAL for performance):
```python
# Story 28.2 / AC-2: Use dictionary encoding for incumbent columns
import pyarrow as pa

# Create dictionary-encoded column (O(1) categorical filtering)
incumbent_col = pa.array(
    ["gas_boiler", "heat_pump", "gas_boiler", ...],
    type=pa.dictionary(pa.int32(), pa.utf8())
)

# Access dictionary for validation
dictionary = incumbent_col.dictionary
unique_values = dictionary.to_pylist()  # ["gas_boiler", "heat_pump"]
```

**Error Response Pattern** (MUST follow for validation errors):
```python
from reformlab.discrete_choice.errors import DiscreteChoiceError

# Fail-loud on unknown incumbent IDs
if unknown_ids:
    raise DiscreteChoiceError(
        f"Population contains unknown incumbent technology IDs: {sorted(unknown_ids)}. "
        f"Valid alternatives for domain '{domain}': {sorted(valid_ids)}. "
        f"Households affected: {count_affected}"
    )
```

### Population Schema Specification (Source: spike ADR Section 3.1)

**Column Naming Convention**:
- One column per domain: `incumbent_heating`, `incumbent_vehicle`
- Stored in the `menage` entity table (French household entity)
- PyArrow type: `pa.dictionary(pa.int32(), pa.utf8())`

**Example Schema**:
```
menage table:
  - household_id: int64
  - heating_type: utf8 (existing attribute column)
  - vehicle_type: utf8 (existing attribute column)
  - incumbent_heating: dictionary<int32, utf8>  [NEW]
  - incumbent_vehicle: dictionary<int32, utf8>  [NEW]
```

**Value Semantics**:
- Each value is a `TechnologyAlternative.id` (e.g., `"gas_boiler"`, `"heat_pump"`, `"ev"`)
- Dictionary encoding provides O(1) categorical filtering for eligibility checks
- Columns are optional (backward compatible)

### Existing Code Patterns (Reference for Implementation)

**PopulationData Access Pattern** (from `src/reformlab/computation/types.py:19-70`):
```python
from reformlab.computation.types import PopulationData

# Access entity table
entity_key = "menage"
if entity_key not in population.tables:
    raise DiscreteChoiceError(f"Entity key '{entity_key}' not found")

table = population.tables[entity_key]

# Check for incumbent column
incumbent_col_name = "incumbent_heating"
if incumbent_col_name in table.column_names:
    incumbent_col = table.column(incumbent_col_name)
    # Access dictionary values
    if isinstance(incumbent_col.type, pa.DictionaryType):
        dictionary = incumbent_col.dictionary
        unique_incumbents = set(dictionary.to_pylist())
```

**Validation Helper Pattern** (from existing `evaluate_eligibility` in `eligibility.py`):
```python
def validate_population_for_technology_set(
    population: PopulationData,
    technology_set: TechnologySet,
    *,
    entity_key: str = "menage",
) -> list[str]:
    """Return a list of human-readable warnings; raise on hard schema errors.

    Story 28.2 / AC-2: Validation function for incumbent technology columns.

    Returns:
        List of warning messages (empty if no warnings). Warnings are
        non-blocking — the orchestrator records them in the manifest
        but proceeds with execution.

    Raises:
        DiscreteChoiceError: If incumbent column contains unknown
            alternative IDs (fail-loud data contract violation).
    """
    warnings: list[str] = []

    # Short-circuit: no validation if technology_set is None
    if technology_set is None:
        return warnings

    # Check each enabled domain
    for domain_name, domain_config in technology_set.domains.items():
        if not domain_config.enabled:
            continue

        incumbent_col_name = f"incumbent_{domain_name}"

        # Get entity table
        if entity_key not in population.tables:
            warnings.append(
                f"Entity key '{entity_key}' not found in population. "
                f"Cannot validate {incumbent_col_name}."
            )
            continue

        table = population.tables[entity_key]

        # Check if incumbent column exists
        if incumbent_col_name not in table.column_names:
            warnings.append(
                f"Column '{incumbent_col_name}' not found. "
                f"All households will start at reference alternative "
                f"'{domain_config.reference_alternative_id}'."
            )
            continue

        # Validate all distinct values are known alternatives
        incumbent_col = table.column(incumbent_col_name)

        # Extract unique values from dictionary or plain string column
        if isinstance(incumbent_col.type, pa.DictionaryType):
            unique_values = set(incumbent_col.dictionary.to_pylist())
        else:
            # Fallback for non-dictionary encoding
            unique_values = set(incumbent_col.unique().to_pylist())

        # Get valid alternative IDs from technology set
        valid_ids = {alt.id for alt in domain_config.alternatives}

        # Check for unknown IDs
        unknown_ids = unique_values - valid_ids
        if unknown_ids:
            raise DiscreteChoiceError(
                f"Population contains unknown incumbent technology IDs "
                f"in column '{incumbent_col_name}': {sorted(unknown_ids)}. "
                f"Valid alternatives for domain '{domain_name}': {sorted(valid_ids)}."
            )

    return warnings
```

**Technology Set Integration** (from Story 28.1):
```python
from reformlab.discrete_choice.technology_set import TechnologySet

# The TechnologySet type is already implemented in Story 28.1
# This story adds validation that consumes it

def validate_and_log(
    population: PopulationData,
    technology_set: TechnologySet | None,
    investment_decisions_enabled: bool,
) -> None:
    """Validate population incumbents and log warnings.

    Story 28.2 / AC-8: Integration with DiscreteChoiceStep.

    Short-circuits when investment_decisions_enabled === false
    (already implemented in Story 28.1's DiscreteChoiceStep.execute()).
    """
    if not investment_decisions_enabled:
        # No validation needed
        return

    if technology_set is None:
        # No technology set configured
        return

    warnings = validate_population_for_technology_set(
        population, technology_set, entity_key="menage"
    )

    for warning in warnings:
        logger.warning("event=population_validation warning=%s", warning)
```

### Migration Strategy for Bundled Populations

**Attribute → Incumbent Mapping**:
```python
# Map existing heating_type values to incumbent alternative IDs
HEATING_TYPE_TO_INCUMBENT = {
    "gas": "condensing_boiler",      # Modern gas boiler
    "oil": "condensing_boiler",      # Fallback (oil banned in new installs)
    "electric": "heat_pump_air",     # Assumed heat pump
    "heat_pump": "heat_pump_air",    # Explicit heat pump
    "district": "district_heating",  # District heating
}

# Map existing vehicle_type values to incumbent alternative IDs
VEHICLE_TYPE_TO_INCUMBENT = {
    "petrol": "petrol",
    "diesel": "diesel",
    "hybrid": "hybrid",
    "electric": "ev",
    "plug_in_hybrid": "plug_in_hybrid",
    "none": "keep_current",  # No vehicle
}
```

**One-Time Migration Implementation**:
```python
def add_incumbent_columns_to_population(
    population: PopulationData,
    *,
    entity_key: str = "menage",
    heating_type_col: str = "heating_type",
    vehicle_type_col: str = "vehicle_type",
) -> PopulationData:
    """Add incumbent_heating and incumbent_vehicle columns to population.

    Story 28.2 / AC-5: Migration for bundled populations.

    Returns:
        New PopulationData with incumbent columns added. Does not
        modify the original (PopulationData is frozen).
    """
    if entity_key not in population.tables:
        logger.warning(
            "Entity key '%s' not found, skipping incumbent column migration",
            entity_key,
        )
        return population

    table = population.tables[entity_key]
    n = table.num_rows

    # Migrate heating incumbent
    if heating_type_col in table.column_names:
        heating_types = table.column(heating_type_col).to_pylist()
        heating_incumbents = [
            HEATING_TYPE_TO_INCUMBENT.get(ht, "keep_current")
            for ht in heating_types
        ]
        heating_col = pa.array(
            heating_incumbents,
            type=pa.dictionary(pa.int32(), pa.utf8()),
        )
        table = table.append_column("incumbent_heating", heating_col)

    # Migrate vehicle incumbent
    if vehicle_type_col in table.column_names:
        vehicle_types = table.column(vehicle_type_col).to_pylist()
        vehicle_incumbents = [
            VEHICLE_TYPE_TO_INCUMBENT.get(vt, "keep_current")
            for vt in vehicle_types
        ]
        vehicle_col = pa.array(
            vehicle_incumbents,
            type=pa.dictionary(pa.int32(), pa.utf8()),
        )
        table = table.append_column("incumbent_vehicle", vehicle_col)

    new_tables = dict(population.tables)
    new_tables[entity_key] = table

    from reformlab.computation.types import PopulationData as _PopulationData
    return _PopulationData(
        tables=new_tables,
        metadata=dict(population.metadata),
    )
```

### Testing Standards

**Backend Testing** (from project-context.md):
- Mirror source structure: `tests/discrete_choice/test_population_validation.py`
- Class-based test grouping: `TestPopulationValidation`, `TestPopulationMigration`
- Fixtures in `conftest.py` — build PyArrow tables inline
- Direct assertions: `assert warnings == [...]`
- Use `pytest.raises(DiscreteChoiceError, match="...")` for errors
- Reference story/AC in docstrings: `# Story 28.2 / AC-3`

**Test Cases** (comprehensive coverage):
```python
# Story 28.2 / AC-2: Valid population with incumbents passes validation
def test_validate_population_valid_incumbents():
    population = PopulationData(
        tables={
            "menage": pa.table({
                "household_id": [1, 2, 3],
                "incumbent_heating": pa.array(
                    ["gas_boiler", "heat_pump", "gas_boiler"],
                    type=pa.dictionary(pa.int32(), pa.utf8()),
                ),
            })
        },
        metadata={},
    )
    technology_set = DEFAULT_TECHNOLOGY_SET

    warnings = validate_population_for_technology_set(
        population, technology_set, entity_key="menage"
    )
    assert warnings == []

# Story 28.2 / AC-3: Unknown incumbent IDs raise error
def test_validate_population_unknown_incumbent_ids():
    population = PopulationData(
        tables={
            "menage": pa.table({
                "household_id": [1, 2],
                "incumbent_heating": pa.array(
                    ["gas_boiler", "unknown_tech"],
                    type=pa.dictionary(pa.int32(), pa.utf8()),
                ),
            })
        },
        metadata={},
    )
    technology_set = DEFAULT_TECHNOLOGY_SET

    with pytest.raises(DiscreteChoiceError, match="unknown incumbent technology IDs"):
        validate_population_for_technology_set(
            population, technology_set, entity_key="menage"
        )

# Story 28.2 / AC-4: Missing incumbent column returns warning
def test_validate_population_missing_incumbent_column():
    population = PopulationData(
        tables={
            "menage": pa.table({
                "household_id": [1, 2, 3],
                # No incumbent_heating column
            })
        },
        metadata={},
    )
    technology_set = DEFAULT_TECHNOLOGY_SET

    warnings = validate_population_for_technology_set(
        population, technology_set, entity_key="menage"
    )
    assert len(warnings) == 1
    assert "incumbent_heating" in warnings[0]
    assert "reference alternative" in warnings[0]

# Story 28.2 / AC-8: Disabled investment decisions short-circuit
def test_validate_population_disabled_decisions():
    population = PopulationData(
        tables={"menage": pa.table({"household_id": [1, 2, 3]})},
        metadata={},
    )
    technology_set = None  # Decisions disabled

    warnings = validate_population_for_technology_set(
        population, technology_set, entity_key="menage"
    )
    assert warnings == []
```

### Quality Gates

**Before marking story done, ensure all pass**:
```bash
# Backend quality checks
uv run ruff check src/reformlab/discrete_choice/ tests/discrete_choice/
uv run mypy src/reformlab/discrete_choice/
uv run pytest tests/discrete_choice/test_population_validation.py -v

# Regression check (existing discrete-choice tests must still pass)
uv run pytest tests/discrete_choice/ -v

# Verify population migration doesn't break existing tests
uv run pytest tests/population/ -v
```

### Project Structure Notes

**New Files** (to create):
- `src/reformlab/discrete_choice/population_validation.py` — Validation module
- `tests/discrete_choice/test_population_validation.py` — Validation tests

**Modified Files**:
- `src/reformlab/discrete_choice/__init__.py` — Re-export validation function
- `src/reformlab/discrete_choice/step.py` — Add validation call (optional, depends on design)
- Population generation files (for bundled migrations) — Location TBD by developer

**No Deletions** — All changes are additive or migration-only

### Dependencies Between Stories

- **Story 28.0** (architect spike) — DONE — provides ADR with schema definitions
- **Story 28.1** — DONE — provides `TechnologySet` and `DomainTechnologySet` types
- **Story 28.2** (this story) — READY FOR DEV — population schema extensions
- **Story 28.3** (writeback) — BACKLOG — wires `DiscreteChoiceStep` outputs to population
- **Story 28.4** (wizard) — BACKLOG — consumes validation warnings for UI display
- **Story 28.5** (regression) — BACKLOG — multi-period decision runs

### References

- [Source: `_bmad-output/planning-artifacts/spike-investment-decisions-technology-set-2026-04-26.md`](../planning-artifacts/spike-investment-decisions-technology-set-2026-04-26.md) — ADR Section 3: Population schema delta
- [Source: `src/reformlab/computation/types.py`](../../src/reformlab/computation/types.py) — PopulationData definition
- [Source: `src/reformlab/discrete_choice/types.py`](../../src/reformlab/discrete_choice/types.py) — Alternative, ChoiceSet types
- [Source: `src/reformlab/discrete_choice/technology_set.py`](../../src/reformlab/discrete_choice/technology_set.py) — TechnologySet from Story 28.1
- [Source: `src/reformlab/discrete_choice/step.py`](../../src/reformlab/discrete_choice/step.py) — DiscreteChoiceStep for integration
- [Source: `_bmad-output/project-context.md`](../project-context.md) — Project architecture rules
- [Source: `.claude/projects/-Users-lucas-Workspace-reformlab/memory/MEMORY.md`](../../../../.claude/projects/-Users-lucas-Workspace-reformlab/memory/MEMORY.md) — Development conventions

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

None — implementation not yet started.

### Completion Notes List

Ultimate context engine analysis completed — comprehensive developer guide created for Story 28.2.

### File List

**Story File:**
- `_bmad-output/implementation-artifacts/28-2-extend-population-data-schema-with-incumbent-technology-columns.md` (status: ready-for-dev)

**Files to Create (Implementation):**
- `src/reformlab/discrete_choice/population_validation.py` — Validation module
- `tests/discrete_choice/test_population_validation.py` — Validation tests

**Files to Modify (Implementation):**
- `src/reformlab/discrete_choice/__init__.py` — Re-export validation function
- `src/reformlab/discrete_choice/step.py` — Optional: Add validation call in execute()
- Population generation files — Location TBD: add incumbent column migration
- Data-fusion pipeline — Location TBD: add incumbent column derivation
