# Epic 26 - Code Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during code review of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent implementation mistakes (race conditions, missing tests, weak assertions, etc.)

## Story 26-5 (2026-04-22)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Frontend column_count mismatch (8 vs 7 actual) | Changed `column_count: 8` to `column_count: 7` to match actual parquet schema (household_id, person_id, age, income, energy_transport_fuel, energy_heating_fuel, energy_natural_gas) |
| high | Silent exception swallowing hides errors | Replaced bare `except Exception: pass` with specific exception types (OSError, pa.ArrowInvalid, pa.ArrowNotImplementedError, IndexError) and debug logging |
| high | Descriptor fields not validated against literal types | Added enum validation for DataAssetOrigin, DataAssetAccessMode, DataAssetTrustStatus in `_scan_populations_with_origin()` using same pattern as `_get_canonical_evidence_from_metadata()` |
| high | Origin classification bug for folder-based uploaded populations | Changed `file_path.parent == uploaded_dir` to check parent directories using `resolved_uploaded in resolved_file.parents` |
| high | Categorical profile computation bug (exposed by exception fix) | `pc.value_counts()` returns StructArray, not Table - converted to table using `pa.Table.from_arrays()` before sorting |
| dismissed | Parquet file loaded with binary read | FALSE POSITIVE: `.parquet` files ARE binary format by design; PyArrow handles them correctly. This is not an issue. |
| dismissed | Test depends on real data directory | FALSE POSITIVE: For Quick Test Population specifically, testing against the real data.parquet file is appropriate and provides stronger validation than mocking. |
