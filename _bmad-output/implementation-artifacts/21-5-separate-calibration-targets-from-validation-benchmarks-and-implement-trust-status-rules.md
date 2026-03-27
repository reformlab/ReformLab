# Story 21.5: Separate calibration targets from validation benchmarks and implement trust-status rules

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

**As a** policy analyst calibrating behavioral models and validating synthetic outputs,
**I want** calibration targets and validation benchmarks stored as distinct concepts with trust-status rules preventing train/test leakage and unsafe synthetic promotion,
**so that** calibration data never silently doubles as validation evidence and synthetic outputs cannot become `production-safe` without explicit validation.

## Acceptance Criteria

1. **AC1:** Calibration target assets use `DataAssetDescriptor` with `data_class="calibration"` and are stored separately from validation benchmarks which use `data_class="validation"`; assets follow the envelope pattern established in Story 21.3 (composition of DataAssetDescriptor, not inheritance from StructuralAsset)
2. **AC2:** Calibration target envelope includes `is_in_sample: bool` and `holdout_group: str | None` fields; validation benchmark envelope includes `certified_at: str | None` (ISO 8601 timestamp), `certified_by: str | None` (actor identity), and `validation_method: str` fields
3. **AC3:** A `TrustStatusRule` protocol in `src/reformlab/governance/trust_rules.py` defines `check(descriptor: DataAssetDescriptor, metadata: dict[str, Any]) -> TrustStatusRuleResult` with fields `passed: bool`, `reason: str`, `recommended_status: DataAssetTrustStatus`
4. **AC4:** Built-in trust-status rules registered in `src/reformlab/governance/registry.py`:
   - `SyntheticWithoutValidationDossierRule`: Synthetic-public assets require non-empty validation dossier and `benchmark_status="passed"` for production-safe status
   - `CalibrationDataNotValidationRule`: Assets with `data_class="calibration"` cannot be used as validation benchmarks (checks `data_class` mismatch)
   - `ValidationAssetCertificationRule`: Validation benchmarks default to `trust_status="validation-pending"`; upgrade to `production-safe` requires explicit certification with complete dossier
5. **AC5:** Validation/preflight check system from Epic-20 Story 20.7 extended with trust-status rules via existing `ValidationCheck` registration pattern in `src/reformlab/server/routes/validation.py`
6. **AC6:** API endpoints for managing calibration targets and validation benchmarks:
   - `POST /api/calibration/targets` - register calibration target with metadata
   - `GET /api/calibration/targets` - list all calibration targets
   - `POST /api/validation/benchmarks` - register validation benchmark
   - `GET /api/validation/benchmarks` - list all validation benchmarks
   - `POST /api/validation/{benchmark_id}/certify` - certify benchmark (requires validation_dossier), upgrades trust_status to "production-safe" when `benchmark_status="passed"` and dossier is complete
7. **AC7:** Preflight check `trust-status-validation` added to scenario execution, runs all registered trust-status rules against scenario-selected calibration targets and validation benchmarks, fails if any synthetic asset lacks validation dossier for production-safe use
8. **AC8:** Calibration engine from Story 15.2 uses calibration target assets for loading and records `calibration_asset_id` in run manifests under `calibration.asset_id` path
9. **AC9:** Frontend displays calibration/validation asset distinction in calibration configuration UI with visual badges for trust-status and certification status
10. **AC10:** Tests cover: calibration vs validation asset separation (different `data_class` values), trust-status rule execution with all rule outcomes, preflight check integration with both pass and fail scenarios, API endpoints with ErrorResponse `what/why/fix` format, certification flow with status transitions, manifest provenance recording

## Tasks / Subtasks

- [ ] **Task 1: Extend existing calibration and validation asset types** (AC: 1, 2)
  - [ ] `CalibrationAsset` and `ValidationAsset` already exist in `src/reformlab/data/assets.py` from Story 21.3
  - [ ] Add `is_in_sample: bool`, `holdout_group: str | None`, `calibration_method: str`, `target_years: tuple[int, ...]` to EXISTING `CalibrationAsset`
  - [ ] Add `certified_at: str | None`, `certified_by: str | None`, `validation_method: str`, `holdout_years: tuple[int, ...]` to EXISTING `ValidationAsset`
  - [ ] Keep envelope pattern: assets compose `DataAssetDescriptor`, do NOT inherit from `StructuralAsset`
  - [ ] Add Literal type constraints: `HoldoutGroup = Literal["train", "validation", "test"]`, `CalibrationMethod = Literal["maximum_likelihood", "method_of_moments", "bayesian"]`, `ValidationMethod = Literal["holdout", "cross_validation", "external", "bootstrap"]`

