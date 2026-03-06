
# Story 12.5: Implement Multi-Portfolio Comparison and Notebook Demo

Status: done
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
Given a `PortfolioComparisonResult`, when exported, then each per-indicator-type comparison table can be exported to CSV/Parquet independently via the existing `ComparisonResult.export_csv()` / `export_parquet()` methods. The cross-comparison metrics are available as a tuple of `CrossComparisonMetric` objects for programmatic access.

## Tasks / Subtasks

### Task 1: Define portfolio comparison types (AC: 1, 2, 5, 6)

- [ ] 1.1 Create `src/reformlab/indicators/portfolio_comparison.py` with module docstring referencing Story 12.5 and FR45
- [ ] 1.2 Define `PortfolioComparisonInput` frozen dataclass: `label: str`, `panel: PanelOutput`. Validate label is non-empty in `__post_init__`. This takes `PanelOutput` (not `SimulationResult`) to match existing indicator function signatures and enable composition
- [ ] 1.3 Define `PortfolioComparisonConfig` frozen dataclass with fields: `baseline_label: str | None = None` (defaults to first portfolio), `indicator_types: tuple[str, ...] = ("distributional", "fiscal")` (which indicator types to compute), `include_welfare: bool = False` (welfare requires baseline vs reform so opt-in), `include_deltas: bool = True`, `include_pct_deltas: bool = True`, `distributional_config: DistributionalConfig | None = None` (passed to `compute_distributional_indicators`), `fiscal_config: FiscalConfig | None = None` (passed to `compute_fiscal_indicators`), `welfare_config: WelfareConfig | None = None` (passed to `compute_welfare_indicators`)
- [ ] 1.4 Define `CrossComparisonMetric` frozen dataclass: `criterion: str` (e.g., `"max_mean_welfare_net_change"`, `"min_fiscal_cost"`), `best_portfolio: str` (label of the portfolio ranked first), `value: float` (metric value for the best portfolio), `all_values: dict[str, float]` (metric value per portfolio label, ordered by ranking)
- [ ] 1.5 Define `PortfolioComparisonResult` frozen dataclass: `comparisons: dict[str, ComparisonResult]` (keyed by indicator type string, e.g., `{"distributional": ..., "fiscal": ...}`), `cross_metrics: tuple[CrossComparisonMetric, ...]` (aggregate metrics across portfolios), `portfolio_labels: tuple[str, ...]` (ordered labels), `metadata: dict[str, Any]`, `warnings: list[str]`

### Task 2: Implement `compare_portfolios()` function (AC: 1, 3, 5)

- [ ] 2.1 Implement input validation: minimum 2 portfolios, unique labels, non-empty labels, labels don't conflict with reserved column names (same checks as `compare_scenarios()`)
- [ ] 2.2 For each indicator type in `config.indicator_types`, compute indicators for each portfolio by calling the appropriate indicator function (`compute_distributional_indicators(panel, config.distributional_config)`, `compute_fiscal_indicators(panel, config.fiscal_config)`) with the portfolio's `PanelOutput` and the typed config. Collect per-portfolio `IndicatorResult` objects
- [ ] 2.3 For welfare indicators (when `config.include_welfare is True`): use the baseline portfolio's panel as the baseline panel, compute welfare indicators for each non-baseline portfolio via `compute_welfare_indicators(baseline_panel, reform_panel, config.welfare_config)`. Collect per-portfolio `IndicatorResult` objects. Skip the baseline portfolio itself (welfare is baseline vs reform, so baseline vs baseline is meaningless). **Edge case:** when only 2 portfolios are provided with welfare enabled, there is only 1 non-baseline result; in this case, skip calling `compare_scenarios()` for welfare and instead store a single-portfolio welfare `ComparisonResult` directly (wrap the single `IndicatorResult` as a degenerate comparison with no deltas). Require at least 3 portfolios for welfare delta computation; with exactly 2, produce welfare indicators without cross-portfolio deltas and add a warning
- [ ] 2.4 For each indicator type, wrap per-portfolio `IndicatorResult` objects as `ScenarioInput(label=portfolio_label, indicators=indicator_result)` and call `compare_scenarios(scenarios, config=ComparisonConfig(baseline_label=config.baseline_label, include_deltas=config.include_deltas, include_pct_deltas=config.include_pct_deltas))`. Store resulting `ComparisonResult` keyed by indicator type string
- [ ] 2.5 Call `_compute_cross_comparison_metrics()` (Task 3) with the per-portfolio indicator results to produce `CrossComparisonMetric` tuples
- [ ] 2.6 Build metadata dict: `{"portfolio_labels": labels, "baseline_label": resolved_baseline, "indicator_types": list(config.indicator_types), "include_welfare": config.include_welfare, "config": ...}`
- [ ] 2.7 Collect all warnings from each `ComparisonResult` into a unified warnings list, prefixed with indicator type (e.g., `"[distributional] Non-overlapping keys..."`)
- [ ] 2.8 Return `PortfolioComparisonResult` with all collected results

