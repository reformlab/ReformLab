# Story 29.5: Add `pa.concat_tables()` schema-mismatch regression tests

Status: done

## Story

As a backend developer maintaining the orchestrator panel,
I want regression tests covering both `concat_tables` paths in `src/reformlab/orchestrator/panel.py` (the `promote_options="permissive"` decision-column branch and the non-decision branch) against divergent yearly schemas,
so that future schema drift can't silently break panel concatenation across years.

## Acceptance Criteria

1. Given the `pa.concat_tables(..., promote_options="permissive")` call in the decision-column branch (`panel.py:158`), when tests feed tables with mismatched schemas (decision columns present in year-N, absent in year-N+1 and vice versa), then each test asserts permissive promotion succeeds without raising and fills missing columns with null.
2. Given the non-decision branch (`panel.py:163`), when a test feeds tables with a data output column present in one year and absent in another, then the test asserts and locks the existing behavior — permissive promotion succeeds and fills missing cells with null.
3. Given a type mismatch between yearly tables (e.g., `income` as `int64` in year-N vs `float64` in year-N+1), when permissive promotion runs, then the test asserts concat succeeds and the result column has the promoted common type (`float64`).
4. Given the existing `tests/orchestrator/test_panel.py`, when this story is complete, then it gains a new `TestConcatTablesSchemaMismatch` class with at least four tests covering: decision-column-in-first-year-only, decision-column-in-second-year-only, output-column-in-first-year-only, type-mismatch-int-vs-float.
5. Given all new tests, when run, then they pass on the current production code with zero modifications to `panel.py`.

## Tasks / Subtasks

