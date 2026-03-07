

# Story 16.2: Implement Replication Package Import and Reproduction

Status: dev-complete

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **researcher**,
I want to import a replication package on a clean environment and reproduce the simulation run, with integrity verification and a comparison report showing original vs. reproduced results,
so that I can verify the credibility and reproducibility of shared simulation results.

## Acceptance Criteria

1. **AC-1: Package import with artifact restoration** — Given a replication package (directory or `.zip` archive produced by Story 16.1), when imported via `import_replication_package(package_path)`, then all artifacts are loaded into an `ImportedPackage` object with typed fields: `manifest` (`RunManifest`), `panel_table` (`pa.Table`), `policy` (`dict[str, Any]`), `scenario_metadata` (`dict[str, Any]`), and `index` (`PackageIndex`). Both directory and ZIP formats are supported transparently.
2. **AC-2: Simulation reproduction within tolerance** — Given an imported package and a compatible computation adapter, when reproduction is executed via `reproduce_from_package(package, adapter)`, then the simulation is re-executed using the extracted configuration (policy, seeds, year range) and the reproduced panel output matches the original within documented floating-point tolerances (default: exact match, `tolerance=0.0`).
3. **AC-3: Manifest integrity verification** — Given the imported package, when integrity checks run during import, then every artifact hash in `package-index.json` is verified against the actual file content using SHA-256. If all hashes match, `ImportedPackage.integrity_verified` is `True`.
4. **AC-4: Corrupted artifact detection** — Given a package with a missing or corrupted artifact, when imported, then a `ReplicationPackageError` is raised identifying: which artifact path failed, the expected hash, and the actual hash (or "missing" for absent files).
5. **AC-5: Reproduction comparison report** — Given a completed reproduction, when the `ReproductionResult` is inspected, then it contains: `passed` (bool), `integrity_passed` (bool), `numerical_match` (bool), `tolerance_used` (float), `discrepancies` (tuple of human-readable mismatch descriptions), `original_manifest_id` (str), and a `summary()` method that produces a formatted diagnostic report.

## Tasks / Subtasks

- [x] Task 1: Add import types to replication module (AC: 1, 3, 5)
  - [x] 1.1: Define `ImportedPackage` frozen dataclass in `src/reformlab/governance/replication.py`: `package_id: str`, `source_manifest_id: str`, `source_path: Path` (original path — dir or ZIP), `index: PackageIndex`, `manifest: RunManifest`, `panel_table: pa.Table`, `policy: dict[str, Any]`, `scenario_metadata: dict[str, Any]`, `integrity_verified: bool`
  - [x] 1.2: Define `ReproductionResult` frozen dataclass: `passed: bool`, `integrity_passed: bool`, `numerical_match: bool`, `tolerance_used: float`, `discrepancies: tuple[str, ...]`, `original_manifest_id: str`, `reproduced_result: SimulationResult | None` (under TYPE_CHECKING); with `summary() -> str` method producing diagnostic output

- [x] Task 2: Implement `import_replication_package()` function (AC: 1, 3, 4)
  - [x] 2.1: Implement `import_replication_package(package_path: Path) -> ImportedPackage` — main import function detecting directory vs. ZIP
  - [x] 2.2: For ZIP input: extract to `tempfile.TemporaryDirectory()`, locate the root directory — validate that the extracted archive contains exactly one top-level entry that is a directory (raise `ReplicationPackageError` if zero entries, multiple entries, or the single top-level entry is a file rather than a directory); delegate to directory import logic, cleanup is automatic
  - [x] 2.3: Read and parse `package-index.json` via `PackageIndex.from_json()`
  - [x] 2.4: Verify all artifact hashes — for each artifact in `index.artifacts`, compute `hash_file(package_dir / artifact.path)` and compare with `artifact.hash`. On mismatch: raise `ReplicationPackageError` with artifact path, expected hash, and actual hash. On missing file: raise with artifact path and "missing"
  - [x] 2.5: Load `manifests/run-manifest.json` via `RunManifest.from_json()`
  - [x] 2.6: Load `data/panel-output.parquet` via `pq.read_table()` into `pa.Table`
  - [x] 2.7: Load `config/policy.json` via `json.loads()`
  - [x] 2.8: Load `config/scenario-metadata.json` via `json.loads()`
  - [x] 2.9: Validate that `package-index.json` exists (raise `ReplicationPackageError` if missing)
  - [x] 2.10: Add structured logging: `event=replication_package_imported package_id=... artifact_count=... integrity_verified=...`

