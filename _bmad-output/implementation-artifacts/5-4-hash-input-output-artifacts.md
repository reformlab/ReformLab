# Story 5.4: Hash Input/Output Artifacts

Status: ready-for-dev

## Story

As a **policy analyst**,
I want **SHA-256 hashes of input data files and output artifacts to be computed and stored in the run manifest**,
so that **I can verify data integrity and detect any changes to inputs or outputs without embedding raw data in manifests**.

## Acceptance Criteria

From backlog (BKL-504), aligned with FR25 (immutable run manifests) and NFR12 (input paths referenced not embedded).

1. **AC-1: Hash input CSV/Parquet files and store in manifest**
   - Given input CSV/Parquet files used in a simulation run, when hashing is invoked, then SHA-256 hashes are computed and stored in `data_hashes` without embedding raw data.
   - Input files are identified by path reference (relative or absolute).
   - Each hash entry has format: `{path_key: sha256_hex_digest}`.
   - Hash computation uses streaming/chunked reading for large files.

2. **AC-2: Hash output artifacts and store in manifest**
   - Given output artifacts produced by a simulation run, when hashing is invoked, then SHA-256 hashes are stored in `output_hashes`.
   - Output artifacts include: yearly panel datasets, indicator exports, comparison tables.
   - Hash entries follow same format as input hashes: `{artifact_key: sha256_hex_digest}`.

3. **AC-3: Verify stored hashes after run**
   - `verify_artifact_hashes(manifest: RunManifest, artifact_paths: dict[str, Path])` verifies hashes match current file contents.
   - Returns `ArtifactVerificationResult` with `passed: bool`, `mismatches: list[str]`, `missing: list[str]`.
   - Raises no exception on mismatch — returns structured result for caller to handle.

4. **AC-4: Hash computation is deterministic**
   - Given the same file contents, when hashed on different machines or at different times, then identical SHA-256 digests are produced.
   - Hash computation uses standard SHA-256 without any platform-specific behavior.
   - Binary files are hashed as-is; no content transformation before hashing.

5. **AC-5: Integration with orchestrator capture boundary**
   - Hashing functions are called from `OrchestratorRunner._capture_manifest_fields()` when input/output paths are available.
   - Hash computation is automatic and requires zero manual user steps (NFR9 compliance).
   - Hash capture extends existing manifest capture flow without modifying manifest schema (fields already exist).

## Dependencies

- **Hard dependencies (from backlog BKL-504):**
  - Story 5-1 (BKL-501): immutable `RunManifest` schema with `data_hashes` and `output_hashes` fields ✅ DONE
- **Integration dependencies:**
  - Story 5-2 (BKL-502): orchestrator-boundary governance capture (`_capture_manifest_fields`) ✅ DONE
  - Story 5-3 (BKL-503): lineage graph for artifact tracking context ✅ DONE
- **Status source (checked 2026-02-27):**
  - `_bmad-output/implementation-artifacts/sprint-status.yaml`

- **Follow-on stories:**
  - Story 5-5 (BKL-505): Reproducibility check harness (uses hashes for rerun verification)
  - Story 5-6 (BKL-506): Warning system for unvalidated templates

## Tasks / Subtasks

- [ ] Task 0: Review prerequisite contracts and boundaries (AC: dependency check)
  - [ ] 0.1 Verify dependency statuses remain `done` in `sprint-status.yaml` for 5-1, 5-2, 5-3
  - [ ] 0.2 Review `RunManifest` schema fields `data_hashes` and `output_hashes` from Story 5-1
  - [ ] 0.3 Review orchestrator capture boundary from Story 5-2 (`OrchestratorRunner._capture_manifest_fields()`)
  - [ ] 0.4 Confirm SHA-256 validation already exists in manifest.py (`SHA256_PATTERN`)

