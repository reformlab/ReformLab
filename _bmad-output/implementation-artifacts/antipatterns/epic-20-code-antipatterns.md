# Epic 20 - Code Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during code review of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent implementation mistakes (race conditions, missing tests, weak assertions, etc.)

## Story 20-1 (2026-03-25)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | Double `refetchResults()` call in auth effect — fires two concurrent `GET /api/results` on every login | Removed the first `refetchResults().catch(() => {})` call at top of the `isAuthenticated` block |
| medium | Silent `null` render for `#results/decisions` without a prior run — blank screen with no user feedback | Added empty-state `<div>` with informative text when `runResult?.run_id` is falsy |
| medium | AC-5 test gap — no test covers `#results/decisions` route | Added new test "renders empty-state for #results/decisions when no run result exists" |
| low | `STAGES.activeFor` typed as `string[]` instead of `(StageKey | Changed type to `(StageKey \| SubView)[]` |
| low | No-op `navigateTo("results", "runner")` in handleStartRun catch block | Removed the call, replaced with comment |
| low | TopBar icons not interactive — deferred (no target URLs defined in story) | Deferred to follow-up |
| low | SubView validation is global, not stage-aware — deferred (zero functional impact) | Deferred to follow-up |
| low | Task 9.5 test is a tautology — deferred (AC-3 is a compile-time guarantee) | Deferred to follow-up |
| dismissed | Engine stage completion always false (CRITICAL per Reviewer B) | FALSE POSITIVE: This is explicitly expected behavior. Story Dev Notes state "Engine validation (Story 20.5) will use a check registry — this story just establishes the routing shell." Task 8.3 says `activeScenario` is added "alongside (not replacing) existing fields" and wiring is deferred to stories 20.3–20.6. Not a bug — by design. |
| dismissed | `navigateTo` state-async hazard in `handleStartRun` | FALSE POSITIVE: `startRun()` does not read `activeStage` or `activeSubView` — it reads template ID, parameter values, and population ID, none of which depend on routing state. No race condition exists. |
| dismissed | Redundant `shrink-0` wrapper in WorkspaceLayout | FALSE POSITIVE: While technically redundant, double `shrink-0` is harmless CSS (idempotent property) and removing the wrapper would require restructuring the slot pattern. Not worth changing. |

## Story 20-2 (2026-03-25)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | `initializedRef` never reset on logout — re-login within same Provider lifetime skips scenario initialization | Added `initializedRef.current = false` in `logout` callback |
| high | `loadSavedScenario` and returning-user restore don't sync legacy `selectedTemplateId`/`selectedPopulationId` — `startRun()` could use stale values | Added `setSelectedTemplateId`/`setSelectedPopulationId` calls when restoring or loading scenarios |
| medium | `useScenarioPersistence` creates unstable function refs every render, cascading into useCallback/useMemo dependency arrays, forcing unnecessary re-renders | Converted all functions to module-level exports; hook retained as thin deprecated wrapper for backward compatibility |
| medium | `ScenarioEntryDialog` missing Escape key handler and backdrop-click-to-close | Added `onKeyDown` (Escape) and `onClick` (backdrop) handlers |
| medium | `aria-label` on dialog div instead of `aria-labelledby` referencing the heading | Changed to `aria-labelledby="scenario-dialog-title"` with `id` on `<h2>` |
| medium | `s.engineConfig.startYear` in saved scenario list can crash on malformed localStorage data | Added conditional rendering guard `{s.engineConfig && (...)}` |
| low | `loadStage()` returns unchecked cast `raw as StageKey` instead of validating | Added `isValidStage(raw) ? raw : null` validation |
| low | AC-4 test gap — no test clicks Run and asserts `runScenario` called with demo params | Deferred to review follow-up task |
| low | `authenticate` test helper asserts always-visible nav rail label, fragile for first-launch paths | Not applied — helper is functional and all actual test assertions check correct state (hash, screen content). Improving the helper is desirable but low priority. |
| dismissed | AC-3 partial — "Create new scenario from template" has no template selection in dialog | FALSE POSITIVE: By design. The "New Scenario" action creates a draft scenario and navigates to the Policies stage where template selection occurs. The story's task list (4.4) describes four action cards, not inline template pickers. The story Dev Notes confirm the dialog-to-policies-stage flow. |
| dismissed | Story file list incomplete vs branch diff (36 files vs 11 documented) | FALSE POSITIVE: The git diff includes Story 20.1 changes (stage screens, nav rail refactor, workspace layout) and branding changes (favicons, logos) that were committed separately. Story 20.2's file list correctly documents only its own changes. The diff overlap is expected on a feature branch with multiple stories. |
