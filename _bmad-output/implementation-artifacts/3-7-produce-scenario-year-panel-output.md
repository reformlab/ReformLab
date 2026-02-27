# Story 3.7: Produce Scenario-Year Panel Output

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **policy analyst**,
I want **to produce a scenario-year panel output dataset from a completed orchestrator run**,
so that **I can analyze year-by-year household-level results, export them to CSV/Parquet, and compare baseline vs reform scenarios**.

## Acceptance Criteria

From backlog (BKL-307), aligned with FR18, FR33.

Scope note: this story adds panel dataset generation from orchestrator results. The panel is a household-by-year table containing all computed fields from each year's state. It builds on Story 3-6 execution trace metadata and completes Epic 3 orchestrator deliverables.

1. **AC-1: Panel output contains one row per household per year**
   - Given a completed 10-year orchestrator run with N households, when panel output is produced, then:
     - Total rows = N households × 10 years
     - Each row has a `year` column identifying the simulation year
     - Each row has a `household_id` column (or equivalent entity identifier)
     - All computed fields from `YearState.data` are included as columns

2. **AC-2: Panel output is exportable to CSV with correct types**
   - Given a panel dataset, when exported to CSV, then:
     - The file is readable by pandas with correct column names
     - Numeric columns preserve numeric types (integers, floats)
     - String columns preserve string encoding
     - No data loss or corruption during export

3. **AC-3: Panel output is exportable to Parquet with correct schema**
   - Given a panel dataset, when exported to Parquet, then:
     - The file is readable by pandas/polars with correct schema
     - Column types are preserved (int64, float64, string, etc.)
     - Arrow/Parquet metadata includes schema version
     - Large panels (100k+ rows) export efficiently (< 5 seconds)

4. **AC-4: Baseline and reform panels are comparable**
   - Given two completed runs (baseline and reform), when panel outputs are compared, then:
     - Per-household per-year differences are computable via join on (`household_id`, `year`)
     - A comparison function returns a delta panel with difference columns
     - Missing households or years in one panel are flagged (not silently dropped)

5. **AC-5: Panel includes orchestrator metadata**
   - Given a panel produced from an orchestrator run, when inspected, then:
     - Panel metadata includes `start_year`, `end_year`, `seed`, `step_pipeline` from run
     - Scenario version (if available) is attached to panel metadata
     - Panel can be traced back to its source run via metadata

6. **AC-6: Empty or failed runs produce appropriate output**
   - Given an orchestrator run with no completed years (failure on first year), when panel output is requested, then:
     - An empty panel is returned (zero rows, correct columns if schema is known)
     - Error information from the run is preserved in panel metadata
   - Given a partial run (some years completed before failure), when panel output is requested, then:
     - Panel includes data for completed years only
     - Metadata indicates partial completion and failure point

## Dependencies

- **Required prior stories (all done):**
  - Story 3-1 (BKL-301): Yearly loop orchestrator - provides `Orchestrator`, `OrchestratorResult`, `YearState`
  - Story 3-2 (BKL-302): Step interface - provides step registration and execution
  - Story 3-3 (BKL-303): Carry-forward step - established state transition patterns
  - Story 3-4 (BKL-304): Vintage transition step - adds vintage data to state
  - Story 3-5 (BKL-305): ComputationStep - adds computation results to state
  - Story 3-6 (BKL-306): Log seed controls - provides `OrchestratorResult.metadata` with trace data
- **Current prerequisite status (from sprint-status.yaml, checked 2026-02-27):**
  - `3-1-implement-yearly-loop-orchestrator`: `done`
  - `3-2-define-orchestrator-step-interface`: `done`
  - `3-3-implement-carry-forward-step`: `done`
  - `3-4-implement-vintage-transition-step`: `done`
  - `3-5-integrate-computationadapter-calls`: `done`
  - `3-6-log-seed-controls`: `done`
- **Follow-on stories:**
  - Story 4-1 (BKL-401): Distributional indicators - consumes panel output for decile analysis
  - Story 4-5 (BKL-405): Scenario comparison tables - uses panel comparison
  - Story 5-1 (BKL-501): Immutable run manifest - captures panel hash
  - Story 6-1 (BKL-601): Stable Python API - exposes panel output through API

## Tasks / Subtasks

