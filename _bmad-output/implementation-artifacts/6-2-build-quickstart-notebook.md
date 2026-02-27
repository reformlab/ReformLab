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
   - Given a fresh install of the reformlab package (`pip install reformlab`), when the quickstart notebook is run cell-by-cell from a clean kernel, then it completes without errors.
   - No external data downloads or API keys required.
   - Uses synthetic data bundled with the package or generated in-notebook.

2. **AC-2: Notebook produces distributional charts**
   - Given the notebook execution, when the distributional analysis cells run, then income decile impact bar charts are displayed inline.
   - Charts show baseline/reform net impact by income decile.
   - Visual output uses matplotlib (standard Jupyter rendering).

3. **AC-3: Notebook demonstrates parameter modification and rerun**
   - Given the notebook, when the user modifies a carbon tax rate from €44/tCO2 to €100/tCO2 and re-runs, then updated charts reflect the higher rate impact.
   - The notebook includes explicit "Try it yourself" guidance on what value to change.

4. **AC-4: Notebook demonstrates basic scenario comparison**
   - Given the notebook, when the user runs baseline vs. reform comparison cells, then a side-by-side or overlaid comparison view is displayed.
   - Comparison scope is single-year quickstart only (multi-year/vintage comparison stays in Story 6-3).

5. **AC-5: Total execution time under 30 minutes**
   - Given a user reading instructions and running cells sequentially, when timed end-to-end, then total execution is under 30 minutes including reading.
   - Target: under 15 minutes for pure execution (excluding reading).
   - Computation cells complete in seconds, not minutes.

6. **AC-6: Notebook includes brief methodology and reproducibility context**
   - Given the notebook, when a user inspects markdown cells, then each major section explains data source, policy setup, and chart interpretation.
   - At least one cell displays run manifest metadata for transparency.

7. **AC-7: Notebook tested in CI**
   - Given the CI pipeline, when tests run, then the quickstart notebook executes successfully via `pytest --nbmake` or equivalent.
   - Notebook cell outputs are cleared before commit (executed in CI, not pre-rendered).

## Dependencies

- **Hard dependency (backlog-declared): Story 6-1 (BKL-601) — DONE**
  - Provides `run_scenario()`, `SimulationResult`, `ScenarioConfig`, `RunConfig`
  - Provides `SimulationResult.indicators()` for distributional analysis

- **Supporting completed stories (required for full quickstart value):**
  - Story 2-2 (BKL-202): Carbon-tax template pack — DONE
  - Provides carbon tax scenario templates
  - Story 4-1 (BKL-401): Distributional indicators — DONE
  - Provides `compute_distributional_indicators()` for decile analysis
  - Story 4-5 (BKL-405): Scenario comparison tables — DONE
  - Provides comparison output generation

- **Follow-on stories:**
  - Story 6-3 (BKL-603): Advanced notebook (multi-year, vintage, comparison)
  - Story 6-5 (BKL-605): Export actions (CSV/Parquet from notebook)

## Tasks / Subtasks

- [ ] Task 0: Confirm blockers and architecture guardrails (AC: dependency check)
  - [ ] 0.1 Confirm backlog blocker `BKL-601` is `done` in `sprint-status.yaml`
  - [ ] 0.2 Confirm supporting stories `BKL-202`, `BKL-401`, `BKL-405` are `done`
  - [ ] 0.3 Confirm notebook implementation will use public API imports only (`from reformlab import ...`)

