

# Story 16.3: Include Population Generation Assumptions and Calibration Provenance

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **researcher**,
I want the replication package to include population generation configuration and calibration provenance alongside the simulation results,
so that every methodological choice — from raw data source selection through statistical merging to calibrated taste parameters — is traceable and the population can be deterministically regenerated on a different machine.

## Acceptance Criteria

1. **AC-1: Population generation provenance in exported package** — Given a simulation run where the caller provides population provenance metadata (step log, assumption chain, source configs, pipeline description, generation seed), when the replication package is exported via `export_replication_package(result, output_path, population_provenance=provenance_dict)`, then a `provenance/population-generation.json` file is created in the package containing the full pipeline configuration: data sources used, merge methods, statistical assumptions, and the generation seed. The file is listed in `package-index.json` with `role="metadata"` and `artifact_type="lineage"`.
2. **AC-2: Calibration provenance in exported package** — Given a simulation run where the caller provides calibration provenance metadata (optimized β values, objective function type, convergence diagnostics, calibration target metadata, holdout validation metrics), when the replication package is exported via `export_replication_package(result, output_path, calibration_provenance=calibration_dict)`, then a `provenance/calibration.json` file is created in the package containing the full calibration provenance. The file is listed in `package-index.json` with `role="metadata"` and `artifact_type="lineage"`.
3. **AC-3: Population regeneration from imported provenance** — Given a package with `provenance/population-generation.json`, when imported via `import_replication_package()`, then `ImportedPackage.population_provenance` is a `dict[str, Any]` containing the pipeline configuration with enough information (source configs, merge methods, seeds, step order) for a developer to reconstruct and re-execute the population pipeline on a different machine. Packages without this file set `population_provenance` to `None`.
4. **AC-4: Full traceability from data source to final result** — Given the provenance files in an imported package, when a reviewer inspects `population_provenance` and `calibration_provenance`, then every methodological choice is traceable: which institutional data sources were used, which merge methods with which assumptions, what calibration targets were used, what objective function, and what the final calibrated parameters are.
5. **AC-5: Backward compatibility** — Given a replication package exported by Story 16.1/16.2 (without provenance files), when imported, then `ImportedPackage.population_provenance` and `ImportedPackage.calibration_provenance` are both `None`, and all existing import/export/reproduction functionality works unchanged.

## Tasks / Subtasks

- [ ] Task 1: Extend `export_replication_package()` with provenance parameters (AC: 1, 2, 5)
  - [ ] 1.1: Add `population_provenance: dict[str, Any] | None = None` keyword parameter to `export_replication_package()`
  - [ ] 1.2: Add `calibration_provenance: dict[str, Any] | None = None` keyword parameter to `export_replication_package()`
  - [ ] 1.3: When either provenance dict is not None, create `provenance/` subdirectory inside the package directory
  - [ ] 1.4: Write `provenance/population-generation.json` with `json.dumps(population_provenance, sort_keys=True, indent=2)` when provided
  - [ ] 1.5: Write `provenance/calibration.json` with `json.dumps(calibration_provenance, sort_keys=True, indent=2)` when provided
  - [ ] 1.6: Add provenance artifacts to `PackageArtifact` list with `role="metadata"`, `artifact_type="lineage"`, and computed SHA-256 hash — population-generation description: `"Population generation pipeline configuration and assumptions"`, calibration description: `"Calibration provenance with optimized parameters and diagnostics"`
  - [ ] 1.7: Structured logging: `event=provenance_exported population=%s calibration=%s` (True/False for each)

- [ ] Task 2: Update `SimulationResult.export_replication_package()` convenience method (AC: 1, 2)
  - [ ] 2.1: Add `population_provenance: dict[str, Any] | None = None` and `calibration_provenance: dict[str, Any] | None = None` keyword parameters to the convenience method on `SimulationResult`
  - [ ] 2.2: Forward both parameters to `export_replication_package()`

- [ ] Task 3: Extend `ImportedPackage` with provenance fields (AC: 3, 4, 5)
  - [ ] 3.1: Add `population_provenance: dict[str, Any] | None = None` field to `ImportedPackage` (after `integrity_verified`, with default `None`)
  - [ ] 3.2: Add `calibration_provenance: dict[str, Any] | None = None` field to `ImportedPackage` (after `population_provenance`, with default `None`)
  - [ ] 3.3: In `__post_init__`, deep-copy both provenance dicts when not None (following the existing `policy` / `scenario_metadata` deep-copy pattern)

