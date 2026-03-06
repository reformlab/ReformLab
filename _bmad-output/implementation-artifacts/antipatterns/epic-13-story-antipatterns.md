# Epic 13 - Story Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during validation of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent story-writing mistakes (unclear AC, missing Notes, unrealistic scope).

## Story 13-1 (2026-03-06)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | JSON Schema `policy_type` enum is hardcoded and story left resolution as "consider whether" | Added explicit decision to Project Structure Notes: JSON Schema stays as-is for built-in types; custom types are validated at runtime only. This is appropriate because JSON Schema is used for IDE-level validation, not runtime enforcement. |
| high | AC4/AC5 use non-measurable language ("like built-in template", "work correctly") | AC4 now specifies exact return type, instance check, and round-trip invariant. AC5 now lists 4 explicit verifiable behaviors (a-d). |
| high | AC1 references wrong API function (`register_policy_type()` instead of `register_custom_template()`) | AC1 now references both functions that are part of the registration flow. |
| high | AC3 uses confusing `rate_schedule` example — `rate_schedule` is always present on any `PolicyParameters` subclass since it's a base field with no default | AC3 rewritten to specify actual validation cases: not a frozen dataclass, not a `PolicyParameters` subclass, duplicate registration. |
| high | Design Decision 1 presents 3 options with "Recommended" instead of a binding decision, risking divergent implementations | Collapsed to single mandatory decision (Option A). Options B/C removed. |
| high | Tasks 5.1/5.2 say "Verify" which is passive and non-actionable | 5.1 converted to "Update" with specific acceptance/rejection behavior. 5.2 converted to "Confirm" with explicit test requirement. |
| medium | Task 2.3 redundantly validates `rate_schedule` presence when Task 2.2 already validates `PolicyParameters` subclassing | Task 2.3 reworded to clarify it's about proper subclass validation, not redundant field checking. |
| medium | Global registration lifecycle not explicitly stated | Not applied as a story change — registration-before-use is implicit in Python's execution model, and the existing error paths (`TemplateError` on unknown types) already handle the failure case. The story's `_reset_custom_registrations()` test helper adequately covers test isolation. |
| low | Dev Notes repeat project-context patterns verbosely | Not applied — the focused reminder in Architecture Patterns section provides valuable quick-reference for the dev agent without requiring context switches to project-context.md. |

## Story 13-2 (2026-03-06)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | AC3 contradicts Task 2.3 on year-schedule error semantics. AC3 says "raises a clear error" for missing years, but Task 2.3 says fall back to default field values, and Key Design Decision #2 confirms override-with-fallback intent. | Rewrote AC3 to specify `.get(t, default_field)` fallback behavior, aligning AC with Task 2.3 and Design Decision #2. Updated Task 2.3 description to remove the stale "raise error" clause. |
| medium | AC2 lists `VehicleMalusResult` fields without `vehicle_emissions`, but Task 2.2 includes it. The feebate pattern (`FeebateResult.metric_value`) also includes the underlying metric in results. | Added `vehicle_emissions` to AC2's field list. |
| medium | `malus_amount` unit (EUR) not explicitly stated in result dataclass. | Added `(EUR)` annotation to Task 2.2's `malus_amount` field description. |
