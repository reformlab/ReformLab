---
title: ReformLab — Epics and Stories
project: ReformLab
description: Single source of truth for all epics, stories, and acceptance criteria
date: 2026-03-02
source_documents:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-03-02.md
  - _bmad-output/planning-artifacts/phase-2-design-note-discrete-choice-household-decisions.md
  - _bmad-output/implementation-artifacts/sprint-status.yaml
---

# Epics and Stories

Single source of truth for all epics and stories across the project. For detailed dev notes, subtask checklists, and agent records, see individual story files in `_bmad-output/implementation-artifacts/`.

## Overview

| Epic | Title | Phase | Status | Stories |
|------|-------|-------|--------|---------|
| Epic 1 | Computation Adapter and Data Layer | 1 | done | 8 |
| Epic 2 | Scenario Templates and Registry | 1 | done | 7 |
| Epic 3 | Step-Pluggable Dynamic Orchestrator and Vintage Tracking | 1 | done | 7 |
| Epic 4 | Indicators and Scenario Comparison | 1 | done | 6 |
| Epic 5 | Governance and Reproducibility | 1 | done | 6 |
| Epic 6 | Interfaces (Python API, Notebooks, Early No-Code GUI) | 1 | done | 8 |
| Epic 7 | Trusted Outputs and External Pilot Validation | 1 | done | 5 |
| Epic 8 | Post-Phase-1 Validation Spikes | 1 | done | 2 |
| Epic 9 | OpenFisca Adapter Hardening | 1 | done | 5 |
| Epic 10 | API Ergonomics and Developer Experience | 1 | done | 2 |
| Epic 11 | Realistic Population Generation Library | 2 | done | 8 |
| Epic 12 | Policy Portfolio Model | 2 | done | 5 |
| Epic 13 | Additional Policy Templates + Extensibility | 2 | backlog | 4 |
| Epic 14 | Discrete Choice Model for Household Decisions | 2 | backlog | 7 |
| Epic 15 | Calibration Engine | 2 | backlog | 5 |
| Epic 16 | Replication Package Export | 2 | backlog | 4 |
| Epic 17 | GUI Showcase Product | 2 | backlog | 8 |

## Conventions

- **Priority:** `P0` (must ship), `P1` (ship if capacity allows after P0)
- **Size:** Story points (`SP`) on Fibonacci scale (1, 2, 3, 5, 8, 13)
- **Types:** `Story`, `Task`, `Spike`
- **Done:** Acceptance criteria pass and tests are in CI
- **Story files:** `_bmad-output/implementation-artifacts/{epic}-{story-slug}.md`

---

## Epic 1: Computation Adapter and Data Layer

_User outcome: Analyst can connect OpenFisca outputs and open datasets to the framework with validated data contracts._

_Status: done_

### Story 1.1: Define ComputationAdapter interface and OpenFiscaAdapter implementation

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR1, FR2, FR3
**Original ID:** BKL-101

### Story 1.2: Implement CSV/Parquet ingestion for OpenFisca outputs and population data

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR1, FR3, NFR14
**Original ID:** BKL-102

### Story 1.3: Build input/output mapping configuration for OpenFisca variable names

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR3, FR4, NFR4
**Original ID:** BKL-103

### Story 1.4: Implement open-data ingestion pipeline (synthetic population, emission factors)

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR5, FR6
**Original ID:** BKL-104

### Story 1.5: Add data-quality checks with blocking field-level errors at adapter boundary

**Status:** done
**Priority:** P0
**Estimate:** 3 SP
**Type:** Task
**PRD Refs:** FR4, FR27, NFR4
**Original ID:** BKL-105

### Story 1.6: Add direct OpenFisca API orchestration mode (version-pinned)

**Status:** done
**Priority:** P1
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR2, NFR15
**Original ID:** BKL-106

### Story 1.7: Create compatibility matrix for supported OpenFisca versions

**Status:** done
**Priority:** P0
**Estimate:** 2 SP
**Type:** Task
**PRD Refs:** NFR15, NFR21
**Original ID:** BKL-107

### Story 1.8: Set up project scaffold, dev environment, and CI smoke pipeline

**Status:** done
**Priority:** P0
**Estimate:** 3 SP
**Type:** Task
**PRD Refs:** NFR18, NFR19
**Original ID:** BKL-108

### Epic-Level Acceptance Criteria

- ComputationAdapter interface is defined with `compute()` and `version()` methods.
- OpenFiscaAdapter passes contract tests for CSV/Parquet input and output mapping.
- Adapter can be mocked for orchestrator unit testing.
- Open-data pipeline loads synthetic population and emission factor datasets.
- Mapping errors return exact field names and actionable messages.
- Unsupported OpenFisca version fails with explicit compatibility error.
- Adapter test fixtures run in CI.
- Repository has pyproject.toml with dependency pinning, ruff linting, mypy type checking, and pytest configured.
- CI pipeline runs lint + unit tests on every push.

### Story-Level Acceptance Criteria

**BKL-101: Define ComputationAdapter interface and OpenFiscaAdapter implementation**

- Given an OpenFisca output dataset (CSV or Parquet), when the adapter's `compute()` method is called, then it returns a ComputationResult with mapped output fields.
- Given a mock adapter, when the orchestrator calls `compute()`, then it receives valid results without requiring OpenFisca installed.
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
- Given the project directory structure, when inspected, then it matches the architecture subsystem layout.

---

## Epic 2: Scenario Templates and Registry

_User outcome: Analyst can define, version, and reuse environmental policy scenarios without writing code._

_Status: done_

### Story 2.1: Define scenario template schema (baseline + reform overrides)

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR7, FR8, FR12
**Original ID:** BKL-201

### Story 2.2: Implement carbon-tax template pack (4-5 variants)

**Status:** done
**Priority:** P0
**Estimate:** 8 SP
**Type:** Story
**PRD Refs:** FR7, FR10, FR11
**Original ID:** BKL-202

### Story 2.3: Implement subsidy/rebate/feebate template pack

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR7, FR11
**Original ID:** BKL-203

### Story 2.4: Build scenario registry with immutable version IDs

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR9, FR28
**Original ID:** BKL-204

### Story 2.5: Implement scenario cloning and baseline/reform linking

**Status:** done
**Priority:** P0
**Estimate:** 3 SP
**Type:** Story
**PRD Refs:** FR8, FR9
**Original ID:** BKL-205

### Story 2.6: Add schema migration helper for template version changes

**Status:** done
**Priority:** P1
**Estimate:** 3 SP
**Type:** Task
**PRD Refs:** FR9, NFR21
**Original ID:** BKL-206

### Story 2.7: Implement YAML/JSON workflow configuration with schema validation

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR31, NFR4, NFR20
**Original ID:** BKL-207

### Epic-Level Acceptance Criteria

- Analysts can create baseline/reform scenarios from templates without code changes.
- Registry stores versioned scenario snapshots.
- Scenario validation enforces year-indexed schedules (>= 10 years configurable).
- Analyst can define and run a complete scenario workflow from a YAML configuration file without code changes.
- YAML schema is validated on load with field-level error messages.
- YAML configuration files are version-controlled and round-trip stable.

### Story-Level Acceptance Criteria

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

---

## Epic 3: Step-Pluggable Dynamic Orchestrator and Vintage Tracking

_User outcome: Analyst can run multi-year projections with vintage tracking and get year-by-year panel results._

_Status: done_

### Story 3.1: Implement yearly loop orchestrator with step pipeline architecture

**Status:** done
**Priority:** P0
**Estimate:** 8 SP
**Type:** Story
**PRD Refs:** FR13, FR18
**Original ID:** BKL-301

### Story 3.2: Define orchestrator step interface and step registration mechanism

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR14, FR16
**Original ID:** BKL-302

### Story 3.3: Implement carry-forward step (deterministic state updates between years)

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR14, FR17, NFR10
**Original ID:** BKL-303

### Story 3.4: Implement vintage transition step for one asset class (vehicle or heating)

**Status:** done
**Priority:** P0
**Estimate:** 8 SP
**Type:** Story
**PRD Refs:** FR15, FR16
**Original ID:** BKL-304

### Story 3.5: Integrate ComputationAdapter calls into orchestrator yearly loop

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR13, FR2
**Original ID:** BKL-305

### Story 3.6: Log seed controls, step execution order, and adapter version per yearly step

**Status:** done
**Priority:** P0
**Estimate:** 3 SP
**Type:** Task
**PRD Refs:** FR17, NFR8
**Original ID:** BKL-306

### Story 3.7: Produce scenario-year panel output dataset

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR18, FR33
**Original ID:** BKL-307

### Epic-Level Acceptance Criteria

- Orchestrator executes a registered pipeline of steps for each year in t..t+n.
- Steps are pluggable: vintage and carry-forward ship in Phase 1; new steps can be added without modifying orchestrator core.
- OpenFisca computation is called via ComputationAdapter at each yearly iteration.
- 10-year baseline and reform runs complete end-to-end.
- Yearly state transitions are deterministic given same inputs and seeds.
- Vintage outputs are visible per year in panel results.
- Step pipeline configuration is recorded in run manifest.

