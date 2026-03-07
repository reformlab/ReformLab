

# Story 15.3: Implement Calibration Validation Against Holdout Data

Status: dev-complete

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **policy analyst**,
I want to validate calibrated discrete choice taste parameters against holdout data (different time period or population subset) so that I can assess whether the calibrated model generalizes beyond the training data,
so that I can trust the behavioral model's predictions are not overfitting to a single dataset and can confidently use calibrated parameters for policy simulations.

## Acceptance Criteria

1. **AC-1: Holdout execution** — Given calibrated β parameters and a holdout dataset (different time period or population subset), when validation runs, then the discrete choice model is executed with the calibrated parameters on the holdout data.
2. **AC-2: Gap metrics** — Given validation results, when compared to holdout observed rates, then the unweighted gap metrics (MSE, mean absolute error) are computed and reported. Metrics are unweighted regardless of `CalibrationTarget.weight` values.
3. **AC-3: Generalization assessment** — Given validation metrics, when inspected, then the analyst can assess whether calibrated parameters generalize beyond the training data — specifically, per-target rate comparisons and aggregate metrics (MSE, MAE) are available.
4. **AC-4: Side-by-side reporting** — Given calibration and validation results, when reported, then both in-sample (training) and out-of-sample (holdout) fit metrics are presented side by side via a single `HoldoutValidationResult` object containing `training_fit` and `holdout_fit` summaries, plus a `to_governance_entry()` method for manifest recording. Note: `training_fit.all_within_tolerance` reflects the original calibration tolerance from `CalibrationConfig`; `holdout_fit.all_within_tolerance` reflects the `rate_tolerance` passed to `validate_holdout()`. The governance entry records these under separate keys (`holdout_rate_tolerance`).

## Tasks / Subtasks

- [x] Task 1: Add `FitMetrics` type to `types.py` (AC: 2, 3, 4)
  - [x] 1.1: Add `FitMetrics` frozen dataclass to `types.py` (after `RateComparison`, before `CalibrationResult`): `mse: float`, `mae: float`, `n_targets: int`, `all_within_tolerance: bool`
  - [x] 1.2: Add `__post_init__` validation: `n_targets > 0`, `mse >= 0.0`, `mae >= 0.0`; raise `CalibrationOptimizationError` on violation

- [x] Task 2: Add `HoldoutValidationResult` type to `types.py` (AC: 3, 4)
  - [x] 2.1: Add `HoldoutValidationResult` frozen dataclass (after `CalibrationConfig`): `domain: str`, `training_fit: FitMetrics`, `holdout_fit: FitMetrics`, `holdout_rate_comparisons: tuple[RateComparison, ...]`, `rate_tolerance: float`
  - [x] 2.2: Add `to_governance_entry(*, source_label: str = "holdout_validation") -> dict[str, Any]` method (see Dev Notes for structure)

- [x] Task 3: Implement validation module (AC: 1, 2, 3, 4)
  - [x] 3.1: Create `src/reformlab/calibration/validation.py` with module docstring referencing Story 15.3 / FR53
  - [x] 3.2: Implement `compute_fit_metrics(rate_comparisons: tuple[RateComparison, ...]) -> FitMetrics` — pure function that computes MSE, MAE from a tuple of `RateComparison` objects; raise `CalibrationOptimizationError` if empty tuple
  - [x] 3.3: Implement `validate_holdout(calibration_result, holdout_targets, holdout_cost_matrix, holdout_from_states, *, rate_tolerance=0.05) -> HoldoutValidationResult` — main entry point (see Dev Notes for full algorithm)
  - [x] 3.4: Implement input validation inside `validate_holdout()` — validate: (a) `rate_tolerance` is finite and > 0 (validate at top of `validate_holdout()` before any other logic), (b) holdout domain targets non-empty after `by_domain()` filter, (c) call `holdout_domain_targets.validate_consistency()` to catch duplicate rows or rate-sum violations in holdout data, (d) all holdout target `to_state` values exist in `holdout_cost_matrix.alternative_ids`, (e) all holdout target `from_state` values exist in `holdout_from_states` array, (f) `len(holdout_from_states) == holdout_cost_matrix.n_households` — raise `CalibrationOptimizationError` with clear messages for all checks
  - [x] 3.5: Add structured logging: `event=holdout_validation_start`, `event=holdout_validation_complete`

