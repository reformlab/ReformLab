# Epic 29 - Story Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during validation of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent story-writing mistakes (unclear AC, missing Notes, unrealistic scope).

## Story 29-1 (2026-05-18)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Hotfix context is factually incorrect | Rewrote "The Problem" section to remove false hotfix narrative. Updated references in three locations (lines 56-57, 200, 220). Corrected statement: `_DEFAULT_LIVE_OUTPUT_VARIABLES` includes all 12 variables, no narrowing was applied. |
| critical | PM decision blocks story start | Added explicit `Prerequisite` section below Status line. Rewrote AC-#3 to be a verifiable behavior rather than a process requirement. Updated task 1 with verification command for `cheque_energie`. |
| critical | OpenFisca formula input variables unspecified | Added comprehensive "Formula Input Variables" section specifying income data access (`menage('revenu_disponible', period)`), population-injected data handling, and policy parameter access patterns. |
| high | Wrong dependency chain | Rewrote Dependencies section to clarify that Story 29.2 is independent and can proceed in parallel. Updated sequence: 29.1 AND 29.2 → 29.3. |
| high | Test population undefined | Added "Test Population Requirements" to Testing Strategy section specifying required columns (household_id, income, vehicle_emissions_gkm, energy_expenditure) and instruction to create inline population if Quick Test Population lacks coverage. |
| high | Extension loading mechanism unspecified | Added "Extension Loading Pattern" section specifying call location (`_get_tax_benefit_system()` after `tbs_class()`), idempotency guard pattern, and instance-only (not class) mutation requirement. |
| high | Manifest extension strategy incomplete | Updated Manifest task to specify exact field structure: `{"name": "reformlab-openfisca-extend-fr", "version": "1.0.0", "variables": [...]}`. Added `EXTENSION_VERSION` constant definition requirement. |
| high | No error handling for extension failures | Added "Error Handling Strategy" section covering four failure modes: import failures, definition errors, TBS extension failures, and version detection failures. |
| high | `_MINIMUM_REQUIRED_COLUMNS` affects integration test | Added "Integration Test Output Variables" note specifying inclusion of `salaire_net` to pass normalizer validation. |
| high | Missing boundary case tests | Updated AC-#5 to explicitly require boundary condition tests (household exactly at eligibility threshold). |
| medium | Test strategy for optional OpenFisca dependency | Added "Test Gating" paragraph after Test Files specifying `pytest.importorskip` pattern and guidance on mocking vs. real TBS usage. |
| medium | Quality gates inconsistent with project standards | Simplified Quality Gates to use standard project-wide commands (`uv run ruff check src/ tests/` etc.) instead of module-specific paths. |
| medium | PM decision verification method missing | Added verification command to task 1 and Variable Specifications section for checking `cheque_energie` existence in OpenFisca-France. |
| low | Performance considerations unspecified | Added "Performance Considerations" section with specific targets: <100ms initialization overhead, <5% computation overhead, <10% memory overhead. |

## Story 29-3 (2026-05-18)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | `malus_ecologique` Always Returns 0 — AC #5 Impossible | Added explicit blocker acknowledgment in Dependency Chain section, added pre-check task to verify Story 29.1 deferred item, updated AC #5 to specify expected behavior when input unavailable ("returns 0.0 if input unavailable — tracked as Story 29.1 deferred item") |
| critical | Integration Test Undefined — Pseudo-code Template | Expanded test template with concrete population structure, explicit eligibility criteria (income < 20000 EUR, emissions > 118 g/km), multi-entity `foyer_fiscal` coverage note, reference to existing test pattern (`test_openfisca_extension.py:162-218`) |
| critical | `foyer_fiscal` Entity Coverage Missing | Added requirement for multi-entity test population with `foyer_fiscal` structure for `irpp_economique` computation, reference to Story 9.4 dev notes and existing adapter test patterns |
| critical | Story Misrepresents Prerequisite Completeness | Updated Dependency Chain section to accurately reflect "Story 29.1 — Complete with deferred items", added Known Blocker subsection documenting `reformlab_malus_emissions` issue |
| high | Missing Verification Task for Prerequisites | Added Task #0 "Pre-check: Verify prerequisite stories are actually complete" with 5 concrete verification commands (extension tests, grep checks, tuple length verification) |
| high | AC #5 "Eligible Households" Not Testable | Rewrote AC #5 with explicit eligibility criteria and expected values for each custom variable (150.0 EUR for subsidy, max(0, (emissions-118)*50) for malus, etc.) |
| high | No Regression Protection | Added regression test subtask under Task #4: "Verify no regressions in existing consumers" with full test suite run, frontend grep for hardcoded variable names, API documentation verification |
| high | Existing `test_dependencies.py` Incomplete | Added subtask to update existing test to assert all 4 custom variables are present in live output tuple |
| high | Exact Count Assertion Missing | Added `assert len(_DEFAULT_LIVE_OUTPUT_VARIABLES) == 9` with formatted error message listing actual variable names |
| high | Test Gating Inconsistency | Replaced `REFORMLAB_RUN_LIVE_TESTS` env var pattern with `pytest.importorskip("openfisca_france")` pattern (consistent with `test_openfisca_extension.py:15`) |
| medium | Environment Variable Documentation | Removed env var gating entirely, switched to `pytest.importorskip` pattern which is already documented in project context |
| medium | Missing Error Scenario Coverage | Added optional "Error Scenario Coverage" section documenting extension load failure, missing variable, invalid population, and no-silent-failure scenarios |
| medium | Exact Expected Values for Custom Variables | Added explicit expected values in Task #3 (150.0 EUR, True/False, formula results) and AC #5 with precise eligibility criteria |
| medium | `cheque_energie` Input Requirements Undefined | Added "`aide_energie` Test Note" with required population attributes (revenu_fiscal_de_reference, chauffage_combustible) and reference to OpenFisca-France test fixtures |
| medium | Test File Location Inconsistency | Consolidated integration test into existing `TestIntegrationWithAdapter` class in `test_openfisca_extension.py` instead of creating new file |
| medium | Documentation Update Task Vague | Clarified Task #2 to verify `result_normalizer.py` docstring (already updated by Story 29.2) — reduced redundancy |
| medium | Story Purpose Contradiction | Added "This story involves / does NOT involve" subsection clarifying scope (tests vs implementation) |
| low | Dev Notes Current State Redundancy | Replaced full `_DEFAULT_OUTPUT_MAPPING` code block (~800 tokens) with concise reference to `result_normalizer.py:78-96` and instruction to read source file |
| low | Test Population Fixture Reuse Opportunity | Added reference to `test_openfisca_extension.py:162-218` pattern for population construction (enables reuse) |
| low | Assertion Precision for Floating-Point Values | Added `pytest.approx()` usage note in Custom Variable Values Test section and integration test example |
| dismissed | Verbose task descriptions | FALSE POSITIVE: Acknowledged as minor but accepted tradeoff for clarity. Tasks now reference ACs explicitly; verbosity reduced by consolidating subtasks. |
| dismissed | Redundant documentation tasks | FALSE POSITIVE: Partially valid. Consolidated into single verification task with explicit "already done by Story 29.2" note to eliminate redundancy. |
| dismissed | Pytest marker for live tests suggestion | FALSE POSITIVE: Resolved by switching to `pytest.importorskip` pattern instead of adding new marker system — maintains consistency with existing test patterns. |
