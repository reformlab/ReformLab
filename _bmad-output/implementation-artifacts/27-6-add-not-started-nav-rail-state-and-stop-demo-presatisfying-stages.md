# Story 27.6: Add explicit "not started" nav-rail state and stop demo from pre-satisfying stages

Status: done

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

- [x] Add "not started" state to nav rail (AC: #1)
  - [x] In `frontend/src/components/layout/WorkflowNavRail.tsx:43-73`, extend the stage-status function to return one of `"not-started" | "active" | "complete" | "incomplete"`
  - [x] At `:143-149`, add a fourth visual treatment: lighter outline (e.g., `border border-dashed border-slate-200`), no fill, smaller dot
- [x] Track stage-touched state (AC: #2, #3, #4)
  - [x] Add `stageTouched: Partial<Record<StageKey, boolean>>` to `WorkspaceScenario` (or `EngineConfig`, whichever is the durable workspace state)
  - [x] Mark a stage `touched: true` when the user explicitly visits and acts on it (selects, toggles, edits)
  - [x] Status function: green only when complete AND touched; not-started when neither
- [x] Demo scenario change (AC: #5)
  - [x] In `frontend/src/data/demo-scenario.ts:32-55`, change `populationIds: [DEMO_POPULATION_ID]` → `populationIds: []`
  - [x] Change `investmentDecisionsEnabled: false` → `investmentDecisionsEnabled: null`
  - [x] Update `EngineConfig` type to allow `boolean | null`
- [x] "Try the demo" affordance (AC: #6)
  - [x] Add a CTA on the empty Policies stage: "Try the demo" button that loads the full pre-filled state (carbon-tax-dividend template + DEMO_POPULATION_ID + decisions=skipped)
  - [x] Mark all five stages `touched: true` for that flow so the nav rail goes green appropriately
- [x] Migration for legacy state (AC: #4)
  - [x] In `useScenarioPersistence` restore path, if `investmentDecisionsEnabled === false` (legacy bool), set `stageTouched.engine = true`
  - [x] If `investmentDecisionsEnabled === null` (new), set `stageTouched.engine = false`
- [x] UX spec amendment (AC: #7)
  - [x] Update `_bmad-output/planning-artifacts/ux-design-specification.md` status table near line 1365 with the four-state model
- [x] Tests
  - [x] First-launch test: nav rail shows no green stages
  - [x] Selection test: select population → only Stage 2 green
  - [x] Skip test: explicit skip → Stage 3 green
  - [x] Migration test: legacy `false` → green; new `null` → not-started
  - [x] "Try the demo" test: button loads full state, all stages green
- [x] Quality gates
  - [x] `npm test`, `npm run typecheck`, `npm run lint`

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

Claude Opus 4.6

### Debug Log References

None

### Completion Notes List

- Added `stageTouched: Partial<Record<StageKey, boolean>>` field to `WorkspaceScenario` type to track which stages user has explicitly interacted with
- Updated `EngineConfig.investmentDecisionsEnabled` type from `boolean` to `boolean | null` (null = not started, false = explicitly skipped, true = enabled)
- Implemented `getStageStatus()` function in WorkflowNavRail with four-state model: Active, Complete, Incomplete, Not started
- Backward compatibility: legacy scenarios without `stageTouched` fall back to old completion logic
- Visual treatment for "not started" state: `border border-dashed border-slate-200 bg-transparent text-slate-400` with smaller dot
- Updated `createDemoScenario()` to return empty `populationIds` and `investmentDecisionsEnabled: null`
- Added `createFullDemoScenario()` for "Try the demo" affordance with pre-filled state and all stages touched
- Added migration logic in `useScenarioPersistence` to set `stageTouched.engine = true` for legacy scenarios with `investmentDecisionsEnabled: false`
- Added "Try the demo" button on empty Policies stage with Play icon and explanatory text
- Updated UX spec with four-state model documentation
- All tests passing (58 tests for modified files)
- Quality gates passing: typecheck (✓), lint (0 errors, 8 pre-existing warnings), tests (✓)

### File List

- `frontend/src/types/workspace.ts` — Added `stageTouched` field to WorkspaceScenario, updated EngineConfig type
- `frontend/src/components/layout/WorkflowNavRail.tsx` — Implemented getStageStatus() with four-state model, updated StepIndicator visual treatments
- `frontend/src/data/demo-scenario.ts` — Updated createDemoScenario() with empty state, added createFullDemoScenario()
- `frontend/src/hooks/useScenarioPersistence.ts` — Added migration logic for legacy investmentDecisionsEnabled state
- `frontend/src/contexts/AppContext.tsx` — Added loadFullDemo() function and context integration
- `frontend/src/components/screens/PoliciesStageScreen.tsx` — Added "Try the demo" button on empty state
- `frontend/src/components/layout/__tests__/WorkflowNavRail.test.tsx` — Added tests for not-started state, stageTouched tracking
- `frontend/src/data/__tests__/demo-scenario.test.ts` — Added tests for demo scenario changes and migration logic
- `_bmad-output/planning-artifacts/ux-design-specification.md` — Updated status table with four-state model
