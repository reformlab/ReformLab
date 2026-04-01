# Sprint Change Proposal — Workspace Boundary Correction for Population, Investment Decisions, and Horizon-Step Simulation

**Project:** ReformLab
**Author:** Lucas
**Date:** 2026-04-01
**Change Scope:** Major — workspace information architecture refinement, execution-contract change, backlog/story updates, PRD/Architecture/UX alignment
**Status:** Draft - Pending approval

---

## Section 1: Issue Summary

### Problem Statement

Current workspace planning mixes three distinct concerns in the Stage 3 `Scenario` surface:

- primary population selection is configured in Stage 2 and then configured again in Stage 3,
- investment decisions are treated as an advanced subsection inside `Scenario` rather than as their own full workspace surface,
- the current backend supports annual execution only, while the desired product behavior includes true `X`-year single-step simulation.

This creates a mismatch between the analyst's mental model and the planned product structure.

### Context

This issue was identified during review of the active Stage 3 design and backlog. The stakeholder position is:

- investment decisions should be a dedicated step after Population, not nested inside Scenario,
- Scenario should expose time-step behavior clearly, including true `X`-year single-step simulation,
- selecting a primary population in Population should not require reselection in Scenario.

### Triggering Stories

| Checklist ID | Status | Finding |
|---|---|---|
| 1.1 | [x] Done | Triggering stories are **BKL-2005** (Stage 3 scenario assembly), **BKL-2206** (investment wizard inside Scenario), and the related UX guidance for Stage 3. |
| 1.2 | [x] Done | Issue type is a combination of **new stakeholder requirement** and **misunderstanding of original workflow boundaries**. |
| 1.3 | [x] Done | Evidence exists in current planning artifacts and in the current frontend/API implementation. |

### Evidence

**Planning artifacts currently encode the behavior being challenged:**

- `epics.md` says Stage 3 owns time horizon, population selection, investment-decision settings, calibration controls, and preflight.
- `ux-design-specification.md` puts both population selection and investment decisions inside Stage 3.
- `architecture.md` describes a four-stage shell with Stage 3 binding portfolio + population(s) into a scenario.

**Current implementation mirrors that design:**

- `PopulationStageScreen.tsx` already writes `populationIds` into scenario state.
- `EngineStageScreen.tsx` asks for primary and secondary populations again.
- `EngineStageScreen.tsx` embeds `InvestmentDecisionsWizard` directly in the Scenario screen.

**Backend constraint is explicit today:**

- `ScenarioConfig` exposes `start_year` / `end_year`.
- `YearSchedule` expands to every year in the inclusive range.
- `Orchestrator.run()` iterates `for year in range(start_year, end_year + 1)`.

Today this means:

- annual execution is supported,
- non-annual stride execution such as "simulate 5 years of subsidy in one modeled step" is **not** currently supported by the API or orchestrator contract.

**New requirement clarified during review:**

- the user does **not** want only annual simulation with the UI filtered to year `X`,
- the user wants a distinct simulation mode where a policy can be applied over an `X`-year horizon in one step and return the resulting endpoint distribution of technologies or outcomes.

---

## Section 2: Impact Analysis

### Checklist Progress Snapshot

| Checklist ID | Status | Summary |
|---|---|---|
| 2.1 | [x] Done | EPIC-20 remains viable, but Story 20.1 and Story 20.5 need scope correction. |
| 2.2 | [x] Done | Existing epic/story scope should be modified rather than replaced by a new epic. |
| 2.3 | [x] Done | EPIC-21 dependency references to Story 20.5 and Story 20.6 should be preserved where possible. |
| 2.4 | [x] Done | No future epic becomes obsolete, but EPIC-22 Story 22.6 must be redefined. |
| 2.5 | [x] Done | Priority stays high; sequencing should shift so shell/navigation alignment reflects the new stage boundary before regression coverage is finalized. |
| 3.1 | [x] Done | PRD needs workflow clarification, not a goal reset. |
| 3.2 | [x] Done | Architecture needs a new interaction model and frontend state/routing update. |
| 3.3 | [x] Done | UX spec needs the largest revision because current Stage 3 IA is now incorrect. |
| 3.4 | [x] Done | Secondary impact includes help copy, tests, accessibility labels, and stage-local routing. |

