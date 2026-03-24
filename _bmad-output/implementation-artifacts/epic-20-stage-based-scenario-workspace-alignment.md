# Epic 20: Stage-Based Scenario Workspace Alignment

Status: planned

## Epic Summary

Implement the revised four-stage ReformLab workspace defined in the UX, PRD, and architecture updates from 2026-03-24. This epic turns the current screen-by-screen GUI backlog into a coherent scenario-centered product surface with explicit object semantics, instant demo onboarding, cross-stage execution validation, and run semantics that match the backend model.

## Motivation

The current backlog for the GUI is split across Epic 17 (GUI showcase) and Epic 18 (UX polish). That split assumes an older screen model and leaves key concepts underspecified: where a scenario lives, how first-run onboarding coexists with stage navigation, and where cross-stage validation happens. The updated planning docs now define a clearer model:

- `Portfolio` is a reusable policy bundle.
- `Population` is a reusable analysis dataset.
- `Scenario` is the versioned executable definition combining portfolio, population selection, engine configuration, mappings, and metadata.
- `Run` is the immutable execution of a specific scenario version.

This epic makes those definitions real in the product.

## Stories

| ID | Story | SP | Priority |
|----|-------|----|----------|
| 20.1 | Implement canonical scenario model and stage-aware routing shell | 5 | P0 |
| 20.2 | Add pre-seeded demo-scenario onboarding and scenario entry flows | 3 | P0 |
| 20.3 | Build Policies & Portfolio stage with inline composition | 5 | P0 |
| 20.4 | Build Population Library and Data Explorer stage | 8 | P0 |
| 20.5 | Build Engine stage with scenario save/clone and cross-stage validation gate | 8 | P0 |
| 20.6 | Refactor Run / Results / Compare around scenario-by-population execution | 5 | P0 |
| 20.7 | Extend backend APIs for population explorer and execution-contract validation | 5 | P0 |
| 20.8 | Add end-to-end regression coverage and sync product docs to the new IA | 3 | P1 |

## Dependencies

- Builds on population capabilities from EPIC-11.
- Builds on portfolio semantics from EPIC-12.
- Must remain compatible with discrete-choice and calibration work in EPIC-14 and EPIC-15.
- Consolidates overlapping GUI restructuring work currently spread across EPIC-17 and EPIC-18.
- Uses the 2026-03-24 versions of:
  - `_bmad-output/planning-artifacts/ux-design-specification.md`
  - `_bmad-output/planning-artifacts/prd.md`
  - `_bmad-output/planning-artifacts/architecture.md`

## Exit Criteria

- The GUI is organized as a four-stage shell: Policies & Portfolio, Population, Engine, Run / Results / Compare.
- First launch opens a valid demo scenario with Run enabled and Stage 1-3 already prefilled.
- Scenario save, clone, baseline/reform linking, and stage navigation all operate on the same canonical scenario model.
- Stage 3 blocks execution unless cross-stage validation passes.
- Population preview/profile/upload flows are available through explicit API endpoints and typed frontend clients.
- Stage 4 presents execution as a scenario-by-population matrix and preserves scenario/run lineage through comparison and export.
- Routing, command-palette navigation, and contextual help reflect the new stage model.
- Updated docs, tests, and implementation artifacts all describe the same object model and workspace behavior.

## Story Notes

### 20.1 Implement canonical scenario model and stage-aware routing shell

Deliver a single scenario-centered workspace shell. Replace the older sequence of full-screen setup views with route-addressable stage and sub-view navigation. Ensure the frontend state model distinguishes clearly between portfolio, scenario, and run.

### 20.2 Add pre-seeded demo-scenario onboarding and scenario entry flows

First launch should open a real demo scenario, not a separate tutorial. Returning users should resume an existing saved scenario. Entry flows must support: create new from template, open saved scenario, clone scenario, and continue demo scenario.

### 20.3 Build Policies & Portfolio stage with inline composition

Implement the Stage 1 surface for browsing templates, composing portfolios inline, editing policy parameters in place, and handling portfolio conflicts without leaving the stage. Portfolio save/load/clone must not be conflated with scenario save/clone.

### 20.4 Build Population Library and Data Explorer stage

Implement the Stage 2 population workspace: library list, quick preview, full explorer, profile charts, upload flow, and handoff to Data Fusion. The stage must support both selection for execution and independent data inspection.

### 20.5 Build Engine stage with scenario save/clone and cross-stage validation gate

Stage 3 is where a scenario becomes executable. It owns time horizon, population selection, investment-decision settings, calibration controls, and the final preflight. Validation must include:

- population schema satisfies template/portfolio requirements
- required OpenFisca/project mappings resolve
- policy year schedules fit the time horizon
- runtime/memory preflight passes

### 20.6 Refactor Run / Results / Compare around scenario-by-population execution

Stage 4 must reflect the durable scenario model. Queues, results, exports, and comparisons are derived from scenario executions. Comparisons operate on completed runs but still preserve the scenario context that produced them.

### 20.7 Extend backend APIs for population explorer and execution-contract validation

Expose the backend contracts needed by the new workspace:

- `/api/populations`
- `/api/populations/{id}/preview`
- `/api/populations/{id}/profile`
- `/api/populations/{id}/crosstab`
- `/api/populations/upload`

Also implement or expose a validation/preflight contract that the Engine stage can call before run submission.

### 20.8 Add end-to-end regression coverage and sync product docs to the new IA

Add end-to-end tests for the critical flows:

- first launch -> demo scenario -> run
- edit portfolio -> validate in engine -> run
- select/upload population -> inspect -> run
- compare completed runs while preserving scenario lineage

Update any remaining planning or product docs that still describe the older screen model.

## Risks

- Scope overlap with existing EPIC-17 and EPIC-18 stories can create duplicate implementation unless sprint planning explicitly maps or retires old stories.
- If scenario semantics are not normalized first, frontend work will drift back into treating results or portfolios as the primary object.
- Population explorer performance and validation preflight can become bottlenecks on large datasets if they are bolted on late instead of designed into the stage model.
