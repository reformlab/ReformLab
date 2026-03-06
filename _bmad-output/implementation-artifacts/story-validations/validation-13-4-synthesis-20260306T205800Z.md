# Story 13.4 Validation Synthesis Report

**Story:** 13-4-validate-custom-templates-in-portfolios-and-build-notebook-demo
**Synthesized:** 2026-03-06
**Validators:** 2 (Validator A, Validator B)
**Synthesizer:** Claude Opus 4.6

---

<!-- VALIDATION_SYNTHESIS_START -->
## Synthesis Summary

5 issues verified across both validators, 4 issues dismissed as false positives or out-of-scope. 7 changes applied to the story file addressing all Critical and High severity issues. The story had one data contract mismatch that would have caused silent test failures, one contradictory task, and several underspecified acceptance criteria.

## Validations Quality

| Validator | Score | Comments |
|-----------|-------|----------|
| Validator A | 6/10 | Identified column prefixing ambiguity but missed the critical `vehicle_emissions` vs `vehicle_emissions_gkm` field name mismatch. Flagged the CSV contradiction only indirectly. Over-rated some low-priority issues as Critical. |
| Validator B | 8/10 | Caught all three genuinely critical issues including the contradictory CSV task, the field name mismatch, and the underspecified output schema. Good enhancement suggestions on registration preconditions and non-zero assertions. Some enhancement suggestions were over-scoped (negative-path ACs). |

**Summary:** Validator B was more thorough and technically accurate. Validator A provided complementary insights on pedagogical quality but missed the most dangerous technical issue (field name mismatch).

## Issues Verified (by severity)

### Critical

- **Issue**: Contradictory population data strategy — Task 1 required creating `data/populations/demo-epic13-100.csv` while Key Design Decisions and Out of Scope Guardrails explicitly forbid CSV creation | **Source**: Validator B | **Fix**: Removed Task 1 entirely; renumbered remaining tasks. Inline synthetic data in notebook (Task 2.2) is the sole data strategy.

- **Issue**: Vehicle emissions field name mismatch — Story used `vehicle_emissions` throughout but `compute_vehicle_malus()` expects `vehicle_emissions_gkm` as the column name. Missing column silently produces zero malus (no error), so tests would pass with incorrect data | **Source**: Validator B | **Fix**: Changed all references from `vehicle_emissions` to `vehicle_emissions_gkm` in AC2, Task 2.2, Population Data Requirements table, Key Design Decision #1, and Notebook Section Plan.

### High

- **Issue**: AC2 column prefixing convention undefined — "correct column prefixing" was not defined, leaving implementation ambiguous | **Source**: Both validators | **Fix**: AC2 now explicitly specifies `{policy_type}_` prefixed columns per `PortfolioComputationStep` convention, with `household_id` preserved as join key. Added non-zero result assertions requirement.

- **Issue**: Registration import precondition for YAML round-trip not specified — `load_portfolio()` with custom templates silently fails if registration imports haven't run | **Source**: Validator B | **Fix**: AC7 now explicitly states that custom template modules must be imported before `load_portfolio()`. Added registration precondition to Testing Standards and Task 1.4 (round-trip test class).

### Medium

- **Issue**: AC5 pedagogical quality criteria too subjective — qualitative requirements without measurable checks | **Source**: Both validators | **Fix**: AC5 now includes 4 measurable criteria: (a) markdown before every code cell, (b) lifecycle steps enumerated, (c) required section headings present, (d) no external docs needed.

## Issues Dismissed

- **Claimed Issue**: Incomplete portfolio comparison details (what metrics to show) | **Raised by**: Validator A (Critical), Validator B (Enhancement) | **Dismissal Reason**: The notebook is pedagogical, not analytical. The story provides adequate guidance via the section plan ("show distributional differences", "use template-specific batch APIs"). Being overly prescriptive about specific metrics defeats the demo's pedagogical purpose and makes the story more rigid. The existing guidance is sufficient.

- **Claimed Issue**: Add negative-path ACs for unknown custom type load | **Raised by**: Validator B | **Dismissal Reason**: Error handling for unregistered types is Story 13.1's scope (already done). Adding new ACs would expand an already substantial story. The existing `TemplateError` behavior is tested in Story 13.1's test suite.

- **Claimed Issue**: Specify MockAdapter contract in story | **Raised by**: Validator B | **Dismissal Reason**: MockAdapter is an established test utility used across multiple stories. Its contract is defined in existing test infrastructure (`tests/orchestrator/conftest.py`). Duplicating its specification in every story would create maintenance overhead.

- **Claimed Issue**: Story size too large for single sprint | **Raised by**: Both validators | **Dismissal Reason**: While the story is substantial, all tasks are tightly coupled (notebook + tests for that notebook + CI for that notebook). Splitting would create artificial dependencies. The story creates no new `src/` code — it's purely validation and demonstration artifacts. The removed Task 1 (CSV creation) reduces scope further.

## Deep Verify Integration

Deep Verify did not produce findings for this story.

### DV Findings Addressed
N/A

### DV Findings Dismissed
N/A