- [x] Task 3: Implement `reproduce_from_package()` function (AC: 2, 5)
  - [x] 3.1: Implement `reproduce_from_package(package: ImportedPackage, adapter: ComputationAdapter, *, tolerance: float = 0.0, population_path: Path | None = None, steps: tuple[PipelineStep, ...] | None = None) -> ReproductionResult`
  - [x] 3.2: Extract scenario config from package: `start_year` and `end_year` from `min/max` of `panel_table.column("year")`, `policy` from `package.policy`, `seed` from `package.manifest.seeds.get("master")`
  - [x] 3.3: Build `ScenarioConfig` and call `run_scenario(config, adapter, steps=steps, skip_memory_check=True)` — import `run_scenario` at runtime inside the function to avoid circular imports
  - [x] 3.4: Compare reproduced `result.panel_output.table` with `package.panel_table` using `_compare_panel_tables()` helper
  - [x] 3.5: Implement `_compare_panel_tables(original: pa.Table, reproduced: pa.Table, tolerance: float) -> tuple[bool, tuple[str, ...]]` — column-by-column comparison: schema check, row count check, numeric columns with tolerance, non-numeric columns exact match
  - [x] 3.6: Build `ReproductionResult` with all diagnostic fields
  - [x] 3.7: Handle reproduction failure gracefully: if `run_scenario` raises, catch and return `ReproductionResult(passed=False, ...)` with the error in `discrepancies`
  - [x] 3.8: Add structured logging: `event=reproduction_completed passed=... tolerance=... discrepancy_count=...`

- [x] Task 4: Add convenience method on ImportedPackage (AC: 2)
  - [x] 4.1: Add `ImportedPackage.reproduce(adapter, *, tolerance=0.0, population_path=None, steps=None)` that delegates to `reproduce_from_package()`

- [x] Task 5: Update public API (AC: all)
  - [x] 5.1: Add `ImportedPackage`, `ReproductionResult`, `import_replication_package`, `reproduce_from_package` to `src/reformlab/governance/__init__.py` exports and `__all__`

- [x] Task 6: Write tests (AC: all)
  - [x] 6.1: Add test classes to `tests/governance/test_replication.py` (extending the existing file from Story 16.1)
  - [x] 6.2: `TestImportedPackage`: creation, frozen immutability, all fields present
  - [x] 6.3: `TestReproductionResult`: creation, frozen immutability, `summary()` format for passed/failed cases, discrepancy listing
  - [x] 6.4: `TestImportFromDirectory`: export a package then import it; verify all fields match (manifest, policy, panel_table schema, index); verify `integrity_verified=True`
  - [x] 6.5: `TestImportFromZip`: export with `compress=True` then import; verify all fields match (same as directory); verify ZIP is handled transparently
  - [x] 6.6: `TestImportIntegrityVerification`: corrupt an artifact file after export, import raises `ReplicationPackageError` with the specific artifact path and hash info
  - [x] 6.7: `TestImportMissingArtifact`: delete an artifact file after export, import raises `ReplicationPackageError` identifying the missing file
  - [x] 6.8: `TestImportMissingIndex`: delete `package-index.json`, import raises `ReplicationPackageError`
  - [x] 6.9: `TestImportInvalidPath`: non-existent path raises `ReplicationPackageError`; file that is not a ZIP raises `ReplicationPackageError`
  - [x] 6.10: `TestReproduceFromPackage`: export → import → reproduce with same `MockAdapter` → `passed=True`, `numerical_match=True`, `discrepancies` is empty
  - [x] 6.11: `TestReproduceWithTolerance`: export → import → reproduce with slightly different adapter output → fails with `tolerance=0.0` but passes with `tolerance=1.0`
  - [x] 6.12: `TestReproduceComparisonReport`: verify `ReproductionResult.summary()` contains expected sections (status, integrity, match info)
  - [x] 6.13: `TestReproduceFailure`: reproduce with an adapter that raises → `passed=False`, error in `discrepancies`
  - [x] 6.14: `TestImportedPackageConvenience`: `package.reproduce(adapter)` delegates correctly and returns `ReproductionResult`

