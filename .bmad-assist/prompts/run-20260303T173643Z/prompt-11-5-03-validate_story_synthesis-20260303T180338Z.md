<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 11 -->
<!-- Story: 5 -->
<!-- Phase: validate-story-synthesis -->
<!-- Timestamp: 20260303T180338Z -->
<compiled-workflow>
<mission><![CDATA[

Master Synthesis: Story 11.5

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
<file id="b5c6fe32" path="_bmad-output/project-context.md" label="PROJECT CONTEXT"><![CDATA[

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
<file id="bca11243" path="_bmad-output/implementation-artifacts/11-5-implement-ipf-and-conditional-sampling-merge-methods.md" label="STORY FILE"><![CDATA[



# Story 11.5: Implement IPF and conditional sampling merge methods

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform developer building the French household population pipeline,
I want IPF (Iterative Proportional Fitting) and conditional sampling merge methods implementing the existing `MergeMethod` protocol,
so that the population pipeline can produce merged populations that respect known marginal distributions (IPF) or leverage shared stratification variables (conditional sampling), enabling more realistic synthetic populations than uniform random matching alone.

## Acceptance Criteria

1. Given two tables and a set of known marginal constraints, when IPF is applied, then the merged population matches the target marginals within documented tolerances.
2. Given IPF output, when the assumption record is inspected, then it lists all marginal constraints used and the convergence status.
3. Given two tables with a conditioning variable (e.g., income bracket), when conditional sampling is applied, then matches are drawn within strata defined by the conditioning variable.
4. Given conditional sampling output, when the assumption record is inspected, then it states the conditioning variable and explains the conditional independence assumption.
5. Given both methods, when docstrings are read, then each includes a plain-language explanation suitable for a policy analyst (not just a statistician).

## Tasks / Subtasks

- [ ] Task 1: Define IPF supporting types in `base.py` (AC: #1, #2)
  - [ ] 1.1 Add `IPFConstraint` frozen dataclass to `src/reformlab/population/methods/base.py` with fields: `dimension: str` (column name in table_a to constrain), `targets: dict[str, float]` (category value -> target count/weight). Validate in `__post_init__` that `dimension` is a non-empty string and `targets` is non-empty with all values >= 0. Deep-copy `targets` dict via `object.__setattr__`.
  - [ ] 1.2 Add `IPFResult` frozen dataclass to `base.py` with fields: `weights: tuple[float, ...]` (per-row IPF weights), `iterations: int` (iterations until convergence), `converged: bool`, `max_deviation: float` (maximum absolute deviation at termination). This captures convergence diagnostics for the assumption record.

- [ ] Task 2: Add `MergeConvergenceError` to error hierarchy (AC: #1)
  - [ ] 2.1 Add `MergeConvergenceError(MergeError)` to `src/reformlab/population/methods/errors.py` — raised when IPF fails to converge within `max_iterations`. Docstring: "Raised when an iterative merge method fails to converge within the configured iteration limit."

- [ ] Task 3: Implement `IPFMergeMethod` — `ipf.py` (AC: #1, #2, #5)
  - [ ] 3.1 Create `src/reformlab/population/methods/ipf.py` with module docstring referencing Story 11.5, FR38, FR39 — include pedagogical docstring explaining IPF in plain language:
    - What IPF does: adjusts row weights so that the merged population's marginal distributions match known targets (e.g., census totals by region, income distribution by bracket)
    - The assumption: the joint distribution between unconstrained variables follows the pattern in the seed data (table_a), adjusted only to match the specified marginals. This is a "minimum information" / maximum entropy approach
    - When appropriate: when you have reliable marginal distributions from census or administrative data that the merged population must respect
    - When problematic: when the seed data has structural zeros (categories with no observations) that should have non-zero representation, or when marginal targets are mutually inconsistent (different grand totals)
  - [ ] 3.2 Implement `IPFMergeMethod` class with constructor:
    ```python
    def __init__(
        self,
        constraints: tuple[IPFConstraint, ...],
        max_iterations: int = 100,
        tolerance: float = 1e-6,
    ) -> None:
    ```
    Validate: `constraints` must be non-empty tuple, `max_iterations >= 1`, `tolerance > 0`. Store as instance attributes. No frozen dataclass for the method itself (it's a service object, not a value object).
  - [ ] 3.3 Implement `name` property returning `"ipf"`
  - [ ] 3.4 Implement private `_run_ipf(self, table_a: pa.Table, config: MergeConfig) -> IPFResult` with this algorithm:
    1. Initialize weights: `[1.0] * table_a.num_rows`
    2. Validate constraint dimensions exist as columns in table_a — raise `MergeValidationError` if not
    3. Validate constraint targets: each target category must exist in the column values — log warning for categories not present (they cannot be satisfied), raise `MergeValidationError` if **all** categories in a constraint are missing
    4. IPF iteration loop (up to `max_iterations`):
       a. For each constraint `(dimension, targets)`:
          - Extract column values: `table_a.column(dimension).to_pylist()`
          - Compute current weighted totals per category: `current[cat] = sum(weights[k] for k where col[k] == cat)`
          - Compute adjustment factors: `factor[cat] = target[cat] / current[cat]` (if `current[cat] > 0`, else `factor = 1.0`)
          - Apply factors: `weights[k] *= factor[col[k]]`
       b. Compute max absolute deviation: `max(|current[cat] - target[cat]|)` across all constraints and categories
       c. If `max_deviation < tolerance`: converged = True, break
    5. Return `IPFResult(weights=tuple(weights), iterations=i+1, converged=converged, max_deviation=max_deviation)`
  - [ ] 3.5 Implement private `_integerize_weights(self, weights: tuple[float, ...], target_count: int, rng: random.Random) -> list[int]` with this algorithm:
    1. Normalize weights so they sum to `target_count` (= `table_a.num_rows`, preserving original count)
    2. For each weight: `integer_part = floor(weight)`, `fractional = weight - integer_part`
    3. Deterministic probabilistic rounding: if `rng.random() < fractional`, add 1
    4. Return list of integer weights (each >= 0)
  - [ ] 3.6 Implement `merge(self, table_a, table_b, config)` with this logic:
    1. Validate inputs: both tables must have `num_rows > 0` — raise `MergeValidationError` (same pattern as uniform)
    2. Apply `config.drop_right_columns` to table_b (same pattern as uniform)
    3. Check column name conflicts (same pattern as uniform)
    4. Run IPF: `ipf_result = self._run_ipf(table_a, config)`
    5. If not converged: raise `MergeConvergenceError` with summary="IPF did not converge", reason with iterations and max_deviation, fix suggesting increasing max_iterations or checking marginal consistency
    6. Integerize weights: `int_weights = self._integerize_weights(ipf_result.weights, table_a.num_rows, random.Random(config.seed))`
    7. Expand table_a: for each row `k`, repeat it `int_weights[k]` times. Build expanded row indices: `expanded_indices = [k for k, w in enumerate(int_weights) for _ in range(w)]`
    8. Create expanded table_a: `expanded_a = table_a.take(pa.array(expanded_indices))`
    9. Random matching: use `random.Random(config.seed + 1)` (different seed stream from integerization) to generate `expanded_a.num_rows` random indices into table_b (same pattern as uniform)
    10. Select matched rows: `matched_b = right_table.take(pa.array(b_indices))`
    11. Combine columns: same pattern as uniform (table_a columns first, then table_b columns)
    12. Build `MergeAssumption` with:
        - `method_name="ipf"`
        - `statement="The merged population is reweighted using Iterative Proportional Fitting so that marginal distributions match the specified targets — this assumes the joint distribution between unconstrained variables follows the seed pattern, adjusted only to match target marginals."`
        - `details={"table_a_rows": table_a.num_rows, "table_b_rows": table_b.num_rows, "expanded_rows": expanded_a.num_rows, "seed": config.seed, "constraints": [{"dimension": c.dimension, "targets": dict(c.targets)} for c in self._constraints], "iterations": ipf_result.iterations, "converged": ipf_result.converged, "max_deviation": ipf_result.max_deviation, "tolerance": self._tolerance, "dropped_right_columns": list(config.drop_right_columns)}`
    13. Return `MergeResult(table=merged, assumption=assumption)`
  - [ ] 3.7 Use `logging.getLogger(__name__)` with structured `event=ipf_start`, `event=ipf_iteration`, `event=ipf_converged`/`event=ipf_not_converged`, `event=merge_start`, `event=merge_complete` log entries

- [ ] Task 4: Implement `ConditionalSamplingMethod` — `conditional.py` (AC: #3, #4, #5)
  - [ ] 4.1 Create `src/reformlab/population/methods/conditional.py` with module docstring referencing Story 11.5, FR38, FR39 — include pedagogical docstring explaining conditional sampling in plain language:
    - What it does: groups both tables by shared variable(s) (strata), then randomly matches rows only within the same group. This preserves the correlation between the stratification variable and all other variables
    - The assumption: conditional independence — within each stratum, the unique variables from table_a and table_b are assumed independent. The correlation between them is captured entirely by the stratification variable
    - When appropriate: when both datasets share a variable that is correlated with the unique variables in each dataset (e.g., income bracket correlates with both energy consumption and vehicle ownership)
    - When problematic: when the strata are too coarse (residual correlation within strata is large) or when some strata have very few observations in one table (small sample noise)
  - [ ] 4.2 Implement `ConditionalSamplingMethod` class with constructor:
    ```python
    def __init__(
        self,
        strata_columns: tuple[str, ...],
    ) -> None:
    ```
    Validate: `strata_columns` must be a non-empty tuple of non-empty strings. Store as instance attribute.
  - [ ] 4.3 Implement `name` property returning `"conditional"`
  - [ ] 4.4 Implement `merge(self, table_a, table_b, config)` with this logic:
    1. Validate inputs: both tables must have `num_rows > 0` — raise `MergeValidationError`
    2. Validate strata columns exist in BOTH tables — raise `MergeValidationError` listing missing columns and which table they're missing from
    3. Apply `config.drop_right_columns` to table_b (same pattern as uniform). Note: strata columns in table_b will be dropped from the merged output to avoid duplication (they already exist in table_a). Add strata column names to the effective drop list automatically (unless already in `drop_right_columns`)
    4. Check column name conflicts on remaining columns (same pattern as uniform)
    5. Build stratum keys: for each row in table_a and table_b, compute a stratum key as a tuple of values from `strata_columns`
    6. Group table_a row indices by stratum: `strata_a: dict[tuple, list[int]]`
    7. Group table_b row indices by stratum: `strata_b: dict[tuple, list[int]]`
    8. Validate coverage: for each stratum present in table_a, check it exists in table_b — raise `MergeValidationError` if any table_a stratum has zero table_b donors (list the empty strata in the error message)
    9. Random matching within strata: `rng = random.Random(config.seed)`. For each stratum, for each table_a row index in that stratum: draw a random index from the table_b row indices in the same stratum (`rng.choice(strata_b[key])`)
    10. Collect all matched (a_idx, b_idx) pairs in original table_a row order
    11. Build merged table: table_a rows (in order) + matched table_b rows (strata columns removed from table_b side)
    12. Build `MergeAssumption` with:
        - `method_name="conditional"`
        - `statement="Rows are matched within strata defined by [{strata_column_list}] — this assumes that, within each stratum, the unique variables from each source are independent (conditional independence given the stratification variables)."`
        - `details={"table_a_rows": n, "table_b_rows": m, "seed": config.seed, "strata_columns": list(self._strata_columns), "strata_count": len(unique_strata), "strata_sizes": {str(k): {"table_a": len(v_a), "table_b": len(v_b)} for k, v_a, v_b in strata_info}, "dropped_right_columns": list(effective_drop_columns)}`
    13. Return `MergeResult(table=merged, assumption=assumption)`
  - [ ] 4.5 Use `logging.getLogger(__name__)` with structured log entries: `event=merge_start method=conditional`, `event=strata_built strata_count=...`, `event=merge_complete`

- [ ] Task 5: Update `__init__.py` exports (AC: all)
  - [ ] 5.1 Export from `src/reformlab/population/methods/__init__.py`: add `IPFConstraint`, `IPFResult`, `IPFMergeMethod`, `ConditionalSamplingMethod`, `MergeConvergenceError` — update `__all__` listing
  - [ ] 5.2 Export from `src/reformlab/population/__init__.py`: add same names — update `__all__` listing

- [ ] Task 6: Create test fixtures for IPF and conditional sampling (AC: all)
  - [ ] 6.1 Add to `tests/population/methods/conftest.py`:
    - `region_income_table` — `pa.Table` with columns: `household_id` (int64), `income_bracket` (utf8: "low"/"medium"/"high"), `region_code` (utf8: "84"/"11"/"75") — 10 rows, with known distribution: 3 low, 4 medium, 3 high; 4 region 84, 3 region 11, 3 region 75
    - `energy_vehicle_table` — `pa.Table` with columns: `income_bracket` (utf8), `vehicle_type` (utf8), `energy_kwh` (float64) — 12 rows, covering all 3 income brackets with known distribution
    - `simple_constraints` — `tuple[IPFConstraint, ...]` with one constraint: `IPFConstraint(dimension="income_bracket", targets={"low": 4.0, "medium": 3.0, "high": 3.0})` — shifts distribution from 3/4/3 to 4/3/3
    - `multi_constraints` — `tuple[IPFConstraint, ...]` with two constraints: income_bracket + region_code targets
    - `inconsistent_constraints` — constraints where totals across dimensions don't match (for convergence failure testing)

- [ ] Task 7: Write comprehensive IPF tests (AC: #1, #2, #5)
  - [ ] 7.1 `tests/population/methods/test_ipf.py`:
    - `TestIPFConstraint`: frozen, `__post_init__` validation (empty dimension raises ValueError, empty targets raises ValueError, negative target raises ValueError), targets deep-copied
    - `TestIPFResult`: frozen, holds weights + convergence diagnostics
    - `TestIPFMergeMethodProtocol`: `isinstance(IPFMergeMethod(...), MergeMethod)` passes
    - `TestIPFMergeMethodName`: `name` property returns `"ipf"`
    - `TestIPFMergeMethodConstructorValidation`: empty constraints raises ValueError, max_iterations < 1 raises ValueError, tolerance <= 0 raises ValueError
    - `TestIPFMergeMethodMerge`:
      - Basic merge with single constraint: region_income_table (10 rows) + vehicle_table → merged table with IPF-adjusted row counts, income_bracket distribution matches target within tolerance
      - Merged table has correct columns (table_a + table_b minus dropped)
      - Values from table_b come from actual rows in table_b (row-level coherence)
    - `TestIPFMergeMethodMarginalMatch`:
      - After merge, count rows per income_bracket → matches targets within tolerance (may differ by ±1 due to integerization)
      - Multi-constraint merge: both income_bracket AND region_code distributions match targets
    - `TestIPFMergeMethodConvergence`:
      - Convergent case: assumption.details contains `converged: True`, `iterations` < max_iterations
      - Non-convergent case (inconsistent constraints): raises `MergeConvergenceError`
    - `TestIPFMergeMethodDeterminism`:
      - Same seed → identical merged table
      - Different seed → different row matching (at least one row differs)
    - `TestIPFMergeMethodAssumption`:
      - `assumption.method_name == "ipf"`
      - `assumption.statement` contains "Iterative Proportional Fitting" and "marginal"
      - `assumption.details` contains `constraints`, `iterations`, `converged`, `max_deviation`, `tolerance`, `expanded_rows`
      - `assumption.to_governance_entry()` returns correct structure
    - `TestIPFMergeMethodEmptyTable`:
      - Empty table_a → `MergeValidationError`
      - Empty table_b → `MergeValidationError`
    - `TestIPFMergeMethodColumnConflict`:
      - Overlapping columns → `MergeValidationError`
    - `TestIPFMergeMethodDropRightColumns`:
      - `drop_right_columns` works correctly
    - `TestIPFMergeMethodInvalidConstraintDimension`:
      - Constraint dimension not in table_a → `MergeValidationError`
    - `TestIPFMergeMethodDocstring`:
      - Class docstring non-empty, mentions "marginal" or "reweight"
      - Module docstring mentions "appropriate" and "problematic"

- [ ] Task 8: Write comprehensive conditional sampling tests (AC: #3, #4, #5)
  - [ ] 8.1 `tests/population/methods/test_conditional.py`:
    - `TestConditionalSamplingMethodProtocol`: `isinstance(ConditionalSamplingMethod(...), MergeMethod)` passes
    - `TestConditionalSamplingMethodName`: `name` property returns `"conditional"`
    - `TestConditionalSamplingMethodConstructorValidation`: empty strata_columns raises ValueError, empty string in strata_columns raises ValueError
    - `TestConditionalSamplingMethodMerge`:
      - Basic merge with single stratum column ("income_bracket"): region_income_table + energy_vehicle_table → merged table with same row count as table_a
      - All columns from both tables present (minus duplicated strata columns from table_b)
      - Row count equals table_a.num_rows
    - `TestConditionalSamplingMethodStrataRespected`:
      - For each row in merged table, the strata column value matches between the table_a side and the original table_b donor row — i.e., a "low" income household is matched with a "low" income vehicle/energy record
    - `TestConditionalSamplingMethodDeterminism`:
      - Same seed → identical merged table
      - Different seed → different row matching
    - `TestConditionalSamplingMethodColumnConflict`:
      - Overlapping non-strata columns → `MergeValidationError`
    - `TestConditionalSamplingMethodDropRightColumns`:
      - `drop_right_columns` works correctly
      - Strata columns in table_b are auto-dropped (not duplicated in output)
    - `TestConditionalSamplingMethodEmptyTable`:
      - Empty table_a → `MergeValidationError`
      - Empty table_b → `MergeValidationError`
    - `TestConditionalSamplingMethodMissingStrataColumn`:
      - Strata column not in table_a → `MergeValidationError` mentioning which table and column
      - Strata column not in table_b → `MergeValidationError`
    - `TestConditionalSamplingMethodEmptyStratum`:
      - table_a has stratum value "X" but table_b has no rows with "X" → `MergeValidationError` listing the empty stratum
    - `TestConditionalSamplingMethodAssumption`:
      - `assumption.method_name == "conditional"`
      - `assumption.statement` contains "conditional independence" and strata column names
      - `assumption.details` contains `strata_columns`, `strata_count`, `strata_sizes`, `seed`
      - `assumption.to_governance_entry()` returns correct structure
    - `TestConditionalSamplingMethodMultipleStrataColumns`:
      - Merge with 2 strata columns: matching respects both dimensions simultaneously
    - `TestConditionalSamplingMethodDocstring`:
      - Class docstring non-empty, mentions "conditional independence" or "strata"
      - Module docstring mentions "appropriate" and "problematic"

- [ ] Task 9: Write tests for new error types and base types (AC: #1, #2)
  - [ ] 9.1 Add to `tests/population/methods/test_errors.py`:
    - `TestMergeConvergenceError`: inherits `MergeError`, summary-reason-fix pattern, catchable as `MergeError`
  - [ ] 9.2 Add to `tests/population/methods/test_base.py`:
    - `TestIPFConstraint`: frozen, validation, targets deep-copied
    - `TestIPFResult`: frozen, holds convergence diagnostics

- [ ] Task 10: Run full test suite and lint (AC: all)
  - [ ] 10.1 `uv run pytest tests/population/methods/` — all new tests pass
  - [ ] 10.2 `uv run pytest tests/population/` — no regressions in loader or uniform merge tests
  - [ ] 10.3 `uv run ruff check src/reformlab/population/methods/ tests/population/methods/` — no lint errors
  - [ ] 10.4 `uv run mypy src/reformlab/population/methods/` — no mypy errors (strict mode)

## Dev Notes

### Architecture Context: Methods Library Extension

This story extends the `src/reformlab/population/methods/` subsystem created in Story 11.4. Two new files are added:

```
src/reformlab/population/methods/
├── __init__.py     ← Updated: add new exports
├── base.py         ← Updated: add IPFConstraint, IPFResult
├── errors.py       ← Updated: add MergeConvergenceError
├── uniform.py      ← UNCHANGED (Story 11.4)
├── ipf.py          ← NEW (this story)
└── conditional.py  ← NEW (this story)
```

### Protocol Compliance: Both Methods Follow Existing Pattern

Both `IPFMergeMethod` and `ConditionalSamplingMethod` implement the `MergeMethod` protocol established in Story 11.4 via duck typing (no inheritance). They follow the **exact same patterns** as `UniformMergeMethod`:

1. **`name` property** — returns short identifier (`"ipf"` or `"conditional"`)
2. **`merge(table_a, table_b, config)` signature** — identical to protocol
3. **Same validation order**: empty tables → drop_right_columns → column conflicts → method-specific logic
4. **Same assumption record pattern**: `MergeAssumption(method_name=..., statement=..., details=...)`
5. **Same error hierarchy**: `MergeValidationError` for input issues, `MergeConvergenceError` (new) for IPF non-convergence
6. **Same logging pattern**: `_logger = logging.getLogger(__name__)` with structured key=value events

### Method-Specific Configuration: Constructor Parameters

The `MergeConfig` dataclass is generic (seed, description, drop_right_columns). Method-specific configuration is passed via constructor parameters:

```python
# IPF: constraints and convergence parameters in constructor
ipf = IPFMergeMethod(
    constraints=(
        IPFConstraint(dimension="income_bracket", targets={"low": 4000, "medium": 3000, "high": 3000}),
        IPFConstraint(dimension="region_code", targets={"84": 3500, "11": 3000, "75": 3500}),
    ),
    max_iterations=100,
    tolerance=1e-6,
)
result = ipf.merge(table_a, table_b, MergeConfig(seed=42))

# Conditional: strata columns in constructor
cond = ConditionalSamplingMethod(strata_columns=("income_bracket",))
result = cond.merge(table_a, table_b, MergeConfig(seed=42))
```

This preserves the `MergeMethod` protocol signature while allowing method-specific parameterization.

### IPF Algorithm — Detailed Specification

**Purpose:** Iterative Proportional Fitting (raking) adjusts per-row weights in table_a so that weighted marginal distributions match target values. The reweighted rows are then integerized and matched with table_b rows.

**Algorithm (record-level IPF):**

```
Input: table_a (N rows), constraints [(dimension, {cat: target}), ...]
Output: weights[0..N-1]

1. weights = [1.0, 1.0, ..., 1.0]  (length N)

2. For iteration = 0 to max_iterations - 1:
     max_deviation = 0.0
     For each constraint (dimension, targets):
       col_values = table_a.column(dimension).to_pylist()

       # Compute current weighted totals
       current_totals = {}
       for k in range(N):
           cat = col_values[k]
           current_totals[cat] = current_totals.get(cat, 0.0) + weights[k]

       # Compute and apply adjustment factors
       for cat, target in targets.items():
           current = current_totals.get(cat, 0.0)
           if current > 0:
               factor = target / current
               max_deviation = max(max_deviation, abs(current - target))
           else:
               factor = 1.0
               max_deviation = max(max_deviation, target)
           # Apply factor to all rows in this category
           for k in range(N):
               if col_values[k] == cat:
                   weights[k] *= factor

     If max_deviation < tolerance:
       return IPFResult(weights, iteration+1, converged=True, max_deviation)

3. Return IPFResult(weights, max_iterations, converged=False, max_deviation)
```

**Integerization (controlled probabilistic rounding):**

```
Input: weights (floats summing to ~total), target_count, rng
Output: int_weights (integers summing to ~target_count)

1. scale = target_count / sum(weights)
2. scaled = [w * scale for w in weights]
3. For each scaled weight:
     integer_part = floor(scaled_w)
     fractional = scaled_w - integer_part
     if rng.random() < fractional:
         int_weight = integer_part + 1
     else:
         int_weight = integer_part
4. Return int_weights
```

**Seed stream separation:** The `config.seed` is used for integerization rounding. A derived seed `config.seed + 1` is used for table_b matching. This prevents correlation between the rounding decisions and the matching decisions. Use `random.Random(seed)` for each stream (stdlib, no numpy).

**Performance note:** The IPF loop is O(N * D * I) where N = rows, D = constraint dimensions, I = iterations. For 10,000 rows, 3 dimensions, 50 iterations = 1.5M operations. Pure Python is sufficient for laptop-scale data.

### Conditional Sampling Algorithm — Detailed Specification

**Purpose:** Groups both tables by shared column(s), then performs uniform random matching within each group (stratum). This preserves the correlation between the stratification variable and all other variables.

**Algorithm:**

```
Input: table_a (N rows), table_b (M rows), strata_columns, seed

1. Compute stratum keys for each row:
     key_a[k] = tuple(table_a.column(c)[k] for c in strata_columns)
     key_b[k] = tuple(table_b.column(c)[k] for c in strata_columns)

2. Group row indices by stratum:
     strata_a = {key: [row_indices...]} for each unique key in key_a
     strata_b = {key: [row_indices...]} for each unique key in key_b

3. Validate: for each key in strata_a, key must exist in strata_b
     (raise MergeValidationError if not)

4. Match within strata:
     rng = random.Random(seed)
     matched_b_indices = []
     for k in range(N):
         key = key_a[k]
         donor_pool = strata_b[key]
         matched_b_indices.append(rng.choice(donor_pool))

5. Build right table:
     Remove strata columns from table_b (they're already in table_a)
     right_table = table_b.drop(strata_columns + drop_right_columns)
     matched_right = right_table.take(pa.array(matched_b_indices))

6. Combine: table_a columns + matched_right columns
```

**Auto-dropping strata columns from table_b:** Strata columns exist in both tables by definition. To avoid duplicate columns in the output, the method automatically adds strata column names to the effective drop list (in addition to `config.drop_right_columns`). If a strata column is already in `drop_right_columns`, it is not dropped twice.

**Stratum key computation:** Use `tuple(table.column(c)[k].as_py() for c in strata_columns)` to build hashable stratum keys. This works for any column type (utf8, int64, etc.).

### IPFConstraint and IPFResult — Exact Specifications

```python
@dataclass(frozen=True)
class IPFConstraint:
    """A marginal constraint for IPF.

    Specifies that the weighted count of rows where ``dimension``
    equals each category key should match the corresponding target value.

    Attributes:
        dimension: Column name in table_a to constrain.
        targets: Mapping from category value to target count/weight.
            All values must be >= 0.
    """

    dimension: str
    targets: dict[str, float]

    def __post_init__(self) -> None:
        if not self.dimension:
            msg = "dimension must be a non-empty string"
            raise ValueError(msg)
        if not self.targets:
            msg = "targets must be a non-empty dict"
            raise ValueError(msg)
        for cat, val in self.targets.items():
            if val < 0:
                msg = f"target for {cat!r} must be >= 0, got {val}"
                raise ValueError(msg)
        object.__setattr__(self, "targets", dict(self.targets))


@dataclass(frozen=True)
class IPFResult:
    """Convergence diagnostics from an IPF run.

    Attributes:
        weights: Per-row weights after IPF adjustment.
        iterations: Number of iterations performed.
        converged: Whether convergence was reached within tolerance.
        max_deviation: Maximum absolute deviation at termination.
    """

    weights: tuple[float, ...]
    iterations: int
    converged: bool
    max_deviation: float
```

### Error Hierarchy Extension

```python
# Added to src/reformlab/population/methods/errors.py

class MergeConvergenceError(MergeError):
    """Raised when an iterative merge method fails to converge.

    Triggered by: IPF exceeding max_iterations without reaching
    the tolerance threshold. Often caused by inconsistent marginal
    constraints (target totals that cannot be simultaneously satisfied).
    """
```

### No New Dependencies Required

All implementation uses existing dependencies and stdlib:

- `random` — deterministic random number generation (stdlib)
- `math` — `floor()` for integerization (stdlib)
- `pyarrow` — table operations, `take()` for row selection (existing dependency)
- `logging` — structured logging (stdlib)

Do **not** introduce `numpy`, `scipy`, `pandas`, or any new dependency.

**Import pattern:** `import pyarrow as pa` at module level in `ipf.py` and `conditional.py` (runtime dependency, same as `uniform.py`). In `base.py`, `pyarrow` stays under `TYPE_CHECKING` guard.

### Test Fixtures — Concrete Data

```python
# Additional fixtures in tests/population/methods/conftest.py

@pytest.fixture()
def region_income_table() -> pa.Table:
    """Table with known income_bracket and region_code distributions (10 rows).

    Distribution: income_bracket: low=3, medium=4, high=3
                  region_code: 84=4, 11=3, 75=3
    """
    return pa.table({
        "household_id": pa.array(list(range(1, 11)), type=pa.int64()),
        "income_bracket": pa.array(
            ["low", "low", "low", "medium", "medium", "medium", "medium",
             "high", "high", "high"],
            type=pa.utf8(),
        ),
        "region_code": pa.array(
            ["84", "84", "11", "84", "11", "75", "84", "11", "75", "75"],
            type=pa.utf8(),
        ),
    })


@pytest.fixture()
def energy_vehicle_table() -> pa.Table:
    """Table with income_bracket (shared), vehicle_type, energy_kwh (12 rows).

    Covers all 3 income brackets: low=4, medium=4, high=4.
    """
    return pa.table({
        "income_bracket": pa.array(
            ["low", "low", "low", "low",
             "medium", "medium", "medium", "medium",
             "high", "high", "high", "high"],
            type=pa.utf8(),
        ),
        "vehicle_type": pa.array(
            ["diesel", "diesel", "essence", "ev",
             "essence", "hybrid", "ev", "diesel",
             "ev", "ev", "hybrid", "essence"],
            type=pa.utf8(),
        ),
        "energy_kwh": pa.array(
            [8500.0, 9200.0, 7800.0, 3200.0,
             7200.0, 5100.0, 3000.0, 8800.0,
             2800.0, 3100.0, 4900.0, 6500.0],
            type=pa.float64(),
        ),
    })


@pytest.fixture()
def simple_constraints() -> tuple[IPFConstraint, ...]:
    """Single IPF constraint shifting income_bracket distribution."""
    return (
        IPFConstraint(
            dimension="income_bracket",
            targets={"low": 4.0, "medium": 3.0, "high": 3.0},
        ),
    )


@pytest.fixture()
def multi_constraints() -> tuple[IPFConstraint, ...]:
    """Two IPF constraints: income_bracket + region_code."""
    return (
        IPFConstraint(
            dimension="income_bracket",
            targets={"low": 4.0, "medium": 3.0, "high": 3.0},
        ),
        IPFConstraint(
            dimension="region_code",
            targets={"84": 3.0, "11": 4.0, "75": 3.0},
        ),
    )
```

### Test Pattern to Follow (from Story 11.4)

Follow the exact test structure from `tests/population/methods/test_uniform.py`:

1. **Class-based grouping** by feature/responsibility
2. **AC references in class docstrings**
3. **Direct assertions** — `assert` statements, `pytest.raises(ExceptionClass, match=...)` for errors
4. **Fixtures via conftest** — injected by parameter name
5. **Frozen dataclass tests** — verify immutability with `pytest.raises(AttributeError)`
6. **Determinism tests** — same seed → identical result, different seed → different
7. **Docstring tests** — verify pedagogical content is present

### IPF Marginal Matching Tolerance in Tests

Due to integerization (probabilistic rounding of fractional weights), the output row counts per category will not match targets exactly. Tests should allow ±1 tolerance:

```python
# Example test pattern for marginal matching
counts = {}
for val in result.table.column("income_bracket").to_pylist():
    counts[val] = counts.get(val, 0) + 1
# Target was {"low": 4.0, "medium": 3.0, "high": 3.0}
assert abs(counts.get("low", 0) - 4) <= 1
assert abs(counts.get("medium", 0) - 3) <= 1
assert abs(counts.get("high", 0) - 3) <= 1
```

### Conditional Sampling: Strata Column Auto-Drop Behavior

The conditional sampling method automatically removes strata columns from the table_b side of the merge to prevent column name conflicts. This is a semantic decision: the strata columns already exist in table_a, so duplicating them would be redundant and would trigger the column conflict check.

The auto-drop is **in addition to** any `config.drop_right_columns` specified by the caller. The effective drop list is the union of both.

### Downstream Dependencies

Story 11.5 is consumed by:

- **Story 11.6** (PopulationPipeline) — composes loaders + methods, calls `merge()` in sequence, collects `MergeAssumption` records
- **Story 11.7** (Validation) — validates merged population against marginals (IPF output should pass validation by construction)
- **Story 11.8** (Notebook) — demonstrates all three merge methods with plain-language explanations, showing progressive improvement from uniform → conditional → IPF

### Project Structure Notes

**New files (4):**
- `src/reformlab/population/methods/ipf.py`
- `src/reformlab/population/methods/conditional.py`
- `tests/population/methods/test_ipf.py`
- `tests/population/methods/test_conditional.py`

**Modified files (6):**
- `src/reformlab/population/methods/base.py` — add `IPFConstraint`, `IPFResult`
- `src/reformlab/population/methods/errors.py` — add `MergeConvergenceError`
- `src/reformlab/population/methods/__init__.py` — add new exports, update `__all__`
- `src/reformlab/population/__init__.py` — add new exports, update `__all__`
- `tests/population/methods/conftest.py` — add new fixtures
- `tests/population/methods/test_base.py` — add `TestIPFConstraint`, `TestIPFResult`
- `tests/population/methods/test_errors.py` — add `TestMergeConvergenceError`

**No changes** to `pyproject.toml` (no new dependencies, no new markers needed)

### Alignment with Project Conventions

All rules from `project-context.md` apply:

- Every file starts with `from __future__ import annotations`
- `if TYPE_CHECKING:` guards for annotation-only imports (in `base.py` only — `ipf.py` and `conditional.py` use `pyarrow` at runtime)
- Frozen dataclasses as default (`@dataclass(frozen=True)`) for `IPFConstraint`, `IPFResult`
- Protocols, not ABCs — new methods satisfy `MergeMethod` protocol via duck typing
- Subsystem-specific exceptions (`MergeConvergenceError`, not bare `Exception`)
- `dict[str, Any]` for metadata bags with stable string-constant keys
- `tuple[...]` for immutable sequences (`IPFConstraint.targets` stored as dict but deep-copied; `IPFResult.weights` as tuple)
- `X | None` union syntax, not `Optional[X]`
- Module-level docstrings referencing story/FR
- `logging.getLogger(__name__)` with structured key=value format
- `# ====...====` section separators for major sections within longer modules

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#New-Subsystem-Population-Generation] — Directory structure, MergeMethod protocol specification
- [Source: _bmad-output/planning-artifacts/epics.md#BKL-1105] — Story definition and acceptance criteria
- [Source: _bmad-output/planning-artifacts/prd.md#FR38] — "System provides a library of statistical methods for merging datasets that do not share the same sample (uniform distribution, IPF, conditional sampling, statistical matching)"
- [Source: _bmad-output/planning-artifacts/prd.md#FR39] — "Analyst can choose which merge method to apply at each dataset join, with plain-language explanation of the assumption"
- [Source: _bmad-output/project-context.md#Python-Language-Rules] — Frozen dataclasses, Protocols, `from __future__ import annotations`
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules] — PyArrow canonical data type, no pandas in core logic
- [Source: src/reformlab/population/methods/base.py] — MergeMethod protocol, MergeConfig, MergeAssumption, MergeResult (Story 11.4)
- [Source: src/reformlab/population/methods/uniform.py] — UniformMergeMethod implementation pattern to follow
- [Source: src/reformlab/population/methods/errors.py] — MergeError hierarchy pattern (summary-reason-fix)
- [Source: src/reformlab/governance/manifest.py#AssumptionEntry] — TypedDict with key/value/source/is_default; JSON-compatibility validation
- [Source: tests/population/methods/test_uniform.py] — Test patterns: class-based grouping, fixture injection, direct assertions
- [Source: tests/population/methods/conftest.py] — Existing test fixtures
- [Source: _bmad-output/implementation-artifacts/11-4-define-mergemethod-protocol-and-uniform-distribution-method.md] — Previous story (protocol reference, implementation patterns)

## File List

**New files (4):**
- `src/reformlab/population/methods/ipf.py`
- `src/reformlab/population/methods/conditional.py`
- `tests/population/methods/test_ipf.py`
- `tests/population/methods/test_conditional.py`

**Modified files (7):**
- `src/reformlab/population/methods/base.py` — add `IPFConstraint`, `IPFResult`
- `src/reformlab/population/methods/errors.py` — add `MergeConvergenceError`
- `src/reformlab/population/methods/__init__.py` — add new exports
- `src/reformlab/population/__init__.py` — add new exports
- `tests/population/methods/conftest.py` — add new fixtures
- `tests/population/methods/test_base.py` — add new type tests
- `tests/population/methods/test_errors.py` — add convergence error tests

## Dev Agent Record

### Completion Notes

## Change Log

- 2026-03-03: Story created by create-story workflow — comprehensive developer context with IPF algorithm specification (record-level reweighting + integerization + matching), conditional sampling algorithm (stratum-based matching with auto-drop), new supporting types (IPFConstraint, IPFResult, MergeConvergenceError), test fixture designs, downstream dependency mapping, and plain-language pedagogical explanations for both methods.


]]></file>
<file id="173799eb" path="src/reformlab/population/__init__.py" label="SOURCE CODE"><![CDATA[

"""Realistic population generation library for ReformLab.

Provides institutional data source loaders, statistical fusion methods,
and population pipeline composition for building synthetic populations
from open data sources (INSEE, Eurostat, ADEME, SDES).

This module implements EPIC-11 (Realistic Population Generation Library).
Phase 2 introduces optional network dependencies for data downloads,
with offline-first caching semantics.

Public API
----------
DataSourceLoader : Protocol
    Interface for institutional data source loaders.
SourceConfig : dataclass
    Immutable configuration for a data source download.
CacheStatus : dataclass
    Status of a cached data source.
SourceCache : class
    Disk-based caching infrastructure for downloaded data.
CachedLoader : class
    Base class wrapping protocol + cache logic.
MergeMethod : Protocol
    Interface for statistical dataset fusion methods.
MergeConfig : dataclass
    Immutable configuration for a merge operation.
MergeAssumption : dataclass
    Structured assumption record from a merge operation.
MergeResult : dataclass
    Immutable result of a merge operation.
UniformMergeMethod : class
    Uniform random matching with replacement.
"""

from __future__ import annotations

from reformlab.population.loaders.ademe import (
    ADEME_AVAILABLE_DATASETS,
    ADEME_CATALOG,
    ADEMEDataset,
    ADEMELoader,
    get_ademe_loader,
    make_ademe_config,
)
from reformlab.population.loaders.base import (
    CachedLoader,
    CacheStatus,
    DataSourceLoader,
    SourceConfig,
)
from reformlab.population.loaders.cache import SourceCache
from reformlab.population.loaders.errors import (
    DataSourceDownloadError,
    DataSourceError,
    DataSourceOfflineError,
    DataSourceValidationError,
)
from reformlab.population.loaders.eurostat import (
    EUROSTAT_AVAILABLE_DATASETS,
    EUROSTAT_CATALOG,
    EurostatDataset,
    EurostatLoader,
    get_eurostat_loader,
    make_eurostat_config,
)
from reformlab.population.loaders.insee import (
    AVAILABLE_DATASETS,
    INSEE_AVAILABLE_DATASETS,
    INSEE_CATALOG,
    INSEEDataset,
    INSEELoader,
    get_insee_loader,
    make_insee_config,
)
from reformlab.population.loaders.sdes import (
    SDES_AVAILABLE_DATASETS,
    SDES_CATALOG,
    SDESDataset,
    SDESLoader,
    get_sdes_loader,
    make_sdes_config,
)
from reformlab.population.methods.base import (
    MergeAssumption,
    MergeConfig,
    MergeMethod,
    MergeResult,
)
from reformlab.population.methods.errors import (
    MergeError,
    MergeValidationError,
)
from reformlab.population.methods.uniform import UniformMergeMethod

__all__ = [
    "ADEME_AVAILABLE_DATASETS",
    "ADEME_CATALOG",
    "ADEMEDataset",
    "ADEMELoader",
    "AVAILABLE_DATASETS",
    "CachedLoader",
    "CacheStatus",
    "DataSourceDownloadError",
    "DataSourceError",
    "DataSourceLoader",
    "DataSourceOfflineError",
    "DataSourceValidationError",
    "EUROSTAT_AVAILABLE_DATASETS",
    "EUROSTAT_CATALOG",
    "EurostatDataset",
    "EurostatLoader",
    "INSEE_AVAILABLE_DATASETS",
    "INSEE_CATALOG",
    "INSEEDataset",
    "INSEELoader",
    "SDES_AVAILABLE_DATASETS",
    "SDES_CATALOG",
    "SDESDataset",
    "SDESLoader",
    "SourceCache",
    "SourceConfig",
    "get_ademe_loader",
    "get_eurostat_loader",
    "get_insee_loader",
    "get_sdes_loader",
    "MergeAssumption",
    "MergeConfig",
    "MergeError",
    "MergeMethod",
    "MergeResult",
    "MergeValidationError",
    "UniformMergeMethod",
    "make_ademe_config",
    "make_eurostat_config",
    "make_insee_config",
    "make_sdes_config",
]


]]></file>
<file id="f2467725" path="src/reformlab/population/methods/__init__.py" label="SOURCE CODE"><![CDATA[

"""Statistical fusion methods library for population generation.

Provides the ``MergeMethod`` protocol for dataset fusion, supporting
types (``MergeConfig``, ``MergeAssumption``, ``MergeResult``), and
concrete implementations starting with ``UniformMergeMethod``.

Implements Story 11.4 (MergeMethod protocol and uniform distribution).
References FR38 (statistical methods library) and FR39 (merge method
selection with plain-language explanations).
"""

from __future__ import annotations

from reformlab.population.methods.base import (
    MergeAssumption,
    MergeConfig,
    MergeMethod,
    MergeResult,
)
from reformlab.population.methods.errors import (
    MergeError,
    MergeValidationError,
)
from reformlab.population.methods.uniform import UniformMergeMethod

__all__ = [
    "MergeAssumption",
    "MergeConfig",
    "MergeError",
    "MergeMethod",
    "MergeResult",
    "MergeValidationError",
    "UniformMergeMethod",
]


]]></file>
<file id="63a021f4" path="src/reformlab/population/methods/base.py" label="SOURCE CODE"><![CDATA[

"""MergeMethod protocol and supporting types for statistical dataset fusion.

Defines the structural interface that all merge methods must satisfy,
plus immutable value objects for configuration, assumption records,
and merge results.

Implements Story 11.4 (MergeMethod protocol and uniform distribution).
References FR38 (statistical methods library).
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    import pyarrow as pa


# ====================================================================
# Configuration
# ====================================================================


@dataclass(frozen=True)
class MergeConfig:
    """Immutable configuration for a merge operation.

    Attributes:
        seed: Random seed for deterministic merge operations. Must be >= 0.
        description: Optional human-readable description for governance.
        drop_right_columns: Column names to remove from table_b before
            merging. Use this to remove shared key columns (e.g.,
            ``"region_code"``) that exist in both tables but should only
            appear once in the result.
    """

    seed: int
    description: str = ""
    drop_right_columns: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            msg = f"seed must be a non-negative integer, got {self.seed!r}"
            raise ValueError(msg)
        if self.seed < 0:
            msg = f"seed must be a non-negative integer, got {self.seed!r}"
            raise ValueError(msg)
        # Coerce to tuple to ensure immutability (caller may pass a list)
        object.__setattr__(
            self, "drop_right_columns", tuple(self.drop_right_columns)
        )


# ====================================================================
# Assumption record
# ====================================================================


@dataclass(frozen=True)
class MergeAssumption:
    """Structured assumption record from a merge operation.

    Records the method name, a plain-language assumption statement,
    and method-specific details. Can be converted to governance
    ``AssumptionEntry`` format via ``to_governance_entry()``.

    Attributes:
        method_name: Short identifier for the method (e.g., ``"uniform"``).
        statement: Plain-language description of the assumption made.
        details: Method-specific metadata. Values must be JSON-compatible
            (``str``, ``int``, ``float``, ``bool``, ``None``, ``list``,
            ``dict``). Never put ``pa.Table``, ``pa.Schema``, ``Path``,
            or custom objects in details.
    """

    method_name: str
    statement: str
    details: dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "details", deepcopy(self.details))

    def to_governance_entry(
        self, *, source_label: str = "merge_step"
    ) -> dict[str, Any]:
        """Convert to governance-compatible assumption entry.

        Returns a dict matching ``governance.manifest.AssumptionEntry``
        structure: ``key``, ``value``, ``source``, ``is_default``.

        The ``value`` field unpacks ``details`` first, then overrides
        with ``method`` and ``statement`` keys to prevent collision.

        Note: When appending to ``RunManifest.assumptions``
        (typed ``list[AssumptionEntry]``), mypy strict requires an
        explicit ``cast(AssumptionEntry, ...)`` at the call site.
        Cross-subsystem import of ``AssumptionEntry`` here is
        intentionally avoided to prevent coupling.
        """
        return {
            "key": f"merge_{self.method_name}",
            "value": {
                **self.details,
                "method": self.method_name,
                "statement": self.statement,
            },
            "source": source_label,
            "is_default": False,
        }


# ====================================================================
# Merge result
# ====================================================================


@dataclass(frozen=True)
class MergeResult:
    """Immutable result of a merge operation.

    Attributes:
        table: The merged PyArrow table.
        assumption: Structured assumption record documenting the merge.
    """

    table: pa.Table
    assumption: MergeAssumption


# ====================================================================
# MergeMethod protocol
# ====================================================================


@runtime_checkable
class MergeMethod(Protocol):
    """Interface for statistical dataset fusion methods.

    Structural (duck-typed) protocol: any class that implements
    ``merge()`` and the ``name`` property with the correct signatures
    satisfies the contract — no explicit inheritance required.

    Each method merges two ``pa.Table`` objects using a specific
    statistical approach, returning the merged table and an assumption
    record documenting the methodological choice.
    """

    @property
    def name(self) -> str:
        """Short identifier for this method (e.g., ``"uniform"``, ``"ipf"``)."""
        ...

    def merge(
        self,
        table_a: pa.Table,
        table_b: pa.Table,
        config: MergeConfig,
    ) -> MergeResult:
        """Merge two tables using this method's statistical approach."""
        ...


]]></file>
<file id="1d910d88" path="[Validator A]" label="VALIDATION OUTPUT"><![CDATA[

# 🎯 Story Context Validation Report

**Story:** 11-5-implement-ipf-and-conditional-sampling-merge-methods
**Story File:** `_bmad-output/implementation-artifacts/11-5-implement-ipf-and-conditional-sampling-merge-methods.md`
**Validated:** 2026-03-03
**Validator:** Quality Competition Engine

---

## Executive Summary

| Category | Found |
|----------|-------|
| 🚨 Critical Issues | 3 |
| ⚡ Enhancements | 4 |
| ✨ Optimizations | 3 |
| 🤖 LLM Optimizations | 1 |

**Overall Assessment:** The story is architecturally sound with well-specified algorithms and clear patterns to follow. However, three issues could cause genuine implementation failures: a missing concrete fixture definition for the convergence failure test case, an undefined variable reference in the conditional sampling pseudocode, and an unused parameter in the `_run_ipf` signature. These are not blocking story viability but will cause a developer to write buggy or confused code without noticing.

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🔴 CRITICAL | `inconsistent_constraints` fixture has no concrete Python code — developer must guess values that reliably trigger non-convergence | Task 6.1 / Dev Notes | +3 |
| 🔴 CRITICAL | `strata_info` variable referenced in conditional sampling `details` construction but never defined in the algorithm spec | Task 4.4, bullet 12 | +3 |
| 🟠 IMPORTANT | `_run_ipf(self, table_a, config)` — `config` parameter is never used by the function body per the spec; misleading and risks unused-arg mypy warning | Task 3.4 | +1 |
| 🟠 IMPORTANT | `table_b.drop(strata_columns + drop_right_columns)` pseudocode can produce duplicate entries → pyarrow runtime error; deduplication is mentioned in prose but missing from algorithm | Task 4.4 / Dev Notes | +1 |
| 🟠 IMPORTANT | File list count inconsistency: "Project Structure Notes" says "Modified files (6)" but lists 7 files | Dev Notes section | +1 |
| 🟡 MINOR | No concrete `max_iterations` guidance for the non-convergence test constructor | Task 7.1 | +0.3 |
| 🟡 MINOR | `IPFConstraint.targets: dict[str, float]` — int64-coded columns require string-converted keys; no callout | Task 1.1 | +0.3 |
| 🟡 MINOR | Missing test for "warning logged when constraint category absent from table_a" case | Task 3.4, step 3 | +0.3 |
| 🟢 CLEAN PASS | INVEST criteria — story is well-formed | — | -0.5 |
| 🟢 CLEAN PASS | Architecture alignment — directory structure, protocol pattern, imports all correct | — | -0.5 |
| 🟢 CLEAN PASS | Algorithm correctness — IPF and conditional sampling logics are sound | — | -0.5 |
| 🟢 CLEAN PASS | Dependencies — no new dependencies, stdlib only | — | -0.5 |

### Evidence Score: **7.9** → **MAJOR REWORK**

The score is above the MAJOR REWORK threshold primarily due to two CRITICAL findings (the missing fixture concrete code and the undefined `strata_info` variable) that would both cause the developer to produce incorrect tests or implementation.

---

## 🎯 Ruthless Story Validation 11.5

### INVEST Criteria Assessment

| Criterion | Status | Severity | Details |
|-----------|--------|----------|---------|
| **I**ndependent | ✅ PASS | 1/10 | Clearly builds on 11.4 types (MergeMethod, MergeConfig, etc.) which are confirmed implemented |
| **N**egotiable | ✅ PASS | 2/10 | Algorithm is heavily specified but appropriately so — this is a numerical method that must be deterministic |
| **V**aluable | ✅ PASS | 1/10 | Clear value: more realistic populations, EPF/ADEME data fusion |
| **E**stimable | ⚠️ WARN | 4/10 | 8 SP estimate is reasonable but conditional sampling stratum-coverage edge cases add hidden complexity |
| **S**mall | ✅ PASS | 3/10 | Two methods + tests in one story is slightly large but manageable |
| **T**estable | ⚠️ WARN | 5/10 | AC #1 ("documented tolerances") relies on `inconsistent_constraints` fixture that has no concrete definition |

### INVEST Violations

- **[4/10] Estimable:** The integerization path (all-zero expansion edge case) and stratum-coverage validation edge cases are not estimated against. Developer will encounter these during implementation, not before.
- **[5/10] Testable:** AC #1 convergence failure path depends on `inconsistent_constraints` fixture that is described in one sentence but lacks concrete Python code in the Dev Notes.

### Acceptance Criteria Issues

- **Underspecified — AC #1:** "matches the target marginals within documented tolerances" — the tolerance is 1e-6 at the weight level but ±1 row at the integer level. Both tolerances are documented, but the AC text doesn't distinguish between them. A strict reading could mean the test must achieve 1e-6 precision, which is impossible after integerization.
  - *Quote:* "the merged population matches the target marginals within documented tolerances"
  - *Recommendation:* Add: "IPF convergence tolerance is `1e-6` (default); after integerization the per-category row count matches within ±1."

- **Missing edge case — AC #3:** Conditional sampling is only described for the happy path. No AC addresses what happens when a stratum exists in table_a but not table_b.
  - *Quote:* "when conditional sampling is applied, then matches are drawn within strata defined by the conditioning variable"
  - *Recommendation:* Add: "Given table_a has a stratum with no matching rows in table_b, when conditional sampling is applied, then a `MergeValidationError` is raised listing the missing strata."

### Hidden Risks and Dependencies

- **Convergence behavior with small fixtures:** The `region_income_table` has only 10 rows. IPF convergence with 10 rows may be fast enough that even mildly inconsistent constraints converge within 100 iterations. If `inconsistent_constraints` is not designed aggressively enough (e.g., sum mismatch factor of 1.5x), the non-convergence test will spuriously pass (IPF actually converges) and the `MergeConvergenceError` branch will never be tested.
  - *Impact:* Dead code path — the `MergeConvergenceError` branch is never exercised in CI.
  - *Mitigation:* Use a large sum mismatch (2x or 3x) in `inconsistent_constraints`. Concrete fixture provided in Critical Issue #1 below.

- **PyArrow `table.drop()` vs `table.remove_column()`:** The conditional sampling pseudocode uses `table_b.drop(strata_columns + drop_right_columns)`. The `uniform.py` implementation uses `remove_column(col_idx)` iteratively. PyArrow's `Table.drop()` exists in PyArrow >= 0.17 but the behaviour on duplicate names in the list is undefined (may raise or silently ignore). The story mixes approaches without explaining why.
  - *Impact:* If developer follows the pseudocode literally and passes duplicate names, a runtime error or silent misbehaviour occurs.
  - *Mitigation:* Deduplicate the drop list explicitly before calling `drop()`.

### Estimation Reality-Check

**Assessment: Realistic (slightly underestimated)**

The 8 SP estimate is reasonable for two algorithms with comprehensive tests. However, the IPF integerization edge cases (zero-weight rows, sum-to-zero guard) and the stratum-coverage validation with helpful error messages will add 1-2 hours beyond the happy path. The estimate does not account for debugging the convergence behavior with the fixture-defined constraints.

### Technical Alignment

**Status: ✅ ALIGNED with one caveat**

All file paths, class names, protocol usage, frozen dataclass patterns, and error hierarchy match the architecture document and preceding implementations. The one caveat: the story correctly specifies `import pyarrow as pa` at module level in `ipf.py` and `conditional.py` (not under TYPE_CHECKING), matching the `uniform.py` established pattern.

---

## 🚨 Critical Issues (Must Fix)

### 1. `inconsistent_constraints` Fixture Has No Concrete Definition

**Impact:** The `TestIPFMergeMethodConvergence` non-convergence test case will either be skipped, written incorrectly, or produce a fixture that happens to converge — leaving the `MergeConvergenceError` code path permanently untested.

**Source:** Task 6.1 / Dev Notes "Test Fixtures — Concrete Data"

**Problem:**

Task 6.1 lists five fixtures to add to `conftest.py`, including `inconsistent_constraints`. The description is: "constraints where totals across dimensions don't match (for convergence failure testing)". The "Test Fixtures — Concrete Data" section in Dev Notes provides concrete Python code for four of the five fixtures but **completely omits** `inconsistent_constraints`. A developer implementing this story sees a one-sentence description and must independently figure out what "inconsistent" means mathematically and what values will reliably fail to converge within 100 iterations.

Classic IPF non-convergence requires constraints whose grand totals across dimensions differ. For the `region_income_table` (10 rows), the minimum viable inconsistent fixture must have a large enough total mismatch that 100 iterations definitely cannot resolve it:

**Recommended Fix:**

Add the following concrete fixture to the "Test Fixtures — Concrete Data" section:

```python
@pytest.fixture()
def inconsistent_constraints() -> tuple[IPFConstraint, ...]:
    """Two constraints with mismatched grand totals — reliably causes non-convergence.

    income_bracket targets sum to 10 (matches 10-row table).
    region_code targets sum to 30 (3x mismatch forces perpetual oscillation).
    With 100 iterations at tolerance=1e-6, IPF cannot converge.
    """
    return (
        IPFConstraint(
            dimension="income_bracket",
            targets={"low": 4.0, "medium": 3.0, "high": 3.0},
        ),
        IPFConstraint(
            dimension="region_code",
            targets={"84": 10.0, "11": 10.0, "75": 10.0},  # sum=30, not 10
        ),
    )
```

Also specify in `TestIPFMergeMethodConvergence` that the test must construct `IPFMergeMethod(constraints=inconsistent_constraints, max_iterations=100, tolerance=1e-6)` to ensure the default parameters are used.

---

### 2. `strata_info` Variable Referenced But Never Defined in Conditional Sampling Algorithm

**Impact:** The developer implementing Task 4.4 will encounter an undefined variable reference in the `details` dict construction and have to reverse-engineer its meaning from context.

**Source:** Task 4.4, bullet 12

**Problem:**

The `details` dict in the `MergeAssumption` is specified as:

```python
"strata_sizes": {str(k): {"table_a": len(v_a), "table_b": len(v_b)} for k, v_a, v_b in strata_info}
```

`strata_info` is never defined anywhere in the algorithm specification. It appears to be an implied iterator over `(key, strata_a[key], strata_b_combined[key])` but this is not documented. Questions the developer must answer without guidance:

1. Does `strata_info` iterate over strata in table_a only, or the union of table_a and table_b strata?
2. What happens for strata that exist in table_b but not table_a (they'd have no `v_a`)? (They were never in table_a, so `strata_a` doesn't have them.)
3. Should `v_b` reflect the original table_b indices or the indices after `drop_right_columns`?

**Recommended Fix:**

Replace the ambiguous `strata_info` reference with a direct definition:

```python
"strata_sizes": {
    str(key): {
        "table_a": len(strata_a[key]),
        "table_b": len(strata_b[key])  # only strata present in table_a (coverage-validated)
    }
    for key in strata_a
}
```

Also specify that the key serialization for multi-column strata should be `"|".join(str(x) for x in key)` rather than `str(key)` to avoid Python tuple repr artifacts in JSON output.

---

### 3. `_run_ipf` Has an Unused `config: MergeConfig` Parameter

**Impact:** Mypy strict may flag an unused parameter; developer must decide what to do with it. Worse, a developer may mistakenly use `config.seed` inside `_run_ipf` thinking it's needed there (it's not — seed is only for integerization in `merge()`).

**Source:** Task 3.4

**Problem:**

The signature is specified as `_run_ipf(self, table_a: pa.Table, config: MergeConfig) -> IPFResult`. However, walking through the entire algorithm specification for `_run_ipf` (steps 1–5), `config` is never referenced:

- Step 1: Uses `table_a.num_rows`
- Steps 2–3: Uses `self._constraints` and `table_a.column(...)`
- Step 4: Uses `self._constraints`, `self._tolerance`, `self._max_iterations`
- Step 5: Returns `IPFResult`

The `config.seed` is only used in `merge()` for `_integerize_weights` (step 6). The `config` parameter serves no purpose in `_run_ipf`.

**Recommended Fix:**

Change the signature to `_run_ipf(self, table_a: pa.Table) -> IPFResult` and call it from `merge()` as `ipf_result = self._run_ipf(table_a)`. This is cleaner, avoids the unused parameter, and makes each function's responsibilities clear.

---

## ⚡ Enhancement Opportunities (Should Add)

### 1. Conditional Sampling Drop-List Deduplication — Missing From Algorithm Pseudocode

**Benefit:** Prevents a runtime pyarrow error when a strata column is also listed in `config.drop_right_columns`.

**Source:** Task 4.4 / Dev Notes "Conditional Sampling: Strata Column Auto-Drop Behavior"

**Current Gap:**

The Dev Notes prose says: "If a strata column is already in `drop_right_columns`, it is not dropped twice." But the algorithm pseudocode directly contradicts this guidance by writing `table_b.drop(strata_columns + drop_right_columns)` — simple tuple concatenation without deduplication. PyArrow's `Table.drop()` with duplicate column names in the list raises an `ArrowInvalid` error.

**Suggested Addition:**

Add to Task 4.4 step 3: "Compute `effective_drop = tuple(dict.fromkeys(strata_columns + config.drop_right_columns))` to preserve order while deduplicating. Apply `right_table = table_b.remove_column()` iteratively (matching the `uniform.py` pattern) rather than calling `table_b.drop(effective_drop)` directly. This avoids the duplicate-name runtime error and keeps implementation consistent with `uniform.py`."

Also add a test to `TestConditionalSamplingMethodDropRightColumns`: "When a strata column name appears in both `strata_columns` and `config.drop_right_columns`, no error is raised and the column appears exactly once in the output (from table_a side)."

---

### 2. IPF Edge Case: Empty `expanded_indices` When All Weights Integerize to 0

**Benefit:** Prevents a silent "0-row merged table" that would not raise an error but would violate AC #1.

**Source:** Task 3.5 / `_integerize_weights`

**Current Gap:**

If IPF weights are sufficiently extreme (e.g., a constraint pushes one category's weight to 0.001 while table_a only has rows in that category), integerization could produce `int_weights = [0, 0, 0, ...]`. This would make `expanded_indices = []` and `expanded_a` a 0-row table, which would silently produce a 0-row merged result. No error is raised, but the merge output is clearly wrong.

**Suggested Addition:**

Add to Task 3.6 after step 7: "If `len(expanded_indices) == 0`, raise `MergeValidationError` with summary='IPF produced empty expansion', reason='All row weights integerized to 0 — no rows survive expansion', fix='Check constraint targets for extreme values or structural zeros.' This validates that the IPF output is usable before proceeding."

---

### 3. `TestIPFMergeMethodConvergence` Needs `max_iterations` Specification

**Benefit:** Prevents the developer from using incorrect constructor parameters in the non-convergence test, which could accidentally allow convergence.

**Source:** Task 7.1 — `TestIPFMergeMethodConvergence`

**Current Gap:**

The test description says: "Non-convergent case (inconsistent constraints): raises `MergeConvergenceError`" but doesn't specify the `IPFMergeMethod` constructor arguments to use. If the developer uses `max_iterations=1000` instead of 100, extremely inconsistent constraints might still appear convergent.

**Suggested Addition:**

In Task 7.1 `TestIPFMergeMethodConvergence`, specify: "Use `IPFMergeMethod(constraints=inconsistent_constraints, max_iterations=100, tolerance=1e-6)` to test non-convergence with default parameters. Do not use a very low `max_iterations` (e.g., 1) as this tests parameter validation, not convergence behavior."

---

### 4. Missing Test: Warning Logged for Absent Constraint Category

**Benefit:** Verifies that the `log warning` behavior in `_run_ipf` step 3 is actually implemented.

**Source:** Task 3.4, step 3

**Current Gap:**

Step 3 of `_run_ipf` says: "log warning for categories not present (they cannot be satisfied), raise `MergeValidationError` if **all** categories in a constraint are missing." The test suite covers the "all categories missing → error" case implicitly, but there is no test for the "some categories missing → warning logged" case. This warning behavior is important for analysts debugging marginal mismatches.

**Suggested Addition:**

Add to `TestIPFMergeMethodInvalidConstraintDimension` (or a new class): "When a constraint specifies a target category not present in table_a (but at least one category IS present), `merge()` completes successfully and a warning is logged. Use `caplog` fixture with `caplog.set_level(logging.WARNING)` to verify the warning was emitted."

---

## ✨ Optimizations (Nice to Have)

### 1. `IPFConstraint.targets` Key Type Limitation Is Undocumented

**Value:** Prevents confusion when an analyst tries to constrain an int64-coded column.

**Suggestion:**

`IPFConstraint.targets` is `dict[str, float]`, which means all category keys must be strings. But SDES and INSEE loaders produce int64-coded columns (e.g., fleet counts by `vehicle_age` which is `int64`). If an analyst wants to constrain on `vehicle_age == 3`, they must provide `"3"` as the key string, not `3`. Add a note to the `IPFConstraint` docstring: "Category keys must be strings. For integer-coded columns (e.g., `vehicle_age: int64`), convert category values to strings: `targets={'3': 1000.0, '7': 500.0}`."

---

### 2. IPF Stratum Key Serialization for `strata_sizes` in Details

**Value:** Produces clean JSON output instead of Python repr artifacts.

**Suggestion:**

The `strata_sizes` keys will be `str(('low', '84'))` = `"('low', '84')"` for multi-column strata. This Python tuple repr is technically JSON-compatible but ugly and fragile. Recommend specifying `"|".join(str(x) for x in key)` in the story to produce `"low|84"` as the key. Add a test that verifies `strata_sizes` keys are serializable to clean JSON strings.

---

### 3. Performance Note for Stratum Key Computation

**Value:** Prevents O(N²) implementation in `conditional.py`.

**Suggestion:**

The stratum key computation pseudocode `tuple(table.column(c)[k].as_py() for c in strata_columns)` iterates per-row per-column. For 100k rows and 2 strata columns, this is 200k individual PyArrow element accesses, each with Python overhead. The more efficient approach is to extract full column arrays first: `col_arrays = {c: table.column(c).to_pylist() for c in strata_columns}` then build keys as `tuple(col_arrays[c][k] for c in strata_columns)`. Add this optimization hint to Task 4.4 with an expected O(N) computation for key building.

---

## 🤖 LLM Optimization Improvements

### 1. File List Count Inconsistency Breaks Quick-Scan Accuracy

**Issue:** Stale count
**Token Impact:** Low (small confusion, developer re-counts manually)

**Current (Project Structure Notes):**
```
**Modified files (6):**
- base.py
- errors.py
- methods/__init__.py
- population/__init__.py
- conftest.py
- test_base.py
- test_errors.py
```

**Optimized:**
```
**Modified files (7):**
[same 7 files listed]
```

**Rationale:** The Project Structure Notes section says "Modified files (6)" but lists 7 files. The File List section at the bottom correctly says "(7)". A developer scanning the story sees the conflicting counts and may doubt the accuracy of the file list. Fix the count in Project Structure Notes to match.

---

## 📝 Changes Applied

No changes were applied to the story file. This report serves as documentation only.

---

## 🏆 Competition Results

### Quality Metrics

| Metric | Score |
|--------|-------|
| Requirements Coverage | 92% |
| Architecture Alignment | 98% |
| Previous Story Integration | 96% |
| LLM Optimization Score | 85% |
| **Overall Quality Score** | **93%** |

### Disaster Prevention Assessment

- **Reinvention Risk:** ✅ Clean — story correctly references uniform.py as the template and specifies matching patterns
- **Technical Specification:** ⚠️ Two spec gaps (undefined `strata_info`, unused `config` param in `_run_ipf`)
- **File Structure:** ✅ All file paths correct, matches architecture.md exactly
- **Regression Risk:** ✅ Low — modifications to base.py and errors.py are additive only
- **Implementation Disasters:** ⚠️ The missing `inconsistent_constraints` fixture could leave the `MergeConvergenceError` branch permanently untested

### Competition Outcome

🏆 **Validator identified 11 improvements** (3 critical, 4 enhancements, 3 optimizations, 1 LLM optimization) that enhance the story context.

The story is fundamentally well-constructed — the algorithm specifications are complete and correct, pattern references are accurate, and test coverage is comprehensive. The critical issues are all "last 5%" gaps where an otherwise excellent story left ambiguities that could cause real implementation problems.

---

**Report Generated:** 2026-03-03
**Validation Engine:** BMAD Method Quality Competition v1.0

]]></file>
<file id="557aedd2" path="[Validator B]" label="VALIDATION OUTPUT"><![CDATA[

# 🎯 Story Context Validation Report

**Story:** 11-5-implement-ipf-and-conditional-sampling-merge-methods - implement-ipf-and-conditional-sampling-merge-methods  
**Story File:** _bmad-output/implementation-artifacts/11-5-implement-ipf-and-conditional-sampling-merge-methods.md  
**Validated:** 2026-03-03  
**Validator:** Quality Competition Engine

---

## Executive Summary

### Issues Overview

| Category | Found | Applied |
|----------|-------|---------|
| 🚨 Critical Issues | 1 | 0 |
| ⚡ Enhancements | 3 | 0 |
| ✨ Optimizations | 1 | 0 |
| 🤖 LLM Optimizations | 1 | 0 |

**Overall Assessment:** MAJOR REWORK

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🔴 CRITICAL | AC1 lacks concrete tolerance/precision definition, making “matches target marginals” untestable | Acceptance Criteria | +3 |
| 🟠 IMPORTANT | Conditional sampling flow omits required behavior when strata are absent in table_b (silent data loss risk) | Tasks 4.4–4.6 | +1 |
| 🟠 IMPORTANT | IPF integerization/total-preservation rules not specified; merged population size may drift | Task 3.5–3.6 | +1 |
| 🟠 IMPORTANT | Story scope (two full algorithms + exhaustive tests) likely exceeds “small”/estimable size without guidance | Overall Story Scope | +1 |

| 🟢 CLEAN PASS | 1 |

### Evidence Score: 5.5

| Score | Verdict |
|-------|---------|
| **5.5** | **MAJOR REWORK** |

---

## 🎯 Ruthless Story Validation 11.5

### INVEST Criteria Assessment

| Criterion | Status | Severity | Details |
|-----------|--------|----------|---------|
| **I**ndependent | ❗ Partially dependent | 3/10 | Depends on Story 11.4 types and Story 11.6 pipeline; not fully stand‑alone. |
| **N**egotiable | ✅ Mostly negotiable | 2/10 | Implementation freedom exists, though some prescriptive seeds/flow given. |
| **V**aluable | ✅ Clear value | 0/10 | Adds realistic population merging methods aligned with FR38/FR39. |
| **E**stimable | ⚠️ Hard to estimate | 6/10 | Two algorithms, convergence logic, integerization, and large test matrix make effort uncertain. |
| **S**mall | ❌ Too large | 7/10 | Covers two substantial methods + fixtures + many tests; likely > single sprint chunk. |
| **T**estable | ❌ Poorly testable | 8/10 | AC1/AC2 omit explicit tolerance and success thresholds; AC3/AC4 miss negative paths. |

### INVEST Violations

- **[8/10] T (Testable):** No numeric tolerance or success thresholds for “matches target marginals,” leaving tests subjective.  
- **[7/10] S (Small):** Story bundles two complex methods, convergence handling, integerization, and broad tests—over-scoped for one story.  
- **[6/10] E (Estimable):** Ambiguous tolerances and undefined failure behaviors make effort sizing unreliable.  
- **[3/10] I (Independent):** Relies on prior story types and the upcoming pipeline; cannot deliver standalone value.

### Acceptance Criteria Issues

- **Ambiguous:** AC1 “matches the target marginals within documented tolerances” never defines the tolerance or how to measure deviation.  
  - *Quote:* "matches the target marginals within documented tolerances."  
  - *Recommendation:* Specify numeric tolerance (e.g., max absolute deviation ≤ 1e-6 before integerization; post-integerization within ±1 row).
- **Ambiguous:** AC2 requests “lists all marginal constraints used and the convergence status” but not the fields (iterations, max deviation, tolerance, convergence boolean).  
  - *Recommendation:* Enumerate required keys: `constraints`, `iterations`, `max_deviation`, `tolerance`, `converged`.
- **Missing:** No AC covers failure modes: non-convergence, inconsistent targets, or missing strata in conditional sampling.  
  - *Recommendation:* Add ACs for explicit errors when constraints inconsistent or strata missing.
- **Missing:** Conditional sampling lacks AC for handling strata with zero donors and for auto-dropping duplicate strata columns to avoid conflicts.  
  - *Recommendation:* Add AC ensuring error on empty donor strata and defining column drop behavior.

### Hidden Risks and Dependencies

- **Dependency:** Relies on MergeMethod/Config/Assumption from Story 11.4; story not explicit about versioning compatibility.  
  - *Impact:* Implementer may diverge from established patterns.  
  - *Mitigation:* Call out reuse of Story 11.4 contracts and column-order rule.
- **Data Dependency:** Requires test fixtures with consistent marginals/strata; absence will stall test writing.  
  - *Mitigation:* Specify minimal fixture schemas and distributions in ACs.

### Estimation Reality-Check

**Assessment:** Underestimated

The story packs two algorithms (IPF + conditional), convergence logic, integerization, extensive fixtures, and multiple error pathways; likely more than one sprint for one developer.

### Technical Alignment

**Status:** Mostly aligned

- No major architecture conflicts, but failure behaviors (non-convergence, missing strata) should align with existing error hierarchy and governance manifest recording; story does not mandate this explicitly.

---

## 🚨 Critical Issues (Must Fix)

### 1. Undefined Tolerance Makes AC1 Untestable
**Impact:** Cannot verify “matches target marginals,” risking silent failures or false passes.  
**Source:** Acceptance Criteria #1  
**Problem:** Tolerance magnitude and measurement (pre/post-integerization) are unspecified.  
**Recommended Fix:** Add explicit numeric tolerance and evaluation method (e.g., max absolute deviation ≤1e-6 before rounding; post-rounding category counts within ±1 row of targets).

---

## ⚡ Enhancement Opportunities (Should Add)

### 1. Specify Assumption Payload Fields
**Benefit:** Ensures consistent governance logging and testability.  
**Source:** AC2 / Tasks 3.6, 4.4  
**Current Gap:** Which fields must be in the assumption record is unstated.  
**Suggested Addition:** Mandate keys: `constraints`, `iterations`, `max_deviation`, `tolerance`, `converged`, `expanded_rows`, `dropped_right_columns`, `strata_columns` (conditional).

### 2. Define Failure Modes
**Benefit:** Prevents silent data corruption and eases testing.  
**Source:** Tasks 3.4–3.6, 4.4  
**Current Gap:** No requirement for behavior when IPF fails to converge or when strata missing.  
**Suggested Addition:** ACs requiring `MergeConvergenceError` on non-convergence and `MergeValidationError` when any table_a stratum lacks donors.

### 3. Bound Story Scope
**Benefit:** Keeps delivery feasible.  
**Source:** Overall scope  
**Current Gap:** Two large methods plus full tests in one story.  
**Suggested Addition:** Split into IPF (11.5a) and Conditional Sampling (11.5b) or clearly limit test matrix.

---

## ✨ Optimizations (Nice to Have)

### 1. Seed Stream Separation Guidance
**Value:** Improves reproducibility and reduces accidental coupling between IPF rounding and donor selection.  
**Suggestion:** Document use of distinct RNG streams (e.g., seed, seed+1) for integerization vs donor sampling.

---

## 🤖 LLM Optimization Improvements

### 1. Trim Repetition and Surface Must-haves
**Issue:** Verbose narrative buries required fields and behaviors.  
**Token Impact:** High (saves ~15-20% tokens).  

**Current:**
```
Long paragraphs mixing pedagogy with requirements; tolerance and error behavior not singled out.
```

**Optimized:**
```
Requirements (bullets):
- Tolerance: pre-round max deviation <=1e-6; post-round counts within ±1 of targets.
- On non-convergence: raise MergeConvergenceError with iterations, max_deviation.
- Conditional sampling: error if any table_a stratum has zero donors; auto-drop strata columns from right table.
- Assumption fields: method, statement, constraints, iterations, max_deviation, tolerance, converged, seed, expanded_rows/strata_sizes, dropped_right_columns.
```

**Rationale:** Clear, scannable directives improve LLM/dev accuracy and reduce prompt length.

---

## 📝 Changes Applied

No changes were applied to the story file. This report serves as documentation only.

---

## 🏆 Competition Results

### Quality Metrics

| Metric | Score |
|--------|-------|
| Requirements Coverage | 65% |
| Architecture Alignment | 85% |
| Previous Story Integration | 70% |
| LLM Optimization Score | 60% |
| **Overall Quality Score** | **70%** |

### Disaster Prevention Assessment

- Reinvention: Mitigated by calling out reuse of MergeMethod patterns, but gaps remain.  
- Technical Spec: Medium risk—tolerance and failure behaviors missing.  
- File Structure: Low risk—paths align.  
- Regression: Medium risk—undefined failures can corrupt pipeline.  
- Implementation: High risk—untestable ACs and large scope.

### Competition Outcome

🏆 Validator identified 6 improvements that enhance the story context.

---

**Report Generated:** 2026-03-03  
**Validation Engine:** BMAD Method Quality Competition v1.0

]]></file>
</context>
<variables>
<var name="author">BMad</var>
<var name="communication_language">English</var>
<var name="date">2026-03-03</var>
<var name="description">Master synthesizes validator findings and applies changes to story file</var>
<var name="document_output_language">English</var>
<var name="epic_num">11</var>
<var name="implementation_artifacts">_bmad-output/implementation-artifacts</var>
<var name="installed_path">_bmad/bmm/workflows/4-implementation/validate-story-synthesis</var>
<var name="instructions">/Users/lucas/Workspace/bmad-assist/src/bmad_assist/workflows/validate-story-synthesis/instructions.xml</var>
<var name="name">validate-story-synthesis</var>
<var name="output_folder">_bmad-output</var>
<var name="planning_artifacts">_bmad-output/planning-artifacts</var>
<var name="project_context" file_id="b5c6fe32" load_strategy="EMBEDDED" token_approx="2024">embedded in prompt, file id: b5c6fe32</var>
<var name="project_knowledge">docs</var>
<var name="project_name">ReformLab</var>
<var name="session_id">c93145ba-837e-43c6-bbb7-6d6d5cc826d4</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_file" file_id="bca11243">embedded in prompt, file id: bca11243</var>
<var name="story_id">11.5</var>
<var name="story_key">11-5-implement-ipf-and-conditional-sampling-merge-methods</var>
<var name="story_num">5</var>
<var name="story_title">implement-ipf-and-conditional-sampling-merge-methods</var>
<var name="template">False</var>
<var name="timestamp">20260303_1903</var>
<var name="user_name">Lucas</var>
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