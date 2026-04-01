---
title: Implementation Readiness Assessment Report
date: 2026-04-01
project: reformlab
stepsCompleted:
  - step-01-document-discovery
  - step-02-prd-analysis
  - step-03-epic-coverage-validation
  - step-04-ux-alignment
  - step-05-epic-quality-review
  - step-06-final-assessment
documentsUsed:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-01.md
  - _bmad-output/planning-artifacts/epics.md
notes:
  - Empty planning-artifacts/epics/ folder treated as non-authoritative; epics.md used as source of truth for readiness assessment.
  - Architecture diagrams file was discovered but not selected as a primary source because the user specified architecture.md explicitly.
---

# Implementation Readiness Assessment Report

**Date:** 2026-04-01
**Project:** reformlab

## Document Discovery

### Selected Documents

- [prd.md](/Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/prd.md)
- [architecture.md](/Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/architecture.md)
- [ux-design-specification.md](/Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/ux-design-specification.md)
- [sprint-change-proposal-2026-04-01.md](/Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/sprint-change-proposal-2026-04-01.md)
- [epics.md](/Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/epics.md)

### Discovery Notes

- `epics.md` was selected as the authoritative epic source.
- The empty `planning-artifacts/epics/` folder was ignored as a non-authoritative duplicate-format artifact.

## PRD Analysis

### Functional Requirements

FR1: Analyst can ingest OpenFisca household-level outputs from CSV or Parquet.
FR2: System can optionally execute OpenFisca runs through a version-pinned API adapter.
FR3: Analyst can map OpenFisca variables to project schema fields through configuration.
FR4: System validates mapping/schema contracts with clear field-level errors.
FR5: Analyst can load synthetic populations and external environmental datasets (for example, energy consumption or emissions factors).
FR6: System records data source metadata and hashes for every run.
FR7: Analyst can load prebuilt environmental policy templates (carbon tax, subsidy, rebate, feebate).
FR8: Analyst can define reforms as parameter overrides to a baseline scenario.
FR9: System stores versioned scenario definitions in a scenario registry.
FR10: Analyst can run multiple scenarios in one batch for comparison.
FR11: Analyst can compose tax-benefit baseline outputs with environmental template logic in one workflow.
FR12: Scenario configuration supports year-indexed policy schedules for at least ten years.
FR13: System can execute iterative yearly simulations for 10+ years.
FR14: System can carry forward state variables between yearly iterations.
FR15: System can track asset/cohort vintages (for example, vehicle/heating cohorts) by year.
FR16: Analyst can configure transition rules for state updates between years.
FR17: System enforces deterministic sequencing and explicit random-seed control in dynamic runs.
FR18: System outputs year-by-year panel results for each scenario.
FR19: Analyst can compute distributional indicators by income decile.
FR20: Analyst can compute indicators by geography (region and related groupings).
FR21: Analyst can compute welfare indicators including winners/losers counts and net gains/losses.
FR22: Analyst can compute fiscal indicators (revenues, costs, balances) per year and cumulatively.
FR23: Analyst can define custom indicators as derived formulas over run outputs.
FR24: Analyst can compare indicators across scenarios side-by-side.
FR25: System automatically generates immutable run manifests including versions, hashes, parameters, and assumptions.
FR26: Analyst can inspect assumptions and mappings used in any run.
FR27: System emits warnings for unvalidated templates, mappings, or unsupported run configurations.
FR28: Results are pinned to scenario version, data version, and OpenFisca adapter/version.
FR29: System maintains run lineage across yearly iterations and scenario variants.
FR30: User can run full workflows from a Python API in notebooks.
FR31: User can configure workflows with YAML/JSON files for analyst-friendly version control.
FR32: User can use a stage-based no-code GUI to create, inspect, clone, and run scenarios.
FR33: User can export tables and indicators in CSV/Parquet for downstream reporting.
FR34: User can run an OpenFisca-plus-environment quickstart in under 30 minutes.
FR35: User can access template authoring and dynamic-run documentation with reproducible examples.
FR36: Analyst can download and cache public datasets from institutional sources (INSEE, Eurostat, ADEME, SDES).
FR37: Analyst can browse available datasets and select which to include in a population.
FR38: System provides a library of statistical methods for merging datasets that do not share the same sample (uniform distribution, IPF, conditional sampling, statistical matching).
FR39: Analyst can choose which merge method to apply at each dataset join, with plain-language explanation of the assumption.
FR40: System produces a complete synthetic population with household-level attributes sufficient for policy simulation (income, household composition, housing, vehicle, heating, energy, geography).
FR41: Every merge, imputation, and extrapolation is recorded as an explicit assumption in the governance layer.
FR42: System validates generated populations against known marginal distributions from source data.
FR43: Analyst can compose multiple individual policy templates into a named policy portfolio.
FR44: System executes a simulation with a policy portfolio, applying all bundled policies together.
FR45: Analyst can compare results across different policy portfolios side-by-side.
FR46: Analyst can define custom policy templates that participate in portfolios alongside built-in templates.
FR47: System models household investment decisions (vehicle, heating, renovation) as discrete choice problems using logit functions.
FR48: System expands population by alternatives and evaluates each alternative through OpenFisca for household-specific cost calculations.
FR49: Logit draws use seed-controlled randomness for reproducibility.
FR50: Panel output records which decision each household made in each domain for each year.
FR51: Taste parameters (beta coefficients) are recorded in run manifests.
FR52: Analyst can calibrate discrete choice taste parameters against observed transition rates.
FR53: System validates calibrated parameters against known marginal distributions.
FR54: Analyst can export a self-contained replication package including data, configuration, manifests, and results.
FR55: Replication package is reproducible on a clean environment with only `pip install reformlab` and the package contents.

