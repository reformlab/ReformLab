# Epic 20: Stage-Based Scenario Workspace Alignment

**User outcome:** Analyst works inside one coherent five-stage workspace where policies, populations, investment decisions, scenarios, runs, and comparisons are clearly separated, first-run onboarding is instant, and execution is guarded by cross-stage validation.

**Status:** backlog

**Builds on:** EPIC-11 (populations), EPIC-12 (portfolios), EPIC-14 (behavioral decisions), EPIC-15 (calibration), EPIC-17 (GUI showcase), EPIC-18 (UX overhaul)

**PRD Refs:** FR3, FR4, FR25-FR29, FR32, FR37-FR45, FR47-FR53

**Primary source documents:**
- `_bmad-output/planning-artifacts/ux-design-specification.md` (Revision 4.1, dated 2026-04-01)
- `_bmad-output/planning-artifacts/prd.md` (Current Program State Update, dated 2026-03-24)
- `_bmad-output/planning-artifacts/architecture.md` (frontend/API alignment update, dated 2026-04-01)
- `_bmad-output/implementation-artifacts/epic-20-stage-based-scenario-workspace-alignment.md`

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-2001 | Story | P0 | 5 | Implement canonical scenario model and stage-aware routing shell | backlog | FR32, FR28, FR29 |
| BKL-2002 | Story | P0 | 3 | Add pre-seeded demo-scenario onboarding and scenario entry flows | backlog | FR32, FR34 |
| BKL-2003 | Story | P0 | 5 | Build Policies & Portfolio stage with inline composition | backlog | FR43, FR44 |
| BKL-2004 | Story | P0 | 8 | Build Population Library and Data Explorer stage | backlog | FR37-FR42 |
| BKL-2005 | Story | P0 | 8 | Build Scenario stage with inherited population context, simulation-mode controls, and cross-stage validation gate | backlog | FR3, FR4, FR25-FR29, FR47-FR53 |
| BKL-2006 | Story | P0 | 5 | Refactor Run / Results / Compare around scenario-by-population execution | backlog | FR32, FR45 |
| BKL-2007 | Task | P0 | 5 | Extend backend APIs for population explorer and execution-contract validation | backlog | FR3, FR4, FR37-FR42 |
| BKL-2008 | Story | P1 | 3 | Add end-to-end regression coverage and sync product docs to the new IA | backlog | FR32, FR34, FR35 |

## Epic-Level Acceptance Criteria

- The GUI uses a five-stage shell: Policies, Population, Investment Decisions, Scenario, Run / Results / Compare.
- `Scenario` is the durable analysis object that binds policy set, population selection, simulation settings, mappings, and metadata.
- First launch opens a valid demo scenario with Run enabled while keeping Stages 1-4 inspectable and editable.
- Stage 4 performs cross-stage validation before execution, including population schema compatibility, mapping completeness, year-schedule coverage, simulation-mode support, and runtime preflight.
- Stage 5 executes a scenario-by-population run matrix and preserves scenario lineage through comparison, export, and manifest views.
- Population exploration, preview, profiling, and upload are available through typed API contracts and corresponding GUI surfaces.
- Browser routing, command palette navigation, and contextual help all reflect the stage-based workspace model.
- PRD, architecture, UX spec, and implementation artifacts remain aligned after delivery.

## Scope Notes

- This epic consolidates and supersedes overlapping restructuring work previously spread across EPIC-17 and EPIC-18 where those epics assume the older screen-by-screen GUI model.
- Portfolio, scenario, and run semantics must remain distinct: portfolios are reusable policy bundles, scenarios are versioned executable definitions, and runs are immutable executions.
- Cross-stage validation is a first-class product feature, not just a backend implementation detail.
- Demo onboarding is not a separate tutorial mode; it is a real pre-seeded scenario inside the same workspace users will use for real analysis.
- **EPIC-21 coordination:** Stories 20.4, 20.5, 20.6, and 20.8 must design for extensibility — EPIC-21 will layer evidence metadata display, trust-status validation checks, exogenous comparison dimensions, and evidence-specific regression flows on top of the surfaces built here.

---

## Story 20.1: Implement canonical scenario model and stage-aware routing shell

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** None

Deliver a single scenario-centered workspace shell. Replace the older sequence of full-screen setup views with route-addressable stage and sub-view navigation. Ensure the frontend state model distinguishes clearly between portfolio, scenario, and run.

### Acceptance Criteria

- Given the application shell, when loaded, then a five-stage navigation is visible: Policies, Population, Investment Decisions, Scenario, Run / Results / Compare.
- Given a stage, when its route is visited, then the corresponding stage view renders without full-page reload.
- Given the frontend state model, when inspected, then portfolio, scenario, and run are represented as distinct objects with clear ownership boundaries.

---

## Story 20.2: Add pre-seeded demo-scenario onboarding and scenario entry flows

**Status:** backlog
**Priority:** P0
**Estimate:** 3

**Dependencies:** Story 20.1

First launch should open a real demo scenario, not a separate tutorial. Returning users should resume an existing saved scenario. Entry flows must support: create new from template, open saved scenario, clone scenario, and continue demo scenario.

### Acceptance Criteria

- Given a first-time user, when the application loads, then a pre-seeded demo scenario opens with Stages 1-4 prefilled and Run enabled.
- Given a returning user, when the application loads, then their most recent saved scenario is resumed.
- Given the scenario entry UI, when accessed, then it supports: create new from template, open saved, clone, and continue demo.

