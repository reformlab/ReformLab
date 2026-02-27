---
title: Phase 1 Implementation Backlog
project: ReformLab
date: 2026-02-25
source_documents:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
status: ready
---

# Phase 1 Implementation Backlog (OpenFisca-First)

## Scope Baseline

This backlog is derived from:

- PRD Phase 1 must-have capabilities and FR1-FR35, NFR1-NFR21.
- Architecture active blueprint and delivery sequence (OpenFisca adapter -> templates -> dynamic/vintage -> indicators/governance -> interfaces).

Out of scope in Phase 1:

- Endogenous market-clearing.
- Physical system feedback loops.
- Full behavioral equilibrium.
- Public-facing election app.

## Backlog Conventions

- Priority: `P0` (must ship in Phase 1), `P1` (ship if capacity allows after P0 complete).
- Size: story points (`SP`) using a rough Fibonacci scale (1, 2, 3, 5, 8, 13).
- Item types: `Story`, `Task`, `Spike`.
- A story is "done" only when acceptance criteria pass and tests are in CI.

## Phase 1 Epics

1. `EPIC-1`: Computation Adapter and Data Layer
2. `EPIC-2`: Scenario Templates and Registry
3. `EPIC-3`: Step-Pluggable Dynamic Orchestrator and Vintage Tracking
4. `EPIC-4`: Indicators and Scenario Comparison
5. `EPIC-5`: Governance and Reproducibility
6. `EPIC-6`: Interfaces (Python API, Notebooks, Early No-Code GUI)
7. `EPIC-7`: Trusted Outputs and External Pilot Validation

## Prioritized Backlog

### EPIC-1 Computation Adapter and Data Layer

**User outcome:** Analyst can connect OpenFisca outputs and open datasets to the framework with validated data contracts.

| ID | Type | Pri | SP | Title | Depends On | PRD Refs |
|---|---|---|---:|---|---|---|
| BKL-101 | Story | P0 | 5 | Define ComputationAdapter interface and OpenFiscaAdapter implementation | - | FR1, FR2, FR3 |
| BKL-102 | Story | P0 | 5 | Implement CSV/Parquet ingestion for OpenFisca outputs and population data | BKL-101 | FR1, FR3, NFR14 |
| BKL-103 | Story | P0 | 5 | Build input/output mapping configuration for OpenFisca variable names | BKL-101 | FR3, FR4, NFR4 |
| BKL-104 | Story | P0 | 5 | Implement open-data ingestion pipeline (synthetic population, emission factors) | BKL-102 | FR5, FR6 |
| BKL-105 | Task | P0 | 3 | Add data-quality checks with blocking field-level errors at adapter boundary | BKL-103 | FR4, FR27, NFR4 |
| BKL-106 | Story | P1 | 5 | Add direct OpenFisca API orchestration mode (version-pinned) | BKL-101 | FR2, NFR15 |
| BKL-107 | Task | P0 | 2 | Create compatibility matrix for supported OpenFisca versions | BKL-101 | NFR15, NFR21 |
| BKL-108 | Task | P0 | 3 | Set up project scaffold, dev environment, and CI smoke pipeline | - | NFR18, NFR19 |

Acceptance criteria:

- ComputationAdapter interface is defined with compute() and version() methods.
- OpenFiscaAdapter passes contract tests for CSV/Parquet input and output mapping.
- Adapter can be mocked for orchestrator unit testing.
- Open-data pipeline loads synthetic population and emission factor datasets.
- Mapping errors return exact field names and actionable messages.
- Unsupported OpenFisca version fails with explicit compatibility error.
- Adapter test fixtures run in CI.
- Repository has pyproject.toml with dependency pinning, ruff linting, mypy type checking, and pytest configured.
- CI pipeline runs lint + unit tests on every push.
- Development environment is reproducible via uv from pyproject.toml.
- Project directory structure matches architecture subsystem layout.

Story-level acceptance criteria:

**BKL-101: Define ComputationAdapter interface and OpenFiscaAdapter implementation**
- Given an OpenFisca output dataset (CSV or Parquet), when the adapter's compute() method is called, then it returns a ComputationResult with mapped output fields.
- Given a mock adapter, when the orchestrator calls compute(), then it receives valid results without requiring OpenFisca installed.
- Given an unsupported OpenFisca version, when the adapter is initialized, then it raises an explicit compatibility error with version mismatch details.

**BKL-102: Implement CSV/Parquet ingestion for OpenFisca outputs and population data**
- Given a valid CSV file with OpenFisca household outputs, when ingested through the adapter, then population data is loaded into the internal schema with correct types.
- Given a valid Parquet file, when ingested, then results match CSV ingestion for the same data.
- Given a CSV with missing required columns, when ingested, then a clear error lists the missing column names.

**BKL-103: Build input/output mapping configuration for OpenFisca variable names**
- Given a YAML mapping configuration, when loaded, then OpenFisca variable names are mapped to project schema field names.
- Given a mapping with an unknown OpenFisca variable, when validated, then an error identifies the exact field name and suggests corrections.
- Given a valid mapping, when applied to adapter output, then all mapped fields are present in the result with correct values.

**BKL-104: Implement open-data ingestion pipeline (synthetic population, emission factors)**
- Given a synthetic population dataset in CSV/Parquet, when loaded through the pipeline, then data source metadata and hash are recorded.
- Given an emission factor dataset, when loaded, then factors are accessible by category and year for template computations.
- Given a corrupted or incomplete dataset, when loaded, then the pipeline fails with a specific error before any computation begins.

**BKL-105: Add data-quality checks with blocking field-level errors at adapter boundary**
- Given adapter output with a null value in a required field, when validated, then a blocking error identifies the exact field and row.
- Given adapter output with type mismatches, when validated, then each mismatch is reported with expected vs actual types.
- Given valid adapter output, when validated, then checks pass silently and computation proceeds.

**BKL-107: Create compatibility matrix for supported OpenFisca versions**
- Given the compatibility matrix, when a user queries a specific OpenFisca version, then the matrix indicates supported/unsupported status.
- Given an OpenFisca version not in the matrix, when the adapter is initialized, then a warning is emitted with a link to the matrix.

**BKL-108: Set up project scaffold, dev environment, and CI smoke pipeline**
- Given a fresh clone of the repository, when `uv sync` is run, then all dependencies install and `pytest` runs successfully.
- Given a push to the repository, when CI triggers, then lint (ruff) and unit tests execute and report pass/fail.
- Given the project directory structure, when inspected, then it matches the architecture subsystem layout (computation/, data/, templates/, orchestrator/, vintage/, indicators/, governance/, interfaces/).

### EPIC-2 Scenario Templates and Registry

**User outcome:** Analyst can define, version, and reuse environmental policy scenarios without writing code.

| ID | Type | Pri | SP | Title | Depends On | PRD Refs |
|---|---|---|---:|---|---|---|
| BKL-201 | Story | P0 | 5 | Define scenario template schema (baseline + reform overrides) | BKL-103 | FR7, FR8, FR12 |
| BKL-202 | Story | P0 | 8 | Implement carbon-tax template pack (4-5 variants) | BKL-201 | FR7, FR10, FR11 |
| BKL-203 | Story | P0 | 5 | Implement subsidy/rebate/feebate template pack | BKL-201 | FR7, FR11 |
| BKL-204 | Story | P0 | 5 | Build scenario registry with immutable version IDs | BKL-201 | FR9, FR28 |
| BKL-205 | Story | P0 | 3 | Implement scenario cloning and baseline/reform linking | BKL-204 | FR8, FR9 |
| BKL-206 | Task | P1 | 3 | Add schema migration helper for template version changes | BKL-204 | FR9, NFR21 |
| BKL-207 | Story | P0 | 5 | Implement YAML/JSON workflow configuration with schema validation | BKL-201 | FR31, NFR4, NFR20 |

Acceptance criteria:

- Analysts can create baseline/reform scenarios from templates without code changes.
- Registry stores versioned scenario snapshots.
- Scenario validation enforces year-indexed schedules (>= 10 years configurable).
- Analyst can define and run a complete scenario workflow from a YAML configuration file without code changes.
- YAML schema is validated on load with field-level error messages.
- YAML configuration files are version-controlled and round-trip stable.
- CI tests validate shipped YAML examples against schema.