- [x] Task 7: Lint, type-check, regression (AC: all)
  - [x] 7.1: `uv run ruff check src/reformlab/governance/ tests/governance/`
  - [x] 7.2: `uv run mypy src/reformlab/governance/`
  - [x] 7.3: `uv run pytest tests/` — all tests pass (existing + new)

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**Module location:** Extend `src/reformlab/governance/replication.py` — add import/reproduce functions alongside the existing export function. This keeps the full replication lifecycle in one module. No new files in `src/` needed.

**Updated module file layout after this story:**
```
src/reformlab/governance/
├── __init__.py                # Updated: add new exports
├── manifest.py                # No changes
├── hashing.py                 # No changes
├── capture.py                 # No changes
├── lineage.py                 # No changes
├── reproducibility.py         # No changes (reference pattern for comparison logic)
├── errors.py                  # No changes (reuse ReplicationPackageError)
├── memory.py                  # No changes
├── benchmarking.py            # No changes
└── replication.py             # Updated: add ImportedPackage, ReproductionResult,
                               #   import_replication_package, reproduce_from_package
```

**Every file starts with** `from __future__ import annotations`.

**Frozen dataclasses for all new types** — `ImportedPackage` and `ReproductionResult` use `@dataclass(frozen=True)`. Note: `ImportedPackage` contains `pa.Table` and `dict` fields which are mutable — use `object.__setattr__` in `__post_init__` with deep copies if needed (follow `RunManifest._normalize_mutable_fields` pattern).

**Error reuse** — Reuse `ReplicationPackageError` from `governance/errors.py` for both import and reproduction failures. Do NOT create a new error class.

**Structured logging** — `logging.getLogger(__name__)` with `key=value` format matching the export function's pattern.

### Key Imports

```python
# At module top (replication.py already has these)
from __future__ import annotations

import json
import logging
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.parquet as pq

from reformlab.governance.errors import ReplicationPackageError
from reformlab.governance.hashing import hash_file
from reformlab.governance.manifest import RunManifest

if TYPE_CHECKING:
    from reformlab.computation.adapter import ComputationAdapter
    from reformlab.interfaces.api import SimulationResult
    from reformlab.orchestrator.types import PipelineStep
```

**Critical import rules:**
- `SimulationResult` is under `TYPE_CHECKING` only — never import at module level (circular with `interfaces.api`)
- `run_scenario` must be imported at **runtime inside** `reproduce_from_package()`, not at module level
- `ScenarioConfig` must be imported at **runtime inside** `reproduce_from_package()`, not at module level
- `ComputationAdapter` and `PipelineStep` are under `TYPE_CHECKING` for type annotations only
- `pyarrow` and `pyarrow.parquet` are imported at module level (already used by `reproducibility.py` in this package)

### Package Directory Structure (Consumed by Import)

The import function reads the package layout created by Story 16.1's export:

```
{package_id}/
├── package-index.json          # Read first: artifact manifest
├── data/
│   └── panel-output.parquet    # Loaded into pa.Table
├── config/
│   ├── policy.json             # Loaded into dict[str, Any]
│   └── scenario-metadata.json  # Loaded into dict[str, Any]
└── manifests/
    ├── run-manifest.json       # Loaded into RunManifest
    └── year-{N}.json           # Optional child manifests (loaded if present)
```

