

# Story 16.1: Implement Replication Package Export with Manifest Index

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **researcher**,
I want to export a self-contained replication package from a completed simulation run, including a manifest index listing all included artifacts with their roles and integrity hashes,
so that I can share the package with co-authors or reviewers who can verify completeness and integrity before attempting reproduction.

## Acceptance Criteria

1. **AC-1: Self-contained package directory** — Given a completed simulation run (`SimulationResult`), when the analyst exports a replication package, then a self-contained directory is created containing: population data (Parquet), scenario/portfolio configuration (YAML), template definitions used (YAML), run manifests (JSON) with all parameters and seeds, and simulation results (Parquet). The directory structure follows a documented layout with subdirectories for each artifact category.
2. **AC-2: Manifest index** — Given the exported package, when its manifest index file (`package-index.json`) is parsed, then it lists every artifact with: `role` (one of `"input"`, `"config"`, `"output"`, `"metadata"`), `artifact_type` (e.g., `"population"`, `"scenario"`, `"template"`, `"manifest"`, `"result"`), `path` (relative path within the package), and `hash` (SHA-256 hex digest for integrity verification).
3. **AC-3: Optional compression** — Given the export, when the `compress=True` option is used, then the package is a single `.zip` archive file that can be shared. When `compress=False` (default), the package is a plain directory.
4. **AC-4: Calibration reference inclusion** — Given a run that used calibrated parameters, when exported, then the package includes the calibrated beta coefficients and references the calibration run metadata within the manifest's assumptions.
5. **AC-5: Manifest index integrity** — Given the manifest index, when parsed, then every listed artifact's hash can be verified against the actual file, the index itself includes a top-level `package_id` (UUID), `created_at` (ISO 8601), `reformlab_version`, and `source_manifest_id` (the original run's manifest ID).

## Tasks / Subtasks

- [ ] Task 1: Create `replication` module with types (AC: 1, 2, 5)
  - [ ] 1.1: Create `src/reformlab/governance/replication.py` with module docstring referencing Story 16.1 / FR54
  - [ ] 1.2: Define `PackageArtifactRole` string literal type: `"input" | "config" | "output" | "metadata"`
  - [ ] 1.3: Define `PackageArtifactType` string literal type: `"population" | "scenario" | "template" | "manifest" | "result" | "lineage"`
  - [ ] 1.4: Define `PackageArtifact` frozen dataclass: `role: PackageArtifactRole`, `artifact_type: PackageArtifactType`, `path: str` (relative), `hash: str` (SHA-256), `description: str`
  - [ ] 1.5: Define `PackageIndex` frozen dataclass: `package_id: str` (UUID), `created_at: str` (ISO 8601), `reformlab_version: str`, `source_manifest_id: str`, `artifacts: tuple[PackageArtifact, ...]`; with `to_json() -> str` (canonical, sorted keys) and `from_json(cls, text) -> PackageIndex` methods
  - [ ] 1.6: Define `ReplicationPackageMetadata` frozen dataclass: `package_id: str`, `source_manifest_id: str`, `package_path: Path`, `artifact_count: int`, `compressed: bool`, `index: PackageIndex`

- [ ] Task 2: Implement `export_replication_package()` function (AC: 1, 2, 3, 4, 5)
  - [ ] 2.1: Implement `export_replication_package(result: SimulationResult, output_path: Path, *, compress: bool = False) -> ReplicationPackageMetadata` — main export function
  - [ ] 2.2: Create package directory structure: `{output_path}/{package_id}/` with subdirectories `data/`, `config/`, `results/`, `manifests/`
  - [ ] 2.3: Export population data — write `result.panel_output` to `data/panel-output.parquet` via `PanelOutput.to_parquet()`
  - [ ] 2.4: Export scenario/portfolio configuration — serialize `result.manifest.policy` to `config/policy.json` (canonical JSON)
  - [ ] 2.5: Export run manifest — write `result.manifest.to_json()` to `manifests/run-manifest.json`
  - [ ] 2.6: Export child manifests if present — for each year in `result.manifest.child_manifests`, write yearly manifest to `manifests/year-{year}.json` (only if yearly manifests are available in the result metadata)
  - [ ] 2.7: Export scenario configuration from manifest — write seeds, step pipeline, assumptions, mappings, and warnings to `config/scenario-metadata.json`
  - [ ] 2.8: Collect all artifact paths, compute SHA-256 hashes via `hash_file()` from `governance.hashing`
  - [ ] 2.9: Build `PackageIndex` with all artifacts, write to `{package_dir}/package-index.json`
  - [ ] 2.10: If `compress=True`, create ZIP archive of the package directory, remove the directory, return metadata pointing to the ZIP file
  - [ ] 2.11: Add structured logging: `event=replication_package_created package_id=... artifact_count=... compressed=...`

