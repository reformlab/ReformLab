# Epic 13 - Code Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during code review of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent implementation mistakes (race conditions, missing tests, weak assertions, etc.)

## Story 13-1 (2026-03-06)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | Silent fallback in `_parse_generic_custom_policy()` — when custom type is registered via `register_policy_type()` but no class is registered via `register_custom_template()`, the function silently returns base `PolicyParameters`, dropping all custom fields. Violates "fail loudly" data contract principle. | Changed fallback to raise `ScenarioError` with clear message directing user to call `register_custom_template()`. |
| medium | Missing `PortfolioComputationStep.execute()` integration test — Task 5.3 requires end-to-end test through orchestrator yearly loop, but existing tests only covered construction and the bridge function. | Added `test_execute_with_custom_template()` that creates a portfolio with custom + built-in types, calls `.execute()` with MockAdapter, and asserts adapter was called twice and merged result is stored in YearState. |
| medium | Task 3.2/3.3 `register_policy_parser()` API not implemented — Tasks marked done but no custom parser registry exists. Only the generic dataclass-introspection parser was implemented. | Deferred as follow-up task. The generic parser covers the common case well. The custom parser API will be needed when Stories 13.2/13.3 encounter types with nested structures. |
| low | Weak test assertion `len(conflicts) > 0` in `test_validate_compatibility_custom_types` | Changed to `assert len(conflicts) >= 2` with specific conflict type checks for `overlapping_years` and `overlapping_categories`. |
| low | `Any` type hints where `PolicyType | Changed to concrete `PolicyType \| CustomPolicyType` union type, added `CustomPolicyType` to module-level imports. |
| low | Cross-module import of private `_CUSTOM_*` registries | Not addressed — internal coupling within same subsystem (templates). Noted for future improvement if registries grow. |
| low | Hardcoded `_BUILTIN_TYPES` tuple in `composition.py` | Not addressed — low risk, new built-in types are rare. Added reverse lookup concern as follow-up task. |
