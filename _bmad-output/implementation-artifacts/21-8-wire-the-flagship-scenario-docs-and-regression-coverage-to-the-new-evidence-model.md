# Story 21.8: Wire the Flagship Scenario, Docs, and Regression Coverage to the New Evidence Model

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

**As a** policy analyst and platform developer using the ReformLab workspace,
**I want** the flagship carbon tax scenario, product documentation, and regression tests to all demonstrate the new evidence model (open official data, public synthetic comparison, explicit trust labels, and separated calibration/validation),
**so that** I can see end-to-end how evidence governance works in practice and trust that the evidence model is consistently applied across the product.

## Acceptance Criteria

1. **AC1:** Flagship carbon tax scenario (`examples/workflows/carbon_tax_analysis.yaml`) updated with evidence metadata:
   - All data sources reference `asset_id` from the evidence source matrix
   - Population source includes `origin: synthetic-public`, `access_mode: bundled`, `trust_status: exploratory`
   - Emission factors include `origin: open-official`, `provider: ademe`, `trust_status: production-safe`
   - Calibration targets (if any) reference validation vs calibration distinction
   - Demo manifest includes evidence governance entries (see AC5)

2. **AC2:** `french_household_pipeline.py` demo updated to export evidence metadata:
   - `PopulationValidator` results include `DataAssetDescriptor` for each source
   - Output summary file lists all sources with evidence classification
   - Pipeline produces `evidence_manifest.json` alongside population CSV
   - Evidence manifest includes: asset_id, origin, access_mode, trust_status, data_class for each source

3. **AC3:** README updated to describe the evidence model:
   - Add "Evidence Model" section explaining origin/access_mode/trust_status
   - Link to evidence source matrix document
   - Distinguish between open official and synthetic data
   - Explain current-phase scope (open + synthetic, restricted deferred)
   - Update "Live services" section if any services reference restricted data

4. **AC4:** API smoke test (`examples/api/api_smoke_test.py`) verifies evidence contracts:
   - Population listing endpoint returns origin/access_mode/trust_status for each population
   - Engine validation includes evidence-specific preflight checks (from Story 21.5)
   - Result endpoints include evidence metadata in response
   - Tests verify 403/422 error responses for trust-status violations

5. **AC5:** RunManifest includes evidence governance fields:
   - `evidence_assets: list[DataAssetDescriptor]` field added to manifest schema
   - `calibration_assets: list[CalibrationAsset]` field for calibration data
   - `validation_assets: list[ValidationAsset]` field for validation data
   - `evidence_summary: dict[str, Any]` field with high-level evidence provenance
   - All evidence fields included in integrity hash computation
   - Manifest serialization excludes empty evidence lists (omit if none)

6. **AC6:** End-to-end regression tests extend EPIC-20 coverage (do NOT duplicate):
   - New `tests/regression/test_evidence_model.py` test class added
   - Test: "Synthetic population loading includes correct evidence metadata"
   - Test: "Calibration with synthetic data vs observed comparison flow"
   - Test: "Trust-status rules enforced in engine validation preflight"
   - Test: "Calibration targets and validation benchmarks remain distinct"
   - Test: "Evidence manifest entries populate in run results"
   - All tests use real API endpoints (not mocks) where available

7. **AC7:** Flagship scenario demonstrates synthetic vs observed comparison:
   - Scenario includes both synthetic population and open-official calibration targets
   - Results view shows explicit trust labels (e.g., "Exploratory synthetic", "Production-safe official")
   - Comparison between synthetic-only and official-data scenarios is possible
   - Warnings displayed when using exploratory data for decision support

8. **AC8:** Documentation coherence across docs, demos, and tests:
   - README, evidence source matrix, and demo pipeline all use same terminology
   - API documentation (if generated) includes evidence field descriptions
   - Run comments and logging reference evidence model consistently
   - No outdated references to "microdata access" as primary value proposition

9. **AC9:** Regression tests verify taste parameter evidence governance (Story 21.7):
   - Test: "TasteParameters governance entry includes literature_sources"
   - Test: "CalibrationResult diagnostics populate in manifest"
   - Test: "ExogenousContext provenance tracked in scenario comparison"
   - Test: "Vehicle ASCs and betas recorded with calibration status"

10. **AC10:** All governance integration tests pass with evidence model:
    - Existing `tests/governance/test_manifest.py` tests pass with evidence fields
    - Existing `tests/calibration/test_governance.py` tests pass with calibration assets
    - Existing `tests/discrete_choice/test_decision_record.py` tests pass with taste parameters
    - No regressions in existing test coverage

## Tasks / Subtasks

