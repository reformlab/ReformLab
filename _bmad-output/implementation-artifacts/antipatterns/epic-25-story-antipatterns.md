# Epic 25 - Story Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during validation of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent story-writing mistakes (unclear AC, missing Notes, unrealistic scope).

## Story 25-1 (2026-04-19)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | `mock-data.ts` and `useApi.ts` missing from file list | Added both files to file list and corresponding tasks: |
| critical | Contradictory category mapping strategy | Clarified that Story 25.1 uses ONLY hardcoded mapping: |
| critical | Missing `category_id` in frontend data mapping chain | Added explicit tasks for the complete chain: |
| critical | "or" component ownership ambiguity | Specified single owner: |
| high | Popover stub not clearly flagged | Updated warning to include Popover with Dialog/Sheet: |
| high | Wrong grouping description (`parameter_groups` vs `type`) | Corrected description: |
| high | TemplateCard.tsx "may exist" is incorrect | Updated to clarify cards are inline: |
| high | Incomplete template-type mapping table | Added explicit mapping: |
| medium | Missing non-happy-path ACs | Added 3 new acceptance criteria: |
| medium | Popover edge cases incomplete | Updated AC4 to specify: |
| low | Regression tests too vague | Expanded to: "select/unselect, composition persistence, type badge display continuity, no-category fallback visibility" |
| low | Auth behavior unspecified | Added to Backend patterns: "Auth: `GET /api/categories` requires authentication (use same auth pattern as `/api/templates`)" |
| low | "Other" group ordering unspecified | Updated AC5: "positioned last (after all named categories)" |
| low | UX spec line references | Changed to section headers: "(Stage 1 — Policies section, API-Driven Categories)" |
| low | Out-of-scope not stated | Added new "Out of Scope" section listing: Template YAML metadata, admin interfaces, dynamic category assignment |

## Story 25-2 (2026-04-19)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | AC-8 self-contradiction | Rewrote AC-8 to state single behavior only: "it adds as a single policy entry per existing behavior (composite template decomposition... is deferred to Story 25.3)". Removed contradictory "creates separate Tax and Subsidy policies" language. |
| critical | instanceId collision risk with Date.now() | Replaced all `Date.now()` references with monotonic counter pattern. Updated code examples, design decisions, and known issues to use `${templateId}-ins${counter}` with counter incrementing on each add. Added note about avoiding Date.now() due to rapid-click collision risk. |
| critical | Missing categories prop interface specification | Updated "Category Badges in Composition Panel" section to explicitly state: "Add `categories?: Category[]` prop to `PortfolioCompositionPanel` interface" and "Add `instanceId?: string` field to `CompositionEntry` interface". Added task subitems for interface updates and graceful fallback handling. |
| critical | Incomplete file impact list missing hooks | Expanded "Frontend files to modify" from 5 to 7 files, adding `usePortfolioLoadDialog.ts` and its test file. Also updated both the "Source Tree Components to Touch" section and the "File List" section in Dev Agent Record. |
| critical | State sync mechanism not specified after removing selectedTemplateIds | Added new "Browser-Composition Synchronization" subsection in Key Design Decisions explaining how to derive browser highlighting from composition state using `useMemo(() => composition.map(c => c.templateId), [composition])`. Added note about count badges in browser cards. |
| high | Type badge terminology doesn't match existing technical types | Updated AC-3 from "Tax/Subsidy/Transfer" to "Carbon Tax/Subsidy/Rebate/Feebate/Vehicle Malus/Energy Poverty Aid with correct per-type color" to accurately reflect the existing TYPE_COLORS mapping in the codebase. |
| high | Missing edge case test specifications | Enhanced Testing task to include "Duplicate instance uniqueness" and "Browser-composition sync tests". Updated Testing Standards Summary to mention "Test instanceId uniqueness with rapid-fire operations". |
| medium | Category badge fallback behavior not specified | Updated Known Issues item #4 to add: "Handle missing categories gracefully: if `categories` prop is null/undefined or template.category_id not found, hide the badge without error." Also added graceful fallback to task subitems. |
| medium | Ambiguous task about adding category_id to CompositionEntry | Clarified task to specify interface prop changes rather than adding category_id to CompositionEntry (which should stay lean since category is looked up from template). |
| medium | Count badge for duplicate instances not mentioned | Added count badge requirement to task: "Add count badge to browser cards showing 'Added N×' when template appears multiple times in composition" and to Key Design Decisions synchronization section. |
