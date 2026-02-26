---
stepsCompleted:
  - step-01-init
  - step-02-discovery
  - step-02b-vision
  - step-02c-executive-summary
  - step-03-success
  - step-04-journeys
  - step-05-domain
  - step-06-innovation
  - step-07-project-type
  - step-08-scoping
  - step-09-functional
  - step-10-nonfunctional
  - step-01b-continue
  - step-11-polish
  - step-12-complete
inputDocuments:
  - _bmad-output/planning-artifacts/product-brief-ReformLab-2026-02-23.md
  - _bmad-output/planning-artifacts/research/domain-generic-microsimulation-frameworks-research-2026-02-23.md
  - _bmad-output/planning-artifacts/research/technical-entity-graph-data-modeling-and-vectorized-simulation-engines-research-2026-02-23.md
  - _bmad-output/brainstorming/brainstorming-session-2026-02-23.md
workflowType: 'prd'
documentCounts:
  briefs: 1
  research: 2
  brainstorming: 1
  projectDocs: 0
classification:
  projectType: developer_tool
  domain: scientific
  complexity: high
  projectContext: greenfield
---

# Product Requirements Document - ReformLab

**Author:** Lucas
**Date:** 2026-02-24

## Strategic Direction Update (2026-02-25)

This PRD follows an **OpenFisca-first platform strategy**.

- **OpenFisca is the tax-benefit computation backend**, accessed through a clean adapter interface (`ComputationAdapter`). No custom policy engine, formula compiler, or entity graph engine will be built.
- **The dynamic orchestrator is the core product.** It manages multi-year projections by executing a pluggable step pipeline between yearly OpenFisca computations: vintage transitions, state carry-forward, and (Phase 2) behavioral response adjustments.
- **Open-data-first:** The platform works out of the box with public data (synthetic populations, emission factors). Custom data is optional.
- ReformLab provides the end-to-end environmental policy assessment experience: data preparation, scenario templates, dynamic orchestration with vintage tracking, indicators, governance, and user interfaces.
- The adapter pattern ensures the platform is not locked to OpenFisca — computation backends can be swapped without changing the orchestration layer.
- Endogenous market-clearing and physical system feedback loops are explicitly out of MVP scope.

If a statement elsewhere implies "new core simulation engine replacing OpenFisca," this section supersedes it.

## Executive Summary

ReformLab is an OpenFisca-first policy analysis platform for environmental and distributional assessment. Instead of rebuilding a microsimulation core, it turns OpenFisca outputs plus external data into a single operational workflow: ingest and harmonize data, define environmental policy scenarios, run multi-year projections, track assumptions, and produce decision-ready indicators.

The target users are analysts and researchers already chaining scripts and tools for carbon-tax and subsidy analysis. The product promise is speed and trust: reusable templates, deterministic scenario execution, ten-year projection support through iterative orchestration, and full run provenance. MVP validates the approach with French household carbon-tax and redistribution scenarios while preserving full compatibility with OpenFisca.

Built by a domain expert with AI-assisted execution, the immediate objective is practical: make policy-grade environmental assessment reproducible and fast without waiting for a new engine ecosystem to emerge.

### What Makes This Special

**Speed-to-decision is the core value.** Configure a carbon-tax scenario, run baseline vs reform over multiple years, and get distributional and welfare indicators in minutes instead of weeks of manual stitching.

**OpenFisca-first architecture is the strategic choice.** Reuse mature tax-benefit policy logic, then layer environmental modeling, orchestration, and indicators on top.

**Assumption transparency is built-in, not aspirational.** Every dataset, parameter, scenario, and run configuration is tracked with reproducible manifests.

**Open-data-first adoption remains key.** Synthetic populations and public datasets enable immediate use; restricted microdata is optional.

## Project Classification

| Dimension | Value |
|-----------|-------|
| **Project Type** | OpenFisca-centered policy analysis product (Python + notebook + no-code UI) |
| **Domain** | Environmental and distributional policy simulation |
| **Complexity** | High — multi-source data engineering, dynamic orchestration, reproducibility governance, multi-persona UX |
| **Project Context** | Greenfield product layer on top of mature open-source core |

## Success Criteria

### User Success

