# Story 2.6: Add Schema Migration Helper

Status: ready-for-dev

## Story

As a **policy analyst**,
I want **to automatically migrate scenario definitions when the template schema changes**,
so that **my existing scenarios remain usable after framework upgrades without manual editing**.

## Acceptance Criteria

From backlog (BKL-206):

1. **AC-1: Detect schema version mismatch on scenario load**
   - Given a scenario with a different schema version than current, when loaded, then the system detects the version difference.
   - System compares `$schema` or `version` field against current template schema version.
   - Detection is non-blocking for backward-compatible changes (warning) and blocking for breaking changes (error with migration guidance).

2. **AC-2: Provide migration function for common schema transformations**
   - Given a scenario with an outdated schema, when migrate() is called, then fields are transformed to match the current schema.
   - Migration handles: field renames, field removals (with default fallback), new required fields (with sensible defaults), and structural changes (nested → flat, flat → nested).
   - Migration produces a new scenario object; original is never mutated.

3. **AC-3: Report migration changes for analyst review**
   - Given a migration operation, when completed, then a MigrationReport details all changes applied.
   - Report includes: fields added (with default values), fields removed, fields renamed, structural transformations, and warnings for manual review items.
   - Analyst can accept or reject the migration before saving.

4. **AC-4: Support batch migration across registry**
   - Given a registry with multiple scenarios, when batch migration is invoked, then all scenarios are analyzed and migration candidates are reported.
   - Batch migration provides a dry-run mode that reports changes without applying them.
   - Batch migration provides an apply mode that creates new versions of migrated scenarios.

## Tasks / Subtasks

- [ ] Task 0: Validate prerequisites and story boundaries
  - [ ] 0.1 Confirm Story 2.4 / BKL-204 is `done` or `review` in `sprint-status.yaml`
  - [ ] 0.2 Review `src/reformlab/templates/schema.py` for current schema structure
  - [ ] 0.3 Confirm Story 2.6 scope: migration helper only, not full schema versioning system

