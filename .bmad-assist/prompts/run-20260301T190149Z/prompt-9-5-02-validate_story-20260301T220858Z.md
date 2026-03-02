<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 9 -->
<!-- Story: 5 -->
<!-- Phase: validate-story -->
<!-- Timestamp: 20260301T220858Z -->
<compiled-workflow>
<mission><![CDATA[

Adversarial Story Validation

Target: Story 9.5 - openfisca-france-reference-test-suite

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

Status: in-progress

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

3. **AC-3: Invalid period format rejection** — Given an invalid period value (non-positive integer, zero, or outside the 4-digit year range 1000–9999), when passed to the adapter's `compute()` as the very first check before any TBS operations, then a clear `ApiMappingError` is raised with summary `"Invalid period"`, the actual value, and the expected format (`"positive integer year in range [1000, 9999], e.g. 2024"`).

4. **AC-4: Backward compatibility** — Given output variables that are all yearly (the existing common case), when `compute()` is called, then behavior is identical to the pre-change implementation — no regression in results, metadata, or `entity_tables`.

5. **AC-5: Periodicity metadata** — Given a completed `compute()` call, when the result metadata is inspected, then it includes two entries: `"variable_periodicities"` (a `dict[str, str]` mapping each output variable to its detected periodicity string, e.g., `{"salaire_net": "month", "irpp": "year"}`) and `"calculation_methods"` (a `dict[str, str]` mapping each output variable to the method invoked, e.g., `{"salaire_net": "calculate_add", "irpp": "calculate"}`).

6. **AC-6: Eternity variable handling** — Given an ETERNITY-period variable (e.g., `date_naissance`, `sexe`) as an output variable, when `compute()` is called, then `simulation.calculate()` is used (NOT `calculate_add()`, which explicitly raises `"eternal variables can't be summed over time"`) and the value is returned correctly. Verified by unit test with mock simulation asserting `simulation.calculate` is called and `simulation.calculate_add` is NOT called when `periodicity == "eternity"`.

## Tasks / Subtasks

- [x] Task 1: Add `_resolve_variable_periodicities()` method (AC: #1, #2, #6)
  - [x] 1.1 Add method to `OpenFiscaApiAdapter` that queries `tbs.variables[var_name].definition_period` for each output variable
  - [x] 1.2 Return `dict[str, str]` mapping variable name to periodicity string (`"month"`, `"year"`, `"eternity"`, `"day"`, `"week"`, `"weekday"`)
  - [x] 1.3 Handle edge case where `definition_period` attribute is missing or has unexpected value — raise `ApiMappingError`
  - [x] 1.4 Unit tests with mock TBS: verify periodicity detection for month/year/eternity variables, error on missing attribute
  - [x] 1.5 Update `_make_mock_tbs()` in `tests/computation/test_openfisca_api_adapter.py` to add `var_mock.definition_period = "year"` in the variable-building loop — required because `_resolve_variable_periodicities()` now accesses `variable.definition_period` during every `compute()` call; without this fix, `MagicMock().definition_period` returns a MagicMock (not `"year"`), causing all existing `compute()` unit tests to dispatch to `calculate_add()` instead of `calculate()`, breaking `TestPeriodFormatting.test_period_passed_as_string`

- [x] Task 2: Add `_calculate_variable()` dispatch method (AC: #1, #2, #6)
  - [x] 2.1 Add private method `_calculate_variable(simulation, var_name, period_str, periodicity) -> numpy.ndarray`
  - [x] 2.2 Dispatch logic: `"month"`, `"day"`, `"week"`, `"weekday"` → `simulation.calculate_add(var, period_str)`; `"year"`, `"eternity"` → `simulation.calculate(var, period_str)`
  - [x] 2.3 Log calculation method used per variable at DEBUG level
  - [x] 2.4 Unit tests with mock simulation: verify correct method called based on periodicity

- [x] Task 3: Refactor `_extract_results_by_entity()` to use periodicity-aware calculation (AC: #1, #2, #4, #6)
  - [x] 3.1 Add `variable_periodicities: dict[str, str]` parameter to `_extract_results_by_entity()` — ⚠️ this is a breaking change to a private method used directly by 3 existing unit tests; update all 3 callers in `TestExtractResultsByEntity` (`test_single_entity_extraction`, `test_multi_entity_extraction`, `test_multiple_variables_per_entity`) to pass `variable_periodicities` with `"year"` for each test variable (e.g., `variable_periodicities={"salaire_net": "year", "irpp": "year"}`)
  - [x] 3.2 Replace `simulation.calculate(var_name, period_str)` with `self._calculate_variable(simulation, var_name, period_str, variable_periodicities[var_name])`
  - [x] 3.3 Unit tests: verify multi-entity extraction with mixed periodicities

- [x] Task 4: Wire periodicity resolution into `compute()` (AC: #1, #2, #4, #5)
  - [x] 4.1 Call `_resolve_variable_periodicities(tbs)` in `compute()` using this explicit call order (fail-fast — all validation before expensive simulation construction):
        1. `_validate_output_variables(tbs)`
        2. `vars_by_entity = _resolve_variable_entities(tbs)`          # Story 9.2
        3. `var_periodicities = _resolve_variable_periodicities(tbs)`  # Story 9.3 (NEW)
        4. `simulation = _build_simulation(population, policy, period, tbs)` # Expensive
        5. `entity_tables = _extract_results_by_entity(simulation, period, vars_by_entity, var_periodicities)` # Modified
  - [x] 4.2 Pass `variable_periodicities` to `_extract_results_by_entity()`
  - [x] 4.3 Add `"variable_periodicities"` and `"calculation_methods"` to result metadata as two separate `dict[str, str]` entries. Example for a mixed-periodicity compute: `"variable_periodicities": {"salaire_net": "month", "irpp": "year"}` and `"calculation_methods": {"salaire_net": "calculate_add", "irpp": "calculate"}`
  - [x] 4.4 Unit tests: verify metadata populated correctly in compute() result

- [x] Task 5: Add period validation (AC: #3)
  - [x] 5.1 Add validation as the FIRST operation in `compute()`, before `_get_tax_benefit_system()` or any TBS queries: period must be a positive integer in range [1000, 9999] (4-digit year; this is OpenFisca's practical supported temporal range — sub-period summation via `calculate_add()` is undefined outside plausible year values)
  - [x] 5.2 Raise `ApiMappingError` with summary "Invalid period", reason showing actual value, fix showing expected format
  - [x] 5.3 Unit tests: invalid periods (0, -1, 99, 99999) raise `ApiMappingError`; valid periods (2024, 2025) pass

- [x] Task 6: Verify backward compatibility (AC: #4)
  - [x] 6.1 Run existing unit tests in `test_openfisca_api_adapter.py` — ensure all pass unchanged
  - [x] 6.2 Run existing integration tests in `test_openfisca_integration.py` — note: any Story 9.2 integration test using `salaire_net` (a monthly variable) that is already failing with `ValueError: Period mismatch` is a pre-existing failure this story fixes as a side-effect (Story 9.2 added the test before the dispatch fix existed); Story 9.3 is expected to make it green; verify all other pre-existing integration tests remain green
  - [ ] 6.3 Verify `MockAdapter` still produces valid `ComputationResult` (no new required fields)
  - [x] 6.4 Verify `ComputationStep` in orchestrator still works (`result.output_fields.num_rows`)

- [x] Task 7: Integration tests with real OpenFisca-France (AC: #1, #2, #6)
  - [x] 7.1 Test: `salaire_net` (MONTH) with yearly period → verify `calculate_add()` is used and returns correct yearly sum. Since real `Simulation` objects cannot be mock-asserted, verify dispatch via metadata: `assert result.metadata["calculation_methods"]["salaire_net"] == "calculate_add"`, and verify value correctness: `assert 20000 < result.entity_tables["individus"].column("salaire_net")[0].as_py() < 30000`
  - [x] 7.2 Test: `impot_revenu_restant_a_payer` (YEAR) with yearly period → verify `calculate()` is used (unchanged)
  - [x] 7.3 Test: mixed periodicity output variables in single `compute()` call → verify correct method per variable
  - [x] 7.4 Test: `adapter.compute()` end-to-end with monthly output variable produces correct values
  - [x] 7.5 Test: verify `variable_periodicities` metadata in integration test result
  - [x] 7.6 Mark integration tests with `@pytest.mark.integration`

- [x] Task 8: Run quality gates (all ACs)
  - [x] 8.1 `uv run ruff check src/ tests/`
  - [x] 8.2 `uv run mypy src/`
  - [x] 8.3 `uv run pytest tests/computation/ tests/orchestrator/`

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
| `tests/computation/test_openfisca_api_adapter.py` | Three required changes: (1) update `_make_mock_tbs()` to add `var_mock.definition_period = "year"` in the variable-building loop; (2) update existing `TestExtractResultsByEntity` tests (3 methods) to pass new `variable_periodicities` argument; (3) add new test classes for periodicity detection, calculation dispatch, and period validation |
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

**Code Review Synthesis (2026-03-01) — applied fixes:**
- Added `from typing import Any` to `test_openfisca_api_adapter.py` imports (mypy strict compliance; `Any` was used at lines 62, 128 without being imported)
- Corrected misleading comment in `_make_mock_tbs()` — the original comment claimed that a MagicMock definition_period would cause dispatch to `calculate_add()`; in fact it causes `ApiMappingError("Unexpected periodicity")` from `_resolve_variable_periodicities()` since the MagicMock string repr is not in `_VALID_PERIODICITIES`
- Added `test_period_validation_precedes_tbs_loading` to `TestPeriodValidation` — verifies AC-3's "FIRST check" ordering constraint by asserting TBS remains `None` after an invalid-period error (previous tests pre-loaded the TBS so the constraint was untested)
- Removed dead SimulationBuilder mock setup from `test_compute_entity_detection_error` — the error fires in `_resolve_variable_entities()` before `_build_simulation()` is ever called; the mock_builder_instance/mock_simulation setup was unreachable
- Added `test_empty_output_variables_raises_error` to `TestOutputVariableValidation` — tests the `__init__` guard for empty `output_variables` tuple (guard existed but was untested)
- Extracted `_periodicity_to_method_name(periodicity: str) -> str` module-level helper in `openfisca_api_adapter.py` — eliminates DRY violation where the `_CALCULATE_ADD_PERIODICITIES` membership check was duplicated between `_calculate_variable()` and the `calculation_methods` metadata dict comprehension in `compute()`
- **False positive (context artifact):** Reviewer A flagged `test_openfisca_integration.py` as having broken imports, duplicate classes, and truncated methods. The actual file on disk is clean — the corrupted rendering was an XML embedding artifact in the review context, not the real file

### File List

- `src/reformlab/computation/openfisca_api_adapter.py` — modify (add `_resolve_variable_periodicities()`, `_calculate_variable()`, refactor `_extract_results_by_entity()`, add period validation)
- `tests/computation/test_openfisca_api_adapter.py` — modify (add periodicity unit tests, extend mock TBS with `definition_period`)
- `tests/computation/test_openfisca_integration.py` — modify (add monthly variable integration tests)

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
<file id="6ee5fa3d" path="_bmad-output/implementation-artifacts/9-5-openfisca-france-reference-test-suite.md" label="STORY FILE"><![CDATA[

# Story 9.5: OpenFisca-France Reference Test Suite

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **platform developer maintaining the OpenFisca adapter**,
I want a comprehensive reference test suite that validates adapter output against known French tax-benefit values across diverse household compositions and income levels,
so that regressions are detected immediately when OpenFisca-France is upgraded, and the adapter's correctness is continuously validated in CI.

## Context & Motivation

The adapter pipeline is now feature-complete for French tax-benefit integration:
- **Story 9.2** added multi-entity output array handling (per-entity tables for individu, foyer_fiscal, menage)
- **Story 9.3** added periodicity-aware calculation dispatch (monthly → `calculate_add`, yearly → `calculate`)
- **Story 9.4** added 4-entity PopulationData format with membership columns

However, the existing integration tests are **feature-validation tests** — they prove that each story's implementation works. What's missing is a **systematic reference test suite** that:

1. **Covers the French tax-benefit model systematically** — not just a few ad-hoc income levels, but a structured set of scenarios covering the progressive tax bracket structure, family quotient, and multi-entity outputs.
2. **Tests through `adapter.compute()` end-to-end** — many existing tests use `_build_simulation()` directly (bypassing the adapter's entity dict construction, periodicity resolution, and result extraction). The reference suite must validate the full pipeline.
3. **Cross-validates 4-entity format** — the membership column path (Story 9.4) must produce identical results to the legacy path for equivalent populations. This cross-validation is the definitive proof that the 4-entity format works correctly.
4. **Provides regression detection scaffolding** — when OpenFisca-France is upgraded from 175.x to a new major version, the reference suite should be the first thing that breaks, with clear failure messages showing expected vs actual values and the OpenFisca version.

**Source:** Spike 8-1 findings, recommended follow-up #5: "Production integration test suite — Expand from this spike's 16 tests to a broader regression suite covering more French tax-benefit variables." [Source: `_bmad-output/implementation-artifacts/spike-findings-8-1-openfisca-integration.md`, line 108]

**Epic 9 AC:** "A reference test suite validates adapter output against known French tax-benefit values." [Source: `_bmad-output/planning-artifacts/epics.md`, Epic 9 acceptance criteria]

## Acceptance Criteria

1. **AC-1: Known-value validation** — Given a set of known French tax-benefit scenarios covering at least: (a) single persons at 3+ income levels spanning different tax brackets, (b) a married couple with joint taxation, (c) a family with children, when run through `adapter.compute()`, then computed values match reference values within the documented `ABSOLUTE_ERROR_MARGIN = 0.5` EUR tolerance.

2. **AC-2: CI integration** — Given the reference test suite, when run in CI with `uv run pytest tests/computation/test_openfisca_integration.py -m integration`, then all tests pass and tolerance thresholds are documented as class-level constants with docstring explanations.

3. **AC-3: Regression detection** — Given the reference test suite, when a new OpenFisca-France version changes a tax computation value, then the test failure message includes: (a) the expected reference value, (b) the actual computed value, (c) the tolerance, and (d) the pinned OpenFisca-France version that produced the reference value — providing all information needed to decide whether the change is expected (parameter update) or a regression.

4. **AC-4: Full-pipeline coverage** — Given all reference scenarios, when tested, then each scenario is exercised through `adapter.compute()` (not `_build_simulation()` directly) — validating the full adapter pipeline including entity dict construction, periodicity resolution, calculation dispatch, and per-entity result extraction.

5. **AC-5: 4-entity format cross-validation** — Given at least one multi-person reference scenario (e.g., married couple), when tested through both the 4-entity format (membership columns) and the legacy format (adapter auto-creation or hand-built entity dicts), then results match within tolerance — cross-validating Story 9.4's implementation against the existing proven path.

6. **AC-6: Multi-entity output validation** — Given at least one reference scenario that requests output variables from multiple entities (e.g., `salaire_net` from individu + `impot_revenu_restant_a_payer` from foyer_fiscal + `revenu_disponible` from menage), when run through `adapter.compute()`, then `entity_tables` contains per-entity tables with correct array lengths and reasonable values.

7. **AC-7: Existing tests unbroken** — Given all pre-existing integration tests in `test_openfisca_integration.py`, when the reference test suite is added, then no existing tests are modified or broken.

## Tasks / Subtasks

- [ ] Task 1: Define reference test scenarios and compute expected values (AC: #1, #3)
  - [ ] 1.1 Create a script or notebook cell (NOT committed) to compute reference values using direct OpenFisca-France calls. Pin all reference values against openfisca-france 175.x / openfisca-core 44.2.2. Document the exact OpenFisca-France version in the test class docstring
  - [ ] 1.2 Compute reference values for single-person scenarios at multiple income levels. Use `salaire_imposable` as the input variable (matching openfisca-france's own test format). Scenarios:
      - **Zero income:** `salaire_imposable=0` → `irpp=0.0` (no tax)
      - **Low income (near SMIC):** `salaire_imposable=15000` → expected irpp (decote may apply)
      - **Mid income:** `salaire_imposable=30000` → known reference (existing tests use ~-1200 for `salaire_de_base=30000`, but `salaire_imposable` is a different variable — recompute)
      - **Upper bracket:** `salaire_imposable=75000` → known reference
      - **High income:** `salaire_imposable=100000` → known reference
  - [ ] 1.3 Compute reference values for family scenarios:
      - **Married couple, dual income:** `salaire_imposable` 40000+30000 → expected joint irpp
      - **Family with 1 child:** 2 parents + 1 enfant, demonstrate `quotient_familial` 2.5 parts advantage
      - **Family with 2 children:** 2 parents + 2 enfants, demonstrate 3 parts
  - [ ] 1.4 Compute reference values for multi-entity output:
      - **Single person multi-entity:** `salaire_net` (individu, monthly) + `impot_revenu_restant_a_payer` (foyer_fiscal, yearly) + `revenu_disponible` (menage, yearly) for a 30k earner
  - [ ] 1.5 Record all reference values in a structured format within the test class docstring, including the exact OpenFisca-France version used, the date computed, and the tolerance

- [ ] Task 2: Implement single-person income tax reference cases via `adapter.compute()` (AC: #1, #3, #4)
  - [ ] 2.1 Create a new test class `TestAdapterReferenceSinglePerson` in `tests/computation/test_openfisca_integration.py`. Docstring must document: pinned OpenFisca-France version, date of reference value computation, tolerance, and purpose (regression detection)
  - [ ] 2.2 Add class attribute `ABSOLUTE_ERROR_MARGIN = 0.5` and `REFERENCE_OPENFISCA_FRANCE_VERSION = "175.0.18"` (or current installed version)
  - [ ] 2.3 For each single-person scenario, create a test method that: (a) constructs a `PopulationData` with a single individu table containing `salaire_imposable`, (b) calls `adapter.compute(population, empty_policy, 2024)`, (c) asserts the `impot_revenu_restant_a_payer` value matches the reference within tolerance, (d) uses a clear assertion message: `f"Expected {expected}, got {actual} (tolerance ±{margin}, ref: OpenFisca-France {version})"`
  - [ ] 2.4 Add a test for **progressive tax monotonicity**: given the full set of reference income levels, assert that tax increases (becomes more negative) monotonically with income. This is a structural test that catches any reference value errors
  - [ ] 2.5 Mark all tests with `@pytest.mark.integration`

- [ ] Task 3: Implement family reference cases via `adapter.compute()` with 4-entity format (AC: #1, #3, #4, #5)
  - [ ] 3.1 Create a new test class `TestAdapterReferenceFamilies` in `tests/computation/test_openfisca_integration.py`. Same docstring and class attributes as Task 2
  - [ ] 3.2 **Married couple test:** construct a `PopulationData` with membership columns (famille_id, famille_role, foyer_fiscal_id, foyer_fiscal_role, menage_id, menage_role) for 2 persons in 1 foyer_fiscal. Use `salaire_imposable` as input. Assert joint irpp matches reference value. ⚠️ This tests the FULL 4-entity pipeline through `adapter.compute()`
  - [ ] 3.3 **Family with child test:** 3 persons (2 parents + 1 enfant with age=10) with membership columns expressing correct roles in all 3 group entities. The child is `personnes_a_charge` in foyer_fiscal, `enfants` in famille and menage. Assert joint irpp with 2.5-part quotient
  - [ ] 3.4 **Family with 2 children test:** 4 persons (2 parents + 2 enfants). Assert quotient familial advantage: family pays less tax than a couple with same total income
  - [ ] 3.5 **Quotient familial structural test:** assert that a married couple with children pays LESS tax than a couple without children (when total income is the same). This is a structural invariant of French tax law

- [ ] Task 4: Implement 4-entity format cross-validation (AC: #5)
  - [ ] 4.1 Create a test class `TestFourEntityCrossValidation` (or add to an existing appropriate class)
  - [ ] 4.2 **Cross-validation test:** for the married couple scenario, run `adapter.compute()` twice: once with the 4-entity format (membership columns on person table) and once with a single-person-per-household setup (auto-created entities, legacy path). For the single-person case, run 2 separate single-person computes and compare the SUM of individual irpp values to the couple's joint irpp. Document that the difference demonstrates the quotient familial benefit (couple pays LESS than sum of singles)
  - [ ] 4.3 **Alternative cross-validation**: For a SINGLE person, run `adapter.compute()` both with and without membership columns. Assert results are identical within tolerance. This directly validates that the 4-entity path produces the same result as the auto-creation path for the simplest case
  - [ ] 4.4 ⚠️ Do NOT call `_build_simulation()` directly in cross-validation tests — the purpose is to validate the adapter pipeline, not to replicate the existing `TestOpenFiscaFranceReferenceCases` tests (which already use `_build_simulation()`)

- [ ] Task 5: Implement multi-entity output reference cases (AC: #4, #6)
  - [ ] 5.1 Create a new test class `TestAdapterReferenceMultiEntity`
  - [ ] 5.2 **Single-person multi-entity test:** Use adapter with `output_variables=("salaire_net", "impot_revenu_restant_a_payer", "revenu_disponible")`. Construct a single-person population (30k salary). Assert:
      - `entity_tables` contains 3 entity keys: `"individus"`, `"foyers_fiscaux"`, `"menages"`
      - `entity_tables["individus"].num_rows == 1` (1 person)
      - `entity_tables["foyers_fiscaux"].num_rows == 1` (1 foyer)
      - `entity_tables["menages"].num_rows == 1` (1 menage)
      - `salaire_net > 0` and in reasonable range (20k-30k for 30k gross)
      - `impot_revenu_restant_a_payer < 0` (tax owed)
      - `revenu_disponible > 0` (positive disposable income)
      - Metadata `calculation_methods` shows `"salaire_net": "calculate_add"` and `"impot_revenu_restant_a_payer": "calculate"`
  - [ ] 5.3 **Married couple multi-entity test:** Use adapter with same 3 output variables. Construct couple via 4-entity format. Assert:
      - `entity_tables["individus"].num_rows == 2` (2 persons)
      - `entity_tables["foyers_fiscaux"].num_rows == 1` (1 foyer — joint filing)
      - `entity_tables["menages"].num_rows == 1` (1 menage)
      - Correct per-entity variable assignment (salaire_net on individus, irpp on foyers_fiscaux, revenu_disponible on menages)
  - [ ] 5.4 **Two independent households multi-entity test:** 2 persons in separate foyers/menages. Assert all entity tables have 2 rows

- [ ] Task 6: Add regression detection metadata (AC: #3)
  - [ ] 6.1 Add a shared module-scope fixture `reference_adapter` with the multi-entity output variable configuration, cached like the existing `adapter` and `multi_entity_adapter` fixtures
  - [ ] 6.2 Add a test `test_openfisca_france_version_documented` that asserts `adapter.version()` returns a version starting with `"44."` (openfisca-core 44.x). If the core version changes, this test forces explicit review of all reference values. Document in the docstring that this test is intentionally version-pinned for regression detection
  - [ ] 6.3 Ensure ALL assertion messages in reference tests include: (a) expected value, (b) actual value, (c) tolerance, (d) a note pointing to the reference version. Use a consistent format:
      ```python
      assert abs(float(actual) - expected) <= self.ABSOLUTE_ERROR_MARGIN, (
          f"Expected {expected}, got {actual} "
          f"(tolerance ±{self.ABSOLUTE_ERROR_MARGIN}, "
          f"ref: OpenFisca-France {self.REFERENCE_OPENFISCA_FRANCE_VERSION})"
      )
      ```
  - [ ] 6.4 Add a class-level constant `REFERENCE_DATE = "2026-03-01"` documenting when reference values were computed. This helps during version upgrades to understand how stale the reference values are

- [ ] Task 7: Verify backward compatibility (AC: #7)
  - [ ] 7.1 Run ALL existing integration tests unchanged: `uv run pytest tests/computation/test_openfisca_integration.py -m integration`
  - [ ] 7.2 Verify no imports added or removed that could affect other test classes
  - [ ] 7.3 Verify the existing `TestOpenFiscaFranceReferenceCases` class is NOT modified — it remains the direct-simulation reference. Story 9.5 adds the adapter-pipeline reference

- [ ] Task 8: Run quality gates (all ACs)
  - [ ] 8.1 `uv run ruff check src/ tests/`
  - [ ] 8.2 `uv run mypy src/`
  - [ ] 8.3 `uv run pytest tests/computation/ -m integration` (all integration tests pass)
  - [ ] 8.4 `uv run pytest tests/computation/ -m "not integration"` (all unit tests still pass)
  - [ ] 8.5 `uv run pytest tests/orchestrator/` (no orchestrator regressions)

## Dev Notes

### This is a TEST-ONLY Story

**No adapter code changes.** Story 9.5 adds integration tests to `tests/computation/test_openfisca_integration.py` only. The adapter pipeline was completed in Stories 9.2-9.4. This story validates correctness systematically.

### Relationship to Existing Tests

The existing integration test file (`test_openfisca_integration.py`) already contains:

| Test Class | Stories | Approach | Count |
|---|---|---|---|
| `TestTaxBenefitSystemLoading` | 8.1 | Direct TBS access | 3 |
| `TestAdapterComputeEndToEnd` | 8.1 | `adapter.compute()` | 3 |
| `TestMultiEntityPopulation` | 8.1 | `_build_simulation()` direct | 3 |
| `TestVariableMappingRoundTrip` | 8.1 | Direct simulation + mapping | 2 |
| `TestOutputQualityValidation` | 8.1 | `adapter.compute()` + validation | 1 |
| `TestKnownValueBenchmark` | 8.1 | Direct simulation | 2 |
| `TestAdapterPluralKeyFix` | 8.1 | `adapter.compute()` + direct | 3 |
| `TestOpenFiscaFranceReferenceCases` | 8.1 | `_build_simulation()` direct | 4 |
| `TestMultiEntityOutputArrays` | 9.2 | Mixed (adapter + direct) | 4 |
| `TestVariablePeriodicityHandling` | 9.3 | `adapter.compute()` | 5 |
| `TestFourEntityPopulationFormat` | 9.4 | `adapter.compute()` | 6 |

**Story 9.5 adds:** Systematic reference tests that go through `adapter.compute()` end-to-end with pinned expected values and regression-detection metadata. The new test classes complement (not replace) the existing ones.

### Key Difference: `_build_simulation()` vs `adapter.compute()`

**Existing `TestOpenFiscaFranceReferenceCases` uses `_build_simulation()` directly.** This bypasses the adapter's `_population_to_entity_dict()`, periodicity resolution, and entity-aware result extraction. It validates OpenFisca-France itself, not the adapter pipeline.

**Story 9.5 tests MUST use `adapter.compute()`.** This validates the full stack:
1. `_validate_period()` — period check
2. `_get_tax_benefit_system()` — TBS loading
3. `_validate_output_variables()` — variable validation
4. `_resolve_variable_entities()` — entity grouping
5. `_resolve_variable_periodicities()` — periodicity detection
6. `_build_simulation()` → `_population_to_entity_dict()` — entity dict construction (including 4-entity membership columns)
7. `_extract_results_by_entity()` → `_calculate_variable()` — periodicity-aware calculation dispatch
8. `_select_primary_output()` — backward-compatible output selection

### Input Variable Choice: `salaire_imposable` vs `salaire_de_base`

**Use `salaire_imposable` for income tax reference tests** (matching openfisca-france's own test format and the existing `TestOpenFiscaFranceReferenceCases`). This is the taxable salary — the direct input to the income tax computation. It removes noise from social contribution deductions.

**Use `salaire_de_base` for multi-entity tests** where you also want `salaire_net` as output (since `salaire_net` is derived from `salaire_de_base` through social contribution formulas).

### Reference Value Computation

All reference values must be computed using the installed OpenFisca-France version (currently 175.0.18 on openfisca-core 44.2.2). Use the existing `_build_simulation()` helper or a temporary notebook to compute and pin values.

**⚠️ Reference values are NOT pulled from external publications.** They are pinned against the specific OpenFisca-France version installed in the project. The purpose is regression detection on version upgrades, not validation against government publications (which may use different rounding rules or parameter vintages).

### French Tax System Concepts for Test Design

**Quotient familial (family quotient):**
- Single person = 1 part
- Married couple = 2 parts
- +0.5 part per child for first two children
- +1 part per child from the third child
- Income is divided by number of parts, tax is computed on per-part income, then multiplied back
- Couples with children pay less tax than couples without children at the same total income

**Progressive tax brackets (barème 2024):**
The French income tax uses progressive marginal rates. Key thresholds change annually. With `salaire_imposable`:
- Low income (<~15k) → near zero tax (decote mechanism reduces very small tax amounts to zero)
- Mid income (30k-50k) → moderate tax (marginal rates ~11-30%)
- High income (75k+) → significant tax (marginal rate 30-41%)
- Very high income (100k+) → top bracket (41%+ marginal rate)

**Decote:** A reduction mechanism that eliminates or reduces very small tax amounts. Applies when raw computed tax is below a threshold (~1,929 EUR for singles in 2024). This makes the zero→positive tax transition non-linear.

### Adapter Fixture Configuration for Multi-Entity Tests

Story 9.5 needs an adapter configured with multiple output variables spanning different entities and periodicities:

```python
@pytest.fixture(scope="module")
def reference_adapter() -> OpenFiscaApiAdapter:
    """Adapter for reference test suite with multi-entity, mixed-periodicity output."""
    return OpenFiscaApiAdapter(
        country_package="openfisca_france",
        output_variables=(
            "salaire_net",                      # individu, MONTH → calculate_add
            "impot_revenu_restant_a_payer",     # foyer_fiscal, YEAR → calculate
            "revenu_disponible",                # menage, YEAR → calculate
        ),
    )
```

This overlaps with the existing `multi_entity_adapter` fixture but should be a separate fixture for test isolation (Story 9.5 tests should not depend on Story 9.2 fixture naming).

### 4-Entity PopulationData Construction for Family Scenarios

**Married couple (2 persons, 1 group per entity):**
```python
PopulationData(
    tables={
        "individu": pa.table({
            "salaire_imposable": pa.array([40000.0, 30000.0]),
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

**Family with 1 child (3 persons, 1 group per entity):**
```python
PopulationData(
    tables={
        "individu": pa.table({
            "salaire_imposable": pa.array([40000.0, 30000.0, 0.0]),
            "age": pa.array([40, 38, 10]),  # age needed for child
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

### Role Reference Table (from Story 9.4 Dev Notes)

| Entity | Role | Dict key (`plural or key`) | `role.max` |
|---|---|---|---|
| famille | Parent | `"parents"` | 2 |
| famille | Child | `"enfants"` | None |
| foyer_fiscal | Declarant | `"declarants"` | 2 |
| foyer_fiscal | Dependent | `"personnes_a_charge"` | None |
| menage | Ref person | `"personne_de_reference"` | 1 |
| menage | Spouse | `"conjoint"` | 1 |
| menage | Child | `"enfants"` | None |
| menage | Other | `"autres"` | None |

### Test Naming Convention

Follow the existing pattern in the file:
```python
@pytest.mark.integration
class TestAdapterReferenceSinglePerson:
    """Story 9.5: Single-person income tax reference cases via adapter.compute().

    Reference values computed against OpenFisca-France 175.0.18,
    openfisca-core 44.2.2, on 2026-03-01. Tolerance ±0.5 EUR.
    """

    ABSOLUTE_ERROR_MARGIN = 0.5
    REFERENCE_OPENFISCA_FRANCE_VERSION = "175.0.18"
    REFERENCE_DATE = "2026-03-01"

    def test_zero_income(self, reference_irpp_adapter: OpenFiscaApiAdapter) -> None:
        """Reference: zero income → zero tax."""
        ...
```

### What This Story Does NOT Cover

- **Modifying adapter code** — this is test-only
- **Adding new output variables** to the adapter
- **Testing non-French country packages** — France-specific only
- **Performance benchmarks** — covered by Story 8-2
- **Sub-yearly period support** — `compute()` takes `period: int` (year only)
- **Person-level broadcasting of group values** — out of epic 9 scope
- **Validation against government publications** — reference values are pinned against OpenFisca-France, not external sources

### Edge Cases to Handle

1. **Zero income → zero IRPP** — the simplest case, but validates the adapter handles it correctly (no division by zero, no negative tax for zero income)

2. **Very low income with decote** — French decote mechanism reduces small tax amounts to zero. The transition from 0 tax to positive tax is non-linear. Test at ~15k `salaire_imposable` where decote applies

3. **Child with age specification** — OpenFisca-France uses `age` (monthly variable) for child-related benefits. Must provide age on the person table. Use `"age": pa.array([...])` with monthly periodicity consideration (the adapter wraps with yearly period, OpenFisca handles the month internally for age)

4. **Children affecting tax computation** — In French tax, children add "demi-parts" to the quotient familial, but the benefit is capped (plafonnement du quotient familial). Very high incomes may see limited benefit from additional children

### Project Structure Notes

- Source layout: `src/reformlab/` is the installable package
- Tests mirror source: `tests/computation/` matches `src/reformlab/computation/`
- Each test subdirectory has `__init__.py` and `conftest.py`
- Class-based test grouping with AC references in docstrings
- Integration tests require `openfisca-france` optional dependency: `uv sync --extra openfisca`
- Run integration tests: `uv run pytest tests/computation/ -m integration`
- Run unit tests: `uv run pytest tests/computation/ -m "not integration"`
- Quality gates: `uv run ruff check src/ tests/` and `uv run mypy src/`

### References

- [Source: `_bmad-output/implementation-artifacts/spike-findings-8-1-openfisca-integration.md` — Follow-up #5: "Production integration test suite", line 108]
- [Source: `_bmad-output/planning-artifacts/epics.md` — Epic 9 acceptance criteria: "A reference test suite validates adapter output against known French tax-benefit values"]
- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 9.5 acceptance criteria, lines in Epic 9 section]
- [Source: `tests/computation/test_openfisca_integration.py` — `TestOpenFiscaFranceReferenceCases` class, lines 565-652; existing reference value pattern with ABSOLUTE_ERROR_MARGIN = 0.5]
- [Source: `tests/computation/test_openfisca_integration.py` — `_build_simulation()` helper, lines 88-118; `_build_entities_dict()` helper, lines 72-87]
- [Source: `tests/computation/test_openfisca_integration.py` — `TestFourEntityPopulationFormat` class, lines 1068-1295; 4-entity format integration tests from Story 9.4]
- [Source: `tests/computation/test_openfisca_integration.py` — Module-scoped fixtures `tbs()`, `adapter()`, `multi_entity_adapter()`, `periodicity_adapter()`]
- [Source: `src/reformlab/computation/openfisca_api_adapter.py` — `compute()` method pipeline: validate_period → TBS → validate_output → resolve_entities → resolve_periodicities → build_simulation → extract_results]
- [Source: `src/reformlab/computation/openfisca_api_adapter.py` — `_population_to_entity_dict()` with 4-entity mode, lines 499-900+]
- [Source: `_bmad-output/implementation-artifacts/9-4-define-population-data-4-entity-format.md` — Role reference table, OpenFisca-France role definitions, 4-entity format specification]
- [Source: `_bmad-output/implementation-artifacts/9-3-add-variable-periodicity-handling.md` — Periodicity dispatch table: month→calculate_add, year→calculate, eternity→calculate]
- [Source: `_bmad-output/implementation-artifacts/9-2-handle-multi-entity-output-arrays.md` — Multi-entity result extraction pattern, entity_tables dict structure]
- [Source: `_bmad-output/project-context.md` — Testing rules: "Class-based test grouping", "Direct assertions", "@pytest.mark.integration"]
- [Source: `.venv/lib/python3.13/site-packages/openfisca_france/parameters/impot_revenu/bareme_ir_depuis_1945/` — French income tax bracket parameters]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (via create-story workflow)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed — comprehensive developer guide created
- All 3 acceptance criteria from epics file expanded to 7 ACs covering: known-value validation, CI integration, regression detection, full-pipeline coverage, 4-entity cross-validation, multi-entity output validation, and backward compatibility
- Spike 8-1 findings fully integrated: follow-up #5 ("Production integration test suite") is the direct motivation
- Existing test infrastructure comprehensively mapped: 36+ integration tests across 11 test classes in test_openfisca_integration.py
- Critical distinction identified: existing `TestOpenFiscaFranceReferenceCases` uses `_build_simulation()` directly (validating OpenFisca-France itself), while Story 9.5 must use `adapter.compute()` (validating the full adapter pipeline)
- 4-entity PopulationData format documented for family scenarios with correct role assignments for children (enfants in famille, personnes_a_charge in foyer_fiscal, enfants in menage)
- French tax system concepts documented for test design: quotient familial, progressive brackets, decote mechanism, plafonnement
- Regression detection scaffolding designed: version pinning, reference date, structured assertion messages with expected/actual/tolerance/version
- Cross-validation strategy defined: 4-entity format vs legacy path for equivalent populations
- Edge cases documented: zero income, decote threshold, child age specification, quotient familial plafonnement

### File List

- `tests/computation/test_openfisca_integration.py` — modify (add `TestAdapterReferenceSinglePerson`, `TestAdapterReferenceFamilies`, `TestFourEntityCrossValidation`, `TestAdapterReferenceMultiEntity` test classes; add `reference_adapter` and `reference_irpp_adapter` module-scope fixtures)

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
<var name="story_file" file_id="6ee5fa3d">embedded in prompt, file id: 6ee5fa3d</var>
<var name="story_id">9.5</var>
<var name="story_key">9-5-openfisca-france-reference-test-suite</var>
<var name="story_num">5</var>
<var name="story_title">openfisca-france-reference-test-suite</var>

<var name="timestamp">20260301_230858</var>
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
      - Story ID: 9.5
      - Story Key: 9-5-openfisca-france-reference-test-suite
      - Title: openfisca-france-reference-test-suite
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
      <check if="5 &gt; 1">
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
      <check if="5 == 1">
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

    <action>Load the story file: /Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/9-5-openfisca-france-reference-test-suite.md</action>

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

**Validation Report:** /Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/story-validations/validation-report-9-5-openfisca-france-reference-test-suite-2026-03-01.md
**Story File:** /Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/9-5-openfisca-france-reference-test-suite.md

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
1. ✅ Review the updated story file: `/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/9-5-openfisca-france-reference-test-suite.md`
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