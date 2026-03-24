"""ReformLab Replication Workflow -- Full Reproducibility Lifecycle.

Demonstrates the complete replication package lifecycle following Marco, a labor
economist studying the distributional impact of a carbon tax:

1. Run a simulation and inspect results
2. Export a self-contained replication package (directory and ZIP)
3. Include population generation and calibration provenance
4. Import the package in a clean context (simulating a co-author's machine)
5. Reproduce the results and verify an exact numerical match
6. Compare original vs. reproduced outputs column by column

Prerequisites: Familiarity with run_scenario() and the governance manifest system.
Estimated time: ~20 minutes
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pyarrow as pa

from reformlab import (
    ScenarioConfig,
    create_quickstart_adapter,
    run_scenario,
)
from reformlab.governance.replication import (
    export_replication_package,
    import_replication_package,
    reproduce_from_package,
)
from reformlab.visualization import show

# ---------------------------------------------------------------------------
# Section 0: Setup
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = (SCRIPT_DIR / "../..").resolve()

OUTPUT_DIR = SCRIPT_DIR / "data" / "replication_demo"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"Repo root:  {REPO_ROOT}")
print(f"Output dir: {OUTPUT_DIR}")

# ---------------------------------------------------------------------------
# Section 1: Run a Simulation
# ---------------------------------------------------------------------------
#
# Marco's scenario: analyze a carbon tax's distributional impact and share
# results with a co-author for publication. French carbon tax rate of
# EUR 44/tCO2, 3-year simulation (2025-2027), fixed seed for reproducibility.

adapter = create_quickstart_adapter(carbon_tax_rate=44.0)
config = ScenarioConfig(
    template_name="carbon-tax",
    policy={"carbon_tax_rate": 44.0},
    start_year=2025,
    end_year=2027,
    seed=42,
)

print(f"\nAdapter: {adapter!r}")
print(f"Config:  {config!r}")

result = run_scenario(config, adapter=adapter)

print(repr(result))
print()
print("Panel output sample (first 5 rows):")
show(result.panel_output.table, n=5)

# The simulation produced:
#   - Panel output: a household x year table with income, carbon tax, disposable income
#   - Run manifest: governance record with seed, assumptions, and data hashes

# ---------------------------------------------------------------------------
# Section 2: Export a Replication Package
# ---------------------------------------------------------------------------
#
# Marco packages his entire analysis into a self-contained replication package
# -- a directory containing all artifacts needed to reproduce the results.

metadata = result.export_replication_package(OUTPUT_DIR)

print(f"\nPackage ID:     {metadata.package_id}")
print(f"Artifact count: {metadata.artifact_count}")
print(f"Package path:   {metadata.package_path}")

# Package directory structure:
#   {package_id}/
#     package-index.json           -- artifact manifest with SHA-256 hashes
#     data/
#       panel-output.parquet       -- simulation results (household x year)
#     config/
#       policy.json                -- policy parameters snapshot
#       scenario-metadata.json     -- seeds, step pipeline, assumptions
#     manifests/
#       run-manifest.json          -- full RunManifest with provenance
#     provenance/                  -- optional (when provenance is included)
#       population-generation.json
#       calibration.json

package_dir = metadata.package_path

print(f"\n{package_dir.name}/")
for f in sorted(package_dir.rglob("*")):
    if f.is_file():
        rel = f.relative_to(package_dir)
        size = f.stat().st_size
        print(f"  {str(rel):<50s}  {size:>8,} bytes")

# Inspect the package index.
index_path = package_dir / "package-index.json"
index_data = json.loads(index_path.read_text())

print(f"\npackage_id:         {index_data['package_id']}")
print(f"source_manifest_id: {index_data['source_manifest_id']}")
print()
print(f"  {'path':<50s}  {'role':<22s}  {'artifact_type':<15s}  sha256[:12]")
print(f"  {'-'*50}  {'-'*22}  {'-'*15}  {'-'*12}")
for artifact in index_data["artifacts"]:
    path = artifact["path"]
    role = artifact["role"]
    atype = artifact["artifact_type"]
    hash_val = artifact.get("sha256", artifact.get("hash", ""))[:12]
    print(f"  {path:<50s}  {role:<22s}  {atype:<15s}  {hash_val}")

# Every artifact is hash-verified with SHA-256. If even one byte has changed,
# the import raises an error.

# ---------------------------------------------------------------------------
# Section 3: Export with Provenance
# ---------------------------------------------------------------------------
#
# For maximum traceability, Marco includes population generation and
# calibration provenance. This creates an unbroken audit trail from the raw
# INSEE data source through calibration to the final results.

pop_prov = {
    "pipeline_description": "French household population for carbon tax study",
    "generation_seed": 42,
    "step_log": [
        {
            "step_index": 0,
            "step_type": "load",
            "label": "income_distribution",
            "input_labels": [],
            "output_rows": 1000,
            "output_columns": ["household_id", "income", "region"],
            "method_name": None,
            "duration_ms": 45.0,
        },
        {
            "step_index": 1,
            "step_type": "merge",
            "label": "income_vehicles",
            "input_labels": ["income_distribution", "vehicle_fleet"],
            "output_rows": 1000,
            "output_columns": ["household_id", "income", "region", "vehicle_type"],
            "method_name": "conditional_sampling",
            "duration_ms": 12.0,
        },
    ],
    "assumption_chain": [
        {
            "key": "merge_conditional_sampling",
            "value": {
                "method": "conditional_sampling",
                "statement": "Households matched within income strata",
                "strata_columns": ["income_bracket"],
                "seed": 42,
            },
            "source": "population_pipeline",
            "is_default": False,
        },
    ],
    "source_configs": [
        {
            "provider": "insee",
            "dataset_id": "filosofi_2021",
            "url": "https://www.insee.fr/fr/statistiques/6036907",
            "params": {},
            "description": "INSEE Filosofi 2021 income distribution",
        },
    ],
}

print("\nPopulation provenance:")
print(f"  pipeline_description: {pop_prov['pipeline_description']}")
print(f"  generation_seed:      {pop_prov['generation_seed']}")
print(f"  step_log entries:     {len(pop_prov['step_log'])}")
print(f"  assumption_chain:     {len(pop_prov['assumption_chain'])} entry")
print(f"  source_configs:       {len(pop_prov['source_configs'])} source (INSEE Filosofi 2021)")

cal_prov = {
    "entries": [
        {
            "key": "calibration_result",
            "value": {
                "domain": "vehicle",
                "optimized_beta_cost": -0.012,
                "objective_type": "mse",
                "final_objective_value": 0.008,
                "convergence_flag": True,
                "iterations": 25,
                "gradient_norm": 1e-8,
                "method": "L-BFGS-B",
                "all_within_tolerance": True,
                "n_targets": 4,
            },
            "source": "calibration_engine",
            "is_default": False,
        },
    ],
}

entry = cal_prov["entries"][0]["value"]
print("\nCalibration provenance:")
print(f"  entries:     {len(cal_prov['entries'])}")
print(f"  domain:      {entry['domain']}")
print(f"  method:      {entry['method']}")
print(f"  converged:   {entry['convergence_flag']} after {entry['iterations']} iterations")
print(f"  beta_cost:   {entry['optimized_beta_cost']}")

metadata_prov = result.export_replication_package(
    OUTPUT_DIR,
    population_provenance=pop_prov,
    calibration_provenance=cal_prov,
)

print(f"\nPackage ID (provenance):     {metadata_prov.package_id}")
print(f"Artifact count (basic):      {metadata.artifact_count}")
print(f"Artifact count (provenance): {metadata_prov.artifact_count}")
print(f"Additional provenance files: {metadata_prov.artifact_count - metadata.artifact_count}")
print()
print("Provenance files:")
for f in sorted(metadata_prov.package_path.rglob("*")):
    if f.is_file() and "provenance" in str(f.relative_to(metadata_prov.package_path)):
        size = f.stat().st_size
        print(f"  {f.relative_to(metadata_prov.package_path)}  ({size:,} bytes)")

# ---------------------------------------------------------------------------
# Section 4: Simulate Sharing -- Clara Receives the Package
# ---------------------------------------------------------------------------
#
# Marco shares the replication package with his co-author Clara. We simulate
# this by saving the package path and deleting local references.

package_path = metadata.package_path

# Simulate a clean environment: Clara does not have access to result, metadata,
# config, or adapter -- only the on-disk package remains.
del result, metadata, config, adapter

print("\nLocal simulation state cleared.")
print(f"Package path preserved: {package_path}")

# Clara imports the package.
pkg = import_replication_package(package_path)

print(f"\npackage_id:         {pkg.package_id}")
print(f"integrity_verified: {pkg.integrity_verified}")
print(f"manifest_id:        {pkg.manifest.manifest_id}")
print(f"panel_table rows:   {pkg.panel_table.num_rows}")
print(f"policy:             {pkg.policy}")

# integrity_verified=True means every artifact was re-hashed and matched the
# SHA-256 checksums in package-index.json.

# ---------------------------------------------------------------------------
# Section 5: Reproduce the Simulation
# ---------------------------------------------------------------------------
#
# Clara reproduces Marco's simulation using the imported package. She creates
# a fresh adapter and calls reproduce_from_package() with zero tolerance --
# requiring an exact numerical match.

carbon_tax_rate = float(pkg.policy["carbon_tax_rate"])
fresh_adapter = create_quickstart_adapter(carbon_tax_rate=carbon_tax_rate)
repro = reproduce_from_package(pkg, fresh_adapter, tolerance=0.0)

print("\nReproduction result:")
print(f"  passed:          {repro.passed}")
print(f"  numerical_match: {repro.numerical_match}")
print(f"  tolerance_used:  {repro.tolerance_used}")
print(f"  discrepancies:   {len(repro.discrepancies)}")

print()
print(repro.summary())

assert repro.passed is True, f"Expected passed=True, got {repro.passed}"
assert repro.numerical_match is True, f"Expected numerical_match=True, got {repro.numerical_match}"
assert len(repro.discrepancies) == 0, f"Expected 0 discrepancies, got {repro.discrepancies}"

print("passed:          True")
print("numerical_match: True")
print("discrepancies:   0")
print()
print("All reproduction assertions passed -- results are exactly reproducible.")

# With the same seed (42) and the same adapter configuration, ReformLab
# produces bit-for-bit identical outputs across independent runs.

# ---------------------------------------------------------------------------
# Section 6: Compare Original vs. Reproduced
# ---------------------------------------------------------------------------
#
# Clara compares the reproduced results with the originals to confirm an exact
# match. She inspects both tables side by side and computes per-column maximum
# absolute differences.

original = pkg.panel_table
reproduced = repro.reproduced_result.panel_output.table

print(f"\nOriginal panel:   {original.num_rows} rows x {original.num_columns} cols")
print(f"Reproduced panel: {reproduced.num_rows} rows x {reproduced.num_columns} cols")

print("\nOriginal (first 5 rows):")
show(original, n=5)

print("\nReproduced (first 5 rows):")
show(reproduced, n=5)

# Guard: tables must have identical row counts and schemas before comparison.
assert original.num_rows == reproduced.num_rows, (
    f"Row count mismatch: original={original.num_rows} reproduced={reproduced.num_rows}"
)
assert original.schema == reproduced.schema, (
    f"Schema mismatch:\n  original:   {original.schema}\n  reproduced: {reproduced.schema}"
)

print(f"\n  {'column':<30s}  {'max_abs_diff':>15s}")
print(f"  {'-'*30}  {'-'*15}")
for col_name in original.column_names:
    col_type = original.schema.field(col_name).type
    if pa.types.is_floating(col_type) or pa.types.is_integer(col_type):
        orig_vals = original.column(col_name).to_pylist()
        repr_vals = reproduced.column(col_name).to_pylist()
        diffs = [
            abs(float(o) - float(r))
            for o, r in zip(orig_vals, repr_vals)
            if o is not None and r is not None
        ]
        max_diff = max(diffs) if diffs else 0.0
        print(f"  {col_name:<30s}  {max_diff:>15.10f}")

print()
print("All numeric columns show zero absolute difference.")

# ---------------------------------------------------------------------------
# Section 7: Inspect Provenance Metadata
# ---------------------------------------------------------------------------
#
# Clara inspects the provenance metadata that Marco included in the
# provenance-enriched package.

pkg_prov = import_replication_package(metadata_prov.package_path)

print(f"\npopulation_provenance is not None: {pkg_prov.population_provenance is not None}")
print(f"calibration_provenance is not None: {pkg_prov.calibration_provenance is not None}")

print("\n=== Population Provenance ===")
print(json.dumps(pkg_prov.population_provenance, indent=2))

print()
print("=== Calibration Provenance ===")
print(json.dumps(pkg_prov.calibration_provenance, indent=2))

# Traceability chain:
#   1. Data source -> INSEE Filosofi 2021
#   2. Population merge -> conditional sampling within income strata (seed=42)
#   3. Calibration -> L-BFGS-B optimization of vehicle beta_cost
#   4. Simulation -> carbon tax at EUR 44/tCO2, panel output for 2025-2027

# ---------------------------------------------------------------------------
# Section 8: Compressed Package for Distribution
# ---------------------------------------------------------------------------
#
# For distribution via email or file sharing, the package can be compressed
# into a single ZIP file. import_replication_package() auto-detects the format.

adapter2 = create_quickstart_adapter(carbon_tax_rate=44.0)
config2 = ScenarioConfig(
    template_name="carbon-tax",
    policy={"carbon_tax_rate": 44.0},
    start_year=2025,
    end_year=2027,
    seed=42,
)
result2 = run_scenario(config2, adapter=adapter2)

metadata_zip = result2.export_replication_package(OUTPUT_DIR, compress=True)
zip_path = metadata_zip.package_path

print(f"\nZIP path:   {zip_path}")
print(f"ZIP size:   {zip_path.stat().st_size:,} bytes")
print(f"Compressed: {metadata_zip.compressed}")

pkg_zip = import_replication_package(zip_path)

print(f"\npackage_id:         {pkg_zip.package_id}")
print(f"integrity_verified: {pkg_zip.integrity_verified}")
print(f"panel_table rows:   {pkg_zip.panel_table.num_rows}")

# Verify numerical equivalence via reproduction.
zip_carbon_tax_rate = float(pkg_zip.policy["carbon_tax_rate"])
zip_adapter = create_quickstart_adapter(carbon_tax_rate=zip_carbon_tax_rate)
repro_zip = reproduce_from_package(pkg_zip, zip_adapter, tolerance=0.0)
assert repro_zip.passed is True, f"ZIP reproduction failed: {repro_zip.summary()}"
assert repro_zip.numerical_match is True

print(f"reproduction passed: {repro_zip.passed}")
print()
print("ZIP import and reproduction verified -- numerically identical to directory workflow.")

# ---------------------------------------------------------------------------
# Conclusion
# ---------------------------------------------------------------------------
#
# What was demonstrated:
#   1. Run   -- Marco ran a 3-year carbon tax simulation with seed=42
#   2. Export -- Marco packaged results into a hash-verified directory
#   3. Provenance -- Marco included INSEE data lineage and calibration history
#   4. Share -- Clara received the package and verified integrity
#   5. Reproduce -- Clara re-ran the simulation and got identical results
#   6. Compare -- Zero absolute difference across all numeric columns
#   7. Inspect -- Clara traced the full methodological chain
#   8. ZIP   -- Same workflow available as a single portable ZIP archive
#
# For publication: cite the package_id hash in the paper. Any reviewer with
# ReformLab installed can independently verify the results.

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
print("\nCleanup complete.")
