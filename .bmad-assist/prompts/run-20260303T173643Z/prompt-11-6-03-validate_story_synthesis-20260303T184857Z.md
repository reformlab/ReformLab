<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 11 -->
<!-- Story: 6 -->
<!-- Phase: validate-story-synthesis -->
<!-- Timestamp: 20260303T184857Z -->
<compiled-workflow>
<mission><![CDATA[

Master Synthesis: Story 11.6

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
<file id="99d0a2db" path="_bmad-output/implementation-artifacts/11-6-build-populationpipeline-builder-with-assumption-recording.md" label="STORY FILE"><![CDATA[



# Story 11.6: Build PopulationPipeline builder with assumption recording

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform developer building the French household population pipeline,
I want a composable `PopulationPipeline` builder that chains data source loaders and merge methods with full assumption recording,
so that analysts can build realistic synthetic populations from multiple institutional data sources with transparent, governance-integrated assumption tracking at every merge step, and the full chain from raw data to final population is traceable and auditable.

## Acceptance Criteria

1. Given a sequence of loaders and merge methods, when composed into a `PopulationPipeline`, then the pipeline executes each step in order and produces a final merged population as a `pa.Table`.
2. Given a pipeline execution, when completed, then every merge step's assumption record is captured in governance-compatible format via `MergeAssumption.to_governance_entry()` — the resulting dicts are directly appendable to `RunManifest.assumptions` (NOT passed to `capture_assumptions()`, which takes flat key-value pairs incompatible with structured merge assumptions).
3. Given a pipeline, when inspected after execution, then the full chain of steps is visible: which source → which method → which output, for every merge — including step index, step type, input labels, output row/column counts, method name, and duration.
4. Given a pipeline step that fails (e.g., schema mismatch between two tables), when executed, then the error identifies the exact step index, step label, step type, the two tables involved (by label), and wraps the underlying cause exception.
5. Given a population produced by the pipeline, when its governance record is queried, then all assumption records from all merge steps are retrievable as a `PipelineAssumptionChain` with per-step context (step index, step label) and a single `to_governance_entries()` call produces all entries.

## Tasks / Subtasks

- [ ] Task 1: Create `assumptions.py` — assumption recording for governance integration (AC: #2, #5)
  - [ ] 1.1 Create `src/reformlab/population/assumptions.py` with module docstring referencing Story 11.6, FR41 — explain the module bridges population pipeline merge assumptions to the governance layer's `RunManifest.assumptions` format.
  - [ ] 1.2 Implement `PipelineAssumptionRecord` frozen dataclass:
    ```python
    @dataclass(frozen=True)
    class PipelineAssumptionRecord:
        """Records a single assumption from a pipeline step with execution context.

        Attributes:
            step_index: Zero-based index of the merge step in the pipeline.
            step_label: Human-readable label for the step's output table.
            assumption: The MergeAssumption produced by the merge method.
        """
        step_index: int
        step_label: str
        assumption: MergeAssumption
    ```
    Validate in `__post_init__`: `step_index >= 0`, `step_label` is non-empty string.
  - [ ] 1.3 Implement `PipelineAssumptionChain` frozen dataclass:
    ```python
    @dataclass(frozen=True)
    class PipelineAssumptionChain:
        """Complete assumption chain from a pipeline execution.

        Collects all merge assumptions from a pipeline run and provides
        a single method to convert them to governance-compatible format
        for appending to ``RunManifest.assumptions``.

        Attributes:
            records: Ordered tuple of assumption records from each merge step.
            pipeline_description: Human-readable description of the pipeline.
        """
        records: tuple[PipelineAssumptionRecord, ...]
        pipeline_description: str = ""
    ```
    Deep-copy `records` in `__post_init__` (defensive, even though contents are frozen).
  - [ ] 1.4 Implement `PipelineAssumptionChain.to_governance_entries()`:
    ```python
    def to_governance_entries(
        self, *, source_label: str = "population_pipeline"
    ) -> list[dict[str, Any]]:
        """Convert all assumptions to governance-compatible AssumptionEntry format.

        Each entry is a dict with keys: ``key``, ``value``, ``source``, ``is_default``.
        The ``value`` dict includes pipeline step context (step_index, step_label).

        The returned list can be directly appended to ``RunManifest.assumptions``.
        Due to mypy strict mode, callers should use ``cast(AssumptionEntry, entry)``
        when appending to typed manifest fields.
        """
        entries: list[dict[str, Any]] = []
        for record in self.records:
            entry = record.assumption.to_governance_entry(
                source_label=source_label,
            )
            # Enrich with pipeline step context
            entry["value"]["pipeline_step_index"] = record.step_index
            entry["value"]["pipeline_step_label"] = record.step_label
            if self.pipeline_description:
                entry["value"]["pipeline_description"] = self.pipeline_description
            entries.append(entry)
        return entries
    ```
  - [ ] 1.5 Implement `PipelineAssumptionChain.__len__()` returning `len(self.records)` for convenience.
  - [ ] 1.6 Implement `PipelineAssumptionChain.__iter__()` returning `iter(self.records)` for iteration.

- [ ] Task 2: Create pipeline error hierarchy in `pipeline.py` (AC: #4)
  - [ ] 2.1 Define `PipelineError(Exception)` base with keyword-only `summary`, `reason`, `fix` arguments following the same pattern as `MergeError` and `DataSourceError`:
    ```python
    class PipelineError(Exception):
        """Base exception for population pipeline operations."""
        def __init__(self, *, summary: str, reason: str, fix: str) -> None:
            self.summary = summary
            self.reason = reason
            self.fix = fix
            super().__init__(f"{summary} - {reason} - {fix}")
    ```
  - [ ] 2.2 Define `PipelineConfigError(PipelineError)` — raised for invalid pipeline configuration (duplicate labels, missing references, empty pipeline).
  - [ ] 2.3 Define `PipelineExecutionError(PipelineError)` — raised when a pipeline step fails during execution. Additional attributes:
    ```python
    class PipelineExecutionError(PipelineError):
        """Raised when a pipeline step fails during execution.

        Wraps the underlying cause and adds step context so the analyst
        can identify exactly which step, which tables, and which error
        caused the failure.
        """
        def __init__(
            self,
            *,
            summary: str,
            reason: str,
            fix: str,
            step_index: int,
            step_label: str,
            step_type: str,
            cause: Exception,
            tables_involved: tuple[str, ...] = (),
        ) -> None:
            self.step_index = step_index
            self.step_label = step_label
            self.step_type = step_type
            self.cause = cause
            self.tables_involved = tables_involved
            super().__init__(summary=summary, reason=reason, fix=fix)
    ```

- [ ] Task 3: Define pipeline step types in `pipeline.py` (AC: #1, #3)
  - [ ] 3.1 Create `src/reformlab/population/pipeline.py` with module docstring referencing Story 11.6, FR40, FR41 — explain the module provides a composable builder for constructing populations from multiple institutional data sources using statistical merge methods.
  - [ ] 3.2 Implement `PipelineStepLog` frozen dataclass — records the outcome of a completed step:
    ```python
    @dataclass(frozen=True)
    class PipelineStepLog:
        """Log entry for a completed pipeline step.

        Records the outcome of each step for traceability (AC #3).

        Attributes:
            step_index: Zero-based position in execution order.
            step_type: Either ``"load"`` or ``"merge"``.
            label: Human-readable label for this step's output.
            input_labels: Empty tuple for load steps; ``(left, right)`` for merge steps.
            output_rows: Number of rows in the step's output table.
            output_columns: Column names in the step's output table.
            method_name: Merge method name (``None`` for load steps).
            duration_ms: Execution time in milliseconds.
        """
        step_index: int
        step_type: str
        label: str
        input_labels: tuple[str, ...]
        output_rows: int
        output_columns: tuple[str, ...]
        method_name: str | None
        duration_ms: float
    ```
  - [ ] 3.3 Implement `PipelineResult` frozen dataclass — immutable result of pipeline execution:
    ```python
    @dataclass(frozen=True)
    class PipelineResult:
        """Immutable result of a population pipeline execution.

        Attributes:
            table: The final merged population table.
            assumption_chain: All merge assumptions with step context.
            step_log: Ordered log of all completed steps.
        """
        table: pa.Table
        assumption_chain: PipelineAssumptionChain
        step_log: tuple[PipelineStepLog, ...]
    ```

- [ ] Task 4: Implement `PopulationPipeline` builder class (AC: #1, #3, #4)
  - [ ] 4.1 Implement `PopulationPipeline.__init__()`:
    ```python
    class PopulationPipeline:
        """Composable builder for population generation pipelines.

        Provides a fluent API for chaining data source loading and
        statistical merging operations. Each step produces a labeled
        intermediate table. The final population is the output of
        the last merge step.

        The pipeline records every merge step's assumption for
        governance integration via ``PipelineAssumptionChain``.
        """
        def __init__(self, *, description: str = "") -> None:
            self._description = description
            self._steps: list[_PipelineStepDef] = []
            self._labels: set[str] = set()
    ```
    where `_PipelineStepDef` is a union type (see 4.2).
  - [ ] 4.2 Define internal step definition types (NOT public API — prefixed with `_`):
    ```python
    @dataclass(frozen=True)
    class _LoadStepDef:
        label: str
        loader: DataSourceLoader
        config: SourceConfig

    @dataclass(frozen=True)
    class _MergeStepDef:
        label: str
        left_label: str
        right_label: str
        method: MergeMethod
        config: MergeConfig

    _PipelineStepDef = _LoadStepDef | _MergeStepDef
    ```
  - [ ] 4.3 Implement `add_source(self, label, loader, config) -> PopulationPipeline` (fluent API):
    - Validate `label` is non-empty string — raise `PipelineConfigError` if not
    - Validate `label` is unique (not in `self._labels`) — raise `PipelineConfigError` if duplicate
    - Append `_LoadStepDef` to `self._steps`
    - Add `label` to `self._labels`
    - Return `self` (fluent)
  - [ ] 4.4 Implement `add_merge(self, label, left, right, method, config) -> PopulationPipeline` (fluent API):
    - Validate `label` is non-empty string — raise `PipelineConfigError`
    - Validate `label` is unique — raise `PipelineConfigError`
    - Validate `left` exists in `self._labels` — raise `PipelineConfigError` with message identifying the missing label
    - Validate `right` exists in `self._labels` — raise `PipelineConfigError`
    - Validate `left != right` — raise `PipelineConfigError`
    - Append `_MergeStepDef` to `self._steps`
    - Add `label` to `self._labels`
    - Return `self` (fluent)
  - [ ] 4.5 Implement `execute(self) -> PipelineResult`:
    - Validate pipeline has at least one merge step — raise `PipelineConfigError` if only load steps
    - Initialize: `tables: dict[str, pa.Table] = {}`, `assumptions: list[PipelineAssumptionRecord] = []`, `step_logs: list[PipelineStepLog] = []`, `step_index = 0`
    - Iterate through `self._steps` in insertion order:
      - For `_LoadStepDef`:
        a. Record `start_time = time.monotonic()`
        b. Call `step.loader.download(step.config)` inside try/except
        c. On success: store `tables[step.label] = table`
        d. On failure: raise `PipelineExecutionError` wrapping the cause, with `step_type="load"`, `step_label=step.label`, `step_index=step_index`
        e. Record `PipelineStepLog` with `step_type="load"`, `input_labels=()`, `method_name=None`, `duration_ms`, `output_rows`, `output_columns`
        f. Increment `step_index`
      - For `_MergeStepDef`:
        a. Record `start_time`
        b. Retrieve `table_a = tables[step.left_label]` and `table_b = tables[step.right_label]`
        c. Call `step.method.merge(table_a, table_b, step.config)` inside try/except
        d. On success: store `tables[step.label] = result.table`, append `PipelineAssumptionRecord(step_index=step_index, step_label=step.label, assumption=result.assumption)` to assumptions
        e. On failure: raise `PipelineExecutionError` wrapping the cause, with `step_type="merge"`, `step_label=step.label`, `step_index=step_index`, `tables_involved=(step.left_label, step.right_label)`
        f. Record `PipelineStepLog` with `step_type="merge"`, `input_labels=(step.left_label, step.right_label)`, `method_name=step.method.name`, `duration_ms`, `output_rows`, `output_columns`
        g. Increment `step_index`
    - Determine final table: the output of the last merge step
    - Build `PipelineAssumptionChain` from collected assumptions
    - Return `PipelineResult(table=final_table, assumption_chain=chain, step_log=tuple(step_logs))`
  - [ ] 4.6 Implement `step_count` property returning `len(self._steps)`
  - [ ] 4.7 Implement `labels` property returning `frozenset(self._labels)` for inspection
  - [ ] 4.8 Use `logging.getLogger(__name__)` with structured log entries:
    - `event=pipeline_execute_start steps={n} description={desc}`
    - `event=pipeline_step_start step_index={i} step_type={type} label={label}`
    - `event=pipeline_step_complete step_index={i} label={label} rows={n} cols={n} duration_ms={d}`
    - `event=pipeline_step_error step_index={i} label={label} error={type}`
    - `event=pipeline_execute_complete total_steps={n} final_rows={n} assumptions={n} duration_ms={d}`

- [ ] Task 5: Update `__init__.py` exports (AC: all)
  - [ ] 5.1 Export from `src/reformlab/population/__init__.py`: add `PopulationPipeline`, `PipelineResult`, `PipelineStepLog`, `PipelineAssumptionChain`, `PipelineAssumptionRecord`, `PipelineError`, `PipelineConfigError`, `PipelineExecutionError` — update `__all__` listing.

- [ ] Task 6: Create test fixtures for pipeline tests (AC: all)
  - [ ] 6.1 Add to `tests/population/conftest.py`:
    - `mock_loader_a` — a minimal object satisfying `DataSourceLoader` protocol that returns a fixed `pa.Table` with columns: `household_id` (int64), `income` (float64), `region_code` (utf8) — 5 rows. Uses a `_MockLoader` class with `download()` returning the table, `status()` returning a minimal `CacheStatus`, `schema()` returning the table's schema.
    - `mock_loader_b` — returns a table with columns: `vehicle_type` (utf8), `vehicle_age` (int64), `fuel_type` (utf8) — 8 rows.
    - `mock_loader_c` — returns a table with columns: `income_bracket` (utf8), `heating_type` (utf8), `energy_kwh` (float64) — 6 rows.
    - `mock_loader_shared` — returns a table with columns: `income_bracket` (utf8), `vehicle_type` (utf8), `energy_kwh` (float64) — 12 rows. (Same as `energy_vehicle_table` from methods conftest, for conditional sampling.)
    - `mock_failing_loader` — a mock loader whose `download()` raises `DataSourceDownloadError`.
    - `mock_source_config_a`, `mock_source_config_b`, `mock_source_config_c`, `mock_source_config_shared` — `SourceConfig` instances for each mock loader.

- [ ] Task 7: Write comprehensive pipeline tests (AC: #1, #3, #4)
  - [ ] 7.1 `tests/population/test_pipeline.py`:
    - `TestPipelineStepLog`: frozen, holds all fields, `step_type` is "load" or "merge"
    - `TestPipelineResult`: frozen, holds table + assumption_chain + step_log
    - `TestPipelineErrorHierarchy`:
      - `PipelineError` inherits `Exception`, summary-reason-fix pattern
      - `PipelineConfigError` inherits `PipelineError`
      - `PipelineExecutionError` inherits `PipelineError`, has `step_index`, `step_label`, `step_type`, `cause`, `tables_involved`
    - `TestPopulationPipelineConstruction`:
      - Constructor accepts optional `description`
      - `step_count` starts at 0
      - `labels` starts empty
    - `TestPopulationPipelineAddSource`:
      - Adds source, label appears in `labels`, `step_count` increments
      - Fluent API: `add_source()` returns `self`
      - Empty label raises `PipelineConfigError`
      - Duplicate label raises `PipelineConfigError`
    - `TestPopulationPipelineAddMerge`:
      - After adding two sources, can add a merge referencing them
      - Fluent API: `add_merge()` returns `self`
      - Missing left label raises `PipelineConfigError`
      - Missing right label raises `PipelineConfigError`
      - Same left and right label raises `PipelineConfigError`
      - Empty label raises `PipelineConfigError`
      - Duplicate label raises `PipelineConfigError`
    - `TestPopulationPipelineExecuteBasic`:
      - Two sources + one uniform merge → result table has correct row count (= table_a rows) and correct columns (all from A + all from B)
      - `result.step_log` has 3 entries (2 loads + 1 merge)
      - Load step logs have `step_type="load"`, `method_name=None`, `input_labels=()`
      - Merge step log has `step_type="merge"`, `method_name="uniform"`, `input_labels=(left, right)`
      - All step logs have `output_rows > 0`, `output_columns` non-empty, `duration_ms >= 0`
    - `TestPopulationPipelineExecuteMultiMerge`:
      - Three sources + two merges (A+B→AB, AB+C→final) → result table has columns from all three sources
      - `result.step_log` has 5 entries
      - `result.assumption_chain` has 2 records (one per merge)
    - `TestPopulationPipelineExecuteWithConditionalSampling`:
      - Source A (with `income_bracket`) + source B (with `income_bracket`) → conditional merge → strata respected in output
    - `TestPopulationPipelineExecuteWithIPF`:
      - Source A (with `income_bracket`) + source B → IPF merge with marginal constraints → result marginals match within ±1
    - `TestPopulationPipelineExecuteDeterminism`:
      - Same pipeline configuration → identical result
      - Different seed in merge config → different result
    - `TestPopulationPipelineExecuteNoMerge`:
      - Pipeline with only load steps (no merges) → `PipelineConfigError` on execute
    - `TestPopulationPipelineExecuteLoadFailure`:
      - Pipeline with a failing loader → `PipelineExecutionError` with correct `step_index`, `step_label`, `step_type="load"`, wraps original exception
    - `TestPopulationPipelineExecuteMergeFailure`:
      - Pipeline with intentionally conflicting column names (no drop_right_columns) → `PipelineExecutionError` with correct `step_index`, `step_label`, `step_type="merge"`, `tables_involved` includes both labels, wraps `MergeValidationError`
    - `TestPopulationPipelineExecuteStepOrder`:
      - Steps execute in insertion order: verify via step_log indices matching insertion order
    - `TestPopulationPipelineFluentAPI`:
      - Full fluent chain: `PopulationPipeline().add_source(...).add_source(...).add_merge(...).execute()` works

- [ ] Task 8: Write comprehensive assumption tests (AC: #2, #5)
  - [ ] 8.1 `tests/population/test_assumptions.py`:
    - `TestPipelineAssumptionRecord`:
      - Frozen dataclass
      - Holds `step_index`, `step_label`, `assumption`
      - Negative `step_index` raises `ValueError`
      - Empty `step_label` raises `ValueError`
    - `TestPipelineAssumptionChain`:
      - Frozen dataclass
      - Empty records tuple is valid (no merge steps = no assumptions)
      - `len()` returns record count
      - Iterable over records
      - `pipeline_description` defaults to empty string
    - `TestPipelineAssumptionChainGovernanceEntries`:
      - Given chain with 2 records, `to_governance_entries()` returns 2 dicts
      - Each dict has `key`, `value`, `source`, `is_default` fields
      - `is_default` is `False` for all entries
      - Default `source` is `"population_pipeline"`
      - Custom `source_label` is respected
      - Each entry's `value` dict contains `pipeline_step_index` and `pipeline_step_label`
      - When `pipeline_description` is set, it appears in each entry's `value`
      - Entries are ordered by step_index
      - Each entry's `key` matches `merge_{method_name}` pattern
    - `TestPipelineAssumptionChainIntegrationWithManifest`:
      - Given governance entries from a chain, when validated against `RunManifest` assumptions schema, then all entries pass validation (key is non-empty string, value is JSON-compatible, source is non-empty string, is_default is bool)
    - `TestPipelineResultAssumptionAccess`:
      - Given a `PipelineResult`, `result.assumption_chain.records` is accessible
      - `result.assumption_chain.to_governance_entries()` works end-to-end

- [ ] Task 9: Run full test suite and lint (AC: all)
  - [ ] 9.1 `uv run pytest tests/population/test_pipeline.py tests/population/test_assumptions.py` — all new tests pass
  - [ ] 9.2 `uv run pytest tests/population/` — no regressions in loader or method tests
  - [ ] 9.3 `uv run ruff check src/reformlab/population/ tests/population/` — no lint errors
  - [ ] 9.4 `uv run mypy src/reformlab/population/` — no mypy errors (strict mode)

## Dev Notes

### Architecture Context: Pipeline Layer

This story creates the **composition layer** that connects the data source loaders (Stories 11.1–11.3) with the statistical merge methods (Stories 11.4–11.5). Two new files are added at the population module level:

```
src/reformlab/population/
├── __init__.py        ← Updated: add new exports
├── assumptions.py     ← NEW (this story) — governance bridge
├── pipeline.py        ← NEW (this story) — builder + execution
├── loaders/           ← UNCHANGED (Stories 11.1–11.3)
│   ├── base.py
│   ├── cache.py
│   ├── insee.py
│   ├── eurostat.py
│   ├── ademe.py
│   └── sdes.py
├── methods/           ← UNCHANGED (Stories 11.4–11.5)
│   ├── base.py
│   ├── uniform.py
│   ├── ipf.py
│   └── conditional.py
└── validation.py      ← NOT YET CREATED (Story 11.7)
```

### Design Pattern: Fluent Builder with Immutable Result

The pipeline follows a **builder pattern**: mutable `PopulationPipeline` accumulates steps via fluent `add_source()` / `add_merge()` calls, then `execute()` produces an immutable `PipelineResult`. This matches existing codebase patterns:

- **Orchestrator analogy:** `OrchestratorConfig.step_pipeline` is a tuple of steps built up, then executed. The pipeline builder is similar but for data composition rather than yearly simulation.
- **DatasetRegistry analogy:** `DatasetRegistry` is mutable (append-only), while `DatasetManifest` is frozen. The pipeline builder is mutable, while `PipelineResult` and `PipelineAssumptionChain` are frozen.

### Governance Integration: NOT via `capture_assumptions()`

**CRITICAL:** The governance integration uses `MergeAssumption.to_governance_entry()` which produces dicts matching the `AssumptionEntry` TypedDict format (`key`, `value`, `source`, `is_default`). These dicts are **appended directly** to `RunManifest.assumptions`.

Do **NOT** use `capture_assumptions()` from `governance/capture.py` — that function takes flat `dict[str, Any]` key-value pairs (e.g., `{"discount_rate": 0.03}`) and produces assumption entries from defaults/overrides. It is incompatible with the structured merge assumption records which have nested `value` dicts containing method details, constraints, convergence diagnostics, etc.

The bridge works as follows:
```python
# In caller code (e.g., Story 11.8 notebook or future orchestrator)
pipeline_result = pipeline.execute()
governance_entries = pipeline_result.assumption_chain.to_governance_entries()
# governance_entries is list[dict[str, Any]] matching AssumptionEntry format
# Append to RunManifest.assumptions when building the manifest
```

### Pipeline Execution Model: Sequential DAG

Steps are added in insertion order. Load steps produce labeled tables stored in an internal `dict[str, pa.Table]`. Merge steps reference previously-produced labels by name. Execution follows insertion order — the user must add sources before merge steps that reference them.

**Example pipeline:**
```python
pipeline = (
    PopulationPipeline(description="French household population 2024")
    .add_source("income", loader=insee_loader, config=insee_config)
    .add_source("vehicles", loader=sdes_loader, config=sdes_config)
    .add_merge(
        "income_vehicles",
        left="income", right="vehicles",
        method=ConditionalSamplingMethod(strata_columns=("income_bracket",)),
        config=MergeConfig(seed=42, drop_right_columns=("income_bracket",)),
    )
    .add_source("energy", loader=ademe_loader, config=ademe_config)
    .add_merge(
        "population",
        left="income_vehicles", right="energy",
        method=UniformMergeMethod(),
        config=MergeConfig(seed=43),
    )
)
result = pipeline.execute()
# result.table → final merged population (pa.Table)
# result.assumption_chain → 2 assumptions (one per merge)
# result.step_log → 5 entries (3 loads + 2 merges)
```

The output is always the table produced by the **last merge step** in insertion order. This is natural: the pipeline progressively enriches the population by merging in new sources.

### Error Handling: Step Context Preservation

When a step fails, `PipelineExecutionError` wraps the underlying exception and adds:
- `step_index` — which step failed (zero-based)
- `step_label` — the label of the failing step
- `step_type` — `"load"` or `"merge"`
- `cause` — the original exception (e.g., `MergeValidationError`, `DataSourceDownloadError`)
- `tables_involved` — tuple of label names (empty for load, `(left, right)` for merge)

This fulfills AC #4: the analyst can identify exactly what went wrong and where.

**Error propagation pattern:**
```python
try:
    merge_result = step.method.merge(table_a, table_b, step.config)
except (MergeValidationError, MergeConvergenceError, MergeError) as exc:
    raise PipelineExecutionError(
        summary=f"Pipeline step {step_index} failed",
        reason=f"Merge step {step.label!r} failed: {exc.summary}",
        fix=exc.fix,
        step_index=step_index,
        step_label=step.label,
        step_type="merge",
        cause=exc,
        tables_involved=(step.left_label, step.right_label),
    ) from exc
```

For load step failures:
```python
try:
    table = step.loader.download(step.config)
except Exception as exc:
    raise PipelineExecutionError(
        summary=f"Pipeline step {step_index} failed",
        reason=f"Load step {step.label!r} failed: {exc}",
        fix="Check data source availability, cache status, and network connectivity",
        step_index=step_index,
        step_label=step.label,
        step_type="load",
        cause=exc,
    ) from exc
```

### Internal Step Definition Types

The builder uses private frozen dataclasses to store step definitions:

```python
@dataclass(frozen=True)
class _LoadStepDef:
    """Internal: describes a pending load step."""
    label: str
    loader: DataSourceLoader
    config: SourceConfig

@dataclass(frozen=True)
class _MergeStepDef:
    """Internal: describes a pending merge step."""
    label: str
    left_label: str
    right_label: str
    method: MergeMethod
    config: MergeConfig

_PipelineStepDef = _LoadStepDef | _MergeStepDef
```

These are NOT part of the public API. The public API consists of:
- `PopulationPipeline` (builder)
- `PipelineResult` (execution result)
- `PipelineStepLog` (step record)
- `PipelineAssumptionChain` (assumption collection)
- `PipelineAssumptionRecord` (single assumption with context)
- `PipelineError`, `PipelineConfigError`, `PipelineExecutionError` (errors)

### Timing Measurement

Use `time.monotonic()` for step duration measurement (not `time.time()` which is affected by system clock adjustments):

```python
import time

start = time.monotonic()
# ... step execution ...
duration_ms = (time.monotonic() - start) * 1000.0
```

### No New Dependencies Required

All implementation uses existing dependencies and stdlib:

- `time` — monotonic clock for duration measurement (stdlib)
- `dataclasses` — frozen dataclasses (stdlib)
- `logging` — structured logging (stdlib)
- `pyarrow` — `pa.Table` (existing dependency)

Import patterns:
- `pyarrow` imported at runtime in `pipeline.py` (same as merge methods)
- `pyarrow` under `TYPE_CHECKING` guard in `assumptions.py` (only used in `PipelineResult` type, which is in `pipeline.py`)
- Actually, `assumptions.py` doesn't need pyarrow at all — it only references `MergeAssumption` from `methods/base.py`

### Test Fixtures: Mock Loaders

Tests must NOT use real data source loaders (no network, no cache). Instead, use mock loaders that satisfy the `DataSourceLoader` protocol:

```python
class _MockLoader:
    """Minimal DataSourceLoader for pipeline testing."""

    def __init__(self, table: pa.Table) -> None:
        self._table = table

    def download(self, config: SourceConfig) -> pa.Table:
        return self._table

    def status(self, config: SourceConfig) -> CacheStatus:
        return CacheStatus(
            cached=True,
            path=None,
            downloaded_at=None,
            hash=None,
            stale=False,
        )

    def schema(self) -> pa.Schema:
        return self._table.schema


class _FailingLoader:
    """Mock loader that always raises on download."""

    def download(self, config: SourceConfig) -> pa.Table:
        raise DataSourceDownloadError(
            summary="Download failed",
            reason="mock failure for testing",
            fix="this is a test mock",
        )

    def status(self, config: SourceConfig) -> CacheStatus:
        return CacheStatus(
            cached=False, path=None, downloaded_at=None, hash=None, stale=False,
        )

    def schema(self) -> pa.Schema:
        return pa.schema([])
```

### AssumptionEntry Validation Compatibility

The `RunManifest._validate()` method (in `governance/manifest.py`) validates each assumption entry for:
- `key`: non-empty string
- `value`: JSON-compatible (str, int, float, bool, None, list, dict — validated recursively)
- `source`: non-empty string
- `is_default`: boolean

The `to_governance_entries()` output must satisfy all these constraints. The existing `MergeAssumption.to_governance_entry()` already produces valid entries. The pipeline enrichment (adding `pipeline_step_index` and `pipeline_step_label` to the `value` dict) uses `int` and `str` — both JSON-compatible.

### Downstream Dependencies

Story 11.6 is consumed by:

- **Story 11.7** (Validation) — validates a population produced by the pipeline against known marginals. May receive a `PipelineResult.table` and check distributions.
- **Story 11.8** (Notebook) — demonstrates the full pipeline end-to-end: load real INSEE/SDES/ADEME data, compose with merge methods, show assumption chain, produce French household population. Uses `PipelineAssumptionChain.to_governance_entries()` for manifest integration.

### Project Structure Notes

**New files (4):**
- `src/reformlab/population/pipeline.py`
- `src/reformlab/population/assumptions.py`
- `tests/population/test_pipeline.py`
- `tests/population/test_assumptions.py`

**Modified files (2):**
- `src/reformlab/population/__init__.py` — add new exports, update `__all__`
- `tests/population/conftest.py` — add mock loader fixtures and source configs

**No changes** to `pyproject.toml` (no new dependencies)

### Alignment with Project Conventions

All rules from `project-context.md` apply:

- Every file starts with `from __future__ import annotations`
- `if TYPE_CHECKING:` guards for annotation-only imports (in `assumptions.py` — no runtime pyarrow needed)
- Frozen dataclasses as default (`@dataclass(frozen=True)`) for all value types: `PipelineStepLog`, `PipelineResult`, `PipelineAssumptionRecord`, `PipelineAssumptionChain`, `_LoadStepDef`, `_MergeStepDef`
- `PopulationPipeline` is a mutable builder class — NOT a frozen dataclass (it accumulates steps)
- Protocols, not ABCs — pipeline accepts any `DataSourceLoader` and `MergeMethod` via duck typing
- Subsystem-specific exceptions (`PipelineError` hierarchy, not bare `Exception`)
- `dict[str, Any]` for metadata bags
- `tuple[...]` for immutable sequences (step_log, records, output_columns)
- `X | None` union syntax
- Module-level docstrings referencing story/FR
- `logging.getLogger(__name__)` with structured key=value format
- `# ====...====` section separators for major sections within longer modules

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#New-Subsystem-Population-Generation] — Directory structure, pipeline.py and assumptions.py placement
- [Source: _bmad-output/planning-artifacts/epics.md#BKL-1106] — Story definition and acceptance criteria
- [Source: _bmad-output/planning-artifacts/prd.md#FR40] — "System produces a complete synthetic population with household-level attributes sufficient for policy simulation"
- [Source: _bmad-output/planning-artifacts/prd.md#FR41] — "Every merge, imputation, and extrapolation is recorded as an explicit assumption in the governance layer"
- [Source: _bmad-output/project-context.md#Python-Language-Rules] — Frozen dataclasses, Protocols, `from __future__ import annotations`
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules] — PyArrow canonical data type, no pandas in core logic
- [Source: src/reformlab/population/methods/base.py] — MergeMethod protocol, MergeConfig, MergeAssumption, MergeResult
- [Source: src/reformlab/population/methods/base.py#to_governance_entry] — Governance bridge pattern (key/value/source/is_default)
- [Source: src/reformlab/population/loaders/base.py] — DataSourceLoader protocol, SourceConfig, CacheStatus, CachedLoader
- [Source: src/reformlab/governance/capture.py] — `capture_assumptions()` API (flat key-value, NOT for structured merge assumptions)
- [Source: src/reformlab/governance/manifest.py#AssumptionEntry] — TypedDict with key/value/source/is_default; JSON-compatibility validation
- [Source: src/reformlab/governance/manifest.py#RunManifest] — Frozen dataclass, assumptions field validation in `_validate()`
- [Source: src/reformlab/population/methods/uniform.py] — Reference merge method implementation (validation order, logging, assumption construction)
- [Source: src/reformlab/population/methods/errors.py] — MergeError hierarchy (summary-reason-fix pattern)
- [Source: src/reformlab/population/loaders/errors.py] — DataSourceError hierarchy (same pattern)
- [Source: src/reformlab/data/pipeline.py] — DatasetManifest/DatasetRegistry pattern (frozen metadata + mutable registry)
- [Source: _bmad-output/implementation-artifacts/11-5-implement-ipf-and-conditional-sampling-merge-methods.md] — Previous story (merge method patterns, test patterns)
- [Source: _bmad-output/implementation-artifacts/11-4-define-mergemethod-protocol-and-uniform-distribution-method.md] — Protocol reference, antipattern about capture_assumptions() mismatch

## File List

**New files (4):**
- `src/reformlab/population/pipeline.py`
- `src/reformlab/population/assumptions.py`
- `tests/population/test_pipeline.py`
- `tests/population/test_assumptions.py`

**Modified files (2):**
- `src/reformlab/population/__init__.py` — add new exports
- `tests/population/conftest.py` — add mock loader fixtures

## Change Log

- 2026-03-03: Story created by create-story workflow — comprehensive developer context with composable builder pattern design, fluent API specification, governance integration via `to_governance_entry()` (NOT `capture_assumptions()`), error hierarchy with step context preservation, mock loader test fixtures, sequential DAG execution model, timing measurement, and downstream dependency mapping.


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
IPFMergeMethod : class
    Iterative Proportional Fitting reweighting and matching.
IPFConstraint : dataclass
    A marginal constraint for IPF.
IPFResult : dataclass
    Convergence diagnostics from an IPF run.
ConditionalSamplingMethod : class
    Stratum-based conditional sampling merge.
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
    IPFConstraint,
    IPFResult,
    MergeAssumption,
    MergeConfig,
    MergeMethod,
    MergeResult,
)
from reformlab.population.methods.conditional import ConditionalSamplingMethod
from reformlab.population.methods.errors import (
    MergeConvergenceError,
    MergeError,
    MergeValidationError,
)
from reformlab.population.methods.ipf import IPFMergeMethod
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
    "ConditionalSamplingMethod",
    "IPFConstraint",
    "IPFMergeMethod",
    "IPFResult",
    "MergeAssumption",
    "MergeConfig",
    "MergeConvergenceError",
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
<file id="a830e2e0" path="tests/population/conftest.py" label="SOURCE CODE"><![CDATA[

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.population.loaders.base import SourceConfig


@pytest.fixture()
def sample_source_config() -> SourceConfig:
    """A minimal SourceConfig for testing."""
    return SourceConfig(
        provider="insee",
        dataset_id="household_income",
        url="https://example.com/dataset.csv",
        params={"year": "2024"},
        description="INSEE household income data",
    )


@pytest.fixture()
def sample_table() -> pa.Table:
    """A small PyArrow table for cache round-trip testing."""
    return pa.table(
        {
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "income": pa.array([25000.0, 35000.0, 50000.0], type=pa.float64()),
            "decile": pa.array([2, 5, 8], type=pa.int32()),
        }
    )


@pytest.fixture()
def sample_schema() -> pa.Schema:
    """Schema matching sample_table."""
    return pa.schema(
        [
            pa.field("household_id", pa.int64()),
            pa.field("income", pa.float64()),
            pa.field("decile", pa.int32()),
        ]
    )


]]></file>
<file id="1d910d88" path="[Validator A]" label="VALIDATION OUTPUT"><![CDATA[

# 🎯 Story Context Validation Report

**Story:** 11-6-build-populationpipeline-builder-with-assumption-recording - build-populationpipeline-builder-with-assumption-recording  
**Story File:** 99d0a2db  
**Validated:** 2026-03-03  
**Validator:** Quality Competition Engine

---

## Executive Summary

### Issues Overview

| Category | Found | Applied |
|----------|-------|---------|
| 🚨 Critical Issues | 0 | 0 |
| ⚡ Enhancements | 3 | 0 |
| ✨ Optimizations | 2 | 0 |
| 🤖 LLM Optimizations | 2 | 0 |

**Overall Assessment:** Pass with moderate improvements recommended

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🟠 IMPORTANT | Story size spans many concerns; risky for single sprint | INVEST-S | +1 |
| 🟠 IMPORTANT | Over-prescriptive implementation leaves limited flexibility | INVEST-N | +1 |
| 🟡 MINOR | Hidden dependency on governance manifest schema not surfaced in AC | Dependencies | +0.3 |
| 🟡 MINOR | Missing edge-case AC for empty/degenerate pipeline outputs | AC coverage | +0.3 |
| 🟡 MINOR | Verbose story text could hinder LLM efficiency | LLM optimization | +0.3 |
| 🟢 CLEAN PASS | 4 |  | -2.0 |

### Evidence Score: 0.9

| Score | Verdict |
|-------|---------|
| **0.9** | **PASS** |

---

## 🎯 Ruthless Story Validation 11.6

### INVEST Criteria Assessment

| Criterion | Status | Severity | Details |
|-----------|--------|----------|---------|
| **I**ndependent | ❌ | 4/10 | Relies on loaders/methods from Stories 11.1–11.5 and governance manifest; not self-contained. |
| **N**egotiable | ⚠️ | 5/10 | Highly prescriptive (exact classes, fields, logging keys), reducing design flexibility. |
| **V**aluable | ✅ | 1/10 | Clear value: auditable population pipeline with assumption recording. |
| **E**stimable | ⚠️ | 3/10 | Scope clear but broad; multiple modules/tests make estimation harder though possible. |
| **S**mall | ❌ | 6/10 | Large multi-file implementation plus extensive tests; likely exceeds a small story. |
| **T**estable | ⚠️ | 3/10 | ACs testable but miss edge cases (empty outputs, duplicate labels, circular refs). |

### INVEST Violations

- **[4/10] Independent:** Hidden reliance on prior stories’ loaders/methods and governance manifest not stated as prerequisites.
- **[5/10] Negotiable:** Story dictates concrete class shapes and logging/event names, limiting implementation choices.
- **[6/10] Small:** Work spans new pipeline core, assumption bridge, error hierarchy, fixtures, and broad tests—large for one sprint.

### Acceptance Criteria Issues

- **Missing Edge Case:** ACs omit behavior when merges yield zero rows or when all steps are loads and no merge executes.  
  - *Quote:* "Given a pipeline execution, when completed, then every merge step's assumption record..."  
  - *Recommendation:* Add AC covering empty/degenerate pipelines and zero-row results.
- **Ambiguity:** AC3 asks for "full chain... visible" but does not specify output format or access method (e.g., API vs. object property).  
  - *Recommendation:* Clarify how step log is exposed (attribute, method) and required fields ordering.
- **Untestable Detail:** AC2 forbids `capture_assumptions()` but does not state failure behavior if caller uses it.  
  - *Recommendation:* Specify validation or error if incompatible capture path is used.

### Hidden Risks and Dependencies

- **Governance Schema Dependency:** Assumes `RunManifest.assumptions` accepts produced dicts; breaking changes there would break pipeline.  
  - *Impact:* Runtime failures or governance inconsistency.  
  - *Mitigation:* Add compatibility check or version reference in story/ACs.
- **Upstream Story Dependency:** Requires MergeMethod implementations (Stories 11.4/11.5) and DataSourceLoader infrastructure (Stories 11.1–11.3).  
  - *Impact:* Blocked if upstream stories slip.  
  - *Mitigation:* Mark as dependent or provide mocks/interfaces for parallel work.

### Estimation Reality-Check

**Assessment:** Underestimated

Scope covers two new modules, error hierarchy, builder, assumption bridge, plus comprehensive tests and fixtures. Comparable earlier stories (11.3–11.5) were sizable; bundling all here likely exceeds a single sprint for one developer.

### Technical Alignment

**Status:** Mostly aligned

- Uses pipeline/assumption layering consistent with architecture Phase 2.
- No conflicts found with adapter isolation or PyArrow rules.

---

## 🚨 Critical Issues (Must Fix)

✅ No critical issues found - the original story covered essential requirements.

---

## ⚡ Enhancement Opportunities (Should Add)

### 1. Explicit AC for zero-merge / zero-row outcomes
**Benefit:** Prevents silent success with empty populations.  
**Source:** AC set

**Current Gap:** No behavior defined when merges drop all rows or when pipeline has loads but no merges.  
**Suggested Addition:** Add AC requiring `PipelineExecutionError` (or specific status) when final table would be empty or when no merge steps exist.

### 2. Declare governance manifest contract version
**Benefit:** Protects against schema drift.  
**Source:** Dependencies

**Current Gap:** Story assumes `RunManifest.assumptions` shape without stating version.  
**Suggested Addition:** Note manifest schema version/date and require validation against it.

### 3. Clarify step-log access and ordering
**Benefit:** Ensures developers expose logs consistently.  
**Source:** AC3 ambiguity

**Current Gap:** AC3 does not specify whether logs are returned via `PipelineResult.step_log`, ordering guarantees, or sort keys.  
**Suggested Addition:** State log is an ordered tuple preserving execution order, accessible via `PipelineResult.step_log`.

---

## ✨ Optimizations (Nice to Have)

### 1. Determinism across multiple merges
**Value:** Easier reproducibility.  
**Suggestion:** Reserve per-merge seed streams (e.g., base seed + step index) and document in story.

### 2. Performance guardrails
**Value:** Avoid slow pipelines on large tables.  
**Suggestion:** Add optional row/column limit checks or timing thresholds in step logs.

---

## 🤖 LLM Optimization Improvements

### 1. Trim repetitive module/file lists
**Issue:** Verbosity  
**Token Impact:** High

**Current:**
```
Extensive repeated listings of files and tasks within tasks.
```

**Optimized:**
```
Summarize file additions once and reference by module (assumptions.py, pipeline.py, tests).
```

**Rationale:** Reduces token load while retaining actionable guidance.

### 2. Condense algorithm prose into bullets
**Issue:** Long narrative for pipeline execution steps  
**Token Impact:** Medium

**Current:**
```
Multi-paragraph explanation of execution loop and error handling.
```

**Optimized:**
```
- Execute steps in insertion order: load -> merge
- On failure: wrap in PipelineExecutionError with step_index, label, type, cause
- Record step_log (rows, cols, duration, method)
```

**Rationale:** Keeps key rules scannable for the dev agent.

---

## 📝 Changes Applied

No changes were applied to the story file. This report serves as documentation only.

---

## 🏆 Competition Results

### Quality Metrics

| Metric | Score |
|--------|-------|
| Requirements Coverage | 82% |
| Architecture Alignment | 90% |
| Previous Story Integration | 78% |
| LLM Optimization Score | 60% |
| **Overall Quality Score** | **78%** |

### Disaster Prevention Assessment

- **Reinvention Risks:** Mitigated with existing loader/method reuse noted.
- **Technical Specs:** Minor gaps; no critical conflicts.
- **File Structure:** Aligned with population/ directory plan.
- **Regression Risks:** Moderate—edge cases not AC-covered.
- **Implementation Risks:** Underestimation and over-prescription flagged.

### Competition Outcome

🏆 **Validator identified 7 improvements** that enhance the story context.

---

**Report Generated:** 2026-03-03  
**Validation Engine:** BMAD Method Quality Competition v1.0

]]></file>
<file id="557aedd2" path="[Validator B]" label="VALIDATION OUTPUT"><![CDATA[

# 🎯 Story Context Validation Report

**Story:** 11-6-build-populationpipeline-builder-with-assumption-recording
**Story File:** `_bmad-output/implementation-artifacts/11-6-build-populationpipeline-builder-with-assumption-recording.md`
**Validated:** 2026-03-03
**Validator:** Quality Competition Engine

---

## Executive Summary

| Category | Found | Applied |
|----------|-------|---------|
| 🚨 Critical Issues | 2 | 0 (read-only validator) |
| ⚡ Enhancements | 5 | 0 |
| ✨ Optimizations | 2 | 0 |
| 🤖 LLM Optimizations | 2 | 0 |

**Overall Assessment:** The story is well-structured and draws on solid prior-story foundations. However, two issues could cause an incorrect implementation: the ambiguous "final table" determination algorithm in `execute()`, and the placement of the error hierarchy inside `pipeline.py` (against the established subsystem convention). Several secondary gaps exist around test setup guidance and key uniqueness in assumption records.

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🔴 CRITICAL | `execute()` final-table determination is ambiguous — load steps after last merge produce incorrect behavior | Task 4.5, Dev Notes | +3 |
| 🟠 IMPORTANT | `PipelineError` hierarchy placed in `pipeline.py` violates loaders/methods errors.py convention | Task 2, File List | +1 |
| 🟠 IMPORTANT | `TestPipelineAssumptionChainIntegrationWithManifest` requires `RunManifest` construction — no guidance given | Task 8.1 | +1 |
| 🟠 IMPORTANT | Non-unique assumption keys for multiple same-method merge steps not addressed | Task 1.4, AC #5 | +1 |
| 🟠 IMPORTANT | `mock_source_config_a/b/c/shared` fixtures underspecified — required fields unstated | Task 6 | +1 |
| 🟡 MINOR | Deep-copy of `PipelineAssumptionChain.records` (frozen objects) is unnecessary and sets bad precedent | Task 1.3 | +0.3 |
| 🟡 MINOR | `execute()` type-narrowing pattern for `_PipelineStepDef` union not mentioned for mypy strict | Task 4.5 | +0.3 |
| 🟢 CLEAN PASS | INVEST: Independent (no unreleased dependencies) | — | -0.5 |
| 🟢 CLEAN PASS | INVEST: Valuable (clear FR40/FR41 integration) | — | -0.5 |
| 🟢 CLEAN PASS | INVEST: Estimable (well-defined scope) | — | -0.5 |
| 🟢 CLEAN PASS | INVEST: Small (appropriate 2-file scope) | — | -0.5 |
| 🟢 CLEAN PASS | Acceptance Criteria (5 clear, testable ACs) | — | -0.5 |

### Evidence Score: **6.1**

| Score | Verdict |
|-------|---------|
| **6.1** | **MAJOR REWORK** |

---

## 🎯 Ruthless Story Validation 11.6

### INVEST Criteria Assessment

| Criterion | Status | Severity | Details |
|-----------|--------|----------|---------|
| **I**ndependent | ✅ Pass | 1/10 | Stories 11.1–11.5 are fully complete (dev-complete/complete). No unreleased dependencies. |
| **N**egotiable | ⚠️ Minor | 2/10 | Fluent API and frozen dataclass patterns are prescribed, but these follow established codebase conventions, not gold-plating. Acceptable. |
| **V**aluable | ✅ Pass | 1/10 | Clearly implements FR40 (synthetic population) and FR41 (assumption transparency). Bridges loaders and methods. |
| **E**stimable | ✅ Pass | 2/10 | Scope is clear: 2 new source files, 2 new test files, conftest additions. Medium complexity. |
| **S**mall | ✅ Pass | 2/10 | Two new source files (~200–300 lines each). Reasonable sprint scope. |
| **T**estable | ✅ Pass | 1/10 | 5 ACs are specific. Test tasks cover all acceptance criteria. Edge cases (empty strata, load failure, merge failure) are specified. |

### INVEST Violations

No significant INVEST violations detected.

### Acceptance Criteria Issues

- **Ambiguous:** AC #5 says "all assumption records from all merge steps are retrievable as a `PipelineAssumptionChain`". It doesn't specify what happens when the pipeline has ZERO merge steps (only loads). The story's `execute()` raises `PipelineConfigError` in this case, so the chain never exists. This edge case is handled in tests but not mentioned in the AC.
  - *Quote:* "Given a population produced by the pipeline, when its governance record is queried..."
  - *Recommendation:* Add a note that AC #5 only applies when at least one merge step exists (the no-merge case is covered by AC #4's error path).

### Hidden Risks and Dependencies

- **Dependency type: Cross-subsystem import pattern** — `pipeline.py` must import from `loaders/base.py` (`DataSourceLoader`, `SourceConfig`, `CacheStatus`) and `methods/base.py` (`MergeMethod`, `MergeConfig`, `MergeResult`, `MergeAssumption`). These are well-established but the story doesn't enumerate the import list explicitly. A developer unfamiliar with the codebase may struggle to identify all needed imports.
  - *Impact:* Minor delay. Not blocking.
  - *Mitigation:* The story's references section lists all relevant source files. Developer can cross-reference.

- **Dependency type: `pa.ChunkedArray` vs `pa.Array` in column access** — `table.column(name)` returns `pa.ChunkedArray`. When building `pa.table(all_columns)` with a dict of `ChunkedArray` values, this works in pyarrow. But the story's `uniform.py` already uses `pa.ChunkedArray` for `all_columns: dict[str, pa.ChunkedArray]` (line 182). Pipeline's `execute()` doesn't store intermediate column data so this isn't an issue—but it's worth noting the type.

### Estimation Reality-Check

**Assessment:** Realistic

The story's scope (2 files, ~300 lines each, 9 tasks) is appropriate for a single sprint day. The methods are well-specified. The main complexity risk is in `execute()` (finding the final table label correctly) and `PipelineAssumptionChain.to_governance_entries()` (mutation pattern). Both are manageable.

### Technical Alignment

**Status:** Mostly Aligned — one deviation found

- **Deviation:** `PipelineError` hierarchy is embedded in `pipeline.py` instead of a separate `errors.py`. The established pattern in `population/loaders/errors.py` and `population/methods/errors.py` puts errors in dedicated files.
  - *Architecture Reference:* `project-context.md` § "Subsystem-specific exceptions — each module defines its own error hierarchy"
  - *Recommendation:* Create `src/reformlab/population/errors.py` for `PipelineError`, `PipelineConfigError`, `PipelineExecutionError` — OR explicitly state the deviation is intentional (e.g., because the pipeline subsystem is a single-file module).

---

## 🚨 Critical Issues (Must Fix)

### 1. `execute()` Final-Table Determination Algorithm Is Ambiguous

**Impact:** Incorrect implementation — the developer could implement `tables[self._steps[-1].label]` (last step's table) instead of `tables[last_merge_step.label]` (last merge step's table), producing wrong behavior when load steps follow the last merge.

**Source:** Task 4.5, Dev Notes § "Pipeline Execution Model: Sequential DAG"

**Problem:**

The `execute()` spec says "Determine final table: the output of the last merge step" but the pseudo-code iterates steps in order and doesn't show how to identify the final merge step's label after the loop. The builder allows adding load sources at any point, including after merges:

```python
pipeline = (
    PopulationPipeline()
    .add_source("income", ...)
    .add_source("vehicles", ...)
    .add_merge("merged", left="income", right="vehicles", ...)
    .add_source("reference_data", ...)  # valid! added for future use or annotation
)
```

In this case, `self._steps[-1]` is a `_LoadStepDef` with label `"reference_data"`. If the developer does `return tables[self._steps[-1].label]`, they return the reference table, not the merged population.

**Recommended Fix:**

Explicitly state the final-table algorithm in Task 4.5:

```python
# After the iteration loop, find the last merge step's output label
last_merge_label: str | None = None
for step in self._steps:
    if isinstance(step, _MergeStepDef):
        last_merge_label = step.label
# last_merge_label is guaranteed non-None because we validated at least one merge step
assert last_merge_label is not None
final_table = tables[last_merge_label]
```

Also add a test case: `TestPopulationPipelineExecuteLoadAfterMerge` — pipeline with a load step added after the last merge — verifies the final table is still the last merge output, not the post-merge load.

---

### 2. `TestPipelineAssumptionChainIntegrationWithManifest` Has No Setup Guidance

**Impact:** Developer writes an incomplete or incorrect test — either skipping the full manifest construction (making the test pointless) or spending significant time figuring out `RunManifest`'s mandatory fields.

**Source:** Task 8.1 test `TestPipelineAssumptionChainIntegrationWithManifest`

**Problem:**

The test is specified as: "when validated against `RunManifest` assumptions schema, then all entries pass validation". Constructing a `RunManifest` that actually validates the entries requires 6 mandatory fields (`manifest_id`, `created_at`, `engine_version`, `openfisca_version`, `adapter_version`, `scenario_version`) that are unrelated to the pipeline. The `RunManifest` validation code calls `_validate_json_compatible()` recursively on each assumption's `value`. Without the full manifest construction, the test only partially validates the entries.

Additionally, `RunManifest.assumptions` is typed as `list[AssumptionEntry]` (a TypedDict). The return type of `to_governance_entries()` is `list[dict[str, Any]]`. Appending to a manifest requires `cast(AssumptionEntry, entry)` for mypy strict, as noted in the story, but the test needs to do this too.

**Recommended Fix:**

Add to Task 8's conftest (or the test file directly) a helper function:

```python
def _make_test_manifest(assumptions: list[dict[str, Any]]) -> RunManifest:
    """Build a minimal RunManifest with given assumptions for validation testing."""
    from typing import cast
    from reformlab.governance.manifest import AssumptionEntry
    return RunManifest(
        manifest_id="test-pipeline-001",
        created_at="2026-01-01T00:00:00Z",
        engine_version="0.1.0",
        openfisca_version="44.0.0",
        adapter_version="1.0.0",
        scenario_version="v1",
        assumptions=[cast(AssumptionEntry, e) for e in assumptions],
    )
```

Note: `tests/governance/conftest.py` has a `minimal_manifest` fixture the developer can look at for reference.

---

## ⚡ Enhancement Opportunities (Should Add)

### 3. Error Hierarchy Convention Deviation Not Documented

**Benefit:** Prevents developer confusion and inconsistent code review feedback.

**Source:** Task 2, File List

**Current Gap:** The project's established convention (`loaders/errors.py`, `methods/errors.py`) puts errors in dedicated files per subsystem. The story places `PipelineError`, `PipelineConfigError`, and `PipelineExecutionError` inside `pipeline.py` with no explanation. The story's File List has no `population/errors.py`.

**Suggested Addition:**

Either:
1. Add `src/reformlab/population/errors.py` to the File List containing the error hierarchy (recommended — follows convention)
2. Add an explicit note in Dev Notes: "Pipeline errors live in `pipeline.py` rather than a separate `errors.py` because the population subsystem at module level is a single-file pipeline — unlike `loaders/` and `methods/` which are multi-file subpackages."

---

### 4. Non-Unique Assumption Keys When the Same Method Is Used Multiple Times

**Benefit:** Prevents downstream analysis bugs; governance consumers may expect unique keys.

**Source:** Task 1.4 `PipelineAssumptionChain.to_governance_entries()`, AC #5

**Current Gap:**

`MergeAssumption.to_governance_entry()` produces `"key": f"merge_{self.method_name}"`. A pipeline with two uniform merges produces:
- Step 0: `{"key": "merge_uniform", "value": {..., "pipeline_step_index": 0, ...}}`
- Step 2: `{"key": "merge_uniform", "value": {..., "pipeline_step_index": 2, ...}}`

Both entries have `key="merge_uniform"`. While `RunManifest` validation does not enforce key uniqueness, downstream consumers (analytics, diff tools) may be confused.

**Suggested Addition:**

Add to the `to_governance_entries()` spec: "Note: The `key` field is `merge_{method_name}` inherited from `MergeAssumption.to_governance_entry()`. When the same method is used multiple times, multiple entries will share the same `key` — this is intentional and accepted by `RunManifest` validation. Downstream consumers should use `pipeline_step_index` to distinguish entries."

Alternatively (stronger fix): Override the key in `to_governance_entries()` to produce `f"merge_{record.assumption.method_name}_step_{record.step_index}"` for uniqueness.

---

### 5. `mock_source_config_a/b/c/shared` Fixtures Are Underspecified

**Benefit:** Prevents developer from guessing required `SourceConfig` fields, saving time.

**Source:** Task 6

**Current Gap:**

Task 6 lists `mock_source_config_a`, `mock_source_config_b`, `mock_source_config_c`, `mock_source_config_shared` but gives no example. `SourceConfig` requires `provider`, `dataset_id`, and `url` (non-empty strings). Developers unfamiliar with the codebase won't know what values to use.

**Suggested Addition:**

```python
@pytest.fixture()
def mock_source_config_a() -> SourceConfig:
    return SourceConfig(
        provider="mock", dataset_id="income", url="mock://income"
    )
```

(And similarly for b, c, shared.)

---

### 6. Catch Clause for Load Step Failures Should Enumerate Expected Exception Types

**Benefit:** Prevents accidental suppression of `SystemExit`/`KeyboardInterrupt` in long-running pipelines.

**Source:** Task 4.5 `execute()` load step error handling

**Current Gap:**

The story's Dev Notes show `except Exception as exc:` for load failures. This catches everything including `KeyboardInterrupt` (which inherits from `BaseException` in Python, so actually not caught — this is fine). But it catches `StopIteration`, `RuntimeError`, `MemoryError`, etc. which would be silently wrapped in `PipelineExecutionError`.

**Suggested Addition:**

Specify: "Catch `(DataSourceError, DataSourceDownloadError, DataSourceOfflineError, DataSourceValidationError, OSError)` for load step failures. Use `except Exception` only as a fallback catch-all, documented intentionally."

---

### 7. Missing Test: Load Step Added After Last Merge

**Benefit:** Validates the critical "final table" determination algorithm.

**Source:** Task 7.1 `TestPopulationPipelineExecuteStepOrder`

**Current Gap:**

No test verifies the case where a load step is added after the last merge (see Critical Issue #1). This is the exact scenario that could produce a wrong implementation.

**Suggested Addition:**

```python
class TestPopulationPipelineExecuteLoadAfterMerge:
    """Verify final table is last merge output, not last step output."""
    def test_load_after_merge_returns_merge_output(...):
        pipeline = (
            PopulationPipeline()
            .add_source("a", mock_loader_a, mock_source_config_a)
            .add_source("b", mock_loader_b, mock_source_config_b)
            .add_merge("merged", "a", "b", UniformMergeMethod(), MergeConfig(seed=42))
            .add_source("extra", mock_loader_c, mock_source_config_c)
        )
        result = pipeline.execute()
        # Final table should be "merged", not "extra"
        assert result.table.num_columns == <a_cols + b_cols>
```

---

## ✨ Optimizations (Nice to Have)

### 8. Deep-Copy of Frozen Records Tuple Is Unnecessary

**Value:** Avoids misleading precedent; frozen objects don't need defensive deep-copying.

**Suggestion:**

In Task 1.3, `PipelineAssumptionChain.__post_init__` is specified to deep-copy `records`. Since `records` is `tuple[PipelineAssumptionRecord, ...]` and both `PipelineAssumptionRecord` and `MergeAssumption` are frozen dataclasses (with `MergeAssumption.details` already deep-copied in its own `__post_init__`), deep-copying is redundant. Replace with a shallow tuple copy: `object.__setattr__(self, "records", tuple(self.records))` — or omit the `__post_init__` copy entirely for `records` (the tuple is immutable).

---

### 9. `execute()` Requires `isinstance()` Type-Narrowing for mypy Strict

**Value:** Prevents mypy strict failures; developer needs this pattern explicitly.

**Suggestion:**

Add to Task 4.5 Dev Notes: "In `execute()`, iterate steps and narrow type via `isinstance()` — required for mypy strict: `if isinstance(step, _LoadStepDef): ...` / `elif isinstance(step, _MergeStepDef): ...`. Without this narrowing, mypy will complain that `step.loader` (or `step.method`) may not exist on the union type."

---

## 🤖 LLM Optimization Improvements

### 10. Redundant Specification of `_LoadStepDef` / `_MergeStepDef`

**Issue:** Duplication
**Token Impact:** ~80 tokens wasted

**Current:** `_LoadStepDef`, `_MergeStepDef`, `_PipelineStepDef` are specified in full in Task 4.2 AND again in the Dev Notes § "Internal Step Definition Types".

**Optimized:** Remove the Dev Notes section (or collapse to a one-line cross-reference: "See Task 4.2 for internal step types"). The task spec is authoritative; the Notes repeat it verbatim.

**Rationale:** Dev Notes should add insight, not duplicate task specs.

---

### 11. `execute()` Pseudo-Code Is Verbose but Buries the Critical Detail

**Issue:** Critical information buried in verbose specification
**Token Impact:** High density, low signal-to-noise on the final table determination

**Current:** The `execute()` pseudo-code in Task 4.5 is ~25 bullet points long. The critical algorithm for determining the final table is in the last bullet ("Determine final table: the output of the last merge step") — a single vague sentence after a wall of detail.

**Optimized:** Promote the final-table algorithm to a separate, explicitly-named sub-task:

```
- [ ] 4.9 Implement final table selection: scan `self._steps` to find the last
  `_MergeStepDef` in insertion order. Return `tables[last_merge_step.label]`.
  Do NOT use `self._steps[-1].label` — load steps may follow the last merge.
```

**Rationale:** Moves the most implementation-error-prone detail to prominence.

---

## 📝 Changes Applied

No changes were applied to the story file. This report serves as documentation only (read-only validator role).

---

## 🏆 Competition Results

### Quality Metrics

| Metric | Score |
|--------|-------|
| Requirements Coverage | 92% |
| Architecture Alignment | 85% |
| Previous Story Integration | 95% |
| LLM Optimization Score | 80% |
| **Overall Quality Score** | **88%** |

### Disaster Prevention Assessment

- **Wheel Reinvention:** ✅ No risks — story correctly references all existing components (loaders, methods, governance)
- **Wrong Libraries:** ✅ Clean — only stdlib + pyarrow used as specified
- **File Structure:** ⚠️ Deviation — error classes in `pipeline.py` instead of `errors.py`
- **Regressions:** ✅ Clean — no modifications to Stories 11.1–11.5 code
- **Vague Implementations:** ⚠️ One ambiguity — final table algorithm in `execute()`
- **Completion Lies:** ✅ Clean — tests cover all ACs with specific, verifiable checks
- **Missing UX Context:** ✅ N/A — library layer, no UX implications

### Competition Outcome

🏆 **Validator identified 11 improvements** that enhance the story context. The original create-story produced high-quality output with thorough Dev Notes and good test coverage. The two critical gaps (final-table ambiguity, missing RunManifest construction pattern) are real implementation risks that could produce incorrect code or broken tests.

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
<var name="session_id">77fb599e-6ba2-4437-be33-8c1d11971f8a</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_file" file_id="99d0a2db">embedded in prompt, file id: 99d0a2db</var>
<var name="story_id">11.6</var>
<var name="story_key">11-6-build-populationpipeline-builder-with-assumption-recording</var>
<var name="story_num">6</var>
<var name="story_title">build-populationpipeline-builder-with-assumption-recording</var>
<var name="template">False</var>
<var name="timestamp">20260303_1948</var>
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