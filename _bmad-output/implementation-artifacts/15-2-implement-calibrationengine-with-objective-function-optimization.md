
# Story 15.2: Implement CalibrationEngine with Objective Function Optimization

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **policy analyst**,
I want a calibration engine that optimizes discrete choice taste parameters (β coefficients) against observed transition rates by minimizing a distance metric (MSE or log-likelihood),
so that my simulated household decisions match real-world data and I can trust the behavioral model's predictions.

## Acceptance Criteria

1. **AC-1: Optimization loop** — Given calibration targets and an initial set of β coefficients, when the calibration engine runs, then it executes the discrete choice model repeatedly with different β values to minimize the gap between simulated and observed transition rates.
2. **AC-2: Objective function** — Given the calibration engine, when optimizing, then the objective function computes the distance (MSE or log-likelihood) between simulated aggregate transition rates and observed targets.
3. **AC-3: Determinism** — Given the optimization process, when run with a fixed seed and initial parameters, then it converges to the same β values across runs (deterministic optimization).
4. **AC-4: Convergence diagnostics** — Given the calibration engine, when it completes, then it returns: optimized β coefficients per domain, final objective function value, convergence diagnostics (iterations, gradient norm, convergence flag).
5. **AC-5: Gap threshold** — Given the calibration engine, when β coefficients produce simulated rates, then the gap between simulated and observed rates is below the documented threshold for each calibration target.

## Tasks / Subtasks

- [ ] Task 1: Add scipy dependency (AC: all)
  - [ ] 1.1: Add `scipy>=1.14.0` to `[project] dependencies` in `pyproject.toml`
  - [ ] 1.2: Add `[[tool.mypy.overrides]]` for `scipy` and `scipy.*` with `ignore_missing_imports = true`
  - [ ] 1.3: Run `uv sync` to install scipy

- [ ] Task 2: Extend CalibrationTarget with weight field (AC: 2)
  - [ ] 2.1: Add `weight: float = 1.0` field to `CalibrationTarget` in `types.py` (after `source_metadata`, before end of class) — **backward-compatible** since it has a default value
  - [ ] 2.2: Add `__post_init__` validation: `weight >= 0.0` (raise `CalibrationTargetValidationError` if negative)
  - [ ] 2.3: Update `_table_to_target_set()` in `loader.py` to extract weight column if present: `weight_col = table.column("weight").to_pylist() if "weight" in table.column_names else [1.0] * n_rows`
  - [ ] 2.4: Update `_load_yaml()` in `loader.py` to extract weight: `weight=float(item.get("weight", 1.0))`
  - [ ] 2.5: Verify all existing 70 calibration tests still pass (no breaking changes due to default value)

- [ ] Task 3: Add CalibrationResult and related types to `types.py` (AC: 4, 5)
  - [ ] 3.1: `RateComparison` frozen dataclass: `from_state: str`, `to_state: str`, `observed_rate: float`, `simulated_rate: float`, `absolute_error: float`, `within_tolerance: bool`
  - [ ] 3.2: `CalibrationResult` frozen dataclass: `optimized_parameters: TasteParameters`, `domain: str`, `objective_type: str`, `objective_value: float`, `convergence_flag: bool`, `iterations: int`, `gradient_norm: float | None`, `method: str`, `rate_comparisons: tuple[RateComparison, ...]`, `all_within_tolerance: bool`
  - [ ] 3.3: `CalibrationConfig` frozen dataclass: `targets: CalibrationTargetSet`, `cost_matrix: CostMatrix`, `from_states: pa.Array`, `domain: str`, `initial_beta: float = -0.01`, `objective_type: str = "mse"`, `method: str = "L-BFGS-B"`, `max_iterations: int = 100`, `tolerance: float = 1e-8`, `beta_bounds: tuple[float, float] = (-1.0, 0.0)`, `rate_tolerance: float = 0.05`
  - [ ] 3.4: `CalibrationConfig.__post_init__` validation: `objective_type` in `("mse", "log_likelihood")`; `max_iterations > 0`; `beta_bounds[0] < beta_bounds[1]`; `rate_tolerance > 0.0`; `len(from_states) == cost_matrix.n_households`
  - [ ] 3.5: `CalibrationResult.to_governance_entry()` method returning `AssumptionEntry`-compatible dict (see Dev Notes for structure)

