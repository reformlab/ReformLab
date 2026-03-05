<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 11 -->
<!-- Story: 1 -->
<!-- Phase: validate-story -->
<!-- Timestamp: 20260303T100448Z -->
<compiled-workflow>
<mission><![CDATA[

Adversarial Story Validation

Target: Story 11.1 - define-datasourceloader-protocol-and-caching-infrastructure

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

<!-- TRUNCATED: Content exceeded token budget. See full document for details. -->

]]></file>
<file id="c687cb63" path="_bmad-output/implementation-artifacts/11-1-define-datasourceloader-protocol-and-caching-infrastructure.md" label="STORY FILE"><![CDATA[

# Story 11.1: Define DataSourceLoader protocol and caching infrastructure

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform developer building institutional data source loaders,
I want a `DataSourceLoader` protocol and disk-based caching infrastructure with offline-first semantics,
so that all subsequent loader implementations (INSEE, Eurostat, ADEME, SDES) share a consistent contract, cache downloaded data locally, and work offline after first download.

## Acceptance Criteria

1. Given the `DataSourceLoader` protocol, when a new loader is implemented, then it must provide `download()`, `status()`, and `schema()` methods.
2. Given a dataset downloaded for the first time, when cached, then the cache stores a schema-validated Parquet file with SHA-256 hash in `~/.reformlab/cache/sources/{provider}/{dataset_id}/`.
3. Given a previously cached dataset, when the loader is called again, then the cache is used without network access.
4. Given a network failure with an existing cache, when the loader is called, then the stale cache is used with a governance warning logged.
5. Given `REFORMLAB_OFFLINE=1` environment variable, when a loader is called and cache misses, then it fails explicitly without attempting network access.
6. Given the cache, when `status()` is called, then it returns `CacheStatus` with cached flag, path, download timestamp, hash, and staleness indicator.

## Tasks / Subtasks

- [ ] Task 1: Create population subsystem package scaffold (AC: all — foundational)
  - [ ] 1.1 Create `src/reformlab/population/__init__.py` with module docstring and public API exports
  - [ ] 1.2 Create `src/reformlab/population/loaders/__init__.py` with public API exports
  - [ ] 1.3 Create `src/reformlab/population/loaders/errors.py` with subsystem-specific exceptions
  - [ ] 1.4 Create `tests/population/__init__.py` and `tests/population/conftest.py`
  - [ ] 1.5 Create `tests/population/loaders/__init__.py` and `tests/population/loaders/conftest.py`

- [ ] Task 2: Define `SourceConfig` frozen dataclass (AC: #1, #2, #3)
  - [ ] 2.1 Define `SourceConfig` in `src/reformlab/population/loaders/base.py` as `@dataclass(frozen=True)` with fields: `provider: str`, `dataset_id: str`, `url: str`, `params: dict[str, str]` (default empty), `description: str` (default empty)
  - [ ] 2.2 Add `__post_init__` validation: `provider` and `dataset_id` must be non-empty strings; normalize `params` via `object.__setattr__` for deep-copy protection

- [ ] Task 3: Define `CacheStatus` frozen dataclass (AC: #6)
  - [ ] 3.1 Define `CacheStatus` in `src/reformlab/population/loaders/base.py` as `@dataclass(frozen=True)` with fields: `cached: bool`, `path: Path | None`, `downloaded_at: datetime | None`, `hash: str | None`, `stale: bool`
  - [ ] 3.2 Ensure `path` uses `Path` from `pathlib`, `downloaded_at` uses `datetime` from `datetime`

- [ ] Task 4: Define `DataSourceLoader` protocol (AC: #1)
  - [ ] 4.1 Define `DataSourceLoader` in `src/reformlab/population/loaders/base.py` as `@runtime_checkable class DataSourceLoader(Protocol)` with three methods:
    - `def download(self, config: SourceConfig) -> pa.Table: ...`
    - `def status(self, config: SourceConfig) -> CacheStatus: ...`
    - `def schema(self) -> pa.Schema: ...`
  - [ ] 4.2 Add comprehensive docstring explaining structural typing, protocol purpose, and downstream loader expectations
  - [ ] 4.3 Verify `isinstance()` check works at runtime (unit test)

- [ ] Task 5: Implement `SourceCache` — disk-based caching infrastructure (AC: #2, #3, #4, #5)
  - [ ] 5.1 Create `src/reformlab/population/loaders/cache.py` with `SourceCache` class
  - [ ] 5.2 Constructor takes `cache_root: Path | None = None` (defaults to `~/.reformlab/cache/sources`)
  - [ ] 5.3 Implement `cache_key(config: SourceConfig) -> str` — deterministic SHA-256 of `url + sorted(params) + date_prefix` (see Dev Notes for hash design)
  - [ ] 5.4 Implement `cache_path(config: SourceConfig) -> Path` — returns `{cache_root}/{provider}/{dataset_id}/{cache_key}.parquet`
  - [ ] 5.5 Implement `metadata_path(config: SourceConfig) -> Path` — returns `{cache_path}.meta.json` (stores download timestamp, hash, URL, params)
  - [ ] 5.6 Implement `get(config: SourceConfig) -> tuple[pa.Table, CacheStatus] | None` — returns cached table + status if cache hit, `None` if miss
  - [ ] 5.7 Implement `put(config: SourceConfig, table: pa.Table) -> CacheStatus` — write schema-validated Parquet + metadata JSON, compute SHA-256 of written file, return `CacheStatus`
  - [ ] 5.8 Implement `status(config: SourceConfig) -> CacheStatus` — read metadata without loading table
  - [ ] 5.9 Implement `is_offline() -> bool` — check `REFORMLAB_OFFLINE` env var (truthy: `"1"`, `"true"`, `"yes"`)
  - [ ] 5.10 Ensure `cache_root` directory is created on first write (not on init — no side effects in constructor)
  - [ ] 5.11 Use `pyarrow.parquet.write_table()` for cache writes and `pyarrow.parquet.read_table()` for reads

- [ ] Task 6: Implement `CachedLoader` — base class wrapping protocol + cache (AC: #2, #3, #4, #5)
  - [ ] 6.1 Create `CachedLoader` in `src/reformlab/population/loaders/base.py` (concrete class, not protocol) that wraps cache logic around the download lifecycle:
    - Constructor: `cache: SourceCache`, `logger: logging.Logger`
    - Abstract-ish method: `_fetch(config: SourceConfig) -> pa.Table` (subclasses override to do real HTTP download)
    - `download(config: SourceConfig) -> pa.Table` — orchestrates: check cache → if miss, check offline → fetch → validate schema → cache → return
    - `status(config: SourceConfig) -> CacheStatus` — delegates to `cache.status()`
    - `schema(self) -> pa.Schema` — abstract, subclasses must implement
  - [ ] 6.2 In `download()`: on network failure (any `OSError`, `urllib.error.URLError`) with existing cache, use stale cache and log governance warning via `logging.getLogger(__name__).warning()`
  - [ ] 6.3 In `download()`: when `REFORMLAB_OFFLINE=1` and cache miss, raise `DataSourceOfflineError` with clear message
  - [ ] 6.4 In `download()`: when cache hit (not stale), return cached table directly without network
  - [ ] 6.5 Governance warning format: `"WARNING: Using stale cache for %s/%s — network unavailable. Downloaded at %s, hash %s"` (provider, dataset_id, timestamp, hash)

- [ ] Task 7: Define subsystem-specific exceptions (AC: #4, #5)
  - [ ] 7.1 In `src/reformlab/population/loaders/errors.py`, define:
    - `DataSourceError(Exception)` — base exception with `*, summary: str, reason: str, fix: str` kwargs following project pattern
    - `DataSourceOfflineError(DataSourceError)` — raised when offline mode prevents download
    - `DataSourceDownloadError(DataSourceError)` — raised on network/download failures (without cache fallback)
    - `DataSourceValidationError(DataSourceError)` — raised when downloaded data fails schema validation
  - [ ] 7.2 Message format: `f"{summary} - {reason} - {fix}"` (matches `IngestionError` pattern)

- [ ] Task 8: Add `network` pytest marker to pyproject.toml (AC: CI fixture pattern)
  - [ ] 8.1 Add `"network: marks tests requiring real network access to institutional APIs (opt-in with '-m network')"` to `[tool.pytest.ini_options].markers`
  - [ ] 8.2 Update `addopts` to exclude `network`: `"-m 'not integration and not scale and not network'"`

- [ ] Task 9: Write comprehensive tests (AC: all)
  - [ ] 9.1 `tests/population/loaders/test_base.py` — Protocol compliance: verify `isinstance()` check, verify minimal conforming class satisfies protocol
  - [ ] 9.2 `tests/population/loaders/test_base.py` — `SourceConfig`: construction, validation (empty provider/dataset_id rejected), frozen immutability, params deep-copy
  - [ ] 9.3 `tests/population/loaders/test_base.py` — `CacheStatus`: construction with all fields, `None` defaults
  - [ ] 9.4 `tests/population/loaders/test_cache.py` — `SourceCache.put()` + `get()` round-trip: write table, read back, verify content identical
  - [ ] 9.5 `tests/population/loaders/test_cache.py` — Cache miss returns `None`
  - [ ] 9.6 `tests/population/loaders/test_cache.py` — `status()` returns correct `CacheStatus` for cached and uncached datasets
  - [ ] 9.7 `tests/population/loaders/test_cache.py` — Cache directory structure: verify `{provider}/{dataset_id}/{hash}.parquet` layout
  - [ ] 9.8 `tests/population/loaders/test_cache.py` — Metadata JSON contains download timestamp, hash, URL, params
  - [ ] 9.9 `tests/population/loaders/test_cache.py` — `is_offline()` respects `REFORMLAB_OFFLINE` env var (use `monkeypatch.setenv`)
  - [ ] 9.10 `tests/population/loaders/test_cached_loader.py` — Cache hit: `_fetch()` is NOT called, cached table returned
  - [ ] 9.11 `tests/population/loaders/test_cached_loader.py` — Cache miss: `_fetch()` IS called, result cached, table returned
  - [ ] 9.12 `tests/population/loaders/test_cached_loader.py` — Network failure + existing cache: stale cache used, warning logged
  - [ ] 9.13 `tests/population/loaders/test_cached_loader.py` — Network failure + no cache: `DataSourceDownloadError` raised
  - [ ] 9.14 `tests/population/loaders/test_cached_loader.py` — Offline mode + cache hit: cached table returned
  - [ ] 9.15 `tests/population/loaders/test_cached_loader.py` — Offline mode + cache miss: `DataSourceOfflineError` raised
  - [ ] 9.16 `tests/population/loaders/test_cached_loader.py` — Schema validation: downloaded table that fails schema check raises `DataSourceValidationError`
  - [ ] 9.17 `tests/population/loaders/test_errors.py` — Exception message format follows `[summary] - [reason] - [fix]` pattern

- [ ] Task 10: Run full test suite and lint (AC: all)
  - [ ] 10.1 `uv run pytest tests/` — all tests pass
  - [ ] 10.2 `uv run ruff check src/ tests/` — no lint errors
  - [ ] 10.3 `uv run mypy src/` — no new mypy errors (pre-existing errors acceptable)

## Dev Notes

### Architecture Context: First Phase 2 Story

This is the **first story of Phase 2** and the first story in EPIC-11 (Realistic Population Generation Library). It creates a new subsystem (`population/`) that does not yet exist in the codebase. All subsequent EPIC-11 stories (11.2–11.8) depend on the protocol and caching infrastructure delivered here.

**Key architectural decision:** Phase 2 introduces the project's first optional network dependencies. Phase 1 had zero network calls at runtime. The caching infrastructure must ensure offline-first operation — network access is entirely opt-in and degradable.

### Protocol Design: Follow `ComputationAdapter` Pattern Exactly

The existing `ComputationAdapter` protocol in `src/reformlab/computation/adapter.py` is the reference implementation:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class DataSourceLoader(Protocol):
    """Interface for institutional data source loaders.

    Structural (duck-typed) protocol: any class that implements download(),
    status(), and schema() with correct signatures satisfies the contract.
    No explicit inheritance required.

    Each loader handles one institutional data source (e.g., INSEE, Eurostat).
    The loader downloads, schema-validates, caches, and returns pa.Table data.
    """

    def download(self, config: SourceConfig) -> pa.Table: ...
    def status(self, config: SourceConfig) -> CacheStatus: ...
    def schema(self) -> pa.Schema: ...
```

**Critical:** Use `@runtime_checkable` — same as `ComputationAdapter` and `OrchestratorStep`. This enables `isinstance(loader, DataSourceLoader)` checks at registration time.

### Cache Key Design: Hash-Based Freshness

The architecture specifies "Hash-based freshness (SHA256 of URL + params + date)." The `date` component should be a date prefix (e.g., `"2026-03"`) — not the full timestamp — to provide monthly freshness windows. This means:

```python
import hashlib

def cache_key(config: SourceConfig) -> str:
    """Deterministic cache key from source config + date prefix."""
    # Monthly granularity: data that's >1 month old is considered stale
    date_prefix = datetime.now(UTC).strftime("%Y-%m")
    raw = f"{config.url}|{'|'.join(f'{k}={v}' for k, v in sorted(config.params.items()))}|{date_prefix}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
```

**Stale detection:** If a cache file exists but its metadata `date_prefix` differs from the current month's prefix, the cache is considered "stale but usable." The `CacheStatus.stale` field reflects this.

### Cache Directory Layout

```
~/.reformlab/cache/
  sources/
    insee/
      household_income/
        a1b2c3d4e5f6g7h8.parquet       ← cached data
        a1b2c3d4e5f6g7h8.parquet.meta.json  ← metadata
      household_composition/
        ...
    eurostat/
      ...
    ademe/
      ...
    sdes/
      ...
```

**Metadata JSON schema:**
```json
{
  "url": "https://example.com/dataset",
  "params": {"year": "2024"},
  "downloaded_at": "2026-03-03T10:30:00+00:00",
  "content_hash": "sha256hexstring...",
  "date_prefix": "2026-03",
  "provider": "insee",
  "dataset_id": "household_income"
}
```

### No New Dependencies Required

The caching infrastructure uses only stdlib and existing dependencies:
- **`pathlib.Path`** — directory management, file paths
- **`hashlib`** — SHA-256 for cache keys and content hashes
- **`json`** — metadata files
- **`datetime`** — timestamps
- **`os.environ`** — `REFORMLAB_OFFLINE` check
- **`pyarrow.parquet`** — read/write cached Parquet files
- **`logging`** — governance warnings

No HTTP client library is needed in this story — `CachedLoader._fetch()` is an abstract method that concrete loaders (Stories 11.2, 11.3) will implement. Those stories may introduce `urllib.request` (stdlib) or a new dependency.

### `CachedLoader` — Not a Protocol, Not an ABC

The codebase rule is "Protocols, not ABCs." However, `CachedLoader` is neither — it's a **concrete base class** that provides shared cache-orchestration logic. Concrete loaders (INSEELoader, EurostatLoader) will subclass it and override `_fetch()` and `schema()`. This is acceptable because:

1. `DataSourceLoader` remains the Protocol (the interface contract)
2. `CachedLoader` is an implementation convenience, not an interface
3. Concrete loaders satisfy `DataSourceLoader` protocol via duck typing (they have `download()`, `status()`, `schema()`)

Pattern: `CachedLoader` is to `DataSourceLoader` what `OpenFiscaAdapter` is to `ComputationAdapter` — a concrete implementation that satisfies the protocol.

### Frozen Dataclass Conventions

Follow existing patterns exactly:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

@dataclass(frozen=True)
class SourceConfig:
    """Immutable configuration for a data source download."""
    provider: str
    dataset_id: str
    url: str
    params: dict[str, str] = field(default_factory=dict)
    description: str = ""

    def __post_init__(self) -> None:
        if not self.provider.strip():
            raise ValueError("provider must be a non-empty string")
        if not self.dataset_id.strip():
            raise ValueError("dataset_id must be a non-empty string")
        # Deep-copy mutable container (frozen dataclass pattern)
        object.__setattr__(self, "params", dict(self.params))
```

### Exception Hierarchy

Follow the `[summary] - [reason] - [fix]` pattern from `IngestionError`:

```python
class DataSourceError(Exception):
    """Base exception for data source operations."""
    def __init__(self, *, summary: str, reason: str, fix: str) -> None:
        self.summary = summary
        self.reason = reason
        self.fix = fix
        super().__init__(f"{summary} - {reason} - {fix}")
```

### Governance Integration Point

When stale cache is used, the warning string should be compatible with the existing `capture_warnings(additional_warnings=...)` pattern in `governance/capture.py`. The loader logs via `logging.getLogger(__name__).warning()` at runtime, and downstream callers (PopulationPipeline in Story 11.6) will collect these warnings for manifest inclusion.

### `from __future__ import annotations` — Every File

Per project rules, every Python file starts with this import. No exceptions.

### Logging Convention

```python
import logging
logger = logging.getLogger(__name__)
# Structured key=value format:
logger.warning("event=stale_cache_used provider=%s dataset_id=%s downloaded_at=%s hash=%s", ...)
```

### Test Structure

Mirror source layout per project rules:
```
tests/
  population/
    __init__.py
    conftest.py              ← shared fixtures (SourceConfig instances, tmp cache dirs)
    loaders/
      __init__.py
      conftest.py            ← loader-specific fixtures (mock tables, mock CachedLoader)
      test_base.py           ← Protocol, SourceConfig, CacheStatus tests
      test_cache.py          ← SourceCache tests (uses tmp_path)
      test_cached_loader.py  ← CachedLoader lifecycle tests (uses monkeypatch)
      test_errors.py         ← Exception tests
```

**Fixture patterns:**
- Use `tmp_path` for cache directories (no real `~/.reformlab` writes in tests)
- Use `monkeypatch.setenv("REFORMLAB_OFFLINE", "1")` for offline mode tests
- Build `pa.Table` fixtures inline (same as `tests/data/conftest.py`)
- Use class-based test grouping with Given/When/Then docstrings

**Mock CachedLoader for tests:**
```python
class MockCachedLoader(CachedLoader):
    """Test double that simulates network fetch."""
    def _fetch(self, config: SourceConfig) -> pa.Table:
        return self._mock_table  # set in test setup

    def schema(self) -> pa.Schema:
        return self._mock_schema
```

### mypy Configuration

Add a new override in `pyproject.toml` only if needed. Since the story only uses `pyarrow` (already has `ignore_missing_imports`) and stdlib, no new mypy overrides should be necessary.

### Project Structure Notes

- **New subsystem:** `src/reformlab/population/` — does not exist yet, must be created from scratch
- **Nested package:** `src/reformlab/population/loaders/` — follows architecture specification exactly
- **Alignment:** Directory structure matches `_bmad-output/planning-artifacts/architecture.md` "New Subsystem: Population Generation" section
- **No conflicts:** No existing code needs modification (except `pyproject.toml` for the `network` marker)
- **Build system:** No changes to `[tool.hatch.build.targets.wheel]` needed — `packages = ["src/reformlab"]` already covers all sub-packages

### Files Created (Expected)

**Source files:**
- `src/reformlab/population/__init__.py`
- `src/reformlab/population/loaders/__init__.py`
- `src/reformlab/population/loaders/base.py` — `DataSourceLoader` Protocol, `SourceConfig`, `CacheStatus`, `CachedLoader`
- `src/reformlab/population/loaders/cache.py` — `SourceCache` class
- `src/reformlab/population/loaders/errors.py` — `DataSourceError`, `DataSourceOfflineError`, `DataSourceDownloadError`, `DataSourceValidationError`

**Test files:**
- `tests/population/__init__.py`
- `tests/population/conftest.py`
- `tests/population/loaders/__init__.py`
- `tests/population/loaders/conftest.py`
- `tests/population/loaders/test_base.py`
- `tests/population/loaders/test_cache.py`
- `tests/population/loaders/test_cached_loader.py`
- `tests/population/loaders/test_errors.py`

**Modified files:**
- `pyproject.toml` — add `network` marker, update `addopts`

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#External-Data-Caching-&-Offline-Strategy] — Cache architecture, CacheStatus/DataSourceLoader protocol specifications, two-layer cache design
- [Source: _bmad-output/planning-artifacts/architecture.md#New-Subsystem-Population-Generation] — Directory structure, design principles
- [Source: _bmad-output/planning-artifacts/architecture.md#Populations-Phase-2-API] — Server-side `CacheStatusResponse` Pydantic model (future, not this story)
- [Source: _bmad-output/planning-artifacts/epics.md#BKL-1101] — Story definition and acceptance criteria
- [Source: _bmad-output/planning-artifacts/prd.md#FR36] — "Analyst can download and cache public datasets from institutional sources"
- [Source: _bmad-output/project-context.md#Python-Language-Rules] — Frozen dataclasses, Protocols, `from __future__ import annotations`
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules] — Subsystem-specific exceptions, structured logging
- [Source: src/reformlab/computation/adapter.py] — `ComputationAdapter` Protocol reference (pattern to follow)
- [Source: src/reformlab/orchestrator/step.py] — `OrchestratorStep` Protocol reference (pattern to follow)
- [Source: src/reformlab/data/pipeline.py] — `DataSourceMetadata`, `DatasetManifest`, `hash_file()` (existing data layer patterns)
- [Source: src/reformlab/governance/capture.py] — `capture_warnings(additional_warnings=...)` (governance warning integration point)
- [Source: src/reformlab/governance/hashing.py] — `hash_file()` with 64KB chunked SHA-256 (hashing pattern reference)
- [Source: src/reformlab/computation/ingestion.py] — `IngestionError` (exception message format reference)
- [Source: src/reformlab/server/dependencies.py] — `ResultCache` (LRU cache pattern reference)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

### Completion Notes List

### File List

## Change Log

- 2026-03-03: Story created by create-story workflow — comprehensive developer context with caching architecture, protocol patterns, and testing strategy.

]]></file>
</context>
<variables>
<var name="architecture_file" description="Architecture for technical requirements verification" load_strategy="SELECTIVE_LOAD" token_approx="2785">_bmad-output/planning-artifacts/architecture-diagrams.md</var>
<var name="author">BMad</var>
<var name="communication_language">English</var>
<var name="date">2026-03-03</var>
<var name="description">Quality competition validator - systematically review and improve story context created by create-story workflow</var>
<var name="document_output_language">English</var>
<var name="epic_num">11</var>
<var name="epics_file" description="Enhanced epics+stories file for story verification" load_strategy="SELECTIVE_LOAD" token_approx="22504">_bmad-output/planning-artifacts/epics.md</var>
<var name="implementation_artifacts">_bmad-output/implementation-artifacts</var>
<var name="installed_path">_bmad/bmm/workflows/4-implementation/validate-story</var>
<var name="instructions">/Users/lucas/Workspace/bmad-assist/src/bmad_assist/workflows/validate-story/instructions.xml</var>
<var name="model">validator</var>
<var name="name">validate-story</var>
<var name="output_folder">_bmad-output/implementation-artifacts</var>
<var name="planning_artifacts">_bmad-output/planning-artifacts</var>
<var name="prd_file" description="PRD for requirements verification" load_strategy="SELECTIVE_LOAD" token_approx="7305">_bmad-output/planning-artifacts/prd-validation-report.md</var>
<var name="project_context" file_id="b5c6fe32" load_strategy="EMBEDDED" token_approx="2024">embedded in prompt, file id: b5c6fe32</var>
<var name="project_knowledge">docs</var>
<var name="project_name">ReformLab</var>

<var name="story_dir">_bmad-output/implementation-artifacts</var>
<var name="story_file" file_id="c687cb63">embedded in prompt, file id: c687cb63</var>
<var name="story_id">11.1</var>
<var name="story_key">11-1-define-datasourceloader-protocol-and-caching-infrastructure</var>
<var name="story_num">1</var>
<var name="story_title">define-datasourceloader-protocol-and-caching-infrastructure</var>

<var name="timestamp">20260303_110448</var>
<var name="user_name">Lucas</var>
<var name="user_skill_level">expert</var>
<var name="ux_file" description="UX design for user experience verification" load_strategy="SELECTIVE_LOAD" token_approx="20820">_bmad-output/planning-artifacts/ux-design-specification.md</var>
<var name="validation_focus">story_quality</var>
</variables>
<instructions><workflow>
  <critical>You MUST have already loaded and processed: /Users/lucas/Workspace/reformlab/_bmad/bmm/workflows/4-implementation/validate-story/workflow.yaml</critical>
  <critical>Communicate all responses in English and generate all documents in English</critical>

  <critical>🔥 CRITICAL MISSION: You are an independent quality validator in a FRESH CONTEXT competing against the original create-story LLM!</critical>
  <critical>Your purpose is to thoroughly review a story file and systematically identify any mistakes, omissions, or disasters that the original LLM missed</critical>
  <critical>🚨 COMMON LLM MISTAKES TO PREVENT: reinventing wheels, wrong libraries, wrong file locations, breaking regressions, ignoring UX, vague implementations, lying about completion, not learning from past work</critical>
  <critical>🔬 UTILIZE SUBPROCESSES AND SUBAGENTS: Use research subagents or parallel processing if available to thoroughly analyze different artifacts simultaneously</critical>

  <step n="1" goal="Load and understand the target story">
    <action>Ask user for story file to validate</action>
    <substep n="1b" title="Load story and extract metadata">
      <action>Load the COMPLETE story file</action>
      <action>Extract metadata from story file:
        - epic_num: from story header (e.g., "Story 1.2" → epic_num=1)
        - story_num: from story header (e.g., "Story 1.2" → story_num=2)
        - story_key: filename without extension (e.g., "1-2-user-authentication")
        - story_title: from story header after colon
        - current_status: from Status field
      </action>
      <action>Store extracted values in workflow variables</action>
    </substep>

    <substep n="1c" title="Resolve workflow variables">
      <action>Resolve all paths: story_dir, output_folder, epics_file, architecture_file, etc.</action>
      <action>Verify story file exists and is readable</action>
      <action>Note current story content for gap analysis</action>
    </substep>

    <o>📋 **Target Story Loaded:**
      - Story ID: 11.1
      - Story Key: 11-1-define-datasourceloader-protocol-and-caching-infrastructure
      - Title: define-datasourceloader-protocol-and-caching-infrastructure
      - Current Status: {{current_status}}
    </o>
  </step>

  <step n="2" goal="Exhaustive source document re-analysis">
    <critical>🔥 CRITICAL: Treat this like YOU are creating the story from scratch to PREVENT DISASTERS!</critical>
    <critical>Discover everything the original LLM missed that could cause developer mistakes!</critical>

    <substep n="2a" title="Epics and Stories Analysis">
      <action>Invoke discover_inputs protocol for epics pattern</action>
      <invoke-protocol name="discover_inputs" />

      <action>Load /Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/epics.md (or sharded equivalents)</action>
      <action>Extract COMPLETE Epic 11 context:
        - Epic objectives and business value
        - ALL stories in this epic (for cross-story context)
        - Our specific story's requirements and acceptance criteria
        - Technical requirements and constraints
        - Cross-story dependencies and prerequisites
        - BDD scenarios if present
      </action>
      <action>Compare extracted requirements against current story file</action>
      <action>Note any missing or incomplete requirements</action>
    </substep>

    <substep n="2b" title="Architecture Deep-Dive">
      <action>Load /Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/architecture-diagrams.md (single or sharded)</action>
      <action>Systematically scan for ANYTHING relevant to this story:
        - Technical stack with versions (languages, frameworks, libraries)
        - Code structure and organization patterns
        - API design patterns and contracts
        - Database schemas and relationships
        - Security requirements and patterns
        - Performance requirements and optimization strategies
        - Testing standards and frameworks
        - Deployment and environment patterns
        - Integration patterns and external services
      </action>
      <action>Compare architecture requirements against current story file</action>
      <action>Note any missing architectural guidance</action>
    </substep>

    <substep n="2c" title="Previous Story Intelligence">
      <check if="1 &gt; 1">
        <action>Calculate previous story path: 11-{{story_num - 1}}-*.md</action>
        <action>Search /Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts for previous story file</action>
        <check if="previous story file exists">
          <action>Load previous story file</action>
          <action>Extract actionable intelligence:
            - Dev notes and learnings
            - Review feedback and corrections needed
            - Files created/modified and their patterns
            - Testing approaches that worked/didn't work
            - Problems encountered and solutions found
            - Code patterns and conventions established
          </action>
          <action>Note any previous story learnings missing from current story</action>
        </check>
      </check>
      <check if="1 == 1">
        <action>This is first story in epic - check for learnings from previous epic if exists</action>
      </check>
    </substep>

    <substep n="2d" title="Git History Analysis">
      <check if="git repository available">
        <action>Get last 5-10 commit titles to understand recent work patterns</action>
        <action>Analyze recent commits for relevance to current story:
          - Files created/modified in previous work
          - Code patterns and conventions used
          - Library dependencies added/changed
          - Architecture decisions implemented
          - Testing approaches used
        </action>
        <action>Note any git insights missing from current story</action>
      </check>
    </substep>

    <substep n="2e" title="Latest Technical Research">
      <action>Identify any libraries/frameworks mentioned in story and architecture</action>
      <action>Research latest versions and critical information:
        - Breaking changes or security updates
        - Performance improvements or deprecations
        - Best practices for current versions
        - API changes that affect implementation
      </action>
      <action>Note any outdated or missing technical information</action>
    </substep>

    <o>📊 **Source Document Re-Analysis Complete**
      - Epics analyzed: {{epics_analyzed_count}}
      - Architecture sections reviewed: {{arch_sections_count}}
      - Previous story learnings: {{previous_learnings_available}}
      - Git insights gathered: {{git_insights_available}}
      - Technical research completed: {{tech_research_count}}
    </o>
  </step>

  <step n="3" goal="Story Quality Gate - INVEST validation">
    <critical>🎯 RUTHLESS STORY VALIDATION: Check story quality with surgical precision!</critical>
    <critical>This assessment determines if the story is fundamentally sound before deeper analysis</critical>

    <substep n="3a" title="INVEST Criteria Validation">
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

    <substep n="3b" title="Acceptance Criteria Deep Analysis">
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

    <substep n="3c" title="Hidden Dependencies Discovery">
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

    <substep n="3d" title="Estimation Reality-Check">
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

    <substep n="3e" title="Technical Alignment Verification">
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

  <step n="4" goal="Disaster prevention gap analysis">
    <critical>🚨 CRITICAL: Identify every mistake the original LLM missed that could cause DISASTERS!</critical>

    <substep n="4a" title="Reinvention Prevention Gaps">
      <action>Analyze for wheel reinvention risks:
        - Areas where developer might create duplicate functionality
        - Code reuse opportunities not identified
        - Existing solutions not mentioned that developer should extend
        - Patterns from previous stories not referenced
      </action>
      <action>Document each reinvention risk found</action>
    </substep>

    <substep n="4b" title="Technical Specification Disasters">
      <action>Analyze for technical specification gaps:
        - Wrong libraries/frameworks: Missing version requirements
        - API contract violations: Missing endpoint specifications
        - Database schema conflicts: Missing requirements that could corrupt data
        - Security vulnerabilities: Missing security requirements
        - Performance disasters: Missing requirements that could cause failures
      </action>
      <action>Document each technical specification gap</action>
    </substep>

    <substep n="4c" title="File Structure Disasters">
      <action>Analyze for file structure issues:
        - Wrong file locations: Missing organization requirements
        - Coding standard violations: Missing conventions
        - Integration pattern breaks: Missing data flow requirements
        - Deployment failures: Missing environment requirements
      </action>
      <action>Document each file structure issue</action>
    </substep>

    <substep n="4d" title="Regression Disasters">
      <action>Analyze for regression risks:
        - Breaking changes: Missing requirements that could break existing functionality
        - Test failures: Missing test requirements
        - UX violations: Missing user experience requirements
        - Learning failures: Missing previous story context
      </action>
      <action>Document each regression risk</action>
    </substep>

    <substep n="4e" title="Implementation Disasters">
      <action>Analyze for implementation issues:
        - Vague implementations: Missing details that could lead to incorrect work
        - Completion lies: Missing acceptance criteria that could allow fake implementations
        - Scope creep: Missing boundaries that could cause unnecessary work
        - Quality failures: Missing quality requirements
      </action>
      <action>Document each implementation issue</action>
    </substep>
  </step>

  <step n="5" goal="LLM-Dev-Agent optimization analysis">
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

  <step n="6" goal="Categorize and prioritize improvements">
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

    <substep n="6b" title="Calculate Evidence Score">
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

  <step n="7" goal="Initialize validation report">
    
    </step>

  <step n="8" goal="Present validation results and improvement suggestions">
    <action>Parse user selection and mark issues for application</action>
  </step>

  <step n="9" goal="Apply selected improvements to story">
    <critical>Apply changes naturally - story should read as if created perfectly the first time</critical>
    <critical>DO NOT reference the review process, original LLM, or that changes were "added"</critical>

    <action>Load the story file: /Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/11-1-define-datasourceloader-protocol-and-caching-infrastructure.md</action>

    <check if="critical issues selected">
      <action>Apply each selected critical fix to story content</action>
      <action>Integrate naturally into existing sections</action>
    </check>

    <check if="enhancements selected">
      <action>Apply each selected enhancement to story content</action>
      <action>Add new sections only if necessary</action>
    </check>

    <check if="optimizations selected">
      <action>Apply each selected optimization to story content</action>
    </check>

    <check if="LLM optimizations selected">
      <action>Rewrite verbose sections for token efficiency</action>
      <action>Improve structure and clarity</action>
      <action>Make instructions more actionable and direct</action>
    </check>

    <action>Save updated story file</action>
    <action>Count total changes applied: {{changes_applied_count}}</action>

    </step>

  <step n="10" goal="Finalize report and present results">
    

    <o>**✅ STORY VALIDATION COMPLETE, Lucas!**

**Validation Report:** /Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/story-validations/validation-report-11-1-define-datasourceloader-protocol-and-caching-infrastructure-2026-03-03.md
**Story File:** /Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/11-1-define-datasourceloader-protocol-and-caching-infrastructure.md

**Evidence Score:** {{evidence_score}} → **{{evidence_verdict}}**

**Issues Found:**
- Critical: {{critical_count}}
- Enhancements: {{enhancement_count}}
- Optimizations: {{optimization_count}}
- LLM optimizations: {{llm_opt_count}}
- Changes applied: {{changes_applied_count}}
    </o>

    <check if="changes were applied">
      <o>**📋 Next Steps:**
1. ✅ Review the updated story file: `/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/11-1-define-datasourceloader-protocol-and-caching-infrastructure.md`
2. Verify applied changes meet your requirements
3. Run `dev-story` when ready for implementation
4. Run `code-review` after implementation complete
      </o>
    </check>

    <check if="no changes were applied">
      <o>**📋 Next Steps:**
1. Review this validation report for potential improvements
2. Manually apply any desired changes to the story file
3. Run `dev-story` when ready for implementation
4. Run `code-review` after implementation complete
      </o>
    </check>

    </step>

</workflow></instructions>
<critical>TEMPLATE USAGE: The template below shows the STRUCTURE and HEADINGS to follow. You MUST replace ALL {{variable}} placeholders with actual values from your analysis. You MUST expand {{#each X}} loops by listing actual items. NEVER output literal {{...}} syntax.</critical>
<output-template>
<!-- VALIDATION_REPORT_START -->
<![CDATA[

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

]]></output-template>
</compiled-workflow>