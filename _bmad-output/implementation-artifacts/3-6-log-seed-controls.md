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

1. **AC-1: Year seed is logged at year start with deterministic markers**
   - Given an orchestrator run, when a year begins, then an INFO log entry includes:
     - `year=<year>`
     - `seed=<derived_year_seed_or_None>`
     - `master_seed=<config.seed_or_None>`
     - `event=year_start`
   - Marker format is stable and grep-friendly (`key=value` tokens).

2. **AC-2: Step execution order is logged exactly as executed**
   - Given a yearly iteration with `N` steps, when steps execute, then DEBUG log entries include:
     - `year=<year>`
     - `step_index=<1..N>`
     - `step_total=<N>`
     - `step_name=<step_name>`
     - `event=step_start|step_end`
   - Logged order matches the actual iteration order of `OrchestratorConfig.step_pipeline` (including pipelines pre-built by `StepRegistry`).

3. **AC-3: Adapter version is logged by ComputationStep**
   - Given a `ComputationStep` in the pipeline, when it executes, then an INFO log entry includes:
     - `year=<year>`
     - `step_name=computation`
     - `adapter_version=<adapter.version()>` (or `<version-unavailable>` on fallback)
   - This extends Story 3-5 metadata recording with explicit runtime logs.

4. **AC-4: Year completion summary is logged only on successful year completion**
   - Given a year completes all steps successfully, when the year ends, then an INFO log entry includes:
     - `year=<year>`
     - `steps_executed=<N>`
     - `seed=<derived_year_seed_or_None>`
     - `adapter_version=<version_or_n/a>`
     - `event=year_complete`

5. **AC-5: Seed differences are observable across runs**
   - Given two runs with different master seeds and identical non-seed inputs, when logs are compared for the same year, then the `seed=` value differs and is visible in year-level log entries.
   - Required searchable markers: `year=`, `seed=`, `step_name=`, `adapter_version=`.

6. **AC-6: Minimal structured trace is exposed in `OrchestratorResult.metadata`**
   - `OrchestratorResult.metadata` includes:
     - `seed_log`: mapping of executed year to derived seed (`dict[int, int | None]`)
     - `step_execution_log`: ordered execution records with `year`, `step_index`, `step_total`, `step_name`, `status`
   - Trace is in-memory run metadata only; manifest persistence remains in Story 5-1.

## Dependencies

- **Required prior stories (all done):**
  - Story 3-1 (BKL-301): Yearly loop orchestrator - provides `Orchestrator`, `YearState`, logging infrastructure
  - Story 3-2 (BKL-302): Step interface - provides `OrchestratorStep`, `StepRegistry`, step ordering
  - Story 3-3 (BKL-303): Carry-forward step - established step logging patterns
  - Story 3-4 (BKL-304): Vintage transition step - additional step context
  - Story 3-5 (BKL-305): ComputationStep - adapter version capture, `COMPUTATION_METADATA_KEY`
- **Current prerequisite status (from `_bmad-output/implementation-artifacts/sprint-status.yaml`, checked 2026-02-27):**
  - `3-1-implement-yearly-loop-orchestrator`: `done`
  - `3-2-define-orchestrator-step-interface`: `done`
  - `3-3-implement-carry-forward-step`: `done`
  - `3-4-implement-vintage-transition-step`: `done`
  - `3-5-integrate-computationadapter-calls`: `done`
- **Follow-on stories:**
  - Story 3-7 (BKL-307): Panel output - consumes orchestrator results
  - Story 5-1 (BKL-501): Immutable run manifest - consumes seed/execution logs
  - Story 5-2 (BKL-502): Capture assumptions/mappings/parameters - extends logging to manifests

## Tasks / Subtasks

- [ ] Task 0: Confirm prerequisites and logging contract boundaries (AC: dependency check)
  - [ ] 0.1 Verify Story 3-1 through 3-5 status is `done` in `sprint-status.yaml`
  - [ ] 0.2 Review `src/reformlab/orchestrator/runner.py` and `src/reformlab/orchestrator/computation_step.py` logging patterns
  - [ ] 0.3 Record boundary note: manifest file generation remains out of scope (Story 5-1)

