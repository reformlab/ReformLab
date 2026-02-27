# Story 6.3: Build Advanced Notebook

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **researcher (Marco persona) working with multi-year projections and scenario comparisons**,
I want **an advanced notebook demonstrating multi-year runs with vintage tracking and baseline/reform comparison**,
so that **I can understand how to use ReformLab's full dynamic orchestration capabilities and produce reproducible research-grade analysis**.

## Acceptance Criteria

From backlog (BKL-603), aligned with FR30 (Python API workflows), FR35 (template authoring and dynamic-run documentation).

1. **AC-1: Notebook demonstrates multi-year simulation**
   - Given the notebook execution, when the multi-year simulation cells run, then a projection with `end_year - start_year + 1 >= 10` completes successfully.
   - The notebook outputs a year-indexed panel containing every year in the configured horizon.
   - The notebook uses only public API imports from `reformlab` for scenario execution (`run_scenario`, `RunConfig`, `ScenarioConfig`), matching quickstart patterns.

2. **AC-2: Notebook demonstrates vintage tracking**
   - Given the notebook, when vintage tracking cells run, then vintage/cohort state changes are visible year-over-year.
   - At least one asset class (vehicle or heating) demonstrates vintage transitions.
   - Vintage composition is displayed per year in panel/derived tables or charts, and at least one cohort value changes between consecutive years.

3. **AC-3: Notebook demonstrates baseline/reform comparison**
   - Given the notebook, when baseline and reform scenarios are run, then side-by-side or overlaid comparison outputs are displayed.
   - Comparison output includes per-household (or decile-level) per-year differences.
   - At least distributional and one additional indicator type (welfare, fiscal) are compared.

4. **AC-4: Notebook runs without errors in CI**
   - Given the CI pipeline, when tests run, then the advanced notebook executes successfully via `pytest --nbmake` or equivalent.
   - Notebook cell outputs are cleared before commit and executed fresh in CI.
   - No external data downloads or API keys required.

5. **AC-5: Notebook includes research-grade reproducibility features**
   - Given the notebook, when a user inspects reproducibility cells, then run manifest with full lineage is displayed.
   - The notebook demonstrates deterministic reruns with fixed seed/config and verifies matching outputs (exact match or documented tolerance).
   - Cross-scenario lineage relationships are visible for baseline and reform runs.

6. **AC-6: Notebook builds on quickstart knowledge**
   - Given a user who completed the quickstart notebook (Story 6-2), when they open the advanced notebook, then the first execution cells reuse the same API patterns and extend them incrementally.
   - The notebook references quickstart concepts and introduces advanced features incrementally.

## Dependencies

Dependency gate: if any hard dependency below is not `done`, set this story to `blocked` and do not start implementation.

- **Hard dependency (backlog-declared): Story 6-1 (BKL-601) — DONE**
  - Provides `run_scenario()`, `SimulationResult`, `ScenarioConfig`, `RunConfig`
  - Provides `SimulationResult.indicators()` for indicator access

- **Hard dependency (backlog-declared): Story 6-2 (BKL-602) — DONE**
  - Quickstart notebook patterns and API usage established
  - User journey baseline for advanced notebook

- **Supporting completed stories (required for full functionality):**
  - Story 3-1 (BKL-301): Yearly loop orchestrator — DONE
    - Provides multi-year execution capability
  - Story 3-4 (BKL-304): Vintage transition step — DONE
    - Provides vintage tracking for asset classes
  - Story 3-7 (BKL-307): Scenario-year panel output — DONE
    - Provides year-by-year panel results
  - Story 4-1 (BKL-401): Distributional indicators — DONE
  - Story 4-3 (BKL-403): Welfare indicators — DONE
  - Story 4-4 (BKL-404): Fiscal indicators — DONE
  - Story 4-5 (BKL-405): Scenario comparison tables — DONE
  - Story 5-1 (BKL-501): Run manifest schema — DONE
  - Story 5-3 (BKL-503): Run lineage graph — DONE

- **Follow-on stories:**
  - Story 6-5 (BKL-605): Export actions (CSV/Parquet from notebook)

## Tasks / Subtasks

- [ ] Task 0: Confirm blockers and architecture guardrails (AC: dependency check)
  - [ ] 0.1 Confirm Story 6-1 and 6-2 are `done` in `sprint-status.yaml`
  - [ ] 0.2 Confirm supporting EPIC-3, EPIC-4, EPIC-5 stories are `done`
  - [ ] 0.3 Review quickstart notebook structure for API pattern consistency
  - [ ] 0.4 If any dependency is not `done`, mark story `blocked` and stop implementation

