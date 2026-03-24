"""Epic 13 Demo — Custom Policy Templates in Portfolios.

Demonstrates the custom template lifecycle: defining, registering, and
deploying custom policy templates in production portfolios.

Epic 2 gave us built-in policy templates (carbon tax, subsidy, rebate,
feebate). Epic 13 adds:

1. Custom template authoring — define your own frozen dataclass extending PolicyParameters
2. Registration API — register_policy_type() + register_custom_template()
3. Built-in custom templates — vehicle malus and energy poverty aid
4. Portfolio integration — mix custom and built-in templates in PolicyPortfolio
"""
from __future__ import annotations

import random
import sys
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Setup: resolve paths and add src/ to sys.path
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR
while not (REPO_ROOT / "src").exists() and REPO_ROOT != REPO_ROOT.parent:
    REPO_ROOT = REPO_ROOT.parent

SRC_DIR = REPO_ROOT / "src"
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import pyarrow as pa

from reformlab.templates.schema import (
    BaselineScenario,
    PolicyParameters,
    YearSchedule,
    infer_policy_type,
    register_custom_template,
    register_policy_type,
)
from reformlab.visualization import show

OUTPUT_DIR = SCRIPT_DIR / "data" / "epic13_outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"Repo root:  {REPO_ROOT}")
print(f"Output dir: {OUTPUT_DIR}")


# ---------------------------------------------------------------------------
# Section 2: The Custom Template Lifecycle
# ---------------------------------------------------------------------------
#
# The custom template API follows four steps:
#
#   1. Define a frozen dataclass   -> subclass PolicyParameters
#   2. Register policy type        -> register_policy_type("my_type")
#   3. Register template class     -> register_custom_template(type, MyParams)
#   4. Use in scenario/portfolio   -> infer_policy_type() resolves automatically
#
# Once registered, custom templates are indistinguishable from built-in
# types in scenarios, portfolios, and YAML serialization.


# ---------------------------------------------------------------------------
# Section 3: Define a Custom Template
# ---------------------------------------------------------------------------
#
# A simple custom template — a parking levy that charges a flat fee per
# vehicle based on urban zone.  Deliberately minimal to focus on the
# registration API, not computation logic.


@dataclass(frozen=True)
class ParkingLevyParameters(PolicyParameters):
    """Parking levy — flat charge per vehicle based on urban zone.

    Fields:
        levy_per_vehicle: EUR per vehicle per year.
    """

    levy_per_vehicle: float = 120.0

    def __post_init__(self) -> None:
        if self.levy_per_vehicle < 0:
            raise ValueError(
                f"levy_per_vehicle must be >= 0, got {self.levy_per_vehicle}"
            )


# Verify it's a proper PolicyParameters subclass
print(f"Is PolicyParameters subclass: {issubclass(ParkingLevyParameters, PolicyParameters)}")
print(f"Instance: {ParkingLevyParameters(rate_schedule={2026: 120.0})}")


# ---------------------------------------------------------------------------
# Section 4: Register and Use
# ---------------------------------------------------------------------------
#
# After registration:
# - infer_policy_type() resolves our class to the registered type
# - BaselineScenario accepts it as a valid policy
# - Portfolios can include it alongside built-in types

# Step 1: Register the policy type name
parking_type = register_policy_type("parking_levy")
print(f"Registered type: {parking_type}")

# Step 2: Link our class to the registered type
register_custom_template(parking_type, ParkingLevyParameters)
print("Template class registered: ParkingLevyParameters")

# Step 3: Verify inference works
policy = ParkingLevyParameters(
    rate_schedule={2026: 120.0, 2027: 130.0},
    levy_per_vehicle=150.0,
)
inferred = infer_policy_type(policy)
print(f"Inferred type: {inferred.value}")

# Step 4: Use in a BaselineScenario
scenario = BaselineScenario(
    name="Parking Levy 2026",
    year_schedule=YearSchedule(start_year=2026, end_year=2030),
    policy=policy,
)
print(f"Scenario: {scenario.name}, policy_type={scenario.policy_type.value}")


