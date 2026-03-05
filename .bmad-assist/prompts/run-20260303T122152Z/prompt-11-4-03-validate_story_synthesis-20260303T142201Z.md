<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 11 -->
<!-- Story: 4 -->
<!-- Phase: validate-story-synthesis -->
<!-- Timestamp: 20260303T142201Z -->
<compiled-workflow>
<mission><![CDATA[

Master Synthesis: Story 11.4

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
<file id="6870c5a9" path="_bmad-output/implementation-artifacts/11-4-define-mergemethod-protocol-and-uniform-distribution-method.md" label="STORY FILE"><![CDATA[


# Story 11.4: Define MergeMethod protocol and implement uniform distribution method

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform developer building the French household population pipeline,
I want a `MergeMethod` protocol defining the interface for statistical dataset fusion and a concrete `UniformMergeMethod` implementation that randomly matches rows between two tables,
so that downstream stories (11.5 IPF/conditional sampling, 11.6 pipeline builder) have a proven protocol pattern to follow, and the simplest merge method is available as a baseline for population construction.

## Acceptance Criteria

1. Given the `MergeMethod` protocol, when a new method is implemented, then it must accept two `pa.Table` inputs plus a config, and return a merged table plus an assumption record.
2. Given two tables with no shared sample, when merged using uniform distribution, then each row from Table A is matched with a randomly drawn row from Table B with equal probability.
3. Given a uniform merge, when the assumption record is inspected, then it states: "Each household in source A is matched to a household in source B with uniform probability — this assumes no correlation between the variables in the two sources."
4. Given the uniform method docstring, when read, then it includes a plain-language explanation of the independence assumption and when this is appropriate vs. problematic.

## Tasks / Subtasks

- [ ] Task 1: Create `src/reformlab/population/methods/` directory structure (AC: #1)
  - [ ] 1.1 Create `src/reformlab/population/methods/__init__.py` with module docstring referencing Story 11.4, FR38, FR39
  - [ ] 1.2 Create `src/reformlab/population/methods/errors.py` with `MergeError` base exception and `MergeValidationError` — follow the `summary - reason - fix` pattern from `DataSourceError` in `population/loaders/errors.py`

- [ ] Task 2: Define `MergeMethod` protocol and supporting types — `base.py` (AC: #1, #3)
  - [ ] 2.1 Create `src/reformlab/population/methods/base.py` with module docstring referencing Story 11.4, FR38
  - [ ] 2.2 Define `MergeConfig` frozen dataclass with fields: `seed: int`, `description: str = ""`, `drop_right_columns: tuple[str, ...] = ()` — validate in `__post_init__` that `seed` is a non-negative integer
  - [ ] 2.3 Define `MergeAssumption` frozen dataclass with fields: `method_name: str`, `statement: str`, `details: dict[str, Any]` — include `to_governance_entry(*, source_label: str = "merge_step") -> dict[str, Any]` method that produces a dict compatible with `governance.manifest.AssumptionEntry` (keys: `key`, `value`, `source`, `is_default`)
  - [ ] 2.4 Define `MergeResult` frozen dataclass with fields: `table: pa.Table`, `assumption: MergeAssumption`
  - [ ] 2.5 Define `MergeMethod` as `@runtime_checkable` Protocol with two required members:
    - `def merge(self, table_a: pa.Table, table_b: pa.Table, config: MergeConfig) -> MergeResult`
    - `name: str` property (read-only)
  - [ ] 2.6 Validate design: `MergeConfig.__post_init__` deep-copies `drop_right_columns` to prevent aliasing (use `object.__setattr__` pattern from `SourceConfig`)
  - [ ] 2.7 Validate design: `MergeAssumption.details` deep-copied in `__post_init__` to prevent mutation

- [ ] Task 3: Implement `UniformMergeMethod` — `uniform.py` (AC: #2, #3, #4)
  - [ ] 3.1 Create `src/reformlab/population/methods/uniform.py` with module docstring referencing Story 11.4, FR38, FR39 — include the pedagogical docstring explaining the independence assumption in plain language (when appropriate: independent surveys; when problematic: correlated variables)
  - [ ] 3.2 Implement `UniformMergeMethod` class with `__init__(self)` (no constructor parameters — uniform has no method-specific config)
  - [ ] 3.3 Implement `name` property returning `"uniform"`
  - [ ] 3.4 Implement `merge(self, table_a, table_b, config)` with this logic:
    1. Validate inputs: both tables must have `num_rows > 0`; raise `MergeValidationError` if empty
    2. Apply `config.drop_right_columns`: remove listed columns from table_b before merge; raise `MergeValidationError` if a column in `drop_right_columns` does not exist in table_b
    3. Check column name conflicts: `set(table_a.schema.names) & set(remaining_b.schema.names)` — raise `MergeValidationError` with exact overlapping names if any
    4. Generate random indices: `random.Random(config.seed)`, generate `table_a.num_rows` random integers in `[0, remaining_b.num_rows)` — this is random matching with replacement (each row from B can be matched to multiple rows from A)
    5. Select matched rows: `remaining_b.take(pa.array(indices))` — efficient vectorized row selection
    6. Combine columns: build merged table by combining all columns from table_a and matched table_b columns
    7. Build `MergeAssumption` with:
       - `method_name="uniform"`
       - `statement="Each household in source A is matched to a household in source B with uniform probability — this assumes no correlation between the variables in the two sources."`
       - `details={"table_a_rows": n, "table_b_rows": m, "seed": config.seed, "with_replacement": True, "dropped_right_columns": list(config.drop_right_columns)}`
    8. Return `MergeResult(table=merged, assumption=assumption)`
  - [ ] 3.5 Use `logging.getLogger(__name__)` with structured `event=merge_start`, `event=merge_complete` log entries including `method=uniform rows_a=... rows_b=... seed=...`

- [ ] Task 4: Update `__init__.py` exports (AC: #1)
  - [ ] 4.1 Export from `src/reformlab/population/methods/__init__.py`: `MergeMethod`, `MergeConfig`, `MergeAssumption`, `MergeResult`, `UniformMergeMethod`, `MergeError`, `MergeValidationError`
  - [ ] 4.2 Add methods exports to `src/reformlab/population/__init__.py`: same names as 4.1

- [ ] Task 5: Create test infrastructure (AC: all)
  - [ ] 5.1 Create `tests/population/methods/__init__.py`
  - [ ] 5.2 Create `tests/population/methods/conftest.py` with fixtures:
    - `income_table` — small `pa.Table` with columns: `household_id` (int64), `income` (float64), `region_code` (utf8) — 5 rows
    - `vehicle_table` — small `pa.Table` with columns: `vehicle_type` (utf8), `vehicle_age` (int64), `fuel_type` (utf8) — 8 rows
    - `overlapping_table` — small `pa.Table` with a column name that conflicts with `income_table` (e.g., `region_code`)
    - `empty_table` — `pa.Table` with schema but 0 rows
    - `default_config` — `MergeConfig(seed=42)`

- [ ] Task 6: Write comprehensive tests (AC: all)
  - [ ] 6.1 `tests/population/methods/test_base.py`:
    - `TestMergeConfig`: frozen, `__post_init__` validation (negative seed raises `ValueError`), `drop_right_columns` deep-copied, default values
    - `TestMergeAssumption`: frozen, `details` deep-copied, `to_governance_entry()` returns correct dict with `key`/`value`/`source`/`is_default` fields
    - `TestMergeResult`: frozen, holds table + assumption
    - `TestMergeMethodProtocol`: verify `UniformMergeMethod` passes `isinstance(m, MergeMethod)` check; verify a non-conforming class fails
  - [ ] 6.2 `tests/population/methods/test_uniform.py`:
    - `TestUniformMergeMethodProtocol`: `isinstance()` check against `MergeMethod`
    - `TestUniformMergeMethodName`: `name` property returns `"uniform"`
    - `TestUniformMergeMethodMerge`:
      - Basic merge: income_table (5 rows) + vehicle_table (8 rows) → merged table with 5 rows and 6 columns (3 from A + 3 from B)
      - Column names: merged table has all columns from both tables
      - Row count: merged table has same row count as table_a
      - Values preserved: all values from table_a are present unchanged in corresponding columns
      - Values from table_b: matched values come from actual rows in table_b (not fabricated)
    - `TestUniformMergeMethodDeterminism`:
      - Same seed → identical merged table (row-by-row comparison)
      - Different seed → different row matching (at least one row differs, verified statistically with high probability for the test fixture sizes)
    - `TestUniformMergeMethodColumnConflict`:
      - Overlapping column names → `MergeValidationError` with exact conflicting names in message
    - `TestUniformMergeMethodDropRightColumns`:
      - `drop_right_columns=("region_code",)` removes `region_code` from right table before merge
      - Invalid `drop_right_columns` with nonexistent column → `MergeValidationError`
    - `TestUniformMergeMethodEmptyTable`:
      - Empty table_a → `MergeValidationError`
      - Empty table_b → `MergeValidationError`
    - `TestUniformMergeMethodAssumption`:
      - `assumption.method_name == "uniform"`
      - `assumption.statement` contains the exact AC #3 text
      - `assumption.details` contains `table_a_rows`, `table_b_rows`, `seed`, `with_replacement`
      - `assumption.to_governance_entry()` returns dict with `key`, `value`, `source`, `is_default` fields
    - `TestUniformMergeMethodWithReplacement`:
      - When table_a has more rows than table_b, merge still works (with replacement)
      - When table_a has fewer rows than table_b, merge still works
      - When table_a and table_b have equal rows, merge still works
    - `TestUniformMergeMethodDocstring`:
      - Class docstring is non-empty
      - Class docstring contains "independence" or "no correlation" (pedagogical content)
  - [ ] 6.3 `tests/population/methods/test_errors.py`:
    - `TestMergeError`: inherits `Exception`, `summary-reason-fix` message format, attributes accessible
    - `TestMergeValidationError`: inherits `MergeError`

- [ ] Task 7: Run full test suite and lint (AC: all)
  - [ ] 7.1 `uv run pytest tests/population/methods/` — all new tests pass
  - [ ] 7.2 `uv run pytest tests/population/` — no regressions in loader tests
  - [ ] 7.3 `uv run ruff check src/reformlab/population/methods/ tests/population/methods/` — no lint errors
  - [ ] 7.4 `uv run mypy src/reformlab/population/methods/` — no mypy errors (strict mode)

## Dev Notes

### Architecture Context: Statistical Methods Library

This story creates the `src/reformlab/population/methods/` subsystem — the second major component of EPIC-11 (after `loaders/`). The architecture specifies this directory explicitly:

```
src/reformlab/population/
├── loaders/           ← Institutional data source loaders (Stories 11.1–11.3, DONE)
│   ├── base.py        ← DataSourceLoader protocol + CachedLoader
│   ├── cache.py       ← SourceCache
│   ├── errors.py      ← DataSourceError hierarchy
│   ├── insee.py       ← INSEELoader
│   ├── eurostat.py    ← EurostatLoader
│   ├── ademe.py       ← ADEMELoader
│   └── sdes.py        ← SDESLoader
├── methods/           ← Statistical fusion methods library (THIS STORY starts it)
│   ├── __init__.py
│   ├── base.py        ← MergeMethod protocol + MergeConfig + MergeAssumption + MergeResult
│   ├── errors.py      ← MergeError hierarchy
│   └── uniform.py     ← UniformMergeMethod (this story)
│                      ← ipf.py, conditional.py, matching.py added in Story 11.5
├── pipeline.py        ← PopulationPipeline builder (Story 11.6)
├── assumptions.py     ← Assumption recording integration (Story 11.6)
└── validation.py      ← Validate against known marginals (Story 11.7)
```

### Protocol Design Pattern (from DataSourceLoader)

Follow the **exact same protocol pattern** established in `src/reformlab/population/loaders/base.py`:

1. **`@runtime_checkable` Protocol** — enables `isinstance()` checks for structural typing
2. **Frozen dataclasses** for all value objects (`MergeConfig`, `MergeAssumption`, `MergeResult`)
3. **`__post_init__` validation** — validate and deep-copy mutable fields using `object.__setattr__()` pattern
4. **No abstract base classes** — Protocols, not ABCs (per project-context.md)
5. **Subsystem-specific exceptions** — `MergeError` hierarchy, not bare `ValueError` or `Exception`

### MergeMethod Protocol — Exact Specification

```python
from typing import Protocol, runtime_checkable

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
        """Short identifier for this method (e.g., "uniform", "ipf")."""
        ...

    def merge(
        self,
        table_a: pa.Table,
        table_b: pa.Table,
        config: MergeConfig,
    ) -> MergeResult:
        """Merge two tables using this method's statistical approach."""
        ...
```

### MergeConfig — Exact Specification

```python
@dataclass(frozen=True)
class MergeConfig:
    """Immutable configuration for a merge operation.

    Attributes:
        seed: Random seed for deterministic merge operations. Must be >= 0.
        description: Optional human-readable description for governance.
        drop_right_columns: Column names to remove from table_b before
            merging. Use this to remove shared key columns (e.g.,
            "region_code") that exist in both tables but should only
            appear once in the result.
    """

    seed: int
    description: str = ""
    drop_right_columns: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.seed, int) or self.seed < 0:
            raise ValueError(
                f"seed must be a non-negative integer, got {self.seed!r}"
            )
        # Deep-copy mutable-origin field
        object.__setattr__(
            self, "drop_right_columns", tuple(self.drop_right_columns)
        )
```

### MergeAssumption — Governance Integration

The `MergeAssumption` must produce records compatible with the existing `governance.manifest.AssumptionEntry` TypedDict (defined in `src/reformlab/governance/manifest.py` lines 60–73):

```python
class AssumptionEntry(TypedDict):
    key: str           # assumption identifier
    value: Any         # JSON-compatible value
    source: str        # e.g., "merge_step", "runtime"
    is_default: bool   # always False for merge assumptions (explicit choice)
```

The `to_governance_entry()` method on `MergeAssumption` bridges the gap:

```python
@dataclass(frozen=True)
class MergeAssumption:
    """Structured assumption record from a merge operation.

    Records the method name, a plain-language assumption statement,
    and method-specific details. Can be converted to governance
    ``AssumptionEntry`` format via ``to_governance_entry()``.
    """

    method_name: str
    statement: str
    details: dict[str, Any]

    def __post_init__(self) -> None:
        from copy import deepcopy
        object.__setattr__(self, "details", deepcopy(self.details))

    def to_governance_entry(
        self, *, source_label: str = "merge_step"
    ) -> dict[str, Any]:
        """Convert to governance-compatible assumption entry.

        Returns a dict matching ``governance.manifest.AssumptionEntry``
        structure: key, value, source, is_default.
        """
        return {
            "key": f"merge_{self.method_name}",
            "value": {
                "method": self.method_name,
                "statement": self.statement,
                **self.details,
            },
            "source": source_label,
            "is_default": False,
        }
```

**CRITICAL:** The `value` field in the governance entry must be JSON-compatible. The `details` dict must only contain JSON-serializable types (`str`, `int`, `float`, `bool`, `None`, `list`, `dict`). The manifest validation in `RunManifest._validate()` (manifest.py lines 230–265) enforces this. Specifically, `_validate_json_compatible()` (lines 523–552) rejects non-finite floats, bytes, and custom objects.

### UniformMergeMethod — Algorithm Detail

The uniform distribution merge is the simplest statistical matching approach:

**Algorithm:**
1. For each of the N rows in table_a, independently draw a random index from `[0, M)` where M = `table_b.num_rows`
2. Select the corresponding rows from table_b (with replacement — a single row from B can be matched to multiple rows from A)
3. Concatenate columns from table_a and the selected table_b rows

**Statistical assumption:** Independence between all variables in table_a and table_b. This means the merge assumes no correlation between, for example, income (from INSEE) and vehicle type (from SDES). This is the weakest assumption — good as a baseline but unrealistic for correlated variables.

**When appropriate:** When merging genuinely independent surveys or when no linking variable is available.
**When problematic:** When variables are correlated (e.g., income and vehicle ownership are correlated — higher-income households are more likely to own newer, more expensive vehicles).

**Implementation pattern:**

```python
import random
import pyarrow as pa

def merge(self, table_a: pa.Table, table_b: pa.Table, config: MergeConfig) -> MergeResult:
    # Validate inputs
    if table_a.num_rows == 0:
        raise MergeValidationError(...)
    if table_b.num_rows == 0:
        raise MergeValidationError(...)

    # Drop specified right columns
    right_table = table_b
    for col in config.drop_right_columns:
        if col not in right_table.schema.names:
            raise MergeValidationError(...)
        col_idx = right_table.schema.get_field_index(col)
        right_table = right_table.remove_column(col_idx)

    # Check column conflicts
    overlap = set(table_a.schema.names) & set(right_table.schema.names)
    if overlap:
        raise MergeValidationError(...)

    # Random matching
    rng = random.Random(config.seed)
    n = table_a.num_rows
    m = right_table.num_rows
    indices = pa.array([rng.randrange(m) for _ in range(n)])
    matched_b = right_table.take(indices)

    # Combine columns
    all_columns: dict[str, pa.Array] = {}
    for name in table_a.schema.names:
        all_columns[name] = table_a.column(name)
    for name in matched_b.schema.names:
        all_columns[name] = matched_b.column(name)
    merged = pa.table(all_columns)

    # Build assumption
    assumption = MergeAssumption(
        method_name="uniform",
        statement=(
            "Each household in source A is matched to a household in "
            "source B with uniform probability \u2014 this assumes no "
            "correlation between the variables in the two sources."
        ),
        details={
            "table_a_rows": n,
            "table_b_rows": m,
            "seed": config.seed,
            "with_replacement": True,
            "dropped_right_columns": list(config.drop_right_columns),
        },
    )

    return MergeResult(table=merged, assumption=assumption)
```

### Error Hierarchy — Follow Loaders Pattern

```python
# src/reformlab/population/methods/errors.py

class MergeError(Exception):
    """Base exception for merge method operations.

    All merge exceptions use keyword-only constructor arguments
    and produce a structured ``summary - reason - fix`` message.
    """

    def __init__(self, *, summary: str, reason: str, fix: str) -> None:
        self.summary = summary
        self.reason = reason
        self.fix = fix
        super().__init__(f"{summary} - {reason} - {fix}")


class MergeValidationError(MergeError):
    """Raised when merge inputs fail validation.

    Triggered by: empty tables, column name conflicts, invalid
    drop_right_columns, or schema mismatches.
    """
```

### No New Dependencies Required

All implementation uses existing dependencies and stdlib:

- `random` — deterministic random number generation (stdlib)
- `pyarrow` — table operations, `take()` for row selection (existing dependency)
- `copy.deepcopy` — immutability for frozen dataclasses (stdlib)
- `logging` — structured logging (stdlib)

Do **not** introduce `numpy`, `scipy`, `pandas`, or any new dependency.

### Test Fixtures — Concrete Data

```python
# tests/population/methods/conftest.py

@pytest.fixture()
def income_table() -> pa.Table:
    """INSEE-style income table (5 households)."""
    return pa.table({
        "household_id": pa.array([1, 2, 3, 4, 5], type=pa.int64()),
        "income": pa.array([18000.0, 25000.0, 32000.0, 45000.0, 72000.0], type=pa.float64()),
        "region_code": pa.array(["84", "11", "84", "75", "11"], type=pa.utf8()),
    })

@pytest.fixture()
def vehicle_table() -> pa.Table:
    """SDES-style vehicle table (8 vehicles)."""
    return pa.table({
        "vehicle_type": pa.array(
            ["diesel", "essence", "ev", "diesel", "hybrid", "essence", "ev", "diesel"],
            type=pa.utf8(),
        ),
        "vehicle_age": pa.array([3, 7, 1, 12, 2, 9, 0, 15], type=pa.int64()),
        "fuel_type": pa.array(
            ["diesel", "petrol", "electric", "diesel", "hybrid", "petrol", "electric", "diesel"],
            type=pa.utf8(),
        ),
    })

@pytest.fixture()
def overlapping_table() -> pa.Table:
    """Table with column name conflicting with income_table."""
    return pa.table({
        "region_code": pa.array(["84", "11", "75"], type=pa.utf8()),
        "heating_type": pa.array(["gas", "electric", "heat_pump"], type=pa.utf8()),
    })

@pytest.fixture()
def empty_table() -> pa.Table:
    """Table with schema but zero rows."""
    return pa.table({
        "x": pa.array([], type=pa.int64()),
        "y": pa.array([], type=pa.float64()),
    })

@pytest.fixture()
def default_config() -> MergeConfig:
    """Default merge config with seed 42."""
    return MergeConfig(seed=42)
```

### Test Pattern to Follow (from loader tests)

Follow the exact test structure from `tests/population/loaders/test_insee.py`:

1. **Class-based grouping** by feature/responsibility — each test class covers a specific aspect
2. **AC references in class docstrings** — e.g., `"""AC #1, #2: Protocol compliance."""`
3. **Direct assertions** — `assert` statements, `pytest.raises(ExceptionClass, match=...)` for errors
4. **Fixtures via conftest** — injected by parameter name
5. **No test helpers** unless genuinely reusable — keep tests self-contained
6. **Frozen dataclass tests** — verify immutability with `pytest.raises(AttributeError)`

### Downstream Dependencies

Story 11.4 is consumed by:

- **Story 11.5** (IPF + conditional sampling) — adds `IPFMergeMethod` and `ConditionalSamplingMethod` implementing the same `MergeMethod` protocol, using the same `MergeConfig`, `MergeAssumption`, and `MergeResult` types
- **Story 11.6** (PopulationPipeline) — composes loaders + methods, calls `merge()` in sequence, collects `MergeAssumption` records, passes them to `governance.capture.capture_assumptions()`
- **Story 11.7** (Validation) — validates merged population against marginals
- **Story 11.8** (Notebook) — demonstrates merge methods with plain-language explanations

### Project Structure Notes

**New files (6):**
- `src/reformlab/population/methods/__init__.py`
- `src/reformlab/population/methods/base.py`
- `src/reformlab/population/methods/errors.py`
- `src/reformlab/population/methods/uniform.py`
- `tests/population/methods/__init__.py`
- `tests/population/methods/conftest.py`
- `tests/population/methods/test_base.py`
- `tests/population/methods/test_uniform.py`
- `tests/population/methods/test_errors.py`

**Modified files (2):**
- `src/reformlab/population/__init__.py` — add methods exports
- (no other files modified)

**No changes** to `pyproject.toml` (no new dependencies, no new markers needed)

### Alignment with Project Conventions

All rules from `project-context.md` apply:

- Every file starts with `from __future__ import annotations`
- `if TYPE_CHECKING:` guards for annotation-only imports
- Frozen dataclasses as default (`@dataclass(frozen=True)`)
- Protocols, not ABCs — `@runtime_checkable` Protocol
- Subsystem-specific exceptions (`MergeError`, not `ValueError`)
- `dict[str, Any]` for metadata bags with stable string-constant keys
- `tuple[...]` for immutable sequences in function parameters and return types
- `X | None` union syntax, not `Optional[X]`
- Module-level docstrings referencing story/FR
- `logging.getLogger(__name__)` with structured key=value format
- `# ====...====` section separators for major sections within longer modules

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#New-Subsystem-Population-Generation] — Directory structure, MergeMethod protocol specification
- [Source: _bmad-output/planning-artifacts/architecture.md#External-Data-Caching-&-Offline-Strategy] — Design principles for population subsystem
- [Source: _bmad-output/planning-artifacts/epics.md#BKL-1104] — Story definition and acceptance criteria
- [Source: _bmad-output/planning-artifacts/prd.md#FR38] — "System provides a library of statistical methods for merging datasets that do not share the same sample (uniform distribution, IPF, conditional sampling, statistical matching)"
- [Source: _bmad-output/planning-artifacts/prd.md#FR39] — "Analyst can choose which merge method to apply at each dataset join, with plain-language explanation of the assumption"
- [Source: _bmad-output/project-context.md#Python-Language-Rules] — Frozen dataclasses, Protocols, `from __future__ import annotations`
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules] — PyArrow canonical data type, no pandas in core logic
- [Source: src/reformlab/population/loaders/base.py] — DataSourceLoader Protocol pattern to follow (SourceConfig, CacheStatus frozen dataclasses, `@runtime_checkable`)
- [Source: src/reformlab/population/loaders/errors.py] — DataSourceError hierarchy pattern (summary-reason-fix)
- [Source: src/reformlab/governance/capture.py] — `capture_assumptions()` function signature and AssumptionEntry format
- [Source: src/reformlab/governance/manifest.py#AssumptionEntry] — TypedDict with key/value/source/is_default fields; JSON-compatibility validation
- [Source: tests/population/loaders/test_insee.py] — Test patterns: class-based grouping, fixture injection, direct assertions
- [Source: _bmad-output/implementation-artifacts/11-3-implement-eurostat-ademe-sdes-data-source-loaders.md] — Previous story (loaders pattern reference)

## Change Log

- 2026-03-03: Story created by create-story workflow — comprehensive developer context with MergeMethod protocol design, UniformMergeMethod algorithm, governance integration pattern, error hierarchy, test fixture designs, and downstream dependency mapping.


]]></file>
<file id="1d910d88" path="[Validator A]" label="VALIDATION OUTPUT"><![CDATA[

# 🎯 Story Context Validation Report

**Story:** 11-4-define-mergemethod-protocol-and-uniform-distribution-method
**Story File:** `_bmad-output/implementation-artifacts/11-4-define-mergemethod-protocol-and-uniform-distribution-method.md`
**Validated:** 2026-03-03
**Validator:** Quality Competition Engine

---

## Executive Summary

| Category | Found | Applied |
|----------|-------|---------|
| 🚨 Critical Issues | 1 | 0 (read-only) |
| ⚡ Enhancements | 5 | 0 (read-only) |
| ✨ Optimizations | 3 | 0 (read-only) |
| 🤖 LLM Optimizations | 2 | 0 (read-only) |

**Overall Assessment:** The story has strong bones — clear algorithm specification, detailed task breakdown, good test coverage, and solid governance integration design. However, it contains one factual API error that will actively mislead Story 11.6's developer, plus several important pattern gaps that conflict with the established codebase.

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🔴 CRITICAL | `capture_assumptions()` API mismatch in Downstream Dependencies section | Dev Notes §Downstream Dependencies | +3 |
| 🟠 IMPORTANT | `bool` not rejected in `MergeConfig.seed` validation — inconsistent with `manifest.py` pattern | Dev Notes §MergeConfig | +1 |
| 🟠 IMPORTANT | File count mismatch: "New files (6)" lists 9; "Modified files (2)" lists 1 | Dev Notes §Project Structure | +1 |
| 🟠 IMPORTANT | Local `from copy import deepcopy` inside `__post_init__` violates top-level import convention | Dev Notes §MergeAssumption | +1 |
| 🟠 IMPORTANT | `**self.details` key collision risk in `to_governance_entry()` could silently override "method"/"statement" | Dev Notes §MergeAssumption | +1 |
| 🟠 IMPORTANT | `methods/__init__.py` `__all__` not specified — inconsistent with `population/__init__.py` pattern | Dev Notes §Project Structure | +1 |
| 🟡 MINOR | `MergeAssumption.method_name` and `statement` lack non-empty validation | Tasks §2.3 | +0.3 |
| 🟡 MINOR | Merged table column ordering (A-first then B) not explicitly documented as a contract | Dev Notes §Algorithm | +0.3 |
| 🟡 MINOR | No test verifying `event=merge_start`/`event=merge_complete` log emission | Tasks §6.2 | +0.3 |
| 🟢 CLEAN PASS | INVEST Independent — 8 categories with no issues | — | -4.0 |

### Evidence Score: **4.9**

| Score | Verdict |
|-------|---------|
| **4.9** | **MAJOR REWORK** |

---

## 🎯 Ruthless Story Validation 11.4

### INVEST Criteria Assessment

| Criterion | Status | Severity | Details |
|-----------|--------|----------|---------|
| **I**ndependent | ✅ Pass | 0/10 | Can be developed fully independently. Stories 11.1–11.3 are done (Status: dev-complete). No blocking dependencies. |
| **N**egotiable | ✅ Pass | 1/10 | Some implementation detail is prescriptive (exact algorithm, exact assumption statement text), but this is appropriate given AC #3 requires verbatim text. |
| **V**aluable | ✅ Pass | 0/10 | Delivers the foundational merge protocol needed by Stories 11.5–11.8. Clear architectural value. |
| **E**stimable | ✅ Pass | 0/10 | 5 SP estimate is reasonable. Task breakdown is exhaustive and maps cleanly to implementation work. |
| **S**mall | ✅ Pass | 0/10 | Well-scoped — protocol + one implementation + tests. Appropriately sized for one sprint. |
| **T**estable | ✅ Pass | 1/10 | Acceptance criteria are specific and testable. Test matrix is detailed. Minor gap: AC #2 "equal probability" is asserted indirectly through determinism tests rather than a direct probability distribution test. |

### INVEST Violations

No significant INVEST violations detected.

### Acceptance Criteria Issues

- **AC #3 — Statement not byte-identical in implementation hint**: The AC states: `"…with uniform probability — this assumes no correlation…"` using a typographic em-dash (`—`). The `uniform.py` implementation hint in Dev Notes uses `\u2014` (correct Unicode em-dash). However, `MergeConfig` uses `description: str` (a different field). A developer might use a standard ASCII dash if they copy from the AC text in the story header, missing the unicode escape. The test `TestUniformMergeMethodAssumption` should `match=` the exact string with Unicode em-dash.

### Hidden Risks and Dependencies

- **Dependency type: API contract**: The `governance.manifest.AssumptionEntry` `_validate_json_compatible()` check (manifest.py:523–552) validates the `value` field of every assumption entry. The `to_governance_entry()` method merges `self.details` into the `value` dict via `**self.details`. If any future `MergeMethod` puts a non-JSON-serializable value in `details` (e.g., a `pa.Schema` or a `Path`), `RunManifest` construction will raise `ManifestValidationError`. Story 11.4 does not document this constraint on `MergeMethod` implementors.

- **Dependency type: `pa.Table.take()` index array type**: `pa.array([rng.randrange(m) for _ in range(n)])` will produce an `int64` array by default. `take()` accepts both `int32` and `int64`. This is fine, but with large tables (>2B rows, theoretical), `int32` would overflow. The story's restriction to laptop-scale populations makes this academic.

### Estimation Reality-Check

**Assessment:** Realistic. 5 SP is appropriate. The protocol design mirrors `DataSourceLoader` exactly, reducing design uncertainty. The test matrix (30+ test cases) is well-specified.

### Technical Alignment

**Status:** Mostly aligned. One critical misalignment identified (governance API).

---

## 🚨 Critical Issues (Must Fix)

### 1. `governance.capture.capture_assumptions()` API Is Incompatible with `MergeAssumption` Output

**Impact:** Story 11.6's developer will call the wrong function or build incorrect integration code. The stated integration path does not exist.

**Source:** Dev Notes §Downstream Dependencies and §MergeAssumption — Governance Integration

**Problem:**

The story states in §Downstream Dependencies:

> Story 11.6 (PopulationPipeline) — composes loaders + methods, calls `merge()` in sequence, collects `MergeAssumption` records, **passes them to `governance.capture.capture_assumptions()`**

The actual `capture_assumptions()` function signature in `src/reformlab/governance/capture.py:19–24` is:

```python
def capture_assumptions(
    *,
    defaults: dict[str, Any] | None = None,
    overrides: dict[str, Any] | None = None,
    source_label: str = "runtime",
) -> list[dict[str, Any]]:
```

This function takes two flat `dict[str, Any]` mappings of scalar assumption keys to values (e.g., `{"discount_rate": 0.03}`). It does **not** accept pre-formed `AssumptionEntry`-shaped dicts or a list of merge assumptions. It produces `AssumptionEntry` dicts from key-value pairs — the opposite direction.

**The correct integration path for Story 11.6** is to call `merge_assumption.to_governance_entry()` and append the result **directly to `RunManifest.assumptions`**:

```python
# Correct:
entries = [ma.to_governance_entry() for ma in merge_assumptions]
# Then pass entries to RunManifest(assumptions=entries + other_entries, ...)

# WRONG (as stated in story):
capture_assumptions(...)  # cannot accept MergeAssumption objects
```

**Recommended Fix:**

Replace the Downstream Dependencies description:

> ~~passes them to `governance.capture.capture_assumptions()`~~

With:

> Story 11.6 (PopulationPipeline) — collects `MergeAssumption` records, calls `assumption.to_governance_entry()` on each, and appends the resulting dicts directly to `RunManifest.assumptions` (type: `list[AssumptionEntry]`). Does NOT use `governance.capture.capture_assumptions()` — that function is for scalar key-value parameter assumptions, not structured merge assumption records.

---

## ⚡ Enhancement Opportunities (Should Add)

### 1. `bool` Not Rejected in `MergeConfig.seed` Validation

**Benefit:** Prevents semantically invalid seeds (`MergeConfig(seed=True)`) that pass isinstance checks due to Python's `bool ⊂ int` inheritance.

**Source:** Dev Notes §MergeConfig — Exact Specification; compare `manifest.py:219`

**Current Gap:**

The story specifies:
```python
if not isinstance(self.seed, int) or self.seed < 0:
    raise ValueError(...)
```

In Python, `isinstance(True, int)` is `True`, so `MergeConfig(seed=True)` silently produces seed=1 and `MergeConfig(seed=False)` produces seed=0.

**Established codebase pattern** (`manifest.py:219`):
```python
if not isinstance(seed_value, int) or isinstance(seed_value, bool):
```

**Suggested Addition:**

Update the `__post_init__` specification to:
```python
def __post_init__(self) -> None:
    if not isinstance(self.seed, int) or isinstance(self.seed, bool) or self.seed < 0:
        raise ValueError(
            f"seed must be a non-negative integer, got {self.seed!r}"
        )
    object.__setattr__(
        self, "drop_right_columns", tuple(self.drop_right_columns)
    )
```

Add a test case: `TestMergeConfig`: `MergeConfig(seed=True)` raises `ValueError`.

### 2. `**self.details` Key Collision in `to_governance_entry()`

**Benefit:** Prevents silent data corruption in governance records when `details` contains "method" or "statement" keys.

**Source:** Dev Notes §MergeAssumption — Governance Integration

**Current Gap:**

```python
return {
    "key": f"merge_{self.method_name}",
    "value": {
        "method": self.method_name,
        "statement": self.statement,
        **self.details,          # ← could override "method" or "statement"
    },
    ...
}
```

If any `MergeMethod` implementation populates `details` with a key named `"method"` or `"statement"`, the explicit values are silently overridden. This is especially dangerous for downstream Story 11.5 IPF implementation which will add richer `details` dicts.

**Suggested Addition:**

Either document this constraint explicitly ("details must not contain keys 'method' or 'statement'") or change the merge order:

```python
"value": {
    **self.details,           # unpack first
    "method": self.method_name,   # then override with authoritative values
    "statement": self.statement,
},
```

And add a note in Task 2.3 and the test `TestMergeAssumption` to verify that `to_governance_entry()` always has the correct `method` and `statement` in `value`, even when `details` contains conflicting keys.

### 3. File Count Mismatch in "Project Structure Notes"

**Benefit:** Developer accurately tracks what to create/modify; avoids confusion at completion checkpoint.

**Source:** Dev Notes §Project Structure Notes

**Current Gap:**

```
**New files (6):**          ← says 6
- src/reformlab/population/methods/__init__.py
- src/reformlab/population/methods/base.py
- src/reformlab/population/methods/errors.py
- src/reformlab/population/methods/uniform.py
- tests/population/methods/__init__.py
- tests/population/methods/conftest.py
- tests/population/methods/test_base.py
- tests/population/methods/test_uniform.py
- tests/population/methods/test_errors.py  ← 9 files listed

**Modified files (2):**     ← says 2
- src/reformlab/population/__init__.py — add methods exports
- (no other files modified)             ← only 1 listed
```

**Suggested Fix:** Update counts to "New files (9):" and "Modified files (1):".

### 4. `from copy import deepcopy` Inside `__post_init__` Violates Top-Level Import Convention

**Benefit:** Consistency with project conventions; avoids surprising import-inside-function pattern.

**Source:** Dev Notes §MergeAssumption; compare `manifest.py:22` (`from copy import deepcopy` at module level)

**Current Gap:**

The story shows:
```python
def __post_init__(self) -> None:
    from copy import deepcopy    # ← local import inside method
    object.__setattr__(self, "details", deepcopy(self.details))
```

**Established pattern** (`manifest.py:22`):
```python
from copy import deepcopy  # at module level
```

`copy` is a stdlib module with no circular dependency risk. The `if TYPE_CHECKING:` guard in `project-context.md` applies to imports that "create circular dependencies" — this is not the case here. The local import provides no benefit and breaks convention.

**Suggested Fix:** Move `from copy import deepcopy` to the module-level imports section in `base.py`.

### 5. `methods/__init__.py` Missing `__all__` Specification

**Benefit:** Consistent with `population/__init__.py` which defines a full `__all__`. Controls public API surface, aids IDE autocompletion and `from methods import *` safety.

**Source:** `src/reformlab/population/__init__.py:74–109` (explicit `__all__` list)

**Current Gap:**

Task 4.1 says "Export from `src/reformlab/population/methods/__init__.py`: ..." but doesn't specify that an `__all__` list must be defined. The existing `population/__init__.py` has a 36-item `__all__`. Omitting this creates inconsistency.

**Suggested Fix:** Add to Task 4.1: "Define `__all__ = [...]` listing all exports explicitly, following the pattern in `src/reformlab/population/__init__.py`."

---

## ✨ Optimizations (Nice to Have)

### 1. Document Merged Table Column Ordering as a Contract

**Value:** Downstream code (Story 11.6 pipeline, Story 11.7 validation) needs to know the column layout of the merged table. Unstated contracts become surprises.

**Suggestion:** Add one sentence to Dev Notes §Algorithm Detail: "The merged table preserves column ordering: all columns from `table_a` appear first (in their original order), followed by all columns from `table_b` (after `drop_right_columns` removal)." Add a test assertion in `TestUniformMergeMethodMerge` verifying column order matches `income_table.schema.names + vehicle_table.schema.names`.

### 2. Specify Runtime `pyarrow` Import Explicitly

**Value:** Prevents a developer from placing `import pyarrow as pa` under `if TYPE_CHECKING:` in `uniform.py`, causing `NameError` at runtime when `pa.array()` and `pa.table()` are called.

**Suggestion:** Add a callout in Task 3 or in Dev Notes §No New Dependencies Required:

> `pyarrow` must be imported at module level in `uniform.py` (NOT under `if TYPE_CHECKING:`), because `pa.array()` and `pa.table()` are called at **runtime** inside `merge()`. Contrast with protocol files where `pa.Table` is annotation-only and can use `TYPE_CHECKING` guard.

### 3. Clarify `MergeAssumption.details` Must Be JSON-Compatible

**Value:** Prevents runtime `ManifestValidationError` when Story 11.6 builds a `RunManifest` with merge assumptions. Establishes a documented constraint for Story 11.5 IPF implementors.

**Suggestion:** Add to Task 2.3 (`MergeAssumption`):

> `details` values must be JSON-compatible (`str`, `int`, `float`, `bool`, `None`, `list`, `dict`). This constraint is enforced at `RunManifest` construction time by `_validate_json_compatible()` in `manifest.py`. Never put `pa.Table`, `pa.Schema`, `Path`, or custom objects in `details`.

---

## 🤖 LLM Optimization Improvements

### 1. Downstream Dependencies Reference Is Misleading

**Issue:** Factual inaccuracy (addressed in Critical Issues #1) will cause an LLM dev agent to implement the wrong integration.

**Token Impact:** High — LLM agents read "Downstream Dependencies" to understand cross-story contracts. A wrong reference causes wrong code in Story 11.6.

**Current:**
```
passes them to `governance.capture.capture_assumptions()`
```

**Optimized:**
```
calls `assumption.to_governance_entry()` on each, appends result directly to 
`RunManifest.assumptions` list (NOT via `capture_assumptions()` — that function 
only handles scalar key-value assumptions, not structured merge records)
```

### 2. `UniformMergeMethod.merge()` Step Ordering Ambiguity

**Issue:** Steps 2 and 3 in Task 3.4 could confuse implementation order — "empty table validation" (step 1) happens BEFORE `drop_right_columns` (step 2), but `drop_right_columns` reduces table_b's columns, not its rows. A developer might wonder whether `table_b.num_rows == 0` should be checked before or after dropping columns.

**Token Impact:** Medium — ambiguous ordering leads to re-reads and possible implementation divergence.

**Current:**
```
1. Validate inputs: both tables must have num_rows > 0
2. Apply config.drop_right_columns: remove listed columns from table_b
3. Check column name conflicts
```

**Optimized:**
```
1. Validate inputs: both tables must have num_rows > 0 (check BEFORE any drops — 
   drop_right_columns removes columns not rows, so row count is unaffected)
2. Apply config.drop_right_columns: remove listed columns from table_b before conflict check
3. Check column name conflicts against the POST-drop table_b schema
```

---

## 📝 Changes Applied

No changes were applied to the story file. This report serves as documentation only.

---

## 🏆 Competition Results

### Quality Metrics

| Metric | Score |
|--------|-------|
| Requirements Coverage | 88% |
| Architecture Alignment | 93% |
| Previous Story Integration | 82% |
| LLM Optimization Score | 89% |
| **Overall Quality Score** | **88%** |

### Disaster Prevention Assessment

- **Reinvention Prevention:** ✅ Clean — correctly references DataSourceLoader, ComputationAdapter patterns; no wheel-reinvention risks
- **Technical Specifications:** ⚠️ One factual API error (`capture_assumptions()`) that will cause wrong Story 11.6 integration
- **File Structure:** ⚠️ Count mismatch (cosmetic but creates confusion at completion checkpoint)
- **Regression Risks:** ✅ Clean — tasks 7.1–7.4 correctly specify running full suite + no regressions
- **Implementation Clarity:** ✅ Mostly clean — algorithm is well-specified; `bool` seed and deepcopy style are gaps

### Competition Outcome

🏆 **Validator identified 9 improvements** (1 critical, 5 important, 3 minor) that enhance the story context. The original create-story produced solid work — the story is fundamentally sound and implementable — but the `capture_assumptions()` API factual error is a genuine disaster that needs fixing before a dev agent picks this up.

---

**Report Generated:** 2026-03-03
**Validation Engine:** BMAD Method Quality Competition v1.0

]]></file>
<file id="557aedd2" path="[Validator B]" label="VALIDATION OUTPUT"><![CDATA[

# 🎯 Story Context Validation Report

**Story:** 11-4-define-mergemethod-protocol-and-uniform-distribution-method - define-mergemethod-protocol-and-uniform-distribution-method  
**Story File:** _bmad-output/implementation-artifacts/11-4-define-mergemethod-protocol-and-uniform-distribution-method.md  
**Validated:** 2026-03-03  
**Validator:** Quality Competition Engine

---

## Executive Summary

### Issues Overview

| Category | Found | Applied |
|----------|-------|---------|
| 🚨 Critical Issues | 2 | 0 |
| ⚡ Enhancements | 3 | 0 |
| ✨ Optimizations | 1 | 0 |
| 🤖 LLM Optimizations | 2 | 0 |

**Overall Assessment:** MAJOR REWORK – key acceptance criteria and safeguards are missing; story needs tightening before dev.

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🔴 CRITICAL | Acceptance criteria omit determinism/seed requirement and “with replacement” semantics for uniform merge, making behavior non-testable and non-reproducible. | AC#2 | +3 |
| 🔴 CRITICAL | No acceptance criteria for failure modes (empty tables, column conflicts, invalid drop_right_columns), risking silent bad merges. | AC set | +3 |
| 🟠 IMPORTANT | Hidden dependency on governance manifest JSON-compatibility for assumptions not captured in ACs. | Tasks 2.3/2.4 | +1 |
| 🟠 IMPORTANT | Logging/governance integration not required by ACs, risking missing audit trail. | Tasks 3.5 | +1 |
| 🟡 MINOR | Story text verbose and repetitive; key requirements buried. | Entire story | +0.3 |
| 🟢 CLEAN PASS | 1 category with no issues (technical alignment) |  | -0.5 |

### Evidence Score: 7.8

| Score | Verdict |
|-------|---------|
| **7.8** | **REJECT** |

---

## 🎯 Ruthless Story Validation 11.4

### INVEST Criteria Assessment

| Criterion | Status | Severity | Details |
|-----------|--------|----------|---------|
| **I**ndependent | Mostly OK | 2/10 | Relies on existing governance manifest types but can be built now; dependency should be surfaced. |
| **N**egotiable | Slightly rigid | 3/10 | Tasks prescribe implementation details (section separators, logging format), leaving little flexibility though not fatal. |
| **V**aluable | Clear | 0/10 | Provides baseline merge method and protocol; clear value for downstream methods. |
| **E**stimable | Minor gaps | 3/10 | Scope clear, but missing ACs for error handling add estimation risk. |
| **S**mall | Acceptable | 2/10 | Several files/tests but still single-sprint; no splitting required. |
| **T**estable | Weak | 7/10 | ACs miss deterministic seed, with/without replacement, and error scenarios; current ACs insufficient for objective testing. |

### INVEST Violations

- **[7/10] Testable:** ACs omit determinism, replacement semantics, and failure cases, making objective verification incomplete.

### Acceptance Criteria Issues

- **Missing:** Deterministic behavior requirement (seeded repeatability) not stated; current AC#2 only says “randomly.”
  - *Quote:* "matched with a randomly drawn row"  
  - *Recommendation:* Add “using provided seed for reproducible draws.”
- **Ambiguous:** No clarity on with/without replacement in uniform match.
  - *Quote:* "randomly drawn row"  
  - *Recommendation:* Specify “uniform with replacement.”
- **Missing:** Failure modes for empty tables, overlapping column names, and invalid `drop_right_columns` are absent.
  - *Quote:* none  
  - *Recommendation:* Add ACs covering validation errors for these cases.
- **Missing:** Governance/assumption output shape and JSON compatibility not validated by ACs.
  - *Quote:* AC#3 only checks statement text  
  - *Recommendation:* Add AC ensuring `assumption.to_governance_entry()` returns manifest-compatible JSON.

### Hidden Risks and Dependencies

- **Governance manifest contract:** Assumption entry must match `governance.manifest.AssumptionEntry` JSON rules; not called out.
  - *Impact:* Runtime manifest validation failures.  
  - *Mitigation:* Add AC and task to assert JSON-compatibility.
- **Logging/audit dependency:** Structured logging expected but not enforced by ACs.
  - *Impact:* Missing audit trail for merges.  
  - *Mitigation:* Add AC for logged events.
- **PyArrow/random determinism:** Depend on pyarrow version behavior and Python RNG; unspecified seed handling.
  - *Impact:* Non-reproducible merges.  
  - *Mitigation:* AC for seed determinism and RNG scope.

### Estimation Reality-Check

**Assessment:** Under-estimated – missing failure-mode ACs and determinism requirements will surface during implementation/testing, adding effort.

### Technical Alignment

**Status:** Aligns with architecture; no structural conflicts found.

---

## 🚨 Critical Issues (Must Fix)

### 1. Acceptance criteria lack determinism and replacement semantics
**Impact:** Non-reproducible merges; tests cannot assert correctness; downstream analyses unreliable.  
**Source:** Acceptance Criteria #2.  

**Problem:** AC#2 only says “randomly drawn row” without specifying with/without replacement or seed-driven determinism.  

**Recommended Fix:** Amend AC#2 to: “...matched with a uniformly random row from Table B **with replacement**, using the provided `MergeConfig.seed` to guarantee reproducibility.”

### 2. No ACs for validation failures (empty inputs, column conflicts, bad drop lists)
**Impact:** Implementations may silently produce corrupted tables; regressions undetected.  
**Source:** Acceptance Criteria set (none cover errors).  

**Problem:** Story omits required behavior when tables are empty, columns overlap, or `drop_right_columns` names are invalid.  

**Recommended Fix:** Add ACs covering: (a) empty table_a or table_b → `MergeValidationError`; (b) overlapping column names → error listing conflicts; (c) nonexistent drop_right_columns → error.

---

## ⚡ Enhancement Opportunities (Should Add)

### 1. Governance/manifest compatibility AC
**Benefit:** Prevents runtime manifest validation failures.  
**Source:** Tasks 2.3/2.4 (assumption to governance entry).  

**Current Gap:** ACs don’t require `MergeAssumption.to_governance_entry()` to produce JSON-compatible, schema-valid entries.  
**Suggested Addition:** New AC: “Assumption entry emitted by uniform merge is JSON-serializable and matches `AssumptionEntry` schema (key/value/source/is_default).”

### 2. Explicit logging requirement
**Benefit:** Ensures auditability for merges.  
**Source:** Task 3.5 mentions logging but ACs ignore it.  

**Current Gap:** Success/failure events may go unlogged.  
**Suggested Addition:** AC: “Merge emits structured log events `event=merge_start` and `event=merge_complete` with method, seed, rows_a, rows_b.”

### 3. Clarify drop_right_columns behavior
**Benefit:** Avoids accidental key duplication.  
**Source:** Task 3.4.  

**Current Gap:** No AC ensuring specified columns are removed before conflict detection.  
**Suggested Addition:** AC: “When `drop_right_columns` is provided, columns are removed from table_b prior to conflict check; invalid column names raise `MergeValidationError`.”

---

## ✨ Optimizations (Nice to Have)

### 1. Performance note on large tables
**Value:** Prevents accidental O(N^2) merges if future method swaps in Python loops.  

**Suggestion:** Add guidance to keep row selection vectorized via `pa.Table.take` and avoid per-row Python loops for uniform merge.

---

## 🤖 LLM Optimization Improvements

### 1. Collapse repeated architectural reminders
**Issue:** Verbose repetition of project rules inflates tokens.  
**Token Impact:** High.  

**Current:**
```
Follow the exact same protocol pattern established in loaders... (multiple paragraphs repeating rules)
```

**Optimized:**
```
Follow loader pattern: @runtime_checkable Protocol, frozen dataclasses with __post_init__ validation, subsystem-specific errors (summary-reason-fix), no ABCs, from __future__ import annotations.
```

**Rationale:** Same guidance conveyed in one sentence aids LLM efficiency.

### 2. Summarize fixture specs
**Issue:** Lengthy fixture descriptions; key requirements buried.  
**Token Impact:** Medium.  

**Current:**
```
Long paragraphs describing each fixture file and sample CSV contents...
```

**Optimized:**
```
Fixtures: income_table (5 rows, id/income/region), vehicle_table (8 rows, type/age/fuel), overlapping_table (conflict column), empty_table; CSV fixtures optional, keep small (≤10 rows).
```

**Rationale:** Keeps essentials while preserving intent.

---

## 📝 Changes Applied

No changes were applied to the story file. This report serves as documentation only.

---

## 🏆 Competition Results

### Quality Metrics

| Metric | Score |
|--------|-------|
| Requirements Coverage | 70% |
| Architecture Alignment | 90% |
| Previous Story Integration | 60% |
| LLM Optimization Score | 65% |
| **Overall Quality Score** | **68%** |

### Disaster Prevention Assessment

- **Reinvention:** Risk present – clarify reuse of governance manifest types.  
- **Technical Specification:** Risk – determinism and error handling unspecified.  
- **File Structure:** Clean.  
- **Regression:** Risk – missing failure-mode ACs may allow silent regressions.  
- **Implementation:** Risk – ambiguous randomness semantics.

### Competition Outcome

🏆 **Validator identified 8 improvements** that enhance the story context.

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
<var name="session_id">7778ca0b-789d-475b-aa39-c644eb0820b9</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_file" file_id="6870c5a9">embedded in prompt, file id: 6870c5a9</var>
<var name="story_id">11.4</var>
<var name="story_key">11-4-define-mergemethod-protocol-and-uniform-distribution-method</var>
<var name="story_num">4</var>
<var name="story_title">define-mergemethod-protocol-and-uniform-distribution-method</var>
<var name="template">False</var>
<var name="timestamp">20260303_1522</var>
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