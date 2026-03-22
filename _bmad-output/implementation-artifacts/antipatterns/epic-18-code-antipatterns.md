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

## Story 18-2 (2026-03-22)

| Severity | Issue | Fix |
|----------|-------|-----|
| medium | `PopulationValidationPanel.tsx` per-marginal result rows (line 59) missing `rounded-lg` — Task 2.11 marked done but incomplete | Added `rounded-lg` to the per-marginal row `<div>` |
| medium | `ComparisonDashboardScreen.tsx` run-selector `<ul>` (line 173) missing `rounded-lg` — Task 2.3 marked done but the inner `<ul>` was missed | Added `rounded-lg` to the `<ul className="divide-y ...">` element |
| low | `button.tsx` base class missing `rounded-md` — AC-1 states "Buttons and inputs already use `rounded-md` from shadcn defaults"; the custom shadcn implementation omitted it | Added `rounded-md` to the `cva` base string |
| low | `input.tsx` base class missing `rounded-md` — same as above | Added `rounded-md` to the base class string |
| low | `App.tsx:253` header subtitle `text-indigo-600/70` yields ~3.1:1 contrast on white, failing WCAG AA (4.5:1 required for 14px text) | Changed to `text-indigo-700` which passes AA while maintaining brand color |