- [ ] **Task 1: Update flagship scenario YAML with evidence metadata** (AC: 1)
  - [ ] Add `evidence_metadata` section to `examples/workflows/carbon_tax_analysis.yaml`
  - [ ] Reference population asset: `fr-synthetic-2024` with `origin: synthetic-public`, `access_mode: bundled`, `trust_status: exploratory`
  - [ ] Reference emission factors: `ademe-carbon-factors-2024` with `origin: open-official`, `access_mode: bundled`, `trust_status: production-safe`
  - [ ] Add optional calibration targets if applicable (EV adoption rates from ADEME)
  - [ ] Include comment linking to evidence source matrix document

- [ ] **Task 2: Update french_household_pipeline.py with evidence export** (AC: 2)
  - [ ] Import `DataAssetDescriptor` from `reformlab.data.descriptor`
  - [ ] Create descriptors for each source (INSEE, Eurostat, SDES, ADEME)
  - [ ] Set appropriate origin/access_mode/trust_status for each source
  - [ ] Write `evidence_manifest.json` alongside population CSV
  - [ ] Include `DataAssetDescriptor.to_json()` output in evidence manifest
  - [ ] Update summary file to list evidence classification per source

- [ ] **Task 3: Update README with evidence model section** (AC: 3, 8)
  - [ ] Add "Evidence Model" section after "Features"
  - [ ] Explain four data classes: structural, exogenous, calibration, validation
  - [ ] Explain classification axes: origin, access_mode, trust_status
  - [ ] Link to `_bmad-output/planning-artifacts/evidence-source-matrix-v1-2026-03-27.md`
  - [ ] Clarify current-phase scope (open + synthetic, restricted deferred)
  - [ ] Review all README sections for outdated "microdata access" language
  - [ ] Update architecture diagram if it references evidence flows

- [ ] **Task 4: Update API smoke test with evidence verification** (AC: 4)
  - [ ] Add test for population listing response includes evidence fields
  - [ ] Add test for engine validation includes trust-status checks
  - [ ] Add test for result endpoints include evidence metadata
  - [ ] Add test for 403 error response on trust-status violation
  - [ ] Add test for 422 error response on evidence validation failure

- [ ] **Task 5: Extend RunManifest schema with evidence fields** (AC: 5)
  - [ ] Add `evidence_assets: list[dict[str, Any]] = field(default_factory=list)` to `RunManifest` in `src/reformlab/governance/manifest.py`
  - [ ] Add `calibration_assets: list[dict[str, Any]] = field(default_factory=list)`
  - [ ] Add `validation_assets: list[dict[str, Any]] = field(default_factory=list)`
  - [ ] Add `evidence_summary: dict[str, Any] = field(default_factory=dict)`
  - [ ] Update `OPTIONAL_JSON_FIELDS` tuple to include new fields
  - [ ] Update `to_json()` to omit empty evidence lists
  - [ ] Update `from_json()` to handle optional evidence fields
  - [ ] Ensure evidence fields included in integrity hash computation

- [ ] **Task 6: Create evidence model regression tests** (AC: 6, 9, 10)
  - [ ] Create `tests/regression/test_evidence_model.py` (file may not exist yet)
  - [ ] Add test class `TestEvidenceMetadataInPopulationListing`
  - [ ] Add test class `TestTrustStatusRulesInEngineValidation`
  - [ ] Add test class `TestCalibrationValidationSeparation`
  - [ ] Add test class `TestSyntheticVsObservedComparison`
  - [ ] Add test class `TestTasteParameterGovernanceIntegration`
  - [ ] Add test class `TestEvidenceManifestPopulation`
  - [ ] Use real API endpoints via `pytest` fixtures
  - [ ] Ensure all tests can run in parallel and are deterministic

- [ ] **Task 7: Implement synthetic vs observed comparison in flagship** (AC: 7)
  - [ ] Add scenario variant using open-official calibration targets
  - [ ] Ensure both scenarios can be loaded and executed
  - [ ] Verify results show correct trust labels in metadata
  - [ ] Add warning display when exploratory data used for decision support
  - [ ] Test comparison workflow between synthetic-only and official-data scenarios

- [ ] **Task 8: Verify documentation coherence** (AC: 8)
  - [ ] Review README for evidence model terminology consistency
  - [ ] Review evidence source matrix for completeness vs demos
  - [ ] Review demo pipeline output matches evidence model description
  - [ ] Review code comments for evidence model references
  - [ ] Check API docstrings (if generated) include evidence fields

- [ ] **Task 9: Run full regression suite and verify no regressions** (AC: 10)
  - [ ] Run `uv run pytest tests/governance/test_manifest.py` and verify passing
  - [ ] Run `uv run pytest tests/calibration/test_governance.py` and verify passing
  - [ ] Run `uv run pytest tests/discrete_choice/test_decision_record.py` and verify passing
  - [ ] Run `uv run pytest tests/regression/test_evidence_model.py` and verify passing
  - [ ] Run `uv run pytest tests/` (full suite) and verify no regressions
  - [ ] Document any test changes required for evidence model compatibility

