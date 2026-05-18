# Story 29.4: Sweep test fixtures off the generic names

Status: ready-for-dev

## Story

As a backend developer maintaining test hygiene,
I want test fixtures and mock data updated to use the resolved variable names from Story 29.2,
so that the test suite no longer encodes the broken naming contract and all test references align with the actual OpenFisca-France variable names.

## Acceptance Criteria

1. Given the test files that reference placeholder names, when updated, then all mock data and test fixtures use the resolved variable names (`irpp_economique` instead of `irpp`, alternative variables instead of `revenu_net`/`revenu_brut`, and no `taxe_carbone` in default-output contexts).
2. Given `tests/computation/test_openfisca_api_adapter.py`, when updated, then all mock TBS examples use `irpp_economique` instead of the placeholder `irpp`.
3. Given `tests/orchestrator/test_panel.py`, when updated, then the `test_normalizer_applies_output_mapping` test no longer uses `taxe_carbone` as a column name expecting `carbon_tax` output (use `irpp_economique` expecting `income_tax` instead).
4. Given `tests/computation/test_openfisca_integration.py`, when updated, then placeholder-related comments are updated to reflect that the placeholders have been resolved, or removed if they no longer add value.
5. Given the grep search for placeholder names in the test suite, when this story is complete, then the only remaining references to `irpp`, `revenu_net`, `revenu_brut`, and `taxe_carbone` are either: (a) legitimate uses of different variables with similar names (e.g., local variable named `irpp` holding `impot_revenu_restant_a_payer` values), (b) intentional test fixtures for custom YAML mapping functionality, or (c) comments explaining the resolution history.
6. Given the full test suite, when run after updates, then all tests pass with no regressions.

## Tasks / Subtasks