- **Time-to-first-result:** New user installs via pip, runs the carbon tax example, and sees distributional charts in under 30 minutes
- **Complete analysis in a single run:** One command produces welfare effects, fiscal cost, and distributional impact in notebook outputs — ready for analysis without post-processing
- **Full assumption traceability:** Every simulation run produces an immutable manifest documenting all parameters, data sources, and assumptions — reproducibility by default
- **Policy correctness:** Simulation results match known policy outcomes and published benchmarks (e.g., known carbon tax revenue, distributional patterns from academic literature) within defined tolerance

### Business Success

Since ReformLab is an open-source project, "business" success means adoption, credibility, and real-world policy impact.

| Objective | 12-Month Target |
| --- | --- |
| **Government adoption** | At least 1 evaluation team in French/EU public administration actively using the framework |
| **Correctness credibility** | Validation suite covering the carbon tax domain; results independently reproducible |
| **Research adoption** | At least 1 published paper or working paper using ReformLab |
| **Ecosystem seeding** | Carbon tax MVP fully functional with 4-5 redistribution scenario templates |

### Technical Success

- **Deterministic execution:** Identical inputs always produce identical outputs across runs and environments
- **Vectorized performance:** Full population simulation (100k+ households) completes in seconds, not minutes
- **Assumption traceability:** Every simulation run produces an immutable manifest — data sources, parameters, assumptions, engine version — with zero manual documentation effort
- **Open-data default:** Framework is fully functional using only publicly available data; no restricted microdata required for any core workflow

### Measurable Outcomes

| Metric | Target | Measurement |
| --- | --- | --- |
| Time from install to first meaningful output | < 30 minutes | Tested with new users unfamiliar with the framework |
| Validation benchmark pass rate | 100% on core benchmarks before any public release | Automated test suite against reference datasets |
| Analysis completeness | Single run produces distributional, welfare, and fiscal cost outputs | Automated check on notebook outputs |
| Run manifest generation | 100% of simulation runs produce complete manifests | Automated verification |

## Product Scope

### MVP Strategy & Philosophy

**MVP Approach:** Problem-solving MVP — prove that an OpenFisca-first stack with dedicated product layers can deliver environmental policy assessment faster and with higher reproducibility than ad-hoc tool chains.

**Resource Reality:** Solo developer with AI assistance. Sequence for leverage: avoid rebuilding policy-calculation internals, build only differentiated layers.

**Architectural Bet:** The differentiation is orchestration and product UX, not core tax-benefit computation. OpenFisca integration is first-class from day one.

### MVP Feature Set (Phase 1)

**Core User Journeys Supported:**
- Alex (First-Time Installer) — pip install → quickstart notebook → carbon tax charts in 15 minutes
- Sophie (Policy Analyst) — YAML policy definition → scenario comparison → distributional analysis in notebooks
- Marco (Researcher) — Python API → Jupyter workflow → reproducible results via run manifests

**Must-Have Capabilities:**

| # | Capability | Justification |
|---|-----------|---------------|
| 1 | OpenFisca Integration Layer | Treat OpenFisca outputs/API as canonical baseline for tax-benefit calculations |
| 2 | Data Ingestion and Harmonization | Ingest OpenFisca outputs, synthetic populations, and environmental datasets into a consistent analytical model |
| 3 | Environmental Policy Template Library | Carbon tax, targeted rebates, subsidy/feebate templates reusable across scenarios |
| 4 | Dynamic Orchestrator | Multi-year (10+ year) iterative simulation runner with explicit yearly state transitions |
| 5 | Vintage Tracking Module | Track cohort/asset vintages (e.g., heating systems, vehicles) through time |
| 6 | Indicator and Analysis Layer | Distributional, welfare, fiscal, and policy-performance indicators |
| 7 | Assumption Logging & Run Manifests | Immutable run-level provenance across datasets, templates, parameters, and code versions |
| 8 | Scenario Registry & Comparison | Versioned baseline/reform scenarios with side-by-side comparison workflows |
| 9 | Python API + Notebook Workflow | Research-grade programmability for advanced users |
| 10 | Early No-Code GUI | Fast scenario setup, launch, and comparison for non-coding policy analysts |

**Explicitly Deferred from MVP:**
- Endogenous market-clearing models
- Physical system feedback loops (energy/climate stock-flow models)
- Full behavioral equilibrium modeling
- Fully automated report authoring pipeline
- Advanced policy-rule authoring beyond template-driven workflows

### Post-MVP Features

**Phase 2 (Growth):**

