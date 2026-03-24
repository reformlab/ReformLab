"""
Epic 2 Demo — Scenario Templates and Registry

In Epic 1 we built the plumbing: loading data, talking to the tax calculator,
checking quality. Now we need a way to describe policies — not just run them,
but define, version, share, and compare them.

This script walks through it step by step:

1. Defining a scenario template — the schema that describes any environmental policy
2. Using prebuilt template packs — ready-made carbon tax, subsidy, rebate, and feebate scenarios
3. Reform-as-delta — defining a reform that only specifies what changes from a baseline
4. Saving to the registry — versioned, immutable storage with content-addressable IDs
5. Cloning and linking — copying scenarios and navigating baseline/reform relationships
6. Schema migration — upgrading old scenario files to newer schema versions
7. Workflow configuration — describing a complete analysis pipeline in YAML or JSON

Usage:
    python demos/guides/02_scenario_templates.py
"""

from pathlib import Path

# All generated files live under demos/guides/data/ so you can inspect them
DATA_DIR = Path(__file__).parent / "data"
TEMPLATES_DIR = DATA_DIR / "templates"
REGISTRY_DIR = DATA_DIR / "registry"
TEMPLATES_DIR.mkdir(exist_ok=True)

print(f"Data directory:      {DATA_DIR}")
print(f"Templates directory: {TEMPLATES_DIR}")
print(f"Registry directory:  {REGISTRY_DIR}")


# ---------------------------------------------------------------------------
# 1. Defining a Scenario Template
# ---------------------------------------------------------------------------
#
# Every policy analysis starts with a scenario template — a structured
# description of the policy you want to study. The template captures:
#
# - Policy type — carbon tax, subsidy, rebate, or feebate
# - Year schedule — the time range the policy covers (e.g., 2026-2036)
# - Parameters — rates, exemptions, redistribution rules, etc.
#
# All templates are frozen dataclasses — once created, they can't be modified
# accidentally. This is important for reproducibility.

from reformlab.templates import (
    PolicyType,
    YearSchedule,
    CarbonTaxParameters,
    BaselineScenario,
)

# Define a simple carbon tax: EUR 44.60/tCO2 in 2026, rising to EUR 100 by 2036
schedule = YearSchedule(start_year=2026, end_year=2036)

params = CarbonTaxParameters(
    rate_schedule={
        2026: 44.60, 2027: 50.00, 2028: 55.00, 2029: 60.00, 2030: 65.00,
        2031: 70.00, 2032: 75.00, 2033: 80.00, 2034: 85.00, 2035: 90.00,
        2036: 100.00,
    },
    covered_categories=("transport_fuel", "heating_fuel", "natural_gas"),
    exemptions=(
        {"category": "agricultural_fuel", "rate_reduction": 1.0},
    ),
)

baseline = BaselineScenario(
    name="French Carbon Tax 2026",
    policy_type=PolicyType.CARBON_TAX,
    year_schedule=schedule,
    policy=params,
    description="Standard French carbon tax trajectory with agricultural exemption",
)

print(f"Name:           {baseline.name}")
print(f"Policy type:    {baseline.policy_type.value}")
print(f"Years:          {schedule.start_year}\u2013{schedule.end_year} ({schedule.duration} years)")
print(f"Rate in 2026:   EUR {params.rate_schedule[2026]}/tCO2")
print(f"Rate in 2036:   EUR {params.rate_schedule[2036]}/tCO2")
print(f"Covered:        {params.covered_categories}")
print(f"Exemptions:     {params.exemptions}")
print(f"Is 2030 in schedule? {2030 in schedule}")


# ---------------------------------------------------------------------------
# Loading from YAML
# ---------------------------------------------------------------------------
#
# In practice, you don't build scenarios in Python — you write them as YAML
# files. The loader reads the YAML, validates every field, and returns a
# typed object. If something is wrong, you get a clear error.

from reformlab.templates import load_scenario_template, dump_scenario_template, ScenarioError

# Save our scenario to a YAML file — you can open this file to inspect it
yaml_path = TEMPLATES_DIR / "carbon-tax-baseline.yaml"
dump_scenario_template(baseline, yaml_path)

# Show what the YAML looks like
print("=== YAML file contents ===")
print(yaml_path.read_text())


