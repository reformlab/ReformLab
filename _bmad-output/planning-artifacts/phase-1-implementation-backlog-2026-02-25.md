---
title: Phase 1 Implementation Backlog
project: Microsimulation
date: 2026-02-25
source_documents:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
status: draft
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
7. `EPIC-7`: Quality Gates, Benchmarks, and Pilot Readiness

## Prioritized Backlog

### EPIC-1 Computation Adapter and Data Layer

| ID | Type | Pri | SP | Title | Depends On | PRD Refs |
|---|---|---|---:|---|---|---|
| BKL-101 | Story | P0 | 5 | Define ComputationAdapter interface and OpenFiscaAdapter implementation | - | FR1, FR2, FR3 |
| BKL-102 | Story | P0 | 5 | Implement CSV/Parquet ingestion for OpenFisca outputs and population data | BKL-101 | FR1, FR3, NFR14 |
| BKL-103 | Story | P0 | 5 | Build input/output mapping configuration for OpenFisca variable names | BKL-101 | FR3, FR4, NFR4 |
| BKL-104 | Story | P0 | 5 | Implement open-data ingestion pipeline (synthetic population, emission factors) | BKL-102 | FR5, FR6 |
| BKL-105 | Task | P0 | 3 | Add data-quality checks with blocking field-level errors at adapter boundary | BKL-103 | FR4, FR27, NFR4 |
| BKL-106 | Story | P1 | 5 | Add direct OpenFisca API orchestration mode (version-pinned) | BKL-101 | FR2, NFR15 |
| BKL-107 | Task | P0 | 2 | Create compatibility matrix for supported OpenFisca versions | BKL-101 | NFR15, NFR21 |

Acceptance criteria:

- ComputationAdapter interface is defined with compute() and version() methods.
- OpenFiscaAdapter passes contract tests for CSV/Parquet input and output mapping.
- Adapter can be mocked for orchestrator unit testing.
- Open-data pipeline loads synthetic population and emission factor datasets.
- Mapping errors return exact field names and actionable messages.
- Unsupported OpenFisca version fails with explicit compatibility error.
- Adapter test fixtures run in CI.

### EPIC-2 Scenario Templates and Registry

| ID | Type | Pri | SP | Title | Depends On | PRD Refs |
|---|---|---|---:|---|---|---|
| BKL-201 | Story | P0 | 5 | Define scenario template schema (baseline + reform overrides) | BKL-103 | FR7, FR8, FR12 |
| BKL-202 | Story | P0 | 8 | Implement carbon-tax template pack (4-5 variants) | BKL-201 | FR7, FR10, FR11 |
| BKL-203 | Story | P0 | 5 | Implement subsidy/rebate/feebate template pack | BKL-201 | FR7, FR11 |
| BKL-204 | Story | P0 | 5 | Build scenario registry with immutable version IDs | BKL-201 | FR9, FR28 |
| BKL-205 | Story | P0 | 3 | Implement scenario cloning and baseline/reform linking | BKL-204 | FR8, FR9 |
| BKL-206 | Task | P1 | 3 | Add schema migration helper for template version changes | BKL-204 | FR9, NFR21 |

Acceptance criteria:

- Analysts can create baseline/reform scenarios from templates without code changes.
- Registry stores versioned scenario snapshots.
- Scenario validation enforces year-indexed schedules (>= 10 years configurable).

### EPIC-3 Step-Pluggable Dynamic Orchestrator and Vintage Tracking

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

### EPIC-4 Indicators and Scenario Comparison

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

### EPIC-5 Governance and Reproducibility

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

### EPIC-6 Interfaces (Python API, Notebooks, Early No-Code GUI)

| ID | Type | Pri | SP | Title | Depends On | PRD Refs |
|---|---|---|---:|---|---|---|
| BKL-601 | Story | P0 | 5 | Implement stable Python API for run orchestration | BKL-301, BKL-405, BKL-501 | FR30, NFR16 |
| BKL-602 | Story | P0 | 5 | Build quickstart notebook (OpenFisca + environmental templates) | BKL-601 | FR34, NFR19 |
| BKL-603 | Story | P0 | 5 | Build advanced notebook (multi-year + vintage + comparison) | BKL-601 | FR30, FR35 |
| BKL-604 | Story | P0 | 8 | Implement early no-code GUI: create/clone/run/compare scenarios | BKL-205, BKL-405 | FR32 |
| BKL-605 | Task | P0 | 3 | Add export actions in API/GUI for CSV/Parquet outputs | BKL-405, BKL-604 | FR33 |
| BKL-606 | Task | P1 | 3 | Improve operational error UX (mapping and run-state failures) | BKL-604 | FR4, FR27 |

Acceptance criteria:

- API supports full run lifecycle from data ingest to comparison outputs.
- New user can complete quickstart workflow in under 30 minutes.
- GUI supports baseline/reform scenario operations without code.

### EPIC-7 Quality Gates, Benchmarks, and Pilot Readiness

| ID | Type | Pri | SP | Title | Depends On | PRD Refs |
|---|---|---|---:|---|---|---|
| BKL-701 | Story | P0 | 5 | Build performance benchmark suite (100k households) | BKL-301, BKL-401 | NFR1, NFR5 |
| BKL-702 | Task | P0 | 3 | Add memory-limit guardrails and warning checks | BKL-701 | NFR3 |
| BKL-703 | Task | P0 | 3 | Enforce CI quality gates (lint, tests, coverage thresholds) | BKL-101 | NFR18, NFR20 |
| BKL-704 | Story | P0 | 5 | Build external pilot package (example datasets, templates, docs) | BKL-602, BKL-603, BKL-501 | FR35, NFR19 |
| BKL-705 | Task | P0 | 3 | Define Phase 1 exit checklist and pilot sign-off form | BKL-704 | PRD go/no-go criteria |

Acceptance criteria:

- Benchmark suite reports pass/fail against Phase 1 NFR targets.
- CI blocks merges on failing tests or coverage gates.
- Pilot package is runnable by at least one external user.

## Suggested Phase 1 Delivery Plan (6 Sprints)

1. Sprint 1: BKL-101 to BKL-105, BKL-201, BKL-703.
2. Sprint 2: BKL-202 to BKL-205, BKL-301, BKL-302.
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