### Story-Level Acceptance Criteria

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

- Given a configured OpenFiscaAdapter, when the orchestrator runs year t, then the adapter's `compute()` is called with the correct population and policy for that year.
- Given a mock adapter, when the orchestrator runs, then the full yearly loop completes using mock results.
- Given an adapter that fails at year t+2, when the orchestrator runs, then the error includes the adapter version, year, and failure details.

**BKL-306: Log seed controls, step execution order, and adapter version per yearly step**

- Given an orchestrator run, when inspecting the log, then each yearly step shows the random seed used, the step execution order, and the adapter version.
- Given two runs with different seeds, when logs are compared, then the seed difference is visible in the log entries.

**BKL-307: Produce scenario-year panel output dataset**

- Given a completed 10-year run, when panel output is produced, then it contains one row per household per year with all computed fields.
- Given panel output, when exported to CSV/Parquet, then the file is readable by pandas/polars with correct types.
- Given baseline and reform runs, when panel outputs are compared, then per-household per-year differences are computable.

---

## Epic 4: Indicators and Scenario Comparison

_User outcome: Analyst can compute and compare distributional, welfare, and fiscal indicators across scenarios._

_Status: done_

### Story 4.1: Implement distributional indicators by income decile

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR19
**Original ID:** BKL-401

### Story 4.2: Implement geographic aggregation indicators

**Status:** done
**Priority:** P0
**Estimate:** 3 SP
**Type:** Story
**PRD Refs:** FR20
**Original ID:** BKL-402

### Story 4.3: Implement welfare indicators (winners/losers, net changes)

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR21
**Original ID:** BKL-403

### Story 4.4: Implement fiscal indicators (annual and cumulative)

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR22
**Original ID:** BKL-404

### Story 4.5: Implement scenario comparison tables across runs

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR24, FR33
**Original ID:** BKL-405

### Story 4.6: Implement custom derived indicator formulas

**Status:** done
**Priority:** P1
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR23
**Original ID:** BKL-406

### Epic-Level Acceptance Criteria

- Indicators are generated per scenario and per year.
- Comparison outputs support side-by-side baseline/reform analysis.
- Export format is machine-readable CSV/Parquet.

### Story-Level Acceptance Criteria

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

**BKL-406: Implement custom derived indicator formulas**

- Given a user-defined formula referencing existing indicator fields, when the formula is registered and invoked, then it produces a new derived indicator column with correct values.
- Given an invalid formula (e.g., referencing a nonexistent field), when registered, then a clear error identifies the problem before computation begins.

---

## Epic 5: Governance and Reproducibility

_User outcome: Analyst can trust and reproduce any simulation run through immutable manifests and lineage tracking._

_Status: done (BKL-502, BKL-504, and BKL-505 are partial stubs — see [Phase 1 retrospective GAP 3](../implementation-artifacts/phase-1-retro-2026-02-28.md))_

### Story 5.1: Define immutable run manifest schema v1

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR25, NFR9
**Original ID:** BKL-501

### Story 5.2: Capture assumptions/mappings/parameters in manifests

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR26, FR27
**Original ID:** BKL-502

### Story 5.3: Implement run lineage graph (scenario run -> yearly child runs)

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR29
**Original ID:** BKL-503

### Story 5.4: Hash input/output artifacts and store in manifest

**Status:** done
**Priority:** P0
**Estimate:** 3 SP
**Type:** Task
**PRD Refs:** FR25, NFR12
**Original ID:** BKL-504

### Story 5.5: Add reproducibility check harness for deterministic reruns

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** NFR6, NFR7
**Original ID:** BKL-505

### Story 5.6: Add warning system for unvalidated templates/configs

**Status:** done
**Priority:** P1
**Estimate:** 3 SP
**Type:** Task
**PRD Refs:** FR27
**Original ID:** BKL-506

### Epic-Level Acceptance Criteria

- Each run emits one parent manifest plus linked yearly manifests.
- Manifest includes OpenFisca adapter version, scenario version, data hashes, and seeds.
- Rerun harness demonstrates reproducibility for benchmark fixtures.

### Story-Level Acceptance Criteria

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

**BKL-506: Add warning system for unvalidated templates/configs**

- Given a scenario using a template not yet marked as validated, when a run is initiated, then a visible warning is emitted before execution proceeds.
- Given a validated template, when a run is initiated, then no warning is emitted.

---

## Epic 6: Interfaces (Python API, Notebooks, Early No-Code GUI)

_User outcome: User can operate the full analysis workflow from Python API, notebooks, or a no-code GUI._

_Status: done_

### Story 6.1: Implement stable Python API for run orchestration

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR30, NFR16
**Original ID:** BKL-601

### Story 6.2: Build quickstart notebook

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR34, NFR19
**Original ID:** BKL-602

### Story 6.3: Build advanced notebook (multi-year + vintage + comparison)

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR30, FR35
**Original ID:** BKL-603

### Story 6.4: Build static GUI prototype

**Status:** done
**Priority:** P0
**Estimate:** 3 SP
**Type:** Story
**PRD Refs:** FR32
**Original ID:** BKL-604a

### Story 6.5: Wire GUI prototype to FastAPI backend

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR32
**Original ID:** BKL-604b

### Story 6.6: Add export actions in API/GUI for CSV/Parquet outputs

**Status:** done
**Priority:** P0
**Estimate:** 3 SP
**Type:** Task
**PRD Refs:** FR33
**Original ID:** BKL-605

### Story 6.7: Improve operational error UX

**Status:** done
**Priority:** P1
**Estimate:** 3 SP
**Type:** Task
**PRD Refs:** FR4, FR27
**Original ID:** BKL-606

### Story 6.8: Rework notebook UX (policy-first)

**Status:** done
**Priority:** P0
**Estimate:** 3 SP
**Type:** Story
**PRD Refs:** FR34

### Epic-Level Acceptance Criteria

- API supports full run lifecycle from data ingest to comparison outputs.
- GUI supports baseline/reform scenario operations without code.

### Story-Level Acceptance Criteria

**BKL-601: Implement stable Python API for run orchestration**

- Given the Python API, when a user calls the run method with a scenario configuration, then a complete orchestration cycle executes and returns results.
- Given API objects (scenarios, results, manifests), when displayed in a Jupyter notebook, then sensible `__repr__` output is shown.
- Given an invalid scenario configuration, when passed to the API, then a clear error is raised before execution begins.

**BKL-602: Build quickstart notebook**

- Given a fresh install of the package, when the quickstart notebook is run cell by cell, then it completes without errors and produces distributional charts.

**BKL-603: Build advanced notebook (multi-year + vintage + comparison)**

- Given the advanced notebook, when executed, then it demonstrates a multi-year run with vintage tracking and baseline/reform comparison.
- Given the advanced notebook, when run in CI, then it passes without modification.

**BKL-604a: Build static GUI prototype**

- Given the prototype, when opened in a browser, then the analyst can navigate the full configuration and simulation flows using clickable screens.
- Given the prototype, when inspected, then it uses the target stack (React + Shadcn/ui + Tailwind) so screens are reusable in the final app.

**BKL-604b: Wire GUI prototype to FastAPI backend**

- Given the wired GUI, when an analyst creates a new scenario from a template, then no code editing is required.
- Given the wired GUI, when an analyst clones a baseline and modifies parameters, then a reform scenario is created and linked to the baseline.
- Given two completed runs in the GUI, when comparison is invoked, then side-by-side indicator tables are displayed.

**BKL-605: Add export actions in API/GUI for CSV/Parquet outputs**

- Given completed scenario results, when export to CSV is invoked, then a valid CSV file is produced with correct headers.
- Given completed scenario results, when export to Parquet is invoked, then a valid Parquet file is produced readable by pandas/polars.

---

## Epic 7: Trusted Outputs and External Pilot Validation

_User outcome: External pilot user can validate simulation credibility against published benchmarks and run the carbon-tax workflow independently._

_Status: done_

### Story 7.1: Verify simulation outputs against published benchmarks (100k households)

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** NFR1, NFR5
**Original ID:** BKL-701

### Story 7.2: System warns analyst before exceeding memory limits

**Status:** done
**Priority:** P0
**Estimate:** 3 SP
**Type:** Task
**PRD Refs:** NFR3
**Original ID:** BKL-702

### Story 7.3: Enforce CI quality gates

**Status:** done
**Priority:** P0
**Estimate:** 3 SP
**Type:** Task
**PRD Refs:** NFR18, NFR20
**Original ID:** BKL-703

### Story 7.4: External pilot user can run complete carbon-tax workflow

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR35, NFR19
**Original ID:** BKL-704

### Story 7.5: Define Phase 1 exit checklist and pilot sign-off criteria

