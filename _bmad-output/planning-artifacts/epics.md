---
title: ReformLab - Epics and Stories
project: ReformLab
description: Consolidated active epics and stories
date: 2026-04-19
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
source_documents:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
---

# Epics and Stories

Consolidated source of truth for the active backlog.
Completed epics are intentionally not reintroduced here to keep bmad-assist context small.

## Epic Index

Epics 1-24 are complete (see git history and implementation artifacts for details).

| Epic | Title | Phase | Status | Stories |
|------|-------|-------|--------|---------|
| EPIC-25 | Stage 1 Policies Redesign (Revision 4.1 UX) | 3 | done | 6 |
| EPIC-26 | Five-Stage Workspace Migration and Stage Completion | 3 | in-progress (26.7 in review) | 7 |
| EPIC-27 | Workspace UX Stabilization | 3 | backlog | 16 |
| EPIC-28 | Investment Decisions — Technology-Set as a First-Class Concept | 4 | backlog (gated on 28.0 spike) | 6 |
| EPIC-29 | OpenFisca Variable Coverage and Live-Output Recovery | 3 | backlog | 5 |

## Conventions

- **Priority:** `P0` (must ship), `P1` (ship if capacity allows after P0)
- **Size:** Story points (`SP`) on Fibonacci scale (1, 2, 3, 5, 8, 13)
- **Types:** `Story`, `Task`, `Spike`
- **Done:** Acceptance criteria pass and tests are in CI
- **Story files:** `_bmad-output/implementation-artifacts/{epic}-{story-slug}.md`

## Completed Epic Archive Policy

To reduce agent context, this file contains only active and upcoming epics.
Completed epics remain available through git history, story artifacts, code reviews, validations, benchmarks, and retrospectives under `_bmad-output/implementation-artifacts/`.
Current completed range: EPIC-1 through EPIC-24.

## Requirements Inventory

### Functional Requirements

- FR25: System automatically generates immutable run manifests including versions, hashes, parameters, and assumptions.
- FR26: Analyst can inspect assumptions and mappings used in any run.
- FR32: User can use a stage-based no-code GUI to create, inspect, clone, and run scenarios.
- FR32a: The primary population for a scenario is selected in the Population stage and inherited by later stages without mandatory reselection.
- FR32c: The Scenario stage configures execution settings, annual horizon, optional sensitivity population, and final validation before run.
- FR43: Analyst can compose multiple individual policy templates into a named policy portfolio.
- FR46: Analyst can define custom policy templates that participate in portfolios alongside built-in templates.

### NonFunctional Requirements

- NFR9: Run manifests are generated automatically with zero manual effort from the user.
- NFR10: No implicit temporal assumptions; period semantics must remain explicit.
- NFR21: Any app-facing contract changes preserve compatibility intentionally and are versioned clearly.
- NFR-RUNTIME-2: Runtime-mode behavior must be explicit and interpretable in manifests, API responses, and validation surfaces.

### Additional Requirements

- The architecture keeps ReformLab as an orchestration platform; computation logic stays behind the `ComputationAdapter` boundary and no non-computation module should import OpenFisca directly.
- The canonical analysis object remains the `Scenario`; simulation configuration, population inputs, and result lineage must stay attached to that durable object.
- `simulation_mode` and `runtime_mode` are distinct contracts. `simulation_mode` belongs to `Scenario` and controls execution semantics such as `annual` versus `horizon_step`. `runtime_mode` belongs to run requests, persisted run metadata, and manifests, and distinguishes `live` from explicit `replay`.
- Population selection remains part of scenario state, but Stage 2 owns the primary population choice and later stages consume inherited context.
- Backend contracts, manifests, and validation surfaces must distinguish runtime modes so demo replay and live execution remain interpretable.
- Policy-set work should reuse completed foundations from EPIC-13, EPIC-17, EPIC-20, and EPIC-24 rather than recreating them.

### UX Design Requirements

- UX-DR6: The workspace must use a five-stage nav rail (Policies → Population → Investment Decisions → Scenario → Run/Results/Compare) as specified in UX Revision 4.1.
- UX-DR7: Stage 1 must implement the Revision 4.1 policy type and category model: three closed policy types (Tax/Subsidy/Transfer), duplicate policy instances, API-driven categories, category badges, and formula-help popovers.
- UX-DR8: Stage 1 must implement create-from-scratch authoring: pick type and compatible category, then receive default parameter groups based on policy type.
- UX-DR9: Stage 1 policy editing must support the 50/50 desktop browser/composition layout, dense grouped parameter controls, and editable parameter groups (rename/add/move/delete).
- UX-DR10: Policy sets must be first-class reusable artifacts, saved and loaded independently from scenarios, with auto-suggested names derived from policy types and categories.
- UX-DR11: Investment Decisions must be a dedicated Stage 3 that can be skipped when decision behavior is disabled, not a sub-wizard embedded in the Scenario/Engine stage.
- UX-DR12: Stage 4 (Scenario) must show inherited primary population as read-only context from Stage 2, own simulation mode and horizon controls, show runtime summary with Live OpenFisca default status, and serve as the cross-stage integration validation gate.
- UX-DR13: Stage 5 (Run / Results / Compare) must include run queue, results, comparison sub-views, and a dedicated Run Manifest Viewer component for assumptions, mappings, lineage, and reproducibility metadata.
- UX-DR14: The Population Library must include a visually differentiated Quick Test Population for demos, smoke tests, and walkthroughs, clearly marked as not analysis-grade.
- UX-DR15: Scenario names must be suggested deterministically from context, preferring policy set name and primary population name, and must freeze once manually edited.

### FR Coverage Map