| Feature | Trigger |
|---------|---------|
| Automated sensitivity sweeps | After MVP scenario flows are stable |
| Replication package export | After run-governance schema is validated with external users |
| Reduced-form behavioral module | After static dynamic loop is benchmarked |
| Additional policy templates | After carbon-tax + subsidy templates are externally piloted |
| GUI expansion | After MVP no-code workflow proves analyst value |
| OpenFisca direct API orchestration hardening | After CSV/Parquet contract is stable in production workflows |
| Calibration engine | After benchmark datasets and acceptance tolerances are finalized |

**Phase 3 (Expansion):**

| Feature | Trigger |
|---------|---------|
| Public-facing web app | Non-technical user access with guardrails |
| Election showcase application | Compare candidate proposals side-by-side |
| Advanced dynamic module | Lifecycle and transition modeling beyond MVP orchestrator |
| Cloud-Scalable Computation | Large Monte Carlo runs |
| Community Template Gallery | Researcher-published reusable model templates |
| Multi-Country Support | Beyond France |
| AI-Assisted Model Building | Interpretation and model construction assistance |

### Risk Mitigation Strategy

**Technical Risks:**

| Risk | Mitigation |
|------|-----------|
| OpenFisca contract drift (outputs/API changes) | Version-pinned adapters, contract tests, and compatibility matrix by OpenFisca version |
| Dynamic orchestration complexity | Start with deterministic yearly loop + explicit state schema before adding behavioral layers |
| Data harmonization fragility | Canonical schema contracts and validation at every ingestion boundary |

**Market Risks:**

| Risk | Mitigation |
|------|-----------|
| Overlap with PolicyEngine positioning | Focus on environmental policy templates, dynamic vintage effects, and analyst workflow governance |
| Researchers don't trust orchestration results | Publish benchmark packs and scenario traceability evidence |
| No adoption beyond creator | Secure one ministry/lab pilot with real policy question and documented outcomes |

**Resource Risks:**

| Risk | Mitigation |
|------|-----------|
| Solo development stalls or scope overwhelms | Ruthless Phase 1 focus on 10 must-have capabilities; defer everything else |
| AI-assisted development hits limits on complex architectural decisions | Entity graph and engine architecture designed upfront with clear interfaces; AI assists on implementation, human decides architecture |
| MVP takes too long to reach external validation | Go/no-go checkpoint: at least 1 external user runs carbon tax model before starting Phase 2 |

## User Journeys

### Journey 1: First-Time Installer — "Alex"

**Profile:** Alex is a PhD student in environmental economics at Sciences Po. He's seen ReformLab mentioned in a conference talk and wants to evaluate whether it's worth using for his dissertation on carbon tax incidence. He's comfortable with Python but has never used a microsimulation framework.

**Opening Scene:** Alex finds the PyPI page after a quick search. He's skeptical — he's tried OpenFisca before and gave up after two hours of configuration. He has 30 minutes before his next seminar.

**Rising Action:** `pip install reformlab` works cleanly. He opens the quickstart notebook linked in the README. The first cell loads a pre-configured carbon tax scenario on synthetic French households. He runs it — distributional charts by income decile appear in seconds. He modifies the tax rate from €44/tCO2 to €100/tCO2, re-runs. The charts update. He switches the redistribution scenario from flat dividend to progressive rebate. New charts, new winners/losers table, all in the same notebook.

**Climax:** Alex realizes he just did in 15 minutes what took him three weeks of ad-hoc scripting last semester — and the results come with full methodology documentation he didn't have to write.

**Resolution:** He bookmarks the API docs, forks the carbon tax example into his dissertation project folder, and starts thinking about how to extend the entity model with vehicle ownership data. He's hooked.

**Requirements revealed:** Frictionless pip install, working quickstart example, pre-loaded synthetic data, instant visual output, clear extension path from examples to custom models.

---

### Journey 2: Sophie — Policy Analyst at French Ministry

**Profile:** Sophie works in the evaluation department of the Ministry of Ecological Transition. She evaluates proposed environmental policies and produces briefing-ready analysis. She's comfortable with Python but frustrated by rebuilding infrastructure for every assessment.

**Opening Scene:** Sophie's director asks for a distributional impact assessment of a proposed carbon tax reform with three redistribution options — due in two weeks. Normally this means: pull the latest INSEE data, chain OpenFisca for income effects, write custom scripts for energy consumption, build Excel charts, and manually document methodology. She's done this five times and dreads it.

