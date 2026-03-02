# Story 10.1: Rename `parameters` to `policy` on scenario types

Status: done

## Story

As a policy analyst or developer,
I want the scenario API to use `policy` instead of `parameters` as the field name for policy configuration objects,
so that the naming is semantically consistent with the domain (policies, not parameters) and the API is more intuitive.

## Acceptance Criteria

1. Given `BaselineScenario(policy=my_policy)`, when constructed, then the policy object is stored and accessible via `.policy`.
2. Given all YAML pack files, when loaded, then they use the `policy:` key exclusively (no backward compat — clean rename).
3. Given the JSON schema for scenario templates, when updated, then it uses `policy` as the field name (replacing `parameters`).
4. Given all tests, when run, then they pass with the renamed field.

## Tasks / Subtasks

- [x] Task 1: Rename `parameters` field to `policy` on core schema types (AC: #1)
  - [x] 1.1 `ScenarioTemplate.parameters` -> `ScenarioTemplate.policy` in `src/reformlab/templates/schema.py`
  - [x] 1.2 `ReformScenario.parameters` -> `ReformScenario.policy` in `src/reformlab/templates/schema.py`
  - [x] 1.3 `BaselineScenario` inherits the change from `ScenarioTemplate`
  - [x] 1.4 Update all references to `.parameters` on scenario objects throughout codebase

- [x] Task 2: Rename `parameters` field on API/server types (AC: #1, #4)
  - [x] 2.1 `ScenarioConfig.parameters` -> `ScenarioConfig.policy` in `src/reformlab/interfaces/api.py`
  - [x] 2.2 `PolicyConfig.parameters` -> `PolicyConfig.policy` in `src/reformlab/computation/types.py` and `.pyi`
  - [x] 2.3 `RunManifest.parameters` -> `RunManifest.policy` in `src/reformlab/governance/manifest.py` (update `REQUIRED_JSON_FIELDS` tuple too)
  - [x] 2.4 Rename all `parameters` fields in Pydantic models in `src/reformlab/server/models.py`:
    - `RunRequest.parameters` -> `RunRequest.policy`
    - `MemoryCheckRequest.parameters` -> `MemoryCheckRequest.policy`
    - `CreateScenarioRequest.parameters` -> `CreateScenarioRequest.policy`
    - `ScenarioResponse.parameters` -> `ScenarioResponse.policy`
    - `TemplateDetailResponse.default_parameters` -> `TemplateDetailResponse.default_policy`

- [x] Task 3: Update function signatures and internal references (AC: #4)
  - [x] 3.1 `_parse_parameters()` -> `_parse_policy()` in `src/reformlab/templates/loader.py`
  - [x] 3.2 `_parameters_to_dict()` -> `_policy_to_dict()` in `src/reformlab/templates/loader.py`
  - [x] 3.3 `_dict_to_parameters()` -> `_dict_to_policy()` in `src/reformlab/templates/registry.py`
  - [x] 3.4 `_merge_parameters()` -> `_merge_policy()` in `src/reformlab/templates/reform.py`
  - [x] 3.5 `capture_parameters()` -> `capture_policy()` in `src/reformlab/governance/capture.py`
  - [x] 3.6 Rename `parameters` parameter/attribute in `OrchestratorRunner.__init__()` and `run()` in `src/reformlab/orchestrator/runner.py`
  - [x] 3.7 Update all `compute_*()` function signatures in template compute modules (parameter name `parameters` -> `policy`):
    - `src/reformlab/templates/carbon_tax/compute.py`
    - `src/reformlab/templates/subsidy/compute.py`
    - `src/reformlab/templates/rebate/compute.py`
    - `src/reformlab/templates/feebate/compute.py`
  - [x] 3.8 Update all `compare.py` modules that reference `scenario.parameters`

- [x] Task 4: Update server routes and API wiring (AC: #4)
  - [x] 4.1 Update all route handlers in `src/reformlab/server/routes/` that reference `.parameters` fields
  - [x] 4.2 Update `src/reformlab/interfaces/api.py` internal logic (e.g., `run_scenario()`, `create_scenario()`)

- [x] Task 5: Update JSON schema (AC: #3)
  - [x] 5.1 Rename `parameters` to `policy` in JSON schemas in `src/reformlab/templates/schema/`

- [x] Task 6: Update YAML pack files to use `policy:` (AC: #2)
  - [x] 6.1 Update all template pack YAML files in `src/reformlab/templates/packs/`:
    - `carbon_tax/carbon-tax-flat-no-redistribution.yaml`
    - `carbon_tax/carbon-tax-flat-lump-sum-dividend.yaml`
    - `carbon_tax/carbon-tax-flat-progressive-dividend.yaml`
    - `carbon_tax/carbon-tax-progressive-no-redistribution.yaml`
    - `carbon_tax/carbon-tax-progressive-progressive-dividend.yaml`
    - `subsidy/subsidy-energy-retrofit.yaml`
    - `rebate/rebate-progressive-income.yaml`
    - `feebate/feebate-vehicle-emissions.yaml`

- [x] Task 7: Update test fixtures and test code (AC: #4)
  - [x] 7.1 Update golden YAML fixtures in `tests/fixtures/templates/` (`golden-carbon-tax.yaml`, `golden-reform.yaml`)
  - [x] 7.2 Update all test files that reference `.parameters` on scenario objects

- [x] Task 8: Update notebooks (AC: #4)
  - [x] 8.1 Update `notebooks/quickstart.ipynb` — replace `parameters` references with `policy`
  - [x] 8.2 Update `notebooks/advanced.ipynb` — replace `parameters` references with `policy`

- [x] Task 9: Run full test suite and lint (AC: #4)
  - [x] 9.1 `uv run pytest tests/`
  - [x] 9.2 `uv run ruff check src/ tests/`
  - [x] 9.3 `uv run mypy src/`

## Dev Notes

### Scope Clarification

This story renames the `parameters` **field** on scenario/template types to `policy`. It does **NOT** rename the parameter **classes** themselves (`PolicyParameters`, `CarbonTaxParameters`, etc.) — that is a separate consideration for Story 10.2 or beyond.

The key distinction:
- **Field rename** (this story): `scenario.parameters` -> `scenario.policy`
- **Class rename** (NOT this story): `CarbonTaxParameters` class name stays as-is

### Important: VintageTransitionRule.parameters is OUT OF SCOPE

`VintageTransitionRule.parameters` in `src/reformlab/vintage/config.py` uses `parameters` with a different semantic meaning — it refers to rule-specific configuration (count, rate, max_age), not policy parameters. Do NOT rename this field. It should remain `parameters` (or be renamed to `config` in a separate story if desired).

### No Backward Compatibility

This is a clean rename — no dual-key support, no deprecation warnings. The project is early-stage with no external consumers. All YAML files, JSON schemas, and code use `policy` exclusively after this story.

### Frozen Dataclass Rename Pattern

Since all types use `@dataclass(frozen=True)`, the rename is a field name change. Use find-and-replace carefully:
- Replace `parameters: PolicyParameters` with `policy: PolicyParameters` in dataclass field definitions
- Replace `.parameters` attribute access with `.policy` on scenario instances
- Replace `parameters=` keyword argument with `policy=` in constructors

### Files to Modify (Complete List)

**Source files (15+ files):**
- `src/reformlab/templates/schema.py` — core type definitions
- `src/reformlab/templates/loader.py` — YAML loading
- `src/reformlab/templates/registry.py` — scenario registry
- `src/reformlab/templates/reform.py` — reform merge logic
- `src/reformlab/templates/__init__.py` — re-exports (verify)
- `src/reformlab/templates/carbon_tax/compute.py` — compute functions
- `src/reformlab/templates/carbon_tax/compare.py` — comparison
- `src/reformlab/templates/subsidy/compute.py`
- `src/reformlab/templates/rebate/compute.py`
- `src/reformlab/templates/feebate/compute.py`
- `src/reformlab/computation/types.py` and `.pyi` — PolicyConfig
- `src/reformlab/interfaces/api.py` — public API
- `src/reformlab/governance/manifest.py` — RunManifest
- `src/reformlab/governance/capture.py` — capture function
- `src/reformlab/orchestrator/runner.py` — OrchestratorRunner
- `src/reformlab/server/models.py` — Pydantic models
- `src/reformlab/server/routes/*.py` — route handlers

**YAML files (10 files):**
- 5 carbon tax pack YAMLs
- 1 subsidy pack YAML
- 1 rebate pack YAML
- 1 feebate pack YAML
- 2 golden test fixture YAMLs

**JSON schema files:**
- `src/reformlab/templates/schema/*.json` — rename `parameters` to `policy`

**Test files (many):**
- All test files referencing `.parameters` on scenario objects
- All test files constructing scenarios with `parameters=`

**Notebooks (2):**
- `notebooks/quickstart.ipynb`
- `notebooks/advanced.ipynb`

### Execution Order

Recommended implementation order to minimize breakage during development:

1. **Schema types first** (Task 1) — change the field definitions
2. **Internal functions** (Task 3) — update function signatures
3. **API/server types** (Tasks 2, 4) — update HTTP layer
4. **JSON schema** (Task 5) — update validation schemas
5. **YAML packs** (Task 6) — update shipped templates
6. **Tests** (Task 7) — update test code and fixtures
7. **Notebooks** (Task 8) — update user-facing notebooks
8. **Full validation** (Task 9) — run pytest, ruff, mypy

### Key Pattern: Search and Replace

For efficient implementation, use these search patterns:
- `\.parameters` -> `.policy` (attribute access on scenario objects)
- `parameters:` (in YAML context) -> `policy:`
- `parameters=` (in Python constructor calls) -> `policy=`
- `"parameters"` (in dict keys/JSON fields) -> `"policy"`

**But be careful to exclude:**
- `VintageTransitionRule.parameters` — different meaning
- `PolicyParameters` class name — out of scope
- `CarbonTaxParameters`, `SubsidyParameters`, etc. class names — out of scope
- Import statements for parameter classes — out of scope
- Docstring/comment references to "parameters" as a general concept vs. the specific field name

### Project Structure Notes

- All source code follows `src/reformlab/` layout
- Tests mirror source: `tests/{subsystem}/`
- Template packs: `src/reformlab/templates/packs/{policy_type}/`
- JSON schemas: `src/reformlab/templates/schema/`
- Test fixtures: `tests/fixtures/templates/`
- No changes to `__init__.py` exports unless they re-export the field name

### Testing Standards

- Use `uv run pytest tests/` for test execution
- Use `uv run ruff check src/ tests/` for linting
- Use `uv run mypy src/` for type checking
- All three must pass cleanly before story completion

### References

- [Source: _bmad-output/planning-artifacts/epics.md#EPIC-10] — Story definition and acceptance criteria
- [Source: _bmad-output/planning-artifacts/architecture.md#Subsystems] — Template packs, schema, loader architecture
- [Source: _bmad-output/planning-artifacts/architecture.md#API-Design] — Server models and route contracts
- [Source: _bmad-output/project-context.md] — Frozen dataclass pattern, adapter isolation, testing conventions
- [Source: src/reformlab/templates/schema.py] — Core type definitions with `parameters` field
- [Source: src/reformlab/server/models.py] — Pydantic request/response models
- [Source: src/reformlab/governance/manifest.py] — RunManifest with `parameters` field

## Senior Developer Review (AI)

### Review: 2026-03-02
- **Reviewer:** AI Code Review Engine
- **Evidence Score:** 2.7 → APPROVED
- **Issues Found:** 9
- **Issues Fixed:** 9
- **Action Items Created:** 0

#### Issues Fixed by Review
1. README code example: `parameters=template.policy` → `policy=template.policy` (`packs/carbon_tax/README.md:121`)
2. Stale docstring in `reproducibility.py:74,79`: `parameters` → `policy` in rerun_callable contract
3. Stale local variable `parameters` → `policy_dict` in `interfaces/api.py:1029`
4. Stale private function `_normalize_parameters` → `_normalize_policy` in `interfaces/api.py:1166`
5. Stale local variable `parameters` → `policy_snapshot` in `orchestrator/runner.py:603`
6. Stale local variable `parameters` → `parsed_policy` in `templates/loader.py:175`
7. Stale comment "Extract parameters as dict" → "Extract policy as dict" in `routes/scenarios.py:30`
8. Stale comment "Build typed parameters" → "Build typed policy" in `routes/scenarios.py:115`
9. Stale comments "Count parameters" / "Extract default parameters" → updated in `routes/templates.py:35,60`

#### Notes
- Story 10-2 changes (infer_policy_type, optional policy_type) are co-mingled in the same uncommitted batch — not a blocker but noted for traceability.
- 4 pre-existing mypy errors (unrelated to this story) remain.
- 1 pre-existing test_memory.py failure (machine-specific available memory check) is unrelated.

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
