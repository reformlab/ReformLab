# Story 21.3: Implement typed structural, exogenous, calibration, and validation asset schemas

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

**As a** developer implementing the evidence taxonomy from the synthetic data decision document,
**I want** typed payload schemas for each data class (structural, exogenous, calibration, validation) plus a shared asset envelope pattern,
**so that** governance metadata is never mixed into domain payloads and each asset type has validated, strongly-typed contracts.

**Acceptance Criteria:**

1. **AC1:** A frozen `StructuralAsset` dataclass exists in `src/reformlab/data/assets.py` combining `DataAssetDescriptor` (governance envelope) with structural-specific payload fields
2. **AC2:** A frozen `ExogenousAsset` dataclass exists combining `DataAssetDescriptor` with exogenous-specific fields including `frequency`, `unit`, `interpolation_method`, `aggregation_method`
3. **AC3:** A frozen `CalibrationAsset` dataclass exists combining `DataAssetDescriptor` with calibration-specific fields including `target_type`, `coverage`, `source_material`
4. **AC4:** A frozen `ValidationAsset` dataclass exists combining `DataAssetDescriptor` with validation-specific fields including `validation_type`, `benchmark_status`, `criteria`
5. **AC5:** `PopulationData` remains narrow — no governance fields are added to the existing type in `src/reformlab/computation/ingestion.py`
6. **AC6:** All asset types have `to_json()` and `from_json()` methods with full validation including payload-specific constraints
7. **AC7:** A new module `src/reformlab/data/assets.py` exports all asset types and imports `DataAssetDescriptor`, `DataAssetClass`, and `EvidenceAssetError` from `descriptor.py`
8. **AC8:** Factory functions `create_structural_asset()`, `create_exogenous_asset()`, `create_calibration_asset()`, `create_validation_asset()` provide convenient construction with validation
9. **AC9:** Asset types validate data_class matches their type (e.g., `ExogenousAsset` rejects `data_class="structural"`)
10. **AC10:** Tests cover: construction with all fields, JSON round-trip, validation of data_class mismatches, frozen immutability, factory functions, and payload-specific field validation

## Tasks / Subtasks

- [ ] **Task 1: Create new assets module with shared envelope pattern** (AC: 1, 7)
  - [ ] Create `src/reformlab/data/assets.py` with `from __future__ import annotations`
  - [ ] Import `DataAssetDescriptor`, `DataAssetClass`, `EvidenceAssetError` from `.descriptor`
  - [ ] Import `pyarrow.Table` for structural asset table reference
  - [ ] Add module docstring referencing Story 21.3 and synthetic-data-decision-document-2026-03-23.md Section 2.7
  - [ ] Export all new asset types from `src/reformlab/data/__init__.py`

- [ ] **Task 2: Implement StructuralAsset frozen dataclass** (AC: 1, 9)
  - [ ] Create `StructuralAsset` dataclass with `frozen=True`
  - [ ] Required fields: `descriptor: DataAssetDescriptor`, `table: pa.Table`, `entity_type: str`, `record_count: int`
  - [ ] Optional fields: `relationships: tuple[str, ...]` (entity-to-entity links), `primary_key: str`
  - [ ] `__post_init__` validates: `descriptor.data_class == "structural"`, `record_count` matches `table.num_rows`
  - [ ] `to_json()` serializes descriptor and metadata (table stored separately via reference)
  - [ ] `from_json()` validates data_class and reconstructs with table reference

- [ ] **Task 3: Implement ExogenousAsset frozen dataclass** (AC: 2, 9)
  - [ ] Create `ExogenousAsset` dataclass with `frozen=True`
  - [ ] Required fields: `descriptor: DataAssetDescriptor`, `name: str`, `values: dict[int, float]`, `unit: str`
  - [ ] Optional fields: `frequency: str = "annual"`, `source: str`, `vintage: str`, `interpolation: str = "linear"`, `aggregation_method: str = "mean"`, `revision_policy: str`
  - [ ] `__post_init__` validates: `descriptor.data_class == "exogenous"`, `values` non-empty, years are integers
  - [ ] Add `get_value(year: int) -> float` method with interpolation logic
  - [ ] Add `validate_coverage(start_year: int, end_year: int) -> None` method that raises if years missing
  - [ ] `to_json()` and `from_json()` with full validation

