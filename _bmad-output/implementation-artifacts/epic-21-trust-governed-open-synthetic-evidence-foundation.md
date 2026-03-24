# Epic 21: Trust-Governed Open + Synthetic Evidence Foundation

Status: backlog

## Epic Summary

Implement the current-phase open + synthetic evidence foundation defined in the 2026-03-23 synthetic data decision baseline. This epic turns the decision document into product and platform capabilities: explicit asset classification, trust-governed ingestion, typed structural/exogenous/calibration contracts, synthetic-versus-observed comparison, and the modelling refactors required to support exogenous inputs and richer taste parameters.

## Motivation

Epic 20 aligns the workspace around canonical scenario semantics, but it does not by itself define what kinds of evidence the scenario can safely use or claim. The updated planning baseline now makes that explicit:

- current-phase scope is `open official + synthetic`, not restricted data
- every dataset and output must be classified by `origin`, `access_mode`, and `trust_status`
- governance metadata must be surfaced in product and API contracts, not left in documentation
- calibration targets and validation benchmarks must remain distinct
- the modelling stack needs `ExogenousContext` and generalized `TasteParameters` to support the intended policy workflows

This epic makes those evidence-system rules real in the backend, API surface, and user-facing scenario experience.

## Stories

| ID | Story | SP | Priority |
|----|-------|----|----------|
| 21.1 | Implement canonical evidence asset descriptor and current-phase source matrix | 5 | P0 |
| 21.2 | Add origin/access mode/trust status contracts across backend APIs and frontend models | 5 | P0 |
| 21.3 | Implement typed structural, exogenous, calibration, and validation asset schemas | 8 | P0 |
| 21.4 | Add public synthetic asset ingestion and observed-versus-synthetic comparison flows | 8 | P0 |
| 21.5 | Separate calibration targets from validation benchmarks and implement trust-status rules | 5 | P0 |
| 21.6 | Implement `ExogenousTimeSeries` and `ExogenousContext` for scenario execution | 5 | P0 |
| 21.7 | Refactor discrete-choice and calibration for generalized `TasteParameters` | 8 | P0 |
| 21.8 | Wire the flagship scenario, docs, and regression coverage to the new evidence model | 5 | P1 |

## Dependencies

- Builds on population ingestion and generation capabilities from EPIC-11.
- Builds on scenario and orchestrator foundations from EPIC-2 and EPIC-3.
- Builds on governance and reproducibility capabilities from EPIC-5 and EPIC-16.
- Extends discrete-choice and calibration work from EPIC-14 and EPIC-15.
- Must remain compatible with the scenario-centered workspace introduced in EPIC-20.
- Stories 21.2, 21.5, 21.6, and 21.8 extend specific EPIC-20 surfaces and contracts. See per-story coordination notes below for the exact integration points.
- Uses the 2026-03-23/2026-03-24 versions of:
  - `_bmad-output/planning-artifacts/synthetic-data-decision-document-2026-03-23.md`
  - `_bmad-output/planning-artifacts/prd.md`
  - `_bmad-output/planning-artifacts/architecture.md`
  - `_bmad-output/planning-artifacts/ux-design-specification.md`

## Exit Criteria

- Current-phase evidence scope is enforced as `open official + synthetic`, with restricted connectors explicitly deferred.
- Every dataset and derived output exposed by the product can carry `origin`, `access_mode`, `trust_status`, provenance, and intended-use metadata.
- Structural, exogenous, calibration, and validation assets are represented by separate typed contracts rather than a catch-all payload.
- At least one public synthetic dataset can be ingested and compared against observed/open data in the flagship workflow.
- Calibration targets and validation benchmarks are stored and executed as distinct concepts.
- Scenario execution can consume scenario-specific exogenous inputs via `ExogenousContext`.
- Discrete-choice calibration supports generalized `TasteParameters` with fixed/calibrated parameter tracking and diagnostics.
- Docs, APIs, tests, and the flagship scenario all describe the same current-phase evidence model.

## Story Notes

### 21.1 Implement canonical evidence asset descriptor and current-phase source matrix

Create the shared asset descriptor used by ingestion, APIs, manifests, and UI surfaces. It must include source metadata plus `origin`, `access_mode`, `trust_status`, intended use, and redistribution notes. Produce a versioned source matrix for all current-phase datasets referenced by docs, demos, and the flagship workflow.

