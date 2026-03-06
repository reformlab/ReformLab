# Story 4.2: Implement Geographic Aggregation Indicators

Status: done

## Story

As a **policy analyst**,
I want **to compute indicators aggregated by geographic region from scenario run results**,
so that **I can analyze territorial disparities in environmental policy impacts and identify regional patterns of winners and losers**.

## Acceptance Criteria

From backlog (BKL-402), aligned with FR20 and NFR5.

Scope note: this story extends the indicator engine from Story 4-1 by adding geographic aggregation capabilities over `PanelOutput`. It reuses the existing `IndicatorResult` contract and `to_table()` pattern. This story focuses on region-based grouping; file export workflows remain downstream concerns (Story 4-5).

1. **AC-1: Region-based grouping for completed runs**
   - Given a completed scenario run with household-level results provided as `PanelOutput`
   - And the panel contains a `region_code` column
   - When `compute_geographic_indicators()` is invoked
   - Then households are grouped by region code
   - And aggregation metrics are returned for each numeric panel field per region

2. **AC-2: Unmatched region code handling**
   - Given a panel where some households have region codes not in the reference table (if provided)
   - When geographic aggregation runs
   - Then those households are grouped into an "unmatched" category
   - And the unmatched count is included in result metadata
   - And a warning is emitted with the exact unmatched count

3. **AC-3: Missing region code handling**
   - Given a panel where some households have null/missing region codes
   - When geographic aggregation runs
   - Then those households are excluded from regional grouping
   - And a warning is emitted with the exact excluded-household count
   - And excluded count is present in result metadata

4. **AC-4: Standard indicator metrics per region**
   - Given region-grouped households
   - When indicators are computed
   - Then metrics include `count`, `mean`, `median`, `sum`, `min`, and `max` per region
   - And metrics are computed for all numeric output fields in the panel

5. **AC-5: Multi-year support**
   - Given a multi-year panel with `year` and `region_code` columns
   - When analysis is requested with `by_year=True`
   - Then indicators are grouped by `(year, region_code)`
   - And when `aggregate_years=True`, indicators are grouped by `region_code` across all years

6. **AC-6: Stable tabular result contract**
   - Given computed geographic indicators
   - When `IndicatorResult.to_table()` is called
   - Then a PyArrow table is returned with stable columns for region, metric, field name, and value
   - And the table schema is compatible with Story 4-1's distributional indicators for downstream comparison

