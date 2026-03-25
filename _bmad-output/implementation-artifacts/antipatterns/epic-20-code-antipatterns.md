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
