# Story 12.3: Extend Orchestrator to Execute Policy Portfolios

Status: done
Dependencies: Story 12.1 (PolicyPortfolio model), Story 12.2 (conflict detection/resolution)

## Story

As a **policy analyst**,
I want the orchestrator to execute a policy portfolio (2+ bundled policies) over a multi-year simulation,
so that I can observe the combined effect of multiple environmental policies on household outcomes without writing custom pipeline code.

## Acceptance Criteria

### AC1: Multi-policy portfolio execution
Given a `PolicyPortfolio` with 3 policies (e.g., carbon tax + subsidy + feebate), when the orchestrator runs a yearly step, then all 3 policies are applied to the population for that year. Each policy's computation result is stored, and a merged result is available under `COMPUTATION_RESULT_KEY` for panel compatibility.

### AC2: 10-year portfolio panel output
Given a portfolio execution completed over 10 years, when `PanelOutput.from_orchestrator_result()` is called, then the panel output reflects the combined effect of all policies — one row per household per year containing output fields from every policy in the portfolio.

### AC3: No changes to ComputationAdapter or orchestrator core
Given the orchestrator receiving a portfolio instead of a single policy, when run, then no changes to `ComputationAdapter` protocol (`src/reformlab/computation/adapter.py`), `Orchestrator` runner (`src/reformlab/orchestrator/runner.py`), `OrchestratorConfig` (`src/reformlab/orchestrator/types.py`), or `PanelOutput.from_orchestrator_result()` (`src/reformlab/orchestrator/panel.py`) are required. The portfolio is unwrapped in a new `PortfolioComputationStep` at the template application layer.

### AC4: Backward compatibility with single-policy scenarios
Given a single-policy scenario (using the existing `ComputationStep`), when run through the same orchestrator, then it behaves identically to pre-portfolio execution. The existing `ComputationStep` class is unchanged.

### AC5: Validation and error handling
Given a `PolicyPortfolio` with an invalid or unsupported policy type, when `PortfolioComputationStep` is constructed, then a `PortfolioComputationStepError` is raised with the exact policy index and type that failed. Given an adapter that fails during one policy's computation, when the step executes, then the error includes: which policy failed (index, name, type), the year, the adapter version, and the original exception.

### AC6: Deterministic execution
Given identical inputs (same portfolio, population, adapter, and seed), when the step executes twice, then the `YearState` outputs are identical — same merged result table, same metadata structure, same per-policy execution order.

### AC7: Portfolio metadata in YearState
Given a completed portfolio computation step, when `YearState.metadata` is inspected, then it contains a `PORTFOLIO_METADATA_KEY` entry with: portfolio name, policy count, per-policy execution records (policy_type, name, adapter_version, row_count), and the execution order.

## Tasks / Subtasks

### Task 1: Create `PortfolioComputationStep` module (AC: 1, 3, 4, 6)

- [x] 1.1 Create new file `src/reformlab/orchestrator/portfolio_step.py` with module docstring referencing Story 12.3 / FR44
- [x] 1.2 Define `PORTFOLIO_METADATA_KEY = "portfolio_metadata"` stable string constant
- [x] 1.3 Define `PORTFOLIO_RESULTS_KEY = "portfolio_results"` stable string constant for per-policy results
- [x] 1.4 Define `PortfolioComputationStepError(Exception)` with `year`, `adapter_version`, `policy_index`, `policy_name`, `policy_type`, `original_error` attributes
- [x] 1.5 Define `_to_computation_policy()` bridge function: converts `portfolios.PolicyConfig` (typed `PolicyParameters`) to `computation.types.PolicyConfig` (generic `dict[str, Any]`) via `dataclasses.asdict()`
- [x] 1.6 Implement `PortfolioComputationStep` class with `__slots__`, `OrchestratorStep` protocol compliance (`name`, `depends_on`, `description`, `execute()`)

### Task 2: Implement `PortfolioComputationStep.__init__()` (AC: 1, 5)

- [x] 2.1 Parameters: `adapter: ComputationAdapter`, `population: PopulationData`, `portfolio: PolicyPortfolio`, `name: str = "portfolio_computation"`, `depends_on: tuple[str, ...] = ()`, `description: str | None = None`
- [x] 2.2 Store all constructor args in `__slots__`
- [x] 2.3 Validate `portfolio.policies` has at least 2 entries (should be guaranteed by `PolicyPortfolio.__post_init__` but defensive check, matching the >=2 invariant)
- [x] 2.4 Validate each `PolicyConfig.policy_type` has a valid `PolicyType` value (fail fast at construction, not at runtime)

