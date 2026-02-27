# Story 5.1: Define Immutable Run Manifest Schema v1

Status: ready-for-dev

## Story

As a **policy analyst**,
I want **every simulation run to produce an immutable manifest documenting all parameters, data sources, and assumptions**,
so that **I can reproduce any run and audit its methodology**.

## Acceptance Criteria

From backlog (BKL-501), aligned with FR25 and NFR9.

1. **AC-1: Schema completeness and architecture-required fields**
   - Given a completed simulation run, when a `RunManifest` is created, then it includes all required governance fields from architecture:
     - `manifest_id`, `created_at`
     - `engine_version`, `openfisca_version`, `adapter_version`, `scenario_version`
     - `data_hashes`, `output_hashes` (all SHA-256 hex digests)
     - `seeds` (master seed + per-year seeds where available)
     - `assumptions`, `step_pipeline`, `parameters`
   - And field names/types are stable and documented in the schema model.

2. **AC-2: Immutable schema objects**
   - `RunManifest` and nested manifest schema types are `@dataclass(frozen=True)`.
   - Any attempted post-construction mutation fails deterministically (`FrozenInstanceError`).

3. **AC-3: Deterministic canonical serialization**
   - Manifest serialization to JSON is canonical and deterministic (sorted keys, stable separators, UTF-8).
   - Serializing the same manifest content on different machines produces byte-equivalent JSON output.
   - `from_json()` recreates an equivalent immutable manifest object.

4. **AC-4: Integrity hash and tamper detection**
   - `compute_integrity_hash()` computes SHA-256 over canonical manifest content excluding `integrity_hash`.
   - `verify_integrity()` raises `ManifestIntegrityError` when any manifest field is altered after hash computation.

5. **AC-5: Validation and explicit errors**
   - Missing required fields, invalid hash format, or invalid structural types raise `ManifestValidationError` with actionable messages.
   - Validation is applied on deserialization and on explicit verification calls.

## Dependencies

- **Required prior stories:**
  - Story 1-1 (BKL-101): adapter version contract source
  - Story 2-4 (BKL-204): scenario registry/version source
  - Story 3-2 (BKL-302): step pipeline contract source
  - Story 3-6 (BKL-306): seed log structure source
  - Story 3-7 (BKL-307): output artifact surface to hash
- **Current prerequisite status (from `_bmad-output/implementation-artifacts/sprint-status.yaml`, checked 2026-02-27):**
  - `1-1-define-computationadapter-interface-and-openfiscaadapter-implementation`: `done`
  - `2-4-build-scenario-registry`: `done`
  - `3-2-define-orchestrator-step-interface`: `done`
  - `3-6-log-seed-controls`: `done`
  - `3-7-produce-scenario-year-panel-output`: `done`
- **Follow-on stories:**
  - Story 5-2 (BKL-502): persists assumptions/mappings/parameters into manifests at runtime
  - Story 5-3 (BKL-503): lineage graph using manifest identifiers/links
  - Story 5-4 (BKL-504): hashing pipeline integration for full run inputs/outputs
  - Story 5-5 (BKL-505): reproducibility harness consuming manifest schema

## Tasks / Subtasks

- [ ] Task 0: Confirm prerequisite contracts and boundaries (AC: dependency check)
  - [ ] 0.1 Verify required prerequisite story statuses remain `done` in `sprint-status.yaml`
  - [ ] 0.2 Confirm source contracts for `scenario_version`, `step_pipeline`, and seed structures from Stories 2-4, 3-2, 3-6
  - [ ] 0.3 Confirm this story defines schema and integrity mechanics only (no orchestrator wiring/persistence)

