<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 9 -->
<!-- Story: 9.5 -->
<!-- Phase: create-story -->
<!-- Timestamp: 20260301T220247Z -->
<compiled-workflow>
<mission><![CDATA[

Create the next user story from epics+stories with enhanced context analysis and direct ready-for-dev marking

Target: Story 9.5 - openfisca-france-reference-test-suite
Create comprehensive developer context and implementation-ready story.

]]></mission>
<context>
<file id="git-intel" path="[git-intelligence]"><![CDATA[<git-intelligence>
Git intelligence extracted at compile time. Do NOT run additional git commands - use this embedded data instead.

### Recent Commits (last 5)
```
b24d996 refactor(story-9.4): apply code review changes
64c4781 feat(story-9.4): implement story
e68180f docs(story-9.4): create story file
0eaf712 refactor(story-9.3): apply code review changes
e8c7e74 feat(story-9.3): implement story
```

### Related Story Commits
```
b24d996 refactor(story-9.4): apply code review changes
64c4781 feat(story-9.4): implement story
e68180f docs(story-9.4): create story file
0eaf712 refactor(story-9.3): apply code review changes
e8c7e74 feat(story-9.3): implement story
```

### Recently Modified Files (excluding docs/)
```
.bmad-assist/runs/run-20260301T190149Z-ae8684d9.yaml
.bmad-assist/state.yaml
_bmad-output/implementation-artifacts/benchmarks/2026-03/eval-9-3-a-20260301T193918Z.yaml
_bmad-output/implementation-artifacts/benchmarks/2026-03/eval-9-3-a-20260301T203944Z.yaml
_bmad-output/implementation-artifacts/benchmarks/2026-03/eval-9-3-b-20260301T193918Z.yaml
_bmad-output/implementation-artifacts/benchmarks/2026-03/eval-9-3-b-20260301T203944Z.yaml
_bmad-output/implementation-artifacts/benchmarks/2026-03/eval-9-3-master-20260301T200908Z.yaml
_bmad-output/implementation-artifacts/benchmarks/2026-03/eval-9-3-synthesizer-20260301T194530Z.yaml
_bmad-output/implementation-artifacts/benchmarks/2026-03/eval-9-3-synthesizer-20260301T204730Z.yaml
_bmad-output/implementation-artifacts/benchmarks/2026-03/eval-9-4-a-20260301T212059Z.yaml
```

</git-intelligence>]]></file>
<file id="b5c6fe32" path="_bmad-output/project-context.md" label="PROJECT CONTEXT"><![CDATA[

---
project_name: 'ReformLab'
user_name: 'Lucas'
date: '2026-02-27'
status: 'complete'
sections_completed: ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'code_quality', 'workflow_rules', 'critical_rules']
rule_count: 38
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

- **Python 3.13+** — `target-version = "py313"` (ruff), `python_version = "3.13"` (mypy strict)
- **uv** — package manager, **hatchling** — build backend
- **pyarrow >= 18.0.0** — canonical data type (`pa.Table`), CSV/Parquet I/O
- **pyyaml >= 6.0.2** — YAML template/config loading
- **jsonschema >= 4.23.0** — JSON Schema validation for templates
- **openfisca-core >= 44.0.0** — optional dependency (`[openfisca]` extra); never import outside adapter modules
- **pytest >= 8.3.3, ruff >= 0.15.0, mypy >= 1.19.0** — dev tooling
- **Planned frontend:** React 18+ / TypeScript / Vite / Shadcn/ui / Tailwind v4
- **Planned backend API:** FastAPI + uvicorn
- **Planned deployment:** Kamal 2 on Hetzner CX22

### Version Constraints

- mypy runs in **strict mode** with explicit `ignore_missing_imports` overrides for openfisca, pyarrow, jsonschema, yaml
- OpenFisca is optional — core library must function without it installed

## Critical Implementation Rules

### Python Language Rules

- **Every file starts with** `from __future__ import annotations` — no exceptions
- **Use `if TYPE_CHECKING:` guards** for imports that are only needed for annotations or would create circular dependencies; do the runtime import locally where needed
- **Frozen dataclasses are the default** — all domain types use `@dataclass(frozen=True)`; mutate via `dataclasses.replace()`, never by assignment
- **Protocols, not ABCs** — interfaces are `Protocol` + `@runtime_checkable`; no abstract base classes; structural (duck) typing only
- **Subsystem-specific exceptions** — each module defines its own error hierarchy; never raise bare `Exception` or `ValueError` for domain errors
- **Metadata bags** use `dict[str, Any]` with **stable string-constant keys** defined at module level (e.g., `STEP_EXECUTION_LOG_KEY`)
- **Union syntax** — use `X | None` not `Optional[X]`; use `dict[str, int]` not `Dict[str, int]` (modern generics, no `typing` aliases)
- **`tuple[...]` for immutable sequences** — function parameters and return types that are ordered-and-fixed use `tuple`, not `list`

### Architecture & Framework Rules

- **Adapter isolation is absolute** — only `computation/openfisca_adapter.py` and `openfisca_api_adapter.py` may import OpenFisca; all other code uses the `ComputationAdapter` protocol
- **Step pipeline contract** — steps implement `OrchestratorStep` protocol (`name` + `execute(year, state) -> YearState`); bare callables accepted via `adapt_callable()`; registration via `StepRegistry` with topological sort on `depends_on`
- **Template packs are YAML** — live in `src/reformlab/templates/packs/{policy_type}/`; validated against JSON Schemas in `templates/schema/`; each policy type has its own subpackage with `compute.py` + `compare.py`
- **Data flows through PyArrow** — `PopulationData` (dict of `pa.Table` by entity) → adapter → `ComputationResult` (`pa.Table`) → `YearState.data` → `PanelOutput` (stacked table) → indicators
- **`YearState` is the state token** — passed between steps and years; immutable (frozen dataclass); updated via `replace()`
- **Orchestrator is the core product** — never build custom policy engines, formula compilers, or entity graph engines; OpenFisca handles computation, this project handles orchestration

### Testing Rules

- **Mirror source structure** — `tests/{subsystem}/` matches `src/reformlab/{subsystem}/`; each has `__init__.py` and `conftest.py`
- **Class-based test grouping** — group tests by feature or acceptance criterion (e.g., `TestOrchestratorBasicExecution`); reference story/AC IDs in comments and docstrings
- **Fixtures in conftest.py** — subsystem-specific fixtures per `conftest.py`; build PyArrow tables inline, use `tmp_path` for I/O, golden YAML files in `tests/fixtures/`
- **Direct assertions** — use plain `assert`; no custom assertion helpers; use `pytest.raises(ExceptionClass, match=...)` for errors
- **Test helpers are explicit** — import shared callables from conftest directly (`from tests.orchestrator.conftest import ...`); no hidden magic
- **Golden file tests** — YAML fixtures in `tests/fixtures/templates/`; test load → validate → round-trip cycle
- **MockAdapter for unit tests** — never use real OpenFisca in orchestrator/template/indicator unit tests; `MockAdapter` is the standard test double

### Code Quality & Style Rules

- **ruff** enforces `E`, `F`, `I`, `W` rule sets; `src = ["src"]`; target Python 3.13
- **mypy strict** — all code must pass `mypy --strict`; new modules need `ignore_missing_imports` overrides in `pyproject.toml` only for third-party libs without stubs
- **File naming** — `snake_case.py` throughout; no PascalCase or kebab-case files
- **Class naming** — PascalCase for classes (`OrchestratorStep`, `CarbonTaxParameters`); no suffixes like `Impl` or `Base`
- **Module-level docstrings** — every module has a docstring explaining its role, referencing relevant story/FR
- **Section separators** — use `# ====...====` comment blocks to separate major sections within longer modules (see `step.py`)
- **No wildcard imports** — always import specific names; `from reformlab.orchestrator import Orchestrator, OrchestratorConfig`
- **Logging** — use `logging.getLogger(__name__)`; structured key=value format for parseable log lines (e.g., `year=%d seed=%s event=year_start`)

### Development Workflow Rules

- **Package manager is uv** — use `uv pip install`, `uv run pytest`, etc.; not `pip` directly
- **Test command** — `uv run pytest tests/` (or specific subsystem path)
- **Lint command** — `uv run ruff check src/ tests/` and `uv run mypy src/`
- **Source layout** — `src/reformlab/` is the installable package; `tests/` is separate; `pythonpath = ["src"]` in pytest config
- **Build system** — hatchling with `packages = ["src/reformlab"]`
- **No auto-formatting on save assumed** — agents must produce ruff-compliant code; run `ruff check --fix` if needed

### Critical Don't-Miss Rules

- **Never import OpenFisca outside adapter modules** — this is the single most important architectural boundary; violation couples the entire codebase to one backend
- **All domain types are frozen** — never add a mutable dataclass; if you need mutation, use `dataclasses.replace()` and return a new instance
- **Determinism is non-negotiable** — every run must be reproducible; seeds are explicit, logged in manifests, derived deterministically (`master_seed XOR year`)
- **Data contracts fail loudly** — contract validation at ingestion boundaries is field-level and blocking; never silently coerce or drop data
- **Assumption transparency** — every run produces a manifest (JSON); assumptions, versions, seeds, data hashes are all recorded
- **PyArrow is the canonical data type** — do not use pandas DataFrames in core logic; `pa.Table` is the standard; pandas only at display/export boundaries if needed
- **No custom formula compiler** — environmental policy logic is Python code in template `compute.py` modules, not YAML formula strings or DSLs
- **France/Europe first** — initial scenarios use French policy parameters (EUR, INSEE deciles, French carbon tax rates); European data sources (Eurostat, EU-SILC)

---

## Usage Guidelines

**For AI Agents:**

- Read this file before implementing any code
- Follow ALL rules exactly as documented
- When in doubt, prefer the more restrictive option
- Update this file if new patterns emerge

**For Humans:**

- Keep this file lean and focused on agent needs
- Update when technology stack changes
- Review quarterly for outdated rules
- Remove rules that become obvious over time

Last Updated: 2026-02-27


]]></file>
<file id="ab55991d" path="_bmad-output/planning-artifacts/prd.md" label="PRD"><![CDATA[

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

<!-- TRUNCATED: Content exceeded token budget. See full document for details. -->

]]></file>
<file id="1456c4bb" path="_bmad-output/planning-artifacts/architecture.md" label="ARCHITECTURE"><![CDATA[

---
stepsCompleted: [1, 2, 3, 4, 5]
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/product-brief-ReformLab-2026-02-23.md
  - _bmad-output/planning-artifacts/stakeholder-review-brief-ReformLab-2026-02-24.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
  - _bmad-output/planning-artifacts/research/technical-entity-graph-data-modeling-and-vectorized-simulation-engines-research-2026-02-23.md
  - _bmad-output/planning-artifacts/research/domain-generic-microsimulation-frameworks-research-2026-02-23.md
workflowType: 'architecture'
project_name: 'ReformLab'
user_name: 'Lucas'
date: '2026-02-25'
---

# Architecture Decision Document

_Updated 2026-02-25: Legacy custom engine sections removed per Sprint Change Proposal. See sprint-change-proposal-2026-02-25.md._

## Strategic Direction Update (2026-02-25)

### Decision

ReformLab will **not** build a replacement tax-benefit microsimulation core.
OpenFisca is the policy-calculation foundation, accessed through a clean adapter interface. This project builds differentiated layers above it: data preparation, environmental policy orchestration, multi-year projection with vintage tracking, indicators, governance, and user interfaces.

The **dynamic orchestrator is the core product** — not a computation engine.

### Active Scope

- Data ingestion and harmonization (OpenFisca outputs, synthetic population inputs, environmental datasets).
- Scenario/template layer for environmental policies (carbon tax, subsidies, rebates, feebates).
- Step-pluggable dynamic orchestrator for multi-year execution (10+ years) with vintage/cohort tracking.
- Indicator layer (distributional, welfare, fiscal, custom metrics).
- Run governance (manifests, assumption logs, lineage).
- No-code analyst GUI for scenario setup, execution, and comparison.

### Out Of Scope (MVP)

- Reimplementing OpenFisca internals.
- Custom formula compiler or policy engine.
- Endogenous market-clearing/equilibrium simulation.
- Physical system loop simulation (climate/energy stock-flow engines).

## Project Context Analysis (Active Baseline)

### Requirements Overview

**Functional focus (35 FRs):**

- OpenFisca integration and data contracts.
- Environmental scenario templates and batch comparison.
- Dynamic yearly orchestration with vintage tracking.
- Indicator computation and extensibility.
- Governance, reproducibility, and lineage.
- Notebook/API + early no-code GUI workflows.

**Non-functional focus (21 NFRs):**

- Deterministic and reproducible outputs.
- Laptop-scale performance for common workloads.
- Strict data privacy and offline execution.
- Versioned adapter compatibility with OpenFisca.
- CI-enforced quality on adapters, orchestration, and templates.

### Technical Constraints

- Python 3.13+.
- OpenFisca as the core rules engine dependency.
- CSV/Parquet as interoperability contracts.
- Fully offline operation in user environment.
- Single-machine target (16GB laptop) for MVP.

### Cross-Cutting Concerns

1. Assumption transparency and manifest lineage across all runs.
2. Deterministic sequencing in multi-year iterative execution.
3. Adapter/version governance for OpenFisca compatibility.
4. Clear data-contract validation at every ingestion boundary.
5. Scenario/template versioning for auditability and collaboration.

## Active Architecture Blueprint

### Core Design Principle

ReformLab does NOT build a policy computation engine. OpenFisca is the tax-benefit computation layer. This project builds everything around it: data preparation, environmental policy orchestration, multi-year projection, vintage tracking, indicators, governance, and user interfaces.

### Layered Architecture

```
┌─────────────────────────────────────────────────┐
│  Interfaces (Python API, Notebooks, No-Code GUI)│
├─────────────────────────────────────────────────┤
│  Indicator Engine (distributional/welfare/fiscal)│
├─────────────────────────────────────────────────┤
│  Governance (manifests, assumptions, lineage)    │
├─────────────────────────────────────────────────┤
│  Dynamic Orchestrator (year loop + step pipeline)│
│  ├── Vintage Transitions                         │
│  ├── State Carry-Forward                         │
│  └── [Phase 2: Behavioral Response Steps]        │
├─────────────────────────────────────────────────┤
│  Scenario Template Layer (environmental policies)│
├─────────────────────────────────────────────────┤
│  Data Layer (ingestion, open data, synthetic pop)│
├─────────────────────────────────────────────────┤
│  Computation Adapter Interface                   │
│  └── OpenFiscaAdapter (primary implementation)   │
└─────────────────────────────────────────────────┘
```

### Computation Adapter Pattern

The orchestrator never calls OpenFisca directly. All tax-benefit computation goes through a clean adapter interface:

```python
class ComputationAdapter(Protocol):
    """Interface for tax-benefit computation backends."""
    def compute(self, population: PopulationData, policy: PolicyConfig,
                period: int) -> ComputationResult: ...
    def version(self) -> str: ...

class OpenFiscaAdapter(ComputationAdapter):
    """Primary implementation wrapping OpenFisca."""
    ...
```

This allows:
- Swapping OpenFisca for PolicyEngine or other backends in the future
- Mocking the computation layer for orchestrator testing
- Version-pinning OpenFisca without coupling the core codebase

### Step-Pluggable Dynamic Orchestrator

The orchestrator runs a yearly loop (t → t+n) where each year executes a pipeline of pluggable steps:

```
For each year t in [start_year .. end_year]:
  1. Run ComputationAdapter (OpenFisca tax-benefit for year t)
  2. Apply environmental policy templates (carbon tax, subsidies)
  3. Execute transition steps (pluggable pipeline):
     a. Vintage transitions (asset cohort aging, fleet turnover)
     b. State carry-forward (income updates, demographic changes)
     c. [Phase 2: Behavioral response adjustments]
  4. Record year-t results and manifest entry
  5. Feed updated state into year t+1
```

Steps are registered as plugins. Phase 1 ships vintage transitions and state carry-forward. Phase 2 adds behavioral response steps without modifying the orchestrator core.

### Subsystems

1. `computation/`: Adapter interface + OpenFiscaAdapter implementation. Handles CSV/Parquet ingestion of OpenFisca outputs and optional direct API orchestration. Version-pinned contracts.
2. `data/`: Open data ingestion, synthetic population generation, data transformation pipelines. Prepares inputs for the computation adapter.
3. `templates/`: Environmental policy templates (carbon tax, subsidies, rebates, feebates) and scenario registry with versioned definitions.
4. `orchestrator/`: Dynamic yearly loop with step-pluggable pipeline. Manages deterministic sequencing, seed control, and state transitions.
5. `vintage/`: Cohort/vintage state management. Registered as orchestrator step. Tracks asset classes (vehicles, heating) through time.
6. `indicators/`: Distributional, welfare, fiscal, and custom indicator computation. Aggregation by decile, geography, and custom groupings.
7. `governance/`: Run manifests, assumption logs, run lineage, output hashes. Tracks OpenFisca version, adapter version, scenario version.
8. `interfaces/`: Python API, notebook workflows, early no-code GUI.

### Starter & Tooling Decisions

- Scientific Python packaging: `pyproject.toml`, `uv`, `pytest`, `ruff`, `mypy`
- CI split: fast adapter/unit tests and slower integration/regression runs
- Coverage focus: adapter contracts, orchestrator determinism, vintage transitions, template correctness
- No custom formula compiler — environmental policy logic is Python code in template modules, not YAML formula strings

### Data Contracts

- Input: OpenFisca outputs (CSV/Parquet), synthetic populations, environmental datasets (emission factors, energy consumption)
- Output: yearly panel datasets, scenario comparison tables, indicator exports
- Contract failures are explicit, field-level, and blocking
- Adapter interface defines the computation contract boundary

### Dynamic Execution Semantics

- Baseline and reform scenarios run over 10+ years.
- Each year is explicit (`t`, `t+1`, ..., `t+n`), with deterministic carry-forward rules.
- Vintage states are updated through registered transition step functions.
- Randomness is seed-controlled and logged in manifests.
- Orchestrator step pipeline is the extension point for Phase 2+ capabilities.

### Reproducibility & Governance

- Every run records: OpenFisca version, adapter version, scenario version, data hashes, seeds, assumptions, step pipeline configuration.
- Cross-machine reproducibility uses documented tolerances where floating point differs.
- Lineage links yearly sub-runs to parent scenario runs.
- Manifests are JSON, machine-readable, Git-diffable.

### Delivery Sequence

1. Computation adapter + OpenFisca integration (simplified EPIC-1).
2. Carbon-tax + subsidy templates with baseline/reform comparison.
3. Dynamic orchestrator (pluggable step pipeline) + vintage module MVP.
4. Indicator layer and manifest lineage hardening.
5. Early no-code GUI workflow for analyst scenario operations.

### Phase 2+ Architecture Extensions

- **Behavioral responses:** New orchestrator step that applies elasticities between yearly computation runs (proven pattern from PolicyEngine).
- **System dynamics bridge:** Aggregate stock-flow outputs derived from microsimulation vintage tracking results.
- **Alternative computation backends:** Swap adapter implementations without changing orchestrator or indicator layers.

## Deployment & GUI Architecture (2026-02-27)

### Deployment Decision

The no-code GUI (EPIC-6) will be a web application with a React/TypeScript frontend and a FastAPI Python backend, deployed on a Hetzner VPS using Kamal 2 (Docker-based deployment tool). The MVP is deployed from day one to enable sharing with colleagues (2-10 users).

### Rationale

- **Same stack for MVP and future phases** — no throwaway prototype. The MVP GUI uses the same React + Shadcn/ui + Tailwind + FastAPI stack specified in the UX design document. Phase 3 (public web app) extends rather than replaces.
- **Hetzner** chosen for: best price/performance in Europe (~3.29 EUR/month for CX22), EU datacenter (Germany), GDPR compliance, not subject to US Cloud Act.
- **Kamal 2** chosen for: zero-downtime Docker deployments via SSH, built-in Traefik reverse proxy with automatic HTTPS, single YAML config file, language-agnostic (works with Python, Node, any Docker image), rollback in one command. Created by DHH (Rails creator), standard in Rails 8, but fully framework-agnostic.
- **Provider-agnostic** — Kamal deploys to any Linux server via SSH. Migrating to a different host (Scaleway, OVH, or a SecNumCloud provider) means changing one IP address in the config.
- **File-based storage works natively** — real persistent disk on the VPS, no need to adapt code for S3/object storage. Standard `open()` / `pd.read_parquet()` calls work as-is.

### Monorepo Structure

```
reformlab/
  src/                        ← Python backend (FastAPI API + core library)
  frontend/                   ← React/TypeScript (Vite + Shadcn/ui + Tailwind)
  tests/
  Dockerfile                  ← Backend container definition
  frontend/Dockerfile         ← Frontend container (nginx serving build)
  config/
    deploy.yml                ← Kamal deployment configuration
  .github/workflows/
    deploy.yml                ← GitHub Actions auto-deploy on push
  .kamal/
    secrets                   ← Encrypted secrets for Kamal
  pyproject.toml
```

Both frontend and backend live in the same repository. Kamal manages both as separate services on the same Hetzner server.

### Deployment Topology

```
┌─────────────────────────────────────────────────────┐
│  GitHub Repository (monorepo)                       │
│  push to master                                     │
└──────────────────────┬──────────────────────────────┘
                       │
                GitHub Actions
                runs: kamal deploy
                       │
                    SSH + Docker
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  Hetzner CX22 (Germany)                             │
│  2 vCPU, 4 GB RAM, 40 GB SSD                       │
│                                                     │
│  ┌───────────────────────────────────────────┐      │
│  │  Traefik (reverse proxy, auto HTTPS)      │      │
│  │  api.reformlab.fr → backend:8000          │      │
│  │  app.reformlab.fr → frontend:8080         │      │
│  └───────────────────────────────────────────┘      │
│                                                     │
│  ┌─────────────────┐   ┌──────────────────┐         │
│  │  FastAPI         │   │  nginx + React   │         │
│  │  (backend)       │   │  (frontend)      │         │
│  │  :8000           │   │  :8080           │         │
│  └────────┬────────┘   └──────────────────┘         │
│           │                                         │
│           ▼                                         │
│  ┌──────────────────┐                               │
│  │  /data/reformlab  │                               │
│  │  (CSV/Parquet/    │                               │
│  │   YAML/JSON)      │                               │
│  └──────────────────┘                               │
└─────────────────────────────────────────────────────┘
```

### Frontend Stack

As specified in the UX design document:

- React 18+ with TypeScript
- Vite (build tooling)
- Shadcn/ui + Radix UI (component library)
- Tailwind CSS v4 (styling with design tokens)
- Recharts/Nivo (simulation charts)
- React Flow (lineage DAG visualization)
- React Hook Form + Zod (form handling)

Served as a static build by an nginx container. Calls the backend API via HTTPS.

### Backend Stack

- FastAPI (REST API)
- Python 3.13+ (same as core library)
- uvicorn (ASGI server)
- The FastAPI layer exposes the existing Python API (orchestrator, scenarios, indicators, governance) as HTTP endpoints

### Deployment Stack

- **Kamal 2** — Docker-based deployment tool (SSH + Docker, no Kubernetes)
- **Traefik** — reverse proxy with automatic Let's Encrypt HTTPS certificates (managed by Kamal)
- **Docker** — containerization for both frontend and backend
- **GitHub Actions** — CI/CD trigger on push to master, calls `kamal deploy`
- **GitHub Container Registry (ghcr.io)** — Docker image storage

### Data Storage (MVP)

File-based, no database:

- **Scenario configs:** YAML/JSON files on server disk (`/data/reformlab/`)
- **Run outputs:** CSV/Parquet on server disk
- **Run manifests:** JSON on server disk
- **Scenario registry:** File-based (already implemented in EPIC-2)

Docker volume mount maps `/data/reformlab` on the host to `/app/data` in the backend container. Data persists across deployments and container restarts. Sufficient for 2-10 users working with open/public data. If multi-user concurrent writes become an issue in Phase 3, migrate to SQLite or PostgreSQL — the file-based contract layer makes this a contained change.

### Authentication (MVP)

Simple shared-password authentication via FastAPI middleware:

- Single shared password stored as a Kamal secret (encrypted in `.kamal/secrets`, injected as environment variable)
- FastAPI middleware checks password on every API request
- Frontend shows a password prompt on first access, stores the token in browser session
- No user accounts, no OAuth, no database — appropriate for 2-10 trusted colleagues

Phase 3 (public web app with Claire persona) will require proper user authentication (OAuth or similar). This is a separate architectural decision at that point.

### Cost Estimate

| Service | Monthly Cost |
| --- | --- |
| Hetzner CX22 (2 vCPU, 4 GB RAM, 40 GB SSD) | 3.29 EUR |
| Domain name (annual, amortized) | ~1 EUR |
| **Total** | **~4.29 EUR/month** |

### Sovereignty & Compliance Positioning

- Hosted on Hetzner, European provider (Germany), EU datacenter
- GDPR compliant, data stays in EU, no transfer outside EU
- Not subject to US Cloud Act or other extra-territorial legislation
- Application uses exclusively open public data (INSEE, Eurostat, synthetic populations)
- SecNumCloud is not required for open public data under the French "Cloud au Centre" doctrine
- If SecNumCloud becomes required (e.g., restricted microdata handling), Kamal deploys to any Linux server via SSH — migrate by changing the target IP to a SecNumCloud-qualified provider (Scalingo on Outscale `osc-secnum-fr1`, or Clever Cloud on Cloud Temple SecNumCloud zone). Application code unchanged.

### Migration Path to Phase 3

Kamal is provider-agnostic. All migrations below require zero application code changes:

1. **More users / more power:** Upgrade Hetzner server (CX32 at 5.39 EUR, CX42 at 17.49 EUR). Change server spec in Hetzner console, redeploy.
2. **French sovereignty required:** Move to Scaleway or OVH VPS in Paris. Change one IP in `config/deploy.yml`, run `kamal setup && kamal deploy`.
3. **SecNumCloud required:** Deploy to a server on Scalingo/Outscale `osc-secnum-fr1` or Clever Cloud on Cloud Temple SecNumCloud zone. Same Kamal config, different target.
4. **User accounts:** Replace shared-password middleware with OAuth/OIDC. Add user table (SQLite or PostgreSQL).
5. **Horizontal scaling:** Kamal supports multi-server deployment. Add server IPs to `config/deploy.yml` and Kamal load-balances across them via Traefik.

## API Design — FastAPI Server Layer (2026-02-28)

### Design Principle

The FastAPI server is a **thin HTTP facade** over the existing Python API in `src/reformlab/interfaces/api.py`. No business logic lives in the server layer. Every route handler delegates to functions that already work: `run_scenario()`, `create_scenario()`, `list_scenarios()`, `get_scenario()`, `clone_scenario()`, `check_memory_requirements()`, and `SimulationResult` methods (`indicators()`, `export_csv()`, `export_parquet()`).

### Package Structure

```
src/reformlab/server/
├── __init__.py
├── app.py              ← FastAPI app factory (create_app())
├── auth.py             ← Shared-password middleware
├── models.py           ← Pydantic v2 request/response models
├── dependencies.py     ← Dependency injection (adapter, result cache)
└── routes/
    ├── __init__.py
    ├── scenarios.py    ← Scenario CRUD
    ├── runs.py         ← Simulation execution
    ├── indicators.py   ← Indicator computation
    ├── exports.py      ← File export/download
    ├── templates.py    ← Template listing
    └── populations.py  ← Population dataset listing
```

### Dependencies

Add as optional extra in `pyproject.toml`:

```toml
[project.optional-dependencies]
server = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "python-multipart>=0.0.9",
]
```

Install with `uv sync --extra server`. Pydantic v2 is already a transitive dependency of FastAPI.

### App Factory

`src/reformlab/server/app.py` exposes `create_app() -> FastAPI`:

```python
def create_app() -> FastAPI:
    app = FastAPI(
        title="ReformLab API",
        version=reformlab.__version__,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    # CORS must be added BEFORE auth middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),  # localhost:5173 + production
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Auth middleware (skips /api/auth/login and /api/docs)
    app.add_middleware(AuthMiddleware)

    # Register route groups
    app.include_router(auth_router,        prefix="/api/auth")
    app.include_router(scenarios_router,   prefix="/api/scenarios")
    app.include_router(runs_router,        prefix="/api/runs")
    app.include_router(indicators_router,  prefix="/api/indicators")
    app.include_router(exports_router,     prefix="/api/exports")
    app.include_router(templates_router,   prefix="/api/templates")
    app.include_router(populations_router, prefix="/api/populations")

    return app
```

Run with: `uvicorn src.reformlab.server.app:create_app --factory --host 0.0.0.0 --port 8000`

Dev mode: `uvicorn src.reformlab.server.app:create_app --factory --reload --port 8000`

### Route Contracts

#### Authentication

| Method | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| `POST` | `/api/auth/login` | `{ "password": "string" }` | `{ "token": "string" }` | 200 or 401 |

- Password validated against `REFORMLAB_PASSWORD` env var.
- Token is a random hex string stored server-side in a session set.
- Subsequent requests pass token via `Authorization: Bearer <token>` header.
- No expiry for MVP. Phase 3 replaces with OAuth/OIDC.

#### Scenarios

| Method | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| `GET` | `/api/scenarios` | — | `{ "scenarios": ["name1", ...] }` | 200 |
| `GET` | `/api/scenarios/{name}` | — | `ScenarioResponse` | 200 or 404 |
| `POST` | `/api/scenarios` | `CreateScenarioRequest` | `{ "version_id": "string" }` | 201 or 422 |
| `POST` | `/api/scenarios/{name}/clone` | `{ "new_name": "string" }` | `ScenarioResponse` | 201 or 404 |

Delegates to: `list_scenarios()`, `get_scenario(name)`, `create_scenario(scenario, name, register=True)`, `clone_scenario(name, new_name=new_name)`.

#### Simulation Runs

| Method | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| `POST` | `/api/runs` | `RunRequest` | `RunResponse` | 200 or 422/500 |
| `POST` | `/api/runs/memory-check` | `MemoryCheckRequest` | `MemoryCheckResponse` | 200 |

**Execution model (MVP):** `POST /api/runs` is **synchronous** — it blocks until the simulation completes and returns the full result. This is acceptable because:
- Target run time is <10s for 100k households (NFR1).
- MVP serves 2-10 users, not concurrent load.
- Frontend shows a loading spinner during the request.

**Upgrade path:** If runs exceed 10s, switch to polling: `POST /api/runs` returns `{ "run_id": "..." }` immediately, `GET /api/runs/{run_id}/status` returns progress, `GET /api/runs/{run_id}/result` returns the completed result.

#### Indicators

| Method | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| `POST` | `/api/indicators/{type}` | `IndicatorRequest` | `IndicatorResponse` | 200 or 422 |
| `POST` | `/api/comparison` | `ComparisonRequest` | `IndicatorResponse` | 200 or 422 |

`{type}` is one of: `distributional`, `geographic`, `welfare`, `fiscal`.

Delegates to: `cached_result.indicators(type, **kwargs)`.

For welfare indicators and comparison, the request must reference both a baseline and reform `run_id` from the result cache.

#### Exports

| Method | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| `POST` | `/api/exports/csv` | `{ "run_id": "string" }` | `StreamingResponse` (file download) | 200 or 404 |
| `POST` | `/api/exports/parquet` | `{ "run_id": "string" }` | `StreamingResponse` (file download) | 200 or 404 |

Delegates to: `cached_result.export_csv(tmp_path)` and `cached_result.export_parquet(tmp_path)`.

Returns file as `StreamingResponse` with appropriate `Content-Disposition` header.

#### Templates

| Method | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| `GET` | `/api/templates` | — | `{ "templates": [TemplateListItem, ...] }` | 200 |
| `GET` | `/api/templates/{name}` | — | `TemplateDetailResponse` | 200 or 404 |

Lists available policy templates (carbon tax, subsidy, rebate, feebate) with their default parameters and parameter groups.

#### Populations

| Method | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| `GET` | `/api/populations` | — | `{ "populations": [PopulationItem, ...] }` | 200 |

Lists available population datasets by scanning the data directory for CSV/Parquet files.

### Pydantic v2 Request/Response Models

All models in `src/reformlab/server/models.py`. Key patterns:

**Frozen dataclass → Pydantic model translation:** The domain layer uses frozen dataclasses (`ScenarioConfig`, `SimulationResult`). The server layer creates parallel Pydantic models for HTTP serialization. Route handlers translate between them.

```python
# Request models

class LoginRequest(BaseModel):
    password: str

class RunRequest(BaseModel):
    template_name: str
    parameters: dict[str, Any]
    start_year: int
    end_year: int
    population_id: str | None = None
    seed: int | None = None
    baseline_id: str | None = None

class MemoryCheckRequest(BaseModel):
    template_name: str
    parameters: dict[str, Any] = {}
    start_year: int
    end_year: int
    population_id: str | None = None

class IndicatorRequest(BaseModel):
    run_id: str
    income_field: str = "income"
    by_year: bool = False

class ComparisonRequest(BaseModel):
    baseline_run_id: str
    reform_run_id: str
    welfare_field: str = "disposable_income"
    threshold: float = 0.0

class ExportRequest(BaseModel):
    run_id: str

class CreateScenarioRequest(BaseModel):
    name: str
    policy_type: str           # "carbon_tax" | "subsidy" | "rebate" | "feebate"
    parameters: dict[str, Any]
    start_year: int
    end_year: int
    description: str = ""
    baseline_ref: str | None = None

class CloneRequest(BaseModel):
    new_name: str
```

```python
# Response models

class LoginResponse(BaseModel):
    token: str

class RunResponse(BaseModel):
    run_id: str
    success: bool
    scenario_id: str
    years: list[int]
    row_count: int
    manifest_id: str

class MemoryCheckResponse(BaseModel):
    should_warn: bool
    estimated_gb: float
    available_gb: float
    message: str

class IndicatorResponse(BaseModel):
    indicator_type: str
    data: dict[str, list[Any]]     # PyArrow table.to_pydict()
    metadata: dict[str, Any]
    warnings: list[str]
    excluded_count: int

class ScenarioResponse(BaseModel):
    name: str
    policy_type: str
    description: str
    version: str
    parameters: dict[str, Any]
    year_schedule: dict[str, int]  # {"start_year": N, "end_year": M}
    baseline_ref: str | None = None

class TemplateListItem(BaseModel):
    id: str
    name: str
    type: str
    parameter_count: int
    description: str
    parameter_groups: list[str]

class TemplateDetailResponse(TemplateListItem):
    default_parameters: dict[str, Any]

class PopulationItem(BaseModel):
    id: str
    name: str
    households: int
    source: str
    year: int

class ErrorResponse(BaseModel):
    error: str
    what: str
    why: str
    fix: str
    status_code: int
```

### Serialization Rules

- **PyArrow `pa.Table` → JSON:** `table.to_pydict()` produces `dict[str, list]`. This is the canonical wire format for panel data and indicator tables.
- **`Path` objects:** Serialize as strings via Pydantic `model_serializer`.
- **`datetime` objects:** Serialize as ISO 8601 strings.
- **Frozen dataclasses:** Converted to Pydantic models at the route handler boundary. No `dataclasses.asdict()` in responses — explicit Pydantic field mapping.

### Result Cache

Simulation results contain large PyArrow tables. Re-serializing on every indicator/export request is wasteful.

```python
class ResultCache:
    """In-memory LRU cache for SimulationResult objects."""

    def __init__(self, max_size: int = 10):
        self._cache: OrderedDict[str, SimulationResult] = OrderedDict()
        self._max_size = max_size

    def store(self, run_id: str, result: SimulationResult) -> None:
        if len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)  # Evict oldest
        self._cache[run_id] = result

    def get(self, run_id: str) -> SimulationResult | None:
        result = self._cache.get(run_id)
        if result is not None:
            self._cache.move_to_end(run_id)  # Mark as recently used
        return result
```

- `POST /api/runs` stores the result under a generated `run_id` (UUID4).
- `POST /api/indicators/{type}` and `POST /api/exports/*` reference `run_id` to retrieve cached results.
- Max 10 entries. LRU eviction. No disk persistence — results are ephemeral across server restarts.

### Dependency Injection

```python
# src/reformlab/server/dependencies.py

# Global singletons (created once in app factory, injected via Depends)
_result_cache = ResultCache(max_size=10)
_adapter: ComputationAdapter | None = None

def get_result_cache() -> ResultCache:
    return _result_cache

def get_adapter() -> ComputationAdapter:
    global _adapter
    if _adapter is None:
        # Initialize default adapter (MockAdapter in dev, OpenFiscaAdapter in prod)
        _adapter = _create_adapter()
    return _adapter
```

Route handlers use `Depends(get_result_cache)` and `Depends(get_adapter)`.

### Authentication Middleware

```python
# src/reformlab/server/auth.py

class AuthMiddleware(BaseHTTPMiddleware):
    """Shared-password auth for MVP (2-10 trusted colleagues)."""

    SKIP_PATHS = {"/api/auth/login", "/api/docs", "/api/openapi.json"}

    async def dispatch(self, request, call_next):
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        token = request.headers.get("Authorization", "").removeprefix("Bearer ")
        if not token or token not in _active_sessions:
            return JSONResponse(status_code=401, content={"error": "Unauthorized"})

        return await call_next(request)
```

- `_active_sessions` is a `set[str]` stored in-memory.
- `POST /api/auth/login` validates password against `os.environ["REFORMLAB_PASSWORD"]`, generates a random token via `secrets.token_hex(32)`, adds it to `_active_sessions`, returns it.
- No expiry for MVP. Server restart clears all sessions (users re-enter password).

### Error Mapping

Python API exceptions map to HTTP responses:

| Python Exception | HTTP Status | Error Response |
|-----------------|-------------|----------------|
| `ConfigurationError` | 422 Unprocessable Entity | `{ "error": "Configuration error", "what": field_path, "why": expected vs actual, "fix": guidance }` |
| `ValidationErrors` | 422 Unprocessable Entity | `{ "error": "Validation failed", "what": "N issues found", "why": issues list, "fix": per-issue guidance }` |
| `SimulationError` | 500 Internal Server Error | `{ "error": "Simulation error", "what": message, "why": cause, "fix": guidance }` |
| `RegistryError` | 404 Not Found | `{ "error": "Not found", "what": summary, "why": reason, "fix": guidance }` |
| `MemoryWarning` | 200 (with `should_warn: true`) | Not an error — returned as data in `MemoryCheckResponse` |

Implement via FastAPI exception handlers registered in `create_app()`:

```python
@app.exception_handler(ConfigurationError)
async def configuration_error_handler(request, exc):
    return JSONResponse(status_code=422, content={
        "error": "Configuration error",
        "what": exc.field_path,
        "why": f"Expected {exc.expected}, got {exc.actual!r}",
        "fix": exc.fix or f"Provide a valid {exc.expected}",
        "status_code": 422,
    })
```

### CORS Configuration

```python
def _cors_origins() -> list[str]:
    origins = ["http://localhost:5173"]  # Vite dev server
    extra = os.environ.get("REFORMLAB_CORS_ORIGINS", "")
    if extra:
        origins.extend(o.strip() for o in extra.split(",") if o.strip())
    return origins
```

Production adds `https://app.reformlab.fr` via `REFORMLAB_CORS_ORIGINS` env var.

### Vite Dev Proxy

Add to `frontend/vite.config.ts`:

```typescript
server: {
  proxy: {
    "/api": {
      target: "http://localhost:8000",
      changeOrigin: true,
    },
  },
}
```

Frontend calls `/api/scenarios` (relative) in development. Vite proxies to the FastAPI backend. In production, Traefik routes by subdomain (`api.reformlab.fr` vs `app.reformlab.fr`).

### Data Flow Summary

```
Frontend (React)
    │
    ├─ POST /api/runs { template, params, years }
    │       ↓
    │  RunRequest → ScenarioConfig → run_scenario(config, adapter)
    │       ↓
    │  SimulationResult stored in ResultCache[run_id]
    │       ↓
    │  RunResponse { run_id, success, years, row_count }
    │
    ├─ POST /api/indicators/distributional { run_id }
    │       ↓
    │  ResultCache.get(run_id) → result.indicators("distributional")
    │       ↓
    │  IndicatorResult.to_table().to_pydict() → IndicatorResponse
    │
    ├─ POST /api/comparison { baseline_run_id, reform_run_id }
    │       ↓
    │  baseline = cache.get(baseline_run_id)
    │  reform = cache.get(reform_run_id)
    │  baseline.indicators("welfare", reform_result=reform)
    │       ↓
    │  IndicatorResponse
    │
    └─ POST /api/exports/csv { run_id }
            ↓
        result.export_csv(tmp) → StreamingResponse
```

### Code Quality Standards

- `from __future__ import annotations` at top of every server module.
- Pydantic v2 conventions: `model_validate()`, `model_dump()`, `ConfigDict`.
- `mypy --strict` must pass on all server code.
- `ruff` compliance (E, F, I, W rules).
- No direct OpenFisca imports in server code — adapter protocol only.
- Structured logging with `logging.getLogger(__name__)`.


]]></file>
<file id="9e4374e5" path="_bmad-output/planning-artifacts/epics.md" label="EPIC"><![CDATA[

---
title: ReformLab — Epics and Stories
project: ReformLab
description: Single source of truth for all epics, stories, and acceptance criteria
date: 2026-03-01
source_documents:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md
  - _bmad-output/implementation-artifacts/sprint-status.yaml
---

# Epics and Stories

Single source of truth for all epics and stories across the project. For detailed dev notes, subtask checklists, and agent records, see individual story files in `_bmad-output/implementation-artifacts/`.

## Epic Index

| Epic | Title | Status | Stories |
|------|-------|--------|---------|
| EPIC-1 | Computation Adapter and Data Layer | done | 8 |
| EPIC-2 | Scenario Templates and Registry | done | 7 |
| EPIC-3 | Step-Pluggable Dynamic Orchestrator and Vintage Tracking | done | 7 |
| EPIC-4 | Indicators and Scenario Comparison | done | 6 |
| EPIC-5 | Governance and Reproducibility | done | 6 |
| EPIC-6 | Interfaces (Python API, Notebooks, Early No-Code GUI) | done | 7 |
| EPIC-7 | Trusted Outputs and External Pilot Validation | done | 5 |
| EPIC-8 | Post-Phase-1 Validation Spikes | done | 2 |
| EPIC-9 | OpenFisca Adapter Hardening | backlog | 5 |

## Conventions

- **Priority:** `P0` (must ship), `P1` (ship if capacity allows after P0)
- **Size:** Story points (`SP`) on Fibonacci scale (1, 2, 3, 5, 8, 13)
- **Types:** `Story`, `Task`, `Spike`
- **Done:** Acceptance criteria pass and tests are in CI
- **Story files:** `_bmad-output/implementation-artifacts/{epic}-{story-slug}.md`

---

## EPIC-1: Computation Adapter and Data Layer

**User outcome:** Analyst can connect OpenFisca outputs and open datasets to the framework with validated data contracts.

**Status:** done

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-101 | Story | P0 | 5 | Define ComputationAdapter interface and OpenFiscaAdapter implementation | done | FR1, FR2, FR3 |
| BKL-102 | Story | P0 | 5 | Implement CSV/Parquet ingestion for OpenFisca outputs and population data | done | FR1, FR3, NFR14 |
| BKL-103 | Story | P0 | 5 | Build input/output mapping configuration for OpenFisca variable names | done | FR3, FR4, NFR4 |
| BKL-104 | Story | P0 | 5 | Implement open-data ingestion pipeline (synthetic population, emission factors) | done | FR5, FR6 |
| BKL-105 | Task | P0 | 3 | Add data-quality checks with blocking field-level errors at adapter boundary | done | FR4, FR27, NFR4 |
| BKL-106 | Story | P1 | 5 | Add direct OpenFisca API orchestration mode (version-pinned) | done | FR2, NFR15 |
| BKL-107 | Task | P0 | 2 | Create compatibility matrix for supported OpenFisca versions | done | NFR15, NFR21 |
| BKL-108 | Task | P0 | 3 | Set up project scaffold, dev environment, and CI smoke pipeline | done | NFR18, NFR19 |

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

## EPIC-2: Scenario Templates and Registry

**User outcome:** Analyst can define, version, and reuse environmental policy scenarios without writing code.

**Status:** done

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-201 | Story | P0 | 5 | Define scenario template schema (baseline + reform overrides) | done | FR7, FR8, FR12 |
| BKL-202 | Story | P0 | 8 | Implement carbon-tax template pack (4-5 variants) | done | FR7, FR10, FR11 |
| BKL-203 | Story | P0 | 5 | Implement subsidy/rebate/feebate template pack | done | FR7, FR11 |
| BKL-204 | Story | P0 | 5 | Build scenario registry with immutable version IDs | done | FR9, FR28 |
| BKL-205 | Story | P0 | 3 | Implement scenario cloning and baseline/reform linking | done | FR8, FR9 |
| BKL-206 | Task | P1 | 3 | Add schema migration helper for template version changes | done | FR9, NFR21 |
| BKL-207 | Story | P0 | 5 | Implement YAML/JSON workflow configuration with schema validation | done | FR31, NFR4, NFR20 |

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

## EPIC-3: Step-Pluggable Dynamic Orchestrator and Vintage Tracking

**User outcome:** Analyst can run multi-year projections with vintage tracking and get year-by-year panel results.

**Status:** done

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-301 | Story | P0 | 8 | Implement yearly loop orchestrator with step pipeline architecture | done | FR13, FR18 |
| BKL-302 | Story | P0 | 5 | Define orchestrator step interface and step registration mechanism | done | FR14, FR16 |
| BKL-303 | Story | P0 | 5 | Implement carry-forward step (deterministic state updates between years) | done | FR14, FR17, NFR10 |
| BKL-304 | Story | P0 | 8 | Implement vintage transition step for one asset class (vehicle or heating) | done | FR15, FR16 |
| BKL-305 | Story | P0 | 5 | Integrate ComputationAdapter calls into orchestrator yearly loop | done | FR13, FR2 |
| BKL-306 | Task | P0 | 3 | Log seed controls, step execution order, and adapter version per yearly step | done | FR17, NFR8 |
| BKL-307 | Story | P0 | 5 | Produce scenario-year panel output dataset | done | FR18, FR33 |

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

## EPIC-4: Indicators and Scenario Comparison

**User outcome:** Analyst can compute and compare distributional, welfare, and fiscal indicators across scenarios.

**Status:** done

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-401 | Story | P0 | 5 | Implement distributional indicators by income decile | done | FR19 |
| BKL-402 | Story | P0 | 3 | Implement geographic aggregation indicators | done | FR20 |
| BKL-403 | Story | P0 | 5 | Implement welfare indicators (winners/losers, net changes) | done | FR21 |
| BKL-404 | Story | P0 | 5 | Implement fiscal indicators (annual and cumulative) | done | FR22 |
| BKL-405 | Story | P0 | 5 | Implement scenario comparison tables across runs | done | FR24, FR33 |
| BKL-406 | Story | P1 | 5 | Implement custom derived indicator formulas | done | FR23 |

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

## EPIC-5: Governance and Reproducibility

**User outcome:** Analyst can trust and reproduce any simulation run through immutable manifests and lineage tracking.

**Status:** done (BKL-502, BKL-504, and BKL-505 are partial stubs — see [Phase 1 retrospective GAP 3](../implementation-artifacts/phase-1-retro-2026-02-28.md))

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-501 | Story | P0 | 5 | Define immutable run manifest schema v1 | done | FR25, NFR9 |
| BKL-502 | Story | P0 | 5 | Capture assumptions/mappings/parameters in manifests | done | FR26, FR27 |
| BKL-503 | Story | P0 | 5 | Implement run lineage graph (scenario run -> yearly child runs) | done | FR29 |
| BKL-504 | Task | P0 | 3 | Hash input/output artifacts and store in manifest | done | FR25, NFR12 |
| BKL-505 | Story | P0 | 5 | Add reproducibility check harness for deterministic reruns | done | NFR6, NFR7 |
| BKL-506 | Task | P1 | 3 | Add warning system for unvalidated templates/configs | done | FR27 |

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

## EPIC-6: Interfaces (Python API, Notebooks, Early No-Code GUI)

**User outcome:** User can operate the full analysis workflow from Python API, notebooks, or a no-code GUI.

**Status:** done

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-601 | Story | P0 | 5 | Implement stable Python API for run orchestration | done | FR30, NFR16 |
| BKL-602 | Story | P0 | 5 | Build quickstart notebook | done | FR34, NFR19 |
| BKL-603 | Story | P0 | 5 | Build advanced notebook (multi-year + vintage + comparison) | done | FR30, FR35 |
| BKL-604a | Story | P0 | 3 | Build static GUI prototype | done | FR32 |
| BKL-604b | Story | P0 | 5 | Wire GUI prototype to FastAPI backend | done | FR32 |
| BKL-605 | Task | P0 | 3 | Add export actions in API/GUI for CSV/Parquet outputs | done | FR33 |
| BKL-606 | Task | P1 | 3 | Improve operational error UX | done | FR4, FR27 |

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

## EPIC-7: Trusted Outputs and External Pilot Validation

**User outcome:** External pilot user can validate simulation credibility against published benchmarks and run the carbon-tax workflow independently.

**Status:** done

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-701 | Story | P0 | 5 | Verify simulation outputs against published benchmarks (100k households) | done | NFR1, NFR5 |
| BKL-702 | Task | P0 | 3 | System warns analyst before exceeding memory limits | done | NFR3 |
| BKL-703 | Task | P0 | 3 | Enforce CI quality gates | done | NFR18, NFR20 |
| BKL-704 | Story | P0 | 5 | External pilot user can run complete carbon-tax workflow | done | FR35, NFR19 |
| BKL-705 | Task | P0 | 3 | Define Phase 1 exit checklist and pilot sign-off criteria | done | PRD go/no-go |

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

## EPIC-8: Post-Phase-1 Validation Spikes

**User outcome:** Platform developers confirm that the adapter layer works end-to-end with real OpenFisca and at production scale.

**Status:** done

Priority and SP are not assigned for post-Phase-1 spikes.

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|------|-------|--------|----------|
| 8-1 | Spike | — | — | End-to-end OpenFisca integration spike | done | — |
| 8-2 | Story | — | — | Scale validation: 100k synthetic population benchmarks | done | NFR1, NFR3 |

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

**User outcome:** Adapter handles real-world OpenFisca entity models, variable periodicities, and multi-entity outputs correctly.

**Status:** backlog (follow-ups from spike 8-1 findings)

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

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 9.1

#### Acceptance Criteria

- Given output variables that return per-entity arrays (e.g., per-menage, per-foyer_fiscal), when the adapter processes results, then arrays are correctly mapped to their respective entity tables.
- Given a variable defined on `foyer_fiscal` entity, when results are returned, then the output array length matches the number of foyers fiscaux, not the number of individuals.
- Given mixed-entity output variables, when processed, then each variable's values are stored in the correct entity-level result table with proper entity IDs.

---

### Story 9.3: Add variable periodicity handling

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 9.2

#### Acceptance Criteria

- Given variables with different periodicities (monthly, yearly), when `compute()` is called, then the adapter converts periods correctly before passing to OpenFisca.
- Given a monthly variable requested for a yearly period, when computed, then the adapter handles period conversion according to OpenFisca conventions.
- Given an invalid period format, when passed to the adapter, then a clear error identifies the expected format.

---

### Story 9.4: Define population data 4-entity format

**Status:** backlog
**Priority:** P0
**Estimate:** 8

**Dependencies:** Story 9.2

#### Acceptance Criteria

- Given the French tax-benefit model's 4 entities (individu, menage, famille, foyer_fiscal), when a population dataset is loaded, then all entity relationships are preserved and passable to `SimulationBuilder`.
- Given a population with membership arrays for all 4 entities, when built via `SimulationBuilder`, then entity group memberships are correctly assigned.
- Given a population dataset missing a required entity relationship, when loaded, then validation fails with a clear error identifying the missing relationship.

---

### Story 9.5: OpenFisca-France reference test suite

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 9.3, Story 9.4

#### Acceptance Criteria

- Given a set of known French tax-benefit scenarios with published expected values, when run through the adapter, then computed values match reference values within documented tolerances.
- Given the reference test suite, when run in CI, then all tests pass and tolerance thresholds are documented.
- Given a new OpenFisca-France version, when the reference suite is run, then regressions are detected and reported.


]]></file>
<file id="bc34e66e" path="_bmad-output/implementation-artifacts/9-4-define-population-data-4-entity-format.md" label="STORY FILE"><![CDATA[

# Story 9.4: Define Population Data 4-Entity Format

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **platform developer integrating OpenFisca-France**,
I want the adapter to support a PopulationData format that expresses the full 4-entity model (individu, famille, foyer_fiscal, menage) with entity membership relationships,
so that multi-person populations with specific household compositions (couples, families) can be passed to `SimulationBuilder.build_from_entities()` with correct group entity role assignments — instead of relying on OpenFisca's single-person auto-creation.

## Context & Motivation

OpenFisca-France operates on a **4-entity model**:

| Entity Key | Plural | Type | Role Keys for `build_from_entities()` |
|---|---|---|---|
| `individu` | `individus` | Person (singular) | N/A — no roles |
| `famille` | `familles` | Group | `parents`, `enfants` |
| `foyer_fiscal` | `foyers_fiscaux` | Group | `declarants`, `personnes_a_charge` |
| `menage` | `menages` | Group | `personne_de_reference`, `conjoint`, `enfants`, `autres` |

**The current adapter (`_population_to_entity_dict()`) does NOT handle entity relationships.** It treats every column in every PopulationData table as a variable value wrapped in a period dict (`{period_str: value}`). This works for single-person populations because OpenFisca auto-creates group entities — but **it fails silently or crashes for multi-person populations** that require explicit group memberships (e.g., a married couple filing joint taxes in one `foyer_fiscal`, or a family with children in one `famille`).

**Real-world consequence:** Without this story, any population with more than one person per household requires hand-building the entity dict outside the adapter (as the integration tests currently do), bypassing the adapter's validation, period-wrapping, and policy parameter injection. This defeats the purpose of the adapter abstraction.

**What `build_from_entities()` expects for group entities:**

```python
{
    "individus": {
        "individu_0": {"salaire_de_base": {"2024": 30000.0}},
        "individu_1": {"salaire_de_base": {"2024": 0.0}},
    },
    "familles": {
        "famille_0": {"parents": ["individu_0", "individu_1"]},
    },
    "foyers_fiscaux": {
        "foyer_0": {"declarants": ["individu_0", "individu_1"]},
    },
    "menages": {
        "menage_0": {
            "personne_de_reference": ["individu_0"],
            "conjoint": ["individu_1"],
        },
    },
}
```

**The role dict keys come from `role.plural or role.key`** (see Dev Notes for details). This is the critical mapping that must be correct for `build_from_entities()` to assign group memberships properly.

**Source:** Spike 8-1 findings, recommended follow-up #4: "Update PopulationData format for OpenFisca-France — Define a standard way to express the 4-entity model with role assignments in PopulationData." [Source: `_bmad-output/implementation-artifacts/spike-findings-8-1-openfisca-integration.md`, line 106]

## Acceptance Criteria

1. **AC-1: 4-entity PopulationData format** — Given the French tax-benefit model's 4 entities (individu, menage, famille, foyer_fiscal), when a population dataset is loaded with membership columns (`{group_entity_key}_id` and `{group_entity_key}_role` on the person entity table), then `_population_to_entity_dict()` produces a valid entity dict with all entity relationships preserved and passable to `SimulationBuilder.build_from_entities()`. Membership columns are excluded from period-wrapped variable values.

2. **AC-2: Group membership assignment** — Given a population with membership columns for all 3 group entities, when built via `SimulationBuilder.build_from_entities()`, then entity group memberships are correctly assigned — e.g., a married couple shares one `foyer_fiscal` with both persons as `declarants`, one `menage` with one `personne_de_reference` and one `conjoint`, and one `famille` with both as `parents`.

3. **AC-3: Missing relationship validation** — Given a population dataset where membership columns are partially present (e.g., `famille_id` exists but `foyer_fiscal_id` is missing, or `famille_id` exists without `famille_role`), when loaded, then validation fails with a clear `ApiMappingError` identifying the missing relationship columns and listing what is required.

4. **AC-4: Invalid role validation** — Given a population dataset with a role value that is not valid for the target entity (e.g., `menage_role="invalid_role"`), when validated, then an `ApiMappingError` is raised listing the invalid role value, the entity it belongs to, and the valid role values queried from the TBS.

5. **AC-5: Null membership value rejection** — Given a population dataset with a null (None/NaN) value in any membership column (`_id` or `_role`), when validated, then an `ApiMappingError` is raised identifying the column name, the row index, and the expected non-null value type.

6. **AC-6: Backward compatibility** — Given a population dataset WITHOUT membership columns (the existing common case — a person table with only variable columns), when `compute()` is called, then behavior is identical to the pre-change implementation — no regression. OpenFisca's auto-creation of group entities for single-person populations continues to work.

7. **AC-7: Group entity input variables** — Given a PopulationData with both membership columns on the person table AND separate group entity tables containing group-level input variables (e.g., a `menage` table with a `loyer` column), when `_population_to_entity_dict()` processes the data, then the group entity instances include both the role assignments (from membership columns) AND the period-wrapped variable values (from the group entity table).

## Tasks / Subtasks

- [ ] Task 1: Implement `_detect_membership_columns()` method (AC: #1, #3, #6)
  - [ ] 1.1 Add method to `OpenFiscaApiAdapter` that queries TBS for group entities (`entity.is_person == False`) and checks the person entity table for `{entity.key}_id` and `{entity.key}_role` columns
  - [ ] 1.2 Return a `dict[str, tuple[str, str]]` mapping group entity key to `(id_column_name, role_column_name)` — e.g., `{"famille": ("famille_id", "famille_role"), "foyer_fiscal": ("foyer_fiscal_id", "foyer_fiscal_role"), "menage": ("menage_id", "menage_role")}`. Return empty dict if NO membership columns are detected (→ backward-compatible old behavior)
  - [ ] 1.3 **All-or-nothing detection**: if ANY `{entity_key}_id` column is found on the person table, then ALL group entities must have complete `_id` AND `_role` column pairs. Missing pairs raise `ApiMappingError` with summary `"Incomplete entity membership columns"`, listing which columns are present and which are missing
  - [ ] 1.4 **Paired column check**: if `{entity_key}_id` exists but `{entity_key}_role` is missing (or vice versa), raise `ApiMappingError` with summary `"Unpaired membership column"` — both `_id` and `_role` are required for each group entity
  - [ ] 1.5 Unit tests with mock TBS: detect all 3 group entities, detect none (backward compat), detect partial (error), detect unpaired (error)

- [ ] Task 2: Implement `_resolve_valid_role_keys()` method (AC: #4)
  - [ ] 2.1 Add method that queries TBS group entity roles and builds a mapping: `dict[str, frozenset[str]]` — entity key → set of valid role keys (using `role.plural or role.key` to match what `build_from_entities()` expects)
  - [ ] 2.2 For OpenFisca-France, this produces: `{"famille": {"parents", "enfants"}, "foyer_fiscal": {"declarants", "personnes_a_charge"}, "menage": {"personne_de_reference", "conjoint", "enfants", "autres"}}`
  - [ ] 2.3 Unit tests with mock TBS entities and roles: verify correct role key resolution for each entity

- [ ] Task 3: Implement `_validate_entity_relationships()` method (AC: #3, #4, #5)
  - [ ] 3.1 Add validation method that takes the person entity table (`pa.Table`) and the detected membership columns dict, plus the valid role keys dict
  - [ ] 3.2 **Null check** (AC-5): for each membership column (`_id` and `_role`), check for null values. If found, raise `ApiMappingError` with summary `"Null value in membership column"`, the column name, and the first row index containing null. Use `pa.compute.is_null()` for efficient PyArrow null detection
  - [ ] 3.3 **Role validation** (AC-4): for each `{entity_key}_role` column, check that all values are in the valid role set for that entity. If invalid values found, raise `ApiMappingError` with summary `"Invalid role value"`, the actual value, the entity key, and the sorted list of valid role values
  - [ ] 3.4 Unit tests: null in `_id` column → error, null in `_role` column → error, invalid role value → error, all valid → passes silently

- [ ] Task 4: Refactor `_population_to_entity_dict()` for 4-entity format (AC: #1, #2, #6, #7)
  - [ ] 4.1 At the start of the method, call `_detect_membership_columns()` to determine format mode. If empty dict returned → execute existing code path unchanged (AC-6 backward compat)
  - [ ] 4.2 If membership columns detected, call `_resolve_valid_role_keys()` then `_validate_entity_relationships()`
  - [ ] 4.3 **Separate membership columns from variable columns**: build a set of all membership column names (all `_id` and `_role` columns). When iterating person table columns for period-wrapping, skip membership columns
  - [ ] 4.4 **Build person instances FROM PERSON TABLE ONLY**: iterate the person entity table (identified by finding the `population.tables` key matching `person_entity.key` or `person_entity.plural`) — NOT all tables in `population.tables`. Exclude membership columns from period-wrapping. The instance ID prefix is the original key used in `population.tables` (e.g. `"individu"` → `"individu_0"`, `"individu_1"`; `"individus"` → `"individus_0"`, `"individus_1"`). ⚠️ In 4-entity mode, the original all-tables loop is **replaced** by this step (person table) combined with Tasks 4.5 (group membership from membership columns) and 4.6 (group variables from group entity tables). Do NOT run the old all-tables loop and then also run 4-entity logic — this would double-write group entity entries.
  - [ ] 4.5 **Build group entity instances from membership columns**: for each group entity:
      - Read `{entity_key}_id` and `{entity_key}_role` columns from person table
      - Group person instance IDs by group ID
      - Within each group, sub-group person IDs by role key
      - Produce: `{"famille_0": {"parents": [f"{person_table_key}_0", f"{person_table_key}_1"]}}` — where `person_table_key` is the original key from `population.tables` (e.g. `"individu"` or `"individus"`). Person instance IDs MUST use the same prefix as Task 4.4.
      - Group instance IDs follow format `f"{entity_key}_{group_id_value}"` — e.g., if `famille_id` column has value `0`, instance ID is `"famille_0"`
  - [ ] 4.6 **Merge group entity table variables** (AC-7): if PopulationData contains a group entity table (e.g., `"menage"` or `"menages"` key in `population.tables`), iterate its columns and merge period-wrapped variable values into the corresponding group entity instances. Match group table row index to group instance by sorted order of distinct group IDs from the person table's `_id` column. ⚠️ Raise `ApiMappingError` if the group entity table row count doesn't match the number of distinct group IDs. ⚠️ **POSITIONAL MATCHING**: row 0 of the group entity table maps to the smallest distinct group ID, row 1 to the second-smallest, etc. This requires the group entity table rows to be ordered by ascending `{entity_key}_id` value — no automatic reordering is performed. If rows are in a different order, values will be silently misassigned to the wrong group instances. Unit test to add: non-contiguous IDs `[0, 2]` → group table row 0 maps to `groupe_0`, row 1 maps to `groupe_2` (not reversed).
  - [ ] 4.7 **Store result keyed by entity plural** (existing behavior): use `key_to_plural` mapping to normalize keys
  - [ ] 4.8 **Policy parameter injection** (existing behavior): unchanged — inject on person entity only
  - [ ] 4.9 Unit tests: married couple (2 persons, 1 famille, 1 foyer, 1 menage), family with child (2 parents + 1 enfant, 1 famille, 2 foyers, 1 menage), backward compat (no membership columns)

- [ ] Task 5: Wire validation into `compute()` (AC: #1, #3, #4, #5)
  - [ ] 5.1 The `_population_to_entity_dict()` method is already called inside `_build_simulation()`. The membership detection and validation happen inside `_population_to_entity_dict()` itself (not in `compute()` directly), so the validation is naturally fail-fast — it runs before `SimulationBuilder.build_from_entities()` is called
  - [ ] 5.2 No changes to `compute()` call order — `_population_to_entity_dict()` is called inside `_build_simulation()` which is already after all output variable/entity/periodicity validation
  - [ ] 5.3 Unit tests: verify validation errors fire before simulation builder is called

- [ ] Task 6: Integration tests with real OpenFisca-France (AC: #1, #2, #7)
  - [ ] 6.1 Test: **married couple** — 2 persons, 1 famille (both as `parents`), 1 foyer_fiscal (both as `declarants`), 1 menage (`personne_de_reference` + `conjoint`). Use membership columns on person table. Verify `compute()` produces correct results matching existing hand-built integration tests (same `irpp` values as `TestOpenFiscaFranceReferenceCases.test_couple_salaire_imposable_30k_25k`). Use `ABSOLUTE_ERROR_MARGIN = 0.5` as a class attribute on the new integration test class, consistent with the existing reference test suite.
  - [ ] 6.2 Test: **single person with membership columns** — 1 person, 1 famille (`parents`), 1 foyer_fiscal (`declarants`), 1 menage (`personne_de_reference`). Verify results match single-person tests without membership columns
  - [ ] 6.3 Test: **two independent households** — 2 persons each in separate famille/foyer_fiscal/menage. Verify entity instance counts match (2 familles, 2 foyers, 2 menages)
  - [ ] 6.4 Test: **group entity input variables** — menage table with `loyer` column. Verify the value appears in the entity dict and is passable to `build_from_entities()`
  - [ ] 6.5 Test: **backward compatibility** — existing `single_person_population` fixture (no membership columns) still works identically via `adapter.compute()`
  - [ ] 6.6 Mark all with `@pytest.mark.integration`

- [ ] Task 7: Verify backward compatibility (AC: #6)
  - [ ] 7.1 Run ALL existing unit tests in `test_openfisca_api_adapter.py` — ensure all pass unchanged
  - [ ] 7.2 Run ALL existing integration tests in `test_openfisca_integration.py` — ensure all pass unchanged
  - [ ] 7.3 Verify `MockAdapter` still produces valid `ComputationResult` (no new required fields or format assumptions)
  - [ ] 7.4 Verify `ComputationStep` in orchestrator still works (`result.output_fields.num_rows`)
  - [ ] 7.5 Run `uv run pytest tests/orchestrator/` to confirm no orchestrator regressions

- [ ] Task 8: Run quality gates (all ACs)
  - [ ] 8.1 `uv run ruff check src/ tests/`
  - [ ] 8.2 `uv run mypy src/`
  - [ ] 8.3 `uv run pytest tests/computation/ tests/orchestrator/`

## Dev Notes

### Prerequisites — Story Sequencing

⚠️ **Story 9.3 (Add Variable Periodicity Handling) must be merged before starting this story.** Both stories modify `src/reformlab/computation/openfisca_api_adapter.py`. Story 9.3 changes `compute()`, `_extract_results_by_entity()`, `_calculate_variable()`, and `_resolve_variable_periodicities()`. Story 9.4 adds three new private methods and refactors `_population_to_entity_dict()` — method-level overlap is limited, but file-level merge conflicts are likely.

If concurrent development is unavoidable: develop Story 9.4 on a branch that explicitly tracks Story 9.3's branch and rebase before raising a PR. After Story 9.3 merges, `_population_to_entity_dict()` is unchanged — the methods added by Story 9.4 are fully additive.

### Architecture Constraints

- **Adapter isolation is absolute**: Only `computation/openfisca_adapter.py` and `openfisca_api_adapter.py` may import OpenFisca. All OpenFisca imports must be lazy (inside methods, not at module level).
- **Frozen dataclasses**: `PopulationData` and `ComputationResult` are `@dataclass(frozen=True)`. NO new fields are added to either in this story — the 4-entity format is expressed purely through column naming conventions in existing `tables: dict[str, pa.Table]`.
- **Protocol compatibility**: `ComputationAdapter` protocol (`period: int`) is unchanged. The membership handling is internal to `OpenFiscaApiAdapter`.
- **PyArrow is canonical**: All data containers use `pa.Table`. No pandas. Use `pa.compute` for null checks.
- **`from __future__ import annotations`** at top of every file.
- **No bare `Exception` or `ValueError`**: Use subsystem-specific exceptions (`ApiMappingError`).
- **Subsystem-specific exceptions**: Reuse existing `ApiMappingError` from `reformlab.computation.exceptions`. No new exception types needed.

### PopulationData 4-Entity Format — Complete Specification

**The format uses membership columns on the person entity table to express entity relationships.** No changes to the `PopulationData` type itself.

#### Column Naming Convention

For each group entity in the TBS (identified by `entity.is_person == False`):
- **`{entity.key}_id`** column (int64 or utf8): foreign key identifying which group instance this person belongs to
- **`{entity.key}_role`** column (utf8): the role key this person has in the group (must match `role.plural or role.key` from the TBS)

For OpenFisca-France, the 6 required membership columns are:

| Column Name | Type | Description | Example Values |
|---|---|---|---|
| `famille_id` | int64 | Family group instance ID | `0`, `0`, `1` |
| `famille_role` | utf8 | Role in family | `"parents"`, `"parents"`, `"parents"` |
| `foyer_fiscal_id` | int64 | Tax household instance ID | `0`, `0`, `1` |
| `foyer_fiscal_role` | utf8 | Role in tax household | `"declarants"`, `"declarants"`, `"declarants"` |
| `menage_id` | int64 | Dwelling instance ID | `0`, `0`, `1` |
| `menage_role` | utf8 | Role in dwelling | `"personne_de_reference"`, `"conjoint"`, `"personne_de_reference"` |

#### Example: Married Couple PopulationData

```python
PopulationData(
    tables={
        "individu": pa.table({
            # Variable columns (period-wrapped by adapter)
            "salaire_de_base": pa.array([30000.0, 0.0]),
            "age": pa.array([30, 28]),
            # Membership columns (NOT period-wrapped — used for entity dict construction)
            "famille_id": pa.array([0, 0]),
            "famille_role": pa.array(["parents", "parents"]),
            "foyer_fiscal_id": pa.array([0, 0]),
            "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
            "menage_id": pa.array([0, 0]),
            "menage_role": pa.array(["personne_de_reference", "conjoint"]),
        }),
    },
)
```

**Produces entity dict:**

```python
{
    "individus": {
        "individu_0": {"salaire_de_base": {"2024": 30000.0}, "age": {"2024": 30}},
        "individu_1": {"salaire_de_base": {"2024": 0.0}, "age": {"2024": 28}},
    },
    "familles": {
        "famille_0": {"parents": ["individu_0", "individu_1"]},
    },
    "foyers_fiscaux": {
        "foyer_fiscal_0": {"declarants": ["individu_0", "individu_1"]},
    },
    "menages": {
        "menage_0": {
            "personne_de_reference": ["individu_0"],
            "conjoint": ["individu_1"],
        },
    },
}
```

#### Example: Family with Child

```python
PopulationData(
    tables={
        "individu": pa.table({
            "salaire_de_base": pa.array([40000.0, 20000.0, 0.0]),
            "age": pa.array([45, 42, 12]),
            "famille_id": pa.array([0, 0, 0]),
            "famille_role": pa.array(["parents", "parents", "enfants"]),
            "foyer_fiscal_id": pa.array([0, 0, 0]),
            "foyer_fiscal_role": pa.array(["declarants", "declarants", "personnes_a_charge"]),
            "menage_id": pa.array([0, 0, 0]),
            "menage_role": pa.array(["personne_de_reference", "conjoint", "enfants"]),
        }),
    },
)
```

#### Example: With Group Entity Input Variables (AC-7)

```python
PopulationData(
    tables={
        "individu": pa.table({
            "salaire_de_base": pa.array([30000.0, 0.0]),
            "age": pa.array([30, 28]),
            "famille_id": pa.array([0, 0]),
            "famille_role": pa.array(["parents", "parents"]),
            "foyer_fiscal_id": pa.array([0, 0]),
            "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
            "menage_id": pa.array([0, 0]),
            "menage_role": pa.array(["personne_de_reference", "conjoint"]),
        }),
        # Optional: group entity table with group-level input variables
        "menage": pa.table({
            "loyer": pa.array([800.0]),  # Monthly rent
        }),
    },
)
```

**Produces entity dict with merged group variables:**

```python
{
    ...
    "menages": {
        "menage_0": {
            "personne_de_reference": ["individu_0"],
            "conjoint": ["individu_1"],
            "loyer": {"2024": 800.0},  # Period-wrapped from group entity table
        },
    },
}
```

### OpenFisca Role System — Reference from TBS Source

**Critical: `build_from_entities()` uses `role.plural or role.key`** as the dict key for role assignment. This was confirmed from `openfisca_core/simulations/simulation_builder.py` line ~517:

```python
role_by_plural = {role.plural or role.key: role for role in entity.roles}
```

**OpenFisca-France role definitions** (from `.venv/.../openfisca_france/entities.py`):

| Entity | Role | `role.key` | `role.plural` | Dict key (`plural or key`) | `role.max` |
|---|---|---|---|---|---|
| famille | Parent | `"parent"` | `"parents"` | **`"parents"`** | 2 |
| famille | Child | `"enfant"` | `"enfants"` | **`"enfants"`** | None |
| foyer_fiscal | Declarant | `"declarant"` | `"declarants"` | **`"declarants"`** | 2 |
| foyer_fiscal | Dependent | `"personne_a_charge"` | `"personnes_a_charge"` | **`"personnes_a_charge"`** | None |
| menage | Ref person | `"personne_de_reference"` | None | **`"personne_de_reference"`** | 1 |
| menage | Spouse | `"conjoint"` | None | **`"conjoint"`** | 1 |
| menage | Child | `"enfant"` | `"enfants"` | **`"enfants"`** | None |
| menage | Other | `"autre"` | `"autres"` | **`"autres"`** | None |

**⚠️ Note:** `role.plural` is `None` for `personne_de_reference` and `conjoint` in menage. The adapter must use `role.plural or role.key` to compute valid role keys — not `role.plural` alone (which would be `None`).

### Querying TBS for Role Information

```python
# In _resolve_valid_role_keys():
valid_roles: dict[str, frozenset[str]] = {}
for entity in tbs.entities:
    if getattr(entity, "is_person", False):
        continue
    role_keys: set[str] = set()
    for role in entity.roles:
        # role.plural is a property that returns None if not defined
        plural = getattr(role, "plural", None)
        key = getattr(role, "key", None)
        role_dict_key = plural or key
        if role_dict_key:
            role_keys.add(role_dict_key)
    valid_roles[entity.key] = frozenset(role_keys)
```

**⚠️ Accessing `entity.roles`:** In OpenFisca-Core, `entity.roles` is available on GroupEntity objects. The Role objects have `.key` and `.plural` as properties. Always access with `getattr()` for defensive coding — some attributes may be `None`.

### Group Instance ID Generation

**Group instance IDs are derived from the `_id` column values:**

```python
# For famille_id column with values [0, 0, 1]:
# → Group IDs: {0, 1}
# → Instance IDs: "famille_0", "famille_1"

# Person instance ID: f"{person_entity_key}_{row_index}"
# → "individu_0", "individu_1", "individu_2"

# Group instance ID: f"{group_entity_key}_{group_id_value}"
# → "famille_0", "foyer_fiscal_0", "menage_0"
```

**The person instance ID is the key used in the role assignment lists.** The person instance IDs must match between the person entity dict and the group entity role arrays. Currently, `_population_to_entity_dict()` uses `f"{entity_key}_{i}"` where `entity_key` comes from the PopulationData table key (e.g., `"individu"`) and `i` is the row index. This convention must be preserved.

**⚠️ Critical:** the prefix is the original `population.tables` key — not necessarily `person_entity.key`. If the caller passes `"individus"` (plural) as the table key, all person instance IDs become `"individus_0"`, `"individus_1"`, etc. The group entity role lists must use these same IDs. Capture this key early (`person_table_key`) and use it consistently for both person instances (Task 4.4) and role assignment lists (Task 4.5).

### Algorithm for Refactored `_population_to_entity_dict()`

```
1. Build key_to_plural mapping: {entity.key: entity.plural for entity in tbs.entities}
2. Identify person entity: person_entity = next(e for e in tbs.entities if e.is_person)
2b. Find person_table_key: the key in population.tables matching person_entity.key
    OR person_entity.plural (user may pass either singular or plural).
    If no matching key found → no person entity table present; fall through to step 4
    (backward-compatible: membership columns require a person entity table).
3. person_table = population.tables[person_table_key]
   membership_cols = _detect_membership_columns(person_table, tbs)
4. IF empty dict returned → execute existing all-tables loop (current lines 538–569
   of _population_to_entity_dict()): iterate ALL population.tables, period-wrap every
   column, store keyed by entity plural. Return immediately.
5. IF membership columns detected (4-entity mode):
   ⚠️ The original all-tables iteration loop is REPLACED by steps 5a–5g.
   Do NOT run the old loop before/after — this would double-write group entity
   entries and corrupt the result dict.

   a. valid_roles = _resolve_valid_role_keys(tbs)
   b. _validate_entity_relationships(person_table, membership_cols, valid_roles)
   c. Build membership_col_names: set of all _id and _role column names
      (these are excluded from period-wrapping in step 5d)
   d. Build person instances FROM PERSON TABLE ONLY:
      - Use person_table_key as the instance ID prefix
        (e.g. "individu" → "individu_0"; "individus" → "individus_0")
      - Skip columns in membership_col_names
      - result[person_entity.plural][f"{person_table_key}_{i}"] =
          {col: {period_str: val} for col not in membership_col_names}
   e. For each group_entity_key in membership_cols:
      i.   id_col = person_table.column(f"{group_entity_key}_id")
           role_col = person_table.column(f"{group_entity_key}_role")
      ii.  sorted_group_ids = sorted(pa.compute.unique(id_col).to_pylist())
      iii. For each group_id in sorted_group_ids:
           - Collect row indices where id_col == group_id
           - Build role_dict: {role_key: [f"{person_table_key}_{i}" for each index]}
      iv.  group_plural = key_to_plural[group_entity_key]
           result[group_plural][f"{group_entity_key}_{group_id}"] = role_dict
   f. Merge group entity table variables (if present):
      i.   For each group entity key with a table in population.tables
      ii.  sorted_group_ids from person table _id column (same order as step 5e)
      iii. Raise ApiMappingError if group_table.num_rows != len(sorted_group_ids)
      iv.  ⚠️ POSITIONAL MATCH: row i of group table → sorted_group_ids[i]
           Requires group table rows to be ordered by ascending {entity_key}_id value
      v.   For each (i, group_id): period-wrap group_table row i columns and
           merge into result[group_plural][f"{group_entity_key}_{group_id}"]
   g. Inject policy parameters into person entity instances (unchanged)
6. Return result
```

### Backward Compatibility Strategy

This story is **internal to `_population_to_entity_dict()`** — no external interface changes:

1. **`PopulationData` type is unchanged** — no new fields, no type changes.
2. **`ComputationResult` is unchanged** — the output format doesn't change.
3. **`ComputationAdapter` protocol is unchanged** — `compute(population, policy, period)` signature unchanged.
4. **`MockAdapter` is unaffected** — it never calls `_population_to_entity_dict()`.
5. **Detection is opt-in by column presence** — no membership columns = old behavior. ALL existing tests use PopulationData without membership columns, so they remain unaffected.
6. **`compute()` call order is unchanged** — `_population_to_entity_dict()` is called inside `_build_simulation()` at the same position in the pipeline.

### Mock TBS Extension for Unit Tests

Extend `_make_mock_tbs_with_entities()` in the test file to support roles:

```python
def _make_mock_tbs_with_entities(
    entity_keys: tuple[str, ...] = ("individu", "foyer_fiscal", "menage"),
    entity_plurals: dict[str, str] | None = None,
    variable_entities: dict[str, str] | None = None,
    variable_periodicities: dict[str, str] | None = None,
    person_entity: str = "individu",
    entity_roles: dict[str, list[dict[str, str | None]]] | None = None,
    # ↑ NEW: e.g., {"famille": [{"key": "parent", "plural": "parents"}, ...]}
) -> MagicMock:
```

Each role entry should be a `SimpleNamespace(key=..., plural=...)` to match the TBS Role interface.

**Example:**
```python
mock_tbs = _make_mock_tbs_with_entities(
    entity_keys=("individu", "famille", "foyer_fiscal", "menage"),
    entity_roles={
        "famille": [
            {"key": "parent", "plural": "parents"},
            {"key": "enfant", "plural": "enfants"},
        ],
        "foyer_fiscal": [
            {"key": "declarant", "plural": "declarants"},
            {"key": "personne_a_charge", "plural": "personnes_a_charge"},
        ],
        "menage": [
            {"key": "personne_de_reference", "plural": None},
            {"key": "conjoint", "plural": None},
            {"key": "enfant", "plural": "enfants"},
            {"key": "autre", "plural": "autres"},
        ],
    },
)
```

**⚠️ Existing mock entities do NOT have `roles` attribute.** The mock must add `entity.roles = [SimpleNamespace(key=..., plural=...) for ...]` for group entities and `entity.roles = []` (or omit) for the person entity. The `_detect_membership_columns()` method uses `entity.is_person` to skip the person entity, so it won't try to access `roles` on it.

### Files to Modify

| File | Change |
|------|--------|
| `src/reformlab/computation/openfisca_api_adapter.py` | Add `_detect_membership_columns()`, `_resolve_valid_role_keys()`, `_validate_entity_relationships()`. Refactor `_population_to_entity_dict()` to handle 4-entity format with membership columns |
| `tests/computation/test_openfisca_api_adapter.py` | Extend `_make_mock_tbs_with_entities()` with `entity_roles` parameter. Add new test classes: `TestDetectMembershipColumns`, `TestResolveValidRoleKeys`, `TestValidateEntityRelationships`, `TestPopulationToEntityDict4Entity`. Add marriage/family fixtures |
| `tests/computation/test_openfisca_integration.py` | Add integration tests for 4-entity format: married couple via membership columns, family with child, backward compat, group entity variables |

### Files to Verify (No Changes Expected)

| File | Why |
|------|-----|
| `src/reformlab/computation/types.py` | `PopulationData` unchanged — no new fields |
| `src/reformlab/computation/types.pyi` | Type stub unchanged |
| `src/reformlab/computation/adapter.py` | Protocol unchanged |
| `src/reformlab/computation/mock_adapter.py` | Unaffected — doesn't call `_population_to_entity_dict()` |
| `src/reformlab/computation/exceptions.py` | Reuse existing `ApiMappingError` — no new exception types |
| `src/reformlab/orchestrator/computation_step.py` | Passes `population` to adapter unchanged |
| `src/reformlab/orchestrator/panel.py` | Accesses `comp_result.output_fields` — unchanged |

### Integration Test Reference Data

**Married couple via membership columns (should match existing hand-built test):**

```python
# This PopulationData with membership columns:
population = PopulationData(
    tables={
        "individu": pa.table({
            "salaire_imposable": pa.array([30000.0, 25000.0]),
            "famille_id": pa.array([0, 0]),
            "famille_role": pa.array(["parents", "parents"]),
            "foyer_fiscal_id": pa.array([0, 0]),
            "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
            "menage_id": pa.array([0, 0]),
            "menage_role": pa.array(["personne_de_reference", "conjoint"]),
        }),
    },
)

# Should produce the SAME irpp as the existing reference case:
# test_couple_salaire_imposable_30k_25k → irpp ≈ -2765.0
```

**Two independent households:**

```python
population = PopulationData(
    tables={
        "individu": pa.table({
            "salaire_de_base": pa.array([30000.0, 50000.0]),
            "age": pa.array([30, 45]),
            "famille_id": pa.array([0, 1]),
            "famille_role": pa.array(["parents", "parents"]),
            "foyer_fiscal_id": pa.array([0, 1]),
            "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
            "menage_id": pa.array([0, 1]),
            "menage_role": pa.array(["personne_de_reference", "personne_de_reference"]),
        }),
    },
)
# Each person in their own groupe → 2 familles, 2 foyers, 2 menages
```

### What This Story Does NOT Cover

- **Person-level broadcasting** of group entity values (e.g., distributing `irpp` from foyer_fiscal to its members) — separate follow-up
- **Input variable period assignment for non-yearly variables** — e.g., `age` may need `"2024-01"` period format instead of `"2024"`. Currently all values are wrapped with the yearly period string. This is a known limitation carried over from the existing implementation
- **Modifying `PopulationData` type** — the 4-entity format is expressed purely through column naming conventions, no type changes
- **Modifying `MockAdapter`** — it never calls OpenFisca and doesn't need membership logic
- **Sub-yearly period support** — `ComputationAdapter.compute(period: int)` remains yearly only
- **`calculate_divide()` support** — not needed for yearly periods
- **Automatic population generation in 4-entity format** — `src/reformlab/data/synthetic.py` generates household-level data, not the 4-entity person-level format. Converting synthetic populations to 4-entity format is a separate concern
- **Country-package-agnostic entity discovery** — this story targets OpenFisca-France specifically. Other country packages may have different entity structures

### Edge Cases to Handle

1. **Group ID values are not contiguous** — e.g., `famille_id = [0, 2, 2]` (no famille 1). This is valid — group IDs are arbitrary identifiers, not indices. Instance IDs: `"famille_0"`, `"famille_2"`.

2. **String group IDs** — `famille_id` column could be utf8 instead of int64. The instance ID format becomes `f"{entity_key}_{str(group_id)}"`. Support both int64 and utf8 column types.

3. **Extra rows in group entity table** — if `population.tables["menage"]` has more rows than the number of distinct `menage_id` values in the person table, the extra rows are unmatched. Raise `ApiMappingError` with summary `"Group entity table row count mismatch"`, including the table row count and the number of distinct group IDs found in the person table. (A group ID appearing in no person's `_id` column cannot occur by construction — groups are discovered from the person table's `_id` column, not from a separate registry. The mismatch only occurs when the caller provides a group entity table with more rows than the person table's distinct IDs.)

4. **Single person with membership columns** — valid. One person assigned to one group per entity. Should produce the same result as without membership columns.

5. **Person table key is plural** — e.g., `"individus"` instead of `"individu"`. The existing key normalization logic handles this.

### Project Structure Notes

- Source layout: `src/reformlab/` is the installable package
- Tests mirror source: `tests/computation/` matches `src/reformlab/computation/`
- Each test subdirectory has `__init__.py` and `conftest.py`
- Class-based test grouping with AC references in docstrings
- Integration tests require `openfisca-france` optional dependency: `uv sync --extra openfisca`
- Run unit tests: `uv run pytest tests/computation/ -m "not integration"`
- Run integration tests: `uv run pytest tests/computation/ -m integration`
- Quality gates: `uv run ruff check src/ tests/` and `uv run mypy src/`

### References

- [Source: `_bmad-output/implementation-artifacts/spike-findings-8-1-openfisca-integration.md` — Follow-up #4: "Update PopulationData format for OpenFisca-France", line 106]
- [Source: `_bmad-output/implementation-artifacts/spike-findings-8-1-openfisca-integration.md` — Gap 2: "Multi-entity output arrays have different lengths", lines 45-61]
- [Source: `_bmad-output/implementation-artifacts/9-2-handle-multi-entity-output-arrays.md` — "What This Story Does NOT Cover": "PopulationData 4-entity format — that is Story 9.4", line 237]
- [Source: `_bmad-output/implementation-artifacts/9-3-add-variable-periodicity-handling.md` — "What This Story Does NOT Cover": "PopulationData 4-entity format — That is Story 9.4", near end of Dev Notes]
- [Source: `src/reformlab/computation/openfisca_api_adapter.py` — `_population_to_entity_dict()` method, lines 499-569]
- [Source: `src/reformlab/computation/types.py` — `PopulationData` dataclass, lines 11-26]
- [Source: `src/reformlab/computation/exceptions.py` — `ApiMappingError` structured error pattern]
- [Source: `.venv/.../openfisca_france/entities.py` — Entity and role definitions for individu, famille, foyer_fiscal, menage]
- [Source: `.venv/.../openfisca_core/simulations/simulation_builder.py` — `build_from_entities()` role parsing: `role_by_plural = {role.plural or role.key: role}`, line ~517]
- [Source: `.venv/.../openfisca_core/entities/role.py` — `Role` class with `.key` and `.plural` properties]
- [Source: `tests/computation/test_openfisca_integration.py` — `_build_entities_dict()` helper, line 75; `_build_simulation()` helper, line 88; married couple entity dict patterns, lines 286-298]
- [Source: `_bmad-output/planning-artifacts/epics.md` — Epic 9, Story 9.4 acceptance criteria]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (via create-story workflow)

### Debug Log References

### Completion Notes List

- Code review synthesis 2026-03-01: 6 issues applied from adversarial review (Reviewer B confirmed; Reviewer A issues were largely false positives based on truncated file views in the review context).
  - CRITICAL FIX: Replaced O(n×g) nested loop in Step 5e with single-pass O(n) approach. Converts both id/role columns to Python lists once, then groups in one enumerated zip iteration. For 250k persons × 100k groups, this reduces from ~25 billion ops to ~250k ops.
  - HIGH FIX: Replaced two load-bearing `assert` statements (lines 838, 867) with explicit `ApiMappingError` raises. `assert` is stripped by Python's `-O` flag; the second assert had `result[None] = person_dict` as its failure mode — a `None` dict key that silently corrupts the entity dict passed to `build_from_entities()`.
  - HIGH FIX: Pre-amortized column extraction in Step 5d — replaced O(n×c) scalar-boxing loop with a dict-comprehension that calls `.to_pylist()` once per column outside the row loop.
  - HIGH FIX: Role validation now checks `pa.compute.unique(role_array)` (≤4 distinct values) instead of the full population array (`to_pylist()` of n rows). Reduces O(n) to O(u) where u ≤ 4.
  - MEDIUM FIX: Null-index detection now uses `pa.compute.filter()` + single `.as_py()` call instead of a Python for-loop with per-element `.as_py()` boxings. Only runs on error path, but consistency matters.
  - LOW FIX: Added `logger.warning()` to Step 5f positional group-table merge to make the ordering assumption visible in structured logs. Silent data corruption on unsorted group tables is now observable.
  - LOW FIX: Updated `Status: ready-for-dev` → `Status: done` (third recurrence of antipattern from Stories 9.2 and 9.3).
- Ultimate context engine analysis completed — comprehensive developer guide created
- All 3 acceptance criteria from epics file expanded to 7 ACs covering: format definition, group membership, missing relationship validation, invalid role validation, null value rejection, backward compatibility, and group entity input variables
- Spike 8-1 findings fully integrated: follow-up #4 (4-entity format) is the direct motivation; Gap 2 (multi-entity arrays) is the predecessor context
- OpenFisca entity role system documented from source code inspection:
  - `Role` has `.key` and `.plural` properties; `.plural` can be `None` (e.g., menage `personne_de_reference`)
  - `build_from_entities()` uses `role.plural or role.key` as dict key (confirmed from `simulation_builder.py` line ~517)
  - Complete role table for all 4 OpenFisca-France entities with 8 roles documented
- Column naming convention designed: `{entity_key}_id` (int64/utf8) + `{entity_key}_role` (utf8) on person table
  - All-or-nothing detection: ANY membership column triggers full 4-entity format requirement
  - Paired column check: both `_id` and `_role` required per entity
- Backward compatibility strategy: purely internal changes to `_population_to_entity_dict()`, auto-detected by column presence
- Three complete example PopulationData formats documented: married couple, family with child, group entity variables
- Algorithm pseudocode provided for refactored `_population_to_entity_dict()`
- Mock TBS extension pattern documented with `entity_roles` parameter and SimpleNamespace role objects
- Edge cases documented: non-contiguous group IDs, string group IDs, empty groups, single person with membership columns
- Integration test reference data with expected values (married couple irpp ≈ -2765.0 cross-validated against existing `test_couple_salaire_imposable_30k_25k`)
- Story 9.2 and 9.3 predecessor analysis: confirms explicit exclusion of 4-entity format from both stories

### File List

- `src/reformlab/computation/openfisca_api_adapter.py` — modify (add `_detect_membership_columns()`, `_resolve_valid_role_keys()`, `_validate_entity_relationships()`, refactor `_population_to_entity_dict()`)
- `tests/computation/test_openfisca_api_adapter.py` — modify (extend mock TBS with roles, add 4-entity format unit tests)
- `tests/computation/test_openfisca_integration.py` — modify (add 4-entity format integration tests with membership columns)


]]></file>
<file id="65375f24" path="src/reformlab/computation/openfisca_api_adapter.py" label="SOURCE CODE"><![CDATA[

"""Adapter that executes OpenFisca computations via the Python API.

Unlike ``OpenFiscaAdapter`` (pre-computed file mode), this adapter
runs live tax-benefit calculations using OpenFisca's ``SimulationBuilder``.

All OpenFisca imports are lazy since ``openfisca-core`` is an optional
dependency.

Story 9.2: Added entity-aware result extraction to correctly handle
output variables belonging to different entity types (individu, menage,
famille, foyer_fiscal).

Story 9.3: Added periodicity-aware calculation dispatch. Monthly variables
use ``calculate_add()`` to sum sub-period values; yearly and eternity
variables use ``calculate()``. Period validation ensures valid 4-digit year.

Story 9.4: Added 4-entity PopulationData format support. Membership columns
on the person entity table (``{entity_key}_id`` and ``{entity_key}_role``)
express entity relationships for multi-person populations. The adapter
detects these columns, validates relationships, and produces a valid entity
dict passable to ``SimulationBuilder.build_from_entities()``.
"""

from __future__ import annotations

import difflib
import logging
import time
from typing import Any

import pyarrow as pa

from reformlab.computation.exceptions import ApiMappingError, CompatibilityError
from reformlab.computation.openfisca_common import (
    _check_version,
    _detect_openfisca_version,
)
from reformlab.computation.types import ComputationResult, PolicyConfig, PopulationData

logger = logging.getLogger(__name__)

# Story 9.3: Valid OpenFisca DateUnit periodicity values (StrEnum).
# Sub-yearly periodicities use calculate_add(); year/eternity use calculate().
_VALID_PERIODICITIES = frozenset({
    "month", "year", "eternity", "day", "week", "weekday",
})
_CALCULATE_ADD_PERIODICITIES = frozenset({
    "month", "day", "week", "weekday",
})


def _periodicity_to_method_name(periodicity: str) -> str:
    """Map a DateUnit periodicity string to the OpenFisca calculation method name.

    Single source of truth for the ``calculate`` vs ``calculate_add`` dispatch
    decision. Sub-yearly periodicities (month, day, week, weekday) aggregate
    via ``calculate_add``; year and eternity use ``calculate`` directly.
    """
    return "calculate_add" if periodicity in _CALCULATE_ADD_PERIODICITIES else "calculate"


class OpenFiscaApiAdapter:
    """Adapter that executes OpenFisca computations via the Python API.

    Unlike ``OpenFiscaAdapter`` (pre-computed file mode), this adapter
    runs live tax-benefit calculations using OpenFisca's ``SimulationBuilder``.
    """

    def __init__(
        self,
        *,
        country_package: str = "openfisca_france",
        output_variables: tuple[str, ...],
        skip_version_check: bool = False,
    ) -> None:
        if not output_variables:
            raise ApiMappingError(
                summary="Empty output_variables",
                reason="output_variables tuple is empty — no variables to compute",
                fix="Provide at least one valid output variable name.",
                invalid_names=(),
                valid_names=(),
            )
        self._country_package = country_package
        self._output_variables = output_variables

        if not skip_version_check:
            self._version = _detect_openfisca_version()
            _check_version(self._version)
        else:
            self._version = "unknown"

        self._tax_benefit_system: Any = None

    def version(self) -> str:
        """Return the detected OpenFisca-Core version string."""
        return self._version

    def compute(
        self,
        population: PopulationData,
        policy: PolicyConfig,
        period: int,
    ) -> ComputationResult:
        """Run a live OpenFisca computation for the given inputs.

        Args:
            population: Input population data with entity tables.
            policy: Scenario parameters (applied as input-variable values).
            period: Computation period (integer year, e.g. 2025).

        Returns:
            A ``ComputationResult`` with output variables as a PyArrow Table.
            When output variables span multiple entities, ``entity_tables``
            contains per-entity tables keyed by entity plural name.

        Raises:
            ApiMappingError: If the period is invalid (not a 4-digit year
                in range [1000, 9999]).
        """
        # Story 9.3 AC-3: Period validation — FIRST check before any TBS operations.
        self._validate_period(period)

        start = time.monotonic()

        tbs = self._get_tax_benefit_system()
        self._validate_output_variables(tbs)

        # Story 9.2: Resolve entity grouping before building simulation (fail fast —
        # avoid expensive SimulationBuilder.build_from_entities() if entity
        # resolution fails due to incompatible country package).
        vars_by_entity = self._resolve_variable_entities(tbs)

        # Story 9.3 AC-1, AC-2, AC-6: Resolve periodicities before simulation
        # (fail fast — detect unsupported periodicity values early).
        var_periodicities = self._resolve_variable_periodicities(tbs)

        simulation = self._build_simulation(population, policy, period, tbs)
        entity_tables = self._extract_results_by_entity(
            simulation, period, vars_by_entity, var_periodicities
        )

        # Determine primary output_fields table for backward compatibility:
        # - Single entity → that entity's table
        # - Multiple entities → person-entity table (or first entity's table)
        output_fields = self._select_primary_output(entity_tables, tbs)

        elapsed = time.monotonic() - start

        # Only expose entity_tables for multi-entity results — keeps metadata
        # consistent with entity_tables (single-entity uses {} for backward compat).
        result_entity_tables = entity_tables if len(entity_tables) > 1 else {}
        output_entities = sorted(result_entity_tables.keys())
        entity_row_counts = {
            entity: table.num_rows for entity, table in result_entity_tables.items()
        }

        # Story 9.3 AC-5: Build calculation methods mapping from periodicities.
        # Uses _periodicity_to_method_name() — single source of truth for the
        # calculate vs calculate_add dispatch decision.
        calculation_methods: dict[str, str] = {
            var_name: _periodicity_to_method_name(periodicity)
            for var_name, periodicity in var_periodicities.items()
        }

        return ComputationResult(
            output_fields=output_fields,
            adapter_version=self._version,
            period=period,
            metadata={
                "timing_seconds": round(elapsed, 4),
                "row_count": output_fields.num_rows,
                "source": "api",
                "policy_name": policy.name,
                "country_package": self._country_package,
                "output_variables": list(self._output_variables),
                "output_entities": output_entities,
                "entity_row_counts": entity_row_counts,
                "variable_periodicities": dict(var_periodicities),
                "calculation_methods": calculation_methods,
            },
            entity_tables=result_entity_tables,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_tax_benefit_system(self) -> Any:
        """Lazily import the country package and cache the TaxBenefitSystem."""
        if self._tax_benefit_system is not None:
            return self._tax_benefit_system

        try:
            import importlib

            module = importlib.import_module(self._country_package)
        except ImportError:
            raise CompatibilityError(
                expected=self._country_package,
                actual="not-installed",
                details=(
                    f"Country package '{self._country_package}' is not installed. "
                    f"Install it with: uv add '{self._country_package}'. "
                    "See https://openfisca.org/doc/ for available country packages."
                ),
            )

        # Country packages expose the TBS via a conventional attribute.
        # openfisca_france → FranceTaxBenefitSystem (via CountryTaxBenefitSystem)
        tbs_class = getattr(module, "CountryTaxBenefitSystem", None)
        if tbs_class is None:
            # Fallback: try the generic TaxBenefitSystem attribute
            tbs_class = getattr(module, "TaxBenefitSystem", None)
        if tbs_class is None:
            raise CompatibilityError(
                expected=f"TaxBenefitSystem in {self._country_package}",
                actual="not found",
                details=(
                    f"Package '{self._country_package}' does not expose "
                    "'CountryTaxBenefitSystem' or 'TaxBenefitSystem'. "
                    "Verify the package is a valid OpenFisca country package."
                ),
            )

        self._tax_benefit_system = tbs_class()
        return self._tax_benefit_system

    def _validate_output_variables(self, tbs: Any) -> None:
        """Check that all requested output variables exist in the TBS."""
        known_variables = set(tbs.variables.keys())
        invalid = [v for v in self._output_variables if v not in known_variables]

        if not invalid:
            return

        suggestions: dict[str, list[str]] = {}
        known_list = sorted(known_variables)
        for name in invalid:
            matches = difflib.get_close_matches(name, known_list, n=3, cutoff=0.6)
            if matches:
                suggestions[name] = matches

        suggestion_lines = []
        for name in invalid:
            if name in suggestions:
                suggestion_lines.append(
                    f"  '{name}' → did you mean: {', '.join(suggestions[name])}?"
                )
            else:
                suggestion_lines.append(f"  '{name}' → no close matches found")

        raise ApiMappingError(
            summary="Unknown output variables",
            reason=(
                f"{len(invalid)} variable(s) not found in "
                f"{self._country_package} TaxBenefitSystem: "
                f"{', '.join(invalid)}"
            ),
            fix=(
                "Check variable names against the country package. "
                "Suggestions:\n" + "\n".join(suggestion_lines)
            ),
            invalid_names=tuple(invalid),
            valid_names=tuple(sorted(known_variables)),
            suggestions=suggestions,
        )

    # ------------------------------------------------------------------
    # Story 9.3: Period validation and periodicity-aware dispatch
    # ------------------------------------------------------------------

    def _validate_period(self, period: int) -> None:
        """Validate that the period is a 4-digit year in [1000, 9999].

        Story 9.3 AC-3: Called as the FIRST operation in ``compute()``,
        before any TBS queries or simulation construction.

        Raises:
            ApiMappingError: If the period is invalid.
        """
        if not (1000 <= period <= 9999):
            raise ApiMappingError(
                summary="Invalid period",
                reason=(
                    f"Period {period!r} is not a valid 4-digit year"
                ),
                fix=(
                    "Provide a positive integer year in range [1000, 9999], "
                    "e.g. 2024"
                ),
                invalid_names=(),
                valid_names=(),
            )

    def _resolve_variable_periodicities(
        self, tbs: Any
    ) -> dict[str, str]:
        """Detect the periodicity of each output variable from the TBS.

        Story 9.3 AC-1, AC-2, AC-6: Queries
        ``tbs.variables[var_name].definition_period`` for each output variable
        to determine whether ``calculate()`` or ``calculate_add()`` should
        be used.

        Args:
            tbs: The loaded TaxBenefitSystem.

        Returns:
            Dict mapping variable name to periodicity string
            (e.g. ``{"salaire_net": "month", "irpp": "year"}``).

        Raises:
            ApiMappingError: If a variable's periodicity cannot be determined
                or has an unexpected value.
        """
        periodicities: dict[str, str] = {}

        for var_name in self._output_variables:
            variable = tbs.variables.get(var_name)
            if variable is None:
                # Defensive — _validate_output_variables should have caught this.
                raise ApiMappingError(
                    summary="Cannot resolve variable periodicity",
                    reason=(
                        f"Variable '{var_name}' not found in "
                        f"{self._country_package} TaxBenefitSystem"
                    ),
                    fix=(
                        "Ensure the variable exists in the country package. "
                        "This may indicate the TBS was modified after validation."
                    ),
                    invalid_names=(var_name,),
                    valid_names=tuple(sorted(tbs.variables.keys())),
                )

            definition_period = getattr(variable, "definition_period", None)
            if definition_period is None:
                raise ApiMappingError(
                    summary="Cannot determine periodicity for variable",
                    reason=(
                        f"Variable '{var_name}' has no .definition_period "
                        f"attribute in {self._country_package} TaxBenefitSystem"
                    ),
                    fix=(
                        "This variable may not be properly defined in the "
                        "country package. Check the variable definition."
                    ),
                    invalid_names=(var_name,),
                    valid_names=tuple(sorted(tbs.variables.keys())),
                )

            # DateUnit is a StrEnum — string comparison works directly.
            periodicity_str = str(definition_period)
            if periodicity_str not in _VALID_PERIODICITIES:
                raise ApiMappingError(
                    summary="Unexpected periodicity for variable",
                    reason=(
                        f"Variable '{var_name}' has definition_period="
                        f"'{periodicity_str}', expected one of: "
                        f"{', '.join(sorted(_VALID_PERIODICITIES))}"
                    ),
                    fix=(
                        "This may indicate an incompatible OpenFisca version. "
                        "Check the OpenFisca compatibility matrix."
                    ),
                    invalid_names=(var_name,),
                    valid_names=tuple(sorted(tbs.variables.keys())),
                )

            periodicities[var_name] = periodicity_str

        logger.debug(
            "variable_periodicities=%s output_variables=%s",
            periodicities,
            list(self._output_variables),
        )

        return periodicities

    def _calculate_variable(
        self,
        simulation: Any,
        var_name: str,
        period_str: str,
        periodicity: str,
    ) -> Any:
        """Dispatch to the correct OpenFisca calculation method.

        Story 9.3 AC-1, AC-2, AC-6:
        - ``"month"``, ``"day"``, ``"week"``, ``"weekday"``
          → ``simulation.calculate_add(var, period)``
        - ``"year"``, ``"eternity"``
          → ``simulation.calculate(var, period)``

        Args:
            simulation: The OpenFisca simulation.
            var_name: Variable name to compute.
            period_str: Period string (e.g. "2024").
            periodicity: The variable's definition_period string.

        Returns:
            numpy.ndarray of computed values.
        """
        method = _periodicity_to_method_name(periodicity)
        logger.debug(
            "var=%s periodicity=%s method=%s period=%s",
            var_name, periodicity, method, period_str,
        )
        if method == "calculate_add":
            return simulation.calculate_add(var_name, period_str)
        else:
            return simulation.calculate(var_name, period_str)

    def _validate_policy_parameters(self, policy: PolicyConfig, tbs: Any) -> None:
        """Check that all policy parameter keys are valid input variables."""
        if not policy.parameters:
            return

        known_variables = set(tbs.variables.keys())
        invalid = [k for k in policy.parameters if k not in known_variables]

        if not invalid:
            return

        suggestions: dict[str, list[str]] = {}
        known_list = sorted(known_variables)
        for name in invalid:
            matches = difflib.get_close_matches(name, known_list, n=3, cutoff=0.6)
            if matches:
                suggestions[name] = matches

        suggestion_lines = []
        for name in invalid:
            if name in suggestions:
                suggestion_lines.append(
                    f"  '{name}' → did you mean: {', '.join(suggestions[name])}?"
                )
            else:
                suggestion_lines.append(f"  '{name}' → no close matches found")

        raise ApiMappingError(
            summary="Unknown policy parameter keys",
            reason=(
                f"{len(invalid)} parameter key(s) not found as variables in "
                f"{self._country_package} TaxBenefitSystem: "
                f"{', '.join(invalid)}"
            ),
            fix=(
                "PolicyConfig.parameters keys must be valid OpenFisca variable names. "
                "Suggestions:\n" + "\n".join(suggestion_lines)
            ),
            invalid_names=tuple(invalid),
            valid_names=tuple(sorted(known_variables)),
            suggestions=suggestions,
        )

    def _build_simulation(
        self,
        population: PopulationData,
        policy: PolicyConfig,
        period: int,
        tbs: Any,
    ) -> Any:
        """Construct an OpenFisca Simulation from population and policy data."""
        from openfisca_core.simulation_builder import SimulationBuilder

        # Validate entity keys against TBS (accept both singular and plural)
        tbs_entity_keys = {entity.key for entity in tbs.entities}
        tbs_entity_plurals = {entity.plural for entity in tbs.entities}
        valid_names = tbs_entity_keys | tbs_entity_plurals
        unknown_entities = [
            key for key in population.tables if key not in valid_names
        ]
        if unknown_entities:
            raise ApiMappingError(
                summary="Unknown entity keys in population data",
                reason=(
                    f"Entity key(s) {', '.join(unknown_entities)} not found in "
                    f"{self._country_package} TaxBenefitSystem"
                ),
                fix=(
                    f"Population entity keys must be one of: "
                    f"{', '.join(sorted(tbs_entity_keys))}. "
                    "Check PopulationData.tables keys."
                ),
                invalid_names=tuple(unknown_entities),
                valid_names=tuple(sorted(tbs_entity_keys)),
            )

        # Validate policy parameters
        self._validate_policy_parameters(policy, tbs)

        # Build entity dict for SimulationBuilder.build_from_entities
        period_str = str(period)
        entities_dict = self._population_to_entity_dict(
            population, policy, period_str, tbs
        )

        builder = SimulationBuilder()
        simulation = builder.build_from_entities(tbs, entities_dict)

        return simulation

    # ------------------------------------------------------------------
    # Story 9.4: 4-entity PopulationData format — membership columns
    # ------------------------------------------------------------------

    def _detect_membership_columns(
        self,
        person_table: pa.Table,
        tbs: Any,
    ) -> dict[str, tuple[str, str]]:
        """Detect membership columns on the person entity table.

        Story 9.4 AC-1, AC-3, AC-6: Checks for ``{entity.key}_id`` and
        ``{entity.key}_role`` columns for each group entity in the TBS.

        Args:
            person_table: The person entity PyArrow table.
            tbs: The loaded TaxBenefitSystem.

        Returns:
            Dict mapping group entity key to ``(id_column, role_column)`` tuple.
            Empty dict if no membership columns are detected (backward compat).

        Raises:
            ApiMappingError: If membership columns are incomplete (all-or-nothing)
                or unpaired (_id without _role or vice versa).
        """
        col_names = set(person_table.column_names)

        # Identify group entities from TBS
        group_entity_keys: list[str] = []
        for entity in tbs.entities:
            if not getattr(entity, "is_person", False):
                group_entity_keys.append(entity.key)

        # Check for membership column presence
        detected: dict[str, tuple[str, str]] = {}
        has_any_id = False
        has_any_role = False
        unpaired: list[str] = []
        present_pairs: list[str] = []
        missing_pairs: list[str] = []

        for entity_key in group_entity_keys:
            id_col = f"{entity_key}_id"
            role_col = f"{entity_key}_role"
            has_id = id_col in col_names
            has_role = role_col in col_names

            if has_id:
                has_any_id = True
            if has_role:
                has_any_role = True

            if has_id and has_role:
                detected[entity_key] = (id_col, role_col)
                present_pairs.append(entity_key)
            elif has_id and not has_role:
                unpaired.append(
                    f"'{id_col}' present but '{role_col}' missing"
                )
            elif has_role and not has_id:
                unpaired.append(
                    f"'{role_col}' present but '{id_col}' missing"
                )
            else:
                missing_pairs.append(entity_key)

        # No membership columns at all → backward compatible
        if not has_any_id and not has_any_role:
            return {}

        # Unpaired columns: _id without _role or vice versa
        if unpaired:
            raise ApiMappingError(
                summary="Unpaired membership column",
                reason=(
                    f"Membership columns must come in pairs "
                    f"({{entity_key}}_id + {{entity_key}}_role). "
                    f"Found: {'; '.join(unpaired)}"
                ),
                fix=(
                    "Add the missing paired column for each membership column. "
                    "Both _id and _role are required for each group entity."
                ),
                invalid_names=tuple(unpaired),
                valid_names=tuple(
                    f"{ek}_id, {ek}_role" for ek in group_entity_keys
                ),
            )

        # All-or-nothing: if any membership columns exist, all group entities
        # must have complete pairs
        if missing_pairs:
            raise ApiMappingError(
                summary="Incomplete entity membership columns",
                reason=(
                    f"Found membership columns for: "
                    f"{', '.join(present_pairs)}. "
                    f"Missing membership columns for: "
                    f"{', '.join(missing_pairs)}. "
                    f"All group entities must have _id and _role columns "
                    f"when any membership columns are present."
                ),
                fix=(
                    f"Add {{entity_key}}_id and {{entity_key}}_role columns "
                    f"for: {', '.join(missing_pairs)}"
                ),
                invalid_names=tuple(missing_pairs),
                valid_names=tuple(group_entity_keys),
            )

        return detected

    def _resolve_valid_role_keys(
        self,
        tbs: Any,
    ) -> dict[str, frozenset[str]]:
        """Build a mapping of entity key → valid role keys from the TBS.

        Story 9.4 AC-4: Uses ``role.plural or role.key`` to match the dict
        keys expected by ``SimulationBuilder.build_from_entities()``.

        Args:
            tbs: The loaded TaxBenefitSystem.

        Returns:
            Dict mapping group entity key to frozenset of valid role keys.
        """
        valid_roles: dict[str, frozenset[str]] = {}

        for entity in tbs.entities:
            if getattr(entity, "is_person", False):
                continue

            role_keys: set[str] = set()
            roles = getattr(entity, "roles", ())
            for role in roles:
                plural = getattr(role, "plural", None)
                key = getattr(role, "key", None)
                role_dict_key = plural or key
                if role_dict_key:
                    role_keys.add(role_dict_key)

            valid_roles[entity.key] = frozenset(role_keys)

        return valid_roles

    def _validate_entity_relationships(
        self,
        person_table: pa.Table,
        membership_cols: dict[str, tuple[str, str]],
        valid_roles: dict[str, frozenset[str]],
    ) -> None:
        """Validate membership column values for nulls and invalid roles.

        Story 9.4 AC-3, AC-4, AC-5: Checks every membership column for null
        values and validates role values against the TBS role definitions.

        Args:
            person_table: The person entity PyArrow table.
            membership_cols: Detected membership columns per group entity.
            valid_roles: Valid role keys per group entity.

        Raises:
            ApiMappingError: If null values or invalid role values are found.
        """
        for entity_key, (id_col, role_col) in membership_cols.items():
            # AC-5: Null check on _id column.
            # Use a vectorised filter to get the first null index rather than
            # iterating element-by-element with .as_py() per row — the Python
            # for-loop is only reached on the exceptional error path, but keeping
            # it vectorised keeps the code consistent and avoids any O(n) per-
            # element overhead even on validation failures.
            id_array = person_table.column(id_col)
            null_mask = pa.compute.is_null(id_array)
            if pa.compute.any(null_mask).as_py():
                # Vectorised first-index extraction — one .as_py() call total.
                null_positions = pa.compute.filter(
                    pa.array(range(len(id_array))), null_mask
                )
                first_null = null_positions[0].as_py()
                raise ApiMappingError(
                    summary="Null value in membership column",
                    reason=(
                        f"Column '{id_col}' has null value at "
                        f"row index {first_null}. All membership columns "
                        f"must have non-null values."
                    ),
                    fix=(
                        f"Ensure every person has a valid "
                        f"{entity_key} group assignment in "
                        f"'{id_col}'."
                    ),
                    invalid_names=(id_col,),
                    valid_names=(),
                )

            # AC-5: Null check on _role column.
            role_array = person_table.column(role_col)
            null_mask = pa.compute.is_null(role_array)
            if pa.compute.any(null_mask).as_py():
                null_positions = pa.compute.filter(
                    pa.array(range(len(role_array))), null_mask
                )
                first_null = null_positions[0].as_py()
                raise ApiMappingError(
                    summary="Null value in membership column",
                    reason=(
                        f"Column '{role_col}' has null value at "
                        f"row index {first_null}. All membership columns "
                        f"must have non-null values."
                    ),
                    fix=(
                        f"Ensure every person has a valid role "
                        f"in '{role_col}'."
                    ),
                    invalid_names=(role_col,),
                    valid_names=(),
                )

            # AC-4: Role value validation — check unique values only (typically ≤4
            # distinct roles per entity regardless of population size) to avoid
            # an O(n) scan over all person records.
            entity_valid_roles = valid_roles.get(entity_key, frozenset())
            if entity_valid_roles:
                for value in pa.compute.unique(role_array).to_pylist():
                    if value not in entity_valid_roles:
                        raise ApiMappingError(
                            summary="Invalid role value",
                            reason=(
                                f"Role value '{value}' in column "
                                f"'{role_col}' is not valid for entity "
                                f"'{entity_key}'. Valid roles: "
                                f"{sorted(entity_valid_roles)}"
                            ),
                            fix=(
                                f"Use one of the valid role values for "
                                f"'{entity_key}': "
                                f"{sorted(entity_valid_roles)}"
                            ),
                            invalid_names=(str(value),),
                            valid_names=tuple(sorted(entity_valid_roles)),
                        )

    def _population_to_entity_dict(
        self,
        population: PopulationData,
        policy: PolicyConfig,
        period_str: str,
        tbs: Any,
    ) -> dict[str, Any]:
        """Convert PopulationData tables to the dict format expected by OpenFisca.

        OpenFisca's ``build_from_entities`` expects **plural** entity keys::

            {
                "individus": {
                    "person_0": {"salaire_de_base": {"2024": 30000.0}},
                    ...
                },
                "menages": {
                    "menage_0": {"personne_de_reference": ["person_0"]},
                    ...
                }
            }

        PopulationData tables may use either singular (entity.key) or plural
        (entity.plural) keys.  This method normalises to plural.

        Story 9.4: When membership columns are detected on the person table
        (``{entity_key}_id`` and ``{entity_key}_role``), the method switches
        to 4-entity mode — building group entity instances with role
        assignments from the membership columns instead of treating every
        table as an independent entity with period-wrapped columns.
        """
        result: dict[str, Any] = {}

        # Step 1: Build key→plural mapping for normalisation
        key_to_plural = {entity.key: entity.plural for entity in tbs.entities}
        plural_set = set(key_to_plural.values())

        # Step 2: Identify the person entity
        person_entity: Any = None
        for entity in tbs.entities:
            if getattr(entity, "is_person", False):
                person_entity = entity
                break

        person_entity_plural = person_entity.plural if person_entity else None

        # Step 2b: Find person_table_key in population.tables
        person_table_key: str | None = None
        if person_entity is not None:
            if person_entity.key in population.tables:
                person_table_key = person_entity.key
            elif person_entity.plural in population.tables:
                person_table_key = person_entity.plural

        # Step 3: Detect membership columns
        membership_cols: dict[str, tuple[str, str]] = {}
        if person_table_key is not None:
            person_table = population.tables[person_table_key]
            membership_cols = self._detect_membership_columns(person_table, tbs)

        # Step 4: No membership columns → execute existing all-tables loop
        if not membership_cols:
            for entity_key, table in population.tables.items():
                # Normalise to plural key
                plural_key = key_to_plural.get(entity_key, entity_key)
                if entity_key in plural_set:
                    plural_key = entity_key

                entity_dict: dict[str, Any] = {}
                columns = table.column_names
                num_rows = table.num_rows

                for i in range(num_rows):
                    instance_id = f"{entity_key}_{i}"
                    instance_data: dict[str, Any] = {}

                    for col in columns:
                        value = table.column(col)[i].as_py()
                        instance_data[col] = {period_str: value}

                    entity_dict[instance_id] = instance_data

                result[plural_key] = entity_dict

            # Inject policy parameters
            if (
                policy.parameters
                and person_entity_plural
                and person_entity_plural in result
            ):
                for instance_id in result[person_entity_plural]:
                    for param_key, param_value in policy.parameters.items():
                        result[person_entity_plural][instance_id][param_key] = {
                            period_str: param_value
                        }

            return result

        # Step 5: 4-entity mode — membership columns detected
        # Defensive: person_table_key should always be non-None here (membership
        # columns require a person table), but assert would be stripped by -O and
        # produce a cryptic KeyError. Raise ApiMappingError explicitly instead.
        if person_table_key is None:
            raise ApiMappingError(
                summary="Person entity table not found in population",
                reason=(
                    "Membership columns were detected but no table keyed by the "
                    "person entity singular or plural name was found in "
                    "population.tables."
                ),
                fix=(
                    "Include the person entity table (e.g. 'individu' or "
                    "'individus') in PopulationData.tables when using membership "
                    "columns."
                ),
                invalid_names=(),
                valid_names=(),
            )
        person_table = population.tables[person_table_key]

        # Step 5a: Resolve valid role keys
        valid_roles = self._resolve_valid_role_keys(tbs)

        # Step 5b: Validate entity relationships
        self._validate_entity_relationships(person_table, membership_cols, valid_roles)

        # Step 5c: Build set of membership column names to exclude from period-wrapping
        membership_col_names: set[str] = set()
        for id_col, role_col in membership_cols.values():
            membership_col_names.add(id_col)
            membership_col_names.add(role_col)

        # Step 5d: Build person instances FROM PERSON TABLE ONLY.
        # Pre-materialise non-membership columns as Python lists once to avoid
        # O(n×c) scalar-boxing inside the row loop (c = variable column count).
        var_columns: dict[str, list[Any]] = {
            col: person_table.column(col).to_pylist()
            for col in person_table.column_names
            if col not in membership_col_names
        }
        person_dict: dict[str, Any] = {
            f"{person_table_key}_{i}": {
                col: {period_str: vals[i]}
                for col, vals in var_columns.items()
            }
            for i in range(person_table.num_rows)
        }

        # Defensive: person_entity_plural should always be non-None for valid TBS
        # instances, but `assert` is stripped by -O and `result[None] = ...` would
        # silently corrupt the entity dict. Raise ApiMappingError explicitly.
        if person_entity_plural is None:
            raise ApiMappingError(
                summary="Cannot determine person entity plural name",
                reason=(
                    "The person entity in the TaxBenefitSystem has no .plural "
                    "attribute. This indicates an incompatible OpenFisca version "
                    "or malformed TBS."
                ),
                fix="Check the OpenFisca compatibility matrix.",
                invalid_names=(),
                valid_names=(),
            )
        result[person_entity_plural] = person_dict

        # Step 5e: Build group entity instances from membership columns.
        # Single-pass O(n) approach: materialise each id/role array to a Python
        # list once, then group persons by (group_id, role_key) in one iteration.
        # The original O(n×g) nested loop (one inner scan per distinct group ID)
        # would take O(n×g) = O(250k × 100k) ≈ 25 billion ops for a realistic
        # French population — this replaces it with O(n) regardless of group count.
        for group_entity_key, (id_col, role_col) in membership_cols.items():
            id_array = person_table.column(id_col)
            role_array = person_table.column(role_col)

            # Materialise ONCE to Python lists — avoids repeated .as_py() per element.
            id_list = id_array.to_pylist()
            role_list = role_array.to_pylist()
            sorted_group_ids = sorted(set(id_list))

            # Single O(n) pass: group person IDs by (group_id, role_key)
            role_assignments_by_group: dict[Any, dict[str, list[str]]] = {}
            for i, (gid, rkey) in enumerate(zip(id_list, role_list)):
                person_id = f"{person_table_key}_{i}"
                role_assignments_by_group.setdefault(gid, {}).setdefault(
                    rkey, []
                ).append(person_id)

            group_dict: dict[str, Any] = {
                f"{group_entity_key}_{group_id}": role_assignments_by_group.get(
                    group_id, {}
                )
                for group_id in sorted_group_ids
            }

            group_plural = key_to_plural[group_entity_key]
            result[group_plural] = group_dict

        # Step 5f: Merge group entity table variables (if present)
        for group_entity_key, (id_col, _role_col) in membership_cols.items():
            # Check if a group entity table exists in population.tables
            group_table: pa.Table | None = None
            group_table_key: str | None = None
            group_plural = key_to_plural[group_entity_key]

            if group_entity_key in population.tables and group_entity_key != person_table_key:
                group_table = population.tables[group_entity_key]
                group_table_key = group_entity_key
            elif group_plural in population.tables and group_plural != person_table_key:
                group_table = population.tables[group_plural]
                group_table_key = group_plural

            if group_table is None:
                continue

            # Get sorted distinct group IDs from person table's _id column
            id_array = person_table.column(id_col)
            sorted_group_ids = sorted(pa.compute.unique(id_array).to_pylist())

            # Validate row count match
            if group_table.num_rows != len(sorted_group_ids):
                raise ApiMappingError(
                    summary="Group entity table row count mismatch",
                    reason=(
                        f"Group entity table '{group_table_key}' has "
                        f"{group_table.num_rows} rows but the person table "
                        f"has {len(sorted_group_ids)} distinct "
                        f"'{id_col}' values. Row counts must match."
                    ),
                    fix=(
                        f"Ensure the '{group_table_key}' table has exactly "
                        f"{len(sorted_group_ids)} rows, one per distinct "
                        f"group ID in the person table's '{id_col}' column."
                    ),
                    invalid_names=(str(group_table_key),),
                    valid_names=(),
                )

            # Positional match: row i → sorted_group_ids[i]
            # ⚠️ ORDERING ASSUMPTION: group table rows must be ordered by ascending
            # {entity_key}_id value from the person table. Mismatched order causes
            # silent per-row value swapping (no error raised). Log a warning so
            # this assumption is visible in structured logs during debugging.
            logger.warning(
                "event=group_entity_table_positional_merge "
                "entity=%s table_key=%s sorted_ids=%s "
                "assumption=rows_ordered_by_ascending_group_id",
                group_entity_key,
                group_table_key,
                sorted_group_ids,
            )
            for i, group_id in enumerate(sorted_group_ids):
                instance_id = f"{group_entity_key}_{group_id}"
                for col in group_table.column_names:
                    value = group_table.column(col)[i].as_py()
                    result[group_plural][instance_id][col] = {period_str: value}

        # Step 5g: Inject policy parameters into person entity instances
        if policy.parameters and person_entity_plural in result:
            for instance_id in result[person_entity_plural]:
                for param_key, param_value in policy.parameters.items():
                    result[person_entity_plural][instance_id][param_key] = {
                        period_str: param_value
                    }

        return result

    # ------------------------------------------------------------------
    # Story 9.2: Entity-aware result extraction
    # ------------------------------------------------------------------

    def _resolve_variable_entities(
        self, tbs: Any
    ) -> dict[str, list[str]]:
        """Group output variables by their entity's plural name.

        Queries ``tbs.variables[var_name].entity`` to determine which entity
        each output variable belongs to, then groups them.

        Args:
            tbs: The loaded TaxBenefitSystem.

        Returns:
            Dict mapping entity plural name to list of variable names.
            E.g. ``{"individus": ["salaire_net"], "foyers_fiscaux": ["irpp"]}``.

        Raises:
            ApiMappingError: If a variable's entity cannot be determined.
        """
        vars_by_entity: dict[str, list[str]] = {}

        for var_name in self._output_variables:
            variable = tbs.variables.get(var_name)
            if variable is None:
                # Should not happen — _validate_output_variables runs first.
                # Defensive guard for edge cases.
                raise ApiMappingError(
                    summary="Cannot resolve variable entity",
                    reason=(
                        f"Variable '{var_name}' not found in "
                        f"{self._country_package} TaxBenefitSystem"
                    ),
                    fix=(
                        "Ensure the variable exists in the country package. "
                        "This may indicate the TBS was modified after validation."
                    ),
                    invalid_names=(var_name,),
                    valid_names=tuple(sorted(tbs.variables.keys())),
                )

            entity = getattr(variable, "entity", None)
            if entity is None:
                raise ApiMappingError(
                    summary="Cannot determine entity for variable",
                    reason=(
                        f"Variable '{var_name}' has no .entity attribute in "
                        f"{self._country_package} TaxBenefitSystem"
                    ),
                    fix=(
                        "This variable may not be properly defined in the "
                        "country package. Check the variable definition."
                    ),
                    invalid_names=(var_name,),
                    valid_names=tuple(sorted(tbs.variables.keys())),
                )

            entity_plural = getattr(entity, "plural", None)
            if entity_plural is None:
                # entity.plural is required — silently falling back to entity.key
                # would produce wrong plural keys (e.g. "foyer_fiscal" instead of
                # "foyers_fiscaux") causing subtle downstream lookup failures.
                # This path only occurs with a malformed/incompatible TBS.
                entity_key = getattr(entity, "key", None)
                raise ApiMappingError(
                    summary="Cannot determine entity plural name for variable",
                    reason=(
                        f"Variable '{var_name}' entity has no .plural attribute"
                        + (
                            f" (entity.key={entity_key!r})"
                            if entity_key
                            else ", no .key attribute either"
                        )
                    ),
                    fix=(
                        "This may indicate an incompatible OpenFisca version. "
                        "Check the OpenFisca compatibility matrix."
                    ),
                    invalid_names=(var_name,),
                    valid_names=tuple(sorted(tbs.variables.keys())),
                )

            vars_by_entity.setdefault(entity_plural, []).append(var_name)

        logger.debug(
            "entity_variable_mapping=%s output_variables=%s",
            {k: v for k, v in vars_by_entity.items()},
            list(self._output_variables),
        )

        return vars_by_entity

    def _extract_results_by_entity(
        self,
        simulation: Any,
        period: int,
        vars_by_entity: dict[str, list[str]],
        variable_periodicities: dict[str, str],
    ) -> dict[str, pa.Table]:
        """Extract output variables grouped by entity into per-entity tables.

        For each entity group, calls the appropriate calculation method
        (``calculate()`` or ``calculate_add()``) for its variables and
        builds a ``pa.Table`` per entity. Arrays within an entity group
        share the same length (entity instance count).

        Story 9.3: Uses ``_calculate_variable()`` for periodicity-aware
        dispatch instead of calling ``simulation.calculate()`` directly.

        Args:
            simulation: The completed OpenFisca simulation.
            period: Computation period (integer year).
            vars_by_entity: Output variables grouped by entity plural name
                (from ``_resolve_variable_entities``).
            variable_periodicities: Periodicity per variable
                (from ``_resolve_variable_periodicities``).

        Returns:
            Dict mapping entity plural name to a PyArrow Table containing
            that entity's output variables.
        """
        period_str = str(period)
        entity_tables: dict[str, pa.Table] = {}

        for entity_plural, var_names in vars_by_entity.items():
            arrays: dict[str, pa.Array] = {}
            for var_name in var_names:
                periodicity = variable_periodicities[var_name]
                numpy_array = self._calculate_variable(
                    simulation, var_name, period_str, periodicity
                )
                arrays[var_name] = pa.array(numpy_array)
            entity_tables[entity_plural] = pa.table(arrays)

        return entity_tables

    def _select_primary_output(
        self,
        entity_tables: dict[str, pa.Table],
        tbs: Any,
    ) -> pa.Table:
        """Select the primary output_fields table for backward compatibility.

        When all variables belong to one entity, returns that entity's table.
        When variables span multiple entities, returns the person-entity table
        (or the first entity's table if no person entity is present).

        Args:
            entity_tables: Per-entity output tables.
            tbs: The loaded TaxBenefitSystem.

        Returns:
            A single PyArrow Table to use as ``output_fields``.
        """
        if len(entity_tables) == 1:
            return next(iter(entity_tables.values()))

        # Find the person entity plural name
        for entity in tbs.entities:
            if getattr(entity, "is_person", False):
                person_plural = entity.plural
                if person_plural in entity_tables:
                    return entity_tables[person_plural]

        # Fallback: return the first entity's table
        return next(iter(entity_tables.values()))


]]></file>
<file id="e38c6079" path="tests/computation/test_openfisca_api_adapter.py" label="SOURCE CODE"><![CDATA[

"""Tests for OpenFiscaApiAdapter (Story 1.6: Direct OpenFisca API mode).

All OpenFisca internals are mocked since openfisca-core is an optional
dependency and may not be installed in CI.

Story 9.2: Added tests for multi-entity output array handling — entity-aware
result extraction, per-entity tables, and backward compatibility.

Story 9.4: Added tests for 4-entity PopulationData format with membership
columns — detect membership columns, resolve valid role keys, validate entity
relationships, and refactored _population_to_entity_dict() for 4-entity mode.
"""

from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pyarrow as pa
import pytest

np = pytest.importorskip("numpy")

from reformlab.computation.adapter import ComputationAdapter
from reformlab.computation.exceptions import ApiMappingError, CompatibilityError
from reformlab.computation.openfisca_api_adapter import OpenFiscaApiAdapter
from reformlab.computation.types import ComputationResult, PolicyConfig, PopulationData

# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------

# Install a fake openfisca_core.simulation_builder module so that
# `from openfisca_core.simulation_builder import SimulationBuilder`
# inside _build_simulation can be patched. We register it once in
# sys.modules so the import succeeds, then individual tests patch
# the SimulationBuilder attribute.

_mock_sim_builder_module = MagicMock()
sys.modules.setdefault("openfisca_core", MagicMock())
sys.modules.setdefault("openfisca_core.simulation_builder", _mock_sim_builder_module)


def _make_mock_tbs(
    entity_keys: tuple[str, ...] = ("persons", "households"),
    variable_names: tuple[str, ...] = ("income_tax", "carbon_tax", "salary"),
    person_entity: str = "persons",
) -> MagicMock:
    """Create a mock TaxBenefitSystem with configurable entities and variables."""
    tbs = MagicMock()

    entities = []
    entities_by_key: dict[str, SimpleNamespace] = {}
    for key in entity_keys:
        entity = SimpleNamespace(key=key, plural=key, is_person=(key == person_entity))
        entities.append(entity)
        entities_by_key[key] = entity
    tbs.entities = entities

    # Variables get a default entity (the person entity) for backward compatibility
    # with existing tests that don't need entity-aware behavior.
    # Story 9.3: Also set definition_period = "year" by default. Without this,
    # MagicMock().definition_period returns a MagicMock object whose str()
    # representation ("<MagicMock ...>") is not in _VALID_PERIODICITIES, causing
    # _resolve_variable_periodicities() to raise ApiMappingError("Unexpected
    # periodicity...") and breaking all existing compute() unit tests.
    default_entity = entities_by_key.get(person_entity, entities[0])
    variables: dict[str, Any] = {}
    for name in variable_names:
        var_mock = MagicMock()
        var_mock.entity = default_entity
        var_mock.definition_period = "year"
        variables[name] = var_mock
    tbs.variables = variables

    return tbs


def _make_mock_tbs_with_entities(
    entity_keys: tuple[str, ...] = ("individu", "foyer_fiscal", "menage"),
    entity_plurals: dict[str, str] | None = None,
    variable_entities: dict[str, str] | None = None,
    variable_periodicities: dict[str, str] | None = None,
    person_entity: str = "individu",
    entity_roles: dict[str, list[dict[str, str | None]]] | None = None,
) -> MagicMock:
    """Create a mock TBS where variables know their entity.

    Story 9.2: Extended mock for entity-aware extraction tests.
    Story 9.3: Added variable_periodicities parameter for periodicity-aware tests.
    Story 9.4: Added entity_roles parameter for 4-entity format tests.

    Args:
        entity_keys: Entity singular keys.
        entity_plurals: Mapping of singular key to plural form.
            Defaults to appending "s" (with special cases).
        variable_entities: Mapping of variable name to entity key.
        variable_periodicities: Mapping of variable name to periodicity string
            (e.g. "month", "year", "eternity"). Defaults to "year" for all.
        person_entity: Which entity key is the person entity.
        entity_roles: Mapping of group entity key to list of role dicts.
            Each role dict has "key" and "plural" (can be None).
            E.g. {"famille": [{"key": "parent", "plural": "parents"}, ...]}.
            Person entity gets empty roles list.

    Returns:
        Mock TBS with entity-aware variables and role information.
    """
    tbs = MagicMock()

    # Default plurals for French entities
    default_plurals = {
        "individu": "individus",
        "famille": "familles",
        "foyer_fiscal": "foyers_fiscaux",
        "menage": "menages",
    }
    if entity_plurals is None:
        entity_plurals = {}
    if variable_periodicities is None:
        variable_periodicities = {}
    if entity_roles is None:
        entity_roles = {}

    entities_by_key: dict[str, SimpleNamespace] = {}
    entities = []
    for key in entity_keys:
        plural = entity_plurals.get(key) or default_plurals.get(key) or key + "s"
        is_person = key == person_entity

        # Story 9.4: Build role objects for group entities
        roles: list[SimpleNamespace] = []
        if not is_person and key in entity_roles:
            for role_def in entity_roles[key]:
                roles.append(SimpleNamespace(
                    key=role_def["key"],
                    plural=role_def.get("plural"),
                ))

        entity = SimpleNamespace(
            key=key,
            plural=plural,
            is_person=is_person,
            roles=roles,
        )
        entities.append(entity)
        entities_by_key[key] = entity
    tbs.entities = entities

    # Build variables with entity references
    # Story 9.3: Also set definition_period (default "year" for backward compat)
    if variable_entities is None:
        variable_entities = {}
    variables: dict[str, Any] = {}
    for var_name, entity_key in variable_entities.items():
        var_mock = MagicMock()
        var_mock.entity = entities_by_key[entity_key]
        var_mock.definition_period = variable_periodicities.get(var_name, "year")
        variables[var_name] = var_mock
    tbs.variables = variables

    return tbs


# Story 9.4: Standard French entity roles for reuse across test classes
_FRENCH_ENTITY_ROLES: dict[str, list[dict[str, str | None]]] = {
    "famille": [
        {"key": "parent", "plural": "parents"},
        {"key": "enfant", "plural": "enfants"},
    ],
    "foyer_fiscal": [
        {"key": "declarant", "plural": "declarants"},
        {"key": "personne_a_charge", "plural": "personnes_a_charge"},
    ],
    "menage": [
        {"key": "personne_de_reference", "plural": None},
        {"key": "conjoint", "plural": None},
        {"key": "enfant", "plural": "enfants"},
        {"key": "autre", "plural": "autres"},
    ],
}


def _make_mock_simulation(
    results: dict[str, np.ndarray],
) -> MagicMock:
    """Create a mock Simulation that returns given arrays for calculate()."""
    sim = MagicMock()
    sim.calculate.side_effect = lambda var, period: results[var]
    return sim


def _patch_simulation_builder(mock_builder_instance: MagicMock):  # type: ignore[no-untyped-def]
    """Patch SimulationBuilder in the fake openfisca_core.simulation_builder module."""
    return patch.object(
        _mock_sim_builder_module,
        "SimulationBuilder",
        return_value=mock_builder_instance,
    )


@pytest.fixture()
def sample_population() -> PopulationData:
    return PopulationData(
        tables={
            "persons": pa.table(
                {
                    "person_id": pa.array([1, 2, 3]),
                    "salary": pa.array([30000.0, 45000.0, 60000.0]),
                }
            ),
        },
        metadata={"source": "test"},
    )


@pytest.fixture()
def sample_policy() -> PolicyConfig:
    return PolicyConfig(
        parameters={"salary": 35000.0},
        name="test-policy",
    )


@pytest.fixture()
def empty_policy() -> PolicyConfig:
    return PolicyConfig(parameters={}, name="no-params")


# ---------------------------------------------------------------------------
# AC-7: Protocol compliance
# ---------------------------------------------------------------------------


class TestProtocolCompliance:
    """AC-7: isinstance(OpenFiscaApiAdapter(...), ComputationAdapter) returns True."""

    def test_isinstance_check(self) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        assert isinstance(adapter, ComputationAdapter)

    def test_has_compute_method(self) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        assert callable(getattr(adapter, "compute", None))

    def test_has_version_method(self) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        assert callable(getattr(adapter, "version", None))


# ---------------------------------------------------------------------------
# AC-2: Version-pinned execution
# ---------------------------------------------------------------------------


class TestVersionChecking:
    """AC-2: Version validation reuses shared logic from openfisca_common."""

    def test_supported_version_passes(self) -> None:
        with patch(
            "reformlab.computation.openfisca_api_adapter._detect_openfisca_version",
            return_value="44.2.2",
        ):
            adapter = OpenFiscaApiAdapter(output_variables=("income_tax",))
            assert adapter.version() == "44.2.2"

    def test_unsupported_version_raises(self) -> None:
        with patch(
            "reformlab.computation.openfisca_api_adapter._detect_openfisca_version",
            return_value="30.0.0",
        ):
            with pytest.raises(CompatibilityError) as exc_info:
                OpenFiscaApiAdapter(output_variables=("income_tax",))
            assert "30.0.0" in str(exc_info.value)

    def test_skip_version_check(self) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        assert adapter.version() == "unknown"


# ---------------------------------------------------------------------------
# AC-8: Graceful degradation when OpenFisca not installed
# ---------------------------------------------------------------------------


class TestGracefulDegradation:
    """AC-8: Missing openfisca-core raises CompatibilityError, not ImportError."""

    def test_not_installed_raises_compatibility_error(self) -> None:
        with patch(
            "reformlab.computation.openfisca_api_adapter._detect_openfisca_version",
            return_value="not-installed",
        ):
            with pytest.raises(CompatibilityError) as exc_info:
                OpenFiscaApiAdapter(output_variables=("income_tax",))
            assert "not installed" in str(exc_info.value).lower()
            assert exc_info.value.actual == "not-installed"

    def test_not_installed_is_not_import_error(self) -> None:
        """Verify the error type is CompatibilityError, NOT ImportError."""
        with patch(
            "reformlab.computation.openfisca_api_adapter._detect_openfisca_version",
            return_value="not-installed",
        ):
            with pytest.raises(CompatibilityError):
                OpenFiscaApiAdapter(output_variables=("income_tax",))


# ---------------------------------------------------------------------------
# AC-3: TaxBenefitSystem configuration (lazy loading + caching)
# ---------------------------------------------------------------------------


class TestTaxBenefitSystemLoading:
    """AC-3: Country package is imported, TBS is instantiated and cached."""

    def test_missing_country_package_raises_compatibility_error(self) -> None:
        adapter = OpenFiscaApiAdapter(
            country_package="openfisca_nonexistent",
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        with patch(
            "importlib.import_module",
            side_effect=ImportError("No module named 'openfisca_nonexistent'"),
        ):
            with pytest.raises(CompatibilityError) as exc_info:
                adapter._get_tax_benefit_system()
            assert "openfisca_nonexistent" in str(exc_info.value)
            assert "not-installed" == exc_info.value.actual

    def test_tbs_is_cached_after_first_load(self) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs()
        mock_module = MagicMock()
        mock_module.CountryTaxBenefitSystem.return_value = mock_tbs

        with patch(
            "importlib.import_module",
            return_value=mock_module,
        ) as mock_import:
            tbs1 = adapter._get_tax_benefit_system()
            tbs2 = adapter._get_tax_benefit_system()

            assert tbs1 is tbs2
            mock_import.assert_called_once()


# ---------------------------------------------------------------------------
# AC-1: Live computation via OpenFisca Python API
# ---------------------------------------------------------------------------


class TestCompute:
    """AC-1: compute() invokes SimulationBuilder and Simulation.calculate()."""

    def test_compute_returns_computation_result(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 2025)

        assert isinstance(result, ComputationResult)
        assert isinstance(result.output_fields, pa.Table)
        assert result.period == 2025
        assert result.output_fields.num_rows == 3
        assert result.output_fields.column_names == ["income_tax"]

    def test_compute_with_policy_parameters(
        self, sample_population: PopulationData, sample_policy: PolicyConfig
    ) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3500.0, 3500.0, 3500.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, sample_policy, 2025)

        assert isinstance(result, ComputationResult)
        call_args = mock_builder_instance.build_from_entities.call_args
        entities_dict = call_args[0][1]
        for instance_data in entities_dict["persons"].values():
            assert "salary" in instance_data

    def test_compute_multiple_output_variables(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax", "carbon_tax"),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {
                "income_tax": np.array([3000.0, 6750.0, 12000.0]),
                "carbon_tax": np.array([134.0, 200.0, 267.0]),
            }
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 2025)

        assert result.output_fields.column_names == ["income_tax", "carbon_tax"]
        assert result.output_fields.num_rows == 3


# ---------------------------------------------------------------------------
# AC-4: Variable selection — unknown variables raise structured error
# ---------------------------------------------------------------------------


class TestOutputVariableValidation:
    """AC-4: Unknown variable names raise a clear error before computation."""

    def test_unknown_variable_raises_api_mapping_error(self) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax", "nonexistent_var"),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs(variable_names=("income_tax", "carbon_tax", "salary"))

        with pytest.raises(ApiMappingError) as exc_info:
            adapter._validate_output_variables(mock_tbs)

        assert "nonexistent_var" in str(exc_info.value)
        assert exc_info.value.invalid_names == ("nonexistent_var",)

    def test_valid_variables_pass_validation(self) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs(variable_names=("income_tax", "carbon_tax"))
        adapter._validate_output_variables(mock_tbs)

    def test_suggestions_for_close_matches(self) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("incme_tax",),  # typo
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs(variable_names=("income_tax", "carbon_tax", "salary"))

        with pytest.raises(ApiMappingError) as exc_info:
            adapter._validate_output_variables(mock_tbs)

        assert "incme_tax" in exc_info.value.invalid_names
        assert len(exc_info.value.suggestions) > 0

    def test_empty_output_variables_raises_error(self) -> None:
        """Empty output_variables tuple raises ApiMappingError at construction time."""
        with pytest.raises(ApiMappingError) as exc_info:
            OpenFiscaApiAdapter(
                output_variables=(),
                skip_version_check=True,
            )
        assert "Empty output_variables" in exc_info.value.summary


# ---------------------------------------------------------------------------
# AC-5: Period mapping
# ---------------------------------------------------------------------------


class TestPeriodFormatting:
    """AC-5: Integer period is correctly passed as OpenFisca period string."""

    def test_period_passed_as_string(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            adapter.compute(sample_population, empty_policy, 2025)

        mock_simulation.calculate.assert_called_once_with("income_tax", "2025")


# ---------------------------------------------------------------------------
# AC-6: ComputationResult compatibility
# ---------------------------------------------------------------------------


class TestComputationResultStructure:
    """AC-6: Result has correct metadata and structure."""

    def test_metadata_source_is_api(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 2025)

        assert result.metadata["source"] == "api"

    def test_adapter_version_in_result(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        with patch(
            "reformlab.computation.openfisca_api_adapter._detect_openfisca_version",
            return_value="44.2.2",
        ):
            adapter = OpenFiscaApiAdapter(output_variables=("income_tax",))

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 2025)

        assert result.adapter_version == "44.2.2"

    def test_output_fields_is_pyarrow_table(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 2025)

        assert isinstance(result.output_fields, pa.Table)

    def test_metadata_includes_required_fields(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 2025)

        assert "timing_seconds" in result.metadata
        assert "row_count" in result.metadata
        assert "source" in result.metadata
        assert "policy_name" in result.metadata
        assert "country_package" in result.metadata
        assert "output_variables" in result.metadata
        assert result.metadata["row_count"] == 3
        assert result.metadata["country_package"] == "openfisca_france"
        assert result.metadata["output_variables"] == ["income_tax"]

    def test_period_is_correct(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 2025)

        assert result.period == 2025


# ---------------------------------------------------------------------------
# AC-9: Coexistence with pre-computed mode
# ---------------------------------------------------------------------------


class TestCoexistence:
    """AC-9: Both adapters instantiate independently."""

    def test_both_adapters_instantiate(self, tmp_path: object) -> None:
        from reformlab.computation.openfisca_adapter import OpenFiscaAdapter

        pre_computed = OpenFiscaAdapter(data_dir=str(tmp_path), skip_version_check=True)
        api_adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        assert isinstance(pre_computed, ComputationAdapter)
        assert isinstance(api_adapter, ComputationAdapter)
        assert type(pre_computed) is not type(api_adapter)

    def test_adapters_do_not_share_state(self, tmp_path: object) -> None:
        from reformlab.computation.openfisca_adapter import OpenFiscaAdapter

        pre_computed = OpenFiscaAdapter(data_dir=str(tmp_path), skip_version_check=True)
        api_adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        # Both return "unknown" when skip_version_check=True
        assert pre_computed.version() == "unknown"
        assert api_adapter.version() == "unknown"
        # They are distinct objects with no shared mutable state
        assert pre_computed is not api_adapter


# ---------------------------------------------------------------------------
# Entity mapping errors
# ---------------------------------------------------------------------------


class TestEntityMapping:
    """Entity keys in PopulationData must match TBS entity names."""

    def test_unknown_entity_raises_api_mapping_error(
        self, sample_policy: PolicyConfig
    ) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs(entity_keys=("persons", "households"))
        adapter._tax_benefit_system = mock_tbs

        bad_population = PopulationData(
            tables={
                "unknown_entity": pa.table({"x": pa.array([1])}),
            },
        )

        mock_builder_instance = MagicMock()
        with _patch_simulation_builder(mock_builder_instance):
            with pytest.raises(ApiMappingError) as exc_info:
                adapter.compute(bad_population, sample_policy, 2025)

        assert "unknown_entity" in str(exc_info.value)
        assert exc_info.value.invalid_names == ("unknown_entity",)

    def test_unknown_policy_parameter_raises_api_mapping_error(self) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs(variable_names=("income_tax", "salary"))
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "persons": pa.table({"salary": pa.array([30000.0])}),
            },
        )
        bad_policy = PolicyConfig(
            parameters={"nonexistent_param": 100.0},
            name="bad-policy",
        )

        mock_builder_instance = MagicMock()
        with _patch_simulation_builder(mock_builder_instance):
            with pytest.raises(ApiMappingError) as exc_info:
                adapter.compute(population, bad_policy, 2025)

        assert "nonexistent_param" in str(exc_info.value)


# ===========================================================================
# Story 9.2: Multi-entity output array handling
# ===========================================================================


class TestResolveVariableEntities:
    """Story 9.2 AC-1, AC-2, AC-5: Variable-to-entity mapping from TBS."""

    def test_groups_variables_by_entity(self) -> None:
        """AC-1: Variables are correctly grouped by their entity."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "irpp", "revenu_disponible"),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={
                "salaire_net": "individu",
                "irpp": "foyer_fiscal",
                "revenu_disponible": "menage",
            },
        )
        adapter._tax_benefit_system = mock_tbs

        result = adapter._resolve_variable_entities(mock_tbs)

        assert "individus" in result
        assert "foyers_fiscaux" in result
        assert "menages" in result
        assert result["individus"] == ["salaire_net"]
        assert result["foyers_fiscaux"] == ["irpp"]
        assert result["menages"] == ["revenu_disponible"]

    def test_multiple_variables_same_entity(self) -> None:
        """AC-1: Multiple variables on the same entity are grouped together."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "age"),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={
                "salaire_net": "individu",
                "age": "individu",
            },
        )
        adapter._tax_benefit_system = mock_tbs

        result = adapter._resolve_variable_entities(mock_tbs)

        assert len(result) == 1
        assert "individus" in result
        assert result["individus"] == ["salaire_net", "age"]

    def test_variable_without_entity_raises_error(self) -> None:
        """AC-5: Variable with no .entity attribute raises ApiMappingError."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("broken_var",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={},
        )
        # Add a variable without entity attribute
        var_mock = MagicMock()
        var_mock.entity = None
        mock_tbs.variables["broken_var"] = var_mock

        with pytest.raises(ApiMappingError, match="Cannot determine entity"):
            adapter._resolve_variable_entities(mock_tbs)

    def test_variable_not_in_tbs_raises_error(self) -> None:
        """AC-5: Variable not in TBS raises ApiMappingError."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("nonexistent_var",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={},
        )
        # TBS has no variables at all

        with pytest.raises(ApiMappingError, match="Cannot resolve variable entity"):
            adapter._resolve_variable_entities(mock_tbs)


class TestExtractResultsByEntity:
    """Story 9.2 AC-1, AC-2, AC-3: Per-entity result extraction."""

    def test_single_entity_extraction(self) -> None:
        """AC-1: Single entity produces one table."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net",),
            skip_version_check=True,
        )
        mock_simulation = _make_mock_simulation(
            {"salaire_net": np.array([20000.0, 35000.0])}
        )
        vars_by_entity = {"individus": ["salaire_net"]}
        # Story 9.3: Pass variable_periodicities (required parameter)
        variable_periodicities = {"salaire_net": "year"}

        result = adapter._extract_results_by_entity(
            mock_simulation, 2024, vars_by_entity, variable_periodicities
        )

        assert "individus" in result
        assert result["individus"].num_rows == 2
        assert result["individus"].column_names == ["salaire_net"]

    def test_multi_entity_extraction(self) -> None:
        """AC-2, AC-3: Different entities produce separate tables with correct lengths."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "irpp", "revenu_disponible"),
            skip_version_check=True,
        )
        mock_simulation = _make_mock_simulation({
            "salaire_net": np.array([20000.0, 35000.0]),
            "irpp": np.array([-1500.0]),
            "revenu_disponible": np.array([40000.0]),
        })
        vars_by_entity = {
            "individus": ["salaire_net"],
            "foyers_fiscaux": ["irpp"],
            "menages": ["revenu_disponible"],
        }
        # Story 9.3: Pass variable_periodicities (required parameter)
        variable_periodicities = {
            "salaire_net": "year",
            "irpp": "year",
            "revenu_disponible": "year",
        }

        result = adapter._extract_results_by_entity(
            mock_simulation, 2024, vars_by_entity, variable_periodicities
        )

        assert len(result) == 3
        assert result["individus"].num_rows == 2
        assert result["foyers_fiscaux"].num_rows == 1
        assert result["menages"].num_rows == 1

    def test_multiple_variables_per_entity(self) -> None:
        """AC-3: Multiple variables on same entity are in the same table."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "age"),
            skip_version_check=True,
        )
        mock_simulation = _make_mock_simulation({
            "salaire_net": np.array([20000.0, 35000.0]),
            "age": np.array([30.0, 45.0]),
        })
        vars_by_entity = {"individus": ["salaire_net", "age"]}
        # Story 9.3: Pass variable_periodicities (required parameter)
        variable_periodicities = {"salaire_net": "year", "age": "year"}

        result = adapter._extract_results_by_entity(
            mock_simulation, 2024, vars_by_entity, variable_periodicities
        )

        assert result["individus"].num_rows == 2
        assert set(result["individus"].column_names) == {"salaire_net", "age"}


class TestSelectPrimaryOutput:
    """Story 9.2 AC-4: Primary output_fields selection for backward compatibility."""

    def test_single_entity_returns_that_table(self) -> None:
        """AC-4: With one entity, output_fields is that entity's table."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net",),
            skip_version_check=True,
        )
        person_table = pa.table({"salaire_net": pa.array([20000.0, 35000.0])})
        mock_tbs = _make_mock_tbs_with_entities()

        result = adapter._select_primary_output({"individus": person_table}, mock_tbs)

        assert result is person_table

    def test_multi_entity_returns_person_table(self) -> None:
        """AC-4: With multiple entities, output_fields is the person-entity table."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "irpp"),
            skip_version_check=True,
        )
        person_table = pa.table({"salaire_net": pa.array([20000.0, 35000.0])})
        foyer_table = pa.table({"irpp": pa.array([-1500.0])})
        mock_tbs = _make_mock_tbs_with_entities()

        result = adapter._select_primary_output(
            {"individus": person_table, "foyers_fiscaux": foyer_table},
            mock_tbs,
        )

        assert result is person_table

    def test_multi_entity_without_person_returns_first(self) -> None:
        """AC-4: Without person entity in results, returns first entity's table."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("irpp", "revenu_disponible"),
            skip_version_check=True,
        )
        foyer_table = pa.table({"irpp": pa.array([-1500.0])})
        menage_table = pa.table({"revenu_disponible": pa.array([40000.0])})
        mock_tbs = _make_mock_tbs_with_entities()

        result = adapter._select_primary_output(
            {"foyers_fiscaux": foyer_table, "menages": menage_table},
            mock_tbs,
        )

        assert result is foyer_table


# ===========================================================================
# Story 9.3: Variable periodicity handling
# ===========================================================================


def _make_mock_simulation_with_methods(
    results: dict[str, np.ndarray],
) -> MagicMock:
    """Mock simulation that tracks calculate vs calculate_add calls.

    Story 9.3: Used for periodicity dispatch verification.
    """
    sim = MagicMock()
    sim.calculate.side_effect = lambda var, period: results[var]
    sim.calculate_add.side_effect = lambda var, period: results[var]
    return sim


class TestResolveVariablePeriodicities:
    """Story 9.3 AC-1, AC-2, AC-6: Periodicity detection from TBS variables."""

    def test_detects_yearly_periodicity(self) -> None:
        """AC-1: Yearly variable detected correctly."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("irpp",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={"irpp": "foyer_fiscal"},
            variable_periodicities={"irpp": "year"},
        )

        result = adapter._resolve_variable_periodicities(mock_tbs)

        assert result == {"irpp": "year"}

    def test_detects_monthly_periodicity(self) -> None:
        """AC-2: Monthly variable detected correctly."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={"salaire_net": "individu"},
            variable_periodicities={"salaire_net": "month"},
        )

        result = adapter._resolve_variable_periodicities(mock_tbs)

        assert result == {"salaire_net": "month"}

    def test_detects_eternity_periodicity(self) -> None:
        """AC-6: Eternity variable detected correctly."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("date_naissance",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={"date_naissance": "individu"},
            variable_periodicities={"date_naissance": "eternity"},
        )

        result = adapter._resolve_variable_periodicities(mock_tbs)

        assert result == {"date_naissance": "eternity"}

    def test_detects_mixed_periodicities(self) -> None:
        """AC-1, AC-2, AC-6: Mixed periodicities detected for multiple variables."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "irpp", "date_naissance"),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={
                "salaire_net": "individu",
                "irpp": "foyer_fiscal",
                "date_naissance": "individu",
            },
            variable_periodicities={
                "salaire_net": "month",
                "irpp": "year",
                "date_naissance": "eternity",
            },
        )

        result = adapter._resolve_variable_periodicities(mock_tbs)

        assert result == {
            "salaire_net": "month",
            "irpp": "year",
            "date_naissance": "eternity",
        }

    def test_missing_definition_period_raises_error(self) -> None:
        """AC-1: Variable with no definition_period attribute raises ApiMappingError."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("broken_var",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={},
        )
        # Add variable without definition_period (set to None explicitly)
        var_mock = MagicMock()
        var_mock.entity = SimpleNamespace(key="individu", plural="individus", is_person=True)
        var_mock.definition_period = None
        mock_tbs.variables["broken_var"] = var_mock

        with pytest.raises(ApiMappingError, match="Cannot determine periodicity"):
            adapter._resolve_variable_periodicities(mock_tbs)

    def test_unexpected_periodicity_raises_error(self) -> None:
        """AC-1: Variable with unexpected periodicity value raises ApiMappingError."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("broken_var",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={},
        )
        var_mock = MagicMock()
        var_mock.entity = SimpleNamespace(key="individu", plural="individus", is_person=True)
        var_mock.definition_period = "invalid_period"
        mock_tbs.variables["broken_var"] = var_mock

        with pytest.raises(ApiMappingError, match="Unexpected periodicity"):
            adapter._resolve_variable_periodicities(mock_tbs)

    def test_day_periodicity_detected(self) -> None:
        """AC-1: Day periodicity is detected correctly."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("daily_var",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={"daily_var": "individu"},
            variable_periodicities={"daily_var": "day"},
        )

        result = adapter._resolve_variable_periodicities(mock_tbs)

        assert result == {"daily_var": "day"}


class TestCalculateVariable:
    """Story 9.3 AC-1, AC-2, AC-6: Calculation dispatch based on periodicity."""

    def test_yearly_uses_calculate(self) -> None:
        """AC-1: Yearly variables use simulation.calculate()."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("irpp",),
            skip_version_check=True,
        )
        sim = _make_mock_simulation_with_methods(
            {"irpp": np.array([-1500.0])}
        )

        result = adapter._calculate_variable(sim, "irpp", "2024", "year")

        sim.calculate.assert_called_once_with("irpp", "2024")
        sim.calculate_add.assert_not_called()
        assert result[0] == -1500.0

    def test_monthly_uses_calculate_add(self) -> None:
        """AC-2: Monthly variables use simulation.calculate_add()."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net",),
            skip_version_check=True,
        )
        sim = _make_mock_simulation_with_methods(
            {"salaire_net": np.array([24000.0])}
        )

        result = adapter._calculate_variable(sim, "salaire_net", "2024", "month")

        sim.calculate_add.assert_called_once_with("salaire_net", "2024")
        sim.calculate.assert_not_called()
        assert result[0] == 24000.0

    def test_eternity_uses_calculate(self) -> None:
        """AC-6: Eternity variables use simulation.calculate(), NOT calculate_add()."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("date_naissance",),
            skip_version_check=True,
        )
        sim = _make_mock_simulation_with_methods(
            {"date_naissance": np.array([19960101])}
        )

        result = adapter._calculate_variable(sim, "date_naissance", "2024", "eternity")

        sim.calculate.assert_called_once_with("date_naissance", "2024")
        sim.calculate_add.assert_not_called()

    def test_day_uses_calculate_add(self) -> None:
        """AC-1: Day-period variables use simulation.calculate_add()."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("daily_var",),
            skip_version_check=True,
        )
        sim = _make_mock_simulation_with_methods(
            {"daily_var": np.array([365.0])}
        )

        result = adapter._calculate_variable(sim, "daily_var", "2024", "day")

        sim.calculate_add.assert_called_once_with("daily_var", "2024")
        sim.calculate.assert_not_called()

    def test_week_uses_calculate_add(self) -> None:
        """AC-1: Week-period variables use simulation.calculate_add()."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("weekly_var",),
            skip_version_check=True,
        )
        sim = _make_mock_simulation_with_methods(
            {"weekly_var": np.array([52.0])}
        )

        result = adapter._calculate_variable(sim, "weekly_var", "2024", "week")

        sim.calculate_add.assert_called_once_with("weekly_var", "2024")
        sim.calculate.assert_not_called()

    def test_weekday_uses_calculate_add(self) -> None:
        """AC-1: Weekday-period variables use simulation.calculate_add()."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("weekday_var",),
            skip_version_check=True,
        )
        sim = _make_mock_simulation_with_methods(
            {"weekday_var": np.array([260.0])}
        )

        result = adapter._calculate_variable(sim, "weekday_var", "2024", "weekday")

        sim.calculate_add.assert_called_once_with("weekday_var", "2024")
        sim.calculate.assert_not_called()


class TestPeriodValidation:
    """Story 9.3 AC-3: Invalid period format rejection."""

    def test_zero_period_raises_error(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-3: Period of 0 raises ApiMappingError."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        with pytest.raises(ApiMappingError, match="Invalid period"):
            adapter.compute(sample_population, empty_policy, 0)

    def test_negative_period_raises_error(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-3: Negative period raises ApiMappingError."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        with pytest.raises(ApiMappingError, match="Invalid period"):
            adapter.compute(sample_population, empty_policy, -1)

    def test_two_digit_period_raises_error(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-3: Two-digit period (99) raises ApiMappingError."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        with pytest.raises(ApiMappingError, match="Invalid period"):
            adapter.compute(sample_population, empty_policy, 99)

    def test_five_digit_period_raises_error(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-3: Five-digit period (99999) raises ApiMappingError."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        with pytest.raises(ApiMappingError, match="Invalid period"):
            adapter.compute(sample_population, empty_policy, 99999)

    def test_valid_period_2024_passes(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-3: Valid period (2024) passes validation."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 2024)

        assert result.period == 2024

    def test_valid_period_1000_passes(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-3: Edge case — period 1000 (minimum valid) passes."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 1000)

        assert result.period == 1000

    def test_valid_period_9999_passes(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-3: Edge case — period 9999 (maximum valid) passes."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 9999)

        assert result.period == 9999

    def test_period_error_includes_actual_value(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-3: Error message includes the actual invalid value."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        with pytest.raises(ApiMappingError) as exc_info:
            adapter.compute(sample_population, empty_policy, 42)

        assert "42" in exc_info.value.reason
        assert "Invalid period" in exc_info.value.summary

    def test_period_validation_precedes_tbs_loading(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-3: Period validation fires BEFORE any TBS operations.

        AC-3 requires the period check to be "the very first check before any
        TBS operations". This test verifies the ordering constraint by NOT
        pre-loading the TBS — if _validate_period() truly runs first, the TBS
        will still be None after the ApiMappingError is raised.
        """
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        # Deliberately do NOT pre-load TBS — if validation runs first,
        # the TBS will still be None after the error.
        assert adapter._tax_benefit_system is None

        with pytest.raises(ApiMappingError, match="Invalid period"):
            adapter.compute(sample_population, empty_policy, 0)

        # Confirm TBS was never loaded — period check was genuinely first.
        assert adapter._tax_benefit_system is None


