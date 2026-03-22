---
title: 'Codebase Explainability Toolkit — Marimo Notebooks + Swimm Architecture Tour'
slug: 'codebase-explainability-toolkit'
created: '2026-03-07'
status: 'in-progress'
stepsCompleted: [1, 2]
tech_stack: ['Python 3.13+', 'marimo', 'swimm', 'pyarrow', 'matplotlib', 'pytest']
files_to_modify: ['pyproject.toml', 'notebooks/quickstart.ipynb', 'notebooks/advanced.ipynb', 'notebooks/population-french-household-example.ipynb', 'notebooks/demo/epic14_discrete_choice.ipynb', '.github/workflows/ci.yml', 'tests/notebooks/test_quickstart_notebook.py', 'tests/notebooks/test_advanced_notebook.py', 'tests/notebooks/test_epic14_notebook.py', '.swm/']
code_patterns: ['from __future__ import annotations in every file', 'PyArrow tables as canonical data type', 'matplotlib for visualization via create_figure()', 'MockAdapter for demos', 'public API imports only in notebooks', 'section-by-section notebook structure: Setup -> Build -> Configure -> Run -> Visualize -> Export', 'plt.show() after every chart (remove in Marimo)', 'show() helper for table display', 'Path(__file__).parent for path resolution']
test_patterns: ['tests/notebooks/ static JSON validation via _load_notebook() + _all_sources()', 'nbmake kernel execution in CI for 4 notebooks', 'string matching on source code for import/section/API call checks', 'CI workflow assertion tests (test_ci_includes_notebook)']
---

# Tech-Spec: Codebase Explainability Toolkit — Marimo Notebooks + Swimm Architecture Tour

**Created:** 2026-03-07

## Overview

### Problem Statement

The ReformLab codebase has been largely AI-generated and lacks two things: (1) interactive exploration tools that let a domain expert tweak parameters and see results reactively, and (2) a guided architectural walkthrough explaining how the 7 layers connect. The current Jupyter notebooks are git-unfriendly (`.ipynb` files produce massive JSON diffs), non-reactive (changing a parameter requires manual re-execution of downstream cells), and require the `nbmake` pytest plugin for CI execution. There is no structured tour of the codebase architecture.

### Solution

Two complementary tools:

1. **Marimo migration** — Convert the 4 CI-tested Jupyter notebooks to Marimo reactive `.py` notebooks. Add interactive UI widgets (sliders, dropdowns) for key policy parameters. Leverage Marimo's DAG-based reactivity so changing a parameter auto-updates all downstream cells and charts. Since Marimo notebooks are plain `.py` files, they can be tested with plain `pytest` — drop `nbmake`.

2. **Swimm architecture tour** — Set up Swimm and create one architecture walkthrough document covering the 7-layer data flow: Computation Adapter → Data Layer → Scenario Templates → Dynamic Orchestrator → Vintage → Indicators → Governance. The tour links to actual code locations so it stays coupled to the codebase.

### Scope

**In Scope:**

- Migrate 4 notebooks to Marimo `.py` format: `quickstart`, `advanced`, `population-french-household-example`, `epic14_discrete_choice`
- Add `marimo` as project dependency
- Add interactive widgets for key parameters (carbon tax rate, beta_cost, seed, projection horizon)
- Update CI to run Marimo notebooks with `pytest` instead of `nbmake`
- Remove `nbmake` dev dependency
- Install and configure Swimm
- Create one architecture walkthrough tour (7-layer data flow)
- Update `tests/notebooks/` static validation tests for new `.py` format

**Out of Scope:**

- Legacy duplicate notebook cleanup (epic1-5 in `notebooks/` root)
- Demo epic1-5 notebook migration (only the 4 CI-tested notebooks)
- Epic-by-epic Swimm tours
- Multi-audience documentation
- Advanced widget design beyond basic sliders/dropdowns
- Changes to `src/` library code

## Context for Development

### Codebase Patterns

- Notebooks import from public API only (`from reformlab import ...`, `from reformlab.templates.schema import ...`)
- `MockAdapter` used in all demo notebooks for computation without OpenFisca
- All notebooks use `matplotlib` for charts — via `reformlab.visualization.create_figure()` and direct `plt.subplots()` calls
- `PyArrow` tables are the canonical data type throughout
- Notebooks follow a section-by-section pattern: Setup → Build Data → Configure → Run → Visualize → Export
- All 4 notebooks use `plt.show()` after charts — these calls become unnecessary in Marimo (auto-display)
- `show()` helper (from `reformlab.visualization`) prints PyArrow tables as aligned text — works unchanged in Marimo but could optionally use `mo.ui.table()` for interactivity
- Path resolution uses `Path(__file__).parent` with fallback — works identically in Marimo `.py` files

### Visualization Module Compatibility

The entire `reformlab.visualization` module is **100% Marimo-compatible** with no changes needed:

