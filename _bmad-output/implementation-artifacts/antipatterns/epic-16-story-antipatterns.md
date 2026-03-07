# Epic 16 - Story Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during validation of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent story-writing mistakes (unclear AC, missing Notes, unrealistic scope).

## Story 16-1 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | AC-1 lists "scenario/portfolio configuration (YAML), template definitions used (YAML)" — but tasks export JSON snapshots and template definitions are not available from `SimulationResult` | AC-1 rewritten to accurately describe what is exported: simulation panel output (Parquet), policy parameters snapshot (JSON), scenario metadata snapshot (JSON), run manifest (JSON). Subdirectory names made explicit. |
| critical | AC-4 "includes the calibrated beta coefficients" implies separate files, but Dev Notes scope note explicitly says 16.1 does NOT add calibration files — contradiction blocks tester agreement on done/not-done | AC-4 rewritten to specify that calibration data is contained in the exported `run-manifest.json` `assumptions` field (via Story 15.4), not as separate files. 16.3 scope boundary restated in the AC itself. |
| high | Task 2.2 creates `results/` subdirectory but no artifact is ever written there; Dev Notes package layout omits `results/` entirely | Removed `results/` from Task 2.2's subdirectory list. |
| medium | Task 3.4 says "validate output_path parent directory exists" but `output_path` IS the parent — the package subdirectory goes inside it, so this validation as written is wrong | Reworded to "Validate `output_path` exists as a directory — the package subdirectory `{package_id}/` is created inside it." |
| medium | AC-5 says "every listed artifact's hash can be verified" but it's unclear whether `package-index.json` is listed in its own artifacts array (which would be circular) | Added explicit Implementation Note: `package-index.json` is NOT in the `artifacts` array; AC-5 applies only to the listed files. |
| medium | Task 2.6 says "only if yearly manifests are available in the result metadata" — untestable without knowing which metadata key and what type | Task 2.6 now specifies `result.metadata.get("child_manifests", {})` with type `dict[int, str]`, and specifies to log `event=child_manifests_absent` when absent. |

## Story 16-2 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | ZIP root directory validation missing — `import_replication_package()` specified "single subdirectory expected" but gave no error path for 0 entries, 2+ entries, or a top-level file | Task 2.2 updated with explicit `ReplicationPackageError` on non-conforming structure; Algorithm step 2a extended with enumerated error condition. |
| medium | `_compare_panel_tables` sort fallback and NaN semantics unspecified — if `household_id`/`year` columns are absent the sort would raise; NaN comparison semantics (False for NaN == NaN) not documented | Algorithm step 3 updated with explicit fallback (skip sort + warning log) and NaN/null treatment documented. |

## Story 16-3 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | Loading unindexed provenance files bypasses hash verification | Tasks 4.1/4.2 updated to use the index as authority for file discovery — unindexed provenance files log WARNING and resolve to `None`. Dev Notes import section rewritten to match. New test 6.17 added. |
| medium | AC-3 "enough information" is qualitative and not objectively testable | AC-3 now enumerates the required keys (`pipeline_description`, `generation_seed`, `step_log`, `assumption_chain`, `source_configs`) explicitly. |
| medium | AC-4 "every methodological choice is traceable" is subjective | AC-4 now specifies exactly what each provenance field must record — data sources with provider/dataset ID/URL for population; targets, objective function, parameters, and diagnostics for calibration. |
| medium | JSON serialization/parse failures not required to wrap in `ReplicationPackageError`, violating subsystem error hierarchy | Tasks 1.4/1.5 now require catching `TypeError` from `json.dumps` and re-raising as `ReplicationPackageError`. New test 6.16 added. |
| low | Task 6.5 artifact count baseline "(4)" ambiguous given optional year manifests | Clarified to "4 core artifacts; optional year manifests not counted." |
| low | Anti-patterns table missing entries for the two new failure modes | Two new anti-pattern rows added. |

## Story 16-4 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | AC-5 references "YAML + notebook + manifest" but no YAML artifacts exist in the replication package contract — all config files are JSON (`policy.json`, `scenario-metadata.json`, `package-index.json`, `run-manifest.json`) | AC-5 rewritten to name the actual JSON artifacts and the exported package as the sharable unit |
| high | `show()` helper has contradictory instructions — Task 1.2 imports `show` from `reformlab`, Dev Notes says "define inline ... alternatively import", Anti-Patterns section says "copy verbatim from 06_portfolio_comparison.ipynb" | Task 1.2 updated to remove `show` from reformlab imports and mandate local helper; Dev Notes updated to specify copy-verbatim as the only approach |
| medium | CI Task 11.1 says "after line 22" — brittle reference that breaks when ci.yml is edited | Both Task 11.1 and the CI Configuration Update section now use anchor-based instruction ("within the `ci` job, immediately after the existing pytest step(s)") |
