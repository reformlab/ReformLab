

# Story 16.4: Build Replication Workflow Notebook Demo

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **researcher** (Marco persona),
I want a pedagogical notebook that demonstrates the complete replication package lifecycle — running a simulation, exporting a self-contained package, importing it in a clean context, reproducing the results, and comparing original vs. reproduced outputs,
so that I can confidently share my analysis with co-authors, knowing they can reproduce my exact results on a different machine, and I can cite the package as a reproducibility artifact in publications.

## Acceptance Criteria

1. **AC-1: End-to-end replication demo** — Given the notebook, when run end-to-end, then it demonstrates: running a simulation, exporting a replication package (both directory and compressed ZIP), clearing local state (simulating a clean environment), importing the package, reproducing the simulation, and comparing original vs. reproduced results.
2. **AC-2: CI execution** — Given the notebook, when run in CI via `uv run pytest --nbmake notebooks/guides/11_replication_workflow.ipynb -v`, then it completes without errors.
3. **AC-3: Package inspection** — Given the notebook output, when inspected, then it shows: package directory listing with all artifact files, `package-index.json` contents with roles and hash excerpts, integrity check confirmation (`integrity_verified=True`), and provenance file contents when provided.
4. **AC-4: Reproduction comparison** — Given the notebook output, when inspected, then it shows: `ReproductionResult.summary()` output with PASSED status, `numerical_match=True`, zero discrepancies, and the reproduced `SimulationResult` matching the original.
5. **AC-5: Marco's sharing workflow** — Given the notebook output, when inspected, then it narratively demonstrates the researcher sharing workflow: Marco exports a replication package, a simulated "co-author" imports and reproduces it in a clean context, confirming that the exported package (containing `package-index.json`, `policy.json`, `scenario-metadata.json`, and `run-manifest.json`) is sufficient for independent reproduction on a different machine.
6. **AC-6: Provenance inclusion** — Given the notebook output, when inspected, then it demonstrates exporting a package with population generation provenance (`population_provenance=`) and calibration provenance (`calibration_provenance=`), and shows the provenance data is round-trip recoverable after import.

## Tasks / Subtasks

- [x] Task 1: Create notebook file with setup cells (AC: 2)
  - [x] 1.1: Create `notebooks/guides/11_replication_workflow.ipynb` with title markdown cell and overview (matching existing guide numbering pattern)
  - [x] 1.2: Add setup code cell with `from __future__ import annotations`, path resolution (`NOTEBOOK_DIR` / `REPO_ROOT` / `SRC_DIR` pattern from existing guides), a local `show(table, n)` helper copied verbatim from `06_portfolio_comparison.ipynb`, and imports: `reformlab` API (`run_scenario`, `ScenarioConfig`, `create_quickstart_adapter`), `reformlab.governance.replication` (`export_replication_package`, `import_replication_package`, `reproduce_from_package`), `pathlib.Path`, `json`, `shutil`, `tempfile`
  - [x] 1.3: Add output directory setup: `OUTPUT_DIR = NOTEBOOK_DIR / "data" / "replication_demo"` with `OUTPUT_DIR.mkdir(parents=True, exist_ok=True)`

- [x] Task 2: Section 1 — Run a simulation (AC: 1, 5)
  - [x] 2.1: Markdown cell introducing Marco's scenario: "Marco, a labor economist, wants to analyze a carbon tax's distributional impact and share results with a co-author for publication"
  - [x] 2.2: Code cell: create adapter with `create_quickstart_adapter(carbon_tax_rate=44.0)`, define `ScenarioConfig` with `template_name="carbon-tax"`, `policy={"carbon_tax_rate": 44.0}`, `start_year=2025`, `end_year=2027`, `seed=42`
  - [x] 2.3: Code cell: `result = run_scenario(config, adapter=adapter)`, print the result `__repr__`, show panel output sample with `show(result.panel_output.table, n=5)`
  - [x] 2.4: Markdown cell: explain what was produced — panel output, manifest, and why reproducibility matters