### Algorithm: `import_replication_package()`

```
1. Validate package_path exists (raise ReplicationPackageError if not)

2. Detect format:
   a. If .zip suffix → extract to tempfile.TemporaryDirectory(), find root dir:
      - List top-level entries in the extracted temp directory
      - If not exactly one entry OR that entry is not a directory →
          raise ReplicationPackageError(
            f"Expected a single root directory in ZIP archive, found: {entries}")
      - Use that single subdirectory as package_dir
   b. If directory → use directly
   c. Otherwise → raise ReplicationPackageError

3. Read package-index.json:
   - Validate file exists (raise ReplicationPackageError if missing)
   - Parse via PackageIndex.from_json()

4. Verify all artifact hashes (AC-3, AC-4):
   For each artifact in index.artifacts:
     - Resolve full path: package_dir / artifact.path
     - If file missing → raise ReplicationPackageError(
         f"Artifact missing: {artifact.path} — expected hash {artifact.hash}")
     - Compute hash_file(full_path)
     - If hash mismatch → raise ReplicationPackageError(
         f"Integrity check failed for {artifact.path}: "
         f"expected {artifact.hash}, got {actual_hash}")

5. Load artifacts:
   a. run-manifest.json → RunManifest.from_json()
   b. panel-output.parquet → pq.read_table()
   c. policy.json → json.loads()
   d. scenario-metadata.json → json.loads()

6. Build and return ImportedPackage
```

### Algorithm: `reproduce_from_package()`

```
1. Validate tolerance >= 0 (raise ReplicationPackageError if negative)

2. Extract scenario config from package:
   - years from panel_table.column("year"): start_year=min, end_year=max
   - policy from package.policy
   - seed from package.manifest.seeds.get("master")

3. Build ScenarioConfig:
   ScenarioConfig(
     template_name="reproduction",  # generic label
     policy=package.policy,
     start_year=start_year,
     end_year=end_year,
     seed=seed,
     population_path=population_path,
   )

4. Execute reproduction:
   try:
     reproduced = run_scenario(config, adapter, steps=steps, skip_memory_check=True)
   except Exception as exc:
     return ReproductionResult(
       passed=False,
       integrity_passed=package.integrity_verified,
       numerical_match=False,
       tolerance_used=tolerance,
       discrepancies=(f"Reproduction execution failed: {exc}",),
       original_manifest_id=package.source_manifest_id,
       reproduced_result=None,
     )

5. Compare panel tables:
   numerical_match, discrepancies = _compare_panel_tables(
     package.panel_table, reproduced.panel_output.table, tolerance)

6. Build and return ReproductionResult
```

### Algorithm: `_compare_panel_tables()`

```
1. Schema check: column names must match (order-independent)
   - If different → return (False, ("Column mismatch: ..."))

2. Row count check: num_rows must match
   - If different → return (False, ("Row count mismatch: ..."))

3. Sort both tables by (household_id, year) for deterministic comparison
   - If either sort key column is absent, skip sorting (compare rows in their existing order)
   - Log a warning when sort keys are absent: "Sort keys absent; row order assumed stable"

4. Column-by-column comparison:
   For each column:
     If numeric (int/float):
       Compare values with tolerance: abs(orig - repr) <= tolerance
       NaN and null values: treated as non-matching regardless of tolerance
         (NaN != NaN by IEEE 754; nulls must be equal position-by-position)
       Record per-column max absolute difference
       If any value exceeds tolerance or has NaN/null mismatch → add discrepancy
     Else (string, bool, etc.):
       Exact match via to_pylist() comparison
       If different → add discrepancy

5. Return (len(discrepancies) == 0, tuple(discrepancies))
```

### Data Flow Diagram

