---
stepsCompleted:
  - step-01-document-discovery
  - step-02-prd-analysis
  - step-03-epic-coverage-validation
  - step-04-ux-alignment
  - step-05-epic-quality-review
  - step-06-final-assessment
project: reformlab
date: 2026-04-19
documentsIncluded:
  prd:
    - _bmad-output/planning-artifacts/prd.md
  architecture:
    - _bmad-output/planning-artifacts/architecture.md
    - _bmad-output/planning-artifacts/architecture-diagrams.md
  epics:
    - _bmad-output/planning-artifacts/epics.md
  ux:
    - _bmad-output/planning-artifacts/ux-design-specification.md
---

# Implementation Readiness Assessment Report

**Date:** 2026-04-19
**Project:** reformlab

## Document Inventory

### PRD Files Found

**Whole Documents:**
- `_bmad-output/planning-artifacts/prd.md` (44,806 bytes, modified 2026-04-02 13:34:50 CEST)

**Sharded Documents:**
- None found

### Architecture Files Found

**Whole Documents:**
- `_bmad-output/planning-artifacts/architecture.md` (25,226 bytes, modified 2026-04-02 13:34:50 CEST)
- `_bmad-output/planning-artifacts/architecture-diagrams.md` (11,146 bytes, modified 2026-04-02 13:34:50 CEST)

**Sharded Documents:**
- None found

### Epics & Stories Files Found

**Whole Documents:**
- `_bmad-output/planning-artifacts/epics.md` (80,611 bytes, modified 2026-04-19 12:04:56 CEST)

**Sharded Documents:**
- None found

### UX Design Files Found

**Whole Documents:**
- `_bmad-output/planning-artifacts/ux-design-specification.md` (126,041 bytes, modified 2026-04-01 22:51:59 CEST)

**Sharded Documents:**
- None found

### Discovery Issues

- No critical duplicate whole-plus-sharded document formats found.
- No required document type appears missing.
- Architecture has two whole-document matches; `architecture.md` is treated as primary and `architecture-diagrams.md` as supporting material.

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
FR38: System provides an extensible library of statistical methods for merging datasets that do not share the same sample. Initial methods: uniform distribution, IPF, conditional sampling. Additional methods (e.g. statistical matching) to be added as the population layer matures.
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

NFR1: Full population simulation (100,000 households) completes in under 10 seconds on a standard laptop (4-core, 16GB RAM)
NFR2: All orchestration hot paths use vectorized array computation where feasible; no row-by-row loops in core aggregation/calculation paths
NFR3: Framework handles populations up to 500,000 households on 16GB RAM without crashing; larger populations produce a clear memory warning before attempting execution
NFR4: YAML configuration loading and validation completes in under 1 second for typical policy definitions
NFR5: Analytical operations (distributional analysis, welfare computation, fiscal cost) execute in under 5 seconds for 100,000 households
NFR6: Identical inputs produce bit-identical outputs across runs on the same machine
NFR7: Identical inputs produce identical outputs across different machines and operating systems (Python version and dependency versions held constant)
NFR8: Random seeds used in synthetic population generation are explicit, pinned, and recorded in the run manifest
NFR9: Run manifests are generated automatically with zero manual effort from the user
NFR10: No implicit temporal assumptions -- all period semantics are explicit in configuration
NFR11: When users supply restricted microdata, the framework never persists, copies, or transmits data beyond the user's local environment
NFR12: Input data paths are referenced in run manifests, not embedded -- no raw data in manifests or logs
NFR13: No telemetry, analytics, or network calls from the framework -- fully offline operation
NFR14: CSV and Parquet files are supported for all data input and output operations
NFR15: OpenFisca integration supports both import contracts (CSV/Parquet) and version-pinned API orchestration modes
NFR16: All Python API objects have sensible `__repr__` for Jupyter notebook display
NFR17: Framework has zero dependency on cloud providers, data vendors, or institutional infrastructure
NFR18: pytest test suite with high coverage on adapters, orchestration, template logic, and simulation runner
NFR19: All shipped examples run end-to-end without modification on a fresh install (tested in CI)
NFR20: YAML examples are tested in CI to prevent documentation drift
NFR21: Semantic versioning -- breaking changes only on major versions

Total NFRs: 21

### Additional Requirements

