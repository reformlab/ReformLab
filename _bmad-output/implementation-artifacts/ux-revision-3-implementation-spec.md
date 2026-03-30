---
title: ReformLab UX Revision 3 Implementation Specification
date: 2026-03-30
author: Lucas
status: draft
references:
  - _bmad-output/planning-artifacts/ux-design-specification.md
  - frontend/src/components/layout/TopBar.tsx
  - frontend/src/components/layout/WorkflowNavRail.tsx
  - frontend/src/components/screens/PoliciesStageScreen.tsx
  - frontend/src/components/screens/PopulationStageScreen.tsx
  - frontend/src/components/screens/PopulationLibraryScreen.tsx
  - frontend/src/components/screens/EngineStageScreen.tsx
  - frontend/src/components/scenario/ScenarioEntryDialog.tsx
  - frontend/src/components/engine/InvestmentDecisionsAccordion.tsx
  - frontend/src/contexts/AppContext.tsx
  - frontend/src/types/workspace.ts
---

# ReformLab UX Revision 3 Implementation Specification

## Purpose

This document is the implementation work order for Revision 3 UX changes. It contains only the deltas to build next. The master UX spec remains the design reference; this file defines what is new, what is revised, and how the dev agent should interpret the current implementation.

When this document conflicts with older Revision 2 wording, this document takes precedence for implementation.

## Current Product Context

The current application already ships the four-stage workspace introduced in Revision 2:

1. Policies
2. Population
3. Engine
4. Run / Results / Compare

The current codebase already includes:

- a stage-aware shell and nav rail,
- a population library with Data Fusion and explorer sub-views,
- a policies stage with inline portfolio composition,
- an engine stage with time horizon, population selection, investment-decision accordion, discount rate, validation, save, and clone flows,
- a top bar with logo, scenario switch trigger, save icon, stage name, and utility icons.

Revision 3 does not replace that architecture. It tightens the product fit after hands-on use by improving brand presentation, stage labeling, naming behavior, sub-navigation, the population fast path, the investment-decision workflow, and phone demo viability.

## Delta Summary

| Change | Current behavior | Target behavior | Impact |
|---|---|---|---|
| 1. Brand header and links | Small logo in top bar, no text wordmark, icons are not wired as links | Stronger brand block with working GitHub and website links | Medium |
| 2. Scenario entry placement | Scenario switch trigger sits beside logo | Scenario switcher moved into a dedicated scenario-controls area away from branding | Medium |
| 3. Policies stage layout | Inline composition exists but sizing is not explicitly constrained | Desktop uses a clear 50/50 split with denser parameter typography | Medium |
| 4. Portfolio naming | Save dialog relies on manual naming | Save flow pre-fills a deterministic suggested portfolio name | Medium |
| 5. Population sub-steps | Population stage has hidden route states only | Population sub-steps are visible in navigation when relevant | Medium |
| 6. Engine rename and scenario naming | User-facing label is Engine; new scenarios default to "New Scenario" | User-facing stage becomes Scenario and names are auto-suggested until manually edited | Medium |
| 7. Investment decision wizard | Inline toggle + accordion; taste params are local-only | Guided sub-step flow for enabling and configuring investment decisions | Large |
| 8. Quick test population | Built-in, generated, uploaded populations only | Add a small fast built-in population for demos and smoke flows | Small |
| 9. Mobile demo viability | Desktop-first shell and stage layouts are difficult on phone | Narrow-screen shell and stage stacking work for walkthroughs and light edits | Medium |

## Implementation Rules

### User-facing terminology

- The user-facing stage label `Engine` becomes `Scenario`.
- The object model still distinguishes `Portfolio` and `Scenario`.
- A portfolio remains the reusable policy bundle.
- A scenario remains the saved analysis definition tying portfolio, population, and scenario/execution settings together.

### Internal naming constraints

- This phase does not require a risky full rename of internal symbols such as `StageKey = "engine"` or `EngineConfig`.
- Internal type names, route keys, and filenames may remain unchanged where that reduces code churn.
- User-facing copy, labels, headings, buttons, nav text, and aria labels must use `Scenario`.

### Auto-suggestion rules

- Auto-generated names must be deterministic and local. No AI service or backend dependency.
- The system may keep updating a generated name only while the user has not manually edited it.
- Once the user manually edits a name, the system must not overwrite it.

### Navigation rules

