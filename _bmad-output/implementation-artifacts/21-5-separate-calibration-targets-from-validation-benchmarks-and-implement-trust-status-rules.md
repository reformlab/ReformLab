# Story 21.5: Separate calibration targets from validation benchmarks and implement trust-status rules

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

**As a** policy analyst calibrating behavioral models and validating synthetic outputs,
**I want** calibration targets and validation benchmarks stored as distinct concepts with trust-status rules preventing train/test leakage and unsafe synthetic promotion,
**so that** calibration data never silently doubles as validation evidence and synthetic outputs cannot become `production-safe` without explicit validation.

## Acceptance Criteria

1. **AC1:** Calibration target assets (`CalibrationAsset`) use the `StructuralAsset` schema from Story 21.3 with `data_class="calibration"` and are stored separately from validation benchmarks (`ValidationAsset`) which use `data_class="validation"`
2. **AC2:** Calibration targets include `is_in_sample: bool` and `holdout_group: str | None` fields; validation benchmarks include `validation_dossier_required: bool` and `certified_at: str | None` fields
3. **AC3:** A `TrustStatusRule` protocol in `src/reformlab/governance/trust_rules.py` defines `check(asset: StructuralAsset) -> TrustStatusRuleResult` with fields `passed: bool`, `reason: str`, `recommended_status: DataAssetTrustStatus`
4. **AC4:** Built-in trust-status rules registered in `src/reformlab/governance/registry.py`:
   - `SyntheticWithoutValidationDossierRule`: Synthetic-public assets require validation dossier for production-safe status
   - `CalibrationDataNotValidationRule`: In-sample calibration data (is_in_sample=True) cannot be used as validation benchmark
   - `SyntheticOutputUpgradeRule`: Synthetic outputs default to exploratory; explicit validation dossier required for production-safe upgrade
5. **AC5:** Validation/preflight check system from EPIC-20 Story 20.5 extended with trust-status rules via `register_trust_status_rule(check_id, rule, severity)` function
6. **AC6:** API endpoints for managing calibration targets and validation benchmarks:
   - `POST /api/calibration/targets` - register calibration target with metadata
   - `GET /api/calibration/targets` - list all calibration targets
   - `POST /api/validation/benchmarks` - register validation benchmark
   - `GET /api/validation/benchmarks` - list all validation benchmarks
   - `POST /api/validation/{benchmark_id}/certify` - certify benchmark (requires validation_dossier), upgrades trust_status to production-safe if applicable
7. **AC7:** Preflight check `trust-status-validation` added to scenario execution, runs all registered trust-status rules against calibration targets and validation benchmarks, fails if any synthetic asset lacks validation dossier for production-safe use
8. **AC8:** Calibration engine from Story 15.2 uses `CalibrationAsset` for target loading and records `calibration_asset_id` in manifests
9. **AC9:** Frontend displays calibration/validation asset distinction in engine validation screen (Story 20.5) with visual badges and trust-status indicators
10. **AC10:** Tests cover: calibration vs validation asset separation, trust-status rule execution, preflight check integration, API endpoints with proper error handling, certification flow, manifest provenance recording

## Tasks / Subtasks

- [ ] **Task 1: Create calibration and validation asset schemas** (AC: 1, 2)
  - [ ] Extend `src/reformlab/data/assets.py` with `CalibrationAsset` and `ValidationAsset` frozen dataclasses
  - [ ] `CalibrationAsset` fields: `is_in_sample: bool`, `holdout_group: str | None`, `calibration_method: str`, `target_years: tuple[int, ...]`
  - [ ] `ValidationAsset` fields: `validation_dossier_required: bool`, `certified_at: str | None`, `certified_by: str | None`, `validation_method: str`, `holdout_years: tuple[int, ...]`
  - [ ] Both extend `StructuralAsset` with appropriate `data_class` values
  - [ ] Add factory functions `create_calibration_asset()` and `create_validation_asset()`

- [ ] **Task 2: Create trust-status rule protocol** (AC: 3, 4)
  - [ ] Create `src/reformlab/governance/trust_rules.py`
  - [ ] Define `TrustStatusRuleResult` frozen dataclass with `passed`, `reason`, `recommended_status`
  - [ ] Define `TrustStatusRule` protocol with `check(asset: StructuralAsset) -> TrustStatusRuleResult` method
  - [ ] Implement `SyntheticWithoutValidationDossierRule`: checks if synthetic asset has validation dossier before production-safe
  - [ ] Implement `CalibrationDataNotValidationRule`: prevents in-sample calibration from being used as validation
  - [ ] Implement `SyntheticOutputUpgradeRule`: synthetic outputs default exploratory, require certification for upgrade

