---
title: 'Integration Hardening — Cross-Epic Wiring Gaps'
slug: 'integration-hardening'
created: '2026-03-21'
status: 'draft'
tech_stack: ['Python 3.13+', 'FastAPI', 'PyArrow', 'React 19', 'TypeScript']
files_to_modify:
  - 'src/reformlab/server/routes/runs.py'
  - 'src/reformlab/server/dependencies.py'
  - 'src/reformlab/data/synthetic.py'
  - 'src/reformlab/data/schemas.py'
  - 'src/reformlab/computation/types.py'
  - 'src/reformlab/server/routes/templates.py'
  - 'src/reformlab/server/models.py'
  - 'frontend/src/api/templates.ts'
  - 'frontend/src/api/types.ts'
  - 'frontend/src/components/screens/TemplateSelectionScreen.tsx'
---

# Tech-Spec: Integration Hardening — Cross-Epic Wiring Gaps

**Created:** 2026-03-21

## Overview

### Problem Statement

Features were built across 17 independent epics. An adversarial integration review (2026-03-20) found 4 gaps where independently-built layers don't actually connect end-to-end. Each piece works in isolation and passes its own tests, but the full pipeline breaks at integration boundaries.

### Findings Addressed

| ID | Gap | Severity |
|----|-----|----------|
| F3 | Portfolio execution path: `portfolio_name` is metadata-only, never triggers multi-policy orchestration | Blocking |
| F4 | Synthetic population produces zero carbon tax burden (missing energy columns, silently filled with zeros) | High |
| F5 | No standard `PopulationData` wrapping — ad-hoc entity keys at every boundary | Medium |
| F8 | Custom templates (Epic 13) have no GUI — breaks no-code promise | Medium |

### Solution

Four focused stories, each closing one integration gap. No new architecture — just wiring existing pieces together.

## Story 1: Wire Portfolio Execution into Run Endpoint

### Problem

`POST /api/runs` accepts `portfolio_name` in `RunRequest` (models.py:30), and `PortfolioComputationStep` exists (orchestrator/portfolio_step.py), but no code in the endpoint loads the portfolio from registry or constructs the step. The `portfolio_name` field is metadata-only — it labels the run but portfolios execute as single-policy simulations.

### What Exists

- `PortfolioComputationStep` — fully implemented, takes adapter + population + `PolicyPortfolio`, merges multi-policy results by `household_id`
- `ScenarioRegistry` — stores/retrieves portfolios by name via `registry.get(name)`
- `RunRequest.portfolio_name` — accepted but ignored for execution
- Portfolio CRUD endpoints — fully working (create, validate, clone, update, delete)

### Changes Required

**`src/reformlab/server/routes/runs.py`:**
1. Inject `ScenarioRegistry` as a dependency (via `dependencies.py`)
2. Add conditional dispatch in `run_simulation()`:
   - If `portfolio_name` provided → `registry.get(portfolio_name)` → construct `PortfolioComputationStep` → execute via orchestrator
   - If `template_name` provided → existing `run_scenario()` path (unchanged)
   - If both provided → 422 error ("specify portfolio_name or template_name, not both")
3. Populate `ResultMetadata` with portfolio provenance (policy count, resolution strategy)

**`src/reformlab/server/dependencies.py`:**
- Add `get_registry()` dependency that returns the singleton `ScenarioRegistry`

### Acceptance Criteria

- [ ] `POST /api/runs` with `portfolio_name` loads portfolio from registry and executes all policies via `PortfolioComputationStep`
- [ ] Result metadata records portfolio name, policy count, and resolution strategy
- [ ] 404 if portfolio_name not found in registry
- [ ] 422 if both portfolio_name and template_name provided
- [ ] Existing template_name-based runs unchanged (regression test)
- [ ] Integration test: create portfolio via API → execute via run endpoint → verify multi-policy results merged

### Files to Modify

- `src/reformlab/server/routes/runs.py` — conditional dispatch logic
- `src/reformlab/server/dependencies.py` — registry dependency
- `tests/server/test_runs.py` — integration tests for portfolio execution

---

## Story 2: Fix Synthetic Population for Carbon Tax Computation

### Problem

