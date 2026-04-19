## Deferred from: adversarial review of deferred-work fixes (2026-04-19)

- No regression tests cover `pa.concat_tables()` schema-mismatch paths in `src/reformlab/orchestrator/panel.py`; neither the `promote_options="permissive"` (decision columns) nor the non-decision branch has a test for divergent yearly schemas.