### Task 3: Implement cross-comparison metrics computation (AC: 2)

- [ ] 3.1 Create `_compute_cross_comparison_metrics()` internal function accepting: `fiscal_indicators: dict[str, IndicatorResult] | None` (keyed by portfolio label), `welfare_indicators: dict[str, IndicatorResult] | None` (keyed by portfolio label), `portfolio_labels: list[str]`
- [ ] 3.2 For fiscal metrics: extract per-portfolio aggregate values from `IndicatorResult.indicators` list. For each portfolio, compute: `total_revenue` (sum of `FiscalIndicators.revenue` across years), `total_cost` (sum of `FiscalIndicators.cost` across years), `fiscal_balance` (sum of `FiscalIndicators.balance` across years). Create `CrossComparisonMetric` for each: `"max_fiscal_revenue"` (highest revenue first), `"min_fiscal_cost"` (lowest cost first), `"max_fiscal_balance"` (highest balance first)
- [ ] 3.3 For welfare metrics: extract per-portfolio aggregate values from `IndicatorResult.indicators` list. For each portfolio, compute: `mean_net_change` (mean of `WelfareIndicators.net_change` across all groups and years), `total_winners` (sum of `WelfareIndicators.winner_count` across groups), `total_losers` (sum of `WelfareIndicators.loser_count` across groups). Create `CrossComparisonMetric` for each: `"max_mean_welfare_net_change"` (highest net change first), `"max_total_winners"` (most winners first), `"min_total_losers"` (fewest losers first)
- [ ] 3.4 Sort each metric's `all_values` dict by ranking order (best first). For "max_*" criteria, sort descending; for "min_*" criteria, sort ascending. **Tie-breaking:** when two portfolios have equal metric values, maintain input order (stable sort) for deterministic ranking
- [ ] 3.5 Return tuple of all `CrossComparisonMetric` objects. If fiscal_indicators is None, skip fiscal metrics. If welfare_indicators is None, skip welfare metrics. If both are None, return empty tuple

### Task 4: Update module exports (AC: all)

- [ ] 4.1 Add imports and exports to `src/reformlab/indicators/__init__.py`: `PortfolioComparisonInput`, `PortfolioComparisonConfig`, `PortfolioComparisonResult`, `CrossComparisonMetric`, `compare_portfolios`
- [ ] 4.2 Update module docstring in `__init__.py` to mention portfolio comparison (add `Story 12.5` reference)

### Task 5: Build notebook demo (AC: 4)

- [ ] 5.1 Create `notebooks/demo/epic12_portfolio_comparison.ipynb` following the pattern of `notebooks/advanced.ipynb`
- [ ] 5.2 **Section 0 — Introduction** (markdown): Explain what portfolio comparison is, prerequisites (quickstart + advanced notebooks), and what the reader will learn
- [ ] 5.3 **Section 1 — Imports and Setup** (code): Import ReformLab API, portfolio types, indicator comparison types, visualization utilities. Resolve population path relative to notebook location. Load the demo population CSV
- [ ] 5.4 **Section 2 — Create Three Portfolios** (code + markdown per portfolio):
  - Portfolio A: "Carbon Tax Light" — carbon tax at €50/tCO2 with minimal subsidy (2 policies)
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
- [ ] 6.4 **TestComparePortfoliosFiscal** (AC1): Compare 3 portfolios with fiscal indicators (config with `fiscal_config=FiscalConfig(revenue_fields=["carbon_tax"], cost_fields=["subsidy_amount"])`). Assert `comparisons` dict has `"fiscal"` key. Assert comparison table has expected columns
- [ ] 6.5 **TestComparePortfoliosWelfare** (AC1, AC2): Compare 3 portfolios with `include_welfare=True`. Assert `comparisons` dict has `"welfare"` key. Assert welfare comparison uses baseline panel vs each reform panel. Assert baseline label is not in welfare comparison (baseline vs itself is skipped). Also test the 2-portfolio welfare edge case: with exactly 2 portfolios and welfare enabled, assert a warning is emitted and welfare indicators are present without cross-portfolio deltas
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
- `field(default_factory=dict)` for mutable default arguments (metadata bags only; use typed config objects for indicator configs)
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
