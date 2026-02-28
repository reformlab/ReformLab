# Story 6.6: Improve Operational Error UX

Status: done

## Story

As a **policy analyst (Sophie) or researcher (Marco)**,
I want **operational errors (mapping failures, run-state issues, configuration problems) to display user-friendly messages with actionable guidance**,
so that **I can quickly understand what went wrong and how to fix it without needing to interpret raw exceptions or technical jargon**.

## Acceptance Criteria

From backlog (BKL-606), aligned with FR4 (field-level error validation) and FR27 (warnings for unvalidated templates/configs).

1. **AC-1: Public API exceptions follow one user-facing format**
   - Given an error raised through the Python API (`ConfigurationError`, `SimulationError`), when the message is shown to the user, then it follows: **"[What failed] — [Why] — [How to fix]"**.
   - User-facing text does not expose stack traces, internal paths, or raw exception class names.
   - Structured attributes remain programmatically accessible (`field_path`, `expected`, `actual`, `cause`).

2. **AC-2: Mapping errors include precise context and suggestions**
   - Given mapping failures (unknown OpenFisca variable, schema mismatch), when raised to API users, then messages identify the failing field/name and include actionable correction guidance.
   - Given close matches exist, when mapping fails, then suggestions are included (for example, "Did you mean ...?").

3. **AC-3: Run-state failures preserve execution context**
   - Given orchestrator failure at year `t+k`, when surfaced through API errors, then the message includes failing year, failing step, and completed years.
   - Given partial yearly states exist, when inspecting the raised error context (directly or via `SimulationError.cause`), completed states are available via `partial_states`.

4. **AC-4: Configuration validation reports multiple issues at once**
   - Given multiple invalid configuration fields, when validation runs before execution, then all issues are returned in a single raised error (aggregate), not fail-fast one-by-one.
   - Each issue includes field path, expected value/type, actual value, and fix guidance.

5. **AC-5: Existing warning signals are surfaced clearly to API users**
   - Given warning entries are present in orchestrator/manifest metadata (from Story 5-6 warning capture), when a run completes, then warnings are visible in `SimulationResult.metadata["warnings"]` and `RunManifest.warnings`.
   - Warnings remain non-blocking and are not converted into hard errors.

## Dependencies

Dependency gate: if any hard dependency below is not `done`, set this story to `blocked`.

- **Hard dependency: Story 6-1 (BKL-601) — DONE**
  - Provides `ConfigurationError` and `SimulationError` base types.

- **Hard dependency: Story 1-3 (BKL-103) — DONE**
  - Provides mapping configuration infrastructure.

- **Hard dependency: Story 1-5 (BKL-105) — DONE**
  - Provides data-quality checks and `DataQualityError`.

- **Integration dependency: Story 5-6 (BKL-506) — READY-FOR-DEV**
  - Owns warning generation/capture infrastructure for unvalidated templates/configs.
  - Not a blocker for AC-1..AC-4 implementation.
  - Required for full end-to-end validation of AC-5.

- **Soft dependency: Story 6-4b (BKL-604b) — BACKLOG**
  - GUI/FastAPI presentation layers consume improved API error and warning UX.
  - Not a blocker for Python API implementation.

## Tasks / Subtasks

