# Story 9.4: Define Population Data 4-Entity Format

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **platform developer integrating OpenFisca-France**,
I want the adapter to support a PopulationData format that expresses the full 4-entity model (individu, famille, foyer_fiscal, menage) with entity membership relationships,
so that multi-person populations with specific household compositions (couples, families) can be passed to `SimulationBuilder.build_from_entities()` with correct group entity role assignments — instead of relying on OpenFisca's single-person auto-creation.

## Context & Motivation

OpenFisca-France operates on a **4-entity model**:

| Entity Key | Plural | Type | Role Keys for `build_from_entities()` |
|---|---|---|---|
| `individu` | `individus` | Person (singular) | N/A — no roles |
| `famille` | `familles` | Group | `parents`, `enfants` |
| `foyer_fiscal` | `foyers_fiscaux` | Group | `declarants`, `personnes_a_charge` |
| `menage` | `menages` | Group | `personne_de_reference`, `conjoint`, `enfants`, `autres` |

**The current adapter (`_population_to_entity_dict()`) does NOT handle entity relationships.** It treats every column in every PopulationData table as a variable value wrapped in a period dict (`{period_str: value}`). This works for single-person populations because OpenFisca auto-creates group entities — but **it fails silently or crashes for multi-person populations** that require explicit group memberships (e.g., a married couple filing joint taxes in one `foyer_fiscal`, or a family with children in one `famille`).

**Real-world consequence:** Without this story, any population with more than one person per household requires hand-building the entity dict outside the adapter (as the integration tests currently do), bypassing the adapter's validation, period-wrapping, and policy parameter injection. This defeats the purpose of the adapter abstraction.

**What `build_from_entities()` expects for group entities:**

```python
{
    "individus": {
        "individu_0": {"salaire_de_base": {"2024": 30000.0}},
        "individu_1": {"salaire_de_base": {"2024": 0.0}},
    },
    "familles": {
        "famille_0": {"parents": ["individu_0", "individu_1"]},
    },
    "foyers_fiscaux": {
        "foyer_0": {"declarants": ["individu_0", "individu_1"]},
    },
    "menages": {
        "menage_0": {
            "personne_de_reference": ["individu_0"],
            "conjoint": ["individu_1"],
        },
    },
}
```

**The role dict keys come from `role.plural or role.key`** (see Dev Notes for details). This is the critical mapping that must be correct for `build_from_entities()` to assign group memberships properly.

**Source:** Spike 8-1 findings, recommended follow-up #4: "Update PopulationData format for OpenFisca-France — Define a standard way to express the 4-entity model with role assignments in PopulationData." [Source: `_bmad-output/implementation-artifacts/spike-findings-8-1-openfisca-integration.md`, line 106]

## Acceptance Criteria

1. **AC-1: 4-entity PopulationData format** — Given the French tax-benefit model's 4 entities (individu, menage, famille, foyer_fiscal), when a population dataset is loaded with membership columns (`{group_entity_key}_id` and `{group_entity_key}_role` on the person entity table), then `_population_to_entity_dict()` produces a valid entity dict with all entity relationships preserved and passable to `SimulationBuilder.build_from_entities()`. Membership columns are excluded from period-wrapped variable values.

2. **AC-2: Group membership assignment** — Given a population with membership columns for all 3 group entities, when built via `SimulationBuilder.build_from_entities()`, then entity group memberships are correctly assigned — e.g., a married couple shares one `foyer_fiscal` with both persons as `declarants`, one `menage` with one `personne_de_reference` and one `conjoint`, and one `famille` with both as `parents`.

3. **AC-3: Missing relationship validation** — Given a population dataset where membership columns are partially present (e.g., `famille_id` exists but `foyer_fiscal_id` is missing, or `famille_id` exists without `famille_role`), when loaded, then validation fails with a clear `ApiMappingError` identifying the missing relationship columns and listing what is required.

4. **AC-4: Invalid role validation** — Given a population dataset with a role value that is not valid for the target entity (e.g., `menage_role="invalid_role"`), when validated, then an `ApiMappingError` is raised listing the invalid role value, the entity it belongs to, and the valid role values queried from the TBS.

5. **AC-5: Null membership value rejection** — Given a population dataset with a null (None/NaN) value in any membership column (`_id` or `_role`), when validated, then an `ApiMappingError` is raised identifying the column name, the row index, and the expected non-null value type.

6. **AC-6: Backward compatibility** — Given a population dataset WITHOUT membership columns (the existing common case — a person table with only variable columns), when `compute()` is called, then behavior is identical to the pre-change implementation — no regression. OpenFisca's auto-creation of group entities for single-person populations continues to work.

7. **AC-7: Group entity input variables** — Given a PopulationData with both membership columns on the person table AND separate group entity tables containing group-level input variables (e.g., a `menage` table with a `loyer` column), when `_population_to_entity_dict()` processes the data, then the group entity instances include both the role assignments (from membership columns) AND the period-wrapped variable values (from the group entity table).

## Tasks / Subtasks

