# Story 4.4: Implement Fiscal Indicators

Status: done

## Story

As a **policy analyst**,
I want **to compute fiscal indicators (annual revenue, cost, balance, and cumulative totals) from scenario results**,
so that **I can assess the budgetary implications of environmental policies over multi-year projections and compare fiscal trajectories across scenarios**.

## Acceptance Criteria

From backlog (BKL-404), aligned with FR22 and NFR5.

Scope note: this story extends the indicator engine primarily from Story 4-1 by adding fiscal metrics computed from a single `PanelOutput`. Unlike welfare indicators which compare two panels, fiscal indicators aggregate revenue/cost fields within a single scenario run. The story reuses the existing `IndicatorResult` contract and `to_table()` pattern for downstream compatibility with Story 4-5.

1. **AC-1: Annual fiscal metrics computation**
   - Given a `PanelOutput` containing revenue and cost fields (e.g., `carbon_tax_collected`, `subsidy_paid`)
   - When `compute_fiscal_indicators()` is invoked
   - Then annual totals are computed for each fiscal field: `revenue`, `cost`, `balance` (revenue - cost)
   - And results are returned per year for multi-year panels

2. **AC-2: Cumulative fiscal metrics**
   - Given fiscal indicators with annual values
   - When cumulative mode is enabled (`cumulative=True`)
   - Then cumulative totals from start_year through each year are computed
   - And `cumulative_revenue`, `cumulative_cost`, `cumulative_balance` are included

3. **AC-3: Configurable revenue/cost field mapping**
   - Given a `FiscalConfig` with `revenue_fields` and `cost_fields` lists
   - When fiscal indicators are computed
   - Then all specified fields are summed into `revenue` and `cost` respectively
   - And unmapped numeric fields are not included in fiscal calculations

4. **AC-4: Multi-year support**
   - Given a multi-year panel
   - When analysis is requested with `by_year=True`
   - Then fiscal indicators are computed per year
   - And when `by_year=False` and `aggregate_years=True`, indicators are summed across all years

5. **AC-5: Missing/null field handling**
   - Given a panel with missing values in fiscal fields
   - When fiscal computation runs
   - Then null values are treated as zero for aggregation
   - And a warning is emitted with count of null values per field

6. **AC-6: Empty panel handling**
   - Given an empty panel (no rows or no matching fiscal fields)
   - When fiscal indicators are computed
   - Then an empty `IndicatorResult` is returned with zero indicators
   - And a warning indicates no fiscal data was available

7. **AC-7: Stable tabular result contract**
   - Given computed fiscal indicators
   - When `IndicatorResult.to_table()` is called
   - Then a PyArrow table is returned with stable long-form columns: `field_name`, `year`, `metric`, `value`
   - And schema is compatible with existing indicator patterns for Story 4-5 comparison

## Tasks / Subtasks

- [ ] Task 0: Confirm prerequisites and input contracts (AC: dependency check)
  - [ ] 0.1 Verify Story 4-1 is `done` in `_bmad-output/implementation-artifacts/sprint-status.yaml`
  - [ ] 0.2 Confirm `PanelOutput` contract in `src/reformlab/orchestrator/panel.py`
  - [ ] 0.3 Review existing indicator types (`IndicatorResult`, `DecileIndicators`, `RegionIndicators`, `WelfareIndicators`) in `src/reformlab/indicators/types.py` for contract consistency
  - [ ] 0.4 Identify fiscal-relevant output fields from `ComputationResult` outputs via configurable mapping (no hardcoded field names)