- [ ] **Task 4: Implement CalibrationAsset frozen dataclass** (AC: 3, 9)
  - [ ] Create `CalibrationAsset` dataclass with `frozen=True`
  - [ ] Required fields: `descriptor: DataAssetDescriptor`, `target_type: str`, `coverage: str`
  - [ ] Optional fields: `source_material: tuple[str, ...]` (literature citations), `margin_of_error: float | None`, `confidence_level: float | None`, `methodology_notes: str`
  - [ ] `__post_init__` validates: `descriptor.data_class == "calibration"`, `target_type` is valid value
  - [ ] Define target type literals: `"marginal"`, `"aggregate_total"`, `"adoption_rate"`, `"transition_rate"`
  - [ ] `to_json()` and `from_json()` with full validation

- [ ] **Task 5: Implement ValidationAsset frozen dataclass** (AC: 4, 9)
  - [ ] Create `ValidationAsset` dataclass with `frozen=True`
  - [ ] Required fields: `descriptor: DataAssetDescriptor`, `validation_type: str`, `benchmark_status: str`, `criteria: dict[str, Any]`
  - [ ] Optional fields: `last_validated: str`, `validation_dossier: str`, `trust_status_upgradable: bool`
  - [ ] `__post_init__` validates: `descriptor.data_class == "validation"`, `benchmark_status` is valid value
  - [ ] Define validation type literals: `"marginal_check"`, `"joint_distribution"`, `"subgroup_stability"`, `"downstream_performance"`
  - [ ] Define benchmark status literals: `"passed"`, `"failed"`, `"pending"`, `"not_applicable"`
  - [ ] `to_json()` and `from_json()` with full validation

- [ ] **Task 6: Implement factory functions** (AC: 8)
  - [ ] Create `create_structural_asset(descriptor_kwargs, table, entity_type, ...)` that constructs `DataAssetDescriptor` with `data_class="structural"` and wraps in `StructuralAsset`
  - [ ] Create `create_exogenous_asset(descriptor_kwargs, name, values, unit, ...)` with `data_class="exogenous"`
  - [ ] Create `create_calibration_asset(descriptor_kwargs, target_type, coverage, ...)` with `data_class="calibration"`
  - [ ] Create `create_validation_asset(descriptor_kwargs, validation_type, benchmark_status, criteria, ...)` with `data_class="validation"`
  - [ ] Each factory validates `DataAssetDescriptor` construction and asset-specific constraints

- [ ] **Task 7: Verify PopulationData remains narrow** (AC: 5)
  - [ ] Review `src/reformlab/computation/ingestion.py` to confirm `PopulationData` has no governance fields
  - [ ] Document that governance metadata travels via `DataAssetDescriptor` envelope, not in `PopulationData`
  - [ ] Add comment in `PopulationData` docstring explaining narrow scope

- [ ] **Task 8: Create comprehensive test suite** (AC: 10)
  - [ ] Create `tests/data/test_assets.py`
  - [ ] Test class structure mirrors `tests/data/test_data_asset_descriptor.py`
  - [ ] Tests: construction with all fields, JSON round-trip, validation of data_class mismatches, frozen immutability
  - [ ] Test `ExogenousAsset.get_value()` interpolation and `validate_coverage()` error cases
  - [ ] Test factory functions with valid and invalid inputs
  - [ ] Test payload-specific field validation (e.g., empty values dict, invalid target_type)
  - [ ] Error path tests: `pytest.raises(EvidenceAssetError, match=...)`

- [ ] **Task 9: Update module exports** (AC: 7)
  - [ ] Add all asset types to `src/reformlab/data/__init__.py`
  - [ ] Add factory functions to exports if public API
  - [ ] Verify imports work: `from reformlab.data import StructuralAsset, ExogenousAsset, CalibrationAsset, ValidationAsset`

## Dev Notes

### Architecture Context

**Evidence Taxonomy (from synthetic-data-decision-document-2026-03-23.md Section 2.6):**

The synthetic data decision document defines a **broader data taxonomy** that ReformLab must implement. Each data class has a distinct role:

| Data Class | Role | Example Questions |
| ----- | ----- | ----- |
| **Structural Data** | Define who or what is modeled | "Who are the households, people, firms, and places?" |
| **Exogenous Data** | Provide observed/projected context inputs | "What are energy prices, carbon tax rates, technology costs this year?" |
| **Calibration and Validation Data** | Fit and test the model | "Does the model reproduce observed reality well enough?" |
| **Governance Data** | Constrain use and claims | "What can be used, and what can be claimed from it?" |

**Story 21.3 Scope:** This story implements the **typed payload contracts** for each data class. Story 21.1 provided the shared `DataAssetDescriptor` governance envelope; this story adds the domain-specific payload types that use that envelope.

