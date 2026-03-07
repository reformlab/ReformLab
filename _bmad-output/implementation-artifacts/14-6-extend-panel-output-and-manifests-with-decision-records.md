

# Story 14.6: Extend Panel Output and Manifests with Decision Records

Status: dev-complete

## Story

As a **platform developer**,
I want panel output and run manifests to include discrete choice decision records (chosen alternatives, probabilities, utilities, taste parameters),
so that analysts can audit household-level behavioral responses year-by-year and researchers can reproduce or critique the decision model configuration.

## Acceptance Criteria

1. **AC-1: DecisionRecord type** — `DecisionRecord` is a frozen dataclass with fields: `domain_name: str`, `chosen: pa.Array` (N-element string array of chosen alternative IDs), `probabilities: pa.Table` (N×M table, one column per alternative — this internal `pa.Table` representation is transformed to `pa.list_(pa.float64())` when written to the panel), `utilities: pa.Table` (N×M table, one column per alternative — same transformation applies), `alternative_ids: tuple[str, ...]`, `seed: int | None`, `taste_parameters: dict[str, float]` (e.g., `{"beta_cost": -0.01}` — treat as logically immutable after construction; do not mutate the dict after passing it to `DecisionRecord`), `eligibility_summary: dict[str, int] | None` (e.g., `{"n_total": 100, "n_eligible": 30, "n_ineligible": 70}` or `None` if no eligibility filtering — same immutability convention). Stored under `DECISION_LOG_KEY = "discrete_choice_decision_log"` in `YearState.data` as a `tuple[DecisionRecord, ...]`.

2. **AC-2: DecisionRecordStep** — `DecisionRecordStep` implements the `OrchestratorStep` protocol. Default `name="decision_record"`, `depends_on=("vehicle_state_update",)` (caller configures per pipeline). It reads `ChoiceResult` from `state.data[DISCRETE_CHOICE_RESULT_KEY]` and domain metadata from `state.data[DISCRETE_CHOICE_METADATA_KEY]`. It creates a `DecisionRecord` and appends it to the existing decision log tuple in `state.data[DECISION_LOG_KEY]` (creating a new tuple if none exists). The step extracts `beta_cost` and `choice_seed` from metadata, and eligibility counts (`eligibility_n_total`, `eligibility_n_eligible`, `eligibility_n_ineligible`) if present. If `DISCRETE_CHOICE_RESULT_KEY` is not in state, the step returns state unchanged (pass-through). This makes it safe to always include in a pipeline.

3. **AC-3: Panel decision columns** — `PanelOutput.from_orchestrator_result()` is extended to detect `DECISION_LOG_KEY` in each yearly state. When present, the panel builder appends decision columns to each yearly table before concatenation. For each `DecisionRecord` in the log, the following domain-prefixed columns are added:
   - `{domain_name}_chosen` (`pa.string()`) — Chosen alternative ID per household.
   - `{domain_name}_probabilities` (`pa.list_(pa.float64())`) — Choice probabilities array per household, ordered by `alternative_ids`. The panel builder transforms the `pa.Table`-typed `probabilities` field from `DecisionRecord` (one column per alternative) into this flat list column.
   - `{domain_name}_utilities` (`pa.list_(pa.float64())`) — Utility values array per household, ordered by `alternative_ids`. Same transformation from `pa.Table` to flat list column.

   Additionally, a `decision_domains` column (`pa.list_(pa.string())`) is added listing all domain names evaluated for that year (e.g., `["vehicle", "heating"]`), the same value for every row in that year.

   The panel metadata dict is extended with `decision_domain_alternatives: dict[str, list[str]]` mapping each domain name to its ordered alternative IDs, so consumers can decode the list column positions.

   When no decision log exists for a year, no decision columns are added (backward compatible with non-discrete-choice runs).

4. **AC-4: Parquet export** — Decision columns with `pa.list_(pa.float64())` type are natively supported by Parquet. Given panel output with decision records, when exported via `to_parquet()`, then the file is readable by pandas (list columns become Python lists) and polars (list columns become `list[f64]`). Given panel output with decision records, when exported via `to_csv()`, then list columns are serialized as bracket-delimited strings (PyArrow default CSV behavior). No changes to `to_csv()` or `to_parquet()` methods are required — the existing implementations handle the new column types natively.

5. **AC-5: Manifest taste parameter capture** — A `capture_discrete_choice_parameters()` function extracts taste parameters and eligibility summaries from the decision log in yearly states. It returns a `list[dict[str, Any]]` where each entry contains: `domain_name`, `beta_cost`, `choice_seed` (from the first year, as a representative sample — seeds vary per year as `master_seed XOR year` and are fully recorded in the existing seed log), and optionally `eligibility_summary`. The function scans the first year's state that contains a decision log (taste parameters such as `beta_cost` are consistent across years; `choice_seed` is year-specific but captured from the first year here as the seed for year N can be recomputed from the manifest's master seed). The extracted parameters are included in the manifest metadata under key `"discrete_choice_parameters"` only when the list is non-empty (key is absent for non-discrete-choice runs). Given a run with two domains (vehicle, heating), when the manifest is inspected, then both domains' taste parameters are listed.