Story-level acceptance criteria:

**BKL-201: Define scenario template schema (baseline + reform overrides)**
- Given a YAML template definition with baseline parameters, when loaded, then the schema validates required fields (policy type, year schedule, parameter values).
- Given a reform defined as parameter overrides to a baseline, when loaded, then only the overridden fields differ from baseline defaults.
- Given a template with a year schedule shorter than 10 years, when validated, then a warning is emitted (error if enforcement mode is strict).

**BKL-202: Implement carbon-tax template pack (4-5 variants)**
- Given the shipped carbon-tax template pack, when listed, then at least 4 variants are available (e.g., flat rate, progressive rate, with/without dividend).
- Given a carbon-tax template, when executed with a baseline population, then tax burden and redistribution amounts are computed per household.
- Given two carbon-tax variants, when run in batch, then comparison output shows per-decile differences.

**BKL-203: Implement subsidy/rebate/feebate template pack**
- Given the subsidy template pack, when listed, then at least subsidy, rebate, and feebate templates are available.
- Given a feebate template, when applied to a population, then households above the threshold pay and households below receive.
- Given a rebate template with income-conditioned parameters, when executed, then rebate amounts vary by income group.

**BKL-204: Build scenario registry with immutable version IDs**
- Given a scenario saved to the registry, when retrieved by version ID, then the returned definition is identical to what was saved.
- Given a saved scenario, when modified and re-saved, then a new version ID is assigned and the previous version remains accessible.
- Given an invalid version ID, when queried, then a clear error indicates the version does not exist.

**BKL-205: Implement scenario cloning and baseline/reform linking**
- Given a baseline scenario, when cloned, then the clone has a new ID and identical parameters.
- Given a reform scenario linked to a baseline, when the baseline is retrieved, then the link is navigable in both directions.
- Given a clone with modifications, when saved, then it does not alter the original scenario.

**BKL-207: Implement YAML/JSON workflow configuration with schema validation**
- Given a valid YAML workflow configuration, when loaded, then the workflow executes end-to-end (data load, scenario, run, indicators).
- Given a YAML file with an invalid field, when validated, then the error message identifies the exact line and field name.
- Given a YAML file saved and reloaded, when compared, then the content is round-trip stable (no silent changes).
- Given the shipped YAML examples, when CI runs validation, then all examples pass schema checks.

### EPIC-3 Step-Pluggable Dynamic Orchestrator and Vintage Tracking

**User outcome:** Analyst can run multi-year projections with vintage tracking and get year-by-year panel results.

| ID | Type | Pri | SP | Title | Depends On | PRD Refs |
|---|---|---|---:|---|---|---|
| BKL-301 | Story | P0 | 8 | Implement yearly loop orchestrator with step pipeline architecture | BKL-202, BKL-203 | FR13, FR18 |
| BKL-302 | Story | P0 | 5 | Define orchestrator step interface and step registration mechanism | BKL-301 | FR14, FR16 |
| BKL-303 | Story | P0 | 5 | Implement carry-forward step (deterministic state updates between years) | BKL-302 | FR14, FR17, NFR10 |
| BKL-304 | Story | P0 | 8 | Implement vintage transition step for one asset class (vehicle or heating) | BKL-302, BKL-303 | FR15, FR16 |
| BKL-305 | Story | P0 | 5 | Integrate ComputationAdapter calls into orchestrator yearly loop | BKL-301, BKL-101 | FR13, FR2 |
| BKL-306 | Task | P0 | 3 | Log seed controls, step execution order, and adapter version per yearly step | BKL-301 | FR17, NFR8 |
| BKL-307 | Story | P0 | 5 | Produce scenario-year panel output dataset | BKL-304 | FR18, FR33 |

Acceptance criteria:

- Orchestrator executes a registered pipeline of steps for each year in t..t+n.
- Steps are pluggable: vintage and carry-forward ship in Phase 1; new steps can be added without modifying orchestrator core.
- OpenFisca computation is called via ComputationAdapter at each yearly iteration.
- 10-year baseline and reform runs complete end-to-end.
- Yearly state transitions are deterministic given same inputs and seeds.
- Vintage outputs are visible per year in panel results.
- Orchestrator regression tests pass for fixed fixtures.
- Step pipeline configuration is recorded in run manifest.

