# Story 2.7: Implement YAML/JSON Workflow Configuration

Status: ready-for-dev

## Story

As a **policy analyst**,
I want **to define and run complete scenario workflows from YAML configuration files with schema validation**,
so that **I can version-control my analysis workflows, share configurations with colleagues, and avoid writing code for common operations**.

## Acceptance Criteria

From backlog (BKL-207), aligned with FR31, NFR4, NFR20:

1. **AC-1: Load and execute complete workflow from YAML configuration**
   - Given a valid YAML workflow configuration file, when loaded through the workflow API, then the workflow executes end-to-end (data load, scenario selection, run, indicators output).
   - The configuration supports specifying: data sources, scenario template references, run parameters, and output format preferences.
   - Workflow execution returns structured results accessible via the Python API.

2. **AC-2: Schema validation with field-level error messages**
   - Given a YAML file with an invalid field, when validated, then the error message identifies the exact line number and field name.
   - Given a YAML file with missing required fields, when validated, then all missing fields are listed with their expected types.
   - Given a YAML file with type mismatches, when validated, then the error specifies expected vs. actual type for each mismatch.

3. **AC-3: Round-trip stability and version control friendliness**
   - Given a YAML file saved and reloaded, when compared, then the content is round-trip stable (no silent changes, no reordering of stable fields).
   - YAML files use human-readable formatting with consistent indentation and key ordering.
   - Comments in YAML files are preserved on round-trip (where feasible with PyYAML limitations).

4. **AC-4: CI validation of shipped examples**
   - Given the shipped YAML workflow examples, when CI runs validation, then all examples pass schema checks.
   - Example workflows include: carbon tax analysis, scenario comparison, multi-scenario batch run.

## Tasks / Subtasks

- [ ] Task 0: Validate prerequisites and boundaries
  - [ ] 0.1 Confirm Story 2.1 (schema/loader) is `done` or `review` in sprint-status.yaml
  - [ ] 0.2 Confirm existing YAML loading patterns in `src/reformlab/templates/loader.py`
  - [ ] 0.3 Confirm JSON Schema infrastructure exists at `src/reformlab/templates/schema/`
  - [ ] 0.4 Define scope boundary: workflow config is for analyst batch operations, not GUI state persistence

