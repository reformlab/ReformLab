# Sprint Change Proposal — Phase 2 Scope Definition

**Project:** ReformLab
**Author:** Lucas
**Date:** 2026-03-02
**Change Scope:** Major — New phase definition with 7 epics, PRD/Architecture/UX/Backlog updates
**Status:** Approved and Applied

---

## Section 1: Issue Summary

### Problem Statement

Phase 1 is complete (10 epics, 57 stories, 1,537 tests, 149/149 exit criteria passing). The project needs a defined Phase 2 backlog with prioritized epics and stories. The PRD defined Phase 2 features at a high level, but several have evolved significantly during Phase 1 execution:

- The "reduced-form behavioral module" has been replaced by a concrete **discrete choice model** design (logit-based household investment decisions), documented in a detailed architecture design note.
- A **realistic population generation library** has emerged as a critical prerequisite — the current synthetic population is a 3-column benchmarking stub, insufficient for behavioral modeling.
- A **policy portfolio model** (composing multiple policies into bundled scenarios) is needed for realistic policy analysis.
- The **GUI** has been elevated from "expansion" to the **showcase product** — the primary deliverable stakeholders will see.

### Context

This change was identified at the Phase 1/Phase 2 boundary. Phase 1 delivered a complete, tested platform with a proven architecture. The discrete choice design note (2026-03-01) demonstrated that Phase 1 infrastructure (step pipeline, adapter, vintage tracking, seed control, manifests) directly supports behavioral modeling.

### Evidence

- Phase 1 retro confirms readiness: 1,537 tests, 86% coverage, hardened OpenFisca adapter (Epic 9), improved API ergonomics (Epic 10)
- Discrete choice design note proves architectural feasibility — `DiscreteChoiceStep` registers as a standard `OrchestratorStep`, population expansion uses existing `ComputationAdapter.compute()`
- Current `data/synthetic.py` produces only 3 columns (household_id, income, carbon_emissions) — insufficient for vehicle/heating/renovation choice sets
- PRD Phase 2 triggers are largely met: scenario flows stable, governance validated, CSV/Parquet contracts stable, 100k population benchmarked at ~1.7s

---

## Section 2: Impact Analysis

### Epic Impact

| Existing Epic | Impact | Details |
|---|---|---|
| EPIC-1 through EPIC-10 | **None** | All Phase 1 epics remain done and unchanged. Phase 2 builds on top. |

**New Epics Required:**

| Epic | Title | Dependencies | Key Deliverable |
|---|---|---|---|
| EPIC-11 | Realistic Population Generation Library | EPIC-1, EPIC-5 | INSEE data loaders, statistical methods library, French example pipeline, pedagogical notebook |
| EPIC-12 | Policy Portfolio Model | EPIC-2, EPIC-3 | Compose multiple policies into bundled scenarios, orchestrator portfolio execution |
| EPIC-13 | Additional Policy Templates + Extensibility | EPIC-2, EPIC-12 | Custom template authoring, new built-in templates, portfolio-ready templates |
| EPIC-14 | Discrete Choice Model for Household Decisions | EPIC-3, EPIC-11, EPIC-12 | `DiscreteChoiceStep`, population expansion, logit model, vehicle + heating domains |
| EPIC-15 | Calibration Engine | EPIC-14, EPIC-11 | Calibrate taste parameters against observed transition rates |
| EPIC-16 | Replication Package Export | EPIC-5, all prior | Self-contained reproducible packages with data, config, manifests, results |
| EPIC-17 | GUI Showcase Product | All P2 epics | Full workbench: data fusion, portfolio design, simulation, persistent results, comparison |

### Artifact Conflicts

| Artifact | Impact Level | Changes Required |
|---|---|---|
| **PRD** | **Moderate** | Update Phase 2 feature table, add new FRs for population generation/portfolios/discrete choice/calibration, update Phase 3 (add sensitivity sweeps) |
| **Architecture** | **Moderate** | Add Phase 2 Architecture Extensions section (new subsystems: population, calibration; extensions to templates, server, frontend) |
| **UX Design** | **Moderate** | Add Phase 2 GUI workflows (data fusion workbench, policy portfolio designer, enhanced results) |
| **Epics** | **Major** | Add 7 new epics with stories and acceptance criteria |
| **Sprint Status** | **Minor** | Add new epic/story entries as backlog |
| **Project Context** | **Minor** | Add new subsystem patterns and testing conventions |