- [x] Task 4: Update public API in `__init__.py` (AC: all)
  - [x] 4.1: Add imports and `__all__` entries for: `FitMetrics`, `HoldoutValidationResult`, `validate_holdout`

- [x] Task 5: Write tests (AC: all)
  - [x] 5.1: Add holdout fixtures to `tests/calibration/conftest.py`: `make_holdout_target_set()`, `make_holdout_cost_matrix()`, `make_holdout_from_states()` helpers
  - [x] 5.2: `test_validation.py` — `TestComputeFitMetrics`: correct MSE/MAE for hand-computed example, empty tuple raises CalibrationOptimizationError, single comparison, all_within_tolerance flag consistency
  - [x] 5.3: `test_validation.py` — `TestValidateHoldout`: correct result structure, holdout_fit and training_fit both populated, MSE/MAE computed correctly for holdout data, rate_comparisons has correct entries per holdout target, all_within_tolerance consistency, holdout_rate_comparisons sorted by (from_state, to_state)
  - [x] 5.4: `test_validation.py` — `TestValidateHoldoutValidation`: invalid rate_tolerance (zero, negative, NaN, inf) raises CalibrationOptimizationError, empty holdout targets raises CalibrationOptimizationError, duplicate holdout target rows raise CalibrationOptimizationError (validate_consistency), unknown to_state raises error, missing from_state raises error, dimension mismatch (from_states length ≠ n_households) raises error
  - [x] 5.5: `test_validation.py` — `TestValidateHoldoutEdgeCases`: single holdout target, holdout with different cost matrix than training, perfect generalization (simulated matches observed → MSE≈0), poor generalization (large gap), holdout with different number of households than training
  - [x] 5.6: `test_validation.py` — `TestHoldoutValidationResult`: construction, frozen immutability, to_governance_entry structure, to_governance_entry custom source_label
  - [x] 5.7: `test_types.py` — add tests for `FitMetrics` (construction, frozen immutability, post_init validation)

- [x] Task 6: Lint, type-check, regression (AC: all)
  - [x] 6.1: `uv run ruff check src/reformlab/calibration/ tests/calibration/` — clean
  - [x] 6.2: `uv run mypy src/reformlab/calibration/` — clean (exclude pre-existing template error)
  - [x] 6.3: `uv run pytest tests/` — all tests pass (existing + new)

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**Module location:** `src/reformlab/calibration/validation.py` — new file in the existing calibration module. Consistent with `population/validation.py` pattern. No new subdirectories needed.

**Updated module file layout after this story:**
```
src/reformlab/calibration/
├── __init__.py                       # Updated: add new exports
├── types.py                          # Updated: add FitMetrics, HoldoutValidationResult
├── errors.py                         # No changes
├── engine.py                         # No changes
├── validation.py                     # NEW: validate_holdout() + compute_fit_metrics()
├── loader.py                         # No changes
└── schema/
    ├── __init__.py                   # No changes
    └── calibration-targets.schema.json  # No changes
```

**Every file starts with** `from __future__ import annotations`.

**Frozen dataclasses everywhere** — `FitMetrics`, `HoldoutValidationResult` are all `@dataclass(frozen=True)`.

**Module docstrings** — `validation.py` must have a module-level docstring referencing Story 15.3 / FR53.

**Non-blocking validation pattern** — Following `population/validation.py`: the validation function does NOT raise exceptions when holdout fit is poor. It returns a result with `all_within_tolerance` flag. Callers decide whether to treat poor fit as an error. Only raises `CalibrationOptimizationError` for _invalid inputs_ (missing from_states, unknown alternatives, empty targets).

**Structured logging** — `logging.getLogger(__name__)` with `key=value` format:
```python
logger.info(
    "event=holdout_validation_start domain=%s n_holdout_targets=%d n_households=%d",
    domain, n_targets, n_households,
)
logger.info(
    "event=holdout_validation_complete domain=%s holdout_mse=%f holdout_mae=%f "
    "training_mse=%f training_mae=%f all_within_tolerance=%s",
    domain, holdout_mse, holdout_mae, training_mse, training_mae, all_within,
)
```

