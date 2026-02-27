# Story 5.3: Implement Run Lineage Graph

Status: done

## Story

As a **policy analyst**,
I want **scenario runs to maintain explicit parent-child relationships between the parent run and its yearly child runs**,
so that **I can trace the complete execution history and understand how yearly results relate to the overall scenario run**.

## Acceptance Criteria

From backlog (BKL-503), aligned with FR29.

1. **AC-1: Parent manifest links to yearly child manifests**
   - Given a 10-year scenario run (e.g., years 2024-2033), when the parent manifest is inspected, then it contains references to all 10 yearly child manifest IDs.
   - Parent manifest includes `child_manifests: dict[int, str]` mapping year -> child manifest ID.
   - All child manifest IDs are valid UUID strings.

2. **AC-2: Child manifest links back to parent**
   - Given a yearly child manifest, when its parent is queried through lineage helpers, then the parent manifest ID is returned.
   - Each child manifest includes `parent_manifest_id: str` field containing the parent's UUID.
   - Querying a root/orphan manifest (empty `parent_manifest_id`) returns `None`, not an error.

3. **AC-3: Lineage graph query model**
   - `get_lineage(manifest: RunManifest)` returns a `LineageGraph` object with parent/children relationships.
   - `LineageGraph` provides: `parent_id`, `child_ids`, `is_root` (no parent), `is_leaf` (no children).
   - `LineageGraph` supports traversal: `get_parent()`, `get_children()`.

4. **AC-4: Lineage integrity validation**
   - Lineage links are validated bidirectionally: child's `parent_manifest_id` must match parent's `child_manifests[year]`, and parent links must resolve to provided children.
   - `validate_lineage(parent: RunManifest, children: dict[int, RunManifest])` raises `LineageIntegrityError` if any link is broken or missing.
   - Validation checks bidirectional consistency (parent->child AND child->parent).

5. **AC-5: Orchestrator integration for automatic lineage capture**
   - Lineage capture is automatic during orchestrator execution and requires zero manual user steps (NFR9).
   - A parent manifest ID is created once per run and reused for all yearly child lineage links.
   - Final run metadata includes complete `child_manifests` mapping for all completed years.

## Dependencies

- **Hard dependencies (from backlog BKL-503):**
  - Story 5-1 (BKL-501): immutable `RunManifest` schema ✅ DONE
  - Story 3-1 (BKL-301): yearly loop orchestrator output structure ✅ DONE