- [ ] Task 1: Define schema version model (AC: #1)
  - [ ] 1.1 Add `CURRENT_SCHEMA_VERSION = "1.0"` constant to schema.py
  - [ ] 1.2 Create `SchemaVersion` dataclass with major, minor, parse() classmethod
  - [ ] 1.3 Add `is_compatible(source: SchemaVersion, target: SchemaVersion) -> bool` function
  - [ ] 1.4 Add `detect_schema_version(scenario: BaselineScenario | ReformScenario) -> SchemaVersion`

- [ ] Task 2: Implement migration infrastructure (AC: #2, #3)
  - [ ] 2.1 Create `src/reformlab/templates/migration.py` module
  - [ ] 2.2 Define `MigrationChange` dataclass (change_type, field_path, old_value, new_value, reason)
  - [ ] 2.3 Define `MigrationReport` dataclass (source_version, target_version, changes, warnings, is_breaking)
  - [ ] 2.4 Define `MigrationRule` protocol (can_apply, apply, describe)
  - [ ] 2.5 Implement `MigrationEngine` class with rule registration and chained application

- [ ] Task 3: Implement common migration rules (AC: #2)
  - [ ] 3.1 `FieldRenameRule`: rename a field path across scenarios
  - [ ] 3.2 `FieldDefaultRule`: add a new field with default value
  - [ ] 3.3 `FieldRemoveRule`: remove a deprecated field (with warning)
  - [ ] 3.4 `NestedToFlatRule`: flatten nested structure to flat fields
  - [ ] 3.5 `FlatToNestedRule`: nest flat fields into structured object

- [ ] Task 4: Integrate with scenario loading (AC: #1)
  - [ ] 4.1 Add `check_schema_compatibility()` to `ScenarioRegistry.get()`
  - [ ] 4.2 Emit warning log for backward-compatible version mismatches
  - [ ] 4.3 Raise `SchemaMigrationRequiredError` for breaking mismatches with migration guidance
  - [ ] 4.4 Add `registry.migrate(name, version_id) -> tuple[Scenario, MigrationReport]` method

- [ ] Task 5: Implement batch migration (AC: #4)
  - [ ] 5.1 Add `registry.analyze_migrations() -> list[MigrationCandidate]` method
  - [ ] 5.2 Add `registry.batch_migrate(dry_run: bool) -> BatchMigrationReport` method
  - [ ] 5.3 MigrationCandidate includes: scenario_name, version_id, source_version, requires_migration, is_breaking
  - [ ] 5.4 BatchMigrationReport includes: candidates, migrated_count, skipped_count, error_count

- [ ] Task 6: Add tests for migration functionality (AC: all)
  - [ ] 6.1 Unit tests for SchemaVersion parsing and compatibility checks
  - [ ] 6.2 Unit tests for individual migration rules
  - [ ] 6.3 Unit tests for MigrationEngine rule chaining
  - [ ] 6.4 Integration tests for registry.migrate() flow
  - [ ] 6.5 Integration tests for batch migration (dry-run and apply modes)

- [ ] Task 7: Documentation and quality checks
  - [ ] 7.1 Add docstrings to all public migration API methods
  - [ ] 7.2 Run targeted `pytest tests/templates/test_migration.py`
  - [ ] 7.3 Run `ruff check` and `mypy` for touched modules

## Dev Notes

### Architecture Patterns to Follow

**From architecture.md:**
- `templates/` subsystem: Environmental policy templates and **scenario registry with versioned definitions**
- Scenario/template versioning for auditability and collaboration (Cross-Cutting Concern #5)
- FR9: System stores versioned scenario definitions in a scenario registry
- NFR21: Semantic versioning — breaking changes only on major versions

**From PRD:**
- FR9: System stores versioned scenario definitions in a scenario registry.
- NFR21: Semantic versioning — breaking changes only on major versions.
- Schema validation on load with field-level error messages.

### Existing Code Patterns to Follow

**From Story 2.4 (`src/reformlab/templates/registry.py`):**
- `ScenarioRegistry` class with content-addressable versioning
- `RegistryError` exception pattern with summary/reason/fix structure
- Atomic file operations with temp file + replace pattern
- `_scenario_to_dict_for_registry()` for serialization

**Schema versioning fields (from `schema.py`):**
```python
@dataclass(frozen=True)
class ScenarioTemplate:
    name: str
    policy_type: PolicyType
    year_schedule: YearSchedule
    parameters: PolicyParameters
    description: str = ""
    version: str = "1.0"       # Scenario version
    schema_ref: str = ""       # Schema reference (for validation)
```

**Migration module structure:**
```python
# src/reformlab/templates/migration.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Any

@dataclass(frozen=True)
class SchemaVersion:
    """Semantic version for template schemas."""
    major: int
    minor: int

    @classmethod
    def parse(cls, version_str: str) -> SchemaVersion:
        """Parse '1.0' or '1.2.3' format."""
        parts = version_str.split(".")
        return cls(major=int(parts[0]), minor=int(parts[1]) if len(parts) > 1 else 0)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}"

    def is_compatible_with(self, target: SchemaVersion) -> bool:
        """Check if this version is compatible with target (same major, <= minor)."""
        return self.major == target.major

CURRENT_SCHEMA_VERSION = SchemaVersion(major=1, minor=0)


@dataclass(frozen=True)
class MigrationChange:
    """A single change applied during migration."""
    change_type: str  # "rename", "add", "remove", "restructure"
    field_path: str   # e.g., "parameters.redistribution.type"
    old_value: Any    # Value before migration (or None for adds)
    new_value: Any    # Value after migration (or None for removes)
    reason: str       # Human-readable explanation


@dataclass(frozen=True)
class MigrationReport:
    """Report of all changes from a migration operation."""
    source_version: SchemaVersion
    target_version: SchemaVersion
    changes: tuple[MigrationChange, ...]
    warnings: tuple[str, ...]
    is_breaking: bool

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0


class MigrationRule(Protocol):
    """Protocol for migration rule implementations."""

    def can_apply(
        self,
        scenario_dict: dict[str, Any],
        source_version: SchemaVersion,
    ) -> bool:
        """Check if this rule applies to the scenario."""
        ...

    def apply(
        self,
        scenario_dict: dict[str, Any],
    ) -> tuple[dict[str, Any], list[MigrationChange]]:
        """Apply the rule and return updated dict + changes."""
        ...

    def describe(self) -> str:
        """Human-readable description of what this rule does."""
        ...
```

**MigrationEngine pattern:**
```python
class MigrationEngine:
    """Engine for applying migration rules to scenarios."""

    def __init__(self) -> None:
        self._rules: list[MigrationRule] = []

    def register_rule(self, rule: MigrationRule) -> None:
        """Register a migration rule."""
        self._rules.append(rule)

    def migrate(
        self,
        scenario: BaselineScenario | ReformScenario,
        source_version: SchemaVersion,
        target_version: SchemaVersion,
    ) -> tuple[BaselineScenario | ReformScenario, MigrationReport]:
        """Apply all applicable rules to migrate scenario."""
        scenario_dict = _scenario_to_dict_for_registry(scenario)
        changes: list[MigrationChange] = []
        warnings: list[str] = []

        for rule in self._rules:
            if rule.can_apply(scenario_dict, source_version):
                scenario_dict, rule_changes = rule.apply(scenario_dict)
                changes.extend(rule_changes)

        # Reconstruct scenario from migrated dict
        migrated = _dict_to_scenario(scenario_dict)

        is_breaking = source_version.major != target_version.major
        report = MigrationReport(
            source_version=source_version,
            target_version=target_version,
            changes=tuple(changes),
            warnings=tuple(warnings),
            is_breaking=is_breaking,
        )

        return migrated, report
```

**Error patterns:**
```python
class SchemaMigrationRequiredError(RegistryError):
    """Exception raised when a scenario requires migration before use."""

    def __init__(
        self,
        scenario_name: str,
        source_version: SchemaVersion,
        target_version: SchemaVersion,
    ) -> None:
        super().__init__(
            summary="Schema migration required",
            reason=(
                f"Scenario '{scenario_name}' uses schema {source_version}, "
                f"but current schema is {target_version}"
            ),
            fix=(
                f"Run registry.migrate('{scenario_name}') to upgrade "
                "the scenario to the current schema"
            ),
            scenario_name=scenario_name,
        )
        self.source_version = source_version
        self.target_version = target_version
```

### Project Structure Notes

**Target module location:** `src/reformlab/templates/migration.py` (new file)

**Files to create:**
```
src/reformlab/templates/
├── migration.py             # New: Migration engine, rules, and report types
```

**Files to modify:**
```
src/reformlab/templates/
├── schema.py                # Add CURRENT_SCHEMA_VERSION constant
├── registry.py              # Add migrate(), analyze_migrations(), batch_migrate()
├── __init__.py              # Export migration types

tests/templates/
├── test_migration.py        # New: Migration tests
```

### Key Dependencies

- `dataclasses` - Standard library for immutable data structures
- Story 2.4 - `ScenarioRegistry`, `RegistryError`, scenario serialization helpers
- Story 2.1 - `BaselineScenario`, `ReformScenario`, `PolicyParameters`

### Cross-Story Dependencies

- **Hard gates (must be done/review):**
  - Story 2.4 / BKL-204 (ScenarioRegistry with immutable versioning)
- **Soft dependency:** Stories 2.1-2.5 provide the template infrastructure this builds upon
- **Related downstream:**
  - Story 2.7 / BKL-207: YAML/JSON workflow configuration may need migration support
  - EPIC-7 / BKL-704: External pilot users may encounter schema changes

### Testing Standards

**From existing test patterns:**
- Use `pytest` with fixtures in `conftest.py`
- Use `tmp_path` fixture for registry directory
- Test both success and failure paths
- Error messages must include: summary, reason, fix guidance

**Key test scenarios:**
```python
def test_schema_version_parse():
    """Parse version strings correctly."""
    v = SchemaVersion.parse("1.0")
    assert v.major == 1
    assert v.minor == 0

    v2 = SchemaVersion.parse("2.3")
    assert v2.major == 2
    assert v2.minor == 3

def test_schema_version_compatibility():
    """Same major version is compatible."""
    v1_0 = SchemaVersion(1, 0)
    v1_2 = SchemaVersion(1, 2)
    v2_0 = SchemaVersion(2, 0)

    assert v1_0.is_compatible_with(v1_2)
    assert v1_2.is_compatible_with(v1_0)
    assert not v1_0.is_compatible_with(v2_0)

def test_field_rename_rule():
    """Field rename rule transforms field path."""
    rule = FieldRenameRule(
        old_path="parameters.redistribution_type",
        new_path="parameters.redistribution.type",
    )

    scenario_dict = {"parameters": {"redistribution_type": "lump_sum"}}
    result, changes = rule.apply(scenario_dict)

    assert "redistribution_type" not in result["parameters"]
    assert result["parameters"]["redistribution"]["type"] == "lump_sum"
    assert len(changes) == 1
    assert changes[0].change_type == "rename"

def test_migration_report_tracks_changes():
    """Migration report captures all applied changes."""
    engine = MigrationEngine()
    engine.register_rule(FieldRenameRule(...))
    engine.register_rule(FieldDefaultRule(...))

    migrated, report = engine.migrate(scenario, v1_0, v1_1)

    assert report.has_changes
    assert len(report.changes) >= 1
    assert not report.is_breaking

def test_batch_migration_dry_run(registry, sample_scenarios):
    """Batch migration dry-run reports candidates without changes."""
    # Save scenarios with outdated schema version
    for scenario in sample_scenarios:
        registry.save(scenario, scenario.name)

    report = registry.batch_migrate(dry_run=True)

    assert report.candidates  # Has candidates
    # Verify no actual changes were made
    for candidate in report.candidates:
        original = registry.get(candidate.scenario_name, candidate.version_id)
        # Original should be unchanged
```

### Out of Scope Guardrails

- No full schema versioning ecosystem (just migration helper utilities)
- No automatic migration on load (explicit migrate() call required)
- No GUI for migration review (Story 6.4 / EPIC-6)
- No migration persistence/history tracking (just one-time operations)
- No cross-registry migration (single registry only)

### Previous Story Learnings

**From Story 2.5:**
- `dataclasses.replace()` works well for frozen dataclass modifications
- Error messages with suggestions (list_scenarios, list_versions) are helpful
- Linear registry scan is acceptable for MVP scale (<100 scenarios)
- Bidirectional navigation patterns work cleanly

**From Story 2.4:**
- Content-addressable version IDs work well for immutability guarantees
- Atomic file operations prevent corruption
- `_scenario_to_dict_for_registry()` and `_dict_to_scenario()` provide serialization round-trip
- Version metadata (parent_version) enables lineage tracking

**From git history (recent commits):**
```
e4c4abe overnight-build: 2-5-implement-scenario-cloning — code review
2f62007 overnight-build: 2-5-implement-scenario-cloning — dev story
be08f4a overnight-build: 2-4-build-scenario-registry — code review
```
- Story 2-5 added cloning and baseline/reform navigation
- Story 2-4 established the comprehensive registry foundation

### Implementation Notes

**Schema version detection:**
Use the `version` field in scenarios for schema version detection. If `$schema` is set, parse version from that URL. Otherwise, default to `1.0` for legacy scenarios.

**Migration rule ordering:**
Rules should be applied in registration order. This allows dependent transformations to be chained correctly (e.g., rename before restructure).

**Non-breaking migrations:**
For minor version bumps (same major), migrations should be automatic and non-blocking. Add warnings to MigrationReport for analyst review.

**Breaking migrations:**
For major version bumps, raise `SchemaMigrationRequiredError` with clear guidance. Analyst must explicitly call migrate() to proceed.

**Batch migration safety:**
Batch migration creates new versions (via existing save() semantics), preserving original versions. This ensures no data loss during bulk migrations.

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#templates/ subsystem]
- [Source: _bmad-output/planning-artifacts/prd.md#FR9, NFR21]
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-206]
- [Source: src/reformlab/templates/registry.py - ScenarioRegistry class]
- [Source: src/reformlab/templates/schema.py - ScenarioTemplate, BaselineScenario, ReformScenario]
- [Source: _bmad-output/implementation-artifacts/2-5-implement-scenario-cloning.md - Story 2.5 patterns]
- [Source: _bmad-output/implementation-artifacts/2-4-build-scenario-registry.md - Story 2.4 patterns]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