### Epic Impact

| Artifact / Epic | Impact | Required Change |
|---|---|---|
| **EPIC-20** | Major | Update the shell from four stages to five stages; redefine Story 20.5 around inherited population context and configurable simulation mode. |
| **EPIC-22** | Major | Replace "wizard inside Scenario" with a dedicated Investment Decisions stage. |
| **EPIC-21** | Minor | Preserve Story 20.5 / 20.6 integration points so trust/evidence extensions still attach to the same validation/comparison contracts. |
| **PRD** | Major | Clarify stage ownership, inherited population behavior, and add horizon-step simulation as an explicit requirement. |
| **Architecture** | Major | Update frontend interaction model, stage table, scenario semantics, and execution-mode contract. |
| **UX Design** | Major | Rewrite the Stage 3/Scenario section and add a dedicated Investment Decisions stage. |
| **Tests / Help Content** | Moderate | Update visible copy, navigation expectations, and Stage 3 test assertions. |

### Technical Impact

- Frontend state model will need a new top-level stage key for investment decisions.
- Navigation, shell layout, and stage order will change from four stages to five.
- Scenario state should continue storing population IDs, but Stage 2 becomes the primary selection owner.
- Scenario should display inherited primary population context and only expose optional sensitivity additions.
- No backend API change is required for the population deduplication improvement alone.
- A backend/API redesign **is** required for true `X`-year single-step simulation.
- The execution contract needs a new simulation mode concept, not just a different label on `start_year` / `end_year`.
- Validation, manifests, and comparison views must distinguish annual runs from horizon-step runs so outputs remain interpretable.

### MVP Impact

The core MVP and product direction remain intact:

- no rollback is required,
- no foundational architecture is invalidated,
- no existing epic outside workspace alignment and UX revision needs to be removed.

This is a workflow-boundary correction, not a change in product purpose.

---

## Section 3: Recommended Approach

### Option Evaluation

| Option | Viability | Effort | Risk | Notes |
|---|---|---|---|---|
| 1. Direct Adjustment | Viable | High | Medium | Best fit. Update stage model, story scope, and docs without backend rollback. |
| 2. Potential Rollback | Not viable | High | High | There is no meaningful simplification from reverting current work; the problem is planning alignment, not broken foundations. |
| 3. PRD MVP Review | Partially viable | Medium | Medium | Useful for formalizing horizon-step semantics, but full MVP reduction is unnecessary. |

### Selected Path

**Selected approach: Hybrid leaning Direct Adjustment**

Apply a direct workspace correction while also adding an explicit execution-contract extension:

1. introduce a dedicated **Investment Decisions** stage immediately after **Population**,
2. redefine **Scenario** as the stage for simulation-mode selection, horizon setup, and final preflight,
3. make the primary population inherited from Stage 2 rather than reselected,
4. add a true `X`-year single-step simulation mode requirement instead of treating time step as annual-only.

### Rationale

- This aligns the product with the analyst mental model described by the stakeholder.
- It removes duplicate configuration of the same scenario field.
- It distinguishes two genuinely different products:
  - annual iterative simulation,
  - single-step `X`-year horizon simulation.
- It preserves existing backend validation and run-matrix semantics.
- It keeps Story 20.5 / 20.6 as stable dependency anchors for EPIC-21 while extending Story 20.7 for the backend contract.

### Effort and Risk

- **Effort:** High
- **Risk:** Medium
- **Timeline impact:** Moderate backlog reshaping before implementation of EPIC-20 / EPIC-22 stories

---

## Section 4: Detailed Change Proposals

### Proposal 1: PRD - Clarify Workspace Ownership and Add Horizon-Step Simulation Requirement

**Section:** `Functional Requirements -> User Interfaces & Workflow`

**OLD:**

```markdown
- FR32: User can use a stage-based no-code GUI to create, inspect, clone, and run scenarios.
```

**NEW:**