### No New Dependencies

This story uses only existing dependencies:
- `pyarrow` — for array operations (`pc.equal`, `pc.filter`, `pc.unique`)
- Types from `calibration.types` and `discrete_choice.types`
- `compute_simulated_rates()` from `calibration.engine`

No new entries in `pyproject.toml` needed.

### Key Imports

```python
import math

from reformlab.calibration.engine import compute_simulated_rates
from reformlab.calibration.errors import CalibrationOptimizationError
from reformlab.calibration.types import (
    CalibrationResult,
    CalibrationTargetSet,
    FitMetrics,
    HoldoutValidationResult,
    RateComparison,
)
from reformlab.discrete_choice.types import CostMatrix, TasteParameters
```

Import `pyarrow` and `pyarrow.compute` at runtime (not behind `TYPE_CHECKING`) since the function operates on `pa.Array` at runtime.

### New Types

**`FitMetrics` frozen dataclass (in `types.py`):**
```python
@dataclass(frozen=True)
class FitMetrics:
    """Aggregate fit metrics for a set of rate comparisons.

    Used to summarize both in-sample (training) and out-of-sample (holdout)
    fit quality for side-by-side comparison.

    Attributes:
        mse: Mean Squared Error across all rate comparisons.
        mae: Mean Absolute Error across all rate comparisons.
        n_targets: Number of rate comparisons summarized.
        all_within_tolerance: True if all comparisons are within tolerance.
    """

    mse: float
    mae: float
    n_targets: int
    all_within_tolerance: bool

    def __post_init__(self) -> None:
        if self.n_targets <= 0:
            raise CalibrationOptimizationError(
                f"n_targets={self.n_targets!r} must be > 0"
            )
        if self.mse < 0.0:
            raise CalibrationOptimizationError(
                f"mse={self.mse!r} must be >= 0.0"
            )
        if self.mae < 0.0:
            raise CalibrationOptimizationError(
                f"mae={self.mae!r} must be >= 0.0"
            )
```

**`HoldoutValidationResult` frozen dataclass (in `types.py`):**
```python
@dataclass(frozen=True)
class HoldoutValidationResult:
    """Result of holdout validation with side-by-side training/holdout metrics.

    Provides both in-sample (training) and out-of-sample (holdout) fit
    metrics so the analyst can assess whether calibrated parameters
    generalize beyond the training data.

    Attributes:
        domain: Decision domain that was validated.
        training_fit: In-sample aggregate fit metrics from calibration.
        holdout_fit: Out-of-sample aggregate fit metrics from holdout validation.
        holdout_rate_comparisons: Per-target observed vs simulated comparisons on holdout.
        rate_tolerance: Tolerance threshold used for holdout within_tolerance checks.
            Note: training_fit.all_within_tolerance reflects the original calibration
            tolerance from CalibrationConfig, which may differ. For a fair side-by-side
            comparison, use the same tolerance here as in CalibrationConfig.
    """

    domain: str
    training_fit: FitMetrics
    holdout_fit: FitMetrics
    holdout_rate_comparisons: tuple[RateComparison, ...]
    rate_tolerance: float
```

### Algorithm: `compute_fit_metrics()`

```python
def compute_fit_metrics(
    rate_comparisons: tuple[RateComparison, ...],
) -> FitMetrics:
    """Compute unweighted aggregate fit metrics (MSE, MAE) from rate comparisons.

    Metrics are computed without applying CalibrationTarget.weight — all
    comparisons contribute equally regardless of their source weight.

    Args:
        rate_comparisons: Per-target observed vs simulated rate comparisons.

    Returns:
        FitMetrics with unweighted MSE, MAE, and tolerance summary.

    Raises:
        CalibrationOptimizationError: If rate_comparisons is empty.
    """
    n = len(rate_comparisons)
    if n == 0:
        raise CalibrationOptimizationError(
            "Cannot compute fit metrics from empty rate comparisons"
        )

    mse = sum(rc.absolute_error ** 2 for rc in rate_comparisons) / n
    mae = sum(rc.absolute_error for rc in rate_comparisons) / n
    all_within = all(rc.within_tolerance for rc in rate_comparisons)

    return FitMetrics(mse=mse, mae=mae, n_targets=n, all_within_tolerance=all_within)
```