### Technical Impact

- **New subsystems:** `population/` (data loaders, methods library, pipeline builder), `calibration/` (parameter calibration)
- **Extended subsystems:** `templates/` (portfolio composition), `orchestrator/` (DiscreteChoiceStep), `governance/` (population assumption provenance), `server/` (new API routes), `frontend/` (data fusion workbench, portfolio designer)
- **Performance scaling:** Discrete choice introduces ~11x computation scaling (100k households × 5 alternatives × 2 domains). Manageable on laptop for 100k; eligibility filtering mitigates for larger populations.
- **Data dependencies:** Real INSEE/Eurostat datasets need download/cache infrastructure
- **Testing expansion:** Statistical method validation, logit model correctness, population distribution tests, portfolio composition tests

---

## Section 3: Recommended Approach

### Selected Path: Direct Adjustment

Add 7 new epics to the backlog within the existing project structure. No Phase 1 code changes needed. No rollback. No MVP scope change (MVP is delivered).

### Rationale

- **Zero implementation debt from Phase 1** — clean foundation with proven architecture
- **Architecture survived 10 epics** without fundamental rethinking (Phase 1 retro confirms)
- **Clear dependency chain** — EPIC-11 → 12 → 13 → 14 → 15 → 16 → 17 reduces integration risk
- **Each epic delivers a notebook demo** — continuous validation, GUI epic translates proven workflows into React
- **GUI as final epic** ensures all backend capabilities are proven before UI investment
- **Phase 1 patterns reuse** — frozen dataclasses, Protocol-based interfaces, PyArrow data contracts, structured errors, governance integration — all carry forward

### Effort and Risk

- **Effort:** High — 7 new epics spanning data engineering, statistical methods, behavioral economics, calibration, and full-stack GUI
- **Risk:** Medium — discrete choice and population generation are technically complex, but architectural risk is low (proven extension points)
- **Timeline:** New phase — no sprint plan disruption. Phase 2 is estimated at approximately 2-3x Phase 1 effort given feature complexity.

---

## Section 4: Detailed Change Proposals

### Proposal 1: PRD — Update Phase 2 Feature Table

**Section:** Product Scope → Post-MVP Features → Phase 2 (Growth)

**OLD:**

```
| Feature | Trigger |
|---------|---------|
| Automated sensitivity sweeps | After MVP scenario flows are stable |
| Replication package export | After run-governance schema is validated with external users |
| Reduced-form behavioral module | After static dynamic loop is benchmarked |
| Additional policy templates | After carbon-tax + subsidy templates are externally piloted |
| GUI expansion | After MVP no-code workflow proves analyst value |
| OpenFisca direct API orchestration hardening | After CSV/Parquet contract is stable in production workflows |
| Calibration engine | After benchmark datasets and acceptance tolerances are finalized |
```

**NEW:**

```
| Feature | Trigger | Epic |
|---------|---------|------|
| Realistic population generation library | After Phase 1 data layer is stable | EPIC-11 |
| Policy portfolio model | After template system is proven | EPIC-12 |
| Additional policy templates + extensibility | After portfolio model is stable | EPIC-13 |
| Discrete choice model for household decisions | After population + portfolio foundations exist | EPIC-14 |
| Calibration engine | After discrete choice model is benchmarked | EPIC-15 |
| Replication package export | After governance schema is validated | EPIC-16 |
| GUI showcase product (data fusion + portfolio + simulation + comparison) | After all backend capabilities are proven | EPIC-17 |
```

**Rationale:** Reflects actual Phase 2 scope. "Reduced-form behavioral module" replaced by concrete discrete choice model. Population generation and policy portfolios added as new foundational features. OpenFisca hardening absorbed into EPIC-14. Sensitivity sweeps moved to Phase 3. GUI elevated to showcase product.

### Proposal 2: PRD — Move Sensitivity Sweeps to Phase 3

**Section:** Product Scope → Post-MVP Features → Phase 3 (Expansion)

**OLD:**

