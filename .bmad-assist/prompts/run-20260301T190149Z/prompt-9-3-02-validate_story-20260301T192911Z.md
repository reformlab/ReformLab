<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 9 -->
<!-- Story: 3 -->
<!-- Phase: validate-story -->
<!-- Timestamp: 20260301T192911Z -->
<compiled-workflow>
<mission><![CDATA[

Adversarial Story Validation

Target: Story 9.3 - add-variable-periodicity-handling

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
<file id="08fae9ea" path="_bmad-output/implementation-artifacts/9-2-handle-multi-entity-output-arrays.md" label="STORY FILE"><![CDATA[

# Story 9.2: Handle Multi-Entity Output Arrays

Status: done

## Story

As a **platform developer integrating OpenFisca-France**,
I want the adapter to correctly handle output variables that belong to different entity types (individu, menage, famille, foyer_fiscal),
so that multi-entity computations return correctly shaped results mapped to their respective entity tables instead of crashing on array length mismatches.

## Context & Motivation

OpenFisca simulations operate on a multi-entity model. In OpenFisca-France, there are 4 entities:

| Entity Key (singular) | Entity Plural | Description | Example Variable |
|---|---|---|---|
| `individu` | `individus` | Person (singular entity) | `salaire_net` |
| `famille` | `familles` | Family (group entity) | `rsa` |
| `foyer_fiscal` | `foyers_fiscaux` | Tax household (group entity) | `impot_revenu_restant_a_payer` |
| `menage` | `menages` | Dwelling (group entity) | `revenu_disponible` |

When `simulation.calculate(var_name, period)` is called, the returned numpy array length equals the number of instances of that variable's entity — **not** the number of persons. For a married couple (2 persons, 1 foyer_fiscal, 1 menage):
- `salaire_net` returns 2 values (one per person)
- `impot_revenu_restant_a_payer` returns 1 value (one per foyer_fiscal)
- `revenu_disponible` returns 1 value (one per menage)

The current `_extract_results()` method (line 341-350 of `openfisca_api_adapter.py`) naively combines all output arrays into a single `pa.Table`, which crashes with a PyArrow error when arrays have different lengths.

**Source:** Spike 8-1 findings, Gap 2. [Source: `_bmad-output/implementation-artifacts/spike-findings-8-1-openfisca-integration.md`]

## Acceptance Criteria

1. **AC-1: Entity-aware result extraction** — Given output variables that return per-entity arrays (e.g., per-menage, per-foyer_fiscal), when the adapter processes results, then arrays are correctly mapped to their respective entity tables.

2. **AC-2: Correct array length per entity** — Given a variable defined on `foyer_fiscal` entity, when results are returned, then the output array length matches the number of foyers fiscaux, not the number of individuals.

3. **AC-3: Mixed-entity output mapping** — Given mixed-entity output variables, when processed, then each variable's values are stored in the correct entity-level result table with proper entity IDs.

4. **AC-4: Backward compatibility** — Given output variables that all belong to the same entity (e.g., all `individu`-level), when processed, then the adapter returns results in a format compatible with existing consumers (`ComputationResult.output_fields` as `pa.Table`).

5. **AC-5: Clear error on entity detection failure** — Given a variable whose entity cannot be determined from the TBS, when `_extract_results()` runs, then a clear `ApiMappingError` is raised with the variable name and available entity information.

## Tasks / Subtasks

- [x] Task 1: Determine variable-to-entity mapping from TBS (AC: #1, #2, #5)
  - [x] 1.1 Add `_resolve_variable_entities()` method that queries `tbs.variables[var_name].entity` to determine which entity each output variable belongs to
  - [x] 1.2 Group output variables by entity (e.g., `{"individu": ["salaire_net"], "foyer_fiscal": ["impot_revenu_restant_a_payer"]}`)
  - [x] 1.3 Handle edge case where variable entity cannot be resolved — raise `ApiMappingError` with actionable message
  - [x] 1.4 Unit tests with mock TBS: verify grouping logic, error on unknown variable entity

- [x] Task 2: Refactor `_extract_results()` to produce per-entity tables (AC: #1, #2, #3)
  - [x] 2.1 Replace single `pa.Table` construction with per-entity extraction loop
  - [x] 2.2 For each entity group, call `simulation.calculate()` for its variables and build a `pa.Table` per entity
  - [x] 2.3 Store results as `dict[str, pa.Table]` keyed by entity plural name
  - [x] 2.4 Unit tests: verify correct array lengths per entity, verify table column names

- [x] Task 3: Evolve `ComputationResult` to support multi-entity outputs (AC: #1, #3, #4)
  - [x] 3.1 Add `entity_tables: dict[str, pa.Table]` field to `ComputationResult` (default empty dict for backward compatibility)
  - [x] 3.2 Keep `output_fields: pa.Table` as the primary/default output for backward compatibility — when all variables belong to one entity, `output_fields` is that entity's table
  - [x] 3.3 When variables span multiple entities, `output_fields` contains the person-entity table (or the first entity's table if no person entity), and `entity_tables` contains all per-entity tables
  - [x] 3.4 Add metadata entry `"output_entities"` listing which entities have tables
  - [x] 3.5 Update `ComputationResult` type stub (`.pyi` file)
  - [x] 3.6 Unit tests: verify backward compatibility (existing code accessing `output_fields` still works), verify `entity_tables` populated correctly

- [x] Task 4: Update `OpenFiscaApiAdapter.compute()` to wire new extraction (AC: #1, #2, #3)
  - [x] 4.1 Pass TBS to `_extract_results()` so it can resolve variable entities
  - [x] 4.2 Update `compute()` return to populate both `output_fields` and `entity_tables`
  - [x] 4.3 Update metadata with `"output_entities"` and per-entity row counts
  - [x] 4.4 Unit tests with mock TBS and mock simulation

- [x] Task 5: Update downstream consumers for backward compatibility (AC: #4)
  - [x] 5.1 Verify `ComputationStep` in orchestrator still works (it accesses `result.output_fields.num_rows`)
  - [x] 5.2 Verify `PanelOutput.from_orchestrator_result()` still works (it accesses `comp_result.output_fields`)
  - [x] 5.3 Verify `MockAdapter` still produces valid `ComputationResult` objects
  - [x] 5.4 Run full existing test suite to confirm no regressions

- [x] Task 6: Integration tests with real OpenFisca-France (AC: #1, #2, #3)
  - [x] 6.1 Test: married couple (2 persons, 1 foyer, 1 menage) with mixed-entity output variables — verify separate tables
  - [x] 6.2 Test: single-entity variables only — verify backward-compatible single table
  - [x] 6.3 Test: verify array lengths match entity instance counts
  - [x] 6.4 Mark integration tests with `@pytest.mark.integration` (requires `openfisca-france` installed)

- [x] Task 7: Run quality gates (all ACs)
  - [x] 7.1 `uv run ruff check src/ tests/`
  - [x] 7.2 `uv run mypy src/`
  - [x] 7.3 `uv run pytest tests/computation/ tests/orchestrator/`

## Dev Notes

### Architecture Constraints

- **Adapter isolation is absolute**: Only `computation/openfisca_adapter.py` and `openfisca_api_adapter.py` may import OpenFisca. All OpenFisca imports must be lazy (inside methods, not at module level).
- **Frozen dataclasses**: `ComputationResult` is `@dataclass(frozen=True)`. Adding `entity_tables` requires a default value (`field(default_factory=dict)`) for backward compatibility.
- **Protocol compatibility**: `ComputationAdapter` protocol defines `compute() -> ComputationResult`. The protocol itself doesn't change — only the `ComputationResult` dataclass gains a new optional field.
- **PyArrow is canonical**: All data containers use `pa.Table`. No pandas.
- **`from __future__ import annotations`** at top of every file.

### Key OpenFisca API Details

**Determining a variable's entity:**
```python
# In OpenFisca, each variable has an .entity attribute
variable = tbs.variables["impot_revenu_restant_a_payer"]
entity = variable.entity  # Returns the Entity object
entity_key = entity.key    # "foyer_fiscal"
entity_plural = entity.plural  # "foyers_fiscaux"
```

**Determining array length for an entity in a simulation:**
```python
# simulation.calculate() returns numpy array with length == entity population count
# For a simulation with 2 persons and 1 foyer_fiscal:
salaire = simulation.calculate("salaire_net", "2024")  # shape: (2,)
irpp = simulation.calculate("impot_revenu_restant_a_payer", "2024")  # shape: (1,)
```

**Entity membership (for future broadcasting — NOT in scope for this story):**
```python
# OpenFisca tracks entity membership via roles
# simulation.populations["foyer_fiscal"].members_entity_id  → array mapping persons to foyers
# This is needed for Story 9.4 (broadcasting group-level values to person level)
```

### Files to Modify

| File | Change |
|------|--------|
| `src/reformlab/computation/types.py` | Add `entity_tables` field to `ComputationResult` |
| `src/reformlab/computation/types.pyi` | Update type stub |
| `src/reformlab/computation/openfisca_api_adapter.py` | Refactor `_extract_results()`, add `_resolve_variable_entities()` |
| `tests/computation/test_openfisca_api_adapter.py` | Add unit tests for entity-aware extraction |
| `tests/computation/test_result.py` | Add tests for new `entity_tables` field |
| `tests/computation/test_openfisca_integration.py` | Add integration tests for multi-entity output |

### Files to Verify (No Changes Expected)

| File | Why |
|------|-----|
| `src/reformlab/computation/adapter.py` | Protocol unchanged — verify still satisfied |
| `src/reformlab/computation/mock_adapter.py` | Verify `ComputationResult` construction still valid |
| `src/reformlab/orchestrator/computation_step.py` | Accesses `result.output_fields.num_rows` — must still work |
| `src/reformlab/orchestrator/panel.py` | Accesses `comp_result.output_fields` — must still work |
| `src/reformlab/computation/quality.py` | Validates `output_fields` schema — must still work |

### Backward Compatibility Strategy

The key design decision is **additive, not breaking**:

1. `ComputationResult.output_fields` remains a single `pa.Table` — all existing consumers continue to work unchanged.
2. A new `entity_tables: dict[str, pa.Table]` field is added with `default_factory=dict` so existing code constructing `ComputationResult` without it continues to work.
3. When all output variables belong to one entity, `output_fields` is that entity's table (same as before).
4. When variables span multiple entities, `output_fields` contains the person-entity table (primary entity), and `entity_tables` contains the full per-entity breakdown.
5. `MockAdapter` is unaffected — it never sets `entity_tables`, which defaults to `{}`.

### Mock TBS Pattern for Unit Tests

The existing test infrastructure uses `SimpleNamespace` mocks. Extend with variable entity info:

```python
from types import SimpleNamespace

def _make_mock_tbs_with_entities(
    entity_keys: tuple[str, ...] = ("individu", "foyer_fiscal", "menage"),
    variable_entities: dict[str, str] | None = None,
    person_entity: str = "individu",
) -> MagicMock:
    """Create a mock TBS where variables know their entity."""
    tbs = MagicMock()

    entities_by_key: dict[str, SimpleNamespace] = {}
    entities = []
    for key in entity_keys:
        entity = SimpleNamespace(
            key=key,
            plural=key + "s" if not key.endswith("s") else key,
            is_person=(key == person_entity),
        )
        entities.append(entity)
        entities_by_key[key] = entity
    tbs.entities = entities

    # Build variables with entity references
    if variable_entities is None:
        variable_entities = {}
    variables = {}
    for var_name, entity_key in variable_entities.items():
        var_mock = MagicMock()
        var_mock.entity = entities_by_key[entity_key]
        variables[var_name] = var_mock
    tbs.variables = variables

    return tbs
```

### Test Data: Married Couple Reference Case

From the spike 8-1 integration tests, the canonical multi-entity test case is:

```python
# 2 persons, 1 foyer_fiscal, 1 menage (married couple)
entities_dict = {
    "individus": {
        "person_0": {"salaire_de_base": {"2024": 30000.0}, "age": {"2024-01": 30}},
        "person_1": {"salaire_de_base": {"2024": 0.0}, "age": {"2024-01": 28}},
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
# Expected:
# salaire_net (individu) → 2 values
# impot_revenu_restant_a_payer (foyer_fiscal) → 1 value
# revenu_disponible (menage) → 1 value
```

### Existing Integration Test Pattern

Integration tests are in `tests/computation/test_openfisca_integration.py` and use:
- `@pytest.mark.integration` marker
- Module-scoped `tbs` fixture (TBS loads once, ~3-5 seconds)
- Direct `SimulationBuilder.build_from_entities()` calls
- Known-value assertions with tolerance: `abs(computed - expected) <= MARGIN`

### What This Story Does NOT Cover

- **Person-level broadcasting** of group entity values (deferred to Story 9.4 or later — requires entity membership arrays)
- **Variable periodicity** handling (`calculate` vs `calculate_add`) — that is Story 9.3
- **PopulationData 4-entity format** with role assignments — that is Story 9.4
- **Modifying the `ComputationAdapter` protocol** — protocol stays unchanged
- **Modifying `MockAdapter`** — it continues to work with the default empty `entity_tables`

### Project Structure Notes

- Source layout: `src/reformlab/` is the installable package
- Tests mirror source: `tests/computation/` matches `src/reformlab/computation/`
- Each test subdirectory has `__init__.py` and `conftest.py`
- Class-based test grouping with AC references in docstrings
- Integration tests require `openfisca-france` optional dependency: `uv sync --extra openfisca`
- Run unit tests: `uv run pytest tests/computation/ -m "not integration"`
- Run integration tests: `uv run pytest tests/computation/ -m integration`

### References

- [Source: `_bmad-output/implementation-artifacts/spike-findings-8-1-openfisca-integration.md` — Gap 2: Multi-entity output arrays]
- [Source: `src/reformlab/computation/openfisca_api_adapter.py` — `_extract_results()` method, lines 341-350]
- [Source: `src/reformlab/computation/types.py` — `ComputationResult` dataclass]
- [Source: `src/reformlab/orchestrator/computation_step.py` — downstream consumer of `ComputationResult.output_fields`]
- [Source: `src/reformlab/orchestrator/panel.py` — downstream consumer of `comp_result.output_fields`]
- [Source: `src/reformlab/computation/mock_adapter.py` — `MockAdapter` constructs `ComputationResult`]
- [Source: `tests/computation/test_openfisca_integration.py` — `test_multi_entity_variable_array_lengths` documenting the gap]
- [Source: `_bmad-output/planning-artifacts/epics.md` — Epic 9, Story 9.2 acceptance criteria]
- [Source: `_bmad-output/planning-artifacts/architecture.md` — Computation Adapter Pattern, Step-Pluggable Orchestrator]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (via create-story workflow)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed — comprehensive developer guide created
- All 3 acceptance criteria from epics file expanded to 5 ACs with backward compatibility and error handling coverage
- Spike 8-1 findings fully integrated as context
- Downstream consumer impact analysis completed (ComputationStep, PanelOutput, MockAdapter, quality.py)
- Backward compatibility strategy documented: additive `entity_tables` field with empty dict default
- Mock TBS pattern extended with variable-to-entity mapping for unit tests
- Integration test reference case (married couple) documented with expected array lengths
- **Code review synthesis (2026-03-01):** Fixed 5 issues found during review:
  1. (Critical) `metadata["output_entities"]` and `metadata["entity_row_counts"]` now computed from `result_entity_tables` (post-filter) so they are consistent with the returned `entity_tables` field — previously single-entity results had non-empty `output_entities` while `entity_tables` was `{}`, violating data contract
  2. (High) Added `ApiMappingError` guard in `__init__` for empty `output_variables` — prevents cryptic `StopIteration` from propagating up
  3. (High) Moved `_resolve_variable_entities()` call before `_build_simulation()` — fail-fast pattern avoids expensive simulation build if entity resolution fails
  4. (Medium) Replaced misleading comment + silent singular-key fallback in `_resolve_variable_entities` with explicit `ApiMappingError` — silently using the singular key as the plural would produce wrong dict keys (e.g. `"foyer_fiscal"` instead of `"foyers_fiscaux"`) and cause silent downstream failures
  5. (Medium) Added `metadata["output_entities"] == []` and `metadata["entity_row_counts"] == {}` assertions to `test_compute_single_entity_backward_compatible` — regression guard that would have caught issue #1

### File List

- `src/reformlab/computation/types.py` — modify (add `entity_tables` field)
- `src/reformlab/computation/types.pyi` — modify (update stub)
- `src/reformlab/computation/openfisca_api_adapter.py` — modify (refactor `_extract_results`, add `_resolve_variable_entities`)
- `tests/computation/test_openfisca_api_adapter.py` — modify (add entity-aware extraction tests)
- `tests/computation/test_result.py` — modify (add `entity_tables` tests)
- `tests/computation/test_openfisca_integration.py` — modify (add multi-entity output integration tests)

]]></file>
<file id="ccd1eda3" path="_bmad-output/implementation-artifacts/9-3-add-variable-periodicity-handling.md" label="STORY FILE"><![CDATA[

# Story 9.3: Add Variable Periodicity Handling

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **platform developer integrating OpenFisca-France**,
I want the adapter to automatically detect variable periodicities and use the correct OpenFisca calculation method (`calculate()` vs `calculate_add()`),
so that monthly variables (e.g., `salaire_net`) are correctly summed over yearly periods without crashing, and yearly/eternity variables continue to work as before.

## Context & Motivation

OpenFisca variables have a `definition_period` attribute that specifies the temporal granularity at which they are computed. In OpenFisca-France:

| Periodicity | `definition_period` | Example Variables | `calculate("var", "2024")` behavior |
|---|---|---|---|
| Monthly | `DateUnit.MONTH` ("month") | `salaire_net`, `salaire_de_base` | **Raises `ValueError`** — period mismatch |
| Yearly | `DateUnit.YEAR` ("year") | `impot_revenu_restant_a_payer`, `revenu_disponible` | Works — period matches |
| Eternal | `DateUnit.ETERNITY` ("eternity") | `date_naissance`, `sexe` | Works — any period accepted |

**The current adapter uses `simulation.calculate()` for ALL variables** (line 503 of `openfisca_api_adapter.py`). This crashes with a `ValueError` for monthly variables like `salaire_net` when the period is yearly (e.g., `"2024"`).

**The fix:** Detect each variable's `definition_period` from the TBS and dispatch to the correct calculation method:
- `MONTH`/`DAY`/`WEEK`/`WEEKDAY` → `simulation.calculate_add(var, period)` — sums sub-period values over the requested period
- `YEAR` → `simulation.calculate(var, period)` — direct calculation (current behavior)
- `ETERNITY` → `simulation.calculate(var, period)` — always accepted by OpenFisca

**Source:** Spike 8-1 findings, Gap 4. [Source: `_bmad-output/implementation-artifacts/spike-findings-8-1-openfisca-integration.md`, lines 71-77]

## Acceptance Criteria

1. **AC-1: Periodicity-aware calculation dispatch** — Given variables with different periodicities (monthly, yearly), when `compute()` is called with a yearly period, then the adapter uses `calculate_add()` for monthly variables and `calculate()` for yearly/eternity variables — producing correct results without `ValueError`.

2. **AC-2: Monthly variable yearly aggregation** — Given a monthly variable (e.g., `salaire_net`) requested for a yearly period, when computed, then the adapter automatically sums the 12 monthly values via `calculate_add()` according to OpenFisca conventions.

3. **AC-3: Invalid period format rejection** — Given an invalid period value (non-positive integer, zero, or unreasonable year), when passed to the adapter's `compute()`, then a clear `ApiMappingError` is raised identifying the expected format.

4. **AC-4: Backward compatibility** — Given output variables that are all yearly (the existing common case), when `compute()` is called, then behavior is identical to the pre-change implementation — no regression in results, metadata, or `entity_tables`.

5. **AC-5: Periodicity metadata** — Given a completed `compute()` call, when the result metadata is inspected, then it includes `"variable_periodicities"` mapping each output variable to its detected periodicity and the calculation method used.

6. **AC-6: Eternity variable handling** — Given an ETERNITY-period variable as an output variable, when `compute()` is called, then `simulation.calculate()` is used (NOT `calculate_add()`, which rejects eternity variables) and the value is returned correctly.

## Tasks / Subtasks

- [ ] Task 1: Add `_resolve_variable_periodicities()` method (AC: #1, #2, #6)
  - [ ] 1.1 Add method to `OpenFiscaApiAdapter` that queries `tbs.variables[var_name].definition_period` for each output variable
  - [ ] 1.2 Return `dict[str, str]` mapping variable name to periodicity string (`"month"`, `"year"`, `"eternity"`, `"day"`, `"week"`, `"weekday"`)
  - [ ] 1.3 Handle edge case where `definition_period` attribute is missing or has unexpected value — raise `ApiMappingError`
  - [ ] 1.4 Unit tests with mock TBS: verify periodicity detection for month/year/eternity variables, error on missing attribute

- [ ] Task 2: Add `_calculate_variable()` dispatch method (AC: #1, #2, #6)
  - [ ] 2.1 Add private method `_calculate_variable(simulation, var_name, period_str, periodicity) -> numpy.ndarray`
  - [ ] 2.2 Dispatch logic: `"month"`, `"day"`, `"week"`, `"weekday"` → `simulation.calculate_add(var, period_str)`; `"year"`, `"eternity"` → `simulation.calculate(var, period_str)`
  - [ ] 2.3 Log calculation method used per variable at DEBUG level
  - [ ] 2.4 Unit tests with mock simulation: verify correct method called based on periodicity

- [ ] Task 3: Refactor `_extract_results_by_entity()` to use periodicity-aware calculation (AC: #1, #2, #4, #6)
  - [ ] 3.1 Add `variable_periodicities: dict[str, str]` parameter to `_extract_results_by_entity()`
  - [ ] 3.2 Replace `simulation.calculate(var_name, period_str)` with `self._calculate_variable(simulation, var_name, period_str, variable_periodicities[var_name])`
  - [ ] 3.3 Unit tests: verify multi-entity extraction with mixed periodicities

- [ ] Task 4: Wire periodicity resolution into `compute()` (AC: #1, #2, #4, #5)
  - [ ] 4.1 Call `_resolve_variable_periodicities(tbs)` in `compute()` after `_resolve_variable_entities()` (fail-fast pattern — resolve both before building simulation)
  - [ ] 4.2 Pass `variable_periodicities` to `_extract_results_by_entity()`
  - [ ] 4.3 Add `"variable_periodicities"` and `"calculation_methods"` to result metadata
  - [ ] 4.4 Unit tests: verify metadata populated correctly in compute() result

- [ ] Task 5: Add period validation (AC: #3)
  - [ ] 5.1 Add validation at the top of `compute()`: period must be a positive integer in range [1000, 9999] (4-digit year)
  - [ ] 5.2 Raise `ApiMappingError` with summary "Invalid period", reason showing actual value, fix showing expected format
  - [ ] 5.3 Unit tests: invalid periods (0, -1, 99, 99999) raise `ApiMappingError`; valid periods (2024, 2025) pass

- [ ] Task 6: Verify backward compatibility (AC: #4)
  - [ ] 6.1 Run existing unit tests in `test_openfisca_api_adapter.py` — ensure all pass unchanged
  - [ ] 6.2 Run existing integration tests in `test_openfisca_integration.py` — ensure all pass unchanged
  - [ ] 6.3 Verify `MockAdapter` still produces valid `ComputationResult` (no new required fields)
  - [ ] 6.4 Verify `ComputationStep` in orchestrator still works (`result.output_fields.num_rows`)

- [ ] Task 7: Integration tests with real OpenFisca-France (AC: #1, #2, #6)
  - [ ] 7.1 Test: `salaire_net` (MONTH) with yearly period → verify `calculate_add()` is used and returns correct yearly sum
  - [ ] 7.2 Test: `impot_revenu_restant_a_payer` (YEAR) with yearly period → verify `calculate()` is used (unchanged)
  - [ ] 7.3 Test: mixed periodicity output variables in single `compute()` call → verify correct method per variable
  - [ ] 7.4 Test: `adapter.compute()` end-to-end with monthly output variable produces correct values
  - [ ] 7.5 Test: verify `variable_periodicities` metadata in integration test result
  - [ ] 7.6 Mark integration tests with `@pytest.mark.integration`

- [ ] Task 8: Run quality gates (all ACs)
  - [ ] 8.1 `uv run ruff check src/ tests/`
  - [ ] 8.2 `uv run mypy src/`
  - [ ] 8.3 `uv run pytest tests/computation/ tests/orchestrator/`

## Dev Notes

### Architecture Constraints

- **Adapter isolation is absolute**: Only `computation/openfisca_adapter.py` and `openfisca_api_adapter.py` may import OpenFisca. All OpenFisca imports must be lazy (inside methods, not at module level).
- **Frozen dataclasses**: `ComputationResult` is `@dataclass(frozen=True)`. No new fields are added in this story — only metadata entries.
- **Protocol compatibility**: `ComputationAdapter` protocol (`period: int`) is unchanged. The periodicity handling is internal to `OpenFiscaApiAdapter`.
- **PyArrow is canonical**: All data containers use `pa.Table`. No pandas.
- **`from __future__ import annotations`** at top of every file.
- **No bare `Exception` or `ValueError`**: Use subsystem-specific exceptions (`ApiMappingError`).

### OpenFisca Periodicity System — Complete Reference

**`DateUnit` is a `StrEnum`** (from `openfisca_core.periods.date_unit`):

```python
class DateUnit(StrEnum, metaclass=DateUnitMeta):
    WEEKDAY = "weekday"    # weight: 100
    WEEK = "week"          # weight: 200
    DAY = "day"            # weight: 100
    MONTH = "month"        # weight: 200
    YEAR = "year"          # weight: 300
    ETERNITY = "eternity"  # weight: 400
```

Since `DateUnit` extends `StrEnum`:
```python
variable.definition_period == "month"   # True (StrEnum comparison)
str(variable.definition_period)          # "month"
variable.definition_period.value         # "month"
variable.definition_period.name          # "MONTH"
```

**Accessing a variable's periodicity:**
```python
variable = tbs.variables["salaire_net"]
periodicity = variable.definition_period  # DateUnit.MONTH (a StrEnum)
# Since it's StrEnum, string comparison works directly:
if periodicity == "month":
    ...
```

### OpenFisca Calculation Method Dispatch

**`simulation.calculate(var, period)`:**
- Calls `_check_period_consistency()` which raises `ValueError` if `definition_period` doesn't match the period's unit
- ETERNITY: always accepted (any period)
- YEAR: requires yearly period
- MONTH: requires monthly period → **fails with yearly period**
- DAY: requires daily period

**`simulation.calculate_add(var, period)`:**
- Sums sub-period values: `sum(calculate(var, sub_period) for sub_period in period.get_subperiods(definition_period))`
- For MONTH variable with "2024" period → sums 12 monthly calculations
- REJECTS ETERNITY variables explicitly: "eternal variables can't be summed over time"
- Rejects if `unit_weight(definition_period) > unit_weight(period.unit)` (can't sum larger into smaller)

**`simulation.calculate_divide(var, period)`:**
- Divides a larger-period variable into smaller periods (e.g., yearly / 12 for monthly)
- Not needed for this story (we only have yearly periods as input)

### Dispatch Table (for yearly period input)

| `definition_period` | Method to use | Rationale |
|---|---|---|
| `"month"` | `calculate_add()` | Sum 12 monthly values to yearly |
| `"year"` | `calculate()` | Period matches directly |
| `"eternity"` | `calculate()` | Any period accepted; `calculate_add()` rejects eternity |
| `"day"` | `calculate_add()` | Sum ~365 daily values to yearly |
| `"week"` | `calculate_add()` | Sum ~52 weekly values to yearly |
| `"weekday"` | `calculate_add()` | Sum weekday values to yearly |

**Simplified rule:** Use `calculate()` for `"year"` and `"eternity"`, `calculate_add()` for everything else.

### Files to Modify

| File | Change |
|------|--------|
| `src/reformlab/computation/openfisca_api_adapter.py` | Add `_resolve_variable_periodicities()`, `_calculate_variable()`, refactor `_extract_results_by_entity()`, add period validation in `compute()` |
| `tests/computation/test_openfisca_api_adapter.py` | Add unit tests for periodicity detection, calculation dispatch, period validation |
| `tests/computation/test_openfisca_integration.py` | Add integration tests with monthly variables (`salaire_net`) |

### Files to Verify (No Changes Expected)

| File | Why |
|------|-----|
| `src/reformlab/computation/adapter.py` | Protocol unchanged (`period: int`) |
| `src/reformlab/computation/types.py` | `ComputationResult` unchanged — no new fields |
| `src/reformlab/computation/types.pyi` | Type stub unchanged |
| `src/reformlab/computation/mock_adapter.py` | Unaffected — no periodicity logic needed |
| `src/reformlab/computation/exceptions.py` | Reuse existing `ApiMappingError` — no new exception types |
| `src/reformlab/orchestrator/computation_step.py` | Passes `period=year` (int) to adapter — unchanged |
| `src/reformlab/orchestrator/panel.py` | Accesses `comp_result.output_fields` — unchanged |

### Backward Compatibility Strategy

This story is purely **internal to `OpenFiscaApiAdapter`** — no external interface changes:

1. `ComputationAdapter` protocol is unchanged (`period: int`).
2. `ComputationResult` is unchanged (no new fields; periodicity info goes in existing `metadata` dict).
3. `MockAdapter` is unaffected — it never calls OpenFisca.
4. Existing unit tests with mock TBS continue to work because `_make_mock_tbs()` creates variables with a default entity that (now) also needs a default `definition_period`. The existing mock assigns all variables to the person entity; Story 9.3 must ensure that mocks also set `definition_period` (default to `"year"` for backward compatibility).
5. `_extract_results_by_entity()` signature changes (new `variable_periodicities` parameter) — this is a private method, no external consumers.

### Mock TBS Extension for Unit Tests

Extend existing `_make_mock_tbs()` and `_make_mock_tbs_with_entities()` in the test file to include `definition_period`:

```python
# Existing _make_mock_tbs() — add default definition_period
def _make_mock_tbs(...):
    ...
    for name in variable_names:
        var_mock = MagicMock()
        var_mock.entity = default_entity
        var_mock.definition_period = "year"  # Default for backward compat
        variables[name] = var_mock
    ...

# New helper or extend _make_mock_tbs_with_entities()
def _make_mock_tbs_with_periodicities(
    variable_entities: dict[str, str],
    variable_periodicities: dict[str, str],
    ...
) -> MagicMock:
    """Create a mock TBS with both entity and periodicity info."""
    ...
    for var_name in variable_entities:
        var_mock = MagicMock()
        var_mock.entity = entities_by_key[variable_entities[var_name]]
        var_mock.definition_period = variable_periodicities.get(var_name, "year")
        variables[var_name] = var_mock
    ...
```

### Mock Simulation Extension for Unit Tests

The existing `_make_mock_simulation()` returns results keyed by variable name. For periodicity dispatch tests, extend to track which method was called:

```python
def _make_mock_simulation_with_methods(
    results: dict[str, numpy.ndarray],
) -> MagicMock:
    """Mock simulation that tracks calculate vs calculate_add calls."""
    sim = MagicMock()
    sim.calculate.side_effect = lambda var, period: results[var]
    sim.calculate_add.side_effect = lambda var, period: results[var]
    return sim
```

Then assert: `sim.calculate.assert_called_with("irpp", "2024")` and `sim.calculate_add.assert_called_with("salaire_net", "2024")`.

### Integration Test Reference Data

**Monthly variable test case — `salaire_net` for single person with 30k base salary:**

```python
# Input: salaire_de_base = 30000.0 (yearly salary base)
# Output: salaire_net = sum of 12 monthly net salary values
# Expected: salaire_net should be positive and in range [20000, 30000]
# (net salary is less than gross due to social contributions)

population = PopulationData(
    tables={
        "individu": pa.table({
            "salaire_de_base": pa.array([30000.0]),
            "age": pa.array([30]),
        }),
    },
)
```

**Mixed periodicity test case — `salaire_net` (MONTH) + `impot_revenu_restant_a_payer` (YEAR):**

```python
# Using multi-entity adapter with mixed periodicities:
adapter = OpenFiscaApiAdapter(
    country_package="openfisca_france",
    output_variables=(
        "salaire_net",                      # individu, MONTH → calculate_add
        "impot_revenu_restant_a_payer",      # foyer_fiscal, YEAR → calculate
    ),
)
# Both variables should return correct values without ValueError
```

### Existing Integration Test Fix Required

The existing integration test `test_multi_entity_variable_array_lengths` (line 305 in `test_openfisca_integration.py`) already uses `calculate_add` for `salaire_net` manually:

```python
salaire_net = simulation.calculate_add("salaire_net", "2024")
```

This test calls OpenFisca directly (not through the adapter). After Story 9.3, new integration tests should verify that the **adapter** itself correctly dispatches to `calculate_add()` for monthly variables.

### What This Story Does NOT Cover

- **Input variable period assignment** — `_population_to_entity_dict()` wraps all input values in `{period_str: value}`. Some input variables may need monthly period format (e.g., `"2024-01"` instead of `"2024"` for `age`). This is a separate concern for future work (potentially Story 9.4 or a follow-up).
- **Sub-yearly period support in the protocol** — `ComputationAdapter.compute(period: int)` remains yearly. Supporting monthly computation periods would require protocol changes.
- **`calculate_divide()` support** — Not needed since the adapter only handles yearly periods (the largest common unit).
- **PopulationData 4-entity format** — That is Story 9.4.
- **Entity broadcasting** — Broadcasting group-level values to person level is not in scope.
- **Modifying `MockAdapter`** — It never calls OpenFisca and doesn't need periodicity logic.

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

- [Source: `_bmad-output/implementation-artifacts/spike-findings-8-1-openfisca-integration.md` — Gap 4: Monthly vs yearly variable periodicity]
- [Source: `src/reformlab/computation/openfisca_api_adapter.py` — `_extract_results_by_entity()` method, line 503: `simulation.calculate(var_name, period_str)`]
- [Source: `.venv/.../openfisca_core/periods/date_unit.py` — `DateUnit(StrEnum)` definition with MONTH, YEAR, ETERNITY values]
- [Source: `.venv/.../openfisca_core/simulations/simulation.py` — `_check_period_consistency()` lines 353-374: raises ValueError for period mismatch]
- [Source: `.venv/.../openfisca_core/simulations/simulation.py` — `calculate_add()` lines 180-223: sums sub-periods, rejects ETERNITY]
- [Source: `.venv/.../openfisca_core/variables/variable.py` — `definition_period` attribute, line 144: required, allowed_values=DateUnit]
- [Source: `src/reformlab/computation/adapter.py` — `ComputationAdapter` protocol, `period: int` parameter]
- [Source: `src/reformlab/computation/exceptions.py` — `ApiMappingError` structured error pattern]
- [Source: `src/reformlab/orchestrator/computation_step.py` — downstream consumer, passes `period=year` to adapter]
- [Source: `_bmad-output/implementation-artifacts/9-2-handle-multi-entity-output-arrays.md` — predecessor story, explicitly excludes periodicity handling]
- [Source: `_bmad-output/planning-artifacts/epics.md` — Epic 9, Story 9.3 acceptance criteria]
- [Source: `tests/computation/test_openfisca_integration.py` — lines 305-314: `calculate_add("salaire_net", "2024")` used manually in existing test]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (via create-story workflow)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed — comprehensive developer guide created
- All 3 acceptance criteria from epics file expanded to 6 ACs with backward compatibility, metadata, and eternity variable coverage
- Spike 8-1 findings Gap 4 fully integrated as context with root cause analysis
- OpenFisca periodicity system documented from source code inspection:
  - `DateUnit` is a `StrEnum` — string comparison works directly
  - `calculate()` raises `ValueError` for MONTH variables with yearly periods
  - `calculate_add()` sums sub-periods but REJECTS ETERNITY variables
  - Complete dispatch table documented for all 6 `DateUnit` values
- `_check_period_consistency()` source code analyzed (simulation.py lines 353-374) to understand exact failure mode
- `calculate_add()` source code analyzed (simulation.py lines 180-223) to understand ETERNITY rejection and sub-period iteration
- Backward compatibility strategy: purely internal changes to `OpenFiscaApiAdapter`, no protocol/type/mock changes
- Mock TBS extension patterns documented for unit tests (add `definition_period` to variable mocks)
- Integration test reference data documented (salaire_net monthly, mixed periodicity cases)
- Story 9.2 predecessor analysis: confirms explicit exclusion of periodicity ("What This Story Does NOT Cover")

### File List

- `src/reformlab/computation/openfisca_api_adapter.py` — modify (add `_resolve_variable_periodicities()`, `_calculate_variable()`, refactor `_extract_results_by_entity()`, add period validation)
- `tests/computation/test_openfisca_api_adapter.py` — modify (add periodicity unit tests, extend mock TBS with `definition_period`)
- `tests/computation/test_openfisca_integration.py` — modify (add monthly variable integration tests)

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
        """
        start = time.monotonic()

        tbs = self._get_tax_benefit_system()
        self._validate_output_variables(tbs)

        # Story 9.2: Resolve entity grouping before building simulation (fail fast —
        # avoid expensive SimulationBuilder.build_from_entities() if entity
        # resolution fails due to incompatible country package).
        vars_by_entity = self._resolve_variable_entities(tbs)

        simulation = self._build_simulation(population, policy, period, tbs)
        entity_tables = self._extract_results_by_entity(
            simulation, period, vars_by_entity
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
        """
        result: dict[str, Any] = {}

        # Build key→plural mapping for normalisation
        key_to_plural = {entity.key: entity.plural for entity in tbs.entities}
        plural_set = set(key_to_plural.values())

        # Identify the person entity (singular entity in OpenFisca)
        person_entity_plural: str | None = None
        for entity in tbs.entities:
            if not getattr(entity, "is_person", False):
                continue
            person_entity_plural = entity.plural
            break

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
                    # Wrap scalar values in period dict for variable assignments
                    instance_data[col] = {period_str: value}

                entity_dict[instance_id] = instance_data

            result[plural_key] = entity_dict

        # Inject policy parameters as input-variable values on the person entity
        if policy.parameters and person_entity_plural and person_entity_plural in result:
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
    ) -> dict[str, pa.Table]:
        """Extract output variables grouped by entity into per-entity tables.

        For each entity group, calls ``simulation.calculate()`` for its
        variables and builds a ``pa.Table`` per entity. Arrays within an
        entity group share the same length (entity instance count).

        Args:
            simulation: The completed OpenFisca simulation.
            period: Computation period (integer year).
            vars_by_entity: Output variables grouped by entity plural name
                (from ``_resolve_variable_entities``).

        Returns:
            Dict mapping entity plural name to a PyArrow Table containing
            that entity's output variables.
        """
        period_str = str(period)
        entity_tables: dict[str, pa.Table] = {}

        for entity_plural, var_names in vars_by_entity.items():
            arrays: dict[str, pa.Array] = {}
            for var_name in var_names:
                numpy_array = simulation.calculate(var_name, period_str)
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
"""

from __future__ import annotations

import sys
from types import SimpleNamespace
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
    default_entity = entities_by_key.get(person_entity, entities[0])
    variables: dict[str, Any] = {}
    for name in variable_names:
        var_mock = MagicMock()
        var_mock.entity = default_entity
        variables[name] = var_mock
    tbs.variables = variables

    return tbs

def _make_mock_tbs_with_entities(
    entity_keys: tuple[str, ...] = ("individu", "foyer_fiscal", "menage"),
    entity_plurals: dict[str, str] | None = None,
    variable_entities: dict[str, str] | None = None,
    person_entity: str = "individu",
) -> MagicMock:
    """Create a mock TBS where variables know their entity.

    Story 9.2: Extended mock for entity-aware extraction tests.

    Args:
        entity_keys: Entity singular keys.
        entity_plurals: Mapping of singular key to plural form.
            Defaults to appending "s" (with special cases).
        variable_entities: Mapping of variable name to entity key.
        person_entity: Which entity key is the person entity.

    Returns:
        Mock TBS with entity-aware variables.
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

    entities_by_key: dict[str, SimpleNamespace] = {}
    entities = []
    for key in entity_keys:
        plural = entity_plurals.get(key) or default_plurals.get(key) or key + "s"
        entity = SimpleNamespace(
            key=key,
            plural=plural,
            is_person=(key == person_entity),
        )
        entities.append(entity)
        entities_by_key[key] = entity
    tbs.entities = entities

    # Build variables with entity references
    if variable_entities is None:
        variable_entities = {}
    variables: dict[str, Any] = {}
    for var_name, entity_key in variable_entities.items():
        var_mock = MagicMock()
        var_mock.entity = entities_by_key[entity_key]
        variables[var_name] = var_mock
    tbs.variables = variables

    return tbs

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

        result = adapter._extract_results_by_entity(mock_simulation, 2024, vars_by_entity)

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

        result = adapter._extract_results_by_entity(mock_simulation, 2024, vars_by_entity)

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

        result = adapter._extract_results_by_entity(mock_simulation, 2024, vars_by_entity)

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

        mock_builder_instance = MagicMock()
        mock_simulation = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            with pytest.raises(ApiMappingError, match="Cannot determine entity"):
                adapter.compute(
                    population, PolicyConfig(parameters={}, name="test"), 2024
                )

]]></file>
<file id="895c54dc" path="tests/computation/test_openfisca_integration.py" label="SOURCE CODE"><![CDATA[

from __future__ import annotations
from 

]]></file>
</context>
<variables>
<var name="architecture_file" description="Architecture for technical requirements verification" load_strategy="SELECTIVE_LOAD" token_approx="2785">_bmad-output/planning-artifacts/architecture-diagrams.md</var>
<var name="author">BMad</var>
<var name="communication_language">English</var>
<var name="date">2026-03-01</var>
<var name="description">Quality competition validator - systematically review and improve story context created by create-story workflow</var>
<var name="document_output_language">English</var>
<var name="epic_num">9</var>
<var name="epics_file" description="Enhanced epics+stories file for story verification" load_strategy="SELECTIVE_LOAD" token_approx="8484">_bmad-output/planning-artifacts/epics.md</var>
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
<var name="story_file" file_id="ccd1eda3">embedded in prompt, file id: ccd1eda3</var>
<var name="story_id">9.3</var>
<var name="story_key">9-3-add-variable-periodicity-handling</var>
<var name="story_num">3</var>
<var name="story_title">add-variable-periodicity-handling</var>

<var name="timestamp">20260301_202911</var>
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
      - Story ID: 9.3
      - Story Key: 9-3-add-variable-periodicity-handling
      - Title: add-variable-periodicity-handling
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
      <action>Extract COMPLETE Epic 9 context:
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
      <check if="3 &gt; 1">
        <action>Calculate previous story path: 9-{{story_num - 1}}-*.md</action>
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
      <check if="3 == 1">
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

    <action>Load the story file: /Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/9-3-add-variable-periodicity-handling.md</action>

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

**Validation Report:** /Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/story-validations/validation-report-9-3-add-variable-periodicity-handling-2026-03-01.md
**Story File:** /Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/9-3-add-variable-periodicity-handling.md

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
1. ✅ Review the updated story file: `/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/9-3-add-variable-periodicity-handling.md`
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