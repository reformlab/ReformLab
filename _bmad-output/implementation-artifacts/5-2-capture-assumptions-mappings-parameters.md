# Story 5.2: Capture Assumptions/Mappings/Parameters in Manifests

Status: ready-for-dev

## Story

As a **policy analyst**,
I want **all assumptions, mappings, and parameter configurations to be automatically captured in run manifests at execution time**,
so that **I can audit the exact methodology used in any simulation and reproduce it with identical results**.

## Acceptance Criteria

From backlog (BKL-502), aligned with FR26 and FR27.

1. **AC-1: Assumption capture in manifests**
   - Given a run with custom mapping configuration, when the manifest is inspected, then all mappings and assumption sources are listed with their values.
   - Assumptions include: data source mappings, variable transformations, default value choices, and configuration overrides.
   - Each assumption is recorded with: key, value, source (where it was defined), and whether it's a default or user-specified value.

2. **AC-2: Mapping configuration capture**
   - Given an OpenFisca variable mapping configuration, when the run completes, then the manifest includes the complete mapping schema.
   - Mapping capture includes: OpenFisca variable names → project schema field names, any transformations applied, and the mapping configuration file path (if external).

3. **AC-3: Parameter snapshot capture**
   - Given a scenario with policy parameters (tax rates, thresholds, etc.), when the run completes, then the manifest contains a complete snapshot of all parameter values as they were at execution time.
   - Parameter snapshot is a deep copy, not a reference — changes to source configurations after the run do not affect the manifest.

4. **AC-4: Unvalidated template warning flag**
   - Given a run using an unvalidated template (not marked as validated in the scenario registry), when the manifest is generated, then a `warnings` field includes a warning flag indicating the template is unvalidated.
   - Warning format is actionable: includes template ID and suggests validation steps.

5. **AC-5: Orchestrator integration for automatic capture**
   - Manifest assumption/mapping/parameter capture is automatic during orchestrator execution — requires zero manual effort from the user (NFR9).
   - Capture happens at the orchestrator layer, not at individual step or adapter layers (single point of capture).

## Dependencies

- **Required prior stories:**
  - Story 5-1 (BKL-501): `RunManifest` schema with `assumptions`, `parameters`, and `integrity_hash` fields ✅ DONE
  - Story 1-3 (BKL-103): Input/output mapping configuration ✅ DONE
  - Story 2-1 (BKL-201): Scenario template schema with parameters ✅ DONE
  - Story 2-4 (BKL-204): Scenario registry with version IDs ✅ DONE
  - Story 3-1 (BKL-301): Orchestrator that runs yearly loop ✅ DONE
  - Story 3-6 (BKL-306): Seed logging in orchestrator ✅ DONE

- **Follow-on stories:**
  - Story 5-3 (BKL-503): Run lineage graph using manifest links
  - Story 5-4 (BKL-504): Hash input/output artifacts and store in manifest
  - Story 5-5 (BKL-505): Reproducibility check harness consuming manifests
  - Story 5-6 (BKL-506): Warning system for unvalidated templates

## Tasks / Subtasks

- [ ] Task 0: Review prerequisite contracts and boundaries (AC: dependency check)
  - [ ] 0.1 Review `RunManifest` schema from Story 5-1 (`src/reformlab/governance/manifest.py`)
  - [ ] 0.2 Review mapping configuration patterns from Story 1-3 (`src/reformlab/data/mapping.py` or computation adapter)
  - [ ] 0.3 Review scenario template parameter structure from Story 2-1 (`src/reformlab/templates/`)
  - [ ] 0.4 Review orchestrator execution flow from Story 3-1 (`src/reformlab/orchestrator/`)
  - [ ] 0.5 Confirm this story wires capture logic into orchestrator, not individual subsystems

