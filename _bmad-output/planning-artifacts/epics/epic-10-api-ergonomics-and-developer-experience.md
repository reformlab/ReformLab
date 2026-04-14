# Epic 10: API Ergonomics and Developer Experience

**User outcome:** Analyst experiences a clean, intuitive API where naming is consistent, redundancy is eliminated, and the type system guides correct usage.

**Status:** done

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-1001 | Story | P1 | 5 | Rename `parameters` to `policy` on `ScenarioTemplate`/`BaselineScenario` and update YAML schema | done | FR7, NFR4 |
| BKL-1002 | Story | P1 | 5 | Infer `policy_type` from parameters class, making it optional on scenario construction | done | FR7, NFR4 |

## Epic-Level Acceptance Criteria

- `BaselineScenario` accepts `policy=` as the field name for the policy parameters object.
- `policy_type` is automatically inferred from the parameters class type (e.g., `CarbonTaxParameters` implies `PolicyType.CARBON_TAX`).
- `policy_type` can still be explicitly provided to override inference.
- All YAML pack files, JSON schema, loader, registry, server routes, and frontend types are updated consistently.
- All existing tests pass with the new API, and backward compatibility is documented.

---

## Story 10.1: Rename `parameters` to `policy` on scenario types

**Status:** done
**Priority:** P1
**Estimate:** 5

**Dependencies:** None

### Acceptance Criteria

- Given `BaselineScenario(policy=my_policy)`, when constructed, then the policy object is stored and accessible via `.policy`.
- Given existing YAML pack files using `parameters:` key, when loaded, then backward-compatible parsing accepts both `parameters:` and `policy:` keys.
- Given the JSON schema for scenario templates, when updated, then it accepts both `parameters` and `policy` field names.
- Given all tests, when run, then they pass with the renamed field.

---

## Story 10.2: Infer `policy_type` from parameters class

**Status:** done
**Priority:** P1
**Estimate:** 5

**Dependencies:** Story 10.1

### Acceptance Criteria

- Given `BaselineScenario(policy=CarbonTaxParameters(...))` without `policy_type`, when constructed, then `policy_type` is automatically set to `PolicyType.CARBON_TAX`.
- Given all four built-in parameter types, when used without explicit `policy_type`, then the correct `PolicyType` is inferred.
- Given a custom `PolicyParameters` subclass without a registered mapping, when used without explicit `policy_type`, then a clear error is raised explaining how to register the mapping.
- Given an explicit `policy_type` that contradicts the parameters class, when constructed, then the explicit value is used (with a warning).

---
