# Story 27.7: Make Investment Decisions wizard step labels clickable

Status: done

## Story

As an analyst configuring investment decisions,
I want to click on any step label in the wizard breadcrumb to jump back to that step,
so that I can revise an earlier choice without using the Back button repeatedly.

## Acceptance Criteria

1. Given the wizard is on the Review step, when the analyst clicks "Model" in the step breadcrumb, then the wizard navigates back to the Model step with all selections preserved.
2. Given the wizard is on the Enable step (the first step), when the analyst clicks any later step label, then those labels are visibly disabled and clicking has no effect.
3. Given the analyst has visited steps 1, 2, 3 and is currently on step 4, when they click step 2, then they navigate back to step 2; clicking step 3 still works (it's been visited).
4. Given the analyst clicks back to an earlier step and then forward via the Next button, when they reach a previously-visited later step, then their previous selections on intermediate steps are still in place.
5. Given each clickable step label, when rendered, then it has appropriate ARIA attributes (`role="button"` or native `<button>`, `aria-disabled` for unreached steps) and a keyboard-focusable behavior.
6. Given the existing `goToStep()` function at `frontend/src/components/engine/InvestmentDecisionsWizard.tsx:84`, when used by the new clickable labels, then it works without modification (only the JSX needs to change).

## Tasks / Subtasks

- [x] Wrap step indicators in clickable buttons (AC: #1, #2, #5)
  - [x] At `InvestmentDecisionsWizard.tsx:152-199`, replace each step indicator `<div>` with a `<button type="button">`
  - [x] Set `onClick={() => goToStep(step)}`
  - [x] Set `disabled={!visitedSteps.includes(step) && step !== currentStep}`
  - [x] Apply consistent styling for visited / current / unreached states (use existing color tokens)
- [x] Track visited steps (AC: #3, #4)
  - [x] Verify `visitedSteps` already exists in component state (the audit noted it does)
  - [x] When a step is rendered (the user reaches it via Next), add to `visitedSteps`
  - [x] On click of a visited step, do not reset later visited state
- [x] Accessibility (AC: #5)
  - [x] Add `aria-current="step"` for the current step
  - [x] Add `aria-disabled="true"` for unreached steps (in addition to the `disabled` attribute, which Radix-derived components may already handle)
  - [x] Ensure keyboard navigation: Tab moves between visited steps, Enter activates
- [x] Tests (AC: #1, #2, #3, #4, #5)
  - [x] Click-back test: from Review, click Model → wizard at Model step
  - [x] Disabled-forward test: from Enable, click Review → no navigation
  - [x] State preservation test: navigate back, then forward → selections intact
  - [x] Accessibility test: assert ARIA attributes
- [x] Quality gates
  - [x] `npm test`, `npm run typecheck`, `npm run lint`

## Dev Notes

- The `goToStep()` function already exists and is wired to the Review step's "Edit" buttons (per the audit at `:352, :372`). This story extends its use to the breadcrumb.
- This is a UI-only change. No state-machine changes; no new persistence.
- Story 27.6 may add visual states for "untouched" stages on the OUTER nav rail; this story is about the INNER wizard breadcrumb. Don't conflate the two.

### Project Structure Notes

- Files touched: `frontend/src/components/engine/InvestmentDecisionsWizard.tsx`, matching test file
- No new files

### References

- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md#Story-27.7]
- [Source: frontend/src/components/engine/InvestmentDecisionsWizard.tsx:84, :152-199, :352, :372]
- [Source: User report 2026-04-26 ("we should be able to come back to the previous step by clicking on it")]

## Dev Agent Record

### Agent Model Used

claude-opus-4-6 (via bmad-dev-story skill)

### Debug Log References

No debug logs required. Implementation completed in one pass.

### Completion Notes List

- Converted step indicator `<div>` elements to clickable `<button type="button">` elements with proper onClick handlers
- Added `isVisited` check using existing `visitedSteps` state to enable/disable clicking
- Applied visual styling: emerald-500 for completed, blue-500 for current, slate for unreached
- Added `aria-label` with step name (Enable/Model/Parameters/Review) for accessibility
- Added `aria-current="step"` for current step, `aria-disabled` for unreached steps
- Fixed initialization of `visitedSteps` to include step 1 when `isEnabled` is true (auto-advance case)
- Updated useEffect that syncs step state to also mark Model step as visited when auto-advancing
- Added 6 new tests covering click-back, disabled-forward, state-preservation, and accessibility
- All 31 tests pass (25 existing + 6 new)
- Typecheck and lint pass clean (only pre-existing warnings in other files)

### File List

- `frontend/src/components/engine/InvestmentDecisionsWizard.tsx` (modified)
- `frontend/src/components/engine/__tests__/InvestmentDecisionsWizard.test.tsx` (modified)
