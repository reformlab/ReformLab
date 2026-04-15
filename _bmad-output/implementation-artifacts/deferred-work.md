## Deferred from: code review of 23-3-normalize-live-openfisca-results-into-the-stable-app-facing-output-schema.md (2026-04-15)

- `apply_output_mapping()` still has no collision guard on the `MappingConfig` path at `src/reformlab/computation/mapping.py:277`; deferred as a pre-existing issue outside Story 23.3.
- `pa.concat_tables()` without `promote_options` can still fail when non-decision yearly schemas differ at `src/reformlab/orchestrator/panel.py:150`; deferred as a pre-existing issue outside Story 23.3.

## Deferred from: code review of story-23.4 (2026-04-15)

- Broad `except Exception` in `_create_adapter()` replay fallback silently swallows programming errors (TypeError, AttributeError) and falls back to MockAdapter at `src/reformlab/server/dependencies.py:159-163`; pre-existing pattern.
- `REFORMLAB_RUNTIME_MODE` env var is case-sensitive and does not strip whitespace — `'Live'` or `'replay '` silently default to live after warning at `src/reformlab/server/dependencies.py:145-148`; pre-existing pattern.
- `_run_direct_scenario()` hardcodes `runtime_mode='live'` in result metadata at `src/reformlab/interfaces/api.py:1722` regardless of actual adapter used; out of Story 23.4 scope.
