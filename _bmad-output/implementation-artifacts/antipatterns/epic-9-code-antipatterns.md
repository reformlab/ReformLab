# Epic 9 - Code Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during code review of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent implementation mistakes (race conditions, missing tests, weak assertions, etc.)

## Story 9-2 (2026-03-01)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | `metadata["output_entities"]` and `metadata["entity_row_counts"]` were computed from the pre-filter `entity_tables` dict, then `entity_tables` was conditionally cleared to `{}` for single-entity results. This left the two metadata fields populated (e.g. `["individus"]`) while `result.entity_tables` was empty — contradictory observable state that violates the "data contracts fail loudly" architectural principle. | Introduced `result_entity_tables` computed before metadata; both metadata fields and the `entity_tables` field now derive from the same filtered value. |
| high | `__init__` accepted `output_variables=()` without error. The empty tuple flowed through `_resolve_variable_entities` (returning `{}`), `_extract_results_by_entity` (returning `{}`), and `_select_primary_output({}, tbs)` which called `next(iter({}.values()))` → bare Python `StopIteration` with no diagnostic. | Added early guard at top of `__init__` raising `ApiMappingError` with clear message. |
| high | `_resolve_variable_entities` was called *after* `_build_simulation`, meaning the expensive `SimulationBuilder.build_from_entities()` call ran even when entity resolution would fail immediately after. Violates fail-fast principle. | Moved `_resolve_variable_entities` call to before `_build_simulation`. |
| medium | Comment at line 430 read `# Fallback: try entity.key + "s" if plural is missing` but the code immediately below assigned `entity_plural = entity_key` (no `+ "s"`). Beyond the comment being wrong, the silent fallback itself was incorrect: for French entities, `foyer_fiscal` → `foyers_fiscaux` (not `foyer_fiscals`), so the fallback would produce wrong dict keys causing misleading downstream lookup failures. | Replaced the entire fallback block with an `ApiMappingError` that fires whenever `entity.plural` is `None`, regardless of whether `entity.key` is present. Real OpenFisca TBS entities always have `.plural`; absence signals an incompatible TBS. |
| medium | `test_compute_single_entity_backward_compatible` verified `entity_tables == {}` but never asserted on `metadata["output_entities"]` or `metadata["entity_row_counts"]`, allowing the metadata/entity_tables inconsistency (Critical bug above) to go undetected. | Added two assertions with a comment explaining the regression guard intent. |
| low | Story file had `Status: ready-for-dev` and all 7 tasks marked `[ ]` despite full implementation being delivered. Governance integrity violation — team members reading the story would assume nothing had been built. | Set `Status: done`, all tasks checked `[x]`, synthesis completion notes appended to Dev Agent Record. |

## Story 9-3 (2026-03-01)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | `from typing import Any` missing in unit test file | Added `from typing import Any` to import block. `Any` was used as a local variable annotation at lines 62 and 128 (`variables: dict[str, Any] = {}`). With `from __future__ import annotations`, this doesn't cause a runtime error but mypy strict mode would flag it as an undefined name. |
| medium | AC-3 "FIRST" ordering constraint untested — existing `TestPeriodValidation` tests pre-load the TBS via `adapter._tax_benefit_system = mock_tbs`, so the tests pass whether `_validate_period()` runs before or after `_get_tax_benefit_system()` | Added `test_period_validation_precedes_tbs_loading` — does NOT pre-load TBS, asserts `adapter._tax_benefit_system is None` before and after raising the error. |
| medium | Dead code in `test_compute_entity_detection_error` — `mock_builder_instance`, `mock_simulation`, and `_patch_simulation_builder` context are set up but never used because the error fires in `_resolve_variable_entities()` before `_build_simulation()` | Removed 3 dead mock setup lines and the `_patch_simulation_builder` wrapper; replaced with a plain `pytest.raises` block plus explanatory comment. |
| medium | Misleading comment on the mock `definition_period` fix — the comment in `_make_mock_tbs()` lacked the accurate explanation of *why* the attribute must be set | Rewrote comment to explain that a `MagicMock` definition_period's `str()` returns `"<MagicMock ...>"` which is not in `_VALID_PERIODICITIES`, causing `ApiMappingError("Unexpected periodicity")` — not silent dispatch to `calculate_add()`. |
| low | Missing test for empty `output_variables` guard — `__init__` raises `ApiMappingError` on empty tuple but no test covered this | Added `test_empty_output_variables_raises_error` to `TestOutputVariableValidation`. |
| low | DRY violation — the `calculate` vs `calculate_add` dispatch decision was duplicated between `_calculate_variable()` and the `calculation_methods` dict-comprehension in `compute()`. Adding a new periodicity to `_CALCULATE_ADD_PERIODICITIES` would update the runtime dispatch automatically but silently leave the metadata reporting stale | Extracted `_periodicity_to_method_name(periodicity: str) -> str` module-level helper; both `_calculate_variable()` and `compute()` now call it as the single source of truth. |
