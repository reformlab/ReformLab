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
