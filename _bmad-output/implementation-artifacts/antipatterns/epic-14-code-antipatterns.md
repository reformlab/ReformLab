# Epic 14 - Code Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during code review of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent implementation mistakes (race conditions, missing tests, weak assertions, etc.)

## Story 14-1 (2026-03-06)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | Reshape silently overwrites duplicate `(household, alternative)` cells and leaves missing cells as None | Added duplicate cell detection (raises ReshapeError) and post-loop completeness check verifying all cells are filled. |
| high | `pa.concat_tables` failure in expansion produces raw ArrowInvalid instead of ExpansionError | Wrapped `pa.concat_tables(segments)` in try/except, raises ExpansionError with entity/domain context. |
| high | `CostMatrix` accepts invalid internal state — no validation that columns match alternative_ids | Added `__post_init__` that validates `table.column_names` matches `alternative_ids` exactly. |
| medium | `ExpansionResult.population` typed as `Any`, weakening mypy strict | Added `TYPE_CHECKING` guard with `PopulationData` import, changed type to `PopulationData`. |
| medium | `_get_population` method scans all state values, potentially picking wrong PopulationData | Replaced with explicit `population_key` constructor parameter (default: `"population_data"`), direct dict lookup. |
| medium | Redundant `isinstance(exc, Exception)` checks in `except Exception as exc` blocks | Simplified to `original_error=exc` (4 occurrences). |
| low | `apply_alternative` docstring implies in-place mutation | Clarified "Return a new table" and noted PyArrow table immutability. |
| low | `type: ignore[arg-type]` for `population=None` in tests | Replaced with minimal `PopulationData` instances. |
