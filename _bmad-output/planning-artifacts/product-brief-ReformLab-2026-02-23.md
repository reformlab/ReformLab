stepsCompleted: [1, 2, 3, 4, 5, 6]
lastStep: 6
workflow_completed: true
inputDocuments:
  - _bmad-output/brainstorming/brainstorming-session-2026-02-23.md
  - _bmad-output/planning-artifacts/research/domain-generic-microsimulation-frameworks-research-2026-02-23.md
  - _bmad-output/planning-artifacts/research/technical-entity-graph-data-modeling-and-vectorized-simulation-engines-research-2026-02-23.md
date: 2026-02-23
author: Lucas
---

# Product Brief: ReformLab

## Strategic Direction Update (2026-02-24)

This brief is updated to reflect the current product decision:

- OpenFisca is the core policy-calculation engine.
- ReformLab focuses on differentiated layers: data collection/manipulation, environmental templates, dynamic year-by-year orchestration with vintage tracking, run governance, and a no-code workflow.
- Building a replacement core microsimulation engine is out of MVP scope.

## Executive Summary

ReformLab is an OpenFisca-first environmental policy analysis product. It addresses the operational gap between policy-calculation outputs and decision-ready environmental analysis by adding data harmonization, scenario templates, dynamic projection, and reproducibility governance.

Built by a domain expert with AI-assisted execution, the product targets policy analysts and researchers who need ten-year scenario projections, subsidy modeling, welfare indicators, and transparent run tracking without rebuilding tax-benefit logic.

---

## Core Vision

### Problem Statement

Microsimulation is essential for rigorous policy assessment, but most teams still hand-stitch datasets and scripts around baseline tax-benefit outputs. The key gap is not absence of a core engine; it is absence of a domain-focused product workflow for environmental policy operations.

### Problem Impact

- **Energy/environmental researchers** must chain multiple tools and custom scripts to assess a single policy — e.g., a carbon tax requires income modeling, energy consumption data, behavioral responses, and distributional analysis across separate systems with no integration guarantees
- **Weeks of infrastructure work** before any analysis begins, repeated for every new project or dataset update
- **Cross-domain policy** (carbon taxes affecting both income distribution and energy consumption) cannot be modeled in any single existing tool
- **Reproducibility crisis** — assumptions are buried in code, undocumented, and impossible for peers to audit or replicate
- **Government analysts** face long turnaround times and depend on specialized teams for assessments that should be routine

### Why Existing Solutions Fall Short

| Gap | OpenFisca | EUROMOD | Energy Tools (ResStock, demod) | Ad-hoc Scripts |
|-----|-----------|---------|-------------------------------|----------------|
| Domain scope | Tax-benefit only | Tax-benefit only | Energy/building only | Any, rebuilt each time |
| Distributional analysis | Yes | Yes | **No** | Manual |
| Entity model | Person/Household fixed | Person/Household fixed | Building/dwelling fixed | Custom, non-reusable |
| Behavioral responses | None (static only) | None (static only) | Physical models only | Manual, inconsistent |
| Cross-domain | No | No | No | Fragile |
| Reproducibility | Manual | Manual | Manual | Nonexistent |

The critical gap: environmental policy teams need an integrated workflow from OpenFisca baseline to multi-year environmental incidence analysis, with governance and no-code usability.

### Proposed Solution

A Python-first OpenFisca companion platform that lets a researcher define a carbon tax or subsidy scenario, run multi-year projections on French households, and get distributional impact indicators in minutes. Concretely:

- **Reuse OpenFisca baseline calculations** instead of recoding mature fiscal logic
- **Define environmental scenarios using templates** (carbon tax, rebates, subsidies, feebates)
- **Run dynamic year-by-year projections** with explicit state and vintage updates
- **Trust every result** through deterministic runs, manifests, and assumption logs
- **Operate through notebooks or no-code workflow** depending on user skill level

### Key Differentiators