- Global stage navigation remains the four-stage shell.
- Stage-specific sub-navigation is allowed for Population and Scenario where it reduces clutter.
- Sub-steps must not read like separate top-level stages.

### Persistence rules

- Existing saved scenarios must remain loadable.
- Existing internal scenario IDs and local persistence contracts remain valid.
- Revision 3 should prefer additive state over destructive migrations.

### Non-goals for this revision

- No full mobile redesign.
- No rewrite of the canonical object model.
- No complete internal `engine` to `scenario` refactor unless already low-risk during implementation.
- No AI-generated names or remote naming service.

## Change 1: Brand Header and External Links

### Current State

- [`frontend/src/components/layout/TopBar.tsx`](../../frontend/src/components/layout/TopBar.tsx) renders a 48px top bar.
- The left side contains a small `logo.svg`, the current scenario trigger, a save icon, and the stage label.
- The right side shows `BookOpen`, `Github`, status dot, and `Settings`, but the icons are not wired to external links.
- The brand presentation is too weak for demos and does not clearly identify the product.

### Required Change

Strengthen the top-bar brand block and wire the external links so the shell feels like a real product rather than a prototype.

### Affected Components

- `frontend/src/components/layout/TopBar.tsx`
- any shell wrapper that controls top-bar spacing

### Interaction Specification

- The top bar must start with a dedicated brand block.
- The brand block shows:
  - a larger logo than the current `h-6` treatment,
  - the `ReformLab` wordmark,
  - enough spacing that it reads as identity, not an icon.
- GitHub and website actions must be real links.
- On desktop they should be directly visible.
- On phone they may move into an overflow menu if necessary.

### Content / Naming Rules

- Website link target: `https://reform-lab.eu`
- GitHub link target: `https://github.com/reformlab/ReformLab`
- External links open in a new tab.
- If the docs/book icon remains, it is secondary to the website and GitHub links.

### Layout / Responsive Rules

- Brand block remains left-aligned.
- Brand should remain visible at narrow widths, even if secondary utilities collapse.
- The wordmark may truncate later than the stage label; do not hide the logo to save a few pixels.

### Acceptance Criteria

- The top bar clearly shows logo plus `ReformLab`.
- GitHub and website actions are clickable links and open the expected destinations.
- The shell remains balanced after the scenario trigger is moved away from the brand block.

### Non-Goals

- No brand redesign beyond placement, scale, and link wiring.
- No replacement of the visual identity guide.

## Change 2: Move Scenario Entry Away From The Brand Area

### Current State

- [`frontend/src/components/layout/TopBar.tsx`](../../frontend/src/components/layout/TopBar.tsx) places the current scenario button directly beside the logo.
- [`frontend/src/components/scenario/ScenarioEntryDialog.tsx`](../../frontend/src/components/scenario/ScenarioEntryDialog.tsx) is opened from that button.
- This makes the brand and the scenario navigation compete for the same visual attention.

### Required Change

Move scenario switching and scenario entry actions into a dedicated scenario-controls area separate from the brand block.

### Affected Components

- `frontend/src/components/layout/TopBar.tsx`
- `frontend/src/components/scenario/ScenarioEntryDialog.tsx`
- `frontend/src/components/screens/EngineStageScreen.tsx`

### Interaction Specification

- The top bar keeps one global scenario switcher trigger.
- That trigger is not adjacent to the logo or wordmark.
- Recommended placement:
  - top bar left: brand,
  - top bar middle: current stage title,
  - top bar right cluster: scenario switcher plus utility actions.
- Scenario save and clone may continue to live in the Scenario stage toolbar.
- The user can still switch scenarios from anywhere in the app.

### Content / Naming Rules

- The trigger label should prefer the active scenario name.
- Fallback label when no scenario exists: `Scenario`.
- The scenario entry dialog title should change from `Switch Scenario` only if the new trigger wording requires it; otherwise keep the dialog title stable.

### Layout / Responsive Rules

- On phone, the scenario switcher may collapse into the same overflow surface as utilities.
- The active scenario label should remain discoverable from the shell even if it is shortened.

### Acceptance Criteria

- Scenario switching is no longer visually attached to the logo.
- The shell has a dedicated scenario-controls area.
- The existing scenario entry actions remain accessible from any stage.

### Non-Goals

- No new scenario registry screen in this phase.
- No removal of the existing scenario entry dialog behavior.

