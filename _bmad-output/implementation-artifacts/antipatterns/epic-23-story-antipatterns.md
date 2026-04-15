# Epic 23 - Story Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during validation of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent story-writing mistakes (unclear AC, missing Notes, unrealistic scope).

## Story 23-4 (2026-04-15)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | household_id contradiction in Task 1 | Removed "plus household_id for join stability" from Task 1 line 29 since Dev Notes correctly state household_id is NOT an output variable (it's an input from population data) |
| critical | Fallback guard checks wrong path | Changed from `result.manifest.runtime_mode` to `result.metadata.get("runtime_mode")` to match Story 23.3's implementation |
| critical | Missing REFORMLAB_RUNTIME_MODE validation | Added validation that checks if value is "live" or "replay", logs warning for invalid values, and defaults to "live" |
| critical | Exception handling too broad | Specified more specific exceptions: `(FileNotFoundError, OSError)` for replay path, `(OSError, RuntimeError)` for live path initialization failures |
| high | Replay exception handling narrow | Expanded to catch `ValueError` in addition to `FileNotFoundError` for precomputed data validation errors |
| high | AC3 not objectively verifiable | Added specific invariants: metadata.json, panel.parquet, manifest.json persistence, cache retrieval, and post-eviction reload behavior |
| high | AC4 runtime fallback conditions undefined | Defined specific fallback conditions (OpenFisca not installed, adapter init failure) and explicit MockAdapter behavior |
| high | Env var precedence unclear | Added "Env Var Precedence" section explaining that REFORMLAB_RUNTIME_MODE sets global adapter at startup, but per-request mode overrides for replay only |
| medium | Test approach unclear for fallback guard | Clarified test should create SimulationResult with mismatched runtime_mode in metadata |
| medium | Test references metadata.source which is undefined | Updated test descriptions to reference metadata.runtime_mode instead, with note that this field is set by Story 23.3's normalizer |
| low | MockAdapter vs SimpleCarbonTaxAdapter inconsistency | Added explanatory notes that this is intentional (server uses MockAdapter for dev/test, API uses SimpleCarbonTaxAdapter for demos) |
