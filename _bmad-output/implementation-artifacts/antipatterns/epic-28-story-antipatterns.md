# Epic 28 - Story Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during validation of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent story-writing mistakes (unclear AC, missing Notes, unrealistic scope).

## Story 28-3 (2026-05-17)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | `keep_current` writeback semantics unspecified | Added logic to skip incumbent writeback for rows where `chosen == "keep_current"`. Updated "Incumbent Writeback Logic" code pattern (lines 193-265) to preserve existing technology values instead of overwriting with "keep_current" string. This prevents data corruption in multi-year runs and fixes both AC-2 (multi-year incumbents) and AC-7 (eligibility invariance). |
| critical | Breaking API change not backward compatible | Changed `domain_key: str` to `domain_key: str \| None = None` in Task 1.1 and function signature example. Added logic to return population unchanged when `domain_key is None`, preserving backward compatibility with existing call sites. Updated Task 1.8 to specify explicit `domain_key="vehicle"` and `domain_key="heating"` values at call sites. |
| critical | Type validation missing for corrupted population | Added type validation logic to "Incumbent Writeback Logic" code pattern that checks if incumbent column is `pa.DictionaryType` with `pa.int32()` index type. Raises `DiscreteChoiceError` with descriptive message for wrong type/encoding. Added AC-8 for error handling acceptance criterion. |
| critical | AC-7 eligibility claim factually incorrect | Corrected "Eligibility Invariance Pattern" section (lines 351-377) to describe actual mechanism using `EligibilityMergeStep` instead of non-existent `eligible_indices` mapping. Added pipeline ordering requirement: `StateUpdateStep.depends_on` must include `"eligibility_merge"` when eligibility filtering is active. |
| critical | Alternative ID mismatch (heating domain) | Added "Alternative ID Reconciliation" warning section after Critical Architecture Constraints. Documented that legacy heating IDs (`gas_boiler`, etc.) differ from `DEFAULT_TECHNOLOGY_SET` IDs and that validation must be bypassed when using legacy config. Marked as deferred to future story (not resolved in this story per existing scope). |
| critical | Missing integration test for concurrent StateUpdateSteps | Added `test_concurrent_state_update_steps()` test pseudocode to Testing Standards section (lines 454-480). Verifies that both `VehicleStateUpdateStep` and `HeatingStateUpdateStep` can execute in same year without clobbering each other's incumbent columns. Updated Task 5 to include this test. |
| high | Panel column naming inconsistent with existing convention | Removed year prefix from transition column names. Updated "Panel Output Extension" code pattern to use `{domain}_from` and `{domain}_to` (no `y{year}_` prefix), matching existing `{domain}_chosen` convention. Updated Task 3 to clarify that transitions are read at same level as decision_log (not inside yearly_states loop). |
| high | RunManifest backward compatibility gap | Added tasks 4.5-4.6 for adding `"technology_set"` to `OPTIONAL_JSON_FIELDS` and handling empty dict default in `from_json()`. Updated "Manifest Capture Extension" documentation to include `technology_set: dict[str, Any]` field with default `{}`. |
| high | Missing type consistency test | Added `test_incumbent_column_type_validation()` test pseudocode to Testing Standards section. Verifies that incumbent column with wrong type (plain string instead of dictionary) raises `DiscreteChoiceError` with descriptive error message. |
| high | Missing backward compatibility test | Added `test_apply_choices_backward_compatibility()` test pseudocode to Testing Standards section. Verifies that calling `apply_choices_to_population()` without `domain_key` parameter preserves old behavior (no incumbent column created). |
