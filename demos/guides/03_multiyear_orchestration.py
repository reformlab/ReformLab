"""
Epic 3 Demo — Dynamic Orchestrator and Vintage Tracking

In Epic 1 we built the data/computation foundation. In Epic 2 we built
scenario templates and workflow configs. Epic 3 is where the platform starts
to *run* multi-year simulations.

This script walks through the Epic 3 capabilities step by step:

1. Yearly loop execution — deterministic run from start_year to end_year
2. Pluggable step pipelines — dependency-aware ordering with StepRegistry
3. Carry-forward logic — deterministic state updates between years
4. Vintage transitions — cohort aging, retirement, and new entry
5. Computation integration — adapter calls in the yearly loop
6. Workflow handoff — running through run_workflow() + OrchestratorRunner
7. Panel output — household-by-year tables and baseline/reform comparison
8. Failure behavior — partial results preserved when a year fails

Usage:
    python demos/guides/03_multiyear_orchestration.py
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pyarrow as pa

from reformlab.computation import ComputationResult, PolicyConfig, PopulationData
from reformlab.computation.mock_adapter import MockAdapter
from reformlab.orchestrator import (
    COMPUTATION_METADATA_KEY,
    COMPUTATION_RESULT_KEY,
    PANEL_VERSION,
    SEED_LOG_KEY,
    STEP_EXECUTION_LOG_KEY,
    CarryForwardConfig,
    CarryForwardRule,
    CarryForwardStep,
    ComputationStep,
    Orchestrator,
    OrchestratorConfig,
    OrchestratorRunner,
    PanelOutput,
    StepRegistry,
    YearState,
    compare_panels,
    step,
)
from reformlab.templates.schema import PolicyParameters
from reformlab.templates.workflow import (
    DataSourceConfig,
    RunConfig,
    ScenarioRef,
    WorkflowConfig,
    run_workflow,
)
from reformlab.vintage import (
    VintageCohort,
    VintageConfig,
    VintageState,
    VintageSummary,
    VintageTransitionRule,
    VintageTransitionStep,
)
from reformlab.visualization import show

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = DATA_DIR / "epic3_outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"Data directory:    {DATA_DIR}")
print(f"Output directory:  {OUTPUT_DIR}")


# ---------------------------------------------------------------------------
# 1. Yearly Loop Execution
# ---------------------------------------------------------------------------
#
# The orchestrator executes each year in order. State from year t becomes
# the input for year t+1.
#
# With a master seed, each year gets a deterministic derived seed
# (seed ^ year) and this seed trace is stored in run metadata.

@step(name="year_counter")
def year_counter(year: int, state: YearState) -> YearState:
    new_data = dict(state.data)
    new_data["counter"] = new_data.get("counter", 0) + 1
    return replace(state, data=new_data)


basic_config = OrchestratorConfig(
    start_year=2026,
    end_year=2028,
    initial_state={"counter": 0},
    seed=42,
    step_pipeline=(year_counter,),
)
basic_result = Orchestrator(basic_config).run()

print(f"Success: {basic_result.success}")
for year in sorted(basic_result.yearly_states):
    year_state = basic_result.yearly_states[year]
    print(f"  Year {year}: counter={year_state.data['counter']}, seed={year_state.seed}")

print("\nSeed log from metadata:")
print(basic_result.metadata[SEED_LOG_KEY])


# ---------------------------------------------------------------------------
# 2. Dependency-Aware Step Pipelines
# ---------------------------------------------------------------------------
#
# Steps are plugins. You register them in any order, and StepRegistry builds
# a dependency-safe execution order.

@step(name="collect_inputs")
def collect_inputs(year: int, state: YearState) -> YearState:
    return state


@step(name="apply_policy", depends_on=("collect_inputs",))
def apply_policy(year: int, state: YearState) -> YearState:
    return state


@step(name="summarize", depends_on=("apply_policy",))
def summarize(year: int, state: YearState) -> YearState:
    return state


registry = StepRegistry()
registry.register(summarize)
registry.register(apply_policy)
registry.register(collect_inputs)

ordered_pipeline = registry.build_pipeline()
print("Pipeline order after dependency resolution:")
print([step_obj.name for step_obj in ordered_pipeline])


# ---------------------------------------------------------------------------
# 3. Carry-Forward State Updates
# ---------------------------------------------------------------------------
#
# Carry-forward applies deterministic year-to-year update rules per variable.
#
# Here we update:
# - income: scale by 1.03 each year
# - tax_rate: increment by 0.005 each year
# - household_size: static (unchanged)

carry_forward_step = CarryForwardStep(
    CarryForwardConfig(
        rules=(
            CarryForwardRule(
                variable="income",
                rule_type="scale",
                period_semantics="annual_growth_rate",
                value=1.03,
            ),
            CarryForwardRule(
                variable="tax_rate",
                rule_type="increment",
                period_semantics="annual_increment",
                value=0.005,
            ),
            CarryForwardRule(
                variable="household_size",
                rule_type="static",
                period_semantics="annual_constant",
            ),
        )
    )
)

carry_config = OrchestratorConfig(
    start_year=2026,
    end_year=2028,
    initial_state={
        "income": 30000.0,
        "tax_rate": 0.10,
        "household_size": 3,
    },
    seed=7,
    step_pipeline=(carry_forward_step,),
)
carry_result = Orchestrator(carry_config).run()

for year in sorted(carry_result.yearly_states):
    s = carry_result.yearly_states[year]
    print(
        f"Year {year}: income={s.data['income']:.2f}, "
        f"tax_rate={s.data['tax_rate']:.3f}, "
        f"household_size={s.data['household_size']}"
    )


# ---------------------------------------------------------------------------
# 4. Vintage Cohort Transitions
# ---------------------------------------------------------------------------
#
# Vintage tracking models asset cohorts (for MVP: vehicles) over time.
#
# Each year:
# 1. Existing cohorts age (age += 1)
# 2. Cohorts above max_age retire
# 3. A new age-0 entry cohort is added

initial_vehicle_state = VintageState(
    asset_class="vehicle",
    cohorts=(
        VintageCohort(age=0, count=900),
        VintageCohort(age=2, count=300),
    ),
)

vintage_step = VintageTransitionStep(
    VintageConfig(
        asset_class="vehicle",
        rules=(
            VintageTransitionRule(rule_type="fixed_entry", parameters={"count": 250}),
            VintageTransitionRule(rule_type="max_age_retirement", parameters={"max_age": 3}),
        ),
        initial_state=initial_vehicle_state,
    )
)

vintage_config = OrchestratorConfig(
    start_year=2026,
    end_year=2029,
    initial_state={},
    seed=11,
    step_pipeline=(vintage_step,),
)
vintage_result = Orchestrator(vintage_config).run()

for year in sorted(vintage_result.yearly_states):
    state = vintage_result.yearly_states[year]
    vintage_state = state.data["vintage_vehicle"]
    summary = VintageSummary.from_state(vintage_state)
    print(
        f"Year {year}: total={summary.total_count}, "
        f"mean_age={summary.mean_age:.2f}, "
        f"distribution={summary.age_distribution}"
    )


# ---------------------------------------------------------------------------
# 5. Computation Step in the Yearly Loop
# ---------------------------------------------------------------------------
#
# ComputationStep invokes a ComputationAdapter each year and stores:
# - ComputationResult in YearState.data["computation_result"]
# - execution metadata in YearState.metadata["computation_metadata"]
#
# We use MockAdapter so this demo runs without OpenFisca.

population = PopulationData(
    tables={
        "default": pa.table(
            {
                "household_id": pa.array([1, 2, 3, 4]),
                "income": pa.array([22000.0, 34000.0, 48000.0, 61000.0]),
            }
        )
    },
    metadata={"source": "epic3-demo"},
)
policy = PolicyConfig(
    policy=PolicyParameters(rate_schedule={2026: 55.0}),
    name="baseline_policy",
)

mock_output = pa.table(
    {
        "household_id": pa.array([1, 2, 3, 4]),
        "income_tax": pa.array([1200.0, 2000.0, 2900.0, 3600.0]),
        "carbon_tax": pa.array([180.0, 190.0, 210.0, 240.0]),
    }
)
adapter = MockAdapter(version_string="mock-epic3-v1", default_output=mock_output)
computation_step = ComputationStep(adapter=adapter, population=population, policy=policy)

computation_config = OrchestratorConfig(
    start_year=2026,
    end_year=2028,
    initial_state={},
    seed=123,
    step_pipeline=(computation_step,),
)
computation_result = Orchestrator(computation_config).run()

print(f"Success: {computation_result.success}")
print(f"Adapter calls: {len(adapter.call_log)}")
for year in sorted(computation_result.yearly_states):
    year_state = computation_result.yearly_states[year]
    metadata = year_state.metadata[COMPUTATION_METADATA_KEY]
    print(
        f"Year {year}: period={metadata['computation_period']}, "
        f"rows={metadata['computation_row_count']}, "
        f"adapter={metadata['adapter_version']}"
    )

print("\nSample computation output:")
show(computation_result.yearly_states[2026].data[COMPUTATION_RESULT_KEY].output_fields)


# ---------------------------------------------------------------------------
# 6. Full Pipeline + Workflow Handoff
# ---------------------------------------------------------------------------
#
# Now combine Epic 3 pieces in one run:
# - computation
# - vintage transition
# - carry-forward
#
# Then run through the workflow API using OrchestratorRunner.

pipeline_registry = StepRegistry()

pipeline_carry = CarryForwardStep(
    CarryForwardConfig(
        rules=(
            CarryForwardRule(
                variable="income_index",
                rule_type="scale",
                period_semantics="annual_growth",
                value=1.01,
            ),
        )
    ),
    depends_on=("vintage_transition",),
)
pipeline_vintage = VintageTransitionStep(
    vintage_step.config,
    depends_on=("computation",),
)

# Register out of order on purpose
pipeline_registry.register(pipeline_carry)
pipeline_registry.register(pipeline_vintage)
pipeline_registry.register(computation_step)

pipeline = pipeline_registry.build_pipeline()
print("Pipeline order:", [s.name for s in pipeline])

full_config = OrchestratorConfig(
    start_year=2026,
    end_year=2028,
    initial_state={"income_index": 1.0},
    seed=2026,
    step_pipeline=pipeline,
)
full_result = Orchestrator(full_config).run()

print(f"\nOrchestrator success: {full_result.success}")
print("Seed trace:")
print(full_result.metadata[SEED_LOG_KEY])
print("\nFirst 5 step execution records:")
for record in full_result.metadata[STEP_EXECUTION_LOG_KEY][:5]:
    print(record)

final_state = full_result.yearly_states[2028]
print(f"\nFinal income_index: {final_state.data['income_index']:.6f}")
print(f"Final vintage total: {final_state.data['vintage_vehicle'].total_count}")

workflow_config = WorkflowConfig(
    name="epic3_workflow_demo",
    version="1.0",
    data_sources=DataSourceConfig(population="synthetic", emission_factors="default"),
    scenarios=(
        ScenarioRef(role="baseline", reference="baseline_scenario"),
        ScenarioRef(role="reform", reference="reform_scenario"),
    ),
    run_config=RunConfig(projection_years=3, start_year=2026, output_format="csv"),
)
workflow_runner = OrchestratorRunner(step_pipeline=pipeline, seed=2026, initial_state={"income_index": 1.0})
workflow_result = run_workflow(workflow_config, runner=workflow_runner)

print("\nrun_workflow() result:")
print(f"  Success: {workflow_result.success}")
print(f"  Years:   {sorted(int(y) for y in workflow_result.outputs['yearly_states'].keys())}")


# ---------------------------------------------------------------------------
# 7. Scenario-Year Panel Output + Baseline/Reform Comparison
# ---------------------------------------------------------------------------
#
# Epic 3 converts yearly states into a panel table (household_id, year,
# computed fields), with CSV/Parquet export.
#
# Then baseline and reform panels can be compared with automatic delta
# columns.

def run_panel(label: str, tax_multiplier: float) -> PanelOutput:
    output = pa.table(
        {
            "household_id": pa.array([1, 2, 3, 4]),
            "income_tax": pa.array([1200.0, 2000.0, 2900.0, 3600.0]),
            "carbon_tax": pa.array([
                180.0 * tax_multiplier,
                190.0 * tax_multiplier,
                210.0 * tax_multiplier,
                240.0 * tax_multiplier,
            ]),
        }
    )
    run_adapter = MockAdapter(version_string=f"{label}-adapter", default_output=output)
    run_step = ComputationStep(adapter=run_adapter, population=population, policy=policy)

    run_config = OrchestratorConfig(
        start_year=2026,
        end_year=2028,
        initial_state={},
        seed=900,
        step_pipeline=(run_step,),
    )
    run_result = Orchestrator(run_config).run()
    panel = PanelOutput.from_orchestrator_result(run_result)

    panel.to_csv(OUTPUT_DIR / f"{label}_panel.csv")
    panel.to_parquet(OUTPUT_DIR / f"{label}_panel.parquet")
    return panel


baseline_panel = run_panel("baseline", tax_multiplier=1.0)
reform_panel = run_panel("reform", tax_multiplier=1.2)
comparison = compare_panels(baseline_panel, reform_panel)

print(f"Panel format version: {PANEL_VERSION}")
print(f"Baseline shape: {baseline_panel.shape}")
print(f"Reform shape:   {reform_panel.shape}")
print(f"Comparison shape: {comparison.shape}")

print("\nComparison preview:")
show(
    comparison.table.select(
        [
            "household_id",
            "year",
            "_baseline_carbon_tax",
            "_reform_carbon_tax",
            "_delta_carbon_tax",
            "_origin",
        ]
    )
)

print("\nComparison metadata keys:")
print(sorted(comparison.metadata.keys()))


# ---------------------------------------------------------------------------
# 8. Failure Path and Partial Results
# ---------------------------------------------------------------------------
#
# If a step fails in year t, the orchestrator returns:
# - success = False
# - failed_year and failed_step
# - all completed years before the failure
# - trace metadata (seed log + executed steps)
#
# Panel generation still works on completed years.

class FailingAt2028Adapter:
    def version(self) -> str:
        return "failing-demo-adapter"

    def compute(self, population: PopulationData, policy: PolicyConfig, period: int) -> ComputationResult:
        if period == 2028:
            raise RuntimeError("Simulated failure at year 2028")
        return ComputationResult(
            output_fields=pa.table(
                {
                    "household_id": pa.array([1, 2]),
                    "income_tax": pa.array([1000.0, 1500.0]),
                }
            ),
            adapter_version=self.version(),
            period=period,
        )


failing_step = ComputationStep(
    adapter=FailingAt2028Adapter(),
    population=population,
    policy=policy,
)
failing_config = OrchestratorConfig(
    start_year=2026,
    end_year=2029,
    initial_state={},
    seed=77,
    step_pipeline=(failing_step,),
)
failing_result = Orchestrator(failing_config).run()

print(f"Success:     {failing_result.success}")
print(f"Failed year: {failing_result.failed_year}")
print(f"Failed step: {failing_result.failed_step}")
print(f"Completed years: {sorted(failing_result.yearly_states.keys())}")
print(f"Errors: {failing_result.errors}")

partial_panel = PanelOutput.from_orchestrator_result(failing_result)
print(f"\nPartial panel shape: {partial_panel.shape}")
print(f"Partial metadata flag: {partial_panel.metadata.get('partial')}")


# ---------------------------------------------------------------------------
# What We Built (Summary)
# ---------------------------------------------------------------------------
#
# | Capability               | In plain terms                                    |
# |--------------------------|---------------------------------------------------|
# | Yearly loop orchestrator | Runs projection years with deterministic seeds    |
# | Step plugin model        | Pluggable steps without changing orchestrator core |
# | Carry-forward step       | Deterministic updates of state between years       |
# | Vintage transition step  | Cohort aging, retirement, and entry                |
# | Computation integration  | Calls adapters inside the yearly loop              |
# | Workflow handoff         | Executes via run_workflow() + OrchestratorRunner   |
# | Panel output             | Household-by-year tables with CSV/Parquet export   |
# | Baseline vs reform       | Outer join + numeric delta columns                 |
# | Failure resilience       | Preserves completed years when a later year fails  |

print("\nGenerated files in data/epic3_outputs:")
for path in sorted(OUTPUT_DIR.iterdir()):
    print(f"  {path.relative_to(DATA_DIR)}")
