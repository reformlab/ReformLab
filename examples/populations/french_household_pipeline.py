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
import pyarrow.compute as pc
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
from reformlab.computation.ingestion import DataSchema
from reformlab.computation.types import PopulationData
from reformlab.data.descriptor import DataAssetDescriptor, DatasetDescriptor
from reformlab.data.pipeline import DataSourceMetadata, DatasetManifest
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
EVIDENCE_MANIFEST_FILE = OUTPUT_DIR / "french-household-example-evidence-manifest.json"

logger = logging.getLogger("reformlab.examples.french_household")


# ====================================================================
# Fixture-based mock loader
# ====================================================================


class _FixtureLoader:
    """Loader that reads a pre-built PyArrow table from a fixture."""

    def __init__(self, table: pa.Table, *, dataset_id: str = "fixture") -> None:
        self._table = table
        self._schema = table.schema
        self._dataset_id = dataset_id

    def download(self, config: SourceConfig) -> tuple[PopulationData, DatasetManifest]:
        import hashlib
        from datetime import UTC, datetime

        population = PopulationData.from_table(self._table, entity_type="default")
        manifest = DatasetManifest(
            source=DataSourceMetadata(
                name=self._dataset_id,
                version="fixture",
                url="",
                description="fixture data",
            ),
            content_hash=hashlib.sha256(b"fixture").hexdigest(),
            file_path=Path("<fixture>"),
            format="parquet",
            row_count=self._table.num_rows,
            column_names=tuple(self._table.column_names),
            loaded_at=datetime.now(UTC).isoformat(timespec="seconds"),
        )
        return population, manifest

    def status(self, config: SourceConfig) -> CacheStatus:
        return CacheStatus(
            cached=True, path=None, downloaded_at=None, hash=None, stale=False,
        )

    def descriptor(self) -> DatasetDescriptor:
        all_cols = tuple(self._schema.names)
        return DatasetDescriptor(
            dataset_id=self._dataset_id,
            provider="fixture",
            description="fixture data",
            schema=DataSchema(
                schema=self._schema,
                required_columns=all_cols,
            ),
        )


# Verify structural compatibility
assert isinstance(_FixtureLoader(pa.table({"a": [1]})), DataSourceLoader)


# ====================================================================
# Fixture integrity guards
# ====================================================================


def _assert_fixture(condition: bool, *, fixture: str, detail: str) -> None:
    """Raise a clear error when fixture semantics do not match expectations."""
    if not condition:
        raise ValueError(
            f"Fixture semantic integrity check failed for {fixture}: {detail}"
        )


def _assert_insee_fixture_identity(raw: pa.Table) -> None:
    fixture = "insee_filosofi_2021_fixture"
    required = {
        "commune_code",
        "median_income",
        "decile_1",
        "decile_5",
        "decile_9",
    }
    missing = required.difference(raw.column_names)
    _assert_fixture(
        not missing,
        fixture=fixture,
        detail=f"missing required columns: {sorted(missing)}",
    )

    commune_codes = []
    for code in raw.column("commune_code").to_pylist():
        if code is None:
            commune_codes.append("")
            continue
        code_str = str(code)
        if code_str.isdigit():
            code_str = code_str.zfill(5)
        commune_codes.append(code_str)
    _assert_fixture(
        all(code.isdigit() and len(code) == 5 for code in commune_codes),
        fixture=fixture,
        detail="commune_code must use 5-digit INSEE commune codes",
    )

    median = raw.column("median_income").to_pylist()
    decile_1 = raw.column("decile_1").to_pylist()
    decile_9 = raw.column("decile_9").to_pylist()
    _assert_fixture(
        all(
            d1 is not None and med is not None and d9 is not None and d1 < med < d9
            for d1, med, d9 in zip(decile_1, median, decile_9)
        ),
        fixture=fixture,
        detail="income deciles must bracket median_income for every commune",
    )

    sentinel_ok = any(
        code == "75101" and float(med) == 32000.0
        for code, med in zip(commune_codes, median)
    )
    _assert_fixture(
        sentinel_ok,
        fixture=fixture,
        detail="expected Paris 1er sentinel row (commune_code=75101, median_income=32000.0)",
    )


