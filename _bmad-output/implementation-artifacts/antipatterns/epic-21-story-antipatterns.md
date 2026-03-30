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

## Story 21-8 (2026-03-30)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | AC4 error-path testing lacks concrete error response specification | Added clarification: "error responses follow project `{"what", "why", "fix"}` format from PROJECT_CONTEXT.md" |
| medium | AC5 RunManifest evidence field format underspecified | Clarified that dict[str, Any] fields store to_json() outputs and explained omit-empty for storage vs consistent structure for hashing |
| medium | AC7 trust labels requirement unclear on backend vs frontend responsibility | Scoped to backend field only: "Backend response includes `trust_warnings: list[str]` field in RunResponse... (frontend display of warnings is future work)" |
| medium | AC8 documentation coherence too qualitative | Converted to concrete checklist with 6 specific verifiable items |
| medium | Task 1 missing discovery step | Added "Read existing `examples/workflows/carbon_tax_analysis.yaml` to understand current structure" |
| medium | Task 2 missing discovery step and output location clarity | Added discovery step and specified "Write `evidence_manifest.json` to same output directory as population CSV" |
| medium | Task 4 smoke tests lack verification step specifications | Added specific assertion for each test (e.g., "assert each population has 'origin', 'access_mode', 'trust_status'") |
| medium | Task 6 test classes lack implementation guidance | Added key assertions for each test class |
| low | Dev Notes overly verbose with redundant information | Streamlined Architecture Context from verbose table to concise summary; streamlined Testing Patterns from verbose code example to concise description |
| dismissed | Missing dependency gate for Story 21.5 - story assumes incomplete prerequisites | FALSE POSITIVE: **FALSE POSITIVE**. Story's "Integration with Previous Stories" section explicitly states Stories 21.1-21.7 are "done". Verified against sprint-status.yaml: all prerequisite stories (21.1-21.7) show status "done" as of 2026-03-30. |
| dismissed | Oversized multi-story scope - combines too much work for one story | FALSE POSITIVE: **FALSE POSITIVE**. This is an end-of-epic integration story with 10 ACs and 9 tasks across 4 domains. Appropriate scope for demonstrating evidence model integration across product. INVEST "Small" criterion allows for 3-5 SP stories; this is typical for epic integration. |
| dismissed | RunManifest evidence contract is non-deterministic (list[dict] + omit-empty + hash inclusion) | FALSE POSITIVE: **PARTIAL but not blocking**. JSON normalization for storage with omit-empty is standard practice. The internal representation for hashing uses consistent structure. Applied clarification to AC5 addresses this concern. |
| dismissed | AC7 UI outcomes cannot be reliably implemented from current tasks | FALSE POSITIVE: **VALID concern addressed**. Applied fix scoped AC7 to backend field only; frontend display clarified as future work. |
| dismissed | README links to internal planning artifact path (`_bmad-output/...`) not suitable for user-facing docs | FALSE POSITIVE: **FALSE POSITIVE**. The evidence source matrix document is both a planning artifact AND the authoritative reference for asset metadata. This is appropriate for a story in active development. |
| dismissed | "Real API endpoints where available" is ambiguous and weakens test rigor | FALSE POSITIVE: **FALSE POSITIVE**. This provides appropriate flexibility for test design based on endpoint availability. The Task 6 clarification added key assertion guidance to maintain rigor. |
| dismissed | Story file references non-existent Story 20.8 path | FALSE POSITIVE: **FALSE POSITIVE**. Story 20.8 file exists at correct path. Validator's claim was incorrect. |
