# Story 3.7: Produce Scenario-Year Panel Output

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **policy analyst**,
I want **to produce a scenario-year panel output dataset from a completed orchestrator run**,
so that **I can analyze year-by-year household-level results, export them to CSV/Parquet, and compare baseline vs reform scenarios**.

## Acceptance Criteria

From backlog (BKL-307), aligned with FR18, FR33.

Scope note: this story adds panel dataset generation from orchestrator results. The panel is a household-by-year table built from yearly computation outputs and run metadata. It builds on Story 3-5 (`ComputationStep`) and Story 3-6 (trace metadata) and completes Epic 3 orchestrator output deliverables.

1. **AC-1: Panel output contains one row per household per completed year**
   - Given a successful 10-year run with `N` households per year, when panel output is produced, then:
     - Total rows = `N * 10`
     - Each row includes a `year` column
     - Each row includes a `household_id` column (or configured ID field mapped to `household_id`)
     - Columns include household-level computed fields from `ComputationResult.output_fields`
   - Given a partial run, row count equals the sum of rows across completed years only.

2. **AC-2: Panel output is exportable to CSV for downstream analysis**
   - Given a panel dataset, when exported to CSV, then:
     - The file is UTF-8 and readable by pandas/polars
     - Column names and row counts match the in-memory panel
     - Numeric and string values round-trip without corruption

3. **AC-3: Panel output is exportable to Parquet with correct schema**
   - Given a panel dataset, when exported to Parquet, then:
     - The file is readable by pandas/polars with correct schema
     - Arrow column types from the panel are preserved
     - Panel-level metadata includes a stable panel format version

4. **AC-4: Baseline and reform panels are comparable**
   - Given two completed runs (baseline and reform), when panel outputs are compared, then:
     - Per-household per-year alignment is computable using join keys (`household_id`, `year`)
     - Missing households/years are flagged (not silently dropped)
     - Numeric deltas are computable for shared numeric fields

5. **AC-5: Panel includes orchestrator metadata**
   - Given a panel produced from an orchestrator run, when inspected, then:
     - Panel metadata includes `start_year`, `end_year`, `seed`, `step_pipeline`
     - Panel metadata carries forward Story 3-6 trace keys (`seed_log`, `step_execution_log`)
     - `scenario_version` is attached if present in run metadata
     - Panel can be traced back to its source run via metadata

6. **AC-6: Empty or failed runs produce appropriate output**
   - Given an orchestrator run with no completed years (failure on first year), when panel output is requested, then:
     - An empty panel is returned (zero rows, key columns if schema is known)
     - Error information from the run is preserved in panel metadata
   - Given a partial run (some years completed before failure), when panel output is requested, then:
     - Panel includes data for completed years only
     - Metadata indicates partial completion and failure point

## Dependencies

- **Required prior stories:**
  - Story 3-1 (BKL-301): Yearly loop orchestrator - provides `OrchestratorResult`, `YearState`
  - Story 3-2 (BKL-302): Step interface - provides stable step pipeline contract
  - Story 3-5 (BKL-305): ComputationStep - stores `ComputationResult` under `COMPUTATION_RESULT_KEY`
  - Story 3-6 (BKL-306): Log seed controls - provides trace metadata keys in `OrchestratorResult.metadata`
- **Current prerequisite status (from `_bmad-output/implementation-artifacts/sprint-status.yaml`, checked 2026-02-27):**
  - `3-1-implement-yearly-loop-orchestrator`: `done`
  - `3-2-define-orchestrator-step-interface`: `done`
  - `3-5-integrate-computationadapter-calls`: `done`
  - `3-6-log-seed-controls`: `done`
- **Follow-on stories:**
  - Story 4-1 (BKL-401): Distributional indicators - consumes panel output for decile analysis
  - Story 4-5 (BKL-405): Scenario comparison tables - builds reporting tables from panel alignment/deltas
  - Story 5-1 (BKL-501): Immutable run manifest - captures panel hash
  - Story 6-1 (BKL-601): Stable Python API - exposes panel output through API

## Tasks / Subtasks

- [x] Task 0: Confirm prerequisites and data contracts (AC: dependency check)
  - [x] 0.1 Verify Story 3-5 and 3-6 statuses are `done` in `_bmad-output/implementation-artifacts/sprint-status.yaml`
  - [x] 0.2 Review `OrchestratorResult.yearly_states` and confirm `COMPUTATION_RESULT_KEY` contract in `YearState.data`
  - [x] 0.3 Confirm canonical tabular source is `ComputationResult.output_fields` (PyArrow table)
  - [x] 0.4 Define/confirm household key mapping to output `household_id`