class TestPeriodicityMetadata:
    """Story 9.3 AC-5: Periodicity metadata in compute() result."""

    def test_variable_periodicities_in_metadata(
        self, empty_policy: PolicyConfig
    ) -> None:
        """AC-5: Metadata includes variable_periodicities dict."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "irpp"),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={
                "salaire_net": "individu",
                "irpp": "foyer_fiscal",
            },
            variable_periodicities={
                "salaire_net": "month",
                "irpp": "year",
            },
        )
        mock_simulation = _make_mock_simulation_with_methods({
            "salaire_net": np.array([24000.0, 40000.0]),
            "irpp": np.array([-1500.0]),
        })
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0, 50000.0]),
                }),
            },
        )

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(
                population, PolicyConfig(parameters={}, name="test"), 2024
            )

        assert "variable_periodicities" in result.metadata
        assert result.metadata["variable_periodicities"] == {
            "salaire_net": "month",
            "irpp": "year",
        }

    def test_calculation_methods_in_metadata(
        self, empty_policy: PolicyConfig
    ) -> None:
        """AC-5: Metadata includes calculation_methods dict."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "irpp"),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={
                "salaire_net": "individu",
                "irpp": "foyer_fiscal",
            },
            variable_periodicities={
                "salaire_net": "month",
                "irpp": "year",
            },
        )
        mock_simulation = _make_mock_simulation_with_methods({
            "salaire_net": np.array([24000.0, 40000.0]),
            "irpp": np.array([-1500.0]),
        })
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0, 50000.0]),
                }),
            },
        )

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(
                population, PolicyConfig(parameters={}, name="test"), 2024
            )

        assert "calculation_methods" in result.metadata
        assert result.metadata["calculation_methods"] == {
            "salaire_net": "calculate_add",
            "irpp": "calculate",
        }

    def test_eternity_variable_uses_calculate_in_metadata(self) -> None:
        """AC-5, AC-6: Eternity variables show 'calculate' method in metadata."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("date_naissance",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={"date_naissance": "individu"},
            variable_periodicities={"date_naissance": "eternity"},
        )
        mock_simulation = _make_mock_simulation_with_methods({
            "date_naissance": np.array([19960101]),
        })
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "age": pa.array([30]),
                }),
            },
        )

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(
                population, PolicyConfig(parameters={}, name="test"), 2024
            )

        assert result.metadata["variable_periodicities"]["date_naissance"] == "eternity"
        assert result.metadata["calculation_methods"]["date_naissance"] == "calculate"


class TestComputeMultiEntity:
    """Story 9.2 AC-1, AC-2, AC-3, AC-4: End-to-end multi-entity compute()."""

    def test_compute_single_entity_backward_compatible(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-4: Single-entity output produces empty entity_tables (backward compat)."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 2025)

        # Single entity: entity_tables should be empty for backward compatibility
        assert result.entity_tables == {}
        # Metadata must be consistent with entity_tables — both empty for single-entity
        # (regression guard for the bug where output_entities was non-empty while
        # entity_tables was {}, causing consumers to see contradictory state).
        assert result.metadata["output_entities"] == []
        assert result.metadata["entity_row_counts"] == {}
        # output_fields still works
        assert result.output_fields.num_rows == 3
        assert result.output_fields.column_names == ["income_tax"]

    def test_compute_multi_entity_populates_entity_tables(self) -> None:
        """AC-1, AC-3: Multi-entity output populates entity_tables."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "irpp", "revenu_disponible"),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={
                "salaire_net": "individu",
                "irpp": "foyer_fiscal",
                "revenu_disponible": "menage",
            },
        )
        mock_simulation = _make_mock_simulation({
            "salaire_net": np.array([20000.0, 35000.0]),
            "irpp": np.array([-1500.0]),
            "revenu_disponible": np.array([40000.0]),
        })
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0, 50000.0]),
                }),
            },
        )

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(
                population, PolicyConfig(parameters={}, name="test"), 2024
            )

        # Multi-entity: entity_tables populated
        assert len(result.entity_tables) == 3
        assert "individus" in result.entity_tables
        assert "foyers_fiscaux" in result.entity_tables
        assert "menages" in result.entity_tables

        # Correct array lengths per entity
        assert result.entity_tables["individus"].num_rows == 2
        assert result.entity_tables["foyers_fiscaux"].num_rows == 1
        assert result.entity_tables["menages"].num_rows == 1

        # output_fields is the person entity table
        assert result.output_fields.num_rows == 2
        assert "salaire_net" in result.output_fields.column_names

    def test_compute_multi_entity_metadata(self) -> None:
        """AC-1: Metadata includes output_entities and entity_row_counts."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "irpp"),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={
                "salaire_net": "individu",
                "irpp": "foyer_fiscal",
            },
        )
        mock_simulation = _make_mock_simulation({
            "salaire_net": np.array([20000.0, 35000.0]),
            "irpp": np.array([-1500.0]),
        })
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0, 50000.0]),
                }),
            },
        )

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(
                population, PolicyConfig(parameters={}, name="test"), 2024
            )

        assert "output_entities" in result.metadata
        assert sorted(result.metadata["output_entities"]) == [
            "foyers_fiscaux", "individus"
        ]
        assert "entity_row_counts" in result.metadata
        assert result.metadata["entity_row_counts"]["individus"] == 2
        assert result.metadata["entity_row_counts"]["foyers_fiscaux"] == 1

    def test_compute_entity_detection_error(self) -> None:
        """AC-5: Variable with no entity raises ApiMappingError during compute."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("broken_var",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs_with_entities(variable_entities={})
        # Add variable with no entity
        var_mock = MagicMock()
        var_mock.entity = None
        mock_tbs.variables["broken_var"] = var_mock
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({"x": pa.array([1.0])}),
            },
        )

        # The error is raised in _resolve_variable_entities() — before _build_simulation().
        # No SimulationBuilder mock needed; the error fires before simulation construction.
        with pytest.raises(ApiMappingError, match="Cannot determine entity"):
            adapter.compute(
                population, PolicyConfig(parameters={}, name="test"), 2024
            )


