# Story 5.5: Add Reproducibility Check Harness

Status: done

## Story

As a **policy analyst or researcher**,
I want **a reproducibility check harness that can re-execute a simulation run using the same inputs and seeds from its manifest and verify outputs are bit-identical**,
so that **I can trust that my simulation results are deterministic and can be reproduced on the same or different machines**.

## Acceptance Criteria

From backlog (BKL-505), aligned with NFR6 (bit-identical on same machine) and NFR7 (identical across machines with same versions).

1. **AC-1: Reproducibility check harness executes rerun from manifest**
   - Given a completed run and its `RunManifest`, when `check_reproducibility(manifest, ..., rerun_callable=...)` is called, then it re-executes the simulation with the same inputs and seeds.
   - The harness extracts from manifest: `seeds`, `parameters`, `scenario_version`, `step_pipeline`, start/end years from `child_manifests` keys.
   - Input data files are located via `data_hashes` keys and provided `input_paths`.
   - The governance harness does not instantiate `OrchestratorRunner` directly; rerun execution is delegated through the injected callable to preserve subsystem boundaries.
   - The harness must NOT modify any existing files or manifests.

2. **AC-2: Output hash comparison detects bit-identical results**
   - Given a rerun with identical inputs/seeds, when outputs are produced, then output hashes are compared against `output_hashes` in the original manifest.
   - Returns `ReproducibilityResult` with `passed: bool`, `hash_mismatches: list[str]`, `missing_artifacts: list[str]`.
   - Comparison uses `verify_artifact_hashes()` from Story 5-4.

3. **AC-3: Cross-machine reproducibility within documented tolerances**
   - Given a run on a different machine (same Python and dependency versions), when re-executed, then outputs match within documented tolerances.
   - For floating-point differences, provide optional `tolerance: float` parameter for soft comparison plus `reference_output_paths` for baseline artifact files.
   - Default behavior is strict bit-identical comparison (tolerance=0).
   - When `tolerance > 0`, soft comparison runs only for artifacts that fail strict hash checks.
   - If `tolerance > 0` and `reference_output_paths` is missing/incomplete, return explicit reproducibility diagnostics (no silent pass/fallback).
   - Document tolerance usage in function docstrings.

4. **AC-4: Clear diagnostics on reproducibility failure**
   - When reproducibility check fails, the result includes:
     - Which artifact keys had hash mismatches
     - Which artifact keys were missing
     - Seed values used in rerun vs original
     - Year range executed
   - Diagnostics enable developer to investigate root cause.

5. **AC-5: Harness integrates with existing governance module**
   - `check_reproducibility()` is exported from `governance/__init__.py`
   - `ReproducibilityResult` dataclass is exported
   - Uses existing `RunManifest`, `verify_artifact_hashes()`, `ArtifactVerificationResult`
   - Does not duplicate any existing hashing or manifest logic

6. **AC-6: Benchmark fixture demonstrates reproducibility**
   - At least one test demonstrates a complete reproducibility cycle:
     - Run orchestrator with fixed seed
     - Capture manifest with input/output hashes
     - Re-execute via harness
     - Verify bit-identical outputs
   - Test passes in CI for benchmark fixtures.

## Dependencies

- **Hard dependencies (from backlog BKL-505):**
  - Story 5-3 (BKL-503): Run lineage graph for manifest structure (child_manifests keys for year range)
  - Story 5-4 (BKL-504): Hash input/output artifacts for comparison
  - Story 3-6 (BKL-306): Seed controls logged in manifests
- **Integration dependencies:**
  - Story 5-1 (BKL-501): `RunManifest` schema with seeds, parameters, data_hashes, output_hashes
  - Story 5-2 (BKL-502): Manifest capture with assumptions/mappings/parameters
  - Story 3-1 (BKL-301): Yearly loop orchestrator execution contract
  - Story 3-7 (BKL-307): Yearly panel output artifacts used as reproducibility surfaces
- **All dependencies are DONE per sprint-status.yaml (checked 2026-02-27)**

- **Follow-on stories:**
  - Story 5-6 (BKL-506): Warning system for unvalidated templates (P1)
  - EPIC-6 stories for Python API exposure of reproducibility features

## Tasks / Subtasks