# ---------------------------------------------------------------------------
# Section 5: Built-in Custom Templates
# ---------------------------------------------------------------------------
#
# ReformLab ships two custom templates registered at import time:
#   - Vehicle malus (VehicleMalusParameters) — emission penalty
#   - Energy poverty aid (EnergyPovertyAidParameters) — income-conditioned aid

from reformlab.templates.vehicle_malus import (
    VehicleMalusParameters,
    compute_vehicle_malus,
    aggregate_vehicle_malus_by_decile,
    vehicle_malus_decile_results_to_table,
)
from reformlab.templates.energy_poverty_aid import (
    EnergyPovertyAidParameters,
    compute_energy_poverty_aid,
    aggregate_energy_poverty_aid_by_decile,
    energy_poverty_aid_decile_results_to_table,
)

print(f"Vehicle malus type: {infer_policy_type(VehicleMalusParameters(rate_schedule={2026: 50.0})).value}")
print(f"Energy poverty aid type: {infer_policy_type(EnergyPovertyAidParameters(rate_schedule={2026: 0.0})).value}")


# ---------------------------------------------------------------------------
# Create synthetic population
# ---------------------------------------------------------------------------
#
# 100 households with income, carbon emissions, vehicle emissions, and
# energy expenditure.  Distributions tuned so that:
# - ~40% exceed the vehicle malus emission threshold (118 gCO2/km)
# - ~30% qualify for energy poverty aid (income < 11,000 AND energy_share >= 8%)

random.seed(42)
NUM_HOUSEHOLDS = 100

hh_incomes = [5000.0 + i * 750.0 + random.gauss(0, 1500) for i in range(NUM_HOUSEHOLDS)]
hh_incomes = [max(2000.0, inc) for inc in hh_incomes]

hh_carbon = [2.0 + random.gauss(0, 1.5) + i * 0.04 for i in range(NUM_HOUSEHOLDS)]
hh_carbon = [max(0.5, c) for c in hh_carbon]

hh_vehicle = [90.0 + random.gauss(0, 40) + i * 0.8 for i in range(NUM_HOUSEHOLDS)]
hh_vehicle = [max(60.0, v) for v in hh_vehicle]

hh_energy = [
    max(100.0, inc * 0.06 + random.gauss(200, 150))
    if inc < 15000
    else max(100.0, 500 + random.gauss(0, 200))
    for inc in hh_incomes
]

population = pa.table({
    "household_id": pa.array(list(range(NUM_HOUSEHOLDS)), type=pa.int64()),
    "income": pa.array(hh_incomes, type=pa.float64()),
    "carbon_emissions": pa.array(hh_carbon, type=pa.float64()),
    "vehicle_emissions_gkm": pa.array(hh_vehicle, type=pa.float64()),
    "energy_expenditure": pa.array(hh_energy, type=pa.float64()),
})

print(f"Population: {population.num_rows} households, {population.num_columns} columns")
print(f"Columns: {population.column_names}")
show(population, n=5)


# ---------------------------------------------------------------------------
# Compute vehicle malus
# ---------------------------------------------------------------------------
#
# Penalizes households whose vehicle emissions exceed the threshold
# (default 118 gCO2/km).  Malus = max(0, emissions - threshold) * rate_per_gkm.

malus_policy = VehicleMalusParameters(
    rate_schedule={2026: 50.0},
    emission_threshold=118.0,
    malus_rate_per_gkm=50.0,
)

malus_result = compute_vehicle_malus(population, malus_policy, year=2026, template_name="vehicle-malus")
print(f"Total malus revenue: EUR {malus_result.total_revenue:,.2f}")

malus_deciles = aggregate_vehicle_malus_by_decile(malus_result)
malus_table = vehicle_malus_decile_results_to_table(malus_deciles)
print("\nVehicle malus by income decile:")
show(malus_table)


# ---------------------------------------------------------------------------
# Compute energy poverty aid
# ---------------------------------------------------------------------------
#
# Targets households with low income (< income_ceiling) and high energy
# burden (energy expenditure / income >= threshold).