**Key Design Principle (Section 2.8):**
> `PopulationData` should remain a narrow structural container, not a catch-all object for all modelling context.

This story enforces that principle by keeping governance metadata in the `DataAssetDescriptor` envelope, separate from domain payload objects.

### Relationship to Story 21.1 and 21.2

**Story 21.1** (completed):
- Created `DataAssetDescriptor` with `data_class: DataAssetClass` field
- Defined `DataAssetClass` Literal: `"structural"`, `"exogenous"`, `"calibration"`, `"validation"`
- Created `EvidenceAssetError` for validation failures

**Story 21.2** (completed):
- Extended API models with dual-field evidence classification
- Frontend TypeScript types updated

**Story 21.3** (this story):
- Creates typed payload contracts for each data class
- Uses `DataAssetDescriptor` as the governance envelope
- Validates `data_class` matches asset type (e.g., `ExogenousAsset` requires `data_class="exogenous"`)

### Project Structure Notes

**File locations:**

- **New module:** `src/reformlab/data/assets.py` — all asset type definitions
- **Existing type (unchanged):** `src/reformlab/computation/ingestion.py` — `PopulationData` stays narrow
- **Tests:** `tests/data/test_assets.py` — mirrors existing `tests/data/test_data_asset_descriptor.py` structure
- **Exports:** `src/reformlab/data/__init__.py` — add new asset types

**Import pattern:**
```python
from reformlab.data.assets import (
    StructuralAsset,
    ExogenousAsset,
    CalibrationAsset,
    ValidationAsset,
    create_structural_asset,
    create_exogenous_asset,
    create_calibration_asset,
    create_validation_asset,
)
from reformlab.data import DataAssetDescriptor, EvidenceAssetError, DataAssetClass
```

### Type System Constraints

**Shared Envelope Pattern:**

All asset types follow the same pattern: `DataAssetDescriptor` (governance envelope) + payload-specific fields.

```python
@dataclass(frozen=True)
class StructuralAsset:
    """Structural data asset with governance envelope.

    Combines DataAssetDescriptor (governance metadata) with structural-
    specific payload (entity tables, relationships, record counts).

    Story 21.3 / AC1.
    """
    descriptor: DataAssetDescriptor  # Governance envelope
    table: pa.Table                   # PyArrow table with entity data
    entity_type: str                  # "household", "person", "firm", etc.
    record_count: int                 # Must match table.num_rows
    relationships: tuple[str, ...] = ()  # entity-to-entity links
    primary_key: str = ""             # Primary key column name
```

**ExogenousAsset with interpolation:**

```python
@dataclass(frozen=True)
class ExogenousAsset:
    """Exogenous time series asset with governance envelope.

    Story 21.3 / AC2.
    """
    descriptor: DataAssetDescriptor
    name: str                          # Series identifier
    values: dict[int, float]           # Year-indexed values
    unit: str                          # Physical unit (e.g., "EUR/kWh")
    frequency: str = "annual"          # Source frequency
    source: str = ""                   # Institutional provenance
    vintage: str = ""                  # Publication vintage
    interpolation: str = "linear"      # "linear", "step", "none"
    aggregation_method: str = "mean"   # How source values are aggregated
    revision_policy: str = ""          # How revisions are tracked

    def get_value(self, year: int) -> float:
        """Get value for year with interpolation."""
        if year in self.values:
            return self.values[year]
        # Interpolate between nearest years
        years = sorted(self.values.keys())
        # ... interpolation logic

    def validate_coverage(self, start_year: int, end_year: int) -> None:
        """Raise EvidenceAssetError if years missing."""
        missing = [y for y in range(start_year, end_year + 1) if y not in self.values]
        if missing:
            raise EvidenceAssetError(
                f"ExogenousAsset coverage incomplete - missing years: {missing}"
            )
```

**CalibrationAsset with target types:**

```python
# Calibration target type literals
CalibrationTargetType = Literal[
    "marginal",           # Distribution marginals
    "aggregate_total",    # Official aggregates (revenue, expenditure)
    "adoption_rate",      # Technology adoption rates
    "transition_rate",    # Year-over-year transition rates
]

@dataclass(frozen=True)
class CalibrationAsset:
    """Calibration target asset with governance envelope.

    Story 21.3 / AC3.
    """
    descriptor: DataAssetDescriptor
    target_type: CalibrationTargetType
    coverage: str                     # "national", "regional", etc.
    source_material: tuple[str, ...] = ()  # Literature citations
    margin_of_error: float | None = None
    confidence_level: float | None = None
    methodology_notes: str = ""
```

