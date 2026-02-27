# Story 3.5: Integrate ComputationAdapter Calls

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **framework developer**,
I want **to integrate ComputationAdapter calls into the orchestrator yearly loop**,
so that **analysts can run multi-year simulations that execute tax-benefit computations through the adapter interface at each year**.

## Acceptance Criteria

From backlog (BKL-305), aligned with FR13, FR2, NFR6, NFR7.

Scope note: this story adds a `ComputationStep` that invokes the adapter at each yearly iteration. It integrates with the existing orchestrator step pipeline (Story 3-2) and operates alongside transition steps (Stories 3-3, 3-4). Panel output assembly is deferred to Story 3-7.

1. **AC-1: ComputationStep invokes adapter per year**
   - Given a configured `ComputationAdapter`, when the orchestrator runs year `t`, then `ComputationStep` calls the adapter's `compute()` method with the correct population, policy, and period for that year.
   - The `ComputationResult` is stored in `YearState.data` under a stable key (`"computation_result"`).

2. **AC-2: Step satisfies orchestrator plugin contract**
   - `ComputationStep` implements the `OrchestratorStep` protocol from Story 3-2 (`name`, `execute`).
   - Given registration in `StepRegistry`, when a pipeline is built and executed, then the step runs in the correct position according to declared dependencies.
   - Default MVP pipeline order: `computation` runs before `vintage_transition` and `carry_forward` (adapter computes first, then state transitions apply), enforced by deterministic registration order and/or explicit `depends_on=("computation",)` edges on transition steps.

3. **AC-3: Mock adapter enables full pipeline testing**
   - Given a `MockAdapter` configured with test outputs, when the orchestrator runs the full yearly loop, then the pipeline completes using mock results without requiring OpenFisca installed.
   - Test suite validates end-to-end orchestration with mock adapter, including integration with vintage and carry-forward steps.

4. **AC-4: Adapter errors include year and version context**
   - Given an adapter that fails at year `t+2`, when the orchestrator catches the error, then the error message includes the adapter version, year, and failure details.
   - Partial results (completed years) are preserved and accessible in `OrchestratorResult.yearly_states`.

5. **AC-5: Determinism and logging requirements are met**
   - Given identical inputs (population, policy, seed), when the step runs twice, then outputs are identical (NFR6).
   - Adapter version is logged per yearly step in the `YearState.metadata` for reproducibility governance (NFR7).
   - The computation step records execution metadata (adapter version, period, row count) in the year state.

## Dependencies

- **Required prior stories (core implementation):**
  - Story 1-1 (BKL-101): ComputationAdapter interface and OpenFiscaAdapter - provides `ComputationAdapter` protocol, `MockAdapter`, `ComputationResult`, `PopulationData`, `PolicyConfig`
  - Story 3-1 (BKL-301): Yearly loop orchestrator - provides `Orchestrator`, `YearState`, `OrchestratorConfig`
  - Story 3-2 (BKL-302): Step interface - provides `OrchestratorStep` Protocol, `StepRegistry`, `@step` decorator
- **Required for full-pipeline integration coverage:**
  - Story 3-3 (BKL-303): Carry-forward step - established transition-step implementation pattern
  - Story 3-4 (BKL-304): Vintage transition step - completed, provides additional pipeline step context
- **Current prerequisite status (from `_bmad-output/implementation-artifacts/sprint-status.yaml`, checked 2026-02-27):**
  - `1-1-define-computationadapter-interface-and-openfiscaadapter-implementation`: `done`
  - `3-1-implement-yearly-loop-orchestrator`: `done`
  - `3-2-define-orchestrator-step-interface`: `done`
  - `3-3-implement-carry-forward-step`: `done`
  - `3-4-implement-vintage-transition-step`: `done`
- **Follow-on stories:**
  - Story 3-6 (BKL-306): Log seed controls and adapter version - extends logging requirements
  - Story 3-7 (BKL-307): Panel output - consumes yearly computation results to assemble output datasets

## Tasks / Subtasks

- [ ] Task 0: Confirm prerequisites and review existing patterns (AC: dependency check)
  - [ ] 0.1 Verify all prerequisite stories are `done` in `sprint-status.yaml`
  - [ ] 0.2 Review `ComputationAdapter` protocol and `MockAdapter` in `src/reformlab/computation/`
  - [ ] 0.3 Review `OrchestratorStep` and `StepRegistry` contracts in `src/reformlab/orchestrator/step.py`
  - [ ] 0.4 Review `YearState` data contract in `src/reformlab/orchestrator/types.py`
  - [ ] 0.5 Review carry-forward and vintage transition step patterns for consistency