```markdown
- FR32: User can use a stage-based no-code GUI to create, inspect, clone, and run scenarios.
- FR32a: The primary population for a scenario is selected in the Population stage and inherited by later stages without mandatory reselection.
- FR32b: Investment decisions are configured in a dedicated workspace stage after Population, not as a nested subsection of Scenario.
- FR32c: The Scenario stage configures execution settings, annual horizon, optional sensitivity population, and final validation before run.
- FR32d: Scenario configuration supports explicit simulation-mode selection, including annual iteration and `X`-year single-step horizon simulation where supported by the execution backend.
- FR32e: In `X`-year single-step mode, the system simulates the effect of sustained policy exposure over the selected horizon as one modeled step and returns endpoint distributions without requiring yearly intermediate outputs.
```

**Additional PRD requirement to add under Dynamic Orchestration & Vintage Tracking:**

```markdown
- FR18a: System supports horizon-step simulation for selected policy domains, producing endpoint state distributions after `X` years of continuous policy exposure.
```

**Rationale:** This adds workflow clarity and formalizes the new execution behavior instead of treating it as a UI-only option.

### Proposal 2: Architecture - Move From Four Stages to Five Stages

**Section:** `5.10 Frontend (frontend/)`

**OLD:**

```markdown
| Policies & Portfolio | Build or edit reusable policy bundles | `PoliciesAndPortfolioScreen`, template browser, inline portfolio composition |
| Population | Select, generate, upload, and inspect populations | `PopulationLibraryScreen`, `DataFusionWorkbench`, population explorer/profiler |
| Engine | Bind portfolio + population(s) into a scenario, configure projection/execution settings, run integration validation | `EngineScreen`, projection assumptions accordion, run summary, validation gate |
| Run / Results / Compare | Execute runs, inspect results, compare completed runs, export outputs | `RunQueuePanel`, results view, comparison dashboard, run manifest viewer |
```

**NEW:**

```markdown
| Policies & Portfolio | Build or edit reusable policy bundles | `PoliciesAndPortfolioScreen`, template browser, inline portfolio composition |
| Population | Select, generate, upload, and inspect populations | `PopulationLibraryScreen`, `DataFusionWorkbench`, population explorer/profiler |
| Investment Decisions | Configure optional household decision behavior in a dedicated full-stage surface | `InvestmentDecisionsScreen`, model selector, parameter editor, calibration status |
| Scenario | Configure simulation mode, horizon settings, inherited population context, optional sensitivity population, and validation | `ScenarioScreen`, run summary, validation gate |
| Run / Results / Compare | Execute runs, inspect results, compare completed runs, export outputs | `RunQueuePanel`, results view, comparison dashboard, run manifest viewer |
```

**Additional architecture note to add:**

```markdown
Population selection remains part of the durable scenario object, but ownership is split by stage:
- Population stage writes the primary population selection.
- Scenario stage consumes and displays inherited population context.
- Scenario stage may add or remove optional sensitivity populations, but it does not require primary population reselection.

Simulation mode remains part of the durable scenario object:
- `annual` = existing year-by-year execution,
- `horizon_step` = single modeled step over `X` years with endpoint outputs.

The backend contract, manifests, and validation surfaces must record which mode was used.
```

**Rationale:** Reflects actual state ownership and prevents the shell from encoding duplicate responsibilities.

### Proposal 3: UX Design - Replace Stage 3 Population Reselection and Move Investment Decisions Out

**Section:** `Revision: Stage 3 - Scenario`

**OLD:**

```markdown
This stage still owns:

- time horizon,
- population sensitivity selection,
- investment decisions,
- discount rate and related advanced controls,
- save/clone actions,
- cross-stage validation before execution.
```

**NEW:**

```markdown
This stage now owns:

- simulation mode,
- annual time horizon or horizon-step size,
- execution seed and related execution controls,
- inherited primary population summary,
- optional secondary population for sensitivity comparison,
- save/clone actions,
- cross-stage validation before execution.

This stage no longer owns:

- primary population selection,
- investment decision configuration.

The inherited primary population must be visible here, but not reselected by default.
```

**Add new UX subsection before Scenario:**

