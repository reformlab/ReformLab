# Epic 21: Trust-Governed Open + Synthetic Evidence Foundation

**User outcome:** Every dataset, output, and model parameter exposed by the platform carries explicit origin, access mode, and trust status metadata — enabling analysts to reason about evidence quality, distinguish synthetic from observed data, and maintain calibration/validation separation.

**Status:** backlog

**Builds on:** EPIC-2 (scenarios), EPIC-3 (orchestrator), EPIC-5 (governance), EPIC-11 (populations), EPIC-14 (discrete choice), EPIC-15 (calibration), EPIC-16 (replication), EPIC-20 (scenario workspace)

**PRD Refs:** FR1, FR2, FR5-FR8, FR10-FR12, FR15-FR18, FR22-FR24

**Primary source documents:**

- `_bmad-output/planning-artifacts/synthetic-data-decision-document-2026-03-23.md`
- `_bmad-output/planning-artifacts/prd.md` (Current Program State Update, dated 2026-03-24)
- `_bmad-output/planning-artifacts/architecture.md` (frontend/API alignment update, dated 2026-03-24)
- `_bmad-output/planning-artifacts/ux-design-specification.md` (Revision 2.0, dated 2026-03-24)
- `_bmad-output/implementation-artifacts/epic-21-trust-governed-open-synthetic-evidence-foundation.md`

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-2101 | Story | P0 | 5 | Implement canonical evidence asset descriptor and current-phase source matrix | backlog | FR1, FR2, FR5 |
| BKL-2102 | Story | P0 | 5 | Add origin/access mode/trust status contracts across backend APIs and frontend models | backlog | FR5, FR6, FR7 |
| BKL-2103 | Story | P0 | 8 | Implement typed structural, exogenous, calibration, and validation asset schemas | backlog | FR8, FR10, FR11 |
| BKL-2104 | Story | P0 | 8 | Add public synthetic asset ingestion and observed-versus-synthetic comparison flows | backlog | FR12, FR15, FR16 |
| BKL-2105 | Story | P0 | 5 | Separate calibration targets from validation benchmarks and implement trust-status rules | backlog | FR17, FR18 |
| BKL-2106 | Story | P0 | 5 | Implement ExogenousTimeSeries and ExogenousContext for scenario execution | backlog | FR22, FR23 |
| BKL-2107 | Story | P0 | 8 | Refactor discrete-choice and calibration for generalized TasteParameters | backlog | FR24 |
| BKL-2108 | Story | P1 | 5 | Wire the flagship scenario, docs, and regression coverage to the new evidence model | backlog | FR1, FR2, FR5 |

## Epic-Level Acceptance Criteria

- Current-phase evidence scope is enforced as `open official + synthetic`, with restricted connectors explicitly deferred.
- Every dataset and derived output carries `origin`, `access_mode`, `trust_status`, provenance, and intended-use metadata.
- Structural, exogenous, calibration, and validation assets are represented by separate typed contracts.
- At least one public synthetic dataset can be ingested and compared against observed/open data in the flagship workflow.
- Calibration targets and validation benchmarks are stored and executed as distinct concepts.
- Scenario execution can consume scenario-specific exogenous inputs via `ExogenousContext`.
- Discrete-choice calibration supports generalized `TasteParameters` with fixed/calibrated tracking and diagnostics.
- Docs, APIs, tests, and the flagship scenario all describe the same current-phase evidence model.

## Scope Notes

- EPIC-20 can drift into frontend-only trust labels unless this epic defines the canonical backend contract first; coordinate sequencing accordingly.
- Public synthetic ingestion must never blur the trust boundary — comparison views and APIs must always show provenance and trust status.
- Calibration targets and validation benchmarks must be separated early to avoid encoding train/test leakage into the governance story.
- The `TasteParameters` refactor touches calibration, provenance, demos, docs, and tests; it is not a local type change.
- **EPIC-20 prerequisites:** Stories 21.2, 21.5, 21.6, and 21.8 extend specific EPIC-20 surfaces (Population Library 20.4, Scenario validation 20.5, comparison model 20.6, regression suite 20.8). These must integrate with EPIC-20 contracts, not create parallel systems.
- **UX spec gap:** The UX spec (Revision 2.0) defines no UI patterns for evidence classification badges, trust-status indicators, or synthetic-vs-observed visual distinction. Stories 21.2 and 21.4 require an addendum or embedded UX design sub-task.

---

## Story 21.1: Implement canonical evidence asset descriptor and current-phase source matrix

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** None

Create the shared asset descriptor used by ingestion, APIs, manifests, and UI surfaces. It must include source metadata plus `origin`, `access_mode`, `trust_status`, intended use, and redistribution notes. Produce a versioned source matrix for all current-phase datasets referenced by docs, demos, and the flagship workflow.

### Acceptance Criteria

- Given the asset descriptor, when inspected, then it includes `origin`, `access_mode`, `trust_status`, intended use, provenance, and redistribution metadata.
- Given the current-phase source matrix, when reviewed, then it covers all datasets referenced by docs, demos, and the flagship workflow.
- Given the descriptor schema, when used by ingestion, APIs, and manifests, then it is the single shared contract — no parallel definitions.

---

## Story 21.2: Add origin/access mode/trust status contracts across backend APIs and frontend models

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 21.1

Extend API responses and frontend types so evidence metadata is not optional or ad hoc. Population selection, data explorer, engine validation, and results surfaces must all be able to display and preserve evidence classification without inventing their own label systems.