### Task 3: Implement `execute()` method (AC: 1, 2, 5, 6, 7)

- [x] 3.1 Get adapter version via `self._adapter.version()` with `"<version-unavailable>"` fallback (same pattern as `ComputationStep`)
- [x] 3.2 Iterate over `self._portfolio.policies` **in tuple order** (deterministic)
- [x] 3.3 For each policy: call `_to_computation_policy()` to create `computation.types.PolicyConfig`
- [x] 3.4 For each policy: call `self._adapter.compute(population=self._population, policy=comp_policy, period=year)`
- [x] 3.5 Collect all `ComputationResult` objects in an ordered list
- [x] 3.6 Build per-policy execution records for metadata: `{"policy_index": i, "policy_type": policy_type.value, "policy_name": name, "adapter_version": version, "row_count": num_rows}`
- [x] 3.7 Merge all `ComputationResult.output_fields` (`pa.Table`) into a single combined table via `_merge_policy_results()`
- [x] 3.8 Create a single `ComputationResult` with: `output_fields` = merged table, `adapter_version` = first policy's adapter version, `period` = year, `metadata` = `{"source": "portfolio", "policy_count": n}`, `entity_tables` = `{}` (multi-entity portfolio merging deferred). Store under `COMPUTATION_RESULT_KEY` (panel compatibility)
- [x] 3.9 Store all individual `ComputationResult` objects under `PORTFOLIO_RESULTS_KEY` in `state.data` (per-policy access)
- [x] 3.10 Store portfolio metadata under `PORTFOLIO_METADATA_KEY` in `state.metadata`
- [x] 3.11 Also store standard `COMPUTATION_METADATA_KEY` with merged info (so `runner.py:_execute_step()` can extract `adapter_version` from its existing metadata path)
- [x] 3.12 Return new `YearState` via `dataclasses.replace()` (immutable updates)

### Task 4: Implement `_merge_policy_results()` helper (AC: 1, 2)

- [x] 4.1 Create module-level function `_merge_policy_results(results: list[ComputationResult], portfolio: PolicyPortfolio) -> pa.Table`
- [x] 4.2 Strategy: join all output tables on `household_id`. For the first result, keep column names as-is. For subsequent results, prefix columns with `{policy_type}_` to avoid name collisions (e.g., `subsidy_amount`, `feebate_net_impact`)
- [x] 4.3 Require `household_id` column in every result table; raise `PortfolioComputationStepError` if missing (fail-loud per project data-contract rules — silent row-index alignment risks merging unrelated households across policies)
- [x] 4.4 Handle edge case: if all results have the same column names (e.g., two carbon tax policies after conflict resolution), prefix ALL with `{policy_type}_{index}_`
- [x] 4.5 Result table must contain ALL columns from ALL policies, plus `household_id`
- [x] 4.6 Deterministic column ordering: `household_id` first, then columns from each policy in portfolio order

### Task 5: Implement error handling (AC: 5)

- [x] 5.1 Wrap individual `adapter.compute()` calls in try/except; on failure, raise `PortfolioComputationStepError` with policy context
- [x] 5.2 Error message format: `"Portfolio computation failed at year {year}, policy[{idx}] '{policy_name}' ({policy_type}): {error_type}: {error}"`
- [x] 5.3 Structured log on error: `event=portfolio_computation_error year={year} policy_index={idx} policy_type={type} adapter_version={version}`
- [x] 5.4 Log INFO per policy execution: `event=portfolio_policy_computed year={year} policy_index={idx} policy_type={type} adapter_version={version} row_count={n}`
- [x] 5.5 Log INFO on portfolio completion: `event=portfolio_computation_complete year={year} portfolio={name} policy_count={n}`

### Task 6: Update `orchestrator/__init__.py` exports (AC: 3, 4)

- [x] 6.1 Add `PortfolioComputationStep`, `PortfolioComputationStepError`, `PORTFOLIO_METADATA_KEY`, `PORTFOLIO_RESULTS_KEY` to `__init__.py` exports under new section comment `# Portfolio step (Story 12-3)`
- [x] 6.2 Add to `__all__` list

