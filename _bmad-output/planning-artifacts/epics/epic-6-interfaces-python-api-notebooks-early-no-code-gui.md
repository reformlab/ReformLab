# Epic 6: Interfaces (Python API, Notebooks, Early No-Code GUI)

**User outcome:** User can operate the full analysis workflow from Python API, notebooks, or a no-code GUI.

**Status:** done

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-601 | Story | P0 | 5 | Implement stable Python API for run orchestration | done | FR30, NFR16 |
| BKL-602 | Story | P0 | 5 | Build quickstart notebook | done | FR34, NFR19 |
| BKL-603 | Story | P0 | 5 | Build advanced notebook (multi-year + vintage + comparison) | done | FR30, FR35 |
| BKL-604a | Story | P0 | 3 | Build static GUI prototype | done | FR32 |
| BKL-604b | Story | P0 | 5 | Wire GUI prototype to FastAPI backend | done | FR32 |
| BKL-605 | Task | P0 | 3 | Add export actions in API/GUI for CSV/Parquet outputs | done | FR33 |
| BKL-606 | Task | P1 | 3 | Improve operational error UX | done | FR4, FR27 |

## Epic-Level Acceptance Criteria

- API supports full run lifecycle from data ingest to comparison outputs.
- GUI supports baseline/reform scenario operations without code.

## Story-Level Acceptance Criteria

**BKL-601: Implement stable Python API for run orchestration**

- Given the Python API, when a user calls the run method with a scenario configuration, then a complete orchestration cycle executes and returns results.
- Given API objects (scenarios, results, manifests), when displayed in a Jupyter notebook, then sensible `__repr__` output is shown.
- Given an invalid scenario configuration, when passed to the API, then a clear error is raised before execution begins.

**BKL-602: Build quickstart notebook**

- Given a fresh install of the package, when the quickstart notebook is run cell by cell, then it completes without errors and produces distributional charts.

**BKL-603: Build advanced notebook (multi-year + vintage + comparison)**

- Given the advanced notebook, when executed, then it demonstrates a multi-year run with vintage tracking and baseline/reform comparison.
- Given the advanced notebook, when run in CI, then it passes without modification.

**BKL-604a: Build static GUI prototype**

- Given the prototype, when opened in a browser, then the analyst can navigate the full configuration and simulation flows using clickable screens.
- Given the prototype, when inspected, then it uses the target stack (React + Shadcn/ui + Tailwind) so screens are reusable in the final app.

**BKL-604b: Wire GUI prototype to FastAPI backend**

- Given the wired GUI, when an analyst creates a new scenario from a template, then no code editing is required.
- Given the wired GUI, when an analyst clones a baseline and modifies parameters, then a reform scenario is created and linked to the baseline.
- Given two completed runs in the GUI, when comparison is invoked, then side-by-side indicator tables are displayed.

**BKL-605: Add export actions in API/GUI for CSV/Parquet outputs**

- Given completed scenario results, when export to CSV is invoked, then a valid CSV file is produced with correct headers.
- Given completed scenario results, when export to Parquet is invoked, then a valid Parquet file is produced readable by pandas/polars.

---
