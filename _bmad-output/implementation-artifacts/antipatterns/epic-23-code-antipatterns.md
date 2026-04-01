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
