

# Story 14.7: Build 10-Year Behavioral Simulation Notebook Demo

Status: ready-for-dev

## Story

As a **policy analyst or platform evaluator**,
I want a pedagogical notebook that demonstrates a full 10-year simulation with discrete choice household decisions (vehicle and heating investment) responding to a policy portfolio,
so that I can understand how behavioral responses reshape fleet composition and distributional outcomes over time, and evaluate the platform's discrete choice capabilities end-to-end.

## Acceptance Criteria

1. **AC-1: Notebook runs end-to-end** — Given the notebook `notebooks/demo/epic14_discrete_choice.ipynb`, when executed cell-by-cell (or via `pytest --nbmake`), then it completes without errors and produces all described outputs.

2. **AC-2: Population with asset attributes** — The notebook creates or loads a population with at least: `household_id`, `income`, `household_size`, `region`, `housing_type`, `heating_type`, `vehicle_type`, `vehicle_age`, `energy_consumption`, `carbon_emissions`. This is the same attribute set required by the vehicle and heating discrete choice domains.

3. **AC-3: Policy portfolio configuration** — The notebook configures a policy portfolio (or equivalent multi-policy setup) that includes at minimum a carbon tax with a 10-year escalating rate schedule and a vehicle subsidy (EV bonus). Policy parameters are visible and explained in narrative cells.

4. **AC-4: 10-year dynamic run with discrete choice** — The notebook executes a 10-year orchestrator run with the full discrete choice pipeline: `DiscreteChoiceStep` → `LogitChoiceStep` → `EligibilityMergeStep` → `VehicleStateUpdateStep` → `DecisionRecordStep` for the vehicle domain, and the same sequence for the heating domain. The run uses a fixed seed (42) for deterministic reproduction.

5. **AC-5: Year-by-year fleet composition changes** — The notebook displays aggregate vehicle fleet composition changes over time (e.g., EV adoption curve, diesel phase-out) and heating system transition charts (e.g., heat pump adoption). At minimum one stacked area chart or line chart showing fleet evolution across years.

6. **AC-6: Distributional indicators accounting for behavioral responses** — The notebook computes and displays distributional indicators (impact by income decile) that reflect post-behavioral-response outcomes — i.e., the carbon tax burden AFTER households have switched vehicles/heating in response to the policy.

7. **AC-7: Decision audit trail** — The notebook demonstrates reading decision records from the panel output: `{domain}_chosen`, `{domain}_probabilities`, `{domain}_utilities`, and `decision_domains` columns. At minimum a summary table or chart showing choice distributions for one year.

8. **AC-8: CI execution** — The notebook is registered in `.github/workflows/ci.yml` as a `pytest --nbmake` target. Committed outputs are cleared (execution_count=None, outputs=[]).

9. **AC-9: Static validation test** — A test file `tests/notebooks/test_epic14_notebook.py` validates: notebook exists, outputs cleared, uses public API only (no internal module imports, no OpenFisca imports), includes required sections (population, policy, simulation, fleet charts, indicators, decision audit), and CI workflow includes the notebook.

10. **AC-10: Manifest and governance** — The notebook inspects the run manifest to show discrete choice taste parameters (beta_cost) recorded per domain and the seed log for reproducibility verification.

## Tasks / Subtasks