# Load it back — the loader adds a $schema reference automatically
loaded = load_scenario_template(yaml_path)
print(f"Type:              {type(loaded).__name__}")
print(f"Frozen (immutable): {type(loaded).__dataclass_params__.frozen}")
print(f"Name match:        {loaded.name == baseline.name}")
print(f"Params match:      {loaded.policy == baseline.policy}")
print(f"Schedule match:    {loaded.year_schedule == baseline.year_schedule}")
print(f"Schema ref added:  {loaded.schema_ref!r}  (auto-inserted by the loader)")


# ---------------------------------------------------------------------------
# What happens with invalid YAML?
# ---------------------------------------------------------------------------
#
# If the YAML is missing required fields or has wrong values, the system
# rejects it with a structured error.

import tempfile

bad_yaml = Path(tempfile.mktemp(suffix=".yaml"))
bad_yaml.write_text('version: "1.0"\nname: "Oops"\npolicy_type: carbon_tax\n')

try:
    load_scenario_template(bad_yaml)
except ScenarioError as e:
    print(f"Caught ScenarioError:")
    print(f"  Message:        {e}")
    print(f"  Invalid fields: {e.invalid_fields}")
    print(f"  File:           {e.file_path.name}")
finally:
    bad_yaml.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# 2. Prebuilt Template Packs
# ---------------------------------------------------------------------------
#
# Writing YAML from scratch every time would be tedious. ReformLab ships
# with template packs — ready-made scenarios for the four policy types.
# Each pack contains realistic defaults based on European policy research.

from reformlab.templates import (
    list_carbon_tax_templates,
    list_subsidy_templates,
    list_rebate_templates,
    list_feebate_templates,
    load_carbon_tax_template,
)

# List all available template packs
print("=== Available Template Packs ===")
print(f"\nCarbon Tax ({len(list_carbon_tax_templates())} variants):")
for name in list_carbon_tax_templates():
    print(f"  - {name}")

print(f"\nSubsidy ({len(list_subsidy_templates())} variants):")
for name in list_subsidy_templates():
    print(f"  - {name}")

print(f"\nRebate ({len(list_rebate_templates())} variants):")
for name in list_rebate_templates():
    print(f"  - {name}")

print(f"\nFeebate ({len(list_feebate_templates())} variants):")
for name in list_feebate_templates():
    print(f"  - {name}")


# Load and inspect a carbon tax template with lump-sum redistribution
lump_sum = load_carbon_tax_template("carbon-tax-flat-lump-sum-dividend")

print(f"Name:             {lump_sum.name}")
print(f"Description:      {lump_sum.description[:80]}...")
print(f"Policy type:      {lump_sum.policy_type.value}")
print(f"Years:            {lump_sum.year_schedule.start_year}\u2013{lump_sum.year_schedule.end_year}")
print(f"Redistribution:   {lump_sum.policy.redistribution_type}")
print(f"Covered:          {lump_sum.policy.covered_categories}")
print(f"\nRate trajectory (EUR/tCO2):")
for year, rate in sorted(lump_sum.policy.rate_schedule.items()):
    bar = '#' * int(rate / 5)
    print(f"  {year}: {rate:6.2f}  {bar}")


# Compare two variants side by side
progressive = load_carbon_tax_template("carbon-tax-flat-progressive-dividend")

print("Lump-Sum vs Progressive Dividend:")
print(f"  Lump-sum redistribution:    {lump_sum.policy.redistribution_type}")
print(f"  Progressive redistribution: {progressive.policy.redistribution_type}")
print(f"\nProgressive income weights (who gets more/less of the dividend):")
for decile, weight in sorted(progressive.policy.income_weights.items()):
    bar = '#' * int(weight * 10)
    print(f"  {decile:10s}: {weight:.1f}  {bar}")


# ---------------------------------------------------------------------------
# 3. Reform-as-Delta
# ---------------------------------------------------------------------------
#
# When comparing policies, you typically have a baseline (the current policy)
# and a reform (a proposed change). Instead of duplicating the entire baseline
# and modifying a few fields, you write a reform that only specifies what
# changes.

from reformlab.templates import ReformScenario, resolve_reform_definition

