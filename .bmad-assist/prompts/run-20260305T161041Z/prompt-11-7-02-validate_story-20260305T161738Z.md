<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 11 -->
<!-- Story: 7 -->
<!-- Phase: validate-story -->
<!-- Timestamp: 20260305T161738Z -->
<compiled-workflow>
<mission><![CDATA[

Adversarial Story Validation

Target: Story 11.7 - implement-population-validation-against-known-marginals

Your mission is to FIND ISSUES in the story file:
- Identify missing requirements or acceptance criteria
- Find ambiguous or unclear specifications
- Detect gaps in technical context
- Suggest improvements for developer clarity

CRITICAL: You are a VALIDATOR, not a developer.
- Read-only: You cannot modify any files
- Adversarial: Assume the story has problems
- Thorough: Check all sections systematically

Focus on STORY QUALITY, not code implementation.

]]></mission>
<context>
<file id="e58fb4dd" path="docs/project-context.md" label="PROJECT CONTEXT"><![CDATA[

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
_Updated 2026-03-03: Phase 2 Architecture Extensions added per Sprint Change Proposal 2026-03-02. New subsystems (population, calibration), policy portfolios, discrete choice model, unified job execution, adaptive UI, external data caching, multi-portfolio comparison. See sprint-change-proposal-2026-03-02.md._

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

**Functional focus (55 FRs — 35 Phase 1, 20 Phase 2):**

- OpenFisca integration and data contracts.
- Environmental scenario templates and batch comparison.
- Dynamic yearly orchestration with vintage tracking.
- Indicator computation and extensibility.
- Governance, reproducibility, and lineage.
- Notebook/API + early no-code GUI workflows.
- _Phase 2:_ Population generation and data fusion (FR36-FR42).
- _Phase 2:_ Policy portfolios (FR43-FR46).
- _Phase 2:_ Behavioral responses via discrete choice (FR47-FR51).
- _Phase 2:_ Calibration engine (FR52-FR53).
- _Phase 2:_ Replication package export (FR54-FR55).

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
- Fully offline operation in user environment (Phase 1). Phase 2 introduces optional network dependencies for institutional data downloads (INSEE, Eurostat, ADEME, SDES) with offline fallback — see External Data Caching section.
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
┌─────────────────────────────────────────────────────┐
│  Interfaces (Python API, Notebooks, GUI Showcase)    │
│  └── Job Dashboard (submit, monitor, browse results) │
├─────────────────────────────────────────────────────┤
│  Indicator Engine (distributional/welfare/fiscal)    │
│  └── Multi-Portfolio Comparison                      │
├─────────────────────────────────────────────────────┤
│  Governance (manifests, assumptions, lineage)        │
├─────────────────────────────────────────────────────┤
│  Calibration Engine (β parameter optimization)       │
├─────────────────────────────────────────────────────┤
│  Dynamic Orchestrator (year loop + step pipeline)    │
│  ├── Vintage Transitions                             │
│  ├── State Carry-Forward                             │
│  └── DiscreteChoiceStep (logit-based decisions)      │
├─────────────────────────────────────────────────────┤
│  Scenario Template Layer (policies + portfolios)     │
│  └── Policy Portfolio Composition                    │
├─────────────────────────────────────────────────────┤
│  Data Layer (ingestion, open data, populations)      │
│  └── Population Generation Library (data fusion)     │
├─────────────────────────────────────────────────────┤
│  Computation Adapter Interface                       │
│  └── OpenFiscaAdapter (primary implementation)       │
└─────────────────────────────────────────────────────┘
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

**Phase 1 (delivered):**

1. `computation/`: Adapter interface + OpenFiscaAdapter implementation. Handles CSV/Parquet ingestion of OpenFisca outputs and optional direct API orchestration. Version-pinned contracts.
2. `data/`: Open data ingestion, synthetic population generation, data transformation pipelines. Prepares inputs for the computation adapter.
3. `templates/`: Environmental policy templates (carbon tax, subsidies, rebates, feebates) and scenario registry with versioned definitions.
4. `orchestrator/`: Dynamic yearly loop with step-pluggable pipeline. Manages deterministic sequencing, seed control, and state transitions.
5. `vintage/`: Cohort/vintage state management. Registered as orchestrator step. Tracks asset classes (vehicles, heating) through time.
6. `indicators/`: Distributional, welfare, fiscal, and custom indicator computation. Aggregation by decile, geography, and custom groupings.
7. `governance/`: Run manifests, assumption logs, run lineage, output hashes. Tracks OpenFisca version, adapter version, scenario version.
8. `interfaces/`: Python API, notebook workflows, early no-code GUI.

**Phase 2 (new + extended):**

1. `population/`: Realistic population generation library. Institutional data source loaders (INSEE, Eurostat, ADEME, SDES), statistical methods library (uniform, IPF, conditional sampling, statistical matching), population pipeline builder, assumption recording, validation against known marginals.
2. `templates/portfolios/`: Policy portfolio composition. Named, versioned collections of policy configs. Portfolio execution through orchestrator, compatibility validation, conflict resolution.
3. `orchestrator/steps/discrete_choice.py`: DiscreteChoiceStep registered as standard OrchestratorStep. Population expansion, logit model, seed-controlled draws, panel decision records.
4. `calibration/`: Calibration engine for discrete choice taste parameters. Objective function optimization against observed transition rates, validation against holdout data.
5. `server/jobs/`: Unified job execution system. File-based job store, background worker, progress reporting, persistent results. Replaces synchronous run model.
6. `frontend/`: GUI showcase product — data fusion workbench, policy portfolio designer, simulation dashboard, persistent results, multi-portfolio comparison, behavioral decision viewer.

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

### Phase 2 Architecture Extensions (2026-03-03)

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

#### External Data Caching & Offline Strategy

Phase 1 had zero network dependencies at runtime. Phase 2 introduces optional HTTP downloads from institutional sources (INSEE, Eurostat, ADEME, SDES). The caching strategy ensures offline-first operation:

**Two-layer cache:**

```
~/.reformlab/cache/
  sources/
    insee/
      {dataset_id}/{hash}.parquet    ← downloaded + schema-validated
    eurostat/
      ...
```

- **First run:** Loader downloads, validates schema, writes to local cache. Hash-based freshness (SHA256 of URL + params + date).
- **Subsequent runs:** Cache hit → no network. Cache miss → download. Network failure + cache exists → use stale cache with governance warning logged.
- **Fully offline mode:** Environment variable `REFORMLAB_OFFLINE=1` — loaders only read cache, never attempt network. Fail explicitly if cache miss.
- **CI/CD:** Tests ship with small fixture files, never hit real APIs. Integration tests for real downloads are opt-in (`pytest -m network`).

**Loader protocol includes cache status reporting:**

```python
class CacheStatus:
    """Status of a cached data source."""
    cached: bool
    path: Path | None
    downloaded_at: datetime | None
    hash: str | None
    stale: bool

class DataSourceLoader(Protocol):
    def download(self, config: SourceConfig) -> pa.Table: ...
    def status(self, config: SourceConfig) -> CacheStatus: ...
    def schema(self) -> pa.Schema: ...
```

The GUI Data Fusion Workbench displays cache status per dataset so analysts know which sources are available offline.

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

Registers as a standard `OrchestratorStep` via existing protocol. Implementation follows the design note (`phase-2-design-note-discrete-choice-household-decisions.md`):

- Population expansion: clone households × N alternatives, modify attributes per alternative
- OpenFisca batch evaluation: call `adapter.compute()` on expanded population
- Reshape to cost matrix: N households × M alternatives
- Logit probability computation: `P(j|C_i) = exp(V_ij) / Σ_k exp(V_ik)`
- Seed-controlled draw: deterministic choice per household
- State update: modify household attributes + create vintage entries

No changes to `ComputationAdapter` interface or orchestrator core needed.

**Performance budget:** Discrete choice introduces ~11x computation scaling (100k households × 5 alternatives × 2 domains). Target: 10-year discrete choice run with 100k households completes in <60s on laptop. Eligibility filtering is mandatory — only eligible households face choices (a household without a car does not face a vehicle investment decision). This is both a performance requirement and a model correctness requirement.

#### New Subsystem: Calibration (`calibration/`)

```
src/reformlab/calibration/
├── __init__.py
├── engine.py          ← CalibrationEngine (optimize β parameters)
├── targets.py         ← Observed transition rates as calibration targets
├── objective.py       ← Objective function (minimize distance to observed rates)
└── validation.py      ← Validate calibrated parameters against holdout data
```

#### Unified Job Execution Model

Phase 1 used synchronous `POST /api/runs` (blocking until completion). Phase 2 replaces this with a **unified job queue** that handles both fast static runs and long-running discrete choice simulations through a single execution path.

**Design: Submit → Persist → Execute → Results Available**

Every simulation is a job. The backend does not distinguish between "fast" and "slow" runs. The frontend adapts:

- **Fast completion (<~5s):** UI auto-navigates to results. Feels instant to the analyst.
- **Slow completion:** UI shows progress, informs analyst they can leave. Job keeps running.
- **Analyst leaves and returns:** Completed jobs are browsable in the simulation dashboard.

**Job store on disk:**

```
/data/reformlab/jobs/
  {job_id}/
    job.json             ← submitted config, status, timestamps
    progress.json        ← last reported progress (year, step, pct)
    result/
      manifest.json      ← run governance manifest
      panel.parquet      ← full panel output
      decisions.parquet  ← discrete choice decision records (Phase 2)
```

**Job lifecycle:**

1. On submit: write `job.json` with status `queued`, return `job_id`
2. Worker thread picks up queued jobs, updates status to `running`, writes `progress.json` as it goes
3. On completion: writes results to `result/`, updates status to `completed`
4. On server restart: scan `/jobs/` directory, resume or mark interrupted jobs as `failed`

**Implementation:** Single background worker thread with `ThreadPoolExecutor(max_workers=1)` for MVP. No Celery, no Redis. Upgrade to thread pool for parallelism if needed.

```python
class JobRunner:
    def __init__(self, store: JobStore, max_workers: int = 1):
        self._store = store
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    def submit(self, config: JobConfig) -> str:
        job_id = self._store.create(config)  # persists to disk
        self._executor.submit(self._run, job_id)
        return job_id
```

**Progress reporting:** Orchestrator callbacks `on_year_start(year)` and `on_step_progress(step_name, pct)` write to `progress.json`. Frontend polls for updates.

**Result access:** In-memory `ResultCache` (LRU, max 10) sits on top of the file-based job store. Cache miss → load from disk. Cache hit → serve from memory.

#### Extension: Multi-Portfolio Comparison

Phase 1 comparison was pairwise (one baseline vs one reform). Phase 2 extends to N-way comparison for policy portfolio analysis:

- Every reform is compared against the same baseline — standard policy analysis pattern
- Cross-comparison adds aggregate metrics: "which portfolio maximizes welfare?", "which has lowest fiscal cost?"
- The pairwise comparison API remains as a convenience alias (N=1 case)

#### Extension: Server Routes

New API route groups for Phase 2:

- `/api/populations` — CRUD + generation pipeline execution + cache status
- `/api/portfolios` — CRUD + composition + versioning
- `/api/calibration` — run calibration + retrieve results
- `/api/jobs` — submit, status, result, cancel, list (replaces synchronous `/api/runs`)
- `/api/comparison` — extended to support multi-portfolio comparison

#### Extension: Frontend

Major new GUI sections for EPIC-17:

- **Data Fusion Workbench:** Browse available datasets with cache status, select sources, choose merge methods with plain-language explanations, preview populations, validate against marginals
- **Policy Portfolio Designer:** Browse templates, compose portfolios, configure parameters per policy, name and version portfolios
- **Simulation Dashboard:** Submit jobs, monitor progress, browse completed simulations — all jobs listed with status, timestamps, and results access
- **Persistent Results:** Completed simulations stored on disk, browsable across browser sessions, no re-runs needed
- **Comparison Dashboard:** Side-by-side comparison across N policy portfolios with distributional, welfare, and fiscal indicators
- **Behavioral Decision Viewer:** Explore household decisions from discrete choice model (who switched vehicles, by decile, by year)

### Phase 3+ Architecture Extensions

- **Automated sensitivity sweeps:** Parameter variation automation over calibrated discrete choice models
- **System dynamics bridge:** Aggregate stock-flow outputs derived from microsimulation vintage tracking results
- **Alternative computation backends:** Swap adapter implementations without changing orchestrator or indicator layers
- **Public-facing web app:** Citizen-facing UI with guided questionnaire and candidate comparison

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

### Data Storage

File-based, no database:

- **Scenario configs:** YAML/JSON files on server disk (`/data/reformlab/`)
- **Run outputs:** CSV/Parquet on server disk
- **Run manifests:** JSON on server disk
- **Scenario registry:** File-based (already implemented in EPIC-2)
- **Job store (Phase 2):** `/data/reformlab/jobs/{job_id}/` directories with `job.json`, `progress.json`, and `result/` subdirectory containing `manifest.json`, `panel.parquet`, `decisions.parquet`
- **Population cache (Phase 2):** `~/.reformlab/cache/sources/` — downloaded institutional datasets, hash-based freshness
- **Portfolio configs (Phase 2):** YAML/JSON in scenario registry, versioned alongside individual scenarios

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

```text
src/reformlab/server/
├── __init__.py
├── app.py              ← FastAPI app factory (create_app())
├── auth.py             ← Shared-password middleware
├── models.py           ← Pydantic v2 request/response models
├── dependencies.py     ← Dependency injection (adapter, job runner, result cache)
├── jobs.py             ← JobStore + JobRunner (Phase 2: unified job execution)
└── routes/
    ├── __init__.py
    ├── scenarios.py    ← Scenario CRUD
    ├── jobs.py         ← Job submission, status, results (Phase 2: replaces runs.py)
    ├── runs.py         ← Simulation execution (Phase 1: synchronous, kept for backwards compat)
    ├── indicators.py   ← Indicator computation
    ├── comparison.py   ← Multi-portfolio comparison (Phase 2)
    ├── exports.py      ← File export/download
    ├── templates.py    ← Template listing
    ├── populations.py  ← Population CRUD + generation + cache status (Phase 2: extended)
    ├── portfolios.py   ← Portfolio CRUD + composition (Phase 2)
    └── calibration.py  ← Calibration run + results (Phase 2)
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
    app.include_router(jobs_router,        prefix="/api/jobs")         # Phase 2: unified job execution
    app.include_router(runs_router,        prefix="/api/runs")         # Phase 1: kept for backwards compat
    app.include_router(indicators_router,  prefix="/api/indicators")
    app.include_router(comparison_router,  prefix="/api/comparison")   # Phase 2: multi-portfolio
    app.include_router(exports_router,     prefix="/api/exports")
    app.include_router(templates_router,   prefix="/api/templates")
    app.include_router(populations_router, prefix="/api/populations")
    app.include_router(portfolios_router,  prefix="/api/portfolios")   # Phase 2
    app.include_router(calibration_router, prefix="/api/calibration")  # Phase 2

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

#### Simulation Runs (Phase 1 — synchronous, kept for backwards compatibility)

| Method | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| `POST` | `/api/runs` | `RunRequest` | `RunResponse` | 200 or 422/500 |
| `POST` | `/api/runs/memory-check` | `MemoryCheckRequest` | `MemoryCheckResponse` | 200 |

Phase 1 synchronous endpoint remains available for simple, fast runs. Internally delegates to the job system and waits for completion.

#### Jobs (Phase 2 — unified job execution)

| Method | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| `POST` | `/api/jobs` | `JobSubmitRequest` | `{ "job_id": "string" }` | 202 |
| `GET` | `/api/jobs` | — | `{ "jobs": [JobSummary, ...] }` | 200 |
| `GET` | `/api/jobs/{job_id}` | — | `JobStatusResponse` | 200 or 404 |
| `GET` | `/api/jobs/{job_id}/result` | — | `JobResultResponse` | 200 or 404/409 |
| `DELETE` | `/api/jobs/{job_id}` | — | — | 204 or 404 |

**Execution model:** Every simulation is a job. `POST /api/jobs` persists the job config to disk and returns immediately with a `job_id`. A background worker thread picks up queued jobs and executes them. Results are persisted to disk and survive server restarts.

**Frontend adaptive UI:** The frontend polls `GET /api/jobs/{job_id}` after submission. If the job completes within ~5s, the UI auto-navigates to results (feels instant). If it takes longer, the UI shows progress and informs the analyst they can leave. All jobs are browsable in the simulation dashboard regardless of completion time.

#### Indicators

| Method | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| `POST` | `/api/indicators/{type}` | `IndicatorRequest` | `IndicatorResponse` | 200 or 422 |

`{type}` is one of: `distributional`, `geographic`, `welfare`, `fiscal`.

Delegates to: `cached_result.indicators(type, **kwargs)`.

#### Comparison (Phase 2 — multi-portfolio)

| Method | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| `POST` | `/api/comparison` | `ComparisonRequest` | `IndicatorResponse` | 200 or 422 |
| `POST` | `/api/comparison/multi` | `MultiComparisonRequest` | `MultiComparisonResponse` | 200 or 422 |

Phase 1 pairwise comparison (`ComparisonRequest` with `baseline_run_id` + `reform_run_id`) remains as a convenience. Phase 2 adds N-way comparison: one baseline vs multiple reform portfolios, with cross-comparison aggregate metrics.

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

#### Populations (Phase 2 — extended with generation + cache status)

| Method | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| `GET` | `/api/populations` | — | `{ "populations": [PopulationItem, ...] }` | 200 |
| `GET` | `/api/populations/{id}` | — | `PopulationDetailResponse` | 200 or 404 |
| `POST` | `/api/populations/generate` | `PopulationGenerateRequest` | `{ "job_id": "string" }` | 202 |
| `GET` | `/api/populations/sources` | — | `{ "sources": [DataSourceStatus, ...] }` | 200 |
| `GET` | `/api/populations/sources/{name}/cache` | — | `CacheStatusResponse` | 200 or 404 |

Phase 1 listing remains. Phase 2 adds population generation (submitted as a job), data source browsing, and cache status reporting for the Data Fusion Workbench.

#### Portfolios (Phase 2)

| Method | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| `GET` | `/api/portfolios` | — | `{ "portfolios": [PortfolioSummary, ...] }` | 200 |
| `GET` | `/api/portfolios/{name}` | — | `PortfolioDetailResponse` | 200 or 404 |
| `POST` | `/api/portfolios` | `PortfolioCreateRequest` | `PortfolioDetailResponse` | 201 or 422 |
| `PUT` | `/api/portfolios/{name}` | `PortfolioUpdateRequest` | `PortfolioDetailResponse` | 200 or 404/422 |
| `DELETE` | `/api/portfolios/{name}` | — | — | 204 or 404 |

CRUD for policy portfolios. Portfolios are named, versioned collections of policy configs stored in the scenario registry.

#### Calibration (Phase 2)

| Method | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| `POST` | `/api/calibration/run` | `CalibrationRunRequest` | `{ "job_id": "string" }` | 202 |
| `GET` | `/api/calibration/{job_id}` | — | `CalibrationResultResponse` | 200 or 404/409 |

Calibration runs are submitted as jobs (same as simulations). Results include optimized taste parameters and validation metrics.

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

# Phase 2 request models

class JobSubmitRequest(BaseModel):
    template_name: str | None = None       # single policy run
    portfolio_name: str | None = None      # portfolio run (Phase 2)
    parameters: dict[str, Any] = {}
    start_year: int
    end_year: int
    population_id: str | None = None
    seed: int | None = None
    baseline_id: str | None = None
    name: str = ""                         # human-readable job name

class PopulationGenerateRequest(BaseModel):
    name: str
    sources: list[str]                     # data source loader names
    merge_steps: list[dict[str, Any]]      # [{method: "ipf", left: ..., right: ..., config: ...}]
    validate_marginals: bool = True

class PortfolioCreateRequest(BaseModel):
    name: str
    description: str = ""
    policies: list[dict[str, Any]]         # [{template_name: ..., parameters: ...}]

class PortfolioUpdateRequest(BaseModel):
    description: str | None = None
    policies: list[dict[str, Any]] | None = None

class MultiComparisonRequest(BaseModel):
    baseline_run_id: str
    reform_run_ids: list[str]
    indicator_types: list[str] = ["distributional", "welfare", "fiscal"]

class CalibrationRunRequest(BaseModel):
    population_id: str
    domain: str                            # "vehicle" | "heating"
    observed_rates: dict[str, float]       # calibration targets
    initial_betas: dict[str, float] = {}
    method: str = "mse"                    # "mse" | "likelihood"
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

# Phase 2 response models

class JobSummary(BaseModel):
    job_id: str
    name: str
    state: str                             # "queued" | "running" | "completed" | "failed" | "cancelled"
    submitted_at: str                      # ISO 8601
    completed_at: str | None = None
    portfolio_name: str | None = None
    template_name: str | None = None
    population_id: str | None = None

class JobStatusResponse(JobSummary):
    progress: dict[str, Any] | None = None  # {"year": 2028, "step": "discrete_choice", "pct": 45}

class JobResultResponse(BaseModel):
    job_id: str
    success: bool
    years: list[int]
    row_count: int
    manifest_id: str
    has_decisions: bool                    # True if discrete choice ran

class PortfolioSummary(BaseModel):
    name: str
    description: str
    version: str
    policy_count: int

class PortfolioDetailResponse(PortfolioSummary):
    policies: list[dict[str, Any]]

class DataSourceStatus(BaseModel):
    name: str
    description: str
    cache: CacheStatusResponse | None = None

class CacheStatusResponse(BaseModel):
    cached: bool
    downloaded_at: str | None = None
    hash: str | None = None
    stale: bool = False

class MultiComparisonResponse(BaseModel):
    baseline: JobSummary
    reforms: dict[str, dict[str, Any]]     # run_id → indicators + deltas vs baseline
    cross_comparison: dict[str, Any]       # aggregate cross-portfolio metrics

class CalibrationResultResponse(BaseModel):
    job_id: str
    state: str
    domain: str
    optimized_betas: dict[str, float] | None = None
    objective_value: float | None = None
    validation_metrics: dict[str, Any] | None = None
```

### Serialization Rules

- **PyArrow `pa.Table` → JSON:** `table.to_pydict()` produces `dict[str, list]`. This is the canonical wire format for panel data and indicator tables.
- **`Path` objects:** Serialize as strings via Pydantic `model_serializer`.
- **`datetime` objects:** Serialize as ISO 8601 strings.
- **Frozen dataclasses:** Converted to Pydantic models at the route handler boundary. No `dataclasses.asdict()` in responses — explicit Pydantic field mapping.

### Job Store & Result Cache (Phase 2)

Phase 2 replaces the ephemeral in-memory result cache with a two-tier architecture: persistent file-based `JobStore` + in-memory `ResultCache` for hot access.

**JobStore** — persistent, file-based, survives server restarts:

```python
class JobStore:
    """File-based job persistence. Each job is a directory on disk."""

    def __init__(self, base_path: Path):
        self._base = base_path  # /data/reformlab/jobs/

    def create(self, config: JobConfig) -> str:
        """Persist job config to disk, return job_id."""
        ...

    def update_status(self, job_id: str, state: str) -> None:
        """Update job.json status field."""
        ...

    def update_progress(self, job_id: str, progress: dict) -> None:
        """Write progress.json (year, step, pct)."""
        ...

    def save_result(self, job_id: str, result: SimulationResult) -> None:
        """Write panel.parquet + manifest.json + decisions.parquet to result/."""
        ...

    def load_result(self, job_id: str) -> SimulationResult:
        """Load result from disk."""
        ...

    def list_jobs(self) -> list[JobSummary]:
        """Scan job directories, return summaries."""
        ...

    def delete(self, job_id: str) -> None:
        """Remove job directory."""
        ...
```

**ResultCache** — in-memory LRU, wraps JobStore for hot access:

```python
class ResultCache:
    """In-memory LRU cache backed by JobStore."""

    def __init__(self, store: JobStore, max_size: int = 10):
        self._store = store
        self._cache: OrderedDict[str, SimulationResult] = OrderedDict()
        self._max_size = max_size

    def get(self, job_id: str) -> SimulationResult | None:
        # Check memory first
        if job_id in self._cache:
            self._cache.move_to_end(job_id)
            return self._cache[job_id]
        # Fall back to disk
        result = self._store.load_result(job_id)
        if result is not None:
            self._put(job_id, result)
        return result

    def _put(self, job_id: str, result: SimulationResult) -> None:
        if len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)
        self._cache[job_id] = result
```

- `POST /api/jobs` creates a job via `JobStore.create()`. Background worker executes and calls `JobStore.save_result()`.
- `GET /api/jobs/{job_id}/result`, `POST /api/indicators/{type}`, and `POST /api/exports/*` retrieve results via `ResultCache.get()` (memory first, disk fallback).
- Max 10 entries in memory. LRU eviction. Disk store has no size limit (manual cleanup via `DELETE /api/jobs/{job_id}`).

### Dependency Injection

```python
# src/reformlab/server/dependencies.py

# Global singletons (created once in app factory, injected via Depends)
_job_store: JobStore | None = None
_job_runner: JobRunner | None = None
_result_cache: ResultCache | None = None
_adapter: ComputationAdapter | None = None

def get_job_store() -> JobStore:
    global _job_store
    if _job_store is None:
        _job_store = JobStore(base_path=_data_path() / "jobs")
    return _job_store

def get_job_runner() -> JobRunner:
    global _job_runner
    if _job_runner is None:
        _job_runner = JobRunner(store=get_job_store(), max_workers=1)
    return _job_runner

def get_result_cache() -> ResultCache:
    global _result_cache
    if _result_cache is None:
        _result_cache = ResultCache(store=get_job_store(), max_size=10)
    return _result_cache

def get_adapter() -> ComputationAdapter:
    global _adapter
    if _adapter is None:
        _adapter = _create_adapter()
    return _adapter
```

Route handlers use `Depends(get_job_runner)`, `Depends(get_result_cache)`, and `Depends(get_adapter)`.

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

**Phase 2 (job-based):**

```text
Frontend (React)
    │
    ├─ POST /api/jobs { template|portfolio, params, years }
    │       ↓
    │  JobSubmitRequest → JobStore.create() → job.json persisted to disk
    │       ↓
    │  { "job_id": "..." } returned immediately (202)
    │       ↓
    │  Background worker: JobRunner picks up job → run_scenario() → JobStore.save_result()
    │
    ├─ GET /api/jobs/{job_id} (frontend polls every 2s)
    │       ↓
    │  JobStore reads job.json + progress.json
    │       ↓
    │  JobStatusResponse { state, progress: { year, step, pct } }
    │       ↓
    │  Frontend: if completed in <~5s → auto-navigate to results
    │            if still running     → show progress, "you can leave"
    │
    ├─ GET /api/jobs/{job_id}/result
    │       ↓
    │  ResultCache.get(job_id) → memory hit or disk load
    │       ↓
    │  JobResultResponse { success, years, row_count, has_decisions }
    │
    ├─ POST /api/indicators/distributional { run_id }
    │       ↓
    │  ResultCache.get(run_id) → result.indicators("distributional")
    │       ↓
    │  IndicatorResponse
    │
    ├─ POST /api/comparison/multi { baseline_run_id, reform_run_ids }
    │       ↓
    │  For each reform: ResultCache.get() → indicators vs baseline
    │       ↓
    │  MultiComparisonResponse { reforms, cross_comparison }
    │
    └─ POST /api/exports/csv { run_id }
            ↓
        ResultCache.get(run_id) → result.export_csv(tmp) → StreamingResponse
```

### Code Quality Standards

- `from __future__ import annotations` at top of every server module.
- Pydantic v2 conventions: `model_validate()`, `model_dump()`, `ConfigDict`.
- `mypy --strict` must pass on all server code.
- `ruff` compliance (E, F, I, W rules).
- No direct OpenFisca imports in server code — adapter protocol only.
- Structured logging with `logging.getLogger(__name__)`.


]]></file>
<file id="6870c5a9" path="_bmad-output/implementation-artifacts/11-4-define-mergemethod-protocol-and-uniform-distribution-method.md" label="STORY FILE"><![CDATA[


# Story 11.4: Define MergeMethod protocol and implement uniform distribution method

Status: dev-complete

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform developer building the French household population pipeline,
I want a `MergeMethod` protocol defining the interface for statistical dataset fusion and a concrete `UniformMergeMethod` implementation that randomly matches rows between two tables,
so that downstream stories (11.5 IPF/conditional sampling, 11.6 pipeline builder) have a proven protocol pattern to follow, and the simplest merge method is available as a baseline for population construction.

## Acceptance Criteria

1. Given the `MergeMethod` protocol, when a new method is implemented, then it must accept two `pa.Table` inputs plus a config, and return a merged table plus an assumption record.
2. Given two tables with no shared sample, when merged using uniform distribution, then each row from Table A is matched with a uniformly random row from Table B with replacement, using the provided `MergeConfig.seed` to guarantee reproducibility.
3. Given a uniform merge, when the assumption record is inspected, then it states: "Each household in source A is matched to a household in source B with uniform probability — this assumes no correlation between the variables in the two sources."
4. Given the uniform method docstring, when read, then it includes a plain-language explanation of the independence assumption and when this is appropriate vs. problematic.

## Tasks / Subtasks

- [x] Task 1: Create `src/reformlab/population/methods/` directory structure (AC: #1)
  - [x]1.1 Create `src/reformlab/population/methods/__init__.py` with module docstring referencing Story 11.4, FR38, FR39
  - [x]1.2 Create `src/reformlab/population/methods/errors.py` with `MergeError` base exception and `MergeValidationError` — follow the `summary - reason - fix` pattern from `DataSourceError` in `population/loaders/errors.py`

- [x] Task 2: Define `MergeMethod` protocol and supporting types — `base.py` (AC: #1, #3)
  - [x]2.1 Create `src/reformlab/population/methods/base.py` with module docstring referencing Story 11.4, FR38
  - [x]2.2 Define `MergeConfig` frozen dataclass with fields: `seed: int`, `description: str = ""`, `drop_right_columns: tuple[str, ...] = ()` — validate in `__post_init__` that `seed` is a non-negative integer and not a `bool` (Python `bool ⊂ int`; follow `manifest.py:219` pattern)
  - [x]2.3 Define `MergeAssumption` frozen dataclass with fields: `method_name: str`, `statement: str`, `details: dict[str, Any]` — include `to_governance_entry(*, source_label: str = "merge_step") -> dict[str, Any]` method that produces a dict compatible with `governance.manifest.AssumptionEntry` (keys: `key`, `value`, `source`, `is_default`). `details` values must be JSON-compatible (`str`, `int`, `float`, `bool`, `None`, `list`, `dict`) — enforced at `RunManifest` construction by `_validate_json_compatible()`. Never put `pa.Table`, `pa.Schema`, `Path`, or custom objects in `details`. The `to_governance_entry()` must unpack `**self.details` first, then override with `method` and `statement` keys to prevent key collision from details
  - [x]2.4 Define `MergeResult` frozen dataclass with fields: `table: pa.Table`, `assumption: MergeAssumption`
  - [x]2.5 Define `MergeMethod` as `@runtime_checkable` Protocol with two required members:
    - `def merge(self, table_a: pa.Table, table_b: pa.Table, config: MergeConfig) -> MergeResult`
    - `name: str` property (read-only)
  - [x]2.6 Validate design: `MergeConfig.__post_init__` deep-copies `drop_right_columns` to prevent aliasing (use `object.__setattr__` pattern from `SourceConfig`)
  - [x]2.7 Validate design: `MergeAssumption.details` deep-copied in `__post_init__` to prevent mutation

- [x] Task 3: Implement `UniformMergeMethod` — `uniform.py` (AC: #2, #3, #4)
  - [x]3.1 Create `src/reformlab/population/methods/uniform.py` with module docstring referencing Story 11.4, FR38, FR39 — include the pedagogical docstring explaining the independence assumption in plain language (when appropriate: independent surveys; when problematic: correlated variables)
  - [x]3.2 Implement `UniformMergeMethod` class with `__init__(self)` (no constructor parameters — uniform has no method-specific config)
  - [x]3.3 Implement `name` property returning `"uniform"`
  - [x]3.4 Implement `merge(self, table_a, table_b, config)` with this logic:
    1. Validate inputs: both tables must have `num_rows > 0`; raise `MergeValidationError` if empty
    2. Apply `config.drop_right_columns`: remove listed columns from table_b before merge; raise `MergeValidationError` if a column in `drop_right_columns` does not exist in table_b
    3. Check column name conflicts: `set(table_a.schema.names) & set(remaining_b.schema.names)` — raise `MergeValidationError` with exact overlapping names if any
    4. Generate random indices: `random.Random(config.seed)`, generate `table_a.num_rows` random integers in `[0, remaining_b.num_rows)` — this is random matching with replacement (each row from B can be matched to multiple rows from A)
    5. Select matched rows: `remaining_b.take(pa.array(indices))` — efficient vectorized row selection
    6. Combine columns: build merged table by combining all columns from table_a and matched table_b columns
    7. Build `MergeAssumption` with:
       - `method_name="uniform"`
       - `statement="Each household in source A is matched to a household in source B with uniform probability — this assumes no correlation between the variables in the two sources."`
       - `details={"table_a_rows": n, "table_b_rows": m, "seed": config.seed, "with_replacement": True, "dropped_right_columns": list(config.drop_right_columns)}`
    8. Return `MergeResult(table=merged, assumption=assumption)`
  - [x]3.5 Use `logging.getLogger(__name__)` with structured `event=merge_start`, `event=merge_complete` log entries including `method=uniform rows_a=... rows_b=... seed=...`

- [x] Task 4: Update `__init__.py` exports (AC: #1)
  - [x]4.1 Export from `src/reformlab/population/methods/__init__.py`: `MergeMethod`, `MergeConfig`, `MergeAssumption`, `MergeResult`, `UniformMergeMethod`, `MergeError`, `MergeValidationError` — define `__all__` listing all exports explicitly (follow `population/loaders/__init__.py` pattern)
  - [x]4.2 Add methods exports to `src/reformlab/population/__init__.py`: same names as 4.1

- [x] Task 5: Create test infrastructure (AC: all)
  - [x]5.1 Create `tests/population/methods/__init__.py`
  - [x]5.2 Create `tests/population/methods/conftest.py` with fixtures:
    - `income_table` — small `pa.Table` with columns: `household_id` (int64), `income` (float64), `region_code` (utf8) — 5 rows
    - `vehicle_table` — small `pa.Table` with columns: `vehicle_type` (utf8), `vehicle_age` (int64), `fuel_type` (utf8) — 8 rows
    - `overlapping_table` — small `pa.Table` with a column name that conflicts with `income_table` (e.g., `region_code`)
    - `empty_table` — `pa.Table` with schema but 0 rows
    - `default_config` — `MergeConfig(seed=42)`

- [x] Task 6: Write comprehensive tests (AC: all)
  - [x]6.1 `tests/population/methods/test_base.py`:
    - `TestMergeConfig`: frozen, `__post_init__` validation (negative seed raises `ValueError`, `bool` seed raises `ValueError`), `drop_right_columns` deep-copied, default values
    - `TestMergeAssumption`: frozen, `details` deep-copied, `to_governance_entry()` returns correct dict with `key`/`value`/`source`/`is_default` fields
    - `TestMergeResult`: frozen, holds table + assumption
    - `TestMergeMethodProtocol`: verify `UniformMergeMethod` passes `isinstance(m, MergeMethod)` check; verify a non-conforming class fails
  - [x]6.2 `tests/population/methods/test_uniform.py`:
    - `TestUniformMergeMethodProtocol`: `isinstance()` check against `MergeMethod`
    - `TestUniformMergeMethodName`: `name` property returns `"uniform"`
    - `TestUniformMergeMethodMerge`:
      - Basic merge: income_table (5 rows) + vehicle_table (8 rows) → merged table with 5 rows and 6 columns (3 from A + 3 from B)
      - Column names: merged table has all columns from both tables
      - Row count: merged table has same row count as table_a
      - Values preserved: all values from table_a are present unchanged in corresponding columns
      - Values from table_b: matched values come from actual rows in table_b (not fabricated)
    - `TestUniformMergeMethodDeterminism`:
      - Same seed → identical merged table (row-by-row comparison)
      - Different seed → different row matching (at least one row differs, verified statistically with high probability for the test fixture sizes)
    - `TestUniformMergeMethodColumnConflict`:
      - Overlapping column names → `MergeValidationError` with exact conflicting names in message
    - `TestUniformMergeMethodDropRightColumns`:
      - `drop_right_columns=("region_code",)` removes `region_code` from right table before merge
      - Invalid `drop_right_columns` with nonexistent column → `MergeValidationError`
    - `TestUniformMergeMethodEmptyTable`:
      - Empty table_a → `MergeValidationError`
      - Empty table_b → `MergeValidationError`
    - `TestUniformMergeMethodAssumption`:
      - `assumption.method_name == "uniform"`
      - `assumption.statement` contains the exact AC #3 text
      - `assumption.details` contains `table_a_rows`, `table_b_rows`, `seed`, `with_replacement`
      - `assumption.to_governance_entry()` returns dict with `key`, `value`, `source`, `is_default` fields
    - `TestUniformMergeMethodWithReplacement`:
      - When table_a has more rows than table_b, merge still works (with replacement)
      - When table_a has fewer rows than table_b, merge still works
      - When table_a and table_b have equal rows, merge still works
    - `TestUniformMergeMethodDocstring`:
      - Class docstring is non-empty
      - Class docstring contains "independence" or "no correlation" (pedagogical content)
  - [x]6.3 `tests/population/methods/test_errors.py`:
    - `TestMergeError`: inherits `Exception`, `summary-reason-fix` message format, attributes accessible
    - `TestMergeValidationError`: inherits `MergeError`

- [x] Task 7: Run full test suite and lint (AC: all)
  - [x]7.1 `uv run pytest tests/population/methods/` — all new tests pass
  - [x]7.2 `uv run pytest tests/population/` — no regressions in loader tests
  - [x]7.3 `uv run ruff check src/reformlab/population/methods/ tests/population/methods/` — no lint errors
  - [x]7.4 `uv run mypy src/reformlab/population/methods/` — no mypy errors (strict mode)

## Dev Notes

### Architecture Context: Statistical Methods Library

This story creates the `src/reformlab/population/methods/` subsystem — the second major component of EPIC-11 (after `loaders/`). The architecture specifies this directory explicitly:

```
src/reformlab/population/
├── loaders/           ← Institutional data source loaders (Stories 11.1–11.3, DONE)
│   ├── base.py        ← DataSourceLoader protocol + CachedLoader
│   ├── cache.py       ← SourceCache
│   ├── errors.py      ← DataSourceError hierarchy
│   ├── insee.py       ← INSEELoader
│   ├── eurostat.py    ← EurostatLoader
│   ├── ademe.py       ← ADEMELoader
│   └── sdes.py        ← SDESLoader
├── methods/           ← Statistical fusion methods library (THIS STORY starts it)
│   ├── __init__.py
│   ├── base.py        ← MergeMethod protocol + MergeConfig + MergeAssumption + MergeResult
│   ├── errors.py      ← MergeError hierarchy
│   └── uniform.py     ← UniformMergeMethod (this story)
│                      ← ipf.py, conditional.py, matching.py added in Story 11.5
├── pipeline.py        ← PopulationPipeline builder (Story 11.6)
├── assumptions.py     ← Assumption recording integration (Story 11.6)
└── validation.py      ← Validate against known marginals (Story 11.7)
```

### Protocol Design Pattern (from DataSourceLoader)

Follow the **exact same protocol pattern** established in `src/reformlab/population/loaders/base.py`:

1. **`@runtime_checkable` Protocol** — enables `isinstance()` checks for structural typing
2. **Frozen dataclasses** for all value objects (`MergeConfig`, `MergeAssumption`, `MergeResult`)
3. **`__post_init__` validation** — validate and deep-copy mutable fields using `object.__setattr__()` pattern
4. **No abstract base classes** — Protocols, not ABCs (per project-context.md)
5. **Subsystem-specific exceptions** — `MergeError` hierarchy, not bare `ValueError` or `Exception`

### MergeMethod Protocol — Exact Specification

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class MergeMethod(Protocol):
    """Interface for statistical dataset fusion methods.

    Structural (duck-typed) protocol: any class that implements
    ``merge()`` and the ``name`` property with the correct signatures
    satisfies the contract — no explicit inheritance required.

    Each method merges two ``pa.Table`` objects using a specific
    statistical approach, returning the merged table and an assumption
    record documenting the methodological choice.
    """

    @property
    def name(self) -> str:
        """Short identifier for this method (e.g., "uniform", "ipf")."""
        ...

    def merge(
        self,
        table_a: pa.Table,
        table_b: pa.Table,
        config: MergeConfig,
    ) -> MergeResult:
        """Merge two tables using this method's statistical approach."""
        ...
```

### MergeConfig — Exact Specification

```python
@dataclass(frozen=True)
class MergeConfig:
    """Immutable configuration for a merge operation.

    Attributes:
        seed: Random seed for deterministic merge operations. Must be >= 0.
        description: Optional human-readable description for governance.
        drop_right_columns: Column names to remove from table_b before
            merging. Use this to remove shared key columns (e.g.,
            "region_code") that exist in both tables but should only
            appear once in the result.
    """

    seed: int
    description: str = ""
    drop_right_columns: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.seed, int) or isinstance(self.seed, bool) or self.seed < 0:
            raise ValueError(
                f"seed must be a non-negative integer, got {self.seed!r}"
            )
        # Deep-copy mutable-origin field
        object.__setattr__(
            self, "drop_right_columns", tuple(self.drop_right_columns)
        )
```

### MergeAssumption — Governance Integration

The `MergeAssumption` must produce records compatible with the existing `governance.manifest.AssumptionEntry` TypedDict (defined in `src/reformlab/governance/manifest.py` lines 60–73):

```python
class AssumptionEntry(TypedDict):
    key: str           # assumption identifier
    value: Any         # JSON-compatible value
    source: str        # e.g., "merge_step", "runtime"
    is_default: bool   # always False for merge assumptions (explicit choice)
```

The `to_governance_entry()` method on `MergeAssumption` bridges the gap:

```python
@dataclass(frozen=True)
class MergeAssumption:
    """Structured assumption record from a merge operation.

    Records the method name, a plain-language assumption statement,
    and method-specific details. Can be converted to governance
    ``AssumptionEntry`` format via ``to_governance_entry()``.
    """

    method_name: str
    statement: str
    details: dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "details", deepcopy(self.details))

    def to_governance_entry(
        self, *, source_label: str = "merge_step"
    ) -> dict[str, Any]:
        """Convert to governance-compatible assumption entry.

        Returns a dict matching ``governance.manifest.AssumptionEntry``
        structure: key, value, source, is_default.
        """
        return {
            "key": f"merge_{self.method_name}",
            "value": {
                **self.details,
                "method": self.method_name,
                "statement": self.statement,
            },
            "source": source_label,
            "is_default": False,
        }
```

**CRITICAL:** The `value` field in the governance entry must be JSON-compatible. The `details` dict must only contain JSON-serializable types (`str`, `int`, `float`, `bool`, `None`, `list`, `dict`). The manifest validation in `RunManifest._validate()` (manifest.py lines 230–265) enforces this. Specifically, `_validate_json_compatible()` (lines 523–552) rejects non-finite floats, bytes, and custom objects.

### UniformMergeMethod — Algorithm Detail

The uniform distribution merge is the simplest statistical matching approach:

**Algorithm:**
1. For each of the N rows in table_a, independently draw a random index from `[0, M)` where M = `table_b.num_rows`
2. Select the corresponding rows from table_b (with replacement — a single row from B can be matched to multiple rows from A)
3. Concatenate columns from table_a and the selected table_b rows — the merged table preserves column ordering: all columns from table_a appear first (in their original order), followed by all columns from table_b (after `drop_right_columns` removal)

**Statistical assumption:** Independence between all variables in table_a and table_b. This means the merge assumes no correlation between, for example, income (from INSEE) and vehicle type (from SDES). This is the weakest assumption — good as a baseline but unrealistic for correlated variables.

**When appropriate:** When merging genuinely independent surveys or when no linking variable is available.
**When problematic:** When variables are correlated (e.g., income and vehicle ownership are correlated — higher-income households are more likely to own newer, more expensive vehicles).

**Implementation pattern:**

```python
import random
import pyarrow as pa

def merge(self, table_a: pa.Table, table_b: pa.Table, config: MergeConfig) -> MergeResult:
    # Validate inputs
    if table_a.num_rows == 0:
        raise MergeValidationError(...)
    if table_b.num_rows == 0:
        raise MergeValidationError(...)

    # Drop specified right columns
    right_table = table_b
    for col in config.drop_right_columns:
        if col not in right_table.schema.names:
            raise MergeValidationError(...)
        col_idx = right_table.schema.get_field_index(col)
        right_table = right_table.remove_column(col_idx)

    # Check column conflicts
    overlap = set(table_a.schema.names) & set(right_table.schema.names)
    if overlap:
        raise MergeValidationError(...)

    # Random matching
    rng = random.Random(config.seed)
    n = table_a.num_rows
    m = right_table.num_rows
    indices = pa.array([rng.randrange(m) for _ in range(n)])
    matched_b = right_table.take(indices)

    # Combine columns
    all_columns: dict[str, pa.Array] = {}
    for name in table_a.schema.names:
        all_columns[name] = table_a.column(name)
    for name in matched_b.schema.names:
        all_columns[name] = matched_b.column(name)
    merged = pa.table(all_columns)

    # Build assumption
    assumption = MergeAssumption(
        method_name="uniform",
        statement=(
            "Each household in source A is matched to a household in "
            "source B with uniform probability \u2014 this assumes no "
            "correlation between the variables in the two sources."
        ),
        details={
            "table_a_rows": n,
            "table_b_rows": m,
            "seed": config.seed,
            "with_replacement": True,
            "dropped_right_columns": list(config.drop_right_columns),
        },
    )

    return MergeResult(table=merged, assumption=assumption)
```

### Error Hierarchy — Follow Loaders Pattern

```python
# src/reformlab/population/methods/errors.py

class MergeError(Exception):
    """Base exception for merge method operations.

    All merge exceptions use keyword-only constructor arguments
    and produce a structured ``summary - reason - fix`` message.
    """

    def __init__(self, *, summary: str, reason: str, fix: str) -> None:
        self.summary = summary
        self.reason = reason
        self.fix = fix
        super().__init__(f"{summary} - {reason} - {fix}")


class MergeValidationError(MergeError):
    """Raised when merge inputs fail validation.

    Triggered by: empty tables, column name conflicts, invalid
    drop_right_columns, or schema mismatches.
    """
```

### No New Dependencies Required

All implementation uses existing dependencies and stdlib:

- `random` — deterministic random number generation (stdlib)
- `pyarrow` — table operations, `take()` for row selection (existing dependency)
- `copy.deepcopy` — immutability for frozen dataclasses (stdlib)
- `logging` — structured logging (stdlib)

Do **not** introduce `numpy`, `scipy`, `pandas`, or any new dependency.

**Import notes:** `from copy import deepcopy` must be at module level in `base.py` (follow `manifest.py:22` pattern — stdlib, no circular dependency risk). `import pyarrow as pa` must be at module level in `uniform.py` (NOT under `if TYPE_CHECKING:`) because `pa.array()` and `pa.table()` are called at runtime. In `base.py`, `pyarrow` may use `TYPE_CHECKING` guard since `pa.Table` is annotation-only.

### Test Fixtures — Concrete Data

```python
# tests/population/methods/conftest.py

@pytest.fixture()
def income_table() -> pa.Table:
    """INSEE-style income table (5 households)."""
    return pa.table({
        "household_id": pa.array([1, 2, 3, 4, 5], type=pa.int64()),
        "income": pa.array([18000.0, 25000.0, 32000.0, 45000.0, 72000.0], type=pa.float64()),
        "region_code": pa.array(["84", "11", "84", "75", "11"], type=pa.utf8()),
    })

@pytest.fixture()
def vehicle_table() -> pa.Table:
    """SDES-style vehicle table (8 vehicles)."""
    return pa.table({
        "vehicle_type": pa.array(
            ["diesel", "essence", "ev", "diesel", "hybrid", "essence", "ev", "diesel"],
            type=pa.utf8(),
        ),
        "vehicle_age": pa.array([3, 7, 1, 12, 2, 9, 0, 15], type=pa.int64()),
        "fuel_type": pa.array(
            ["diesel", "petrol", "electric", "diesel", "hybrid", "petrol", "electric", "diesel"],
            type=pa.utf8(),
        ),
    })

@pytest.fixture()
def overlapping_table() -> pa.Table:
    """Table with column name conflicting with income_table."""
    return pa.table({
        "region_code": pa.array(["84", "11", "75"], type=pa.utf8()),
        "heating_type": pa.array(["gas", "electric", "heat_pump"], type=pa.utf8()),
    })

@pytest.fixture()
def empty_table() -> pa.Table:
    """Table with schema but zero rows."""
    return pa.table({
        "x": pa.array([], type=pa.int64()),
        "y": pa.array([], type=pa.float64()),
    })

@pytest.fixture()
def default_config() -> MergeConfig:
    """Default merge config with seed 42."""
    return MergeConfig(seed=42)
```

### Test Pattern to Follow (from loader tests)

Follow the exact test structure from `tests/population/loaders/test_insee.py`:

1. **Class-based grouping** by feature/responsibility — each test class covers a specific aspect
2. **AC references in class docstrings** — e.g., `"""AC #1, #2: Protocol compliance."""`
3. **Direct assertions** — `assert` statements, `pytest.raises(ExceptionClass, match=...)` for errors
4. **Fixtures via conftest** — injected by parameter name
5. **No test helpers** unless genuinely reusable — keep tests self-contained
6. **Frozen dataclass tests** — verify immutability with `pytest.raises(AttributeError)`

### Downstream Dependencies

Story 11.4 is consumed by:

- **Story 11.5** (IPF + conditional sampling) — adds `IPFMergeMethod` and `ConditionalSamplingMethod` implementing the same `MergeMethod` protocol, using the same `MergeConfig`, `MergeAssumption`, and `MergeResult` types
- **Story 11.6** (PopulationPipeline) — composes loaders + methods, calls `merge()` in sequence, collects `MergeAssumption` records, calls `assumption.to_governance_entry()` on each, and appends the resulting dicts directly to `RunManifest.assumptions` (type: `list[AssumptionEntry]`). Does NOT use `governance.capture.capture_assumptions()` — that function handles scalar key-value parameter assumptions, not structured merge assumption records
- **Story 11.7** (Validation) — validates merged population against marginals
- **Story 11.8** (Notebook) — demonstrates merge methods with plain-language explanations

### Project Structure Notes

**New files (9):**
- `src/reformlab/population/methods/__init__.py`
- `src/reformlab/population/methods/base.py`
- `src/reformlab/population/methods/errors.py`
- `src/reformlab/population/methods/uniform.py`
- `tests/population/methods/__init__.py`
- `tests/population/methods/conftest.py`
- `tests/population/methods/test_base.py`
- `tests/population/methods/test_uniform.py`
- `tests/population/methods/test_errors.py`

**Modified files (1):**
- `src/reformlab/population/__init__.py` — add methods exports

**No changes** to `pyproject.toml` (no new dependencies, no new markers needed)

### Alignment with Project Conventions

All rules from `project-context.md` apply:

- Every file starts with `from __future__ import annotations`
- `if TYPE_CHECKING:` guards for annotation-only imports
- Frozen dataclasses as default (`@dataclass(frozen=True)`)
- Protocols, not ABCs — `@runtime_checkable` Protocol
- Subsystem-specific exceptions (`MergeError`, not `ValueError`)
- `dict[str, Any]` for metadata bags with stable string-constant keys
- `tuple[...]` for immutable sequences in function parameters and return types
- `X | None` union syntax, not `Optional[X]`
- Module-level docstrings referencing story/FR
- `logging.getLogger(__name__)` with structured key=value format
- `# ====...====` section separators for major sections within longer modules

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#New-Subsystem-Population-Generation] — Directory structure, MergeMethod protocol specification
- [Source: _bmad-output/planning-artifacts/architecture.md#External-Data-Caching-&-Offline-Strategy] — Design principles for population subsystem
- [Source: _bmad-output/planning-artifacts/epics.md#BKL-1104] — Story definition and acceptance criteria
- [Source: _bmad-output/planning-artifacts/prd.md#FR38] — "System provides a library of statistical methods for merging datasets that do not share the same sample (uniform distribution, IPF, conditional sampling, statistical matching)"
- [Source: _bmad-output/planning-artifacts/prd.md#FR39] — "Analyst can choose which merge method to apply at each dataset join, with plain-language explanation of the assumption"
- [Source: _bmad-output/project-context.md#Python-Language-Rules] — Frozen dataclasses, Protocols, `from __future__ import annotations`
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules] — PyArrow canonical data type, no pandas in core logic
- [Source: src/reformlab/population/loaders/base.py] — DataSourceLoader Protocol pattern to follow (SourceConfig, CacheStatus frozen dataclasses, `@runtime_checkable`)
- [Source: src/reformlab/population/loaders/errors.py] — DataSourceError hierarchy pattern (summary-reason-fix)
- [Source: src/reformlab/governance/capture.py] — `capture_assumptions()` function signature and AssumptionEntry format
- [Source: src/reformlab/governance/manifest.py#AssumptionEntry] — TypedDict with key/value/source/is_default fields; JSON-compatibility validation
- [Source: tests/population/loaders/test_insee.py] — Test patterns: class-based grouping, fixture injection, direct assertions
- [Source: _bmad-output/implementation-artifacts/11-3-implement-eurostat-ademe-sdes-data-source-loaders.md] — Previous story (loaders pattern reference)

## File List

**New files (9):**
- `src/reformlab/population/methods/__init__.py`
- `src/reformlab/population/methods/base.py`
- `src/reformlab/population/methods/errors.py`
- `src/reformlab/population/methods/uniform.py`
- `tests/population/methods/__init__.py`
- `tests/population/methods/conftest.py`
- `tests/population/methods/test_base.py`
- `tests/population/methods/test_uniform.py`
- `tests/population/methods/test_errors.py`

**Modified files (1):**
- `src/reformlab/population/__init__.py` — added methods exports

## Dev Agent Record

### Implementation Plan

Implemented all 7 tasks following the story spec exactly:

1. Created `methods/` package with `__init__.py` (FR38/FR39 docstring) and `errors.py` (`MergeError` hierarchy with summary-reason-fix pattern).
2. Defined `MergeConfig` (frozen, bool-rejecting seed validation, deep-copied `drop_right_columns`), `MergeAssumption` (deep-copied details, `to_governance_entry()` with key-collision prevention), `MergeResult`, and `MergeMethod` runtime-checkable Protocol in `base.py`.
3. Implemented `UniformMergeMethod` in `uniform.py` with: input validation, `drop_right_columns` removal, column conflict detection, `random.Random(seed)`-based deterministic matching with replacement, `pa.table()` column combination, structured assumption record, and structured logging.
4. Updated both `methods/__init__.py` and `population/__init__.py` with all 7 exports and `__all__`.
5. Created test infrastructure: `conftest.py` with 5 fixtures (`income_table`, `vehicle_table`, `overlapping_table`, `empty_table`, `default_config`).
6. Wrote 50 tests across 3 test files covering: frozen dataclass immutability, `__post_init__` validation, governance entry generation, protocol compliance, merge behavior, determinism, column conflicts, `drop_right_columns`, empty table rejection, assumption record content, with-replacement behavior, and pedagogical docstrings.
7. All 235 population tests pass (50 new + 185 existing), ruff clean, mypy strict clean.

### Completion Notes

- All 4 acceptance criteria satisfied
- `pyarrow` import in `base.py` uses `TYPE_CHECKING` guard (annotation-only); runtime import in `uniform.py`
- `deepcopy` imported at module level in `base.py`
- No new dependencies introduced
- All conventions from `project-context.md` followed

## Change Log

- 2026-03-03: Story created by create-story workflow — comprehensive developer context with MergeMethod protocol design, UniformMergeMethod algorithm, governance integration pattern, error hierarchy, test fixture designs, and downstream dependency mapping.
- 2026-03-03: Validation synthesis — fixed `capture_assumptions()` API reference in Downstream Dependencies, added `bool` rejection to `MergeConfig.seed` validation, fixed `to_governance_entry()` key collision risk, moved `deepcopy` import to module level, added `__all__` requirement, fixed file counts, improved AC#2 wording, documented column ordering contract and import notes.
- 2026-03-03: Implementation complete — all 7 tasks done, 50 new tests passing, 0 regressions, ruff clean, mypy strict clean.


]]></file>
<file id="bca11243" path="_bmad-output/implementation-artifacts/11-5-implement-ipf-and-conditional-sampling-merge-methods.md" label="STORY FILE"><![CDATA[



# Story 11.5: Implement IPF and conditional sampling merge methods

Status: complete

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform developer building the French household population pipeline,
I want IPF (Iterative Proportional Fitting) and conditional sampling merge methods implementing the existing `MergeMethod` protocol,
so that the population pipeline can produce merged populations that respect known marginal distributions (IPF) or leverage shared stratification variables (conditional sampling), enabling more realistic synthetic populations than uniform random matching alone.

## Acceptance Criteria

1. Given two tables and a set of known marginal constraints, when IPF is applied, then the merged population matches the target marginals within documented tolerances (IPF convergence tolerance is `1e-6` at the weight level; after integerization, per-category row counts match targets within ±1).
2. Given IPF output, when the assumption record is inspected, then it lists all marginal constraints used and the convergence status.
3. Given two tables with a conditioning variable (e.g., income bracket), when conditional sampling is applied, then matches are drawn within strata defined by the conditioning variable.
4. Given conditional sampling output, when the assumption record is inspected, then it states the conditioning variable and explains the conditional independence assumption.
5. Given both methods, when docstrings are read, then each includes a plain-language explanation suitable for a policy analyst (not just a statistician).

## Tasks / Subtasks

- [x] Task 1: Define IPF supporting types in `base.py` (AC: #1, #2)
  - [x] 1.1 Add `IPFConstraint` frozen dataclass to `src/reformlab/population/methods/base.py` with fields: `dimension: str` (column name in table_a to constrain), `targets: dict[str, float]` (category value -> target count/weight). Validate in `__post_init__` that `dimension` is a non-empty string and `targets` is non-empty with all values >= 0. Deep-copy `targets` dict via `object.__setattr__`.
  - [x] 1.2 Add `IPFResult` frozen dataclass to `base.py` with fields: `weights: tuple[float, ...]` (per-row IPF weights), `iterations: int` (iterations until convergence), `converged: bool`, `max_deviation: float` (maximum absolute deviation at termination). This captures convergence diagnostics for the assumption record.

- [x] Task 2: Add `MergeConvergenceError` to error hierarchy (AC: #1)
  - [x] 2.1 Add `MergeConvergenceError(MergeError)` to `src/reformlab/population/methods/errors.py` — raised when IPF fails to converge within `max_iterations`. Docstring: "Raised when an iterative merge method fails to converge within the configured iteration limit."

- [x] Task 3: Implement `IPFMergeMethod` — `ipf.py` (AC: #1, #2, #5)
  - [x] 3.1 Create `src/reformlab/population/methods/ipf.py` with module docstring referencing Story 11.5, FR38, FR39 — include pedagogical docstring explaining IPF in plain language:
    - What IPF does: adjusts row weights so that the merged population's marginal distributions match known targets (e.g., census totals by region, income distribution by bracket)
    - The assumption: the joint distribution between unconstrained variables follows the pattern in the seed data (table_a), adjusted only to match the specified marginals. This is a "minimum information" / maximum entropy approach
    - When appropriate: when you have reliable marginal distributions from census or administrative data that the merged population must respect
    - When problematic: when the seed data has structural zeros (categories with no observations) that should have non-zero representation, or when marginal targets are mutually inconsistent (different grand totals)
  - [x] 3.2 Implement `IPFMergeMethod` class with constructor:
    ```python
    def __init__(
        self,
        constraints: tuple[IPFConstraint, ...],
        max_iterations: int = 100,
        tolerance: float = 1e-6,
    ) -> None:
    ```
    Validate: `constraints` must be non-empty tuple, `max_iterations >= 1`, `tolerance > 0`. Store as instance attributes. No frozen dataclass for the method itself (it's a service object, not a value object).
  - [x] 3.3 Implement `name` property returning `"ipf"`
  - [x] 3.4 Implement private `_run_ipf(self, table_a: pa.Table) -> IPFResult` with this algorithm:
    1. Initialize weights: `[1.0] * table_a.num_rows`
    2. Validate constraint dimensions exist as columns in table_a — raise `MergeValidationError` if not
    3. Validate constraint targets: each target category must exist in the column values — log warning for categories not present (they cannot be satisfied), raise `MergeValidationError` if **all** categories in a constraint are missing
    4. IPF iteration loop (up to `max_iterations`):
       a. For each constraint `(dimension, targets)`:
          - Extract column values: `table_a.column(dimension).to_pylist()`
          - Compute current weighted totals per category: `current[cat] = sum(weights[k] for k where col[k] == cat)`
          - Compute adjustment factors: `factor[cat] = target[cat] / current[cat]` (if `current[cat] > 0`, else `factor = 1.0`)
          - Apply factors: `weights[k] *= factor[col[k]]`
       b. Compute max absolute deviation: `max(|current[cat] - target[cat]|)` across all constraints and categories
       c. If `max_deviation < tolerance`: converged = True, break
    5. Return `IPFResult(weights=tuple(weights), iterations=i+1, converged=converged, max_deviation=max_deviation)`
  - [x] 3.5 Implement private `_integerize_weights(self, weights: tuple[float, ...], target_count: int, rng: random.Random) -> list[int]` with this algorithm:
    1. Normalize weights so they sum to `target_count` (= `table_a.num_rows`, preserving original count)
    2. For each weight: `integer_part = floor(weight)`, `fractional = weight - integer_part`
    3. Deterministic probabilistic rounding: if `rng.random() < fractional`, add 1
    4. Return list of integer weights (each >= 0)
  - [x] 3.6 Implement `merge(self, table_a, table_b, config)` with this logic:
    1. Validate inputs: both tables must have `num_rows > 0` — raise `MergeValidationError` (same pattern as uniform)
    2. Apply `config.drop_right_columns` to table_b (same pattern as uniform)
    3. Check column name conflicts (same pattern as uniform)
    4. Run IPF: `ipf_result = self._run_ipf(table_a)`
    5. If not converged: raise `MergeConvergenceError` with summary="IPF did not converge", reason with iterations and max_deviation, fix suggesting increasing max_iterations or checking marginal consistency
    6. Integerize weights: `int_weights = self._integerize_weights(ipf_result.weights, table_a.num_rows, random.Random(config.seed))`
    7. Expand table_a: for each row `k`, repeat it `int_weights[k]` times. Build expanded row indices: `expanded_indices = [k for k, w in enumerate(int_weights) for _ in range(w)]`
    8. Guard: if `len(expanded_indices) == 0`, raise `MergeValidationError` with summary="IPF produced empty expansion", reason="All row weights integerized to 0 — no rows survive expansion", fix="Check constraint targets for extreme values or structural zeros"
    9. Create expanded table_a: `expanded_a = table_a.take(pa.array(expanded_indices))`
    10. Random matching: use `random.Random(config.seed + 1)` (different seed stream from integerization) to generate `expanded_a.num_rows` random indices into table_b (same pattern as uniform)
    11. Select matched rows: `matched_b = right_table.take(pa.array(b_indices))`
    12. Combine columns: same pattern as uniform (table_a columns first, then table_b columns)
    13. Build `MergeAssumption` with:
        - `method_name="ipf"`
        - `statement="The merged population is reweighted using Iterative Proportional Fitting so that marginal distributions match the specified targets — this assumes the joint distribution between unconstrained variables follows the seed pattern, adjusted only to match target marginals."`
        - `details={"table_a_rows": table_a.num_rows, "table_b_rows": table_b.num_rows, "expanded_rows": expanded_a.num_rows, "seed": config.seed, "constraints": [{"dimension": c.dimension, "targets": dict(c.targets)} for c in self._constraints], "iterations": ipf_result.iterations, "converged": ipf_result.converged, "max_deviation": ipf_result.max_deviation, "tolerance": self._tolerance, "dropped_right_columns": list(config.drop_right_columns)}`
    14. Return `MergeResult(table=merged, assumption=assumption)`
  - [x] 3.7 Use `logging.getLogger(__name__)` with structured `event=ipf_start`, `event=ipf_iteration`, `event=ipf_converged`/`event=ipf_not_converged`, `event=merge_start`, `event=merge_complete` log entries

- [x] Task 4: Implement `ConditionalSamplingMethod` — `conditional.py` (AC: #3, #4, #5)
  - [x] 4.1 Create `src/reformlab/population/methods/conditional.py` with module docstring referencing Story 11.5, FR38, FR39 — include pedagogical docstring explaining conditional sampling in plain language:
    - What it does: groups both tables by shared variable(s) (strata), then randomly matches rows only within the same group. This preserves the correlation between the stratification variable and all other variables
    - The assumption: conditional independence — within each stratum, the unique variables from table_a and table_b are assumed independent. The correlation between them is captured entirely by the stratification variable
    - When appropriate: when both datasets share a variable that is correlated with the unique variables in each dataset (e.g., income bracket correlates with both energy consumption and vehicle ownership)
    - When problematic: when the strata are too coarse (residual correlation within strata is large) or when some strata have very few observations in one table (small sample noise)
  - [x] 4.2 Implement `ConditionalSamplingMethod` class with constructor:
    ```python
    def __init__(
        self,
        strata_columns: tuple[str, ...],
    ) -> None:
    ```
    Validate: `strata_columns` must be a non-empty tuple of non-empty strings. Store as instance attribute.
  - [x] 4.3 Implement `name` property returning `"conditional"`
  - [x] 4.4 Implement `merge(self, table_a, table_b, config)` with this logic:
    1. Validate inputs: both tables must have `num_rows > 0` — raise `MergeValidationError`
    2. Validate strata columns exist in BOTH tables — raise `MergeValidationError` listing missing columns and which table they're missing from
    3. Compute effective drop list: `effective_drop = tuple(dict.fromkeys(self._strata_columns + config.drop_right_columns))` to deduplicate (a strata column may also appear in `drop_right_columns`). Remove effective_drop columns from table_b using iterative `remove_column()` (same pattern as uniform.py). Validate each column exists before removal — raise `MergeValidationError` for any `drop_right_columns` entry not found (strata columns are guaranteed present by step 2)
    4. Check column name conflicts on remaining columns (same pattern as uniform)
    5. Build stratum keys: for each row in table_a and table_b, compute a stratum key as a tuple of values from `strata_columns`
    6. Group table_a row indices by stratum: `strata_a: dict[tuple, list[int]]`
    7. Group table_b row indices by stratum: `strata_b: dict[tuple, list[int]]`
    8. Validate coverage: for each stratum present in table_a, check it exists in table_b — raise `MergeValidationError` if any table_a stratum has zero table_b donors (list the empty strata in the error message)
    9. Random matching within strata: `rng = random.Random(config.seed)`. For each stratum, for each table_a row index in that stratum: draw a random index from the table_b row indices in the same stratum (`rng.choice(strata_b[key])`)
    10. Collect all matched (a_idx, b_idx) pairs in original table_a row order
    11. Build merged table: table_a rows (in order) + matched table_b rows (strata columns removed from table_b side)
    12. Build `MergeAssumption` with:
        - `method_name="conditional"`
        - `statement="Rows are matched within strata defined by [{strata_column_list}] — this assumes that, within each stratum, the unique variables from each source are independent (conditional independence given the stratification variables)."`
        - `details={"table_a_rows": n, "table_b_rows": m, "seed": config.seed, "strata_columns": list(self._strata_columns), "strata_count": len(strata_a), "strata_sizes": {"|".join(str(x) for x in key): {"table_a": len(strata_a[key]), "table_b": len(strata_b[key])} for key in strata_a}, "dropped_right_columns": list(effective_drop_columns)}`
    13. Return `MergeResult(table=merged, assumption=assumption)`
  - [x] 4.5 Use `logging.getLogger(__name__)` with structured log entries: `event=merge_start method=conditional`, `event=strata_built strata_count=...`, `event=merge_complete`

- [x] Task 5: Update `__init__.py` exports (AC: all)
  - [x] 5.1 Export from `src/reformlab/population/methods/__init__.py`: add `IPFConstraint`, `IPFResult`, `IPFMergeMethod`, `ConditionalSamplingMethod`, `MergeConvergenceError` — update `__all__` listing
  - [x] 5.2 Export from `src/reformlab/population/__init__.py`: add same names — update `__all__` listing

- [x] Task 6: Create test fixtures for IPF and conditional sampling (AC: all)
  - [x] 6.1 Add to `tests/population/methods/conftest.py`:
    - `region_income_table` — `pa.Table` with columns: `household_id` (int64), `income_bracket` (utf8: "low"/"medium"/"high"), `region_code` (utf8: "84"/"11"/"75") — 10 rows, with known distribution: 3 low, 4 medium, 3 high; 4 region 84, 3 region 11, 3 region 75
    - `energy_vehicle_table` — `pa.Table` with columns: `income_bracket` (utf8), `vehicle_type` (utf8), `energy_kwh` (float64) — 12 rows, covering all 3 income brackets with known distribution
    - `simple_constraints` — `tuple[IPFConstraint, ...]` with one constraint: `IPFConstraint(dimension="income_bracket", targets={"low": 4.0, "medium": 3.0, "high": 3.0})` — shifts distribution from 3/4/3 to 4/3/3
    - `multi_constraints` — `tuple[IPFConstraint, ...]` with two constraints: income_bracket + region_code targets
    - `inconsistent_constraints` — constraints where totals across dimensions don't match (for convergence failure testing)

- [x] Task 7: Write comprehensive IPF tests (AC: #1, #2, #5)
  - [x] 7.1 `tests/population/methods/test_ipf.py`:
    - `TestIPFConstraint`: frozen, `__post_init__` validation (empty dimension raises ValueError, empty targets raises ValueError, negative target raises ValueError), targets deep-copied
    - `TestIPFResult`: frozen, holds weights + convergence diagnostics
    - `TestIPFMergeMethodProtocol`: `isinstance(IPFMergeMethod(...), MergeMethod)` passes
    - `TestIPFMergeMethodName`: `name` property returns `"ipf"`
    - `TestIPFMergeMethodConstructorValidation`: empty constraints raises ValueError, max_iterations < 1 raises ValueError, tolerance <= 0 raises ValueError
    - `TestIPFMergeMethodMerge`:
      - Basic merge with single constraint: region_income_table (10 rows) + vehicle_table → merged table with IPF-adjusted row counts, income_bracket distribution matches target within tolerance
      - Merged table has correct columns (table_a + table_b minus dropped)
      - Values from table_b come from actual rows in table_b (row-level coherence)
    - `TestIPFMergeMethodMarginalMatch`:
      - After merge, count rows per income_bracket → matches targets within tolerance (may differ by ±1 due to integerization)
      - Multi-constraint merge: both income_bracket AND region_code distributions match targets
    - `TestIPFMergeMethodConvergence`:
      - Convergent case: assumption.details contains `converged: True`, `iterations` < max_iterations
      - Non-convergent case: use `IPFMergeMethod(constraints=inconsistent_constraints, max_iterations=100, tolerance=1e-6)` — raises `MergeConvergenceError`
    - `TestIPFMergeMethodDeterminism`:
      - Same seed → identical merged table
      - Different seed → different row matching (at least one row differs)
    - `TestIPFMergeMethodAssumption`:
      - `assumption.method_name == "ipf"`
      - `assumption.statement` contains "Iterative Proportional Fitting" and "marginal"
      - `assumption.details` contains `constraints`, `iterations`, `converged`, `max_deviation`, `tolerance`, `expanded_rows`
      - `assumption.to_governance_entry()` returns correct structure
    - `TestIPFMergeMethodEmptyTable`:
      - Empty table_a → `MergeValidationError`
      - Empty table_b → `MergeValidationError`
    - `TestIPFMergeMethodColumnConflict`:
      - Overlapping columns → `MergeValidationError`
    - `TestIPFMergeMethodDropRightColumns`:
      - `drop_right_columns` works correctly
    - `TestIPFMergeMethodInvalidConstraintDimension`:
      - Constraint dimension not in table_a → `MergeValidationError`
    - `TestIPFMergeMethodMissingCategory`:
      - Constraint has a target category not present in table_a (but at least one IS present): merge completes successfully and a warning is logged (use `caplog` fixture)
    - `TestIPFMergeMethodDocstring`:
      - Class docstring non-empty, mentions "marginal" or "reweight"
      - Module docstring mentions "appropriate" and "problematic"

- [x] Task 8: Write comprehensive conditional sampling tests (AC: #3, #4, #5)
  - [x] 8.1 `tests/population/methods/test_conditional.py`:
    - `TestConditionalSamplingMethodProtocol`: `isinstance(ConditionalSamplingMethod(...), MergeMethod)` passes
    - `TestConditionalSamplingMethodName`: `name` property returns `"conditional"`
    - `TestConditionalSamplingMethodConstructorValidation`: empty strata_columns raises ValueError, empty string in strata_columns raises ValueError
    - `TestConditionalSamplingMethodMerge`:
      - Basic merge with single stratum column ("income_bracket"): region_income_table + energy_vehicle_table → merged table with same row count as table_a
      - All columns from both tables present (minus duplicated strata columns from table_b)
      - Row count equals table_a.num_rows
    - `TestConditionalSamplingMethodStrataRespected`:
      - For each row in merged table, the strata column value matches between the table_a side and the original table_b donor row — i.e., a "low" income household is matched with a "low" income vehicle/energy record
    - `TestConditionalSamplingMethodDeterminism`:
      - Same seed → identical merged table
      - Different seed → different row matching
    - `TestConditionalSamplingMethodColumnConflict`:
      - Overlapping non-strata columns → `MergeValidationError`
    - `TestConditionalSamplingMethodDropRightColumns`:
      - `drop_right_columns` works correctly
      - Strata columns in table_b are auto-dropped (not duplicated in output)
      - When a strata column name also appears in `config.drop_right_columns`, no error is raised (deduplication)
    - `TestConditionalSamplingMethodEmptyTable`:
      - Empty table_a → `MergeValidationError`
      - Empty table_b → `MergeValidationError`
    - `TestConditionalSamplingMethodMissingStrataColumn`:
      - Strata column not in table_a → `MergeValidationError` mentioning which table and column
      - Strata column not in table_b → `MergeValidationError`
    - `TestConditionalSamplingMethodEmptyStratum`:
      - table_a has stratum value "X" but table_b has no rows with "X" → `MergeValidationError` listing the empty stratum
    - `TestConditionalSamplingMethodAssumption`:
      - `assumption.method_name == "conditional"`
      - `assumption.statement` contains "conditional independence" and strata column names
      - `assumption.details` contains `strata_columns`, `strata_count`, `strata_sizes`, `seed`
      - `assumption.to_governance_entry()` returns correct structure
    - `TestConditionalSamplingMethodMultipleStrataColumns`:
      - Merge with 2 strata columns: matching respects both dimensions simultaneously
    - `TestConditionalSamplingMethodDocstring`:
      - Class docstring non-empty, mentions "conditional independence" or "strata"
      - Module docstring mentions "appropriate" and "problematic"

- [x] Task 9: Write tests for new error types and base types (AC: #1, #2)
  - [x] 9.1 Add to `tests/population/methods/test_errors.py`:
    - `TestMergeConvergenceError`: inherits `MergeError`, summary-reason-fix pattern, catchable as `MergeError`
  - [x] 9.2 Add to `tests/population/methods/test_base.py`:
    - `TestIPFConstraint`: frozen, validation, targets deep-copied
    - `TestIPFResult`: frozen, holds convergence diagnostics

- [x] Task 10: Run full test suite and lint (AC: all)
  - [x] 10.1 `uv run pytest tests/population/methods/` — all new tests pass
  - [x] 10.2 `uv run pytest tests/population/` — no regressions in loader or uniform merge tests
  - [x] 10.3 `uv run ruff check src/reformlab/population/methods/ tests/population/methods/` — no lint errors
  - [x] 10.4 `uv run mypy src/reformlab/population/methods/` — no mypy errors (strict mode)

## Dev Notes

### Architecture Context: Methods Library Extension

This story extends the `src/reformlab/population/methods/` subsystem created in Story 11.4. Two new files are added:

```
src/reformlab/population/methods/
├── __init__.py     ← Updated: add new exports
├── base.py         ← Updated: add IPFConstraint, IPFResult
├── errors.py       ← Updated: add MergeConvergenceError
├── uniform.py      ← UNCHANGED (Story 11.4)
├── ipf.py          ← NEW (this story)
└── conditional.py  ← NEW (this story)
```

### Protocol Compliance: Both Methods Follow Existing Pattern

Both `IPFMergeMethod` and `ConditionalSamplingMethod` implement the `MergeMethod` protocol established in Story 11.4 via duck typing (no inheritance). They follow the **exact same patterns** as `UniformMergeMethod`:

1. **`name` property** — returns short identifier (`"ipf"` or `"conditional"`)
2. **`merge(table_a, table_b, config)` signature** — identical to protocol
3. **Same validation order**: empty tables → drop_right_columns → column conflicts → method-specific logic
4. **Same assumption record pattern**: `MergeAssumption(method_name=..., statement=..., details=...)`
5. **Same error hierarchy**: `MergeValidationError` for input issues, `MergeConvergenceError` (new) for IPF non-convergence
6. **Same logging pattern**: `_logger = logging.getLogger(__name__)` with structured key=value events

### Method-Specific Configuration: Constructor Parameters

The `MergeConfig` dataclass is generic (seed, description, drop_right_columns). Method-specific configuration is passed via constructor parameters:

```python
# IPF: constraints and convergence parameters in constructor
ipf = IPFMergeMethod(
    constraints=(
        IPFConstraint(dimension="income_bracket", targets={"low": 4000, "medium": 3000, "high": 3000}),
        IPFConstraint(dimension="region_code", targets={"84": 3500, "11": 3000, "75": 3500}),
    ),
    max_iterations=100,
    tolerance=1e-6,
)
result = ipf.merge(table_a, table_b, MergeConfig(seed=42))

# Conditional: strata columns in constructor
cond = ConditionalSamplingMethod(strata_columns=("income_bracket",))
result = cond.merge(table_a, table_b, MergeConfig(seed=42))
```

This preserves the `MergeMethod` protocol signature while allowing method-specific parameterization.

### IPF Algorithm — Detailed Specification

**Purpose:** Iterative Proportional Fitting (raking) adjusts per-row weights in table_a so that weighted marginal distributions match target values. The reweighted rows are then integerized and matched with table_b rows.

**Algorithm (record-level IPF):**

```
Input: table_a (N rows), constraints [(dimension, {cat: target}), ...]
Output: weights[0..N-1]

1. weights = [1.0, 1.0, ..., 1.0]  (length N)

2. For iteration = 0 to max_iterations - 1:
     max_deviation = 0.0
     For each constraint (dimension, targets):
       col_values = table_a.column(dimension).to_pylist()

       # Compute current weighted totals
       current_totals = {}
       for k in range(N):
           cat = col_values[k]
           current_totals[cat] = current_totals.get(cat, 0.0) + weights[k]

       # Compute and apply adjustment factors
       for cat, target in targets.items():
           current = current_totals.get(cat, 0.0)
           if current > 0:
               factor = target / current
               max_deviation = max(max_deviation, abs(current - target))
           else:
               factor = 1.0
               max_deviation = max(max_deviation, target)
           # Apply factor to all rows in this category
           for k in range(N):
               if col_values[k] == cat:
                   weights[k] *= factor

     If max_deviation < tolerance:
       return IPFResult(weights, iteration+1, converged=True, max_deviation)

3. Return IPFResult(weights, max_iterations, converged=False, max_deviation)
```

**Integerization (controlled probabilistic rounding):**

```
Input: weights (floats summing to ~total), target_count, rng
Output: int_weights (integers summing to ~target_count)

1. scale = target_count / sum(weights)
2. scaled = [w * scale for w in weights]
3. For each scaled weight:
     integer_part = floor(scaled_w)
     fractional = scaled_w - integer_part
     if rng.random() < fractional:
         int_weight = integer_part + 1
     else:
         int_weight = integer_part
4. Return int_weights
```

**Seed stream separation:** The `config.seed` is used for integerization rounding. A derived seed `config.seed + 1` is used for table_b matching. This prevents correlation between the rounding decisions and the matching decisions. Use `random.Random(seed)` for each stream (stdlib, no numpy).

**Performance note:** The IPF loop is O(N * D * I) where N = rows, D = constraint dimensions, I = iterations. For 10,000 rows, 3 dimensions, 50 iterations = 1.5M operations. Pure Python is sufficient for laptop-scale data.

### Conditional Sampling Algorithm — Detailed Specification

**Purpose:** Groups both tables by shared column(s), then performs uniform random matching within each group (stratum). This preserves the correlation between the stratification variable and all other variables.

**Algorithm:**

```
Input: table_a (N rows), table_b (M rows), strata_columns, seed

1. Compute stratum keys for each row:
     key_a[k] = tuple(table_a.column(c)[k] for c in strata_columns)
     key_b[k] = tuple(table_b.column(c)[k] for c in strata_columns)

2. Group row indices by stratum:
     strata_a = {key: [row_indices...]} for each unique key in key_a
     strata_b = {key: [row_indices...]} for each unique key in key_b

3. Validate: for each key in strata_a, key must exist in strata_b
     (raise MergeValidationError if not)

4. Match within strata:
     rng = random.Random(seed)
     matched_b_indices = []
     for k in range(N):
         key = key_a[k]
         donor_pool = strata_b[key]
         matched_b_indices.append(rng.choice(donor_pool))

5. Build right table:
     Compute effective_drop = tuple(dict.fromkeys(strata_columns + config.drop_right_columns))
     Remove effective_drop columns from table_b using iterative remove_column() (same pattern as uniform.py)
     right_table = table_b with effective_drop columns removed
     matched_right = right_table.take(pa.array(matched_b_indices))

6. Combine: table_a columns + matched_right columns
```

**Auto-dropping strata columns from table_b:** Strata columns exist in both tables by definition. To avoid duplicate columns in the output, the method automatically adds strata column names to the effective drop list (in addition to `config.drop_right_columns`). If a strata column is already in `drop_right_columns`, it is not dropped twice.

**Stratum key computation:** Use `tuple(table.column(c)[k].as_py() for c in strata_columns)` to build hashable stratum keys. This works for any column type (utf8, int64, etc.).

### IPFConstraint and IPFResult — Exact Specifications

```python
@dataclass(frozen=True)
class IPFConstraint:
    """A marginal constraint for IPF.

    Specifies that the weighted count of rows where ``dimension``
    equals each category key should match the corresponding target value.

    Attributes:
        dimension: Column name in table_a to constrain.
        targets: Mapping from category value to target count/weight.
            All values must be >= 0.
    """

    dimension: str
    targets: dict[str, float]

    def __post_init__(self) -> None:
        if not self.dimension:
            msg = "dimension must be a non-empty string"
            raise ValueError(msg)
        if not self.targets:
            msg = "targets must be a non-empty dict"
            raise ValueError(msg)
        for cat, val in self.targets.items():
            if val < 0:
                msg = f"target for {cat!r} must be >= 0, got {val}"
                raise ValueError(msg)
        object.__setattr__(self, "targets", dict(self.targets))


@dataclass(frozen=True)
class IPFResult:
    """Convergence diagnostics from an IPF run.

    Attributes:
        weights: Per-row weights after IPF adjustment.
        iterations: Number of iterations performed.
        converged: Whether convergence was reached within tolerance.
        max_deviation: Maximum absolute deviation at termination.
    """

    weights: tuple[float, ...]
    iterations: int
    converged: bool
    max_deviation: float
```

### Error Hierarchy Extension

```python
# Added to src/reformlab/population/methods/errors.py

class MergeConvergenceError(MergeError):
    """Raised when an iterative merge method fails to converge.

    Triggered by: IPF exceeding max_iterations without reaching
    the tolerance threshold. Often caused by inconsistent marginal
    constraints (target totals that cannot be simultaneously satisfied).
    """
```

### No New Dependencies Required

All implementation uses existing dependencies and stdlib:

- `random` — deterministic random number generation (stdlib)
- `math` — `floor()` for integerization (stdlib)
- `pyarrow` — table operations, `take()` for row selection (existing dependency)
- `logging` — structured logging (stdlib)

Do **not** introduce `numpy`, `scipy`, `pandas`, or any new dependency.

**Import pattern:** `import pyarrow as pa` at module level in `ipf.py` and `conditional.py` (runtime dependency, same as `uniform.py`). In `base.py`, `pyarrow` stays under `TYPE_CHECKING` guard.

### Test Fixtures — Concrete Data

```python
# Additional fixtures in tests/population/methods/conftest.py

@pytest.fixture()
def region_income_table() -> pa.Table:
    """Table with known income_bracket and region_code distributions (10 rows).

    Distribution: income_bracket: low=3, medium=4, high=3
                  region_code: 84=4, 11=3, 75=3
    """
    return pa.table({
        "household_id": pa.array(list(range(1, 11)), type=pa.int64()),
        "income_bracket": pa.array(
            ["low", "low", "low", "medium", "medium", "medium", "medium",
             "high", "high", "high"],
            type=pa.utf8(),
        ),
        "region_code": pa.array(
            ["84", "84", "11", "84", "11", "75", "84", "11", "75", "75"],
            type=pa.utf8(),
        ),
    })


@pytest.fixture()
def energy_vehicle_table() -> pa.Table:
    """Table with income_bracket (shared), vehicle_type, energy_kwh (12 rows).

    Covers all 3 income brackets: low=4, medium=4, high=4.
    """
    return pa.table({
        "income_bracket": pa.array(
            ["low", "low", "low", "low",
             "medium", "medium", "medium", "medium",
             "high", "high", "high", "high"],
            type=pa.utf8(),
        ),
        "vehicle_type": pa.array(
            ["diesel", "diesel", "essence", "ev",
             "essence", "hybrid", "ev", "diesel",
             "ev", "ev", "hybrid", "essence"],
            type=pa.utf8(),
        ),
        "energy_kwh": pa.array(
            [8500.0, 9200.0, 7800.0, 3200.0,
             7200.0, 5100.0, 3000.0, 8800.0,
             2800.0, 3100.0, 4900.0, 6500.0],
            type=pa.float64(),
        ),
    })


@pytest.fixture()
def simple_constraints() -> tuple[IPFConstraint, ...]:
    """Single IPF constraint shifting income_bracket distribution."""
    return (
        IPFConstraint(
            dimension="income_bracket",
            targets={"low": 4.0, "medium": 3.0, "high": 3.0},
        ),
    )


@pytest.fixture()
def multi_constraints() -> tuple[IPFConstraint, ...]:
    """Two IPF constraints: income_bracket + region_code."""
    return (
        IPFConstraint(
            dimension="income_bracket",
            targets={"low": 4.0, "medium": 3.0, "high": 3.0},
        ),
        IPFConstraint(
            dimension="region_code",
            targets={"84": 3.0, "11": 4.0, "75": 3.0},
        ),
    )


@pytest.fixture()
def inconsistent_constraints() -> tuple[IPFConstraint, ...]:
    """Two constraints with mismatched grand totals — reliably causes non-convergence.

    income_bracket targets sum to 10 (matches 10-row table).
    region_code targets sum to 30 (3x mismatch forces perpetual oscillation).
    With 100 iterations at tolerance=1e-6, IPF cannot converge.
    """
    return (
        IPFConstraint(
            dimension="income_bracket",
            targets={"low": 4.0, "medium": 3.0, "high": 3.0},
        ),
        IPFConstraint(
            dimension="region_code",
            targets={"84": 10.0, "11": 10.0, "75": 10.0},
        ),
    )
```

### Test Pattern to Follow (from Story 11.4)

Follow the exact test structure from `tests/population/methods/test_uniform.py`:

1. **Class-based grouping** by feature/responsibility
2. **AC references in class docstrings**
3. **Direct assertions** — `assert` statements, `pytest.raises(ExceptionClass, match=...)` for errors
4. **Fixtures via conftest** — injected by parameter name
5. **Frozen dataclass tests** — verify immutability with `pytest.raises(AttributeError)`
6. **Determinism tests** — same seed → identical result, different seed → different
7. **Docstring tests** — verify pedagogical content is present

### IPF Marginal Matching Tolerance in Tests

Due to integerization (probabilistic rounding of fractional weights), the output row counts per category will not match targets exactly. Tests should allow ±1 tolerance:

```python
# Example test pattern for marginal matching
counts = {}
for val in result.table.column("income_bracket").to_pylist():
    counts[val] = counts.get(val, 0) + 1
# Target was {"low": 4.0, "medium": 3.0, "high": 3.0}
assert abs(counts.get("low", 0) - 4) <= 1
assert abs(counts.get("medium", 0) - 3) <= 1
assert abs(counts.get("high", 0) - 3) <= 1
```

### Conditional Sampling: Strata Column Auto-Drop Behavior

The conditional sampling method automatically removes strata columns from the table_b side of the merge to prevent column name conflicts. This is a semantic decision: the strata columns already exist in table_a, so duplicating them would be redundant and would trigger the column conflict check.

The auto-drop is **in addition to** any `config.drop_right_columns` specified by the caller. The effective drop list is the union of both.

### Downstream Dependencies

Story 11.5 is consumed by:

- **Story 11.6** (PopulationPipeline) — composes loaders + methods, calls `merge()` in sequence, collects `MergeAssumption` records
- **Story 11.7** (Validation) — validates merged population against marginals (IPF output should pass validation by construction)
- **Story 11.8** (Notebook) — demonstrates all three merge methods with plain-language explanations, showing progressive improvement from uniform → conditional → IPF

### Project Structure Notes

**New files (4):**
- `src/reformlab/population/methods/ipf.py`
- `src/reformlab/population/methods/conditional.py`
- `tests/population/methods/test_ipf.py`
- `tests/population/methods/test_conditional.py`

**Modified files (7):**
- `src/reformlab/population/methods/base.py` — add `IPFConstraint`, `IPFResult`
- `src/reformlab/population/methods/errors.py` — add `MergeConvergenceError`
- `src/reformlab/population/methods/__init__.py` — add new exports, update `__all__`
- `src/reformlab/population/__init__.py` — add new exports, update `__all__`
- `tests/population/methods/conftest.py` — add new fixtures
- `tests/population/methods/test_base.py` — add `TestIPFConstraint`, `TestIPFResult`
- `tests/population/methods/test_errors.py` — add `TestMergeConvergenceError`

**No changes** to `pyproject.toml` (no new dependencies, no new markers needed)

### Alignment with Project Conventions

All rules from `project-context.md` apply:

- Every file starts with `from __future__ import annotations`
- `if TYPE_CHECKING:` guards for annotation-only imports (in `base.py` only — `ipf.py` and `conditional.py` use `pyarrow` at runtime)
- Frozen dataclasses as default (`@dataclass(frozen=True)`) for `IPFConstraint`, `IPFResult`
- Protocols, not ABCs — new methods satisfy `MergeMethod` protocol via duck typing
- Subsystem-specific exceptions (`MergeConvergenceError`, not bare `Exception`)
- `dict[str, Any]` for metadata bags with stable string-constant keys
- `tuple[...]` for immutable sequences (`IPFConstraint.targets` stored as dict but deep-copied; `IPFResult.weights` as tuple)
- `X | None` union syntax, not `Optional[X]`
- Module-level docstrings referencing story/FR
- `logging.getLogger(__name__)` with structured key=value format
- `# ====...====` section separators for major sections within longer modules

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#New-Subsystem-Population-Generation] — Directory structure, MergeMethod protocol specification
- [Source: _bmad-output/planning-artifacts/epics.md#BKL-1105] — Story definition and acceptance criteria
- [Source: _bmad-output/planning-artifacts/prd.md#FR38] — "System provides a library of statistical methods for merging datasets that do not share the same sample (uniform distribution, IPF, conditional sampling, statistical matching)"
- [Source: _bmad-output/planning-artifacts/prd.md#FR39] — "Analyst can choose which merge method to apply at each dataset join, with plain-language explanation of the assumption"
- [Source: _bmad-output/project-context.md#Python-Language-Rules] — Frozen dataclasses, Protocols, `from __future__ import annotations`
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules] — PyArrow canonical data type, no pandas in core logic
- [Source: src/reformlab/population/methods/base.py] — MergeMethod protocol, MergeConfig, MergeAssumption, MergeResult (Story 11.4)
- [Source: src/reformlab/population/methods/uniform.py] — UniformMergeMethod implementation pattern to follow
- [Source: src/reformlab/population/methods/errors.py] — MergeError hierarchy pattern (summary-reason-fix)
- [Source: src/reformlab/governance/manifest.py#AssumptionEntry] — TypedDict with key/value/source/is_default; JSON-compatibility validation
- [Source: tests/population/methods/test_uniform.py] — Test patterns: class-based grouping, fixture injection, direct assertions
- [Source: tests/population/methods/conftest.py] — Existing test fixtures
- [Source: _bmad-output/implementation-artifacts/11-4-define-mergemethod-protocol-and-uniform-distribution-method.md] — Previous story (protocol reference, implementation patterns)

## File List

**New files (4):**
- `src/reformlab/population/methods/ipf.py`
- `src/reformlab/population/methods/conditional.py`
- `tests/population/methods/test_ipf.py`
- `tests/population/methods/test_conditional.py`

**Modified files (7):**
- `src/reformlab/population/methods/base.py` — add `IPFConstraint`, `IPFResult`
- `src/reformlab/population/methods/errors.py` — add `MergeConvergenceError`
- `src/reformlab/population/methods/__init__.py` — add new exports
- `src/reformlab/population/__init__.py` — add new exports
- `tests/population/methods/conftest.py` — add new fixtures
- `tests/population/methods/test_base.py` — add new type tests
- `tests/population/methods/test_errors.py` — add convergence error tests

## Dev Agent Record

### Implementation Plan

Implemented all 10 tasks in sequence following the story spec exactly:

1. Added `IPFConstraint` and `IPFResult` frozen dataclasses to `base.py` with validation
2. Added `MergeConvergenceError` to error hierarchy in `errors.py`
3. Implemented `IPFMergeMethod` in `ipf.py` — record-level IPF algorithm with weight integerization and seed-stream separation
4. Implemented `ConditionalSamplingMethod` in `conditional.py` — stratum-based matching with auto-drop of strata columns from table_b
5. Updated both `__init__.py` files with new exports
6. Created test fixtures (region_income_table, energy_vehicle_table, simple/multi/inconsistent constraints)
7. Wrote 24 IPF tests covering protocol, name, constructor validation, merge, marginal matching, convergence, determinism, assumptions, empty tables, column conflicts, drop_right_columns, invalid dimensions, missing categories, docstrings
8. Wrote 28 conditional sampling tests covering protocol, name, constructor validation, merge, strata respected, determinism, column conflicts, drop_right_columns (auto-drop + dedup), empty tables, missing strata columns, empty strata, assumptions, multiple strata columns, docstrings
9. Added `TestMergeConvergenceError` (4 tests), `TestIPFConstraint` (7 tests), `TestIPFResult` (3 tests) to existing test files
10. All 122 method tests pass, 307 total population tests pass, ruff clean, mypy strict clean

### Completion Notes

All 5 acceptance criteria satisfied:
- AC #1: IPF matches marginals within ±1 (integerization tolerance), convergence at 1e-6
- AC #2: Assumption record lists all constraints, iterations, convergence status, max_deviation
- AC #3: Conditional sampling matches within strata — verified via row-level coherence tests
- AC #4: Assumption record states conditioning variable and conditional independence assumption
- AC #5: Both module and class docstrings include plain-language explanations with "appropriate"/"problematic" sections

No new dependencies. No changes to pyproject.toml. Both methods follow the exact same patterns as UniformMergeMethod (validation order, error hierarchy, logging, assumption records).

## Change Log

- 2026-03-03: Story created by create-story workflow — comprehensive developer context with IPF algorithm specification (record-level reweighting + integerization + matching), conditional sampling algorithm (stratum-based matching with auto-drop), new supporting types (IPFConstraint, IPFResult, MergeConvergenceError), test fixture designs, downstream dependency mapping, and plain-language pedagogical explanations for both methods.
- 2026-03-03: Story implemented — all 10 tasks complete, 122 tests passing, ruff/mypy clean. 4 new files, 7 modified files.


]]></file>
<file id="99d0a2db" path="_bmad-output/implementation-artifacts/11-6-build-populationpipeline-builder-with-assumption-recording.md" label="STORY FILE"><![CDATA[



# Story 11.6: Build PopulationPipeline builder with assumption recording

Status: complete

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform developer building the French household population pipeline,
I want a composable `PopulationPipeline` builder that chains data source loaders and merge methods with full assumption recording,
so that analysts can build realistic synthetic populations from multiple institutional data sources with transparent, governance-integrated assumption tracking at every merge step, and the full chain from raw data to final population is traceable and auditable.

## Acceptance Criteria

1. Given a sequence of loaders and merge methods, when composed into a `PopulationPipeline`, then the pipeline executes each step in order and produces a final merged population as a `pa.Table`.
2. Given a pipeline execution, when completed, then every merge step's assumption record is captured in governance-compatible format via `MergeAssumption.to_governance_entry()` — the resulting dicts are directly appendable to `RunManifest.assumptions` (NOT passed to `capture_assumptions()`, which takes flat key-value pairs incompatible with structured merge assumptions).
3. Given a pipeline, when inspected after execution, then the full chain of steps is visible: which source → which method → which output, for every merge — including step index, step type, input labels, output row/column counts, method name, and duration.
4. Given a pipeline step that fails (e.g., schema mismatch between two tables), when executed, then the error identifies the exact step index, step label, step type, the two tables involved (by label), and wraps the underlying cause exception.
5. Given a population produced by the pipeline, when its governance record is queried, then all assumption records from all merge steps are retrievable as a `PipelineAssumptionChain` with per-step context (step index, step label) and a single `to_governance_entries()` call produces all entries.

## Tasks / Subtasks

- [x] Task 1: Create `assumptions.py` — assumption recording for governance integration (AC: #2, #5)
  - [x] 1.1 Create `src/reformlab/population/assumptions.py` with module docstring referencing Story 11.6, FR41 — explain the module bridges population pipeline merge assumptions to the governance layer's `RunManifest.assumptions` format.
  - [x] 1.2 Implement `PipelineAssumptionRecord` frozen dataclass:
    ```python
    @dataclass(frozen=True)
    class PipelineAssumptionRecord:
        """Records a single assumption from a pipeline step with execution context.

        Attributes:
            step_index: Zero-based index of the merge step in the pipeline.
            step_label: Human-readable label for the step's output table.
            assumption: The MergeAssumption produced by the merge method.
        """
        step_index: int
        step_label: str
        assumption: MergeAssumption
    ```
    Validate in `__post_init__`: `step_index >= 0`, `step_label` is non-empty string.
  - [x] 1.3 Implement `PipelineAssumptionChain` frozen dataclass:
    ```python
    @dataclass(frozen=True)
    class PipelineAssumptionChain:
        """Complete assumption chain from a pipeline execution.

        Collects all merge assumptions from a pipeline run and provides
        a single method to convert them to governance-compatible format
        for appending to ``RunManifest.assumptions``.

        Attributes:
            records: Ordered tuple of assumption records from each merge step.
            pipeline_description: Human-readable description of the pipeline.
        """
        records: tuple[PipelineAssumptionRecord, ...]
        pipeline_description: str = ""
    ```
    Ensure `records` is a tuple in `__post_init__` via `object.__setattr__(self, "records", tuple(self.records))` — coerces any iterable and prevents external list aliasing. Deep-copy is unnecessary since all contents are frozen dataclasses (and `MergeAssumption.details` is already deep-copied in its own `__post_init__`).
  - [x] 1.4 Implement `PipelineAssumptionChain.to_governance_entries()`:
    ```python
    def to_governance_entries(
        self, *, source_label: str = "population_pipeline"
    ) -> list[dict[str, Any]]:
        """Convert all assumptions to governance-compatible AssumptionEntry format.

        Each entry is a dict with keys: ``key``, ``value``, ``source``, ``is_default``.
        The ``value`` dict includes pipeline step context (step_index, step_label).

        The returned list can be directly appended to ``RunManifest.assumptions``.
        Due to mypy strict mode, callers should use ``cast(AssumptionEntry, entry)``
        when appending to typed manifest fields.
        """
        entries: list[dict[str, Any]] = []
        for record in self.records:
            entry = record.assumption.to_governance_entry(
                source_label=source_label,
            )
            # Enrich with pipeline step context
            entry["value"]["pipeline_step_index"] = record.step_index
            entry["value"]["pipeline_step_label"] = record.step_label
            if self.pipeline_description:
                entry["value"]["pipeline_description"] = self.pipeline_description
            entries.append(entry)
        return entries
    ```
    **Note on key uniqueness:** The `key` field is `merge_{method_name}` inherited from `MergeAssumption.to_governance_entry()`. When the same method is used multiple times (e.g., two uniform merges), multiple entries share the same `key` — this is intentional and accepted by `RunManifest` validation, which does not enforce key uniqueness. Downstream consumers should use `pipeline_step_index` within each entry's `value` to distinguish entries.
  - [x] 1.5 Implement `PipelineAssumptionChain.__len__()` returning `len(self.records)` for convenience.
  - [x] 1.6 Implement `PipelineAssumptionChain.__iter__()` returning `iter(self.records)` for iteration.

- [x] Task 2: Create pipeline error hierarchy in `pipeline.py` (AC: #4)
  - [x] 2.1 Define `PipelineError(Exception)` base with keyword-only `summary`, `reason`, `fix` arguments following the same pattern as `MergeError` and `DataSourceError`:
    ```python
    class PipelineError(Exception):
        """Base exception for population pipeline operations."""
        def __init__(self, *, summary: str, reason: str, fix: str) -> None:
            self.summary = summary
            self.reason = reason
            self.fix = fix
            super().__init__(f"{summary} - {reason} - {fix}")
    ```
  - [x] 2.2 Define `PipelineConfigError(PipelineError)` — raised for invalid pipeline configuration (duplicate labels, missing references, empty pipeline).
  - [x] 2.3 Define `PipelineExecutionError(PipelineError)` — raised when a pipeline step fails during execution. Additional attributes:
    ```python
    class PipelineExecutionError(PipelineError):
        """Raised when a pipeline step fails during execution.

        Wraps the underlying cause and adds step context so the analyst
        can identify exactly which step, which tables, and which error
        caused the failure.
        """
        def __init__(
            self,
            *,
            summary: str,
            reason: str,
            fix: str,
            step_index: int,
            step_label: str,
            step_type: str,
            cause: Exception,
            tables_involved: tuple[str, ...] = (),
        ) -> None:
            self.step_index = step_index
            self.step_label = step_label
            self.step_type = step_type
            self.cause = cause
            self.tables_involved = tables_involved
            super().__init__(summary=summary, reason=reason, fix=fix)
    ```

- [x] Task 3: Define pipeline step types in `pipeline.py` (AC: #1, #3)
  - [x] 3.1 Create `src/reformlab/population/pipeline.py` with module docstring referencing Story 11.6, FR40, FR41 — explain the module provides a composable builder for constructing populations from multiple institutional data sources using statistical merge methods.
  - [x] 3.2 Implement `PipelineStepLog` frozen dataclass — records the outcome of a completed step:
    ```python
    @dataclass(frozen=True)
    class PipelineStepLog:
        """Log entry for a completed pipeline step.

        Records the outcome of each step for traceability (AC #3).

        Attributes:
            step_index: Zero-based position in execution order.
            step_type: Either ``"load"`` or ``"merge"``.
            label: Human-readable label for this step's output.
            input_labels: Empty tuple for load steps; ``(left, right)`` for merge steps.
            output_rows: Number of rows in the step's output table.
            output_columns: Column names in the step's output table.
            method_name: Merge method name (``None`` for load steps).
            duration_ms: Execution time in milliseconds.
        """
        step_index: int
        step_type: str
        label: str
        input_labels: tuple[str, ...]
        output_rows: int
        output_columns: tuple[str, ...]
        method_name: str | None
        duration_ms: float
    ```
  - [x] 3.3 Implement `PipelineResult` frozen dataclass — immutable result of pipeline execution:
    ```python
    @dataclass(frozen=True)
    class PipelineResult:
        """Immutable result of a population pipeline execution.

        Attributes:
            table: The final merged population table.
            assumption_chain: All merge assumptions with step context.
            step_log: Ordered log of all completed steps.
        """
        table: pa.Table
        assumption_chain: PipelineAssumptionChain
        step_log: tuple[PipelineStepLog, ...]
    ```

- [x] Task 4: Implement `PopulationPipeline` builder class (AC: #1, #3, #4)
  - [x] 4.1 Implement `PopulationPipeline.__init__()`:
    ```python
    class PopulationPipeline:
        """Composable builder for population generation pipelines.

        Provides a fluent API for chaining data source loading and
        statistical merging operations. Each step produces a labeled
        intermediate table. The final population is the output of
        the last merge step.

        The pipeline records every merge step's assumption for
        governance integration via ``PipelineAssumptionChain``.
        """
        def __init__(self, *, description: str = "") -> None:
            self._description = description
            self._steps: list[_PipelineStepDef] = []
            self._labels: set[str] = set()
    ```
    where `_PipelineStepDef` is a union type (see 4.2).
  - [x] 4.2 Define internal step definition types (NOT public API — prefixed with `_`):
    ```python
    @dataclass(frozen=True)
    class _LoadStepDef:
        label: str
        loader: DataSourceLoader
        config: SourceConfig

    @dataclass(frozen=True)
    class _MergeStepDef:
        label: str
        left_label: str
        right_label: str
        method: MergeMethod
        config: MergeConfig

    _PipelineStepDef = _LoadStepDef | _MergeStepDef
    ```
  - [x] 4.3 Implement `add_source(self, label, loader, config) -> PopulationPipeline` (fluent API):
    - Validate `label` is non-empty string — raise `PipelineConfigError` if not
    - Validate `label` is unique (not in `self._labels`) — raise `PipelineConfigError` if duplicate
    - Append `_LoadStepDef` to `self._steps`
    - Add `label` to `self._labels`
    - Return `self` (fluent)
  - [x] 4.4 Implement `add_merge(self, label, left, right, method, config) -> PopulationPipeline` (fluent API):
    - Validate `label` is non-empty string — raise `PipelineConfigError`
    - Validate `label` is unique — raise `PipelineConfigError`
    - Validate `left` exists in `self._labels` — raise `PipelineConfigError` with message identifying the missing label
    - Validate `right` exists in `self._labels` — raise `PipelineConfigError`
    - Validate `left != right` — raise `PipelineConfigError`
    - Append `_MergeStepDef` to `self._steps`
    - Add `label` to `self._labels`
    - Return `self` (fluent)
  - [x] 4.5 Implement `execute(self) -> PipelineResult`:
    - Validate pipeline has at least one merge step — raise `PipelineConfigError` if only load steps
    - Initialize: `tables: dict[str, pa.Table] = {}`, `assumptions: list[PipelineAssumptionRecord] = []`, `step_logs: list[PipelineStepLog] = []`, `step_index = 0`
    - Iterate through `self._steps` in insertion order:
      - For `_LoadStepDef`:
        a. Record `start_time = time.monotonic()`
        b. Call `step.loader.download(step.config)` inside try/except
        c. On success: store `tables[step.label] = table`
        d. On failure: raise `PipelineExecutionError` wrapping the cause, with `step_type="load"`, `step_label=step.label`, `step_index=step_index`
        e. Record `PipelineStepLog` with `step_type="load"`, `input_labels=()`, `method_name=None`, `duration_ms`, `output_rows`, `output_columns`
        f. Increment `step_index`
      - For `_MergeStepDef`:
        a. Record `start_time`
        b. Retrieve `table_a = tables[step.left_label]` and `table_b = tables[step.right_label]`
        c. Call `step.method.merge(table_a, table_b, step.config)` inside try/except
        d. On success: store `tables[step.label] = result.table`, append `PipelineAssumptionRecord(step_index=step_index, step_label=step.label, assumption=result.assumption)` to assumptions
        e. On failure: raise `PipelineExecutionError` wrapping the cause, with `step_type="merge"`, `step_label=step.label`, `step_index=step_index`, `tables_involved=(step.left_label, step.right_label)`
        f. Record `PipelineStepLog` with `step_type="merge"`, `input_labels=(step.left_label, step.right_label)`, `method_name=step.method.name`, `duration_ms`, `output_rows`, `output_columns`
        g. Increment `step_index`
    - Determine final table: scan `self._steps` to find the last `_MergeStepDef` in insertion order and use `tables[last_merge_step.label]`. Do NOT use `self._steps[-1].label` — load steps may follow the last merge.
    - Build `PipelineAssumptionChain` from collected assumptions
    - Return `PipelineResult(table=final_table, assumption_chain=chain, step_log=tuple(step_logs))`
    - **mypy strict note:** Use `isinstance(step, _LoadStepDef)` / `isinstance(step, _MergeStepDef)` to narrow the `_PipelineStepDef` union in the loop — required for mypy strict to access type-specific attributes.
  - [x] 4.6 Implement `step_count` property returning `len(self._steps)`
  - [x] 4.7 Implement `labels` property returning `frozenset(self._labels)` for inspection
  - [x] 4.8 Use `logging.getLogger(__name__)` with structured log entries:
    - `event=pipeline_execute_start steps={n} description={desc}`
    - `event=pipeline_step_start step_index={i} step_type={type} label={label}`
    - `event=pipeline_step_complete step_index={i} label={label} rows={n} cols={n} duration_ms={d}`
    - `event=pipeline_step_error step_index={i} label={label} error={type}`
    - `event=pipeline_execute_complete total_steps={n} final_rows={n} assumptions={n} duration_ms={d}`

- [x] Task 5: Update `__init__.py` exports (AC: all)
  - [x] 5.1 Export from `src/reformlab/population/__init__.py`: add `PopulationPipeline`, `PipelineResult`, `PipelineStepLog`, `PipelineAssumptionChain`, `PipelineAssumptionRecord`, `PipelineError`, `PipelineConfigError`, `PipelineExecutionError` — update `__all__` listing.

- [x] Task 6: Create test fixtures for pipeline tests (AC: all)
  - [x] 6.1 Add to `tests/population/conftest.py`:
    - `mock_loader_a` — a minimal object satisfying `DataSourceLoader` protocol that returns a fixed `pa.Table` with columns: `household_id` (int64), `income` (float64), `region_code` (utf8) — 5 rows. Uses a `_MockLoader` class with `download()` returning the table, `status()` returning a minimal `CacheStatus`, `schema()` returning the table's schema.
    - `mock_loader_b` — returns a table with columns: `vehicle_type` (utf8), `vehicle_age` (int64), `fuel_type` (utf8) — 8 rows.
    - `mock_loader_c` — returns a table with columns: `income_bracket` (utf8), `heating_type` (utf8), `energy_kwh` (float64) — 6 rows.
    - `mock_loader_shared` — returns a table with columns: `income_bracket` (utf8), `vehicle_type` (utf8), `energy_kwh` (float64) — 12 rows. (Same as `energy_vehicle_table` from methods conftest, for conditional sampling.)
    - `mock_failing_loader` — a mock loader whose `download()` raises `DataSourceDownloadError`.
    - `mock_source_config_a`, `mock_source_config_b`, `mock_source_config_c`, `mock_source_config_shared` — `SourceConfig` instances for each mock loader. Example:
      ```python
      @pytest.fixture()
      def mock_source_config_a() -> SourceConfig:
          return SourceConfig(provider="mock", dataset_id="income", url="mock://income")
      ```
      Use `provider="mock"` and `url="mock://{name}"` for all mock configs.

- [x] Task 7: Write comprehensive pipeline tests (AC: #1, #3, #4)
  - [x] 7.1 `tests/population/test_pipeline.py`:
    - `TestPipelineStepLog`: frozen, holds all fields, `step_type` is "load" or "merge"
    - `TestPipelineResult`: frozen, holds table + assumption_chain + step_log
    - `TestPipelineErrorHierarchy`:
      - `PipelineError` inherits `Exception`, summary-reason-fix pattern
      - `PipelineConfigError` inherits `PipelineError`
      - `PipelineExecutionError` inherits `PipelineError`, has `step_index`, `step_label`, `step_type`, `cause`, `tables_involved`
    - `TestPopulationPipelineConstruction`:
      - Constructor accepts optional `description`
      - `step_count` starts at 0
      - `labels` starts empty
    - `TestPopulationPipelineAddSource`:
      - Adds source, label appears in `labels`, `step_count` increments
      - Fluent API: `add_source()` returns `self`
      - Empty label raises `PipelineConfigError`
      - Duplicate label raises `PipelineConfigError`
    - `TestPopulationPipelineAddMerge`:
      - After adding two sources, can add a merge referencing them
      - Fluent API: `add_merge()` returns `self`
      - Missing left label raises `PipelineConfigError`
      - Missing right label raises `PipelineConfigError`
      - Same left and right label raises `PipelineConfigError`
      - Empty label raises `PipelineConfigError`
      - Duplicate label raises `PipelineConfigError`
    - `TestPopulationPipelineExecuteBasic`:
      - Two sources + one uniform merge → result table has correct row count (= table_a rows) and correct columns (all from A + all from B)
      - `result.step_log` has 3 entries (2 loads + 1 merge)
      - Load step logs have `step_type="load"`, `method_name=None`, `input_labels=()`
      - Merge step log has `step_type="merge"`, `method_name="uniform"`, `input_labels=(left, right)`
      - All step logs have `output_rows > 0`, `output_columns` non-empty, `duration_ms >= 0`
    - `TestPopulationPipelineExecuteMultiMerge`:
      - Three sources + two merges (A+B→AB, AB+C→final) → result table has columns from all three sources
      - `result.step_log` has 5 entries
      - `result.assumption_chain` has 2 records (one per merge)
    - `TestPopulationPipelineExecuteWithConditionalSampling`:
      - Source A (with `income_bracket`) + source B (with `income_bracket`) → conditional merge → strata respected in output
    - `TestPopulationPipelineExecuteWithIPF`:
      - Source A (with `income_bracket`) + source B → IPF merge with marginal constraints → result marginals match within ±1
    - `TestPopulationPipelineExecuteDeterminism`:
      - Same pipeline configuration → identical result
      - Different seed in merge config → different result
    - `TestPopulationPipelineExecuteNoMerge`:
      - Pipeline with only load steps (no merges) → `PipelineConfigError` on execute
    - `TestPopulationPipelineExecuteLoadFailure`:
      - Pipeline with a failing loader → `PipelineExecutionError` with correct `step_index`, `step_label`, `step_type="load"`, wraps original exception
    - `TestPopulationPipelineExecuteMergeFailure`:
      - Pipeline with intentionally conflicting column names (no drop_right_columns) → `PipelineExecutionError` with correct `step_index`, `step_label`, `step_type="merge"`, `tables_involved` includes both labels, wraps `MergeValidationError`
    - `TestPopulationPipelineExecuteLoadAfterMerge`:
      - Pipeline with a load step added after the last merge → final table is still the last merge output, not the post-merge load
      - Verify `result.table.num_columns` matches merged columns, not the extra load's columns
    - `TestPopulationPipelineExecuteStepOrder`:
      - Steps execute in insertion order: verify via step_log indices matching insertion order
    - `TestPopulationPipelineFluentAPI`:
      - Full fluent chain: `PopulationPipeline().add_source(...).add_source(...).add_merge(...).execute()` works

- [x] Task 8: Write comprehensive assumption tests (AC: #2, #5)
  - [x] 8.1 `tests/population/test_assumptions.py`:
    - `TestPipelineAssumptionRecord`:
      - Frozen dataclass
      - Holds `step_index`, `step_label`, `assumption`
      - Negative `step_index` raises `ValueError`
      - Empty `step_label` raises `ValueError`
    - `TestPipelineAssumptionChain`:
      - Frozen dataclass
      - Empty records tuple is valid (no merge steps = no assumptions)
      - `len()` returns record count
      - Iterable over records
      - `pipeline_description` defaults to empty string
    - `TestPipelineAssumptionChainGovernanceEntries`:
      - Given chain with 2 records, `to_governance_entries()` returns 2 dicts
      - Each dict has `key`, `value`, `source`, `is_default` fields
      - `is_default` is `False` for all entries
      - Default `source` is `"population_pipeline"`
      - Custom `source_label` is respected
      - Each entry's `value` dict contains `pipeline_step_index` and `pipeline_step_label`
      - When `pipeline_description` is set, it appears in each entry's `value`
      - Entries are ordered by step_index
      - Each entry's `key` matches `merge_{method_name}` pattern
    - `TestPipelineAssumptionChainIntegrationWithManifest`:
      - Given governance entries from a chain, when validated against `RunManifest` assumptions schema, then all entries pass validation (key is non-empty string, value is JSON-compatible, source is non-empty string, is_default is bool)
      - **Setup pattern:** Construct a minimal `RunManifest` with the pipeline entries as assumptions. Reference `tests/governance/conftest.py:minimal_manifest` for required fields. Use `cast(AssumptionEntry, entry)` for mypy strict:
        ```python
        from typing import cast
        from reformlab.governance.manifest import AssumptionEntry, RunManifest
        manifest = RunManifest(
            manifest_id="test-pipeline-001",
            created_at="2026-01-01T00:00:00Z",
            engine_version="0.1.0",
            openfisca_version="44.0.0",
            adapter_version="1.0.0",
            scenario_version="v1",
            assumptions=[cast(AssumptionEntry, e) for e in governance_entries],
        )
        ```
    - `TestPipelineResultAssumptionAccess`:
      - Given a `PipelineResult`, `result.assumption_chain.records` is accessible
      - `result.assumption_chain.to_governance_entries()` works end-to-end

- [x] Task 9: Run full test suite and lint (AC: all)
  - [x] 9.1 `uv run pytest tests/population/test_pipeline.py tests/population/test_assumptions.py` — all new tests pass
  - [x] 9.2 `uv run pytest tests/population/` — no regressions in loader or method tests
  - [x] 9.3 `uv run ruff check src/reformlab/population/ tests/population/` — no lint errors
  - [x] 9.4 `uv run mypy src/reformlab/population/` — no mypy errors (strict mode)

## Dev Notes

### Architecture Context: Pipeline Layer

This story creates the **composition layer** that connects the data source loaders (Stories 11.1–11.3) with the statistical merge methods (Stories 11.4–11.5). Two new files are added at the population module level:

```
src/reformlab/population/
├── __init__.py        ← Updated: add new exports
├── assumptions.py     ← NEW (this story) — governance bridge
├── pipeline.py        ← NEW (this story) — builder + execution
├── loaders/           ← UNCHANGED (Stories 11.1–11.3)
│   ├── base.py
│   ├── cache.py
│   ├── insee.py
│   ├── eurostat.py
│   ├── ademe.py
│   └── sdes.py
├── methods/           ← UNCHANGED (Stories 11.4–11.5)
│   ├── base.py
│   ├── uniform.py
│   ├── ipf.py
│   └── conditional.py
└── validation.py      ← NOT YET CREATED (Story 11.7)
```

### Design Pattern: Fluent Builder with Immutable Result

The pipeline follows a **builder pattern**: mutable `PopulationPipeline` accumulates steps via fluent `add_source()` / `add_merge()` calls, then `execute()` produces an immutable `PipelineResult`. This matches existing codebase patterns:

- **Orchestrator analogy:** `OrchestratorConfig.step_pipeline` is a tuple of steps built up, then executed. The pipeline builder is similar but for data composition rather than yearly simulation.
- **DatasetRegistry analogy:** `DatasetRegistry` is mutable (append-only), while `DatasetManifest` is frozen. The pipeline builder is mutable, while `PipelineResult` and `PipelineAssumptionChain` are frozen.

### Governance Integration: NOT via `capture_assumptions()`

**CRITICAL:** The governance integration uses `MergeAssumption.to_governance_entry()` which produces dicts matching the `AssumptionEntry` TypedDict format (`key`, `value`, `source`, `is_default`). These dicts are **appended directly** to `RunManifest.assumptions`.

Do **NOT** use `capture_assumptions()` from `governance/capture.py` — that function takes flat `dict[str, Any]` key-value pairs (e.g., `{"discount_rate": 0.03}`) and produces assumption entries from defaults/overrides. It is incompatible with the structured merge assumption records which have nested `value` dicts containing method details, constraints, convergence diagnostics, etc.

The bridge works as follows:
```python
# In caller code (e.g., Story 11.8 notebook or future orchestrator)
pipeline_result = pipeline.execute()
governance_entries = pipeline_result.assumption_chain.to_governance_entries()
# governance_entries is list[dict[str, Any]] matching AssumptionEntry format
# Append to RunManifest.assumptions when building the manifest
```

### Pipeline Execution Model: Sequential DAG

Steps are added in insertion order. Load steps produce labeled tables stored in an internal `dict[str, pa.Table]`. Merge steps reference previously-produced labels by name. Execution follows insertion order — the user must add sources before merge steps that reference them.

**Example pipeline:**
```python
pipeline = (
    PopulationPipeline(description="French household population 2024")
    .add_source("income", loader=insee_loader, config=insee_config)
    .add_source("vehicles", loader=sdes_loader, config=sdes_config)
    .add_merge(
        "income_vehicles",
        left="income", right="vehicles",
        method=ConditionalSamplingMethod(strata_columns=("income_bracket",)),
        config=MergeConfig(seed=42, drop_right_columns=("income_bracket",)),
    )
    .add_source("energy", loader=ademe_loader, config=ademe_config)
    .add_merge(
        "population",
        left="income_vehicles", right="energy",
        method=UniformMergeMethod(),
        config=MergeConfig(seed=43),
    )
)
result = pipeline.execute()
# result.table → final merged population (pa.Table)
# result.assumption_chain → 2 assumptions (one per merge)
# result.step_log → 5 entries (3 loads + 2 merges)
```

The output is always the table produced by the **last merge step** in insertion order. This is natural: the pipeline progressively enriches the population by merging in new sources.

### Error Hierarchy Placement

Pipeline errors (`PipelineError`, `PipelineConfigError`, `PipelineExecutionError`) live in `pipeline.py` rather than a separate `errors.py`. This is intentional: `loaders/` and `methods/` are multi-file subpackages where a dedicated `errors.py` reduces coupling between sibling modules. The pipeline layer is a single-file module (`pipeline.py`) at the population package level — a separate `errors.py` alongside it would add a file for three small classes that are only used by `pipeline.py` itself.

### Error Handling: Step Context Preservation

When a step fails, `PipelineExecutionError` wraps the underlying exception and adds:
- `step_index` — which step failed (zero-based)
- `step_label` — the label of the failing step
- `step_type` — `"load"` or `"merge"`
- `cause` — the original exception (e.g., `MergeValidationError`, `DataSourceDownloadError`)
- `tables_involved` — tuple of label names (empty for load, `(left, right)` for merge)

This fulfills AC #4: the analyst can identify exactly what went wrong and where.

**Error propagation pattern:**
```python
try:
    merge_result = step.method.merge(table_a, table_b, step.config)
except (MergeValidationError, MergeConvergenceError, MergeError) as exc:
    raise PipelineExecutionError(
        summary=f"Pipeline step {step_index} failed",
        reason=f"Merge step {step.label!r} failed: {exc.summary}",
        fix=exc.fix,
        step_index=step_index,
        step_label=step.label,
        step_type="merge",
        cause=exc,
        tables_involved=(step.left_label, step.right_label),
    ) from exc
```

For load step failures:
```python
try:
    table = step.loader.download(step.config)
except Exception as exc:
    raise PipelineExecutionError(
        summary=f"Pipeline step {step_index} failed",
        reason=f"Load step {step.label!r} failed: {exc}",
        fix="Check data source availability, cache status, and network connectivity",
        step_index=step_index,
        step_label=step.label,
        step_type="load",
        cause=exc,
    ) from exc
```

### Internal Step Definition Types

See Task 4.2 for `_LoadStepDef`, `_MergeStepDef`, `_PipelineStepDef`. These are NOT part of the public API — prefixed with `_`.

### Timing Measurement

Use `time.monotonic()` for step duration measurement (not `time.time()` which is affected by system clock adjustments):

```python
import time

start = time.monotonic()
# ... step execution ...
duration_ms = (time.monotonic() - start) * 1000.0
```

### No New Dependencies Required

All implementation uses existing dependencies and stdlib:

- `time` — monotonic clock for duration measurement (stdlib)
- `dataclasses` — frozen dataclasses (stdlib)
- `logging` — structured logging (stdlib)
- `pyarrow` — `pa.Table` (existing dependency)

Import patterns:
- `pyarrow` imported at runtime in `pipeline.py` (same as merge methods)
- `pyarrow` under `TYPE_CHECKING` guard in `assumptions.py` (only used in `PipelineResult` type, which is in `pipeline.py`)
- Actually, `assumptions.py` doesn't need pyarrow at all — it only references `MergeAssumption` from `methods/base.py`

### Test Fixtures: Mock Loaders

Tests must NOT use real data source loaders (no network, no cache). Instead, use mock loaders that satisfy the `DataSourceLoader` protocol:

```python
class _MockLoader:
    """Minimal DataSourceLoader for pipeline testing."""

    def __init__(self, table: pa.Table) -> None:
        self._table = table

    def download(self, config: SourceConfig) -> pa.Table:
        return self._table

    def status(self, config: SourceConfig) -> CacheStatus:
        return CacheStatus(
            cached=True,
            path=None,
            downloaded_at=None,
            hash=None,
            stale=False,
        )

    def schema(self) -> pa.Schema:
        return self._table.schema


class _FailingLoader:
    """Mock loader that always raises on download."""

    def download(self, config: SourceConfig) -> pa.Table:
        raise DataSourceDownloadError(
            summary="Download failed",
            reason="mock failure for testing",
            fix="this is a test mock",
        )

    def status(self, config: SourceConfig) -> CacheStatus:
        return CacheStatus(
            cached=False, path=None, downloaded_at=None, hash=None, stale=False,
        )

    def schema(self) -> pa.Schema:
        return pa.schema([])
```

### AssumptionEntry Validation Compatibility

The `RunManifest._validate()` method (in `governance/manifest.py`) validates each assumption entry for:
- `key`: non-empty string
- `value`: JSON-compatible (str, int, float, bool, None, list, dict — validated recursively)
- `source`: non-empty string
- `is_default`: boolean

The `to_governance_entries()` output must satisfy all these constraints. The existing `MergeAssumption.to_governance_entry()` already produces valid entries. The pipeline enrichment (adding `pipeline_step_index` and `pipeline_step_label` to the `value` dict) uses `int` and `str` — both JSON-compatible.

### Downstream Dependencies

Story 11.6 is consumed by:

- **Story 11.7** (Validation) — validates a population produced by the pipeline against known marginals. May receive a `PipelineResult.table` and check distributions.
- **Story 11.8** (Notebook) — demonstrates the full pipeline end-to-end: load real INSEE/SDES/ADEME data, compose with merge methods, show assumption chain, produce French household population. Uses `PipelineAssumptionChain.to_governance_entries()` for manifest integration.

### Project Structure Notes

**New files (4):**
- `src/reformlab/population/pipeline.py`
- `src/reformlab/population/assumptions.py`
- `tests/population/test_pipeline.py`
- `tests/population/test_assumptions.py`

**Modified files (2):**
- `src/reformlab/population/__init__.py` — add new exports, update `__all__`
- `tests/population/conftest.py` — add mock loader fixtures and source configs

**No changes** to `pyproject.toml` (no new dependencies)

### Alignment with Project Conventions

All rules from `project-context.md` apply:

- Every file starts with `from __future__ import annotations`
- `if TYPE_CHECKING:` guards for annotation-only imports (in `assumptions.py` — no runtime pyarrow needed)
- Frozen dataclasses as default (`@dataclass(frozen=True)`) for all value types: `PipelineStepLog`, `PipelineResult`, `PipelineAssumptionRecord`, `PipelineAssumptionChain`, `_LoadStepDef`, `_MergeStepDef`
- `PopulationPipeline` is a mutable builder class — NOT a frozen dataclass (it accumulates steps)
- Protocols, not ABCs — pipeline accepts any `DataSourceLoader` and `MergeMethod` via duck typing
- Subsystem-specific exceptions (`PipelineError` hierarchy, not bare `Exception`)
- `dict[str, Any]` for metadata bags
- `tuple[...]` for immutable sequences (step_log, records, output_columns)
- `X | None` union syntax
- Module-level docstrings referencing story/FR
- `logging.getLogger(__name__)` with structured key=value format
- `# ====...====` section separators for major sections within longer modules

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#New-Subsystem-Population-Generation] — Directory structure, pipeline.py and assumptions.py placement
- [Source: _bmad-output/planning-artifacts/epics.md#BKL-1106] — Story definition and acceptance criteria
- [Source: _bmad-output/planning-artifacts/prd.md#FR40] — "System produces a complete synthetic population with household-level attributes sufficient for policy simulation"
- [Source: _bmad-output/planning-artifacts/prd.md#FR41] — "Every merge, imputation, and extrapolation is recorded as an explicit assumption in the governance layer"
- [Source: _bmad-output/project-context.md#Python-Language-Rules] — Frozen dataclasses, Protocols, `from __future__ import annotations`
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules] — PyArrow canonical data type, no pandas in core logic
- [Source: src/reformlab/population/methods/base.py] — MergeMethod protocol, MergeConfig, MergeAssumption, MergeResult
- [Source: src/reformlab/population/methods/base.py#to_governance_entry] — Governance bridge pattern (key/value/source/is_default)
- [Source: src/reformlab/population/loaders/base.py] — DataSourceLoader protocol, SourceConfig, CacheStatus, CachedLoader
- [Source: src/reformlab/governance/capture.py] — `capture_assumptions()` API (flat key-value, NOT for structured merge assumptions)
- [Source: src/reformlab/governance/manifest.py#AssumptionEntry] — TypedDict with key/value/source/is_default; JSON-compatibility validation
- [Source: src/reformlab/governance/manifest.py#RunManifest] — Frozen dataclass, assumptions field validation in `_validate()`
- [Source: src/reformlab/population/methods/uniform.py] — Reference merge method implementation (validation order, logging, assumption construction)
- [Source: src/reformlab/population/methods/errors.py] — MergeError hierarchy (summary-reason-fix pattern)
- [Source: src/reformlab/population/loaders/errors.py] — DataSourceError hierarchy (same pattern)
- [Source: src/reformlab/data/pipeline.py] — DatasetManifest/DatasetRegistry pattern (frozen metadata + mutable registry)
- [Source: _bmad-output/implementation-artifacts/11-5-implement-ipf-and-conditional-sampling-merge-methods.md] — Previous story (merge method patterns, test patterns)
- [Source: _bmad-output/implementation-artifacts/11-4-define-mergemethod-protocol-and-uniform-distribution-method.md] — Protocol reference, antipattern about capture_assumptions() mismatch

## File List

**New files (4):**
- `src/reformlab/population/pipeline.py`
- `src/reformlab/population/assumptions.py`
- `tests/population/test_pipeline.py`
- `tests/population/test_assumptions.py`

**Modified files (2):**
- `src/reformlab/population/__init__.py` — add new exports
- `tests/population/conftest.py` — add mock loader fixtures

## Change Log

- 2026-03-05: Story implementation completed — all 9 tasks and 39 subtasks delivered and verified. Comprehensive test coverage with 73 new tests for pipeline and assumption modules. All tests pass (382 total in population module). Ruff and mypy strict validation passed. Full governance integration via `PipelineAssumptionChain.to_governance_entries()` with step context preservation. Error handling with `PipelineExecutionError` capturing step-level context.
- 2026-03-03: Story created by create-story workflow — comprehensive developer context with composable builder pattern design, fluent API specification, governance integration via `to_governance_entry()` (NOT `capture_assumptions()`), error hierarchy with step context preservation, mock loader test fixtures, sequential DAG execution model, timing measurement, and downstream dependency mapping.


]]></file>
<file id="e4da3166" path="_bmad-output/implementation-artifacts/11-7-implement-population-validation-against-known-marginals.md" label="STORY FILE"><![CDATA[

# Story 11.7: Implement population validation against known marginals

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform developer validating synthetic population quality,
I want to validate generated populations against known reference marginal distributions from institutional sources (e.g., INSEE income decile distributions, SDES vehicle fleet composition),
so that analysts can detect deviations in their synthetic populations and ensure statistical credibility before using populations for policy simulation.

## Acceptance Criteria

1. Given a generated population (pa.Table) and a set of reference marginal distributions (e.g., income distribution by decile from INSEE), when validation is run, then each marginal is compared with a documented distance metric (Chi-squared or total variation distance).
2. Given validation results, when a marginal exceeds the tolerance threshold, then a warning identifies the specific marginal, expected vs. actual values (category-level breakdown), and the tolerance used.
3. Given validation results, when all marginals pass, then a validation summary is produced confirming the population matches reference distributions within tolerances.
4. Given validation output, when recorded in governance, then the validation status and per-marginal results are part of the population's assumption chain via `ValidationAssumption.to_governance_entry()`.

## Tasks / Subtasks

- [ ] Task 1: Create `validation.py` with error hierarchy and constraint/result types (AC: #1, #2)
  - [ ] 1.1 Create `src/reformlab/population/validation.py` with module docstring referencing Story 11.7, FR42 — explain the module validates synthetic populations against known marginal distributions from institutional sources.
  - [ ] 1.2 Define `PopulationValidationError(Exception)` base class following summary-reason-fix pattern:
    ```python
    class PopulationValidationError(Exception):
        """Base exception for population validation operations."""
        def __init__(self, *, summary: str, reason: str, fix: str) -> None:
            self.summary = summary
            self.reason = reason
            self.fix = fix
            super().__init__(f"{summary} - {reason} - {fix}")
    ```
  - [ ] 1.3 Define `MarginalConstraintMismatch(PopulationValidationError)` — raised when a marginal exceeds tolerance. Additional attributes: `dimension`, `tolerance`, `max_deviation`, `expected_values`, `actual_values`.
  - [ ] 1.4 Implement `MarginalConstraint` frozen dataclass:
    ```python
    @dataclass(frozen=True)
    class MarginalConstraint:
        """A reference marginal distribution for validation.

        Specifies the expected distribution of a categorical variable
        in the population. Used to validate synthetic populations
        against institutional benchmarks.

        Attributes:
            dimension: Column name in the population table.
            distribution: Mapping from category value to expected proportion (sums to 1.0).
            tolerance: Maximum acceptable absolute deviation per category.
        """
        dimension: str
        distribution: dict[str, float]
        tolerance: float

        def __post_init__(self) -> None:
            # Validate dimension is non-empty string
            if not self.dimension or self.dimension.strip() == "":
                msg = "dimension must be a non-empty string"
                raise ValueError(msg)
            # Validate distribution is non-empty
            if not self.distribution:
                msg = "distribution must be a non-empty dict"
                raise ValueError(msg)
            # Validate all proportions are >= 0
            for cat, prop in self.distribution.items():
                if prop < 0:
                    msg = f"distribution proportion for {cat!r} must be >= 0, got {prop}"
                    raise ValueError(msg)
            # Validate proportions sum to 1.0 (within floating point tolerance)
            total = sum(self.distribution.values())
            if not math.isclose(total, 1.0, reltol=1e-9, abs_tol=1e-9):
                msg = f"distribution proportions must sum to 1.0, got {total}"
                raise ValueError(msg)
            # Validate tolerance is positive
            if self.tolerance < 0:
                msg = f"tolerance must be >= 0, got {self.tolerance}"
                raise ValueError(msg)
            # Shallow copy — safe because values are floats (immutable)
            object.__setattr__(self, "distribution", dict(self.distribution))
    ```
  - [ ] 1.5 Implement `MarginalResult` frozen dataclass:
    ```python
    @dataclass(frozen=True)
    class MarginalResult:
        """Result of validating a single marginal constraint.

        Records the observed distribution in the population,
        the deviation from expected, and whether validation passed.

        Attributes:
            constraint: The marginal constraint being validated.
            observed: Observed proportions in the population.
            deviations: Absolute deviation per category (observed - expected).
            max_deviation: Maximum absolute deviation across all categories.
            passed: Whether constraint passed (max_deviation <= tolerance).
        """
        constraint: MarginalConstraint
        observed: dict[str, float]
        deviations: dict[str, float]
        max_deviation: float
        passed: bool
    ```
    Validate in `__post_init__`: all category keys in `observed` and `deviations` match `constraint.distribution`, `passed` is boolean, `max_deviation >= 0`.
  - [ ] 1.6 Implement `ValidationResult` frozen dataclass:
    ```python
    @dataclass(frozen=True)
    class ValidationResult:
        """Overall result of population validation against marginals.

        Aggregates results from all marginal constraints and provides
        governance-integrated assumption recording.

        Attributes:
            all_passed: Whether all constraints passed within tolerance.
            marginal_results: Ordered results for each constraint.
            total_constraints: Number of constraints validated.
            failed_count: Number of constraints that failed.
        """
        all_passed: bool
        marginal_results: tuple[MarginalResult, ...]
        total_constraints: int
        failed_count: int
    ```
    Validate in `__post_init__`: `marginal_results` is tuple, `total_constraints == len(marginal_results)`, `failed_count` matches count of `not result.passed` for each result.

- [ ] Task 2: Implement `PopulationValidator` class with validation logic (AC: #1, #2)
  - [ ] 2.1 Implement `PopulationValidator.__init__()`:
    ```python
    class PopulationValidator:
        """Validates synthetic populations against known marginal distributions.

        Supports multiple distance metrics and configurable tolerances.
        Results integrate with governance layer via assumption recording.

        Example:
            >>> validator = PopulationValidator(
            ...     constraints=[
            ...         MarginalConstraint(
            ...             dimension="income_decile",
            ...             distribution={"1": 0.08, "2": 0.12, "3": 0.15, ...},
            ...             tolerance=0.02,
            ...         ),
            ...         MarginalConstraint(
            ...             dimension="vehicle_type",
            ...             distribution={"car": 0.65, "suv": 0.20, "bike": 0.15},
            ...             tolerance=0.03,
            ...         ),
            ...     ],
            ... )
            >>> result = validator.validate(population_table)
            >>> result.all_passed  # True if all within tolerance
        """
        def __init__(self, constraints: Sequence[MarginalConstraint]) -> None:
            if not constraints:
                msg = "constraints must be a non-empty sequence"
                raise ValueError(msg)
            self._constraints = tuple(constraints)
    ```
  - [ ] 2.2 Implement `validate(self, population: pa.Table) -> ValidationResult`:
    - Extract dimension column from population for each constraint
    - Compute observed proportions by counting rows per category, dividing by total rows
    - Handle missing categories in population (observed proportion = 0.0)
    - Compute absolute deviation per category: `|observed - expected|`
    - Determine `max_deviation` across all categories
    - Set `passed` if `max_deviation <= constraint.tolerance`
    - Build `MarginalResult` for each constraint
    - Determine `all_passed` (all results passed) and `failed_count`
    - Return `ValidationResult` with tuple of marginal results
  - [ ] 2.3 Implement `MarginalConstraintMismatch` raising:
    - **Do NOT raise by default** — validation errors should be informational, not blocking pipeline execution. The `PopulationValidator.validate()` method always returns `ValidationResult`; mismatches are recorded in `MarginalResult.passed=False`.
    - `MarginalConstraintMismatch` is provided as an optional error type for downstream code that wants to enforce strict validation (e.g., a quality gate before publishing a population).

- [ ] Task 3: Create `ValidationAssumption` for governance integration (AC: #4)
  - [ ] 3.1 Implement `ValidationAssumption` frozen dataclass in `validation.py`:
    ```python
    @dataclass(frozen=True)
    class ValidationAssumption:
        """Structured assumption record from population validation.

        Records the validation status and per-marginal results for
        governance integration. Can be converted to governance-compatible
        AssumptionEntry format via to_governance_entry().

        Attributes:
            all_passed: Whether all constraints passed within tolerance.
            total_constraints: Number of constraints validated.
            failed_count: Number of constraints that failed.
            marginal_details: Per-constraint details with deviations.
        """
        all_passed: bool
        total_constraints: int
        failed_count: int
        marginal_details: dict[str, dict[str, Any]]

        def __post_init__(self) -> None:
            # Coerce to tuple for immutability
            # Deep-copy is unnecessary since all contents are primitives/floats
            object.__setattr__(self, "marginal_details", dict(self.marginal_details))
    ```
  - [ ] 3.2 Implement `ValidationAssumption.to_governance_entry()`:
    ```python
    def to_governance_entry(self, *, source_label: str = "population_validation") -> dict[str, Any]:
        """Convert to governance-compatible AssumptionEntry format.

        Returns a dict with keys: key, value, source, is_default.
        The value dict includes all validation details.

        Args:
            source_label: Label for the source field.
                Defaults to "population_validation".

        Returns:
            Dict matching governance.manifest.AssumptionEntry structure.
        """
        return {
            "key": "population_validation",
            "value": {
                "all_passed": self.all_passed,
                "total_constraints": self.total_constraints,
                "failed_count": self.failed_count,
                "marginal_details": self.marginal_details,
            },
            "source": source_label,
            "is_default": False,
        }
    ```
  - [ ] 3.3 Add `ValidationResult.to_assumption()` method to `ValidationResult`:
    ```python
    def to_assumption(self) -> ValidationAssumption:
        """Convert validation result to governance-compatible assumption.

        Builds a ValidationAssumption with per-constraint details
        including dimension, tolerance, max_deviation, passed status, and
        expected vs. observed proportions.
        """
        marginal_details: dict[str, dict[str, Any]] = {}
        for result in self.marginal_results:
            marginal_details[result.constraint.dimension] = {
                "tolerance": result.constraint.tolerance,
                "max_deviation": result.max_deviation,
                "passed": result.passed,
                "expected": result.constraint.distribution,
                "observed": result.observed,
                "deviations": result.deviations,
            }

        return ValidationAssumption(
            all_passed=self.all_passed,
            total_constraints=self.total_constraints,
            failed_count=self.failed_count,
            marginal_details=marginal_details,
        )
    ```

- [ ] Task 4: Update `__init__.py` exports (AC: all)
  - [ ] 4.1 Export from `src/reformlab/population/__init__.py`: add `PopulationValidator`, `MarginalConstraint`, `MarginalResult`, `ValidationResult`, `ValidationAssumption`, `PopulationValidationError`, `MarginalConstraintMismatch` — update `__all__` listing.

- [ ] Task 5: Create test fixtures for validation tests (AC: all)
  - [ ] 5.1 Add to `tests/population/conftest.py`:
    - `population_table_valid` — a PyArrow table with columns: `income_decile` (utf8), `vehicle_type` (utf8), `region_code` (utf8). 10 rows with income deciles distributed roughly matching INSEE reference: decile 1: 1 household, decile 2: 1 household, ... decile 10: 1 household (uniform distribution). Vehicle types: 7 cars, 2 suvs, 1 bike.
    - `population_table_invalid_income` — same structure but income decile distribution deviates: decile 1: 3 households (expected ~1), decile 10: 0 households (expected ~1).
    - `population_table_invalid_vehicle` — vehicle type distribution deviates: 10 cars, 0 suvs, 0 bikes (expected ~7/2/1).
    - `constraint_income_decile` — `MarginalConstraint` for `income_decile` with distribution matching INSEE reference (equal 0.08 per decile? No, decile 1-10 each ~10% = 0.1), tolerance 0.02.
    - `constraint_vehicle_type` — `MarginalConstraint` for `vehicle_type` with distribution: {"car": 0.65, "suv": 0.20, "bike": 0.15}, tolerance 0.03.
    - `constraint_region_code` — `MarginalConstraint` for `region_code` with distribution: {"11": 0.2, "24": 0.2, "31": 0.2, "44": 0.2, "75": 0.2}, tolerance 0.05.

- [ ] Task 6: Write comprehensive validation tests (AC: #1, #2, #3, #4)
  - [ ] 6.1 `tests/population/test_validation.py`:
    - `TestPopulationValidationErrorHierarchy`:
      - `PopulationValidationError` inherits `Exception`, summary-reason-fix pattern
      - `MarginalConstraintMismatch` inherits `PopulationValidationError`, has `dimension`, `tolerance`, `max_deviation`, `expected_values`, `actual_values`
    - `TestMarginalConstraint`:
      - Frozen dataclass
      - Holds `dimension`, `distribution`, `tolerance`
      - Empty `dimension` raises `ValueError`
      - Empty `distribution` raises `ValueError`
      - Negative proportion in `distribution` raises `ValueError`
      - Proportions not summing to 1.0 raise `ValueError`
      - Negative `tolerance` raises `ValueError`
      - Distribution coerced to dict in `__post_init__`
    - `TestMarginalResult`:
      - Frozen dataclass
      - Holds `constraint`, `observed`, `deviations`, `max_deviation`, `passed`
      - All category keys match between `constraint.distribution`, `observed`, and `deviations`
      - `max_deviation` equals maximum value in `deviations` dict
      - `passed` is boolean
      - `max_deviation >= 0`
    - `TestValidationResult`:
      - Frozen dataclass
      - Holds `all_passed`, `marginal_results`, `total_constraints`, `failed_count`
      - `marginal_results` is tuple
      - `total_constraints` equals `len(marginal_results)`
      - `failed_count` matches count of failed results
    - `TestPopulationValidatorConstruction`:
      - Constructor accepts constraints sequence
      - Empty constraints list raises `ValueError`
      - Constraints stored as tuple
    - `TestPopulationValidatorValidateSingleConstraint`:
      - Single constraint with perfect match → `MarginalResult.passed` is `True`, `max_deviation == 0.0`
      - Single constraint within tolerance → `passed` is `True`
      - Single constraint exceeding tolerance → `passed` is `False`, `max_deviation > tolerance`
      - `observed` proportions sum to 1.0
      - `deviations` computed correctly per category
    - `TestPopulationValidatorValidateMultipleConstraints`:
      - Two constraints, both passing → `ValidationResult.all_passed` is `True`, `failed_count` is 0
      - Two constraints, one failing → `all_passed` is `False`, `failed_count` is 1
      - `total_constraints` is 2
      - `marginal_results` ordered by constraint insertion order
    - `TestPopulationValidatorValidateMissingCategory`:
      - Population missing a category from expected distribution → observed proportion 0.0, deviation equals expected proportion
      - Constraint fails if deviation exceeds tolerance
    - `TestPopulationValidatorValidateExtraCategory`:
      - Population has category not in expected distribution → observed proportion for that category, but deviation only computed for expected categories
      - Extra category counts toward total rows for proportion calculation
    - `TestPopulationValidatorValidateAgainstRealisticPopulation`:
      - Use `population_table_valid` with `constraint_income_decile` and `constraint_vehicle_type` → both pass within tolerance
      - Use `population_table_valid` with `constraint_region_code` → passes within tolerance
      - Use `population_table_invalid_income` → `constraint_income_decile` fails with max deviation documented
      - Use `population_table_invalid_vehicle` → `constraint_vehicle_type` fails with max deviation documented
    - `TestValidationAssumptionGovernanceEntries`:
      - Given `ValidationAssumption`, `to_governance_entries()` returns dict with `key`, `value`, `source`, `is_default`
      - `is_default` is `False`
      - Default `source` is `"population_validation"`
      - Custom `source_label` is respected
      - `value` dict contains `all_passed`, `total_constraints`, `failed_count`, `marginal_details`
      - `marginal_details` contains per-constraint entries with `tolerance`, `max_deviation`, `passed`, `expected`, `observed`, `deviations`
    - `TestValidationAssumptionIntegrationWithManifest`:
      - Given governance entry from `ValidationAssumption`, when validated against `RunManifest` assumptions schema, then entry passes validation
      - Use `minimal_manifest` from `tests/governance/conftest.py` for required fields
      - Use `cast(AssumptionEntry, entry)` for mypy strict
    - `TestValidationResultToAssumption`:
      - Given `ValidationResult` with all passed, `to_assumption()` produces `ValidationAssumption` with `all_passed=True`
      - Given `ValidationResult` with failures, `to_assumption()` produces `ValidationAssumption` with `all_passed=False` and correct `failed_count`
      - `marginal_details` contains per-constraint details extracted from `marginal_results`

- [ ] Task 7: Run full test suite and lint (AC: all)
  - [ ] 7.1 `uv run pytest tests/population/test_validation.py` — all new tests pass
  - [ ] 7.2 `uv run pytest tests/population/` — no regressions in loader, method, pipeline, or assumption tests
  - [ ] 7.3 `uv run ruff check src/reformlab/population/ tests/population/` — no lint errors
  - [ ] 7.4 `uv run mypy src/reformlab/population/` — no mypy errors (strict mode)

## Dev Notes

### Architecture Context: Validation Layer

This story creates the **validation layer** for the population module. It validates synthetic populations produced by `PopulationPipeline` against known reference marginals from institutional sources (INSEE, Eurostat, ADEME, SDES).

```
src/reformlab/population/
├── __init__.py          ← Modified: add new exports
├── assumptions.py       ← UNCHANGED (Story 11.6)
├── pipeline.py          ← UNCHANGED (Story 11.6)
├── validation.py        ← NEW (this story) — population validation
├── loaders/             ← UNCHANGED (Stories 11.1–11.3)
├── methods/             ← UNCHANGED (Stories 11.4–11.5)
└── validation.py        ← Will NOT exist after Story 11.8 (integration into pipeline)
```

**Wait, correction:** The validation.py file IS created by this story. Story 11.8 (notebook) will use `PopulationValidator` to validate the example French household population. The validation module persists — it's not temporary.

### Design Pattern: Non-Blocking Validation by Default

**CRITICAL:** `PopulationValidator.validate()` does NOT raise exceptions when constraints fail. It returns a `ValidationResult` with `passed=False` flags. This is intentional:

- Validation is **informational**, not blocking — analysts should see validation warnings and decide whether to proceed
- Pipeline execution (`PopulationPipeline.execute()`) continues even if validation fails
- Downstream code can optionally enforce strict validation by raising `MarginalConstraintMismatch` if needed

**Error hierarchy purpose:** `PopulationValidationError` and `MarginalConstraintMismatch` exist for:
1. Quality gates (e.g., a "population must pass validation" workflow step)
2. Optional strict mode: caller checks `result.all_passed` and raises `MarginalConstraintMismatch` if `False`

### Distance Metric: Absolute Deviation per Category

The validation metric is **absolute deviation per category**:

```
deviation[category] = |observed[category] - expected[category]|
max_deviation = max(deviations.values())
passed = (max_deviation <= tolerance)
```

This is simple, interpretable, and sufficient for detecting significant deviations in categorical marginal distributions. More complex metrics (Chi-squared, K-S test) are out of scope for MVP.

**Example interpretation:**
- Constraint: `income_decile` distribution: {"1": 0.08, "2": 0.12, ..., "10": 0.08}
- Tolerance: 0.02
- Observed: {"1": 0.10, "2": 0.11, ..., "10": 0.07}
- Deviations: {"1": 0.02, "2": 0.01, ..., "10": 0.01}
- `max_deviation`: 0.02 (from decile 1)
- `passed`: `True` (0.02 <= 0.02)

If `max_deviation` were 0.025, then `passed` would be `False` and the analyst would see a warning identifying decile 1 as the problematic marginal.

### Governance Integration Pattern

`ValidationAssumption.to_governance_entry()` follows the same pattern as `MergeAssumption.to_governance_entry()`:

```python
{
    "key": "population_validation",
    "value": {
        "all_passed": True,
        "total_constraints": 2,
        "failed_count": 0,
        "marginal_details": {
            "income_decile": {
                "tolerance": 0.02,
                "max_deviation": 0.01,
                "passed": True,
                "expected": {"1": 0.08, "2": 0.12, ...},
                "observed": {"1": 0.09, "2": 0.11, ...},
                "deviations": {"1": 0.01, "2": -0.01, ...},
            },
            "vehicle_type": {
                "tolerance": 0.03,
                "max_deviation": 0.02,
                "passed": True,
                "expected": {"car": 0.65, "suv": 0.20, "bike": 0.15},
                "observed": {"car": 0.67, "suv": 0.18, "bike": 0.15},
                "deviations": {"car": 0.02, "suv": -0.02, "bike": 0.0},
            },
        },
    },
    "source": "population_validation",
    "is_default": False,
}
```

This entry is appended to `RunManifest.assumptions` alongside pipeline merge assumptions, providing full traceability of validation results.

### Proportion Computation Algorithm

To compute observed proportions from a PyArrow table:

```python
# Extract dimension column
column_data = population.column(dimension).to_pylist()

# Count rows per category
counts: dict[str, int] = {}
for category in constraint.distribution.keys():
    counts[category] = column_data.count(category)

# Count extra categories (not in expected distribution)
all_categories = set(column_data)
extra_categories = all_categories - set(constraint.distribution.keys())
for category in extra_categories:
    counts[category] = column_data.count(category)

total_rows = len(column_data)

# Compute observed proportions
observed: dict[str, float] = {}
for category, count in counts.items():
    observed[category] = count / total_rows if total_rows > 0 else 0.0
```

**Edge cases handled:**
- Missing category in population: `observed[category] = 0.0`, `deviation = expected[category]`
- Extra category not in expected: included in counts but not in `deviations` (deviation undefined for non-expected categories)
- Zero rows: all proportions are 0.0, deviations equal expected values (constraint will fail unless expected values are all 0.0)

### Tolerance Selection Guidance

The choice of tolerance is analyst-controlled and depends on the marginal and use case. Typical ranges:

| Marginal Type | Typical Tolerance | Rationale |
|---------------|-------------------|-----------|
| Income decile distribution | 0.01 - 0.03 | INSEE surveys have sampling error; synthetic population matching within 1-3 percentage points is acceptable |
| Vehicle fleet composition | 0.02 - 0.05 | SDES data aggregates from multiple sources; moderate tolerance accommodates reporting lag |
| Geographic distribution | 0.01 - 0.02 | Regional populations are well-measured; synthetic should match closely |
| Heating system mix | 0.03 - 0.05 | ADEME surveys smaller samples; higher tolerance |

**No automatic tolerance selection:** The system does not infer tolerances from sample size or statistical significance. Analysts must provide explicit tolerance values based on domain knowledge and credibility requirements.

### Relationship to IPF Constraints

`MarginalConstraint` is simpler than `IPFConstraint` from `methods/base.py`:

| Aspect | IPFConstraint | MarginalConstraint |
|--------|---------------|-------------------|
| Purpose | Enforce marginals during merge (reweighting) | Validate final population against reference |
| Targets | Target counts (absolute) | Expected proportions (relative) |
| Enforcement | Active (modifies weights) | Passive (only checks) |
| Use case | IPF merge method parameter | Post-merge quality check |

Both share the same conceptual model: a dimension with categorical values and target/reference distribution. However, `MarginalConstraint` is for validation only — it does not modify the population.

### PyArrow Table Operations

Validation relies on PyArrow operations:
- `population.column(name)` — extract a column as ChunkedArray
- `.to_pylist()` — convert to Python list for counting
- `len(column_data)` — get total row count

No new PyArrow dependencies or patterns beyond what's already used in the pipeline and merge methods.

### Integration with Pipeline (Story 11.6)

`PopulationValidator` can be used after `PopulationPipeline.execute()`:

```python
# Execute pipeline
pipeline_result = pipeline.execute()

# Validate population
validator = PopulationValidator(constraints=[...])
validation_result = validator.validate(pipeline_result.table)

# Check validation
if not validation_result.all_passed:
    # Log warning or raise MarginalConstraintMismatch if strict mode
    pass

# Record validation assumption
validation_assumption = validation_result.to_assumption()
# Append to governance manifest
manifest.assumptions.append(cast(AssumptionEntry, validation_assumption.to_governance_entry()))
```

This workflow will be demonstrated in Story 11.8 (notebook) for the French household example.

### No New Dependencies Required

All implementation uses existing dependencies and stdlib:

- `dataclasses` — frozen dataclasses (stdlib)
- `math` — `math.isclose()` for proportion sum validation (stdlib)
- `typing` — type hints (stdlib)
- `pyarrow` — `pa.Table` operations (existing dependency)
- `logging` — optional for structured logging (stdlib, existing pattern in pipeline)

Import patterns:
- `pyarrow` imported at runtime in `validation.py` (same as pipeline.py)
- No `TYPE_CHECKING` guards needed for PyArrow in validation types (only used in method signatures)

### Error Hierarchy Placement

Validation errors (`PopulationValidationError`, `MarginalConstraintMismatch`) live in `validation.py` rather than a separate `errors.py`. This follows the pattern from `pipeline.py` — the module is a single-file module at the population package level, and a separate `errors.py` would add a file for two small exception classes that are only used by validation logic.

### Logging Strategy (Optional)

Structured logging is optional but recommended for traceability:

```python
import logging

_logger = logging.getLogger(__name__)

# In validate() method:
_logger.info(
    "event=population_validation_start constraints=%d rows=%d",
    len(self._constraints),
    len(population),
)

_logger.info(
    "event=population_validation_complete all_passed=%s failed_count=%d/%d",
    validation_result.all_passed,
    validation_result.failed_count,
    validation_result.total_constraints,
)

# In to_assumption() method:
_logger.debug(
    "event=validation_assumption_created all_passed=%s constraints=%d",
    self.all_passed,
    self.total_constraints,
)
```

Follows the same key=value format as `pipeline.py`.

### Downstream Dependencies

Story 11.7 is consumed by:

- **Story 11.8** (Notebook) — demonstrates validation of the French household population against INSEE/SDES marginals
- **Future population workflows** — analysts can add validation steps to their pipelines to ensure quality before policy simulation
- **Governance layer** — validation assumptions are recorded in manifests for traceability

### Project Structure Notes

**New files (2):**
- `src/reformlab/population/validation.py`
- `tests/population/test_validation.py`

**Modified files (1):**
- `src/reformlab/population/__init__.py` — add new exports, update `__all__`

**No changes** to `pyproject.toml` (no new dependencies)

### Alignment with Project Conventions

All rules from `project-context.md` apply:

- Every file starts with `from __future__ import annotations`
- `if TYPE_CHECKING:` guards for annotation-only imports (not needed in validation.py)
- Frozen dataclasses as default (`@dataclass(frozen=True)`) for all value types: `MarginalConstraint`, `MarginalResult`, `ValidationResult`, `ValidationAssumption`
- `PopulationValidator` is a mutable class — NOT a frozen dataclass (it holds state)
- Protocols, not ABCs — no protocols in this story (validation is a concrete implementation)
- Subsystem-specific exceptions (`PopulationValidationError` hierarchy, not bare `Exception`)
- `dict[str, Any]` for metadata bags (`ValidationAssumption.marginal_details`)
- `tuple[...]` for immutable sequences (`marginal_results` in `ValidationResult`)
- `X | None` union syntax (not needed in this story)
- Module-level docstrings referencing story/FR
- `logging.getLogger(__name__)` with structured key=value format (optional but recommended)
- `# ====...====` section separators for major sections within longer modules

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#New-Subsystem-Population-Generation] — Directory structure, validation.py placement
- [Source: _bmad-output/planning-artifacts/epics.md#BKL-1107] — Story definition and acceptance criteria
- [Source: _bmad-output/planning-artifacts/prd.md#FR42] — "System validates generated populations against known marginal distributions from source data"
- [Source: _bmad-output/project-context.md#Python-Language-Rules] — Frozen dataclasses, `from __future__ import annotations`
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules] — PyArrow canonical data type
- [Source: src/reformlab/population/methods/base.py] — `IPFConstraint` pattern reference for constraint design
- [Source: src/reformlab/population/pipeline.py] — Error hierarchy pattern, logging pattern
- [Source: src/reformlab/governance/manifest.py#AssumptionEntry] — TypedDict with key/value/source/is_default; governance integration pattern
- [Source: src/reformlab/population/assumptions.py] — `to_governance_entry()` pattern reference

## Dev Agent Record

### Agent Model Used

glm-4.7

### Debug Log References

None - story created from scratch, no debug logs needed.

### Completion Notes List

- Comprehensive developer context created with validation algorithm specification
- Error hierarchy designed following pipeline.py pattern
- Governance integration via `ValidationAssumption.to_governance_entry()` matching `MergeAssumption` pattern
- Non-blocking validation by default with optional strict mode via `MarginalConstraintMismatch`
- Absolute deviation metric chosen for interpretability
- Test fixtures designed with valid and invalid populations
- Full alignment with project conventions (frozen dataclasses, PyArrow usage, structured logging)

### File List

**New files (2):**
- `src/reformlab/population/validation.py`
- `tests/population/test_validation.py`

**Modified files (1):**
- `src/reformlab/population/__init__.py` — add new exports

## Change Log

- 2026-03-05: Story created with comprehensive developer context, ready for dev-story workflow.



]]></file>
<file id="173799eb" path="src/reformlab/population/__init__.py" label="SOURCE CODE"><![CDATA[

"""Realistic population generation library for ReformLab.

Provides institutional data source loaders, statistical fusion methods,
and population pipeline composition for building synthetic populations
from open data sources (INSEE, Eurostat, ADEME, SDES).

This module implements EPIC-11 (Realistic Population Generation Library).
Phase 2 introduces optional network dependencies for data downloads,
with offline-first caching semantics.

Public API
----------
DataSourceLoader : Protocol
    Interface for institutional data source loaders.
SourceConfig : dataclass
    Immutable configuration for a data source download.
CacheStatus : dataclass
    Status of a cached data source.
SourceCache : class
    Disk-based caching infrastructure for downloaded data.
CachedLoader : class
    Base class wrapping protocol + cache logic.
MergeMethod : Protocol
    Interface for statistical dataset fusion methods.
MergeConfig : dataclass
    Immutable configuration for a merge operation.
MergeAssumption : dataclass
    Structured assumption record from a merge operation.
MergeResult : dataclass
    Immutable result of a merge operation.
UniformMergeMethod : class
    Uniform random matching with replacement.
IPFMergeMethod : class
    Iterative Proportional Fitting reweighting and matching.
IPFConstraint : dataclass
    A marginal constraint for IPF.
IPFResult : dataclass
    Convergence diagnostics from an IPF run.
ConditionalSamplingMethod : class
    Stratum-based conditional sampling merge.
PopulationPipeline : class
    Composable builder for population generation pipelines.
PipelineResult : dataclass
    Immutable result of a pipeline execution.
PipelineStepLog : dataclass
    Log entry for a completed pipeline step.
PipelineAssumptionChain : dataclass
    Complete assumption chain from a pipeline execution.
PipelineAssumptionRecord : dataclass
    Records a single assumption from a pipeline step.
PipelineError : Exception
    Base exception for population pipeline operations.
PipelineConfigError : PipelineError
    Raised for invalid pipeline configuration.
PipelineExecutionError : PipelineError
    Raised when a pipeline step fails during execution.
"""

from __future__ import annotations

from reformlab.population.assumptions import (
    PipelineAssumptionChain,
    PipelineAssumptionRecord,
)
from reformlab.population.loaders.ademe import (
    ADEME_AVAILABLE_DATASETS,
    ADEME_CATALOG,
    ADEMEDataset,
    ADEMELoader,
    get_ademe_loader,
    make_ademe_config,
)
from reformlab.population.loaders.base import (
    CachedLoader,
    CacheStatus,
    DataSourceLoader,
    SourceConfig,
)
from reformlab.population.loaders.cache import SourceCache
from reformlab.population.loaders.errors import (
    DataSourceDownloadError,
    DataSourceError,
    DataSourceOfflineError,
    DataSourceValidationError,
)
from reformlab.population.loaders.eurostat import (
    EUROSTAT_AVAILABLE_DATASETS,
    EUROSTAT_CATALOG,
    EurostatDataset,
    EurostatLoader,
    get_eurostat_loader,
    make_eurostat_config,
)
from reformlab.population.loaders.insee import (
    AVAILABLE_DATASETS,
    INSEE_AVAILABLE_DATASETS,
    INSEE_CATALOG,
    INSEEDataset,
    INSEELoader,
    get_insee_loader,
    make_insee_config,
)
from reformlab.population.loaders.sdes import (
    SDES_AVAILABLE_DATASETS,
    SDES_CATALOG,
    SDESDataset,
    SDESLoader,
    get_sdes_loader,
    make_sdes_config,
)
from reformlab.population.methods.base import (
    IPFConstraint,
    IPFResult,
    MergeAssumption,
    MergeConfig,
    MergeMethod,
    MergeResult,
)
from reformlab.population.methods.conditional import ConditionalSamplingMethod
from reformlab.population.methods.errors import (
    MergeConvergenceError,
    MergeError,
    MergeValidationError,
)
from reformlab.population.methods.ipf import IPFMergeMethod
from reformlab.population.methods.uniform import UniformMergeMethod
from reformlab.population.pipeline import (
    PipelineConfigError,
    PipelineError,
    PipelineExecutionError,
    PipelineResult,
    PipelineStepLog,
    PopulationPipeline,
)

__all__ = [
    "ADEME_AVAILABLE_DATASETS",
    "ADEME_CATALOG",
    "ADEMEDataset",
    "ADEMELoader",
    "AVAILABLE_DATASETS",
    "CachedLoader",
    "CacheStatus",
    "DataSourceDownloadError",
    "DataSourceError",
    "DataSourceLoader",
    "DataSourceOfflineError",
    "DataSourceValidationError",
    "EUROSTAT_AVAILABLE_DATASETS",
    "EUROSTAT_CATALOG",
    "EurostatDataset",
    "EurostatLoader",
    "INSEE_AVAILABLE_DATASETS",
    "INSEE_CATALOG",
    "INSEEDataset",
    "INSEELoader",
    "SDES_AVAILABLE_DATASETS",
    "SDES_CATALOG",
    "SDESDataset",
    "SDESLoader",
    "SourceCache",
    "SourceConfig",
    "PipelineAssumptionChain",
    "PipelineAssumptionRecord",
    "PipelineConfigError",
    "PipelineError",
    "PipelineExecutionError",
    "PipelineResult",
    "PipelineStepLog",
    "PopulationPipeline",
    "get_ademe_loader",
    "get_eurostat_loader",
    "get_insee_loader",
    "get_sdes_loader",
    "ConditionalSamplingMethod",
    "IPFConstraint",
    "IPFMergeMethod",
    "IPFResult",
    "MergeAssumption",
    "MergeConfig",
    "MergeConvergenceError",
    "MergeError",
    "MergeMethod",
    "MergeResult",
    "MergeValidationError",
    "UniformMergeMethod",
    "make_ademe_config",
    "make_eurostat_config",
    "make_insee_config",
    "make_sdes_config",
]


]]></file>
</context>
<variables>
<var name="architecture_file" description="Architecture for technical requirements verification" load_strategy="SELECTIVE_LOAD" token_approx="2785">_bmad-output/planning-artifacts/architecture-diagrams.md</var>
<var name="author">BMad</var>
<var name="communication_language">English</var>
<var name="date">2026-03-05</var>
<var name="description">Quality competition validator - systematically review and improve story context created by create-story workflow</var>
<var name="document_output_language">English</var>
<var name="epic_num">11</var>
<var name="epics_file" description="Enhanced epics+stories file for story verification" load_strategy="SELECTIVE_LOAD" token_approx="22505">_bmad-output/planning-artifacts/epics.md</var>
<var name="implementation_artifacts">_bmad-output/implementation-artifacts</var>
<var name="model">validator</var>
<var name="name">validate-story</var>
<var name="output_folder">_bmad-output/implementation-artifacts</var>
<var name="planning_artifacts">_bmad-output/planning-artifacts</var>
<var name="prd_file" description="PRD for requirements verification" load_strategy="SELECTIVE_LOAD" token_approx="7305">_bmad-output/planning-artifacts/prd-validation-report.md</var>
<var name="project_context" file_id="e58fb4dd" load_strategy="EMBEDDED" token_approx="2024">embedded in prompt, file id: e58fb4dd</var>
<var name="project_knowledge">docs</var>
<var name="project_name">ReformLab</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_dir">_bmad-output/implementation-artifacts</var>
<var name="story_file" file_id="e4da3166">embedded in prompt, file id: e4da3166</var>
<var name="story_id">11.7</var>
<var name="story_key">11-7-implement-population-validation-against-known-marginals</var>
<var name="story_num">7</var>
<var name="story_title">implement-population-validation-against-known-marginals</var>
<var name="timestamp">20260305_171738</var>
<var name="user_name">Lucas</var>
<var name="user_skill_level">expert</var>
<var name="ux_file" description="UX design for user experience verification" load_strategy="SELECTIVE_LOAD" token_approx="20820">_bmad-output/planning-artifacts/ux-design-specification.md</var>
<var name="validation_focus">story_quality</var>
</variables>
<instructions><workflow>
  <critical>SCOPE LIMITATION: You are a READ-ONLY VALIDATOR. Output your validation report to stdout ONLY. Do NOT create files, do NOT modify files, do NOT use Write/Edit/Bash tools. Your stdout output will be captured and saved by the orchestration system.</critical>
  <critical>All configuration and context is available in the VARIABLES section below. Use these resolved values directly.</critical>
  <critical>Communicate all responses in English and generate all documents in English</critical>

  <critical>🔥 CRITICAL MISSION: You are an independent quality validator in a FRESH CONTEXT competing against the original create-story LLM!</critical>
  <critical>Your purpose is to thoroughly review a story file and systematically identify any mistakes, omissions, or disasters that the original LLM missed</critical>
  <critical>🚨 COMMON LLM MISTAKES TO PREVENT: reinventing wheels, wrong libraries, wrong file locations, breaking regressions, ignoring UX, vague implementations, lying about completion, not learning from past work</critical>
  <critical>🔬 UTILIZE SUBPROCESSES AND SUBAGENTS: Use research subagents or parallel processing if available to thoroughly analyze different artifacts simultaneously</critical>

  <step n="1" goal="Story Quality Gate - INVEST validation">
    <critical>🎯 RUTHLESS STORY VALIDATION: Check story quality with surgical precision!</critical>
    <critical>This assessment determines if the story is fundamentally sound before deeper analysis</critical>

    <substep n="1a" title="INVEST Criteria Validation">
      <action>Evaluate each INVEST criterion with severity score (1-10, where 10 is critical violation):</action>

      <action>**I - Independent:** Check if story can be developed independently
        - Does it have hidden dependencies on other stories?
        - Can it be implemented without waiting for other work?
        - Are there circular dependencies?
        Score severity of any violations found
      </action>

      <action>**N - Negotiable:** Check if story allows implementation flexibility
        - Is it overly prescriptive about HOW vs WHAT?
        - Does it leave room for technical decisions?
        - Are requirements stated as outcomes, not solutions?
        Score severity of any violations found
      </action>

      <action>**V - Valuable:** Check if story delivers clear business value
        - Is the benefit clearly stated and meaningful?
        - Does it contribute to epic/product goals?
        - Would stakeholder recognize the value?
        Score severity of any violations found
      </action>

      <action>**E - Estimable:** Check if story can be accurately estimated
        - Are requirements clear enough to estimate?
        - Is scope well-defined without ambiguity?
        - Are there unknown technical risks that prevent estimation?
        Score severity of any violations found
      </action>

      <action>**S - Small:** Check if story is appropriately sized
        - Can it be completed in a single sprint?
        - Is it too large and should be split?
        - Is it too small to be meaningful?
        Score severity of any violations found
      </action>

      <action>**T - Testable:** Check if story has testable acceptance criteria
        - Are acceptance criteria specific and measurable?
        - Can each criterion be verified objectively?
        - Are edge cases and error scenarios covered?
        Score severity of any violations found
      </action>

      <action>Store INVEST results: {{invest_results}} with individual scores</action>
    </substep>

    <substep n="1b" title="Acceptance Criteria Deep Analysis">
      <action>Hunt for acceptance criteria issues:
        - Ambiguous criteria: Vague language like "should work well", "fast", "user-friendly"
        - Untestable criteria: Cannot be objectively verified
        - Missing criteria: Expected behaviors not covered
        - Conflicting criteria: Criteria that contradict each other
        - Incomplete scenarios: Missing edge cases, error handling, boundary conditions
      </action>
      <action>Document each issue with specific quote and recommendation</action>
      <action>Store as {{acceptance_criteria_issues}}</action>
    </substep>

    <substep n="1c" title="Hidden Dependencies Discovery">
      <action>Uncover hidden dependencies and future sprint-killers:
        - Undocumented technical dependencies (libraries, services, APIs)
        - Cross-team dependencies not mentioned
        - Infrastructure dependencies (databases, queues, caches)
        - Data dependencies (migrations, seeds, external data)
        - Sequential dependencies on other stories
        - External blockers (third-party services, approvals)
      </action>
      <action>Document each hidden dependency with impact assessment</action>
      <action>Store as {{hidden_dependencies}}</action>
    </substep>

    <substep n="1d" title="Estimation Reality-Check">
      <action>Reality-check the story estimate against complexity:
        - Compare stated/implied effort vs actual scope
        - Check for underestimated technical complexity
        - Identify scope creep risks
        - Assess if unknown unknowns are accounted for
        - Compare with similar stories from previous work
      </action>
      <action>Provide estimation assessment: realistic / underestimated / overestimated / unestimable</action>
      <action>Store as {{estimation_assessment}}</action>
    </substep>

    <substep n="1e" title="Technical Alignment Verification">
      <action>Verify alignment with /Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/architecture-diagrams.md patterns:
        - Does story follow established architectural patterns?
        - Are correct technologies/frameworks specified?
        - Does it respect defined boundaries and layers?
        - Are naming conventions and file structures aligned?
        - Does it integrate correctly with existing components?
      </action>
      <action>Document any misalignments or conflicts</action>
      <action>Store as {{technical_alignment_issues}}</action>
    </substep>

    <o>🎯 **Story Quality Gate Results:**
      - INVEST Violations: {{invest_violation_count}}
      - Acceptance Criteria Issues: {{ac_issues_count}}
      - Hidden Dependencies: {{hidden_deps_count}}
      - Estimation: {{estimation_assessment}}
      - Technical Alignment: {{alignment_status}}

      ℹ️ Continuing with full analysis...
    </o>
  </step>

  <step n="2" goal="Disaster prevention gap analysis">
    <critical>🚨 CRITICAL: Identify every mistake the original LLM missed that could cause DISASTERS!</critical>

    <substep n="2a" title="Reinvention Prevention Gaps">
      <action>Analyze for wheel reinvention risks:
        - Areas where developer might create duplicate functionality
        - Code reuse opportunities not identified
        - Existing solutions not mentioned that developer should extend
        - Patterns from previous stories not referenced
      </action>
      <action>Document each reinvention risk found</action>
    </substep>

    <substep n="2b" title="Technical Specification Disasters">
      <action>Analyze for technical specification gaps:
        - Wrong libraries/frameworks: Missing version requirements
        - API contract violations: Missing endpoint specifications
        - Database schema conflicts: Missing requirements that could corrupt data
        - Security vulnerabilities: Missing security requirements
        - Performance disasters: Missing requirements that could cause failures
      </action>
      <action>Document each technical specification gap</action>
    </substep>

    <substep n="2c" title="File Structure Disasters">
      <action>Analyze for file structure issues:
        - Wrong file locations: Missing organization requirements
        - Coding standard violations: Missing conventions
        - Integration pattern breaks: Missing data flow requirements
        - Deployment failures: Missing environment requirements
      </action>
      <action>Document each file structure issue</action>
    </substep>

    <substep n="2d" title="Regression Disasters">
      <action>Analyze for regression risks:
        - Breaking changes: Missing requirements that could break existing functionality
        - Test failures: Missing test requirements
        - UX violations: Missing user experience requirements
        - Learning failures: Missing previous story context
      </action>
      <action>Document each regression risk</action>
    </substep>

    <substep n="2e" title="Implementation Disasters">
      <action>Analyze for implementation issues:
        - Vague implementations: Missing details that could lead to incorrect work
        - Completion lies: Missing acceptance criteria that could allow fake implementations
        - Scope creep: Missing boundaries that could cause unnecessary work
        - Quality failures: Missing quality requirements
      </action>
      <action>Document each implementation issue</action>
    </substep>
  </step>

  <step n="3" goal="LLM-Dev-Agent optimization analysis">
    <critical>CRITICAL: Optimize story context for LLM developer agent consumption</critical>

    <action>Analyze current story for LLM optimization issues:
      - Verbosity problems: Excessive detail that wastes tokens without adding value
      - Ambiguity issues: Vague instructions that could lead to multiple interpretations
      - Context overload: Too much information not directly relevant to implementation
      - Missing critical signals: Key requirements buried in verbose text
      - Poor structure: Information not organized for efficient LLM processing
    </action>

    <action>Apply LLM Optimization Principles:
      - Clarity over verbosity: Be precise and direct, eliminate fluff
      - Actionable instructions: Every sentence should guide implementation
      - Scannable structure: Clear headings, bullet points, and emphasis
      - Token efficiency: Pack maximum information into minimum text
      - Unambiguous language: Clear requirements with no room for interpretation
    </action>

    <action>Document each LLM optimization opportunity</action>
  </step>

  <step n="4" goal="Categorize and prioritize improvements">
    <action>Categorize all identified issues into:
      - critical_issues: Must fix - essential requirements, security, blocking issues
      - enhancements: Should add - helpful guidance, better specifications
      - optimizations: Nice to have - performance hints, development tips
      - llm_optimizations: Token efficiency and clarity improvements
    </action>

    <action>Count issues in each category:
      - {{critical_count}} critical issues
      - {{enhancement_count}} enhancements
      - {{optimization_count}} optimizations
      - {{llm_opt_count}} LLM optimizations
    </action>

    <action>Assign numbers to each issue for user selection</action>

    <substep n="4b" title="Calculate Evidence Score">
      <critical>🔥 CRITICAL: You MUST calculate and output the Evidence Score for synthesis!</critical>

      <action>Map each finding to Evidence Score severity:
        - **🔴 CRITICAL** (+3 points): Security vulnerabilities, data corruption risks, blocking issues, missing essential requirements
        - **🟠 IMPORTANT** (+1 point): Missing guidance, unclear specifications, integration risks
        - **🟡 MINOR** (+0.3 points): Typos, style issues, minor clarifications
      </action>

      <action>Count CLEAN PASS categories - areas with NO issues found:
        - Each clean category: -0.5 points
        - Categories to check: INVEST criteria (6), Acceptance Criteria, Dependencies, Technical Alignment, Implementation
      </action>

      <action>Calculate Evidence Score:
        {{evidence_score}} = SUM(finding_scores) + (clean_pass_count × -0.5)

        Example: 2 CRITICAL (+6) + 1 IMPORTANT (+1) + 4 CLEAN PASSES (-2) = 5.0
      </action>

      <action>Determine Evidence Verdict:
        - **EXCELLENT** (score ≤ -3): Many clean passes, minimal issues
        - **PASS** (score &lt; 3): Acceptable quality, minor issues only
        - **MAJOR REWORK** (3 ≤ score &lt; 7): Significant issues require attention
        - **REJECT** (score ≥ 7): Critical problems, needs complete rewrite
      </action>

      <action>Store for template output:
        - {{evidence_findings}}: List of findings with severity_icon, severity, description, source, score
        - {{clean_pass_count}}: Number of clean categories
        - {{evidence_score}}: Calculated total score
        - {{evidence_verdict}}: EXCELLENT/PASS/MAJOR REWORK/REJECT
      </action>
    </substep>
  </step>

  <step n="5" goal="Generate validation report">
    <critical>OUTPUT MARKERS REQUIRED: Your validation report MUST start with the marker <!-- VALIDATION_REPORT_START --> on its own line BEFORE the report header, and MUST end with the marker <!-- VALIDATION_REPORT_END --> on its own line AFTER the final line. The orchestrator extracts ONLY content between these markers. Any text outside the markers (thinking, commentary) will be discarded.</critical>

    <action>Use the output template as a FORMAT GUIDE, replacing all {{placeholders}} with your actual analysis</action>
    <action>Output the complete report to stdout with all sections filled in</action>
    <action>Do NOT save to any file - orchestrator handles persistence</action>
  </step>

</workflow></instructions>
<output-template><![CDATA[

<!-- VALIDATION_REPORT_START -->

# 🎯 Story Context Validation Report

<!-- report_header -->

**Story:** {{story_key}} - {{story_title}}
**Story File:** {{story_file}}
**Validated:** {{date}}
**Validator:** Quality Competition Engine

---

<!-- executive_summary -->

## Executive Summary

### Issues Overview

| Category | Found | Applied |
|----------|-------|---------|
| 🚨 Critical Issues | {{critical_count}} | {{critical_applied}} |
| ⚡ Enhancements | {{enhancement_count}} | {{enhancements_applied}} |
| ✨ Optimizations | {{optimization_count}} | {{optimizations_applied}} |
| 🤖 LLM Optimizations | {{llm_opt_count}} | {{llm_opts_applied}} |

**Overall Assessment:** {{overall_assessment}}

---

<!-- evidence_score_summary -->

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
{{#each evidence_findings}}
| {{severity_icon}} {{severity}} | {{description}} | {{source}} | +{{score}} |
{{/each}}
{{#if clean_pass_count}}
| 🟢 CLEAN PASS | {{clean_pass_count}} |
{{/if}}

### Evidence Score: {{evidence_score}}

| Score | Verdict |
|-------|---------|
| **{{evidence_score}}** | **{{evidence_verdict}}** |

---

<!-- story_quality_gate -->

## 🎯 Ruthless Story Validation {{epic_num}}.{{story_num}}

### INVEST Criteria Assessment

| Criterion | Status | Severity | Details |
|-----------|--------|----------|---------|
| **I**ndependent | {{invest_i_status}} | {{invest_i_severity}}/10 | {{invest_i_details}} |
| **N**egotiable | {{invest_n_status}} | {{invest_n_severity}}/10 | {{invest_n_details}} |
| **V**aluable | {{invest_v_status}} | {{invest_v_severity}}/10 | {{invest_v_details}} |
| **E**stimable | {{invest_e_status}} | {{invest_e_severity}}/10 | {{invest_e_details}} |
| **S**mall | {{invest_s_status}} | {{invest_s_severity}}/10 | {{invest_s_details}} |
| **T**estable | {{invest_t_status}} | {{invest_t_severity}}/10 | {{invest_t_details}} |

### INVEST Violations

{{#each invest_violations}}
- **[{{severity}}/10] {{criterion}}:** {{description}}
{{/each}}

{{#if no_invest_violations}}
✅ No significant INVEST violations detected.
{{/if}}

### Acceptance Criteria Issues

{{#each acceptance_criteria_issues}}
- **{{issue_type}}:** {{description}}
  - *Quote:* "{{quote}}"
  - *Recommendation:* {{recommendation}}
{{/each}}

{{#if no_acceptance_criteria_issues}}
✅ Acceptance criteria are well-defined and testable.
{{/if}}

### Hidden Risks and Dependencies

{{#each hidden_dependencies}}
- **{{dependency_type}}:** {{description}}
  - *Impact:* {{impact}}
  - *Mitigation:* {{mitigation}}
{{/each}}

{{#if no_hidden_dependencies}}
✅ No hidden dependencies or blockers identified.
{{/if}}

### Estimation Reality-Check

**Assessment:** {{estimation_assessment}}

{{estimation_details}}

### Technical Alignment

**Status:** {{technical_alignment_status}}

{{#each technical_alignment_issues}}
- **{{issue_type}}:** {{description}}
  - *Architecture Reference:* {{architecture_reference}}
  - *Recommendation:* {{recommendation}}
{{/each}}

{{#if no_technical_alignment_issues}}
✅ Story aligns with architecture.md patterns.
{{/if}}

### Evidence Score: {{evidence_score}} → {{evidence_verdict}}

---

<!-- critical_issues_section -->

## 🚨 Critical Issues (Must Fix)

These are essential requirements, security concerns, or blocking issues that could cause implementation disasters.

{{#each critical_issues}}
### {{number}}. {{title}}

**Impact:** {{impact}}
**Source:** {{source_reference}}

**Problem:**
{{problem_description}}

**Recommended Fix:**
{{recommended_fix}}

{{/each}}

{{#if no_critical_issues}}
✅ No critical issues found - the original story covered essential requirements.
{{/if}}

---

<!-- enhancements_section -->

## ⚡ Enhancement Opportunities (Should Add)

Additional guidance that would significantly help the developer avoid mistakes.

{{#each enhancements}}
### {{number}}. {{title}}

**Benefit:** {{benefit}}
**Source:** {{source_reference}}

**Current Gap:**
{{gap_description}}

**Suggested Addition:**
{{suggested_addition}}

{{/each}}

{{#if no_enhancements}}
✅ No significant enhancement opportunities identified.
{{/if}}

---

<!-- optimizations_section -->

## ✨ Optimizations (Nice to Have)

Performance hints, development tips, and additional context for complex scenarios.

{{#each optimizations}}
### {{number}}. {{title}}

**Value:** {{value}}

**Suggestion:**
{{suggestion}}

{{/each}}

{{#if no_optimizations}}
✅ No additional optimizations identified.
{{/if}}

---

<!-- llm_optimizations_section -->

## 🤖 LLM Optimization Improvements

Token efficiency and clarity improvements for better dev agent processing.

{{#each llm_optimizations}}
### {{number}}. {{title}}

**Issue:** {{issue_type}}
**Token Impact:** {{token_impact}}

**Current:**
```
{{current_text}}
```

**Optimized:**
```
{{optimized_text}}
```

**Rationale:** {{rationale}}

{{/each}}

{{#if no_llm_optimizations}}
✅ Story content is well-optimized for LLM processing.
{{/if}}

---

<!-- changes_applied_section -->

## 📝 Changes Applied

{{#if changes_applied}}
The following improvements were applied to the story file:

{{#each applied_changes}}
- ✅ **{{category}}:** {{title}}
{{/each}}

**Total Changes:** {{changes_applied_count}}

**Updated Sections:**
{{#each updated_sections}}
- {{section_name}}
{{/each}}
{{/if}}

{{#if no_changes_applied}}
No changes were applied to the story file. This report serves as documentation only.
{{/if}}

---

<!-- competition_results -->

## 🏆 Competition Results

### Quality Metrics

| Metric | Score |
|--------|-------|
| Requirements Coverage | {{requirements_coverage}}% |
| Architecture Alignment | {{architecture_alignment}}% |
| Previous Story Integration | {{previous_story_integration}}% |
| LLM Optimization Score | {{llm_optimization_score}}% |
| **Overall Quality Score** | **{{overall_quality_score}}%** |

### Disaster Prevention Assessment

{{#each disaster_categories}}
- **{{category}}:** {{status}} {{details}}
{{/each}}

### Competition Outcome

{{#if validator_won}}
🏆 **Validator identified {{total_issues}} improvements** that enhance the story context.
{{/if}}

{{#if original_won}}
✅ **Original create-story produced high-quality output** with minimal gaps identified.
{{/if}}

---

**Report Generated:** {{date}}
**Validation Engine:** BMAD Method Quality Competition v1.0

<!-- VALIDATION_REPORT_END -->

]]></output-template>
</compiled-workflow>