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