## Dev Notes

### Architecture Context

**Evidence Model Summary (from Epic 21 stories 21.1-21.7):**

The evidence model classifies all data and model inputs into four categories with explicit governance:

| Data Class | Role | Example Assets |
|------------|------|----------------|
| **Structural** | Define who/what is modeled | `fr-synthetic-2024`, `insee-fideli-2021` |
| **Exogenous** | Context inputs to simulation | `energy-price-elec-fr`, `carbon-tax-rate-fr` |
| **Calibration** | Fit model to observed reality | `ev-adoption-fr`, `household-energy-consumption` |
| **Validation** | Test model against independent observations | `household-survey-fr`, `transport-mode-shares` |

Each asset carries classification metadata:
- **origin**: `open-official`, `synthetic-public` (current phase); `synthetic-internal`, `restricted` (future)
- **access_mode**: `bundled`, `fetched` (current phase); `deferred-user-connector` (future)
- **trust_status**: `production-safe`, `exploratory`, `demo-only`, `validation-pending`, `not-for-public-inference`
- **data_class**: `structural`, `exogenous`, `calibration`, `validation`

**Key Design Constraints:**
1. Current phase is **open official + synthetic only** — restricted connectors deferred
2. Calibration and validation data must remain **distinct concepts** (Story 21.5)
3. Taste parameters have separate provenance (literature sources, calibration diagnostics) — Story 21.7
4. All evidence must be **explicitly labelled** — no implicit trust assumptions

### Project Structure Notes

**Files to modify:**

**Documentation:**
- `README.md` — Add evidence model section, update feature descriptions
- `_bmad-output/planning-artifacts/evidence-source-matrix-v1-2026-03-27.md` — Reference for all asset metadata

**Demos:**
- `examples/workflows/carbon_tax_analysis.yaml` — Add evidence metadata section
- `examples/populations/french_household_pipeline.py` — Export evidence manifest

**Tests:**
- `tests/regression/test_evidence_model.py` — New file for evidence-specific regression tests
- `tests/governance/test_manifest.py` — Extend tests for evidence fields
- `examples/api/api_smoke_test.py` — Add evidence contract verification tests

**Backend (if needed for evidence export):**
- `src/reformlab/governance/manifest.py` — Add evidence fields to RunManifest

### Integration with Previous Stories

**Story 21.1** (done): `DataAssetDescriptor` type and evidence source matrix created
- Use `DataAssetDescriptor.from_json()` to load asset metadata
- Reference asset IDs from evidence source matrix

**Story 21.2** (done): API contracts include origin/access_mode/trust_status
- Population listing response includes evidence fields
- Engine validation includes trust-status checks

**Story 21.3** (done): Typed schemas for structural, exogenous, calibration, validation assets
- Use appropriate asset type (StructuralAsset, ExogenousAsset, etc.)

**Story 21.5** (done): Calibration/validation separation and trust-status rules
- Calibration targets and validation benchmarks are stored separately
- Trust-status rules enforced as preflight checks

**Story 21.6** (done): `ExogenousContext` for scenario-specific exogenous inputs
- Exogenous series provenance tracked in scenarios
- Scenario comparison includes exogenous assumption differences

**Story 21.7** (done): Generalized `TasteParameters` with governance entries
- Taste parameters include literature_sources and calibration diagnostics
- Manifest includes taste_parameters field

**EPIC-20 Story 20.8** (done): End-to-end regression test framework
- Extend with evidence-specific tests (do NOT duplicate existing flows)
- Add evidence metadata verification to existing flows

### Evidence Manifest Format

The `evidence_manifest.json` exported by the pipeline should have this structure:

```json
{
  "format_version": "1.0",
  "generated_at": "2026-03-30T10:00:00Z",
  "pipeline_name": "french_household_example",
  "evidence_assets": [
    {
      "asset_id": "insee-fideli-2021",
      "name": "Fidéli (Données de cadrage)",
      "description": "French demographic data sources",
      "data_class": "structural",
      "origin": "open-official",
      "access_mode": "bundled",
      "trust_status": "production-safe",
      "provider": "insee",
      "license": "Open License",
      "redistribution_allowed": true
    },
    {
      "asset_id": "reformlab-fr-synthetic-2024",
      "name": "French Synthetic Population 2024",
      "description": "100k synthetic households for demo/exploratory",
      "data_class": "structural",
      "origin": "synthetic-public",
      "access_mode": "bundled",
      "trust_status": "exploratory",
      "provider": "reformlab",
      "license": "CC-BY-4.0",
      "redistribution_allowed": true
    }
  ],
  "calibration_assets": [],
  "validation_assets": [],
  "assumptions": []
}
```