- [x] Task 3: Section 2 — Export a replication package (AC: 1, 3)
  - [x] 3.1: Markdown cell explaining export: "Marco packages his entire analysis into a self-contained replication package"
  - [x] 3.2: Code cell: export using the convenience method `metadata = result.export_replication_package(OUTPUT_DIR)`, print `metadata.package_id`, `metadata.artifact_count`, `metadata.package_path`
  - [x] 3.3: Markdown cell explaining the package directory structure (reference the layout from Dev Notes)
  - [x] 3.4: Code cell: list package contents using `Path.rglob("*")`, showing the directory tree. Print each file with relative path and size.
  - [x] 3.5: Code cell: read and display `package-index.json` contents — show `package_id`, `source_manifest_id`, and for each artifact show `path`, `role`, `artifact_type`, and hash excerpt (first 12 chars)
  - [x] 3.6: Markdown cell: explain the integrity guarantees — SHA-256 hashes, role classification

- [x] Task 4: Section 3 — Export with provenance (AC: 6)
  - [x] 4.1: Markdown cell: "For maximum traceability, Marco includes population generation and calibration provenance in the package"
  - [x] 4.2: Code cell: build a representative `population_provenance` dict with `pipeline_description`, `generation_seed`, `step_log` (1 load + 1 merge step), `assumption_chain` (1 entry), `source_configs` (1 INSEE source)
  - [x] 4.3: Code cell: build a representative `calibration_provenance` dict with `entries` containing a calibration result entry (domain, beta, objective, convergence)
  - [x] 4.4: Code cell: export with provenance `metadata_prov = result.export_replication_package(OUTPUT_DIR, population_provenance=pop_prov, calibration_provenance=cal_prov)`, show artifact count (should be baseline + 2), list provenance files
  - [x] 4.5: Markdown cell: explain what provenance enables — full traceability from data source to result

- [x] Task 5: Section 4 — Simulate sharing (clear state + import) (AC: 1, 5)
  - [x] 5.1: Markdown cell: "Marco shares the package with his co-author Clara. She receives the package and imports it on her machine." Narratively delete local references to simulate a clean environment.
  - [x] 5.2: Code cell: save `package_path = metadata.package_path` (from Task 3 basic export), then `del result, metadata` to simulate clean state. Print confirmation that local state is cleared.
  - [x] 5.3: Code cell: `pkg = import_replication_package(package_path)`, print `pkg.package_id`, `pkg.integrity_verified`, `pkg.manifest.manifest_id`, `pkg.panel_table.num_rows`, `pkg.policy`
  - [x] 5.4: Markdown cell: explain what integrity verification means and what the co-author now has access to

- [x] Task 6: Section 5 — Reproduce the simulation (AC: 1, 4)
  - [x] 6.1: Markdown cell: "Clara reproduces Marco's simulation using the imported package"
  - [x] 6.2: Code cell: create a fresh adapter `fresh_adapter = create_quickstart_adapter(carbon_tax_rate=44.0)`, reproduce with `repro = reproduce_from_package(pkg, fresh_adapter, tolerance=0.0)`
  - [x] 6.3: Code cell: print `repro.summary()` showing full reproduction report
  - [x] 6.4: Code cell: verify `repro.passed is True`, `repro.numerical_match is True`, `len(repro.discrepancies) == 0`. Print confirmation.
  - [x] 6.5: Markdown cell: explain what the reproduction proves — deterministic outputs with identical seeds and adapter

- [x] Task 7: Section 6 — Compare original vs. reproduced (AC: 4)
  - [x] 7.1: Markdown cell: "Clara compares the reproduced results with the originals to confirm exact match"
  - [x] 7.2: Code cell: extract original and reproduced panel tables (`pkg.panel_table` and `repro.reproduced_result.panel_output.table`), show side-by-side first 5 rows of each
  - [x] 7.3: Code cell: compute column-level comparison — for each numeric column, compute max absolute difference and print (should all be 0.0)
  - [x] 7.4: Markdown cell: explain that zero discrepancy confirms cross-environment reproducibility

- [x] Task 8: Section 7 — Import with provenance (AC: 6)
  - [x] 8.1: Markdown cell: "Clara can also inspect the provenance metadata to understand every methodological choice"
  - [x] 8.2: Code cell: import the provenance-enriched package from Task 4 (`pkg_prov = import_replication_package(metadata_prov.package_path)`), print `pkg_prov.population_provenance is not None`, `pkg_prov.calibration_provenance is not None`
  - [x] 8.3: Code cell: pretty-print the population provenance (`json.dumps(pkg_prov.population_provenance, indent=2)`) and calibration provenance
  - [x] 8.4: Markdown cell: explain traceability — from INSEE data source through merge methods to calibrated parameters to final result