| Function | Implementation | Marimo Notes |
| ---- | ---- | ---- |
| `show(table, n)` | Pure PyArrow + print | Works as-is; optionally replace with `mo.ui.table()` |
| `create_figure(...)` | `plt.subplots()` + styling | Works as-is; Marimo auto-displays |
| `plot_deciles(...)` | Filter + bar chart | Works as-is |
| `plot_yearly(...)` | Sort + line chart | Works as-is |
| `plot_comparison(...)` | Grouped bar chart | Works as-is |

### Per-Notebook Investigation

#### quickstart.ipynb (27 cells, linear flow)

**Imports:** `reformlab` public API (`RunConfig`, `ScenarioConfig`, `create_quickstart_adapter`, `run_scenario`, `show`), `reformlab.templates.schema` (typed policy objects), `matplotlib.pyplot`, `pyarrow.csv`, `json`, `tempfile`

**File I/O:** Reads `data/populations/demo-quickstart-100.csv`, writes to temp dir for exports

**Widget opportunities:**
- `rate_schedule={2025: 44.0}` → carbon tax rate slider (0-200 EUR/tCO2)
- `rate_schedule={2025: 100.0}` → comparison rate slider
- `seed=42` → integer input

**Charts:** 2 (plot_deciles, plot_comparison)

#### advanced.ipynb (47 cells, multi-scenario branches)

**Imports:** Same as quickstart plus `reformlab.vintage` (VintageConfig, VintageTransitionStep, etc.), `reformlab.indicators` (ComparisonConfig, FiscalConfig, compare_scenarios), `reformlab.visualization.create_figure`, `pyarrow.compute`, `pyarrow.parquet`

**File I/O:** Same CSV population read, Parquet exports for panel/fiscal/comparison

**Widget opportunities:**
- `rate_schedule={2025: 50.0, ..., 2034: 100.0}` → start/end rate sliders
- `YearSchedule(start_year=2025, end_year=2034)` → year range slider
- `max_age=15` → vintage max age slider (5-25)
- `tolerance=1.5` → convergence tolerance slider

**Charts:** 4 (plot_yearly, stackplot, plot_comparison, fiscal line)

#### population-french-household-example.ipynb (28 cells, linear pipeline)

**Imports:** `reformlab.population` (ConditionalSamplingMethod, IPFMergeMethod, PopulationPipeline, PopulationValidator, etc.), bare `matplotlib.pyplot`, `pyarrow`

**File I/O:** Reads 4 fixture CSVs from `tests/fixtures/populations/sources/`, writes to temp dir

**Widget opportunities:**
- `SEED = 42` → integer input
- `tolerance=1.5` → IPF convergence slider
- `MarginalConstraint(tolerance=0.15)` → per-constraint tolerance slider
- `max_iterations=200` → IPF iterations slider

**Charts:** 3 histogram pairs via raw `plt.subplots(1, 2)`

#### epic14_discrete_choice.ipynb (28 cells, declarative pipeline)

**Imports:** `reformlab.computation.mock_adapter`, `reformlab.computation.types`, `reformlab.discrete_choice` (12 symbols), `reformlab.governance.capture`, `reformlab.indicators`, `reformlab.orchestrator` (runner, panel, types, computation_step), `reformlab.visualization.create_figure`

**File I/O:** Inline population generation (no CSV read), Parquet export of panel

**Widget opportunities:**
- `CARBON_TAX_SCHEDULE` → start/end rate sliders (EUR 50-100/tCO2)
- `EV_SUBSIDY = 4000.0` → EUR slider
- `HEAT_PUMP_SUBSIDY = 2000.0` → EUR slider
- `N = 100` → population size slider
- `taste_params_vehicle.beta_cost = -0.01` → cost sensitivity slider
- `taste_params_heating.beta_cost = -0.02` → cost sensitivity slider
- `vehicle_age > 8` → eligibility threshold slider
- `heating_age > 12` → eligibility threshold slider
- `seed=42` → integer input

**Charts:** 2 stackplots (vehicle + heating fleet), 1 bar chart (carbon tax by decile)

### Current Test Files (Deep Analysis)

All 3 test files follow the same pattern: parse `.ipynb` JSON, concatenate all code cell sources into one string, then assert substrings are present.

#### test_quickstart_notebook.py (8 tests)
- Checks: file exists, outputs cleared, public API imports (`from reformlab import`), visualization API calls (`plot_deciles(`, `plot_comparison(`), section headings (`## 1. Define a Policy`), export examples (`result.export_csv(`), population loading (`POPULATION_PATH`), section ordering

#### test_advanced_notebook.py (9 tests)
- Checks: file exists, outputs cleared, public API surfaces (reformlab, vintage, indicators imports), visualization API (`plot_yearly(`, `create_figure(`), multi-year/vintage/comparison sections (11 sub-checks), reproducibility sections, export + round-trip, section ordering, CI workflow inclusion

