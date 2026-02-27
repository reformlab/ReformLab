# Story 3.2: Define Orchestrator Step Interface

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **framework developer**,
I want **to define a formal step interface (Protocol) and step registration mechanism for the orchestrator**,
so that **new step implementations (carry-forward, vintage transitions, computation adapter calls) can be added without modifying the orchestrator core, enabling extensible multi-year projections**.

## Acceptance Criteria

From backlog (BKL-302), aligned with FR14, FR16.

1. **AC-1: Custom step implementing the step interface integrates correctly**
   - Given a custom step class implementing the step interface (Protocol), when registered with the orchestrator, then it is called at the correct position in the pipeline for each year.
   - The step receives the current year and state, and returns updated state.

2. **AC-2: Steps execute in dependency order**
   - Given a step registered with dependencies on another step, when the pipeline is built, then steps execute in dependency order.
   - Dependency declaration is optional; steps without dependencies execute in registration order.

3. **AC-3: Invalid step interface produces clear error**
   - Given a step with an invalid interface (missing method or signature mismatch), when registered, then a clear error identifies the missing method or signature mismatch.
   - Registration fails fast with actionable error message before orchestrator execution begins.

4. **AC-4: Step registration mechanism is ergonomic**
   - Given the step registration API, when a developer registers a new step, then the API is intuitive and follows Python conventions (Protocol pattern, type hints).
   - Both class-based and function-based steps are supported.

5. **AC-5: Integration with existing Orchestrator from Story 3-1**
   - Given the new step interface, when the orchestrator runs, then it uses the formal step interface instead of the current `YearStep` callable alias.
   - Backward compatibility: existing callable steps continue to work during migration.

## Dependencies

- **Required prior stories:** BKL-301 (Story 3-1) must be `done` or `review` - provides the base orchestrator implementation.
- **Follow-on stories:** BKL-303, BKL-304, BKL-305 will implement concrete steps using this interface.

## Tasks / Subtasks