### Task 7: Write tests in `tests/orchestrator/test_portfolio_step.py` (AC: all)

- [x] 7.1 Create test file with standard imports and module docstring referencing Story 12.3
- [x] 7.2 **TestPortfolioStepProtocol** (AC3): Verify `PortfolioComputationStep` satisfies `OrchestratorStep` protocol (has `name`, `depends_on`, `execute`, isinstance check)
- [x] 7.3 **TestPortfolioStepExecution** (AC1, AC2): Given 3-policy portfolio + `MockAdapter`, execute returns `YearState` with `COMPUTATION_RESULT_KEY` containing merged `ComputationResult`. Assert all policy columns present. Assert `MockAdapter.call_log` has 3 entries (one per policy). Assert `household_id` column present
- [x] 7.4 **TestPortfolioStepMergedOutput** (AC2): Merged table has columns from all policies with correct prefixing. Column order is deterministic (household_id first, then by policy order)
- [x] 7.5 **TestPortfolioStepMetadata** (AC7): `state.metadata[PORTFOLIO_METADATA_KEY]` contains portfolio name, policy count, per-policy records with policy_type/name/adapter_version/row_count
- [x] 7.6 **TestPortfolioStepMetadata_ComputationKey** (AC3): `state.metadata[COMPUTATION_METADATA_KEY]` is present (backward compat with `runner.py` metadata extraction)
- [x] 7.7 **TestPortfolioStepDeterminism** (AC6): Two runs with identical inputs produce identical `YearState` output (data and metadata)
- [x] 7.8 **TestPortfolioStepErrorHandling** (AC5): Adapter failure at policy[1] raises `PortfolioComputationStepError` with correct `policy_index=1`, `policy_name`, `policy_type`, `year`, `adapter_version`, `original_error`
- [x] 7.9 **TestPortfolioStepErrorHandling_VersionFallback** (AC5): Adapter with failing `version()` uses `"<version-unavailable>"` fallback
- [x] 7.10 **TestPortfolioStepBackwardCompat** (AC4): Existing `ComputationStep` continues to work unchanged in the same pipeline. Pipeline with `[PortfolioComputationStep, CarryForwardStep]` works
- [x] 7.11 **TestPortfolioStepInPipeline** (AC1, AC4): Full orchestrator run with `PortfolioComputationStep` in step pipeline over 3 years. Verify yearly states contain portfolio results for each year
- [x] 7.12 **TestPortfolioStepPanelIntegration** (AC2): Full orchestrator run → `PanelOutput.from_orchestrator_result()` produces panel with all policy columns across all years. Panel export to CSV/Parquet works
- [x] 7.13 **TestPolicyConfigBridge** (AC1): `_to_computation_policy()` converts `portfolios.PolicyConfig` → `computation.types.PolicyConfig` correctly. `rate_schedule`, `exemptions`, custom fields are preserved in the dict
- [x] 7.14 **TestPerPolicyResults** (AC1): `state.data[PORTFOLIO_RESULTS_KEY]` stores individual `ComputationResult` per policy, accessible by index

### Task 8: Add portfolio step fixtures to `tests/orchestrator/conftest.py` (AC: all)

- [x] 8.1 Add `sample_portfolio` fixture: 2-policy portfolio (carbon tax + subsidy) with test parameters
- [x] 8.2 Add `three_policy_portfolio` fixture: 3-policy portfolio (carbon tax + subsidy + feebate)
- [x] 8.3 Add `portfolio_computation_step` fixture: `PortfolioComputationStep` with `MockAdapter` and sample population
- [x] 8.4 Reuse existing `MockAdapter` patterns from `tests/orchestrator/test_computation_step.py`

### Task 9: Run quality checks (AC: all)

- [x] 9.1 Run `uv run pytest tests/orchestrator/test_portfolio_step.py -v` — all 36 tests pass
- [x] 9.2 Run `uv run pytest tests/orchestrator/ -v` — all 270 orchestrator tests pass (no regressions)
- [x] 9.3 Run `uv run pytest tests/templates/portfolios/ -v` — all 73 portfolio tests pass
- [x] 9.4 Run `uv run ruff check src/reformlab/orchestrator/portfolio_step.py tests/orchestrator/test_portfolio_step.py` — all checks passed
- [x] 9.5 Run `uv run mypy src/reformlab/orchestrator/portfolio_step.py` — passes strict mode
- [x] 9.6 Run full test suite: `uv run pytest tests/ -v` — 2077 passed (2 pre-existing doc-contract failures unrelated to this story)

