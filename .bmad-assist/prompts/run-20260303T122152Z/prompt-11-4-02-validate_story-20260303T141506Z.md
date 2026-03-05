<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 11 -->
<!-- Story: 4 -->
<!-- Phase: validate-story -->
<!-- Timestamp: 20260303T141506Z -->
<compiled-workflow>
<mission><![CDATA[

Adversarial Story Validation

Target: Story 11.4 - define-mergemethod-protocol-and-uniform-distribution-method

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

Status: done

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

- [x] Task 1: Create population subsystem package scaffold (AC: all — foundational)
  - [x] 1.1 Create `src/reformlab/population/__init__.py` with module docstring and public API exports
  - [x] 1.2 Create `src/reformlab/population/loaders/__init__.py` with public API exports
  - [x] 1.3 Create `src/reformlab/population/loaders/errors.py` with subsystem-specific exceptions
  - [x] 1.4 Create `tests/population/__init__.py` and `tests/population/conftest.py`
  - [x] 1.5 Create `tests/population/loaders/__init__.py` and `tests/population/loaders/conftest.py`

- [x] Task 2: Define `SourceConfig` frozen dataclass (AC: #1, #2, #3)
  - [x] 2.1 Define `SourceConfig` in `src/reformlab/population/loaders/base.py` as `@dataclass(frozen=True)` with fields: `provider: str`, `dataset_id: str`, `url: str`, `params: dict[str, str]` (default empty), `description: str` (default empty)
  - [x] 2.2 Add `__post_init__` validation: `provider` and `dataset_id` must be non-empty strings; normalize `params` via `object.__setattr__` for deep-copy protection

- [x] Task 3: Define `CacheStatus` frozen dataclass (AC: #6)
  - [x] 3.1 Define `CacheStatus` in `src/reformlab/population/loaders/base.py` as `@dataclass(frozen=True)` with fields: `cached: bool`, `path: Path | None`, `downloaded_at: datetime | None`, `hash: str | None`, `stale: bool`
  - [x] 3.2 Ensure `path` uses `Path` from `pathlib`, `downloaded_at` uses `datetime` from `datetime`

- [x] Task 4: Define `DataSourceLoader` protocol (AC: #1)
  - [x] 4.1 Define `DataSourceLoader` in `src/reformlab/population/loaders/base.py` as `@runtime_checkable class DataSourceLoader(Protocol)` with three methods:
    - `def download(self, config: SourceConfig) -> pa.Table: ...`
    - `def status(self, config: SourceConfig) -> CacheStatus: ...`
    - `def schema(self) -> pa.Schema: ...`
  - [x] 4.2 Add comprehensive docstring explaining structural typing, protocol purpose, and downstream loader expectations
  - [x] 4.3 Verify `isinstance()` check works at runtime (unit test)

- [x] Task 5: Implement `SourceCache` — disk-based caching infrastructure (AC: #2, #3, #4, #5)
  - [x] 5.1 Create `src/reformlab/population/loaders/cache.py` with `SourceCache` class
  - [x] 5.2 Constructor takes `cache_root: Path | None = None` (defaults to `~/.reformlab/cache/sources`)
  - [x] 5.3 Implement `cache_key(config: SourceConfig) -> str` — deterministic SHA-256 of `url + sorted(params) + date_prefix` (see Dev Notes for hash design)
  - [x] 5.4 Implement `cache_path(config: SourceConfig) -> Path` — returns `{cache_root}/{provider}/{dataset_id}/{cache_key}.parquet`
  - [x] 5.5 Implement `metadata_path(config: SourceConfig) -> Path` — returns `{cache_path}.meta.json` (stores download timestamp, hash, URL, params)
  - [x] 5.6 Implement `get(config: SourceConfig) -> tuple[pa.Table, CacheStatus] | None` — returns cached table + status if cache hit, `None` if miss
  - [x] 5.7 Implement `put(config: SourceConfig, table: pa.Table) -> CacheStatus` — write schema-validated Parquet + metadata JSON, compute SHA-256 of written file, return `CacheStatus`
  - [x] 5.8 Implement `status(config: SourceConfig) -> CacheStatus` — read metadata without loading table
  - [x] 5.9 Implement `is_offline() -> bool` — check `REFORMLAB_OFFLINE` env var (truthy: `"1"`, `"true"`, `"yes"`)
  - [x] 5.10 Ensure `cache_root` directory is created on first write (not on init — no side effects in constructor)
  - [x] 5.11 Use `pyarrow.parquet.write_table()` for cache writes and `pyarrow.parquet.read_table()` for reads

- [x] Task 6: Implement `CachedLoader` — base class wrapping protocol + cache (AC: #2, #3, #4, #5)
  - [x] 6.1 Create `CachedLoader` in `src/reformlab/population/loaders/base.py` (concrete class, not protocol) that wraps cache logic around the download lifecycle:
    - Constructor: `cache: SourceCache`, `logger: logging.Logger`
    - Abstract-ish method: `_fetch(config: SourceConfig) -> pa.Table` (subclasses override to do real HTTP download)
    - `download(config: SourceConfig) -> pa.Table` — orchestrates: check cache → if miss, check offline → fetch → validate schema → cache → return
    - `status(config: SourceConfig) -> CacheStatus` — delegates to `cache.status()`
    - `schema(self) -> pa.Schema` — abstract, subclasses must implement
  - [x] 6.2 In `download()`: on network failure (any `OSError`, `urllib.error.URLError`) with existing cache, use stale cache and log governance warning via `logging.getLogger(__name__).warning()`
  - [x] 6.3 In `download()`: when `REFORMLAB_OFFLINE=1` and cache miss, raise `DataSourceOfflineError` with clear message
  - [x] 6.4 In `download()`: when cache hit (not stale), return cached table directly without network
  - [x] 6.5 Governance warning format: `"WARNING: Using stale cache for %s/%s — network unavailable. Downloaded at %s, hash %s"` (provider, dataset_id, timestamp, hash)

- [x] Task 7: Define subsystem-specific exceptions (AC: #4, #5)
  - [x] 7.1 In `src/reformlab/population/loaders/errors.py`, define:
    - `DataSourceError(Exception)` — base exception with `*, summary: str, reason: str, fix: str` kwargs following project pattern
    - `DataSourceOfflineError(DataSourceError)` — raised when offline mode prevents download
    - `DataSourceDownloadError(DataSourceError)` — raised on network/download failures (without cache fallback)
    - `DataSourceValidationError(DataSourceError)` — raised when downloaded data fails schema validation
  - [x] 7.2 Message format: `f"{summary} - {reason} - {fix}"` (matches `IngestionError` pattern)

- [x] Task 8: Add `network` pytest marker to pyproject.toml (AC: CI fixture pattern)
  - [x] 8.1 Add `"network: marks tests requiring real network access to institutional APIs (opt-in with '-m network')"` to `[tool.pytest.ini_options].markers`
  - [x] 8.2 Update `addopts` to exclude `network`: `"-m 'not integration and not scale and not network'"`

- [x] Task 9: Write comprehensive tests (AC: all)
  - [x] 9.1 `tests/population/loaders/test_base.py` — Protocol compliance: verify `isinstance()` check, verify minimal conforming class satisfies protocol
  - [x] 9.2 `tests/population/loaders/test_base.py` — `SourceConfig`: construction, validation (empty provider/dataset_id rejected), frozen immutability, params deep-copy
  - [x] 9.3 `tests/population/loaders/test_base.py` — `CacheStatus`: construction with all fields, `None` defaults
  - [x] 9.4 `tests/population/loaders/test_cache.py` — `SourceCache.put()` + `get()` round-trip: write table, read back, verify content identical
  - [x] 9.5 `tests/population/loaders/test_cache.py` — Cache miss returns `None`
  - [x] 9.6 `tests/population/loaders/test_cache.py` — `status()` returns correct `CacheStatus` for cached and uncached datasets
  - [x] 9.7 `tests/population/loaders/test_cache.py` — Cache directory structure: verify `{provider}/{dataset_id}/{hash}.parquet` layout
  - [x] 9.8 `tests/population/loaders/test_cache.py` — Metadata JSON contains download timestamp, hash, URL, params
  - [x] 9.9 `tests/population/loaders/test_cache.py` — `is_offline()` respects `REFORMLAB_OFFLINE` env var (use `monkeypatch.setenv`)
  - [x] 9.10 `tests/population/loaders/test_cached_loader.py` — Cache hit: `_fetch()` is NOT called, cached table returned
  - [x] 9.11 `tests/population/loaders/test_cached_loader.py` — Cache miss: `_fetch()` IS called, result cached, table returned
  - [x] 9.12 `tests/population/loaders/test_cached_loader.py` — Network failure + existing cache: stale cache used, warning logged
  - [x] 9.13 `tests/population/loaders/test_cached_loader.py` — Network failure + no cache: `DataSourceDownloadError` raised
  - [x] 9.14 `tests/population/loaders/test_cached_loader.py` — Offline mode + cache hit: cached table returned
  - [x] 9.15 `tests/population/loaders/test_cached_loader.py` — Offline mode + cache miss: `DataSourceOfflineError` raised
  - [x] 9.16 `tests/population/loaders/test_cached_loader.py` — Schema validation: downloaded table that fails schema check raises `DataSourceValidationError`
  - [x] 9.17 `tests/population/loaders/test_errors.py` — Exception message format follows `[summary] - [reason] - [fix]` pattern

- [x] Task 10: Run full test suite and lint (AC: all)
  - [x] 10.1 `uv run pytest tests/` — all tests pass (52 new, 1589 total; 1 pre-existing memory assertion failure unrelated)
  - [x] 10.2 `uv run ruff check src/ tests/` — no lint errors
  - [x] 10.3 `uv run mypy src/reformlab/population/` — no mypy errors (strict mode, 5 source files)

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

No issues encountered during implementation. All code passed on first attempt.

### Completion Notes List

- All 6 acceptance criteria satisfied and tested
- AC1: `DataSourceLoader` protocol is `@runtime_checkable` with `download()`, `status()`, `schema()` — tested with conforming and non-conforming classes
- AC2: `SourceCache.put()` writes schema-validated Parquet + metadata JSON with SHA-256 hash to `{provider}/{dataset_id}/` layout
- AC3: `CachedLoader.download()` returns cached table on fresh cache hit without calling `_fetch()`
- AC4: `CachedLoader.download()` falls back to stale cache on `OSError` and logs structured governance warning
- AC5: `CachedLoader.download()` raises `DataSourceOfflineError` when `REFORMLAB_OFFLINE=1` and cache miss
- AC6: `SourceCache.status()` returns `CacheStatus` with all required fields (cached, path, downloaded_at, hash, stale)
- 52 tests across 4 test files, all passing
- ruff clean, mypy strict clean (5 source files)
- No new dependencies required — uses stdlib + pyarrow only
- Follows existing codebase patterns: `ComputationAdapter` (protocol), `IngestionError` (exceptions), `hash_file()` (hashing)

### File List

**New source files:**
- `src/reformlab/population/__init__.py`
- `src/reformlab/population/loaders/__init__.py`
- `src/reformlab/population/loaders/base.py`
- `src/reformlab/population/loaders/cache.py`
- `src/reformlab/population/loaders/errors.py`

**New test files:**
- `tests/population/__init__.py`
- `tests/population/conftest.py`
- `tests/population/loaders/__init__.py`
- `tests/population/loaders/conftest.py`
- `tests/population/loaders/test_base.py`
- `tests/population/loaders/test_cache.py`
- `tests/population/loaders/test_cached_loader.py`
- `tests/population/loaders/test_errors.py`

**Modified files:**
- `pyproject.toml` — added `network` pytest marker and updated `addopts`

## Senior Developer Review (AI)

### Review: 2026-03-03
- **Reviewer:** AI Code Review Engine
- **Evidence Score:** 1.0 -> APPROVED
- **Issues Found:** 12
- **Issues Fixed:** 12
- **Action Items Created:** 0

### Fixes Applied

- Tightened stale-cache matching: stale fallback now only considers entries with matching `provider`, `dataset_id`, `url`, and `params`.
- Made stale-cache selection deterministic by choosing the newest matching entry based on metadata `downloaded_at`.
- Avoided eager stale-table loading: `CachedLoader.download()` now checks `status()` first and only loads stale tables when fallback is actually needed.
- Fixed exception handling so stale fallback is only used for `OSError` network failures; non-network errors now propagate instead of being masked.
- Reused shared hashing utility (`reformlab.governance.hashing.hash_file`) instead of local duplicate hashing logic.
- Added stronger `SourceConfig` validation for empty `url` and path-separator safety on `provider`/`dataset_id`.
- Added runtime guard in `CachedLoader.__init__` to reject subclasses that fail to implement `schema()` or `_fetch()`.
- Added missing `from __future__ import annotations` to empty package initializers in `tests/population/` and `tests/population/loaders/`.
- Expanded tests to cover stale status reporting, stale candidate matching/selection, stale-entry pruning, non-network exception behavior, and constructor guard behavior.

### Verification

- `uv run ruff check src/reformlab/population tests/population` -> pass
- `uv run pytest tests/population/loaders -q` -> 62 passed

## Change Log

- 2026-03-03: Story created by create-story workflow — comprehensive developer context with caching architecture, protocol patterns, and testing strategy.
- 2026-03-03: Story implemented — all 10 tasks complete, 52 tests passing, ruff clean, mypy strict clean.
- 2026-03-03: Senior code review fixes applied — stale-cache matching/selection corrected, error handling hardened, shared hashing utility reused, and test suite extended to 62 passing tests.


]]></file>
<file id="51f70c3b" path="_bmad-output/implementation-artifacts/11-2-implement-insee-data-source-loader.md" label="STORY FILE"><![CDATA[


# Story 11.2: Implement INSEE data source loader

Status: complete

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform developer building the French household population pipeline,
I want an INSEE data source loader that downloads, caches, and schema-validates key INSEE Filosofi income distribution datasets (commune-level and IRIS-level),
so that downstream merge methods (Stories 11.4–11.6) can consume real French public data as `pa.Table` objects through the `DataSourceLoader` protocol.

## Acceptance Criteria

1. Given a valid INSEE dataset identifier, when the loader downloads it, then a schema-validated `pa.Table` is returned with documented columns.
2. Given the INSEE loader, when queried for available datasets, then at least 3 income distribution datasets at commune and IRIS granularity are available.
3. Given an invalid or unavailable INSEE dataset ID, when requested, then a clear error identifies the specific dataset and suggests alternatives.
4. Given the INSEE loader, when run in CI, then tests use fixture files (no real network calls) marked with `pytest -m network` for opt-in integration tests.

## Tasks / Subtasks

- [x] Task 1: Define INSEE dataset catalog and schema constants (AC: #1, #2, #3)
  - [x] 1.1 Create `src/reformlab/population/loaders/insee.py` with module docstring referencing Story 11.2, FR36, FR37
  - [x] 1.2 Define `INSEEDataset` frozen dataclass with fields: `dataset_id: str`, `description: str`, `url: str`, `file_format: str` (csv or zip), `encoding: str` (default "utf-8"), `separator: str` (default ";"), `null_markers: tuple[str, ...] = ("s", "nd", "")` (INSEE suppression markers), `columns: tuple[tuple[str, str], ...] = ()` where each inner tuple is `(raw_insee_column_name, project_column_name)` — serves as both documentation and rename mapping
  - [x] 1.3 Define the INSEE dataset catalog as a module-level `dict[str, INSEEDataset]` mapping dataset IDs to their metadata. Include at minimum:
    - `"filosofi_2021_commune"` — Filosofi 2021 commune-level income data (deciles D1–D9, median, poverty rate)
    - `"filosofi_2021_iris_declared"` — Filosofi 2021 IRIS-level declared income
    - `"filosofi_2021_iris_disposable"` — Filosofi 2021 IRIS-level disposable income
  - [x] 1.4 Define a `pa.Schema` per dataset for the output columns the loader produces (subset of raw columns, renamed/typed to project conventions)
  - [x] 1.5 Add a `AVAILABLE_DATASETS` module-level constant exposing the catalog keys for discovery

- [x] Task 2: Implement `INSEELoader` class extending `CachedLoader` (AC: #1, #2)
  - [x] 2.1 `INSEELoader.__init__(self, *, cache: SourceCache, logger: logging.Logger, dataset: INSEEDataset)` — store the dataset reference, call `super().__init__()`
  - [x] 2.2 Implement `schema(self) -> pa.Schema` — return the schema for the loader's dataset
  - [x] 2.3 Implement `_fetch(self, config: SourceConfig) -> pa.Table` — download from `config.url` using `urllib.request`, parse using `self._dataset.encoding` and `self._dataset.separator` for format metadata (SourceConfig carries URL + cache key; INSEEDataset carries format/encoding metadata), select and rename columns per `self._dataset.columns` mapping, cast types to match `self.schema()`, return `pa.Table`
  - [x] 2.4 Handle ZIP-wrapped CSV files (INSEE often wraps CSVs in ZIP archives): detect `.zip` suffix in URL, extract using `zipfile.ZipFile(io.BytesIO(raw_bytes))`, find the first entry whose name ends with `.csv` (case-insensitive) via `namelist()`. If zero or multiple `.csv` files are found, raise `DataSourceValidationError` with a clear message listing the archive contents
  - [x] 2.5 On any network error (`urllib.error.URLError`, `OSError`, `http.client.HTTPException`), re-raise as `OSError` so `CachedLoader.download()` can handle stale-cache fallback correctly
  - [x] 2.6 Add structured logging: `event=fetch_start`, `event=fetch_complete` with `provider=insee dataset_id=... url=... rows=... columns=...`

- [x] Task 3: Implement `get_insee_loader` factory function (AC: #2, #3)
  - [x] 3.1 Create `get_insee_loader(dataset_id: str, *, cache: SourceCache, logger: logging.Logger | None = None) -> INSEELoader` factory that looks up dataset from catalog and constructs the loader
  - [x] 3.2 When `dataset_id` is not in the catalog, raise `DataSourceValidationError` with summary "Unknown INSEE dataset", reason listing the requested ID, and fix listing available dataset IDs
  - [x] 3.3 When `logger` is `None`, default to `logging.getLogger("reformlab.population.loaders.insee")`

- [x] Task 4: Implement `make_insee_config` helper (AC: #1, #2)
  - [x] 4.1 Create `make_insee_config(dataset_id: str, **params: str) -> SourceConfig` convenience function that constructs a `SourceConfig` from the catalog entry, using `provider="insee"`, the catalog's URL, and any additional params
  - [x] 4.2 When `dataset_id` is not in the catalog, raise `DataSourceValidationError` with guidance

- [x] Task 5: Update `__init__.py` exports (AC: all)
  - [x] 5.1 Add `INSEELoader`, `INSEEDataset`, `AVAILABLE_DATASETS`, `get_insee_loader`, `make_insee_config` to `src/reformlab/population/loaders/__init__.py`
  - [x] 5.2 Add the same exports to `src/reformlab/population/__init__.py`

- [x] Task 6: Create test fixtures (AC: #4)
  - [x] 6.1 Create `tests/fixtures/insee/` directory
  - [x] 6.2 Create small CSV fixture files mimicking Filosofi commune-level format (5-10 rows, semicolon-separated, UTF-8, with real column names from INSEE)
  - [x] 6.3 Create a small Parquet fixture file mimicking the relevant schema
  - [x] 6.4 Add conftest fixtures in `tests/population/loaders/conftest.py`: `insee_fixture_dir`, `filosofi_commune_csv_path`, `filosofi_commune_table`

- [x] Task 7: Write comprehensive tests (AC: all)
  - [x] 7.1 `tests/population/loaders/test_insee.py` — `TestINSEELoaderProtocol`: `INSEELoader` instance satisfies `DataSourceLoader` protocol via `isinstance()` check
  - [x] 7.2 `TestINSEELoaderSchema`: `schema()` returns a valid `pa.Schema` with expected field names and types for each dataset
  - [x] 7.3 `TestINSEELoaderFetch`: monkeypatch `urllib.request.urlopen` to return fixture CSV content; verify `_fetch()` returns correctly-parsed `pa.Table` with expected columns and types
  - [x] 7.4 `TestINSEELoaderFetchZip`: monkeypatch `urllib.request.urlopen` to return a ZIP-wrapped CSV fixture; verify extraction and parsing
  - [x] 7.5 `TestINSEELoaderFetchEncodingFallback`: verify Latin-1 fallback when UTF-8 decode fails
  - [x] 7.5b `TestINSEELoaderFetchSuppressedValues`: verify that fixture rows containing `"s"` and `"nd"` in numeric income columns produce `null` values (not parse errors) in the output table
  - [x] 7.5c `TestINSEELoaderFetchHTTPError`: monkeypatch `urllib.request.urlopen` to raise `urllib.error.HTTPError(url, 404, 'Not Found', {}, None)` — verify it is caught and re-raised as `OSError` so `CachedLoader.download()` handles it correctly
  - [x] 7.6 `TestINSEELoaderDownloadIntegration`: full `download()` cycle via `CachedLoader` — cache miss → fetch → cache → cache hit (uses monkeypatched `_fetch`, no real network)
  - [x] 7.7 `TestINSEELoaderCatalog`: verify `AVAILABLE_DATASETS` contains at least the required datasets, `get_insee_loader` returns correct loader, invalid ID raises error with suggestions
  - [x] 7.8 `TestMakeInseeConfig`: verify `make_insee_config` produces correct `SourceConfig` for each catalog entry
  - [x] 7.9 `tests/population/loaders/test_insee_network.py` — `@pytest.mark.network` integration tests: real HTTP download of a small Filosofi commune-level file, verify schema and row count are reasonable. These tests are excluded from CI by default.

- [x] Task 8: Run full test suite and lint (AC: all)
  - [x] 8.1 `uv run pytest tests/population/` — all tests pass
  - [x] 8.2 `uv run ruff check src/reformlab/population/ tests/population/` — no lint errors
  - [x] 8.3 `uv run mypy src/reformlab/population/` — no mypy errors (strict mode)

## Dev Notes

### Architecture Context: First Concrete Loader

This is the **first concrete `DataSourceLoader` implementation** in the codebase. Story 11.1 delivered the protocol, caching infrastructure, and `CachedLoader` base class. This story proves the pattern works end-to-end with a real institutional data source.

Story 11.3 (Eurostat, ADEME, SDES loaders) depends on this story establishing the concrete loader pattern. The pattern established here becomes the template for all subsequent loaders.

### INSEE Data Sources — What to Download

INSEE provides data as **direct file downloads** from `https://www.insee.fr/fr/statistiques/fichier/...`. No authentication is required. No API key needed. Files are publicly accessible via anonymous HTTPS GET.

**Key datasets for carbon tax microsimulation:**

| Dataset ID | Source | Format | Size | What it provides |
|---|---|---|---|---|
| `filosofi_2021_commune` | Filosofi 2021 | CSV | ~3 KB | Income deciles (D1–D9), median, poverty rates by commune |
| `filosofi_2021_iris_declared` | Filosofi 2021 IRIS | CSV | ~835 KB | Declared income quartiles/deciles at IRIS level |
| `filosofi_2021_iris_disposable` | Filosofi 2021 IRIS | CSV | ~892 KB | Disposable income quartiles/deciles at IRIS level |

**Important context:**
- Filosofi 2021 is the **last available vintage** — the 2022 vintage was not produced due to the housing tax (taxe d'habitation) suppression disrupting fiscal data sources.
- INSEE census (Recensement RP) files are very large (400–700 MB) and are better handled by a separate config/dataset entry for opt-in loading. Start with the small Filosofi files.
- INSEE CSVs use **semicolon separators** (`;`) and are predominantly **UTF-8** for recent files (2021+). Older vintages (pre-2020) may use Latin-1 or Windows-1252.

### INSEE CSV Format Specifics

Filosofi commune-level CSV structure (tab `filo2021_cc_rev.csv`):
- Separator: `;`
- Encoding: UTF-8 (modern files)
- Header row with INSEE variable codes (e.g., `CODGEO`, `LIBGEO`, `NBMENFISC21`, `MED21`, `D121`, `D221`, ..., `D921`)
- `CODGEO` = commune code (5 chars), `LIBGEO` = commune name
- `MED21` = median standard of living, `D121`–`D921` = income decile thresholds
- `NBMENFISC21` = number of fiscal households

**INSEE null value markers:** Filosofi files use `"s"` (secret statistique — suppressed for privacy when cell size is too small) and `"nd"` (non disponible — data not available) as string placeholders in numeric columns. Small communes regularly have suppressed decile values. These must be treated as nulls during parsing.

The loader should:
1. Download the raw CSV
2. Parse with semicolon separator and UTF-8 encoding (Latin-1 fallback)
3. Configure null value markers: `pyarrow.csv.ConvertOptions(null_values=["s", "nd", ""])`
4. Select relevant columns and rename to project-standard names (e.g., `CODGEO` → `commune_code`, `MED21` → `median_income`, `D121` → `decile_1`, etc.)
5. Cast to appropriate PyArrow types using `ConvertOptions(column_types={...})` — `commune_code` as `utf8`, income values as `float64`
6. Return as `pa.Table`

### HTTP Download — stdlib Only

The project has **no HTTP client library** in its dependencies (no `requests`, no `httpx`). Use `urllib.request` from stdlib:

```python
import io
import urllib.error
import urllib.request

def _fetch(self, config: SourceConfig) -> pa.Table:
    self._logger.debug(
        "event=fetch_start provider=%s dataset_id=%s url=%s",
        config.provider, config.dataset_id, config.url,
    )
    try:
        with urllib.request.urlopen(config.url, timeout=300) as response:
            raw_bytes = response.read()
    except (urllib.error.URLError, OSError) as exc:
        raise OSError(
            f"Failed to download {config.provider}/{config.dataset_id} from {config.url}: {exc}"
        ) from exc
    # Parse raw_bytes → pa.Table
    ...
```

**ZIP handling:** Some INSEE files are distributed as `.zip` archives. Detect by URL suffix or content-type and extract using `zipfile.ZipFile(io.BytesIO(raw_bytes))`.

**Encoding fallback:** Try UTF-8 first, fall back to Latin-1 on `UnicodeDecodeError`. This is a common pattern for INSEE files.

### Schema Design

Each dataset should have a defined output schema. The loader transforms raw INSEE column names to project-standard names:

**Filosofi commune-level output schema (example):**
```python
pa.schema([
    pa.field("commune_code", pa.utf8()),        # CODGEO
    pa.field("commune_name", pa.utf8()),         # LIBGEO
    pa.field("nb_fiscal_households", pa.int64()),# NBMENFISC21
    pa.field("median_income", pa.float64()),     # MED21
    pa.field("decile_1", pa.float64()),          # D121
    pa.field("decile_2", pa.float64()),          # D221
    pa.field("decile_3", pa.float64()),          # D321
    pa.field("decile_4", pa.float64()),          # D421
    pa.field("decile_5", pa.float64()),          # D521 (= median)
    pa.field("decile_6", pa.float64()),          # D621
    pa.field("decile_7", pa.float64()),          # D721
    pa.field("decile_8", pa.float64()),          # D821
    pa.field("decile_9", pa.float64()),          # D921
])
```

The column renaming mapping should be defined as a constant per dataset, keeping raw INSEE names documented in comments.

**Mandatory type casting:** `CachedLoader.download()` enforces exact column name and type equality against `schema()` (see `base.py:260-270`). `_fetch()` **must** return a `pa.Table` with (1) project-standard column names (not raw INSEE names), and (2) exact types matching the schema (`float64`, not auto-inferred `int64` or `string`). Use `pyarrow.csv.ConvertOptions(column_types={...})` to enforce types at parse time. The validation gate raises `DataSourceValidationError` before caching if types don't match.

### No New Dependencies Required

Everything is achievable with:
- `urllib.request` / `urllib.error` — HTTP downloads (stdlib)
- `zipfile` — ZIP extraction (stdlib)
- `io.BytesIO` — in-memory file handling (stdlib)
- `pyarrow` / `pyarrow.csv` — CSV parsing, table construction, and Parquet I/O (existing dependency)

Do **not** introduce `requests`, `pandas`, or `pynsee` as dependencies.

### CSV Parsing Strategy: pyarrow.csv

Use `pyarrow.csv.read_csv()` exclusively — it is efficient, already a project dependency, and handles type casting and null values natively. Do not use stdlib `csv` module.

```python
import pyarrow.csv as pcsv

read_options = pcsv.ReadOptions(encoding=encoding)
parse_options = pcsv.ParseOptions(delimiter=separator)
convert_options = pcsv.ConvertOptions(
    null_values=["s", "nd", ""],       # INSEE suppressed/unavailable markers
    column_types={"commune_code": pa.string(), "median_income": pa.float64(), ...},
    include_columns=["CODGEO", "LIBGEO", ...],  # Select only relevant raw columns
)
table = pcsv.read_csv(io.BytesIO(raw_bytes), read_options=read_options,
                       parse_options=parse_options, convert_options=convert_options)
# Then rename columns from raw INSEE names to project names
```

Use `ConvertOptions` for column selection, type casting, and null value handling. Column renaming is done after parsing using the `INSEEDataset.columns` mapping.

### `INSEEDataset` Design

```python
@dataclass(frozen=True)
class INSEEDataset:
    """Metadata for a known INSEE dataset."""
    dataset_id: str
    description: str
    url: str
    file_format: str  # "csv" or "zip" (INSEE distributes CSV or ZIP-wrapped CSV)
    encoding: str = "utf-8"
    separator: str = ";"
    null_markers: tuple[str, ...] = ("s", "nd", "")  # INSEE suppression markers
    columns: tuple[tuple[str, str], ...] = ()  # (raw_name, project_name) pairs
```

The `columns` field serves as both documentation and the rename mapping. `null_markers` configures `pyarrow.csv.ConvertOptions(null_values=...)`.

### Test Fixture Design

Create minimal CSV fixtures that mimic real INSEE format:

```csv
CODGEO;LIBGEO;NBMENFISC21;MED21;D121;D221;D321;D421;D521;D621;D721;D821;D921
01001;L'Abergement-Clémenciat;330;22050;12180;14790;17120;19460;22050;24950;28420;33500;42890
01002;L'Abergement-de-Varey;100;23800;13500;16200;18900;21300;23800;26700;30200;35100;44500
01003;Ambérieu-en-Bugey;5200;19850;10200;12500;14800;17200;19850;22800;26500;31800;41200
01004;Ambérieux-en-Dombes;s;s;s;s;s;s;s;s;s;s;s
01005;Ambléon;nd;nd;nd;nd;nd;nd;nd;nd;nd;nd;nd
```

Include at least one row with `"s"` (suppressed) and one with `"nd"` (non-available) markers — these are critical for testing null handling. Keep fixtures small (5-10 rows) and realistic. Store in `tests/fixtures/insee/`. Use `tmp_path` in tests for cache directories.

### Network Integration Tests

Create `tests/population/loaders/test_insee_network.py` with `@pytest.mark.network` marker. These tests hit real INSEE servers and are excluded from CI by default (`addopts = "-m 'not integration and not scale and not network'"`).

```python
@pytest.mark.network
class TestINSEELoaderRealDownload:
    def test_filosofi_commune_real_download(self, tmp_path):
        """Given a real INSEE URL, when downloaded, then returns valid table."""
        ...
```

### Project Structure Notes

- **New file:** `src/reformlab/population/loaders/insee.py` — the INSEE loader implementation
- **Modified files:**
  - `src/reformlab/population/loaders/__init__.py` — add `INSEELoader` exports
  - `src/reformlab/population/__init__.py` — add `INSEELoader` exports
  - `tests/population/loaders/conftest.py` — add INSEE fixture helpers
- **New test files:**
  - `tests/population/loaders/test_insee.py` — unit tests
  - `tests/population/loaders/test_insee_network.py` — network integration tests
- **New fixture directory:** `tests/fixtures/insee/`
- **No changes** to `pyproject.toml` (no new dependencies, `network` marker already exists from 11.1)

### Alignment with Architecture

The architecture specifies `src/reformlab/population/loaders/insee.py` explicitly. The loader satisfies `DataSourceLoader` protocol via `CachedLoader` base class, matching the pattern specified in the "External Data Caching & Offline Strategy" architecture section.

### Error Handling Notes

- `_fetch()` should only raise `OSError` for network errors — `CachedLoader.download()` handles everything else
- Invalid dataset IDs → `DataSourceValidationError` (from factory function, not from `_fetch`)
- Schema mismatches are caught by `CachedLoader.download()` automatically after `_fetch()` returns
- INSEE servers returning 404 or error pages → `urllib.error.HTTPError` (subclass of `urllib.error.URLError`) → caught by the `except (urllib.error.URLError, OSError)` clause → re-raised as `OSError`

### INSEE Data Encoding Notes

| File vintage | Encoding | Notes |
|---|---|---|
| Filosofi 2021+ | UTF-8 | Modern files, confirmed in documentation |
| RP Census 2021+ | UTF-8 | Parquet files have no encoding issues |
| Older files (pre-2020) | Latin-1 or cp1252 | Some data.gouv.fr hosted files |

The loader should try UTF-8 first, catch `UnicodeDecodeError`, then retry with Latin-1. Log the fallback as a debug event.

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#New-Subsystem-Population-Generation] — Directory structure, `insee.py` file specification
- [Source: _bmad-output/planning-artifacts/architecture.md#External-Data-Caching-&-Offline-Strategy] — Cache protocol, offline semantics, `DataSourceLoader` protocol
- [Source: _bmad-output/planning-artifacts/epics.md#BKL-1102] — Story definition and acceptance criteria
- [Source: _bmad-output/planning-artifacts/prd.md#FR36] — "Analyst can download and cache public datasets from institutional sources (INSEE, Eurostat, ADEME, SDES)"
- [Source: _bmad-output/planning-artifacts/prd.md#FR37] — "Analyst can browse available datasets and select which to include in a population"
- [Source: _bmad-output/project-context.md#Python-Language-Rules] — Frozen dataclasses, Protocols, `from __future__ import annotations`
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules] — PyArrow canonical data type, no pandas in core logic
- [Source: src/reformlab/population/loaders/base.py] — `DataSourceLoader` Protocol, `CachedLoader` base class, `SourceConfig`, `CacheStatus`
- [Source: src/reformlab/population/loaders/cache.py] — `SourceCache` caching infrastructure
- [Source: src/reformlab/population/loaders/errors.py] — `DataSourceError` hierarchy
- [Source: tests/population/loaders/conftest.py] — `MockCachedLoader` pattern, test fixtures
- [Source: _bmad-output/implementation-artifacts/11-1-define-datasourceloader-protocol-and-caching-infrastructure.md] — Predecessor story (protocol + caching), patterns to follow
- [Source: INSEE Filosofi 2021 commune-level] — https://www.insee.fr/fr/statistiques/7758831 (income deciles by commune)
- [Source: INSEE Filosofi 2021 IRIS-level] — https://www.insee.fr/fr/statistiques/8229323 (income at IRIS level)
- [Source: INSEE API documentation] — https://www.insee.fr/fr/information/8184146 (no auth needed for file downloads)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

No debug issues encountered. All tests passed on first run after lint fixes.

### Completion Notes List

- Implemented `INSEELoader` as the first concrete `DataSourceLoader` in the codebase, extending `CachedLoader` base class from Story 11.1
- `INSEEDataset` frozen dataclass holds per-dataset metadata (URL, encoding, separator, null markers, column mapping)
- `INSEE_CATALOG` maps 3 dataset IDs to `INSEEDataset` instances: `filosofi_2021_commune`, `filosofi_2021_iris_declared`, `filosofi_2021_iris_disposable`
- Per-dataset `pa.Schema` definitions enforce exact types (utf8 for codes/names, float64 for all numeric columns including `nb_fiscal_households` — required because INSEE suppression markers make the column nullable)
- ZIP extraction handles `.csv` suffix detection (case-insensitive), with clear errors for 0 or >1 CSV entries
- CSV parsing uses `pyarrow.csv.read_csv()` with `ConvertOptions(null_values=["s","nd",""], column_types={...}, include_columns=[...])` for column selection, type casting, and null handling in one pass
- Encoding fallback: tries primary encoding (UTF-8), catches `pa.ArrowInvalid`, retries with Latin-1
- Network errors caught and re-raised as `OSError` for `CachedLoader.download()` stale-cache fallback
- 35 unit tests covering protocol compliance, schema correctness, CSV parsing, ZIP extraction, encoding fallback, suppressed values, HTTP errors, full download lifecycle, catalog/factory, and config helpers
- 1 network integration test (`@pytest.mark.network`) excluded from CI by default
- Full test suite: 1635 passed, 0 failures, 0 regressions

### File List

**New files:**
- `src/reformlab/population/loaders/insee.py` — INSEE loader implementation
- `tests/population/loaders/test_insee.py` — 35 unit tests
- `tests/population/loaders/test_insee_network.py` — network integration tests
- `tests/fixtures/insee/filosofi_2021_commune.csv` — commune-level CSV fixture (5 rows, includes "s" and "nd" markers)
- `tests/fixtures/insee/filosofi_2021_iris_declared.csv` — IRIS declared income CSV fixture (3 rows)
- `tests/fixtures/insee/filosofi_2021_iris_disposable.csv` — IRIS disposable income CSV fixture (3 rows)

**Modified files:**
- `src/reformlab/population/loaders/__init__.py` — added INSEE exports
- `src/reformlab/population/__init__.py` — added INSEE exports
- `tests/population/loaders/conftest.py` — added INSEE fixture helpers

## Change Log

- 2026-03-03: Story created by create-story workflow — comprehensive developer context with INSEE data source details, CSV parsing strategy, schema design, and test fixture approach.
- 2026-03-03: Post-validation fixes — aligned AC#2 with actual catalog scope (income datasets only, household composition deferred), fixed INSEEDataset.columns type to tuple[tuple[str,str],...] rename mapping, added INSEE null marker handling (s/nd), added mandatory type casting callout, consolidated CSV parsing to pyarrow.csv only, clarified ZIP extraction strategy, added suppressed values and HTTP error test cases.
- 2026-03-03: Story implemented — all 8 tasks complete, 35 unit tests + 1 network integration test, full suite green (1635 passed), ruff clean, mypy strict clean.


]]></file>
<file id="7243a2d9" path="_bmad-output/implementation-artifacts/11-3-implement-eurostat-ademe-sdes-data-source-loaders.md" label="STORY FILE"><![CDATA[


# Story 11.3: Implement Eurostat, ADEME, and SDES data source loaders

Status: dev-complete

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform developer building the French household population pipeline,
I want concrete data source loaders for Eurostat (EU-SILC income distribution, household energy consumption), ADEME (Base Carbone emission factors), and SDES (vehicle fleet composition),
so that downstream merge methods (Stories 11.4–11.6) can consume real European and French public data as schema-validated `pa.Table` objects through the `DataSourceLoader` protocol.

## Acceptance Criteria

1. Given the Eurostat loader, when called with a valid dataset code, then EU-level household data is returned as a schema-validated `pa.Table`.
2. Given the ADEME loader, when called, then energy consumption and emission factor datasets are returned with documented schemas.
3. Given the SDES loader, when called, then vehicle fleet composition data (including vehicle age classification) is returned as a schema-validated `pa.Table`.
4. Given all three loaders, when run, then each follows the `DataSourceLoader` protocol and integrates with the caching infrastructure from BKL-1101.
5. Given CI tests for all loaders, then they use fixture files and do not require network access.

## Tasks / Subtasks

- [x] Task 1: Create Eurostat loader — `eurostat.py` (AC: #1, #4)
  - [x]1.1 Create `src/reformlab/population/loaders/eurostat.py` with module docstring referencing Story 11.3, FR36, FR37
  - [x]1.2 Define `EurostatDataset` frozen dataclass with fields: `dataset_id: str`, `description: str`, `url: str`, `encoding: str = "utf-8"`, `separator: str = ","`, `null_markers: tuple[str, ...] = ("", ":")`, `columns: tuple[tuple[str, str], ...] = ()` where each inner tuple is `(raw_sdmx_column_name, project_column_name)` — consistent with `INSEEDataset`/`ADEMEDataset`/`SDESDataset` pattern where the dataclass is the single source of truth for parsing configuration
  - [x]1.3 Define `EUROSTAT_CATALOG` as module-level `dict[str, EurostatDataset]` with at minimum:
    - `"ilc_di01"` — Income distribution by quantile (EU-SILC deciles D1–D10, shares/EUR)
    - `"nrg_d_hhq"` — Disaggregated final energy consumption in households
  - [x]1.4 Define per-dataset `pa.Schema` objects for the output columns each dataset produces (after column selection and renaming)
  - [x]1.5 Add `EUROSTAT_AVAILABLE_DATASETS` module-level constant
  - [x]1.6 Implement `EurostatLoader(CachedLoader)` with `__init__(self, *, cache, logger, dataset)` — store dataset reference, call `super().__init__()`
  - [x]1.7 Implement `schema(self) -> pa.Schema` — return schema for this loader's dataset
  - [x]1.8 Implement `_fetch(self, config: SourceConfig) -> pa.Table` — download gzip-compressed SDMX-CSV via `urllib.request`, decompress with `gzip.decompress()`, parse with `pyarrow.csv.read_csv()`, select and rename columns, cast types, return `pa.Table`
  - [x]1.9 On any network error, re-raise as `OSError` for stale-cache fallback
  - [x]1.10 Add structured logging: `event=fetch_start`, `event=fetch_complete` with `provider=eurostat dataset_id=... rows=... columns=...`
  - [x]1.11 Implement `get_eurostat_loader(dataset_id, *, cache, logger=None)` factory function with catalog validation
  - [x]1.12 Implement `make_eurostat_config(dataset_id, **params)` helper function

- [x] Task 2: Create ADEME loader — `ademe.py` (AC: #2, #4)
  - [x]2.1 Create `src/reformlab/population/loaders/ademe.py` with module docstring referencing Story 11.3, FR36, FR37
  - [x]2.2 Define `ADEMEDataset` frozen dataclass with fields: `dataset_id: str`, `description: str`, `url: str`, `encoding: str = "windows-1252"`, `separator: str = ";"`, `null_markers: tuple[str, ...] = ("",)`, `columns: tuple[tuple[str, str], ...] = ()` — raw-to-project column rename mapping
  - [x]2.3 Define `ADEME_CATALOG` with at minimum:
    - `"base_carbone"` — Base Carbone V23.6 emission factors (CSV from data.gouv.fr)
  - [x]2.4 Define per-dataset `pa.Schema` for the output columns (subset of the 60+ raw columns, focused on emission factors relevant to carbon tax simulation)
  - [x]2.5 Add `ADEME_AVAILABLE_DATASETS` module-level constant
  - [x]2.6 Implement `ADEMELoader(CachedLoader)` with dataset-specific parsing — handle Windows-1252 encoding (primary), UTF-8 fallback, semicolon separator
  - [x]2.7 Implement `get_ademe_loader(dataset_id, *, cache, logger=None)` factory function
  - [x]2.8 Implement `make_ademe_config(dataset_id, **params)` helper function

- [x] Task 3: Create SDES loader — `sdes.py` (AC: #3, #4)
  - [x]3.1 Create `src/reformlab/population/loaders/sdes.py` with module docstring referencing Story 11.3, FR36, FR37
  - [x]3.2 Define `SDESDataset` frozen dataclass with fields: `dataset_id: str`, `description: str`, `url: str`, `encoding: str = "utf-8"`, `separator: str = ";"`, `null_markers: tuple[str, ...] = ("",)`, `columns: tuple[tuple[str, str], ...] = ()`, `skip_rows: int = 0` — number of header rows to skip before the column name row (DiDo CSVs may have description rows)
  - [x]3.3 Define `SDES_CATALOG` with at minimum:
    - `"vehicle_fleet"` — Vehicle fleet composition by fuel type, age, Crit'Air, region (communal-level data from data.gouv.fr)
  - [x]3.4 Define per-dataset `pa.Schema` for the output columns (fleet counts by year, fuel type, region)
  - [x]3.5 Add `SDES_AVAILABLE_DATASETS` module-level constant
  - [x]3.6 Implement `SDESLoader(CachedLoader)` with DiDo CSV parsing — UTF-8 encoding, semicolon separator; wire `SDESDataset.skip_rows` into `ReadOptions(skip_rows=self._dataset.skip_rows)`
  - [x]3.7 Implement `get_sdes_loader(dataset_id, *, cache, logger=None)` factory function
  - [x]3.8 Implement `make_sdes_config(dataset_id, **params)` helper function

- [x] Task 4: Update `__init__.py` exports (AC: #4)
  - [x]4.1 Rename `AVAILABLE_DATASETS` → `INSEE_AVAILABLE_DATASETS` in `src/reformlab/population/loaders/insee.py` and update all references (factory functions, `__init__.py`, tests). Keep a `AVAILABLE_DATASETS = INSEE_AVAILABLE_DATASETS` alias for backward compatibility until all existing code is updated.
  - [x]4.2 Add all Eurostat exports to `src/reformlab/population/loaders/__init__.py`: `EurostatDataset`, `EurostatLoader`, `EUROSTAT_AVAILABLE_DATASETS`, `get_eurostat_loader`, `make_eurostat_config`
  - [x]4.3 Add all ADEME exports to `src/reformlab/population/loaders/__init__.py`: `ADEMEDataset`, `ADEMELoader`, `ADEME_AVAILABLE_DATASETS`, `get_ademe_loader`, `make_ademe_config`
  - [x]4.4 Add all SDES exports to `src/reformlab/population/loaders/__init__.py`: `SDESDataset`, `SDESLoader`, `SDES_AVAILABLE_DATASETS`, `get_sdes_loader`, `make_sdes_config`
  - [x]4.5 Add the same exports to `src/reformlab/population/__init__.py`

- [x] Task 5: Create test fixtures (AC: #5)
  - [x]5.1 Create `tests/fixtures/eurostat/` directory with small SDMX-CSV fixtures mimicking `ilc_di01` and `nrg_d_hhq` format (5–10 rows each, comma-separated, UTF-8)
  - [x]5.2 Create `tests/fixtures/ademe/` directory with small CSV fixture mimicking Base Carbone format (5–10 rows, semicolon-separated, Windows-1252 encoded)
  - [x]5.3 Create `tests/fixtures/sdes/` directory with small CSV fixture mimicking DiDo vehicle fleet format (5–10 rows, semicolon-separated, UTF-8)
  - [x]5.4 Add fixture helpers in `tests/population/loaders/conftest.py`: paths and byte-reading fixtures for each provider

- [x] Task 6: Write comprehensive tests (AC: all)
  - [x]6.1 `tests/population/loaders/test_eurostat.py`:
    - `TestEurostatLoaderProtocol`: `isinstance()` check against `DataSourceLoader`
    - `TestEurostatLoaderSchema`: `schema()` returns valid `pa.Schema` for each dataset
    - `TestEurostatLoaderFetch`: monkeypatch `urllib.request.urlopen` to return gzip-compressed fixture; verify `_fetch()` returns correctly-parsed `pa.Table`
    - `TestEurostatLoaderFetchMissingValues`: verify `:` and empty cells produce nulls
    - `TestEurostatLoaderFetchBadGzip`: verify `gzip.BadGzipFile` on corrupt gzip content raises `DataSourceValidationError` (not `OSError`) — prevents wrong stale-cache fallback since `BadGzipFile` inherits from `OSError`
    - `TestEurostatLoaderFetchHTTPError`: verify network errors re-raised as `OSError`
    - `TestEurostatLoaderDownloadIntegration`: full `download()` lifecycle via `CachedLoader`
    - `TestEurostatLoaderCatalog`: catalog completeness, factory function, invalid ID error
    - `TestMakeEurostatConfig`: config construction for each catalog entry
  - [x]6.2 `tests/population/loaders/test_ademe.py`:
    - `TestADEMELoaderProtocol`: protocol compliance
    - `TestADEMELoaderSchema`: schema correctness
    - `TestADEMELoaderFetch`: monkeypatch fetch with Windows-1252 fixture; verify parsing
    - `TestADEMELoaderFetchEncodingFallback`: UTF-8 fallback when primary encoding fails
    - `TestADEMELoaderFetchHTTPError`: network error handling
    - `TestADEMELoaderDownloadIntegration`: full download lifecycle
    - `TestADEMELoaderCatalog`: catalog and factory
    - `TestMakeAdemeConfig`: config construction
  - [x]6.3 `tests/population/loaders/test_sdes.py`:
    - `TestSDESLoaderProtocol`: protocol compliance
    - `TestSDESLoaderSchema`: schema correctness
    - `TestSDESLoaderFetch`: monkeypatch fetch with fixture; verify parsing
    - `TestSDESLoaderFetchSkipRows`: fixture with leading description rows; verify `skip_rows > 0` correctly skips to the header row
    - `TestSDESLoaderFetchHTTPError`: network error handling
    - `TestSDESLoaderDownloadIntegration`: full download lifecycle
    - `TestSDESLoaderCatalog`: catalog and factory
    - `TestMakeSDESConfig`: config construction

- [x] Task 7: Network integration tests (AC: #5)
  - [x]7.1 `tests/population/loaders/test_eurostat_network.py` — `@pytest.mark.network` real download of `ilc_di01` (small dataset)
  - [x]7.2 `tests/population/loaders/test_ademe_network.py` — `@pytest.mark.network` real download of Base Carbone CSV
  - [x]7.3 `tests/population/loaders/test_sdes_network.py` — `@pytest.mark.network` real download of vehicle fleet data

- [x] Task 8: Run full test suite and lint (AC: all)
  - [x]8.1 `uv run pytest tests/population/` — all tests pass
  - [x]8.2 `uv run ruff check src/reformlab/population/ tests/population/` — no lint errors
  - [x]8.3 `uv run mypy src/reformlab/population/` — no mypy errors (strict mode)

## Dev Notes

### Architecture Context: Three Loaders Following the INSEE Pattern

This story implements 3 concrete `DataSourceLoader` implementations, all following the pattern established by `INSEELoader` in Story 11.2. The architecture specifies these files explicitly in `src/reformlab/population/loaders/`:

```
src/reformlab/population/loaders/
├── base.py        ← DataSourceLoader protocol + CachedLoader (Story 11.1)
├── cache.py       ← SourceCache (Story 11.1)
├── errors.py      ← Error hierarchy (Story 11.1)
├── insee.py       ← INSEELoader (Story 11.2) — THE TEMPLATE TO FOLLOW
├── eurostat.py    ← NEW: EurostatLoader (this story)
├── ademe.py       ← NEW: ADEMELoader (this story)
└── sdes.py        ← NEW: SDESLoader (this story)
```

**Every loader MUST:**

1. Subclass `CachedLoader` with keyword-only `__init__` accepting `cache: SourceCache`, `logger: logging.Logger`, and a loader-specific dataset dataclass
2. Override `schema() -> pa.Schema` returning per-dataset schema
3. Override `_fetch(config: SourceConfig) -> pa.Table` performing network download + parsing
4. Re-raise **all** network errors as `OSError` (enables `CachedLoader.download()` stale-cache fallback)
5. Use `DataSourceValidationError` for format/parsing errors (not `OSError`)
6. Provide a `get_{provider}_loader(dataset_id, *, cache, logger=None)` factory function
7. Provide a `make_{provider}_config(dataset_id, **params)` config helper
8. Export a frozen `{Provider}Dataset` dataclass and `{PROVIDER}_AVAILABLE_DATASETS` tuple
9. Use structured logging: `event=fetch_start`, `event=fetch_complete` with `provider=`, `dataset_id=`, etc.

### CachedLoader Contract (CRITICAL — read `base.py`)

The `CachedLoader.download()` method (lines 188–274 of `base.py`) orchestrates the full lifecycle. Concrete loaders ONLY implement `_fetch()` and `schema()`. Key contract rules:

- `_fetch()` **MUST** return a `pa.Table` with exact column names and types matching `schema()`. The validation gate at lines 246–270 checks column names (set equality) and types (exact match per field). A `float64` column in the schema requires `float64` in the table — not `int64`, not `string`.
- `_fetch()` **MUST** raise `OSError` on network failure. `CachedLoader.download()` catches `OSError` to trigger stale-cache fallback (line 230). Any other exception type bypasses fallback and propagates directly.
- `_fetch()` **MUST NOT** interact with the cache. Caching is handled by `CachedLoader.download()` after schema validation passes.

### No New Dependencies Required

All three loaders use only existing dependencies and stdlib:

- `urllib.request` / `urllib.error` — HTTP downloads (stdlib)
- `gzip` — gzip decompression for Eurostat (stdlib)
- `io.BytesIO` — in-memory file handling (stdlib)
- `pyarrow` / `pyarrow.csv` — CSV parsing, table construction (existing dependency)
- `http.client` — for `HTTPException` in network error handling (stdlib)

Do **not** introduce `requests`, `httpx`, `pandas`, `openpyxl`, or any new dependency.

### Network Error Handling Pattern (from INSEE)

All three loaders must follow the same network error handling pattern:

```python
_NETWORK_ERRORS: tuple[type[Exception], ...] = (
    urllib.error.URLError,
    OSError,
    http.client.HTTPException,
)

_HTTP_TIMEOUT_SECONDS = 300

def _fetch(self, config: SourceConfig) -> pa.Table:
    try:
        with urllib.request.urlopen(config.url, timeout=_HTTP_TIMEOUT_SECONDS) as response:
            raw_bytes = response.read()
    except _NETWORK_ERRORS as exc:
        raise OSError(
            f"Failed to download {provider}/{dataset_id} from {url}: {exc}"
        ) from exc
    # Parse raw_bytes → pa.Table ...
```

---

## Eurostat Loader — Detailed Specification

### Data Source: Eurostat SDMX 2.1 API

Eurostat provides bulk data via the SDMX 2.1 Dissemination API. No authentication required. Fully public, anonymous HTTPS GET.

**API base URL:**
```
https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/{DATASET_CODE}
```

**Format choice: SDMX-CSV** (not TSV). SDMX-CSV is a standard long-format CSV (one observation per row) that pyarrow.csv can parse directly. TSV has a non-standard header format that requires custom parsing.

**Download URL pattern with gzip compression:**
```
https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/{CODE}?format=SDMX-CSV&compressed=true
```

With `compressed=true`, the API returns a gzip-compressed `.csv.gz` file. This is **file-level compression** (not HTTP Content-Encoding), so `urllib` does NOT decompress it automatically. Use `gzip.decompress(raw_bytes)` to get the CSV content.

### Eurostat Datasets

| Dataset ID | Code | Description | Size (compressed) | Key Variables |
|---|---|---|---|---|
| `ilc_di01` | `ilc_di01` | Income distribution by quantile (EU-SILC) | ~75 KB | Income shares by decile (D1–D10), by country, by year |
| `nrg_d_hhq` | `nrg_d_hhq` | Household energy consumption | ~150 KB | Energy use in GWh by fuel type, end-use, country, year |

### SDMX-CSV Format Specifics

**Encoding:** UTF-8 (pure ASCII for dimension codes and numeric values).
**Separator:** Comma (`,`).
**Line endings:** `\r\n` (CRLF).

**Column structure per dataset:**

`ilc_di01` SDMX-CSV columns:
```
DATAFLOW,LAST UPDATE,freq,quantile,indic_il,currency,geo,TIME_PERIOD,OBS_VALUE,OBS_FLAG
```

Example rows:
```csv
ESTAT:ILC_DI01(1.0),2024-03-15T23:00:00+0100,A,D1,SHARE,EUR,FR,2022,3.3,
ESTAT:ILC_DI01(1.0),2024-03-15T23:00:00+0100,A,D2,SHARE,EUR,FR,2022,4.8,b
```

`nrg_d_hhq` SDMX-CSV columns:
```
DATAFLOW,LAST UPDATE,freq,nrg_bal,siec,unit,geo,TIME_PERIOD,OBS_VALUE,OBS_FLAG
```

**Metadata columns to DROP:** `DATAFLOW`, `LAST UPDATE` (not useful for analysis).

**Missing values:** `OBS_VALUE` may be empty (missing observation). Use `null_values=["", ":"]` in ConvertOptions.

**Observation flags** (`OBS_FLAG`): Single or combined letters indicating data quality:
- `b` = break in time series, `e` = estimated, `p` = provisional, `c` = confidential, `u` = low reliability
- Flags are informational strings — keep as `utf8` type.

### Eurostat Column Mapping and Schemas

**`ilc_di01` column mapping:**
```python
_ILC_DI01_COLUMNS: tuple[tuple[str, str], ...] = (
    ("freq", "frequency"),
    ("quantile", "quantile"),
    ("indic_il", "indicator"),
    ("currency", "currency"),
    ("geo", "country"),
    ("TIME_PERIOD", "time_period"),
    ("OBS_VALUE", "value"),
    ("OBS_FLAG", "obs_flag"),
)
```

**`ilc_di01` output schema:**
```python
pa.schema([
    pa.field("frequency", pa.utf8()),
    pa.field("quantile", pa.utf8()),
    pa.field("indicator", pa.utf8()),
    pa.field("currency", pa.utf8()),
    pa.field("country", pa.utf8()),
    pa.field("time_period", pa.utf8()),
    pa.field("value", pa.float64()),
    pa.field("obs_flag", pa.utf8()),
])
```

**`nrg_d_hhq` column mapping:**
```python
_NRG_D_HHQ_COLUMNS: tuple[tuple[str, str], ...] = (
    ("freq", "frequency"),
    ("nrg_bal", "energy_balance"),
    ("siec", "energy_product"),
    ("unit", "unit"),
    ("geo", "country"),
    ("TIME_PERIOD", "time_period"),
    ("OBS_VALUE", "value"),
    ("OBS_FLAG", "obs_flag"),
)
```

**`nrg_d_hhq` output schema:**
```python
pa.schema([
    pa.field("frequency", pa.utf8()),
    pa.field("energy_balance", pa.utf8()),
    pa.field("energy_product", pa.utf8()),
    pa.field("unit", pa.utf8()),
    pa.field("country", pa.utf8()),
    pa.field("time_period", pa.utf8()),
    pa.field("value", pa.float64()),
    pa.field("obs_flag", pa.utf8()),
])
```

### Eurostat Parsing Strategy

```python
import gzip

def _fetch(self, config: SourceConfig) -> pa.Table:
    # 1. Download gzip-compressed SDMX-CSV
    raw_bytes = ...  # urllib.request.urlopen(config.url)

    # 2. Decompress gzip (file-level, NOT http-level)
    #    CRITICAL: gzip.BadGzipFile inherits from OSError. If not caught
    #    explicitly here, it propagates as OSError and CachedLoader.download()
    #    triggers stale-cache fallback instead of raising a validation error.
    try:
        csv_bytes = gzip.decompress(raw_bytes)
    except (OSError, gzip.BadGzipFile) as exc:
        raise DataSourceValidationError(
            summary="Gzip decompression failed",
            reason=f"Downloaded content for eurostat/{self._dataset.dataset_id} "
                   f"is not valid gzip: {exc}",
            fix="Check the Eurostat API URL and compressed=true parameter",
        ) from exc

    # 3. Parse with pyarrow.csv
    ds = self._dataset
    raw_names = [col[0] for col in ds.columns]
    project_names = [col[1] for col in ds.columns]
    schema = self.schema()

    column_types: dict[str, pa.DataType] = {}
    for raw_name, proj_name in ds.columns:
        column_types[raw_name] = schema.field(proj_name).type

    convert_options = pcsv.ConvertOptions(
        null_values=list(ds.null_markers),
        column_types=column_types,
        include_columns=raw_names,
    )
    parse_options = pcsv.ParseOptions(delimiter=ds.separator)
    read_options = pcsv.ReadOptions(encoding=ds.encoding)

    table = pcsv.read_csv(
        io.BytesIO(csv_bytes),
        read_options=read_options,
        parse_options=parse_options,
        convert_options=convert_options,
    )

    # 4. Rename columns
    table = table.rename_columns(project_names)
    return table
```

### Eurostat Fixture Design

Create `tests/fixtures/eurostat/ilc_di01.csv` (NOT gzip-compressed, plain CSV for readability — the test wraps it in gzip at runtime):

```csv
DATAFLOW,LAST UPDATE,freq,quantile,indic_il,currency,geo,TIME_PERIOD,OBS_VALUE,OBS_FLAG
ESTAT:ILC_DI01(1.0),2024-03-15T23:00:00+0100,A,D1,SHARE,EUR,FR,2022,3.3,
ESTAT:ILC_DI01(1.0),2024-03-15T23:00:00+0100,A,D2,SHARE,EUR,FR,2022,4.8,b
ESTAT:ILC_DI01(1.0),2024-03-15T23:00:00+0100,A,D3,SHARE,EUR,FR,2022,5.9,
ESTAT:ILC_DI01(1.0),2024-03-15T23:00:00+0100,A,D4,SHARE,EUR,FR,2022,6.8,
ESTAT:ILC_DI01(1.0),2024-03-15T23:00:00+0100,A,D5,SHARE,EUR,DE,2022,,c
```

Note: last row has empty OBS_VALUE (missing) and flag "c" (confidential). Tests should verify this produces `null` in the `value` column.

---

## ADEME Loader — Detailed Specification

### Data Source: Base Carbone via data.gouv.fr

ADEME provides the Base Carbone emission factors as a CSV download on data.gouv.fr. No authentication required. The data.gouv.fr URL serves the file directly.

**Download URL (stable data.gouv.fr resource):**
```
https://www.data.gouv.fr/api/1/datasets/r/ac6a3044-459c-4520-b85a-7e1740f7cd1f
```

**Current version:** V23.6 (updated February 2026), ~10.3 MB, ~18,600 emission factor records.

### ADEME CSV Format Specifics

**CRITICAL: Encoding is Windows-1252 (cp1252), NOT UTF-8.** This is the most important difference from INSEE and Eurostat. French characters like `é`, `è`, `ê`, `ô` are encoded as single bytes in Windows-1252 that are invalid UTF-8.

**Separator:** Semicolon (`;`).
**Line endings:** `\r\n` (CRLF).
**Quote character:** `"` (standard CSV quoting).

**Encoding handling strategy:**

`pyarrow.csv.ReadOptions(encoding=...)` supports Python codec names. Use `"windows-1252"` as the primary encoding, with `"utf-8"` as fallback (in case ADEME switches to UTF-8 in future versions). Follow the same try/catch `pa.ArrowInvalid` pattern as INSEE's encoding fallback:

```python
read_options = pcsv.ReadOptions(encoding="windows-1252")
try:
    table = pcsv.read_csv(io.BytesIO(raw_bytes), ...)
except pa.ArrowInvalid:
    # Fallback to UTF-8 (future-proofing)
    read_options = pcsv.ReadOptions(encoding="utf-8")
    table = pcsv.read_csv(io.BytesIO(raw_bytes), ...)
```

### ADEME Column Mapping and Schema

The Base Carbone CSV has 60+ columns. Select only those relevant to carbon tax microsimulation. The raw column names are French with spaces and accents:

**`base_carbone` column mapping (key subset):**
```python
_BASE_CARBONE_COLUMNS: tuple[tuple[str, str], ...] = (
    ("Identifiant de l'élément", "element_id"),
    ("Nom base français", "name_fr"),
    ("Nom attribut français", "attribute_name_fr"),
    ("Type Ligne", "line_type"),
    ("Unité français", "unit_fr"),
    ("Total poste non décomposé", "total_co2e"),
    ("CO2f", "co2_fossil"),
    ("CH4f", "ch4_fossil"),
    ("CH4b", "ch4_biogenic"),
    ("N2O", "n2o"),
    ("CO2b", "co2_biogenic"),
    ("Autre GES", "other_ghg"),
    ("Localisation géographique", "geography"),
    ("Sous-localisation géographique français", "sub_geography"),
    ("Contributeur", "contributor"),
)
```

**Note on column names:** See "Column Name Verification Strategy" section below for the approach to handling column name drift across data vintages.

**`base_carbone` output schema:**
```python
pa.schema([
    pa.field("element_id", pa.int64()),
    pa.field("name_fr", pa.utf8()),
    pa.field("attribute_name_fr", pa.utf8()),
    pa.field("line_type", pa.utf8()),
    pa.field("unit_fr", pa.utf8()),
    pa.field("total_co2e", pa.float64()),
    pa.field("co2_fossil", pa.float64()),
    pa.field("ch4_fossil", pa.float64()),
    pa.field("ch4_biogenic", pa.float64()),
    pa.field("n2o", pa.float64()),
    pa.field("co2_biogenic", pa.float64()),
    pa.field("other_ghg", pa.float64()),
    pa.field("geography", pa.utf8()),
    pa.field("sub_geography", pa.utf8()),
    pa.field("contributor", pa.utf8()),
])
```

**IMPORTANT:** See "Column Name Verification Strategy" section for handling column name drift. Run the network integration test early to verify ADEME headers match the mapping above.

### ADEME Fixture Design

Create `tests/fixtures/ademe/base_carbone.csv` — a small file (5–10 rows) encoded in **Windows-1252** with semicolon separator, mimicking the real Base Carbone format. Include:
- At least one row with French characters (`é`, `è`, `ê`) to test encoding
- At least one row with empty/null emission values
- Realistic column names from the real dataset

```
Identifiant de l'élément;Nom base français;Nom attribut français;Type Ligne;Unité français;Total poste non décomposé;CO2f;CH4f;CH4b;N2O;CO2b;Autre GES;Localisation géographique;Sous-localisation géographique français;Contributeur
1234;Gaz naturel;PCI;Elément;kgCO2e/kWh PCI;0.227;0.205;0.004;0;0.018;0;0;France métropolitaine;;ADEME
5678;Fioul domestique;PCI;Elément;kgCO2e/litre;3.25;3.15;0.001;0;0.089;0;0;France métropolitaine;;ADEME
9012;Électricité;Mix moyen;Elément;kgCO2e/kWh;0.0569;0.0479;0;0;0.009;0;0;France métropolitaine;;ADEME
```

**The fixture MUST be saved as Windows-1252 encoding**, not UTF-8. The `Write` tool outputs UTF-8, so the fixture must be generated programmatically. Add a fixture helper to `tests/population/loaders/conftest.py`:

```python
@pytest.fixture()
def ademe_base_carbone_csv_bytes() -> bytes:
    """Windows-1252 encoded ADEME Base Carbone CSV fixture."""
    content = (
        "Identifiant de l'élément;Nom base français;Nom attribut français;"
        "Type Ligne;Unité français;Total poste non décomposé;CO2f;CH4f;"
        "CH4b;N2O;CO2b;Autre GES;Localisation géographique;"
        "Sous-localisation géographique français;Contributeur\r\n"
        "1234;Gaz naturel;PCI;Elément;kgCO2e/kWh PCI;0.227;0.205;0.004;"
        "0;0.018;0;0;France métropolitaine;;ADEME\r\n"
        # ... more rows with French characters (é, è, ê) ...
    )
    return content.encode("windows-1252")
```

Tests that monkeypatch `_fetch` should use these bytes directly. The on-disk fixture file at `tests/fixtures/ademe/base_carbone.csv` should be created by a one-time setup script writing `content.encode("windows-1252")` to disk, NOT by the `Write` tool. Include at least one non-ASCII French character (e.g., `é` in `métropolitaine`, `è` in `Elément`) to verify encoding — these differ between UTF-8 (multi-byte) and Windows-1252 (single-byte).

---

## SDES Loader — Detailed Specification

### Data Source: Vehicle Fleet via data.gouv.fr

SDES provides communal-level vehicle fleet data as CSV on data.gouv.fr. The national/regional aggregates are XLSX-only (requires openpyxl, which we don't have), so use the communal-level CSV instead.

**Download URL (data.gouv.fr resource for communal vehicle fleet):**
```
https://www.data.gouv.fr/api/1/datasets/r/2f9fd9c8-e6e1-450e-8548-f479b8a401cd
```

**Alternative: DiDo API endpoint:**
```
https://data.statistiques.developpement-durable.gouv.fr/dido/api/v1/datafiles/3750a580-f249-42d3-b488-5cf8acb767b7/csv?millesime=2023-05&withColumnName=true&withColumnDescription=false&withColumnUnit=false
```

**Decision:** Use the data.gouv.fr URL in `SDES_CATALOG["vehicle_fleet"].url` for simplicity (single GET, no query params needed). The DiDo API URL above is informational only — do not use it in the catalog.

**Note:** The data.gouv.fr resource ID (`2f9fd9c8-...`) may change when new data vintages are published. The URL is stored in the catalog constant and can be updated easily.

### SDES CSV Format Specifics

**Encoding:** UTF-8.
**Separator:** Semicolon (`;`).
**Line endings:** Standard (`\n` or `\r\n`).
**Missing values:** Empty fields (no special markers observed).
**File size:** Large (~10 MB). This is fine for download/cache but test fixtures must be small.

**The DiDo CSV may have multiple header rows** (descriptions, units, column names). The data.gouv.fr version typically has a single header row. If using DiDo API directly, use query parameters `withColumnDescription=false&withColumnUnit=false` to get clean single-header output.

### SDES Column Mapping and Schema

The CSV columns include geographic codes, vehicle classification, and fleet counts by year:

**`vehicle_fleet` column mapping (key subset):**
```python
_VEHICLE_FLEET_COLUMNS: tuple[tuple[str, str], ...] = (
    ("REGION_CODE", "region_code"),
    ("REGION_LIBELLE", "region_name"),
    ("CLASSE_VEHICULE", "vehicle_class"),
    ("CATEGORIE_VEHICULE", "vehicle_category"),
    ("CARBURANT", "fuel_type"),
    ("AGE", "vehicle_age"),
    ("CRITAIR", "critair_sticker"),
    ("PARC_2022", "fleet_count_2022"),
)
```

**Note on column selection:** The raw CSV has fleet count columns for many years (`PARC_2011` through `PARC_2022` or later). For the initial loader, select only the most recent year column to keep the schema manageable. The mapping can be expanded later.

**Alternative approach:** Select multiple year columns:
```python
("PARC_2018", "fleet_2018"),
("PARC_2019", "fleet_2019"),
("PARC_2020", "fleet_2020"),
("PARC_2021", "fleet_2021"),
("PARC_2022", "fleet_2022"),
```

**`vehicle_fleet` output schema:**
```python
pa.schema([
    pa.field("region_code", pa.utf8()),
    pa.field("region_name", pa.utf8()),
    pa.field("vehicle_class", pa.utf8()),
    pa.field("vehicle_category", pa.utf8()),
    pa.field("fuel_type", pa.utf8()),
    pa.field("vehicle_age", pa.utf8()),
    pa.field("critair_sticker", pa.utf8()),
    pa.field("fleet_count_2022", pa.float64()),  # float64 for null handling
])
```

**Note:** Fleet counts use `float64` (not `int64`) to handle potential null values, following the same pattern as INSEE's `nb_fiscal_households`.

**IMPORTANT:** See "Column Name Verification Strategy" section for handling column name drift. Run the network integration test early to verify SDES headers match the mapping above.

### SDES Fixture Design

Create `tests/fixtures/sdes/vehicle_fleet.csv` — a small CSV (5–10 rows) mimicking the DiDo format:

```csv
REGION_CODE;REGION_LIBELLE;CLASSE_VEHICULE;CATEGORIE_VEHICULE;CARBURANT;AGE;CRITAIR;PARC_2022
84;Auvergne-Rhône-Alpes;VP;M1;Diesel;De 1 à 5 ans;Crit'Air 2;450000
84;Auvergne-Rhône-Alpes;VP;M1;Essence;De 1 à 5 ans;Crit'Air 1;380000
84;Auvergne-Rhône-Alpes;VP;M1;Electrique;De 1 à 5 ans;Crit'Air E;95000
11;Île-de-France;VP;M1;Diesel;De 1 à 5 ans;Crit'Air 2;520000
11;Île-de-France;VP;M1;Essence;Plus de 15 ans;;
```

Include at least one row with empty fleet count to test null handling.

---

### Test Pattern to Follow (from INSEE tests)

Follow the exact test structure from `tests/population/loaders/test_insee.py`:

1. **Test helpers** at top of file: `_make_gzip()` (for Eurostat), `_mock_urlopen()` (reuse from INSEE pattern):
   ```python
   def _make_gzip(csv_bytes: bytes) -> bytes:
       """Create gzip-compressed bytes from CSV content."""
       return gzip.compress(csv_bytes)
   ```
2. **Protocol compliance class**: verify `isinstance(loader, DataSourceLoader)`
3. **Schema class**: verify field names and types for each dataset
4. **Fetch class**: monkeypatch `urllib.request.urlopen` to return fixture data; for Eurostat, wrap fixture in gzip first
5. **Error handling class**: verify network errors become `OSError`
6. **Download integration class**: full `CachedLoader.download()` cycle — cache miss → fetch → cache → cache hit
7. **Catalog class**: verify `AVAILABLE_DATASETS`, factory function, invalid ID error
8. **Config class**: verify `make_{provider}_config` produces correct `SourceConfig`

### Network Integration Tests

Create `test_{provider}_network.py` files with `@pytest.mark.network` marker. These are excluded from CI by default (`addopts = "-m 'not integration and not scale and not network'"` in pyproject.toml).

For Eurostat network tests, download the smallest dataset (`ilc_di01` at ~75 KB compressed) to verify schema and basic row count. For ADEME and SDES, download and verify similarly.

### Project Structure Notes

**New files:**
- `src/reformlab/population/loaders/eurostat.py`
- `src/reformlab/population/loaders/ademe.py`
- `src/reformlab/population/loaders/sdes.py`
- `tests/population/loaders/test_eurostat.py`
- `tests/population/loaders/test_ademe.py`
- `tests/population/loaders/test_sdes.py`
- `tests/population/loaders/test_eurostat_network.py`
- `tests/population/loaders/test_ademe_network.py`
- `tests/population/loaders/test_sdes_network.py`
- `tests/fixtures/eurostat/ilc_di01.csv`
- `tests/fixtures/eurostat/nrg_d_hhq.csv`
- `tests/fixtures/ademe/base_carbone.csv`
- `tests/fixtures/sdes/vehicle_fleet.csv`

**Modified files:**
- `src/reformlab/population/loaders/__init__.py` — add all new exports
- `src/reformlab/population/__init__.py` — add all new exports
- `tests/population/loaders/conftest.py` — add fixture helpers for Eurostat, ADEME, SDES

**No changes** to `pyproject.toml` (no new dependencies, `network` marker already exists from Story 11.1)

### Alignment with Architecture

The architecture (`architecture.md`) specifies:

```
src/reformlab/population/
├── loaders/
│   ├── base.py        ← DataSourceLoader protocol (Story 11.1)
│   ├── insee.py       ← INSEE data loader (Story 11.2)
│   ├── eurostat.py    ← Eurostat data loader (this story)
│   ├── ademe.py       ← ADEME energy data loader (this story)
│   └── sdes.py        ← SDES vehicle fleet data loader (this story)
```

All loaders satisfy `DataSourceLoader` protocol via `CachedLoader` base class, matching the "External Data Caching & Offline Strategy" architecture section. Cache paths follow `~/.reformlab/cache/sources/{provider}/{dataset_id}/{hash}.parquet`.

### Error Handling Notes

- `_fetch()` should only raise `OSError` for network errors — `CachedLoader.download()` handles everything else
- Invalid dataset IDs → `DataSourceValidationError` (from factory function, not from `_fetch`)
- Schema mismatches are caught by `CachedLoader.download()` automatically after `_fetch()` returns
- For Eurostat gzip decompression errors → raise `DataSourceValidationError` (not `OSError`, since the download succeeded but the content is invalid)

### Column Name Verification Strategy

For all three data sources, the exact raw column names may vary across data vintages. The recommended approach:

1. **Start with the column names documented in this story** (based on 2026-03 research)
2. **Run the network integration test** early in development to verify column names against live data
3. **If column names differ**, update the catalog constants and fixtures accordingly
4. **Document any discrepancies** in the dev agent record

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#New-Subsystem-Population-Generation] — Directory structure, loader file specifications
- [Source: _bmad-output/planning-artifacts/architecture.md#External-Data-Caching-&-Offline-Strategy] — Cache protocol, offline semantics, DataSourceLoader protocol
- [Source: _bmad-output/planning-artifacts/epics.md#BKL-1103] — Story definition and acceptance criteria
- [Source: _bmad-output/planning-artifacts/prd.md#FR36] — "Analyst can download and cache public datasets from institutional sources"
- [Source: _bmad-output/planning-artifacts/prd.md#FR37] — "Analyst can browse available datasets and select which to include in a population"
- [Source: _bmad-output/project-context.md#Python-Language-Rules] — Frozen dataclasses, Protocols, `from __future__ import annotations`
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules] — PyArrow canonical data type, no pandas in core logic
- [Source: src/reformlab/population/loaders/base.py] — DataSourceLoader Protocol, CachedLoader base class, SourceConfig, CacheStatus
- [Source: src/reformlab/population/loaders/cache.py] — SourceCache caching infrastructure
- [Source: src/reformlab/population/loaders/errors.py] — DataSourceError hierarchy
- [Source: src/reformlab/population/loaders/insee.py] — INSEELoader concrete implementation (THE PATTERN TO FOLLOW)
- [Source: tests/population/loaders/test_insee.py] — INSEE test patterns to replicate
- [Source: tests/population/loaders/conftest.py] — Test fixture patterns, MockCachedLoader
- [Source: _bmad-output/implementation-artifacts/11-1-define-datasourceloader-protocol-and-caching-infrastructure.md] — Story 11.1 (protocol + caching)
- [Source: _bmad-output/implementation-artifacts/11-2-implement-insee-data-source-loader.md] — Story 11.2 (INSEE loader, predecessor)
- [Source: Eurostat SDMX 2.1 API] — https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-getting-started/sdmx2.1
- [Source: Eurostat ilc_di01] — https://ec.europa.eu/eurostat/databrowser/product/page/ilc_di01
- [Source: Eurostat nrg_d_hhq] — https://ec.europa.eu/eurostat/databrowser/product/page/NRG_D_HHQ
- [Source: Base Carbone on data.gouv.fr] — https://www.data.gouv.fr/datasets/base-carbone-r-2
- [Source: SDES Vehicle Fleet on data.gouv.fr] — https://www.data.gouv.fr/datasets/parc-de-vehicules-routiers

## Dev Agent Record

### Agent Model Used

claude-opus-4-6

### Debug Log References

None — clean implementation with one test fix (ADEME encoding fallback needed `ArrowKeyError` in addition to `ArrowInvalid`).

### Completion Notes List

- All 3 loaders (Eurostat, ADEME, SDES) implemented following the INSEE pattern exactly
- `AVAILABLE_DATASETS` renamed to `INSEE_AVAILABLE_DATASETS` with backward-compatible alias
- ADEME encoding fallback catches both `pa.ArrowInvalid` and `pa.lib.ArrowKeyError` (UTF-8 bytes decoded as Windows-1252 garble column names, producing `ArrowKeyError` not `ArrowInvalid`)
- Eurostat gzip decompression errors correctly raise `DataSourceValidationError` (not `OSError`) to prevent wrong stale-cache fallback
- ADEME fixture written as Windows-1252 via Python script (Write tool outputs UTF-8)
- 87 new tests + 1723 total pass, 0 regressions
- ruff, mypy strict: all clean

### File List

**New files:**
- `src/reformlab/population/loaders/eurostat.py`
- `src/reformlab/population/loaders/ademe.py`
- `src/reformlab/population/loaders/sdes.py`
- `tests/population/loaders/test_eurostat.py`
- `tests/population/loaders/test_ademe.py`
- `tests/population/loaders/test_sdes.py`
- `tests/population/loaders/test_eurostat_network.py`
- `tests/population/loaders/test_ademe_network.py`
- `tests/population/loaders/test_sdes_network.py`
- `tests/fixtures/eurostat/ilc_di01.csv`
- `tests/fixtures/eurostat/nrg_d_hhq.csv`
- `tests/fixtures/ademe/base_carbone.csv`
- `tests/fixtures/sdes/vehicle_fleet.csv`

**Modified files:**
- `src/reformlab/population/loaders/insee.py` — renamed `AVAILABLE_DATASETS` → `INSEE_AVAILABLE_DATASETS` + alias
- `src/reformlab/population/loaders/__init__.py` — added all new exports
- `src/reformlab/population/__init__.py` — added all new exports
- `tests/population/loaders/conftest.py` — added Eurostat, ADEME, SDES fixture helpers

## Change Log

- 2026-03-03: Story created by create-story workflow — comprehensive developer context with Eurostat SDMX-CSV parsing, ADEME Windows-1252 handling, SDES DiDo CSV format, test fixture designs, and verified download URLs.
- 2026-03-03: Story implemented — all 3 loaders, 87 new tests, full CI validation (ruff + mypy strict + 1723 tests pass).


]]></file>
<file id="6870c5a9" path="_bmad-output/implementation-artifacts/11-4-define-mergemethod-protocol-and-uniform-distribution-method.md" label="STORY FILE"><![CDATA[


# Story 11.4: Define MergeMethod protocol and implement uniform distribution method

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform developer building the French household population pipeline,
I want a `MergeMethod` protocol defining the interface for statistical dataset fusion and a concrete `UniformMergeMethod` implementation that randomly matches rows between two tables,
so that downstream stories (11.5 IPF/conditional sampling, 11.6 pipeline builder) have a proven protocol pattern to follow, and the simplest merge method is available as a baseline for population construction.

## Acceptance Criteria

1. Given the `MergeMethod` protocol, when a new method is implemented, then it must accept two `pa.Table` inputs plus a config, and return a merged table plus an assumption record.
2. Given two tables with no shared sample, when merged using uniform distribution, then each row from Table A is matched with a randomly drawn row from Table B with equal probability.
3. Given a uniform merge, when the assumption record is inspected, then it states: "Each household in source A is matched to a household in source B with uniform probability — this assumes no correlation between the variables in the two sources."
4. Given the uniform method docstring, when read, then it includes a plain-language explanation of the independence assumption and when this is appropriate vs. problematic.

## Tasks / Subtasks

- [ ] Task 1: Create `src/reformlab/population/methods/` directory structure (AC: #1)
  - [ ] 1.1 Create `src/reformlab/population/methods/__init__.py` with module docstring referencing Story 11.4, FR38, FR39
  - [ ] 1.2 Create `src/reformlab/population/methods/errors.py` with `MergeError` base exception and `MergeValidationError` — follow the `summary - reason - fix` pattern from `DataSourceError` in `population/loaders/errors.py`

- [ ] Task 2: Define `MergeMethod` protocol and supporting types — `base.py` (AC: #1, #3)
  - [ ] 2.1 Create `src/reformlab/population/methods/base.py` with module docstring referencing Story 11.4, FR38
  - [ ] 2.2 Define `MergeConfig` frozen dataclass with fields: `seed: int`, `description: str = ""`, `drop_right_columns: tuple[str, ...] = ()` — validate in `__post_init__` that `seed` is a non-negative integer
  - [ ] 2.3 Define `MergeAssumption` frozen dataclass with fields: `method_name: str`, `statement: str`, `details: dict[str, Any]` — include `to_governance_entry(*, source_label: str = "merge_step") -> dict[str, Any]` method that produces a dict compatible with `governance.manifest.AssumptionEntry` (keys: `key`, `value`, `source`, `is_default`)
  - [ ] 2.4 Define `MergeResult` frozen dataclass with fields: `table: pa.Table`, `assumption: MergeAssumption`
  - [ ] 2.5 Define `MergeMethod` as `@runtime_checkable` Protocol with two required members:
    - `def merge(self, table_a: pa.Table, table_b: pa.Table, config: MergeConfig) -> MergeResult`
    - `name: str` property (read-only)
  - [ ] 2.6 Validate design: `MergeConfig.__post_init__` deep-copies `drop_right_columns` to prevent aliasing (use `object.__setattr__` pattern from `SourceConfig`)
  - [ ] 2.7 Validate design: `MergeAssumption.details` deep-copied in `__post_init__` to prevent mutation

- [ ] Task 3: Implement `UniformMergeMethod` — `uniform.py` (AC: #2, #3, #4)
  - [ ] 3.1 Create `src/reformlab/population/methods/uniform.py` with module docstring referencing Story 11.4, FR38, FR39 — include the pedagogical docstring explaining the independence assumption in plain language (when appropriate: independent surveys; when problematic: correlated variables)
  - [ ] 3.2 Implement `UniformMergeMethod` class with `__init__(self)` (no constructor parameters — uniform has no method-specific config)
  - [ ] 3.3 Implement `name` property returning `"uniform"`
  - [ ] 3.4 Implement `merge(self, table_a, table_b, config)` with this logic:
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
  - [ ] 3.5 Use `logging.getLogger(__name__)` with structured `event=merge_start`, `event=merge_complete` log entries including `method=uniform rows_a=... rows_b=... seed=...`

- [ ] Task 4: Update `__init__.py` exports (AC: #1)
  - [ ] 4.1 Export from `src/reformlab/population/methods/__init__.py`: `MergeMethod`, `MergeConfig`, `MergeAssumption`, `MergeResult`, `UniformMergeMethod`, `MergeError`, `MergeValidationError`
  - [ ] 4.2 Add methods exports to `src/reformlab/population/__init__.py`: same names as 4.1

- [ ] Task 5: Create test infrastructure (AC: all)
  - [ ] 5.1 Create `tests/population/methods/__init__.py`
  - [ ] 5.2 Create `tests/population/methods/conftest.py` with fixtures:
    - `income_table` — small `pa.Table` with columns: `household_id` (int64), `income` (float64), `region_code` (utf8) — 5 rows
    - `vehicle_table` — small `pa.Table` with columns: `vehicle_type` (utf8), `vehicle_age` (int64), `fuel_type` (utf8) — 8 rows
    - `overlapping_table` — small `pa.Table` with a column name that conflicts with `income_table` (e.g., `region_code`)
    - `empty_table` — `pa.Table` with schema but 0 rows
    - `default_config` — `MergeConfig(seed=42)`

- [ ] Task 6: Write comprehensive tests (AC: all)
  - [ ] 6.1 `tests/population/methods/test_base.py`:
    - `TestMergeConfig`: frozen, `__post_init__` validation (negative seed raises `ValueError`), `drop_right_columns` deep-copied, default values
    - `TestMergeAssumption`: frozen, `details` deep-copied, `to_governance_entry()` returns correct dict with `key`/`value`/`source`/`is_default` fields
    - `TestMergeResult`: frozen, holds table + assumption
    - `TestMergeMethodProtocol`: verify `UniformMergeMethod` passes `isinstance(m, MergeMethod)` check; verify a non-conforming class fails
  - [ ] 6.2 `tests/population/methods/test_uniform.py`:
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
  - [ ] 6.3 `tests/population/methods/test_errors.py`:
    - `TestMergeError`: inherits `Exception`, `summary-reason-fix` message format, attributes accessible
    - `TestMergeValidationError`: inherits `MergeError`

- [ ] Task 7: Run full test suite and lint (AC: all)
  - [ ] 7.1 `uv run pytest tests/population/methods/` — all new tests pass
  - [ ] 7.2 `uv run pytest tests/population/` — no regressions in loader tests
  - [ ] 7.3 `uv run ruff check src/reformlab/population/methods/ tests/population/methods/` — no lint errors
  - [ ] 7.4 `uv run mypy src/reformlab/population/methods/` — no mypy errors (strict mode)

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
        if not isinstance(self.seed, int) or self.seed < 0:
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
        from copy import deepcopy
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
                "method": self.method_name,
                "statement": self.statement,
                **self.details,
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
3. Concatenate columns from table_a and the selected table_b rows

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
- **Story 11.6** (PopulationPipeline) — composes loaders + methods, calls `merge()` in sequence, collects `MergeAssumption` records, passes them to `governance.capture.capture_assumptions()`
- **Story 11.7** (Validation) — validates merged population against marginals
- **Story 11.8** (Notebook) — demonstrates merge methods with plain-language explanations

### Project Structure Notes

**New files (6):**
- `src/reformlab/population/methods/__init__.py`
- `src/reformlab/population/methods/base.py`
- `src/reformlab/population/methods/errors.py`
- `src/reformlab/population/methods/uniform.py`
- `tests/population/methods/__init__.py`
- `tests/population/methods/conftest.py`
- `tests/population/methods/test_base.py`
- `tests/population/methods/test_uniform.py`
- `tests/population/methods/test_errors.py`

**Modified files (2):**
- `src/reformlab/population/__init__.py` — add methods exports
- (no other files modified)

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

## Change Log

- 2026-03-03: Story created by create-story workflow — comprehensive developer context with MergeMethod protocol design, UniformMergeMethod algorithm, governance integration pattern, error hierarchy, test fixture designs, and downstream dependency mapping.


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
<var name="epics_file" description="Enhanced epics+stories file for story verification" load_strategy="SELECTIVE_LOAD" token_approx="22505">_bmad-output/planning-artifacts/epics.md</var>
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
<var name="story_file" file_id="6870c5a9">embedded in prompt, file id: 6870c5a9</var>
<var name="story_id">11.4</var>
<var name="story_key">11-4-define-mergemethod-protocol-and-uniform-distribution-method</var>
<var name="story_num">4</var>
<var name="story_title">define-mergemethod-protocol-and-uniform-distribution-method</var>
<var name="template">embedded context</var>
<var name="timestamp">20260303_151506</var>
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

      <action>Store for report output:
        - {{evidence_findings}}: List of findings with severity_icon, severity, description, source, score
        - {{clean_pass_count}}: Number of clean categories
        - {{evidence_score}}: Calculated total score
        - {{evidence_verdict}}: EXCELLENT/PASS/MAJOR REWORK/REJECT
      </action>
    </substep>
  </step>

  <step n="5" goal="Generate validation report">
    <critical>OUTPUT MARKERS REQUIRED: Your validation report MUST start with the marker &lt;!-- VALIDATION_REPORT_START --&gt; on its own line BEFORE the report header, and MUST end with the marker &lt;!-- VALIDATION_REPORT_END --&gt; on its own line AFTER the final line. The orchestrator extracts ONLY content between these markers. Any text outside the markers (thinking, commentary) will be discarded.</critical>

    <action>Use the output template as a FORMAT GUIDE, replacing all {{placeholders}} with your actual analysis</action>
    <action>Output the complete report to stdout with all sections filled in</action>
    <action>Do NOT save to any file - the orchestrator handles persistence</action>
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