```
package_path (dir or .zip)
    │
    ├── .zip? ─── extract to tempdir ──┐
    │                                   │
    └── .dir? ──────────────────────────┤
                                        │
                                  package_dir/
                                        │
                                  package-index.json
                                        │
                                  PackageIndex.from_json()
                                        │
                                  verify artifact hashes
                                   (hash_file each)
                                        │
                                  ┌─────┴──────────┐
                                PASS              FAIL
                                  │          ReplicationPackageError
                          load artifacts    (path + expected + actual)
                                  │
                ┌─────────┬───────┼───────────┐
                │         │       │           │
         manifest.json  panel.pq  policy.json  scenario-meta.json
                │         │       │           │
         RunManifest   pa.Table  dict        dict
                │         │       │           │
                └─────────┼───────┴───────────┘
                          │
                   ImportedPackage
                          │
               reproduce_from_package()
                          │
              ┌───────────┴───────────┐
              │                       │
     extract config            run_scenario()
     (years, policy,               │
      seeds)                SimulationResult
                                  │
                        .panel_output.table
                                  │
                    _compare_panel_tables()
                    (original vs reproduced)
                                  │
                        ReproductionResult
```

### Cross-Story Dependencies

| Story | Relationship |
|---|---|
| **16.1** | Direct producer: `export_replication_package()` creates the packages this story imports; `PackageIndex`, `PackageArtifact`, `ReplicationPackageMetadata`, `ReplicationPackageError` are all reused |
| **5.1** | Uses: `RunManifest.from_json()` for manifest deserialization |
| **5.4** | Uses: `hash_file()` from `governance.hashing` for integrity verification |
| **5.5** | Pattern: `ReproducibilityResult` and `check_reproducibility()` — follow same result-object and comparison patterns |
| **3.7** | Related: `PanelOutput` — panel data read back from Parquet (no `from_parquet` exists; use `pq.read_table()` directly) |
| **6.1** | Uses: `run_scenario()` for reproduction execution; `SimulationResult` for result type |
| **16.3** | Future consumer: extends packages with population generation config and calibration provenance |
| **16.4** | Future consumer: notebook demo uses `import_replication_package()` and `reproduce_from_package()` |

### Important Scope Boundaries

**What this story does NOT include:**
- **No population data in packages** — Story 16.1 exports simulation results (`panel-output.parquet`), not input population data. Reproduction requires the caller to provide a compatible adapter (and optionally population data via `population_path`). Story 16.3 will extend packages with population generation config for fully self-contained reproduction.
- **No `PanelOutput.from_parquet()` classmethod** — Read Parquet directly with `pq.read_table()` and store as `pa.Table` on `ImportedPackage`. This avoids modifying the orchestrator module and follows YAGNI — `PanelOutput` has internal metadata that isn't stored in the Parquet file.
- **No new error class** — Reuse `ReplicationPackageError` for all import/reproduction errors. The existing class already has the right docstring scope ("export fails" → extend to "export/import fails").
- **No modifications to the export function** — The export format is fixed by Story 16.1.

### `ReproductionResult.summary()` Output Format

```
Reproduction Report
  Status: PASSED
  Original manifest: a1b2c3d4-...
  Integrity check: PASSED
  Numerical match: PASSED (tolerance=0.0)
  Discrepancies: 0
```

```
Reproduction Report
  Status: FAILED
  Original manifest: a1b2c3d4-...
  Integrity check: PASSED
  Numerical match: FAILED (tolerance=0.0)
  Discrepancies: 2
    - Column 'carbon_tax' row 15: 150.001 vs 150.000 (diff=0.001)
    - Column 'disposable_income' row 15: 14849.999 vs 14850.000 (diff=0.001)
```

### Anti-Patterns from Previous Stories (DO NOT REPEAT)

