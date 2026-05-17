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
  - [x] Mark the pre-filled stages as touched for that flow without fabricating saved policy-set or run-history completion
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
  - [x] "Try the demo" tests: factory pre-fills population + skipped decisions and does not invent policy/run completion
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
- Added `createFullDemoScenario()` for "Try the demo" with pre-selected population, explicit decision skip, and only the corresponding touched stages
- Added migration logic in `useScenarioPersistence` to set `stageTouched.engine = true` for legacy scenarios with `investmentDecisionsEnabled: false`
- Updated `AppContext.updateScenarioField()` to mark `policies`, `population`, and `engine` as touched when durable scenario state changes; `startRun()` now marks `results` as touched and stores `lastRunId`
- Added "Try the demo" button on empty Policies stage with Play icon and explanatory text
- Corrected the demo CTA/toast contract so it no longer claims fabricated all-green completion
- Updated UX spec with four-state model documentation
- Targeted Story 27.6 tests passing (63 tests)
- Quality gates passing: typecheck (✓), lint (0 errors, 8 pre-existing warnings), targeted tests (✓)

### File List

- `frontend/src/types/workspace.ts` — Added `stageTouched` field to WorkspaceScenario, updated EngineConfig type
- `frontend/src/components/layout/WorkflowNavRail.tsx` — Implemented getStageStatus() with four-state model, updated StepIndicator visual treatments
- `frontend/src/data/demo-scenario.ts` — Updated createDemoScenario() with empty state, added createFullDemoScenario()
- `frontend/src/hooks/useScenarioPersistence.ts` — Added migration logic for legacy investmentDecisionsEnabled state
- `frontend/src/contexts/AppContext.tsx` — Added loadFullDemo() function and context integration
- `frontend/src/components/screens/PoliciesStageScreen.tsx` — Added "Try the demo" button on empty state
- `frontend/src/components/layout/__tests__/WorkflowNavRail.test.tsx` — Added tests for not-started state, stageTouched tracking
- `frontend/src/data/__tests__/demo-scenario.test.ts` — Added tests for demo scenario changes and migration logic
- `frontend/src/hooks/__tests__/useScenarioPersistence.test.ts` — Updated makeScenario() to use null for investmentDecisionsEnabled
- `_bmad-output/planning-artifacts/ux-design-specification.md` — Updated status table with four-state model

<!-- CODE_REVIEW_SYNTHESIS_START -->
## Synthesis Summary
Synthesized 2 adversarial code reviews. The `code_review_synthesis` run timed out on 2026-05-04 before the close-out was finished. Manual follow-up on 2026-05-10 resolved the remaining lifecycle gap, corrected the demo-completion wording, and strengthened the not-started tests. Quality gates for the touched Story 27.6 files now pass: 63 targeted tests, 0 type errors, 0 lint errors (8 pre-existing warnings).

## Validations Quality
- **Reviewer A**: Score 12.5/20 → REJECT. Identified critical gaps in stage-touch lifecycle and AC-6 implementation. Good technical depth but some false positives on already-fixed code.
- **Reviewer B**: Score 7.2/20 → REJECT. Confirmed critical stage-touch lifecycle issue. Noted scope contamination (24 files vs 9 listed) which is accurate but out of scope for this story.

## Issues Verified (by severity)

### Critical

- **Stage-touch lifecycle incomplete** | **Source**: Reviewers A & B | **File**: `frontend/src/contexts/AppContext.tsx`, `frontend/src/components/screens/*.tsx`
  **Issue**: No code writes `stageTouched` when users interact with stages. Task explicitly states "Mark a stage `touched: true` when the user explicitly visits and acts on it" but this is unimplemented. AC-2 and AC-3 cannot work without this.
  **Fix**: APPLIED - `updateScenarioField()` now stamps `policies`, `population`, and `engine` touched markers when durable scenario fields change, and `startRun()` stamps `results` while persisting `lastRunId`.

