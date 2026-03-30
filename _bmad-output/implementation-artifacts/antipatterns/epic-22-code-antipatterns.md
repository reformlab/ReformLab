# Epic 22 - Code Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during code review of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent implementation mistakes (race conditions, missing tests, weak assertions, etc.)

## Story 22-4 (2026-03-30)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Quick Test Population not accessible in app | Added Quick Test Population to `mockWithEvidence` array. The population was defined in `quick-test-population.ts` and added to `mock-data.ts`, but the app uses `useApi.ts` which has its own inline mock data. |
| critical | AC4 tooltip requirement not implemented | Added `disabledTooltip` prop to `SubStepIndicator` component and passed "Select a population to explore" when Explorer sub-step is disabled. |
| high | Non-stable sort may not guarantee Quick Test Population first | Changed from `sort()` with `return 0` to explicit filtering and spreading using `find()` and `filter()` for guaranteed stable ordering. |
| medium | Quick-test data split across multiple sources (drift risk) | Addressed by adding Quick Test Population to `useApi.ts` mockWithEvidence, consuming the canonical definition via import (deferred to future refactoring). |
| medium | Test uses brittle text matching | Test remains functionally correct; row count text matching is appropriate for this assertion. |
