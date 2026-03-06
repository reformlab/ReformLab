# Story 4.3: Implement Welfare Indicators

Status: done

## Story

As a **policy analyst**,
I want **to compute welfare indicators (winners/losers counts, net gains/losses) comparing baseline and reform scenario results**,
so that **I can assess the distributional welfare impact of environmental policies and communicate who benefits and who loses from proposed reforms**.

## Acceptance Criteria

From backlog (BKL-403), aligned with FR21 and NFR5.

Scope note: this story extends the indicator engine from Stories 4-1 and 4-2 by adding welfare comparison capabilities between baseline and reform `PanelOutput` results. It requires two scenario runs (baseline + reform) as inputs, computes household-level net changes, and produces winner/loser classifications with aggregated welfare metrics. The story reuses the existing `IndicatorResult` contract and `to_table()` pattern for downstream compatibility.

1. **AC-1: Winner/loser classification for household pairs**
   - Given baseline and reform scenario results as two `PanelOutput` objects
   - And both panels contain matching `household_id` values
   - When `compute_welfare_indicators()` is invoked
   - Then each household is classified as "winner", "loser", or "neutral" based on net change in the target welfare field
   - And classification uses configurable threshold (default: zero)

2. **AC-2: Net gain/loss computation**
   - Given baseline and reform scenario results
   - When welfare indicators are computed
   - Then net change (reform - baseline) is calculated for each household on the target welfare field
   - And aggregate metrics (`total_gain`, `total_loss`, `net_change`) are computed

3. **AC-3: Winner/loser counts by grouping**
   - Given welfare indicator results
   - When grouped by income decile
   - Then winner count, loser count, and neutral count are returned per decile
   - And when grouped by region (optional), counts are returned per region

4. **AC-4: Welfare metrics per group**
   - Given grouped welfare results
   - When indicators are computed
   - Then metrics include `winner_count`, `loser_count`, `neutral_count`, `mean_gain`, `mean_loss`, `median_change`, `total_gain`, `total_loss`, `net_change` per group
   - And `total_gain` is the sum of positive changes, `total_loss` is the absolute sum of negative changes, and `net_change = total_gain - total_loss`
   - And all matched households with non-null welfare values are included in aggregations

5. **AC-5: Missing household handling**
   - Given baseline and reform panels where some households exist in only one panel
   - When welfare computation runs
   - Then those households are excluded from comparison
   - And a warning is emitted with the exact unmatched-household count
   - And unmatched count is present in result metadata

6. **AC-6: Multi-year support**
   - Given multi-year baseline and reform panels
   - When analysis is requested with `by_year=True`
   - Then welfare indicators are computed per year with year-matched household comparisons
   - And when `by_year=False` and `aggregate_years=True`, indicators are computed across all years
   - And when `by_year=False` and `aggregate_years=False`, year-level detail is preserved

7. **AC-7: Scenario where all households are neutral**
   - Given baseline and reform scenarios with identical welfare field values for all households
   - When welfare indicators are computed
   - Then winner count and loser count are both zero
   - And neutral count equals total household count

8. **AC-8: Stable tabular result contract**
   - Given computed welfare indicators
   - When `IndicatorResult.to_table()` is called
   - Then a PyArrow table is returned with stable long-form columns compatible with existing indicator patterns
   - And schema uses `field_name` + group column (`decile` or `region`) + `year` + `metric` + `value` for downstream comparison (Story 4-5)

## Tasks / Subtasks

- [ ] Task 0: Confirm prerequisites and input contracts (AC: dependency check)
  - [ ] 0.1 Verify Stories 4-1 and 4-2 are `done` in `_bmad-output/implementation-artifacts/sprint-status.yaml`
  - [ ] 0.2 Confirm `PanelOutput` contract in `src/reformlab/orchestrator/panel.py` (`table`, `metadata`) and required join-key columns (`household_id`, `year`) in panel tables
  - [ ] 0.3 Review existing indicator types (`IndicatorResult`, `DecileIndicators`, `RegionIndicators`) for extension patterns
  - [ ] 0.4 Identify the welfare/income field to use for net change computation (likely `disposable_income` or similar)