- **Integration dependencies (used by this story's implementation approach):**
  - Story 5-2 (BKL-502): orchestrator-boundary governance capture (`_capture_manifest_fields`) ✅ DONE
  - Story 3-6 (BKL-306): per-year execution metadata patterns ✅ DONE
- **Status source (checked 2026-02-27):**
  - `_bmad-output/implementation-artifacts/sprint-status.yaml`

- **Follow-on stories:**
  - Story 5-4 (BKL-504): Hash input/output artifacts (can use lineage for artifact tracking)
  - Story 5-5 (BKL-505): Reproducibility check harness (uses lineage for rerun verification)

## Tasks / Subtasks

- [ ] Task 0: Review prerequisite contracts and boundaries (AC: dependency check)
  - [ ] 0.1 Verify dependency statuses remain `done` in `sprint-status.yaml` for 5-1, 5-2, 3-1, 3-6
  - [ ] 0.2 Confirm BKL-503 hard dependency contract is 5-1 + 3-1, with 5-2 + 3-6 as integration dependencies
  - [ ] 0.3 Confirm this story adds lineage schema/query/validation plus runner integration only (no persistence/UI)
  - [ ] 0.4 Review `RunManifest` schema from Story 5-1 (`src/reformlab/governance/manifest.py`)
  - [ ] 0.5 Review orchestrator capture boundary from Story 5-2 (`src/reformlab/orchestrator/runner.py`)
  - [ ] 0.6 Review `OrchestratorResult` / `YearState` structures from Story 3-1 (`src/reformlab/orchestrator/types.py`)

- [ ] Task 1: Extend `RunManifest` schema for lineage fields (AC: #1-2)
  - [ ] 1.1 Add `parent_manifest_id: str` field to `RunManifest` (empty string for root manifests)
  - [ ] 1.2 Add `child_manifests: dict[int, str]` field mapping year -> child manifest ID
  - [ ] 1.3 Update `REQUIRED_JSON_FIELDS` to include new lineage fields
  - [ ] 1.4 Update `_validate()` for UUID format validation on lineage IDs (when present)
  - [ ] 1.5 Update `_normalize_mutable_fields()` to deep-copy `child_manifests`
  - [ ] 1.6 Update `from_json()` and `with_integrity_hash()` to include lineage fields

- [ ] Task 2: Implement lineage query model (AC: #2-3)
  - [ ] 2.1 Create `src/reformlab/governance/lineage.py`
  - [ ] 2.2 Define frozen `LineageGraph` dataclass with `manifest_id`, `parent_id`, `child_ids`, `is_root`, `is_leaf`
  - [ ] 2.3 Implement `get_parent() -> str | None` returning parent manifest ID or `None` for roots
  - [ ] 2.4 Implement `get_children() -> dict[int, str]` returning year -> child manifest ID mapping
  - [ ] 2.5 Implement `get_lineage(manifest: RunManifest) -> LineageGraph`

- [ ] Task 3: Implement lineage integrity validation (AC: #4)
  - [ ] 3.1 Add `LineageIntegrityError` to `src/reformlab/governance/errors.py`
  - [ ] 3.2 Implement `validate_lineage(parent: RunManifest, children: dict[int, RunManifest]) -> None` in `lineage.py`
  - [ ] 3.3 Validate parent->child consistency: `parent.child_manifests[year] == child.manifest_id`
  - [ ] 3.4 Validate child->parent consistency: `child.parent_manifest_id == parent.manifest_id`
  - [ ] 3.5 Raise `LineageIntegrityError` with actionable mismatch details

- [ ] Task 4: Wire lineage capture into orchestrator boundary (AC: #5)
  - [ ] 4.1 Update `OrchestratorRunner.run()` flow to create one parent manifest ID at run start
  - [ ] 4.2 Build yearly child lineage map from completed `OrchestratorResult.yearly_states`
  - [ ] 4.3 Update `_capture_manifest_fields()` to include lineage payload (`parent_manifest_id`, `child_manifests`)
  - [ ] 4.4 Include lineage metadata in `WorkflowResult.metadata` without manual user steps
  - [ ] 4.5 Keep capture centralized in runner boundary (no step-level scattering)

- [ ] Task 5: Export public APIs (AC: #3-4)
  - [ ] 5.1 Export `LineageGraph`, `get_lineage`, `validate_lineage` from `governance/__init__.py`
  - [ ] 5.2 Export `LineageIntegrityError` from `governance/__init__.py`

- [ ] Task 6: Tests and quality gates (AC: #1-5)
  - [ ] 6.1 Create `tests/governance/test_lineage.py`
  - [ ] 6.2 Test parent-child manifest linking (10-year projection shape)
  - [ ] 6.3 Test child-to-parent reverse lookup and root/orphan `None` behavior
  - [ ] 6.4 Test `LineageGraph` query methods and computed properties
  - [ ] 6.5 Test bidirectional lineage validation success and error detection
  - [ ] 6.6 Update `tests/governance/test_manifest.py` for new lineage fields
  - [ ] 6.7 Add orchestrator integration test for automatic lineage capture in workflow metadata
  - [ ] 6.8 Run `ruff check src/reformlab/governance tests/governance tests/orchestrator`
  - [ ] 6.9 Run `mypy src/reformlab/governance`
  - [ ] 6.10 Run targeted tests (`pytest tests/governance -v` and lineage-related orchestrator integration tests)

## Dev Notes

### Architecture Compliance

This story implements **FR29** (run lineage across yearly iterations and scenario variants).

**Key architectural constraints:**

- **Immutable manifest lineage** - All lineage fields use frozen dataclass patterns from 5-1. Parent/child links are set at construction time and never mutated. [Source: architecture.md#Reproducibility-&-Governance]
- **Bidirectional integrity** - Lineage must be verifiable in both directions. [Source: prd.md#Governance-&-Reproducibility FR29]
- **Zero manual effort** - NFR9 requires automatic lineage capture without user intervention. [Source: prd.md#Non-Functional-Requirements]
- **JSON-compatible storage** - Lineage fields must serialize to canonical JSON. [Source: 5-1 manifest implementation]

### Previous Story Intelligence

From Story 5-1 implementation (manifest schema):
- `RunManifest` is `@dataclass(frozen=True)` with `__post_init__` validation
- All mutable fields are deep-copied in `_normalize_mutable_fields()`
- Canonical JSON serialization uses `sort_keys=True, separators=(',', ':')`
- SHA-256 hash validation uses `SHA256_PATTERN` regex
- Field validation is explicit with `ManifestValidationError`

From Story 5-2 implementation (capture):
- Capture functions are in `src/reformlab/governance/capture.py`
- Orchestrator integration happens in `OrchestratorRunner._capture_manifest_fields()`
- Manifest metadata flows through `WorkflowResult.metadata`

From Story 3-1/3-6 implementation (orchestrator):
- Yearly loop in `Orchestrator.run()` produces `OrchestratorResult`
- Each year produces a `YearState` with data, seed, metadata
- `seed_log` and `step_execution_log` are captured per year
- `OrchestratorRunner.run()` bridges workflow API to orchestrator

### Existing Patterns to Follow

**Manifest field pattern** from `manifest.py`:
```python
@dataclass(frozen=True)
class RunManifest:
    # Existing fields...
    parent_manifest_id: str = ""  # Empty for root manifests
    child_manifests: dict[int, str] = field(default_factory=dict)  # year -> child manifest ID
```

**Validation pattern** for UUID fields:
```python
UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

# In _validate():
if self.parent_manifest_id and not UUID_PATTERN.match(self.parent_manifest_id):
    raise ManifestValidationError(
        f"Invalid parent_manifest_id: expected UUID format, got {self.parent_manifest_id!r}"
    )
```

**Frozen dataclass pattern** for LineageGraph:
```python
@dataclass(frozen=True)
class LineageGraph:
    """Lineage graph for a single manifest with parent/child relationships."""
    manifest_id: str
    parent_id: str | None  # None if root manifest
    child_ids: dict[int, str]  # year -> child manifest ID

    @property
    def is_root(self) -> bool:
        return self.parent_id is None

    @property
    def is_leaf(self) -> bool:
        return len(self.child_ids) == 0
```

### Module Structure

```
src/reformlab/governance/
├── __init__.py          # Add LineageGraph, get_lineage, validate_lineage exports
├── manifest.py          # Update RunManifest with parent_manifest_id, child_manifests
├── errors.py            # Add LineageIntegrityError
├── capture.py           # Existing capture helpers
└── lineage.py           # NEW: LineageGraph, get_lineage(), validate_lineage()

tests/governance/
├── __init__.py
├── conftest.py          # Add lineage test fixtures
├── test_manifest.py     # Extend for new lineage fields
├── test_capture.py      # Existing capture tests
└── test_lineage.py      # NEW: LineageGraph and validation tests
```

### Orchestrator Integration Points

**Run-boundary lineage capture flow:**
1. `OrchestratorRunner.run()` starts
2. Generate one parent lineage ID (`str(uuid.uuid4())`) for the run
3. Execute `Orchestrator.run()` and read completed years from `OrchestratorResult.yearly_states`
4. Build `child_manifests: dict[int, str]` for completed years
5. Merge lineage payload into `_capture_manifest_fields()` output
6. Include lineage payload in `WorkflowResult.metadata`

### Lineage Validation Logic

```python
def validate_lineage(
    parent: RunManifest,
    children: dict[int, RunManifest]
) -> None:
    """Validate bidirectional lineage integrity.

    Raises:
        LineageIntegrityError: If any link is broken or mismatched.
    """
    # Check parent->child links
    for year, expected_child_id in parent.child_manifests.items():
        if year not in children:
            raise LineageIntegrityError(
                f"Parent references child for year {year} but child manifest not provided"
            )
        actual_child_id = children[year].manifest_id
        if actual_child_id != expected_child_id:
            raise LineageIntegrityError(
                f"Parent's child_manifests[{year}] = {expected_child_id!r} "
                f"but child.manifest_id = {actual_child_id!r}"
            )

    # Check child->parent links
    for year, child in children.items():
        if year not in parent.child_manifests:
            raise LineageIntegrityError(
                f"Child provided for year {year} but parent.child_manifests has no entry"
            )
        if child.parent_manifest_id != parent.manifest_id:
            raise LineageIntegrityError(
                f"Child for year {year} has parent_manifest_id = {child.parent_manifest_id!r} "
                f"but expected {parent.manifest_id!r}"
            )
```

### Scope Guardrails

- **In scope:**
  - `RunManifest` schema extensions for parent_manifest_id, child_manifests
  - `LineageGraph` frozen dataclass with query methods
  - `get_lineage()` factory function
  - `validate_lineage()` integrity checker
  - `LineageIntegrityError` error class
  - Orchestrator integration for automatic lineage capture
  - Unit tests for lineage schema, query, and validation

- **Out of scope:**
  - Hashing of input/output artifacts (Story 5-4)
  - Reproducibility check harness (Story 5-5)
  - Lineage persistence/storage layer (manifests remain in-memory for MVP)
  - Lineage visualization or UI (EPIC-6)

### Testing Standards

- Mirror source structure: `tests/governance/test_lineage.py`
- Class-based test grouping: `TestLineageGraph`, `TestLineageValidation`, `TestOrchestratorLineage`
- Direct assertions with plain `assert`
- Use `pytest.raises(LineageIntegrityError, match=...)` for error tests
- Test fixtures in `tests/governance/conftest.py`

### Project Structure Notes

- **Existing governance module**: `src/reformlab/governance/` with `manifest.py`, `capture.py`, `errors.py`
- **Orchestrator integration point**: `src/reformlab/orchestrator/runner.py` `OrchestratorRunner._capture_manifest_fields()`
- **Manifest fields follow existing frozen dataclass patterns**
- **Naming**: snake_case for files, PascalCase for classes

### References

- [Source: architecture.md#Reproducibility-&-Governance] - Lineage requirements
- [Source: backlog BKL-503] - Story acceptance criteria
- [Source: prd.md#Governance-&-Reproducibility] - FR29 lineage requirement
- [Source: prd.md#Non-Functional-Requirements] - NFR9 zero manual effort
- [Source: 5-1-define-immutable-run-manifest-schema.md] - Manifest schema implementation
- [Source: 5-2-capture-assumptions-mappings-parameters.md] - Capture pattern implementation

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