- [x] Task 1: Implement `PanelOutput` and factory from orchestrator results (AC: #1, #5, #6)
  - [x] 1.1 Create `src/reformlab/orchestrator/panel.py` module
  - [x] 1.2 Define `PanelOutput` dataclass:
    - `table`: `pa.Table` (household x year panel)
    - `metadata`: dict with `start_year`, `end_year`, `seed`, `step_pipeline`, `seed_log`, `step_execution_log`, `partial`, `errors`
    - `shape`: tuple[int, int] (rows, columns)
  - [x] 1.3 Implement `PanelOutput.from_orchestrator_result(result: OrchestratorResult) -> PanelOutput`:
    - Iterate `result.yearly_states` in year order
    - For each year, extract `YearState.data[COMPUTATION_RESULT_KEY].output_fields`
    - Add/normalize `household_id` and add `year` column
    - Concatenate yearly tables into one panel table
    - Handle partial results (failed_year present)
    - Copy relevant metadata from `result.metadata` and `result.errors`
  - [x] 1.4 Handle empty results gracefully (zero completed years -> empty table with key columns when schema known)

- [x] Task 2: Implement CSV export (AC: #2)
  - [x] 2.1 Add `PanelOutput.to_csv(path: str | Path) -> Path` method
  - [x] 2.2 Export with stable column names and UTF-8 encoding
  - [x] 2.3 Validate round-trip row count and key columns using pandas/polars in tests

- [x] Task 3: Implement Parquet export (AC: #3)
  - [x] 3.1 Add `PanelOutput.to_parquet(path: str | Path) -> Path` method
  - [x] 3.2 Write Parquet with Arrow schema/type preservation
  - [x] 3.3 Include panel format metadata key (e.g., `reformlab_panel_version`)

- [x] Task 4: Implement comparison helper for panel alignment/deltas (AC: #4)
  - [x] 4.1 Add `compare_panels(baseline: PanelOutput, reform: PanelOutput) -> PanelOutput` helper
  - [x] 4.2 Outer-join on (`household_id`, `year`) to retain unmatched rows
  - [x] 4.3 Add row origin marker (`both`, `baseline_only`, `reform_only`)
  - [x] 4.4 Add delta columns for shared numeric fields only
  - [x] 4.5 Preserve baseline/reform provenance in comparison metadata

- [x] Task 5: Add module exports and focused tests (AC: all)
  - [x] 5.1 Export `PanelOutput`, `compare_panels` from `src/reformlab/orchestrator/__init__.py`
  - [x] 5.2 Create `tests/orchestrator/test_panel.py` with tests:
    - Panel from successful 10-year run (row count, columns, types)
    - Panel from partial run (completed years only)
    - Panel from empty run (zero rows)
    - CSV export and reload (row/column integrity)
    - Parquet export and reload (schema/type preservation)
    - Panel comparison (alignment, origin markers, numeric deltas)
  - [x] 5.3 Run quality gates:
    - `ruff check src/reformlab/orchestrator tests/orchestrator`
    - `mypy src/reformlab/orchestrator`
    - `pytest tests/orchestrator/test_panel.py tests/orchestrator/test_runner.py tests/orchestrator/test_computation_step.py -v`

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

**Computation payload contract from Story 3-5 (`computation_step.py` + `computation/types.py`):**
```python
COMPUTATION_RESULT_KEY = "computation_result"

@dataclass(frozen=True)
class ComputationResult:
    output_fields: pa.Table
    adapter_version: str
    period: int
```

**Trace metadata keys from Story 3-6 (`runner.py`):**
```python
STEP_EXECUTION_LOG_KEY = "step_execution_log"
SEED_LOG_KEY = "seed_log"
# Additional metadata: start_year, end_year, seed, step_pipeline
```

### Implementation Strategy

1. **Use Arrow table as canonical panel representation:** Build and store panel as `pa.Table` to align with computation output contracts and Parquet interoperability.

2. **Panel assembly from completed years only:**
   - Read `COMPUTATION_RESULT_KEY` from each `YearState.data`
   - Use `ComputationResult.output_fields` as the tabular row source
   - Add `year` column and normalize household identifier to `household_id`

3. **Panel column structure:** Each row has:
   - `household_id`: identifier from population data (or synthetic index)
   - `year`: simulation year from `YearState.year`
   - Household-level computed fields from `output_fields`

4. **Metadata inheritance:** Panel metadata should include:
   - `start_year`, `end_year`, `seed`, `step_pipeline` from orchestrator config
   - `seed_log`, `step_execution_log` from Story 3-6 trace
   - `partial: bool` if run failed before completion
   - `errors: list[str]` if any errors occurred

5. **Comparison helper strategy (bounded scope):**
   - Outer join on (`household_id`, `year`) to capture all combinations
   - Add origin marker and numeric deltas only
   - Do not implement indicator/report tables in this story

### Data Model Notes

**Expected `YearState.data` shape for this story:**
```python
{
    "computation_result": ComputationResult(...),  # required for panel rows
    # other step outputs may exist but are not panel row sources in this story
}
```

**Panel row source rule:**
- Use only household-level fields from `ComputationResult.output_fields` for row columns.
- Preserve non-tabular run context in `PanelOutput.metadata` instead of flattening arbitrary objects from `YearState.data`.

### Performance Considerations

- **Memory:** Panel size scales with `sum(rows_per_completed_year)`; avoid unnecessary DataFrame conversions during assembly.
- **Export:** Prefer direct Arrow-to-Parquet writing to preserve types.
- **Comparison:** Outer join cost grows with panel size; tests should include representative medium-size fixtures.

### Scope Guardrails

- **In scope:**
  - `PanelOutput` dataclass with factory from `OrchestratorResult`
  - CSV and Parquet export methods
  - Minimal comparison helper for baseline/reform alignment and numeric deltas
  - Unit tests for panel generation, export, metadata, and comparison helper

- **Out of scope:**
  - Indicator computation from panels (Story 4-1)
  - Scenario comparison report/table generation (Story 4-5)
  - Run manifest file generation (Story 5-1)
  - GUI visualization of panels (Epic 6)
  - Streaming/chunked panel processing for very large populations
  - Database persistence of panels

### Testing Notes

- Use `tmp_path` fixture for export file tests
- Round-trip tests: create panel -> export -> import -> compare
- Mock `OrchestratorResult` with explicit `ComputationResult.output_fields` fixtures
- Test edge cases: empty run, single year, partial failure
- Comparison tests: identical panels, disjoint panels, overlapping panels

### Project Structure Notes

- New module: `src/reformlab/orchestrator/panel.py`
- New tests: `tests/orchestrator/test_panel.py`
- Exports via: `src/reformlab/orchestrator/__init__.py`
- No new dependencies (uses existing pyarrow/pandas/polars interoperability)

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Data Contracts]
- [Source: _bmad-output/planning-artifacts/architecture.md#Step-Pluggable Dynamic Orchestrator]
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-307]
- [Source: _bmad-output/planning-artifacts/prd.md#FR18]
- [Source: _bmad-output/planning-artifacts/prd.md#FR33]
- [Source: src/reformlab/computation/types.py]
- [Source: src/reformlab/orchestrator/computation_step.py]
- [Source: src/reformlab/orchestrator/runner.py]
- [Source: src/reformlab/orchestrator/types.py]
- [Source: _bmad-output/implementation-artifacts/3-6-log-seed-controls.md]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - No debugging issues encountered.

### Completion Notes List

- Implemented `PanelOutput` dataclass with `from_orchestrator_result()` factory method that builds household-by-year panel tables from `OrchestratorResult.yearly_states`
- Panel assembly iterates years in sorted order, extracts `ComputationResult.output_fields` from each `YearState.data[COMPUTATION_RESULT_KEY]`, adds `year` column, and concatenates into single PyArrow table
- Implemented `to_csv()` and `to_parquet()` export methods with proper type preservation and panel version metadata
- Implemented `compare_panels()` helper using pure PyArrow for full outer join on (household_id, year), adding `_origin` markers and `_delta_*` columns for numeric fields
- All 16 panel-specific tests pass covering: 10-year runs, partial runs, empty runs, CSV/Parquet roundtrips, metadata preservation, and panel comparison scenarios
- Full test suite regression check: 891 passed, 2 skipped (no regressions)
- Quality gates passed: ruff (0 errors on new files), mypy (no issues in 8 orchestrator files)

### File List

**New files:**
- `src/reformlab/orchestrator/panel.py` - PanelOutput dataclass and compare_panels helper
- `tests/orchestrator/test_panel.py` - 16 tests for panel generation, export, and comparison

**Modified files:**
- `src/reformlab/orchestrator/__init__.py` - Added exports for PanelOutput, compare_panels, PANEL_VERSION