Total FRs: 55

### Non-Functional Requirements

NFR1: Full population simulation (100,000 households) completes in under 10 seconds on a standard laptop (4-core, 16GB RAM).
NFR2: All orchestration hot paths use vectorized array computation where feasible; no row-by-row loops in core aggregation/calculation paths.
NFR3: Framework handles populations up to 500,000 households on 16GB RAM without crashing; larger populations produce a clear memory warning before attempting execution.
NFR4: YAML configuration loading and validation completes in under 1 second for typical policy definitions.
NFR5: Analytical operations (distributional analysis, welfare computation, fiscal cost) execute in under 5 seconds for 100,000 households.
NFR6: Identical inputs produce bit-identical outputs across runs on the same machine.
NFR7: Identical inputs produce identical outputs across different machines and operating systems (Python version and dependency versions held constant).
NFR8: Random seeds used in synthetic population generation are explicit, pinned, and recorded in the run manifest.
NFR9: Run manifests are generated automatically with zero manual effort from the user.
NFR10: No implicit temporal assumptions; all period semantics are explicit in configuration.
NFR11: When users supply restricted microdata, the framework never persists, copies, or transmits data beyond the user's local environment.
NFR12: Input data paths are referenced in run manifests, not embedded; no raw data in manifests or logs.
NFR13: No telemetry, analytics, or network calls from the framework; fully offline operation.
NFR14: CSV and Parquet files are supported for all data input and output operations.
NFR15: OpenFisca integration supports both import contracts (CSV/Parquet) and version-pinned API orchestration modes.
NFR16: All Python API objects have sensible `__repr__` for Jupyter notebook display.
NFR17: Framework has zero dependency on cloud providers, data vendors, or institutional infrastructure.
NFR18: pytest test suite with high coverage on adapters, orchestration, template logic, and simulation runner.
NFR19: All shipped examples run end-to-end without modification on a fresh install (tested in CI).
NFR20: YAML examples are tested in CI to prevent documentation drift.
NFR21: Semantic versioning; breaking changes only on major versions.

Total NFRs: 21

### Additional Requirements

- OpenFisca-first strategy supersedes any earlier suggestion of building a replacement core simulation engine.
- ReformLab remains an orchestration and product layer over a computation backend exposed through a `ComputationAdapter` boundary.
- Open-data-first remains a standing product assumption; restricted microdata is optional and local-only.
- The canonical workflow artifact model in the PRD is `portfolio -> scenario -> run`, with scenario carrying selected population(s), engine configuration, mappings, and metadata.
- Jupyter and YAML remain first-class interfaces even as the GUI grows.
- Endogenous market-clearing, physical system feedback loops, and full behavioral equilibrium modeling remain out of MVP scope.

### PRD Completeness Assessment