**ValidationAsset with benchmark status:**

```python
# Validation type literals
ValidationType = Literal[
    "marginal_check",           # Marginal distribution validation
    "joint_distribution",       # Cross-tab validation
    "subgroup_stability",       # Subgroup consistency checks
    "downstream_performance",   # Model output validation
]

# Benchmark status literals
ValidationBenchmarkStatus = Literal[
    "passed",
    "failed",
    "pending",
    "not_applicable",
]

@dataclass(frozen=True)
class ValidationAsset:
    """Validation benchmark asset with governance envelope.

    Story 21.3 / AC4.
    """
    descriptor: DataAssetDescriptor
    validation_type: ValidationType
    benchmark_status: ValidationBenchmarkStatus
    criteria: dict[str, Any]            # Validation criteria
    last_validated: str = ""            # ISO 8601 date
    validation_dossier: str = ""         # Link to dossier
    trust_status_upgradable: bool = False  # Can status improve?
```

### Factory Function Pattern

Factory functions simplify construction by handling `DataAssetDescriptor` creation with correct `data_class`:

```python
def create_exogenous_asset(
    # Descriptor fields
    asset_id: str,
    name: str,
    description: str,
    origin: DataAssetOrigin,
    access_mode: DataAssetAccessMode,
    trust_status: DataAssetTrustStatus,
    # Exogenous-specific fields
    values: dict[int, float],
    unit: str,
    frequency: str = "annual",
    interpolation: str = "linear",
    # ... other fields
) -> ExogenousAsset:
    """Factory function for creating ExogenousAsset with validated descriptor.

    Story 21.3 / AC8.
    """
    descriptor = DataAssetDescriptor(
        asset_id=asset_id,
        name=name,
        description=description,
        data_class="exogenous",  # Enforced by factory
        origin=origin,
        access_mode=access_mode,
        trust_status=trust_status,
        # ... other descriptor fields
    )
    return ExogenousAsset(
        descriptor=descriptor,
        name=name,
        values=values,
        unit=unit,
        frequency=frequency,
        interpolation=interpolation,
    )
```

### Testing Standards

**From project-context.md:**
- Mirror source structure: `tests/data/` matches `src/reformlab/data/`
- Class-based test grouping
- Direct assertions with plain `assert`
- Error path tests use `pytest.raises(EvidenceAssetError, match=...)`

**Required test coverage:**
1. Construction with all fields for each asset type — AC1-AC4
2. JSON round-trip (to_json → from_json → equality) — AC6
3. data_class mismatch raises `EvidenceAssetError` — AC9
4. Frozen immutability (raises `FrozenInstanceError` on mutation) — AC1-AC4
5. Factory functions create valid assets — AC8
6. ExogenousAsset.get_value() interpolation logic — AC2
7. ExogenousAsset.validate_coverage() error on missing years — AC2
8. Payload-specific validation (empty values, invalid target_type, etc.) — AC10

**Example test structure:**

```python
class TestStructuralAsset:
    """Tests for StructuralAsset typed contract.

    Story 21.3 / AC1.
    """

    def test_create_with_all_fields(self) -> None:
        """Given all fields, when created, then all fields are accessible."""
        descriptor = DataAssetDescriptor(
            asset_id="test-population",
            name="Test Population",
            description="Test structural asset",
            data_class="structural",
            origin="synthetic-public",
            access_mode="bundled",
            trust_status="exploratory",
        )
        table = pa.Table.from_pydict({"household_id": [1, 2, 3]})
        asset = StructuralAsset(
            descriptor=descriptor,
            table=table,
            entity_type="household",
            record_count=3,
            primary_key="household_id",
        )
        assert asset.descriptor.data_class == "structural"
        assert asset.record_count == 3
        assert asset.entity_type == "household"

    def test_data_class_mismatch_raises_error(self) -> None:
        """Given descriptor with wrong data_class, when created, then raises."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test",
            description="Test",
            data_class="exogenous",  # Wrong!
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        table = pa.Table.from_pydict({"col": [1]})
        with pytest.raises(EvidenceAssetError, match="data_class.*structural"):
            StructuralAsset(
                descriptor=descriptor,
                table=table,
                entity_type="household",
                record_count=1,
            )
```

### Data Class Validation Pattern

All asset types validate `descriptor.data_class` in `__post_init__`:

