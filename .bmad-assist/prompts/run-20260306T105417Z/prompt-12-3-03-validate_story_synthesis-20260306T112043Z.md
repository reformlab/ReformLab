<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 12 -->
<!-- Story: 3 -->
<!-- Phase: validate-story-synthesis -->
<!-- Timestamp: 20260306T112043Z -->
<compiled-workflow>
<mission><![CDATA[

Master Synthesis: Story 12.3

You are synthesizing 2 independent validator reviews.

Your mission:
1. VERIFY each issue raised by validators
   - Cross-reference with story content
   - Identify false positives (issues that aren't real problems)
   - Confirm valid issues with evidence

2. PRIORITIZE real issues by severity
   - Critical: Blocks implementation or causes major problems
   - High: Significant gaps or ambiguities
   - Medium: Improvements that would help
   - Low: Nice-to-have suggestions

3. SYNTHESIZE findings
   - Merge duplicate issues from different validators
   - Note validator consensus (if 3+ agree, high confidence)
   - Highlight unique insights from individual validators

4. APPLY changes to story file
   - You have WRITE PERMISSION to modify the story
   - CRITICAL: Before using Edit tool, ALWAYS Read the target file first
   - Use EXACT content from Read tool output as old_string, NOT content from this prompt
   - If Read output is truncated, use offset/limit parameters to locate the target section
   - Apply fixes for verified issues
   - Document what you changed and why

Output format:
## Synthesis Summary
## Issues Verified (by severity)
## Issues Dismissed (false positives with reasoning)
## Changes Applied

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

Status: ready-for-dev

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

- [ ] 1.1 Create new file `src/reformlab/orchestrator/portfolio_step.py` with module docstring referencing Story 12.3 / FR44
- [ ] 1.2 Define `PORTFOLIO_METADATA_KEY = "portfolio_metadata"` stable string constant
- [ ] 1.3 Define `PORTFOLIO_RESULTS_KEY = "portfolio_results"` stable string constant for per-policy results
- [ ] 1.4 Define `PortfolioComputationStepError(Exception)` with `year`, `adapter_version`, `policy_index`, `policy_type`, `original_error` attributes
- [ ] 1.5 Define `_to_computation_policy()` bridge function: converts `portfolios.PolicyConfig` (typed `PolicyParameters`) to `computation.types.PolicyConfig` (generic `dict[str, Any]`) via `dataclasses.asdict()`
- [ ] 1.6 Implement `PortfolioComputationStep` class with `__slots__`, `OrchestratorStep` protocol compliance (`name`, `depends_on`, `description`, `execute()`)

### Task 2: Implement `PortfolioComputationStep.__init__()` (AC: 1, 5)

- [ ] 2.1 Parameters: `adapter: ComputationAdapter`, `population: PopulationData`, `portfolio: PolicyPortfolio`, `name: str = "portfolio_computation"`, `depends_on: tuple[str, ...] = ()`, `description: str | None = None`
- [ ] 2.2 Store all constructor args in `__slots__`
- [ ] 2.3 Validate `portfolio.policies` is non-empty (should be guaranteed by `PolicyPortfolio.__post_init__` but defensive check)
- [ ] 2.4 Validate each `PolicyConfig.policy_type` has a valid `PolicyType` value (fail fast at construction, not at runtime)

### Task 3: Implement `execute()` method (AC: 1, 2, 5, 6, 7)

- [ ] 3.1 Get adapter version via `self._adapter.version()` with `"<version-unavailable>"` fallback (same pattern as `ComputationStep`)
- [ ] 3.2 Iterate over `self._portfolio.policies` **in tuple order** (deterministic)
- [ ] 3.3 For each policy: call `_to_computation_policy()` to create `computation.types.PolicyConfig`
- [ ] 3.4 For each policy: call `self._adapter.compute(population=self._population, policy=comp_policy, period=year)`
- [ ] 3.5 Collect all `ComputationResult` objects in an ordered list
- [ ] 3.6 Build per-policy execution records for metadata: `{"policy_index": i, "policy_type": policy_type.value, "policy_name": name, "adapter_version": version, "row_count": num_rows}`
- [ ] 3.7 Merge all `ComputationResult.output_fields` (`pa.Table`) into a single combined table via `_merge_policy_results()`
- [ ] 3.8 Create a single `ComputationResult` with the merged output table, store under `COMPUTATION_RESULT_KEY` (panel compatibility)
- [ ] 3.9 Store all individual `ComputationResult` objects under `PORTFOLIO_RESULTS_KEY` in `state.data` (per-policy access)
- [ ] 3.10 Store portfolio metadata under `PORTFOLIO_METADATA_KEY` in `state.metadata`
- [ ] 3.11 Also store standard `COMPUTATION_METADATA_KEY` with merged info (so `runner.py` can extract adapter_version from existing metadata path at line 342-346)
- [ ] 3.12 Return new `YearState` via `dataclasses.replace()` (immutable updates)

### Task 4: Implement `_merge_policy_results()` helper (AC: 1, 2)

- [ ] 4.1 Create module-level function `_merge_policy_results(results: list[ComputationResult], portfolio: PolicyPortfolio) -> pa.Table`
- [ ] 4.2 Strategy: join all output tables on `household_id`. For the first result, keep column names as-is. For subsequent results, prefix columns with `{policy_type}_` to avoid name collisions (e.g., `subsidy_amount`, `feebate_net_impact`)
- [ ] 4.3 Handle the case where `household_id` is missing from a result table (use row-index alignment as fallback, matching panel.py pattern at line 233-235)
- [ ] 4.4 Handle edge case: if all results have the same column names (e.g., two carbon tax policies after conflict resolution), prefix ALL with `{policy_type}_{index}_`
- [ ] 4.5 Result table must contain ALL columns from ALL policies, plus `household_id`
- [ ] 4.6 Deterministic column ordering: `household_id` first, then columns from each policy in portfolio order

### Task 5: Implement error handling (AC: 5)

- [ ] 5.1 Wrap individual `adapter.compute()` calls in try/except; on failure, raise `PortfolioComputationStepError` with policy context
- [ ] 5.2 Error message format: `"Portfolio computation failed at year {year}, policy[{idx}] ({policy_type}): {error_type}: {error}"`
- [ ] 5.3 Structured log on error: `event=portfolio_computation_error year={year} policy_index={idx} policy_type={type} adapter_version={version}`
- [ ] 5.4 Log INFO per policy execution: `event=portfolio_policy_computed year={year} policy_index={idx} policy_type={type} adapter_version={version} row_count={n}`
- [ ] 5.5 Log INFO on portfolio completion: `event=portfolio_computation_complete year={year} portfolio={name} policy_count={n}`

### Task 6: Update `orchestrator/__init__.py` exports (AC: 3, 4)

- [ ] 6.1 Add `PortfolioComputationStep`, `PortfolioComputationStepError`, `PORTFOLIO_METADATA_KEY`, `PORTFOLIO_RESULTS_KEY` to `__init__.py` exports under new section comment `# Portfolio step (Story 12-3)`
- [ ] 6.2 Add to `__all__` list

### Task 7: Write tests in `tests/orchestrator/test_portfolio_step.py` (AC: all)

- [ ] 7.1 Create test file with standard imports and module docstring referencing Story 12.3
- [ ] 7.2 **TestPortfolioStepProtocol** (AC3): Verify `PortfolioComputationStep` satisfies `OrchestratorStep` protocol (has `name`, `depends_on`, `execute`, isinstance check)
- [ ] 7.3 **TestPortfolioStepExecution** (AC1, AC2): Given 3-policy portfolio + `MockAdapter`, execute returns `YearState` with `COMPUTATION_RESULT_KEY` containing merged `ComputationResult`. Assert all policy columns present. Assert `MockAdapter.call_log` has 3 entries (one per policy). Assert `household_id` column present
- [ ] 7.4 **TestPortfolioStepMergedOutput** (AC2): Merged table has columns from all policies with correct prefixing. Column order is deterministic (household_id first, then by policy order)
- [ ] 7.5 **TestPortfolioStepMetadata** (AC7): `state.metadata[PORTFOLIO_METADATA_KEY]` contains portfolio name, policy count, per-policy records with policy_type/name/adapter_version/row_count
- [ ] 7.6 **TestPortfolioStepMetadata_ComputationKey** (AC3): `state.metadata[COMPUTATION_METADATA_KEY]` is present (backward compat with `runner.py` metadata extraction)
- [ ] 7.7 **TestPortfolioStepDeterminism** (AC6): Two runs with identical inputs produce identical `YearState` output (data and metadata)
- [ ] 7.8 **TestPortfolioStepErrorHandling** (AC5): Adapter failure at policy[1] raises `PortfolioComputationStepError` with correct `policy_index=1`, `policy_type`, `year`, `adapter_version`, `original_error`
- [ ] 7.9 **TestPortfolioStepErrorHandling_VersionFallback** (AC5): Adapter with failing `version()` uses `"<version-unavailable>"` fallback
- [ ] 7.10 **TestPortfolioStepBackwardCompat** (AC4): Existing `ComputationStep` continues to work unchanged in the same pipeline. Pipeline with `[PortfolioComputationStep, CarryForwardStep]` works
- [ ] 7.11 **TestPortfolioStepInPipeline** (AC1, AC4): Full orchestrator run with `PortfolioComputationStep` in step pipeline over 3 years. Verify yearly states contain portfolio results for each year
- [ ] 7.12 **TestPortfolioStepPanelIntegration** (AC2): Full orchestrator run → `PanelOutput.from_orchestrator_result()` produces panel with all policy columns across all years. Panel export to CSV/Parquet works
- [ ] 7.13 **TestPolicyConfigBridge** (AC1): `_to_computation_policy()` converts `portfolios.PolicyConfig` → `computation.types.PolicyConfig` correctly. `rate_schedule`, `exemptions`, custom fields are preserved in the dict
- [ ] 7.14 **TestPerPolicyResults** (AC1): `state.data[PORTFOLIO_RESULTS_KEY]` stores individual `ComputationResult` per policy, accessible by index

### Task 8: Add portfolio step fixtures to `tests/orchestrator/conftest.py` (AC: all)

- [ ] 8.1 Add `sample_portfolio` fixture: 2-policy portfolio (carbon tax + subsidy) with test parameters
- [ ] 8.2 Add `three_policy_portfolio` fixture: 3-policy portfolio (carbon tax + subsidy + feebate)
- [ ] 8.3 Add `portfolio_computation_step` fixture: `PortfolioComputationStep` with `MockAdapter` and sample population
- [ ] 8.4 Reuse existing `MockAdapter` patterns from `tests/orchestrator/test_computation_step.py`

### Task 9: Run quality checks (AC: all)

- [ ] 9.1 Run `uv run pytest tests/orchestrator/test_portfolio_step.py -v` — all tests pass
- [ ] 9.2 Run `uv run pytest tests/orchestrator/ -v` — all existing orchestrator tests still pass (no regressions)
- [ ] 9.3 Run `uv run pytest tests/templates/portfolios/ -v` — all portfolio tests still pass
- [ ] 9.4 Run `uv run ruff check src/reformlab/orchestrator/portfolio_step.py tests/orchestrator/test_portfolio_step.py`
- [ ] 9.5 Run `uv run mypy src/reformlab/orchestrator/portfolio_step.py` — passes strict mode
- [ ] 9.6 Run full test suite: `uv run pytest tests/ -v` — no regressions

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
1. First policy's columns keep their original names
2. Subsequent policies' columns are prefixed with `{policy_type}_` (e.g., `subsidy_amount`, `feebate_net_impact`)
3. `household_id` is shared (join key) — not duplicated
4. If two policies have the same `policy_type` (after conflict resolution), use `{policy_type}_{index}_` prefix

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

**`runner.py` metadata extraction** [Source: src/reformlab/orchestrator/runner.py:342-346]:
The orchestrator runner reads `COMPUTATION_METADATA_KEY` from `state.metadata` to extract adapter version. `PortfolioComputationStep` MUST populate this key for backward compatibility with the runner's step execution logging.

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
- [Source: src/reformlab/orchestrator/runner.py:342-346] — Runner metadata extraction requiring `COMPUTATION_METADATA_KEY`
- [Source: src/reformlab/orchestrator/panel.py:58-110] — `PanelOutput.from_orchestrator_result()` reading `COMPUTATION_RESULT_KEY`
- [Source: src/reformlab/templates/portfolios/portfolio.py] — `PolicyPortfolio` and `PolicyConfig` (portfolio type)
- [Source: src/reformlab/computation/types.py:29-35] — `PolicyConfig` (computation type)
- [Source: src/reformlab/orchestrator/step.py:42-70] — `OrchestratorStep` protocol
- [Source: src/reformlab/computation/mock_adapter.py] — `MockAdapter` for testing
- [Source: docs/project-context.md#Architecture] — Adapter isolation, step pipeline contract, frozen dataclasses
- [Source: _bmad-output/implementation-artifacts/12-1-*.md] — Story 12.1 decisions on `PolicyConfig` as new frozen dataclass
- [Source: _bmad-output/implementation-artifacts/12-2-*.md] — Story 12.2 code review, enum extraction, conflict resolution

## Dev Agent Record

### Agent Model Used


### Debug Log References


### Completion Notes List


### File List



]]></file>
<file id="1d910d88" path="[Validator A]" label="VALIDATION OUTPUT"><![CDATA[

# 🎯 Story Context Validation Report

<!-- report_header -->

**Story:** 12.3 - extend-orchestrator-to-execute-policy-portfolios
**Story File:** _bmad-output/implementation-artifacts/12-3-extend-orchestrator-to-execute-policy-portfolios.md
**Validated:** 2026-03-06
**Validator:** Quality Competition Engine

---

<!-- executive_summary -->

## Executive Summary

### Issues Overview

| Category | Found | Applied |
|----------|-------|---------|
| 🚨 Critical Issues | 1 | 0 |
| ⚡ Enhancements | 0 | 0 |
| ✨ Optimizations | 0 | 0 |
| 🤖 LLM Optimizations | 0 | 0 |

**Overall Assessment:** The story is exceptionally well-structured, detailed, and aligned with project architecture and conventions. It effectively mitigates common development risks through explicit instructions and clear scope boundaries. The only identified issue is its potentially large size, which could challenge single-sprint delivery for a human developer, but is still highly estimable due to the level of detail.

---

<!-- evidence_score_summary -->

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🔴 CRITICAL | Story Size / Estimability Risk: The story might be too large for a single sprint given the implementation and comprehensive testing requirements. | INVEST 'Small' Criterion | +3 |
| 🟢 CLEAN PASS | 13 |
| 🟢 CLEAN PASS | 13 |

### Evidence Score: -3.5

| Score | Verdict |
|-------|---------|
| **-3.5** | **EXCELLENT** |

---

<!-- story_quality_gate -->

## 🎯 Ruthless Story Validation 12.3

### INVEST Criteria Assessment

| Criterion | Status | Severity | Details |
|-----------|--------|----------|---------|
| **I**ndependent | ✅ Pass | 0/10 | Dependencies on Stories 12.1 and 12.2 are clearly acknowledged, and future dependencies (12.4, 12.5) are explicitly deferred, ensuring transparency and independence for the current scope. |
| **N**egotiable | ✅ Pass | 1/10 | The story is slightly prescriptive in its 'Tasks' and 'Dev Notes,' providing detailed implementation guidance (e.g., bridge function pseudo-code, merging strategy). While this offers less flexibility, it significantly aids an LLM agent in adhering to complex architectural patterns and avoids common pitfalls. |
| **V**aluable | ✅ Pass | 0/10 | The value is clearly articulated: enabling policy analysts to simulate bundled policies without custom pipeline code, directly contributing to core product goals (FR44). |
| **E**stimable | ✅ Pass | 0/10 | Requirements are exceptionally clear and detailed. The IN/OUT OF SCOPE sections are comprehensive, and potential technical risks (e.g., type bridging) are addressed with proposed solutions, making the story highly estimable. |
| **S**mall | 🟠 Fail | 3/10 | The story is comprehensive, encompassing new module creation, core logic development (including complex merging), extensive metadata handling, robust error handling, and a very detailed test plan (14 distinct test cases). For a human developer, this could be too large for a single sprint. For an LLM, it requires substantial output. |
| **T**estable | ✅ Pass | 0/10 | Acceptance criteria are specific, measurable, and directly mapped to a thorough testing plan (Task 7), including explicit coverage for edge cases and error handling. This ensures objective verification. |

### INVEST Violations

- **[3/10] Small:** The story's scope is quite large, combining significant implementation of core logic (new step, complex merging helper) with comprehensive testing (14 detailed test cases). Consider splitting the story into smaller, more manageable units, e.g., separating core logic from comprehensive testing, or breaking down the `execute()` and `_merge_policy_results()` implementations.

### Acceptance Criteria Issues

✅ Acceptance criteria are well-defined and testable.

### Hidden Risks and Dependencies

✅ No hidden dependencies or blockers identified.

### Estimation Reality-Check

**Assessment:** Potentially Underestimated / Large

While highly detailed and estimable, the sheer volume of implementation (new step, complex merge logic) and comprehensive testing (14 specific tests) might make this story too large for a typical single sprint for a human developer. For an LLM agent, it represents a substantial task with many sub-components to generate.

### Technical Alignment

**Status:** ✅ Excellent Alignment

✅ Story aligns with architecture.md patterns.

### Evidence Score: -3.5 → EXCELLENT

---

<!-- critical_issues_section -->

## 🚨 Critical Issues (Must Fix)

These are essential requirements, security concerns, or blocking issues that could cause implementation disasters.

### 1. Story Size / Potentially Overloaded Scope

**Impact:** Increased risk of incomplete delivery within a sprint; higher cognitive load during development and review; substantial token/turn consumption for LLM agents.
**Source:** INVEST 'Small' Criterion

**Problem:**
The story combines the creation of a new orchestrator step, implementation of a complex result merging helper function, detailed error handling, and a very comprehensive testing plan (14 distinct test cases) into a single unit. This scope, while clear, is quite large.

**Recommended Fix:**
Consider splitting the story. For example, 'Implement PortfolioComputationStep Core Logic' (Tasks 1, 2, 3, 5, 6) and 'Implement Portfolio Result Merging & Comprehensive Testing' (Tasks 4, 7, 8, 9). This would reduce the individual story size and allow for more incremental development and review.

---

<!-- enhancements_section -->

## ⚡ Enhancement Opportunities (Should Add)

✅ No significant enhancement opportunities identified.

---

<!-- optimizations_section -->

## ✨ Optimizations (Nice to Have)

✅ No additional optimizations identified.

---

<!-- llm_optimizations_section -->

## 🤖 LLM Optimization Improvements

✅ Story content is well-optimized for LLM processing.

---

<!-- changes_applied_section -->

## 📝 Changes Applied

No changes were applied to the story file. This report serves as documentation only.

---

<!-- competition_results -->

## 🏆 Competition Results

### Quality Metrics

| Metric | Score |
|--------|-------|
| Requirements Coverage | 100% |
| Architecture Alignment | 100% |
| Previous Story Integration | 100% |
| LLM Optimization Score | 95% |
| **Overall Quality Score** | **98%** |

### Disaster Prevention Assessment

- **Reinvention Prevention:** ✅ Pass Story leverages existing components and patterns, explicitly avoiding reinvention.
- **Technical Specification:** ✅ Pass API contracts are respected, and new technical specifications are well-defined and aligned with project standards.
- **File Structure:** ✅ Pass New file locations and naming conventions adhere to project guidelines.
- **Regression Prevention:** ✅ Pass Backward compatibility is a core AC, and comprehensive testing is planned to prevent regressions.
- **Implementation Quality:** ✅ Pass Highly detailed instructions, clear scope, and strong adherence to coding standards minimize implementation risks.

### Competition Outcome

🏆 **Validator identified 1 improvements** that enhance the story context.

---

**Report Generated:** 2026-03-06
**Validation Engine:** BMAD Method Quality Competition v1.0

]]></file>
<file id="557aedd2" path="[Validator B]" label="VALIDATION OUTPUT"><![CDATA[

# 🎯 Story Context Validation Report

**Story:** 12-3-extend-orchestrator-to-execute-policy-portfolios - extend-orchestrator-to-execute-policy-portfolios  
**Story File:** _bmad-output/implementation-artifacts/12-3-extend-orchestrator-to-execute-policy-portfolios.md  
**Validated:** 2026-03-06  
**Validator:** Quality Competition Engine

---

## Executive Summary

### Issues Overview

| Category | Found | Applied |
|----------|-------|---------|
| 🚨 Critical Issues | 3 | 0 |
| ⚡ Enhancements | 6 | 0 |
| ✨ Optimizations | 3 | 0 |
| 🤖 LLM Optimizations | 4 | 0 |

**Overall Assessment:** REJECT for dev-readiness. Core behavior is directionally correct, but critical requirements are under-specified or internally inconsistent (error contract, merge correctness, dependency on conflict validation).

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🔴 CRITICAL | AC5 requires policy **name** in failure context, but task/test contract omits it | Story 12.3 AC5 vs Tasks 1.4, 5.2, 7.8 | +3 |
| 🔴 CRITICAL | Merge fallback can silently row-align unrelated households, violating fail-loud data-contract rule | Story 12.3 Task 4.3 vs project-context “Data contracts fail loudly” | +3 |
| 🔴 CRITICAL | Story omits mandatory use of portfolio conflict validation/resolution before execution | Story 12.3 scope/tasks vs Story 12.2 compatibility layer | +3 |
| 🟠 IMPORTANT | “Invalid policy type at constructor” is weakly testable due upstream typed model invariants | AC5 + existing `PolicyConfig`/`PolicyPortfolio` validations | +1 |
| 🟠 IMPORTANT | Join semantics are underspecified for duplicate IDs, unequal row counts, null IDs | AC2 + Task 4.x | +1 |
| 🟠 IMPORTANT | No explicit contract for merged `ComputationResult.metadata` / `entity_tables` preservation | `computation.types.ComputationResult` + AC1/AC2 | +1 |
| 🟠 IMPORTANT | Story likely underestimated for 5 SP given scope and regression matrix | epics BKL-1203 estimate vs tasks 1-9 | +1 |
| 🟠 IMPORTANT | Reference drift risk (`docs/epics.md` path, hard line-coupled references) | Story references section | +1 |
| 🟡 MINOR | Task 2.3 (“non-empty”) conflicts with portfolio invariant (>=2 policies) | Story 12.3 Task 2.3 vs Story 12.1 model | +0.3 |
| 🟡 MINOR | Verbose repetitive dev notes bury critical implementation signals | Dev Notes structure | +0.3 |
| 🟢 CLEAN PASS | Valuable business outcome is clear and aligned to FR44 | User story + PRD FR44 | -0.5 |

### Evidence Score: 14.1

| Score | Verdict |
|-------|---------|
| **14.1** | **REJECT** |

---

## 🎯 Ruthless Story Validation 12.3

### INVEST Criteria Assessment

| Criterion | Status | Severity | Details |
|-----------|--------|----------|---------|
| **I**ndependent | ⚠️ Partial | 6/10 | Depends materially on Story 12.1/12.2 artifacts and conflict workflow, but dependency is not explicitly gated in story header. |
| **N**egotiable | ❌ Violated | 7/10 | Over-prescriptive HOW (exact helper names, logging strings, line-coupled behavior) reduces implementation flexibility. |
| **V**aluable | ✅ Pass | 1/10 | Clear analyst value and direct FR44 alignment. |
| **E**stimable | ⚠️ Partial | 6/10 | Estimation blocked by unresolved merge correctness and error-contract ambiguities. |
| **S**mall | ❌ Violated | 8/10 | Scope includes new module, orchestration integration, merge engine, fixture expansion, multiple integration tests, and full-suite regression. |
| **T**estable | ⚠️ Partial | 6/10 | Most ACs testable, but AC5 contract mismatch and constructor-invalid-type scenario are poorly specified. |

### INVEST Violations

- **[6/10] Independent:** Hidden dependency on prior conflict-resolution story behavior is not made explicit as a prerequisite.
- **[7/10] Negotiable:** Story dictates implementation internals rather than acceptance outcomes in several places.
- **[6/10] Estimable:** Critical edge-case behavior for table merging is not specified enough for reliable estimation.
- **[8/10] Small:** Story is too large for a clean single-sprint 5-point implementation.
- **[6/10] Testable:** AC5 and tests disagree on required error payload fields.

### Acceptance Criteria Issues

- **Conflict / Inconsistency:** AC5 requires policy name in failure context, but task/test definitions do not.
  - *Quote:* “error includes: which policy failed (index, **name**, type) …”
  - *Recommendation:* Add `policy_name` as a required `PortfolioComputationStepError` attribute and assert it in tests.

- **Ambiguity:** “combined effect” is not operationally defined.
  - *Quote:* “panel output reflects the combined effect of all policies”
  - *Recommendation:* Define explicitly whether “combined effect” means independent side-by-side outputs or true inter-policy dependency flow.

- **Untestable Edge Case Spec:** Join behavior for key quality failures is incomplete.
  - *Quote:* “join all output tables on `household_id`… fallback row-index alignment”
  - *Recommendation:* Specify behavior for duplicate keys, unequal row counts, missing key in some tables, and null/invalid IDs.

- **Ambiguity:** AC3 forbids changes to core files, but story still relies on behavior tightly coupled to those files.
  - *Quote:* “no changes to ... `panel.py` are required”
  - *Recommendation:* Convert to outcome-based requirement (“no breaking API changes”) instead of hard file immutability constraint.

- **Inconsistent Guard Requirement:** Constructor validation says non-empty while model invariant is >=2 policies.
  - *Quote:* “Validate `portfolio.policies` is non-empty”
  - *Recommendation:* Align to “at least 2 policies,” matching `PolicyPortfolio.__post_init__`.

- **Missing Requirement:** No AC for preserving existing `YearState.data/metadata` keys on update.
  - *Quote:* (implicit via Task 3.12 only)
  - *Recommendation:* Add explicit AC for immutable, non-destructive merge with existing state.

### Hidden Risks and Dependencies

- **Sequential dependency:** Story assumes completed and trusted Story 12.1/12.2 portfolio model and conflict logic.
  - *Impact:* Execution may proceed with invalid or unresolved conflicting portfolios.
  - *Mitigation:* Add explicit dependency gate and constructor/load-time requirement to validate/resolve conflicts before compute.

- **Data contract dependency:** Adapter outputs must be join-compatible at household granularity.
  - *Impact:* Silent mis-merges can corrupt simulation outputs.
  - *Mitigation:* Require fail-fast validation for join keys/row alignment, with explicit error modes.

- **Schema dependency:** Two `PolicyConfig` types plus conversion via `asdict()` can leak internal fields.
  - *Impact:* Unexpected adapter payload shape and inconsistent compute behavior.
  - *Mitigation:* Define strict bridge mapping contract (allowlist fields) instead of raw `asdict()`.

- **Regression dependency:** Existing downstream consumers may depend on first-policy unprefixed column names.
  - *Impact:* Non-deterministic naming expectations across portfolios.
  - *Mitigation:* Define deterministic naming contract independent of policy ordering assumptions.

### Estimation Reality-Check

**Assessment:** underestimated

The story is estimated at 5 SP in epics but includes cross-subsystem behavior definition, table-merge logic with edge cases, error taxonomy, backward compatibility validation, pipeline integration, and broad regression testing. Without tighter merge/error contracts, implementation risk is materially higher than a typical 5-point story.

### Technical Alignment

**Status:** Misaligned in critical areas

- **Architecture/data contract conflict:** Row-index fallback for missing `household_id` can silently coerce data.
  - *Architecture Reference:* project-context critical rule “Data contracts fail loudly.”
  - *Recommendation:* Require explicit validation failure unless a formally defined alignment mode is chosen and logged.

- **Boundary conflict with prior portfolio architecture:** Story does not mandate invoking `validate_compatibility` / `resolve_conflicts`.
  - *Architecture Reference:* Story 12.2 introduced compatibility/resolution as execution guardrails.
  - *Recommendation:* Add prerequisite: step consumes only validated/resolved portfolios or validates itself.

- **Result type incompleteness risk:** `ComputationResult` has `metadata` and `entity_tables`; merge contract ignores both.
  - *Architecture Reference:* `src/reformlab/computation/types.py`
  - *Recommendation:* Specify merged metadata/entity-tables behavior (preserve, merge, or explicitly empty with rationale).

- **Reference hygiene risk:** Story references `docs/epics.md`, but planning artifact path differs.
  - *Architecture Reference:* repository layout
  - *Recommendation:* Use actual artifact paths and avoid brittle line-number coupling where possible.

### Evidence Score: 14.1 → REJECT

---

## 🚨 Critical Issues (Must Fix)

### 1. AC5 Error Contract Is Internally Inconsistent

**Impact:** High risk of “passing tests but failing requirement” implementation.  
**Source:** AC5 vs Tasks 1.4/5.2/7.8

**Problem:**  
AC5 requires policy index, name, type, year, adapter version, original exception. Tasks and tests only require index/type/year/version/original error.

**Recommended Fix:**  
Update story contract to require and test `policy_name` explicitly in `PortfolioComputationStepError` attributes and message format.

### 2. Merge Rules Can Produce Silent Data Corruption

**Impact:** Incorrect panel outputs with no hard failure.  
**Source:** Task 4.2–4.4 + project-context data-contract rule

**Problem:**  
Current story allows row-index fallback without strict constraints. If row counts/order differ across policy outputs, merged rows can map different households together silently.

**Recommended Fix:**  
Define mandatory fail-fast checks for join compatibility. If fallback mode is allowed, specify exact preconditions and mandatory warning metadata.

### 3. Missing Execution Gate for Portfolio Conflict Validation

**Impact:** Incompatible policy bundles may execute and produce invalid “combined” results.  
**Source:** Story 12.3 tasks vs Story 12.2 compatibility/resolution design

**Problem:**  
Story 12.3 never requires validated/resolved portfolio input, despite Story 12.2 introducing explicit conflict detection/resolution.

**Recommended Fix:**  
Add AC/task: constructor or execute path must enforce validated/resolved portfolio state (or call compatibility resolution explicitly).

---

## ⚡ Enhancement Opportunities (Should Add)

### 1. Define Exact `PORTFOLIO_METADATA_KEY` Schema

**Benefit:** Removes ambiguity; improves deterministic tests and downstream consumption.  
**Source:** AC7 + Task 3.6/3.10

**Current Gap:**  
Field names/types/order are partially implied, not formally specified.

**Suggested Addition:**  
Add canonical metadata schema with required keys, value types, and deterministic ordering guarantees.

### 2. Specify `ComputationResult` Merge Semantics Beyond `output_fields`

**Benefit:** Prevents accidental loss of `entity_tables`/metadata.  
**Source:** `computation.types.ComputationResult`

**Current Gap:**  
Story defines merged table only.

**Suggested Addition:**  
Explicitly define how `adapter_version`, `period`, `metadata`, and `entity_tables` are populated in merged result.

### 3. Clarify “Combined Effect” vs “Independent Outputs”

**Benefit:** Avoids conceptual mismatch with analysts and developers.  
**Source:** AC1/AC2 wording + out-of-scope note on cross-policy flow

**Current Gap:**  
Text suggests economic interaction but implementation is independent computations + merge.

**Suggested Addition:**  
State that this story delivers “combined reporting output,” not causal inter-policy coupling.

### 4. Add Non-Destructive State Update AC

**Benefit:** Protects pipeline composability and backward compatibility.  
**Source:** Task 3.12 only

**Current Gap:**  
Not explicit in acceptance criteria.

**Suggested Addition:**  
Add AC: existing `YearState.data` and `YearState.metadata` entries remain intact after step execution.

### 5. Strengthen Test Matrix for Merge Edge Cases

**Benefit:** Prevents latent defects in production data variation.  
**Source:** Task 7.x coverage

**Current Gap:**  
No explicit tests for duplicate `household_id`, mismatched row counts, null IDs, or empty tables.

**Suggested Addition:**  
Add dedicated edge-case test class with strict expected outcomes (fail-fast or explicitly defined fallback behavior).

### 6. Make Dependency on Story 12.2 Explicit

**Benefit:** Reduces integration surprises and sequencing risk.  
**Source:** cross-story architecture

**Current Gap:**  
Dependency is implicit only.

**Suggested Addition:**  
Add `Dependencies: Story 12.1, 12.2 (portfolio model + conflict resolution)` near header.

---

## ✨ Optimizations (Nice to Have)

### 1. Reuse Existing Household-ID Normalization Logic

**Value:** Reduces duplicated logic and behavior drift.  
**Suggestion:** Reuse/adapt panel household-id normalization helper semantics instead of re-implementing divergence-prone variants.

### 2. Extract Shared Adapter-Version Fallback Pattern

**Value:** Keeps `ComputationStep` and `PortfolioComputationStep` behavior consistent.  
**Suggestion:** Introduce a small shared helper for version fallback and metadata construction.

### 3. Prefer Outcome-Oriented ACs over File-Immutability Clauses

**Value:** Improves maintainability while preserving compatibility intent.  
**Suggestion:** Replace “do not modify file X” with “public contract of X remains backward compatible.”

---

## 🤖 LLM Optimization Improvements

### 1. Collapse Repeated Scope Statements

**Issue:** Context overload  
**Token Impact:** High

**Current:**
```text
Multiple repeated “no changes to core files” statements across AC3, Scope Boundaries, and Files NOT to modify.
```

**Optimized:**
```text
Single immutable-contract section:
- Must preserve public behavior of adapter, orchestrator config, runner metadata extraction, and panel creation.
- Internal refactors allowed only if tests prove no behavioral change.
```

**Rationale:** Removes repetition and keeps the true constraint explicit.

### 2. Replace Narrative Merge Description with Decision Table

**Issue:** Ambiguity in implementation details  
**Token Impact:** Medium

**Current:**
```text
Merge all policy tables on household_id, prefix some columns, fallback by row index, handle edge cases...
```

**Optimized:**
```text
Decision table:
- Missing household_id: FAIL (or Fallback mode with explicit guard).
- Duplicate household_id: FAIL.
- Unequal key sets: OUTER JOIN with null-fill + warning metadata.
- Column collision: deterministic prefix rule with examples.
```

**Rationale:** Converts prose into executable requirements.

### 3. Normalize Error Contract Into One Canonical Spec

**Issue:** Contradictory requirements  
**Token Impact:** Medium

**Current:**
```text
AC5 requires index, name, type, year, adapter version, original exception; tasks/tests only assert subset.
```

**Optimized:**
```text
PortfolioComputationStepError required attributes:
year, adapter_version, policy_index, policy_name, policy_type, original_error
```

**Rationale:** Prevents drift between AC, implementation, and tests.

### 4. Remove Brittle Line-Number Coupling

**Issue:** Reference fragility  
**Token Impact:** Low

**Current:**
```text
“matching panel.py pattern at line 233-235”
```

**Optimized:**
```text
“matching panel household-id fallback helper behavior”
```

**Rationale:** Keeps references stable through refactors.

---

## 📝 Changes Applied

No changes were applied to the story file. This report serves as documentation only.

---

## 🏆 Competition Results

### Quality Metrics

| Metric | Score |
|--------|-------|
| Requirements Coverage | 72% |
| Architecture Alignment | 68% |
| Previous Story Integration | 64% |
| LLM Optimization Score | 58% |
| **Overall Quality Score** | **65%** |

### Disaster Prevention Assessment

- **Reinvention Prevention:** ⚠️ Partial - reuse opportunities noted but not enforced.
- **Technical Specification:** ❌ Risk - merge and error contracts can cause incorrect behavior.
- **File Structure Integrity:** ⚠️ Partial - mostly aligned, but reference hygiene issues exist.
- **Regression Safety:** ⚠️ Partial - core regressions considered, key edge cases missing.
- **Implementation Clarity:** ❌ Risk - critical ambiguities remain in AC interpretation.

### Competition Outcome

🏆 **Validator identified 16 improvements** that materially increase implementation safety and clarity.

---

**Report Generated:** 2026-03-06  
**Validation Engine:** BMAD Method Quality Competition v1.0

]]></file>
</context>
<variables>
<var name="author">BMad</var>
<var name="communication_language">English</var>
<var name="date">2026-03-06</var>
<var name="description">Master synthesizes validator findings and applies changes to story file</var>
<var name="document_output_language">English</var>
<var name="epic_num">12</var>
<var name="implementation_artifacts">_bmad-output/implementation-artifacts</var>
<var name="installed_path">_bmad/bmm/workflows/4-implementation/validate-story-synthesis</var>
<var name="instructions">/Users/lucas/Workspace/bmad-assist/src/bmad_assist/workflows/validate-story-synthesis/instructions.xml</var>
<var name="name">validate-story-synthesis</var>
<var name="output_folder">_bmad-output</var>
<var name="planning_artifacts">_bmad-output/planning-artifacts</var>
<var name="project_context" file_id="e58fb4dd" load_strategy="EMBEDDED" token_approx="2024">embedded in prompt, file id: e58fb4dd</var>
<var name="project_knowledge">docs</var>
<var name="project_name">reformlab</var>
<var name="session_id">4c449b88-e17e-4a0f-9db1-eb0789042491</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_file" file_id="78cc87c5">embedded in prompt, file id: 78cc87c5</var>
<var name="story_id">12.3</var>
<var name="story_key">12-3-extend-orchestrator-to-execute-policy-portfolios</var>
<var name="story_num">3</var>
<var name="story_title">extend-orchestrator-to-execute-policy-portfolios</var>
<var name="template">False</var>
<var name="timestamp">20260306_1220</var>
<var name="user_name">User</var>
<var name="user_skill_level">expert</var>
<var name="validator_count">2</var>
</variables>
<instructions><workflow>
  <critical>Communicate all responses in English and generate all documents in English</critical>

  <critical>You are the MASTER SYNTHESIS agent. Your role is to evaluate validator findings
    and produce a definitive synthesis with applied fixes.</critical>
  <critical>You have WRITE PERMISSION to modify the story file being validated.</critical>
  <critical>All context (project_context.md, story file, anonymized validations) is EMBEDDED below - do NOT attempt to read files.</critical>
  <critical>Apply changes to story file directly using atomic write pattern (temp file + rename).</critical>

  <step n="1" goal="Analyze validator findings">
    <action>Read all anonymized validator outputs (Validator A, B, C, D, etc.)</action>
    <action>For each issue raised:
      - Cross-reference with story content and project_context.md
      - Determine if issue is valid or false positive
      - Note validator consensus (if 3+ validators agree, high confidence issue)
    </action>
    <action>Issues with low validator agreement (1-2 validators) require extra scrutiny</action>
  </step>

  <step n="1.5" goal="Review Deep Verify technical findings" conditional="[Deep Verify Findings] section present">
    <critical>Deep Verify provides automated technical analysis that complements validator reviews.
      DV findings focus on: patterns, boundary cases, assumptions, temporal issues, security, and worst-case scenarios.</critical>

    <action>Review each DV finding:
      - CRITICAL findings: Must be addressed - these indicate serious technical issues
      - ERROR findings: Should be addressed unless clearly false positive
      - WARNING findings: Consider addressing, document if dismissed
    </action>

    <action>Cross-reference DV findings with validator findings:
      - If validators AND DV flag same issue: High confidence, prioritize fix
      - If only DV flags issue: Verify technically valid, may be edge case validators missed
      - If only validators flag issue: Normal processing per step 1
    </action>

    <action>For each DV finding, determine:
      - Is this a genuine issue in the story specification?
      - Does the story need to address this edge case/scenario?
      - Is this already covered but DV missed it? (false positive)
    </action>

    <action>DV findings with patterns (CC-*, SEC-*, DB-*, DT-*, GEN-*) reference known antipatterns.
      Treat pattern-matched findings as higher confidence.</action>
  </step>

  <step n="2" goal="Verify and prioritize issues">
    <action>For verified issues, assign severity:
      - Critical: Blocks implementation or causes major problems
      - High: Significant gaps or ambiguities that need attention
      - Medium: Improvements that would help quality
      - Low: Nice-to-have suggestions
    </action>
    <action>Document false positives with clear reasoning for dismissal:
      - Why the validator was wrong
      - What evidence contradicts the finding
      - Reference specific story content or project_context.md
    </action>
  </step>

  <step n="3" goal="Apply changes to story file">
    <action>For each verified issue (starting with Critical, then High), apply fix directly to story file</action>
    <action>Changes should be natural improvements:
      - DO NOT add review metadata or synthesis comments to story
      - DO NOT reference the synthesis or validation process
      - Preserve story structure, formatting, and style
      - Make changes look like they were always there
    </action>
    <action>For each change, log in synthesis output:
      - File path modified
      - Section/line reference (e.g., "AC4", "Task 2.3")
      - Brief description of change
      - Before snippet (2-3 lines context)
      - After snippet (2-3 lines context)
    </action>
    <action>Use atomic write pattern for story modifications to prevent corruption</action>
  </step>

  <step n="4" goal="Generate synthesis report">
    <critical>Your synthesis report MUST be wrapped in HTML comment markers for extraction:</critical>
    <action>Produce structured output in this exact format (including the markers):</action>
    <output-format>
&lt;!-- VALIDATION_SYNTHESIS_START --&gt;
## Synthesis Summary
[Brief overview: X issues verified, Y false positives dismissed, Z changes applied to story file]

## Validations Quality
[For each validator: name, score, comments]
[Summary of validation quality - 1-10 scale]

## Issues Verified (by severity)

### Critical
[Issues that block implementation - list with evidence and fixes applied]
[Format: "- **Issue**: Description | **Source**: Validator(s) | **Fix**: What was changed"]

### High
[Significant gaps requiring attention]

### Medium
[Quality improvements]

### Low
[Nice-to-have suggestions - may be deferred]

## Issues Dismissed
[False positives with reasoning for each dismissal]
[Format: "- **Claimed Issue**: Description | **Raised by**: Validator(s) | **Dismissal Reason**: Why this is incorrect"]

## Deep Verify Integration
[If DV findings were present, document how they were handled]

### DV Findings Addressed
[List DV findings that resulted in story changes]
[Format: "- **{ID}** [{SEVERITY}]: {Title} | **Action**: {What was changed}"]

### DV Findings Dismissed
[List DV findings determined to be false positives or not applicable]
[Format: "- **{ID}** [{SEVERITY}]: {Title} | **Reason**: {Why dismissed}"]

### DV-Validator Overlap
[Note any findings flagged by both DV and validators - these are high confidence]
[If no DV findings: "Deep Verify did not produce findings for this story."]

## Changes Applied
[Complete list of modifications made to story file]
[Format for each change:
  **Location**: [File path] - [Section/line]
  **Change**: [Brief description]
  **Before**:
  ```
  [2-3 lines of original content]
  ```
  **After**:
  ```
  [2-3 lines of updated content]
  ```
]
&lt;!-- VALIDATION_SYNTHESIS_END --&gt;
    </output-format>

  </step>

  <step n="5" goal="Final verification">
    <action>Verify all Critical and High issues have been addressed</action>
    <action>Confirm story file changes are coherent and preserve structure</action>
    <action>Ensure synthesis report is complete with all sections populated</action>
  </step>
</workflow></instructions>
<output-template></output-template>
</compiled-workflow>