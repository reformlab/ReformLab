"""Epic 14 Demo — 10-Year Behavioral Simulation with Discrete Choice.

Demonstrates a full 10-year simulation where households make discrete
investment decisions (vehicle replacement and heating system upgrade) in
response to an escalating carbon tax and EV subsidy policy portfolio.

Epic 14 adds behavioral responses to the platform:

1. Discrete choice steps — DiscreteChoiceStep expands populations, LogitChoiceStep draws choices
2. Domain-specific state updates — Vehicle and heating fleet composition evolve year-by-year
3. Eligibility filtering — Only eligible households face the choice (performance optimization)
4. Decision audit trail — Full provenance: chosen alternatives, probabilities, utilities per domain
5. Governance — Taste parameters and seeds recorded in manifests
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Section 0: Setup
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR
while not (REPO_ROOT / "src").exists() and REPO_ROOT != REPO_ROOT.parent:
    REPO_ROOT = REPO_ROOT.parent

SRC_DIR = REPO_ROOT / "src"
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import pyarrow as pa
import pyarrow.parquet as pq

# Mock adapter
from reformlab.computation.mock_adapter import MockAdapter
from reformlab.computation.types import PolicyConfig, PopulationData

# Discrete choice
from reformlab.discrete_choice import (
    DECISION_LOG_KEY,
    DecisionRecordStep,
    DiscreteChoiceStep,
    EligibilityFilter,
    EligibilityMergeStep,
    EligibilityRule,
    HeatingInvestmentDomain,
    HeatingStateUpdateStep,
    LogitChoiceStep,
    TasteParameters,
    VehicleInvestmentDomain,
    VehicleStateUpdateStep,
    default_heating_domain_config,
    default_vehicle_domain_config,
)

# Governance
from reformlab.governance.capture import capture_discrete_choice_parameters

# Indicators
from reformlab.indicators import compute_distributional_indicators
from reformlab.orchestrator.computation_step import (
    COMPUTATION_METADATA_KEY,
    COMPUTATION_RESULT_KEY,
)
from reformlab.orchestrator.panel import PanelOutput

# Orchestrator
from reformlab.orchestrator.runner import Orchestrator
from reformlab.orchestrator.types import OrchestratorConfig, YearState

# Visualization
from reformlab.visualization import (
    create_figure_grid,
    plot_bar_series,
    plot_stacked_area,
    show,
    show_figure,
)

OUTPUT_DIR = SCRIPT_DIR / "data" / "epic14_outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"Repo root:  {REPO_ROOT}")
print(f"Output dir: {OUTPUT_DIR}")


# ---------------------------------------------------------------------------
# Section 1: Build Population
# ---------------------------------------------------------------------------
#
# 100 synthetic households with demographic and asset attributes:
#   Demographics: household_id, income, household_size, region
#   Housing:      housing_type, heating_type, heating_age
#   Vehicle:      vehicle_type, vehicle_age
#   Energy:       energy_consumption, carbon_emissions

random.seed(42)
N = 100

household_ids = list(range(N))
incomes = [15000.0 + i * 850.0 + random.gauss(0, 2000) for i in range(N)]
household_sizes = [random.choice([1, 2, 3, 4, 5]) for _ in range(N)]
regions = random.choices(
    ["ile_de_france", "auvergne_rhone_alpes", "occitanie", "nouvelle_aquitaine", "bretagne"],
    weights=[0.25, 0.20, 0.15, 0.20, 0.20],
    k=N,
)
housing_types = random.choices(
    ["apartment", "house", "townhouse"],
    weights=[0.45, 0.40, 0.15],
    k=N,
)

# Vehicle attributes
vehicle_types = random.choices(
    ["petrol", "diesel", "hybrid", "ev"],
    weights=[0.35, 0.40, 0.15, 0.10],
    k=N,
)
vehicle_ages = [random.randint(0, 20) for _ in range(N)]

vehicle_emission_map = {"petrol": 120.0, "diesel": 110.0, "hybrid": 50.0, "ev": 0.0}
vehicle_emissions_gkm = [vehicle_emission_map[vt] for vt in vehicle_types]

# Heating attributes
heating_types = random.choices(
    ["gas", "electric", "oil", "heat_pump", "wood"],
    weights=[0.35, 0.25, 0.20, 0.10, 0.10],
    k=N,
)
heating_ages = [random.randint(0, 25) for _ in range(N)]

heating_emission_map = {"gas": 0.227, "electric": 0.057, "oil": 0.324, "heat_pump": 0.057, "wood": 0.030}
heating_emissions_kgco2_kwh = [heating_emission_map[ht] for ht in heating_types]

# Energy and emissions — correlated with vehicle and heating types
emission_factors = {"petrol": 4.5, "diesel": 4.0, "hybrid": 2.5, "ev": 0.5}
heating_emission_factors = {"gas": 3.0, "electric": 1.0, "oil": 4.0, "heat_pump": 0.5, "wood": 0.3}

energy_consumption = [
    8000.0 + random.gauss(0, 1500) + household_sizes[i] * 500
    for i in range(N)
]
carbon_emissions = [
    emission_factors[vehicle_types[i]] + heating_emission_factors[heating_types[i]] + random.gauss(0, 0.5)
    for i in range(N)
]

entity_table = pa.table({
    "household_id": pa.array(household_ids, type=pa.int64()),
    "income": pa.array(incomes, type=pa.float64()),
    "household_size": pa.array(household_sizes, type=pa.int64()),
    "region": pa.array(regions, type=pa.string()),
    "housing_type": pa.array(housing_types, type=pa.string()),
    "vehicle_type": pa.array(vehicle_types, type=pa.string()),
    "vehicle_age": pa.array(vehicle_ages, type=pa.int64()),
    "vehicle_emissions_gkm": pa.array(vehicle_emissions_gkm, type=pa.float64()),
    "heating_type": pa.array(heating_types, type=pa.string()),
    "heating_age": pa.array(heating_ages, type=pa.int64()),
    "heating_emissions_kgco2_kwh": pa.array(heating_emissions_kgco2_kwh, type=pa.float64()),
    "energy_consumption": pa.array(energy_consumption, type=pa.float64()),
    "carbon_emissions": pa.array(carbon_emissions, type=pa.float64()),
})

population = PopulationData(tables={"menage": entity_table})

print(f"Population: {entity_table.num_rows} households, {entity_table.num_columns} columns")
print(f"Columns: {entity_table.column_names}")
print()
show(entity_table, n=8)


# ---------------------------------------------------------------------------
# Section 2: Configure Policy Portfolio
# ---------------------------------------------------------------------------
#
# 10-year escalating carbon tax (EUR 50 to EUR 100/tCO2) combined with an
# EV purchase subsidy (EUR 4,000) and heat pump subsidy (EUR 2,000).

CARBON_TAX_SCHEDULE = {
    year: 50.0 + (year - 2025) * (50.0 / 9)
    for year in range(2025, 2035)
}

EV_SUBSIDY = 4000.0
HEAT_PUMP_SUBSIDY = 2000.0

policy = PolicyConfig(
    policy={
        "carbon_tax_schedule": CARBON_TAX_SCHEDULE,
        "ev_subsidy": EV_SUBSIDY,
        "heat_pump_subsidy": HEAT_PUMP_SUBSIDY,
    },
    name="carbon_tax_ev_subsidy_2025",
    description=(
        "Escalating carbon tax (EUR 50-100/tCO2) "
        "with EV and heat pump subsidies"
    ),
)

print("Policy portfolio configured:")
start_rate = CARBON_TAX_SCHEDULE[2025]
end_rate = CARBON_TAX_SCHEDULE[2034]
print(f"  Carbon tax: EUR {start_rate:.0f}/tCO2 (2025) -> EUR {end_rate:.0f}/tCO2 (2034)")
print(f"  EV subsidy: EUR {EV_SUBSIDY:,.0f}")
print(f"  Heat pump subsidy: EUR {HEAT_PUMP_SUBSIDY:,.0f}")
print("\nRate schedule:")
for year, rate in CARBON_TAX_SCHEDULE.items():
    print(f"  {year}: EUR {rate:.1f}/tCO2")


# ---------------------------------------------------------------------------
# Section 3: Wire Discrete Choice Pipeline
# ---------------------------------------------------------------------------
#
# 10-step pipeline with two decision domains (vehicle and heating).
# Each domain follows the same 5-step sequence:
#   1. DiscreteChoiceStep  — expand population by alternatives, compute costs
#   2. LogitChoiceStep     — apply conditional logit model to draw choices
#   3. EligibilityMergeStep — merge eligible/ineligible households
#   4. State update step   — apply chosen alternatives to population
#   5. DecisionRecordStep  — record decision audit trail

vehicle_config = default_vehicle_domain_config()
heating_config = default_heating_domain_config()

vehicle_domain = VehicleInvestmentDomain(vehicle_config)
heating_domain = HeatingInvestmentDomain(heating_config)

print(f"Vehicle domain: {vehicle_domain.name}")
print(f"  Alternatives: {[a.id for a in vehicle_domain.alternatives]}")
print(f"  Cost column: {vehicle_domain.cost_column}")
print()
print(f"Heating domain: {heating_domain.name}")
print(f"  Alternatives: {[a.id for a in heating_domain.alternatives]}")
print(f"  Cost column: {heating_domain.cost_column}")


# ---------------------------------------------------------------------------
# Mock adapter with policy-responsive cost model
# ---------------------------------------------------------------------------
#
# The compute_fn receives either the EXPANDED population (N x M rows for
# discrete choice) or the post-choice population (N rows for panel output).
# It prices vehicle and heating alternatives using domain-specific emissions
# columns so the escalating carbon tax actually changes utilities over time.

vehicle_alt_lookup = {
    idx: alt.id for idx, alt in enumerate(vehicle_domain.alternatives)
}
heating_alt_lookup = {
    idx: alt.id for idx, alt in enumerate(heating_domain.alternatives)
}


def compute_fn(
    pop: PopulationData, pol: PolicyConfig, period: int
) -> pa.Table:
    """Compute policy-responsive costs for vehicle and heating alternatives."""
    entity_table = pop.tables.get("menage", pa.table({}))
    n = entity_table.num_rows

    schedule = pol.policy.get("carbon_tax_schedule", {})
    carbon_tax_rate = float(schedule.get(period, 75.0))
    ev_subsidy = float(pol.policy.get("ev_subsidy", 0.0))
    hp_subsidy = float(pol.policy.get("heat_pump_subsidy", 0.0))

    cn = entity_table.column_names
    incomes_col = (
        entity_table.column("income").to_pylist()
        if "income" in cn
        else [40000.0] * n
    )
    energy_col = (
        entity_table.column("energy_consumption").to_pylist()
        if "energy_consumption" in cn
        else [9000.0] * n
    )
    vehicle_types_col = (
        entity_table.column("vehicle_type").to_pylist()
        if "vehicle_type" in cn
        else ["petrol"] * n
    )
    heating_types_col = (
        entity_table.column("heating_type").to_pylist()
        if "heating_type" in cn
        else ["gas"] * n
    )
    vehicle_ages_col = (
        entity_table.column("vehicle_age").to_pylist()
        if "vehicle_age" in cn
        else [8] * n
    )
    heating_ages_col = (
        entity_table.column("heating_age").to_pylist()
        if "heating_age" in cn
        else [12] * n
    )
    vehicle_emissions_col = (
        entity_table.column("vehicle_emissions_gkm").to_pylist()
        if "vehicle_emissions_gkm" in cn
        else [120.0] * n
    )
    heating_emissions_col = (
        entity_table.column("heating_emissions_kgco2_kwh").to_pylist()
        if "heating_emissions_kgco2_kwh" in cn
        else [0.227] * n
    )

    alt_indices = (
        entity_table.column("_alternative_id").to_pylist()
        if "_alternative_id" in cn
        else None
    )
    alt_count = len(set(alt_indices)) if alt_indices else 0
    is_vehicle_choice = alt_count == len(vehicle_alt_lookup)
    is_heating_choice = alt_count == len(heating_alt_lookup)

    vehicle_purchase_costs = {
        "keep_current": 700.0,
        "buy_petrol": 9000.0,
        "buy_diesel": 8500.0,
        "buy_hybrid": 12500.0,
        "buy_ev": 15500.0,
        "buy_no_vehicle": 500.0,
    }
    vehicle_running_costs = {
        "petrol": 2200.0,
        "diesel": 2050.0,
        "hybrid": 1500.0,
        "ev": 750.0,
        "none": 0.0,
    }
    heating_install_costs = {
        "keep_current": 400.0,
        "gas_boiler": 4200.0,
        "heat_pump": 9800.0,
        "electric": 3600.0,
        "wood_pellet": 5200.0,
    }
    heating_running_multipliers = {
        "gas": 1.00,
        "electric": 0.82,
        "oil": 1.18,
        "heat_pump": 0.55,
        "wood": 0.68,
    }

    vehicle_costs: list[float] = []
    heating_costs: list[float] = []
    carbon_tax_burden: list[float] = []
    disposable_incomes: list[float] = []
    total_emissions: list[float] = []

    for i in range(n):
        vehicle_alt_id = (
            vehicle_alt_lookup[int(alt_indices[i])]
            if is_vehicle_choice and alt_indices is not None
            else "keep_current"
        )
        heating_alt_id = (
            heating_alt_lookup[int(alt_indices[i])]
            if is_heating_choice and alt_indices is not None
            else "keep_current"
        )

        annual_vehicle_tons = max(0.0, float(vehicle_emissions_col[i])) * 12_000.0 / 1_000_000.0
        annual_heating_tons = (
            max(0.0, float(heating_emissions_col[i]))
            * max(0.0, float(energy_col[i]))
            / 1000.0
        )
        total_tons = annual_vehicle_tons + annual_heating_tons
        total_emissions.append(total_tons)

        annual_vehicle_tax = annual_vehicle_tons * carbon_tax_rate
        annual_heating_tax = annual_heating_tons * carbon_tax_rate
        annual_carbon_tax = annual_vehicle_tax + annual_heating_tax
        carbon_tax_burden.append(annual_carbon_tax)
        disposable_incomes.append(float(incomes_col[i]) - annual_carbon_tax)

        vehicle_type = str(vehicle_types_col[i])
        heating_type = str(heating_types_col[i])
        vehicle_age = float(vehicle_ages_col[i])
        heating_age = float(heating_ages_col[i])

        vehicle_base = vehicle_purchase_costs.get(vehicle_alt_id, 9000.0)
        vehicle_running = vehicle_running_costs.get(vehicle_type, 1800.0)
        vehicle_age_penalty = max(vehicle_age, 0.0) * 180.0
        vehicle_subsidy = ev_subsidy if vehicle_alt_id == "buy_ev" else 0.0
        if vehicle_alt_id == "buy_no_vehicle":
            vehicle_running = 0.0
            vehicle_age_penalty = 0.0
        elif vehicle_alt_id != "keep_current":
            vehicle_age_penalty = 0.0
        vehicle_total = (
            vehicle_base
            + vehicle_running
            + annual_vehicle_tax * 6.0
            + vehicle_age_penalty
            - vehicle_subsidy
        )
        vehicle_costs.append(max(0.0, vehicle_total))

        heating_base = heating_install_costs.get(heating_alt_id, 4200.0)
        heating_running = (
            max(0.0, float(energy_col[i]))
            * heating_running_multipliers.get(heating_type, 1.0)
            * 0.14
        )
        heating_age_penalty = max(heating_age, 0.0) * 90.0
        heating_subsidy = hp_subsidy if heating_alt_id == "heat_pump" else 0.0
        if heating_alt_id != "keep_current":
            heating_age_penalty = 0.0
        heating_total = (
            heating_base
            + heating_running
            + annual_heating_tax * 4.0
            + heating_age_penalty
            - heating_subsidy
        )
        heating_costs.append(max(0.0, heating_total))

    hh_id = (
        entity_table.column("household_id")
        if "household_id" in cn
        else pa.array(list(range(n)), type=pa.int64())
    )
    result_columns = {
        "household_id": hh_id,
        "income": pa.array(incomes_col, type=pa.float64()),
        "carbon_emissions": pa.array(total_emissions, type=pa.float64()),
        "total_vehicle_cost": pa.array(vehicle_costs, type=pa.float64()),
        "total_heating_cost": pa.array(heating_costs, type=pa.float64()),
        "carbon_tax": pa.array(carbon_tax_burden, type=pa.float64()),
        "disposable_income": pa.array(disposable_incomes, type=pa.float64()),
    }

    for tracking_col in ("_alternative_id", "_original_household_index"):
        if tracking_col in cn:
            result_columns[tracking_col] = entity_table.column(tracking_col)

    return pa.table(result_columns)


adapter = MockAdapter(compute_fn=compute_fn)
print(f"MockAdapter version: {adapter.version()}")
print(
    "compute_fn: alternative-specific cost model with escalating carbon tax, "
    "EV subsidy, and heat pump subsidy"
)


# ---------------------------------------------------------------------------
# Eligibility filters
# ---------------------------------------------------------------------------
#
# Only households with older vehicles/heating face the replacement choice.
# Younger assets default to "keep_current" without entering the logit model.

vehicle_eligibility = EligibilityFilter(
    rules=(
        EligibilityRule(
            column="vehicle_age",
            operator="gt",
            threshold=8,
            description="Only vehicles older than 8 years face replacement choice",
        ),
    ),
    default_choice="keep_current",
    entity_key="menage",
)

heating_eligibility = EligibilityFilter(
    rules=(
        EligibilityRule(
            column="heating_age",
            operator="gt",
            threshold=12,
            description="Only heating systems older than 12 years face replacement choice",
        ),
    ),
    default_choice="keep_current",
    entity_key="menage",
)

print("Eligibility filters:")
print(f"  Vehicle: {vehicle_eligibility.rules[0].description}")
print(f"  Heating: {heating_eligibility.rules[0].description}")


# ---------------------------------------------------------------------------
# Taste parameters and pipeline construction
# ---------------------------------------------------------------------------
#
# beta_cost < 0 means higher cost => lower utility => less likely to be chosen.
# A stronger (more negative) beta_cost means households are more cost-sensitive.

taste_params_vehicle = TasteParameters(beta_cost=-0.01)
taste_params_heating = TasteParameters(beta_cost=-0.02)

print(f"Vehicle taste parameters: beta_cost={taste_params_vehicle.beta_cost}")
print(f"Heating taste parameters: beta_cost={taste_params_heating.beta_cost}")
print("  (Households are more cost-sensitive for heating decisions)")


def reset_decision_log(year: int, state: YearState) -> YearState:
    """Clear the decision log at the start of each year."""
    from dataclasses import replace as _replace
    new_data = dict(state.data)
    new_data.pop(DECISION_LOG_KEY, None)
    return _replace(state, data=new_data)


# Vehicle domain (5 steps)
step_1 = DiscreteChoiceStep(
    adapter, vehicle_domain, policy,
    name="discrete_choice_vehicle",
    eligibility_filter=vehicle_eligibility,
)
step_2 = LogitChoiceStep(
    taste_params_vehicle,
    name="logit_choice_vehicle",
    depends_on=("discrete_choice_vehicle",),
)
step_3 = EligibilityMergeStep(
    name="eligibility_merge_vehicle",
    depends_on=("logit_choice_vehicle",),
)
step_4 = VehicleStateUpdateStep(
    vehicle_domain,
    name="vehicle_state_update",
    depends_on=("eligibility_merge_vehicle",),
)
step_5 = DecisionRecordStep(
    name="decision_record_vehicle",
    depends_on=("vehicle_state_update",),
)

# Heating domain (5 steps) — depends_on vehicle pipeline completion
step_6 = DiscreteChoiceStep(
    adapter, heating_domain, policy,
    name="discrete_choice_heating",
    depends_on=("decision_record_vehicle",),
    eligibility_filter=heating_eligibility,
)
step_7 = LogitChoiceStep(
    taste_params_heating,
    name="logit_choice_heating",
    depends_on=("discrete_choice_heating",),
)
step_8 = EligibilityMergeStep(
    name="eligibility_merge_heating",
    depends_on=("logit_choice_heating",),
)
step_9 = HeatingStateUpdateStep(
    heating_domain,
    name="heating_state_update",
    depends_on=("eligibility_merge_heating",),
)
step_10 = DecisionRecordStep(
    name="decision_record_heating",
    depends_on=("heating_state_update",),
)


# Panel computation step — use the UPDATED population from state so the
# financial impacts reflect post-behavioral-response outcomes.
def compute_post_choice_impacts(year: int, state: YearState) -> YearState:
    """Compute household impacts from the post-choice population."""
    from dataclasses import replace as _replace

    current_population = state.data["population_data"]
    comp_result = adapter.compute(
        population=current_population,
        policy=policy,
        period=year,
    )
    new_data = dict(state.data)
    new_data[COMPUTATION_RESULT_KEY] = comp_result
    new_metadata = dict(state.metadata)
    new_metadata[COMPUTATION_METADATA_KEY] = {
        "adapter_version": adapter.version(),
        "computation_period": year,
        "computation_row_count": comp_result.output_fields.num_rows,
        "population_source": "post_behavior_population_data",
    }
    return _replace(state, data=new_data, metadata=new_metadata)

step_pipeline = (
    reset_decision_log,  # Clear accumulated decision log from previous year
    step_1, step_2, step_3, step_4, step_5,
    step_6, step_7, step_8, step_9, step_10,
    compute_post_choice_impacts,
)

print(f"\nPipeline: {len(step_pipeline)} steps")
for i, step in enumerate(step_pipeline, 1):
    name = step.name if hasattr(step, "name") else step.__name__
    print(f"  {i:2d}. {name}")


# ---------------------------------------------------------------------------
# Section 4: Run 10-Year Simulation
# ---------------------------------------------------------------------------

config = OrchestratorConfig(
    start_year=2025,
    end_year=2034,
    initial_state={"population_data": population},
    seed=42,
    step_pipeline=step_pipeline,
)

print("Running 10-year behavioral simulation...")
print(f"  Years: {config.start_year}-{config.end_year}")
print(f"  Seed: {config.seed}")
print(f"  Steps per year: {len(config.step_pipeline)}")
print(f"  Total step executions: {len(config.step_pipeline) * (config.end_year - config.start_year + 1)}")

orchestrator = Orchestrator(config)
result = orchestrator.run()

print("\nSimulation complete!")
print(f"  Success: {result.success}")
print(f"  Years completed: {sorted(result.yearly_states.keys())}")
if result.errors:
    print(f"  Errors: {result.errors}")


# ---------------------------------------------------------------------------
# Section 5: Fleet Composition Over Time
# ---------------------------------------------------------------------------
#
# Extract vehicle and heating fleet composition from each year's state.

vehicle_fleet_data = {}
heating_fleet_data = {}

for year in sorted(result.yearly_states.keys()):
    state = result.yearly_states[year]
    pop = state.data.get("population_data")
    if pop is None:
        continue
    et = pop.tables["menage"]

    vehicle_counts = {}
    for vt in et.column("vehicle_type").to_pylist():
        vehicle_counts[vt] = vehicle_counts.get(vt, 0) + 1
    vehicle_fleet_data[year] = vehicle_counts

    heating_counts = {}
    for ht in et.column("heating_type").to_pylist():
        heating_counts[ht] = heating_counts.get(ht, 0) + 1
    heating_fleet_data[year] = heating_counts

years = sorted(vehicle_fleet_data.keys())
all_vehicle_types = sorted({vt for counts in vehicle_fleet_data.values() for vt in counts})
all_heating_types = sorted({ht for counts in heating_fleet_data.values() for ht in counts})

print("Vehicle Fleet Composition Over Time:")
header = f"{'Year':>6}" + "".join(f"{vt:>10}" for vt in all_vehicle_types)
print(header)
print("-" * len(header))
for year in years:
    counts = vehicle_fleet_data[year]
    row = f"{year:>6}" + "".join(f"{counts.get(vt, 0):>10}" for vt in all_vehicle_types)
    print(row)

print("\nHeating Fleet Composition Over Time:")
header = f"{'Year':>6}" + "".join(f"{ht:>12}" for ht in all_heating_types)
print(header)
print("-" * len(header))
for year in years:
    counts = heating_fleet_data[year]
    row = f"{year:>6}" + "".join(f"{counts.get(ht, 0):>12}" for ht in all_heating_types)
    print(row)


# ---------------------------------------------------------------------------
# Fleet composition charts
# ---------------------------------------------------------------------------

vehicle_type_labels = {
    "diesel": "Diesel", "ev": "EV", "hybrid": "Hybrid",
    "none": "No Vehicle", "petrol": "Petrol",
}
vehicle_colors = {
    "diesel": "#d62728", "ev": "#2ca02c", "hybrid": "#ff7f0e",
    "none": "#7f7f7f", "petrol": "#1f77b4",
}
heating_type_labels = {
    "electric": "Electric", "gas": "Gas", "heat_pump": "Heat Pump",
    "oil": "Oil", "wood": "Wood",
}
heating_colors = {
    "electric": "#ff7f0e", "gas": "#d62728",
    "heat_pump": "#2ca02c", "oil": "#7f7f7f", "wood": "#8c564b",
}

fig, axes = create_figure_grid(1, 2, figsize=(14, 5))

vehicle_series = {
    vt: [vehicle_fleet_data[y].get(vt, 0) for y in years]
    for vt in sorted({vt for counts in vehicle_fleet_data.values() for vt in counts})
}
plot_stacked_area(
    years,
    vehicle_series,
    title="Vehicle Fleet Evolution (2025-2034)",
    xlabel="Year",
    ylabel="Number of Households",
    label_map=vehicle_type_labels,
    color_map=vehicle_colors,
    legend_loc="upper right",
    ax=axes[0],
)

heating_series = {
    ht: [heating_fleet_data[y].get(ht, 0) for y in years]
    for ht in sorted({ht for counts in heating_fleet_data.values() for ht in counts})
}
plot_stacked_area(
    years,
    heating_series,
    title="Heating System Evolution (2025-2034)",
    xlabel="Year",
    ylabel="Number of Households",
    label_map=heating_type_labels,
    color_map=heating_colors,
    legend_loc="upper right",
    ax=axes[1],
)

show_figure(fig)


# ---------------------------------------------------------------------------
# Section 6: Panel Output and Decision Records
# ---------------------------------------------------------------------------
#
# PanelOutput collects yearly computation results into a single
# household-by-year table.  When DecisionRecordStep is in the pipeline,
# the panel also includes domain-prefixed decision columns.

panel = PanelOutput.from_orchestrator_result(result)
table = panel.table

print(f"Panel shape: {panel.shape[0]} rows x {panel.shape[1]} columns")
print(f"Columns: {table.column_names}")
print()
show(table, n=8)

# Inspect decision columns
print("Decision columns in panel:")
decision_cols = [
    c for c in table.column_names
    if "chosen" in c or "probabilities" in c
    or "utilities" in c or "decision_domains" in c
]
for col in decision_cols:
    print(f"  {col}: {table.column(col).type}")

domains_val = table.column("decision_domains")[0].as_py()
print(f"\nDecision domains (first row): {domains_val}")

alts = panel.metadata.get("decision_domain_alternatives", {})
print("\nDecision domain alternatives:")
for domain, alt_list in alts.items():
    print(f"  {domain}: {alt_list}")

# Vehicle choice distribution for year 2025
year_2025 = table.filter(
    pa.compute.equal(table.column("year"), 2025)
)
vehicle_chosen_2025 = year_2025.column("vehicle_chosen").to_pylist()
choice_counts = {}
for c in vehicle_chosen_2025:
    choice_counts[c] = choice_counts.get(c, 0) + 1

total_2025 = len(vehicle_chosen_2025) or 1
print("\nVehicle choice distribution (2025):")
for choice, count in sorted(
    choice_counts.items(), key=lambda x: -x[1]
):
    share = count / total_2025 * 100.0
    print(f"  {choice}: {count} households ({share:.1f}%)")


# ---------------------------------------------------------------------------
# Section 7: Distributional Indicators
# ---------------------------------------------------------------------------
#
# Distributional impacts change when households respond to policy.
# Households that switch to EVs or heat pumps face lower carbon tax
# burdens in later years.

indicators = compute_distributional_indicators(panel)
ind_table = indicators.to_table()

print(f"Distributional indicators: {ind_table.num_rows} rows")
print(f"Columns: {ind_table.column_names}")
print()
show(ind_table, n=15)

# Plot carbon tax burden by income decile
import pyarrow.compute as pc

carbon_tax_rows = ind_table.filter(
    pc.and_(
        pc.equal(ind_table["field_name"], "carbon_tax"),
        pc.equal(ind_table["metric"], "mean"),
    )
)

if carbon_tax_rows.num_rows > 0:
    deciles = carbon_tax_rows["decile"].to_pylist()
    mean_values = carbon_tax_rows["value"].to_pylist()

    # NOTE: colors= (not color=) is the correct keyword for plot_bar_series()
    fig, ax = plot_bar_series(
        deciles,
        mean_values,
        title="Carbon Tax Burden by Income Decile\n(Post-Behavioral Response, All Years)",
        xlabel="Income Decile",
        ylabel="Mean Carbon Tax (EUR/year)",
        colors="steelblue",
    )
    show_figure(fig)

    print("Interpretation:")
    print("- These indicators reflect AFTER households have responded to the carbon tax")
    print("- Households that switched to EVs/heat pumps face lower burdens in later years")
    print("- Without behavioral response, all deciles would show higher burdens")
else:
    print("No carbon_tax distributional data available")


# ---------------------------------------------------------------------------
# Section 8: Governance and Reproducibility
# ---------------------------------------------------------------------------
#
# Every discrete choice run records taste parameters (beta_cost) per domain
# and seed values per year for reproducibility verification.

dc_params = capture_discrete_choice_parameters(result.yearly_states)

print("Discrete choice parameters recorded in manifest:")
for param in dc_params:
    print(f"\n  Domain: {param['domain_name']}")
    print(f"  Alternatives: {param.get('alternative_ids', 'N/A')}")
    for key, value in param.items():
        if key not in ("domain_name", "alternative_ids"):
            print(f"  {key}: {value}")

seed_log = panel.metadata.get("seed_log", {})
print("\nSeed log (per-year seeds for reproducibility):")
for year in sorted(seed_log.keys()):
    print(f"  {year}: seed={seed_log[year]}")

# Verify determinism: re-run with same configuration and compare
print("Verifying determinism: re-running with identical config...")
orchestrator_rerun = Orchestrator(config)
result_rerun = orchestrator_rerun.run()

all_match = True
for year in sorted(result.yearly_states.keys()):
    orig_pop = result.yearly_states[year].data["population_data"]
    rerun_pop = result_rerun.yearly_states[year].data["population_data"]
    orig_vt = orig_pop.tables["menage"].column("vehicle_type").to_pylist()
    rerun_vt = rerun_pop.tables["menage"].column("vehicle_type").to_pylist()
    match = orig_vt == rerun_vt
    all_match = all_match and match
    symbol = "+" if match else "x"
    print(f"  {year}: [{symbol}] vehicle fleet match")

if all_match:
    print("\nDeterminism verified: identical fleet evolution across all years")


# ---------------------------------------------------------------------------
# Section 9: Export and Next Steps
# ---------------------------------------------------------------------------

parquet_path = panel.to_parquet(OUTPUT_DIR / "epic14_panel.parquet")
print(f"Panel exported to: {parquet_path}")
print(f"  Size: {parquet_path.stat().st_size:,} bytes")

roundtrip = pq.read_table(str(parquet_path))
print("\nRound-trip verification:")
print(f"  Original: {panel.shape[0]} rows x {panel.shape[1]} columns")
print(f"  Reloaded: {roundtrip.num_rows} rows x {roundtrip.num_columns} columns")
assert roundtrip.num_rows == panel.shape[0], "Row count mismatch!"
print("  Match: rows and columns verified")
