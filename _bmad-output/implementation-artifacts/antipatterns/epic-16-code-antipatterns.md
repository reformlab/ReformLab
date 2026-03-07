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
