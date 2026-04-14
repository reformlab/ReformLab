# Epic 14: Discrete Choice Model for Household Decisions

**User outcome:** Analyst can run multi-year simulations where households make investment decisions (vehicle, heating, renovation) in response to policy signals, with decisions feeding back into subsequent years.

**Status:** backlog

**Builds on:** EPIC-3 (orchestrator, step protocol), EPIC-11 (realistic population with asset attributes), EPIC-12 (policy portfolios)

**PRD Refs:** FR47–FR51

**Reference:** [Phase 2 Design Note: Discrete Choice Model](phase-2-design-note-discrete-choice-household-decisions.md)

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-1401 | Story | P0 | 8 | Implement DiscreteChoiceStep with population expansion pattern | backlog | FR47, FR48 |
| BKL-1402 | Story | P0 | 5 | Implement conditional logit model with seed-controlled draws | backlog | FR47, FR49 |
| BKL-1403 | Story | P0 | 8 | Implement vehicle investment decision domain | backlog | FR47, FR50 |
| BKL-1404 | Story | P0 | 8 | Implement heating system decision domain | backlog | FR47, FR50 |
| BKL-1405 | Story | P0 | 5 | Implement eligibility filtering for performance optimization | backlog | FR48 |
| BKL-1406 | Task | P0 | 3 | Extend panel output and manifests with decision records | backlog | FR50, FR51 |
| BKL-1407 | Story | P0 | 5 | Build 10-year behavioral simulation notebook demo | backlog | FR47 |

## Epic-Level Acceptance Criteria

- `DiscreteChoiceStep` registers via standard step protocol without modifying orchestrator core.
- Population expansion pattern works: clone households × alternatives, evaluate via OpenFisca, reshape to cost matrix.
- Conditional logit model produces realistic choice distributions for vehicle and heating domains.
- 10-year run with 100k households completes within acceptable time on laptop.
- Identical seeds produce identical household decisions across runs.
- Panel output records every decision for every household every year (chosen alternative, probabilities, utilities).
- Taste parameters (β coefficients) appear in run manifests.
- Eligibility filtering reduces expanded population for performance (only eligible households face choices).
- Notebook demo runs end-to-end in CI.

---

## Story 14.1: Implement DiscreteChoiceStep with population expansion pattern

**Status:** backlog
**Priority:** P0
**Estimate:** 8

**PRD Refs:** FR47, FR48

### Acceptance Criteria

- Given the `DiscreteChoiceStep`, when registered with the orchestrator, then it implements the `OrchestratorStep` protocol and executes at the correct position in the yearly pipeline (after vintage transitions, before state carry-forward).
- Given a population of N households and a choice set of M alternatives, when expansion runs, then M copies of each household are created with attributes modified per alternative.
- Given an expanded population, when passed to `ComputationAdapter.compute()`, then OpenFisca evaluates all N×M rows in one vectorized batch call.
- Given OpenFisca results for the expanded population, when reshaped, then an N×M cost matrix is produced with one cost per household per alternative.
- Given the orchestrator core, when `DiscreteChoiceStep` is added, then no modifications to `ComputationAdapter` interface or orchestrator loop logic are required.

---

## Story 14.2: Implement conditional logit model with seed-controlled draws

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 14.1
**PRD Refs:** FR47, FR49

### Acceptance Criteria

- Given an N×M cost matrix and taste parameters (β coefficients), when the logit model computes, then choice probabilities are `P(j|C_i) = exp(V_ij) / Σ_k exp(V_ik)` for each household.
- Given choice probabilities and a random seed, when draws are made, then each household is assigned exactly one chosen alternative per decision domain.
- Given identical cost matrices and identical seeds, when draws are made twice, then the chosen alternatives are identical across runs.
- Given a different seed, when draws are made, then the household-level choices differ but the aggregate distribution remains statistically consistent.
- Given the logit model, when probabilities are computed, then all probability vectors sum to 1.0 (within floating-point tolerance) for each household.

---

## Story 14.3: Implement vehicle investment decision domain

