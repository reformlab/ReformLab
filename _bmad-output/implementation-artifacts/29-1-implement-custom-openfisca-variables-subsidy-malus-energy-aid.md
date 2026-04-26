# Story 29.1: Implement custom OpenFisca variables (subsidy_amount, subsidy_eligible, vehicle_malus, energy_poverty_aid)

Status: ready-for-dev

## Story

As a backend developer maintaining the live OpenFisca path,
I want the four French-named output variables (`montant_subvention`, `eligible_subvention`, `malus_ecologique`, `aide_energie`) implemented as custom variables in a registered TaxBenefitSystem extension,
so that the existing `_DEFAULT_OUTPUT_MAPPING` references resolve at runtime and the live path can produce subsidy/malus/energy-aid outputs.

## Acceptance Criteria

1. Given the existing mapping at `src/reformlab/computation/result_normalizer.py` referencing `montant_subvention`, `eligible_subvention`, `malus_ecologique`, and `aide_energie`, when a live OpenFisca run completes, then the four variables resolve and their values appear in the normalised result panel as `subsidy_amount`, `subsidy_eligible`, `vehicle_malus`, and `energy_poverty_aid` respectively.
2. Given the registered TaxBenefitSystem extension under `src/reformlab/`, when inspected, then it defines the four custom variables with appropriate entity assignment, definition_period, value_type, and formula(s) consistent with French tax-benefit conventions.
3. Given the analyst PM has reviewed the `cheque_energie` question (the OpenFisca core variable that may already cover energy-poverty-aid), when this story starts, then the spec records the decision: implement a fresh `aide_energie` OR alias the mapping to `cheque_energie`. Pick one.
4. Given the four custom variables, when invoked on a synthetic population, then they produce non-zero values for households satisfying the eligibility criteria (e.g., subsidy eligible based on income threshold and policy parameters).
5. Given the test suite, when this story is complete, then each custom variable has a unit test asserting: (a) variable resolves at simulation time, (b) value matches expected formula output for at least three test cases, (c) value type and definition period match the variable definition.
6. Given the manifest produced by a live run, when inspected, then it captures the custom variables and the version of the registered extension so reproducibility is preserved.

## Tasks / Subtasks

- [ ] PM decision on `aide_energie` vs `cheque_energie` (AC: #3)
  - [ ] Coordinate with PM (or analyst) to decide whether to implement a fresh `aide_energie` or alias to existing `cheque_energie`
  - [ ] Record the decision in this story's Dev Notes section before implementation
- [ ] Identify or create the registered extension (AC: #2)
  - [ ] Search for the existing TaxBenefitSystem extension under `src/reformlab/computation/` or `src/reformlab/templates/`
  - [ ] If none, create a new extension module (e.g., `src/reformlab/computation/openfisca_extension/`) with a `register()` entrypoint
- [ ] Implement `subsidy_amount` and `subsidy_eligible` (AC: #2, #4)
  - [ ] Define `subsidy_amount` (value_type=float, entity=household, definition_period=year)
  - [ ] Define `subsidy_eligible` (value_type=bool, entity=household, definition_period=year)
  - [ ] Implement formulas using existing parameter inputs from `_DEFAULT_OUTPUT_MAPPING`
- [ ] Implement `vehicle_malus` (AC: #2, #4)
  - [ ] Define `vehicle_malus` (value_type=float, entity=household or person)
  - [ ] Implement formula based on vehicle CO2 emissions parameters (existing `vehicle_co2` columns from population schema)
- [ ] Implement `energy_poverty_aid` (AC: #2, #3, #4)
  - [ ] Either implement fresh `aide_energie` per the PM decision OR add an alias mapping in `_DEFAULT_OUTPUT_MAPPING` to point to `cheque_energie`
- [ ] Register extension in adapter (AC: #2)
  - [ ] Wire the extension into the `ComputationAdapter` initialisation so live runs see the custom variables
  - [ ] Verify no non-computation module imports the extension directly (CLAUDE.md constraint)
- [ ] Tests (AC: #4, #5)
  - [ ] Unit tests for each custom variable (3+ cases each)
  - [ ] Integration test: live run on Quick Test Population produces non-zero values for at least one eligible household
- [ ] Manifest update (AC: #6)
  - [ ] Verify the manifest captures the extension version
  - [ ] If not, add a `custom_variables_version` field
- [ ] Quality gates
  - [ ] `uv run ruff check src/ tests/`, `uv run mypy src/`, `uv run pytest tests/computation/ tests/server/`

## Dev Notes

- This story is the parent of stories 29.2 and 29.3. 29.2 resolves the four generic-name placeholders; 29.3 restores the resolved names in `_DEFAULT_LIVE_OUTPUT_VARIABLES`. Sequence: 29.1 → 29.2 → 29.3.
- The existing mapping in `_DEFAULT_OUTPUT_MAPPING` already uses these French names; we're only implementing the matching variables.
- 2026-04-26 hotfix narrowed `_DEFAULT_LIVE_OUTPUT_VARIABLES` to four resolvable names; this story restores four of the eight that the hotfix excluded.

### Project Structure Notes

- New: `src/reformlab/computation/openfisca_extension/` (or equivalent), with one module per variable group; matching tests under `tests/computation/`
- Modified: `src/reformlab/computation/result_normalizer.py` (only if alias needed for `aide_energie`); manifest writer if version field missing

### References

- [Source: _bmad-output/implementation-artifacts/deferred-work.md:19-25] (the parent context)
- [Source: src/reformlab/computation/result_normalizer.py:71-76] (live output set)
- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md#Story-29.1]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