```
| Feature | Trigger |
|---------|---------|
| Public-facing web app | Non-technical user access with guardrails |
| Election showcase application | Compare candidate proposals side-by-side |
| Advanced dynamic module | Lifecycle and transition modeling beyond MVP orchestrator |
| Cloud-Scalable Computation | Large Monte Carlo runs |
| Community Template Gallery | Researcher-published reusable model templates |
| Multi-Country Support | Beyond France |
| AI-Assisted Model Building | Interpretation and model construction assistance |
```

**NEW:**

```
| Feature | Trigger |
|---------|---------|
| Automated sensitivity sweeps | After calibration engine and discrete choice are stable |
| Public-facing web app | Non-technical user access with guardrails |
| Election showcase application | Compare candidate proposals side-by-side |
| Advanced dynamic module | Lifecycle and transition modeling beyond MVP orchestrator |
| Cloud-Scalable Computation | Large Monte Carlo runs |
| Community Template Gallery | Researcher-published reusable model templates |
| Multi-Country Support | Beyond France |
| AI-Assisted Model Building | Interpretation and model construction assistance |
```

**Rationale:** Sensitivity sweeps were deprioritized relative to behavioral modeling and population generation. They can naturally build on the calibration engine.

### Proposal 3: PRD — Add Phase 2 Functional Requirements

**Section:** Functional Requirements (new subsections)

**ADD** the following FR groups:

```markdown
### Population Generation & Data Fusion

- FR36: Analyst can download and cache public datasets from institutional sources (INSEE, Eurostat, ADEME, SDES).
- FR37: Analyst can browse available datasets and select which to include in a population.
- FR38: System provides a library of statistical methods for merging datasets that do not share the same sample (uniform distribution, IPF, conditional sampling, statistical matching).
- FR39: Analyst can choose which merge method to apply at each dataset join, with plain-language explanation of the assumption.
- FR40: System produces a complete synthetic population with household-level attributes sufficient for policy simulation (income, household composition, housing, vehicle, heating, energy, geography).
- FR41: Every merge, imputation, and extrapolation is recorded as an explicit assumption in the governance layer.
- FR42: System validates generated populations against known marginal distributions from source data.

### Policy Portfolios

- FR43: Analyst can compose multiple individual policy templates into a named policy portfolio.
- FR44: System executes a simulation with a policy portfolio, applying all bundled policies together.
- FR45: Analyst can compare results across different policy portfolios side-by-side.
- FR46: Analyst can define custom policy templates that participate in portfolios alongside built-in templates.

### Behavioral Responses (Discrete Choice)

- FR47: System models household investment decisions (vehicle, heating, renovation) as discrete choice problems using logit functions.
- FR48: System expands population by alternatives and evaluates each alternative through OpenFisca for household-specific cost calculations.
- FR49: Logit draws use seed-controlled randomness for reproducibility.
- FR50: Panel output records which decision each household made in each domain for each year.
- FR51: Taste parameters (β coefficients) are recorded in run manifests.

### Calibration

- FR52: Analyst can calibrate discrete choice taste parameters against observed transition rates.
- FR53: System validates calibrated parameters against known marginal distributions.

### Replication Package

- FR54: Analyst can export a self-contained replication package including data, configuration, manifests, and results.
- FR55: Replication package is reproducible on a clean environment with only `pip install reformlab` and the package contents.
```

**Rationale:** Phase 2 features need formal functional requirements for traceability and story decomposition.

### Proposal 4: Architecture — Add Phase 2 Extensions Section

**Section:** After "Phase 2+ Architecture Extensions" (currently a brief paragraph)

**OLD:**

```markdown
### Phase 2+ Architecture Extensions

- **Behavioral responses:** New orchestrator step that applies elasticities between yearly computation runs (proven pattern from PolicyEngine).
- **System dynamics bridge:** Aggregate stock-flow outputs derived from microsimulation vintage tracking results.
- **Alternative computation backends:** Swap adapter implementations without changing orchestrator or indicator layers.
```

**NEW:**