**Status:** done
**Priority:** P0
**Estimate:** 3 SP
**Type:** Task
**PRD Refs:** PRD go/no-go
**Original ID:** BKL-705

### Epic-Level Acceptance Criteria

- Analyst can run benchmark suite and see pass/fail against Phase 1 NFR targets.
- CI blocks merges on failing tests or coverage gates.
- At least one external pilot user runs the carbon-tax workflow end-to-end and confirms result credibility.
- Pilot package includes example datasets, templates, and documentation sufficient for independent execution.

### Story-Level Acceptance Criteria

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

## Epic 8: Post-Phase-1 Validation Spikes

_User outcome: Platform developers confirm that the adapter layer works end-to-end with real OpenFisca and at production scale._

_Status: done_

### Story 8.1: End-to-end OpenFisca integration spike

**Status:** done
**Type:** Spike
**Original ID:** 8-1

### Story 8.2: Scale validation: 100k synthetic population benchmarks

**Status:** done
**Type:** Story
**PRD Refs:** NFR1, NFR3
**Original ID:** 8-2

### Epic-Level Acceptance Criteria

- Adapter processes real OpenFisca-France computations end-to-end without error.
- Platform handles 100k-household populations within NFR performance targets.
- All findings and gaps are documented for follow-up in EPIC-9.

### Story-Level Acceptance Criteria

**8-1: End-to-end OpenFisca integration spike**

- `openfisca-france` installs and is importable in the project's Python 3.13 environment.
- `OpenFiscaApiAdapter` loads a real `CountryTaxBenefitSystem` and returns a valid version string.
- Real computation returns numeric values (not all zeros, not NaN) for known variables and periods.
- Multi-entity population works via `SimulationBuilder.build_from_entities()`.
- Variable mapping round-trip produces correct project-schema column names.
- Findings documented in [8-1 spike findings](../implementation-artifacts/spike-findings-8-1-openfisca-integration.md).

**8-2: Scale validation — 100k synthetic population benchmarks**

- Persistent 100k synthetic population generated with seed 42, registered via `DatasetManifest` with SHA-256 hash.
- BKL-701 benchmark suite passes with the persistent population.
- Full simulation completes within NFR1 target (< 10 seconds) for 100k households.

---

## Epic 9: OpenFisca Adapter Hardening

_User outcome: Adapter handles real-world OpenFisca entity models, variable periodicities, and multi-entity outputs correctly._

_Status: done_

### Epic-Level Acceptance Criteria

- Adapter correctly handles all OpenFisca-France entity types and variable periodicities.
- A reference test suite validates adapter output against known French tax-benefit values.

---

### Story 9.1: Fix entity-dict plural keys

**Status:** done
**Priority:** P0
**Estimate:** 1

Entity dicts use correct plural key names as expected by OpenFisca's `SimulationBuilder`.
Fixed during 8-1 code review.

#### Acceptance Criteria

- Entity dicts use correct plural key names as expected by OpenFisca's `SimulationBuilder`.

---

### Story 9.2: Handle multi-entity output arrays

**Status:** done
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 9.1

#### Acceptance Criteria

- Given output variables that return per-entity arrays (e.g., per-menage, per-foyer_fiscal), when the adapter processes results, then arrays are correctly mapped to their respective entity tables.
- Given a variable defined on `foyer_fiscal` entity, when results are returned, then the output array length matches the number of foyers fiscaux, not the number of individuals.
- Given mixed-entity output variables, when processed, then each variable's values are stored in the correct entity-level result table with proper entity IDs.

---

### Story 9.3: Add variable periodicity handling

**Status:** done
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 9.2

#### Acceptance Criteria

- Given variables with different periodicities (monthly, yearly), when `compute()` is called, then the adapter converts periods correctly before passing to OpenFisca.
- Given a monthly variable requested for a yearly period, when computed, then the adapter handles period conversion according to OpenFisca conventions.
- Given an invalid period format, when passed to the adapter, then a clear error identifies the expected format.

---

### Story 9.4: Define population data 4-entity format

**Status:** done
**Priority:** P0
**Estimate:** 8

**Dependencies:** Story 9.2

#### Acceptance Criteria

- Given the French tax-benefit model's 4 entities (individu, menage, famille, foyer_fiscal), when a population dataset is loaded, then all entity relationships are preserved and passable to `SimulationBuilder`.
- Given a population with membership arrays for all 4 entities, when built via `SimulationBuilder`, then entity group memberships are correctly assigned.
- Given a population dataset missing a required entity relationship, when loaded, then validation fails with a clear error identifying the missing relationship.

---

### Story 9.5: OpenFisca-France reference test suite

**Status:** done
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 9.3, Story 9.4

#### Acceptance Criteria

- Given a set of known French tax-benefit scenarios with published expected values, when run through the adapter, then computed values match reference values within documented tolerances.
- Given the reference test suite, when run in CI, then all tests pass and tolerance thresholds are documented.
- Given a new OpenFisca-France version, when the reference suite is run, then regressions are detected and reported.

---

## Epic 10: API Ergonomics and Developer Experience

_User outcome: Analyst experiences a clean, intuitive API where naming is consistent, redundancy is eliminated, and the type system guides correct usage._

_Status: done_

### Epic-Level Acceptance Criteria

- `BaselineScenario` accepts `policy=` as the field name for the policy parameters object.
- `policy_type` is automatically inferred from the parameters class type (e.g., `CarbonTaxParameters` implies `PolicyType.CARBON_TAX`).
- `policy_type` can still be explicitly provided to override inference.
- All YAML pack files, JSON schema, loader, registry, server routes, and frontend types are updated consistently.
- All existing tests pass with the new API, and backward compatibility is documented.

---

### Story 10.1: Rename `parameters` to `policy` on scenario types

**Status:** done
**Priority:** P1
**Estimate:** 5

**Dependencies:** None

#### Acceptance Criteria

- Given `BaselineScenario(policy=my_policy)`, when constructed, then the policy object is stored and accessible via `.policy`.
- Given existing YAML pack files using `parameters:` key, when loaded, then backward-compatible parsing accepts both `parameters:` and `policy:` keys.
- Given the JSON schema for scenario templates, when updated, then it accepts both `parameters` and `policy` field names.
- Given all tests, when run, then they pass with the renamed field.

---

### Story 10.2: Infer `policy_type` from parameters class

**Status:** done
**Priority:** P1
**Estimate:** 5

**Dependencies:** Story 10.1

#### Acceptance Criteria

- Given `BaselineScenario(policy=CarbonTaxParameters(...))` without `policy_type`, when constructed, then `policy_type` is automatically set to `PolicyType.CARBON_TAX`.
- Given all four built-in parameter types, when used without explicit `policy_type`, then the correct `PolicyType` is inferred.
- Given a custom `PolicyParameters` subclass without a registered mapping, when used without explicit `policy_type`, then a clear error is raised explaining how to register the mapping.
- Given an explicit `policy_type` that contradicts the parameters class, when constructed, then the explicit value is used (with a warning).

---

# Phase 2 Epics

Phase 2 builds on the complete Phase 1 foundation (10 epics, 57 stories, 1,537 tests). Each epic delivers a notebook demo that previews the eventual GUI workflow. See [Sprint Change Proposal 2026-03-02](sprint-change-proposal-2026-03-02.md) for full rationale.

**Implementation order:** EPIC-11 → 12 → 13 → 14 → 15 → 16 → 17

---

## Epic 11: Realistic Population Generation Library

_User outcome: Analyst can build a credible French household population from real public data sources, choosing merge methods with transparent assumptions, and producing a population with all attributes needed for policy simulation._

_Status: done_

_Builds on: EPIC-1 (data layer), EPIC-5 (governance)_

_PRD Refs: FR36–FR42_

### Story 11.1: Define DataSourceLoader protocol and caching infrastructure

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR36
**Original ID:** BKL-1101

### Story 11.2: Implement INSEE data source loader

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR36, FR37
**Original ID:** BKL-1102

### Story 11.3: Implement Eurostat, ADEME, and SDES data source loaders

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR36, FR37
**Original ID:** BKL-1103

### Story 11.4: Define MergeMethod protocol and implement uniform distribution method

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR38, FR39
**Original ID:** BKL-1104

### Story 11.5: Implement IPF and conditional sampling merge methods

**Status:** done
**Priority:** P0
**Estimate:** 8 SP
**Type:** Story
**PRD Refs:** FR38, FR39
**Original ID:** BKL-1105

### Story 11.6: Build PopulationPipeline builder with assumption recording

**Status:** done
**Priority:** P0
**Estimate:** 8 SP
**Type:** Story
**PRD Refs:** FR40, FR41
**Original ID:** BKL-1106

### Story 11.7: Implement population validation against known marginals

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR42
**Original ID:** BKL-1107

### Story 11.8: Build French household example pipeline and pedagogical notebook

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR40, FR37
**Original ID:** BKL-1108

### Epic-Level Acceptance Criteria