- [ ] Task 1: Create notebook file (AC: 1, 2, 3, 4, 5, 6, 7, 8, 10)
  - [ ] 1.1: Create `notebooks/demo/epic14_discrete_choice.ipynb` with cleared outputs
  - [ ] 1.2: Section 0: Setup — imports, path resolution, `show()` helper, output dir
  - [ ] 1.3: Section 1: Build Population — construct a synthetic population (100 households) with all required asset attributes using inline PyArrow table construction (NOT the population pipeline — keep it self-contained like epic12 demo)
  - [ ] 1.4: Section 2: Configure Policy Portfolio — escalating carbon tax (€50→€100/tCO2 over 10 years) + EV subsidy; explain parameters in markdown
  - [ ] 1.5: Section 3: Wire Discrete Choice Pipeline — set up vehicle domain (6 alternatives) + heating domain (5 alternatives) with `DiscreteChoiceStep`, `LogitChoiceStep`, `EligibilityMergeStep`, state update steps, and `DecisionRecordStep` for both domains; use `MockAdapter` with `compute_fn` that computes per-alternative costs from population attributes and policy parameters
  - [ ] 1.6: Section 4: Run 10-Year Simulation — build `OrchestratorConfig` with start_year=2025, end_year=2034, seed=42, step_pipeline from Section 3; execute via `Orchestrator`; show progress and completion
  - [ ] 1.7: Section 5: Fleet Composition Over Time — extract vehicle_type and heating_type from yearly states' population data; build stacked area chart for vehicle fleet evolution (EV adoption) and heating system transitions; use `matplotlib` and `create_figure()`
  - [ ] 1.8: Section 6: Panel Output and Decision Records — build `PanelOutput.from_orchestrator_result()`; inspect decision columns (`vehicle_chosen`, `vehicle_probabilities`, `heating_chosen`, etc.); show `decision_domains` column; display `decision_domain_alternatives` metadata
  - [ ] 1.9: Section 7: Distributional Indicators — compute distributional indicators from panel output; show impact by income decile with behavioral responses; use `plot_deciles()` or custom bar chart
  - [ ] 1.10: Section 8: Governance and Reproducibility — inspect manifest metadata for `discrete_choice_parameters` (beta_cost per domain); show seed_log; verify determinism by re-running and comparing
  - [ ] 1.11: Section 9: Export and Next Steps — export panel to Parquet, verify round-trip, mention next steps (calibration, GUI)

- [ ] Task 2: Add CI integration (AC: 8)
  - [ ] 2.1: Add `uv run pytest --nbmake notebooks/demo/epic14_discrete_choice.ipynb -v` to `.github/workflows/ci.yml`

- [ ] Task 3: Create static validation test (AC: 9)
  - [ ] 3.1: Create `tests/notebooks/test_epic14_notebook.py` following `test_advanced_notebook.py` pattern
  - [ ] 3.2: Test: notebook exists at expected path
  - [ ] 3.3: Test: outputs are cleared (execution_count=None, outputs=[])
  - [ ] 3.4: Test: uses public API only — imports from `reformlab.discrete_choice`, `reformlab.orchestrator`, `reformlab.indicators`, `reformlab.visualization`; no `reformlab.computation` internal imports, no `openfisca` imports
  - [ ] 3.5: Test: includes required sections (population, policy, pipeline, simulation, fleet composition, decision records, indicators, governance)
  - [ ] 3.6: Test: includes key API calls — `DiscreteChoiceStep(`, `LogitChoiceStep(`, `VehicleStateUpdateStep(`, `HeatingStateUpdateStep(`, `DecisionRecordStep(`, `EligibilityMergeStep(`, `PanelOutput.from_orchestrator_result(`, `discrete_choice_parameters`
  - [ ] 3.7: Test: CI workflow includes this notebook's nbmake execution

- [ ] Task 4: Verify full regression (AC: all)
  - [ ] 4.1: `uv run pytest --nbmake notebooks/demo/epic14_discrete_choice.ipynb -v`
  - [ ] 4.2: `uv run pytest tests/notebooks/test_epic14_notebook.py -v`
  - [ ] 4.3: `uv run ruff check notebooks/ tests/notebooks/`
  - [ ] 4.4: `uv run pytest tests/` — full regression (no existing tests broken)

## Dev Notes

### Notebook Architecture — Self-Contained Demo Pattern

This notebook follows the **Epic 12 demo pattern** (NOT the population pipeline notebook pattern):
- Builds synthetic data inline using PyArrow table construction (100 households, deterministic with `random.seed(42)`)
- Does NOT use the PopulationPipeline or DataSourceLoader from Epic 11
- Does NOT import real INSEE/Eurostat/SDES data
- Uses `MockAdapter` with a `compute_fn` for computation (no OpenFisca dependency)