```markdown
### Phase 2 Architecture Extensions

#### New Subsystem: Population Generation (`population/`)

```
src/reformlab/population/
├── __init__.py
├── loaders/           ← Institutional data source downloaders/cachers
│   ├── __init__.py
│   ├── base.py        ← DataSourceLoader protocol
│   ├── insee.py       ← INSEE data loader
│   ├── eurostat.py    ← Eurostat data loader
│   ├── ademe.py       ← ADEME energy data loader
│   └── sdes.py        ← SDES vehicle fleet data loader
├── methods/           ← Statistical fusion methods library
│   ├── __init__.py
│   ├── base.py        ← MergeMethod protocol
│   ├── uniform.py     ← Uniform distribution assumption
│   ├── ipf.py         ← Iterative Proportional Fitting
│   ├── conditional.py ← Conditional distribution sampling
│   └── matching.py    ← Statistical matching / data fusion
├── pipeline.py        ← PopulationPipeline builder (compose loaders + methods)
├── assumptions.py     ← Assumption recording for governance integration
└── validation.py      ← Validate against known marginals
```

Design principles:
- Each loader implements `DataSourceLoader` protocol (download, cache, schema-validate, return `pa.Table`)
- Each method implements `MergeMethod` protocol (takes two tables + config, returns merged table + assumption record)
- Pipeline is composable: chain loaders and methods, record every step
- Assumption records integrate with existing governance `capture.py`
- Methods library includes pedagogical docstrings explaining assumptions in plain language

#### Extension: Policy Portfolio Layer (`templates/portfolios/`)

```
src/reformlab/templates/
├── portfolios/
│   ├── __init__.py
│   ├── portfolio.py     ← PolicyPortfolio frozen dataclass (list of policy configs)
│   ├── composition.py   ← Compose templates, validate compatibility, resolve conflicts
│   └── execution.py     ← Execute portfolio through orchestrator (apply all policies per year)
```

Design: A `PolicyPortfolio` is a named, versioned collection of `PolicyConfig` objects. The orchestrator receives a portfolio instead of a single policy, and applies each policy in the portfolio at each yearly step. The scenario registry stores portfolios alongside individual scenarios.

#### New Orchestrator Step: `DiscreteChoiceStep`

Registers as a standard `OrchestratorStep` via existing protocol. Implementation follows the design note:
- Population expansion: clone households × N alternatives, modify attributes per alternative
- OpenFisca batch evaluation: call `adapter.compute()` on expanded population
- Reshape to cost matrix: N households × M alternatives
- Logit probability computation: `P(j|C_i) = exp(V_ij) / Σ_k exp(V_ik)`
- Seed-controlled draw: deterministic choice per household
- State update: modify household attributes + create vintage entries

No changes to `ComputationAdapter` interface or orchestrator core needed.

#### New Subsystem: Calibration (`calibration/`)

```
src/reformlab/calibration/
├── __init__.py
├── engine.py          ← CalibrationEngine (optimize β parameters)
├── targets.py         ← Observed transition rates as calibration targets
├── objective.py       ← Objective function (minimize distance to observed rates)
└── validation.py      ← Validate calibrated parameters against holdout data
```

#### Extension: Server Routes

New API route groups: `/api/populations` (CRUD + generation), `/api/portfolios` (CRUD + composition), `/api/calibration` (run + results). Follow existing pattern from Phase 1 server design.

#### Extension: Frontend

Major new GUI sections:
- Data Fusion Workbench: browse datasets, select merge methods with plain-language explanations, preview populations, validate against marginals
- Policy Portfolio Designer: compose policies, configure parameters per policy, name and version portfolios
- Enhanced Results: persistent simulation results, multi-portfolio comparison, behavioral decision tracking per household

### Phase 3+ Architecture Extensions

- **Automated sensitivity sweeps:** Parameter variation automation over calibrated discrete choice models
- **System dynamics bridge:** Aggregate stock-flow outputs derived from microsimulation vintage tracking results
- **Alternative computation backends:** Swap adapter implementations without changing orchestrator or indicator layers
- **Public-facing web app:** Citizen-facing UI with guided questionnaire and candidate comparison
```

**Rationale:** Phase 2 adds substantial new subsystems. Architecture needs to document them before implementation begins.

### Proposal 5: Epics — Add Phase 2 Epics to epics.md

**Section:** After EPIC-10 in `_bmad-output/planning-artifacts/epics.md`

