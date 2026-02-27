# Story 6.2: Build Quickstart Notebook

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **first-time user (Alex persona) unfamiliar with microsimulation frameworks**,
I want **a quickstart notebook that runs cell-by-cell with pre-configured carbon tax scenarios on synthetic data**,
so that **I can see distributional charts in under 15 minutes and understand how to use ReformLab without prior setup or configuration**.

## Acceptance Criteria

From backlog (BKL-602), aligned with FR34 (quickstart in under 30 minutes) and NFR19 (examples run without modification).

1. **AC-1: Notebook runs without errors on fresh install**
   - Given a fresh install of the reformlab package (`pip install reformlab`), when the quickstart notebook is run cell-by-cell, then it completes without errors.
   - No external data downloads or API keys required.
   - Uses synthetic French household population bundled with the package or generated on-the-fly.

2. **AC-2: Notebook produces distributional charts**
   - Given the notebook execution, when the distributional analysis cells run, then income decile impact bar charts are displayed inline.
   - Charts show tax burden and redistribution effects by income decile.
   - Visual output uses matplotlib (standard Jupyter rendering).

3. **AC-3: Notebook demonstrates parameter modification and rerun**
   - Given the notebook, when the user modifies a carbon tax rate from €44/tCO2 to €100/tCO2 and re-runs, then updated charts reflect the higher rate impact.
   - The notebook includes commented guidance explaining what to modify.

4. **AC-4: Notebook demonstrates scenario comparison**
   - Given the notebook, when the user runs baseline vs. reform comparison cells, then side-by-side or overlaid comparison charts are displayed.
   - At least two redistribution variants are compared (e.g., flat dividend vs. progressive rebate).

5. **AC-5: Total execution time under 30 minutes**
   - Given a user reading instructions and running cells sequentially, when timed end-to-end, then total execution is under 30 minutes including reading.
   - Target: under 15 minutes for pure execution (excluding reading).
   - Computation cells complete in seconds, not minutes.

6. **AC-6: Notebook includes methodology documentation**
   - Given the notebook, when a user inspects markdown cells, then each major section explains: what data is used, what policy is being simulated, and how to interpret results.
   - Run manifest and assumption transparency are demonstrated.

7. **AC-7: Notebook tested in CI**
   - Given the CI pipeline, when tests run, then the quickstart notebook executes successfully via `pytest --nbmake` or equivalent.
   - Notebook cell outputs are cleared before commit (executed in CI, not pre-rendered).

## Dependencies

- **Story 6-1 (BKL-601): Implement stable Python API** — DONE
  - Provides `run_scenario()`, `SimulationResult`, `ScenarioConfig`, `RunConfig`
  - Provides `SimulationResult.indicators()` for distributional analysis

- **Story 2-2 (BKL-202): Carbon-tax template pack** — DONE
  - Provides carbon tax scenario templates

- **Story 4-1 (BKL-401): Distributional indicators** — DONE
  - Provides `compute_distributional_indicators()` for decile analysis

- **Story 4-5 (BKL-405): Scenario comparison tables** — DONE
  - Provides comparison output generation

- **Follow-on stories:**
  - Story 6-3 (BKL-603): Advanced notebook (multi-year, vintage, comparison)
  - Story 6-5 (BKL-605): Export actions (CSV/Parquet from notebook)

## Tasks / Subtasks

- [ ] Task 0: Review existing patterns and prepare test data (AC: dependency check)
  - [ ] 0.1 Review `src/reformlab/interfaces/api.py` for API usage patterns
  - [ ] 0.2 Review `src/reformlab/templates/carbon_tax/` for available templates and parameters
  - [ ] 0.3 Review `src/reformlab/indicators/distributional.py` for indicator API
  - [ ] 0.4 Review `tests/` for MockAdapter usage patterns
  - [ ] 0.5 Identify or create synthetic population fixture data