This keeps the notebook self-contained, fast (~seconds not minutes), and runnable in CI without network access or large data files.

### Mock Adapter Design for Discrete Choice

The critical design challenge is that `DiscreteChoiceStep` calls `adapter.compute()` with the expanded population (N×M rows) and needs realistic per-alternative cost outputs. The `compute_fn` must:

1. Read population attributes from the expanded table (income, vehicle_type/heating_type, carbon_emissions)
2. Apply policy parameters (carbon tax rate, EV subsidy) to compute per-household costs
3. Return a table with the domain's `cost_column` (e.g., `total_vehicle_cost`, `total_heating_cost`)
4. Handle both vehicle and heating domains (the same adapter is called for both)

**Pattern from MockAdapter:**
```python
from reformlab.computation.mock_adapter import MockAdapter
from reformlab.computation.types import PopulationData, PolicyConfig

def compute_fn(population: PopulationData, policy: PolicyConfig, period: int) -> pa.Table:
    entity_table = population.entities.get("menage", pa.table({}))
    n = entity_table.num_rows
    # ... compute costs based on attributes and policy year ...
    return pa.table({"total_vehicle_cost": costs, "total_heating_cost": heating_costs})

adapter = MockAdapter(compute_fn=compute_fn)
```

### Step Pipeline Wiring — Full Two-Domain Pipeline

The notebook must wire the following 12-step pipeline (6 per domain):

```
# Vehicle domain
DiscreteChoiceStep(adapter, vehicle_domain, policy, name="discrete_choice_vehicle", ...)
LogitChoiceStep(taste_params, name="logit_choice_vehicle", depends_on=("discrete_choice_vehicle",))
EligibilityMergeStep(name="eligibility_merge_vehicle", depends_on=("logit_choice_vehicle",))
VehicleStateUpdateStep(vehicle_domain, name="vehicle_state_update", depends_on=("eligibility_merge_vehicle",))
DecisionRecordStep(name="decision_record_vehicle", depends_on=("vehicle_state_update",))

# Heating domain
DiscreteChoiceStep(adapter, heating_domain, policy, name="discrete_choice_heating", depends_on=("decision_record_vehicle",))
LogitChoiceStep(taste_params_heating, name="logit_choice_heating", depends_on=("discrete_choice_heating",))
EligibilityMergeStep(name="eligibility_merge_heating", depends_on=("logit_choice_heating",))
HeatingStateUpdateStep(heating_domain, name="heating_state_update", depends_on=("eligibility_merge_heating",))
DecisionRecordStep(name="decision_record_heating", depends_on=("heating_state_update",))
```

Note: The heating domain's `DiscreteChoiceStep` must `depends_on=("decision_record_vehicle",)` to ensure sequential domain execution.

### Key API Imports for the Notebook

```python
# Discrete choice
from reformlab.discrete_choice import (
    DiscreteChoiceStep,
    LogitChoiceStep,
    EligibilityMergeStep,
    VehicleInvestmentDomain,
    VehicleStateUpdateStep,
    HeatingInvestmentDomain,
    HeatingStateUpdateStep,
    DecisionRecordStep,
    TasteParameters,
    EligibilityFilter,
    EligibilityRule,
    default_vehicle_domain_config,
    default_heating_domain_config,
    DECISION_LOG_KEY,
)

# Orchestrator
from reformlab.orchestrator.runner import Orchestrator
from reformlab.orchestrator.types import OrchestratorConfig, YearState
from reformlab.orchestrator.panel import PanelOutput

# Mock adapter
from reformlab.computation.mock_adapter import MockAdapter
from reformlab.computation.types import PopulationData, PolicyConfig

# Indicators
from reformlab.indicators import compute_distributional_indicators, DistributionalConfig

# Visualization
from reformlab.visualization import create_figure
import matplotlib.pyplot as plt
```