Add 7 new epic entries. Story-level details will be developed during sprint planning (following Phase 1 pattern where the SM creates story files). The epic-level scope and acceptance criteria are defined here.

*(Full epic definitions included in the Sprint Change Proposal document below)*

### Proposal 6: Sprint Status — Add Phase 2 Entries

**File:** `_bmad-output/implementation-artifacts/sprint-status.yaml`

Add new entries for EPIC-11 through EPIC-17, all with status `backlog`.

### Proposal 7: Project Context — Add Phase 2 Patterns

**File:** `_bmad-output/project-context.md`

Add patterns for:
- Population generation module (DataSourceLoader protocol, MergeMethod protocol)
- Statistical method testing conventions (distribution validation, marginal checks)
- Policy portfolio composition patterns
- Discrete choice model testing (logit correctness, seed reproducibility)

### Proposal 8: Phase 1 Technical Debt Resolution Plan

16 technical debt items carried from Phase 1 retro. Resolution strategy:

| Category | Items | Resolution |
|----------|-------|------------|
| **Absorb into EPIC-11** | TD-07 (single asset class for vintage) | Population generation will define multiple asset classes |
| **Absorb into EPIC-12** | TD-09 (growing IndicatorResult union), TD-04 (templates __init__.py surface) | Portfolio model refactors template API |
| **Absorb into EPIC-14** | TD-05 (shallow state copy), TD-06 (custom callable trust boundary) | Discrete choice stresses state management |
| **Absorb into EPIC-17** | TD-13 (frontend 3 tests), TD-14 (GUI backend wiring prototype) | GUI rebuild addresses both |
| **Fix opportunistically** | TD-01 (pytest ceiling), TD-02 (DecileResults location), TD-03 (registry scan), TD-08 (approximate median), TD-16 (memory heuristic), TD-18 (assert convention), TD-19 (status drift) | Address when touching related code |
| **Monitor** | TD-17 (cross-machine reproducibility) | Replication package epic (EPIC-16) validates this |

---

## Section 5: Implementation Handoff

### Change Scope Classification: Moderate

Phase 2 is a full new phase with 7 epics. This requires backlog creation, artifact updates, and sprint planning — but no code rework or architectural redesign. The existing architecture, patterns, and codebase are the foundation.

### Handoff Plan

| Action | Owner | Priority |
|---|---|---|
| Apply PRD changes (Proposals 1-3) | Dev (Lucas) | After approval |
| Apply Architecture changes (Proposal 4) | Dev (Lucas) | After approval |
| Add Phase 2 epics to epics.md (Proposal 5) | SM (Bob) / Dev (Lucas) | After approval |
| Update sprint-status.yaml (Proposal 6) | SM (Bob) / Dev (Lucas) | After approval |
| Update project-context.md (Proposal 7) | Dev (Lucas) | Before first Phase 2 story |
| Run sprint planning for EPIC-11 | SM (Bob) | After all artifacts updated |
| Create story files for EPIC-11 | SM (Bob) | During sprint planning |

### Success Criteria

- PRD Phase 2 feature table reflects 7 approved features with epic mapping
- Architecture document includes Phase 2 Extensions section with subsystem designs
- `epics.md` contains EPIC-11 through EPIC-17 with acceptance criteria
- `sprint-status.yaml` contains all new epics as `backlog`
- Sprint planning can begin for EPIC-11 immediately after artifacts are updated
- Phase 1 code is untouched — no regressions from artifact updates

### Phase 2 Implementation Principles (Carried from Phase 1 Retro)

1. **Planning quality predicts implementation smoothness** — invest in story specs
2. **Dev Agent Records are mandatory** — enforce from story 1
3. **Spike before hardening** — if a feature area is uncertain, spike first
4. **Adversarial code review on AI-generated work** — continue the practice
5. **Each epic produces a notebook demo** — continuous validation, GUI-ready
6. **Process discipline requires active maintenance** — don't let it decay

---

## Appendix: Phase 2 Epic Definitions

### EPIC-11: Realistic Population Generation Library

**User outcome:** Analyst can build a credible French household population from real public data sources, choosing merge methods with transparent assumptions, and producing a population with all attributes needed for policy simulation.

**Implementation order:** 1 (foundation for all subsequent epics)