- [ ] Task 1: Create fiscal indicator types and configuration models (AC: #1, #3, #7)
  - [ ] 1.1 Define `FiscalIndicators` dataclass for fiscal metric payloads in `src/reformlab/indicators/types.py`
  - [ ] 1.2 Define `FiscalConfig` dataclass with `revenue_fields`, `cost_fields`, `by_year`, `aggregate_years`, `cumulative`
  - [ ] 1.3 Ensure `IndicatorResult` can hold `FiscalIndicators` (extend union type in `indicators` field)
  - [ ] 1.4 Extend `IndicatorResult.to_table()` to support fiscal indicator output schema

- [ ] Task 2: Implement annual fiscal computation (AC: #1, #4, #5)
  - [ ] 2.1 Create `src/reformlab/indicators/fiscal.py` module
  - [ ] 2.2 Implement `_compute_annual_totals()` internal function
  - [ ] 2.3 Sum `revenue_fields` columns into `revenue` total per year
  - [ ] 2.4 Sum `cost_fields` columns into `cost` total per year
  - [ ] 2.5 Compute `balance = revenue - cost` per year
  - [ ] 2.6 Handle null values as zero with warning emission

- [ ] Task 3: Implement cumulative fiscal computation (AC: #2)
  - [ ] 3.1 Implement `_compute_cumulative_totals()` internal function
  - [ ] 3.2 Compute running cumulative sums from start year through each subsequent year
  - [ ] 3.3 Add `cumulative_revenue`, `cumulative_cost`, `cumulative_balance` metrics

- [ ] Task 4: Implement main fiscal computation API (AC: #1-#7)
  - [ ] 4.1 Create `compute_fiscal_indicators(panel: PanelOutput, config: FiscalConfig)` main function
  - [ ] 4.2 Validate config: ensure revenue_fields or cost_fields are provided
  - [ ] 4.3 Validate panel: ensure at least one configured fiscal field exists
  - [ ] 4.4 Support `by_year=True`, `by_year=False` with `aggregate_years=True`, and preserve annual detail when `by_year=False` and `aggregate_years=False`
  - [ ] 4.5 Include cumulative metrics when `config.cumulative=True` and year detail is present
  - [ ] 4.6 Return `IndicatorResult` with metadata and warnings

- [ ] Task 5: Handle edge cases (AC: #5, #6)
  - [ ] 5.1 Handle empty panels gracefully (return empty IndicatorResult with warning)
  - [ ] 5.2 Handle panels with no matching fiscal fields (return empty with warning)
  - [ ] 5.3 Handle null values in fiscal fields (treat as zero, emit warning with count)
  - [ ] 5.4 Handle single-year panels (cumulative values equal annual values when enabled)

- [ ] Task 6: Add focused tests and quality gates (AC: all)
  - [ ] 6.1 Create `tests/indicators/test_fiscal.py`
  - [ ] 6.2 Test annual fiscal computation correctness
  - [ ] 6.3 Test cumulative computation correctness
  - [ ] 6.4 Test configurable field mapping
  - [ ] 6.5 Test null value handling with warning
  - [ ] 6.6 Test empty panel handling (AC-6)
  - [ ] 6.7 Test single-year vs multi-year behavior
  - [ ] 6.8 Test `IndicatorResult.to_table()` schema for fiscal indicators
  - [ ] 6.9 Run `ruff check src/reformlab/indicators tests/indicators`
  - [ ] 6.10 Run `mypy src/reformlab/indicators`
  - [ ] 6.11 Run `pytest tests/indicators/test_fiscal.py -v`

- [ ] Task 7: Module exports and API surface (AC: #7)
  - [ ] 7.1 Export `compute_fiscal_indicators`, `FiscalConfig`, `FiscalIndicators` from `src/reformlab/indicators/__init__.py`
  - [ ] 7.2 Add concise docstrings for public fiscal indicator functions/classes

## Dependencies

- **Required prior stories:**
  - Story 4-1 (BKL-401): Distributional indicators — provides `IndicatorResult`, `DecileIndicators`, base patterns
  - Story 3-7 (BKL-307): `PanelOutput` as canonical input

- **Current prerequisite status (from `_bmad-output/implementation-artifacts/sprint-status.yaml`):**
  - `4-1-implement-distributional-indicators`: `done`
  - `3-7-produce-scenario-year-panel-output`: `done`

- **Helpful prior implementations (not hard dependencies):**
  - Story 4-2 (BKL-402): Geographic aggregation — warning and aggregation patterns
  - Story 4-3 (BKL-403): Welfare indicators — multi-metric table shaping patterns

- **Follow-on stories:**
  - Story 4-5 (BKL-405): Scenario comparison tables across indicator families (depends on 4-2, 4-3, 4-4)
  - Story 4-6 (BKL-406): Custom derived indicator formulas (P1, depends on 4-5)

## Dev Notes

### Architecture Patterns

This story extends the Indicator Engine layer:

```
+-------------------------------------------------+
|  Indicator Engine (distributional/welfare/fiscal)|  <- Story 4-4 adds fiscal
+-------------------------------------------------+
|  Governance (manifests, assumptions, lineage)    |
+-------------------------------------------------+
|  Dynamic Orchestrator (year loop + step pipeline)|  <- Epic 3 complete
+-------------------------------------------------+
```

Unlike welfare indicators (which compare two panels), fiscal indicators operate on a **single** `PanelOutput` and aggregate revenue/cost fields into budgetary metrics.

### Data Flow

```
OrchestratorResult
         |
         v
PanelOutput.from_orchestrator_result()
         |
         v
compute_fiscal_indicators(panel: PanelOutput, config: FiscalConfig)
         |
         v
Validate fiscal fields exist in panel
         |
         v
Compute annual totals (revenue, cost, balance) per year
         |
         v
[if cumulative=True] Compute cumulative totals
         |
         v
IndicatorResult (with FiscalIndicators per year)
         |
         v
IndicatorResult.to_table() for downstream export/comparison
```

### Technical Stack

- **PyArrow** for all data manipulation (consistent with existing codebase)
- Use `pyarrow.compute` functions for vectorized aggregation
- Follow existing patterns from `src/reformlab/indicators/distributional.py`, `geographic.py`, `welfare.py`
- Reuse `IndicatorResult` contract from `src/reformlab/indicators/types.py`

### Key Implementation Details

1. **FiscalIndicators Dataclass:**
   ```python
   @dataclass
   class FiscalIndicators:
       field_name: str  # stable label, e.g. "fiscal_summary"
       year: int | None
       revenue: float
       cost: float
       balance: float
       cumulative_revenue: float | None = None
       cumulative_cost: float | None = None
       cumulative_balance: float | None = None
   ```

2. **FiscalConfig Dataclass:**
   ```python
   @dataclass
   class FiscalConfig:
       revenue_fields: list[str] = field(default_factory=list)  # e.g., ["carbon_tax_collected"]
       cost_fields: list[str] = field(default_factory=list)     # e.g., ["subsidy_paid", "rebate_paid"]
       by_year: bool = True
       aggregate_years: bool = False  # Only used when by_year=False
       cumulative: bool = True        # Compute cumulative totals
   ```

3. **Annual Aggregation:**
   - Group panel by `year` column
   - For each year, sum all `revenue_fields` columns into `revenue`
   - Sum all `cost_fields` columns into `cost`
   - Compute `balance = revenue - cost`
   - Use `pyarrow.compute.sum()` for vectorized sums

4. **Cumulative Computation:**
   - After computing annual values, iterate through years in sorted order
   - Maintain running totals: `cumulative_revenue += revenue[year]`
   - Store cumulative values alongside annual values

5. **Null Value Handling:**
   - Use `pyarrow.compute.fill_null(column, 0.0)` before aggregation
   - Count null values per field with `pyarrow.compute.count(is_null=True)`
   - Emit warning with null counts per field

6. **Multi-Year Modes:**
   - `by_year=True`: One `FiscalIndicators` per year
   - `by_year=False, aggregate_years=True`: Single `FiscalIndicators` summed across all years
   - `by_year=False, aggregate_years=False`: Preserve annual detail for parity with existing indicator APIs
   - Cumulative metrics only apply when year detail is present

### Code Patterns from Previous Stories to Reuse

From `src/reformlab/indicators/distributional.py`:
- Warning capture pattern with `warnings.catch_warnings(record=True)`
- Metadata construction with panel info
- Numeric field iteration pattern

From `src/reformlab/indicators/types.py`:
- `IndicatorResult` container structure
- `to_table()` long-form conversion pattern with field_name, year, metric, value columns

From `src/reformlab/indicators/welfare.py`:
- Multi-field aggregation patterns
- Config-driven computation modes
- Warning emission with counts

### Scope Guardrails

- **In scope:**
  - Single-panel fiscal aggregation (revenue, cost, balance)
  - Annual and cumulative metrics
  - Configurable field mapping
  - Stable in-memory indicator table contract (`to_table()`)

- **Out of scope:**
  - Baseline vs reform fiscal comparison (use Story 4-5 comparison tables)
  - Fiscal breakdown by income decile (combine with Story 4-1 distributional if needed)
  - Fiscal breakdown by region (combine with Story 4-2 geographic if needed)
  - Per-household fiscal statistics (defer to follow-up story if needed)
  - CSV/Parquet file export methods on indicator objects (Story 4-5)
  - Governance manifest persistence for indicator outputs (Epic 5)
  - Net present value (NPV) or discounting calculations (Phase 2)

### File Structure

```
src/reformlab/indicators/
|-- __init__.py           # Public exports (add fiscal exports)
|-- types.py              # Add FiscalIndicators, FiscalConfig
|-- deciles.py            # [existing]
|-- distributional.py     # [existing]
|-- geographic.py         # [existing]
|-- welfare.py            # [existing]
+-- fiscal.py             # NEW: compute_fiscal_indicators()
```

### Testing Standards

- Use pytest with fixtures following existing patterns in `tests/indicators/`
- Create test fixtures with known revenue/cost values for predictable results
- Test with controlled multi-year data where fiscal totals are verifiable
- Test edge cases:
  - Empty panels
  - Single-year panels
  - Multi-year panels with gaps
  - Panels with only revenue fields (no cost)
  - Panels with only cost fields (no revenue)
  - Panels with null values in fiscal fields
  - Large populations (verify performance)

### Performance Considerations

- Vectorized PyArrow operations (not row-by-row Python loops) per NFR2
- Target: 100k households analyzed in under 5 seconds per NFR5
- Memory efficient: avoid creating intermediate DataFrames
- Use `pyarrow.compute` for all aggregations

### UX Context (from UX Design Specification)

Fiscal indicators feed into the GUI's comparison view:
- Side-by-side scenario comparison shows fiscal balance trajectories
- Annual and cumulative charts visualize budgetary implications

The `to_table()` output format enables:
- Chart rendering via Recharts/Nivo
- Export to CSV/Parquet for reporting
- Comparison tables in Story 4-5

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Subsystems] - Indicator layer definition
- [Source: _bmad-output/planning-artifacts/prd.md#FR22] - FR22: Analyst can compute fiscal indicators (revenues, costs, balances) per year and cumulatively
- [Source: _bmad-output/planning-artifacts/prd.md#FR33] - FR33: User can export tables and indicators in CSV/Parquet
- [Source: _bmad-output/planning-artifacts/prd.md#NFR5] - NFR5: Analytical operations execute in under 5 seconds for 100k households
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-404] - Story acceptance criteria
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-401-BKL-405] - Epic-4 dependency chain
- [Source: src/reformlab/orchestrator/panel.py] - PanelOutput class, input data structure
- [Source: src/reformlab/indicators/types.py] - IndicatorResult, DecileIndicators, RegionIndicators, WelfareIndicators patterns
- [Source: src/reformlab/indicators/distributional.py] - compute_distributional_indicators() pattern
- [Source: src/reformlab/indicators/geographic.py] - Region aggregation and warning patterns
- [Source: src/reformlab/indicators/welfare.py] - Multi-field aggregation and config patterns
- [Source: _bmad-output/implementation-artifacts/4-3-implement-welfare-indicators.md] - Previous story learnings

## Dev Agent Record

### Agent Model Used

Unknown (record not captured during implementation)

### Debug Log References

- Dev Agent Record backfilled during Phase 1 retro cleanup. Original debug logs were not recorded.

### Completion Notes List

- Dev Agent Record backfilled during Phase 1 retro cleanup. Original implementation agent and debug details were not recorded.

### File List

- `src/reformlab/indicators/__init__.py` (modified) — indicators package exports updated
- `src/reformlab/indicators/fiscal.py` (new) — fiscal indicator calculations
- `src/reformlab/indicators/types.py` (modified) — type definitions extended for fiscal indicators
- `tests/indicators/test_fiscal.py` (new) — fiscal indicator tests