6. **AC-6: Panel schema consistency across years** — Given a multi-year run with discrete choice, when panel tables from different years have the same decision domains, then all yearly tables have identical column schemas and `pa.concat_tables()` succeeds without error. Given a multi-year run where Year 1 has decision records but Year 2 does not (e.g., partial run), then decision columns are only present in the Year 1 table and concatenation uses `promote_options="permissive"` to handle schema differences.

7. **AC-7: Edge cases** — No decision log in any year: panel is identical to pre-14.6 output (backward compatible). Single domain: one set of `{domain}_chosen`, `{domain}_probabilities`, `{domain}_utilities` columns. Two domains: two sets of domain-prefixed columns. Empty ChoiceResult (N=0): empty arrays in decision columns. DecisionRecordStep without ChoiceResult in state: pass-through. Panel with mixed years (some with decisions, some without): uses `promote_options="permissive"` in `pa.concat_tables()`.

## Tasks / Subtasks

- [x] Task 1: Create `decision_record.py` with types and step (AC: 1, 2)
  - [x] 1.1: Define `DECISION_LOG_KEY = "discrete_choice_decision_log"` state key constant
  - [x] 1.2: Implement `DecisionRecord` frozen dataclass with all fields (domain_name, chosen, probabilities, utilities, alternative_ids, seed, taste_parameters, eligibility_summary)
  - [x] 1.3: Implement `DecisionRecordStep` with `__slots__`, OrchestratorStep protocol
  - [x] 1.4: In `execute()`: read ChoiceResult and metadata from state; if absent, return state unchanged
  - [x] 1.5: Extract taste parameters (`beta_cost`, `choice_seed`) from `DISCRETE_CHOICE_METADATA_KEY`
  - [x] 1.6: Extract eligibility summary from metadata if present (`eligibility_n_total`, etc.)
  - [x] 1.7: Create `DecisionRecord`, append to existing log tuple (or create new tuple)
  - [x] 1.8: Store updated log in new state via `dataclasses.replace()` (immutable pattern)
  - [x] 1.9: Structured logging: `domain_name`, `n_households`, `n_alternatives`, `event=decision_recorded`
  - [x] 1.10: Add module docstring referencing Story 14-6 and FR50/FR51

- [x] Task 2: Extend `panel.py` with decision column injection (AC: 3, 4, 6, 7)
  - [x] 2.1: In `from_orchestrator_result()`, after extracting computation result, check for `DECISION_LOG_KEY` in yearly state
  - [x] 2.2: For each `DecisionRecord` in the log, build domain-prefixed columns: `{domain}_chosen`, `{domain}_probabilities`, `{domain}_utilities`
  - [x] 2.3: Build `decision_domains` list column (same value for all rows in a year)
  - [x] 2.4: Append decision columns to the yearly output table before adding household_id and year columns
  - [x] 2.5: Add `decision_domain_alternatives` to panel metadata (domain → alternative_ids mapping)
  - [x] 2.6: Handle schema differences across years: use `promote_options="permissive"` in `pa.concat_tables()` when decision columns are present in some years but not others
  - [x] 2.7: Extract `_build_decision_columns()` helper function for testability

- [x] Task 3: Add `capture_discrete_choice_parameters()` to `capture.py` (AC: 5)
  - [x] 3.1: Implement function that accepts `yearly_states: dict[int, Any]` and returns `list[dict[str, Any]]`
  - [x] 3.2: Scan yearly states for `DECISION_LOG_KEY`; extract per-domain taste parameters from DecisionRecord
  - [x] 3.3: Each entry: `{"domain_name": str, "beta_cost": float, "choice_seed": int | None, "eligibility_summary": dict | None}`
  - [x] 3.4: Return sorted by domain_name for determinism

- [x] Task 4: Extend `runner.py` to capture discrete choice parameters in manifest (AC: 5)
  - [x] 4.1: In `OrchestratorRunner.run()`, after `orchestrator.run()`, call `capture_discrete_choice_parameters(result.yearly_states)`
  - [x] 4.2: Add result to metadata dict under `"discrete_choice_parameters"` key
  - [x] 4.3: Import `capture_discrete_choice_parameters` from `governance.capture`

- [x] Task 5: Update `__init__.py` with new exports (AC: all)
  - [x] 5.1: Export `DecisionRecord`, `DecisionRecordStep`, `DECISION_LOG_KEY` from `decision_record`
  - [x] 5.2: Add to `__all__` in discrete_choice `__init__.py`

