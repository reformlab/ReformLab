## Deferred from: code review of 23-3-normalize-live-openfisca-results-into-the-stable-app-facing-output-schema.md (2026-04-15)

- `apply_output_mapping()` still has no collision guard on the `MappingConfig` path at `src/reformlab/computation/mapping.py:277`; deferred as a pre-existing issue outside Story 23.3.
- `pa.concat_tables()` without `promote_options` can still fail when non-decision yearly schemas differ at `src/reformlab/orchestrator/panel.py:150`; deferred as a pre-existing issue outside Story 23.3.