## Dev Notes

### Architecture Decisions

**Design: `PortfolioComputationStep` — a new step, not a modification**

The key architectural constraint (AC3) is: *no changes to `ComputationAdapter`, `Orchestrator`, `OrchestratorConfig`, or `PanelOutput`*. This means the portfolio must be unwrapped at the template application layer, not inside the orchestrator runner.

The solution is a **new `PortfolioComputationStep`** class that:
1. Implements the existing `OrchestratorStep` protocol (name + execute)
2. Takes a `PolicyPortfolio` instead of a single `PolicyConfig`
3. Iterates over each policy in the portfolio, converting it and calling the adapter
4. Merges results into a single `ComputationResult` stored under the **same `COMPUTATION_RESULT_KEY`**

This means `PanelOutput.from_orchestrator_result()` works unchanged — it reads `COMPUTATION_RESULT_KEY` from each yearly state, extracts `output_fields`, and concatenates. The merged table just has more columns.

**Two PolicyConfig types — the bridge function**

There are TWO `PolicyConfig` classes in the codebase:
- `reformlab.computation.types.PolicyConfig` — holds `policy: dict[str, Any]`, used by `ComputationAdapter.compute()`
- `reformlab.templates.portfolios.portfolio.PolicyConfig` — holds `policy_type: PolicyType`, `policy: PolicyParameters`, used by `PolicyPortfolio`

The bridge function `_to_computation_policy()` converts the portfolio type to the computation type:
```python
from dataclasses import asdict

def _to_computation_policy(
    policy_config: "portfolios_PolicyConfig",
) -> "computation_PolicyConfig":
    from reformlab.computation.types import PolicyConfig as ComputationPolicyConfig
    return ComputationPolicyConfig(
        policy=asdict(policy_config.policy),
        name=policy_config.name or policy_config.policy_type.value,
        description=f"{policy_config.policy_type.value} policy",
    )
```

**Result merging strategy**

Each policy produces a `ComputationResult` with `output_fields: pa.Table`. The merge:
1. All result tables MUST contain `household_id` — raise `PortfolioComputationStepError` if missing (fail-loud data contract)
2. First policy's columns keep their original names
3. Subsequent policies' columns are prefixed with `{policy_type}_` (e.g., `subsidy_amount`, `feebate_net_impact`)
4. `household_id` is shared (join key) — not duplicated
5. If two policies have the same `policy_type` (after conflict resolution), use `{policy_type}_{index}_` prefix

This avoids column name collisions while keeping the first policy's columns backward-compatible with existing downstream code (e.g., indicators that reference `tax_burden` directly).

**Cross-policy data flow is OUT OF SCOPE**

Rebate templates require a `rebate_pool` parameter that could come from carbon tax revenue. This cross-policy dependency is NOT handled in this story. Each policy is computed independently with the same population data. Cross-policy data flow will be addressed in Story 12.5 or a future story.

### Key Interfaces to Follow

**`OrchestratorStep` protocol** [Source: src/reformlab/orchestrator/step.py:42-70]:
```python
@runtime_checkable
class OrchestratorStep(Protocol):
    @property
    def name(self) -> str: ...
    def execute(self, year: int, state: YearState) -> YearState: ...
```
Optional: `depends_on: tuple[str, ...]`, `description: str`

**`ComputationAdapter.compute()` signature** [Source: src/reformlab/computation/adapter.py]:
```python
def compute(self, population: PopulationData, policy: PolicyConfig, period: int) -> ComputationResult
```

**`ComputationStep.execute()` pattern to follow** [Source: src/reformlab/orchestrator/computation_step.py:118-196]:
- Get adapter version with fallback
- Call adapter.compute()
- Store result under `COMPUTATION_RESULT_KEY` in `state.data`
- Store metadata under `COMPUTATION_METADATA_KEY` in `state.metadata`
- Return `replace(state, data=new_data, metadata=new_metadata)`

