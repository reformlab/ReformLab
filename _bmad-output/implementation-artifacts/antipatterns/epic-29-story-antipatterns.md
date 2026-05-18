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