# Define a reform that adds progressive redistribution to our baseline
# Notice: we only specify what changes — the reform inherits everything else
reform = ReformScenario(
    name="Progressive Carbon Dividend",
    policy_type=PolicyType.CARBON_TAX,
    baseline_ref="french-carbon-tax-2026",
    policy=CarbonTaxParameters(
        rate_schedule={},  # empty = inherit baseline rates
        redistribution_type="progressive_dividend",
        income_weights={
            "decile_1": 2.0, "decile_2": 1.8, "decile_3": 1.5,
            "decile_4": 1.2, "decile_5": 1.0, "decile_6": 0.9,
            "decile_7": 0.7, "decile_8": 0.5, "decile_9": 0.3,
            "decile_10": 0.1,
        },
    ),
    description="Reform: redistribute carbon tax revenue progressively",
)

print(f"Reform name:      {reform.name}")
print(f"Baseline ref:     {reform.baseline_ref}")
print(f"Own rate_schedule: {reform.policy.rate_schedule}  (empty = inherit)")
print(f"Redistribution:   {reform.policy.redistribution_type}  (this is the change)")


# Resolve the reform against its baseline to get a fully-specified scenario
resolved = resolve_reform_definition(reform, baseline)

print(f"Resolved name:     {resolved.name}")
print(f"Type:              {type(resolved).__name__}  (now a full BaselineScenario)")
print(f"Rate in 2026:      EUR {resolved.policy.rate_schedule[2026]}/tCO2  (inherited)")
print(f"Rate in 2036:      EUR {resolved.policy.rate_schedule[2036]}/tCO2  (inherited)")
print(f"Redistribution:    {resolved.policy.redistribution_type}  (from reform)")
print(f"Covered:           {resolved.policy.covered_categories}  (inherited)")
print(f"Exemptions:        {resolved.policy.exemptions}  (inherited)")


# ---------------------------------------------------------------------------
# 4. The Scenario Registry
# ---------------------------------------------------------------------------
#
# Once you have scenarios, you need somewhere to store them. The registry
# provides:
# - Immutable versions — once saved, a version can never be modified
# - Content-addressable IDs — the version ID is derived from the content
# - Version history — every save creates a new version with a timestamp

from reformlab.templates import ScenarioRegistry

# Create a registry in our temp directory
registry = ScenarioRegistry(registry_path=REGISTRY_DIR)

# Save the baseline — returns a content-addressable version ID
v1 = registry.save(baseline, "french-carbon-tax-2026", "Initial baseline")
print(f"Saved baseline:  version_id = {v1}")

# Save the reform — links to the baseline via baseline_ref
v2 = registry.save(reform, "progressive-dividend", "Progressive redistribution reform")
print(f"Saved reform:    version_id = {v2}")

# List what's in the registry
print(f"\nRegistry contents: {registry.list_scenarios()}")


# Retrieve a scenario by name (gets the latest version)
retrieved = registry.get("french-carbon-tax-2026")
print(f"Retrieved:  {retrieved.name}")
print(f"Same as original: {retrieved == baseline}")

# Idempotent: saving the same content again returns the same version ID
v1_again = registry.save(baseline, "french-carbon-tax-2026", "Duplicate save")
print(f"\nIdempotent save: {v1_again == v1}  (same content = same ID)")


# Create a second version by modifying a parameter
from dataclasses import replace

# Raise the 2036 rate to EUR 120/tCO2
updated_rates = dict(baseline.policy.rate_schedule)
updated_rates[2036] = 120.00
updated_params = replace(baseline.policy, rate_schedule=updated_rates)
updated = replace(baseline, policy=updated_params)

v3 = registry.save(updated, "french-carbon-tax-2026", "Raised 2036 target to EUR 120")
print(f"New version: {v3}  (different from {v1})")

# Now check the version history
versions = registry.list_versions("french-carbon-tax-2026")
print(f"\nVersion history ({len(versions)} versions):")
for v in versions:
    print(f"  {v.version_id}  {v.timestamp:%Y-%m-%d %H:%M}  {v.change_description}")


# ---------------------------------------------------------------------------
# What happens when a scenario doesn't exist?
# ---------------------------------------------------------------------------

from reformlab.templates import ScenarioNotFoundError

try:
    registry.get("nonexistent-scenario")
except ScenarioNotFoundError as e:
    print(f"Caught ScenarioNotFoundError:")
    print(f"  Summary: {e.summary}")
    print(f"  Reason:  {e.reason}")
    print(f"  Fix:     {e.fix}")


