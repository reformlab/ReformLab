---
title: 'Extract PoliciesStageScreen dialog/composition state into hooks'
type: 'refactor'
created: '2026-04-19'
status: 'done'
baseline_commit: '86f188ec043cd12c580306e3d9e9831d645a2471'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `PoliciesStageScreen.tsx` is 878 lines with 17 `useState` calls. Save dialog alone uses 6 state variables + 1 ref + an auto-suggestion effect, all inline. Clone dialog adds 4 more. This makes the component hard to test in isolation and painful to modify.

**Approach:** Extract three custom hooks — `usePortfolioSaveDialog`, `usePortfolioCloneDialog`, `usePortfolioLoadDialog` — into `frontend/src/hooks/`. Each hook owns its dialog's open/close state, form values, validation errors, loading flag, and submit handler. The component delegates to the hooks and passes their return values to the JSX.

## Boundaries & Constraints

**Always:** Follow existing hook patterns in `useApi.ts` (loading/error state) and `useScenarioPersistence.ts` (module-level utils + thin hook). Keep all 37 existing tests passing without modification — they test the component's public interface (buttons, API calls), not internal state.

**Ask First:** Extracting validation/conflict state (`usePortfolioValidation`) — it's coupled to composition state and may not separate cleanly.

**Never:** Do not refactor composition state (selectedTemplateIds, composition, resolutionStrategy) — that is core business logic tightly bound to the component. Do not change the component's public props or visual output. Do not touch the test file.

</frozen-after-approval>

## Code Map

- `frontend/src/components/screens/PoliciesStageScreen.tsx` -- 878-line component; lines 94-108 are the dialog useState calls to extract
- `frontend/src/hooks/useApi.ts` -- existing hook patterns (loading/error/fetch)
- `frontend/src/hooks/useScenarioPersistence.ts` -- existing pattern (module utils + hook wrapper)
- `frontend/src/components/screens/__tests__/PoliciesStageScreen.test.tsx` -- 37 tests; must remain green, no changes needed

## Tasks & Acceptance

**Execution:**
- [x] `frontend/src/hooks/usePortfolioSaveDialog.ts` -- Create hook extracting: `saveDialogOpen`, `portfolioSaveName`, `portfolioSaveDesc`, `saveNameError`, `saving`, `saveDialogNameManuallyEdited`, the auto-suggestion effect (lines 124-128), and `handleSave` (lines 296-359)
- [x] `frontend/src/hooks/usePortfolioCloneDialog.ts` -- Create hook extracting: `cloneDialogName`, `cloneNewName`, `cloneNameError`, `cloning`, and `handleClone` (lines 379-401)
- [x] `frontend/src/hooks/usePortfolioLoadDialog.ts` -- Create hook extracting: `loadDialogOpen` and `handleLoad` (lines 365-373)
- [x] `frontend/src/components/screens/PoliciesStageScreen.tsx` -- Replace 10+ useState calls and 3 handlers with hook invocations; net reduction ~150-200 lines

**Acceptance Criteria:**
- Given the refactored component, when all 37 existing PoliciesStageScreen tests run, then all pass without modification
- Given the save dialog hook, when the dialog opens with an existing composition, then the name auto-suggestion effect still fires
- Given the clone dialog hook, when clone is submitted with a duplicate name, then the validation error is set and displayed

## Verification

**Commands:**
- `cd frontend && npx vitest run src/components/screens/__tests__/PoliciesStageScreen.test.tsx` -- expected: 37 tests pass
- `cd frontend && npm run typecheck` -- expected: no new errors
- `cd frontend && npm run lint` -- expected: no new errors (pre-existing ones acceptable)

## Suggested Review Order

**Hook Wiring**

- Start with the screen-level delegation boundary.
  [`PoliciesStageScreen.tsx:216`](../../frontend/src/components/screens/PoliciesStageScreen.tsx#L216)

- Check toolbar actions now call hook commands.
  [`PoliciesStageScreen.tsx:348`](../../frontend/src/components/screens/PoliciesStageScreen.tsx#L348)

- Confirm dialog JSX only binds hook state and handlers.
  [`PoliciesStageScreen.tsx:515`](../../frontend/src/components/screens/PoliciesStageScreen.tsx#L515)

**Save Dialog**

- Review extracted save form state and suggestion effect.
  [`usePortfolioSaveDialog.ts:61`](../../frontend/src/hooks/usePortfolioSaveDialog.ts#L61)

- Verify save submit preserves scenario and portfolio side effects.
  [`usePortfolioSaveDialog.ts:94`](../../frontend/src/hooks/usePortfolioSaveDialog.ts#L94)

**Load Dialog**

- Review portfolio rehydration and composition setter boundary.
  [`usePortfolioLoadDialog.ts:48`](../../frontend/src/hooks/usePortfolioLoadDialog.ts#L48)

- Check auto-load retry guard after failed loads.
  [`usePortfolioLoadDialog.ts:89`](../../frontend/src/hooks/usePortfolioLoadDialog.ts#L89)

- Confirm manual load updates scenario linkage after success.
  [`usePortfolioLoadDialog.ts:115`](../../frontend/src/hooks/usePortfolioLoadDialog.ts#L115)

**Clone Dialog**

- Review duplicate-name validation before clone submission.
  [`usePortfolioCloneDialog.ts:19`](../../frontend/src/hooks/usePortfolioCloneDialog.ts#L19)

- Confirm clone open, input change, and submit state stay isolated.
  [`usePortfolioCloneDialog.ts:40`](../../frontend/src/hooks/usePortfolioCloneDialog.ts#L40)
