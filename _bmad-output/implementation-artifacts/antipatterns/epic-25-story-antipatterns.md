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
