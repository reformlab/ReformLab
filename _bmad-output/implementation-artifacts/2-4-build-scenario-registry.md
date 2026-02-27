# Story 2.4: Build Scenario Registry with Immutable Version IDs

Status: review

## Story

As a **policy analyst**,
I want **a scenario registry that stores versioned scenario definitions with immutable version IDs**,
so that **I can reliably retrieve, track, and audit scenario configurations across runs, ensuring full reproducibility and enabling scenario comparison workflows**.

## Acceptance Criteria

Scope note: BKL-204 baseline is AC-1 through AC-3 (per backlog). AC-4 and AC-5 are implementation details that support that baseline and must not expand into orchestrator integration, scenario cloning, or multi-user synchronization.

1. **AC-1: Scenario can be saved to registry with immutable version ID**
   - Given a scenario saved to the registry, when retrieved by version ID, then the returned definition is identical to what was saved.
   - Version IDs are deterministically generated from scenario content (content-addressable hash).
   - Saved scenarios are immutable: once saved, the definition cannot be modified.

2. **AC-2: Modified scenario creates new version**
   - Given a saved scenario, when modified and re-saved, then a new version ID is assigned and the previous version remains accessible.
   - Version history is preserved: all previous versions of a scenario remain retrievable.
   - Version metadata includes timestamp, parent version (if any), and optional change description.

3. **AC-3: Invalid version ID produces clear error**
   - Given an invalid version ID, when queried, then a clear error indicates the version does not exist.
   - Error message includes the requested version ID and suggests listing available versions.

4. **AC-4: Registry supports listing and version lookup**
   - Registry provides `list_scenarios()` returning all stored scenario names with latest version.
   - Registry provides `list_versions(scenario_name)` returning version history for a specific scenario.
   - Registry provides `get(name, version_id=None)` where None returns latest version.

5. **AC-5: Registry persistence is file-based and portable**
   - Registry stores scenarios in a structured directory format suitable for version control.
   - Registry location is configurable (default: `~/.reformlab/registry/` or project-local).
   - Registry format is YAML for human readability and Git diffability, using existing template loader/dumper conventions.

## Tasks / Subtasks

- [x] Task 0: Validate prerequisites and story boundaries
  - [x] 0.1 Confirm Story 2.1 / BKL-201 is `done` in `sprint-status.yaml` before implementation starts
  - [x] 0.2 Treat Stories 2.2 and 2.3 as optional integration inputs only (not hard blockers for BKL-204)
  - [x] 0.3 Confirm Story 2.4 implementation excludes orchestrator integration, cloning workflows, and multi-user sync