- FR25: EPIC-26 - expose manifests in a dedicated Stage 5 manifest viewer.
- FR26: EPIC-26 - make assumptions, mappings, lineage, and reproducibility metadata inspectable in Stage 5.
- FR32: EPIC-26 - migrate the no-code workspace to the five-stage flow.
- FR32a: EPIC-26 - show inherited primary population context in Scenario.
- FR32c: EPIC-26 - keep Scenario as the execution and validation owner without adding a runtime selector.
- FR43: EPIC-25 - make policy sets reusable artifacts independent from scenarios.
- FR46: EPIC-25 - add custom from-scratch policy authoring alongside built-in templates.
- UX-DR6: EPIC-26 - five-stage nav rail (Policies, Population, Investment Decisions, Scenario, Run/Results/Compare).
- UX-DR7: EPIC-25 - three policy types, duplicate instances, API-driven categories, category badges, and formula help.
- UX-DR8: EPIC-25 - create-from-scratch policy authoring with compatible categories and default groups.
- UX-DR9: EPIC-25 - 50/50 Policies layout, dense grouped controls, and editable parameter groups.
- UX-DR10: EPIC-25 - policy sets as first-class reusable artifacts with auto-suggested names.
- UX-DR11: EPIC-26 - Investment Decisions as dedicated Stage 3 with skip-when-disabled routing.
- UX-DR12: EPIC-26 - Scenario stage with inherited population context, runtime summary, and cross-stage validation gate.
- UX-DR13: EPIC-26 - Stage 5 Run / Results / Compare with a dedicated Run Manifest Viewer.
- UX-DR14: EPIC-26 - Quick Test Population in the Population Library.
- UX-DR15: EPIC-26 - deterministic scenario name suggestions that freeze after manual edit.

## Epic List

### Epic 25: Stage 1 Policies Redesign (Revision 4.1 UX)
Analyst can build reusable policy sets in the redesigned Policies stage using three policy types, API-driven categories, formula help, from-template or from-scratch creation, editable parameter groups, and policy set save/load independent from scenarios.
**FRs covered:** FR43, FR46, UX-DR7, UX-DR8, UX-DR9, UX-DR10

### Epic 26: Five-Stage Workspace Migration and Stage Completion
Analyst can move through the canonical five-stage workspace, configure optional investment decisions in their own stage, review inherited population and runtime context in Scenario, and use completed Stage 2/4/5 UX affordances including Quick Test Population, scenario name suggestions, and run manifest viewing.
**FRs covered:** FR25, FR26, FR32, FR32a, FR32c, UX-DR6, UX-DR11, UX-DR12, UX-DR13, UX-DR14, UX-DR15

---
# Epic 25: Stage 1 Policies Redesign (Revision 4.1 UX)

**User outcome:** The analyst builds reusable policy sets in a redesigned Policies stage with three policy types, API-driven categories, formula help, from-template or from-scratch creation, editable parameter groups, and policy set save/load independent from scenarios.

**Status:** backlog

**Builds on:** EPIC-13 (policy templates and extensibility), EPIC-17 (GUI showcase product), EPIC-20 (workspace alignment), EPIC-24 (surfaced live-capable catalog packs where available)

**PRD Refs:** FR43, FR46, UX-DR7, UX-DR8, UX-DR9, UX-DR10

**Primary source documents:**
- `_bmad-output/planning-artifacts/ux-design-specification.md` (Revision 4.1, dated 2026-04-01)
- `_bmad-output/planning-artifacts/prd.md`

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-2501 | Story | P0 | 8 | Add API-driven categories endpoint and formula-help metadata | backlog | FR46, UX-DR7 |
| BKL-2502 | Story | P0 | 5 | Redesign Policies stage browser/composition layout with types, categories, and duplicate policy instances | backlog | FR43, UX-DR7, UX-DR9 |
| BKL-2503 | Story | P0 | 8 | Implement create-from-scratch policy flow with compatible category picker and default parameter groups | backlog | FR46, UX-DR8 |
| BKL-2504 | Story | P0 | 5 | Make parameter groups editable within policy cards | backlog | FR46, UX-DR9 |
| BKL-2505 | Story | P0 | 8 | Make policy sets first-class reusable artifacts independent from scenarios | backlog | FR43, UX-DR10 |
| BKL-2506 | Story | P1 | 3 | Add Stage 1 validation, responsive polish, and regression coverage | backlog | FR43, FR46, UX-DR7, UX-DR8, UX-DR9, UX-DR10 |

## Epic-Level Acceptance Criteria

- Stage 1 is named Policies and removes Portfolio from user-facing copy while preserving backward-compatible API aliases where needed.
- Policies use the closed Tax/Subsidy/Transfer type model with the specified amber/emerald/blue badges.
- Categories are fetched from `GET /api/categories`, not hardcoded in frontend UI, and expose formula-help metadata.
- The Policies stage supports both from-template and from-scratch creation, including duplicate instances of the same template with independent parameters.
- Parameter groups are editable: the analyst can rename groups, add groups, move parameters between groups, and delete empty groups.
- Policy sets are saved and loaded independently from scenarios with deterministic name suggestions that freeze after manual edit.
- Desktop Stage 1 uses the UX-specified 50/50 browser/composition layout and remains usable when stacked on phone.

## Implementation Intent

- Reuse the existing `PoliciesStageScreen`, template catalog, and `PortfolioCompositionPanel` where possible; the work is a redesign of Stage 1 behavior, not a new workspace shell.
- Backend additions are limited to category metadata, from-scratch policy scaffolding, and policy-set persistence aliases/entities needed by the UI.
- The old `portfolio` implementation can remain as a compatibility layer internally, but user-facing copy and new APIs should use Policy Set terminology.
- Policy set independence requires decoupling saved policy composition from scenario state; scenarios should reference a policy set identifier/version rather than owning the full composition inline.

## Scope Notes

- This epic can start before the five-stage shell migration because it is limited to Stage 1 surfaces and policy-set contracts.
- Epic 24 can expand which templates appear, but this epic defines how all policy types, categories, and policy sets are authored and reused.
- Cross-stage population-column warnings may be implemented here as Stage 1 warnings and completed in Epic 26's Scenario integration gate.

---