- [ ] Task 1: Define immutable manifest schema models (AC: #1, #2)
  - [ ] 1.1 Create `src/reformlab/governance/manifest.py`
  - [ ] 1.2 Define frozen `RunManifest` with architecture-required fields:
    - `manifest_id`, `created_at`
    - `engine_version`, `openfisca_version`, `adapter_version`, `scenario_version`
    - `data_hashes`, `output_hashes`, `seeds`, `assumptions`, `step_pipeline`, `parameters`, `integrity_hash`
  - [ ] 1.3 Define frozen nested types (e.g., `YearlyManifest`, `ManifestMetadata`, or equivalent) only where needed for schema clarity

- [ ] Task 2: Implement canonical JSON serialization (AC: #3, #5)
  - [ ] 2.1 Implement `to_json()` canonical serialization (sorted keys, stable separators, UTF-8)
  - [ ] 2.2 Implement `from_json()` with schema validation and explicit error mapping to `ManifestValidationError`
  - [ ] 2.3 Ensure stable round-trip for all required fields

- [ ] Task 3: Implement integrity hashing and verification (AC: #4, #5)
  - [ ] 3.1 Add `compute_integrity_hash()` excluding `integrity_hash` from hash input
  - [ ] 3.2 Add `verify_integrity()` raising `ManifestIntegrityError` on mismatch
  - [ ] 3.3 Enforce SHA-256 hex format validation for `data_hashes`, `output_hashes`, and `integrity_hash`

- [ ] Task 4: Add governance errors and API surface (AC: #4, #5)
  - [ ] 4.1 Create `src/reformlab/governance/errors.py`
  - [ ] 4.2 Define `ManifestIntegrityError` and `ManifestValidationError`
  - [ ] 4.3 Export public manifest schema APIs from `src/reformlab/governance/__init__.py`

- [ ] Task 5: Write focused tests and run quality gates (AC: #1-#5)
  - [ ] 5.1 Create `tests/governance/test_manifest.py`
  - [ ] 5.2 Test required-field completeness and frozen immutability behavior
  - [ ] 5.3 Test canonical JSON determinism and round-trip equality
  - [ ] 5.4 Test tampering detection and integrity mismatch errors
  - [ ] 5.5 Test validation failures for missing fields and invalid hash formats
  - [ ] 5.6 Run `ruff check src/reformlab/governance tests/governance`
  - [ ] 5.7 Run `mypy src/reformlab/governance`
  - [ ] 5.8 Run `pytest tests/governance/test_manifest.py -v`

## Dev Notes

### Architecture Compliance

This story implements **FR25** (immutable run manifests) and **NFR9** (automatic manifest generation with zero manual effort).
It covers manifest schema definition, canonical serialization, and integrity verification only.

**Key architectural constraints:**

- **Frozen dataclasses only** - All manifest types MUST use `@dataclass(frozen=True)`. Never add mutable dataclasses. [Source: project-context.md#Critical-Implementation-Rules]
- **JSON output** - Manifests are JSON, machine-readable, Git-diffable. [Source: architecture.md#Reproducibility-&-Governance]
- **SHA-256 hashing** - All content hashes use SHA-256 without embedding raw data. [Source: architecture.md#Reproducibility-&-Governance]
- **Deterministic serialization** - JSON must be sorted-key, stable for cross-machine reproducibility. [Source: NFR6, NFR7]

### Required Manifest Fields

From architecture.md and backlog, the manifest MUST include:

| Field | Type | Description |
|-------|------|-------------|
| `manifest_id` | `str` | UUID for this manifest |
| `created_at` | `str` | ISO 8601 timestamp |
| `engine_version` | `str` | ReformLab package version |
| `openfisca_version` | `str` | OpenFisca package/model version used by the adapter |
| `adapter_version` | `str` | OpenFiscaAdapter version string |
| `scenario_version` | `str` | Version ID from scenario registry |
| `data_hashes` | `dict[str, str]` | SHA-256 of input files by path reference |
| `output_hashes` | `dict[str, str]` | SHA-256 of output artifacts by artifact key/path |
| `seeds` | `dict[str, int]` | All random seeds used (master + per-year) |
| `parameters` | `dict[str, Any]` | Complete parameter snapshot |
| `assumptions` | `list[str]` | Explicit assumption keys used |
| `step_pipeline` | `list[str]` | Ordered step names executed |
| `integrity_hash` | `str` | SHA-256 of entire manifest (excluding this field) |

### Module Structure

```
src/reformlab/governance/
├── __init__.py          # Public exports
├── manifest.py          # RunManifest, YearlyManifest, ManifestMetadata
├── errors.py            # ManifestIntegrityError, ManifestValidationError
└── types.py             # DataSourceReference, VersionInfo, ParameterSnapshot (optional, can be in manifest.py)

tests/governance/
├── __init__.py
├── conftest.py          # Test fixtures
└── test_manifest.py     # All manifest tests
```

### Implementation Patterns

**Follow existing frozen dataclass pattern** from `orchestrator/types.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class RunManifest:
    """Immutable run manifest documenting all parameters, data sources, and assumptions.

    Every simulation run produces one manifest. Integrity is verified via SHA-256 hash.
    """
    manifest_id: str
    created_at: str  # ISO 8601
    engine_version: str
    openfisca_version: str
    adapter_version: str
    scenario_version: str
    data_hashes: dict[str, str] = field(default_factory=dict)
    output_hashes: dict[str, str] = field(default_factory=dict)
    # ... etc
```

**Integrity hash computation** - exclude the integrity_hash field itself:

```python
def compute_integrity_hash(self) -> str:
    """Compute SHA-256 hash of manifest content (excluding integrity_hash)."""
    import hashlib
    import json

    # Create dict without integrity_hash
    content = {k: v for k, v in self.__dict__.items() if k != 'integrity_hash'}
    # Deterministic JSON: sorted keys, no indent, separators without spaces
    canonical = json.dumps(content, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
```

### Testing Standards

- Mirror source structure: `tests/governance/` matches `src/reformlab/governance/`
- Class-based test grouping: `TestRunManifestCreation`, `TestManifestIntegrity`, `TestManifestSerialization`
- Direct assertions with plain `assert`
- Use `pytest.raises(ManifestIntegrityError, match=...)` for error tests
- Test fixtures in `tests/governance/conftest.py`

### Scope Guardrails

- **In scope:**
  - Immutable schema dataclasses and required fields
  - Canonical serialization/deserialization
  - Integrity hash computation and verification APIs
  - Unit tests for schema behavior and integrity checks
- **Out of scope:**
  - Runtime orchestration wiring (manifest generation during run execution)
  - Persistence/orchestration integration across all subsystems
  - Lineage graph generation and UI visualization (later stories)

### Project Structure Notes

- **New module**: `src/reformlab/governance/manifest.py` - first real code in governance subsystem
- **Existing empty**: `src/reformlab/governance/__init__.py` exists but is empty
- **Test structure**: `tests/governance/__init__.py` exists but empty
- **Naming**: snake_case for files, PascalCase for classes

### References

- [Source: architecture.md#Reproducibility-&-Governance] - Manifest requirements
- [Source: backlog BKL-501] - Story acceptance criteria
- [Source: backlog BKL-504] - SHA-256 hashing requirement
- [Source: prd.md#Reproducibility-&-Auditability] - FR25, NFR9
- [Source: project-context.md#Critical-Implementation-Rules] - Frozen dataclasses, determinism

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
