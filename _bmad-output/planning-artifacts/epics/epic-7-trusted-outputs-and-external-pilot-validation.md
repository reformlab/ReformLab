# Epic 7: Trusted Outputs and External Pilot Validation

**User outcome:** External pilot user can validate simulation credibility against published benchmarks and run the carbon-tax workflow independently.

**Status:** done

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-701 | Story | P0 | 5 | Verify simulation outputs against published benchmarks (100k households) | done | NFR1, NFR5 |
| BKL-702 | Task | P0 | 3 | System warns analyst before exceeding memory limits | done | NFR3 |
| BKL-703 | Task | P0 | 3 | Enforce CI quality gates | done | NFR18, NFR20 |
| BKL-704 | Story | P0 | 5 | External pilot user can run complete carbon-tax workflow | done | FR35, NFR19 |
| BKL-705 | Task | P0 | 3 | Define Phase 1 exit checklist and pilot sign-off criteria | done | PRD go/no-go |

## Epic-Level Acceptance Criteria

- Analyst can run benchmark suite and see pass/fail against Phase 1 NFR targets.
- CI blocks merges on failing tests or coverage gates.
- At least one external pilot user runs the carbon-tax workflow end-to-end and confirms result credibility.
- Pilot package includes example datasets, templates, and documentation sufficient for independent execution.

## Story-Level Acceptance Criteria

**BKL-701: Verify simulation outputs against published benchmarks (100k households)**

- Given the benchmark suite and a 100k household population, when run on a standard laptop (4-core, 16GB RAM), then all benchmark tests complete and deviations are within documented tolerances.
- Given a benchmark failure, when reported, then the output identifies which metric failed, expected vs actual values, and tolerance.

**BKL-702: System warns analyst before exceeding memory limits**

- Given a population exceeding 500k households on a 16GB machine, when a run is attempted, then a clear memory warning is displayed before execution begins.

**BKL-703: Enforce CI quality gates**

- Given a pull request with failing lint checks, when CI runs, then the merge is blocked with specific lint errors listed.
- Given a pull request with test coverage below the threshold, when CI runs, then the merge is blocked with coverage report.

**BKL-704: External pilot user can run complete carbon-tax workflow**

- Given the pilot package on a clean Python environment, when installed and the example is run, then the carbon-tax workflow completes end-to-end with charts and indicators.
- Given the pilot package, when an external user follows the documentation, then they can reproduce the example results without assistance.

**BKL-705: Define Phase 1 exit checklist and pilot sign-off criteria**

- Given the exit checklist, when reviewed against completed work, then each criterion maps to a verifiable artifact or test result.

---