- [ ] Task 4: Extend `_load_package_from_dir()` to load provenance files (AC: 3, 4, 5)
  - [ ] 4.1: After loading existing artifacts (Task 2 in 16.2), check for `provenance/population-generation.json` — if present, load via `json.loads()` into `dict[str, Any]`; if absent, set to `None`
  - [ ] 4.2: Check for `provenance/calibration.json` — if present, load via `json.loads()`; if absent, set to `None`
  - [ ] 4.3: Pass loaded provenance dicts to `ImportedPackage` constructor
  - [ ] 4.4: Structured logging: `event=provenance_loaded population=%s calibration=%s` (True/False for each)

- [ ] Task 5: Update public API exports (AC: all)
  - [ ] 5.1: No new public types needed — `ImportedPackage` already exported. Verify `__all__` in `governance/__init__.py` is unchanged.

- [ ] Task 6: Write tests (AC: all)
  - [ ] 6.1: Add test classes to `tests/governance/test_replication.py` (extending the existing file)
  - [ ] 6.2: `TestExportPopulationProvenance`: export with `population_provenance` dict → verify `provenance/population-generation.json` exists, content matches, artifact in index with correct role/type
  - [ ] 6.3: `TestExportCalibrationProvenance`: export with `calibration_provenance` dict → verify `provenance/calibration.json` exists, content matches, artifact in index
  - [ ] 6.4: `TestExportBothProvenance`: export with both → verify both files, both in index, artifact count increased by 2
  - [ ] 6.5: `TestExportNoProvenance`: export with neither (default) → verify no `provenance/` directory, artifact count unchanged from 16.1 baseline (4)
  - [ ] 6.6: `TestExportProvenanceCompressed`: export with provenance + `compress=True` → verify ZIP contains provenance files
  - [ ] 6.7: `TestImportWithPopulationProvenance`: round-trip export with population provenance → import → verify `pkg.population_provenance` matches input
  - [ ] 6.8: `TestImportWithCalibrationProvenance`: round-trip export with calibration provenance → import → verify `pkg.calibration_provenance` matches input
  - [ ] 6.9: `TestImportWithBothProvenance`: round-trip with both → verify both fields populated
  - [ ] 6.10: `TestImportWithoutProvenance`: import old-style package (no provenance/) → verify both fields are `None`
  - [ ] 6.11: `TestImportProvenanceIntegrity`: corrupt a provenance file after export → import raises `ReplicationPackageError` with hash mismatch
  - [ ] 6.12: `TestImportProvenanceMutableFieldIsolation`: verify deep-copy of provenance dicts (mutating returned dict doesn't affect package)
  - [ ] 6.13: `TestReproduceWithProvenance`: export with provenance → import → reproduce → verify provenance doesn't interfere with reproduction
  - [ ] 6.14: `TestConvenienceMethodWithProvenance`: `SimulationResult.export_replication_package()` correctly forwards provenance kwargs
  - [ ] 6.15: `TestProvenanceArtifactHashVerification`: verify provenance artifact hashes in `package-index.json` match actual file content

- [ ] Task 7: Lint, type-check, regression (AC: all)
  - [ ] 7.1: `uv run ruff check src/reformlab/governance/ src/reformlab/interfaces/ tests/governance/`
  - [ ] 7.2: `uv run mypy src/reformlab/governance/ src/reformlab/interfaces/`
  - [ ] 7.3: `uv run pytest tests/` — all tests pass (existing + new)

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**Module location:** Extend `src/reformlab/governance/replication.py` — add provenance parameters to the existing `export_replication_package()` function. Also extend `src/reformlab/interfaces/api.py` for the `SimulationResult` convenience method. No new files in `src/` needed.

**Updated module file layout after this story (changes only):**
```
src/reformlab/governance/
└── replication.py             # Updated: add provenance params to export,
                               #   extend ImportedPackage with provenance fields,
                               #   extend _load_package_from_dir to load provenance

src/reformlab/interfaces/
└── api.py                     # Updated: add provenance params to
                               #   SimulationResult.export_replication_package()
```

**Every file starts with** `from __future__ import annotations`.

**Frozen dataclasses for all types** — `ImportedPackage` already uses `@dataclass(frozen=True)`. The new optional fields use `None` as default, and `__post_init__` is extended to deep-copy non-None dicts.

**No new types needed** — Provenance is `dict[str, Any] | None`. The caller is responsible for preparing the dict content using existing serialization methods (`PipelineAssumptionChain.to_governance_entries()`, `capture_calibration_provenance()`, etc.). This keeps the replication module's responsibility narrow: packaging/unpackaging, not domain-specific serialization.

**Error reuse** — Reuse `ReplicationPackageError` for any provenance-related export/import failures.

**Structured logging** — `logging.getLogger(__name__)` with `key=value` format matching the existing pattern.

### Updated Package Directory Structure

After this story, the replication package optionally contains:

```
{package_id}/
├── package-index.json
├── data/
│   └── panel-output.parquet
├── config/
│   ├── policy.json
│   └── scenario-metadata.json
├── manifests/
│   ├── run-manifest.json
│   └── year-{N}.json           (optional, from 16.1)
└── provenance/                  # NEW — only when provenance data provided
    ├── population-generation.json   # NEW (optional)
    └── calibration.json             # NEW (optional)
```

**Provenance files are optional.** When neither `population_provenance` nor `calibration_provenance` is provided to `export_replication_package()`, the `provenance/` directory is not created and the package layout is unchanged from Story 16.1/16.2.

### Key Implementation Details

#### Export Changes (in `export_replication_package()`)

After writing the existing artifacts (panel output, policy, scenario metadata, manifest) and before building `PackageIndex`, insert provenance writing:

```python
# ── Provenance artifacts (Story 16.3) ──────────────────────────────────
if population_provenance is not None or calibration_provenance is not None:
    provenance_dir = package_dir / "provenance"
    provenance_dir.mkdir()

    if population_provenance is not None:
        pop_prov_path = provenance_dir / "population-generation.json"
        pop_prov_path.write_text(
            json.dumps(population_provenance, sort_keys=True, indent=2),
            encoding="utf-8",
        )
        artifacts_info.append(
            (pop_prov_path, "metadata", "lineage",
             "Population generation pipeline configuration and assumptions"),
        )

    if calibration_provenance is not None:
        cal_prov_path = provenance_dir / "calibration.json"
        cal_prov_path.write_text(
            json.dumps(calibration_provenance, sort_keys=True, indent=2),
            encoding="utf-8",
        )
        artifacts_info.append(
            (cal_prov_path, "metadata", "lineage",
             "Calibration provenance with optimized parameters and diagnostics"),
        )
```

**IMPORTANT:** The `PackageArtifactType` literal union in `replication.py` must be extended to include `"lineage"` as a valid value.

#### Import Changes (in `_load_package_from_dir()`)

After loading existing artifacts and before building `ImportedPackage`:

```python
# ── Load provenance files (Story 16.3, optional) ────────────────────────
pop_prov_path = package_dir / "provenance" / "population-generation.json"
population_provenance: dict[str, Any] | None = None
if pop_prov_path.exists():
    population_provenance = json.loads(pop_prov_path.read_text(encoding="utf-8"))

cal_prov_path = package_dir / "provenance" / "calibration.json"
calibration_provenance: dict[str, Any] | None = None
if cal_prov_path.exists():
    calibration_provenance = json.loads(cal_prov_path.read_text(encoding="utf-8"))
```

**Note:** Provenance files are NOT loaded independently of the artifact index. If a provenance file is listed in `package-index.json`, its hash was already verified during the integrity check loop (step 4 of the import algorithm). If a provenance file exists on disk but is NOT listed in the index (shouldn't happen with packages exported by this code), it is still loaded — the index is the authority for integrity, not for file discovery of provenance. This design is backward-compatible: old packages have no provenance files and no provenance artifacts in the index.

#### ImportedPackage Extension

```python
@dataclass(frozen=True)
class ImportedPackage:
    # ... existing fields ...
    integrity_verified: bool
    population_provenance: dict[str, Any] | None = None   # NEW
    calibration_provenance: dict[str, Any] | None = None   # NEW

    def __post_init__(self) -> None:
        # Existing deep copies
        object.__setattr__(self, "policy", copy.deepcopy(self.policy))
        object.__setattr__(self, "scenario_metadata", copy.deepcopy(self.scenario_metadata))
        # NEW: deep-copy provenance dicts when not None
        if self.population_provenance is not None:
            object.__setattr__(
                self, "population_provenance",
                copy.deepcopy(self.population_provenance),
            )
        if self.calibration_provenance is not None:
            object.__setattr__(
                self, "calibration_provenance",
                copy.deepcopy(self.calibration_provenance),
            )
```

#### PackageArtifactType Extension

The `PackageArtifactType` literal must include `"lineage"`:

```python
PackageArtifactType = Literal[
    "population", "scenario", "template", "manifest", "result", "lineage"
]
```

This type already has 6 values — `"lineage"` is already in the list. **No change needed.**

#### SimulationResult Convenience Method

```python
def export_replication_package(
    self,
    output_path: Path,
    *,
    compress: bool = False,
    population_provenance: dict[str, Any] | None = None,
    calibration_provenance: dict[str, Any] | None = None,
) -> ReplicationPackageMetadata:
    from reformlab.governance.replication import export_replication_package
    return export_replication_package(
        self, output_path,
        compress=compress,
        population_provenance=population_provenance,
        calibration_provenance=calibration_provenance,
    )
```

### Expected Provenance Data Formats

The replication module does NOT define or enforce the internal structure of provenance dicts — callers are responsible for preparing the content. However, the expected formats are documented here for reference:

#### Population Generation Provenance (prepared by caller using existing APIs)

```json
{
  "pipeline_description": "French household population 2024",
  "generation_seed": 42,
  "step_log": [
    {
      "step_index": 0,
      "step_type": "load",
      "label": "income",
      "input_labels": [],
      "output_rows": 1000,
      "output_columns": ["household_id", "income", "region"],
      "method_name": null,
      "duration_ms": 123.4
    },
    {
      "step_index": 1,
      "step_type": "load",
      "label": "vehicles",
      "input_labels": [],
      "output_rows": 800,
      "output_columns": ["vehicle_type", "vehicle_age"],
      "method_name": null,
      "duration_ms": 98.2
    },
    {
      "step_index": 2,
      "step_type": "merge",
      "label": "income_vehicles",
      "input_labels": ["income", "vehicles"],
      "output_rows": 1000,
      "output_columns": ["household_id", "income", "region", "vehicle_type", "vehicle_age"],
      "method_name": "conditional_sampling",
      "duration_ms": 45.1
    }
  ],
  "assumption_chain": [
    {
      "key": "merge_conditional_sampling",
      "value": {
        "method": "conditional_sampling",
        "statement": "Households matched within strata defined by income bracket...",
        "strata_columns": ["income_bracket"],
        "seed": 42,
        "pipeline_step_index": 2,
        "pipeline_step_label": "income_vehicles"
      },
      "source": "population_pipeline",
      "is_default": false
    }
  ],
  "source_configs": [
    {
      "provider": "insee",
      "dataset_id": "filosofi_2021_commune",
      "url": "https://www.insee.fr/...",
      "params": {},
      "description": "INSEE Filosofi 2021 commune-level data"
    },
    {
      "provider": "sdes",
      "dataset_id": "vehicle_fleet_2023",
      "url": "https://www.statistiques.developpement-durable.gouv.fr/...",
      "params": {},
      "description": "SDES vehicle fleet composition data"
    }
  ]
}
```

**How the caller prepares this:**
```python
from reformlab.population.pipeline import PipelineResult, PipelineStepLog
from dataclasses import asdict

def prepare_population_provenance(
    pipeline_result: PipelineResult,
    source_configs: list[SourceConfig],
    generation_seed: int,
) -> dict[str, Any]:
    return {
        "pipeline_description": pipeline_result.assumption_chain.pipeline_description,
        "generation_seed": generation_seed,
        "step_log": [asdict(step) for step in pipeline_result.step_log],
        "assumption_chain": pipeline_result.assumption_chain.to_governance_entries(),
        "source_configs": [
            {
                "provider": sc.provider,
                "dataset_id": sc.dataset_id,
                "url": sc.url,
                "params": dict(sc.params),
                "description": sc.description,
            }
            for sc in source_configs
        ],
    }
```

#### Calibration Provenance (prepared by caller using existing APIs)

```json
{
  "entries": [
    {
      "key": "calibration_result",
      "value": {
        "domain": "vehicle",
        "optimized_beta_cost": -0.012345,
        "objective_type": "mse",
        "final_objective_value": 0.00847,
        "convergence_flag": true,
        "iterations": 42,
        "gradient_norm": 1.23e-08,
        "method": "L-BFGS-B",
        "all_within_tolerance": true,
        "n_targets": 6
      },
      "source": "calibration_engine",
      "is_default": false
    },
    {
      "key": "calibration_targets",
      "value": {
        "domain": "vehicle",
        "period": "2020-2023",
        "n_targets": 6,
        "source_urls": ["https://..."]
      },
      "source": "calibration_engine",
      "is_default": false
    },
    {
      "key": "holdout_validation",
      "value": {
        "domain": "vehicle",
        "training_mse": 0.00847,
        "holdout_mse": 0.01234,
        "training_mae": 0.023,
        "holdout_mae": 0.045
      },
      "source": "calibration_engine",
      "is_default": false
    }
  ]
}
```

**How the caller prepares this:**
```python
from reformlab.calibration.provenance import capture_calibration_provenance

entries = capture_calibration_provenance(
    calibration_result,
    target_set=target_set,
    holdout_result=holdout_result,
)
calibration_provenance = {"entries": entries}
```

### Cross-Story Dependencies

| Story | Relationship |
|---|---|
| **16.1** | Direct producer: `export_replication_package()` is extended with new parameters. `PackageArtifact`, `PackageIndex`, `ReplicationPackageMetadata`, `ReplicationPackageError` are reused. |
| **16.2** | Direct producer: `import_replication_package()` is extended to load provenance files. `ImportedPackage` is extended with new fields. `reproduce_from_package()` is NOT modified (provenance is informational). |
| **11.6** | Source of population provenance: `PipelineResult.step_log`, `PipelineAssumptionChain.to_governance_entries()` — these produce the data the caller serializes into `population_provenance`. |
| **15.4** | Source of calibration provenance: `capture_calibration_provenance()` — produces the governance entries the caller serializes into `calibration_provenance`. |
| **16.4** | Future consumer: notebook demo will demonstrate export with provenance, import, and inspection of provenance data. |

### Important Scope Boundaries

**What this story does:**
- Adds optional provenance file writing to `export_replication_package()`
- Adds optional provenance file reading to `import_replication_package()`
- Extends `ImportedPackage` with optional provenance fields
- Updates `SimulationResult.export_replication_package()` convenience method

**What this story does NOT do:**
- **No automatic population provenance capture** — the replication module does NOT import from `reformlab.population` or `reformlab.calibration`. The caller prepares the provenance dict using existing APIs and passes it to the export function. This keeps adapter isolation clean.
- **No programmatic population regeneration** — AC-3 requires the provenance data to contain *enough information* for regeneration, but the actual regeneration step is the caller's responsibility (reconstruct the pipeline from the stored config and re-execute). The replication module stores and retrieves, it does not interpret provenance content.
- **No changes to `reproduce_from_package()`** — reproduction uses `population_path` and the adapter, not provenance data. Provenance is informational (for traceability and manual regeneration).
- **No changes to `PackageIndex` or `PackageArtifact` types** — the `"lineage"` value is already in the `PackageArtifactType` literal.
- **No changes to `RunManifest`** — population and calibration assumptions are already stored in `RunManifest.assumptions` via existing capture functions. The provenance files provide richer, structured detail alongside the manifest.
- **No new error classes** — reuse `ReplicationPackageError`.

### Data Flow Diagram

```
CALLER PREPARATION (outside replication module):

PipelineResult.step_log ─────────────┐
PipelineResult.assumption_chain ─────┤
SourceConfig objects ────────────────┤ → dict[str, Any]  → population_provenance
generation_seed ─────────────────────┘

capture_calibration_provenance() ────── → dict[str, Any]  → calibration_provenance

                                           │                    │
                                           ▼                    ▼
                                    export_replication_package(
                                        result, output_path,
                                        population_provenance=...,
                                        calibration_provenance=...,
                                    )
                                           │
                               ┌───────────┴───────────┐
                               │                       │
                    existing artifacts          provenance/
                    (data/, config/,        ┌────────────────────┐
                     manifests/)            │ population-        │
                               │            │   generation.json  │
                               │            │ calibration.json   │
                               │            └────────────────────┘
                               │                       │
                               └───────────┬───────────┘
                                           │
                                    package-index.json
                                    (includes provenance
                                     artifacts with hashes)
                                           │
                               import_replication_package()
                                           │
                                    ImportedPackage(
                                        ...,
                                        population_provenance=dict | None,
                                        calibration_provenance=dict | None,
                                    )
```

### Anti-Patterns from Previous Stories (DO NOT REPEAT)

| Issue | Prevention |
|---|---|
| Circular imports between governance and population/calibration | Do NOT import from `reformlab.population` or `reformlab.calibration` in `replication.py`. Provenance is `dict[str, Any]` — the caller prepares it. |
| Breaking backward compatibility on import | Provenance fields default to `None`. Old packages without `provenance/` directory load without error. |
| Missing `__post_init__` deep-copy for mutable fields | Deep-copy `population_provenance` and `calibration_provenance` dicts when not `None`. |
| Forgetting to hash new artifacts | Provenance files must be added to `artifacts_info` list BEFORE the hash-and-build loop. |
| Forgetting to update convenience method | `SimulationResult.export_replication_package()` must forward new kwargs. |
| Creating provenance dir when not needed | Only create `provenance/` when at least one provenance dict is not None. |
| Non-deterministic JSON output | Use `json.dumps(sort_keys=True, indent=2)` for all provenance files. |
| Path traversal in provenance file paths | Provenance paths are hardcoded (`provenance/population-generation.json`, `provenance/calibration.json`) — no user-controlled path components. |

### Testing Standards Summary

- Extend existing `tests/governance/test_replication.py` with new test classes
- Class-based grouping by feature (matching 16.1/16.2 pattern)
- Use `tmp_path` fixture for all file I/O
- Build test fixtures inline using existing `_make_result()`, `_make_manifest()`, `_make_panel_output()` helpers
- **Round-trip tests**: export with provenance → import → verify fields match
- Direct assertions with plain `assert`
- `pytest.raises(ReplicationPackageError, match="...")` for error cases
- Reference story/AC IDs in test docstrings

### Test Fixture Pattern for Provenance

```python
def _make_population_provenance() -> dict[str, Any]:
    """Build a minimal population provenance dict for tests."""
    return {
        "pipeline_description": "Test pipeline",
        "generation_seed": 42,
        "step_log": [
            {
                "step_index": 0,
                "step_type": "load",
                "label": "income",
                "input_labels": [],
                "output_rows": 100,
                "output_columns": ["household_id", "income"],
                "method_name": None,
                "duration_ms": 10.0,
            },
        ],
        "assumption_chain": [
            {
                "key": "merge_uniform",
                "value": {
                    "method": "uniform",
                    "statement": "Uniform random matching",
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
                "url": "https://www.insee.fr/example",
                "params": {},
                "description": "Test INSEE dataset",
            },
        ],
    }


def _make_calibration_provenance() -> dict[str, Any]:
    """Build a minimal calibration provenance dict for tests."""
    return {
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

### Project Structure Notes

**New files:** None

**Modified files:**
- `src/reformlab/governance/replication.py` — add `population_provenance` and `calibration_provenance` params to `export_replication_package()`, extend `ImportedPackage.__post_init__()`, extend `_load_package_from_dir()` to load provenance files
- `src/reformlab/interfaces/api.py` — add `population_provenance` and `calibration_provenance` params to `SimulationResult.export_replication_package()` convenience method
- `tests/governance/test_replication.py` — add new test classes for provenance export/import

### References

- [Source: docs/epics.md#Epic 16 — Story-Level AC for BKL-1603]
- [Source: src/reformlab/governance/replication.py — export_replication_package(), ImportedPackage, _load_package_from_dir(), PackageArtifact, PackageArtifactType (includes "lineage")]
- [Source: src/reformlab/interfaces/api.py — SimulationResult.export_replication_package() convenience method (line 209)]
- [Source: src/reformlab/population/pipeline.py — PipelineResult, PipelineStepLog, PopulationPipeline, PipelineAssumptionChain]
- [Source: src/reformlab/population/assumptions.py — PipelineAssumptionChain.to_governance_entries()]
- [Source: src/reformlab/population/loaders/base.py — SourceConfig (provider, dataset_id, url, params, description)]
- [Source: src/reformlab/population/methods/base.py — MergeConfig (seed, description, drop_right_columns), MergeAssumption (method_name, statement, details)]
- [Source: src/reformlab/calibration/provenance.py — capture_calibration_provenance(), make_calibration_reference(), extract_calibrated_parameters()]
- [Source: src/reformlab/calibration/types.py — CalibrationResult.to_governance_entry()]
- [Source: src/reformlab/governance/errors.py — ReplicationPackageError]
- [Source: src/reformlab/governance/hashing.py — hash_file()]
- [Source: docs/project-context.md — Frozen dataclasses, structured logging, error hierarchy conventions]
- [Source: _bmad-output/implementation-artifacts/16-2-implement-replication-package-import-and-reproduction.md — 16.2 story patterns, anti-patterns, test structure]

## Dev Agent Record

### Agent Model Used

<!-- filled by dev agent -->

### Debug Log References

### Completion Notes List

### File List