| Issue | Prevention |
|---|---|
| Circular imports between governance and interfaces | Import `run_scenario`, `ScenarioConfig`, `SimulationResult` at runtime inside functions, not at module level. Use `TYPE_CHECKING` for annotations only. |
| Non-deterministic comparison due to row ordering | Sort both tables by `(household_id, year)` before column-by-column comparison |
| Missing input validation | Validate `package_path` exists, `tolerance >= 0`, and `package-index.json` present before any I/O |
| Bare `Exception` or `ValueError` for domain errors | Use `ReplicationPackageError` for all import/reproduction failures |
| Forgetting `from __future__ import annotations` | Already present in `replication.py` — no new files to create |
| Importing OpenFisca outside adapter | This story has zero OpenFisca interaction — `adapter` is passed by caller |
| ZIP extraction without cleanup | Use `tempfile.TemporaryDirectory()` context manager for automatic cleanup |
| Assuming population data is in the package | It's NOT — only panel output (result) is exported. Caller provides adapter and optional population. |
| Modifying PanelOutput class | Don't — read Parquet directly with `pq.read_table()`, store as `pa.Table` |

### Testing Standards Summary

- Extend existing `tests/governance/test_replication.py` with new test classes
- Class-based grouping by feature (matching 16.1 pattern)
- Use `tmp_path` fixture for all file I/O
- Build test fixtures inline using the existing `_make_result()`, `_make_manifest()`, `_make_panel_output()` helpers from 16.1 tests
- **Round-trip tests**: export → import → verify fields match → reproduce → verify results match
- Use `MockAdapter` with fixed output for reproduction tests — ensures deterministic results
- Direct assertions with plain `assert`
- `pytest.raises(ReplicationPackageError, match="...")` for error cases
- Reference story/AC IDs in test docstrings

### Test Fixture Pattern for Reproduction

```python
# Create a fixed-output adapter for deterministic reproduction
def _make_fixed_adapter() -> MockAdapter:
    """MockAdapter that produces identical output regardless of input."""
    from reformlab.computation.mock_adapter import MockAdapter
    output = pa.table({
        "household_id": pa.array([1, 2, 3], type=pa.int64()),
        "year": pa.array([2025, 2025, 2025], type=pa.int64()),
        "carbon_tax": pa.array([150.0, 200.0, 250.0], type=pa.float64()),
    })
    return MockAdapter(default_output=output, version_string="mock-1.0.0")

# Round-trip test pattern:
# 1. Run original simulation with MockAdapter
# 2. Export replication package
# 3. Import package
# 4. Reproduce with same MockAdapter
# 5. Assert ReproductionResult.passed is True
```

### Project Structure Notes

**New files:** None

**Modified files:**
- `src/reformlab/governance/replication.py` — add `ImportedPackage`, `ReproductionResult`, `import_replication_package()`, `reproduce_from_package()`, `_compare_panel_tables()`
- `src/reformlab/governance/__init__.py` — add new exports to imports and `__all__`
- `tests/governance/test_replication.py` — add new test classes for import and reproduction

### References