## Story 25.1: Add API-driven categories endpoint and formula-help metadata

**Status:** backlog
**Priority:** P0
**Estimate:** 8

**Dependencies:** None

Implement the `GET /api/categories` backend endpoint and update the Policies stage (Stage 1) to fetch and display categories. Policy templates in the browser are grouped and filterable by category. Each policy card shows a category badge with a formula-help popover.

**Implementation Notes:**

- **Backend:** Add `GET /api/categories` route in `src/reformlab/server/routes/` returning the category schema from the UX spec: `id`, `label`, `columns`, `compatible_types`, `formula_explanation`, `description`. Initial categories: `carbon_emissions`, `energy_consumption`, `vehicle_emissions`, `housing`, `income`.
- **Frontend API wrapper:** Add `listCategories()` in `frontend/src/api/categories.ts` calling `GET /api/categories`. Add `Category` type to `frontend/src/api/types.ts`.
- **Policy browser update:** Fetch categories on mount. Group templates by category (existing grouping may use `parameter_groups` — switch to category). Add category filter chips alongside the existing type filter.
- **Category badge:** Each policy card shows a category badge (e.g., "Carbon Emissions") using the category's label. The badge uses a neutral color (slate) to distinguish from the type badge (amber/emerald/blue).
- **Formula help popover:** Add a CircleHelp icon next to each category badge. Clicking it opens a Shadcn Popover showing the category's `formula_explanation` and `description` from the API.
- **Template list item type:** Extend `TemplateListItem` to include `category_id` so the frontend can join templates to categories.

**Test Notes:**

- Add backend tests for `GET /api/categories` response shape and content.
- Add frontend tests for category fetching, template grouping by category, and filter behavior.
- Add popover render tests confirming formula help content appears on click.
- Verify existing template selection flows still work after the grouping change.

### Acceptance Criteria

- Given the categories API, when called, then it returns the defined categories with id, label, columns, compatible_types, formula_explanation, and description.
- Given the Policies stage, when rendered, then templates are grouped by category with category headers.
- Given a category filter chip, when selected, then only templates matching that category are shown.
- Given a policy card, when the category help icon is clicked, then a popover appears showing the formula explanation and description.
- Given a template without a matching category, when the browser renders, then it appears in a fallback "Other" group rather than being hidden.

---

## Story 25.2: Redesign Policies stage browser/composition layout with types, categories, and duplicate policy instances

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 25.1

Update Stage 1 so the analyst works in the Revision 4.1 Policies model: a 50/50 desktop workbench with a category/type-aware browser on the left and inline policy composition on the right. Template cards must support duplicate additions and show truthful type, category, formula-help, and live-availability signals.

**Implementation Notes:**

- Rename user-facing stage copy to "Policies" and remove "Portfolio" from visible labels in this surface.
- Apply the desktop 50/50 split between policy browser and policy composition; stack the panels vertically on phone.
- Render closed-set policy type badges: Tax (amber), Subsidy (emerald), Transfer (blue).
- Group and filter the policy browser by API category, type, and search keyword.
- Allow the same template to be added multiple times as independent policy instances with distinct IDs and parameters.
- Keep composite templates such as feebate as policy-set templates that add multiple independently editable policies.
- Preserve Epic 24 live-availability metadata on cards and detail panels without adding a runtime selector.

**Test Notes:**

- Add layout/render tests for the 50/50 desktop structure and stacked mobile structure.
- Add duplicate-template tests proving two instances of the same template can be added and edited independently.
- Add type/category badge tests for Tax, Subsidy, and Transfer.
- Verify existing template-add flows still work with the redesigned layout.

### Acceptance Criteria

- Given the Policies stage on desktop, when rendered, then the policy browser and composition panel occupy a balanced 50/50 workbench layout.
- Given the Policies stage on phone width, when rendered, then browser and composition panels stack without horizontal overflow.
- Given a template card, when displayed, then it shows type badge, category badge, formula-help affordance, and live-availability status when available.
- Given the same template is added twice, when the analyst edits one instance, then the other instance keeps its own parameters.
- Given a feebate template is added, when it enters the composition panel, then it creates separate Tax and Subsidy policies that can be edited independently.

---

## Story 25.3: Implement create-from-scratch policy flow with type selection, category picker, and default parameter groups

**Status:** backlog
**Priority:** P0
**Estimate:** 8

**Dependencies:** Story 25.1, Story 25.2

Add the "create from scratch" path alongside the existing "from template" path in the Policies stage. The analyst picks a policy type (Tax / Subsidy / Transfer), selects a category, and receives a new policy with default parameter groups pre-populated for that type.

**Implementation Notes:**

- **"+ Add Policy" flow:** The existing "+ Add Policy" button (or equivalent) opens a choice: "From template" (existing flow) or "From scratch" (new flow).
- **From-scratch step 1 — Type selection:** Three large cards for Tax (amber), Subsidy (emerald), Transfer (blue) with one-line descriptions. Selecting one highlights it and reveals step 2.
- **From-scratch step 2 — Category selection:** Show only categories whose `compatible_types` includes the selected type (from the categories API). Each category card shows its label and description.
- **From-scratch step 3 — Policy created:** A new policy entry is added to the composition panel with:
  - Auto-generated name: `"{Type} — {Category}"` (e.g., "Tax — Carbon Emissions")
  - The selected type and category
  - Default parameter groups per the UX spec table: Mechanism, Eligibility, Schedule for all types; Redistribution added for Tax
  - Each group has placeholder parameters with sensible defaults (rate = 0, threshold = 0, etc.)
- **Backend:** Add a `POST /api/templates/from-scratch` endpoint (or extend the existing custom template endpoint) that generates a blank policy structure given type + category.
- **Composition panel:** The new policy appears in the panel identically to template-sourced policies — same card layout, same expand/collapse, same parameter editing.

**Test Notes:**

