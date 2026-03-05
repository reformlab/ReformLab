

# Story 11.5: Implement IPF and conditional sampling merge methods

Status: complete

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform developer building the French household population pipeline,
I want IPF (Iterative Proportional Fitting) and conditional sampling merge methods implementing the existing `MergeMethod` protocol,
so that the population pipeline can produce merged populations that respect known marginal distributions (IPF) or leverage shared stratification variables (conditional sampling), enabling more realistic synthetic populations than uniform random matching alone.

## Acceptance Criteria

1. Given two tables and a set of known marginal constraints, when IPF is applied, then the merged population matches the target marginals within documented tolerances (IPF convergence tolerance is `1e-6` at the weight level; after integerization, per-category row counts match targets within ±1).
2. Given IPF output, when the assumption record is inspected, then it lists all marginal constraints used and the convergence status.
3. Given two tables with a conditioning variable (e.g., income bracket), when conditional sampling is applied, then matches are drawn within strata defined by the conditioning variable.
4. Given conditional sampling output, when the assumption record is inspected, then it states the conditioning variable and explains the conditional independence assumption.
5. Given both methods, when docstrings are read, then each includes a plain-language explanation suitable for a policy analyst (not just a statistician).

## Tasks / Subtasks

- [x] Task 1: Define IPF supporting types in `base.py` (AC: #1, #2)
  - [x] 1.1 Add `IPFConstraint` frozen dataclass to `src/reformlab/population/methods/base.py` with fields: `dimension: str` (column name in table_a to constrain), `targets: dict[str, float]` (category value -> target count/weight). Validate in `__post_init__` that `dimension` is a non-empty string and `targets` is non-empty with all values >= 0. Deep-copy `targets` dict via `object.__setattr__`.
  - [x] 1.2 Add `IPFResult` frozen dataclass to `base.py` with fields: `weights: tuple[float, ...]` (per-row IPF weights), `iterations: int` (iterations until convergence), `converged: bool`, `max_deviation: float` (maximum absolute deviation at termination). This captures convergence diagnostics for the assumption record.

- [x] Task 2: Add `MergeConvergenceError` to error hierarchy (AC: #1)
  - [x] 2.1 Add `MergeConvergenceError(MergeError)` to `src/reformlab/population/methods/errors.py` — raised when IPF fails to converge within `max_iterations`. Docstring: "Raised when an iterative merge method fails to converge within the configured iteration limit."

- [x] Task 3: Implement `IPFMergeMethod` — `ipf.py` (AC: #1, #2, #5)
  - [x] 3.1 Create `src/reformlab/population/methods/ipf.py` with module docstring referencing Story 11.5, FR38, FR39 — include pedagogical docstring explaining IPF in plain language:
    - What IPF does: adjusts row weights so that the merged population's marginal distributions match known targets (e.g., census totals by region, income distribution by bracket)
    - The assumption: the joint distribution between unconstrained variables follows the pattern in the seed data (table_a), adjusted only to match the specified marginals. This is a "minimum information" / maximum entropy approach
    - When appropriate: when you have reliable marginal distributions from census or administrative data that the merged population must respect
    - When problematic: when the seed data has structural zeros (categories with no observations) that should have non-zero representation, or when marginal targets are mutually inconsistent (different grand totals)
  - [x] 3.2 Implement `IPFMergeMethod` class with constructor:
    ```python
    def __init__(
        self,
        constraints: tuple[IPFConstraint, ...],
        max_iterations: int = 100,
        tolerance: float = 1e-6,
    ) -> None:
    ```
    Validate: `constraints` must be non-empty tuple, `max_iterations >= 1`, `tolerance > 0`. Store as instance attributes. No frozen dataclass for the method itself (it's a service object, not a value object).
  - [x] 3.3 Implement `name` property returning `"ipf"`
  - [x] 3.4 Implement private `_run_ipf(self, table_a: pa.Table) -> IPFResult` with this algorithm:
    1. Initialize weights: `[1.0] * table_a.num_rows`
    2. Validate constraint dimensions exist as columns in table_a — raise `MergeValidationError` if not
    3. Validate constraint targets: each target category must exist in the column values — log warning for categories not present (they cannot be satisfied), raise `MergeValidationError` if **all** categories in a constraint are missing
    4. IPF iteration loop (up to `max_iterations`):
       a. For each constraint `(dimension, targets)`:
          - Extract column values: `table_a.column(dimension).to_pylist()`
          - Compute current weighted totals per category: `current[cat] = sum(weights[k] for k where col[k] == cat)`
          - Compute adjustment factors: `factor[cat] = target[cat] / current[cat]` (if `current[cat] > 0`, else `factor = 1.0`)
          - Apply factors: `weights[k] *= factor[col[k]]`
       b. Compute max absolute deviation: `max(|current[cat] - target[cat]|)` across all constraints and categories
       c. If `max_deviation < tolerance`: converged = True, break
    5. Return `IPFResult(weights=tuple(weights), iterations=i+1, converged=converged, max_deviation=max_deviation)`
  - [x] 3.5 Implement private `_integerize_weights(self, weights: tuple[float, ...], target_count: int, rng: random.Random) -> list[int]` with this algorithm:
    1. Normalize weights so they sum to `target_count` (= `table_a.num_rows`, preserving original count)
    2. For each weight: `integer_part = floor(weight)`, `fractional = weight - integer_part`
    3. Deterministic probabilistic rounding: if `rng.random() < fractional`, add 1
    4. Return list of integer weights (each >= 0)
  - [x] 3.6 Implement `merge(self, table_a, table_b, config)` with this logic:
    1. Validate inputs: both tables must have `num_rows > 0` — raise `MergeValidationError` (same pattern as uniform)
    2. Apply `config.drop_right_columns` to table_b (same pattern as uniform)
    3. Check column name conflicts (same pattern as uniform)
    4. Run IPF: `ipf_result = self._run_ipf(table_a)`
    5. If not converged: raise `MergeConvergenceError` with summary="IPF did not converge", reason with iterations and max_deviation, fix suggesting increasing max_iterations or checking marginal consistency
    6. Integerize weights: `int_weights = self._integerize_weights(ipf_result.weights, table_a.num_rows, random.Random(config.seed))`
    7. Expand table_a: for each row `k`, repeat it `int_weights[k]` times. Build expanded row indices: `expanded_indices = [k for k, w in enumerate(int_weights) for _ in range(w)]`
    8. Guard: if `len(expanded_indices) == 0`, raise `MergeValidationError` with summary="IPF produced empty expansion", reason="All row weights integerized to 0 — no rows survive expansion", fix="Check constraint targets for extreme values or structural zeros"
    9. Create expanded table_a: `expanded_a = table_a.take(pa.array(expanded_indices))`
    10. Random matching: use `random.Random(config.seed + 1)` (different seed stream from integerization) to generate `expanded_a.num_rows` random indices into table_b (same pattern as uniform)
    11. Select matched rows: `matched_b = right_table.take(pa.array(b_indices))`
    12. Combine columns: same pattern as uniform (table_a columns first, then table_b columns)
    13. Build `MergeAssumption` with:
        - `method_name="ipf"`
        - `statement="The merged population is reweighted using Iterative Proportional Fitting so that marginal distributions match the specified targets — this assumes the joint distribution between unconstrained variables follows the seed pattern, adjusted only to match target marginals."`
        - `details={"table_a_rows": table_a.num_rows, "table_b_rows": table_b.num_rows, "expanded_rows": expanded_a.num_rows, "seed": config.seed, "constraints": [{"dimension": c.dimension, "targets": dict(c.targets)} for c in self._constraints], "iterations": ipf_result.iterations, "converged": ipf_result.converged, "max_deviation": ipf_result.max_deviation, "tolerance": self._tolerance, "dropped_right_columns": list(config.drop_right_columns)}`
    14. Return `MergeResult(table=merged, assumption=assumption)`
  - [x] 3.7 Use `logging.getLogger(__name__)` with structured `event=ipf_start`, `event=ipf_iteration`, `event=ipf_converged`/`event=ipf_not_converged`, `event=merge_start`, `event=merge_complete` log entries

- [x] Task 4: Implement `ConditionalSamplingMethod` — `conditional.py` (AC: #3, #4, #5)
  - [x] 4.1 Create `src/reformlab/population/methods/conditional.py` with module docstring referencing Story 11.5, FR38, FR39 — include pedagogical docstring explaining conditional sampling in plain language:
    - What it does: groups both tables by shared variable(s) (strata), then randomly matches rows only within the same group. This preserves the correlation between the stratification variable and all other variables
    - The assumption: conditional independence — within each stratum, the unique variables from table_a and table_b are assumed independent. The correlation between them is captured entirely by the stratification variable
    - When appropriate: when both datasets share a variable that is correlated with the unique variables in each dataset (e.g., income bracket correlates with both energy consumption and vehicle ownership)
    - When problematic: when the strata are too coarse (residual correlation within strata is large) or when some strata have very few observations in one table (small sample noise)
  - [x] 4.2 Implement `ConditionalSamplingMethod` class with constructor:
    ```python
    def __init__(
        self,
        strata_columns: tuple[str, ...],
    ) -> None:
    ```
    Validate: `strata_columns` must be a non-empty tuple of non-empty strings. Store as instance attribute.
  - [x] 4.3 Implement `name` property returning `"conditional"`
  - [x] 4.4 Implement `merge(self, table_a, table_b, config)` with this logic:
    1. Validate inputs: both tables must have `num_rows > 0` — raise `MergeValidationError`
    2. Validate strata columns exist in BOTH tables — raise `MergeValidationError` listing missing columns and which table they're missing from
    3. Compute effective drop list: `effective_drop = tuple(dict.fromkeys(self._strata_columns + config.drop_right_columns))` to deduplicate (a strata column may also appear in `drop_right_columns`). Remove effective_drop columns from table_b using iterative `remove_column()` (same pattern as uniform.py). Validate each column exists before removal — raise `MergeValidationError` for any `drop_right_columns` entry not found (strata columns are guaranteed present by step 2)
    4. Check column name conflicts on remaining columns (same pattern as uniform)
    5. Build stratum keys: for each row in table_a and table_b, compute a stratum key as a tuple of values from `strata_columns`
    6. Group table_a row indices by stratum: `strata_a: dict[tuple, list[int]]`
    7. Group table_b row indices by stratum: `strata_b: dict[tuple, list[int]]`
    8. Validate coverage: for each stratum present in table_a, check it exists in table_b — raise `MergeValidationError` if any table_a stratum has zero table_b donors (list the empty strata in the error message)
    9. Random matching within strata: `rng = random.Random(config.seed)`. For each stratum, for each table_a row index in that stratum: draw a random index from the table_b row indices in the same stratum (`rng.choice(strata_b[key])`)
    10. Collect all matched (a_idx, b_idx) pairs in original table_a row order
    11. Build merged table: table_a rows (in order) + matched table_b rows (strata columns removed from table_b side)
    12. Build `MergeAssumption` with:
        - `method_name="conditional"`
        - `statement="Rows are matched within strata defined by [{strata_column_list}] — this assumes that, within each stratum, the unique variables from each source are independent (conditional independence given the stratification variables)."`
        - `details={"table_a_rows": n, "table_b_rows": m, "seed": config.seed, "strata_columns": list(self._strata_columns), "strata_count": len(strata_a), "strata_sizes": {"|".join(str(x) for x in key): {"table_a": len(strata_a[key]), "table_b": len(strata_b[key])} for key in strata_a}, "dropped_right_columns": list(effective_drop_columns)}`
    13. Return `MergeResult(table=merged, assumption=assumption)`
  - [x] 4.5 Use `logging.getLogger(__name__)` with structured log entries: `event=merge_start method=conditional`, `event=strata_built strata_count=...`, `event=merge_complete`

- [x] Task 5: Update `__init__.py` exports (AC: all)
  - [x] 5.1 Export from `src/reformlab/population/methods/__init__.py`: add `IPFConstraint`, `IPFResult`, `IPFMergeMethod`, `ConditionalSamplingMethod`, `MergeConvergenceError` — update `__all__` listing
  - [x] 5.2 Export from `src/reformlab/population/__init__.py`: add same names — update `__all__` listing

- [x] Task 6: Create test fixtures for IPF and conditional sampling (AC: all)
  - [x] 6.1 Add to `tests/population/methods/conftest.py`:
    - `region_income_table` — `pa.Table` with columns: `household_id` (int64), `income_bracket` (utf8: "low"/"medium"/"high"), `region_code` (utf8: "84"/"11"/"75") — 10 rows, with known distribution: 3 low, 4 medium, 3 high; 4 region 84, 3 region 11, 3 region 75
    - `energy_vehicle_table` — `pa.Table` with columns: `income_bracket` (utf8), `vehicle_type` (utf8), `energy_kwh` (float64) — 12 rows, covering all 3 income brackets with known distribution
    - `simple_constraints` — `tuple[IPFConstraint, ...]` with one constraint: `IPFConstraint(dimension="income_bracket", targets={"low": 4.0, "medium": 3.0, "high": 3.0})` — shifts distribution from 3/4/3 to 4/3/3
    - `multi_constraints` — `tuple[IPFConstraint, ...]` with two constraints: income_bracket + region_code targets
    - `inconsistent_constraints` — constraints where totals across dimensions don't match (for convergence failure testing)

- [x] Task 7: Write comprehensive IPF tests (AC: #1, #2, #5)
  - [x] 7.1 `tests/population/methods/test_ipf.py`:
    - `TestIPFConstraint`: frozen, `__post_init__` validation (empty dimension raises ValueError, empty targets raises ValueError, negative target raises ValueError), targets deep-copied
    - `TestIPFResult`: frozen, holds weights + convergence diagnostics
    - `TestIPFMergeMethodProtocol`: `isinstance(IPFMergeMethod(...), MergeMethod)` passes
    - `TestIPFMergeMethodName`: `name` property returns `"ipf"`
    - `TestIPFMergeMethodConstructorValidation`: empty constraints raises ValueError, max_iterations < 1 raises ValueError, tolerance <= 0 raises ValueError
    - `TestIPFMergeMethodMerge`:
      - Basic merge with single constraint: region_income_table (10 rows) + vehicle_table → merged table with IPF-adjusted row counts, income_bracket distribution matches target within tolerance
      - Merged table has correct columns (table_a + table_b minus dropped)
      - Values from table_b come from actual rows in table_b (row-level coherence)
    - `TestIPFMergeMethodMarginalMatch`:
      - After merge, count rows per income_bracket → matches targets within tolerance (may differ by ±1 due to integerization)
      - Multi-constraint merge: both income_bracket AND region_code distributions match targets
    - `TestIPFMergeMethodConvergence`:
      - Convergent case: assumption.details contains `converged: True`, `iterations` < max_iterations
      - Non-convergent case: use `IPFMergeMethod(constraints=inconsistent_constraints, max_iterations=100, tolerance=1e-6)` — raises `MergeConvergenceError`
    - `TestIPFMergeMethodDeterminism`:
      - Same seed → identical merged table
      - Different seed → different row matching (at least one row differs)
    - `TestIPFMergeMethodAssumption`:
      - `assumption.method_name == "ipf"`
      - `assumption.statement` contains "Iterative Proportional Fitting" and "marginal"
      - `assumption.details` contains `constraints`, `iterations`, `converged`, `max_deviation`, `tolerance`, `expanded_rows`
      - `assumption.to_governance_entry()` returns correct structure
    - `TestIPFMergeMethodEmptyTable`:
      - Empty table_a → `MergeValidationError`
      - Empty table_b → `MergeValidationError`
    - `TestIPFMergeMethodColumnConflict`:
      - Overlapping columns → `MergeValidationError`
    - `TestIPFMergeMethodDropRightColumns`:
      - `drop_right_columns` works correctly
    - `TestIPFMergeMethodInvalidConstraintDimension`:
      - Constraint dimension not in table_a → `MergeValidationError`
    - `TestIPFMergeMethodMissingCategory`:
      - Constraint has a target category not present in table_a (but at least one IS present): merge completes successfully and a warning is logged (use `caplog` fixture)
    - `TestIPFMergeMethodDocstring`:
      - Class docstring non-empty, mentions "marginal" or "reweight"
      - Module docstring mentions "appropriate" and "problematic"

- [x] Task 8: Write comprehensive conditional sampling tests (AC: #3, #4, #5)
  - [x] 8.1 `tests/population/methods/test_conditional.py`:
    - `TestConditionalSamplingMethodProtocol`: `isinstance(ConditionalSamplingMethod(...), MergeMethod)` passes
    - `TestConditionalSamplingMethodName`: `name` property returns `"conditional"`
    - `TestConditionalSamplingMethodConstructorValidation`: empty strata_columns raises ValueError, empty string in strata_columns raises ValueError
    - `TestConditionalSamplingMethodMerge`:
      - Basic merge with single stratum column ("income_bracket"): region_income_table + energy_vehicle_table → merged table with same row count as table_a
      - All columns from both tables present (minus duplicated strata columns from table_b)
      - Row count equals table_a.num_rows
    - `TestConditionalSamplingMethodStrataRespected`:
      - For each row in merged table, the strata column value matches between the table_a side and the original table_b donor row — i.e., a "low" income household is matched with a "low" income vehicle/energy record
    - `TestConditionalSamplingMethodDeterminism`:
      - Same seed → identical merged table
      - Different seed → different row matching
    - `TestConditionalSamplingMethodColumnConflict`:
      - Overlapping non-strata columns → `MergeValidationError`
    - `TestConditionalSamplingMethodDropRightColumns`:
      - `drop_right_columns` works correctly
      - Strata columns in table_b are auto-dropped (not duplicated in output)
      - When a strata column name also appears in `config.drop_right_columns`, no error is raised (deduplication)
    - `TestConditionalSamplingMethodEmptyTable`:
      - Empty table_a → `MergeValidationError`
      - Empty table_b → `MergeValidationError`
    - `TestConditionalSamplingMethodMissingStrataColumn`:
      - Strata column not in table_a → `MergeValidationError` mentioning which table and column
      - Strata column not in table_b → `MergeValidationError`
    - `TestConditionalSamplingMethodEmptyStratum`:
      - table_a has stratum value "X" but table_b has no rows with "X" → `MergeValidationError` listing the empty stratum
    - `TestConditionalSamplingMethodAssumption`:
      - `assumption.method_name == "conditional"`
      - `assumption.statement` contains "conditional independence" and strata column names
      - `assumption.details` contains `strata_columns`, `strata_count`, `strata_sizes`, `seed`
      - `assumption.to_governance_entry()` returns correct structure
    - `TestConditionalSamplingMethodMultipleStrataColumns`:
      - Merge with 2 strata columns: matching respects both dimensions simultaneously
    - `TestConditionalSamplingMethodDocstring`:
      - Class docstring non-empty, mentions "conditional independence" or "strata"
      - Module docstring mentions "appropriate" and "problematic"

- [x] Task 9: Write tests for new error types and base types (AC: #1, #2)
  - [x] 9.1 Add to `tests/population/methods/test_errors.py`:
    - `TestMergeConvergenceError`: inherits `MergeError`, summary-reason-fix pattern, catchable as `MergeError`
  - [x] 9.2 Add to `tests/population/methods/test_base.py`:
    - `TestIPFConstraint`: frozen, validation, targets deep-copied
    - `TestIPFResult`: frozen, holds convergence diagnostics

- [x] Task 10: Run full test suite and lint (AC: all)
  - [x] 10.1 `uv run pytest tests/population/methods/` — all new tests pass
  - [x] 10.2 `uv run pytest tests/population/` — no regressions in loader or uniform merge tests
  - [x] 10.3 `uv run ruff check src/reformlab/population/methods/ tests/population/methods/` — no lint errors
  - [x] 10.4 `uv run mypy src/reformlab/population/methods/` — no mypy errors (strict mode)

## Dev Notes

### Architecture Context: Methods Library Extension

This story extends the `src/reformlab/population/methods/` subsystem created in Story 11.4. Two new files are added:

```
src/reformlab/population/methods/
├── __init__.py     ← Updated: add new exports
├── base.py         ← Updated: add IPFConstraint, IPFResult
├── errors.py       ← Updated: add MergeConvergenceError
├── uniform.py      ← UNCHANGED (Story 11.4)
├── ipf.py          ← NEW (this story)
└── conditional.py  ← NEW (this story)
```

### Protocol Compliance: Both Methods Follow Existing Pattern

Both `IPFMergeMethod` and `ConditionalSamplingMethod` implement the `MergeMethod` protocol established in Story 11.4 via duck typing (no inheritance). They follow the **exact same patterns** as `UniformMergeMethod`:

1. **`name` property** — returns short identifier (`"ipf"` or `"conditional"`)
2. **`merge(table_a, table_b, config)` signature** — identical to protocol
3. **Same validation order**: empty tables → drop_right_columns → column conflicts → method-specific logic
4. **Same assumption record pattern**: `MergeAssumption(method_name=..., statement=..., details=...)`
5. **Same error hierarchy**: `MergeValidationError` for input issues, `MergeConvergenceError` (new) for IPF non-convergence
6. **Same logging pattern**: `_logger = logging.getLogger(__name__)` with structured key=value events

### Method-Specific Configuration: Constructor Parameters

The `MergeConfig` dataclass is generic (seed, description, drop_right_columns). Method-specific configuration is passed via constructor parameters:

```python
# IPF: constraints and convergence parameters in constructor
ipf = IPFMergeMethod(
    constraints=(
        IPFConstraint(dimension="income_bracket", targets={"low": 4000, "medium": 3000, "high": 3000}),
        IPFConstraint(dimension="region_code", targets={"84": 3500, "11": 3000, "75": 3500}),
    ),
    max_iterations=100,
    tolerance=1e-6,
)
result = ipf.merge(table_a, table_b, MergeConfig(seed=42))

# Conditional: strata columns in constructor
cond = ConditionalSamplingMethod(strata_columns=("income_bracket",))
result = cond.merge(table_a, table_b, MergeConfig(seed=42))
```

This preserves the `MergeMethod` protocol signature while allowing method-specific parameterization.

### IPF Algorithm — Detailed Specification

**Purpose:** Iterative Proportional Fitting (raking) adjusts per-row weights in table_a so that weighted marginal distributions match target values. The reweighted rows are then integerized and matched with table_b rows.

**Algorithm (record-level IPF):**

```
Input: table_a (N rows), constraints [(dimension, {cat: target}), ...]
Output: weights[0..N-1]

1. weights = [1.0, 1.0, ..., 1.0]  (length N)

2. For iteration = 0 to max_iterations - 1:
     max_deviation = 0.0
     For each constraint (dimension, targets):
       col_values = table_a.column(dimension).to_pylist()

       # Compute current weighted totals
       current_totals = {}
       for k in range(N):
           cat = col_values[k]
           current_totals[cat] = current_totals.get(cat, 0.0) + weights[k]

       # Compute and apply adjustment factors
       for cat, target in targets.items():
           current = current_totals.get(cat, 0.0)
           if current > 0:
               factor = target / current
               max_deviation = max(max_deviation, abs(current - target))
           else:
               factor = 1.0
               max_deviation = max(max_deviation, target)
           # Apply factor to all rows in this category
           for k in range(N):
               if col_values[k] == cat:
                   weights[k] *= factor

     If max_deviation < tolerance:
       return IPFResult(weights, iteration+1, converged=True, max_deviation)

3. Return IPFResult(weights, max_iterations, converged=False, max_deviation)
```

**Integerization (controlled probabilistic rounding):**

```
Input: weights (floats summing to ~total), target_count, rng
Output: int_weights (integers summing to ~target_count)

1. scale = target_count / sum(weights)
2. scaled = [w * scale for w in weights]
3. For each scaled weight:
     integer_part = floor(scaled_w)
     fractional = scaled_w - integer_part
     if rng.random() < fractional:
         int_weight = integer_part + 1
     else:
         int_weight = integer_part
4. Return int_weights
```

**Seed stream separation:** The `config.seed` is used for integerization rounding. A derived seed `config.seed + 1` is used for table_b matching. This prevents correlation between the rounding decisions and the matching decisions. Use `random.Random(seed)` for each stream (stdlib, no numpy).

**Performance note:** The IPF loop is O(N * D * I) where N = rows, D = constraint dimensions, I = iterations. For 10,000 rows, 3 dimensions, 50 iterations = 1.5M operations. Pure Python is sufficient for laptop-scale data.

### Conditional Sampling Algorithm — Detailed Specification

**Purpose:** Groups both tables by shared column(s), then performs uniform random matching within each group (stratum). This preserves the correlation between the stratification variable and all other variables.

**Algorithm:**

```
Input: table_a (N rows), table_b (M rows), strata_columns, seed

1. Compute stratum keys for each row:
     key_a[k] = tuple(table_a.column(c)[k] for c in strata_columns)
     key_b[k] = tuple(table_b.column(c)[k] for c in strata_columns)

2. Group row indices by stratum:
     strata_a = {key: [row_indices...]} for each unique key in key_a
     strata_b = {key: [row_indices...]} for each unique key in key_b

3. Validate: for each key in strata_a, key must exist in strata_b
     (raise MergeValidationError if not)

4. Match within strata:
     rng = random.Random(seed)
     matched_b_indices = []
     for k in range(N):
         key = key_a[k]
         donor_pool = strata_b[key]
         matched_b_indices.append(rng.choice(donor_pool))

5. Build right table:
     Compute effective_drop = tuple(dict.fromkeys(strata_columns + config.drop_right_columns))
     Remove effective_drop columns from table_b using iterative remove_column() (same pattern as uniform.py)
     right_table = table_b with effective_drop columns removed
     matched_right = right_table.take(pa.array(matched_b_indices))

6. Combine: table_a columns + matched_right columns
```

**Auto-dropping strata columns from table_b:** Strata columns exist in both tables by definition. To avoid duplicate columns in the output, the method automatically adds strata column names to the effective drop list (in addition to `config.drop_right_columns`). If a strata column is already in `drop_right_columns`, it is not dropped twice.

**Stratum key computation:** Use `tuple(table.column(c)[k].as_py() for c in strata_columns)` to build hashable stratum keys. This works for any column type (utf8, int64, etc.).

### IPFConstraint and IPFResult — Exact Specifications

```python
@dataclass(frozen=True)
class IPFConstraint:
    """A marginal constraint for IPF.

    Specifies that the weighted count of rows where ``dimension``
    equals each category key should match the corresponding target value.

    Attributes:
        dimension: Column name in table_a to constrain.
        targets: Mapping from category value to target count/weight.
            All values must be >= 0.
    """

    dimension: str
    targets: dict[str, float]

    def __post_init__(self) -> None:
        if not self.dimension:
            msg = "dimension must be a non-empty string"
            raise ValueError(msg)
        if not self.targets:
            msg = "targets must be a non-empty dict"
            raise ValueError(msg)
        for cat, val in self.targets.items():
            if val < 0:
                msg = f"target for {cat!r} must be >= 0, got {val}"
                raise ValueError(msg)
        object.__setattr__(self, "targets", dict(self.targets))


@dataclass(frozen=True)
class IPFResult:
    """Convergence diagnostics from an IPF run.

    Attributes:
        weights: Per-row weights after IPF adjustment.
        iterations: Number of iterations performed.
        converged: Whether convergence was reached within tolerance.
        max_deviation: Maximum absolute deviation at termination.
    """

    weights: tuple[float, ...]
    iterations: int
    converged: bool
    max_deviation: float
```

### Error Hierarchy Extension

```python
# Added to src/reformlab/population/methods/errors.py

class MergeConvergenceError(MergeError):
    """Raised when an iterative merge method fails to converge.

    Triggered by: IPF exceeding max_iterations without reaching
    the tolerance threshold. Often caused by inconsistent marginal
    constraints (target totals that cannot be simultaneously satisfied).
    """
```

### No New Dependencies Required

All implementation uses existing dependencies and stdlib:

- `random` — deterministic random number generation (stdlib)
- `math` — `floor()` for integerization (stdlib)
- `pyarrow` — table operations, `take()` for row selection (existing dependency)
- `logging` — structured logging (stdlib)

Do **not** introduce `numpy`, `scipy`, `pandas`, or any new dependency.

**Import pattern:** `import pyarrow as pa` at module level in `ipf.py` and `conditional.py` (runtime dependency, same as `uniform.py`). In `base.py`, `pyarrow` stays under `TYPE_CHECKING` guard.

### Test Fixtures — Concrete Data

```python
# Additional fixtures in tests/population/methods/conftest.py

@pytest.fixture()
def region_income_table() -> pa.Table:
    """Table with known income_bracket and region_code distributions (10 rows).

    Distribution: income_bracket: low=3, medium=4, high=3
                  region_code: 84=4, 11=3, 75=3
    """
    return pa.table({
        "household_id": pa.array(list(range(1, 11)), type=pa.int64()),
        "income_bracket": pa.array(
            ["low", "low", "low", "medium", "medium", "medium", "medium",
             "high", "high", "high"],
            type=pa.utf8(),
        ),
        "region_code": pa.array(
            ["84", "84", "11", "84", "11", "75", "84", "11", "75", "75"],
            type=pa.utf8(),
        ),
    })


@pytest.fixture()
def energy_vehicle_table() -> pa.Table:
    """Table with income_bracket (shared), vehicle_type, energy_kwh (12 rows).

    Covers all 3 income brackets: low=4, medium=4, high=4.
    """
    return pa.table({
        "income_bracket": pa.array(
            ["low", "low", "low", "low",
             "medium", "medium", "medium", "medium",
             "high", "high", "high", "high"],
            type=pa.utf8(),
        ),
        "vehicle_type": pa.array(
            ["diesel", "diesel", "essence", "ev",
             "essence", "hybrid", "ev", "diesel",
             "ev", "ev", "hybrid", "essence"],
            type=pa.utf8(),
        ),
        "energy_kwh": pa.array(
            [8500.0, 9200.0, 7800.0, 3200.0,
             7200.0, 5100.0, 3000.0, 8800.0,
             2800.0, 3100.0, 4900.0, 6500.0],
            type=pa.float64(),
        ),
    })


@pytest.fixture()
def simple_constraints() -> tuple[IPFConstraint, ...]:
    """Single IPF constraint shifting income_bracket distribution."""
    return (
        IPFConstraint(
            dimension="income_bracket",
            targets={"low": 4.0, "medium": 3.0, "high": 3.0},
        ),
    )


@pytest.fixture()
def multi_constraints() -> tuple[IPFConstraint, ...]:
    """Two IPF constraints: income_bracket + region_code."""
    return (
        IPFConstraint(
            dimension="income_bracket",
            targets={"low": 4.0, "medium": 3.0, "high": 3.0},
        ),
        IPFConstraint(
            dimension="region_code",
            targets={"84": 3.0, "11": 4.0, "75": 3.0},
        ),
    )


@pytest.fixture()
def inconsistent_constraints() -> tuple[IPFConstraint, ...]:
    """Two constraints with mismatched grand totals — reliably causes non-convergence.

    income_bracket targets sum to 10 (matches 10-row table).
    region_code targets sum to 30 (3x mismatch forces perpetual oscillation).
    With 100 iterations at tolerance=1e-6, IPF cannot converge.
    """
    return (
        IPFConstraint(
            dimension="income_bracket",
            targets={"low": 4.0, "medium": 3.0, "high": 3.0},
        ),
        IPFConstraint(
            dimension="region_code",
            targets={"84": 10.0, "11": 10.0, "75": 10.0},
        ),
    )
```

### Test Pattern to Follow (from Story 11.4)

Follow the exact test structure from `tests/population/methods/test_uniform.py`:

1. **Class-based grouping** by feature/responsibility
2. **AC references in class docstrings**
3. **Direct assertions** — `assert` statements, `pytest.raises(ExceptionClass, match=...)` for errors
4. **Fixtures via conftest** — injected by parameter name
5. **Frozen dataclass tests** — verify immutability with `pytest.raises(AttributeError)`
6. **Determinism tests** — same seed → identical result, different seed → different
7. **Docstring tests** — verify pedagogical content is present

### IPF Marginal Matching Tolerance in Tests

Due to integerization (probabilistic rounding of fractional weights), the output row counts per category will not match targets exactly. Tests should allow ±1 tolerance:

```python
# Example test pattern for marginal matching
counts = {}
for val in result.table.column("income_bracket").to_pylist():
    counts[val] = counts.get(val, 0) + 1
# Target was {"low": 4.0, "medium": 3.0, "high": 3.0}
assert abs(counts.get("low", 0) - 4) <= 1
assert abs(counts.get("medium", 0) - 3) <= 1
assert abs(counts.get("high", 0) - 3) <= 1
```

### Conditional Sampling: Strata Column Auto-Drop Behavior

The conditional sampling method automatically removes strata columns from the table_b side of the merge to prevent column name conflicts. This is a semantic decision: the strata columns already exist in table_a, so duplicating them would be redundant and would trigger the column conflict check.

The auto-drop is **in addition to** any `config.drop_right_columns` specified by the caller. The effective drop list is the union of both.

### Downstream Dependencies

Story 11.5 is consumed by:

- **Story 11.6** (PopulationPipeline) — composes loaders + methods, calls `merge()` in sequence, collects `MergeAssumption` records
- **Story 11.7** (Validation) — validates merged population against marginals (IPF output should pass validation by construction)
- **Story 11.8** (Notebook) — demonstrates all three merge methods with plain-language explanations, showing progressive improvement from uniform → conditional → IPF

### Project Structure Notes

**New files (4):**
- `src/reformlab/population/methods/ipf.py`
- `src/reformlab/population/methods/conditional.py`
- `tests/population/methods/test_ipf.py`
- `tests/population/methods/test_conditional.py`

**Modified files (7):**
- `src/reformlab/population/methods/base.py` — add `IPFConstraint`, `IPFResult`
- `src/reformlab/population/methods/errors.py` — add `MergeConvergenceError`
- `src/reformlab/population/methods/__init__.py` — add new exports, update `__all__`
- `src/reformlab/population/__init__.py` — add new exports, update `__all__`
- `tests/population/methods/conftest.py` — add new fixtures
- `tests/population/methods/test_base.py` — add `TestIPFConstraint`, `TestIPFResult`
- `tests/population/methods/test_errors.py` — add `TestMergeConvergenceError`

**No changes** to `pyproject.toml` (no new dependencies, no new markers needed)

### Alignment with Project Conventions

All rules from `project-context.md` apply:

- Every file starts with `from __future__ import annotations`
- `if TYPE_CHECKING:` guards for annotation-only imports (in `base.py` only — `ipf.py` and `conditional.py` use `pyarrow` at runtime)
- Frozen dataclasses as default (`@dataclass(frozen=True)`) for `IPFConstraint`, `IPFResult`
- Protocols, not ABCs — new methods satisfy `MergeMethod` protocol via duck typing
- Subsystem-specific exceptions (`MergeConvergenceError`, not bare `Exception`)
- `dict[str, Any]` for metadata bags with stable string-constant keys
- `tuple[...]` for immutable sequences (`IPFConstraint.targets` stored as dict but deep-copied; `IPFResult.weights` as tuple)
- `X | None` union syntax, not `Optional[X]`
- Module-level docstrings referencing story/FR
- `logging.getLogger(__name__)` with structured key=value format
- `# ====...====` section separators for major sections within longer modules

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#New-Subsystem-Population-Generation] — Directory structure, MergeMethod protocol specification
- [Source: _bmad-output/planning-artifacts/epics.md#BKL-1105] — Story definition and acceptance criteria
- [Source: _bmad-output/planning-artifacts/prd.md#FR38] — "System provides a library of statistical methods for merging datasets that do not share the same sample (uniform distribution, IPF, conditional sampling, statistical matching)"
- [Source: _bmad-output/planning-artifacts/prd.md#FR39] — "Analyst can choose which merge method to apply at each dataset join, with plain-language explanation of the assumption"
- [Source: _bmad-output/project-context.md#Python-Language-Rules] — Frozen dataclasses, Protocols, `from __future__ import annotations`
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules] — PyArrow canonical data type, no pandas in core logic
- [Source: src/reformlab/population/methods/base.py] — MergeMethod protocol, MergeConfig, MergeAssumption, MergeResult (Story 11.4)
- [Source: src/reformlab/population/methods/uniform.py] — UniformMergeMethod implementation pattern to follow
- [Source: src/reformlab/population/methods/errors.py] — MergeError hierarchy pattern (summary-reason-fix)
- [Source: src/reformlab/governance/manifest.py#AssumptionEntry] — TypedDict with key/value/source/is_default; JSON-compatibility validation
- [Source: tests/population/methods/test_uniform.py] — Test patterns: class-based grouping, fixture injection, direct assertions
- [Source: tests/population/methods/conftest.py] — Existing test fixtures
- [Source: _bmad-output/implementation-artifacts/11-4-define-mergemethod-protocol-and-uniform-distribution-method.md] — Previous story (protocol reference, implementation patterns)

## File List

**New files (4):**
- `src/reformlab/population/methods/ipf.py`
- `src/reformlab/population/methods/conditional.py`
- `tests/population/methods/test_ipf.py`
- `tests/population/methods/test_conditional.py`

**Modified files (7):**
- `src/reformlab/population/methods/base.py` — add `IPFConstraint`, `IPFResult`
- `src/reformlab/population/methods/errors.py` — add `MergeConvergenceError`
- `src/reformlab/population/methods/__init__.py` — add new exports
- `src/reformlab/population/__init__.py` — add new exports
- `tests/population/methods/conftest.py` — add new fixtures
- `tests/population/methods/test_base.py` — add new type tests
- `tests/population/methods/test_errors.py` — add convergence error tests

## Dev Agent Record

### Implementation Plan

Implemented all 10 tasks in sequence following the story spec exactly:

1. Added `IPFConstraint` and `IPFResult` frozen dataclasses to `base.py` with validation
2. Added `MergeConvergenceError` to error hierarchy in `errors.py`
3. Implemented `IPFMergeMethod` in `ipf.py` — record-level IPF algorithm with weight integerization and seed-stream separation
4. Implemented `ConditionalSamplingMethod` in `conditional.py` — stratum-based matching with auto-drop of strata columns from table_b
5. Updated both `__init__.py` files with new exports
6. Created test fixtures (region_income_table, energy_vehicle_table, simple/multi/inconsistent constraints)
7. Wrote 24 IPF tests covering protocol, name, constructor validation, merge, marginal matching, convergence, determinism, assumptions, empty tables, column conflicts, drop_right_columns, invalid dimensions, missing categories, docstrings
8. Wrote 28 conditional sampling tests covering protocol, name, constructor validation, merge, strata respected, determinism, column conflicts, drop_right_columns (auto-drop + dedup), empty tables, missing strata columns, empty strata, assumptions, multiple strata columns, docstrings
9. Added `TestMergeConvergenceError` (4 tests), `TestIPFConstraint` (7 tests), `TestIPFResult` (3 tests) to existing test files
10. All 122 method tests pass, 307 total population tests pass, ruff clean, mypy strict clean

### Completion Notes

All 5 acceptance criteria satisfied:
- AC #1: IPF matches marginals within ±1 (integerization tolerance), convergence at 1e-6
- AC #2: Assumption record lists all constraints, iterations, convergence status, max_deviation
- AC #3: Conditional sampling matches within strata — verified via row-level coherence tests
- AC #4: Assumption record states conditioning variable and conditional independence assumption
- AC #5: Both module and class docstrings include plain-language explanations with "appropriate"/"problematic" sections

No new dependencies. No changes to pyproject.toml. Both methods follow the exact same patterns as UniformMergeMethod (validation order, error hierarchy, logging, assumption records).

## Change Log

- 2026-03-03: Story created by create-story workflow — comprehensive developer context with IPF algorithm specification (record-level reweighting + integerization + matching), conditional sampling algorithm (stratum-based matching with auto-drop), new supporting types (IPFConstraint, IPFResult, MergeConvergenceError), test fixture designs, downstream dependency mapping, and plain-language pedagogical explanations for both methods.
- 2026-03-03: Story implemented — all 10 tasks complete, 122 tests passing, ruff/mypy clean. 4 new files, 7 modified files.
