# Story 6.5: Add Export Actions for CSV/Parquet Outputs

Status: ready-for-dev

## Story

As a **policy analyst (Sophie) or researcher (Marco)**,
I want **to export simulation results, indicators, and comparison tables to CSV and Parquet from the Python API**,
so that **I can share outputs, use them in external tools, and keep runs reproducible (with GUI wiring added in Story 6-4b)**.

## Acceptance Criteria

From backlog (BKL-605), aligned with FR33 (export tables and indicators in CSV/Parquet).

1. **AC-1: API export for simulation results**
   - Given a completed `SimulationResult`, when `result.export_csv(path)` or `result.export_parquet(path)` is called, then panel output is written to the specified path.
   - Export methods return `Path` to the written file.
   - If `panel_output` is unavailable, methods raise a clear `SimulationError`.

2. **AC-2: API export for indicator results**
   - Given an `IndicatorResult`, when `export_csv(path)` or `export_parquet(path)` is called, then `IndicatorResult.to_table()` content is exported.
   - Distributional, geographic, welfare, and fiscal indicator outputs are all exportable.
   - Export methods return `Path` to the written file.

3. **AC-3: Comparison export reliability**
   - Given a `ComparisonResult` from `compare_scenarios(...)`, when `export_csv(path)` or `export_parquet(path)` is called, then exported files contain expected scenario and delta columns.
   - Existing behavior remains backward compatible unless an explicit API change is approved.

4. **AC-4: Manifest traceability in exported artifacts**
   - Given a simulation Parquet export, schema metadata includes run provenance keys (`manifest_id`, engine/version context).
   - Given a CSV export, provenance remains available through run manifest records (`result.manifest`) and documented usage.

5. **AC-5: Notebook verification**
   - Quickstart and advanced notebooks include export examples (CSV and Parquet).
   - Exported files round-trip through PyArrow/polars with expected schema/types.

6. **AC-6: Scope boundary for GUI**
   - No GUI button/preview wiring is implemented in this story.
   - GUI download actions are deferred to Story 6-4b, which consumes these export APIs.

## Dependencies

Dependency gate: if any hard dependency below is not `done`, set this story to `blocked`.

- **Hard dependency: Story 6-1 (BKL-601) — DONE**
  - Provides `SimulationResult` and stable Python API surface.

- **Hard dependency: Story 3-7 (BKL-307) — DONE**
  - Provides `PanelOutput.to_csv()` and `PanelOutput.to_parquet()`.

- **Hard dependency: Story 4-5 (BKL-405) — DONE**
  - Provides `ComparisonResult` and existing comparison export methods.

- **Hard dependency: Story 5-1 (BKL-501) — DONE**
  - Provides run manifest schema required for provenance metadata.

- **Follow-on dependency: Story 6-4b (BKL-604b) — BACKLOG**
  - Consumes this story to wire GUI export actions/download flow.
  - Not a blocker for Python API export implementation.

- **Follow-on dependency: Story 6-6 (BKL-606) — BACKLOG**
  - May refine user-facing export error messaging in GUI/API wrappers.

## Tasks / Subtasks