- [ ] Task 4: Add CalibrationOptimizationError to `errors.py` (AC: 4)
  - [ ] 4.1: Add `CalibrationOptimizationError(CalibrationError)` with docstring: "Raised when calibration optimization fails (convergence, invalid parameters, input validation)."

- [ ] Task 5: Implement engine module (AC: 1, 2, 3, 4, 5)
  - [ ] 5.1: Create `src/reformlab/calibration/engine.py` with module docstring referencing Story 15.2 / FR52
  - [ ] 5.2: Implement `compute_simulated_rates(cost_matrix, taste_parameters, from_states, alternative_ids) -> dict[tuple[str, str], float]` — pure function that calls `compute_utilities()` and `compute_probabilities()` from `discrete_choice.logit`, then groups probabilities by from_state and computes mean per (from_state, to_state) pair using `pyarrow.compute` (see Dev Notes algorithm)
  - [ ] 5.3: Implement `build_mse_objective(targets, cost_matrix, from_states) -> Callable[[NDArray], float]` — returns a closure that takes `beta_array: NDArray[np.float64]` (shape `(1,)` — scipy convention), creates `TasteParameters(beta_cost=beta_array[0])`, calls `compute_simulated_rates()`, and returns weighted MSE (see Dev Notes formula)
  - [ ] 5.4: Implement `build_log_likelihood_objective(targets, cost_matrix, from_states) -> Callable[[NDArray], float]` — same pattern but returns negative log-likelihood with epsilon clamping (`1e-15`) to avoid `log(0)`
  - [ ] 5.5: Implement `CalibrationEngine` frozen dataclass with single field `config: CalibrationConfig`
  - [ ] 5.6: Implement `CalibrationEngine.calibrate() -> CalibrationResult` (see Dev Notes for full algorithm)
  - [ ] 5.7: Implement `CalibrationEngine._validate_inputs()` — validate: (a) domain targets non-empty after `by_domain()` filter, (b) all target `to_state` values exist in `cost_matrix.alternative_ids`, (c) all target `from_state` values exist in `from_states` array, (d) no duplicate `(from_state, to_state)` pairs in filtered targets — raise `CalibrationOptimizationError` with clear messages on failure
  - [ ] 5.8: Add structured logging: `event=calibration_start`, `event=iteration` (debug), `event=calibration_complete`, `event=calibration_failed`

- [ ] Task 6: Update public API in `__init__.py` (AC: all)
  - [ ] 6.1: Add imports and `__all__` entries for: `CalibrationConfig`, `CalibrationResult`, `RateComparison`, `CalibrationEngine`, `CalibrationOptimizationError`

