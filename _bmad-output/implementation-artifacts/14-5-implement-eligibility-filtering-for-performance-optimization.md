

# Story 14.5: Implement Eligibility Filtering for Performance Optimization

Status: dev-complete

## Story

As a **platform developer**,
I want eligibility filtering that restricts population expansion to only eligible households per decision domain,
so that multi-year simulations with 100k+ households complete within acceptable performance budgets by avoiding unnecessary computation for households that don't face a given decision.

## Acceptance Criteria

1. **AC-1: EligibilityRule and EligibilityFilter types** — `EligibilityRule` is a frozen dataclass with fields: `column: str`, `operator: str`, `threshold: int | float | str`, `description: str` (default `""`). Supported operators: `"gt"`, `"ge"`, `"lt"`, `"le"`, `"eq"`, `"ne"`. Invalid operator raises `DiscreteChoiceError` at construction time (`__post_init__`). `EligibilityFilter` is a frozen dataclass with fields: `rules: tuple[EligibilityRule, ...]`, `logic: str` (default `"all"` for AND, also accepts `"any"` for OR), `default_choice: str` (default `"keep_current"`), `entity_key: str` (default `"menage"`), `description: str` (default `""`). Invalid logic value raises `DiscreteChoiceError` at construction. Both types use frozen dataclasses without `__slots__` (intentional for these config/payload types; step classes like `DiscreteChoiceStep` use `__slots__`, but config and state-payload types do not).

2. **AC-2: evaluate_eligibility function** — `evaluate_eligibility(table: pa.Table, eligibility_filter: EligibilityFilter) -> pa.ChunkedArray` evaluates all rules against the entity table and returns a boolean mask (True = eligible). Rules are combined with AND logic (`logic="all"`) or OR logic (`logic="any"`). If a rule's `column` is not in the table, raise `DiscreteChoiceError` with the column name and available columns. If `rules` is empty, all households are eligible (returns all-True array). Uses PyArrow compute functions (`pyarrow.compute.greater`, etc.) for efficient evaluation at 100k+ scale.

3. **AC-3: filter_population_by_eligibility function** — `filter_population_by_eligibility(population: PopulationData, eligible_mask: pa.ChunkedArray, entity_key: str) -> tuple[PopulationData, tuple[int, ...]]` filters the `entity_key` table in the population using `pa.Table.filter()` and returns both the filtered `PopulationData` and a tuple of original row indices of eligible households. Only the `entity_key` table is filtered; other entity tables are excluded from the filtered population (the expansion only needs the decision-relevant entity table). Input population is not modified.

