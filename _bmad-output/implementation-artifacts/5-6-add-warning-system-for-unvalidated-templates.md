# Story 5.6: Add Warning System for Unvalidated Templates

Status: ready-for-dev

## Story

As a **policy analyst or researcher**,
I want **the system to emit warnings when I use templates or configurations that haven't been validated against established benchmarks or quality criteria**,
so that **I am aware of the credibility level of my simulation outputs and can take appropriate action before relying on results for production decisions**.

## Acceptance Criteria

From backlog (BKL-506), aligned with FR27 (system emits warnings for unvalidated templates/mappings/configs).

1. **AC-1: Warning emitted for unvalidated templates in registry**
   - Given a scenario loaded from the registry where `is_validated=False` or not set, when the scenario is used in a run, then a warning is captured in the manifest's `warnings` field.
   - Warning format: `"WARNING: Scenario '<name>' (version '<version>') is not marked as validated in registry metadata. Action: Mark this scenario as validated before relying on outputs for production decisions."`
   - The warning does NOT block execution — the run proceeds with the warning recorded.

2. **AC-2: Warning emitted for unvalidated mapping configurations**
   - Given a `MappingConfig` where `is_validated=False` or not set, when used in adapter operations, then a warning is captured.
   - Warning format: `"WARNING: Mapping configuration '<source_file>' is not marked as validated. Action: Review mapping correctness before relying on outputs."`
   - Mapping warnings are accumulated with template warnings in manifest.

3. **AC-3: Warning emitted for unsupported run configurations**
   - Given a run configuration with parameters outside tested ranges (e.g., projection horizon > 30 years, population > 500k without explicit memory warning ack), when orchestrator prepares the run, then a warning is emitted.
   - Warning categories:
     - Untested projection horizon: `"WARNING: Projection horizon of N years exceeds tested range (10-20 years). Action: Results for years beyond tested range may have reduced credibility."`
     - Large population without ack: `"WARNING: Population size (N households) exceeds standard test coverage (100k). Action: Review memory usage and consider chunked processing."`

4. **AC-4: Warnings are surfaced in run manifest**
   - All captured warnings appear in `RunManifest.warnings: list[str]`.
   - Warnings are deduplicated (same warning text only appears once per manifest).
   - Warnings include actionable guidance (what to check, how to resolve).

5. **AC-5: Validation status tracking in registry**
   - `ScenarioRegistry` can store and retrieve `is_validated: bool` metadata per scenario version.
   - API: `registry.set_validated(name, version_id=None, validated=True)` and `registry.is_validated(name, version_id=None) -> bool`.
   - If `version_id=None`, both methods resolve to `metadata.get('latest_version')` before operating (mirrors existing registry method patterns).
   - Default for scenarios without explicit validation status: `is_validated=False` (conservative assumption).
   - Backward compatibility: existing registry metadata without `is_validated` field defaults to `False` via `.get("is_validated", False)`.

6. **AC-6: Warning helper functions are exported**
   - `capture_unvalidated_template_warning()` and `capture_warnings()` exist in `governance/capture.py` (from Story 5-2), but `capture_unvalidated_template_warning()` is NOT currently exported from `governance/__init__.py` — export it.
   - This story adds: `capture_unvalidated_mapping_warning()`, `capture_unsupported_config_warning()`.
   - All warning capture functions must be exported from `governance/__init__.py` and listed in `__all__`.

7. **AC-7: Integration with orchestrator**
   - `OrchestratorRunner.run()` collects warnings from:
     - Scenario validation status (via registry or scenario metadata)
     - Mapping configuration validation status
     - Run configuration parameter checks
   - Collected warnings are passed to manifest generation via `capture_warnings()`.

## Dependencies

- **Hard dependencies:**
  - Story 5-1 (BKL-501): `RunManifest` schema with `warnings: list[str]` field (DONE)
  - Story 5-2 (BKL-502): `capture_warnings()` and `capture_unvalidated_template_warning()` (DONE)
  - Story 2-4 (BKL-204): Scenario registry with versioned definitions (DONE)

- **Integration dependencies:**
  - Story 1-3 (BKL-103): `MappingConfig` structure for validation status (DONE)
  - Story 3-1 (BKL-301): `OrchestratorRunner` for warning collection point (DONE)

- **All dependencies are DONE per sprint-status.yaml**

