# Story 2.6: Add Schema Migration Helper

Status: review

## Story

As a **policy analyst**,
I want **a helper that upgrades older scenario schema shapes to the current template schema**,
so that **saved scenarios remain usable across template schema updates without manual YAML edits**.

## Acceptance Criteria

From backlog (BKL-206), refined for implementation scope:

1. **AC-1: Detect schema compatibility for a scenario version**
   - Given a scenario loaded from the registry, when its `version` is evaluated against the current schema version, then compatibility status is returned using semantic-version rules.
   - Same major version is treated as compatible; major mismatch is treated as breaking.
   - Detection uses existing scenario metadata (`version` and optional `$schema`) and does not introduce a new persistence format.

2. **AC-2: Provide a pure migration helper for known 1.x schema deltas**
   - Given a scenario in an older but compatible schema shape, when migration is executed, then a migrated scenario payload is returned in current schema shape.
   - Migration covers documented, deterministic transformations for existing template fields (for example, field renames and default insertion for missing optional fields).
   - Migration does not mutate the input object.

3. **AC-3: Support explicit single-scenario migration via registry workflow**
   - Given a scenario in the registry, when `migrate(...)` is called in dry-run mode, then a `MigrationReport` is returned and no new version is saved.
   - Given apply mode, when migration succeeds, then a new immutable version is saved through existing `ScenarioRegistry.save(...)` semantics.
   - Given an unsupported/breaking version gap, migration fails with a clear `RegistryError` fix message.

## Tasks / Subtasks

- [x] Task 0: Validate prerequisites and boundaries
  - [x] 0.1 Confirm Story 2.1 (schema/loader) and Story 2.4 (registry) are `done` or `review` in `_bmad-output/implementation-artifacts/sprint-status.yaml`
  - [x] 0.2 Confirm existing schema-version sources in `src/reformlab/templates/loader.py` (`SCHEMA_VERSION`, `validate_schema_version`) before adding new constants
  - [x] 0.3 Confirm this story is limited to helper utilities + single-scenario registry flow (no batch migration system)

