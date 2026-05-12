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

## Story 27-5 (2026-04-30)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Missing draft version field**: CompositionDraft lacks version field, breaking future schema migrations | Added `version: 1` field to interface with migration logic in load function |
| critical | "Empty composition" undefined**: Story doesn't define what "empty" means (null? undefined? length === 0?) | Defined empty as `composition.length === 0` in AC-2, Task 3.2, and Edge Cases |
| critical | Timestamp type contradiction**: Interface says `number` but comment says "ISO timestamp" (ISO is string) | Changed to `timestamp: number` with comment "Unix epoch milliseconds (Date.now())" |
| critical | Debounce/clear race condition**: Pending autosave timer can re-create draft after explicit clear/load/save | Added explicit requirement to cancel pending timers in Task 2.4 and Task 4 |
| critical | Draft validation insufficient**: AC-8 only handles unparseable JSON, not parseable-but-invalid shapes | Added schema validation requirement to Task 1.4 and AC-8 |
| high | Race condition in instanceCounter capture**: Effect dependencies don't include instanceCounterRef, risking stale value capture | Added explicit note in Task 2.4 about capturing ref value inside debounced callback |
| high | Missing explicit test for AC-6**: No test subtask verifies `activePortfolioName === null` after restore | Added Subtask 5.9 for explicit AC-6 assertion |
| high | Optional affordance creates scope ambiguity**: Task 3.6 has zero specifications for badge UI | Removed Task 3.6 entirely - this affordance is out of scope for Story 27.5 |
| medium | Silent failure scope ambiguous**: "Silent" undefined beyond toasts | Added explicit definition: "no thrown exceptions, no toast calls, no user-visible error UI" |
| medium | Draft clear integration with activeScenario**: Unclear whether draft clear should modify scenario state | Added explicit clarification in Integration Points section |

## Story 27-8 (2026-05-12)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | URL hash separator strategy internally inconsistent: AC-8 shows `#population?source` but `navigateTo` produces `${stage}/${subView}` | Added Dev Note clarifying slash format is used; AC-8 examples were illustrative only |
| critical | LEGACY_POPULATION_SUBVIEW_MAP null-key JavaScript bug: `{ null: "source" }` stores string `"null"` not JS `null` | Updated migration pattern to use explicit null check in Dev Notes code example |
| critical | SubView type union missing new values: Task 1 doesn't explicitly state to add `"source"` and `"inspect"` | Added explicit subtask 1.2a to update SubView type union |
| critical | VALID_SUBVIEWS Set not updated: Adding to type union without updating runtime Set causes `isValidSubView()` to reject new values | Added subtask 1.2b to update VALID_SUBVIEWS Set |
| critical | POPULATION_SUB_STEPS constant structure unspecified: Task 1.2 says "replace with two items" but doesn't specify exact structure | Added exact constant structure in Task 1.2c |
| high | Empty state for Inspect view undefined: AC-5 doesn't specify behavior when user navigates to inspect without population selection | Added AC-9 for empty state behavior with explicit requirements |
| high | Inspect disabled state logic incomplete: AC-2 gates on `selectedPopulationId` but doesn't address durable state (`activeScenario.populationIds`) which Story 27.6 prioritizes | Updated AC-2 to check both transient and durable state signals |
| high | handleExplore behavior after story unspecified: "Explore" button currently navigates to "population-explorer" | Added to Edge Cases section specifying Explore should select population and navigate to inspect |
| high | Task 5 is ghost task: `useScenarioPersistence.ts` only saves `activeStage`, not `activeSubView` | Removed Task 5 entirely; added note to Task 4 clarifying sub-view is URL-only |
| high | E2E test regression not addressed: `population-workflow.test.tsx:205` hard-codes `#population/population-explorer` hash | Added subtask 5.7 to update E2E test |
| high | STAGES.activeFor not in "Files to Modify": Adding `"source"` and `"inspect"` requires updating STAGES constant | Added subtask 1.5 to update STAGES.activeFor array |
| medium | AppContext.test.tsx doesn't exist but referenced in Subtask 6.5 | Changed subtask 5.5 to reference App context testing in existing test files |
| medium | WorkflowNavRail.explorerPopulationId prop dead code after story | Added to Task 3.7: remove dead prop |
| medium | accessibility requirements incomplete: Task 3.3 mentions disabled + title but not ARIA attributes | Added aria-disabled requirement to Task 3.3 |
| medium | Browser back button behavior untested | Added subtask 5.8 for back button test |
| low | PopulationSubStep type will have phantom values after changing POPULATION_SUB_STEPS | Noted but deferred; type will be updated by implementation |
| low | Consider renaming explorerPopulationId to align with new IA vocabulary | Noted as optional suggestion |
| dismissed | AC-3 ambiguous about "Explore" button vs "Select" button | FALSE POSITIVE: Edge Cases section now explicitly covers this; Explore selects population and navigates to inspect |
| dismissed | ContextualHelpPanel has test for activeSubView="data-fusion" that may break | FALSE POSITIVE: Story keeps "data-fusion" in SubView for legacy support (Build New button), so test remains valid |
| dismissed | Story is overly prescriptive about implementation (reduces Negotiable score) | FALSE POSITIVE: For IA changes, specificity is appropriate to prevent implementation drift; INVEST criteria satisfied |
| dismissed | DataFusionResult persistence unspecified | FALSE POSITIVE: AppContext manages dataFusionResult globally; it persists across sub-view changes by existing design, no story change needed |
