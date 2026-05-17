# Story 27.0: Close out story-26.7 review patches and retro EPIC-26

Status: ready-for-dev

## Story

As a developer closing out EPIC-26,
I want to land the seven outstanding code-review patches identified for story 26.7 and run the EPIC-26 retrospective addendum,
so that EPIC-26 can be marked done and EPIC-27 can build on a clean branch.

## Acceptance Criteria

1. Given the passive-autoload guard in `usePortfolioLoadDialog.ts`, when `availablePortfolioNames` does not yet contain the active scenario's `portfolioName`, then the membership-fail branch must NOT mutate `loadedPortfolioRef.current` — it must return without writing the marker so a deferred autoload can still fire when the matching name appears later.
2. Given `PoliciesStageScreen.tsx` passes `availablePortfolioNames` to the load-dialog hook, when the screen rerenders, then the array reference must be stable across renders unless `portfolios` changes (wrap in `useMemo`).
3. Given the autoload-state-transition tests in `PoliciesStageScreen.test.tsx`, when run, then they must cover (a) `portfoliosLoading: true → false` rerender (regression of the loading-gate guard) and (b) deferred autoload when the matching name appears in `portfolios` after the first render.
4. Given the explicit-failure regression in `PoliciesStageScreen.test.tsx`, when assertion runs, then it must include `toHaveBeenCalledTimes(1)` so duplicate warnings cannot regress.
5. Given EPIC-26 is being closed, when story 26.7 is marked done, then `sprint-status.yaml` is updated and an EPIC-26 retrospective addendum is appended documenting: "AppContext naming-state issues deferred to EPIC-27 story 27.13" and "passive-autoload guard pattern established as canonical (see feedback memory)".
6. Given all quality gates run, when complete, then `npm test`, `npm run typecheck`, `npm run lint`, `uv run pytest tests/`, `uv run ruff check src/ tests/`, `uv run mypy src/` all pass.

## Tasks / Subtasks

- [ ] Apply Review:Patch fixes to `usePortfolioLoadDialog.ts` (AC: #1)
  - [ ] Remove `loadedPortfolioRef.current = activeScenarioPortfolioName` assignment in the membership-fail branch around lines 135–141
  - [ ] Verify the early-return path no longer pins the marker
- [ ] Stabilise `availablePortfolioNames` reference (AC: #2)
  - [ ] Wrap `portfolios.map((p) => p.name)` in `useMemo([portfolios])` at `PoliciesStageScreen.tsx:555`
- [ ] Add transition-state regression tests (AC: #3)
  - [ ] Add test for `portfoliosLoading: true → false` rerender
  - [ ] Add test for deferred autoload when portfolio appears in subsequent fetch
- [ ] Tighten explicit-failure assertion (AC: #4)
  - [ ] Add `toHaveBeenCalledTimes(1)` to the existing `toHaveBeenCalledWith(...)` assertion at `PoliciesStageScreen.test.tsx:428`
- [ ] Mark 26.7 done and write retro addendum (AC: #5)
  - [ ] Update `sprint-status.yaml`: `26-7-...: done`, `epic-26: done`
  - [ ] Append addendum to `_bmad-output/implementation-artifacts/retrospectives/epic-26-retro-20260422.md`
- [ ] Quality gate (AC: #6)
  - [ ] Run all six commands; all green

## Dev Notes

- The four "Decision" items from the 26.7 review (selectedPortfolioName not reset on createScenario/cloneScenario; loaded-name guard not invalidated on direct field mutation; empty `populationIds` invalidates loaded-name guard; auto-name effect dep self-retrigger) are NOT in this story — they are scheduled as story 27.13.
- The toast-policy memory `feedback_error_toasts_user_initiated_only.md` is the canonical reference for why the passive-autoload guard is silent.

### Project Structure Notes

- Files touched: `frontend/src/hooks/usePortfolioLoadDialog.ts`, `frontend/src/components/screens/PoliciesStageScreen.tsx`, `frontend/src/components/screens/__tests__/PoliciesStageScreen.test.tsx`, `_bmad-output/implementation-artifacts/sprint-status.yaml`, `_bmad-output/implementation-artifacts/retrospectives/epic-26-retro-20260422.md`
- No new files

### References

- [Source: _bmad-output/implementation-artifacts/spec-fix-passive-policy-set-autoload-for-non-portfolio-references.md#Review-Findings]
- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md#Section-4.0]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