- [ ] **Task 2: Create trust-status rule protocol** (AC: 3, 4)
  - [ ] Create `src/reformlab/governance/trust_rules.py`
  - [ ] Define `TrustStatusRuleResult` frozen dataclass with `passed`, `reason`, `recommended_status`
  - [ ] Define `TrustStatusRule` protocol with `check(descriptor: DataAssetDescriptor, metadata: dict[str, Any]) -> TrustStatusRuleResult` method
  - [ ] Implement `SyntheticWithoutValidationDossierRule`: checks descriptor.origin for "synthetic-public", validates metadata has non-empty `validation_dossier` and `benchmark_status="passed"`
  - [ ] Implement `CalibrationDataNotValidationRule`: checks descriptor.data_class is never used across roles (calibration assets only in calibration, validation only in validation)
  - [ ] Implement `ValidationAssetCertificationRule`: validation assets with `certified_at != None` and complete dossier can be production-safe

- [ ] **Task 3: Create trust-rule registry** (AC: 5)
  - [ ] Create `src/reformlab/governance/registry.py`
  - [ ] Define `TrustRuleRegistry` class with `register(rule_id, rule)`, `get(rule_id)`, `list_all()`, `execute_all(descriptor, metadata) -> list[TrustStatusRuleResult]`
  - [ ] Initialize registry with built-in rules from Task 2
  - [ ] Add adapter function to wrap trust-status rules as `ValidationCheck` instances for preflight integration

- [ ] **Task 4: Extend validation/preflight check system** (AC: 5, 7)
  - [ ] Extend `src/reformlab/server/routes/validation.py` (from Story 20.7) with trust-status rule support
  - [ ] Use existing `ValidationCheck` class and `register_check()` function pattern
  - [ ] Create adapter that wraps `TrustStatusRule` as `ValidationCheck` with check_id format "trust-status-{rule-name}"
  - [ ] Execute all registered trust-status rules during preflight for scenario-selected assets
  - [ ] Fail preflight with HTTPException (what/why/fix format) if any critical rule fails for production-safe assets

- [ ] **Task 5: Create storage for calibration and validation assets** (AC: 1, 6)
  - [ ] Create `data/calibration/targets/` directory for calibration target assets
  - [ ] Create `data/validation/benchmarks/` directory for validation benchmark assets
  - [ ] Each asset stored as folder with `data.parquet`, `descriptor.json`, `metadata.json`
  - [ ] `metadata.json` schema: `{"is_in_sample": bool, "holdout_group": str, "calibration_method": str, "target_years": [int], ...}`
  - [ ] Implement `load_calibration_asset(asset_id)` and `load_validation_asset(asset_id)` functions in `src/reformlab/data/assets.py`

- [ ] **Task 6: Add API endpoints for calibration targets** (AC: 6)
  - [ ] Add `POST /api/calibration/targets` to `src/reformlab/server/routes/calibration.py`
  - [ ] Request body: asset metadata (including `is_in_sample`, `holdout_group`, etc.), data file (upload) or reference to existing file
  - [ ] Validates required fields with ErrorResponse format (what/why/fix), creates asset folder, stores data and metadata
  - [ ] Returns calibration asset descriptor with all fields
  - [ ] Add `GET /api/calibration/targets` - lists all calibration targets with metadata

- [ ] **Task 7: Add API endpoints for validation benchmarks** (AC: 6)
  - [ ] Add `POST /api/validation/benchmarks` to `src/reformlab/server/routes/validation.py` (separate from preflight checks)
  - [ ] Request body: benchmark metadata, data file, optional `validation_dossier`
  - [ ] Creates benchmark with `trust_status="validation-pending"` by default
  - [ ] Returns validation asset descriptor with all fields
  - [ ] Add `GET /api/validation/benchmarks` - lists all validation benchmarks