Story-level acceptance criteria:

**BKL-301: Implement yearly loop orchestrator with step pipeline architecture**
- Given a scenario with a 10-year horizon, when the orchestrator runs, then it executes the step pipeline for each year from t to t+9 in order.
- Given an empty step pipeline, when the orchestrator runs, then it completes without error (no-op per year).
- Given a step that raises an error at year t+3, when the orchestrator runs, then execution halts with a clear error indicating the failing step and year.

**BKL-302: Define orchestrator step interface and step registration mechanism**
- Given a custom step implementing the step interface, when registered with the orchestrator, then it is called at the correct position in the pipeline for each year.
- Given a step registered with dependencies on another step, when the pipeline is built, then steps execute in dependency order.
- Given a step with an invalid interface, when registered, then a clear error identifies the missing method or signature mismatch.

**BKL-303: Implement carry-forward step (deterministic state updates between years)**
- Given household state at year t, when carry-forward executes, then state variables are updated for year t+1 according to configured rules.
- Given identical inputs and seeds, when carry-forward runs twice, then outputs are bit-identical.
- Given no explicit period semantics in configuration, when carry-forward is configured, then validation rejects the configuration (NFR10 compliance).

**BKL-304: Implement vintage transition step for one asset class (vehicle or heating)**
- Given a vehicle fleet with age distribution at year t, when vintage transition runs, then cohorts age by one year and new vintages are added according to transition rules.
- Given identical transition rules and seeds, when run twice, then vintage state at year t+n is identical.
- Given vintage state at each year, when panel output is produced, then vintage composition is visible per year.

**BKL-305: Integrate ComputationAdapter calls into orchestrator yearly loop**
- Given a configured OpenFiscaAdapter, when the orchestrator runs year t, then the adapter's compute() is called with the correct population and policy for that year.
- Given a mock adapter, when the orchestrator runs, then the full yearly loop completes using mock results.
- Given an adapter that fails at year t+2, when the orchestrator runs, then the error includes the adapter version, year, and failure details.

**BKL-306: Log seed controls, step execution order, and adapter version per yearly step**
- Given an orchestrator run, when inspecting the log, then each yearly step shows the random seed used, the step execution order, and the adapter version.
- Given two runs with different seeds, when logs are compared, then the seed difference is visible in the log entries.

**BKL-307: Produce scenario-year panel output dataset**
- Given a completed 10-year run, when panel output is produced, then it contains one row per household per year with all computed fields.
- Given panel output, when exported to CSV/Parquet, then the file is readable by pandas/polars with correct types.
- Given baseline and reform runs, when panel outputs are compared, then per-household per-year differences are computable.

### EPIC-4 Indicators and Scenario Comparison

**User outcome:** Analyst can compute and compare distributional, welfare, and fiscal indicators across scenarios.

| ID | Type | Pri | SP | Title | Depends On | PRD Refs |
|---|---|---|---:|---|---|---|
| BKL-401 | Story | P0 | 5 | Implement distributional indicators by income decile | BKL-306 | FR19 |
| BKL-402 | Story | P0 | 3 | Implement geographic aggregation indicators | BKL-401 | FR20 |
| BKL-403 | Story | P0 | 5 | Implement welfare indicators (winners/losers, net changes) | BKL-401 | FR21 |
| BKL-404 | Story | P0 | 5 | Implement fiscal indicators (annual and cumulative) | BKL-401 | FR22 |
| BKL-405 | Story | P0 | 5 | Implement scenario comparison tables across runs | BKL-402, BKL-403, BKL-404 | FR24, FR33 |
| BKL-406 | Story | P1 | 5 | Implement custom derived indicator formulas | BKL-405 | FR23 |

Acceptance criteria:

- Indicators are generated per scenario and per year.
- Comparison outputs support side-by-side baseline/reform analysis.
- Export format is machine-readable CSV/Parquet.

