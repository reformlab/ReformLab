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