# ===========================================================================
# Story 9.4: 4-Entity PopulationData format — membership columns
# ===========================================================================


def _make_french_mock_tbs(
    variable_entities: dict[str, str] | None = None,
    variable_periodicities: dict[str, str] | None = None,
) -> MagicMock:
    """Create a full French 4-entity mock TBS with roles for Story 9.4 tests."""
    return _make_mock_tbs_with_entities(
        entity_keys=("individu", "famille", "foyer_fiscal", "menage"),
        entity_roles=_FRENCH_ENTITY_ROLES,
        variable_entities=variable_entities or {},
        variable_periodicities=variable_periodicities or {},
        person_entity="individu",
    )


class TestDetectMembershipColumns:
    """Story 9.4 Task 1: _detect_membership_columns() detection logic.

    AC-1: Detect membership columns on person entity table.
    AC-3: Missing relationship validation (all-or-nothing, paired columns).
    AC-6: Backward compatibility (no membership columns → empty dict).
    """

    def test_detect_all_three_group_entities(self) -> None:
        """AC-1: All 3 group entity membership columns detected correctly."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        person_table = pa.table({
            "salaire_de_base": pa.array([30000.0, 0.0]),
            "famille_id": pa.array([0, 0]),
            "famille_role": pa.array(["parents", "parents"]),
            "foyer_fiscal_id": pa.array([0, 0]),
            "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
            "menage_id": pa.array([0, 0]),
            "menage_role": pa.array(["personne_de_reference", "conjoint"]),
        })

        result = adapter._detect_membership_columns(person_table, mock_tbs)

        assert len(result) == 3
        assert result["famille"] == ("famille_id", "famille_role")
        assert result["foyer_fiscal"] == ("foyer_fiscal_id", "foyer_fiscal_role")
        assert result["menage"] == ("menage_id", "menage_role")

    def test_detect_none_backward_compat(self) -> None:
        """AC-6: No membership columns → empty dict (backward compatible)."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        person_table = pa.table({
            "salaire_de_base": pa.array([30000.0]),
            "age": pa.array([30]),
        })

        result = adapter._detect_membership_columns(person_table, mock_tbs)
        assert result == {}

    def test_detect_partial_raises_error(self) -> None:
        """AC-3: Only famille_id present (missing foyer_fiscal, menage) → error."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        person_table = pa.table({
            "salaire_de_base": pa.array([30000.0]),
            "famille_id": pa.array([0]),
            "famille_role": pa.array(["parents"]),
        })

        with pytest.raises(ApiMappingError, match="Incomplete entity membership columns"):
            adapter._detect_membership_columns(person_table, mock_tbs)

    def test_detect_unpaired_id_without_role_raises_error(self) -> None:
        """AC-3: famille_id exists but famille_role missing → unpaired error."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        person_table = pa.table({
            "salaire_de_base": pa.array([30000.0]),
            "famille_id": pa.array([0]),
            # famille_role is missing — only _id without _role
            "foyer_fiscal_id": pa.array([0]),
            "foyer_fiscal_role": pa.array(["declarants"]),
            "menage_id": pa.array([0]),
            "menage_role": pa.array(["personne_de_reference"]),
        })

        with pytest.raises(ApiMappingError, match="Unpaired membership column"):
            adapter._detect_membership_columns(person_table, mock_tbs)

    def test_detect_unpaired_role_without_id_raises_error(self) -> None:
        """AC-3: famille_role exists but famille_id missing → unpaired error."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        person_table = pa.table({
            "salaire_de_base": pa.array([30000.0]),
            # famille_id is missing — only _role without _id
            "famille_role": pa.array(["parents"]),
            "foyer_fiscal_id": pa.array([0]),
            "foyer_fiscal_role": pa.array(["declarants"]),
            "menage_id": pa.array([0]),
            "menage_role": pa.array(["personne_de_reference"]),
        })

        with pytest.raises(ApiMappingError, match="Unpaired membership column"):
            adapter._detect_membership_columns(person_table, mock_tbs)


class TestResolveValidRoleKeys:
    """Story 9.4 Task 2: _resolve_valid_role_keys() role key resolution.

    AC-4: Valid role keys queried from TBS.
    """

    def test_french_entity_role_keys(self) -> None:
        """AC-4: Correct role keys for all French group entities.

        Uses role.plural or role.key — matching build_from_entities() behavior.
        """
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        result = adapter._resolve_valid_role_keys(mock_tbs)

        assert result["famille"] == frozenset({"parents", "enfants"})
        assert result["foyer_fiscal"] == frozenset({"declarants", "personnes_a_charge"})
        # menage: personne_de_reference and conjoint have plural=None → uses key
        assert result["menage"] == frozenset({
            "personne_de_reference", "conjoint", "enfants", "autres",
        })

    def test_person_entity_excluded(self) -> None:
        """AC-4: Person entity (individu) is not in role keys dict."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        result = adapter._resolve_valid_role_keys(mock_tbs)
        assert "individu" not in result