- At least 4 institutional data source loaders are functional (download, cache, schema-validate): INSEE, Eurostat, ADEME, SDES.
- At least 3 statistical merge methods are implemented with `MergeMethod` protocol: uniform distribution, IPF, conditional sampling.
- The French example pipeline produces a population with at least: household_id, income, household_size, region, housing_type, heating_type, vehicle_type, vehicle_age, energy_consumption, carbon_emissions.
- Every merge step records an assumption in the governance layer.
- Generated population validates against source marginals within documented tolerances.
- Methods library docstrings include plain-language explanations of what each method assumes.
- Pedagogical notebook runs end-to-end in CI.

### Story-Level Acceptance Criteria

**BKL-1101: Define DataSourceLoader protocol and caching infrastructure**

- Given the `DataSourceLoader` protocol, when a new loader is implemented, then it must provide `download()`, `status()`, and `schema()` methods.
- Given a dataset downloaded for the first time, when cached, then the cache stores a schema-validated Parquet file with SHA-256 hash in `~/.reformlab/cache/sources/{provider}/{dataset_id}/`.
- Given a previously cached dataset, when the loader is called again, then the cache is used without network access.
- Given a network failure with an existing cache, when the loader is called, then the stale cache is used with a governance warning logged.
- Given `REFORMLAB_OFFLINE=1` environment variable, when a loader is called and cache misses, then it fails explicitly without attempting network access.
- Given the cache, when `status()` is called, then it returns `CacheStatus` with cached flag, path, download timestamp, hash, and staleness indicator.

**BKL-1102: Implement INSEE data source loader**

- Given a valid INSEE dataset identifier, when the loader downloads it, then a schema-validated `pa.Table` is returned with documented columns.
- Given the INSEE loader, when queried for available datasets, then at least household income distribution and household composition tables are available.
- Given an invalid or unavailable INSEE dataset ID, when requested, then a clear error identifies the specific dataset and suggests alternatives.
- Given the INSEE loader, when run in CI, then tests use fixture files (no real network calls) marked with `pytest -m network` for opt-in integration tests.

**BKL-1103: Implement Eurostat, ADEME, and SDES data source loaders**

- Given the Eurostat loader, when called with a valid dataset code, then EU-level household data is returned as a schema-validated `pa.Table`.
- Given the ADEME loader, when called, then energy consumption and emission factor datasets are returned with documented schemas.
- Given the SDES loader, when called, then vehicle fleet composition and age distribution data is returned.
- Given all three loaders, when run, then each follows the `DataSourceLoader` protocol and integrates with the caching infrastructure from BKL-1101.
- Given CI tests for all loaders, then they use fixture files and do not require network access.

**BKL-1104: Define MergeMethod protocol and implement uniform distribution method**

- Given the `MergeMethod` protocol, when a new method is implemented, then it must accept two `pa.Table` inputs plus a config, and return a merged table plus an assumption record.
- Given two tables with no shared sample, when merged using uniform distribution, then each row from Table A is matched with a randomly drawn row from Table B with equal probability.
- Given a uniform merge, when the assumption record is inspected, then it states: "Each household in source A is matched to a household in source B with uniform probability — this assumes no correlation between the variables in the two sources."
- Given the uniform method docstring, when read, then it includes a plain-language explanation of the independence assumption and when this is appropriate vs. problematic.

**BKL-1105: Implement IPF and conditional sampling merge methods**

- Given two tables and a set of known marginal constraints, when IPF is applied, then the merged population matches the target marginals within documented tolerances.
- Given IPF output, when the assumption record is inspected, then it lists all marginal constraints used and the convergence status.
- Given two tables with a conditioning variable (e.g., income bracket), when conditional sampling is applied, then matches are drawn within strata defined by the conditioning variable.
- Given conditional sampling output, when the assumption record is inspected, then it states the conditioning variable and explains the conditional independence assumption.
- Given both methods, when docstrings are read, then each includes a plain-language explanation suitable for a policy analyst (not just a statistician).

**BKL-1106: Build PopulationPipeline builder with assumption recording**

- Given a sequence of loaders and merge methods, when composed into a `PopulationPipeline`, then the pipeline executes each step in order and produces a final merged population.
- Given a pipeline execution, when completed, then every merge step's assumption record is captured in the governance layer via the existing `capture.py` integration.
- Given a pipeline, when inspected after execution, then the full chain of steps is visible: which source → which method → which output, for every merge.
- Given a pipeline step that fails (e.g., schema mismatch between two tables), when executed, then the error identifies the exact step, the two tables involved, and the mismatched columns.
- Given a population produced by the pipeline, when its governance record is queried, then all assumption records from all merge steps are retrievable.

**BKL-1107: Implement population validation against known marginals**

- Given a generated population and a set of reference marginal distributions (e.g., income distribution by decile from INSEE), when validation is run, then each marginal is compared with a documented distance metric.
- Given validation results, when a marginal exceeds the tolerance threshold, then a warning identifies the specific marginal, expected vs. actual values, and the tolerance used.
- Given validation results, when all marginals pass, then a validation summary is produced confirming the population matches reference distributions.
- Given validation output, when recorded in governance, then the validation status and per-marginal results are part of the population's assumption chain.

**BKL-1108: Build French household example pipeline and pedagogical notebook**

- Given the example pipeline, when executed, then it produces a French household population with at least: household_id, income, household_size, region, housing_type, heating_type, vehicle_type, vehicle_age, energy_consumption, carbon_emissions.
- Given the pedagogical notebook, when run cell by cell, then each merge step is preceded by a plain-language explanation of the method and its assumption, followed by a summary chart showing the result.
- Given the notebook, when run in CI, then it completes without errors.
- Given the notebook, when read by an analyst unfamiliar with statistical matching, then the plain-language explanations make each methodological choice understandable without consulting external references.

### Scope Notes

- **Start with uniform distribution** as the simplest method (equal probability assumption), then layer IPF and conditional sampling.
- **One complete French household example** is the primary deliverable — proving end-to-end pipeline with real INSEE data.
- **Pedagogical notebook** teaches by doing: real data source names, plain-language assumption statements before each merge, summary charts after.
- **Data download/cache infrastructure** — module handles fetching and caching public datasets from institutional APIs/downloads.

---

## Epic 12: Policy Portfolio Model

_User outcome: Analyst can compose multiple individual policy templates into a named portfolio and run simulations with bundled policies applied together._

_Status: done_

_Builds on: EPIC-2 (templates, registry), EPIC-3 (orchestrator)_

_PRD Refs: FR43–FR46_

### Story 12.1: Define PolicyPortfolio dataclass and composition logic

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR43
**Original ID:** BKL-1201

### Story 12.2: Implement portfolio compatibility validation and conflict resolution

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR43, FR44
**Original ID:** BKL-1202

### Story 12.3: Extend orchestrator to execute policy portfolios

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR44
**Original ID:** BKL-1203

### Story 12.4: Extend scenario registry with portfolio versioning

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR43
**Original ID:** BKL-1204

### Story 12.5: Implement multi-portfolio comparison and notebook demo

**Status:** done
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR45
**Original ID:** BKL-1205

### Epic-Level Acceptance Criteria

- Analyst can create a portfolio from 2+ individual policy templates.
- Orchestrator executes a portfolio, applying all bundled policies at each yearly step.
- Portfolio is versioned in the scenario registry alongside individual scenarios.
- Portfolio comparison produces side-by-side indicator tables.
- Custom policy templates participate in portfolios alongside built-in templates.
- Notebook demo runs end-to-end in CI.

### Story-Level Acceptance Criteria

**BKL-1201: Define PolicyPortfolio dataclass and composition logic**

- Given 2+ individual `PolicyConfig` objects, when composed into a `PolicyPortfolio`, then the portfolio is a named, frozen dataclass containing all policies.
- Given a portfolio, when inspected, then it lists all constituent policies with their types and parameter summaries.
- Given a portfolio, when serialized to YAML, then it round-trips correctly (save and reload produces identical object).

**BKL-1202: Implement portfolio compatibility validation and conflict resolution**

- Given two policies in a portfolio that affect the same household attribute (e.g., two different carbon tax rates), when validated, then a conflict is detected and reported with the exact parameter names.
- Given a portfolio with non-conflicting policies (e.g., carbon tax + vehicle subsidy), when validated, then validation passes.
- Given a conflict, when the analyst provides an explicit resolution rule (e.g., "sum" or "first wins"), then the conflict is resolved and recorded in the portfolio metadata.
- Given an unresolvable conflict with no resolution rule, when the portfolio is executed, then it fails before computation with a clear error listing the conflicting policies and parameters.

**BKL-1203: Extend orchestrator to execute policy portfolios**

- Given a portfolio with 3 policies, when the orchestrator runs a yearly step, then all 3 policies are applied to the population for that year.
- Given a portfolio execution, when completed over 10 years, then yearly panel output reflects the combined effect of all policies.
- Given the orchestrator receiving a portfolio instead of a single policy, when run, then no changes to `ComputationAdapter` interface or orchestrator core logic are required (portfolio is unwrapped in the template application layer).
- Given a single-policy scenario (backward compatibility), when run through the portfolio-aware orchestrator, then it behaves identically to pre-portfolio execution.