- [ ] Task 7: Write tests (AC: all)
  - [ ] 7.1: Add fixtures to `tests/calibration/conftest.py`: `sample_cost_matrix()` (3×3 CostMatrix), `sample_from_states()` (pa.Array of 3 households), `sample_calibration_config()`, `sample_engine()` helpers
  - [ ] 7.2: `test_engine.py` — `TestComputeSimulatedRates`: correct rates for hand-computed 3-household example (see Dev Notes), empty population returns empty dict, single-household group, multiple from_state groups
  - [ ] 7.3: `test_engine.py` — `TestMSEObjective`: zero error when simulated matches observed, known MSE value for hand-computed example, weighted MSE applies weights correctly
  - [ ] 7.4: `test_engine.py` — `TestLogLikelihoodObjective`: known value for hand-computed example, clamping prevents log(0), negative log-likelihood is returned (positive scalar for minimization)
  - [ ] 7.5: `test_engine.py` — `TestCalibrationEngine`: construction with valid config, calibrate() returns CalibrationResult with all required fields, convergence_flag is True for well-posed problems, determinism (same initial beta + same inputs → same result), optimized beta is within bounds, all_within_tolerance check, rate_comparisons has correct per-target entries
  - [ ] 7.6: `test_engine.py` — `TestCalibrationEngineValidation`: missing from_state raises CalibrationOptimizationError, missing to_state (alternative) raises error, empty domain targets raises error, dimension mismatch (from_states length ≠ n_households) caught by CalibrationConfig post_init
  - [ ] 7.7: `test_engine.py` — `TestCalibrationEngineEdgeCases`: single target calibration, single household, all households same from_state, beta at bounds boundary, non-convergence (max_iterations=1) still returns result with convergence_flag=False
  - [ ] 7.8: `test_types.py` — add tests for `RateComparison`, `CalibrationResult`, `CalibrationConfig` (construction, frozen immutability, post_init validation, to_governance_entry)
  - [ ] 7.9: `test_types.py` — add tests for `CalibrationTarget.weight` field (default=1.0, negative raises, positive works)
  - [ ] 7.10: `test_errors.py` — add `CalibrationOptimizationError` hierarchy test (is subclass of CalibrationError)

- [ ] Task 8: Lint, type-check, regression (AC: all)
  - [ ] 8.1: `uv run ruff check src/reformlab/calibration/ tests/calibration/` — clean
  - [ ] 8.2: `uv run mypy src/reformlab/calibration/` — no issues
  - [ ] 8.3: `uv run mypy src/` — no issues across all source files
  - [ ] 8.4: `uv run pytest tests/` — all tests pass, zero failures, including all existing 2639+ tests

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**Module location:** `src/reformlab/calibration/engine.py` — new file in the existing calibration module (created in Story 15.1). No new subdirectories needed.

**Updated module file layout after this story:**
```
src/reformlab/calibration/
├── __init__.py                       # Updated: add new exports
├── types.py                          # Updated: add CalibrationConfig, CalibrationResult, RateComparison; add weight to CalibrationTarget
├── errors.py                         # Updated: add CalibrationOptimizationError
├── engine.py                         # NEW: CalibrationEngine + objective functions
├── loader.py                         # Updated: extract weight field from CSV/YAML
└── schema/
    ├── __init__.py                   # No changes
    └── calibration-targets.schema.json  # No changes (weight already in schema)
```

**Every file starts with** `from __future__ import annotations`.

**Frozen dataclasses everywhere** — CalibrationEngine, CalibrationConfig, CalibrationResult, RateComparison are all `@dataclass(frozen=True)`.

**Module docstrings** — `engine.py` must have a module-level docstring referencing Story 15.2 / FR52.

**Structured logging** — `logging.getLogger(__name__)` with `key=value` format:
```python
logger.info("event=calibration_start domain=%s initial_beta=%f method=%s", domain, beta, method)
logger.debug("event=objective_eval beta=%f objective=%f", beta, obj_value)
logger.info("event=calibration_complete domain=%s optimized_beta=%f iterations=%d converged=%s", ...)
```

### New Dependency: scipy

**Add to pyproject.toml:**
```toml
dependencies = [
    "jsonschema>=4.23.0",
    "matplotlib>=3.8.0",
    "pyarrow>=18.0.0",
    "pyyaml>=6.0.2",
    "scipy>=1.14.0",
]
```

scipy 1.14.0+ supports Python 3.13. Key APIs used:
- `scipy.optimize.minimize(fun, x0, method, bounds, options)` — general-purpose optimizer
- `method="L-BFGS-B"` — bounded quasi-Newton method (default, supports bounds on β)
- Alternative methods to consider: `"Nelder-Mead"` (gradient-free), `"Powell"` (gradient-free bounded)