- [ ] Task 1: Create welfare indicator types and configuration models (AC: #1, #4, #8)
  - [ ] 1.1 Define `WelfareIndicators` dataclass for group-level welfare metric payloads
  - [ ] 1.2 Define `WelfareConfig` dataclass (`welfare_field`, `threshold`, `by_year`, `aggregate_years`, `group_by_decile`, `group_by_region`)
  - [ ] 1.3 Add definitions to `src/reformlab/indicators/types.py`
  - [ ] 1.4 Ensure `IndicatorResult` can hold `WelfareIndicators` (extend union type)

- [ ] Task 2: Implement household-level comparison and classification (AC: #1, #2, #5)
  - [ ] 2.1 Create `compare_households()` in `src/reformlab/indicators/welfare.py`
  - [ ] 2.2 Join baseline and reform panels on `household_id` (and optionally `year`)
  - [ ] 2.3 Compute net change: `reform_value - baseline_value` for target welfare field
  - [ ] 2.4 Classify households: winner (change > threshold), loser (change < -threshold), neutral (else)
  - [ ] 2.5 Handle unmatched households: exclude with warning + unmatched count in metadata

- [ ] Task 3: Implement welfare aggregations by group (AC: #3, #4)
  - [ ] 3.1 Create `aggregate_welfare_by_decile()` in `src/reformlab/indicators/welfare.py`
  - [ ] 3.2 Create `aggregate_welfare_by_region()` in `src/reformlab/indicators/welfare.py` (optional grouping)
  - [ ] 3.3 Compute `winner_count`, `loser_count`, `neutral_count` per group
  - [ ] 3.4 Compute `mean_gain` (mean of positive changes), `mean_loss` (mean of negative changes)
  - [ ] 3.5 Compute `median_change`, `total_gain` (sum of positive changes), `total_loss` (absolute sum of negative changes), `net_change` (`total_gain - total_loss`) per group
  - [ ] 3.6 Use vectorized PyArrow operations only (no row-wise Python loops on hot paths)

- [ ] Task 4: Implement main welfare computation API (AC: #1-#7)
  - [ ] 4.1 Create `compute_welfare_indicators(baseline: PanelOutput, reform: PanelOutput, config: WelfareConfig)` in `src/reformlab/indicators/welfare.py`
  - [ ] 4.2 Support single-year (default), `by_year=True`, and `aggregate_years=True` modes
  - [ ] 4.3 Support grouping by decile (default) or region (optional alternate mode)
  - [ ] 4.4 Return `IndicatorResult` containing stable metadata and warning details
  - [ ] 4.5 Include unmatched count in metadata

- [ ] Task 5: Extend IndicatorResult for welfare indicators (AC: #8)
  - [ ] 5.1 Ensure `IndicatorResult.to_table()` produces consistent output for welfare indicators
  - [ ] 5.2 Output columns follow existing contracts: `field_name`, `decile|region`, `year`, `metric`, `value`
  - [ ] 5.3 Verify schema compatibility with distributional and geographic indicators for Story 4-5 comparison

- [ ] Task 6: Add focused tests and quality gates (AC: all)
  - [ ] 6.1 Create `tests/indicators/test_welfare.py`
  - [ ] 6.2 Test household-level net change computation correctness
  - [ ] 6.3 Test winner/loser/neutral classification with various thresholds
  - [ ] 6.4 Test unmatched household exclusion + warning emission + metadata count
  - [ ] 6.5 Test all-neutral scenario (AC-7): zero winners and losers
  - [ ] 6.6 Test welfare metrics correctness: mean_gain, mean_loss, total_gain, total_loss, net_change
  - [ ] 6.7 Test grouping by decile and by region (separate runs)
  - [ ] 6.8 Test multi-year `by_year` and `aggregate_years` behavior
  - [ ] 6.9 Test `IndicatorResult.to_table()` schema stability for welfare results
  - [ ] 6.10 Run `ruff check src/reformlab/indicators tests/indicators`
  - [ ] 6.11 Run `mypy src/reformlab/indicators`
  - [ ] 6.12 Run `pytest tests/indicators/test_welfare.py -v`

- [ ] Task 7: Module exports and API surface (AC: #8)
  - [ ] 7.1 Export `compute_welfare_indicators`, `WelfareConfig`, `WelfareIndicators` from `src/reformlab/indicators/__init__.py`
  - [ ] 7.2 Add concise docstrings for public welfare indicator functions/classes

## Dependencies

- **Required prior stories:**
  - Story 4-1 (BKL-401): Distributional indicators by income decile — provides `IndicatorResult`, `DecileIndicators`, `DistributionalConfig`, decile assignment logic
  - Story 4-2 (BKL-402): Geographic aggregation indicators — provides `RegionIndicators`, `GeographicConfig`, region grouping patterns
  - Story 3-7 (BKL-307): `PanelOutput` available as canonical household-year input and `compare_panels()` helper
- **Current prerequisite status (from `_bmad-output/implementation-artifacts/sprint-status.yaml`):**
  - `4-1-implement-distributional-indicators`: `done`
  - `4-2-implement-geographic-aggregation-indicators`: `done`
  - `3-7-produce-scenario-year-panel-output`: `done`
- **Follow-on stories:**
  - Story 4-4 (BKL-404): Fiscal indicators (depends on 4-1)
  - Story 4-5 (BKL-405): Scenario comparison/export tables across indicator families (depends on 4-2, 4-3, 4-4)

## Dev Notes

### Architecture Patterns

This story extends the Indicator Engine layer from Stories 4-1 and 4-2:

```
┌─────────────────────────────────────────────────┐
│  Indicator Engine (distributional/welfare/fiscal)│  ← Story 4-3 adds welfare
├─────────────────────────────────────────────────┤
│  Governance (manifests, assumptions, lineage)    │
├─────────────────────────────────────────────────┤
│  Dynamic Orchestrator (year loop + step pipeline)│  ← Epic 3 complete
```

The welfare indicator component differs from distributional and geographic indicators in that it requires **two** `PanelOutput` inputs (baseline and reform) for comparison. It remains a read-only consumer of orchestrator results.

### Data Flow

```
OrchestratorResult (baseline)          OrchestratorResult (reform)
         ↓                                       ↓
PanelOutput.from_orchestrator_result()  PanelOutput.from_orchestrator_result()
         ↓                                       ↓
         └───────────────┬───────────────────────┘
                         ↓
compute_welfare_indicators(baseline: PanelOutput, reform: PanelOutput, config: WelfareConfig)
                         ↓
              Household join on household_id
                         ↓
              Net change computation (reform - baseline)
                         ↓
              Winner/Loser/Neutral classification
                         ↓
              Group aggregation (by decile or region)
                         ↓
         IndicatorResult (with WelfareIndicators per group)
                         ↓
         IndicatorResult.to_table() for downstream export/comparison workflows
```

### Technical Stack

- **PyArrow** for all data manipulation (consistent with existing codebase)
- Use `pyarrow.compute` functions for vectorized aggregation
- Follow existing patterns from `src/reformlab/indicators/deciles.py` and `src/reformlab/indicators/geographic.py`
- Reuse `IndicatorResult` contract from `src/reformlab/indicators/types.py`

### Key Implementation Details

1. **Panel Joining Strategy:**
   - Join baseline and reform panels on `household_id` (inner join for matched households)
   - For multi-year panels, join on `(household_id, year)`
   - Reuse `compare_panels()` patterns from `src/reformlab/orchestrator/panel.py` where appropriate
   - Use PyArrow join operations: `pa.Table.join()` with join_type="inner"
   - Track unmatched households from both sides for warning

2. **Net Change Computation:**
   - After join, compute `change = reform_welfare_field - baseline_welfare_field`
   - Use `pyarrow.compute.subtract()` for vectorized subtraction
   - Handle potential null values in either panel gracefully

3. **Winner/Loser Classification:**
   - Default threshold: 0 (any positive change = winner, any negative = loser)
   - Configurable threshold for "neutral zone" (e.g., changes within ±1€ are neutral)
   - Classification formula:
     - Winner: `change > threshold`
     - Loser: `change < -threshold`
     - Neutral: `-threshold <= change <= threshold`

4. **Welfare Field Selection:**
   - Default field: `disposable_income` (or equivalent welfare measure in schema)
   - Configurable via `WelfareConfig.welfare_field`
   - Validate field exists in both panels before computation

5. **Group Aggregation:**
   - Reuse `assign_deciles()` from `deciles.py` for decile-based grouping
   - Reuse region grouping patterns from `geographic.py` for regional grouping
   - Use one grouping dimension per run (decile default, region optional)

6. **Welfare Metrics Per Group:**
   - `winner_count`: count where change > threshold
   - `loser_count`: count where change < -threshold
   - `neutral_count`: count where -threshold <= change <= threshold
   - `mean_gain`: mean of positive changes (winners only)
   - `mean_loss`: mean of negative changes (losers only)
   - `median_change`: median of all changes in group
   - `total_gain`: sum of positive changes
   - `total_loss`: absolute sum of negative changes
   - `net_change`: `total_gain - total_loss`

7. **Multi-Year Handling:**
   - Join on `(household_id, year)` for year-matched comparison
   - `by_year=True`: produce indicators per year
   - `by_year=False` and `aggregate_years=True`: aggregate across all years
   - `by_year=False` and `aggregate_years=False`: keep year detail

### Code Patterns from Previous Stories to Reuse

From `src/reformlab/indicators/deciles.py`:
- `assign_deciles()` — reuse for decile-based welfare grouping
- Aggregation helper patterns for PyArrow group-by operations

From `src/reformlab/indicators/geographic.py`:
- `assign_regions()` and `aggregate_by_region()` patterns — reuse for regional welfare grouping
- Warning capture and metadata construction patterns

From `src/reformlab/indicators/types.py`:
- `DecileIndicators` and `RegionIndicators` structure — create parallel `WelfareIndicators`
- `IndicatorResult.to_table()` — extend for welfare indicator output schema

From `src/reformlab/indicators/distributional.py`:
- `compute_distributional_indicators()` structure — parallel `compute_welfare_indicators()`
- Config pattern and metadata construction

### Scope Guardrails

- **In scope:**
  - Baseline vs reform panel comparison for welfare assessment
  - Winner/loser/neutral classification per household
  - Welfare metrics aggregated by decile or region
  - Single-year and multi-year (`by_year` / `aggregate_years`) indicator computation
  - Stable in-memory indicator table contract (`to_table()`)
- **Out of scope:**
  - Combined `(decile, region)` grouping in a single run (defer unless required by Story 4-5)
  - CSV/Parquet file export methods on indicator objects (Story 4-5)
  - Scenario side-by-side comparison tables across indicator families (Story 4-5)
  - Governance manifest persistence for indicator outputs (Epic 5)
  - Decomposition of welfare changes into components (e.g., tax vs transfer effects)

### File Structure

```
src/reformlab/indicators/
├── __init__.py           # Public exports (add welfare exports)
├── types.py              # DecileIndicators, RegionIndicators, WelfareIndicators, IndicatorResult, configs
├── deciles.py            # assign_deciles(), aggregate_by_decile() [existing]
├── distributional.py     # compute_distributional_indicators() [existing]
├── geographic.py         # compute_geographic_indicators() [existing]
└── welfare.py            # NEW: compute_welfare_indicators(), compare_households(), aggregate_welfare_*()
```

### Testing Standards

- Use pytest with fixtures from existing test patterns in `tests/indicators/`
- Create test fixtures with paired baseline/reform panels having known welfare differences
- Test with controlled populations where winner/loser counts are predictable
- Test edge cases:
  - Empty panels
  - All winners (reform strictly better for all)
  - All losers (reform strictly worse for all)
  - All neutral (identical panels, AC-7)
  - Mixed with varying thresholds
  - Unmatched households (present in only one panel)
  - Single household

### Performance Considerations

- Vectorized PyArrow operations (not row-by-row Python loops) per NFR2
- Target: 100k households analyzed in under 5 seconds per NFR5
- Memory efficient: join operations should not duplicate data unnecessarily
- Panel join is the critical path: use efficient PyArrow join implementation

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Subsystems] - Indicator layer definition
- [Source: _bmad-output/planning-artifacts/prd.md#FR21] - FR21: Analyst can compute welfare indicators including winners/losers counts and net gains/losses
- [Source: _bmad-output/planning-artifacts/prd.md#FR33] - FR33: User can export tables and indicators in CSV/Parquet (downstream via table contract)
- [Source: _bmad-output/planning-artifacts/prd.md#NFR5] - NFR5: Analytical operations execute in under 5 seconds for 100k households
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-403] - Story acceptance criteria
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-401-BKL-405] - Epic-4 dependency chain
- [Source: src/reformlab/orchestrator/panel.py] - PanelOutput class, input data structure
- [Source: src/reformlab/indicators/types.py] - IndicatorResult, DecileIndicators, RegionIndicators patterns
- [Source: src/reformlab/indicators/deciles.py] - assign_deciles(), aggregation patterns
- [Source: src/reformlab/indicators/geographic.py] - Region grouping and aggregation patterns
- [Source: src/reformlab/indicators/distributional.py] - compute_distributional_indicators() pattern
- [Source: _bmad-output/implementation-artifacts/4-1-implement-distributional-indicators.md] - Previous story learnings
- [Source: _bmad-output/implementation-artifacts/4-2-implement-geographic-aggregation-indicators.md] - Previous story learnings and patterns

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-5-20250929

### Debug Log References

N/A - no significant debugging required.

### Completion Notes List

- Implemented `WelfareIndicators` dataclass with all welfare metrics (winner/loser counts, mean_gain, mean_loss, median_change, total_gain, total_loss, net_change)
- Implemented `WelfareConfig` with configurable welfare field, threshold, grouping dimensions (decile/region), and multi-year options
- Created `compare_households()` to join baseline/reform panels and compute net changes
- Created `aggregate_welfare_by_decile()` and `aggregate_welfare_by_region()` for group-level welfare metrics
- Implemented `compute_welfare_indicators()` main API following existing indicator patterns
- Extended `IndicatorResult.to_table()` to support welfare indicators with stable schema (field_name, group_type, group_value, year, metric, value)
- All 16 tests pass, covering all acceptance criteria including winner/loser classification, unmatched household handling, all-neutral scenario (AC-7), welfare metrics correctness, multi-year support, and to_table() schema stability
- mypy type checking passes (only pre-existing error in unrelated file)
- Updated module exports in `__init__.py`
- Updated sprint status to mark story as done

### File List

- src/reformlab/indicators/types.py — added WelfareIndicators and WelfareConfig
- src/reformlab/indicators/welfare.py — NEW: all welfare computation logic
- src/reformlab/indicators/__init__.py — added welfare exports
- tests/indicators/test_welfare.py — NEW: comprehensive test coverage (16 tests)