- [x] Task 9: Section 8 — Compressed package for distribution (AC: 1)
  - [x] 9.1: Markdown cell: "For distribution via email or file sharing, the package can be compressed into a single ZIP file"
  - [x] 9.2: Code cell: re-run the simulation (`result2 = run_scenario(config2, adapter=adapter2)` with same config/adapter), export with `compress=True`, print ZIP path and file size
  - [x] 9.3: Code cell: import from ZIP, verify integrity, show it works identically to directory import
  - [x] 9.4: Markdown cell: note that ZIP and directory imports produce equivalent results

- [x] Task 10: Conclusion and cleanup (AC: 1, 5)
  - [x] 10.1: Markdown cell: wrap up Marco's story — "Marco and Clara have confirmed that ReformLab's replication packages provide full reproducibility. Marco can cite the package hash in his paper, and any reviewer can verify the results." Summarize what was demonstrated.
  - [x] 10.2: Code cell: cleanup output directory `shutil.rmtree(OUTPUT_DIR, ignore_errors=True)`, print "Cleanup complete"

- [x] Task 11: Add notebook to CI (AC: 2)
  - [x] 11.1: In `.github/workflows/ci.yml`, within the `ci` job, add the following step immediately after the existing pytest step(s): `- run: uv run pytest --nbmake notebooks/guides/11_replication_workflow.ipynb -v`

- [x] Task 12: Verify end-to-end (AC: all)
  - [x] 12.1: Run `uv run pytest --nbmake notebooks/guides/11_replication_workflow.ipynb -v` locally
  - [x] 12.2: Verify all cells execute without error
  - [x] 12.3: Run `uv run ruff check notebooks/` if any .py helper files were created (unlikely)

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**Notebook location:** `notebooks/guides/11_replication_workflow.ipynb` — follows the existing numbered guide convention (01–10 exist, this is 11).

**No new source files needed.** This story creates only:
1. A Jupyter notebook (`.ipynb`)
2. A one-line addition to `.github/workflows/ci.yml`

**No test files needed.** The notebook IS the test — `nbmake` executes all cells sequentially and fails on any exception.

### Notebook Cell Structure Pattern (from existing guides)

Every notebook in this project follows this pattern:

1. **First markdown cell:** Title with `#`, "What is this?", prerequisites, estimated time
2. **First code cell:** `from __future__ import annotations`, path resolution boilerplate, imports, output directory setup
3. **Alternating sections:** Markdown explanation → Code execution → Markdown interpretation
4. **Final markdown cell:** "Next Steps" summary

**Path resolution boilerplate (MUST USE):**
```python
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

NOTEBOOK_DIR = Path.cwd() if "__file__" not in dir() else Path(__file__).parent
if not (NOTEBOOK_DIR / "data").exists() and (NOTEBOOK_DIR / "notebooks" / "data").exists():
    NOTEBOOK_DIR = NOTEBOOK_DIR / "notebooks"
REPO_ROOT = NOTEBOOK_DIR if (NOTEBOOK_DIR / "src").exists() else NOTEBOOK_DIR.parent
SRC_DIR = REPO_ROOT / "src"
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
```

This pattern ensures the notebook works both from Jupyter (interactive) and from nbmake (CI).

**`show()` function:** Define a local `show(table, n)` helper inline in the setup cell, copied verbatim from `06_portfolio_comparison.ipynb`. Do not import `show` from `reformlab` — use the local helper exclusively.

### Key Imports for This Notebook

```python
# Core simulation API
from reformlab import (
    ScenarioConfig,
    create_quickstart_adapter,
    run_scenario,
)

# Replication module — all types exported from governance
from reformlab.governance.replication import (
    export_replication_package,
    import_replication_package,
    reproduce_from_package,
)
```

### API Usage Reference

**Export (Story 16.1):**
```python
metadata = export_replication_package(result, output_path, compress=False)
# Returns ReplicationPackageMetadata with package_id, package_path, artifact_count, index
```

**Export with provenance (Story 16.3):**
```python
metadata = export_replication_package(
    result, output_path,
    population_provenance=pop_prov_dict,
    calibration_provenance=cal_prov_dict,
)
```

**Convenience method on SimulationResult:**
```python
metadata = result.export_replication_package(output_path, compress=True)
```

**Import (Story 16.2):**
```python
pkg = import_replication_package(package_path)  # directory or .zip
# Returns ImportedPackage with panel_table, policy, manifest, integrity_verified,
#   population_provenance, calibration_provenance
```

**Reproduce (Story 16.2):**
```python
repro = reproduce_from_package(pkg, adapter, tolerance=0.0)
# Returns ReproductionResult with passed, numerical_match, discrepancies, summary()
```

