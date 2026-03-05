# Epic 12 - Code Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during code review of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent implementation mistakes (race conditions, missing tests, weak assertions, etc.)

## Story 12-1 (2026-03-05)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Immutability breach - `list_policies()` returns direct reference to mutable `rate_schedule` dict, allowing external mutation of internal state. | Changed line 116 to return `dict(config.policy.rate_schedule)` instead of direct reference |
| high | Package integration gap - Portfolio types not exported from `reformlab.templates` | Added PolicyConfig, PolicyPortfolio, and portfolio exceptions to imports and __all__ list |
| high | Schema too permissive - No `additionalProperties: false` at root/policy levels, typos silently accepted | Added `additionalProperties: false` to root, policy item, and policy.parameters objects |
| high | Test data format mismatch - Test uses `redistribution_type` but loader expects `redistribution: {type: ...}` | Updated test to use canonical nested format |
| high | Unused imports - `yaml` imported but not used in test file, **Source**: Reviewer A | Removed unused `yaml` import |
| medium | Lint violations - Unused `PolicyType` import and unused `lines` variable | Removed unused imports |
| medium | Story traceability incomplete - Tasks marked incomplete despite implementation | Deferred (not applying - outside scope of code fixes) |