**mypy override** — scipy does not ship type stubs:
```toml
[[tool.mypy.overrides]]
module = ["scipy", "scipy.*"]
ignore_missing_imports = true
```

**Import pattern in engine.py:**
```python
from scipy.optimize import minimize, OptimizeResult
```

### Key Imports from Discrete Choice Module

The calibration engine reuses logit functions directly — no reimplementation:

```python
from reformlab.discrete_choice.logit import compute_utilities, compute_probabilities
from reformlab.discrete_choice.types import CostMatrix, TasteParameters
```

These are **pure functions** with no side effects:
- `compute_utilities(cost_matrix: CostMatrix, taste_parameters: TasteParameters) -> pa.Table` — computes `V_ij = beta_cost × cost_ij`
- `compute_probabilities(utilities: pa.Table) -> pa.Table` — applies softmax with log-sum-exp trick, returns N×M probability table with row sums = 1.0

### Algorithm: Simulated Rate Computation

Given a CostMatrix (N × M), TasteParameters, and a from_states array (N,):

```
1. utilities = compute_utilities(cost_matrix, taste_params)  →  N × M table
2. probabilities = compute_probabilities(utilities)           →  N × M table (rows sum to 1.0)
3. For each unique from_state in targets:
   a. mask = pc.equal(from_states, from_state)               →  N boolean array
   b. For each to_state (alternative) in targets for this from_state:
      - prob_col = probabilities.column(to_state)            →  N float array
      - group_probs = pc.filter(prob_col, mask)              →  K float array (K = # households in group)
      - simulated_rate = pc.mean(group_probs).as_py()        →  scalar float
4. Return dict[(from_state, to_state)] → simulated_rate
```

**Use `pyarrow.compute` (imported as `pc`)** for efficient filtering and aggregation:
```python
import pyarrow.compute as pc

mask = pc.equal(from_states, pa.scalar(from_state_value, type=pa.utf8()))
group_probs = pc.filter(prob_col, mask)
simulated_rate = pc.mean(group_probs).as_py()
```

**Key insight:** Uses expected probabilities (not stochastic draws) for the objective function. This produces a smooth, differentiable objective suitable for gradient-based optimization. No random seed is needed within the objective function itself — the optimization is deterministic by construction.

### Algorithm: MSE Objective Function

```
Input: beta (scalar) — candidate beta_cost value
       targets — CalibrationTargetSet filtered to domain
       cost_matrix — N × M CostMatrix (fixed, pre-computed)
       from_states — N-element pa.Array (fixed)

1. taste = TasteParameters(beta_cost=beta)
2. simulated = compute_simulated_rates(cost_matrix, taste, from_states, alternative_ids)
3. total_weighted_error = 0.0
   total_weight = 0.0
   For each target t in domain_targets:
     sim_rate = simulated[(t.from_state, t.to_state)]
     total_weighted_error += t.weight × (sim_rate - t.observed_rate)²
     total_weight += t.weight
4. Return total_weighted_error / total_weight

Output: scalar MSE value (to minimize)
```

### Algorithm: Negative Log-Likelihood Objective

```
Input: same as MSE

1-2. Same as MSE (compute simulated rates)
3. eps = 1e-15  (clamping to avoid log(0))
   total_ll = 0.0
   For each target t:
     sim = clamp(simulated[(t.from_state, t.to_state)], eps, 1 - eps)
     obs = t.observed_rate
     total_ll += t.weight × (obs × log(sim) + (1 - obs) × log(1 - sim))
4. Return -total_ll  (minimize negative log-likelihood)

Output: scalar positive value (to minimize)
```

### Algorithm: CalibrationEngine.calibrate()