- [ ] Search and categorize all remaining placeholder name references (AC: #1)
  - [ ] Run `grep -rn -E "\b(irpp|revenu_net|revenu_brut|taxe_carbone)\b" tests/` to find all references
  - [ ] Categorize each reference as: mock data, test fixture, comment, legitimate different variable, or intentional custom mapping
  - [ ] Document findings in story notes for implementation reference

- [ ] Update mock variable names in `test_openfisca_api_adapter.py` (AC: #2)
  - [ ] Replace `irpp` with `irpp_economique` in mock TBS examples (lines ~789-795, ~889-890, ~904-905)
  - [ ] Update all test assertions that reference the mock `irpp` variable
  - [ ] Verify mock data still correctly tests entity resolution behavior

- [ ] Update test data in `test_panel.py` (AC: #3)
  - [ ] Replace `taxe_carbone` column with `irpp_economique` in `test_normalizer_applies_output_mapping` (line ~518)
  - [ ] Update rename_map to use `irpp_economique` → `income_tax` instead of `taxe_carbone` → `carbon_tax` (lines ~548-550)
  - [ ] Update assertion to expect `irpp_economique` instead of `taxe_carbone` in normalized column names (line ~565)
  - [ ] Verify test still validates that French variable names are renamed to English project names

- [ ] Update or remove placeholder-related comments in `test_openfisca_integration.py` (AC: #4)
  - [ ] Review comments around lines ~672-674 that reference placeholder names
  - [ ] Update comments to explain that placeholders were resolved in Story 29.2, or remove if they no longer add value
  - [ ] Ensure any remaining comments about `irpp` clearly distinguish between the placeholder (replaced) and the actual OpenFisca variable `impot_revenu_restant_a_payer` (still in use)

- [ ] Verify no test fixture YAML files reference placeholder names (AC: #5)
  - [ ] Run `grep -rn -E "\b(irpp|revenu_net|revenu_brut|taxe_carbone)\b" tests/fixtures/` to verify fixtures are clean
  - [ ] If any fixtures are found, update them to use resolved names or document why they should remain

- [ ] Verify intentional uses are documented (AC: #5)
  - [ ] For `test_mapping.py` line ~69 (`taxe_carbone` in custom YAML mapping test), add comment explaining this is intentional (tests custom mapping functionality, not default output variables)
  - [ ] For `test_result.py` mock column names (`irpp`), add comment explaining these are arbitrary column names, not OpenFisca variable references

- [ ] Quality gates (AC: #6)
  - [ ] Run full test suite: `uv run pytest tests/`
  - [ ] Run linting: `uv run ruff check tests/`
  - [ ] Run type checking: `uv run mypy tests/`
  - [ ] Verify all tests pass with no regressions

## Dev Notes

### Critical Context for Implementation

**The Problem Chain (from Stories 29.1 and 29.2):**
- Story 29.2 resolved four generic-name placeholder names in `_DEFAULT_OUTPUT_MAPPING`:
  - `irpp` → Replaced with `irpp_economique` (actual OpenFisca-France variable)
  - `revenu_net` → Removed (no direct equivalent exists)
  - `revenu_brut` → Removed (no household-level equivalent exists)
  - `taxe_carbone` → Removed (ReformLab-specific policy output)
- Story 29.2 updated all high-priority tests that would fail quality gates
- Story 29.4 handles lower-priority test cleanup (mock data, comments, fixtures)

**What Was Already Updated in Story 29.2:**
The following tests were already updated in Story 29.2 and should NOT be modified:
- `test_result_normalizer.py::test_default_mapping_constants` — Updated to verify `irpp_economique` in mapping
- `test_result_normalizer.py::test_renames_known_openfisca_variables` — Uses `irpp_economique` instead of `irpp`
- `test_result_normalizer.py::test_without_mapping_uses_defaults` — Uses `irpp_economique` instead of `irpp`
- `test_result_normalizer.py::test_callable_produces_normalized_table` — Uses `irpp_economique` instead of `taxe_carbone`
- `test_result_normalizer.py::test_both_modes_produce_same_column_names` — Uses `irpp_economique` instead of `taxe_carbone`
- `test_dependencies.py::test_default_live_output_variables_are_french_names` — Updated to verify `irpp_economique` in live output
- `test_normalization_regression.py` — Fixed: replaced `taxe_carbone` with `irpp_economique`

**What This Story Handles:**
Story 29.4 focuses on lower-priority test cleanup that doesn't affect functionality but improves test hygiene:
1. Mock variable names in adapter tests (cosmetic consistency)
2. Test data in panel tests (uses removed `taxe_carbone` mapping)
3. Comments explaining placeholder resolution (historical context)
4. Verification that fixture YAML files are clean
5. Documentation of intentional uses

### Key Files to Update

**1. `tests/computation/test_openfisca_api_adapter.py`**
- Lines ~789-795, ~889-890, ~904-905: Mock TBS examples use `irpp` as a placeholder variable name
- These are cosmetic updates for consistency — the mock data doesn't affect actual OpenFisca behavior
- Replace `irpp` with `irpp_economique` in:
  - `output_variables` tuples
  - `variable_entities` dicts
  - Mock simulation data arrays
  - Test assertions

**2. `tests/orchestrator/test_panel.py`**
- Line ~518: Test data creates a `taxe_carbone` column expecting `carbon_tax` output
- Lines ~548-550: Rename map includes `taxe_carbone` → `carbon_tax`
- Line ~565: Assertion expects `taxe_carbone` to be absent from normalized output
- **Issue:** `taxe_carbone` was removed from `_DEFAULT_OUTPUT_MAPPING` in Story 29.2, so this test no longer reflects the current state
- **Solution:** Replace `taxe_carbone` with `irpp_economique` and update expected mapping to `income_tax`

**3. `tests/computation/test_openfisca_integration.py`**
- Lines ~672-674: Comments reference the placeholder names in historical context
- **Solution:** Update comments to explain that placeholders were resolved in Story 29.2, or remove if they no longer add value
- **Important:** Many local variables named `irpp` in this file are NOT placeholders — they hold values from the actual OpenFisca variable `impot_revenu_restant_a_payer` (a different variable entirely). Do NOT change these.

**4. `tests/computation/test_mapping.py`**
- Line ~69: Contains `taxe_carbone` in a YAML test fixture for custom mapping functionality
- **Solution:** Add a comment explaining this is intentional (tests custom YAML mapping, not default output variables)

**5. `tests/computation/test_result.py`**
- Lines ~95, ~115, ~136: Mock data tables use `irpp` as an arbitrary column name
- **Solution:** Add a comment explaining these are arbitrary mock column names, not OpenFisca variable references

### Files to Verify (No Changes Expected)

- `tests/fixtures/**/*.yaml` — No placeholder name references expected (already verified clean)
- `tests/fixtures/**/*.csv` — No placeholder name references expected
- Other test files — Only update if placeholder names are found in inappropriate contexts

### Testing Strategy

**Search First:**
```bash
# Find all references to placeholder names
grep -rn -E "\b(irpp|revenu_net|revenu_brut|taxe_carbone)\b" tests/
```

**Categorize Each Reference:**
- **Mock data:** Update to use resolved names
- **Test fixtures:** Update if testing default behavior, leave if testing custom functionality
- **Comments:** Update to reflect resolution or remove if obsolete
- **Legitimate different variable:** Leave as-is (e.g., local variable `irpp` holding `impot_revenu_restant_a_payer`)
- **Intentional custom mapping:** Document with comment explaining purpose

**Validation:**
After updates, run the full test suite to ensure no regressions:
```bash
uv run pytest tests/
```

### Quality Gates

```bash
# Full test suite
uv run pytest tests/

# Linting
uv run ruff check tests/

# Type checking
uv run mypy tests/
```

### Dependencies

**Requires:**
- Story 29.2 (placeholder resolution) — Complete

**Blocks:** Story 29.5 (regression tests for schema-mismatch handling)

**Independent of:** Story 29.1 (custom variables) — already complete
**Independent of:** Story 29.3 (live output validation) — already complete

### Project Structure Notes

**Files to Modify:**
- `tests/computation/test_openfisca_api_adapter.py` — Update mock variable names
- `tests/orchestrator/test_panel.py` — Update test data to use resolved variable name
- `tests/computation/test_openfisca_integration.py` — Update or remove placeholder-related comments
- `tests/computation/test_mapping.py` — Add documentation comment
- `tests/computation/test_result.py` — Add documentation comment

**Files to Verify:**
- `tests/fixtures/**/*.yaml` — Verify no placeholder name references
- All test files — Verify only appropriate references remain

### References

- [Source: _bmad-output/implementation-artifacts/29-2-migration-plan.md] — Detailed migration plan from Story 29.2
- [Source: _bmad-output/implementation-artifacts/29-2-resolve-generic-name-placeholders.md] — Story 29.2 completion state
- [Source: src/reformlab/computation/result_normalizer.py:73-96] — Current `_DEFAULT_OUTPUT_MAPPING` with resolved names
- [Source: tests/computation/test_openfisca_api_adapter.py] — Mock TBS examples using placeholder names
- [Source: tests/orchestrator/test_panel.py] — Test data using removed `taxe_carbone` mapping
- [Source: tests/computation/test_openfisca_integration.py] — Comments referencing placeholder resolution

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

No debug logs. Story file created through comprehensive analysis of Epic 29 context, Story 29.2 migration plan, and test file grep analysis.

### Completion Notes List

1. **Epic 29 Analysis Complete** — Reviewed Epic 29 scope and dependency chain: 29.1 + 29.2 → 29.3 → 29.4 → 29.5.
2. **Story 29.2 Migration Plan Reviewed** — Analyzed the detailed migration plan created in Story 29.2 to understand exactly what test cleanup work remains.
3. **Test File Grep Analysis Complete** — Searched for all remaining references to placeholder names (`irpp`, `revenu_net`, `revenu_brut`, `taxe_carbone`) in the test suite.
4. **Reference Categorization Complete** — Categorized all found references as mock data, test fixtures, comments, legitimate different variables, or intentional custom mappings.
5. **Files to Update Identified** — Confirmed 5 files need updates: `test_openfisca_api_adapter.py`, `test_panel.py`, `test_openfisca_integration.py`, `test_mapping.py`, `test_result.py`.
6. **Fixture YAML Files Verified Clean** — Confirmed no fixture YAML files reference placeholder names.
7. **Acceptance Criteria Specified** — Six criteria covering reference updates, specific file updates, comment cleanup, grep verification, and test suite passing.
8. **Implementation Strategy Defined** — Search-first approach with categorization, then targeted updates, followed by validation.
9. **Quality Gates Specified** — Full test suite, linting, and type checking required.
10. **Documentation Comments Planned** — Intentional uses (custom mapping tests, mock column names) will be documented with comments.
11. **Story Purpose Clarified** — This is a test hygiene story focusing on lower-priority cleanup after the core functionality changes in Story 29.2.
12. **Scope Boundaries Defined** — Clearly distinguished between placeholder names (removed/replaced) and legitimate different variables (e.g., `impot_revenu_restant_a_payer` often abbreviated as `irpp` in code).

### File List

**Context Files Read:**
- `_bmad-output/implementation-artifacts/29-2-migration-plan.md` — Migration plan from Story 29.2
- `_bmad-output/implementation-artifacts/29-2-resolve-generic-name-placeholders.md` — Story 29.2 completion state
- `_bmad-output/planning-artifacts/epics.md` — Epic 29 context
- `src/reformlab/computation/result_normalizer.py` — Current mapping state
- `tests/computation/test_openfisca_api_adapter.py` — Mock TBS examples
- `tests/orchestrator/test_panel.py` — Test data with `taxe_carbone`
- `tests/computation/test_openfisca_integration.py` — Comments referencing placeholders
- `tests/computation/test_mapping.py` — Custom YAML mapping test
- `tests/computation/test_result.py` — Mock data with `irpp` column names

**Files to Modify:**
- `tests/computation/test_openfisca_api_adapter.py` — Update mock variable names (cosmetic consistency)
- `tests/orchestrator/test_panel.py` — Update test data to use `irpp_economique` instead of `taxe_carbone`
- `tests/computation/test_openfisca_integration.py` — Update or remove placeholder-related comments
- `tests/computation/test_mapping.py` — Add documentation comment for intentional `taxe_carbone` use
- `tests/computation/test_result.py` — Add documentation comment for mock column names

**Files to Verify:**
- All test files — Verify no inappropriate placeholder name references remain
- `tests/fixtures/**/*.yaml` — Verify clean (already verified)

## Change Log

### 2026-05-18
- Story created based on Epic 29 context and Story 29.2 migration plan
- Analyzed all remaining placeholder name references in test suite
- Identified 5 files requiring updates
- Specified acceptance criteria, tasks, and quality gates
- Set status to ready-for-dev
- Ultimate context engine analysis completed - comprehensive developer guide created