- [ ] **Task 8: Add certification endpoint** (AC: 6)
  - [ ] Add `POST /api/validation/{benchmark_id}/certify` endpoint
  - [ ] Request: `{"validation_dossier": str, "certified_by": str}` (document reference or metadata)
  - [ ] Validation requirements checklist: non-empty `validation_dossier`, `benchmark_status="passed"`, `last_validated` within 12 months, at least 2 validation criteria met
  - [ ] Updates `certified_at` (ISO 8601 timestamp), `certified_by` fields
  - [ ] Upgrades `trust_status` to "production-safe" only when all requirements satisfied
  - [ ] Returns specific error for each missing requirement (403 for auth failures, 422 for incomplete dossier)
  - [ ] Returns updated `ValidationAsset` descriptor

- [ ] **Task 9: Update calibration engine** (AC: 8)
  - [ ] Modify `src/reformlab/calibration/engine.py` (from Story 15.2)
  - [ ] Load calibration targets via `load_calibration_asset()` instead of raw files
  - [ ] Record `calibration_asset_id` in run manifests at path `manifest.calibration.asset_id`
  - [ ] Validate calibration target has `data_class="calibration"` (prevents train/test leakage)
  - [ ] Add backward compatibility: support legacy CalibrationTargetSet loading with deprecation warning

- [ ] **Task 10: Frontend calibration/validation UI integration** (AC: 9)
  - [ ] Add calibration asset selection to scenario configuration UI with `is_in_sample` badges
  - [ ] Add validation benchmark selection with certification status display
  - [ ] Display trust-status badges for all assets (using canonical trust status values)
  - [ ] Show warning if in-sample calibration data is selected as validation
  - [ ] Add API state management for `calibrationAssetId` and `validationAssetId` in scenario config

- [ ] **Task 11: Add API models and TypeScript types** (AC: 6, 9)
  - [ ] Add `CalibrationAssetResponse` and `ValidationAssetResponse` to `src/reformlab/server/models.py`
  - [ ] Response models include: all descriptor fields, asset-specific fields, trust-status and certification fields
  - [ ] Add corresponding TypeScript types to `frontend/src/api/types.ts`
  - [ ] Add API client functions in `frontend/src/api/calibration.ts` and `frontend/src/api/validation.ts`

- [ ] **Task 12: Create comprehensive test suite** (AC: 10)
  - [ ] Unit tests for trust-status rules in `tests/governance/test_trust_rules.py` with all rule outcomes (passed, failed with reasons)
  - [ ] Unit tests for trust-rule registry in `tests/governance/test_registry.py`
  - [ ] API endpoint tests for calibration/targets and validation/benchmarks with ErrorResponse format validation
  - [ ] Certification flow tests including: incomplete dossier rejection, status upgrade on completion, auth requirement
  - [ ] Preflight integration tests with rule pass and fail scenarios
  - [ ] Calibration engine integration tests with asset loading and manifest recording
  - [ ] Frontend component tests for calibration/validation UI

- [ ] **Task 13: Add prebuilt calibration/validation assets** (AC: 1)
  - [ ] Create at least one example calibration target (e.g., French vehicle adoption rates 2015-2020, `is_in_sample=True`, `holdout_group="train"`)
  - [ ] Create at least one example validation benchmark (e.g., French vehicle adoption rates 2021-2022 holdout, `validation_method="holdout"`)
  - [ ] Store in `data/calibration/targets/` and `data/validation/benchmarks/` with proper metadata.json following schema

## Dev Notes

### Architecture Context

**From Epic 21 Story 21.5 Notes:**
> Define distinct storage, APIs, and execution paths for fitting versus certification. Synthetic outputs must not become `production-safe` without an explicit validation dossier, and in-sample calibration data must not silently double as validation evidence.

**Key Design Principle:** Calibration and validation must be semantically and storage-separated to prevent train/test leakage. Assets use the envelope pattern (composition of DataAssetDescriptor) established in Story 21.3.

### Existing Code Patterns to Reference

**Story 21.3 (completed) - Asset Types:**
- `CalibrationAsset` exists at `src/reformlab/data/assets.py` from Story 21.3
- `ValidationAsset` exists at `src/reformlab/data/assets.py` from Story 21.3
- Both use envelope pattern: compose `DataAssetDescriptor`, NOT inheritance from `StructuralAsset`
- `DataAssetDescriptor` has `data_class` field for categorization

**Story 20.7 (completed) - Preflight Checks:**
- `ValidationCheck` class at `src/reformlab/server/routes/validation.py`
- `register_check()` function for registering preflight checks
- `PreflightRequest`/`PreflightResponse` models in `src/reformlab/server/models.py`
- NOT Story 20.5 - preflight system was implemented in Story 20.7

