"""
Epic 1 Demo — The Foundation Layer

ReformLab is a platform for analysing the impact of environmental policies
(like a carbon tax) on households. Before we can run any analysis, we need
solid plumbing: a way to load data, talk to the tax calculator, check that
nothing is broken, and keep track of where every number came from.

That plumbing is what Epic 1 built. This script walks through it step by step:

1. Loading data files — reading household and emission data, catching errors early
2. Tracking where data comes from — fingerprinting every file so results are reproducible
3. Translating column names — the tax calculator uses its own naming; we map to ours
4. Running the tax calculator — via pre-computed files or a fake stand-in for testing
5. Checking output quality — catching missing values, wrong types, out-of-range numbers
6. Version compatibility — knowing which versions of the tax calculator we support

Usage:
    python demos/guides/01_data_foundation.py
"""

from pathlib import Path

from reformlab.visualization import show

# Point to the folder with our sample data files
DATA_DIR = Path(__file__).parent / "data"
print(f"Data directory: {DATA_DIR}")
print(f"Files: {sorted(p.name for p in DATA_DIR.iterdir())}")


# ---------------------------------------------------------------------------
# 1. Loading a Data File
# ---------------------------------------------------------------------------
#
# Our analyses start with data about people and households (age, income,
# region, etc.). That data lives in CSV files — simple spreadsheets.
#
# When we load a file, the system checks that it has the right columns and
# the right data types BEFORE anything else happens. Think of it like a
# bouncer at the door: if your file is missing a required column, it gets
# rejected immediately with a clear explanation of what's wrong.

from reformlab.computation import ingest_csv
from reformlab.data import SYNTHETIC_POPULATION_SCHEMA

# Load the CSV and check it against the expected schema (column names + types)
pop_result = ingest_csv(DATA_DIR / "synthetic_population.csv", SYNTHETIC_POPULATION_SCHEMA)

print(f"Format:    {pop_result.format}")
print(f"Rows:      {pop_result.row_count}")
print(f"Source:    {pop_result.source_path.name}")
print(f"Loaded at: {pop_result.metadata['loaded_at']}")
print()
print("Schema (what each column is called and its data type):")
print(pop_result.table.schema)
print()
show(pop_result.table)


# ---------------------------------------------------------------------------
# What happens when the data is wrong?
# ---------------------------------------------------------------------------
#
# Below we deliberately feed in a file that's missing two required columns
# (age and income). Instead of crashing mysteriously, the system tells you
# exactly which columns are missing and what to do about it.

import tempfile
import csv
from reformlab.computation import IngestionError

# Write a CSV missing the required "age" and "income" columns
bad_csv = Path(tempfile.mktemp(suffix=".csv"))
bad_csv.write_text("household_id,person_id\n1,101\n")

try:
    ingest_csv(bad_csv, SYNTHETIC_POPULATION_SCHEMA)
except IngestionError as e:
    print(f"Caught IngestionError:")
    print(f"  Missing columns: {e.missing_columns}")
    print(f"  Message: {e}")
finally:
    bad_csv.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# 2. Tracking Where Data Comes From (Provenance)
# ---------------------------------------------------------------------------
#
# For any policy analysis to be trusted, you need to be able to answer:
# "Where did this data come from? Is it the same file we used last time?"
#
# Every time we load a dataset, the system:
# - Computes a fingerprint (SHA-256 hash) of the file
# - Records who published it, what version it is, and when we loaded it
# - Stores all of this in a registry so we can reconstruct any analysis later
#
# This is what makes results reproducible.

from reformlab.data import (
    DataSourceMetadata,
    DatasetRegistry,
    EMISSION_FACTOR_SCHEMA,
    load_dataset,
    build_emission_factor_index,
)

# Describe where this dataset comes from (name, version, URL, license)
pop_source = DataSourceMetadata(
    name="synthetic_population_fr",
    version="2024.1",
    url="https://example.com/synthetic-pop",
    description="Synthetic French households (demo)",
    license="Open Data Commons",
)

# Load the file — this validates the data AND computes a fingerprint
pop_table, pop_manifest = load_dataset(
    DATA_DIR / "synthetic_population.csv",
    SYNTHETIC_POPULATION_SCHEMA,
    pop_source,
)

print("=== Population Manifest (the dataset's ID card) ===")
print(f"  Key:         {pop_manifest.dataset_key}")
print(f"  SHA-256:     {pop_manifest.content_hash[:24]}...")
print(f"  Rows:        {pop_manifest.row_count}")
print(f"  Columns:     {pop_manifest.column_names}")
print(f"  Loaded at:   {pop_manifest.loaded_at}")


