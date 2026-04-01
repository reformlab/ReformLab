# Epic 23 - Story Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during validation of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent story-writing mistakes (unclear AC, missing Notes, unrealistic scope).

## Story 23-1 (2026-04-01)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | ScenarioConfig ownership violation | Changed task from "Add `runtime_mode` to `ScenarioConfig` and `RunConfig`" to "Add `runtime_mode` to `RunConfig` only (NOT ScenarioConfig — architecture §5.9 assigns runtime_mode to Run, not Scenario)". Also updated the Source Tree Components table. The architecture document explicitly states that `Scenario` owns `simulation_mode` while `Run` and its manifest own `runtime_mode`. Adding `runtime_mode` to `ScenarioConfig` would violate this boundary. |
| high | Frontend `runtime_mode` should be optional | Changed frontend `RunRequest` task from `runtime_mode: "live" \| "replay"` to `runtime_mode?: "live" \| "replay"` (optional). If the frontend always sends `runtime_mode` explicitly, it defeats the backend's default-live semantics. The frontend should omit the field for standard runs, letting the backend default apply. |
| medium | Migration/backward-compat policy underspecified | Expanded the Migration Compatibility section with explicit guidance: `runtime_mode` goes in `OPTIONAL_JSON_FIELDS` (not `REQUIRED_JSON_FIELDS`), `from_json()` uses `data.get("runtime_mode", "live")`, `_dict_to_metadata()` needs a fallback, `_make_minimal_manifest()` needs the field, and `from_json()` must validate values if present. |
| medium | Invalid `runtime_mode` value validation missing | Added `test_manifest_from_json_with_invalid_runtime_mode_raises()` to migration tests. Added explicit requirement in Migration Compatibility notes that `from_json()` must validate values and raise `ManifestValidationError` for invalid ones. |
| medium | Replay trigger scope ambiguity | Added Non-Goals section explicitly stating replay invocation mechanism, live execution engine, orchestrator changes, and frontend UI are all out of scope for this story. |
| medium | Misleading `type: ignore` patterns in code examples | Removed `# type: ignore[valid-type]` comments from all code examples (RunManifest snippet and test code examples). Changed RunManifest field type from `RuntimeMode = "live"` with type ignore to `str = "live"` with inline comment, matching the actual codebase pattern for frozen dataclass fields. |
| low | Duplicate file list | Consolidated the "File List" section at the bottom to a single pointer to the Source Tree Components table, eliminating ~200 tokens of duplication. |
| low | Missing round-trip persistence test | Added `test_legacy_load_then_save_preserves_runtime_mode()` to migration tests. |
| dismissed | Missing test for runtime_mode null/empty/wrong-type during deserialization | FALSE POSITIVE: Over-engineering for a field that doesn't exist yet. The manifest's `from_json()` handles missing fields via `data.get()` with defaults. Null and wrong-type are Python JSON parsing edge cases that the existing validation framework handles generically. Adding parametrized tests for null/""/123 is yak-shaving. |
| dismissed | Missing migration test for pre-existing invalid runtime_mode | FALSE POSITIVE: `runtime_mode` doesn't exist in any manifest yet. There cannot be "pre-existing invalid values" for a field that hasn't been added. This is a theoretical scenario with zero production instances. |
| dismissed | Performance/SLA requirement for batch migration (100K manifests in 60s) | FALSE POSITIVE: No batch migration process exists. This story adds a single optional field with a default. Each manifest is loaded individually on demand. There is no migration script to optimize. |
| dismissed | Rollback strategy needed | FALSE POSITIVE: Adding an optional field with a default value is inherently safe. If it causes issues, removing the field from the code is the rollback. No feature flag needed. |
| dismissed | 5 SP estimate is too low, should be 8 SP | FALSE POSITIVE: Cross-referenced with actual codebase. The story adds one Literal type, updates ~7 backend files with single-field additions, updates 1 frontend file, and adds tests. The existing `exogenous_series` field addition (Story 21.6) was similar scope. 5 SP is appropriate. |
| dismissed | RuntimeMode should be in server/interfaces, not computation/types | FALSE POSITIVE: `computation/types.py` already contains shared computation types (`PopulationData`, `PolicyConfig`, `ComputationResult`). Adding `RuntimeMode` here is consistent. The alternative (server/ layer) would create a circular dependency since the manifest module needs this type and is in governance/, not server/. |
| dismissed | Replay eligibility/authorization rules needed | FALSE POSITIVE: Out of scope. This story defines the type contract only. Replay authorization is Story 23.4's concern. |
| dismissed | OpenAPI snapshot test needed | FALSE POSITIVE: Nice to have but not blocking. The typed contracts (Pydantic + TypeScript) are the primary validation. |
| dismissed | Encode runtime_mode in run_id string prefix | FALSE POSITIVE: Over-engineering. Run IDs are UUIDs. The runtime_mode is in metadata/manifests where it belongs. |
| dismissed | Add runtime_mode to distributed tracing spans | FALSE POSITIVE: No distributed tracing infrastructure exists. Out of scope. |
| dismissed | Unclear error contract for invalid runtime_mode (exact 422 body) | FALSE POSITIVE: Pydantic handles Literal validation automatically. The existing `{"what", "why", "fix"}` error pattern in the project context covers this. Specifying exact error text for Pydantic's built-in validation is over-constraining. |
| dismissed | AC-5 is subjective and untestable | FALSE POSITIVE: AC-5 is a negative constraint ("no new frontend runtime selector"). It's verifiable by checking that no new UI component was added. The story's tasks explicitly exclude frontend screen modifications. This is adequate. |
| dismissed | Need end-to-end propagation integration test | FALSE POSITIVE: The story scope is contract definition, not execution flow. E2E propagation tests belong in later stories (23.2-23.3) when the live execution path is actually wired up. |
| dismissed | Result list/comparison/export consumers need regression tests | FALSE POSITIVE: Adding an optional field to response models doesn't break existing consumers. TypeScript and Pydantic handle extra fields gracefully. No regression risk. |
