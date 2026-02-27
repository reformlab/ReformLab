# Story 6.6: Improve Operational Error UX

Status: ready-for-dev

## Story

As a **policy analyst (Sophie) or researcher (Marco)**,
I want **operational errors (mapping failures, run-state issues, configuration problems) to display user-friendly messages with actionable guidance**,
so that **I can quickly understand what went wrong and how to fix it without needing to interpret raw exceptions or technical jargon**.

## Acceptance Criteria

From backlog (BKL-606), aligned with FR4 (field-level error validation) and FR27 (warnings for unvalidated templates/configs).

1. **AC-1: Consistent error message format across all public API exceptions**
   - Given any error raised by the public Python API (ConfigurationError, SimulationError), when the user sees the error message, then it follows the format: **"[What failed]** — [Why] — [How to fix]".
   - No raw stack traces, internal paths, or technical codes are exposed in user-facing messages.
   - Exception types preserve structured attributes (field_path, expected, actual, cause) for programmatic access.

2. **AC-2: Mapping errors provide field-level context and suggestions**
   - Given a mapping configuration error (invalid OpenFisca variable, schema mismatch), when the error is raised, then the message identifies the exact field name and suggests corrections.
   - Given close-match candidates exist, when a mapping error occurs, then suggestions are included (e.g., "Did you mean 'income_tax' instead of 'income_taxes'?").

3. **AC-3: Run-state errors preserve partial results and context**
   - Given an orchestrator failure at year t+k, when the error is raised, then the message indicates the failing year, step, and completed years are preserved for debugging.
   - Given partial yearly states exist, when querying the error, then completed states are accessible via the error object's `partial_states` attribute.

4. **AC-4: Configuration validation errors are aggregated**
   - Given multiple validation issues in a configuration, when validated before execution, then all errors are reported together (not one at a time).
   - Each error entry includes field path, expected value description, and actual value.

5. **AC-5: Warnings system for unvalidated configurations**
   - Given a scenario using an unvalidated template or non-standard configuration, when the run is initiated, then a warning is emitted (not a blocking error).
   - Warnings are logged and optionally surfaced in `SimulationResult.metadata["warnings"]`.
   - Given a run manifest, when inspected, then warning flags for unvalidated templates are visible.

6. **AC-6: Error recovery guidance**
   - Given any operational error, when raised, then the exception message includes an actionable "fix" clause describing what the user should do.
   - Fix guidance is specific to the error type (e.g., "Check your mapping file at line X" or "Ensure population file exists at path Y").

## Dependencies

Dependency gate: if any hard dependency below is not `done`, set this story to `blocked`.

- **Soft dependency: Story 6-4b (BKL-604b) — BACKLOG**
  - GUI wiring may consume improved error presentation.
  - Not a blocker — Python API error improvements are standalone.

- **Hard dependency: Story 6-1 (BKL-601) — DONE**
  - Provides `ConfigurationError` and `SimulationError` base types.

- **Hard dependency: Story 1-3 (BKL-103) — DONE**
  - Provides mapping configuration infrastructure.

- **Hard dependency: Story 1-5 (BKL-105) — DONE**
  - Provides data-quality checks and `DataQualityError`.

- **Hard dependency: Story 5-6 (BKL-506) — READY-FOR-DEV**
  - Provides warning system for unvalidated templates.
  - Coordinate implementation — this story improves UX presentation of those warnings.

## Tasks / Subtasks