- Strategic architecture constraint: OpenFisca is the tax-benefit computation backend accessed through `ComputationAdapter`; no custom policy engine, formula compiler, or entity graph engine should be built.
- Strategic architecture constraint: the dynamic orchestrator is the core product layer and must execute a pluggable step pipeline between yearly OpenFisca computations.
- Scope constraint: endogenous market-clearing models, physical system feedback loops, full behavioral equilibrium modeling, fully automated report authoring, and advanced authoring beyond template-driven workflows are outside the original MVP.
- Current-state constraint: the April 2026 product baseline has moved beyond the original Phase 1 MVP boundary; population generation, portfolio composition, richer GUI flows, and behavioral-model scaffolding are active product surfaces.
- Interface constraint: the primary product interface is now a web GUI backed by React 19 SPA + FastAPI at `app.reformlab.fr` / `api.reformlab.fr`; Python package and YAML remain first-class.
- Delivery constraint: Python package distribution via PyPI must support `pip install reformlab`; Docker/Kamal deployment applies to the web product.
- Validation requirement: carbon tax MVP must validate against published reference results, including aggregate revenue and distributional patterns.
- Testing requirement: validation must include formula-level unit tests, policy-regression golden outputs, and cross-model benchmark tests where overlap exists.
- Statistical validity requirement: synthetic population generation must match known marginal distributions within documented tolerances, and deviations must be reported.
- Data governance requirement: open-data operation is the default; restricted user-supplied microdata must remain local and be referenced rather than embedded.
- Reproducibility requirement: run manifests must include engine version, dependency versions, input data hashes, parameters, assumptions, and timestamp.
- Replication requirement: exported replication packages must run on a clean environment using only package contents plus `pip install reformlab`.
- Data interoperability requirement: inputs must support CSV and Parquet; outputs must support CSV, Parquet, and Arrow; policy definitions use YAML.
- Documentation requirement: README/quickstart, installation guide, carbon tax tutorial, YAML reference, Python API reference, OpenFisca integration guide, assumptions guide, and example notebooks are part of MVP documentation.
- Example requirement: shipped examples must include carbon tax templates, quickstart notebook, researcher workflow notebook, and OpenFisca integration examples, all running end-to-end in CI.
- Release requirement: standard Python packaging, automated PyPI release through CI/CD, semantic versioning, and pinned dependency ranges for reproducibility.

### PRD Completeness Assessment

The PRD contains a complete explicit requirement set with 55 functional requirements and 21 non-functional requirements. It also includes substantial strategic, domain, interface, validation, documentation, and release constraints. The main readiness risk is not absence of PRD requirements, but scope layering: original MVP, growth streams, and the April 2026 product-state update coexist in one document. Epic coverage validation must therefore distinguish baseline/current product requirements from historical sequencing notes and growth-stream requirements.

## Epic Coverage Validation

### Epic FR Coverage Extracted

FR2: Covered in EPIC-23.
FR3: Covered in EPIC-23.
FR4: Covered in EPIC-23.
FR5: Covered in EPIC-23.
FR7: Covered in EPIC-24.
FR11: Covered in EPIC-23.
FR18: Covered in EPIC-23.
FR25: Covered in EPIC-23 and EPIC-26.
FR26: Covered in EPIC-23 and EPIC-26.
FR27: Covered in EPIC-23.
FR28: Covered in EPIC-23.
FR32: Covered in EPIC-23 and EPIC-26.
FR43: Covered in EPIC-24 and EPIC-25.
FR44: Covered in EPIC-24.
FR45: Covered in EPIC-24.
FR46: Covered in EPIC-24 and EPIC-25.

Additional non-PRD functional references in epics:
- FR32a, FR32c
- FR-RUNTIME-1 through FR-RUNTIME-7

Total PRD FRs explicitly covered in current epics: 16

### Coverage Matrix