### Relationship to Previous Stories

**Story 21.1** (completed):
- Created `DataAssetDescriptor` with `trust_status` field
- Defines canonical trust status values: `production-safe`, `exploratory`, `demo-only`, `validation-pending`, `not-for-public-inference`

**Story 21.2** (completed):
- Extended API models with evidence fields
- Frontend TypeScript types include canonical evidence fields

**Story 21.3** (completed):
- Created `StructuralAsset` and `ExogenousAsset` combining `DataAssetDescriptor` with typed payload
- Created `CalibrationAsset` and `ValidationAsset` with envelope pattern
- Introduced `data_class` field for asset categorization

**Epic 20 Story 20.7** (completed):
- Extensible validation/preflight check registry exists in `src/reformlab/server/routes/validation.py`
- `ValidationCheck` protocol and `register_check()` patterns established
- This story extends the same registry with trust-status rules via adapter

**Epic 15 Stories 15.1-15.5** (completed):
- Calibration engine exists in `src/reformlab/calibration/`
- Calibration target loading via `CalibrationTargetSet`
- This story upgrades calibration targets to first-class assets with governance

### Project Structure Notes

**New files to create:**
- `src/reformlab/governance/__init__.py` — governance subsystem package
- `src/reformlab/governance/trust_rules.py` — trust-status rule protocol and implementations
- `src/reformlab/governance/registry.py` — trust-rule registry
- `src/reformlab/server/routes/calibration.py` — calibration target API endpoints
- `frontend/src/api/calibration.ts` — calibration API client
- `frontend/src/api/validation.ts` — validation API client

**New directories to create:**
- `data/calibration/targets/` — calibration target asset folders
- `data/validation/benchmarks/` — validation benchmark asset folders

**Files to modify:**
- `src/reformlab/data/assets.py` — extend existing CalibrationAsset and ValidationAsset with new fields
- `src/reformlab/server/routes/validation.py` — extend preflight system with trust-status rules (NOT server/validation.py)
- `src/reformlab/server/models.py` — add API response models
- `src/reformlab/calibration/engine.py` — use CalibrationAsset for target loading, record manifest.calibration.asset_id
- `frontend/src/api/types.ts` — add TypeScript types
- Frontend calibration configuration UI — display calibration/validation distinction

### Type System Constraints

**Extend existing CalibrationAsset (from Story 21.3):**
```python
@dataclass(frozen=True)
class CalibrationAsset:
    """Calibration target asset for model fitting.

    Used by the calibration engine to fit behavioral model parameters.
    Separated from validation benchmarks to prevent train/test leakage.

    Uses envelope pattern: composes DataAssetDescriptor, does NOT inherit from StructuralAsset.
    """
    descriptor: DataAssetDescriptor  # Must have data_class="calibration"
    # ... existing fields from Story 21.3 (target_type, coverage, etc.)
    # NEW fields for train/test separation:
    is_in_sample: bool
    holdout_group: Literal["train", "validation", "test"] | None
    calibration_method: Literal["maximum_likelihood", "method_of_moments", "bayesian"]
    target_years: tuple[int, ...]
```

**Extend existing ValidationAsset (from Story 21.3):**
```python
@dataclass(frozen=True)
class ValidationAsset:
    """Validation benchmark asset for model certification.

    Used to validate calibrated models against holdout data.
    Requires validation dossier for synthetic outputs to become production-safe.

    Uses envelope pattern: composes DataAssetDescriptor, does NOT inherit from StructuralAsset.
    """
    descriptor: DataAssetDescriptor  # Must have data_class="validation"
    # ... existing fields from Story 21.3 (validation_type, benchmark_status, validation_dossier, etc.)
    # NEW fields for certification:
    certified_at: str | None  # ISO 8601 timestamp if certified
    certified_by: str | None  # Actor identity (username/system ID)
    validation_method: Literal["holdout", "cross_validation", "external", "bootstrap"]
    holdout_years: tuple[int, ...]
```

**TrustStatusRuleResult:**
```python
@dataclass(frozen=True)
class TrustStatusRuleResult:
    """Result of executing a trust-status rule."""
    passed: bool
    reason: str
    recommended_status: DataAssetTrustStatus  # From Story 21.1
```

