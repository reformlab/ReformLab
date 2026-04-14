# Epic 22: UX Revision 3 Workspace Fit and Mobile Demo Viability

**User outcome:** Analyst works in a clearer, better-branded five-stage workspace where scenario naming, stage wayfinding, and investment setup are easier to understand, and the core flow remains usable on phone-sized screens for demos and light edits.

**Status:** backlog

**Builds on:** EPIC-18 (UX overhaul), EPIC-20 (scenario workspace), EPIC-21 (evidence-aware workspace surfaces)

**PRD Refs:** FR32, FR34, FR37-FR45, FR47-FR53

**Primary source documents:**
- `_bmad-output/implementation-artifacts/ux-revision-3-implementation-spec.md` (dated 2026-03-30)
- `_bmad-output/planning-artifacts/ux-design-specification.md` (Revision 4.1, dated 2026-04-01)
- `_bmad-output/implementation-artifacts/retrospectives/epic-21-retro-20260330.md`

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-2201 | Story | P0 | 5 | Shell branding, external links, and scenario entry relocation | backlog | FR32, FR34 |
| BKL-2202 | Story | P0 | 5 | Policies stage layout rebalance and denser parameter typography | backlog | FR43, FR44 |
| BKL-2203 | Story | P0 | 3 | Deterministic portfolio and scenario auto naming | backlog | FR32, FR43 |
| BKL-2204 | Story | P0 | 5 | Population sub steps and quick test population | backlog | FR34, FR37-FR42 |
| BKL-2205 | Story | P0 | 3 | User-facing Scenario labeling across shell and stage copy | backlog | FR32, FR47-FR53 |
| BKL-2206 | Story | P0 | 8 | Guided investment decision flow in the dedicated Investment Decisions stage | backlog | FR25-FR29, FR47-FR53 |
| BKL-2207 | Story | P1 | 5 | Mobile demo viability pass across shell and core stages | backlog | FR32, FR34, FR37-FR45, FR47-FR53 |

## Epic-Level Acceptance Criteria

- The top bar presents a stronger ReformLab brand block with working website and GitHub links, while scenario controls no longer compete with branding.
- User-facing `Engine` labels are replaced with `Scenario` where the scenario stage is shown, without breaking saved-scenario compatibility.
- Portfolio and scenario names are suggested deterministically from local context and stop auto-updating once the user edits them.
- The Population stage exposes clear sub-steps and includes a clearly marked quick test population for fast demos and smoke flows.
- Investment decisions are configured through a guided optional flow in the dedicated Investment Decisions stage rather than a single dense accordion inside Scenario.
- At phone width, the shell and core stages remain operable without page-level horizontal overflow.
- Existing scenarios, portfolios, and typed evidence-aware surfaces remain loadable after the UX revision.

## Scope Notes

- This epic refines the EPIC-20 five-stage workspace; it does not replace that information architecture with a new flow.
- User-facing copy must say `Scenario`, but internal route keys, type names, and filenames may remain `engine` where that avoids low-value churn.
- Generated names must be deterministic and local-only; no AI or network dependency is allowed for naming.
- The quick test population is explicitly for speed, demos, and smoke runs; it must not be presented as analysis-grade evidence.
- This epic must not assume unfinished EPIC-21 runtime capabilities (notably 21.4, 21.5, and 21.6) exist. If a story needs them, either complete the prerequisite work first or document a fallback during story planning.
- Backend regressions identified in the EPIC-21 retrospective are prerequisite debt for any backend-touching work inside this epic.

---

## Story 22.1: Shell branding, external links, and scenario entry relocation

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** None

Strengthen the shell identity and separate brand from scenario operations. The top bar should lead with a real ReformLab brand block, expose live website and GitHub links, and move scenario switching into its own controls area so the shell reads like a product rather than a prototype.

### Acceptance Criteria

- Given the top bar on desktop, when rendered, then it shows a stronger ReformLab brand block with logo plus wordmark.
- Given the website and GitHub actions, when clicked, then they open the configured external destinations in a new tab.
- Given scenario switching, when used from the shell, then it is accessible from a dedicated controls area rather than sitting beside the logo.
- Given narrow screens, when space is constrained, then the brand remains visible while secondary utilities can collapse into overflow.

---

## Story 22.2: Policies stage layout rebalance and denser parameter typography

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** None

Rebalance the Policies stage into a deliberate two-panel workbench. The template browser and portfolio composition surfaces should carry equal visual weight on desktop, while parameter editing becomes slightly denser without sacrificing readability.

### Acceptance Criteria