Story-level acceptance criteria:

**BKL-401: Implement distributional indicators by income decile**
- Given a completed scenario run with household-level results, when distributional analysis is invoked, then indicators are computed for each of the 10 income deciles.
- Given a population with missing income data for some households, when analysis runs, then those households are flagged and excluded with a count warning.

**BKL-402: Implement geographic aggregation indicators**
- Given household results with region codes, when geographic aggregation is invoked, then indicators are grouped by region.
- Given a region code not in the reference table, when aggregated, then results include an "unmatched" category with count.

**BKL-403: Implement welfare indicators (winners/losers, net changes)**
- Given baseline and reform scenario results, when welfare indicators are computed, then winner count, loser count, and net gain/loss per decile are returned.
- Given a scenario where all households are neutral (zero net change), when computed, then winner and loser counts are both zero.

**BKL-404: Implement fiscal indicators (annual and cumulative)**
- Given a multi-year scenario run, when fiscal indicators are computed, then annual revenue, cost, and balance are returned per year.
- Given a 10-year run, when cumulative fiscal indicators are requested, then they sum correctly across all years.

**BKL-405: Implement scenario comparison tables across runs**
- Given two completed scenario runs (baseline and reform), when comparison is invoked, then a side-by-side table is produced with all indicator types.
- Given comparison output, when exported to CSV/Parquet, then the file is readable with correct column headers and types.

### EPIC-5 Governance and Reproducibility

**User outcome:** Analyst can trust and reproduce any simulation run through immutable manifests and lineage tracking.

| ID | Type | Pri | SP | Title | Depends On | PRD Refs |
|---|---|---|---:|---|---|---|
| BKL-501 | Story | P0 | 5 | Define immutable run manifest schema v1 | BKL-204 | FR25, NFR9 |
| BKL-502 | Story | P0 | 5 | Capture assumptions/mappings/parameters in manifests | BKL-501 | FR26, FR27 |
| BKL-503 | Story | P0 | 5 | Implement run lineage graph (scenario run -> yearly child runs) | BKL-501, BKL-301 | FR29 |
| BKL-504 | Task | P0 | 3 | Hash input/output artifacts and store in manifest | BKL-501 | FR25, NFR12 |
| BKL-505 | Story | P0 | 5 | Add reproducibility check harness for deterministic reruns | BKL-503 | NFR6, NFR7 |
| BKL-506 | Task | P1 | 3 | Add warning system for unvalidated templates/configs | BKL-502 | FR27 |

Acceptance criteria:

- Each run emits one parent manifest plus linked yearly manifests.
- Manifest includes OpenFisca adapter version, scenario version, data hashes, and seeds.
- Rerun harness demonstrates reproducibility for benchmark fixtures.

Story-level acceptance criteria:

**BKL-501: Define immutable run manifest schema v1**
- Given a completed simulation run, when the manifest is generated, then it contains engine version, adapter version, scenario version, data hashes, seeds, timestamps, and parameter snapshot.
- Given a generated manifest, when any field is modified, then integrity checks detect the tampering.

**BKL-502: Capture assumptions/mappings/parameters in manifests**
- Given a run with custom mapping configuration, when the manifest is inspected, then all mappings and assumption sources are listed with their values.
- Given a run using an unvalidated template, when the manifest is generated, then a warning flag is included in the manifest metadata.

**BKL-503: Implement run lineage graph (scenario run -> yearly child runs)**
- Given a 10-year scenario run, when lineage is queried, then one parent manifest links to 10 yearly child manifests.
- Given a yearly child manifest, when its parent is queried, then the parent scenario run is returned.

**BKL-504: Hash input/output artifacts and store in manifest**
- Given input CSV/Parquet files, when hashed, then SHA-256 hashes are stored in the manifest without embedding raw data.
- Given output artifacts, when hashed, then output hashes are stored and can be verified after the run.

**BKL-505: Add reproducibility check harness for deterministic reruns**
- Given a completed run and its manifest, when the harness re-executes with the same inputs and seeds, then outputs are bit-identical.
- Given a run on a different machine (same Python and dependency versions), when re-executed, then outputs match within documented tolerances.

