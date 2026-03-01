# Epic 9 - Story Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during validation of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent story-writing mistakes (unclear AC, missing Notes, unrealistic scope).

## Story 9-3 (2026-03-01)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Metadata field name contradiction in AC-5 vs Task 4.3 | Rewrote AC-5 to explicitly name two separate `dict[str, str]` keys with concrete examples; updated Task 4.3 to match with inline examples. *Consensus — both validators independently flagged this.* |
| critical | `_make_mock_tbs()` lacks `definition_period` — silent test regression | Added explicit Task 1.5 requiring `var_mock.definition_period = "year"` in `_make_mock_tbs()` variable loop, with full explanation of the MagicMock failure mode and which specific test breaks (`TestPeriodFormatting.test_period_passed_as_string`). Without this task, the failure is a confusing `AssertionError` ("Expected call: calculate(...) not found") with no obvious cause. |
| critical | `_extract_results_by_entity()` signature change silently breaks 3 existing test callers | Rewrote Task 3.1 to call out the breaking change explicitly, name all 3 affected test methods (`test_single_entity_extraction`, `test_multi_entity_extraction`, `test_multiple_variables_per_entity`), and show the required fix (`variable_periodicities={"var_name": "year"}`). Without this, a dev agent adds a new required parameter and watches 3 previously-passing tests fail with `TypeError`. |
| high | Period validation placement ambiguous in AC-3 and Task 5.1 | Updated AC-3 to specify "very first check before any TBS operations"; updated Task 5.1 to say "FIRST operation in `compute()`, before `_get_tax_benefit_system()`" with rationale for the [1000, 9999] range. |
| high | Explicit `compute()` call order not shown in Task 4.1 | Replaced the vague "fail-fast pattern" note with a numbered 5-step pseudocode sequence showing exactly where `_resolve_variable_periodicities()` fits relative to `_validate_output_variables()`, `_resolve_variable_entities()`, `_build_simulation()`, and `_extract_results_by_entity()`. |
| high | Pre-existing Story 9.2 integration test failure not acknowledged | Updated Task 6.2 to warn that any Story 9.2 integration test using `salaire_net` may already be red (pre-existing `ValueError: Period mismatch`), and that Story 9.3 is expected to turn it green as a side-effect. |
| high | Integration test dispatch verification strategy missing | Expanded Task 7.1 to explain that real `Simulation` objects cannot be mock-asserted, and provided the correct two-pronged verification approach (metadata `calculation_methods` key + value range assertion). |
| medium | AC-6 eternity handling lacks WHY and test verification hint | Expanded AC-6 to add concrete example variables (`date_naissance`, `sexe`), the exact error message `calculate_add()` raises, and a test verification hint (assert `calculate` called, assert `calculate_add` NOT called for `periodicity == "eternity"`). |
| medium | Files to Modify table understates test file changes | Replaced the single-line description with an enumerated 3-change list: (1) `_make_mock_tbs()` update, (2) existing `TestExtractResultsByEntity` caller updates, (3) new test classes. |