**BKL-1204: Extend scenario registry with portfolio versioning**

- Given a portfolio saved to the registry, when retrieved by version ID, then the returned portfolio is identical to what was saved, including all constituent policies.
- Given a portfolio, when a constituent policy is modified and the portfolio is re-saved, then a new version ID is assigned.
- Given the registry, when queried, then portfolios and individual scenarios are both listable and distinguishable by type.

**BKL-1205: Implement multi-portfolio comparison and notebook demo**

- Given 3 completed portfolio runs (each against the same baseline), when comparison is invoked, then a side-by-side table shows all indicator types per portfolio.
- Given multi-portfolio comparison, when cross-comparison metrics are computed, then aggregate metrics are available (e.g., "which portfolio maximizes welfare?", "which has lowest fiscal cost?").
- Given the pairwise comparison API from Phase 1, when used with portfolios, then it works as a convenience alias (N=1 case).
- Given the notebook demo, when run in CI, then it demonstrates portfolio creation, execution, comparison, and cross-comparison metrics end-to-end.

### Scope Notes

- **Portfolios are compositions** of existing individual policy templates — no new policy type concept.
- **Conflict resolution** — when two policies in a portfolio affect the same parameter, the composition layer resolves or raises an explicit error.
- **Naming example:** Portfolio "Green Transition 2030" = carbon tax (€100/tCO2) + vehicle bonus (€5k EV subsidy) + MaPrimeRénov' (renovation aid) + feebate (vehicle malus).

---

## Epic 13: Additional Policy Templates + Extensibility

_User outcome: Analyst can define custom policy templates and use new built-in templates beyond the Phase 1 set, with all templates portfolio-ready._

_Status: backlog_

_Builds on: EPIC-2 (templates), EPIC-12 (portfolios)_

_PRD Refs: FR46_

### Story 13.1: Define custom template authoring API and registration

**Status:** backlog
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR46
**Original ID:** BKL-1301

### Story 13.2: Implement vehicle malus template (new built-in)

**Status:** backlog
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR46
**Original ID:** BKL-1302

### Story 13.3: Implement energy poverty aid template (new built-in)

**Status:** backlog
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR46
**Original ID:** BKL-1303

### Story 13.4: Validate custom templates in portfolios and build notebook demo

**Status:** backlog
**Priority:** P0
**Estimate:** 3 SP
**Type:** Story
**PRD Refs:** FR46
**Original ID:** BKL-1304

### Epic-Level Acceptance Criteria

- At least 2 new built-in templates are shipped (candidates: vehicle malus, energy poverty aid, building energy performance standards — to be determined during sprint planning).
- Analyst can author a custom template from Python and register it.
- Custom templates participate in portfolios alongside built-in templates.
- Template schema validation accepts custom templates.
- Notebook demo runs end-to-end in CI.

### Story-Level Acceptance Criteria

**BKL-1301: Define custom template authoring API and registration**

- Given a Python class implementing the template interface (parameters dataclass + apply function), when registered with the template system, then it is available for use in scenarios and portfolios.
- Given a custom template, when validated, then the schema validation accepts it if it conforms to the template protocol.
- Given a custom template with a missing required method, when registered, then a clear error identifies the missing method or signature mismatch.
- Given a registered custom template, when used in a YAML scenario configuration, then it loads and executes like a built-in template.

**BKL-1302: Implement vehicle malus template (new built-in)**

- Given the vehicle malus template, when applied to a population with vehicle attributes, then a malus (penalty) is computed for high-emission vehicles based on configurable emission thresholds.
- Given the vehicle malus template with year-indexed schedules, when run over 10 years, then malus rates follow the configured yearly schedule.
- Given the vehicle malus template, when composed into a portfolio with a carbon tax and vehicle subsidy, then all three policies apply without conflict.

**BKL-1303: Implement energy poverty aid template (new built-in)**

- Given the energy poverty aid template, when applied to a population, then households below a configurable income threshold and above a configurable energy expenditure share receive aid.
- Given the template with income-conditioned parameters, when executed, then aid amounts vary by income group and energy burden.
- Given the template, when composed into a portfolio with a carbon tax, then the aid offsets carbon tax burden for eligible households.

**BKL-1304: Validate custom templates in portfolios and build notebook demo**

- Given a custom template authored by an analyst, when added to a portfolio alongside built-in templates, then the portfolio executes correctly with all templates applied.
- Given the notebook demo, when run in CI, then it demonstrates: custom template authoring, registration, portfolio inclusion, execution, and comparison against a portfolio using only built-in templates.
- Given the custom template authoring guide in the notebook, when read by an analyst, then the steps to create and register a new template are clear without consulting external documentation.

### Scope Notes

- **Extensibility is the primary goal** — the template system must be open for analyst-defined policies, not just the shipped templates.
- **New templates should be policy-relevant** to French environmental policy context.

---

## Epic 14: Discrete Choice Model for Household Decisions

_User outcome: Analyst can run multi-year simulations where households make investment decisions (vehicle, heating, renovation) in response to policy signals, with decisions feeding back into subsequent years._

_Status: backlog_

_Builds on: EPIC-3 (orchestrator, step protocol), EPIC-11 (realistic population with asset attributes), EPIC-12 (policy portfolios)_

_PRD Refs: FR47–FR51_

_Reference: [Phase 2 Design Note: Discrete Choice Model](phase-2-design-note-discrete-choice-household-decisions.md)_

### Story 14.1: Implement DiscreteChoiceStep with population expansion pattern

**Status:** backlog
**Priority:** P0
**Estimate:** 8 SP
**Type:** Story
**PRD Refs:** FR47, FR48
**Original ID:** BKL-1401

### Story 14.2: Implement conditional logit model with seed-controlled draws

**Status:** backlog
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR47, FR49
**Original ID:** BKL-1402

### Story 14.3: Implement vehicle investment decision domain

**Status:** backlog
**Priority:** P0
**Estimate:** 8 SP
**Type:** Story
**PRD Refs:** FR47, FR50
**Original ID:** BKL-1403

### Story 14.4: Implement heating system decision domain

**Status:** backlog
**Priority:** P0
**Estimate:** 8 SP
**Type:** Story
**PRD Refs:** FR47, FR50
**Original ID:** BKL-1404

### Story 14.5: Implement eligibility filtering for performance optimization

**Status:** backlog
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR48
**Original ID:** BKL-1405

### Story 14.6: Extend panel output and manifests with decision records

**Status:** backlog
**Priority:** P0
**Estimate:** 3 SP
**Type:** Task
**PRD Refs:** FR50, FR51
**Original ID:** BKL-1406

### Story 14.7: Build 10-year behavioral simulation notebook demo

**Status:** backlog
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR47
**Original ID:** BKL-1407

### Epic-Level Acceptance Criteria

- `DiscreteChoiceStep` registers via standard step protocol without modifying orchestrator core.
- Population expansion pattern works: clone households × alternatives, evaluate via OpenFisca, reshape to cost matrix.
- Conditional logit model produces realistic choice distributions for vehicle and heating domains.
- 10-year run with 100k households completes within acceptable time on laptop.
- Identical seeds produce identical household decisions across runs.
- Panel output records every decision for every household every year (chosen alternative, probabilities, utilities).
- Taste parameters (β coefficients) appear in run manifests.
- Eligibility filtering reduces expanded population for performance (only eligible households face choices).
- Notebook demo runs end-to-end in CI.

### Story-Level Acceptance Criteria

**BKL-1401: Implement DiscreteChoiceStep with population expansion pattern**

- Given the `DiscreteChoiceStep`, when registered with the orchestrator, then it implements the `OrchestratorStep` protocol and executes at the correct position in the yearly pipeline (after vintage transitions, before state carry-forward).
- Given a population of N households and a choice set of M alternatives, when expansion runs, then M copies of each household are created with attributes modified per alternative.
- Given an expanded population, when passed to `ComputationAdapter.compute()`, then OpenFisca evaluates all N×M rows in one vectorized batch call.
- Given OpenFisca results for the expanded population, when reshaped, then an N×M cost matrix is produced with one cost per household per alternative.
- Given the orchestrator core, when `DiscreteChoiceStep` is added, then no modifications to `ComputationAdapter` interface or orchestrator loop logic are required.

**BKL-1402: Implement conditional logit model with seed-controlled draws**

- Given an N×M cost matrix and taste parameters (β coefficients), when the logit model computes, then choice probabilities are `P(j|C_i) = exp(V_ij) / Σ_k exp(V_ik)` for each household.
- Given choice probabilities and a random seed, when draws are made, then each household is assigned exactly one chosen alternative per decision domain.
- Given identical cost matrices and identical seeds, when draws are made twice, then the chosen alternatives are identical across runs.
- Given a different seed, when draws are made, then the household-level choices differ but the aggregate distribution remains statistically consistent.
- Given the logit model, when probabilities are computed, then all probability vectors sum to 1.0 (within floating-point tolerance) for each household.

