# Story 6.5: Add Export Actions for CSV/Parquet Outputs

Status: ready-for-dev

## Story

As a **policy analyst (Sophie) or researcher (Marco)**,
I want **to export simulation results, indicators, and comparison tables to CSV and Parquet formats from both the Python API and the GUI**,
so that **I can share outputs with colleagues, load them into other analytical tools, and archive results for reproducibility**.

## Acceptance Criteria

From backlog (BKL-605), aligned with FR33 (export tables and indicators in CSV/Parquet).

1. **AC-1: API export for simulation results**
   - Given a completed `SimulationResult`, when `result.export_csv(path)` or `result.export_parquet(path)` is called, then the panel output is written to the specified file path.
   - The exported file includes all household-by-year panel data with correct column headers and types.
   - Export methods return the `Path` to the written file for confirmation.

2. **AC-2: API export for indicator results**
   - Given a computed `IndicatorResult` from `result.indicators(...)`, when `indicators.export_csv(path)` or `indicators.export_parquet(path)` is called, then the indicator data is written to the specified file path.
   - All indicator types (distributional, geographic, welfare, fiscal) support export.
   - Export includes appropriate metadata fields (field_name, grouping dimensions, year, metric, value).

3. **AC-3: API export for comparison results**
   - Given a `ComparisonResult` from `compare_scenarios(...)`, when `comparison.export_csv(path)` or `comparison.export_parquet(path)` is called, then the comparison table is written to the specified file path.
   - Export includes side-by-side scenario columns and computed delta columns.
   - Export methods already exist on `ComparisonResult` — verify they work correctly with current schema.

4. **AC-4: GUI export actions**
   - Given the wired GUI (Story 6-4b), when an analyst clicks an export action on results, indicators, or comparison views, then a file download is triggered.
   - Export format selection (CSV/Parquet) is available before download.
   - Export preview shows column summary and row count before confirming.

5. **AC-5: Manifest metadata in exports**
   - Given an export from simulation results, when the Parquet file is inspected, then schema metadata includes the run manifest ID and engine version.
   - CSV exports include a metadata comment header with manifest reference.

6. **AC-6: Export verification in notebooks**
   - Given the quickstart or advanced notebook, when export examples are added, then users can see how to export results to CSV/Parquet.
   - Export round-trips correctly: exported files can be re-read with pandas/polars with correct types.

## Dependencies

Dependency gate: if any hard dependency below is not `done`, set this story to `blocked` and do not start implementation.

- **Hard dependency (backlog-declared): Story 6-1 (BKL-601) — DONE**
  - Provides `SimulationResult`, `run_scenario()`, indicator access API
  - Export methods will be added to `SimulationResult`

- **Hard dependency (backlog-declared): Story 4-5 (BKL-405) — DONE**
  - Provides `ComparisonResult` with existing `export_csv()` and `export_parquet()` methods
  - This story verifies and extends those methods if needed

- **Hard dependency (backlog-declared): Story 6-4b (BKL-604b) — BACKLOG**
  - Provides wired GUI with backend integration
  - AC-4 (GUI export) requires 6-4b to be completed first
  - **Note:** Backend export endpoints can be implemented before 6-4b; GUI wiring is deferred

- **Supporting completed stories:**
  - Story 3-7 (BKL-307): Panel output with `to_csv()` and `to_parquet()` methods — DONE
  - Story 4-1 to 4-4: Indicator types (distributional, geographic, welfare, fiscal) — DONE
  - Story 5-1 (BKL-501): Run manifest schema — DONE

- **Follow-on stories:**
  - Story 6-6 (BKL-606): Improve operational error UX (may affect export error messages)

## Tasks / Subtasks

- [ ] Task 0: Confirm blockers and review existing export code (AC: dependency check)
  - [ ] 0.1 Confirm Stories 6-1, 4-5, 3-7 are `done` in `sprint-status.yaml`
  - [ ] 0.2 Review existing export methods: `PanelOutput.to_csv()`, `PanelOutput.to_parquet()`, `ComparisonResult.export_csv()`, `ComparisonResult.export_parquet()`
  - [ ] 0.3 Review `IndicatorResult` class for export method gaps
  - [ ] 0.4 Document API surface for export actions

