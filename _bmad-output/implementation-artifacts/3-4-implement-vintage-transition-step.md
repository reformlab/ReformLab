# Story 3.4: Implement Vintage Transition Step

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **framework developer**,
I want **to implement a vintage transition step that ages and turns over asset cohorts across years**,
so that **analysts can model fleet evolution in multi-year simulations for environmental policy analysis**.

## Acceptance Criteria

From backlog (BKL-304), aligned with FR15, FR16, NFR6, NFR7.

Scope note: this story implements one MVP asset class (`vehicle`) in the `vintage/` subsystem and integrates it as a pluggable orchestrator step. It does not implement panel dataset assembly (Story 3-7).

1. **AC-1: Vintage transition updates cohort state for one year**
   - Given a vehicle vintage state at year `t`, when `VintageTransitionStep` runs, then all cohorts age by one year (`age += 1`), cohorts above configured retirement age are removed, and new cohorts (`age = 0`) are added based on configured entry rules.
   - The transition result is stored back into `YearState.data` under a stable key (`"vintage_vehicle"`).

2. **AC-2: Transition behavior is configuration-driven and validated**
   - Given a `VintageConfig` for `asset_class="vehicle"`, when the step is initialized, then required transition settings (entry and retirement parameters) are validated and invalid configs raise `VintageConfigError` with actionable messages.
   - Given valid configuration, when transition executes, then rule application matches configured parameters.

3. **AC-3: Step satisfies orchestrator plugin contract**
   - `VintageTransitionStep` implements the `OrchestratorStep` protocol from Story 3-2 (`name`, `execute`).
   - Given registration in `StepRegistry`, when a pipeline is built and executed by the orchestrator, then the step runs in deterministic pipeline order.
   - For Epic-3 architecture alignment, when vintage is registered before carry-forward with no explicit dependency edge, pipeline order preserves `vintage_transition` before `carry_forward`.

4. **AC-4: Determinism and reproducibility requirements are met**
   - Given identical input state, config, and seed, when the step runs twice on the same machine, then outputs are bit-identical (NFR6).
   - Implementation avoids nondeterministic iteration (for example, deterministic sorting of cohorts/rules) and documents reproducibility assumptions for cross-machine runs with pinned Python/dependency versions (NFR7).

5. **AC-5: Downstream consumers can read yearly vintage composition**
   - Given yearly orchestrator outputs, vintage composition (cohort counts and age distribution) is available in the year state structure for downstream stories (for example, Story 3-7 panel output and EPIC-4 indicators).
   - This story provides state shape and extraction helpers only; no panel formatting/export logic is implemented here.

## Dependencies

- **Required prior stories:**
  - Story 3-1 (BKL-301): Yearly loop orchestrator - provides `Orchestrator`, `YearState`, `OrchestratorConfig`
  - Story 3-2 (BKL-302): Step interface - provides `OrchestratorStep` Protocol, `StepRegistry`, `@step` decorator
  - Story 3-3 (BKL-303): Carry-forward step - established deterministic transition-step implementation pattern
- **Current prerequisite status (from `_bmad-output/implementation-artifacts/sprint-status.yaml`, checked 2026-02-27):**
  - `3-1-implement-yearly-loop-orchestrator`: `done`
  - `3-2-define-orchestrator-step-interface`: `done`
  - `3-3-implement-carry-forward-step`: `done`
- **Follow-on stories:**
  - Story 3-5 (BKL-305): ComputationAdapter integration - orchestrates adapter calls alongside transition steps
  - Story 3-7 (BKL-307): Panel output - consumes yearly vintage state to assemble output datasets

## Tasks / Subtasks

- [x] Task 0: Confirm prerequisites and implementation boundaries (AC: dependency check)
  - [x] 0.1 Verify Story 3-1, 3-2, and 3-3 status is `done` in `sprint-status.yaml`
  - [x] 0.2 Review `OrchestratorStep` and `StepRegistry` contracts in `src/reformlab/orchestrator/step.py`
  - [x] 0.3 Review `YearState` data contract in `src/reformlab/orchestrator/types.py`
  - [x] 0.4 Record boundary note: no panel-output generation in this story