- [ ] Task 1: Implement `_detect_membership_columns()` method (AC: #1, #3, #6)
  - [ ] 1.1 Add method to `OpenFiscaApiAdapter` that queries TBS for group entities (`entity.is_person == False`) and checks the person entity table for `{entity.key}_id` and `{entity.key}_role` columns
  - [ ] 1.2 Return a `dict[str, tuple[str, str]]` mapping group entity key to `(id_column_name, role_column_name)` — e.g., `{"famille": ("famille_id", "famille_role"), "foyer_fiscal": ("foyer_fiscal_id", "foyer_fiscal_role"), "menage": ("menage_id", "menage_role")}`. Return empty dict if NO membership columns are detected (→ backward-compatible old behavior)
  - [ ] 1.3 **All-or-nothing detection**: if ANY `{entity_key}_id` column is found on the person table, then ALL group entities must have complete `_id` AND `_role` column pairs. Missing pairs raise `ApiMappingError` with summary `"Incomplete entity membership columns"`, listing which columns are present and which are missing
  - [ ] 1.4 **Paired column check**: if `{entity_key}_id` exists but `{entity_key}_role` is missing (or vice versa), raise `ApiMappingError` with summary `"Unpaired membership column"` — both `_id` and `_role` are required for each group entity
  - [ ] 1.5 Unit tests with mock TBS: detect all 3 group entities, detect none (backward compat), detect partial (error), detect unpaired (error)

- [ ] Task 2: Implement `_resolve_valid_role_keys()` method (AC: #4)
  - [ ] 2.1 Add method that queries TBS group entity roles and builds a mapping: `dict[str, frozenset[str]]` — entity key → set of valid role keys (using `role.plural or role.key` to match what `build_from_entities()` expects)
  - [ ] 2.2 For OpenFisca-France, this produces: `{"famille": {"parents", "enfants"}, "foyer_fiscal": {"declarants", "personnes_a_charge"}, "menage": {"personne_de_reference", "conjoint", "enfants", "autres"}}`
  - [ ] 2.3 Unit tests with mock TBS entities and roles: verify correct role key resolution for each entity

- [ ] Task 3: Implement `_validate_entity_relationships()` method (AC: #3, #4, #5)
  - [ ] 3.1 Add validation method that takes the person entity table (`pa.Table`) and the detected membership columns dict, plus the valid role keys dict
  - [ ] 3.2 **Null check** (AC-5): for each membership column (`_id` and `_role`), check for null values. If found, raise `ApiMappingError` with summary `"Null value in membership column"`, the column name, and the first row index containing null. Use `pa.compute.is_null()` for efficient PyArrow null detection
  - [ ] 3.3 **Role validation** (AC-4): for each `{entity_key}_role` column, check that all values are in the valid role set for that entity. If invalid values found, raise `ApiMappingError` with summary `"Invalid role value"`, the actual value, the entity key, and the sorted list of valid role values
  - [ ] 3.4 Unit tests: null in `_id` column → error, null in `_role` column → error, invalid role value → error, all valid → passes silently

- [ ] Task 4: Refactor `_population_to_entity_dict()` for 4-entity format (AC: #1, #2, #6, #7)
  - [ ] 4.1 At the start of the method, call `_detect_membership_columns()` to determine format mode. If empty dict returned → execute existing code path unchanged (AC-6 backward compat)
  - [ ] 4.2 If membership columns detected, call `_resolve_valid_role_keys()` then `_validate_entity_relationships()`
  - [ ] 4.3 **Separate membership columns from variable columns**: build a set of all membership column names (all `_id` and `_role` columns). When iterating person table columns for period-wrapping, skip membership columns
  - [ ] 4.4 **Build person instances FROM PERSON TABLE ONLY**: iterate the person entity table (identified by finding the `population.tables` key matching `person_entity.key` or `person_entity.plural`) — NOT all tables in `population.tables`. Exclude membership columns from period-wrapping. The instance ID prefix is the original key used in `population.tables` (e.g. `"individu"` → `"individu_0"`, `"individu_1"`; `"individus"` → `"individus_0"`, `"individus_1"`). ⚠️ In 4-entity mode, the original all-tables loop is **replaced** by this step (person table) combined with Tasks 4.5 (group membership from membership columns) and 4.6 (group variables from group entity tables). Do NOT run the old all-tables loop and then also run 4-entity logic — this would double-write group entity entries.
  - [ ] 4.5 **Build group entity instances from membership columns**: for each group entity:
      - Read `{entity_key}_id` and `{entity_key}_role` columns from person table
      - Group person instance IDs by group ID
      - Within each group, sub-group person IDs by role key
      - Produce: `{"famille_0": {"parents": [f"{person_table_key}_0", f"{person_table_key}_1"]}}` — where `person_table_key` is the original key from `population.tables` (e.g. `"individu"` or `"individus"`). Person instance IDs MUST use the same prefix as Task 4.4.
      - Group instance IDs follow format `f"{entity_key}_{group_id_value}"` — e.g., if `famille_id` column has value `0`, instance ID is `"famille_0"`
  - [ ] 4.6 **Merge group entity table variables** (AC-7): if PopulationData contains a group entity table (e.g., `"menage"` or `"menages"` key in `population.tables`), iterate its columns and merge period-wrapped variable values into the corresponding group entity instances. Match group table row index to group instance by sorted order of distinct group IDs from the person table's `_id` column. ⚠️ Raise `ApiMappingError` if the group entity table row count doesn't match the number of distinct group IDs. ⚠️ **POSITIONAL MATCHING**: row 0 of the group entity table maps to the smallest distinct group ID, row 1 to the second-smallest, etc. This requires the group entity table rows to be ordered by ascending `{entity_key}_id` value — no automatic reordering is performed. If rows are in a different order, values will be silently misassigned to the wrong group instances. Unit test to add: non-contiguous IDs `[0, 2]` → group table row 0 maps to `groupe_0`, row 1 maps to `groupe_2` (not reversed).
  - [ ] 4.7 **Store result keyed by entity plural** (existing behavior): use `key_to_plural` mapping to normalize keys
  - [ ] 4.8 **Policy parameter injection** (existing behavior): unchanged — inject on person entity only
  - [ ] 4.9 Unit tests: married couple (2 persons, 1 famille, 1 foyer, 1 menage), family with child (2 parents + 1 enfant, 1 famille, 2 foyers, 1 menage), backward compat (no membership columns)

- [ ] Task 5: Wire validation into `compute()` (AC: #1, #3, #4, #5)
  - [ ] 5.1 The `_population_to_entity_dict()` method is already called inside `_build_simulation()`. The membership detection and validation happen inside `_population_to_entity_dict()` itself (not in `compute()` directly), so the validation is naturally fail-fast — it runs before `SimulationBuilder.build_from_entities()` is called
  - [ ] 5.2 No changes to `compute()` call order — `_population_to_entity_dict()` is called inside `_build_simulation()` which is already after all output variable/entity/periodicity validation
  - [ ] 5.3 Unit tests: verify validation errors fire before simulation builder is called

- [ ] Task 6: Integration tests with real OpenFisca-France (AC: #1, #2, #7)
  - [ ] 6.1 Test: **married couple** — 2 persons, 1 famille (both as `parents`), 1 foyer_fiscal (both as `declarants`), 1 menage (`personne_de_reference` + `conjoint`). Use membership columns on person table. Verify `compute()` produces correct results matching existing hand-built integration tests (same `irpp` values as `TestOpenFiscaFranceReferenceCases.test_couple_salaire_imposable_30k_25k`). Use `ABSOLUTE_ERROR_MARGIN = 0.5` as a class attribute on the new integration test class, consistent with the existing reference test suite.
  - [ ] 6.2 Test: **single person with membership columns** — 1 person, 1 famille (`parents`), 1 foyer_fiscal (`declarants`), 1 menage (`personne_de_reference`). Verify results match single-person tests without membership columns
  - [ ] 6.3 Test: **two independent households** — 2 persons each in separate famille/foyer_fiscal/menage. Verify entity instance counts match (2 familles, 2 foyers, 2 menages)
  - [ ] 6.4 Test: **group entity input variables** — menage table with `loyer` column. Verify the value appears in the entity dict and is passable to `build_from_entities()`
  - [ ] 6.5 Test: **backward compatibility** — existing `single_person_population` fixture (no membership columns) still works identically via `adapter.compute()`
  - [ ] 6.6 Mark all with `@pytest.mark.integration`

- [ ] Task 7: Verify backward compatibility (AC: #6)
  - [ ] 7.1 Run ALL existing unit tests in `test_openfisca_api_adapter.py` — ensure all pass unchanged
  - [ ] 7.2 Run ALL existing integration tests in `test_openfisca_integration.py` — ensure all pass unchanged
  - [ ] 7.3 Verify `MockAdapter` still produces valid `ComputationResult` (no new required fields or format assumptions)
  - [ ] 7.4 Verify `ComputationStep` in orchestrator still works (`result.output_fields.num_rows`)
  - [ ] 7.5 Run `uv run pytest tests/orchestrator/` to confirm no orchestrator regressions

- [ ] Task 8: Run quality gates (all ACs)
  - [ ] 8.1 `uv run ruff check src/ tests/`
  - [ ] 8.2 `uv run mypy src/`
  - [ ] 8.3 `uv run pytest tests/computation/ tests/orchestrator/`

## Dev Notes

### Prerequisites — Story Sequencing

⚠️ **Story 9.3 (Add Variable Periodicity Handling) must be merged before starting this story.** Both stories modify `src/reformlab/computation/openfisca_api_adapter.py`. Story 9.3 changes `compute()`, `_extract_results_by_entity()`, `_calculate_variable()`, and `_resolve_variable_periodicities()`. Story 9.4 adds three new private methods and refactors `_population_to_entity_dict()` — method-level overlap is limited, but file-level merge conflicts are likely.

If concurrent development is unavoidable: develop Story 9.4 on a branch that explicitly tracks Story 9.3's branch and rebase before raising a PR. After Story 9.3 merges, `_population_to_entity_dict()` is unchanged — the methods added by Story 9.4 are fully additive.

### Architecture Constraints

- **Adapter isolation is absolute**: Only `computation/openfisca_adapter.py` and `openfisca_api_adapter.py` may import OpenFisca. All OpenFisca imports must be lazy (inside methods, not at module level).
- **Frozen dataclasses**: `PopulationData` and `ComputationResult` are `@dataclass(frozen=True)`. NO new fields are added to either in this story — the 4-entity format is expressed purely through column naming conventions in existing `tables: dict[str, pa.Table]`.
- **Protocol compatibility**: `ComputationAdapter` protocol (`period: int`) is unchanged. The membership handling is internal to `OpenFiscaApiAdapter`.
- **PyArrow is canonical**: All data containers use `pa.Table`. No pandas. Use `pa.compute` for null checks.
- **`from __future__ import annotations`** at top of every file.
- **No bare `Exception` or `ValueError`**: Use subsystem-specific exceptions (`ApiMappingError`).
- **Subsystem-specific exceptions**: Reuse existing `ApiMappingError` from `reformlab.computation.exceptions`. No new exception types needed.

### PopulationData 4-Entity Format — Complete Specification

**The format uses membership columns on the person entity table to express entity relationships.** No changes to the `PopulationData` type itself.

#### Column Naming Convention

For each group entity in the TBS (identified by `entity.is_person == False`):
- **`{entity.key}_id`** column (int64 or utf8): foreign key identifying which group instance this person belongs to
- **`{entity.key}_role`** column (utf8): the role key this person has in the group (must match `role.plural or role.key` from the TBS)

For OpenFisca-France, the 6 required membership columns are:

| Column Name | Type | Description | Example Values |
|---|---|---|---|
| `famille_id` | int64 | Family group instance ID | `0`, `0`, `1` |
| `famille_role` | utf8 | Role in family | `"parents"`, `"parents"`, `"parents"` |
| `foyer_fiscal_id` | int64 | Tax household instance ID | `0`, `0`, `1` |
| `foyer_fiscal_role` | utf8 | Role in tax household | `"declarants"`, `"declarants"`, `"declarants"` |
| `menage_id` | int64 | Dwelling instance ID | `0`, `0`, `1` |
| `menage_role` | utf8 | Role in dwelling | `"personne_de_reference"`, `"conjoint"`, `"personne_de_reference"` |

#### Example: Married Couple PopulationData

```python
PopulationData(
    tables={
        "individu": pa.table({
            # Variable columns (period-wrapped by adapter)
            "salaire_de_base": pa.array([30000.0, 0.0]),
            "age": pa.array([30, 28]),
            # Membership columns (NOT period-wrapped — used for entity dict construction)
            "famille_id": pa.array([0, 0]),
            "famille_role": pa.array(["parents", "parents"]),
            "foyer_fiscal_id": pa.array([0, 0]),
            "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
            "menage_id": pa.array([0, 0]),
            "menage_role": pa.array(["personne_de_reference", "conjoint"]),
        }),
    },
)
```

**Produces entity dict:**

```python
{
    "individus": {
        "individu_0": {"salaire_de_base": {"2024": 30000.0}, "age": {"2024": 30}},
        "individu_1": {"salaire_de_base": {"2024": 0.0}, "age": {"2024": 28}},
    },
    "familles": {
        "famille_0": {"parents": ["individu_0", "individu_1"]},
    },
    "foyers_fiscaux": {
        "foyer_fiscal_0": {"declarants": ["individu_0", "individu_1"]},
    },
    "menages": {
        "menage_0": {
            "personne_de_reference": ["individu_0"],
            "conjoint": ["individu_1"],
        },
    },
}
```

#### Example: Family with Child

```python
PopulationData(
    tables={
        "individu": pa.table({
            "salaire_de_base": pa.array([40000.0, 20000.0, 0.0]),
            "age": pa.array([45, 42, 12]),
            "famille_id": pa.array([0, 0, 0]),
            "famille_role": pa.array(["parents", "parents", "enfants"]),
            "foyer_fiscal_id": pa.array([0, 0, 0]),
            "foyer_fiscal_role": pa.array(["declarants", "declarants", "personnes_a_charge"]),
            "menage_id": pa.array([0, 0, 0]),
            "menage_role": pa.array(["personne_de_reference", "conjoint", "enfants"]),
        }),
    },
)
```

#### Example: With Group Entity Input Variables (AC-7)

```python
PopulationData(
    tables={
        "individu": pa.table({
            "salaire_de_base": pa.array([30000.0, 0.0]),
            "age": pa.array([30, 28]),
            "famille_id": pa.array([0, 0]),
            "famille_role": pa.array(["parents", "parents"]),
            "foyer_fiscal_id": pa.array([0, 0]),
            "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
            "menage_id": pa.array([0, 0]),
            "menage_role": pa.array(["personne_de_reference", "conjoint"]),
        }),
        # Optional: group entity table with group-level input variables
        "menage": pa.table({
            "loyer": pa.array([800.0]),  # Monthly rent
        }),
    },
)
```

**Produces entity dict with merged group variables:**

```python
{
    ...
    "menages": {
        "menage_0": {
            "personne_de_reference": ["individu_0"],
            "conjoint": ["individu_1"],
            "loyer": {"2024": 800.0},  # Period-wrapped from group entity table
        },
    },
}
```

### OpenFisca Role System — Reference from TBS Source

**Critical: `build_from_entities()` uses `role.plural or role.key`** as the dict key for role assignment. This was confirmed from `openfisca_core/simulations/simulation_builder.py` line ~517:

```python
role_by_plural = {role.plural or role.key: role for role in entity.roles}
```

**OpenFisca-France role definitions** (from `.venv/.../openfisca_france/entities.py`):

| Entity | Role | `role.key` | `role.plural` | Dict key (`plural or key`) | `role.max` |
|---|---|---|---|---|---|
| famille | Parent | `"parent"` | `"parents"` | **`"parents"`** | 2 |
| famille | Child | `"enfant"` | `"enfants"` | **`"enfants"`** | None |
| foyer_fiscal | Declarant | `"declarant"` | `"declarants"` | **`"declarants"`** | 2 |
| foyer_fiscal | Dependent | `"personne_a_charge"` | `"personnes_a_charge"` | **`"personnes_a_charge"`** | None |
| menage | Ref person | `"personne_de_reference"` | None | **`"personne_de_reference"`** | 1 |
| menage | Spouse | `"conjoint"` | None | **`"conjoint"`** | 1 |
| menage | Child | `"enfant"` | `"enfants"` | **`"enfants"`** | None |
| menage | Other | `"autre"` | `"autres"` | **`"autres"`** | None |

**⚠️ Note:** `role.plural` is `None` for `personne_de_reference` and `conjoint` in menage. The adapter must use `role.plural or role.key` to compute valid role keys — not `role.plural` alone (which would be `None`).

### Querying TBS for Role Information

```python
# In _resolve_valid_role_keys():
valid_roles: dict[str, frozenset[str]] = {}
for entity in tbs.entities:
    if getattr(entity, "is_person", False):
        continue
    role_keys: set[str] = set()
    for role in entity.roles:
        # role.plural is a property that returns None if not defined
        plural = getattr(role, "plural", None)
        key = getattr(role, "key", None)
        role_dict_key = plural or key
        if role_dict_key:
            role_keys.add(role_dict_key)
    valid_roles[entity.key] = frozenset(role_keys)
```

**⚠️ Accessing `entity.roles`:** In OpenFisca-Core, `entity.roles` is available on GroupEntity objects. The Role objects have `.key` and `.plural` as properties. Always access with `getattr()` for defensive coding — some attributes may be `None`.

### Group Instance ID Generation

**Group instance IDs are derived from the `_id` column values:**

```python
# For famille_id column with values [0, 0, 1]:
# → Group IDs: {0, 1}
# → Instance IDs: "famille_0", "famille_1"

# Person instance ID: f"{person_entity_key}_{row_index}"
# → "individu_0", "individu_1", "individu_2"

# Group instance ID: f"{group_entity_key}_{group_id_value}"
# → "famille_0", "foyer_fiscal_0", "menage_0"
```

**The person instance ID is the key used in the role assignment lists.** The person instance IDs must match between the person entity dict and the group entity role arrays. Currently, `_population_to_entity_dict()` uses `f"{entity_key}_{i}"` where `entity_key` comes from the PopulationData table key (e.g., `"individu"`) and `i` is the row index. This convention must be preserved.

**⚠️ Critical:** the prefix is the original `population.tables` key — not necessarily `person_entity.key`. If the caller passes `"individus"` (plural) as the table key, all person instance IDs become `"individus_0"`, `"individus_1"`, etc. The group entity role lists must use these same IDs. Capture this key early (`person_table_key`) and use it consistently for both person instances (Task 4.4) and role assignment lists (Task 4.5).

### Algorithm for Refactored `_population_to_entity_dict()`

```
1. Build key_to_plural mapping: {entity.key: entity.plural for entity in tbs.entities}
2. Identify person entity: person_entity = next(e for e in tbs.entities if e.is_person)
2b. Find person_table_key: the key in population.tables matching person_entity.key
    OR person_entity.plural (user may pass either singular or plural).
    If no matching key found → no person entity table present; fall through to step 4
    (backward-compatible: membership columns require a person entity table).
3. person_table = population.tables[person_table_key]
   membership_cols = _detect_membership_columns(person_table, tbs)
4. IF empty dict returned → execute existing all-tables loop (current lines 538–569
   of _population_to_entity_dict()): iterate ALL population.tables, period-wrap every
   column, store keyed by entity plural. Return immediately.
5. IF membership columns detected (4-entity mode):
   ⚠️ The original all-tables iteration loop is REPLACED by steps 5a–5g.
   Do NOT run the old loop before/after — this would double-write group entity
   entries and corrupt the result dict.

   a. valid_roles = _resolve_valid_role_keys(tbs)
   b. _validate_entity_relationships(person_table, membership_cols, valid_roles)
   c. Build membership_col_names: set of all _id and _role column names
      (these are excluded from period-wrapping in step 5d)
   d. Build person instances FROM PERSON TABLE ONLY:
      - Use person_table_key as the instance ID prefix
        (e.g. "individu" → "individu_0"; "individus" → "individus_0")
      - Skip columns in membership_col_names
      - result[person_entity.plural][f"{person_table_key}_{i}"] =
          {col: {period_str: val} for col not in membership_col_names}
   e. For each group_entity_key in membership_cols:
      i.   id_col = person_table.column(f"{group_entity_key}_id")
           role_col = person_table.column(f"{group_entity_key}_role")
      ii.  sorted_group_ids = sorted(pa.compute.unique(id_col).to_pylist())
      iii. For each group_id in sorted_group_ids:
           - Collect row indices where id_col == group_id
           - Build role_dict: {role_key: [f"{person_table_key}_{i}" for each index]}
      iv.  group_plural = key_to_plural[group_entity_key]
           result[group_plural][f"{group_entity_key}_{group_id}"] = role_dict
   f. Merge group entity table variables (if present):
      i.   For each group entity key with a table in population.tables
      ii.  sorted_group_ids from person table _id column (same order as step 5e)
      iii. Raise ApiMappingError if group_table.num_rows != len(sorted_group_ids)
      iv.  ⚠️ POSITIONAL MATCH: row i of group table → sorted_group_ids[i]
           Requires group table rows to be ordered by ascending {entity_key}_id value
      v.   For each (i, group_id): period-wrap group_table row i columns and
           merge into result[group_plural][f"{group_entity_key}_{group_id}"]
   g. Inject policy parameters into person entity instances (unchanged)
6. Return result
```

### Backward Compatibility Strategy

This story is **internal to `_population_to_entity_dict()`** — no external interface changes:

1. **`PopulationData` type is unchanged** — no new fields, no type changes.
2. **`ComputationResult` is unchanged** — the output format doesn't change.
3. **`ComputationAdapter` protocol is unchanged** — `compute(population, policy, period)` signature unchanged.
4. **`MockAdapter` is unaffected** — it never calls `_population_to_entity_dict()`.
5. **Detection is opt-in by column presence** — no membership columns = old behavior. ALL existing tests use PopulationData without membership columns, so they remain unaffected.
6. **`compute()` call order is unchanged** — `_population_to_entity_dict()` is called inside `_build_simulation()` at the same position in the pipeline.

### Mock TBS Extension for Unit Tests

Extend `_make_mock_tbs_with_entities()` in the test file to support roles:

```python
def _make_mock_tbs_with_entities(
    entity_keys: tuple[str, ...] = ("individu", "foyer_fiscal", "menage"),
    entity_plurals: dict[str, str] | None = None,
    variable_entities: dict[str, str] | None = None,
    variable_periodicities: dict[str, str] | None = None,
    person_entity: str = "individu",
    entity_roles: dict[str, list[dict[str, str | None]]] | None = None,
    # ↑ NEW: e.g., {"famille": [{"key": "parent", "plural": "parents"}, ...]}
) -> MagicMock:
```

Each role entry should be a `SimpleNamespace(key=..., plural=...)` to match the TBS Role interface.

**Example:**
```python
mock_tbs = _make_mock_tbs_with_entities(
    entity_keys=("individu", "famille", "foyer_fiscal", "menage"),
    entity_roles={
        "famille": [
            {"key": "parent", "plural": "parents"},
            {"key": "enfant", "plural": "enfants"},
        ],
        "foyer_fiscal": [
            {"key": "declarant", "plural": "declarants"},
            {"key": "personne_a_charge", "plural": "personnes_a_charge"},
        ],
        "menage": [
            {"key": "personne_de_reference", "plural": None},
            {"key": "conjoint", "plural": None},
            {"key": "enfant", "plural": "enfants"},
            {"key": "autre", "plural": "autres"},
        ],
    },
)
```

**⚠️ Existing mock entities do NOT have `roles` attribute.** The mock must add `entity.roles = [SimpleNamespace(key=..., plural=...) for ...]` for group entities and `entity.roles = []` (or omit) for the person entity. The `_detect_membership_columns()` method uses `entity.is_person` to skip the person entity, so it won't try to access `roles` on it.

### Files to Modify

| File | Change |
|------|--------|
| `src/reformlab/computation/openfisca_api_adapter.py` | Add `_detect_membership_columns()`, `_resolve_valid_role_keys()`, `_validate_entity_relationships()`. Refactor `_population_to_entity_dict()` to handle 4-entity format with membership columns |
| `tests/computation/test_openfisca_api_adapter.py` | Extend `_make_mock_tbs_with_entities()` with `entity_roles` parameter. Add new test classes: `TestDetectMembershipColumns`, `TestResolveValidRoleKeys`, `TestValidateEntityRelationships`, `TestPopulationToEntityDict4Entity`. Add marriage/family fixtures |
| `tests/computation/test_openfisca_integration.py` | Add integration tests for 4-entity format: married couple via membership columns, family with child, backward compat, group entity variables |

### Files to Verify (No Changes Expected)

| File | Why |
|------|-----|
| `src/reformlab/computation/types.py` | `PopulationData` unchanged — no new fields |
| `src/reformlab/computation/types.pyi` | Type stub unchanged |
| `src/reformlab/computation/adapter.py` | Protocol unchanged |
| `src/reformlab/computation/mock_adapter.py` | Unaffected — doesn't call `_population_to_entity_dict()` |
| `src/reformlab/computation/exceptions.py` | Reuse existing `ApiMappingError` — no new exception types |
| `src/reformlab/orchestrator/computation_step.py` | Passes `population` to adapter unchanged |
| `src/reformlab/orchestrator/panel.py` | Accesses `comp_result.output_fields` — unchanged |

### Integration Test Reference Data

**Married couple via membership columns (should match existing hand-built test):**

```python
# This PopulationData with membership columns:
population = PopulationData(
    tables={
        "individu": pa.table({
            "salaire_imposable": pa.array([30000.0, 25000.0]),
            "famille_id": pa.array([0, 0]),
            "famille_role": pa.array(["parents", "parents"]),
            "foyer_fiscal_id": pa.array([0, 0]),
            "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
            "menage_id": pa.array([0, 0]),
            "menage_role": pa.array(["personne_de_reference", "conjoint"]),
        }),
    },
)

# Should produce the SAME irpp as the existing reference case:
# test_couple_salaire_imposable_30k_25k → irpp ≈ -2765.0
```

**Two independent households:**

```python
population = PopulationData(
    tables={
        "individu": pa.table({
            "salaire_de_base": pa.array([30000.0, 50000.0]),
            "age": pa.array([30, 45]),
            "famille_id": pa.array([0, 1]),
            "famille_role": pa.array(["parents", "parents"]),
            "foyer_fiscal_id": pa.array([0, 1]),
            "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
            "menage_id": pa.array([0, 1]),
            "menage_role": pa.array(["personne_de_reference", "personne_de_reference"]),
        }),
    },
)
# Each person in their own groupe → 2 familles, 2 foyers, 2 menages
```

### What This Story Does NOT Cover

- **Person-level broadcasting** of group entity values (e.g., distributing `irpp` from foyer_fiscal to its members) — separate follow-up
- **Input variable period assignment for non-yearly variables** — e.g., `age` may need `"2024-01"` period format instead of `"2024"`. Currently all values are wrapped with the yearly period string. This is a known limitation carried over from the existing implementation
- **Modifying `PopulationData` type** — the 4-entity format is expressed purely through column naming conventions, no type changes
- **Modifying `MockAdapter`** — it never calls OpenFisca and doesn't need membership logic
- **Sub-yearly period support** — `ComputationAdapter.compute(period: int)` remains yearly only
- **`calculate_divide()` support** — not needed for yearly periods
- **Automatic population generation in 4-entity format** — `src/reformlab/data/synthetic.py` generates household-level data, not the 4-entity person-level format. Converting synthetic populations to 4-entity format is a separate concern
- **Country-package-agnostic entity discovery** — this story targets OpenFisca-France specifically. Other country packages may have different entity structures

### Edge Cases to Handle

1. **Group ID values are not contiguous** — e.g., `famille_id = [0, 2, 2]` (no famille 1). This is valid — group IDs are arbitrary identifiers, not indices. Instance IDs: `"famille_0"`, `"famille_2"`.

2. **String group IDs** — `famille_id` column could be utf8 instead of int64. The instance ID format becomes `f"{entity_key}_{str(group_id)}"`. Support both int64 and utf8 column types.

3. **Extra rows in group entity table** — if `population.tables["menage"]` has more rows than the number of distinct `menage_id` values in the person table, the extra rows are unmatched. Raise `ApiMappingError` with summary `"Group entity table row count mismatch"`, including the table row count and the number of distinct group IDs found in the person table. (A group ID appearing in no person's `_id` column cannot occur by construction — groups are discovered from the person table's `_id` column, not from a separate registry. The mismatch only occurs when the caller provides a group entity table with more rows than the person table's distinct IDs.)

4. **Single person with membership columns** — valid. One person assigned to one group per entity. Should produce the same result as without membership columns.

5. **Person table key is plural** — e.g., `"individus"` instead of `"individu"`. The existing key normalization logic handles this.

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

- [Source: `_bmad-output/implementation-artifacts/spike-findings-8-1-openfisca-integration.md` — Follow-up #4: "Update PopulationData format for OpenFisca-France", line 106]
- [Source: `_bmad-output/implementation-artifacts/spike-findings-8-1-openfisca-integration.md` — Gap 2: "Multi-entity output arrays have different lengths", lines 45-61]
- [Source: `_bmad-output/implementation-artifacts/9-2-handle-multi-entity-output-arrays.md` — "What This Story Does NOT Cover": "PopulationData 4-entity format — that is Story 9.4", line 237]
- [Source: `_bmad-output/implementation-artifacts/9-3-add-variable-periodicity-handling.md` — "What This Story Does NOT Cover": "PopulationData 4-entity format — That is Story 9.4", near end of Dev Notes]
- [Source: `src/reformlab/computation/openfisca_api_adapter.py` — `_population_to_entity_dict()` method, lines 499-569]
- [Source: `src/reformlab/computation/types.py` — `PopulationData` dataclass, lines 11-26]
- [Source: `src/reformlab/computation/exceptions.py` — `ApiMappingError` structured error pattern]
- [Source: `.venv/.../openfisca_france/entities.py` — Entity and role definitions for individu, famille, foyer_fiscal, menage]
- [Source: `.venv/.../openfisca_core/simulations/simulation_builder.py` — `build_from_entities()` role parsing: `role_by_plural = {role.plural or role.key: role}`, line ~517]
- [Source: `.venv/.../openfisca_core/entities/role.py` — `Role` class with `.key` and `.plural` properties]
- [Source: `tests/computation/test_openfisca_integration.py` — `_build_entities_dict()` helper, line 75; `_build_simulation()` helper, line 88; married couple entity dict patterns, lines 286-298]
- [Source: `_bmad-output/planning-artifacts/epics.md` — Epic 9, Story 9.4 acceptance criteria]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (via create-story workflow)

### Debug Log References

### Completion Notes List

- Code review synthesis 2026-03-01: 6 issues applied from adversarial review (Reviewer B confirmed; Reviewer A issues were largely false positives based on truncated file views in the review context).
  - CRITICAL FIX: Replaced O(n×g) nested loop in Step 5e with single-pass O(n) approach. Converts both id/role columns to Python lists once, then groups in one enumerated zip iteration. For 250k persons × 100k groups, this reduces from ~25 billion ops to ~250k ops.
  - HIGH FIX: Replaced two load-bearing `assert` statements (lines 838, 867) with explicit `ApiMappingError` raises. `assert` is stripped by Python's `-O` flag; the second assert had `result[None] = person_dict` as its failure mode — a `None` dict key that silently corrupts the entity dict passed to `build_from_entities()`.
  - HIGH FIX: Pre-amortized column extraction in Step 5d — replaced O(n×c) scalar-boxing loop with a dict-comprehension that calls `.to_pylist()` once per column outside the row loop.
  - HIGH FIX: Role validation now checks `pa.compute.unique(role_array)` (≤4 distinct values) instead of the full population array (`to_pylist()` of n rows). Reduces O(n) to O(u) where u ≤ 4.
  - MEDIUM FIX: Null-index detection now uses `pa.compute.filter()` + single `.as_py()` call instead of a Python for-loop with per-element `.as_py()` boxings. Only runs on error path, but consistency matters.
  - LOW FIX: Added `logger.warning()` to Step 5f positional group-table merge to make the ordering assumption visible in structured logs. Silent data corruption on unsorted group tables is now observable.
  - LOW FIX: Updated `Status: ready-for-dev` → `Status: done` (third recurrence of antipattern from Stories 9.2 and 9.3).
- Ultimate context engine analysis completed — comprehensive developer guide created
- All 3 acceptance criteria from epics file expanded to 7 ACs covering: format definition, group membership, missing relationship validation, invalid role validation, null value rejection, backward compatibility, and group entity input variables
- Spike 8-1 findings fully integrated: follow-up #4 (4-entity format) is the direct motivation; Gap 2 (multi-entity arrays) is the predecessor context
- OpenFisca entity role system documented from source code inspection:
  - `Role` has `.key` and `.plural` properties; `.plural` can be `None` (e.g., menage `personne_de_reference`)
  - `build_from_entities()` uses `role.plural or role.key` as dict key (confirmed from `simulation_builder.py` line ~517)
  - Complete role table for all 4 OpenFisca-France entities with 8 roles documented
- Column naming convention designed: `{entity_key}_id` (int64/utf8) + `{entity_key}_role` (utf8) on person table
  - All-or-nothing detection: ANY membership column triggers full 4-entity format requirement
  - Paired column check: both `_id` and `_role` required per entity
- Backward compatibility strategy: purely internal changes to `_population_to_entity_dict()`, auto-detected by column presence
- Three complete example PopulationData formats documented: married couple, family with child, group entity variables
- Algorithm pseudocode provided for refactored `_population_to_entity_dict()`
- Mock TBS extension pattern documented with `entity_roles` parameter and SimpleNamespace role objects
- Edge cases documented: non-contiguous group IDs, string group IDs, empty groups, single person with membership columns
- Integration test reference data with expected values (married couple irpp ≈ -2765.0 cross-validated against existing `test_couple_salaire_imposable_30k_25k`)
- Story 9.2 and 9.3 predecessor analysis: confirms explicit exclusion of 4-entity format from both stories

### File List

- `src/reformlab/computation/openfisca_api_adapter.py` — modify (add `_detect_membership_columns()`, `_resolve_valid_role_keys()`, `_validate_entity_relationships()`, refactor `_population_to_entity_dict()`)
- `tests/computation/test_openfisca_api_adapter.py` — modify (extend mock TBS with roles, add 4-entity format unit tests)
- `tests/computation/test_openfisca_integration.py` — modify (add 4-entity format integration tests with membership columns)