- Add frontend tests for the from-scratch wizard: type selection → category filtering → policy creation.
- Add backend tests for blank policy structure generation given type + category.
- Verify that a from-scratch policy can be saved as part of a policy set and later loaded.
- Verify the composition panel treats from-scratch and from-template policies identically.

### Acceptance Criteria

- Given the Policies stage, when the analyst clicks "+ Add Policy", then two paths are offered: "From template" and "From scratch".
- Given the from-scratch flow, when a type is selected, then only compatible categories are shown.
- Given a type and category selection, when confirmed, then a new policy appears in the composition panel with the correct type badge, category badge, and default parameter groups.
- Given a Tax policy created from scratch, when expanded, then it shows Mechanism, Eligibility, Schedule, and Redistribution parameter groups.
- Given a Subsidy policy created from scratch, when expanded, then it shows Mechanism, Eligibility, and Schedule parameter groups (no Redistribution).
- Given the new policy, when the analyst edits its parameters and saves the policy set, then the from-scratch policy persists and reloads correctly.

---

## Story 25.4: Make parameter groups editable within policy cards

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 25.3

Enable editable parameter groups within policy cards. Group editing stays hidden behind a gear/tool action by default so the ordinary parameter-editing path remains simple.

**Implementation Notes:**

- Add an "Edit groups" icon action on each policy card with an accessible label and tooltip.
- In edit-groups mode, allow analysts to rename a group inline, add a new empty group, move parameters between groups, and delete empty groups.
- Disable deletion for non-empty groups and explain why in the tooltip or disabled action label.
- Keep parameter value editing available in both normal and edit-groups modes.
- Preserve the primary parameter summary in collapsed card headers after group edits.
- Persist group names/order/membership inside the policy instance so from-template and from-scratch policies behave the same way.

**Test Notes:**

- Add frontend tests for rename, add, delete-empty, block-delete-non-empty, and move-parameter operations.
- Add persistence tests proving group edits survive collapse/expand, save, and reload.
- Add accessibility checks for the icon action, inline edit fields, and disabled delete state.

### Acceptance Criteria

- Given a policy card in edit-groups mode, when the analyst renames a group, then the new name persists and displays on collapse and expand.
- Given a policy card in edit-groups mode, when the analyst adds a new group, then an empty group appears and can receive moved parameters.
- Given an empty parameter group, when deleted, then it disappears.
- Given a non-empty group, when delete is attempted, then the action is disabled and the parameters remain intact.
- Given a parameter is moved between groups, when the policy is saved and reloaded, then the parameter remains in the selected group.

---

## Story 25.5: Make policy sets first-class reusable artifacts independent from scenarios

**Status:** backlog
**Priority:** P0
**Estimate:** 8

**Dependencies:** Story 25.4

Decouple policy set persistence from scenario persistence. The analyst can save, load, clone, and reuse policy sets independently, while scenarios reference a selected policy set rather than owning the entire policy composition inline.

**Implementation Notes:**

- Add a `PolicySet` entity in frontend state with `id`, `name`, `description`, `policies[]`, `createdAt`, and `updatedAt`.
- Add or alias backend routes under `/api/policy-sets` while keeping current portfolio routes compatible during migration.
- Update scenario state so new scenarios reference a `policySetId` or policy set version instead of owning only `portfolioName`.
- Add a localStorage migration for old `portfolioName` and inline composition state.
- Add policy set actions in Stage 1: save, load, clone, clear/start over.
- Pre-fill save names deterministically from selected policy types and categories, and stop updating the suggestion once the analyst manually edits it.
- Keep a loaded policy set reusable across scenarios without mutating previous scenario references unexpectedly.

**Test Notes:**

- Add backend tests for policy set create/list/load/clone compatibility.
- Add frontend tests for save with auto-name, manual-name freeze, load into composition, and clone.
- Add migration tests for old `portfolioName` state.
- Add scenario-reference tests proving scenarios point to policy sets by ID/version.

### Acceptance Criteria

- Given the Policies stage, when the analyst saves the current composition, then a policy set is persisted independently from the scenario.
- Given the current composition contains a Tax on Carbon Emissions and Subsidy on Energy Consumption, when the save dialog opens, then the suggested name reflects those policy types/categories.
- Given the analyst manually edits the suggested policy set name, when the composition changes later, then the manual name is not overwritten.
- Given a saved policy set, when loaded into a different scenario, then the composition panel populates with the set's policies, categories, groups, and parameters.
- Given a scenario, when inspected, then it references a policy set by ID or version rather than embedding policy composition as the only source of truth.
- Given old localStorage state with `portfolioName`, when the app initializes, then it migrates to the new policy set reference model without losing the existing composition.

---

## Story 25.6: Add Stage 1 validation, responsive polish, and regression coverage

**Status:** backlog
**Priority:** P1
**Estimate:** 3

**Dependencies:** Story 25.5

Close the Policies redesign with validation and regression coverage for the revised Stage 1 model.

**Implementation Notes:**

- Validate every policy has type, category, required parameters, and valid year schedule before the policy set is considered ready.
- Add non-blocking population-column warnings in Stage 1 when a selected population is already known and lacks required category columns.
- Preserve duplicate-policy validation so two instances of the same template are allowed but conflicts are surfaced inline.
- Verify Stage 1 copy uses Policies and Policy Set terminology, not Portfolio.
- Add responsive checks for the 50/50 split and stacked phone layout.

**Test Notes:**

- Add validation tests for missing type/category/parameters, invalid schedules, and allowed duplicate template instances.
- Add population-column warning tests for missing category columns.
- Add terminology assertions for Stage 1 visible copy.
- Add a focused regression test for from-template, from-scratch, group-edit, save, load, and reload.

### Acceptance Criteria

