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

## Story 15-3 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | `FitMetrics.__post_init__` accepted `NaN`/`inf` silently — `mse < 0.0` is `False` for both, so non-finite values propagated to governance payloads | Changed guards to `not math.isfinite(self.mse) or self.mse < 0.0` (and same for mae); updated error messages; added 3 new tests in `test_types.py`. |
| high | `TestValidateHoldout.test_holdout_fit_computed_from_holdout_data` only asserted `isfinite` and `>= 0` — a broken implementation returning any non-negative finite value would pass | Replaced weak assertions with exact cross-checks: `expected_mse = sum(rc.absolute_error**2 for rc in rcs) / len(rcs)` against `result.holdout_fit.mse`. |
| high | Null values in `holdout_from_states` were silently dropped during rate computation (nulls excluded by `pc.equal` filter), violating "data contracts fail loudly" | Added `pc.any(pc.is_null(holdout_from_states))` check in `_validate_holdout_inputs`; added test `test_null_from_states_raises`. |
| medium | `CalibrationTargetLoadError` and `CalibrationTargetValidationError` imported locally inside `_validate_holdout_inputs`, inconsistent with `engine.py` pattern (module-level imports) | Moved both to module-level import block alongside `CalibrationOptimizationError`. |
| medium | `CostMatrix` imported at runtime in `validation.py` but only needed for type annotations (with `from __future__ import annotations` all annotations are strings) | Moved `from reformlab.discrete_choice.types import CostMatrix` under `if TYPE_CHECKING:` block; added `from typing import TYPE_CHECKING`. |
| medium | AC-2 "unweighted regardless of `CalibrationTarget.weight`" had no test; a future weighted-metrics regression would pass | Added `test_metrics_are_unweighted` to `TestComputeFitMetrics` verifying hand-computed unweighted formula. |
| low | No `caplog` assertions for structured log events | **Deferred** — logging works correctly; caplog tests would add coverage but the format is validated by the existing log strings. Low risk of silent regression on this dimension. |

## Story 15-4 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | `extract_calibrated_parameters` crashes with `AttributeError` when a manifest entry has a non-dict `value` (e.g., `"value": "string"`) — `str` has no `.get()` method | Replaced list comprehension with explicit loop; validates `isinstance(value, dict)` and raises `CalibrationProvenanceError` with "non-dict" message before domain matching. |
| low | `make_calibration_reference` validates `calibration_manifest_id` is not whitespace-only via `.strip()`, but stores the original un-stripped value — `"  uuid  "` passes validation and is stored with surrounding whitespace, breaking downstream equality checks | Changed `calibration_manifest_id` to `calibration_manifest_id.strip()` in the stored value dict. |
| low | Missing test coverage for the AttributeError crash path (non-dict `value`) | Added `test_non_dict_value_raises_provenance_error` to `TestExtractCalibratedParameters`. |