- [ ] Task 0: Baseline and dependency check (AC: #1-#5)
  - [ ] 0.1 Confirm dependency status from `sprint-status.yaml` (6-1/1-3/1-5 done; 5-6 integration pending)
  - [ ] 0.2 Capture current behavior for API error rendering and warning propagation in tests

- [ ] Task 1: Standardize public API exception format (AC: #1)
  - [ ] 1.1 Update `ConfigurationError` and `SimulationError` in `interfaces/errors.py` to support explicit `fix` guidance and canonical message formatting
  - [ ] 1.2 Ensure structured fields remain accessible and stable for callers
  - [ ] 1.3 Ensure low-level exception details remain available via `cause` without leaking raw internals in user-facing text
  - [ ] 1.4 Add/extend tests in `tests/interfaces/test_api.py`

- [ ] Task 2: Mapping error UX alignment (AC: #2)
  - [ ] 2.1 Reuse existing close-match suggestion logic in `computation/mapping.py` / adapter flows
  - [ ] 2.2 Ensure raised API-level error text consistently includes field context + actionable fix + optional suggestions
  - [ ] 2.3 Add/extend tests in `tests/computation/test_mapping.py` and API-path tests

- [ ] Task 3: Preserve run-state failure context through API boundary (AC: #3)
  - [ ] 3.1 Ensure orchestrator failure context (`year`, `step_name`, `partial_states`) is preserved when surfaced as `SimulationError`
  - [ ] 3.2 Ensure user-facing message includes failure location and recovery guidance
  - [ ] 3.3 Add integration coverage in `tests/orchestrator/test_integration.py` and/or `tests/interfaces/test_api.py`

- [ ] Task 4: Add aggregated configuration validation error type (AC: #4)
  - [ ] 4.1 Add `ValidationErrors` aggregate exception in `interfaces/errors.py`
  - [ ] 4.2 Update `_validate_config()` in `interfaces/api.py` to accumulate all config issues before raising
  - [ ] 4.3 Ensure aggregate message entries follow canonical format and preserve per-field structure
  - [ ] 4.4 Add tests for multi-error validation behavior in `tests/interfaces/test_api.py`

- [ ] Task 5: Warning surfacing integration (AC: #5)
  - [ ] 5.1 Preserve and expose warning metadata in `SimulationResult.metadata["warnings"]` and `RunManifest.warnings`
  - [ ] 5.2 Ensure warnings stay non-blocking
  - [ ] 5.3 Add tests that validate warning passthrough behavior, using Story 5-6 outputs when available

- [ ] Task 6: Final verification (AC: #1-#5)
  - [ ] 6.1 Run targeted lint/type/test checks for touched modules
  - [ ] 6.2 Verify no raw traceback text leaks to API users
  - [ ] 6.3 Update API docstrings for revised error and warning behavior

## Dev Notes

### Architecture Compliance

This story implements FR4 and FR27 within the architecture's layered model:

- **Interfaces layer boundary**: User-facing error contracts are enforced in `interfaces/errors.py` and `interfaces/api.py`.
- **Layer-preserving propagation**: Lower-layer exceptions (`OrchestratorError`, `DataQualityError`, `ApiMappingError`) keep structured context and are surfaced through the API boundary without leaking raw internals.
- **Governance integration (no duplication)**: Warning generation remains owned by governance/orchestrator (Story 5-6); this story only standardizes API-facing presentation/surfacing.
- **UX design compliance**: API-visible messages follow "[What failed] — [Why] — [How to fix]".

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
- `ApiMappingError` already carries structured suggestion metadata (`suggestions`, `invalid_names`, `valid_names`)
- `OrchestratorError` has rich structured context (year, step, partial_states)
- `DataQualityError` aggregates multiple issues

**Patterns to improve:**
- `ConfigurationError` message format inconsistent (sometimes auto-generated, sometimes custom)
- `SimulationError` lacks structured fix guidance
- API boundary sometimes leaks low-level exception text directly

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
- Mapping error context/suggestion presentation at API boundary
- Aggregated validation errors
- Warning surfacing from existing warning infrastructure
- Partial state preservation in failure scenarios

Out of scope (deferred):
- GUI error display components (Story 6-4b)
- FastAPI error response formatting (Story 6-4b)
- Internationalization of error messages
- New warning-generation infrastructure (Story 5-6 scope)
- Broad governance exception redesign

### File Locations

```text
src/reformlab/
├── interfaces/
│   ├── errors.py           ← Standardize `ConfigurationError`/`SimulationError`; add `ValidationErrors`
│   └── api.py              ← Update validation aggregation and API-boundary error wrapping
├── computation/
│   ├── exceptions.py       ← Ensure mapping error payload supports API UX requirements
│   └── mapping.py          ← Reuse/verify close-match suggestion behavior
├── orchestrator/
│   └── errors.py           ← Preserve run-state context for API wrapping

tests/
├── interfaces/test_api.py      ← Error formatting, aggregation, and warning surfacing tests
├── computation/test_mapping.py ← Mapping suggestion and context tests
└── orchestrator/test_integration.py ← Partial-state propagation tests
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
