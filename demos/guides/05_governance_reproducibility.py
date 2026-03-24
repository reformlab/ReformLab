"""Epic 5 Demo -- Governance and Reproducibility.

Adds the trust layer that makes every simulation run auditable,
reproducible, and tamper-evident:
  1. Immutable run manifests -- sealed documents with versions, seeds, hashes
  2. Assumption and mapping capture -- structured snapshots for audit
  3. Run lineage graph -- parent-child execution tree
  4. Artifact hashing -- SHA-256 integrity verification
  5. Reproducibility check harness -- re-execute and verify outputs match
  6. Warning system for unvalidated templates -- governance warnings
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR
while REPO_ROOT != REPO_ROOT.parent and not (REPO_ROOT / "src").exists():
    REPO_ROOT = REPO_ROOT.parent

SRC_DIR = REPO_ROOT / "src"
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from reformlab.governance import (
    # Core manifest
    RunManifest,
    ManifestIntegrityError,
    ManifestValidationError,
    # Lineage
    LineageGraph,
    LineageIntegrityError,
    get_lineage,
    validate_lineage,
    # Capture helpers
    capture_assumptions,
    capture_mappings,
    capture_policy,
    capture_warnings,
    capture_unvalidated_template_warning,
    capture_unvalidated_mapping_warning,
    capture_unsupported_config_warning,
    TESTED_MAX_HORIZON_YEARS,
    TESTED_MAX_POPULATION_SIZE,
    # Hashing
    hash_file,
    hash_input_artifacts,
    hash_output_artifacts,
    verify_artifact_hashes,
    ArtifactVerificationResult,
    # Reproducibility
    check_reproducibility,
    ReproducibilityResult,
    ReproducibilityValidationError,
)
from reformlab.computation.mapping import FieldMapping, MappingConfig

import pyarrow as pa
import pyarrow.csv as pa_csv
import pyarrow.parquet as pq

DATA_DIR = REPO_ROOT / "notebooks" / "guides" / "data"
OUTPUT_DIR = DATA_DIR / "epic5_outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"Repo root:          {REPO_ROOT}")
print(f"Script directory:   {SCRIPT_DIR}")
print(f"Output directory:   {OUTPUT_DIR}")


# ---------------------------------------------------------------------------
# 1. Immutable Run Manifests (Story 5-1)
# ---------------------------------------------------------------------------
# Every simulation run produces a RunManifest -- an immutable, frozen
# dataclass that captures everything needed to understand and reproduce
# the run:
#
# - Version strings (engine, OpenFisca, adapter, scenario)
# - Random seeds (master + per-year)
# - Policy parameters
# - SHA-256 hashes of input and output files
# - Structured assumptions and variable mappings
# - Step pipeline order
# - Parent/child lineage links
#
# The manifest supports integrity sealing via SHA-256: once sealed,
# any tampering is detected.
# ---------------------------------------------------------------------------

# Create a minimal manifest -- only the 6 required version fields
minimal = RunManifest(
    manifest_id="demo-run-001",
    created_at="2026-02-27T10:00:00Z",
    engine_version="0.1.0",
    openfisca_version="40.0.0",
    adapter_version="1.0.0",
    scenario_version="v1.0",
)

print(f"Manifest ID:       {minimal.manifest_id}")
print(f"Engine version:    {minimal.engine_version}")
print(f"OpenFisca version: {minimal.openfisca_version}")
print(f"Integrity hash:    {minimal.integrity_hash!r}  (empty -- not yet sealed)")
print(f"\nAll optional fields default to empty:")
print(f"  seeds:           {minimal.seeds}")
print(f"  policy:          {minimal.policy}")
print(f"  assumptions:     {minimal.assumptions}")
print(f"  data_hashes:     {minimal.data_hashes}")
print(f"  step_pipeline:   {minimal.step_pipeline}")

# Create a full manifest with all governance fields populated
full_manifest = RunManifest(
    manifest_id="demo-run-002",
    created_at="2026-02-27T10:30:00Z",
    engine_version="0.1.0",
    openfisca_version="40.0.0",
    adapter_version="1.0.0",
    scenario_version="v2.1",
    seeds={"master": 42, "year_2026": 1001, "year_2027": 1002, "year_2028": 1003},
    policy={
        "carbon_tax_rate": 44.60,
        "rebate_amount": 150.0,
        "discount_rate": 0.03,
        "exemptions": ["food", "medicine"],
    },
    assumptions=[
        {"key": "constant_population", "value": True, "source": "scenario", "is_default": True},
        {"key": "no_behavioral_response", "value": True, "source": "user", "is_default": False},
        {"key": "inflation_rate", "value": 0.02, "source": "scenario", "is_default": True},
    ],
    mappings=[
        {"openfisca_name": "household_income", "project_name": "income", "direction": "input"},
        {"openfisca_name": "carbon_tax_paid", "project_name": "carbon_tax", "direction": "output"},
        {"openfisca_name": "lump_sum_rebate", "project_name": "subsidy", "direction": "output"},
    ],
    step_pipeline=["load_population", "compute_baseline", "apply_carbon_tax", "compute_rebate", "vintage_transition"],
    data_hashes={"population.csv": "a" * 64, "emissions.parquet": "b" * 64},
    output_hashes={"results/2026.parquet": "c" * 64, "results/2027.parquet": "d" * 64},
    child_manifests={
        2026: "11111111-1111-1111-1111-111111111111",
        2027: "22222222-2222-2222-2222-222222222222",
        2028: "33333333-3333-3333-3333-333333333333",
    },
)

print(f"Manifest ID: {full_manifest.manifest_id}")
print(f"Seeds:       {full_manifest.seeds}")
print(f"Policy:      {json.dumps(full_manifest.policy, indent=2)}")
print(f"\nAssumptions ({len(full_manifest.assumptions)}):")
for a in full_manifest.assumptions:
    default_tag = "DEFAULT" if a["is_default"] else "OVERRIDE"
    print(f"  [{default_tag:8s}] {a['key']:30s} = {a['value']}  (source: {a['source']})")
print(f"\nStep pipeline: {' -> '.join(full_manifest.step_pipeline)}")
print(f"Data hashes:   {len(full_manifest.data_hashes)} files")
print(f"Output hashes: {len(full_manifest.output_hashes)} files")
print(f"Child years:   {sorted(full_manifest.child_manifests.keys())}")

# Seal the manifest with an integrity hash
sealed = full_manifest.with_integrity_hash()

print(f"Integrity hash: {sealed.integrity_hash}")
print(f"Hash length:    {len(sealed.integrity_hash)} hex chars (SHA-256)")

# Verify integrity -- no exception means it's valid
sealed.verify_integrity()
print("\nIntegrity verification: PASSED")

# Demonstrate tamper detection: create a manifest with a wrong hash
tampered = RunManifest(
    manifest_id=sealed.manifest_id,
    created_at=sealed.created_at,
    engine_version=sealed.engine_version,
    openfisca_version=sealed.openfisca_version,
    adapter_version=sealed.adapter_version,
    scenario_version=sealed.scenario_version,
    seeds=sealed.seeds,
    policy={"carbon_tax_rate": 99.99},  # <-- tampered!
    assumptions=sealed.assumptions,
    mappings=sealed.mappings,
    step_pipeline=sealed.step_pipeline,
    data_hashes=sealed.data_hashes,
    output_hashes=sealed.output_hashes,
    child_manifests=sealed.child_manifests,
    integrity_hash=sealed.integrity_hash,  # original hash, but content changed
)

try:
    tampered.verify_integrity()
except ManifestIntegrityError as e:
    print(f"\nTamper detection: CAUGHT")
    print(f"  {e}")

# JSON round-trip: serialize and deserialize with deterministic output
json_str = sealed.to_json()

print(f"Serialized JSON length: {len(json_str)} bytes")
print(f"First 200 chars: {json_str[:200]}...")

# Deserialize and verify round-trip integrity
restored = RunManifest.from_json(json_str)
restored.verify_integrity()
print(f"\nRound-trip:        PASSED")
print(f"Same manifest_id:  {restored.manifest_id == sealed.manifest_id}")
print(f"Same hash:         {restored.integrity_hash == sealed.integrity_hash}")
print(f"Same seeds:        {restored.seeds == sealed.seeds}")
print(f"Same policy:       {restored.policy == sealed.policy}")

# Determinism: serializing twice gives identical bytes
json_str_2 = restored.to_json()
print(f"\nDeterministic:     {json_str == json_str_2}  (byte-identical across machines)")

# Validation catches bad data early with actionable errors
bad_inputs = [
    ("Empty manifest_id", dict(manifest_id="", created_at="2026-01-01T00:00:00Z",
     engine_version="0.1.0", openfisca_version="40.0.0", adapter_version="1.0.0",
     scenario_version="v1.0")),
    ("Bad hash format", dict(manifest_id="test", created_at="2026-01-01T00:00:00Z",
     engine_version="0.1.0", openfisca_version="40.0.0", adapter_version="1.0.0",
     scenario_version="v1.0", data_hashes={"file": "not-a-sha256"})),
    ("Bad seed type", dict(manifest_id="test", created_at="2026-01-01T00:00:00Z",
     engine_version="0.1.0", openfisca_version="40.0.0", adapter_version="1.0.0",
     scenario_version="v1.0", seeds={"master": True})),
]

print("Validation catches errors at construction time:")
for label, kwargs in bad_inputs:
    try:
        RunManifest(**kwargs)
    except ManifestValidationError as e:
        print(f"  [{label}] {e}")


# ---------------------------------------------------------------------------
# 2. Assumption and Mapping Capture (Story 5-2)
# ---------------------------------------------------------------------------
# At orchestration time, the system automatically captures:
#
# - Assumptions: structured entries distinguishing defaults from user overrides
# - Mappings: variable mapping configurations (OpenFisca <-> project names)
# - Policy: deep-copied snapshots immune to post-capture mutation
#
# These capture functions produce manifest-ready data structures.
# ---------------------------------------------------------------------------

# Capture assumptions: defaults vs user overrides
defaults = {
    "discount_rate": 0.03,
    "inflation_rate": 0.02,
    "constant_population": True,
    "behavioral_response": False,
}
overrides = {
    "discount_rate": 0.05,      # User chose a higher discount rate
    "behavioral_response": True, # User enabled behavioral response
}

assumptions = capture_assumptions(
    defaults=defaults,
    overrides=overrides,
    source_label="scenario",
)

print(f"Captured {len(assumptions)} assumptions (sorted by key):")
print(f"{'Key':30s}  {'Value':>10s}  {'Source':>10s}  {'Status':>10s}")
print("-" * 68)
for entry in assumptions:
    status = "DEFAULT" if entry["is_default"] else "OVERRIDE"
    print(f"{entry['key']:30s}  {str(entry['value']):>10s}  {entry['source']:>10s}  {status:>10s}")

print(f"\nOverrides are clearly distinguishable from defaults")
print(f"Override count: {sum(1 for a in assumptions if not a['is_default'])}")
print(f"Default count:  {sum(1 for a in assumptions if a['is_default'])}")

# Capture variable mappings from a MappingConfig
mapping_config = MappingConfig(
    mappings=(
        FieldMapping(
            openfisca_name="household_income", project_name="income",
            direction="input", pa_type=pa.float64(),
        ),
        FieldMapping(
            openfisca_name="carbon_tax_paid", project_name="carbon_tax",
            direction="output", pa_type=pa.float64(),
        ),
        FieldMapping(
            openfisca_name="lump_sum_rebate", project_name="subsidy",
            direction="output", pa_type=pa.float64(),
        ),
        FieldMapping(
            openfisca_name="region_code", project_name="region",
            direction="both", pa_type=pa.utf8(),
        ),
    ),
    source_path=Path("/data/mappings/carbon-tax-v2.yaml"),
)

mapping_entries = capture_mappings(mapping_config)

print(f"Captured {len(mapping_entries)} mapping entries:")
print(f"{'OpenFisca Name':25s}  {'Project Name':15s}  {'Direction':10s}  {'Source File'}")
print("-" * 85)
for m in mapping_entries:
    print(
        f"{m['openfisca_name']:25s}  {m['project_name']:15s}  "
        f"{m['direction']:10s}  {m.get('source_file', 'N/A')}"
    )

# Capture policy: deep copy ensures immutability
params = {
    "carbon_tax_rate": 44.60,
    "rebate_amount": 150.0,
    "exemptions": ["food", "medicine"],
    "nested": {"sub_rate": 0.15},
}

snapshot = capture_policy(params)

# Mutate the original -- snapshot is unaffected
params["carbon_tax_rate"] = 99.99
params["exemptions"].append("energy")
params["nested"]["sub_rate"] = 0.99

print("Original (mutated after capture):")
print(f"  carbon_tax_rate: {params['carbon_tax_rate']}")
print(f"  exemptions:      {params['exemptions']}")
print(f"  nested.sub_rate: {params['nested']['sub_rate']}")

print(f"\nSnapshot (frozen at capture time):")
print(f"  carbon_tax_rate: {snapshot['carbon_tax_rate']}")
print(f"  exemptions:      {snapshot['exemptions']}")
print(f"  nested.sub_rate: {snapshot['nested']['sub_rate']}")
print(f"\nDeep copy confirmed: mutations don't leak into the manifest")


# ---------------------------------------------------------------------------
# 3. Run Lineage Graph (Story 5-3)
# ---------------------------------------------------------------------------
# Multi-year simulations create a tree of manifests: a parent manifest
# (the orchestration run) links to child manifests (one per simulated year).
# Lineage enables:
#
# - Tracing exactly which run produced which year's output
# - Validating that parent-child links are bidirectionally consistent
# - Querying the execution tree (roots, leaves, traversal)
# ---------------------------------------------------------------------------

# Build a parent manifest with 3 child years
parent_id = "00000000-0000-0000-0000-000000000001"
child_ids = {
    2026: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    2027: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
    2028: "cccccccc-cccc-cccc-cccc-cccccccccccc",
}

parent_manifest = RunManifest(
    manifest_id=parent_id,
    created_at="2026-02-27T10:00:00Z",
    engine_version="0.1.0",
    openfisca_version="40.0.0",
    adapter_version="1.0.0",
    scenario_version="v1.0",
    seeds={"master": 42},
    child_manifests=child_ids,
)

# Extract the lineage graph
lineage = get_lineage(parent_manifest)

print(f"Lineage for: {lineage.manifest_id}")
print(f"  is_root:  {lineage.is_root}  (no parent)")
print(f"  is_leaf:  {lineage.is_leaf}  (has children)")
print(f"  parent:   {lineage.get_parent()}")
print(f"  children: {len(lineage.get_children())} years")
for year, cid in sorted(lineage.get_children().items()):
    print(f"    {year}: {cid}")

# Build child manifests and validate bidirectional lineage
children = {}
for year, cid in child_ids.items():
    children[year] = RunManifest(
        manifest_id=cid,
        created_at=f"2026-02-27T10:{year - 2025:02d}:00Z",
        engine_version="0.1.0",
        openfisca_version="40.0.0",
        adapter_version="1.0.0",
        scenario_version="v1.0",
        seeds={"master": 42, f"year_{year}": year ^ 42},
        parent_manifest_id=parent_id,  # <-- links back to parent
    )

# Validate: parent->child and child->parent links are consistent
validate_lineage(parent_manifest, children)
print("Lineage validation: PASSED")
print(f"\nAll {len(children)} child manifests have correct parent_manifest_id")
print(f"Parent's child_manifests match all child manifest_ids")

# Show each child's lineage
for year, child in sorted(children.items()):
    child_lineage = get_lineage(child)
    print(f"\n  Year {year}: is_root={child_lineage.is_root}, is_leaf={child_lineage.is_leaf}")
    print(f"           parent={child_lineage.get_parent()}")

# Demonstrate lineage integrity error: what if a child points to the wrong parent?
bad_child = RunManifest(
    manifest_id=child_ids[2026],
    created_at="2026-02-27T10:01:00Z",
    engine_version="0.1.0",
    openfisca_version="40.0.0",
    adapter_version="1.0.0",
    scenario_version="v1.0",
    parent_manifest_id="99999999-9999-9999-9999-999999999999",  # wrong parent!
)

try:
    validate_lineage(parent_manifest, {2026: bad_child, **{y: children[y] for y in [2027, 2028]}})
except LineageIntegrityError as e:
    print(f"Lineage break detected: {e}")

# What about a missing child?
try:
    validate_lineage(parent_manifest, {2026: children[2026], 2027: children[2027]})  # missing 2028
except LineageIntegrityError as e:
    print(f"Missing child:          {e}")


# ---------------------------------------------------------------------------
# 4. Artifact Hashing (Story 5-4)
# ---------------------------------------------------------------------------
# Every input and output file is hashed with SHA-256 at run time. Later,
# we can verify that files haven't changed. This is the foundation for:
#
# - Detecting data drift (someone updated the input CSV)
# - Confirming output integrity (results weren't modified after the run)
# - Enabling reproducibility checks (same inputs should produce same outputs)
# ---------------------------------------------------------------------------

# Create sample input/output CSV files
input_table = pa.table({
    "household_id": pa.array([0, 1, 2, 3, 4], type=pa.int64()),
    "income": pa.array([15000.0, 25000.0, 35000.0, 55000.0, 85000.0], type=pa.float64()),
    "region_code": pa.array(["11", "75", "84", "32", "44"], type=pa.utf8()),
})

output_table = pa.table({
    "household_id": pa.array([0, 1, 2, 3, 4], type=pa.int64()),
    "carbon_tax": pa.array([180.0, 185.0, 190.0, 195.0, 200.0], type=pa.float64()),
    "subsidy": pa.array([250.0, 180.0, 100.0, 0.0, 0.0], type=pa.float64()),
})

input_path = OUTPUT_DIR / "demo_input.csv"
output_path = OUTPUT_DIR / "demo_output.csv"

pa_csv.write_csv(input_table, input_path)
pa_csv.write_csv(output_table, output_path)

# Hash individual files
input_hash = hash_file(input_path)
output_hash = hash_file(output_path)

print(f"Input file hash:  {input_hash}")
print(f"Output file hash: {output_hash}")
print(f"Hash length:      {len(input_hash)} hex chars (SHA-256)")

# Batch hash input and output artifacts
input_hashes = hash_input_artifacts({
    "population": input_path,
})

output_hashes = hash_output_artifacts({
    "results_2026": output_path,
})

print("Input hashes:")
for key, h in input_hashes.items():
    print(f"  {key}: {h[:32]}...")

print(f"\nOutput hashes:")
for key, h in output_hashes.items():
    print(f"  {key}: {h[:32]}...")

# Verify hashes -- all should pass
result = verify_artifact_hashes(
    {**input_hashes, **output_hashes},
    {"population": input_path, "results_2026": output_path},
)
print(f"\nVerification passed:  {result.passed}")
print(f"Mismatches:           {result.mismatches}")
print(f"Missing:              {result.missing}")

# Simulate data drift: modify the input file and re-verify
drifted_table = pa.table({
    "household_id": pa.array([0, 1, 2, 3, 4], type=pa.int64()),
    "income": pa.array([15000.0, 25000.0, 35000.0, 55000.0, 99999.0], type=pa.float64()),  # changed!
    "region_code": pa.array(["11", "75", "84", "32", "44"], type=pa.utf8()),
})
pa_csv.write_csv(drifted_table, input_path)

result_after_drift = verify_artifact_hashes(
    input_hashes,
    {"population": input_path},
)
print(f"After data drift:")
print(f"  Passed:     {result_after_drift.passed}")
print(f"  Mismatches: {result_after_drift.mismatches}")

# Restore the original for later sections
pa_csv.write_csv(input_table, input_path)

# Verify with a RunManifest (merges data_hashes + output_hashes)
hash_manifest = RunManifest(
    manifest_id="hash-demo",
    created_at="2026-02-27T11:00:00Z",
    engine_version="0.1.0",
    openfisca_version="40.0.0",
    adapter_version="1.0.0",
    scenario_version="v1.0",
    data_hashes=input_hashes,
    output_hashes=output_hashes,
)

result_from_manifest = verify_artifact_hashes(
    hash_manifest,
    {"population": input_path, "results_2026": output_path},
)
print(f"\nVerification via RunManifest: passed={result_from_manifest.passed}")


# ---------------------------------------------------------------------------
# 5. Reproducibility Check Harness (Story 5-5)
# ---------------------------------------------------------------------------
# The ultimate governance test: can we re-execute a run from its manifest
# and get the same outputs?
#
# check_reproducibility() automates the full cycle:
# 1. Extract seeds, policy, and pipeline from the manifest
# 2. Call a rerun_callable with those inputs
# 3. Compare rerun output hashes against the manifest's stored hashes
# 4. Optionally apply floating-point tolerance for cross-machine drift
# ---------------------------------------------------------------------------

# Build a manifest that records the original run
original_input_hash = hash_file(input_path)
original_output_hash = hash_file(output_path)

repro_manifest = RunManifest(
    manifest_id="repro-demo-001",
    created_at="2026-02-27T12:00:00Z",
    engine_version="0.1.0",
    openfisca_version="40.0.0",
    adapter_version="1.0.0",
    scenario_version="v1.0",
    seeds={"master": 42, "year_2026": 1001},
    policy={"carbon_tax_rate": 44.60, "rebate_amount": 150.0},
    step_pipeline=["compute_baseline", "apply_carbon_tax", "compute_rebate"],
    data_hashes={"population": original_input_hash},
    output_hashes={"results_2026": original_output_hash},
    child_manifests={2026: "11111111-1111-1111-1111-111111111111"},
)

# Define a rerun callable that writes the same output (simulating deterministic rerun)
rerun_output_path = OUTPUT_DIR / "rerun_output.csv"

def deterministic_rerun(**kwargs):
    """Simulates a deterministic rerun -- same seeds produce same output."""
    print(f"  Rerun called with:")
    print(f"    seeds:            {kwargs['seeds']}")
    print(f"    policy:           {kwargs['policy']}")
    print(f"    scenario_version: {kwargs['scenario_version']}")
    print(f"    step_pipeline:    {kwargs['step_pipeline']}")
    print(f"    year_range:       {kwargs['year_range']}")
    # Write identical output (deterministic simulation)
    pa_csv.write_csv(output_table, rerun_output_path)

# Run the reproducibility check
print("Running reproducibility check (strict, bit-identical):")
result = check_reproducibility(
    manifest=repro_manifest,
    input_paths={"population": input_path},
    output_paths={"results_2026": rerun_output_path},
    rerun_callable=deterministic_rerun,
)

print(f"\n{result.details()}")

# Simulate a non-reproducible run: slightly different output
# We use Parquet here because it preserves exact column types -- CSV type
# inference can change float64 to int64 when values happen to be whole
# numbers, causing schema mismatches that confuse the tolerance comparison.
output_parquet_path = OUTPUT_DIR / "demo_output.parquet"
rerun_parquet_path = OUTPUT_DIR / "rerun_output.parquet"
reference_parquet_path = OUTPUT_DIR / "reference_output.parquet"

pq.write_table(output_table, output_parquet_path)
original_parquet_hash = hash_file(output_parquet_path)

# Build a manifest referencing the Parquet output
parquet_manifest = RunManifest(
    manifest_id="repro-parquet-001",
    created_at="2026-02-27T12:30:00Z",
    engine_version="0.1.0",
    openfisca_version="40.0.0",
    adapter_version="1.0.0",
    scenario_version="v1.0",
    seeds={"master": 42, "year_2026": 1001},
    policy={"carbon_tax_rate": 44.60, "rebate_amount": 150.0},
    step_pipeline=["compute_baseline", "apply_carbon_tax", "compute_rebate"],
    data_hashes={"population": original_input_hash},
    output_hashes={"results_2026": original_parquet_hash},
    child_manifests={2026: "11111111-1111-1111-1111-111111111111"},
)

non_deterministic_output = pa.table({
    "household_id": pa.array([0, 1, 2, 3, 4], type=pa.int64()),
    "carbon_tax": pa.array([180.001, 185.0, 190.0, 195.0, 200.0], type=pa.float64()),  # tiny drift
    "subsidy": pa.array([250.0, 180.0, 100.0, 0.0, 0.0], type=pa.float64()),
})

def drifted_rerun(**kwargs):
    """Simulates a non-deterministic rerun -- floating-point drift."""
    pq.write_table(non_deterministic_output, rerun_parquet_path)

# Strict check: FAILS (hash mismatch due to 0.001 drift)
print("Strict check with floating-point drift:")
strict_result = check_reproducibility(
    manifest=parquet_manifest,
    input_paths={"population": input_path},
    output_paths={"results_2026": rerun_parquet_path},
    rerun_callable=drifted_rerun,
)
print(f"  {strict_result.details()}")

# Tolerant check: PASSES (drift of 0.001 is within tolerance of 0.01)
pq.write_table(output_table, reference_parquet_path)

print(f"\nTolerant check (tolerance=0.01):")
tolerant_result = check_reproducibility(
    manifest=parquet_manifest,
    input_paths={"population": input_path},
    output_paths={"results_2026": rerun_parquet_path},
    rerun_callable=drifted_rerun,
    tolerance=0.01,
    reference_output_paths={"results_2026": reference_parquet_path},
)
print(f"  {tolerant_result.details()}")

# Contract validation: check_reproducibility catches bad inputs early
print("Contract validation:")

# Negative tolerance
try:
    check_reproducibility(
        manifest=repro_manifest,
        input_paths={"population": input_path},
        output_paths={"results_2026": rerun_output_path},
        rerun_callable=deterministic_rerun,
        tolerance=-0.1,
    )
except ReproducibilityValidationError as e:
    print(f"  [Negative tolerance] {e}")

# Tolerance > 0 without reference paths
try:
    check_reproducibility(
        manifest=repro_manifest,
        input_paths={"population": input_path},
        output_paths={"results_2026": rerun_output_path},
        rerun_callable=deterministic_rerun,
        tolerance=0.01,
        reference_output_paths=None,
    )
except ReproducibilityValidationError as e:
    print(f"  [Missing references] {e}")

# Missing input path that manifest requires
try:
    check_reproducibility(
        manifest=repro_manifest,
        input_paths={},  # missing 'population' key
        output_paths={"results_2026": rerun_output_path},
        rerun_callable=deterministic_rerun,
    )
except ReproducibilityValidationError as e:
    print(f"  [Missing inputs]     {e}")


# ---------------------------------------------------------------------------
# 6. Warning System for Unvalidated Templates (Story 5-6)
# ---------------------------------------------------------------------------
# Not all scenarios are created equal. Some are validated and
# production-ready; others are experimental drafts. The governance layer
# generates warnings when:
#
# - A scenario template is not marked as validated in the registry
# - A mapping configuration is not marked as validated
# - Run configuration exceeds tested ranges (horizon years, population size)
#
# These warnings are captured in the manifest so stakeholders can assess
# output trustworthiness.
# ---------------------------------------------------------------------------

# Unvalidated template warning
w1 = capture_unvalidated_template_warning(
    scenario_name="carbon-tax-progressive-2026",
    scenario_version="draft-abc123",
    is_validated=False,
)
print(f"Unvalidated template: {w1}")

# No warning when validated
w2 = capture_unvalidated_template_warning(
    scenario_name="carbon-tax-baseline-2026",
    scenario_version="v2.1-final",
    is_validated=True,
)
print(f"\nValidated template:   {w2}  (None = no warning)")

# Unknown name/version falls back gracefully
w3 = capture_unvalidated_template_warning(is_validated=False)
print(f"\nMissing name/version: {w3}")

# Unvalidated mapping warning
m_warn = capture_unvalidated_mapping_warning(
    source_file="mappings/carbon-tax-experimental.yaml",
    is_validated=False,
)
print(f"Unvalidated mapping: {m_warn}")

m_ok = capture_unvalidated_mapping_warning(
    source_file="mappings/carbon-tax-v2.yaml",
    is_validated=True,
)
print(f"Validated mapping:   {m_ok}  (None = no warning)")

# Configuration range warnings
print(f"Tested ranges: max horizon = {TESTED_MAX_HORIZON_YEARS} years, "
      f"max population = {TESTED_MAX_POPULATION_SIZE:,} households")

# Within range -- no warnings
safe = capture_unsupported_config_warning(horizon_years=10, population_size=50_000)
print(f"\nWithin range:    {safe}  (empty list = no warnings)")

# At boundary -- no warnings (boundary is exclusive)
boundary = capture_unsupported_config_warning(
    horizon_years=TESTED_MAX_HORIZON_YEARS,
    population_size=TESTED_MAX_POPULATION_SIZE,
)
print(f"At boundary:     {boundary}  (boundary = OK)")

# Beyond range -- warnings emitted
beyond = capture_unsupported_config_warning(horizon_years=30, population_size=500_000)
print(f"\nBeyond range ({len(beyond)} warnings):")
for w in beyond:
    print(f"  {w}")

# Combined warning capture (as the orchestrator does it)
all_warnings = capture_warnings(
    scenario_name="carbon-tax-experimental",
    scenario_version="draft-001",
    is_validated=False,
    additional_warnings=[
        "Data quality: 3 households have missing income values",
        "Population data is from 2023 census (may be outdated)",
    ],
)

print(f"Total warnings captured: {len(all_warnings)}")
for i, w in enumerate(all_warnings, 1):
    print(f"  [{i}] {w}")

# These warnings go directly into the manifest
warned_manifest = RunManifest(
    manifest_id="warned-run-001",
    created_at="2026-02-27T14:00:00Z",
    engine_version="0.1.0",
    openfisca_version="40.0.0",
    adapter_version="1.0.0",
    scenario_version="draft-001",
    warnings=all_warnings,
)
print(f"\nManifest warnings: {len(warned_manifest.warnings)} stored")
print(f"These persist in the sealed JSON for auditors to review")


# ---------------------------------------------------------------------------
# Putting It All Together: Full Governance Flow
# ---------------------------------------------------------------------------
# In production, the orchestrator does all of this automatically. Here we
# assemble the full flow manually to show how the pieces connect.
# ---------------------------------------------------------------------------

# === STEP 1: Capture assumptions and policy before the run ===
run_assumptions = capture_assumptions(
    defaults={"constant_population": True, "discount_rate": 0.03, "inflation": 0.02},
    overrides={"discount_rate": 0.05},
    source_label="carbon-tax-scenario",
)
run_policy = capture_policy({
    "carbon_tax_rate": 44.60,
    "rebate_amount": 150.0,
    "start_year": 2026,
    "end_year": 2028,
})

# === STEP 2: Capture variable mappings ===
run_mappings = capture_mappings(mapping_config)

# === STEP 3: Check for governance warnings ===
run_warnings = capture_warnings(
    scenario_name="carbon-tax-progressive",
    scenario_version="v2.1",
    is_validated=True,  # This scenario is validated -- no template warning
)
# Add mapping validation warning
mapping_warn = capture_unvalidated_mapping_warning(
    source_file=str(mapping_config.source_path),
    is_validated=mapping_config.is_validated,
)
if mapping_warn:
    run_warnings.append(mapping_warn)
# Add config range warnings
run_warnings.extend(capture_unsupported_config_warning(horizon_years=3, population_size=100))

# === STEP 4: Hash input artifacts ===
pa_csv.write_csv(input_table, input_path)  # ensure fresh
run_input_hashes = hash_input_artifacts({"population": input_path})

# === STEP 5: (Run the simulation -- omitted, using demo output) ===
pa_csv.write_csv(output_table, output_path)

# === STEP 6: Hash output artifacts ===
run_output_hashes = hash_output_artifacts({"results_2026": output_path})

# === STEP 7: Assemble the manifest ===
run_manifest = RunManifest(
    manifest_id="production-run-2026-02-27",
    created_at="2026-02-27T15:00:00Z",
    engine_version="0.1.0",
    openfisca_version="40.0.0",
    adapter_version="1.0.0",
    scenario_version="v2.1",
    seeds={"master": 42, "year_2026": 1001},
    policy=run_policy,
    assumptions=run_assumptions,
    mappings=run_mappings,
    warnings=run_warnings,
    step_pipeline=["load_population", "compute_baseline", "apply_carbon_tax", "vintage_transition"],
    data_hashes=run_input_hashes,
    output_hashes=run_output_hashes,
    child_manifests={2026: "11111111-1111-1111-1111-111111111111"},
)

# === STEP 8: Seal with integrity hash ===
sealed_manifest = run_manifest.with_integrity_hash()
sealed_manifest.verify_integrity()

# === STEP 9: Serialize for storage ===
manifest_json = sealed_manifest.to_json()
manifest_path = OUTPUT_DIR / "run_manifest.json"
manifest_path.write_text(manifest_json)

print("=== Full Governance Flow Complete ===")
print(f"\nManifest saved to: {manifest_path.relative_to(REPO_ROOT)}")
print(f"Manifest size:     {len(manifest_json)} bytes")
print(f"Integrity hash:    {sealed_manifest.integrity_hash[:32]}...")
print(f"\nAssumptions:  {len(sealed_manifest.assumptions)} entries")
print(f"Mappings:     {len(sealed_manifest.mappings)} entries")
print(f"Warnings:     {len(sealed_manifest.warnings)} entries")
print(f"Data hashes:  {len(sealed_manifest.data_hashes)} files")
print(f"Output hashes:{len(sealed_manifest.output_hashes)} files")
print(f"Seeds:        {sealed_manifest.seeds}")
print(f"Pipeline:     {' -> '.join(sealed_manifest.step_pipeline)}")

if sealed_manifest.warnings:
    print(f"\nGovernance warnings:")
    for w in sealed_manifest.warnings:
        print(f"  {w}")
else:
    print(f"\nNo governance warnings -- scenario and mappings are validated")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
# | Capability                 | In plain terms                              |
# |----------------------------|---------------------------------------------|
# | Immutable run manifests    | Frozen, sealed documents -- tamper-evident   |
# | Assumption capture         | Defaults vs overrides -- full transparency   |
# | Mapping capture            | OpenFisca variable mapping snapshots         |
# | Policy snapshot            | Deep-copied, immune to post-capture mutation |
# | Run lineage graph          | Parent-child execution tree                  |
# | Artifact hashing           | SHA-256 for drift/tampering detection        |
# | Hash verification          | Stored vs current with clear diagnostics     |
# | Reproducibility harness    | Re-execute and verify (strict or tolerant)   |
# | Template warnings          | Flags for unvalidated scenarios/mappings     |
# | Config range warnings      | Flags for exceeding tested ranges            |
# | Deterministic JSON         | Byte-identical serialization across machines |
# ---------------------------------------------------------------------------

print("Generated files in notebooks/data/epic5_outputs:")
for path in sorted(OUTPUT_DIR.iterdir()):
    print(f"  {path.relative_to(DATA_DIR)}")
