# Story 2.7: Implement YAML/JSON Workflow Configuration

Status: done

## Story

As a **policy analyst**,
I want **to define and run complete scenario workflows from YAML/JSON configuration files with schema validation**,
so that **I can version-control my analysis workflows, share configurations with colleagues, and avoid writing code for common operations**.

## Acceptance Criteria

From backlog (BKL-207), aligned with FR31, NFR4, NFR20.

Scope note: this story delivers workflow configuration contracts (schema, load/validate, serialize, and execution handoff APIs) in the `templates/` subsystem. It does not implement orchestrator or indicator engines owned by EPIC-3/EPIC-4.

1. **AC-1: Load validated workflow configuration from YAML or JSON and hand off for execution**
   - Given a valid `.yaml`, `.yml`, or `.json` workflow configuration file, when loaded through the workflow API, then it is parsed into a typed `WorkflowConfig` and passes schema validation.
   - The configuration supports specifying: data sources, scenario template references, run parameters, and output preferences.
   - A workflow run can be initiated through a handoff API that delegates to an injected/existing runtime entrypoint and returns structured results when a backend is available.

2. **AC-2: Schema validation with field-level error messages for both formats**
   - Given a YAML or JSON file with an invalid field, when validated, then the error identifies the field path and source location (line number where available; JSON pointer otherwise).
   - Given missing required fields, validation lists all missing fields with expected types.
   - Given type mismatches, validation reports expected vs actual type for each mismatch.

3. **AC-3: Deterministic round-trip stability and version-control-friendly output**
   - Given a valid workflow config serialized and reloaded in the same format (YAML or JSON), semantic content remains unchanged with deterministic key ordering for stable fields.
   - YAML output is human-readable and consistently indented; JSON output is pretty-printed with stable ordering.
   - YAML comment preservation is explicitly documented as out of guarantee with the chosen parser/dumper.

4. **AC-4: CI validation of shipped workflow examples**
   - Given the shipped workflow examples in YAML and JSON, when CI runs validation, then all examples pass schema checks.
   - Example workflows include: carbon tax analysis, scenario comparison, and multi-scenario batch run.

## Tasks / Subtasks

- [x] Task 0: Validate prerequisites and boundaries
  - [x] 0.1 Confirm Story 2.1 (schema/loader) and Story 2.4 (registry) are `done` or `review` in `_bmad-output/implementation-artifacts/sprint-status.yaml`
  - [x] 0.2 Confirm Story 2.6 migration helper APIs are available for schema-version compatibility checks (or document fallback behavior)
  - [x] 0.3 Confirm existing YAML/JSON loading patterns in `src/reformlab/templates/loader.py` and error shape patterns in `src/reformlab/templates/exceptions.py`
  - [x] 0.4 Define scope boundary: this story owns config contracts + execution handoff only, not orchestrator/indicator implementation

