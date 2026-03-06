---
title: 'Quickstart Data Flow Rework — Real Pipeline with Adapter Explainer'
slug: 'quickstart-data-flow-rework'
created: '2026-03-01'
status: 'completed'
stepsCompleted: [1, 2, 3, 4, 5, 6]
tech_stack: ['Python 3.13+', 'pyarrow', 'csv']
files_to_modify: ['data/populations/demo-quickstart-100.csv', 'src/reformlab/computation/mock_adapter.py', 'src/reformlab/interfaces/api.py', 'notebooks/quickstart.ipynb', 'tests/interfaces/test_api.py', 'tests/notebooks/test_quickstart_notebook.py']
code_patterns: ['from __future__ import annotations in every file', 'lazy imports inside methods', 'frozen dataclasses for domain types', 'MockAdapter is non-frozen class with call_log', 'PyArrow tables as canonical data type', 'module-level docstrings referencing stories', 'logging via getLogger(__name__)']
test_patterns: ['tests/ mirrors src/reformlab/', 'class-based test grouping by feature', 'conftest.py per subsystem', 'inline PyArrow table fixtures', 'notebook tests are static JSON checks (no kernel)']
---

# Tech-Spec: Quickstart Data Flow Rework — Real Pipeline with Adapter Explainer

**Created:** 2026-03-01

## Overview

### Problem Statement

The quickstart notebook bypasses the real data pipeline entirely. `create_quickstart_adapter()` generates hardcoded data in-memory (`income = 15000 + i*800`) and returns a `MockAdapter` that ignores population input — its `compute()` method always returns the same pre-built table regardless of what population data it receives. Users never see how data enters the system. They don't learn the real workflow of loading a population file, passing it through the adapter, and getting computed results back. The adapter concept — the core architectural boundary between ReformLab's orchestration and the computation backend — is invisible to them.

### Solution

1. Ship a pre-generated CSV population file in the repo (`data/populations/demo-quickstart-100.csv`) with 100 synthetic households
2. Make `MockAdapter` population-aware — instead of ignoring population data, it reads the population table and applies a simple formula (`carbon_tax = carbon_emissions × rate`) when a population is provided
3. Rework `create_quickstart_adapter()` to produce a population-aware adapter that computes from real input data
4. Rewrite the quickstart notebook to use `population_path` → load CSV → explain the adapter pattern → run → inspect results, with clear prose explaining what adapters are and why they exist

### Scope

**In Scope:**

- Pre-generated demo CSV file (`data/populations/demo-quickstart-100.csv`) with 100 households from `generate_synthetic_population(size=100, seed=42)`
- Population-aware mode for `MockAdapter` — when population data has rows, compute from it instead of returning fixed output
- Updated `create_quickstart_adapter()` to produce a population-aware adapter
- Quickstart notebook rewrite: load CSV → explain adapter → run with `population_path` → inspect
- Notebook prose sections explaining what adapters are and how the pipeline works
- Test updates for `MockAdapter`, `create_quickstart_adapter()`, and notebook static checks

**Out of Scope:**

- `generate_population()` changes (already works, separate topic)
- Advanced notebook changes
- OpenFisca adapter changes
- Visualization API (separate spec in progress)
- Server/GUI population browsing
- Parquet format for the demo file (CSV chosen for human inspectability)

## Context for Development

### Codebase Patterns

- `ComputationAdapter` is a `@runtime_checkable` structural `Protocol` with `compute(population, policy, period) -> ComputationResult` and `version() -> str`
- `MockAdapter` currently accepts `default_output: pa.Table | None` at construction and always returns it from `compute()`, ignoring population data entirely
- `PopulationData` is `@dataclass(frozen=True)` with `tables: dict[str, pa.Table]` and `metadata: dict[str, Any]`; population table lives under the `"default"` key
- `generate_synthetic_population(size, seed)` produces columns: `household_id` (int64), `income` (float64), `carbon_emissions` (float64)
- `_load_population_data(path)` reads CSV/Parquet into `PopulationData(tables={"default": table}, metadata={"source": str(path)})`
- `ScenarioConfig.population_path` is `Path | None` — when set, the orchestrator loads the file via `_load_population_data()` and passes the `PopulationData` to `ComputationStep`, which calls `adapter.compute(population=..., policy=..., period=...)`
- `create_quickstart_adapter()` currently builds a hardcoded `pa.Table` with `income = 15000 + i*800` and wraps it in `MockAdapter(default_output=synthetic_output)` — the adapter ignores whatever population it receives
- Current quickstart notebook uses `adapter=adapter` parameter in `run_scenario()` to inject the mock adapter, and `ScenarioConfig` has no `population_path`

### Files to Modify/Create

| File | Action | Purpose |
| ---- | ------ | ------- |
| `data/populations/demo-quickstart-100.csv` | Create | Pre-generated demo population (100 households, seed=42) |
| `src/reformlab/computation/mock_adapter.py` | Modify | Add population-aware computation mode |
| `src/reformlab/interfaces/api.py` | Modify | Update `create_quickstart_adapter()` to produce population-aware adapter |
| `notebooks/quickstart.ipynb` | Modify | Rewrite to use `population_path` + adapter explainer |
| `tests/interfaces/test_api.py` | Modify | Update `TestQuickstartAdapter` tests |
| `tests/notebooks/test_quickstart_notebook.py` | Modify | Update static assertions for new notebook content |

### Files to Reference (read-only)

| File | Purpose |
| ---- | ------- |
| `src/reformlab/computation/adapter.py` | `ComputationAdapter` protocol definition |
| `src/reformlab/computation/types.py` | `PopulationData`, `PolicyConfig`, `ComputationResult` definitions |
| `src/reformlab/data/synthetic.py` | `generate_synthetic_population()` — column schema and generation logic |
| `src/reformlab/orchestrator/computation_step.py` | How the orchestrator calls `adapter.compute()` |
| `src/reformlab/interfaces/api.py` lines 1368-1409 | `_load_population_data()` — how CSV/Parquet is loaded into `PopulationData` |

### Technical Decisions

- **CSV not Parquet** for the demo file — users can open it in any text editor or spreadsheet to inspect before running
- **Backward-compatible MockAdapter** — the existing `default_output` behavior is preserved when no population data is provided (empty tables dict or zero rows). This avoids breaking existing orchestrator/template tests that use `MockAdapter` with pre-built output.
- **Simple formula** in population-aware mode: `carbon_tax = carbon_emissions × (rate / baseline_rate)`, `disposable_income = income - carbon_tax`. This mirrors what the current hardcoded adapter does but computes from actual population data.
- **`population_path` on `ScenarioConfig`** — the notebook will set this to the demo CSV path, teaching users the real configuration pattern
- **Adapter still injected via `adapter=` parameter** — the quickstart still needs a mock adapter (no OpenFisca), but now the adapter reads the population instead of ignoring it

## Review Notes
- Adversarial review completed with 10 findings
- Findings: 10 total, 6 fixed, 4 skipped (pre-existing or acceptable)
- Resolution approach: auto-fix for real findings
- Fixed: F1 (notebook cell types), F2 (column validation), F3 (fallback semantics), F4 (docstring), F5 (evaluated, no fix needed), F6 (removed alias)
- Skipped: F7 (pre-existing dead code), F8 (pre-existing test style), F9 (pre-existing formula), F10 (acceptable for demo)
