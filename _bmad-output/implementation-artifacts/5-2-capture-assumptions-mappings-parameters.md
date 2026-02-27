# Story 5.2: Capture Assumptions/Mappings/Parameters in Manifests

Status: ready-for-dev

## Story

As a **policy analyst**,
I want **all assumptions, mappings, and parameter configurations to be automatically captured in run manifests at execution time**,
so that **I can audit the exact methodology used in any simulation and reproduce it with identical results**.

## Acceptance Criteria

From backlog (BKL-502), aligned with FR26 and FR27.

1. **AC-1: Assumption capture in manifests**
   - Given a run with defaults and user overrides, when the manifest is inspected, then `assumptions` contains structured entries for each captured assumption.
   - Each assumption entry includes: `key`, `value`, `source`, and `is_default`.
   - Assumption entries are JSON-serializable and include non-empty `key` and `source` values.

2. **AC-2: Mapping configuration capture**
   - Given an OpenFisca mapping configuration from Story 1-3, when the run completes, then the manifest includes `mappings` capturing the mapping used at execution time.
   - Mapping capture includes: OpenFisca variable name, project field name, direction, and source mapping file path when available.
   - If a transform is configured in the mapping layer, the transform identifier is included in captured mapping metadata.

3. **AC-3: Parameter snapshot capture**
   - Given a scenario with policy parameters, when manifest capture occurs, then the manifest contains a complete parameter snapshot as it existed at capture time.
   - Parameter snapshot is a deep copy and detached from source objects; mutating source configuration after capture does not modify manifest content.

4. **AC-4: Unvalidated template warning flag**
   - Given a run where the scenario/template is not marked validated in registry metadata (or validation metadata is missing), when the manifest is generated, then `warnings` includes an actionable warning.
   - Warning includes scenario/template identifier and version identifier where available.

5. **AC-5: Orchestrator integration for automatic capture**
   - Manifest assumption/mapping/parameter/warning capture is automatic during orchestrator execution and requires zero manual user steps (NFR9).
   - Capture is wired at the orchestrator boundary (`src/reformlab/orchestrator/runner.py` flow), not scattered across adapter/step modules.

## Dependencies

- **Required prior stories:**
  - Story 5-1 (BKL-501): `RunManifest` schema with `assumptions`, `parameters`, and `integrity_hash` fields ✅ DONE
  - Story 1-3 (BKL-103): Input/output mapping configuration ✅ DONE
  - Story 2-1 (BKL-201): Scenario template schema with parameters ✅ DONE
  - Story 2-4 (BKL-204): Scenario registry with version IDs ✅ DONE
  - Story 3-1 (BKL-301): Orchestrator that runs yearly loop ✅ DONE
  - Story 3-6 (BKL-306): Seed logging in orchestrator ✅ DONE
  - Status source: `_bmad-output/implementation-artifacts/sprint-status.yaml` (checked 2026-02-27)

- **Dependency note (validation metadata):**
  - Story 2-4 provides scenario versioning, but does not guarantee an explicit "validated" boolean in registry metadata.
  - This story should treat missing validation metadata as "not validated" and emit warning text; richer validation lifecycle remains in Story 5-6.

- **Follow-on stories:**
  - Story 5-3 (BKL-503): Run lineage graph using manifest links
  - Story 5-4 (BKL-504): Hash input/output artifacts and store in manifest
  - Story 5-5 (BKL-505): Reproducibility check harness consuming manifests
  - Story 5-6 (BKL-506): Warning system for unvalidated templates

## Tasks / Subtasks

- [ ] Task 0: Review prerequisite contracts and boundaries (AC: dependency check)
  - [ ] 0.1 Review `RunManifest` schema from Story 5-1 (`src/reformlab/governance/manifest.py`)
  - [ ] 0.2 Review mapping configuration patterns from Story 1-3 (`src/reformlab/computation/mapping.py`)
  - [ ] 0.3 Review scenario template parameter structure from Story 2-1 (`src/reformlab/templates/`)
  - [ ] 0.4 Review orchestrator execution flow from Story 3-1 (`src/reformlab/orchestrator/runner.py`)
  - [ ] 0.5 Confirm this story captures at the orchestrator boundary and does not create new adapter-side capture responsibilities

