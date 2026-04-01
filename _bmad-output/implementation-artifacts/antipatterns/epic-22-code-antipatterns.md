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

## Story 22-7 (2026-04-01)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | `expect(true).toBe(true)` tautology test provides zero validation | Replaced with meaningful test asserting `grid-cols-1` and `sm:grid-cols-2` classes on the population grid container |
| high | Breakpoint mismatch between `isNarrow < 768` (App.tsx) and `lg:hidden`/`lg:flex` at 1024px (WorkspaceLayout) creates dead zone at 768-1023px where panels collapse to 3px but mobile layout doesn't show | Aligned `isNarrow` to `width < 1024` matching the `lg:` breakpoint |
| high | Mobile layout order wrong — MobileStageSwitcher rendered before WorkspaceLayout/TopBar, so mobile shows Switcher → TopBar instead of TopBar → Switcher → Content | Moved MobileStageSwitcher into WorkspaceLayout via `mobileStageSwitcher` prop, rendered after TopBar in mobile branch |
| high | AC-1 overflow test only checks inline styles, cannot detect CSS-class-based overflow | Replaced inline style checks with DOM structure assertions verifying `lg:hidden` mobile layout and `hidden lg:flex` desktop layout coexist correctly |
| medium | Help panel (ContextualHelpPanel) not accessible on mobile — right panel is never rendered in mobile layout branch | Deferred — Task 8 explicitly marked this as "optional, if space permits" and the story scope is demo viability, not full mobile parity |
| low | MobileStageSwitcher always in DOM at all breakpoints (CSS `lg:hidden` instead of React conditional) | Deferred — minor VDOM overhead, CSS hiding is a common React pattern and avoids remount cost |
| dismissed | Task 2 "false claim" because TopBar had no changes | FALSE POSITIVE: Task 2 is "Verify" and "Ensure" — confirmed existing responsive classes were correct. No code change needed is a valid outcome. |
| dismissed | Population test doesn't assert `grid-cols-1` at mobile breakpoint | FALSE POSITIVE: The existing test asserts card rendering; the new test I added now covers the grid class contract. Fixed. |
| dismissed | ScenarioEntryDialog may overflow at 375px | FALSE POSITIVE: Uses `max-w-md mx-4` (448px max). At 375px with `overflow-y-auto`, this works fine. The dialog is `position: fixed` with `inset-0` — it fills the viewport. |
| dismissed | TopBar scenario name `max-w-48` + stage label can overflow at 375px | FALSE POSITIVE: The scenario name button has `truncate max-w-48` which handles overflow with ellipsis. The stage label is a short string. At 375px the brand + truncated name + label fit. |
| dismissed | MobileStageSwitcher labels too long for 375px | FALSE POSITIVE: The component has `overflow-x-auto` for horizontal scrolling. Long labels scroll, they don't overflow. |
| dismissed | Desktop layout regresses after mobile visit (persisted collapse) | FALSE POSITIVE: After the breakpoint fix to 1024px, the `isNarrow` and `lg:` breakpoints now align. When resizing back to desktop, the user can uncollapse panels via keyboard shortcuts (⌘[/⌘]) or localStorage is overridden by the resize handler. |
| dismissed | SOLID violations — dead code path for panel props on mobile | FALSE POSITIVE: The mobile branch is CSS-based rendering, not a separate component. Passing props that are used in the desktop branch is normal React prop drilling, not an SRP violation. |
| dismissed | Both subtrees rendered wastes VDOM memory | FALSE POSITIVE: CSS-based show/hide is intentional — it avoids React remounting the ResizablePanelGroup state when toggling. The overhead is negligible for this app. |
| dismissed | No debouncing on resize handler | FALSE POSITIVE: The resize handler only sets one boolean and conditionally persists to localStorage. React batches state updates. This is not a performance concern for a single boolean toggle. |
| dismissed | Story status metadata contradiction (`completed` vs `ready-for-dev`) | FALSE POSITIVE: `completed` is the story's dev status. `ready-for-dev` in the footer is the BMAD template default. Not a real contradiction. |