- [ ] Task 3: Add error handling (AC: all)
  - [ ] 3.1: Define `ReplicationPackageError(Exception)` in `src/reformlab/governance/errors.py`
  - [ ] 3.2: Validate that `result.success` is True before export (raise `ReplicationPackageError` if not)
  - [ ] 3.3: Validate that `result.panel_output` is not None (raise `ReplicationPackageError` if missing)
  - [ ] 3.4: Validate `output_path` parent directory exists (raise `ReplicationPackageError` if not)

- [ ] Task 4: Update public API (AC: all)
  - [ ] 4.1: Add `export_replication_package` to `src/reformlab/governance/__init__.py` exports
  - [ ] 4.2: Add convenience method `SimulationResult.export_replication_package(output_path, *, compress=False)` in `src/reformlab/interfaces/api.py` that delegates to the governance function
  - [ ] 4.3: Export new types (`PackageIndex`, `PackageArtifact`, `ReplicationPackageMetadata`, `ReplicationPackageError`) from `governance.__init__`

- [ ] Task 5: Write tests (AC: all)
  - [ ] 5.1: Create `tests/governance/test_replication.py` with test classes
  - [ ] 5.2: `TestPackageArtifact`: creation, frozen immutability, field validation
  - [ ] 5.3: `TestPackageIndex`: creation with artifacts, `to_json()` produces canonical JSON, `from_json()` round-trip is lossless, required fields validated
  - [ ] 5.4: `TestExportReplicationPackage`: successful export creates correct directory structure, all expected files exist, artifact hashes match file contents, manifest index lists all artifacts with correct roles and types
  - [ ] 5.5: `TestExportCompression`: `compress=True` produces `.zip` file, ZIP contains all expected files, ZIP entries match artifact index
  - [ ] 5.6: `TestExportCalibrationInclusion`: manifest with calibration assumptions includes calibration reference in exported package, calibrated beta values are present in the exported manifest
  - [ ] 5.7: `TestExportValidation`: failed result raises `ReplicationPackageError`, missing panel output raises `ReplicationPackageError`, invalid output path raises `ReplicationPackageError`
  - [ ] 5.8: `TestManifestIndexIntegrity`: package index has valid UUID, ISO timestamp, reformlab version, source manifest ID; every artifact hash in index matches actual file hash when verified
  - [ ] 5.9: `TestSimulationResultConvenience`: `SimulationResult.export_replication_package()` delegates correctly and returns metadata

- [ ] Task 6: Lint, type-check, regression (AC: all)
  - [ ] 6.1: `uv run ruff check src/reformlab/governance/ tests/governance/`
  - [ ] 6.2: `uv run mypy src/reformlab/governance/`
  - [ ] 6.3: `uv run pytest tests/` — all tests pass (existing + new)

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**Module location:** `src/reformlab/governance/replication.py` — new file in the existing governance module. Follows the pattern of `governance/reproducibility.py` (Story 5.5) and `calibration/provenance.py` (Story 15.4). No new subdirectories in `src/` needed.

**Updated module file layout after this story:**
```
src/reformlab/governance/
├── __init__.py                # Updated: add new exports
├── manifest.py                # No changes (RunManifest, to_json, from_json)
├── hashing.py                 # No changes (hash_file, hash_input_artifacts)
├── capture.py                 # No changes (assumption/mapping capture)
├── lineage.py                 # No changes (LineageGraph, validate_lineage)
├── reproducibility.py         # No changes (check_reproducibility)
├── errors.py                  # Updated: add ReplicationPackageError
├── memory.py                  # No changes
├── benchmarking.py            # No changes
└── replication.py             # NEW: export_replication_package + types
```

**Every file starts with** `from __future__ import annotations`.

**Frozen dataclasses for all types** — `PackageArtifact`, `PackageIndex`, `ReplicationPackageMetadata` are all `@dataclass(frozen=True)`.

**Structured logging** — `logging.getLogger(__name__)` with `key=value` format.

**No new external dependencies** — uses only Python stdlib (`zipfile`, `uuid`, `json`, `datetime`, `pathlib`) and existing governance utilities (`hash_file` from `hashing.py`).

### Key Imports

```python
from __future__ import annotations

import json
import logging
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from reformlab.governance.errors import ReplicationPackageError
from reformlab.governance.hashing import hash_file

if TYPE_CHECKING:
    from reformlab.governance.manifest import RunManifest
    from reformlab.interfaces.api import SimulationResult
```