- [x] Task 1: Design registry data model and storage format (AC: #1, #5)
  - [x] 1.1 Define `ScenarioVersion` dataclass with version_id, timestamp, parent_version, change_description
  - [x] 1.2 Define `RegistryEntry` dataclass with scenario_name, versions dict, latest_version pointer
  - [x] 1.3 Design file layout: `registry/{scenario_name}/versions/{version_id}.yaml` + `registry/{scenario_name}/metadata.yaml`
  - [x] 1.4 Define version ID generation strategy using deterministic content hash (SHA-256 prefix)

- [x] Task 2: Implement core registry class (AC: #1, #2, #3, #4)
  - [x] 2.1 Create `src/reformlab/templates/registry.py` with `ScenarioRegistry` class
  - [x] 2.2 Implement `save(scenario: BaselineScenario | ReformScenario, name: str, change_description: str = "") -> str` returning version_id
  - [x] 2.3 Implement `get(name: str, version_id: str | None = None) -> BaselineScenario | ReformScenario`
  - [x] 2.4 Implement `list_scenarios() -> list[str]`
  - [x] 2.5 Implement `list_versions(name: str) -> list[ScenarioVersion]`
  - [x] 2.6 Implement `exists(name: str, version_id: str | None = None) -> bool`

- [x] Task 3: Implement version ID generation and immutability (AC: #1, #2)
  - [x] 3.1 Implement content-based version ID using SHA-256 hash of serialized scenario
  - [x] 3.2 Add immutability check: if version_id already exists, verify content matches (idempotent save)
  - [x] 3.3 Implement version metadata storage (timestamp, parent_version, change_description)
  - [x] 3.4 Add `RegistryError` exception for version conflicts, not found, etc.

- [x] Task 4: Implement registry persistence layer (AC: #5)
  - [x] 4.1 Create `_save_scenario_file()` and `_load_scenario_file()` using existing YAML loader pattern
  - [x] 4.2 Create `_save_metadata()` and `_load_metadata()` for registry entry metadata
  - [x] 4.3 Implement configurable registry path (env var `REFORMLAB_REGISTRY_PATH` or constructor param)
  - [x] 4.4 Implement `initialize()` method for first-time registry setup
  - [x] 4.5 Use atomic write pattern (temp file + replace) for single-machine safety; multi-writer locking is out of scope

- [x] Task 5: Implement error handling (AC: #3)
  - [x] 5.1 Create `RegistryError` exception following `ScenarioError` pattern
  - [x] 5.2 Implement `ScenarioNotFoundError` for missing scenarios
  - [x] 5.3 Implement `VersionNotFoundError` for missing versions
  - [x] 5.4 Add helpful error messages with available alternatives (suggest `list_versions()`)

- [x] Task 6: Write comprehensive tests (AC: all)
  - [x] 6.1 Unit tests for version ID generation (deterministic, content-based)
  - [x] 6.2 Unit tests for save/get round-trip
  - [x] 6.3 Unit tests for version history tracking
  - [x] 6.4 Unit tests for error cases (not found, invalid ID)
  - [x] 6.5 Integration tests for file persistence
  - [x] 6.6 Tests for registry with multiple scenarios and versions

## Dev Notes

### Architecture Patterns to Follow

**From architecture.md:**
- `templates/` subsystem: Environmental policy templates and **scenario registry with versioned definitions**
- Scenario/template versioning for auditability and collaboration (Cross-Cutting Concern #5)
- Reproducibility & Governance: "Every run records: ... scenario version..." (section)
- Run governance schema requires scenario version references

**From PRD:**
- FR9: System stores versioned scenario definitions in a scenario registry
- FR28: Results are pinned to scenario version, data version, and OpenFisca adapter/version
- FR26: Analyst can inspect assumptions and mappings used in any run (requires version retrieval)

### Existing Code Patterns to Follow

**From Story 2.1 (`src/reformlab/templates/`):**
- `BaselineScenario` and `ReformScenario` dataclasses (frozen, immutable)
- `load_scenario_template()` and `dump_scenario_template()` for YAML I/O
- `ScenarioError` exception pattern with structured error messages

**YAML serialization pattern (from `loader.py`):**
```python
def dump_scenario_template(scenario: BaselineScenario | ReformScenario, path: str | Path) -> None:
    """Serialize scenario to YAML file."""
    # Already implemented in Story 2.1
```

**Error handling pattern:**
```python
class RegistryError(Exception):
    """Base exception for registry operations."""
    def __init__(
        self,
        *,
        summary: str,
        reason: str,
        fix: str,
        scenario_name: str = "",
        version_id: str = "",
    ) -> None:
        self.summary = summary
        self.reason = reason
        self.fix = fix
        self.scenario_name = scenario_name
        self.version_id = version_id
        super().__init__(f"{summary}: {reason}")
```

### Project Structure Notes

**Target module location:** `src/reformlab/templates/registry.py`

**Files to create:**
```
src/reformlab/templates/
├── registry.py              # ScenarioRegistry class and related types
└── __init__.py              # Add registry exports

tests/templates/
├── test_registry.py         # Registry unit tests
└── conftest.py              # Add registry fixtures
```

**Registry file layout:**
```
~/.reformlab/registry/           # Default location (configurable)
├── french-carbon-tax-2026/
│   ├── metadata.yaml            # name, created, latest_version, versions list
│   └── versions/
│       ├── abc123def.yaml       # Immutable scenario definition
│       └── def456ghi.yaml       # New version after modification
├── progressive-dividend-reform/
│   ├── metadata.yaml
│   └── versions/
│       └── xyz789abc.yaml
```

**Metadata YAML structure:**
```yaml
name: "french-carbon-tax-2026"
created: "2026-02-27T10:30:00Z"
latest_version: "def456ghi"
versions:
  - version_id: "abc123def"
    timestamp: "2026-02-27T10:30:00Z"
    parent_version: null
    change_description: "Initial version"
  - version_id: "def456ghi"
    timestamp: "2026-02-27T14:15:00Z"
    parent_version: "abc123def"
    change_description: "Increased 2030 rate to 70 EUR/tCO2"
```

### Key Dependencies

- `pyyaml` - Already in project for YAML serialization
- `hashlib` - Standard library for SHA-256 content hashing
- `dataclasses` - Standard library for frozen dataclasses
- Story 2.1 types - `BaselineScenario`, `ReformScenario`, `dump_scenario_template`, `load_scenario_template`

### Cross-Story Dependencies

- **Hard gate (must be done first):** Story 2.1 / BKL-201 (schema types, YAML loader/dumper)
- **Soft dependency (helpful but not blocking):** Stories 2.2 / BKL-202 and 2.3 / BKL-203 provide additional real templates for integration fixtures
- **Related downstream:**
  - Story 2.5 / BKL-205: Scenario cloning and baseline/reform linking (consumes registry)
  - Story 5.1 / BKL-501: Run manifest schema references scenario version IDs from registry
  - Story 5.2 / BKL-502: Assumption capture references registry versions

### Version ID Generation Strategy

**Content-addressable hashing (required for AC-1):**
```python
import hashlib
from reformlab.templates.loader import dump_scenario_template
import io

def generate_version_id(scenario: BaselineScenario | ReformScenario) -> str:
    """Generate deterministic version ID from scenario content."""
    # Serialize to YAML string (deterministic ordering)
    buffer = io.StringIO()
    # Use internal serialization to dict, then sort keys
    content = _serialize_scenario_to_dict(scenario)
    yaml_str = yaml.dump(content, sort_keys=True)

    # Hash first 12 chars of SHA-256 for readability
    hash_bytes = hashlib.sha256(yaml_str.encode()).hexdigest()[:12]
    return hash_bytes
```

**Benefits of content-addressable IDs:**
- Same content always produces same ID (idempotent saves)
- Easy to detect duplicate saves
- Natural deduplication
- Verifiable integrity

### Registry API Design

```python
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

@dataclass(frozen=True)
class ScenarioVersion:
    """Metadata for a single scenario version."""
    version_id: str
    timestamp: datetime
    parent_version: str | None
    change_description: str

@dataclass(frozen=True)
class RegistryEntry:
    """Metadata for a scenario in the registry."""
    name: str
    created: datetime
    latest_version: str
    versions: tuple[ScenarioVersion, ...]

class ScenarioRegistry:
    """File-based scenario registry with immutable versioning."""

    def __init__(self, registry_path: Path | str | None = None) -> None:
        """Initialize registry at given path or default location."""
        ...

    def save(
        self,
        scenario: BaselineScenario | ReformScenario,
        name: str,
        change_description: str = "",
    ) -> str:
        """Save scenario to registry, returning version ID."""
        ...

    def get(
        self,
        name: str,
        version_id: str | None = None,
    ) -> BaselineScenario | ReformScenario:
        """Get scenario by name and optional version (default: latest)."""
        ...

    def list_scenarios(self) -> list[str]:
        """List all scenario names in registry."""
        ...

    def list_versions(self, name: str) -> list[ScenarioVersion]:
        """List version history for a scenario."""
        ...

    def exists(self, name: str, version_id: str | None = None) -> bool:
        """Check if scenario/version exists."""
        ...

    def get_entry(self, name: str) -> RegistryEntry:
        """Get full registry entry metadata."""
        ...
```

### Testing Standards

**From existing test patterns:**
- Use `pytest` with fixtures in `conftest.py`
- Use `tmp_path` fixture for registry directory
- Test both success and failure paths
- Error messages must include: summary, reason, fix guidance
- Test atomic-write behavior and repeated single-writer saves; multi-writer concurrency is out of scope for this story

**Key test scenarios:**
```python
def test_save_and_get_roundtrip(registry, sample_baseline):
    """Saved scenario can be retrieved identically."""
    version_id = registry.save(sample_baseline, "test-scenario")
    retrieved = registry.get("test-scenario", version_id)
    assert retrieved == sample_baseline

def test_modified_scenario_creates_new_version(registry, sample_baseline):
    """Modifying and re-saving creates new version."""
    v1 = registry.save(sample_baseline, "test-scenario")
    modified = replace(sample_baseline, description="Modified")
    v2 = registry.save(modified, "test-scenario", "Updated description")
    assert v1 != v2
    assert registry.get("test-scenario", v1) == sample_baseline
    assert registry.get("test-scenario", v2) == modified

def test_get_nonexistent_version_raises_error(registry):
    """Getting nonexistent version produces helpful error."""
    with pytest.raises(VersionNotFoundError) as exc_info:
        registry.get("test-scenario", "nonexistent123")
    assert "nonexistent123" in str(exc_info.value)
    assert "list_versions" in exc_info.value.fix
```

### Out of Scope Guardrails

- No baseline/reform linking or bidirectional navigation (Story 2.5)
- No scenario cloning workflows (Story 2.5)
- No orchestrator integration or run execution (Epic 3)
- No GUI/notebook visualization (Epic 6)
- No remote/cloud registry storage (MVP is local file-based only)
- No registry synchronization or multi-user conflict resolution

### Previous Story Learnings

**From Story 2.1:**
- Frozen dataclasses work well for immutable scenario representations
- YAML round-trip stability is critical - use `dump_scenario_template()` pattern
- Error messages with summary/reason/fix structure are helpful

**From Story 2.2 and 2.3:**
- Template packs demonstrate the need for registry: multiple variants need organized storage
- Version tracking becomes important when analysts modify shipped templates
- Content-based deduplication prevents accidental duplicate entries

**From git history:**
- Recent commits show active template development - registry will help organize this work
- Code review feedback emphasizes reproducibility - version IDs support this

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#templates/ subsystem]
- [Source: _bmad-output/planning-artifacts/architecture.md#Reproducibility & Governance]
- [Source: _bmad-output/planning-artifacts/prd.md#FR9, FR26, FR28]
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-204]
- [Source: src/reformlab/templates/schema.py - BaselineScenario, ReformScenario]
- [Source: src/reformlab/templates/loader.py - dump_scenario_template, load_scenario_template]
- [Source: src/reformlab/templates/exceptions.py - ScenarioError pattern]
- [Source: _bmad-output/implementation-artifacts/2-1-define-scenario-template-schema.md - Story 2.1 patterns]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Implemented `ScenarioRegistry` class with full CRUD operations for versioned scenario storage
- Version IDs are content-addressable (12-character SHA-256 prefix of serialized scenario)
- Scenarios are immutable: same content produces same version ID (idempotent saves)
- Modified scenarios create new versions with parent_version linking
- File-based persistence with atomic writes (temp file + replace pattern)
- Registry location configurable via `REFORMLAB_REGISTRY_PATH` env var or constructor param
- Default location: `~/.reformlab/registry/`
- Comprehensive error handling with `RegistryError`, `ScenarioNotFoundError`, `VersionNotFoundError`
- Error messages include available alternatives (list_scenarios/list_versions suggestions)
- 40 unit and integration tests covering all acceptance criteria
- All 519 project tests pass with no regressions
- Linting (ruff) and type checking (mypy) pass for new code

### File List

**New files:**
- src/reformlab/templates/registry.py
- tests/templates/test_registry.py

**Modified files:**
- src/reformlab/templates/__init__.py (added registry exports)

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-02-27 | Story implementation complete - ScenarioRegistry with immutable versioning | Claude Opus 4.5 |