```python
def __post_init__(self) -> None:
    """Validate data_class matches asset type."""
    if self.descriptor.data_class != "structural":
        raise EvidenceAssetError(
            f"StructuralAsset requires data_class='structural', "
            f"got '{self.descriptor.data_class}'"
        )
    if self.record_count != self.table.num_rows:
        raise EvidenceAssetError(
            f"StructuralAsset record_count mismatch: "
            f"expected {self.table.num_rows}, got {self.record_count}"
        )
```

### Integration with Existing Types

**PopulationData stays narrow (AC5):**

The existing `PopulationData` type in `src/reformlab/computation/ingestion.py` should NOT be modified to add governance fields. Instead, governance metadata travels via the `DataAssetDescriptor` envelope when assets are ingested or serialized.

```python
# PopulationData remains narrow - no changes needed
@dataclass(frozen=True)
class PopulationData:
    """Container for population entity tables.

    This type stays narrow — governance metadata lives in
    DataAssetDescriptor, not here.

    Story 21.3 / AC5: Do not add governance fields to this type.
    """
    primary_table: pa.Table
    entity_tables: dict[str, pa.Table] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
```

### Exogenous Context Integration

Story 21.6 will implement `ExogenousContext` which groups multiple `ExogenousAsset` instances. This story defines the individual asset type; Story 21.6 defines the collection and read-only lookup interface.

**Future integration (Story 21.6):**
```python
@dataclass(frozen=True)
class ExogenousContext:
    """Groups all exogenous series for a scenario.

    Story 21.6 will implement this using ExogenousAsset from Story 21.3.
    """
    series: dict[str, ExogenousAsset]  # name -> asset

    def get(self, name: str, year: int) -> float:
        """Look up value by series name and year."""
        if name not in self.series:
            raise KeyError(f"Exogenous series '{name}' not found")
        return self.series[name].get_value(year)

    def validate_coverage(self, start_year: int, end_year: int) -> None:
        """Validate all series cover the simulation horizon."""
        for asset in self.series.values():
            asset.validate_coverage(start_year, end_year)
```

### References

**Primary source documents:**
- [synthetic-data-decision-document-2026-03-23.md](/Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/synthetic-data-decision-document-2026-03-23.md) — Sections 2.2-2.7 for data taxonomy and recommended internal objects
- [epic-21-trust-governed-open-synthetic-evidence-foundation.md](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/epic-21-trust-governed-open-synthetic-evidence-foundation.md) — Story 21.3 notes and epic context
- [Story 21.1](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/21-1-implement-canonical-evidence-asset-descriptor-and-current-phase-source-matrix.md) — DataAssetDescriptor and DataAssetClass definitions
- [Story 21.2](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/21-2-add-origin-access-mode-trust-status-contracts-across-backend-apis-and-frontend-models.md) — API model integration

**Code patterns to follow:**
- [src/reformlab/data/descriptor.py](/Users/lucas/Workspace/reformlab/src/reformlab/data/descriptor.py) — DataAssetDescriptor pattern and validation
- [src/reformlab/computation/ingestion.py](/Users/lucas/Workspace/reformlab/src/reformlab/computation/ingestion.py) — PopulationData (keep narrow, do not modify)
- [tests/data/test_data_asset_descriptor.py](/Users/lucas/Workspace/reformlab/tests/data/test_data_asset_descriptor.py) — Test class structure
- [src/reformlab/orchestrator/types.py](/Users/lucas/Workspace/reformlab/src/reformlab/orchestrator/types.py) — YearState and OrchestratorConfig patterns

**Project context:**
- [docs/project-context.md](/Users/lucas/Workspace/reformlab/docs/project-context.md) — Critical rules for language rules, framework rules, testing rules
- [_bmad-output/project-context.md](/Users/lucas/Workspace/reformlab/_bmad-output/project-context.md) — Technology stack, architecture patterns

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

None (story creation)

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

### File List

**Files to create:**
- `src/reformlab/data/assets.py` — StructuralAsset, ExogenousAsset, CalibrationAsset, ValidationAsset, factory functions
- `tests/data/test_assets.py` — Comprehensive test suite for all asset types

**Files to modify:**
- `src/reformlab/data/__init__.py` — Export new asset types and factory functions
- `src/reformlab/computation/ingestion.py` — Add comment to PopulationData docstring explaining narrow scope (AC5)

**Files to read for context:**
- `src/reformlab/data/descriptor.py` — DataAssetDescriptor, DataAssetClass, EvidenceAssetError
- `src/reformlab/computation/ingestion.py` — PopulationData (verify narrow scope)
- `tests/data/test_data_asset_descriptor.py` — Test class structure pattern
