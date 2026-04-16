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

## Story 23-6 (2026-04-16)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Wrong API endpoint references for indicators | Changed `POST /api/indicators/compute` to `POST /api/indicators/{indicator_type}` throughout Task 5, test patterns, and documentation template |
| critical | Wrong API endpoint reference for comparisons | Changed `POST /api/results/compare` to `POST /api/comparison` throughout Task 6, test patterns, and documentation template |
| critical | Non-existent metadata and panel endpoints | Removed references to `GET /api/results/{run_id}/metadata` and `GET /api/results/{run_id}/panel`, replaced with `GET /api/results/{run_id}` for result details |
| critical | Unrealistic 5 SP estimate for declared scope | Updated estimate from 5 SP to 8 SP in story header and Dev Agent Record |
| critical | Generated population test underspecified | Replaced vague "data fusion or generator" with explicit CSV + manifest sidecar fixture pattern in Task 3 and Implementation Notes |
| critical | Documentation test only checks file existence | Added `test_docs_contain_population_diagnostics()`, `test_docs_contain_mapping_diagnostics()`, and `test_docs_include_investigation_checklist()` to Task 9 |
| critical | Test data assumptions not validated | Added explicit fixture setup for bundled populations in Task 1 with `tmp_path` creation instead of assuming external data |
| critical | Preflight warning expectation conflicts with MockAdapter | Added adapter-aware guidance in Testing Standards and fixture patterns to expect warnings with MockAdapter, no warnings with real adapter |
| critical | Out-of-scope feature expectations | Removed Parquet schema metadata and replication package export references from Task 7 and Scope Boundaries, keeping only export endpoint functionality |
| critical | Vague self-referential acceptance criteria | Rewrote ACs 1-4 to be objective statements of system capabilities rather than tests of tests |
| high | Missing error scenario tests | Added `test_bundled_population_not_found_returns_error()` to Task 1, `test_indicator_computation_fails_without_panel()` to Task 5, `test_comparison_with_nonexistent_run_fails()` to Task 6, `test_export_without_panel_fails()` to Task 7 |
| medium | Missing portfolio comparison regression test | Not applied - Story 23.4 portfolio feature is out of scope for this regression story, which focuses on basic live/replay smoke paths |
| medium | Missing preflight integration tests | Not applied - Preflight is already tested in Story 23.5's test suite; this story focuses on run execution regression |