### EPIC-6 Interfaces (Python API, Notebooks, Early No-Code GUI)

**User outcome:** User can operate the full analysis workflow from Python API, notebooks, or a no-code GUI.

| ID | Type | Pri | SP | Title | Depends On | PRD Refs |
|---|---|---|---:|---|---|---|
| BKL-601 | Story | P0 | 5 | Implement stable Python API for run orchestration | BKL-301, BKL-405, BKL-501 | FR30, NFR16 |
| BKL-602 | Story | P0 | 5 | Build quickstart notebook (OpenFisca + environmental templates) | BKL-601 | FR34, NFR19 |
| BKL-603 | Story | P0 | 5 | Build advanced notebook (multi-year + vintage + comparison) | BKL-601 | FR30, FR35 |
| BKL-604a | Story | P0 | 3 | Build static GUI prototype: configuration and simulation flows | — | FR32 |
| BKL-604b | Story | P0 | 5 | Wire GUI prototype to FastAPI backend | BKL-601, BKL-604a | FR32 |
| BKL-605 | Task | P0 | 3 | Add export actions in API/GUI for CSV/Parquet outputs | BKL-405, BKL-604b | FR33 |
| BKL-606 | Task | P1 | 3 | Improve operational error UX (mapping and run-state failures) | BKL-604b | FR4, FR27 |

Acceptance criteria:

- API supports full run lifecycle from data ingest to comparison outputs.
- New user can complete quickstart workflow in under 30 minutes.
- GUI supports baseline/reform scenario operations without code.

Story-level acceptance criteria:

**BKL-601: Implement stable Python API for run orchestration**
- Given the Python API, when a user calls the run method with a scenario configuration, then a complete orchestration cycle executes and returns results.
- Given API objects (scenarios, results, manifests), when displayed in a Jupyter notebook, then sensible `__repr__` output is shown.
- Given an invalid scenario configuration, when passed to the API, then a clear error is raised before execution begins.

**BKL-602: Build quickstart notebook (OpenFisca + environmental templates)**
- Given a fresh install of the package, when the quickstart notebook is run cell by cell, then it completes without errors and produces distributional charts.
- Given the quickstart notebook, when timed end-to-end, then total execution is under 30 minutes including reading instructions.

**BKL-603: Build advanced notebook (multi-year + vintage + comparison)**
- Given the advanced notebook, when executed, then it demonstrates a multi-year run with vintage tracking and baseline/reform comparison.
- Given the advanced notebook, when run in CI, then it passes without modification.

**BKL-604a: Build static GUI prototype: configuration and simulation flows**
- Given the prototype, when opened in a browser, then the analyst can navigate the full configuration flow (population selection → policy template → parameter editing → assumptions review) and the simulation flow (run → results → comparison) using clickable screens.
- Given the prototype, when reviewed by the product owner, then screen layout and navigation can be adjusted before backend integration begins.
- Given the prototype, when inspected, then it uses the target stack (React + Shadcn/ui + Tailwind) so screens are reusable in the final app.

**BKL-604b: Wire GUI prototype to FastAPI backend**
- Given the wired GUI, when an analyst creates a new scenario from a template, then no code editing is required.
- Given the wired GUI, when an analyst clones a baseline and modifies parameters, then a reform scenario is created and linked to the baseline.
- Given two completed runs in the GUI, when comparison is invoked, then side-by-side indicator tables are displayed.

**BKL-605: Add export actions in API/GUI for CSV/Parquet outputs**
- Given completed scenario results, when export to CSV is invoked, then a valid CSV file is produced with correct headers.
- Given completed scenario results, when export to Parquet is invoked, then a valid Parquet file is produced readable by pandas/polars.

### EPIC-7 Trusted Outputs and External Pilot Validation

**User outcome:** External pilot user can validate simulation credibility against published benchmarks and run the carbon-tax workflow independently.