- Given a policy is missing type, category, or required parameters, when validation runs, then the policy set is not marked ready and the failing field is identified.
- Given two instances of the same template, when validation runs, then duplicates are allowed and any real conflicts are shown as inline warnings.
- Given selected policies require `vehicle_co2` and the selected population lacks that column, when Stage 1 renders, then a non-blocking warning explains the missing data.
- Given Stage 1 renders, when visible copy is inspected, then the stage says Policies and Policy Set rather than Portfolio.
- Given the Stage 1 regression suite, when it runs, then it covers from-template creation, from-scratch creation, editable groups, policy set save/load, and responsive layout.

---

# Epic 26: Five-Stage Workspace Migration and Stage Completion

**User outcome:** The analyst uses the canonical five-stage workspace (Policies → Population → Investment Decisions → Scenario → Run/Results/Compare), with optional investment decisions separated from Scenario, inherited population context visible before execution, completed run-manifest access, Quick Test Population support, and deterministic scenario naming.

**Status:** backlog

**Builds on:** EPIC-20 (workspace alignment and four-stage nav rail), EPIC-22 (Scenario-stage fit), EPIC-23 (live runtime metadata), EPIC-25 (policy set reference model)

**PRD Refs:** FR25, FR26, FR32, FR32a, FR32c, UX-DR6, UX-DR11, UX-DR12, UX-DR13, UX-DR14, UX-DR15

**Primary source documents:**
- `_bmad-output/planning-artifacts/ux-design-specification.md` (Revision 4.1, dated 2026-04-01)
- `_bmad-output/planning-artifacts/prd.md`
- `_bmad-output/planning-artifacts/architecture.md`

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-2601 | Story | P0 | 5 | Migrate nav rail and routing from four stages to five stages | backlog | FR32, UX-DR6 |
| BKL-2602 | Story | P0 | 5 | Extract Investment Decisions into a dedicated Stage 3 with skip-when-disabled routing | backlog | UX-DR11 |
| BKL-2603 | Story | P0 | 5 | Refactor Engine into Scenario stage with inherited population and runtime summary | backlog | FR32a, FR32c, UX-DR12 |
| BKL-2604 | Story | P0 | 5 | Complete Stage 5 Run / Results / Compare with dedicated Run Manifest Viewer | backlog | FR25, FR26, UX-DR13 |
| BKL-2605 | Story | P1 | 3 | Add Quick Test Population to the Population Library | backlog | UX-DR14 |
| BKL-2606 | Story | P1 | 3 | Add deterministic scenario name suggestions from policy set and population context | backlog | UX-DR15 |
| BKL-2607 | Story | P1 | 3 | Add five-stage migration, demo, restore, and cross-stage regression coverage | backlog | FR32, FR32a, FR32c, UX-DR6, UX-DR11, UX-DR12 |

## Epic-Level Acceptance Criteria

- The nav rail shows five stages: Policies, Population, Investment Decisions, Scenario, Run / Results / Compare.
- Existing `engine` route/state values migrate to `scenario` without breaking bookmarks or localStorage restore.
- Investment Decisions is a dedicated Stage 3, optional by default, and skippable when disabled.
- Stage 4 Scenario shows inherited primary population context, owns simulation-mode and horizon controls, shows Live OpenFisca as the default runtime summary when applicable, and performs final cross-stage validation.
- Stage 5 includes run queue, results, comparison, and a dedicated Run Manifest Viewer for assumptions, mappings, lineage, and reproducibility metadata.
- Population Library includes a visually differentiated Quick Test Population near the top.
- Scenario names are suggested from policy set and population context and freeze after manual edit.

## Implementation Intent

- Keep hash routing and `navigateTo(stage, subView?)` patterns unless implementation evidence shows a safer local alternative.
- Reuse the existing `InvestmentDecisionsWizard`; extract it into a stage screen rather than rewriting the wizard.
- Rename or wrap `EngineStageScreen` as `ScenarioStageScreen` and remove investment-decision editing from it.
- Use Epic 23 runtime metadata for Live OpenFisca/replay badges when available; do not add a runtime selector to the standard path.
- Keep Results and Comparison as sub-views under Stage 5 rather than top-level stages.

## Scope Notes

- Epic 26 depends on Epic 25 only where Stage 4 scenario summaries need policy set names/IDs. The route split and Investment Decisions extraction can begin independently.
- Quick Test Population and scenario naming are included here because they are workspace UX gaps from Revision 3/4.1 that were not covered by existing epics.
- This epic should not change live runtime execution semantics; it surfaces and routes the existing contracts.

---

## Story 26.1: Migrate nav rail and routing from four stages to five stages

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** None

Update the workspace shell from the current four-stage layout to the canonical five-stage nav rail: Policies, Population, Investment Decisions, Scenario, Run / Results / Compare.

**Implementation Notes:**

- Update `WorkflowNavRail.tsx` `STAGES` to include `investment-decisions` and `scenario` as separate top-level stages.
- Retire user-facing "Engine" terminology and route old `#engine` hash values to `#scenario`.
- Update workspace stage types, active-stage state, route parsing, and `navigateTo()` calls.
- Keep Population sub-steps (`Library`, `Build`, `Explorer`) as stage-local navigation, not top-level stages.
- Keep Stage 5 active for run queue, results, comparison, decisions, and runner sub-views as specified by UX labels.

**Test Notes:**

- Update nav rail and mobile stage switcher tests to assert five stages and labels.
- Add hash migration tests for `#engine` to `#scenario`.
- Add localStorage migration tests for saved `activeStage: "engine"`.
- Verify Population sub-step routing remains unchanged.

### Acceptance Criteria

- Given the workspace renders, then the nav rail shows Policies, Population, Investment Decisions, Scenario, and Run / Results / Compare in that order.
- Given the URL hash is `#engine`, when the app loads, then it redirects or resolves to Scenario.
- Given saved workspace state has `activeStage: "engine"`, when restored, then the active stage becomes `scenario`.
- Given Population is active, then Library, Build, and Explorer remain sub-steps rather than top-level stages.
- Given any five-stage nav item is clicked, then the correct stage renders and the hash updates.

---

## Story 26.2: Extract Investment Decisions into a dedicated Stage 3 with skip-when-disabled routing

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 26.1