class TestValidateEntityRelationships:
    """Story 9.4 Task 3: _validate_entity_relationships() validation.

    AC-3: Missing relationship validation.
    AC-4: Invalid role validation.
    AC-5: Null membership value rejection.
    """

    def test_null_in_id_column_raises_error(self) -> None:
        """AC-5: Null value in _id column → ApiMappingError."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        person_table = pa.table({
            "salaire_de_base": pa.array([30000.0, 0.0]),
            "famille_id": pa.array([0, None]),  # null in _id
            "famille_role": pa.array(["parents", "parents"]),
            "foyer_fiscal_id": pa.array([0, 0]),
            "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
            "menage_id": pa.array([0, 0]),
            "menage_role": pa.array(["personne_de_reference", "conjoint"]),
        })

        membership_cols = {
            "famille": ("famille_id", "famille_role"),
            "foyer_fiscal": ("foyer_fiscal_id", "foyer_fiscal_role"),
            "menage": ("menage_id", "menage_role"),
        }
        valid_roles = {
            "famille": frozenset({"parents", "enfants"}),
            "foyer_fiscal": frozenset({"declarants", "personnes_a_charge"}),
            "menage": frozenset({"personne_de_reference", "conjoint", "enfants", "autres"}),
        }

        with pytest.raises(ApiMappingError, match="Null value in membership column"):
            adapter._validate_entity_relationships(
                person_table, membership_cols, valid_roles
            )

    def test_null_in_role_column_raises_error(self) -> None:
        """AC-5: Null value in _role column → ApiMappingError."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        person_table = pa.table({
            "salaire_de_base": pa.array([30000.0, 0.0]),
            "famille_id": pa.array([0, 0]),
            "famille_role": pa.array(["parents", None]),  # null in _role
            "foyer_fiscal_id": pa.array([0, 0]),
            "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
            "menage_id": pa.array([0, 0]),
            "menage_role": pa.array(["personne_de_reference", "conjoint"]),
        })

        membership_cols = {
            "famille": ("famille_id", "famille_role"),
            "foyer_fiscal": ("foyer_fiscal_id", "foyer_fiscal_role"),
            "menage": ("menage_id", "menage_role"),
        }
        valid_roles = {
            "famille": frozenset({"parents", "enfants"}),
            "foyer_fiscal": frozenset({"declarants", "personnes_a_charge"}),
            "menage": frozenset({"personne_de_reference", "conjoint", "enfants", "autres"}),
        }

        with pytest.raises(ApiMappingError, match="Null value in membership column"):
            adapter._validate_entity_relationships(
                person_table, membership_cols, valid_roles
            )

    def test_invalid_role_value_raises_error(self) -> None:
        """AC-4: Invalid role value → ApiMappingError with valid roles listed."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        person_table = pa.table({
            "salaire_de_base": pa.array([30000.0]),
            "famille_id": pa.array([0]),
            "famille_role": pa.array(["parents"]),
            "foyer_fiscal_id": pa.array([0]),
            "foyer_fiscal_role": pa.array(["declarants"]),
            "menage_id": pa.array([0]),
            "menage_role": pa.array(["invalid_role"]),  # invalid role
        })

        membership_cols = {
            "famille": ("famille_id", "famille_role"),
            "foyer_fiscal": ("foyer_fiscal_id", "foyer_fiscal_role"),
            "menage": ("menage_id", "menage_role"),
        }
        valid_roles = {
            "famille": frozenset({"parents", "enfants"}),
            "foyer_fiscal": frozenset({"declarants", "personnes_a_charge"}),
            "menage": frozenset({"personne_de_reference", "conjoint", "enfants", "autres"}),
        }

        with pytest.raises(ApiMappingError, match="Invalid role value"):
            adapter._validate_entity_relationships(
                person_table, membership_cols, valid_roles
            )

    def test_all_valid_passes_silently(self) -> None:
        """AC-3, AC-4, AC-5: All valid data passes without error."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        person_table = pa.table({
            "salaire_de_base": pa.array([30000.0, 0.0]),
            "famille_id": pa.array([0, 0]),
            "famille_role": pa.array(["parents", "parents"]),
            "foyer_fiscal_id": pa.array([0, 0]),
            "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
            "menage_id": pa.array([0, 0]),
            "menage_role": pa.array(["personne_de_reference", "conjoint"]),
        })

        membership_cols = {
            "famille": ("famille_id", "famille_role"),
            "foyer_fiscal": ("foyer_fiscal_id", "foyer_fiscal_role"),
            "menage": ("menage_id", "menage_role"),
        }
        valid_roles = {
            "famille": frozenset({"parents", "enfants"}),
            "foyer_fiscal": frozenset({"declarants", "personnes_a_charge"}),
            "menage": frozenset({"personne_de_reference", "conjoint", "enfants", "autres"}),
        }

        # Should not raise
        adapter._validate_entity_relationships(
            person_table, membership_cols, valid_roles
        )


