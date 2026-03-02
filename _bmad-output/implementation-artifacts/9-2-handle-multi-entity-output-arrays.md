# Story 9.2: Handle Multi-Entity Output Arrays

Status: done

## Story

As a **platform developer integrating OpenFisca-France**,
I want the adapter to correctly handle output variables that belong to different entity types (individu, menage, famille, foyer_fiscal),
so that multi-entity computations return correctly shaped results mapped to their respective entity tables instead of crashing on array length mismatches.

## Context & Motivation

OpenFisca simulations operate on a multi-entity model. In OpenFisca-France, there are 4 entities:

| Entity Key (singular) | Entity Plural | Description | Example Variable |
|---|---|---|---|
| `individu` | `individus` | Person (singular entity) | `salaire_net` |
| `famille` | `familles` | Family (group entity) | `rsa` |
| `foyer_fiscal` | `foyers_fiscaux` | Tax household (group entity) | `impot_revenu_restant_a_payer` |
| `menage` | `menages` | Dwelling (group entity) | `revenu_disponible` |

When `simulation.calculate(var_name, period)` is called, the returned numpy array length equals the number of instances of that variable's entity — **not** the number of persons. For a married couple (2 persons, 1 foyer_fiscal, 1 menage):
- `salaire_net` returns 2 values (one per person)
- `impot_revenu_restant_a_payer` returns 1 value (one per foyer_fiscal)
- `revenu_disponible` returns 1 value (one per menage)

The current `_extract_results()` method (line 341-350 of `openfisca_api_adapter.py`) naively combines all output arrays into a single `pa.Table`, which crashes with a PyArrow error when arrays have different lengths.

**Source:** Spike 8-1 findings, Gap 2. [Source: `_bmad-output/implementation-artifacts/spike-findings-8-1-openfisca-integration.md`]

## Acceptance Criteria

1. **AC-1: Entity-aware result extraction** — Given output variables that return per-entity arrays (e.g., per-menage, per-foyer_fiscal), when the adapter processes results, then arrays are correctly mapped to their respective entity tables.

2. **AC-2: Correct array length per entity** — Given a variable defined on `foyer_fiscal` entity, when results are returned, then the output array length matches the number of foyers fiscaux, not the number of individuals.

3. **AC-3: Mixed-entity output mapping** — Given mixed-entity output variables, when processed, then each variable's values are stored in the correct entity-level result table with proper entity IDs.

4. **AC-4: Backward compatibility** — Given output variables that all belong to the same entity (e.g., all `individu`-level), when processed, then the adapter returns results in a format compatible with existing consumers (`ComputationResult.output_fields` as `pa.Table`).

5. **AC-5: Clear error on entity detection failure** — Given a variable whose entity cannot be determined from the TBS, when `_extract_results()` runs, then a clear `ApiMappingError` is raised with the variable name and available entity information.

## Tasks / Subtasks