- [ ] **Task 3: Create trust-rule registry** (AC: 5)
  - [ ] Create `src/reformlab/governance/registry.py`
  - [ ] Define `TrustRuleRegistry` class with `register(rule_id, rule)`, `get(rule_id)`, `list_all()`, `execute_all(asset) -> list[TrustStatusRuleResult]`
  - [ ] Initialize registry with built-in rules from Task 2
  - [ ] Add `register_trust_status_rule(check_id, rule, severity)` function for preflight integration

- [ ] **Task 4: Extend validation/preflight check system** (AC: 5, 7)
  - [ ] Extend `src/reformlab/server/validation.py` (from Story 20.5) with trust-status rule support
  - [ ] Add `register_trust_status_rule(check_id, rule, severity)` function
  - [ ] Create `TrustStatusValidationCheck` class implementing `PreflightCheck` protocol
  - [ ] Execute all registered trust-status rules during preflight
  - [ ] Fail preflight if any critical rule fails for production-safe assets

- [ ] **Task 5: Create storage for calibration and validation assets** (AC: 1, 6)
  - [ ] Create `data/calibration/targets/` directory for calibration targets
  - [ ] Create `data/validation/benchmarks/` directory for validation benchmarks
  - [ ] Each asset stored as folder with `data.parquet`, `descriptor.json`, `metadata.json`
  - [ ] `metadata.json` includes asset-specific fields (is_in_sample, holdout_group, etc.)
  - [ ] Implement `load_calibration_asset(asset_id)` and `load_validation_asset(asset_id)` functions in `src/reformlab/data/assets.py`

- [ ] **Task 6: Add API endpoints for calibration targets** (AC: 6)
  - [ ] Add `POST /api/calibration/targets` to `src/reformlab/server/routes/calibration.py`
  - [ ] Request body: asset metadata, data file (upload) or reference to existing file
  - [ ] Validates required fields, creates asset folder, stores data and metadata
  - [ ] Returns created `CalibrationAsset` descriptor
  - [ ] Add `GET /api/calibration/targets` - lists all calibration targets with metadata

- [ ] **Task 7: Add API endpoints for validation benchmarks** (AC: 6)
  - [ ] Add `POST /api/validation/benchmarks` to `src/reformlab/server/routes/validation.py`
  - [ ] Request body: benchmark metadata, data file, optional validation_dossier
  - [ ] Creates benchmark with trust_status="validation-pending" by default
  - [ ] Returns created `ValidationAsset` descriptor
  - [ ] Add `GET /api/validation/benchmarks` - lists all validation benchmarks

- [ ] **Task 8: Add certification endpoint** (AC: 6)
  - [ ] Add `POST /api/validation/{benchmark_id}/certify` endpoint
  - [ ] Accepts `validation_dossier` (document reference or metadata)
  - [ ] Validates synthetic-public assets have required dossier
  - [ ] Updates `certified_at`, `certified_by` fields
  - [ ] Upgrades `trust_status` to "production-safe" for synthetic assets with complete dossier
  - [ ] Returns updated `ValidationAsset` descriptor

- [ ] **Task 9: Update calibration engine** (AC: 8)
  - [ ] Modify `src/reformlab/calibration/engine.py` (from Story 15.2)
  - [ ] Load calibration targets via `load_calibration_asset()` instead of raw files
  - [ ] Record `calibration_asset_id` in run manifests
  - [ ] Validate calibration target is not marked as validation benchmark (prevents train/test leakage)

- [ ] **Task 10: Frontend engine validation integration** (AC: 9)
  - [ ] Extend `frontend/src/components/engine/EngineValidationScreen.tsx` (from Story 20.5)
  - [ ] Add calibration target list with `is_in_sample` badges
  - [ ] Add validation benchmark list with certification status
  - [ ] Display trust-status badges for all assets
  - [ ] Show warning if in-sample calibration data is selected as validation

- [ ] **Task 11: Add API models and TypeScript types** (AC: 6, 9)
  - [ ] Add `CalibrationAssetResponse` and `ValidationAssetResponse` to `src/reformlab/server/models.py`
  - [ ] Include trust-status and certification fields
  - [ ] Add corresponding TypeScript types to `frontend/src/api/types.ts`
  - [ ] Add API client functions in `frontend/src/api/calibration.ts` and `frontend/src/api/validation.ts`

- [ ] **Task 12: Create comprehensive test suite** (AC: 10)
  - [ ] Unit tests for trust-status rules in `tests/governance/test_trust_rules.py`
  - [ ] Unit tests for trust-rule registry in `tests/governance/test_registry.py`
  - [ ] API endpoint tests for calibration/targets and validation/benchmarks
  - [ ] Certification flow tests including synthetic promotion
  - [ ] Preflight integration tests
  - [ ] Calibration engine integration tests
  - [ ] Frontend component tests for engine validation screen

