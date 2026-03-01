<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 9 -->
<!-- Story: 4 -->
<!-- Phase: validate-story-synthesis -->
<!-- Timestamp: 20260301T212059Z -->
<compiled-workflow>
<mission><![CDATA[

Master Synthesis: Story 9.4

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
<file id="bc34e66e" path="_bmad-output/implementation-artifacts/9-4-define-population-data-4-entity-format.md" label="STORY FILE"><![CDATA[

# Story 9.4: Define Population Data 4-Entity Format

Status: ready-for-dev

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
  - [ ] 4.4 **Build person instances**: same as current logic but excluding membership columns — produce `{"individu_0": {"salaire_de_base": {"2024": 30000.0}}, ...}`
  - [ ] 4.5 **Build group entity instances from membership columns**: for each group entity:
      - Read `{entity_key}_id` and `{entity_key}_role` columns from person table
      - Group person instance IDs by group ID
      - Within each group, sub-group person IDs by role key
      - Produce: `{"famille_0": {"parents": ["individu_0", "individu_1"]}, ...}`
      - Group instance IDs follow format `f"{entity_key}_{group_id_value}"` — e.g., if `famille_id` column has value `0`, instance ID is `"famille_0"`
  - [ ] 4.6 **Merge group entity table variables** (AC-7): if PopulationData contains a group entity table (e.g., `"menage"` or `"menages"` key in `population.tables`), iterate its columns and merge period-wrapped variable values into the corresponding group entity instances. Match group table row index to group instance by sorted order of distinct group IDs from the person table's `_id` column. ⚠️ Raise `ApiMappingError` if the group entity table row count doesn't match the number of distinct group IDs
  - [ ] 4.7 **Store result keyed by entity plural** (existing behavior): use `key_to_plural` mapping to normalize keys
  - [ ] 4.8 **Policy parameter injection** (existing behavior): unchanged — inject on person entity only
  - [ ] 4.9 Unit tests: married couple (2 persons, 1 famille, 1 foyer, 1 menage), family with child (2 parents + 1 enfant, 1 famille, 2 foyers, 1 menage), backward compat (no membership columns)

- [ ] Task 5: Wire validation into `compute()` (AC: #1, #3, #4, #5)
  - [ ] 5.1 The `_population_to_entity_dict()` method is already called inside `_build_simulation()`. The membership detection and validation happen inside `_population_to_entity_dict()` itself (not in `compute()` directly), so the validation is naturally fail-fast — it runs before `SimulationBuilder.build_from_entities()` is called
  - [ ] 5.2 No changes to `compute()` call order — `_population_to_entity_dict()` is called inside `_build_simulation()` which is already after all output variable/entity/periodicity validation
  - [ ] 5.3 Unit tests: verify validation errors fire before simulation builder is called

- [ ] Task 6: Integration tests with real OpenFisca-France (AC: #1, #2, #7)
  - [ ] 6.1 Test: **married couple** — 2 persons, 1 famille (both as `parents`), 1 foyer_fiscal (both as `declarants`), 1 menage (`personne_de_reference` + `conjoint`). Use membership columns on person table. Verify `compute()` produces correct results matching existing hand-built integration tests (same `irpp` values as `TestOpenFiscaFranceReferenceCases.test_couple_salaire_imposable_30k_25k`)
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

### Algorithm for Refactored `_population_to_entity_dict()`

```
1. Build key_to_plural mapping (existing)
2. Identify person entity (existing)
3. Call _detect_membership_columns(person_table, tbs)
4. IF no membership columns → execute EXISTING code path unchanged
5. IF membership columns detected:
   a. Call _resolve_valid_role_keys(tbs)
   b. Call _validate_entity_relationships(person_table, membership_cols, valid_roles)
   c. Build set of all membership column names (for exclusion)
   d. Build person instances (excluding membership columns from period-wrapping)
   e. For each group entity:
      i.   Read _id and _role columns from person table
      ii.  Get sorted distinct group IDs
      iii. For each group ID:
           - Collect person instance IDs with this group ID
           - Sub-group by role key
           - Build: {role_key: [person_ids]}
      iv.  Store: result[entity_plural][f"{entity_key}_{group_id}"] = role_dict
   f. Merge group entity table variables (if present):
      i.   For each group entity with a table in PopulationData
      ii.  Match table rows to group instances by sorted distinct ID order
      iii. Add period-wrapped variable values to group instance dict
   g. Inject policy parameters (existing, person entity only)
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

3. **Empty group** — a group ID that appears in no person's `_id` column. This can't happen by construction (groups are discovered from person table), but if a group entity table has more rows than distinct group IDs from the person table, the extra rows are orphaned. Raise `ApiMappingError`.

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

Story 9.3: Added periodicity-aware calculation dispatch. Monthly variables
use ``calculate_add()`` to sum sub-period values; yearly and eternity
variables use ``calculate()``. Period validation ensures valid 4-digit year.
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

# Story 9.3: Valid OpenFisca DateUnit periodicity values (StrEnum).
# Sub-yearly periodicities use calculate_add(); year/eternity use calculate().
_VALID_PERIODICITIES = frozenset({
    "month", "year", "eternity", "day", "week", "weekday",
})
_CALCULATE_ADD_PERIODICITIES = frozenset({
    "month", "day", "week", "weekday",
})


def _periodicity_to_method_name(periodicity: str) -> str:
    """Map a DateUnit periodicity string to the OpenFisca calculation method name.

    Single source of truth for the ``calculate`` vs ``calculate_add`` dispatch
    decision. Sub-yearly periodicities (month, day, week, weekday) aggregate
    via ``calculate_add``; year and eternity use ``calculate`` directly.
    """
    return "calculate_add" if periodicity in _CALCULATE_ADD_PERIODICITIES else "calculate"


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

        Raises:
            ApiMappingError: If the period is invalid (not a 4-digit year
                in range [1000, 9999]).
        """
        # Story 9.3 AC-3: Period validation — FIRST check before any TBS operations.
        self._validate_period(period)

        start = time.monotonic()

        tbs = self._get_tax_benefit_system()
        self._validate_output_variables(tbs)

        # Story 9.2: Resolve entity grouping before building simulation (fail fast —
        # avoid expensive SimulationBuilder.build_from_entities() if entity
        # resolution fails due to incompatible country package).
        vars_by_entity = self._resolve_variable_entities(tbs)

        # Story 9.3 AC-1, AC-2, AC-6: Resolve periodicities before simulation
        # (fail fast — detect unsupported periodicity values early).
        var_periodicities = self._resolve_variable_periodicities(tbs)

        simulation = self._build_simulation(population, policy, period, tbs)
        entity_tables = self._extract_results_by_entity(
            simulation, period, vars_by_entity, var_periodicities
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

        # Story 9.3 AC-5: Build calculation methods mapping from periodicities.
        # Uses _periodicity_to_method_name() — single source of truth for the
        # calculate vs calculate_add dispatch decision.
        calculation_methods: dict[str, str] = {
            var_name: _periodicity_to_method_name(periodicity)
            for var_name, periodicity in var_periodicities.items()
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
                "variable_periodicities": dict(var_periodicities),
                "calculation_methods": calculation_methods,
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

    # ------------------------------------------------------------------
    # Story 9.3: Period validation and periodicity-aware dispatch
    # ------------------------------------------------------------------

    def _validate_period(self, period: int) -> None:
        """Validate that the period is a 4-digit year in [1000, 9999].

        Story 9.3 AC-3: Called as the FIRST operation in ``compute()``,
        before any TBS queries or simulation construction.

        Raises:
            ApiMappingError: If the period is invalid.
        """
        if not (1000 <= period <= 9999):
            raise ApiMappingError(
                summary="Invalid period",
                reason=(
                    f"Period {period!r} is not a valid 4-digit year"
                ),
                fix=(
                    "Provide a positive integer year in range [1000, 9999], "
                    "e.g. 2024"
                ),
                invalid_names=(),
                valid_names=(),
            )

    def _resolve_variable_periodicities(
        self, tbs: Any
    ) -> dict[str, str]:
        """Detect the periodicity of each output variable from the TBS.

        Story 9.3 AC-1, AC-2, AC-6: Queries
        ``tbs.variables[var_name].definition_period`` for each output variable
        to determine whether ``calculate()`` or ``calculate_add()`` should
        be used.

        Args:
            tbs: The loaded TaxBenefitSystem.

        Returns:
            Dict mapping variable name to periodicity string
            (e.g. ``{"salaire_net": "month", "irpp": "year"}``).

        Raises:
            ApiMappingError: If a variable's periodicity cannot be determined
                or has an unexpected value.
        """
        periodicities: dict[str, str] = {}

        for var_name in self._output_variables:
            variable = tbs.variables.get(var_name)
            if variable is None:
                # Defensive — _validate_output_variables should have caught this.
                raise ApiMappingError(
                    summary="Cannot resolve variable periodicity",
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

            definition_period = getattr(variable, "definition_period", None)
            if definition_period is None:
                raise ApiMappingError(
                    summary="Cannot determine periodicity for variable",
                    reason=(
                        f"Variable '{var_name}' has no .definition_period "
                        f"attribute in {self._country_package} TaxBenefitSystem"
                    ),
                    fix=(
                        "This variable may not be properly defined in the "
                        "country package. Check the variable definition."
                    ),
                    invalid_names=(var_name,),
                    valid_names=tuple(sorted(tbs.variables.keys())),
                )

            # DateUnit is a StrEnum — string comparison works directly.
            periodicity_str = str(definition_period)
            if periodicity_str not in _VALID_PERIODICITIES:
                raise ApiMappingError(
                    summary="Unexpected periodicity for variable",
                    reason=(
                        f"Variable '{var_name}' has definition_period="
                        f"'{periodicity_str}', expected one of: "
                        f"{', '.join(sorted(_VALID_PERIODICITIES))}"
                    ),
                    fix=(
                        "This may indicate an incompatible OpenFisca version. "
                        "Check the OpenFisca compatibility matrix."
                    ),
                    invalid_names=(var_name,),
                    valid_names=tuple(sorted(tbs.variables.keys())),
                )

            periodicities[var_name] = periodicity_str

        logger.debug(
            "variable_periodicities=%s output_variables=%s",
            periodicities,
            list(self._output_variables),
        )

        return periodicities

    def _calculate_variable(
        self,
        simulation: Any,
        var_name: str,
        period_str: str,
        periodicity: str,
    ) -> Any:
        """Dispatch to the correct OpenFisca calculation method.

        Story 9.3 AC-1, AC-2, AC-6:
        - ``"month"``, ``"day"``, ``"week"``, ``"weekday"``
          → ``simulation.calculate_add(var, period)``
        - ``"year"``, ``"eternity"``
          → ``simulation.calculate(var, period)``

        Args:
            simulation: The OpenFisca simulation.
            var_name: Variable name to compute.
            period_str: Period string (e.g. "2024").
            periodicity: The variable's definition_period string.

        Returns:
            numpy.ndarray of computed values.
        """
        method = _periodicity_to_method_name(periodicity)
        logger.debug(
            "var=%s periodicity=%s method=%s period=%s",
            var_name, periodicity, method, period_str,
        )
        if method == "calculate_add":
            return simulation.calculate_add(var_name, period_str)
        else:
            return simulation.calculate(var_name, period_str)

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
        variable_periodicities: dict[str, str],
    ) -> dict[str, pa.Table]:
        """Extract output variables grouped by entity into per-entity tables.

        For each entity group, calls the appropriate calculation method
        (``calculate()`` or ``calculate_add()``) for its variables and
        builds a ``pa.Table`` per entity. Arrays within an entity group
        share the same length (entity instance count).

        Story 9.3: Uses ``_calculate_variable()`` for periodicity-aware
        dispatch instead of calling ``simulation.calculate()`` directly.

        Args:
            simulation: The completed OpenFisca simulation.
            period: Computation period (integer year).
            vars_by_entity: Output variables grouped by entity plural name
                (from ``_resolve_variable_entities``).
            variable_periodicities: Periodicity per variable
                (from ``_resolve_variable_periodicities``).

        Returns:
            Dict mapping entity plural name to a PyArrow Table containing
            that entity's output variables.
        """
        period_str = str(period)
        entity_tables: dict[str, pa.Table] = {}

        for entity_plural, var_names in vars_by_entity.items():
            arrays: dict[str, pa.Array] = {}
            for var_name in var_names:
                periodicity = variable_periodicities[var_name]
                numpy_array = self._calculate_variable(
                    simulation, var_name, period_str, periodicity
                )
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

from __future__ import annotations
import sys
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch
import pyarrow as pa
import pytest
from reformlab.computation.adapter import ComputationAdapter
from reformlab.computation.exceptions import ApiMappingError, CompatibilityError
from reformlab.computation.openfisca_api_adapter import OpenFiscaApiAdapter
from reformlab.computation.types import ComputationResult, PolicyConfig, PopulationData
        from reformlab.computation.openfisca_adapter import OpenFiscaAdapter
        from reformlab.computation.openfisca_adapter import OpenFiscaAdapter

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
    # Story 9.3: Also set definition_period = "year" by default. Without this,
    # MagicMock().definition_period returns a MagicMock object whose str()
    # representation ("<MagicMock ...>") is not in _VALID_PERIODICITIES, causing
    # _resolve_variable_periodicities() to raise ApiMappingError("Unexpected
    # periodicity...") and breaking all existing compute() unit tests.
    default_entity = entities_by_key.get(person_entity, entities[0])
    variables: dict[str, Any] = {}
    for name in variable_names:
        var_mock = MagicMock()
        var_mock.entity = default_entity
        var_mock.definition_period = "year"
        variables[name] = var_mock
    tbs.variables = variables

    return tbs


def _make_mock_tbs_with_entities(
    entity_keys: tuple[str, ...] = ("individu", "foyer_fiscal", "menage"),
    entity_plurals: dict[str, str] | None = None,
    variable_entities: dict[str, str] | None = None,
    variable_periodicities: dict[str, str] | None = None,
    person_entity: str = "individu",
) -> MagicMock:
    """Create a mock TBS where variables know their entity.

    Story 9.2: Extended mock for entity-aware extraction tests.
    Story 9.3: Added variable_periodicities parameter for periodicity-aware tests.

    Args:
        entity_keys: Entity singular keys.
        entity_plurals: Mapping of singular key to plural form.
            Defaults to appending "s" (with special cases).
        variable_entities: Mapping of variable name to entity key.
        variable_periodicities: Mapping of variable name to periodicity string
            (e.g. "month", "year", "eternity"). Defaults to "year" for all.
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
    if variable_periodicities is None:
        variable_periodicities = {}

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
    # Story 9.3: Also set definition_period (default "year" for backward compat)
    if variable_entities is None:
        variable_entities = {}
    variables: dict[str, Any] = {}
    for var_name, entity_key in variable_entities.items():
        var_mock = MagicMock()
        var_mock.entity = entities_by_key[entity_key]
        var_mock.definition_period = variable_periodicities.get(var_name, "year")
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

    def test_empty_output_variables_raises_error(self) -> None:
        """Empty output_variables tuple raises ApiMappingError at construction time."""
        with pytest.raises(ApiMappingError) as exc_info:
            OpenFiscaApiAdapter(
                output_variables=(),
                skip_version_check=True,
            )
        assert "Empty output_variables" in exc_info.value.summary


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


    def test_empty_output_variables_raises_error(self) -> None:
        """Empty output_variables tuple raises ApiMappingError at construction time."""
        with pytest.raises(ApiMappingError) as exc_info:
            OpenFiscaApiAdapter(
                output_variables=(),
                skip_version_check=True,
            )
        assert "Empty output_variables" in exc_info.value.summary


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


    def test_adapter_version_in_result(  # ...

]]></file>
<file id="895c54dc" path="tests/computation/test_openfisca_integration.py" label="SOURCE CODE"><![CDATA[

from __futur

]]></file>
<file id="1d910d88" path="[Validator A]" label="VALIDATION OUTPUT"><![CDATA[

# 🎯 Story Validation: Epic 9.4 - Define Population Data 4-Entity Format

I've completed a comprehensive adversarial review of **Story 9.4: Define Population Data 4-Entity Format** from the ReformLab OpenFisca integration epic.

## 📊 Quick Assessment

| Category | Count | Status |
|----------|-------|--------|
| **Critical Issues** | 3 | 🚨 Blocking |
| **Important Gaps** | 4 | ⚠️ Should fix |
| **Enhancements** | 5 | ✨ Polish |
| **LLM Optimizations** | 3 | 🤖 Efficiency |

**Evidence Score: 6.2** → **MAJOR REWORK REQUIRED**

---

## 🚨 Critical Issues Found

### **Issue #1: Test File Corruption (BLOCKER)**
**Severity:** 🔴 CRITICAL | **Impact:** Tests won't compile

The provided test file (`test_openfisca_api_adapter.py`) contains **duplicate class and method definitions**:
- `TestProtocolCompliance` class defined, then methods repeated
- `test_isinstance_check()` appears twice
- `TestVersionChecking` methods duplicated  
- `test_openfisca_integration.py` truncated mid-file

**Problem:** Python will raise `SyntaxError: redefinition of unused name` or `IndentationError`.

**Recommendation:** 
```bash
# Verify the actual stored files are clean
# The provided context appears corrupted
# Either:
1. The files have real duplication (fix before running tests)
2. The context rendering had XML/embedding issues (not a real problem)
```

**Action:** Before dev starts, confirm actual source files are syntactically valid:
```bash
uv run python -m py_compile tests/computation/test_openfisca_api_adapter.py
```

---

### **Issue #2: Missing Import Statements**
**Severity:** 🔴 CRITICAL | **Impact:** Tests will fail with NameError

The test file uses:
- `np.ndarray` — **no `import numpy as np`**
- `_mock_sim_builder_module` — **undefined, used in `_patch_simulation_builder()`**
- `_make_mock_simulation()` calls `numpy.ndarray` without numpy imported

**Problem:** All tests referencing these will crash.

**Recommendation:**
Add to test file imports:
```python
import numpy as np
```

And define/import `_mock_sim_builder_module` or remove the undefined `_patch_simulation_builder()` function if it's not used.

---

### **Issue #3: Story 9.3 Status Is Blocking (DEPENDENCY)**
**Severity:** 🔴 CRITICAL | **Impact:** Development sequence risk

**Current state:**
- Story 9.2 (Handle Multi-Entity Output Arrays): ✅ **DONE** 
- Story 9.3 (Add Variable Periodicity Handling): ⚠️ **IN-PROGRESS** (not complete)
- Story 9.4: 🟡 **READY-FOR-DEV** (depends on 9.3)

**Problem:** Story assumes `_resolve_variable_periodicities()` from 9.3 is complete, but 9.3 is still in-progress. If dev starts on 9.4 now, they'll hit:
- Missing method in `openfisca_api_adapter.py`
- Missing periodicity-aware dispatch in `_extract_results_by_entity()`
- Breaking test failures

**Recommendation:**
Update story prerequisite section:
```markdown
## Prerequisites

**MUST BE COMPLETE BEFORE STARTING:**
- ✅ Story 9.2: Handle Multi-Entity Output Arrays
- ✅ Story 9.3: Add Variable Periodicity Handling (currently IN-PROGRESS)

If Story 9.3 is not yet complete, **pause this story** until it reaches "done" status.
```

---

## ⚠️ Important Gaps (Should Add)

### **Gap #1: Role Plural Edge Case Not Documented**
**Source:** Task 2.2 - `_resolve_valid_role_keys()`

The code pattern `role.plural or role.key` is correct, but doesn't handle:
- What if `role.plural = ""` (empty string)?
- What if `role.plural = None` but code already returns `None`?

**Current guidance:**
```python
# From Dev Notes:
plural = getattr(role, "plural", None)
key = getattr(role, "key", None)
role_dict_key = plural or key
```

**Problem:** Empty string `""` is falsy but not None, so `"" or key` would work. But what if role.plural is specifically set to `""`? This is unlikely in OpenFisca but the docs should be explicit.

**Recommendation:**
```python
# More defensive approach
role_dict_key = (plural if plural else None) or key
# Or explicitly check:
if plural and len(plural) > 0:
    role_dict_key = plural
else:
    role_dict_key = key
```

### **Gap #2: Fragile Group-to-Row Matching (Data Corruption Risk)**
**Source:** Task 4.6 - "Merge group entity table variables"

Current algorithm:
```
1. Get distinct group IDs from person table: [0, 2, 2] → {0, 2}
2. Sort them: [0, 2]
3. Match group table rows by position: row[0] → group 0, row[1] → group 2
```

**Problem:** **SILENT DATA CORRUPTION** if:
- Group entity table rows are in different order than person table group IDs
- Sorted group IDs don't match row order
- Someone inserts a row in the middle

**Current mitigation:** 
- AC-7 validates row count matches distinct group count ✓
- Prevents wrong counts but not wrong ORDER

**Recommendation:**
Add validation that catches order mismatches:
```python
# Task 4.6 Implementation Detail:
distinct_group_ids = sorted(set(person_table['menage_id'].to_pylist()))
group_table_rows = group_entity_table.num_rows

if len(distinct_group_ids) != group_table_rows:
    raise ApiMappingError(...)  # ✓ Already does this

# NEW: Validate order assumption
# If group table has an ID column, use it for matching (safer)
if 'menage_id' in group_entity_table.column_names:
    group_ids_from_table = group_entity_table['menage_id'].to_pylist()
    if group_ids_from_table != distinct_group_ids:
        raise ApiMappingError(
            summary="Group entity table row order doesn't match person table group order",
            reason=f"Expected group IDs {distinct_group_ids}, but table has {group_ids_from_table}",
            fix="Ensure group entity table rows are sorted by group ID"
        )
```

**Action Item:** Add this validation to Task 4.6.

### **Gap #3: Missing Pytest Fixtures for Integration Tests**
**Source:** Task 6 - Integration tests

Story provides **example data** in Dev Notes but no actual **pytest fixture code**.

Developers will hand-write fixtures, introducing errors. 

**Recommendation:**
Add actual fixture code under "Integration Test Fixtures" section:

```python
@pytest.fixture()
def married_couple_population() -> PopulationData:
    """Married couple: 2 persons, shared foyer, shared menage."""
    return PopulationData(
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
        },
    )

@pytest.fixture()  
def family_with_child_population() -> PopulationData:
    """Family: 2 adults + 1 child, 1 famille, 1 foyer, 1 menage."""
    return PopulationData(
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

### **Gap #4: Missing Backward Compatibility Test Example**
**Source:** Task 6.5 - "Backward compatibility"

Story says:
```
[ ] 6.5 Test: **backward compatibility** — existing `single_person_population` 
    fixture (no membership columns) still works identically
```

But doesn't provide an actual test. Dev has to write from scratch.

**Recommendation:**
Add explicit test template:
```python
class TestBackwardCompatibility:
    """AC-6: PopulationData without membership columns works unchanged."""
    
    def test_single_person_no_membership_columns(self):
        """Single person with no membership columns → behaves identically to pre-9.4."""
        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0]),
                    "age": pa.array([30]),
                    # NO membership columns!
                }),
            },
        )
        # Compute should succeed and return same result as before 9.4
        result = adapter.compute(population, policy, 2025)
        assert result.output_fields.num_rows == 1
        # Value should match pre-9.4 behavior
        assert result.output_fields.column("irpp")[0].as_py() == pytest.approx(-1234.0, rel=1e-3)
```

### **Gap #5: OpenFisca Version Compatibility Not Documented**
**Source:** Story entire scope

Story targets OpenFisca 44.x (from project context), but:
- No warning if used with older OpenFisca versions that don't have entity.roles
- No documented minimum version

**Recommendation:**
Add to Dev Notes:
```
### OpenFisca Compatibility

**Minimum Version:** openfisca-core >= 44.0.0

This story uses entity.roles which changed in 44.x. Earlier versions may not support this pattern.

Verify with:
```python
import openfisca_core
assert openfisca_core.__version__ >= "44.0.0"
```
```

---

## ✨ Enhancements (Nice to Have)

### **E1: Membership Detection Visualization**
Add ASCII diagram showing the detection logic:
```
PopulationData.tables["individu"]:
  ├─ Column: salaire_de_base → variable ✓
  ├─ Column: famille_id → membership! 
  ├─ Column: famille_role → membership!
  ├─ Column: foyer_fiscal_id → membership!
  └─ ...
  
Detection: Found ANY membership column → 
  → Require ALL entities have both _id AND _role → 
  → Enter 4-entity format mode
```

### **E2: Configuration Defaults Doc**
Add table of defaults the adapter uses when membership columns detected:
```
| Setting | Default | Override? |
|---------|---------|-----------|
| Group ID format | int64 or utf8 | Use as-is |
| Group instance ID prefix | "{entity_key}_{id_value}" | Fixed |
| Row order matching | Sorted by distinct ID | See Risk #2 |
| Role validation | Check against TBS | Fixed |
```

### **E3: Troubleshooting Section**
Add common error scenarios:
```
**ERROR: "Incomplete entity membership columns"**
→ You have famille_id but missing famille_role
→ Fix: Add both columns for ALL group entities or remove all

**ERROR: "Invalid role value"**  
→ menage_role = "invalid_role" not in {personne_de_reference, conjoint, ...}
→ Fix: Check spelling against TBS roles
```

### **E4: Algorithm Pseudocode**
Replace verbose english with clearer pseudocode for Task 4.5-4.6:
```python
# Task 4.5: Build group entities from membership columns
for group_entity_key in ["famille", "foyer_fiscal", "menage"]:
    id_col = population["individu"][f"{group_entity_key}_id"]
    role_col = population["individu"][f"{group_entity_key}_role"]
    
    groups = {}
    for i, (person_id, group_id, role) in enumerate(
        zip(person_ids, id_col, role_col)
    ):
        group_instance_id = f"{group_entity_key}_{group_id}"
        if group_instance_id not in groups:
            groups[group_instance_id] = {}
        if role not in groups[group_instance_id]:
            groups[group_instance_id][role] = []
        groups[group_instance_id][role].append(person_id)
    
    entity_dict[entity_plurals[group_entity_key]] = groups
```

### **E5: Cross-reference Previous Stories**
Add explicit "builds on" section:
```
## Previous Story Integration

This story builds on the work from Stories 9.2 and 9.3:

**Story 9.2** (Handle Multi-Entity Output Arrays):
- Added `_resolve_variable_entities()` 
- Produces `entity_tables` dict keyed by plural entity name
- **Implication for 9.4:** Output from compute() now has per-entity tables

**Story 9.3** (Add Variable Periodicity Handling):
- Added `_resolve_variable_periodicities()`
- Dispatch to calculate() vs calculate_add()
- **Implication for 9.4:** Periodicity is already resolved, just use it

**Impact on 9.4:**
- `_population_to_entity_dict()` is called by `_build_simulation()` 
- which is already called in the 9.2/9.3 compute() chain
- 9.4 extends this with membership column detection
```

---

## 🤖 LLM Optimization Opportunities

### **Opt #1: Consolidate Edge Cases Section**
**Current:** Scattered throughout Dev Notes  
**Issue:** Dev agent has to search multiple places

**Consolidate into single table:**
```markdown
## Edge Cases (Handled)

| Scenario | Current Handling | Risk Level |
|----------|------------------|-----------|
| Non-contiguous group IDs (0, 2, 2) | Use ID as dict key | ✅ Safe |
| String vs int group IDs | Auto-convert via f-string | ✅ Safe |
| Null in membership columns | PyArrow null check in AC-5 | ✅ Validated |
| Group table row count mismatch | ApiMappingError in AC-7 | ✅ Caught |
| Single person w/ membership | Supported edge case | ✅ Works |
| Empty string role.plural | Handled by `plural or key` | ⚠️ See Gap #1 |
| Group table row order != person order | ⚠️ RISK: Silent mismatch | 🚨 See Gap #2 |
```

### **Opt #2: Reduce Dev Notes Verbosity**
**Current:** 600+ lines of detailed reference material  
**Issue:** Dev agent wastes tokens on low-priority details

**Action:**
- Move detailed role table to appendix
- Condense algorithm description to pseudocode
- Keep critical notes inline

**Example reduction:**
```markdown
### OpenFisca Role System

Key: `build_from_entities()` uses `role.plural or role.key` as dict key

OpenFisca-France roles:
- famille: parents, enfants
- foyer_fiscal: declarants, personnes_a_charge  
- menage: personne_de_reference, conjoint, enfants, autres

[Full role table in Appendix A]
```

Saves ~200 tokens.

### **Opt #3: Task List Formatting**
**Current:** Tasks 1.1-1.4 are separate bullet points  
**Better:** Group by task type

```markdown
## Tasks / Subtasks

- [ ] Task 1: Implement membership column detection
  - [ ] 1.1-1.2: Add `_detect_membership_columns()` method
  - [ ] 1.3-1.4: All-or-nothing validation + unit tests
  
- [ ] Task 2: Implement role validation  
  - [ ] 2.1-2.3: Add `_resolve_valid_role_keys()` method
  
...
```

Saves ~50 tokens, same info.

---

## 📋 Summary & Recommendations

### **What's Strong:**
✅ Comprehensive acceptance criteria (7 ACs)  
✅ Good backward compatibility story  
✅ Thoughtful error handling patterns  
✅ Detailed dev notes with examples  
✅ Architecture alignment verified  

### **What Needs Attention:**

| Priority | Issue | Effort |
|----------|-------|--------|
| 🔴 CRITICAL | Fix test file corruption | 15 min |
| 🔴 CRITICAL | Add missing imports | 5 min |
| 🔴 CRITICAL | Update Story 9.3 dependency note | 10 min |
| 🟠 IMPORTANT | Add group ID order validation | 30 min |
| 🟠 IMPORTANT | Add pytest fixtures | 20 min |
| 🟡 MINOR | LLM optimization | 30 min |

---

## 🎯 Next Steps

**Recommended Actions:**

1. **Verify source files** - Confirm test file in `tests/computation/` doesn't have duplicate definitions
   ```bash
   ls -la tests/computation/test_openfisca_api_adapter.py
   python -m py_compile tests/computation/test_openfisca_api_adapter.py
   ```

2. **Confirm Story 9.3 status** - Check if it's actually complete or still in-progress
   ```bash
   grep "Status:" _bmad-output/implementation-artifacts/9-3-*.md
   ```

3. **Address Critical Issues** - Apply the 3 critical fixes before dev starts

4. **Consider enhancements** - The 5 enhancements would reduce developer confusion

5. **Request updated story** - When ready, I can generate a revised version with these improvements

Would you like me to:
- **A)** Apply selected improvements to the story file?
- **B)** Generate a detailed issue-by-issue improvement guide?
- **C)** Create a checklist of items dev should verify before starting?
- **D)** Compare this story against Stories 9.2 and 9.3 for cross-story consistency?

What would be most helpful? 🎯

]]></file>
<file id="557aedd2" path="[Validator B]" label="VALIDATION OUTPUT"><![CDATA[

# 🎯 Story Context Validation Report

**Story:** `9-4-define-population-data-4-entity-format`
**Story File:** `_bmad-output/implementation-artifacts/9-4-define-population-data-4-entity-format.md`
**Validated:** 2026-03-01
**Validator:** Quality Competition Engine

---

## Executive Summary

### Issues Overview

| Category | Found | Applied |
|----------|-------|---------|
| 🚨 Critical Issues | 0 | 0 |
| ⚡ Enhancements | 6 | 0 |
| ✨ Optimizations | 3 | 0 |
| 🤖 LLM Optimizations | 2 | 0 |

**Overall Assessment:** Story 9.4 is well-researched and comprehensive — the OpenFisca role system is correctly documented, backward compatibility is thoroughly handled, and the AC coverage is strong (3 epics ACs expanded to 7). However, six important gaps in the implementation algorithm could cause a developer to write subtly incorrect code. The most critical are: (1) ambiguity about whether the main table-iteration loop should be replaced or extended in 4-entity mode, (2) hardcoded instance ID prefixes in Task 4.5 examples that contradict the code's actual behavior, and (3) missing documentation for how to extract the person table from PopulationData inside `_population_to_entity_dict()`. These are not fatal but will generate real confusion and debugging time.

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🟠 IMPORTANT | Main table-iteration loop behavior in 4-entity mode is ambiguous — "same as current logic" could mean iterate all tables or person-only | Task 4.4 algorithm | +1 |
| 🟠 IMPORTANT | Task 4.5 hardcodes `"individu_0"` in role array example but actual prefix is the original PopulationData table key | Task 4.5 / Dev Notes contradiction | +1 |
| 🟠 IMPORTANT | How to extract `person_table` from `population.tables` to call `_detect_membership_columns(person_table, tbs)` is never documented | Task 1 / Algorithm step 3 | +1 |
| 🟠 IMPORTANT | Story 9.3 is "in-progress" and Story 9.4 is "ready-for-dev" — both modify the same file `openfisca_api_adapter.py`, creating merge conflict risk | Story statuses | +1 |
| 🟠 IMPORTANT | AC-7 group entity variable merge uses positional row-order matching — silent data corruption risk with non-contiguous IDs understated | Task 4.6 | +1 |
| 🟠 IMPORTANT | No documented behavior when `population.tables` has no person entity table (e.g., only a `menage` table provided) | Task 1, Algorithm | +1 |
| 🟡 MINOR | `pa.compute` import pattern not shown (though accessible as `pa.compute` directly in PyArrow ≥18) | Task 3.2 | +0.3 |
| 🟡 MINOR | Column type validation before null check not specified — a float64 `_id` column would pass detection but produce unexpected behavior | Task 3.2 | +0.3 |
| 🟡 MINOR | Mock TBS entity building loop example does not show adding `entity.roles = []` on the person entity mock | Dev Notes mock section | +0.3 |
| 🟡 MINOR | ABSOLUTE_ERROR_MARGIN for new integration tests not specified; existing reference tests use 0.5 — should be stated explicitly | Task 6 integration tests | +0.3 |
| 🟢 CLEAN PASS | INVEST compliance — story is independent enough, valuable, estimable, and well-scoped | Full story | -0.5 |
| 🟢 CLEAN PASS | Architecture alignment — frozen dataclasses, adapter isolation, PyArrow canonical, exceptions correct | Full story | -0.5 |
| 🟢 CLEAN PASS | Backward compatibility — thoroughly documented with opt-in detection, MockAdapter unaffected | Full story / Task 7 | -0.5 |

### Evidence Score: **5.7**

| Score | Verdict |
|-------|---------|
| **5.7** | **MAJOR REWORK** |

---

## 🎯 Ruthless Story Validation 9.4

### INVEST Criteria Assessment

| Criterion | Status | Severity | Details |
|-----------|--------|----------|---------|
| **I**ndependent | ⚠️ Minor concern | 3/10 | Story 9.3 is "in-progress" and modifies the same file — concurrent development on `openfisca_api_adapter.py` creates merge conflict risk |
| **N**egotiable | ✅ Pass | 2/10 | Prescriptive about method signatures but appropriately so; implementation flexibility maintained on algorithm internals |
| **V**aluable | ✅ Pass | 1/10 | Clear business value — enables multi-person household simulations required for all realistic French tax policy analysis |
| **E**stimable | ✅ Pass | 3/10 | 8-point estimate is reasonable for 7 tasks; AC-7 (group entity variable merge) is the most uncertain subtask |
| **S**mall | ✅ Pass | 3/10 | 7 tasks + quality gates is substantial but logically cohesive; splitting AC-7 would fragment a natural unit |
| **T**estable | ✅ Pass | 2/10 | ACs are specific and measurable; AC-1 and AC-2 are slightly vague ("correctly assigned", "preserved") but the integration test references make them concrete |

### INVEST Violations

- **[3/10] Independent:** Story 9.3 is currently in-progress and modifies `openfisca_api_adapter.py`. Story 9.4 is marked ready-for-dev on the same file. The story should note this dependency and recommend waiting for Story 9.3 to merge before starting, or developing on a branch that rebases against 9.3's changes.

### Acceptance Criteria Issues

- **Missing detail — AC-1:** The phrase "all entity relationships are preserved and passable to `SimulationBuilder`" requires the developer to know what "passable" means. The integration test reference data (Task 6.1) makes this concrete, but the AC itself has no measurable boundary.
  - *Quote:* "when a population dataset is loaded with membership columns…then `_population_to_entity_dict()` produces a valid entity dict with all entity relationships preserved and passable to `SimulationBuilder.build_from_entities()`"
  - *Recommendation:* Add "and the returned dict produces a working simulation when passed to `SimulationBuilder.build_from_entities(tbs, entity_dict)` without raising `SituationParsingError`" to make AC-1 objectively testable at the unit level.

- **Ambiguity — AC-7:** "Verify the value appears in the entity dict and is passable to `build_from_entities()`" is the correct scope limit (doesn't test computed correctness), but the test description says "Verify the value appears in the entity dict" — a unit-level check — while the test is listed under integration tests (Task 6.4). Should be clear whether this is a unit test or integration test.
  - *Recommendation:* Move the group entity variable check to a unit test in `TestPopulationToEntityDict4Entity`, leaving integration test 6.4 to verify an end-to-end compute call succeeds with a `loyer` variable in the group entity table.

### Hidden Risks and Dependencies

- **Story 9.3 merge conflict risk:** Story 9.3 (in-progress) modifies `openfisca_api_adapter.py`, specifically the `compute()` call order and `_extract_results_by_entity()` signature. Story 9.4 modifies `_population_to_entity_dict()` and adds three new private methods. These don't directly overlap but a developer starting 9.4 now will need to rebase against 9.3's completed changes before PR.
  - *Impact:* Moderate — 9.3 changes are additive; the conflict will be in import ordering and potentially `_build_simulation()`. But if developer doesn't track this, the 9.4 branch may fail CI after 9.3 merges.
  - *Mitigation:* Add a note to Story 9.4 that it should not be started until Story 9.3 is merged, or should be developed on a branch that explicitly tracks `9.3-branch`.

- **OpenFisca role.plural == None edge case:** The story correctly documents that `menage`'s `personne_de_reference` and `conjoint` roles have `role.plural = None` and that `role.plural or role.key` must be used. But the mock TBS pattern doesn't show what happens when `getattr(role, "plural", None)` returns `None` vs `""`. A developer building a mock where `plural` is set to `""` (empty string) instead of `None` would get `role_dict_key = "" or "personne_de_reference"` = `"personne_de_reference"` — correct. But if `plural = None`, then `None or "personne_de_reference"` = `"personne_de_reference"` — also correct. This edge case is actually safe, but worth verifying the mock sets `plural=None` not `plural=""`.

### Estimation Reality-Check

**Assessment:** Realistic at 8 points

The 8-point estimate is appropriate. The three new methods (`_detect_membership_columns`, `_resolve_valid_role_keys`, `_validate_entity_relationships`) plus refactoring `_population_to_entity_dict` is substantial but well-scoped. The main risk is AC-7 (group entity variable merge) which requires careful coordination between the person-table processing and group-table merging loops. Recommend treating AC-7's Task 4.6 as its own unit of work.

### Technical Alignment

**Status:** ✅ Aligned

- Frozen dataclasses: `PopulationData` and `ComputationResult` are not modified — correct.
- Adapter isolation: All changes are within `openfisca_api_adapter.py` — correct.
- PyArrow canonical: Uses `pa.Table`, `pa.compute.is_null()` — correct.
- Subsystem exceptions: Reuses `ApiMappingError` — correct.
- `from __future__ import annotations` — correctly noted.
- `mypy --strict` compliance: The new methods are fully typed in examples — aligned.

### Evidence Score: 5.7 → **MAJOR REWORK**

---

## 🚨 Critical Issues (Must Fix)

✅ No critical issues found — the original story covered essential requirements, role system documentation is accurate, and backward compatibility strategy is sound.

---

## ⚡ Enhancement Opportunities (Should Add)

### 1. Ambiguity: Main table-iteration loop behavior in 4-entity mode

**Benefit:** Prevents a developer from writing code that silently overwrites membership-derived group entity instances with period-wrapped table data.
**Source:** `_population_to_entity_dict()` lines 538–569, Task 4 algorithm

**Current Gap:**
Task 4.4 says "Build person instances: same as current logic but excluding membership columns". This is ambiguous. The existing "current logic" iterates ALL tables in `population.tables`. If a developer reads "same as current logic" literally, they will keep the all-table loop and process both the person table AND any group entity tables (e.g., the `menage` table for AC-7). This creates a collision:

- If the existing loop processes the `menage` table first → `result["menages"] = {"menage_0": {"loyer": {"2024": 800.0}}}`
- Then Task 4.5 tries to build group instances from membership columns → also writes to `result["menages"]`
- The two writes produce inconsistent results depending on order

The algorithm INTENDS for Task 4.4 to process **only the person entity table**, and Task 4.6 to handle group entity table variables separately via merging. But this is never stated explicitly.

**Suggested Addition:**
In Task 4.4, add explicitly:

```
4.4 Build person instances ONLY FROM THE PERSON ENTITY TABLE:
    - Identify person entity table: find key in population.tables whose normalized 
      plural matches person_entity.plural
    - Iterate person table rows only (not group entity tables)
    - Excluding membership columns from period-wrapping
    - Result: {"individu_0": {"salaire_de_base": {"2024": 30000.0}}, ...}
    
    ⚠️ DO NOT iterate group entity tables in this step. 
    Group entity table variables are merged later in Task 4.6.
    In 4-entity mode, the original "iterate ALL tables" loop is REPLACED 
    by the combination of Tasks 4.4 (person) + 4.5 (group from membership) 
    + 4.6 (group variables merge).
```

---

### 2. Task 4.5 hardcodes `"individu_0"` — misleads on actual instance ID prefix

**Benefit:** Prevents a developer from hardcoding `"individu"` as the person instance ID prefix, which would break for populations with `"individus"` as the table key.
**Source:** Task 4.5, Dev Notes "Group Instance ID Generation"

**Current Gap:**
Task 4.5 says:
> "Produce: `{'famille_0': {'parents': ['individu_0', 'individu_1']}, ...}`"

This hardcodes `"individu_0"` as the person instance ID. But the existing code does:
```python
instance_id = f"{entity_key}_{i}"  # entity_key from population.tables
```

If the user passes `"individus"` as the PopulationData table key, person instance IDs are `"individus_0"`, `"individus_1"`. The group entity role lists MUST use these same IDs. The Dev Notes "Group Instance ID Generation" section correctly states: "Currently, `_population_to_entity_dict()` uses `f'{entity_key}_{i}'` where `entity_key` comes from the PopulationData table key" — but Task 4.5 contradicts this with its hardcoded example.

**Suggested Addition:**
Change Task 4.5's example to:
```python
# person_table_key is the original key from population.tables (e.g. "individu" or "individus")
# NOT necessarily the TBS entity.key
# person instance IDs: f"{person_table_key}_{row_index}"
# → if person_table_key = "individu": "individu_0", "individu_1"
# → if person_table_key = "individus": "individus_0", "individus_1"
produce: {
    "famille_0": {"parents": [f"{person_table_key}_0", f"{person_table_key}_1"]}
}
```

And in the algorithm, add:
```
Step d.0: Capture person_table_key = the original key used in population.tables for 
the person entity (found in step 3). This key is the prefix for all person instance IDs.
```

---

### 3. Missing documentation: how to extract `person_table` from `population.tables`

**Benefit:** Eliminates a gap in the algorithm that a developer must independently solve, risking an incorrect implementation.
**Source:** Task 1.1, Dev Notes Algorithm step 3

**Current Gap:**
The algorithm (Dev Notes) shows:
```
3. Call _detect_membership_columns(person_table, tbs)
```

But `person_table` is never shown being extracted from `population`. The method's parameter signature says it takes `person_table: pa.Table` and `tbs: Any`, but the calling code must first find which table in `population.tables` is the person entity. The existing code already identifies the person entity plural:
```python
for entity in tbs.entities:
    if not getattr(entity, "is_person", False):
        continue
    person_entity_plural = entity.plural
    break
```
But there's no code showing how to then find the corresponding table in `population.tables` (the user might pass `"individu"` or `"individus"` as the key).

**Suggested Addition:**
Add to the algorithm or to Task 1.1's documentation:
```python
# How to find person_table inside _population_to_entity_dict():
person_entity = next(
    (e for e in tbs.entities if getattr(e, "is_person", False)), None
)
# Find person table key — user may pass singular or plural
person_table_key = next(
    (k for k in population.tables 
     if k == person_entity.key or k == person_entity.plural),
    None
)
if person_table_key is None:
    # No person entity table → backward-compatible path (no membership cols possible)
    membership_cols = {}
else:
    person_table = population.tables[person_table_key]
    membership_cols = self._detect_membership_columns(person_table, tbs)
```

Also add as **edge case #6**: "No person entity table in population.tables → `_detect_membership_columns()` returns empty dict immediately (backward-compatible: treat as no-membership-column mode)."

---

### 4. Story 9.3 merge conflict risk not documented

**Benefit:** Prevents a developer from starting Story 9.4 work that will create avoidable merge conflicts with the actively-in-progress Story 9.3.
**Source:** Story 9.3 Status = "in-progress", Story 9.4 Status = "ready-for-dev"

**Current Gap:**
Story 9.3 is currently in-progress and modifies `src/reformlab/computation/openfisca_api_adapter.py` (multiple methods). Story 9.4 also modifies this file (adds 3 new methods, refactors `_population_to_entity_dict()`). Although the method-level conflict is limited (9.3 modifies `compute()`, `_extract_results_by_entity()`, `_calculate_variable()`, and `_resolve_variable_periodicities()`; 9.4 modifies `_population_to_entity_dict()` and adds new methods), the file-level overlap will produce merge conflicts in import ordering, class structure, and potentially `_build_simulation()`.

Additionally, Story 9.3's code review notes added `_periodicity_to_method_name()` as a module-level helper — the developer of Story 9.4 needs to be aware of the file state they'll be working against.

**Suggested Addition:**
Add to Dev Notes under a "Prerequisites and Merge Strategy" subsection:
```
⚠️ Story 9.3 is currently in-progress and modifies openfisca_api_adapter.py.
Story 9.4 should NOT be started until Story 9.3 is merged to main.
If concurrent development is unavoidable, develop Story 9.4 on a branch 
that tracks Story 9.3's branch and rebase before PR.

After Story 9.3 merges, Story 9.4's _population_to_entity_dict() is unchanged
(Story 9.3 does not modify this method). The new methods added by Story 9.4
(_detect_membership_columns, _resolve_valid_role_keys, _validate_entity_relationships)
are entirely additive.
```

---

### 5. AC-7 positional merge algorithm risk understated

**Benefit:** Prevents silent data corruption when group entity tables have rows in unexpected order.
**Source:** Task 4.6, Edge Cases section

**Current Gap:**
Task 4.6 says: "Match group table row index to group instance by sorted order of distinct group IDs from the person table's `_id` column."

This positional matching is fragile:
- If `famille_id = [5, 5, 12]` → sorted distinct IDs = [5, 12] → famille table row 0 → `famille_5`, row 1 → `famille_12`
- If the group entity table was constructed in a different order (e.g., row 0 = data for famille_12, row 1 = data for famille_5), data is silently assigned to the wrong group

The edge case section mentions "Raise `ApiMappingError` if the group entity table row count doesn't match the number of distinct group IDs" but says nothing about row ORDER validation.

**Suggested Addition:**
In Task 4.6, add a warning:
```
⚠️ POSITIONAL MATCHING WARNING: Row 0 of the group entity table is matched to the 
smallest group ID, row 1 to the second-smallest, etc. This requires the group entity 
table rows to be ordered by ascending group ID value. If the group entity table was 
constructed in a different order, values will be silently misassigned.

Consider adding a note to PopulationData's docstring when group entity tables are 
provided: rows must be ordered by ascending {entity_key}_id value as it appears in 
the person table's _id column.

Unit test to add: Verify that non-contiguous sorted IDs ([0, 2]) correctly map
row 0 → groupe_0, row 1 → groupe_2 and NOT the reverse.
```

---

### 6. AC-7 integration test coverage gap: Verify computation result, not just entity dict

**Benefit:** The integration test for AC-7 (Task 6.4) only verifies the entity dict is built — not that the computation produces meaningful output with the group-level variable.
**Source:** Task 6.4, AC-7 description

**Current Gap:**
Task 6.4 says: "Verify the value appears in the entity dict and is passable to `build_from_entities()`". This is scoped correctly (to avoid the input period-format limitation for monthly variables like `loyer`), but the test doesn't verify that `adapter.compute()` succeeds end-to-end when a group entity table is provided. A developer could pass an entity dict with a malformed `loyer` assignment that `build_from_entities()` silently ignores.

**Suggested Addition:**
In Task 6.4, add:
```python
# At minimum, verify compute() completes without error when a group entity table 
# is provided (even if we don't assert the loyer computation result):
result = adapter.compute(population, policy, 2024)
assert isinstance(result, ComputationResult)
assert result.output_fields.num_rows > 0
# If testing loyer-dependent output, use a yearly variable that depends on loyer
# (e.g., aide_logement) — not loyer itself (monthly variable, period mismatch limitation)
```

---

## ✨ Optimizations (Nice to Have)

### 1. Explicitly show `import pyarrow.compute as pc` pattern

**Value:** Avoids a developer using `pa.compute.is_null()` when the standard project pattern might prefer explicit submodule import.

**Suggestion:**
Task 3.2 references `pa.compute.is_null()`. In PyArrow ≥18, both `pa.compute.is_null(array)` and `import pyarrow.compute as pc; pc.is_null(array)` work. The project context says "no wildcard imports" — using `import pyarrow.compute as pc` is more explicit and follows the project's import hygiene. Add a note:
```python
# Null detection in PyArrow — use explicit submodule import:
import pyarrow.compute as pc
null_mask = pc.is_null(table.column(col_name))  # Returns BooleanArray
if pc.any(null_mask).as_py():
    first_null_idx = pc.list_flatten(pc.indices_nonzero(null_mask)).as_py()[0]
    raise ApiMappingError(...)
```

### 2. Specify `ABSOLUTE_ERROR_MARGIN` for new integration tests

**Value:** Ensures new integration tests use consistent tolerances with the existing reference suite.

**Suggestion:**
In Task 6.1, note: "Use the same `ABSOLUTE_ERROR_MARGIN = 0.5` as in `TestOpenFiscaFranceReferenceCases`. Add this as a class attribute in the new `TestPopulationData4EntityFormat` integration test class."

### 3. Clarify `pa.compute.unique()` for distinct group ID extraction

**Value:** Slightly more efficient and idiomatic PyArrow for the Task 4.5 "sorted distinct group IDs" step.

**Suggestion:**
```python
# More efficient than to_pylist() + set() + sorted():
id_column = person_table.column(f"{entity_key}_id")
unique_ids = pa.compute.unique(id_column).to_pylist()
sorted_group_ids = sorted(unique_ids)
```

---

## 🤖 LLM Optimization Improvements

### 1. Algorithm pseudocode references "(existing)" without sufficient clarity

**Issue:** Ambiguity
**Token Impact:** Medium — the phrase "(existing)" in the pseudocode creates ambiguity that causes a developer to re-read prior story context to understand what to preserve.

**Current:**
```
1. Build key→plural mapping (existing)
2. Identify person entity (existing)
3. Call _detect_membership_columns(person_table, tbs)
4. IF no membership columns → execute EXISTING code path unchanged
```

**Optimized:**
```
1. Build key→plural mapping: {entity.key: entity.plural for entity in tbs.entities} [UNCHANGED]
2. Identify person entity: next(e for e in tbs.entities if e.is_person) [UNCHANGED]
2b. Find person_table_key in population.tables (key matching person.key or person.plural)
    If not found → return existing all-table loop result (backward-compatible)
3. Call _detect_membership_columns(population.tables[person_table_key], tbs)
4. IF empty dict returned → execute lines 538-569 of current _population_to_entity_dict() UNCHANGED
```

**Rationale:** Removes ambiguity about what "existing" means and what to preserve.

---

### 2. Edge case #3 ("Empty group") has contradictory logic

**Issue:** Contradictory statements confuse the developer.
**Token Impact:** Low — but the contradiction creates unnecessary parsing overhead.

**Current:**
```
Empty group — a group ID that appears in no person's _id column. This can't happen 
by construction (groups are discovered from person table), but if a group entity table 
has more rows than distinct group IDs from the person table, the extra rows are orphaned. 
Raise ApiMappingError.
```

**Optimized:**
```
Extra rows in group entity table — if population.tables["menage"] has 3 rows but 
the person table's menage_id column only has 2 distinct values, the 3rd row is 
unmatched. Raise ApiMappingError with summary "Group entity table row count mismatch":
reason=f"menage table has {table.num_rows} rows but only {len(distinct_ids)} distinct 
menage_id values in person table", fix="Ensure group entity table has exactly one 
row per distinct {entity_key}_id value"
```

**Rationale:** Removes the contradictory "can't happen by construction / raise ApiMappingError" framing. It CAN happen (user passes mismatched tables), so just state what to do.

---

## 📝 Changes Applied

No changes were applied to the story file. This report serves as documentation only.

---

## 🏆 Competition Results

### Quality Metrics

| Metric | Score |
|--------|-------|
| Requirements Coverage | 95% |
| Architecture Alignment | 98% |
| Previous Story Integration | 90% |
| LLM Optimization Score | 72% |
| **Overall Quality Score** | **89%** |

### Disaster Prevention Assessment

- **Reinvention Prevention:** ✅ Clean — story correctly reuses `ApiMappingError`, existing entity discovery patterns, and PyArrow patterns. No wheel reinvention risk.
- **Technical Specification:** ⚠️ Moderate risk — role system is documented accurately, but the interaction between the all-tables iteration loop and 4-entity mode group entity tables is ambiguous enough to cause a real implementation error.
- **File Structure:** ✅ Clean — correct files identified, test structure aligned with project conventions.
- **Regression Prevention:** ⚠️ Moderate risk — Story 9.3 merge conflict risk not documented; instance ID prefix ambiguity could cause subtle bugs in group membership assignment.
- **Implementation Clarity:** ⚠️ Moderate risk — Task 4.5's hardcoded `"individu_0"` example contradicts the Dev Notes' explanation of how instance IDs are derived.

### Competition Outcome

🏆 **Validator identified 11 improvements** across 6 enhancements, 3 optimizations, and 2 LLM optimizations that would meaningfully reduce developer confusion on the most complex aspects of this story.

The original create-story did excellent work on: role table documentation, backward compatibility strategy, mock TBS extension pattern, and the complete 3-example format specification. The gaps are concentrated in the algorithm pseudocode section where interactions between old and new code paths are underspecified.

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
<var name="session_id">329799e0-5fd6-43db-9378-537a818c719f</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_file" file_id="bc34e66e">embedded in prompt, file id: bc34e66e</var>
<var name="story_id">9.4</var>
<var name="story_key">9-4-define-population-data-4-entity-format</var>
<var name="story_num">4</var>
<var name="story_title">define-population-data-4-entity-format</var>
<var name="template">False</var>
<var name="timestamp">20260301_2220</var>
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