- [ ] Task 1: Add year and step structured logs in `Orchestrator` (AC: #1, #2, #4, #5)
  - [ ] 1.1 Emit year-start INFO log in `_run_year()` with stable markers:
    - `year=... seed=... master_seed=... event=year_start`
  - [ ] 1.2 Emit step-start and step-end DEBUG logs in `_execute_step()`:
    - include `step_index`, `step_total`, `step_name`, `event=step_start|step_end`
  - [ ] 1.3 Emit year-complete INFO summary with:
    - `year=... steps_executed=... seed=... adapter_version=... event=year_complete`
  - [ ] 1.4 Ensure marker names are consistent across all runner logs (`key=value` tokens)

- [ ] Task 2: Add adapter version runtime logs in `ComputationStep` (AC: #3, #5)
  - [ ] 2.1 Add module logger in `src/reformlab/orchestrator/computation_step.py`
  - [ ] 2.2 Emit INFO log during `execute()`:
    - `year=... step_name=computation adapter_version=...`
  - [ ] 2.3 Emit DEBUG computation context log:
    - `year=... step_name=computation row_count=...`

- [ ] Task 3: Add minimal execution trace metadata on result (AC: #6)
  - [ ] 3.1 Define stable metadata keys:
    - `STEP_EXECUTION_LOG_KEY = "step_execution_log"`
    - `SEED_LOG_KEY = "seed_log"`
  - [ ] 3.2 Collect ordered step execution records during `_run_year()`
  - [ ] 3.3 Collect per-year derived seeds during `run()`
  - [ ] 3.4 Merge trace fields into `OrchestratorResult.metadata` for success and failure paths

- [ ] Task 4: Add focused tests for logging and trace metadata (AC: all)
  - [ ] 4.1 Create `tests/orchestrator/test_logging.py` with `caplog` assertions for year, step, seed, and adapter markers
  - [ ] 4.2 Add test comparing two runs with different master seeds to assert visible seed differences in logs
  - [ ] 4.3 Add tests validating `seed_log` and `step_execution_log` structure/content on `OrchestratorResult.metadata`

- [ ] Task 5: Export constants and run quality gates (AC: all)
  - [ ] 5.1 Export `STEP_EXECUTION_LOG_KEY` and `SEED_LOG_KEY` from `src/reformlab/orchestrator/__init__.py`
  - [ ] 5.2 Run `ruff check src/reformlab/orchestrator tests/orchestrator`
  - [ ] 5.3 Run `mypy src/reformlab/orchestrator`
  - [ ] 5.4 Run targeted tests:
    - `pytest tests/orchestrator/test_logging.py tests/orchestrator/test_runner.py tests/orchestrator/test_computation_step.py`

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

1. **Structured runtime logs first (Tasks 1-2):** Add stable `key=value` markers for year/step/adapter logging without altering pipeline semantics.

2. **Minimal trace metadata second (Task 3):** Add in-memory execution trace (`seed_log`, `step_execution_log`) to `OrchestratorResult.metadata` for downstream governance stories.

3. **Searchable marker contract:** Use consistent markers (`year=`, `seed=`, `step_name=`, `adapter_version=`). Example:
   ```
   INFO  reformlab.orchestrator.runner: year=2024 seed=1234567890 master_seed=42 event=year_start
   DEBUG reformlab.orchestrator.runner: year=2024 step_index=1 step_total=3 step_name=computation event=step_start
   INFO  reformlab.orchestrator.computation_step: year=2024 step_name=computation adapter_version=openfisca-france-167.0.0
   DEBUG reformlab.orchestrator.runner: year=2024 step_index=1 step_total=3 step_name=computation event=step_end
   DEBUG reformlab.orchestrator.runner: year=2024 step_index=2 step_total=3 step_name=vintage_transition event=step_start
   ...
   INFO  reformlab.orchestrator.runner: year=2024 steps_executed=3 seed=1234567890 adapter_version=openfisca-france-167.0.0 event=year_complete
   ```

### Scope Guardrails

- **In scope:**
  - Structured logging of seed, step order, adapter version
  - Stable searchable log markers for debugging and reproducibility checks
  - Minimal in-memory execution trace in `OrchestratorResult.metadata`
  - Focused tests for log content and metadata structure

- **Out of scope:**
  - Manifest file generation (Story 5-1)
  - Log file persistence or rotation (infrastructure concern)
  - Log aggregation or analysis tools
  - Broad observability refactors beyond orchestrator/computation-step logging
  - Panel output formatting (Story 3-7)

### Testing Notes

- Use `caplog` fixture in pytest to capture and assert log messages
- Test at both INFO and DEBUG levels
- Verify required searchable markers appear in log output (`year=`, `seed=`, `step_name=`, `adapter_version=`)
- Validate metadata trace schema and ordering in `OrchestratorResult`
- Compare logs from runs with different seeds to verify visible seed deltas

### Project Structure Notes

- New code in `src/reformlab/orchestrator/runner.py` (enhanced logging)
- New code in `src/reformlab/orchestrator/computation_step.py` (adapter version logging)
- New constants in `src/reformlab/orchestrator/runner.py` (exported via `src/reformlab/orchestrator/__init__.py`)
- New tests in `tests/orchestrator/test_logging.py`
- No production modules added; this is enhancement of existing modules plus one focused test module

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