- [ ] Task 1: Create advanced notebook scaffold (AC: #1, #6)
  - [ ] 1.1 Create `notebooks/advanced.ipynb` as the primary deliverable
  - [ ] 1.2 Add markdown sections for introduction, multi-year runs, vintage tracking, comparison, lineage, and reproducibility
  - [ ] 1.3 Include explicit reference to quickstart as prerequisite
  - [ ] 1.4 Use consistent API import patterns from quickstart
  - [ ] 1.5 Enforce architecture boundary: no direct `openfisca` or internal subsystem imports for scenario execution

- [ ] Task 2: Implement multi-year simulation section (AC: #1)
  - [ ] 2.1 Define scenario with 10-year horizon (`start_year=2025`, `end_year=2034`)
  - [ ] 2.2 Run multi-year simulation using public API
  - [ ] 2.3 Display year-by-year panel output with clear structure
  - [ ] 2.4 Show yearly progression of key indicators
  - [ ] 2.5 Explain dynamic orchestrator concepts in markdown

- [ ] Task 3: Implement vintage tracking section (AC: #2)
  - [ ] 3.1 Configure vintage tracking for at least one asset class (vehicle or heating)
  - [ ] 3.2 Run simulation with vintage transitions enabled
  - [ ] 3.3 Display vintage composition changes year-over-year
  - [ ] 3.4 Visualize cohort aging and new vintage additions
  - [ ] 3.5 Explain vintage concepts and state transitions in markdown

- [ ] Task 4: Implement baseline/reform comparison section (AC: #3)
  - [ ] 4.1 Define baseline scenario (e.g., current carbon tax policy)
  - [ ] 4.2 Define reform scenario (e.g., higher carbon tax with progressive rebate)
  - [ ] 4.3 Run both scenarios with multi-year projection
  - [ ] 4.4 Generate side-by-side comparison output
  - [ ] 4.5 Display per-household per-year differences
  - [ ] 4.6 Compare distributional, welfare, and fiscal indicators
  - [ ] 4.7 Create comparison visualization (overlaid charts or tables)

- [ ] Task 5: Implement lineage and reproducibility section (AC: #5)
  - [ ] 5.1 Display full run manifest for a completed scenario
  - [ ] 5.2 Show run lineage graph (parent scenario -> yearly child runs)
  - [ ] 5.3 Demonstrate cross-scenario lineage relationships
  - [ ] 5.4 Show how to verify deterministic rerun (fixed seed/config -> matching outputs or documented tolerance)
  - [ ] 5.5 Explain reproducibility concepts and manifest fields

- [ ] Task 6: Add CI notebook execution coverage (AC: #4)
  - [ ] 6.1 Ensure pytest/CI executes `notebooks/advanced.ipynb`
  - [ ] 6.2 Ensure committed notebook has cleared outputs
  - [ ] 6.3 Verify notebook completes within CI timeout

- [ ] Task 7: Final validation against acceptance criteria (AC: #1-6)
  - [ ] 7.1 Run notebook from a clean environment install path
  - [ ] 7.2 Verify all cells execute without error
  - [ ] 7.3 Verify vintage tracking shows visible state changes
  - [ ] 7.4 Verify comparison outputs show expected per-year deltas for baseline vs reform
  - [ ] 7.5 Run notebook test in CI-equivalent command
  - [ ] 7.6 Verify architecture guardrails: API facade-only usage and no direct adapter/backend calls in notebook

## Dev Notes

### Architecture Compliance

This story implements **FR30** (full run workflows from Python API), **FR35** (dynamic-run documentation with reproducible examples), and supports user journey **Journey 3: Marco (Academic Researcher)** from the PRD.

**Key architectural constraints:**

- **API facade only** - Notebook uses public API (`run_scenario`, `RunConfig`, `ScenarioConfig`, `SimulationResult`) and avoids direct subsystem imports. [Source: architecture.md#Layered-Architecture]
- **Adapter boundary respected** - Notebook remains adapter-agnostic; adapter injection stays in tests. [Source: architecture.md#Computation-Adapter-Pattern]
- **Orchestrator visibility** - Notebook demonstrates multi-year loop with step pipeline concepts. [Source: architecture.md#Step-Pluggable-Dynamic-Orchestrator]
- **Governance visibility** - Notebook surfaces run manifest, lineage, and reproducibility features. [Source: architecture.md#Reproducibility-&-Governance]
- **Matplotlib for plotting** - Keep visualization dependency lightweight and notebook-native.

### User Journey Alignment

This notebook supports the **Marco (Academic Researcher)** journey from the PRD:

> Marco opens a Jupyter notebook with the ReformLab carbon tax template. He loads the built-in synthetic French population, defines his carbon tax reform in YAML, and — crucially — his elasticities aren't needed for the MVP (behavioral responses are Phase 2). But the static simulation already gives him the mechanical distributional impact. He runs the simulation and gets distributional charts with deterministic run manifests for reproducibility.
>
> Marco shares the YAML configuration, notebook, and run manifest with his co-author. The co-author reruns the analysis in a clean environment and gets matching outputs because assumptions, parameters, and engine context are pinned.

**Target emotional state:** Trust → "I can click any number and trace it back to source assumptions"

### Existing Code to Reuse

**From `interfaces/api.py` (Story 6-1):**
```python
from reformlab import run_scenario, RunConfig, ScenarioConfig, SimulationResult

# Multi-year configuration
config = ScenarioConfig(
    template_name="carbon-tax",
    parameters={"rate_schedule": {2025: 50.0, 2030: 100.0}},
    start_year=2025,
    end_year=2034,
)
result = run_scenario(RunConfig(scenario=config))
```

**From `orchestrator/` (EPIC-3):**
```python
# Year-by-year panel access
panel = result.panel  # DataFrame with household x year structure

# Yearly results iteration
for year, yearly_result in result.by_year.items():
    print(f"Year {year}: {yearly_result}")
```

**From `vintage/` (Story 3-4):**
```python
# Vintage configuration in scenario
config = ScenarioConfig(
    template_name="carbon-tax",
    parameters={...},
    vintage_config={
        "vehicle_fleet": {
            "enabled": True,
            "transition_rules": {...}
        }
    },
    start_year=2025,
    end_year=2034,
)
```

**From `indicators/comparison.py` (Story 4-5):**
```python
# Scenario comparison
from reformlab import compare_scenarios

comparison = compare_scenarios(baseline_result, reform_result)
comparison.to_table()  # Side-by-side indicator table
comparison.to_chart()  # Overlaid visualization
```

**From `governance/lineage.py` (Story 5-3):**
```python
# Run lineage access
lineage = result.lineage
lineage.parent_manifest  # Parent scenario manifest
lineage.yearly_manifests  # Dict[int, Manifest] for each year
lineage.graph()  # DAG visualization
```

### Notebook Structure

```
notebooks/
├── quickstart.ipynb          # Prerequisites - Story 6-2
├── advanced.ipynb            # Main deliverable - Story 6-3
├── data/
│   └── synthetic_population_sample.parquet
└── README.md
```

**Notebook sections:**

1. **Introduction** (~3 min read)
   - Prerequisites (quickstart completion)
   - What you'll learn: multi-year, vintage, comparison, lineage
   - ReformLab's dynamic orchestration architecture overview

2. **Multi-Year Simulation** (~8 min)
   - Configure 10-year projection
   - Run multi-year scenario
   - View year-by-year panel output
   - Visualize yearly indicator progression
   - Understand orchestrator step pipeline

3. **Vintage Tracking** (~10 min)
   - Explain vintage/cohort concepts
   - Configure vehicle fleet vintage tracking
   - Run simulation with vintage transitions
   - Visualize cohort aging over 10 years
   - Show fleet composition evolution

4. **Baseline/Reform Comparison** (~10 min)
   - Define baseline (current policy)
   - Define reform (higher tax + rebate)
   - Run both with multi-year projection
   - Side-by-side comparison table
   - Per-household per-year differences
   - Distributional + welfare + fiscal comparison
   - Overlaid visualization

5. **Lineage and Reproducibility** (~8 min)
   - View full run manifest
   - Navigate lineage graph
   - Cross-scenario relationships
   - Verify deterministic rerun
   - Export manifest for sharing

6. **Next Steps** (~2 min)
   - Advanced parameter sweeps (future)
   - Custom indicator formulas
   - API documentation links
   - Community resources

**Total: ~40 minutes** (reading + execution)

### Plotting Patterns

```python
import matplotlib.pyplot as plt

def plot_yearly_progression(result, indicator_name="gini"):
    """Plot indicator progression over multi-year run."""
    years = sorted(result.by_year.keys())
    values = [result.by_year[y].indicators(indicator_name).value for y in years]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(years, values, marker='o', linewidth=2, color='steelblue')

    ax.set_xlabel("Year")
    ax.set_ylabel(indicator_name.title())
    ax.set_title(f"{indicator_name.title()} Progression (10-Year Projection)")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()

def plot_vintage_composition(result, asset_class="vehicle_fleet"):
    """Plot vintage composition evolution."""
    years = sorted(result.by_year.keys())
    vintages = result.vintage_state[asset_class]

    # Stacked area chart of vintage cohorts
    fig, ax = plt.subplots(figsize=(12, 6))
    # ... vintage visualization logic
    plt.show()

def plot_comparison(baseline_result, reform_result, indicator="net_impact"):
    """Plot baseline vs reform comparison."""
    fig, ax = plt.subplots(figsize=(10, 6))

    deciles = range(1, 11)
    baseline_values = baseline_result.indicators("distributional").by_decile[indicator]
    reform_values = reform_result.indicators("distributional").by_decile[indicator]

    x = np.arange(len(deciles))
    width = 0.35

    ax.bar(x - width/2, baseline_values, width, label='Baseline', color='gray')
    ax.bar(x + width/2, reform_values, width, label='Reform', color='steelblue')

    ax.set_xlabel("Income Decile")
    ax.set_ylabel(f"{indicator.replace('_', ' ').title()} (€/year)")
    ax.set_title("Baseline vs Reform: Distributional Impact")
    ax.set_xticks(x)
    ax.set_xticklabels(deciles)
    ax.legend()
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

    plt.tight_layout()
    plt.show()
```

### Scope Guardrails

**In scope:**
- `notebooks/advanced.ipynb` with 6 sections
- Multi-year projection (10-year horizon) using public API
- Vintage tracking demonstration (vehicle or heating)
- Baseline/reform comparison with multiple indicator types
- Run lineage and manifest display
- Reproducibility verification demonstration
- CI testing with nbmake
- matplotlib charts for visualization

**Out of scope:**
- Behavioral response modeling (Phase 2)
- Automated sensitivity sweeps (Phase 2)
- Replication package export (Phase 2)
- Custom template creation tutorial
- Interactive widgets or dashboards
- CSV/Parquet export demos (Story 6-5)
- GUI integration patterns

### Testing Standards

- Notebook executes via `pytest --nbmake notebooks/advanced.ipynb`
- All cells must complete without error
- Multi-year run must complete within reasonable CI timeout (~2 min)
- Charts must render (matplotlib inline)
- Outputs cleared before commit (CI renders fresh)
- No hardcoded file paths outside notebook directory
- Notebook uses public API imports only

### Previous Story Intelligence

**From Story 6-2 (Quickstart Notebook):**
- API import patterns established: `from reformlab import run_scenario, RunConfig, ScenarioConfig`
- Single-year flow demonstrated; advanced builds on this
- matplotlib plotting patterns for distributional charts
- Run manifest display pattern with `result.manifest`
- CI integration with nbmake established

**From EPIC-3 (Dynamic Orchestrator):**
- Multi-year execution via `start_year`, `end_year` in `ScenarioConfig`
- Panel output available via `result.panel`
- Year-by-year iteration via `result.by_year`
- Vintage state tracking in `result.vintage_state`

**From EPIC-4 (Indicators):**
- Multiple indicator types: distributional, welfare, fiscal
- Comparison via `compare_scenarios()` or direct API

**From EPIC-5 (Governance):**
- Run manifest access via `result.manifest`
- Lineage graph via `result.lineage`
- Reproducibility check via `governance.verify_rerun()`

### References

- [Source: prd.md#User-Journeys] - Marco (Academic Researcher) journey
- [Source: prd.md#Functional-Requirements] - FR30, FR35
- [Source: backlog BKL-603] - Story acceptance criteria
- [Source: architecture.md#Step-Pluggable-Dynamic-Orchestrator] - Dynamic orchestration
- [Source: architecture.md#Reproducibility-&-Governance] - Lineage and manifests
- [Source: ux-design-specification.md#Journey-4-Assumption-Inspection] - Lineage drill-down patterns
- [Source: interfaces/api.py] - Python API usage patterns
- [Source: orchestrator/] - Multi-year execution
- [Source: vintage/] - Vintage tracking
- [Source: governance/lineage.py] - Run lineage

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
