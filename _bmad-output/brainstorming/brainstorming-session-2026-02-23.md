---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: []
session_topic: 'Generic microsimulation framework for public policy assessment — serving policymakers, researchers, and citizens'
session_goals: 'Architecture, feature innovation, usability across skill levels, data strategy, democratization of policy analysis'
selected_approach: 'AI-Recommended Techniques'
techniques_used: ['Role Playing', 'Morphological Analysis', 'Cross-Pollination', 'First Principles Thinking', 'Constraint Mapping']
ideas_generated: 51
context_file: ''
session_active: false
workflow_completed: true
---

# Brainstorming Session Results

**Facilitator:** Lucas
**Date:** 2026-02-23

## Session Overview

**Topic:** Generic microsimulation framework for public policy assessment — leveraging survey and detailed data, with pre-built agent decision functions, easy data/parameter configurability, and a robust computational core.

**Goals:** Architecture design, feature scoping, and innovation around usability, extensibility, and analytical rigor. Serving three user personas: policymakers, researchers/economists, and citizens.

### Session Setup

**User Personas:**

1. **Policymakers** — government ministries, agencies; need accessible tools to evaluate policy impacts
2. **Researchers/Economists** — rapid microsimulation analyses after econometric estimation, full analytical rigor
3. **Citizens** — explore policy impacts using pre-loaded public datasets (e.g., INSEE), build simple models

**Key Vision Elements:**

- Core Python library (simulation engine, uncertainty/sensitivity analysis, testing)
- Pre-built agent decision functions
- Easy data/parameter extensibility
- Skills/templates layer for guided model building
- Simple web UI for non-technical users
- Pre-loaded public datasets (INSEE, etc.)
- Multi-tier accessibility: no-code → low-code → full-code

## Technique Selection

**Approach:** AI-Recommended Techniques
**Analysis Context:** Microsimulation framework for public policy with focus on architecture, usability, and democratization

**Recommended Techniques:**

- **Phase 1 — Role Playing + Six Thinking Hats:** Empathy-driven persona exploration followed by 360-degree analysis
- **Phase 2 — Morphological Analysis + Cross-Pollination:** Systematic architecture mapping combined with cross-domain inspiration
- **Phase 3 — First Principles Thinking + Constraint Mapping:** Strip to essentials then map real vs. imagined barriers

**AI Rationale:** Multi-persona system serving three very different user types demands deep empathy work first, then systematic exploration of the solution space, and finally grounding in what's truly essential and what's truly hard.

## Technique Execution Results

### Phase 1: Role Playing — Persona Deep Dives

#### Policymaker Persona (Senior policy analyst, French ministry)

