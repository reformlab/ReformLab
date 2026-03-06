<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 12 -->
<!-- Story: 5 -->
<!-- Phase: validate-story-synthesis -->
<!-- Timestamp: 20260306T134952Z -->
<compiled-workflow>
<mission><![CDATA[

Master Synthesis: Story 12.5

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
<file id="8233c651" path="_bmad-output/implementation-artifacts/12-5-implement-multi-portfolio-comparison-and-notebook-demo.md" label="STORY FILE"><![CDATA[


# Story 12.5: Implement Multi-Portfolio Comparison and Notebook Demo

Status: ready-for-dev
Dependencies: Story 12.1 (PolicyPortfolio model), Story 12.2 (conflict detection), Story 12.3 (orchestrator portfolio execution), Story 12.4 (registry portfolio versioning)

## Story

As a **policy analyst**,
I want to compare results across multiple policy portfolios side-by-side, with aggregate cross-comparison metrics and a pedagogical notebook demo,
so that I can determine which portfolio best achieves my policy objectives (e.g., maximizes welfare, minimizes fiscal cost) and share these analyses with colleagues.

## Acceptance Criteria

### AC1: Multi-portfolio side-by-side comparison
Given 3 completed portfolio runs (each against the same baseline population), when comparison is invoked per indicator type (distributional, fiscal, welfare), then a side-by-side `ComparisonResult` table shows all indicator metrics per portfolio. Each comparison table uses portfolio labels as column names.

### AC2: Cross-comparison aggregate metrics
Given multi-portfolio comparison results, when cross-comparison metrics are computed, then aggregate metrics are available per portfolio: (a) total fiscal revenue, (b) total fiscal cost, (c) fiscal balance, (d) mean net welfare change (if welfare indicators are included). Each metric ranks portfolios from best to worst, answering questions like "which portfolio maximizes welfare?" and "which has lowest fiscal cost?".

### AC3: Backward compatibility with pairwise comparison API
Given the Phase 1 `compare_scenarios()` API, when used with 2 portfolio `ScenarioInput` objects, then it works identically to pre-portfolio behavior. The `compare_portfolios()` convenience function transparently delegates to `compare_scenarios()` for each indicator type and adds cross-comparison metrics on top.

### AC4: Notebook demo runs in CI
Given the notebook demo, when run in CI, then it demonstrates: (a) creating 3 distinct portfolios, (b) executing each against the same baseline population, (c) computing distributional and fiscal comparison tables, (d) computing cross-comparison metrics, (e) visualizing portfolio differences with charts. The notebook completes without errors.

### AC5: Input validation and error handling
Given fewer than 2 portfolios, when `compare_portfolios()` is called, then a `ValueError` is raised with a clear message. Given portfolio inputs with non-unique labels, when called, then a `ValueError` is raised. Given an empty portfolio panel (no rows), when indicators are computed, then warnings are collected (not exceptions) and the comparison proceeds with available data.

### AC6: Export support
Given a `PortfolioComparisonResult`, when exported, then each per-indicator-type comparison table can be exported to CSV/Parquet independently via the existing `ComparisonResult.export_csv()` / `export_parquet()` methods. The cross-comparison metrics are available as a dict for programmatic access.

## Tasks / Subtasks

### Task 1: Define portfolio comparison types (AC: 1, 2, 5, 6)

- [ ] 1.1 Create `src/reformlab/indicators/portfolio_comparison.py` with module docstring referencing Story 12.5 and FR45
- [ ] 1.2 Define `PortfolioComparisonInput` frozen dataclass: `label: str`, `panel: PanelOutput`. Validate label is non-empty in `__post_init__`. This takes `PanelOutput` (not `SimulationResult`) to match existing indicator function signatures and enable composition
- [ ] 1.3 Define `PortfolioComparisonConfig` frozen dataclass with fields: `baseline_label: str | None = None` (defaults to first portfolio), `indicator_types: tuple[str, ...] = ("distributional", "fiscal")` (which indicator types to compute), `include_welfare: bool = False` (welfare requires baseline vs reform so opt-in), `include_deltas: bool = True`, `include_pct_deltas: bool = True`, `distributional_kwargs: dict[str, Any] = field(default_factory=dict)` (passed to `compute_distributional_indicators`), `fiscal_kwargs: dict[str, Any] = field(default_factory=dict)` (passed to `compute_fiscal_indicators`), `welfare_kwargs: dict[str, Any] = field(default_factory=dict)` (passed to `compute_welfare_indicators`)
- [ ] 1.4 Define `CrossComparisonMetric` frozen dataclass: `criterion: str` (e.g., `"max_mean_welfare_net_change"`, `"min_fiscal_cost"`), `best_portfolio: str` (label of the portfolio ranked first), `value: float` (metric value for the best portfolio), `all_values: dict[str, float]` (metric value per portfolio label, ordered by ranking)
- [ ] 1.5 Define `PortfolioComparisonResult` frozen dataclass: `comparisons: dict[str, ComparisonResult]` (keyed by indicator type string, e.g., `{"distributional": ..., "fiscal": ...}`), `cross_metrics: tuple[CrossComparisonMetric, ...]` (aggregate metrics across portfolios), `portfolio_labels: tuple[str, ...]` (ordered labels), `metadata: dict[str, Any]`, `warnings: list[str]`

### Task 2: Implement `compare_portfolios()` function (AC: 1, 3, 5)

- [ ] 2.1 Implement input validation: minimum 2 portfolios, unique labels, non-empty labels, labels don't conflict with reserved column names (same checks as `compare_scenarios()`)
- [ ] 2.2 For each indicator type in `config.indicator_types`, compute indicators for each portfolio by calling the appropriate indicator function (`compute_distributional_indicators`, `compute_fiscal_indicators`) with the portfolio's `PanelOutput`. Collect per-portfolio `IndicatorResult` objects
- [ ] 2.3 For welfare indicators (when `config.include_welfare is True`): use the baseline portfolio's panel as the baseline panel, compute welfare indicators for each non-baseline portfolio via `compute_welfare_indicators(baseline_panel, reform_panel, **config.welfare_kwargs)`. Collect per-portfolio `IndicatorResult` objects. Skip the baseline portfolio itself (welfare is baseline vs reform, so baseline vs baseline is meaningless)
- [ ] 2.4 For each indicator type, wrap per-portfolio `IndicatorResult` objects as `ScenarioInput(label=portfolio_label, indicators=indicator_result)` and call `compare_scenarios(scenarios, config=ComparisonConfig(baseline_label=config.baseline_label, include_deltas=config.include_deltas, include_pct_deltas=config.include_pct_deltas))`. Store resulting `ComparisonResult` keyed by indicator type string
- [ ] 2.5 Call `_compute_cross_comparison_metrics()` (Task 3) with the per-portfolio indicator results to produce `CrossComparisonMetric` tuples
- [ ] 2.6 Build metadata dict: `{"portfolio_labels": labels, "baseline_label": resolved_baseline, "indicator_types": list(config.indicator_types), "include_welfare": config.include_welfare, "config": ...}`
- [ ] 2.7 Collect all warnings from each `ComparisonResult` into a unified warnings list, prefixed with indicator type (e.g., `"[distributional] Non-overlapping keys..."`)
- [ ] 2.8 Return `PortfolioComparisonResult` with all collected results

### Task 3: Implement cross-comparison metrics computation (AC: 2)

- [ ] 3.1 Create `_compute_cross_comparison_metrics()` internal function accepting: `fiscal_indicators: dict[str, IndicatorResult] | None` (keyed by portfolio label), `welfare_indicators: dict[str, IndicatorResult] | None` (keyed by portfolio label), `portfolio_labels: list[str]`
- [ ] 3.2 For fiscal metrics: extract per-portfolio aggregate values from `IndicatorResult.indicators` list. For each portfolio, compute: `total_revenue` (sum of `FiscalIndicators.revenue` across years), `total_cost` (sum of `FiscalIndicators.cost` across years), `fiscal_balance` (sum of `FiscalIndicators.balance` across years). Create `CrossComparisonMetric` for each: `"max_fiscal_revenue"` (highest revenue first), `"min_fiscal_cost"` (lowest cost first), `"max_fiscal_balance"` (highest balance first)
- [ ] 3.3 For welfare metrics: extract per-portfolio aggregate values from `IndicatorResult.indicators` list. For each portfolio, compute: `mean_net_change` (mean of `WelfareIndicators.net_change` across all groups and years), `total_winners` (sum of `WelfareIndicators.winner_count` across groups), `total_losers` (sum of `WelfareIndicators.loser_count` across groups). Create `CrossComparisonMetric` for each: `"max_mean_welfare_net_change"` (highest net change first), `"max_total_winners"` (most winners first), `"min_total_losers"` (fewest losers first)
- [ ] 3.4 Sort each metric's `all_values` dict by ranking order (best first). For "max_*" criteria, sort descending; for "min_*" criteria, sort ascending
- [ ] 3.5 Return tuple of all `CrossComparisonMetric` objects. If fiscal_indicators is None, skip fiscal metrics. If welfare_indicators is None, skip welfare metrics. If both are None, return empty tuple

### Task 4: Update module exports (AC: all)

- [ ] 4.1 Add imports and exports to `src/reformlab/indicators/__init__.py`: `PortfolioComparisonInput`, `PortfolioComparisonConfig`, `PortfolioComparisonResult`, `CrossComparisonMetric`, `compare_portfolios`
- [ ] 4.2 Update module docstring in `__init__.py` to mention portfolio comparison (add `Story 12.5` reference)

### Task 5: Build notebook demo (AC: 4)

- [ ] 5.1 Create `notebooks/demo/epic12_portfolio_comparison.ipynb` following the pattern of `notebooks/advanced.ipynb`
- [ ] 5.2 **Section 0 — Introduction** (markdown): Explain what portfolio comparison is, prerequisites (quickstart + advanced notebooks), and what the reader will learn
- [ ] 5.3 **Section 1 — Imports and Setup** (code): Import ReformLab API, portfolio types, indicator comparison types, visualization utilities. Resolve population path relative to notebook location. Load the demo population CSV
- [ ] 5.4 **Section 2 — Create Three Portfolios** (code + markdown per portfolio):
  - Portfolio A: "Carbon Tax Only" — single carbon tax at €50/tCO2 (2-policy portfolio: carbon tax + minimal subsidy)
  - Portfolio B: "Carbon Tax + Subsidy" — carbon tax at €50/tCO2 + vehicle subsidy at €5000
  - Portfolio C: "Green Transition" — carbon tax at €80/tCO2 + vehicle subsidy at €7000 + feebate
  - Use `PolicyConfig`, `PolicyPortfolio` from `reformlab.templates.portfolios`
  - Show `portfolio.list_policies()` for each
- [ ] 5.5 **Section 3 — Execute All Three Portfolios** (code): For each portfolio, create a `PortfolioComputationStep`, configure `RunConfig` with `ScenarioConfig`, and call `run_scenario()`. Use the same population, seed, and year range (2025-2034) for fair comparison. Store results as dict `{label: SimulationResult}`
- [ ] 5.6 **Section 4 — Distributional Comparison** (code + markdown): Extract `panel_output` from each result. Create `PortfolioComparisonInput` objects. Call `compare_portfolios()` with distributional indicators. Display the comparison table with `show()`. Create a grouped bar chart showing mean carbon tax burden by decile per portfolio
- [ ] 5.7 **Section 5 — Fiscal Comparison** (code + markdown): Call `compare_portfolios()` with fiscal indicators. Display revenue/cost comparison table. Create a line chart showing fiscal balance over time per portfolio
- [ ] 5.8 **Section 6 — Cross-Comparison Metrics** (code + markdown): Display the `cross_metrics` from the comparison result. Show which portfolio has highest revenue, lowest cost, best fiscal balance. Format as a summary table
- [ ] 5.9 **Section 7 — Using the Phase 1 API Directly** (code + markdown): Demonstrate that `compare_scenarios()` works with portfolio results (backward compatibility). Show it's the same as the per-indicator-type result from `compare_portfolios()`. One-liner comparison
- [ ] 5.10 **Section 8 — Export Results** (code + markdown): Export comparison tables to Parquet. Export panel outputs. Verify round-trip
- [ ] 5.11 **Section 9 — Next Steps** (markdown): Summary of what was learned, link to EPIC-13 (custom templates in portfolios) and future GUI

### Task 6: Write tests in `tests/indicators/test_portfolio_comparison.py` (AC: all)

- [ ] 6.1 Create test file with module docstring referencing Story 12.5
- [ ] 6.2 Add fixtures in `tests/indicators/conftest.py`: `portfolio_panels` fixture returning 3 `PanelOutput` objects with different numeric values (simulating different portfolio outcomes). Use inline PyArrow table construction. Each panel: 30 households × 3 years (2025-2027), with columns `household_id`, `year`, `income`, `carbon_tax`, `subsidy_amount`. Portfolio A: carbon_tax=500 per household. Portfolio B: carbon_tax=500, subsidy_amount=200. Portfolio C: carbon_tax=800, subsidy_amount=300
- [ ] 6.3 **TestComparePortfoliosBasic** (AC1): Compare 3 portfolios with distributional indicators. Assert `comparisons` dict has `"distributional"` key. Assert comparison table has columns for each portfolio label. Assert table has rows (non-empty)
- [ ] 6.4 **TestComparePortfoliosFiscal** (AC1): Compare 3 portfolios with fiscal indicators (config with `fiscal_kwargs=FiscalConfig(revenue_fields=["carbon_tax"], cost_fields=["subsidy_amount"])`). Assert `comparisons` dict has `"fiscal"` key. Assert comparison table has expected columns
- [ ] 6.5 **TestComparePortfoliosWelfare** (AC1, AC2): Compare 3 portfolios with `include_welfare=True`. Assert `comparisons` dict has `"welfare"` key. Assert welfare comparison uses baseline panel vs each reform panel. Assert baseline label is not in welfare comparison (baseline vs itself is skipped)
- [ ] 6.6 **TestCrossComparisonMetrics** (AC2): Compare 3 portfolios with fiscal indicators. Assert `cross_metrics` tuple is non-empty. Assert metrics include `"max_fiscal_revenue"`, `"min_fiscal_cost"`, `"max_fiscal_balance"`. Assert each metric has `best_portfolio`, `value`, `all_values` with 3 entries. Assert `all_values` is sorted by ranking (best first)
- [ ] 6.7 **TestCrossComparisonMetricsWelfare** (AC2): Compare with welfare. Assert metrics include `"max_mean_welfare_net_change"`, `"max_total_winners"`, `"min_total_losers"`
- [ ] 6.8 **TestBackwardCompatibility** (AC3): Use `compare_scenarios()` directly with 2 portfolio `ScenarioInput` objects. Assert it produces valid `ComparisonResult`. Compare with `compare_portfolios()` result for same 2 portfolios — per-indicator comparison table should be equivalent
- [ ] 6.9 **TestComparePortfoliosValidation** (AC5): Test fewer than 2 portfolios raises `ValueError`. Test duplicate labels raises `ValueError`. Test empty labels raises `ValueError`. Test labels conflicting with reserved names raises `ValueError`
- [ ] 6.10 **TestComparePortfoliosExport** (AC6): Compare portfolios, export each comparison to CSV and Parquet via `ComparisonResult.export_csv()` / `export_parquet()`. Verify round-trip (read back and compare table shapes). Use `tmp_path` fixture
- [ ] 6.11 **TestComparePortfoliosMetadata** (AC1): Assert `metadata` dict contains `portfolio_labels`, `baseline_label`, `indicator_types`. Assert `warnings` is a list
- [ ] 6.12 **TestComparePortfoliosConfig** (AC1): Test custom config: `baseline_label` set to non-first portfolio. Test `include_deltas=False` produces no delta columns. Test `indicator_types=("fiscal",)` produces only fiscal comparison

### Task 7: Run quality checks (AC: all)

- [ ] 7.1 Run `uv run pytest tests/indicators/test_portfolio_comparison.py -v` — all tests pass
- [ ] 7.2 Run `uv run pytest tests/indicators/ -v` — all indicator tests pass (no regressions)
- [ ] 7.3 Run `uv run ruff check src/reformlab/indicators/portfolio_comparison.py tests/indicators/test_portfolio_comparison.py`
- [ ] 7.4 Run `uv run mypy src/reformlab/indicators/portfolio_comparison.py` — passes strict mode
- [ ] 7.5 Run full test suite: `uv run pytest tests/ -v`

## Dev Notes

### Architecture Decisions

**Design: `compare_portfolios()` as a convenience wrapper over `compare_scenarios()`**

The existing `compare_scenarios()` already supports N-way comparison (2+ `ScenarioInput` objects) with delta computation against a baseline. It handles join key alignment, null handling, and schema detection for all indicator types (decile, region, fiscal).

`compare_portfolios()` does NOT reimplement comparison logic. It:
1. Computes indicators for each portfolio (calling existing `compute_*_indicators()` functions)
2. Wraps each portfolio's `IndicatorResult` as a `ScenarioInput` with the portfolio label
3. Calls `compare_scenarios()` for each indicator type
4. Adds cross-comparison aggregate metrics on top

This approach:
- Avoids duplicating the comparison engine
- Ensures backward compatibility (AC3)
- Keeps the API surface small
- Leverages battle-tested N-way comparison logic from Story 4.5

**Design: `PanelOutput` as input, not `SimulationResult`**

`compare_portfolios()` accepts `PortfolioComparisonInput(label, panel)` where `panel` is `PanelOutput`, not `SimulationResult`. This matches existing indicator function signatures (`compute_distributional_indicators(panel)`, `compute_fiscal_indicators(panel)`, etc.) and enables composition — panels can come from `SimulationResult.panel_output`, from disk (Parquet files), or from manual construction.

Users extract panels from simulation results: `PortfolioComparisonInput(label="Green2030", panel=result.panel_output)`.

**Design: Cross-comparison metrics as post-hoc aggregation**

Cross-comparison metrics (`CrossComparisonMetric`) are computed from the per-portfolio `IndicatorResult` objects, not from the `ComparisonResult` tables. This is because:
- `ComparisonResult` tables are in long-form (one row per metric per group per year)
- Aggregate metrics need to sum/average across groups and years
- Working with the structured `IndicatorResult.indicators` list (typed dataclass instances) is more reliable than parsing table rows

Metrics are intentionally simple: sums and means across indicator instances. No complex aggregation formulas. The cross-comparison answers: "which portfolio scores best on this simple aggregate?"

**Design: Welfare indicators are opt-in**

`PortfolioComparisonConfig.include_welfare` defaults to `False` because welfare indicators require a baseline panel vs. each reform panel (two-panel computation). The baseline is the portfolio labeled `baseline_label`. If the user enables welfare but all portfolios are different reforms (no "baseline"), the function raises a clear error.

When welfare is enabled, the baseline portfolio is excluded from welfare comparison (comparing baseline vs. itself is meaningless), so the welfare `ComparisonResult` has N-1 scenario columns.

### Key Interfaces to Follow

**Existing `compare_scenarios()` API** [Source: src/reformlab/indicators/comparison.py:406-557]:
```python
def compare_scenarios(
    scenarios: list[ScenarioInput],
    config: ComparisonConfig | None = None,
) -> ComparisonResult:
```
- Already handles 2+ scenarios
- Validates: min 2, unique labels, compatible schemas, reserved names
- Produces delta and pct_delta columns vs baseline
- Returns `ComparisonResult` with table, metadata, warnings

**Indicator computation functions** [Source: src/reformlab/indicators/]:
```python
# Distributional
compute_distributional_indicators(panel: PanelOutput, config=None) -> IndicatorResult

# Fiscal
compute_fiscal_indicators(panel: PanelOutput, config=None) -> IndicatorResult

# Welfare (requires baseline + reform panels)
compute_welfare_indicators(baseline: PanelOutput, reform: PanelOutput, config=None) -> IndicatorResult
```

**Indicator result types** [Source: src/reformlab/indicators/types.py]:
```python
@dataclass
class IndicatorResult:
    indicators: Sequence[DecileIndicators | RegionIndicators | WelfareIndicators | FiscalIndicators]
    metadata: dict[str, Any]
    warnings: list[str]

@dataclass
class FiscalIndicators:
    field_name: str
    year: int | None
    revenue: float
    cost: float
    balance: float
    cumulative_revenue: float | None
    cumulative_cost: float | None
    cumulative_balance: float | None

@dataclass
class WelfareIndicators:
    field_name: str
    group_type: str
    group_value: int | str
    year: int | None
    winner_count: int
    loser_count: int
    neutral_count: int
    mean_gain: float
    mean_loss: float
    median_change: float
    total_gain: float
    total_loss: float
    net_change: float
```

**Portfolio types** [Source: src/reformlab/templates/portfolios/portfolio.py]:
```python
@dataclass(frozen=True)
class PolicyConfig:
    policy_type: PolicyType
    policy: PolicyParameters
    name: str = ""

@dataclass(frozen=True)
class PolicyPortfolio:
    name: str
    policies: tuple[PolicyConfig, ...]
    version: str = "1.0"
    description: str = ""
    resolution_strategy: str = "error"
```

**PortfolioComputationStep** [Source: src/reformlab/orchestrator/portfolio_step.py]:
```python
class PortfolioComputationStep:
    def __init__(self, adapter, population, portfolio, *, name="portfolio_computation"): ...
    def execute(self, year: int, state: YearState) -> YearState: ...
```

**ScenarioInput and ComparisonConfig** [Source: src/reformlab/indicators/comparison.py:33-64]:
```python
@dataclass
class ScenarioInput:
    label: str
    indicators: IndicatorResult

@dataclass
class ComparisonConfig:
    baseline_label: str | None = None
    include_deltas: bool = True
    include_pct_deltas: bool = True
```

**Notebook execution in CI** [Source: notebooks/advanced.ipynb pattern]:
- Notebooks resolve paths via `_NB_DIR = Path(__file__).parent if "__file__" in dir() else Path(".")`
- Use `create_quickstart_adapter()` for demo execution (no real OpenFisca required)
- Population path: `_NB_DIR / "../data/populations/demo-quickstart-100.csv"`
- All notebooks use `seed=42` for determinism

**Public API run functions** [Source: src/reformlab/interfaces/api.py]:
```python
def run_scenario(
    config: RunConfig | ScenarioConfig | Path | dict[str, Any],
    adapter: ComputationAdapter | None = None,
    *,
    steps: tuple[PipelineStep, ...] | None = None,
    initial_state: dict[str, Any] | None = None,
    skip_memory_check: bool = False,
) -> SimulationResult
```

### Notebook Demo Patterns

**From `notebooks/advanced.ipynb` (47 cells):**

1. Imports resolve paths relative to notebook location
2. Uses `create_quickstart_adapter()` with explicit `carbon_tax_rate` and `year`
3. The demo adapter applies a fixed formula — doesn't read per-year rate_schedule
4. Comparison uses `compare_scenarios()` with `ScenarioInput` wrappers
5. Visualization uses `create_figure()` from `reformlab.visualization` + matplotlib
6. Each section starts with markdown explaining the concept, followed by code
7. Verification cells use `print("✓ ...")` pattern

**Important demo adapter limitation:** The `create_quickstart_adapter()` applies a generic carbon tax formula. When running portfolios with different policy types (subsidy, feebate), the adapter still computes the same `carbon_tax` column. For the demo, this means:
- All portfolio runs produce the same column structure
- The "difference" between portfolios comes from using different `carbon_tax_rate` values when creating adapters
- The demo should use **different adapters per portfolio** with different rates to simulate different outcomes

**Alternative approach for notebook:** Create separate adapters with different `carbon_tax_rate` values (e.g., 44.0, 50.0, 80.0) to simulate the effect of different policy portfolios. Then compare using `compare_portfolios()`. This is honest about the demo adapter limitation while still demonstrating the comparison API.

### Existing Error Pattern

Indicator module errors use `ValueError` (not custom exceptions) [Source: src/reformlab/indicators/comparison.py:433-490]:
```python
raise ValueError(f"Comparison requires at least 2 scenarios, got {len(scenarios)}. ...")
raise ValueError(f"Duplicate scenario labels detected: {duplicate_labels}. ...")
```

Follow the same pattern for `compare_portfolios()` — use `ValueError` for input validation, consistent with `compare_scenarios()`.

### Scope Boundaries

**IN SCOPE:**
- `compare_portfolios()` convenience function
- `PortfolioComparisonInput`, `PortfolioComparisonConfig`, `PortfolioComparisonResult`, `CrossComparisonMetric` types
- Cross-comparison aggregate metrics (fiscal: revenue/cost/balance, welfare: net_change/winners/losers)
- Notebook demo with 3 portfolios
- Tests for all new functionality

**OUT OF SCOPE (deferred to future stories):**
- GUI portfolio comparison dashboard — EPIC-17
- Geographic indicator comparison in portfolios — can be added later (the function supports `indicator_types` extension)
- Custom formula indicators in cross-comparison — EPIC-4.6 already exists, can be composed manually
- Portfolio-specific indicator types (e.g., "portfolio diversity score") — not in FR45
- Automated portfolio optimization ("find the best portfolio parameters") — not in scope

### Project Structure Notes

**New files:**
```
src/reformlab/indicators/portfolio_comparison.py   ← Main implementation
tests/indicators/test_portfolio_comparison.py      ← All tests
notebooks/demo/epic12_portfolio_comparison.ipynb    ← Notebook demo
```

**Modified files:**
```
src/reformlab/indicators/__init__.py               ← Add exports
tests/indicators/conftest.py                       ← Add portfolio panel fixtures
```

**Files NOT to modify:**
```
src/reformlab/indicators/comparison.py              ← No changes (reuse as-is)
src/reformlab/indicators/distributional.py          ← No changes
src/reformlab/indicators/fiscal.py                  ← No changes
src/reformlab/indicators/welfare.py                 ← No changes
src/reformlab/templates/portfolios/                 ← No changes
src/reformlab/orchestrator/portfolio_step.py        ← No changes
src/reformlab/interfaces/api.py                     ← No changes
```

### Code Conventions to Follow

- `from __future__ import annotations` at top of every file
- `if TYPE_CHECKING:` guards for type-only imports
- Frozen dataclasses for all new types (`PortfolioComparisonInput`, etc.) with `@dataclass(frozen=True)`
- `field(default_factory=dict)` for mutable default arguments
- `ValueError` for input validation (matching `compare_scenarios()` pattern)
- `logging.getLogger(__name__)` for logger
- Section separators `# ====...====` for major sections
- Module-level docstring referencing Story 12.5 and FR45
- `tuple[...]` for immutable sequences in return types
- `dict[str, Any]` for metadata bags

### Test Patterns to Follow

**From existing indicator tests** [Source: tests/indicators/]:
- Build PyArrow tables inline with `pa.table({...})`
- Use `PanelOutput(table=table, metadata={...})` directly
- Assert with plain `assert` — no custom helpers
- Test error cases with `pytest.raises(ValueError, match=...)`
- Class-based test grouping: `TestComparePortfoliosBasic`, `TestCrossComparisonMetrics`, etc.
- Use `tmp_path` for file export tests

**From comparison test patterns** [Source: tests/indicators/test_comparison.py]:
- Create indicators first, wrap as `ScenarioInput`, then compare
- Check `result.table.column_names` for expected columns
- Check `result.metadata` dict for expected keys
- Verify warnings list for edge cases

### Performance Considerations

Portfolio comparison is O(N × I) where N = number of portfolios and I = number of indicator types. For the expected use case (3-5 portfolios, 2-3 indicator types), this is negligible. Each `compare_scenarios()` call processes the already-computed indicator tables, which are small (deciles × years × metrics ≈ hundreds of rows).

Cross-comparison metrics iterate over indicator instances (O(N × G × Y) where G = groups, Y = years). For typical scenarios (10 deciles, 10 years, 5 portfolios) this is ~500 iterations — negligible.

### References

- [Source: docs/epics.md#BKL-1205] — Story acceptance criteria
- [Source: docs/prd.md#FR45] — "Analyst can compare results across different policy portfolios side-by-side"
- [Source: src/reformlab/indicators/comparison.py] — Existing comparison module (557 lines)
- [Source: src/reformlab/indicators/comparison.py:406-557] — `compare_scenarios()` function
- [Source: src/reformlab/indicators/comparison.py:33-64] — `ScenarioInput`, `ComparisonConfig` types
- [Source: src/reformlab/indicators/comparison.py:67-120] — `ComparisonResult` with export methods
- [Source: src/reformlab/indicators/types.py] — `IndicatorResult`, `FiscalIndicators`, `WelfareIndicators`, `DecileIndicators`
- [Source: src/reformlab/indicators/__init__.py] — Current module exports
- [Source: src/reformlab/indicators/distributional.py] — `compute_distributional_indicators()`
- [Source: src/reformlab/indicators/fiscal.py] — `compute_fiscal_indicators()`
- [Source: src/reformlab/indicators/welfare.py] — `compute_welfare_indicators()`
- [Source: src/reformlab/orchestrator/portfolio_step.py] — `PortfolioComputationStep` (Story 12.3)
- [Source: src/reformlab/templates/portfolios/portfolio.py] — `PolicyPortfolio`, `PolicyConfig`
- [Source: src/reformlab/interfaces/api.py:97-206] — `SimulationResult` with `.indicators()` method
- [Source: src/reformlab/interfaces/api.py:299-] — `SimulationResult.plot_yearly()`, `plot_comparison()`
- [Source: notebooks/advanced.ipynb] — Advanced notebook patterns (47 cells, sections 1-6)
- [Source: tests/indicators/conftest.py] — Existing indicator test fixtures (panel construction patterns)
- [Source: docs/project-context.md#Architecture] — Frozen dataclasses, PyArrow-first, deterministic execution
- [Source: docs/project-context.md#Testing] — Mirror source structure, class-based grouping, direct assertions

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

### Completion Notes List

### Change Log

### File List


]]></file>
<file id="1d910d88" path="[Validator A]" label="VALIDATION OUTPUT"><![CDATA[

# 🎯 Story Context Validation Report

**Story:** 12-5-implement-multi-portfolio-comparison-and-notebook-demo - implement-multi-portfolio-comparison-and-notebook-demo  
**Story File:** _bmad-output/implementation-artifacts/12-5-implement-multi-portfolio-comparison-and-notebook-demo.md  
**Validated:** 2026-03-06  
**Validator:** Quality Competition Engine

---

## Executive Summary

### Issues Overview

| Category | Found | Applied |
|----------|-------|---------|
| 🚨 Critical Issues | 5 | 0 |
| ⚡ Enhancements | 6 | 0 |
| ✨ Optimizations | 4 | 0 |
| 🤖 LLM Optimizations | 4 | 0 |

**Overall Assessment:** REJECT. Story is not implementation-ready due to multiple contract conflicts, untestable CI requirements, and blocking ambiguity around welfare comparison behavior.

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🔴 CRITICAL | `cross_metrics` contract conflict (AC6 says dict, Task 1.5 defines tuple) | AC6 vs Task 1.5 | +3 |
| 🔴 CRITICAL | Welfare comparison flow can violate `compare_scenarios()` minimum-input rules | Task 2.3 + Task 2.4 + existing API behavior | +3 |
| 🔴 CRITICAL | Notebook “runs in CI” is required but no CI execution mechanism is specified | AC4 + Task 5 | +3 |
| 🔴 CRITICAL | Indicator config contract is inconsistent (`dict` kwargs vs typed config objects in tests) | Task 1.3 vs Task 6.4 | +3 |
| 🔴 CRITICAL | Hard dependency on Story 12.4 (still ready-for-dev) blocks independence | Dependencies + Story 12.4 status | +3 |
| 🟠 IMPORTANT | Tie-breaking/ranking semantics are undefined for equal metric values | AC2 + Task 3.4 | +1 |
| 🟠 IMPORTANT | Empty-panel warning contract is vague (message format, provenance, merge behavior) | AC5 + Task 2.7 | +1 |
| 🟠 IMPORTANT | Baseline semantics are ambiguous when welfare is enabled | Task 1.3 + Task 2.3 | +1 |
| 🟠 IMPORTANT | Frozen dataclass uses mutable containers (`dict`, `list`) without immutability guarantees | Task 1.5 | +1 |
| 🟠 IMPORTANT | Notebook portfolio examples are internally inconsistent (“Carbon Tax Only” but 2 policies) | Task 5.4 | +1 |
| 🟠 IMPORTANT | Runtime/test scope is oversized for one story (core API + notebook + CI + full suite) | Tasks 1-7 | +1 |
| 🟡 MINOR | Repeated constraints increase token load and hide critical requirements | Dev Notes verbosity | +0.3 |
| 🟡 MINOR | Indicator type control duplicates (`indicator_types` + `include_welfare`) | Task 1.3 | +0.3 |
| 🟢 CLEAN PASS | Clear user/business value is well stated | INVEST Valuable | -0.5 |

### Evidence Score: 19.1

| Score | Verdict |
|-------|---------|
| **19.1** | **REJECT** |

---

## 🎯 Ruthless Story Validation 12.5

### INVEST Criteria Assessment

| Criterion | Status | Severity | Details |
|-----------|--------|----------|---------|
| **I**ndependent | FAIL | 8/10 | Explicit dependency on unfinished Story 12.4 and implicit CI infra dependency make this non-independent. |
| **N**egotiable | PARTIAL | 6/10 | Highly prescriptive implementation details constrain design choices beyond outcomes. |
| **V**aluable | PASS | 1/10 | Business value is clear and aligned with portfolio decision-making goals. |
| **E**stimable | FAIL | 8/10 | Conflicting contracts and missing CI/test execution definition prevent reliable estimation. |
| **S**mall | FAIL | 9/10 | Scope combines new indicator API, aggregation logic, exports, notebook authoring, CI validation, and broad tests. |
| **T**estable | FAIL | 8/10 | Several ACs are not objectively testable as written (notebook CI, warning semantics, ranking ties). |

### INVEST Violations

- **[8/10] Independent:** Requires Story 12.4 readiness and CI notebook execution infrastructure not defined here.
- **[6/10] Negotiable:** Task list hardcodes many implementation choices (data structures, internals) rather than behavior.
- **[8/10] Estimable:** Conflicting type/API contracts create unknown implementation churn.
- **[9/10] Small:** Story is oversized for a single sprint unit.
- **[8/10] Testable:** Key outcomes lack deterministic pass/fail criteria.

### Acceptance Criteria Issues

- **Conflict:** Cross-metric output type mismatch.
  - *Quote:* “cross-comparison metrics are available as a dict for programmatic access.”
  - *Recommendation:* Standardize on one contract (`tuple[CrossComparisonMetric]` or `dict[str, CrossComparisonMetric]`) and reflect it in AC, tasks, and tests.

- **Ambiguity:** Welfare comparison path for 2 portfolios is undefined.
  - *Quote:* “skip the baseline portfolio itself.”
  - *Recommendation:* Define behavior when welfare leaves fewer than 2 scenarios for `compare_scenarios()`.

- **Untestable AC:** Notebook CI completion lacks execution definition.
  - *Quote:* “The notebook completes without errors.”
  - *Recommendation:* Add explicit CI runner requirement (e.g., notebook execution job + timeout + artifacts).

- **Ambiguity:** Ranking behavior for metric ties is unspecified.
  - *Quote:* “ranks portfolios from best to worst.”
  - *Recommendation:* Define deterministic tie-break rule (e.g., stable by input order or lexical label).

- **Inconsistency:** Config contract conflicts with tests.
  - *Quote:* `fiscal_kwargs: dict[str, Any]` vs test using `FiscalConfig(...)`.
  - *Recommendation:* Use typed config fields consistently and remove kwargs ambiguity.

- **Ambiguity:** Warning aggregation behavior is vague.
  - *Quote:* “warnings are collected (not exceptions).”
  - *Recommendation:* Define warning schema, source tagging, and behavior when one indicator computation fails.

- **Internal contradiction:** Portfolio A labeled “Carbon Tax Only” but includes two policies.
  - *Quote:* “Carbon Tax Only — ... (2-policy portfolio: carbon tax + minimal subsidy)”
  - *Recommendation:* Rename or make true single-policy example.

### Hidden Risks and Dependencies

- **Sequential dependency:** Story 12.4 is required but still `ready-for-dev`.
  - *Impact:* Implementation can stall or require temporary bypasses.
  - *Mitigation:* Gate 12.5 start on 12.4 completion or explicitly remove dependency if unnecessary.

- **CI infrastructure dependency:** No defined notebook execution pipeline.
  - *Impact:* AC4 cannot be validated objectively.
  - *Mitigation:* Add explicit CI job specification and pass criteria.

- **API contract dependency:** Existing `compare_scenarios()` constraints may invalidate welfare flow.
  - *Impact:* Runtime exceptions or brittle special-casing.
  - *Mitigation:* Define adapter/wrapper behavior for N-1 welfare scenarios.

- **Unresolved upstream risk:** Story 12.3 has open review follow-up on `PolicyConfig.__post_init__`.
  - *Impact:* Portfolio construction may fail unexpectedly in demo or tests.
  - *Mitigation:* Resolve upstream action item before 12.5 integration.

- **Visualization dependency:** Notebook chart stack is implied but not concretely constrained.
  - *Impact:* Environment drift and CI failures.
  - *Mitigation:* Lock plotting/tooling requirements and import strategy.

### Estimation Reality-Check

**Assessment:** underestimated

Current scope spans core comparison API, metric ranking semantics, export behavior, notebook pedagogy, and CI execution guarantees. Given contract conflicts and undefined edge behavior, this is closer to 2 stories (core feature + notebook/CI hardening) than one.

### Technical Alignment

**Status:** PARTIAL / CONFLICTED

- **Error strategy conflict:** Story mandates `ValueError` broadly while project context requires subsystem-specific exceptions for domain errors.
  - *Architecture Reference:* project-context “Subsystem-specific exceptions”
  - *Recommendation:* Define indicator-specific exception or explicitly document exception policy override for this subsystem.

- **Immutability mismatch:** Frozen dataclass fields use mutable containers (`dict`, `list`).
  - *Architecture Reference:* project-context “All domain types are frozen”
  - *Recommendation:* Use immutable containers (`tuple`, mapping proxies) or document intentional mutability.

- **Typed config mismatch:** Story alternates between raw kwargs dicts and typed config objects.
  - *Architecture Reference:* architecture + existing indicator APIs
  - *Recommendation:* Standardize on typed config interfaces.

- **Boundary clarity gap:** CI notebook execution requirement is not reflected in workflow/dev rules section.
  - *Architecture Reference:* workflow/testing rules
  - *Recommendation:* Add explicit CI/test integration task.

### Evidence Score: 19.1 → REJECT

---

## 🚨 Critical Issues (Must Fix)

These are essential requirements, security concerns, or blocking issues that could cause implementation disasters.

### 1. Cross-Metrics Output Contract Conflict

**Impact:** Developer can implement incompatible APIs while still “passing” partial tests.  
**Source:** AC6, Task 1.5

**Problem:** AC6 requires cross-metrics “as a dict,” but Task 1.5 defines `cross_metrics` as tuple dataclass objects.

**Recommended Fix:** Choose one canonical contract and align ACs, dataclasses, and tests to it.

### 2. Welfare Comparison Can Break Existing Comparison API

**Impact:** Runtime failures in valid user scenarios (especially small N).  
**Source:** Task 2.3, Task 2.4, existing `compare_scenarios()` constraints

**Problem:** Skipping baseline for welfare can leave fewer than 2 scenarios, violating pairwise/N-way comparison assumptions.

**Recommended Fix:** Define explicit welfare flow for 2-portfolio input and baseline handling; add guardrails in AC and tests.

### 3. AC4 Is Not Verifiable As Written

**Impact:** “Notebook runs in CI” may be claimed without actual CI execution.  
**Source:** AC4 + Task 5

**Problem:** No task defines CI runner wiring, notebook executor, timeout, or pass/fail conditions.

**Recommended Fix:** Add concrete CI task(s): execution command, environment, timeout, and artifact checks.

### 4. Indicator Config Interface Is Contradictory

**Impact:** Incorrect function signatures and failing tests/typing.  
**Source:** Task 1.3 vs Task 6.4

**Problem:** Config fields are declared as `dict[str, Any]`, but tests specify typed config objects (`FiscalConfig` etc.).

**Recommended Fix:** Standardize config model per indicator function contracts and remove mixed paradigms.

### 5. Story Is Blocked by Incomplete Dependency

**Impact:** Non-independent story with high integration risk.  
**Source:** Dependencies + Story 12.4 status

**Problem:** Portfolio versioning story is not complete; 12.5 assumes mature multi-portfolio inputs and retrieval flows.

**Recommended Fix:** Gate 12.5 start on 12.4 completion criteria, or narrow 12.5 scope to panel-input-only comparison independent of registry.

---

## ⚡ Enhancement Opportunities (Should Add)

### 1. Define Deterministic Tie-Breaking
**Benefit:** Prevent nondeterministic ranking outputs across runs.  
**Source:** AC2, Task 3.4  
**Current Gap:** No tie policy for equal metric values.  
**Suggested Addition:** State tie-break rule (input order or lexical label).

### 2. Specify Warning Contract
**Benefit:** Makes AC5 testable and prevents ad-hoc warning formats.  
**Source:** AC5, Task 2.7  
**Current Gap:** “warnings are collected” is underspecified.  
**Suggested Addition:** Define warning schema and aggregation policy.

### 3. Clarify Indicator Selection Semantics
**Benefit:** Eliminates dual control confusion (`indicator_types` and `include_welfare`).  
**Source:** Task 1.3  
**Current Gap:** Two partially overlapping knobs for indicator execution.  
**Suggested Addition:** Single source of truth for selected indicator types.

### 4. Add Schema/Population Compatibility Guard
**Benefit:** Prevents invalid cross-portfolio comparisons.  
**Source:** AC1 context  
**Current Gap:** No explicit check for year/population comparability before comparison.  
**Suggested Addition:** Add validation criteria and errors/warnings for incompatible panels.

### 5. Split Notebook Demo from Core API Delivery
**Benefit:** Reduces risk and improves sprint reliability.  
**Source:** Tasks 1-7  
**Current Gap:** Feature and educational artifact are tightly coupled.  
**Suggested Addition:** Move notebook+CI to follow-up story or explicit sub-story.

### 6. Resolve Upstream 12.3 Follow-Up Before Demo
**Benefit:** Prevents demo/runtime failures on portfolio config validation path.  
**Source:** Story 12.3 review follow-up  
**Current Gap:** Open action item may surface during notebook execution.  
**Suggested Addition:** Add explicit precondition checklist in dependencies.

---

## ✨ Optimizations (Nice to Have)

### 1. Reuse `compare_scenarios()` Validation Directly
**Value:** Lower code duplication and fewer drift bugs.  
**Suggestion:** Call existing validators once and map portfolio inputs to `ScenarioInput` early.

### 2. Consolidate Cross-Metric Extraction Helpers
**Value:** Cleaner implementation and easier test isolation.  
**Suggestion:** Separate fiscal and welfare aggregation helpers with shared ranking utility.

### 3. Reduce Full-Suite Runs in Story Definition
**Value:** Faster developer loop and lower CI load.  
**Suggestion:** Require targeted tests + one smoke suite in-story; full suite in merge gate.

### 4. Add Notebook Runtime Budget
**Value:** Prevents flaky CI due to long-running demos.  
**Suggestion:** Add max runtime expectation and dataset size constraints.

---

## 🤖 LLM Optimization Improvements

### 1. Remove Contract Duplication
**Issue:** Ambiguity through repeated and conflicting requirements  
**Token Impact:** High

**Current:**
```text
Cross metrics are available as a dict... (AC6)
cross_metrics: tuple[CrossComparisonMetric, ...] (Task 1.5)
```

**Optimized:**
```text
Cross metrics contract: `dict[str, CrossComparisonMetric]` (canonical).
All sections (AC, tasks, tests) must use this shape.
```

**Rationale:** Single canonical contract reduces implementation branching.

### 2. Collapse Repeated API Explanations
**Issue:** Context overload  
**Token Impact:** Medium

**Current:**
```text
`compare_scenarios()` behavior is described repeatedly across Dev Notes and references.
```

**Optimized:**
```text
Reference once: “`compare_portfolios()` wraps `compare_scenarios()`; do not reimplement schema alignment.”
```

**Rationale:** Keeps core instruction visible and concise.

### 3. Replace Mixed Config Wording with Typed Contract
**Issue:** Ambiguity  
**Token Impact:** Medium

**Current:**
```text
distributional_kwargs: dict[str, Any]
fiscal_kwargs: dict[str, Any]
... tests pass FiscalConfig(...)
```

**Optimized:**
```text
Use typed config fields:
distributional_config: DistributionalConfig | None
fiscal_config: FiscalConfig | None
welfare_config: WelfareConfig | None
```

**Rationale:** Prevents signature confusion and mypy churn.

### 4. Split Notebook Requirements into Verifiable Checklist
**Issue:** Untestable prose requirement  
**Token Impact:** Medium

**Current:**
```text
Notebook demo runs in CI and demonstrates sections a-e.
```

**Optimized:**
```text
CI must execute notebook with zero errors, under X minutes, and validate output artifacts A/B/C.
```

**Rationale:** Converts narrative into deterministic acceptance checks.

---

## 📝 Changes Applied

No changes were applied to the story file. This report serves as documentation only.

---

## 🏆 Competition Results

### Quality Metrics

| Metric | Score |
|--------|-------|
| Requirements Coverage | 68% |
| Architecture Alignment | 62% |
| Previous Story Integration | 57% |
| LLM Optimization Score | 55% |
| **Overall Quality Score** | **61%** |

### Disaster Prevention Assessment

- **Reinvention Prevention:** At risk. Existing comparison engine reuse is stated but not contractually enforced.
- **Technical Specification:** High risk. Core type/contracts conflict in multiple sections.
- **File Structure:** Moderate risk. Locations are mostly clear, but CI integration path is missing.
- **Regression Safety:** High risk. Welfare path can break existing comparison assumptions.
- **Implementation Quality:** High risk. Story allows divergent interpretations and non-verifiable completion claims.

### Competition Outcome

🏆 **Validator identified 19 improvements** that materially improve implementation safety and story clarity.

---

**Report Generated:** 2026-03-06  
**Validation Engine:** BMAD Method Quality Competition v1.0

]]></file>
<file id="557aedd2" path="[Validator B]" label="VALIDATION OUTPUT"><![CDATA[

# 🎯 Story Context Validation Report

**Story:** 12-5-implement-multi-portfolio-comparison-and-notebook-demo
**Story File:** _bmad-output/implementation-artifacts/12-5-implement-multi-portfolio-comparison-and-notebook-demo.md
**Validated:** 2026-03-06
**Validator:** Quality Competition Engine

---

## Executive Summary

### Issues Overview

| Category | Found | Applied |
|----------|-------|---------|
| 🚨 Critical Issues | 0 | 0 |
| ⚡ Enhancements | 2 | 0 |
| ✨ Optimizations | 1 | 0 |
| 🤖 LLM Optimizations | 0 | 0 |

**Overall Assessment:** PASS - The story is well-defined, aligns with architectural principles, and offers significant value. Minor enhancements for clarity and completeness are suggested.

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🟠 IMPORTANT | Enhancement: Clarify "portfolio labels as column names" in AC1 | AC1 | +1 |
| 🟠 IMPORTANT | Enhancement: Clarify fiscal metrics in AC2 | AC2 | +1 |
| 🟡 MINOR | Optimization: Ensure consistent `sort_keys` for `yaml.dump` in `_compute_cross_comparison_metrics` | Task 3.4 | +0.3 |
| 🟢 CLEAN PASS | INVEST Criteria Assessment | INVEST Validation | -0.5 |
| 🟢 CLEAN PASS | Acceptance Criteria Deep Analysis | AC Analysis | -0.5 |
| 🟢 CLEAN PASS | Hidden Dependencies Discovery | Dependency Analysis | -0.5 |
| 🟢 CLEAN PASS | Estimation Reality-Check | Estimation Analysis | -0.5 |
| 🟢 CLEAN PASS | Technical Alignment Verification | Technical Alignment | -0.5 |
| 🟢 CLEAN PASS | Reinvention Prevention Gaps | Disaster Prevention | -0.5 |
| 🟢 CLEAN PASS | Technical Specification Disasters | Disaster Prevention | -0.5 |
| 🟢 CLEAN PASS | File Structure Disasters | Disaster Prevention | -0.5 |
| 🟢 CLEAN PASS | Regression Disasters | Disaster Prevention | -0.5 |
| 🟢 CLEAN PASS | Implementation Disasters | Disaster Prevention | -0.5 |

### Evidence Score: 0.3

| Score | Verdict |
|-------|---------|
| **0.3** | **PASS** |

---

## 🎯 Ruthless Story Validation 12.5

### INVEST Criteria Assessment

| Criterion | Status | Severity | Details |
|-----------|--------|----------|---------|
| **I**ndependent | ✅ | 0/10 | Story clearly lists explicit dependencies on previous stories (12.1-12.4) and avoids new hidden dependencies. The use of PanelOutput as input also promotes independence. |
| **N**egotiable | ✅ | 0/10 | The story specifies desired outcomes and high-level approaches while allowing flexibility in implementation details. The notebook demo outline is detailed but still negotiable on exact content. |
| **V**aluable | ✅ | 0/10 | Clearly articulated value for policy analysts to compare portfolios and achieve objectives. Directly contributes to the project's strategic goals. |
| **E**stimable | ✅ | 0/10 | Detailed acceptance criteria, granular tasks, clear scope boundaries, and explicit references to existing patterns make this story highly estimable. |
| **S**mall | ✅ | 0/10 | The story is well-scoped, focusing on comparison and a demo. It builds incrementally on previous work and explicitly defers larger-scale features to future stories, making it suitable for a single sprint. |
| **T**estable | ✅ | 0/10 | All acceptance criteria are specific, measurable, and have corresponding test tasks. Edge cases and error handling are explicitly covered in AC5 and Task 5. |

### INVEST Violations

✅ No significant INVEST violations detected.

### Acceptance Criteria Issues

✅ Acceptance criteria are well-defined and testable.

### Hidden Risks and Dependencies

✅ No hidden dependencies or blockers identified.

### Estimation Reality-Check

**Assessment:** Realistic

The story provides a detailed task breakdown, explicitly identifies dependencies, and separates out-of-scope items. The complexity of integrating with existing comparison logic and building a comprehensive notebook demo is acknowledged through the task list. The Dev Notes also clarify the approach, making the estimate sound.

### Technical Alignment

**Status:** Aligned

✅ Story aligns with architecture.md patterns.

---

## 🚨 Critical Issues (Must Fix)

✅ No critical issues found - the original story covered essential requirements.

---

## ⚡ Enhancement Opportunities (Should Add)

### 1. Clarify column naming for side-by-side comparison tables in AC1

**Benefit:** Improved clarity for the developer, ensuring consistency in generated output and avoiding ambiguity. This impacts how the comparison table is ultimately structured and presented to the user.
**Source:** AC1
**Current Gap:** AC1 states "Each comparison table uses portfolio labels as column names." While this generally makes sense for the value columns, it's not explicit for potentially shared metrics (e.g., 'mean_income' per decile across portfolios). Without a clear rule, a developer might duplicate the metric name (e.g., 'mean_income_A', 'mean_income_B') or assume the portfolio label is a top-level header with metrics nested underneath, which is ambiguous for PyArrow tables.
**Suggested Addition:** Update AC1 to specify how shared metric names are handled in the columnar output. For example: "Each comparison table uses portfolio labels as column name *prefixes* for indicator values (e.g., 'PortfolioA_mean_income', 'PortfolioB_mean_income') alongside common keys (e.g., 'decile', 'year')." This aligns with how `_merge_policy_results()` from Story 12.3 handles column name conflicts by prefixing.

### 2. Clarify "fiscal metrics" in AC2

**Benefit:** Explicitly defining which fiscal metrics are used for cross-comparison enhances precision and prevents misinterpretation, ensuring the developer implements the intended comparison logic.
**Source:** AC2
**Current Gap:** AC2 mentions "(a) total fiscal revenue, (b) total fiscal cost, (c) fiscal balance" as cross-comparison aggregate metrics. However, Task 3.2 expands on this to include "max_fiscal_revenue", "min_fiscal_cost", "max_fiscal_balance". It should be explicit in AC2 that these are the *criteria* for ranking. The current wording could be interpreted as just providing the raw numbers.
**Suggested Addition:** Update AC2 to clarify the intent for fiscal metrics. For example: "Each metric ranks portfolios from best to worst based on criteria such as 'maximizing fiscal revenue', 'minimizing fiscal cost', and 'maximizing fiscal balance'..."

---

## ✨ Optimizations (Nice to Have)

### 1. Ensure consistent `sort_keys` for `yaml.dump` calls

**Value:** Ensures deterministic output for any debug or intermediate YAML representations, aligning with project's determinism rule and preventing subtle inconsistencies in different YAML operations.
**Suggestion:** Task 3.4 outlines sorting `all_values` by ranking. If these values are ever serialized to YAML (e.g., for logging or intermediate storage), it's good practice to ensure `yaml.dump` uses `sort_keys=True` for determinism, similar to the pattern in version ID generation for the registry. While not explicitly mentioned for serialization here, ensuring this is noted for any future YAML output from this function would be beneficial for consistency.

---

## 🤖 LLM Optimization Improvements

✅ Story content is well-optimized for LLM processing.

---

## 📝 Changes Applied

No changes were applied to the story file. This report serves as documentation only.

---

## 🏆 Competition Results

### Quality Metrics

| Metric | Score |
|--------|-------|
| Requirements Coverage | 100% |
| Architecture Alignment | 100% |
| Previous Story Integration | 100% |
| LLM Optimization Score | 100% |
| **Overall Quality Score** | **99%** |

### Disaster Prevention Assessment

- **Reinvention Prevention:** ✅ No reinvention risks identified; leverages existing `compare_scenarios()` and indicator functions effectively.
- **Technical Specification:** ✅ Technical specifications are clear and detailed, explicitly defining types, interfaces, and expected behaviors.
- **File Structure:** ✅ New files and modifications adhere to project's file structure conventions.
- **Regression:** ✅ Explicit backward compatibility AC and comprehensive testing tasks minimize regression risks.
- **Implementation:** ✅ Clear ACs, detailed tasks, and comprehensive Dev Notes reduce vagueness and scope creep.

### Competition Outcome

✅ **Original create-story produced high-quality output** with minimal gaps identified.

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
<var name="session_id">35fccde2-18e9-4bae-8db0-c40213a36b79</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_file" file_id="8233c651">embedded in prompt, file id: 8233c651</var>
<var name="story_id">12.5</var>
<var name="story_key">12-5-implement-multi-portfolio-comparison-and-notebook-demo</var>
<var name="story_num">5</var>
<var name="story_title">implement-multi-portfolio-comparison-and-notebook-demo</var>
<var name="template">False</var>
<var name="timestamp">20260306_1449</var>
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