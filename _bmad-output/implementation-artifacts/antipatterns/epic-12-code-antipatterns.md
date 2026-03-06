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

## Story 12-3 (2026-03-06)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | `_merge_policy_results()` uses `inner` join, silently dropping households not present in all policy outputs — violates "Data contracts fail loudly" rule | Added household_id set consistency validation before merge; changed join to `left outer`; raise `PortfolioComputationStepError` on mismatch |
| critical | No uniqueness check on `household_id` before join — duplicate keys cause cartesian row explosion | Added duplicate household_id detection per policy result; raise `PortfolioComputationStepError` with count details |
| high | Mutable `list` stored in `YearState.data[PORTFOLIO_RESULTS_KEY]` undermines immutability semantics | Changed to `tuple(policy_results)` |
| medium | Repeated `append_column` calls create unnecessary intermediate PyArrow tables | Build columns/names arrays then construct table via `pa.table(dict(...))` in single operation; simplified first-policy path to use `renamed_table` directly |
| medium | Type hint `"PolicyConfig"` with `# noqa: F821` for undefined name in conftest | Imported `ComputationPolicyConfig` from `reformlab.computation.types` and used it directly |