- [ ] Task 0: Validate dependencies and baseline behavior (AC: #1-#3, dependency gate)
  - [ ] 0.1 Confirm stories 6-1, 3-7, 4-5, and 5-1 are `done` in `sprint-status.yaml`
  - [ ] 0.2 Review current export paths in `PanelOutput` and `ComparisonResult`
  - [ ] 0.3 Confirm no FastAPI route layer is required in this story (deferred to 6-4b)

- [ ] Task 1: Add `SimulationResult` export methods (AC: #1, #4)
  - [ ] 1.1 Implement `SimulationResult.export_csv(path: str | Path) -> Path` in `src/reformlab/interfaces/api.py`
  - [ ] 1.2 Implement `SimulationResult.export_parquet(path: str | Path) -> Path`
  - [ ] 1.3 Delegate export writes through `PanelOutput.to_csv()` / `PanelOutput.to_parquet()` (facade pattern)
  - [ ] 1.4 Add/propagate manifest provenance metadata for Parquet exports
  - [ ] 1.5 Raise clear `SimulationError` when `panel_output` is `None`
  - [ ] 1.6 Add/extend tests in `tests/interfaces/test_api.py`

- [ ] Task 2: Add `IndicatorResult` export methods (AC: #2)
  - [ ] 2.1 Implement `IndicatorResult.export_csv(path: str | Path) -> Path` in `src/reformlab/indicators/types.py`
  - [ ] 2.2 Implement `IndicatorResult.export_parquet(path: str | Path) -> Path`
  - [ ] 2.3 Use PyArrow writers on `IndicatorResult.to_table()`
  - [ ] 2.4 Add tests covering distributional, geographic, welfare, and fiscal indicators in `tests/indicators/`

- [ ] Task 3: Verify/extend `ComparisonResult` export behavior (AC: #3)
  - [ ] 3.1 Add export verification tests in `tests/indicators/test_comparison.py`
  - [ ] 3.2 Assert scenario value columns and delta columns are present as configured
  - [ ] 3.3 Keep API behavior backward compatible (or document intentional change)

- [ ] Task 4: Add notebook export examples (AC: #5)
  - [ ] 4.1 Update `notebooks/quickstart.ipynb` with CSV export example
  - [ ] 4.2 Update `notebooks/advanced.ipynb` with Parquet export example
  - [ ] 4.3 Add round-trip checks using PyArrow/polars in notebook test flow (`tests/notebooks/`)

- [ ] Task 5: Final validation (AC: #1-#6)
  - [ ] 5.1 Run focused tests for interfaces/indicators/notebooks export paths
  - [ ] 5.2 Validate CSV/Parquet files are readable with expected schema
  - [ ] 5.3 Validate Parquet metadata includes provenance keys
  - [ ] 5.4 Confirm no GUI component changes are included in this story

## Dev Notes

### Architecture Compliance

This story implements FR33 within the architecture's layered model:

- **Interfaces layer first**: Export capability is added on Python API objects (`SimulationResult`, `IndicatorResult`) and consumed later by GUI/API transport layers.
- **PyArrow-first contracts**: CSV/Parquet export uses PyArrow writers, aligned with architecture data contracts.
- **Facade delegation**: `SimulationResult` delegates data writes to `PanelOutput` rather than duplicating export logic.
- **Governance traceability**: Exports preserve run provenance through manifest-aware metadata and documented manifest linkage.
- **Scope alignment with deployment architecture**: FastAPI transport endpoints and GUI download buttons are intentionally deferred to Story 6-4b.

### Existing Export Infrastructure

Already implemented:

```python
# PanelOutput (orchestrator/panel.py)
class PanelOutput:
    def to_csv(self, path: str | Path) -> Path: ...
    def to_parquet(self, path: str | Path) -> Path: ...

# ComparisonResult (indicators/comparison.py)
class ComparisonResult:
    def export_csv(self, path: str | Path) -> None: ...
    def export_parquet(self, path: str | Path) -> None: ...
```

Needs implementation in this story:

```python
# SimulationResult (interfaces/api.py)
class SimulationResult:
    def export_csv(self, path: str | Path) -> Path: ...
    def export_parquet(self, path: str | Path) -> Path: ...

# IndicatorResult (indicators/types.py)
class IndicatorResult:
    def export_csv(self, path: str | Path) -> Path: ...
    def export_parquet(self, path: str | Path) -> Path: ...
```

### Scope Guardrails

In scope:

- Python API export methods for `SimulationResult` and `IndicatorResult`
- Export verification for `ComparisonResult`
- Provenance metadata for simulation Parquet exports
- Notebook export examples and associated tests

Out of scope (deferred):

- GUI export preview/download UI behavior (Story 6-4b)
- FastAPI route/controller layer for file downloads (Story 6-4b)
- Additional formats (Excel/XLSX), bulk export orchestration, streaming exports

### File Locations

```text
src/reformlab/
├── interfaces/
│   └── api.py                    ← Add SimulationResult.export_* methods
├── indicators/
│   ├── types.py                  ← Add IndicatorResult.export_* methods
│   └── comparison.py             ← Verify existing export behavior
├── orchestrator/
│   └── panel.py                  ← Reused by SimulationResult exports
└── governance/
    └── manifest.py               ← Provenance context source

notebooks/
├── quickstart.ipynb              ← Add CSV export example
└── advanced.ipynb                ← Add Parquet export example

tests/
├── interfaces/test_api.py        ← Add SimulationResult export tests
├── indicators/test_comparison.py ← Extend comparison export tests
├── indicators/                   ← Add indicator export coverage
└── notebooks/                    ← Extend notebook checks
```

### References

- [Source: prd.md#Functional-Requirements] — FR33 export tables and indicators
- [Source: architecture.md#Data Contracts] — CSV/Parquet interoperability contract
- [Source: architecture.md#Layered Architecture] — interfaces/indicators/governance layering
- [Source: architecture.md#Deployment & GUI Architecture (2026-02-27)] — FastAPI + GUI integration path
- [Source: sprint-status.yaml] — dependency statuses for stories 6-1, 3-7, 4-5, 5-1, 6-4b

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