# Load emission factors (how much CO2 per unit of activity)
ef_source = DataSourceMetadata(
    name="emission_factors_ademe",
    version="2024.1",
    url="https://example.com/emission-factors",
    description="ADEME/Agribalyse emission factors (demo)",
    license="Etalab Open License",
)

ef_table, ef_manifest = load_dataset(
    DATA_DIR / "emission_factors.csv",
    EMISSION_FACTOR_SCHEMA,
    ef_source,
)

# Build a lookup index so we can query by category and year
ef_index = build_emission_factor_index(ef_table)

print("=== Emission Factor Index ===")
print(f"  Categories:  {ef_index.categories()}")
print()
print("Transport factors for 2024 (kgCO2 per km):")
show(ef_index.by_category_and_year("transport", 2024))


# The registry keeps a record of every dataset we've loaded
# This is the audit trail — useful for governance and reproducibility
registry = DatasetRegistry()
registry.register(pop_manifest)
registry.register(ef_manifest)

print("Registry contents (can be saved as JSON for audit trails):")
import json
print(json.dumps(registry.to_dict(), indent=2, default=str))


# ---------------------------------------------------------------------------
# 3. Translating Column Names (Field Mapping)
# ---------------------------------------------------------------------------
#
# The tax calculator (OpenFisca) uses its own column names — for example
# income_tax. But in our project we might want to use French names like
# impot_revenu, or just different conventions.
#
# Instead of hard-coding these translations everywhere, we define them once
# in a simple YAML configuration file. The system then automatically renames
# columns in both directions:
# - Going in: our names to OpenFisca names
# - Coming out: OpenFisca names back to ours

from reformlab.computation import load_mapping, validate_mapping

# Load the YAML file that defines our column name translations
mapping = load_mapping(DATA_DIR / "field_mapping.yaml")

print("Loaded mappings (OpenFisca name <-> our project name):")
for fm in mapping.mappings:
    print(f"  {fm.openfisca_name:15s} <-> {fm.project_name:15s}  [{fm.direction:6s}]")

print(f"\nColumns we rename on output: {[m.openfisca_name for m in mapping.output_mappings]}")
print(f"Columns we rename on input:  {[m.openfisca_name for m in mapping.input_mappings]}")


# Check that every name in our mapping actually exists in the data
available_cols = ("household_id", "person_id", "income_tax", "carbon_tax")
result = validate_mapping(mapping, available_cols)
print(f"Validation errors:   {result.errors}")
print(f"Validation warnings: {result.warnings}")
print("All good — every mapped name was found in the data!")


# ---------------------------------------------------------------------------
# 4. Running the Tax Calculator
# ---------------------------------------------------------------------------
#
# This is the core of the system: given a population and a policy, compute
# the taxes.
#
# We don't build our own tax engine — we use OpenFisca, an open-source
# tax-benefit calculator maintained by the French government. Our code talks
# to it through an adapter (a standardised plug), which means we could swap
# in a different calculator without rewriting everything else.
#
# 4a. File-based mode
#
# The simplest mode: OpenFisca has already been run separately, and we just
# read the result files. This is fast and doesn't require OpenFisca to be
# installed.

from reformlab.computation.openfisca_adapter import OpenFiscaAdapter
from reformlab.computation import PopulationData, PolicyConfig, apply_output_mapping
from reformlab.templates.schema import PolicyParameters

# Set up a folder with a pre-computed result file (named by year)
import shutil
adapter_dir = DATA_DIR / "adapter_store"
adapter_dir.mkdir(exist_ok=True)
shutil.copy(DATA_DIR / "openfisca_output_2024.csv", adapter_dir / "2024.csv")

# Create the adapter (skip_version_check=True because OpenFisca isn't installed here)
adapter = OpenFiscaAdapter(adapter_dir, skip_version_check=True)

# Describe our inputs: who are the people, and what policy are we testing?
population = PopulationData(
    tables={"default": pop_table},
    metadata={"source": pop_manifest.dataset_key},
)
policy = PolicyConfig(
    policy=PolicyParameters(rate_schedule={2024: 44.6}),
    name="baseline_2024",
    description="Baseline carbon tax scenario at 44.6 EUR/tCO2",
)

# "Compute" — in file mode this just reads the pre-computed CSV for year 2024
result = adapter.compute(population, policy, period=2024)

print(f"Adapter version: {adapter.version()}")
print(f"Period:          {result.period}")
print(f"Output rows:     {result.output_fields.num_rows}")
print()
print("Raw output from the tax calculator:")
show(result.output_fields)


# Now translate the column names: income_tax -> impot_revenu, etc.
mapped_table = apply_output_mapping(result.output_fields, mapping)

print("Same data, but with our project's column names:")
show(mapped_table)


