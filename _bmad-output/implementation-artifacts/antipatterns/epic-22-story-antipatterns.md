# Epic 22 - Story Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during validation of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent story-writing mistakes (unclear AC, missing Notes, unrealistic scope).

## Story 22-1 (2026-03-30)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | ASCII layout contradiction**: 2-row ASCII diagram conflicts with h-12 height constraint | Replaced ASCII with single-row layout spec and clarified that horizontal separator was visual-only |
| critical | External link destination ambiguity**: "GitHub repo URL" and "or actual repo URL" gave multiple options | Pinned exact URLs in External Links Configuration section |
| critical | Non-deterministic responsive behavior**: AC-4 allowed "overflow menu OR hide" creating untestable options | Specified exact behavior: hide with `hidden md:flex` CSS classes |
| high | Ambiguous wording in AC-1**: "Stronger ReformLab brand block" is subjective and non-testable | Rewrote as "displays the logo icon plus visible 'ReformLab' wordmark text in the left slot" |
| high | Ambiguous wording in AC-3**: "Dedicated controls area separate from brand block" not structurally defined | Specified "center-left flex container" with `gap-x-4` for visual separation |
| high | Wordmark size ambiguity**: "text-base (16px) or text-sm (14px) for wordmark" gave two options | Specified exact: `text-sm font-semibold` (14px, semibold) |
| high | Missing spacing specification**: "Proper spacing between icon and wordmark" not quantified | Specified exact: `gap-2` (8px) |
| medium | Logo verification gap**: No criterion to verify current logo.svg matches bimodal dot histogram spec | Added clarification note in Known Constraints: use existing logo.svg as-is; logo alignment with VIDG is separate task |
| medium | LeftPanel scope ambiguity**: Deduplication marked as "optional for this story" creates uncertainty about whether it's in scope | Added Scope Boundaries section explicitly marking LeftPanel changes as OUT OF SCOPE |
| medium | Settings icon state unclear**: Current Settings icon is non-functional; story didn't clarify if this should change | Added to Scope Boundaries: "Settings icon remains display-only" with note that functionality is future work |

## Story 22-2 (2026-03-30)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Story status "ready-for-dev" but all task checkboxes pre-checked | Reset all 24 task checkboxes from `[x]` to `[ ]` so dev agent can check them as work progresses |
| high | AC-3 uses subjective language ("feeling like a cramped sidebar") not objectively testable | Rewrote AC-3 to use measurable criteria: "3+ policies, no horizontal overflow, all operations complete without layout breakage or clipped controls" |
| high | ParameterRow.tsx is a shared component but story doesn't acknowledge cross-surface impact | Added "Shared Component Scope Note" section explaining ParameterRow is used across multiple surfaces and recommending verification of non-Policies consumers |
| medium | No-op subtasks ("change from text-xs to text-xs") confuse execution intent | Cleaned up Task 2 subtasks to use "Verify [state] remains [value] (no change)" pattern instead of confusing "change X to X" phrasing |
| medium | Test coverage approach unclear for responsive behavior (jsdom limitations) | Added "Test implementation notes" section explaining CSS class assertions for responsive behavior, noting jsdom does not render viewport-dependent styles |
| medium | "Legible" in AC-2 lacks measurable threshold | Added WCAG 2.1 AA reference: "text-xs labels with text-slate-900 on white background meet 4.5:1 contrast minimum" |
| low | Task 1 subtask says "confirm no cramping" - still somewhat subjective | Changed to "Test with 3+ policy cards in composition to confirm usable space" (more specific fixture, less subjective) |
| dismissed | Line-number references are brittle and age poorly | FALSE POSITIVE: Line numbers provide useful implementation precision for a single-story context. The tradeoff (precision vs. maintainability) is acceptable for immediate development work. Removing them would make the story less actionable. |
| dismissed | Cross-browser validation not mentioned for CSS Grid changes | FALSE POSITIVE: CSS Grid has universal modern browser support (Chrome 57+, Firefox 52+, Safari 10.1+, Edge 16+). The project is desktop-first with no IE11 requirement. Explicit cross-browser notes would add noise without value. |
| dismissed | Visual regression guidance needed for "balanced layout" verification | FALSE POSITIVE: AC-1 specifies the measurable outcome (`grid-cols-2` for 50/50 split). Visual regression testing is out of scope for this story; CSS class assertions are sufficient. |
| dismissed | Story requires "major rework" before dev handoff | FALSE POSITIVE: The story is technically well-specified with clear acceptance criteria, file paths, and implementation details. Only process refinements were needed, not a major rewrite. |
