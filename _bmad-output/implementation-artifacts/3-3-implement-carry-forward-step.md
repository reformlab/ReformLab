# Story 3.3: Implement Carry-Forward Step

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **framework developer**,
I want **to implement a carry-forward step that deterministically updates household state variables between years**,
so that **multi-year projections can model state transitions (income updates, demographic changes) with explicit period semantics and full reproducibility**.

## Acceptance Criteria

From backlog (BKL-303), aligned with FR14, FR17, NFR10.

1. **AC-1: Carry-forward step executes deterministic state updates between years**
   - Given household state at year t, when carry-forward executes, then state variables are updated for year t+1 according to configured rules.
   - The step implements the `OrchestratorStep` protocol from Story 3-2.

2. **AC-2: Identical inputs and seeds produce bit-identical outputs**
   - Given identical inputs and seeds, when carry-forward runs twice, then outputs are bit-identical.
   - Determinism is maintained across runs on the same machine.

3. **AC-3: Configuration requires explicit period semantics (NFR10 compliance)**
   - Given no explicit period semantics in configuration, when carry-forward is configured, then validation rejects the configuration with a clear error message.
   - Configuration must explicitly specify the period/year behavior for each rule.

4. **AC-4: Step integrates with orchestrator pipeline from Stories 3-1 and 3-2**
   - Given a configured CarryForwardStep, when registered with StepRegistry and executed via Orchestrator, then it executes correctly in the yearly pipeline.
   - Given multiple registered steps with dependencies, when `depends_on` is declared, then pipeline order honors dependency constraints deterministically.

5. **AC-5: Carry-forward rules are configurable per state variable**
   - Given a configuration with multiple state variables (income, household_size, etc.), when carry-forward runs, then each variable is updated according to its specific rule.
   - Supported rule types: `static` (no change), `scale` (multiply by factor), `increment` (add value), `custom` (callable).

## Dependencies

- **Required prior stories:**
  - Story 3-1 (BKL-301): Yearly loop orchestrator - provides `Orchestrator`, `YearState`, `OrchestratorConfig`
  - Story 3-2 (BKL-302): Step interface - provides `OrchestratorStep` Protocol, `StepRegistry`, `@step` decorator
- **Current prerequisite status (from `_bmad-output/implementation-artifacts/sprint-status.yaml`, checked 2026-02-27):**
  - `3-1-implement-yearly-loop-orchestrator`: `done`
  - `3-2-define-orchestrator-step-interface`: `done`
- **Follow-on stories:**
  - Story 3-4 (BKL-304): Vintage transition step - will use carry-forward as dependency
  - Story 3-5 (BKL-305): ComputationAdapter integration - orchestrates adapter calls alongside carry-forward

## Tasks / Subtasks

- [x] Task 0: Confirm prerequisites and baseline (AC: dependency check)
  - [x] 0.1 Verify Story 3-1 and 3-2 status is `done` or `review`
  - [x] 0.2 Confirm `OrchestratorStep` protocol and `StepRegistry` are available in `src/reformlab/orchestrator/step.py`
  - [x] 0.3 Review `YearState` dataclass to understand state data structure
  - [x] 0.4 Record dependency verification evidence in Dev Agent Record before starting implementation