- The PRD provides a strong numbered requirement baseline and explicit workflow artifact model.
- The PRD predates the April 1 runtime/data-path decisions, so EPIC-23 and EPIC-24 readiness depends on newer documents to resolve runtime-default behavior, executable population semantics, and domain-to-OpenFisca policy translation boundaries.
- The most likely readiness risks are not missing core product intent, but contract ambiguity between legacy import/replay assumptions and the new live-runtime path.

## Epic Coverage Validation

### Coverage Matrix

| FR Number | PRD Requirement | Epic Coverage | Status |
| --------- | --------------- | ------------- | ------ |
| FR1 | Ingest OpenFisca household-level outputs from CSV/Parquet | EPIC-1, EPIC-7, EPIC-8, EPIC-21 | Covered |
| FR2 | Optional version-pinned OpenFisca API execution | EPIC-1, EPIC-3, EPIC-21, EPIC-23 | Covered |
| FR3 | Configurable mapping from OpenFisca variables to project schema | EPIC-1, EPIC-7, EPIC-8, EPIC-20, EPIC-23 | Covered |
| FR4 | Validate mapping/schema contracts with field-level errors | EPIC-1, EPIC-2, EPIC-6, EPIC-10, EPIC-20, EPIC-23 | Covered |
| FR5 | Load synthetic populations and external environmental datasets | EPIC-1, EPIC-7, EPIC-21, EPIC-23 | Covered |
| FR6 | Record data source metadata and hashes for every run | EPIC-1, EPIC-5, EPIC-21 | Covered |
| FR7 | Load prebuilt environmental policy templates | EPIC-2, EPIC-5, EPIC-10, EPIC-21, EPIC-24 | Covered |
| FR8 | Define reforms as parameter overrides to a baseline scenario | EPIC-2, EPIC-3, EPIC-21 | Covered |
| FR9 | Store versioned scenario definitions in a scenario registry | EPIC-2, EPIC-5 | Covered |
| FR10 | Run multiple scenarios in one batch for comparison | EPIC-2, EPIC-3, EPIC-21 | Covered |
| FR11 | Compose tax-benefit baseline outputs with environmental logic | EPIC-2, EPIC-21, EPIC-23 | Covered |
| FR12 | Support year-indexed policy schedules for at least ten years | EPIC-2, EPIC-5, EPIC-21 | Covered |
| FR13 | Execute iterative yearly simulations for 10+ years | EPIC-3 | Covered |
| FR14 | Carry forward state variables between yearly iterations | EPIC-1, EPIC-3 | Covered |
| FR15 | Track asset/cohort vintages by year | EPIC-1, EPIC-3, EPIC-21 | Covered |
| FR16 | Configure transition rules for state updates | EPIC-3, EPIC-6, EPIC-21 | Covered |
| FR17 | Deterministic sequencing and explicit random-seed control | EPIC-3, EPIC-21 | Covered |
| FR18 | Output year-by-year panel results | EPIC-1, EPIC-3, EPIC-7, EPIC-21, EPIC-23 | Covered |
| FR19 | Compute distributional indicators by income decile | EPIC-1, EPIC-4, EPIC-6, EPIC-7 | Covered |
| FR20 | Compute indicators by geography | EPIC-2, EPIC-4, EPIC-7 | Covered |
| FR21 | Compute welfare indicators | EPIC-1, EPIC-2, EPIC-4 | Covered |
| FR22 | Compute fiscal indicators per year and cumulatively | EPIC-4, EPIC-21 | Covered |
| FR23 | Define custom indicators as derived formulas | EPIC-4, EPIC-21 | Covered |
| FR24 | Compare indicators across scenarios side-by-side | EPIC-4, EPIC-21 | Covered |
| FR25 | Generate immutable run manifests automatically | EPIC-5, EPIC-20, EPIC-22, EPIC-23 | Covered |
| FR26 | Inspect assumptions and mappings used in any run | EPIC-5, EPIC-20, EPIC-22, EPIC-23 | Covered |
| FR27 | Warn on unvalidated templates, mappings, or unsupported configs | EPIC-1, EPIC-5, EPIC-6, EPIC-20, EPIC-22, EPIC-23 | Covered |
| FR28 | Pin results to scenario, data, and adapter/version | EPIC-2, EPIC-20, EPIC-22, EPIC-23 | Covered |
| FR29 | Maintain run lineage across iterations and variants | EPIC-5, EPIC-20, EPIC-22 | Covered |
| FR30 | Run full workflows from Python API in notebooks | EPIC-6 | Covered |
| FR31 | Configure workflows with YAML/JSON files | EPIC-2 | Covered |
| FR32 | Use a stage-based no-code GUI to create, inspect, clone, and run scenarios | EPIC-6, EPIC-17, EPIC-20, EPIC-22, EPIC-23 | Covered |
| FR33 | Export tables and indicators in CSV/Parquet | EPIC-3, EPIC-4, EPIC-6 | Covered |
| FR34 | Run quickstart in under 30 minutes | EPIC-6, EPIC-20, EPIC-22 | Covered |
| FR35 | Access authoring and dynamic-run documentation with reproducible examples | EPIC-6, EPIC-7, EPIC-20 | Covered |
| FR36 | Download and cache public datasets | EPIC-11 | Covered |
| FR37 | Browse available datasets and select inputs for a population | EPIC-11, EPIC-17, EPIC-20, EPIC-22 | Covered |
| FR38 | Provide statistical methods for dataset merging | EPIC-11, EPIC-20, EPIC-22 | Covered |
| FR39 | Let analyst choose merge method with plain-language explanation | EPIC-11, EPIC-17, EPIC-20, EPIC-22 | Covered |
| FR40 | Produce a complete synthetic population for simulation | EPIC-11, EPIC-20, EPIC-22 | Covered |
| FR41 | Record every merge/imputation/extrapolation assumption | EPIC-11, EPIC-20, EPIC-22 | Covered |
| FR42 | Validate generated populations against source marginals | EPIC-11, EPIC-20, EPIC-22 | Covered |
| FR43 | Compose multiple templates into a named portfolio | EPIC-12, EPIC-17, EPIC-20, EPIC-22, EPIC-24 | Covered |
| FR44 | Execute a simulation with a policy portfolio | EPIC-12, EPIC-20, EPIC-22, EPIC-24 | Covered |
| FR45 | Compare results across policy portfolios | EPIC-12, EPIC-17, EPIC-20, EPIC-22, EPIC-24 | Covered |
| FR46 | Define custom templates that participate in portfolios | EPIC-12, EPIC-13, EPIC-24 | Covered |
| FR47 | Model household investment decisions as discrete choice problems | EPIC-14, EPIC-20, EPIC-22 | Covered |
| FR48 | Expand population by alternatives and evaluate through OpenFisca | EPIC-14, EPIC-20, EPIC-22 | Covered |
| FR49 | Use seed-controlled randomness for logit draws | EPIC-14, EPIC-20, EPIC-22 | Covered |
| FR50 | Record household decisions by domain/year in panel output | EPIC-14, EPIC-20, EPIC-22 | Covered |
| FR51 | Record taste parameters in run manifests | EPIC-14, EPIC-20, EPIC-22 | Covered |
| FR52 | Calibrate taste parameters against observed transition rates | EPIC-15, EPIC-20, EPIC-22 | Covered |
| FR53 | Validate calibrated parameters against known marginals | EPIC-15, EPIC-20, EPIC-22 | Covered |
| FR54 | Export a self-contained replication package | EPIC-16 | Covered |
| FR55 | Reproduce exported package on a clean environment | EPIC-16 | Covered |

