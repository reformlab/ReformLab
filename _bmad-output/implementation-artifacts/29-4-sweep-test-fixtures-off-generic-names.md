# Story 29.4: Sweep test fixtures off the generic names

Status: ready-for-dev

## Story

As a backend developer cleaning up test hygiene,
I want every test fixture that uses the generic placeholder names (`irpp`, `revenu_net`, `revenu_brut`, `taxe_carbone`) replaced with the real OpenFisca-France names from Story 29.2,
so that the test suite stops encoding the convention that blew up production on 2026-04-26.

## Acceptance Criteria

1. Given the test files identified in `deferred-work.md` (`tests/computation/test_result_normalizer.py:148-149`, `tests/computation/test_normalization_regression.py`, `tests/computation/test_openfisca_api_adapter.py` (many sites), `tests/orchestrator/test_panel.py:518`), when this story is complete, then no fixture references `irpp`, `revenu_net`, `revenu_brut`, or `taxe_carbone` as a synthetic PyArrow column name.
2. Given the renaming decisions from Story 29.2, when fixtures are updated, then they use `impot_revenu_restant_a_payer`, `taxe_carbone` (custom variable name — same as before but now real), and either drop `revenu_net`/`revenu_brut` or rename per 29.2's decision.
3. Given the existing assertions in those tests, when the fixtures are renamed, then the assertions also use the renamed columns and continue to pass.
4. Given a final repo-wide grep for the four generic names in `tests/`, when run, then it returns zero hits in non-comment lines.

## Tasks / Subtasks

- [ ] Enumerate fixture sites
  - [ ] `grep -rn "irpp\|revenu_net\|revenu_brut\|taxe_carbone" tests/`
  - [ ] Build a checklist of files and line numbers
- [ ] Update `test_result_normalizer.py` (AC: #1, #3)
  - [ ] Lines 148-149 and any other sites
- [ ] Update `test_normalization_regression.py` (AC: #1, #3)
- [ ] Update `test_openfisca_api_adapter.py` (AC: #1, #3)
  - [ ] Audit said "many sites" — enumerate and update each
- [ ] Update `test_panel.py:518` (AC: #1, #3)
- [ ] Final grep (AC: #4)
  - [ ] Confirm zero hits in non-comment lines
  - [ ] If any hits remain, decide whether they're intentional regression markers or genuine sweeps
- [ ] Quality gates
  - [ ] `uv run pytest tests/`

## Dev Notes

- This story depends on Story 29.2 because the renaming decisions live there.
- This is purely test hygiene. No production code changes.
- `taxe_carbone` may stay if Story 29.2 implemented it as a custom variable — the fixture name doesn't change but the underlying meaning does.

### Project Structure Notes

- Files touched: the four test files identified, plus any others surfaced by grep
- No production code changes
- No new files

### References

- [Source: _bmad-output/implementation-artifacts/deferred-work.md:19-25]
- [Source: Story 29.2 (renaming decisions)]
- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md#Story-29.4]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
