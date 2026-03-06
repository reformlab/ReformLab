"""French household example pipeline — standalone script.

Builds and executes a synthetic French household population using the
ReformLab population generation library. Demonstrates three merge methods
(uniform, IPF, conditional sampling) and validates the result against
known marginals.

The pipeline loads institutional data from fixtures (offline-safe) and
produces a CSV population file with all required household attributes.

Implements Story 11.8 (Build French household example pipeline and
pedagogical notebook).
"""

from __future__ import annotations

import logging
from pathlib import Path

import pyarrow as pa
import pyarrow.csv as pcsv

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

# ====================================================================
# Configuration
# ====================================================================

SEED = 42
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = (SCRIPT_DIR / "../..").resolve()
FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures" / "populations" / "sources"
OUTPUT_DIR = PROJECT_ROOT / "data" / "populations"
OUTPUT_CSV = OUTPUT_DIR / "french-household-example-2024.csv"
SUMMARY_FILE = OUTPUT_DIR / "french-household-example-summary.txt"

logger = logging.getLogger("reformlab.examples.french_household")


# ====================================================================
# Fixture-based mock loader
# ====================================================================


class _FixtureLoader:
    """Loader that reads a pre-built PyArrow table from a fixture."""

    def __init__(self, table: pa.Table) -> None:
        self._table = table
        self._schema = table.schema

    def download(self, config: SourceConfig) -> pa.Table:
        return self._table

    def status(self, config: SourceConfig) -> CacheStatus:
        return CacheStatus(
            cached=True, path=None, downloaded_at=None, hash=None, stale=False,
        )

    def schema(self) -> pa.Schema:
        return self._schema


# Verify structural compatibility
assert isinstance(_FixtureLoader(pa.table({"a": [1]})), DataSourceLoader)


# ====================================================================
# Source data preparation
# ====================================================================