### DV-Validator Overlap
N/A

## Changes Applied

**Location**: Story file - AC2 (line 18)
**Change**: Fixed column name `vehicle_emissions` → `vehicle_emissions_gkm`; specified `{policy_type}_` prefixing convention; added non-zero assertion requirement
**Before**:
```
with a population containing `household_id`, `income`, `carbon_emissions`, `vehicle_emissions`, and `energy_expenditure` columns, then all three policies produce per-household results that are merged into a single output table with correct column prefixing.
```
**After**:
```
with a population containing `household_id`, `income`, `carbon_emissions`, `vehicle_emissions_gkm`, and `energy_expenditure` columns, then all three policies produce per-household results that are merged into a single output table with `{policy_type}_` prefixed columns per the `PortfolioComputationStep` convention (`household_id` preserved as join key, each policy's output columns prefixed by its policy type). Tests must assert non-zero malus and aid totals to confirm the population data actually triggers policy logic.
```

**Location**: Story file - AC5 (line 24)
**Change**: Added measurable criteria (a-d) replacing subjective phrasing
**Before**:
```
then each section includes a plain-language explanation before code, the steps to author a new template are explicit...
```
**After**:
```
then: (a) every code cell is preceded by a markdown cell with a plain-language explanation, (b) the lifecycle steps are explicitly enumerated..., (c) sections "Define a Custom Template", "Register and Use", and "Portfolios with Custom Templates" are present as markdown headings, and (d) no external documentation is needed...
```

**Location**: Story file - AC7 (line 28)
**Change**: Added registration import precondition for YAML round-trip
**Before**:
```
when serialized via `dump_portfolio()` and reloaded via `load_portfolio()`, then the round-trip preserves all custom template fields...
```
**After**:
```
when serialized via `dump_portfolio()` and reloaded via `load_portfolio()` (with the custom template modules imported beforehand so types are registered), then the round-trip preserves all custom template fields... Tests and notebook must import `reformlab.templates.vehicle_malus` and `reformlab.templates.energy_poverty_aid` before calling `load_portfolio()` to ensure registration side effects have run.
```

**Location**: Story file - Tasks section (lines 32-80)
**Change**: Removed contradictory Task 1 (CSV creation); renumbered Tasks 2-6 → 1-5; fixed subtask numbering; fixed `vehicle_emissions` → `vehicle_emissions_gkm` in Task 2.2; added non-zero assertion and registration precondition notes to test task subtasks
**Before**:
```
- [ ] **Task 1: Create population data file for notebook** (AC: #2, #4)
  - [ ] 1.1 Create `data/populations/demo-epic13-100.csv`...
  ...
- [ ] **Task 2: Write portfolio integration tests**
```
**After**:
```
- [ ] **Task 1: Write portfolio integration tests** (AC: #1, #2, #3, #7)
  - [ ] 1.1 Create `tests/templates/test_custom_template_portfolio_integration.py`...
```

**Location**: Story file - Key Design Decision #1 (line 142-143)
**Change**: Fixed column name `vehicle_emissions` → `vehicle_emissions_gkm` with explanatory note
**Before**:
```
The population needs `vehicle_emissions` (float64, gCO2/km) and `energy_expenditure` (float64, EUR) columns...
```
**After**:
```
The population needs `vehicle_emissions_gkm` (float64, gCO2/km — matching `compute_vehicle_malus()` expected column name) and `energy_expenditure` (float64, EUR — matching `compute_energy_poverty_aid()` expected column name) columns...
```

**Location**: Story file - Population Data Requirements table (lines 170-176)
**Change**: Fixed column name and added contract source notes
**Before**:
```
| `vehicle_emissions` | float64 | ~80-250 gCO2/km | Vehicle malus computation |
| `energy_expenditure` | float64 | ~200-3,000 EUR | Energy poverty aid eligibility |
```
**After**:
```
| `vehicle_emissions_gkm` | float64 | ~80-250 gCO2/km | Vehicle malus computation (must match `compute_vehicle_malus()` expected column name) |
| `energy_expenditure` | float64 | ~200-3,000 EUR | Energy poverty aid eligibility (must match `compute_energy_poverty_aid()` expected column name) |
```

**Location**: Story file - Testing Standards (lines 201-210)
**Change**: Added 3 new testing standards: PortfolioComputationStep scope clarification, registration precondition, non-zero result assertions
**Before**:
```
- **Portfolio integration tests in `tests/templates/`** — unit tests with MockAdapter, no real OpenFisca
- **Class-based test grouping**...
```
**After**:
```
- **Portfolio integration tests in `tests/templates/`** — unit tests with MockAdapter, no real OpenFisca
- **`PortfolioComputationStep` is test-only** — integration tests may use `PortfolioComputationStep` directly, but the notebook must NOT...
- **Registration precondition** — tests involving `load_portfolio()` with custom templates must import custom template modules before loading...
- **Non-zero result assertions** — integration tests must assert that malus totals > 0 and aid totals > 0...
- **Class-based test grouping**...
```
<!-- VALIDATION_SYNTHESIS_END -->