- [ ] Task 1: Define assumption capture structures (AC: #1)
  - [ ] 1.1 Create `src/reformlab/governance/assumptions.py` for assumption tracking types
  - [ ] 1.2 Define frozen `Assumption` dataclass with: `key`, `value`, `source`, `is_default`
  - [ ] 1.3 Define frozen `AssumptionSet` or collection type for grouping assumptions by category
  - [ ] 1.4 Export types from `src/reformlab/governance/__init__.py`

- [ ] Task 2: Define mapping capture structures (AC: #2)
  - [ ] 2.1 Define frozen `MappingCapture` dataclass in `assumptions.py` or separate module
  - [ ] 2.2 Include: variable mappings dict, transformations list, config file path (if any)
  - [ ] 2.3 Ensure serialization is JSON-compatible for manifest storage

- [ ] Task 3: Implement parameter snapshot capture (AC: #3)
  - [ ] 3.1 Define `capture_parameter_snapshot()` function that deep-copies scenario parameters
  - [ ] 3.2 Ensure snapshot is immutable and detached from source configuration
  - [ ] 3.3 Validate parameter snapshot is JSON-serializable for manifest storage

- [ ] Task 4: Implement warning flag for unvalidated templates (AC: #4)
  - [ ] 4.1 Add `warnings: list[str]` field to `RunManifest` (or extend existing schema)
  - [ ] 4.2 Implement `check_template_validation_status()` helper
  - [ ] 4.3 Generate actionable warning message: "Template '{template_id}' is not validated. Run template validation before production use."

- [ ] Task 5: Wire capture logic into orchestrator (AC: #5)
  - [ ] 5.1 Identify orchestrator entry point where manifest is created (likely `Orchestrator.run()` or similar)
  - [ ] 5.2 Add assumption capture call at orchestrator level
  - [ ] 5.3 Add mapping capture call at orchestrator level
  - [ ] 5.4 Add parameter snapshot capture at orchestrator level
  - [ ] 5.5 Ensure all captures happen before `RunManifest` construction
  - [ ] 5.6 Add unvalidated template warning check

- [ ] Task 6: Update RunManifest schema if needed (AC: #1-4)
  - [ ] 6.1 Review if existing `assumptions`, `parameters` fields are sufficient
  - [ ] 6.2 Add `mappings` field to `RunManifest` if not already present
  - [ ] 6.3 Add `warnings` field to `RunManifest` for template validation warnings
  - [ ] 6.4 Update validation logic for new fields
  - [ ] 6.5 Update `REQUIRED_JSON_FIELDS` tuple if needed

- [ ] Task 7: Write tests and run quality gates (AC: #1-5)
  - [ ] 7.1 Create `tests/governance/test_assumptions.py` for assumption capture tests
  - [ ] 7.2 Test assumption capture with default vs user-specified values
  - [ ] 7.3 Test mapping capture with variable name mappings
  - [ ] 7.4 Test parameter snapshot immutability (modifications don't affect snapshot)
  - [ ] 7.5 Test unvalidated template warning generation
  - [ ] 7.6 Test orchestrator integration with mock scenarios
  - [ ] 7.7 Run `ruff check src/reformlab/governance tests/governance`
  - [ ] 7.8 Run `mypy src/reformlab/governance`
  - [ ] 7.9 Run `pytest tests/governance/ -v`

## Dev Notes

### Architecture Compliance

This story implements **FR26** (analyst can inspect assumptions and mappings used in any run) and **FR27** (system emits warnings for unvalidated templates).

**Key architectural constraints:**

- **Frozen dataclasses only** - All new assumption/mapping types MUST use `@dataclass(frozen=True)`. [Source: project-context.md#Critical-Implementation-Rules]
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

**Frozen dataclass pattern** from `manifest.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class Assumption:
    """Single assumption captured during run execution."""
    key: str
    value: Any
    source: str  # File path, config name, or "default"
    is_default: bool = False
```

**Validation pattern** from `manifest.py`:

```python
def _validate(self) -> None:
    """Validate assumption invariants."""
    if not isinstance(self.key, str) or not self.key.strip():
        raise ManifestValidationError(
            "Assumption key must be a non-empty string"
        )
    # ... etc
```

### Module Structure (Updated)

```
src/reformlab/governance/
├── __init__.py          # Add new exports
├── manifest.py          # Update RunManifest with new fields
├── errors.py            # Existing errors (may add AssumptionCaptureError)
├── assumptions.py       # NEW: Assumption, MappingCapture types
└── capture.py           # NEW: capture_assumptions(), capture_mappings(), capture_parameters()

tests/governance/
├── __init__.py
├── conftest.py          # Add fixtures for assumptions
├── test_manifest.py     # Existing tests
└── test_assumptions.py  # NEW: Assumption capture tests
```

### Orchestrator Integration Points

Based on architecture.md, the orchestrator runs:
1. ComputationAdapter call per year
2. Environmental policy templates
3. Transition steps (vintage, carry-forward)
4. Record year-t results

Manifest capture should happen at the **start of orchestrator execution** before any computation, capturing:
- Scenario parameters (from scenario template)
- Variable mappings (from adapter configuration)
- Assumption overrides (from configuration)
- Template validation status

### Warning Message Format

For unvalidated templates (AC-4):
```
WARNING: Template 'carbon-tax-v1' is not validated for production use.
Action: Run `reformlab validate template carbon-tax-v1` before using results in production.
```

### Scope Guardrails

- **In scope:**
  - Assumption capture structures and types
  - Mapping capture structures and types
  - Parameter snapshot capture function
  - Unvalidated template warning generation
  - Orchestrator integration for automatic capture
  - RunManifest schema updates (new fields if needed)
  - Unit tests for capture behavior

- **Out of scope:**
  - Hashing of input/output artifacts (Story 5-4)
  - Lineage graph generation (Story 5-3)
  - Reproducibility check harness (Story 5-5)
  - Full warning system beyond template validation (Story 5-6)

### Project Structure Notes

- **Existing governance module**: `src/reformlab/governance/` with manifest.py and errors.py
- **Orchestrator module**: `src/reformlab/orchestrator/` — need to identify exact integration point
- **Scenario templates**: `src/reformlab/templates/` — source of parameters to capture
- **Data mapping**: Need to identify where mapping configuration lives (likely in computation/ or data/)

### References

- [Source: architecture.md#Reproducibility-&-Governance] - Manifest requirements
- [Source: architecture.md#Step-Pluggable-Dynamic-Orchestrator] - Orchestrator as capture point
- [Source: backlog BKL-502] - Story acceptance criteria
- [Source: prd.md#Reproducibility-&-Auditability] - FR26, FR27, NFR9
- [Source: project-context.md#Critical-Implementation-Rules] - Frozen dataclasses, determinism
- [Source: 5-1-define-immutable-run-manifest-schema.md] - Previous story implementation

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

