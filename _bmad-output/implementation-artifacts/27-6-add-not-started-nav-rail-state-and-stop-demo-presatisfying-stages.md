# Story 27.6: Add explicit "not started" nav-rail state and stop demo from pre-satisfying stages

Status: ready-for-dev

## Story

As an analyst opening the workspace for the first time,
I want stages I have not yet touched to look "not started" rather than "complete",
so that the nav rail honestly tells me what I still need to do instead of showing every stage as green before I've made any choices.

## Acceptance Criteria

1. Given a brand-new workspace (first launch, empty localStorage), when the nav rail renders, then NO stage indicator is green. Stages should render in a new "not started" state visually distinct from "incomplete" (which today renders gray).
2. Given the analyst selects a population in Stage 2, when they navigate away, then ONLY Stage 2 turns green; other stages remain in the appropriate state (not-started or active).
3. Given the analyst opens Stage 3 and explicitly toggles "Skip" (or clicks "Continue without decisions"), when they continue, then Stage 3 turns green ("explicitly skipped"); if they never visit Stage 3, it remains "not started".
4. Given a returning user with legacy `investmentDecisionsEnabled: false` in localStorage, when the app initializes, then the value migrates to `false` (explicit skip) AND a `stageTouched.investmentDecisions: true` marker is set so the stage renders green.
5. Given the demo scenario factory at `frontend/src/data/demo-scenario.ts`, when called for first launch, then `populationIds` is empty (`[]`) instead of `[DEMO_POPULATION_ID]`, and `investmentDecisionsEnabled` is `null` instead of `false`.
6. Given the user wants the demo's full pre-filled state, when they click a "Load Demo" or "Try the demo" affordance (NEW), then the demo loads with population pre-selected and decisions explicitly skipped, mirroring the previous first-launch behaviour.
7. Given the UX spec status table at `_bmad-output/planning-artifacts/ux-design-specification.md` (around line 1365), when this story is complete, then the spec documents four states: Active, Complete, Incomplete, Not started.

## Tasks / Subtasks

- [ ] Add "not started" state to nav rail (AC: #1)
  - [ ] In `frontend/src/components/layout/WorkflowNavRail.tsx:43-73`, extend the stage-status function to return one of `"not-started" | "active" | "complete" | "incomplete"`
  - [ ] At `:143-149`, add a fourth visual treatment: lighter outline (e.g., `border border-dashed border-slate-200`), no fill, smaller dot
- [ ] Track stage-touched state (AC: #2, #3, #4)
  - [ ] Add `stageTouched: Partial<Record<StageKey, boolean>>` to `WorkspaceScenario` (or `EngineConfig`, whichever is the durable workspace state)
  - [ ] Mark a stage `touched: true` when the user explicitly visits and acts on it (selects, toggles, edits)
  - [ ] Status function: green only when complete AND touched; not-started when neither
- [ ] Demo scenario change (AC: #5)
  - [ ] In `frontend/src/data/demo-scenario.ts:32-55`, change `populationIds: [DEMO_POPULATION_ID]` → `populationIds: []`
  - [ ] Change `investmentDecisionsEnabled: false` → `investmentDecisionsEnabled: null`
  - [ ] Update `EngineConfig` type to allow `boolean | null`
- [ ] "Try the demo" affordance (AC: #6)
  - [ ] Add a CTA on the empty Policies stage: "Try the demo" button that loads the full pre-filled state (carbon-tax-dividend template + DEMO_POPULATION_ID + decisions=skipped)
  - [ ] Mark all five stages `touched: true` for that flow so the nav rail goes green appropriately
- [ ] Migration for legacy state (AC: #4)
  - [ ] In `useScenarioPersistence` restore path, if `investmentDecisionsEnabled === false` (legacy bool), set `stageTouched.investmentDecisions = true`
  - [ ] If `investmentDecisionsEnabled === null` (new), set `stageTouched.investmentDecisions = false`
- [ ] UX spec amendment (AC: #7)
  - [ ] Update `_bmad-output/planning-artifacts/ux-design-specification.md` status table near line 1365 with the four-state model
- [ ] Tests
  - [ ] First-launch test: nav rail shows no green stages
  - [ ] Selection test: select population → only Stage 2 green
  - [ ] Skip test: explicit skip → Stage 3 green
  - [ ] Migration test: legacy `false` → green; new `null` → not-started
  - [ ] "Try the demo" test: button loads full state, all stages green
- [ ] Quality gates
  - [ ] `npm test`, `npm run typecheck`, `npm run lint`

## Dev Notes

- The current bug: `WorkflowNavRail.tsx` completion logic is binary (null = incomplete, populated = complete). Demo pre-fills `populationIds` and sets `investmentDecisionsEnabled: false` (which short-circuits to "complete"), so 4/5 stages light green before any user action.
- The "not started" state must be visually distinguishable from "incomplete" (which is reserved for stages the user has touched but not finished).
- Loosening `investmentDecisionsEnabled` to `boolean | null` is a deliberate type widening; downstream consumers must handle the null case (treat as "decision not made"; do not run decisions module).

### Project Structure Notes

- Files touched: `WorkflowNavRail.tsx`, `demo-scenario.ts`, `types/workspace.ts`, `useScenarioPersistence.ts`, possibly `ScenarioStageScreen.tsx` and `InvestmentDecisionsStageScreen.tsx` (handle the null case)
- New: a small "Try the demo" button component on the empty Policies stage; UX spec updated under story 27.15 if not folded here

### References

- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md#Story-27.6]
- [Source: frontend/src/components/layout/WorkflowNavRail.tsx:43-73, :143-149]
- [Source: frontend/src/data/demo-scenario.ts:32-55]
- [Source: User report 2026-04-26 ("everything is green on the left panel even though I didn't even start")]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
