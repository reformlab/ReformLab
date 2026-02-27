# Story 3.1: Implement Yearly Loop Orchestrator

Status: ready-for-dev

## Story

As a **policy analyst**,
I want **to run multi-year projections (10+ years) through a yearly loop orchestrator with a pluggable step pipeline**,
so that **I can analyze how environmental policies and their effects evolve over time through deterministic, reproducible simulations**.

## Acceptance Criteria

From backlog (BKL-301), aligned with FR13, FR18.

1. **AC-1: Execute step pipeline for each year in projection horizon**
   - Given a scenario with a 10-year horizon (e.g., 2025-2034), when the orchestrator runs, then it executes the step pipeline for each year from t to t+9 in order.
   - Each year receives the output state from the previous year as input.
   - Year execution order is strict: year t must complete before year t+1 begins.

2. **AC-2: Handle empty step pipeline gracefully**
   - Given an empty step pipeline (no registered steps), when the orchestrator runs, then it completes without error (no-op per year).
   - The orchestrator logs each year iteration even when no steps execute.

3. **AC-3: Halt on step failure with clear error context**
   - Given a step that raises an error at year t+3, when the orchestrator runs, then execution halts immediately.
   - The error message includes: failing step name, year when failure occurred, original error details, and partial results if any.

4. **AC-4: Deterministic yearly state transitions**
   - Given identical inputs, configuration, and seeds, when the orchestrator runs twice, then year-by-year outputs are bit-identical.
   - Random seeds (if any) are explicit, logged, and reproducible.

5. **AC-5: Integration with WorkflowConfig from Story 2.7**
   - Given a `WorkflowConfig` with `run_config.projection_years` and `run_config.start_year`, when the orchestrator runs, then it uses those values for the yearly loop bounds.
   - The orchestrator can be invoked through the `run_workflow()` handoff API when a runner is provided.

## Tasks / Subtasks

- [ ] Task 0: Validate prerequisites and environment
  - [ ] 0.1 Confirm Epic 2 stories are `done` or `review` in sprint-status.yaml (especially 2-7 workflow config)
  - [ ] 0.2 Review existing `orchestrator/__init__.py` placeholder
  - [ ] 0.3 Review `computation/adapter.py` interface for integration patterns
  - [ ] 0.4 Review `templates/workflow.py` for `WorkflowConfig` and `RunConfig` structures