**`runner.py` metadata extraction** [Source: src/reformlab/orchestrator/runner.py `_execute_step()`]:
The orchestrator runner reads `COMPUTATION_METADATA_KEY` from `state.metadata` to extract `adapter_version`. `PortfolioComputationStep` MUST populate this key for backward compatibility with the runner's step execution logging.

### Scope Boundaries

**IN SCOPE:**
- `PortfolioComputationStep` class implementing `OrchestratorStep` protocol
- Bridge function from `portfolios.PolicyConfig` to `computation.types.PolicyConfig`
- Result merging (join policy output tables on `household_id`)
- Per-policy and portfolio-level metadata in `YearState`
- `PortfolioComputationStepError` exception class
- Tests for all acceptance criteria
- Export updates in `orchestrator/__init__.py`

**OUT OF SCOPE (deferred to future stories):**
- Cross-policy data flow (e.g., carbon tax revenue → rebate pool) — Story 12.5 or later
- `OrchestratorRunner` / `WorkflowResult` integration with portfolios — Story 12.4 or later
- Portfolio-aware `from_workflow_config()` factory — Story 12.4 or later
- Portfolio versioning in scenario registry — Story 12.4
- Multi-portfolio comparison — Story 12.5
- Modifications to `PanelOutput`, `Orchestrator`, `ComputationAdapter`, or any existing step

### Project Structure Notes

**New files:**
```
src/reformlab/orchestrator/portfolio_step.py    ← PortfolioComputationStep, error, bridge, merge
tests/orchestrator/test_portfolio_step.py       ← All tests for this story
```

**Modified files:**
```
src/reformlab/orchestrator/__init__.py          ← Add exports (PortfolioComputationStep, error, keys)
tests/orchestrator/conftest.py                  ← Add portfolio fixtures
```

**Files NOT to modify:**
```
src/reformlab/orchestrator/runner.py            ← AC3: no changes
src/reformlab/orchestrator/types.py             ← AC3: no changes
src/reformlab/orchestrator/panel.py             ← AC3: no changes
src/reformlab/computation/adapter.py            ← AC3: no changes
src/reformlab/computation/types.py              ← no changes
src/reformlab/orchestrator/computation_step.py  ← AC4: unchanged
src/reformlab/orchestrator/step.py              ← no changes
```

### Code Conventions to Follow

- `from __future__ import annotations` at top of every file
- `if TYPE_CHECKING:` guards for imports only needed for type annotations
- Frozen dataclasses for all domain types; mutate via `dataclasses.replace()`
- `__slots__` on step classes (matching `ComputationStep` pattern)
- Stable string-constant keys at module level (e.g., `PORTFOLIO_METADATA_KEY`)
- Structured log format: `key=value` pairs (e.g., `event=portfolio_policy_computed year=2025 policy_index=0`)
- `logging.getLogger(__name__)` for logger
- Section separators `# ====...====` for major sections in longer modules
- Exception hierarchy: `PortfolioComputationStepError(Exception)` with structured attributes

### MockAdapter Usage in Tests

The `MockAdapter` [Source: src/reformlab/computation/mock_adapter.py] supports two modes:
1. Fixed output: `MockAdapter(default_output=pa.table(...))` — returns same table for every `compute()` call
2. Custom function: `MockAdapter(compute_fn=lambda pop, policy, period: pa.table(...))` — can vary output per call

For portfolio tests, use `compute_fn` mode to return different column sets per policy, verifying the merge logic. Use `mock_adapter.call_log` to assert each policy was computed.

Example pattern from existing tests [Source: tests/orchestrator/test_computation_step.py]:
```python
@pytest.fixture
def mock_adapter():
    output_table = pa.table({"household_id": [1, 2, 3], "tax_burden": [100.0, 200.0, 300.0]})
    return MockAdapter(default_output=output_table)
```

For portfolio tests, create a `compute_fn` that returns policy-type-specific columns:
```python
def portfolio_compute_fn(population, policy, period):
    if "carbon_tax" in policy.name:
        return pa.table({"household_id": [1, 2], "tax_burden": [100.0, 200.0]})
    elif "subsidy" in policy.name:
        return pa.table({"household_id": [1, 2], "subsidy_amount": [50.0, 75.0]})
    ...
```

### Performance Considerations

Portfolio execution scales linearly with policy count — N adapter calls per year step. For typical portfolios (2-5 policies), this is negligible. No optimization needed.