| FR Number | PRD Requirement | Epic Coverage | Status |
| --------- | --------------- | ------------- | ------ |
| FR1 | Analyst can ingest OpenFisca household-level outputs from CSV or Parquet. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR2 | System can optionally execute OpenFisca runs through a version-pinned API adapter. | EPIC-23 / BKL-2304 | Covered |
| FR3 | Analyst can map OpenFisca variables to project schema fields through configuration. | EPIC-23 / BKL-2303 | Covered |
| FR4 | System validates mapping/schema contracts with clear field-level errors. | EPIC-23 / BKL-2303, BKL-2305 | Covered |
| FR5 | Analyst can load synthetic populations and external environmental datasets. | EPIC-23 / BKL-2302 | Covered |
| FR6 | System records data source metadata and hashes for every run. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR7 | Analyst can load prebuilt environmental policy templates (carbon tax, subsidy, rebate, feebate). | EPIC-24 / BKL-2401, BKL-2404 | Covered |
| FR8 | Analyst can define reforms as parameter overrides to a baseline scenario. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR9 | System stores versioned scenario definitions in a scenario registry. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR10 | Analyst can run multiple scenarios in one batch for comparison. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR11 | Analyst can compose tax-benefit baseline outputs with environmental template logic in one workflow. | EPIC-23 / BKL-2303 | Covered |
| FR12 | Scenario configuration supports year-indexed policy schedules for at least ten years. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR13 | System can execute iterative yearly simulations for 10+ years. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR14 | System can carry forward state variables between yearly iterations. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR15 | System can track asset/cohort vintages by year. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR16 | Analyst can configure transition rules for state updates between years. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR17 | System enforces deterministic sequencing and explicit random-seed control in dynamic runs. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR18 | System outputs year-by-year panel results for each scenario. | EPIC-23 / BKL-2303, BKL-2306 | Covered |
| FR19 | Analyst can compute distributional indicators by income decile. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR20 | Analyst can compute indicators by geography. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR21 | Analyst can compute welfare indicators including winners/losers counts and net gains/losses. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR22 | Analyst can compute fiscal indicators per year and cumulatively. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR23 | Analyst can define custom indicators as derived formulas over run outputs. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR24 | Analyst can compare indicators across scenarios side-by-side. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR25 | System automatically generates immutable run manifests including versions, hashes, parameters, and assumptions. | EPIC-23 / BKL-2301, BKL-2305, BKL-2306; EPIC-26 / BKL-2604 | Covered |
| FR26 | Analyst can inspect assumptions and mappings used in any run. | EPIC-23 / BKL-2305; EPIC-26 / BKL-2604 | Covered |
| FR27 | System emits warnings for unvalidated templates, mappings, or unsupported run configurations. | EPIC-23 / BKL-2304, BKL-2305 | Covered |
| FR28 | Results are pinned to scenario version, data version, and OpenFisca adapter/version. | EPIC-23 / BKL-2301, BKL-2305 | Covered |
| FR29 | System maintains run lineage across yearly iterations and scenario variants. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR30 | User can run full workflows from a Python API in notebooks. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR31 | User can configure workflows with YAML/JSON files for analyst-friendly version control. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR32 | User can use a stage-based no-code GUI to create, inspect, clone, and run scenarios. | EPIC-23 / BKL-2304, BKL-2306; EPIC-26 / BKL-2601, BKL-2607 | Covered |
| FR33 | User can export tables and indicators in CSV/Parquet for downstream reporting. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR34 | User can run an OpenFisca-plus-environment quickstart in under 30 minutes. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR35 | User can access template authoring and dynamic-run documentation with reproducible examples. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR36 | Analyst can download and cache public datasets from institutional sources. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR37 | Analyst can browse available datasets and select which to include in a population. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR38 | System provides an extensible library of statistical methods for merging datasets without shared samples. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR39 | Analyst can choose which merge method to apply at each dataset join, with plain-language explanation. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR40 | System produces a complete synthetic population with household-level attributes sufficient for policy simulation. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR41 | Every merge, imputation, and extrapolation is recorded as an explicit assumption in the governance layer. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR42 | System validates generated populations against known marginal distributions from source data. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR43 | Analyst can compose multiple individual policy templates into a named policy portfolio. | EPIC-24 / BKL-2403, BKL-2404; EPIC-25 / BKL-2502, BKL-2505, BKL-2506 | Covered |
| FR44 | System executes a simulation with a policy portfolio, applying all bundled policies together. | EPIC-24 / BKL-2403, BKL-2404 | Covered |
| FR45 | Analyst can compare results across different policy portfolios side-by-side. | EPIC-24 / BKL-2403 | Covered |
| FR46 | Analyst can define custom policy templates that participate in portfolios alongside built-in templates. | EPIC-24 / BKL-2402, BKL-2403, BKL-2405; EPIC-25 / BKL-2501, BKL-2503, BKL-2504, BKL-2506 | Covered |
| FR47 | System models household investment decisions as discrete choice problems using logit functions. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR48 | System expands population by alternatives and evaluates each alternative through OpenFisca for household-specific cost calculations. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR49 | Logit draws use seed-controlled randomness for reproducibility. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR50 | Panel output records which decision each household made in each domain for each year. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR51 | Taste parameters are recorded in run manifests. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR52 | Analyst can calibrate discrete choice taste parameters against observed transition rates. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR53 | System validates calibrated parameters against known marginal distributions. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR54 | Analyst can export a self-contained replication package including data, configuration, manifests, and results. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |
| FR55 | Replication package is reproducible on a clean environment with only `pip install reformlab` and the package contents. | NOT FOUND in active EPIC-23 to EPIC-26 document | MISSING |

