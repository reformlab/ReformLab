---
title: 'Fix deferred work items from code reviews 23.3 and 23.4'
type: 'chore'
created: '2026-04-19'
status: 'done'
route: 'one-shot'
---

## Intent

**Problem:** Five defensive issues were deferred during code reviews of stories 23.3 and 23.4: missing collision guard in output mapping, missing `promote_options` on `concat_tables`, broad `except Exception` swallowing programming errors, case-sensitive env var parsing, and a reportedly hardcoded `runtime_mode` in metadata.

**Approach:** Fix the 4 real issues (the 5th was already resolved). Add collision guards for both source and target names in output mapping, use `promote_options="permissive"` on all `concat_tables` paths, normalize the env var with `.strip().lower()`, and split the broad except into specific exceptions plus a logged fallback.

## Suggested Review Order

1. [mapping.py](../../src/reformlab/computation/mapping.py) — collision guard: dual check for duplicate targets and duplicate sources in `apply_output_mapping()`
2. [panel.py](../../src/reformlab/orchestrator/panel.py) — `promote_options="permissive"` added to the non-decision `concat_tables` path for schema tolerance parity
3. [dependencies.py](../../src/reformlab/server/dependencies.py) — `.strip().lower()` on env var + split except into `(ImportError, ValueError, KeyError)` with a logged `except Exception` fallback
4. [deferred-work.md](deferred-work.md) — remaining deferred item (missing regression tests for schema-mismatch concat paths)
