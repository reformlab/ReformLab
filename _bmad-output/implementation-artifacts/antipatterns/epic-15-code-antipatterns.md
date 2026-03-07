# Epic 15 - Code Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during code review of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent implementation mistakes (race conditions, missing tests, weak assertions, etc.)

## Story 15-1 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | `_load_yaml` lets `FileNotFoundError`/`OSError` escape unwrapped, breaking the `CalibrationError` hierarchy | Added `except OSError` handler before `except yaml.YAMLError`, wraps in `CalibrationTargetLoadError` |
| medium | `CALIBRATION_TARGET_SCHEMA` missing `weight` optional column — JSON Schema (YAML path) accepts `weight` but CSV/Parquet path has no corresponding declaration, creating an inconsistent contract | Added `pa.field("weight", pa.float64())` to schema and `optional_columns=("weight",)` |
| medium | `_table_to_target_set` catch-all reports `field='row'` — 'row' is a location, not a field name, misleading AC-4 output | Changed to `field='unknown'`; the `{exc}` text already contains the actual field name from `CalibrationTargetValidationError` |