**BKL-1403: Implement vehicle investment decision domain**

- Given the vehicle decision domain, when configured, then the choice set includes at minimum: keep current vehicle, buy petrol, buy diesel, buy hybrid, buy EV, buy no vehicle.
- Given a household with vehicle attributes, when the domain evaluates alternatives, then utility inputs include: purchase cost (net of subsidy), annual fuel/electricity cost, annual carbon tax, maintenance.
- Given a household that chooses a new vehicle, when the state is updated, then the household's vehicle attributes change and a new vintage cohort entry is created (age=0).
- Given a household that keeps their current vehicle, when the state is updated, then vehicle attributes are unchanged.

**BKL-1404: Implement heating system decision domain**

- Given the heating system domain, when configured, then the choice set includes at minimum: keep current, gas boiler, heat pump, electric, wood/pellet.
- Given a household with heating attributes, when the domain evaluates alternatives, then utility inputs include: equipment cost (net of subsidy), annual energy cost by fuel type, annual carbon tax by fuel type, maintenance.
- Given a household that switches heating systems, when the state is updated, then `heating_type`, `energy_consumption`, and related attributes change, and a new vintage entry is created.
- Given both vehicle and heating domains configured, when the orchestrator runs a year, then domains execute sequentially (vehicle first, then heating) and the second domain sees the state updated by the first.

**BKL-1405: Implement eligibility filtering for performance optimization**

- Given eligibility rules (e.g., only households whose vehicle is older than 10 years face the vehicle choice), when the population is expanded, then only eligible households are cloned × alternatives.
- Given a population of 100k households where 30k are eligible for vehicle choice, when expanded with 5 alternatives, then the expanded population is 150k rows (not 500k).
- Given eligibility filtering, when a 10-year run with 100k households and 2 domains completes, then execution time is within the performance budget documented in the design note.
- Given a household that is not eligible for a decision domain, when the step runs, then the household retains its current state without evaluation.
- Given eligibility rules, when recorded in the run manifest, then the rules and the count of eligible vs. ineligible households per domain per year are documented.

**BKL-1406: Extend panel output and manifests with decision records**

- Given a completed discrete choice run, when panel output is inspected, then each household-year row includes: `decision_domain`, `chosen_alternative`, `choice_probabilities` (array), and `utility_values` (array).
- Given a run with discrete choice, when the manifest is inspected, then taste parameters (β coefficients) for each domain are recorded.
- Given panel output with decision records, when exported to Parquet, then decision columns are correctly typed and readable by pandas/polars.

**BKL-1407: Build 10-year behavioral simulation notebook demo**

- Given the notebook, when run end-to-end, then it demonstrates: population with asset attributes, policy portfolio configuration, 10-year dynamic run with discrete choice, year-by-year fleet composition changes, and distributional indicators.
- Given the notebook, when run in CI, then it completes without errors.
- Given the notebook output, when inspected, then it shows: aggregate vehicle fleet turnover charts (EV adoption over time), heating system transition charts, and distributional impact by income decile accounting for behavioral responses.

### Scope Notes

- **Two decision domains in scope:** vehicle investment, heating system. Energy renovation is a stretch goal.
- **Conditional logit first**, nested logit as extension.
- **Performance:** ~11x scaling factor (100k × 5 alternatives × 2 domains). Eligibility filtering mitigates.
- **Myopic decisions:** households decide based on current-year costs, not discounted future streams.
- **No peer effects:** household decisions are independent.

---

## Epic 15: Calibration Engine

_User outcome: Analyst can calibrate discrete choice taste parameters against observed data so that simulated transition rates match reality._

_Status: backlog_

_Builds on: EPIC-14 (discrete choice model), EPIC-11 (population generation)_

_PRD Refs: FR52–FR53_

### Story 15.1: Define calibration target format and load observed transition rates

**Status:** backlog
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR52
**Original ID:** BKL-1501

### Story 15.2: Implement CalibrationEngine with objective function optimization

**Status:** backlog
**Priority:** P0
**Estimate:** 8 SP
**Type:** Story
**PRD Refs:** FR52
**Original ID:** BKL-1502

### Story 15.3: Implement calibration validation against holdout data

**Status:** backlog
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR53
**Original ID:** BKL-1503

### Story 15.4: Record calibrated parameters in run manifests

**Status:** backlog
**Priority:** P0
**Estimate:** 3 SP
**Type:** Task
**PRD Refs:** FR52
**Original ID:** BKL-1504

### Story 15.5: Build calibration workflow notebook demo

**Status:** backlog
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR52, FR53
**Original ID:** BKL-1505

### Epic-Level Acceptance Criteria

- Calibration engine produces β parameters that reduce simulation-vs-observed gap below documented threshold.
- Calibrated parameters are reproducible (deterministic optimization).
- Validation step confirms calibrated model on holdout data or known aggregates.
- Calibrated parameters are recorded in run manifests.
- Notebook demo runs end-to-end in CI.

### Story-Level Acceptance Criteria

**BKL-1501: Define calibration target format and load observed transition rates**

- Given observed transition rate data (e.g., vehicle adoption rates from ADEME/SDES), when formatted as calibration targets, then the format specifies: decision domain, time period, transition type (from → to), observed rate, and source metadata.
- Given a calibration target file (CSV or YAML), when loaded by the calibration engine, then targets are validated for completeness (all required fields present) and consistency (rates sum to ≤1.0 per origin state).
- Given calibration targets for multiple decision domains, when loaded, then each domain's targets are accessible independently.
- Given a calibration target with a missing or malformed field, when loaded, then a clear error message identifies the field and row.

**BKL-1502: Implement CalibrationEngine with objective function optimization**

- Given calibration targets and an initial set of β coefficients, when the calibration engine runs, then it executes the discrete choice model repeatedly with different β values to minimize the gap between simulated and observed transition rates.
- Given the calibration engine, when optimizing, then the objective function computes the distance (MSE or log-likelihood) between simulated aggregate transition rates and observed targets.
- Given the optimization process, when run with a fixed seed and initial parameters, then it converges to the same β values across runs (deterministic optimization).
- Given the calibration engine, when it completes, then it returns: optimized β coefficients per domain, final objective function value, convergence diagnostics (iterations, gradient norm, convergence flag).
- Given the calibration engine, when β coefficients produce simulated rates, then the gap between simulated and observed rates is below the documented threshold for each calibration target.

**BKL-1503: Implement calibration validation against holdout data**

- Given calibrated β parameters and a holdout dataset (different time period or population subset), when validation runs, then the discrete choice model is executed with the calibrated parameters on the holdout data.
- Given validation results, when compared to holdout observed rates, then the gap metrics (MSE, mean absolute error) are computed and reported.
- Given validation metrics, when inspected, then the analyst can assess whether calibrated parameters generalize beyond the training data.
- Given calibration and validation results, when reported, then both in-sample (training) and out-of-sample (holdout) fit metrics are presented side by side.

**BKL-1504: Record calibrated parameters in run manifests**

- Given a completed calibration run, when the manifest is inspected, then it includes: calibrated β coefficients per domain, objective function type and final value, convergence diagnostics, calibration target source metadata, and holdout validation metrics.
- Given a simulation run that uses calibrated parameters, when the manifest is inspected, then it references the calibration run that produced the parameters (calibration run ID or manifest hash).
- Given calibrated parameters recorded in a manifest, when loaded for a subsequent simulation, then the exact same β values are used.

**BKL-1505: Build calibration workflow notebook demo**

- Given the notebook, when run end-to-end, then it demonstrates: loading observed transition rates, running the calibration engine, inspecting convergence diagnostics, validating against holdout data, and using calibrated parameters in a simulation.
- Given the notebook, when run in CI, then it completes without errors.
- Given the notebook output, when inspected, then it shows: training vs. observed rate comparison charts, convergence trajectory plots, holdout validation metrics, and a final simulation using calibrated parameters with fleet composition outcomes.

### Scope Notes

- **Calibration targets** — observed vehicle adoption rates, heating system transition rates from public data (ADEME, SDES).
- **Objective function** — MSE or likelihood-based, to be determined during sprint planning.
- **This epic naturally follows discrete choice** — it calibrates the model that EPIC-14 builds.

---

## Epic 16: Replication Package Export

_User outcome: Researcher can export a self-contained package that reproduces any simulation on a clean environment._

_Status: backlog_

_Builds on: EPIC-5 (governance, manifests), all prior Phase 2 epics_

_PRD Refs: FR54–FR55_

### Story 16.1: Implement replication package export with manifest index

**Status:** backlog
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR54
**Original ID:** BKL-1601

### Story 16.2: Implement replication package import and reproduction

**Status:** backlog
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR54, FR55
**Original ID:** BKL-1602

