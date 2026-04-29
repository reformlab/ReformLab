# Epic 27 - Story Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during validation of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent story-writing mistakes (unclear AC, missing Notes, unrealistic scope).

## Story 27-2 (2026-04-29)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | AC5 references non-existent visual regression test infrastructure | Rewrote AC5 to use className assertion: "Given a PopoverContent component is rendered in tests, when the element's classes are inspected, then the `bg-popover` class is present" |
| critical | Story state internally inconsistent - ready-for-dev with populated Completion Notes/File List | Cleared Dev Agent Record completion sections, replaced with HTML comments: `<!-- Populated after implementation is complete -->` |
| high | AC1 allows two locations for token definition using "or" | Changed AC1 to specify single canonical location: "_bmad-output/branding/theme.css ONLY (tokens must not be defined in frontend/src/index.css)". Added verification step to Tasks. |
| high | AC2 uses subjective language without measurable criteria | Changed from "opaque white (or theme-appropriate) background and readable foreground text" to "opaque white background and slate-900 foreground text that meets WCAG AA contrast requirements" |
| high | AC3 lacks specificity for consumer override verification | Rewrote AC3 to specify exact consumers and verification: "Given the two popover consumers at PortfolioTemplateBrowser.tsx and PortfolioCompositionPanel.tsx, when their className props are inspected, then neither includes bg- background overrides (only sizing/typography classes like w-64 text-xs)" |
| high | Test subtask creates new UI component test pattern without precedent | Changed from creating new `ui/__tests__/popover.test.tsx` to adding test to existing `PoliciesStageScreen.categories.test.tsx` following established patterns |
| medium | AC4 line number reference may be inaccurate | Removed specific line number reference, changed to "in frontend/src/components/ui/popover.tsx (PopoverContent component)" |
| medium | Test subtask references non-existent getComputedStyle pattern | Provided concrete test code using existing toHaveClass pattern from TopBar.test.tsx |
| medium | No explicit accessibility criterion in ACs | Added WCAG AA reference to AC2: "foreground text that meets WCAG AA contrast requirements" |
| low | No verification of Tailwind v4 --color-white availability | Added note to Dev Notes: "Token availability: --color-white is defined in Tailwind v4 defaults (no additional definition needed)" |
| dismissed | Root-cause text mixes `--popover` vs `--color-popover`, which can mislead implementers | FALSE POSITIVE: The Dev Notes correctly explain why `--popover` won't work and `--color-popover` is required. This is educational content, not misleading. |
| dismissed | Should add manual verification steps to Tasks | FALSE POSITIVE: Manual verification is implied for any visual change. Adding explicit manual steps would create bloat across all visual stories. |
| dismissed | Should add empty popover edge case test | FALSE POSITIVE: The bug is about missing theme tokens affecting all popovers equally. Empty popover would render identically, no edge case. |
| dismissed | Should document CSS custom property fallback pattern | FALSE POSITIVE: `var(--color-white)` references a Tailwind v4 built-in that's guaranteed to exist. Adding fallbacks would be defensive programming for a non-existent failure mode. |