**Note on import boundaries:** The notebook imports from `reformlab.computation.mock_adapter` (public test utility) and `reformlab.computation.types` (public types). These are NOT internal OpenFisca adapter imports. The static test should verify no `from reformlab.computation.adapter import` or `from reformlab.computation.openfisca` imports. The `MockAdapter` and `PopulationData`/`PolicyConfig` types are public API surface used by all existing notebooks and tests.

### Population Construction

Build a 100-household synthetic population inline:

```python
random.seed(42)
N = 100

# Household attributes
household_ids = list(range(N))
incomes = [15000.0 + i * 850.0 + random.gauss(0, 2000) for i in range(N)]
vehicle_types = random.choices(["petrol", "diesel", "hybrid", "ev"], weights=[0.35, 0.40, 0.15, 0.10], k=N)
vehicle_ages = [random.randint(0, 20) for _ in range(N)]
heating_types = random.choices(["gas", "electric", "oil", "heat_pump", "wood"], weights=[0.35, 0.25, 0.20, 0.10, 0.10], k=N)
# ... etc.
```

Store as `PopulationData` for use with `DiscreteChoiceStep`:
```python
entity_table = pa.table({...})
population = PopulationData(entities={"menage": entity_table})
```

### Fleet Composition Extraction

After the 10-year run, extract per-year fleet composition from yearly states:

```python
fleet_data = {}
for year, state in sorted(result.yearly_states.items()):
    pop = state.data.get("population_data")
    entity_table = pop.entities["menage"]
    vehicle_counts = {}
    for vt in entity_table.column("vehicle_type").to_pylist():
        vehicle_counts[vt] = vehicle_counts.get(vt, 0) + 1
    fleet_data[year] = vehicle_counts
```

Then use `matplotlib` stacked area chart to show fleet evolution.

### Panel Decision Column Access

```python
panel = PanelOutput.from_orchestrator_result(result)
table = panel.table

# Decision columns present
print(table.column_names)  # [..., "vehicle_chosen", "vehicle_probabilities", ...]

# Access decision metadata
alts = panel.metadata["decision_domain_alternatives"]
# {"vehicle": ["keep_current", "buy_petrol", ...], "heating": ["keep_current", ...]}
```

### Manifest Discrete Choice Parameters

```python
# Via OrchestratorRunner (if used) or direct extraction
from reformlab.governance.capture import capture_discrete_choice_parameters

dc_params = capture_discrete_choice_parameters(result.yearly_states)
# [{"domain_name": "heating", "alternative_ids": [...], "beta_cost": -0.02, ...},
#  {"domain_name": "vehicle", "alternative_ids": [...], "beta_cost": -0.01, ...}]
```

### Eligibility Filtering Setup

Optional but recommended to demonstrate performance optimization:

```python
vehicle_eligibility = EligibilityFilter(
    rules=(
        EligibilityRule(column="vehicle_age", operator="gt", threshold=8,
                       description="Only vehicles older than 8 years face replacement choice"),
    ),
    default_choice="keep_current",
    entity_key="menage",
)
```

Pass to `DiscreteChoiceStep(eligibility_filter=vehicle_eligibility, ...)`.

### Notebook Cell Conventions (MUST FOLLOW)

From analysis of existing notebooks:
- **Path resolution:** `Path.cwd() if "__file__" not in dir() else Path(__file__).parent` for CI compatibility
- **sys.path insertion:** Add `src/` dir to sys.path for notebook imports
- **Cleared outputs:** All cells must have `execution_count: None` and `outputs: []`
- **`show()` helper:** Define inline for readable PyArrow table display
- **Seed fixing:** All stochastic operations use seed=42
- **Section numbering:** `## Section N: Title` format
- **Narrative before code:** Plain-English explanations before each code cell
- **"What just happened?" summaries:** After complex operations
- **No `def show(` in imported form:** Define inline, matching existing patterns

### Static Test Patterns (from test_advanced_notebook.py)

