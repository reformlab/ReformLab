---
title: 'Advanced Notebook Rework — Real Vintage Pipeline with Demo Population'
slug: 'advanced-notebook-vintage-pipeline'
created: '2026-03-01'
status: 'complete'
stepsCompleted: [1, 2, 3]
tech_stack: ['Python 3.13+', 'pyarrow', 'csv', 'matplotlib>=3.8.0']
files_to_modify: ['data/populations/demo-advanced-100.csv', 'src/reformlab/interfaces/api.py', 'src/reformlab/__init__.py', 'notebooks/advanced.ipynb', 'tests/notebooks/test_advanced_notebook.py']
code_patterns: ['from __future__ import annotations in every file', 'lazy imports inside methods', 'frozen dataclasses for domain types', 'PyArrow tables as canonical data type', 'module-level docstrings referencing stories', 'logging via getLogger(__name__)', 'VintageTransitionStep implements OrchestratorStep protocol', 'VintageState stored in YearState.data["vintage_vehicle"]']
test_patterns: ['tests/ mirrors src/reformlab/', 'class-based test grouping by feature', 'conftest.py per subsystem', 'inline PyArrow table fixtures', 'notebook tests are static JSON checks (no kernel)']
---

# Tech-Spec: Advanced Notebook Rework — Real Vintage Pipeline with Demo Population

**Created:** 2026-03-01

## Overview

### Problem Statement

The advanced notebook (BKL-603) has two major problems:

1. **Fake vintage data**: Section 2 (Vintage Tracking) uses hardcoded Python lists (`vintage_old = [50, 45, 40, ...]`) to plot a stacked area chart. The real `VintageTransitionStep` is fully implemented — it ages cohorts, retires vehicles past max age, adds new entries — but the notebook never uses it. Users see a pretty chart but learn nothing about how vintage tracking actually works in the orchestrator.

2. **No real population data**: The notebook uses `create_quickstart_adapter()` which generates hardcoded data in-memory and returns a `MockAdapter` that ignores population input. Users never load a CSV, never see household attributes like vehicle type, and never understand the data flow.

3. **No step pipeline visibility**: `run_scenario()` hardcodes `step_pipeline=(ComputationStep(...),)` — there's no way to inject `VintageTransitionStep` from the public API. The orchestrator's step-pluggable architecture — the core product — is invisible to notebook users.

The result: the notebook that's supposed to demonstrate "multi-year + vintage + comparison" (per BKL-603 acceptance criteria) demonstrates none of those with real code.

### Solution

1. Ship a `data/populations/demo-advanced-100.csv` with 100 households including `vehicle_type` column (diesel/gasoline/electric/hybrid distributed by income)
2. Add an optional `steps` parameter to `run_scenario()` so users can inject additional orchestrator steps (like `VintageTransitionStep`) into the pipeline alongside the default `ComputationStep`
3. Export vintage types from the top-level `reformlab` package so notebook users can import them directly
4. Rewrite the entire advanced notebook to use real data, real vintage tracking, and real step pipeline — every section demonstrates actual working code, not faked charts

### Scope

**In Scope:**

- New demo CSV: `data/populations/demo-advanced-100.csv` with `household_id`, `income`, `carbon_emissions`, `vehicle_type` columns
- `run_scenario()` gains optional `steps` parameter for injecting orchestrator steps
- Top-level `reformlab` exports for vintage types: `VintageConfig`, `VintageTransitionRule`, `VintageTransitionStep`, `VintageCohort`, `VintageState`, `VintageSummary`
- Full advanced notebook rewrite (all 5 sections):
  - Section 1: Multi-year simulation with real CSV population
  - Section 2: Real `VintageTransitionStep` configured and registered, cohort aging extracted from `yearly_states`
  - Section 3: Baseline vs reform comparison with real data
  - Section 4: Lineage and reproducibility (unchanged logic, but using real data)
  - Section 5: Next steps (updated prose)
- Updated notebook static tests

**Out of Scope:**