- [x] Read and confirm both concat paths in `panel.py` (AC: #1, #2)
  - [x] Verify line 158 uses `promote_options="permissive"` in the decision branch
  - [x] Verify line 163 uses `promote_options="permissive"` in the non-decision branch
  - [x] Confirm the `has_any_decision_columns` flag (line 92, set at lines 130 and 136) gates the branch choice
- [x] Add `TestConcatTablesSchemaMismatch` class to `tests/orchestrator/test_panel.py` (AC: #3, #4)
  - [x] Test 1: Decision column in year-1, absent in year-2 → null fill (AC: #1)
  - [x] Test 2: Decision column absent in year-1, present in year-2 → null fill (AC: #1)
  - [x] Test 3: Data output column present in year-1, absent in year-2 → non-decision branch null fill (AC: #2)
  - [x] Test 4: `int64` vs `float64` type mismatch → promoted to `float64` (AC: #3)
- [x] Quality gates (AC: #5)
  - [x] `uv run ruff check src/ tests/`
  - [x] `uv run mypy src/`
  - [x] `uv run pytest tests/orchestrator/`

## Dev Notes

### Scope — pure test addition

This is a pure test story. **Do not modify `panel.py` or any production code.** If a test reveals an actual bug (e.g., a non-permissive raise that loses data), capture it as a follow-up GitHub issue comment in the story but leave the code unchanged.

### Exact code paths under test

**`src/reformlab/orchestrator/panel.py:155–163`** (read the file before coding):

```python
elif has_any_decision_columns:
    # Use promote_options for schema flexibility when some years
    # have decision columns and others don't
    panel_table = pa.concat_tables(
        yearly_tables, promote_options="permissive"        # line 158
    )
else:
    # Concatenate all yearly tables
    panel_table = pa.concat_tables(yearly_tables, promote_options="permissive")  # line 163
```

Both branches use `promote_options="permissive"`. The branch is selected by `has_any_decision_columns` (bool, line 92), which is set to `True` at:
- Line 130: when `_build_decision_columns()` returns a tuple (non-empty decision log)
- Line 136: when only transition records exist

### How permissive promotion works (PyArrow)

`pa.concat_tables(tables, promote_options="permissive")` resolves schema differences by:
- **Missing columns**: filled with null values for the rows that lack the column — the column retains the type from the schema of the year(s) that do have it (e.g., a `float64` column absent in one year appears as `float64` with null values, not as a `null`-typed column). Do not assert `pa.types.is_null(...)` for null-fill scenarios.
- **Numeric type promotion**: `int64` + `float64` → `float64`; narrower types are widened
- **Incompatible types** (e.g., `int64` vs `string`): raises `ArrowInvalid`; permissive does NOT handle these

The tests should assert on null presence and promoted types, not on exact arrow types for the null columns (which vary by PyArrow version).

### Test class to add to `test_panel.py`

Add a new class `TestConcatTablesSchemaMismatch` at the bottom of `tests/orchestrator/test_panel.py`. The class uses existing helpers from the same file (`make_computation_result`, `make_orchestrator_result`) and imports from `reformlab.discrete_choice.decision_record`.

**Required imports** (already present in `test_panel_decision.py`; add only if missing from `test_panel.py`):

```python
from reformlab.discrete_choice.decision_record import (
    DECISION_LOG_KEY,
    DecisionRecord,
)
```

**Decision record helper** — inline within the test class or as a module-level helper:

```python
def _make_minimal_decision_record(domain: str, n: int) -> DecisionRecord:
    """Minimal DecisionRecord for schema-mismatch tests."""
    return DecisionRecord(
        domain_name=domain,
        alternative_ids=("ev", "ice"),
        chosen=pa.array(["ev"] * n, type=pa.string()),
        probabilities=pa.table({"ev": [0.6] * n, "ice": [0.4] * n}),
        utilities=pa.table({"ev": [-1.0] * n, "ice": [-2.0] * n}),
        seed=42,
        taste_parameters={"beta_cost": -0.01},
        eligibility_summary=None,
    )
```

### Concrete test scaffolds

#### Test 1 — decision column in year-1, absent in year-2

```python
def test_decision_column_in_first_year_only_fills_null_in_second(self) -> None:
    """AC-1: permissive promotion fills decision columns absent in year-2 with null."""
    n = 3
    comp_2024 = ComputationResult(
        output_fields=pa.table({
            "household_id": pa.array(range(n), type=pa.int64()),
            "income": pa.array([50000.0] * n),
        }),
        adapter_version="test-1.0.0",
        period=2024,
    )
    comp_2025 = ComputationResult(
        output_fields=pa.table({
            "household_id": pa.array(range(n), type=pa.int64()),
            "income": pa.array([52000.0] * n),
        }),
        adapter_version="test-1.0.0",
        period=2025,
    )
    decision = _make_minimal_decision_record("heating", n)

    result = OrchestratorResult(
        success=True,
        yearly_states={
            2024: YearState(
                year=2024,
                data={
                    COMPUTATION_RESULT_KEY: comp_2024,
                    DECISION_LOG_KEY: (decision,),
                },
                seed=42,
                metadata={},
            ),
            2025: YearState(
                year=2025,
                data={COMPUTATION_RESULT_KEY: comp_2025},
                seed=43,
                metadata={},
            ),
        },
        errors=[],
        failed_year=None,
        metadata={"start_year": 2024, "end_year": 2025, "seed": 42, "step_pipeline": ["computation"]},
    )

    panel = PanelOutput.from_orchestrator_result(result)

    # Does not raise — permissive handles missing decision columns
    assert panel.table.num_rows == n * 2

    # Decision column present (with null for year 2025)
    assert "heating_chosen" in panel.table.column_names

    # Year 2024 rows have non-null chosen value
    import pyarrow.compute as pc
    year_2024_mask = pc.equal(panel.table.column("year"), 2024)
    year_2024_rows = panel.table.filter(year_2024_mask)
    assert not any(v is None for v in year_2024_rows.column("heating_chosen").to_pylist())

    # Year 2025 rows have null chosen value
    year_2025_mask = pc.equal(panel.table.column("year"), 2025)
    year_2025_rows = panel.table.filter(year_2025_mask)
    assert all(v is None for v in year_2025_rows.column("heating_chosen").to_pylist())
```

#### Test 2 — decision column absent in year-1, present in year-2

```python
def test_decision_column_in_second_year_only_fills_null_in_first(self) -> None:
    """AC-1: permissive promotion fills decision columns absent in year-2024 with null."""
    n = 3
    comp_2024 = ComputationResult(
        output_fields=pa.table({
            "household_id": pa.array(range(n), type=pa.int64()),
            "income": pa.array([50000.0] * n),
        }),
        adapter_version="test-1.0.0",
        period=2024,
    )
    comp_2025 = ComputationResult(
        output_fields=pa.table({
            "household_id": pa.array(range(n), type=pa.int64()),
            "income": pa.array([52000.0] * n),
        }),
        adapter_version="test-1.0.0",
        period=2025,
    )
    decision = _make_minimal_decision_record("heating", n)

    result = OrchestratorResult(
        success=True,
        yearly_states={
            2024: YearState(
                year=2024,
                data={COMPUTATION_RESULT_KEY: comp_2024},  # no decision record
                seed=42,
                metadata={},
            ),
            2025: YearState(
                year=2025,
                data={
                    COMPUTATION_RESULT_KEY: comp_2025,
                    DECISION_LOG_KEY: (decision,),
                },
                seed=43,
                metadata={},
            ),
        },
        errors=[],
        failed_year=None,
        metadata={"start_year": 2024, "end_year": 2025, "seed": 42, "step_pipeline": ["computation"]},
    )

    panel = PanelOutput.from_orchestrator_result(result)

    # Does not raise — permissive handles missing decision columns
    assert panel.table.num_rows == n * 2

    # Decision column present (with null for year 2024)
    assert "heating_chosen" in panel.table.column_names

    # Year 2024 rows have null chosen value (no decision record)
    import pyarrow.compute as pc
    year_2024_mask = pc.equal(panel.table.column("year"), 2024)
    year_2024_rows = panel.table.filter(year_2024_mask)
    assert all(v is None for v in year_2024_rows.column("heating_chosen").to_pylist())

    # Year 2025 rows have non-null chosen value
    year_2025_mask = pc.equal(panel.table.column("year"), 2025)
    year_2025_rows = panel.table.filter(year_2025_mask)
    assert not any(v is None for v in year_2025_rows.column("heating_chosen").to_pylist())
```

#### Test 3 — output column in year-1 only (non-decision branch)

```python
def test_output_column_in_first_year_only_fills_null_in_second(self) -> None:
    """AC-2: non-decision branch promotes missing output columns with null."""
    n = 3
    # Year 2024 has an extra "subsidy_amount" column
    comp_2024 = ComputationResult(
        output_fields=pa.table({
            "household_id": pa.array(range(n), type=pa.int64()),
            "income": pa.array([50000.0] * n),
            "subsidy_amount": pa.array([200.0] * n),
        }),
        adapter_version="test-1.0.0",
        period=2024,
    )
    # Year 2025 lacks "subsidy_amount"
    comp_2025 = ComputationResult(
        output_fields=pa.table({
            "household_id": pa.array(range(n), type=pa.int64()),
            "income": pa.array([52000.0] * n),
        }),
        adapter_version="test-1.0.0",
        period=2025,
    )
    result = OrchestratorResult(
        success=True,
        yearly_states={
            2024: YearState(year=2024, data={COMPUTATION_RESULT_KEY: comp_2024}, seed=42, metadata={}),
            2025: YearState(year=2025, data={COMPUTATION_RESULT_KEY: comp_2025}, seed=43, metadata={}),
        },
        errors=[],
        failed_year=None,
        metadata={"start_year": 2024, "end_year": 2025, "seed": 42, "step_pipeline": ["computation"]},
    )

    # No decision records → non-decision branch (line 163)
    panel = PanelOutput.from_orchestrator_result(result)

    assert panel.table.num_rows == n * 2
    assert "subsidy_amount" in panel.table.column_names

    import pyarrow.compute as pc
    year_2024_rows = panel.table.filter(pc.equal(panel.table.column("year"), 2024))
    year_2025_rows = panel.table.filter(pc.equal(panel.table.column("year"), 2025))

    assert not any(v is None for v in year_2024_rows.column("subsidy_amount").to_pylist())
    assert all(v is None for v in year_2025_rows.column("subsidy_amount").to_pylist())
```

#### Test 4 — int64 vs float64 type mismatch

```python
def test_int_float_type_mismatch_promotes_to_float(self) -> None:
    """AC-3: permissive concat promotes int64/float64 mismatch to float64."""
    n = 3
    comp_2024 = ComputationResult(
        output_fields=pa.table({
            "household_id": pa.array(range(n), type=pa.int64()),
            "income": pa.array([50000, 60000, 70000], type=pa.int64()),  # int64
        }),
        adapter_version="test-1.0.0",
        period=2024,
    )
    comp_2025 = ComputationResult(
        output_fields=pa.table({
            "household_id": pa.array(range(n), type=pa.int64()),
            "income": pa.array([52000.5, 62000.5, 72000.5], type=pa.float64()),  # float64
        }),
        adapter_version="test-1.0.0",
        period=2025,
    )
    result = OrchestratorResult(
        success=True,
        yearly_states={
            2024: YearState(year=2024, data={COMPUTATION_RESULT_KEY: comp_2024}, seed=42, metadata={}),
            2025: YearState(year=2025, data={COMPUTATION_RESULT_KEY: comp_2025}, seed=43, metadata={}),
        },
        errors=[],
        failed_year=None,
        metadata={"start_year": 2024, "end_year": 2025, "seed": 42, "step_pipeline": ["computation"]},
    )

    panel = PanelOutput.from_orchestrator_result(result)

    assert panel.table.num_rows == n * 2
    # Permissive promotion widens to float64
    assert pa.types.is_floating(panel.table.schema.field("income").type)
    # Original values preserved (int promoted to float, no data loss)
    import pyarrow.compute as pc
    year_2024_rows = panel.table.filter(pc.equal(panel.table.column("year"), 2024))
    assert year_2024_rows.column("income").to_pylist() == [50000.0, 60000.0, 70000.0]
```

### Imports to add (if not already present in `test_panel.py`)

```python
from reformlab.discrete_choice.decision_record import (
    DECISION_LOG_KEY,
    DecisionRecord,
)
```

`DECISION_LOG_KEY` and `DecisionRecord` are NOT in the top-level imports of `test_panel.py`; they are imported locally at line 570 inside `test_normalizer_preserves_decision_columns`. Add them to top-level imports (after `from reformlab.orchestrator.types import ...`) or keep them local per method — either is fine for this story.

### `pyarrow.compute` import pattern

Tests use `import pyarrow.compute as pc` locally (inside test methods) — consistent with the existing test file pattern (see lines 123, 251, 269 in `test_panel.py`). Do not add it as a top-level import.

### What NOT to do

- Do not add tests to `test_panel_decision.py` — the mismatch tests belong with the panel builder tests, not the decision column injection tests. Note: `test_panel_decision.py:384` already contains `TestPanelDecisionSchemaConsistency.test_partial_decisions_concat_with_promote`, which covers a similar scenario (year-1 has decisions, year-2 doesn't) using index-based assertions. The new Test 1 is not redundant — it uses explicit year-filtered assertions (`pc.equal`) and belongs with the panel builder tests. Test 2 (decisions in year-2 only) has no existing coverage anywhere.
- Do not create a new test file — add the class to the existing `test_panel.py`
- Do not use `promote_options="default"` or no promote_options in any new test — the story is specifically about documenting the `"permissive"` behavior
- Do not fix any production code even if a test scenario unexpectedly raises — record it and stop

### Project Structure Notes

- **File to modify:** `tests/orchestrator/test_panel.py` only
- **No production code changes**
- `panel.py` must not import OpenFisca — verify with `grep -n "openfisca" src/reformlab/orchestrator/panel.py` (should be empty)
- New test class: `TestConcatTablesSchemaMismatch` appended at bottom of `test_panel.py`

### Quality Gate Commands

```bash
uv run ruff check src/ tests/
uv run mypy src/
uv run pytest tests/orchestrator/
```

All three must pass with zero new failures.

### References

- [Source: src/reformlab/orchestrator/panel.py:155–163] — both `pa.concat_tables` call sites
- [Source: src/reformlab/orchestrator/panel.py:92,130,136] — `has_any_decision_columns` flag logic
- [Source: tests/orchestrator/test_panel.py] — existing test class structure and helpers
- [Source: tests/orchestrator/test_panel_decision.py:37–73] — `_make_computation_result` and `_make_decision_record` helpers to reference
- [Source: _bmad-output/implementation-artifacts/deferred-work.md] — original deferred entry for this story

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (claude-sonnet-4-6)

### Debug Log References

None. Implementation was a pure test addition with no production code changes.

### Completion Notes List

1. **Both concat paths confirmed** — `panel.py:158` and `panel.py:163` both use `promote_options="permissive"`; the branch is gated by `has_any_decision_columns` (initialized at line 92, set True at lines 130 and 136).
2. **`TestConcatTablesSchemaMismatch` added** — 4 tests covering all ACs: decision-column-in-year-1-only (null fill in year 2), decision-column-in-year-2-only (null fill in year 1), output-column-in-year-1-only (non-decision branch), int64/float64 type promotion.
3. **`DECISION_LOG_KEY` and `DecisionRecord` added to module-level imports** — `_make_minimal_decision_record` helper defined at module level.
4. **Quality gates** — ruff: 0 new errors (3 pre-existing); mypy: 0 new errors (7 pre-existing); pytest tests/orchestrator/: 335 passed, 0 failed.
5. **Code review synthesis fixes (2026-05-23)** — 6 issues applied to `test_panel.py`: (a) vacuous-truth guards: added `assert .num_rows == n` before null-check assertions in all 4 original tests; (b) full decision-column null coverage: tests 1 & 2 now assert `heating_probabilities`, `heating_utilities`, and `decision_domains` are null-filled for the year without a record; (c) tightened type assertion in test 4: `pa.types.is_floating` → `== pa.float64()`; (d) year-2025 value preservation added to test 4; (e) new test 5 `test_output_column_in_second_year_only_fills_null_in_first` (symmetric AC-2 case); (f) new test 6 `test_int_float_type_mismatch_in_decision_branch_promotes_to_float` (locks decision branch path at line 158); (g) removed redundant local import of `DECISION_LOG_KEY`/`DecisionRecord` inside `test_normalizer_preserves_decision_columns`. Final count: 337 passed, 0 failed.

### File List

- `tests/orchestrator/test_panel.py`

## Senior Developer Review (AI)

### Review: 2026-05-23
- **Reviewer:** AI Code Review Synthesis
- **Evidence Score:** 3.3 (avg of 3.4 and 3.2) → REJECT
- **Issues Found:** 8 (6 verified, 2 dismissed)
- **Issues Fixed:** 6
- **Action Items Created:** 1

#### Review Follow-ups (AI)
- [ ] [AI-Review] Medium: Transition-only branch (`TRANSITION_LOG_KEY`, panel.py:131) schema-mismatch across years is untested — consider a follow-up story to add `TestConcatTablesSchemaMismatch.test_transition_column_in_first_year_only_fills_null_in_second` (`tests/orchestrator/test_panel.py`)
