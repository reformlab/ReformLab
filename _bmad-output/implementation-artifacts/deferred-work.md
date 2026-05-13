## Completed

### Story 27.14 - Frontend cleanup sweep (2026-05-13)

**[EXISTS] Circular-import risk**: `frontend/src/components/simulation/portfolioValidation.ts:11` imports `CompositionEntry` from `PortfolioCompositionPanel`. → **Completed in Story 27.11** (import now from `@/api/types`).

**[EXISTS] Error badge styling**: `PortfolioCompositionPanel.tsx:786` uses `variant="default"` + `bg-red-500` → **Completed in Story 27.14** (code moved to `PolicyCard.tsx:271` during Story 27.4; now uses `variant="destructive"`).

**[EXISTS] AC-3 warning text split**: Heading + two `<p>` elements at `PoliciesStageScreen.tsx:990-1002` → **Reviewed and accepted in Story 27.14** (multi-paragraph structure intentional for scannability; documented with code comment).

**[EXISTS] Portfolio round-tripping fallback**: Template matching falls back to `policy_type` → **Documented in Story 27.14** (console.warn + code comment added at `usePortfolioDialog.ts:284-293`).

**[NEW] Editing badge styling bypass**: `PolicyCard.tsx:278` uses `variant="default"` + `bg-blue-500` → **Resolved in Story 27.14** (now uses `variant="info"`).

**[NEW] Active badge styling bypass**: `PoliciesStageScreen.tsx:1086` uses `variant="default"` + `bg-blue-100` → **Resolved in Story 27.14** (now uses `variant="secondary"`).

### Deferred to Epic 29

**[EXISTS] Backend regression tests**: `pa.concat_tables()` schema-mismatch paths in `src/reformlab/orchestrator/panel.py` → **Deferred to Epic 29** (backend work).

---

## Deferred from: code review of story 25-6 (2026-04-20)

~~- Circular-import risk: `frontend/src/components/simulation/portfolioValidation.ts:11` imports `CompositionEntry` from `PortfolioCompositionPanel`. Move to `api/types.ts` in a dedicated cleanup.~~ (Completed in Story 27.11)

~~- Error badge styling: `PortfolioCompositionPanel.tsx:786` uses `variant="default"` + `bg-red-500`, bypassing the Badge variant system. Add a `destructive` variant or use an error-color token.~~ (Completed in Story 27.14)

~~- AC-3 warning text is split across heading + two `<p>` elements at `frontend/src/components/screens/PoliciesStageScreen.tsx:760-776`. Reason for deferring: visible content matches the spec sentence; the heading improves scannability. If strict-match grading is ever required, collapse to a single `<p>`.~~ (Accepted in Story 27.14)

## Deferred from: adversarial review of deferred-work fixes (2026-04-19)

- No regression tests cover `pa.concat_tables()` schema-mismatch paths in `src/reformlab/orchestrator/panel.py`; neither the `promote_options="permissive"` (decision columns) nor the non-decision branch has a test for divergent yearly schemas.

## Deferred from: spec-extract-policies-screen-dialog-state review (2026-04-19)

~~- Portfolio load/save round-tripping still falls back to raw `policy_type`/`carbon_tax` when a saved portfolio policy cannot be matched to a current template. This behavior existed before the hook extraction, but it can turn an unmatched loaded policy into the wrong saved policy type if edited and saved later.~~ (Documented in Story 27.14)