### Algorithm: `validate_holdout()`

```python
def validate_holdout(
    calibration_result: CalibrationResult,
    holdout_targets: CalibrationTargetSet,
    holdout_cost_matrix: CostMatrix,
    holdout_from_states: pa.Array,
    *,
    rate_tolerance: float = 0.05,
) -> HoldoutValidationResult:
    """Validate calibrated parameters against holdout data.

    Executes the discrete choice model with the calibrated β parameters
    on a holdout dataset (different time period or population subset),
    computes gap metrics (MSE, MAE), and returns both training and holdout
    fit metrics side by side.

    Args:
        calibration_result: Result from CalibrationEngine.calibrate() containing
            the optimized TasteParameters and training rate comparisons.
        holdout_targets: Calibration targets for the holdout dataset (same format
            as training targets, loaded via load_calibration_targets()).
        holdout_cost_matrix: Pre-computed N×M CostMatrix for the holdout population.
        holdout_from_states: Length-N PyArrow array of household origin states
            for the holdout population.
        rate_tolerance: Maximum acceptable |simulated - observed| per target.
            Defaults to 0.05. Must be finite and > 0. Note: this tolerance
            applies only to holdout comparisons. training_fit.all_within_tolerance
            reflects the original calibration tolerance from CalibrationConfig,
            which may differ. For a meaningful side-by-side comparison, use the
            same rate_tolerance here as in CalibrationConfig.

    Returns:
        HoldoutValidationResult with training_fit and holdout_fit side by side.

    Raises:
        CalibrationOptimizationError: If holdout inputs are invalid (non-positive
            rate_tolerance, empty targets, duplicate targets, unknown to_state,
            missing from_state, dimension mismatch).
    """
    domain = calibration_result.domain

    # 0. Validate rate_tolerance immediately (before any other logic)
    if not math.isfinite(rate_tolerance) or rate_tolerance <= 0.0:
        raise CalibrationOptimizationError(
            f"rate_tolerance={rate_tolerance!r} must be a finite positive number"
        )

    # 1. Log start
    logger.info(...)

    # 2. Filter holdout targets to domain
    holdout_domain_targets = holdout_targets.by_domain(domain)

    # 3. Validate holdout inputs (includes validate_consistency() on holdout targets)
    _validate_holdout_inputs(
        holdout_domain_targets, holdout_cost_matrix,
        holdout_from_states, domain,
    )

    # 4. Compute simulated rates on holdout data using calibrated β
    optimized_taste = calibration_result.optimized_parameters
    holdout_rates = compute_simulated_rates(
        holdout_cost_matrix, optimized_taste,
        holdout_from_states, holdout_cost_matrix.alternative_ids,
    )

    # 5. Build holdout rate comparisons
    holdout_comparisons_list: list[RateComparison] = []
    for t in holdout_domain_targets.targets:
        key = (t.from_state, t.to_state)
        sim_rate = holdout_rates.get(key, 0.0)
        abs_err = abs(sim_rate - t.observed_rate)
        holdout_comparisons_list.append(
            RateComparison(
                from_state=t.from_state,
                to_state=t.to_state,
                observed_rate=t.observed_rate,
                simulated_rate=sim_rate,
                absolute_error=abs_err,
                within_tolerance=abs_err <= rate_tolerance,
            )
        )
    holdout_comparisons = tuple(
        sorted(holdout_comparisons_list, key=lambda rc: (rc.from_state, rc.to_state))
    )

    # 6. Compute holdout fit metrics
    holdout_fit = compute_fit_metrics(holdout_comparisons)

    # 7. Compute training fit metrics from calibration result
    training_fit = compute_fit_metrics(calibration_result.rate_comparisons)

    # 8. Log completion and return
    logger.info(...)

    return HoldoutValidationResult(
        domain=domain,
        training_fit=training_fit,
        holdout_fit=holdout_fit,
        holdout_rate_comparisons=holdout_comparisons,
        rate_tolerance=rate_tolerance,
    )
```