```python
def calibrate(self) -> CalibrationResult:
    # 1. Filter targets to domain
    domain_targets = self.config.targets.by_domain(self.config.domain)

    # 2. Validate inputs
    self._validate_inputs(domain_targets)

    # 3. Build objective function (closure)
    if self.config.objective_type == "mse":
        objective = build_mse_objective(domain_targets, self.config.cost_matrix, self.config.from_states)
    else:  # "log_likelihood"
        objective = build_log_likelihood_objective(domain_targets, self.config.cost_matrix, self.config.from_states)

    # 4. Run scipy.optimize.minimize
    result = minimize(
        objective,
        x0=[self.config.initial_beta],
        method=self.config.method,
        bounds=[(self.config.beta_bounds[0], self.config.beta_bounds[1])],
        options={
            "maxiter": self.config.max_iterations,
            "ftol": self.config.tolerance,
        },
    )

    # 5. Extract results
    optimized_beta = float(result.x[0])
    gradient_norm = None
    if hasattr(result, "jac") and result.jac is not None:
        gradient_norm = float(abs(result.jac[0]))

    # 6. Compute final simulated rates for comparison
    optimized_taste = TasteParameters(beta_cost=optimized_beta)
    final_rates = compute_simulated_rates(
        self.config.cost_matrix, optimized_taste,
        self.config.from_states, self.config.cost_matrix.alternative_ids,
    )

    # 7. Build per-target rate comparisons
    rate_comparisons = []
    for t in domain_targets.targets:
        key = (t.from_state, t.to_state)
        sim_rate = final_rates.get(key, 0.0)
        abs_err = abs(sim_rate - t.observed_rate)
        rate_comparisons.append(RateComparison(
            from_state=t.from_state, to_state=t.to_state,
            observed_rate=t.observed_rate, simulated_rate=sim_rate,
            absolute_error=abs_err,
            within_tolerance=abs_err <= self.config.rate_tolerance,
        ))

    # 8. Return CalibrationResult
    return CalibrationResult(
        optimized_parameters=optimized_taste,
        domain=self.config.domain,
        objective_type=self.config.objective_type,
        objective_value=float(result.fun),
        convergence_flag=bool(result.success),
        iterations=int(result.nit),
        gradient_norm=gradient_norm,
        method=self.config.method,
        rate_comparisons=tuple(rate_comparisons),
        all_within_tolerance=all(rc.within_tolerance for rc in rate_comparisons),
    )
```

**scipy.optimize.minimize notes:**
- Passes `NDArray` (shape `(1,)`) to objective function — extract `beta = x[0]`
- Returns `OptimizeResult` with: `.x` (solution array), `.fun` (objective value), `.success` (bool), `.nit` (iterations), `.jac` (gradient, may be None depending on method)
- `L-BFGS-B` supports bounds and computes approximate gradient → `.jac` is available
- `Nelder-Mead` does not compute gradient → `.jac` will not be present
- Always check `hasattr(result, "jac")` before accessing

### Hand-Computed Test Example

**Setup:** 3 households, 2 alternatives (A, B), beta = -0.01

| Household | from_state | cost_A | cost_B |
|-----------|-----------|--------|--------|
| 0         | petrol    | 100.0  | 200.0  |
| 1         | petrol    | 150.0  | 100.0  |
| 2         | diesel    | 200.0  | 300.0  |

**Utilities** (V = -0.01 × cost):
- H0: V_A = -1.0, V_B = -2.0
- H1: V_A = -1.5, V_B = -1.0
- H2: V_A = -2.0, V_B = -3.0

**Probabilities** (softmax with log-sum-exp):
- H0: P_A = 0.7311, P_B = 0.2689
- H1: P_A = 0.3775, P_B = 0.6225
- H2: P_A = 0.7311, P_B = 0.2689

**Simulated rates:**
- Group "petrol" (H0, H1): rate_A = (0.7311 + 0.3775) / 2 = 0.5543, rate_B = 0.4457
- Group "diesel" (H2): rate_A = 0.7311, rate_B = 0.2689

**MSE example** (observed: petrol→A=0.40, petrol→B=0.55, diesel→A=0.60):
```
MSE = ((0.5543 - 0.40)² + (0.4457 - 0.55)² + (0.7311 - 0.60)²) / 3
    = (0.0238 + 0.0109 + 0.0172) / 3
    = 0.0173
```