- Quickstart notebook changes (separate spec: `quickstart-data-flow-rework`)
- Visualization API (separate spec: `visualization-api`)
- New asset classes beyond vehicle (MVP restriction)
- Panel output surfacing vintage columns as table rows (future story)
- Behavioral response steps (Phase 2 — vintage affecting computation)
- `MockAdapter` population-aware changes (handled by quickstart spec)

## Context for Development

### Codebase Patterns

**Vintage subsystem (fully implemented):**
- `VintageTransitionStep` implements `OrchestratorStep` protocol: `name: str`, `depends_on: tuple[str, ...]`, `execute(year: int, state: YearState) -> YearState`
- `VintageConfig(asset_class, rules, initial_state)` requires at least one retirement rule (`max_age_retirement`) and one entry rule (`fixed_entry` or `proportional_entry`)
- `VintageTransitionRule(rule_type, parameters, description)` — `rule_type` is `Literal["fixed_entry", "proportional_entry", "max_age_retirement"]`
- `VintageState(asset_class, cohorts, metadata)` is frozen dataclass; stored in `YearState.data["vintage_{asset_class}"]`
- `VintageCohort(age, count, attributes)` — frozen dataclass, `age >= 0`, `count >= 0`
- `VintageSummary.from_state(vintage_state)` derives: `total_count`, `cohort_count`, `age_distribution: dict[int, int]`, `mean_age: float`, `max_age: int`
- MVP restricts `asset_class` to `"vehicle"` only (`_SUPPORTED_ASSET_CLASSES = ("vehicle",)`)
- `VintageTransitionStep.execute()` order: load/init state → age all cohorts (+1) → retire above max age → add new entry cohorts (age=0)

**Orchestrator pipeline:**
- `OrchestratorRunner(step_pipeline, seed, initial_state, ...)` accepts `step_pipeline: tuple[PipelineStep, ...]`
- `PipelineStep = YearStep | OrchestratorStep` — union type accepting both callables and protocol steps
- `Orchestrator._run_year()` iterates `config.step_pipeline` in order, calling `step.execute(year, state)` for protocol steps
- `_execute_orchestration()` (api.py:1250) currently hardcodes `step_pipeline=(ComputationStep(...),)` with `initial_state={}`
- `run_scenario()` signature: `run_scenario(config, adapter=None, *, skip_memory_check=False)` — needs `steps` and `initial_state` added
- `WorkflowResult.outputs["yearly_states"]` preserves `state.data` dict values (including `VintageState` objects) — no serialization boundary

**Public API export chain:**
- `reformlab.__init__` → imports from `reformlab.interfaces` and `reformlab.visualization`
- `reformlab.interfaces.__init__` → imports from `reformlab.interfaces.api`
- Vintage types currently exported only from `reformlab.vintage` — not from top-level package

**Existing notebook bugs (to be fixed in rewrite):**
- Cell 26 references `comp_table` which is never defined (should be `comparison.table`)
- Cell 26 uses `pc` (pyarrow.compute) which is only imported in cell 28
- Cell 26 has `import pyarrow.compute as pc` inside a conditional block but the cell itself never imports it

**Notebook static tests (`test_advanced_notebook.py`):**
- `test_advanced_notebook_covers_multi_year_vintage_and_comparison_sections` asserts `vintage_old = [50, 45, 40` — this assertion must change to expect real vintage API usage
- `test_advanced_notebook_uses_public_api_surfaces` asserts `reformlab.computation` not in source — vintage imports must go through `reformlab` or `reformlab.vintage`, not internal modules
- `test_advanced_notebook_uses_visualization_api` asserts `plot_yearly(`, `plot_comparison(`, `create_figure(` — these should be preserved
- `test_ci_executes_advanced_notebook_with_nbmake` checks CI workflow runs notebook end-to-end

**Data patterns:**
- `generate_synthetic_population(size, seed)` produces 3 columns: `household_id` (int64), `income` (float64), `carbon_emissions` (float64)
- Demo CSV must be human-inspectable and committed to repo
- `_load_population_data(path)` reads CSV/Parquet into `PopulationData(tables={"default": table}, metadata={"source": str(path)})`

### Files to Modify/Create