## Change 3: Policies Stage 50/50 Split and Smaller Parameter Typography

### Current State

- [`frontend/src/components/screens/PoliciesStageScreen.tsx`](../../frontend/src/components/screens/PoliciesStageScreen.tsx) already uses inline composition rather than a wizard.
- The spec does not currently define panel proportions or parameter-density rules.
- In practice the screen feels visually unbalanced and parameter editors are slightly too large for dense policy work.

### Required Change

Make the desktop layout intentionally balanced and slightly denser:

- template browser panel,
- portfolio composition panel,
- equal desktop emphasis.

### Affected Components

- `frontend/src/components/screens/PoliciesStageScreen.tsx`
- `frontend/src/components/simulation/PortfolioTemplateBrowser.tsx`
- `frontend/src/components/simulation/PortfolioCompositionPanel.tsx`
- any parameter-row or policy-card subcomponents used inside the composition panel

### Interaction Specification

- On desktop, Stage 1 presents a clear two-panel workbench.
- Left panel: browse and add policies.
- Right panel: inspect, edit, reorder, validate, save.
- The user should not feel that one side is "primary" and the other is a cramped sidebar.

### Content / Naming Rules

- Stage label remains `Policies & Portfolio`.
- Portfolio validity and conflict messaging remain visible without opening another view.

### Layout / Responsive Rules

- At desktop widths, the layout uses an explicit 50/50 split.
- At tablet widths, panels may shift to a 45/55 or stacked mode if necessary to preserve usability.
- At phone widths, the panels stack vertically.
- Parameter editor typography becomes denser:
  - parameter labels may move to `text-xs`,
  - parameter values remain legible at `text-sm`,
  - section headers stay visually stronger than controls.

### Acceptance Criteria

- The Policies stage uses a visibly balanced desktop split.
- Parameter editing feels denser without becoming hard to read.
- The stage still works when multiple policies are added and reordered.

### Non-Goals

- No new policy authoring model.
- No wizardization of the policies stage.

## Change 4: Auto-Suggested Portfolio Names

### Current State

- [`frontend/src/components/screens/PoliciesStageScreen.tsx`](../../frontend/src/components/screens/PoliciesStageScreen.tsx) uses a save dialog with manually entered `portfolioSaveName`.
- [`frontend/src/contexts/AppContext.tsx`](../../frontend/src/contexts/AppContext.tsx) does not provide naming help for portfolios.
- Saving requires the user to invent a name from scratch every time.

### Required Change

Pre-fill the portfolio save flow with a deterministic suggested name derived from the current composition.

### Affected Components

- `frontend/src/components/screens/PoliciesStageScreen.tsx`
- any portfolio save dialog or validation helper used by that screen

### Interaction Specification

- When the user opens the portfolio save flow and no portfolio name has been manually provided yet, the name field is pre-filled with a suggested name.
- The suggestion should be useful immediately, not generic.
- The user can accept it unchanged or edit it.
- If the user manually edits the suggested value, future composition changes do not overwrite that manual edit during the same save flow.

### Content / Naming Rules

- Suggested names must be deterministic and derived locally from selected policy templates.
- Recommended rule:
  - one policy: use the policy/template name,
  - two policies: join both short names with ` + `,
  - three or more policies: `[first short policy name] + [N] more`.
- If an obvious headline parameter is available for a single-policy case, it may be appended, but this is optional. The implementation should not depend on every template exposing the same metadata shape.
- Fallback: `Untitled Portfolio`.

### Layout / Responsive Rules

- The save dialog layout does not need to change materially.
- The suggested value should appear in the existing name field rather than as placeholder text.

### Acceptance Criteria

- Opening the save flow produces a useful default portfolio name.
- Manual edits are preserved.
- Suggestions do not require network calls or AI services.

### Non-Goals

- No automatic saving.
- No retroactive renaming of already-saved portfolios.

## Change 5: Population Sub-Steps In The Navigation Rail

### Current State

- [`frontend/src/components/screens/PopulationStageScreen.tsx`](../../frontend/src/components/screens/PopulationStageScreen.tsx) routes internally between:
  - library,
  - data fusion,
  - population explorer.
- [`frontend/src/components/layout/WorkflowNavRail.tsx`](../../frontend/src/components/layout/WorkflowNavRail.tsx) only shows the top-level Population stage.
- The sub-views exist in code but are not visible as explicit workflow sub-steps.

### Required Change

