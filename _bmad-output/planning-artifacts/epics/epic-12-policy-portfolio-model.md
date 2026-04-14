# Epic 12: Policy Portfolio Model

**User outcome:** Analyst can compose multiple individual policy templates into a named portfolio and run simulations with bundled policies applied together.

**Status:** done

**Builds on:** EPIC-2 (templates, registry), EPIC-3 (orchestrator)

**PRD Refs:** FR43–FR46

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-1201 | Story | P0 | 5 | Define PolicyPortfolio dataclass and composition logic | done | FR43 |
| BKL-1202 | Story | P0 | 5 | Implement portfolio compatibility validation and conflict resolution | done | FR43, FR44 |
| BKL-1203 | Story | P0 | 5 | Extend orchestrator to execute policy portfolios | done | FR44 |
| BKL-1204 | Story | P0 | 5 | Extend scenario registry with portfolio versioning | done | FR43 |
| BKL-1205 | Story | P0 | 5 | Implement multi-portfolio comparison and notebook demo | done | FR45 |

## Epic-Level Acceptance Criteria

- Analyst can create a portfolio from 2+ individual policy templates.
- Orchestrator executes a portfolio, applying all bundled policies at each yearly step.
- Portfolio is versioned in the scenario registry alongside individual scenarios.
- Portfolio comparison produces side-by-side indicator tables.
- Custom policy templates participate in portfolios alongside built-in templates.
- Notebook demo runs end-to-end in CI.

---

## Story 12.1: Define PolicyPortfolio dataclass and composition logic

**Status:** done
**Priority:** P0
**Estimate:** 5

**PRD Refs:** FR43

### Acceptance Criteria

- Given 2+ individual `PolicyConfig` objects, when composed into a `PolicyPortfolio`, then the portfolio is a named, frozen dataclass containing all policies.
- Given a portfolio, when inspected, then it lists all constituent policies with their types and parameter summaries.
- Given a portfolio, when serialized to YAML, then it round-trips correctly (save and reload produces identical object).

---

## Story 12.2: Implement portfolio compatibility validation and conflict resolution

**Status:** done
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 12.1
**PRD Refs:** FR43, FR44

### Acceptance Criteria

- Given two policies in a portfolio that affect the same household attribute (e.g., two different carbon tax rates), when validated, then a conflict is detected and reported with the exact parameter names.
- Given a portfolio with non-conflicting policies (e.g., carbon tax + vehicle subsidy), when validated, then validation passes.
- Given a conflict, when the analyst provides an explicit resolution rule (e.g., "sum" or "first wins"), then the conflict is resolved and recorded in the portfolio metadata.
- Given an unresolvable conflict with no resolution rule, when the portfolio is executed, then it fails before computation with a clear error listing the conflicting policies and parameters.

---

## Story 12.3: Extend orchestrator to execute policy portfolios

**Status:** done
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 12.1
**PRD Refs:** FR44

### Acceptance Criteria

- Given a portfolio with 3 policies, when the orchestrator runs a yearly step, then all 3 policies are applied to the population for that year.
- Given a portfolio execution, when completed over 10 years, then yearly panel output reflects the combined effect of all policies.
- Given the orchestrator receiving a portfolio instead of a single policy, when run, then no changes to `ComputationAdapter` interface or orchestrator core logic are required (portfolio is unwrapped in the template application layer).
- Given a single-policy scenario (backward compatibility), when run through the portfolio-aware orchestrator, then it behaves identically to pre-portfolio execution.

---

## Story 12.4: Extend scenario registry with portfolio versioning

**Status:** done
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 12.1
**PRD Refs:** FR43

### Acceptance Criteria

- Given a portfolio saved to the registry, when retrieved by version ID, then the returned portfolio is identical to what was saved, including all constituent policies.
- Given a portfolio, when a constituent policy is modified and the portfolio is re-saved, then a new version ID is assigned.
- Given the registry, when queried, then portfolios and individual scenarios are both listable and distinguishable by type.

---

## Story 12.5: Implement multi-portfolio comparison and notebook demo

**Status:** done
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 12.3
**PRD Refs:** FR45

### Acceptance Criteria

- Given 3 completed portfolio runs (each against the same baseline), when comparison is invoked, then a side-by-side table shows all indicator types per portfolio.
- Given multi-portfolio comparison, when cross-comparison metrics are computed, then aggregate metrics are available (e.g., "which portfolio maximizes welfare?", "which has lowest fiscal cost?").
- Given the pairwise comparison API from Phase 1, when used with portfolios, then it works as a convenience alias (N=1 case).
- Given the notebook demo, when run in CI, then it demonstrates portfolio creation, execution, comparison, and cross-comparison metrics end-to-end.

## Scope Notes

- **Portfolios are compositions** of existing individual policy templates — no new policy type concept.
- **Conflict resolution** — when two policies in a portfolio affect the same parameter, the composition layer resolves or raises an explicit error.
- **Naming example:** Portfolio "Green Transition 2030" = carbon tax (€100/tCO2) + vehicle bonus (€5k EV subsidy) + MaPrimeRénov' (renovation aid) + feebate (vehicle malus).

---
