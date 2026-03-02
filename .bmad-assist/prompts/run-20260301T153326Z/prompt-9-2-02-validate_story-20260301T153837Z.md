<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 9 -->
<!-- Story: 2 -->
<!-- Phase: validate-story -->
<!-- Timestamp: 20260301T153837Z -->
<compiled-workflow>
<mission><![CDATA[

Adversarial Story Validation

Target: Story 9.2 - handle-multi-entity-output-arrays

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

Status: ready-for-dev

## Story

As a **platform developer integrating OpenFisca-France**,
I want the adapter to correctly handle output variables that belong to different entities (individu, menage, famille, foyer_fiscal),
so that mixed-entity `compute()` calls return correctly-shaped results with each variable's values stored in the appropriate entity-level table.

## Problem Statement

The current `_extract_results()` method in `OpenFiscaApiAdapter` (line 341 of `openfisca_api_adapter.py`) naively combines all output variable arrays into a single `pa.Table`:

```python
def _extract_results(self, simulation: Any, period: int) -> pa.Table:
    period_str = str(period)
    arrays: dict[str, pa.Array] = {}
    for var_name in self._output_variables:
        numpy_array = simulation.calculate(var_name, period_str)
        arrays[var_name] = pa.array(numpy_array)
    return pa.table(arrays)
```

This breaks when output variables belong to different entities because OpenFisca returns different-length arrays per entity:
- `salaire_net` (individu-level) returns **N values** (one per person)
- `impot_revenu_restant_a_payer` (foyer_fiscal-level) returns **M values** (one per tax household)
- `revenu_disponible` (menage-level) returns **K values** (one per dwelling)

For a married couple (2 persons, 1 foyer_fiscal, 1 menage), `salaire_net` returns 2 values but `impot_revenu_restant_a_payer` returns 1 value. PyArrow cannot combine these into a single table.

**Evidence:** Spike 8-1 integration test `test_multi_entity_variable_array_lengths` (line 266 of `test_openfisca_integration.py`) explicitly demonstrates this gap.

## Acceptance Criteria

1. Given output variables that return per-entity arrays (e.g., per-menage, per-foyer_fiscal), when the adapter processes results, then arrays are correctly mapped to their respective entity tables.
2. Given a variable defined on `foyer_fiscal` entity, when results are returned, then the output array length matches the number of foyers fiscaux, not the number of individuals.
3. Given mixed-entity output variables, when processed, then each variable's values are stored in the correct entity-level result table with proper entity IDs.

## Tasks / Subtasks

- [ ] Task 1: Add `output_tables` field to `ComputationResult` (AC: #1, #3)
  - [ ] 1.1 Add `output_tables: dict[str, pa.Table] | None = None` field to `ComputationResult` in `types.py`
  - [ ] 1.2 Keep existing `output_fields: pa.Table` for backward compatibility (single-entity or flattened results)
  - [ ] 1.3 Add helper property `all_entity_tables() -> dict[str, pa.Table]` that returns `output_tables` when set, or wraps `output_fields` in `{"default": output_fields}` as fallback
  - [ ] 1.4 Add helper method `row_count_by_entity() -> dict[str, int]` for governance metadata
  - [ ] 1.5 Update `OutputFields` type alias documentation to reflect dual-mode usage

- [ ] Task 2: Implement entity-aware `_extract_results()` in `OpenFiscaApiAdapter` (AC: #1, #2, #3)
  - [ ] 2.1 Add `_resolve_variable_entities()` method that queries `tbs.variables[var_name].entity.key` for each output variable and groups variables by entity key
  - [ ] 2.2 Rewrite `_extract_results()` to iterate entity groups: for each entity, call `simulation.calculate()` on its variables and build a per-entity `pa.Table`
  - [ ] 2.3 When all variables belong to one entity, set `output_fields` to that single table (backward-compatible path)
  - [ ] 2.4 When variables span multiple entities, set `output_fields` to the person-entity table (or first entity if no person entity) and populate `output_tables` with all entity tables
  - [ ] 2.5 Store the TBS reference on the instance (`self._tbs`) so `_extract_results` can access entity metadata without re-loading
  - [ ] 2.6 Add entity key as metadata in each per-entity table's schema metadata or in `ComputationResult.metadata["entity_map"]`

- [ ] Task 3: Add validation for entity resolution (AC: #2)
  - [ ] 3.1 Add error handling for variables whose entity cannot be resolved (e.g., raise `ApiMappingError` with variable name and available entities)
  - [ ] 3.2 Log entity grouping at DEBUG level: `"entity=%s variables=%s count=%d"` for each entity group

- [ ] Task 4: Update downstream consumers for backward compatibility (AC: #1, #3)
  - [ ] 4.1 Update `ComputationStep.execute()` in `computation_step.py` (line 154): use `result.output_fields.num_rows` (unchanged — single-entity path still works) and optionally log per-entity row counts from `row_count_by_entity()`
  - [ ] 4.2 Verify `PanelOutput.from_orchestrator_result()` in `panel.py` (line 81) still works since it reads `result.output_fields` (the person-entity or default table)
  - [ ] 4.3 Verify `validate_output()` in `quality.py` still works against `output_fields`
  - [ ] 4.4 Verify `MockAdapter` still works (it only sets `output_fields`, never `output_tables`)

- [ ] Task 5: Update unit tests (AC: #1, #2, #3)
  - [ ] 5.1 Add unit tests in `test_openfisca_api_adapter.py` for `_resolve_variable_entities()` with mock TBS containing multi-entity variables
  - [ ] 5.2 Add unit tests for `_extract_results()` with mock simulation returning different-length arrays per entity
  - [ ] 5.3 Add unit test verifying single-entity case produces backward-compatible `output_fields` (no `output_tables`)
  - [ ] 5.4 Add unit test for `ComputationResult.all_entity_tables()` helper
  - [ ] 5.5 Add unit test for `ComputationResult.row_count_by_entity()` helper

- [ ] Task 6: Update integration tests (AC: #1, #2, #3)
  - [ ] 6.1 Add integration test: mixed-entity compute (individu + foyer_fiscal variables) returns correct entity tables
  - [ ] 6.2 Add integration test: entity table lengths match expected entity counts (2 persons, 1 foyer_fiscal for married couple)
  - [ ] 6.3 Add integration test: single-entity compute returns backward-compatible result (output_fields only)
  - [ ] 6.4 Update existing `test_multi_entity_variable_array_lengths` to verify adapter now handles this case correctly (was previously documenting the gap)

- [ ] Task 7: Run full test suite and type checks
  - [ ] 7.1 `uv run pytest tests/computation/` — all unit tests pass
  - [ ] 7.2 `uv run pytest tests/orchestrator/` — no regressions in orchestrator
  - [ ] 7.3 `uv run pytest tests/ -m "not integration"` — full non-integration suite passes
  - [ ] 7.4 `uv run ruff check src/ tests/` — no lint errors
  - [ ] 7.5 `uv run mypy src/` — strict mode passes

## Dev Notes

### Architecture Constraints

- **Frozen dataclasses everywhere** — `ComputationResult` is `@dataclass(frozen=True)`. New fields must have defaults to preserve backward compatibility. Use `field(default=None)` for `output_tables`.
- **`from __future__ import annotations`** at top of every file, no exceptions.
- **Adapter isolation** — only files in `src/reformlab/computation/` may import OpenFisca. The `tbs.variables[var].entity` lookup must stay inside the adapter module.
- **PyArrow is canonical** — all entity tables are `pa.Table`. No pandas.
- **Protocol, not ABC** — `ComputationAdapter` is a `Protocol`. Adding `output_tables` to `ComputationResult` does NOT change the protocol signature (it's a return type field, not a method).
- **Subsystem exceptions** — use `ApiMappingError` for entity resolution failures (already defined in `exceptions.py`).

### OpenFisca Entity API (Critical Knowledge)

OpenFisca's TaxBenefitSystem exposes variable-to-entity mapping:

```python
# How to determine which entity a variable belongs to:
variable = tbs.variables["impot_revenu_restant_a_payer"]
entity_key = variable.entity.key        # "foyer_fiscal"
entity_plural = variable.entity.plural  # "foyers_fiscaux"

variable2 = tbs.variables["salaire_net"]
entity_key2 = variable2.entity.key      # "individu"
```

**OpenFisca-France entities:**
| Entity Key | Plural | Description | Is Person |
|---|---|---|---|
| `individu` | `individus` | Individual person | Yes |
| `famille` | `familles` | Family (benefits unit) | No |
| `foyer_fiscal` | `foyers_fiscaux` | Tax household (income tax unit) | No |
| `menage` | `menages` | Dwelling/household (housing unit) | No |

**Entity array lengths** — For N persons grouped into M foyers fiscaux and K menages:
- `simulation.calculate("salaire_net", "2024")` returns array of length N
- `simulation.calculate("impot_revenu_restant_a_payer", "2024")` returns array of length M
- `simulation.calculate("revenu_disponible", "2024")` returns array of length K

### Implementation Strategy: Additive, Not Breaking

The recommended approach is **additive** — add `output_tables` alongside existing `output_fields`, not replace it:

```python
@dataclass(frozen=True)
class ComputationResult:
    output_fields: OutputFields                        # Keep: backward compat
    output_tables: dict[str, pa.Table] | None = None   # New: per-entity tables
    adapter_version: str
    period: int
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def all_entity_tables(self) -> dict[str, pa.Table]:
        if self.output_tables is not None:
            return self.output_tables
        return {"default": self.output_fields}

    def row_count_by_entity(self) -> dict[str, int]:
        return {k: t.num_rows for k, t in self.all_entity_tables.items()}
```

**Why additive?** There are 5+ critical downstream consumers of `output_fields` (see "Downstream Consumers" below). Changing its type from `pa.Table` to `dict[str, pa.Table]` would break them all. The additive approach means:
1. All existing code works unchanged (reads `output_fields`)
2. New multi-entity-aware code reads `output_tables` or `all_entity_tables`
3. Story 9.4 (4-entity population format) can later migrate consumers to `output_tables`

### Downstream Consumers of `output_fields` (DO NOT BREAK)

| Consumer | File | Line | Access Pattern |
|---|---|---|---|
| `ComputationStep.execute()` | `orchestrator/computation_step.py` | 154 | `.num_rows` |
| `PanelOutput.from_orchestrator_result()` | `orchestrator/panel.py` | 81-92 | Full table methods |
| `validate_output()` | `computation/quality.py` | 356+ | `.column_names`, `.column()` |
| `MockAdapter.compute()` | `computation/mock_adapter.py` | 82 | Returns `pa.Table` |
| Determinism test | `tests/orchestrator/test_computation_step.py` | 247 | `.equals()` |
| API interface tests | `tests/interfaces/test_api.py` | 933+ | `.num_rows`, `.column()` |

### Source Files to Modify

| File | Change |
|---|---|
| `src/reformlab/computation/types.py` | Add `output_tables` field and helper methods to `ComputationResult` |
| `src/reformlab/computation/openfisca_api_adapter.py` | Rewrite `_extract_results()`, add `_resolve_variable_entities()` |
| `tests/computation/test_openfisca_api_adapter.py` | New unit tests for entity-aware extraction |
| `tests/computation/test_openfisca_integration.py` | New integration tests, update gap-documenting test |
| `tests/computation/test_result.py` | Tests for new `ComputationResult` helpers |

### Files to Verify (No Changes Expected)

| File | Verify |
|---|---|
| `src/reformlab/computation/adapter.py` | Protocol unchanged (returns `ComputationResult`) |
| `src/reformlab/computation/mock_adapter.py` | Still works (only sets `output_fields`, `output_tables` defaults to `None`) |
| `src/reformlab/orchestrator/computation_step.py` | Still works (reads `output_fields.num_rows`) |
| `src/reformlab/orchestrator/panel.py` | Still works (reads `output_fields`) |
| `src/reformlab/computation/quality.py` | Still works (validates `output_fields`) |

### Testing Patterns

- **Unit tests** mock the TBS with configurable entities. The existing `_make_mock_tbs()` helper in `test_openfisca_api_adapter.py` already creates mock entities — extend it to include mock variables with `.entity.key` attributes.
- **Integration tests** use `pytest.importorskip("openfisca_france")` and are marked `@pytest.mark.integration`. They require the `openfisca-france` optional dependency.
- **Fixtures in conftest** — `sample_population()`, `sample_policy()`, `empty_policy()` in `tests/computation/conftest.py`.
- Run unit tests: `uv run pytest tests/computation/ -m "not integration"`
- Run integration tests: `uv run pytest tests/computation/ -m integration`
- Run full suite: `uv run pytest tests/ -m "not integration"`

### Interaction with Story 9.3 (Variable Periodicity)

This story does NOT need to handle monthly vs yearly periodicity — that's Story 9.3's scope. However, `_extract_results()` currently uses `simulation.calculate()` for all variables. When testing with real OpenFisca-France, some variables (e.g., `salaire_net`) will need `calculate_add()` for yearly aggregation. For this story's integration tests:
- Use variables with `definition_period = YEAR` (e.g., `impot_revenu_restant_a_payer`, `revenu_disponible`) to avoid periodicity issues
- Or use `calculate_add()` in test helpers as a workaround (already done in existing integration tests)

The production fix for periodicity is Story 9.3.

### Interaction with Story 9.4 (4-Entity Population Format)

Story 9.4 will define a richer `PopulationData` format with entity membership arrays (person-to-household mappings). This story enables 9.4 by providing per-entity output tables. Once 9.4 is done, a future enhancement could broadcast group-level results to person level using membership arrays — but that's NOT in scope here.

### Project Structure Notes

- Source: `src/reformlab/computation/` (all changes contained in this subsystem)
- Tests: `tests/computation/` (mirrors source structure)
- All domain types in `types.py` are frozen dataclasses
- Module docstrings reference story/FR IDs
- Section separators use `# ====...====` comment blocks

### References

- [Source: `_bmad-output/implementation-artifacts/spike-findings-8-1-openfisca-integration.md` — Gap 2: Multi-entity output arrays]
- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 9.2 acceptance criteria]
- [Source: `src/reformlab/computation/openfisca_api_adapter.py` lines 341-350 — current `_extract_results()` implementation]
- [Source: `src/reformlab/computation/types.py` — `ComputationResult`, `PopulationData`, `OutputFields` definitions]
- [Source: `tests/computation/test_openfisca_integration.py` lines 266-313 — existing gap test]
- [Source: `src/reformlab/orchestrator/computation_step.py` line 154 — downstream consumer]
- [Source: `src/reformlab/orchestrator/panel.py` lines 81-92 — downstream consumer]
- [Source: `_bmad-output/project-context.md` — project coding standards and rules]

## Dev Agent Record

### Agent Model Used

<!-- filled by dev agent -->

### Debug Log References

<!-- filled by dev agent -->

### Completion Notes List

<!-- filled by dev agent -->

### Change Log

| Date | Author | Change |
|------|--------|--------|
| 2026-03-01 | BMad create-story workflow | Initial story creation — comprehensive context analysis |

### File List

<!-- filled by dev agent after implementation -->

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
<var name="story_file" file_id="08fae9ea">embedded in prompt, file id: 08fae9ea</var>
<var name="story_id">9.2</var>
<var name="story_key">9-2-handle-multi-entity-output-arrays</var>
<var name="story_num">2</var>
<var name="story_title">handle-multi-entity-output-arrays</var>

<var name="timestamp">20260301_163837</var>
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
      - Story ID: 9.2
      - Story Key: 9-2-handle-multi-entity-output-arrays
      - Title: handle-multi-entity-output-arrays
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
      <check if="2 &gt; 1">
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
      <check if="2 == 1">
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

    <action>Load the story file: /Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/9-2-handle-multi-entity-output-arrays.md</action>

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

**Validation Report:** /Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/story-validations/validation-report-9-2-handle-multi-entity-output-arrays-2026-03-01.md
**Story File:** /Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/9-2-handle-multi-entity-output-arrays.md

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
1. ✅ Review the updated story file: `/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/9-2-handle-multi-entity-output-arrays.md`
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