- [ ] Task 1: Define computation step types and errors (AC: #1, #4)
  - [ ] 1.1 Create `src/reformlab/orchestrator/computation_step.py` with:
    - `ComputationStepError` for adapter-related failures with context
  - [ ] 1.2 Define stable keys for yearly computation payloads:
    - `COMPUTATION_RESULT_KEY = "computation_result"` (stored in `YearState.data`)
    - `COMPUTATION_METADATA_KEY = "computation_metadata"` (stored in `YearState.metadata`)

- [ ] Task 2: Implement `ComputationStep` (AC: #1, #2, #5)
  - [ ] 2.1 Implement `ComputationStep` class implementing `OrchestratorStep` protocol:
    - Constructor accepts: `adapter: ComputationAdapter`, `population: PopulationData`, `policy: PolicyConfig`
    - `name` property returns `"computation"`
    - Optional `depends_on` defaults to empty tuple (computation is independent; order is then controlled by deterministic registration order unless explicit dependency edges are configured)
  - [ ] 2.2 Implement `execute(year, state)` method:
    - Call `adapter.compute(population, policy, year)`
    - Store `ComputationResult` in `YearState.data[COMPUTATION_RESULT_KEY]`
    - Store execution metadata (adapter version, period, row count) in `YearState.metadata[COMPUTATION_METADATA_KEY]`
    - Return new immutable state via `replace(state, data=..., metadata=...)`
  - [ ] 2.3 Implement error handling:
    - Catch adapter exceptions and wrap with `ComputationStepError`
    - Include adapter version, year, and original error details in error message
    - Preserve exception chain with `from e`

- [ ] Task 3: Add tests for behavior, errors, and integration (AC: all)
  - [ ] 3.1 Create `tests/orchestrator/test_computation_step.py` covering:
    - Step protocol conformance (name, execute signature)
    - Correct adapter invocation per year
    - Result storage in `YearState.data`
    - Metadata recording in `YearState.metadata[COMPUTATION_METADATA_KEY]`
  - [ ] 3.2 Add error handling tests:
    - Adapter failure produces `ComputationStepError` with context
    - Error includes adapter version and year
    - Original error preserved in chain
  - [ ] 3.3 Create `tests/orchestrator/test_computation_integration.py` covering:
    - Full pipeline with MockAdapter + VintageTransitionStep + CarryForwardStep
    - Multi-year execution produces computation results for each year
    - Pipeline ordering: computation -> vintage -> carry_forward
    - Partial results (completed years) preserved on year `t+2` adapter failure

- [ ] Task 4: Export API and run quality gates (AC: all)
  - [ ] 4.1 Update `src/reformlab/orchestrator/__init__.py` exports:
    - Add `ComputationStep`, `ComputationStepError`
    - Add `COMPUTATION_RESULT_KEY`, `COMPUTATION_METADATA_KEY` constants
  - [ ] 4.2 Add concise docstrings for public APIs
  - [ ] 4.3 Run `ruff check src/reformlab/orchestrator tests/orchestrator`
  - [ ] 4.4 Run `mypy src/reformlab/orchestrator`
  - [ ] 4.5 Run targeted tests: `pytest tests/orchestrator/test_computation_step.py tests/orchestrator/test_computation_integration.py tests/orchestrator/test_runner.py tests/computation/test_mock_adapter.py`

## Dev Notes

### Architecture Alignment

**From architecture.md - Step-Pluggable Dynamic Orchestrator:**
> For each year t in [start_year .. end_year]:
>   1. Run ComputationAdapter (OpenFisca tax-benefit for year t)
>   2. Apply environmental policy templates (carbon tax, subsidies)
>   3. Execute transition steps (pluggable pipeline):
>      a. Vintage transitions (asset cohort aging, fleet turnover)
>      b. State carry-forward (income updates, demographic changes)

**From architecture.md - Computation Adapter Pattern:**
> The orchestrator never calls OpenFisca directly. All tax-benefit computation goes through a clean adapter interface.

**From backlog BKL-305:**
> Integrate ComputationAdapter calls into orchestrator yearly loop
> - Given a configured OpenFiscaAdapter, when the orchestrator runs year t, then the adapter's compute() is called with the correct population and policy for that year.
> - Given a mock adapter, when the orchestrator runs, then the full yearly loop completes using mock results.
> - Given an adapter that fails at year t+2, when the orchestrator runs, then the error includes the adapter version, year, and failure details.

### Existing Code Patterns to Follow

- `src/reformlab/orchestrator/step.py`
  - `OrchestratorStep` protocol: requires `name` property and `execute(year, state)` method
  - `StepRegistry` topological ordering with deterministic tie-break by registration order
- `src/reformlab/orchestrator/types.py`
  - `YearState` immutable dataclass with `data: dict[str, Any]` and `metadata: dict[str, Any]`
  - Use `replace(state, data=..., metadata=...)` for immutable updates
- `src/reformlab/orchestrator/carry_forward.py`
  - Transition-step implementation pattern (`__slots__`, explicit errors, deterministic behavior)
- `src/reformlab/vintage/transition.py`
  - Step plugin example with config validation and stable state keys
- `src/reformlab/computation/mock_adapter.py`
  - `MockAdapter` with call logging for test verification
  - Returns `ComputationResult` with configurable output table

### Pipeline Ordering Strategy

The step pipeline should execute in this order per year:
1. **computation** - Invoke adapter to compute tax-benefit results for year t
2. **vintage_transition** - Age cohorts and apply fleet turnover rules
3. **carry_forward** - Update demographic and income state variables

This ordering matches the currently implemented step sequence in the architecture (computation before transition steps). The `ComputationStep` should declare no dependencies (runs first), while vintage and carry-forward steps can optionally depend on computation if their logic needs adapter results.

Architecture also includes environmental template application between computation and transition steps. That template-layer integration is out of scope for this story and remains covered by EPIC-2 + later orchestration wiring stories.

For MVP, computation results are stored in state but not yet consumed by transition steps. Story 3-7 (panel output) will aggregate these results. Future stories in EPIC-4 (indicators) will consume the computation results.

### State Key Design

```python
# Stable keys for computation data in YearState.data
COMPUTATION_RESULT_KEY = "computation_result"  # Full ComputationResult object

# Stable key for computation metadata payload in YearState.metadata
COMPUTATION_METADATA_KEY = "computation_metadata"
# Computation metadata payload fields:
# - "adapter_version": str - version of adapter used
# - "computation_period": int - period passed to compute()
# - "computation_row_count": int - rows in output table
```

### Error Handling Pattern

```python
class ComputationStepError(Exception):
    """Error during computation step execution."""
    def __init__(
        self,
        message: str,
        year: int,
        adapter_version: str,
        original_error: Exception | None = None,
    ) -> None:
        self.year = year
        self.adapter_version = adapter_version
        self.original_error = original_error
        super().__init__(message)
```

The orchestrator's existing error handling will wrap this in `OrchestratorError` with partial state preservation.

### Scope Guardrails

- In scope:
  - `ComputationStep` implementing `OrchestratorStep` protocol
  - Adapter invocation with population, policy, and period
  - Result storage in `YearState.data`
  - Error handling with adapter context
  - Integration tests with `MockAdapter`
- Out of scope:
  - Panel output formatting/export (Story 3-7)
  - Seed logging infrastructure (Story 3-6)
  - Environmental policy template integration (EPIC-2 templates applied separately)
  - Indicator computation from results (EPIC-4)

### Testing Notes

- Use `MockAdapter` for all unit and integration tests - no OpenFisca dependency
- Verify call_log on `MockAdapter` to confirm correct invocation parameters
- Test multi-year pipelines with computation + vintage + carry_forward steps
- Verify partial state preservation when adapter failure occurs at year `t+2`
- Assert determinism by running the same configuration twice and comparing results

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Computation Adapter Pattern]
- [Source: _bmad-output/planning-artifacts/architecture.md#Step-Pluggable Dynamic Orchestrator]
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-305]
- [Source: _bmad-output/planning-artifacts/prd.md#FR2]
- [Source: _bmad-output/planning-artifacts/prd.md#FR13]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR6]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR7]
- [Source: src/reformlab/computation/adapter.py]
- [Source: src/reformlab/computation/types.py]
- [Source: src/reformlab/computation/mock_adapter.py]
- [Source: src/reformlab/orchestrator/step.py]
- [Source: src/reformlab/orchestrator/types.py]
- [Source: src/reformlab/orchestrator/runner.py]
- [Source: src/reformlab/orchestrator/carry_forward.py]
- [Source: src/reformlab/vintage/transition.py]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
