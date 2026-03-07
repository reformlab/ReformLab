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

## Story 15-2 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | `_validate_inputs()` in `CalibrationEngine` calls `domain_targets.validate_consistency()` directly, which can raise `CalibrationTargetLoadError` or `CalibrationTargetValidationError`. These escape the method, violating the contract documented in Task 5.7 ("Raise `CalibrationOptimizationError` for all failures"). | Wrapped the call in `try/except (CalibrationTargetLoadError, CalibrationTargetValidationError)` and re-raised as `CalibrationOptimizationError` with domain context; added the two error imports to the module. |
| high | `CalibrationTarget.weight` validation only checks `weight < 0.0`. Since `NaN < 0.0 → False` and `inf < 0.0 → False` in IEEE 754, both `float('nan')` and `float('inf')` pass silently and propagate into the objective function, producing `NaN` or `inf` results that bypass the `total_weight <= 0.0` guard. | Changed guard to `not math.isfinite(self.weight) or self.weight < 0.0`; added `import math`. |
| medium | `TestLogLikelihoodObjective.test_known_value_hand_computed` is named "known value" but only asserts `isfinite` and `> 0` — no exact value check. Large numeric regressions would pass silently. | Added `assert ll == pytest.approx(2.14, abs=0.02)` with the hand-computed derivation documented in the test docstring. |
| medium | `TestCalibrationEngineEdgeCases.test_non_convergence_returns_result_with_flag_false` is named "flag_false" but only asserts `result.iterations >= 0`. The `convergence_flag` field is never checked. | Replaced weak assertion with `assert result.convergence_flag is False`. |
| low | `src/reformlab/calibration/schema/__init__.py` docstring does not reference Story 15.1/15.2, violating the project convention "every module has a docstring explaining its role, referencing relevant story/FR". | Added story references to the docstring. |