`generate_synthetic_population()` produces only `household_id`, `income`, `carbon_emissions`. The carbon tax template expects `energy_transport_fuel`, `energy_heating_fuel`, `energy_natural_gas`. The gap is masked by `fill_missing_energy_columns()` which silently appends zeros — producing zero tax burden for every household.

The `carbon_emissions` column is never consumed by any downstream code. It's a dead column.

### What Exists

- `generate_synthetic_population()` (data/synthetic.py) — income-correlated `carbon_emissions` aggregate
- `SYNTHETIC_POPULATION_SCHEMA` (data/schemas.py) — defines energy columns as optional
- `fill_missing_energy_columns()` (data/schemas.py) — silent zero-fill
- `compute_tax_burden()` (templates/carbon_tax/compute.py) — multiplies energy × emission_factor × rate

### Changes Required

**`src/reformlab/data/synthetic.py`:**
1. Replace `carbon_emissions` with 3 energy columns: `energy_transport_fuel`, `energy_heating_fuel`, `energy_natural_gas`
2. Generate realistic synthetic values correlated with income:
   - Transport fuel: 500–1500 liters/year (higher income → more driving)
   - Heating fuel: 200–800 liters/year (random, weakly income-correlated)
   - Natural gas: 300–1200 m³/year (random, weakly income-correlated)
3. Add `person_id` column (= `household_id` for single-person simplification)
4. Add `age` column (uniform 20–80, for schema compliance)