4. **AC-4: DiscreteChoiceStep eligibility integration** — `DiscreteChoiceStep.__init__` accepts an optional `eligibility_filter: EligibilityFilter | None = None` parameter. When provided:
   - Before expansion, the step evaluates `evaluate_eligibility()` against `population.tables[entity_key]` where `entity_key` comes from `eligibility_filter.entity_key`.
   - The population is filtered to eligible households only via `filter_population_by_eligibility()`.
   - `expand_population()` receives the filtered population (N' households instead of N).
   - An `EligibilityInfo` frozen dataclass is stored in `state.data[DISCRETE_CHOICE_ELIGIBILITY_KEY]` containing: `n_total` (N), `n_eligible` (N'), `eligible_indices` (tuple of original row indices), `default_choice`, `filter_description`, `alternative_ids`, `filter_rules` (the rules from the `EligibilityFilter`, for manifest auditability).
   - Metadata in `DISCRETE_CHOICE_METADATA_KEY` is extended with: `eligibility_n_total` (int), `eligibility_n_eligible` (int), `eligibility_n_ineligible` (int), `eligibility_filter_description` (str).
   - When `eligibility_filter` is `None`, behavior is identical to the current implementation (full N × M expansion, no `EligibilityInfo` stored).

5. **AC-5: EligibilityMergeStep** — `EligibilityMergeStep` implements the `OrchestratorStep` protocol. Default `name="eligibility_merge"`, `depends_on=("logit_choice",)`. It reads `ChoiceResult` (N' entries) from `state.data[DISCRETE_CHOICE_RESULT_KEY]` and `EligibilityInfo` from `state.data[DISCRETE_CHOICE_ELIGIBILITY_KEY]`. It produces a full N-entry `ChoiceResult` where:
   - Eligible household i (at eligible_indices[j]) gets the logit choice from position j.
   - Ineligible household i gets `default_choice` with probability 1.0 for the default alternative and 0.0 for all others, and utility 0.0 for all alternatives.
   - The merged `ChoiceResult` passes `__post_init__` validation (probability rows sum to 1.0, correct column names, correct length).
   - If `DISCRETE_CHOICE_ELIGIBILITY_KEY` is not in `state.data` (no eligibility filtering was applied), the step passes through unchanged (returns state as-is). This makes the step safe to always include in a pipeline.
   - The merged `ChoiceResult` replaces the filtered one in `state.data[DISCRETE_CHOICE_RESULT_KEY]`.

6. **AC-6: Performance scaling** — Given a population of 100k households where 30k are eligible for a vehicle choice with 6 alternatives, when expanded, then the expanded population is 180k rows (30k × 6), not 600k rows (100k × 6). Given eligibility filtering, when a 10-year run with 100k households completes, then adapter computation scales with N' × M (eligible × alternatives), not N × M. A performance test validates that expanded row count equals `n_eligible × n_alternatives`.

7. **AC-7: Ineligible household state preservation** — Given a household that is not eligible for a decision domain, when the full pipeline executes (DiscreteChoiceStep → LogitChoiceStep → EligibilityMergeStep → StateUpdateStep), then the household's `chosen` value is `default_choice` (e.g., `"keep_current"`), its population attributes are unchanged, and no vintage entry is created for it. The state update step requires no modifications — it already handles `"keep_current"` as a no-op for attributes.

8. **AC-8: Manifest and metadata integration** — Given eligibility rules, when the DiscreteChoiceStep stores metadata, then the metadata dict contains: `eligibility_n_total`, `eligibility_n_eligible`, `eligibility_n_ineligible`, and `eligibility_filter_description`. Given eligibility filtering is applied, when `EligibilityInfo` is stored in `state.data`, then it contains all data needed for manifest documentation: the structured rules (`filter_rules`), eligibility counts (`n_total`, `n_eligible`), and human-readable description (`filter_description`). This enables Story 14.6 to surface eligibility context in run manifests without requiring further state access.

9. **AC-9: EligibilityInfo type** — `EligibilityInfo` is a frozen dataclass with fields: `n_total: int`, `n_eligible: int`, `eligible_indices: tuple[int, ...]`, `default_choice: str`, `filter_description: str`, `alternative_ids: tuple[str, ...]`, `filter_rules: tuple[EligibilityRule, ...]`. The `filter_rules` field carries the originating rule definitions (column, operator, threshold) so that manifest documentation in Story 14.6 can reconstruct which eligibility criteria were applied. Stored under `DISCRETE_CHOICE_ELIGIBILITY_KEY = "discrete_choice_eligibility"` in `YearState.data`.

10. **AC-10: Edge cases** — All-ineligible population (N' = 0): produces empty cost matrix, empty logit choices, merge step assigns default_choice to all N households. All-eligible population (N' = N): identical to no filtering (merge is 1:1 mapping). Empty rules tuple: all households eligible. Single-rule filter: works without composition logic.

## Tasks / Subtasks

- [x] Task 1: Create `eligibility.py` with types (AC: 1, 9)
  - [x] 1.1: Define `VALID_OPERATORS` frozenset: `{"gt", "ge", "lt", "le", "eq", "ne"}`
  - [x] 1.2: Define `VALID_LOGIC` frozenset: `{"all", "any"}`
  - [x] 1.3: Implement `EligibilityRule` frozen dataclass with `__post_init__` validating `operator in VALID_OPERATORS`
  - [x] 1.4: Implement `EligibilityFilter` frozen dataclass with `__post_init__` validating `logic in VALID_LOGIC`
  - [x] 1.5: Implement `EligibilityInfo` frozen dataclass (state payload type) with `filter_rules: tuple[EligibilityRule, ...]` for manifest auditability
  - [x] 1.6: Define `DISCRETE_CHOICE_ELIGIBILITY_KEY = "discrete_choice_eligibility"` state key constant
  - [x] 1.7: Add module docstring referencing Story 14-5 and FR48

- [x] Task 2: Implement `evaluate_eligibility()` function (AC: 2)
  - [x] 2.1: Validate all rule columns exist in table; raise `DiscreteChoiceError` if not
  - [x] 2.2: Apply each rule using PyArrow compute functions: `pc.greater`, `pc.greater_equal`, `pc.less`, `pc.less_equal`, `pc.equal`, `pc.not_equal`
  - [x] 2.3: Combine masks: AND (`pc.and_`) for `logic="all"`, OR (`pc.or_`) for `logic="any"`
  - [x] 2.4: Handle empty rules: return all-True mask (`pa.array([True] * n)`)
  - [x] 2.5: Return `pa.ChunkedArray` (result of `pa.Table.filter` operations)

- [x] Task 3: Implement `filter_population_by_eligibility()` function (AC: 3)
  - [x] 3.1: Validate `entity_key` exists in `population.tables`; raise `DiscreteChoiceError` if not
  - [x] 3.2: Filter entity table using `table.filter(eligible_mask)`
  - [x] 3.3: Build `eligible_indices` tuple from mask
  - [x] 3.4: Return new `PopulationData` with only the `entity_key` table (other tables excluded) and original metadata
  - [x] 3.5: Input population is not modified (immutable pattern)

- [x] Task 4: Modify `DiscreteChoiceStep` to support eligibility filtering (AC: 4)
  - [x] 4.1: Add `eligibility_filter: EligibilityFilter | None = None` to `__init__` (add to `__slots__`)
  - [x] 4.2: In `execute()`, if filter provided: evaluate eligibility, filter population, store `EligibilityInfo` in state
  - [x] 4.3: Pass filtered population (N' rows) to `expand_population()` instead of full population
  - [x] 4.4: Extend metadata with eligibility counts (`eligibility_n_total`, `eligibility_n_eligible`, `eligibility_n_ineligible`, `eligibility_filter_description`)
  - [x] 4.5: Log eligibility counts in structured key=value format: `n_total`, `n_eligible`, `event=eligibility_evaluated`
  - [x] 4.6: When filter is None, behavior is identical to current implementation (no `EligibilityInfo` stored)

- [x] Task 5: Implement `EligibilityMergeStep` (AC: 5)
  - [x] 5.1: Class with `__slots__` implementing `OrchestratorStep` protocol
  - [x] 5.2: Constructor: `name`, `depends_on`, `description`
  - [x] 5.3: `execute()`: read `EligibilityInfo` from state; if absent, return state unchanged (pass-through)
  - [x] 5.4: Read `ChoiceResult` (N' entries) from `DISCRETE_CHOICE_RESULT_KEY`
  - [x] 5.5: Build full N-entry arrays: `chosen`, `probabilities`, `utilities`
  - [x] 5.6: For eligible household at `eligible_indices[j]`: copy logit result from position j
  - [x] 5.7: For ineligible households: set `chosen=default_choice`, probability 1.0 for default / 0.0 for others, utility 0.0 for all
  - [x] 5.8: Create merged `ChoiceResult` (must pass `__post_init__` validation)
  - [x] 5.9: Store merged ChoiceResult, remove `EligibilityInfo` from state (consumed), extend metadata with `eligibility_merge_n_defaulted`
  - [x] 5.10: Structured logging: `n_total`, `n_eligible`, `n_defaulted`, `default_choice`, `event=eligibility_merge_complete`

- [x] Task 6: Update `__init__.py` with new exports (AC: all)
  - [x] 6.1: Export `EligibilityRule`, `EligibilityFilter`, `EligibilityInfo` from `eligibility`
  - [x] 6.2: Export `evaluate_eligibility`, `filter_population_by_eligibility` from `eligibility`
  - [x] 6.3: Export `EligibilityMergeStep`, `DISCRETE_CHOICE_ELIGIBILITY_KEY` from `eligibility`

- [x] Task 7: Write tests (AC: all)
  - [x] 7.1: `test_eligibility.py` — `TestEligibilityRule`: construction, operator validation, invalid operator raises, frozen
  - [x] 7.2: `test_eligibility.py` — `TestEligibilityFilter`: construction, logic validation, invalid logic raises, defaults, frozen
  - [x] 7.3: `test_eligibility.py` — `TestEligibilityInfo`: construction, frozen
  - [x] 7.4: `test_eligibility.py` — `TestEvaluateEligibility`: single rule (gt, ge, lt, le, eq, ne), multiple rules with AND, multiple rules with OR, missing column error, empty rules → all eligible, all-True result, all-False result, mixed result, type variations (int/float/str thresholds)
  - [x] 7.5: `test_eligibility.py` — `TestFilterPopulation`: correct filtering, eligible indices, entity key not found error, input not modified, empty eligible (N'=0), all eligible (N'=N)
  - [x] 7.6: `test_eligibility.py` — `TestEligibilityMergeStep`: protocol compliance, StepRegistry registration, pass-through when no eligibility info, merge N' → N with correct chosen/probabilities/utilities, all-eligible merge (1:1), all-ineligible merge (all defaults), ChoiceResult validation passes, state immutability, metadata extension
  - [x] 7.7: `test_eligibility.py` — `TestDiscreteChoiceStepWithEligibility`: step with filter expands only eligible, step without filter expands all (backward compat), EligibilityInfo stored in state, metadata has eligibility counts, adapter receives N'×M rows (not N×M)
  - [x] 7.8: `test_eligibility.py` — Full pipeline integration: `DiscreteChoiceStep(eligibility_filter=...)` → `LogitChoiceStep` → `EligibilityMergeStep` — verify ineligible households get keep_current, eligible households get logit choices
  - [x] 7.9: `test_eligibility.py` — Performance assertion: 100-household population with 30 eligible, 3 alternatives → adapter called with 90 rows (not 300)

- [x] Task 8: Lint, type-check, regression (AC: all)
  - [x] 8.1: `uv run ruff check src/reformlab/discrete_choice/ tests/discrete_choice/`
  - [x] 8.2: `uv run mypy src/reformlab/discrete_choice/`
  - [x] 8.3: `uv run mypy src/`
  - [x] 8.4: `uv run pytest tests/` — full regression, 2515 passed, 0 failures

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**OrchestratorStep protocol** (from `src/reformlab/orchestrator/step.py`):
```python
@runtime_checkable
class OrchestratorStep(Protocol):
    @property
    def name(self) -> str: ...
    def execute(self, year: int, state: YearState) -> YearState: ...
```

Optional: `depends_on: tuple[str, ...]` and `description: str`.

**DecisionDomain protocol** (from `src/reformlab/discrete_choice/domain.py`):
```python
@runtime_checkable
class DecisionDomain(Protocol):
    @property
    def name(self) -> str: ...
    @property
    def alternatives(self) -> tuple[Alternative, ...]: ...
    @property
    def cost_column(self) -> str: ...
    def apply_alternative(self, table: pa.Table, alternative: Alternative) -> pa.Table: ...
```

**Immutable state updates:** Always use `dataclasses.replace(state, data=new_data)`. Never mutate `state.data` in-place. Create a new dict: `new_data = dict(state.data)`, modify `new_data`, then `replace(state, data=new_data)`.

### Data Flow — Current Pipeline (Without Eligibility)

```
DiscreteChoiceStep.execute():
  reads: PopulationData from state["population_data"] (N households)
  calls: expand_population() → N×M expanded population
  calls: adapter.compute() → N×M computation results
  calls: reshape_to_cost_matrix() → N×M CostMatrix
  stores: CostMatrix → state["discrete_choice_cost_matrix"]
          ExpansionResult → state["discrete_choice_expansion"]
          metadata dict → state["discrete_choice_metadata"]
    ↓
LogitChoiceStep.execute():
  reads: CostMatrix from state["discrete_choice_cost_matrix"] (N×M)
  calls: compute_utilities() → N×M utilities
  calls: compute_probabilities() → N×M probabilities
  calls: draw_choices() → ChoiceResult (N entries)
  stores: ChoiceResult → state["discrete_choice_result"]
    ↓
StateUpdateStep.execute() (Vehicle or Heating):
  reads: ChoiceResult from state["discrete_choice_result"] (N entries)
         PopulationData from state["population_data"] (N rows)
  calls: apply_choices_to_population() → updated population
  calls: create_vintage_entries() → new VintageCohort entries
  stores: Updated PopulationData, VintageState, metadata
```

### Data Flow — With Eligibility Filtering (THIS STORY)

```
DiscreteChoiceStep.execute() (MODIFIED):
  reads: PopulationData from state["population_data"] (N households)
  NEW → evaluates: evaluate_eligibility() → boolean mask (N booleans)
  NEW → filters: filter_population_by_eligibility() → filtered population (N' rows)
  calls: expand_population() → N'×M expanded population (SMALLER)
  calls: adapter.compute() → N'×M computation results (FASTER)
  calls: reshape_to_cost_matrix() → N'×M CostMatrix (SMALLER)
  stores: CostMatrix (N'×M) → state["discrete_choice_cost_matrix"]
          ExpansionResult (N'×M) → state["discrete_choice_expansion"]
          NEW → EligibilityInfo → state["discrete_choice_eligibility"]
          metadata dict (with eligibility counts)
    ↓
LogitChoiceStep.execute() (UNMODIFIED):
  reads: CostMatrix (N'×M) — works identically, just fewer rows
  stores: ChoiceResult (N' entries)
    ↓
EligibilityMergeStep.execute() (NEW):
  reads: ChoiceResult (N' entries) from state["discrete_choice_result"]
         EligibilityInfo from state["discrete_choice_eligibility"]
  creates: Full N-entry ChoiceResult:
           - eligible[j] → logit choice from position j
           - ineligible[i] → default_choice, prob=1.0/0.0, utility=0.0
  stores: Merged ChoiceResult (N entries) → state["discrete_choice_result"]
    ↓
StateUpdateStep.execute() (UNMODIFIED):
  reads: ChoiceResult (N entries) — works identically
         PopulationData (N rows) — original unfiltered population
  applies: Per-household choices (ineligible got "keep_current" → no attribute change)
```

### Key Design Decisions

1. **Filter at DiscreteChoiceStep level, merge after logit** — The filter is evaluated in `DiscreteChoiceStep.execute()` before calling `expand_population()`. The filtered population is what gets expanded, computed, and reshaped. After logit produces N' choices, `EligibilityMergeStep` expands them back to N choices. This approach:
   - Keeps `expand_population()`, `reshape_to_cost_matrix()`, and `LogitChoiceStep` **completely unmodified**
   - Keeps `VehicleStateUpdateStep` and `HeatingStateUpdateStep` **completely unmodified**
   - Only modifies `DiscreteChoiceStep` (eligibility config + filter before expand)
   - Only adds one new module (`eligibility.py`) and one new step (`EligibilityMergeStep`)

2. **Tracking columns are relative to eligible subset** — After filtering, the entity table has N' rows indexed 0..N'-1. The expansion's `_original_household_index` tracking column maps to these N' rows, not the original N. The mapping from eligible-subset-index to original-population-index is stored in `EligibilityInfo.eligible_indices`. This is correct because `reshape_to_cost_matrix()` uses `expansion.n_households` (which will be N'), and the cost matrix will have N' rows.

3. **Filtered population contains only the entity_key table** — When filtering, the returned `PopulationData` contains only the filtered `entity_key` table (e.g., `"menage"`). Other entity tables (e.g., `"individu"`) are excluded. This is safe because:
   - The expansion expands all tables independently — having only one table is correct
   - The adapter computation for cost evaluation only needs the decision-relevant entity
   - The original unfiltered population in `state["population_data"]` is preserved for the state update step

4. **EligibilityMergeStep is a pass-through when unused** — If `DISCRETE_CHOICE_ELIGIBILITY_KEY` is not in state (no eligibility filter was applied), the step returns state unchanged. This makes it safe to always include in a pipeline, regardless of whether eligibility filtering is enabled. The step is idempotent.

5. **EligibilityMergeStep removes EligibilityInfo from state after consuming it** — After merging, the `EligibilityInfo` is removed from `state.data` so it doesn't leak into subsequent domain steps. In sequential domain execution (vehicle → heating), each domain has its own `EligibilityInfo` that is consumed by its own `EligibilityMergeStep`. This prevents cross-domain contamination. The eligibility counts remain in the `DISCRETE_CHOICE_METADATA_KEY` dict (which preserves all keys across domains).

6. **Rule-based eligibility (not callable-based)** — Eligibility rules are frozen dataclasses with `column`, `operator`, `threshold`. This makes them:
   - Serializable and inspectable for run manifests (AC-8)
   - Composable with AND/OR logic
   - Validated at construction time (invalid operator → immediate error)
   - Deterministic and reproducible

7. **PyArrow compute for performance** — `evaluate_eligibility()` uses `pyarrow.compute` functions (`pc.greater`, `pc.less`, etc.) instead of Python loops. This is critical for 100k+ populations — PyArrow compute is vectorized C++ under the hood. The project already depends on `pyarrow >= 18.0.0`, so `pyarrow.compute` is available with no new dependencies.

8. **default_choice must be a valid alternative ID** — The `EligibilityMergeStep` validates that `default_choice` is in `alternative_ids`. If not, it raises `DiscreteChoiceError`. This prevents silent errors where ineligible households get assigned an unknown alternative.

### Pipeline Example With Sequential Domains

```
# Vehicle domain with eligibility (only vehicles > 10 years)
discrete_choice_vehicle (depends_on=())
  → eligibility_filter: rules=[(column="vehicle_age", operator="gt", threshold=10)]
  → Evaluates: 100k → 25k eligible
  → Expands 25k × 6 = 150k rows (not 600k)

logit_choice_vehicle (depends_on=("discrete_choice_vehicle",))
  → Processes 25k × 6 cost matrix → 25k choices

eligibility_merge_vehicle (depends_on=("logit_choice_vehicle",))
  → Merges 25k → 100k choices (75k get "keep_current")

vehicle_state_update (depends_on=("eligibility_merge_vehicle",))
  → Applies 100k choices to 100k households

# Heating domain with eligibility (only heating > 15 years)
discrete_choice_heating (depends_on=("vehicle_state_update",))
  → eligibility_filter: rules=[(column="heating_age", operator="gt", threshold=15)]
  → Evaluates: 100k → 20k eligible
  → Expands 20k × 5 = 100k rows (not 500k)

logit_choice_heating (depends_on=("discrete_choice_heating",))
  → Processes 20k × 5 cost matrix → 20k choices

eligibility_merge_heating (depends_on=("logit_choice_heating",))
  → Merges 20k → 100k choices (80k get "keep_current")

heating_state_update (depends_on=("eligibility_merge_heating",))
  → Applies 100k choices to 100k households

# Total expanded rows: 150k + 100k = 250k (instead of 600k + 500k = 1.1M)
# ~4.4x reduction in computation
```

### EligibilityMergeStep — Merge Algorithm

```python
def execute(self, year: int, state: YearState) -> YearState:
    eligibility_info = state.data.get(DISCRETE_CHOICE_ELIGIBILITY_KEY)
    if eligibility_info is None:
        return state  # No filtering — pass through

    choice_result = state.data[DISCRETE_CHOICE_RESULT_KEY]  # N' entries
    n_total = eligibility_info.n_total
    n_eligible = eligibility_info.n_eligible
    eligible_indices = eligibility_info.eligible_indices
    default_choice = eligibility_info.default_choice
    alt_ids = eligibility_info.alternative_ids

    # Validate default_choice is a valid alternative ID
    if default_choice not in alt_ids:
        raise DiscreteChoiceError(...)

    # Build eligible index set for O(1) lookup
    eligible_set = set(eligible_indices)

    # Build mapping: eligible_indices[j] → position j in choice_result
    eligible_pos_map = {idx: j for j, idx in enumerate(eligible_indices)}

    # Extract N' arrays from choice_result
    cr_chosen = choice_result.chosen.to_pylist()       # N' strings
    cr_probs = {aid: choice_result.probabilities.column(aid).to_pylist() for aid in alt_ids}
    cr_utils = {aid: choice_result.utilities.column(aid).to_pylist() for aid in alt_ids}

    # Build full N arrays
    full_chosen: list[str] = []
    full_probs: dict[str, list[float]] = {aid: [] for aid in alt_ids}
    full_utils: dict[str, list[float]] = {aid: [] for aid in alt_ids}

    for i in range(n_total):
        if i in eligible_set:
            j = eligible_pos_map[i]
            full_chosen.append(cr_chosen[j])
            for aid in alt_ids:
                full_probs[aid].append(cr_probs[aid][j])
                full_utils[aid].append(cr_utils[aid][j])
        else:
            full_chosen.append(default_choice)
            for aid in alt_ids:
                full_probs[aid].append(1.0 if aid == default_choice else 0.0)
                full_utils[aid].append(0.0)

    merged = ChoiceResult(
        chosen=pa.array(full_chosen),
        probabilities=pa.table({aid: pa.array(full_probs[aid]) for aid in alt_ids}),
        utilities=pa.table({aid: pa.array(full_utils[aid]) for aid in alt_ids}),
        alternative_ids=alt_ids,
        seed=choice_result.seed,
    )

    # Store merged result, remove consumed EligibilityInfo
    new_data = dict(state.data)
    new_data[DISCRETE_CHOICE_RESULT_KEY] = merged
    del new_data[DISCRETE_CHOICE_ELIGIBILITY_KEY]  # Consumed

    # Extend metadata
    existing_metadata = state.data.get(DISCRETE_CHOICE_METADATA_KEY, {})
    ...
    extended_metadata["eligibility_merge_n_defaulted"] = n_total - n_eligible

    return replace(state, data=new_data)
```

### evaluate_eligibility — Operator Mapping

```python
import pyarrow.compute as pc

_OPERATOR_MAP = {
    "gt": pc.greater,
    "ge": pc.greater_equal,
    "lt": pc.less,
    "le": pc.less_equal,
    "eq": pc.equal,
    "ne": pc.not_equal,
}

def evaluate_eligibility(table: pa.Table, eligibility_filter: EligibilityFilter) -> pa.ChunkedArray:
    n = table.num_rows
    if not eligibility_filter.rules:
        return pa.chunked_array([pa.array([True] * n)])

    masks: list[pa.ChunkedArray] = []
    for rule in eligibility_filter.rules:
        if rule.column not in table.column_names:
            raise DiscreteChoiceError(
                f"Eligibility column '{rule.column}' not found. "
                f"Available: {sorted(table.column_names)}"
            )
        col = table.column(rule.column)
        op_fn = _OPERATOR_MAP[rule.operator]  # Already validated in __post_init__
        mask = op_fn(col, rule.threshold)
        masks.append(mask)

    result = masks[0]
    if eligibility_filter.logic == "all":
        for m in masks[1:]:
            result = pc.and_(result, m)
    else:  # "any"
        for m in masks[1:]:
            result = pc.or_(result, m)

    return result
```

### DiscreteChoiceStep Modification Pattern

The modification to `execute()` is minimal. Add this block **before** the existing expansion phase:

```python
# NEW: Eligibility filtering (Story 14.5)
eligibility_info = None
if self._eligibility_filter is not None:
    from reformlab.discrete_choice.eligibility import (
        DISCRETE_CHOICE_ELIGIBILITY_KEY,
        EligibilityInfo,
        evaluate_eligibility,
        filter_population_by_eligibility,
    )

    entity_key = self._eligibility_filter.entity_key
    if entity_key not in population.tables:
        raise DiscreteChoiceError(
            f"Eligibility entity_key '{entity_key}' not found. "
            f"Available: {sorted(population.tables.keys())}",
            year=year, step_name=self._name,
        )
    eligible_mask = evaluate_eligibility(
        population.tables[entity_key], self._eligibility_filter
    )
    filtered_pop, eligible_indices = filter_population_by_eligibility(
        population, eligible_mask, entity_key
    )
    n_total = population.tables[entity_key].num_rows
    n_eligible = len(eligible_indices)

    logger.info(
        "year=%d step_name=%s n_total=%d n_eligible=%d event=eligibility_evaluated",
        year, self._name, n_total, n_eligible,
    )

    eligibility_info = EligibilityInfo(
        n_total=n_total,
        n_eligible=n_eligible,
        eligible_indices=eligible_indices,
        default_choice=self._eligibility_filter.default_choice,
        filter_description=self._eligibility_filter.description,
        alternative_ids=choice_set.alternative_ids,
        filter_rules=self._eligibility_filter.rules,
    )

    # Use filtered population for expansion
    population = filtered_pop
    # Update n for logging
    n = n_eligible

# ... existing expansion logic (now operates on filtered population if applicable)

# In Phase 4 (Store in YearState), ADD:
if eligibility_info is not None:
    new_data[DISCRETE_CHOICE_ELIGIBILITY_KEY] = eligibility_info
    extended_metadata["eligibility_n_total"] = eligibility_info.n_total
    extended_metadata["eligibility_n_eligible"] = eligibility_info.n_eligible
    extended_metadata["eligibility_n_ineligible"] = eligibility_info.n_total - eligibility_info.n_eligible
    extended_metadata["eligibility_filter_description"] = eligibility_info.filter_description
```

### Edge Case Handling

| Scenario | Expected Behavior |
|----------|-------------------|
| All households eligible (N' = N) | Merge step maps 1:1, identical to no filtering. EligibilityInfo still stored (counts documented). |
| All households ineligible (N' = 0) | Empty population → empty expansion → empty cost matrix → empty logit choices → merge assigns default_choice to all N households. Works because empty population is already handled in expansion.py, reshape.py, and logit.py. |
| Empty rules tuple | `evaluate_eligibility` returns all-True mask → all eligible → same as no filtering. |
| Single rule | Works without composition logic (no AND/OR needed). |
| eligibility_filter is None | DiscreteChoiceStep behavior identical to current implementation. No `EligibilityInfo` stored. EligibilityMergeStep passes through. |
| Missing column in rule | `DiscreteChoiceError` raised with column name and available columns. |
| Invalid operator | `DiscreteChoiceError` raised at `EligibilityRule.__post_init__`. |
| Invalid logic value | `DiscreteChoiceError` raised at `EligibilityFilter.__post_init__`. |
| default_choice not a valid alternative | `DiscreteChoiceError` raised in `EligibilityMergeStep.execute()` with valid alternatives listed. |
| Sequential domains (vehicle → heating) | Each domain has its own EligibilityInfo. Vehicle merge consumes vehicle EligibilityInfo. Heating merge consumes heating EligibilityInfo. No cross-contamination. |
| EligibilityMergeStep without EligibilityInfo in state | Pass-through (returns state unchanged). Safe to always include. |
| ChoiceResult missing in merge step | `DiscreteChoiceError` raised (same pattern as state update steps). |
| Non-dict metadata in state | `DiscreteChoiceError` raised (consistent with other steps). |

### State Key Integration

New state key:
```python
DISCRETE_CHOICE_ELIGIBILITY_KEY = "discrete_choice_eligibility"  # EligibilityInfo
```

Reads from state (set by Stories 14.1 and 14.2):
```python
DISCRETE_CHOICE_RESULT_KEY = "discrete_choice_result"       # ChoiceResult (from logit.py)
DISCRETE_CHOICE_METADATA_KEY = "discrete_choice_metadata"   # dict (from step.py)
DISCRETE_CHOICE_COST_MATRIX_KEY = "discrete_choice_cost_matrix"  # CostMatrix (from step.py)
```

Extends `DISCRETE_CHOICE_METADATA_KEY` dict with:
```python
"eligibility_n_total": int               # Original population size
"eligibility_n_eligible": int            # Number eligible for expansion
"eligibility_n_ineligible": int          # Number skipped
"eligibility_filter_description": str    # Human-readable description
"eligibility_merge_n_defaulted": int     # Number assigned default choice (set by merge step)
```

### Testing Standards

- **Mirror structure:** Tests in `tests/discrete_choice/test_eligibility.py`
- **Self-contained helpers:** Test classes use private `_make_population`/`_make_state` helpers (follows test_vehicle.py and test_heating.py pattern)
- **Class-based grouping:** `TestEligibilityRule`, `TestEligibilityFilter`, `TestEligibilityInfo`, `TestEvaluateEligibility`, `TestFilterPopulation`, `TestEligibilityMergeStep`, `TestDiscreteChoiceStepWithEligibility`
- **Protocol compliance test:** `assert is_protocol_step(step)` for EligibilityMergeStep
- **StepRegistry test:** Register and retrieve EligibilityMergeStep
- **Golden value test:** Hand-build a 5-household population with 3 eligible, verify exact merge output
- **Performance assertion test:** Verify adapter receives N'×M rows (check `MockAdapter.call_log`)
- **Backward compatibility test:** DiscreteChoiceStep without eligibility_filter behaves identically to pre-14.5
- **Integration test:** Full pipeline with eligibility filter → verify ineligible households unchanged
- **MockAdapter for tests:** Reuse existing conftest `_discrete_choice_compute_fn` pattern
- **Backward compatibility:** All pre-14.5 `DiscreteChoiceStep` tests in `test_step.py` must pass without modification — `test_step.py` is listed as UNCHANGED in the file list

### Project Structure Notes

```
src/reformlab/discrete_choice/
├── __init__.py       # MODIFIED: add eligibility exports
├── types.py          # UNCHANGED
├── errors.py         # UNCHANGED
├── domain.py         # UNCHANGED
├── expansion.py      # UNCHANGED
├── reshape.py        # UNCHANGED
├── step.py           # MODIFIED: DiscreteChoiceStep gets eligibility_filter param
├── logit.py          # UNCHANGED
├── domain_utils.py   # UNCHANGED
├── vehicle.py        # UNCHANGED
├── heating.py        # UNCHANGED
└── eligibility.py    # NEW — EligibilityRule, EligibilityFilter, EligibilityInfo,
                      #        evaluate_eligibility, filter_population_by_eligibility,
                      #        EligibilityMergeStep, DISCRETE_CHOICE_ELIGIBILITY_KEY

tests/discrete_choice/
├── __init__.py       # UNCHANGED
├── conftest.py       # UNCHANGED
├── test_types.py     # UNCHANGED
├── test_expansion.py # UNCHANGED
├── test_reshape.py   # UNCHANGED
├── test_step.py      # UNCHANGED (existing tests validate backward compatibility)
├── test_logit.py     # UNCHANGED
├── test_vehicle.py   # UNCHANGED
├── test_domain_utils.py # UNCHANGED
├── test_heating.py   # UNCHANGED
└── test_eligibility.py  # NEW — All eligibility tests
```

No new dependencies required — uses `pyarrow.compute` which is part of the existing `pyarrow >= 18.0.0` dependency.

### Cross-Story Dependencies

| Story | Relationship | Notes |
|-------|-------------|-------|
| 14.1 | Depends on | `DiscreteChoiceStep` modified to add eligibility config; `expand_population()`, `reshape_to_cost_matrix()` unchanged |
| 14.2 | Depends on | `LogitChoiceStep` unchanged; produces N' ChoiceResult consumed by merge step |
| 14.3 | Related | Vehicle domain works with or without eligibility filtering |
| 14.4 | Related | Heating domain works with or without eligibility filtering |
| 14.6 | Blocks | Panel output should include eligibility metadata from manifests |
| 14.7 | Blocks | Notebook demo should demonstrate eligibility filtering for performance |
| 15.1 | Related | Calibration targets may reference filtered vs unfiltered populations |

### Out of Scope Guardrails

- **DO NOT** modify `expand_population()` in `expansion.py`
- **DO NOT** modify `reshape_to_cost_matrix()` in `reshape.py`
- **DO NOT** modify `LogitChoiceStep` in `logit.py`
- **DO NOT** modify `VehicleStateUpdateStep` in `vehicle.py`
- **DO NOT** modify `HeatingStateUpdateStep` in `heating.py`
- **DO NOT** modify `domain_utils.py`
- **DO NOT** modify `domain.py` (DecisionDomain protocol)
- **DO NOT** modify `types.py` (ExpansionResult, CostMatrix, ChoiceResult, etc.)
- **DO NOT** modify `errors.py` (use existing DiscreteChoiceError)
- **DO NOT** modify any orchestrator files (`runner.py`, `step.py`, `types.py`)
- **DO NOT** modify `ComputationAdapter` protocol or `MockAdapter`
- **DO NOT** add numpy or any new dependency
- **DO NOT** implement callable-based eligibility rules (use declarative EligibilityRule only)
- **DO NOT** implement nested/hierarchical eligibility logic beyond AND/OR
- **DO NOT** modify existing test files — only add `test_eligibility.py`
- **DO NOT** implement panel output extensions (Story 14.6)
- **DO NOT** implement calibration of eligibility thresholds (Epic 15)

### References

- [Source: `src/reformlab/discrete_choice/step.py` — DiscreteChoiceStep, state keys, expand→compute→reshape pipeline]
- [Source: `src/reformlab/discrete_choice/expansion.py` — expand_population, TRACKING_COL_ALTERNATIVE_ID, TRACKING_COL_ORIGINAL_INDEX]
- [Source: `src/reformlab/discrete_choice/reshape.py` — reshape_to_cost_matrix, tracking-column-based reshape]
- [Source: `src/reformlab/discrete_choice/logit.py` — LogitChoiceStep, DISCRETE_CHOICE_RESULT_KEY, ChoiceResult storage]
- [Source: `src/reformlab/discrete_choice/types.py` — Alternative, ChoiceSet, CostMatrix, ExpansionResult, ChoiceResult, TasteParameters]
- [Source: `src/reformlab/discrete_choice/errors.py` — DiscreteChoiceError hierarchy]
- [Source: `src/reformlab/discrete_choice/vehicle.py` — VehicleStateUpdateStep (unmodified, validates merge produces N entries)]
- [Source: `src/reformlab/discrete_choice/heating.py` — HeatingStateUpdateStep (unmodified, validates merge produces N entries)]
- [Source: `src/reformlab/discrete_choice/domain_utils.py` — apply_choices_to_population (unchanged, validates chosen length = population rows)]
- [Source: `src/reformlab/discrete_choice/__init__.py` — Public API exports]
- [Source: `src/reformlab/orchestrator/types.py` — YearState (data, seed, metadata)]
- [Source: `src/reformlab/orchestrator/step.py` — OrchestratorStep protocol, StepRegistry, is_protocol_step]
- [Source: `src/reformlab/computation/types.py` — PopulationData (tables, metadata), PolicyConfig]
- [Source: `src/reformlab/computation/mock_adapter.py` — MockAdapter (compute_fn, version_string, call_log)]
- [Source: `tests/discrete_choice/conftest.py` — MockDomain, _discrete_choice_compute_fn, sample fixtures]
- [Source: `tests/discrete_choice/test_vehicle.py` — Vehicle domain test patterns]
- [Source: `tests/discrete_choice/test_heating.py` — Heating domain test patterns, sequential domain test]
- [Source: `_bmad-output/planning-artifacts/phase-2-design-note-discrete-choice-household-decisions.md` — Performance considerations (line 197): "filter households by eligibility to reduce expanded population size"; Data requirements (line 205): "Eligibility rules: which households face which choices"]
- [Source: `docs/epics.md` — Epic 14 AC for BKL-1405, Story 14.5 acceptance criteria]
- [Source: `docs/project-context.md` — Project rules: PyArrow-first, frozen dataclasses, Protocols not ABCs, adapter isolation]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — clean implementation, no debugging issues.

### Completion Notes List

- Story creation notes (pre-implementation):
  - Ultimate context engine analysis completed — comprehensive developer guide created
  - All discrete choice pipeline components analyzed: expansion.py, reshape.py, logit.py, step.py, types.py, domain.py
  - Data flow mapped end-to-end for both current and eligibility-filtered pipelines
  - Design decision: filter at DiscreteChoiceStep, merge after logit via new EligibilityMergeStep
  - Key insight: LogitChoiceStep, expand_population, reshape_to_cost_matrix, and all state update steps require ZERO modifications
  - Only DiscreteChoiceStep.execute() is modified (eligibility config + filter before expand)
  - PyArrow compute used for efficient 100k+ evaluation (pc.greater, pc.less, etc.)
  - Rule-based eligibility (frozen dataclasses) chosen over callable-based for manifest serialization
  - EligibilityMergeStep pass-through behavior enables safe always-include pipeline pattern
  - Sequential domain execution validated: each domain's EligibilityInfo is consumed by its own merge step
  - All edge cases documented: all-eligible, all-ineligible, empty rules, missing columns, invalid operators
  - Performance scaling quantified: 250k expanded rows instead of 1.1M for dual-domain 100k population (4.4x reduction)
  - Antipatterns from Stories 14.1-14.4 integrated: explicit validation, structured logging, metadata preservation
- Implementation notes (2026-03-07):
  - All 8 tasks and all subtasks implemented and verified
  - 55 new tests in test_eligibility.py — all passing
  - Full regression: 2515 passed, 0 failures
  - ruff: All checks passed
  - mypy strict: Success, no issues in 132 source files
  - No existing files modified beyond step.py and __init__.py (as planned)
  - No new dependencies added
  - Backward compatibility verified: all pre-14.5 tests pass unmodified
- Code review synthesis notes (2026-03-07):
  - Added invariant validation in EligibilityMergeStep.execute(): validates n_eligible == len(eligible_indices), 0 <= n_eligible <= n_total, and len(choice_result.chosen) == n_eligible — raises DiscreteChoiceError on violation (prevents raw IndexError and negative n_defaulted)
  - Wrapped PyArrow compute operations in evaluate_eligibility() with try/except for ArrowNotImplementedError/ArrowTypeError/ArrowInvalid — raises DiscreteChoiceError with rule context (e.g., string threshold on numeric column)
  - Wrapped table.filter() in filter_population_by_eligibility() with try/except for ArrowInvalid/ArrowTypeError — raises DiscreteChoiceError with entity key context
  - Added test_pipeline_with_state_update_ac7() to TestFullPipelineIntegration: full pipeline including VehicleStateUpdateStep verifies ineligible households have unchanged vehicle_type and vintage cohort count is bounded by eligible household count (completes AC-7 verification)
  - 1 new test added: 56 total in test_eligibility.py — all passing
  - Full regression: 2516 passed, 0 failures

### File List

#### New Files
- `src/reformlab/discrete_choice/eligibility.py` — EligibilityRule, EligibilityFilter, EligibilityInfo, evaluate_eligibility, filter_population_by_eligibility, EligibilityMergeStep, DISCRETE_CHOICE_ELIGIBILITY_KEY
- `tests/discrete_choice/test_eligibility.py` — Comprehensive tests for all eligibility types, functions, and steps

#### Modified Files
- `src/reformlab/discrete_choice/step.py` — DiscreteChoiceStep.__init__ gets optional `eligibility_filter` parameter; execute() evaluates and filters before expansion when filter is provided
- `src/reformlab/discrete_choice/__init__.py` — Added eligibility exports (EligibilityRule, EligibilityFilter, EligibilityInfo, evaluate_eligibility, filter_population_by_eligibility, EligibilityMergeStep, DISCRETE_CHOICE_ELIGIBILITY_KEY)

#### Code Review Synthesis — Additional Modifications
- `src/reformlab/discrete_choice/eligibility.py` — Added: (1) invariant validation in EligibilityMergeStep.execute() for n_eligible/eligible_indices consistency and ChoiceResult length; (2) try/except around PyArrow compute in evaluate_eligibility(); (3) try/except around table.filter() in filter_population_by_eligibility()
- `tests/discrete_choice/test_eligibility.py` — Added test_pipeline_with_state_update_ac7() to TestFullPipelineIntegration for full AC-7 verification including VehicleStateUpdateStep

## Senior Developer Review (AI)

### Review: 2026-03-07
- **Reviewer:** AI Code Review Synthesis
- **Evidence Score:** 9.3 (combined A: 5.3, B: 12.8, adjusted for false positives) → CHANGES REQUESTED (pre-fix)
- **Issues Found:** 4 verified (3 source code bugs, 1 test gap)
- **Issues Fixed:** 4
- **Action Items Created:** 0