**Convenience method on ImportedPackage:**
```python
repro = pkg.reproduce(adapter, tolerance=0.0)
```

### Package Directory Structure (for narrative display in notebook)

```
{package_id}/
├── package-index.json           # Artifact manifest with SHA-256 hashes
├── data/
│   └── panel-output.parquet     # Simulation results (household × year)
├── config/
│   ├── policy.json              # Policy parameters snapshot
│   └── scenario-metadata.json   # Seeds, step pipeline, assumptions
├── manifests/
│   └── run-manifest.json        # Full RunManifest with provenance
└── provenance/                  # Optional (Story 16.3)
    ├── population-generation.json
    └── calibration.json
```

### Marco's Journey (from UX Specification)

The notebook narratively tells Marco's story:

1. **Marco runs his analysis** — carbon tax distributional impact on French households
2. **Marco exports a replication package** — self-contained directory with all artifacts
3. **Marco shares the package** — sends to co-author Clara (ZIP or directory)
4. **Clara imports and reproduces** — on her machine, verifies integrity, re-runs simulation
5. **Clara confirms match** — reproduction report shows PASSED, zero discrepancies
6. **Publication confidence** — Marco cites the package hash in his paper; any reviewer can verify

This maps directly to the PRD's "Journey 3: Marco — Academic Researcher" and the UX spec's researcher persona workflow.

### Representative Provenance Data (for Task 4)

**Population provenance** — a plausible minimal example:
```python
population_provenance = {
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
```

**Calibration provenance** — a plausible minimal example:
```python
calibration_provenance = {
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
```

### CI Configuration Update

In `.github/workflows/ci.yml`, within the `ci` job, add the following step immediately after the existing pytest step(s):
```yaml
      - run: uv run pytest --nbmake notebooks/guides/11_replication_workflow.ipynb -v
```

### Cross-Story Dependencies

| Story | Relationship |
|---|---|
| **16.1** | Direct dependency: `export_replication_package()`, `PackageIndex`, `ReplicationPackageMetadata` |
| **16.2** | Direct dependency: `import_replication_package()`, `reproduce_from_package()`, `ImportedPackage`, `ReproductionResult` |
| **16.3** | Direct dependency: `population_provenance` and `calibration_provenance` parameters on export/import |
| **6.1** | Uses `SimulationResult` convenience methods |
| **6.2** | Notebook structure pattern reference (quickstart) |

### Anti-Patterns from Previous Stories (DO NOT REPEAT)

| Issue | Prevention |
|---|---|
| Notebook cells that depend on variables defined much earlier without context | Each section should be relatively self-contained; re-state key variables when needed |
| Using `pandas` for display when project uses PyArrow | Use the `show()` helper pattern from existing guides, or `pa.Table` methods directly |
| Importing OpenFisca directly | Use `create_quickstart_adapter()` — the quickstart adapter from `reformlab` API |
| Hardcoded absolute paths | Use the `NOTEBOOK_DIR` / `REPO_ROOT` path resolution boilerplate |
| Network calls in CI | No network access needed — everything is local (synthetic data, mock adapter) |
| Forgetting cleanup | `shutil.rmtree(OUTPUT_DIR, ignore_errors=True)` at the end to clean up created packages |
| Using `result.panel_output.table.head()` | `pa.Table` has no `.head()` — use `show(table, n=5)` or `table.slice(0, 5)` |
| Defining `show()` differently from existing guides | Copy the exact `show()` helper from `06_portfolio_comparison.ipynb` |
| Non-deterministic outputs | Always use `seed=42` for all operations |

### Important Scope Boundaries

**What this story does:**
- Creates one Jupyter notebook (`notebooks/guides/11_replication_workflow.ipynb`)
- Adds one line to CI configuration (`.github/workflows/ci.yml`)

**What this story does NOT do:**
- No new Python source files under `src/`
- No new test files under `tests/`
- No modifications to existing source code
- No new dependencies in `pyproject.toml`
- No modifications to existing notebooks

### Expected Cell Count

Target: ~20 code cells + ~14 markdown cells (similar to `09_population_generation.ipynb` which has 14 code + 18 markdown cells). The notebook should be thorough but not verbose — each cell should teach one concept.

### Testing Standards Summary