| File | Action | Purpose |
| ---- | ------ | ------- |
| `data/populations/demo-advanced-100.csv` | Create | Demo population with vehicle_type attribute (100 households) |
| `src/reformlab/interfaces/api.py` | Modify | Add `steps` and `initial_state` parameters to `run_scenario()` and `_execute_orchestration()` |
| `src/reformlab/__init__.py` | Modify | Export vintage types from top-level package |
| `notebooks/advanced.ipynb` | Modify | Full rewrite — real vintage pipeline, real data |
| `tests/notebooks/test_advanced_notebook.py` | Modify | Update static assertions for new notebook content |
| `tests/interfaces/test_api.py` | Modify | Add tests for `run_scenario()` with `steps` parameter |

### Files to Reference (read-only)

| File | Purpose |
| ---- | ------- |
| `src/reformlab/vintage/types.py` | `VintageCohort`, `VintageState`, `VintageSummary` — domain types |
| `src/reformlab/vintage/config.py` | `VintageConfig`, `VintageTransitionRule` — configuration |
| `src/reformlab/vintage/transition.py` | `VintageTransitionStep` — the step implementation |
| `src/reformlab/vintage/__init__.py` | Current vintage package exports (8 names) |
| `src/reformlab/orchestrator/runner.py` | `OrchestratorRunner` — how step_pipeline is consumed; `Orchestrator._run_year()` loop |
| `src/reformlab/orchestrator/types.py` | `YearState`, `OrchestratorConfig`, `PipelineStep` — core types |
| `src/reformlab/orchestrator/step.py` | `StepRegistry`, `OrchestratorStep` protocol |
| `src/reformlab/data/synthetic.py` | `generate_synthetic_population()` — column schema |
| `tests/vintage/test_integration.py` | Integration test patterns: VintageConfig setup, Orchestrator wiring, assertion patterns |
| `src/reformlab/interfaces/__init__.py` | Re-export chain for public API |

### Technical Decisions