1. **OpenFisca-first leverage** — stand on a mature open-source engine instead of rebuilding one
2. **Environmental policy template system** — direct support for carbon tax and subsidy family use cases
3. **Dynamic vintage projection** — practical 10+ year scenario operations above static baseline calculations
4. **Run governance by default** — assumption transparency and reproducibility as non-optional outputs
5. **No-code analyst workflow** — scenario setup/comparison without coding as an early product capability

---

## Target Users

### Primary Users

#### 1. Applied Policy Analyst — "Sophie"

**Profile:** Former researcher in environmental economics, now working in the evaluation department of the French Ministry of Ecological Transition. 35 years old, has built ad-hoc microsimulation models in Python during her PhD and postdoc. Comfortable with data and methodology but frustrated by rebuilding infrastructure for every policy assessment.

**Context:** Sophie's department evaluates proposed environmental policies — carbon tax reforms, energy renovation subsidies, vehicle emission standards. She typically has several weeks for deep analysis but must produce clear visual results quickly when the minister's office requests a briefing. Her current workflow involves chaining OpenFisca for income effects, custom Python scripts for energy consumption modeling, and Excel for final charts.

**Pain Points:**

- Rebuilds simulation pipelines for each new policy proposal
- Cross-domain analysis (income + energy) requires manually connecting separate tools
- Methodology documentation is an afterthought — audits and peer review are painful
- When a minister asks "what about income decile 3?" she needs hours, not minutes

**Success Vision:** Sophie starts from a no-code policy template, runs it against the latest INSEE household data, and within minutes has distributional charts by income decile, energy consumption type, and region. When the methodology is questioned, she exports the full assumption log — every parameter, data source, and behavioral assumption documented automatically.

**Primary Interface:** No-code scenario workflow + built-in visualizations, with optional YAML editing for advanced users.

#### 2. Academic Researcher — "Marco"

**Profile:** Labor and environmental economist at a European university. 40 years old, publishes regularly on carbon tax incidence and behavioral responses. Runs econometric estimations in Stata and R, then needs a microsimulation layer to compute distributional impacts.

**Context:** Marco has estimated energy demand elasticities by income group and wants to plug them into a simulation to show the distributional effect of a carbon tax with progressive redistribution. Currently writes custom Python/NumPy code for each paper's simulation section.

**Pain Points:**

- Rebuilds microsimulation infrastructure for every paper
- No standard way to make his behavioral estimates reusable by others
- Replication packages are incomplete because the simulation code is ad-hoc
- Peer reviewers can't verify methodology without running his custom scripts

**Success Vision:** Marco plugs his estimated elasticities into ReformLab's behavioral response layer, runs the simulation via Jupyter notebook, and exports a complete replication package — code, data references, parameters, and methodology — ready for a journal appendix. He publishes his elasticity template so other researchers can reuse it.

**Primary Interface:** Python API + Jupyter notebooks. Contributes model templates back to the ecosystem.

### Secondary Users

#### 3. Engaged Public / Showcase Consumer — "Claire"

**Profile:** French teacher, 32 years old, politically engaged, wants to understand how different candidates' environmental proposals would affect her household and others like hers.

**Context:** Before elections, Claire wants to compare candidates' platforms on their environmental policies — who benefits, who pays, what's the distributional impact. She doesn't build models — she uses a pre-built showcase application.

**Pain Points:**

- Policy debates are abstract — "this carbon tax will cost X billion" means nothing for her household
- No way to see the distributional impact of competing proposals side by side
- Media coverage rarely shows "who wins, who loses" by income group

**Success Vision:** Claire visits a public web application built on ReformLab that compares all candidates' environmental proposals. She enters her household profile (income, region, housing type, commuting pattern) and sees: "Under Candidate A's carbon tax, your household pays €X more but receives €Y in rebates. Under Candidate B's approach, the effect is €Z." She also sees the full distributional picture across income deciles.

**Primary Interface:** Web-based showcase application (built on top of the ReformLab framework by the project maintainer or contributors).

### User Journey

#### Discovery → Adoption Path

