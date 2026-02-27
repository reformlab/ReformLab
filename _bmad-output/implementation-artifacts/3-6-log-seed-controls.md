# Story 3.6: Log Seed Controls

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **framework developer**,
I want **to log seed controls, step execution order, and adapter version per yearly step**,
so that **analysts can inspect run logs to verify determinism, reproduce results, and debug simulation differences**.

## Acceptance Criteria

From backlog (BKL-306), aligned with FR17, NFR8, NFR9.

Scope note: this story adds structured logging infrastructure to capture seed information, step execution sequence, and adapter version at each yearly iteration. The log output enables governance (EPIC-5) and debugging workflows. It builds on the orchestrator infrastructure from Stories 3-1 through 3-5.

1. **AC-1: Year seed logged at yearly step start**
   - Given an orchestrator run, when each year begins execution, then the log entry includes:
     - Year number
     - Derived year seed (or "None" if no master seed)
     - Master seed reference (for traceability)
   - Log level: INFO for year start, DEBUG for detailed seed derivation.

2. **AC-2: Step execution order logged per year**
   - Given a yearly iteration with N steps, when steps execute, then the log shows:
     - Step sequence number (1 of N, 2 of N, etc.)
     - Step name
     - Year
   - The logged order matches the actual execution order (topological sort from StepRegistry or explicit pipeline order).
   - Log level: DEBUG for step execution, INFO for year summary.

3. **AC-3: Adapter version logged during computation step**
   - Given a `ComputationStep` in the pipeline, when it executes, then the log includes the adapter version returned by `adapter.version()`.
   - This extends the existing computation metadata (Story 3-5) to include log output.
   - Log level: INFO for adapter version, DEBUG for detailed computation context.

4. **AC-4: Year summary logged at yearly step completion**
   - Given a year completes all steps successfully, when the year ends, then a summary log entry includes:
     - Year number
     - Step count executed
     - Year seed used
     - Adapter version (if computation step executed)
   - Log level: INFO.

5. **AC-5: Logs enable seed difference detection**
   - Given two runs with different master seeds, when logs are compared, then the seed differences are visible in log entries at every year.
   - Log format should include searchable markers (e.g., `seed=`, `year=`, `step=`) for grep/filter operations.

6. **AC-6: Structured metadata extends OrchestratorResult**
   - `OrchestratorResult.metadata` includes:
     - `step_execution_log`: List of step execution records per year
     - `seed_log`: Mapping of year to derived seed
   - This enables programmatic access to execution trace for governance manifests.

## Dependencies

- **Required prior stories (all done):**
  - Story 3-1 (BKL-301): Yearly loop orchestrator - provides `Orchestrator`, `YearState`, logging infrastructure
  - Story 3-2 (BKL-302): Step interface - provides `OrchestratorStep`, `StepRegistry`, step ordering
  - Story 3-3 (BKL-303): Carry-forward step - established step logging patterns
  - Story 3-4 (BKL-304): Vintage transition step - additional step context
  - Story 3-5 (BKL-305): ComputationStep - adapter version capture, `COMPUTATION_METADATA_KEY`
- **Current prerequisite status (from sprint-status.yaml):**
  - All stories 3-1 through 3-5: `done`
- **Follow-on stories:**
  - Story 3-7 (BKL-307): Panel output - consumes orchestrator results
  - Story 5-1 (BKL-501): Immutable run manifest - consumes seed/execution logs
  - Story 5-2 (BKL-502): Capture assumptions/mappings/parameters - extends logging to manifests

## Tasks / Subtasks

- [ ] Task 0: Review existing logging infrastructure (AC: all)
  - [ ] 0.1 Review `src/reformlab/orchestrator/runner.py` for current logging patterns
  - [ ] 0.2 Review `src/reformlab/orchestrator/computation_step.py` for adapter metadata capture
  - [ ] 0.3 Identify log format conventions and logger naming patterns in codebase
  - [ ] 0.4 Verify Python logging best practices for structured output