Move investment-decision configuration out of the Scenario/Engine stage into its own optional Stage 3.

**Implementation Notes:**

- Create `InvestmentDecisionsStageScreen.tsx` from the existing investment-decision content currently nested in the engine/scenario screen.
- Reuse `InvestmentDecisionsWizard` and preserve its Enable, Model, Parameters, Review flow.
- When disabled, show optional-behavior summary copy, an enable toggle, and a clear Continue to Scenario action.
- Remove the investment-decision editor from Scenario; Scenario should only summarize decision behavior with a link back to Stage 3.
- Add Stage 3 nav summary states: Disabled, Incomplete, or selected model/calibration summary.

**Test Notes:**

- Add render tests for disabled, enabled incomplete, and enabled configured states.
- Add navigation test for Continue to Scenario.
- Add regression test proving Scenario no longer renders the wizard editor.
- Verify wizard behavior remains unchanged after extraction.

### Acceptance Criteria

- Given Stage 3 renders with decisions disabled, then the analyst sees the enable toggle and can continue directly to Scenario.
- Given decisions are enabled, then the full four-step wizard renders and works in Stage 3.
- Given Stage 4 Scenario renders, then it does not include investment-decision editing controls.
- Given decisions are enabled and configured, then the nav rail summary shows the selected model or calibration summary.
- Given decisions are disabled, then cross-stage validation treats Stage 3 as skippable.

---

## Story 26.3: Refactor Engine into Scenario stage with inherited population and runtime summary

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 26.1, Story 26.2

Make Stage 4 the Scenario stage described by Revision 4.1: inherited primary population context, simulation mode, horizon controls, runtime summary, run summary, and final integration validation.

**Implementation Notes:**

- Rename or wrap `EngineStageScreen.tsx` as `ScenarioStageScreen.tsx`.
- Add an inherited primary population summary from Stage 2: population name, source badge (Built-in / Generated / Uploaded), household count, and link back to Population.
- Keep simulation mode and horizon controls in Scenario and keep them distinct from runtime mode.
- Add runtime summary panel showing Live OpenFisca as the standard web path and replay/demo badge only when explicitly selected by demo/replay flow.
- Add a run summary panel with scenario name, policy set, primary/sensitivity populations, simulation mode/horizon, decision summary, run count, and estimated time if available.
- Strengthen validation to check policy set validity, executable population, required mappings, schedules, decision completeness when enabled, and runtime preflight.
- Each failing validation item should link to the owning stage.

**Test Notes:**

- Add Scenario render tests for inherited population, runtime summary, and decision summary.
- Add validation tests for missing policy set, missing population, incomplete decisions, invalid schedules, missing mappings, and all-valid state.
- Add navigation tests for stage-fix links.
- Add regression coverage for live-default display without a runtime selector.

### Acceptance Criteria

- Given Stage 4 renders, then inherited primary population appears as read-only context with name, source badge, and household count.
- Given standard web execution, then the runtime summary shows Live OpenFisca as the default path and does not show a runtime selector.
- Given a replay/demo flow is active, then the runtime summary shows explicit replay/demo status.
- Given investment decisions are enabled, then Scenario summarizes them and links to Stage 3 for edits.
- Given validation fails, then each failing check identifies the owning stage and links to it.
- Given all checks pass, then the Ready to Run action is enabled.

---

## Story 26.4: Complete Stage 5 Run / Results / Compare with dedicated Run Manifest Viewer

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 26.1, Story 26.3

Make Stage 5 the canonical home for run queue, results, comparison, and run manifest inspection.

**Implementation Notes:**

- Keep run queue, results, and comparison as Stage 5 sub-views.
- Add or extract a dedicated `RunManifestViewer` component for per-run assumptions, mappings, lineage, hashes, versions, population reference, runtime mode, and reproducibility metadata.
- Link the manifest viewer from completed run rows, result views, exports, and comparison context where relevant.
- Preserve existing indicator and comparison rendering; this story adds manifest access rather than changing result schemas.
- Show clear empty states for no runs, running only, failed run, and completed run with missing manifest.

**Test Notes:**

- Add component tests for `RunManifestViewer` with complete and partial manifests.
- Add Stage 5 routing tests for run queue, results, comparison, and manifest view.
- Add regression tests proving existing result and comparison screens still render.
- Add accessibility tests for manifest disclosure and close/back navigation.

### Acceptance Criteria

- Given Stage 5 renders before any runs exist, then it shows a run queue or empty state under Run / Results / Compare.
- Given a completed run exists, when the analyst opens its manifest, then a dedicated manifest viewer shows assumptions, mappings, lineage, versions, hashes, runtime mode, and population reference.
- Given a comparison view is active, when a run is selected, then its manifest is reachable without leaving Stage 5.
- Given a manifest is incomplete or unavailable, then the viewer shows a clear missing-metadata state rather than failing silently.
- Given existing results and comparison views render, then adding manifest access does not change their visible indicator semantics.

---

## Story 26.5: Add Quick Test Population to the Population Library

**Status:** backlog
**Priority:** P1
**Estimate:** 3

**Dependencies:** Story 26.1

Add the UX-specified Quick Test Population near the top of the Population Library for demos, smoke tests, and walkthroughs.

**Implementation Notes:**

- Add a built-in Quick Test Population entry near the top of the library.
- Label it with copy such as "Fast demo / smoke test" and "Not for substantive analysis".
- Visually differentiate it from analysis-grade populations without making it look like an error.
- Ensure it can be selected as primary population and inherited by Scenario like any other population.
- Keep it out of analysis-grade default recommendations where those exist.

**Test Notes:**

- Add Population Library render/order tests.
- Add selection tests proving Quick Test can become the inherited primary population.
- Add copy tests for demo/smoke-test and not-for-analysis labeling.

### Acceptance Criteria

