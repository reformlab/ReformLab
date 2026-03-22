# Epic 18 - Code Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during code review of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent implementation mistakes (race conditions, missing tests, weak assertions, etc.)

## Story 18-1 (2026-03-22)

| Severity | Issue | Fix |
|----------|-------|-----|
| medium | `focus:outline-none` on nav rail buttons strips the browser's keyboard focus ring with no visible replacement, creating an accessibility regression for keyboard users. | Added `focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2` alongside the outline removal. |
| low | Unnecessary `as string[]` cast on `stage.activeFor.includes(viewMode)` — `activeFor: WorkflowViewMode[]` and `viewMode: WorkflowViewMode` are already compatible; the cast bypasses TypeScript's type-safety. | Removed the cast; type check confirms no errors. |
