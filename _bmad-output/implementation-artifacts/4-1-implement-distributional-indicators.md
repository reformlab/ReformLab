# Story 4.1: Implement Distributional Indicators by Income Decile

Status: ready-for-dev

## Story

As a **policy analyst**,
I want **to compute distributional indicators grouped by income decile from scenario run results**,
so that **I can analyze how environmental policies affect different income groups and identify winners and losers across the income distribution**.

## Acceptance Criteria

From backlog (BKL-401), aligned with FR19 and NFR5.

Scope note: this story implements the core decile indicator engine over `PanelOutput` (read-only consumer of orchestrator outputs). File export workflows remain downstream concerns (Story 4-5 and interface stories), while this story provides a stable in-memory tabular indicator result.

1. **AC-1: Decile computation for completed runs**
   - Given a completed scenario run with household-level results provided as `PanelOutput`
   - When `compute_distributional_indicators()` is invoked
   - Then households with valid income are assigned to 10 income deciles (`D1`-`D10`)
   - And decile indicators are returned for each numeric panel field

2. **AC-2: Missing income data handling**
   - Given a panel where some households have null/missing income
   - When decile computation runs
   - Then those households are excluded from decile assignment
   - And a warning is emitted with the exact excluded-household count
   - And excluded count is present in result metadata

3. **AC-3: Standard indicator metrics**
   - Given decile-grouped households
   - When indicators are computed
   - Then metrics include `count`, `mean`, `median`, `sum`, `min`, and `max` per decile
   - And metrics are computed for all numeric output fields in the panel

4. **AC-4: Multi-year support**
   - Given a multi-year panel with a `year` column
   - When analysis is requested with `by_year=True`
   - Then indicators are grouped by `(year, decile)`
   - And when `aggregate_years=True`, indicators are grouped by `decile` across all years

5. **AC-5: Stable tabular result contract**
   - Given computed distributional indicators
   - When `IndicatorResult.to_table()` is called
   - Then a PyArrow table is returned with stable columns for decile, metric, field name, and value
   - And the table is suitable for downstream CSV/Parquet export workflows

## Tasks / Subtasks

- [ ] Task 0: Confirm prerequisites and input contracts (AC: dependency check)
  - [ ] 0.1 Verify Story 3-6 and Story 3-7 are `done` in `_bmad-output/implementation-artifacts/sprint-status.yaml`
  - [ ] 0.2 Confirm `PanelOutput` contract in `src/reformlab/orchestrator/panel.py` (`table`, `metadata`, `year`, `household_id`)
  - [ ] 0.3 Confirm canonical income field name/config contract for decile assignment

