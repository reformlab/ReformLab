# Story 5.1: Define Immutable Run Manifest Schema v1

Status: ready-for-dev

## Story

As a **policy analyst**,
I want **every simulation run to produce an immutable manifest documenting all parameters, data sources, and assumptions**,
so that **I can reproduce any run and audit its methodology**.

## Acceptance Criteria

1. **AC1 - Manifest Generation**: Given a completed simulation run, when the manifest is generated, then it contains: engine version, adapter version, scenario version, data hashes (SHA-256), seeds, timestamps, and parameter snapshot.

2. **AC2 - Tampering Detection**: Given a generated manifest, when any field is modified, then integrity checks detect the tampering.

## Tasks / Subtasks

- [ ] Task 1: Define `RunManifest` frozen dataclass (AC: #1)
  - [ ] 1.1: Create `src/reformlab/governance/manifest.py` module
  - [ ] 1.2: Define `RunManifest` with required fields
  - [ ] 1.3: Define `YearlyManifest` for per-year child manifests
  - [ ] 1.4: Define `ManifestMetadata` for common metadata
- [ ] Task 2: Implement manifest content hashing (AC: #2)
  - [ ] 2.1: Add `compute_integrity_hash()` method to `RunManifest`
  - [ ] 2.2: Add `verify_integrity()` method for tampering detection
  - [ ] 2.3: Use SHA-256 for all hashes (content + integrity)
- [ ] Task 3: Define supporting types (AC: #1)
  - [ ] 3.1: Create `DataSourceReference` for input artifact tracking
  - [ ] 3.2: Create `VersionInfo` for engine/adapter/scenario versions
  - [ ] 3.3: Create `ParameterSnapshot` for frozen parameter state
- [ ] Task 4: Implement manifest serialization (AC: #1, #2)
  - [ ] 4.1: Add `to_json()` and `from_json()` methods
  - [ ] 4.2: Ensure JSON is deterministic (sorted keys, stable format)
  - [ ] 4.3: Test round-trip serialization
- [ ] Task 5: Add governance exceptions (AC: #2)
  - [ ] 5.1: Create `src/reformlab/governance/errors.py`
  - [ ] 5.2: Define `ManifestIntegrityError` exception
  - [ ] 5.3: Define `ManifestValidationError` exception
- [ ] Task 6: Write tests (AC: #1, #2)
  - [ ] 6.1: Create `tests/governance/test_manifest.py`
  - [ ] 6.2: Test manifest creation with all required fields
  - [ ] 6.3: Test integrity hash computation and verification
  - [ ] 6.4: Test tampering detection (modify field, verify fails)
  - [ ] 6.5: Test JSON round-trip stability
- [ ] Task 7: Export public API (AC: #1, #2)
  - [ ] 7.1: Update `src/reformlab/governance/__init__.py` with exports

## Dev Notes

### Architecture Compliance

This story implements **FR25** (immutable run manifests) and **NFR9** (automatic manifest generation with zero manual effort).

**Key architectural constraints:**

- **Frozen dataclasses only** - All manifest types MUST use `@dataclass(frozen=True)`. Never add mutable dataclasses. [Source: project-context.md#Critical-Implementation-Rules]
- **JSON output** - Manifests are JSON, machine-readable, Git-diffable. [Source: architecture.md#Reproducibility-&-Governance]
- **SHA-256 hashing** - All content hashes use SHA-256 without embedding raw data. [Source: backlog BKL-504]
- **Deterministic serialization** - JSON must be sorted-key, stable for cross-machine reproducibility. [Source: NFR6, NFR7]

### Required Manifest Fields

From architecture.md and backlog, the manifest MUST include:

| Field | Type | Description |
|-------|------|-------------|
| `manifest_id` | `str` | UUID for this manifest |
| `created_at` | `str` | ISO 8601 timestamp |
| `engine_version` | `str` | ReformLab package version |
| `adapter_version` | `str` | OpenFiscaAdapter version string |
| `scenario_version` | `str` | Version ID from scenario registry |
| `data_hashes` | `dict[str, str]` | SHA-256 of input files by path reference |
| `output_hash` | `str` | SHA-256 of output artifacts |
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
    adapter_version: str
    scenario_version: str
    data_hashes: dict[str, str] = field(default_factory=dict)
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

