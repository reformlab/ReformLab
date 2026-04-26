# Story 27.5: Auto-save policy-set composition draft to localStorage

Status: ready-for-dev

## Story

As an analyst editing a policy set,
I want my unsaved composition changes to be auto-saved as a local draft and offered back to me on the next session,
so that I don't lose work when I close the tab, refresh, or forget to click Save.

## Acceptance Criteria

1. Given the analyst makes any change to the composition (add policy, edit parameter, rename group, change resolution strategy), when 750 ms elapse without further changes, then a draft is written to localStorage at a stable key with shape `{ composition, name, resolutionStrategy, savedAt }`.
2. Given the Policies stage mounts and a draft newer than the loaded policy set is found, when rendered, then a non-blocking banner appears at the top of the composition panel: "You have unsaved changes from {relativeTime}. [Restore] [Discard]".
3. Given the analyst clicks Restore, when actioned, then the draft replaces the current composition and the banner is dismissed.
4. Given the analyst clicks Discard, when actioned, then the draft is cleared from localStorage, the loaded state remains active, and the banner is dismissed.
5. Given the analyst clicks Save (explicit save) and the save succeeds, when complete, then the draft is cleared from localStorage automatically.
6. Given the analyst has unsaved draft changes and attempts to close/refresh the tab, when triggered, then a `beforeunload` warning appears asking to confirm leaving (browser-native dialog).
7. Given two scenarios are open in two tabs, when both edit independent policy sets, then the draft key is namespaced per policy-set ID (or per scenario ID) so drafts do not collide.

## Tasks / Subtasks

- [ ] Create draft autosave hook (AC: #1)
  - [ ] New file `frontend/src/hooks/usePolicySetDraftAutosave.ts`
  - [ ] Subscribe to composition + name + resolutionStrategy changes via the existing AppContext or PoliciesStageScreen state
  - [ ] Debounce writes to 750 ms
  - [ ] Storage key: `reformlab-policy-set-draft:{policySetId | "unsaved"}`
- [ ] Restore banner (AC: #2, #3, #4)
  - [ ] On Policies-stage mount, read the draft and compare `savedAt` with the loaded policy set's `updatedAt`
  - [ ] If the draft is newer, render a banner above the composition panel
  - [ ] Restore: replace composition with draft contents
  - [ ] Discard: clear the draft, leave loaded state
- [ ] Clear-on-save (AC: #5)
  - [ ] In the existing save flow (`usePortfolioSaveDialog`), on success, clear the corresponding draft key
- [ ] Beforeunload warning (AC: #6)
  - [ ] Add a `useEffect` that registers a `beforeunload` listener whenever the draft is dirty (composition differs from loaded state)
  - [ ] Use the standard `event.preventDefault(); event.returnValue = ""` pattern for cross-browser support
- [ ] Per-scenario namespacing (AC: #7)
  - [ ] Use the active policy-set ID as part of the storage key
  - [ ] Fallback for "unsaved new policy set": use a session-scoped UUID stored in sessionStorage so refreshes recover but new tabs don't collide
- [ ] Tests
  - [ ] Hook unit test: edit → 750 ms → localStorage updated
  - [ ] Restore flow test: localStorage seeded → mount → banner → restore → composition replaced
  - [ ] Discard flow test: localStorage seeded → mount → discard → state untouched, key cleared
  - [ ] Save-clears-draft test: dirty draft → save → key removed
  - [ ] Multi-tab namespacing test: two different policy-set IDs → independent drafts
- [ ] Quality gates
  - [ ] `npm test`, `npm run typecheck`, `npm run lint`

## Dev Notes

- This is local-only persistence. Drafts are NOT synced to the backend; only explicit Save calls hit `/api/portfolios`.
- The `usePolicySetDraftAutosave` hook should be small and easily testable — keep persistence side-effects in the hook, render side-effects in the screen.
- localStorage keys must be stable enough across sessions but namespaced enough to avoid collisions. The CLAUDE memory notes the existing pattern in `useScenarioPersistence` — match its export-as-constant convention.

### Project Structure Notes

- New: `frontend/src/hooks/usePolicySetDraftAutosave.ts`, matching test file
- Modified: `PoliciesStageScreen.tsx` (banner rendering), `usePortfolioSaveDialog.ts` (clear-on-save)
- Storage key constant exported alongside other key constants in `useScenarioPersistence.ts` or a new `frontend/src/hooks/storageKeys.ts`

### References

- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md#Story-27.5]
- [Source: frontend/src/hooks/useScenarioPersistence.ts] (pattern to match)
- [Source: User report 2026-04-26 ("if we forget to save it doesn't work")]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
