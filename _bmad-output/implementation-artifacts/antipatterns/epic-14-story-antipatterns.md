# Epic 14 - Story Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during validation of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent story-writing mistakes (unclear AC, missing Notes, unrealistic scope).

## Story 14-1 (2026-03-06)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | Dual CostMatrix representation (`pa.Table` or `dict[str, pa.Array]`) allows incompatible implementations | Mandated single `pa.Table` representation, removed "Or: dict mapping" branch |
| high | Cost extraction ownership split between `reshape_to_cost_matrix(cost_column)` and `DecisionDomain.extract_cost()` | Replaced `extract_cost` method with `cost_column` property on protocol; reshape uses column name from domain |
| high | Tracking column naming inconsistency (`_original_household_index` vs `_original_index`) | Normalized to `_original_household_index` everywhere |
| high | AC-4 didn't specify whether reshape uses tracking columns or positional row order | AC-4 now explicitly states tracking-column-based reshape, not positional |
| medium | AC-3 mandates batch compute call but edge case says N=0 skips adapter | Added explicit exception in AC-3 for N=0 |
| medium | No validation for invalid choice sets (M=0, duplicate IDs) | Added M≥1 and unique ID requirements to AC-2 and edge case table |
| medium | State payload types unspecified | AC-7 now defines exact types stored under each key |
| medium | Task 3.3 allowed "StructArray or dict of arrays" | Now specifies `pa.Table` with tracking-column-based reshape |
| low | Task 6.2 "add mypy overrides if needed" too permissive | Tightened to "no new overrides expected" |

## Story 14-2 (2026-03-06)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | Metadata key inconsistency — Task 4.4 says `seed` but Dev Notes State Key Integration section says `choice_seed` | Standardized on `choice_seed` in both Task 4.4 and AC-8. Also clarified immutability pattern in both locations. |
| high | AC-4 statistical test is under-specified — "chi-squared or similar for large N" is ambiguous, could lead to scipy dependency or flaky tests | Replaced with concrete tolerance formula using standard error bounds, specified N ≥ 1000, no external library. Updated matching Testing Standards entry. |
| medium | AC-8 "extending" language could be misread as dict mutation, violating frozen dataclass principle | Rewrote AC-8 to explicitly state "creating a new dict" and "never mutate the existing dict in-place", with `dataclasses.replace()` reference. |
| medium | NaN/Inf handling documented only in edge case table, not enforceable via ACs | Added fail-fast `LogitError` requirement with invalid cell positions to AC-1. |
| low | Missing module docstring task for `logit.py` | Not applied — this is a standard project convention documented in `project-context.md` that all dev agents follow. Adding explicit tasks for every convention would bloat the story. |

## Story 14-3 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | Missing validation for unknown alternative IDs in `ChoiceResult.chosen` | Added Task 3.9 (validate all IDs exist in `alt_map`), added validation block to algorithm pseudocode, added unknown-ID test to Task 6.5, added edge case row, added explicit statement in AC-6. |
| medium | AC-3 type mismatch behavior undefined when attribute value is incompatible with existing column type | AC-3 now explicitly states incompatible casts wrap `ArrowInvalid` in `DiscreteChoiceError`. Type inference rules pseudocode updated with try/except pattern. Edge case row added. |
| medium | Task 3.5 type inference wording inconsistent with `_infer_pa_type` mapping rules | Task 3.5 now explicitly references `_infer_pa_type` mapping and `pa.array(..., type=existing_type)` cast pattern. |
| medium | AC-6 positional alignment between `ChoiceResult.chosen` and entity table underspecified | AC-6 now states positional alignment is guaranteed by upstream pipeline and that unknown IDs raise errors. |
| medium | Empty population edge case conflicts with AC-9 metadata extension | Edge case row clarified: population and vintage unchanged, but metadata is still extended with zero counts. |