### Missing Requirements

#### Critical Missing FRs

FR1: Analyst can ingest OpenFisca household-level outputs from CSV or Parquet.
- Impact: This is foundational to the OpenFisca-first strategy and import-contract mode.
- Recommendation: Add explicit traceability to the existing completed data/adapters epic or include a current maintenance story if this contract is still active.

FR6: System records data source metadata and hashes for every run.
- Impact: This is part of run reproducibility and overlaps with manifest trust, but the current epics mention manifests without explicitly guaranteeing data-source hashes.
- Recommendation: Add to EPIC-23 Story 23.5 or EPIC-26 Story 26.4 acceptance criteria.

FR8: Analyst can define reforms as parameter overrides to a baseline scenario.
- Impact: Core scenario modeling path is not explicitly traceable in current active epics.
- Recommendation: Add historical coverage reference or a current policy-set/scenario story reference.

FR9: System stores versioned scenario definitions in a scenario registry.
- Impact: Scenario versioning is required for FR28 result pinning but is not independently traceable in active epics.
- Recommendation: Add explicit scenario-registry coverage to EPIC-26 Scenario-stage work or reference the completed scenario epic.

FR10: Analyst can run multiple scenarios in one batch for comparison.
- Impact: Scenario comparison is a primary analyst workflow and is only indirectly implied through Stage 5 comparison surfaces.
- Recommendation: Add explicit batch/comparison execution coverage to EPIC-26 Stage 5 or trace to completed epics.

FR12-FR17: Year-indexed policy schedules, 10+ year yearly simulation, state carry-forward, vintage tracking, transition rules, and deterministic sequencing.
- Impact: These define the dynamic orchestrator core product. No active epic in EPIC-23 to EPIC-26 revalidates this foundation.
- Recommendation: Add an explicit archived-epic coverage appendix or current regression-hardening story for orchestrator contracts.

FR19-FR24: Distributional, geographic, welfare, fiscal, custom, and side-by-side indicator computation.
- Impact: These are decision-output requirements. Current epics preserve result surfaces but do not trace core indicator capabilities.
- Recommendation: Add explicit indicator coverage references, likely to completed analytics/result epics, or add Stage 5 regression coverage.

FR29: System maintains run lineage across yearly iterations and scenario variants.
- Impact: Run lineage is necessary for reproducible dynamic analysis and comparison.
- Recommendation: Add to EPIC-23 manifests/result metadata or EPIC-26 Run Manifest Viewer acceptance criteria.

FR30-FR31: Python API notebook workflows and YAML/JSON workflow configuration.
- Impact: These first-class non-web interfaces are absent from current active epics, which focus on the web product.
- Recommendation: Add explicit coverage references for library/YAML interface maintenance or mark as already satisfied in archived epics.

FR33-FR35: CSV/Parquet exports, quickstart, and template/dynamic-run documentation.
- Impact: Enablement and downstream reporting are central to adoption and reproducibility.
- Recommendation: Add docs/export coverage references or include current regression/doc stories.

#### High Priority Missing FRs

FR36-FR42: Public dataset download/cache, dataset browsing, merge-method library, merge-method selection, complete synthetic population generation, assumption logging for generation, and marginal validation.
- Impact: Population generation is part of the April 2026 active product surface according to the PRD current-state update, but current active epics only address population executability and Quick Test Population.
- Recommendation: Add coverage references to existing population-generation epics or create a dedicated active epic/story set.

FR47-FR53: Discrete choice, alternative expansion, seed-controlled logit draws, decision panel output, taste-parameter manifests, calibration, and calibration validation.
- Impact: Investment decisions get a UX stage in EPIC-26, but the behavioral modeling engine requirements are not covered there.
- Recommendation: Add explicit modeling/backend coverage or mark EPIC-26 as UX shell only and link to the behavioral-model epic.

FR54-FR55: Replication package export and clean-environment reproducibility.
- Impact: These are growth-stream requirements and may be intentionally deferred, but current epics do not state their status.
- Recommendation: Mark as deferred in epics or create a future epic placeholder so readiness review distinguishes "not covered yet" from "forgotten."

