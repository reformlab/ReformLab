# Story 29.5: Add `pa.concat_tables()` schema-mismatch regression tests

Status: ready-for-dev

## Story

As a backend developer maintaining the orchestrator panel,
I want regression tests covering both `concat_tables` paths in `src/reformlab/orchestrator/panel.py` (the `promote_options="permissive"` decision-column branch and the non-decision branch) against divergent yearly schemas,
so that future schema drift can't silently break panel concatenation across years.

## Acceptance Criteria

1. Given the `pa.concat_tables(..., promote_options="permissive")` call in the decision-column branch of `panel.py`, when a regression test feeds tables with mismatched schemas (e.g., year-N has decision columns, year-N+1 doesn't), then the test asserts the permissive promotion succeeds without raising.
2. Given the non-decision branch in `panel.py`, when a regression test feeds tables with mismatched schemas (e.g., year-N has output column X, year-N+1 lacks it), then the test asserts the existing behaviour — either explicit raise OR documented promotion — and asserts the documented behaviour, locking it for the future.
3. Given the existing test suite at `tests/orchestrator/test_panel.py`, when this story is complete, then it gains tests covering at least four mismatch scenarios: decision-only-in-N, decision-only-in-N+1, output-column-in-N-not-N+1, schema-type-mismatch-with-permissive-promotion.
4. Given the tests, when run, then they pass on the current code.

## Tasks / Subtasks

- [ ] Read current `panel.py` concat paths (AC: #1, #2)
  - [ ] Identify both `pa.concat_tables` call sites and their `promote_options` arguments
  - [ ] Document the current behaviour for each branch
- [ ] Add regression tests (AC: #3)
  - [ ] Test: decision column present in year-1, missing in year-2 → permissive promotion fills with null in year-2
  - [ ] Test: decision column missing in year-1, present in year-2 → permissive promotion fills with null in year-1
  - [ ] Test: non-decision branch with output column missing in one year — assert and lock the current behaviour
  - [ ] Test: schema type mismatch (e.g., int vs float) under permissive — should promote to common type
- [ ] Quality gates
  - [ ] `uv run ruff check src/ tests/`, `uv run mypy src/`, `uv run pytest tests/orchestrator/`

## Dev Notes

- The deferred-work entry was added 2026-04-19 from an adversarial review; the underlying production code has not changed since. This story is pure test addition.
- If the test reveals an actual bug (e.g., the non-decision branch raises in a way that loses data), capture the bug as a follow-up issue but DO NOT fix it in this story.
- The `panel.py` file is part of the orchestrator and should not import OpenFisca (verify this still holds after any test imports are added).

### Project Structure Notes

- Files touched: `tests/orchestrator/test_panel.py`
- No production code changes (unless a bug is found and explicitly approved)
- No new files

### References

- [Source: _bmad-output/implementation-artifacts/deferred-work.md:9] (the original deferred entry)
- [Source: src/reformlab/orchestrator/panel.py]
- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md#Story-29.5]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