**[Policy #1]**: Zero-Install Web Access
_Concept_: The policymaker opens a URL, logs in, and is immediately productive. No Python, no environment setup, no dependencies. A cloud-hosted web application that "just works."
_Novelty_: Most microsimulation tools (OpenFisca, EUROMOD) require technical setup — this flips the paradigm to SaaS-style access.

**[Policy #2]**: Trusted Data Already There
_Concept_: When the policymaker lands on the tool, French tax and household survey data (INSEE) is already loaded, validated, and documented. They don't go hunting for data — it's waiting for them.
_Novelty_: Shifts from "bring your own data" to "data is part of the service" — like how Google Maps doesn't ask you to upload a map.

**[Policy #3]**: Quick Visual Results
_Concept_: Within minutes of tweaking a policy parameter, the policymaker sees distributional impact charts — who wins, who loses, by how much, across which income deciles.
_Novelty_: The feedback loop is measured in minutes, not days. Think "policy playground" rather than "simulation project."

**[Policy #4]**: Auto-Generated Methodology Documentation
_Concept_: Every simulation run automatically produces a methodology report — what parameters were changed, what data was used, what assumptions underlie the model. The policymaker doesn't write documentation, it writes itself.
_Novelty_: Turns reproducibility from an afterthought into a built-in feature.

**[Policy #5]**: Excel-Native Export with Flexible Aggregation
_Concept_: One-click export to Excel with the user choosing aggregation level — by income decile, by region, by household type, by age group, or any combination. The policymaker builds the exact table the minister needs.
_Novelty_: Most tools export raw data or fixed tables. This gives the policymaker a "pivot table builder" before export.

**[Policy #6]**: Smart Output Size Advisor
_Concept_: Before exporting, the system warns: "This export will generate 2.3 GB across 450,000 rows. Would you like to aggregate by decile instead? That would be 12 KB." Intelligent guidance on output sizing with suggested alternatives.
_Novelty_: Prevents the classic mistake of exporting individual-level data when you only need summary statistics.

**[Policy #7]**: "Minister-Ready" Export Template
_Concept_: A pre-formatted export mode — clean charts, summary table, methodology footnote, comparison against baseline — formatted for a slide deck or a 2-page policy brief. One click, ready for the cabinet meeting.
_Novelty_: The tool understands that the end product isn't a spreadsheet — it's a decision.

#### Researcher/Economist Persona (Labor economist at university)

**[Research #8]**: The Integration Gap as Core Value Proposition
_Concept_: The framework fills the gap that neither OpenFisca nor EUROMOD nor any energy model addresses — a generic, extensible microsimulation engine where "entities" aren't just persons and households, but also buildings, vehicles, energy systems. Policy rules, behavioral responses, AND physical models coexist in one framework.
_Novelty_: Nobody has built this. OpenFisca is locked to tax-benefit. Energy models are locked to physics. This framework is domain-agnostic by design.

**[Research #9]**: Pluggable Econometric Results
_Concept_: The researcher estimates labor supply elasticities or energy demand elasticities in their own workflow (Stata, R, Python), then plugs the coefficients directly into the framework's behavioral response layer. The framework consumes estimation results, not raw data.
_Novelty_: OpenFisca has zero behavioral response. EUROMOD has experimental add-ons. This framework makes behavioral modeling a first-class citizen.

**[Research #10]**: Guided Notebooks + AI-Native Workflow
_Concept_: For the researcher persona, the primary interface is Jupyter notebooks with pre-built templates — "Plug in your elasticities here, define your reform here, run." Combined with BMAD-style AI skills that help scaffold a new model domain from scratch.
_Novelty_: Meets researchers where they already work (notebooks), while AI assistance lowers the barrier from "build from scratch" to "guided configuration."

**[Research #11]**: One-Click Data Population Loading
_Concept_: The researcher selects a population dataset (e.g., INSEE household survey) and the framework automatically maps variables to the simulation's entity structure — income, household composition, occupation, housing type. No manual column mapping unless you want to override.
_Novelty_: Makes "get the data" a solved problem, not a project.

**[Research #12]**: Elasticity Application Engine
_Concept_: A dedicated layer where researchers define behavioral responses — "apply this elasticity to this household group for this variable." The framework handles the mechanics: identify the subpopulation, apply the response function, propagate through the simulation.
_Novelty_: Behavioral response becomes a composable, declarative operation — not buried in custom code.

**[Research #13]**: Smart Assumption Library with Pre-Built Distributions
_Concept_: When you need to cross income by occupation but lack the joint distribution, the framework offers pre-calculated assumptions: uniform, proportional to marginals, log-normal, or custom. You pick from a menu, and the choice is automatically logged in the methodology documentation.
_Novelty_: Every microsimulation involves assumptions about missing data. This framework makes assumptions explicit, documented, and swappable.

**[Research #14]**: Self-Updating Documentation & Replication Package
_Concept_: Every action — data selection, assumption choice, elasticity application, parameter change — is logged into a living methodology document. At any point, the researcher clicks "Export Replication Package" and gets: data references, code, parameters, assumptions, and a narrative methodology — ready for a journal submission appendix.
_Novelty_: Reproducibility is the number one crisis in empirical economics. This framework makes it automatic, not aspirational.

**[Research #15]**: Exogenous Data Registry with Pre-Loaded Sources
_Concept_: Macroeconomic and external data — inflation rates, energy prices, demographic projections, exchange rates — are pre-loaded from official sources (INSEE, Eurostat, ECB, IEA) and versioned. The researcher selects a scenario or imports custom projections, and the framework injects these into the simulation environment.
_Novelty_: Eliminates the "where do I get inflation data and how do I plug it in" problem.

**[Research #16]**: The "Assumption-Transparent" Paradigm
_Concept_: The entire framework philosophy is that every assumption is visible, documented, and swappable. No hidden defaults. No magic numbers buried in code. Every distributional assumption, every exogenous input, every behavioral parameter is surfaced, explained, and exportable. This becomes the framework's intellectual identity.
_Novelty_: Positions the framework not just as a tool but as a methodological standard — "if you used this framework, your work is reproducible by definition."

#### Citizen Persona (French teacher, €2,400/month)

**[Citizen #17]**: Guided Questionnaire Entry ("Tell Us About You")
_Concept_: The citizen answers simple closed questions — "What's your monthly income?", "How many people in your household?", "Do you rent or own?", "What region do you live in?" — and the framework builds their household profile automatically. No jargon, no data uploads, just a friendly form.
_Novelty_: Like a tax calculator on steroids — but instead of calculating what you owe, it calculates how a policy reform changes your life.

**[Citizen #18]**: Advanced Mode Toggle
_Concept_: A simple toggle: "Basic Mode" (closed questions, pre-set assumptions) vs. "Advanced Mode" (custom assumptions, detailed parameters). The citizen starts in basic, but curious users can unlock the full power without leaving the interface.
_Novelty_: Respects both the "just tell me the answer" user and the "I want to understand the details" user.

**[Citizen #19]**: Scenario Comparison Dashboard
_Concept_: The citizen creates multiple scenarios — "What if the reform passes? What if a different version passes? What if nothing changes?" — and sees them side-by-side. Visual, instant, comparative. Slider-based: drag the housing benefit amount and watch your results update in real time.
_Novelty_: Transforms passive policy consumption into active policy exploration. Democratic empowerment.

**[Citizen #20]**: The "Both Sides" View — Benefits AND Costs
_Concept_: The citizen doesn't just see "you gain €50/month in housing benefits." They also see: "This reform costs €X billion, financed by Y, which means your taxes increase by €Z." The full picture — what you gain, what it costs, who pays. Transparent fiscal balance.
_Novelty_: Radical transparency. Most policy communication shows only the benefit side.

**[Citizen #21]**: "People Like Me" Comparison
_Concept_: Beyond your personal result, the tool shows: "Here's how this reform affects households similar to yours — same income range, same region, same family structure." And also: "Here's the impact across all income groups." The citizen sees themselves in context.
_Novelty_: Moves from individual calculator to societal mirror.

### Phase 2: Morphological Analysis — Architecture Dimensions

#### Architecture Map

| Dimension | Choice | Rationale |
|-----------|--------|-----------|
| 1. Entity Model | C — Fully extensible entity graph | Domain-agnostic; any entity type, any relationship |
| 2. Behavioral Response | A+B+C+D — Layered system | Static through custom functions; static as baseline comparator |
| 3. Time Structure | E — Hybrid static + dynamic | Quick static for policymakers, dynamic for researchers |
| 4. Data Architecture | E — Unified multi-source + synthetic | Files, catalog, APIs, synthetic generation; unified abstraction |
| 5. Computation | E — Tiered performance | Vectorized → parallel → cloud; auto-selects by workload |
| 6. Analytical Toolkit | E — Full suite + validation + calibration | Distributional, uncertainty, sensitivity, validation, calibration |
| 7. Interface Layers | E — Full stack, AI last | Library → CLI → Notebooks → Web UI → AI assistant |

#### Architecture Ideas

**[Arch #22]**: Extensible Entity Graph Model
_Concept_: The framework core is entity-agnostic. Users define entity types (Person, Household, Building, Vehicle, Firm, PowerPlant...) and relationships between them (lives_in, owns, employs, supplies_energy_to). The simulation engine operates on this graph.
_Novelty_: No existing microsimulation framework does this. This makes the framework truly domain-agnostic.

**[Arch #23]**: Layered Behavioral Response System (A+B+C+D)
_Concept_: Four behavioral modes: Static (mechanical, fast, baseline), Reduced-form elasticities (plug your own), Structural models (pre-built labor supply, consumption), Pluggable custom functions (anything). Run the same reform through multiple modes and compare.
_Novelty_: Static isn't a limitation — it's a feature. Comparing modes becomes built-in sensitivity analysis.

**[Arch #24]**: Behavioral Mode Comparison as Default Output
_Concept_: Default output shows: "Static impact: €X. With elasticities: €Y. With structural model: €Z." The gap between them IS the story.
_Novelty_: Makes the methodological choice transparent across all personas.

**[Arch #25]**: Hybrid Static + Dynamic Time Engine
_Concept_: Static snapshot for fast policy assessment, dynamic with discrete time steps for lifecycle and transition modeling. Same model definition works in both modes — switching is a parameter, not a redesign.
_Novelty_: Most frameworks commit to one paradigm. This supports both.

**[Arch #26]**: Unified Data Layer with Multi-Source Abstraction
_Concept_: A single data interface that transparently handles files, pre-loaded catalog, live APIs, and synthetic populations. Data provenance automatically tracked.
_Novelty_: Eliminates the "data preparation project" that precedes every microsimulation.

**[Arch #27]**: Built-in Synthetic Population Generator
_Concept_: From published marginal distributions, generate statistically consistent synthetic populations using IPF or copula-based methods. Designed from day one — entity graph, validation, and assumption logging all work seamlessly with synthetic data.
_Novelty_: Solves the data access paradox. Synthetic data with transparent methodology is the bridge.

**[Arch #28]**: Tiered Computation Engine
_Concept_: Vectorized NumPy by default (sub-second for citizens), parallel multi-core for medium workloads (sensitivity analysis), cloud-scalable for heavy research (Monte Carlo). Auto-selects tier based on workload.
_Novelty_: Same codebase, three performance modes.

**[Arch #29]**: Deployable Web App as Future Layer
_Concept_: Core Python library designed from day one with clean API boundaries, stateless simulation runs, serializable inputs/outputs. Web deployment (FastAPI + frontend) wraps the library later.
_Novelty_: Library first, web app wraps the library. Avoids monolithic desktop trap.

**[Arch #30]**: Full Analytical Suite as Core
_Concept_: Distributional analysis (deciles, Gini, poverty rates, winners/losers), uncertainty analysis (Monte Carlo, confidence intervals), and sensitivity analysis (parameter sweeps, tornado diagrams) built into the core library as first-class operations.
_Novelty_: Usually afterthoughts requiring separate tools. Here they're core operations any persona can access.

**[Arch #31]**: Validation Mode with Benchmark Targets
_Concept_: User defines validation targets — "In 2023, total income tax revenue was €X billion." Framework runs baseline and reports deviations. Dashboard shows green/yellow/red for each target. Validation results are part of the replication package.
_Novelty_: Transforms validation from "I hope my model is right" into structured quality assurance.

**[Arch #32]**: Calibration Engine
_Concept_: If the model doesn't match targets, the framework suggests or automatically calibrates parameters. User approves each calibration, and it's logged.
_Novelty_: Turns days-long manual calibration into a guided workflow.

**[Arch #33]**: Full Interface Stack with AI as Future Layer
_Concept_: Build order: Python library (core) → CLI (automation) → Guided notebooks (researcher onboarding) → Web UI (policymaker/citizen) → AI assistant (interpretation, plain-language). Each layer wraps the previous one. AI planned for but built last.
_Novelty_: Build order matches persona priority. Each layer proves the one beneath it.

### Phase 2: Cross-Pollination — Ideas from Other Domains

**[Cross #34]**: Shareable Policy Notebooks
_Concept_: Like Jupyter notebooks but for policy analysis. A researcher publishes a "Policy Notebook" — model, data references, reform definition, results. Anyone can fork, change parameters, re-run. GitHub for policy analysis.
_Novelty_: Turns microsimulation from private research into collaborative open science.

**[Cross #35]**: Model Templates Gallery
_Concept_: Like Canva templates — browse "Income Tax Reform (France)", "Energy Poverty Assessment (EU)", "Housing Benefit Analysis (UK)". Pick, customize, run. Template includes entity structure, rules, behavioral assumptions, visualization layout.
_Novelty_: Collapses "build from scratch" into "customize an existing model." Community contributes templates.

**[Cross #36]**: Reform Version Control
_Concept_: Every policy reform is a "diff" against a baseline — like a code commit. Branch, compare, merge, trace history. "Show me every reform tested against the 2024 baseline."
_Novelty_: Software engineering's most powerful concept applied to policy analysis.

**[Cross #37]**: Community Template Marketplace
_Concept_: Living ecosystem where researchers publish model templates, others review and rate them, popular templates get "verified" status. A researcher in Brazil builds an energy poverty template, one in France forks and adapts it. npm/PyPI for policy models.
_Novelty_: Network effects — every new template makes the framework more valuable.

**[Cross #38]**: Template Anatomy — What's Inside
_Concept_: Every template is a structured package: entity definitions, policy rules, behavioral configs, data requirements (with sample data), visualization layouts, validation benchmarks, narrative README. The README explains the economics, not just the code.
_Novelty_: Templates aren't just code — they're complete, documented, runnable policy analysis environments.

**[Cross #39]**: Policy Simulation Sandbox
_Concept_: Inspired by city-builder games — visual, interactive environment with sliders for tax rates, benefit levels, energy prices. Watch the simulated population respond in real time. Instant-feedback exploratory feel.
_Novelty_: Makes policy analysis feel like exploration rather than computation.

**[Cross #40]**: Declarative Policy Definition Language (YAML/DSL)
_Concept_: Instead of Python functions for every rule, write declarative YAML policy definitions. The framework compiles into simulation logic. Readable by policymakers, editable by researchers, versionable by Git. Covers 80% of use cases; custom Python for the rest.
_Novelty_: The configuration file IS the documentation.

**[Cross #41]**: Declarative Policy-as-Code (confirmed)
_Concept_: YAML configuration files as single source of truth for policy reforms. Versionable, diffable, shareable. Policymaker reads it, researcher writes it, Git tracks it.

**[Cross #42]**: Policy Sandbox (noted for UI phase)
_Concept_: Interactive, real-time slider-based exploration. Key UI design concept for future web application layer.

### Phase 3: First Principles Thinking + Constraint Mapping

**[FP #43]**: The Three Primitives — Entities, Rules, Engine
_Concept_: The entire framework rests on three abstractions: an Entity (any object with typed attributes), a Rule (a function that reads entity attributes and produces outputs), and an Engine (the orchestrator that applies rules to a population). Everything else is layered on top. If you get these three right, everything works.
_Novelty_: Domain-free version of what OpenFisca partially achieved with Variable/Entity/Simulation.

**[FP #44]**: The Framework's Value = Structure + Guarantees
_Concept_: The framework gives what scripts don't: guaranteed reproducibility (every run logged), guaranteed consistency (relationships enforced), guaranteed analysis (uncertainty/sensitivity come free), guaranteed documentation (assumptions tracked automatically). Not faster — trustworthy.
_Novelty_: Positions the framework as a credibility tool. "Built with MicroSim" = quality signal.

**[Constraint #45]**: Scope Risk — Mitigated by Layered Build
_Concept_: Serving three personas is risky but manageable through sequenced layers. Researchers first (validate core), policymakers second (need UI), citizens third (need simplest interface). The constraint becomes the roadmap.

**[Constraint #46]**: Adoption — Side Project Advantage
_Concept_: As a side project, adoption pressure is lower. Need one compelling use case (energy sector) that demonstrates the framework works. Build something you yourself would use. If a domain expert finds it useful, other domain experts will too.

**[Constraint #47]**: Data — Synthetic Generation as Strategic Moat
_Concept_: Data restrictions are an opportunity. If the framework works beautifully with synthetic data AND real data, it solves the access problem that blocks OpenFisca/EUROMOD adoption. "Works without restricted data access" is a competitive advantage.

**[Constraint #48]**: Technical — Claude Code as Force Multiplier
_Concept_: Building a generic entity graph engine is hard — but AI-assisted development dramatically increases solo developer velocity.

### Phase 3: MVP Definition

**[FP #49]**: MVP Model — Carbon Tax on Total Household Energy Footprint
_Concept_: Carbon tax applied to full household carbon footprint — transportation, housing, food. Revenue redistributed under different scenarios: flat rebate, progressive rebate, targeted vouchers, reduced VAT. Distributional impact across income deciles. One model that exercises every core feature.

**[FP #50]**: The Carbon Footprint Entity Structure
_Concept_: Each household has consumption sub-entities: Transportation (car type, km/year, fuel type), Housing (dwelling type, heating system, electricity, insulation), Food (dietary pattern → carbon intensity). Different carbon coefficients, elasticities, and equity implications per category.

**[FP #51]**: Redistribution Scenarios as Policy-as-Code Templates
_Concept_: MVP ships with 4-5 redistribution YAML templates: flat carbon dividend, progressive rebate, energy renovation vouchers, reduced VAT on green alternatives, 50/50 mix. Each is a one-page YAML. User runs all five and compares. The template gallery in miniature.

## Idea Organization and Prioritization

### Thematic Organization

| Theme | Ideas | Description |
|-------|-------|-------------|
| 1. User Experience by Persona | #1-7, #17-21 | Each persona needs a radically different entry point, same engine underneath |
| 2. Core Architecture | #22-29, #43-44 | Domain-agnostic by design; extensible entity graph, layered complexity |
| 3. Transparency & Reproducibility | #4, #13-16, #31-32 | Framework's intellectual identity: every assumption visible, documented, swappable |
| 4. Analytical Power | #23-24, #30-32 | Analysis as core feature, not afterthought; validation and calibration built in |
| 5. Ecosystem & Community | #34-38 | Network effects through templates, notebooks, marketplace |
| 6. Policy-as-Code | #40-41, #51 | YAML configuration as single source of truth; readable, writable, versionable |
| 7. MVP & Strategy | #45-51 | Carbon tax MVP; layered build; constraints as roadmap |

### Breakthrough Concepts

1. **Extensible Entity Graph (#22)** — The architectural decision that makes this fundamentally different from OpenFisca/EUROMOD. Not locked to person/household. Any entity, any relationship.
2. **Assumption-Transparent Paradigm (#16)** — The intellectual identity. Every assumption visible, documented, swappable. "Built with this framework" = "reproducible by definition."
3. **The Integration Gap (#8)** — Fills a gap nobody else has filled: income + energy + policy + behavior in one model.

### Prioritization Results

**User-selected priorities:**

- **Top High-Impact Themes:** Theme 1 (UX by Persona), Theme 3 (Transparency), Theme 4 (Analytical Power)
- **Foundation / Quick Win:** Theme 2 (Core Architecture) — must be built first as everything depends on it
- **Most Innovative:** Theme 2 — the extensible entity graph is the technical breakthrough that enables everything

### Action Plans

**Priority 1: Core Architecture (Theme 2) — THE FOUNDATION**

1. Design the Entity Graph data model — entity types, attributes, relationships in Python
2. Implement the Rule engine — composable functions with static + behavioral modes
3. Build the Simulation Engine — orchestrator applying rules to populations, static first
4. Define YAML policy-as-code schema — configuration format for policy rules
5. Prove with **Carbon Tax MVP** — households + consumption sub-entities + 4-5 redistribution scenarios

_Success Indicator:_ Define a carbon tax in YAML, apply to synthetic French households, see distributional results by decile — from a Jupyter notebook.

**Priority 2: Transparency & Reproducibility (Theme 3)**

1. Auto-logging of every simulation run: data sources, parameters, assumptions, engine version
2. Assumption library with pre-built distributions (uniform, proportional, log-normal), logged on selection
3. Validation mode: define benchmark targets, compare model output, report deviations
4. One-click replication package export

_Success Indicator:_ Researcher runs carbon tax model and exports complete replication package another researcher can reproduce exactly.

**Priority 3: Analytical Power (Theme 4)**

1. Distributional analysis module (deciles, Gini, poverty rates, winners/losers)
2. Behavioral mode comparison (static vs. elasticity-based, side by side)
3. Sensitivity analysis (parameter sweeps, tornado diagrams)
4. Uncertainty analysis (Monte Carlo wrapper, confidence intervals)

_Success Indicator:_ Carbon tax MVP produces distributional charts, sensitivity diagrams, and confidence intervals from built-in functions.

**Priority 4: User Experience by Persona (Theme 1)**

1. Guided Jupyter notebook template for carbon tax MVP
2. Excel export with flexible aggregation
3. Auto-generated methodology documentation
4. Web UI and citizen interface — planned architecturally, built later

_Success Indicator:_ Researcher opens notebook, follows guide, plugs in own elasticities, produces publishable analysis.

**Longer-term Roadmap:**

- Template gallery and community marketplace (Theme 5) — after 3-5 proven models
- Policy sandbox UI (Theme 6) — when web application layer is built
- AI assistant integration (Theme 7) — last layer, highest citizen impact

## Competitive Landscape

### Existing Tools Comparison

| Dimension | OpenFisca | EUROMOD | This Framework |
|-----------|-----------|---------|---------------|
| Entity model | Person/Household only | Person/Household only | Fully extensible entity graph |
| Behavioral response | None (static only) | None (static only) | Layered: static → elasticities → structural → custom |
| Time structure | Static snapshot | Static snapshot | Hybrid static + dynamic |
| Data access | Bring your own | Restricted (EU-SILC, ~8 weeks) | Unified: files + catalog + APIs + synthetic |
| Language | Python | C# (Windows GUI) | Python (library-first) |
| Sectors | Tax-benefit only | Tax-benefit only | Domain-agnostic (energy, health, housing...) |
| Reproducibility | Manual | Manual | Automatic (assumption-transparent paradigm) |
| Citizen access | None | None | Web UI with guided questionnaire |

### Energy Sector Gap

No unified framework exists that joins income + energy consumption + policy intervention. Current state: chain OpenFisca/EUROMOD with demod/ResStock and TABULA manually in fragile pipelines. This framework fills that gap.

## Session Summary and Insights

### Key Achievements

- **51 ideas** generated across 7 themes using 5 brainstorming techniques
- **Clear architectural vision** with 7 dimensions fully specified
- **Defined MVP** — carbon tax on total household energy footprint with redistribution scenarios
- **Identified core differentiators** — extensible entity graph, assumption transparency, integration gap
- **Actionable 4-priority roadmap** from foundation to full platform

### Creative Facilitation Narrative

This session moved from empathy (inhabiting three radically different user personas) through systematic architecture mapping (7 dimensions explored exhaustively) to grounded reality (first principles, constraints, and MVP definition). The breakthrough moment came when connecting the energy sector gap research to the extensible entity graph — confirming that no existing tool serves this space, and that the architectural choice to be domain-agnostic is not just elegant but necessary. Lucas's instinct to start with the carbon tax MVP is strategically sound: it exercises every core feature while addressing a real gap in his domain expertise.

### Session Reflections

**What worked well:** The persona role-playing generated surprisingly concrete UX ideas (minister-ready exports, smart output sizing). The morphological analysis forced systematic consideration of every architectural dimension. The competitive landscape research (OpenFisca, EUROMOD, ResStock, demod) grounded the vision in reality.

**Key insight:** The framework's identity is not "another microsimulation tool" — it's an "assumption-transparent, domain-agnostic policy analysis platform." The transparency paradigm is what turns a technical tool into a credibility standard.