# ---------------------------------------------------------------------------
# 5. Cloning and Baseline/Reform Navigation
# ---------------------------------------------------------------------------
#
# - Cloning — create a copy of a scenario with a new name, then tweak it
# - Link navigation — from a reform, find its baseline; from a baseline,
#   find all reforms that reference it

# Clone the baseline to create a variant
clone = registry.clone("french-carbon-tax-2026", new_name="high-ambition-variant")
print(f"Clone name: {clone.name}")
print(f"Clone == original? {clone == baseline}  (different name)")

# Modify the clone — raise all rates by 20%
boosted_rates = {year: rate * 1.2 for year, rate in clone.policy.rate_schedule.items()}
boosted_params = replace(clone.policy, rate_schedule=boosted_rates)
high_ambition = replace(clone, policy=boosted_params, description="20% higher carbon tax trajectory")

# Save the clone
v_clone = registry.save(
    high_ambition, "high-ambition-variant",
    f"Cloned from french-carbon-tax-2026@{v1}, rates +20%",
)
print(f"\nSaved clone: {v_clone}")
print(f"Rate in 2026: EUR {high_ambition.policy.rate_schedule[2026]:.2f} (was {baseline.policy.rate_schedule[2026]:.2f})")
print(f"Rate in 2036: EUR {high_ambition.policy.rate_schedule[2036]:.2f} (was {baseline.policy.rate_schedule[2036]:.2f})")


# Navigate from reform to baseline
linked_baseline = registry.get_baseline("progressive-dividend")
print(f"Reform 'progressive-dividend' links to baseline: '{linked_baseline.name}'")

# Navigate from baseline to all reforms
reforms = registry.list_reforms("french-carbon-tax-2026")
print(f"\nReforms referencing 'french-carbon-tax-2026':")
for reform_name, reform_vid in reforms:
    print(f"  - {reform_name} (version {reform_vid})")


# ---------------------------------------------------------------------------
# 6. Schema Migration
# ---------------------------------------------------------------------------
#
# As the project evolves, the schema may change. The migration helper:
# - Detects compatibility — same version, minor bump, major bump (breaking)
# - Migrates automatically — applies deterministic rules to update the schema
# - Reports every change — you see exactly what was modified and why

from reformlab.templates import (
    SchemaVersion,
    CompatibilityStatus,
    check_compatibility,
    migrate_scenario_dict,
)

# Check compatibility between different schema versions
print("=== Schema Compatibility ===")
pairs = [("1.0", "1.0"), ("1.0", "1.1"), ("1.1", "1.0"), ("1.0", "2.0")]
for src, tgt in pairs:
    status = check_compatibility(src, tgt)
    print(f"  {src} -> {tgt}: {status.value:20s} (needs migration: {status.needs_migration})")

print(f"\nCurrent schema version: {SchemaVersion.current()}")


# Simulate migrating a scenario from an older schema version
old_scenario_dict = {
    "version": "1.0",
    "name": "Old Format Scenario",
    "policy_type": "rebate",
    "year_schedule": {"start_year": 2026, "end_year": 2036},
    "policy": {
        "rate_schedule": {2026: 100.0},
        # Old format: redistribution nested inside a container
        "redistribution": {
            "type": "progressive_dividend",
            "income_weights": {"decile_1": 2.0, "decile_10": 0.2},
        },
    },
}

# Migrate to version 1.1 (preview)
migrated_dict, report = migrate_scenario_dict(old_scenario_dict, target_version="1.1")

print(f"Migration: {report.source_version} -> {report.target_version}")
print(f"Status:    {report.status.value}")
print(f"Success:   {report.success}")
print(f"\nChanges applied ({len(report.changes)}):")
for change in report.changes:
    print(f"  [{change.field_path}]")
    print(f"    {change.old_value} -> {change.new_value}")
    print(f"    Reason: {change.reason}")

if report.warnings:
    print(f"\nWarnings:")
    for w in report.warnings:
        print(f"  - {w}")


# What happens with a breaking version change?
try:
    migrate_scenario_dict(old_scenario_dict, target_version="2.0")
except ValueError as e:
    print(f"Breaking change detected:")
    print(f"  {e}")


