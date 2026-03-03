
# Story 11.4: Define MergeMethod protocol and implement uniform distribution method

Status: dev-complete

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform developer building the French household population pipeline,
I want a `MergeMethod` protocol defining the interface for statistical dataset fusion and a concrete `UniformMergeMethod` implementation that randomly matches rows between two tables,
so that downstream stories (11.5 IPF/conditional sampling, 11.6 pipeline builder) have a proven protocol pattern to follow, and the simplest merge method is available as a baseline for population construction.

## Acceptance Criteria

1. Given the `MergeMethod` protocol, when a new method is implemented, then it must accept two `pa.Table` inputs plus a config, and return a merged table plus an assumption record.
2. Given two tables with no shared sample, when merged using uniform distribution, then each row from Table A is matched with a uniformly random row from Table B with replacement, using the provided `MergeConfig.seed` to guarantee reproducibility.
3. Given a uniform merge, when the assumption record is inspected, then it states: "Each household in source A is matched to a household in source B with uniform probability — this assumes no correlation between the variables in the two sources."
4. Given the uniform method docstring, when read, then it includes a plain-language explanation of the independence assumption and when this is appropriate vs. problematic.

## Tasks / Subtasks

- [x] Task 1: Create `src/reformlab/population/methods/` directory structure (AC: #1)
  - [x]1.1 Create `src/reformlab/population/methods/__init__.py` with module docstring referencing Story 11.4, FR38, FR39
  - [x]1.2 Create `src/reformlab/population/methods/errors.py` with `MergeError` base exception and `MergeValidationError` — follow the `summary - reason - fix` pattern from `DataSourceError` in `population/loaders/errors.py`

- [x] Task 2: Define `MergeMethod` protocol and supporting types — `base.py` (AC: #1, #3)
  - [x]2.1 Create `src/reformlab/population/methods/base.py` with module docstring referencing Story 11.4, FR38
  - [x]2.2 Define `MergeConfig` frozen dataclass with fields: `seed: int`, `description: str = ""`, `drop_right_columns: tuple[str, ...] = ()` — validate in `__post_init__` that `seed` is a non-negative integer and not a `bool` (Python `bool ⊂ int`; follow `manifest.py:219` pattern)
  - [x]2.3 Define `MergeAssumption` frozen dataclass with fields: `method_name: str`, `statement: str`, `details: dict[str, Any]` — include `to_governance_entry(*, source_label: str = "merge_step") -> dict[str, Any]` method that produces a dict compatible with `governance.manifest.AssumptionEntry` (keys: `key`, `value`, `source`, `is_default`). `details` values must be JSON-compatible (`str`, `int`, `float`, `bool`, `None`, `list`, `dict`) — enforced at `RunManifest` construction by `_validate_json_compatible()`. Never put `pa.Table`, `pa.Schema`, `Path`, or custom objects in `details`. The `to_governance_entry()` must unpack `**self.details` first, then override with `method` and `statement` keys to prevent key collision from details
  - [x]2.4 Define `MergeResult` frozen dataclass with fields: `table: pa.Table`, `assumption: MergeAssumption`
  - [x]2.5 Define `MergeMethod` as `@runtime_checkable` Protocol with two required members:
    - `def merge(self, table_a: pa.Table, table_b: pa.Table, config: MergeConfig) -> MergeResult`
    - `name: str` property (read-only)
  - [x]2.6 Validate design: `MergeConfig.__post_init__` deep-copies `drop_right_columns` to prevent aliasing (use `object.__setattr__` pattern from `SourceConfig`)
  - [x]2.7 Validate design: `MergeAssumption.details` deep-copied in `__post_init__` to prevent mutation

- [x] Task 3: Implement `UniformMergeMethod` — `uniform.py` (AC: #2, #3, #4)
  - [x]3.1 Create `src/reformlab/population/methods/uniform.py` with module docstring referencing Story 11.4, FR38, FR39 — include the pedagogical docstring explaining the independence assumption in plain language (when appropriate: independent surveys; when problematic: correlated variables)
  - [x]3.2 Implement `UniformMergeMethod` class with `__init__(self)` (no constructor parameters — uniform has no method-specific config)
  - [x]3.3 Implement `name` property returning `"uniform"`
  - [x]3.4 Implement `merge(self, table_a, table_b, config)` with this logic:
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
  - [x]3.5 Use `logging.getLogger(__name__)` with structured `event=merge_start`, `event=merge_complete` log entries including `method=uniform rows_a=... rows_b=... seed=...`

- [x] Task 4: Update `__init__.py` exports (AC: #1)
  - [x]4.1 Export from `src/reformlab/population/methods/__init__.py`: `MergeMethod`, `MergeConfig`, `MergeAssumption`, `MergeResult`, `UniformMergeMethod`, `MergeError`, `MergeValidationError` — define `__all__` listing all exports explicitly (follow `population/loaders/__init__.py` pattern)
  - [x]4.2 Add methods exports to `src/reformlab/population/__init__.py`: same names as 4.1

- [x] Task 5: Create test infrastructure (AC: all)
  - [x]5.1 Create `tests/population/methods/__init__.py`
  - [x]5.2 Create `tests/population/methods/conftest.py` with fixtures:
    - `income_table` — small `pa.Table` with columns: `household_id` (int64), `income` (float64), `region_code` (utf8) — 5 rows
    - `vehicle_table` — small `pa.Table` with columns: `vehicle_type` (utf8), `vehicle_age` (int64), `fuel_type` (utf8) — 8 rows
    - `overlapping_table` — small `pa.Table` with a column name that conflicts with `income_table` (e.g., `region_code`)
    - `empty_table` — `pa.Table` with schema but 0 rows
    - `default_config` — `MergeConfig(seed=42)`

- [x] Task 6: Write comprehensive tests (AC: all)
  - [x]6.1 `tests/population/methods/test_base.py`:
    - `TestMergeConfig`: frozen, `__post_init__` validation (negative seed raises `ValueError`, `bool` seed raises `ValueError`), `drop_right_columns` deep-copied, default values
    - `TestMergeAssumption`: frozen, `details` deep-copied, `to_governance_entry()` returns correct dict with `key`/`value`/`source`/`is_default` fields
    - `TestMergeResult`: frozen, holds table + assumption
    - `TestMergeMethodProtocol`: verify `UniformMergeMethod` passes `isinstance(m, MergeMethod)` check; verify a non-conforming class fails
  - [x]6.2 `tests/population/methods/test_uniform.py`:
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
  - [x]6.3 `tests/population/methods/test_errors.py`:
    - `TestMergeError`: inherits `Exception`, `summary-reason-fix` message format, attributes accessible
    - `TestMergeValidationError`: inherits `MergeError`

- [x] Task 7: Run full test suite and lint (AC: all)
  - [x]7.1 `uv run pytest tests/population/methods/` — all new tests pass
  - [x]7.2 `uv run pytest tests/population/` — no regressions in loader tests
  - [x]7.3 `uv run ruff check src/reformlab/population/methods/ tests/population/methods/` — no lint errors
  - [x]7.4 `uv run mypy src/reformlab/population/methods/` — no mypy errors (strict mode)

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
        if not isinstance(self.seed, int) or isinstance(self.seed, bool) or self.seed < 0:
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
                **self.details,
                "method": self.method_name,
                "statement": self.statement,
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
3. Concatenate columns from table_a and the selected table_b rows — the merged table preserves column ordering: all columns from table_a appear first (in their original order), followed by all columns from table_b (after `drop_right_columns` removal)

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

**Import notes:** `from copy import deepcopy` must be at module level in `base.py` (follow `manifest.py:22` pattern — stdlib, no circular dependency risk). `import pyarrow as pa` must be at module level in `uniform.py` (NOT under `if TYPE_CHECKING:`) because `pa.array()` and `pa.table()` are called at runtime. In `base.py`, `pyarrow` may use `TYPE_CHECKING` guard since `pa.Table` is annotation-only.

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
- **Story 11.6** (PopulationPipeline) — composes loaders + methods, calls `merge()` in sequence, collects `MergeAssumption` records, calls `assumption.to_governance_entry()` on each, and appends the resulting dicts directly to `RunManifest.assumptions` (type: `list[AssumptionEntry]`). Does NOT use `governance.capture.capture_assumptions()` — that function handles scalar key-value parameter assumptions, not structured merge assumption records
- **Story 11.7** (Validation) — validates merged population against marginals
- **Story 11.8** (Notebook) — demonstrates merge methods with plain-language explanations

### Project Structure Notes

**New files (9):**
- `src/reformlab/population/methods/__init__.py`
- `src/reformlab/population/methods/base.py`
- `src/reformlab/population/methods/errors.py`
- `src/reformlab/population/methods/uniform.py`
- `tests/population/methods/__init__.py`
- `tests/population/methods/conftest.py`
- `tests/population/methods/test_base.py`
- `tests/population/methods/test_uniform.py`
- `tests/population/methods/test_errors.py`

**Modified files (1):**
- `src/reformlab/population/__init__.py` — add methods exports

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

## File List

**New files (9):**
- `src/reformlab/population/methods/__init__.py`
- `src/reformlab/population/methods/base.py`
- `src/reformlab/population/methods/errors.py`
- `src/reformlab/population/methods/uniform.py`
- `tests/population/methods/__init__.py`
- `tests/population/methods/conftest.py`
- `tests/population/methods/test_base.py`
- `tests/population/methods/test_uniform.py`
- `tests/population/methods/test_errors.py`

**Modified files (1):**
- `src/reformlab/population/__init__.py` — added methods exports

## Dev Agent Record

### Implementation Plan

Implemented all 7 tasks following the story spec exactly:

1. Created `methods/` package with `__init__.py` (FR38/FR39 docstring) and `errors.py` (`MergeError` hierarchy with summary-reason-fix pattern).
2. Defined `MergeConfig` (frozen, bool-rejecting seed validation, deep-copied `drop_right_columns`), `MergeAssumption` (deep-copied details, `to_governance_entry()` with key-collision prevention), `MergeResult`, and `MergeMethod` runtime-checkable Protocol in `base.py`.
3. Implemented `UniformMergeMethod` in `uniform.py` with: input validation, `drop_right_columns` removal, column conflict detection, `random.Random(seed)`-based deterministic matching with replacement, `pa.table()` column combination, structured assumption record, and structured logging.
4. Updated both `methods/__init__.py` and `population/__init__.py` with all 7 exports and `__all__`.
5. Created test infrastructure: `conftest.py` with 5 fixtures (`income_table`, `vehicle_table`, `overlapping_table`, `empty_table`, `default_config`).
6. Wrote 50 tests across 3 test files covering: frozen dataclass immutability, `__post_init__` validation, governance entry generation, protocol compliance, merge behavior, determinism, column conflicts, `drop_right_columns`, empty table rejection, assumption record content, with-replacement behavior, and pedagogical docstrings.
7. All 235 population tests pass (50 new + 185 existing), ruff clean, mypy strict clean.

### Completion Notes

- All 4 acceptance criteria satisfied
- `pyarrow` import in `base.py` uses `TYPE_CHECKING` guard (annotation-only); runtime import in `uniform.py`
- `deepcopy` imported at module level in `base.py`
- No new dependencies introduced
- All conventions from `project-context.md` followed

## Change Log

- 2026-03-03: Story created by create-story workflow — comprehensive developer context with MergeMethod protocol design, UniformMergeMethod algorithm, governance integration pattern, error hierarchy, test fixture designs, and downstream dependency mapping.
- 2026-03-03: Validation synthesis — fixed `capture_assumptions()` API reference in Downstream Dependencies, added `bool` rejection to `MergeConfig.seed` validation, fixed `to_governance_entry()` key collision risk, moved `deepcopy` import to module level, added `__all__` requirement, fixed file counts, improved AC#2 wording, documented column ordering contract and import notes.
- 2026-03-03: Implementation complete — all 7 tasks done, 50 new tests passing, 0 regressions, ruff clean, mypy strict clean.
