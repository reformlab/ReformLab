<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 12 -->
<!-- Story: 3 -->
<!-- Phase: code-review-synthesis -->
<!-- Timestamp: 20260306T121509Z -->
<compiled-workflow>
<mission><![CDATA[

Master Code Review Synthesis: Story 12.3

You are synthesizing 2 independent code review findings.

Your mission:
1. VERIFY each issue raised by reviewers
   - Cross-reference with project_context.md (ground truth)
   - Cross-reference with git diff and source files
   - Identify false positives (issues that aren't real problems)
   - Confirm valid issues with evidence

2. PRIORITIZE real issues by severity
   - Critical: Security vulnerabilities, data corruption risks
   - High: Bugs, logic errors, missing error handling
   - Medium: Code quality issues, performance concerns
   - Low: Style issues, minor improvements

3. SYNTHESIZE findings
   - Merge duplicate issues from different reviewers
   - Note reviewer consensus (if 3+ agree, high confidence)
   - Highlight unique insights from individual reviewers

4. APPLY source code fixes
   - You have WRITE PERMISSION to modify SOURCE CODE files
   - CRITICAL: Before using Edit tool, ALWAYS Read the target file first
   - Use EXACT content from Read tool output as old_string, NOT content from this prompt
   - If Read output is truncated, use offset/limit parameters to locate the target section
   - Apply fixes for verified issues
   - Do NOT modify the story file (only Dev Agent Record if needed)
   - Document what you changed and why

Output format:
## Synthesis Summary
## Issues Verified (by severity)
## Issues Dismissed (false positives with reasoning)
## Source Code Fixes Applied

]]></mission>
<context>
<file id="e58fb4dd" path="docs/project-context.md" label="PROJECT CONTEXT"><![CDATA[

---
project_name: 'ReformLab'
user_name: 'Lucas'
date: '2026-02-27'
status: 'complete'
sections_completed: ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'code_quality', 'workflow_rules', 'critical_rules']
rule_count: 38
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

- **Python 3.13+** — `target-version = "py313"` (ruff), `python_version = "3.13"` (mypy strict)
- **uv** — package manager, **hatchling** — build backend
- **pyarrow >= 18.0.0** — canonical data type (`pa.Table`), CSV/Parquet I/O
- **pyyaml >= 6.0.2** — YAML template/config loading
- **jsonschema >= 4.23.0** — JSON Schema validation for templates
- **openfisca-core >= 44.0.0** — optional dependency (`[openfisca]` extra); never import outside adapter modules
- **pytest >= 8.3.3, ruff >= 0.15.0, mypy >= 1.19.0** — dev tooling
- **Planned frontend:** React 18+ / TypeScript / Vite / Shadcn/ui / Tailwind v4
- **Planned backend API:** FastAPI + uvicorn
- **Planned deployment:** Kamal 2 on Hetzner CX22

### Version Constraints

- mypy runs in **strict mode** with explicit `ignore_missing_imports` overrides for openfisca, pyarrow, jsonschema, yaml
- OpenFisca is optional — core library must function without it installed

## Critical Implementation Rules

### Python Language Rules

- **Every file starts with** `from __future__ import annotations` — no exceptions
- **Use `if TYPE_CHECKING:` guards** for imports that are only needed for annotations or would create circular dependencies; do the runtime import locally where needed
- **Frozen dataclasses are the default** — all domain types use `@dataclass(frozen=True)`; mutate via `dataclasses.replace()`, never by assignment
- **Protocols, not ABCs** — interfaces are `Protocol` + `@runtime_checkable`; no abstract base classes; structural (duck) typing only
- **Subsystem-specific exceptions** — each module defines its own error hierarchy; never raise bare `Exception` or `ValueError` for domain errors
- **Metadata bags** use `dict[str, Any]` with **stable string-constant keys** defined at module level (e.g., `STEP_EXECUTION_LOG_KEY`)
- **Union syntax** — use `X | None` not `Optional[X]`; use `dict[str, int]` not `Dict[str, int]` (modern generics, no `typing` aliases)
- **`tuple[...]` for immutable sequences** — function parameters and return types that are ordered-and-fixed use `tuple`, not `list`

### Architecture & Framework Rules

- **Adapter isolation is absolute** — only `computation/openfisca_adapter.py` and `openfisca_api_adapter.py` may import OpenFisca; all other code uses the `ComputationAdapter` protocol
- **Step pipeline contract** — steps implement `OrchestratorStep` protocol (`name` + `execute(year, state) -> YearState`); bare callables accepted via `adapt_callable()`; registration via `StepRegistry` with topological sort on `depends_on`
- **Template packs are YAML** — live in `src/reformlab/templates/packs/{policy_type}/`; validated against JSON Schemas in `templates/schema/`; each policy type has its own subpackage with `compute.py` + `compare.py`
- **Data flows through PyArrow** — `PopulationData` (dict of `pa.Table` by entity) → adapter → `ComputationResult` (`pa.Table`) → `YearState.data` → `PanelOutput` (stacked table) → indicators
- **`YearState` is the state token** — passed between steps and years; immutable (frozen dataclass); updated via `replace()`
- **Orchestrator is the core product** — never build custom policy engines, formula compilers, or entity graph engines; OpenFisca handles computation, this project handles orchestration

### Testing Rules

- **Mirror source structure** — `tests/{subsystem}/` matches `src/reformlab/{subsystem}/`; each has `__init__.py` and `conftest.py`
- **Class-based test grouping** — group tests by feature or acceptance criterion (e.g., `TestOrchestratorBasicExecution`); reference story/AC IDs in comments and docstrings
- **Fixtures in conftest.py** — subsystem-specific fixtures per `conftest.py`; build PyArrow tables inline, use `tmp_path` for I/O, golden YAML files in `tests/fixtures/`
- **Direct assertions** — use plain `assert`; no custom assertion helpers; use `pytest.raises(ExceptionClass, match=...)` for errors
- **Test helpers are explicit** — import shared callables from conftest directly (`from tests.orchestrator.conftest import ...`); no hidden magic
- **Golden file tests** — YAML fixtures in `tests/fixtures/templates/`; test load → validate → round-trip cycle
- **MockAdapter for unit tests** — never use real OpenFisca in orchestrator/template/indicator unit tests; `MockAdapter` is the standard test double

### Code Quality & Style Rules

- **ruff** enforces `E`, `F`, `I`, `W` rule sets; `src = ["src"]`; target Python 3.13
- **mypy strict** — all code must pass `mypy --strict`; new modules need `ignore_missing_imports` overrides in `pyproject.toml` only for third-party libs without stubs
- **File naming** — `snake_case.py` throughout; no PascalCase or kebab-case files
- **Class naming** — PascalCase for classes (`OrchestratorStep`, `CarbonTaxParameters`); no suffixes like `Impl` or `Base`
- **Module-level docstrings** — every module has a docstring explaining its role, referencing relevant story/FR
- **Section separators** — use `# ====...====` comment blocks to separate major sections within longer modules (see `step.py`)
- **No wildcard imports** — always import specific names; `from reformlab.orchestrator import Orchestrator, OrchestratorConfig`
- **Logging** — use `logging.getLogger(__name__)`; structured key=value format for parseable log lines (e.g., `year=%d seed=%s event=year_start`)

### Development Workflow Rules

- **Package manager is uv** — use `uv pip install`, `uv run pytest`, etc.; not `pip` directly
- **Test command** — `uv run pytest tests/` (or specific subsystem path)
- **Lint command** — `uv run ruff check src/ tests/` and `uv run mypy src/`
- **Source layout** — `src/reformlab/` is the installable package; `tests/` is separate; `pythonpath = ["src"]` in pytest config
- **Build system** — hatchling with `packages = ["src/reformlab"]`
- **No auto-formatting on save assumed** — agents must produce ruff-compliant code; run `ruff check --fix` if needed

### Critical Don't-Miss Rules

- **Never import OpenFisca outside adapter modules** — this is the single most important architectural boundary; violation couples the entire codebase to one backend
- **All domain types are frozen** — never add a mutable dataclass; if you need mutation, use `dataclasses.replace()` and return a new instance
- **Determinism is non-negotiable** — every run must be reproducible; seeds are explicit, logged in manifests, derived deterministically (`master_seed XOR year`)
- **Data contracts fail loudly** — contract validation at ingestion boundaries is field-level and blocking; never silently coerce or drop data
- **Assumption transparency** — every run produces a manifest (JSON); assumptions, versions, seeds, data hashes are all recorded
- **PyArrow is the canonical data type** — do not use pandas DataFrames in core logic; `pa.Table` is the standard; pandas only at display/export boundaries if needed
- **No custom formula compiler** — environmental policy logic is Python code in template `compute.py` modules, not YAML formula strings or DSLs
- **France/Europe first** — initial scenarios use French policy parameters (EUR, INSEE deciles, French carbon tax rates); European data sources (Eurostat, EU-SILC)

---

## Usage Guidelines

**For AI Agents:**

- Read this file before implementing any code
- Follow ALL rules exactly as documented
- When in doubt, prefer the more restrictive option
- Update this file if new patterns emerge

**For Humans:**

- Keep this file lean and focused on agent needs
- Update when technology stack changes
- Review quarterly for outdated rules
- Remove rules that become obvious over time

Last Updated: 2026-02-27


]]></file>
<file id="78cc87c5" path="_bmad-output/implementation-artifacts/12-3-extend-orchestrator-to-execute-policy-portfolios.md" label="STORY FILE"><![CDATA[

# Story 12.3: Extend Orchestrator to Execute Policy Portfolios

Status: Ready for Review
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

### Change Log

- 2026-03-06: Story 12.3 implemented — PortfolioComputationStep, bridge function, result merging, error handling, 36 tests

### File List

**New files:**
- `src/reformlab/orchestrator/portfolio_step.py`
- `tests/orchestrator/test_portfolio_step.py`

**Modified files:**
- `src/reformlab/orchestrator/__init__.py` (added portfolio step exports)
- `tests/orchestrator/conftest.py` (added portfolio fixtures)



]]></file>
<file id="d9f1f494" path="src/reformlab/orchestrator/__init__.py" label="SOURCE CODE"><![CDATA[

"""Orchestrator subsystem for multi-year projections.

This module provides the yearly loop orchestrator with step-pluggable
pipeline execution for deterministic multi-year simulations.

Public API:
- Orchestrator: Main orchestrator class for executing projections
- OrchestratorConfig: Configuration for orchestrator execution
- OrchestratorResult: Result container for orchestrator execution
- YearState: State carried between years
- YearStep: Type alias for step callables
- PipelineStep: Union type for callable and protocol-based steps
- OrchestratorError: Structured error with execution context
- OrchestratorRunner: Runner adapter for run_workflow() integration
- from_workflow_config: Factory to create config from WorkflowConfig
- OrchestratorStep: Protocol for pipeline steps (Story 3-2)
- StepRegistry: Registration and dependency ordering for steps (Story 3-2)
- step: Decorator for function-based steps (Story 3-2)
- adapt_callable: Adapter for bare YearStep callables (Story 3-2)
- Step errors: StepValidationError, StepRegistrationError, CircularDependencyError
- CarryForwardStep: Deterministic state carry-forward step (Story 3-3)
- CarryForwardConfig: Configuration for carry-forward rules (Story 3-3)
- CarryForwardRule: Single variable update rule (Story 3-3)
- CarryForwardConfigError: Invalid carry-forward configuration (Story 3-3)
- CarryForwardExecutionError: Error during carry-forward execution (Story 3-3)
- ComputationStep: Adapter invocation step for tax-benefit computation (Story 3-5)
- ComputationStepError: Error during computation step execution (Story 3-5)
- COMPUTATION_RESULT_KEY: Stable key for ComputationResult in YearState.data (Story 3-5)
- COMPUTATION_METADATA_KEY: Stable key for computation metadata (Story 3-5)
- SEED_LOG_KEY: Stable key for seed log in metadata (Story 3-6)
- STEP_EXECUTION_LOG_KEY: Stable key for step execution log in metadata (Story 3-6)
- PanelOutput: Household-by-year panel dataset from orchestrator run (Story 3-7)
- compare_panels: Helper to compare baseline and reform panels (Story 3-7)
- PANEL_VERSION: Panel format version for metadata (Story 3-7)
- PortfolioComputationStep: Portfolio execution step (Story 12-3)
- PortfolioComputationStepError: Error during portfolio step execution (Story 12-3)
- PORTFOLIO_METADATA_KEY: Stable key for portfolio metadata (Story 12-3)
- PORTFOLIO_RESULTS_KEY: Stable key for per-policy results (Story 12-3)
"""

from reformlab.orchestrator.carry_forward import (
    CarryForwardConfig,
    CarryForwardConfigError,
    CarryForwardExecutionError,
    CarryForwardRule,
    CarryForwardStep,
)
from reformlab.orchestrator.computation_step import (
    COMPUTATION_METADATA_KEY,
    COMPUTATION_RESULT_KEY,
    ComputationStep,
    ComputationStepError,
)
from reformlab.orchestrator.errors import OrchestratorError
from reformlab.orchestrator.panel import PANEL_VERSION, PanelOutput, compare_panels
from reformlab.orchestrator.portfolio_step import (
    PORTFOLIO_METADATA_KEY,
    PORTFOLIO_RESULTS_KEY,
    PortfolioComputationStep,
    PortfolioComputationStepError,
)
from reformlab.orchestrator.runner import (
    SEED_LOG_KEY,
    STEP_EXECUTION_LOG_KEY,
    Orchestrator,
    OrchestratorRunner,
    from_workflow_config,
)
from reformlab.orchestrator.step import (
    CircularDependencyError,
    OrchestratorStep,
    StepRegistrationError,
    StepRegistry,
    StepValidationError,
    adapt_callable,
    is_protocol_step,
    step,
)
from reformlab.orchestrator.types import (
    OrchestratorConfig,
    OrchestratorResult,
    PipelineStep,
    YearState,
    YearStep,
)

__all__ = [
    # Core orchestrator
    "Orchestrator",
    "OrchestratorConfig",
    "OrchestratorError",
    "OrchestratorResult",
    "OrchestratorRunner",
    "PipelineStep",
    "YearState",
    "YearStep",
    "from_workflow_config",
    # Step interface (Story 3-2)
    "OrchestratorStep",
    "StepRegistry",
    "step",
    "adapt_callable",
    "is_protocol_step",
    # Step errors (Story 3-2)
    "StepValidationError",
    "StepRegistrationError",
    "CircularDependencyError",
    # Carry-forward step (Story 3-3)
    "CarryForwardStep",
    "CarryForwardConfig",
    "CarryForwardRule",
    "CarryForwardConfigError",
    "CarryForwardExecutionError",
    # Computation step (Story 3-5)
    "ComputationStep",
    "ComputationStepError",
    "COMPUTATION_RESULT_KEY",
    "COMPUTATION_METADATA_KEY",
    # Logging keys (Story 3-6)
    "SEED_LOG_KEY",
    "STEP_EXECUTION_LOG_KEY",
    # Panel output (Story 3-7)
    "PanelOutput",
    "compare_panels",
    "PANEL_VERSION",
    # Portfolio step (Story 12-3)
    "PortfolioComputationStep",
    "PortfolioComputationStepError",
    "PORTFOLIO_METADATA_KEY",
    "PORTFOLIO_RESULTS_KEY",
]


]]></file>
<file id="65dde92f" path="src/reformlab/orchestrator/portfolio_step.py" label="SOURCE CODE"><![CDATA[

"""Portfolio computation step for executing multi-policy portfolios.

This module provides:
- PortfolioComputationStep: OrchestratorStep for portfolio execution
- PortfolioComputationStepError: Error during portfolio computation
- PORTFOLIO_METADATA_KEY: Stable key for portfolio metadata in YearState.metadata
- PORTFOLIO_RESULTS_KEY: Stable key for per-policy results in YearState.data

Story 12.3 / FR44: Extend orchestrator to execute policy portfolios.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, replace
from typing import TYPE_CHECKING, Any

import pyarrow as pa

from reformlab.orchestrator.computation_step import (
    COMPUTATION_METADATA_KEY,
    COMPUTATION_RESULT_KEY,
)

if TYPE_CHECKING:
    from reformlab.computation.adapter import ComputationAdapter
    from reformlab.computation.types import (
        ComputationResult,
        PopulationData,
    )
    from reformlab.computation.types import PolicyConfig as ComputationPolicyConfig
    from reformlab.orchestrator.types import YearState
    from reformlab.templates.portfolios.portfolio import (
        PolicyConfig as PortfolioPolicyConfig,
    )
    from reformlab.templates.portfolios.portfolio import PolicyPortfolio
    from reformlab.templates.schema import PolicyType

logger = logging.getLogger(__name__)


# ============================================================================
# Stable keys for portfolio data in YearState
# ============================================================================

PORTFOLIO_METADATA_KEY = "portfolio_metadata"
PORTFOLIO_RESULTS_KEY = "portfolio_results"


# ============================================================================
# Error class
# ============================================================================


class PortfolioComputationStepError(Exception):
    """Error during portfolio computation step execution.

    Includes policy context (index, name, type), adapter version, year,
    and original error for debugging and governance tracking.
    """

    def __init__(
        self,
        message: str,
        *,
        year: int,
        adapter_version: str,
        policy_index: int,
        policy_name: str,
        policy_type: str,
        original_error: Exception | None = None,
    ) -> None:
        self.year = year
        self.adapter_version = adapter_version
        self.policy_index = policy_index
        self.policy_name = policy_name
        self.policy_type = policy_type
        self.original_error = original_error
        super().__init__(message)


# ============================================================================
# Bridge function
# ============================================================================


def _to_computation_policy(
    policy_config: PortfolioPolicyConfig,
) -> ComputationPolicyConfig:
    """Convert a portfolio PolicyConfig to a computation PolicyConfig.

    The portfolio layer uses typed PolicyParameters (frozen dataclass),
    while the computation layer uses generic dict[str, Any].
    """
    from reformlab.computation.types import PolicyConfig as ComputationPolicyConfig

    return ComputationPolicyConfig(
        policy=asdict(policy_config.policy),
        name=policy_config.name or policy_config.policy_type.value,
        description=f"{policy_config.policy_type.value} policy",
    )


# ============================================================================
# Result merging
# ============================================================================


def _merge_policy_results(
    results: list[ComputationResult],
    portfolio: PolicyPortfolio,
) -> pa.Table:
    """Merge output tables from multiple policies into a single table.

    Strategy: join all output tables on ``household_id``. The first result
    keeps column names as-is. Subsequent results prefix columns with
    ``{policy_type}_`` to avoid collisions. If two policies share the
    same policy_type, ALL are prefixed with ``{policy_type}_{index}_``.

    Args:
        results: Ordered list of ComputationResult from each policy.
        portfolio: The portfolio providing policy metadata.

    Returns:
        Merged pa.Table with household_id first, then columns from
        each policy in portfolio order.

    Raises:
        PortfolioComputationStepError: If any result lacks household_id.
    """
    if not results:
        return pa.table({"household_id": pa.array([], type=pa.int64())})

    # Validate household_id column presence
    for i, result in enumerate(results):
        if "household_id" not in result.output_fields.column_names:
            policy_cfg = portfolio.policies[i]
            raise PortfolioComputationStepError(
                f"Policy[{i}] '{policy_cfg.name or policy_cfg.policy_type.value}' "
                f"output_fields missing required 'household_id' column",
                year=result.period,
                adapter_version=result.adapter_version,
                policy_index=i,
                policy_name=policy_cfg.name or policy_cfg.policy_type.value,
                policy_type=policy_cfg.policy_type.value,
            )

    # Detect duplicate policy types to decide prefixing strategy
    type_counts: dict[str, int] = {}
    for policy_cfg in portfolio.policies:
        ptype = policy_cfg.policy_type.value
        type_counts[ptype] = type_counts.get(ptype, 0) + 1

    has_duplicate_types = any(count > 1 for count in type_counts.values())

    # Build merged table starting from household_id of first result
    merged = results[0].output_fields.select(["household_id"])

    for i, (result, policy_cfg) in enumerate(
        zip(results, portfolio.policies, strict=True)
    ):
        table = result.output_fields
        ptype = policy_cfg.policy_type.value
        non_id_cols = [c for c in table.column_names if c != "household_id"]

        # Determine prefix
        if i == 0 and not has_duplicate_types:
            # First policy keeps original names when no type duplicates
            prefix = ""
        elif has_duplicate_types:
            prefix = f"{ptype}_{i}_"
        else:
            prefix = f"{ptype}_"

        # Build rename mapping and join
        renamed_table = table.select(["household_id"])
        for col_name in non_id_cols:
            new_name = f"{prefix}{col_name}" if prefix else col_name
            renamed_table = renamed_table.append_column(
                new_name, table.column(col_name)
            )

        # Join on household_id
        if i == 0:
            # First policy: take all columns directly
            for col_name in non_id_cols:
                new_name = f"{prefix}{col_name}" if prefix else col_name
                merged = merged.append_column(new_name, table.column(col_name))
        else:
            # Subsequent policies: join on household_id
            merged = merged.join(
                renamed_table,
                keys="household_id",
                join_type="inner",
            )

    return merged


# ============================================================================
# PortfolioComputationStep
# ============================================================================


class PortfolioComputationStep:
    """Orchestrator step for executing a policy portfolio.

    Iterates over each policy in the portfolio, invokes the adapter
    for each, merges results into a single ComputationResult stored
    under COMPUTATION_RESULT_KEY for panel compatibility.

    Implements the OrchestratorStep protocol.
    """

    __slots__ = (
        "_adapter",
        "_population",
        "_portfolio",
        "_name",
        "_depends_on",
        "_description",
    )

    def __init__(
        self,
        adapter: ComputationAdapter,
        population: PopulationData,
        portfolio: PolicyPortfolio,
        name: str = "portfolio_computation",
        depends_on: tuple[str, ...] = (),
        description: str | None = None,
    ) -> None:
        """Initialize the portfolio computation step.

        Args:
            adapter: ComputationAdapter to invoke for each policy.
            population: PopulationData to pass to adapter.
            portfolio: PolicyPortfolio with 2+ policies.
            name: Step name for registry.
            depends_on: Names of steps this step depends on.
            description: Optional description.

        Raises:
            PortfolioComputationStepError: If portfolio has < 2 policies
                or contains an invalid policy type.
        """
        self._adapter = adapter
        self._population = population
        self._portfolio = portfolio
        self._name = name
        self._depends_on = depends_on
        self._description = (
            description or "Portfolio computation step for multi-policy execution"
        )

        # Defensive validation (should be guaranteed by PolicyPortfolio.__post_init__)
        if len(portfolio.policies) < 2:
            raise PortfolioComputationStepError(
                f"Portfolio must have at least 2 policies, got {len(portfolio.policies)}",
                year=0,
                adapter_version="<not-started>",
                policy_index=-1,
                policy_name="",
                policy_type="",
            )

        # Validate each policy type at construction time (fail fast)
        for i, policy_cfg in enumerate(portfolio.policies):
            _validate_policy_type(policy_cfg.policy_type, i, policy_cfg)

    @property
    def name(self) -> str:
        """Unique identifier for this step."""
        return self._name

    @property
    def depends_on(self) -> tuple[str, ...]:
        """Names of steps this step depends on."""
        return self._depends_on

    @property
    def description(self) -> str:
        """Human-readable description of the step."""
        return self._description

    def execute(self, year: int, state: YearState) -> YearState:
        """Execute all portfolio policies for a given year.

        Iterates over policies in tuple order (deterministic), invokes
        the adapter for each, merges results, and stores them in
        YearState for panel compatibility.

        Args:
            year: Current simulation year.
            state: Current year state.

        Returns:
            New YearState with merged computation result and metadata.

        Raises:
            PortfolioComputationStepError: If any policy computation fails.
        """
        # Get adapter version with fallback
        adapter_version = _get_adapter_version(self._adapter, year, self._name)

        # Execute each policy in order
        policy_results: list[ComputationResult] = []
        execution_records: list[dict[str, Any]] = []

        for i, policy_cfg in enumerate(self._portfolio.policies):
            comp_policy = _to_computation_policy(policy_cfg)
            policy_name = policy_cfg.name or policy_cfg.policy_type.value
            policy_type_value = policy_cfg.policy_type.value

            try:
                result = self._adapter.compute(
                    population=self._population,
                    policy=comp_policy,
                    period=year,
                )
            except Exception as e:
                logger.error(
                    "event=portfolio_computation_error year=%d "
                    "policy_index=%d policy_type=%s adapter_version=%s",
                    year,
                    i,
                    policy_type_value,
                    adapter_version,
                )
                raise PortfolioComputationStepError(
                    f"Portfolio computation failed at year {year}, "
                    f"policy[{i}] '{policy_name}' ({policy_type_value}): "
                    f"{type(e).__name__}: {e}",
                    year=year,
                    adapter_version=adapter_version,
                    policy_index=i,
                    policy_name=policy_name,
                    policy_type=policy_type_value,
                    original_error=e,
                ) from e

            policy_results.append(result)

            row_count = result.output_fields.num_rows
            execution_records.append(
                {
                    "policy_index": i,
                    "policy_type": policy_type_value,
                    "policy_name": policy_name,
                    "adapter_version": adapter_version,
                    "row_count": row_count,
                }
            )

            logger.info(
                "event=portfolio_policy_computed year=%d policy_index=%d "
                "policy_type=%s adapter_version=%s row_count=%d",
                year,
                i,
                policy_type_value,
                adapter_version,
                row_count,
            )

        # Merge all results into a single table
        merged_table = _merge_policy_results(policy_results, self._portfolio)

        # Build merged ComputationResult for panel compatibility
        from reformlab.computation.types import ComputationResult

        merged_result = ComputationResult(
            output_fields=merged_table,
            adapter_version=adapter_version,
            period=year,
            metadata={"source": "portfolio", "policy_count": len(policy_results)},
            entity_tables={},
        )

        # Build portfolio metadata
        portfolio_metadata: dict[str, Any] = {
            "portfolio_name": self._portfolio.name,
            "policy_count": len(policy_results),
            "execution_records": execution_records,
            "execution_order": [
                r["policy_name"] for r in execution_records
            ],
        }

        # Build computation metadata (backward compat with runner.py)
        computation_metadata: dict[str, Any] = {
            "adapter_version": adapter_version,
            "computation_period": year,
            "computation_row_count": merged_table.num_rows,
            "source": "portfolio",
            "policy_count": len(policy_results),
        }

        # Update state immutably
        new_data = dict(state.data)
        new_data[COMPUTATION_RESULT_KEY] = merged_result
        new_data[PORTFOLIO_RESULTS_KEY] = policy_results

        new_metadata = dict(state.metadata)
        new_metadata[PORTFOLIO_METADATA_KEY] = portfolio_metadata
        new_metadata[COMPUTATION_METADATA_KEY] = computation_metadata

        logger.info(
            "event=portfolio_computation_complete year=%d portfolio=%s policy_count=%d",
            year,
            self._portfolio.name,
            len(policy_results),
        )

        return replace(state, data=new_data, metadata=new_metadata)


# ============================================================================
# Helpers
# ============================================================================


def _get_adapter_version(
    adapter: ComputationAdapter, year: int, step_name: str
) -> str:
    """Get adapter version with fallback to placeholder."""
    adapter_version = "<version-unavailable>"
    try:
        adapter_version = adapter.version()
    except Exception:
        logger.debug(
            "year=%d step_name=%s adapter_version=%s event=adapter_version_fallback",
            year,
            step_name,
            adapter_version,
        )
    return adapter_version


def _validate_policy_type(
    policy_type: PolicyType,
    index: int,
    policy_cfg: PortfolioPolicyConfig,
) -> None:
    """Validate that a policy type is a valid PolicyType enum value."""
    from reformlab.templates.schema import PolicyType as PolicyTypeEnum

    if not isinstance(policy_type, PolicyTypeEnum):
        raise PortfolioComputationStepError(
            f"Invalid policy_type at index {index}: {policy_type!r}",
            year=0,
            adapter_version="<not-started>",
            policy_index=index,
            policy_name=policy_cfg.name or str(policy_type),
            policy_type=str(policy_type),
        )


]]></file>
<file id="374c9051" path="tests/orchestrator/conftest.py" label="SOURCE CODE"><![CDATA[

"""Test fixtures for the orchestrator module."""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.computation.mock_adapter import MockAdapter
from reformlab.computation.types import PopulationData
from reformlab.orchestrator.portfolio_step import PortfolioComputationStep
from reformlab.orchestrator.types import OrchestratorConfig, YearState
from reformlab.templates.portfolios.portfolio import (
    PolicyConfig as PortfolioPolicyConfig,
)
from reformlab.templates.portfolios.portfolio import (
    PolicyPortfolio,
)
from reformlab.templates.schema import (
    CarbonTaxParameters,
    FeebateParameters,
    PolicyType,
    SubsidyParameters,
)


@pytest.fixture
def simple_config() -> OrchestratorConfig:
    """Return a simple orchestrator config with no steps."""
    return OrchestratorConfig(
        start_year=2025,
        end_year=2034,
        initial_state={"population": 1000},
        seed=42,
        step_pipeline=(),
    )


@pytest.fixture
def empty_pipeline_config() -> OrchestratorConfig:
    """Return config with explicitly empty pipeline."""
    return OrchestratorConfig(
        start_year=2025,
        end_year=2027,
        initial_state={},
        seed=None,
        step_pipeline=(),
    )


def increment_population(year: int, state: YearState) -> YearState:
    """Test step that increments population by year offset."""
    from dataclasses import replace

    new_data = dict(state.data)
    new_data["population"] = new_data.get("population", 0) + 100
    return replace(state, data=new_data)


def add_year_marker(year: int, state: YearState) -> YearState:
    """Test step that adds a year marker to metadata."""
    from dataclasses import replace

    new_metadata = dict(state.metadata)
    new_metadata[f"marker_{year}"] = True
    return replace(state, metadata=new_metadata)


def failing_step(year: int, state: YearState) -> YearState:
    """Test step that always fails."""
    raise ValueError(f"Intentional failure at year {year}")


def fail_at_year_2028(year: int, state: YearState) -> YearState:
    """Test step that fails only at year 2028."""
    if year == 2028:
        raise RuntimeError("Failing at year 2028 as expected")
    return state


@pytest.fixture
def config_with_steps() -> OrchestratorConfig:
    """Return config with two test steps."""
    return OrchestratorConfig(
        start_year=2025,
        end_year=2029,
        initial_state={"population": 1000},
        seed=12345,
        step_pipeline=(increment_population, add_year_marker),
    )


@pytest.fixture
def config_with_failing_step() -> OrchestratorConfig:
    """Return config with a step that fails at year 2028."""
    return OrchestratorConfig(
        start_year=2025,
        end_year=2030,
        initial_state={"population": 1000},
        seed=None,
        step_pipeline=(increment_population, fail_at_year_2028),
    )


# ============================================================================
# Portfolio fixtures (Story 12-3)
# ============================================================================


def _portfolio_compute_fn(
    population: PopulationData, policy: "PolicyConfig", period: int  # noqa: F821
) -> pa.Table:
    """Return policy-type-specific columns based on policy name."""
    hh_ids = [1, 2, 3]
    if "carbon_tax" in policy.name:
        return pa.table({
            "household_id": pa.array(hh_ids, type=pa.int64()),
            "tax_burden": pa.array([100.0, 200.0, 300.0]),
            "emissions": pa.array([2.5, 5.0, 7.5]),
        })
    if "subsidy" in policy.name:
        return pa.table({
            "household_id": pa.array(hh_ids, type=pa.int64()),
            "subsidy_amount": pa.array([50.0, 75.0, 100.0]),
        })
    if "feebate" in policy.name:
        return pa.table({
            "household_id": pa.array(hh_ids, type=pa.int64()),
            "net_impact": pa.array([-20.0, 10.0, 30.0]),
        })
    # Fallback
    return pa.table({
        "household_id": pa.array(hh_ids, type=pa.int64()),
        "value": pa.array([1.0, 2.0, 3.0]),
    })


@pytest.fixture
def portfolio_population() -> PopulationData:
    """Population data for portfolio tests."""
    table = pa.table({
        "person_id": pa.array([1, 2, 3]),
        "salary": pa.array([30000.0, 45000.0, 60000.0]),
    })
    return PopulationData(tables={"individu": table}, metadata={"source": "test"})


@pytest.fixture
def portfolio_mock_adapter() -> MockAdapter:
    """MockAdapter that returns different columns per policy type."""
    return MockAdapter(
        version_string="mock-portfolio-1.0.0",
        compute_fn=_portfolio_compute_fn,
    )


@pytest.fixture
def sample_portfolio() -> PolicyPortfolio:
    """2-policy portfolio: carbon tax + subsidy."""
    return PolicyPortfolio(
        name="test-2-policy",
        policies=(
            PortfolioPolicyConfig(
                policy_type=PolicyType.CARBON_TAX,
                policy=CarbonTaxParameters(rate_schedule={2025: 44.6, 2026: 50.0}),
                name="carbon_tax_baseline",
            ),
            PortfolioPolicyConfig(
                policy_type=PolicyType.SUBSIDY,
                policy=SubsidyParameters(rate_schedule={2025: 100.0, 2026: 120.0}),
                name="subsidy_green",
            ),
        ),
    )


@pytest.fixture
def three_policy_portfolio() -> PolicyPortfolio:
    """3-policy portfolio: carbon tax + subsidy + feebate."""
    return PolicyPortfolio(
        name="test-3-policy",
        policies=(
            PortfolioPolicyConfig(
                policy_type=PolicyType.CARBON_TAX,
                policy=CarbonTaxParameters(rate_schedule={2025: 44.6}),
                name="carbon_tax_baseline",
            ),
            PortfolioPolicyConfig(
                policy_type=PolicyType.SUBSIDY,
                policy=SubsidyParameters(rate_schedule={2025: 100.0}),
                name="subsidy_green",
            ),
            PortfolioPolicyConfig(
                policy_type=PolicyType.FEEBATE,
                policy=FeebateParameters(rate_schedule={2025: 0.05}),
                name="feebate_auto",
            ),
        ),
    )


@pytest.fixture
def portfolio_computation_step(
    portfolio_mock_adapter: MockAdapter,
    portfolio_population: PopulationData,
    three_policy_portfolio: PolicyPortfolio,
) -> PortfolioComputationStep:
    """PortfolioComputationStep with MockAdapter and 3-policy portfolio."""
    return PortfolioComputationStep(
        adapter=portfolio_mock_adapter,
        population=portfolio_population,
        portfolio=three_policy_portfolio,
    )


]]></file>
<file id="90dfc412" path="[ANTIPATTERNS - DO NOT REPEAT]" label="VIRTUAL CONTENT"><![CDATA[

# Epic 12 - Code Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during code review of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent implementation mistakes (race conditions, missing tests, weak assertions, etc.)

## Story 12-1 (2026-03-05)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Immutability breach - `list_policies()` returns direct reference to mutable `rate_schedule` dict, allowing external mutation of internal state. | Changed line 116 to return `dict(config.policy.rate_schedule)` instead of direct reference |
| high | Package integration gap - Portfolio types not exported from `reformlab.templates` | Added PolicyConfig, PolicyPortfolio, and portfolio exceptions to imports and __all__ list |
| high | Schema too permissive - No `additionalProperties: false` at root/policy levels, typos silently accepted | Added `additionalProperties: false` to root, policy item, and policy.parameters objects |
| high | Test data format mismatch - Test uses `redistribution_type` but loader expects `redistribution: {type: ...}` | Updated test to use canonical nested format |
| high | Unused imports - `yaml` imported but not used in test file, **Source**: Reviewer A | Removed unused `yaml` import |
| medium | Lint violations - Unused `PolicyType` import and unused `lines` variable | Removed unused imports |
| medium | Story traceability incomplete - Tasks marked incomplete despite implementation | Deferred (not applying - outside scope of code fixes) |


]]></file>
<file id="1d910d88" path="[Validator A]" label="VALIDATION OUTPUT"><![CDATA[

**🔥 ADVERSARIAL CODE REVIEW COMPLETE, User!**

**Story:** /Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/12-3-extend-orchestrator-to-execute-policy-portfolios.md

---

## 📊 Review Summary

| Category | Issues Found |
|----------|--------------|
| Git vs Story Discrepancies | 2 |
| AC Implementation Gaps | 1 |
| Task Completion Lies | 1 |
| SOLID Violations | 0 |
| Hidden Bugs | 1 |
| Performance Footguns | 1 |
| Security Vulnerabilities | 0 |
| **Total Issues** | **6** |

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🟠 IMPORTANT | Story File List incomplete (missing `templates.portfolios` changes). | STORY FILE vs git-diff | +1 |
| 🟡 MINOR | `__init__.py` imports not consistently grouped with comments. | src/reformlab/orchestrator/__init__.py | +0.3 |
| 🟠 IMPORTANT | `_merge_policy_results` uses `inner` join, silently dropping households not present in all policies. Violates AC2 and "Data contracts fail loudly." | src/reformlab/orchestrator/portfolio_step.py | +1 |
| 🟡 MINOR | `src/reformlab/population/pipeline.py` changed but not documented in story. | src/reformlab/population/pipeline.py | +0.3 |
| 🔴 CRITICAL | Core `PolicyPortfolio` implementation for Stories 12.1/12.2 is included in this story's `git-diff` but listed as dependencies/out-of-scope in story documentation. | STORY FILE vs git-diff | +3 |
| 🟡 MINOR | `tests/orchestrator/conftest.py` uses string literal for `PolicyConfig` type hint unnecessarily. | tests/orchestrator/conftest.py | +0.3 |
| 🟡 MINOR | `test_portfolio_step.py` uses stateful mock (`nonlocal call_count`) for error handling test. | tests/orchestrator/test_portfolio_step.py | +0.3 |
| 🟠 IMPORTANT | Test coverage for the new `templates.portfolios` subpackage is entirely absent from the `STORY FILE`'s test task list. | STORY FILE vs git-diff | +1 |
| 🟡 MINOR | In `_merge_policy_results`, repeated `append_column` calls for `renamed_table` create intermediate PyArrow tables inefficiently. | src/reformlab/orchestrator/portfolio_step.py | +0.3 |
| 🟢 CLEAN PASS | SOLID Principles | N/A | -0.5 |
| 🟢 CLEAN PASS | Abstraction Level Analysis | N/A | -0.5 |
| 🟢 CLEAN PASS | Security Vulnerability Scan | N/A | -0.5 |

### Evidence Score: 5.2

| Score | Verdict |
|-------|---------|
| **5.2** | **MAJOR REWORK** |

---

## 🏛️ Architectural Sins

✅ No significant architectural violations detected.

---

## 🐍 Pythonic Crimes &amp; Readability

- **Style Violation:** The `__all__` list in `src/reformlab/orchestrator/__init__.py` is neatly categorized with comments (e.g., `# Portfolio step (Story 12-3)`), but the actual import statements above it are not similarly grouped or commented. This inconsistency reduces readability and makes it harder to see which imports belong to which story or category at a glance.
  - 📍 `src/reformlab/orchestrator/__init__.py:32`
- **Type Safety:** In `tests/orchestrator/conftest.py`, the type hint for `policy` in the `_portfolio_compute_fn` function signature is `"PolicyConfig"` (a string literal). While `from __future__ import annotations` allows for this, `PolicyConfig` is already explicitly imported at the module level, making the string literal unnecessary and less direct.
  - 📍 `tests/orchestrator/conftest.py:139`

---

## ⚡ Performance &amp; Scalability

- **[LOW] Inefficient PyArrow Table Construction:** In `src/reformlab/orchestrator/portfolio_step.py`, the `_merge_policy_results` function constructs `renamed_table` (and eventually `merged`) by repeatedly calling `pa.Table.append_column` within a loop. Since `append_column` returns a *new* table object each time, this creates multiple intermediate PyArrow table objects. For tables with many columns, this can lead to unnecessary memory allocations and slight performance overhead compared to building a complete list of `pa.Field` objects or performing a more vectorized rename/reconstruction.
  - 📍 `src/reformlab/orchestrator/portfolio_step.py:160`
  - 💡 Fix: Collect all desired columns and their new names, then construct the final `pa.Table` in a single operation (e.g., `table.select(...)` or `pa.Table.from_arrays(...)`).

---

## 🐛 Correctness &amp; Safety

- **🐛 Bug:** The `_merge_policy_results` function in `src/reformlab/orchestrator/portfolio_step.py` uses an `inner` join (`join_type="inner"`) to combine the output tables of individual policies. This implies that if a household is present in the `output_fields` of one policy but not another, it will be silently dropped from the final merged PyArrow table. This directly violates Acceptance Criterion AC2, which states "one row per household per year containing output fields from every policy in the portfolio," implying all original households should be represented. It also goes against the "Data contracts fail loudly" rule, as it's a silent data transformation.
  - 📍 `src/reformlab/orchestrator/portfolio_step.py:177`
  - 🔄 Reproduction: Create a `PolicyPortfolio` where one policy's `compute_fn` (e.g., in `MockAdapter`) returns an `output_fields` table that intentionally excludes a `household_id` that is present in another policy's output. Observe the merged table's row count; it will be less than the expected total unique households.
- **🎭 Lying Test:** In `tests/orchestrator/test_portfolio_step.py`, the `test_adapter_failure_raises_portfolio_error` test uses a `nonlocal call_count` inside its `failing_at_second` mock function. This makes the `MockAdapter`'s behavior stateful and dependent on the exact iteration order of policies within `PortfolioComputationStep.execute()`. This approach is brittle and couples the test too tightly to the internal implementation details and execution order, making the test less reliable if the internal iteration logic changes.
  - 📍 `tests/orchestrator/test_portfolio_step.py:175`
  - 🤥 Why it lies: The test's ability to trigger the specific failure condition relies on a mutable, internal counter (`call_count`), rather than a stable characteristic of the `policy` object being passed to the mock. If the order of policies in the portfolio or the internal loop structure changes, the test might pass or fail incorrectly without reflecting the true behavior of the error handling for a specific policy.

---

## 🔧 Maintainability Issues

- **💣 Tech Debt:** The `STORY FILE`'s "File List" significantly under-reports the scope of changes for this story. It omits the creation and modification of an entire subpackage (`src/reformlab/templates/portfolios/`) and its corresponding tests, which are explicitly stated as dependencies (Story 12.1 and 12.2) but appear in the `git-diff` for *this* story. This misrepresentation of scope leads to a lack of transparency and makes tracking changes, conducting reviews, and understanding the true work for Story 12.3 extremely difficult. It falsely claims that extensive foundational work was "done" beforehand when it's part of the current changes.
  - 📍 `/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/12-3-extend-orchestrator-to-execute-policy-portfolios.md:275` (File List section)
  - 💥 Explosion radius: High. Affects project management, sprint planning, accurate reporting, and future maintainability as the documentation does not match reality.
- **💣 Tech Debt:** The `STORY FILE`'s "Tasks / Subtasks" lists a detailed set of tests (`Task 7`) only for `test_portfolio_step.py`. However, the `git-diff` reveals that numerous other test files were created for the newly introduced `reformlab.templates.portfolios` subpackage (e.g., `tests/templates/portfolios/test_composition.py`, `test_conflicts.py`, `test_portfolio.py`). The omission of these significant test tasks from the story's "Tasks / Subtasks" means that the documentation under-reports the actual testing effort and makes it seem as though these critical components (the portfolio model, conflict detection, and resolution) lack dedicated test coverage.
  - 📍 `/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/12-3-extend-orchestrator-to-execute-policy-portfolios.md:435` (Task 7 section)
  - 💥 Explosion radius: Medium. Impacts understanding of test coverage, verification of testing completeness, and could lead to oversight of regressions in the unlisted test areas.
- **💣 Tech Debt:** `src/reformlab/population/pipeline.py` was modified to replace `(time.monotonic() - step_start) * 1000.0` with `step_logs[-1].duration_ms`. While this is a valid refactoring to use a more standardized logging mechanism, this change (and potentially its context) is entirely unmentioned in the `STORY FILE`'s "File List" or "Dev Notes." This creates a documentation gap, making it harder to trace the reason for the change or understand its full impact without deep diving into the `git-diff`.
  - 📍 `src/reformlab/population/pipeline.py:503`
  - 💥 Explosion radius: Low. Minor impact, but indicates a potential for incomplete documentation across changes.

---

## 🛠️ Suggested Fixes

### 1. Correct `_merge_policy_results` Join Type

**File:** `src/reformlab/orchestrator/portfolio_step.py`
**Issue:** The use of `inner` join can lead to silent data loss for households not present in all policy outputs.

```diff
--- a/src/reformlab/orchestrator/portfolio_step.py
+++ b/src/reformlab/orchestrator/portfolio_step.py
@@ -174,7 +174,7 @@
             merged = merged.join(
                 renamed_table,
                 keys="household_id",
-                join_type="inner",
+                join_type="left outer", # Ensure all households from the first policy are retained.
             )
 
     return merged
```

### 2. Explicitly Build PyArrow Tables to Avoid Intermediate Objects

**File:** `src/reformlab/orchestrator/portfolio_step.py`
**Issue:** Repeated `append_column` calls can be inefficient.

```diff
--- a/src/reformlab/orchestrator/portfolio_step.py
+++ b/src/reformlab/orchestrator/portfolio_step.py
@@ -156,22 +156,24 @@
             prefix = f"{ptype}_"
 
         # Build rename mapping and join
-        renamed_table = renamed_table.append_column(
-            new_name, table.column(col_name)
-        )
+        current_columns = [table.column("household_id")]
+        current_column_names = ["household_id"]
+        for col_name in non_id_cols:
+            new_name = f"{prefix}{col_name}" if prefix else col_name
+            current_columns.append(table.column(col_name))
+            current_column_names.append(new_name)
+        renamed_table = pa.Table.from_arrays(current_columns, names=current_column_names)
 
         # Join on household_id
         if i == 0:
             # First policy: take all columns directly
-            for col_name in non_id_cols:
-                new_name = f"{prefix}{col_name}" if prefix else col_name
-                merged = merged.append_column(new_name, table.column(col_name))
+            merged = renamed_table
         else:
             # Subsequent policies: join on household_id
             merged = merged.join(
                 renamed_table,
                 keys="household_id",
-                join_type="inner",
+                join_type="left outer", # Maintain consistency with change #1
             )
 
     return merged
```

### 3. Simplify Type Hint in `tests/orchestrator/conftest.py`

**File:** `tests/orchestrator/conftest.py`
**Issue:** Unnecessary string literal for an imported type hint.

```diff
--- a/tests/orchestrator/conftest.py
+++ b/tests/orchestrator/conftest.py
@@ -136,7 +136,7 @@
 
 
 def _portfolio_compute_fn(
-    population: PopulationData, policy: "PolicyConfig", period: int  # noqa: F821
+    population: PopulationData, policy: PortfolioPolicyConfig, period: int
 ) -> pa.Table:
     """Return policy-type-specific columns based on policy name."""
     hh_ids = [1, 2, 3]
```

**Story:** /Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/12-3-extend-orchestrator-to-execute-policy-portfolios.md
**Evidence Score:** 5.2 → **MAJOR REWORK**

**Review Actions:**
- Issues Found: 9
- Issues Fixed: 0
- Action Items Created: 0

⚠️ Address the identified issues before proceeding.

]]></file>
<file id="557aedd2" path="[Validator B]" label="VALIDATION OUTPUT"><![CDATA[

**Adversarial Code Review Report**

Skill used: `bmad-bmm-code-review` (task explicitly matches adversarial code review workflow).

**Story:** `/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/12-3-extend-orchestrator-to-execute-policy-portfolios.md`

## Review Summary

| Category | Issues |
|---|---:|
| Git vs Story Discrepancies | 1 |
| AC Gaps / Partials | 3 |
| Task Claims Not Fully True | 1 |
| Hidden Bugs | 3 |
| Type/Immutability Problems | 2 |
| Total | 8 |

## Findings (ordered by severity)

1. **CRITICAL: Silent data loss in merge due `inner` join**
Evidence: [`portfolio_step.py:191`](/Users/lucas/Workspace/reformlab/src/reformlab/orchestrator/portfolio_step.py:191), [`portfolio_step.py:194`](/Users/lucas/Workspace/reformlab/src/reformlab/orchestrator/portfolio_step.py:194).  
Impact: households missing from any policy output are dropped without error, violating fail-loud data contract expectations. Runtime repro (`household_id` sets `{1,2,3}` and `{2,3,4}`) returns only 2 rows.  
Fix: validate identical `household_id` key sets before merging; raise `PortfolioComputationStepError` on mismatch.

2. **CRITICAL: Duplicate `household_id` causes row explosion / corrupted outputs**
Evidence: no uniqueness check before join in [`portfolio_step.py:134`](/Users/lucas/Workspace/reformlab/src/reformlab/orchestrator/portfolio_step.py:134) and join logic at [`portfolio_step.py:191`](/Users/lucas/Workspace/reformlab/src/reformlab/orchestrator/portfolio_step.py:191).  
Impact: duplicate keys produce cartesian multiplication (runtime repro: 3+3 input rows became 5 merged rows).  
Fix: enforce uniqueness of join keys per policy table and fail if duplicates exist.

3. **CRITICAL: AC5 invalid policy-type path is broken; throws `AttributeError` instead of structured domain error**
Evidence: [`portfolio.py:43`](/Users/lucas/Workspace/reformlab/src/reformlab/templates/portfolios/portfolio.py:43) accesses `self.policy_type.value` without type guard.  
Impact: malformed `policy_type` fails with raw `AttributeError` (`'str' object has no attribute 'value'`), not `PortfolioComputationStepError` with index/type as AC5 requires.  
Fix: add explicit type validation in `PolicyConfig.__post_init__` and/or hardened step-side validation path with structured error.

4. **IMPORTANT: Task 3.8 claim is inaccurate (`adapter_version` source)**
Evidence: story claim at [`story.md:62`](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/12-3-extend-orchestrator-to-execute-policy-portfolios.md:62) says merged `ComputationResult.adapter_version = first policy result`; implementation uses adapter-level version from [`portfolio_step.py:304`](/Users/lucas/Workspace/reformlab/src/reformlab/orchestrator/portfolio_step.py:304) and [`portfolio_step.py:373`](/Users/lucas/Workspace/reformlab/src/reformlab/orchestrator/portfolio_step.py:373).  
Impact: provenance mismatch when `compute()` result versions differ from `adapter.version()`.  
Fix: set merged and per-policy metadata adapter version from `policy_results[0].adapter_version` (or validate consistency across results).

5. **IMPORTANT: Immutability breach via mutable list in `YearState.data`**
Evidence: list created at [`portfolio_step.py:307`](/Users/lucas/Workspace/reformlab/src/reformlab/orchestrator/portfolio_step.py:307), stored directly at [`portfolio_step.py:401`](/Users/lucas/Workspace/reformlab/src/reformlab/orchestrator/portfolio_step.py:401).  
Impact: callers can mutate returned state (`clear()` etc.), undermining deterministic/state-token semantics.  
Fix: store `tuple(policy_results)` and type it immutably.

6. **IMPORTANT: AC2 is only partially validated; “10-year + all policy columns” is not tested**
Evidence: AC2 in story at [`story.md:17`](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/12-3-extend-orchestrator-to-execute-policy-portfolios.md:17); panel test runs only 3 years at [`test_portfolio_step.py:616`](/Users/lucas/Workspace/reformlab/tests/orchestrator/test_portfolio_step.py:616) and asserts only `tax_burden` at [`test_portfolio_step.py:630`](/Users/lucas/Workspace/reformlab/tests/orchestrator/test_portfolio_step.py:630).  
Impact: regression risk for 10-year behavior and missing-policy-column propagation in panel output.

7. **IMPORTANT: AC5 constructor validation scenario (invalid/unsupported policy type) is untested**
Evidence: error tests only cover adapter failure/version fallback at [`test_portfolio_step.py:381`](/Users/lucas/Workspace/reformlab/tests/orchestrator/test_portfolio_step.py:381) and [`test_portfolio_step.py:485`](/Users/lucas/Workspace/reformlab/tests/orchestrator/test_portfolio_step.py:485); no constructor-invalid-type test despite AC5 at [`story.md:26`](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/12-3-extend-orchestrator-to-execute-policy-portfolios.md:26).  
Impact: broken path in finding #3 escaped test suite.

8. **MINOR: Story file list does not match provided change scope**
Evidence: story lists only 4 files at [`story.md:223`](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/12-3-extend-orchestrator-to-execute-policy-portfolios.md:223), while provided `[git-diff]` artifact includes 26 changed files.  
Impact: reduced traceability; reviewers can miss scope creep or cross-story coupling.

## AC Verdict

| AC | Verdict | Notes |
|---|---|---|
| AC1 | Partial | Works on happy path; merge contract unsafe on key mismatch/duplicates. |
| AC2 | Partial | Not validated for 10-year and not asserted for all policy columns in panel. |
| AC3 | Implemented | Core files remained unchanged as required. |
| AC4 | Implemented | Backward-compat checks exist. |
| AC5 | Partial/Fail | Invalid policy-type path broken + missing tests. |
| AC6 | Partial | Determinism claims weakened by mutable stored list and unsafe join semantics. |
| AC7 | Partial | Metadata exists, but adapter-version provenance can be inaccurate. |

## Evidence Score

| Finding | Severity | Score |
|---|---|---:|
| Silent row drop on merge | CRITICAL | +3 |
| Duplicate-key row explosion | CRITICAL | +3 |
| Invalid policy-type path raises wrong exception | CRITICAL | +3 |
| Adapter-version provenance mismatch | IMPORTANT | +1 |
| Mutable list in state | IMPORTANT | +1 |
| AC2 test gap (10-year/all columns) | IMPORTANT | +1 |
| AC5 test gap | IMPORTANT | +1 |
| Git/story scope mismatch | MINOR | +0.3 |
| Clean pass: Security | CLEAN | -0.5 |
| Clean pass: Style/PEP8 basics | CLEAN | -0.5 |
| Clean pass: No obvious hot-path perf anti-pattern beyond merge contract | CLEAN | -0.5 |

**Total Evidence Score: 10.8**  
**Verdict: REJECT**

## Suggested Fix Set (ready to implement on approval)

1. Harden `_merge_policy_results()` with key-set equality + uniqueness checks and explicit `PortfolioComputationStepError` failures.
2. Store per-policy results as tuple, not list.
3. Align `adapter_version` semantics with task spec (use first policy result or assert consistency).
4. Add missing tests:
   - invalid/unsupported `policy_type` constructor path,
   - key mismatch failure,
   - duplicate `household_id` failure,
   - full AC2 10-year panel with all policy columns asserted.
5. Fix `PolicyConfig.__post_init__` to avoid raw `AttributeError` on malformed `policy_type`.

]]></file>
<file id="dc422a86" path="[git-diff]" label="VIRTUAL CONTENT"><![CDATA[

<!-- GIT_DIFF_START -->
 .gitignore                                         |   3 +
 bmad-assist.example.yaml                           | 109 +++
 bmad-assist.legacy.yaml                            | 108 +++
 bmad-assist.yaml                                   | 109 +++
 data/populations/demo-quickstart-100.csv           | 101 +++
 scripts/check_ai_usage.py                          | 317 ++++++++
 src/reformlab/orchestrator/__init__.py             |  15 +
 src/reformlab/orchestrator/portfolio_step.py       | 455 ++++++++++++
 src/reformlab/population/assumptions.py            |   8 +-
 src/reformlab/population/pipeline.py               |   2 +-
 src/reformlab/templates/__init__.py                |  27 +
 src/reformlab/templates/portfolios/__init__.py     |  40 +
 src/reformlab/templates/portfolios/composition.py  | 824 +++++++++++++++++++++
 src/reformlab/templates/portfolios/enums.py        |  27 +
 src/reformlab/templates/portfolios/exceptions.py   |  51 ++
 src/reformlab/templates/portfolios/portfolio.py    | 168 +++++
 .../templates/schema/portfolio.schema.json         | 135 ++++
 tests/orchestrator/conftest.py                     | 127 ++++
 tests/orchestrator/test_portfolio_step.py          | 762 +++++++++++++++++++
 tests/population/conftest.py                       |   1 +
 tests/population/test_assumptions.py               |  15 -
 tests/templates/portfolios/__init__.py             |   1 +
 tests/templates/portfolios/conftest.py             |  55 ++
 tests/templates/portfolios/test_composition.py     | 599 +++++++++++++++
 tests/templates/portfolios/test_conflicts.py       | 671 +++++++++++++++++
 tests/templates/portfolios/test_portfolio.py       | 418 +++++++++++
 26 files changed, 5125 insertions(+), 23 deletions(-)

diff --git a/scripts/check_ai_usage.py b/scripts/check_ai_usage.py
new file mode 100755
index 0000000..1e18c43
--- /dev/null
+++ b/scripts/check_ai_usage.py
@@ -0,0 +1,317 @@
+#!/usr/bin/env python3
+"""One-shot local usage snapshot for Claude Code, Codex, and Gemini CLI."""
+
+from __future__ import annotations
+
+import argparse
+import json
+import os
+import re
+import subprocess
+import sys
+from datetime import datetime, timezone
+from pathlib import Path
+from typing import Any
+
+
+def run_command(args: list[str]) -> tuple[int, str, str]:
+    try:
+        proc = subprocess.run(args, capture_output=True, text=True, check=False)
+    except FileNotFoundError:
+        return 127, "", "not installed"
+    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
+
+
+def summarize_cli_error(raw: str, fallback: str) -> str:
+    text = (raw or "").strip()
+    if not text:
+        return fallback
+
+    if "Unexpected token '??='" in text:
+        return "Node runtime in this shell is too old for this CLI (`??=` syntax). Use Node 22."
+
+    if "Missing optional dependency @openai/codex-" in text:
+        match = re.search(r"Missing optional dependency (@openai/codex-[^.\s]+)", text)
+        dep = match.group(1) if match else "@openai/codex-<platform>"
+        return f"Codex optional binary mismatch ({dep}). Reinstall under Node 22: npm install -g @openai/codex@latest"
+
+    lines = [line.strip() for line in text.splitlines() if line.strip()]
+    for line in lines:
+        if any(token in line for token in ("Error:", "SyntaxError:", "TypeError:", "ReferenceError:")):
+            return line[:220]
+    return lines[0][:220]
+
+
+def format_epoch(value: Any) -> str:
+    try:
+        if value is None:
+            return "n/a"
+        dt = datetime.fromtimestamp(int(value), tz=timezone.utc).astimezone()
+        return dt.strftime("%Y-%m-%d %H:%M:%S %Z")
+    except Exception:
+        return "n/a"
+
+
+def parse_iso(value: Any) -> datetime | None:
+    if not isinstance(value, str):
+        return None
+    try:
+        if value.endswith("Z"):
+            value = value[:-1] + "+00:00"
+        return datetime.fromisoformat(value)
+    except ValueError:
+        return None
+
+
+def fmt_int(value: Any) -> str:
+    try:
+        return f"{int(value):,}"
+    except Exception:
+        return "n/a"
+
+
+def newest_file(root: Path, pattern: str) -> Path | None:
+    if not root.exists():
+        return None
+    files = list(root.rglob(pattern))
+    if not files:
+        return None
+    return max(files, key=lambda p: p.stat().st_mtime)
+
+
+def newest_files(root: Path, pattern: str, limit: int = 30) -> list[Path]:
+    if not root.exists():
+        return []
+    files = list(root.rglob(pattern))
+    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
+    return files[:limit]
+
+
+def check_claude() -> list[str]:
+    lines = ["[Claude Code]"]
+    code, stdout, stderr = run_command(["claude", "auth", "status", "--json"])
+    if code == 127:
+        lines.append("- CLI: not installed")
+    elif code != 0:
+        err = summarize_cli_error(stderr or stdout, "auth status failed")
+        lines.append(f"- CLI auth check failed: {err}")
+    else:
+        try:
+            data = json.loads(stdout)
+            logged = "yes" if data.get("loggedIn") else "no"
+            subscription = data.get("subscriptionType", "n/a")
+            org_name = data.get("orgName", "n/a")
+            lines.append(f"- Logged in: {logged}")
+            lines.append(f"- Subscription: {subscription}")
+            lines.append(f"- Org: {org_name}")
+        except json.JSONDecodeError:
+            lines.append("- CLI auth output could not be parsed")
+
+    candidate_files = newest_files(Path.home() / ".claude" / "projects", "*.jsonl", limit=40)
+    if not candidate_files:
+        lines.append("- Local usage event: not found")
+    else:
+        latest_usage: dict[str, Any] | None = None
+        latest_model = "n/a"
+        latest_ts: datetime | None = None
+        latest_ts_raw = "n/a"
+        for latest_jsonl in candidate_files:
+            try:
+                with latest_jsonl.open("r", encoding="utf-8", errors="ignore") as handle:
+                    for raw in handle:
+                        raw = raw.strip()
+                        if not raw:
+                            continue
+                        try:
+                            item = json.loads(raw)
+                        except json.JSONDecodeError:
+                            continue
+                        message = item.get("message")
+                        if not isinstance(message, dict):
+                            continue
+                        usage = message.get("usage")
+                        if not isinstance(usage, dict):
+                            continue
+                        ts_raw = item.get("timestamp")
+                        ts = parse_iso(ts_raw)
+                        if latest_ts is None or (ts and ts >= latest_ts):
+                            latest_ts = ts or latest_ts
+                            latest_ts_raw = ts_raw if isinstance(ts_raw, str) else "n/a"
+                            latest_usage = usage
+                            latest_model = str(message.get("model", "n/a"))
+            except OSError:
+                continue
+
+        if not latest_usage:
+            lines.append("- Local usage event: not found")
+        else:
+            in_tokens = (
+                int(latest_usage.get("input_tokens", 0))
+                + int(latest_usage.get("cache_creation_input_tokens", 0))
+                + int(latest_usage.get("cache_read_input_tokens", 0))
+            )
+            out_tokens = int(latest_usage.get("output_tokens", 0))
+            lines.append(f"- Latest local model: {latest_model}")
+            lines.append(f"- Latest local tokens (in/out): {fmt_int(in_tokens)}/{fmt_int(out_tokens)}")
+            lines.append(f"- Latest local event time: {latest_ts_raw}")
+
+    lines.append("- Dashboard: https://console.anthropic.com/settings/usage")
+    return lines
+
+
+def check_codex() -> list[str]:
+    lines = ["[GPT-Codex]"]
+    code, stdout, stderr = run_command(["codex", "login", "status"])
+    if code == 127:
+        lines.append("- CLI: not installed")
+    elif code != 0:
+        err = summarize_cli_error(stderr or stdout, "login status failed")
+        lines.append(f"- CLI auth check failed: {err}")
+    else:
+        status_text = stdout or stderr or "available"
+        lines.append(f"- Login status: {status_text}")
+
+    latest_jsonl = newest_file(Path.home() / ".codex" / "sessions", "*.jsonl")
+    if latest_jsonl is None:
+        lines.append("- Local rate-limit snapshot: not found")
+    else:
+        latest_rate: dict[str, Any] | None = None
+        latest_usage: dict[str, Any] | None = None
+        latest_ts = "n/a"
+        try:
+            with latest_jsonl.open("r", encoding="utf-8", errors="ignore") as handle:
+                for raw in handle:
+                    raw = raw.strip()
+                    if not raw:
+                        continue
+                    try:
+                        item = json.loads(raw)
+                    except json.JSONDecodeError:
+                        continue
+                    if item.get("type") != "event_msg":
+                        continue
+                    payload = item.get("payload")
+                    if not isinstance(payload, dict) or payload.get("type") != "token_count":
+                        continue
+                    rate = payload.get("rate_limits")
+                    info = payload.get("info") or {}
+                    usage = info.get("total_token_usage")
+                    if isinstance(rate, dict):
+                        latest_rate = rate
+                        latest_usage = usage if isinstance(usage, dict) else None
+                        latest_ts = str(item.get("timestamp", "n/a"))
+        except OSError:
+            latest_rate = None
+
+        if not latest_rate:
+            lines.append("- Local rate-limit snapshot: not found")
+        else:
+            primary = latest_rate.get("primary", {})
+            secondary = latest_rate.get("secondary", {})
+            lines.append(
+                f"- Primary window used: {primary.get('used_percent', 'n/a')}% (resets {format_epoch(primary.get('resets_at'))})"
+            )
+            lines.append(
+                f"- Secondary window used: {secondary.get('used_percent', 'n/a')}% (resets {format_epoch(secondary.get('resets_at'))})"
+            )
+            if latest_usage:
+                total = latest_usage.get("total_tokens")
+                lines.append(f"- Latest local total tokens: {fmt_int(total)}")
+            lines.append(f"- Snapshot time: {latest_ts}")
+
+    lines.append("- API dashboard: https://platform.openai.com/usage")
+    lines.append("- ChatGPT plan dashboard: https://chatgpt.com/")
+    return lines
+
+
+def check_gemini() -> list[str]:
+    lines = ["[Gemini CLI]"]
+    code, stdout, stderr = run_command(["gemini", "--version"])
+    if code == 127:
+        lines.append("- CLI: not installed")
+    elif code != 0:
+        err = summarize_cli_error(stderr or stdout, "version check failed")
+        lines.append(f"- CLI check failed: {err}")
+    else:
+        lines.append(f"- CLI version: {stdout}")
+
+    has_env_auth = any(
+        os.getenv(key)
+        for key in ("GEMINI_API_KEY", "GOOGLE_GENAI_USE_VERTEXAI", "GOOGLE_GENAI_USE_GCA")
+    )
+    has_oauth = (Path.home() / ".gemini" / "oauth_creds.json").exists()
+    lines.append(f"- Auth configured: {'yes' if (has_env_auth or has_oauth) else 'no'}")
+
+    prompt_count = 0
+    latest_prompt_ts: datetime | None = None
+    latest_prompt_raw = "n/a"
+    tmp_root = Path.home() / ".gemini" / "tmp"
+    if tmp_root.exists():
+        for log_file in tmp_root.rglob("logs.json"):
+            try:
+                with log_file.open("r", encoding="utf-8", errors="ignore") as handle:
+                    data = json.load(handle)
+            except (OSError, json.JSONDecodeError):
+                continue
+            if not isinstance(data, list):
+                continue
+            for row in data:
+                if not isinstance(row, dict) or row.get("type") != "user":
+                    continue
+                prompt_count += 1
+                ts_raw = row.get("timestamp")
+                ts = parse_iso(ts_raw)
+                if ts and (latest_prompt_ts is None or ts >= latest_prompt_ts):
+                    latest_prompt_ts = ts
+                    latest_prompt_raw = str(ts_raw)
+    lines.append(f"- Local prompts recorded: {prompt_count}")
+    lines.append(f"- Latest local prompt time: {latest_prompt_raw}")
+    lines.append("- Dashboard: https://aistudio.google.com/")
+    return lines
+
+
+def open_dashboards() -> None:
+    urls = [
+        "https://console.anthropic.com/settings/usage",
+        "https://platform.openai.com/usage",
+        "https://chatgpt.com/",
+        "https://aistudio.google.com/",
+    ]
+    opener = None
+    if sys.platform == "darwin":
+        opener = "open"
+    elif sys.platform.startswith("linux"):
+        opener = "xdg-open"
+    if not opener:
+        return
+    for url in urls:
+        subprocess.run([opener, url], check=False, capture_output=True)
+
+
+def main() -> int:
+    parser = argparse.ArgumentParser(description="Check local usage snapshots for Claude/Codex/Gemini.")
+    parser.add_argument(
+        "--open-dashboards",
+        action="store_true",
+        help="Open provider usage dashboards in your browser.",
+    )
+    args = parser.parse_args()
+
+    print("AI usage snapshot (local + dashboard links)")
+    print(f"Generated: {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}")
+    print("Note: provider billing dashboards remain the source of truth.\n")
+
+    for section in (check_claude(), check_codex(), check_gemini()):
+        for line in section:
+            print(line)
+        print()
+
+    if args.open_dashboards:
+        open_dashboards()
+        print("Opened dashboards in browser.")
+
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/src/reformlab/orchestrator/__init__.py b/src/reformlab/orchestrator/__init__.py
index 53a49b2..5e445da 100644
--- a/src/reformlab/orchestrator/__init__.py
+++ b/src/reformlab/orchestrator/__init__.py
@@ -32,6 +32,10 @@ Public API:
 - PanelOutput: Household-by-year panel dataset from orchestrator run (Story 3-7)
 - compare_panels: Helper to compare baseline and reform panels (Story 3-7)
 - PANEL_VERSION: Panel format version for metadata (Story 3-7)
+- PortfolioComputationStep: Portfolio execution step (Story 12-3)
+- PortfolioComputationStepError: Error during portfolio step execution (Story 12-3)
+- PORTFOLIO_METADATA_KEY: Stable key for portfolio metadata (Story 12-3)
+- PORTFOLIO_RESULTS_KEY: Stable key for per-policy results (Story 12-3)
 """
 
 from reformlab.orchestrator.carry_forward import (
@@ -49,6 +53,12 @@ from reformlab.orchestrator.computation_step import (
 )
 from reformlab.orchestrator.errors import OrchestratorError
 from reformlab.orchestrator.panel import PANEL_VERSION, PanelOutput, compare_panels
+from reformlab.orchestrator.portfolio_step import (
+    PORTFOLIO_METADATA_KEY,
+    PORTFOLIO_RESULTS_KEY,
+    PortfolioComputationStep,
+    PortfolioComputationStepError,
+)
 from reformlab.orchestrator.runner import (
     SEED_LOG_KEY,
     STEP_EXECUTION_LOG_KEY,
@@ -113,4 +123,9 @@ __all__ = [
     "PanelOutput",
     "compare_panels",
     "PANEL_VERSION",
+    # Portfolio step (Story 12-3)
+    "PortfolioComputationStep",
+    "PortfolioComputationStepError",
+    "PORTFOLIO_METADATA_KEY",
+    "PORTFOLIO_RESULTS_KEY",
 ]
diff --git a/src/reformlab/orchestrator/portfolio_step.py b/src/reformlab/orchestrator/portfolio_step.py
new file mode 100644
index 0000000..dd322a0
--- /dev/null
+++ b/src/reformlab/orchestrator/portfolio_step.py
@@ -0,0 +1,455 @@
+"""Portfolio computation step for executing multi-policy portfolios.
+
+This module provides:
+- PortfolioComputationStep: OrchestratorStep for portfolio execution
+- PortfolioComputationStepError: Error during portfolio computation
+- PORTFOLIO_METADATA_KEY: Stable key for portfolio metadata in YearState.metadata
+- PORTFOLIO_RESULTS_KEY: Stable key for per-policy results in YearState.data
+
+Story 12.3 / FR44: Extend orchestrator to execute policy portfolios.
+"""
+
+from __future__ import annotations
+
+import logging
+from dataclasses import asdict, replace
+from typing import TYPE_CHECKING, Any
+
+import pyarrow as pa
+
+from reformlab.orchestrator.computation_step import (
+    COMPUTATION_METADATA_KEY,
+    COMPUTATION_RESULT_KEY,
+)
+
+if TYPE_CHECKING:
+    from reformlab.computation.adapter import ComputationAdapter
+    from reformlab.computation.types import (
+        ComputationResult,
+        PopulationData,
+    )
+    from reformlab.computation.types import PolicyConfig as ComputationPolicyConfig
+    from reformlab.orchestrator.types import YearState
+    from reformlab.templates.portfolios.portfolio import (
+        PolicyConfig as PortfolioPolicyConfig,
+    )
+    from reformlab.templates.portfolios.portfolio import PolicyPortfolio
+    from reformlab.templates.schema import PolicyType
+
+logger = logging.getLogger(__name__)
+
+
+# ============================================================================
+# Stable keys for portfolio data in YearState
+# ============================================================================
+
+PORTFOLIO_METADATA_KEY = "portfolio_metadata"
+PORTFOLIO_RESULTS_KEY = "portfolio_results"
+
+
+# ============================================================================
+# Error class
+# ============================================================================
+
+
+class PortfolioComputationStepError(Exception):
+    """Error during portfolio computation step execution.
+
+    Includes policy context (index, name, type), adapter version, year,
+    and original error for debugging and governance tracking.
+    """
+
+    def __init__(
+        self,
+        message: str,
+        *,
+        year: int,
+        adapter_version: str,
+        policy_index: int,
+        policy_name: str,
+        policy_type: str,
+        original_error: Exception | None = None,
+    ) -> None:
+        self.year = year
+        self.adapter_version = adapter_version
+        self.policy_index = policy_index
+        self.policy_name = policy_name
+        self.policy_type = policy_type
+        self.original_error = original_error
+        super().__init__(message)
+
+
+# ============================================================================
+# Bridge function
+# ============================================================================
+
+
+def _to_computation_policy(
+    policy_config: PortfolioPolicyConfig,
+) -> ComputationPolicyConfig:
+    """Convert a portfolio PolicyConfig to a computation PolicyConfig.
+
+    The portfolio layer uses typed PolicyParameters (frozen dataclass),
+    while the computation layer uses generic dict[str, Any].
+    """
+    from reformlab.computation.types import PolicyConfig as ComputationPolicyConfig
+
+    return ComputationPolicyConfig(
+        policy=asdict(policy_config.policy),
+        name=policy_config.name or policy_config.policy_type.value,
+        description=f"{policy_config.policy_type.value} policy",
+    )
+
+
+# ============================================================================
+# Result merging
+# ============================================================================
+
+
+def _merge_policy_results(
+    results: list[ComputationResult],
+    portfolio: PolicyPortfolio,
+) -> pa.Table:
+    """Merge output tables from multiple policies into a single table.
+
+    Strategy: join all output tables on ``household_id``. The first result
+    keeps column names as-is. Subsequent results prefix columns with
+    ``{policy_type}_`` to avoid collisions. If two policies share the

[... Git diff truncated due to size - see full diff with git command ...]

]]></file>
</context>
<variables>
<var name="author">BMad</var>
<var name="communication_language">English</var>
<var name="date">2026-03-06</var>
<var name="description">Master synthesizes code review findings and applies fixes to source code</var>
<var name="document_output_language">English</var>
<var name="epic_num">12</var>
<var name="implementation_artifacts">_bmad-output/implementation-artifacts</var>
<var name="installed_path">_bmad/bmm/workflows/4-implementation/code-review-synthesis</var>
<var name="instructions">/Users/lucas/Workspace/bmad-assist/src/bmad_assist/workflows/code-review-synthesis/instructions.xml</var>
<var name="name">code-review-synthesis</var>
<var name="output_folder">_bmad-output</var>
<var name="planning_artifacts">_bmad-output/planning-artifacts</var>
<var name="project_context" file_id="e58fb4dd" load_strategy="EMBEDDED" token_approx="2024">embedded in prompt, file id: e58fb4dd</var>
<var name="project_knowledge">docs</var>
<var name="project_name">reformlab</var>
<var name="reviewer_count">2</var>
<var name="session_id">91225abb-f4b8-4a9f-bdbd-e4fb5134df90</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_file" file_id="78cc87c5">embedded in prompt, file id: 78cc87c5</var>
<var name="story_id">12.3</var>
<var name="story_key">12-3-extend-orchestrator-to-execute-policy-portfolios</var>
<var name="story_num">3</var>
<var name="story_title">extend-orchestrator-to-execute-policy-portfolios</var>
<var name="template">False</var>
<var name="timestamp">20260306_1315</var>
<var name="user_name">User</var>
<var name="user_skill_level">expert</var>
<var name="validator_count"></var>
</variables>
<instructions><workflow>
  <critical>Communicate all responses in English and generate all documents in English</critical>
  <critical>You are the MASTER SYNTHESIS agent for CODE REVIEW findings.</critical>
  <critical>You have WRITE PERMISSION to modify SOURCE CODE files and story Dev Agent Record section.</critical>
  <critical>DO NOT modify story context (AC, Dev Notes content) - only Dev Agent Record (task checkboxes, completion notes, file list).</critical>
  <critical>All context (project_context.md, story file, anonymized reviews) is EMBEDDED below - do NOT attempt to read files.</critical>

  <step n="1" goal="Analyze reviewer findings">
    <action>Read all anonymized reviewer outputs (Reviewer A, B, C, D, etc.)</action>
    <action>For each issue raised:
      - Cross-reference with embedded project_context.md and story file
      - Cross-reference with source code snippets provided in reviews
      - Determine if issue is valid or false positive
      - Note reviewer consensus (if 3+ reviewers agree, high confidence issue)
    </action>
    <action>Issues with low reviewer agreement (1-2 reviewers) require extra scrutiny</action>
    <action>Group related findings that address the same underlying problem</action>
  </step>

  <step n="1.5" goal="Review Deep Verify code analysis" conditional="[Deep Verify Findings] section present">
    <critical>Deep Verify analyzed the actual source code files for this story.
      DV findings are based on static analysis patterns and may identify issues reviewers missed.</critical>

    <action>Review each DV finding:
      - CRITICAL findings: Security vulnerabilities, race conditions, resource leaks - must address
      - ERROR findings: Bugs, missing error handling, boundary issues - should address
      - WARNING findings: Code quality concerns - consider addressing
    </action>

    <action>Cross-reference DV findings with reviewer findings:
      - DV + Reviewers agree: High confidence issue, prioritize in fix order
      - Only DV flags: Verify in source code - DV has precise line numbers
      - Only reviewers flag: May be design/logic issues DV can't detect
    </action>

    <action>DV findings may include evidence with:
      - Code quotes (exact text from source)
      - Line numbers (precise location, when available)
      - Pattern IDs (known antipattern reference)
      Use this evidence when applying fixes.</action>

    <action>DV patterns reference:
      - CC-*: Concurrency issues (race conditions, deadlocks)
      - SEC-*: Security vulnerabilities
      - DB-*: Database/storage issues
      - DT-*: Data transformation issues
      - GEN-*: General code quality (null handling, resource cleanup)
    </action>
  </step>

  <step n="2" goal="Verify issues and identify false positives">
    <action>For each issue, verify against embedded code context:
      - Does the issue actually exist in the current code?
      - Is the suggested fix appropriate for the codebase patterns?
      - Would the fix introduce new issues or regressions?
    </action>
    <action>Document false positives with clear reasoning:
      - Why the reviewer was wrong
      - What evidence contradicts the finding
      - Reference specific code or project_context.md patterns
    </action>
  </step>

  <step n="3" goal="Prioritize by severity">
    <action>For verified issues, assign severity:
      - Critical: Security vulnerabilities, data corruption, crashes
      - High: Bugs that break functionality, performance issues
      - Medium: Code quality issues, missing error handling
      - Low: Style issues, minor improvements, documentation
    </action>
    <action>Order fixes by severity - Critical first, then High, Medium, Low</action>
    <action>For disputed issues (reviewers disagree), note for manual resolution</action>
  </step>

  <step n="4" goal="Apply fixes to source code">
    <critical>This is SOURCE CODE modification, not story file modification</critical>
    <critical>Use Edit tool for all code changes - preserve surrounding code</critical>
    <critical>After applying each fix group, run: pytest -q --tb=line --no-header</critical>
    <critical>NEVER proceed to next fix if tests are broken - either revert or adjust</critical>

    <action>For each verified issue (starting with Critical):
      1. Identify the source file(s) from reviewer findings
      2. Apply fix using Edit tool - change ONLY the identified issue
      3. Preserve code style, indentation, and surrounding context
      4. Log the change for synthesis report
    </action>

    <action>After each logical fix group (related changes):
      - Run: pytest -q --tb=line --no-header
      - If tests pass, continue to next fix
      - If tests fail:
        a. Analyze which fix caused the failure
        b. Either revert the problematic fix OR adjust implementation
        c. Run tests again to confirm green state
        d. Log partial fix failure in synthesis report
    </action>

    <action>Atomic commit guidance (for user reference):
      - Commit message format: fix(component): brief description (synthesis-12.3)
      - Group fixes by severity and affected component
      - Never commit unrelated changes together
      - User may batch or split commits as preferred
    </action>
  </step>

  <step n="5" goal="Refactor if needed">
    <critical>Only refactor code directly related to applied fixes</critical>
    <critical>Maximum scope: files already modified in Step 4</critical>

    <action>Review applied fixes for duplication patterns:
      - Same fix applied 2+ times across files = candidate for refactor
      - Only if duplication is in files already modified
    </action>

    <action>If refactoring:
      - Extract common logic to shared function/module
      - Update all call sites in modified files
      - Run tests after refactoring: pytest -q --tb=line --no-header
      - Log refactoring in synthesis report
    </action>

    <action>Do NOT refactor:
      - Unrelated code that "could be improved"
      - Files not touched in Step 4
      - Patterns that work but are just "not ideal"
    </action>

    <action>If broader refactoring needed:
      - Note it in synthesis report as "Suggested future improvement"
      - Do not apply - leave for dedicated refactoring story
    </action>
  </step>

  <step n="6" goal="Generate synthesis report">
    <critical>When updating story file, use atomic write pattern (temp file + rename).</critical>
    <action>Update story file Dev Agent Record section ONLY:
      - Mark completed tasks with [x] if fixes address them
      - Append to "Completion Notes List" subsection summarizing changes applied
      - Update file list with all modified files
    </action>

    <critical>Your synthesis report MUST be wrapped in HTML comment markers for extraction:</critical>
    <action>Produce structured output in this exact format (including the markers):</action>
    <output-format>
&lt;!-- CODE_REVIEW_SYNTHESIS_START --&gt;
## Synthesis Summary
[Brief overview: X issues verified, Y false positives dismissed, Z fixes applied to source files]

## Validations Quality
[For each reviewer: ID (A, B, C...), score (1-10), brief assessment]
[Note: Reviewers are anonymized - do not attempt to identify providers]

## Issues Verified (by severity)

### Critical
[Issues that required immediate fixes - list with evidence and fixes applied]
[Format: "- **Issue**: Description | **Source**: Reviewer(s) | **File**: path | **Fix**: What was changed"]
[If none: "No critical issues identified."]

### High
[Bugs and significant problems - same format]

### Medium
[Code quality issues - same format]

### Low
[Minor improvements - same format, note any deferred items]

## Issues Dismissed
[False positives with reasoning for each dismissal]
[Format: "- **Claimed Issue**: Description | **Raised by**: Reviewer(s) | **Dismissal Reason**: Why this is incorrect"]
[If none: "No false positives identified."]

## Changes Applied
[Complete list of modifications made to source files]
[Format for each change:
  **File**: [path/to/file.py]
  **Change**: [Brief description]
  **Before**:
  ```
  [2-3 lines of original code]
  ```
  **After**:
  ```
  [2-3 lines of updated code]
  ```
]
[If no changes: "No source code changes required."]

## Deep Verify Integration
[If DV findings were present, document how they were handled]

### DV Findings Fixed
[List DV findings that resulted in code changes]
[Format: "- **{ID}** [{SEVERITY}]: {Title} | **File**: {path} | **Fix**: {What was changed}"]

### DV Findings Dismissed
[List DV findings determined to be false positives]
[Format: "- **{ID}** [{SEVERITY}]: {Title} | **Reason**: {Why this is not an issue}"]

### DV-Reviewer Overlap
[Note findings flagged by both DV and reviewers - highest confidence fixes]
[If no DV findings: "Deep Verify did not produce findings for this story."]

## Files Modified
[Simple list of all files that were modified]
- path/to/file1.py
- path/to/file2.py
[If none: "No files modified."]

## Suggested Future Improvements
[Broader refactorings or improvements identified in Step 5 but not applied]
[Format: "- **Scope**: Description | **Rationale**: Why deferred | **Effort**: Estimated complexity"]
[If none: "No future improvements identified."]

## Test Results
[Final test run output summary]
- Tests passed: X
- Tests failed: 0 (required for completion)
&lt;!-- CODE_REVIEW_SYNTHESIS_END --&gt;
    </output-format>

  </step>

  <step n="6.5" goal="Write Senior Developer Review section to story file for dev_story rework detection">
    <critical>This section enables dev_story to detect that a code review has occurred and extract action items.</critical>
    <critical>APPEND this section to the story file - do NOT replace existing content.</critical>

    <action>Determine the evidence verdict from the [Evidence Score] section:
      - REJECT: Evidence score exceeds reject threshold
      - PASS: Evidence score is below accept threshold
      - UNCERTAIN: Evidence score is between thresholds
    </action>

    <action>Map evidence verdict to review outcome:
      - PASS → "Approved"
      - REJECT → "Changes Requested"
      - UNCERTAIN → "Approved with Reservations"
    </action>

    <action>Append to story file "## Senior Developer Review (AI)" section:
      ```
      ## Senior Developer Review (AI)

      ### Review: {current_date}
      - **Reviewer:** AI Code Review Synthesis
      - **Evidence Score:** {evidence_score} → {evidence_verdict}
      - **Issues Found:** {total_verified_issues}
      - **Issues Fixed:** {fixes_applied_count}
      - **Action Items Created:** {remaining_unfixed_count}
      ```
    </action>

    <critical>When evidence verdict is REJECT, you MUST create Review Follow-ups tasks.
      If "Action Items Created" count is &gt; 0, there MUST be exactly that many [ ] [AI-Review] tasks.
      Do NOT skip this step. Do NOT claim all issues are fixed if you reported deferred items above.</critical>

    <action>Find the "## Tasks / Subtasks" section in the story file</action>
    <action>Append a "#### Review Follow-ups (AI)" subsection with checkbox tasks:
      ```
      #### Review Follow-ups (AI)
      - [ ] [AI-Review] {severity}: {brief description of unfixed issue} ({file path})
      ```
      One line per unfixed/deferred issue, prefixed with [AI-Review] tag.
      Order by severity: Critical first, then High, Medium, Low.
    </action>

    <critical>ATDD DEFECT CHECK: Search test directories (tests/**) for test.fixme() calls in test files related to this story.
      If ANY test.fixme() calls remain in story-related test files, this is a DEFECT — the dev_story agent failed to activate ATDD RED-phase tests.
      Create an additional [AI-Review] task:
      - [ ] [AI-Review] HIGH: Activate ATDD tests — convert all test.fixme() to test() and ensure they pass ({test file paths})
      Do NOT dismiss test.fixme() as "intentional TDD methodology". After dev_story completes, ALL test.fixme() tests for the story MUST be converted to test().</critical>
  </step>

  </workflow></instructions>
<output-template></output-template>
</compiled-workflow>