```python
NOTEBOOK_PATH = Path(__file__).resolve().parents[2] / "notebooks" / "demo" / "epic14_discrete_choice.ipynb"
CI_WORKFLOW_PATH = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"

def test_notebook_exists() -> None: ...
def test_outputs_cleared() -> None: ...
def test_uses_public_api() -> None: ...
def test_required_sections() -> None: ...
def test_key_api_calls() -> None: ...
def test_ci_includes_notebook() -> None: ...
```

### CI Integration

Add to `.github/workflows/ci.yml` after the existing notebook entries:
```yaml
- run: uv run pytest --nbmake notebooks/demo/epic14_discrete_choice.ipynb -v
```

### Project Structure Notes

```
notebooks/
├── demo/
│   ├── epic14_discrete_choice.ipynb  # NEW — This story's deliverable
│   ├── epic12_portfolio_comparison.ipynb  # Existing — pattern reference
│   └── epic13_custom_templates.ipynb     # Existing — pattern reference

tests/
├── notebooks/
│   ├── test_quickstart_notebook.py       # Existing
│   ├── test_advanced_notebook.py         # Existing — test pattern reference
│   └── test_epic14_notebook.py           # NEW — Static validation

.github/
└── workflows/
    └── ci.yml                            # MODIFIED — Add nbmake entry
```

No new Python source files in `src/reformlab/`. No new dependencies.

### Edge Cases and Gotchas

| Scenario | Handling |
|----------|----------|
| MockAdapter must return correct N×M rows for expanded population | `compute_fn` reads `entity_table.num_rows` and returns matching row count |
| `PopulationData` construction | Use `PopulationData(entities={"menage": table})` — discrete choice reads from `population_key="population_data"` which maps to `PopulationData` |
| `PolicyConfig` for DiscreteChoiceStep | Need a valid `PolicyConfig` with `.name` property; use `PolicyConfig(name="carbon_tax_2025", parameters={...})` |
| Vehicle domain uses `cost_column="total_vehicle_cost"` | `compute_fn` must return a table containing this column name |
| Heating domain uses `cost_column="total_heating_cost"` | Same — `compute_fn` must return this column too |
| 10-year run modifies `PopulationData` in state each year | `VehicleStateUpdateStep` and `HeatingStateUpdateStep` update population attributes based on choices; subsequent years see updated fleet |
| Eligibility filtering reduces expanded population | If vehicle_eligibility filters 70% of households, only 30% × 6 alternatives = 180 rows go to adapter (instead of 600) |
| Decision records only appear when `DecisionRecordStep` is in pipeline | Must explicitly add these steps; panel extension checks `DECISION_LOG_KEY` in yearly states |

### Cross-Story Dependencies

| Story | Relationship | Notes |
|-------|-------------|-------|
| 14.1 | Depends on | DiscreteChoiceStep, expansion, reshape |
| 14.2 | Depends on | LogitChoiceStep, TasteParameters, ChoiceResult |
| 14.3 | Depends on | VehicleInvestmentDomain, VehicleStateUpdateStep |
| 14.4 | Depends on | HeatingInvestmentDomain, HeatingStateUpdateStep |
| 14.5 | Depends on | EligibilityFilter, EligibilityMergeStep |
| 14.6 | Depends on | DecisionRecordStep, DECISION_LOG_KEY, panel decision columns |
| 3.7 | Depends on | PanelOutput.from_orchestrator_result() |
| 4.1 | Depends on | compute_distributional_indicators() |
| 5.2 | Depends on | capture_discrete_choice_parameters() |

### Out of Scope Guardrails

- **DO NOT** modify any existing source files in `src/reformlab/`
- **DO NOT** modify any existing test files
- **DO NOT** modify any existing notebooks
- **DO NOT** add new Python dependencies
- **DO NOT** use real OpenFisca or network data
- **DO NOT** implement calibration (Epic 15)
- **DO NOT** implement GUI features (Epic 17)
- **DO NOT** modify the PopulationPipeline or data source loaders

### References