**Rising Action:** Sophie opens ReformLab, copies the carbon tax template YAML, and adjusts the parameters to match the proposed reform: tax rate, energy categories, exemptions. She defines the three redistribution scenarios as YAML diffs against the baseline. She points the framework at the synthetic French population (already built-in) and runs all three scenarios.

**Climax:** Within an hour, Sophie has distributional impact charts by income decile for all three scenarios, a winners/losers table, and fiscal cost estimates in her notebook workflow. She runs manual parameter variations (for example, tax rate ±20%) by editing YAML and rerunning. The methodology trail is already documented through run manifests.

**Resolution:** The director gets the briefing a week early. When a colleague questions an assumption about energy consumption by income group, Sophie opens the assumption log, shows the exact distributional assumption used, and re-runs with an alternative assumption in five minutes. She becomes the department's go-to person for policy assessment and starts customizing templates for recurring evaluations.

**Requirements revealed:** YAML policy definition with reform-as-diff, multiple scenario comparison, built-in synthetic population, assumption logging via run manifests, assumption swappability, and fast rerun workflow from notebooks.

---

### Journey 3: Marco — Academic Researcher

**Profile:** Marco is a labor and environmental economist. He's estimated energy demand elasticities by income group using French household survey data. Now he needs to show the distributional effect of a carbon tax with progressive redistribution for a journal submission.

**Opening Scene:** Marco has a set of estimated elasticities in a CSV file from his Stata analysis. He needs a microsimulation layer to compute distributional impacts. Last time, he wrote 800 lines of custom NumPy code that took a month, produced results he couldn't easily replicate, and generated a replication package his co-author couldn't run.

**Rising Action:** Marco opens a Jupyter notebook with the ReformLab carbon tax template. He loads the built-in synthetic French population, defines his carbon tax reform in YAML, and — crucially — his elasticities aren't needed for the MVP (behavioral responses are Phase 2). But the static simulation already gives him the mechanical distributional impact. He runs the simulation and gets distributional charts with deterministic run manifests for reproducibility.

**Climax:** Marco shares the YAML configuration, notebook, and run manifest with his co-author. The co-author reruns the analysis in a clean environment and gets matching outputs because assumptions, parameters, and engine context are pinned.

**Resolution:** Marco includes the ReformLab results in his paper's simulation section. When Phase 2 adds replication package export and behavioral responses, he'll use those for journal appendices and elasticity integration. Even the Phase 1 static results are publishable and credible, so he starts planning an energy poverty template contribution.

**Requirements revealed:** Jupyter notebook workflow, Python API, static simulation as credible standalone output, run-manifest-based cross-machine reproducibility, and clear extension points for future behavioral and replication features.

---

### Journey 4: Claire — Engaged Citizen (Vision / Post-MVP)

**Profile:** Claire is a French teacher, 32, politically engaged. She wants to understand how proposed environmental policies would affect her household and others like hers. She doesn't code.

**Opening Scene:** Before municipal or national elections, Claire sees a link shared on social media: "Compare candidates' carbon tax proposals — see who wins, who loses." She clicks through to a web application built on the ReformLab framework.

**Rising Action:** Claire answers a short questionnaire: monthly household income, region, housing type (apartment, gas heating), commuting pattern (15km by car), household composition. The app builds her household profile and runs pre-configured simulations for each candidate's environmental proposal.

**Climax:** Claire sees: "Under Candidate A's carbon tax, your household pays €340/year more in energy costs but receives €420 in carbon dividends — net gain €80. Under Candidate B's approach, you pay €280 more but receive no rebate." She also sees the distributional picture: income decile 1 gains under both proposals, decile 10 loses under both, but the magnitude differs. She switches to "People Like Me" view and sees how households with her profile compare to the national average.

**Resolution:** Claire shares the comparison with friends. She returns before the election with updated proposals. She doesn't know she's using a microsimulation framework — she just knows she finally understands who wins and who loses.

**Requirements revealed (Vision):** Web UI with guided questionnaire, pre-configured policy scenarios, household profile builder, candidate comparison dashboard, "People Like Me" contextual view, accessible non-technical language, social sharing.

---

### Journey Requirements Summary