Import `RunManifest` and `SimulationResult` at runtime inside functions that need them (not at module level) to avoid circular imports. The `governance` module should not import from `interfaces`.

### Package Directory Structure

The export function creates this layout:

```
{package_id}/
├── package-index.json          # Manifest index (role: metadata)
├── data/
│   └── panel-output.parquet    # Simulation results table (role: output)
├── config/
│   ├── policy.json             # Policy parameters snapshot (role: config)
│   └── scenario-metadata.json  # Seeds, step pipeline, assumptions (role: config)
└── manifests/
    └── run-manifest.json       # Full RunManifest (role: metadata)
```

If child manifests are available (multi-year lineage), yearly manifests are added:
```
manifests/
├── run-manifest.json
├── year-2025.json
├── year-2026.json
└── ...
```

### Algorithm: `export_replication_package()`

```
1. Validate inputs:
   - result.success is True
   - result.panel_output is not None
   - output_path.parent exists

2. Generate package_id (UUID4)

3. Create package directory: output_path / package_id /
   - Create subdirectories: data/, config/, manifests/

4. Export artifacts:
   a. panel-output.parquet ← result.panel_output.to_parquet()
   b. policy.json ← json.dumps(result.manifest.policy, sort_keys=True, indent=2)
   c. scenario-metadata.json ← json.dumps({
        "seeds": result.manifest.seeds,
        "step_pipeline": result.manifest.step_pipeline,
        "assumptions": result.manifest.assumptions,
        "mappings": result.manifest.mappings,
        "warnings": result.manifest.warnings,
        "engine_version": result.manifest.engine_version,
        "adapter_version": result.manifest.adapter_version,
        "scenario_version": result.manifest.scenario_version,
      }, sort_keys=True, indent=2)
   d. run-manifest.json ← result.manifest.to_json()

5. Hash all artifact files via hash_file()

6. Build PackageIndex:
   - package_id, created_at (UTC ISO 8601), reformlab_version (from engine_version), source_manifest_id
   - One PackageArtifact per file with role, artifact_type, relative path, hash, description

7. Write package-index.json (canonical JSON)

8. If compress:
   a. Create ZIP archive at output_path / {package_id}.zip
   b. Add all files from package directory to ZIP preserving relative paths
   c. Remove package directory (shutil.rmtree)
   d. Return metadata with package_path pointing to ZIP

9. Return ReplicationPackageMetadata
```

### Data Flow Diagram

```
SimulationResult
    │
    ├── .manifest (RunManifest)
    │       │
    │       ├── .policy ──────────► config/policy.json
    │       ├── .seeds, .step_pipeline, .assumptions,
    │       │   .mappings, .warnings ──► config/scenario-metadata.json
    │       ├── .to_json() ───────► manifests/run-manifest.json
    │       └── .child_manifests ─► manifests/year-{N}.json (if available)
    │
    └── .panel_output (PanelOutput)
            │
            └── .to_parquet() ───► data/panel-output.parquet
                                          │
                                          ▼
                              hash_file() per artifact
                                          │
                                          ▼
                              PackageIndex (package-index.json)
                                          │
                                    ┌─────┴─────┐
                                    │           │
                               Directory    ZIP archive
                             (compress=F)  (compress=T)
                                    │           │
                                    ▼           ▼
                          ReplicationPackageMetadata
```

### Manifest Index JSON Schema

```json
{
  "package_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-03-07T17:50:00+00:00",
  "reformlab_version": "0.1.0",
  "source_manifest_id": "a1b2c3d4-...",
  "artifacts": [
    {
      "role": "output",
      "artifact_type": "result",
      "path": "data/panel-output.parquet",
      "hash": "abc123...64hex",
      "description": "Panel output table (household x year)"
    },
    {
      "role": "config",
      "artifact_type": "scenario",
      "path": "config/policy.json",
      "hash": "def456...64hex",
      "description": "Policy parameters snapshot"
    },
    {
      "role": "config",
      "artifact_type": "scenario",
      "path": "config/scenario-metadata.json",
      "hash": "ghi789...64hex",
      "description": "Seeds, step pipeline, assumptions, mappings"
    },
    {
      "role": "metadata",
      "artifact_type": "manifest",
      "path": "manifests/run-manifest.json",
      "hash": "jkl012...64hex",
      "description": "Immutable run manifest with full provenance"
    }
  ]
}
```

### Cross-Story Dependencies

