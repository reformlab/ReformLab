# Epic 15 - Story Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during validation of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent story-writing mistakes (unclear AC, missing Notes, unrealistic scope).

## Story 15-1 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | `source_metadata` declared required in dataclass (Task 2.1) but optional in JSON Schema (Task 3.2), and absent from CSV schema entirely — contract conflict that allows divergent implementations | Made `source_metadata` optional with `field(default_factory=dict)` in Task 2.1; JSON Schema task already had it optional (no change needed there); the dataclass now matches the schema |
| critical | AC-2 says "CSV or YAML" but Task 4.4 explicitly includes `.parquet` extension → format scope conflict | Updated AC-2 to "CSV, Parquet, or YAML"; added `TestParquetLoading` to test task 6.3; added `valid_vehicle_targets.parquet` fixture |
| high | AC-4 error location "field and row" is unambiguous for CSV but maps to nothing in YAML (no row numbers in YAML) — makes AC-4 objectively untestable across formats | AC-4 now specifies `row=N` for CSV/Parquet and `targets[N].field_name` for YAML; Task 4.7 defines the error message format with example |
| high | JSON Schema loaded from `src/reformlab/calibration/schema/` will be missing in installed wheel without explicit packaging configuration | Task 4.3 now specifies `importlib.resources.files()` loading; Project Structure Notes specify `schema/__init__.py` requirement and `pyproject.toml` include pattern; `schema/__init__.py` added to File List |
| medium | `sum ≤ 1.0` consistency check has no floating-point tolerance — boundary values (e.g., `0.1 + 0.1 + 0.8`) can fail due to binary float accumulation | Task 2.4 adds `1e-9` tolerance; Consistency Validation Rule section documents boundary test cases |
| medium | Duplicate `(domain, period, from_state, to_state)` row behavior unspecified — double-counting would silently inflate probability sums | Task 2.4 and Consistency Validation Rule section now specify: duplicates are always a `CalibrationTargetLoadError`, not a validation error |
| medium | JSON Schema type for `source_metadata` was unspecified — allows any object type | Task 3.2 now types `source_metadata` as `{type: object, additionalProperties: {type: string}}` |