| Journey | User Type | MVP Scope | Key Capabilities Required |
| --- | --- | --- | --- |
| Alex (First-Time Installer) | Evaluator / new user | MVP | pip install, quickstart example, pre-loaded data, instant visual output |
| Sophie (Policy Analyst) | Primary — YAML workflow | MVP | YAML policy-as-code, scenario comparison, assumption logging, notebook outputs, manual parameter reruns |
| Marco (Researcher) | Primary — Python API | MVP | Jupyter notebook, Python API, run-manifest reproducibility, extension points for behavioral modeling |
| Claire (Citizen) | Secondary — web consumer | Vision | Web UI, guided questionnaire, candidate comparison, accessible language |

**Core capability overlap across MVP journeys:** Synthetic population, distributional analysis, assumption transparency, run manifests, YAML configuration, Python API.

**Phase 2 capability targets across journeys:** report generation (HTML + DOCX), automated sensitivity analysis, and one-command replication package export.

## Domain-Specific Requirements

### Scientific Rigor & Validation

- **Deterministic reproducibility:** Identical inputs must produce bit-identical outputs across runs, machines, and OS versions. Random seeds must be explicit and pinned.
- **Benchmark validation:** Carbon tax MVP must validate against published reference results — known aggregate revenue estimates and distributional patterns from academic literature (e.g., published carbon tax incidence studies for France).
- **Three-layer validation program:** Formula-level unit tests, policy-regression tests (golden outputs), and cross-model benchmark tests against established tools where overlapping results exist.
- **Statistical validity:** Synthetic population generation methods must produce populations that match known marginal distributions within documented tolerances. Deviations must be reported, not hidden.

### Data Governance & Privacy

- **Open-data default:** MVP operates entirely on publicly available data (INSEE published tables, Eurostat public marginals). No restricted microdata dependency for any core workflow.
- **Real microdata support:** When users supply restricted microdata (EU-SILC, national surveys), the framework must never persist, copy, or transmit the data beyond the user's local environment. Input data paths are referenced, not embedded.
- **Assumption provenance:** Every distributional assumption in synthetic population generation is logged with its source, method, and alternatives considered. No hidden defaults.

### Reproducibility & Auditability

- **Immutable run manifests:** Every simulation run produces a manifest: engine version, dependency versions, input data hashes, all parameters, all assumptions, timestamp. Manifests are append-only and tamper-evident.
- **Replication package standard:** Exported packages must be self-contained and reproducible on a clean environment with only `pip install reformlab` and the package contents.
- **Version-pinned results:** Results are tied to specific engine version + data version + parameter version. Upgrading any component produces a clear diff, not silent changes.

### Computational Performance

- **Vectorized execution contract:** All core simulation operations must operate on population-scale arrays (NumPy/Arrow), not row-by-row loops. Performance target: 100k+ households in seconds.
- **Memory management:** Framework must handle populations up to 500k households on a standard laptop (16GB RAM). Larger populations should degrade gracefully with clear memory warnings, not crashes.
- **Deterministic period semantics:** Annual snapshot computation with explicit period handling. No implicit temporal assumptions.

### Domain Integration Patterns

- **Data format interoperability:** Input via CSV and Parquet. Output via CSV, Parquet, and Arrow for downstream analytics. YAML for policy definitions.
- **Notebook-first research workflow:** Jupyter notebook is a first-class interface, not an afterthought. All API operations must work cleanly in notebook cells with sensible display representations.
- **No vendor lock-in:** Framework must remain independent of any cloud provider, data vendor, or institutional infrastructure. Pure Python with standard scientific stack dependencies (NumPy, pandas/Polars, matplotlib).

### Risk Mitigations

Risks and mitigations are consolidated in **Product Scope → Risk Mitigation Strategy** to keep one authoritative risk register for this PRD.

## Innovation & Novel Patterns

### Detected Innovation Areas

**1. Step-Pluggable Dynamic Orchestrator (Core Differentiator)**

The dynamic orchestrator is the product's central innovation. It manages multi-year policy projections by executing a pipeline of pluggable steps between yearly OpenFisca computations: vintage transitions, state carry-forward, and (Phase 2) behavioral response adjustments. No existing open-source tool offers this for environmental policy assessment. OpenFisca computes static snapshots; ReformLab turns them into dynamic projections.

**2. OpenFisca-First Environmental Product Layer (Strategic Positioning)**