- Given the Population Library renders, then Quick Test Population appears near the top.
- Given Quick Test Population is displayed, then it is labeled as fast demo/smoke test and not for substantive analysis.
- Given the analyst selects Quick Test Population, then Scenario inherits it as primary population.
- Given analysis-grade population recommendations are shown, then Quick Test is visually differentiated from those recommendations.

---

## Story 26.6: Add deterministic scenario name suggestions from policy set and population context

**Status:** backlog
**Priority:** P1
**Estimate:** 3

**Dependencies:** Story 26.3

Replace generic new-scenario names with deterministic suggestions derived from available policy set and population context.

**Implementation Notes:**

- Add a scenario-name suggestion helper that prefers policy set name, then primary population name, with a simple fallback when context is incomplete.
- Keep updating the suggestion while the scenario name is untouched by the user.
- Freeze the name once the analyst manually edits it.
- Ensure loaded/cloned scenarios keep explicit names and do not receive unexpected renames.
- Use the same helper in first-create, clone-as-new where appropriate, and Scenario save controls.

**Test Notes:**

- Add unit tests for full context, partial context, fallback context, manual-edit freeze, and clone behavior.
- Add Scenario screen tests proving the suggested name appears and then freezes after edit.

### Acceptance Criteria

- Given a new scenario has policy set "Carbon Tax" and population "FR Synthetic 2024", when the name has not been manually edited, then the suggested name is "Carbon Tax — FR Synthetic 2024".
- Given only a policy set is selected, then the suggested name uses the policy set with a sensible fallback suffix.
- Given the analyst manually edits the scenario name, when policy set or population changes later, then the manual name is not overwritten.
- Given a named scenario is cloned, when the clone opens, then it follows the clone naming rule rather than reverting to a generic "New Scenario".

---

## Story 26.7: Add five-stage migration, demo, restore, and cross-stage regression coverage

**Status:** backlog
**Priority:** P1
**Estimate:** 3

**Dependencies:** Story 26.6

Close the workspace migration with regression coverage across first launch, returning-user restore, skip routing, and final validation.

**Implementation Notes:**

- Add a full five-stage happy-path regression: demo scenario, policy set, population, optional decisions disabled, Scenario validation, run, results.
- Add returning-user restore coverage for new stage keys, migrated `engine`, selected policy set, primary population, decision enabled/disabled state, scenario settings, and Stage 5 sub-view.
- Add cross-stage validation coverage for Policies x Population warnings in Stage 1 and Stage 2, and hard blockers in Scenario where execution cannot proceed.
- Verify Stage 5 stays active for run queue, results, comparison, and manifest sub-views.

**Test Notes:**

- Add or update analyst-journey tests for the five-stage flow.
- Add localStorage migration fixture tests.
- Add cross-stage warning/blocker tests.
- Add mobile stage-switcher coverage for five stages.

### Acceptance Criteria

- Given first launch uses the demo scenario, when the workspace opens, then valid Stage 1-4 selections are present and the analyst can run immediately.
- Given a returning user has saved old four-stage state, when the app initializes, then state migrates to the five-stage model without losing scenario context.
- Given investment decisions are disabled, when the analyst follows the natural flow, then Stage 3 can be skipped and Scenario validation can still pass.
- Given policies require columns missing from the selected population, when Stage 1 and Stage 2 render, then both show non-blocking warnings.
- Given Stage 5 sub-views are used, then run queue, results, comparison, and manifest viewer all keep Run / Results / Compare active in the nav rail.
- Given the regression suite runs, then it covers five-stage nav, skip routing, scenario validation, Quick Test Population, scenario naming, manifest access, demo flow, and restore flow.

---

# Epic 27: Workspace UX Stabilization

**User outcome:** the analyst sees an honest "not started" workspace, can read help popovers, can run a single-policy assessment, gets useful information without expanding cards, never loses unsaved policy-set work, navigates Population and Investment Decisions in the way the UX spec already documents in prose, sees consistent units and labels in Run/Results/Compare, and benefits from a modest code consolidation that makes future polish cheaper.

**Status:** backlog

**Builds on:** EPIC-25, EPIC-26

**PRD Refs:** FR43 (clarification: ≥1 policy), UX-DR7, UX-DR9, UX-DR10, UX-DR11, UX-DR12, UX-DR13, UX-DR15

**Source documents:**
- `_bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md`
- User reports 2026-04-26 with screenshots
- `_bmad-output/implementation-artifacts/spec-fix-passive-policy-set-autoload-for-non-portfolio-references.md`
- `_bmad-output/implementation-artifacts/deferred-work.md`

**Toast policy (durable rule):** passive / autoload / restore failures are silent; explicit user-initiated actions (Save, Load click, Run) keep their toasts.

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|----|------|-----|----|-------|--------|----------|
| BKL-2700 | Bug | P0 | 2 | Close out story-26.7 review patches and retro EPIC-26 | backlog | UX-DR15 |
| BKL-2701 | Bug | P0 | 1 | Allow single-policy portfolio runs (drop ≥2 minimum) | backlog | FR43 |
| BKL-2702 | Bug | P0 | 1 | Fix Popover transparent background (define `--popover` token) | backlog | UX-DR7 |
| BKL-2703 | Story | P0 | 5 | Show actual parameter values inline in policy cards | backlog | UX-DR7, UX-DR9 |
| BKL-2704 | Story | P0 | 3 | Unify template vs from-scratch policy-card visuals | backlog | UX-DR7, UX-DR8, UX-DR9 |
| BKL-2705 | Story | P0 | 3 | Auto-save policy-set composition draft to localStorage | backlog | UX-DR10 |
| BKL-2706 | Story | P0 | 3 | Add explicit "not started" nav-rail state and stop demo from pre-satisfying stages | backlog | UX-DR6 |
| BKL-2707 | Story | P0 | 3 | Make Investment Decisions wizard step labels clickable | backlog | UX-DR11 |
| BKL-2708 | Story | P1 | 3 | Restructure Population stage as Library-or-Build → Explorer | backlog | UX-DR14 |
| BKL-2709 | Story | P1 | 2 | Improve policy-set auto-name suggestion | backlog | UX-DR10, UX-DR15 |
| BKL-2710 | Story | P1 | 3 | Consolidate frontend formatters | backlog | (cross-cutting) |
| BKL-2711 | Story | P1 | 3 | Consolidate portfolio dialog hooks and unify policy types | backlog | (cross-cutting) |
| BKL-2712 | Story | P1 | 3 | Stage 5 polish — breadcrumb, palette, units, run-id, NaN guards, stale reset | backlog | UX-DR13 |
| BKL-2713 | Story | P1 | 2 | AppContext naming-state hardening | backlog | UX-DR15 |
| BKL-2714 | Story | P1 | 2 | Frontend cleanup sweep absorbing `deferred-work.md` items | backlog | (cleanup) |
| BKL-2715 | Story | P2 | 2 | UX-spec amendments (not-started, Population IA, clickable wizard, Stage 5 breadcrumb) | backlog | UX-DR6, UX-DR11, UX-DR13 |