---

## Story 20.3: Build Policies & Portfolio stage with inline composition

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 20.1

Implement the Stage 1 surface for browsing templates, composing portfolios inline, editing policy parameters in place, and handling portfolio conflicts without leaving the stage. Portfolio save/load/clone must not be conflated with scenario save/clone.

### Acceptance Criteria

- Given Stage 1, when opened, then the user can browse available policy templates and compose a portfolio inline.
- Given a portfolio, when policies conflict, then conflicts are surfaced and resolvable without leaving the stage.
- Given portfolio operations, when save/load/clone are used, then they operate independently of scenario save/clone.

---

## Story 20.4: Build Population Library and Data Explorer stage

**Status:** backlog
**Priority:** P0
**Estimate:** 8

**Dependencies:** Story 20.1

Implement the Stage 2 population workspace: library list, quick preview, full explorer, profile charts, upload flow, and handoff to Data Fusion. The stage must support both selection for execution and independent data inspection.

**EPIC-21 coordination:** Population metadata display must use placeholder slots for evidence classification (`origin`, `access_mode`, `trust_status`) that EPIC-21 Story 21.2 will populate with canonical contracts.

### Acceptance Criteria

- Given Stage 2, when opened, then a population library lists available datasets with quick preview.
- Given a population, when selected, then full explorer with profile charts is available.
- Given the upload flow, when a dataset is uploaded, then it is validated and added to the library.
- Given population metadata display, when rendered, then placeholder slots exist for evidence classification fields.

---

## Story 20.5: Build Scenario stage with inherited population context, simulation-mode controls, and cross-stage validation gate

**Status:** backlog
**Priority:** P0
**Estimate:** 8

**Dependencies:** Story 20.1, Story 20.3, Story 20.4

Stage 4 is where a scenario becomes executable. It owns simulation-mode selection, horizon controls, inherited primary population context, optional sensitivity populations, save/clone actions, and the final preflight. Primary population selection remains owned by Stage 2, and investment-decision settings remain owned by the dedicated Stage 3 surface.

**EPIC-21 coordination:** The validation/preflight contract must be designed as an extensible check registry so EPIC-21 Story 21.5 can add trust-status rules without replacing the validation infrastructure.

### Acceptance Criteria

- Given Stage 4, when opened, then simulation mode, horizon controls, inherited primary population context, optional sensitivity populations, and final validation controls are configurable.
- Given a scenario, when save or clone is invoked, then the scenario is persisted with all stage settings.
- Given cross-stage validation, when Run is requested, then preflight checks verify: population schema compatibility, mapping completeness, year-schedule coverage, simulation-mode support, and runtime/memory limits.
- Given a validation failure, when detected, then execution is blocked with actionable error messages.
- Given the validation contract, when inspected, then it uses an extensible check registry pattern.

---

## Story 20.6: Refactor Run / Results / Compare around scenario-by-population execution

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 20.5

Stage 5 must reflect the durable scenario model. Queues, results, exports, and comparisons are derived from scenario executions. Comparisons operate on completed runs but still preserve the scenario context that produced them.

**EPIC-21 coordination:** The comparison model must support pluggable comparison dimensions so EPIC-21 Story 21.6 can add exogenous assumption comparison without restructuring the data model.

### Acceptance Criteria

- Given Stage 5, when a run completes, then results are presented as a scenario-by-population matrix.
- Given completed runs, when compared, then scenario lineage is preserved through comparison and export views.
- Given the comparison infrastructure, when inspected, then it supports pluggable comparison dimensions.

---

## Story 20.7: Extend backend APIs for population explorer and execution-contract validation

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 20.1

Expose the backend contracts needed by the new workspace: `/api/populations`, `/api/populations/{id}/preview`, `/api/populations/{id}/profile`, `/api/populations/{id}/crosstab`, `/api/populations/upload`, plus a validation/preflight and execution contract for the Scenario stage that supports both `annual` and `horizon_step` simulation modes.

### Acceptance Criteria

- Given the API surface, when inspected, then population endpoints exist: list, preview, profile, crosstab, upload.
- Given the validation/preflight endpoint, when called, then it returns pass/fail with check-level detail.
- Given `horizon_step` mode, when validated, then unsupported policy domains or incompatible settings fail with actionable errors.
- Given all new endpoints, when called, then they return typed responses matching frontend model contracts.

---

## Story 20.8: Add end-to-end regression coverage and sync product docs to the new IA

**Status:** backlog
**Priority:** P1
**Estimate:** 3

**Dependencies:** Story 20.5, Story 20.6

Add end-to-end tests for the critical flows and update any remaining planning or product docs that still describe the older screen model.

**EPIC-21 coordination:** Structure test fixtures and assertions so EPIC-21 Story 21.8 can add evidence scenarios without duplicating the workspace flow coverage built here.

### Acceptance Criteria

- Given the test suite, when run, then end-to-end tests cover: first launch → demo scenario → run, edit portfolio → validate → run, select/upload population → inspect → run, compare runs with scenario lineage.
- Given planning and product docs, when reviewed, then none describe the older screen-by-screen model.
- Given test fixtures, when inspected, then they are structured for extension by EPIC-21 evidence flows.

---
