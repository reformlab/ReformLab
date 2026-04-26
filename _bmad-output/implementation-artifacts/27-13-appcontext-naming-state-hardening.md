# Story 27.13: AppContext naming-state hardening

Status: ready-for-dev

## Story

As a frontend developer maintaining scenario state,
I want the AppContext naming logic to handle create-from-scratch, clone, direct-field-mutation, and empty-populationIds restore correctly,
so that auto-name suggestions and the manual-edit freeze rule work in the four edge cases the 26.7 review flagged but did not fix.

## Acceptance Criteria

1. Given the analyst calls `createScenario`, when a new scenario is created, then `selectedPortfolioName` is reset to `null` so a stale UI selection from a previous scenario does not seed the auto-name suggestion.
2. Given the analyst calls `cloneScenario`, when a clone is created, then `selectedPortfolioName` is reset and the clone's name follows the existing clone-naming rule (e.g., "Original — copy"), not a fresh auto-suggestion.
3. Given the loaded-scenario name guard at `AppContext.tsx:531-541`, when `activeScenario.portfolioName` or `activeScenario.populationIds` is mutated directly via `updateScenarioField()`, then the guard is invalidated so the auto-name effect can recompute.
4. Given a restored scenario where `populationIds === []` (empty), when the default-selection effect later sets `selectedPopulationId` to `populations[0].id`, then the guard correctly distinguishes "user has not picked a population" from "user explicitly chose population[0]" and does not auto-rename a freshly restored named scenario.
5. Given the auto-name effect at `AppContext.tsx:550-560`, when `activeScenarioName` is in the dep array, then the effect uses a functional setter or a name-ref read so `activeScenarioName` does not need to be a dep (idempotent convergence in one render instead of two).
6. Given existing `AppContext.integration.test.tsx` coverage, when this story is complete, then the four edge cases above each have an integration test, and all existing tests still pass.

## Tasks / Subtasks

- [ ] Reset `selectedPortfolioName` on create/clone (AC: #1, #2)
  - [ ] In `AppContext.tsx`, around `createScenario` (lines ~639-643) and `cloneScenario` (lines ~659-663), call `setSelectedPortfolioName(null)`
  - [ ] Match the existing `resetToDemo` pattern
- [ ] Invalidate guard on direct mutation (AC: #3)
  - [ ] At `AppContext.tsx:531-541`, expand the guard's dep set to include scenario-level fields: when `activeScenario.portfolioName` or `activeScenario.populationIds` change, clear the guard
  - [ ] Or: switch the guard to compare against the active scenario's fields rather than the standalone selection state
- [ ] Handle empty populationIds restore (AC: #4)
  - [ ] At `AppContext.tsx:335-345`, `:464-468`, `:534-541`, distinguish "restored with `populationIds: []`" from "restored with explicit population", e.g., introduce a `restoredFromStorage: boolean` flag and skip the rename for restored scenarios with explicit non-default names
  - [ ] Add a fixture test that seeds `populationIds: []` plus a saved name; assert the saved name is preserved after restore
- [ ] Tighten auto-name effect deps (AC: #5)
  - [ ] At `AppContext.tsx:550-560`, refactor the effect to use `setActiveScenario((current) => ...)` so it doesn't depend on the post-update `activeScenarioName`
  - [ ] Remove `activeScenarioName` from the dep array
- [ ] Tests (AC: #6)
  - [ ] Add four new integration tests in `AppContext.integration.test.tsx`, one per edge case
  - [ ] Verify existing tests still pass
- [ ] Quality gates
  - [ ] `npm test`, `npm run typecheck`, `npm run lint`

## Dev Notes

- The four cases are taken verbatim from the review section of `spec-fix-passive-policy-set-autoload-for-non-portfolio-references.md` lines 82–89, deferred from Story 26.7 because they were classified as auxiliary AppContext naming work.
- Coordinate with Story 27.6 (nav-rail "not started" state): the touched/complete logic added there shares some restore-path code; ensure the two stories don't conflict on the restore migration.

### Project Structure Notes

- Files touched: `frontend/src/contexts/AppContext.tsx`, `frontend/src/contexts/__tests__/AppContext.integration.test.tsx`
- No new files

### References

- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md#Story-27.13]
- [Source: _bmad-output/implementation-artifacts/spec-fix-passive-policy-set-autoload-for-non-portfolio-references.md#Review-Findings] (lines 82–89)
- [Source: _bmad-output/implementation-artifacts/spec-establish-appcontext-integration-testing.md] (testing harness)

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