### Input Validation: `_validate_holdout_inputs()`

Private function inside `validation.py`:

```python
def _validate_holdout_inputs(
    holdout_domain_targets: CalibrationTargetSet,
    holdout_cost_matrix: CostMatrix,
    holdout_from_states: pa.Array,
    domain: str,
) -> None:
    """Validate holdout inputs before running validation.

    Raises:
        CalibrationOptimizationError: On any validation failure.
    """
    # 1. Non-empty holdout targets
    if len(holdout_domain_targets.targets) == 0:
        raise CalibrationOptimizationError(
            f"No holdout calibration targets for domain={domain!r}"
        )

    # 1b. Semantic consistency (duplicate rows, rate sums) — fail loudly
    holdout_domain_targets.validate_consistency()

    # 2. Dimension match
    if len(holdout_from_states) != holdout_cost_matrix.n_households:
        raise CalibrationOptimizationError(
            f"holdout from_states length ({len(holdout_from_states)}) must equal "
            f"holdout cost_matrix.n_households ({holdout_cost_matrix.n_households})"
        )

    # 3. All to_state values exist in holdout cost_matrix alternatives
    available_alts = set(holdout_cost_matrix.alternative_ids)
    unknown_alts = {t.to_state for t in holdout_domain_targets.targets} - available_alts
    if unknown_alts:
        raise CalibrationOptimizationError(
            f"Unknown holdout to_state values {sorted(unknown_alts)!r} in domain={domain!r}; "
            f"expected one of {sorted(available_alts)!r}"
        )

    # 4. All from_state values exist in holdout from_states array
    available_from: set[str] = set(pc.unique(holdout_from_states).to_pylist())
    target_from = {t.from_state for t in holdout_domain_targets.targets}
    missing_from = target_from - available_from
    if missing_from:
        raise CalibrationOptimizationError(
            f"Missing holdout from_state values {sorted(missing_from)!r} "
            f"from provided holdout_from_states in domain={domain!r}"
        )
```

### Governance Integration Pattern

`HoldoutValidationResult.to_governance_entry()`:
```python
def to_governance_entry(self, *, source_label: str = "holdout_validation") -> dict[str, Any]:
    return {
        "key": "holdout_validation",
        "value": {
            "domain": self.domain,
            "holdout_rate_tolerance": self.rate_tolerance,
            "training": {
                "mse": self.training_fit.mse,
                "mae": self.training_fit.mae,
                "n_targets": self.training_fit.n_targets,
                "all_within_tolerance": self.training_fit.all_within_tolerance,
            },
            "holdout": {
                "mse": self.holdout_fit.mse,
                "mae": self.holdout_fit.mae,
                "n_targets": self.holdout_fit.n_targets,
                "all_within_tolerance": self.holdout_fit.all_within_tolerance,
            },
        },
        "source": source_label,
        "is_default": False,
    }
```

### Hand-Computed Test Example

**Setup:** Reuse the 3-household example from Story 15.2.

**Training calibration result (from Story 15.2):**
- Calibrated beta: let's say β = -0.03 (the optimizer finds this)
- Training targets: petrol→A=0.40, petrol→B=0.55, diesel→A=0.60
- Training rate_comparisons: available from CalibrationResult

**Holdout data (different observed rates representing a different time period):**

| Household | from_state | cost_A | cost_B |
|-----------|-----------|--------|--------|
| 0         | petrol    | 110.0  | 190.0  |
| 1         | petrol    | 140.0  | 110.0  |
| 2         | diesel    | 210.0  | 280.0  |

Holdout targets (e.g., 2023 data vs 2022 training):
- petrol→A=0.45, petrol→B=0.50, diesel→A=0.65