```markdown
### Revision: Stage 3 - Investment Decisions

This stage is a dedicated workspace for optional household decision behavior.

It owns:
- enable/disable investment decisions,
- model selection,
- parameter editing,
- calibration state and diagnostics,
- review of decision-domain assumptions before execution.

The default path remains simple:
- if investment decisions are off, the user can continue directly to Scenario,
- if investment decisions are on, the user completes this stage before final Scenario validation.
```

**Add simulation-mode guidance:**

```markdown
Scenario must expose simulation mode truthfully.
- `Annual` means iterative yearly execution with intermediate years available.
- `X-Year Step` means one modeled step representing `X` years of sustained policy exposure, with endpoint outputs.
- These two modes are not equivalent and must not be presented as simple display filters on the same result.
```

**Rationale:** This preserves simplicity, gives investment decisions the conceptual weight the stakeholder requested, and encodes the newly clarified simulation requirement.

### Proposal 4: Epics - Update Existing Stories Instead of Adding a New Epic

#### Story 20.1

**OLD:**

```markdown
- Given the application shell, when loaded, then a four-stage navigation is visible: Policies & Portfolio, Population, Engine, Run / Results / Compare.
```

**NEW:**

```markdown
- Given the application shell, when loaded, then a five-stage navigation is visible: Policies & Portfolio, Population, Investment Decisions, Scenario, Run / Results / Compare.
```

#### Story 20.5

**OLD TITLE:**

```markdown
Story 20.5: Build Engine stage with scenario save/clone and cross-stage validation gate
```

**NEW TITLE:**

```markdown
Story 20.5: Build Scenario stage with inherited population context, simulation-mode controls, and cross-stage validation gate
```

**OLD CORE SCOPE:**

```markdown
Stage 3 is where a scenario becomes executable. It owns time horizon, population selection, investment-decision settings, calibration controls, and the final preflight.
```

**NEW CORE SCOPE:**

```markdown
The Scenario stage is where a scenario becomes executable. It owns simulation-mode selection, annual horizon or `X`-year step configuration, execution controls, optional sensitivity population handling, inherited primary population context, and the final preflight.
Primary population selection is owned by the Population stage. Investment-decision settings are owned by the dedicated Investment Decisions stage.
```

**NEW ACCEPTANCE CRITERIA:**

```markdown
- Given the Scenario stage, when opened, then simulation mode, annual time horizon or `X`-year step size, seed, optional sensitivity population, and validation controls are configurable.
- Given a primary population selected earlier, when Scenario opens, then that population is shown as inherited context without mandatory reselection.
- Given an optional sensitivity population, when added, then the resulting run matrix reflects the selected scenario-by-population combinations.
- Given simulation mode controls, when inspected, then annual and `X`-year single-step modes are represented as distinct execution contracts.
- Given a scenario, when save or clone is invoked, then the scenario is persisted with all stage settings.
- Given cross-stage validation, when Run is requested, then preflight checks verify: population schema compatibility, mapping completeness, year-schedule coverage, and runtime/memory limits.
```

#### Story 20.7

**OLD CORE SCOPE:**

```markdown
Expose the backend contracts needed by the new workspace: `/api/populations`, `/api/populations/{id}/preview`, `/api/populations/{id}/profile`, `/api/populations/{id}/crosstab`, `/api/populations/upload`, and a validation/preflight contract for the Engine stage.
```

**NEW CORE SCOPE:**

```markdown
Expose the backend contracts needed by the new workspace: `/api/populations`, `/api/populations/{id}/preview`, `/api/populations/{id}/profile`, `/api/populations/{id}/crosstab`, `/api/populations/upload`, plus a validation/preflight and execution contract for Scenario that supports both annual and `X`-year single-step simulation modes.
```

**NEW ACCEPTANCE CRITERIA TO ADD:**

```markdown
- Given the execution contract, when a scenario is submitted, then the request explicitly records whether the run is annual or `X`-year single-step.
- Given `X`-year single-step mode, when validated, then unsupported policy domains or incompatible settings fail with actionable errors.
- Given completed runs, when inspected in metadata or manifests, then the simulation mode and selected horizon-step size are visible.
```

#### Story 22.6

**OLD TITLE:**