### Story 16.3: Include population generation assumptions and calibration provenance

**Status:** backlog
**Priority:** P0
**Estimate:** 3 SP
**Type:** Task
**PRD Refs:** FR54
**Original ID:** BKL-1603

### Story 16.4: Build replication workflow notebook demo

**Status:** backlog
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR54, FR55
**Original ID:** BKL-1604

### Epic-Level Acceptance Criteria

- Export produces a self-contained directory/archive with all artifacts needed for reproduction.
- Package contents: population data or generation config, scenario/portfolio config, template definitions, run manifests, seeds, results.
- Import on a clean environment with `pip install reformlab` reproduces results within documented tolerances.
- Package includes all assumption records from population generation.
- Manifest integrity checks pass on reimport.
- Notebook demo runs end-to-end in CI.

### Story-Level Acceptance Criteria

**BKL-1601: Implement replication package export with manifest index**

- Given a completed simulation run, when the analyst exports a replication package, then a self-contained directory is created with a manifest index file listing all included artifacts.
- Given the exported package, when its contents are inspected, then it includes: population data (or generation config + seed), scenario/portfolio configuration (YAML), template definitions used, run manifests with all parameters and seeds, and simulation results.
- Given the export, when optionally compressed, then the package is a single archive file (zip or tar.gz) that can be shared.
- Given a run that used calibrated parameters, when exported, then the package includes the calibrated β coefficients and references the calibration run metadata.
- Given the manifest index, when parsed, then it lists every artifact with its role (input/config/output), hash for integrity verification, and relative path within the package.

**BKL-1602: Implement replication package import and reproduction**

- Given a replication package, when imported on a clean environment with `pip install reformlab`, then all configuration and data artifacts are restored to the correct locations.
- Given an imported package, when the simulation is re-executed, then results match the original within documented floating-point tolerances.
- Given an imported package, when manifest integrity checks run, then all artifact hashes match the recorded values (no corruption or tampering).
- Given a package with a missing or corrupted artifact, when imported, then a clear error identifies which artifact failed integrity checks.
- Given an imported package, when the reproduction run completes, then a comparison report is generated showing original vs. reproduced results with any discrepancies flagged.

**BKL-1603: Include population generation assumptions and calibration provenance**

- Given a run that used a generated population (EPIC-11), when the replication package is exported, then it includes the population generation configuration: data sources used, merge methods, statistical assumptions, and the generation seed.
- Given a run that used calibrated parameters (EPIC-15), when exported, then the package includes calibration targets, objective function type, convergence diagnostics, and the final β values.
- Given a package with population generation config, when imported and regenerated on a different machine, then the population is identical (deterministic generation from seed + config).
- Given the assumption records in the package, when inspected by a reviewer, then every methodological choice in the pipeline is traceable from data source to final result.

**BKL-1604: Build replication workflow notebook demo**