**Test approach:**
1. First run `CalibrationEngine.calibrate()` on training data to get calibration_result
2. Call `validate_holdout(calibration_result, holdout_targets, holdout_cost_matrix, holdout_from_states)`
3. Verify holdout_fit.mse and holdout_fit.mae are computed correctly
4. Verify training_fit is extracted from calibration_result.rate_comparisons
5. Verify both are present in the result for side-by-side comparison

**Simpler hand-computed test for `compute_fit_metrics()`:**

Given rate_comparisons:
- RC1: absolute_error = 0.05
- RC2: absolute_error = 0.10
- RC3: absolute_error = 0.02

```
MSE = (0.05² + 0.10² + 0.02²) / 3 = (0.0025 + 0.01 + 0.0004) / 3 = 0.0043
MAE = (0.05 + 0.10 + 0.02) / 3 = 0.0567
```

Use these values (with `pytest.approx(abs=1e-4)`) in test fixtures.

### Cross-Story Dependencies

| Story | Relationship |
|---|---|
| **14.2** | Imports: `TasteParameters`, `CostMatrix` — used as inputs |
| **15.1** | Imports: `CalibrationTargetSet`, `CalibrationTarget` — holdout targets use same format |
| **15.1** | `load_calibration_targets()` — loads holdout data from same file formats |
| **15.2** | Imports: `CalibrationResult`, `RateComparison`, `CalibrationEngine` — training result is input |
| **15.2** | Imports: `compute_simulated_rates()` — core computation reused on holdout data |
| **15.4** | Consumer — records `HoldoutValidationResult.to_governance_entry()` in run manifests |
| **15.5** | Consumer — notebook demo displays training vs holdout comparison |

### Data Flow

```
CalibrationResult              Holdout CalibrationTargetSet     Holdout CostMatrix
(from Story 15.2)              (loaded via loader.py)            (pre-computed)
       │                              │                              │
       ├── optimized_parameters       │                              │
       ├── rate_comparisons           │                              │
       │   (training)                 │                              │
       │                              ▼                              ▼
       │                    by_domain(domain) ───►  holdout domain targets
       │                                                             │
       ▼                                                             ▼
  compute_fit_metrics()               _validate_holdout_inputs()
  (training comparisons)                         │
       │                                         ▼
       │                          compute_simulated_rates()
       │                          (calibrated β + holdout data)
       │                                         │
       │                                         ▼
       │                          Build holdout RateComparisons
       │                                         │
       │                                         ▼
       │                          compute_fit_metrics()
       │                          (holdout comparisons)
       │                                         │
       ▼                                         ▼
  training_fit: FitMetrics      holdout_fit: FitMetrics
       │                                         │
       └────────────────┬────────────────────────┘
                        ▼
              HoldoutValidationResult
              (side-by-side metrics,
               holdout_rate_comparisons,
               to_governance_entry())
```

### Anti-Patterns from Stories 15.1 and 15.2 (DO NOT REPEAT)

| Issue | Prevention |
|-------|-----------|
| Contract conflict between dataclass and schema | `FitMetrics` and `HoldoutValidationResult` fields have clear types — no ambiguity with schema |
| Missing floating-point tolerance | MSE and MAE are computed as float division — use `pytest.approx()` in tests |
| Unclear error locations | All `CalibrationOptimizationError` messages include: `domain=`, specific values, what was expected |
| Divide-by-zero | `compute_fit_metrics()` raises on empty input; `__post_init__` validates `n_targets > 0` |
| AC wording ambiguity | AC-1 through AC-4 are specific about what's validated and how results are structured |
| Docstring ordering | Module docstring first, then `from __future__ import annotations` (project convention) |

### Project Structure Notes

- `validation.py` is a new file in `src/reformlab/calibration/` — mirrors the pattern of `population/validation.py`
- Test file `tests/calibration/test_validation.py` mirrors the source
- No new test fixture files needed — tests use inline PyArrow table construction and existing conftest helpers
- No changes to `pyproject.toml` — no new dependencies or schema files
- Holdout data uses **the same format** as training data (`CalibrationTargetSet` loaded via `load_calibration_targets()`) — no new file formats

### Testing Standards Summary

