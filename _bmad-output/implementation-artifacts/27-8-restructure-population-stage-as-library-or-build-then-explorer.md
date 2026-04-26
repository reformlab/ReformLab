# Story 27.8: Restructure Population stage as Library-or-Build → Explorer with proper gating

Status: ready-for-dev

## Story

As an analyst preparing population data for a scenario,
I want the Population stage to express the natural flow "pick or build a population, then inspect it" instead of presenting Library / Build / Explorer as three peer tabs,
so that the information architecture matches the UX spec's prose intent and the Explorer is only available when there's something to explore.

## Acceptance Criteria

1. Given the Population stage is active, when the nav rail renders, then it shows two sub-steps: "Source" (containing Library and Build choices inside the screen) and "Inspect" (Explorer).
2. Given no population is currently selected, when the nav rail renders, then "Inspect" is visibly disabled with a tooltip "Select or build a population first".
3. Given the analyst is in Library and selects a population, when actioned, then the population becomes the selected primary population and "Inspect" becomes available.
4. Given the analyst is in Build and clicks "Generate and use", when the build completes, then the resulting population is selected automatically and "Inspect" becomes available (the existing `handleDataFusionGenerated` callback at `PopulationStageScreen.tsx:268` is the integration point).
5. Given a returning user with the legacy `population-explorer` activeSubView in localStorage, when restored, then the new `inspect` sub-view resolves correctly without losing the user's intended context.
6. Given the UX spec's existing prose ("Population Library is the entry point") at `_bmad-output/planning-artifacts/ux-design-specification.md` (line ~1703), when the implementation matches, then the prose and the IA are consistent.

## Tasks / Subtasks

- [ ] Update sub-step types (AC: #1)
  - [ ] In `frontend/src/types/workspace.ts:33-37`, change `POPULATION_SUB_STEPS` from three peer items to two: `source` and `inspect`
  - [ ] Update the `SubView` union type accordingly
  - [ ] Add a migration constant mapping legacy values: `null → "source"`, `"data-fusion" → "source"`, `"population-explorer" → "inspect"`
- [ ] Implement gating in screen (AC: #2, #3, #4)
  - [ ] In `PopulationStageScreen.tsx:282-318`, render the `source` sub-view as a unified "Library or Build" surface (Library is the default; "Build new" is a button inside the screen that swaps to the build workbench)
  - [ ] Render the `inspect` sub-view as the Explorer, gated on `selectedPopulationId !== null`
  - [ ] Update `handleDataFusionGenerated` to set the selected population and switch sub-view to `inspect`
- [ ] Update nav rail (AC: #1, #2)
  - [ ] In `WorkflowNavRail.tsx:228-294`, render two sub-step items
  - [ ] Disable Inspect when no population is selected; add tooltip
  - [ ] Reuse the existing nav-rail completion semantics from Story 27.6
- [ ] Migration for legacy state (AC: #5)
  - [ ] In `useScenarioPersistence` (or wherever sub-view state restores), map legacy `population-explorer` → `inspect`, `data-fusion` → `source`
  - [ ] Add a migration test
- [ ] Reconcile UX spec (AC: #6)
  - [ ] If the spec prose contradicts the new IA, update the spec text in story 27.15 (or fold here)
  - [ ] If the prose already supports it, just confirm
- [ ] Tests
  - [ ] Render test: Population active → two sub-steps; Inspect disabled if no selection
  - [ ] Selection test: pick a population → Inspect enabled
  - [ ] Build test: Build → Generate and use → Inspect enabled
  - [ ] Migration test: legacy `population-explorer` → `inspect`
- [ ] Quality gates
  - [ ] `npm test`, `npm run typecheck`, `npm run lint`

## Dev Notes

- The current implementation treats Library, Build, and Explorer as parallel tabs. This story collapses Library/Build into one "Source" sub-step (with a switch inside) and gates Explorer behind a selection. The user mental model becomes: "I'm picking or making a population (one or the other), then I'm inspecting it (only after I have one)."
- This story does NOT change the underlying components (`PopulationLibraryScreen`, `DataFusionWorkbench`, `PopulationExplorer`) — only the routing and the screen-level orchestration.
- Coordinate with Story 27.6 (nav-rail "not started" state): the gating rules here interact with the touched/complete logic there.

### Project Structure Notes

- Files touched: `types/workspace.ts`, `PopulationStageScreen.tsx`, `WorkflowNavRail.tsx`, `useScenarioPersistence.ts` (migration), tests
- No new components; the existing screens and the workbench are reused

### References

- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md#Story-27.8]
- [Source: frontend/src/types/workspace.ts:33-37]
- [Source: frontend/src/components/screens/PopulationStageScreen.tsx:268, :282-318]
- [Source: frontend/src/components/layout/WorkflowNavRail.tsx:228-294]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md (Population stage prose around line 1703)]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
