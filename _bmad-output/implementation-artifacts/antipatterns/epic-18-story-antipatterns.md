# Epic 18 - Story Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during validation of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent story-writing mistakes (unclear AC, missing Notes, unrealistic scope).

## Story 18-2 (2026-03-22)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | AC-2 lists the login card as a `shadow-sm` container while AC-4 explicitly assigns it `shadow-lg` — direct spec conflict | Removed "the login card" from AC-2's scope; clarified that login card and modals use `shadow-lg` as elevated floating surfaces. |
| critical | AC-1 "all Card, section, and panel containers across all 9 screens" is unbounded — could include structural chrome (LeftPanel, RightPanel) that the story explicitly excludes in Files NOT to Modify | AC-1 now references the Codebase Inventory as the bounded target list and explicitly names structural layout chrome exclusions. |
| critical | Task 5.1 adds `overflow-hidden` to the workspace frame with no corresponding verification that dropdown menus, tooltips, popovers, and overlay panels still render correctly | Added Task 6.5 with explicit overlay verification across ParameterEditingScreen, SimulationRunnerScreen, and ComparisonDashboardScreen. |
| high | Task 6.4 ("Visually verify at 1280px viewport that no layouts overflow or break") is too sparse to objectively verify a 15-file visual sweep | Expanded 6.4 into a five-point checklist covering overflow, container rounding, shadow hierarchy, header/login rendering, and text contrast. |
| medium | AC-1 wording "panel containers" conflicts with the exclusion of LeftPanel/RightPanel in Files NOT to Modify | Addressed by AC-1 update (Critical fix 2) — "content panel containers" with explicit exclusions named. |

## Story 18-3 (2026-03-22)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | AC-4 contradicts Dev Notes — "visual output identical to before" conflicts with the explicit instruction to normalize ErrorAlert styling across 4 screens (different icon sizes, spacing, typography) | AC-4 now explicitly permits visual normalization for ErrorAlert while requiring identical output for WorkbenchStepper and SelectionGrid. |
| critical | AC-5 / Task 4.2 dead-code deletion relies solely on grep, which misses barrel exports, dynamic imports, and test-only references | AC-5 now requires grep + typecheck passing post-deletion. Task 4.2 now explicitly requires running typecheck and tests immediately after deletion. |
| medium | AC-4's hardcoded "259/259" test count is self-contradictory — this story adds 3 new test files, so the post-story count can't equal 259/259 | Task 5.4 now reads "0 failures; total count will exceed pre-story baseline due to new component tests"; AC-4 now reads "all pre-existing tests pass". |
| medium | extractErrorDetail disposition is ambiguous ("Consider... or leave it... Check before deciding") — dev agent would branch | Dev Notes now decisively state "Leave it in BehavioralDecisionViewerScreen — it is the only consumer." |
