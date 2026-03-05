<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 12 -->
<!-- Story: 2 -->
<!-- Phase: validate-story -->
<!-- Timestamp: 20260305T195602Z -->
<compiled-workflow>
<mission><![CDATA[

Adversarial Story Validation

Target: Story 12.2 - implement-portfolio-compatibility-validation-and-conflict-resolution

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
<file id="d908788b" path="_bmad-output/implementation-artifacts/12-1-define-policyportfolio-dataclass-and-composition-logic.md" label="STORY FILE"><![CDATA[

# Story 12.1: Define PolicyPortfolio dataclass and composition logic

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a policy analyst,
I want to compose multiple individual policy templates into a named policy portfolio,
so that I can run simulations with bundled policies applied together and compare comprehensive policy packages.

## Acceptance Criteria

1. **AC1: Frozen dataclass composition** — Given 2+ individual `PolicyConfig` objects, when composed into a `PolicyPortfolio`, then the portfolio is a named, frozen dataclass containing all policies in the order provided.
   
2. **AC2: Policy inspection** — Given a portfolio, when inspected, then it lists all constituent policies with their types and parameter summaries in deterministic order.

3. **AC3: YAML round-trip** — Given a portfolio, when serialized to YAML and reloaded, then the round-trip produces an identical object using dataclass equality, with preserved policy order and default field values.

4. **AC4: Validation error handling** — Given invalid portfolio inputs (fewer than 2 policies, invalid YAML structure, missing required fields), when construction or loading is attempted, then clear `PortfolioError` exceptions are raised with field-level error messages.

5. **AC5: Deterministic serialization** — Given two identical portfolios, when serialized to YAML, then the output is byte-for-byte identical (canonical ordering, stable key order, deterministic formatting).

## Tasks / Subtasks

- [ ] **Task 1: Define PolicyPortfolio frozen dataclass** (AC: #1)
  - [ ] 1.1 Create `src/reformlab/templates/portfolios/` directory structure
  - [ ] 1.2 Create `__init__.py` with module docstring
  - [ ] 1.3 Create `portfolio.py` with `PolicyPortfolio` frozen dataclass
  - [ ] 1.4 Define fields: `name: str`, `policies: tuple[PolicyConfig, ...]`, `version: str`, `description: str`
  - [ ] 1.5 Add `__post_init__` validation (at least 2 policies required)
  - [ ] 1.6 Add property methods: `policy_types`, `policy_count`, `policy_summaries`
  - [ ] 1.7 Add `__repr__` for notebook-friendly display

- [ ] **Task 2: Define PolicyConfig wrapper type** (AC: #1, #2)
  - [ ] 2.1 Analyze existing `PolicyParameters` and `ScenarioTemplate` structures
  - [ ] 2.2 Create `PolicyConfig` as a new frozen dataclass (NOT an alias)
  - [ ] 2.3 Define fields: `policy_type: PolicyType`, `policy: PolicyParameters`, `name: str = ""`
  - [ ] 2.4 Add `get_summary() -> dict[str, Any]` method to extract policy type and parameter summary
  - [ ] 2.5 Add `__post_init__` to validate `policy` matches declared `policy_type`
  - [ ] 2.6 Ensure `PolicyConfig` integrates with existing `BaselineScenario` and `ReformScenario`

- [ ] **Task 3: Implement portfolio inspection methods** (AC: #2)
  - [ ] 3.1 Add `list_policies() -> list[dict[str, Any]]` method
  - [ ] 3.2 Each policy dict includes: name, type, rate_schedule summary, key parameters
  - [ ] 3.3 Add `get_policy_by_type(policy_type: PolicyType) -> PolicyConfig | None`
  - [ ] 3.4 Add `has_policy_type(policy_type: PolicyType) -> bool`
  - [ ] 3.5 Ensure methods work with frozen dataclass (no mutation, return new values)

- [ ] **Task 4: Implement YAML serialization** (AC: #3, #5)
  - [ ] 4.1 Create `composition.py` module in `portfolios/` directory
  - [ ] 4.2 Implement `portfolio_to_dict(portfolio: PolicyPortfolio) -> dict[str, Any]` with deterministic key ordering
  - [ ] 4.3 Implement `dict_to_portfolio(data: dict[str, Any]) -> PolicyPortfolio`
  - [ ] 4.4 Add `dump_portfolio(portfolio: PolicyPortfolio, path: Path) -> None` with canonical YAML formatting
  - [ ] 4.5 Add `load_portfolio(path: Path) -> PolicyPortfolio` with jsonschema validation
  - [ ] 4.6 Create schema file at `src/reformlab/templates/schema/portfolio.schema.json` with `version` field
  - [ ] 4.7 Include `$schema` reference in dumped YAML files for IDE validation support

- [ ] **Task 5: Add validation and error handling** (AC: #1, #2, #3, #4)
  - [ ] 5.1 Validate portfolio has at least 2 policies on construction
  - [ ] 5.2 OUT OF SCOPE: Cross-policy year schedule compatibility validation (deferred to future story)
  - [ ] 5.3 Create `PortfolioError` exception in `exceptions.py` with subclasses for validation vs serialization errors
  - [ ] 5.4 Add clear error messages for invalid portfolios (missing policies, missing required fields)
  - [ ] 5.5 Validate YAML structure on load with field-level error messages using `jsonschema` library
  - [ ] 5.6 Create schema file at `src/reformlab/templates/schema/portfolio.schema.json`

- [ ] **Task 6: Write comprehensive tests** (AC: #1, #2, #3, #4, #5)
  - [ ] 6.1 Create `tests/templates/portfolios/` directory
  - [ ] 6.2 Create `conftest.py` with portfolio fixtures
  - [ ] 6.3 Create `test_portfolio.py` for dataclass tests
  - [ ] 6.4 Create `test_composition.py` for YAML serialization tests
  - [ ] 6.5 Test frozen dataclass immutability
  - [ ] 6.6 Test inspection methods return correct summaries in deterministic order
  - [ ] 6.7 Test YAML round-trip produces identical objects using dataclass equality
  - [ ] 6.8 Test error cases: <2 policies raises PortfolioError, invalid YAML structure, missing required fields
  - [ ] 6.9 Test deterministic serialization: identical portfolios produce byte-identical YAML
  - [ ] 6.10 Run `uv run pytest tests/templates/portfolios/ --cov=src/reformlab/templates/portfolios --cov-report=term-missing` to verify >90% coverage

- [ ] **Task 7: Update module exports** (AC: #1, #2, #3)
  - [ ] 7.1 Update `src/reformlab/templates/portfolios/__init__.py` exports
  - [ ] 7.2 Update `src/reformlab/templates/__init__.py` to export portfolio types
  - [ ] 7.3 Ensure imports follow `from __future__ import annotations` pattern
  - [ ] 7.4 Use `TYPE_CHECKING` guards for type-only imports

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**Frozen dataclass is NON-NEGOTIABLE** — All domain types in ReformLab use `@dataclass(frozen=True)`. This is a core architectural decision [Source: project-context.md#architecture-framework-rules].

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from reformlab.templates.schema import PolicyParameters, PolicyType

@dataclass(frozen=True)
class PolicyConfig:
    """Wrapper for policy parameters with metadata for portfolio composition."""
    policy_type: PolicyType
    policy: PolicyParameters
    name: str = ""
    
    def get_summary(self) -> dict[str, Any]:
        """Extract policy type and key parameter summary."""
        return {
            "name": self.name,
            "type": self.policy_type.value,
            "rate_schedule_years": sorted(self.policy.rate_schedule.keys()),
        }

@dataclass(frozen=True)
class PolicyPortfolio:
    """Named, versioned collection of policy configurations."""
    name: str
    policies: tuple[PolicyConfig, ...]  # tuple for immutability
    version: str = "1.0"
    description: str = ""
```

**Use `tuple` not `list`** — Function parameters and return types that are ordered-and-fixed use `tuple`, not `list` [Source: project-context.md#python-language-rules].

**No ABCs, use Protocols** — Interfaces are `Protocol` + `@runtime_checkable`, not abstract base classes [Source: project-context.md#python-language-rules].

### Existing Schema Analysis

**Current `PolicyParameters` hierarchy** [Source: src/reformlab/templates/schema.py]:
```python
from dataclasses import dataclass, field

@dataclass(frozen=True)
class PolicyParameters:
    """Base class for policy-specific parameters."""
    rate_schedule: dict[int, float]
    exemptions: tuple[dict[str, Any], ...] = ()
    thresholds: tuple[dict[str, Any], ...] = ()
    covered_categories: tuple[str, ...] = ()

@dataclass(frozen=True)
class CarbonTaxParameters(PolicyParameters):
    redistribution_type: str = ""
    income_weights: dict[str, float] = field(default_factory=dict)

# Similar: SubsidyParameters, RebateParameters, FeebateParameters
```

**Current `ScenarioTemplate` structure** [Source: src/reformlab/templates/schema.py:192-213]:
```python
@dataclass(frozen=True)
class ScenarioTemplate:
    """Base scenario template shape."""
    name: str
    year_schedule: YearSchedule
    policy: PolicyParameters
    policy_type: PolicyType | None = None  # Inferred if None
    description: str = ""
    version: str = "1.0"
    schema_ref: str = ""
```

**Design decision: `PolicyConfig` is a new frozen dataclass wrapper** — Option 2 from the list below is required. This allows naming individual policies within a portfolio and extracting summaries without modifying existing scenario templates. Aliases are NOT acceptable.

**Previous design options considered:**
1. An alias for `PolicyParameters`? (REJECTED - insufficient for portfolio needs)
2. A new wrapper containing `PolicyParameters` + metadata? (REQUIRED - provides needed flexibility)
3. A reference to `ScenarioTemplate`? (REJECTED - creates unnecessary coupling)

### YAML Serialization Pattern

**Follow existing loader patterns** [Source: src/reformlab/templates/loader.py]:
- Schema version field: `version: "1.0"`
- `$schema` reference for IDE validation
- `load_portfolio(path: Path) -> PolicyPortfolio`
- `dump_portfolio(portfolio: PolicyPortfolio, path: Path) -> None`
- Clear `ScenarioError` or `PortfolioError` on validation failures

**Deterministic serialization requirements** [Source: project-context.md#critical-dont-miss-rules]:
- Use `jsonschema` library for YAML validation on load (consistent with project stack)
- Sort dictionary keys alphabetically in output
- Use canonical YAML formatting (consistent indentation, no trailing spaces)
- Preserve policy order from tuple (do not reorder)
- Round-trip equality must include order preservation

**Example YAML structure** (proposed):
```yaml
$schema: "../schema/portfolio.schema.json"
version: "1.0"

name: "Green Transition 2030"
description: >
  Comprehensive climate policy package combining carbon pricing,
  vehicle incentives, and home renovation subsidies.

policies:
  - name: "Carbon Tax Component"
    policy_type: carbon_tax
    policy:
      rate_schedule:
        2026: 44.60
        2027: 50.00
        # ... (full policy parameters)
      redistribution_type: lump_sum
      
  - name: "EV Bonus"
    policy_type: subsidy
    policy:
      rate_schedule:
        2026: 5000.0
        2027: 5000.0
        # ... (full policy parameters)
      eligible_categories:
        - electric_vehicle
```

### Testing Standards

**Mirror source structure** [Source: project-context.md#testing-rules]:
```
tests/templates/portfolios/
├── __init__.py
├── conftest.py          ← fixtures: sample portfolios, policy configs
├── test_portfolio.py    ← dataclass construction, inspection methods
└── test_composition.py  ← YAML serialization, round-trip, validation
```

**Class-based test grouping** [Source: project-context.md]:
```python
class TestPolicyPortfolioConstruction:
    """Tests for portfolio creation and validation (AC #1)."""
    
class TestPolicyPortfolioInspection:
    """Tests for policy listing and summaries (AC #2)."""
    
class TestPolicyPortfolioYAML:
    """Tests for YAML serialization round-trip (AC #3)."""
```

**Direct assertions, no helpers** [Source: project-context.md]:
```python
def test_portfolio_requires_two_policies(self) -> None:
    """Portfolio with <2 policies raises clear error."""
    with pytest.raises(PortfolioError, match="at least 2 policies"):
        PolicyPortfolio(
            name="invalid",
            policies=(policy_1,),  # Only 1 policy
        )
```

### File Structure

**New directory** [Source: architecture.md#phase-2-architecture-extensions]:
```
src/reformlab/templates/
├── portfolios/
│   ├── __init__.py
│   ├── portfolio.py     ← PolicyPortfolio frozen dataclass
│   ├── composition.py   ← YAML serialization, validation
│   └── exceptions.py    ← PortfolioError hierarchy
```

**Exception taxonomy** — Create exception hierarchy consistent with project patterns:
```python
class PortfolioError(Exception):
    """Base exception for portfolio-related errors."""
    pass

class PortfolioValidationError(PortfolioError):
    """Raised when portfolio structure or policy configuration is invalid."""
    pass

class PortfolioSerializationError(PortfolioError):
    """Raised when YAML serialization or deserialization fails."""
    pass
```

**Update exports** in:
- `src/reformlab/templates/portfolios/__init__.py`
- `src/reformlab/templates/__init__.py` (add portfolio types to `__all__`)

### Integration with Existing Code

**Scope boundaries** — This story focuses on data structure and serialization ONLY:
- ✅ IN SCOPE: PolicyPortfolio frozen dataclass, PolicyConfig wrapper, YAML serialization, basic validation
- ❌ OUT OF SCOPE: Cross-policy year schedule compatibility checks (future story)
- ❌ OUT OF SCOPE: Orchestrator integration (Story 12.3)
- ❌ OUT OF SCOPE: Conflict resolution or policy compatibility logic

**Scenario Registry compatibility** — Portfolios will eventually be stored in the scenario registry alongside individual scenarios [Source: architecture.md#extension-policy-portfolio-layer]. Design `PolicyPortfolio` to be registry-friendly:
- Include `version` field for versioning
- Include `name` field for registry lookup
- Follow same immutability patterns as `BaselineScenario` and `ReformScenario`

**Orchestrator integration** — The orchestrator will receive a portfolio instead of a single policy [Source: architecture.md#extension-policy-portfolio-layer]. This is Story 12.3, not this story. Design `PolicyPortfolio` to expose the policies list in a way that's easy for the orchestrator to iterate.

### Project Structure Notes

- **Alignment with unified project structure:** New `portfolios/` subdirectory follows existing template subsystem pattern (similar to `carbon_tax/`, `subsidy/`, etc.)
- **Naming convention:** `portfolio.py` and `composition.py` follow `snake_case.py` convention
- **Module docstrings:** Every module needs a docstring explaining its role [Source: project-context.md#code-quality-style-rules]

### Critical Don't-Miss Rules

1. **Every file starts with `from __future__ import annotations`** — no exceptions [Source: project-context.md#python-language-rules]
2. **Use `if TYPE_CHECKING:` guards** for imports only needed for annotations [Source: project-context.md#python-language-rules]
3. **All domain types are frozen** — never add a mutable dataclass [Source: project-context.md#critical-dont-miss-rules]
4. **Determinism is non-negotiable** — portfolio construction and serialization must be deterministic [Source: project-context.md#critical-dont-miss-rules]
5. **No wildcard imports** — always import specific names [Source: project-context.md#code-quality-style-rules]

### References

**Architecture:**
- [Source: architecture.md#phase-2-architecture-extensions] — Policy Portfolio Layer design
- [Source: architecture.md#extension-policy-portfolio-layer] — Portfolio composition and orchestrator integration

**PRD:**
- [Source: prd.md#phase-2-policy-portfolios] — FR43-FR46 functional requirements
- [Source: prd.md#product-scope-post-mvp-features] — Phase 2 feature table

**Existing Code:**
- [Source: src/reformlab/templates/schema.py] — Existing `PolicyParameters`, `ScenarioTemplate` structures
- [Source: src/reformlab/templates/loader.py] — YAML serialization patterns
- [Source: src/reformlab/templates/registry.py] — Registry patterns for versioned artifacts

**Testing:**
- [Source: tests/templates/test_loader.py] — Example test patterns for YAML serialization
- [Source: tests/templates/test_registry.py] — Example test patterns for versioned artifacts

**Project Context:**
- [Source: project-context.md#architecture-framework-rules] — Frozen dataclasses, Protocols, step pipeline
- [Source: project-context.md#testing-rules] — Test structure, fixtures, assertions
- [Source: project-context.md#code-quality-style-rules] — ruff, mypy, naming conventions

## Dev Agent Record

### Agent Model Used

GLM-5 (zai-coding-plan/glm-5)

### Debug Log References

Code review synthesis performed on 2026-03-05. Fixed critical immutability breach and high-priority integration/validation issues.

### Completion Notes List

**Code Review Synthesis (2026-03-05):**
- Fixed CRITICAL immutability breach: `list_policies()` now returns defensive copy of rate_schedule dict instead of direct reference
- Fixed HIGH package integration: Added PolicyConfig, PolicyPortfolio, and portfolio exceptions to templates/__init__.py exports
- Fixed HIGH schema validation: Added `additionalProperties: false` to portfolio.schema.json (root, policy item, policy.parameters) to prevent typos/unknown fields from being silently accepted
- Fixed HIGH test data format: Updated test_dict_to_portfolio_basic to use canonical nested `redistribution` format instead of legacy flat format
- Fixed MEDIUM lint issues: Removed unused `yaml` import from test_composition.py, removed unused `PolicyType` import from conftest.py, removed unused `lines` variable from test_deterministic_key_ordering
- All ruff checks pass
- 41/47 tests pass (6 pre-existing failures in TestPortfolioErrorHandling - these expect field-specific error messages but jsonschema provides generic type errors; validation IS working, just error message format differs)

**Deferred items:**
- Story task checkboxes not updated (outside scope of code fixes - would require modifying story file context)
- 6 error handling tests failing (pre-existing issue - validation works but error message format doesn't match test expectations)
- Type checker warning at test_composition.py:472 (pre-existing - accessing income_weights on PolicyParameters base class)

### File List

**Source code files modified:**
- src/reformlab/templates/portfolios/portfolio.py (immutability fix)
- src/reformlab/templates/__init__.py (export additions)
- src/reformlab/templates/schema/portfolio.schema.json (strict validation)
- tests/templates/portfolios/test_composition.py (format fix, lint fixes)
- tests/templates/portfolios/conftest.py (lint fix)

## Senior Developer Review (AI)

### Review: 2026-03-05
- **Reviewer:** AI Code Review Synthesis
- **Evidence Score:** 7.2 → REJECT
- **Issues Found:** 8
- **Issues Fixed:** 5
- **Action Items Created:** 3

#### Review Follow-ups (AI)
- [ ] [AI-Review] MEDIUM: Improve error handling tests - update test expectations to match jsonschema error message format or use field-specific error extraction from jsonschema.ValidationError (tests/templates/portfolios/test_composition.py:497,516,536,558,578,598)
- [ ] [AI-Review] MEDIUM: Fix type checker warning - add type assertion or cast for income_weights access on RebateParameters (tests/templates/portfolios/test_composition.py:472)
- [ ] [AI-Review] LOW: Consider strengthening test_deterministic_key_ordering to validate actual key ordering, not just presence (tests/templates/portfolios/test_composition.py:249-254)


]]></file>
<file id="38e1067d" path="_bmad-output/implementation-artifacts/12-2-implement-portfolio-compatibility-validation-and-conflict-resolution.md" label="STORY FILE"><![CDATA[



# Story 12.2: Implement portfolio compatibility validation and conflict resolution

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a policy analyst,
I want to detect and resolve conflicts when multiple policies in a portfolio affect the same household attributes,
so that I can ensure coherent policy combinations and prevent unintended interactions during simulation runs.

## Acceptance Criteria

1. **AC1: Conflict detection for same policy type** — Given two policies of the same type in a portfolio (e.g., two carbon taxes), when validated, then a conflict is detected and reported with the exact policy names and conflicting parameters.

2. **AC2: Non-conflicting portfolio validation** — Given a portfolio with non-conflicting policies (e.g., carbon tax + vehicle subsidy), when validated, then validation passes with no conflicts reported.

3. **AC3: Resolution strategy application** — Given a conflict and an explicit resolution strategy ("sum", "first_wins", "last_wins", "max"), when the portfolio is validated or executed, then the conflict is resolved according to the strategy and the resolution is recorded in portfolio metadata.

4. **AC4: Execution blocking for unresolved conflicts** — Given an unresolvable conflict with resolution strategy "error" (default), when the portfolio is executed, then it fails before computation with a clear error listing all conflicting policies, parameters, and suggested resolution strategies.

5. **AC5: Deterministic conflict resolution** — Given identical portfolios and resolution strategies, when validated/executed multiple times, then conflict detection and resolution produce identical results (deterministic ordering, stable output).

## Tasks / Subtasks

- [ ] **Task 1: Define conflict detection data structures** (AC: #1, #5)
  - [ ] 1.1 Create `Conflict` frozen dataclass in `composition.py` with fields: `conflict_type`, `policy_indices`, `parameter_name`, `conflicting_values`, `description`
  - [ ] 1.2 Create `ConflictType` enum: `SAME_POLICY_TYPE`, `OVERLAPPING_CATEGORIES`, `OVERLAPPING_YEARS`, `PARAMETER_MISMATCH`
  - [ ] 1.3 Add `__repr__` for readable conflict descriptions
  - [ ] 1.4 Ensure frozen dataclass pattern with `from __future__ import annotations`

- [ ] **Task 2: Add resolution strategy field to PolicyPortfolio** (AC: #3, #5)
  - [ ] 2.1 Add `resolution_strategy: str = "error"` field to `PolicyPortfolio` dataclass
  - [ ] 2.2 Create `ResolutionStrategy` enum in `composition.py`: `ERROR`, `SUM`, `FIRST_WINS`, `LAST_WINS`, `MAX`
  - [ ] 2.3 Validate resolution_strategy in `__post_init__` (must be valid enum value)
  - [ ] 2.4 Update YAML serialization in `composition.py` to include resolution_strategy field
  - [ ] 2.5 Update portfolio.schema.json to include resolution_strategy field with enum validation
  - [ ] 2.6 Ensure round-trip preserves resolution_strategy value

- [ ] **Task 3: Implement conflict detection logic** (AC: #1, #2, #5)
  - [ ] 3.1 Create `validate_compatibility(portfolio: PolicyPortfolio) -> tuple[Conflict, ...]` function
  - [ ] 3.2 Detect `SAME_POLICY_TYPE` conflicts: two policies with same PolicyType
  - [ ] 3.3 Detect `OVERLAPPING_CATEGORIES` conflicts: overlapping covered_categories or eligible_categories
  - [ ] 3.4 Detect `OVERLAPPING_YEARS` conflicts: overlapping years in rate_schedule dictionaries
  - [ ] 3.5 Detect `PARAMETER_MISMATCH` conflicts: same category affected by different parameters
  - [ ] 3.6 Ensure deterministic conflict ordering (sorted by policy indices, then parameter name)
  - [ ] 3.7 Return empty tuple for non-conflicting portfolios

- [ ] **Task 4: Implement conflict resolution logic** (AC: #3, #4, #5)
  - [ ] 4.1 Create `resolve_conflicts(portfolio: PolicyPortfolio, conflicts: tuple[Conflict, ...]) -> PolicyPortfolio` function
  - [ ] 4.2 Implement "error" strategy: raise `PortfolioValidationError` if any conflicts exist
  - [ ] 4.3 Implement "sum" strategy: add rate values for overlapping years
  - [ ] 4.4 Implement "first_wins" strategy: use first policy's values for conflicts
  - [ ] 4.5 Implement "last_wins" strategy: use last policy's values for conflicts
  - [ ] 4.6 Implement "max" strategy: use maximum rate for overlapping years
  - [ ] 4.7 Return new PolicyPortfolio with resolved policies (frozen dataclass → create new instance)
  - [ ] 4.8 Record resolution metadata in description or new metadata field
  - [ ] 4.9 Ensure deterministic resolution (stable ordering, identical results for identical inputs)

- [ ] **Task 5: Integrate validation into portfolio loading** (AC: #4)
  - [ ] 5.1 Update `load_portfolio()` to call `validate_compatibility()` after loading
  - [ ] 5.2 Add optional parameter `validate: bool = True` to `load_portfolio()`
  - [ ] 5.3 If conflicts exist and resolution_strategy is "error", raise `PortfolioValidationError` with conflict details
  - [ ] 5.4 If conflicts exist and resolution_strategy is not "error", log warning with conflict summary
  - [ ] 5.5 Include suggested resolution strategies in error messages

- [ ] **Task 6: Write comprehensive tests** (AC: #1, #2, #3, #4, #5)
  - [ ] 6.1 Create `tests/templates/portfolios/test_conflicts.py` for conflict detection tests
  - [ ] 6.2 Test `SAME_POLICY_TYPE` conflict detection with two carbon taxes
  - [ ] 6.3 Test `OVERLAPPING_CATEGORIES` conflict detection with overlapping covered_categories
  - [ ] 6.4 Test `OVERLAPPING_YEARS` conflict detection with overlapping rate_schedule years
  - [ ] 6.5 Test non-conflicting portfolio (carbon tax + subsidy) passes validation
  - [ ] 6.6 Test "error" strategy raises exception with clear conflict details
  - [ ] 6.7 Test "sum" strategy adds rates for overlapping years
  - [ ] 6.8 Test "first_wins" strategy uses first policy values
  - [ ] 6.9 Test "last_wins" strategy uses last policy values
  - [ ] 6.10 Test "max" strategy uses maximum rate
  - [ ] 6.11 Test deterministic conflict ordering (sorted by indices, then parameter)
  - [ ] 6.12 Test deterministic resolution (identical results for identical inputs)
  - [ ] 6.13 Test YAML round-trip preserves resolution_strategy
  - [ ] 6.14 Test error messages include suggested resolution strategies
  - [ ] 6.15 Run `uv run pytest tests/templates/portfolios/ --cov=src/reformlab/templates/portfolios --cov-report=term-missing` to verify >90% coverage

- [ ] **Task 7: Update module exports and documentation** (AC: #1, #2, #3, #4)
  - [ ] 7.1 Export `Conflict`, `ConflictType`, `ResolutionStrategy` from `portfolios/__init__.py`
  - [ ] 7.2 Export `validate_compatibility`, `resolve_conflicts` from `portfolios/__init__.py`
  - [ ] 7.3 Update `templates/__init__.py` to export conflict types
  - [ ] 7.4 Add module docstring to `composition.py` explaining conflict detection and resolution
  - [ ] 7.5 Add inline code comments explaining resolution strategy semantics

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**Frozen dataclass is NON-NEGOTIABLE** — `Conflict` and all new types must use `@dataclass(frozen=True)`. Resolution functions return NEW PolicyPortfolio instances, never mutate existing ones [Source: project-context.md#architecture-framework-rules].

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from reformlab.templates.portfolios.portfolio import PolicyPortfolio

class ConflictType(Enum):
    """Types of conflicts that can occur in a portfolio."""
    SAME_POLICY_TYPE = "same_policy_type"
    OVERLAPPING_CATEGORIES = "overlapping_categories"
    OVERLAPPING_YEARS = "overlapping_years"
    PARAMETER_MISMATCH = "parameter_mismatch"

class ResolutionStrategy(Enum):
    """Strategies for resolving portfolio conflicts."""
    ERROR = "error"
    SUM = "sum"
    FIRST_WINS = "first_wins"
    LAST_WINS = "last_wins"
    MAX = "max"

@dataclass(frozen=True)
class Conflict:
    """Represents a detected conflict between policies in a portfolio."""
    conflict_type: ConflictType
    policy_indices: tuple[int, ...]  # Indices of conflicting policies
    parameter_name: str  # e.g., "rate_schedule", "covered_categories"
    conflicting_values: tuple[Any, ...]  # The actual conflicting values
    description: str  # Human-readable description
```

**Use `tuple` not `list`** — All ordered collections in conflict detection use `tuple` for immutability [Source: project-context.md#python-language-rules].

**Determinism is NON-NEGOTIABLE** — Conflict detection and resolution must be deterministic:
- Conflicts sorted by policy indices (ascending), then parameter name (alphabetical)
- Resolution produces identical results for identical inputs
- No random or unordered iteration (use sorted() where needed)

### Existing Code Integration

**PolicyPortfolio structure** [Source: src/reformlab/templates/portfolios/portfolio.py]:
```python
@dataclass(frozen=True)
class PolicyPortfolio:
    name: str
    policies: tuple[PolicyConfig, ...]
    version: str = "1.0"
    description: str = ""
    # NEW FIELD: resolution_strategy: str = "error"
```

**PolicyConfig structure** [Source: src/reformlab/templates/portfolios/portfolio.py]:
```python
@dataclass(frozen=True)
class PolicyConfig:
    policy_type: PolicyType
    policy: PolicyParameters
    name: str = ""
```

**PolicyParameters hierarchy** [Source: src/reformlab/templates/schema.py]:
- All policies: `rate_schedule`, `exemptions`, `thresholds`, `covered_categories`
- CarbonTaxParameters: `redistribution_type`, `income_weights`
- SubsidyParameters: `eligible_categories`, `income_caps`
- RebateParameters: `rebate_type`, `income_weights`
- FeebateParameters: `pivot_point`, `fee_rate`, `rebate_rate`

### Conflict Detection Logic

**SAME_POLICY_TYPE conflicts:**
- Detect when two policies have identical `PolicyType` values
- Example: Two `PolicyType.CARBON_TAX` policies
- Conflicting parameter: `"policy_type"`
- Conflicting values: tuple of the two policy names or indices

**OVERLAPPING_CATEGORIES conflicts:**
- Detect overlapping `covered_categories` or `eligible_categories`
- Example: Carbon tax covers ["transport", "heating"] and subsidy covers ["heating", "electricity"]
- Overlap: "heating"
- Conflicting parameter: `"covered_categories"` or `"eligible_categories"`

**OVERLAPPING_YEARS conflicts:**
- Detect overlapping years in `rate_schedule` dictionaries
- Example: Policy A has rates for 2026-2028, Policy B has rates for 2027-2029
- Overlap: 2027, 2028
- Conflicting parameter: `"rate_schedule"`

**PARAMETER_MISMATCH conflicts:**
- Detect when same category has different parameter values
- Example: Two policies affect "transport" but with different income_caps
- Conflicting parameter: specific parameter name (e.g., `"income_caps"`)

### Resolution Strategy Semantics

**"error" (default):**
- Raise `PortfolioValidationError` if ANY conflicts exist
- Error message includes: conflict type, policy names, parameter name, conflicting values
- Suggested resolution strategies in error message: "Consider using resolution_strategy: 'sum', 'first_wins', 'last_wins', or 'max'"

**"sum":**
- For `OVERLAPPING_YEARS` conflicts: add rate values for overlapping years
- Example: Policy A rate 2027 = 50, Policy B rate 2027 = 30 → resolved rate = 80
- Only applies to numeric rate values
- For other conflict types: treat as "error" (cannot sum non-numeric values)

**"first_wins":**
- Use first policy's values for all conflicts
- Example: Policy A (index 0) vs Policy B (index 1) → use Policy A's values
- Preserves first policy's rate_schedule, categories, parameters

**"last_wins":**
- Use last policy's values for all conflicts
- Example: Policy A (index 0) vs Policy B (index 1) → use Policy B's values
- Preserves last policy's rate_schedule, categories, parameters

**"max":**
- For `OVERLAPPING_YEARS` conflicts: use maximum rate for overlapping years
- Example: Policy A rate 2027 = 50, Policy B rate 2027 = 30 → resolved rate = 50
- Only applies to numeric rate values
- For other conflict types: treat as "error" (cannot take max of non-numeric values)

### Resolution Implementation Pattern

**Creating new PolicyPortfolio with resolved policies:**
```python
def resolve_conflicts(
    portfolio: PolicyPortfolio, 
    conflicts: tuple[Conflict, ...]
) -> PolicyPortfolio:
    """Resolve conflicts and return new portfolio with resolved policies."""
    if portfolio.resolution_strategy == "error":
        if conflicts:
            raise PortfolioValidationError(
                summary="Unresolved portfolio conflicts",
                reason=f"{len(conflicts)} conflicts detected",
                fix="Set resolution_strategy to 'sum', 'first_wins', 'last_wins', or 'max'",
                invalid_fields=tuple(f"policies[{c.policy_indices[0]}]" for c in conflicts),
            )
        return portfolio  # No conflicts, return as-is
    
    # Apply resolution strategy
    resolved_policies = _apply_resolution_strategy(
        portfolio.policies, 
        conflicts, 
        portfolio.resolution_strategy
    )
    
    # Create new portfolio with resolved policies
    return PolicyPortfolio(
        name=portfolio.name,
        policies=resolved_policies,
        version=portfolio.version,
        description=f"{portfolio.description}\n\nResolved {len(conflicts)} conflicts using '{portfolio.resolution_strategy}' strategy.".strip(),
        resolution_strategy=portfolio.resolution_strategy,
    )
```

### Testing Standards

**Mirror source structure** [Source: project-context.md#testing-rules]:
```
tests/templates/portfolios/
├── conftest.py              ← existing (fixtures for policies, portfolios)
├── test_portfolio.py        ← existing (dataclass tests)
├── test_composition.py      ← existing (YAML tests) - UPDATE for resolution_strategy
└── test_conflicts.py        ← NEW (conflict detection and resolution)
```

**Class-based test grouping** [Source: project-context.md]:
```python
class TestConflictDetection:
    """Tests for conflict detection logic (AC #1, #2, #5)."""
    
class TestConflictResolution:
    """Tests for conflict resolution strategies (AC #3, #4, #5)."""
    
class TestConflictYAMLIntegration:
    """Tests for YAML serialization with resolution_strategy (AC #3, #5)."""
```

**Direct assertions, no helpers** [Source: project-context.md]:
```python
def test_sum_strategy_adds_rates(self) -> None:
    """Sum strategy adds rates for overlapping years."""
    portfolio = PolicyPortfolio(
        name="Test",
        policies=(policy_a, policy_b),
        resolution_strategy="sum",
    )
    conflicts = validate_compatibility(portfolio)
    resolved = resolve_conflicts(portfolio, conflicts)
    # Direct assertion on resolved rates
    assert resolved.policies[0].policy.rate_schedule[2027] == 80  # 50 + 30
```

### File Structure

**Updated directory** [Source: architecture.md#extension-policy-portfolio-layer]:
```
src/reformlab/templates/
├── portfolios/
│   ├── __init__.py
│   ├── portfolio.py     ← PolicyPortfolio (ADD resolution_strategy field)
│   ├── composition.py   ← ADD: Conflict, ConflictType, ResolutionStrategy,
│   │                    ←      validate_compatibility(), resolve_conflicts()
│   └── exceptions.py    ← existing (PortfolioError hierarchy)
└── schema/
    └── portfolio.schema.json  ← UPDATE: add resolution_strategy field
```

**Exception taxonomy** — Use existing `PortfolioValidationError` for conflict errors:
```python
# In composition.py
if conflicts and portfolio.resolution_strategy == "error":
    conflict_details = "\n".join(
        f"  - {c.description}" for c in conflicts
    )
    raise PortfolioValidationError(
        summary="Portfolio has unresolved conflicts",
        reason=f"{len(conflicts)} conflicts detected:\n{conflict_details}",
        fix="Set resolution_strategy to 'sum', 'first_wins', 'last_wins', or 'max' "
            "to automatically resolve conflicts",
        invalid_fields=tuple(f"policies[{i}]" for c in conflicts for i in c.policy_indices),
    )
```

### Integration with Existing Code

**Scope boundaries** — This story focuses on conflict detection and resolution ONLY:
- ✅ IN SCOPE: Conflict detection, resolution strategies, metadata recording, validation integration
- ❌ OUT OF SCOPE: Orchestrator execution (Story 12.3), scenario registry integration (Story 12.4), multi-portfolio comparison (Story 12.5)

**YAML schema compatibility** — Portfolio YAML files from Story 12.1 must remain valid:
- `resolution_strategy` field is optional (defaults to "error")
- Existing portfolios without resolution_strategy work as before (fail on conflicts)
- Schema version remains "1.0" (additive change, not breaking)

**Load-time validation** — Conflicts detected at load time, not construction time:
- `PolicyPortfolio.__post_init__` does NOT validate conflicts (deferred to load_portfolio)
- `load_portfolio(path, validate=True)` calls `validate_compatibility()` after loading
- `load_portfolio(path, validate=False)` skips conflict detection (for testing/special cases)

### Error Message Examples

**Conflict detection error (strategy="error"):**
```
PortfolioValidationError: Portfolio has unresolved conflicts
  Reason: 2 conflicts detected:
    - SAME_POLICY_TYPE conflict between policies[0] and policies[1]: both are carbon_tax
    - OVERLAPPING_YEARS conflict in rate_schedule: years 2027-2028 overlap
  Fix: Set resolution_strategy to 'sum', 'first_wins', 'last_wins', or 'max' to automatically resolve conflicts
  Invalid fields: policies[0], policies[1]
```

**Resolution warning (strategy!="error"):**
```
WARNING: Portfolio 'Green Transition 2030' has 2 conflicts resolved using 'sum' strategy:
  - SAME_POLICY_TYPE: policies[0] and policies[1] (carbon_tax)
  - OVERLAPPING_YEARS: rate_schedule years 2027-2028
```

### Project Structure Notes

- **Alignment with unified project structure:** Conflict logic added to existing `composition.py` module (not new file)
- **Naming convention:** `Conflict`, `ConflictType`, `ResolutionStrategy` follow PascalCase enum/class naming
- **Module docstrings:** Update `composition.py` docstring to explain conflict detection and resolution
- **Frozen dataclass pattern:** `Conflict` is frozen, resolution returns new `PolicyPortfolio` instances

### Critical Don't-Miss Rules

1. **Every file starts with `from __future__ import annotations`** — no exceptions [Source: project-context.md#python-language-rules]
2. **Use `if TYPE_CHECKING:` guards** for imports only needed for annotations [Source: project-context.md#python-language-rules]
3. **All domain types are frozen** — `Conflict` must be frozen, resolution returns new `PolicyPortfolio` [Source: project-context.md#critical-dont-miss-rules]
4. **Determinism is non-negotiable** — conflict ordering and resolution must be deterministic [Source: project-context.md#critical-dont-miss-rules]
5. **No wildcard imports** — always import specific names [Source: project-context.md#code-quality-style-rules]
6. **Resolution creates new objects** — never mutate frozen dataclasses, use `PolicyPortfolio(...)` to create new instance

### References

**Architecture:**
- [Source: architecture.md#extension-policy-portfolio-layer] — Policy Portfolio Layer design, composition.py responsibilities
- [Source: architecture.md#phase-2-architecture-extensions] — Phase 2 subsystem overview

**PRD:**
- [Source: prd.md#phase-2-policy-portfolios] — FR43: compose policies, FR44: execute portfolio

**Existing Code:**
- [Source: src/reformlab/templates/portfolios/portfolio.py] — PolicyPortfolio and PolicyConfig definitions
- [Source: src/reformlab/templates/portfolios/composition.py] — YAML serialization (extend for conflicts)
- [Source: src/reformlab/templates/schema.py] — PolicyParameters hierarchy and attributes
- [Source: src/reformlab/templates/portfolios/exceptions.py] — PortfolioValidationError

**Previous Story:**
- [Source: _bmad-output/implementation-artifacts/12-1-define-policyportfolio-dataclass-and-composition-logic.md] — Story 12.1 implementation patterns, frozen dataclass approach, testing standards

**Testing:**
- [Source: tests/templates/portfolios/test_composition.py] — Example YAML round-trip tests
- [Source: tests/templates/portfolios/conftest.py] — Existing fixtures for policies

**Project Context:**
- [Source: project-context.md#architecture-framework-rules] — Frozen dataclasses, Protocols, determinism
- [Source: project-context.md#testing-rules] — Test structure, fixtures, assertions
- [Source: project-context.md#code-quality-style-rules] — ruff, mypy, naming conventions

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

Story 12.1 completed successfully on 2026-03-05. Code review synthesis applied fixes for immutability, package integration, and schema validation.

### Completion Notes List

Ultimate context engine analysis completed - comprehensive developer guide created with detailed conflict detection logic, resolution strategy semantics, and integration patterns.

### File List

**Source code files to create/modify:**
- src/reformlab/templates/portfolios/portfolio.py (add resolution_strategy field)
- src/reformlab/templates/portfolios/composition.py (add Conflict, ConflictType, ResolutionStrategy, validate_compatibility, resolve_conflicts)
- src/reformlab/templates/schema/portfolio.schema.json (add resolution_strategy field)
- src/reformlab/templates/portfolios/__init__.py (export new types)
- src/reformlab/templates/__init__.py (export conflict types)

**Test files to create:**
- tests/templates/portfolios/test_conflicts.py (new file)
- tests/templates/portfolios/test_composition.py (update for resolution_strategy)



]]></file>
<file id="986a4896" path="src/reformlab/templates/__init__.py" label="SOURCE CODE"><![CDATA[

"""Scenario template schema and loader for ReformLab.

This module provides:
- Schema dataclasses for defining scenario templates
- YAML loader/serializer for scenario template files
- Reform-as-delta resolution for reform scenarios
- JSON Schema for IDE validation support
- Template pack discovery and loading utilities
- Scenario registry with immutable versioning
- Schema migration utilities for version compatibility
- Workflow configuration schema and execution handoff
"""

from reformlab.templates.exceptions import ScenarioError, TemplateError
from reformlab.templates.loader import (
    SCHEMA_VERSION,
    dump_scenario_template,
    get_schema_path,
    load_scenario_template,
    validate_schema_version,
)
from reformlab.templates.migration import (
    CompatibilityStatus,
    MigrationChange,
    MigrationReport,
    SchemaVersion,
    check_compatibility,
    migrate_scenario_dict,
)
from reformlab.templates.packs import (
    get_carbon_tax_pack_dir,
    get_feebate_pack_dir,
    get_rebate_pack_dir,
    get_subsidy_pack_dir,
    list_carbon_tax_templates,
    list_feebate_templates,
    list_rebate_templates,
    list_subsidy_templates,
    load_carbon_tax_template,
    load_feebate_template,
    load_rebate_template,
    load_subsidy_template,
)
from reformlab.templates.reform import resolve_reform_definition
from reformlab.templates.registry import (
    RegistryEntry,
    RegistryError,
    ScenarioNotFoundError,
    ScenarioRegistry,
    ScenarioVersion,
    VersionNotFoundError,
)
from reformlab.templates.schema import (
    BaselineScenario,
    CarbonTaxParameters,
    FeebateParameters,
    PolicyParameters,
    PolicyType,
    RebateParameters,
    ReformScenario,
    ScenarioTemplate,
    SubsidyParameters,
    YearSchedule,
    infer_policy_type,
)
from reformlab.templates.portfolios import (
    PolicyConfig,
    PolicyPortfolio,
    PortfolioError,
    PortfolioSerializationError,
    PortfolioValidationError,
)
from reformlab.templates.workflow import (
    WORKFLOW_SCHEMA_VERSION,
    DataSourceConfig,
    OutputConfig,
    OutputFormat,
    OutputType,
    RunConfig,
    ScenarioRef,
    WorkflowConfig,
    WorkflowError,
    WorkflowResult,
    dump_workflow_config,
    get_workflow_schema_path,
    load_workflow_config,
    prepare_workflow_request,
    run_workflow,
    validate_workflow_config,
    validate_workflow_with_schema,
    workflow_to_json,
    workflow_to_yaml,
)

__all__ = [
    # Portfolio types
    "PolicyConfig",
    "PolicyPortfolio",
    "PortfolioError",
    "PortfolioSerializationError",
    "PortfolioValidationError",
    # Migration types and functions
    "CompatibilityStatus",
    "MigrationChange",
    "MigrationReport",
    "SchemaVersion",
    "check_compatibility",
    "migrate_scenario_dict",
    # Registry types
    "RegistryEntry",
    "RegistryError",
    "ScenarioNotFoundError",
    "ScenarioRegistry",
    "ScenarioVersion",
    "VersionNotFoundError",
    # Schema types
    "BaselineScenario",
    "CarbonTaxParameters",
    "FeebateParameters",
    "PolicyParameters",
    "PolicyType",
    "RebateParameters",
    "ReformScenario",
    "ScenarioTemplate",
    "SubsidyParameters",
    "YearSchedule",
    # Loader functions
    "dump_scenario_template",
    "get_schema_path",
    "load_scenario_template",
    "resolve_reform_definition",
    "validate_schema_version",
    # Pack utilities - Carbon tax
    "get_carbon_tax_pack_dir",
    "list_carbon_tax_templates",
    "load_carbon_tax_template",
    # Pack utilities - Subsidy
    "get_subsidy_pack_dir",
    "list_subsidy_templates",
    "load_subsidy_template",
    # Pack utilities - Rebate
    "get_rebate_pack_dir",
    "list_rebate_templates",
    "load_rebate_template",
    # Pack utilities - Feebate
    "get_feebate_pack_dir",
    "list_feebate_templates",
    "load_feebate_template",
    # Inference
    "infer_policy_type",
    # Exceptions
    "ScenarioError",
    "TemplateError",
    # Constants
    "SCHEMA_VERSION",
    # Workflow types and functions
    "DataSourceConfig",
    "OutputConfig",
    "OutputFormat",
    "OutputType",
    "RunConfig",
    "ScenarioRef",
    "WorkflowConfig",
    "WorkflowError",
    "WorkflowResult",
    "WORKFLOW_SCHEMA_VERSION",
    "dump_workflow_config",
    "get_workflow_schema_path",
    "load_workflow_config",
    "prepare_workflow_request",
    "run_workflow",
    "validate_workflow_config",
    "validate_workflow_with_schema",
    "workflow_to_json",
    "workflow_to_yaml",
]


]]></file>
<file id="499cc132" path="src/reformlab/templates/portfolios/__init__.py" label="SOURCE CODE"><![CDATA[

"""Policy portfolio composition and serialization.

This module provides the PolicyPortfolio frozen dataclass for composing
multiple individual policy templates into named, versioned policy packages.

Story 12.1: Define PolicyPortfolio dataclass and composition logic
"""

from __future__ import annotations

from reformlab.templates.portfolios.exceptions import (
    PortfolioError,
    PortfolioSerializationError,
    PortfolioValidationError,
)
from reformlab.templates.portfolios.portfolio import PolicyConfig, PolicyPortfolio

__all__ = [
    "PolicyConfig",
    "PolicyPortfolio",
    "PortfolioError",
    "PortfolioValidationError",
    "PortfolioSerializationError",
]


]]></file>
<file id="15cb27f1" path="src/reformlab/templates/portfolios/composition.py" label="SOURCE CODE"><![CDATA[

"""Portfolio YAML serialization and deserialization.

Story 12.1: Define PolicyPortfolio dataclass and composition logic
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from reformlab.templates.portfolios.exceptions import (
    PortfolioSerializationError,
    PortfolioValidationError,
)
from reformlab.templates.portfolios.portfolio import PolicyConfig, PolicyPortfolio
from reformlab.templates.schema import (
    CarbonTaxParameters,
    FeebateParameters,
    PolicyParameters,
    PolicyType,
    RebateParameters,
    SubsidyParameters,
)

logger = logging.getLogger(__name__)

_SCHEMA_VERSION = "1.0"
_SCHEMA_DIR = Path(__file__).parent.parent / "schema"


def get_portfolio_schema_path() -> Path:
    """Return path to portfolio JSON Schema."""
    return _SCHEMA_DIR / "portfolio.schema.json"


def _load_schema() -> dict[str, Any]:
    """Load portfolio JSON Schema from disk."""
    schema_path = get_portfolio_schema_path()
    with open(schema_path, encoding="utf-8") as f:
        return json.load(f)  # type: ignore[no-any-return]


def portfolio_to_dict(portfolio: PolicyPortfolio) -> dict[str, Any]:
    """Convert PolicyPortfolio to dictionary with deterministic ordering.

    Keys are sorted alphabetically for canonical output.

    Args:
        portfolio: The portfolio to convert

    Returns:
        Dictionary with canonical key ordering
    """
    data: dict[str, Any] = {}

    data["$schema"] = "./schema/portfolio.schema.json"
    data["version"] = portfolio.version
    data["name"] = portfolio.name

    if portfolio.description:
        data["description"] = portfolio.description

    policies_list = []
    for config in portfolio.policies:
        policy_dict: dict[str, Any] = {}
        if config.name:
            policy_dict["name"] = config.name
        policy_dict["policy_type"] = config.policy_type.value
        policy_dict["policy"] = _policy_params_to_dict(config.policy)
        policies_list.append(policy_dict)

    data["policies"] = policies_list

    return data


def _policy_params_to_dict(params: PolicyParameters) -> dict[str, Any]:
    """Convert PolicyParameters to dictionary for YAML serialization."""
    result: dict[str, Any] = {}

    if params.rate_schedule:
        result["rate_schedule"] = params.rate_schedule

    if params.exemptions:
        result["exemptions"] = list(params.exemptions)

    if params.thresholds:
        result["thresholds"] = list(params.thresholds)

    if params.covered_categories:
        result["covered_categories"] = list(params.covered_categories)

    if isinstance(params, CarbonTaxParameters):
        if params.redistribution_type or params.income_weights:
            redistribution: dict[str, Any] = {}
            if params.redistribution_type:
                redistribution["type"] = params.redistribution_type
            if params.income_weights:
                redistribution["income_weights"] = params.income_weights
            result["redistribution"] = redistribution
    elif isinstance(params, SubsidyParameters):
        if params.eligible_categories:
            result["eligible_categories"] = list(params.eligible_categories)
        if params.income_caps:
            result["income_caps"] = params.income_caps
    elif isinstance(params, RebateParameters):
        if params.rebate_type:
            result["rebate_type"] = params.rebate_type
        if params.income_weights:
            result["income_weights"] = params.income_weights
    elif isinstance(params, FeebateParameters):
        if params._pivot_point_set or params.pivot_point != 0.0:
            result["pivot_point"] = params.pivot_point
        if params._fee_rate_set or params.fee_rate != 0.0:
            result["fee_rate"] = params.fee_rate
        if params._rebate_rate_set or params.rebate_rate != 0.0:
            result["rebate_rate"] = params.rebate_rate

    return result


def dict_to_portfolio(data: dict[str, Any]) -> PolicyPortfolio:
    """Convert dictionary to PolicyPortfolio.

    Args:
        data: Dictionary with portfolio data

    Returns:
        PolicyPortfolio instance

    Raises:
        PortfolioValidationError: If data is invalid
    """
    try:
        schema = _load_schema()
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        raise PortfolioValidationError(
            summary="Portfolio validation failed",
            reason=f"Schema validation error: {e.message}",
            fix="Ensure portfolio YAML follows the schema structure",
            invalid_fields=(e.json_path,),
        ) from None
    except jsonschema.SchemaError as e:
        logger.error("Schema error: %s", e)
        raise PortfolioValidationError(
            summary="Portfolio validation failed",
            reason=f"Invalid schema: {e}",
            fix="Check portfolio.schema.json file",
        ) from None

    name = str(data["name"])
    version = str(data.get("version", _SCHEMA_VERSION))
    description = str(data.get("description", ""))

    policies_list = []
    for idx, policy_data in enumerate(data["policies"]):
        policy_name = str(policy_data.get("name", ""))
        policy_type_str = str(policy_data["policy_type"])
        policy_type = PolicyType(policy_type_str)
        policy_params_data = policy_data["policy"]

        policy_params = _dict_to_policy_params(policy_type, policy_params_data)
        config = PolicyConfig(
            policy_type=policy_type,
            policy=policy_params,
            name=policy_name,
        )
        policies_list.append(config)

    portfolio = PolicyPortfolio(
        name=name,
        policies=tuple(policies_list),
        version=version,
        description=description,
    )

    return portfolio


def _dict_to_policy_params(policy_type: PolicyType, raw: dict[str, Any]) -> PolicyParameters:
    """Parse policy parameters from dict based on policy type."""
    rate_schedule: dict[int, float] = {}
    if "rate_schedule" in raw:
        raw_rate = raw["rate_schedule"]
        if not isinstance(raw_rate, dict):
            raise PortfolioValidationError(
                summary="Policy validation failed",
                reason="policy.rate_schedule must be a mapping",
                fix="Set rate_schedule as a YAML object with numeric values",
                invalid_fields=("policy.rate_schedule",),
            )
        try:
            for k, v in raw_rate.items():
                rate_schedule[int(k)] = float(v)
        except (TypeError, ValueError):
            raise PortfolioValidationError(
                summary="Policy validation failed",
                reason="policy.rate_schedule contains non-numeric year or value",
                fix="Use integer-like years and numeric rate values in rate_schedule",
                invalid_fields=("policy.rate_schedule",),
            ) from None

    exemptions = tuple(raw.get("exemptions", []))
    thresholds = tuple(raw.get("thresholds", []))
    covered_categories = tuple(raw.get("covered_categories", []))

    if policy_type == PolicyType.CARBON_TAX:
        redistribution_type = ""
        income_weights: dict[str, float] = {}
        if "redistribution" in raw:
            redist = raw["redistribution"]
            if not isinstance(redist, dict):
                raise PortfolioValidationError(
                    summary="Policy validation failed",
                    reason="policy.redistribution must be a mapping",
                    fix="Set redistribution as a YAML object with type/income_weights",
                    invalid_fields=("policy.redistribution",),
                )
            if "type" in redist:
                redistribution_type = str(redist["type"])
            if "income_weights" in redist:
                raw_weights = redist["income_weights"]
                if not isinstance(raw_weights, dict):
                    raise PortfolioValidationError(
                        summary="Policy validation failed",
                        reason="policy.redistribution.income_weights must be a mapping",
                        fix="Set income_weights as decile -> numeric weight pairs",
                        invalid_fields=("policy.redistribution.income_weights",),
                    )
                try:
                    for k, v in raw_weights.items():
                        income_weights[str(k)] = float(v)
                except (TypeError, ValueError):
                    raise PortfolioValidationError(
                        summary="Policy validation failed",
                        reason="policy.redistribution.income_weights has non-numeric values",
                        fix="Use numeric values for all redistribution income_weights",
                        invalid_fields=("policy.redistribution.income_weights",),
                    ) from None
        return CarbonTaxParameters(
            rate_schedule=rate_schedule,
            exemptions=exemptions,
            thresholds=thresholds,
            covered_categories=covered_categories,
            redistribution_type=redistribution_type,
            income_weights=income_weights,
        )
    elif policy_type == PolicyType.SUBSIDY:
        eligible_categories = tuple(raw.get("eligible_categories", []))
        income_caps: dict[int, float] = {}
        if "income_caps" in raw:
            raw_caps = raw["income_caps"]
            if not isinstance(raw_caps, dict):
                raise PortfolioValidationError(
                    summary="Policy validation failed",
                    reason="policy.income_caps must be a mapping",
                    fix="Set income_caps as a YAML object with numeric values",
                    invalid_fields=("policy.income_caps",),
                )
            try:
                for k, v in raw_caps.items():
                    income_caps[int(k)] = float(v)
            except (TypeError, ValueError):
                raise PortfolioValidationError(
                    summary="Policy validation failed",
                    reason="policy.income_caps contains non-numeric year or value",
                    fix="Use integer-like years and numeric values in income_caps",
                    invalid_fields=("policy.income_caps",),
                ) from None
        return SubsidyParameters(
            rate_schedule=rate_schedule,
            exemptions=exemptions,
            thresholds=thresholds,
            covered_categories=covered_categories,
            eligible_categories=eligible_categories,
            income_caps=income_caps,
        )
    elif policy_type == PolicyType.REBATE:
        rebate_type = str(raw.get("rebate_type", ""))
        rebate_weights: dict[str, float] = {}
        if "income_weights" in raw:
            raw_weights = raw["income_weights"]
            if not isinstance(raw_weights, dict):
                raise PortfolioValidationError(
                    summary="Policy validation failed",
                    reason="policy.income_weights must be a mapping",
                    fix="Set income_weights as decile -> numeric weight pairs",
                    invalid_fields=("policy.income_weights",),
                )
            try:
                for k, v in raw_weights.items():
                    rebate_weights[str(k)] = float(v)
            except (TypeError, ValueError):
                raise PortfolioValidationError(
                    summary="Policy validation failed",
                    reason="policy.income_weights has non-numeric values",
                    fix="Use numeric values for all income_weights",
                    invalid_fields=("policy.income_weights",),
                ) from None
        return RebateParameters(
            rate_schedule=rate_schedule,
            exemptions=exemptions,
            thresholds=thresholds,
            covered_categories=covered_categories,
            rebate_type=rebate_type,
            income_weights=rebate_weights,
        )
    elif policy_type == PolicyType.FEEBATE:
        pivot_point_set = "pivot_point" in raw
        fee_rate_set = "fee_rate" in raw
        rebate_rate_set = "rebate_rate" in raw
        try:
            pivot_point = float(raw.get("pivot_point", 0.0))
            fee_rate = float(raw.get("fee_rate", 0.0))
            rebate_rate = float(raw.get("rebate_rate", 0.0))
        except (TypeError, ValueError):
            raise PortfolioValidationError(
                summary="Policy validation failed",
                reason="feebate numeric fields must be numbers",
                fix="Use numeric values for pivot_point, fee_rate, and rebate_rate",
                invalid_fields=("policy",),
            ) from None
        return FeebateParameters(
            rate_schedule=rate_schedule,
            exemptions=exemptions,
            thresholds=thresholds,
            covered_categories=covered_categories,
            pivot_point=pivot_point,
            fee_rate=fee_rate,
            rebate_rate=rebate_rate,
            _pivot_point_set=pivot_point_set,
            _fee_rate_set=fee_rate_set,
            _rebate_rate_set=rebate_rate_set,
        )
    else:
        return PolicyParameters(
            rate_schedule=rate_schedule,
            exemptions=exemptions,
            thresholds=thresholds,
            covered_categories=covered_categories,
        )


def dump_portfolio(portfolio: PolicyPortfolio, path: Path | str) -> None:
    """Serialize portfolio to YAML file with canonical formatting.

    Args:
        portfolio: The portfolio to serialize
        path: Output file path
    """
    file_path = Path(path)
    data = portfolio_to_dict(portfolio)

    with open(file_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=True)


def load_portfolio(path: Path | str) -> PolicyPortfolio:
    """Load portfolio from YAML file.

    Args:
        path: Path to YAML file

    Returns:
        PolicyPortfolio instance

    Raises:
        PortfolioSerializationError: If file not found or invalid YAML
        PortfolioValidationError: If data is invalid
    """
    file_path = Path(path)

    if not file_path.exists():
        raise PortfolioSerializationError(
            summary="Portfolio load failed",
            reason=f"file was not found: {file_path}",
            fix="Provide an existing .yaml or .yml portfolio file path",
            file_path=file_path,
        )

    try:
        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise PortfolioSerializationError(
            summary="Portfolio load failed",
            reason=f"invalid YAML syntax: {exc}",
            fix="Fix the YAML syntax errors in the portfolio file",
            file_path=file_path,
        ) from None

    if not isinstance(data, dict):
        raise PortfolioValidationError(
            summary="Portfolio load failed",
            reason="portfolio file must contain a YAML mapping (dict)",
            fix="Ensure the file has top-level keys: name, version, policies",
            file_path=file_path,
        )

    portfolio = dict_to_portfolio(data)
    return portfolio


]]></file>
<file id="52d8c030" path="src/reformlab/templates/portfolios/portfolio.py" label="SOURCE CODE"><![CDATA[

"""PolicyPortfolio frozen dataclass for composing multiple policies.

Story 12.1: Define PolicyPortfolio dataclass and composition logic
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from reformlab.templates.portfolios.exceptions import PortfolioValidationError
from reformlab.templates.schema import PolicyParameters, PolicyType, infer_policy_type

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class PolicyConfig:
    """Wrapper for policy parameters with metadata for portfolio composition.

    This is a NEW frozen dataclass (not an alias) that wraps PolicyParameters
    with additional metadata needed for portfolio composition.

    Attributes:
        policy_type: The type of policy (CARBON_TAX, SUBSIDY, etc.)
        policy: The actual policy parameters object
        name: Optional human-readable name for this policy within the portfolio
    """

    policy_type: PolicyType
    policy: PolicyParameters
    name: str = ""

    def __post_init__(self) -> None:
        """Validate that policy matches declared policy_type."""
        inferred_type = infer_policy_type(self.policy)
        if inferred_type != self.policy_type:
            raise PortfolioValidationError(
                summary="PolicyConfig type mismatch",
                reason=f"policy_type={self.policy_type.value} does not match "
                f"inferred type {inferred_type.value} from {type(self.policy).__name__}",
                fix="Ensure policy_type matches the policy parameters class, or "
                "omit policy_type to use automatic inference",
                invalid_fields=("policy_type", "policy"),
            )

    def get_summary(self) -> dict[str, Any]:
        """Extract policy type and key parameter summary.

        Returns:
            Dictionary with name, type, and rate_schedule_years.
        """
        return {
            "name": self.name,
            "type": self.policy_type.value,
            "rate_schedule_years": sorted(self.policy.rate_schedule.keys()),
        }


@dataclass(frozen=True)
class PolicyPortfolio:
    """Named, versioned collection of policy configurations.

    A portfolio is a frozen dataclass containing 2+ individual policies
    that will be applied together during simulation runs.

    Attributes:
        name: Portfolio name
        policies: Tuple of PolicyConfig objects (at least 2 required)
        version: Schema version (defaults to "1.0")
        description: Human-readable description
    """

    name: str
    policies: tuple[PolicyConfig, ...]
    version: str = "1.0"
    description: str = ""

    def __post_init__(self) -> None:
        """Validate portfolio has at least 2 policies."""
        if len(self.policies) < 2:
            raise PortfolioValidationError(
                summary="Invalid portfolio",
                reason=f"Portfolio must have at least 2 policies, got {len(self.policies)}",
                fix="Add at least 2 PolicyConfig objects to the portfolio",
                invalid_fields=("policies",),
            )

    @property
    def policy_types(self) -> tuple[PolicyType, ...]:
        """Return tuple of policy types in order."""
        return tuple(p.policy_type for p in self.policies)

    @property
    def policy_count(self) -> int:
        """Return number of policies in portfolio."""
        return len(self.policies)

    @property
    def policy_summaries(self) -> tuple[dict[str, Any], ...]:
        """Return tuple of policy summaries in order."""
        return tuple(p.get_summary() for p in self.policies)

    def list_policies(self) -> list[dict[str, Any]]:
        """Return detailed list of all policies with their configurations.

        Returns:
            List of dicts with name, type, rate_schedule, and other policy details.
        """
        result = []
        for config in self.policies:
            policy_dict: dict[str, Any] = {
                "name": config.name,
                "type": config.policy_type.value,
                "rate_schedule": dict(config.policy.rate_schedule),  # Defensive copy
            }
            result.append(policy_dict)
        return result

    def get_policy_by_type(self, policy_type: PolicyType) -> PolicyConfig | None:
        """Get first policy matching the given type.

        Args:
            policy_type: The policy type to search for

        Returns:
            First matching PolicyConfig or None if not found.
        """
        for config in self.policies:
            if config.policy_type == policy_type:
                return config
        return None

    def has_policy_type(self, policy_type: PolicyType) -> bool:
        """Check if portfolio contains a policy of the given type.

        Args:
            policy_type: The policy type to check for

        Returns:
            True if at least one policy of that type exists.
        """
        return any(config.policy_type == policy_type for config in self.policies)

    def __repr__(self) -> str:
        """Notebook-friendly representation."""
        return (
            f"PolicyPortfolio(name={self.name!r}, "
            f"version={self.version!r}, "
            f"policies={self.policy_count} policies)"
        )


]]></file>
<file id="f564228b" path="src/reformlab/templates/schema/portfolio.schema.json" label="CONFIG FILE"><![CDATA[

{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "portfolio.schema.json",
  "title": "Policy Portfolio Schema",
  "description": "Schema for policy portfolio YAML files",
  "type": "object",
  "required": ["name", "version", "policies"],
  "additionalProperties": false,
  "properties": {
    "$schema": {
      "type": "string",
      "description": "Reference to this schema file for IDE validation"
    },
    "name": {
      "type": "string",
      "description": "Portfolio name",
      "minLength": 1
    },
    "version": {
      "type": "string",
      "description": "Schema version",
      "pattern": "^[0-9]+\\.[0-9]+$",
      "default": "1.0"
    },
    "description": {
      "type": "string",
      "description": "Human-readable description of the portfolio",
      "default": ""
    },
    "policies": {
      "type": "array",
      "description": "List of policy configurations",
      "minItems": 2,
      "items": {
        "type": "object",
        "required": ["policy_type", "policy"],
        "additionalProperties": false,
        "properties": {
          "name": {
            "type": "string",
            "description": "Human-readable name for this policy within the portfolio",
            "default": ""
          },
          "policy_type": {
            "type": "string",
            "enum": ["carbon_tax", "subsidy", "rebate", "feebate"],
            "description": "Type of policy"
          },
          "policy": {
            "type": "object",
            "description": "Policy parameters",
            "additionalProperties": false,
            "properties": {
              "rate_schedule": {
                "type": "object",
                "description": "Year to rate mapping",
                "additionalProperties": {
                  "type": "number"
                }
              },
              "exemptions": {
                "type": "array",
                "items": {
                  "type": "object"
                }
              },
              "thresholds": {
                "type": "array",
                "items": {
                  "type": "object"
                }
              },
              "covered_categories": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "redistribution": {
                "type": "object",
                "properties": {
                  "type": {
                    "type": "string"
                  },
                  "income_weights": {
                    "type": "object",
                    "additionalProperties": {
                      "type": "number"
                    }
                  }
                }
              },
              "eligible_categories": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "income_caps": {
                "type": "object",
                "additionalProperties": {
                  "type": "number"
                }
              },
              "rebate_type": {
                "type": "string"
              },
              "income_weights": {
                "type": "object",
                "additionalProperties": {
                  "type": "number"
                }
              },
              "pivot_point": {
                "type": "number"
              },
              "fee_rate": {
                "type": "number"
              },
              "rebate_rate": {
                "type": "number"
              }
            }
          }
        }
      }
    }
  }
}


]]></file>
<file id="cbee94eb" path="tests/templates/portfolios/test_composition.py" label="SOURCE CODE"><![CDATA[

"""Tests for portfolio YAML serialization and round-trip.

Story 12.1: Define PolicyPortfolio dataclass and composition logic
AC3: YAML round-trip
AC4: Validation error handling
AC5: Deterministic serialization
"""

from __future__ import annotations

from pathlib import Path

import pytest

from reformlab.templates.portfolios.composition import (
    dict_to_portfolio,
    dump_portfolio,
    load_portfolio,
    portfolio_to_dict,
)
from reformlab.templates.portfolios.exceptions import (
    PortfolioSerializationError,
    PortfolioValidationError,
)
from reformlab.templates.portfolios.portfolio import PolicyConfig, PolicyPortfolio
from reformlab.templates.schema import (
    CarbonTaxParameters,
    FeebateParameters,
    PolicyType,
    RebateParameters,
    SubsidyParameters,
)


class TestPortfolioYAMLSerialization:
    """Tests for YAML serialization round-trip (AC3, AC5)."""

    def test_portfolio_to_dict_basic(
        self, carbon_tax_params: CarbonTaxParameters, subsidy_params: SubsidyParameters
    ) -> None:
        """portfolio_to_dict produces correct dictionary structure."""
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
            name="Carbon Tax",
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=subsidy_params,
            name="EV Subsidy",
        )
        portfolio = PolicyPortfolio(
            name="Test Portfolio",
            policies=(policy1, policy2),
            version="1.0",
            description="Test description",
        )
        data = portfolio_to_dict(portfolio)
        assert data["name"] == "Test Portfolio"
        assert data["version"] == "1.0"
        assert data["description"] == "Test description"
        assert len(data["policies"]) == 2
        assert data["policies"][0]["name"] == "Carbon Tax"
        assert data["policies"][0]["policy_type"] == "carbon_tax"
        assert data["policies"][1]["name"] == "EV Subsidy"
        assert data["policies"][1]["policy_type"] == "subsidy"

    def test_dict_to_portfolio_basic(
        self, carbon_tax_params: CarbonTaxParameters, subsidy_params: SubsidyParameters
    ) -> None:
        """dict_to_portfolio reconstructs portfolio from dict."""
        data = {
            "name": "Test Portfolio",
            "version": "1.0",
            "description": "Test description",
            "policies": [
                {
                    "name": "Carbon Tax",
                    "policy_type": "carbon_tax",
                    "policy": {
                        "rate_schedule": {2026: 44.6, 2027: 50.0},
                        "redistribution": {
                            "type": "lump_sum",
                        },
                    },
                },
                {
                    "name": "EV Subsidy",
                    "policy_type": "subsidy",
                    "policy": {
                        "rate_schedule": {2026: 5000.0},
                        "eligible_categories": ["electric_vehicle"],
                    },
                },
            ],
        }
        portfolio = dict_to_portfolio(data)
        assert portfolio.name == "Test Portfolio"
        assert portfolio.version == "1.0"
        assert portfolio.description == "Test description"
        assert len(portfolio.policies) == 2
        assert portfolio.policies[0].name == "Carbon Tax"
        assert portfolio.policies[0].policy_type == PolicyType.CARBON_TAX
        assert portfolio.policies[1].name == "EV Subsidy"
        assert portfolio.policies[1].policy_type == PolicyType.SUBSIDY

    def test_round_trip_preserves_equality(
        self,
        carbon_tax_params: CarbonTaxParameters,
        subsidy_params: SubsidyParameters,
        temp_portfolio_dir: Path,
    ) -> None:
        """YAML round-trip produces identical object using dataclass equality."""
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
            name="Carbon Tax",
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=subsidy_params,
            name="EV Subsidy",
        )
        original = PolicyPortfolio(
            name="Test Portfolio",
            policies=(policy1, policy2),
            version="1.0",
            description="Test description",
        )
        file_path = temp_portfolio_dir / "test-portfolio.yaml"
        dump_portfolio(original, file_path)
        loaded = load_portfolio(file_path)
        assert loaded == original

    def test_round_trip_preserves_order(
        self,
        carbon_tax_params: CarbonTaxParameters,
        subsidy_params: SubsidyParameters,
        temp_portfolio_dir: Path,
    ) -> None:
        """YAML round-trip preserves policy order."""
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
            name="First",
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=subsidy_params,
            name="Second",
        )
        policy3 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
            name="Third",
        )
        original = PolicyPortfolio(
            name="Multi Policy",
            policies=(policy1, policy2, policy3),
        )
        file_path = temp_portfolio_dir / "test-order.yaml"
        dump_portfolio(original, file_path)
        loaded = load_portfolio(file_path)
        assert loaded.policies[0].name == "First"
        assert loaded.policies[1].name == "Second"
        assert loaded.policies[2].name == "Third"

    def test_round_trip_preserves_defaults(
        self,
        carbon_tax_params: CarbonTaxParameters,
        subsidy_params: SubsidyParameters,
        temp_portfolio_dir: Path,
    ) -> None:
        """YAML round-trip preserves default field values."""
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=subsidy_params,
        )
        original = PolicyPortfolio(
            name="Test",
            policies=(policy1, policy2),
        )
        file_path = temp_portfolio_dir / "test-defaults.yaml"
        dump_portfolio(original, file_path)
        loaded = load_portfolio(file_path)
        assert loaded.version == "1.0"
        assert loaded.description == ""
        assert loaded.policies[0].name == ""
        assert loaded.policies[1].name == ""

    def test_deterministic_serialization(
        self,
        carbon_tax_params: CarbonTaxParameters,
        subsidy_params: SubsidyParameters,
        temp_portfolio_dir: Path,
    ) -> None:
        """Identical portfolios produce byte-identical YAML (AC5)."""
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
            name="Carbon Tax",
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=subsidy_params,
            name="EV Subsidy",
        )
        portfolio = PolicyPortfolio(
            name="Test Portfolio",
            policies=(policy1, policy2),
        )
        file1 = temp_portfolio_dir / "test1.yaml"
        file2 = temp_portfolio_dir / "test2.yaml"
        dump_portfolio(portfolio, file1)
        dump_portfolio(portfolio, file2)
        content1 = file1.read_text()
        content2 = file2.read_text()
        assert content1 == content2

    def test_deterministic_key_ordering(
        self,
        carbon_tax_params: CarbonTaxParameters,
        subsidy_params: SubsidyParameters,
        temp_portfolio_dir: Path,
    ) -> None:
        """YAML output has canonical (alphabetical) key ordering (AC5)."""
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
            name="Carbon Tax",
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=subsidy_params,
            name="EV Subsidy",
        )
        portfolio = PolicyPortfolio(
            name="Test Portfolio",
            policies=(policy1, policy2),
        )
        file_path = temp_portfolio_dir / "test-canonical.yaml"
        dump_portfolio(portfolio, file_path)
        content = file_path.read_text()

        # Check that keys are in alphabetical order (this is the best we can do with yaml.dump)
        # Just verify the output is deterministic and well-formed
        assert "$schema" in content
        assert "name:" in content
        assert "policies:" in content
        assert "version:" in content


class TestPortfolioYAMLValidation:
    """Tests for YAML validation and error handling (AC4)."""

    def test_load_invalid_yaml_syntax(self, temp_portfolio_dir: Path) -> None:
        """Loading invalid YAML syntax raises clear error."""
        file_path = temp_portfolio_dir / "invalid.yaml"
        file_path.write_text("name: [unclosed\nlist")
        with pytest.raises(PortfolioSerializationError, match="invalid YAML"):
            load_portfolio(file_path)

    def test_load_missing_required_field_name(self, temp_portfolio_dir: Path) -> None:
        """Loading portfolio without 'name' raises clear error."""
        file_path = temp_portfolio_dir / "missing-name.yaml"
        file_path.write_text(
            """
version: "1.0"
policies:
  - policy_type: carbon_tax
    policy:
      rate_schedule: {2026: 44.6}
"""
        )
        with pytest.raises(PortfolioValidationError, match="name"):
            load_portfolio(file_path)

    def test_load_missing_required_field_policies(self, temp_portfolio_dir: Path) -> None:
        """Loading portfolio without 'policies' raises clear error."""
        file_path = temp_portfolio_dir / "missing-policies.yaml"
        file_path.write_text(
            """
name: "Test Portfolio"
version: "1.0"
"""
        )
        with pytest.raises(PortfolioValidationError, match="policies"):
            load_portfolio(file_path)

    def test_load_insufficient_policies(self, temp_portfolio_dir: Path) -> None:
        """Loading portfolio with <2 policies raises clear error."""
        file_path = temp_portfolio_dir / "insufficient.yaml"
        file_path.write_text(
            """
name: "Single Policy Portfolio"
version: "1.0"
policies:
  - policy_type: carbon_tax
    policy:
      rate_schedule: {2026: 44.6}
"""
        )
        with pytest.raises(PortfolioValidationError, match="too short"):
            load_portfolio(file_path)

    def test_load_invalid_policy_type(self, temp_portfolio_dir: Path) -> None:
        """Loading portfolio with invalid policy_type raises clear error."""
        file_path = temp_portfolio_dir / "invalid-type.yaml"
        file_path.write_text(
            """
name: "Invalid Type Portfolio"
version: "1.0"
policies:
  - policy_type: invalid_type
    policy:
      rate_schedule: {2026: 44.6}
  - policy_type: carbon_tax
    policy:
      rate_schedule: {2026: 50.0}
"""
        )
        with pytest.raises(PortfolioValidationError, match="invalid_type"):
            load_portfolio(file_path)

    def test_load_missing_policy_field(self, temp_portfolio_dir: Path) -> None:
        """Loading portfolio with missing policy field raises clear error."""
        file_path = temp_portfolio_dir / "missing-policy.yaml"
        file_path.write_text(
            """
name: "Missing Policy Field"
version: "1.0"
policies:
  - policy_type: carbon_tax
  - policy_type: subsidy
    policy:
      rate_schedule: {2026: 5000.0}
"""
        )
        with pytest.raises(PortfolioValidationError, match="policy"):
            load_portfolio(file_path)

    def test_load_file_not_found(self, temp_portfolio_dir: Path) -> None:
        """Loading non-existent file raises clear error."""
        file_path = temp_portfolio_dir / "nonexistent.yaml"
        with pytest.raises(PortfolioSerializationError, match="not found"):
            load_portfolio(file_path)

    def test_load_non_dict_structure(self, temp_portfolio_dir: Path) -> None:
        """Loading non-dict YAML raises clear error."""
        file_path = temp_portfolio_dir / "not-dict.yaml"
        file_path.write_text("- item1\n- item2")
        with pytest.raises(PortfolioValidationError, match="mapping"):
            load_portfolio(file_path)

    def test_schema_reference_included(
        self,
        carbon_tax_params: CarbonTaxParameters,
        subsidy_params: SubsidyParameters,
        temp_portfolio_dir: Path,
    ) -> None:
        """Dumped YAML includes $schema reference for IDE validation."""
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=subsidy_params,
        )
        portfolio = PolicyPortfolio(
            name="Test",
            policies=(policy1, policy2),
        )
        file_path = temp_portfolio_dir / "test-schema.yaml"
        dump_portfolio(portfolio, file_path)
        content = file_path.read_text()
        assert "$schema" in content
        assert "portfolio.schema.json" in content


class TestPortfolioPolicyTypes:
    """Tests for different policy types in portfolios."""

    def test_portfolio_with_rebate_policy(self, temp_portfolio_dir: Path) -> None:
        """Portfolio can contain rebate policies."""
        carbon_tax = CarbonTaxParameters(
            rate_schedule={2026: 50.0},
        )
        rebate = RebateParameters(
            rate_schedule={2026: 100.0},
            rebate_type="lump_sum",
        )
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax,
            name="Carbon Tax",
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.REBATE,
            policy=rebate,
            name="Climate Dividend",
        )
        portfolio = PolicyPortfolio(
            name="Rebate Portfolio",
            policies=(policy1, policy2),
        )
        file_path = temp_portfolio_dir / "rebate.yaml"
        dump_portfolio(portfolio, file_path)
        loaded = load_portfolio(file_path)
        assert loaded.name == "Rebate Portfolio"
        assert loaded.has_policy_type(PolicyType.REBATE)

    def test_portfolio_with_feebate_policy(self, temp_portfolio_dir: Path) -> None:
        """Portfolio can contain feebate policies."""
        carbon_tax = CarbonTaxParameters(
            rate_schedule={2026: 50.0},
        )
        feebate = FeebateParameters(
            rate_schedule={2026: 0.0},
            pivot_point=100.0,
            fee_rate=0.1,
            rebate_rate=0.2,
        )
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax,
            name="Carbon Tax",
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.FEEBATE,
            policy=feebate,
            name="Vehicle Feebate",
        )
        portfolio = PolicyPortfolio(
            name="Feebate Portfolio",
            policies=(policy1, policy2),
        )
        file_path = temp_portfolio_dir / "feebate.yaml"
        dump_portfolio(portfolio, file_path)
        loaded = load_portfolio(file_path)
        assert loaded.name == "Feebate Portfolio"
        assert loaded.has_policy_type(PolicyType.FEEBATE)

    def test_round_trip_with_income_weights(
        self, carbon_tax_params: CarbonTaxParameters, temp_portfolio_dir: Path
    ) -> None:
        """Round-trip preserves income_weights."""
        rebate = RebateParameters(
            rate_schedule={2026: 100.0},
            rebate_type="progressive_dividend",
            income_weights={"decile_1": 1.5, "decile_2": 1.2},
        )
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.REBATE,
            policy=rebate,
        )
        original = PolicyPortfolio(
            name="Test",
            policies=(policy1, policy2),
        )
        file_path = temp_portfolio_dir / "weights.yaml"
        dump_portfolio(original, file_path)
        loaded = load_portfolio(file_path)
        assert loaded.policies[1].policy.income_weights == {
            "decile_1": 1.5,
            "decile_2": 1.2,
        }


class TestPortfolioErrorHandling:
    """Tests for error handling in portfolio composition."""

    def test_invalid_rate_schedule_type(self, temp_portfolio_dir: Path) -> None:
        """Invalid rate_schedule type raises clear error."""
        file_path = temp_portfolio_dir / "bad-rate-schedule.yaml"
        file_path.write_text(
            """
name: "Bad Rate Schedule"
version: "1.0"
policies:
  - policy_type: carbon_tax
    policy:
      rate_schedule: "not a dict"
  - policy_type: subsidy
    policy:
      rate_schedule: {2026: 100}
"""
        )
        with pytest.raises(PortfolioValidationError, match="rate_schedule"):
            load_portfolio(file_path)

    def test_invalid_rate_schedule_value(self, temp_portfolio_dir: Path) -> None:
        """Non-numeric rate_schedule value raises clear error."""
        file_path = temp_portfolio_dir / "bad-rate-value.yaml"
        file_path.write_text(
            """
name: "Bad Rate Value"
version: "1.0"
policies:
  - policy_type: carbon_tax
    policy:
      rate_schedule: {2026: "not a number"}
  - policy_type: subsidy
    policy:
      rate_schedule: {2026: 100}
"""
        )
        with pytest.raises(PortfolioValidationError, match="rate_schedule"):
            load_portfolio(file_path)

    def test_invalid_redistribution_type(self, temp_portfolio_dir: Path) -> None:
        """Invalid redistribution type raises clear error."""
        file_path = temp_portfolio_dir / "bad-redistribution.yaml"
        file_path.write_text(
            """
name: "Bad Redistribution"
version: "1.0"
policies:
  - policy_type: carbon_tax
    policy:
      rate_schedule: {2026: 50}
      redistribution: "not a dict"
  - policy_type: subsidy
    policy:
      rate_schedule: {2026: 100}
"""
        )
        with pytest.raises(PortfolioValidationError, match="redistribution"):
            load_portfolio(file_path)

    def test_invalid_income_weights_type(self, temp_portfolio_dir: Path) -> None:
        """Invalid income_weights type raises clear error."""
        file_path = temp_portfolio_dir / "bad-weights.yaml"
        file_path.write_text(
            """
name: "Bad Weights"
version: "1.0"
policies:
  - policy_type: carbon_tax
    policy:
      rate_schedule: {2026: 50}
      redistribution:
        type: progressive_dividend
        income_weights: "not a dict"
  - policy_type: subsidy
    policy:
      rate_schedule: {2026: 100}
"""
        )
        with pytest.raises(PortfolioValidationError, match="income_weights"):
            load_portfolio(file_path)

    def test_invalid_income_caps_type(self, temp_portfolio_dir: Path) -> None:
        """Invalid income_caps type raises clear error."""
        file_path = temp_portfolio_dir / "bad-caps.yaml"
        file_path.write_text(
            """
name: "Bad Caps"
version: "1.0"
policies:
  - policy_type: carbon_tax
    policy:
      rate_schedule: {2026: 50}
  - policy_type: subsidy
    policy:
      rate_schedule: {2026: 100}
      income_caps: "not a dict"
"""
        )
        with pytest.raises(PortfolioValidationError, match="income_caps"):
            load_portfolio(file_path)

    def test_invalid_feebate_numeric_fields(self, temp_portfolio_dir: Path) -> None:
        """Invalid feebate numeric fields raise clear error."""
        file_path = temp_portfolio_dir / "bad-feebate.yaml"
        file_path.write_text(
            """
name: "Bad Feebate"
version: "1.0"
policies:
  - policy_type: carbon_tax
    policy:
      rate_schedule: {2026: 50}
  - policy_type: feebate
    policy:
      rate_schedule: {2026: 0}
      pivot_point: "not a number"
"""
        )
        with pytest.raises(PortfolioValidationError, match="feebate"):
            load_portfolio(file_path)


]]></file>
</context>
<variables>
<var name="architecture_file" description="Architecture for technical requirements verification" load_strategy="SELECTIVE_LOAD" token_approx="2785">_bmad-output/planning-artifacts/architecture-diagrams.md</var>
<var name="author">BMad</var>
<var name="communication_language">English</var>
<var name="date">2026-03-05</var>
<var name="description">Quality competition validator - systematically review and improve story context created by create-story workflow</var>
<var name="document_output_language">English</var>
<var name="epic_num">12</var>
<var name="epics_file" description="Enhanced epics+stories file for story verification" load_strategy="SELECTIVE_LOAD" token_approx="22457">_bmad-output/planning-artifacts/epics.md</var>
<var name="implementation_artifacts">_bmad-output/implementation-artifacts</var>
<var name="instructions">embedded context</var>
<var name="model">validator</var>
<var name="name">validate-story</var>
<var name="output_folder">_bmad-output/implementation-artifacts</var>
<var name="planning_artifacts">_bmad-output/planning-artifacts</var>
<var name="prd_file" description="PRD for requirements verification" load_strategy="SELECTIVE_LOAD" token_approx="7305">_bmad-output/planning-artifacts/prd-validation-report.md</var>
<var name="project_context" file_id="b5c6fe32" load_strategy="EMBEDDED" token_approx="2024">embedded in prompt, file id: b5c6fe32</var>
<var name="project_knowledge">docs</var>
<var name="project_name">ReformLab</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_dir">_bmad-output/implementation-artifacts</var>
<var name="story_file" file_id="38e1067d">embedded in prompt, file id: 38e1067d</var>
<var name="story_id">12.2</var>
<var name="story_key">12-2-implement-portfolio-compatibility-validation-and-conflict-resolution</var>
<var name="story_num">2</var>
<var name="story_title">implement-portfolio-compatibility-validation-and-conflict-resolution</var>
<var name="template">embedded context</var>
<var name="timestamp">20260305_205602</var>
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
    <critical>OUTPUT MARKERS REQUIRED: Your validation report MUST start with the marker &lt;!-- VALIDATION_REPORT_START --&gt; on its own line BEFORE the report header, and MUST end with the marker &lt;!-- VALIDATION_REPORT_END --&gt; on its own line AFTER the final line. The orchestrator extracts ONLY content between these markers. Any text outside the markers (thinking, commentary) will be discarded.</critical>

    <action>Use the output template as a FORMAT GUIDE</action>
    <action>Replace all {{placeholders}} in the template with your actual analysis results</action>
    <action>Output the complete validation report to stdout with all sections filled in</action>
    <action>Do NOT save to any file - the orchestration system handles persistence</action>
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