class TestPopulationToEntityDict4Entity:
    """Story 9.4 Task 4: Refactored _population_to_entity_dict() for 4-entity format.

    AC-1: 4-entity format produces valid entity dict.
    AC-2: Group membership assignment is correct.
    AC-6: Backward compatibility (no membership columns → old behavior).
    AC-7: Group entity input variables merged correctly.
    """

    def test_married_couple_entity_dict(self) -> None:
        """AC-1, AC-2: Married couple produces correct entity dict.

        2 persons in 1 famille, 1 foyer_fiscal, 1 menage with correct roles.
        """
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs(
            variable_entities={"income_tax": "individu"},
        )
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0, 0.0]),
                    "age": pa.array([30, 28]),
                    "famille_id": pa.array([0, 0]),
                    "famille_role": pa.array(["parents", "parents"]),
                    "foyer_fiscal_id": pa.array([0, 0]),
                    "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
                    "menage_id": pa.array([0, 0]),
                    "menage_role": pa.array(["personne_de_reference", "conjoint"]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="test")

        entity_dict = adapter._population_to_entity_dict(
            population, policy, "2024", mock_tbs
        )

        # Person instances with period-wrapped variable values
        assert "individus" in entity_dict
        assert "individu_0" in entity_dict["individus"]
        assert "individu_1" in entity_dict["individus"]
        assert entity_dict["individus"]["individu_0"]["salaire_de_base"] == {"2024": 30000.0}
        assert entity_dict["individus"]["individu_1"]["age"] == {"2024": 28}

        # Membership columns should NOT appear in person instance data
        assert "famille_id" not in entity_dict["individus"]["individu_0"]
        assert "famille_role" not in entity_dict["individus"]["individu_0"]
        assert "foyer_fiscal_id" not in entity_dict["individus"]["individu_0"]
        assert "menage_id" not in entity_dict["individus"]["individu_0"]

        # Group entity instances with role assignments
        assert "familles" in entity_dict
        assert "famille_0" in entity_dict["familles"]
        assert entity_dict["familles"]["famille_0"]["parents"] == [
            "individu_0", "individu_1"
        ]

        assert "foyers_fiscaux" in entity_dict
        assert "foyer_fiscal_0" in entity_dict["foyers_fiscaux"]
        assert entity_dict["foyers_fiscaux"]["foyer_fiscal_0"]["declarants"] == [
            "individu_0", "individu_1"
        ]

        assert "menages" in entity_dict
        assert "menage_0" in entity_dict["menages"]
        assert entity_dict["menages"]["menage_0"]["personne_de_reference"] == ["individu_0"]
        assert entity_dict["menages"]["menage_0"]["conjoint"] == ["individu_1"]

    def test_family_with_child(self) -> None:
        """AC-1, AC-2: Family with 2 parents + 1 child, different roles."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs(
            variable_entities={"income_tax": "individu"},
        )
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([40000.0, 20000.0, 0.0]),
                    "age": pa.array([45, 42, 12]),
                    "famille_id": pa.array([0, 0, 0]),
                    "famille_role": pa.array(["parents", "parents", "enfants"]),
                    "foyer_fiscal_id": pa.array([0, 0, 0]),
                    "foyer_fiscal_role": pa.array([
                        "declarants", "declarants", "personnes_a_charge",
                    ]),
                    "menage_id": pa.array([0, 0, 0]),
                    "menage_role": pa.array([
                        "personne_de_reference", "conjoint", "enfants",
                    ]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="test")

        entity_dict = adapter._population_to_entity_dict(
            population, policy, "2024", mock_tbs
        )

        # famille roles
        famille = entity_dict["familles"]["famille_0"]
        assert famille["parents"] == ["individu_0", "individu_1"]
        assert famille["enfants"] == ["individu_2"]

        # foyer_fiscal roles
        foyer = entity_dict["foyers_fiscaux"]["foyer_fiscal_0"]
        assert foyer["declarants"] == ["individu_0", "individu_1"]
        assert foyer["personnes_a_charge"] == ["individu_2"]

        # menage roles
        menage = entity_dict["menages"]["menage_0"]
        assert menage["personne_de_reference"] == ["individu_0"]
        assert menage["conjoint"] == ["individu_1"]
        assert menage["enfants"] == ["individu_2"]

    def test_backward_compat_no_membership_columns(self) -> None:
        """AC-6: No membership columns → identical to pre-change behavior."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs(
            variable_entities={"income_tax": "individu"},
        )
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0]),
                    "age": pa.array([30]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="test")

        entity_dict = adapter._population_to_entity_dict(
            population, policy, "2024", mock_tbs
        )

        # Old behavior: all columns period-wrapped, no group entities
        assert "individus" in entity_dict
        assert entity_dict["individus"]["individu_0"]["salaire_de_base"] == {"2024": 30000.0}
        assert entity_dict["individus"]["individu_0"]["age"] == {"2024": 30}

    def test_two_independent_households(self) -> None:
        """AC-1, AC-2: Two independent single-person households."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs(
            variable_entities={"income_tax": "individu"},
        )
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0, 50000.0]),
                    "famille_id": pa.array([0, 1]),
                    "famille_role": pa.array(["parents", "parents"]),
                    "foyer_fiscal_id": pa.array([0, 1]),
                    "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
                    "menage_id": pa.array([0, 1]),
                    "menage_role": pa.array([
                        "personne_de_reference", "personne_de_reference",
                    ]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="test")

        entity_dict = adapter._population_to_entity_dict(
            population, policy, "2024", mock_tbs
        )

        # 2 familles, 2 foyers, 2 menages
        assert len(entity_dict["familles"]) == 2
        assert len(entity_dict["foyers_fiscaux"]) == 2
        assert len(entity_dict["menages"]) == 2

        assert entity_dict["familles"]["famille_0"]["parents"] == ["individu_0"]
        assert entity_dict["familles"]["famille_1"]["parents"] == ["individu_1"]

    def test_group_entity_input_variables(self) -> None:
        """AC-7: Group entity table with variables merged into entity dict."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs(
            variable_entities={"income_tax": "individu"},
        )
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0, 0.0]),
                    "famille_id": pa.array([0, 0]),
                    "famille_role": pa.array(["parents", "parents"]),
                    "foyer_fiscal_id": pa.array([0, 0]),
                    "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
                    "menage_id": pa.array([0, 0]),
                    "menage_role": pa.array(["personne_de_reference", "conjoint"]),
                }),
                "menage": pa.table({
                    "loyer": pa.array([800.0]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="test")

        entity_dict = adapter._population_to_entity_dict(
            population, policy, "2024", mock_tbs
        )

        # menage entity should have role assignments AND period-wrapped loyer
        menage = entity_dict["menages"]["menage_0"]
        assert menage["personne_de_reference"] == ["individu_0"]
        assert menage["conjoint"] == ["individu_1"]
        assert menage["loyer"] == {"2024": 800.0}

    def test_non_contiguous_group_ids(self) -> None:
        """Edge case: non-contiguous group IDs [0, 2] work correctly."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs(
            variable_entities={"income_tax": "individu"},
        )
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0, 50000.0]),
                    "famille_id": pa.array([0, 2]),
                    "famille_role": pa.array(["parents", "parents"]),
                    "foyer_fiscal_id": pa.array([0, 2]),
                    "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
                    "menage_id": pa.array([0, 2]),
                    "menage_role": pa.array([
                        "personne_de_reference", "personne_de_reference",
                    ]),
                }),
                "menage": pa.table({
                    "loyer": pa.array([800.0, 1200.0]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="test")

        entity_dict = adapter._population_to_entity_dict(
            population, policy, "2024", mock_tbs
        )

        # Non-contiguous IDs: famille_0 and famille_2 (no famille_1)
        assert "famille_0" in entity_dict["familles"]
        assert "famille_2" in entity_dict["familles"]
        assert "famille_1" not in entity_dict["familles"]

        # Group table: row 0 → smallest ID (0), row 1 → second-smallest ID (2)
        assert entity_dict["menages"]["menage_0"]["loyer"] == {"2024": 800.0}
        assert entity_dict["menages"]["menage_2"]["loyer"] == {"2024": 1200.0}

    def test_group_table_row_count_mismatch_raises_error(self) -> None:
        """Edge case: group entity table has more rows than distinct group IDs."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs(
            variable_entities={"income_tax": "individu"},
        )
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0]),
                    "famille_id": pa.array([0]),
                    "famille_role": pa.array(["parents"]),
                    "foyer_fiscal_id": pa.array([0]),
                    "foyer_fiscal_role": pa.array(["declarants"]),
                    "menage_id": pa.array([0]),
                    "menage_role": pa.array(["personne_de_reference"]),
                }),
                "menage": pa.table({
                    "loyer": pa.array([800.0, 1200.0]),  # 2 rows but only 1 menage
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="test")

        with pytest.raises(ApiMappingError, match="Group entity table row count mismatch"):
            adapter._population_to_entity_dict(
                population, policy, "2024", mock_tbs
            )

    def test_policy_parameters_injected_in_4entity_mode(self) -> None:
        """AC-1: Policy parameters are injected into person instances in 4-entity mode."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs(
            variable_entities={"income_tax": "individu"},
        )
        # Add the policy parameter variable to mock TBS
        policy_var = MagicMock()
        policy_var.entity = mock_tbs.entities[0]  # individu
        policy_var.definition_period = "year"
        mock_tbs.variables["custom_param"] = policy_var
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0]),
                    "famille_id": pa.array([0]),
                    "famille_role": pa.array(["parents"]),
                    "foyer_fiscal_id": pa.array([0]),
                    "foyer_fiscal_role": pa.array(["declarants"]),
                    "menage_id": pa.array([0]),
                    "menage_role": pa.array(["personne_de_reference"]),
                }),
            },
        )
        policy = PolicyConfig(parameters={"custom_param": 42.0}, name="test")

        entity_dict = adapter._population_to_entity_dict(
            population, policy, "2024", mock_tbs
        )

        assert entity_dict["individus"]["individu_0"]["custom_param"] == {"2024": 42.0}

    def test_string_group_ids(self) -> None:
        """Edge case: String (utf8) group IDs work correctly."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs(
            variable_entities={"income_tax": "individu"},
        )
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0, 0.0]),
                    "famille_id": pa.array(["fam_a", "fam_a"]),
                    "famille_role": pa.array(["parents", "parents"]),
                    "foyer_fiscal_id": pa.array(["ff_a", "ff_a"]),
                    "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
                    "menage_id": pa.array(["men_a", "men_a"]),
                    "menage_role": pa.array(["personne_de_reference", "conjoint"]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="test")

        entity_dict = adapter._population_to_entity_dict(
            population, policy, "2024", mock_tbs
        )

        assert "famille_fam_a" in entity_dict["familles"]
        assert "foyer_fiscal_ff_a" in entity_dict["foyers_fiscaux"]
        assert "menage_men_a" in entity_dict["menages"]
        assert entity_dict["menages"]["menage_men_a"]["personne_de_reference"] == [
            "individu_0",
        ]

    def test_plural_person_table_key(self) -> None:
        """Edge case: Person table key is plural ('individus' instead of 'individu').

        Person instance IDs should use the plural key prefix.
        """
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs(
            variable_entities={"income_tax": "individu"},
        )
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individus": pa.table({  # plural key
                    "salaire_de_base": pa.array([30000.0, 0.0]),
                    "famille_id": pa.array([0, 0]),
                    "famille_role": pa.array(["parents", "parents"]),
                    "foyer_fiscal_id": pa.array([0, 0]),
                    "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
                    "menage_id": pa.array([0, 0]),
                    "menage_role": pa.array(["personne_de_reference", "conjoint"]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="test")

        entity_dict = adapter._population_to_entity_dict(
            population, policy, "2024", mock_tbs
        )

        # Person instance IDs use the original table key prefix ("individus")
        assert "individus_0" in entity_dict["individus"]
        assert "individus_1" in entity_dict["individus"]

        # Group role assignments also use "individus_" prefix
        assert entity_dict["familles"]["famille_0"]["parents"] == [
            "individus_0", "individus_1"
        ]


]]></file>
<file id="895c54dc" path="tests/computation/test_openfisca_integration.py" label="SOURCE CODE"><![CDATA[

"""Integration tests for OpenFiscaApiAdapter against real OpenFisca-France.

Story 8.1: End-to-End OpenFisca Integration Spike.
Story 9.2: Multi-entity output array handling integration tests.
Story 9.4: 4-entity PopulationData format integration tests.

These tests call real OpenFisca-France computations (no mocking).
Run with: uv run pytest tests/computation/test_openfisca_integration.py -m integration
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pyarrow as pa
import pytest

openfisca_france = pytest.importorskip("openfisca_france")

from reformlab.computation.ingestion import DataSchema
from reformlab.computation.mapping import apply_output_mapping, load_mapping
from reformlab.computation.openfisca_api_adapter import OpenFiscaApiAdapter
from reformlab.computation.quality import validate_output
from reformlab.computation.types import ComputationResult, PolicyConfig, PopulationData

# ---------------------------------------------------------------------------
# Shared fixtures — TBS is expensive, cache at module scope
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def tbs() -> Any:
    """Load the real French TaxBenefitSystem once per module."""
    return openfisca_france.CountryTaxBenefitSystem()


@pytest.fixture(scope="module")
def adapter() -> OpenFiscaApiAdapter:
    """Create a real OpenFiscaApiAdapter with a common output variable."""
    return OpenFiscaApiAdapter(
        country_package="openfisca_france",
        output_variables=("impot_revenu_restant_a_payer",),
    )


@pytest.fixture()
def single_person_population() -> PopulationData:
    """Minimal single-person population using singular entity keys.

    Only provides the individu table with input variables. The adapter's
    _population_to_entity_dict handles normalisation to plural keys.
    Note: group entities (famille, foyer_fiscal, menage) are omitted
    because the adapter auto-creates them for single-person populations.
    """
    return PopulationData(
        tables={
            "individu": pa.table({
                "salaire_de_base": pa.array([30000.0]),
                "age": pa.array([30]),
            }),
        },
        metadata={"source": "integration-test"},
    )


@pytest.fixture()
def empty_policy() -> PolicyConfig:
    return PolicyConfig(parameters={}, name="integration-test-policy")


def _build_entities_dict(salary: float = 30000.0, age: int = 30) -> dict[str, Any]:
    """Helper to build a valid OpenFisca-France entity dict (plural keys)."""
    return {
        "individus": {
            "person_0": {
                "salaire_de_base": {"2024": salary},
                "age": {"2024-01": age},
            },
        },
        "familles": {"famille_0": {"parents": ["person_0"]}},
        "foyers_fiscaux": {"foyer_0": {"declarants": ["person_0"]}},
        "menages": {"menage_0": {"personne_de_reference": ["person_0"]}},
    }


def _build_simulation(
    tbs: Any,
    individus: dict[str, dict[str, Any]],
    *,
    couples: bool = False,
) -> Any:
    """Helper to build a simulation with standard 4-entity structure."""
    from openfisca_core.simulation_builder import SimulationBuilder

    person_ids = list(individus.keys())

    if couples and len(person_ids) == 2:
        familles = {"famille_0": {"parents": person_ids}}
        foyers = {"foyer_0": {"declarants": person_ids}}
        menages = {"menage_0": {
            "personne_de_reference": [person_ids[0]],
            "conjoint": [person_ids[1]],
        }}
    else:
        familles = {f"famille_{i}": {"parents": [pid]} for i, pid in enumerate(person_ids)}
        foyers = {f"foyer_{i}": {"declarants": [pid]} for i, pid in enumerate(person_ids)}
        menages = {f"menage_{i}": {"personne_de_reference": [pid]} for i, pid in enumerate(person_ids)}

    entities_dict = {
        "individus": individus,
        "familles": familles,
        "foyers_fiscaux": foyers,
        "menages": menages,
    }

    builder = SimulationBuilder()
    return builder.build_from_entities(tbs, entities_dict)


# ---------------------------------------------------------------------------
# AC-2: TaxBenefitSystem loads (Task 3)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestTaxBenefitSystemLoading:
    """AC-2: TaxBenefitSystem loads without error via adapter."""

    def test_adapter_instantiates_without_error(self) -> None:
        """AC-2: OpenFiscaApiAdapter with openfisca_france instantiates successfully."""
        a = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("impot_revenu_restant_a_payer",),
        )
        assert a is not None

    def test_version_returns_valid_string(self) -> None:
        """AC-2: adapter.version() returns a valid openfisca-core version string."""
        a = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("impot_revenu_restant_a_payer",),
        )
        version = a.version()
        assert isinstance(version, str)
        parts = version.split(".")
        assert len(parts) == 3
        assert parts[0] == "44"

    def test_tbs_loads_lazily_and_is_cached(self) -> None:
        """AC-2: TBS is loaded lazily on first access and cached."""
        a = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("impot_revenu_restant_a_payer",),
        )
        assert a._tax_benefit_system is None

        local_tbs = a._get_tax_benefit_system()
        assert local_tbs is not None

        local_tbs2 = a._get_tax_benefit_system()
        assert local_tbs is local_tbs2


# ---------------------------------------------------------------------------
# AC-3, AC-7: Real computation via adapter.compute() (Tasks 4, 8)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestAdapterComputeEndToEnd:
    """AC-3, AC-7: adapter.compute() returns valid results with real OpenFisca-France.

    These tests call the adapter's public compute() method end-to-end,
    validating that the full pipeline (TBS loading, entity dict construction,
    simulation building, result extraction) works with OpenFisca-France.
    """

    def test_compute_returns_computation_result(
        self,
        adapter: OpenFiscaApiAdapter,
        single_person_population: PopulationData,
        empty_policy: PolicyConfig
    ) -> None:
        """AC-3: adapter.compute() returns a ComputationResult with real values."""
        result = adapter.compute(single_person_population, empty_policy, 2024)

        assert isinstance(result, ComputationResult)
        assert isinstance(result.output_fields, pa.Table)
        assert "impot_revenu_restant_a_payer" in result.output_fields.column_names
        assert result.output_fields.num_rows == 1

    def test_compute_result_has_correct_metadata(
        self,
        adapter: OpenFiscaApiAdapter,
        single_person_population: PopulationData,
        empty_policy: PolicyConfig
    ) -> None:
        """AC-3: adapter.compute() sets source='api' in metadata."""
        result = adapter.compute(single_person_population, empty_policy, 2024)

        assert result.metadata["source"] == "api"
        assert result.metadata["country_package"] == "openfisca_france"
        assert result.period == 2024

    def test_irpp_value_is_negative_tax(
        self,
        adapter: OpenFiscaApiAdapter,
        single_person_population: PopulationData,
        empty_policy: PolicyConfig
    ) -> None:
        """AC-3, AC-7: irpp for 30k salary is negative (tax owed) and in reasonable range."""
        result = adapter.compute(single_person_population, empty_policy, 2024)

        irpp = result.output_fields.column("impot_revenu_restant_a_payer")[0].as_py()
        assert irpp < 0, f"Expected negative irpp (tax), got {irpp}"
        assert -5000 < irpp < 0, f"irpp {irpp} outside expected range [-5000, 0]"


# ---------------------------------------------------------------------------
# AC-4: Multi-entity population (Task 5)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestMultiEntityPopulation:
    """AC-4: Multi-entity population with all 4 OpenFisca-France entities."""

    def test_multi_person_computation(self, tbs: Any) -> None:
        """AC-4: Computation with 2 persons returns results for all."""
        from openfisca_core.simulation_builder import SimulationBuilder

        entities_dict = {
            "individus": {
                "person_0": {
                    "salaire_de_base": {"2024": 30000.0},
                    "age": {"2024-01": 30},
                },
                "person_1": {
                    "salaire_de_base": {"2024": 50000.0},
                    "age": {"2024-01": 45},
                },
            },
            "familles": {
                "famille_0": {"parents": ["person_0"]},
                "famille_1": {"parents": ["person_1"]},
            },
            "foyers_fiscaux": {
                "foyer_0": {"declarants": ["person_0"]},
                "foyer_1": {"declarants": ["person_1"]},
            },
            "menages": {
                "menage_0": {"personne_de_reference": ["person_0"]},
                "menage_1": {"personne_de_reference": ["person_1"]},
            },
        }

        builder = SimulationBuilder()
        simulation = builder.build_from_entities(tbs, entities_dict)

        irpp = simulation.calculate("impot_revenu_restant_a_payer", "2024")
        assert len(irpp) == 2, f"Expected 2 results, got {len(irpp)}"
        assert irpp[0] < 0
        assert irpp[1] < 0
        # Higher salary -> more tax (more negative)
        assert irpp[1] < irpp[0], "Higher salary should yield higher tax"

    def test_multi_entity_variable_array_lengths(self, tbs: Any) -> None:
        """AC-4: Variables from different entities return different-length arrays.

        This documents the known gap (Gap 2 in findings): multi-entity output
        arrays have different lengths, so they can't be combined into one table.
        """
        from openfisca_core.simulation_builder import SimulationBuilder

        # 2 persons but 1 foyer_fiscal and 1 menage (married couple)
        entities_dict = {
            "individus": {
                "person_0": {
                    "salaire_de_base": {"2024": 30000.0},
                    "age": {"2024-01": 30},
                },
                "person_1": {
                    "salaire_de_base": {"2024": 0.0},
                    "age": {"2024-01": 28},
                },
            },
            "familles": {
                "famille_0": {"parents": ["person_0", "person_1"]},
            },
            "foyers_fiscaux": {
                "foyer_0": {"declarants": ["person_0", "person_1"]},
            },
            "menages": {
                "menage_0": {
                    "personne_de_reference": ["person_0"],
                    "conjoint": ["person_1"],
                },
            },
        }

        builder = SimulationBuilder()
        simulation = builder.build_from_entities(tbs, entities_dict)

        # individu-level variable: 2 values
        salaire_net = simulation.calculate_add("salaire_net", "2024")
        assert len(salaire_net) == 2

        # foyer_fiscal-level variable: 1 value
        irpp = simulation.calculate("impot_revenu_restant_a_payer", "2024")
        assert len(irpp) == 1

        # menage-level variable: 1 value
        revenu_disponible = simulation.calculate("revenu_disponible", "2024")
        assert len(revenu_disponible) == 1

    def test_adapter_entity_key_to_plural_mapping(self, tbs: Any) -> None:
        """AC-4: Document that entity.key != build_from_entities key (plural)."""
        key_to_plural = {}
        for entity in tbs.entities:
            key_to_plural[entity.key] = entity.plural

        assert key_to_plural["individu"] == "individus"
        assert key_to_plural["famille"] == "familles"
        assert key_to_plural["foyer_fiscal"] == "foyers_fiscaux"
        assert key_to_plural["menage"] == "menages"


# ---------------------------------------------------------------------------
# AC-5: Variable mapping round-trip (Task 6)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestVariableMappingRoundTrip:
    """AC-5: Variable mapping correctly renames OpenFisca columns to project names."""

    def test_mapping_renames_columns_correctly(self, tbs: Any, tmp_path: Path) -> None:
        """AC-5: apply_output_mapping renames OpenFisca variable names to project names."""
        from openfisca_core.simulation_builder import SimulationBuilder

        mapping_yaml = tmp_path / "test_mapping.yaml"
        mapping_yaml.write_text(
            "version: 1\n"
            "mappings:\n"
            "  - openfisca_name: impot_revenu_restant_a_payer\n"
            "    project_name: income_tax\n"
            "    direction: output\n"
            "    type: float64\n"
            "  - openfisca_name: salaire_net\n"
            "    project_name: net_salary\n"
            "    direction: output\n"
            "    type: float64\n"
        )

        config = load_mapping(mapping_yaml)

        entities_dict = _build_entities_dict()
        builder = SimulationBuilder()
        simulation = builder.build_from_entities(tbs, entities_dict)

        irpp_val = simulation.calculate("impot_revenu_restant_a_payer", "2024")
        salaire_net_val = simulation.calculate_add("salaire_net", "2024")

        original_table = pa.table({
            "impot_revenu_restant_a_payer": pa.array(irpp_val),
            "salaire_net": pa.array(salaire_net_val),
        })

        mapped_table = apply_output_mapping(original_table, config)

        assert "income_tax" in mapped_table.column_names
        assert "net_salary" in mapped_table.column_names
        assert "impot_revenu_restant_a_payer" not in mapped_table.column_names
        assert "salaire_net" not in mapped_table.column_names

    def test_mapped_values_are_numerically_identical(self, tbs: Any, tmp_path: Path) -> None:
        """AC-5: Mapped values are numerically identical to unmapped values."""
        from openfisca_core.simulation_builder import SimulationBuilder

        mapping_yaml = tmp_path / "test_mapping.yaml"
        mapping_yaml.write_text(
            "version: 1\n"
            "mappings:\n"
            "  - openfisca_name: impot_revenu_restant_a_payer\n"
            "    project_name: income_tax\n"
            "    direction: output\n"
            "    type: float64\n"
        )

        config = load_mapping(mapping_yaml)

        entities_dict = _build_entities_dict()
        builder = SimulationBuilder()
        simulation = builder.build_from_entities(tbs, entities_dict)

        irpp_val = simulation.calculate("impot_revenu_restant_a_payer", "2024")

        original_table = pa.table({
            "impot_revenu_restant_a_payer": pa.array(irpp_val),
        })
        mapped_table = apply_output_mapping(original_table, config)

        original_value = original_table.column("impot_revenu_restant_a_payer")[0].as_py()
        mapped_value = mapped_table.column("income_tax")[0].as_py()
        assert original_value == mapped_value


# ---------------------------------------------------------------------------
# AC-6: Output quality validation (Task 7)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestOutputQualityValidation:
    """AC-6: Output passes quality validation with appropriate schema."""

    def test_validate_output_passes_with_adapter_result(
        self,
        adapter: OpenFiscaApiAdapter,
        single_person_population: PopulationData,
        empty_policy: PolicyConfig
    ) -> None:
        """AC-6: Real adapter.compute() output passes validate_output."""
        result = adapter.compute(single_person_population, empty_policy, 2024)

        schema = DataSchema(
            schema=pa.schema([
                pa.field("impot_revenu_restant_a_payer", pa.float32()),
            ]),
            required_columns=("impot_revenu_restant_a_payer",),
        )

        qr = validate_output(result, schema)
        assert qr.passed is True
        assert len(qr.errors) == 0


# ---------------------------------------------------------------------------
# AC-7: Known-value benchmark (Task 8)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestKnownValueBenchmark:
    """AC-7: Adapter results match expected French income tax for known salary."""

    def test_irpp_determinism_via_adapter(
        self, single_person_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-7: Two independent adapter.compute() calls produce identical results."""
        adapter1 = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("impot_revenu_restant_a_payer",),
        )
        adapter2 = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("impot_revenu_restant_a_payer",),
        )

        result1 = adapter1.compute(single_person_population, empty_policy, 2024)
        result2 = adapter2.compute(single_person_population, empty_policy, 2024)

        val1 = result1.output_fields.column("impot_revenu_restant_a_payer")[0].as_py()
        val2 = result2.output_fields.column("impot_revenu_restant_a_payer")[0].as_py()

        assert abs(float(val1) - float(val2)) < 1.0, (
            f"Non-deterministic results: {val1} vs {val2}"
        )

    def test_higher_salary_yields_higher_tax(self, tbs: Any) -> None:
        """AC-7: Progressive tax -- higher salary results in more tax."""
        from openfisca_core.simulation_builder import SimulationBuilder

        def compute_irpp(salary: float) -> float:
            entities_dict = _build_entities_dict(salary=salary)
            builder = SimulationBuilder()
            sim = builder.build_from_entities(tbs, entities_dict)
            return float(sim.calculate("impot_revenu_restant_a_payer", "2024")[0])

        irpp_30k = compute_irpp(30000.0)
        irpp_60k = compute_irpp(60000.0)
        irpp_100k = compute_irpp(100000.0)

        assert irpp_60k < irpp_30k, f"60k ({irpp_60k}) should pay more tax than 30k ({irpp_30k})"
        assert irpp_100k < irpp_60k, f"100k ({irpp_100k}) should pay more tax than 60k ({irpp_60k})"