- [x] Task 6: Write tests (AC: all)
  - [x] 6.1: `test_decision_record.py` — `TestDecisionRecord`: construction, frozen, all fields accessible
  - [x] 6.2: `test_decision_record.py` — `TestDecisionRecordStep`: protocol compliance, StepRegistry registration, pass-through when no ChoiceResult, snapshot creates record with correct fields, appends to existing log, creates new log when none exists, extracts taste parameters from metadata, extracts eligibility summary, state immutability
  - [x] 6.3: `test_decision_record.py` — `TestDecisionRecordStepMultiDomain`: two domains in sequence produce two records in log, each with correct domain_name and taste_parameters
  - [x] 6.4: `test_panel_decision.py` — `TestPanelWithDecisionRecords`: single domain adds domain-prefixed columns, two domains add two sets of columns, decision_domains list column present, probabilities and utilities are list<float64> type, panel metadata includes decision_domain_alternatives, backward compatibility (no decision log → no decision columns)
  - [x] 6.5: `test_panel_decision.py` — `TestPanelDecisionParquet`: export to Parquet and reload, verify list columns are correctly typed, verify domain-prefixed column names
  - [x] 6.6: `test_panel_decision.py` — `TestPanelDecisionCSV`: export to CSV and verify file is valid
  - [x] 6.7: `test_panel_decision.py` — `TestPanelDecisionSchemaConsistency`: multi-year run with same domains → concat succeeds, multi-year run with partial decisions → concat with promote_options succeeds
  - [x] 6.8: `tests/governance/test_capture_discrete_choice.py` — `TestCaptureDiscreteChoiceParameters`: extracts from single domain, extracts from two domains, returns empty list when no decision log, sorted by domain_name
  - [x] 6.9: `tests/orchestrator/test_runner_discrete_choice.py` — `TestRunnerDiscreteChoiceCapture`: verify `discrete_choice_parameters` appears in WorkflowResult metadata

- [x] Task 7: Lint, type-check, regression (AC: all)
  - [x] 7.1: `uv run ruff check src/reformlab/discrete_choice/ src/reformlab/orchestrator/ src/reformlab/governance/ tests/`
  - [x] 7.2: `uv run mypy src/reformlab/discrete_choice/ src/reformlab/orchestrator/ src/reformlab/governance/`
  - [x] 7.3: `uv run mypy src/`
  - [x] 7.4: `uv run pytest tests/` — full regression

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

**Immutable state updates:** Always use `dataclasses.replace(state, data=new_data)`. Never mutate `state.data` in-place. Create a new dict: `new_data = dict(state.data)`, modify `new_data`, then `replace(state, data=new_data)`.

**Frozen dataclasses:** All domain types use `@dataclass(frozen=True)`. Config/payload types do not use `__slots__`; step classes do.

### Problem: Multi-Domain Metadata Overwrite

The core challenge this story solves is that sequential domain execution (vehicle → heating) overwrites shared metadata keys. After a full vehicle+heating pipeline:

