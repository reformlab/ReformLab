---
title: 'Fix Passive Policy-Set Autoload for Non-Portfolio References'
type: 'bugfix'
created: '2026-04-26'
status: 'in-review'
baseline_commit: 'dbad85b7d78bfd9fbc51e5fcf9f63be32b5cdaf0'
context:
  - '{project-root}/_bmad-output/project-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/24-1-publish-canonical-catalog-and-api-exposure-for-already-modeled-hidden-policy-packs.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-establish-appcontext-integration-testing.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The current branch is not merge-ready because the Policies stage passively auto-loads any `activeScenario.portfolioName` through `/api/portfolios/{name}`. When restored or pre-existing scenario state contains a non-portfolio reference such as `carbon-plus-rebate`, the UI emits duplicate "Could not load policy set" warnings even though the user did not explicitly ask to load a saved policy set.

**Approach:** Tighten passive autoload so it only hydrates composition from names that are known saved portfolios in the current workspace. Preserve the existing explicit load-dialog failure behavior for real user actions, add regression coverage for restored non-portfolio references, and leave the current AppContext naming work intact while making the branch safe to merge to `master`.

## Boundaries & Constraints

**Always:** Preserve successful autoload for real saved portfolios; preserve explicit warning toasts when the user actively selects a missing portfolio from the load dialog; keep `WorkspaceScenario.portfolioName` semantics unchanged; avoid disturbing the uncommitted AppContext integration-testing work already present in the tree.

**Ask First:** Any fix that requires changing the persisted scenario schema, reinterpreting `portfolioName` as a different field, clearing user-saved scenarios automatically, or altering visible UX copy beyond the erroneous passive warning behavior.

**Never:** Do not hide explicit user-triggered portfolio load failures; do not add destructive git cleanup, history rewriting, or storage wipes; do not broaden this into a catalog/portfolio architecture rewrite.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Passive restore with non-portfolio reference | `activeScenario.portfolioName` is set, composition is empty, and the name is not present in the current saved portfolio list | Policies stage does not call portfolio detail load, does not toast a warning, and leaves composition empty for manual correction | Silent no-op for passive hydration only |
| Passive restore with saved portfolio | `activeScenario.portfolioName` matches a saved portfolio name and composition is empty | Policies stage autoloads the saved portfolio once and hydrates composition normally | Existing failure handling remains if backend unexpectedly breaks |
| Explicit user load failure | User opens the load dialog and clicks a portfolio that now fails to load | Existing warning toast appears and scenario state is not corrupted | Preserve current `ApiError` / generic error messaging |
| Re-render after passive skip | Same unmatched `portfolioName` persists across subsequent renders | No repeated fetch attempts or duplicate warnings | Idempotent skip behavior |

</frozen-after-approval>

## Code Map

- `frontend/src/hooks/usePortfolioLoadDialog.ts` -- Owns passive autoload effect and explicit load-dialog behavior; likely primary fix point.
- `frontend/src/components/screens/PoliciesStageScreen.tsx` -- Supplies active scenario and saved portfolio context to the load-dialog hook.
- `frontend/src/components/screens/__tests__/PoliciesStageScreen.test.tsx` -- Existing screen-level regression coverage for autoload, load failure, and scenario linkage.
- `frontend/src/contexts/AppContext.tsx` -- Already contains local uncommitted naming-state fixes; must remain compatible and must not be reverted while making the branch merge-ready.
- `frontend/src/contexts/__tests__/AppContext.integration.test.tsx` -- New local coverage that should continue passing after the portfolio autoload guard is introduced.

## Tasks & Acceptance

**Execution:**
- [x] `frontend/src/hooks/usePortfolioLoadDialog.ts` -- Distinguish passive autoload from explicit user loads, and gate passive autoload on the current known saved-portfolio names so non-portfolio references are skipped without warning -- removes the erroneous `carbon-plus-rebate` toast while preserving intentional error feedback.
- [x] `frontend/src/components/screens/PoliciesStageScreen.tsx` -- Pass the saved portfolio list or equivalent membership signal into the hook and preserve current load/save/clone wiring -- keeps the guard driven by real workspace state instead of hard-coded heuristics.
- [x] `frontend/src/components/screens/__tests__/PoliciesStageScreen.test.tsx` -- Add regressions for passive skip on unmatched `portfolioName`, one-shot passive autoload for matched portfolios, and preserved explicit load failure warnings -- locks the branch against recurrence.

**Acceptance Criteria:**
- Given a restored scenario references `portfolioName: "carbon-plus-rebate"` and no saved portfolio with that name exists, when the Policies stage mounts, then no passive warning toast appears and no portfolio detail fetch is attempted for that name.
- Given a restored scenario references a real saved portfolio and composition is empty, when the Policies stage mounts, then the saved portfolio loads into composition exactly once.
- Given a user explicitly clicks a saved-portfolio row that fails to load, when the request rejects, then the warning toast still appears and `activeScenario.portfolioName` is not updated to a bad state.
- Given the current AppContext naming changes are present in the working tree, when this bugfix is applied, then the branch remains compatible with those files and can be verified before merge.

## Spec Change Log

## Design Notes