- Given the Policies stage at desktop widths, when rendered, then it uses a visibly balanced two-panel layout with equal emphasis.
- Given parameter editing controls, when rendered, then labels and supporting text are denser while values and section structure remain legible.
- Given multiple policies in a portfolio, when the user adds, edits, reorders, validates, saves, or loads them, then the stage remains usable without the composition panel feeling like a cramped sidebar.
- Given narrower breakpoints, when the layout collapses, then the stage stacks cleanly rather than forcing horizontal overflow.

---

## Story 22.3: Deterministic portfolio and scenario auto naming

**Status:** backlog
**Priority:** P0
**Estimate:** 3

**Dependencies:** Story 22.1

Replace generic manual-only naming with deterministic suggestions derived from the current portfolio and scenario context. Suggestions should improve the default save/create experience, but any manual edit must freeze the generated value.

### Acceptance Criteria

- Given the portfolio save flow, when opened without a manual name, then the name field is pre-filled with a deterministic suggestion derived from the current composition.
- Given a new scenario, when created, then its initial name is suggested from the current portfolio and population context rather than defaulting to `New Scenario`.
- Given a generated portfolio or scenario name, when the user edits it manually, then future context changes do not overwrite that manual edit.
- Given cloning, when invoked, then the clone naming convention remains deterministic and distinguishable from the original.

---

## Story 22.4: Population sub steps and quick test population

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 22.1

Make Stage 2 easier to navigate and faster to demo. Surface the Population stage's internal work modes directly in navigation and add a small built-in population that is optimized for quick walkthroughs, smoke runs, and light validation.

### Acceptance Criteria

- Given Population as the active stage, when navigation is shown, then stage-local sub-steps for Library, Build, and Explorer are visible and understandable.
- Given the Explorer sub-step, when no population is actively being explored, then it is disabled or redirects without a confusing empty state.
- Given the Population Library, when viewed, then a clearly labeled `Quick Test Population` appears near the top and is selectable like any other population.
- Given the quick test population, when used, then it works through the existing scenario and run flow while remaining visibly marked as demo/smoke-test oriented rather than analysis-grade.

---

## Story 22.5: User-facing Scenario labeling across shell and stage copy

**Status:** backlog
**Priority:** P0
**Estimate:** 3

**Dependencies:** Story 22.1

Align visible product language with the scenario-centered workspace. The Scenario stage should read as `Scenario` everywhere a user sees it, while the implementation may keep internal `engine` identifiers where that reduces refactor risk.

### Acceptance Criteria

- Given the shell, top bar, nav rail, screen headings, validation copy, and related aria labels, when inspected by a user, then the stage is labeled `Scenario` rather than `Engine`.
- Given internal implementation details, when reviewed, then low-risk internal `engine` identifiers may remain if they do not leak into the UI.
- Given saved scenarios and local persistence state, when loaded after this change, then they remain compatible.
- Given existing tests and snapshots that assert visible stage names, when updated, then they validate the `Scenario` wording.

---

## Story 22.6: Guided investment decision flow in the dedicated Investment Decisions stage

**Status:** backlog
**Priority:** P0
**Estimate:** 8

**Dependencies:** Story 22.3, Story 22.5

Replace the current dense accordion with a guided dedicated-stage flow for advanced decision behavior. The feature stays optional, but once enabled the user should move through Enable, Model, Parameters, and Review in a clearer order, with settings represented in durable scenario state rather than local-only UI state.

### Acceptance Criteria

- Given the Investment Decisions stage, when investment decisions are enabled, then the user can progress through a visible guided sequence for Enable, Model, Parameters, and Review.
- Given investment decisions are disabled, when the user leaves the flow off, then the scenario remains valid and the user can continue directly to the Scenario stage.
- Given enabled investment decisions, when validation runs, then a logit model is required, required parameters have valid values, and the review step reflects calibration state.
- Given taste parameters and related controls, when edited, then they persist in scenario state rather than existing only as transient local UI values.

---

## Story 22.7: Mobile demo viability pass across shell and core stages

**Status:** backlog
**Priority:** P1
**Estimate:** 5

**Dependencies:** Story 22.1, Story 22.2, Story 22.4, Story 22.5, Story 22.6

Perform a focused responsive pass so the workspace can be demonstrated and lightly edited on phone-sized screens. This is not a full mobile redesign; it is a viability pass across the shell, navigation, Policies, Population, and Scenario surfaces.

### Acceptance Criteria

- Given a 375px viewport, when the application is used, then there is no page-level horizontal overflow.
- Given phone-width navigation, when the user needs to change stage, then stage switching is reachable from every screen in one tap or equivalent compact interaction.
- Given the top bar at narrow widths, when rendered, then brand, current stage, and scenario context remain visible while secondary actions can move into overflow.
- Given Policies, Population, and Scenario screens at phone width, when used, then split layouts stack vertically and secondary panels move below primary editing surfaces.
- Given desktop widths above the mobile breakpoint, when the workspace is viewed, then the existing desktop layouts remain intact.

---