- [x] Task 1: Define migration contract and compatibility check (AC: #1)
  - [x] 1.1 Create `src/reformlab/templates/migration.py`
  - [x] 1.2 Add `SchemaVersion` parser/comparator and `check_compatibility(source, target)`
  - [x] 1.3 Add immutable report types: `MigrationChange`, `MigrationReport`
  - [x] 1.4 Reuse `loader.SCHEMA_VERSION` as the default target version to avoid version-source duplication

- [x] Task 2: Implement deterministic migration helper (AC: #2)
  - [x] 2.1 Implement `migrate_scenario_dict(...)` as a pure function over serialized scenario dicts
  - [x] 2.2 Implement a minimal rule set for known schema deltas in current templates (rename/default/shape normalization)
  - [x] 2.3 Return detailed change log entries in `MigrationReport` (field path, old value, new value, reason)
  - [x] 2.4 Return explicit compatibility/migration-required warnings for analyst review

- [x] Task 3: Integrate explicit migration with `ScenarioRegistry` (AC: #3)
  - [x] 3.1 Add `ScenarioRegistry.migrate(name: str, version_id: str | None = None, *, dry_run: bool = True)`
  - [x] 3.2 Use existing registry serialization path (`_scenario_to_dict_for_registry` and `_dict_to_scenario`) for round-trip safety
  - [x] 3.3 In apply mode, persist migrated scenario as a new version with clear lineage `change_description`
  - [x] 3.4 Keep `ScenarioRegistry.get(...)` behavior non-mutating and non-auto-migrating in this story

- [x] Task 4: Add tests for migration behavior (AC: all)
  - [x] 4.1 Unit tests for semantic-version compatibility logic
  - [x] 4.2 Unit tests for each implemented migration rule and immutability guarantee
  - [x] 4.3 Integration tests for `ScenarioRegistry.migrate(...)` dry-run and apply paths
  - [x] 4.4 Error-path tests for breaking major-version mismatch (`RegistryError` with actionable fix)

- [x] Task 5: Documentation and quality checks
  - [x] 5.1 Export migration APIs in `src/reformlab/templates/__init__.py`
  - [x] 5.2 Add docstrings for public migration APIs and report fields
  - [x] 5.3 Run targeted tests (`pytest tests/templates/test_migration.py tests/templates/test_registry.py`)
  - [x] 5.4 Run `ruff check` and `mypy` on touched modules

## Dev Notes

### Architecture Alignment

**From architecture.md:**
- `templates/` subsystem owns scenario templates and versioned registry definitions.
- Cross-cutting concern: scenario/template versioning supports auditability and collaboration.
- NFR21 requires semantic-version handling, with breaking changes represented by major versions.

This story aligns by adding a migration helper around existing template/registry primitives, without expanding into a new subsystem.

### Existing Code Patterns to Reuse

- `src/reformlab/templates/loader.py`
  - `SCHEMA_VERSION = "1.0"`
  - `validate_schema_version(...)` already enforces major-version compatibility behavior.
- `src/reformlab/templates/registry.py`
  - `RegistryError` pattern (`summary`, `reason`, `fix`)
  - `_scenario_to_dict_for_registry(...)` and `_dict_to_scenario(...)` for stable round-trips
  - immutable version persistence via `save(...)`

### Project Structure Notes

**New file:**
- `src/reformlab/templates/migration.py`

**Files to modify:**
- `src/reformlab/templates/registry.py` (single-scenario migrate workflow)
- `src/reformlab/templates/__init__.py` (exports)
- `tests/templates/test_migration.py` (new)
- `tests/templates/test_registry.py` (migration integration coverage)

### Key Dependencies

- Story 2.1 / BKL-201: scenario schema dataclasses and loader semantics
- Story 2.4 / BKL-204: immutable scenario registry and serialization helpers
- Standard library: `dataclasses`, `typing`, `copy`

### Cross-Story Dependencies

- **Hard gates (must be done/review):**
  - Story 2.1 / BKL-201
  - Story 2.4 / BKL-204
- **Related but non-blocking:**
  - Story 2.5 / BKL-205 (clone/link APIs can consume migrated versions but are not required to implement this story)
  - Story 2.7 / BKL-207 (workflow config validation may later reuse migration helper)

### Out-of-Scope Guardrails

- No batch migration API (`analyze_migrations`, `batch_migrate`) in this story
- No automatic migration on read/load paths
- No GUI migration review workflow
- No migration-history subsystem beyond normal registry version lineage

### Testing Standards

- Use `pytest` and existing template fixtures
- Cover success and failure paths
- Assert `RegistryError` messages include clear fix guidance
- Verify dry-run mode has no persistence side effects

### References

- [Source: _bmad-output/planning-artifacts/architecture.md]
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-206]
- [Source: src/reformlab/templates/loader.py]
- [Source: src/reformlab/templates/registry.py]
- [Source: _bmad-output/implementation-artifacts/sprint-status.yaml]
- [Source: _bmad-output/implementation-artifacts/2-4-build-scenario-registry.md]
- [Source: _bmad-output/implementation-artifacts/2-5-implement-scenario-cloning.md]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

No debug issues encountered.

### Completion Notes List

- Implemented SchemaVersion parser with major.minor comparison and ordering
- Implemented CompatibilityStatus enum with COMPATIBLE, MIGRATION_AVAILABLE, BREAKING states
- Implemented check_compatibility() for semantic version compatibility checks
- Implemented MigrationChange and MigrationReport immutable dataclasses
- Implemented migrate_scenario_dict() pure function that does not mutate input
- Integrated ScenarioRegistry.migrate() method with dry_run and apply modes
- Migration uses existing registry serialization path for round-trip safety
- Applied ruff formatting fixes for import sorting and line length
- All 104 migration/registry tests pass, 583 total tests pass

### File List

**New files:**
- src/reformlab/templates/migration.py
- tests/templates/test_migration.py

**Modified files:**
- src/reformlab/templates/registry.py (added migrate method, import for migration module)
- src/reformlab/templates/__init__.py (exported migration APIs)
- tests/templates/test_registry.py (added TestMigrate class with 8 tests)

### Change Log

- 2026-02-27: Implemented schema migration helper (Story 2.6)
  - Added migration.py with SchemaVersion, CompatibilityStatus, check_compatibility, migrate_scenario_dict
  - Added ScenarioRegistry.migrate() method for dry-run and apply migration workflows
  - Exported migration APIs in __init__.py
  - Added 31 tests for migration functionality