| Story | Relationship |
|---|---|
| **5.1** | Imports: `RunManifest` — the manifest included in every package |
| **5.4** | Uses: `hash_file()` from `governance.hashing` — for artifact integrity |
| **5.3** | Related: `LineageGraph` — child manifests included when available |
| **6.1** | Extends: `SimulationResult` — adds convenience `export_replication_package()` method |
| **3.7** | Uses: `PanelOutput.to_parquet()` — for result data export |
| **15.4** | Consumes: calibration provenance assumptions — included in manifest and scenario-metadata |
| **16.2** | Consumer: import/reproduction story reads the package this story creates |
| **16.3** | Consumer: adds population generation config and calibration provenance details to packages |
| **16.4** | Consumer: notebook demo uses `export_replication_package()` |

### Anti-Patterns from Previous Stories (DO NOT REPEAT)

| Issue | Prevention |
|---|---|
| Circular imports between modules | Import `SimulationResult` at runtime inside functions, not at module level |
| Non-deterministic JSON output | Use `json.dumps(sort_keys=True, separators=(",", ": "))` for canonical output |
| Forgetting `from __future__ import annotations` | First line of every new file |
| Mutable dataclasses | All types use `@dataclass(frozen=True)` |
| Missing input validation | Validate `result.success`, `result.panel_output`, and `output_path` before any I/O |
| Bare `Exception` or `ValueError` | Use subsystem-specific `ReplicationPackageError` |
| Missing structured logging | Log `event=replication_package_created` with key=value fields |
| Importing OpenFisca outside adapter | This story has zero OpenFisca interaction — maintain boundary |

### Implementation Notes

**ZIP compression:** Use Python stdlib `zipfile.ZipFile` with `ZIP_DEFLATED` compression. Walk the package directory and add files with `arcname` set to relative paths within the package.

**UUID generation:** Use `str(uuid.uuid4())` for `package_id`. This is not seed-controlled — package IDs are unique identifiers, not reproducibility-relevant.

**Timestamps:** Use `datetime.now(timezone.utc).isoformat()` for `created_at`.

**reformlab_version:** Extract from `result.manifest.engine_version` — this field already contains the reformlab version string.

**Child manifests:** Story 16.1 only exports child manifests if they are directly available in `result.metadata`. The manifest stores child manifest IDs but not the full child manifest objects. If yearly manifests are not available in the result, only the parent manifest is exported. Story 16.2 (import) will handle reconstruction.

**Scope boundary with Story 16.3:** This story (16.1) does NOT add population generation config or calibration target files to the package. It exports what's already in the `SimulationResult` — manifest (which includes calibration assumptions via Story 15.4), panel output, and policy config. Story 16.3 extends the package with population pipeline config and explicit calibration provenance files.

### Testing Standards Summary

- Mirror source structure: `tests/governance/test_replication.py`
- Class-based grouping by feature
- Use `tmp_path` fixture for all file I/O
- Build test `SimulationResult` fixtures inline in `conftest.py` or test file
- Use `MockAdapter` patterns — construct minimal `RunManifest` with required fields only
- Direct assertions with plain `assert`
- `pytest.raises(ReplicationPackageError, match="...")` for error cases
- Reference story/AC IDs in test docstrings

### Project Structure Notes

**New files:**
- `src/reformlab/governance/replication.py` — core module
- `tests/governance/test_replication.py` — tests

**Modified files:**
- `src/reformlab/governance/__init__.py` — add exports
- `src/reformlab/governance/errors.py` — add `ReplicationPackageError`
- `src/reformlab/interfaces/api.py` — add convenience method on `SimulationResult`

### References

- [Source: docs/epics.md#Epic 16 — Story-Level AC for BKL-1601]
- [Source: _bmad-output/planning-artifacts/architecture.md — Governance Layer, Reproducibility]
- [Source: src/reformlab/governance/manifest.py — RunManifest schema, to_json/from_json]
- [Source: src/reformlab/governance/hashing.py — hash_file, hash_input_artifacts]
- [Source: src/reformlab/governance/lineage.py — LineageGraph]
- [Source: src/reformlab/governance/reproducibility.py — ReproducibilityResult pattern]
- [Source: src/reformlab/interfaces/api.py — SimulationResult, export_manifest/csv/parquet methods]
- [Source: src/reformlab/orchestrator/panel.py — PanelOutput.to_parquet()]
- [Source: src/reformlab/calibration/provenance.py — calibration provenance capture pattern]
- [Source: docs/project-context.md — Frozen dataclasses, structured logging, error hierarchy conventions]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List

New files:
- `src/reformlab/governance/replication.py`
- `tests/governance/test_replication.py`

Modified files:
- `src/reformlab/governance/__init__.py`
- `src/reformlab/governance/errors.py`
- `src/reformlab/interfaces/api.py`