- [x] Task 1: Define carry-forward configuration schema (AC: #3, #5)
  - [x] 1.1 Create `src/reformlab/orchestrator/carry_forward.py`
  - [x] 1.2 Define `CarryForwardRule` dataclass with:
    - `variable: str` - name of state variable to update
    - `rule_type: Literal["static", "scale", "increment", "custom"]`
    - `period_semantics: str` - explicit period specification (NFR10 compliance)
    - `value: float | None` - for scale/increment rules
    - `custom_fn: Callable | None` - for custom rules
  - [x] 1.3 Define `CarryForwardConfig` dataclass with:
    - `rules: tuple[CarryForwardRule, ...]`
    - `strict_period: bool = True` - enforce period semantics
  - [x] 1.4 Add config validation to reject missing period semantics

- [x] Task 2: Implement CarryForwardStep class (AC: #1, #2, #4)
  - [x] 2.1 Implement `CarryForwardStep` satisfying `OrchestratorStep` protocol:
    - `name: str = "carry_forward"`
    - `depends_on: tuple[str, ...] = ()` (default: no dependencies)
    - `description: str | None`
    - `execute(year: int, state: YearState) -> YearState`
  - [x] 2.2 Implement deterministic rule application logic:
    - `static`: return value unchanged
    - `scale`: multiply by factor
    - `increment`: add value
    - `custom`: call custom_fn(year, value, state)
  - [x] 2.3 Ensure state updates create new `YearState` (immutability via `replace()`)
  - [x] 2.4 Use deterministic ordering of rule application (sorted by variable name)

- [x] Task 3: Add carry-forward specific errors (AC: #3)
  - [x] 3.1 Define `CarryForwardConfigError` for invalid configuration
  - [x] 3.2 Define `CarryForwardExecutionError` for runtime failures
  - [x] 3.3 Ensure errors include actionable messages with variable names

- [x] Task 4: Add determinism and reproducibility guarantees (AC: #2)
  - [x] 4.1 Document seed usage (carry-forward is deterministic without randomness by default)
  - [x] 4.2 If custom rules use randomness, require explicit seed from `state.seed`
  - [x] 4.3 Add determinism test: same input state produces identical output across runs

- [x] Task 5: Add tests for carry-forward step (AC: all)
  - [x] 5.1 Create `tests/orchestrator/test_carry_forward.py`
  - [x] 5.2 Test configuration validation:
    - Valid configurations pass
    - Missing period semantics rejected (NFR10)
    - Invalid rule types rejected
  - [x] 5.3 Test rule execution:
    - Static rule preserves value
    - Scale rule multiplies correctly
    - Increment rule adds correctly
    - Custom rule executes callable
  - [x] 5.4 Test determinism:
    - Same inputs produce identical outputs
    - Order-independent variable updates (sorted)
  - [x] 5.5 Test orchestrator integration:
    - CarryForwardStep works with StepRegistry
    - `depends_on` ordering is honored when carry-forward is combined with other registered steps
    - Step executes in pipeline with other steps

- [x] Task 6: Export APIs and run quality gates (AC: all)
  - [x] 6.1 Update `src/reformlab/orchestrator/__init__.py` exports (`CarryForwardStep`, `CarryForwardConfig`, `CarryForwardRule`)
  - [x] 6.2 Add concise docstrings for public APIs
  - [x] 6.3 Run `ruff check src/reformlab/orchestrator tests/orchestrator`
  - [x] 6.4 Run `mypy src/reformlab/orchestrator`
  - [x] 6.5 Run `pytest tests/orchestrator/test_carry_forward.py tests/orchestrator/test_runner.py`

## Dev Notes

### Architecture Alignment

**From architecture.md - Step-Pluggable Dynamic Orchestrator:**
> For each year t in [start_year .. end_year]:
>   3. Execute transition steps (pluggable pipeline):
>      b. State carry-forward (income updates, demographic changes)

**From architecture.md - Dynamic Execution Semantics:**
> Each year is explicit (`t`, `t+1`, ..., `t+n`), with deterministic carry-forward rules.
> Randomness is seed-controlled and logged in manifests.

**From PRD FR14:**
> System can carry forward state variables between yearly iterations.

**From PRD FR17:**
> System enforces deterministic sequencing and explicit random-seed control in dynamic runs.

**From PRD NFR10:**
> No implicit temporal assumptions — all period semantics are explicit in configuration.

### Existing Code to Build Upon

**From Story 3-2 (`src/reformlab/orchestrator/step.py`):**
```python
@runtime_checkable
class OrchestratorStep(Protocol):
    @property
    def name(self) -> str: ...
    def execute(self, year: int, state: YearState) -> YearState: ...

# Optional metadata
@property
def depends_on(self) -> tuple[str, ...]:
    return ()
```

**From Story 3-1 (`src/reformlab/orchestrator/types.py`):**
```python
@dataclass(frozen=True)
class YearState:
    year: int
    data: dict[str, Any] = field(default_factory=dict)
    seed: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
```

**State update pattern (immutability via replace):**
```python
from dataclasses import replace

# Create new state with updated data
new_data = dict(state.data)
new_data["income"] = state.data["income"] * 1.02  # 2% increase
return replace(state, data=new_data)
```

### Previous Story Intelligence (Story 3-2)

From Story 3-2 completion notes:
- `OrchestratorStep` Protocol implemented with `@runtime_checkable`
- `StepRegistry` with Kahn's algorithm for topological sorting
- `@step` decorator for function-based steps
- `adapt_callable()` for adapting bare callables
- Step errors: `StepValidationError`, `StepRegistrationError`, `CircularDependencyError`
- Orchestrator dispatches based on step type (protocol vs callable)
- 103 orchestrator tests pass

Key patterns established:
- Protocol-based step interface
- Frozen dataclasses for immutable state
- `depends_on` for step ordering
- Clear error classes with actionable messages

### Design Decisions

**CarryForwardRule Design:**
```python
@dataclass(frozen=True)
class CarryForwardRule:
    """Rule for updating a single state variable."""
    variable: str
    rule_type: Literal["static", "scale", "increment", "custom"]
    period_semantics: str  # e.g., "annual", "from_year_t_to_t+1"
    value: float | None = None  # For scale/increment
    custom_fn: Callable[[int, Any, YearState], Any] | None = None  # For custom

    def __post_init__(self) -> None:
        if not self.period_semantics:
            raise CarryForwardConfigError(
                f"Rule for '{self.variable}' missing period_semantics (NFR10)"
            )
```

**CarryForwardStep Design:**
```python
class CarryForwardStep:
    """Orchestrator step for deterministic state carry-forward."""

    def __init__(
        self,
        config: CarryForwardConfig,
        name: str = "carry_forward",
        depends_on: tuple[str, ...] = (),
    ) -> None:
        self._config = config
        self._name = name
        self._depends_on = depends_on

    @property
    def name(self) -> str:
        return self._name

    @property
    def depends_on(self) -> tuple[str, ...]:
        return self._depends_on

    def execute(self, year: int, state: YearState) -> YearState:
        new_data = dict(state.data)
        # Apply rules in sorted order for determinism
        for rule in sorted(self._config.rules, key=lambda r: r.variable):
            new_data[rule.variable] = self._apply_rule(rule, year, state)
        return replace(state, data=new_data)
```

**Rule Application Logic:**
```python
def _apply_rule(
    self, rule: CarryForwardRule, year: int, state: YearState
) -> Any:
    current_value = state.data.get(rule.variable)

    if rule.rule_type == "static":
        return current_value
    elif rule.rule_type == "scale":
        if current_value is None or rule.value is None:
            raise CarryForwardExecutionError(...)
        return current_value * rule.value
    elif rule.rule_type == "increment":
        if current_value is None or rule.value is None:
            raise CarryForwardExecutionError(...)
        return current_value + rule.value
    elif rule.rule_type == "custom":
        if rule.custom_fn is None:
            raise CarryForwardExecutionError(...)
        return rule.custom_fn(year, current_value, state)
```

### Project Structure Notes

**New file:**
- `src/reformlab/orchestrator/carry_forward.py` - CarryForwardStep, CarryForwardConfig, CarryForwardRule, errors

**Files to modify:**
- `src/reformlab/orchestrator/__init__.py` - Export new APIs

**New test file:**
- `tests/orchestrator/test_carry_forward.py`

### Testing Standards

- Use `pytest` with orchestrator-specific fixtures
- Test all rule types: static, scale, increment, custom
- Test NFR10 compliance (period semantics validation)
- Test determinism with identical inputs
- Test integration with StepRegistry and Orchestrator
- Ensure existing 103 orchestrator tests still pass

### Out-of-Scope Guardrails

- No vintage/cohort tracking (Story 3-4)
- No ComputationAdapter calls (Story 3-5)
- No manifest generation (Epic 5)
- No complex demographic modeling (just state variable updates)
- No market equilibrium or behavioral responses (Phase 2)

### Error Handling Patterns

Follow existing orchestrator error patterns:
```python
class CarryForwardConfigError(Exception):
    """Invalid carry-forward configuration."""

class CarryForwardExecutionError(Exception):
    """Error during carry-forward step execution."""
```

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Step-Pluggable Dynamic Orchestrator]
- [Source: _bmad-output/planning-artifacts/architecture.md#Dynamic Execution Semantics]
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-303]
- [Source: _bmad-output/planning-artifacts/prd.md#FR14]
- [Source: _bmad-output/planning-artifacts/prd.md#FR17]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR10]
- [Source: src/reformlab/orchestrator/step.py - OrchestratorStep Protocol]
- [Source: src/reformlab/orchestrator/types.py - YearState dataclass]
- [Source: src/reformlab/orchestrator/runner.py - Orchestrator class]
- [Source: _bmad-output/implementation-artifacts/3-2-define-orchestrator-step-interface.md]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

- **Task 0 Prerequisites Verified (2026-02-27):**
  - Story 3-1 `implement-yearly-loop-orchestrator`: `done`
  - Story 3-2 `define-orchestrator-step-interface`: `done`
  - `OrchestratorStep` protocol confirmed in `src/reformlab/orchestrator/step.py:43-70`
  - `StepRegistry` confirmed in `src/reformlab/orchestrator/step.py:242-378`
  - `YearState` dataclass confirmed in `src/reformlab/orchestrator/types.py:20-37` (frozen, with year, data, seed, metadata)
  - `@step` decorator and `adapt_callable` available for function-based steps
  - Step errors available: `StepValidationError`, `StepRegistrationError`, `CircularDependencyError`

- **Task 1-6 Completed (2026-02-27):**
  - Created `src/reformlab/orchestrator/carry_forward.py` with:
    - `CarryForwardRule`: frozen dataclass for rule configuration
    - `CarryForwardConfig`: frozen dataclass grouping rules
    - `CarryForwardStep`: OrchestratorStep implementation with deterministic rule application
    - `CarryForwardConfigError`: raised for invalid config (e.g., missing period_semantics)
    - `CarryForwardExecutionError`: raised for runtime failures
  - Rule types implemented: `static`, `scale`, `increment`, `custom`
  - NFR10 compliance: `period_semantics` required on all rules, validated in `__post_init__`
  - Determinism: rules sorted by variable name before application
  - Immutability: uses `replace()` to create new `YearState`
  - Created 38 tests in `tests/orchestrator/test_carry_forward.py`
  - All 144 orchestrator tests pass (103 existing + 38 new + 3 integration)
  - ruff check passed, mypy passed with no issues

### File List

**New Files:**
- `src/reformlab/orchestrator/carry_forward.py`
- `tests/orchestrator/test_carry_forward.py`

**Modified Files:**
- `src/reformlab/orchestrator/__init__.py`

## Change Log

- **2026-02-27**: Implemented CarryForwardStep with all rule types (static, scale, increment, custom). Added NFR10-compliant period semantics validation. Added 38 unit and integration tests. All 144 orchestrator tests pass.