## Story 14-4 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | AC-11 lacks explicit dependency chain and test assertions for sequential multi-domain execution | AC-11 now specifies the full 6-step dependency chain with naming convention and requires the integration test to verify vehicle attribute presence in heating's population. |
| high | AC-9 metadata preservation semantics are ambiguous for sequential execution | AC-9 now explicitly requires preservation of all pre-existing metadata keys and raises DiscreteChoiceError on non-dict metadata. |
| medium | AC-3 omits explicit `bool` type handling | AC-3 now lists `bool` alongside other unsupported types. |
| medium | AC-8 zero-switcher/no-existing-vintage behavior is implicit | AC-8 now explicitly states that no empty VintageState is created when there are zero switchers and no existing state. |
| medium | AC-10 import path change in `__init__.py` is implied but not stated | AC-10 now explicitly states the import source changes from `vehicle` to `domain_utils`. |
| medium | Design Decision #8 doesn't explain metadata key preservation in sequential mode | DD#8 now documents how domain-prefixed metadata keys coexist and that final results use separate vintage keys. |
| low | AC-3 "returned unchanged" vs "new table" ambiguity | Addressed as part of the AC-3 update — clarified that identity return is acceptable since PyArrow tables are immutable. |
| low | LLM token efficiency improvements (redundant protocol blocks, algorithm code) | Not applied. The story is already written and the dev agent context benefits from having protocol definitions inline. Removing them risks implementation errors. |

## Story 14-6 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | `capture_discrete_choice_parameters()` hardcodes `"discrete_choice_decision_log"` string literal instead of importing `DECISION_LOG_KEY` | Updated Design Decision #8 to require import; updated code example to add `from reformlab.discrete_choice.decision_record import DECISION_LOG_KEY` and use the constant instead of the raw string. |
| high | AC-5 states "all years use the same taste parameters" which is incorrect for `choice_seed` — seeds are derived as `master_seed XOR year` and vary per year | Updated AC-5 to distinguish static taste parameters (`beta_cost`) from year-varying `choice_seed`; added clarification that the seed log already provides the authoritative per-year record and that per-year seeds can be recomputed from the manifest's master seed. |
| high | No behavior specified for duplicate `domain_name` in one year's decision log; `_build_decision_columns()` would silently produce duplicate PyArrow column names | Added duplicate domain_name row to edge cases table (raises `DiscreteChoiceError`); added uniqueness validation code block at the top of `_build_decision_columns()`. |
| medium | `taste_parameters: dict[str, float]` and `eligibility_summary: dict[str, int] | Added "treat as logically immutable after construction" convention note to both fields in AC-1. |
| medium | AC-5 does not specify whether `"discrete_choice_parameters"` manifest key is always present or only when non-empty | Added explicit "only when non-empty (key is absent for non-discrete-choice runs)" clause to AC-5. |
| low | `DecisionRecord.probabilities` and `utilities` are `pa.Table` internally but `pa.list_(pa.float64())` in the panel — the transformation is only in Dev Notes code, not in ACs | Added note to AC-1 field descriptions and AC-3 column descriptions clarifying the `pa.Table` → `pa.list_` transformation. |

## Story 14-7 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | `PopulationData` uses `.tables` not `.entities` | All 4 code snippets updated to `population.tables.get(...)`, `PopulationData(tables={...})`, `pop.tables[...]` |
| critical | `PolicyConfig` constructor uses `policy=` not `parameters=` | Edge Cases table updated to `PolicyConfig(policy={...}, name="carbon_tax_2025")` |
| critical | Task 3.4 forbids `reformlab.computation` imports but notebook requires `mock_adapter` and `types` from that package | Task 3.4 now explicitly whitelists `reformlab.computation.mock_adapter` and `reformlab.computation.types`; forbidden imports are now `reformlab.computation.adapter` and `reformlab.computation.openfisca` |
| high | Pipeline step count stated as "12-step (6 per domain)" but only 5 steps listed per domain = 10 total | Corrected to "10-step pipeline (5 per domain)" |
| high | AC-10 referred to "run manifest" ambiguously, conflicting with notebook using `Orchestrator` (not `OrchestratorRunner`) | AC-10 now explicitly specifies `capture_discrete_choice_parameters(result.yearly_states)` as the mechanism |
| high | `MockAdapter.compute_fn` behavioral contract too vague to guarantee pedagogically meaningful demo | Task 1.5 now specifies that costs must increase with `carbon_emissions` × carbon tax rate, decrease for EV alternatives by subsidy amount, and vary meaningfully across alternatives |
| medium | AC-9 redundantly required CI workflow check (already covered by AC-8) | Removed "and CI workflow includes the notebook" clause from AC-9 |
| medium | AC-2 missing `heating_age` attribute needed for realistic heating eligibility filtering | Added `heating_age` to AC-2 required attribute list; added requirement that attributes must be demonstrably used by `compute_fn` |