- [ ] Task 0: Review prerequisites and design panel data model (AC: dependency check)
  - [ ] 0.1 Verify Story 3-6 status is `done` in `sprint-status.yaml`
  - [ ] 0.2 Review `OrchestratorResult.yearly_states` structure and `YearState.data` schema
  - [ ] 0.3 Decide on panel data structure (polars DataFrame or pandas DataFrame)
  - [ ] 0.4 Define household identifier column name convention (`household_id`)

- [ ] Task 1: Implement `PanelOutput` dataclass and `from_orchestrator_result` factory (AC: #1, #5, #6)
  - [ ] 1.1 Create `src/reformlab/orchestrator/panel.py` module
  - [ ] 1.2 Define `PanelOutput` dataclass:
    - `data`: DataFrame (household × year with all computed columns)
    - `metadata`: dict with `start_year`, `end_year`, `seed`, `step_pipeline`, `scenario_version`, `partial`, `errors`
    - `shape`: tuple[int, int] (rows, columns)
  - [ ] 1.3 Implement `PanelOutput.from_orchestrator_result(result: OrchestratorResult) -> PanelOutput`:
    - Iterate `result.yearly_states` in year order
    - For each year, extract `YearState.data` and add `year` column
    - Concatenate into a single DataFrame
    - Handle partial results (failed_year present)
    - Copy relevant metadata from `result.metadata`
  - [ ] 1.4 Handle empty results gracefully (zero yearly_states → empty DataFrame)

- [ ] Task 2: Implement CSV export (AC: #2)
  - [ ] 2.1 Add `PanelOutput.to_csv(path: str | Path) -> Path` method
  - [ ] 2.2 Write CSV with header row containing column names
  - [ ] 2.3 Ensure numeric types preserved in output (no quoting of numbers)
  - [ ] 2.4 Add metadata comment header (optional, configurable)

- [ ] Task 3: Implement Parquet export (AC: #3)
  - [ ] 3.1 Add `PanelOutput.to_parquet(path: str | Path) -> Path` method
  - [ ] 3.2 Write Parquet with correct column types (int64, float64, string)
  - [ ] 3.3 Include schema version in Parquet metadata (`reformlab_panel_version`)
  - [ ] 3.4 Performance test with 100k+ row panel (target: < 5 seconds)

- [ ] Task 4: Implement panel comparison function (AC: #4)
  - [ ] 4.1 Add `compare_panels(baseline: PanelOutput, reform: PanelOutput) -> PanelOutput` function
  - [ ] 4.2 Join on (`household_id`, `year`) with outer join
  - [ ] 4.3 Compute difference columns for numeric fields (reform - baseline)
  - [ ] 4.4 Flag rows present in only one panel (baseline_only, reform_only markers)
  - [ ] 4.5 Preserve metadata from both panels (baseline_metadata, reform_metadata)

- [ ] Task 5: Add module exports and tests (AC: all)
  - [ ] 5.1 Export `PanelOutput`, `compare_panels` from `src/reformlab/orchestrator/__init__.py`
  - [ ] 5.2 Create `tests/orchestrator/test_panel.py` with tests:
    - Panel from successful 10-year run (row count, columns, types)
    - Panel from partial run (completed years only)
    - Panel from empty run (zero rows)
    - CSV export and reload (round-trip)
    - Parquet export and reload (round-trip, type preservation)
    - Panel comparison (differences computed, missing rows flagged)
  - [ ] 5.3 Run quality gates:
    - `ruff check src/reformlab/orchestrator tests/orchestrator`
    - `mypy src/reformlab/orchestrator`
    - `pytest tests/orchestrator/test_panel.py tests/orchestrator/test_runner.py -v`

## Dev Notes

### Architecture Alignment

**From architecture.md - Data Contracts:**
> Output: yearly panel datasets, scenario comparison tables, indicator exports

**From architecture.md - Step-Pluggable Dynamic Orchestrator:**
> For each year t in [start_year .. end_year]:
>   4. Record year-t results and manifest entry

**From PRD - FR18:**
> System outputs year-by-year panel results for each scenario.

**From PRD - FR33:**
> User can export tables and indicators in CSV/Parquet for downstream reporting.

**From backlog BKL-307:**
> Produce scenario-year panel output dataset
> - Given a completed 10-year run, when panel output is produced, then it contains one row per household per year with all computed fields.
> - Given panel output, when exported to CSV/Parquet, then the file is readable by pandas/polars with correct types.
> - Given baseline and reform runs, when panel outputs are compared, then per-household per-year differences are computable.

### Existing Code Patterns to Follow

**OrchestratorResult structure from `types.py`:**
```python
@dataclass
class OrchestratorResult:
    success: bool
    yearly_states: dict[int, YearState] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    failed_year: int | None = None
    failed_step: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class YearState:
    year: int
    data: dict[str, Any] = field(default_factory=dict)
    seed: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
```

**Metadata keys from Story 3-6 (`runner.py`):**
```python
STEP_EXECUTION_LOG_KEY = "step_execution_log"
SEED_LOG_KEY = "seed_log"
# Additional metadata: start_year, end_year, seed, step_pipeline
```

**Export patterns from data layer (`ingestion.py`, `pipeline.py`):**
```python
# CSV reading pattern
df = pd.read_csv(path)

# Parquet writing pattern
df.to_parquet(path, engine="pyarrow")
```

### Implementation Strategy

1. **Use pandas for MVP, polars optional:** Start with pandas DataFrames for compatibility with existing data layer patterns. Polars can be added as an optimization in Phase 2.

2. **Panel column structure:** Each row has:
   - `household_id`: identifier from population data (or synthetic index)
   - `year`: simulation year from `YearState.year`
   - All columns from `YearState.data` flattened (nested dicts → prefixed columns)

3. **Metadata inheritance:** Panel metadata should include:
   - `start_year`, `end_year`, `seed`, `step_pipeline` from orchestrator config
   - `seed_log`, `step_execution_log` from Story 3-6 trace
   - `partial: bool` if run failed before completion
   - `errors: list[str]` if any errors occurred

4. **Comparison join strategy:**
   - Outer join on (`household_id`, `year`) to capture all combinations
   - Suffix columns: `_baseline`, `_reform` for original values
   - Create `_diff` columns for numeric fields
   - Add `_source` column: "both", "baseline_only", "reform_only"

### Data Model Notes

**Expected `YearState.data` structure (from computation and vintage steps):**
```python
{
    "population": [...],  # List of household dicts or DataFrame
    "computation_result": {...},  # From ComputationStep
    "vintage_state": {...},  # From VintageTransitionStep
    # Additional step outputs
}
```

**Panel flattening approach:**
- If `data["population"]` is a DataFrame or list of dicts, expand to rows
- Each household becomes one row per year
- Nested dict values are prefixed (e.g., `vintage_vehicle_age`)

### Performance Considerations

- **Memory:** Panel with 100k households × 10 years × 50 columns ≈ 50M cells. Pandas handles this comfortably on 16GB laptop.
- **Export speed:** Parquet export target < 5 seconds for 1M rows. Use `pyarrow` engine for best performance.
- **Comparison:** Outer join on indexed columns is O(n log n). Pre-sort by (`household_id`, `year`) for efficiency.

### Scope Guardrails

- **In scope:**
  - `PanelOutput` dataclass with factory from `OrchestratorResult`
  - CSV and Parquet export methods
  - Panel comparison function for baseline/reform analysis
  - Unit tests for panel generation, export, and comparison

- **Out of scope:**
  - Indicator computation from panels (Story 4-1)
  - Run manifest file generation (Story 5-1)
  - GUI visualization of panels (Epic 6)
  - Panel streaming for very large populations
  - Database persistence of panels

### Testing Notes

- Use `tmp_path` fixture for export file tests
- Round-trip tests: create panel → export → import → compare
- Mock `OrchestratorResult` with known data for deterministic assertions
- Test edge cases: empty run, single year, partial failure
- Comparison tests: identical panels, disjoint panels, overlapping panels

### Project Structure Notes

- New module: `src/reformlab/orchestrator/panel.py`
- New tests: `tests/orchestrator/test_panel.py`
- Exports via: `src/reformlab/orchestrator/__init__.py`
- No new dependencies (uses pandas and pyarrow already in project)

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Data Contracts]
- [Source: _bmad-output/planning-artifacts/architecture.md#Step-Pluggable Dynamic Orchestrator]
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-307]
- [Source: _bmad-output/planning-artifacts/prd.md#FR18]
- [Source: _bmad-output/planning-artifacts/prd.md#FR33]
- [Source: src/reformlab/orchestrator/runner.py]
- [Source: src/reformlab/orchestrator/types.py]
- [Source: _bmad-output/implementation-artifacts/3-6-log-seed-controls.md]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