### Requirements in Epics but Not in PRD FR List

- FR32a and FR32c refine the GUI workflow but are not numbered PRD FRs.
- FR-RUNTIME-1 through FR-RUNTIME-7 are current runtime requirements derived from product/architecture updates, not PRD-numbered FRs.
- UX-DR6 through UX-DR15 are UX requirements, not PRD FRs, and should be validated in the UX alignment step.

### Coverage Statistics

- Total PRD FRs: 55
- PRD FRs covered in current epics: 16
- PRD FRs missing from current epics: 39
- Coverage percentage: 29.1%

Coverage note: `epics.md` states EPIC-1 through EPIC-22 are complete and archived in git history. This validation did not count archived-only coverage because the current epics document does not provide a traceable coverage appendix for those completed epics.

## UX Alignment Assessment

### UX Document Status

Found: `_bmad-output/planning-artifacts/ux-design-specification.md`

Current UX version: Revision 4.1, dated 2026-04-01.

Supporting architecture documents reviewed:
- `_bmad-output/planning-artifacts/architecture.md`
- `_bmad-output/planning-artifacts/architecture-diagrams.md`

### UX to PRD Alignment

Aligned areas:
- PRD current-state update says the primary product interface is now a web GUI; UX Revision 4.1 treats the GUI as the primary analyst surface.
- PRD FR32 requires a stage-based no-code GUI; UX defines the five-stage workspace: Policies, Population, Investment Decisions, Scenario, Run / Results / Compare.
- PRD FR25-FR29 require manifests, assumptions, version pinning, and lineage; UX makes run manifests and traceability visible in results and Stage 5.
- PRD FR43-FR46 require policy portfolios/templates/custom policies; UX Revision 4.1 translates this into Policy Sets, closed policy types, API-driven categories, create-from-scratch authoring, editable parameter groups, and save/load.
- PRD FR5 and FR36-FR42 require population loading/generation; UX gives Stage 2 population library, upload, preview, profile, and data fusion flows.
- PRD FR47-FR53 cover behavioral/discrete-choice work; UX gives Investment Decisions a dedicated optional stage.

UX requirements not explicitly represented as PRD-numbered FRs:
- FR32a and FR32c from `epics.md`: inherited primary population and Scenario-stage execution settings.
- UX-DR6 through UX-DR15: five-stage nav rail, three policy types, category model, from-scratch authoring, editable groups, reusable policy sets, dedicated Investment Decisions stage, Scenario integration gate, Run Manifest Viewer, Quick Test Population, and deterministic scenario naming.
- UX lineage specifics: click-to-highlight upstream chain, depth-bounded tracing, lineage DAG lenses, and lineage diff.
- UX export specifics: notebook export, export preview, embedded manifest/hash, and view-level export affordances.

### UX to Architecture Alignment

Architecture-supported UX decisions:
- React SPA plus FastAPI backend supports the web-GUI product direction.
- Typed frontend API client and server route layer support stage-based frontend flows.
- Canonical `Scenario`, `Portfolio`/policy bundle, and `Run` objects support durable scenario/run workflows.
- Architecture explicitly separates `simulation_mode` on Scenario from `runtime_mode` on Run/manifests, matching UX Revision 4.1.
- Population ownership by Stage 2 and inherited display in Scenario is explicitly described in architecture.
- Manifest-first governance, run metadata, hashes, lineage, and result persistence support Stage 5 manifest inspection.
- PyArrow-first tables and CSV/Parquet support align with population upload/explore/export requirements.
- Shadcn/Radix/Tailwind/React technology choices align with the UX design system.

Architecture gaps or misalignments:
- Architecture section 5.10 still describes the GUI as a four-stage shell with an `engine` stage. UX Revision 4.1 and active epics require five stages, with Investment Decisions separated from Scenario.
- Architecture route inventory lists `/api/templates` with `GET /categories`, while UX and EPIC-25 require `GET /api/categories`. The canonical categories endpoint needs one source of truth.
- Architecture supports manifests and lineage as backend concepts, but it does not define the lineage graph API/data contract needed for UX lineage DAGs, lenses, and click-through result tracing.
- Architecture lists `/api/exports` as CSV export only, while UX expects CSV, Parquet, and Notebook export with preview and provenance metadata.
- Architecture uses `Portfolio` terminology in several places, while UX Revision 4.1 removes "Portfolio" from user-facing copy in favor of Policy Set. Internal compatibility is acceptable, but API/user-facing naming needs migration guidance.
- UX says the app is local-first with a bundled local service layer, while the PRD/architecture also describe deployed domains and Docker/Kamal production hosting. The deployment posture should be clarified so offline/local-first UX promises are not accidentally contradicted by hosted assumptions.
- UX requires category-to-population-column cross-stage warnings in Stage 1 and Stage 2; architecture has validation routes and data contracts, but does not yet specify category column compatibility as an API contract.
- UX requires Quick Test Population; architecture supports population library concepts but does not specify this seed artifact or its not-analysis-grade metadata.