aid_policy = EnergyPovertyAidParameters(
    rate_schedule={2026: 0.0},
    income_ceiling=11000.0,
    energy_share_threshold=0.08,
    base_aid_amount=150.0,
)

aid_result = compute_energy_poverty_aid(population, aid_policy, year=2026, template_name="energy-aid")
print(f"Total aid cost: EUR {aid_result.total_cost:,.2f}")
print(f"Eligible households: {aid_result.eligible_count} / {NUM_HOUSEHOLDS}")

aid_deciles = aggregate_energy_poverty_aid_by_decile(aid_result)
aid_table = energy_poverty_aid_decile_results_to_table(aid_deciles)
print("\nEnergy poverty aid by income decile:")
show(aid_table)


# ---------------------------------------------------------------------------
# Section 6: Portfolios with Custom Templates
# ---------------------------------------------------------------------------
#
# Custom templates integrate seamlessly into portfolios alongside built-in
# types.  Here we compose a "Green Transition" portfolio:
#
#   Carbon tax     — Built-in — Revenue from carbon pricing
#   Vehicle malus  — Custom   — Penalize high-emission vehicles
#   Energy poverty — Custom   — Protect low-income households

from reformlab.templates.schema import CarbonTaxParameters
from reformlab.templates.portfolios.portfolio import PolicyConfig, PolicyPortfolio
from reformlab.templates.portfolios.composition import validate_compatibility

carbon_params = CarbonTaxParameters(rate_schedule={2026: 44.6, 2027: 50.0})
malus_params = VehicleMalusParameters(rate_schedule={2026: 50.0, 2027: 55.0})
aid_params = EnergyPovertyAidParameters(
    rate_schedule={2026: 0.0, 2027: 0.0},
    income_ceiling=11000.0,
    energy_share_threshold=0.08,
    base_aid_amount=150.0,
)

green_portfolio = PolicyPortfolio(
    name="green-transition",
    policies=(
        PolicyConfig(
            policy_type=infer_policy_type(carbon_params),
            policy=carbon_params,
            name="carbon-tax",
        ),
        PolicyConfig(
            policy_type=infer_policy_type(malus_params),
            policy=malus_params,
            name="vehicle-malus",
        ),
        PolicyConfig(
            policy_type=infer_policy_type(aid_params),
            policy=aid_params,
            name="energy-aid",
        ),
    ),
)

print(f"Portfolio: {green_portfolio.name}")
print(f"Policies: {green_portfolio.policy_count}")
for p in green_portfolio.policies:
    print(f"  - {p.name} ({p.policy_type.value})")

conflicts = validate_compatibility(green_portfolio)
print(f"\nConflicts: {len(conflicts)}")
if not conflicts:
    print("No conflicts — all policy types are distinct.")


# ---------------------------------------------------------------------------
# Section 7: Compare Portfolios
# ---------------------------------------------------------------------------
#
# Compare vehicle malus scenarios: standard vs strict threshold.

from reformlab.templates.vehicle_malus import (
    run_vehicle_malus_batch,
    compare_vehicle_malus_decile_impacts,
)
from reformlab.templates.energy_poverty_aid import (
    run_energy_poverty_aid_batch,
    compare_energy_poverty_aid_decile_impacts,
)

malus_standard = BaselineScenario(
    name="Standard Malus",
    year_schedule=YearSchedule(start_year=2026, end_year=2026),
    policy=VehicleMalusParameters(
        rate_schedule={2026: 50.0},
        emission_threshold=118.0,
    ),
)
malus_strict = BaselineScenario(
    name="Strict Malus",
    year_schedule=YearSchedule(start_year=2026, end_year=2026),
    policy=VehicleMalusParameters(
        rate_schedule={2026: 75.0},
        emission_threshold=100.0,
    ),
)

malus_batch = run_vehicle_malus_batch(population, [malus_standard, malus_strict], year=2026)
malus_comparison = compare_vehicle_malus_decile_impacts(malus_batch)
print("Vehicle malus comparison — Standard vs Strict:")
show(malus_comparison.comparison_table)