The result merge (`_merge_policy_results`) uses PyArrow table operations which are efficient for typical household counts (10k-100k rows).

### References

- [Source: docs/prd.md#FR44] — "System executes a simulation with a policy portfolio, applying all bundled policies together."
- [Source: docs/epics.md#BKL-1203] — Story acceptance criteria
- [Source: src/reformlab/orchestrator/computation_step.py] — `ComputationStep` pattern to follow
- [Source: src/reformlab/orchestrator/runner.py `_execute_step()`] — Runner metadata extraction requiring `COMPUTATION_METADATA_KEY`
- [Source: src/reformlab/orchestrator/panel.py `from_orchestrator_result()`] — `PanelOutput` reading `COMPUTATION_RESULT_KEY`
- [Source: src/reformlab/templates/portfolios/portfolio.py] — `PolicyPortfolio` and `PolicyConfig` (portfolio type)
- [Source: src/reformlab/computation/types.py:29-35] — `PolicyConfig` (computation type)
- [Source: src/reformlab/orchestrator/step.py:42-70] — `OrchestratorStep` protocol
- [Source: src/reformlab/computation/mock_adapter.py] — `MockAdapter` for testing
- [Source: docs/project-context.md#Architecture] — Adapter isolation, step pipeline contract, frozen dataclasses
- [Source: _bmad-output/implementation-artifacts/12-1-*.md] — Story 12.1 decisions on `PolicyConfig` as new frozen dataclass
- [Source: _bmad-output/implementation-artifacts/12-2-*.md] — Story 12.2 code review, enum extraction, conflict resolution

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — all tests passed on first run after lint fixes.

### Completion Notes List

- Implemented `PortfolioComputationStep` in `src/reformlab/orchestrator/portfolio_step.py` following `ComputationStep` patterns
- Bridge function `_to_computation_policy()` converts portfolio `PolicyConfig` to computation `PolicyConfig` via `dataclasses.asdict()`
- Result merge joins on `household_id` with policy-type prefixing for subsequent policies; indexed prefixing for duplicate policy types
- All 7 acceptance criteria satisfied with 36 dedicated tests across 12 test classes
- No modifications to `runner.py`, `types.py`, `panel.py`, `adapter.py`, or `computation_step.py` (AC3 satisfied)
- Backward compatibility verified: existing `ComputationStep` works unchanged (AC4)
- Panel integration verified: `PanelOutput.from_orchestrator_result()` works with portfolio results, CSV/Parquet export tested (AC2)
- ruff clean, mypy strict passes, 270 orchestrator tests pass with no regressions
- **Code Review Synthesis (2026-03-06):** Fixed `_merge_policy_results()` — added household_id set consistency and uniqueness validation (fail-loud), changed join from `inner` to `left outer`, optimized table construction. Stored per-policy results as `tuple` for immutability. Added 3 new tests (39 total). Fixed conftest type hint. 273 orchestrator tests pass.

### Change Log

- 2026-03-06: Story 12.3 implemented — PortfolioComputationStep, bridge function, result merging, error handling, 36 tests
- 2026-03-06: Code Review Synthesis — hardened merge validation, immutability fix, 3 new tests

### File List

**New files:**
- `src/reformlab/orchestrator/portfolio_step.py`
- `tests/orchestrator/test_portfolio_step.py`

**Modified files:**
- `src/reformlab/orchestrator/__init__.py` (added portfolio step exports)
- `tests/orchestrator/conftest.py` (added portfolio fixtures)

## Senior Developer Review (AI)

### Review: 2026-03-06
- **Reviewer:** AI Code Review Synthesis
- **Evidence Score:** 5.2 (Reviewer A) / 10.8 (Reviewer B) → Changes Requested
- **Issues Found:** 6 verified
- **Issues Fixed:** 5
- **Action Items Created:** 1

#### Review Follow-ups (AI)
- [ ] [AI-Review] MEDIUM: `PolicyConfig.__post_init__` in `portfolio.py:43` accesses `self.policy_type.value` without guarding against non-enum input — should use `str(self.policy_type)` or `getattr(self.policy_type, 'value', str(self.policy_type))` to produce a structured error instead of `AttributeError` (`src/reformlab/templates/portfolios/portfolio.py`)