### Missing Requirements

- No PRD FRs are uncovered in the current epic corpus.
- EPIC-23 and EPIC-24 add runtime-specific FRs (`FR-RUNTIME-1` through `FR-RUNTIME-7`) and GUI refinements (`FR32a`, `FR32c`) that extend the baseline PRD rather than filling missing legacy FR coverage.

### Coverage Statistics

- Total PRD FRs: 55
- FRs covered in epics: 55
- Coverage percentage: 100%

### Coverage Notes Relevant to EPIC-23 and EPIC-24

- EPIC-23 is an execution-contract and runtime-default realignment on top of already-covered foundations in EPIC-1, EPIC-9, EPIC-17, EPIC-20, and EPIC-22.
- EPIC-24 is a catalog/translation activation slice on top of already-covered portfolio and template foundations in EPIC-12 and EPIC-13.
- The principal readiness risk is not missing headline FR coverage; it is whether the new stories define sufficiently concrete contracts to avoid duplicating existing adapter, catalog, portfolio, and workspace responsibilities.

## UX Alignment Assessment

### UX Document Status

- UX document found: [ux-design-specification.md](/Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/ux-design-specification.md)
- Architecture document found: [architecture.md](/Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/architecture.md)
- April 1 change proposal found: [sprint-change-proposal-2026-04-01.md](/Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/sprint-change-proposal-2026-04-01.md)