Expose the Population stage sub-steps in the navigation pattern so the user understands where they are inside Stage 2.

### Affected Components

- `frontend/src/components/layout/WorkflowNavRail.tsx`
- `frontend/src/components/screens/PopulationStageScreen.tsx`
- `frontend/src/components/screens/PopulationLibraryScreen.tsx`
- `frontend/src/types/workspace.ts`

### Interaction Specification

- When Population is the active stage, the navigation reveals Stage 2 sub-steps.
- Recommended sub-steps:
  - `Library`
  - `Build`
  - `Explorer`
- `Library` maps to the default Population Library view.
- `Build` maps to `data-fusion`.
- `Explorer` maps to `population-explorer` when a population is being explored; otherwise it is visible but disabled or routes back to Library with no confusing empty state.

### Content / Naming Rules

- The top-level stage remains `Population`.
- Sub-steps are labels, not full new stages.
- Avoid jargon like `Data Fusion` as the only label if `Build` is clearer in the nav; the detailed screen can still use `Data Fusion Workbench`.

### Layout / Responsive Rules

- Desktop nav rail may show Population sub-steps only when Stage 2 is active or expanded.
- Mobile may render them in a compact stage-switcher surface rather than inside the left rail.

### Acceptance Criteria

- The user can see that Population has nested work modes.
- Navigating between Library and Build does not feel like leaving the stage.
- Explorer state is more discoverable than the current hidden route model.

### Non-Goals

- No extra backend routes.
- No new top-level stage for Data Fusion or Explorer.

## Change 6: Rename Engine To Scenario And Add Scenario Name Suggestions

### Current State

- [`frontend/src/types/workspace.ts`](../../frontend/src/types/workspace.ts) defines the third stage as `engine`.
- [`frontend/src/components/screens/EngineStageScreen.tsx`](../../frontend/src/components/screens/EngineStageScreen.tsx) renders `Engine Configuration`.
- [`frontend/src/contexts/AppContext.tsx`](../../frontend/src/contexts/AppContext.tsx) creates new scenarios with the default name `New Scenario`.
- Cloning appends `(copy)`.

### Required Change

Rename the user-facing stage from `Engine` to `Scenario` and replace generic scenario naming with deterministic suggestions.

### Affected Components

- `frontend/src/types/workspace.ts`
- `frontend/src/components/layout/WorkflowNavRail.tsx`
- `frontend/src/components/layout/TopBar.tsx`
- `frontend/src/components/screens/EngineStageScreen.tsx`
- `frontend/src/contexts/AppContext.tsx`
- any tests asserting visible `Engine` labels

### Interaction Specification

- All user-facing references to the third stage become `Scenario`.
- The stage remains the place where the user sets time horizon, population sensitivity, investment decisions, discount rate, and run validation.
- When a new scenario is created, the name is suggested automatically.
- Suggested scenario names should reflect current portfolio and population context where available.

### Content / Naming Rules

- Keep internal route keys such as `"engine"` only if that materially reduces refactoring risk.
- Recommended scenario naming rule:
  - if both portfolio and primary population are present: `[Portfolio Name] on [Population Name]`,
  - if only portfolio is present: `[Portfolio Name] scenario`,
  - if only population is present: `Scenario on [Population Name]`,
  - fallback: `Untitled Scenario`.
- The system may update this generated name while it is still system-managed.
- A manual edit freezes the name.
- Cloning should produce `[Existing Scenario Name] copy` unless a stronger existing clone convention already exists.

### Layout / Responsive Rules

- The screen title, top bar, nav rail, and validation copy must all use `Scenario`.
- Internal file names such as `EngineStageScreen.tsx` may remain unchanged in this phase.

### Acceptance Criteria

- The user no longer sees `Engine` as a stage label.
- New scenarios no longer start as `New Scenario`.
- Generated names improve as more context becomes available, until the user manually edits them.

### Non-Goals

- No schema migration of persisted data purely to rename internal fields.
- No replacement of the ScenarioEntryDialog object model.

## Change 7: Investment Decision Sub-Step Wizard

### Current State

- [`frontend/src/components/engine/InvestmentDecisionsAccordion.tsx`](../../frontend/src/components/engine/InvestmentDecisionsAccordion.tsx) provides:
  - a toggle,
  - logit model selector,
  - three local taste-parameter sliders,
  - a calibration stub.
- The interaction is technically present but not structured enough for guided use.
- Taste parameters are local UI state only in the current story.