**Builds on:** EPIC-1 (data layer, `DatasetManifest`, `DataSourceMetadata`), EPIC-5 (governance, assumption capture)

**Scope:**

- Institutional data source loaders (INSEE, Eurostat, ADEME, SDES) with download/cache
- Statistical methods library: uniform distribution (baseline), IPF, conditional sampling, statistical matching
- Population pipeline builder (compose loaders + methods)
- Assumption recording integrated with governance layer
- Validation against known marginal distributions
- One complete realistic French household example (end-to-end)
- Pedagogical notebook demonstrating the full pipeline with plain-language method explanations
- Plain-language docstrings on every method explaining the assumption in analyst terms

**Epic-Level Acceptance Criteria:**

- At least 4 institutional data source loaders are functional (download, cache, schema-validate)
- At least 3 statistical merge methods are implemented with `MergeMethod` protocol
- The French example pipeline produces a population with at least: household_id, income, household_size, region, housing_type, heating_type, vehicle_type, vehicle_age, energy_consumption, carbon_emissions
- Every merge step records an assumption in the governance layer
- Generated population validates against source marginals within documented tolerances
- Pedagogical notebook runs end-to-end in CI
- Methods library docstrings include plain-language explanations of what each method assumes

---

### EPIC-12: Policy Portfolio Model

**User outcome:** Analyst can compose multiple individual policy templates into a named portfolio and run simulations with bundled policies.

**Implementation order:** 2

**Builds on:** EPIC-2 (scenario templates, registry), EPIC-3 (orchestrator)

**Scope:**

- `PolicyPortfolio` frozen dataclass (named, versioned list of policy configs)
- Portfolio composition logic (validate compatibility, resolve parameter conflicts)
- Orchestrator extension to execute portfolios (apply all policies per year)
- Scenario registry extension to store and version portfolios
- Portfolio comparison (compare results across different bundles)
- Notebook demonstrating portfolio creation, execution, and comparison

**Epic-Level Acceptance Criteria:**

- Analyst can create a portfolio from 2+ individual policy templates
- Orchestrator executes a portfolio, applying all bundled policies at each yearly step
- Portfolio is versioned in the scenario registry
- Portfolio comparison produces side-by-side indicator tables
- Notebook demo runs end-to-end in CI

---

### EPIC-13: Additional Policy Templates + Extensibility

**User outcome:** Analyst can define custom policy templates and use new built-in templates beyond the Phase 1 set, with all templates portfolio-ready.

**Implementation order:** 3

**Builds on:** EPIC-2 (templates), EPIC-12 (portfolios)

**Scope:**

- Custom template authoring API (analyst can define a new policy template in Python or YAML)
- Template validation and registration
- New built-in templates relevant to French environmental policy (to be determined during sprint planning — candidates: vehicle malus, energy poverty aid, building energy performance standards)
- All templates composable into portfolios
- Notebook demonstrating custom template creation and portfolio integration

**Epic-Level Acceptance Criteria:**

- At least 2 new built-in templates are shipped
- Analyst can author a custom template from Python and register it
- Custom templates participate in portfolios alongside built-in templates
- Template schema validation accepts custom templates
- Notebook demo runs end-to-end in CI

---

### EPIC-14: Discrete Choice Model for Household Decisions

**User outcome:** Analyst can run multi-year simulations where households make investment decisions (vehicle, heating, renovation) in response to policy signals, with decisions feeding back into subsequent years.

**Implementation order:** 4

**Builds on:** EPIC-3 (orchestrator, step protocol), EPIC-11 (realistic population with asset attributes), EPIC-12 (policy portfolios for multi-policy cost evaluation)

**Scope:**

- `DiscreteChoiceStep` implementing `OrchestratorStep` protocol
- Population expansion pattern (clone households × alternatives)
- OpenFisca batch evaluation of alternatives via `ComputationAdapter`
- Conditional logit model implementation
- At least 2 decision domains: vehicle investment, heating system
- Seed-controlled logit draws for reproducibility
- Panel output extended with decision records (chosen alternative, probabilities, utilities)
- Taste parameters recorded in run manifests
- Eligibility filtering (only eligible households face choices) for performance
- Notebook demonstrating dynamic behavioral simulation over 10 years

