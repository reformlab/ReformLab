# Epic 9: OpenFisca Adapter Hardening

**User outcome:** Adapter handles real-world OpenFisca entity models, variable periodicities, and multi-entity outputs correctly.

**Status:** done

## Epic-Level Acceptance Criteria

- Adapter correctly handles all OpenFisca-France entity types and variable periodicities.
- A reference test suite validates adapter output against known French tax-benefit values.

---

## Story 9.1: Fix entity-dict plural keys

**Status:** done
**Priority:** P0
**Estimate:** 1

Entity dicts use correct plural key names as expected by OpenFisca's `SimulationBuilder`.
Fixed during 8-1 code review.

### Acceptance Criteria

- Entity dicts use correct plural key names as expected by OpenFisca's `SimulationBuilder`.

---

## Story 9.2: Handle multi-entity output arrays

**Status:** done
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 9.1

### Acceptance Criteria

- Given output variables that return per-entity arrays (e.g., per-menage, per-foyer_fiscal), when the adapter processes results, then arrays are correctly mapped to their respective entity tables.
- Given a variable defined on `foyer_fiscal` entity, when results are returned, then the output array length matches the number of foyers fiscaux, not the number of individuals.
- Given mixed-entity output variables, when processed, then each variable's values are stored in the correct entity-level result table with proper entity IDs.

---

## Story 9.3: Add variable periodicity handling

**Status:** done
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 9.2

### Acceptance Criteria

- Given variables with different periodicities (monthly, yearly), when `compute()` is called, then the adapter converts periods correctly before passing to OpenFisca.
- Given a monthly variable requested for a yearly period, when computed, then the adapter handles period conversion according to OpenFisca conventions.
- Given an invalid period format, when passed to the adapter, then a clear error identifies the expected format.

---

## Story 9.4: Define population data 4-entity format

**Status:** done
**Priority:** P0
**Estimate:** 8

**Dependencies:** Story 9.2

### Acceptance Criteria

- Given the French tax-benefit model's 4 entities (individu, menage, famille, foyer_fiscal), when a population dataset is loaded, then all entity relationships are preserved and passable to `SimulationBuilder`.
- Given a population with membership arrays for all 4 entities, when built via `SimulationBuilder`, then entity group memberships are correctly assigned.
- Given a population dataset missing a required entity relationship, when loaded, then validation fails with a clear error identifying the missing relationship.

---

## Story 9.5: OpenFisca-France reference test suite

**Status:** done
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 9.3, Story 9.4

### Acceptance Criteria

- Given a set of known French tax-benefit scenarios with published expected values, when run through the adapter, then computed values match reference values within documented tolerances.
- Given the reference test suite, when run in CI, then all tests pass and tolerance thresholds are documented.
- Given a new OpenFisca-France version, when the reference suite is run, then regressions are detected and reported.

---
