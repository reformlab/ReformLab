# Story 2.6: Add Schema Migration Helper for Template Version Changes

Status: backlog

## Story

As a **policy analyst**,
I want **a schema migration helper that upgrades older scenario payloads to the current template schema version**,
so that **I can keep using versioned scenarios safely as schema definitions evolve without breaking reproducibility guarantees**.

## Acceptance Criteria

Scope note: BKL-206 covers migration planning and execution helpers in the `templates/` subsystem only. Bulk backfills, automatic registry rewrites, and orchestration/GUI wiring are explicitly out of scope.

1. **AC-1: Migration planning for version upgrades is explicit and deterministic**
   - Given a source `schema_version` and target `schema_version`, when planning a migration, then the helper returns an ordered list of migration steps (or an explicit no-op plan).
   - Given an unsupported upgrade path, when planning, then a structured `SchemaMigrationError` explains the missing path and available versions.
   - Migration planning is deterministic for identical inputs.

2. **AC-2: Payload migration produces schema-valid upgraded output without mutating source**
   - Given a valid scenario payload on an older schema version, when migrated to a supported newer version, then the output payload validates against the target schema.
   - Migration preserves scenario semantics (policy intent and year-indexed values) except for documented structural transformations.
   - Source payload objects remain unchanged; migration returns a new upgraded payload.

3. **AC-3: Registry-compatible migration contract is provided without in-place persistence rewrite**
   - Given a registry-loaded payload with an older `schema_version`, when migration is requested, then the helper returns upgraded payload + migration metadata (`from_version`, `to_version`, `applied_steps`).
   - Migration helper does not mutate existing registry entries in place.
   - Persisting a migrated payload as a new immutable scenario version remains a caller action (Story 2.4 registry APIs).

4. **AC-4: Semantic-version guardrails are enforced (NFR21)**
   - Given a major-version upgrade path, when no explicit migration step exists, then migration fails with actionable guidance.
   - Given minor/patch upgrades with no structural differences, when migrated, then helper supports deterministic no-op or metadata-only upgrade behavior.
   - Supported migration paths and schema versions are discoverable in code (migration registry/index).

## Tasks / Subtasks

- [ ] Task 1: Define migration domain model and error contracts (AC: #1, #4)
  - [ ] 1.1 Create `src/reformlab/templates/migrations.py` with `MigrationStep`, `MigrationPlan`, and registry/index types
  - [ ] 1.2 Add `SchemaMigrationError` to `src/reformlab/templates/exceptions.py` using existing structured error style
  - [ ] 1.3 Define canonical version parsing and comparison helpers for semantic version guardrails

- [ ] Task 2: Implement migration planner and executor APIs (AC: #1, #2, #4)
  - [ ] 2.1 Implement `plan_schema_migration(source_version, target_version) -> MigrationPlan`
  - [ ] 2.2 Implement `migrate_scenario_payload(payload, target_version) -> MigratedScenarioPayload`
  - [ ] 2.3 Ensure planner/executor behavior is deterministic and side-effect free
  - [ ] 2.4 Enforce unsupported-path and major-version explicit-step rules

- [ ] Task 3: Provide integration hooks for loader/registry boundaries (AC: #2, #3)
  - [ ] 3.1 Add helper entry point callable by loader/registry code paths (no automatic persistence rewrites)
  - [ ] 3.2 Ensure upgraded payloads are compatible with schema validation and typed scenario reconstruction
  - [ ] 3.3 Return migration metadata (`from_version`, `to_version`, `applied_steps`) for governance/manifests

- [ ] Task 4: Add focused tests for migration behavior and guardrails (AC: all)
  - [ ] 4.1 Unit tests for planner path resolution and unsupported-path errors
  - [ ] 4.2 Unit tests for deterministic migration execution and no source mutation
  - [ ] 4.3 Integration tests for loader/registry-compatible upgrade flow
  - [ ] 4.4 Regression tests for major-version guardrail failures and no-op upgrade paths

- [ ] Task 5: Document migration path contracts (AC: #1, #4)
  - [ ] 5.1 Add concise module docstrings describing supported source->target schema paths
  - [ ] 5.2 Add developer notes on when to add a new migration step versus no-op mapping

## Dev Notes

### Architecture Alignment

From `architecture.md`, this story belongs to the `templates/` subsystem ("environmental policy templates ... and scenario registry with versioned definitions"). The migration helper must remain template-layer infrastructure and avoid orchestrator/computation coupling.

Key architecture constraints for this story:
- Keep work inside `src/reformlab/templates/` with schema/registry-facing contracts.
- Preserve deterministic behavior and reproducibility for version upgrades.
- Support governance readiness by returning explicit migration metadata, without implementing manifest plumbing in this story.

### Existing Code Patterns to Reuse

- Reuse structured exception style in `src/reformlab/templates/exceptions.py` (`summary - reason - fix`).
- Reuse schema loading/validation contracts from `src/reformlab/templates/loader.py`.
- Reuse canonical scenario object/payload shape from Story 2.1 and registry conventions from Story 2.4.

### Project Structure Notes

**Target module location:** `src/reformlab/templates/`

**Likely files to update/create:**
- `src/reformlab/templates/migrations.py` - Migration registry, plan, and executor
- `src/reformlab/templates/exceptions.py` - `SchemaMigrationError`
- `src/reformlab/templates/loader.py` - Optional migration hook at load boundary
- `src/reformlab/templates/registry.py` - Optional helper integration point (if Story 2.4 artifacts exist)
- `tests/templates/test_schema_migrations.py` - Migration unit and integration tests

### Cross-Story Dependencies

- **Depends on Story 2.1 / BKL-201 (required gate):** Schema types, version field conventions, and loader validation contracts.
- **Depends on Story 2.4 / BKL-204 (required gate):** Registry version metadata and immutable scenario versioning interface.
- **Related upstream stories (recommended ready):**
  - Story 2.2 / BKL-202 and Story 2.3 / BKL-203 provide realistic scenario fixtures for migration tests.
- **Related downstream stories (do not implement here):**
  - Story 2.5 / BKL-205 may consume migration helper for link/clone continuity across schema versions.
  - Story 5.1+ governance work consumes migration metadata in run manifests.
  - Story 2.7 / BKL-207 can leverage migration helper for YAML/JSON workflow compatibility.

### Out of Scope Guardrails

- No bulk rewrite/backfill of persisted registry data.
- No automatic migration-on-save that mutates existing immutable entries.
- No orchestrator behavior changes (Epic 3).
- No GUI/notebook migration UX flows (Epic 6).
- No remote data store migration framework; local template payload migration only.

### Testing Standards

- Use `pytest` with deterministic fixtures and explicit versioned payload samples.
- Validate source immutability: migration returns new payload objects.
- Validate upgraded payloads pass schema validation for target version.
- Validate major-version guardrails and actionable error messages.

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Subsystems]
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-206]
- [Source: _bmad-output/planning-artifacts/prd.md#FR9, NFR21]
- [Source: _bmad-output/implementation-artifacts/2-1-define-scenario-template-schema.md]
- [Source: _bmad-output/implementation-artifacts/2-4-build-scenario-registry.md]