# ---------------------------------------------------------------------------
# Adapter plural-key fix validation (Task 5 supplement)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestAdapterPluralKeyFix:
    """Validate that the adapter normalises singular entity keys to plural.

    The original spike identified that _population_to_entity_dict used
    entity.key (singular) but build_from_entities requires entity.plural.
    The fix normalises to plural keys automatically.
    """

    def test_population_to_entity_dict_normalises_to_plural(
        self, adapter: OpenFiscaApiAdapter
    ) -> None:
        """Adapter now normalises singular entity keys to plural."""
        local_tbs = adapter._get_tax_benefit_system()

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="test")

        entity_dict = adapter._population_to_entity_dict(population, policy, "2024", local_tbs)

        assert "individus" in entity_dict, "Adapter should normalise to plural key"
        assert "individu" not in entity_dict, "Singular key should be normalised away"

    def test_build_from_entities_rejects_singular_keys(self, tbs: Any) -> None:
        """build_from_entities raises error with singular entity keys."""
        from openfisca_core.errors import SituationParsingError
        from openfisca_core.simulation_builder import SimulationBuilder

        singular_dict = {
            "individu": {
                "person_0": {"salaire_de_base": {"2024": 30000.0}},
            },
            "famille": {"famille_0": {"parents": ["person_0"]}},
            "foyer_fiscal": {"foyer_0": {"declarants": ["person_0"]}},
            "menage": {"menage_0": {"personne_de_reference": ["person_0"]}},
        }

        builder = SimulationBuilder()
        with pytest.raises(SituationParsingError):
            builder.build_from_entities(tbs, singular_dict)

    def test_compute_works_with_singular_entity_keys(
        self,
        adapter: OpenFiscaApiAdapter,
        single_person_population: PopulationData,
        empty_policy: PolicyConfig
    ) -> None:
        """adapter.compute() works when PopulationData uses singular entity keys."""
        result = adapter.compute(single_person_population, empty_policy, 2024)

        assert isinstance(result, ComputationResult)
        irpp = result.output_fields.column("impot_revenu_restant_a_payer")[0].as_py()
        assert irpp < 0, f"Expected negative irpp, got {irpp}"


