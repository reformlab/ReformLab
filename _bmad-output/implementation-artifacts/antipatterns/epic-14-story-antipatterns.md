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