ReformLab does not replace OpenFisca. It delegates all tax-benefit computation to OpenFisca through a clean adapter interface, then layers environmental policy orchestration, vintage tracking, and governance on top. The adapter pattern ensures the platform is not locked to a single computation backend.

**3. Template-Driven Policy Modeling (Operational DSL)**

Environmental policy templates (carbon tax, subsidies, rebates, feebates) are encoded as reusable scenario artifacts, enabling analysts to run credible comparisons without writing low-level model code.

**4. Assumption-Transparent Governance (Process Innovation)**

Every run is fully auditable: inputs, mappings, parameters, scenario versions, and outputs are logged and reproducible. This shifts trust from informal scripts to governed simulation workflows.

**5. Microsimulation-to-System-Dynamics Bridge (Strategic Vision)**

The vintage tracking module produces aggregate stock trajectories (fleet turnover, heating system transitions) as a natural byproduct of household-level simulation. This creates a bridge between microsimulation (who wins/loses) and system dynamics (macro emission trajectories) — two approaches that are typically siloed in separate teams and models. Phase 3 target.

### OpenFisca/PolicyEngine Interoperability Strategy

ReformLab does not aim to replace OpenFisca or PolicyEngine for tax-benefit legislation encoding. It treats OpenFisca as the core computational layer and focuses on differentiated workflow layers:

- **Canonical workflow:** OpenFisca baseline (tax-benefit + income) -> ReformLab data harmonization -> environmental policy templates -> dynamic multi-year loop with vintage updates -> distributional/welfare/fiscal indicators.
- **What this unlocks:** Analysts can evaluate environmental policy incidence over time without rebuilding tax-benefit rules.
- **MVP scope:** CSV/Parquet ingestion and versioned mapping of OpenFisca outputs, with optional direct API orchestration in controlled workflows.
- **Growth phase:** Stronger API coupling, richer template ecosystem, and optional connectors to external physical or macro modules.
- **Strategic positioning:** OpenFisca for core policy formulas, ReformLab for environmental scenario operations.

### Market Context & Competitive Landscape

Research confirms no existing platform combines this exact package for the target use case:
- **LIAM2** (generic microsimulation) is explicitly discontinued
- **OpenM++** core repository is archived/read-only as of February 2026
- **OpenFisca** remains strongest as a legislative microsimulation core, not as an environmental workflow product
- **EUROMOD** is institutional EU-focused with C#/Windows architecture
- **PolicyEngine** emphasizes public-facing tax-benefit delivery and reform tooling

The technical ecosystem is moving toward composable stacks. The opportunity is to specialize those stacks for environmental policy operations rather than build another general-purpose core engine.

### Validation Approach

| Innovation | Validation Method |
| --- | --- |
| OpenFisca integration robustness | Baseline scenarios reproduce expected OpenFisca outputs within defined tolerance and mapping checks |
| Template usability | Analysts can modify template parameters and run scenario comparisons without coding |
| Dynamic projection credibility | 10-year run with explicit vintage state transitions passes deterministic regression tests |
| Assumption transparency | Independent reproduction using run manifest and scenario registry succeeds on another machine |
| Synthetic population viability | Synthetic population validated against known marginals and benchmark distributions |

### Risk Mitigation

Innovation-related risks and fallbacks are tracked in **Product Scope → Risk Mitigation Strategy** with technical, market, and resource coverage.

## Developer Tool Specific Requirements

### Project-Type Overview

ReformLab is a Python library distributed via PyPI (`pip install reformlab`) with a heavier default install that includes all analytical and visualization dependencies out of the box. The framework exposes two complementary interfaces: YAML configuration for policy analysts and a full Python API for researchers working in Jupyter notebooks. No IDE integration or language server needed — this is a scientific computing library, not a developer productivity tool.

### Installation & Distribution

- **Primary distribution:** PyPI via `pip install reformlab` — single command, all dependencies included
- **Python version:** Latest stable Python (3.13+). No backward compatibility burden — users in this domain typically manage their own environments
- **Dependency philosophy:** Batteries-included default install. MVP ships core + analytics + visualization (NumPy, pandas/Polars, matplotlib, PyArrow). Report-templating dependencies (Jinja2, python-docx) are introduced with Phase 2 report generation.
- **Conda:** Future consideration, not MVP priority. Many researchers use conda environments but pip-in-conda works fine
- **Standalone executable:** Feasible via PyInstaller/Nuitka if needed for government environments without Python — post-MVP consideration