- **CI tool:** `nbmake` (already a dev dependency)
- **CI command:** `uv run pytest --nbmake notebooks/guides/11_replication_workflow.ipynb -v`
- **Execution model:** All cells run sequentially with shared state; any exception = failure
- **No conftest needed:** Notebooks don't use pytest fixtures
- **Determinism:** `seed=42` everywhere; `create_quickstart_adapter` produces deterministic output
- **Cleanup:** Output directory removed at end of notebook to avoid CI artifacts

### Project Structure Notes

**New files:**
- `notebooks/guides/11_replication_workflow.ipynb` — the notebook demo

**Modified files:**
- `.github/workflows/ci.yml` — add one nbmake line

**Alignment:** File numbering follows existing convention (01–10 exist → 11 is next). Notebook lives in `notebooks/guides/` matching all Phase 2 guide notebooks.

### References

- [Source: docs/epics.md#Epic 16 — Story-Level AC for BKL-1604]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md — Marco persona, researcher sharing workflow]
- [Source: _bmad-output/planning-artifacts/prd.md — Journey 3: Marco, FR54, FR55]
- [Source: src/reformlab/governance/replication.py — export_replication_package(), import_replication_package(), reproduce_from_package(), ImportedPackage, ReproductionResult]
- [Source: src/reformlab/interfaces/api.py — SimulationResult.export_replication_package(), create_quickstart_adapter(), ScenarioConfig, run_scenario()]
- [Source: src/reformlab/governance/__init__.py — public API exports for replication types]
- [Source: notebooks/guides/06_portfolio_comparison.ipynb — notebook structure pattern, show() helper, path resolution boilerplate]
- [Source: notebooks/guides/09_population_generation.ipynb — pedagogical notebook pattern]
- [Source: .github/workflows/ci.yml — nbmake CI integration pattern]
- [Source: _bmad-output/implementation-artifacts/16-3-include-population-generation-assumptions-and-calibration-provenance.md — provenance data formats, Story 16.3 patterns]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — implementation was clean on first attempt. Notebook executed in 3.59s via nbmake with 1 passed.

### Completion Notes List

- ✅ Created `notebooks/guides/11_replication_workflow.ipynb` with 21 code cells + 19 markdown cells covering all 8 guide sections
- ✅ Setup cell: exact `show()` helper copied verbatim from `06_portfolio_comparison.ipynb`, defensive path resolution boilerplate, all required imports including `tempfile`
- ✅ Section 1: Marco's simulation with `create_quickstart_adapter(carbon_tax_rate=44.0)`, `ScenarioConfig(template_name="carbon-tax", seed=42)`, `run_scenario()`, `show(result.panel_output.table, n=5)`
- ✅ Section 2: Basic export via `result.export_replication_package(OUTPUT_DIR)`, directory listing with `Path.rglob("*")` + file sizes, `package-index.json` inspection with role/type/hash-excerpt columns
- ✅ Section 3: Provenance export with representative INSEE pop_prov dict (1 load + 1 merge step, 1 assumption, 1 source_config) and L-BFGS-B cal_prov dict; shows baseline+2 artifact count delta; lists provenance files
- ✅ Section 4: `del result, metadata` clean-environment simulation; `import_replication_package(package_path)` with `integrity_verified=True` confirmed
- ✅ Section 5: `reproduce_from_package(pkg, fresh_adapter, tolerance=0.0)`; `repro.summary()` printed; assertions `repro.passed is True`, `repro.numerical_match is True`, `len(repro.discrepancies) == 0` all pass
- ✅ Section 6: Column-level comparison using `pa.types.is_floating`/`is_integer` + `to_pylist()` — zero max_abs_diff across all numeric columns
- ✅ Section 7: Import provenance-enriched package; `json.dumps()` pretty-print of both provenance dicts; round-trip recovery confirmed
- ✅ Section 8: Re-run simulation, `compress=True`, ZIP path + size printed; `import_replication_package(zip_path)` with `integrity_verified=True`
- ✅ Conclusion: Marco/Clara narrative wrap-up table + next steps
- ✅ Cleanup: `shutil.rmtree(OUTPUT_DIR, ignore_errors=True)` — no CI artifacts left
- ✅ CI: Added `uv run pytest --nbmake notebooks/guides/11_replication_workflow.ipynb -v` as last step in `.github/workflows/ci.yml`
- ✅ `uv run pytest --nbmake notebooks/guides/11_replication_workflow.ipynb -v` → 1 passed in 3.59s

### File List

- `notebooks/guides/11_replication_workflow.ipynb` (created)
- `.github/workflows/ci.yml` (modified — appended nbmake step for guide 11)