### Alignment Issues

- **EPIC-23 vs UX spec:** The current UX spec still makes Stage 3 own primary population selection and investment decisions, and still models an `Engine`/execution-control surface with `Fast preview / Full run`. This conflicts with the April 1 proposal, which moves investment decisions to their own stage and requires Scenario to show inherited primary population context rather than reselection.
- **EPIC-23 vs architecture:** The architecture document still describes a four-stage frontend shell with `Engine` as Stage 3. It does not yet reflect the April 1 five-stage correction or the clarified ownership split where Population owns primary selection and Scenario consumes inherited context.
- **EPIC-23 runtime clarity gap:** The UX spec does not currently document live OpenFisca as the default web runtime, explicit replay-only flows, or the requirement to avoid a frontend engine selector. The architecture document also lacks a runtime-mode contract description, replay-path separation, and manifest/result metadata expectations for runtime provenance.
- **EPIC-24 catalog alignment is partially positive:** UX Revision 4 Stage 1 supports an API-driven template catalog, category metadata, and frontend behavior that does not hardcode categories. This aligns with exposing additional supported policy packs through catalog/API. However, the UX spec does not yet distinguish live-capable versus unavailable surfaced packs or document readiness caveats for newly exposed items.
- **Terminology drift remains:** UX Revision 4 uses user-facing `Policies` and `Policy Set`, while architecture still uses `Policies & Portfolio` and `Portfolio` in the frontend stage table. Internal portfolio semantics remain valid, but the documents are not synchronized.

### Warnings

- The UX and architecture artifacts are not yet fully updated to the April 1 stage-ownership corrections, so EPIC-23 story implementation would otherwise rely on the epic text and change proposal as de facto source of truth.
- EPIC-23 should not be treated as fully implementation-ready from UX/architecture alone until runtime-mode behavior, replay boundaries, inherited-population display, and no-selector constraints are written into the canonical UX and architecture docs.
- EPIC-24 is closer to UX readiness because Stage 1 already assumes API-driven catalog metadata, but it still lacks explicit UX treatment for pack availability states and surfaced-but-not-executable cases.

## Epic Quality Review

### Structural Assessment

- **Epic 23 user value:** Valid. The epic is framed as a user outcome: web runs execute against the actual selected population through live OpenFisca by default while preserving existing results behavior.
- **Epic 24 user value:** Valid. The epic is framed as a user outcome: analysts can discover and execute already-modeled subsidy and related packs through the product catalog/API.
- **Epic ordering:** Mostly sound. EPIC-23 is a runtime foundation slice; EPIC-24 correctly builds on that foundation before expanding policy breadth.
- **Within-epic sequencing:** EPIC-23 story order is coherent and mostly dependency-safe. EPIC-24 story order is mostly coherent but has one hidden dependency issue.

### Critical Violations

- **Contract ambiguity between `runtime mode` and April 1 `simulation mode`:** Story 23.1 introduces a runtime-mode contract (`live` vs `replay`) while the April 1 proposal introduces Scenario simulation mode (`annual` vs `horizon_step`). The artifacts do not yet define these as separate fields with separate ownership. This is a blocking readiness issue because implementation could collapse two distinct concepts into one overloaded `mode` field.
- **Canonical UX/architecture sources are stale for EPIC-23:** The epic text is ahead of the canonical UX and architecture docs on primary-population inheritance, dedicated investment-decision stage ownership, and runtime/replay behavior. That leaves implementers without a single authoritative contract source.

### Major Issues

