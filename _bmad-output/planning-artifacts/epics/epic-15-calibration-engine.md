# Epic 15: Calibration Engine

**User outcome:** Analyst can calibrate discrete choice taste parameters against observed data so that simulated transition rates match reality.

**Status:** backlog

**Builds on:** EPIC-14 (discrete choice model), EPIC-11 (population generation)

**PRD Refs:** FR52–FR53

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-1501 | Story | P0 | 5 | Define calibration target format and load observed transition rates | backlog | FR52 |
| BKL-1502 | Story | P0 | 8 | Implement CalibrationEngine with objective function optimization | backlog | FR52 |
| BKL-1503 | Story | P0 | 5 | Implement calibration validation against holdout data | backlog | FR53 |
| BKL-1504 | Task | P0 | 3 | Record calibrated parameters in run manifests | backlog | FR52 |
| BKL-1505 | Story | P0 | 5 | Build calibration workflow notebook demo | backlog | FR52, FR53 |

## Epic-Level Acceptance Criteria

- Calibration engine produces β parameters that reduce simulation-vs-observed gap below documented threshold.
- Calibrated parameters are reproducible (deterministic optimization).
- Validation step confirms calibrated model on holdout data or known aggregates.
- Calibrated parameters are recorded in run manifests.
- Notebook demo runs end-to-end in CI.

---

## Story 15.1: Define calibration target format and load observed transition rates

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**PRD Refs:** FR52

### Acceptance Criteria

- Given observed transition rate data (e.g., vehicle adoption rates from ADEME/SDES), when formatted as calibration targets, then the format specifies: decision domain, time period, transition type (from → to), observed rate, and source metadata.
- Given a calibration target file (CSV or YAML), when loaded by the calibration engine, then targets are validated for completeness (all required fields present) and consistency (rates sum to ≤1.0 per origin state).
- Given calibration targets for multiple decision domains, when loaded, then each domain's targets are accessible independently.
- Given a calibration target with a missing or malformed field, when loaded, then a clear error message identifies the field and row.

---

## Story 15.2: Implement CalibrationEngine with objective function optimization

**Status:** backlog
**Priority:** P0
**Estimate:** 8

**Dependencies:** Story 15.1
**PRD Refs:** FR52

### Acceptance Criteria

- Given calibration targets and an initial set of β coefficients, when the calibration engine runs, then it executes the discrete choice model repeatedly with different β values to minimize the gap between simulated and observed transition rates.
- Given the calibration engine, when optimizing, then the objective function computes the distance (MSE or log-likelihood) between simulated aggregate transition rates and observed targets.
- Given the optimization process, when run with a fixed seed and initial parameters, then it converges to the same β values across runs (deterministic optimization).
- Given the calibration engine, when it completes, then it returns: optimized β coefficients per domain, final objective function value, convergence diagnostics (iterations, gradient norm, convergence flag).
- Given the calibration engine, when β coefficients produce simulated rates, then the gap between simulated and observed rates is below the documented threshold for each calibration target.

---

## Story 15.3: Implement calibration validation against holdout data

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 15.2
**PRD Refs:** FR53

### Acceptance Criteria

- Given calibrated β parameters and a holdout dataset (different time period or population subset), when validation runs, then the discrete choice model is executed with the calibrated parameters on the holdout data.
- Given validation results, when compared to holdout observed rates, then the gap metrics (MSE, mean absolute error) are computed and reported.
- Given validation metrics, when inspected, then the analyst can assess whether calibrated parameters generalize beyond the training data.
- Given calibration and validation results, when reported, then both in-sample (training) and out-of-sample (holdout) fit metrics are presented side by side.

---

## Story 15.4: Record calibrated parameters in run manifests

**Status:** backlog
**Priority:** P0
**Estimate:** 3

**Dependencies:** Story 15.2
**PRD Refs:** FR52

### Acceptance Criteria

- Given a completed calibration run, when the manifest is inspected, then it includes: calibrated β coefficients per domain, objective function type and final value, convergence diagnostics, calibration target source metadata, and holdout validation metrics.
- Given a simulation run that uses calibrated parameters, when the manifest is inspected, then it references the calibration run that produced the parameters (calibration run ID or manifest hash).
- Given calibrated parameters recorded in a manifest, when loaded for a subsequent simulation, then the exact same β values are used.

---

## Story 15.5: Build calibration workflow notebook demo

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 15.3
**PRD Refs:** FR52, FR53

### Acceptance Criteria

- Given the notebook, when run end-to-end, then it demonstrates: loading observed transition rates, running the calibration engine, inspecting convergence diagnostics, validating against holdout data, and using calibrated parameters in a simulation.
- Given the notebook, when run in CI, then it completes without errors.
- Given the notebook output, when inspected, then it shows: training vs. observed rate comparison charts, convergence trajectory plots, holdout validation metrics, and a final simulation using calibrated parameters with fleet composition outcomes.

## Scope Notes

- **Calibration targets** — observed vehicle adoption rates, heating system transition rates from public data (ADEME, SDES).
- **Objective function** — MSE or likelihood-based, to be determined during sprint planning.
- **This epic naturally follows discrete choice** — it calibrates the model that EPIC-14 builds.

---