### Alignment Issues

1. Five-stage workspace is not yet fully reflected in architecture.
   - Impact: Implementers may follow stale four-stage/Engine-stage architecture text instead of Revision 4.1.
   - Recommendation: Update architecture section 5.10 and diagrams to match the five-stage model and keep `engine` only as a migration alias if needed.

2. Categories API path is inconsistent.
   - Impact: Frontend and backend implementations may split between `/api/templates/categories` and `/api/categories`.
   - Recommendation: Declare `GET /api/categories` canonical, with compatibility aliases only if required.

3. Lineage UX exceeds current architecture detail.
   - Impact: Clickable result lineage, DAG lenses, and depth-bounded tracing cannot be implemented consistently without a lineage data contract.
   - Recommendation: Add architecture for result-to-lineage graph nodes, edges, lens metadata, and query endpoints.

4. Export UX exceeds current server route definition.
   - Impact: CSV-only export architecture does not satisfy UX expectations for Parquet and Notebook export with provenance.
   - Recommendation: Expand export architecture or explicitly defer Notebook export.

5. UX document includes historical sections that conflict with Revision 4.1.
   - Impact: The same document contains old four-stage component trees and `EngineScreen` references after the canonical five-stage revision.
   - Recommendation: Add a short "canonical as of Revision 4.1" index or move superseded sections to an appendix.

### Warnings

- UX documentation is present and substantial; missing UX documentation is not a risk.
- The main UX readiness risk is version drift between PRD, UX, architecture, and epics rather than lack of detail.
- The active epics cover the Revision 4.1 UX slice well, but the architecture should be updated before or during implementation to avoid stale four-stage assumptions.

## Epic Quality Review

### Review Scope

Reviewed active epics and stories in `_bmad-output/planning-artifacts/epics.md`:
- EPIC-23: Live OpenFisca Runtime and Executable Population Alignment
- EPIC-24: Live Policy Catalog Activation and Domain-to-OpenFisca Translation
- EPIC-25: Stage 1 Policies Redesign (Revision 4.1 UX)
- EPIC-26: Five-Stage Workspace Migration and Stage Completion

The file states EPIC-1 through EPIC-22 are complete and archived in git history. This review evaluates the current epics document, not archived story files.

### Critical Violations

No critical epic-quality violations found in the active EPIC-23 through EPIC-26 backlog.

Specific checks passed:
- No forward dependencies found within active epics.
- No circular dependencies found.
- Story dependencies progress backward or within the same epic in order.
- Stories include test notes and mostly testable acceptance criteria.
- No "create every table/model up front" database/entity anti-pattern found.
- Brownfield integration context is acknowledged through "Builds on" references and scope notes.

### Major Issues

1. Archived foundations are referenced but not traceable in the current epics document.
   - Examples: EPIC-23 builds on EPIC-1, EPIC-9, EPIC-17, EPIC-20, EPIC-22; EPIC-24 builds on EPIC-2, EPIC-12, EPIC-13, EPIC-20, EPIC-23; EPIC-25 and EPIC-26 also depend on completed foundations.
   - Why this matters: The active stories are valid brownfield work, but implementation readiness depends on contracts from archived epics that are not visible in the current planning artifact.
   - Recommendation: Add a "Completed Foundations Reference" appendix listing each dependency, the completed capability it provides, and where to find the canonical implementation/story evidence.

2. Several story titles are technical rather than user-value phrased.
   - Examples: Story 23.1 "Define explicit runtime-mode contract and default-live execution semantics"; Story 23.3 "Normalize live OpenFisca results into the stable app-facing output schema"; Story 24.2 "Implement domain-layer live translation for subsidy-style policies without adapter-interface changes"; Story 25.1 "Add API-driven categories endpoint and formula-help metadata."
   - Why this matters: The story bodies and acceptance criteria usually recover the user value, but the backlog title can steer implementation toward internal plumbing instead of user-visible behavior.
   - Recommendation: Rephrase titles to lead with analyst-visible outcome while retaining the technical constraint in implementation notes.