- [x] Task 1: Determine variable-to-entity mapping from TBS (AC: #1, #2, #5)
  - [x] 1.1 Add `_resolve_variable_entities()` method that queries `tbs.variables[var_name].entity` to determine which entity each output variable belongs to
  - [x] 1.2 Group output variables by entity (e.g., `{"individu": ["salaire_net"], "foyer_fiscal": ["impot_revenu_restant_a_payer"]}`)
  - [x] 1.3 Handle edge case where variable entity cannot be resolved — raise `ApiMappingError` with actionable message
  - [x] 1.4 Unit tests with mock TBS: verify grouping logic, error on unknown variable entity

- [x] Task 2: Refactor `_extract_results()` to produce per-entity tables (AC: #1, #2, #3)
  - [x] 2.1 Replace single `pa.Table` construction with per-entity extraction loop
  - [x] 2.2 For each entity group, call `simulation.calculate()` for its variables and build a `pa.Table` per entity
  - [x] 2.3 Store results as `dict[str, pa.Table]` keyed by entity plural name
  - [x] 2.4 Unit tests: verify correct array lengths per entity, verify table column names

- [x] Task 3: Evolve `ComputationResult` to support multi-entity outputs (AC: #1, #3, #4)
  - [x] 3.1 Add `entity_tables: dict[str, pa.Table]` field to `ComputationResult` (default empty dict for backward compatibility)
  - [x] 3.2 Keep `output_fields: pa.Table` as the primary/default output for backward compatibility — when all variables belong to one entity, `output_fields` is that entity's table
  - [x] 3.3 When variables span multiple entities, `output_fields` contains the person-entity table (or the first entity's table if no person entity), and `entity_tables` contains all per-entity tables
  - [x] 3.4 Add metadata entry `"output_entities"` listing which entities have tables
  - [x] 3.5 Update `ComputationResult` type stub (`.pyi` file)
  - [x] 3.6 Unit tests: verify backward compatibility (existing code accessing `output_fields` still works), verify `entity_tables` populated correctly

- [x] Task 4: Update `OpenFiscaApiAdapter.compute()` to wire new extraction (AC: #1, #2, #3)
  - [x] 4.1 Pass TBS to `_extract_results()` so it can resolve variable entities
  - [x] 4.2 Update `compute()` return to populate both `output_fields` and `entity_tables`
  - [x] 4.3 Update metadata with `"output_entities"` and per-entity row counts
  - [x] 4.4 Unit tests with mock TBS and mock simulation

- [x] Task 5: Update downstream consumers for backward compatibility (AC: #4)
  - [x] 5.1 Verify `ComputationStep` in orchestrator still works (it accesses `result.output_fields.num_rows`)
  - [x] 5.2 Verify `PanelOutput.from_orchestrator_result()` still works (it accesses `comp_result.output_fields`)
  - [x] 5.3 Verify `MockAdapter` still produces valid `ComputationResult` objects
  - [x] 5.4 Run full existing test suite to confirm no regressions

- [x] Task 6: Integration tests with real OpenFisca-France (AC: #1, #2, #3)
  - [x] 6.1 Test: married couple (2 persons, 1 foyer, 1 menage) with mixed-entity output variables — verify separate tables
  - [x] 6.2 Test: single-entity variables only — verify backward-compatible single table
  - [x] 6.3 Test: verify array lengths match entity instance counts
  - [x] 6.4 Mark integration tests with `@pytest.mark.integration` (requires `openfisca-france` installed)

- [x] Task 7: Run quality gates (all ACs)
  - [x] 7.1 `uv run ruff check src/ tests/`
  - [x] 7.2 `uv run mypy src/`
  - [x] 7.3 `uv run pytest tests/computation/ tests/orchestrator/`

## Dev Notes

### Architecture Constraints

- **Adapter isolation is absolute**: Only `computation/openfisca_adapter.py` and `openfisca_api_adapter.py` may import OpenFisca. All OpenFisca imports must be lazy (inside methods, not at module level).
- **Frozen dataclasses**: `ComputationResult` is `@dataclass(frozen=True)`. Adding `entity_tables` requires a default value (`field(default_factory=dict)`) for backward compatibility.
- **Protocol compatibility**: `ComputationAdapter` protocol defines `compute() -> ComputationResult`. The protocol itself doesn't change — only the `ComputationResult` dataclass gains a new optional field.
- **PyArrow is canonical**: All data containers use `pa.Table`. No pandas.
- **`from __future__ import annotations`** at top of every file.

### Key OpenFisca API Details

**Determining a variable's entity:**
```python
# In OpenFisca, each variable has an .entity attribute
variable = tbs.variables["impot_revenu_restant_a_payer"]
entity = variable.entity  # Returns the Entity object
entity_key = entity.key    # "foyer_fiscal"
entity_plural = entity.plural  # "foyers_fiscaux"
```

**Determining array length for an entity in a simulation:**
```python
# simulation.calculate() returns numpy array with length == entity population count
# For a simulation with 2 persons and 1 foyer_fiscal:
salaire = simulation.calculate("salaire_net", "2024")  # shape: (2,)
irpp = simulation.calculate("impot_revenu_restant_a_payer", "2024")  # shape: (1,)
```

**Entity membership (for future broadcasting — NOT in scope for this story):**
```python
# OpenFisca tracks entity membership via roles
# simulation.populations["foyer_fiscal"].members_entity_id  → array mapping persons to foyers
# This is needed for Story 9.4 (broadcasting group-level values to person level)
```

### Files to Modify

| File | Change |
|------|--------|
| `src/reformlab/computation/types.py` | Add `entity_tables` field to `ComputationResult` |
| `src/reformlab/computation/types.pyi` | Update type stub |
| `src/reformlab/computation/openfisca_api_adapter.py` | Refactor `_extract_results()`, add `_resolve_variable_entities()` |
| `tests/computation/test_openfisca_api_adapter.py` | Add unit tests for entity-aware extraction |
| `tests/computation/test_result.py` | Add tests for new `entity_tables` field |
| `tests/computation/test_openfisca_integration.py` | Add integration tests for multi-entity output |

### Files to Verify (No Changes Expected)

| File | Why |
|------|-----|
| `src/reformlab/computation/adapter.py` | Protocol unchanged — verify still satisfied |
| `src/reformlab/computation/mock_adapter.py` | Verify `ComputationResult` construction still valid |
| `src/reformlab/orchestrator/computation_step.py` | Accesses `result.output_fields.num_rows` — must still work |
| `src/reformlab/orchestrator/panel.py` | Accesses `comp_result.output_fields` — must still work |
| `src/reformlab/computation/quality.py` | Validates `output_fields` schema — must still work |

### Backward Compatibility Strategy

The key design decision is **additive, not breaking**:

1. `ComputationResult.output_fields` remains a single `pa.Table` — all existing consumers continue to work unchanged.
2. A new `entity_tables: dict[str, pa.Table]` field is added with `default_factory=dict` so existing code constructing `ComputationResult` without it continues to work.
3. When all output variables belong to one entity, `output_fields` is that entity's table (same as before).
4. When variables span multiple entities, `output_fields` contains the person-entity table (primary entity), and `entity_tables` contains the full per-entity breakdown.
5. `MockAdapter` is unaffected — it never sets `entity_tables`, which defaults to `{}`.

### Mock TBS Pattern for Unit Tests

The existing test infrastructure uses `SimpleNamespace` mocks. Extend with variable entity info:

```python
from types import SimpleNamespace

def _make_mock_tbs_with_entities(
    entity_keys: tuple[str, ...] = ("individu", "foyer_fiscal", "menage"),
    variable_entities: dict[str, str] | None = None,
    person_entity: str = "individu",
) -> MagicMock:
    """Create a mock TBS where variables know their entity."""
    tbs = MagicMock()

    entities_by_key: dict[str, SimpleNamespace] = {}
    entities = []
    for key in entity_keys:
        entity = SimpleNamespace(
            key=key,
            plural=key + "s" if not key.endswith("s") else key,
            is_person=(key == person_entity),
        )
        entities.append(entity)
        entities_by_key[key] = entity
    tbs.entities = entities

    # Build variables with entity references
    if variable_entities is None:
        variable_entities = {}
    variables = {}
    for var_name, entity_key in variable_entities.items():
        var_mock = MagicMock()
        var_mock.entity = entities_by_key[entity_key]
        variables[var_name] = var_mock
    tbs.variables = variables

    return tbs
```

### Test Data: Married Couple Reference Case

From the spike 8-1 integration tests, the canonical multi-entity test case is:

```python
# 2 persons, 1 foyer_fiscal, 1 menage (married couple)
entities_dict = {
    "individus": {
        "person_0": {"salaire_de_base": {"2024": 30000.0}, "age": {"2024-01": 30}},
        "person_1": {"salaire_de_base": {"2024": 0.0}, "age": {"2024-01": 28}},
    },
    "familles": {
        "famille_0": {"parents": ["person_0", "person_1"]},
    },
    "foyers_fiscaux": {
        "foyer_0": {"declarants": ["person_0", "person_1"]},
    },
    "menages": {
        "menage_0": {
            "personne_de_reference": ["person_0"],
            "conjoint": ["person_1"],
        },
    },
}
# Expected:
# salaire_net (individu) → 2 values
# impot_revenu_restant_a_payer (foyer_fiscal) → 1 value
# revenu_disponible (menage) → 1 value
```

### Existing Integration Test Pattern

Integration tests are in `tests/computation/test_openfisca_integration.py` and use:
- `@pytest.mark.integration` marker
- Module-scoped `tbs` fixture (TBS loads once, ~3-5 seconds)
- Direct `SimulationBuilder.build_from_entities()` calls
- Known-value assertions with tolerance: `abs(computed - expected) <= MARGIN`

### What This Story Does NOT Cover

- **Person-level broadcasting** of group entity values (deferred to Story 9.4 or later — requires entity membership arrays)
- **Variable periodicity** handling (`calculate` vs `calculate_add`) — that is Story 9.3
- **PopulationData 4-entity format** with role assignments — that is Story 9.4
- **Modifying the `ComputationAdapter` protocol** — protocol stays unchanged
- **Modifying `MockAdapter`** — it continues to work with the default empty `entity_tables`

### Project Structure Notes

- Source layout: `src/reformlab/` is the installable package
- Tests mirror source: `tests/computation/` matches `src/reformlab/computation/`
- Each test subdirectory has `__init__.py` and `conftest.py`
- Class-based test grouping with AC references in docstrings
- Integration tests require `openfisca-france` optional dependency: `uv sync --extra openfisca`
- Run unit tests: `uv run pytest tests/computation/ -m "not integration"`
- Run integration tests: `uv run pytest tests/computation/ -m integration`

### References

- [Source: `_bmad-output/implementation-artifacts/spike-findings-8-1-openfisca-integration.md` — Gap 2: Multi-entity output arrays]
- [Source: `src/reformlab/computation/openfisca_api_adapter.py` — `_extract_results()` method, lines 341-350]
- [Source: `src/reformlab/computation/types.py` — `ComputationResult` dataclass]
- [Source: `src/reformlab/orchestrator/computation_step.py` — downstream consumer of `ComputationResult.output_fields`]
- [Source: `src/reformlab/orchestrator/panel.py` — downstream consumer of `comp_result.output_fields`]
- [Source: `src/reformlab/computation/mock_adapter.py` — `MockAdapter` constructs `ComputationResult`]
- [Source: `tests/computation/test_openfisca_integration.py` — `test_multi_entity_variable_array_lengths` documenting the gap]
- [Source: `_bmad-output/planning-artifacts/epics.md` — Epic 9, Story 9.2 acceptance criteria]
- [Source: `_bmad-output/planning-artifacts/architecture.md` — Computation Adapter Pattern, Step-Pluggable Orchestrator]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (via create-story workflow)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed — comprehensive developer guide created
- All 3 acceptance criteria from epics file expanded to 5 ACs with backward compatibility and error handling coverage
- Spike 8-1 findings fully integrated as context
- Downstream consumer impact analysis completed (ComputationStep, PanelOutput, MockAdapter, quality.py)
- Backward compatibility strategy documented: additive `entity_tables` field with empty dict default
- Mock TBS pattern extended with variable-to-entity mapping for unit tests
- Integration test reference case (married couple) documented with expected array lengths
- **Code review synthesis (2026-03-01):** Fixed 5 issues found during review:
  1. (Critical) `metadata["output_entities"]` and `metadata["entity_row_counts"]` now computed from `result_entity_tables` (post-filter) so they are consistent with the returned `entity_tables` field — previously single-entity results had non-empty `output_entities` while `entity_tables` was `{}`, violating data contract
  2. (High) Added `ApiMappingError` guard in `__init__` for empty `output_variables` — prevents cryptic `StopIteration` from propagating up
  3. (High) Moved `_resolve_variable_entities()` call before `_build_simulation()` — fail-fast pattern avoids expensive simulation build if entity resolution fails
  4. (Medium) Replaced misleading comment + silent singular-key fallback in `_resolve_variable_entities` with explicit `ApiMappingError` — silently using the singular key as the plural would produce wrong dict keys (e.g. `"foyer_fiscal"` instead of `"foyers_fiscaux"`) and cause silent downstream failures
  5. (Medium) Added `metadata["output_entities"] == []` and `metadata["entity_row_counts"] == {}` assertions to `test_compute_single_entity_backward_compatible` — regression guard that would have caught issue #1

### File List

- `src/reformlab/computation/types.py` — modify (add `entity_tables` field)
- `src/reformlab/computation/types.pyi` — modify (update stub)
- `src/reformlab/computation/openfisca_api_adapter.py` — modify (refactor `_extract_results`, add `_resolve_variable_entities`)
- `tests/computation/test_openfisca_api_adapter.py` — modify (add entity-aware extraction tests)
- `tests/computation/test_result.py` — modify (add `entity_tables` tests)
- `tests/computation/test_openfisca_integration.py` — modify (add multi-entity output integration tests)