- [x] Task 1: Define vintage domain types and errors (AC: #1, #5)
  - [x] 1.1 Create `src/reformlab/vintage/types.py` with immutable dataclasses:
    - `VintageCohort` (age, count, attributes)
    - `VintageState` (asset_class, cohorts, optional metadata)
    - `VintageSummary` (derived metrics used by downstream consumers)
  - [x] 1.2 Create `src/reformlab/vintage/errors.py`:
    - `VintageConfigError`
    - `VintageTransitionError`
  - [x] 1.3 Keep MVP scope to one implemented asset class (`vehicle`) while leaving extension points for future classes

- [x] Task 2: Define and validate vintage configuration (AC: #2)
  - [x] 2.1 Create `src/reformlab/vintage/config.py` with:
    - `VintageTransitionRule` (rule type + parameters)
    - `VintageConfig` (asset class, transition rules, retirement settings, optional initial state)
  - [x] 2.2 Validate config invariants with explicit errors:
    - required rule coverage for aging/entry/retirement behavior
    - non-negative counts/rates and valid age bounds
    - required `asset_class == "vehicle"` for MVP implementation path
  - [x] 2.3 Ensure validation messages include actionable fix context

- [x] Task 3: Implement `VintageTransitionStep` (AC: #1, #3, #4, #5)
  - [x] 3.1 Create `src/reformlab/vintage/transition.py` with `VintageTransitionStep` implementing `OrchestratorStep`
  - [x] 3.2 Implement deterministic transition sequence in `execute(year, state)`:
    - age existing cohorts
    - apply retirement/removal by configured max age
    - add entry cohorts (`age = 0`) from config/state inputs
  - [x] 3.3 Read/write vintage state via stable `YearState.data["vintage_vehicle"]` contract
  - [x] 3.4 Return new immutable state via `replace(state, data=...)`
  - [x] 3.5 Do not hard-code dependency on carry-forward; rely on pipeline build order/declared dependencies from orchestrator composition

- [x] Task 4: Add tests for behavior, determinism, and integration (AC: all)
  - [x] 4.1 Create `tests/vintage/test_config.py` for config validation and error paths
  - [x] 4.2 Create `tests/vintage/test_transition.py` covering:
    - cohort aging
    - entry cohort creation
    - retirement/removal behavior
    - deterministic outputs for identical inputs/seeds
  - [x] 4.3 Create `tests/vintage/test_integration.py` covering:
    - `StepRegistry` registration and orchestrator execution
    - pipeline order scenario where vintage is registered before carry-forward
    - yearly state key visibility for downstream consumption

- [x] Task 5: Export API and run quality gates (AC: all)
  - [x] 5.1 Update `src/reformlab/vintage/__init__.py` exports (`VintageCohort`, `VintageState`, `VintageSummary`, `VintageConfig`, `VintageTransitionRule`, `VintageTransitionStep`, error classes)
  - [x] 5.2 Add concise docstrings for public APIs
  - [x] 5.3 Run `ruff check src/reformlab/vintage tests/vintage`
  - [x] 5.4 Run `mypy src/reformlab/vintage`
  - [x] 5.5 Run targeted tests: `pytest tests/vintage tests/orchestrator`

## Dev Notes

### Architecture Alignment

**From architecture.md - Step-Pluggable Dynamic Orchestrator:**
> For each year t in [start_year .. end_year]:
>   3. Execute transition steps (pluggable pipeline):
>      a. Vintage transitions (asset cohort aging, fleet turnover)
>      b. State carry-forward (income updates, demographic changes)

**From architecture.md - Subsystems:**
> `vintage/`: Cohort/vintage state management. Registered as orchestrator step. Tracks asset classes (vehicles, heating) through time.

**From architecture.md - Dynamic Execution Semantics:**
> Vintage states are updated through registered transition step functions.
> Randomness is seed-controlled and logged in manifests.

**From backlog BKL-304:**
> Implement vintage transition step for one asset class (vehicle or heating)

### Existing Code Patterns to Follow

- `src/reformlab/orchestrator/step.py`
  - `OrchestratorStep` protocol
  - `StepRegistry` topological ordering with deterministic tie-break by registration order
- `src/reformlab/orchestrator/types.py`
  - `YearState` immutable dataclass used as transition input/output state container
- `src/reformlab/orchestrator/carry_forward.py`
  - transition-step implementation pattern (`__slots__`, explicit errors, deterministic behavior, immutable updates via `replace`)

### Scope Guardrails

- In scope:
  - Vintage state transition logic for one asset class (`vehicle`)
  - Config-driven aging, entry, and retirement
  - Orchestrator step integration + tests
- Out of scope:
  - Panel output formatting/export (Story 3-7)
  - ComputationAdapter orchestration logic (Story 3-5)
  - Additional asset-class implementations (future stories)
  - Governance manifest implementation (EPIC-5)

### Testing Notes

- Prefer focused unit tests for transition semantics and config validation.
- Include integration tests for registry/pipeline behavior without coupling to future panel-output modules.
- Determinism checks should assert equality of full output state objects for repeated runs with identical inputs.

### References

- [Source: _bmad-output/planning-artifacts/architecture.md]
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-304]
- [Source: _bmad-output/planning-artifacts/prd.md#FR15]
- [Source: _bmad-output/planning-artifacts/prd.md#FR16]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR6]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR7]
- [Source: src/reformlab/orchestrator/step.py]
- [Source: src/reformlab/orchestrator/types.py]
- [Source: src/reformlab/orchestrator/carry_forward.py]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

- Implemented full vintage subsystem for vehicle asset class (MVP scope)
- Created immutable domain types: `VintageCohort`, `VintageState`, `VintageSummary`
- Implemented configuration-driven transitions with validation: `VintageConfig`, `VintageTransitionRule`
- Created `VintageTransitionStep` implementing `OrchestratorStep` protocol
- Transition behavior: aging (+1), max-age retirement, fixed/proportional entry
- State stored at stable key `vintage_vehicle` in `YearState.data`
- All operations deterministic (sorted cohort processing, immutable state updates)
- 65 comprehensive tests covering config validation, transition behavior, and orchestrator integration
- Quality gates passed: ruff (0 issues), mypy (0 issues), pytest (817 passed, 2 skipped)
- Updated scaffold test to reflect vintage package implementation

### File List

**New files:**
- src/reformlab/vintage/errors.py
- src/reformlab/vintage/types.py
- src/reformlab/vintage/config.py
- src/reformlab/vintage/transition.py
- tests/vintage/test_types.py
- tests/vintage/test_config.py
- tests/vintage/test_transition.py
- tests/vintage/test_integration.py

**Modified files:**
- src/reformlab/vintage/__init__.py (was empty, now exports public API)
- tests/test_scaffold.py (removed vintage from scaffold-only list)

## Change Log

- 2026-02-27: Implemented Story 3-4 vintage transition step with full test coverage
