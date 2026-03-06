# Spike Findings: Story 8.1 — End-to-End OpenFisca Integration

**Date:** 2026-02-28
**Status:** Complete
**Installed Versions:** openfisca-core 44.2.2, openfisca-france 175.0.18

---

## Summary

The OpenFiscaApiAdapter was tested against real OpenFisca-France computations. The adapter's core pipeline (TBS loading, version detection, variable validation, output extraction) works correctly. However, two issues were identified that prevent the adapter's `compute()` method from working end-to-end with OpenFisca-France without modification.

**Outcome:** Partial success — adapter fundamentals are sound, but the `_population_to_entity_dict()` and `_extract_results()` methods need targeted fixes before production use with real country packages.

---

## What Worked

1. **TBS loading and caching** — `CountryTaxBenefitSystem` loads successfully via the adapter's lazy import mechanism. The country package detection (`CountryTaxBenefitSystem` attribute) works correctly. TBS is cached after first load.

2. **Version detection** — `_detect_openfisca_version()` correctly identifies openfisca-core 44.2.2, which passes compatibility matrix validation.

3. **Variable validation** — `_validate_output_variables()` correctly validates variable names against the TBS. Close-match suggestions work (e.g., typo "irpp" suggests related variables).

4. **Real computation** — OpenFisca-France computes French income tax (`impot_revenu_restant_a_payer`) correctly for a single person with a 30k EUR/year salary. The result (-812 EUR) is deterministic across runs and consistent with progressive tax expectations (higher salary → more tax).

5. **Variable mapping round-trip** — `apply_output_mapping()` correctly renames OpenFisca-France variable names to project schema names. Values are numerically identical after mapping.

6. **Output quality validation** — `validate_output()` passes when given a correctly-typed schema matching the adapter output.

---

## What Broke (Adapter Gaps)

### Gap 1: Entity dict keys must use `entity.plural`, not `entity.key` — FIXED

**Severity:** High — blocks `compute()` from working with any real country package.

**Status:** Fixed during code review (2026-02-28).

**Problem:** The adapter's `_population_to_entity_dict()` built entity dicts keyed by `entity.key` (e.g., `"individu"`, `"famille"`, `"foyer_fiscal"`, `"menage"`). However, OpenFisca's `SimulationBuilder.build_from_entities()` expects **plural** entity names (e.g., `"individus"`, `"familles"`, `"foyers_fiscaux"`, `"menages"`).

**Fix applied:** `_population_to_entity_dict()` now normalises singular keys to plural using a `key_to_plural` mapping. `_build_simulation()` accepts both singular and plural entity keys in validation. Integration tests now call `adapter.compute()` end-to-end successfully.

### Gap 2: Multi-entity output arrays have different lengths

**Severity:** Medium — blocks requesting variables from multiple entities in one `compute()` call.

**Problem:** `_extract_results()` calls `simulation.calculate(var, period)` for each output variable and combines all results into a single `pa.Table`. However, different variables belong to different entities and return arrays of different lengths:
- `individu`-level variables → 1 value per person
- `foyer_fiscal`-level variables → 1 value per tax household
- `menage`-level variables → 1 value per dwelling

For a married couple (2 persons, 1 foyer_fiscal, 1 menage), `salaire_net` returns 2 values but `impot_revenu_restant_a_payer` returns 1 value. These cannot be combined into a single `pa.Table`.

**Fix options:**
1. **Restrict to single-entity variables per compute() call** — validate that all output variables belong to the same entity.
2. **Return separate tables per entity** — change `ComputationResult.output_fields` to support multiple entity tables.
3. **Flatten via entity membership** — broadcast group-level values to person level using entity membership arrays.

**Recommended:** Option 1 for the near term (simple validation), with option 3 as a follow-up story for production use.

### Gap 3: `irpp` variable does not exist (naming)

**Severity:** Low — documentation issue only.

**Problem:** The story specified `irpp` as a test variable, but OpenFisca-France 175.x uses `impot_revenu_restant_a_payer` for the final income tax. The variable `irpp_economique` exists but has different semantics. This is not an adapter bug — it's a naming difference in the OpenFisca-France legislative model.

**Fix:** Use correct variable names when configuring the adapter. The adapter's `_validate_output_variables()` already catches unknown names and provides suggestions.

### Gap 4: Monthly vs yearly variable periodicity

**Severity:** Low — affects specific variables, not the adapter architecture.

**Problem:** Some OpenFisca-France variables (e.g., `salaire_net`) require monthly periods and raise `ValueError` when called with `simulate.calculate("salaire_net", "2024")`. Must use `calculate_add("salaire_net", "2024")` to sum monthly values over a year.

**Fix:** The adapter currently uses `simulation.calculate()` for all variables. Could add detection of variable periodicity and use `calculate_add()` for monthly variables when a yearly period is requested. This requires checking `tbs.variables[var].definition_period`.

---

## Performance Observations

- **TBS initialization:** ~3-5 seconds (loads all French legislation). Module-scoped fixture avoids repeated loading.
- **Single-person compute:** <1 second after TBS init.
- **Multi-person compute:** <1 second for 2 persons after TBS init.
- **Full test suite (16 tests):** ~47 seconds (dominated by TBS initialization across test classes).

**Recommendation:** In production, initialize the TBS once at application startup and reuse across compute calls (the adapter already caches it).

---

## Adapter Code Changes Made

None. The spike was conducted test-first without modifying adapter code, per the anti-patterns guidance. All tests bypass the broken `_population_to_entity_dict()` by building entity dicts directly.

---

## Recommended Follow-Up Stories

1. **Fix entity dict plural keys** (High priority) — Update `_population_to_entity_dict()` to use `entity.plural` keys. ~1 story point, localized change.

2. **Handle multi-entity output arrays** (Medium priority) — Add entity-aware result extraction to `_extract_results()`. Options: single-entity validation, per-entity tables, or person-level broadcasting.

3. **Add variable periodicity handling** (Low priority) — Detect monthly variables and use `calculate_add()` when yearly period is requested.

4. **Update PopulationData format for OpenFisca-France** (Medium priority) — Define a standard way to express the 4-entity model (individu, famille, foyer_fiscal, menage) with role assignments in `PopulationData`. Current table-based format doesn't naturally express group entity roles.

5. **Production integration test suite** (Low priority) — Expand from this spike's 16 tests to a broader regression suite covering more French tax-benefit variables.

---

## Files Created/Modified

| File | Action | Description |
|------|--------|-------------|
| `pyproject.toml` | Modified | Added `openfisca-france>=175.0.0` to optional deps, `integration` marker, `addopts` filter, ruff override |
| `tests/computation/test_openfisca_integration.py` | Created | 21 integration tests covering AC-1 through AC-7 + OpenFisca-France reference cases |
| `_bmad-output/implementation-artifacts/spike-findings-8-1-openfisca-integration.md` | Created | This findings document |
