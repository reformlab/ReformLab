# Story 28.2: Extend `PopulationData` schema with optional incumbent-technology columns

Status: ready-for-dev

## Story

As a backend developer wiring investment decisions to population data,
I want population tables to optionally carry `incumbent_<domain>` columns (`incumbent_heating`, `incumbent_vehicle`) using PyArrow dictionary encoding, plus a validation helper that fails loud on unknown alternative ids and warns on missing columns,
so that subsequent stories (28.3 writeback, 28.4 wizard, 28.5 regression) have a typed convention to lean on without breaking populations that don't enable decisions.

## Acceptance Criteria

1. Given a population that has `incumbent_heating: dictionary<int32, utf8>` and `incumbent_vehicle: dictionary<int32, utf8>` in its menage entity table, when validated against a `TechnologySet` whose enabled domains include both, then `validate_population_for_technology_set()` returns `[]` (no warnings, no errors).
2. Given a population missing `incumbent_<domain>` for a domain that is enabled, when validated, then the helper returns a human-readable warning string ("Population lacks `incumbent_heating`; all households will start at the reference alternative `keep_current`"); the run proceeds.
3. Given a population whose `incumbent_<domain>` column contains values not present in `TechnologySet.domains[d].alternatives`, when validated, then the helper raises a hard error (e.g., `PopulationSchemaError`) listing the unknown ids and household counts. The run does NOT proceed.
4. Given the bundled `fr-synthetic-2024` population, when this story is complete, then it includes `incumbent_heating` and `incumbent_vehicle` columns derived deterministically from the existing `heating_type` / `vehicle_type` attribute columns. Row count, household_id values, and all other columns are unchanged. A test asserts byte-stable output (same seed → same population).
5. Given the Quick Test Population, when this story is complete, then it includes both incumbent columns derived the same way.
6. Given the data-fusion pipeline (Story 22 / `DataFusionWorkbench`), when fusion completes, then incumbent columns are written at the end of the pipeline using the same alternative-id mapping rule used for the bundled populations. Existing fusion output for non-incumbent columns is unchanged.
7. Given a user-uploaded population without `incumbent_*` columns, when used in a scenario with `investmentDecisionsEnabled === false`, then the run is unaffected (no validation runs).
8. Given a user-uploaded population without `incumbent_*` columns, when used in a scenario with `investmentDecisionsEnabled === true`, then the run proceeds, the manifest records a warning, and all households are treated as starting at the reference alternative.

## Tasks / Subtasks

- [ ] Validation helper (AC: #1, #2, #3, #7, #8)
  - [ ] New module `src/reformlab/discrete_choice/population_validation.py`
  - [ ] Implement `validate_population_for_technology_set(population, technology_set, *, entity_key="menage") -> list[str]`
  - [ ] No-op when `technology_set is None or not any(d.enabled for d in technology_set.domains.values())`
  - [ ] Return warnings for missing columns; raise `PopulationSchemaError` for unknown alternative ids
- [ ] Wire validation into orchestrator (AC: #2, #3, #8)
  - [ ] In `src/reformlab/orchestrator/runner.py`, call the helper at scenario start when `investmentDecisionsEnabled === true`
  - [ ] Capture returned warnings into the manifest's existing warning surface (`RunManifest` already has a warnings field — verify and use it)
- [ ] Bundled-population migration (AC: #4)
  - [ ] Locate the `fr-synthetic-2024` generation script (search for `fr-synthetic-2024` or the data file path)
  - [ ] Add a deterministic mapping `heating_type → incumbent_heating` and `vehicle_type → incumbent_vehicle` using the canonical alternative ids from Story 28.1's API
  - [ ] Regenerate the population data artifact; commit it alongside the script change
  - [ ] Add a regression test asserting row count, household_ids, and existing columns are unchanged; new incumbent columns have expected non-null counts
- [ ] Quick Test Population migration (AC: #5)
  - [ ] Same migration; this is a tiny ~10-household fixture, trivial change
- [ ] Data-fusion pipeline (AC: #6)
  - [ ] Locate the fusion writer in `src/reformlab/data/fusion/` (or wherever the fused output is written)
  - [ ] Add the incumbent-column write step at the end of the fusion pipeline
  - [ ] Add a fusion-output test asserting incumbent columns are present and dictionary-encoded
- [ ] PyArrow type assertion (AC: #1, #4)
  - [ ] Validation helper checks the column type is `pa.dictionary(pa.int32(), pa.utf8())`; if a writer produced a plain `pa.utf8()` column, normalise via dictionary encoding before consumption
- [ ] Quality gates
  - [ ] `uv run ruff check src/ tests/`, `uv run mypy src/`, `uv run pytest tests/discrete_choice/ tests/data/ tests/orchestrator/`
  - [ ] `npm test` for any frontend reads of population data (likely none affected)

## Dev Notes

- **No frontend changes** in this story (other than possibly the data-fusion UI status reporting if it reads column lists, which is unlikely).
- This story depends on Story 28.1 (`TechnologySet` types). It is the gating dependency for 28.3 and 28.4.
- The dictionary encoding choice (`pa.dictionary(pa.int32(), pa.utf8())`) is mandated by the spike's Section 3.3. Do not store the column as plain `pa.utf8()` — eligibility filters and joins downstream rely on `is_in` semantics that work cleanly only on dictionary-encoded columns.
- Migration is one-shot; do not write a generic forward-migration helper for arbitrary populations. User-uploaded populations get the warning-and-default-to-reference path (AC #8) instead of a migration.

### Project Structure Notes

- New files: `src/reformlab/discrete_choice/population_validation.py`, matching tests
- Modified: `src/reformlab/orchestrator/runner.py`, the `fr-synthetic-2024` and Quick Test generation scripts, the data-fusion pipeline writer
- Population data artifacts (parquet files) regenerated; commit them
- No deletions

### References

- [Source: _bmad-output/planning-artifacts/spike-investment-decisions-technology-set-2026-04-26.md#Section-3]
- [Source: src/reformlab/computation/types.py:19] (PopulationData)
- [Source: Story 28.1] (TechnologySet contract)

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