## Tasks / Subtasks

- [ ] Task 1: Extend registry with validation status (AC: #5)
  - [ ] 1.1 Add `is_validated: bool` field to registry metadata structure
  - [ ] 1.2 Implement `ScenarioRegistry.set_validated(name, version_id, validated: bool) -> None`
  - [ ] 1.3 Implement `ScenarioRegistry.is_validated(name, version_id) -> bool` with default `False`
  - [ ] 1.4 Update `_save_metadata()` and `_load_metadata()` to handle validation status
  - [ ] 1.5 Add tests for validation status CRUD in `tests/templates/test_registry.py`

- [ ] Task 2: Add warning capture for mappings (AC: #2, #6)
  - [ ] 2.1 Add `is_validated: bool = False` field to frozen `MappingConfig` in `computation/mapping.py` (field must have default; callers use `dataclasses.replace()` to create validated copies)
  - [ ] 2.2 Create `capture_unvalidated_mapping_warning()` in `governance/capture.py`
  - [ ] 2.3 Update `capture_warnings()` to accept optional mapping config and emit mapping warning
  - [ ] 2.4 Export `capture_unvalidated_template_warning` AND new function from `governance/__init__.py` (add to imports and `__all__`)
  - [ ] 2.5 Add tests in `tests/governance/test_capture.py`

- [ ] Task 3: Add warning capture for unsupported configs (AC: #3, #6)
  - [ ] 3.1 Create `capture_unsupported_config_warning()` in `governance/capture.py`
  - [ ] 3.2 Define configuration limit constants: `TESTED_MAX_HORIZON = 20`, `TESTED_MAX_POPULATION = 100_000`
  - [ ] 3.3 Implement warning generation for horizon and population size
  - [ ] 3.4 Export new function from `governance/__init__.py`
  - [ ] 3.5 Add tests in `tests/governance/test_capture.py`

- [ ] Task 4: Integrate warnings into orchestrator (AC: #7)
  - [ ] 4.1 Update `OrchestratorRunner._capture_manifest_fields()` to collect all warning types
  - [ ] 4.2 Add validation status check: query registry or scenario metadata for `is_validated`
  - [ ] 4.3 Add mapping validation check: inspect `MappingConfig.is_validated` from adapter
  - [ ] 4.4 Add config range check: horizon years and population size validation
  - [ ] 4.5 Pass collected warnings to `capture_warnings()` with deduplication
  - [ ] 4.6 Add integration test: run with unvalidated template produces manifest with warnings

- [ ] Task 5: Update manifest capture flow (AC: #4)
  - [ ] 5.1 Add deduplication in `OrchestratorRunner._capture_manifest_fields()` via `list(dict.fromkeys(manifest_warnings))` — `capture_warnings()` does NOT deduplicate, so dedup must happen before manifest construction
  - [ ] 5.2 Verify warning format includes actionable guidance
  - [ ] 5.3 Add test: multiple warnings from different sources all appear in manifest

- [ ] Task 6: Run quality checks (AC: all)
  - [ ] 6.1 Run `ruff check src/reformlab/governance src/reformlab/templates src/reformlab/orchestrator`
  - [ ] 6.2 Run `mypy src/reformlab/governance src/reformlab/templates src/reformlab/orchestrator`
  - [ ] 6.3 Run targeted tests (`pytest tests/governance tests/templates/test_registry.py tests/orchestrator -v`)
  - [ ] 6.4 Verify all existing tests still pass

## Dev Notes

### Architecture Compliance

This story implements **FR27** (system emits warnings for unvalidated templates/mappings/configs) from the PRD.

**Key architectural constraints:**

- **Warnings don't block execution** — FR27 specifies warnings, not errors. Runs proceed with warnings recorded in manifests.
- **Frozen dataclasses** — `MappingConfig` is frozen; add `is_validated` as a construction-time field with default `False`. Callers wanting to mark as validated must use `dataclasses.replace(config, is_validated=True)` to create a new instance.
- **Governance owns warning logic** — all warning capture functions live in `governance/capture.py`, not scattered across modules.
- **Orchestrator is the integration point** — warning collection happens in `OrchestratorRunner._capture_manifest_fields()`.
- **Conservative defaults** — scenarios/mappings without explicit validation status default to `is_validated=False`.

### Existing Code to Reuse

**From `governance/capture.py` (Story 5-2):**
```python
def capture_unvalidated_template_warning(
    *,
    scenario_name: str = "",
    scenario_version: str = "",
    is_validated: bool | None = None,
) -> str | None:
    """Generate warning if template/scenario is not validated."""
    # Already implemented — returns warning string or None

def capture_warnings(
    *,
    scenario_name: str = "",
    scenario_version: str = "",
    is_validated: bool | None = None,
    additional_warnings: list[str] | None = None,
) -> list[str]:
    """Capture all warnings for manifest generation."""
    # Already implemented — consolidates warnings (but does NOT deduplicate)
```

**IMPORTANT: Current export status in `governance/__init__.py`:**
- `capture_warnings` — already exported
- `capture_unvalidated_template_warning` — EXISTS but NOT exported (must add to imports and `__all__`)

**From `templates/registry.py` (Story 2-4):**
- `RegistryEntry` — metadata structure (extend with `is_validated`)
- `ScenarioVersion` — version metadata (consider adding validation status here)
- `_save_metadata()` / `_load_metadata()` — file persistence (update for validation)

**From `computation/mapping.py` (Story 1-3):**
- `MappingConfig` — frozen dataclass with `mappings`, `source_path` (add `is_validated`)

**From `orchestrator/runner.py` (Story 3-1):**
- `OrchestratorRunner._capture_manifest_fields()` — where warnings are collected for manifest

### Implementation Pattern

```python
# governance/capture.py - Add new warning functions

def capture_unvalidated_mapping_warning(
    *,
    source_file: str = "",
    is_validated: bool | None = None,
) -> str | None:
    """Generate warning if mapping configuration is not validated.

    Args:
        source_file: Path to the mapping configuration file.
        is_validated: Whether the mapping is marked as validated.

    Returns:
        Warning message string if not validated, None otherwise.
    """
    if is_validated is True:
        return None
    normalized_source = source_file.strip() or "unknown"
    return (
        f"WARNING: Mapping configuration '{normalized_source}' is not marked as "
        "validated. Action: Review mapping correctness before relying on outputs."
    )


# Constants for tested ranges
TESTED_MAX_HORIZON_YEARS = 20
TESTED_MAX_POPULATION_SIZE = 100_000


def capture_unsupported_config_warning(
    *,
    horizon_years: int | None = None,
    population_size: int | None = None,
) -> list[str]:
    """Generate warnings for run configurations outside tested ranges.

    Args:
        horizon_years: Number of years in the projection horizon.
        population_size: Number of households in the population.

    Returns:
        List of warning strings (empty if all within tested ranges).
    """
    warnings: list[str] = []

    if horizon_years is not None and horizon_years > TESTED_MAX_HORIZON_YEARS:
        warnings.append(
            f"WARNING: Projection horizon of {horizon_years} years exceeds tested "
            f"range (10-{TESTED_MAX_HORIZON_YEARS} years). Action: Results for years "
            "beyond tested range may have reduced credibility."
        )

    if population_size is not None and population_size > TESTED_MAX_POPULATION_SIZE:
        warnings.append(
            f"WARNING: Population size ({population_size:,} households) exceeds "
            f"standard test coverage ({TESTED_MAX_POPULATION_SIZE:,}). Action: "
            "Review memory usage and consider chunked processing."
        )

    return warnings
```

### Registry Validation Status Extension

```python
# templates/registry.py - Extend metadata handling

def set_validated(
    self,
    name: str,
    version_id: str | None = None,
    *,
    validated: bool = True,
) -> None:
    """Set validation status for a scenario version.

    Args:
        name: Scenario name.
        version_id: Version ID (None = latest version).
        validated: Whether to mark as validated.

    Raises:
        ScenarioNotFoundError: If scenario doesn't exist.
        VersionNotFoundError: If version doesn't exist.
    """
    scenario_name = _validate_scenario_name(name)
    scenario_dir = self._path / scenario_name
    metadata_file = scenario_dir / "metadata.yaml"

    if not metadata_file.exists():
        raise ScenarioNotFoundError(scenario_name, self.list_scenarios())

    metadata = self._load_metadata(metadata_file)
    versions = metadata.get("versions", [])

    # Resolve version_id
    if version_id is None:
        version_id = metadata.get("latest_version")

    # Find and update the version entry
    for version in versions:
        if version.get("version_id") == version_id:
            version["is_validated"] = validated
            break
    else:
        raise VersionNotFoundError(
            scenario_name, version_id,
            [v.get("version_id", "") for v in versions]
        )

    self._save_metadata(metadata, metadata_file)


def is_validated(self, name: str, version_id: str | None = None) -> bool:
    """Check validation status for a scenario version.

    Args:
        name: Scenario name.
        version_id: Version ID (None = latest version).

    Returns:
        True if scenario version is marked as validated, False otherwise.
        Returns False for scenarios without explicit validation status.
    """
    try:
        scenario_name = _validate_scenario_name(name)
        scenario_dir = self._path / scenario_name
        metadata_file = scenario_dir / "metadata.yaml"

        if not metadata_file.exists():
            return False

        metadata = self._load_metadata(metadata_file)

        if version_id is None:
            version_id = metadata.get("latest_version")

        for version in metadata.get("versions", []):
            if version.get("version_id") == version_id:
                return version.get("is_validated", False)

        return False
    except (ScenarioNotFoundError, VersionNotFoundError):
        return False
```

### Module Structure

```
src/reformlab/
├── governance/
│   ├── __init__.py           # Add new exports
│   ├── capture.py            # Add capture_unvalidated_mapping_warning, capture_unsupported_config_warning
│   ├── manifest.py           # No changes needed
│   └── ...
├── templates/
│   ├── registry.py           # Add set_validated(), is_validated()
│   └── ...
├── computation/
│   ├── mapping.py            # Add is_validated field to MappingConfig
│   └── ...
└── orchestrator/
    └── runner.py             # Update _capture_manifest_fields() for warning collection

tests/
├── governance/
│   ├── test_capture.py       # Add tests for new warning functions
│   └── ...
├── templates/
│   └── test_registry.py      # Add tests for validation status
└── orchestrator/
    └── test_runner.py        # Add integration test for warning flow
```

### Scope Guardrails

- **In scope:**
  - Registry validation status tracking (get/set)
  - Warning capture for unvalidated mappings
  - Warning capture for unsupported config ranges
  - Orchestrator integration for warning collection
  - Manifest capture with deduplicated warnings
  - Unit and integration tests

- **Out of scope:**
  - GUI warning display (EPIC-6 scope)
  - Automated validation workflows
  - Warning severity levels (all warnings are informational)
  - Warning suppression mechanisms
  - Historical warning analysis

### Testing Standards

- Mirror source structure: `tests/governance/test_capture.py`, `tests/templates/test_registry.py`
- Class-based test grouping: `TestCaptureUnvalidatedMappingWarning`, `TestCaptureUnsupportedConfigWarning`, `TestRegistryValidationStatus`
- Use `tmp_path` fixture for registry operations
- Test warning format includes actionable guidance
- Integration test: full orchestrator run with unvalidated scenario produces warnings in manifest

### Previous Story Intelligence

From Story 5-5 (reproducibility harness):
- `capture_warnings()` is already integrated into manifest generation
- `RunManifest.warnings` field is validated on construction
- Warning strings must be non-empty (validated in `_validate()`)

From Story 5-2 (capture assumptions):
- `capture_unvalidated_template_warning()` pattern establishes the warning format
- `capture_warnings()` handles deduplication via list append (should add explicit dedup)
- Source label pattern: `normalized_name = scenario_name.strip() or "unknown"`

From Story 2-4 (registry):
- Metadata is stored in `metadata.yaml` per scenario directory
- Version entries are dictionaries in the `versions` list
- Adding fields to version entries is backward-compatible (missing keys default)

### References

- [Source: prd.md#Functional-Requirements] - FR27: System emits warnings for unvalidated templates, mappings, or unsupported run configurations
- [Source: backlog BKL-506] - Story acceptance criteria and P1 priority
- [Source: architecture.md#Reproducibility-&-Governance] - Manifest includes warnings
- [Source: governance/capture.py] - Existing warning capture implementation
- [Source: governance/manifest.py] - RunManifest.warnings field definition
- [Source: templates/registry.py] - RegistryEntry and metadata handling
- [Source: project-context.md#Critical-Implementation-Rules] - Frozen dataclasses, subsystem exceptions

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
