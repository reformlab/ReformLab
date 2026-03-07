# Epic 14 - Code Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during code review of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent implementation mistakes (race conditions, missing tests, weak assertions, etc.)

## Story 14-1 (2026-03-06)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | Reshape silently overwrites duplicate `(household, alternative)` cells and leaves missing cells as None | Added duplicate cell detection (raises ReshapeError) and post-loop completeness check verifying all cells are filled. |
| high | `pa.concat_tables` failure in expansion produces raw ArrowInvalid instead of ExpansionError | Wrapped `pa.concat_tables(segments)` in try/except, raises ExpansionError with entity/domain context. |
| high | `CostMatrix` accepts invalid internal state — no validation that columns match alternative_ids | Added `__post_init__` that validates `table.column_names` matches `alternative_ids` exactly. |
| medium | `ExpansionResult.population` typed as `Any`, weakening mypy strict | Added `TYPE_CHECKING` guard with `PopulationData` import, changed type to `PopulationData`. |
| medium | `_get_population` method scans all state values, potentially picking wrong PopulationData | Replaced with explicit `population_key` constructor parameter (default: `"population_data"`), direct dict lookup. |
| medium | Redundant `isinstance(exc, Exception)` checks in `except Exception as exc` blocks | Simplified to `original_error=exc` (4 occurrences). |
| low | `apply_alternative` docstring implies in-place mutation | Clarified "Return a new table" and noted PyArrow table immutability. |
| low | `type: ignore[arg-type]` for `population=None` in tests | Replaced with minimal `PopulationData` instances. |

## Story 14-2 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | `draw_choices` returns `utilities=probabilities` — semantically wrong ChoiceResult when called outside LogitChoiceStep | Added `utilities: pa.Table` parameter to `draw_choices`, removed the `ChoiceResult` re-construction hack in `LogitChoiceStep.execute()`. Public API now always produces correct ChoiceResult. |
| medium | AC-4 test checks only one alternative's frequency instead of all alternatives | Rewrote `test_stochastic_variation_aggregate_consistency` to iterate over all alternatives with per-alternative tolerance assertion. |
| medium | `seed=None` governance warning only at step level, not in pure function | Added `logger.warning` in `draw_choices` when `seed is None`. |
| medium | `dict(existing_metadata)` can throw raw `TypeError` if metadata is not a dict | Added `isinstance(existing_metadata, dict)` guard with `DiscreteChoiceError`. |
| low | `test_result_fields_populated` only checks types, not semantic correctness of utilities | Updated test to use distinct utility values and assert they are correctly stored (not copied from probabilities). |

## Story 14-3 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | `apply_choices_to_population` raises raw `KeyError` when `entity_key` not in `population.tables` | Added explicit key check with `DiscreteChoiceError` listing available keys |
| medium | Non-dict metadata silently reset to `{}` instead of fail-loud error, inconsistent with `LogitChoiceStep.execute()` pattern | Changed to raise `DiscreteChoiceError` with type information, matching `logit.py:330-336` |
| medium | Existing `VintageState` with wrong `asset_class` (e.g., "heating") merged without validation, allowing state contamination | Added `asset_class != "vehicle"` validation before merge, raising `DiscreteChoiceError` |
| low | `sorted(unknown_ids)` can throw `TypeError` for heterogeneous types in edge cases | Changed to `sorted(str(x) for x in unknown_ids)` for robust formatting |

## Story 14-5 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | `EligibilityMergeStep.execute()` throws raw `IndexError` on inconsistent EligibilityInfo/ChoiceResult lengths | Added three invariant checks before the merge loop: `n_eligible == len(eligible_indices)`, `0 <= n_eligible <= n_total`, and `len(choice_result.chosen) == n_eligible` — each raises `DiscreteChoiceError` on violation. |
| critical | Invalid `EligibilityInfo` (e.g., `n_eligible=10, n_total=3`) silently produces `eligibility_merge_n_defaulted=-7` | Covered by the same invariant checks above (`0 <= n_eligible <= n_total`). |
| high | `TestFullPipelineIntegration.test_pipeline_with_eligibility` stops at `EligibilityMergeStep`, leaving AC-7 ("population attributes unchanged, no vintage entry created") unverified | Added `test_pipeline_with_state_update_ac7()` — runs full pipeline through `VehicleStateUpdateStep`, asserts ineligible households have unchanged `vehicle_type` and vintage cohort count is bounded by eligible household count. |
| medium | `evaluate_eligibility()` leaks raw `ArrowNotImplementedError`/`ArrowTypeError` when threshold type is incompatible with column type (e.g., string threshold on numeric column) | Wrapped `op_fn(col, rule.threshold)` in `try/except (pa.ArrowNotImplementedError, pa.ArrowTypeError, pa.ArrowInvalid)` raising `DiscreteChoiceError` with rule context. |
| medium | `filter_population_by_eligibility()` leaks raw `ArrowInvalid` when mask length doesn't match table length | Wrapped `table.filter(eligible_mask)` in `try/except (pa.ArrowInvalid, pa.ArrowTypeError)` raising `DiscreteChoiceError` with entity key context. |

## Story 14-6 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| medium | Eligibility `n_eligible`/`n_ineligible` values not validated as `int` before storing in `dict[str,int]` | Added `isinstance(..., int)` guards before storing; falls back to safe defaults on type mismatch |
| medium | No row-count invariant check before appending decision columns — PyArrow error would be cryptic | Added explicit check raising `DiscreteChoiceError` with row count context |
| medium | No upfront validation that probabilities/utilities tables contain columns for all `alternative_ids` — `KeyError` from Arrow leaks uncontextually | Added pre-loop column presence validation with `DiscreteChoiceError` |
| medium | O(N×M) per-cell Arrow bridge crossings (`column(aid)[i].as_py()`) — scales poorly at 100k households | Vectorized with `column(aid).to_pylist()` per alternative (O(M) Arrow calls, then pure Python list comprehension) |
| low | CSV test only checks for column name in raw text, not list serialization format | Added assertions for bracket presence in data rows and correct line count |