Deferred enhancement (not part of this story's acceptance criteria): region hierarchy rollups (for example, department → region) should be handled in a dedicated follow-up story to keep MVP scope focused.

## Tasks / Subtasks

- [ ] Task 0: Confirm prerequisites and input contracts (AC: dependency check)
  - [ ] 0.1 Verify Story 4-1 is `done` in `_bmad-output/implementation-artifacts/sprint-status.yaml`
  - [ ] 0.2 Confirm `PanelOutput` contract in `src/reformlab/orchestrator/panel.py` (`table`, `metadata`, `year`, `household_id`)
  - [ ] 0.3 Confirm `region_code` field name from `src/reformlab/data/schemas.py` (SYNTHETIC_POPULATION_SCHEMA shows `region_code` as `pa.utf8()`)
  - [ ] 0.4 Review Story 4-1 indicator types (`IndicatorResult`, `DistributionalConfig`) for extension patterns

- [ ] Task 1: Create geographic indicator types and configuration models (AC: #1, #4, #6)
  - [ ] 1.1 Define `RegionIndicators` dataclass for region-level metric payloads (parallel to `DecileIndicators`)
  - [ ] 1.2 Define `GeographicConfig` dataclass (`region_field`, `by_year`, `aggregate_years`, optional `reference_table`)
  - [ ] 1.3 Add definitions to `src/reformlab/indicators/types.py`
  - [ ] 1.4 Ensure `IndicatorResult` can hold both `DecileIndicators` and `RegionIndicators` (consider union type or base class)

- [ ] Task 2: Implement region grouping and unmatched handling (AC: #1, #2, #3)
  - [ ] 2.1 Create `group_by_region()` in `src/reformlab/indicators/geographic.py`
  - [ ] 2.2 Handle null/missing region codes: filter out with warning + excluded count
  - [ ] 2.3 Handle unmatched region codes (when reference table provided): group into "unmatched" category
  - [ ] 2.4 Return table with validated region assignments

- [ ] Task 3: Implement geographic aggregations (AC: #1, #4)
  - [ ] 3.1 Create `aggregate_by_region()` in `src/reformlab/indicators/geographic.py`
  - [ ] 3.2 Compute `count`, `mean`, `median`, `sum`, `min`, `max` for each numeric field per region
  - [ ] 3.3 Use vectorized PyArrow operations only (no row-wise Python loops on hot paths)
  - [ ] 3.4 Reuse patterns from `src/reformlab/indicators/deciles.py` where applicable

- [ ] Task 4: Implement main geographic computation API (AC: #1, #2, #3, #4, #5)
  - [ ] 4.1 Create `compute_geographic_indicators(panel: PanelOutput, config: GeographicConfig)` in `src/reformlab/indicators/geographic.py`
  - [ ] 4.2 Support single-year (default), `by_year=True`, and `aggregate_years=True` modes
  - [ ] 4.3 Return `IndicatorResult` containing stable metadata and warning details
  - [ ] 4.4 Include unmatched count and excluded count in metadata

- [ ] Task 5: Extend IndicatorResult for geographic indicators (AC: #6)
  - [ ] 5.1 Ensure `IndicatorResult.to_table()` produces consistent output for geographic indicators
  - [ ] 5.2 Output columns should be: field_name, region, year (optional), metric, value
  - [ ] 5.3 Verify schema compatibility with distributional indicators for Story 4-5 comparison

- [ ] Task 6: Add focused tests and quality gates (AC: all)
  - [ ] 6.1 Create `tests/indicators/test_geographic.py`
  - [ ] 6.2 Test region grouping across controlled region distributions
  - [ ] 6.3 Test missing region code exclusion + warning emission + metadata count
  - [ ] 6.4 Test unmatched region codes grouped into "unmatched" category
  - [ ] 6.5 Test metric correctness for numeric fields
  - [ ] 6.6 Test multi-year `by_year` and `aggregate_years` behavior
  - [ ] 6.7 Test `IndicatorResult.to_table()` schema stability for geographic results
  - [ ] 6.8 Run `ruff check src/reformlab/indicators tests/indicators`
  - [ ] 6.9 Run `mypy src/reformlab/indicators`
  - [ ] 6.10 Run `pytest tests/indicators/test_geographic.py -v`

- [ ] Task 7: Module exports and API surface (AC: #6)
  - [ ] 7.1 Export `compute_geographic_indicators`, `GeographicConfig`, `RegionIndicators` from `src/reformlab/indicators/__init__.py`
  - [ ] 7.2 Add concise docstrings for public geographic indicator functions/classes

## Dependencies

- **Required prior stories:**
  - Story 4-1 (BKL-401): Distributional indicators by income decile — provides `IndicatorResult`, `DistributionalConfig`, aggregation patterns
  - Story 3-7 (BKL-307): `PanelOutput` available as canonical household-year input
- **Current prerequisite status (from `_bmad-output/implementation-artifacts/sprint-status.yaml`):**
  - `4-1-implement-distributional-indicators`: `done`
  - `3-7-produce-scenario-year-panel-output`: `done`
- **Follow-on stories:**
  - Story 4-3 (BKL-403): Welfare indicators (depends on 4-1)
  - Story 4-4 (BKL-404): Fiscal indicators (depends on 4-1)
  - Story 4-5 (BKL-405): Scenario comparison/export tables across indicator families (depends on 4-2)

## Dev Notes

### Architecture Patterns

This story extends the Indicator Engine layer from Story 4-1:

```
┌─────────────────────────────────────────────────┐
│  Indicator Engine (distributional/welfare/fiscal)│  ← Story 4-2 adds geographic
├─────────────────────────────────────────────────┤
│  Governance (manifests, assumptions, lineage)    │
├─────────────────────────────────────────────────┤
│  Dynamic Orchestrator (year loop + step pipeline)│  ← Epic 3 complete
```

The geographic indicator component follows the same read-only consumer pattern as distributional indicators — it consumes `PanelOutput` without mutating orchestration state.

### Data Flow

```
OrchestratorResult
    ↓
PanelOutput.from_orchestrator_result()
    ↓
compute_geographic_indicators(panel: PanelOutput, config: GeographicConfig)
    ↓
IndicatorResult (with RegionIndicators per numeric field)
    ↓
IndicatorResult.to_table() for downstream export/comparison workflows
```

### Technical Stack

- **PyArrow** for all data manipulation (consistent with existing codebase)
- Use `pyarrow.compute` functions for vectorized aggregation
- Follow existing patterns from `src/reformlab/indicators/deciles.py` for aggregation logic
- Reuse `IndicatorResult` contract from `src/reformlab/indicators/types.py`

### Key Implementation Details

1. **Region Field:**
   - Default field name: `region_code` (from `SYNTHETIC_POPULATION_SCHEMA`)
   - Type: `pa.utf8()` (string-based region codes)
   - Common formats: French region codes (e.g., "11" for Île-de-France), INSEE department codes, or custom codes

2. **Missing Region Handling:**
   - Use `pyarrow.compute.is_null()` to identify missing values
   - Filter out nulls before region grouping
   - Emit warning via Python `warnings` module with count
   - Store exclusion count in result metadata

3. **Unmatched Region Handling:**
   - When a reference table is provided, check region codes against it
   - Unmatched codes are assigned to special category: `"_UNMATCHED"`
   - Include unmatched count in result metadata
   - Emit warning with unmatched count

4. **Aggregation Implementation:**
   - Use `pyarrow.compute.count()`, `mean()`, `sum()`, `min()`, `max()`
   - For median: use `approximate_median()` (same as deciles.py)
   - Group-by using PyArrow's `Table.group_by()` method
   - Follow pattern from `aggregate_by_decile()` in `deciles.py`

5. **Multi-Year Support:**
   - Panel already has `year` column from orchestrator
   - Group by (region, year) for year-by-year analysis
   - Aggregate across years by grouping by region only

6. **Result Schema Compatibility:**
   - Geographic indicators should produce table with same structure as distributional
   - Column names: `field_name`, `region` (instead of `decile`), `year`, `metric`, `value`
   - This enables Story 4-5 to compare across indicator types

7. **Hierarchy Rollups Are Deferred:**
   - Do not implement region hierarchy/level rollups in this story
   - Keep `GeographicConfig` scoped to base region grouping plus optional reference-table validation
   - Capture hierarchy rollups as a follow-up backlog item to protect Story 4-2 delivery size

### Code Patterns from Story 4-1 to Reuse

From `src/reformlab/indicators/deciles.py`:
- `assign_deciles()` pattern → adapt to `assign_regions()` or `validate_regions()`
- `aggregate_by_decile()` pattern → adapt to `aggregate_by_region()`
- `_empty_aggregation_table()` helper → extend for region schema

From `src/reformlab/indicators/types.py`:
- `DecileIndicators` dataclass structure → create parallel `RegionIndicators`
- `DistributionalConfig` pattern → create parallel `GeographicConfig`
- `IndicatorResult.to_table()` format → reuse/extend for region output

From `src/reformlab/indicators/distributional.py`:
- `compute_distributional_indicators()` structure → parallel `compute_geographic_indicators()`
- Warning capture pattern
- Metadata construction pattern

### Scope Guardrails

- **In scope:**
  - Region-based grouping and metric aggregation over `PanelOutput`
  - Single-year and multi-year (`by_year` / `aggregate_years`) indicator computation
  - Handling of missing and unmatched region codes
  - Stable in-memory indicator table contract (`to_table()`)
- **Out of scope:**
  - CSV/Parquet file export methods on indicator objects
  - Scenario side-by-side comparison tables across indicator families (Story 4-5)
  - Governance manifest persistence for indicator outputs (Epic 5)
  - Region hierarchy rollups (deferred to a dedicated follow-up story)

### File Structure

```
src/reformlab/indicators/
├── __init__.py           # Public exports (add geographic exports)
├── types.py              # DecileIndicators, RegionIndicators, IndicatorResult, configs
├── deciles.py            # assign_deciles(), aggregate_by_decile() [existing]
├── distributional.py     # compute_distributional_indicators() [existing]
└── geographic.py         # NEW: compute_geographic_indicators(), aggregate_by_region()
```

### Testing Standards

- Use pytest with fixtures from existing test patterns
- Create test fixtures in `tests/indicators/conftest.py` (or extend existing)
- Test with synthetic populations having known region distributions
- Test edge cases: empty panels, all-null regions, single region, all unmatched
- Test region codes that are strings with various formats (numeric strings, alpha codes)

### French Region Context (for realistic test data)

Common French region codes (INSEE):
- "11" = Île-de-France
- "24" = Centre-Val de Loire
- "27" = Bourgogne-Franche-Comté
- "28" = Normandie
- "32" = Hauts-de-France
- "44" = Grand Est
- "52" = Pays de la Loire
- "53" = Bretagne
- "75" = Nouvelle-Aquitaine
- "76" = Occitanie
- "84" = Auvergne-Rhône-Alpes
- "93" = Provence-Alpes-Côte d'Azur
- "94" = Corse

This context is useful for creating realistic test fixtures but not strictly required for implementation.

### Project Structure Notes

- Follows existing subsystem pattern in `indicators/`
- Uses PyArrow consistently with rest of codebase (not pandas)
- Follows existing docstring style with Args/Returns sections
- Uses `from __future__ import annotations` for type hints

### Performance Considerations

- Vectorized PyArrow operations (not row-by-row Python loops) per NFR2
- Target: 100k households analyzed in under 5 seconds per NFR5
- Memory efficient: work with PyArrow Tables, no full DataFrame copies
- Region grouping should be O(n) with hash-based grouping

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Subsystems] - Indicator layer definition
- [Source: _bmad-output/planning-artifacts/prd.md#FR20] - FR20: Analyst can compute indicators by geography (region and related groupings)
- [Source: _bmad-output/planning-artifacts/prd.md#FR33] - FR33: User can export tables and indicators in CSV/Parquet (downstream via table contract)
- [Source: _bmad-output/planning-artifacts/prd.md#NFR5] - NFR5: Analytical operations execute in under 5 seconds for 100k households
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-402] - Story acceptance criteria
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-401-BKL-405] - Epic-4 dependency chain
- [Source: src/reformlab/orchestrator/panel.py] - PanelOutput class, input data structure
- [Source: src/reformlab/data/schemas.py] - SYNTHETIC_POPULATION_SCHEMA with region_code field
- [Source: src/reformlab/indicators/deciles.py] - Pattern for assign_deciles(), aggregate_by_decile()
- [Source: src/reformlab/indicators/types.py] - DecileIndicators, IndicatorResult, DistributionalConfig patterns
- [Source: src/reformlab/indicators/distributional.py] - Pattern for compute_distributional_indicators()

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

None

### Completion Notes List

1. Successfully implemented all acceptance criteria (AC-1 through AC-6)
2. Extended IndicatorResult to support both DecileIndicators and RegionIndicators via union type
3. Implemented robust handling of missing and unmatched region codes with proper warnings
4. Added comprehensive test coverage (15 tests) covering all edge cases
5. All quality gates passed: ruff (linting), mypy (type checking), pytest (37/37 tests passing)
6. Code follows existing patterns from Story 4-1 (distributional indicators)
7. Uses PyArrow's vectorized operations for performance (no Python row loops)
8. Multi-year support implemented with by_year and aggregate_years modes
9. Stable table schema compatible with distributional indicators for Story 4-5 comparison

### File List

**Created:**
- src/reformlab/indicators/geographic.py (323 lines)
- tests/indicators/test_geographic.py (510 lines)

**Modified:**
- src/reformlab/indicators/types.py (extended with RegionIndicators, GeographicConfig)
- src/reformlab/indicators/__init__.py (updated exports)
- _bmad-output/implementation-artifacts/sprint-status.yaml (marked story as done)