**EPIC-20 prerequisite:** Requires the Population Library (20.4), Scenario validation (20.5), and Results/Compare (20.6) surfaces to exist. Replaces EPIC-20's placeholder `[Built-in]`/`[Generated]`/`[Uploaded]` tags with canonical contracts.

### Acceptance Criteria

- Given API responses for populations, runs, and results, when inspected, then they include `origin`, `access_mode`, and `trust_status` fields.
- Given frontend models, when inspected, then evidence classification is typed and non-optional.
- Given EPIC-20 placeholder tags, when this story is complete, then they are replaced by canonical evidence contracts.

---

## Story 21.3: Implement typed structural, exogenous, calibration, and validation asset schemas

**Status:** backlog
**Priority:** P0
**Estimate:** 8

**Dependencies:** Story 21.1

Introduce a shared envelope plus typed payload contracts. `PopulationData` stays narrow; exogenous series, calibration targets, and validation benchmarks get their own types and validation rules. This story should prevent governance metadata from being mixed into domain payload objects.

### Acceptance Criteria

- Given asset types, when inspected, then structural, exogenous, calibration, and validation assets each have distinct typed schemas.
- Given `PopulationData`, when inspected, then it remains narrow and does not carry governance metadata.
- Given the shared envelope, when used, then governance metadata is carried at the envelope level, not mixed into domain payloads.

---

## Story 21.4: Add public synthetic asset ingestion and observed-versus-synthetic comparison flows

**Status:** backlog
**Priority:** P0
**Estimate:** 8

**Dependencies:** Story 21.1, Story 21.2

Support public synthetic datasets in the same ingestion framework as open official data, but never blur their trust boundary. The flagship scenario should be able to load at least one synthetic dataset variant and present an explicit observed-versus-synthetic comparison with visible trust labels.

### Acceptance Criteria

- Given a public synthetic dataset, when ingested, then it is classified with correct `origin` and `trust_status` — never promoted to `production-safe` without validation.
- Given the flagship scenario, when run with synthetic data, then an observed-versus-synthetic comparison is available with visible trust labels.
- Given comparison views, when displaying synthetic data, then provenance and trust status are always visible.

---

## Story 21.5: Separate calibration targets from validation benchmarks and implement trust-status rules

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 21.1, Story 21.3

Define distinct storage, APIs, and execution paths for fitting versus certification. Synthetic outputs must not become `production-safe` without an explicit validation dossier, and in-sample calibration data must not silently double as validation evidence.

**EPIC-20 prerequisite:** Extends the extensible validation/preflight check registry created by EPIC-20 Story 20.5.

### Acceptance Criteria

- Given calibration targets and validation benchmarks, when stored, then they use distinct storage and API paths.
- Given a synthetic output, when assessed, then it cannot reach `production-safe` trust status without a validation dossier.
- Given calibration data, when used in a run, then it cannot silently serve as validation evidence.
- Given trust-status rules, when registered, then they are additional checks in the EPIC-20 preflight registry.

---

## Story 21.6: Implement ExogenousTimeSeries and ExogenousContext for scenario execution

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 21.3

Add read-only scenario exogenous context with coverage validation, year-slice lookup, provenance metadata, and interpolation rules. At least one flagship domain must consume scenario-specific exogenous inputs, and scenario comparison must support differing exogenous assumptions.

**EPIC-20 prerequisite:** Extends the comparison infrastructure built by EPIC-20 Story 20.6. Exogenous assumptions are a new pluggable comparison dimension.

### Acceptance Criteria

- Given `ExogenousContext`, when attached to a scenario, then it provides read-only access with coverage validation and year-slice lookup.
- Given exogenous inputs, when used in execution, then provenance metadata and interpolation rules are recorded.
- Given scenario comparison, when two runs differ by exogenous assumptions, then the comparison surfaces the difference as a named dimension.

---

## Story 21.7: Refactor discrete-choice and calibration for generalized TasteParameters

**Status:** backlog
**Priority:** P0
**Estimate:** 8

**Dependencies:** Story 21.3, Story 21.5

Refactor the current single-`beta_cost` model toward ASCs plus named coefficients with fixed/calibrated tracking, diagnostics, and migration compatibility. Preserve a compatibility path for the existing single-parameter workflow while moving the flagship domain onto the richer contract.

### Acceptance Criteria

- Given `TasteParameters`, when inspected, then it supports ASCs plus named coefficients with fixed/calibrated tracking.
- Given the existing single-`beta_cost` workflow, when run, then it continues to work via the compatibility path.
- Given the flagship domain, when calibrated, then it uses the generalized `TasteParameters` contract with diagnostics.

---

## Story 21.8: Wire the flagship scenario, docs, and regression coverage to the new evidence model

**Status:** backlog
**Priority:** P1
**Estimate:** 5

**Dependencies:** Story 21.4, Story 21.5, Story 21.6, Story 21.7

Close the loop with an end-to-end scenario that proves the new evidence contracts actually work together. Update demos, docs, manifests, and regression coverage so the current-phase story is coherent.

**EPIC-20 prerequisite:** Extends the regression suite created by EPIC-20 Story 20.8. Adds evidence-specific test flows on top of existing workspace flow coverage.

### Acceptance Criteria

- Given the flagship scenario, when executed end-to-end, then it demonstrates: open official data, public synthetic comparison, explicit trust labels, and separated calibration/validation.
- Given docs and manifests, when reviewed, then they describe the current-phase evidence model consistently.
- Given regression tests, when inspected, then evidence-specific flows extend (not duplicate) the EPIC-20 workspace coverage.

---