## Epic-Level Acceptance Criteria

- The Policies stage no longer emits any spurious "Could not load policy set" toast on mount.
- A single-policy scenario can be saved and run end-to-end.
- Help popovers are readable.
- Policy cards show information that helps the analyst recognise a policy without expanding it.
- The nav rail truthfully signals progress on first launch.
- Population stage no longer presents Library, Build, and Explorer as if they were three peer choices.
- Investment Decisions wizard step labels navigate backward on click.
- Stage 5 displays consistent units, semantic colors for baseline/reform, and clear sub-view location.
- Quality gates pass: ruff, mypy, pytest, npm typecheck, npm lint, npm test.

---

# Epic 28: Investment Decisions — Technology-Set as a First-Class Concept

**User outcome:** the analyst can declare which technologies are in scope for an investment decision, the population carries an incumbent technology per household, the discrete-choice step writes chosen technologies back into the population, and multi-period runs reflect technology transitions.

**Status:** backlog (gated on architect spike — story 28.0)

**Builds on:** EPIC-23, EPIC-26, the existing `src/reformlab/discrete_choice/` module

**PRD Refs:** likely new FRs (PM owns) around technology-set, population-state transitions, multi-period semantics. Existing FR43, FR46 expanded.

**Source documents:**
- `_bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md` Section 4.2
- `src/reformlab/discrete_choice/types.py`, `step.py`, `heating.py`, `vehicle.py`
- `src/reformlab/computation/types.py` (PopulationData)

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|----|------|-----|----|-------|--------|----------|
| BKL-2800 | Spike | P0 | 3 | Architect spike — technology-set contract and population state-transition model | backlog | (architecture) |
| BKL-2801 | Story | P0 | 5 | Add `technology_set` to `EngineConfig`; expose API and persistence | backlog | (new FR pending) |
| BKL-2802 | Story | P0 | 5 | Extend `PopulationData` schema with optional incumbent-technology columns | backlog | (new FR pending) |
| BKL-2803 | Story | P0 | 5 | Wire `DiscreteChoiceStep` outputs back into the population frame | backlog | (new FR pending) |
| BKL-2804 | Story | P0 | 3 | Investment Decisions wizard — Technology step | backlog | UX-DR11 |
| BKL-2805 | Story | P1 | 3 | Regression and analyst-journey coverage for multi-period decisions runs | backlog | NFR9 |

## Epic-Level Acceptance Criteria

- An analyst configures a heating scenario over 5 years with EV/heat-pump/gas alternatives, sees transition counts in results, and the manifest captures the technology-set version.
- Backward compatibility verified for scenarios that don't enable decisions or for populations without incumbent columns.
- Architect spike produces an ADR that PM signs off before stories 28.1–28.5 are sized.

---

# Epic 29: OpenFisca Variable Coverage and Live-Output Recovery

**User outcome:** the live OpenFisca path produces the full set of policy-relevant outputs (subsidies, malus, energy aid, French income variables) instead of the four currently-resolvable variables, and the test suite stops encoding the generic-name placeholders that blew up production on 2026-04-26.

**Status:** backlog

**Builds on:** EPIC-23 (live OpenFisca default) and the 2026-04-26 hotfix that narrowed `_DEFAULT_LIVE_OUTPUT_VARIABLES`

**PRD Refs:** FR43, FR46, NFR9 (richer policy outputs and manifest fidelity)

**Source documents:**
- `_bmad-output/implementation-artifacts/deferred-work.md` lines 19–25
- `src/reformlab/computation/result_normalizer.py:71-76`
- 2026-04-26 hotfix commit (search git log for `_DEFAULT_LIVE_OUTPUT_VARIABLES`)

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|----|------|-----|----|-------|--------|----------|
| BKL-2901 | Story | P0 | 5 | Implement custom OpenFisca variables: subsidy_amount, subsidy_eligible, vehicle_malus, energy_poverty_aid | backlog | FR46 |
| BKL-2902 | Story | P0 | 3 | Resolve generic-name placeholders (irpp/revenu_net/revenu_brut/taxe_carbone) | backlog | NFR21 |
| BKL-2903 | Story | P0 | 2 | Restore resolved names in `_DEFAULT_LIVE_OUTPUT_VARIABLES` | backlog | FR43, NFR9 |
| BKL-2904 | Story | P1 | 3 | Sweep test fixtures off the generic names | backlog | (test hygiene) |
| BKL-2905 | Story | P1 | 3 | Add `pa.concat_tables()` schema-mismatch regression tests | backlog | (test hygiene) |

## Epic-Level Acceptance Criteria

- Live OpenFisca runs produce all eight intended output variables.
- No test fixture references generic placeholder names (`irpp`, `revenu_net`, `revenu_brut`, `taxe_carbone`).
- `pa.concat_tables()` schema-mismatch paths in `panel.py` have regression coverage.
- Manifest version bumped if the output set has changed semantics.