- [ ] Task 1: Define workflow configuration schema (AC: #1, #2)
  - [ ] 1.1 Create `src/reformlab/templates/workflow.py` with workflow dataclasses
  - [ ] 1.2 Define `WorkflowConfig` dataclass with required fields:
    - `name`: str - Workflow identifier
    - `version`: str - Schema version for migration compatibility
    - `description`: str (optional) - Human-readable description
    - `data_sources`: dict - Data source references (population, emission factors)
    - `scenarios`: list - Scenario references or inline definitions
    - `run_config`: dict - Orchestrator settings (years, output format)
    - `outputs`: list - Requested output types (indicators, exports)
  - [ ] 1.3 Define `DataSourceConfig`, `ScenarioRef`, `RunConfig`, `OutputConfig` supporting dataclasses
  - [ ] 1.4 Implement validation methods with field-path error reporting

- [ ] Task 2: Create JSON Schema for workflow validation (AC: #2, #4)
  - [ ] 2.1 Create `src/reformlab/templates/schema/workflow.schema.json`
  - [ ] 2.2 Define schema with:
    - Required fields with types
    - Enum constraints for output formats, scenario references
    - Pattern constraints for version strings
    - Nested object definitions for data_sources, scenarios, run_config
  - [ ] 2.3 Add `$schema` reference support for IDE validation
  - [ ] 2.4 Test schema with `jsonschema` library validation

- [ ] Task 3: Implement workflow loader with validation (AC: #1, #2)
  - [ ] 3.1 Add `load_workflow_config(path)` function to `workflow.py`
  - [ ] 3.2 Implement YAML parsing with `yaml.safe_load()`
  - [ ] 3.3 Implement JSON Schema validation with line number tracking via `jsonschema`
  - [ ] 3.4 Return `WorkflowConfig` dataclass on success, raise `WorkflowError` on failure
  - [ ] 3.5 Add `validate_workflow_config(data)` for programmatic dict validation
  - [ ] 3.6 Error messages follow existing `ScenarioError` pattern: summary, reason, fix, invalid_fields

- [ ] Task 4: Implement workflow serializer with round-trip stability (AC: #3)
  - [ ] 4.1 Add `dump_workflow_config(config, path)` function
  - [ ] 4.2 Use `yaml.safe_dump()` with `sort_keys=False` for stable ordering
  - [ ] 4.3 Use `default_flow_style=False` for readable multi-line format
  - [ ] 4.4 Add round-trip unit tests (load → dump → load → compare)
  - [ ] 4.5 Document comment preservation limitations (PyYAML does not preserve comments)

- [ ] Task 5: Implement workflow executor (AC: #1)
  - [ ] 5.1 Add `WorkflowRunner` class for orchestrating workflow execution
  - [ ] 5.2 Implement data source resolution (registry lookup, file paths)
  - [ ] 5.3 Implement scenario resolution (registry lookup, inline parsing)
  - [ ] 5.4 Integrate with existing registry and template loading APIs
  - [ ] 5.5 Return `WorkflowResult` with structured output access
  - [ ] 5.6 Stub orchestrator/indicator integration for EPIC-3/4 (return mock results for now)

- [ ] Task 6: Create example workflow configurations (AC: #4)
  - [ ] 6.1 Create `examples/workflows/` directory
  - [ ] 6.2 Add `carbon_tax_analysis.yaml` - Single scenario analysis workflow
  - [ ] 6.3 Add `scenario_comparison.yaml` - Baseline vs reform comparison workflow
  - [ ] 6.4 Add `batch_sensitivity.yaml` - Multi-scenario batch analysis workflow
  - [ ] 6.5 Add `README.md` documenting example workflows

- [ ] Task 7: Add tests and CI integration (AC: #2, #4)
  - [ ] 7.1 Create `tests/templates/test_workflow.py`
  - [ ] 7.2 Add unit tests for schema validation (valid, invalid, edge cases)
  - [ ] 7.3 Add unit tests for loader error messages (line numbers, field paths)
  - [ ] 7.4 Add round-trip stability tests
  - [ ] 7.5 Add integration test that validates all shipped examples
  - [ ] 7.6 Ensure CI runs example validation on every push

- [ ] Task 8: Export APIs and documentation
  - [ ] 8.1 Export workflow APIs in `src/reformlab/templates/__init__.py`
  - [ ] 8.2 Add docstrings for all public workflow APIs
  - [ ] 8.3 Run `ruff check` and `mypy` on workflow module
  - [ ] 8.4 Run targeted tests (`pytest tests/templates/test_workflow.py`)

## Dev Notes

### Architecture Alignment

**From architecture.md:**
- `templates/` subsystem owns scenario templates, versioned registry definitions, and workflow configuration.
- FR31: "User can configure workflows with YAML/JSON files for analyst-friendly version control."
- NFR4: "YAML configuration loading and validation completes in under 1 second for typical policy definitions."
- NFR20: "YAML examples are tested in CI to prevent documentation drift."

This story extends the templates subsystem with workflow-level configuration while reusing existing scenario and loader infrastructure.

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
- `examples/workflows/*.yaml` - Example workflow configurations
- `examples/workflows/README.md` - Example documentation
- `tests/templates/test_workflow.py` - Workflow tests

**Files to modify:**
- `src/reformlab/templates/__init__.py` - Export workflow APIs

### Key Dependencies

- **Story 2.1 / BKL-201:** Scenario schema dataclasses and loader semantics (prerequisite)
- **Story 2.4 / BKL-204:** Scenario registry for scenario references in workflows
- **Standard library:** `dataclasses`, `typing`, `pathlib`
- **External packages:**
  - `pyyaml` (already in use)
  - `jsonschema` for JSON Schema validation

### Cross-Story Dependencies

- **Hard gates (must be done/review):**
  - Story 2.1 / BKL-201 (scenario schema and loader)
- **Related but non-blocking:**
  - Story 2.4 / BKL-204 (registry for scenario references - enhancement path)
  - EPIC-3 orchestrator (workflow executor will integrate when available)
  - EPIC-4 indicators (workflow outputs will integrate when available)

### Out-of-Scope Guardrails

- No GUI workflow builder in this story
- No real-time workflow editing/hot-reload
- No workflow execution history/lineage (governance layer handles this in EPIC-5)
- No distributed/parallel workflow execution
- Orchestrator integration returns stubs until EPIC-3 is implemented

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
- Test valid workflows load and execute successfully
- Test invalid workflows produce actionable error messages
- Test round-trip stability (load → dump → load → compare)
- Test CI validation of shipped examples
- Assert error messages include file path, line number (where available), and fix guidance

### Performance Considerations

- NFR4 requires validation under 1 second for typical configurations
- Use lazy loading for referenced scenarios (don't load all until execution)
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

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