Use these values (with `pytest.approx(tolerance=1e-3)`) in test fixtures for `TestComputeSimulatedRates` and `TestMSEObjective`.

### Governance Integration Pattern

`CalibrationResult.to_governance_entry()`:
```python
def to_governance_entry(self, *, source_label: str = "calibration_engine") -> dict[str, Any]:
    return {
        "key": "calibration_result",
        "value": {
            "domain": self.domain,
            "optimized_beta_cost": self.optimized_parameters.beta_cost,
            "objective_type": self.objective_type,
            "final_objective_value": self.objective_value,
            "convergence_flag": self.convergence_flag,
            "iterations": self.iterations,
            "method": self.method,
            "all_within_tolerance": self.all_within_tolerance,
            "n_targets": len(self.rate_comparisons),
        },
        "source": source_label,
        "is_default": False,
    }
```

### Input Validation Rules

`CalibrationEngine._validate_inputs(domain_targets)` must check:

1. **Non-empty targets:** `len(domain_targets.targets) > 0` — raise `CalibrationOptimizationError(f"No calibration targets for domain={self.config.domain!r}")`
2. **Alternative IDs exist:** Every `target.to_state` must be in `self.config.cost_matrix.alternative_ids` — raise with the unknown to_state values listed
3. **From-states exist:** Every unique `target.from_state` must appear in `self.config.from_states` array — raise with the missing from_state values listed (use `pc.unique()` on from_states to get available values)
4. **Consistency:** `domain_targets.validate_consistency()` (already called by loader, but defensive re-check)

### Cross-Story Dependencies

| Story | Relationship |
|---|---|
| **14.2** | Direct import: `TasteParameters`, `CostMatrix`, `compute_utilities`, `compute_probabilities` |
| **14.3** | Vehicle alternative IDs define valid `to_state` values for vehicle domain cost matrix columns |
| **14.4** | Heating alternative IDs define valid `to_state` values for heating domain cost matrix columns |
| **15.1** | Direct import: `CalibrationTargetSet`, `CalibrationTarget`, `CalibrationTargetLoadError`, `CalibrationTargetValidationError` |
| **15.3** | Consumer — uses `CalibrationResult` and `CalibrationEngine` on holdout data |
| **15.4** | Consumer — records `CalibrationResult.to_governance_entry()` in run manifests |
| **15.5** | Consumer — notebook demo calls `CalibrationEngine.calibrate()` |

### Data Flow

```
Observed Data (CSV/YAML)       Pre-computed CostMatrix        Population from_states
        │                              │                              │
        ▼                              │                              │
  load_calibration_targets()           │                              │
        │                              │                              │
        ▼                              ▼                              ▼
  CalibrationTargetSet ──────► CalibrationConfig ◄─── pa.Array (from_states)
                                       │
                                       ▼
                               CalibrationEngine
                                       │
                                  calibrate()
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                   │
                    ▼                  ▼                   ▼
             _validate_inputs   build_objective    scipy.optimize.minimize
                                       │                   │
                              ┌────────┘                   │
                              ▼                            ▼
                    compute_simulated_rates()      optimization loop
                              │                    (calls objective N times)
                    ┌─────────┼──────────┐                │
                    ▼         ▼          ▼                ▼
              compute_    compute_   pc.filter +     OptimizeResult
              utilities   probs     pc.mean              │
              (14.2)      (14.2)                         ▼
                                              CalibrationResult
                                              (optimized β, diagnostics,
                                               rate_comparisons)
```

### Anti-Patterns from Story 15.1 (DO NOT REPEAT)

