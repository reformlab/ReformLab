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

## Story 26-6 (2026-04-22)

| Severity | Issue | Fix |
|----------|-------|-----|
| dismissed | Empty string `portfolioName` returns `""` instead of "Untitled — population" | FALSE POSITIVE: FALSE POSITIVE - JavaScript's `if (portfolioName)` treats empty string as falsy, so it correctly falls through to population/composition fallback. Code tracing confirms: `""` → `if (portfolioName)` is false → falls through to `if (population)` → returns "Untitled — FR Synthetic 2024" |
| dismissed | Missing test for empty string `portfolioName` edge case | FALSE POSITIVE: NOT NEEDED - The edge case is already handled correctly by existing logic. Empty string and `null` both fall through to the same code path, which is tested by existing "population only" test cases. |
| dismissed | No validation for invalid population IDs | FALSE POSITIVE: DESIGN CHOICE - Function fails gracefully by returning portfolio-only name. This is appropriate for a utility function - validation should happen at the call site, not in the naming utility. |
| dismissed | AC5 gap - loaded scenario names can be overwritten | FALSE POSITIVE: OUT OF SCOPE - This involves `AppContext.tsx` and `loadSavedScenario()` which were NOT modified in Story 26.6. The story's scope was `naming.ts` and `naming.test.ts` only. Any AC5 issues should be addressed in a separate story focused on AppContext behavior. |
| dismissed | Scenario name input is uncontrolled, doesn't reflect auto-updates | FALSE POSITIVE: OUT OF SCOPE - This involves `ScenarioStageScreen.tsx` which was NOT modified in Story 26.6. Should be addressed in a separate story. |
| dismissed | Story scope/documentation mismatch | FALSE POSITIVE: NOT AN ISSUE - The story's "Files to Modify" section correctly lists only the two files changed for this story's specific requirement (em dash separator). Other changes in the working diff belong to different stories. |
