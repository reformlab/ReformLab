# Epic 21 - Story Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during validation of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent story-writing mistakes (unclear AC, missing Notes, unrealistic scope).

## Story 21-5 (2026-03-27)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Asset type conflict with Story 21.3 | Changed AC1 and Task 1 to extend existing CalibrationAsset/ValidationAsset rather than create new types; removed inheritance from StructuralAsset, clarified envelope pattern (DataAssetDescriptor composition) |
| critical | Wrong inheritance pattern specified | Removed all references to inheriting from StructuralAsset; updated to use envelope pattern consistently throughout story |
| critical | Wrong story reference for preflight (20.5 vs 20.7) | Changed all references from "Story 20.5" to "Story 20.7" in AC5, Dev Notes, Completion Notes |
| critical | Wrong file reference for preflight extension | Changed Task 4 from `server/validation.py` to `server/routes/validation.py`; updated Dev Notes "Files to modify" |
| critical | TrustStatusRule protocol signature insufficient | Changed AC3 from `check(asset: StructuralAsset)` to `check(descriptor: DataAssetDescriptor, metadata: dict[str, Any])` to access calibration/validation-specific fields |
| critical | Rule descriptions misaligned with asset model | Rewrote AC4 rules to check `data_class` values and existing ValidationAsset fields rather than non-existent fields |
| critical | Certification requirements undefined | Added certification requirements checklist to Task 8 and Dev Notes; specified error codes (403, 422) and specific error messages |
| critical | Test path typo | Fixed `tests/governage/test_trust_rules.py` to `tests/governance/test_trust_rules.py` in File List |
| critical | Manifest field path undefined | Specified `manifest.calibration.asset_id` in AC8 and Task 9 |
| critical | Field value constraints missing | Added Literal type definitions for HoldoutGroup, CalibrationMethod, ValidationMethod in Task 1 and Type System Constraints |
| high | API error response format not specified | Added "API Error Response Format" section to Dev Notes with ErrorResponse what/why/fix pattern |
| high | Storage format underspecified | Added "Storage Format Specification" section with folder structure and metadata.json schemas |
| high | Field formats missing | Specified ISO 8601 format for `certified_at`, actor identity description for `certified_by` in AC2 |
| high | Frontend component reference may not exist | Changed AC9 and Task 10 from specific component reference to general "calibration configuration UI" |
| high | Preflight integration pattern undefined | Added example ValidationCheck wrapper pattern to "Existing Code Patterns to Reference" section |
| high | Test requirements vague | Enhanced AC10 and Task 12 with specific test scenarios (rule outcomes, error formats, status transitions) |
| high | Scenario binding for preflight missing | Updated AC7 to reference "scenario-selected" assets; clarified asset selection in preflight context |
| medium | API response models not specified | Updated Task 11 to specify response model contents (all descriptor fields, asset-specific fields, trust-status/certification fields) |
| low | Rule evaluation precedence unspecified | Note: Existing ValidationCheck pattern handles rule execution order; no additional specification needed |
| low | Storage location not verified against existing calibration data | Note: Task 5 creates new asset storage separate from existing calibration target files; this is intentional migration |
