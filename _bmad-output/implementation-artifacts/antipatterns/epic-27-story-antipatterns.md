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

## Story 27-9 (2026-05-13)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | AC-7 regex typo: `[a-z7-9]` excludes digits 0-6 | Changed to `[a-z0-9]` in AC-7 |
| critical | Parameter schemas source not specified - blocks AC-5 implementation | Added ParameterSchema interface specification and resolution notes |
| critical | TYPE_SLUGS mapping incomplete - "Add more as needed" is vague | Added canonical source reference and fallback rules |
| critical | "{Type} — {Category}" pattern detection underspecified | Added exact regex pattern and matching rules |
| critical | Template.type values not documented | Added template type specification section |
| critical | Policy type fallback conditions undefined | Added explicit fallback rules with examples |
| high | AC-4 says "first policy's category" but algorithm uses `getDominantCategory()` | Clarified algorithm uses dominant category for consistency |
| high | Task 3.4 contradicts Dev Notes on AC-6 | Removed Task 3.4, added note that AC-6 already satisfied |
| high | Category state handling (null vs []) not fully specified | Added explicit null/empty handling in algorithm |
| high | generateScenarioSuggestion not addressed post-signature change | Added note about intentional behavior preservation |
| medium | Truncation strategy for 48-char limit unclear | Added explicit truncation strategy (skip enrichment if exceeds) |
| medium | Percentage decimal convention not explicit | Added explicit note about decimal storage (0.2 = 20%) |
| medium | naming.test.ts file creation instruction misleading | Changed to "Add to existing file" not "NEW FILE" |
| low | Category label vs ID terminology inconsistency | Clarified usage (slugify label, use ID for lookups) |
| low | Validation test examples missing | Added concrete validation test examples |

## Story 27-10 (2026-05-13)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | statusVariant "Current State" contains factual errors**: Story claimed ResultDetailView returns "default" for failed and comparison-helpers returns "warning", but actual code returns "destructive" in both files. This would cause developer confusion and wrong reconciliation. | Corrected "Current State" section to show actual return values |
| critical | AC-8 proposes wrong reconciliation direction**: Story says "reconcile to 'warning' (the most common variant)" but all three files return "destructive" for failed. The only divergence is in the default case (warning vs default). This conflicts with AC-11 (no visual regressions). | Changed AC-8 and Implementation Specification to preserve `failed → "destructive"` and reconcile default case to `"warning"` |
| critical | 4th statusVariant in ExecutionMatrix.tsx undocumented**: Uses uppercase ExecutionStatus enum values, incompatible with proposed lowercase-string helper. Silently breaking this would cause wrong badge colors. | Added ExecutionMatrix to "Status Badge Mappings" with note about type incompatibility and special handling |
| critical | Tasks 4 and 5 orphaned (no AC coverage)**: Loading-state component references "AC: #4" but AC-4 is formatDate; Canonical icons references "AC: #5" but AC-5 is formatTimestamp. These are truly orphaned. | Removed Tasks 4 and 5 entirely along with related new files from Project Structure Notes |
| high | policyLabel interface type mismatch**: Story specifies `scenarioName`/`portfolioName` (camelCase) but API types use `portfolio_name`/`template_name` (snake_case) and `run_kind`. Also loses "Scenario" vs "Scenario run" distinction. | Updated policyLabel interface and implementation to use snake_case matching API types |
| high | 11 files missing from migration target list**: Grep finds 26 files with toLocaleString(), story only lists 15. AC-9 would fail if not addressed. | Added comprehensive list by using grep output pattern |
| high | Two wrong file paths**: RunSummaryPanel is in `engine/` not `screens/`, ExecutionMatrix is in `comparison/` not `simulation/`. | Corrected paths throughout story |
| high | Task AC reference numbers wrong**: Tasks reference AC: #2, #3, #7 but should reference AC: #9, #8, #12 respectively. | Corrected AC reference numbers in task labels |
| high | comparison/index.ts barrel export missing from file list**: Re-exports statusVariant, needs update when moving to status-variants.ts. | Added comparison/index.ts to modified files list |
| medium | formatTimestamp interface not clear in AC-5**: Shows single-param usage but spec has two params. | Updated AC-5 to clarify optional style parameter |
| medium | Locale preservation guidance missing**: AC-9 has exception clause but no guidance on identifying intentional locale differences. | Added Dev Notes section on locale exception identification |
| medium | ResultDetailView formatTs includes seconds**: Current behavior includes seconds, default formatTimestamp is "short" (no seconds). Migration risk. | Added note in migration targets to use "full" style for ResultDetailView |
| medium | statusVariant placement ambiguous**: AC-8 says formatters.ts, Tasks say status-variants.ts, Notes say "or include in formatters.ts". | Chose status-variants.ts as canonical location per Tasks section |
| medium | Task AC cross-references misnumbered**: "Sweep .toLocaleString() (AC: #2)" should be AC-9, etc. | Already addressed above |
| low | Story size concern**: Touching 25-30 files is large but work is mechanical. Not splitting as the work is straightforward. | None - keeping as-is, work is parallelizable |
| low | Performance considerations missing**: No requirements for Intl formatter memoization. | None - defer to implementation; formatters are simple utilities |
| dismissed | "can land in parallel with most P0/P1 stories" contradicts touching 25-30 files | FALSE POSITIVE: While merge conflicts are possible, the changes are mechanical and isolated to formatting. Component-level commits make conflict resolution straightforward. This is not a blocker. |
| dismissed | Verbose Dev Notes repeat implementation specifications | FALSE POSITIVE: The duplication provides context for developers without scrolling. Token optimization is not critical here since story file is not heavily token-constrained for this workflow. |
| dismissed | Test migration strategy missing | FALSE POSITIVE: AC-10 requires unit tests for new utilities; snapshot test updates are implied by AC-11 (no visual regressions). Additional guidance not required. |

