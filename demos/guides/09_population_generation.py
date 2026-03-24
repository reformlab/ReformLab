"""ReformLab Population Generation — French Household Example.

Demonstrates how to build a synthetic population from multiple institutional
data sources using statistical fusion methods:

1. Load institutional data sources (INSEE, Eurostat, ADEME, SDES)
2. Choose and apply merge methods: Uniform, IPF, and Conditional Sampling
3. Understand the assumptions behind each merge method
4. Validate the generated population against known marginals
5. Export the result for use in policy simulations
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pcsv
import pyarrow.parquet as pq

# ---------------------------------------------------------------------------
# Section 1: Setup and Imports
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR
while not (REPO_ROOT / "src").exists() and REPO_ROOT != REPO_ROOT.parent:
    REPO_ROOT = REPO_ROOT.parent

SRC_DIR = REPO_ROOT / "src"
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from reformlab.computation.ingestion import DataSchema
from reformlab.computation.types import PopulationData
from reformlab.data.descriptor import DatasetDescriptor
from reformlab.data.pipeline import DatasetManifest, DataSourceMetadata
from reformlab.population import (
    ConditionalSamplingMethod,
    IPFMergeMethod,
    MarginalConstraint,
    MergeConfig,
    PopulationPipeline,
    PopulationValidator,
    UniformMergeMethod,
)
from reformlab.population.loaders.base import CacheStatus, DataSourceLoader, SourceConfig
from reformlab.population.methods.base import IPFConstraint
from reformlab.visualization import (
    create_figure_grid,
    plot_bar_series,
    plot_histogram,
    show,
    show_figure,
)

# Resolve fixtures directory relative to repo root
FIXTURES_DIR = (REPO_ROOT / "tests" / "fixtures" / "populations" / "sources").resolve()

SEED = 42  # Deterministic seed for reproducibility

print("Population generation API loaded successfully!")


# ---------------------------------------------------------------------------
# Section 2: Load Data Sources
# ---------------------------------------------------------------------------
#
# Population generation starts with institutional data sources — publicly
# available datasets from government statistical agencies.  For this example
# we use four sources:
#
#   Filosofi 2021     | INSEE    | Commune-level income distribution
#   Energy consumption| Eurostat | Household energy consumption by fuel type
#   Vehicle fleet     | SDES     | Vehicle fleet by fuel type, age, region
#   Emission factors  | ADEME    | CO2 emission factors per energy source
#
# In production these are downloaded via factory functions with automatic
# caching.  Here we use fixture files so the script runs offline.


class FixtureLoader:
    """Loader that reads from a pre-built PyArrow table (fixture data).

    Satisfies the DataSourceLoader protocol.  In production you would use
    get_insee_loader(), get_eurostat_loader(), etc.
    """

    def __init__(self, table: pa.Table, dataset_id: str = "fixture") -> None:
        self._table = table
        self._dataset_id = dataset_id

    def download(self, config: SourceConfig) -> tuple[PopulationData, DatasetManifest]:
        pop_data = PopulationData.from_table(self._table)
        source = DataSourceMetadata(
            name=self._dataset_id,
            version="fixture",
            url=config.url,
            description=config.description,
        )
        sink = pa.BufferOutputStream()
        pq.write_table(self._table, sink)
        content_hash = hashlib.sha256(sink.getvalue().to_pybytes()).hexdigest()
        manifest = DatasetManifest(
            source=source,
            content_hash=content_hash,
            file_path=Path(f"<fixture:{self._dataset_id}>"),
            format="parquet",
            row_count=self._table.num_rows,
            column_names=tuple(self._table.column_names),
            loaded_at=datetime.now(UTC).isoformat(timespec="seconds"),
        )
        return pop_data, manifest

    def status(self, config: SourceConfig) -> CacheStatus:
        return CacheStatus(cached=True, path=None, downloaded_at=None, hash=None, stale=False)

    def descriptor(self) -> DatasetDescriptor:
        fields = self._table.schema
        required = tuple(fields.names)
        data_schema = DataSchema(
            schema=fields,
            required_columns=required,
        )
        return DatasetDescriptor(
            dataset_id=self._dataset_id,
            provider="fixture",
            description="In-memory fixture data for demo purposes",
            schema=data_schema,
        )


# Verify it satisfies the DataSourceLoader protocol
assert isinstance(FixtureLoader(pa.table({"a": [1]})), DataSourceLoader)
print("FixtureLoader satisfies the DataSourceLoader protocol")


# ---------------------------------------------------------------------------
# Load Source 1: INSEE Income Data
# ---------------------------------------------------------------------------
#
# The INSEE Filosofi dataset provides commune-level income distributions.
# We transform it into a household-level table with household_id, income,
# region, and income_decile columns.

raw_insee = pcsv.read_csv(FIXTURES_DIR / "insee_filosofi_2021_fixture.csv")
print(f"Raw INSEE data: {raw_insee.num_rows} communes, columns: {raw_insee.column_names}")

household_ids = list(range(raw_insee.num_rows))
incomes = raw_insee.column("median_income").to_pylist()
commune_codes = [str(c) for c in raw_insee.column("commune_code").to_pylist()]
regions = [code[:2] for code in commune_codes]
income_deciles = [str(min(10, (i * 10 // raw_insee.num_rows) + 1)) for i in range(raw_insee.num_rows)]

income_table = pa.table({
    "household_id": pa.array(household_ids, type=pa.int64()),
    "income": pa.array(incomes, type=pa.float64()),
    "region": pa.array(regions, type=pa.utf8()),
    "income_decile": pa.array(income_deciles, type=pa.utf8()),
})

income_loader = FixtureLoader(income_table)
income_config = SourceConfig(
    provider="insee", dataset_id="filosofi_2021_commune",
    url="fixture://insee", description="INSEE Filosofi 2021 (fixture)",
)

print(f"\nIncome source: {income_table.num_rows} households")
print(f"Columns: {income_table.column_names}")
print(f"Income range: {pc.min(income_table['income']).as_py():,.0f} - {pc.max(income_table['income']).as_py():,.0f} EUR")
print(f"Regions: {income_table['region'].unique().to_pylist()}")


# ---------------------------------------------------------------------------
# Load Source 2: Eurostat Housing Data
# ---------------------------------------------------------------------------
#
# The Eurostat nrg_d_hhq dataset provides household energy consumption by
# fuel type.  We derive housing attributes: household_size, housing_type,
# and heating_type.

raw_eurostat = pcsv.read_csv(FIXTURES_DIR / "eurostat_hhcomp_2022_fixture.csv")
print(f"Raw Eurostat data: {raw_eurostat.num_rows} rows, columns: {raw_eurostat.column_names}")

housing_table = pa.table({
    "household_size": pa.array([2, 3, 1, 4, 2, 3, 4, 1, 5, 2, 1, 3, 2, 2, 4], type=pa.int64()),
    "housing_type": pa.array(
        ["apartment", "house", "apartment", "house", "apartment",
         "house", "house", "apartment", "house", "apartment",
         "apartment", "house", "house", "apartment", "house"], type=pa.utf8()),
    "heating_type": pa.array(
        ["gas", "oil", "electric", "wood", "heat_pump",
         "gas", "oil", "electric", "wood", "gas",
         "electric", "electric", "gas", "oil", "heat_pump"], type=pa.utf8()),
})

housing_loader = FixtureLoader(housing_table)
housing_config = SourceConfig(
    provider="eurostat", dataset_id="nrg_d_hhq",
    url="fixture://eurostat", description="Eurostat household energy 2022 (fixture)",
)

print(f"\nHousing source: {housing_table.num_rows} profiles")
print(f"Columns: {housing_table.column_names}")
print(f"Housing types: {housing_table['housing_type'].unique().to_pylist()}")
print(f"Heating types: {housing_table['heating_type'].unique().to_pylist()}")


# ---------------------------------------------------------------------------
# Load Source 3: SDES Vehicle Fleet Data
# ---------------------------------------------------------------------------
#
# The SDES vehicle fleet dataset provides vehicle composition by fuel type,
# age bracket, and region.

raw_sdes = pcsv.read_csv(FIXTURES_DIR / "sdes_vehicles_2023_fixture.csv")
print(f"Raw SDES data: {raw_sdes.num_rows} rows, columns: {raw_sdes.column_names}")

age_map = {"De 1 a 5 ans": 3, "De 6 a 10 ans": 8, "De 11 a 15 ans": 13, "Plus de 15 ans": 18}
vehicle_ages = [age_map.get(a, 5) for a in raw_sdes.column("vehicle_age").to_pylist()]

vehicle_table = pa.table({
    "vehicle_type": raw_sdes.column("fuel_type"),
    "vehicle_age": pa.array(vehicle_ages, type=pa.int64()),
    "region": pa.array([str(r).zfill(2) for r in raw_sdes.column("departement_code").to_pylist()], type=pa.utf8()),
})

vehicle_loader = FixtureLoader(vehicle_table)
vehicle_config = SourceConfig(
    provider="sdes", dataset_id="vehicle_fleet_2023",
    url="fixture://sdes", description="SDES vehicle fleet 2023 (fixture)",
)

print(f"\nVehicle source: {vehicle_table.num_rows} records")
print(f"Columns: {vehicle_table.column_names}")
print(f"Vehicle types: {vehicle_table['vehicle_type'].unique().to_pylist()}")
print(f"Age range: {pc.min(vehicle_table['vehicle_age']).as_py()}-{pc.max(vehicle_table['vehicle_age']).as_py()} years")
print(f"Departements: {vehicle_table['region'].unique().to_pylist()}")


# ---------------------------------------------------------------------------
# Load Source 4: ADEME Energy/Emissions Data
# ---------------------------------------------------------------------------
#
# The ADEME Base Carbone provides CO2 emission factors per energy source.
# We derive energy_consumption (kWh) and carbon_emissions (kgCO2e) profiles.

raw_ademe = pcsv.read_csv(FIXTURES_DIR / "ademe_energy_2023_fixture.csv")
print(f"Raw ADEME data: {raw_ademe.num_rows} rows, columns: {raw_ademe.column_names}")

co2e_all = raw_ademe.column("total_co2e").to_pylist()
emission_factors = {
    "gas": co2e_all[0],       # 0.227 kgCO2e/kWh
    "electric": co2e_all[2],  # 0.0569 kgCO2e/kWh
    "wood": co2e_all[3],      # 0.030 kgCO2e/kWh
    "oil": co2e_all[4],       # 0.272 kgCO2e/kWh (GPL as oil proxy)
    "heat_pump": co2e_all[2] * 0.33,  # electric COP~3 effective factor
}
print(f"\nEmission factors (kgCO2e/kWh): {emission_factors}")

heating_types_energy = ["gas", "oil", "electric", "wood", "gas",
                        "electric", "oil", "gas", "heat_pump", "electric",
                        "wood", "heat_pump"]
energy_kwh = [8500.0, 12000.0, 5200.0, 6800.0, 9500.0,
              7200.0, 10500.0, 4800.0, 11000.0, 7800.0,
              6500.0, 9000.0]
carbon_emissions = [e * emission_factors[ht] for e, ht in zip(energy_kwh, heating_types_energy)]

energy_table = pa.table({
    "heating_type": pa.array(heating_types_energy, type=pa.utf8()),
    "energy_consumption": pa.array(energy_kwh, type=pa.float64()),
    "carbon_emissions": pa.array(carbon_emissions, type=pa.float64()),
})

energy_loader = FixtureLoader(energy_table)
energy_config = SourceConfig(
    provider="ademe", dataset_id="base_carbone_v23",
    url="fixture://ademe", description="ADEME Base Carbone V23.6 (fixture)",
)

print(f"\nEnergy source: {energy_table.num_rows} profiles")
print(f"Columns: {energy_table.column_names}")
print(f"Heating types: {energy_table['heating_type'].unique().to_pylist()}")
print(f"Energy range: {pc.min(energy_table['energy_consumption']).as_py():,.0f} - {pc.max(energy_table['energy_consumption']).as_py():,.0f} kWh")
print(f"Emissions range: {pc.min(energy_table['carbon_emissions']).as_py():,.1f} - {pc.max(energy_table['carbon_emissions']).as_py():,.1f} kgCO2e")


# ---------------------------------------------------------------------------
# Section 3: Build the Population Pipeline
# ---------------------------------------------------------------------------
#
# Combine the four sources into a single population using three merge steps.
# Each step uses a different statistical method with different assumptions.
#
# The PopulationPipeline builder uses a fluent pattern:
#   1. Add sources — register each data source with a label
#   2. Add merges — specify method, configuration
#   3. Execute    — run pipeline, get PipelineResult


# ---------------------------------------------------------------------------
# Merge Step 1: Income + Housing (Uniform Method)
# ---------------------------------------------------------------------------
#
# The Uniform method assumes statistical independence between sources.
# Each income household is randomly paired with a housing profile.
# This is the simplest fusion method — "like drawing a name from a hat."


# ---------------------------------------------------------------------------
# Merge Step 2: IPF (Iterative Proportional Fitting)
# ---------------------------------------------------------------------------
#
# IPF adjusts weights so that marginal totals match known targets
# while preserving correlation patterns from the initial match.


# ---------------------------------------------------------------------------
# Merge Step 3: Conditional Sampling (by heating_type)
# ---------------------------------------------------------------------------
#
# Matches energy consumption profiles to households based on their
# heating type.  Within each heating-type group, the match is random.

pipeline = (
    PopulationPipeline(description="French household population 2024")
    .add_source("income", loader=income_loader, config=income_config)
    .add_source("housing", loader=housing_loader, config=housing_config)
    .add_source("vehicles", loader=vehicle_loader, config=vehicle_config)
    .add_source("energy", loader=energy_loader, config=energy_config)
    # Merge Step 1: Uniform merge (income + housing)
    .add_merge(
        "income_housing",
        left="income",
        right="housing",
        method=UniformMergeMethod(),
        config=MergeConfig(
            seed=SEED,
            description="Uniform merge: income and housing are assumed independent",
        ),
    )
    # Merge Step 2: IPF merge (income_housing + vehicles)
    # IPF constraints must match actual region values in income table.
    # With only 15 rows we use a relaxed tolerance.
    .add_merge(
        "with_vehicles",
        left="income_housing",
        right="vehicles",
        method=IPFMergeMethod(
            constraints=(
                IPFConstraint(
                    dimension="region",
                    targets={
                        "75": 2.0, "69": 1.0, "13": 1.0,
                        "31": 1.0, "33": 1.0, "44": 1.0,
                        "67": 1.0, "59": 1.0, "06": 1.0,
                        "35": 1.0, "34": 1.0, "21": 1.0,
                        "38": 1.0, "76": 1.0,
                    },
                ),
            ),
            max_iterations=200,
            tolerance=1.5,  # Relaxed for small fixture data (15 rows)
        ),
        config=MergeConfig(
            seed=SEED,
            description="IPF merge: reweight to match regional vehicle fleet distribution",
            drop_right_columns=("region",),
        ),
    )
    # Merge Step 3: Conditional sampling (with_vehicles + energy, stratified by heating_type)
    .add_merge(
        "with_energy",
        left="with_vehicles",
        right="energy",
        method=ConditionalSamplingMethod(strata_columns=("heating_type",)),
        config=MergeConfig(
            seed=SEED,
            description="Conditional sampling: match energy profiles by heating type",
        ),
    )
)

print(f"Pipeline configured: {pipeline.step_count} steps")
print(f"Labels: {sorted(pipeline.labels)}")

print("\nExecuting pipeline...")
result = pipeline.execute()
print(f"Done! Result: {result.table.num_rows} rows, {result.table.num_columns} columns")
print(f"Columns: {result.table.column_names}")
print(f"Assumptions recorded: {len(result.assumption_chain)}")


# ---------------------------------------------------------------------------
# Merge Step 1 Result: Income Distribution
# ---------------------------------------------------------------------------

population = result.table
incomes_list = population.column("income").to_pylist()

fig, axes = create_figure_grid(1, 2, figsize=(12, 4))

plot_histogram(
    incomes_list,
    title="Income Distribution (After Merge Step 1)",
    xlabel="Median Income (EUR)",
    ylabel="Number of Households",
    bins=10,
    color="#2196F3",
    ax=axes[0],
)

housing_types_list = population.column("housing_type").to_pylist()
type_counts: dict[str, int] = {}
for ht in housing_types_list:
    type_counts[ht] = type_counts.get(ht, 0) + 1
labels = list(type_counts.keys())
counts = [type_counts[label] for label in labels]
plot_bar_series(
    labels,
    counts,
    title="Housing Type Distribution",
    xlabel="Housing Type",
    ylabel="Count",
    colors=["#FF9800", "#4CAF50"][: len(labels)],
    ax=axes[1],
)

show_figure(fig)

print(f"Merged population: {population.num_rows} households")
print(f"Income range: {min(incomes_list):,.0f} - {max(incomes_list):,.0f} EUR")
print(f"Housing type split: {type_counts}")


# ---------------------------------------------------------------------------
# Merge Step 2: Adding Vehicles (IPF Method)
# ---------------------------------------------------------------------------
#
# IPF adjusts matching weights so the final population matches known
# marginal totals while preserving correlation patterns from the seed.

fig, axes = create_figure_grid(1, 2, figsize=(12, 4))

vtypes = population.column("vehicle_type").to_pylist()
vtype_counts: dict[str, int] = {}
for vt in vtypes:
    vtype_counts[vt] = vtype_counts.get(vt, 0) + 1
vlabels = sorted(vtype_counts.keys())
vcounts = [vtype_counts[label] for label in vlabels]
plot_bar_series(
    vlabels,
    vcounts,
    title="Vehicle Fleet Composition (After IPF Merge)",
    xlabel="Vehicle Fuel Type",
    ylabel="Count",
    colors=["#E91E63", "#9C27B0", "#3F51B5", "#009688", "#FF5722"][: len(vlabels)],
    ax=axes[0],
)

vages = population.column("vehicle_age").to_pylist()
plot_histogram(
    vages,
    title="Vehicle Age Distribution",
    xlabel="Vehicle Age (years)",
    ylabel="Count",
    bins=range(0, 22, 2),
    color="#795548",
    ax=axes[1],
)

show_figure(fig)

print(f"Vehicle type distribution: {vtype_counts}")
print(f"Mean vehicle age: {sum(vages) / len(vages):.1f} years")


# ---------------------------------------------------------------------------
# Merge Step 3: Adding Energy/Emissions (Conditional Sampling)
# ---------------------------------------------------------------------------
#
# Conditional sampling matches energy consumption profiles to households
# based on their heating type.  Within each heating-type group the match
# is random (conditional independence within strata).

fig, axes = create_figure_grid(1, 2, figsize=(12, 4))

energy = population.column("energy_consumption").to_pylist()
emissions = population.column("carbon_emissions").to_pylist()

plot_histogram(
    energy,
    title="Energy Consumption Distribution",
    xlabel="Energy Consumption (kWh)",
    ylabel="Count",
    bins=10,
    color="#4CAF50",
    ax=axes[0],
)
plot_histogram(
    emissions,
    title="Carbon Emissions Distribution",
    xlabel="Carbon Emissions (kgCO2e)",
    ylabel="Count",
    bins=10,
    color="#F44336",
    ax=axes[1],
)

show_figure(fig)

print(f"Energy consumption: mean={sum(energy)/len(energy):,.0f} kWh")
print(f"Carbon emissions: mean={sum(emissions)/len(emissions):,.1f} kgCO2e")


# ---------------------------------------------------------------------------
# Pipeline Execution Log
# ---------------------------------------------------------------------------

print("Pipeline Step Log:")
print(f"{'Step':<6} {'Type':<8} {'Label':<20} {'Rows':<8} {'Method':<14} {'Duration (ms)'}")
print("-" * 78)
for step in result.step_log:
    print(
        f"{step.step_index:<6} {step.step_type:<8} {step.label:<20} "
        f"{step.output_rows:<8} {step.method_name or '-':<14} {step.duration_ms:.1f}"
    )

print(f"\nAssumption Chain ({len(result.assumption_chain)} records):")
for i, record in enumerate(result.assumption_chain):
    print(f"  [{i}] {record.assumption.method_name}: {record.assumption.statement}")


# ---------------------------------------------------------------------------
# Section 4: Validate the Population
# ---------------------------------------------------------------------------
#
# After generating a synthetic population, validate it against known
# marginal distributions.  The PopulationValidator checks whether the
# distribution of each attribute matches a reference within tolerance.

constraints = [
    MarginalConstraint(
        dimension="housing_type",
        distribution={"apartment": 0.50, "house": 0.50},
        tolerance=0.15,  # Allow 15% deviation (fixture data is small)
    ),
    MarginalConstraint(
        dimension="heating_type",
        distribution={
            "gas": 0.35, "electric": 0.25, "oil": 0.20,
            "wood": 0.10, "heat_pump": 0.10,
        },
        tolerance=0.15,
    ),
]

validator = PopulationValidator(constraints=constraints)
validation_result = validator.validate(result.table)

print(f"Validation: {'ALL PASSED' if validation_result.all_passed else 'SOME FAILED'}")
print(f"Total constraints: {validation_result.total_constraints}")
print(f"Failed: {validation_result.failed_count}\n")

for mr in validation_result.marginal_results:
    status = "PASS" if mr.passed else "FAIL"
    print(f"  [{status}] {mr.constraint.dimension} (tolerance={mr.constraint.tolerance})")
    print(f"        Max deviation: {mr.max_deviation:.4f}")
    print(f"        Expected: {mr.constraint.distribution}")
    print(f"        Observed: {mr.observed}")
    print()


# ---------------------------------------------------------------------------
# Section 5: Export and Governance Integration
# ---------------------------------------------------------------------------

export_dir = Path(tempfile.mkdtemp())
csv_path = export_dir / "french-household-example-2024.csv"
pcsv.write_csv(result.table, csv_path)
print(f"Population exported to CSV: {csv_path}")
print(f"  Size: {csv_path.stat().st_size:,} bytes")
print(f"  Rows: {result.table.num_rows}")
print(f"  Columns: {result.table.column_names}")

parquet_path = export_dir / "french-household-example-2024.parquet"
pq.write_table(result.table, parquet_path)
print(f"\nPopulation exported to Parquet: {parquet_path}")
print(f"  Size: {parquet_path.stat().st_size:,} bytes")

reloaded = pq.read_table(parquet_path)
assert reloaded.num_rows == result.table.num_rows
assert reloaded.column_names == result.table.column_names
print(f"  Round-trip verified: {reloaded.num_rows} rows, schema preserved")


# ---------------------------------------------------------------------------
# Governance: Assumption Chain
# ---------------------------------------------------------------------------
#
# Every merge operation records its methodological assumptions.  These can
# be exported to governance entries for the RunManifest.

entries = result.assumption_chain.to_governance_entries(
    source_label="french_household_example",
)
print(f"Governance entries: {len(entries)} records\n")

for entry in entries:
    print(f"Key: {entry['key']}")
    print(f"Source: {entry['source']}")
    print(f"Method: {entry['value']['method']}")
    print(f"Statement: {entry['value']['statement']}")
    print()

val_assumption = validation_result.to_assumption()
val_entry = val_assumption.to_governance_entry(source_label="population_validation")
print("Validation governance entry:")
print(json.dumps(val_entry, indent=2, default=str))