### Required Change

Replace the bare accordion interaction with a guided wizard-like sub-step inside the Scenario stage.

### Affected Components

- `frontend/src/components/screens/EngineStageScreen.tsx`
- `frontend/src/components/engine/InvestmentDecisionsAccordion.tsx`
- any future extracted stepper/wizard components for Scenario stage sub-steps

### Interaction Specification

- The Scenario stage gains a visible internal flow for investment decisions.
- Recommended sub-step sequence:
  1. `Enable`
  2. `Model`
  3. `Parameters`
  4. `Review`
- `Enable`:
  - explain what investment decisions do,
  - toggle feature on or off.
- `Model`:
  - choose the logit model.
- `Parameters`:
  - edit taste parameters and related controls.
- `Review`:
  - summarize chosen settings and calibration state.

### Content / Naming Rules

- The feature label remains `Investment Decisions`.
- The wizard should explain that this is an advanced scenario behavior layer, not a required step for every run.
- The tone should be guided, not academic.

### Layout / Responsive Rules

- Desktop may render the wizard inline inside the Scenario stage.
- Phone may present these sub-steps as stacked sections or a compact stepper.
- This does not need to become a modal.

### Validation Rules

- If investment decisions are disabled, the wizard collapses to an off state and the scenario remains valid.
- If enabled:
  - a logit model must be selected,
  - required parameters must have valid values,
  - the review step shows whether calibration is still default/stubbed.

### Acceptance Criteria

- A user can progress through investment decisions in a guided order rather than one dense accordion block.
- Disabling the feature returns the stage to the simpler default path.
- The feature remains clearly optional.

### Non-Goals

- No full calibration product redesign.
- No backend expansion beyond what is already supported by the current engine/scenario model in this phase.

## Change 8: Quick / Simple Test Population

### Current State

- [`frontend/src/components/screens/PopulationStageScreen.tsx`](../../frontend/src/components/screens/PopulationStageScreen.tsx) merges built-in, generated, and uploaded populations.
- [`frontend/src/components/screens/PopulationLibraryScreen.tsx`](../../frontend/src/components/screens/PopulationLibraryScreen.tsx) presents the library cards and `Build New` / `Upload` actions.
- There is no explicit fast test population optimized for demos, smoke runs, or quick validation.

### Required Change

Add a clearly labeled built-in quick test population that prioritizes speed and demo readiness over realism.

### Affected Components

- `frontend/src/components/screens/PopulationStageScreen.tsx`
- `frontend/src/components/screens/PopulationLibraryScreen.tsx`
- any demo/mock/built-in population data definition used by the frontend or backend

### Interaction Specification

- The Population Library includes a built-in card for the quick test population.
- It is selectable like any other population.
- It supports downstream Scenario and Results flows.

### Content / Naming Rules

- Recommended label: `Quick Test Population`
- Recommended supporting copy or badge:
  - `Fast demo / smoke test`
  - `Not for substantive analysis`
- The row count should be intentionally small and the card should visually signal that it is for speed, not policy-quality evidence.

### Layout / Responsive Rules

- It should appear near the top of the library because its purpose is speed.
- It should remain visible on phone without needing horizontal scroll.

### Acceptance Criteria

- The user can select a small fast population immediately.
- The population is clearly differentiated from serious analysis populations.
- It works end-to-end with the existing run flow.

### Non-Goals

- No replacement of the main demo scenario.
- No claim that this population is representative for real analysis.

## Change 9: Mobile Demo Viability

### Current State

- The shell and major screens are desktop-first.
- [`frontend/src/components/layout/TopBar.tsx`](../../frontend/src/components/layout/TopBar.tsx) compresses too many visible actions into a 48px header.
- [`frontend/src/components/layout/WorkflowNavRail.tsx`](../../frontend/src/components/layout/WorkflowNavRail.tsx) assumes a persistent desktop rail.
- [`frontend/src/components/screens/EngineStageScreen.tsx`](../../frontend/src/components/screens/EngineStageScreen.tsx) uses a fixed-width right panel.
- [`frontend/src/components/screens/PopulationLibraryScreen.tsx`](../../frontend/src/components/screens/PopulationLibraryScreen.tsx) uses a multi-column grid that is not explicitly tuned for phone-width demos.

### Required Change

Improve phone usability enough for demos, walkthroughs, and light interaction without promising full mobile parity.