# ---------------------------------------------------------------------------
# OpenFisca-France reference test cases
# Mirrors the format used in openfisca-france/tests/formulas/irpp.yaml
# to verify our pipeline produces bit-identical results to the official
# OpenFisca-France test suite.
# See: https://github.com/openfisca/openfisca-france/tree/master/tests/formulas
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestOpenFiscaFranceReferenceCases:
    """Reference test cases mirroring openfisca-france's own test format.

    These tests use salaire_imposable (taxable salary) as input -- the same
    input variable used in openfisca-france/tests/formulas/irpp.yaml -- to
    verify that our pipeline produces the same results as the official
    OpenFisca-France test suite.

    The expected values were computed directly via OpenFisca-France 175.0.18
    with openfisca-core 44.2.2 on 2026-02-28 and serve as pinned reference
    values for regression detection.
    """

    ABSOLUTE_ERROR_MARGIN = 0.5  # Same margin used by openfisca-france tests

    def test_single_person_salaire_imposable_20k(self, tbs: Any) -> None:
        """Reference: single person, salaire_imposable=20000, period 2024.

        Expected: impot_revenu_restant_a_payer = -150.0
        """
        sim = _build_simulation(tbs, {
            "person_0": {"salaire_imposable": {"2024": 20000.0}},
        })
        irpp = float(sim.calculate("impot_revenu_restant_a_payer", "2024")[0])
        assert abs(irpp - (-150.0)) <= self.ABSOLUTE_ERROR_MARGIN, (
            f"Expected -150.0, got {irpp}"
        )

    def test_single_person_salaire_imposable_50k(self, tbs: Any) -> None:
        """Reference: single person, salaire_imposable=50000, period 2024.

        Expected: impot_revenu_restant_a_payer = -6665.0
        """
        sim = _build_simulation(tbs, {
            "person_0": {"salaire_imposable": {"2024": 50000.0}},
        })
        irpp = float(sim.calculate("impot_revenu_restant_a_payer", "2024")[0])
        assert abs(irpp - (-6665.0)) <= self.ABSOLUTE_ERROR_MARGIN, (
            f"Expected -6665.0, got {irpp}"
        )

    def test_couple_salaire_imposable_30k_25k(self, tbs: Any) -> None:
        """Reference: couple, salaire_imposable=30000+25000, period 2024.

        Expected: impot_revenu_restant_a_payer = -2765.0
        Joint taxation with 2 tax shares (quotient familial).
        """
        sim = _build_simulation(
            tbs,
            {
                "person_0": {"salaire_imposable": {"2024": 30000.0}},
                "person_1": {"salaire_imposable": {"2024": 25000.0}},
            },
            couples=True,
        )
        irpp = float(sim.calculate("impot_revenu_restant_a_payer", "2024")[0])
        assert abs(irpp - (-2765.0)) <= self.ABSOLUTE_ERROR_MARGIN, (
            f"Expected -2765.0, got {irpp}"
        )

    def test_couple_pays_less_than_single_high_earner(self, tbs: Any) -> None:
        """Reference: joint taxation benefit with asymmetric incomes.

        French quotient familial means a couple filing jointly should pay
        less total tax than a single person with the same total income,
        especially when incomes are asymmetric.  We use 80k+0 to make the
        benefit unambiguous (at lower incomes, the decote can make two
        singles cheaper than one couple).
        """
        sim_couple = _build_simulation(
            tbs,
            {
                "person_0": {"salaire_imposable": {"2024": 80000.0}},
                "person_1": {"salaire_imposable": {"2024": 0.0}},
            },
            couples=True,
        )
        irpp_couple = float(sim_couple.calculate("impot_revenu_restant_a_payer", "2024")[0])

        sim_single = _build_simulation(tbs, {
            "person_0": {"salaire_imposable": {"2024": 80000.0}},
        })
        irpp_single = float(sim_single.calculate("impot_revenu_restant_a_payer", "2024")[0])

        # Couple should pay less (less negative = less tax)
        assert irpp_couple > irpp_single, (
            f"Couple ({irpp_couple}) should pay less tax than single earner ({irpp_single})"
        )


# ===========================================================================
# Story 9.2: Multi-entity output array handling (integration tests)
# ===========================================================================


@pytest.fixture(scope="module")
def multi_entity_adapter() -> OpenFiscaApiAdapter:
    """Adapter configured with mixed-entity output variables.

    Story 9.2 AC-1, AC-2, AC-3: Tests multi-entity output extraction
    with real OpenFisca-France variables from different entities.
    """
    return OpenFiscaApiAdapter(
        country_package="openfisca_france",
        output_variables=(
            "salaire_net",                      # individu
            "impot_revenu_restant_a_payer",      # foyer_fiscal
            "revenu_disponible",                 # menage
        ),
    )