def _assert_eurostat_fixture_identity(raw: pa.Table) -> None:
    fixture = "eurostat_hhcomp_2022_fixture"
    required = {"country", "energy_product", "time_period", "value"}
    missing = required.difference(raw.column_names)
    _assert_fixture(
        not missing,
        fixture=fixture,
        detail=f"missing required columns: {sorted(missing)}",
    )

    countries = set(raw.column("country").to_pylist())
    _assert_fixture(
        {"FR", "DE"}.issubset(countries),
        fixture=fixture,
        detail="expected FR and DE rows for cross-country energy context",
    )

    products = raw.column("energy_product").to_pylist()
    periods = raw.column("time_period").to_pylist()
    values = raw.column("value").to_pylist()
    sentinel_ok = any(
        country == "FR" and product == "G3000" and int(period) == 2022 and float(value) == 155.2
        for country, product, period, value in zip(
            raw.column("country").to_pylist(),
            products,
            periods,
            values,
        )
    )
    _assert_fixture(
        sentinel_ok,
        fixture=fixture,
        detail="expected FR G3000 2022 sentinel value 155.2",
    )


def _assert_sdes_fixture_identity(raw: pa.Table) -> None:
    fixture = "sdes_vehicles_2023_fixture"
    required = {"region_code", "departement_code", "fuel_type", "fleet_count_2022"}
    missing = required.difference(raw.column_names)
    _assert_fixture(
        not missing,
        fixture=fixture,
        detail=f"missing required columns: {sorted(missing)}",
    )

    fuel_types = set(str(f) for f in raw.column("fuel_type").to_pylist())
    _assert_fixture(
        {"Diesel", "Essence", "Electrique"}.issubset(fuel_types),
        fixture=fixture,
        detail="expected fuel types Diesel/Essence/Electrique",
    )

    sentinel_ok = any(
        int(dep) == 75 and str(fuel) == "Diesel" and float(count) == 520000.0
        for dep, fuel, count in zip(
            raw.column("departement_code").to_pylist(),
            raw.column("fuel_type").to_pylist(),
            raw.column("fleet_count_2022").to_pylist(),
        )
    )
    _assert_fixture(
        sentinel_ok,
        fixture=fixture,
        detail="expected Ile-de-France diesel sentinel row (departement_code=75, fleet_count_2022=520000)",
    )