- [x] Task 1: Define workflow configuration schema (AC: #1, #2)
  - [x] 1.1 Create `src/reformlab/templates/workflow.py` with workflow dataclasses
  - [x] 1.2 Define `WorkflowConfig` dataclass with required fields:
    - `name`: str - Workflow identifier
    - `version`: str - Schema version for migration compatibility
    - `description`: str (optional) - Human-readable description
    - `data_sources`: dict - Data source references (population, emission factors)
    - `scenarios`: list - Scenario references or inline definitions
    - `run_config`: dict - Orchestrator settings (years, output format)
    - `outputs`: list - Requested output types (indicators, exports)
  - [x] 1.3 Define `DataSourceConfig`, `ScenarioRef`, `RunConfig`, `OutputConfig` supporting dataclasses
  - [x] 1.4 Add `format` metadata (`yaml`/`json`) and schema-version metadata for deterministic serialization and compatibility checks
  - [x] 1.5 Implement validation methods with field-path error reporting

- [x] Task 2: Create JSON Schema for workflow validation (AC: #2, #4)
  - [x] 2.1 Create `src/reformlab/templates/schema/workflow.schema.json`
  - [x] 2.2 Define schema with:
    - Required fields with types
    - Enum constraints for output formats, scenario references
    - Pattern constraints for version strings
    - Nested object definitions for data_sources, scenarios, run_config
  - [x] 2.3 Add `$schema` reference support for IDE validation
  - [x] 2.4 Test schema with `jsonschema` library validation

- [x] Task 3: Implement workflow loader with validation (AC: #1, #2, #3)
  - [x] 3.1 Add `load_workflow_config(path)` function to `workflow.py`
  - [x] 3.2 Implement format detection by extension (`.yaml`, `.yml`, `.json`)
  - [x] 3.3 Implement YAML parsing with `yaml.safe_load()` and JSON parsing with `json.loads()`
  - [x] 3.4 Implement JSON Schema validation with field-path and source-location reporting
  - [x] 3.5 Return `WorkflowConfig` dataclass on success, raise `WorkflowError` on failure
  - [x] 3.6 Add `validate_workflow_config(data)` for programmatic dict validation
  - [x] 3.7 Error messages follow existing `ScenarioError` pattern: summary, reason, fix, invalid_fields

- [x] Task 4: Implement workflow serializer with round-trip stability (AC: #3)
  - [x] 4.1 Add `dump_workflow_config(config, path, *, format: str | None = None)` function
  - [x] 4.2 Use deterministic YAML output (`yaml.safe_dump(..., sort_keys=False, default_flow_style=False)`)
  - [x] 4.3 Use deterministic JSON output (`json.dumps(..., indent=2, sort_keys=True)`)
  - [x] 4.4 Add round-trip unit tests (YAML: load → dump → load, JSON: load → dump → load)
  - [x] 4.5 Document comment preservation limitations (YAML comments are not guaranteed to survive round-trip)

- [x] Task 5: Implement execution handoff API (AC: #1)
  - [x] 5.1 Add `prepare_workflow_request(config)` to normalize config into runtime request payload
  - [x] 5.2 Add `run_workflow(config, *, runner=None)` that delegates to an injected runner or existing API entrypoint
  - [x] 5.3 Validate scenario/data-source references before handoff using existing template/registry lookup helpers where available
  - [x] 5.4 Return structured delegated result on success; if runtime backend is unavailable, raise actionable `WorkflowError` with fix guidance
  - [x] 5.5 Keep runtime semantics thin: no orchestrator step logic or indicator computations are implemented in this story

- [x] Task 6: Create example workflow configurations (AC: #4)
  - [x] 6.1 Create `examples/workflows/` directory
  - [x] 6.2 Add `carbon_tax_analysis.yaml` - Single scenario analysis workflow
  - [x] 6.3 Add `scenario_comparison.yaml` - Baseline vs reform comparison workflow
  - [x] 6.4 Add `batch_sensitivity.json` - Multi-scenario batch analysis workflow
  - [x] 6.5 Add `README.md` documenting YAML/JSON example workflows

- [x] Task 7: Add tests and CI integration (AC: #2, #4)
  - [x] 7.1 Create `tests/templates/test_workflow.py`
  - [x] 7.2 Add unit tests for schema validation in YAML and JSON (valid, invalid, edge cases)
  - [x] 7.3 Add unit tests for loader error messages (line numbers where available, field paths / JSON pointers)
  - [x] 7.4 Add round-trip stability tests for both formats
  - [x] 7.5 Add integration tests validating all shipped examples
  - [x] 7.6 Add execution-handoff contract tests (runner available vs unavailable backend path)
  - [x] 7.7 Ensure CI runs example validation on every push

- [x] Task 8: Export APIs and documentation
  - [x] 8.1 Export workflow APIs in `src/reformlab/templates/__init__.py`
  - [x] 8.2 Add docstrings for all public workflow APIs
  - [x] 8.3 Run `ruff check` and `mypy` on workflow module
  - [x] 8.4 Run targeted tests (`pytest tests/templates/test_workflow.py`)

## Dev Notes

### Architecture Alignment

**From architecture.md:**
- `templates/` subsystem owns scenario templates, versioned registry definitions, and workflow configuration.
- FR31: "User can configure workflows with YAML/JSON files for analyst-friendly version control."
- NFR4: "YAML configuration loading and validation completes in under 1 second for typical policy definitions."
- NFR20: "YAML examples are tested in CI to prevent documentation drift."

This story extends the `templates/` subsystem with workflow-level configuration contracts and execution handoff APIs while reusing existing scenario and loader infrastructure. Runtime execution internals remain in orchestrator/indicator subsystems.

### Existing Code Patterns to Reuse

- **`src/reformlab/templates/loader.py`:**
  - `load_scenario_template()` pattern for YAML loading with validation
  - `ScenarioError` pattern with summary, reason, fix, invalid_fields
  - `SCHEMA_VERSION` constant for version tracking
  - `validate_schema_version()` for compatibility checks

- **`src/reformlab/templates/schema.py`:**
  - Frozen dataclass pattern for immutable configuration objects
  - Enum-based type constraints (PolicyType pattern)
  - YearSchedule for temporal configuration

- **`src/reformlab/templates/registry.py`:**
  - `RegistryError` pattern for actionable error messages
  - Scenario lookup and version resolution patterns

- **`src/reformlab/templates/exceptions.py`:**
  - Custom exception hierarchy with structured fields

### Project Structure Notes

**New files:**
- `src/reformlab/templates/workflow.py` - Workflow schema and loader
- `src/reformlab/templates/schema/workflow.schema.json` - JSON Schema
- `examples/workflows/*.{yaml,json}` - Example workflow configurations
- `examples/workflows/README.md` - Example documentation
- `tests/templates/test_workflow.py` - Workflow tests

**Files to modify:**
- `src/reformlab/templates/__init__.py` - Export workflow APIs

### Key Dependencies

- **Story 2.1 / BKL-201:** Scenario schema dataclasses and loader semantics (prerequisite)
- **Story 2.4 / BKL-204:** Scenario registry APIs for scenario references in workflows
- **Story 2.6 / BKL-206:** Schema migration/version compatibility utilities (optional reuse for workflow schema versions)
- **Standard library:** `dataclasses`, `typing`, `pathlib`
- **External packages:**
  - `pyyaml` (already in use)
  - `jsonschema` for JSON Schema validation

### Cross-Story Dependencies

- **Hard gates (must be done/review):**
  - Story 2.1 / BKL-201 (scenario schema and loader)
  - Story 2.4 / BKL-204 (registry lookups for scenario references)
- **Related but non-blocking:**
  - Story 2.6 / BKL-206 (version compatibility/migration helper reuse)
  - EPIC-3 orchestrator (runtime backend used by handoff API when available)
  - EPIC-4 indicators (result payloads may include indicator outputs when backend supports them)

### Out-of-Scope Guardrails

- No GUI workflow builder in this story
- No real-time workflow editing/hot-reload
- No workflow execution history/lineage (governance layer handles this in EPIC-5)
- No distributed/parallel workflow execution
- No orchestrator step implementation, yearly loop logic, or indicator computation logic in this story

### Implementation Guidelines

**Error Message Pattern (follow existing ScenarioError style):**
```python
raise WorkflowError(
    file_path=path,
    summary="Workflow validation failed",
    reason="missing required field: scenarios",
    fix="Add a 'scenarios' list with at least one scenario reference",
    invalid_fields=("scenarios",),
    line_number=12,  # NEW: line number for YAML errors
)
```

**Workflow Configuration Shape (YAML):**
```yaml
$schema: "./schema/workflow.schema.json"
version: "1.0"
name: "carbon_tax_comparison"
description: "Compare baseline with progressive redistribution reform"

data_sources:
  population: "synthetic_french_2024"  # Registry reference
  emission_factors: "default"

scenarios:
  - baseline: "carbon_tax_flat_44"     # Registry reference
  - reform: "carbon_tax_progressive"   # Registry reference

run_config:
  projection_years: 10
  start_year: 2025

outputs:
  - type: "distributional_indicators"
    by: ["income_decile"]
  - type: "comparison_table"
    format: "csv"
    path: "outputs/comparison.csv"
```

**JSON Schema Validation with Line Numbers:**
- Use `ruamel.yaml` or custom line tracking if precise line numbers are critical
- Fallback: jsonschema errors include JSON path which maps to YAML structure

### Testing Standards

- Use `pytest` and existing template fixtures
- Test valid workflows load/validate/serialize successfully in YAML and JSON
- Test invalid workflows produce actionable error messages
- Test round-trip stability (load → dump → load → compare)
- Test CI validation of shipped examples
- Test execution handoff behavior for available and unavailable runtime backends
- Assert error messages include file path, line number (where available), and fix guidance

### Performance Considerations

- NFR4 requires validation under 1 second for typical configurations
- Keep config validation independent of heavy runtime execution paths
- Cache JSON Schema compilation for repeated validations

### References

- [Source: _bmad-output/planning-artifacts/architecture.md]
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-207]
- [Source: _bmad-output/planning-artifacts/prd.md#FR31]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR4]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR20]
- [Source: src/reformlab/templates/loader.py]
- [Source: src/reformlab/templates/schema.py]
- [Source: src/reformlab/templates/registry.py]
- [Source: src/reformlab/templates/exceptions.py]
- [Source: _bmad-output/implementation-artifacts/2-1-define-scenario-template-schema.md]
- [Source: _bmad-output/implementation-artifacts/2-6-add-schema-migration-helper.md]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- All 44 workflow tests pass
- All 408 templates tests pass (excluding numpy-dependent test)
- ruff check passes with no issues
- mypy passes with no issues

### Completion Notes List

- Implemented complete workflow configuration schema with frozen dataclasses (WorkflowConfig, DataSourceConfig, ScenarioRef, RunConfig, OutputConfig)
- Created JSON Schema (workflow.schema.json) with Draft 2020-12 support for IDE validation
- Implemented YAML/JSON loader with format detection (.yaml, .yml, .json)
- JSON Schema validation integrated with field-path error reporting
- Deterministic serialization: YAML with consistent indentation, JSON with sorted keys
- Round-trip stability verified through tests (load -> dump -> load)
- Execution handoff API with injected runner support and actionable error messages when backend unavailable
- Added 3 example workflows: carbon_tax_analysis.yaml, scenario_comparison.yaml, batch_sensitivity.json
- Added comprehensive test suite (44 tests) covering validation, loading, serialization, round-trip, and execution handoff
- Exported 20 new APIs in templates/__init__.py
- Added jsonschema dependency to pyproject.toml

### File List

**New files:**
- src/reformlab/templates/workflow.py
- src/reformlab/templates/schema/workflow.schema.json
- examples/workflows/carbon_tax_analysis.yaml
- examples/workflows/scenario_comparison.yaml
- examples/workflows/batch_sensitivity.json
- examples/workflows/README.md
- tests/templates/test_workflow.py

**Modified files:**
- src/reformlab/templates/__init__.py (added workflow API exports)
- pyproject.toml (added jsonschema dependency and mypy overrides)
- _bmad-output/implementation-artifacts/sprint-status.yaml (status: in-progress -> review)

## Change Log

- 2026-02-27: Implemented Story 2.7 - YAML/JSON workflow configuration with schema validation and execution handoff API