- `DISCRETE_CHOICE_RESULT_KEY` contains only heating's ChoiceResult (vehicle's was overwritten)
- `DISCRETE_CHOICE_METADATA_KEY["beta_cost"]` contains heating's beta (vehicle's was overwritten)
- `DISCRETE_CHOICE_METADATA_KEY["domain_name"]` contains "heating" (vehicle's was overwritten)

Domain-specific keys survive (e.g., `vehicle_n_keepers`, `heating_n_keepers`) because they use domain-prefixed names. But `chosen`, `probabilities`, `utilities`, `beta_cost`, and `choice_seed` are lost for all domains except the last.

**Solution**: `DecisionRecordStep` snapshots the current ChoiceResult and metadata AFTER each domain's state update step, BEFORE the next domain's DiscreteChoiceStep overwrites them.

### Data Flow — Decision Record Pipeline

```
# Vehicle domain (existing steps)
discrete_choice_vehicle → logit_choice_vehicle → eligibility_merge_vehicle → vehicle_state_update
  ↓
decision_record_vehicle (NEW — snapshots vehicle ChoiceResult into decision log)
  ↓
# Heating domain (existing steps)
discrete_choice_heating → logit_choice_heating → eligibility_merge_heating → heating_state_update
  ↓
decision_record_heating (NEW — appends heating ChoiceResult to decision log)

# After full pipeline, state.data[DECISION_LOG_KEY] = (
#     DecisionRecord(domain_name="vehicle", chosen=..., beta_cost=-0.01, ...),
#     DecisionRecord(domain_name="heating", chosen=..., beta_cost=-0.02, ...),
# )
```

### DecisionRecordStep — Execute Algorithm

```python
def execute(self, year: int, state: YearState) -> YearState:
    from reformlab.discrete_choice.types import ChoiceResult as _ChoiceResult

    # Pass-through if no ChoiceResult in state
    choice_result = state.data.get(DISCRETE_CHOICE_RESULT_KEY)
    if not isinstance(choice_result, _ChoiceResult):
        return state

    # Read metadata
    metadata = state.data.get(DISCRETE_CHOICE_METADATA_KEY, {})
    if not isinstance(metadata, dict):
        raise DiscreteChoiceError(...)

    domain_name = metadata.get("domain_name", "unknown")

    # Extract taste parameters
    taste_params: dict[str, float] = {}
    beta = metadata.get("beta_cost")
    if isinstance(beta, (int, float)):
        taste_params["beta_cost"] = float(beta)

    # Extract eligibility summary (if present)
    eligibility_summary: dict[str, int] | None = None
    n_total = metadata.get("eligibility_n_total")
    if isinstance(n_total, int):
        eligibility_summary = {
            "n_total": n_total,
            "n_eligible": metadata.get("eligibility_n_eligible", n_total),
            "n_ineligible": metadata.get("eligibility_n_ineligible", 0),
        }

    record = DecisionRecord(
        domain_name=domain_name,
        chosen=choice_result.chosen,
        probabilities=choice_result.probabilities,
        utilities=choice_result.utilities,
        alternative_ids=choice_result.alternative_ids,
        seed=choice_result.seed,
        taste_parameters=taste_params,
        eligibility_summary=eligibility_summary,
    )

    # Append to log
    existing_log = state.data.get(DECISION_LOG_KEY, ())
    if not isinstance(existing_log, tuple):
        raise DiscreteChoiceError(...)
    new_log = (*existing_log, record)

    new_data = dict(state.data)
    new_data[DECISION_LOG_KEY] = new_log

    logger.info(
        "year=%d step_name=%s domain_name=%s n_households=%d "
        "n_alternatives=%d event=decision_recorded",
        year, self._name, domain_name,
        len(choice_result.chosen), len(choice_result.alternative_ids),
    )

    return replace(state, data=new_data)
```

### Panel Extension — Decision Column Construction

The panel builder in `from_orchestrator_result()` is extended with a helper:

```python
def _build_decision_columns(
    output_table: pa.Table,
    decision_log: tuple[DecisionRecord, ...],
) -> tuple[pa.Table, dict[str, list[str]]]:
    """Add decision columns from the decision log to the output table.

    Returns the extended table and a domain→alternative_ids mapping for metadata.
    """
    # Validate unique domain names before building columns
    domain_names_seen = [r.domain_name for r in decision_log]
    duplicates = {n for n in domain_names_seen if domain_names_seen.count(n) > 1}
    if duplicates:
        raise DiscreteChoiceError(
            f"Duplicate domain_name(s) in decision log: {sorted(duplicates)}. "
            "Each domain must appear at most once per year."
        )

    domain_alternatives: dict[str, list[str]] = {}

    for record in decision_log:
        domain = record.domain_name
        alt_ids = record.alternative_ids
        domain_alternatives[domain] = list(alt_ids)
        n = len(record.chosen)

        # {domain}_chosen: string column
        output_table = output_table.append_column(
            f"{domain}_chosen", record.chosen
        )

        # {domain}_probabilities: list<float64> column
        prob_lists = []
        for i in range(n):
            row = [record.probabilities.column(aid)[i].as_py() for aid in alt_ids]
            prob_lists.append(row)
        output_table = output_table.append_column(
            f"{domain}_probabilities",
            pa.array(prob_lists, type=pa.list_(pa.float64())),
        )

        # {domain}_utilities: list<float64> column
        util_lists = []
        for i in range(n):
            row = [record.utilities.column(aid)[i].as_py() for aid in alt_ids]
            util_lists.append(row)
        output_table = output_table.append_column(
            f"{domain}_utilities",
            pa.array(util_lists, type=pa.list_(pa.float64())),
        )

    # decision_domains: list<string> column (same value for all rows)
    domain_names = [r.domain_name for r in decision_log]
    n_rows = output_table.num_rows
    output_table = output_table.append_column(
        "decision_domains",
        pa.array([domain_names] * n_rows, type=pa.list_(pa.string())),
    )

    return output_table, domain_alternatives
```

**Integration in `from_orchestrator_result()`:**

```python
# After: output_table = comp_result.output_fields
# NEW: Decision record columns
decision_log = year_state.data.get(DECISION_LOG_KEY)
has_decision_columns = False
if isinstance(decision_log, tuple) and decision_log:
    output_table, year_domain_alts = _build_decision_columns(output_table, decision_log)
    all_domain_alternatives.update(year_domain_alts)
    has_decision_columns = True

# Existing: household_id and year columns
output_table = _ensure_household_id_column(...)
output_table = _set_year_column(output_table, year)
yearly_tables.append(output_table)

# At concatenation:
if not yearly_tables:
    ...
else:
    # Use promote_options for schema flexibility when some years
    # have decision columns and others don't
    panel_table = pa.concat_tables(yearly_tables, promote_options="permissive")
```

### Manifest Capture — `capture_discrete_choice_parameters()`

```python
def capture_discrete_choice_parameters(
    yearly_states: dict[int, Any],
) -> list[dict[str, Any]]:
    """Extract taste parameters per domain from decision log in yearly states.

    Scans yearly states for DECISION_LOG_KEY and extracts per-domain
    taste parameters (β coefficients), seed, and eligibility summary.
    Uses the first year containing a decision log (parameters are
    consistent across years).

    Args:
        yearly_states: dict mapping year to YearState (or state-like objects
            with .data attribute).

    Returns:
        Sorted list of dicts with domain_name, beta_cost, choice_seed,
        eligibility_summary per domain. Empty list if no discrete choice.
    """
    from reformlab.discrete_choice.decision_record import DECISION_LOG_KEY

    for year in sorted(yearly_states.keys()):
        state = yearly_states[year]
        data = state.data if hasattr(state, "data") else {}
        decision_log = data.get(DECISION_LOG_KEY)
        if not isinstance(decision_log, tuple) or not decision_log:
            continue

        entries: list[dict[str, Any]] = []
        for record in decision_log:
            entry: dict[str, Any] = {
                "domain_name": record.domain_name,
                "alternative_ids": list(record.alternative_ids),
            }
            entry.update(record.taste_parameters)  # beta_cost, etc.
            if record.seed is not None:
                entry["choice_seed"] = record.seed
            if record.eligibility_summary is not None:
                entry["eligibility_summary"] = dict(record.eligibility_summary)
            entries.append(entry)

        return sorted(entries, key=lambda x: x.get("domain_name", ""))

    return []
```

**Integration in `OrchestratorRunner.run()`:**

```python
# After: result = orchestrator.run()
# Before: manifest_capture = self._capture_manifest_fields(...)

# Story 14-6: Extract discrete choice parameters from decision log
from reformlab.governance.capture import capture_discrete_choice_parameters
dc_params = capture_discrete_choice_parameters(result.yearly_states)

# In metadata dict:
metadata: dict[str, Any] = {
    ...
    **result.metadata,
    **manifest_capture,
}
if dc_params:
    metadata["discrete_choice_parameters"] = dc_params
```

### Key Design Decisions

1. **DecisionRecordStep is a separate step, not embedded in state update steps** — This keeps VehicleStateUpdateStep and HeatingStateUpdateStep completely unmodified. The DecisionRecordStep is a standalone OrchestratorStep that the caller inserts after each domain's state update step. This follows the step-pluggable architecture principle.

2. **Decision log is a tuple of DecisionRecords, not a dict** — Tuples preserve insertion order (vehicle first, heating second) and are immutable. Using domain_name as dict key would work but offers no benefit since the order of domains is meaningful. Tuples also align with the frozen-dataclass pattern.

3. **Domain-prefixed columns in panel** — With two decision domains, the panel has `vehicle_chosen`, `vehicle_probabilities`, `vehicle_utilities`, `heating_chosen`, `heating_probabilities`, `heating_utilities`. This keeps one row per household per year (consistent with the existing panel contract). An alternative (one row per domain) would double the row count and break downstream indicator code.

4. **List columns for probabilities/utilities** — PyArrow `pa.list_(pa.float64())` stores variable-length arrays per cell. This is compact and natively supported by Parquet, pandas, and polars. The alternative (one column per alternative like `vehicle_prob_ev`) would create too many columns and require foreknowledge of alternative names in the panel schema.

5. **`decision_domains` metadata column** — A `pa.list_(pa.string())` column with the same value for all rows in a year. This lets consumers discover which domains are present without scanning column names. Combined with `decision_domain_alternatives` in panel metadata, the full domain→alternatives mapping is available.

6. **`promote_options="permissive"` for concat** — When some years have decision columns and others don't (partial runs, or years before discrete choice kicks in), PyArrow's permissive promotion fills missing columns with nulls. This prevents schema mismatch errors during concatenation.

7. **Capture from first year only** — Taste parameters are configuration inputs that don't change across years. The capture function scans sorted years and returns on the first match, avoiding redundant processing.

8. **`capture_discrete_choice_parameters` is in `governance/capture.py`** — Follows the existing pattern where all manifest capture functions live in `capture.py`. The function accesses `DecisionRecord` via duck typing on the `.domain_name`, `.taste_parameters`, `.seed`, `.eligibility_summary` attributes. `DECISION_LOG_KEY` is imported from `reformlab.discrete_choice.decision_record` — importing a constant is not meaningful coupling (the module still has no runtime dependency on discrete_choice types), and hardcoding the raw string would create a brittle out-of-sync contract that linters and type checkers cannot catch.

9. **DecisionRecordStep is pass-through safe** — If no ChoiceResult exists in state, the step returns state unchanged. This means it can always be included in a pipeline even when discrete choice is not configured.

### Row Count Alignment

Decision columns must have the same number of rows as the computation output for `pa.concat_tables()` to work. Both have N rows per year (N = population size). The ChoiceResult stored in `DISCRETE_CHOICE_RESULT_KEY` always has N entries (full population, after eligibility merge). The computation result in `COMPUTATION_RESULT_KEY` also has N rows. If row counts mismatch (shouldn't happen in normal operation), the column append will fail with a clear PyArrow error.

### Pipeline Example With Decision Records

```
# Full pipeline with decision recording:
discrete_choice_vehicle (depends_on=())
logit_choice_vehicle (depends_on=("discrete_choice_vehicle",))
eligibility_merge_vehicle (depends_on=("logit_choice_vehicle",))
vehicle_state_update (depends_on=("eligibility_merge_vehicle",))
decision_record_vehicle (depends_on=("vehicle_state_update",))  # NEW

discrete_choice_heating (depends_on=("decision_record_vehicle",))
logit_choice_heating (depends_on=("discrete_choice_heating",))
eligibility_merge_heating (depends_on=("logit_choice_heating",))
heating_state_update (depends_on=("eligibility_merge_heating",))
decision_record_heating (depends_on=("heating_state_update",))  # NEW

# After pipeline, state contains:
# DECISION_LOG_KEY → (DecisionRecord(vehicle, ...), DecisionRecord(heating, ...))
# Each record snapshots that domain's ChoiceResult + taste parameters
```

### Edge Case Handling

| Scenario | Expected Behavior |
|----------|-------------------|
| No discrete choice in pipeline | No decision log → panel is unchanged from pre-14.6. `capture_discrete_choice_parameters` returns `[]`. |
| Single domain | Log contains one DecisionRecord. Panel has one set of `{domain}_*` columns. |
| Two domains (vehicle + heating) | Log contains two DecisionRecords. Panel has two sets of `{domain}_*` columns. |
| Empty population (N=0) | DecisionRecord has empty arrays. Panel decision columns are empty. |
| DecisionRecordStep without ChoiceResult | Pass-through (returns state unchanged). |
| Partial run (Year 1 has decisions, Year 2 fails) | Year 1 has decision columns, Year 2 is absent. `concat_tables` with `promote_options="permissive"` handles schema difference. |
| Year without computation result but with decision log | Year is skipped (existing panel behavior — no computation result = skip). Decision records for that year are not included. |
| Non-dict metadata | `DiscreteChoiceError` raised (consistent with other steps). |
| Non-tuple decision log in state | `DiscreteChoiceError` raised with type name. |
| Missing `domain_name` in metadata | Falls back to `"unknown"` domain name. |
| Missing `beta_cost` in metadata | `taste_parameters` dict is empty `{}`. |
| Duplicate `domain_name` in decision log (misconfigured pipeline with two `DecisionRecordStep`s for same domain) | `_build_decision_columns()` raises `DiscreteChoiceError` if duplicate domain names are detected before appending columns. Validate uniqueness at the start of `_build_decision_columns()`. |

### State Key Integration

New state key:
```python
DECISION_LOG_KEY = "discrete_choice_decision_log"  # tuple[DecisionRecord, ...]
```

Reads from state (set by Stories 14.1-14.5):
```python
DISCRETE_CHOICE_RESULT_KEY = "discrete_choice_result"       # ChoiceResult
DISCRETE_CHOICE_METADATA_KEY = "discrete_choice_metadata"   # dict
```

Does NOT modify or read from:
```python
DISCRETE_CHOICE_COST_MATRIX_KEY  # Not needed for decision records
DISCRETE_CHOICE_EXPANSION_KEY    # Not needed for decision records
DISCRETE_CHOICE_ELIGIBILITY_KEY  # Consumed by EligibilityMergeStep before this step runs
```

### Testing Standards

- **Mirror structure:** Tests in `tests/discrete_choice/test_decision_record.py` and `tests/orchestrator/test_panel_decision.py`
- **Self-contained helpers:** Test classes use private `_make_*` helpers (follows test_eligibility.py pattern)
- **Class-based grouping:** `TestDecisionRecord`, `TestDecisionRecordStep`, `TestDecisionRecordStepMultiDomain`
- **Protocol compliance test:** `assert is_protocol_step(step)` for DecisionRecordStep
- **StepRegistry test:** Register and retrieve DecisionRecordStep
- **Golden value test:** Hand-build a 3-household, 2-alternative, 2-domain scenario, verify exact panel columns and values
- **Parquet round-trip test:** Export → reimport → verify column types and values
- **Backward compatibility test:** Panel without any decision log produces identical output to pre-14.6
- **MockAdapter for tests:** Reuse existing test patterns from conftest.py
- **All existing tests must pass unmodified:** No changes to existing test files

### Project Structure Notes

```
src/reformlab/discrete_choice/
├── __init__.py           # MODIFIED: add decision_record exports
├── types.py              # UNCHANGED
├── errors.py             # UNCHANGED
├── domain.py             # UNCHANGED
├── expansion.py          # UNCHANGED
├── reshape.py            # UNCHANGED
├── step.py               # UNCHANGED
├── logit.py              # UNCHANGED
├── domain_utils.py       # UNCHANGED
├── vehicle.py            # UNCHANGED
├── heating.py            # UNCHANGED
├── eligibility.py        # UNCHANGED
└── decision_record.py    # NEW — DecisionRecord, DecisionRecordStep,
                          #        DECISION_LOG_KEY

src/reformlab/orchestrator/
├── panel.py              # MODIFIED: _build_decision_columns helper,
│                         #   from_orchestrator_result extension
├── runner.py             # MODIFIED: capture discrete_choice_parameters
│                         #   in OrchestratorRunner.run()
└── (all others)          # UNCHANGED

src/reformlab/governance/
├── capture.py            # MODIFIED: add capture_discrete_choice_parameters()
└── (all others)          # UNCHANGED

tests/discrete_choice/
├── test_decision_record.py  # NEW — DecisionRecord and DecisionRecordStep tests
└── (all others)             # UNCHANGED

tests/orchestrator/
├── test_panel_decision.py   # NEW — Panel decision column tests, Parquet/CSV export
├── test_panel.py            # UNCHANGED (existing panel tests validate backward compat)
└── (all others)             # UNCHANGED

tests/governance/
├── test_capture_discrete_choice.py  # NEW — capture_discrete_choice_parameters tests
└── (all others)                     # UNCHANGED
```

No new dependencies required — uses PyArrow list types (`pa.list_(pa.float64())`, `pa.list_(pa.string())`) which are part of the existing `pyarrow >= 18.0.0` dependency.

### Cross-Story Dependencies

| Story | Relationship | Notes |
|-------|-------------|-------|
| 14.1 | Depends on | `DISCRETE_CHOICE_COST_MATRIX_KEY`, `DISCRETE_CHOICE_METADATA_KEY` defined in step.py |
| 14.2 | Depends on | `DISCRETE_CHOICE_RESULT_KEY`, `ChoiceResult` type, `TasteParameters` (beta_cost stored in metadata) |
| 14.3 | Depends on | VehicleStateUpdateStep runs before DecisionRecordStep; vehicle domain test fixtures |
| 14.4 | Depends on | HeatingStateUpdateStep runs before DecisionRecordStep; heating domain test fixtures |
| 14.5 | Depends on | EligibilityMergeStep runs before StateUpdateStep; eligibility metadata present in `DISCRETE_CHOICE_METADATA_KEY` |
| 14.7 | Blocks | Notebook demo needs decision records in panel for fleet composition charts |
| 3.7 | Extends | PanelOutput.from_orchestrator_result() extended with decision column injection |
| 5.2 | Extends | Manifest metadata extended with discrete_choice_parameters |

### Out of Scope Guardrails

- **DO NOT** modify `DiscreteChoiceStep` in `step.py`
- **DO NOT** modify `LogitChoiceStep` in `logit.py`
- **DO NOT** modify `EligibilityMergeStep` in `eligibility.py`
- **DO NOT** modify `VehicleStateUpdateStep` in `vehicle.py`
- **DO NOT** modify `HeatingStateUpdateStep` in `heating.py`
- **DO NOT** modify `expand_population()` in `expansion.py`
- **DO NOT** modify `reshape_to_cost_matrix()` in `reshape.py`
- **DO NOT** modify `domain_utils.py`, `domain.py`, `types.py`, `errors.py`
- **DO NOT** modify `Orchestrator` class in `runner.py` (only modify `OrchestratorRunner`)
- **DO NOT** modify `RunManifest` dataclass schema (only add to metadata dict)
- **DO NOT** modify `ComputationAdapter` protocol or `MockAdapter`
- **DO NOT** add numpy or any new dependency
- **DO NOT** modify existing test files — only add new test files
- **DO NOT** implement notebook demo (Story 14.7)
- **DO NOT** implement calibration (Epic 15)
- **DO NOT** implement panel comparison for decision columns (future enhancement)

### References

- [Source: `src/reformlab/orchestrator/panel.py` — PanelOutput class, from_orchestrator_result(), _build_panel_metadata(), to_csv(), to_parquet(), compare_panels()]
- [Source: `src/reformlab/orchestrator/runner.py` — OrchestratorRunner.run(), _capture_manifest_fields(), OrchestratorResult yearly_states]
- [Source: `src/reformlab/governance/capture.py` — capture_assumptions(), capture_policy(), capture_warnings()]
- [Source: `src/reformlab/discrete_choice/step.py` — DISCRETE_CHOICE_COST_MATRIX_KEY, DISCRETE_CHOICE_METADATA_KEY, DiscreteChoiceStep]
- [Source: `src/reformlab/discrete_choice/logit.py` — DISCRETE_CHOICE_RESULT_KEY, LogitChoiceStep, metadata extension (beta_cost, choice_seed)]
- [Source: `src/reformlab/discrete_choice/types.py` — ChoiceResult (chosen, probabilities, utilities, alternative_ids, seed), TasteParameters]
- [Source: `src/reformlab/discrete_choice/eligibility.py` — EligibilityInfo, EligibilityMergeStep, DISCRETE_CHOICE_ELIGIBILITY_KEY]
- [Source: `src/reformlab/discrete_choice/vehicle.py` — VehicleStateUpdateStep, vintage_vehicle key, vehicle_n_keepers metadata]
- [Source: `src/reformlab/discrete_choice/heating.py` — HeatingStateUpdateStep, vintage_heating key, heating_n_keepers metadata]
- [Source: `src/reformlab/discrete_choice/__init__.py` — Public API exports]
- [Source: `src/reformlab/orchestrator/computation_step.py` — COMPUTATION_RESULT_KEY, COMPUTATION_METADATA_KEY]
- [Source: `src/reformlab/computation/types.py` — ComputationResult, PopulationData]
- [Source: `src/reformlab/orchestrator/types.py` — YearState, OrchestratorResult, OrchestratorConfig]
- [Source: `src/reformlab/governance/manifest.py` — RunManifest schema, manifest_id, policy, assumptions, seeds]
- [Source: `tests/orchestrator/test_panel.py` — Panel test patterns, make_orchestrator_result helper]
- [Source: `tests/discrete_choice/test_eligibility.py` — Eligibility test patterns, _make_population, _make_state helpers]
- [Source: `docs/epics.md` — Epic 14 AC for BKL-1406: decision_domain, chosen_alternative, choice_probabilities, utility_values, taste parameters]
- [Source: `docs/project-context.md` — Project rules: PyArrow-first, frozen dataclasses, Protocols not ABCs, adapter isolation]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- No issues encountered during implementation

### Completion Notes List

- Implementation notes:
  - All 7 tasks completed with TDD (red-green-refactor cycle)
  - 46 new tests across 4 test files, all passing
  - Full regression: 2562 tests pass, 0 failures
  - Ruff lint: all checks pass
  - Mypy strict: all 133 source files pass
  - AC-4 deviation: PyArrow CSV writer does not support `pa.list_()` types natively (story assumed it would). Added `_cast_list_columns_to_string()` helper in `to_csv()` to serialize list columns as bracket-delimited strings. Parquet export works natively as specified.
  - `capture_discrete_choice_parameters()` uses duck typing on DecisionRecord attributes, with DECISION_LOG_KEY imported as a constant (not hardcoded string)

- Story creation notes (pre-implementation):
  - Ultimate context engine analysis completed — comprehensive developer guide created
  - Full PanelOutput system analyzed: from_orchestrator_result(), _build_panel_metadata(), to_csv(), to_parquet(), compare_panels()
  - Full manifest/governance system analyzed: RunManifest schema, capture.py functions, _capture_manifest_fields() in runner.py
  - All discrete choice state keys mapped: COST_MATRIX, EXPANSION, METADATA, RESULT, ELIGIBILITY, and metadata dict contents
  - Critical insight: sequential domain execution overwrites shared state keys (domain_name, beta_cost, choice_seed, ChoiceResult)
  - Design decision: DecisionRecordStep snapshots ChoiceResult + metadata per domain before next domain overwrites
  - Panel extension: domain-prefixed columns ({domain}_chosen, {domain}_probabilities, {domain}_utilities)
  - List columns (pa.list_(pa.float64())) chosen for probabilities/utilities — Parquet/pandas/polars native support
  - promote_options="permissive" enables schema flexibility for partial runs with/without decision columns
  - Manifest extension: capture_discrete_choice_parameters() extracts from decision log, scans first year only
  - Governance module decoupled from discrete_choice via duck typing on DecisionRecord attributes
  - All edge cases documented: no decisions, single domain, two domains, empty population, partial runs, pass-through

### File List

#### New Files
- `src/reformlab/discrete_choice/decision_record.py` — DecisionRecord, DecisionRecordStep, DECISION_LOG_KEY
- `tests/discrete_choice/test_decision_record.py` — DecisionRecord type and step tests (21 tests)
- `tests/orchestrator/test_panel_decision.py` — Panel decision column tests, Parquet/CSV export (15 tests)
- `tests/governance/test_capture_discrete_choice.py` — capture_discrete_choice_parameters tests (8 tests)
- `tests/orchestrator/test_runner_discrete_choice.py` — Runner discrete choice capture tests (2 tests)

#### Modified Files
- `src/reformlab/discrete_choice/__init__.py` — Added decision_record exports (DecisionRecord, DecisionRecordStep, DECISION_LOG_KEY) to imports and __all__
- `src/reformlab/orchestrator/panel.py` — Extended from_orchestrator_result() with _build_decision_columns() helper; added _cast_list_columns_to_string() for CSV export; DECISION_LOG_KEY import; promote_options="permissive" for concat; decision_domain_alternatives in metadata
- `src/reformlab/governance/capture.py` — Added capture_discrete_choice_parameters() function
- `src/reformlab/orchestrator/runner.py` — Added capture_discrete_choice_parameters import and call in OrchestratorRunner.run(); discrete_choice_parameters in manifest metadata