def _assert_ademe_fixture_identity(raw: pa.Table) -> None:
    fixture = "ademe_energy_2023_fixture"
    required = {"name_fr", "unit_fr", "total_co2e"}
    missing = required.difference(raw.column_names)
    _assert_fixture(
        not missing,
        fixture=fixture,
        detail=f"missing required columns: {sorted(missing)}",
    )

    factors = {
        str(name): float(value)
        for name, value in zip(
            raw.column("name_fr").to_pylist(),
            raw.column("total_co2e").to_pylist(),
        )
    }
    expected = {
        "Gaz naturel": 0.227,
        "Electricite": 0.0569,
        "Bois buche": 0.03,
        "GPL": 0.272,
    }
    for name, expected_value in expected.items():
        _assert_fixture(
            name in factors and abs(factors[name] - expected_value) < 1e-9,
            fixture=fixture,
            detail=f"expected sentinel factor for {name} = {expected_value}",
        )

    _assert_fixture(
        factors["Gaz naturel"] > factors["Electricite"],
        fixture=fixture,
        detail="gas factor must remain higher than electricity factor",
    )


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
    _assert_insee_fixture_identity(raw)

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
    fixture_path = FIXTURES_DIR / "eurostat_hhcomp_2022_fixture.csv"
    raw = pcsv.read_csv(fixture_path)
    _assert_eurostat_fixture_identity(raw)

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
    _assert_sdes_fixture_identity(raw)

    vehicle_types = raw.column("fuel_type").to_pylist()
    # Map French age ranges to numeric mid-point
    age_map = {
        "De 1 a 5 ans": 3,
        "De 6 a 10 ans": 8,
        "De 11 a 15 ans": 13,
        "Plus de 15 ans": 18,
    }
    vehicle_ages = [age_map.get(a, 5) for a in raw.column("vehicle_age").to_pylist()]
    # Convert departement codes to zero-padded strings (fixture stores them as integers)
    regions = [str(r).zfill(2) for r in raw.column("departement_code").to_pylist()]

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

    Uses only heating-related emission factors (kgCO2e/kWh) from the ADEME
    fixture to compute carbon emissions from annual energy consumption.
    """
    fixture_path = FIXTURES_DIR / "ademe_energy_2023_fixture.csv"
    raw = pcsv.read_csv(fixture_path)
    _assert_ademe_fixture_identity(raw)

    # Extract emission factors for heating fuels only (rows with kgCO2e/kWh units)
    # Row 0: Gaz naturel  → 0.227 kgCO2e/kWh
    # Row 2: Electricite   → 0.0569 kgCO2e/kWh
    # Row 3: Bois buche    → 0.030 kgCO2e/kWh
    # Row 4: GPL           → 0.272 kgCO2e/kWh (used as proxy for heat_pump backup)
    co2e_all = raw.column("total_co2e").to_pylist()
    emission_factors = {
        "gas": co2e_all[0],       # 0.227 kgCO2e/kWh
        "electric": co2e_all[2],  # 0.0569 kgCO2e/kWh
        "wood": co2e_all[3],      # 0.030 kgCO2e/kWh
        "oil": co2e_all[4],       # 0.272 kgCO2e/kWh (GPL as oil proxy)
        "heat_pump": co2e_all[2] * 0.33,  # electric COP~3 effective factor
    }

    # Create energy consumption profiles keyed by heating_type
    # Annual kWh values represent typical French household heating consumption
    heating_types = ["gas", "oil", "electric", "wood", "gas",
                     "electric", "oil", "gas", "heat_pump", "electric",
                     "wood", "heat_pump"]
    energy_kwh = [8500.0, 12000.0, 5200.0, 6800.0, 9500.0,
                  7200.0, 10500.0, 4800.0, 11000.0, 7800.0,
                  6500.0, 9000.0]
    # Carbon = energy_kWh * emission_factor (kgCO2e/kWh) → kgCO2e
    carbon_emissions = [e * emission_factors[ht] for e, ht in zip(energy_kwh, heating_types)]

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
# Evidence descriptors (Story 21.8 / AC2)
# ====================================================================


def _create_evidence_descriptors() -> list[DataAssetDescriptor]:
    """Create evidence asset descriptors for all data sources.

    Returns a list of DataAssetDescriptor instances documenting the
    provenance, classification, and trust status of each data source
    used in the pipeline.

    See _bmad-output/planning-artifacts/evidence-source-matrix-v1-2026-03-27.md
    for the complete evidence taxonomy.
    """
    descriptors = [
        # INSEE Filosofi income data
        DataAssetDescriptor(
            asset_id="insee-fideli-2021",
            name="Fidéli (Données de cadrage)",
            description="INSEE Fidéli 2021 provides French demographic and income "
            "data at commune level (median income, deciles)",
            data_class="structural",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
            source_url="https://www.insee.fr/fr/statistiques/fichier/4808649/FIDELI_2019.zip",
            license="Open License",
            version="2021",
            geographic_coverage=("FR",),
            years=(2021,),
            intended_use="Structural household income distribution for policy analysis",
            redistribution_allowed=True,
            redistribution_notes="INSEE data requires attribution; derivative works must "
            "cite INSEE as source",
            update_cadence="annual",
            quality_notes="Commune-level data; household counts are fiscal households "
            "(foyers fiscaux), not all households",
            references=("https://www.insee.fr/fr/statistiques/4808649",),
        ),
        # Eurostat household energy data
        DataAssetDescriptor(
            asset_id="eurostat-silc-2022",
            name="EU-SILC Survey Data",
            description="European Union Statistics on Income and Living Conditions, "
            "household composition and energy consumption patterns",
            data_class="structural",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
            source_url="https://ec.europa.eu/eurostat/web/income-and-living-conditions/data",
            license="CC-BY-4.0",
            version="2022",
            geographic_coverage=("EU",),
            years=(2022,),
            intended_use="Housing and energy consumption patterns for household modeling",
            redistribution_allowed=True,
            update_cadence="annual",
            quality_notes="Microdata access requires application; aggregates used here "
            "are public domain",
            references=(
                "https://ec.europa.eu/eurostat/web/income-and-living-conditions/data",
                "https://ec.europa.eu/eurostat/databrowser/view/ilc_lvho09/default/table",
            ),
        ),
        # SDES vehicle fleet data
        DataAssetDescriptor(
            asset_id="sdes-vehicles-2023",
            name="SDES Vehicle Fleet Composition",
            description="French vehicle fleet statistics by fuel type, region, and age "
            "from Service des données et études statistiques (SDES)",
            data_class="structural",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
            source_url="https://www.statistiques.developpement-durable.gouv.fr/",
            license="Open License",
            version="2023",
            geographic_coverage=("FR",),
            years=(2023,),
            intended_use="Vehicle ownership and fleet composition for transport modeling",
            redistribution_allowed=True,
            update_cadence="annual",
            quality_notes="Regional aggregates; national-level data more complete than "
            "department-level",
            references=(
                "https://www.statistiques.developpement-durable.gouv.fr/"
                "transports/mobilite/parc-vehicules",
            ),
        ),
        # ADEME emission factors
        DataAssetDescriptor(
            asset_id="ademe-carbon-factors-2024",
            name="Base Carbone® ADEME",
            description="ADEME Base Carbone emission factors for carbon footprint "
            "assessment (heating fuels, electricity, transport)",
            data_class="exogenous",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
            source_url="https://bilans-ges.ademe.fr/",
            license="Open License",
            version="2024",
            geographic_coverage=("FR",),
            years=(2024,),
            intended_use="Carbon emission factors for energy consumption and transport",
            redistribution_allowed=True,
            redistribution_notes="Base Carbone is a registered trademark of ADEME; "
            "attribution required",
            update_cadence="annual",
            quality_notes="Factors updated annually; version tracking required for "
            "reproducibility",
            references=(
                "https://bilans-ges.ademe.fr/",
                "https://www.ademe.fr/",
            ),
        ),
    ]
    return descriptors


def _write_evidence_manifest(
    descriptors: list[DataAssetDescriptor],
    output_path: Path,
) -> None:
    """Write evidence manifest JSON file documenting all data sources.

    Args:
        descriptors: List of DataAssetDescriptor instances for all sources.
        output_path: Path where evidence_manifest.json should be written.
    """
    import json
    from datetime import UTC, datetime

    manifest = {
        "format_version": "1.0",
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "pipeline_name": "french_household_example",
        "evidence_assets": [d.to_json() for d in descriptors],
        "assumptions": [
            "Fixtures used for demo purposes replace full institutional datasets",
            "Regional vehicle fleet targets use simplified 12-region sample",
            "Heating type stratification assumes independence from income",
        ],
    }

    output_path.write_text(json.dumps(manifest, indent=2) + "\n")
    logger.info("evidence manifest written path=%s assets=%d", output_path, len(descriptors))


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


def write_summary(
    table: pa.Table,
    summary_path: Path,
    evidence_descriptors: list[DataAssetDescriptor] | None = None,
) -> None:
    """Write population summary statistics to a text file.

    Args:
        table: Generated population table.
        summary_path: Path where summary file should be written.
        evidence_descriptors: Optional list of evidence descriptors for documentation.
    """
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
            lines.append(
                f"  {col_name}: min={pc.min(col).as_py():.1f}, "
                f"max={pc.max(col).as_py():.1f}, "
                f"mean={pc.mean(col).as_py():.1f}"
            )
        elif pa.types.is_string(col.type):
            unique = col.unique().to_pylist()
            lines.append(f"  {col_name}: {len(unique)} unique values: {unique[:10]}")

    # Evidence classification (Story 21.8 / AC2)
    if evidence_descriptors:
        lines.extend([
            "",
            "Evidence Sources:",
            "=================",
        ])
        for desc in evidence_descriptors:
            lines.extend([
                f"",
                f"Asset: {desc.asset_id}",
                f"  Name: {desc.name}",
                f"  Origin: {desc.origin}",
                f"  Access Mode: {desc.access_mode}",
                f"  Trust Status: {desc.trust_status}",
                f"  Data Class: {desc.data_class}",
                f"  Provider: {desc.asset_id.split('-')[0] if '-' in desc.asset_id else 'unknown'}",
                f"  License: {desc.license or 'Not specified'}",
            ])

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

    # Create evidence descriptors and write manifest (Story 21.8 / AC2)
    evidence_descriptors = _create_evidence_descriptors()
    _write_evidence_manifest(evidence_descriptors, EVIDENCE_MANIFEST_FILE)
    logger.info("Evidence manifest written path=%s", EVIDENCE_MANIFEST_FILE)

    # Write summary with evidence classification
    write_summary(result.table, SUMMARY_FILE, evidence_descriptors)

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
    print(f"Evidence manifest saved to {EVIDENCE_MANIFEST_FILE}")


if __name__ == "__main__":
    main()