**Reference:** `_bmad-output/planning-artifacts/phase-2-design-note-discrete-choice-household-decisions.md`

**Epic-Level Acceptance Criteria:**

- `DiscreteChoiceStep` registers via standard step protocol without modifying orchestrator core
- Vehicle and heating decision domains produce realistic choice distributions
- 10-year run with 100k households completes within acceptable time on laptop
- Identical seeds produce identical household decisions across runs
- Panel output records every decision for every household every year
- Taste parameters appear in run manifests
- Notebook demo runs end-to-end in CI

---

### EPIC-15: Calibration Engine

**User outcome:** Analyst can calibrate discrete choice taste parameters against observed data so that simulated transition rates match reality.

**Implementation order:** 5

**Builds on:** EPIC-14 (discrete choice model), EPIC-11 (population generation for realistic marginals)

**Scope:**

- Calibration engine (optimize β parameters to minimize distance between simulated and observed transition rates)
- Calibration target definitions (observed vehicle adoption rates, heating system transition rates from public data)
- Objective function design (MSE or likelihood-based)
- Validation against holdout data or known aggregates
- Notebook demonstrating calibration workflow and parameter sensitivity

**Epic-Level Acceptance Criteria:**

- Calibration engine produces β parameters that reduce simulation-vs-observed gap below documented threshold
- Calibrated parameters are reproducible (deterministic optimization)
- Validation step confirms calibrated model on holdout data
- Calibrated parameters are recorded in run manifests
- Notebook demo runs end-to-end in CI

---

### EPIC-16: Replication Package Export

**User outcome:** Researcher can export a self-contained package that reproduces any simulation on a clean environment.

**Implementation order:** 6

**Builds on:** EPIC-5 (governance, manifests), all prior Phase 2 epics

**Scope:**

- Package export API (single command produces a directory/archive with everything needed)
- Package contents: population data or generation config, scenario/portfolio config, template definitions, run manifests, seeds, results
- Package import/replay API (load package, re-execute, verify outputs match)
- Cross-machine reproducibility verification
- Notebook demonstrating export → clean environment → import → verify cycle

**Epic-Level Acceptance Criteria:**

- Export produces a self-contained directory with all artifacts needed for reproduction
- Import on a clean environment with `pip install reformlab` reproduces results within documented tolerances
- Package includes all assumption records from population generation
- Manifest integrity checks pass on reimport
- Notebook demo runs end-to-end in CI

---

### EPIC-17: GUI Showcase Product

**User outcome:** Non-coding analyst can operate the complete Phase 2 workflow through a web GUI: build populations from real data, design policy portfolios, run simulations, browse persistent results, and compare across portfolios.

**Implementation order:** 7 (final — integrates all backend capabilities)

**Builds on:** All Phase 2 epics (P2-1 through P2-6), EPIC-6 (Phase 1 GUI prototype and FastAPI backend)

**Scope:**

- **Data Fusion Workbench:** Browse available datasets, select sources, choose merge methods with plain-language explanations, preview population, validate against marginals
- **Policy Portfolio Designer:** Browse templates, compose portfolios, configure parameters per policy, name and version portfolios
- **Simulation Runner:** Run simulations with configured population + portfolio, show progress, handle errors
- **Persistent Results:** Completed simulations are stored and browsable — no need to re-run
- **Comparison Dashboard:** Side-by-side comparison across policy portfolios with distributional, welfare, and fiscal indicators
- **Behavioral Decision Viewer:** Explore household decisions from discrete choice model (who switched vehicles, by decile, by year)
- Extends Phase 1 FastAPI backend with new routes for all Phase 2 capabilities
- React + TypeScript + Shadcn/ui + Tailwind v4 (same stack as Phase 1 prototype)

**Epic-Level Acceptance Criteria:**

- Analyst can build a population from real data sources through the GUI without writing code
- Analyst can compose and run a policy portfolio through the GUI
- Completed simulation results persist across browser sessions
- Analyst can compare multiple portfolio results side-by-side
- GUI displays behavioral decision outcomes (discrete choice results) per household group
- All GUI operations map to API endpoints tested independently
- Frontend tests cover core workflows (data fusion, portfolio creation, simulation, comparison)