3. EPIC-24 has a story-level dependency on Story 23.4 instead of an epic-level contract.
   - Example: Story 24.1 depends on Story 23.4.
   - Why this matters: A downstream epic depending on one story from the prior epic can be brittle if the actual enabling contract is spread across Stories 23.1 through 23.5.
   - Recommendation: Express the dependency as "EPIC-23 live-default runtime and normalized result contract" or list the exact contract dependencies, not only Story 23.4.

4. Some 8-point stories bundle backend, frontend, persistence, migration, and test work.
   - Examples: Story 25.3 includes frontend wizard, backend endpoint, policy creation defaults, composition-panel parity, persistence, and tests; Story 25.5 includes PolicySet entity, backend routes, scenario references, localStorage migration, save/load/clone UX, naming behavior, and compatibility.
   - Why this matters: These may still fit as 8-point stories, but they have multiple integration boundaries and a higher risk of partial completion.
   - Recommendation: Keep as single stories only if implementation ownership is unified; otherwise split along backend contract, frontend workflow, and migration/persistence boundaries.

5. Regression/documentation stories are broad closure buckets.
   - Examples: Story 23.6, Story 24.5, Story 25.6, Story 26.7.
   - Why this matters: Closure stories can become catch-alls where acceptance becomes harder to verify cleanly.
   - Recommendation: Ensure each closure story has a concrete test file/flow ownership list before implementation starts.

### Minor Concerns

1. EPIC-25 dependency language is slightly ambiguous.
   - The epic says it builds on EPIC-24, but scope notes say it can start before the five-stage shell migration and Epic 24 can expand which templates appear.
   - Recommendation: State explicitly which parts are independent of EPIC-24 and which only consume EPIC-24 metadata when available.

2. User-facing terminology migration needs stronger guardrails.
   - EPIC-25 requires "Policy Set" user copy, while architecture and older UX sections still use Portfolio.
   - Recommendation: Add a terminology acceptance criterion to affected stories requiring visible copy checks and compatibility alias tests.

3. Some acceptance criteria use review-based wording.
   - Examples include "when reviewed" criteria for absence of runtime selectors or subsidy-specific adapter behavior.
   - Recommendation: Convert review-based criteria into concrete assertions where possible, such as route/component absence tests, type/interface contract tests, or source-level forbidden-import checks.

### Per-Epic Assessment

EPIC-23:
- User value: Strong. Analyst can run the web product against actual selected populations through live OpenFisca by default.
- Independence: Acceptable for brownfield work; depends on completed foundations but does not depend on future active epics.
- Story sequencing: Sound. Dependencies flow from contract to resolver to normalization to default-live route to metadata/regression.
- Readiness concern: Story titles and several tasks are infrastructure-heavy; keep analyst-visible behavior prominent.

EPIC-24:
- User value: Strong. Analyst can discover, configure, and execute surfaced policy packs.
- Independence: Depends on EPIC-23 live runtime contract, which is valid in sequence.
- Story sequencing: Sound. Catalog exposure precedes translation, portfolio execution, workspace surfacing, and regression examples.
- Readiness concern: Story 24.1 dependency on Story 23.4 is narrower than the actual enabling contract.

EPIC-25:
- User value: Strong. Analyst can build reusable policy sets in the redesigned Policies stage.
- Independence: Mostly sound; can proceed in parallel with parts of EPIC-24 if availability metadata is treated as optional.
- Story sequencing: Sound but dense. Categories precede layout, from-scratch creation, group editing, policy-set persistence, then validation polish.
- Readiness concern: Stories 25.3 and 25.5 are integration-heavy and should have clear implementation boundaries.

EPIC-26:
- User value: Strong. Analyst gets the canonical five-stage workspace and completed Run/Results/Compare affordances.
- Independence: Sequenced after EPIC-25 where policy-set references are needed; otherwise route split can begin independently.
- Story sequencing: Sound. Nav migration precedes stage extraction/refactor, Stage 5 completion, then Quick Test, naming, and regression.
- Readiness concern: The architecture still contains stale four-stage shell text, so implementers need explicit guidance that EPIC-26 supersedes it.

### Best Practices Compliance Checklist