- [ ] Task 1: Define Step Protocol interface (AC: #1, #3, #4)
  - [ ] 1.1 Create `src/reformlab/orchestrator/step.py` with core step protocol
  - [ ] 1.2 Define `OrchestratorStep` Protocol with required methods:
    - `name` property: str - Unique identifier for the step
    - `execute(year: int, state: YearState) -> YearState` - Core execution method
  - [ ] 1.3 Add optional methods/properties to Protocol:
    - `depends_on` property: tuple[str, ...] - Step dependencies (default empty)
    - `description` property: str | None - Human-readable description
  - [ ] 1.4 Add `@runtime_checkable` decorator for duck typing validation

- [ ] Task 2: Implement step registration mechanism (AC: #2, #3, #4)
  - [ ] 2.1 Create `StepRegistry` class for step management:
    - `register(step: OrchestratorStep) -> None` - Register a step
    - `get(name: str) -> OrchestratorStep` - Retrieve step by name
    - `build_pipeline() -> tuple[OrchestratorStep, ...]` - Build ordered pipeline
  - [ ] 2.2 Implement dependency-aware pipeline ordering using topological sort
  - [ ] 2.3 Detect and report circular dependencies with clear error message
  - [ ] 2.4 Validate step interface on registration (fail-fast)

- [ ] Task 3: Create function-based step adapter (AC: #4, #5)
  - [ ] 3.1 Implement `@step` decorator to convert functions to OrchestratorStep
  - [ ] 3.2 Support decorator parameters: `name`, `depends_on`, `description`
  - [ ] 3.3 Maintain backward compatibility with existing `YearStep` callable alias

- [ ] Task 4: Integrate with Orchestrator (AC: #1, #5)
  - [ ] 4.1 Update `OrchestratorConfig` to accept `StepRegistry` or step pipeline
  - [ ] 4.2 Modify `Orchestrator._execute_step()` to use `OrchestratorStep.execute()`
  - [ ] 4.3 Update step name extraction to use `OrchestratorStep.name`
  - [ ] 4.4 Preserve backward compatibility: wrap bare callables in adapter

- [ ] Task 5: Add comprehensive tests (AC: all)
  - [ ] 5.1 Create `tests/orchestrator/test_step.py`:
    - Test Protocol validation (valid/invalid implementations)
    - Test class-based step registration and execution
    - Test function-based step via `@step` decorator
    - Test step name uniqueness enforcement
  - [ ] 5.2 Create `tests/orchestrator/test_registry.py`:
    - Test dependency ordering (topological sort)
    - Test circular dependency detection
    - Test registration validation (fail-fast)
    - Test pipeline building
  - [ ] 5.3 Update `tests/orchestrator/test_runner.py`:
    - Test new OrchestratorStep interface integration
    - Test backward compatibility with bare callables

- [ ] Task 6: Export APIs and finalize (AC: all)
  - [ ] 6.1 Update `src/reformlab/orchestrator/__init__.py` with exports:
    - `OrchestratorStep` Protocol
    - `StepRegistry` class
    - `step` decorator
  - [ ] 6.2 Add docstrings for all public APIs
  - [ ] 6.3 Run `ruff check` and `mypy` on orchestrator module
  - [ ] 6.4 Run full test suite: `pytest tests/orchestrator/`
  - [ ] 6.5 Verify all tests pass and no regressions

## Dev Notes

### Architecture Alignment

**From architecture.md - Step-Pluggable Dynamic Orchestrator:**
> Steps are registered as plugins. Phase 1 ships vintage transitions and state carry-forward. Phase 2 adds behavioral response steps without modifying the orchestrator core.

This story implements the "registered as plugins" infrastructure. The orchestrator core (Story 3-1) provides the yearly loop; this story provides the step interface and registration mechanism that makes it pluggable.

**Subsystem from architecture.md:**
> `orchestrator/`: Dynamic yearly loop with step-pluggable pipeline. Manages deterministic sequencing, seed control, and state transitions.

### Existing Code to Build Upon

**From Story 3-1 (`src/reformlab/orchestrator/types.py`):**
```python
# Current simple callable alias (to be formalized):
YearStep = Callable[[int, "YearState"], "YearState"]

# Existing types to reuse:
@dataclass(frozen=True)
class YearState:
    year: int
    data: dict[str, Any]
    seed: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
```

**From Story 3-1 (`src/reformlab/orchestrator/runner.py`):**
```python
# Current step execution (to be updated):
def _execute_step(self, step: YearStep, year: int, state: YearState) -> YearState:
    step_name = getattr(step, "__name__", str(step))
    result = step(year, state)
    return result
```

**Protocol pattern from `src/reformlab/computation/adapter.py`:**
```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class ComputationAdapter(Protocol):
    def compute(self, ...) -> ComputationResult: ...
    def version(self) -> str: ...
```

### Previous Story Intelligence (Story 3-1)

From Story 3-1 completion notes:
- `YearState`, `OrchestratorConfig`, `OrchestratorResult` dataclasses exist in `types.py`
- `Orchestrator` class with `run()`, `_run_year()`, `_execute_step()` methods exist in `runner.py`
- `OrchestratorError` structured exception exists in `errors.py`
- Step execution uses `getattr(step, "__name__", str(step))` for step name extraction
- 48 orchestrator tests exist - ensure no regressions

Key patterns established:
- Frozen dataclasses for immutable state
- Protocol interfaces for extensibility
- Structured error classes with actionable messages
- Comprehensive test coverage

### Design Decisions

**Step Protocol Design:**
```python
@runtime_checkable
class OrchestratorStep(Protocol):
    """Protocol for orchestrator pipeline steps."""

    @property
    def name(self) -> str:
        """Unique identifier for this step."""
        ...

    def execute(self, year: int, state: YearState) -> YearState:
        """Execute the step for a given year.

        Args:
            year: Current simulation year.
            state: Current year state.

        Returns:
            Updated state after step execution.
        """
        ...

    @property
    def depends_on(self) -> tuple[str, ...]:
        """Step names this step depends on (optional)."""
        return ()
```

**Function Decorator Design:**
```python
@step(name="my_step", depends_on=("carry_forward",))
def my_step_function(year: int, state: YearState) -> YearState:
    # Step implementation
    return state
```

**Registry Pattern:**
```python
registry = StepRegistry()
registry.register(CarryForwardStep())
registry.register(VintageTransitionStep())

pipeline = registry.build_pipeline()  # Topologically sorted
```

### Dependency Ordering Algorithm

Use Kahn's algorithm for topological sort:
1. Build adjacency list from `depends_on` declarations
2. Track in-degree (number of dependencies) for each step
3. Start with steps that have zero in-degree
4. Process queue, decrementing in-degree of dependents
5. Detect cycle if not all steps are processed

### Project Structure Notes

**New files:**
- `src/reformlab/orchestrator/step.py` - OrchestratorStep Protocol, StepRegistry, @step decorator

**Files to modify:**
- `src/reformlab/orchestrator/types.py` - May import new step types (or keep separate)
- `src/reformlab/orchestrator/runner.py` - Update to use OrchestratorStep
- `src/reformlab/orchestrator/__init__.py` - Export new APIs

**Test files:**
- `tests/orchestrator/test_step.py` (new)
- `tests/orchestrator/test_registry.py` (new)
- `tests/orchestrator/test_runner.py` (update)

### Testing Standards

- Use `pytest` with orchestrator-specific fixtures from Story 3-1
- Test Protocol validation with valid and invalid implementations
- Test topological sort with various dependency graphs
- Test circular dependency detection with clear error messages
- Test backward compatibility with existing bare callables
- Ensure all 683+ existing tests continue to pass

### Out-of-Scope Guardrails

- No concrete step implementations (carry-forward is Story 3-3, vintage is Story 3-4)
- No ComputationAdapter integration (Story 3-5)
- No manifest/lineage generation (Epic 5)
- No parallel step execution (single-threaded for determinism)
- No dynamic step loading from external packages (keep simple for MVP)

### Error Handling Patterns

Follow `OrchestratorError` pattern for step-related errors:
```python
class StepRegistrationError(Exception):
    """Error during step registration."""

class StepValidationError(Exception):
    """Step does not implement required interface."""

class CircularDependencyError(Exception):
    """Circular dependency detected in step pipeline."""
```

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Step-Pluggable Dynamic Orchestrator]
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-302]
- [Source: _bmad-output/planning-artifacts/prd.md#FR14]
- [Source: _bmad-output/planning-artifacts/prd.md#FR16]
- [Source: src/reformlab/orchestrator/types.py]
- [Source: src/reformlab/orchestrator/runner.py]
- [Source: src/reformlab/computation/adapter.py - Protocol pattern reference]
- [Source: _bmad-output/implementation-artifacts/3-1-implement-yearly-loop-orchestrator.md]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