- [ ] Task 1: Enhance year-level logging in Orchestrator (AC: #1, #4, #5)
  - [ ] 1.1 Add year start log entry with seed information:
    - `logger.info("Year %d started: seed=%s (master=%s)", year, year_seed, master_seed)`
  - [ ] 1.2 Add year completion summary log entry:
    - `logger.info("Year %d completed: %d steps, seed=%s", year, step_count, year_seed)`
  - [ ] 1.3 Ensure log format uses searchable markers (`year=`, `seed=`)

- [ ] Task 2: Add step execution logging (AC: #2, #5)
  - [ ] 2.1 Log step sequence in `_execute_step()`:
    - `logger.debug("Year %d: step %d/%d '%s' starting", year, step_index+1, total_steps, step_name)`
    - `logger.debug("Year %d: step %d/%d '%s' completed", year, step_index+1, total_steps, step_name)`
  - [ ] 2.2 Pass step index and total to `_execute_step()` or track in `_run_year()`
  - [ ] 2.3 Ensure step names match topological order from pipeline

- [ ] Task 3: Enhance adapter version logging in ComputationStep (AC: #3)
  - [ ] 3.1 Add logger to `computation_step.py` module
  - [ ] 3.2 Log adapter version at INFO level during execute():
    - `logger.info("Year %d: ComputationStep using adapter version %s", year, adapter_version)`
  - [ ] 3.3 Log computation row count at DEBUG level:
    - `logger.debug("Year %d: computation produced %d rows", year, row_count)`

- [ ] Task 4: Add structured execution metadata to OrchestratorResult (AC: #6)
  - [ ] 4.1 Define stable keys for execution log in metadata:
    - `STEP_EXECUTION_LOG_KEY = "step_execution_log"`
    - `SEED_LOG_KEY = "seed_log"`
  - [ ] 4.2 Build step execution log during `_run_year()`:
    - List of `{"year": int, "step_index": int, "step_name": str, "status": str}`
  - [ ] 4.3 Build seed log during orchestrator run:
    - Dict `{year: seed}` for all executed years
  - [ ] 4.4 Include both in `OrchestratorResult.metadata`

- [ ] Task 5: Add tests for logging behavior (AC: all)
  - [ ] 5.1 Create `tests/orchestrator/test_logging.py` with:
    - Test year start/end log messages include seed
    - Test step execution log includes sequence numbers
    - Test adapter version appears in logs when ComputationStep runs
    - Test seed differences are visible in logs for different master seeds
  - [ ] 5.2 Add integration test validating `OrchestratorResult.metadata` contains execution logs
  - [ ] 5.3 Test seed_log and step_execution_log structure and content

- [ ] Task 6: Export API and run quality gates (AC: all)
  - [ ] 6.1 Export new constants from `src/reformlab/orchestrator/__init__.py`:
    - `STEP_EXECUTION_LOG_KEY`, `SEED_LOG_KEY`
  - [ ] 6.2 Update module docstring with new exports
  - [ ] 6.3 Run `ruff check src/reformlab/orchestrator tests/orchestrator`
  - [ ] 6.4 Run `mypy src/reformlab/orchestrator`
  - [ ] 6.5 Run `pytest tests/orchestrator/`

## Dev Notes

### Architecture Alignment

**From architecture.md - Reproducibility & Governance:**
> Every run records: OpenFisca version, adapter version, scenario version, data hashes, seeds, assumptions, step pipeline configuration.

**From architecture.md - Dynamic Execution Semantics:**
> Randomness is seed-controlled and logged in manifests.

**From PRD - FR17:**
> System enforces deterministic sequencing and explicit random-seed control in dynamic runs.

**From PRD - NFR8:**
> Random seeds used in synthetic population generation are explicit, pinned, and recorded in the run manifest.

**From backlog BKL-306:**
> Log seed controls, step execution order, and adapter version per yearly step
> - Given an orchestrator run, when inspecting the log, then each yearly step shows the random seed used, the step execution order, and the adapter version.
> - Given two runs with different seeds, when logs are compared, then the seed difference is visible in the log entries.

### Existing Code Patterns to Follow

**Logging conventions from `runner.py`:**
```python
logger = logging.getLogger(__name__)

# Current patterns:
logger.info("Starting orchestrator run: years %d-%d with %d steps", ...)
logger.debug("Starting year %d", year)
logger.debug("Year %d initialized with seed=%s (previous_year=%d)", ...)
logger.debug("Year %d: executing step %s", year, step_name)
logger.debug("Completed year %d", year)
logger.error("Orchestrator failed at year %d: %s", year, e)
logger.info("Orchestrator completed successfully: %d years processed", ...)
```

**ComputationStep metadata pattern from `computation_step.py`:**
```python
computation_metadata = {
    "adapter_version": adapter_version,
    "computation_period": year,
    "computation_row_count": row_count,
}
new_metadata[COMPUTATION_METADATA_KEY] = computation_metadata
```

**Seed derivation from `runner.py`:**
```python
def _derive_year_seed(self, year: int) -> int | None:
    if self.config.seed is None:
        return None
    return self.config.seed ^ year
```

### Implementation Strategy

1. **Logging only (Tasks 1-3):** Add structured log output without changing data flow. Use existing `logger` patterns.

2. **Metadata extension (Task 4):** Add execution trace to `OrchestratorResult.metadata` for programmatic access. This enables EPIC-5 governance without changing the logging itself.

3. **Searchable log format:** Use consistent markers (`year=`, `seed=`, `step=`, `adapter=`) for grep/filter. Example:
   ```
   INFO  reformlab.orchestrator.runner: year=2024 started seed=1234567890 master_seed=42
   DEBUG reformlab.orchestrator.runner: year=2024 step=1/3 name=computation starting
   INFO  reformlab.orchestrator.computation_step: year=2024 adapter_version=openfisca-france-167.0.0
   DEBUG reformlab.orchestrator.runner: year=2024 step=1/3 name=computation completed
   DEBUG reformlab.orchestrator.runner: year=2024 step=2/3 name=vintage_transition starting
   ...
   INFO  reformlab.orchestrator.runner: year=2024 completed steps=3 seed=1234567890
   ```

### Scope Guardrails

- **In scope:**
  - Structured logging of seed, step order, adapter version
  - Searchable log markers for debugging
  - Execution metadata in `OrchestratorResult`
  - Tests for logging behavior and metadata structure

- **Out of scope:**
  - Manifest file generation (Story 5-1)
  - Log file persistence or rotation (infrastructure concern)
  - Log aggregation or analysis tools
  - Panel output formatting (Story 3-7)

### Testing Notes

- Use `caplog` fixture in pytest to capture and assert log messages
- Test at both INFO and DEBUG levels
- Verify searchable markers appear in log output
- Test metadata structure in `OrchestratorResult`
- Compare logs from runs with different seeds to verify difference visibility

### Project Structure Notes

- New code in `src/reformlab/orchestrator/runner.py` (enhanced logging)
- New code in `src/reformlab/orchestrator/computation_step.py` (adapter version logging)
- New constants potentially in `src/reformlab/orchestrator/types.py` or `runner.py`
- New tests in `tests/orchestrator/test_logging.py`
- No new files needed - this is enhancement of existing modules

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Reproducibility & Governance]
- [Source: _bmad-output/planning-artifacts/architecture.md#Dynamic Execution Semantics]
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-306]
- [Source: _bmad-output/planning-artifacts/prd.md#FR17]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR8]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR9]
- [Source: src/reformlab/orchestrator/runner.py]
- [Source: src/reformlab/orchestrator/computation_step.py]
- [Source: src/reformlab/orchestrator/types.py]
- [Source: src/reformlab/orchestrator/step.py]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