- [ ] Task 0: Audit existing error patterns and establish format standard (AC: #1, #6)
  - [ ] 0.1 Review all exception classes in `interfaces/errors.py`, `orchestrator/errors.py`, `computation/exceptions.py`, `governance/errors.py`
  - [ ] 0.2 Document current format inconsistencies
  - [ ] 0.3 Define canonical "[What failed] — [Why] — [How to fix]" format as a code guideline

- [ ] Task 1: Enhance ConfigurationError with consistent format (AC: #1, #4, #6)
  - [ ] 1.1 Update `ConfigurationError.__str__()` in `interfaces/errors.py` to emit "[What failed] — [Why] — [How to fix]" format
  - [ ] 1.2 Add optional `fix` attribute to `ConfigurationError` for explicit fix guidance
  - [ ] 1.3 Ensure field_path, expected, actual attributes remain accessible
  - [ ] 1.4 Add tests verifying message format and structured attribute access

- [ ] Task 2: Enhance SimulationError with cause chain and recovery guidance (AC: #1, #3, #6)
  - [ ] 2.1 Update `SimulationError.__str__()` to include recovery guidance
  - [ ] 2.2 Add optional `fix` attribute to `SimulationError`
  - [ ] 2.3 Ensure `cause` exception is not exposed in user-facing message but remains accessible programmatically
  - [ ] 2.4 Add tests for error chaining and message format

- [ ] Task 3: Implement mapping error suggestions (AC: #2)
  - [ ] 3.1 Extend `ApiMappingError` with close-match suggestion logic (Levenshtein or similar)
  - [ ] 3.2 Update error messages to include "Did you mean..." suggestions when candidates exist
  - [ ] 3.3 Integrate suggestion logic in mapping validation path (`computation/mapping.py`)
  - [ ] 3.4 Add tests for suggestion accuracy and message format

- [ ] Task 4: Implement aggregated validation errors (AC: #4)
  - [ ] 4.1 Create `ValidationErrors` aggregate exception type in `interfaces/errors.py`
  - [ ] 4.2 Update `_validate_config()` in `interfaces/api.py` to collect all errors before raising
  - [ ] 4.3 Format aggregated errors as numbered list with individual "[What] — [Why] — [Fix]" entries
  - [ ] 4.4 Add tests verifying multiple errors are aggregated and formatted correctly

- [ ] Task 5: Integrate warning system for unvalidated configs (AC: #5)
  - [ ] 5.1 Coordinate with Story 5-6 warning infrastructure
  - [ ] 5.2 Capture warnings in `SimulationResult.metadata["warnings"]` list
  - [ ] 5.3 Ensure warnings are non-blocking and logged (not raised as exceptions)
  - [ ] 5.4 Update `RunManifest` documentation to note warning fields
  - [ ] 5.5 Add tests for warning capture and manifest presence

- [ ] Task 6: Verify run-state error context preservation (AC: #3)
  - [ ] 6.1 Confirm `OrchestratorError` preserves `partial_states`, `year`, `step_name`
  - [ ] 6.2 Update `OrchestratorError.__str__()` to follow "[What] — [Why] — [Fix]" format
  - [ ] 6.3 Ensure `SimulationResult` captures partial states when run fails mid-execution
  - [ ] 6.4 Add integration tests verifying partial state recovery

- [ ] Task 7: Final validation and documentation (AC: #1-#6)
  - [ ] 7.1 Run full test suite focused on error paths
  - [ ] 7.2 Verify no raw tracebacks appear in user-facing messages
  - [ ] 7.3 Update API docstrings with error behavior documentation
  - [ ] 7.4 Add error handling examples to notebooks if appropriate

## Dev Notes

### Architecture Compliance

This story implements FR4 and FR27 within the architecture's layered model:

- **Interfaces layer**: `ConfigurationError` and `SimulationError` are the public-facing exception types. All subsystem exceptions should be wrapped in these before reaching user code.
- **Exception wrapping pattern**: Lower-layer exceptions (`OrchestratorError`, `DataQualityError`, `ApiMappingError`) are caught and re-raised as `SimulationError` or `ConfigurationError` with the original as `cause`.
- **UX design compliance**: Error format follows UX spec requirement: "[What failed] — [Why] — [How to fix]" with no raw exceptions exposed.

### Existing Error Patterns

**Current exception hierarchy:**

```
interfaces/errors.py
├── ConfigurationError(field_path, expected, actual, message)
└── SimulationError(message, cause)

orchestrator/errors.py
└── OrchestratorError(summary, reason, year, step_name, partial_states, original_error)

computation/exceptions.py
├── CompatibilityError(expected, actual, details)
└── ApiMappingError(summary, reason, fix, invalid_names, valid_names, suggestions)

computation/quality.py
└── DataQualityError(result: QualityCheckResult)

governance/errors.py
├── ManifestIntegrityError
├── ManifestValidationError
├── LineageIntegrityError
└── ReproducibilityValidationError
```

**Good patterns to preserve:**
- `ApiMappingError` already uses "[summary] — [reason] — [fix]" format
- `OrchestratorError` has rich structured context (year, step, partial_states)
- `DataQualityError` aggregates multiple issues

**Patterns to improve:**
- `ConfigurationError` message format inconsistent (sometimes auto-generated, sometimes custom)
- `SimulationError` lacks structured fix guidance
- Governance errors lack actionable fix suggestions

### Error Format Standard

All user-facing error messages should follow:

```
[What failed] — [Why it failed] — [How to fix it]
```

Examples:
- "Configuration error at 'scenario.start_year' — Expected int, got 'abc' — Provide a valid integer year value"
- "Mapping validation failed — Variable 'incomes_tax' not found in OpenFisca — Did you mean 'income_tax'? Check variable name spelling"
- "Simulation failed at year 2027 — ComputationStep raised ValueError — Check adapter configuration and input data for year 2027"

### Scope Guardrails

In scope:
- Python API exception message formatting improvements
- Mapping error suggestion system
- Aggregated validation errors
- Warning integration for unvalidated templates
- Partial state preservation in failure scenarios

Out of scope (deferred):
- GUI error display components (Story 6-4b)
- FastAPI error response formatting (Story 6-4b)
- Internationalization of error messages
- Error logging infrastructure changes

### File Locations

```text
src/reformlab/
├── interfaces/
│   ├── errors.py           ← Enhance ConfigurationError, SimulationError; add ValidationErrors
│   └── api.py              ← Update _validate_config() for aggregation
├── computation/
│   ├── exceptions.py       ← Enhance ApiMappingError suggestions
│   ├── mapping.py          ← Integrate suggestion logic
│   └── quality.py          ← Already compliant; minor format updates if needed
├── orchestrator/
│   └── errors.py           ← Update OrchestratorError format
└── governance/
    └── errors.py           ← Add fix guidance to manifest errors

tests/
├── interfaces/test_errors.py  ← Add/extend error format tests
├── computation/test_mapping_errors.py  ← Suggestion tests
└── orchestrator/test_errors.py ← Partial state recovery tests
```

### Project Structure Notes

- Unified error format improves analyst confidence (UX design principle)
- Exception attributes remain structured for programmatic consumption
- Warning system aligns with governance manifest warnings field

### References

- [Source: prd.md#Functional Requirements] — FR4 field-level validation, FR27 unvalidated config warnings
- [Source: architecture.md#Layered Architecture] — Exception wrapping pattern
- [Source: ux-design-specification.md#Error Handling] — "[What failed] — [Why] — [How to fix]" format requirement
- [Source: ux-design-specification.md#Feedback & State Communication] — Error message guidelines
- [Source: 6-5-add-export-actions.md] — Follow-on dependency context

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
