# Story 2.4: Build Scenario Registry with Immutable Version IDs

Status: backlog

## Story

As a **policy analyst**,
I want **a scenario registry that stores immutable, versioned scenario definitions**,
so that **I can reliably retrieve exact scenario versions for reproducible comparisons and downstream manifest pinning**.

## Acceptance Criteria

Scope note: BKL-204 covers local scenario registry persistence, immutable version IDs, retrieval, and version history APIs. Cloning workflows, schema migration, and run-manifest wiring are explicitly out of scope for this story.

1. **AC-1: Save and retrieve immutable scenario versions**
   - Given a validated baseline or reform scenario, when saved to the registry, then a deterministic immutable `version_id` is returned.
   - Given a `version_id`, when retrieved, then the returned scenario definition is byte-equivalent to the stored canonical payload.
   - Registry metadata includes at least: `version_id`, `scenario_name`, `policy_type`, `template_version`, `schema_version`, `content_hash`, and `created_at`.

2. **AC-2: Append-only version history**
   - Given an existing scenario saved in the registry, when parameters are modified and saved again, then a new `version_id` is generated.
   - The previous version remains retrievable and unchanged.
   - Registry writes are append-only; existing entries cannot be mutated in place.

3. **AC-3: Query and error behavior**
   - Given an invalid or unknown `version_id`, when queried, then a structured `ScenarioRegistryError` clearly reports that the version does not exist and how to inspect available versions.
   - Given a scenario name, when listing versions, then results are returned in deterministic newest-first order.
   - Duplicate save attempts of identical canonical content return the existing `version_id` without duplicating entries.

4. **AC-4: Governance-ready output contract**
   - Registry can export machine-readable metadata for manifest consumption (`to_dict()` or equivalent JSON-compatible structure).
   - Exported entries are stable across repeated loads/saves (deterministic ordering and field names).
   - Contract supports FR28 readiness by exposing `scenario_version_id` for downstream run pinning (actual run-manifest integration is out of scope).

## Tasks / Subtasks

- [ ] Task 1: Define registry domain model and IDs (AC: #1, #2, #4)
  - [ ] 1.1 Create immutable `ScenarioRegistryEntry` dataclass in `src/reformlab/templates/registry.py`
  - [ ] 1.2 Implement canonical scenario serialization (sorted keys, normalized year keys, stable numeric representation)
  - [ ] 1.3 Implement deterministic `version_id` generation from canonical content hash (SHA-256 prefix or equivalent documented format)
  - [ ] 1.4 Add `ScenarioRegistryError` exception following existing structured error style in `templates/exceptions.py`

- [ ] Task 2: Implement append-only registry storage (AC: #1, #2, #3)
  - [ ] 2.1 Create local JSON-backed store module `src/reformlab/templates/registry_store.py`
  - [ ] 2.2 Implement `save(entry)` with append-only semantics and duplicate-content dedup behavior
  - [ ] 2.3 Implement `get(version_id)`, `list_versions(scenario_name)`, and `all()` retrieval methods
  - [ ] 2.4 Ensure deterministic on-disk ordering for reproducible diffs

- [ ] Task 3: Implement public registry API for template scenarios (AC: #1, #3, #4)
  - [ ] 3.1 Add `ScenarioRegistry` service in `src/reformlab/templates/registry.py`
  - [ ] 3.2 Implement `register_scenario(scenario) -> version_id` for `BaselineScenario | ReformScenario`
  - [ ] 3.3 Implement `load_scenario_version(version_id) -> BaselineScenario | ReformScenario`
  - [ ] 3.4 Implement `export_metadata() -> dict[str, Any]` for governance consumers

- [ ] Task 4: Integrate with templates package surface (AC: #1, #3)
  - [ ] 4.1 Export registry API symbols via `src/reformlab/templates/__init__.py`
  - [ ] 4.2 Add concise docstrings/examples showing registry usage with `load_scenario_template()` and template packs
  - [ ] 4.3 Preserve backward compatibility for existing template APIs

- [ ] Task 5: Add focused tests for immutability and retrieval contracts (AC: all)
  - [ ] 5.1 Unit tests for canonicalization and deterministic `version_id` generation
  - [ ] 5.2 Unit tests for append-only behavior and duplicate-content dedup
  - [ ] 5.3 Integration tests for register/retrieve round-trip with baseline and reform scenarios
  - [ ] 5.4 Error-path tests for unknown `version_id` and malformed store data
  - [ ] 5.5 Persistence tests validating deterministic JSON output and newest-first list ordering

## Dev Notes

### Architecture Alignment

From `architecture.md`, scenario registry belongs in the `templates/` subsystem as part of "environmental policy templates ... and scenario registry with versioned definitions." This story must stay within template-layer concerns and provide contracts consumed later by governance/manifests.

### Existing Code Patterns to Reuse

- Reuse structured error/message style from `src/reformlab/templates/exceptions.py` (`summary - reason - fix` semantics).
- Reuse deterministic hash and registry concepts from `src/reformlab/data/pipeline.py`:
  - content hash generation (`sha256`)
  - append-only registry semantics
  - JSON-compatible `to_dict()` export pattern
- Reuse typed scenario serialization from `dump_scenario_template()` / `_scenario_to_dict()` in `src/reformlab/templates/loader.py` for canonical payload generation.

### Project Structure Notes

**Target module location:** `src/reformlab/templates/`

**Files to create:**
- `src/reformlab/templates/registry.py` - Entry types, service API, deterministic ID logic
- `src/reformlab/templates/registry_store.py` - JSON-backed persistence helpers
- `tests/templates/test_registry.py` - Unit tests for IDs, errors, behavior
- `tests/templates/test_registry_persistence.py` - Integration tests for on-disk persistence

### Cross-Story Dependencies

- **Depends on Story 2.1 / BKL-201 (required gate):** Registry stores/reconstructs typed `BaselineScenario` and `ReformScenario` objects from schema-compliant payloads.
- **Depends on Story 1.4 / BKL-104 (pattern dependency):** Follow dataset registry/hash conventions for append-only behavior and deterministic serialization.
- **Related upstream stories (recommended ready):**
  - Story 2.2 / BKL-202 and Story 2.3 / BKL-203 provide real template fixtures for integration tests.
- **Related downstream stories (do not implement here):**
  - Story 2.5 / BKL-205 uses registry IDs for cloning and baseline/reform navigation.
  - Story 2.6 / BKL-206 handles schema migration/version upgrade paths.
  - Epic 5 manifest work consumes `scenario_version_id` for run pinning (FR28).

### Out of Scope Guardrails

- No scenario cloning behavior or bidirectional link traversal (Story 2.5).
- No schema migration/up-conversion tooling (Story 2.6).
- No orchestrator integration or runtime execution changes (Epic 3).
- No GUI or notebook workflow wiring (Epic 6).
- No remote DB backend; local filesystem JSON store only for this story.

### Testing Standards

- Use `pytest` with `tmp_path` fixtures for isolated registry files.
- Cover both baseline and reform scenarios in round-trip tests.
- Validate deterministic IDs across repeated loads/saves.
- Validate append-only guarantees: prior versions remain unchanged and accessible.

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Subsystems]
- [Source: _bmad-output/planning-artifacts/prd.md#FR9, FR28]
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-204]
- [Source: src/reformlab/templates/loader.py]
- [Source: src/reformlab/data/pipeline.py]