- [ ] Task 1: Define orchestrator core types (AC: #1, #4, #5)
  - [ ] 1.1 Create `src/reformlab/orchestrator/types.py` with core dataclasses
  - [ ] 1.2 Define `YearState` dataclass:
    - `year`: int - The simulation year
    - `data`: dict[str, Any] - State data carried forward between years
    - `seed`: int | None - Random seed for this year (explicit, logged)
    - `metadata`: dict[str, Any] - Additional year-level metadata
  - [ ] 1.3 Define `StepResult` dataclass:
    - `step_name`: str - Name of the step that produced this result
    - `year`: int - Year this result applies to
    - `output_state`: dict[str, Any] - State updates from this step
    - `metadata`: dict[str, Any] - Step execution metadata (timing, etc.)
  - [ ] 1.4 Define `OrchestratorConfig` dataclass:
    - `start_year`: int - First year of projection
    - `end_year`: int - Last year of projection (inclusive)
    - `initial_state`: dict[str, Any] - Starting state for year 0
    - `seed`: int | None - Master random seed for determinism
    - `step_pipeline`: list[str] - Ordered list of registered step names
  - [ ] 1.5 Define `OrchestratorResult` dataclass:
    - `success`: bool - Whether orchestration completed
    - `yearly_states`: dict[int, YearState] - State at end of each year
    - `errors`: list[str] - Error messages if execution failed
    - `failed_year`: int | None - Year when failure occurred
    - `failed_step`: str | None - Step that caused failure
    - `metadata`: dict[str, Any] - Orchestration-level metadata

- [ ] Task 2: Define step interface (AC: #1, #2, #3)
  - [ ] 2.1 Create `src/reformlab/orchestrator/steps.py` with step protocol
  - [ ] 2.2 Define `OrchestratorStep` Protocol:
    - `name: str` property - Unique step identifier
    - `execute(year: int, state: YearState) -> StepResult` method
  - [ ] 2.3 Document step contract: steps must be pure functions of (year, state) for determinism
  - [ ] 2.4 Add `StepError` exception for step-level failures with context fields

- [ ] Task 3: Implement step registry (AC: #1, #2)
  - [ ] 3.1 Add `StepRegistry` class in `steps.py`
  - [ ] 3.2 Implement `register(step: OrchestratorStep)` method
  - [ ] 3.3 Implement `get(name: str) -> OrchestratorStep` method
  - [ ] 3.4 Implement `list_steps() -> list[str]` method
  - [ ] 3.5 Handle duplicate registration with clear error
  - [ ] 3.6 Create module-level default registry: `default_registry`

- [ ] Task 4: Implement yearly loop orchestrator core (AC: #1, #2, #3, #4)
  - [ ] 4.1 Create `src/reformlab/orchestrator/runner.py`
  - [ ] 4.2 Implement `Orchestrator` class:
    - `__init__(config: OrchestratorConfig, registry: StepRegistry | None)`
    - `run() -> OrchestratorResult` - Main execution method
    - `_run_year(year: int, state: YearState) -> YearState` - Single year execution
    - `_execute_step(step: OrchestratorStep, year: int, state: YearState) -> StepResult`
  - [ ] 4.3 Implement deterministic year iteration: `range(start_year, end_year + 1)`
  - [ ] 4.4 Implement state carry-forward: each year starts with previous year's end state
  - [ ] 4.5 Implement seed propagation: derive year-level seeds from master seed if provided
  - [ ] 4.6 Add logging for each year start/end and step execution

- [ ] Task 5: Implement error handling and partial results (AC: #3)
  - [ ] 5.1 Wrap step execution in try/except with context preservation
  - [ ] 5.2 On step failure, capture: step name, year, original exception, traceback
  - [ ] 5.3 Store partial results (completed years) in `OrchestratorResult`
  - [ ] 5.4 Define `OrchestratorError` exception with structured fields:
    - `year`: int
    - `step_name`: str
    - `original_error`: Exception
    - `partial_states`: dict[int, YearState]

- [ ] Task 6: Implement WorkflowConfig integration (AC: #5)
  - [ ] 6.1 Add `from_workflow_config(config: WorkflowConfig) -> OrchestratorConfig` factory
  - [ ] 6.2 Map `run_config.projection_years` + `run_config.start_year` to orchestrator bounds
  - [ ] 6.3 Create `OrchestratorRunner` class implementing the runner interface for `run_workflow()`
  - [ ] 6.4 Implement `OrchestratorRunner.run(request: dict) -> WorkflowResult`
  - [ ] 6.5 Register default runner in orchestrator module for workflow handoff

- [ ] Task 7: Add tests (AC: all)
  - [ ] 7.1 Create `tests/orchestrator/test_types.py` - Type validation tests
  - [ ] 7.2 Create `tests/orchestrator/test_steps.py` - Step registry tests
  - [ ] 7.3 Create `tests/orchestrator/test_runner.py` - Core orchestrator tests:
    - Test 10-year loop completes successfully
    - Test empty pipeline completes without error
    - Test step failure halts with correct error context
    - Test deterministic execution (same inputs = same outputs)
    - Test state carry-forward between years
    - Test seed propagation for reproducibility
  - [ ] 7.4 Create `tests/orchestrator/test_integration.py` - WorkflowConfig integration tests
  - [ ] 7.5 Add fixture for mock step implementations

- [ ] Task 8: Export APIs and finalize (AC: all)
  - [ ] 8.1 Update `src/reformlab/orchestrator/__init__.py` with public exports
  - [ ] 8.2 Add docstrings for all public APIs
  - [ ] 8.3 Run `ruff check` and `mypy` on orchestrator module
  - [ ] 8.4 Run full test suite: `pytest tests/orchestrator/`
  - [ ] 8.5 Verify all tests pass

## Dev Notes

### Architecture Alignment

**From architecture.md - Core Design:**
> The dynamic orchestrator is the core product — not a computation engine. OpenFisca handles policy calculations; this project handles everything above that.

**Step-Pluggable Dynamic Orchestrator:**
```
For each year t in [start_year .. end_year]:
  1. Run ComputationAdapter (OpenFisca tax-benefit for year t)
  2. Apply environmental policy templates (carbon tax, subsidies)
  3. Execute transition steps (pluggable pipeline):
     a. Vintage transitions (asset cohort aging, fleet turnover)
     b. State carry-forward (income updates, demographic changes)
     c. [Phase 2: Behavioral response adjustments]
  4. Record year-t results and manifest entry
  5. Feed updated state into year t+1
```

This story implements the outer yearly loop and step pipeline execution infrastructure. ComputationAdapter integration (3-5), vintage transitions (3-4), and carry-forward (3-3) are separate stories that plug into this infrastructure.

**Subsystem from architecture.md:**
> `orchestrator/`: Dynamic yearly loop with step-pluggable pipeline. Manages deterministic sequencing, seed control, and state transitions.

### Existing Code Patterns to Reuse

- **`src/reformlab/computation/adapter.py`:**
  - Protocol pattern for interfaces (`ComputationAdapter`)
  - `@runtime_checkable` decorator for duck typing
  - Type annotations with `from __future__ import annotations`

- **`src/reformlab/computation/types.py`:**
  - Frozen dataclass pattern for immutable data containers
  - `field(default_factory=dict)` for mutable defaults
  - Metadata dict pattern for extensibility

- **`src/reformlab/templates/workflow.py`:**
  - `WorkflowConfig`, `RunConfig` for configuration binding
  - `WorkflowResult` for result container pattern
  - `WorkflowError` for structured error reporting
  - `run_workflow()` runner injection pattern

- **`src/reformlab/templates/registry.py`:**
  - Registry pattern with `register()`, `get()`, `list()`
  - Error handling for missing/duplicate entries

### Previous Story Intelligence (Story 2.7)

From Story 2.7 completion notes:
- Workflow configuration schema provides `run_config.projection_years` and `run_config.start_year`
- `run_workflow()` accepts a `runner` parameter for execution delegation
- `prepare_workflow_request()` normalizes config into runtime request payload
- `WorkflowResult` is the standard return type for workflow execution

The orchestrator should implement a runner class that `run_workflow()` can delegate to.

### Git Intelligence

Recent commits show consistent patterns:
- Frozen dataclasses for immutable state
- Protocol interfaces for extensibility
- Structured error classes with actionable messages
- Comprehensive test coverage

### Project Structure Notes

**New files:**
- `src/reformlab/orchestrator/types.py` - Core dataclasses
- `src/reformlab/orchestrator/steps.py` - Step protocol and registry
- `src/reformlab/orchestrator/runner.py` - Orchestrator implementation
- `src/reformlab/orchestrator/errors.py` - Error classes
- `tests/orchestrator/test_types.py`
- `tests/orchestrator/test_steps.py`
- `tests/orchestrator/test_runner.py`
- `tests/orchestrator/test_integration.py`
- `tests/orchestrator/conftest.py` - Test fixtures

**Files to modify:**
- `src/reformlab/orchestrator/__init__.py` - Export public APIs

### Key Dependencies

- **Story 2.7 / BKL-207:** WorkflowConfig and run_workflow() for configuration binding (prerequisite)
- **Standard library:** `dataclasses`, `typing`, `logging`
- **Internal modules:**
  - `reformlab.templates.workflow` for WorkflowConfig, RunConfig, WorkflowResult

### Cross-Story Dependencies in Epic 3

- **Story 3-2 (BKL-302):** Defines the full step interface and registration mechanism - will refine/extend what we create here
- **Story 3-3 (BKL-303):** Carry-forward step - first step implementation, plugs into this infrastructure
- **Story 3-4 (BKL-304):** Vintage transition step - plugs into this infrastructure
- **Story 3-5 (BKL-305):** ComputationAdapter integration - integrates adapter calls into yearly loop
- **Story 3-6 (BKL-306):** Log seed controls - extends logging from this story
- **Story 3-7 (BKL-307):** Panel output - consumes orchestrator results

This story creates the foundation that all other Epic 3 stories build upon.

### Out-of-Scope Guardrails

- No ComputationAdapter calls in this story (Story 3-5)
- No vintage transition logic (Story 3-4)
- No carry-forward step implementation (Story 3-3)
- No panel output generation (Story 3-7)
- No manifest/lineage generation (Epic 5)
- No parallel step execution (single-threaded for determinism)

### Implementation Guidelines

**Orchestrator Core Pattern:**
```python
class Orchestrator:
    """Yearly loop orchestrator with step pipeline execution."""

    def __init__(
        self,
        config: OrchestratorConfig,
        registry: StepRegistry | None = None,
    ) -> None:
        self.config = config
        self.registry = registry or default_registry

    def run(self) -> OrchestratorResult:
        """Execute the full projection from start_year to end_year."""
        yearly_states: dict[int, YearState] = {}
        current_state = YearState(
            year=self.config.start_year - 1,
            data=self.config.initial_state,
            seed=self.config.seed,
        )

        for year in range(self.config.start_year, self.config.end_year + 1):
            try:
                current_state = self._run_year(year, current_state)
                yearly_states[year] = current_state
            except StepError as e:
                return OrchestratorResult(
                    success=False,
                    yearly_states=yearly_states,
                    errors=[str(e)],
                    failed_year=year,
                    failed_step=e.step_name,
                )

        return OrchestratorResult(success=True, yearly_states=yearly_states)
```

**Step Protocol:**
```python
@runtime_checkable
class OrchestratorStep(Protocol):
    """Interface for orchestrator pipeline steps."""

    @property
    def name(self) -> str:
        """Unique step identifier."""
        ...

    def execute(self, year: int, state: YearState) -> StepResult:
        """Execute step for given year and state."""
        ...
```

**Error Pattern (follow WorkflowError style):**
```python
class OrchestratorError(Exception):
    """Structured orchestrator error with context."""

    def __init__(
        self,
        *,
        summary: str,
        reason: str,
        year: int | None = None,
        step_name: str | None = None,
        partial_states: dict[int, YearState] | None = None,
    ) -> None:
        # ...
```

### Testing Standards

- Use `pytest` with orchestrator-specific fixtures
- Test determinism: run twice with same inputs, compare outputs
- Test error handling: inject failing steps, verify error context
- Test empty pipeline: should complete without error
- Test state carry-forward: verify year N+1 receives year N state
- Test WorkflowConfig integration: verify projection bounds are respected

### Performance Considerations

- Keep per-year overhead minimal (logging, state copying)
- State dictionaries should be shallow-copied, not deep-copied, unless deep copy is required for isolation
- Profile with 100-year projections to ensure linear scaling

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Step-Pluggable Dynamic Orchestrator]
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-301]
- [Source: _bmad-output/planning-artifacts/prd.md#FR13]
- [Source: _bmad-output/planning-artifacts/prd.md#FR18]
- [Source: src/reformlab/computation/adapter.py]
- [Source: src/reformlab/computation/types.py]
- [Source: src/reformlab/templates/workflow.py]
- [Source: _bmad-output/implementation-artifacts/2-7-implement-yaml-json-workflow-configuration.md]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