- **AC-6 "all stages green" impossible** | **Source**: Reviewers A & B | **File**: `frontend/src/data/demo-scenario.ts`, `frontend/src/components/layout/WorkflowNavRail.tsx`
  **Issue**: Policies completion requires a saved policy set and Results completion requires actual run history. The earlier "all stages green" completion note was false for the demo shortcut.
  **Fix**: APPLIED - Story notes, factory docs, and toast copy now describe the real contract: the demo shortcut pre-selects population and explicitly skips investment decisions without fabricating policy or results completion.

### Important

- **Population selector fallback breaks "not started"** | **Source**: Reviewer A | **File**: `frontend/src/components/layout/WorkflowNavRail.tsx:79-86`
  **Issue**: Nav rail uses transient `selectedPopulationId` UI state for completion, not durable `activeScenario.populationIds`. On first launch, selector is set but scenario is empty, causing population stage to show as complete before user action.
  **Fix**: APPLIED - Modified population completion logic to condition on `hasStageTouched`. New scenarios (with stageTouched) use only durable state; legacy scenarios keep fallback for BC.

- **Migration guard incomplete in getSavedScenarios()** | **Source**: Reviewers A & B | **File**: `frontend/src/hooks/useScenarioPersistence.ts:135`
  **Issue**: Early-return condition omits `needsInvestmentDecisionsMigration`. Scenarios with `stageTouched: {}` and `investmentDecisionsEnabled: false` escape migration without `engine: true`.
  **Fix**: APPLIED - Added `&& !needsInvestmentDecisionsMigration` to early-return guard in `getSavedScenarios()`.

- **Test coverage gap for createFullDemoScenario** | **Source**: Reviewers A & B | **File**: `frontend/src/data/__tests__/demo-scenario.test.ts`
  **Issue**: No tests verify `createFullDemoScenario` contract or the "Try the demo" workflow outcome.
  **Fix**: APPLIED - Added `createFullDemoScenario()` tests covering the pre-filled population, explicit skip, and no-fabricated-history contract.

### Minor

- **"Not started" tests use negative assertions only** | **Source**: Reviewer B | **File**: `frontend/src/components/layout/__tests__/WorkflowNavRail.test.tsx:258-262`
  **Issue**: Tests only verify `not.toHaveClass("bg-emerald-500")`, not positive presence of "not-started" styling (`border-dashed`, `bg-transparent`, etc.).
  **Fix**: APPLIED - Added positive assertions for the dashed/transparent treatment on untouched inactive stages.

## Issues Dismissed

- **createNewScenario uses false instead of null** | **Raised by**: Reviewers A & B | **Dismissal Reason**: FALSE POSITIVE. Current code at line 586 already uses `investmentDecisionsEnabled: null`. Reviewers may have been looking at an intermediate version. Git diff confirms this was fixed in the original implementation.

- **Engine completion allows touched-only** | **Raised by**: Reviewers A & B | **Dismissal Reason**: FALSE POSITIVE. Current code at line 93 shows `dataSatisfied = investmentDecisionsEnabled !== null` (without `|| isTouched`). The git diff in review context showed `|| isTouched` was added, but this was already removed/fixed in current codebase.

## Changes Applied

**File**: `frontend/src/hooks/useScenarioPersistence.ts`
**Change**: Fixed migration guard in `getSavedScenarios()` to include `needsInvestmentDecisionsMigration` check
**Before**:
```typescript
      if (!needsTasteMigration && !needsCalibrationMigration && !needsStageTouchedMigration) {
        return scenario;
      }
```
**After**:
```typescript
      if (!needsTasteMigration && !needsCalibrationMigration && !needsStageTouchedMigration && !needsInvestmentDecisionsMigration) {
        return scenario;
      }
```