@pytest.mark.integration
class TestMultiEntityOutputArrays:
    """Story 9.2 AC-1, AC-2, AC-3: Multi-entity output variable handling.

    These tests validate that the adapter correctly handles output variables
    belonging to different entities, producing separate per-entity tables
    with correct array lengths.
    """

    def test_married_couple_multi_entity_extraction(
        self, tbs: Any, multi_entity_adapter: OpenFiscaApiAdapter
    ) -> None:
        """AC-1, AC-2, AC-3: Married couple with 2 persons, 1 foyer, 1 menage.

        The canonical multi-entity test case from spike 8-1:
        - salaire_net (individu) → 2 values
        - impot_revenu_restant_a_payer (foyer_fiscal) → 1 value
        - revenu_disponible (menage) → 1 value
        """
        from openfisca_core.simulation_builder import SimulationBuilder

        entities_dict = {
            "individus": {
                "person_0": {
                    "salaire_de_base": {"2024": 30000.0},
                    "age": {"2024-01": 30},
                },
                "person_1": {
                    "salaire_de_base": {"2024": 0.0},
                    "age": {"2024-01": 28},
                },
            },
            "familles": {
                "famille_0": {"parents": ["person_0", "person_1"]},
            },
            "foyers_fiscaux": {
                "foyer_0": {"declarants": ["person_0", "person_1"]},
            },
            "menages": {
                "menage_0": {
                    "personne_de_reference": ["person_0"],
                    "conjoint": ["person_1"],
                },
            },
        }

        # Test _resolve_variable_entities with real TBS
        local_tbs = multi_entity_adapter._get_tax_benefit_system()
        vars_by_entity = multi_entity_adapter._resolve_variable_entities(local_tbs)

        # Verify entity grouping
        assert "individus" in vars_by_entity
        assert "foyers_fiscaux" in vars_by_entity
        assert "menages" in vars_by_entity
        assert "salaire_net" in vars_by_entity["individus"]
        assert "impot_revenu_restant_a_payer" in vars_by_entity["foyers_fiscaux"]
        assert "revenu_disponible" in vars_by_entity["menages"]

        # Story 9.3: Resolve periodicities for _extract_results_by_entity
        var_periodicities = multi_entity_adapter._resolve_variable_periodicities(
            local_tbs
        )

        # Build simulation and extract results by entity
        builder = SimulationBuilder()
        simulation = builder.build_from_entities(tbs, entities_dict)

        entity_tables = multi_entity_adapter._extract_results_by_entity(
            simulation, 2024, vars_by_entity, var_periodicities
        )

        # AC-2: Correct array lengths per entity
        assert entity_tables["individus"].num_rows == 2
        assert entity_tables["foyers_fiscaux"].num_rows == 1
        assert entity_tables["menages"].num_rows == 1

        # AC-3: Correct columns per entity
        assert "salaire_net" in entity_tables["individus"].column_names
        assert "impot_revenu_restant_a_payer" in entity_tables["foyers_fiscaux"].column_names
        assert "revenu_disponible" in entity_tables["menages"].column_names

    def test_single_entity_backward_compatible(
        self, tbs: Any
    ) -> None:
        """AC-4: Single-entity output produces backward-compatible result."""
        adapter = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("impot_revenu_restant_a_payer",),
        )

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0]),
                    "age": pa.array([30]),
                }),
            },
            metadata={"source": "integration-test"},
        )
        policy = PolicyConfig(parameters={}, name="test")

        result = adapter.compute(population, policy, 2024)

        # Single entity: entity_tables should be empty
        assert result.entity_tables == {}
        # output_fields works as before
        assert isinstance(result.output_fields, pa.Table)
        assert "impot_revenu_restant_a_payer" in result.output_fields.column_names
        assert result.output_fields.num_rows == 1

    def test_variable_entity_resolution_matches_tbs(self, tbs: Any) -> None:
        """AC-1: Variable entity resolution matches actual TBS entity definitions."""
        # Verify entity attributes are accessible on real TBS variables
        irpp_var = tbs.variables["impot_revenu_restant_a_payer"]
        assert irpp_var.entity.key == "foyer_fiscal"
        assert irpp_var.entity.plural == "foyers_fiscaux"

        salaire_var = tbs.variables["salaire_net"]
        assert salaire_var.entity.key == "individu"
        assert salaire_var.entity.plural == "individus"

        revenu_var = tbs.variables["revenu_disponible"]
        assert revenu_var.entity.key == "menage"
        assert revenu_var.entity.plural == "menages"

    def test_multi_entity_adapter_compute_end_to_end(self, tbs: Any) -> None:
        """AC-1, AC-2, AC-3: Full adapter.compute() with multi-entity output.

        Tests that entity_tables and output_entities metadata are correctly
        populated when output variables span multiple entities.

        Note: This test uses only the individu table in PopulationData.
        The adapter's _population_to_entity_dict handles auto-creation of
        group entities for single-person populations. For married couples
        (2 persons, 1 foyer), all 4 entity tables must be provided.
        """
        adapter = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=(
                "salaire_net",
                "impot_revenu_restant_a_payer",
            ),
        )

        # Use 2 persons, 2 separate foyers (not married) to keep it simple
        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0, 50000.0]),
                    "age": pa.array([30, 45]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="multi-entity-test")

        result = adapter.compute(population, policy, 2024)

        # Multi-entity: entity_tables populated
        assert len(result.entity_tables) == 2
        assert "individus" in result.entity_tables
        assert "foyers_fiscaux" in result.entity_tables

        # AC-2: Correct array lengths
        assert result.entity_tables["individus"].num_rows == 2
        assert result.entity_tables["foyers_fiscaux"].num_rows == 2

        # output_fields is person-entity table
        assert result.output_fields.num_rows == 2
        assert "salaire_net" in result.output_fields.column_names

        # Metadata includes entity information
        assert "output_entities" in result.metadata
        assert "entity_row_counts" in result.metadata


# ===========================================================================
# Story 9.3: Variable periodicity handling (integration tests)
# ===========================================================================


@pytest.fixture(scope="module")
def periodicity_adapter() -> OpenFiscaApiAdapter:
    """Adapter with mixed-periodicity output variables.

    Story 9.3 AC-1, AC-2: Tests periodicity-aware calculation dispatch
    with real OpenFisca-France variables:
    - salaire_net (individu, MONTH) → calculate_add
    - impot_revenu_restant_a_payer (foyer_fiscal, YEAR) → calculate
    """
    return OpenFiscaApiAdapter(
        country_package="openfisca_france",
        output_variables=(
            "salaire_net",                      # individu, MONTH
            "impot_revenu_restant_a_payer",      # foyer_fiscal, YEAR
        ),
    )


@pytest.mark.integration
class TestVariablePeriodicityHandling:
    """Story 9.3 AC-1, AC-2, AC-6: Periodicity-aware calculation dispatch.

    These tests validate that the adapter correctly detects variable
    periodicities and dispatches to the appropriate OpenFisca calculation
    method (calculate vs calculate_add).
    """

    def test_monthly_variable_yearly_aggregation(self, tbs: Any) -> None:
        """AC-2: Monthly variable (salaire_net) with yearly period returns correct sum.

        Story 9.3 AC-2: Given a monthly variable requested for a yearly period,
        the adapter automatically sums the 12 monthly values via calculate_add().
        """
        adapter = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("salaire_net",),
        )

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0]),
                    "age": pa.array([30]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="periodicity-test")

        result = adapter.compute(population, policy, 2024)

        # AC-2: salaire_net should be a positive value representing yearly net salary
        salaire_net = result.output_fields.column("salaire_net")[0].as_py()
        assert 20000 < salaire_net < 30000, (
            f"salaire_net={salaire_net} outside expected range [20000, 30000] "
            f"for 30k gross salary"
        )

        # AC-5: Metadata shows correct dispatch
        assert result.metadata["calculation_methods"]["salaire_net"] == "calculate_add"
        assert result.metadata["variable_periodicities"]["salaire_net"] == "month"

    def test_yearly_variable_uses_calculate(self, tbs: Any) -> None:
        """AC-1: Yearly variable (irpp) with yearly period uses calculate().

        Story 9.3 AC-4: Behavior is identical to pre-change implementation.
        """
        adapter = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("impot_revenu_restant_a_payer",),
        )

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0]),
                    "age": pa.array([30]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="periodicity-test")

        result = adapter.compute(population, policy, 2024)

        # irpp should be negative (tax owed)
        irpp = result.output_fields.column("impot_revenu_restant_a_payer")[0].as_py()
        assert irpp < 0, f"Expected negative irpp (tax), got {irpp}"

        # AC-5: Metadata shows correct dispatch
        assert result.metadata["calculation_methods"]["impot_revenu_restant_a_payer"] == "calculate"
        assert result.metadata["variable_periodicities"]["impot_revenu_restant_a_payer"] == "year"

    def test_mixed_periodicity_compute(
        self, periodicity_adapter: OpenFiscaApiAdapter
    ) -> None:
        """AC-1, AC-2: Mixed periodicity output variables in single compute().

        Story 9.3 AC-1: The adapter uses calculate_add() for monthly variables
        and calculate() for yearly variables, producing correct results for both.
        """
        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0, 50000.0]),
                    "age": pa.array([30, 45]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="mixed-periodicity-test")

        result = periodicity_adapter.compute(population, policy, 2024)

        # Both variables should return results without ValueError
        assert result.output_fields.num_rows == 2
        assert "salaire_net" in result.output_fields.column_names

        # entity_tables should have both entities
        assert "individus" in result.entity_tables
        assert "foyers_fiscaux" in result.entity_tables

        # AC-5: Correct methods per variable
        assert result.metadata["calculation_methods"]["salaire_net"] == "calculate_add"
        assert result.metadata["calculation_methods"]["impot_revenu_restant_a_payer"] == "calculate"

    def test_monthly_variable_end_to_end(self, tbs: Any) -> None:
        """AC-2: End-to-end test that monthly output variable produces correct values.

        Story 9.3 AC-2: adapter.compute() with a monthly output variable
        produces correct yearly aggregated values.
        """
        adapter = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("salaire_net",),
        )

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0]),
                    "age": pa.array([30]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="monthly-e2e-test")

        result = adapter.compute(population, policy, 2024)

        assert isinstance(result, ComputationResult)
        assert result.output_fields.num_rows == 1
        assert "salaire_net" in result.output_fields.column_names

        # Verify the value is reasonable (should be yearly aggregate)
        salaire_net = result.output_fields.column("salaire_net")[0].as_py()
        assert salaire_net > 0, f"Net salary should be positive, got {salaire_net}"

    def test_periodicity_metadata_in_integration(
        self, periodicity_adapter: OpenFiscaApiAdapter
    ) -> None:
        """AC-5: variable_periodicities metadata in integration test result.

        Story 9.3 AC-5: The result metadata includes variable_periodicities
        and calculation_methods entries for each output variable.
        """
        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0]),
                    "age": pa.array([30]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="metadata-test")

        result = periodicity_adapter.compute(population, policy, 2024)

        # AC-5: variable_periodicities present and correct
        assert "variable_periodicities" in result.metadata
        vp = result.metadata["variable_periodicities"]
        assert vp["salaire_net"] == "month"
        assert vp["impot_revenu_restant_a_payer"] == "year"

        # AC-5: calculation_methods present and correct
        assert "calculation_methods" in result.metadata
        cm = result.metadata["calculation_methods"]
        assert cm["salaire_net"] == "calculate_add"
        assert cm["impot_revenu_restant_a_payer"] == "calculate"

    def test_variable_periodicity_resolution_matches_tbs(self, tbs: Any) -> None:
        """AC-1: Variable periodicity resolution matches actual TBS definitions.

        Story 9.3: Verify that definition_period attributes are accessible
        and match expected values for known OpenFisca-France variables.
        """
        # salaire_net is a MONTH variable
        salaire_var = tbs.variables["salaire_net"]
        assert str(salaire_var.definition_period) == "month"

        # impot_revenu_restant_a_payer is a YEAR variable
        irpp_var = tbs.variables["impot_revenu_restant_a_payer"]
        assert str(irpp_var.definition_period) == "year"

        # date_naissance is an ETERNITY variable
        birth_var = tbs.variables["date_naissance"]
        assert str(birth_var.definition_period) == "eternity"


# ===========================================================================
# Story 9.4: 4-entity PopulationData format (integration tests)
# ===========================================================================


@pytest.mark.integration
class TestFourEntityPopulationFormat:
    """Story 9.4: 4-entity PopulationData format via membership columns.

    AC-1: Membership columns produce valid entity dict.
    AC-2: Group membership assignment is correct.
    AC-6: Backward compatibility preserved.
    AC-7: Group entity input variables merged correctly.
    """

    ABSOLUTE_ERROR_MARGIN = 0.5  # Consistent with TestOpenFiscaFranceReferenceCases

    def test_married_couple_via_membership_columns(self, tbs: Any) -> None:
        """AC-1, AC-2: Married couple via membership columns matches hand-built test.

        Should produce the SAME irpp as test_couple_salaire_imposable_30k_25k
        (irpp ≈ -2765.0) — this validates that the membership column approach
        produces identical results to manually building the entity dict.
        """
        adapter = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("impot_revenu_restant_a_payer",),
        )

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_imposable": pa.array([30000.0, 25000.0]),
                    "famille_id": pa.array([0, 0]),
                    "famille_role": pa.array(["parents", "parents"]),
                    "foyer_fiscal_id": pa.array([0, 0]),
                    "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
                    "menage_id": pa.array([0, 0]),
                    "menage_role": pa.array([
                        "personne_de_reference", "conjoint",
                    ]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="4entity-couple-test")

        result = adapter.compute(population, policy, 2024)

        assert isinstance(result, ComputationResult)
        irpp = result.output_fields.column(
            "impot_revenu_restant_a_payer"
        )[0].as_py()

        # Match the reference case value from TestOpenFiscaFranceReferenceCases
        assert abs(float(irpp) - (-2765.0)) <= self.ABSOLUTE_ERROR_MARGIN, (
            f"Expected -2765.0, got {irpp}. Membership columns should produce "
            f"identical results to hand-built entity dict."
        )

    def test_single_person_with_membership_columns(self, tbs: Any) -> None:
        """AC-2, AC-6: Single person with membership columns matches without.

        Results should be identical to single-person tests without membership
        columns — the membership columns just make the entity structure explicit.
        """
        # Adapter with membership columns
        adapter = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("impot_revenu_restant_a_payer",),
        )

        population_with_membership = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0]),
                    "age": pa.array([30]),
                    "famille_id": pa.array([0]),
                    "famille_role": pa.array(["parents"]),
                    "foyer_fiscal_id": pa.array([0]),
                    "foyer_fiscal_role": pa.array(["declarants"]),
                    "menage_id": pa.array([0]),
                    "menage_role": pa.array(["personne_de_reference"]),
                }),
            },
        )

        population_without_membership = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0]),
                    "age": pa.array([30]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="4entity-single-test")

        result_with = adapter.compute(population_with_membership, policy, 2024)
        result_without = adapter.compute(population_without_membership, policy, 2024)

        irpp_with = float(result_with.output_fields.column(
            "impot_revenu_restant_a_payer"
        )[0].as_py())
        irpp_without = float(result_without.output_fields.column(
            "impot_revenu_restant_a_payer"
        )[0].as_py())

        assert abs(irpp_with - irpp_without) < 1.0, (
            f"Single person with membership ({irpp_with}) should match "
            f"without membership ({irpp_without})"
        )

    def test_two_independent_households(self, tbs: Any) -> None:
        """AC-1, AC-2: Two persons in separate households via membership columns."""
        adapter = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("impot_revenu_restant_a_payer",),
        )

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0, 50000.0]),
                    "age": pa.array([30, 45]),
                    "famille_id": pa.array([0, 1]),
                    "famille_role": pa.array(["parents", "parents"]),
                    "foyer_fiscal_id": pa.array([0, 1]),
                    "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
                    "menage_id": pa.array([0, 1]),
                    "menage_role": pa.array([
                        "personne_de_reference", "personne_de_reference",
                    ]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="4entity-independent-test")

        result = adapter.compute(population, policy, 2024)

        assert isinstance(result, ComputationResult)
        # 2 separate foyers → 2 irpp values
        irpp_col = result.output_fields.column("impot_revenu_restant_a_payer")
        assert len(irpp_col) == 2
        # Both should pay tax (negative values)
        assert irpp_col[0].as_py() < 0
        assert irpp_col[1].as_py() < 0
        # Higher salary → more tax
        assert irpp_col[1].as_py() < irpp_col[0].as_py()

    def test_group_entity_input_variables(self, tbs: Any) -> None:
        """AC-7: Group entity table (menage with loyer) is merged into entity dict.

        Verifies that group-level input variables from a separate table are
        correctly period-wrapped and included in the entity dict passed to
        SimulationBuilder.build_from_entities().
        """
        adapter = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("impot_revenu_restant_a_payer",),
        )

        local_tbs = adapter._get_tax_benefit_system()

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0, 0.0]),
                    "age": pa.array([30, 28]),
                    "famille_id": pa.array([0, 0]),
                    "famille_role": pa.array(["parents", "parents"]),
                    "foyer_fiscal_id": pa.array([0, 0]),
                    "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
                    "menage_id": pa.array([0, 0]),
                    "menage_role": pa.array([
                        "personne_de_reference", "conjoint",
                    ]),
                }),
                "menage": pa.table({
                    "loyer": pa.array([800.0]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="4entity-loyer-test")

        # Verify entity dict has loyer merged
        entity_dict = adapter._population_to_entity_dict(
            population, policy, "2024", local_tbs
        )

        assert "loyer" in entity_dict["menages"]["menage_0"]
        assert entity_dict["menages"]["menage_0"]["loyer"] == {"2024": 800.0}

    def test_backward_compatibility_no_membership_columns(
        self,
        adapter: OpenFiscaApiAdapter,
        single_person_population: PopulationData,
        empty_policy: PolicyConfig,
    ) -> None:
        """AC-6: Existing single_person_population fixture still works identically."""
        result = adapter.compute(single_person_population, empty_policy, 2024)

        assert isinstance(result, ComputationResult)
        irpp = result.output_fields.column(
            "impot_revenu_restant_a_payer"
        )[0].as_py()
        assert irpp < 0, f"Expected negative irpp, got {irpp}"

    def test_entity_role_resolution_from_real_tbs(self, tbs: Any) -> None:
        """AC-4: _resolve_valid_role_keys() produces correct keys from real TBS.

        Validates that the role key resolution logic works with real
        OpenFisca-France entity and role objects.
        """
        adapter = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("impot_revenu_restant_a_payer",),
        )
        local_tbs = adapter._get_tax_benefit_system()

        valid_roles = adapter._resolve_valid_role_keys(local_tbs)

        # famille roles
        assert "parents" in valid_roles["famille"]
        assert "enfants" in valid_roles["famille"]

        # foyer_fiscal roles
        assert "declarants" in valid_roles["foyer_fiscal"]
        assert "personnes_a_charge" in valid_roles["foyer_fiscal"]

        # menage roles — personne_de_reference and conjoint have plural=None
        assert "personne_de_reference" in valid_roles["menage"]
        assert "conjoint" in valid_roles["menage"]
        assert "enfants" in valid_roles["menage"]
        assert "autres" in valid_roles["menage"]


]]></file>
<file id="90dfc412" path="[ANTIPATTERNS - DO NOT REPEAT]" label="VIRTUAL CONTENT"><![CDATA[

# Epic 9 - Story Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during validation of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent story-writing mistakes (unclear AC, missing Notes, unrealistic scope).

## Story 9-3 (2026-03-01)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Metadata field name contradiction in AC-5 vs Task 4.3 | Rewrote AC-5 to explicitly name two separate `dict[str, str]` keys with concrete examples; updated Task 4.3 to match with inline examples. *Consensus — both validators independently flagged this.* |
| critical | `_make_mock_tbs()` lacks `definition_period` — silent test regression | Added explicit Task 1.5 requiring `var_mock.definition_period = "year"` in `_make_mock_tbs()` variable loop, with full explanation of the MagicMock failure mode and which specific test breaks (`TestPeriodFormatting.test_period_passed_as_string`). Without this task, the failure is a confusing `AssertionError` ("Expected call: calculate(...) not found") with no obvious cause. |
| critical | `_extract_results_by_entity()` signature change silently breaks 3 existing test callers | Rewrote Task 3.1 to call out the breaking change explicitly, name all 3 affected test methods (`test_single_entity_extraction`, `test_multi_entity_extraction`, `test_multiple_variables_per_entity`), and show the required fix (`variable_periodicities={"var_name": "year"}`). Without this, a dev agent adds a new required parameter and watches 3 previously-passing tests fail with `TypeError`. |
| high | Period validation placement ambiguous in AC-3 and Task 5.1 | Updated AC-3 to specify "very first check before any TBS operations"; updated Task 5.1 to say "FIRST operation in `compute()`, before `_get_tax_benefit_system()`" with rationale for the [1000, 9999] range. |
| high | Explicit `compute()` call order not shown in Task 4.1 | Replaced the vague "fail-fast pattern" note with a numbered 5-step pseudocode sequence showing exactly where `_resolve_variable_periodicities()` fits relative to `_validate_output_variables()`, `_resolve_variable_entities()`, `_build_simulation()`, and `_extract_results_by_entity()`. |
| high | Pre-existing Story 9.2 integration test failure not acknowledged | Updated Task 6.2 to warn that any Story 9.2 integration test using `salaire_net` may already be red (pre-existing `ValueError: Period mismatch`), and that Story 9.3 is expected to turn it green as a side-effect. |
| high | Integration test dispatch verification strategy missing | Expanded Task 7.1 to explain that real `Simulation` objects cannot be mock-asserted, and provided the correct two-pronged verification approach (metadata `calculation_methods` key + value range assertion). |
| medium | AC-6 eternity handling lacks WHY and test verification hint | Expanded AC-6 to add concrete example variables (`date_naissance`, `sexe`), the exact error message `calculate_add()` raises, and a test verification hint (assert `calculate` called, assert `calculate_add` NOT called for `periodicity == "eternity"`). |
| medium | Files to Modify table understates test file changes | Replaced the single-line description with an enumerated 3-change list: (1) `_make_mock_tbs()` update, (2) existing `TestExtractResultsByEntity` caller updates, (3) new test classes. |

## Story 9-4 (2026-03-01)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | Story 9.3 dependency not documented — 9.3 is in-progress and modifies the same file | Added "Prerequisites — Story Sequencing" subsection to Dev Notes with explicit merge-first guidance and concurrent-development strategy. |
| high | Algorithm pseudocode step 3 calls `_detect_membership_columns(person_table, tbs)` without showing how to extract `person_table` from `population.tables` | Algorithm steps 2b and 3 now show the full extraction pattern, including singular/plural key matching and the "no person table → backward-compatible" fallback. |
| high | Task 4.4 "same as current logic" is ambiguous — it was unclear whether the original all-tables loop was replaced or augmented in 4-entity mode | Task 4.4 now explicitly states the original all-tables loop is **replaced** by 4.4+4.5+4.6 combined, with a ⚠️ warning against running both paths. |
| high | Task 4.5 hardcodes `"individu_0"` in role assignment example, contradicting Dev Notes' explanation that the prefix is the `population.tables` key | Task 4.5 example now uses `f"{person_table_key}_0"` with explicit note that this key must match Task 4.4's prefix. |
| high | Task 4.6 positional matching risk was understated — silent data corruption possible when group entity table rows are not in ascending ID order | Task 4.6 now includes an explicit ⚠️ POSITIONAL MATCHING warning, the assumption about row ordering, and a specific unit test to validate non-contiguous ID mapping. |
| medium | Edge Case #3 contained contradictory language: "This can't happen by construction" immediately followed by "Raise ApiMappingError" | Rewritten to accurately describe the actual scenario (group entity table with more rows than distinct person-table group IDs) and explain why the other formulation was contradictory. |
| low | Integration test tolerance margin (`ABSOLUTE_ERROR_MARGIN`) not specified for new tests | Task 6.1 now specifies `ABSOLUTE_ERROR_MARGIN = 0.5` as a class attribute, consistent with the existing reference test suite. |


]]></file>
</context>
<variables>
<var name="architecture_file" description="Architecture (fallback - epics file should have relevant sections)" load_strategy="SELECTIVE_LOAD" token_approx="2785">_bmad-output/planning-artifacts/architecture-diagrams.md</var>
<var name="author">BMad</var>
<var name="communication_language">English</var>
<var name="date">2026-03-01</var>
<var name="default_output_file">_bmad-output/implementation-artifacts/9-5-openfisca-france-reference-test-suite.md</var>
<var name="description">Create the next user story from epics+stories with enhanced context analysis and direct ready-for-dev marking</var>
<var name="document_output_language">English</var>
<var name="epic_num">9</var>
<var name="epics_file" file_id="9e4374e5" description="Enhanced epics+stories file with BDD and source hints" load_strategy="EMBEDDED" token_approx="8484">embedded in prompt, file id: 9e4374e5</var>
<var name="implementation_artifacts">_bmad-output/implementation-artifacts</var>
<var name="name">create-story</var>
<var name="output_folder">_bmad-output/implementation-artifacts</var>
<var name="planning_artifacts">_bmad-output/planning-artifacts</var>
<var name="prd_file" description="PRD (fallback - epics file should have most content)" load_strategy="SELECTIVE_LOAD" token_approx="7305">_bmad-output/planning-artifacts/prd-validation-report.md</var>
<var name="project_context" file_id="b5c6fe32" load_strategy="EMBEDDED" token_approx="2024">embedded in prompt, file id: b5c6fe32</var>
<var name="project_knowledge">docs</var>
<var name="project_name">ReformLab</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_dir">_bmad-output/implementation-artifacts</var>
<var name="story_id">9.5</var>
<var name="story_key">9-5-openfisca-france-reference-test-suite</var>
<var name="story_num">5</var>
<var name="story_title">openfisca-france-reference-test-suite</var>
<var name="timestamp">20260301_2302</var>
<var name="user_name">Lucas</var>
<var name="user_skill_level">expert</var>
<var name="ux_file" description="UX design (fallback - epics file should have relevant sections)" load_strategy="SELECTIVE_LOAD" token_approx="20820">_bmad-output/planning-artifacts/ux-design-specification.md</var>
</variables>
<instructions><workflow>
  <critical>🚫 SCOPE LIMITATION: Your ONLY task is to create the story markdown file. Do NOT read, modify, or update any sprint tracking files - that is handled programmatically by bmad-assist.</critical>
<critical>You MUST have already loaded and processed: the &lt;workflow-yaml&gt; section embedded above</critical>
  <critical>Communicate all responses in English and generate all documents in English</critical>

  <critical>🔥 CRITICAL MISSION: You are creating the ULTIMATE story context engine that prevents LLM developer mistakes, omissions or
    disasters! 🔥</critical>
  <critical>Your purpose is NOT to copy from epics - it's to create a comprehensive, optimized story file that gives the DEV agent
    EVERYTHING needed for flawless implementation</critical>
  <critical>COMMON LLM MISTAKES TO PREVENT: reinventing wheels, wrong libraries, wrong file locations, breaking regressions, ignoring UX,
    vague implementations, lying about completion, not learning from past work</critical>
  <critical>🚨 EXHAUSTIVE ANALYSIS REQUIRED: You must thoroughly analyze ALL artifacts to extract critical context - do NOT be lazy or skim!
    This is the most important function in the entire development process!</critical>
  <critical>🔬 UTILIZE SUBPROCESSES AND SUBAGENTS: Use research subagents, subprocesses or parallel processing if available to thoroughly
    analyze different artifacts simultaneously and thoroughly</critical>
  <critical>❓ SAVE QUESTIONS: If you think of questions or clarifications during analysis, save them for the end after the complete story is
    written</critical>
  <critical>🎯 ZERO USER INTERVENTION: Process should be fully automated except for initial epic/story selection or missing documents</critical>
  <critical>Git Intelligence is EMBEDDED in &lt;git-intelligence&gt; at the start of the prompt - do NOT run git commands yourself, use the embedded data instead</critical>

  <step n="1" goal="Architecture analysis for developer guardrails">
    <critical>🏗️ ARCHITECTURE INTELLIGENCE - Extract everything the developer MUST follow!</critical> **ARCHITECTURE DOCUMENT ANALYSIS:** <action>Systematically
    analyze architecture content for story-relevant requirements:</action>

    <!-- Load architecture - single file or sharded -->
    <check if="architecture file is single file">
      <action>Load complete {architecture_content}</action>
    </check>
    <check if="architecture is sharded to folder">
      <action>Load architecture index and scan all architecture files</action>
    </check> **CRITICAL ARCHITECTURE EXTRACTION:** <action>For
    each architecture section, determine if relevant to this story:</action> - **Technical Stack:** Languages, frameworks, libraries with
    versions - **Code Structure:** Folder organization, naming conventions, file patterns - **API Patterns:** Service structure, endpoint
    patterns, data contracts - **Database Schemas:** Tables, relationships, constraints relevant to story - **Security Requirements:**
    Authentication patterns, authorization rules - **Performance Requirements:** Caching strategies, optimization patterns - **Testing
    Standards:** Testing frameworks, coverage expectations, test patterns - **Deployment Patterns:** Environment configurations, build
    processes - **Integration Patterns:** External service integrations, data flows <action>Extract any story-specific requirements that the
    developer MUST follow</action>
    <action>Identify any architectural decisions that override previous patterns</action>
  </step>

  <step n="2" goal="Web research for latest technical specifics">
    <critical>🌐 ENSURE LATEST TECH KNOWLEDGE - Prevent outdated implementations!</critical> **WEB INTELLIGENCE:** <action>Identify specific
    technical areas that require latest version knowledge:</action>

    <!-- Check for libraries/frameworks mentioned in architecture -->
    <action>From architecture analysis, identify specific libraries, APIs, or
    frameworks</action>
    <action>For each critical technology, research latest stable version and key changes:
      - Latest API documentation and breaking changes
      - Security vulnerabilities or updates
      - Performance improvements or deprecations
      - Best practices for current version
    </action>
    **EXTERNAL CONTEXT INCLUSION:** <action>Include in story any critical latest information the developer needs:
      - Specific library versions and why chosen
      - API endpoints with parameters and authentication
      - Recent security patches or considerations
      - Performance optimization techniques
      - Migration considerations if upgrading
    </action>
  </step>

  <step n="3" goal="Create comprehensive story file">
    <critical>📝 CREATE ULTIMATE STORY FILE - The developer's master implementation guide!</critical>

    <action>Create file using the output-template format at: /Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/9-5-openfisca-france-reference-test-suite.md</action>
    <!-- Story foundation from epics analysis -->
    <!-- Developer context section - MOST IMPORTANT PART -->
    <!-- Previous story intelligence -->
    <!-- Git intelligence -->
    <!-- Latest technical specifics -->
    <!-- Project context reference -->
    <!-- Final status update -->
    <!-- CRITICAL: Set status to ready-for-dev -->
    <action>Set story Status to: "ready-for-dev"</action>
    <action>Add completion note: "Ultimate
    context engine analysis completed - comprehensive developer guide created"</action>
  </step>

  <step n="4" goal="Validate and finalize">
    <!-- checklist validation is separate workflow -->
    <action>Save story document unconditionally</action>

    <action>Report completion</action>
    </step>

</workflow></instructions>
<output-template><![CDATA[

# Story {{epic_num}}.{{story_num}}: {{story_title}}

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a {{role}},
I want {{action}},
so that {{benefit}}.

## Acceptance Criteria

1. [Add acceptance criteria from epics/PRD]

## Tasks / Subtasks

- [ ] Task 1 (AC: #)
  - [ ] Subtask 1.1
- [ ] Task 2 (AC: #)
  - [ ] Subtask 2.1

## Dev Notes

- Relevant architecture patterns and constraints
- Source tree components to touch
- Testing standards summary

### Project Structure Notes

- Alignment with unified project structure (paths, modules, naming)
- Detected conflicts or variances (with rationale)

### References

- Cite all technical details with source paths and sections, e.g. [Source: docs/<file>.md#Section]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

]]></output-template>
</compiled-workflow>