- **Story 24.3 has a hidden dependency on Story 24.1:** Its acceptance criteria rely on packs being "marked unavailable for live execution," but that availability metadata is introduced by Story 24.1. Story 24.3 should either depend on 24.1 explicitly or narrow its scope.
- **Story 23.2 scope exceeds its acceptance criteria:** The narrative and test notes mention bundled, uploaded, and generated populations, but the acceptance criteria only verify bundled and uploaded populations. Generated population resolution is not explicitly accepted or tested.
- **Story 23.3 lacks a concrete normalized-result contract in the planning artifacts:** The story says a stable app-facing schema will exist, but the required fields, ownership boundary, and compatibility/versioning rules are not enumerated here. That makes downstream regression expectations under-specified.
- **Story 24.1 lacks a defined availability metadata contract:** The story requires "stable identifiers and availability metadata," but the metadata fields and semantics are not specified in the epic, UX, or architecture docs.
- **Story 24.2 lacks a concrete translator contract boundary:** The intent is correct and aligned with the architecture, but the planned artifacts do not yet specify the translator input/output shape, where translation is invoked, or what one canonical supported subsidy-family path looks like.

### Minor Concerns

- **Story 23.5 uses ambiguous outcome language:** "blocked or warned" is not deterministic enough for acceptance testing. Unsupported live-path requests need a clearer rule for when execution must stop versus when a non-blocking warning is acceptable.
- **Story 24.4/24.5 assume UI and example behavior not yet documented canonically:** The epic expects surfaced-pack readiness caveats and lightweight examples, but the UX and docs do not yet define the exact presentation pattern.

### Dependency and Duplication Notes

- **EPIC-23 vs EPIC-1 / EPIC-9:** The epic is well positioned to extend adapter/runtime behavior rather than recreate adapter capabilities, but only if Story 23.3 explicitly reuses existing mapping and ingestion primitives and Story 23.4 avoids introducing a second persistence or execution stack.
- **EPIC-24 vs EPIC-13:** The epic correctly focuses on surfacing and translating already-modeled packs rather than inventing a second template-authoring system. That boundary should remain explicit.
- **EPIC-23 / EPIC-24 vs EPIC-17 / EPIC-20:** Both new epics are intended as extensions of the existing workspace and catalog flows, not new screens. That reuse intent is stated, but the canonical UX and architecture docs have not yet been updated to make the extension boundaries unambiguous.

### Recommendations from Quality Review

- Separate `runtime_mode` and `simulation_mode` explicitly in the shared contracts and name them differently everywhere.
- Amend Story 24.3 dependencies to include Story 24.1, or remove availability-status behavior from 24.3.
- Expand Story 23.2 acceptance criteria to cover generated populations if that source class remains in scope.
- Add a minimal normalized-result schema contract and a minimal catalog-availability metadata contract to the planning artifacts before implementation starts.

## Summary and Recommendations

### Overall Readiness Status

NEEDS WORK

### Critical Issues Requiring Immediate Action

1. Separate the April 1 `simulation_mode` contract from EPIC-23 `runtime_mode` so implementers cannot conflate horizon behavior with live-vs-replay execution behavior.
2. Update the canonical UX and architecture documents to reflect the April 1 stage-ownership and runtime/data-path decisions, rather than leaving the epics as the only authoritative source.
3. Fix the hidden dependency and contract gaps in EPIC-24 around availability metadata and unavailable-pack behavior.

### Recommended Next Steps

1. Amend [epics.md](/Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/epics.md) to define distinct `simulation_mode` and `runtime_mode` fields, and add explicit contract notes for both.
2. Update [ux-design-specification.md](/Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/ux-design-specification.md) and [architecture.md](/Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/architecture.md) so they match the April 1 stage model, inherited-population behavior, live-default runtime, and replay-path rules.
3. Amend Story 23.2, Story 23.3, Story 24.1, Story 24.2, and Story 24.3 with missing acceptance criteria and explicit contracts before implementation begins.
4. Preserve reuse boundaries explicitly: EPIC-23 extends EPIC-1/9/20 rather than replacing them, and EPIC-24 extends EPIC-13/17/20 rather than creating parallel catalog or adapter logic.

### Final Note

This assessment found 2 critical issues, 5 major issues, and 2 minor concerns across document alignment, story independence, and contract completeness. The epics are directionally sound and mostly well ordered, but they are not yet crisp enough to start implementation without avoidable interpretation risk.