# ---------------------------------------------------------------------------
# Energy poverty aid comparison — standard vs generous ceiling
# ---------------------------------------------------------------------------

aid_standard = BaselineScenario(
    name="Standard Aid",
    year_schedule=YearSchedule(start_year=2026, end_year=2026),
    policy=EnergyPovertyAidParameters(
        rate_schedule={2026: 0.0},
        income_ceiling=11000.0,
        base_aid_amount=150.0,
    ),
)
aid_generous = BaselineScenario(
    name="Generous Aid",
    year_schedule=YearSchedule(start_year=2026, end_year=2026),
    policy=EnergyPovertyAidParameters(
        rate_schedule={2026: 0.0},
        income_ceiling=15000.0,
        base_aid_amount=250.0,
    ),
)

aid_batch = run_energy_poverty_aid_batch(population, [aid_standard, aid_generous], year=2026)
aid_comparison = compare_energy_poverty_aid_decile_impacts(aid_batch)
print("Energy poverty aid comparison — Standard vs Generous:")
show(aid_comparison.comparison_table)


# ---------------------------------------------------------------------------
# Section 8: YAML Round-Trip
# ---------------------------------------------------------------------------
#
# Portfolios with custom templates can be serialized to YAML and reloaded
# with all custom fields preserved.

from reformlab.templates.portfolios.composition import dump_portfolio, load_portfolio

yaml_path = OUTPUT_DIR / "green_transition_portfolio.yaml"
dump_portfolio(green_portfolio, yaml_path)
print(f"Portfolio saved to: {yaml_path.name}")

print("\nYAML content:")
print(yaml_path.read_text(encoding="utf-8"))

# Reload from YAML — custom template modules must be imported first
# so that registration side effects have run
import reformlab.templates.vehicle_malus  # noqa: F401
import reformlab.templates.energy_poverty_aid  # noqa: F401

reloaded = load_portfolio(yaml_path, validate=False)
print(f"Reloaded portfolio: {reloaded.name}")
print(f"Policies: {reloaded.policy_count}")

for p in reloaded.policies:
    print(f"  - {p.name} ({p.policy_type.value}): {type(p.policy).__name__}")

reloaded_malus = reloaded.policies[1].policy
original_malus = green_portfolio.policies[1].policy
print(f"\nVehicle malus emission_threshold preserved: {reloaded_malus.emission_threshold == original_malus.emission_threshold}")

reloaded_aid = reloaded.policies[2].policy
original_aid = green_portfolio.policies[2].policy
print(f"Energy poverty aid income_ceiling preserved: {reloaded_aid.income_ceiling == original_aid.income_ceiling}")


# ---------------------------------------------------------------------------
# Section 9: Export and Verify
# ---------------------------------------------------------------------------

import pyarrow.csv as pcsv
import pyarrow.parquet as pq

malus_csv = OUTPUT_DIR / "malus_comparison.csv"
malus_parquet = OUTPUT_DIR / "malus_comparison.parquet"
pcsv.write_csv(malus_comparison.comparison_table, str(malus_csv))
pq.write_table(malus_comparison.comparison_table, str(malus_parquet))

aid_csv = OUTPUT_DIR / "aid_comparison.csv"
aid_parquet = OUTPUT_DIR / "aid_comparison.parquet"
pcsv.write_csv(aid_comparison.comparison_table, str(aid_csv))
pq.write_table(aid_comparison.comparison_table, str(aid_parquet))

# Round-trip verification
malus_rt = pq.read_table(str(malus_parquet))
assert malus_rt.num_rows == malus_comparison.comparison_table.num_rows
aid_rt = pq.read_table(str(aid_parquet))
assert aid_rt.num_rows == aid_comparison.comparison_table.num_rows

print("Exported files:")
for path in sorted(OUTPUT_DIR.iterdir()):
    print(f"  {path.name}")
print("\nRound-trip verification: OK")
