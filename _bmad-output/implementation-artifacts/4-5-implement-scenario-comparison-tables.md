# Story 4.5: Implement Scenario Comparison Tables

Status: ready-for-dev

## Story

As a **policy analyst**,
I want **to produce side-by-side comparison tables across baseline and reform scenario runs**,
so that **I can analyze indicator differences, export comparison outputs in machine-readable formats (CSV/Parquet), and make data-driven policy recommendations**.

## Acceptance Criteria

From backlog (BKL-405), aligned with FR24 and FR33.

Scope note: this story consumes `IndicatorResult` outputs from Stories 4-1 through 4-4 and produces unified comparison tables. It provides the final indicator-layer integration point before GUI visualization (EPIC-6) and governance manifest persistence (EPIC-5).

1. **AC-1: Side-by-side comparison table generation**
   - Given two or more completed scenario runs with computed indicators (any combination of distributional, geographic, welfare, or fiscal)
   - When `compare_scenarios()` is invoked with their `IndicatorResult` objects
   - Then a side-by-side comparison table is produced with columns: `field_name`, grouping dimension(s), `year`, `metric`, plus one value column per scenario (e.g., `baseline`, `reform_a`, `reform_b`)

2. **AC-2: Delta computation**
   - Given a comparison with a designated baseline scenario
   - When delta columns are enabled (`include_deltas=True`)
   - Then absolute delta columns (`delta_reform_a = reform_a - baseline`) are added for each non-baseline scenario
   - And percentage delta columns (`pct_delta_reform_a = delta / baseline * 100`) are added where baseline != 0

3. **AC-3: Cross-indicator-type comparison**
   - Given indicator results of different types (e.g., distributional + fiscal from the same scenario)
   - When comparison is requested for a single scenario with multiple indicator types
   - Then the comparison table vertically stacks all indicator metrics with an `indicator_type` column

4. **AC-4: CSV export**
   - Given a comparison table
   - When `export_csv()` is called with a file path
   - Then a valid CSV file is produced with headers matching the comparison table columns
   - And the file is readable by pandas/polars with correct types

5. **AC-5: Parquet export**
   - Given a comparison table
   - When `export_parquet()` is called with a file path
   - Then a valid Parquet file is produced with schema matching the comparison table
   - And the file is readable by pandas/polars with correct column types

6. **AC-6: Metadata preservation**
   - Given a comparison operation
   - When the comparison result is created
   - Then metadata from all source indicator results is preserved in a `comparison_metadata` dict
   - And scenario labels, indicator types, and field mappings are recorded for downstream governance

7. **AC-7: Empty and mismatched input handling**
   - Given indicator results with non-overlapping grouping dimensions or years
   - When comparison is attempted
   - Then rows with missing values in some scenarios use `null`/`None`
   - And a warning lists which scenarios are missing data for specific groups/years

8. **AC-8: Stable PyArrow table contract**
   - Given computed comparison results
   - When `ComparisonResult.to_table()` is called
   - Then a PyArrow table is returned with stable column schema
   - And the schema supports downstream chart rendering and export operations

## Tasks / Subtasks

- [ ] Task 0: Confirm prerequisites and input contracts (AC: dependency check)
  - [ ] 0.1 Verify Stories 4-1, 4-2, 4-3, 4-4 are `done` in `sprint-status.yaml`
  - [ ] 0.2 Confirm `IndicatorResult` contract and `to_table()` output schemas from `src/reformlab/indicators/types.py`
  - [ ] 0.3 Review existing indicator types' table schemas for join compatibility

