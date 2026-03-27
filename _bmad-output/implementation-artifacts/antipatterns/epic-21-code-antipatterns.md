# Epic 21 - Code Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during code review of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent implementation mistakes (race conditions, missing tests, weak assertions, etc.)

## Story 21-2 (2026-03-27)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Frontend drops canonical evidence fields in `toLibraryItem` function | Changed `toLibraryItem` to pass through all `PopulationLibraryItem` fields instead of dropping them and hardcoding values |
| critical | Frontend upload component omits canonical fields | Added `canonical_origin`, `access_mode`, `trust_status` fields to uploaded population item with appropriate defaults |
| critical | Generated population item omits canonical fields | Added canonical evidence fields to data fusion result population item |
| critical | Upload endpoint unbounded memory read (DoS risk) | Changed from `file.file.read()` to chunked streaming with 100 MB size limit, returns HTTP 413 for oversized files |
| high | Metadata values trusted without validation | Added validation of canonical evidence fields against Literal types before using metadata values, with fallback to mapping function and warning log on invalid values |
| high | Provider evidence mapping fails open to INSEE defaults | Changed from silent fallback to fail-fast HTTPException 422 for unknown providers |
| high | DataSourceItem has default values for Literal types | Removed default values for `origin`, `access_mode`, `trust_status` fields (now required) |
| medium | No CHANGELOG.md entry for API changes | Deferred — CHANGELOG.md does not exist in project; this is a project-level documentation decision |
| dismissed | Task 7 claim "test_populations_evidence.py doesn't exist" | FALSE POSITIVE: File exists at `tests/server/test_models_evidence.py` with 11 passing tests |
| dismissed | Nav rail summary missing trust status display | FALSE POSITIVE: Nav rail correctly shows population name; trust badges are in PopulationLibraryScreen cards which is the appropriate location per UI design (PopulationLibraryScreen.tsx lines 44-63, 104-108) |
| dismissed | AC10 test coverage incomplete | FALSE POSITIVE: Tests cover dual-field model validation, mapping, error handling in test_models_evidence.py; API responses tested in test_populations_api.py |
| dismissed | Frontend/backend type contracts diverge | FALSE POSITIVE: TypeScript interface correctly narrows Literal types to values actually used by current providers (`open-official`, `synthetic-public`); this maintains type safety and prevents invalid values |
| dismissed | File extension validation spoofable | FALSE POSITIVE: Extension validation is appropriate for current threat model; file content validation would be a separate enhancement |
| dismissed | Redundant mapping function | FALSE POSITIVE: Mapping function documents the intentional design choice that all current populations map to the same evidence classification (`synthetic-public`/`bundled`/`exploratory`) |