### Affected Components

- `frontend/src/components/layout/TopBar.tsx`
- `frontend/src/components/layout/WorkflowNavRail.tsx`
- `frontend/src/components/screens/PoliciesStageScreen.tsx`
- `frontend/src/components/screens/PopulationStageScreen.tsx`
- `frontend/src/components/screens/PopulationLibraryScreen.tsx`
- `frontend/src/components/screens/EngineStageScreen.tsx`
- any shared shell/container component enforcing desktop-only widths

### Interaction Specification

- On phone-width viewports:
  - the user can identify the current stage immediately,
  - stage navigation is reachable in one tap,
  - top-bar actions are reduced to essentials,
  - split layouts stack vertically,
  - secondary panels move below primary editing surfaces.
- Dense content may scroll inside bounded containers when necessary, but the full page must not overflow horizontally.

### Layout / Responsive Rules

- Replace the persistent desktop nav rail with a compact mobile stage switcher, drawer, or horizontal selector below the desktop breakpoint.
- Keep brand, current stage, and scenario context visible.
- Move GitHub, website, docs, and settings into overflow when space is limited.
- Policies stage stacks the template browser and portfolio composition panels.
- Population library uses a single-column card layout on phone.
- Scenario stage moves summary and validation below the main form.
- Remove fixed-width sidebar behavior on phone.

### Acceptance Criteria

- At 375px viewport width, there is no page-level horizontal overflow.
- Stage navigation is reachable from every screen.
- The top bar remains readable and usable on phone.
- Policies, Population, and Scenario screens are navigable without pinch-zoom.
- Desktop layouts remain intact above the mobile breakpoint.

### Non-Goals

- No full mobile-first redesign.
- No bespoke mobile results analytics experience in this phase.

## Cross-Cutting Acceptance Criteria

- User-facing `Engine` labels are removed in favor of `Scenario`.
- Brand presentation is stronger without crowding global navigation.
- New defaults and suggestions never overwrite manual user edits.
- Population sub-steps are discoverable and stage-local.
- Quick test population is clearly labeled as fast/demo-oriented.
- The app does not introduce page-level horizontal scrolling at phone width.
- Existing saved scenarios remain loadable.

## Affected Files And Components

| Area | Likely files | Notes |
|---|---|---|
| Shell / branding | `frontend/src/components/layout/TopBar.tsx` | Brand block, scenario trigger placement, external links, overflow behavior |
| Stage nav | `frontend/src/components/layout/WorkflowNavRail.tsx`, `frontend/src/types/workspace.ts` | User-facing stage labels and Population sub-steps |
| Scenario entry | `frontend/src/components/scenario/ScenarioEntryDialog.tsx`, `frontend/src/contexts/AppContext.tsx` | Trigger placement and naming defaults |
| Policies stage | `frontend/src/components/screens/PoliciesStageScreen.tsx` | 50/50 split, save naming prefill |
| Population stage | `frontend/src/components/screens/PopulationStageScreen.tsx`, `frontend/src/components/screens/PopulationLibraryScreen.tsx` | Sub-steps, quick test population, phone layout |
| Scenario stage | `frontend/src/components/screens/EngineStageScreen.tsx`, `frontend/src/components/engine/InvestmentDecisionsAccordion.tsx` | User-facing rename, wizard, stacking on phone |
| Shared responsive tuning | shell/layout wrappers and any dense card/list components touched by the stages above | Narrow-screen polish only, not a redesign |

## Story Breakdown Proposal

1. Shell branding, external links, and scenario-entry relocation.
2. Policies stage layout rebalance and denser policy parameter typography.
3. Portfolio auto-naming and scenario auto-naming behavior.
4. Population sub-steps plus quick test population.
5. User-facing Engine → Scenario rename across the shell and stage copy.
6. Investment decision wizard inside the Scenario stage.
7. Mobile demo viability pass across shell, Policies, Population, and Scenario.

## Implementation Sequencing Recommendation

1. Update naming and shell structure first.
2. Implement portfolio/scenario suggestion logic next so labels stabilize before tests/screenshots are updated.
3. Add Population sub-steps and the quick test population.
4. Rework the investment-decision experience.
5. Finish with the mobile demo viability pass, because it touches the same shell and stage containers changed above.

## Open Questions

No blocking open questions remain for drafting. The implementation should proceed with the assumptions in this document unless product direction changes again before development starts.
