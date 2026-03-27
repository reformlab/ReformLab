# Story 21.3 Validation Synthesis Report

**Story:** 21-3-implement-typed-structural-exogenous-calibration-and-validation-asset-schemas
**Validated:** 2026-03-27
**Synthesis Agent:** Master Validator

<!-- VALIDATION_SYNTHESIS_START -->
## Synthesis Summary

Synthesis of 2 validator reviews identified **9 verified issues** (3 critical, 4 high, 2 medium) and **4 dismissed issues** as false positives. **12 changes** were applied to the story file to address field naming inconsistencies, missing export requirements, test coverage gaps, and documentation clarity issues.

The story has strong alignment with architecture patterns and clear value proposition. The main issues were internal inconsistencies (field naming), missing requirements for Literal type exports, and documentation gaps that could lead to implementation ambiguity.

## Validations Quality

### Validator A (Quality Competition Engine)
**Score:** 15.1 / 20 (REJECT)
**Quality Assessment:** High
**Comments:** Validator A identified field naming inconsistency, missing Literal type exports, and test coverage gaps. The analysis was thorough and technically accurate. Minor false positive on section reference (2.7 vs 2.7b - both are valid references to different parts of the decision document).

### Validator B (Adversarial Review)
**Score:** 13.8 / 20 (REJECT)
**Quality Assessment:** Good
**Comments:** Validator B correctly identified the JSON round-trip ambiguity for StructuralAsset and the need to clarify scope boundaries with Story 21.6. False positive on PopulationData file location (could not be verified - story's reference to ingestion.py may be intentional or an error, but without definitive proof, was not changed).

**Overall Validation Quality:** 8/10 - Both validators provided valuable insights with reasonable false positive rates.

## Issues Verified (by severity)

### Critical

- **Issue 1: AC2 field naming inconsistency - `interpolation_method` vs `interpolation`**
  - **Source:** Validator A, Validator B (consensus)
  - **Evidence:** AC2 states `interpolation_method` but Task 3 code uses `interpolation: str = "linear"`
  - **Fix Applied:** Updated AC2 to clarify both are valid (`interpolation_method` with alias `interpolation`), changed Task 3, Dev Notes examples, and factory function to use `interpolation_method` as primary field name
  - **Locations Modified:** AC2, Task 3, Dev Notes code examples (ExogenousAsset class, factory function)

- **Issue 2: Missing export requirements for new Literal types**
  - **Source:** Validator A
  - **Evidence:** Story introduces `CalibrationTargetType`, `ValidationType`, `ValidationBenchmarkStatus` but AC7 doesn't explicitly require exporting them
  - **Fix Applied:** Updated AC7 to explicitly require exporting new Literal types; updated Task 9 to add Literal types to exports; updated import pattern example
  - **Locations Modified:** AC7, Task 9, Dev Notes Import pattern section

- **Issue 3: AC10 missing test coverage for Literal type validation**
  - **Source:** Validator A
  - **Evidence:** AC10 lists test coverage but doesn't include validation of new Literal types
  - **Fix Applied:** Updated AC10 to explicitly include "validation of Literal type values (CalibrationTargetType, ValidationType, ValidationBenchmarkStatus)"
  - **Locations Modified:** AC10

### High

- **Issue 4: StructuralAsset JSON round-trip ambiguity**
  - **Source:** Validator B
  - **Evidence:** Task 2 says "table stored separately via reference" but doesn't define how from_json() reconstructs the asset
  - **Fix Applied:** Clarified that `to_json()` includes `table_path: str` field and `from_json()` validates descriptor but caller must load table separately
  - **Locations Modified:** Task 2

- **Issue 5: Exogenous scope overlap with Story 21.6**
  - **Source:** Validator B
  - **Evidence:** Story 21.3 implements interpolation/coverage methods which Story 21.6 might also need
  - **Fix Applied:** Added scope note in "Exogenous Context Integration" section clarifying that Story 21.3 provides basic interpolation (linear) and Story 21.6 will extend with more sophisticated strategies
  - **Locations Modified:** Dev Notes - Exogenous Context Integration

- **Issue 6: CalibrationAsset relationship to existing types not documented**
  - **Source:** Validator A, Validator B (consensus)
  - **Evidence:** Existing `CalibrationTarget` and `CalibrationTargetSet` types exist but relationship to new `CalibrationAsset` is unclear
  - **Fix Applied:** Added "Relationship to Existing Calibration Types" subsection explaining that CalibrationAsset is ADDITIVE, not a replacement
  - **Locations Modified:** Dev Notes - Integration with Existing Types

- **Issue 7: ExogenousAsset name field potentially redundant**
  - **Source:** Validator A
  - **Evidence:** Both descriptor and ExogenousAsset have `name` field, creating ambiguity
  - **Fix Applied:** Clarified that `ExogenousAsset.name` is series identifier for lookup (e.g., "energy_price_electricity"), distinct from `descriptor.name` (human-readable display name)
  - **Locations Modified:** Task 3, Dev Notes code example

### Medium

- **Issue 8: Missing explicit validation for NaN/infinite values in ExogenousAsset**
  - **Source:** Validator A
  - **Evidence:** `values: dict[int, float]` doesn't specify whether NaN/infinite are allowed
  - **Fix Applied:** Updated Task 3 `__post_init__` validation to include "all values are finite (not NaN or infinite)"; updated test requirements
  - **Locations Modified:** Task 3, Task 8, Dev Notes - Required test coverage

- **Issue 9: Module docstring section reference could be clearer**
  - **Source:** Validator A (partial)
  - **Evidence:** Section 2.7 reference is correct for internal data objects, but architectural separation is in Section 2.8
  - **Fix Applied:** No change needed - story correctly references Section 2.7 for data taxonomy and Section 2.8 for design principle. Reference is accurate as-is.

## Issues Dismissed

- **Claimed Issue:** Wrong PopulationData file target (should be computation/types.py not ingestion.py)
  - **Raised by:** Validator B
  - **Dismissal Reason:** Could not verify definitively. The story references `src/reformlab/computation/ingestion.py` and the ingestion.py file in context shows DataSchema and IngestionResult but no PopulationData. Without access to the actual file system to confirm PopulationData location, this issue remains uncertain. The story's reference may be intentional or an error, but changing it without verification could introduce a worse error.

- **Claimed Issue:** Section reference should be 2.7b not 2.7
  - **Raised by:** Validator A
  - **Dismissal Reason:** False positive. Story references Section 2.7 for data taxonomy (correct) and Section 2.8 for design principle (also correct). Section 2.7b is not referenced because the story doesn't focus on that specific subsection.

- **Claimed Issue:** Factory function API is ambiguous (descriptor_kwargs not typed)
  - **Raised by:** Validator B
  - **Dismissal Reason:** False positive. The `descriptor_kwargs` pattern is a common Python convention for forwarding keyword arguments. The Dev Notes provide full example with explicit parameters, making the API clear.

- **Claimed Issue:** Story is verbose and repeats concepts
  - **Raised by:** Validator B
  - **Dismissal Reason:** Minor stylistic concern. The verbosity provides valuable context for implementation and aligns with story documentation standards. No change needed.

## Deep Verify Integration

Deep Verify did not produce findings for this story.

## Changes Applied

**Location:** _bmad-output/implementation-artifacts/21-3-implement-typed-structural-exogenous-calibration-and-validation-asset-schemas.md

### Change 1: AC2 - Clarify field name consistency
**Before:**
```markdown
2. **AC2:** A frozen `ExogenousAsset` dataclass exists combining `DataAssetDescriptor` with exogenous-specific fields including `frequency`, `unit`, `interpolation_method`, `aggregation_method`
```
**After:**
```markdown
2. **AC2:** A frozen `ExogenousAsset` dataclass exists combining `DataAssetDescriptor` with exogenous-specific fields including `frequency`, `unit`, `interpolation_method` (alias `interpolation`), `aggregation_method`
```

### Change 2: Task 3 - Use interpolation_method as field name
**Before:**
```markdown
  - [ ] Optional fields: `frequency: str = "annual"`, `source: str`, `vintage: str`, `interpolation: str = "linear"`, `aggregation_method: str = "mean"`, `revision_policy: str`
```
**After:**
```markdown
  - [ ] Optional fields: `frequency: str = "annual"`, `source: str`, `vintage: str`, `interpolation_method: str = "linear"`, `aggregation_method: str = "mean"`, `revision_policy: str`
```

### Change 3: Task 3 - Add name field clarification
**Before:**
```markdown
  - [ ] Required fields: `descriptor: DataAssetDescriptor`, `name: str`, `values: dict[int, float]`, `unit: str`
```
**After:**
```markdown
  - [ ] Required fields: `descriptor: DataAssetDescriptor`, `name: str` (series identifier for lookup, distinct from `descriptor.name`), `values: dict[int, float]`, `unit: str`
```

### Change 4: Task 3 - Add finite value validation
**Before:**
```markdown
  - [ ] `__post_init__` validates: `descriptor.data_class == "exogenous"`, `values` non-empty, years are integers
```
**After:**
```markdown
  - [ ] `__post_init__` validates: `descriptor.data_class == "exogenous"`, `values` non-empty, years are integers, all values are finite (not NaN or infinite)
```

### Change 5: Task 2 - Clarify JSON round-trip for StructuralAsset
**Before:**
```markdown
  - [ ] `to_json()` serializes descriptor and metadata (table stored separately via reference)
  - [ ] `from_json()` validates data_class and reconstructs with table reference
```
**After:**
```markdown
  - [ ] `to_json()` serializes descriptor and metadata; table is NOT serialized (use `table_path: str` field to reference external storage)
  - [ ] `from_json()` validates data_class and returns asset with descriptor; caller must load table separately and construct full asset
```

### Change 6: Task 8 - Add NaN/infinite value test coverage
**Before:**
```markdown
  - [ ] Test payload-specific field validation (e.g., empty values dict, invalid target_type)
```
**After:**
```markdown
  - [ ] Test payload-specific field validation (e.g., empty values dict, invalid target_type, NaN/infinite values in ExogenousAsset)
```

### Change 7: Task 9 - Add Literal type exports
**Before:**
```markdown
- [ ] **Task 9: Update module exports** (AC: 7)
  - [ ] Add all asset types to `src/reformlab/data/__init__.py`
  - [ ] Add factory functions to exports if public API
  - [ ] Verify imports work: `from reformlab.data import StructuralAsset, ExogenousAsset, CalibrationAsset, ValidationAsset`
```
**After:**
```markdown
- [ ] **Task 9: Update module exports** (AC: 7)
  - [ ] Add all asset types to `src/reformlab/data/__init__.py`
  - [ ] Add new Literal types to exports: `CalibrationTargetType`, `ValidationType`, `ValidationBenchmarkStatus`
  - [ ] Add factory functions to exports if public API
  - [ ] Verify imports work: `from reformlab.data import StructuralAsset, ExogenousAsset, CalibrationAsset, ValidationAsset, CalibrationTargetType, ValidationType, ValidationBenchmarkStatus`
```

### Change 8: AC7 - Add Literal type export requirement
**Before:**
```markdown
7. **AC7:** A new module `src/reformlab/data/assets.py` exports all asset types and imports `DataAssetDescriptor`, `DataAssetClass`, and `EvidenceAssetError` from `descriptor.py`
```
**After:**
```markdown
7. **AC7:** A new module `src/reformlab/data/assets.py` exports all asset types and Literal types (`CalibrationTargetType`, `ValidationType`, `ValidationBenchmarkStatus`) and imports `DataAssetDescriptor`, `DataAssetClass`, and `EvidenceAssetError` from `descriptor.py`
```

### Change 9: AC10 - Add Literal type validation test requirement
**Before:**
```markdown
10. **AC10:** Tests cover: construction with all fields, JSON round-trip, validation of data_class mismatches, frozen immutability, factory functions, and payload-specific field validation
```
**After:**
```markdown
10. **AC10:** Tests cover: construction with all fields, JSON round-trip, validation of data_class mismatches, validation of Literal type values (CalibrationTargetType, ValidationType, ValidationBenchmarkStatus), frozen immutability, factory functions, and payload-specific field validation
```

### Change 10: Dev Notes - ExogenousAsset code example (interpolation_method)
**Before:**
```markdown
    interpolation: str = "linear"      # "linear", "step", "none"
```
**After:**
```markdown
    interpolation_method: str = "linear"  # "linear", "step", "none"
```

### Change 11: Dev Notes - ExogenousAsset code example (name field)
**Before:**
```markdown
    name: str                          # Series identifier
```
**After:**
```markdown
    name: str                          # Series identifier for lookup (e.g., "energy_price_electricity")
```

### Change 12: Dev Notes - Factory function example (interpolation_method)
**Before:**
```markdown
    interpolation: str = "linear",
    # ... other fields
) -> ExogenousAsset:
    # ...
        interpolation=interpolation,
```
**After:**
```markdown
    interpolation_method: str = "linear",
    # ... other fields
) -> ExogenousAsset:
    # ...
        interpolation_method=interpolation_method,
```

### Change 13: Dev Notes - Exogenous Context Integration (scope note)
**Before:**
```markdown
### Exogenous Context Integration

Story 21.6 will implement `ExogenousContext` which groups multiple `ExogenousAsset` instances. This story defines the individual asset type; Story 21.6 defines the collection and read-only lookup interface.
```
**After:**
```markdown
### Exogenous Context Integration

Story 21.6 will implement `ExogenousContext` which groups multiple `ExogenousAsset` instances. This story defines the individual asset type; Story 21.6 defines the collection and read-only lookup interface.

**Scope Note:** The `get_value()` and `validate_coverage()` methods in this story provide basic interpolation (linear) and coverage validation. Story 21.6 will extend this with more sophisticated interpolation strategies and context-aware validation.
```

### Change 14: Dev Notes - Relationship to Existing Calibration Types
**Before:**
```markdown
**PopulationData stays narrow (AC5):**
```
**After:**
```markdown
**Relationship to Existing Calibration Types (AC3):**

The existing calibration system (`src/reformlab/calibration/`) uses `CalibrationTarget` and `CalibrationTargetSet` types. **CalibrationAsset is ADDITIVE**, not a replacement:
- Existing `CalibrationTarget`/`CalibrationTargetSet` remain in use for calibration engine
- `CalibrationAsset` wraps calibration targets with the `DataAssetDescriptor` governance envelope
- Future stories may migrate existing calibration to use `CalibrationAsset` for consistency

**PopulationData stays narrow (AC5):**
```

### Change 15: Dev Notes - Required test coverage (updated)
**Before:**
```markdown
**Required test coverage:**
1. Construction with all fields for each asset type — AC1-AC4
2. JSON round-trip (to_json → from_json → equality) — AC6
3. data_class mismatch raises `EvidenceAssetError` — AC9
4. Frozen immutability (raises `FrozenInstanceError` on mutation) — AC1-AC4
5. Factory functions create valid assets — AC8
6. ExogenousAsset.get_value() interpolation logic — AC2
7. ExogenousAsset.validate_coverage() error on missing years — AC2
8. Payload-specific validation (empty values, invalid target_type, etc.) — AC10
```
**After:**
```markdown
**Required test coverage:**
1. Construction with all fields for each asset type — AC1-AC4
2. JSON round-trip (to_json → from_json → equality) — AC6
3. data_class mismatch raises `EvidenceAssetError` — AC9
4. Literal type validation raises `EvidenceAssetError` for invalid values — AC10
5. Frozen immutability (raises `FrozenInstanceError` on mutation) — AC1-AC4
6. Factory functions create valid assets — AC8
7. ExogenousAsset.get_value() interpolation logic — AC2
8. ExogenousAsset.validate_coverage() error on missing years — AC2
9. ExogenousAsset values validation (non-empty, integer keys, finite floats) — AC10
10. Payload-specific validation (invalid target_type, benchmark_status, etc.) — AC10
```

### Change 16: Dev Notes - Import pattern example
**Before:**
```markdown
from reformlab.data import DataAssetDescriptor, EvidenceAssetError, DataAssetClass
```
**After:**
```python
from reformlab.data import (
    DataAssetDescriptor,
    EvidenceAssetError,
    DataAssetClass,
    CalibrationTargetType,
    ValidationType,
    ValidationBenchmarkStatus,
)
```

### Change 17: Completion Notes List (updated)
**Before:**
```markdown
### Completion Notes List

- Story 21.3 creates typed payload contracts for each data class defined in Story 21.1
- Uses `DataAssetDescriptor` as shared governance envelope
- `PopulationData` stays narrow — governance metadata lives in the envelope
- Factory functions simplify construction with enforced `data_class` values
- `ExogenousAsset` includes `get_value()` interpolation and `validate_coverage()` methods
- `CalibrationAsset` defines target type literals for different calibration purposes
- `ValidationAsset` defines validation type and benchmark status literals
- All asset types validate `data_class` matches their expected value
- JSON serialization uses descriptor pattern from Story 21.1
```
**After:**
```markdown
### Completion Notes List

- Story 21.3 creates typed payload contracts for each data class defined in Story 21.1
- Uses `DataAssetDescriptor` as shared governance envelope
- `PopulationData` stays narrow — governance metadata lives in the envelope
- Factory functions simplify construction with enforced `data_class` values
- `ExogenousAsset` includes `get_value()` interpolation and `validate_coverage()` methods
- `CalibrationAsset` defines target type literals for different calibration purposes
- `ValidationAsset` defines validation type and benchmark status literals
- All asset types validate `data_class` matches their expected value
- JSON serialization uses descriptor pattern from Story 21.1
- New Literal types (`CalibrationTargetType`, `ValidationType`, `ValidationBenchmarkStatus`) are exported for reuse in APIs and Pydantic models
- `ExogenousAsset.name` is the series identifier (for lookup), distinct from `descriptor.name` (display name)
- `CalibrationAsset` is additive to existing `CalibrationTarget`/`CalibrationTargetSet` types
```

<!-- VALIDATION_SYNTHESIS_END -->