| Stage | Sophie (Policy Analyst) | Marco (Researcher) | Claire (Citizen) |
|-------|------------------------|--------------------|--------------------|
| **Discovery** | Finds ReformLab through a colleague or conference presentation on carbon tax modeling | Discovers it in a journal paper that used it for distributional analysis, or through the Python/open-source ecosystem | Sees the election comparison tool shared on social media or in a news article |
| **Onboarding** | Installs the library, runs the carbon tax example, sees distributional charts in minutes — "this used to take me weeks" | Reads the API docs, runs a notebook example, plugs in her own elasticities | Opens the web app, answers household profile questions |
| **Aha Moment** | Modifies a YAML parameter, re-runs, and gets updated charts instantly — realizes she'll never chain three tools again | Exports a complete replication package with one command | Sees side-by-side candidate comparison with her household highlighted |
| **Core Usage** | Configures new policy assessments in YAML, generates briefing-ready visualizations for her department | Uses Python API for papers, contributes templates for reuse | Returns before elections to compare updated proposals |
| **Long-term** | Becomes the department's go-to tool; she customizes templates for recurring policy domains | Publishes reusable templates; framework becomes standard in her field | Shares the tool with friends; expects it for every election |

---

## Success Metrics

### User Success Metrics

| Metric | Definition | Target |
|--------|-----------|--------|
| **Complete analysis deliverable** | A single simulation run produces a full report — welfare effects, fiscal cost, sensitivity analysis, distributional impact — ready to send to a manager without post-processing | Report generated in a single command from YAML config |
| **Replication package export** | Complete, self-contained replication package (code, data refs, parameters, methodology narrative) exportable from any simulation run | One-command export, verifiable by a third party |
| **Policy correctness** | Simulation results match known policy outcomes and published benchmarks within defined tolerance | Validation suite passes against reference datasets (e.g., known carbon tax revenue, distributional benchmarks) |
| **Time-to-first-result** | New user installs the framework, runs the carbon tax example, and sees distributional charts | Under 30 minutes from install to first meaningful output |

### Business Objectives

Since ReformLab is an open-source project (not a commercial product), "business" objectives are adoption, credibility, and real-world policy impact.

| Objective | Definition | 12-Month Target |
|-----------|-----------|-----------------|
| **Government adoption** | Evaluation departments or policy teams within public administration actively using the framework | 5 teams in government/administration |
| **Correctness credibility** | Framework produces validated, trustworthy results that withstand methodological scrutiny | Validation suite covering core policy domains; results reproducible by independent users |
| **Ecosystem seeding** | Researchers contributing model templates or using the framework in published work | At least 1 published paper or working paper using ReformLab |
| **Showcase impact** | Election comparison tool generates public engagement and policy debate visibility | Measurable public engagement (visitors, social media shares, media citations) |

### Key Performance Indicators

**Core KPIs (tracked from launch):**

1. **Correctness rate** — % of validation benchmarks passed across all policy domain test suites. Target: 100% on core benchmarks before any public release
2. **Active government teams** — Number of distinct teams in administration/international orgs actively running simulations. Target: 5 within first year
3. **Report completeness** — A single simulation run produces welfare analysis, fiscal cost, sensitivity analysis, and distributional impact in one exportable report. Target: all four components in MVP
4. **Showcase engagement** — Unique visitors and social shares on the election comparison application. Target: meaningful public reach during election cycle

**Secondary KPIs (tracked as ecosystem grows):**

5. **Community templates** — Number of reusable model templates contributed by external researchers
6. **PyPI downloads** — Monthly install volume as a proxy for awareness and experimentation
7. **Replication success rate** — % of exported replication packages that reproduce results independently

---

## MVP Scope

### Core Features

**1. OpenFisca Integration Layer**

- Import OpenFisca outputs via CSV/Parquet and optional direct API orchestration
- Versioned mapping between OpenFisca variables and project schema

**2. Environmental Policy Template Layer**

- Declarative scenario templates in YAML/JSON
- Carbon tax MVP ships with 4-5 redistribution templates: flat dividend, progressive rebate, renovation voucher, green VAT relief, mixed approach
- Subsidy and feebate pattern support in the same workflow

