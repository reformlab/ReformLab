# Epic 23 - Code Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during code review of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent implementation mistakes (race conditions, missing tests, weak assertions, etc.)

## Story 23-1 (2026-04-01)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Bug: Portfolio run ignores `runtime_mode` | Added `runtime_mode=body.runtime_mode` to `RunConfig` constructor in `_run_portfolio()` |
| critical | Bug: `ResultDetailResponse` always returns default `"live"` | Added `runtime_mode=meta.runtime_mode` to `ResultDetailResponse` constructor with validation and cast |
| high | `RunManifest.runtime_mode` lacks construction-time validation | Added runtime_mode validation in `_validate()` method, ensuring only "live" or "replay" values pass |
| high | Unnecessary `cast()` in runs.py | Kept cast (still needed due to `str` vs `Literal` type mismatch with `from __future__ import annotations`), but validated at `_validate()` boundary |
| medium | Test file in wrong location | Deferred to review follow-up task (tests work correctly, just need relocation) |
| low | Story 22.7 scope bleed in git history | Deferred to review follow-up task (git history concern, not a code defect) |

## Story 23-2 (2026-04-03)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | `_metadata_to_detail()` in `results.py` omits `population_source` — `GET /api/results/{run_id}` always returns `null` for this field | Added `population_source=` with validation and cast to `ResultDetailResponse` constructor |
| high | `frozenset` iteration order is non-deterministic under `PYTHONHASHSEED` randomization — if both `.csv` and `.parquet` exist for same ID, selected file varies between runs | Changed `frozenset` to ordered `tuple` with explicit preference (Parquet first) |
| high | Unsanitized `population_id` used in path construction allows traversal to arbitrary filesystem locations | Added input validation guard rejecting IDs with `/`, `\`, `..`, or empty strings; added `is_relative_to()` check for `descriptor.json` `data_file` values |
| dismissed | Failure metadata regression on 404 population resolution — missing population returns 404 without persisted metadata | FALSE POSITIVE: The 404 occurs before a `run_id` is created and before execution starts. There is no run to persist metadata for. This is consistent with how other pre-execution validation errors (e.g., portfolio not found at line 263) behave. |
| dismissed | Route bypasses FastAPI DI contract — resolver not injected via `Depends()` | FALSE POSITIVE: `get_adapter()` in the same function follows the identical pattern (line 75 — called directly, not via `Depends`). This is a consistent codebase convention for singletons that don't need request-scoped lifecycle. Changing one without the other would create inconsistency. |