### 21.2 Add origin/access mode/trust status contracts across backend APIs and frontend models

Extend API responses and frontend types so evidence metadata is not optional or ad hoc. Population selection, data explorer, engine validation, and results surfaces must all be able to display and preserve evidence classification without inventing their own label systems.

**EPIC-20 prerequisite:** Requires the Population Library (20.4), Engine validation (20.5), and Results/Compare (20.6) surfaces to exist. This story replaces EPIC-20's placeholder population origin tags (`[Built-in]`/`[Generated]`/`[Uploaded]`) with the canonical `origin`/`access_mode`/`trust_status` contracts from Story 21.1.

### 21.3 Implement typed structural, exogenous, calibration, and validation asset schemas

Introduce a shared envelope plus typed payload contracts. `PopulationData` stays narrow; exogenous series, calibration targets, and validation benchmarks get their own types and validation rules. This story should prevent governance metadata from being mixed into domain payload objects.

### 21.4 Add public synthetic asset ingestion and observed-versus-synthetic comparison flows

Support public synthetic datasets in the same ingestion framework as open official data, but never blur their trust boundary. The flagship scenario should be able to load at least one synthetic dataset variant and present an explicit observed-versus-synthetic comparison with visible trust labels.

### 21.5 Separate calibration targets from validation benchmarks and implement trust-status rules

Define distinct storage, APIs, and execution paths for fitting versus certification. Synthetic outputs must not become `production-safe` without an explicit validation dossier, and in-sample calibration data must not silently double as validation evidence.

**EPIC-20 prerequisite:** Extends the extensible validation/preflight check registry created by EPIC-20 Story 20.5. Trust-status rules are registered as additional preflight checks within the same contract, not a parallel validation system.

### 21.6 Implement `ExogenousTimeSeries` and `ExogenousContext` for scenario execution

Add read-only scenario exogenous context with coverage validation, year-slice lookup, provenance metadata, and interpolation rules. At least one flagship domain must consume scenario-specific exogenous inputs, and scenario comparison must support differing exogenous assumptions.

**EPIC-20 prerequisite:** Extends the comparison infrastructure built by EPIC-20 Story 20.6. Exogenous assumptions are a new pluggable comparison dimension added to the existing comparison data model, not a separate comparison system.

### 21.7 Refactor discrete-choice and calibration for generalized `TasteParameters`

Refactor the current single-`beta_cost` model toward ASCs plus named coefficients with fixed/calibrated tracking, diagnostics, and migration compatibility. Preserve a compatibility path for the existing single-parameter workflow while moving the flagship domain onto the richer contract.

### 21.8 Wire the flagship scenario, docs, and regression coverage to the new evidence model

Close the loop with an end-to-end scenario that proves the new evidence contracts actually work together. Update demos, docs, manifests, and regression coverage so the current-phase story is coherent: open official data, public synthetic comparison, explicit trust labels, separated calibration/validation, and no restricted-data promises.

**EPIC-20 prerequisite:** Extends the regression suite created by EPIC-20 Story 20.8. Add evidence-specific test flows (synthetic ingestion, trust labels, calibration/validation separation) on top of the existing workspace flow coverage — do not duplicate it.

## Risks

- EPIC-20 can drift into frontend-only trust labels unless this epic defines the canonical backend contract first.
- The `TasteParameters` refactor touches calibration, provenance, demos, docs, and tests; treating it as a local type change will cause churn.
- Public synthetic ingestion can create accidental trust inflation if comparison views or APIs omit provenance and trust status.
- If validation benchmarks are not separated from calibration inputs early, the product will encode train/test leakage into its governance story.
- Exogenous time-series handling can become underspecified if frequency, vintage, and revision policy are omitted from the contract.
- The UX spec (Revision 2.0, 2026-03-24) defines population origin tags and lineage drill-down but contains no UI patterns for evidence classification badges, trust-status indicators, or synthetic-vs-observed visual distinction. Stories 21.2 and 21.4 require evidence governance UI that has not been designed. Either the UX spec needs an addendum before implementation, or these stories must include a UX design sub-task.
