# Story 4.1: Implement Distributional Indicators by Income Decile

Status: ready-for-dev

## Story

As a **policy analyst**,
I want **to compute distributional indicators grouped by income decile from scenario run results**,
so that **I can analyze how environmental policies affect different income groups and identify winners and losers across the income distribution**.

## Acceptance Criteria

1. **AC1: Decile computation for completed runs**
   - Given a completed scenario run with household-level results (via PanelOutput)
   - When distributional analysis is invoked
   - Then indicators are computed for each of the 10 income deciles (D1-D10)
   - And the output includes per-decile aggregations of all numeric output fields

2. **AC2: Missing income data handling**
   - Given a population with missing income data for some households
   - When analysis runs
   - Then those households are flagged and excluded from decile assignment
   - And a count warning is emitted with the exact number of excluded households
   - And the analysis proceeds with valid households only

3. **AC3: Standard indicator metrics**
   - Given decile-grouped results
   - When indicators are computed
   - Then the following metrics are produced per decile: count, mean, median, sum, min, max
   - And indicators are available for all numeric fields in the panel output

4. **AC4: Multi-year panel support**
   - Given a multi-year scenario run (10-year horizon)
   - When distributional analysis is invoked
   - Then indicators can be computed per-year or aggregated across years
   - And year-by-year decile trajectories are computable

5. **AC5: Export to CSV/Parquet**
   - Given computed distributional indicators
   - When export is requested
   - Then indicators are exportable to CSV/Parquet with correct schema
   - And the export includes decile labels (D1-D10) and metric names

## Tasks / Subtasks

- [ ] Task 1: Create indicator types and data structures (AC: 1, 3)
  - [ ] 1.1 Define `DecileIndicators` dataclass with decile-level aggregations
  - [ ] 1.2 Define `IndicatorResult` dataclass for structured output
  - [ ] 1.3 Define `DistributionalConfig` for analysis configuration options
  - [ ] 1.4 Add type definitions to `src/reformlab/indicators/types.py`

- [ ] Task 2: Implement income decile assignment (AC: 1, 2)
  - [ ] 2.1 Create `assign_deciles()` function that computes income decile (1-10) for each household
  - [ ] 2.2 Use weighted percentile calculation (weights optional, default to equal weights)
  - [ ] 2.3 Handle null/missing income values by exclusion with warning
  - [ ] 2.4 Add to `src/reformlab/indicators/deciles.py`

- [ ] Task 3: Implement decile aggregation functions (AC: 1, 3)
  - [ ] 3.1 Create `aggregate_by_decile()` function that groups panel data by decile
  - [ ] 3.2 Compute standard metrics: count, mean, median, sum, min, max per numeric field
  - [ ] 3.3 Use PyArrow compute functions for vectorized aggregation
  - [ ] 3.4 Return structured `DecileIndicators` with all metrics

- [ ] Task 4: Implement distributional indicator computation (AC: 1, 3, 4)
  - [ ] 4.1 Create `compute_distributional_indicators()` main entry point
  - [ ] 4.2 Accept PanelOutput from orchestrator as input
  - [ ] 4.3 Support single-year and multi-year modes
  - [ ] 4.4 Return `IndicatorResult` with decile breakdown and metadata

- [ ] Task 5: Implement multi-year support (AC: 4)
  - [ ] 5.1 Add `by_year=True` option to compute year-by-year decile indicators
  - [ ] 5.2 Add `aggregate_years=True` option to compute across all years
  - [ ] 5.3 Track decile trajectories over simulation horizon

- [ ] Task 6: Implement export functionality (AC: 5)
  - [ ] 6.1 Add `to_table()` method returning PyArrow Table
  - [ ] 6.2 Add `to_csv()` method for CSV export
  - [ ] 6.3 Add `to_parquet()` method for Parquet export with schema metadata

- [ ] Task 7: Write comprehensive tests
  - [ ] 7.1 Test decile assignment with various income distributions
  - [ ] 7.2 Test missing income handling and warning emission
  - [ ] 7.3 Test aggregation metrics accuracy
  - [ ] 7.4 Test multi-year indicator computation
  - [ ] 7.5 Test export round-trip (CSV/Parquet)

- [ ] Task 8: Update module exports and documentation
  - [ ] 8.1 Export public API from `src/reformlab/indicators/__init__.py`
  - [ ] 8.2 Add docstrings with examples to all public functions

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

The indicator layer sits above the orchestrator and consumes `PanelOutput` from `src/reformlab/orchestrator/panel.py`. This is a read-only consumer of orchestrator results.

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
Export to CSV/Parquet
```

### Technical Stack

- **PyArrow** for all data manipulation (consistent with existing codebase)
- Use `pyarrow.compute` functions for vectorized aggregation
- Follow existing patterns from `src/reformlab/orchestrator/panel.py` for table handling

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

### File Structure

```
src/reformlab/indicators/
├── __init__.py           # Public exports
├── types.py              # DecileIndicators, IndicatorResult, DistributionalConfig
├── deciles.py            # assign_deciles(), aggregate_by_decile()
└── distributional.py     # compute_distributional_indicators(), export functions
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
- [Source: _bmad-output/planning-artifacts/prd.md#NFR5] - NFR5: Analytical operations execute in under 5 seconds for 100k households
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-401] - Story acceptance criteria
- [Source: src/reformlab/orchestrator/panel.py] - PanelOutput class, input data structure
- [Source: src/reformlab/data/schemas.py] - SYNTHETIC_POPULATION_SCHEMA with income field

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