- [ ] Task 1: Create indicator types and configuration models (AC: #1, #3, #5)
  - [ ] 1.1 Define `DecileIndicators` for decile-level metric payloads
  - [ ] 1.2 Define `IndicatorResult` for result table + metadata + warnings
  - [ ] 1.3 Define `DistributionalConfig` (`income_field`, `by_year`, `aggregate_years`, optional weights)
  - [ ] 1.4 Add definitions to `src/reformlab/indicators/types.py`

- [ ] Task 2: Implement income decile assignment (AC: #1, #2)
  - [ ] 2.1 Create `assign_deciles()` in `src/reformlab/indicators/deciles.py`
  - [ ] 2.2 Compute decile boundaries with PyArrow quantile utilities
  - [ ] 2.3 Exclude null income records with explicit warning + excluded count
  - [ ] 2.4 Ensure deterministic boundary behavior for tied values

- [ ] Task 3: Implement decile aggregations (AC: #1, #3)
  - [ ] 3.1 Create `aggregate_by_decile()` in `src/reformlab/indicators/deciles.py`
  - [ ] 3.2 Compute `count`, `mean`, `median`, `sum`, `min`, `max` for each numeric field
  - [ ] 3.3 Use vectorized PyArrow operations only (no row-wise Python loops on hot paths)

- [ ] Task 4: Implement main distributional computation API (AC: #1, #2, #3, #4)
  - [ ] 4.1 Create `compute_distributional_indicators(panel: PanelOutput, config: DistributionalConfig)` in `src/reformlab/indicators/distributional.py`
  - [ ] 4.2 Support single-year (default), `by_year=True`, and `aggregate_years=True` modes
  - [ ] 4.3 Return `IndicatorResult` containing stable metadata and warning details

- [ ] Task 5: Implement stable in-memory result table output (AC: #5)
  - [ ] 5.1 Add `IndicatorResult.to_table() -> pa.Table`
  - [ ] 5.2 Define and test stable output column contract for downstream export/comparison flows
  - [ ] 5.3 Keep file export (`to_csv`/`to_parquet`) out of this story scope

- [ ] Task 6: Add focused tests and quality gates (AC: all)
  - [ ] 6.1 Create `tests/indicators/test_distributional.py`
  - [ ] 6.2 Test decile assignment across controlled income distributions
  - [ ] 6.3 Test missing income exclusion + warning emission + metadata count
  - [ ] 6.4 Test metric correctness for numeric fields
  - [ ] 6.5 Test multi-year `by_year` and `aggregate_years` behavior
  - [ ] 6.6 Test `IndicatorResult.to_table()` schema stability
  - [ ] 6.7 Run `ruff check src/reformlab/indicators tests/indicators`
  - [ ] 6.8 Run `mypy src/reformlab/indicators`
  - [ ] 6.9 Run `pytest tests/indicators/test_distributional.py -v`

- [ ] Task 7: Module exports and API surface (AC: #5)
  - [ ] 7.1 Export public API from `src/reformlab/indicators/__init__.py`
  - [ ] 7.2 Add concise docstrings for public indicator functions/classes

## Dependencies

- **Required prior stories:**
  - Story 3-6 (BKL-306): Seed/step trace metadata available in orchestrator outputs
  - Story 3-7 (BKL-307): `PanelOutput` available as canonical household-year input
- **Current prerequisite status (from `_bmad-output/implementation-artifacts/sprint-status.yaml`, checked 2026-02-27):**
  - `3-6-log-seed-controls`: `done`
  - `3-7-produce-scenario-year-panel-output`: `done`
- **Follow-on stories:**
  - Story 4-2 (BKL-402): Geographic aggregation indicators (depends on 4-1)
  - Story 4-3 (BKL-403): Welfare indicators (depends on 4-1)
  - Story 4-4 (BKL-404): Fiscal indicators (depends on 4-1)
  - Story 4-5 (BKL-405): Scenario comparison/export tables across indicator families

## Dev Notes

### Architecture Patterns

This story implements the first component of the Indicator Engine layer from the architecture:

```
┌─────────────────────────────────────────────────┐
│  Indicator Engine (distributional/welfare/fiscal)│  ← Story 4-1 starts here
├─────────────────────────────────────────────────┤
│  Governance (manifests, assumptions, lineage)    │
├─────────────────────────────────────────────────┤
│  Dynamic Orchestrator (year loop + step pipeline)│  ← Epic 3 complete
```

The indicator layer sits above the orchestrator and consumes `PanelOutput` from `src/reformlab/orchestrator/panel.py`. This story must remain a read-only consumer of orchestrator results (no orchestration state mutations).

### Data Flow

```
OrchestratorResult
    ↓
PanelOutput.from_orchestrator_result()
    ↓
compute_distributional_indicators(panel: PanelOutput)
    ↓
IndicatorResult (with DecileIndicators per numeric field)
    ↓
IndicatorResult.to_table() for downstream export/comparison workflows
```

### Technical Stack

- **PyArrow** for all data manipulation (consistent with existing codebase)
- Use `pyarrow.compute` functions for vectorized aggregation
- Follow existing patterns from `src/reformlab/orchestrator/panel.py` for table handling and metadata contracts

### Key Implementation Details

1. **Decile Assignment Algorithm:**
   - Use `pyarrow.compute.quantile()` to find decile boundaries (0.1, 0.2, ..., 0.9)
   - Assign each household to decile 1-10 based on income position
   - Handle ties at boundaries consistently (include in lower decile)

2. **Missing Income Handling:**
   - Use `pyarrow.compute.is_null()` to identify missing values
   - Filter out nulls before decile computation
   - Emit warning via Python `warnings` module with count
   - Store exclusion count in result metadata

3. **Aggregation Implementation:**
   - Use `pyarrow.compute.count()`, `mean()`, `sum()`, `min()`, `max()`
   - For median: use `approximate_median()` or sort-based exact median
   - Group-by using PyArrow's Table.group_by() method

4. **Multi-Year Support:**
   - Panel already has `year` column from orchestrator
   - Group by (decile, year) for year-by-year analysis
   - Aggregate across years by grouping by decile only

### Scope Guardrails

- **In scope:**
  - Income-decile assignment and metric aggregation over `PanelOutput`
  - Single-year and multi-year (`by_year` / `aggregate_years`) indicator computation
  - Stable in-memory indicator table contract (`to_table()`)
- **Out of scope:**
  - CSV/Parquet file export methods on indicator objects
  - Scenario side-by-side comparison tables across indicator families (Story 4-5)
  - Governance manifest persistence for indicator outputs (Epic 5)

### File Structure

```
src/reformlab/indicators/
├── __init__.py           # Public exports
├── types.py              # DecileIndicators, IndicatorResult, DistributionalConfig
├── deciles.py            # assign_deciles(), aggregate_by_decile()
└── distributional.py     # compute_distributional_indicators()
```

### Testing Standards

- Use pytest with fixtures from existing test patterns
- Create test fixtures in `tests/indicators/conftest.py`
- Test with synthetic populations having known income distributions
- Verify decile boundaries match expected percentiles
- Test edge cases: empty panels, all-null income, single household

### Project Structure Notes

- Follows existing subsystem pattern (`computation/`, `data/`, `templates/`, `orchestrator/`, `vintage/`, `indicators/`)
- Uses PyArrow consistently with rest of codebase (not pandas)
- Follows existing docstring style with Args/Returns sections
- Uses `from __future__ import annotations` for type hints

### Performance Considerations

- Vectorized PyArrow operations (not row-by-row Python loops) per NFR2
- Target: 100k households analyzed in under 5 seconds per NFR5
- Memory efficient: work with PyArrow Tables, no full DataFrame copies

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Subsystems] - Indicator layer definition
- [Source: _bmad-output/planning-artifacts/prd.md#FR19] - FR19: Analyst can compute distributional indicators by income decile
- [Source: _bmad-output/planning-artifacts/prd.md#FR33] - FR33: User can export tables and indicators in CSV/Parquet (downstream via table contract)
- [Source: _bmad-output/planning-artifacts/prd.md#NFR5] - NFR5: Analytical operations execute in under 5 seconds for 100k households
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-401] - Story acceptance criteria
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-402-BKL-405] - Epic-4 dependency chain
- [Source: src/reformlab/orchestrator/panel.py] - PanelOutput class, input data structure
- [Source: src/reformlab/data/schemas.py] - SYNTHETIC_POPULATION_SCHEMA with income field

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