- [Source: `notebooks/demo/epic12_portfolio_comparison.ipynb` — Self-contained demo pattern with inline data construction]
- [Source: `tests/notebooks/test_advanced_notebook.py` — Static validation test pattern]
- [Source: `.github/workflows/ci.yml` — CI nbmake integration]
- [Source: `src/reformlab/discrete_choice/__init__.py` — Full public API surface]
- [Source: `src/reformlab/discrete_choice/step.py` — DiscreteChoiceStep constructor, DISCRETE_CHOICE_METADATA_KEY]
- [Source: `src/reformlab/discrete_choice/logit.py` — LogitChoiceStep, TasteParameters, DISCRETE_CHOICE_RESULT_KEY]
- [Source: `src/reformlab/discrete_choice/vehicle.py` — VehicleInvestmentDomain, VehicleStateUpdateStep, default_vehicle_domain_config()]
- [Source: `src/reformlab/discrete_choice/heating.py` — HeatingInvestmentDomain, HeatingStateUpdateStep, default_heating_domain_config()]
- [Source: `src/reformlab/discrete_choice/eligibility.py` — EligibilityFilter, EligibilityRule, EligibilityMergeStep]
- [Source: `src/reformlab/discrete_choice/decision_record.py` — DecisionRecordStep, DecisionRecord, DECISION_LOG_KEY]
- [Source: `src/reformlab/orchestrator/runner.py` — Orchestrator, OrchestratorConfig]
- [Source: `src/reformlab/orchestrator/panel.py` — PanelOutput, _build_decision_columns, compare_panels]
- [Source: `src/reformlab/orchestrator/types.py` — OrchestratorConfig, YearState, OrchestratorResult]
- [Source: `src/reformlab/computation/mock_adapter.py` — MockAdapter with compute_fn pattern]
- [Source: `src/reformlab/computation/types.py` — PopulationData, PolicyConfig, ComputationResult]
- [Source: `src/reformlab/indicators/__init__.py` — compute_distributional_indicators, DistributionalConfig]
- [Source: `src/reformlab/visualization/plotting.py` — plot_deciles, plot_yearly, plot_comparison]
- [Source: `src/reformlab/visualization/styling.py` — create_figure]
- [Source: `src/reformlab/governance/capture.py` — capture_discrete_choice_parameters]
- [Source: `docs/epics.md` — Epic 14 AC for BKL-1407]
- [Source: `docs/project-context.md` — Project rules: PyArrow-first, frozen dataclasses, adapter isolation]
- [Source: `_bmad-output/implementation-artifacts/14-6-extend-panel-output-and-manifests-with-decision-records.md` — Story 14.6 with pipeline wiring details]

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

- Story creation notes (pre-implementation):
  - Ultimate context engine analysis completed — comprehensive developer guide created
  - Full discrete choice subsystem API analyzed: 7 step types, 2 domain implementations, types, state keys
  - Existing notebook conventions analyzed: 10 notebooks, path resolution, cell patterns, show() helper, visualization API
  - Epic 12 demo pattern identified as reference: self-contained inline data, MockAdapter, no external data dependencies
  - CI integration pattern confirmed: pytest --nbmake in ci.yml
  - Static test pattern from test_advanced_notebook.py: 12 tests covering existence, output clearing, public API, sections, CI
  - Full step pipeline wiring documented: 10-step two-domain pipeline with correct depends_on chains
  - MockAdapter compute_fn design documented: must handle expanded N×M populations and return domain cost columns
  - Fleet composition extraction pattern documented: yearly state population data → vehicle_type/heating_type counts
  - Decision column access pattern documented: panel.table.column("vehicle_chosen"), panel.metadata["decision_domain_alternatives"]

### File List

#### New Files
- `notebooks/demo/epic14_discrete_choice.ipynb` — 10-year behavioral simulation notebook demo
- `tests/notebooks/test_epic14_notebook.py` — Static validation tests for the notebook

#### Modified Files
- `.github/workflows/ci.yml` — Add nbmake entry for epic14 notebook
