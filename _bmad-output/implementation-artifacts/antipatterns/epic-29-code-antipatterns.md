# Epic 29 - Code Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during code review of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent implementation mistakes (race conditions, missing tests, weak assertions, etc.)

## Story 29-1 (2026-05-18)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | `menage.household_index` AttributeError | Changed all 4 occurrences from `len(menage.household_index)` to `menage.count` — OpenFisca's `GroupEntity` exposes `.count` not `.household_index`, so the exception handlers themselves would raise `AttributeError`. |
| high | Tautological test assertion | Replaced `assert adapter.version() != "unknown" or adapter.version() == "unknown"` (always true) with actual variable registration verification. |
| medium | Duplicate version constant | Removed duplicate `_EXTENSION_VERSION` from adapter, now imports authoritative `EXTENSION_VERSION` from extension module (eliminates sync risk). |