The core distinction is intent, not transport. A passive restore path should be conservative because it is replaying stored state the user may no longer control, while the explicit load dialog is a fresh user action and should continue surfacing backend problems. The simplest robust design is to give the hook enough information to answer "is this name currently a saved portfolio?" before it decides to auto-fetch.

That means avoiding brittle string heuristics such as "if the name looks like a template id, skip it." A membership check against the actual portfolio list is better because it covers built-in pack names, stale deleted portfolios, and any other non-portfolio reference with one rule. If the list has not loaded yet, the passive effect should wait until it can make a correct membership decision rather than fetching optimistically and warning incorrectly.

## Verification

**Commands:**
- `cd frontend && npm test -- src/components/screens/__tests__/PoliciesStageScreen.test.tsx` -- expected: new passive-autoload and explicit-failure regressions pass.
- `cd frontend && npm test -- src/contexts/__tests__/AppContext.integration.test.tsx` -- expected: existing local AppContext integration coverage still passes.
- `cd frontend && npm run typecheck` -- expected: TypeScript accepts the hook signature and screen wiring changes.

### Review Findings

Reviewed 2026-04-26 via bmad-code-review (3 layers: Blind Hunter, Edge Case Hunter, Acceptance Auditor). Acceptance Auditor returned a clean report. Blind + Edge layers raised the items below.

Note: the Acceptance Auditor verified that Vitest does in fact run on the current Node 22.22.0 runtime (`PoliciesStageScreen.test.tsx` 55/55 + `AppContext.integration.test.tsx` 4/4 + `typecheck` clean), contrary to the implementation's claim that local Vitest was blocked.

- [ ] **[Review:Decision]** `selectedPortfolioName` not reset on `createScenario`/`cloneScenario` paths — `resetToDemo` adds `setSelectedPortfolioName(null)` but `createScenario` (around `frontend/src/contexts/AppContext.tsx:639-643`) and `cloneScenario` (around `:659-663`) do not. Stale UI selection can carry into a fresh/cloned scenario and seed the auto-name suggestion. Treat as decision-needed because this is in the auxiliary AppContext naming work, not in this spec's autoload-fix scope.
- [ ] **[Review:Decision]** Loaded-name guard does not invalidate on direct `activeScenario.portfolioName` / `populationIds` mutation (`frontend/src/contexts/AppContext.tsx:531-541`) — guard compares only `selectedPortfolioName` / `selectedPopulationId`. If the user mutates the scenario fields via `updateScenarioField`, the guard remains active and freezes the suggested name. Decision-needed because this is auxiliary AppContext naming work.
- [ ] **[Review:Decision]** Empty `populationIds` in restored scenario invalidates loaded-name guard (`frontend/src/contexts/AppContext.tsx:335-345, 464-468, 534-541`) — when saved `populationIds=[]`, the default-selection effect later sets `selectedPopulationId` to `populations[0].id`, the guard sees a context change, clears the marker, and auto-renames a freshly restored named scenario. Integration-test fixture always seeds `populationIds`, so the case is uncovered. Decision-needed because this is auxiliary AppContext naming work.
- [ ] **[Review:Patch]** Skip-marker leaks across portfolio-list updates, blocking deferred autoload (`frontend/src/hooks/usePortfolioLoadDialog.ts:135-141`) — when `availablePortfolioNames` does not yet contain the active scenario's `portfolioName`, the patch writes `loadedPortfolioRef.current = activeScenarioPortfolioName` and returns. If portfolios later refetch and the matching name appears, the effect early-exits at the ref-equality check and never autoloads. Fix: do not mutate `loadedPortfolioRef` in the membership-fail branch; just `return`.
- [ ] **[Review:Patch]** `availablePortfolioNames` is a fresh array per render (`frontend/src/components/screens/PoliciesStageScreen.tsx:555`) — `portfolios.map(...)` produces a new array reference every render, so the autoload effect re-fires every render of `PoliciesStageScreen`. Functionally bounded by early-returns but amplifies the skip-marker leak above and is needless work. Fix: wrap in `useMemo(() => portfolios.map((p) => p.name), [portfolios])`.
- [ ] **[Review:Patch]** Test coverage gaps for autoload state transitions (`frontend/src/components/screens/__tests__/PoliciesStageScreen.test.tsx:509-557`) — no test covers (a) `portfoliosLoading: true → false` transition (a regression dropping the loading-gate guard would still pass), and (b) deferred autoload when the matching name appears in `portfolios` after the first render (would pin the skip-marker fix above). Fix: add the two missing rerender tests.
- [ ] **[Review:Patch]** Explicit-failure toast not regression-locked against duplicates (`frontend/src/components/screens/__tests__/PoliciesStageScreen.test.tsx:428`) — original symptom was duplicate warnings, but `toHaveBeenCalledWith(...)` matches at-least-once. Fix: also assert `toHaveBeenCalledTimes(1)`.
- [x] **[Review:Defer]** Auto-name effect dep includes `activeScenarioName`, causing self-retrigger (`frontend/src/contexts/AppContext.tsx:550-560`) — deferred, AppContext naming-effect cosmetic; converges idempotently in one extra render. No correctness impact.