- [ ] Task 1: Extend `RunManifest` schema for capture payloads (AC: #1-4)
  - [ ] 1.1 Update `src/reformlab/governance/manifest.py` to support structured `assumptions` entries (key/value/source/is_default)
  - [ ] 1.2 Add `mappings` field to `RunManifest` and validation rules for JSON-compatible payload
  - [ ] 1.3 Add `warnings: list[str]` field and validation for non-empty warning strings
  - [ ] 1.4 Update canonical serialization/deserialization required-field handling (`REQUIRED_JSON_FIELDS`)

- [ ] Task 2: Implement governance capture helpers (AC: #1-3)
  - [ ] 2.1 Create `src/reformlab/governance/capture.py`
  - [ ] 2.2 Implement `capture_assumptions(...)` returning structured assumption entries
  - [ ] 2.3 Implement `capture_mappings(...)` from `MappingConfig` data used at runtime
  - [ ] 2.4 Implement `capture_parameters(...)` using deep copy and JSON-compatibility checks
  - [ ] 2.5 Export capture APIs from `src/reformlab/governance/__init__.py` if part of public surface

- [ ] Task 3: Implement minimal unvalidated-template warning behavior (AC: #4)
  - [ ] 3.1 Add helper that derives validation warning from scenario registry metadata
  - [ ] 3.2 Treat missing validation metadata as "not validated" for warning purposes in this story
  - [ ] 3.3 Use actionable warning format with scenario/template identifier (without implementing the full warning framework from Story 5-6)

- [ ] Task 4: Wire capture into orchestrator execution (AC: #5)
  - [ ] 4.1 Identify current manifest construction point in orchestrator/workflow execution path
  - [ ] 4.2 Invoke capture helpers once per run at orchestrator boundary before final manifest creation
  - [ ] 4.3 Ensure captured values come from actual runtime config objects (scenario, mapping, registry metadata)
  - [ ] 4.4 Ensure no manual user step is required to trigger capture

- [ ] Task 5: Tests and quality gates (AC: #1-5)
  - [ ] 5.1 Add `tests/governance/test_capture.py` for assumption/mapping/parameter capture behavior
  - [ ] 5.2 Update `tests/governance/test_manifest.py` for new `mappings` and `warnings` fields
  - [ ] 5.3 Add orchestrator integration test ensuring capture fields are present in produced manifest payload
  - [ ] 5.4 Test parameter snapshot detachment (source mutation does not alter captured manifest value)
  - [ ] 5.5 Test warning generation when validation metadata is false/missing
  - [ ] 5.6 Run `ruff check src/reformlab/governance tests/governance`
  - [ ] 5.7 Run `mypy src/reformlab/governance`
  - [ ] 5.8 Run targeted tests (`pytest tests/governance -v` and orchestrator integration test)

## Dev Notes

### Architecture Compliance

This story implements **FR26** (analyst can inspect assumptions and mappings used in any run) and **FR27** (system emits warnings for unvalidated templates).

**Key architectural constraints:**

- **Immutable capture payloads** - Captured assumptions/mappings/parameters must not retain mutable references to runtime config objects. Use frozen types and/or deep-copied JSON-compatible structures. [Source: project-context.md#Critical-Implementation-Rules]
- **Single point of capture** - All captures happen at orchestrator layer, not scattered across subsystems. [Source: architecture.md#Step-Pluggable-Dynamic-Orchestrator]
- **Zero manual effort** - NFR9 requires automatic manifest generation without user intervention. [Source: prd.md#Non-Functional-Requirements]
- **JSON-compatible storage** - All captured data must serialize to canonical JSON for manifest storage. [Source: 5-1 manifest implementation]

### Previous Story Intelligence

From Story 5-1 implementation:

- `RunManifest` already has `assumptions: list[str]` and `parameters: dict[str, Any]` fields
- The current `assumptions` field is a simple list of strings — may need to be enriched to `list[dict]` or custom type
- The current `parameters` field accepts `dict[str, Any]` — already suitable for parameter snapshot
- Manifest validation uses `_validate_json_compatible()` for nested dict/list validation
- Pattern to follow: define types in separate module, import into manifest.py, update validation

Files created in 5-1:
- `src/reformlab/governance/errors.py` - Error classes
- `src/reformlab/governance/manifest.py` - RunManifest schema
- `tests/governance/conftest.py` - Test fixtures
- `tests/governance/test_manifest.py` - Test suite

### Existing Patterns to Follow

**Manifest field pattern** from `manifest.py`:

```python
@dataclass(frozen=True)
class RunManifest:
    ...
    parameters: dict[str, Any] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)
    step_pipeline: list[str] = field(default_factory=list)
    integrity_hash: str = ""
```

**Validation pattern** from `manifest.py`:

```python
def _validate(self) -> None:
    if not isinstance(self.parameters, dict):
        raise ManifestValidationError("Field 'parameters' must be a dictionary")
    _validate_json_compatible(self.parameters, "parameters")

    if not isinstance(self.assumptions, list):
        raise ManifestValidationError("Field 'assumptions' must be a list")
    # validate list contents...
```

For this story, extend this validation approach to structured assumptions and the new `mappings` / `warnings` fields.

### Module Structure (Updated)

```
src/reformlab/governance/
├── __init__.py          # Add new exports
├── manifest.py          # Update RunManifest with new fields
├── errors.py            # Existing errors
└── capture.py           # NEW: capture_assumptions(), capture_mappings(), capture_parameters(), capture_warnings()

tests/governance/
├── __init__.py
├── conftest.py          # Existing fixtures
├── test_manifest.py     # Extend for new schema fields
└── test_capture.py      # NEW: Capture behavior tests
```

### Orchestrator Integration Points

Based on architecture.md, the orchestrator runs:
1. ComputationAdapter call per year
2. Environmental policy templates
3. Transition steps (vintage, carry-forward)
4. Record year-t results

Capture logic for this story should execute once per run in the orchestrator/workflow boundary, before final `RunManifest` materialization, capturing:
- Scenario parameters (from scenario/template objects)
- Variable mappings (from mapping config used at runtime)
- Assumption overrides/defaults (from effective runtime config)
- Template validation warning inputs (from registry metadata)

### Warning Message Format

For unvalidated templates/scenarios (AC-4):
```
WARNING: Scenario '<scenario_name>' (version '<scenario_version>') is not marked as validated in registry metadata.
Action: Mark this scenario as validated before relying on outputs for production decisions.
```

### Scope Guardrails

- **In scope:**
  - Structured assumption capture payloads
  - Mapping capture payloads from runtime mapping config
  - Parameter snapshot capture function (deep-copy behavior)
  - Minimal unvalidated-template warning generation in manifest payload
  - Orchestrator integration for automatic capture
  - RunManifest schema updates for `assumptions` (structured), `mappings`, `warnings`
  - Unit/integration tests for capture and schema behavior

- **Out of scope:**
  - Hashing of input/output artifacts (Story 5-4)
  - Lineage graph generation (Story 5-3)
  - Reproducibility check harness (Story 5-5)
  - Full warning orchestration/routing framework (Story 5-6)

### Project Structure Notes

- **Existing governance module**: `src/reformlab/governance/` with `manifest.py` and `errors.py`
- **Orchestrator entry flow**: `src/reformlab/orchestrator/runner.py`
- **Scenario templates and registry**: `src/reformlab/templates/` (`schema.py`, `registry.py`)
- **Mapping configuration source**: `src/reformlab/computation/mapping.py`

### References

- [Source: architecture.md#Reproducibility-&-Governance] - Manifest requirements
- [Source: architecture.md#Step-Pluggable-Dynamic-Orchestrator] - Orchestrator as capture point
- [Source: backlog BKL-502] - Story acceptance criteria
- [Source: prd.md#Reproducibility-&-Auditability] - FR26, FR27, NFR9
- [Source: project-context.md#Critical-Implementation-Rules] - Determinism and immutability constraints
- [Source: 5-1-define-immutable-run-manifest-schema.md] - Previous story implementation

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