| ID | Type | Pri | SP | Title | Depends On | PRD Refs |
|---|---|---|---:|---|---|---|
| BKL-701 | Story | P0 | 5 | Analyst can verify simulation outputs against published benchmarks (100k households) | BKL-301, BKL-401 | NFR1, NFR5 |
| BKL-702 | Task | P0 | 3 | System warns analyst before exceeding memory limits on large populations | BKL-701 | NFR3 |
| BKL-703 | Task | P0 | 3 | Enforce CI quality gates (lint, tests, coverage thresholds) | BKL-101 | NFR18, NFR20 |
| BKL-704 | Story | P0 | 5 | External pilot user can run complete carbon-tax workflow from shipped package | BKL-602, BKL-603, BKL-501 | FR35, NFR19 |
| BKL-705 | Task | P0 | 3 | Define Phase 1 exit checklist and pilot sign-off criteria | BKL-704 | PRD go/no-go criteria |

Acceptance criteria:

- Analyst can run benchmark suite and see pass/fail against Phase 1 NFR targets for their environment.
- CI blocks merges on failing tests or coverage gates.
- At least one external pilot user runs the carbon-tax workflow end-to-end and confirms result credibility.
- Pilot package includes example datasets, templates, and documentation sufficient for independent execution.

Story-level acceptance criteria:

**BKL-701: Analyst can verify simulation outputs against published benchmarks (100k households)**
- Given the benchmark suite and a 100k household population, when run on a standard laptop (4-core, 16GB RAM), then all benchmark tests complete in under 10 seconds.
- Given benchmark results, when compared to published reference values, then deviations are within documented tolerances.
- Given a benchmark failure, when reported, then the output identifies which metric failed, expected vs actual values, and tolerance.

**BKL-702: System warns analyst before exceeding memory limits on large populations**
- Given a population exceeding 500k households on a 16GB machine, when a run is attempted, then a clear memory warning is displayed before execution begins.
- Given a population within limits, when a run is attempted, then no warning is shown and execution proceeds normally.

**BKL-703: Enforce CI quality gates (lint, tests, coverage thresholds)**
- Given a pull request with failing lint checks, when CI runs, then the merge is blocked with specific lint errors listed.
- Given a pull request with test coverage below the threshold, when CI runs, then the merge is blocked with coverage report.

**BKL-704: External pilot user can run complete carbon-tax workflow from shipped package**
- Given the pilot package on a clean Python environment, when `pip install reformlab` and the example are run, then the carbon-tax workflow completes end-to-end with charts and indicators.
- Given the pilot package, when an external user follows the documentation, then they can reproduce the example results without assistance.

**BKL-705: Define Phase 1 exit checklist and pilot sign-off criteria**
- Given the exit checklist, when reviewed against completed work, then each criterion maps to a verifiable artifact or test result.
- Given pilot sign-off criteria, when presented to the external pilot user, then they can confirm or deny each criterion based on their experience.

## Suggested Phase 1 Delivery Plan (6 Sprints)

1. Sprint 1: BKL-108, BKL-101 to BKL-105, BKL-201, BKL-703.
2. Sprint 2: BKL-202 to BKL-205, BKL-207, BKL-301, BKL-302.
3. Sprint 3: BKL-303 to BKL-307, BKL-501, BKL-502.
4. Sprint 4: BKL-401 to BKL-405, BKL-503, BKL-504, BKL-601.
5. Sprint 5: BKL-602, BKL-603, BKL-604, BKL-605, BKL-701, BKL-702.
6. Sprint 6: BKL-505, BKL-704, BKL-705, plus remaining P1 pull-ins if capacity exists.

## Phase 1 Exit Criteria (Backlog Gate)

Phase 1 is complete when all are true:

1. All `P0` stories are done.
2. 10-year deterministic run with vintage tracking passes regression tests.
3. Core indicators and comparison outputs are available via API and GUI.
4. Full manifest + lineage is emitted for every run.
5. Performance and reproducibility NFR checks pass for benchmark fixtures.
6. At least one external pilot user runs the workflow and confirms credibility.

## Open Questions To Resolve During Grooming

1. Which asset class is first for vintage tracking: vehicles or heating systems?
2. Should OpenFisca API orchestration (`BKL-106`) remain Phase 1 `P1` or move to Phase 2?
3. What minimum GUI scope is acceptable if Sprint 5 overruns?
4. Which external pilot partner is the go/no-go reference user?
