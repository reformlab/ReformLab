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

## Story 29-2 (2026-05-18)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | `test_normalization_regression.py` tests expect `taxe_carbone` → `carbon_tax` normalization but mapping was REMOVED | Replaced `taxe_carbone` with `irpp_economique` in test data and updated assertions to expect `income_tax` instead of `carbon_tax` |
| critical | Quality gate ran only modified files' tests — breaking regression undetected | Ran full test suite during code review synthesis; 73 tests pass |
| high | Comment `# Removed: irpp -> income_tax` is factually wrong — irpp was REPLACED, not removed | Changed comment to `# Replaced: irpp -> irpp_economique (still maps to income_tax output)` with accurate explanation |
| high | `_MINIMUM_REQUIRED_COLUMNS` still contains `carbon_tax` with no updated semantics comment | Added note explaining `carbon_tax` is no longer produced by default mapping but can appear via template pack output |
| medium | `test_normalization_regression.py` missing from Story 29.4 migration plan entirely | Added test file to migration plan with "Tests Already Updated in Story 29.2" section |
| low | `_KNOWN_POLICY_TYPES` defined inside function body; reconstructed on every portfolio call | DISMISSED — Pre-existing code pattern, not introduced by Story 29.2 |
| low | `test_mapping.py` fixture uses removed `taxe_carbone` placeholder in YAML test data | DISMISSED — Intentional test of custom YAML mapping functionality, not default mapping |
| dismissed | `test_translation_integration.py:560` has failing `carbon_tax` assertion | FALSE POSITIVE: File is only 341 lines; line 560 doesn't exist. No failing `carbon_tax` assertions in this file. |
| dismissed | `test_panel.py:176` has failing `carbon_tax` assertion | FALSE POSITIVE: Line 176 is a docstring; grep shows only comments and function names, no failing test code related to `taxe_carbone` normalization. |
| dismissed | AC #3 acceptance criteria contradiction with task completion | FALSE POSITIVE: AC #3 clearly states "Given a placeholder is removed from the mapping, when tests are updated in Story 29.4" — this refers to test cleanup, not critical test fixes. The migration plan clarifies this distinction. |
| dismissed | No test verifies `irpp_economique` is the actual OpenFisca-France variable | FALSE POSITIVE: Dev Notes #9 explicitly verified this by inspecting `CountryTaxBenefitSystem().variables.keys()` and finding `irpp_economique` at foyer_fiscal entity level. |
| dismissed | SOLID violation in normalization module | FALSE POSITIVE: The module's design is appropriate for its purpose; extracting portfolio normalization would add complexity without benefit. Pre-existing pattern, not introduced by Story 29.2. |
