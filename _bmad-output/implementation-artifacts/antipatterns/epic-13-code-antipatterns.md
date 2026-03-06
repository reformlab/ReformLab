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

## Story 13-2 (2026-03-06)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | Python row loops in compute path instead of vectorized PyArrow operations | Replaced Python loops with `pc.cast`, `pc.fill_null`, `pc.subtract`, `pc.max_element_wise`, `pc.multiply` vectorized operations. Also handles non-numeric emissions gracefully via try/except on `pc.cast`. |
| medium | Non-idempotent import-time registration — `importlib.reload()` crashes | Added guard checking `_CUSTOM_POLICY_TYPES` and `_CUSTOM_PARAMETERS_TO_POLICY_TYPE` before registration. |
| medium | Batch silently overwrites duplicate scenario names | Added duplicate name detection with `ValueError` before batch execution. |
| medium | Weak test assertion for AC7 portfolio integration | Changed from `isinstance(conflicts, tuple)` to asserting `len(conflicts) >= 1` and checking `"overlapping_years"` in conflict types. |
| medium | `__import__("dataclasses").field(...)` is opaque | Changed to proper `from dataclasses import dataclass, field` import. |
| low | Missing `from __future__ import annotations` in `vehicle_malus/__init__.py` | Added the import. |
| low | Story "Source File Touchpoints" incomplete | Deferred as follow-up task (documentation-only). |
| low | `aggregate_vehicle_malus_by_decile` uses Python loops | Deferred — matches feebate pattern exactly, and the aggregation path processes only 10 decile buckets (not per-row). |

## Story 13-3 (2026-03-06)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | Silent fallback to zeros on invalid `energy_expenditure` column type | Changed `except` block to raise `TemplateError` with column/type context instead of silently falling back to zeros. |
| high | Schedule overrides not validated — `income_ceiling_schedule` or `energy_share_schedule` value of 0 causes divide-by-zero | Added runtime validation of `effective_ceiling` and `effective_threshold` after schedule lookup, raising `TemplateError` if <= 0. |
| high | Bare `ValueError` for duplicate scenario names — project rules require `TemplateError` | Changed to `TemplateError`. Updated matching test to expect `TemplateError`. |
| high | Python row loops in compute path instead of vectorized PyArrow operations | Replaced all `to_pylist()` + Python loops with vectorized `pc.if_else`, `pc.divide`, `pc.subtract`, `pc.multiply`, `pc.min_element_wise`, `pc.max_element_wise` operations. |
| medium | Weak AC7(b) portfolio test assertion — only checks `"overlapping_years"`, not `"same_policy_type"` | Changed `len(conflicts) >= 1` to `>= 2` and added assertion for both `"same_policy_type"` and `"overlapping_years"` conflict types. |
| medium | AC7(c) evidence gap — no execution-path test proving adapter receives `asdict()` payload | Deferred as review follow-up task — requires orchestrator-level integration test setup beyond story scope. |
| medium | Comparison table column slug collisions possible | Deferred — matches vehicle_malus pattern exactly, low practical risk. Noted as follow-up. |