### API Surface

**Python API (programmatic interface):**

- Population data loading and preparation
- OpenFisca adapter configuration and execution
- Scenario template configuration and comparison
- Dynamic orchestration (multi-year runs with vintage tracking)
- Analytical operations (distributional analysis, welfare, fiscal cost; manual parameter reruns in MVP)
- Report generation and replication package export (Phase 2)
- All objects have sensible `__repr__` for notebook display

**YAML Configuration (declarative interface):**

- Scenario template definitions (carbon tax rates, redistribution parameters)
- Reform definitions as parameter overrides against baseline
- Orchestrator configuration (projection horizon, transition rules, step pipeline)
- Population and data source configuration
- OpenFisca adapter settings (version pin, input/output mappings)

**YAML schema must be:**

- Fully documented with a JSON Schema / YAML schema reference
- Validated on load with clear error messages pointing to the exact line/field
- Versionable — schema version in every YAML file for forward compatibility

### Documentation Strategy

**MVP documentation set:**

| Document | Purpose | Audience |
| --- | --- | --- |
| README + Quickstart | 5-minute overview and first run | Alex (evaluator) |
| Installation guide | Environment setup, dependency details | All |
| Carbon tax tutorial | Step-by-step walkthrough of the MVP model | Sophie, Marco |
| YAML reference | Complete schema documentation for policy-as-code | Sophie |
| Python API reference | Auto-generated from docstrings | Marco |
| Entity graph guide | How to define entities, relationships, and attributes | Marco, advanced Sophie |
| Assumptions guide | How assumption logging works, how to swap assumptions | All |
| Example notebooks | 4-5 carbon tax redistribution scenarios as runnable notebooks | All |

**Documentation principles:**

- Docs live in the repository, versioned with the code
- Every public API function has a docstring with at least one example
- YAML examples are tested (CI runs them to prevent doc drift)
- Tutorial guide designed to also work as the foundation for future web UI onboarding

### Code Examples & Templates

**Shipped with the package:**

- `examples/carbon_tax/` — Complete carbon tax model with 4-5 redistribution YAML templates
- `examples/quickstart.ipynb` — The 15-minute notebook from Alex's journey
- `examples/researcher_workflow.ipynb` — Marco's notebook with API usage, scenario comparison, and run-manifest reproducibility
- `examples/openfisca_integration/` — Importing OpenFisca outputs and layering energy policy

**Example quality bar:**

- Every example runs end-to-end without modification on a fresh install
- Examples produce visual output (charts) by default
- Examples are tested in CI

### Implementation Considerations

**Build & release:**

- Standard Python packaging (pyproject.toml, setuptools or hatch)
- Automated release to PyPI via CI/CD (GitHub Actions)
- Semantic versioning — breaking changes only on major versions
- Pinned dependency ranges for reproducibility

**Testing strategy:**

- pytest-based test suite
- OpenFisca adapter contract tests (input/output mapping validation)
- Orchestrator determinism tests (multi-year runs with fixed seeds)
- Vintage transition regression tests (asset cohort state over time)
- Golden output regression tests for the carbon tax model
- CI runs all examples as integration tests
- Coverage target: high for adapter contracts, orchestrator logic, vintage transitions, and template correctness

**Migration guide (future):**

- Not needed for MVP (no users to migrate)
- Post-MVP: guide for OpenFisca users wanting to extend their workflow with environmental templates and dynamic scenario operations

## Functional Requirements

### OpenFisca Integration & Data Foundation

- FR1: Analyst can ingest OpenFisca household-level outputs from CSV or Parquet.
- FR2: System can optionally execute OpenFisca runs through a version-pinned API adapter.
- FR3: Analyst can map OpenFisca variables to project schema fields through configuration.
- FR4: System validates mapping/schema contracts with clear field-level errors.
- FR5: Analyst can load synthetic populations and external environmental datasets (for example, energy consumption or emissions factors).
- FR6: System records data source metadata and hashes for every run.

### Scenario & Template Layer