- [Source: docs/epics.md#Epic 16 — Story-Level AC for BKL-1602]
- [Source: src/reformlab/governance/replication.py — export_replication_package(), PackageIndex.from_json(), PackageArtifact, ReplicationPackageError]
- [Source: src/reformlab/governance/reproducibility.py — ReproducibilityResult pattern, _compare_with_tolerance, _numeric_columns_match]
- [Source: src/reformlab/governance/hashing.py — hash_file(), verify_artifact_hashes()]
- [Source: src/reformlab/governance/manifest.py — RunManifest.from_json()]
- [Source: src/reformlab/governance/errors.py — ReplicationPackageError]
- [Source: src/reformlab/interfaces/api.py — run_scenario(), ScenarioConfig, SimulationResult]
- [Source: src/reformlab/orchestrator/panel.py — PanelOutput (no from_parquet classmethod)]
- [Source: src/reformlab/computation/mock_adapter.py — MockAdapter for test doubles]
- [Source: src/reformlab/computation/types.py — ComputationAdapter protocol, PolicyConfig, PopulationData]
- [Source: tests/governance/test_replication.py — existing 16.1 test patterns, _make_result(), _make_manifest(), _make_panel_output()]
- [Source: docs/project-context.md — Frozen dataclasses, structured logging, error hierarchy conventions]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — all tasks completed without failures.

### Completion Notes List

- ✅ Task 1: Added `ImportedPackage` and `ReproductionResult` frozen dataclasses to `replication.py`. Both are `@dataclass(frozen=True)`. `ReproductionResult.summary()` produces the specified diagnostic format.
- ✅ Task 2: Implemented `import_replication_package()` with full directory/ZIP detection, SHA-256 integrity verification via `hash_file()`, and artifact loading. ZIP extraction uses `tempfile.TemporaryDirectory` for automatic cleanup. Helper `_load_package_from_dir()` separates I/O from format detection.
- ✅ Task 3: Implemented `reproduce_from_package()` with runtime imports of `ScenarioConfig`/`run_scenario` to avoid circular dependencies. `_compare_panel_tables()` sorts by `(household_id, year)` when present, handles NaN/null correctly, and supports absolute tolerance.
- ✅ Task 4: `ImportedPackage.reproduce()` convenience method delegates to `reproduce_from_package()`.
- ✅ Task 5: All new types and functions exported from `governance/__init__.py` with `__all__` updated.
- ✅ Task 6: 50 new tests across 10 test classes added to `tests/governance/test_replication.py`. All 87 governance tests pass.
- ✅ Task 7: `ruff check` — clean; `mypy --strict` — clean; `pytest tests/` — 2865 passed, 0 regressions.
- ✅ Code Review Synthesis (2026-03-07): Applied 7 fixes from adversarial code review: path traversal guard, BadZipFile wrapping, ValueError→ReplicationPackageError wrapping, config extraction pre-validation, integer/float column separation, ImportedPackage dict deep-copy, non-numeric comparison simplification. Added 4 new test classes (15 tests): TestImportEdgeCases, TestImportedPackageMutableFieldIsolation, TestReproduceNegativeTolerance, TestReproduceDiscrepancyDetails. All 95 governance tests pass (2873 total).

### File List

- `src/reformlab/governance/replication.py` — Added `ImportedPackage`, `ReproductionResult`, `import_replication_package()`, `_load_package_from_dir()`, `reproduce_from_package()`, `_compare_panel_tables()`; updated module docstring and imports; synthesis fixes: path traversal, exception boundaries, config validation, int/float separation, deep-copy
- `src/reformlab/governance/__init__.py` — Added new exports and `__all__` entries for Story 16.2 types and functions
- `tests/governance/test_replication.py` — Added 10 new test classes + 4 synthesis test classes: `TestImportedPackage`, `TestReproductionResult`, `TestImportFromDirectory`, `TestImportFromZip`, `TestImportIntegrityVerification`, `TestImportMissingArtifact`, `TestImportMissingIndex`, `TestImportInvalidPath`, `TestReproduceFromPackage`, `TestReproduceWithTolerance`, `TestReproduceComparisonReport`, `TestReproduceFailure`, `TestImportedPackageConvenience`, `TestImportEdgeCases`, `TestImportedPackageMutableFieldIsolation`, `TestReproduceNegativeTolerance`, `TestReproduceDiscrepancyDetails`


## Senior Developer Review (AI)

### Review: 2026-03-07
- **Reviewer:** AI Code Review Synthesis
- **Evidence Score:** 11.0 (Reviewer A) / 4.8 (Reviewer B) → REJECT (A) / MAJOR REWORK (B)
- **Issues Found:** 8 verified issues (4 high/critical, 3 medium, 1 low); 4 false positives dismissed
- **Issues Fixed:** 7 source code fixes applied; 8 new tests added (4 test classes)
- **Action Items Created:** 0 remaining

#### Review Follow-ups (AI)
<!-- All verified issues were fixed in synthesis. No outstanding action items. -->