**`src/reformlab/data/schemas.py`:**
1. Promote energy columns from optional to required in `SYNTHETIC_POPULATION_SCHEMA`
2. Add a warning log in `fill_missing_energy_columns()` when it fills zeros (don't remove the function — external data may still need it, but make the silent behavior visible)

### Acceptance Criteria

- [ ] `generate_synthetic_population()` produces all 4 required columns (`household_id`, `person_id`, `age`, `income`) plus 3 energy columns
- [ ] Carbon tax computation on synthetic population produces non-zero, income-correlated tax burdens
- [ ] `fill_missing_energy_columns()` logs a warning when it fills zeros
- [ ] Quickstart notebook runs end-to-end with non-zero results
- [ ] Existing tests updated for new column set
- [ ] `carbon_emissions` column removed (dead code)

### Files to Modify

- `src/reformlab/data/synthetic.py` — generation logic
- `src/reformlab/data/schemas.py` — schema + warning
- `tests/data/test_synthetic.py` — updated column assertions
- `tests/benchmarks/conftest.py` — uses `generate_synthetic_population()`
- `notebooks/` — any notebook using synthetic data

---

## Story 3: Standardize PopulationData Wrapping

### Problem

Three different population representations exist with no conversion:
- **Data layer** (`load_dataset`) → flat `pa.Table`
- **Orchestrator** (`ComputationStep`) → `PopulationData(tables={"entity_key": pa.Table})`
- **Templates** (`compute_tax_burden`) → flat `pa.Table`

Each integration point constructs `PopulationData` ad-hoc with inconsistent entity keys (`"default"`, `"individu"`, `"menage"`). Adapters must guess which key to use.

### Changes Required

**`src/reformlab/computation/types.py`:**
1. Add `PopulationData.from_table(table, entity_type="default")` classmethod — canonical way to wrap a flat table
2. Add `PopulationData.primary_table` property — returns the first (or only) table, regardless of key name
3. Document that `"default"` is the standard key for single-entity populations

**`src/reformlab/data/pipeline.py`:**
1. Add `load_population(path, schema, source) -> PopulationData` convenience function that calls `load_dataset()` and wraps result via `PopulationData.from_table()`

**Adapters** (openfisca_adapter.py, mock_adapter.py):
1. Use `population.primary_table` instead of indexing by hardcoded key

### Acceptance Criteria

- [ ] `PopulationData.from_table()` classmethod exists with `entity_type` parameter (default: `"default"`)
- [ ] `PopulationData.primary_table` property returns the single/first table
- [ ] `load_population()` convenience function returns `PopulationData` directly
- [ ] All adapter implementations use `primary_table` instead of key lookups
- [ ] Existing tests pass without changes (backward-compatible)

### Files to Modify

- `src/reformlab/computation/types.py` — classmethod + property
- `src/reformlab/data/pipeline.py` — convenience wrapper
- `src/reformlab/computation/openfisca_adapter.py` — use `primary_table`
- `src/reformlab/computation/mock_adapter.py` — use `primary_table`
- `tests/computation/` — test new API

---

## Story 4: Custom Template CRUD Endpoints + Minimal GUI

### Problem

Custom templates (Epic 13) work via Python API (`register_policy_type()` + `register_custom_template()`), but:
- Backend has only read-only template endpoints (`GET /api/templates`, `GET /api/templates/{name}`)
- No HTTP endpoint to register/create custom types dynamically
- Frontend has no template authoring UI — only browsing
- Custom templates can be used in scenarios and portfolios once registered, but can't be created from the GUI

### What Exists

- Python registration API: `register_policy_type()`, `register_custom_template()` in `templates/schema.py`
- Template listing/detail endpoints: `GET /api/templates`, `GET /api/templates/{name}`
- Full CRUD for scenarios and portfolios that reference templates
- Notebook guide: `notebooks/guides/07_custom_templates.ipynb`

### Changes Required

**Backend — `src/reformlab/server/routes/templates.py`:**
1. `POST /api/templates/custom` — register custom template with name, description, parameter schema (field names, types, defaults, units)
2. `DELETE /api/templates/custom/{name}` — unregister custom template
3. Validation: reject names that collide with built-in types, enforce snake_case naming
4. Custom templates persist in `ScenarioRegistry` so they survive restarts

**Backend — `src/reformlab/server/models.py`:**
1. `CreateCustomTemplateRequest` — name, description, parameters (list of `{name, type, default, unit, min, max}`)
2. `CustomTemplateResponse` — confirmation with generated parameter class info

**Frontend — `frontend/src/api/templates.ts`:**
1. `createCustomTemplate(req)` — POST to new endpoint
2. `deleteCustomTemplate(name)` — DELETE

**Frontend — `frontend/src/api/types.ts`:**
1. `CreateCustomTemplateRequest` interface
2. Add `is_custom: boolean` to `TemplateListItem`

**Frontend — minimal UI:**
1. Add "Create Custom Template" button to template selection screen
2. Simple dialog: name, description, parameter list (add/remove rows with name/type/default/unit fields)
3. Distinguish custom vs built-in templates in listing (badge or icon)

### Acceptance Criteria

- [ ] `POST /api/templates/custom` creates a custom template with parameter schema
- [ ] Created template appears in `GET /api/templates` listing with `is_custom: true`
- [ ] Created template usable in scenario creation and portfolio composition
- [ ] `DELETE /api/templates/custom/{name}` removes custom template (404 if not found, 409 if in use by scenarios/portfolios)
- [ ] Frontend shows "Create Custom Template" button with dialog form
- [ ] Custom templates visually distinguished in template list
- [ ] Built-in templates cannot be deleted (403)

### Files to Modify

- `src/reformlab/server/routes/templates.py` — CRUD endpoints
- `src/reformlab/server/models.py` — request/response models
- `src/reformlab/templates/schema.py` — persistence of custom registrations
- `frontend/src/api/templates.ts` — API calls
- `frontend/src/api/types.ts` — type definitions
- `frontend/src/components/screens/TemplateSelectionScreen.tsx` — create button + dialog
- `tests/server/test_templates.py` — endpoint tests

---

## Implementation Order

1. **Story 3** (PopulationData wrapping) — smallest scope, unblocks cleaner code in other stories
2. **Story 2** (Synthetic population fix) — high impact, standalone
3. **Story 1** (Portfolio execution wiring) — blocking feature gap
4. **Story 4** (Custom template GUI) — largest scope, least urgent

Stories 1–3 are independent and can be parallelized. Story 4 is standalone.

## Additional Context

### What Was Already Fixed (2026-03-20)

- **F1**: `ScenarioResponse.parameters` → `policy` field name mismatch in `frontend/src/api/types.ts:97` — fixed
- **F2**: `TemplateDetailResponse.default_parameters` → `default_policy` field name mismatch in `frontend/src/api/types.ts:112` and `frontend/src/hooks/useApi.ts:156` — fixed
- Both fixes verified with `npm run typecheck` (clean)

### Deferred Findings (see `integration-review-deferred.md`)

Findings F6, F7, F9–F12 are documented as known limitations. They don't break current functionality and are not worth implementing now.