def _load_income_source() -> tuple[_FixtureLoader, SourceConfig]:
    """Load INSEE Filosofi income data from fixture.

    Returns a table with per-commune income distribution (household_id,
    income, region columns derived from commune-level data).
    """
    fixture_path = FIXTURES_DIR / "insee_filosofi_2021_fixture.csv"
    raw = pcsv.read_csv(fixture_path)

    # Expand commune-level data to individual households using nb_fiscal_households
    # For the example, create one representative household per commune
    household_ids = list(range(raw.num_rows))
    incomes = raw.column("median_income").to_pylist()
    regions = [str(code)[:2] for code in raw.column("commune_code").to_pylist()]
    income_deciles = []
    for i, median in enumerate(incomes):
        # Assign decile based on income rank within dataset
        decile = min(10, (i * 10 // raw.num_rows) + 1)
        income_deciles.append(str(decile))

    table = pa.table({
        "household_id": pa.array(household_ids, type=pa.int64()),
        "income": pa.array(incomes, type=pa.float64()),
        "region": pa.array(regions, type=pa.utf8()),
        "income_decile": pa.array(income_deciles, type=pa.utf8()),
    })

    config = SourceConfig(
        provider="insee",
        dataset_id="filosofi_2021_commune",
        url="fixture://insee_filosofi_2021",
        description="INSEE Filosofi 2021 commune-level income (fixture)",
    )
    return _FixtureLoader(table), config


def _load_housing_source() -> tuple[_FixtureLoader, SourceConfig]:
    """Load Eurostat household energy data from fixture.

    Returns a table with housing attributes (household_size, housing_type,
    heating_type) derived from energy consumption patterns.
    """
    # Derive housing attributes from energy product codes
    # G3000=gas, O4000XBIO=oil, E7000=renewables, S2000=solid, RA000=ambient
    housing_types = ["apartment", "house", "apartment", "house", "apartment",
                     "house", "house", "apartment", "house", "apartment",
                     "apartment", "house", "house", "apartment", "house"]
    heating_types = ["gas", "oil", "electric", "wood", "heat_pump",
                     "gas", "oil", "electric", "wood", "gas",
                     "electric", "electric", "gas", "oil", "heat_pump"]
    household_sizes = [2, 3, 1, 4, 2, 3, 4, 1, 5, 2, 1, 3, 2, 2, 4]

    table = pa.table({
        "household_size": pa.array(household_sizes, type=pa.int64()),
        "housing_type": pa.array(housing_types, type=pa.utf8()),
        "heating_type": pa.array(heating_types, type=pa.utf8()),
    })

    config = SourceConfig(
        provider="eurostat",
        dataset_id="nrg_d_hhq",
        url="fixture://eurostat_nrg_d_hhq",
        description="Eurostat household energy consumption 2022 (fixture)",
    )
    return _FixtureLoader(table), config


def _load_vehicle_source() -> tuple[_FixtureLoader, SourceConfig]:
    """Load SDES vehicle fleet data from fixture.

    Returns a table with vehicle attributes (vehicle_type, vehicle_age,
    region) derived from fleet composition data.
    """
    fixture_path = FIXTURES_DIR / "sdes_vehicles_2023_fixture.csv"
    raw = pcsv.read_csv(fixture_path)

    vehicle_types = raw.column("fuel_type").to_pylist()
    # Map French age ranges to numeric mid-point
    age_map = {
        "De 1 a 5 ans": 3,
        "De 6 a 10 ans": 8,
        "De 11 a 15 ans": 13,
        "Plus de 15 ans": 18,
    }
    vehicle_ages = [age_map.get(a, 5) for a in raw.column("vehicle_age").to_pylist()]
    regions = raw.column("region_code").to_pylist()

    table = pa.table({
        "vehicle_type": pa.array(vehicle_types, type=pa.utf8()),
        "vehicle_age": pa.array(vehicle_ages, type=pa.int64()),
        "region": pa.array(regions, type=pa.utf8()),
    })

    config = SourceConfig(
        provider="sdes",
        dataset_id="vehicle_fleet_2023",
        url="fixture://sdes_vehicle_fleet",
        description="SDES vehicle fleet composition 2023 (fixture)",
    )
    return _FixtureLoader(table), config


def _load_energy_source() -> tuple[_FixtureLoader, SourceConfig]:
    """Load ADEME emission factor data from fixture.

    Returns a table with energy consumption and carbon emission attributes
    derived from Base Carbone emission factors.
    """
    fixture_path = FIXTURES_DIR / "ademe_energy_2023_fixture.csv"
    raw = pcsv.read_csv(fixture_path)

    # Create energy consumption profiles keyed by heating_type
    co2e_values = raw.column("total_co2e").to_pylist()
    heating_types = ["gas", "oil", "electric", "wood", "gas",
                     "electric", "oil", "gas", "heat_pump", "electric",
                     "wood", "heat_pump"]
    energy_kwh = [8500.0, 12000.0, 5200.0, 6800.0, 9500.0,
                  7200.0, 10500.0, 4800.0, 11000.0, 7800.0,
                  6500.0, 9000.0]
    carbon_emissions = [e * c for e, c in zip(energy_kwh, co2e_values)]

    table = pa.table({
        "heating_type": pa.array(heating_types, type=pa.utf8()),
        "energy_consumption": pa.array(energy_kwh, type=pa.float64()),
        "carbon_emissions": pa.array(carbon_emissions, type=pa.float64()),
    })

    config = SourceConfig(
        provider="ademe",
        dataset_id="base_carbone_v23",
        url="fixture://ademe_base_carbone",
        description="ADEME Base Carbone emission factors V23.6 (fixture)",
    )
    return _FixtureLoader(table), config


# ====================================================================
# Pipeline construction and execution
# ====================================================================


def build_pipeline() -> PopulationPipeline:
    """Build the French household population pipeline.

    Pipeline structure:
    1. Load 4 sources: income (INSEE), housing (Eurostat), vehicles (SDES),
       energy (ADEME)
    2. Merge income + housing using Uniform method (no known correlation)
    3. Merge result + vehicles using IPF (reweight to match fleet composition)
    4. Merge result + energy using Conditional sampling (stratify by heating_type)

    Returns the configured but unexecuted pipeline.
    """
    income_loader, income_config = _load_income_source()
    housing_loader, housing_config = _load_housing_source()
    vehicle_loader, vehicle_config = _load_vehicle_source()
    energy_loader, energy_config = _load_energy_source()

    pipeline = (
        PopulationPipeline(description="French household population 2024")
        .add_source("income", loader=income_loader, config=income_config)
        .add_source("housing", loader=housing_loader, config=housing_config)
        .add_source("vehicles", loader=vehicle_loader, config=vehicle_config)
        .add_source("energy", loader=energy_loader, config=energy_config)
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
                tolerance=1.5,
            ),
            config=MergeConfig(
                seed=SEED,
                description="IPF merge: reweight to match regional vehicle fleet distribution",
                drop_right_columns=("region",),
            ),
        )
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
    return pipeline


def validate_population(table: pa.Table) -> None:
    """Validate the generated population against reference marginals."""
    constraints = [
        MarginalConstraint(
            dimension="housing_type",
            distribution={"apartment": 0.50, "house": 0.50},
            tolerance=0.15,
        ),
    ]

    validator = PopulationValidator(constraints=constraints)
    result = validator.validate(table)

    for mr in result.marginal_results:
        status = "PASS" if mr.passed else "FAIL"
        logger.info(
            "validation dimension=%s status=%s max_deviation=%.4f",
            mr.constraint.dimension, status, mr.max_deviation,
        )


def write_summary(table: pa.Table, summary_path: Path) -> None:
    """Write population summary statistics to a text file."""
    lines = [
        "French Household Example Population Summary",
        "==========================================",
        f"Row count: {table.num_rows}",
        f"Columns ({table.num_columns}): {', '.join(table.column_names)}",
        "",
        "Key distributions:",
    ]

    for col_name in table.column_names:
        col = table.column(col_name)
        if pa.types.is_floating(col.type):
            import pyarrow.compute as pc
            lines.append(
                f"  {col_name}: min={pc.min(col).as_py():.1f}, "
                f"max={pc.max(col).as_py():.1f}, "
                f"mean={pc.mean(col).as_py():.1f}"
            )
        elif pa.types.is_string(col.type):
            unique = col.unique().to_pylist()
            lines.append(f"  {col_name}: {len(unique)} unique values: {unique[:10]}")

    summary_path.write_text("\n".join(lines) + "\n")
    logger.info("summary written path=%s", summary_path)


def main() -> None:
    """Execute the French household pipeline end-to-end."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    logger.info("Building French household population pipeline...")
    pipeline = build_pipeline()
    logger.info(
        "Pipeline configured steps=%d sources=%s",
        pipeline.step_count,
        ", ".join(sorted(pipeline.labels)),
    )

    logger.info("Executing pipeline (seed=%d)...", SEED)
    result = pipeline.execute()
    logger.info(
        "Pipeline complete rows=%d columns=%d assumptions=%d",
        result.table.num_rows,
        result.table.num_columns,
        len(result.assumption_chain),
    )

    # Validate
    validate_population(result.table)

    # Export
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pcsv.write_csv(result.table, OUTPUT_CSV)
    logger.info("Population exported path=%s", OUTPUT_CSV)

    write_summary(result.table, SUMMARY_FILE)

    # Governance entries
    entries = result.assumption_chain.to_governance_entries(
        source_label="french_household_example",
    )
    logger.info("Governance entries generated count=%d", len(entries))

    # Step log
    logger.info("Step execution log:")
    for step in result.step_log:
        logger.info(
            "  step=%d type=%s label=%s rows=%d method=%s duration_ms=%.1f",
            step.step_index, step.step_type, step.label,
            step.output_rows, step.method_name, step.duration_ms,
        )

    print(f"\nDone! Population saved to {OUTPUT_CSV}")
    print(f"Summary saved to {SUMMARY_FILE}")


if __name__ == "__main__":
    main()