#### test_epic14_notebook.py (6 tests)
- Checks: file exists, outputs cleared, public API (discrete_choice, orchestrator, mock_adapter imports), required sections (9 headings), key API calls (11 function calls), behavioral response wiring (6 specific code patterns), CI workflow inclusion

**Migration impact:** All tests parse JSON notebook format — must be rewritten for `.py` format. Options:
1. AST parsing of `.py` files for import/function call checks
2. Source text scanning (same substring checks, just read `.py` instead of JSON)
3. Execution-based tests (import and run the marimo notebook)

**Recommended approach:** Option 2 (simplest migration) — read `.py` file as text, same substring assertions. The `.py` source will contain the same import statements and function calls.

### Architecture Layers (for Swimm tour)

| Layer | Package | Key Entry Point | What to Explain |
| ----- | ------- | --------------- | --------------- |
| 1. Computation Adapter | `src/reformlab/computation/` | `adapter.py` (Protocol) | The core abstraction: how OpenFisca is decoupled via Protocol |
| 2. Data Layer | `src/reformlab/data/` | `pipeline.py`, `synthetic.py` | Data ingestion, CSV/Parquet boundaries, synthetic population |
| 3. Scenario Templates | `src/reformlab/templates/` | `workflow.py`, `carbon_tax/` | How policy scenarios are defined and composed |
| 4. Dynamic Orchestrator | `src/reformlab/orchestrator/` | `runner.py` (Orchestrator) | **The core product** — multi-year step pipeline execution |
| 5. Vintage | `src/reformlab/vintage/` | `transition.py`, `config.py` | Cohort tracking and fleet composition evolution |
| 6. Indicators | `src/reformlab/indicators/` | `distributional.py`, `fiscal.py` | Output metrics: distributional, fiscal, welfare, comparison |
| 7. Governance | `src/reformlab/governance/` | `manifest.py`, `lineage.py` | Reproducibility: manifests, hashing, assumption capture |

### Files to Reference (read-only)

| File | Purpose |
| ---- | ------- |
| `src/reformlab/computation/adapter.py` | `ComputationAdapter` protocol — the core abstraction boundary |
| `src/reformlab/orchestrator/runner.py` | `Orchestrator` class — the core product |
| `src/reformlab/governance/manifest.py` | Run manifest structure — reproducibility backbone |
| `src/reformlab/visualization/__init__.py` | Public chart API: `create_figure`, `show`, `plot_deciles`, `plot_yearly`, `plot_comparison` |
| `src/reformlab/visualization/styling.py` | `create_figure()` and `style_axes()` implementation |
| `src/reformlab/visualization/plotting.py` | `plot_deciles()`, `plot_yearly()`, `plot_comparison()` implementation |
| `src/reformlab/visualization/display.py` | `show()` table display implementation |

### Technical Decisions

- **Marimo over Streamlit** — Avoids creating a competing interface with the planned FastAPI GUI (Epic 17). Marimo is a notebook replacement, not a web app framework.
- **Marimo `.py` format** — Git-friendly diffs, importable, testable with plain pytest. No more JSON notebook noise in PRs.
- **Swimm over CodeTour** — CodeTour is unmaintained since 2022 and uses brittle line-number references that break on code changes. Swimm auto-detects when referenced code changes and flags stale docs.
- **One architecture tour first** — Keeps scope small. Epic-by-epic tours can be added later.
- **Keep matplotlib** — No migration to Marimo's built-in charting. Existing `create_figure()` works as-is in Marimo.
- **Test migration: source text scanning** — Simplest approach. Read `.py` file as text, same substring assertions as current JSON-based tests. No need for AST parsing or execution-based tests.
- **Remove `plt.show()` calls** — Marimo auto-displays matplotlib figures. Keeping `plt.show()` causes double-rendering.

## Implementation Plan

### Tasks

_To be filled in Step 3_

### Acceptance Criteria

_To be filled in Step 3_

## Additional Context

### Dependencies

- `marimo` — pure Python, pip-installable, no heavy deps
- `swimm` — CLI tool, installed separately (npm or binary), free for open-source
- Both tools are actively maintained (2026)

### Testing Strategy

- Marimo notebooks are `.py` files — test by reading source text and checking same substrings
- Remove `_load_notebook()` JSON parsing — replace with simple `Path.read_text()`
- Remove "outputs cleared" tests (no longer applicable to `.py` files)
- Remove "CI includes notebook" tests — replace with new CI config assertions for `marimo run`
- CI replaces `--nbmake` lines with `marimo run` or direct `pytest` execution

### Notes

- Primary audience for Swimm tour: Lucas (domain expert understanding AI-generated code)
- Marimo conversion can be bootstrapped with `marimo convert notebook.ipynb > notebook.py` then manual widget additions
- `ipykernel` and `jupyter` dev dependencies can be kept for now (useful for other tooling)
- All 4 notebooks are 95%+ Marimo-compatible — no blocking technical issues
- Path resolution (`Path(__file__).parent`) works identically in Marimo `.py` files
