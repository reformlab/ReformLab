# Design Note — Time Step vs Investment Decisions and OpenFisca Integration

**Project:** ReformLab  
**Author:** Lucas  
**Date:** 2026-04-01  
**Status:** Draft  
**Purpose:** Clarify the architectural distinction between simulation time-step semantics and the independent investment decision model, and define how both connect to OpenFisca without violating existing adapter boundaries.

---

## 1. Decision Summary

ReformLab should treat these as two separate but composable concerns:

1. **Simulation time step / simulation mode**
   Controls how the model moves through time.

2. **Investment decision model**
   Controls whether and how households switch technologies.

They are not the same feature and must not be implemented as one UI or one backend concept.

OpenFisca remains a **single-period computation backend** behind the existing [`ComputationAdapter`](/Users/lucas/Workspace/reformlab/src/reformlab/computation/adapter.py#L11). ReformLab adds orchestration and behavioral logic above that boundary.

---

## 2. Core Distinction

### 2.1 Simulation Time Step

This defines the temporal execution contract.

Examples:

- `annual_iterative`
  Run year by year.

- `horizon_step`
  Simulate an `X`-year policy horizon as one modeled step and return endpoint outputs.

This is about **time aggregation and execution semantics**.

### 2.2 Investment Decision Model

This defines behavioral dynamics.

Examples:

- no behavior model: households keep baseline technologies,
- discrete-choice model: households choose between alternatives based on costs, subsidies, taxes, and preferences.

This is about **technology adoption / switching behavior**.

### 2.3 Resulting Matrix

These features can exist independently:

| Simulation mode | Investment decisions | Meaning |
|---|---|---|
| `annual_iterative` | off | Standard yearly fiscal/distributional simulation |
| `annual_iterative` | on | Year-by-year adoption dynamics |
| `horizon_step` | off | Endpoint fiscal/distributional effect after `X` years |
| `horizon_step` | on | Endpoint technology distribution after `X` years of sustained policy exposure |

---

## 3. Existing Architectural Boundary

The current backend already provides the right separation of concerns:

- OpenFisca is isolated behind [`ComputationAdapter.compute(population, policy, period)`](/Users/lucas/Workspace/reformlab/src/reformlab/computation/adapter.py#L26).
- Yearly execution is orchestrated above that boundary in [`Orchestrator.run()`](/Users/lucas/Workspace/reformlab/src/reformlab/orchestrator/runner.py#L81).
- Behavioral choice logic already lives above that boundary in [`DiscreteChoiceStep`](/Users/lucas/Workspace/reformlab/src/reformlab/discrete_choice/step.py#L43).

This means:

- **Do not modify OpenFisca to “understand 5 years at once.”**
- **Do not collapse time-step logic into the discrete-choice model.**
- **Do not collapse discrete choice into UI-only configuration.**

---

## 4. Proposed Execution Model

### 4.1 Annual Iterative Mode

This is the current model.

Execution:

1. Start with population state at year `t`.
2. Run `ComputationStep` for year `t`.
3. Optionally run `DiscreteChoiceStep`.
4. Apply carry-forward / vintage updates.
5. Repeat for year `t+1`.

Output:

- yearly states,
- yearly indicators,
- optional yearly decision records.

### 4.2 Horizon Step Mode

This is the proposed new model.

Execution:

1. Start with population state at year `t`.
2. Define horizon length `X`.
3. Compute or derive `X`-year policy exposure for each household / alternative.
4. If the investment model is enabled, evaluate alternatives using aggregated `X`-year economics.
5. Produce endpoint state at year `t + X`.

Output:

- endpoint household state,
- endpoint technology distribution,
- optional aggregated indicators over the horizon,
- no requirement for yearly intermediate outputs.

This is **not** the same as:

- running annual simulation and filtering to year `t + X`,
- or skipping years in the current yearly loop.

---

## 5. How Horizon Step Connects to OpenFisca

### 5.1 What OpenFisca Should Continue Doing

OpenFisca should continue to provide:

- annual taxes/transfers,
- household-level policy calculations,
- alternative-specific economics when population expansion is used.

### 5.2 What ReformLab Must Add Above It

ReformLab must add a horizon aggregation layer that can transform annual economics into `X`-year decision signals.

Examples of aggregated features:

- cumulative subsidy over `X` years,
- cumulative tax burden over `X` years,
- discounted net cost,
- simple payback period,
- expected operating-cost difference,
- total ownership cost over `X` years.

These are not native OpenFisca outputs. They are **derived orchestration-layer constructs** built from repeated or parameterized use of OpenFisca results.

### 5.3 Clean Integration Pattern

Recommended pattern:

1. Expand population by alternatives, as already done by `DiscreteChoiceStep`.
2. Use OpenFisca via `ComputationAdapter` to compute annual household economics for each alternative.
3. Aggregate those annual results into horizon features for each household-alternative pair.
4. Feed those horizon features into the choice model.
5. Write the chosen endpoint technology/state back into ReformLab state.

This preserves the existing architectural rule:

- OpenFisca computes,
- ReformLab orchestrates and decides.

---

## 6. New Backend Concepts Required

### 6.1 Scenario Execution Mode

Add a scenario-level execution mode concept:

```text
simulation_mode = "annual_iterative" | "horizon_step"
```

### 6.2 Horizon Configuration

Add explicit horizon-step configuration:

```text
horizon_step_years: int
```

Optional future extensions:

- discounting strategy,
- exogenous-price series,
- technology cost trajectories,
- income uprating assumptions,
- domain-specific aggregation rules.

### 6.3 Horizon Aggregator

Introduce a new orchestration/domain component, conceptually:

```text
HorizonAggregator
```

Responsibility:

- derive `X`-year endpoint economics from annual policy computations,
- support multiple policy domains without changing `ComputationAdapter`.

### 6.4 Endpoint Output Contract

For `horizon_step`, outputs should include:

- endpoint year,
- simulation mode,
- horizon length,
- endpoint household states,
- endpoint decision records if behavior is enabled.

---

## 7. Validation and Governance Implications

The preflight layer must validate more than it does today.

New checks needed:

- `horizon_step_years > 0`,
- simulation mode is explicitly set,
- selected policy domain supports `horizon_step`,
- required exogenous assumptions are available for the full horizon,
- investment decisions are either disabled or fully configured,
- output semantics are compatible with the requested comparison/reporting view.

Governance and manifests must also record:

- simulation mode,
- horizon length,
- aggregation assumptions,
- discounting assumptions,
- exogenous series used,
- adapter version,
- whether results are yearly or endpoint-only.

This is required so analysts do not compare annual runs and horizon-step runs as if they were identical artifacts.

---

## 8. Frontend Implications

### 8.1 Workspace Structure

Recommended top-level stages:

1. Policies & Portfolio
2. Population
3. Investment Decisions
4. Scenario
5. Run / Results / Compare

### 8.2 Stage Ownership

**Investment Decisions**

- optional stage,
- enable/disable behavior,
- model choice,
- parameters,
- calibration/review.

**Scenario**

- simulation mode,
- annual horizon or horizon-step size,
- seed,
- inherited primary population,
- optional sensitivity population,
- final validation.

### 8.3 Skip Logic

- If investment decisions are disabled, the user can skip that stage.
- If simulation mode is `annual_iterative`, existing yearly output surfaces remain valid.
- If simulation mode is `horizon_step`, result surfaces must make clear that outputs are endpoint-only unless additional decomposition is available.

---

## 9. Recommended Implementation Strategy

### Phase A: Product and Architecture Alignment

Clarify artifacts first:

- separate `time_step / simulation mode` from `investment decisions`,
- define top-level stage ownership,
- define annual vs horizon-step output semantics.

### Phase B: Backend Contract

Implement:

- scenario execution mode,
- horizon-step validation contract,
- manifest fields,
- endpoint result metadata.

### Phase C: Domain Logic

Implement:

- horizon aggregation layer,
- first supported domain for `horizon_step`,
- integration with discrete choice.

### Phase D: UI

Implement:

- dedicated Investment Decisions stage,
- Scenario-stage simulation-mode controls,
- result-surface differentiation between yearly and endpoint outputs.

---

## 10. Recommended First Slice

The best first implementation slice is:

1. support `horizon_step` **without** investment decisions,
2. produce endpoint fiscal/distributional outputs,
3. then integrate the investment model on top.

Reason:

- it validates the execution contract independently,
- it reduces ambiguity in result semantics,
- it avoids coupling two new sources of complexity in the first slice.

Then the second slice is:

4. enable `horizon_step + investment decisions`,
5. return endpoint technology distribution.

---

## 11. BMAD Implementation Path

Recommended BMAD sequence:

1. `bmad-correct-course`
   Approve the sprint change proposal and the stage-boundary correction.

2. `bmad-edit-prd`
   Add explicit requirements for:
   - simulation mode,
   - `horizon_step`,
   - separation from investment decisions.

3. `bmad-create-ux-design`
   Update the workspace IA to a five-stage shell and define skip logic.

4. `bmad-create-architecture`
   Fold this design note into the canonical architecture decision set.

5. `bmad-create-epics-and-stories`
   Revise existing stories and add backend work for:
   - execution contract,
   - horizon aggregation,
   - endpoint outputs.

6. `bmad-check-implementation-readiness`
   Ensure PRD, UX, architecture, and epics are aligned before development.

7. `bmad-sprint-planning`
   Plan the first implementation slice:
   - `horizon_step` without behavior first,
   - then `horizon_step` with investment decisions.

---

## 12. Final Recommendation

Proceed with this principle:

> **Time-step semantics and investment decisions are independent features that meet at the orchestration layer, not inside OpenFisca.**

That gives ReformLab a clean architecture:

- OpenFisca stays a single-period calculator,
- ReformLab owns temporal orchestration,
- ReformLab owns behavioral adoption logic,
- the frontend reflects those as separate analyst decisions.