### Testing Patterns

**Evidence Model Regression Test Structure:**

```python
# tests/regression/test_evidence_model.py

class TestEvidenceMetadataInPopulationListing:
    """AC6, AC4: Verify population listing includes evidence metadata."""

    def test_population_response_includes_evidence_fields(self):
        """Given GET /populations, when response received,
        then each population has origin/access_mode/trust_status."""
        response = client.get("/api/populations")
        assert response.status_code == 200
        for pop in response.json()["populations"]:
            assert "origin" in pop
            assert "access_mode" in pop
            assert "trust_status" in pop

class TestTrustStatusRulesInEngineValidation:
    """AC6, AC5: Verify trust-status rules enforced in engine validation."""

    def test_exploratory_data_warning_in_validation(self):
        """Given exploratory population and official calibration targets,
        when validating engine, then warning displayed but validation passes."""
        # Test implementation

class TestCalibrationValidationSeparation:
    """AC6, AC9: Verify calibration and validation remain distinct."""

    def test_calibration_targets_not_used_as_validation(self):
        """Given calibration targets registered,
        when computing validation metrics,
        then calibration data excluded from validation dataset."""
        # Test implementation
```

### References

- **Evidence source matrix**: `_bmad-output/planning-artifacts/evidence-source-matrix-v1-2026-03-27.md`
- **Synthetic data decision document**: `_bmad-output/planning-artifacts/synthetic-data-decision-document-2026-03-23.md`
- **Epic 21**: `_bmad-output/implementation-artifacts/epic-21-trust-governed-open-synthetic-evidence-foundation.md`
- **Story 21.1**: `_bmad-output/implementation-artifacts/21-1-implement-canonical-evidence-asset-descriptor.md`
- **Story 21.5**: `_bmad-output/implementation-artifacts/21-5-separate-calibration-targets-from-validation-benchmarks.md`
- **Story 21.7**: `_bmad-output/implementation-artifacts/21-7-refactor-discrete-choice-and-calibration-for-generalized-tasteparameters.md`
- **Story 20.8**: `_bmad-output/implementation-artifacts/20-8-add-end-to-end-regression-coverage-and-sync-product-docs.md`

## Dev Agent Record

### Agent Model Used

claude-opus-4-6

### Debug Log References

None (story creation)

### Completion Notes List

ULTIMATE CONTEXT ENGINE ANALYSIS COMPLETED - Comprehensive developer guide created

**Context extraction completed from:**
- Epic 21 story definition and notes
- Evidence source matrix v1 (current-phase datasets)
- Synthetic data decision document (evidence taxonomy)
- Story 21.1 (DataAssetDescriptor implementation)
- Story 21.5 (calibration/validation separation)
- Story 21.7 (TasteParameters governance integration)
- Story 20.8 (end-to-end regression test framework)
- Example workflows and pipelines (flagship scenario patterns)
- README and documentation structure

**Key developer guardrails provided:**
- Complete evidence model taxonomy (4 data classes with classification axes)
- Current-phase scope boundaries (open + synthetic only, restricted deferred)
- Evidence manifest format for pipeline export
- Integration points with all previous Epic 21 stories
- Testing patterns for evidence-specific regression tests
- Documentation coherence requirements across README, demos, and code

**Story ready-for-dev with comprehensive acceptance criteria covering:**
1. Flagship scenario evidence metadata
2. Demo pipeline evidence export
3. README evidence model section
4. API smoke test evidence verification
5. RunManifest evidence fields
6. Evidence model regression tests (extending EPIC-20)
7. Synthetic vs observed comparison demonstration
8. Documentation coherence verification
9. Taste parameter governance integration
10. All governance integration tests passing

### File List

**New files to create:**
- `tests/regression/test_evidence_model.py` — Evidence-specific regression tests

**Files to modify:**
- `README.md` — Add evidence model section
- `examples/workflows/carbon_tax_analysis.yaml` — Add evidence metadata
- `examples/populations/french_household_pipeline.py` — Export evidence manifest
- `examples/api/api_smoke_test.py` — Add evidence contract tests
- `src/reformlab/governance/manifest.py` — Add evidence fields to RunManifest

**Reference files (read-only):**
- `_bmad-output/planning-artifacts/evidence-source-matrix-v1-2026-03-27.md`
- `_bmad-output/implementation-artifacts/epic-21-trust-governed-open-synthetic-evidence-foundation.md`
- `_bmad-output/implementation-artifacts/21-5-separate-calibration-targets-from-validation-benchmarks.md`
- `_bmad-output/implementation-artifacts/21-7-refactor-discrete-choice-and-calibration-for-generalized-tasteparameters.md`
- `_bmad-output/implementation-artifacts/20-8-add-end-to-end-regression-coverage-and-sync-product-docs-to-the-new-ia.md`