- [ ] Task 1: Create notebook directory structure (AC: #7)
  - [ ] 1.1 Create `notebooks/` directory at project root (if not exists)
  - [ ] 1.2 Create `notebooks/quickstart.ipynb` as main deliverable
  - [ ] 1.3 Create `notebooks/data/` for any embedded sample data
  - [ ] 1.4 Add `notebooks/` to pytest collection with nbmake

- [ ] Task 2: Build Section 1 - Introduction and Setup (AC: #1, #6)
  - [ ] 2.1 Markdown cell: Title, overview, what user will learn
  - [ ] 2.2 Code cell: Import statements (`from reformlab import ...`)
  - [ ] 2.3 Code cell: Verify installation (`reformlab.__version__`)
  - [ ] 2.4 Markdown cell: Explain OpenFisca-first approach and synthetic data

- [ ] Task 3: Build Section 2 - First Simulation Run (AC: #1, #2, #5)
  - [ ] 3.1 Markdown cell: Explain what we're about to run
  - [ ] 3.2 Code cell: Define basic carbon tax ScenarioConfig
      ```python
      config = ScenarioConfig(
          template_name="carbon-tax",
          parameters={"rate_schedule": {2025: 44.0}},  # €44/tCO2
          start_year=2025,
          end_year=2025,
      )
      ```
  - [ ] 3.3 Code cell: Run simulation with MockAdapter for reproducible demo
  - [ ] 3.4 Code cell: Display SimulationResult (shows __repr__)
  - [ ] 3.5 Code cell: Access panel output and show shape
  - [ ] 3.6 Markdown cell: Explain what we just computed

- [ ] Task 4: Build Section 3 - Distributional Analysis (AC: #2, #6)
  - [ ] 4.1 Markdown cell: Explain distributional indicators
  - [ ] 4.2 Code cell: Compute distributional indicators
      ```python
      indicators = result.indicators("distributional")
      ```
  - [ ] 4.3 Code cell: Create income decile bar chart with matplotlib
  - [ ] 4.4 Markdown cell: Interpret the chart (who pays more, who benefits)
  - [ ] 4.5 Code cell: Show winners/losers summary if available

- [ ] Task 5: Build Section 4 - Parameter Modification (AC: #3)
  - [ ] 5.1 Markdown cell: "Try it yourself" - modify the tax rate
  - [ ] 5.2 Code cell: Higher tax rate scenario (€100/tCO2)
  - [ ] 5.3 Code cell: Re-run simulation
  - [ ] 5.4 Code cell: New distributional chart
  - [ ] 5.5 Markdown cell: Compare results and explain impact

- [ ] Task 6: Build Section 5 - Scenario Comparison (AC: #4)
  - [ ] 6.1 Markdown cell: Explain baseline vs. reform comparison
  - [ ] 6.2 Code cell: Define baseline scenario (no carbon tax or lower rate)
  - [ ] 6.3 Code cell: Define reform scenario (with carbon tax + redistribution)
  - [ ] 6.4 Code cell: Run both scenarios
  - [ ] 6.5 Code cell: Side-by-side comparison chart
  - [ ] 6.6 Code cell: Comparison of two redistribution variants (flat vs. progressive)
  - [ ] 6.7 Markdown cell: Interpret comparison results

- [ ] Task 7: Build Section 6 - Run Manifest and Reproducibility (AC: #6)
  - [ ] 7.1 Markdown cell: Explain run manifest and assumption transparency
  - [ ] 7.2 Code cell: Access and display manifest
      ```python
      result.manifest
      ```
  - [ ] 7.3 Code cell: Show key manifest fields (parameters, seeds, versions)
  - [ ] 7.4 Markdown cell: Explain reproducibility guarantee

- [ ] Task 8: Build Section 7 - Next Steps (AC: #6)
  - [ ] 8.1 Markdown cell: Summary of what was learned
  - [ ] 8.2 Markdown cell: Links to advanced notebook (Story 6-3)
  - [ ] 8.3 Markdown cell: Links to API documentation
  - [ ] 8.4 Markdown cell: Links to YAML workflow configuration

- [ ] Task 9: Create test fixtures and mock data (AC: #1, #7)
  - [ ] 9.1 Create synthetic population generator or fixture for notebook
  - [ ] 9.2 Ensure MockAdapter works correctly for notebook demos
  - [ ] 9.3 Verify notebook can run in CI without real OpenFisca

- [ ] Task 10: Add CI integration for notebook testing (AC: #7)
  - [ ] 10.1 Install nbmake or pytest-notebook in dev dependencies
  - [ ] 10.2 Add `notebooks/` to pytest configuration
  - [ ] 10.3 Create CI job or step to run notebook tests
  - [ ] 10.4 Clear notebook outputs before commit (add pre-commit hook or CI check)

- [ ] Task 11: Final validation (AC: #1-7)
  - [ ] 11.1 Run notebook fresh from `pip install -e .`
  - [ ] 11.2 Time full execution (target: <15 min)
  - [ ] 11.3 Verify all charts render correctly
  - [ ] 11.4 Run `ruff check notebooks/` (if .py cells extracted)
  - [ ] 11.5 Run notebook via pytest nbmake
  - [ ] 11.6 Verify notebook documentation is clear for new users

## Dev Notes

### Architecture Compliance

This story implements **FR34** (quickstart in under 30 minutes) and **NFR19** (examples run without modification) from the PRD.

**Key architectural constraints:**

- **API facade only** - Notebook uses public API (`run_scenario`, `SimulationResult.indicators`) - no direct subsystem imports. [Source: architecture.md#Layered-Architecture]
- **MockAdapter for demos** - Use `MockAdapter` from `computation/mock_adapter.py` to ensure reproducible, fast execution without real OpenFisca dependency. [Source: architecture.md#Computation-Adapter-Pattern]
- **PyArrow-first** - Panel output is PyArrow (`pa.Table`), convert to pandas only for plotting. [Source: project-context.md#Critical-Implementation-Rules]
- **Matplotlib for plotting** - Standard Jupyter visualization, no additional dependencies. [Source: prd.md#Developer-Tool-Specific-Requirements]

### User Journey Alignment

This notebook supports the **Alex (First-Time Installer)** journey from the PRD:

> Alex finds the PyPI page after a quick search. He's skeptical — he's tried OpenFisca before and gave up after two hours of configuration. He has 30 minutes before his next seminar.
>
> `pip install reformlab` works cleanly. He opens the quickstart notebook linked in the README. The first cell loads a pre-configured carbon tax scenario on synthetic French households. He runs it — distributional charts by income decile appear in seconds.

**Target emotional state:** Surprise → "I clicked Run and got distributional charts from the default template in minutes"

### Existing Code to Reuse

**From `interfaces/api.py` (Story 6-1):**
```python
from reformlab import run_scenario, RunConfig, ScenarioConfig, SimulationResult

# Basic usage pattern
config = ScenarioConfig(
    template_name="carbon-tax",
    parameters={"rate_schedule": {2025: 50.0}},
    start_year=2025,
    end_year=2030,
)
result = run_scenario(RunConfig(scenario=config))
print(result)  # SimulationResult(SUCCESS, scenario='carbon-tax', years=2025-2030, ...)

# Indicator access
indicators = result.indicators("distributional")
```

**From `computation/mock_adapter.py`:**
```python
from reformlab.computation.mock_adapter import MockAdapter

# Use MockAdapter for reproducible notebook execution
adapter = MockAdapter(seed=42)
result = run_scenario(config, adapter=adapter)
```

**From `indicators/distributional.py`:**
```python
# Indicators returned from result.indicators("distributional")
# IndicatorResult with by_decile data
```

### Notebook Structure

```
notebooks/
├── quickstart.ipynb          # Main deliverable
├── data/
│   └── synthetic_population_sample.parquet  # Optional: small sample data
└── README.md                 # Brief index of notebooks
```

**Notebook sections:**

1. **Introduction** (~2 min read)
   - What is ReformLab
   - What you'll learn
   - Prerequisites (just `pip install reformlab`)

2. **First Run** (~3 min)
   - Import and verify installation
   - Define carbon tax scenario
   - Run simulation
   - View results

3. **Distributional Analysis** (~5 min)
   - Compute indicators
   - Plot income decile chart
   - Interpret results

4. **Parameter Modification** (~3 min)
   - Modify tax rate
   - Re-run and compare

5. **Scenario Comparison** (~5 min)
   - Baseline vs. reform
   - Two redistribution variants
   - Comparison charts

6. **Reproducibility** (~2 min)
   - View run manifest
   - Understand assumption tracking

7. **Next Steps** (~1 min)
   - Links to advanced notebook
   - API documentation

**Total: ~20 minutes** (reading + execution)

### Plotting Pattern

```python
import matplotlib.pyplot as plt

def plot_decile_impact(indicators, title="Carbon Tax Impact by Income Decile"):
    """Plot distributional impact by income decile."""
    deciles = indicators.by_decile

    fig, ax = plt.subplots(figsize=(10, 6))

    x = range(1, 11)
    ax.bar(x, deciles["net_impact"], color="steelblue")

    ax.set_xlabel("Income Decile")
    ax.set_ylabel("Net Impact (€/year)")
    ax.set_title(title)
    ax.set_xticks(x)
    ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)

    plt.tight_layout()
    plt.show()
```

### CI Integration Pattern

**pyproject.toml addition:**
```toml
[project.optional-dependencies]
dev = [
    # ... existing dev deps
    "nbmake>=1.4",
]

[tool.pytest.ini_options]
testpaths = ["tests", "notebooks"]
```

**pytest command:**
```bash
pytest --nbmake notebooks/quickstart.ipynb -v
```

### Scope Guardrails

**In scope:**
- `notebooks/quickstart.ipynb` with 7 sections
- Synthetic population data or MockAdapter-based execution
- matplotlib charts for distributional analysis
- Basic scenario comparison (baseline vs. reform)
- Run manifest display
- CI testing with nbmake

**Out of scope:**
- Multi-year projections with vintage tracking (Story 6-3)
- Advanced comparison workflows (Story 6-3)
- CSV/Parquet export demos (Story 6-5)
- Interactive widgets or dashboards
- Custom template creation tutorial
- YAML configuration deep-dive (separate tutorial)

### Testing Standards

- Notebook executes via `pytest --nbmake notebooks/quickstart.ipynb`
- All cells must complete without error
- Charts must render (matplotlib inline)
- Outputs cleared before commit (CI renders fresh)
- No hardcoded file paths outside notebook directory
- Use `tmp_path` equivalent or MockAdapter for data

### Previous Story Intelligence

**From Story 6-1 (Python API):**
- `SimulationResult.__repr__()` provides notebook-friendly display
- `result.indicators("distributional")` returns `IndicatorResult`
- MockAdapter can be injected via `run_scenario(config, adapter=adapter)`
- Error messages are user-friendly (`ConfigurationError`, `SimulationError`)

**From EPIC-2 (Templates):**
- Carbon tax templates available: `"carbon-tax"` template name
- Parameters include `rate_schedule` (year -> rate mapping)

**From EPIC-4 (Indicators):**
- `compute_distributional_indicators()` returns decile-level data
- Indicator results include `by_decile` with income group breakdown

### References

- [Source: prd.md#User-Journeys] - Alex (First-Time Installer) journey
- [Source: prd.md#Functional-Requirements] - FR34 quickstart in under 30 minutes
- [Source: prd.md#Non-Functional-Requirements] - NFR19 examples run without modification
- [Source: backlog BKL-602] - Story acceptance criteria
- [Source: architecture.md#Computation-Adapter-Pattern] - MockAdapter for testing
- [Source: ux-design-specification.md#Journey-2-First-Run-Onboarding] - Onboarding UX patterns
- [Source: interfaces/api.py] - Python API usage patterns

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