- [ ] Task 1: Implement file hashing utilities (AC: #1, #4)
  - [ ] 1.1 Create `src/reformlab/governance/hashing.py`
  - [ ] 1.2 Implement `hash_file(path: Path) -> str` with chunked/streaming SHA-256
  - [ ] 1.3 Use 64KB chunks for memory-efficient hashing of large files
  - [ ] 1.4 Handle file-not-found with explicit error message
  - [ ] 1.5 Ensure binary mode reading (no text encoding issues)

- [ ] Task 2: Implement input artifact hashing (AC: #1)
  - [ ] 2.1 Implement `hash_input_artifacts(paths: dict[str, Path]) -> dict[str, str]`
  - [ ] 2.2 Accept dictionary of path_key -> Path mapping
  - [ ] 2.3 Return dictionary of path_key -> SHA-256 hex digest
  - [ ] 2.4 Skip missing files with warning logged (don't fail entire run)

- [ ] Task 3: Implement output artifact hashing (AC: #2)
  - [ ] 3.1 Implement `hash_output_artifacts(paths: dict[str, Path]) -> dict[str, str]`
  - [ ] 3.2 Accept dictionary of artifact_key -> Path mapping
  - [ ] 3.3 Return dictionary of artifact_key -> SHA-256 hex digest
  - [ ] 3.4 Output files must exist at hash time (raise if missing)

- [ ] Task 4: Implement hash verification (AC: #3)
  - [ ] 4.1 Create `ArtifactVerificationResult` dataclass with `passed`, `mismatches`, `missing`
  - [ ] 4.2 Implement `verify_artifact_hashes(manifest: RunManifest, artifact_paths: dict[str, Path]) -> ArtifactVerificationResult`
  - [ ] 4.3 Compare stored hashes against recomputed hashes
  - [ ] 4.4 Report mismatches with path and expected vs actual hash
  - [ ] 4.5 Report missing files (path in manifest but file not found)

- [ ] Task 5: Wire hashing into orchestrator capture boundary (AC: #5)
  - [ ] 5.1 Update `OrchestratorRunner._capture_manifest_fields()` to accept input/output paths
  - [ ] 5.2 Call `hash_input_artifacts()` when input paths provided
  - [ ] 5.3 Call `hash_output_artifacts()` when output paths provided
  - [ ] 5.4 Merge hash results into manifest capture payload

- [ ] Task 6: Export public APIs (AC: #1-4)
  - [ ] 6.1 Export `hash_file`, `hash_input_artifacts`, `hash_output_artifacts` from `governance/__init__.py`
  - [ ] 6.2 Export `verify_artifact_hashes`, `ArtifactVerificationResult` from `governance/__init__.py`

- [ ] Task 7: Tests and quality gates (AC: #1-5)
  - [ ] 7.1 Create `tests/governance/test_hashing.py`
  - [ ] 7.2 Test `hash_file()` with small and large files
  - [ ] 7.3 Test hash determinism (same content → same hash across calls)
  - [ ] 7.4 Test `hash_input_artifacts()` with valid and missing files
  - [ ] 7.5 Test `hash_output_artifacts()` with valid paths
  - [ ] 7.6 Test `verify_artifact_hashes()` success and mismatch cases
  - [ ] 7.7 Test orchestrator integration captures hashes in metadata
  - [ ] 7.8 Run `ruff check src/reformlab/governance tests/governance`
  - [ ] 7.9 Run `mypy src/reformlab/governance`
  - [ ] 7.10 Run targeted tests (`pytest tests/governance -v`)

## Dev Notes

### Architecture Compliance

This story implements **FR25** (immutable run manifests with data hashes) and **NFR12** (input data paths referenced not embedded).

**Key architectural constraints:**

- **No raw data in manifests** - Only SHA-256 hashes are stored, not file contents. Paths are reference keys. [Source: prd.md#Non-Functional-Requirements NFR12]
- **Deterministic hashing** - Standard SHA-256 without platform-specific behavior ensures cross-machine reproducibility. [Source: prd.md#Non-Functional-Requirements NFR6-7]
- **Zero manual effort** - Hash computation is automatic at orchestrator boundary. [Source: prd.md#Non-Functional-Requirements NFR9]
- **Memory-efficient** - Chunked/streaming hashing for large CSV/Parquet files (up to 500k households). [Source: prd.md#Non-Functional-Requirements NFR3]

### Previous Story Intelligence

From Story 5-1 implementation (manifest schema):
- `RunManifest` already has `data_hashes: dict[str, str]` and `output_hashes: dict[str, str]` fields
- Hash validation uses `SHA256_PATTERN = re.compile(r"^[a-fA-F0-9]{64}$")`
- Validation raises `ManifestValidationError` for invalid hash formats
- All hash dict keys must be non-empty strings

From Story 5-2 implementation (capture):
- `OrchestratorRunner._capture_manifest_fields()` is the integration point
- Capture functions return JSON-compatible dictionaries
- Capture happens once at runner boundary, not per-step

From Story 5-3 implementation (lineage):
- Lineage capture happens in same boundary as manifest capture
- Pattern: generate IDs at run start, build maps from completed results

### Existing Patterns to Follow

**Chunked file hashing pattern:**
```python
import hashlib
from pathlib import Path

CHUNK_SIZE = 65536  # 64KB chunks for memory efficiency

def hash_file(path: Path) -> str:
    """Compute SHA-256 hash of a file using streaming reads.

    Args:
        path: Path to the file to hash.

    Returns:
        SHA-256 hex digest (64 lowercase hex characters).

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    sha256 = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            sha256.update(chunk)
    return sha256.hexdigest()
```

**Verification result pattern:**
```python
@dataclass(frozen=True)
class ArtifactVerificationResult:
    """Result of artifact hash verification."""
    passed: bool
    mismatches: tuple[str, ...]  # path keys with hash mismatch
    missing: tuple[str, ...]  # path keys where file not found

    @property
    def failed(self) -> bool:
        return not self.passed
```

**Capture integration pattern** (extending existing boundary):
```python
def _capture_manifest_fields(
    self,
    request: dict[str, Any],
    parent_manifest_id: str,
    child_manifests: dict[int, str],
    input_paths: dict[str, Path] | None = None,  # NEW
    output_paths: dict[str, Path] | None = None,  # NEW
) -> dict[str, Any]:
    # ... existing capture logic ...

    # Hash artifacts if paths provided
    data_hashes: dict[str, str] = {}
    if input_paths:
        data_hashes = hash_input_artifacts(input_paths)

    output_hashes: dict[str, str] = {}
    if output_paths:
        output_hashes = hash_output_artifacts(output_paths)

    return {
        # ... existing fields ...
        "data_hashes": data_hashes,
        "output_hashes": output_hashes,
    }
```

### Module Structure

```
src/reformlab/governance/
├── __init__.py          # Add hashing exports
├── manifest.py          # Existing (data_hashes, output_hashes fields)
├── errors.py            # Existing
├── capture.py           # Existing capture helpers
├── lineage.py           # Existing lineage helpers
└── hashing.py           # NEW: hash_file, hash_*_artifacts, verify_*

tests/governance/
├── __init__.py
├── conftest.py          # Add hashing test fixtures
├── test_manifest.py     # Existing
├── test_capture.py      # Existing
├── test_lineage.py      # Existing
└── test_hashing.py      # NEW: Hashing and verification tests
```

### Scope Guardrails

- **In scope:**
  - `hash_file()` streaming file hasher
  - `hash_input_artifacts()` for input data files
  - `hash_output_artifacts()` for output artifacts
  - `verify_artifact_hashes()` for post-run verification
  - `ArtifactVerificationResult` dataclass
  - Orchestrator integration for automatic hashing
  - Unit tests for all hashing functions

- **Out of scope:**
  - Reproducibility check harness (Story 5-5)
  - Warning system for unvalidated templates (Story 5-6)
  - Hash-based caching or deduplication
  - Artifact storage/persistence layer
  - UI for hash verification

### Testing Standards

- Mirror source structure: `tests/governance/test_hashing.py`
- Class-based test grouping: `TestHashFile`, `TestHashInputArtifacts`, `TestVerification`
- Direct assertions with plain `assert`
- Use `pytest.raises(FileNotFoundError)` for missing file tests
- Use `tmp_path` fixture for test file creation
- Test with both small (< 1KB) and larger (> 64KB) files to exercise chunking

### File Size Considerations

- Parquet files for 100k households: typically 5-50 MB
- CSV files for 100k households: typically 50-200 MB
- 64KB chunk size ensures efficient memory usage
- No need to handle files > 500MB (architecture constraint: NFR3 caps at 500k households)

### Project Structure Notes

- **Existing governance module**: `src/reformlab/governance/` with `manifest.py`, `capture.py`, `errors.py`, `lineage.py`
- **Orchestrator integration point**: `src/reformlab/orchestrator/runner.py` `OrchestratorRunner._capture_manifest_fields()`
- **Manifest fields already exist**: `data_hashes` and `output_hashes` with SHA256 validation
- **Naming**: snake_case for files, PascalCase for classes

### References

- [Source: architecture.md#Reproducibility-&-Governance] - Hash requirements
- [Source: backlog BKL-504] - Story acceptance criteria
- [Source: prd.md#Governance-&-Reproducibility] - FR25 immutable manifests with hashes
- [Source: prd.md#Non-Functional-Requirements] - NFR12 no raw data in manifests, NFR9 zero manual effort
- [Source: 5-1-define-immutable-run-manifest-schema.md] - Manifest schema with hash fields
- [Source: 5-2-capture-assumptions-mappings-parameters.md] - Capture pattern at runner boundary
- [Source: manifest.py:31-35] - SHA256_PATTERN regex for hash validation

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