```markdown
Story 22.6: Guided investment decision wizard inside the Scenario stage
```

**NEW TITLE:**

```markdown
Story 22.6: Dedicated Investment Decisions stage after Population
```

**OLD CORE SCOPE:**

```markdown
Replace the current dense accordion with a guided internal flow for advanced scenario behavior.
```

**NEW CORE SCOPE:**

```markdown
Introduce a dedicated full-stage workspace for investment decisions after Population. The stage remains optional, but when enabled it owns the complete decision setup flow: Enable, Model, Parameters, Review, and calibration state.
```

**NEW ACCEPTANCE CRITERIA:**

```markdown
- Given the workspace navigation, when the user progresses after Population, then a dedicated Investment Decisions stage is available before Scenario.
- Given investment decisions are disabled, when the user leaves the stage untouched, then the scenario remains valid and the user can continue directly to Scenario.
- Given investment decisions are enabled, when the user configures them, then the stage provides a full dedicated flow for Enable, Model, Parameters, Review, and calibration status.
- Given the Scenario stage, when reached after this stage, then investment settings are summarized there but not edited there.
- Given validation runs, when investment decisions are enabled, then required model and parameter checks still participate in the shared preflight contract.
```

**Rationale:** Keeps stable story anchors while moving the feature to the stage boundary requested by the stakeholder.

### Proposal 5: Secondary Artifact Updates

If approved, the following implementation-aligned artifacts must also be updated:

- frontend help copy describing Stage 3 as population + investment configuration,
- Stage-key types and nav-rail tests assuming four stages,
- `EngineStageScreen` tests asserting direct population selection inside Scenario,
- API types, manifests, and validation tests assuming annual-only execution semantics,
- accessibility labels and headings that still describe investment decisions as part of Scenario,
- any implementation spec that assumes the wizard lives inside the Scenario screen.

---

## Section 5: Implementation Handoff

### Change Scope Classification

**Major**

This proposal changes the workspace information architecture, story scope, stage ordering, and several cross-document assumptions. It does not require a backend redesign immediately, but it does require coordinated PM, UX, architecture, and backlog updates before implementation.

### Handoff Plan

| Action | Owner | Priority |
|---|---|---|
| Approve or revise the sprint change proposal | Lucas | Immediate |
| Update PRD clarification text | Product / PM | After approval |
| Update architecture stage model | Architect | After approval |
| Update UX specification for five-stage shell | UX | After approval |
| Update `epics.md` story titles, scope, and acceptance criteria | PM / SM | After approval |
| Decide whether `sprint-status.yaml` needs new story entries or only updated story definitions | SM | After approval |
| Re-plan frontend implementation order for shell, stage routing, and tests | SM / Dev | After artifact updates |

### Success Criteria

- Workspace artifacts consistently describe the same five-stage model.
- No artifact requires primary population reselection in Scenario.
- Investment decisions are defined as their own stage, not as a nested Scenario subsection.
- Scenario simulation modes are documented truthfully, with annual and `X`-year single-step defined as distinct behaviors.
- EPIC-21 dependency references to validation/comparison contracts remain intact.

### Checklist Completion

| Checklist ID | Status |
|---|---|
| 4.1 | [x] Viable |
| 4.2 | [x] Not viable |
| 4.3 | [x] Partially viable |
| 4.4 | [x] Done |
| 5.1 | [x] Done |
| 5.2 | [x] Done |
| 5.3 | [x] Done |
| 5.4 | [x] Done |
| 5.5 | [x] Done |
| 6.1 | [x] Done |
| 6.2 | [x] Done |
| 6.3 | [!] Action-needed - explicit user approval required before applying artifact changes |
| 6.4 | [!] Action-needed - `sprint-status.yaml` should only be updated after approval |
| 6.5 | [!] Action-needed - final handoff depends on user decision |

---

## Recommended Next Step

Review this proposal and choose one of:

- approve the direction as drafted,
- request edits to the proposed five-stage model,
- keep four stages and instead move investment decisions into a stage-local sub-step rather than a top-level stage.

The last option is lower-risk technically, but it is a weaker interpretation of the stakeholder request.