- **`steps` parameter on `run_scenario()`** — keyword-only, optional tuple of `PipelineStep` instances. These are appended after the default `ComputationStep` in the pipeline tuple passed to `OrchestratorRunner`. This preserves backward compatibility (no steps = current behavior) while letting advanced users compose pipelines. The type hint uses `PipelineStep` (the existing union type from `orchestrator.types`) so both protocol steps and bare callables work.
- **`initial_state` parameter on `run_scenario()`** — keyword-only, optional `dict[str, Any]`. Passed to `OrchestratorRunner(initial_state=...)`. Needed so the notebook can seed initial vintage state (e.g., a fleet with pre-existing cohorts at various ages) before the first year runs. Without this, vintage starts from empty every time.
- **CSV for demo population** — same rationale as quickstart: human-inspectable in any text editor. File committed to repo at `data/populations/demo-advanced-100.csv`.
- **`vehicle_type` column** — values: `"diesel"`, `"gasoline"`, `"electric"`, `"hybrid"`. Distribution correlates with income: lower-income households skew diesel/gasoline, higher-income skew electric/hybrid. This makes the population data richer and gives context for why vintage tracking matters (fleet turnover from fossil to electric).
- **Vintage doesn't affect computation yet** — the notebook will explain this explicitly: vintage state evolves alongside computation but doesn't yet feed back into carbon tax calculations (that's Phase 2 behavioral response). Users see cohorts aging, which teaches the mechanism even without feedback loops.
- **`VintageSummary` for inspection** — the notebook uses `VintageSummary.from_state()` to display derived metrics (mean age, total count, age distribution) rather than printing raw cohort tuples. More readable and teaches the downstream API.
- **No new `create_advanced_adapter()`** — the notebook uses the same `create_quickstart_adapter()` with the advanced CSV file. This assumes the quickstart data flow rework spec has landed. If it hasn't, the notebook falls back to passing `adapter=` directly.
- **Vintage exports via `reformlab.vintage`** — the notebook imports vintage types from `from reformlab.vintage import (...)` since these are domain-specific types that don't belong in the top-level convenience namespace alongside `run_scenario`. The top-level `reformlab.__init__` only needs to know about `VintageTransitionStep` for the `steps=` parameter type hint if desired, but the notebook will import directly from `reformlab.vintage`.

## Implementation Plan

### Tasks

- [x] Task 1: Create demo population CSV with vehicle_type attribute
  - File: `data/populations/demo-advanced-100.csv`
  - Action: Generate a CSV with 100 households and 4 columns: `household_id` (int, 0-99), `income` (float, 15k-95k EUR range), `carbon_emissions` (float, 2-12 tCO2/year correlated with income), `vehicle_type` (string: "diesel", "gasoline", "electric", "hybrid"). Use `generate_synthetic_population(size=100, seed=42)` to produce the first 3 columns, then add `vehicle_type` with income-correlated distribution: deciles 1-3 → 60% diesel, 25% gasoline, 10% hybrid, 5% electric; deciles 4-7 → 30% diesel, 35% gasoline, 20% hybrid, 15% electric; deciles 8-10 → 10% diesel, 20% gasoline, 25% hybrid, 45% electric. Use seed=42 for deterministic assignment.
  - Notes: Write a one-off Python script or notebook cell to generate this file and commit the output. The CSV must be human-inspectable. Sort by household_id.

- [x] Task 2: Add `steps` and `initial_state` parameters to `run_scenario()`
  - File: `src/reformlab/interfaces/api.py`
  - Action: Modify the `run_scenario()` signature from `run_scenario(config, adapter=None, *, skip_memory_check=False)` to `run_scenario(config, adapter=None, *, steps=None, initial_state=None, skip_memory_check=False)`. Type hints: `steps: tuple[PipelineStep, ...] | None = None`, `initial_state: dict[str, Any] | None = None`. Add `from reformlab.orchestrator.types import PipelineStep` to the `TYPE_CHECKING` block. Pass both parameters through to `_execute_orchestration()`.
  - File: `src/reformlab/interfaces/api.py` (function `_execute_orchestration`, line ~1190)
  - Action: Add `steps` and `initial_state` parameters to `_execute_orchestration()`. In the `OrchestratorRunner` construction (line ~1250), change `step_pipeline=(ComputationStep(...),)` to `step_pipeline=(ComputationStep(...),) + (steps or ())` and change `initial_state={}` to `initial_state=dict(initial_state or {})`.
  - Notes: The `steps` tuple is appended after `ComputationStep` so computation runs first, then vintage transition. This matches the orchestrator's sequential execution model where computation produces results that vintage can read. Backward compatible — `steps=None` and `initial_state=None` produce identical behavior to current code.

- [x] Task 3: Add `run_scenario()` with steps to tests
  - File: `tests/interfaces/test_api.py`
  - Action: Add a new test class `TestRunScenarioWithSteps` with:
    - `test_run_scenario_with_vintage_step` — configure a `VintageTransitionStep`, pass via `steps=(vintage_step,)`, verify `result.yearly_states[year].data["vintage_vehicle"]` contains a `VintageState` with expected cohorts.
    - `test_run_scenario_with_initial_state` — pass `initial_state={"vintage_vehicle": VintageState(...)}`, verify the initial state is carried into the first year's computation.
    - `test_run_scenario_without_steps_unchanged` — call `run_scenario()` without `steps` parameter, verify behavior is identical to current (no `vintage_vehicle` key in state data).
  - Notes: Use existing `MockAdapter`/`create_quickstart_adapter()` patterns from the file. Import vintage types from `reformlab.vintage`.

- [x] Task 4: Export vintage types from top-level `reformlab` package
  - File: `src/reformlab/__init__.py`
  - Action: Add import block for vintage types and add to `__all__`:
    ```python
    from reformlab.vintage import (
        VintageCohort,
        VintageConfig,
        VintageState,
        VintageSummary,
        VintageTransitionRule,
        VintageTransitionStep,
    )
    ```
    Add all 6 names to `__all__` under a `# Vintage types` comment section.
  - Notes: These are exported for notebook convenience. The notebook can import from either `reformlab` or `reformlab.vintage`.

- [x] Task 5: Rewrite advanced notebook — Section 1 (Multi-Year Simulation)
  - File: `notebooks/advanced.ipynb`
  - Action: Rewrite cells 0-11 (intro + Section 1):
    - Cell 0 (markdown): Update intro to mention real population data and real vintage tracking
    - Cell 2 (imports): Change to:
      ```python
      from reformlab import (
          RunConfig,
          ScenarioConfig,
          create_quickstart_adapter,
          run_scenario,
          show,
      )
      from reformlab.vintage import (
          VintageCohort,
          VintageConfig,
          VintageState,
          VintageSummary,
          VintageTransitionRule,
          VintageTransitionStep,
      )
      from pathlib import Path
      ```
    - Cell 4 (config): Keep same `multi_year_config` with rate_schedule 2025-2034. Add `population_path=Path("data/populations/demo-advanced-100.csv")` to `ScenarioConfig`.
    - Cell 5 (adapter): Keep `create_quickstart_adapter()` call but update comments to explain this is a mock adapter that processes the population CSV.
    - Cell 6 (run): Keep `run_scenario()` call as-is for Section 1 (no vintage step yet — that comes in Section 2).
    - Cells 7-11: Keep panel inspection and yearly progression plot logic. Update prose to reference the real CSV data.
  - Notes: Section 1 runs WITHOUT vintage to establish the baseline multi-year flow. Section 2 then adds vintage on top.

- [x] Task 6: Rewrite advanced notebook — Section 2 (Vintage Tracking) — the core change
  - File: `notebooks/advanced.ipynb`
  - Action: Replace cells 12-15 (currently fake vintage) with real vintage pipeline cells:
    - Cell 12 (markdown): Update Section 2 intro. Explain that `VintageTransitionStep` is a real orchestrator step that ages cohorts, retires old vehicles, and adds new fleet entries each year. Explain the step pipeline concept.
    - Cell 13 (code — configure vintage): Define `VintageConfig` and `VintageTransitionStep`:
      ```python
      # Configure the vintage transition step for the vehicle fleet
      vintage_config = VintageConfig(
          asset_class="vehicle",
          rules=(
              VintageTransitionRule(
                  rule_type="fixed_entry",
                  parameters={"count": 10},
                  description="10 new vehicles enter the fleet each year",
              ),
              VintageTransitionRule(
                  rule_type="max_age_retirement",
                  parameters={"max_age": 15},
                  description="Vehicles older than 15 years are retired",
              ),
          ),
          description="Vehicle fleet vintage tracking with fixed entry and retirement",
      )
      vintage_step = VintageTransitionStep(vintage_config)
      print(f"Step name: {vintage_step.name}")
      print(f"Asset class: {vintage_config.asset_class}")
      print(f"Rules: {len(vintage_config.rules)} configured")
      print(f"  Entry: {vintage_config.entry_rules[0].description}")
      print(f"  Retirement: {vintage_config.retirement_rules[0].description}")
      ```
    - Cell 13b (markdown): Explain what initial_state is — a pre-existing fleet composition at simulation start. Without it, the fleet starts empty and grows from zero.
    - Cell 14 (code — set initial state and run with vintage):
      ```python
      # Define the initial fleet composition (100 vehicles spread across ages 0-10)
      initial_fleet = VintageState(
          asset_class="vehicle",
          cohorts=tuple(
              VintageCohort(age=age, count=10 - age)
              for age in range(11)  # ages 0 through 10
          ),
      )
      print(f"Initial fleet: {initial_fleet.total_count} vehicles across {len(initial_fleet.cohorts)} cohorts")
      print(f"Age distribution: {initial_fleet.age_distribution}")

      # Re-run the multi-year simulation with the vintage step in the pipeline
      result_vintage = run_scenario(
          multi_year_config,
          adapter=adapter_multi,
          steps=(vintage_step,),
          initial_state={"vintage_vehicle": initial_fleet},
      )
      print(result_vintage)
      ```
    - Cell 15 (code — inspect vintage state year by year):
      ```python
      # Extract vintage state from each year and display summaries
      print("Vintage fleet evolution over 10 years:\n")
      print(f"{'Year':<8} {'Total':<8} {'Cohorts':<10} {'Mean Age':<10} {'Max Age':<10}")
      print("-" * 46)
      for year in sorted(result_vintage.yearly_states.keys()):
          vintage_state = result_vintage.yearly_states[year].data["vintage_vehicle"]
          summary = VintageSummary.from_state(vintage_state)
          print(f"{year:<8} {summary.total_count:<8} {summary.cohort_count:<10} {summary.mean_age:<10.1f} {summary.max_age:<10}")
      ```
    - Cell 16 (code — plot vintage evolution using real data):
      ```python
      import matplotlib.pyplot as plt
      from reformlab.visualization import create_figure

      # Extract age distribution per year for stacked area chart
      years = sorted(result_vintage.yearly_states.keys())
      # Group by age bracket: young (0-5), mid (6-10), old (11-15)
      young_counts = []
      mid_counts = []
      old_counts = []
      for year in years:
          vs = result_vintage.yearly_states[year].data["vintage_vehicle"]
          dist = vs.age_distribution
          young_counts.append(sum(dist.get(a, 0) for a in range(0, 6)))
          mid_counts.append(sum(dist.get(a, 0) for a in range(6, 11)))
          old_counts.append(sum(dist.get(a, 0) for a in range(11, 16)))

      fig, ax = create_figure(
          title="Vehicle Fleet Vintage Evolution (2025-2034)",
          xlabel="Year",
          ylabel="Number of Vehicles",
      )
      ax.stackplot(
          years, young_counts, mid_counts, old_counts,
          labels=["Young (0-5 years)", "Mid-age (6-10 years)", "Old (11-15 years)"],
          colors=["#2ca02c", "#ff7f0e", "#d62728"],
          alpha=0.8,
      )
      ax.legend(loc="upper left", fontsize=10)
      ax.set_xticks(years)
      plt.show()
      ```
    - Cell 17 (markdown): Explain what happened — the orchestrator ran `ComputationStep` then `VintageTransitionStep` for each year. Cohorts aged, old ones retired at 15, new ones entered at age 0. The fleet composition changed over time based on real rules, not hardcoded lists.
  - Notes: This is the most important section of the rewrite. Every number in the chart comes from the real `VintageTransitionStep` executing in the orchestrator loop.

- [x] Task 7: Rewrite advanced notebook — Section 3 (Baseline vs Reform Comparison)
  - File: `notebooks/advanced.ipynb`
  - Action: Rewrite cells 16-28 (Section 3):
    - Keep the baseline config (€44/tCO2 constant) and reform config (€50→€100/tCO2 escalating)
    - Both runs should use `population_path` pointing to the demo CSV
    - Both runs should include `steps=(vintage_step,)` and `initial_state={"vintage_vehicle": initial_fleet}` so vintage tracking runs in both scenarios
    - Keep the comparison API usage (`compare_scenarios`, `ComparisonConfig`, `ScenarioInput`)
    - Keep the `plot_comparison()` call
    - Replace the broken cell 26 (with `comp_table` bug) with a working version that uses `comparison.table` and properly imports `pyarrow.compute as pc`
    - Keep fiscal indicator comparison (cell 28) — fix any styling to use `create_figure()`
  - Notes: The key change is that both baseline and reform now run with real vintage tracking, so the comparison is between two scenarios that both have evolving fleet composition.

- [x] Task 8: Rewrite advanced notebook — Section 4 (Lineage and Reproducibility)
  - File: `notebooks/advanced.ipynb`
  - Action: Update cells 30-39 (Section 4):
    - Keep manifest inspection logic unchanged
    - Keep deterministic rerun verification — re-run reform scenario with same config, adapter, steps, and initial_state; verify outputs match
    - Update the rerun cell to include `steps=(vintage_step,)` and `initial_state={"vintage_vehicle": initial_fleet}` so the rerun is truly identical
    - Add a cell inspecting vintage state in the rerun to verify determinism extends to vintage cohort counts
    - Keep manifest JSON export
  - Notes: The lineage section now demonstrates that vintage state is also deterministic — same seed, same config, same cohort counts.

- [x] Task 9: Rewrite advanced notebook — Section 5 (Next Steps) and exports
  - File: `notebooks/advanced.ipynb`
  - Action: Update cells 40-45:
    - Keep export section (Story 6-5) functionality — export panel, fiscal indicators, comparison tables to Parquet
    - Update next steps prose to mention:
      - Behavioral response steps (vintage → computation feedback, Phase 2)
      - Additional asset classes (heating systems)
      - Custom orchestrator steps
      - Vintage-aware indicators
    - Keep the closing markdown
  - Notes: Minor prose updates only. Export code stays the same.

- [x] Task 10: Update notebook static tests
  - File: `tests/notebooks/test_advanced_notebook.py`
  - Action: Update assertions:
    - `test_advanced_notebook_uses_public_api_surfaces`: Add assertions for `from reformlab.vintage import (` in source. Keep existing assertions. Ensure `reformlab.computation` not in source still holds (vintage imports go through `reformlab.vintage`, not `reformlab.computation`).
    - `test_advanced_notebook_covers_multi_year_vintage_and_comparison_sections`: Replace `vintage_old = [50, 45, 40` and `vintage_new = [20, 25, 30` assertions with `VintageConfig(` and `VintageTransitionStep(` and `vintage_vehicle` and `VintageSummary.from_state(`. Keep `Section 2: Vintage Tracking` assertion.
    - `test_advanced_notebook_covers_reproducibility_and_lineage`: Add assertion for `steps=(vintage_step,)` in the rerun cell.
    - `test_advanced_notebook_uses_visualization_api`: Keep `plot_yearly(`, `plot_comparison(`, `create_figure(` assertions.
    - Keep all other tests unchanged (`test_advanced_notebook_exists`, `test_advanced_notebook_outputs_are_cleared`, `test_ci_executes_advanced_notebook_with_nbmake`, export tests).
  - Notes: The key assertion changes are in the vintage section test — from fake list assertions to real API usage assertions.

- [x] Task 11: Run tests and verify
  - Action: Run `uv run pytest tests/notebooks/test_advanced_notebook.py -v` and `uv run pytest tests/interfaces/test_api.py -v -k "steps"`. Run `uv run ruff check src/reformlab/interfaces/api.py src/reformlab/__init__.py` and `uv run mypy src/reformlab/interfaces/api.py src/reformlab/__init__.py`. Fix any issues.

## Acceptance Criteria

- [ ] AC 1: Given the file `data/populations/demo-advanced-100.csv`, when opened, then it contains exactly 100 rows (plus header) with columns `household_id`, `income`, `carbon_emissions`, `vehicle_type`, where `vehicle_type` values are only `"diesel"`, `"gasoline"`, `"electric"`, or `"hybrid"`.

- [ ] AC 2: Given a `VintageTransitionStep` and `run_scenario()` called with `steps=(vintage_step,)`, when the simulation completes, then `result.yearly_states[year].data["vintage_vehicle"]` contains a `VintageState` object for every year in the projection.

- [ ] AC 3: Given `run_scenario()` called with `initial_state={"vintage_vehicle": initial_fleet}` where `initial_fleet` has 55 total vehicles, when the simulation runs for year 2025, then the vintage state at year 2025 has the initial cohorts (aged +1) plus 10 new entries minus any retired above max_age=15.

- [ ] AC 4: Given `run_scenario()` called without `steps` or `initial_state` parameters, when the simulation completes, then behavior is identical to the current implementation (no `vintage_vehicle` key in `yearly_states[year].data`).

- [ ] AC 5: Given the advanced notebook Section 2, when all code cells are executed, then vintage state is extracted from `result_vintage.yearly_states` and displayed as a summary table with Year, Total, Cohorts, Mean Age, Max Age columns — all values computed from real `VintageTransitionStep` execution, not hardcoded lists.

- [ ] AC 6: Given the advanced notebook Section 2, when the stacked area chart is displayed, then the data comes from `result_vintage.yearly_states[year].data["vintage_vehicle"].age_distribution` for each year — not from Python list literals.

- [ ] AC 7: Given the advanced notebook Section 3, when baseline and reform scenarios are both run with `steps=(vintage_step,)` and compared, then both scenarios have vintage state in their yearly_states and the comparison table shows real distributional differences.

- [ ] AC 8: Given the advanced notebook Section 4, when the reform scenario is rerun with identical config (including `steps` and `initial_state`), then the vintage state at each year matches the original run exactly (deterministic vintage tracking).

- [ ] AC 9: Given the advanced notebook, when `from reformlab.vintage import (` appears in the source, then the static test `test_advanced_notebook_uses_public_api_surfaces` passes (no internal module imports).

- [ ] AC 10: Given the advanced notebook static tests, when `uv run pytest tests/notebooks/test_advanced_notebook.py -v` is run, then all tests pass with updated assertions that check for real vintage API usage (`VintageConfig(`, `VintageTransitionStep(`, `VintageSummary.from_state(`) instead of fake data lists.

- [ ] AC 11: Given the `run_scenario()` changes, when `uv run ruff check src/reformlab/interfaces/api.py` and `uv run mypy src/reformlab/interfaces/api.py` are run, then no errors or warnings are reported.

## Additional Context

### Dependencies

- **No new external dependencies** — `matplotlib>=3.8.0` and `pyarrow` are already in `pyproject.toml`
- **Inter-spec dependency**: This spec assumes the quickstart data flow rework spec (`quickstart-data-flow-rework`) has landed, making `MockAdapter` population-aware and `create_quickstart_adapter()` return a population-aware adapter. If it hasn't landed, the notebook can still work with the current `create_quickstart_adapter()` since it produces usable (if hardcoded) output — vintage tracking operates independently on `YearState.data`, not on computation results.
- **Visualization API spec**: The notebook uses `create_figure()`, `plot_yearly()`, `plot_comparison()` from the visualization spec (`visualization-api`). If that spec hasn't landed, the notebook falls back to inline matplotlib. The current notebook already uses these functions, so this is not a new dependency.

### Testing Strategy

- **Unit tests** (`tests/interfaces/test_api.py`): New test class `TestRunScenarioWithSteps` covering `steps` parameter, `initial_state` parameter, and backward compatibility. Uses existing `MockAdapter` and `VintageTransitionStep` with inline `VintageConfig`.
- **Notebook static tests** (`tests/notebooks/test_advanced_notebook.py`): Updated assertions checking for real vintage API usage in cell sources. No kernel execution — just string matching on cell content.
- **Notebook end-to-end** (CI): `uv run pytest --nbmake notebooks/advanced.ipynb -v` executes the notebook with a real kernel. This catches runtime errors, import failures, and API mismatches. Already configured in CI workflow.
- **Lint/type checks**: `ruff check` and `mypy` on modified source files.

### Notes

- **The `steps` parameter is a general-purpose extension point** — while this spec motivates it with vintage tracking, it enables any custom `OrchestratorStep` to be injected. Future notebooks could use it for `CarryForwardStep`, behavioral response steps, or custom user steps. The API change is permanent and broadly useful.
- **Vintage state doesn't affect computation results yet** — the notebook must explain this clearly to avoid user confusion. The carbon tax values in the panel output are identical with or without the vintage step. Vintage tracking demonstrates the orchestrator's step pipeline architecture and prepares the groundwork for Phase 2 behavioral response (where fleet composition influences emissions).
- **The demo CSV is deterministic** — generated from `seed=42` with a fixed vehicle_type assignment algorithm. Regenerating from the same seed produces the same file. This supports reproducibility testing.
- **Existing cell 26 bug** — the current notebook has a bug where `comp_table` is referenced but never defined, and `pc` (pyarrow.compute) is used but imported only in a later cell. This will be fixed in the rewrite as part of Task 7.
- **Follow-up work**: Once vintage-aware indicators exist (EPIC-4), the notebook should be updated to show how `VintageSummary` feeds into indicator computation. This is out of scope for this spec.