## Story 27-14 (2026-05-13)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | AC-3 decision point unresolved — story left choice between `variant="secondary"` vs adding new `active` variant | Made explicit decision to use `variant="secondary"` with documented rationale. Removed ambiguous Task 2.2 subtask that left decision to implementation time. |
| high | Task 5.2 uses incorrect console API name "console.warning" (should be "console.warn") | Changed Task 5.2 title from "Add console.warning when fallback is triggered:" to "Add console.warn when fallback is triggered:" and updated AC-6 to specify `console.warn()`. |
| high | Task 6.2 references "Auto-name effect dep array" item that does not exist in deferred-work.md | Completely rewrote Task 6.2 to accurately reference deferred-work.md contents. Added [EXISTS]/[NEW] markers to distinguish tracked items from newly-discovered cleanup. Removed the non-existent item entirely. |
| high | Task 6.2 missing newly-fixed badge items from Completed section | Added two new items to Completed list: "[NEW] Editing badge styling bypass (PolicyCard.tsx:278)" and "[NEW] Active badge styling bypass (PoliciesStageScreen.tsx:1086)". |
| medium | Background section misleadingly implies all 5 items come from deferred-work.md (items 2 & 3 were discovered during story authoring) | Reorganized Background section with explicit "**From deferred-work.md:**" and "**Additional cleanup discovered during story authoring:**" headings. |
| medium | Task 3.1 grep pattern `variant="default"` returns ~20 false positives from legitimate default badge usages | Changed to targeted pattern `variant="default".*bg-` and added explanatory note about avoiding false positives. |
| medium | No note about deferred-work.md location drift for error badge (references old PortfolioCompositionPanel.tsx:786 location) | Added note in Background item #1 and in Dev Notes explaining the code moved to PolicyCard.tsx:271 during Story 27.4. |
| low | AC-5 comment format ambiguous (single-line vs multi-line) | Changed "documented with a code comment" to "documented with a multi-line code comment (4+ lines) immediately before the warning div". |
| low | Verbose appearance change notes repeated across AC-1, AC-2, AC-3 | Consolidated to single note: "All badge changes use lighter backgrounds (`bg-*-50`) instead of dark (`bg-*-500`) to align with the Badge design system." |
| low | Dev Notes migration path duplicates AC content | Changed "**Migration path:**" to "**Migration path:** See AC-1, AC-2, AC-3 for specific mappings per badge type." |
| dismissed | Badge appearance changes not validated for user acceptability | FALSE POSITIVE: The story correctly documents these as intentional design system alignment changes. The Dev Notes section explains that all Badge semantic variants use light backgrounds (`bg-*-50`) — this is the canonical design system. If darker badges were semantically required, that would be a design system change proposal, not a cleanup task. The appearance changes are feature, not bug. |
| dismissed | Missing AC for visual verification of badge appearances | FALSE POSITIVE: Task 7.4 covers manual verification in browser. For a cleanup story with behavior-preserving changes, manual browser verification is appropriate. Adding a separate AC for "designer approval" would introduce subjective criteria that can't be objectively measured. The story's approach (document the change, verify visually in browser) is correct for this scope. --- |