| Epic | User Value | Independent in Sequence | Story Sizing | No Forward Dependencies | Clear ACs | Traceability |
| ---- | ---------- | ----------------------- | ------------ | ----------------------- | --------- | ------------ |
| EPIC-23 | Pass | Pass with archived-foundation caveat | Pass with dense technical stories | Pass | Pass | Pass for active FRs |
| EPIC-24 | Pass | Pass with EPIC-23 contract dependency | Pass | Pass | Pass | Pass for active FRs |
| EPIC-25 | Pass | Pass with EPIC-24 availability caveat | Watch | Pass | Pass | Pass for UX/active FRs |
| EPIC-26 | Pass | Pass with EPIC-25 policy-set caveat | Pass | Pass | Pass | Pass for UX/active FRs |

### Epic Quality Recommendation

The active epics are implementation-usable after clarifying archived-foundation references and updating stale architecture guidance. No blocker-level quality violation prevents development, but dependency traceability and title/user-value phrasing should be tightened before using these epics as the sole implementation source of truth.

## Summary and Recommendations

### Overall Readiness Status

NEEDS WORK

The active EPIC-23 through EPIC-26 backlog is largely implementation-usable as a focused active slice. The full planning set is not yet cleanly ready as a complete PRD-to-implementation trace because the current epics document only covers 16 of 55 PRD functional requirements and relies on EPIC-1 through EPIC-22 being archived in git history rather than traceable in the active planning artifact.

### Critical Issues Requiring Immediate Action

1. PRD functional requirement traceability is incomplete in the current epics document.
   - Evidence: 39 of 55 PRD FRs are not traceable in active EPIC-23 through EPIC-26.
   - Required action: Add an archived-epic coverage appendix or reintroduce coverage references for completed EPIC-1 through EPIC-22.

2. Architecture still contains stale four-stage GUI guidance.
   - Evidence: Architecture section 5.10 describes a four-stage shell and `engine` stage, while UX Revision 4.1 and EPIC-26 require five stages.
   - Required action: Update architecture and diagrams so the five-stage model is canonical.

3. Categories API contract is inconsistent.
   - Evidence: UX and EPIC-25 require `GET /api/categories`; architecture route inventory lists `/api/templates` with `GET /categories`.
   - Required action: Declare one canonical endpoint and document compatibility behavior if both are kept.

4. UX lineage and export promises exceed current architecture detail.
   - Evidence: UX specifies lineage DAGs, lens overlays, notebook export, export preview, and manifest-backed exports; architecture defines manifests and CSV export but not those full contracts.
   - Required action: Either add architecture contracts for these features or explicitly defer them.

5. Current planning artifacts mix canonical and superseded guidance.
   - Evidence: UX Revision 4.1 supersedes older four-stage/Engine guidance, but the older sections remain in the same document and architecture still reflects parts of them.
   - Required action: Add a canonical-current-state index and move superseded material to an appendix or clearly mark it as historical.

### Recommended Next Steps

1. Add a traceability appendix to `epics.md` mapping all 55 PRD FRs to either active epics, completed archived epics, or explicitly deferred future epics.

2. Patch `architecture.md` section 5.10 and relevant diagrams to reflect the five-stage workspace, Policy Set terminology, inherited primary population, dedicated Investment Decisions stage, and Stage 5 manifest viewer.

3. Resolve API contract naming for categories and policy sets before implementation starts: canonical paths, response schemas, compatibility aliases, and tests.

4. Decide whether lineage DAGs, notebook export, and Parquet export are in the current implementation slice. If yes, add architecture and epic coverage; if not, mark them deferred in UX and epics.

5. Tighten EPIC-23 through EPIC-26 by adding archived-foundation references, rephrasing technical story titles toward user outcomes, and splitting dense 8-point stories if ownership spans backend, frontend, migration, and persistence.

### Issue Count

This assessment identified:
- 39 missing PRD FR traceability entries in the active epics document.
- 5 UX/architecture alignment issues.
- 5 major and 3 minor epic-quality concerns.
- 3 categories of non-PRD functional references in epics requiring classification.

### Final Note

The strongest finding is not that the active backlog is poor. It is that the artifacts are at different revision levels. EPIC-23 through EPIC-26 are coherent for the current active web-product slice, but the broader PRD/UX/architecture package needs synchronization before it can serve as a reliable end-to-end implementation source of truth.

**Assessment completed:** 2026-04-19  
**Assessor:** Codex using `bmad-check-implementation-readiness`
