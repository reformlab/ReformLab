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

## Story 28-5 (2026-05-17)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | `PopulationSchemaError` does not exist | Changed all references to `DiscreteChoiceError` in AC #7 and Task 8 |
| critical | `RunManifest.from_dict()` does not exist | Changed AC #8 and Task 9.3 to use `RunManifest.from_json()` |
| critical | `EngineConfigCompiler` class does not exist | Changed Task 2.3 to use `from_workflow_config()` and updated Dev Notes with correct setup pattern |
| critical | Wrong panel column names in AC #1 | Changed AC #1 from `incumbent_heating_t == heating_chosen_{t-1}` to `heating_from[year N] == heating_to[year N-1]` and updated Task 2.6 assertion |
| critical | `OrchestratorConfig` with wrong fields | Updated Dev Notes test pattern to use correct `WorkflowConfig` → `from_workflow_config()` → `OrchestratorConfig` chain |
| high | Step pipeline construction guidance missing | Added Dev Note "Step Pipeline Construction for Multi-Period Tests" with concrete example |
| high | Alternative ID reconciliation conflict | Added Dev Note clarifying to use legacy IDs throughout (not DEFAULT_TECHNOLOGY_SET IDs) for heating tests |
| high | `@pytest.mark.nightly` conflicts with existing `scale` marker | Changed Task 10 to use `@pytest.mark.scale` instead and removed pytest configuration subtask |
| high | Manifest reproducibility misses non-deterministic fields | Updated `_canonical_json` example to strip `manifest_id`, `created_at`, `integrity_hash` in addition to `timestamp`/`run_id` |
| high | Frontend test missing full API mock specification | Updated Task 11.2 to specify mocking all API modules following existing pattern |
| high | Manifest warning structure not specified | Clarified that warnings go in `manifest.assumptions` dict per Story 28.2 pattern |
| medium | AC #5 legacy fallback warning - no code path exists | Added Task 6.6 note to implement warning detection or simplify AC to just verify completion |
| medium | AC #6 missing-column warning - deferred from Story 28.2 | Added note that this requires production code implementation (was deferred) |
| medium | Baseline snapshot bootstrapping unclear | Added Task 5.2 clarification on generating baseline if doesn't exist |
| medium | Transition counts fixture bootstrapping | Added Task 4.5 bootstrap subtask |
| low | Fixture incumbents mismatch in AC #1 description | Changed AC #1 from legacy IDs to match DEFAULT_TECHNOLOGY_SET IDs (condensing_boiler, heat_pump_air, etc.) |
| low | Frontend UI assumes unimplemented features | Scoped AC #10 to wizard flow only (results UI deferred per Story 28.4) |
| low | Redundant "Project Structure Notes" section | Removed duplicate second occurrence |
| low | Verbose test patterns increase token count | Condensed code examples where possible while preserving essential references |