**TrustStatusRule protocol:**
```python
@runtime_checkable
class TrustStatusRule(Protocol):
    """Protocol for trust-status governance rules.

    Rules check assets for trust-status compliance and return
    recommendations for status upgrades/downgrades.
    """
    def check(self, descriptor: DataAssetDescriptor, metadata: dict[str, Any]) -> TrustStatusRuleResult:
        """Execute rule against asset descriptor and metadata."""
        ...
```

### Storage Format Specification

**Asset folder structure:**
```
data/calibration/targets/{asset_id}/
    data.parquet          # Calibration target data
    descriptor.json       # DataAssetDescriptor JSON
    metadata.json         # Asset-specific metadata
    schema.json           # DataSchema (optional)

data/validation/benchmarks/{asset_id}/
    data.parquet          # Validation benchmark data
    descriptor.json       # DataAssetDescriptor JSON
    metadata.json         # Asset-specific metadata
    schema.json           # DataSchema (optional)
```

**metadata.json schema for calibration:**
```json
{
    "is_in_sample": true,
    "holdout_group": "train",
    "calibration_method": "maximum_likelihood",
    "target_years": [2015, 2016, 2017, 2018, 2019, 2020]
}
```

**metadata.json schema for validation:**
```json
{
    "certified_at": "2026-03-27T15:00:00Z",
    "certified_by": "analyst@example.com",
    "validation_method": "holdout",
    "holdout_years": [2021, 2022]
}
```

### Certification Workflow

**Certification requirements checklist:**
1. `validation_dossier` string is non-empty
2. `benchmark_status` is "passed"
3. `last_validated` timestamp is within last 12 months
4. At least 2 validation criteria met

**Certification endpoint behavior:**
- Request: `POST /api/validation/{benchmark_id}/certify` with `{"validation_dossier": str, "certified_by": str}`
- Success (200): Updates `certified_at`, `certified_by`, upgrades `trust_status` to "production-safe" if all requirements met
- Incomplete dossier (422): Returns specific error for each missing requirement
- Auth failure (403): Actor not authorized to certify
- Asset not found (404): Benchmark ID does not exist

### API Error Response Format

**All new endpoints use ErrorResponse format:**
```python
raise HTTPException(
    status_code=422,
    detail={
        "what": "Calibration target has invalid is_in_sample value",
        "why": "is_in_sample must be a boolean",
        "fix": "Provide boolean value for is_in_sample field"
    }
)
```

### Testing Standards

**Backend tests:**
- `tests/governance/test_trust_rules.py` — rule execution tests with all outcomes
- `tests/governance/test_registry.py` — registry management tests
- `tests/server/test_routes_calibration.py` — calibration API tests with ErrorResponse validation
- `tests/server/test_routes_validation.py` — validation API tests
- `tests/calibration/test_engine_integration.py` — calibration engine with assets

**Frontend tests:**
- Component tests for calibration/validation UI
- API client tests for calibration and validation endpoints

### Integration with Existing Patterns

**Use existing ValidationCheck pattern from Story 20.7:**
```python
# Wrap trust-status rules as ValidationCheck instances:
register_check(ValidationCheck(
    check_id="trust-status-synthetic-no-dossier",
    label="Synthetic asset has validation dossier",
    severity="error",
    check_fn=lambda req: _check_synthetic_dossier(req)
))
```

**Calibration engine from Story 15.2:**
- Load calibration targets via `load_calibration_asset()`
- Record `calibration_asset_id` in manifests at path `manifest.calibration.asset_id`
- Prevents silent use of validation data as calibration targets via `data_class` validation
- Backward compatibility: legacy `CalibrationTargetSet` loading with deprecation warning

### Trust Boundary Rules

**From synthetic-data-decision-document-2026-03-23.md:**
> In-sample calibration data must not silently double as validation evidence.
> Synthetic outputs must remain visibly distinct from official observed data.
> Validation benchmarks require explicit certification dossier.

**Implementation rules:**
1. Calibration and validation assets stored in separate directories
2. API endpoints are separate (`/api/calibration/*` vs `/api/validation/*`)
3. Trust-status rules prevent misuse during preflight (check `data_class` values)
4. Certification is explicit (user action) not automatic
5. All references recorded in manifests for provenance

### References

