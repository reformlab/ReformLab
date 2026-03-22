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

## Story 18-3 (2026-03-22)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | `onTemplatesChanged` never wired in App.tsx — custom template creation silently succeeds but list doesn't refresh | Destructured `refetchTemplates` from `useAppState()` and passed as `onTemplatesChanged` to `TemplateSelectionScreen` |
| high | `is_custom` field dropped in `mapTemplate()` — API-sourced templates never show the custom badge | Added `is_custom: item.is_custom` to mapped object |
| medium | `WorkbenchStepper` buttons missing `aria-current="step"` — active step not semantically indicated to screen readers | Added `aria-current={isActive ? "step" : undefined}` |
| medium | `SelectionGrid` buttons missing `aria-pressed` — selected state is visual-only, invisible to screen readers | Added `aria-pressed={selected}` |
| medium | `Number(...) | Replaced with `Number.isFinite(Number(v)) ? Number(v) : 0` |
| low | `WorkbenchStepper` buttons lack `focus-visible:ring` — missing consistent keyboard focus style (antipattern from Story 18.1) | Added `focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2` |

## Story 18-4 (2026-03-22)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | Stale detail race condition — `getResult(runA)` response commits to state after run switches to B, overwriting the reset from `useEffect` | Added `activeRunIdRef`, capture `capturedRunId` before await, guard all three state commits with `activeRunIdRef.current === capturedRunId` |
| medium | AC-1 mock mode shows hardcoded `"Results"` instead of `reformLabel` | Changed to `{reformLabel}` and added "—" year badge in mock branch |
| medium | AC-1 year range badge suppressed (null) instead of showing "—" when `years` is empty | Always render badge; `{yearRange ?? "—"}` |
| medium | Test at line 123 asserts `"Results"` (wrong requirement encoding) | Updated to assert `reformLabel` value and absence of "Results" |
| medium | Test at line 129 asserts no badge instead of "—" badge (wrong requirement encoding) | Updated to assert `getByText("—")` |
| medium | `WorkflowNavRail` nav buttons missing `aria-pressed` (recurring antipattern from 18.1/18.3) | Added `aria-pressed={active}` |
| low | `+0` displayed when non-zero deltas average to exactly zero (rounded) | Extract `roundedMean`, use `roundedMean === 0 ? "0" : ...` |
| low | AC-4 requires "No indicator data" note for empty/all-zero `decileData`; note missing | Added `isPlaceholder` flag; conditionally render `<p>No indicator data available.</p>` |

## Story 18-6 (2026-03-22)

| Severity | Issue | Fix |
|----------|-------|-----|
| medium | `Select` component missing `focus-visible:ring` keyboard focus indicator — `outline-none` removes the browser default with only a subtle border-color change as replacement, which fails the keyboard accessibility standard documented as a recurring Epic 18 antipattern (first flagged in Story 18-1 for nav buttons, 18-2 for `button.tsx`/`input.tsx`) | Added `focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2` to base class string |
| low | The 3 skeleton loading containers replaced visible "Loading…" text (which is readable by screen readers) with purely visual pulses, creating a semantic loading state regression for assistive technology | Added `aria-busy="true" role="status"` to each container with a `<span className="sr-only">Loading …</span>` inside |

## Story 18-7 (2026-03-22)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | `conceptsOpen` state never resets when `viewMode`/`activeStep` changes — once "Key Concepts" is opened in one stage it remains expanded when the user navigates to another stage that also has concepts, violating AC-3 "collapsed by default" | Added `useEffect(() => { setConceptsOpen(false); }, [viewMode, activeStep])` and `useEffect` import. |
| medium | No test for AC-3 default-collapsed state or expand-on-click behavior; tests only checked text presence of trigger | Added tests: "Key Concepts section is collapsed by default (AC-3)", "Key Concepts section expands when trigger is clicked (AC-3)", "resets Key Concepts to collapsed when navigating (AC-3)". |
| medium | No rerender test for AC-1 "updates automatically when user navigates to a different stage" | Added test "updates content automatically when viewMode changes (AC-1)" using `rerender`. |

## Story 18-8 (2026-03-22)

| Severity | Issue | Fix |
|----------|-------|-----|
| medium | No tests for `PopulationDistributionChart` — AC-3 (`rounded-lg`) and AC-4 (single fill, no `Cell`) were unguarded | Created test file with 3 tests: title rendering, empty-data null return, AC-3 `rounded-lg` class assertion. |
| low | `CHART_COLORS` and `DECISION_COLORS` exported as mutable `string[]`, allowing accidental runtime mutation | Added `as const` to both array literals; aligns with existing `RELATIVE_COLORS` which already used `as const`. |