**File**: `frontend/src/components/layout/WorkflowNavRail.tsx`
**Change**: Fixed population selector fallback to respect stageTouched for new scenarios
**Before**:
```typescript
    case "population":
      // AC-5 (Story 20.4): primary signal is activeScenario.populationIds; legacy fallback
      dataSatisfied = (
        (activeScenario?.populationIds?.length ?? 0) > 0 ||
        !!selectedPopulationId ||
        dataFusionResult !== null
      );
      break;
```
**After**:
```typescript
    case "population":
      // AC-5 (Story 20.4): primary signal is activeScenario.populationIds
      // Story 27.6: For new scenarios (with stageTouched), only use durable state,
      // not transient UI selector. For legacy scenarios, keep selector fallback.
      if (hasStageTouched) {
        // New path: only durable scenario state
        dataSatisfied = (
          (activeScenario?.populationIds?.length ?? 0) > 0 ||
          dataFusionResult !== null
        );
      } else {
        // Legacy path: include UI selector fallback
        dataSatisfied = (
          (activeScenario?.populationIds?.length ?? 0) > 0 ||
          !!selectedPopulationId ||
          dataFusionResult !== null
        );
      }
      break;
```

**File**: `frontend/src/hooks/__tests__/useScenarioPersistence.test.ts`
**Change**: Updated `makeScenario()` helper to use `null` for `investmentDecisionsEnabled` and add `stageTouched: {}`
**Before**:
```typescript
      investmentDecisionsEnabled: false,
      // ...
      },
    policyType: "carbon-tax",
    lastRunId: null,
    ...overrides,
  };
}
```
**After**:
```typescript
      investmentDecisionsEnabled: null,  // Use null to avoid migration in round-trip test
      // ...
      },
    policyType: "carbon-tax",
    lastRunId: null,
    stageTouched: {},  // Story 27.6: New scenarios have stageTouched
    ...overrides,
  };
}
```

**File**: `frontend/src/data/__tests__/demo-scenario.test.ts`
**Change**: Added new test suite for `getSavedScenarios` investment decisions migration
**Tests Added**:
- `getSavedScenarios migrates legacy investmentDecisionsEnabled: false in saved scenarios list`
- `getSavedScenarios does NOT migrate when all migrations are already applied`

## Deep Verify Integration

Deep Verify did not produce findings for this story.

## Files Modified

- frontend/src/hooks/useScenarioPersistence.ts
- frontend/src/components/layout/WorkflowNavRail.tsx
- frontend/src/hooks/__tests__/useScenarioPersistence.test.ts
- frontend/src/data/__tests__/demo-scenario.test.ts
- frontend/src/contexts/AppContext.tsx
- frontend/src/data/demo-scenario.ts

## Suggested Future Improvements

- **Scope**: Add an integration test for the full "Try the demo" button flow through `AppContext` and the empty Policies state | **Rationale**: the factory contract is covered, but the UI affordance itself still relies on mocked component-level coverage | **Effort**: Medium

## Test Results

- Tests passed: 85 (WorkflowNavRail: 37, demo-scenario: 23, useScenarioPersistence: 25)
- Tests failed: 0
- Typecheck: 0 errors
- Lint: 0 errors, 8 pre-existing warnings
<!-- CODE_REVIEW_SYNTHESIS_END -->

## Senior Developer Review (AI)

### Review: 2026-05-04
- **Reviewer:** AI Code Review Synthesis
- **Evidence Score:** 9.85 (average of 12.5 and 7.2) → REJECT
- **Issues Found:** 6 verified (2 critical, 3 important, 1 minor)
- **Issues Fixed:** 4 (migration guard, population selector fallback, test updates, new tests)
- **Action Items Created:** 3

### Review: 2026-05-10
- **Reviewer:** Manual close-out after synthesis timeout
- **Verdict:** ACCEPT
- **Resolved Items:** stage-touch lifecycle, demo-contract wording, positive not-started assertions
- **Residual Note:** the demo shortcut intentionally does not invent a saved policy set or run history

### Review Follow-ups (AI)
- [x] [AI-Review] CRITICAL: Implement stage-touch lifecycle in stage screens/context so explicit stage actions persist touched state
- [x] [AI-Review] CRITICAL: Fix or document AC-6 limitation - demo shortcut now documents its real completion contract
- [x] [AI-Review] MINOR: Add positive assertions for "not started" visual treatment in WorkflowNavRail tests