- [ ] **Task 13: Add prebuilt calibration/validation assets** (AC: 1)
  - [ ] Create at least one example calibration target (e.g., French vehicle adoption rates 2015-2020)
  - [ ] Create at least one example validation benchmark (e.g., French vehicle adoption rates 2021-2022 holdout)
  - [ ] Store in `data/calibration/targets/` and `data/validation/benchmarks/` with proper metadata

## Dev Notes

### Architecture Context

**From Epic 21 Story 21.5 Notes:**
> Define distinct storage, APIs, and execution paths for fitting versus certification. Synthetic outputs must not become `production-safe` without an explicit validation dossier, and in-sample calibration data must not silently double as validation evidence.

**Key Design Principle:** Calibration and validation must be semantically and storage-separated to prevent train/test leakage.

### Relationship to Previous Stories

**Story 21.1** (completed):
- Created `DataAssetDescriptor` with `trust_status` field
- Defines canonical trust status values: `production-safe`, `exploratory`, `demo-only`, `validation-pending`, `not-for-public-inference`

**Story 21.2** (completed):
- Extended API models with evidence fields
- Frontend TypeScript types include canonical evidence fields

**Story 21.3** (completed):
- Created `StructuralAsset` combining `DataAssetDescriptor` with typed payload
- Introduced `data_class` field for asset categorization
- Factory function `create_structural_asset()` for convenient construction

**Epic 20 Story 20.5** (completed):
- Extensible validation/preflight check registry exists
- `PreflightCheck` protocol and `ValidationRegistry` patterns established
- This story extends the same registry with trust-status rules

**Epic 15 Stories 15.1-15.5** (completed):
- Calibration engine exists in `src/reformlab/calibration/`
- Calibration target loading from files
- This story upgrades calibration targets to first-class assets with governance

### Project Structure Notes

**New files to create:**
- `src/reformlab/governance/__init__.py` — governance subsystem package
- `src/reformlab/governance/trust_rules.py` — trust-status rule protocol and implementations
- `src/reformlab/governance/registry.py` — trust-rule registry
- `src/reformlab/server/routes/calibration.py` — calibration target API endpoints
- `src/reformlab/server/routes/validation.py` — validation benchmark API endpoints
- `frontend/src/api/calibration.ts` — calibration API client
- `frontend/src/api/validation.ts` — validation API client

**New directories to create:**
- `data/calibration/targets/` — calibration target asset folders
- `data/validation/benchmarks/` — validation benchmark asset folders

**Files to modify:**
- `src/reformlab/data/assets.py` — add CalibrationAsset and ValidationAsset types
- `src/reformlab/server/validation.py` — extend preflight system for trust-status rules
- `src/reformlab/server/models.py` — add API response models
- `src/reformlab/calibration/engine.py` — use CalibrationAsset for target loading
- `frontend/src/api/types.ts` — add TypeScript types
- `frontend/src/components/engine/EngineValidationScreen.tsx` — display calibration/validation distinction

### Type System Constraints

**CalibrationAsset:**
```python
@dataclass(frozen=True)
class CalibrationAsset(StructuralAsset):
    """Calibration target asset for model fitting.

    Used by the calibration engine to fit behavioral model parameters.
    Separated from validation benchmarks to prevent train/test leakage.
    """
    is_in_sample: bool
    holdout_group: str | None
    calibration_method: str  # e.g., "maximum_likelihood", "method_of_moments"
    target_years: tuple[int, ...]
```

**ValidationAsset:**
```python
@dataclass(frozen=True)
class ValidationAsset(StructuralAsset):
    """Validation benchmark asset for model certification.

    Used to validate calibrated models against holdout data.
    Requires validation dossier for synthetic outputs to become production-safe.
    """
    validation_dossier_required: bool
    certified_at: str | None
    certified_by: str | None
    validation_method: str  # e.g., "holdout", "cross_validation", "external"
    holdout_years: tuple[int, ...]
```

**TrustStatusRuleResult:**
```python
@dataclass(frozen=True)
class TrustStatusRuleResult:
    """Result of executing a trust-status rule."""
    passed: bool
    reason: str
    recommended_status: DataAssetTrustStatus
```

### Testing Standards

**Backend tests:**
- `tests/governance/test_trust_rules.py` — rule execution tests
- `tests/governance/test_registry.py` — registry management tests
- `tests/server/test_routes_calibration.py` — calibration API tests
- `tests/server/test_routes_validation.py` — validation API tests
- `tests/calibration/test_engine_integration.py` — calibration engine with assets

**Frontend tests:**
- Component tests for extended EngineValidationScreen
- API client tests for calibration and validation endpoints

### Integration with Existing Patterns

**Use existing PreflightCheck protocol from Story 20.5:**
- Trust-status rules are registered as preflight checks
- Same execution flow, error handling, and UI integration
- Extends rather than duplicates validation infrastructure

