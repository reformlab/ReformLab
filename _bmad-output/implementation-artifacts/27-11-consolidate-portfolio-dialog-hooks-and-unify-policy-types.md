# Story 27.11: Consolidate portfolio dialog hooks and unify policy types

Status: ready-for-dev

## Story

As a frontend developer maintaining policy-set workflows,
I want the three portfolio dialog hooks (save, load, clone) merged into one and the two divergent policy types reconciled,
so that future changes to portfolio dialog behavior land in one file and the renderer doesn't need to translate between two type shapes.

## Acceptance Criteria

1. Given the new `usePortfolioDialog({ mode: "save" | "load" | "clone" })` hook, when imported, then it exposes the union of operations previously spread across `usePortfolioSaveDialog`, `usePortfolioLoadDialog`, and `usePortfolioCloneDialog`, with mode-specific behavior selected by the `mode` argument.
2. Given the consolidated hook, when used in `PoliciesStageScreen.tsx`, then the screen wiring is shorter and there is exactly one source of error-handling, confirmation, and toast logic for the three flows.
3. Given the existing `CompositionEntry` and `PortfolioPolicyItem` types, when this story is complete, then a single `PortfolioPolicy` type is the canonical shape (matching `PortfolioPolicyItem` from `api/types.ts`) and `CompositionEntry extends PortfolioPolicy { instanceId: string; templateId: string; editableParameterGroups?: ParameterGroups }`.
4. Given the conversion logic at `usePortfolioLoadDialog.ts:66-101` (policy → CompositionEntry), when the unified type lands, then this conversion is reduced to setting `instanceId` and `templateId` on top of the API shape, and any field renames (e.g., `policy_type` ↔ `policyType`) are handled by a small adapter.
5. Given the deprecated `useScenarioPersistence` hook export at `frontend/src/hooks/useScenarioPersistence.ts:216-228`, when this story is complete, then the deprecated hook export is removed and the module-level functions remain.
6. Given the deprecated `PortfolioDesignerScreen.tsx`, when audited, then any inline duplicate of `validatePortfolioName` (lines 93–104) is removed in favour of the canonical import from `portfolioValidation.ts`. If the screen is unreachable from routing, delete it entirely along with its tests.
7. Given the LOC count before and after, when measured, then this consolidation removes at least ~150 lines (target ~250) without losing functional coverage.
8. Given a saved portfolio policy whose `templateId` does not match any current template (e.g., template was renamed or removed), when the policy is loaded into composition, then the unified adapter MUST NOT silently fall back to a generic `policy_type` / `carbon_tax` shape — instead, surface the unmatched policy with an explicit "unmatched template" marker on the `CompositionEntry` so the renderer can warn the analyst, and prevent a subsequent save from rewriting the original `policy_type` to the wrong concrete type.

## Tasks / Subtasks

- [ ] Design unified hook signature (AC: #1, #2)
  - [ ] Sketch `usePortfolioDialog({ mode })` API that covers save (name, description, composition), load (portfolio name → composition), clone (portfolio name → new name + composition)
  - [ ] Decide whether to expose three separate `open*()` functions or a single `openWithMode(mode)`
- [ ] Implement unified hook (AC: #1)
  - [ ] New file `frontend/src/hooks/usePortfolioDialog.ts`
  - [ ] Migrate behaviour from the three existing hooks
  - [ ] Centralise error handling: passive autoload (silent), explicit user actions (toast)
- [ ] Migrate consumers (AC: #2)
  - [ ] Update `PoliciesStageScreen.tsx` to use the unified hook
  - [ ] Update any other consumers found via grep
  - [ ] Delete the three old hook files once unreferenced
- [ ] Unify policy types (AC: #3, #4)
  - [ ] In `frontend/src/api/types.ts`, ensure `PortfolioPolicy` is the canonical name (rename `PortfolioPolicyItem` if needed)
  - [ ] Move `CompositionEntry` from `PortfolioCompositionPanel.tsx` to `frontend/src/api/types.ts` (also closes the deferred-work circular-import risk)
  - [ ] Make `CompositionEntry` extend `PortfolioPolicy`
  - [ ] Update the conversion logic in the unified hook to set `instanceId` and `templateId` on the API shape rather than translating field names
- [ ] Handle unmatched template on load (AC: #8)
  - [ ] At the conversion site (formerly `usePortfolioLoadDialog.ts:66-101`), when no template matches the saved `templateId`, attach an explicit `unmatchedTemplate: true` marker on the `CompositionEntry` instead of falling back to `policy_type: "carbon_tax"`
  - [ ] In `PortfolioCompositionPanel`, surface the unmatched marker as an inline warning ("Saved template no longer available — review before saving") and disable inline editing of `policy_type` for that entry
  - [ ] On save, if any entry carries the `unmatchedTemplate` marker, preserve its original saved `policy_type` rather than rewriting from a guess
  - [ ] Add a regression test covering load-with-unknown-templateId → save round trip (asserts original `policy_type` is preserved)
- [ ] Remove deprecated hook export (AC: #5)
  - [ ] In `useScenarioPersistence.ts`, remove the deprecated hook re-export at lines 216–228
  - [ ] Audit any remaining imports; tests use module-level functions per the spec
- [ ] Clean up `PortfolioDesignerScreen` (AC: #6)
  - [ ] If the screen is reachable: remove the inline duplicate `validatePortfolioName` and import from `portfolioValidation.ts`
  - [ ] If unreachable: delete the screen file and its tests
- [ ] Tests (AC: #1, #2, #3)
  - [ ] Hook tests covering save, load, and clone flows
  - [ ] Type-system test (compile-time): `CompositionEntry extends PortfolioPolicy` and unifying the API → composition path with `satisfies`
  - [ ] Update `PoliciesStageScreen.test.tsx` consumers to use the unified hook
- [ ] Measure LOC delta (AC: #7)
  - [ ] Record before/after LOC for the four affected files in the PR description
- [ ] Quality gates
  - [ ] `npm test`, `npm run typecheck`, `npm run lint`

## Dev Notes

- The toast-policy memory (`feedback_error_toasts_user_initiated_only.md`) is the canonical reference for error handling: passive autoload silent, explicit user actions toast.
- This story closes the deferred-work circular-import risk (CompositionEntry import direction) and the deferred-work `useScenarioPersistence` hook deprecation.
- Sequencing: lands after Story 27.4 (unified PolicyCard) for cleanest type unification.

### Project Structure Notes

- New: `frontend/src/hooks/usePortfolioDialog.ts`, matching test
- Modified: `api/types.ts` (CompositionEntry move), `PoliciesStageScreen.tsx`, `useScenarioPersistence.ts`, possibly `PortfolioDesignerScreen.tsx`
- Deleted: `usePortfolioSaveDialog.ts`, `usePortfolioLoadDialog.ts`, `usePortfolioCloneDialog.ts` (after consumers migrated)
- Possibly deleted: `PortfolioDesignerScreen.tsx` and its test if unreachable

### References

- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md#Story-27.11]
- [Source: _bmad-output/implementation-artifacts/deferred-work.md:3] (circular-import risk)
- [Source: _bmad-output/implementation-artifacts/deferred-work.md] (policy-type fallback on unmatched template, originally deferred from spec-extract-policies-screen-dialog-state review 2026-04-19)
- [Source: Audit findings (frontend code redundancy report) findings #4, #11, #14, #15, #16]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
