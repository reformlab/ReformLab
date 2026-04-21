## Deferred from: code review of story 25-6 (2026-04-20)

- Circular-import risk: `frontend/src/components/simulation/portfolioValidation.ts:11` imports `CompositionEntry` from `PortfolioCompositionPanel`. Move to `api/types.ts` in a dedicated cleanup.
- Error badge styling: `PortfolioCompositionPanel.tsx:786` uses `variant="default"` + `bg-red-500`, bypassing the Badge variant system. Add a `destructive` variant or use an error-color token.
- AC-3 warning text is split across heading + two `<p>` elements at `frontend/src/components/screens/PoliciesStageScreen.tsx:760-776`. Reason for deferring: visible content matches the spec sentence; the heading improves scannability. If strict-match grading is ever required, collapse to a single `<p>`.

## Deferred from: adversarial review of deferred-work fixes (2026-04-19)

- No regression tests cover `pa.concat_tables()` schema-mismatch paths in `src/reformlab/orchestrator/panel.py`; neither the `promote_options="permissive"` (decision columns) nor the non-decision branch has a test for divergent yearly schemas.

## Deferred from: spec-extract-policies-screen-dialog-state review (2026-04-19)

- Portfolio load/save round-tripping still falls back to raw `policy_type`/`carbon_tax` when a saved portfolio policy cannot be matched to a current template. This behavior existed before the hook extraction, but it can turn an unmatched loaded policy into the wrong saved policy type if edited and saved later.