- [ ] Task 0: Review prerequisite contracts and boundaries (AC: dependency check)
  - [ ] 0.1 Verify `RunManifest` fields: `seeds`, `parameters`, `data_hashes`, `output_hashes`, `child_manifests`, `step_pipeline`
  - [ ] 0.2 Review `verify_artifact_hashes()` contract from `governance/hashing.py`
  - [ ] 0.3 Review orchestrator-facing rerun interface used by callers (`OrchestratorRunner.run()` request contract)
  - [ ] 0.4 Confirm seed derivation logic in `orchestrator/runner.py` (`_derive_year_seed`)
  - [ ] 0.5 Verify dependency statuses in `sprint-status.yaml` for 5-1, 5-2, 5-3, 5-4, 3-1, 3-6, 3-7

- [ ] Task 1: Create ReproducibilityResult dataclass (AC: #2, #4)
  - [ ] 1.1 Create `src/reformlab/governance/reproducibility.py`
  - [ ] 1.2 Define `ReproducibilityResult` frozen dataclass with fields:
        - `passed: bool`
        - `hash_mismatches: list[str]`
        - `missing_artifacts: list[str]`
        - `rerun_seeds: dict[str, int]`
        - `original_seeds: dict[str, int]`
        - `year_range: tuple[int, int]`
        - `tolerance_used: float`
  - [ ] 1.3 Add `details() -> str` method for human-readable diagnostics

- [ ] Task 2: Implement check_reproducibility function (AC: #1, #2, #3)
  - [ ] 2.1 Signature: `check_reproducibility(manifest: RunManifest, input_paths: dict[str, Path], output_paths: dict[str, Path], rerun_callable: Callable[..., Any], tolerance: float = 0.0, reference_output_paths: dict[str, Path] | None = None) -> ReproducibilityResult`
  - [ ] 2.2 Extract rerun parameters from manifest:
        - Master seed from `manifest.seeds["master"]`
        - Year range from `manifest.child_manifests.keys()` (min/max)
        - Parameters from `manifest.parameters`
        - Step pipeline from `manifest.step_pipeline`
  - [ ] 2.3 Execute rerun via `rerun_callable` only (no direct `OrchestratorRunner` construction inside governance)
  - [ ] 2.4 Validate provided artifact maps before verification (required keys from `manifest.output_hashes`)
  - [ ] 2.5 Compare hashes using `verify_artifact_hashes()` (AC-2)
  - [ ] 2.6 Return `ReproducibilityResult` with comparison outcome

- [ ] Task 3: Implement tolerance-based soft comparison (AC: #3)
  - [ ] 3.1 Validate tolerance contract (`tolerance >= 0`) and require `reference_output_paths` when `tolerance > 0`
  - [ ] 3.2 For artifacts with strict hash mismatches, compare rerun outputs against reference outputs:
        - For Parquet files, use PyArrow tables and compare numeric columns within tolerance
        - For CSV files, use PyArrow CSV reader and compare numeric columns within tolerance
        - Non-numeric columns require exact match
  - [ ] 3.3 Apply tolerance only to strict hash mismatches and keep mismatch reporting explicit in `details()` output
  - [ ] 3.4 Document tolerance semantics and limitations in docstrings

- [ ] Task 4: Export public APIs (AC: #5)
  - [ ] 4.1 Export `check_reproducibility` from `governance/__init__.py`
  - [ ] 4.2 Export `ReproducibilityResult` from `governance/__init__.py`
  - [ ] 4.3 Update module docstring with new exports

- [ ] Task 5: Create tests (AC: #1-6)
  - [ ] 5.1 Create `tests/governance/test_reproducibility.py`
  - [ ] 5.2 Test `ReproducibilityResult` dataclass (immutability, fields, details method)
  - [ ] 5.3 Test `check_reproducibility()` with matching outputs (passes)
  - [ ] 5.4 Test `check_reproducibility()` with modified output (fails with mismatch)
  - [ ] 5.5 Test `check_reproducibility()` with missing output (fails with missing)
  - [ ] 5.6 Test tolerance-based comparison for floating-point differences (with `reference_output_paths`)
  - [ ] 5.7 Integration test: full reproducibility cycle with MockAdapter (AC-6)
  - [ ] 5.8 Run `ruff check src/reformlab/governance tests/governance`
  - [ ] 5.9 Run `mypy src/reformlab/governance`
  - [ ] 5.10 Run targeted tests (`pytest tests/governance -v`)

## Dev Notes

### Architecture Compliance

This story implements **NFR6** (bit-identical on same machine) and **NFR7** (identical across machines with same versions) from the PRD.

**Key architectural constraints:**

- **Determinism is non-negotiable** - Every run must be reproducible; seeds are explicit, logged in manifests, derived deterministically (`master_seed XOR year`). [Source: project-context.md#Critical-Implementation-Rules]
- **Frozen dataclasses are the default** - `ReproducibilityResult` must be `@dataclass(frozen=True)`. [Source: project-context.md#Python-Language-Rules]
- **Use existing infrastructure** - Reuse `verify_artifact_hashes()` and `ArtifactVerificationResult` from Story 5-4. Do NOT duplicate hashing logic.
- **Preserve subsystem boundaries** - Governance validates reproducibility; orchestrator execution remains in orchestrator/interfaces layers via injected `rerun_callable`.
- **PyArrow is the canonical data type** - If loading Parquet for tolerance comparison, use `pa.Table`, not pandas. [Source: project-context.md#Critical-Implementation-Rules]
- **Subsystem-specific exceptions** - If errors are needed, define in `governance/errors.py`. Never raise bare `ValueError`.

### Existing Code to Reuse

**From `governance/hashing.py` (Story 5-4):**
```python
def verify_artifact_hashes(
    manifest: dict[str, str] | RunManifest,
    artifact_paths: dict[str, Path],
) -> ArtifactVerificationResult:
    """Verify stored hashes against current file contents."""
```

**From `governance/manifest.py` (Story 5-1):**
- `RunManifest.seeds: dict[str, int]` - Contains `"master"` key with master seed
- `RunManifest.child_manifests: dict[int, str]` - Year keys reveal projection range
- `RunManifest.parameters: dict[str, Any]` - Scenario parameters
- `RunManifest.step_pipeline: list[str]` - Step names executed

**From `orchestrator/runner.py` (Story 3-6):**
- `_derive_year_seed(year: int) -> int | None` - `master_seed XOR year`
- `OrchestratorRunner.run(request)` defines the rerun request contract used by caller-provided rerun callables

### Implementation Pattern

```python
@dataclass(frozen=True)
class ReproducibilityResult:
    """Result of reproducibility check."""
    passed: bool
    hash_mismatches: list[str]
    missing_artifacts: list[str]
    rerun_seeds: dict[str, int]
    original_seeds: dict[str, int]
    year_range: tuple[int, int]
    tolerance_used: float

    def details(self) -> str:
        """Return human-readable diagnostic summary."""
        lines = [f"Reproducibility check: {'PASSED' if self.passed else 'FAILED'}"]
        lines.append(f"Year range: {self.year_range[0]}-{self.year_range[1]}")
        lines.append(f"Tolerance: {self.tolerance_used}")
        if self.hash_mismatches:
            lines.append(f"Hash mismatches: {', '.join(self.hash_mismatches)}")
        if self.missing_artifacts:
            lines.append(f"Missing artifacts: {', '.join(self.missing_artifacts)}")
        return "\n".join(lines)


def check_reproducibility(
    manifest: RunManifest,
    input_paths: dict[str, Path],
    output_paths: dict[str, Path],
    rerun_callable: Callable[..., Any],
    tolerance: float = 0.0,
    reference_output_paths: dict[str, Path] | None = None,
) -> ReproducibilityResult:
    """Re-execute a run and verify outputs match original.

    Args:
        manifest: Original run manifest with seeds, parameters, hashes.
        input_paths: Mapping of manifest data_hash keys to current file paths.
        output_paths: Mapping of manifest output_hash keys to rerun output paths.
        rerun_callable: Callable that executes the rerun using manifest-derived config.
        tolerance: Floating-point tolerance for soft comparison (0.0 = strict).
        reference_output_paths: Optional original output artifact paths used for
            tolerance-based comparisons when strict hashes differ.

    Returns:
        ReproducibilityResult with comparison outcome and diagnostics.
    """
    # Extract parameters from manifest
    year_range = _extract_year_range(manifest)
    master_seed = manifest.seeds.get("master")

    # Execute rerun (governance does not construct orchestrator runner directly)
    _execute_rerun(rerun_callable, manifest, input_paths)

    # Compare outputs
    if tolerance == 0.0:
        verification = verify_artifact_hashes(manifest.output_hashes, output_paths)
        return ReproducibilityResult(
            passed=verification.passed,
            hash_mismatches=verification.mismatches,
            missing_artifacts=verification.missing,
            rerun_seeds={"master": master_seed} if master_seed else {},
            original_seeds=dict(manifest.seeds),
            year_range=year_range,
            tolerance_used=tolerance,
        )
    else:
        return _compare_with_tolerance(
            manifest,
            output_paths,
            tolerance,
            year_range,
            reference_output_paths=reference_output_paths,
        )
```

### Module Structure

```
src/reformlab/governance/
├── __init__.py           # Add reproducibility exports
├── manifest.py           # Existing RunManifest
├── errors.py             # Existing errors (add ReproducibilityError if needed)
├── capture.py            # Existing capture helpers
├── lineage.py            # Existing lineage helpers
├── hashing.py            # Existing hashing (reuse verify_artifact_hashes)
└── reproducibility.py    # NEW: check_reproducibility, ReproducibilityResult

tests/governance/
├── __init__.py
├── conftest.py           # Add reproducibility fixtures
├── test_manifest.py      # Existing
├── test_capture.py       # Existing
├── test_lineage.py       # Existing
├── test_hashing.py       # Existing
└── test_reproducibility.py  # NEW: Reproducibility tests
```

### Scope Guardrails

- **In scope:**
  - `ReproducibilityResult` dataclass
  - `check_reproducibility()` function
  - Strict hash comparison (tolerance=0)
  - Optional tolerance-based soft comparison for hash-mismatched artifacts only
  - Integration with existing governance module
  - Unit and integration tests

- **Out of scope:**
  - Automated rerun scheduling
  - CI/CD integration for reproducibility checks
  - Cross-version compatibility testing
  - Parallel execution of reruns
  - Caching of rerun results
  - UI for reproducibility verification

### Testing Standards

- Mirror source structure: `tests/governance/test_reproducibility.py`
- Class-based test grouping: `TestReproducibilityResult`, `TestCheckReproducibility`, `TestReproducibilityIntegration`
- Use `tmp_path` fixture for file creation
- Use `MockAdapter` from `computation/mock_adapter.py` for orchestrator tests
- Test both strict (tolerance=0) and soft (tolerance>0) comparison
- Integration test must complete full cycle: run -> manifest -> rerun -> verify

### Previous Story Intelligence

From Story 5-4 (hashing):
- `hash_file()` uses 64KB chunks for memory efficiency
- `verify_artifact_hashes()` returns `ArtifactVerificationResult` without exceptions on mismatch
- Orchestrator integration already captures hashes via `_capture_manifest_fields()`

From Story 5-3 (lineage):
- `child_manifests: dict[int, str]` maps year to child manifest ID
- Year keys can be used to determine projection range: `min(keys)` to `max(keys)`

From Story 5-2 (capture):
- Manifest capture happens at runner boundary
- Seeds are captured as `{"master": seed, "year_{n}": derived_seed, ...}`

### References

- [Source: prd.md#Non-Functional-Requirements] - NFR6 bit-identical on same machine, NFR7 cross-machine reproducibility
- [Source: backlog BKL-505] - Story acceptance criteria
- [Source: architecture.md#Reproducibility-&-Governance] - Cross-machine tolerances
- [Source: 5-4-hash-input-output-artifacts.md] - Hash verification patterns
- [Source: governance/hashing.py] - `verify_artifact_hashes()` implementation
- [Source: governance/manifest.py] - `RunManifest` schema with seeds, child_manifests
- [Source: orchestrator/runner.py:362-379] - `_derive_year_seed()` implementation

## Dev Agent Record

### Agent Model Used

Unknown (record not captured during implementation)

### Debug Log References

- Dev Agent Record backfilled during Phase 1 retro cleanup. Original debug logs were not recorded.

### Completion Notes List

- Dev Agent Record backfilled during Phase 1 retro cleanup. Original implementation agent and debug details were not recorded.

### File List

- `src/reformlab/governance/__init__.py` (modified) — governance package exports updated
- `src/reformlab/governance/reproducibility.py` (new) — reproducibility check harness implementation
- `src/reformlab/governance/errors.py` (modified) — governance error types extended
- `tests/governance/test_reproducibility.py` (new) — reproducibility harness tests