**Calibration engine from Story 15.2:**
- Load calibration targets via `load_calibration_asset()`
- Record `calibration_asset_id` in manifests for provenance
- Prevents silent use of validation data as calibration targets

### Trust Boundary Rules

**From synthetic-data-decision-document-2026-03-23.md:**
> In-sample calibration data must not silently double as validation evidence.
> Synthetic outputs must remain visibly distinct from official observed data.
> Validation benchmarks require explicit certification dossier.

**Implementation rules:**
1. Calibration and validation assets stored in separate directories
2. API endpoints are separate (`/api/calibration/*` vs `/api/validation/*`)
3. Trust-status rules prevent misuse during preflight
4. Certification is explicit (user action) not automatic
5. All references recorded in manifests for provenance

### References

**Primary source documents:**
- [synthetic-data-decision-document-2026-03-23.md](/Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/synthetic-data-decision-document-2026-03-23.md) — Sections on train/test leakage prevention
- [epic-21-trust-governed-open-synthetic-evidence-foundation.md](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/epic-21-trust-governed-open-synthetic-evidence-foundation.md) — Story 21.5 notes
- [Story 21.1](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/21-1-implement-canonical-evidence-asset-descriptor-and-current-phase-source-matrix.md) — DataAssetDescriptor pattern
- [Story 21.3](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/21-3-implement-typed-structural-exogenous-calibration-and-validation-asset-schemas.md) — StructuralAsset type

**Code patterns to follow:**
- [src/reformlab/data/assets.py](/Users/lucas/Workspace/reformlab/src/reformlab/data/assets.py) — StructuralAsset factory pattern
- [src/reformlab/server/validation.py](/Users/lucas/Workspace/reformlab/src/reformlab/server/validation.py) — PreflightCheck protocol (from Story 20.5)
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
- Uses `StructuralAsset` from Story 21.3 as base type
- Adds `CalibrationAsset` with `is_in_sample`, `holdout_group` fields
- Adds `ValidationAsset` with `validation_dossier_required`, `certified_at` fields
- Creates `TrustStatusRule` protocol for governance rules
- Implements three built-in rules: SyntheticWithoutValidationDossierRule, CalibrationDataNotValidationRule, SyntheticOutputUpgradeRule
- Extends validation/preflight check system from Story 20.5 with trust-status rules
- Separate API endpoints: `/api/calibration/targets` and `/api/validation/benchmarks`
- Certification endpoint upgrades trust status for synthetic assets with validation dossier
- Calibration engine updated to use CalibrationAsset and record provenance
- Frontend displays calibration/validation distinction with trust badges
- Storage separation: `data/calibration/targets/` and `data/validation/benchmarks/`
- Prevents train/test leakage via semantic separation and governance rules

### File List

**Files to create:**
- `src/reformlab/governance/__init__.py` — Governance subsystem package
- `src/reformlab/governance/trust_rules.py` — TrustStatusRule protocol and implementations
- `src/reformlab/governance/registry.py` — TrustRuleRegistry class
- `src/reformlab/server/routes/calibration.py` — Calibration target API endpoints
- `src/reformlab/server/routes/validation.py` — Validation benchmark API endpoints
- `frontend/src/api/calibration.ts` — Calibration API client
- `frontend/src/api/validation.ts` — Validation API client
- `data/calibration/targets/{asset-id}/data.parquet` — Example calibration targets
- `data/calibration/targets/{asset-id}/descriptor.json`
- `data/calibration/targets/{asset-id}/metadata.json`
- `data/validation/benchmarks/{asset-id}/data.parquet` — Example validation benchmarks
- `data/validation/benchmarks/{asset-id}/descriptor.json`
- `data/validation/benchmarks/{asset-id}/metadata.json`

**Files to modify:**
- `src/reformlab/data/assets.py` — Add CalibrationAsset, ValidationAsset, load functions
- `src/reformlab/server/validation.py` — Extend preflight system with trust-status rules
- `src/reformlab/server/models.py` — Add API response models
- `src/reformlab/server/routes/__init__.py` — Include new routers
- `src/reformlab/calibration/engine.py` — Use CalibrationAsset for target loading
- `frontend/src/api/types.ts` — Add TypeScript types
- `frontend/src/components/engine/EngineValidationScreen.tsx` — Display calibration/validation distinction

**Tests to create:**
- `tests/governage/test_trust_rules.py` — Rule execution tests
- `tests/governance/test_registry.py` — Registry tests
- `tests/server/test_routes_calibration.py` — Calibration API tests
- `tests/server/test_routes_validation.py` — Validation API tests
- `tests/calibration/test_engine_integration.py` — Calibration engine integration tests
- `frontend/src/api/__tests__/calibration.test.ts` — Calibration API client tests
- `frontend/src/api/__tests__/validation.test.ts` — Validation API client tests