- [ ] Task 1: Create comparison types and configuration models (AC: #1, #6, #8)
  - [ ] 1.1 Define `ComparisonConfig` dataclass in `src/reformlab/indicators/comparison.py`
  - [ ] 1.2 Define `ComparisonResult` dataclass with comparison table, metadata, warnings
  - [ ] 1.3 Define `ScenarioInput` dataclass to wrap `IndicatorResult` with scenario label

- [ ] Task 2: Implement side-by-side comparison core (AC: #1, #7)
  - [ ] 2.1 Create `src/reformlab/indicators/comparison.py` module
  - [ ] 2.2 Implement `_align_indicator_tables()` to join indicator tables on common dimensions
  - [ ] 2.3 Handle dimension alignment: (field_name, decile|region, year, metric) depending on indicator type
  - [ ] 2.4 Rename value columns by scenario label (e.g., `value` -> `baseline`, `value` -> `reform_a`)
  - [ ] 2.5 Handle mismatched dimensions with outer join and null fill

- [ ] Task 3: Implement delta computation (AC: #2)
  - [ ] 3.1 Implement `_compute_deltas()` internal function
  - [ ] 3.2 Compute absolute deltas: `delta_{scenario} = value_{scenario} - value_baseline`
  - [ ] 3.3 Compute percentage deltas: `pct_delta_{scenario} = delta / baseline * 100` (guard against div-by-zero)
  - [ ] 3.4 Add delta columns conditionally based on `include_deltas` config

- [ ] Task 4: Implement cross-indicator-type stacking (AC: #3)
  - [ ] 4.1 Implement `_stack_indicator_types()` for single-scenario multi-indicator comparison
  - [ ] 4.2 Add `indicator_type` column ("distributional", "geographic", "welfare", "fiscal")
  - [ ] 4.3 Normalize grouping columns: use `group_key` union column or preserve type-specific columns

- [ ] Task 5: Implement main comparison API (AC: #1-#8)
  - [ ] 5.1 Create `compare_scenarios(scenarios: list[ScenarioInput], config: ComparisonConfig)` main function
  - [ ] 5.2 Validate inputs: at least one scenario, consistent indicator types across scenarios
  - [ ] 5.3 Detect comparison mode: multi-scenario (same indicator type) vs single-scenario (multi-indicator)
  - [ ] 5.4 Designate baseline scenario via config (first by default) for delta computation
  - [ ] 5.5 Return `ComparisonResult` with table, metadata, and warnings

- [ ] Task 6: Implement CSV export (AC: #4)
  - [ ] 6.1 Add `export_csv(path: str | Path)` method to `ComparisonResult`
  - [ ] 6.2 Use PyArrow CSV writer with appropriate options (include header, UTF-8 encoding)
  - [ ] 6.3 Verify round-trip: exported file readable by pandas with correct dtypes

- [ ] Task 7: Implement Parquet export (AC: #5)
  - [ ] 7.1 Add `export_parquet(path: str | Path)` method to `ComparisonResult`
  - [ ] 7.2 Use PyArrow Parquet writer with schema preservation
  - [ ] 7.3 Verify round-trip: exported file readable by pandas/polars with correct column types

- [ ] Task 8: Handle edge cases (AC: #7)
  - [ ] 8.1 Handle empty indicator results gracefully (return empty comparison with warning)
  - [ ] 8.2 Handle mismatched years across scenarios (outer join with nulls)
  - [ ] 8.3 Handle mismatched grouping dimensions (outer join with nulls)
  - [ ] 8.4 Handle single scenario input (no comparison, just format for export)

- [ ] Task 9: Add focused tests and quality gates (AC: all)
  - [ ] 9.1 Create `tests/indicators/test_comparison.py`
  - [ ] 9.2 Test side-by-side comparison with 2 scenarios (distributional)
  - [ ] 9.3 Test side-by-side comparison with 3+ scenarios
  - [ ] 9.4 Test delta computation correctness (absolute and percentage)
  - [ ] 9.5 Test cross-indicator-type stacking (distributional + fiscal)
  - [ ] 9.6 Test mismatched dimension handling (outer join, null fill)
  - [ ] 9.7 Test CSV export and round-trip verification
  - [ ] 9.8 Test Parquet export and round-trip verification
  - [ ] 9.9 Test metadata preservation
  - [ ] 9.10 Run `ruff check src/reformlab/indicators tests/indicators`
  - [ ] 9.11 Run `mypy src/reformlab/indicators`
  - [ ] 9.12 Run `pytest tests/indicators/test_comparison.py -v`

- [ ] Task 10: Module exports and API surface (AC: #8)
  - [ ] 10.1 Export `compare_scenarios`, `ComparisonConfig`, `ComparisonResult`, `ScenarioInput` from `src/reformlab/indicators/__init__.py`
  - [ ] 10.2 Add concise docstrings for public comparison functions/classes

## Dependencies

- **Required prior stories:**
  - Story 4-1 (BKL-401): Distributional indicators — provides `IndicatorResult`, `DecileIndicators`
  - Story 4-2 (BKL-402): Geographic aggregation — provides `RegionIndicators`
  - Story 4-3 (BKL-403): Welfare indicators — provides `WelfareIndicators`
  - Story 4-4 (BKL-404): Fiscal indicators — provides `FiscalIndicators`

- **Current prerequisite status (from sprint-status.yaml):**
  - `4-1-implement-distributional-indicators`: `done`
  - `4-2-implement-geographic-aggregation-indicators`: `done`
  - `4-3-implement-welfare-indicators`: `done`
  - `4-4-implement-fiscal-indicators`: `done`

- **Follow-on stories:**
  - Story 4-6 (BKL-406): Custom derived indicator formulas (P1, depends on 4-5)
  - Story 6-1 (BKL-601): Stable Python API for run orchestration (will use comparison tables)
  - Story 6-4 (BKL-604): Early no-code GUI (comparison view uses these tables)

## Dev Notes

### Architecture Patterns

This story completes the Indicator Engine layer by adding the comparison capability:

```
+-------------------------------------------------+
|  Indicator Engine (distributional/welfare/fiscal)|
|  ├── compute_distributional_indicators()        |
|  ├── compute_geographic_indicators()            |
|  ├── compute_welfare_indicators()               |
|  ├── compute_fiscal_indicators()                |
|  └── compare_scenarios()  <- Story 4-5 adds     |
+-------------------------------------------------+
|  Governance (manifests, assumptions, lineage)    |
+-------------------------------------------------+
```

The comparison module consumes `IndicatorResult` objects from all four indicator types and produces unified comparison tables suitable for:
- GUI visualization (side-by-side charts, delta tables)
- Export to CSV/Parquet for external analysis
- Integration with governance manifests (EPIC-5)

### Data Flow

```
IndicatorResult (from 4-1, 4-2, 4-3, 4-4)
         |
         v
ScenarioInput (label + IndicatorResult)
         |
         v
compare_scenarios(scenarios: list[ScenarioInput], config: ComparisonConfig)
         |
         v
Detect comparison mode (multi-scenario vs multi-indicator)
         |
         v
Align indicator tables on common dimensions
         |
         v
[if include_deltas=True] Compute delta columns
         |
         v
ComparisonResult (with PyArrow table, metadata, warnings)
         |
         +---> export_csv(path)   -> CSV file
         +---> export_parquet(path) -> Parquet file
         +---> to_table() -> PyArrow Table for GUI
```

### Technical Stack

- **PyArrow** for all data manipulation (consistent with existing codebase)
- Use `pyarrow.Table.join()` for dimension alignment
- Use `pyarrow.csv.write_csv()` and `pyarrow.parquet.write_table()` for export
- Follow existing patterns from `src/reformlab/indicators/` modules

### Key Implementation Details

1. **ScenarioInput Dataclass:**
   ```python
   @dataclass
   class ScenarioInput:
       label: str  # e.g., "baseline", "reform_a", "reform_b"
       indicators: IndicatorResult
   ```

2. **ComparisonConfig Dataclass:**
   ```python
   @dataclass
   class ComparisonConfig:
       baseline_label: str | None = None  # First scenario if None
       include_deltas: bool = True
       include_pct_deltas: bool = True
   ```

3. **ComparisonResult Dataclass:**
   ```python
   @dataclass
   class ComparisonResult:
       table: pa.Table  # Side-by-side comparison table
       metadata: dict[str, Any]  # Scenario labels, indicator types, config
       warnings: list[str] = field(default_factory=list)

       def to_table(self) -> pa.Table:
           return self.table

       def export_csv(self, path: str | Path) -> None:
           ...

       def export_parquet(self, path: str | Path) -> None:
           ...
   ```

4. **Table Schema (multi-scenario comparison, distributional):**
   ```
   field_name: utf8
   decile: int64
   year: int64
   metric: utf8
   baseline: float64
   reform_a: float64
   reform_b: float64
   delta_reform_a: float64  # if include_deltas
   delta_reform_b: float64
   pct_delta_reform_a: float64  # if include_pct_deltas
   pct_delta_reform_b: float64
   ```

5. **Table Schema (multi-scenario comparison, geographic):**
   ```
   field_name: utf8
   region: utf8
   year: int64
   metric: utf8
   baseline: float64
   reform_a: float64
   ...
   ```

6. **Table Schema (multi-scenario comparison, fiscal):**
   ```
   field_name: utf8
   year: int64
   metric: utf8
   baseline: float64
   reform_a: float64
   ...
   ```

7. **Table Schema (single-scenario, multi-indicator stacking):**
   ```
   indicator_type: utf8  # "distributional", "geographic", "welfare", "fiscal"
   field_name: utf8
   group_key: utf8  # Unified grouping (decile as string, region code, or "aggregate")
   year: int64
   metric: utf8
   value: float64
   ```

### Dimension Alignment Strategy

The comparison must handle different indicator types with different grouping dimensions:

| Indicator Type | Grouping Columns |
|----------------|------------------|
| Distributional | field_name, decile, year, metric |
| Geographic | field_name, region, year, metric |
| Welfare (by decile) | field_name, decile, year, metric |
| Welfare (by region) | field_name, region, year, metric |
| Fiscal | field_name, year, metric |

**Multi-scenario comparison (same indicator type):**
- Direct join on all grouping columns
- Value column renamed per scenario label

**Single-scenario multi-indicator stacking:**
- Normalize decile/region to `group_key` string column
- Add `indicator_type` column
- Vertical concatenation (union)

### Delta Computation

1. **Absolute delta:**
   ```python
   delta = pc.subtract(reform_value, baseline_value)
   ```

2. **Percentage delta (with div-by-zero guard):**
   ```python
   # Guard: if baseline == 0, set pct_delta = null
   is_zero = pc.equal(baseline_value, 0.0)
   pct_delta = pc.if_else(
       is_zero,
       None,
       pc.multiply(pc.divide(delta, baseline_value), 100.0)
   )
   ```

### CSV Export Implementation

```python
def export_csv(self, path: str | Path) -> None:
    """Export comparison table to CSV file.

    Args:
        path: Destination file path.
    """
    import pyarrow.csv as csv
    csv.write_csv(self.table, path)
```

### Parquet Export Implementation

```python
def export_parquet(self, path: str | Path) -> None:
    """Export comparison table to Parquet file.

    Args:
        path: Destination file path.
    """
    import pyarrow.parquet as pq
    pq.write_table(self.table, path)
```

### Code Patterns from Previous Stories to Reuse

From `src/reformlab/indicators/types.py`:
- `IndicatorResult.to_table()` pattern for consistent table output
- Dataclass structure for config and result types

From `src/reformlab/indicators/welfare.py`:
- Multi-metric table construction
- Warning emission with counts
- Config-driven computation modes

From `src/reformlab/orchestrator/panel.py`:
- PyArrow table manipulation patterns
- Column renaming and schema transformation

### Scope Guardrails

- **In scope:**
  - Side-by-side comparison tables for 2+ scenarios
  - Delta (absolute and percentage) computation
  - Cross-indicator-type stacking for single scenario
  - CSV and Parquet export
  - Metadata preservation for governance
  - Stable PyArrow table contract

- **Out of scope:**
  - GUI visualization (EPIC-6)
  - Governance manifest persistence (EPIC-5)
  - Custom derived indicator formulas (Story 4-6)
  - Chart rendering (handled by frontend)
  - Weighted comparisons (Phase 2)
  - Scenario-level aggregate statistics (e.g., "overall reform impact score")

### File Structure

```
src/reformlab/indicators/
|-- __init__.py           # Public exports (add comparison exports)
|-- types.py              # Existing indicator types
|-- deciles.py            # [existing]
|-- distributional.py     # [existing]
|-- geographic.py         # [existing]
|-- welfare.py            # [existing]
|-- fiscal.py             # [existing]
+-- comparison.py         # NEW: compare_scenarios(), ComparisonResult, etc.
```

### Testing Standards

- Use pytest with fixtures following existing patterns in `tests/indicators/`
- Create test fixtures with known indicator values for predictable comparisons
- Test edge cases:
  - Two-scenario comparison (baseline vs single reform)
  - Three+ scenario comparison
  - Delta computation with zero baseline values
  - Mismatched years across scenarios
  - Mismatched grouping dimensions
  - Empty indicator results
  - Single scenario with multiple indicator types
  - CSV export and round-trip
  - Parquet export and round-trip

### Performance Considerations

- Vectorized PyArrow operations (not row-by-row Python loops) per NFR2
- Table joins use PyArrow native operations
- Export uses PyArrow native writers (no pandas intermediate)
- Memory efficient: avoid unnecessary table copies

### UX Context (from UX Design Specification)

Comparison tables feed directly into the GUI's comparison view:
- **Side-by-side mode:** Columns per scenario with indicator rows (uses comparison table directly)
- **Overlay mode:** All scenarios on same chart axes (uses comparison table for data)
- **Delta table mode:** Difference from baseline per indicator (uses delta columns)

The export functionality supports:
- Analyst workflows: export to CSV for Excel analysis
- Research workflows: export to Parquet for Python/R analysis
- Governance: metadata preservation for audit trails

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Subsystems] - Indicator layer definition
- [Source: _bmad-output/planning-artifacts/prd.md#FR24] - FR24: Analyst can compare indicators across scenarios side-by-side
- [Source: _bmad-output/planning-artifacts/prd.md#FR33] - FR33: User can export tables and indicators in CSV/Parquet
- [Source: _bmad-output/planning-artifacts/prd.md#NFR14] - NFR14: CSV and Parquet supported for all data input and output
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-405] - Story acceptance criteria
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#ComparisonView] - GUI comparison view specification
- [Source: src/reformlab/indicators/types.py] - IndicatorResult, DecileIndicators, RegionIndicators, WelfareIndicators, FiscalIndicators patterns
- [Source: src/reformlab/indicators/__init__.py] - Current indicator module exports
- [Source: _bmad-output/implementation-artifacts/4-4-implement-fiscal-indicators.md] - Previous story patterns

### Project Structure Notes

- New module `comparison.py` follows established pattern in `src/reformlab/indicators/`
- Export methods on result class follow existing `to_table()` pattern
- Imports added to `__init__.py` consistent with existing indicator exports

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