- Class-based test grouping: `TestComputeFitMetrics`, `TestValidateHoldout`, `TestValidateHoldoutValidation`, `TestValidateHoldoutEdgeCases`, `TestHoldoutValidationResult`, `TestFitMetrics`
- Docstrings in Given/When/Then format
- Direct `assert` statements — no custom assertion helpers
- `pytest.raises(CalibrationOptimizationError, match=...)` for error cases
- `pytest.approx(expected, abs=1e-4)` for float comparisons
- Inline PyArrow table construction in fixtures
- Reference story/AC IDs in test comments
- Hand-computed expected values for metric tests
- Integration test: run `CalibrationEngine.calibrate()` first, then `validate_holdout()` on holdout data

### References

- [Source: docs/epics.md — Epic 15 / Story 15.3 acceptance criteria]
- [Source: docs/project-context.md — coding conventions, frozen dataclasses, PyArrow canonical type]
- [Source: src/reformlab/calibration/engine.py — compute_simulated_rates(), CalibrationEngine.calibrate()]
- [Source: src/reformlab/calibration/types.py — CalibrationResult, RateComparison, CalibrationTargetSet, CalibrationConfig]
- [Source: src/reformlab/calibration/errors.py — CalibrationOptimizationError]
- [Source: src/reformlab/population/validation.py — non-blocking validation pattern, ValidationResult, to_governance_entry()]
- [Source: src/reformlab/governance/manifest.py — AssumptionEntry TypedDict]
- [Source: src/reformlab/discrete_choice/types.py — TasteParameters, CostMatrix]
- [Source: src/reformlab/discrete_choice/logit.py — compute_utilities(), compute_probabilities()]
- [Source: _bmad-output/implementation-artifacts/15-2-implement-calibrationengine-with-objective-function-optimization.md — Story 15.2 completion notes, anti-patterns]
- [Source: _bmad-output/implementation-artifacts/15-1-define-calibration-target-format-and-load-observed-transition-rates.md — Story 15.1 patterns]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — implementation was straightforward with no blockers.

### Completion Notes List

- ✅ `FitMetrics` frozen dataclass added to `types.py` after `RateComparison`, with `__post_init__` validation for n_targets > 0, mse >= 0, mae >= 0.
- ✅ `HoldoutValidationResult` frozen dataclass added to `types.py` after `CalibrationConfig`, with `to_governance_entry()` matching the specified structure.
- ✅ `validation.py` created with `compute_fit_metrics()` (unweighted MSE/MAE) and `validate_holdout()` (non-blocking, returns result with all_within_tolerance flag).
- ✅ `_validate_holdout_inputs()` validates: rate_tolerance first, empty targets, consistency (duplicates/rate-sums via validate_consistency()), dimension match, unknown to_state, missing from_state.
- ✅ `validate_consistency()` errors re-raised as `CalibrationOptimizationError` to maintain single exception boundary.
- ✅ Structured logging with `event=holdout_validation_start` and `event=holdout_validation_complete`.
- ✅ Public API updated: `FitMetrics`, `HoldoutValidationResult`, `validate_holdout` in `__init__.py`.
- ✅ 168 calibration tests pass (120 pre-existing + 48 new); 2709 total non-server tests pass.
- ✅ Ruff clean; mypy clean for calibration module (pre-existing template error in composition.py excluded per story spec).
- ✅ Non-blocking validation pattern followed: poor holdout fit never raises, callers inspect `all_within_tolerance`.

### File List

New files:
- `src/reformlab/calibration/validation.py`
- `tests/calibration/test_validation.py`

Modified files:
- `src/reformlab/calibration/__init__.py` — add FitMetrics, HoldoutValidationResult, validate_holdout exports
- `src/reformlab/calibration/types.py` — add FitMetrics, HoldoutValidationResult, update module docstring
- `tests/calibration/conftest.py` — add make_holdout_target_set(), make_holdout_cost_matrix(), make_holdout_from_states() helpers
- `tests/calibration/test_types.py` — add TestFitMetrics class (construction, frozen, post_init validation)

### Change Log

- 2026-03-07: Implemented Story 15.3 — FitMetrics, HoldoutValidationResult types, validation.py module, full test coverage (168 calibration tests pass).