# ---------------------------------------------------------------------------
# 4b. Fake stand-in for testing (Mock Adapter)
# ---------------------------------------------------------------------------
#
# When developing the rest of the platform (scenario orchestration,
# indicators, etc.), we don't want to depend on OpenFisca being installed.
# So we built a "mock" adapter — a fake calculator that returns whatever
# numbers we configure.

import pyarrow as pa
from reformlab.computation import ComputationAdapter
from reformlab.computation.mock_adapter import MockAdapter

# Create a fake adapter with hand-picked output numbers
mock_output = pa.table({
    "income_tax": pa.array([3200.0, 1800.0, 5400.0]),
    "carbon_tax": pa.array([150.0, 210.0, 170.0]),
})
mock = MockAdapter(version_string="mock-carbon-v1", default_output=mock_output)

# The mock "quacks like" the real adapter — it satisfies the same contract
print(f"Satisfies the ComputationAdapter contract: {isinstance(mock, ComputationAdapter)}")

# Run it — returns our hand-picked numbers regardless of the input
mock_result = mock.compute(population, policy, period=2024)
print(f"Mock version: {mock.version()}")
print(f"Mock output:")
show(mock_result.output_fields)

# The mock also logs every call — useful for verifying test behaviour
print(f"\nCall log: {mock.call_log}")


# ---------------------------------------------------------------------------
# 5. Checking Output Quality
# ---------------------------------------------------------------------------
#
# Even if the data loads fine and the calculator runs, we still need to check
# the results before using them. Things that could go wrong:
# - A column that should always have a value has blanks (nulls)
# - A column has the wrong data type (text where we expected numbers)
# - Values are outside a reasonable range

from reformlab.computation import (
    validate_output,
    DEFAULT_OPENFISCA_OUTPUT_SCHEMA,
    RangeRule,
    DataQualityError,
)

# Run quality checks on the real result — should pass with flying colours
qc = validate_output(
    result,
    DEFAULT_OPENFISCA_OUTPUT_SCHEMA,
    range_rules=(
        RangeRule(field="income_tax", min_value=0, max_value=100_000, description="Reasonable income tax range"),
        RangeRule(field="carbon_tax", min_value=0, max_value=5_000, description="Reasonable carbon tax range"),
    ),
)

print(f"Quality check passed: {qc.passed}")
print(f"Checked columns:      {qc.checked_columns}")
print(f"Rows validated:       {qc.row_count}")
print(f"Errors:               {len(qc.errors)}")
print(f"Warnings:             {len(qc.warnings)}")


# Deliberately create bad data with missing values (None = blank)
from reformlab.computation import ComputationResult

bad_table = pa.table({
    "income_tax": pa.array([1200.0, None, 3400.0]),   # row 1 is blank!
    "carbon_tax": pa.array([100.0, 200.0, None]),      # row 2 is blank!
})
bad_result = ComputationResult(
    output_fields=bad_table,
    adapter_version="test",
    period=2024,
)

# The quality check catches the blanks and tells us exactly where they are
try:
    validate_output(bad_result, DEFAULT_OPENFISCA_OUTPUT_SCHEMA)
except DataQualityError as e:
    print("Quality validation FAILED (as expected):")
    print(f"  Blocking errors: {len(e.result.errors)}")
    for issue in e.result.errors:
        print(f"    Column '{issue.field}': {issue.issue_type} at row(s) {issue.row_indices}")


# ---------------------------------------------------------------------------
# 6. Version Compatibility
# ---------------------------------------------------------------------------
#
# OpenFisca evolves over time — new versions may change how calculations
# work. We maintain a compatibility matrix that tracks which versions we've
# tested against.

from reformlab.computation import get_compatibility_info

# Check a few versions — supported, untested, too old, and invalid
for version in ["44.0.0", "44.2.2", "45.0.0", "43.0.0", "not-installed"]:
    info = get_compatibility_info(version)
    print(f"  {version:15s} -> {info.status}")
    if info.guidance:
        print(f"                    {info.guidance[:80]}")


# ---------------------------------------------------------------------------
# What We Built (Summary)
# ---------------------------------------------------------------------------
#
# All of the above is the foundation layer — the plumbing that everything
# else sits on top of.
#
# | Capability             | In plain terms                                    |
# |------------------------|---------------------------------------------------|
# | Data loading           | Read CSV/Parquet files with automatic validation   |
# | Provenance tracking    | Every dataset gets a fingerprint and an ID card    |
# | Emission factor lookup | Look up CO2 per km, per kWh, etc.                 |
# | Column name mapping    | Translate between OpenFisca's naming and ours      |
# | Tax calculator adapter | Plug-and-play interface to OpenFisca               |
# | Quality checks         | Automatic validation of results                    |
# | Version compatibility  | Know if a given OpenFisca version is supported     |

# Cleanup
shutil.rmtree(adapter_dir, ignore_errors=True)
