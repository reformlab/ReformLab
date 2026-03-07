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