- [ ] Task 1: Add export methods to SimulationResult (AC: #1, #5)
  - [ ] 1.1 Add `export_csv(path: str | Path) -> Path` to `SimulationResult` in `interfaces/api.py`
  - [ ] 1.2 Add `export_parquet(path: str | Path) -> Path` to `SimulationResult`
  - [ ] 1.3 Delegate to `PanelOutput.to_csv()` and `PanelOutput.to_parquet()` internally
  - [ ] 1.4 Ensure Parquet schema metadata includes manifest_id and engine_version
  - [ ] 1.5 Add unit tests for export methods
  - [ ] 1.6 Handle edge case: export when `panel_output` is None (failed run) with clear error

- [ ] Task 2: Add export methods to IndicatorResult (AC: #2)
  - [ ] 2.1 Add `export_csv(path: str | Path) -> Path` to `IndicatorResult` in `indicators/types.py`
  - [ ] 2.2 Add `export_parquet(path: str | Path) -> Path` to `IndicatorResult`
  - [ ] 2.3 Use PyArrow CSV/Parquet writers on `IndicatorResult.to_table()`
  - [ ] 2.4 Ensure all indicator types (distributional, geographic, welfare, fiscal) export correctly
  - [ ] 2.5 Add unit tests for each indicator type export

- [ ] Task 3: Verify and enhance ComparisonResult exports (AC: #3)
  - [ ] 3.1 Write tests to verify `ComparisonResult.export_csv()` works correctly
  - [ ] 3.2 Write tests to verify `ComparisonResult.export_parquet()` works correctly
  - [ ] 3.3 Verify delta columns are included in exports
  - [ ] 3.4 Add metadata inclusion (scenario labels, baseline label) if not present
  - [ ] 3.5 Document export schema in docstrings

- [ ] Task 4: Add FastAPI export endpoints (AC: #4 backend prep)
  - [ ] 4.1 Add `POST /api/runs/{run_id}/export` endpoint for panel export
  - [ ] 4.2 Add `POST /api/runs/{run_id}/indicators/{type}/export` endpoint
  - [ ] 4.3 Add `POST /api/comparisons/{comparison_id}/export` endpoint
  - [ ] 4.4 Support format parameter: `format=csv` or `format=parquet`
  - [ ] 4.5 Return `FileResponse` with appropriate content-type and filename headers
  - [ ] 4.6 Add tests for export endpoints

- [ ] Task 5: Add notebook export examples (AC: #6)
  - [ ] 5.1 Add export section to quickstart notebook with CSV example
  - [ ] 5.2 Add export section to advanced notebook with Parquet example
  - [ ] 5.3 Show round-trip verification (export then re-read with polars)
  - [ ] 5.4 Verify notebooks pass CI execution

- [ ] Task 6: Final validation (AC: #1-6)
  - [ ] 6.1 Run all export-related tests
  - [ ] 6.2 Verify CSV files are valid and readable by pandas/polars
  - [ ] 6.3 Verify Parquet files include schema metadata
  - [ ] 6.4 Verify notebook examples execute without errors
  - [ ] 6.5 Update `__init__.py` exports if any public API additions

## Dev Notes

### Architecture Compliance

This story implements **FR33** (export tables and indicators in CSV/Parquet) from the PRD and supports both Sophie (analyst) and Marco (researcher) user journeys.

**Key architectural constraints:**

- **PyArrow-first exports** — Use `pyarrow.csv` and `pyarrow.parquet` writers (not pandas) for consistency with existing codebase patterns. [Source: architecture.md#Data-Contracts]
- **Facade delegation** — `SimulationResult.export_*` delegates to `PanelOutput.to_*` methods. Do not duplicate export logic.
- **Manifest traceability** — Every export should be traceable back to a run manifest. Parquet files embed manifest_id in schema metadata; CSV files can include a header comment.
- **Path return convention** — All export methods return `Path` to the written file, matching existing `PanelOutput.to_csv()` and `PanelOutput.to_parquet()` patterns.

### Existing Export Infrastructure

**Already implemented (Story 3-7 and 4-5):**

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

**Needs implementation:**

```python
# SimulationResult (interfaces/api.py) — NEW
class SimulationResult:
    def export_csv(self, path: str | Path) -> Path:
        """Export panel output to CSV file."""
        if self.panel_output is None:
            raise SimulationError("No panel output available for export")
        return self.panel_output.to_csv(path)

    def export_parquet(self, path: str | Path) -> Path:
        """Export panel output to Parquet file with manifest metadata."""
        if self.panel_output is None:
            raise SimulationError("No panel output available for export")
        return self.panel_output.to_parquet(path)

# IndicatorResult (indicators/types.py) — NEW
class IndicatorResult:
    def export_csv(self, path: str | Path) -> Path:
        """Export indicator table to CSV file."""
        import pyarrow.csv as pa_csv
        from pathlib import Path
        path = Path(path)
        pa_csv.write_csv(self.to_table(), path)
        return path

    def export_parquet(self, path: str | Path) -> Path:
        """Export indicator table to Parquet file."""
        import pyarrow.parquet as pq
        from pathlib import Path
        path = Path(path)
        pq.write_table(self.to_table(), path)
        return path
```

### FastAPI Export Endpoint Pattern

```python
# interfaces/api_routes.py (or similar)
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import tempfile

router = APIRouter()

@router.post("/api/runs/{run_id}/export")
async def export_run(
    run_id: str,
    format: str = "csv",  # "csv" or "parquet"
) -> FileResponse:
    """Export simulation panel output to file."""
    # Load result from storage
    result = load_simulation_result(run_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    # Export to temp file
    suffix = ".csv" if format == "csv" else ".parquet"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        output_path = Path(tmp.name)

    if format == "csv":
        result.export_csv(output_path)
        media_type = "text/csv"
    else:
        result.export_parquet(output_path)
        media_type = "application/octet-stream"

    filename = f"{run_id}_panel{suffix}"
    return FileResponse(
        path=output_path,
        media_type=media_type,
        filename=filename,
    )
```

### UX Design Alignment

From the UX specification, Journey 5 (Export Flow):

- **One-action export** — Export is at most 2 clicks: trigger → confirm
- **Format defaults to last-used format** — Store preference in session
- **Run manifest always included** — Every export includes provenance metadata
- **Preview before write** — Show first rows, column summary, file size estimate
- **Reproducibility hash** — Can be added as Parquet metadata (future enhancement)

### Scope Guardrails

**In scope:**
- `SimulationResult.export_csv()` and `export_parquet()` methods
- `IndicatorResult.export_csv()` and `export_parquet()` methods
- Verification of existing `ComparisonResult` export methods
- FastAPI export endpoints (backend only, GUI wiring deferred to 6-4b completion)
- Notebook export examples in quickstart and advanced notebooks
- Unit tests for all export methods

**Out of scope (deferred):**
- GUI export preview component (requires 6-4b)
- GUI download button wiring (requires 6-4b)
- Notebook export format (Jupyter notebook reproduction) — Phase 2
- Export to Excel/XLSX format
- Bulk/batch export of multiple runs
- Export streaming for very large datasets

### Testing Standards

- Export tests use `pytest` with `tmp_path` fixture for temporary files
- Verify exported files are readable by PyArrow and polars
- Verify column names and types match source data
- Verify Parquet schema metadata contains expected keys
- Test edge cases: empty panels, failed simulations, null values
- Notebook export examples are tested via `pytest --nbmake`

### Previous Story Intelligence

**From Story 6-4a (Static GUI Prototype):**
- Export preview component spec exists in UX design
- Target stack: React + Shadcn/ui + Tailwind v4 + Vite
- ExportPreview component design defined but not implemented yet

**From Story 6-1 (Python API):**
- `SimulationResult` is a frozen dataclass with `panel_output: PanelOutput | None`
- Error handling uses `SimulationError` from `interfaces/errors.py`
- All API methods have type hints and docstrings

**From Story 3-7 (Panel Output):**
- `PanelOutput.to_csv()` uses `pyarrow.csv.write_csv()`
- `PanelOutput.to_parquet()` adds schema metadata with panel version
- Return type is `Path` to written file

**From Story 4-5 (Comparison Tables):**
- `ComparisonResult.export_csv()` and `export_parquet()` exist
- These use `csv.write_csv()` and `pq.write_table()`
- Return type is `None` (inconsistent with PanelOutput — consider changing to Path)

### File Locations

```
src/reformlab/
├── interfaces/
│   ├── api.py             ← Add SimulationResult.export_* methods
│   ├── errors.py          ← ExportError if needed
│   └── api_routes.py      ← NEW: FastAPI export endpoints
├── indicators/
│   ├── types.py           ← Add IndicatorResult.export_* methods
│   └── comparison.py      ← Verify/enhance ComparisonResult exports
├── orchestrator/
│   └── panel.py           ← Existing PanelOutput.to_* methods (reference)
└── __init__.py            ← Export any new public symbols

notebooks/
├── quickstart.ipynb       ← Add export example section
└── advanced.ipynb         ← Add export example section

tests/
├── unit/
│   ├── interfaces/
│   │   └── test_api_export.py     ← NEW: SimulationResult export tests
│   └── indicators/
│       ├── test_types_export.py   ← NEW: IndicatorResult export tests
│       └── test_comparison.py     ← Add export verification tests
└── integration/
    └── test_api_routes.py         ← NEW: FastAPI endpoint tests
```

### References

- [Source: prd.md#Functional-Requirements] — FR33 export tables and indicators
- [Source: backlog BKL-605] — Story acceptance criteria
- [Source: architecture.md#Data-Contracts] — CSV/Parquet interoperability
- [Source: ux-design-specification.md#Journey-5-Export-Flow] — Export UX patterns
- [Source: orchestrator/panel.py] — Existing PanelOutput export implementation
- [Source: indicators/comparison.py] — Existing ComparisonResult export implementation
- [Source: interfaces/api.py] — SimulationResult class to extend

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
