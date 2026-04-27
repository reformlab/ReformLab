# Deferred Work

This file tracks items deferred from code reviews, retrospectives, and incident hotfixes. Items here have known owners (a future story or epic) and are not lost — they are queued for a sweep rather than fixed inline.

**Convention:** Each item has a section header recording its origin. When a story or epic absorbs the item, append `→ migrated to <story-id>` and move the item to the "## Closed (migrated)" section at the bottom.

---

## Open

_None._

---

## Closed (migrated)

### Deferred from: spec-extract-policies-screen-dialog-state review (2026-04-19)

- Portfolio load/save round-tripping still falls back to raw `policy_type`/`carbon_tax` when a saved portfolio policy cannot be matched to a current template. This behavior existed before the hook extraction, but it can turn an unmatched loaded policy into the wrong saved policy type if edited and saved later. → **migrated to story 27.11** (AC #8: explicit unmatched-template marker, preserve original `policy_type` on save).

### Deferred from: code review of story 25-6 (2026-04-20)

- Circular-import risk: `frontend/src/components/simulation/portfolioValidation.ts:11` imports `CompositionEntry` from `PortfolioCompositionPanel`. Move to `api/types.ts` in a dedicated cleanup. → **migrated to story 27.14** (and partially overlaps with story 27.11's type unification).
- Error badge styling: `PortfolioCompositionPanel.tsx:786` uses `variant="default"` + `bg-red-500`, bypassing the Badge variant system. Add a `destructive` variant or use an error-color token. → **migrated to story 27.14**.
- AC-3 warning text is split across heading + two `<p>` elements at `frontend/src/components/screens/PoliciesStageScreen.tsx:760-776`. Reason for deferring: visible content matches the spec sentence; the heading improves scannability. If strict-match grading is ever required, collapse to a single `<p>`. → **migrated to story 27.14**.

### Deferred from: adversarial review of deferred-work fixes (2026-04-19)

- No regression tests cover `pa.concat_tables()` schema-mismatch paths in `src/reformlab/orchestrator/panel.py`; neither the `promote_options="permissive"` (decision columns) nor the non-decision branch has a test for divergent yearly schemas. → **migrated to story 29.5**.

### Deferred from: code review of spec-fix-passive-policy-set-autoload-for-non-portfolio-references (2026-04-26)

- Auto-name effect at `frontend/src/contexts/AppContext.tsx:550-560` now lists `activeScenarioName` in its dep array, so the effect re-runs after the same effect commits the new name (computes the suggestion again, hits the `===` early-return, bails). Cosmetic — converges idempotently in one extra render — but worth tightening with a functional setter or a name-ref read so `activeScenarioName` does not need to be a dep. → **migrated to story 27.13** (covered by AC #5).

### Deferred from: hotfix `_DEFAULT_LIVE_OUTPUT_VARIABLES` mismatch with openfisca-france 44.2.2 (2026-04-26)

Context: live computation was failing at year 2025 because eight names in `_DEFAULT_OUTPUT_MAPPING` did not resolve in core `openfisca_france` (`irpp`, `revenu_net`, `revenu_brut`, `taxe_carbone`, `montant_subvention`, `eligible_subvention`, `malus_ecologique`, `aide_energie`). Hotfix in `src/reformlab/computation/result_normalizer.py` narrowed `_DEFAULT_LIVE_OUTPUT_VARIABLES` to four names that resolve today (`revenu_disponible`, `impots_directs`, `salaire_net`, `prestations_sociales`) while keeping the unimplemented names in the rename map so they normalize for free once their custom variables land.

- **Story 24.2 subsidy/malus/energy-aid custom variables not implemented.** `montant_subvention`, `eligible_subvention`, `malus_ecologique`, `aide_energie` exist in `_DEFAULT_OUTPUT_MAPPING` but have no matching custom variable in any TaxBenefitSystem extension. → **migrated to story 29.1** (PM-decision on `cheque_energie` aliasing recorded in 29.1 Dev Notes before implementation).
- **Generic-name placeholders need real OpenFisca-France targets.** `irpp`, `revenu_net`, `revenu_brut`, `taxe_carbone` are project-internal generic names that don't exist in `openfisca_france` 44.2.2. Decision per name: rename, drop, or implement as custom. → **migrated to story 29.2**.
- **Test scaffolding still references generic names as fixtures.** `tests/computation/test_result_normalizer.py:148-149`, `tests/computation/test_normalization_regression.py`, `tests/computation/test_openfisca_api_adapter.py` (many sites), `tests/orchestrator/test_panel.py:518` use `irpp`/`revenu_net`/`taxe_carbone` as synthetic PyArrow fixtures. → **migrated to story 29.4** (depends on 29.2 renaming decisions).
- **Restore resolved names in `_DEFAULT_LIVE_OUTPUT_VARIABLES`** once 29.1/29.2 land. → **migrated to story 29.3**.