- [ ] Task 1: Create quickstart notebook scaffold (AC: #1, #6)
  - [ ] 1.1 Create `notebooks/quickstart.ipynb` as the primary deliverable
  - [ ] 1.2 Add short markdown sections for setup, first run, analysis, comparison, reproducibility, and next steps
  - [ ] 1.3 Keep content scoped to single-year quickstart flow

- [ ] Task 2: Implement first-run simulation via API facade (AC: #1, #5)
  - [ ] 2.1 Import public API symbols only (`run_scenario`, `RunConfig`, `ScenarioConfig`)
  - [ ] 2.2 Define baseline scenario with `rate_schedule={2025: 44.0}` and run it
  - [ ] 2.3 Show notebook-friendly `SimulationResult` output and panel table shape
  - [ ] 2.4 Add concise markdown on synthetic data assumptions and expected runtime

- [ ] Task 3: Implement distributional chart section (AC: #2)
  - [ ] 3.1 Compute `result.indicators("distributional")`
  - [ ] 3.2 Plot decile impacts with matplotlib inline
  - [ ] 3.3 Add brief interpretation guidance for first-time users

- [ ] Task 4: Implement parameter change and basic comparison (AC: #3, #4)
  - [ ] 4.1 Add "Try it yourself" cell changing carbon tax from €44/tCO2 to €100/tCO2
  - [ ] 4.2 Re-run scenario and show updated chart
  - [ ] 4.3 Add one baseline-vs-reform comparison view (chart or table)
  - [ ] 4.4 Explicitly defer advanced multi-year/vintage comparison to Story 6-3

- [ ] Task 5: Add reproducibility and docs cells (AC: #6)
  - [ ] 5.1 Display `result.manifest` and highlight key provenance fields
  - [ ] 5.2 Add concise next-step links to Story 6-3 materials and API docs

- [ ] Task 6: Add CI notebook execution coverage (AC: #7)
  - [ ] 6.1 Ensure `nbmake` (or equivalent) is included in dev test dependencies
  - [ ] 6.2 Ensure pytest/CI executes `notebooks/quickstart.ipynb`
  - [ ] 6.3 Ensure committed notebook has cleared outputs

- [ ] Task 7: Final validation against acceptance criteria (AC: #1-7)
  - [ ] 7.1 Run notebook from a clean environment install path
  - [ ] 7.2 Verify timed run is <30 minutes end-to-end
  - [ ] 7.3 Run notebook test in CI-equivalent command

## Dev Notes

### Architecture Compliance

This story implements **FR34** (quickstart in under 30 minutes) and **NFR19** (examples run without modification) from the PRD.

**Key architectural constraints:**

- **API facade only** - Notebook uses public API (`run_scenario`, `RunConfig`, `ScenarioConfig`, `SimulationResult.indicators`) and avoids direct subsystem imports. [Source: architecture.md#Layered-Architecture]
- **Adapter boundary respected** - Notebook remains adapter-agnostic; any adapter injection stays in tests, not user-facing notebook cells. [Source: architecture.md#Computation-Adapter-Pattern]
- **Governance visibility** - Notebook surfaces run manifest metadata for transparency/reproducibility. [Source: architecture.md#Reproducibility-&-Governance]
- **Matplotlib for plotting** - Keep visualization dependency lightweight and notebook-native. [Source: prd.md#Developer-Tool-Specific-Requirements]

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
   - One quickstart comparison view (chart or table)

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
- Single-year quickstart flow using public API only
- matplotlib charts for distributional analysis
- Basic scenario comparison (baseline vs. reform)
- Run manifest display
- CI testing with nbmake

**Out of scope:**
- Multi-year projections with vintage tracking (Story 6-3)
- Advanced comparison workflows (Story 6-3)
- Internal adapter implementation details in notebook content
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
- Notebook uses public API imports only; internal adapters may be used in tests, not notebook cells

### Previous Story Intelligence

**From Story 6-1 (Python API):**
- `SimulationResult.__repr__()` provides notebook-friendly display
- `result.indicators("distributional")` returns `IndicatorResult`
- Adapter injection is available for tests via `run_scenario(config, adapter=adapter)`
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
- [Source: architecture.md#Computation-Adapter-Pattern] - adapter boundary and testability
- [Source: ux-design-specification.md#Journey-2-First-Run-Onboarding] - Onboarding UX patterns
- [Source: interfaces/api.py] - Python API usage patterns

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
