# Epic 26 - Story Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during validation of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent story-writing mistakes (unclear AC, missing Notes, unrealistic scope).

## Story 26-1 (2026-04-21)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Missing help content migration | Added task for help-content.ts migration and AC-9 for help panel correctness |
| critical | Investment-decisions placeholder not testable | Changed "placeholder or skip" to explicit placeholder with test-id requirement in App.tsx section and AC-5 clarification |
| critical | Hash subView migration missing | Added AC-2 extension for `#engine/<subview>` → `#scenario/<subview>` and corresponding test |
| high | Docstring updates not explicitly required | Added explicit task to update docstrings in workspace.ts, WorkflowNavRail.tsx, and MobileStageSwitcher.tsx |
| high | Runtime StageKey vs migration layer contradiction | Clarified in Migration Strategy that "engine" is migration-only, never a runtime StageKey; added note about removing any runtime fallback |
| high | Missing migration edge case tests | Added tests for direct `#scenario` navigation and hash+localStorage conflict scenario |
| high | TypeScript compilation verification not specified | Added explicit task with command to verify TS rejects "engine" literal |
| medium | Investment-decisions completion logic edge case | Added null scenario check in isComplete() target implementation with comment |
| dismissed | Hash migration creates infinite loop risk | FALSE POSITIVE: Story already provides alternative approach using `engineMigratedRef` flag (lines 386-413). Developer can choose either approach; both are safe |
| dismissed | "investments-decisions" typo in story | FALSE POSITIVE: After searching the entire story file, all instances consistently use "investment-decisions" (singular). No typo found |
| dismissed | Wrong test file path for useScenarioPersistence | FALSE POSITIVE: Story correctly uses `.test.tsx` extension for React component testing (standard for components using JSX/TSX) |
| dismissed | AC-7 and App notes contradict each other | FALSE POSITIVE: AC-7 specifies StageKey type (compile-time), App notes describe which existing component to render (runtime). No contradiction—migration layer handles the translation |
| dismissed | Unscoped regression surface for engine migration | FALSE POSITIVE: The 9 listed files cover all critical paths. Residual "engine" references in non-critical tests won't cause CI failures since they're isolated from type system |