# ---------------------------------------------------------------------------
# 7. Workflow Configuration
# ---------------------------------------------------------------------------
#
# A single scenario tells you what policy to model. A workflow configuration
# tells you how to run the full analysis: which data to use, which scenarios
# to compare, how many years to project, and what outputs to produce.

from reformlab.templates import (
    WorkflowConfig,
    DataSourceConfig,
    ScenarioRef,
    RunConfig,
    OutputConfig,
    workflow_to_yaml,
    workflow_to_json,
    dump_workflow_config,
    load_workflow_config,
)

# Build a workflow configuration programmatically
workflow = WorkflowConfig(
    name="carbon_tax_comparison",
    version="1.0",
    description="Compare baseline carbon tax with progressive dividend redistribution",
    data_sources=DataSourceConfig(
        population="synthetic_french_2024",
        emission_factors="default",
    ),
    scenarios=(
        ScenarioRef(role="baseline", reference="french-carbon-tax-2026"),
        ScenarioRef(role="reform", reference="progressive-dividend"),
    ),
    run_config=RunConfig(
        projection_years=10,
        start_year=2026,
        output_format="csv",
    ),
    outputs=(
        OutputConfig(type="distributional_indicators", by=("income_decile",), format="csv", path=""),
        OutputConfig(type="comparison_table", by=(), format="csv", path="outputs/comparison.csv"),
        OutputConfig(type="summary_report", by=(), format="yaml", path="outputs/summary.yaml"),
    ),
)

# Show the YAML representation
print("=== Workflow as YAML ===")
print(workflow_to_yaml(workflow))


# Save as YAML and JSON
yaml_wf = TEMPLATES_DIR / "workflow-comparison.yaml"
json_wf = TEMPLATES_DIR / "workflow-comparison.json"

dump_workflow_config(workflow, yaml_wf)
dump_workflow_config(workflow, json_wf)

loaded_yaml = load_workflow_config(yaml_wf)
loaded_json = load_workflow_config(json_wf)

# Core content is identical — only the "format" field differs
print(f"Name match:       {loaded_yaml.name == workflow.name}")
print(f"Scenarios match:  {loaded_yaml.scenarios == workflow.scenarios}")
print(f"Run config match: {loaded_yaml.run_config == workflow.run_config}")
print(f"Outputs match:    {loaded_yaml.outputs == workflow.outputs}")
print(f"Format field:     YAML={loaded_yaml.format!r}, JSON={loaded_json.format!r}  (tracks source format)")


# Show the JSON representation for comparison
print("=== Workflow as JSON ===")
print(workflow_to_json(workflow))


# Load one of the example workflows shipped with ReformLab
example_dir = Path(__file__).parent.parent.parent / "examples" / "workflows"
if not example_dir.exists():
    # Handle running from different working directories
    from importlib.resources import files
    example_dir = Path(str(files("reformlab"))).parent.parent / "examples" / "workflows"

if example_dir.exists():
    example_wf = load_workflow_config(example_dir / "scenario_comparison.yaml")
    print(f"Loaded example workflow: {example_wf.name}")
    print(f"  Description: {example_wf.description}")
    print(f"  Scenarios:   {[(s.role, s.reference) for s in example_wf.scenarios]}")
    print(f"  Outputs:     {[o.type for o in example_wf.outputs]}")
else:
    print("(Example workflows directory not found \u2014 skipping)")


# ---------------------------------------------------------------------------
# What We Built (Summary)
# ---------------------------------------------------------------------------
#
# | Capability              | In plain terms                                     |
# |-------------------------|----------------------------------------------------|
# | Scenario template schema| Structured format for describing any policy        |
# | YAML/JSON loader        | Load and validate scenario files                   |
# | Template packs          | Ready-made scenarios for 4 policy types             |
# | Reform-as-delta         | Define a reform by specifying only what changes     |
# | Scenario registry       | Immutable, versioned storage                        |
# | Cloning and linking     | Copy scenarios; navigate baseline/reform links      |
# | Schema migration        | Upgrade old scenario files automatically             |
# | Workflow configuration  | Describe a complete analysis pipeline               |

# Clean up the registry
import shutil
shutil.rmtree(REGISTRY_DIR, ignore_errors=True)

print("Generated files you can inspect:")
for f in sorted(TEMPLATES_DIR.iterdir()):
    print(f"  {f.relative_to(DATA_DIR)}")
