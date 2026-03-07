# Epic 16 - Code Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during code review of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent implementation mistakes (race conditions, missing tests, weak assertions, etc.)

## Story 16-1 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | Child manifest iteration order nondeterministic — violates project's non-negotiable determinism requirement | Changed `child_manifests_meta.items()` to `sorted(child_manifests_meta.items())` |
| medium | `PackageIndex.from_json()` artifact entry access throws `KeyError`/`TypeError` on malformed input instead of documented `ValueError` | Wrapped artifact tuple construction in `try/except (KeyError, TypeError)` raising `ValueError` |
| medium | Non-atomic export — failure mid-export leaves partial package directory on disk | Wrapped all I/O in `try/except Exception` with `shutil.rmtree(package_dir)` cleanup on failure |
| medium | `result` parameter typed as `Any` suppresses type checking; empty `TYPE_CHECKING` block | Added `SimulationResult` to `TYPE_CHECKING` block; updated function signature to `result: SimulationResult` |
| medium | `SimulationResult.export_replication_package()` returns `Any` instead of `ReplicationPackageMetadata` | Added `ReplicationPackageMetadata` to `TYPE_CHECKING` imports; updated return type annotation |

## Story 16-2 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Path traversal via unvalidated `artifact.path` in `_load_package_from_dir` | Added `.resolve().relative_to(pkg_dir_resolved)` confinement check before hash verification; raises `ReplicationPackageError` on escape. |
| high | `zipfile.BadZipFile` leaks from `import_replication_package` instead of `ReplicationPackageError` | Wrapped `ZipFile` open/extract in `try/except zipfile.BadZipFile`. |
| high | `ValueError` from `PackageIndex.from_json()` leaks from `_load_package_from_dir` | Wrapped `PackageIndex.from_json()` call in `try/except ValueError → ReplicationPackageError`. |
| high | Config extraction (`year` column access, seed coercion) outside the `try/except` guard block in `reproduce_from_package` | Added explicit pre-validation (`year` column presence, non-empty table, seed coercion try/except) before config extraction. |
| medium | Integer columns cast to `float` for comparison, risking precision loss on large IDs | Split `is_floating or is_integer` branch into separate `is_floating` (tolerance-based) and `is_integer` (exact equality, no float conversion). |
| medium | `ImportedPackage` frozen dataclass holds mutable `dict` fields without defensive copies | Added `__post_init__` using `object.__setattr__` + `copy.deepcopy` for `policy` and `scenario_metadata`. |
| medium | Missing tests for negative tolerance, malformed ZIP, malformed index JSON, path traversal, mutable field isolation, and discrepancy column naming | Added 4 test classes: `TestImportEdgeCases`, `TestImportedPackageMutableFieldIsolation`, `TestReproduceNegativeTolerance`, `TestReproduceDiscrepancyDetails`. |
| low | Non-numeric column comparison has redundant outer `if orig_list != repr_list` check causing double traversal | Removed outer check; loop directly finds and reports first mismatch. |

## Story 16-3 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | `integrity_verified=True` set without verifying that mandatory core artifacts are listed in the index. A crafted index omitting core files would allow those files to be loaded without hash verification. | Added mandatory artifact presence check (step 3b) before hash verification — raises `ReplicationPackageError` if any of the 4 core paths are absent from the index. |
| high | Provenance JSON parsing (`json.loads`) can raise `json.JSONDecodeError` leaking through the `ReplicationPackageError` boundary. | Wrapped both provenance `json.loads` calls in `try/except json.JSONDecodeError → ReplicationPackageError`. |
| high | Loaded provenance value is not validated as `dict` — `json.loads` can return list/string/null while the field is typed `dict[str, Any] | Added `isinstance(loaded, dict)` check after parsing; raises `ReplicationPackageError` on type mismatch. |
| medium | `TestImportProvenanceMutableFieldIsolation` test methods were misleadingly named "does_not_affect_package" but actually only verified disk stability (re-importing from disk), not in-memory isolation of the same `pkg` instance. | Renamed methods and rewrote docstrings to accurately describe what is tested (file/disk stability after mutation of the returned reference). Behavior unchanged. |
| medium | Path traversal test replaced mandatory artifact[0] with traversal path, breaking the new mandatory artifact check. | Changed test to inject traversal path as an additional entry (not replacing a mandatory one), so mandatory check passes and path traversal guard fires correctly. |
| low | Task 5 completion note incorrectly stated "No changes to `__all__` needed" — the git diff shows `governance/__init__.py` did have additions (from prior stories). | Updated completion note to accurate wording. |
