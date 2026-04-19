## Deferred from: adversarial review of deferred-work fixes (2026-04-19)

- No regression tests cover `pa.concat_tables()` schema-mismatch paths in `src/reformlab/orchestrator/panel.py`; neither the `promote_options="permissive"` (decision columns) nor the non-decision branch has a test for divergent yearly schemas.

## Deferred from: spec-extract-policies-screen-dialog-state review (2026-04-19)

- Portfolio load/save round-tripping still falls back to raw `policy_type`/`carbon_tax` when a saved portfolio policy cannot be matched to a current template. This behavior existed before the hook extraction, but it can turn an unmatched loaded policy into the wrong saved policy type if edited and saved later.