| Issue | Prevention |
|-------|-----------|
| Contract conflict between dataclass and schema | `CalibrationConfig` field types must match what `CalibrationResult` returns — verify with test |
| Missing floating-point tolerance | Simulated rates use PyArrow compute (double precision); rate comparisons use `abs_err <= rate_tolerance` (configurable) |
| Unclear error locations | All `CalibrationOptimizationError` messages must include: `domain=`, specific values that failed, and what was expected |
| Packaging issues | No new schema files or package data in this story — only Python modules |
| Docstring ordering | Module docstring first, then `from __future__ import annotations` (project convention from `discrete_choice/errors.py` pattern) |

### Project Structure Notes

- `engine.py` is a new file in the existing `src/reformlab/calibration/` module — consistent with adding `logit.py` to `discrete_choice/`
- Test file `tests/calibration/test_engine.py` mirrors the source — consistent with `tests/discrete_choice/test_logit.py`
- No new test fixture files needed — engine tests use inline PyArrow table construction
- `pyproject.toml` changes: add scipy to dependencies + mypy override
- No changes to `pyproject.toml` wheel includes (no new non-Python files)

### Testing Standards Summary

- Class-based test grouping: `TestComputeSimulatedRates`, `TestMSEObjective`, `TestLogLikelihoodObjective`, `TestCalibrationEngine`, `TestCalibrationEngineValidation`, `TestCalibrationEngineEdgeCases`
- Docstrings in Given/When/Then format
- Direct `assert` statements — no custom assertion helpers
- `pytest.raises(CalibrationOptimizationError, match=...)` for error cases
- `pytest.approx(expected, abs=1e-3)` for float comparisons (simulated rates have limited precision)
- Inline PyArrow table construction in fixtures (small 3×2 or 3×3 matrices)
- Reference story/AC IDs in test comments
- Hand-computed expected values for objective function tests (see test example above)
- Determinism test: call `calibrate()` twice with identical config, assert results are equal

### References

- [Source: docs/epics.md — Epic 15 / Story 15.2 acceptance criteria]
- [Source: docs/project-context.md — coding conventions, frozen dataclasses, PyArrow canonical type, scipy not yet a dependency]
- [Source: src/reformlab/discrete_choice/logit.py — compute_utilities(), compute_probabilities(), draw_choices()]
- [Source: src/reformlab/discrete_choice/types.py — TasteParameters, CostMatrix, ChoiceResult]
- [Source: src/reformlab/calibration/types.py — CalibrationTarget, CalibrationTargetSet]
- [Source: src/reformlab/calibration/errors.py — CalibrationError hierarchy]
- [Source: src/reformlab/calibration/loader.py — load_calibration_targets(), CALIBRATION_TARGET_SCHEMA]
- [Source: src/reformlab/calibration/schema/calibration-targets.schema.json — weight field already defined]
- [Source: src/reformlab/governance/manifest.py — AssumptionEntry TypedDict]
- [Source: src/reformlab/population/validation.py — to_governance_entry() pattern]
- [Source: _bmad-output/implementation-artifacts/15-1-define-calibration-target-format-and-load-observed-transition-rates.md — Story 15.1 completion notes]

## Dev Agent Record

### Agent Model Used

_(To be filled by dev agent)_

### Debug Log References

_(To be filled by dev agent)_

### Completion Notes List

_(To be filled by dev agent)_

### File List

New files:
- `src/reformlab/calibration/engine.py`
- `tests/calibration/test_engine.py`

Modified files:
- `src/reformlab/calibration/__init__.py` — add new exports
- `src/reformlab/calibration/types.py` — add CalibrationConfig, CalibrationResult, RateComparison; add weight to CalibrationTarget
- `src/reformlab/calibration/errors.py` — add CalibrationOptimizationError
- `src/reformlab/calibration/loader.py` — extract weight field from CSV/YAML
- `pyproject.toml` — add scipy dependency + mypy override
- `tests/calibration/conftest.py` — add engine-related fixtures
- `tests/calibration/test_types.py` — add new type tests
- `tests/calibration/test_errors.py` — add CalibrationOptimizationError test

### Change Log

_(To be filled by dev agent)_
