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
