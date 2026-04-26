# Story 29.3: Restore resolved names in `_DEFAULT_LIVE_OUTPUT_VARIABLES`

Status: ready-for-dev

## Story

As a backend developer wrapping up the live-output recovery,
I want `_DEFAULT_LIVE_OUTPUT_VARIABLES` at `src/reformlab/computation/result_normalizer.py:71-76` to include all the names that 29.1 and 29.2 made resolvable,
so that live OpenFisca runs produce the full intended output set instead of the four-name minimum the 2026-04-26 hotfix established.

## Acceptance Criteria

1. Given stories 29.1 and 29.2 have landed, when `_DEFAULT_LIVE_OUTPUT_VARIABLES` is updated, then it includes: the original four (`revenu_disponible`, `impots_directs`, `salaire_net`, `prestations_sociales`) plus the four custom variables from 29.1 (`montant_subvention`, `eligible_subvention`, `malus_ecologique`, `aide_energie` or alias) plus the resolved names from 29.2 (`impot_revenu_restant_a_payer`, `taxe_carbone`, plus optional `revenu_brut` per the 29.2 decision).
2. Given a live run on the Quick Test Population, when complete, then the result panel contains all the variables in the new `_DEFAULT_LIVE_OUTPUT_VARIABLES` list with non-error values (zeros are acceptable for households not subject to the policy).
3. Given the manifest produced by a live run, when inspected, then the `output_variables` field reflects the new full set.
4. Given the existing tests at `tests/computation/test_result_normalizer.py`, when this story is complete, then assertions on the live output set are updated to expect the new full list.
5. Given the existing live integration tests, when run, then they pass without manifest-shape regressions and runtime errors caused by missing variables are absent.

## Tasks / Subtasks

- [ ] Update `_DEFAULT_LIVE_OUTPUT_VARIABLES` (AC: #1)
  - [ ] Edit `src/reformlab/computation/result_normalizer.py:71-76` to include the new full list
  - [ ] Group with comments showing provenance (core / custom-29.1 / resolved-29.2)
- [ ] Update tests (AC: #4)
  - [ ] `tests/computation/test_result_normalizer.py` assertions on live output set
  - [ ] Any other tests that pin the output list
- [ ] Manifest verification (AC: #3)
  - [ ] Add or update a test that runs a live scenario and asserts the manifest's `output_variables` field matches the new list
- [ ] Smoke test on Quick Test Population (AC: #2)
  - [ ] Run a live scenario end-to-end and inspect the panel result
- [ ] Quality gates
  - [ ] `uv run ruff check src/ tests/`, `uv run mypy src/`, `uv run pytest tests/computation/`

## Dev Notes

- This story is small but blocks on 29.1 and 29.2. Sequencing: 29.1 → 29.2 → 29.3 is mandatory.
- The 2026-04-26 hotfix that narrowed the list explained: "live computation was failing at year 2025 because eight names in `_DEFAULT_OUTPUT_MAPPING` did not resolve in core `openfisca_france`". This story closes the loop on those eight names.

### Project Structure Notes

- Files touched: `src/reformlab/computation/result_normalizer.py`, `tests/computation/test_result_normalizer.py`, possibly other test files
- No new files

### References

- [Source: _bmad-output/implementation-artifacts/deferred-work.md:19-25]
- [Source: src/reformlab/computation/result_normalizer.py:71-76]
- [Source: stories 29.1 and 29.2]
- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md#Story-29.3]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