- FR7: Analyst can load prebuilt environmental policy templates (carbon tax, subsidy, rebate, feebate).
- FR8: Analyst can define reforms as parameter overrides to a baseline scenario.
- FR9: System stores versioned scenario definitions in a scenario registry.
- FR10: Analyst can run multiple scenarios in one batch for comparison.
- FR11: Analyst can compose tax-benefit baseline outputs with environmental template logic in one workflow.
- FR12: Scenario configuration supports year-indexed policy schedules for at least ten years.

### Dynamic Orchestration & Vintage Tracking

- FR13: System can execute iterative yearly simulations for 10+ years.
- FR14: System can carry forward state variables between yearly iterations.
- FR15: System can track asset/cohort vintages (for example, vehicle/heating cohorts) by year.
- FR16: Analyst can configure transition rules for state updates between years.
- FR17: System enforces deterministic sequencing and explicit random-seed control in dynamic runs.
- FR18: System outputs year-by-year panel results for each scenario.

### Indicators & Analysis

- FR19: Analyst can compute distributional indicators by income decile.
- FR20: Analyst can compute indicators by geography (region and related groupings).
- FR21: Analyst can compute welfare indicators including winners/losers counts and net gains/losses.
- FR22: Analyst can compute fiscal indicators (revenues, costs, balances) per year and cumulatively.
- FR23: Analyst can define custom indicators as derived formulas over run outputs.
- FR24: Analyst can compare indicators across scenarios side-by-side.

### Governance & Reproducibility

- FR25: System automatically generates immutable run manifests including versions, hashes, parameters, and assumptions.
- FR26: Analyst can inspect assumptions and mappings used in any run.
- FR27: System emits warnings for unvalidated templates, mappings, or unsupported run configurations.
- FR28: Results are pinned to scenario version, data version, and OpenFisca adapter/version.
- FR29: System maintains run lineage across yearly iterations and scenario variants.

### User Interfaces & Workflow

- FR30: User can run full workflows from a Python API in notebooks.
- FR31: User can configure workflows with YAML/JSON files for analyst-friendly version control.
- FR32: User can use an early no-code GUI to create, clone, and run scenarios.
- FR33: User can export tables and indicators in CSV/Parquet for downstream reporting.

### Documentation & Enablement

- FR34: User can run an OpenFisca-plus-environment quickstart in under 30 minutes.
- FR35: User can access template authoring and dynamic-run documentation with reproducible examples.

## Non-Functional Requirements

### Performance

- NFR1: Full population simulation (100,000 households) completes in under 10 seconds on a standard laptop (4-core, 16GB RAM)
- NFR2: All orchestration hot paths use vectorized array computation where feasible; no row-by-row loops in core aggregation/calculation paths
- NFR3: Framework handles populations up to 500,000 households on 16GB RAM without crashing; larger populations produce a clear memory warning before attempting execution
- NFR4: YAML configuration loading and validation completes in under 1 second for typical policy definitions
- NFR5: Analytical operations (distributional analysis, welfare computation, fiscal cost) execute in under 5 seconds for 100,000 households

### Reproducibility & Determinism

- NFR6: Identical inputs produce bit-identical outputs across runs on the same machine
- NFR7: Identical inputs produce identical outputs across different machines and operating systems (Python version and dependency versions held constant)
- NFR8: Random seeds used in synthetic population generation are explicit, pinned, and recorded in the run manifest
- NFR9: Run manifests are generated automatically with zero manual effort from the user
- NFR10: No implicit temporal assumptions — all period semantics are explicit in configuration

### Data Privacy

- NFR11: When users supply restricted microdata, the framework never persists, copies, or transmits data beyond the user's local environment
- NFR12: Input data paths are referenced in run manifests, not embedded — no raw data in manifests or logs
- NFR13: No telemetry, analytics, or network calls from the framework — fully offline operation

### Integration & Interoperability

- NFR14: CSV and Parquet files are supported for all data input and output operations
- NFR15: OpenFisca integration supports both import contracts (CSV/Parquet) and version-pinned API orchestration modes
- NFR16: All Python API objects have sensible `__repr__` for Jupyter notebook display
- NFR17: Framework has zero dependency on cloud providers, data vendors, or institutional infrastructure

### Code Quality & Maintainability

- NFR18: pytest test suite with high coverage on adapters, orchestration, template logic, and simulation runner
- NFR19: All shipped examples run end-to-end without modification on a fresh install (tested in CI)
- NFR20: YAML examples are tested in CI to prevent documentation drift
- NFR21: Semantic versioning — breaking changes only on major versions
