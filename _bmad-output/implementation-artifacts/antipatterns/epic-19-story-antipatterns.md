# Epic 19 - Story Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during validation of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent story-writing mistakes (unclear AC, missing Notes, unrealistic scope).

## Story 19-1 (2026-03-23)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | AC7 conflates PR-verifiable build with post-merge deployment requiring external admin setup, making pass/fail ambiguous | Rewrote AC7 to clearly scope PR acceptance to build/upload success; explicit note that full deploy is a post-merge out-of-band step, not a story blocker. |
| high | AC10 is a compound criterion (4 independent assertions) allowing ambiguous partial-done | Replaced AC10 with 4 labeled atomic sub-criteria (10a–10d) — each independently verifiable; exact task labels now embedded in AC10c eliminating Dev Notes duplication. |