**3. Dynamic Orchestrator + Vintage Tracking**

- Deterministic year-by-year execution for 10+ years
- Explicit carry-forward state updates between years
- Vintage/cohort tracking for assets relevant to environmental transitions

**4. Synthetic Population & Data Inputs (Open Data Default)**

- Framework works out of the box with no restricted data — critical for adoption
- Simple default method: cross-tabulation from published marginals (INSEE, Eurostat public tables) with equal distribution within cells
- Also supports more sophisticated methods (IPF, copula-based) as the framework matures — research needed during development
- Also accepts real microdata when users have access (CSV/Parquet import)
- Every distributional assumption in the synthetic population is logged and documented

**5. Indicator & Analytics Toolkit**

- Distributional analysis: impact by income decile, energy consumption type, region
- Welfare analysis: winners/losers counts, average gains/losses by group
- Fiscal cost: total revenue/expenditure impact of the reform
- Parameter-sweep support for policy sensitivity analysis

**6. Assumption Logging & Reproducibility**

- Every simulation run produces an immutable run manifest: data sources, parameters, assumptions, engine version
- Run lineage across years and scenario branches

**7. Python API + No-Code Workflow**

- Full Python API for programmatic use (Marco's notebook workflow)
- No-code GUI for scenario creation/execution/comparison (Sophie's operational workflow)
- `pip install reformlab` quickstart with OpenFisca integration examples

### Out of Scope for MVP

| Feature | Rationale | Target Phase |
|---------|-----------|-------------|
| **Behavioral equilibrium responses** (full structural layer) | Adds major complexity after dynamic orchestration baseline | Phase 2 |
| **Physical system loops** (energy/climate stock-flow) | Requires coupling external specialized models | Phase 2 |
| **Election showcase application** | Requires stable core + web layer | Phase 3 |
| **Community template marketplace** | Needs critical mass of models first (3-5 proven templates) | Phase 4 |
| **Cloud/distributed computation** | Single-machine vectorized is sufficient for MVP populations | Phase 3 |
| **CLI interface** | Python API + no-code flow covers personas; CLI is convenience | Phase 2 |
| **Advanced synthetic methods** | Simple cross-tabulation first; IPF/copula methods added as research progresses | Phase 2 |

### MVP Success Criteria

The MVP is validated when:

1. **End-to-end carbon tax model works**: Define a carbon tax on household energy footprint in YAML, run against a synthetic French population generated from open data, compare 4-5 redistribution scenarios
2. **Dynamic loop works**: Run baseline and reform over at least 10 yearly periods with deterministic output
3. **Vintage tracking works**: At least one asset cohort/vintage dimension is updated and reported through time
4. **Correctness validated**: Results match known benchmarks (published carbon tax revenue estimates, distributional patterns from academic literature)
5. **30-minute onboarding**: New user installs via pip, runs the carbon tax example, and sees meaningful distributional output
6. **Assumption transparency proven**: Every assumption in the synthetic population and policy model is logged and exportable

**Go/no-go for Phase 2**: At least 1 external user (government team or researcher) has run the carbon tax model successfully and confirmed the results are credible.

### Future Vision

**Phase 2 — Behavioral & Ecosystem Expansion**

- Reduced-form elasticity layer (plug in estimated behavioral responses)
- Advanced synthetic population methods (IPF, copula-based)
- CLI interface for automation
- Additional policy domain templates (energy renovation subsidies, vehicle emission standards)
- Replication package improvements based on researcher feedback
- Physical-system connector interfaces (optional couplings)

**Phase 3 — Platform & Accessibility**

- Web UI for non-technical users (no-code interface)
- Election showcase application — compare candidates' environmental proposals
- Advanced dynamic modules for lifecycle modeling
- Cloud-scalable computation for large Monte Carlo runs
- API service layer (FastAPI) for integration into external systems

**Phase 4 — Community & Standards**

- Community template gallery and marketplace
- Structural behavioral models (labor supply, energy demand)
- Multi-country support beyond France
- AI-assisted model building and interpretation
- "Built with ReformLab" certification/credibility standard