**Primary source documents:**
- [synthetic-data-decision-document-2026-03-23.md](/Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/synthetic-data-decision-document-2026-03-23.md) — Sections on train/test leakage prevention
- [epic-21-trust-governed-open-synthetic-evidence-foundation.md](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/epic-21-trust-governed-open-synthetic-evidence-foundation.md) — Story 21.5 notes
- [Story 21.1](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/21-1-implement-canonical-evidence-asset-descriptor-and-current-phase-source-matrix.md) — DataAssetDescriptor pattern
- [Story 21.3](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/21-3-implement-typed-structural-exogenous-calibration-and-validation-asset-schemas.md) — Existing asset types with envelope pattern
- [Story 20.7](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/) — Preflight check system (NOT Story 20.5)

**Code patterns to follow:**
- [src/reformlab/data/assets.py](/Users/lucas/Workspace/reformlab/src/reformlab/data/assets.py) — Envelope pattern for assets
- [src/reformlab/server/routes/validation.py](/Users/lucas/Workspace/reformlab/src/reformlab/server/routes/validation.py) — ValidationCheck protocol (from Story 20.7)
- [src/reformlab/calibration/engine.py](/Users/lucas/Workspace/reformlab/src/reformlab/calibration/engine.py) — Calibration engine (from Story 15.2)

**Project context:**
- [_bmad-output/project-context.md](/Users/lucas/Workspace/reformlab/_bmad-output/project-context.md) — Critical rules for language rules, framework rules, testing rules

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

None (story creation)

### Completion Notes List

- Story 21.5 implements separation of calibration targets from validation benchmarks
- Uses envelope pattern from Story 21.3 (composes DataAssetDescriptor, NOT inheritance from StructuralAsset)
- Extends existing CalibrationAsset with train/test separation fields: `is_in_sample`, `holdout_group`, `calibration_method`, `target_years`
- Extends existing ValidationAsset with certification fields: `certified_at`, `certified_by`, `validation_method`, `holdout_years`
- Creates `TrustStatusRule` protocol for governance rules with `check(descriptor, metadata)` signature
- Implements three built-in rules aligned with actual asset model
- Extends validation/preflight check system from Story 20.7 with trust-status rules via ValidationCheck adapter
- Separate API endpoints: `/api/calibration/targets` and `/api/validation/benchmarks`
- Certification endpoint upgrades trust status when dossier requirements are satisfied
- Calibration engine updated to use CalibrationAsset, record manifest.calibration.asset_id, with backward compatibility
- Frontend displays calibration/validation distinction with trust badges
- Storage separation: `data/calibration/targets/` and `data/validation/benchmarks/`
- Prevents train/test leakage via semantic separation, `data_class` validation, and governance rules

### File List

**Files to create:**
- `src/reformlab/governance/__init__.py` — Governance subsystem package
- `src/reformlab/governance/trust_rules.py` — TrustStatusRule protocol and implementations
- `src/reformlab/governance/registry.py` — TrustRuleRegistry class
- `src/reformlab/server/routes/calibration.py` — Calibration target API endpoints
- `frontend/src/api/calibration.ts` — Calibration API client
- `frontend/src/api/validation.ts` — Validation API client
- `data/calibration/targets/{asset-id}/data.parquet` — Example calibration targets
- `data/calibration/targets/{asset-id}/descriptor.json`
- `data/calibration/targets/{asset-id}/metadata.json`
- `data/validation/benchmarks/{asset-id}/data.parquet` — Example validation benchmarks
- `data/validation/benchmarks/{asset-id}/descriptor.json`
- `data/validation/benchmarks/{asset-id}/metadata.json`

**Files to modify:**
- `src/reformlab/data/assets.py` — Extend existing CalibrationAsset, ValidationAsset with new fields; add load functions
- `src/reformlab/server/routes/validation.py` — Extend preflight system with trust-status rules (NOT server/validation.py)
- `src/reformlab/server/models.py` — Add API response models
- `src/reformlab/server/routes/__init__.py` — Include calibration router
- `src/reformlab/calibration/engine.py` — Use CalibrationAsset for target loading, record manifest.calibration.asset_id
- `frontend/src/api/types.ts` — Add TypeScript types

**Tests to create:**
- `tests/governance/test_trust_rules.py` — Rule execution tests
- `tests/governance/test_registry.py` — Registry tests
- `tests/server/test_routes_calibration.py` — Calibration API tests
- `tests/server/test_routes_validation.py` — Validation API tests
- `tests/calibration/test_engine_integration.py` — Calibration engine integration tests
- `frontend/src/api/__tests__/calibration.test.ts` — Calibration API client tests
- `frontend/src/api/__tests__/validation.test.ts` — Validation API client tests
