# Story 2.5: Implement Scenario Cloning and Baseline/Reform Linking

Status: backlog

## Story

As a **policy analyst**,
I want **to clone scenarios and navigate baseline/reform links in both directions**,
so that **I can create variant reforms quickly without mutating prior versions and keep scenario lineage clear for comparison workflows**.

## Acceptance Criteria

Scope note: BKL-205 covers registry-level cloning and bidirectional baseline/reform link navigation only. GUI flows, orchestrator execution, and manifest wiring are explicitly out of scope.

1. **AC-1: Clone creates a new immutable scenario version**
   - Given a stored baseline or reform scenario `version_id`, when cloned, then a new `version_id` is returned.
   - The clone payload is content-equivalent to the source scenario except for clone metadata fields (`version_id`, `created_at`, and optional `source_version_id`/`clone_of`).
   - Cloning is append-only and never mutates the source registry entry.

2. **AC-2: Baseline/reform links are navigable in both directions**
   - Given a reform scenario linked to a baseline, when loading the reform, then baseline linkage metadata is resolvable (`baseline_version_id` or equivalent canonical link).
   - Given a baseline scenario, when querying linked reforms, then all directly linked reform versions are returned in deterministic order.
   - Link resolution is deterministic and survives registry reload/restart.

3. **AC-3: Editing a cloned scenario does not alter the original**
   - Given a cloned scenario, when parameters are modified and re-saved, then a new `version_id` is generated for the edited clone.
   - The original source scenario and the intermediate clone version remain retrievable and byte-equivalent to their original stored canonical payloads.
   - Registry history remains append-only across clone and post-clone edits.

4. **AC-4: Structured errors for invalid link/clone operations**
   - Given an unknown source `version_id`, when clone is requested, then `ScenarioRegistryError` clearly identifies missing source version and remediation.
   - Given a reform with missing baseline reference, when link traversal is requested, then a structured error identifies the broken link.
   - Given cyclic or self-referential links in persisted data, when validated/loaded, then registry rejects the entry with actionable diagnostics.

## Tasks / Subtasks

- [ ] Task 1: Define cloning and link domain contracts (AC: #1, #2, #4)
  - [ ] 1.1 Extend `ScenarioRegistryEntry` metadata model in `src/reformlab/templates/registry.py` with canonical clone/link fields (`clone_of`, `baseline_version_id`, `scenario_kind`)
  - [ ] 1.2 Define deterministic ordering/selection contract for `list_linked_reforms(baseline_version_id)`
  - [ ] 1.3 Add invariant validation helpers for broken/cyclic/self links

- [ ] Task 2: Implement clone workflow in registry service (AC: #1, #3, #4)
  - [ ] 2.1 Add `clone_scenario(source_version_id: str, *, new_name: str | None = None) -> str` to `ScenarioRegistry`
  - [ ] 2.2 Reuse canonical serialization + deterministic ID generation from Story 2.4 (no ad-hoc copy logic)
  - [ ] 2.3 Ensure clone metadata is persisted while preserving canonical payload immutability guarantees
  - [ ] 2.4 Raise structured errors for unknown source version IDs

- [ ] Task 3: Implement bidirectional link traversal APIs (AC: #2, #4)
  - [ ] 3.1 Add `get_baseline_for_reform(reform_version_id: str) -> BaselineScenario`
  - [ ] 3.2 Add `list_linked_reforms(baseline_version_id: str) -> list[ReformScenario]`
  - [ ] 3.3 Persist/rebuild link index deterministically in local JSON store (`src/reformlab/templates/registry_store.py`)
  - [ ] 3.4 Validate link integrity on load/save boundaries

- [ ] Task 4: Package and contract surface updates (AC: #1, #2)
  - [ ] 4.1 Export new clone/link APIs via `src/reformlab/templates/__init__.py`
  - [ ] 4.2 Add concise docstrings and examples for clone + bidirectional navigation
  - [ ] 4.3 Preserve backward compatibility for existing registry APIs from Story 2.4

- [ ] Task 5: Add focused test coverage for clone/link invariants (AC: all)
  - [ ] 5.1 Unit tests for clone immutability and deterministic metadata behavior
  - [ ] 5.2 Integration tests for baseline->reforms and reform->baseline traversal across persisted reloads
  - [ ] 5.3 Regression tests verifying clone edit flows keep source versions unchanged
  - [ ] 5.4 Error-path tests for missing source IDs, broken links, and cyclic/self links

## Dev Notes

### Architecture Alignment

From `architecture.md`, this work belongs to the `templates/` subsystem ("scenario registry with versioned definitions") and must remain independent from orchestrator internals. Cloning and link traversal are registry capabilities layered above schema validation and below orchestration execution.

Relevant architecture constraints:
- Keep computation and orchestrator layers untouched (`computation/`, `orchestrator/`, `vintage/` are out of scope).
- Maintain deterministic behavior and reproducibility in registry operations.
- Preserve adapter/governance boundaries: this story exposes clone/link metadata but does not implement run-manifest integration.

### Existing Code Patterns to Reuse

- Reuse `ScenarioRegistryError` structured error format from `src/reformlab/templates/exceptions.py`.
- Reuse canonical scenario serialization and deterministic `version_id` generation from Story 2.4 (`src/reformlab/templates/registry.py` / `registry_store.py`).
- Reuse schema-level baseline/reform structure from Story 2.1 types and loader contracts.

### Project Structure Notes

**Target module location:** `src/reformlab/templates/`

**Likely files to update:**
- `src/reformlab/templates/registry.py` - Clone/link service APIs and invariants
- `src/reformlab/templates/registry_store.py` - Persistence and link index mechanics
- `src/reformlab/templates/__init__.py` - Public API exports
- `tests/templates/test_registry.py` - Unit behavior tests
- `tests/templates/test_registry_persistence.py` - Persistence and traversal tests

### Cross-Story Dependencies

- **Depends on Story 2.1 / BKL-201 (required gate):** Typed baseline/reform schema and baseline linkage fields must exist.
- **Depends on Story 2.4 / BKL-204 (required gate):** Clone/link behavior extends immutable versioned registry capabilities.
- **Related upstream stories (recommended ready):**
  - Story 2.2 / BKL-202 and Story 2.3 / BKL-203 provide realistic template fixtures for clone/link tests.
- **Related downstream stories (do not implement here):**
  - Story 2.6 / BKL-206 handles schema migration and upgrade tooling.
  - Story 5.1+ (governance) consumes scenario lineage metadata for manifests.
  - Story 6.4 / BKL-604 uses clone/link APIs in the early no-code GUI flow.

### Out of Scope Guardrails

- No GUI UX implementation for clone actions (Epic 6).
- No orchestrator run execution changes (Epic 3).
- No run-manifest lineage graph implementation (Epic 5).
- No schema migration/backfill tooling for historical registry records (Story 2.6).
- No remote DB backend; keep local JSON-backed registry for MVP.

### Testing Standards

- Use `pytest` with `tmp_path` fixtures for isolated registry persistence tests.
- Assert append-only history across clone and clone-edit operations.
- Assert deterministic ordering for linked reform listings.
- Include negative tests for broken link graphs and unknown IDs.

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Subsystems]
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-205]
- [Source: _bmad-output/planning-artifacts/prd.md#FR8, FR9, FR28, FR32]
- [Source: _bmad-output/implementation-artifacts/2-1-define-scenario-template-schema.md]
- [Source: _bmad-output/implementation-artifacts/2-4-build-scenario-registry.md]
