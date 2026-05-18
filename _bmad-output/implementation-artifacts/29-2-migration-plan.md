# Story 29.2 Migration Plan for Story 29.4 (Test Cleanup)

**Date:** 2026-05-18
**Story:** 29.2 - Resolve generic-name placeholders

## Overview

Story 29.2 resolved four generic-name placeholder names in `_DEFAULT_OUTPUT_MAPPING`:
- `irpp` → Replaced with `irpp_economique` (actual OpenFisca-France variable)
- `revenu_net` → Removed (no direct equivalent exists)
- `revenu_brut` → Removed (no household-level equivalent exists)
- `taxe_carbone` → Removed (ReformLab-specific policy output)

This migration plan documents test fixture cleanup needed for Story 29.4.

## Placeholder Resolution Summary

| Placeholder | Action | Replacement/Reason | Affects Tests |
|-------------|--------|-------------------|---------------|
| `irpp` | Replace | `irpp_economique` (actual OpenFisca-France variable) | Yes - see below |
| `revenu_net` | Remove | No direct equivalent; use `revenu_disponible` or `salaire_net` instead | Yes - see below |
| `revenu_brut` | Remove | No household-level equivalent; person-level `salaire_de_base` exists | Yes - see below |
| `taxe_carbone` | Remove | ReformLab-specific policy output, not core OpenFisca-France | Yes - see below |

## Test Files Requiring Updates in Story 29.4

### 1. `tests/computation/test_openfisca_api_adapter.py`

**Status:** Tests updated in Story 29.2 (current story) - NO ACTION NEEDED for 29.4

The adapter tests use placeholder names only in mock scenarios and comments. These don't break functionality but could be updated for consistency:

| Line | Context | Current | Suggested Update for 29.4 |
|------|---------|---------|---------------------------|
| ~789-795 | Mock TBS examples | `irpp` in mock variable names | Update to `irpp_economique` |
| ~889-890 | Mock TBS examples | `irpp` in mock variable names | Update to `irpp_economique` |
| ~904-905 | Mock TBS examples | `irpp` in mock variable names | Update to `irpp_economique` |

**Note:** These are low-priority since they're mock data and don't affect actual functionality.

### 2. `tests/computation/test_openfisca_integration.py`

**Status:** Comments only - NO ACTION NEEDED for 29.4

| Line | Context | Current |
|------|---------|---------|
| ~672-674 | Comments mentioning placeholders | Comments reference `irpp`, `revenu_net`, `revenu_brut`, `taxe_carbone` |

**Note:** These are just comments explaining the placeholder problem. They could be updated or removed in 29.4 for clarity, but don't affect functionality.

### 3. Tests Already Updated in Story 29.2 (NO ACTION NEEDED)

The following tests were already updated in Story 29.2 and should pass as-is:

| Test File | Test Name | Changes Made |
|-----------|-----------|--------------|
| `test_result_normalizer.py` | `test_default_mapping_constants` | Updated to verify `irpp_economique` in mapping, removed placeholders |
| `test_result_normalizer.py` | `test_renames_known_openfisca_variables` | Uses `irpp_economique` instead of `irpp`, removed `taxe_carbone` |
| `test_result_normalizer.py` | `test_without_mapping_uses_defaults` | Uses `irpp_economique` instead of `irpp`, removed `revenu_net` |
| `test_result_normalizer.py` | `test_callable_produces_normalized_table` | Uses `irpp_economique` instead of `taxe_carbone` |
| `test_result_normalizer.py` | `test_both_modes_produce_same_column_names` | Uses `irpp_economique` instead of `taxe_carbone` |
| `test_dependencies.py` | `test_default_live_output_variables_are_french_names` | Updated to verify `irpp_economique` in live output, removed placeholders |
| `test_normalization_regression.py` | `test_french_columns_normalized_through_panel_builder` | Fixed: replaced `taxe_carbone` with `irpp_economique`, asserts `income_tax` instead of `carbon_tax` |
| `test_normalization_regression.py` | `test_live_panel_works_with_indicators` | Fixed: replaced `taxe_carbone` with `irpp_economique` in test data |

## Recommendations for Story 29.4

1. **Update mock variable names in adapter tests** (low priority)
   - Replace `irpp` with `irpp_economique` in mock TBS examples
   - Files: `tests/computation/test_openfisca_api_adapter.py`

2. **Update or remove comments** (low priority)
   - Update comments in `tests/computation/test_openfisca_integration.py` to reflect that placeholders have been resolved
   - Consider removing the placeholder-related comments entirely since the issue is now resolved

3. **Verify no test fixtures reference old placeholders**
   - Search for any remaining references to placeholder names in test fixture YAML files
   - Update golden test files if needed

## Verification Steps for Story 29.4

After completing the test cleanup in Story 29.4:

1. Run full test suite: `uv run pytest tests/`
2. Verify no references to placeholder names in test code (except in comments explaining the resolution)
3. Run linting: `uv run ruff check tests/`
4. Run type checking: `uv run mypy tests/`

## Notes

- Story 29.2 completed all high-priority test updates (tests that would fail quality gates)
- Story 29.2 code review synthesis identified and fixed test_normalization_regression.py regressions
- Story 29.4 handles lower-priority test cleanup (mock data, comments, fixtures)
- The core functionality changes are complete and verified in Story 29.2