**Status:** backlog
**Priority:** P0
**Estimate:** 8

**Dependencies:** Story 14.2
**PRD Refs:** FR47, FR50

### Acceptance Criteria

- Given the vehicle decision domain, when configured, then the choice set includes at minimum: keep current vehicle, buy petrol, buy diesel, buy hybrid, buy EV, buy no vehicle.
- Given a household with vehicle attributes, when the domain evaluates alternatives, then utility inputs include: purchase cost (net of subsidy), annual fuel/electricity cost, annual carbon tax, maintenance.
- Given a household that chooses a new vehicle, when the state is updated, then the household's vehicle attributes change and a new vintage cohort entry is created (age=0).
- Given a household that keeps their current vehicle, when the state is updated, then vehicle attributes are unchanged.

---

## Story 14.4: Implement heating system decision domain

**Status:** backlog
**Priority:** P0
**Estimate:** 8

**Dependencies:** Story 14.2
**PRD Refs:** FR47, FR50

### Acceptance Criteria

- Given the heating system domain, when configured, then the choice set includes at minimum: keep current, gas boiler, heat pump, electric, wood/pellet.
- Given a household with heating attributes, when the domain evaluates alternatives, then utility inputs include: equipment cost (net of subsidy), annual energy cost by fuel type, annual carbon tax by fuel type, maintenance.
- Given a household that switches heating systems, when the state is updated, then `heating_type`, `energy_consumption`, and related attributes change, and a new vintage entry is created.
- Given both vehicle and heating domains configured, when the orchestrator runs a year, then domains execute sequentially (vehicle first, then heating) and the second domain sees the state updated by the first.

---

## Story 14.5: Implement eligibility filtering for performance optimization

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 14.1
**PRD Refs:** FR48

### Acceptance Criteria

- Given eligibility rules (e.g., only households whose vehicle is older than 10 years face the vehicle choice), when the population is expanded, then only eligible households are cloned × alternatives.
- Given a population of 100k households where 30k are eligible for vehicle choice, when expanded with 5 alternatives, then the expanded population is 150k rows (not 500k).
- Given eligibility filtering, when a 10-year run with 100k households and 2 domains completes, then execution time is within the performance budget documented in the design note.
- Given a household that is not eligible for a decision domain, when the step runs, then the household retains its current state without evaluation.
- Given eligibility rules, when recorded in the run manifest, then the rules and the count of eligible vs. ineligible households per domain per year are documented.

---

## Story 14.6: Extend panel output and manifests with decision records

**Status:** backlog
**Priority:** P0
**Estimate:** 3

**Dependencies:** Story 14.3
**PRD Refs:** FR50, FR51

### Acceptance Criteria

- Given a completed discrete choice run, when panel output is inspected, then each household-year row includes: `decision_domain`, `chosen_alternative`, `choice_probabilities` (array), and `utility_values` (array).
- Given a run with discrete choice, when the manifest is inspected, then taste parameters (β coefficients) for each domain are recorded.
- Given panel output with decision records, when exported to Parquet, then decision columns are correctly typed and readable by pandas/polars.

---

## Story 14.7: Build 10-year behavioral simulation notebook demo

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 14.6
**PRD Refs:** FR47

### Acceptance Criteria

- Given the notebook, when run end-to-end, then it demonstrates: population with asset attributes, policy portfolio configuration, 10-year dynamic run with discrete choice, year-by-year fleet composition changes, and distributional indicators.
- Given the notebook, when run in CI, then it completes without errors.
- Given the notebook output, when inspected, then it shows: aggregate vehicle fleet turnover charts (EV adoption over time), heating system transition charts, and distributional impact by income decile accounting for behavioral responses.

## Scope Notes

- **Two decision domains in scope:** vehicle investment, heating system. Energy renovation is a stretch goal.
- **Conditional logit first**, nested logit as extension.
- **Performance:** ~11x scaling factor (100k × 5 alternatives × 2 domains). Eligibility filtering mitigates.
- **Myopic decisions:** households decide based on current-year costs, not discounted future streams.
- **No peer effects:** household decisions are independent.

---