- Given the notebook, when run end-to-end, then it demonstrates: running a simulation, exporting a replication package, clearing local state, importing the package, reproducing the simulation, and comparing original vs. reproduced results.
- Given the notebook, when run in CI, then it completes without errors.
- Given the notebook output, when inspected, then it shows: package contents listing, integrity check results, reproduction comparison (matching results), and the researcher sharing workflow (Marco's journey from UX spec).

### Scope Notes

- **Cross-machine reproducibility** — this epic validates TD-17 from Phase 1 retro.
- **Package format** — directory structure with a manifest index, optionally compressed as archive.
- **Marco's journey** — this is the key deliverable for the researcher persona (share YAML + notebook + manifest, co-author reproduces).

---

## Epic 17: GUI Showcase Product

_User outcome: Non-coding analyst can operate the complete Phase 2 workflow through a web GUI: build populations from real data, design policy portfolios, run simulations, browse persistent results, and compare across portfolios._

_Status: backlog_

_Builds on: All Phase 2 epics (EPIC-11 through EPIC-16), EPIC-6 (Phase 1 GUI prototype and FastAPI backend)_

_PRD Refs: FR32, FR37, FR39, FR43, FR45_

### Story 17.1: Build Data Fusion Workbench GUI

**Status:** backlog
**Priority:** P0
**Estimate:** 8 SP
**Type:** Story
**PRD Refs:** FR37, FR39
**Original ID:** BKL-1701

### Story 17.2: Build Policy Portfolio Designer GUI

**Status:** backlog
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR43
**Original ID:** BKL-1702

### Story 17.3: Build Simulation Runner with progress and persistent results

**Status:** backlog
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR32, FR45
**Original ID:** BKL-1703

### Story 17.4: Build Comparison Dashboard with multi-portfolio side-by-side

**Status:** backlog
**Priority:** P0
**Estimate:** 8 SP
**Type:** Story
**PRD Refs:** FR32, FR45
**Original ID:** BKL-1704

### Story 17.5: Build Behavioral Decision Viewer

**Status:** backlog
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR45
**Original ID:** BKL-1705

### Story 17.6: Implement FastAPI endpoints for Phase 2 GUI operations

**Status:** backlog
**Priority:** P0
**Estimate:** 5 SP
**Type:** Task
**PRD Refs:** FR32
**Original ID:** BKL-1706

### Story 17.7: Implement persistent result storage and retrieval

**Status:** backlog
**Priority:** P0
**Estimate:** 3 SP
**Type:** Task
**PRD Refs:** FR45
**Original ID:** BKL-1707

### Story 17.8: Build end-to-end GUI workflow tests

**Status:** backlog
**Priority:** P0
**Estimate:** 5 SP
**Type:** Story
**PRD Refs:** FR32
**Original ID:** BKL-1708

### Epic-Level Acceptance Criteria

- Analyst can build a population from real data sources through the GUI without writing code.
- Analyst can choose merge methods with plain-language explanations in the GUI.
- Analyst can compose and run a policy portfolio through the GUI.
- Completed simulation results persist across browser sessions — no need to re-run.
- Analyst can compare multiple portfolio results side-by-side.
- GUI displays behavioral decision outcomes (discrete choice results) per household group.
- All GUI operations map to API endpoints tested independently.
- Frontend tests cover core workflows (data fusion, portfolio creation, simulation, comparison).

### Story-Level Acceptance Criteria

**BKL-1701: Build Data Fusion Workbench GUI**

- Given the Data Fusion Workbench screen, when the analyst opens it, then available data sources are listed with metadata (name, description, variables, record count, source URL).
- Given the source browser, when the analyst selects two or more data sources, then the GUI shows overlapping and unique variables and prompts merge method selection.
- Given merge method selection, when the analyst chooses a method (e.g., statistical matching, calibration weighting), then a plain-language explanation of the method's assumptions and trade-offs is displayed.
- Given a configured merge, when the analyst clicks "Generate Population", then the population generation pipeline runs and the GUI shows progress.
- Given a generated population, when previewed, then the GUI displays summary statistics (record count, variable distributions, key demographics) and validation results against known marginals.
- Given the workbench, when the analyst adjusts merge parameters and regenerates, then the new population reflects the changed configuration.

**BKL-1702: Build Policy Portfolio Designer GUI**

- Given the Portfolio Designer screen, when the analyst opens it, then available policy templates are listed with descriptions, configurable parameters, and category tags.
- Given the template browser, when the analyst selects templates, then they are added to a portfolio composition panel where parameters can be configured per template.
- Given a portfolio with multiple templates, when the analyst reorders or removes templates, then the portfolio updates accordingly.
- Given template parameters, when the analyst configures year-indexed schedules (e.g., carbon tax trajectory), then a visual timeline editor allows setting values per year.
- Given a complete portfolio configuration, when saved, then the portfolio is persisted as a named configuration that can be loaded, cloned, or edited later.

**BKL-1703: Build Simulation Runner with progress and persistent results**

- Given a configured population and policy portfolio, when the analyst clicks "Run Simulation", then the simulation starts and a progress indicator shows current year, estimated remaining time, and completion percentage.
- Given a running simulation, when it completes, then results are automatically saved to persistent storage with a unique run ID, timestamp, and configuration summary.
- Given persistent results, when the analyst returns to the application (even after closing the browser), then all previously completed runs are listed and browsable.
- Given a completed run in the results list, when the analyst clicks it, then the full result detail view opens with indicators, panel data summary, and run manifest.

**BKL-1704: Build Comparison Dashboard with multi-portfolio side-by-side**

- Given two or more completed simulation runs, when the analyst selects them for comparison, then a side-by-side dashboard displays key indicators (distributional, welfare, fiscal, environmental) for each run.
- Given the comparison view, when the analyst inspects distributional indicators, then charts show impact by income decile for each portfolio with clear visual differentiation.
- Given the comparison view, when the analyst hovers over or selects a specific indicator, then a detail panel shows the breakdown and methodology.
- Given the comparison dashboard, when the analyst toggles between absolute and relative views, then the charts and tables update to show the selected representation.
- Given the comparison dashboard, when populated with runs that include behavioral responses (discrete choice), then indicators reflect post-behavioral-response outcomes (not just static impacts).

**BKL-1705: Build Behavioral Decision Viewer**

- Given a completed run with discrete choice results, when the analyst opens the Behavioral Decision Viewer, then aggregate decision outcomes are displayed per domain (vehicle fleet composition, heating system mix over time).
- Given the decision viewer, when the analyst selects a decision domain (e.g., vehicle), then year-by-year transition charts show the evolution of the fleet (e.g., EV adoption curve, diesel phase-out).
- Given the decision viewer, when the analyst filters by household group (e.g., income decile, location), then the decision outcomes update to show group-specific transition patterns.
- Given the decision viewer, when the analyst clicks on a specific year, then a detail panel shows choice probabilities and the distribution of chosen alternatives for that year.

**BKL-1706: Implement FastAPI endpoints for Phase 2 GUI operations**

- Given the Phase 2 backend capabilities, when the GUI needs them, then FastAPI endpoints exist for: population generation (start, status, result), portfolio CRUD (create, read, update, delete, list), simulation execution (start, progress, result), result listing and retrieval, and comparison queries.
- Given each API endpoint, when called with valid parameters, then it returns correctly typed JSON responses matching documented schemas.
- Given each API endpoint, when called with invalid parameters, then it returns appropriate error codes (400, 404, 422) with descriptive error messages.
- Given API endpoints, when tested independently (without the GUI), then all endpoints pass integration tests.

**BKL-1707: Implement persistent result storage and retrieval**

- Given a completed simulation, when results are stored, then all outputs (indicators, panel summary, manifest, configuration) are persisted to disk in a structured directory per run.
- Given stored results, when listed via API, then the response includes: run ID, timestamp, population summary, portfolio name, and status.
- Given a stored result, when retrieved by run ID, then all artifacts are returned (indicators, panel data, manifest, configuration used).
- Given stored results, when the application restarts, then all previously stored results remain accessible.

**BKL-1708: Build end-to-end GUI workflow tests**

- Given the frontend test suite, when run, then it covers the core analyst workflow: open Data Fusion Workbench → configure and generate population → open Portfolio Designer → compose portfolio → run simulation → view results → compare two runs.
- Given the test suite, when run in CI, then all tests pass.
- Given the test suite, when a GUI component changes, then relevant tests fail and identify the broken workflow step.
- Given the test suite, when inspected, then it covers: data fusion (source selection, merge method, generation), portfolio design (template selection, parameter configuration, save), simulation (run, progress, completion), results (persistence, retrieval, browsing), and comparison (multi-run selection, side-by-side display).

### Scope Notes

- **Built last, shown first** — the GUI integrates all backend capabilities from EPIC-11 through EPIC-16.
- **Notebook demos from prior epics** directly inform GUI screen design — each notebook workflow maps to a GUI screen.
- **Tech stack:** React + TypeScript + Shadcn/ui + Tailwind v4 (same as Phase 1 prototype).
- **Key new GUI sections:**
  - **Data Fusion Workbench** — browse datasets, select sources, choose merge methods, preview population, validate against marginals
  - **Policy Portfolio Designer** — browse templates, compose portfolios, configure parameters per policy
  - **Simulation Runner** — run with configured population + portfolio, show progress
  - **Persistent Results** — completed simulations stored and browsable
  - **Comparison Dashboard** — side-by-side across portfolios with distributional/welfare/fiscal indicators
  - **Behavioral Decision Viewer** — explore household decisions from discrete choice model

---

## Epic 18: UX Polish & Aesthetic Overhaul

**User outcome:** Non-coding analyst experiences a polished, cohesive product with persistent navigation, visual warmth, shared components, and clear information hierarchy — instead of separate screens stitched together.

**Status:** backlog

**Builds on:** EPIC-17 (GUI Showcase), EPIC-6 (Phase 1 GUI prototype)

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-1801 | Story | P0 | 5 | Implement workflow navigation rail | backlog | — |
| BKL-1802 | Story | P0 | 3 | Visual polish pass (rounded corners, shadows, header, login) | backlog | — |
| BKL-1803 | Story | P0 | 3 | Extract shared components (WorkbenchStepper, ErrorAlert, SelectionGrid) | backlog | — |
| BKL-1804 | Story | P0 | 5 | Restructure results view with tabs and hierarchy | backlog | — |
| BKL-1805 | Story | P1 | 5 | Consolidate configuration flow and split dense screens | backlog | — |
| BKL-1806 | Story | P1 | 3 | Standardize form inputs and add loading skeletons | backlog | — |
| BKL-1807 | Story | P1 | 5 | Repurpose right panel as contextual help | backlog | — |
| BKL-1808 | Story | P1 | 3 | Chart polish and color palette refinement | backlog | — |

### Epic-Level Acceptance Criteria

- All 9 screens use shared components (no duplicated WorkbenchStepper, no inline error displays).
- Persistent navigation rail visible in all view modes.
- All containers have rounded corners and appropriate elevation.
- Results view has clear information hierarchy with tabs.
- All form inputs use shadcn Input component (no raw `<input>` elements).
- Visual regression: no broken layouts at 1280px+ viewport.

---

### Story 18.1: Implement workflow navigation rail

**Status:** backlog
**Priority:** P0
**Estimate:** 5

#### Acceptance Criteria

- Given the left panel, when the workspace loads, then the four navigation buttons are replaced by a vertical stepper showing workflow stages with numbered step indicators and connecting lines.
- Given a workflow stage, when the user has completed meaningful work in that stage, then the step indicator shows a checkmark icon instead of the stage number.
- Given each workflow stage in the nav rail, when there is relevant state, then a one-line summary is displayed below the stage label in muted text.
- Given the nav rail, when the analyst clicks any stage, then the main panel switches to that stage's view mode.
- Given the left panel, when scenarios exist, then ScenarioCards still appear below the navigation rail, separated by a visual divider.
- Given the left panel in collapsed state, when viewed, then the nav rail shows only the step indicator icons in a vertical column.

---

### Story 18.2: Visual polish pass (rounded corners, shadows, header, login)

**Status:** backlog
**Priority:** P0
**Estimate:** 3

#### Acceptance Criteria

- Given all Card, section, and panel containers across all 9 screens, when rendered, then they use rounded corners.
- Given primary content containers, when rendered, then they use subtle shadows for depth.
- Given the main workspace header, when rendered, then it displays a gradient background with branding.
- Given the PasswordPrompt screen, when rendered, then the login card uses rounded corners, shadow, and brand mark.
- Given all existing screens, when rendered at 1280px+ viewport, then no layouts are broken.

---

### Story 18.3: Extract shared components (WorkbenchStepper, ErrorAlert, SelectionGrid)

**Status:** backlog
**Priority:** P0
**Estimate:** 3

#### Acceptance Criteria

- Given WorkbenchStepper variants across screens, when refactored, then a single shared component is used everywhere.
- Given inline error displays, when refactored, then a shared ErrorAlert component is used.
- Given selection grid patterns, when refactored, then a shared SelectionGrid component is used.
- Given the refactored components, when all screens render, then no visual regressions occur.

---

### Story 18.4: Restructure results view with tabs and hierarchy

**Status:** backlog
**Priority:** P0
**Estimate:** 5

#### Acceptance Criteria

- Given the results view, when a completed run is selected, then results are organized with tabs for different indicator categories.
- Given the results view, when browsing indicators, then information hierarchy distinguishes primary metrics from details.
- Given the results view, when switching between tabs, then content loads without full re-render.

---

### Story 18.5: Consolidate configuration flow and split dense screens

**Status:** backlog
**Priority:** P1
**Estimate:** 5

**Dependencies:** Story 18.3

#### Acceptance Criteria

- Given dense configuration screens, when viewed, then content is split into logical sections or steps.
- Given the configuration flow, when navigating between sections, then state is preserved.

---

### Story 18.6: Standardize form inputs and add loading skeletons

**Status:** backlog
**Priority:** P1
**Estimate:** 3

**Dependencies:** Story 18.3

#### Acceptance Criteria

- Given all form inputs, when rendered, then they use the shadcn Input component (no raw `<input>` elements).
- Given loading states, when data is being fetched, then skeleton placeholders are shown instead of blank areas.

---

### Story 18.7: Repurpose right panel as contextual help

**Status:** backlog
**Priority:** P1
**Estimate:** 5

**Dependencies:** Story 18.3

#### Acceptance Criteria

- Given the right panel, when a workflow stage is active, then contextual help relevant to that stage is displayed.
- Given the right panel, when the user dismisses it, then it collapses and persists its state.

---

### Story 18.8: Chart polish and color palette refinement

**Status:** backlog
**Priority:** P1
**Estimate:** 3

**Dependencies:** Story 18.3

#### Acceptance Criteria

- Given all chart components, when rendered, then they use a refined, consistent color palette.
- Given chart containers, when rendered within rounded parents, then they display correctly without clipping.
