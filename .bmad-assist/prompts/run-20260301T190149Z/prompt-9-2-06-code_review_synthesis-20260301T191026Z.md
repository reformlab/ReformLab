<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 9 -->
<!-- Story: 2 -->
<!-- Phase: code-review-synthesis -->
<!-- Timestamp: 20260301T191026Z -->
<compiled-workflow>
<mission><![CDATA[

Master Code Review Synthesis: Story 9.2

You are synthesizing 2 independent code review findings.

Your mission:
1. VERIFY each issue raised by reviewers
   - Cross-reference with project_context.md (ground truth)
   - Cross-reference with git diff and source files
   - Identify false positives (issues that aren't real problems)
   - Confirm valid issues with evidence

2. PRIORITIZE real issues by severity
   - Critical: Security vulnerabilities, data corruption risks
   - High: Bugs, logic errors, missing error handling
   - Medium: Code quality issues, performance concerns
   - Low: Style issues, minor improvements

3. SYNTHESIZE findings
   - Merge duplicate issues from different reviewers
   - Note reviewer consensus (if 3+ agree, high confidence)
   - Highlight unique insights from individual reviewers

4. APPLY source code fixes
   - You have WRITE PERMISSION to modify SOURCE CODE files
   - CRITICAL: Before using Edit tool, ALWAYS Read the target file first
   - Use EXACT content from Read tool output as old_string, NOT content from this prompt
   - If Read output is truncated, use offset/limit parameters to locate the target section
   - Apply fixes for verified issues
   - Do NOT modify the story file (only Dev Agent Record if needed)
   - Document what you changed and why

Output format:
## Synthesis Summary
## Issues Verified (by severity)
## Issues Dismissed (false positives with reasoning)
## Source Code Fixes Applied

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

- [ ] Task 1: Determine variable-to-entity mapping from TBS (AC: #1, #2, #5)
  - [ ] 1.1 Add `_resolve_variable_entities()` method that queries `tbs.variables[var_name].entity` to determine which entity each output variable belongs to
  - [ ] 1.2 Group output variables by entity (e.g., `{"individu": ["salaire_net"], "foyer_fiscal": ["impot_revenu_restant_a_payer"]}`)
  - [ ] 1.3 Handle edge case where variable entity cannot be resolved — raise `ApiMappingError` with actionable message
  - [ ] 1.4 Unit tests with mock TBS: verify grouping logic, error on unknown variable entity

- [ ] Task 2: Refactor `_extract_results()` to produce per-entity tables (AC: #1, #2, #3)
  - [ ] 2.1 Replace single `pa.Table` construction with per-entity extraction loop
  - [ ] 2.2 For each entity group, call `simulation.calculate()` for its variables and build a `pa.Table` per entity
  - [ ] 2.3 Store results as `dict[str, pa.Table]` keyed by entity plural name
  - [ ] 2.4 Unit tests: verify correct array lengths per entity, verify table column names

- [ ] Task 3: Evolve `ComputationResult` to support multi-entity outputs (AC: #1, #3, #4)
  - [ ] 3.1 Add `entity_tables: dict[str, pa.Table]` field to `ComputationResult` (default empty dict for backward compatibility)
  - [ ] 3.2 Keep `output_fields: pa.Table` as the primary/default output for backward compatibility — when all variables belong to one entity, `output_fields` is that entity's table
  - [ ] 3.3 When variables span multiple entities, `output_fields` contains the person-entity table (or the first entity's table if no person entity), and `entity_tables` contains all per-entity tables
  - [ ] 3.4 Add metadata entry `"output_entities"` listing which entities have tables
  - [ ] 3.5 Update `ComputationResult` type stub (`.pyi` file)
  - [ ] 3.6 Unit tests: verify backward compatibility (existing code accessing `output_fields` still works), verify `entity_tables` populated correctly

- [ ] Task 4: Update `OpenFiscaApiAdapter.compute()` to wire new extraction (AC: #1, #2, #3)
  - [ ] 4.1 Pass TBS to `_extract_results()` so it can resolve variable entities
  - [ ] 4.2 Update `compute()` return to populate both `output_fields` and `entity_tables`
  - [ ] 4.3 Update metadata with `"output_entities"` and per-entity row counts
  - [ ] 4.4 Unit tests with mock TBS and mock simulation

- [ ] Task 5: Update downstream consumers for backward compatibility (AC: #4)
  - [ ] 5.1 Verify `ComputationStep` in orchestrator still works (it accesses `result.output_fields.num_rows`)
  - [ ] 5.2 Verify `PanelOutput.from_orchestrator_result()` still works (it accesses `comp_result.output_fields`)
  - [ ] 5.3 Verify `MockAdapter` still produces valid `ComputationResult` objects
  - [ ] 5.4 Run full existing test suite to confirm no regressions

- [ ] Task 6: Integration tests with real OpenFisca-France (AC: #1, #2, #3)
  - [ ] 6.1 Test: married couple (2 persons, 1 foyer, 1 menage) with mixed-entity output variables — verify separate tables
  - [ ] 6.2 Test: single-entity variables only — verify backward-compatible single table
  - [ ] 6.3 Test: verify array lengths match entity instance counts
  - [ ] 6.4 Mark integration tests with `@pytest.mark.integration` (requires `openfisca-france` installed)

- [ ] Task 7: Run quality gates (all ACs)
  - [ ] 7.1 `uv run ruff check src/ tests/`
  - [ ] 7.2 `uv run mypy src/`
  - [ ] 7.3 `uv run pytest tests/computation/ tests/orchestrator/`

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

### File List

- `src/reformlab/computation/types.py` — modify (add `entity_tables` field)
- `src/reformlab/computation/types.pyi` — modify (update stub)
- `src/reformlab/computation/openfisca_api_adapter.py` — modify (refactor `_extract_results`, add `_resolve_variable_entities`)
- `tests/computation/test_openfisca_api_adapter.py` — modify (add entity-aware extraction tests)
- `tests/computation/test_result.py` — modify (add `entity_tables` tests)
- `tests/computation/test_openfisca_integration.py` — modify (add multi-entity output integration tests)


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

        simulation = self._build_simulation(population, policy, period, tbs)

        # Story 9.2: Entity-aware result extraction
        vars_by_entity = self._resolve_variable_entities(tbs)
        entity_tables = self._extract_results_by_entity(
            simulation, period, vars_by_entity
        )

        # Determine primary output_fields table for backward compatibility:
        # - Single entity → that entity's table
        # - Multiple entities → person-entity table (or first entity's table)
        output_fields = self._select_primary_output(entity_tables, tbs)

        elapsed = time.monotonic() - start

        # Build output_entities metadata listing which entities have tables
        output_entities = sorted(entity_tables.keys())
        entity_row_counts = {
            entity: table.num_rows for entity, table in entity_tables.items()
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
            entity_tables=entity_tables if len(entity_tables) > 1 else {},
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
                # Fallback: try entity.key + "s" if plural is missing
                entity_key = getattr(entity, "key", None)
                if entity_key is None:
                    raise ApiMappingError(
                        summary="Cannot determine entity name for variable",
                        reason=(
                            f"Variable '{var_name}' entity has neither .plural "
                            f"nor .key attribute"
                        ),
                        fix=(
                            "This may indicate an incompatible OpenFisca version. "
                            "Check the OpenFisca compatibility matrix."
                        ),
                        invalid_names=(var_name,),
                        valid_names=tuple(sorted(tbs.variables.keys())),
                    )
                entity_plural = entity_key

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
<file id="5d4bf368" path="src/reformlab/computation/types.py" label="SOURCE CODE"><![CDATA[

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pyarrow as pa

OutputFields = pa.Table


@dataclass(frozen=True)
class PopulationData:
    """Wraps a population dataset with metadata.

    The underlying data is a PyArrow Table keyed by entity type
    (e.g. ``"individu"``, ``"menage"``).  A single-entity dataset
    can use the default ``"default"`` key.
    """

    tables: dict[str, pa.Table]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def row_count(self) -> int:
        """Total rows across all entity tables."""
        return sum(t.num_rows for t in self.tables.values())


@dataclass(frozen=True)
class PolicyConfig:
    """Scenario parameters for a single computation period."""

    parameters: dict[str, Any]
    name: str = ""
    description: str = ""


@dataclass(frozen=True)
class ComputationResult:
    """Result returned by a ComputationAdapter.compute() call.

    Attributes:
        output_fields: Mapped output data as a PyArrow Table. When all output
            variables belong to a single entity, this is that entity's table.
            When variables span multiple entities, this contains the person-entity
            table (primary entity).
        adapter_version: Version string of the adapter that produced the result.
        period: The computation period (e.g. year).
        metadata: Timing, row count, and other run-level information.
        entity_tables: Per-entity output tables keyed by entity plural name
            (e.g. ``"individus"``, ``"foyers_fiscaux"``). Empty dict when all
            outputs belong to a single entity (backward-compatible default).
            Story 9.2: Handle multi-entity output arrays.
    """

    output_fields: OutputFields
    adapter_version: str
    period: int
    metadata: dict[str, Any] = field(default_factory=dict)
    entity_tables: dict[str, pa.Table] = field(default_factory=dict)


]]></file>
<file id="d77c98a3" path="src/reformlab/computation/types.pyi" label="FILE"><![CDATA[

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeAlias

import pyarrow as pa

OutputFields: TypeAlias = pa.Table

@dataclass(frozen=True)
class PopulationData:
    tables: dict[str, pa.Table]
    metadata: dict[str, Any] = ...

    @property
    def row_count(self) -> int: ...

@dataclass(frozen=True)
class PolicyConfig:
    parameters: dict[str, Any]
    name: str = ...
    description: str = ...

@dataclass(frozen=True)
class ComputationResult:
    output_fields: OutputFields
    adapter_version: str
    period: int
    metadata: dict[str, Any] = ...
    entity_tables: dict[str, pa.Table] = ...


]]></file>
<file id="1d910d88" path="[Validator A]" label="VALIDATION OUTPUT"><![CDATA[

## 📊 Review Summary

| Category | Issues Found |
|----------|--------------|
| Story Governance / Process | 1 |
| Data Contract Bugs | 1 |
| Correctness / Crash Bugs | 1 |
| Validation Order | 1 |
| Comment/Code Mismatch | 1 |
| Test Coverage Gaps | 2 |
| Test Fragility | 2 |
| Mock Fidelity | 1 |
| **Total Issues** | **10** |

---

## Evidence Score Summary

| Severity | Finding | Source | Score |
|----------|---------|--------|-------|
| 🟠 IMPORTANT | Metadata `output_entities` reports entities that don't exist in `entity_tables` — data contract bug | `openfisca_api_adapter.py:101-120` | +1 |
| 🟠 IMPORTANT | `_select_primary_output` raises unhandled `StopIteration` on empty dict — crash with no diagnostic | `openfisca_api_adapter.py:510-521` | +1 |
| 🟠 IMPORTANT | Canonical married couple case never exercised through `adapter.compute()` — AC-2/AC-3 integration gap | `test_openfisca_integration.py` | +1 |
| 🟠 IMPORTANT | Story status "ready-for-dev", all 7 tasks unchecked `[ ]` — governance violation despite delivered code | `9-2-handle-multi-entity-output-arrays.md` | +1 |
| 🟡 MINOR | `_resolve_variable_entities` called AFTER `_build_simulation` — simulation built before entity validation | `openfisca_api_adapter.py:85-88` | +0.3 |
| 🟡 MINOR | Line 430 comment says "try entity.key + 's'" but line 446 does `entity_plural = entity_key` — code contradicts comment, fallback is silently wrong | `openfisca_api_adapter.py:430-446` | +0.3 |
| 🟡 MINOR | `test_compute_single_entity_backward_compatible` doesn't verify `metadata["output_entities"]` consistency — lying test masks bug #1 | `test_openfisca_api_adapter.py:897-922` | +0.3 |
| 🟡 MINOR | `test_multi_entity_without_person_returns_first` asserts dict-order-dependent result without documenting the dependency | `test_openfisca_api_adapter.py:876-891` | +0.3 |
| 🟡 MINOR | `_make_mock_tbs_with_entities` default entity_keys omits `famille` — 3-entity mock vs 4-entity real OpenFisca-France | `test_openfisca_api_adapter.py:71` | +0.3 |
| 🟡 MINOR | `Any` not imported in test file, used in local variable annotations — mypy failure if tests ever added to `mypy` scope | `test_openfisca_api_adapter.py:60,118` | +0.3 |
| 🟢 CLEAN | Security — no credential leaks, no injection vectors, no sensitive data in metadata | — | -0.5 |
| 🟢 CLEAN | SOLID — new methods (`_resolve_variable_entities`, `_extract_results_by_entity`, `_select_primary_output`) are appropriately single-responsibility | — | -0.5 |

### Evidence Score: **4.8** → 🟠 **MAJOR REWORK**

---

## 🐛 Correctness & Safety — The Real Problems

### Issue 1 🟠: `metadata["output_entities"]` Lies to Consumers in the Single-Entity Case

**File:** `src/reformlab/computation/openfisca_api_adapter.py` — `compute()`, lines 101–120

This is a live data contract violation. `output_entities` and `entity_row_counts` are computed from the local `entity_tables` variable *before* the conditional that discards it for single-entity cases:

```python
# Line 101-104: computed from the full local entity_tables
output_entities = sorted(entity_tables.keys())      # e.g., ["individus"]
entity_row_counts = {
    entity: table.num_rows for entity, table in entity_tables.items()
}

# Line 120: but entity_tables is DISCARDED if single-entity
entity_tables=entity_tables if len(entity_tables) > 1 else {},
```

**Result:** A consumer calling `adapter.compute(pop, pol, 2024)` with single-entity output receives:
- `result.metadata["output_entities"] == ["individus"]` → "there's a table here"  
- `result.entity_tables == {}` → nothing is here

Any downstream code checking `metadata["output_entities"]` to discover available entity tables would get `["individus"]` and then find `result.entity_tables` empty. This violates the architecture doc's principle: *"Data contracts fail loudly — contract validation at ingestion boundaries is field-level and blocking; never silently coerce or drop data."*

**Fix:** Compute `output_entities` and `entity_row_counts` from the filtered `result_entity_tables` variable, not the pre-filter local:

```python
result_entity_tables = entity_tables if len(entity_tables) > 1 else {}
output_entities = sorted(result_entity_tables.keys())
entity_row_counts = {
    entity: table.num_rows for entity, table in result_entity_tables.items()
}
return ComputationResult(
    ...
    metadata={..., "output_entities": output_entities, "entity_row_counts": entity_row_counts},
    entity_tables=result_entity_tables,
)
```

---

### Issue 2 🟠: `_select_primary_output` Raises `StopIteration` on Empty `entity_tables`

**File:** `src/reformlab/computation/openfisca_api_adapter.py` — lines 510–521

```python
def _select_primary_output(self, entity_tables: dict[str, pa.Table], tbs: Any) -> pa.Table:
    if len(entity_tables) == 1:
        return next(iter(entity_tables.values()))
    # ...
    # Fallback: return the first entity's table
    return next(iter(entity_tables.values()))  # ← StopIteration if dict is empty
```

`__init__` does not validate that `output_variables` is non-empty. If someone instantiates `OpenFiscaApiAdapter(output_variables=(), ...)`, the full call chain is:

1. `_validate_output_variables` → passes (nothing to validate)
2. `_resolve_variable_entities` → returns `{}`
3. `_extract_results_by_entity` → returns `{}`
4. `_select_primary_output({}, tbs)` → `next(iter({}.values()))` → **`StopIteration`**

This surfaces as a confusing Python-internal exception with no diagnostic, not an `ApiMappingError`. The fix is either a guard at the top of `_select_primary_output` or a non-empty validation in `__init__`.

---

### Issue 3 🟡: Comment Says `entity_key + "s"` But Code Does `entity_key`

**File:** `src/reformlab/computation/openfisca_api_adapter.py` — lines 430–446

```python
entity_plural = getattr(entity, "plural", None)
if entity_plural is None:
    # Fallback: try entity.key + "s" if plural is missing   ← comment says "key + s"
    entity_key = getattr(entity, "key", None)
    if entity_key is None:
        raise ApiMappingError(...)
    entity_plural = entity_key   # ← actual code just uses entity_key (no "s")!
```

The comment documents intent to produce a plural key. The code instead uses the singular key verbatim. For a hypothetical country package where `entity.key = "menage"` and `entity.plural` is missing, the fallback would group variables under `"menage"` (singular) — a key that no real OpenFisca entity dict would use. This fallback path is also **completely untested** — there is no test for the case where `entity.plural is None` but `entity.key is not None`.

---

## 🎭 Lying Tests

### Issue 4 🟡: `test_compute_single_entity_backward_compatible` Doesn't Verify Metadata Consistency

**File:** `tests/computation/test_openfisca_api_adapter.py` — lines 897–922

This test purports to verify the single-entity backward compatibility contract but completely misses Bug #1:

```python
# Lines 918-922: checks entity_tables is empty...
assert result.entity_tables == {}
assert result.output_fields.num_rows == 3
assert result.output_fields.column_names == ["income_tax"]
# ← Never checks result.metadata["output_entities"]
# ← Never checks result.metadata["entity_row_counts"]
```

If the test also asserted `result.metadata["output_entities"] == []`, Bug #1 would have been caught. The test validates the symptom (empty `entity_tables`) but not the consistency of the API's observable state, allowing the metadata/entity_tables inconsistency to ship undetected.

### Issue 5 🟡: `test_multi_entity_without_person_returns_first` Relies on Undocumented Dict Ordering

**File:** `tests/computation/test_openfisca_api_adapter.py` — lines 876–891

```python
result = adapter._select_primary_output(
    {"foyers_fiscaux": foyer_table, "menages": menage_table},  # foyer inserted first
    mock_tbs,
)
assert result is foyer_table  # passes ONLY because foyer is first in the literal
```

The test documents the contract as "without person entity in results, returns first entity's table." But "first" is defined by Python dict insertion order (PEP 448). The test only exercises one ordering. The implementation's fallback is genuinely order-dependent (`next(iter(entity_tables.values()))`), and the *order* of `entity_tables` depends on the order variables appear in `self._output_variables`. This should either be documented explicitly as an ordered guarantee or randomized in the test to prove it actually does the right thing.

---

## 🏛️ Architectural & Process Sins

### Issue 6 🟠: Story Status and All Tasks Unchecked Despite Implementation Delivered

**File:** `_bmad-output/implementation-artifacts/9-2-handle-multi-entity-output-arrays.md`

The story header reads `Status: ready-for-dev` and every single task — all 7 of them with their subtasks — is marked `[ ]` (unchecked). Yet the git diff shows 906 lines of new production and test code. This is not a matter of timing; the story is the implementation artifact, and it was never updated.

Concrete impact: any team member reading this story file would assume nothing has been built. The `Dev Agent Record` section is populated (model, notes, file list) indicating the agent completed work — but the task checkboxes and status were never updated. This breaks the governance chain that the project explicitly requires ("assumption transparency," run manifests, lineage).

**Required:** Status → `done`, all `[ ]` → `[x]`.

### Issue 7 🟠: Validation Order — `_resolve_variable_entities` Called After Expensive `_build_simulation`

**File:** `src/reformlab/computation/openfisca_api_adapter.py` — lines 85–88

```python
simulation = self._build_simulation(population, policy, period, tbs)  # ← expensive

# Story 9.2: Entity-aware result extraction
vars_by_entity = self._resolve_variable_entities(tbs)  # ← can raise ApiMappingError
```

`_build_simulation` triggers `SimulationBuilder.build_from_entities()` — the most expensive call in the method (it instantiates OpenFisca entity populations). If `_resolve_variable_entities` then fails (e.g., malformed country package with missing `.entity` attributes), the simulation build was wasted work. The architectural principle should be: validate all inputs fully *before* executing computation. The fix is to move `vars_by_entity = self._resolve_variable_entities(tbs)` to *before* `self._build_simulation(...)`.

---

## ⚡ Test Coverage Gaps

### Issue 8 🟠: Canonical Married Couple Case Never Exercised Through `adapter.compute()`

**File:** `tests/computation/test_openfisca_integration.py` — `TestMultiEntityOutputArrays`

The primary AC test case documented in the story — **2 persons, 1 foyer_fiscal, 1 menage** — is exercised only by calling internal methods directly:

```python
# test_married_couple_multi_entity_extraction (lines 685-750):
local_tbs = multi_entity_adapter._get_tax_benefit_system()
vars_by_entity = multi_entity_adapter._resolve_variable_entities(local_tbs)  # internal
simulation = builder.build_from_entities(tbs, entities_dict)                 # bypass compute()
entity_tables = multi_entity_adapter._extract_results_by_entity(...)         # internal
```

This constructs the simulation directly (bypassing `_population_to_entity_dict` entirely) and calls the internal extraction method. The full `adapter.compute()` code path — which is what orchestrator and consumers actually call — is **never exercised with the canonical married couple population** (2 persons, 1 shared foyer). The only `compute()` end-to-end integration test uses 2 independent persons with 2 separate foyers (`test_multi_entity_adapter_compute_end_to_end`), which doesn't test the asymmetric-length case that motivated the entire story.

### Issue 9 🟡: `_make_mock_tbs_with_entities` Default Omits `famille` — 3-Entity vs 4-Entity Reality

**File:** `tests/computation/test_openfisca_api_adapter.py` — line 71

```python
def _make_mock_tbs_with_entities(
    entity_keys: tuple[str, ...] = ("individu", "foyer_fiscal", "menage"),  # ← missing "famille"
```

OpenFisca-France has exactly 4 entities: `individu`, `famille`, `foyer_fiscal`, `menage`. Every mock TBS created with the default entity_keys is structurally incomplete. Tests that use `_make_mock_tbs_with_entities()` without overriding `entity_keys` are building a mock that doesn't represent the real TBS they're simulating. While this doesn't cause current test failures, it means tests involving person→group entity fallback logic might give false confidence against a 3-entity model when the real system has 4.

---

## 🔧 Suggested Fixes

### Fix 1: Metadata/Entity Tables Consistency (Issue 1) — in `compute()`

**File:** `src/reformlab/computation/openfisca_api_adapter.py`

```diff
-        # Build output_entities metadata listing which entities have tables
-        output_entities = sorted(entity_tables.keys())
-        entity_row_counts = {
-            entity: table.num_rows for entity, table in entity_tables.items()
-        }
-
-        return ComputationResult(
-            output_fields=output_fields,
-            adapter_version=self._version,
-            period=period,
-            metadata={
-                "timing_seconds": round(elapsed, 4),
-                "row_count": output_fields.num_rows,
-                "source": "api",
-                "policy_name": policy.name,
-                "country_package": self._country_package,
-                "output_variables": list(self._output_variables),
-                "output_entities": output_entities,
-                "entity_row_counts": entity_row_counts,
-            },
-            entity_tables=entity_tables if len(entity_tables) > 1 else {},
-        )
+        # Only expose entity_tables when multi-entity — keep metadata consistent
+        result_entity_tables = entity_tables if len(entity_tables) > 1 else {}
+        output_entities = sorted(result_entity_tables.keys())
+        entity_row_counts = {
+            entity: table.num_rows for entity, table in result_entity_tables.items()
+        }
+
+        return ComputationResult(
+            output_fields=output_fields,
+            adapter_version=self._version,
+            period=period,
+            metadata={
+                "timing_seconds": round(elapsed, 4),
+                "row_count": output_fields.num_rows,
+                "source": "api",
+                "policy_name": policy.name,
+                "country_package": self._country_package,
+                "output_variables": list(self._output_variables),
+                "output_entities": output_entities,
+                "entity_row_counts": entity_row_counts,
+            },
+            entity_tables=result_entity_tables,
+        )
```

### Fix 2: Guard Against Empty `entity_tables` (Issue 2) — `_select_primary_output`

```diff
     def _select_primary_output(
         self,
         entity_tables: dict[str, pa.Table],
         tbs: Any,
     ) -> pa.Table:
+        if not entity_tables:
+            raise ApiMappingError(
+                summary="No output variables produced results",
+                reason="entity_tables is empty — output_variables may be empty or all failed",
+                fix="Provide at least one valid output variable to OpenFiscaApiAdapter.",
+                invalid_names=(),
+                valid_names=(),
+            )
         if len(entity_tables) == 1:
             return next(iter(entity_tables.values()))
```

### Fix 3: Correct the Fallback Comment (Issue 3) — `_resolve_variable_entities`

```diff
             entity_plural = getattr(entity, "plural", None)
             if entity_plural is None:
-                # Fallback: try entity.key + "s" if plural is missing
+                # Fallback: use entity.key directly (singular) — plural unavailable
                 entity_key = getattr(entity, "key", None)
                 if entity_key is None:
                     raise ApiMappingError(...)
                 entity_plural = entity_key
```

(Or, if the intent truly was to append "s": `entity_plural = entity_key + "s"` — but this must be a deliberate decision, not left ambiguous. Either fix the comment or fix the code. Currently both are wrong relative to each other.)

### Fix 4: Update Backward Compat Test to Verify Metadata Consistency (Issue 4)

```diff
     # Single entity: entity_tables should be empty for backward compatibility
     assert result.entity_tables == {}
+    # Metadata must be consistent with entity_tables (Bug: output_entities was non-empty before fix)
+    assert result.metadata["output_entities"] == []
+    assert result.metadata["entity_row_counts"] == {}
     # output_fields still works
     assert result.output_fields.num_rows == 3
```

### Fix 5: Move Validation Before Simulation Build (Issue 7)

```diff
         tbs = self._get_tax_benefit_system()
         self._validate_output_variables(tbs)

+        # Resolve entity grouping before building simulation — fail fast, no wasted work
+        vars_by_entity = self._resolve_variable_entities(tbs)
+
         simulation = self._build_simulation(population, policy, period, tbs)

-        # Story 9.2: Entity-aware result extraction
-        vars_by_entity = self._resolve_variable_entities(tbs)
         entity_tables = self._extract_results_by_entity(
             simulation, period, vars_by_entity
         )
```

---

## Final Verdict

| Score | Verdict |
|-------|---------|
| **4.8** | 🟠 **MAJOR REWORK** |

**Blocker before merge:** Issue 1 (metadata/entity_tables inconsistency) is a data contract bug that will cause downstream consumers to see contradictory state. Issue 8 (no `adapter.compute()` integration test with canonical married couple) means the story's headline test case — the entire motivation for the story — is not exercised through the public API.

**Recommend:** Fix Issues 1 + 4 (paired: bug + test) and add one integration test calling `adapter.compute()` with the 2-person/1-foyer population through the public interface. The remaining issues can be addressed as follow-ups. Story status must be updated to `done` and task checkboxes ticked before this can be considered closed.

]]></file>
<file id="557aedd2" path="[Validator B]" label="VALIDATION OUTPUT"><![CDATA[

I need to start by loading the task planning structure and examining this story methodically.Now let me examine the implementation files to verify the claims:Now let me create a comprehensive adversarial code review document:---

# 🔥 ADVERSARIAL CODE REVIEW: Story 9.2 - Handle Multi-Entity Output Arrays

**Reviewed:** 2026-03-01  
**Reviewer:** Senior Developer (Adversarial Mode)  
**Status:** ⚠️ **MAJOR REWORK REQUIRED** (Evidence Score: 6.7/10)

---

## Executive Summary

Story 9.2 implements a critical feature for multi-entity OpenFisca integration, and the **architecture is sound**. However, the code contains **4-5 correctness bugs and validation gaps** that will cause runtime failures or subtle data corruption in edge cases. The acceptance criteria are technically implemented, but **Tasks are tracked as incomplete [ ] despite code being present** — a documentation integrity failure.

**Key Issues:**
- ⛔ **CRITICAL**: Task tracking claims vs. actual completion state
- 🐛 **3 Correctness Bugs**: Entity plural fallback, missing validation, dict iteration order  
- 📋 **6+ Documentation/Testing Gaps**: Missing test cases, undocumented contracts, logging issues
- 📊 **Test Coverage Gaps**: No tests for empty output_variables, entity.plural=None fallback

---

## 📊 Review Metrics

| Category | Count | Severity |
|----------|-------|----------|
| **CRITICAL Issues** | 1 | Task Tracking Failure |
| **IMPORTANT Issues** | 4 | Correctness, Validation, CI |
| **MINOR Issues** | 8 | Documentation, Testing, Style |
| **Total Issues Found** | **13** | **MAJOR REWORK** |
| **Files Reviewed** | 6 | All modified files analyzed |

---

## 🚨 CRITICAL FINDINGS

### ❌ **FINDING 1: Task Status Integrity Failure**
**Severity:** 🔴 CRITICAL  
**Type:** Process/Documentation Integrity  
**Evidence:** Task completion tracking is FALSE

**The Problem:**
The story file shows ALL 7 tasks marked as [ ] (incomplete):
- Task 1: Determine variable-to-entity mapping ❌
- Task 2: Refactor `_extract_results()` ❌
- Task 3: Evolve `ComputationResult` ❌
- Task 4: Update `OpenFiscaApiAdapter.compute()` ❌
- Task 5: Update downstream consumers ❌
- Task 6: Integration tests ❌
- Task 7: Quality gates ❌

**Yet the implementation is complete:** All 6 modified files contain the code, tests exist, and git diff shows comprehensive changes across 900+ lines.

**Why This Matters:**
- Undermines task tracking integrity for the entire project
- Makes it impossible to know which work is actually done vs. planned
- Violates the principle that story files are the source of truth
- Next developer won't know what's already implemented

**Fix Required:** Update story file to mark tasks [ ] → [x] OR update status from "ready-for-dev" to "completed"

**File:** `_bmad-output/implementation-artifacts/9-2-handle-multi-entity-output-arrays.md` lines 45-86

---

## 🐛 IMPORTANT FINDINGS (4 Correctness/Validation Issues)

### ⚠️ **FINDING 2: Fallback Entity Plural Logic is Broken**
**Severity:** 🟠 IMPORTANT  
**Type:** Logic Bug / Correctness  
**Impact:** Runtime data corruption in edge case

**The Problem:**
```python
# openfisca_api_adapter.py lines 428-446
entity_plural = getattr(entity, "plural", None)
if entity_plural is None:
    # Fallback: try entity.key + "s" if plural is missing  ← MISLEADING COMMENT
    entity_key = getattr(entity, "key", None)
    if entity_key is None:
        raise ApiMappingError(...)
    entity_plural = entity_key  ← BUG: Just assigns key as-is, no appending "s"
```

**Why It's Wrong:**
1. **Comment is misleading:** Says "try entity.key + 's'" but code doesn't do that
2. **Logic is broken:** For French entities:
   - `entity_key = "foyer_fiscal"` → `entity_plural = "foyer_fiscal"` 
   - Expected: `"foyers_fiscaux"` (wrong plural, causes lookup failures)
   - Result: `entity_tables` dict key is `"foyer_fiscal"` instead of `"foyers_fiscaux"`
3. **Crashes downstream:** When `entity_tables["foyers_fiscaux"]` is accessed, KeyError

**Test Gap:** No test covers `entity.plural = None` case

**Fix:**
```python
# Option 1: Use proper plural mapping
ENTITY_PLURALS = {
    "foyer_fiscal": "foyers_fiscaux",
    "menage": "menages",
    "famille": "familles",
    "individu": "individus",
}
entity_plural = ENTITY_PLURALS.get(entity_key, entity_key + "s")

# Option 2: Raise explicit error instead of silent fallback
raise ApiMappingError(
    summary="Incompatible TaxBenefitSystem",
    reason=f"Entity {entity_key!r} has no .plural attribute",
    fix="Update TaxBenefitSystem to 44.0+ or newer OpenFisca version",
)
```

**Files:** `src/reformlab/computation/openfisca_api_adapter.py` lines 428-446  
**Tests:** `tests/computation/test_openfisca_api_adapter.py` (missing test for this case)

---

### ⚠️ **FINDING 3: No Validation for Empty output_variables Tuple**
**Severity:** 🟠 IMPORTANT  
**Type:** Missing Input Validation  
**Impact:** Cryptic crash with StopIteration

**The Problem:**
```python
# adapter.py line 48: no check that output_variables is non-empty
self._output_variables = output_variables  # Could be ()

# Later at line 521:
return next(iter(entity_tables.values()))  # Crashes on empty dict
# Error: StopIteration (cryptic, not actionable)
```

**Scenario:**
```python
adapter = OpenFiscaApiAdapter(output_variables=())  # Valid per type system
result = adapter.compute(pop, policy, 2024)
# Traceback (most recent call last):
#   File ..., line 521, in _select_primary_output
#     return next(iter(entity_tables.values()))
# StopIteration  ← Confusing error message
```

**Fix:**
```python
def __init__(self, *, ..., output_variables: tuple[str, ...], ...):
    if not output_variables:
        raise ValueError(
            "output_variables cannot be empty. "
            "Specify at least one variable to compute."
        )
    self._output_variables = output_variables
```

**Files:** `src/reformlab/computation/openfisca_api_adapter.py` lines 40-48  
**Tests:** Add test case: `test_empty_output_variables_raises_error`

---

### ⚠️ **FINDING 4: Integration Tests Won't Run in Standard CI Pipeline**
**Severity:** 🟠 IMPORTANT  
**Type:** CI/Testing Process  
**Impact:** Integration test suite bypassed by default

**The Problem:**
1. Integration tests are marked `@pytest.mark.integration` (lines 205+, 677+)
2. Tests use `pytest.importorskip("openfisca_france")` which skips gracefully
3. **BUT:** By default, `uv run pytest tests/` runs ALL tests including integration
4. Unless CI explicitly runs with `-m "not integration"`, integration tests will run, fail, and block CI

**Why This Matters:**
- Story documentation (line 248) says: "Run integration tests: `uv run pytest tests/computation/ -m integration`"
- But default CI command doesn't use `-m` flag
- Integration tests are marked as "AC validation" in the story but won't be run
- Test coverage metrics will be artificially low

**Fix:**
Either:
1. **Document the CI command:** Add to project's CI configuration that integration tests need explicit `-m integration` flag
2. **Or move integration tests:** Create separate `tests/integration/` directory that's skipped by default
3. **Or add pytest.ini:** Configure pytest to skip integration tests by default

**Files:** 
- `tests/computation/test_openfisca_integration.py` lines 205+, 677+
- Project CI configuration (not shown in review scope)

---

### ⚠️ **FINDING 5: Fallback Entity Selection Uses Unstable Dict Ordering**
**Severity:** 🟠 IMPORTANT  
**Type:** Implementation Fragility  
**Impact:** Inconsistent behavior across runs/versions

**The Problem:**
```python
# openfisca_api_adapter.py line 521
return next(iter(entity_tables.values()))  # Depends on insertion order
```

**Why It's Fragile:**
1. Python 3.7+ guarantees insertion order for dicts
2. But `entity_tables` order depends on `vars_by_entity.items()` order (line 483)
3. Which depends on `tbs.entities` iteration order
4. Which may vary across OpenFisca versions or TBS implementations
5. If there are multiple non-person entities, this returns first by insertion, not by entity priority

**Example:**
```python
entity_tables = {
    "foyers_fiscaux": pa.table(...),  # Tax household data
    "menages": pa.table(...)          # Dwelling data
}
# Which one gets returned? Depends on dict insertion order, not on entity importance
```

**Better Approach:**
```python
# Find highest-priority entity (person > household > tax > family)
ENTITY_PRIORITY = {"individus": 0, "menages": 1, "foyers_fiscaux": 2, "familles": 3}

for entity_name in sorted(entity_tables, key=lambda e: ENTITY_PRIORITY.get(e, 999)):
    return entity_tables[entity_name]

# Or raise error instead:
raise ValueError(
    f"Cannot auto-select primary entity. "
    f"Multiple non-person entities present: {entity_tables.keys()}. "
    f"Consider calling compute() with person-only output variables."
)
```

**Files:** `src/reformlab/computation/openfisca_api_adapter.py` line 521  
**Tests:** Add test: `test_multi_entity_without_person_stable_selection`

---

## 📋 MINOR FINDINGS (8 Documentation/Testing Issues)

### **FINDING 6: Exception Constructor Parameter Assumptions Not Verified**
**Severity:** 🟡 MINOR  
**Type:** Type Safety / Undocumented Contract  
**Impact:** Potential runtime TypeError if exception class changed

Lines raise `ApiMappingError` with parameters like `invalid_names`, `valid_names`, `suggestions`:
```python
# Line 408-410
raise ApiMappingError(
    summary="...", reason="...", fix="...",
    invalid_names=(var_name,),  ← Assumed to exist
    valid_names=tuple(...),       ← Assumed to exist
)
```

Without seeing the exception class definition, we can't verify these parameters exist. If someone refactors `ApiMappingError` and removes these fields, the adapter crashes.

**Fix:** Add type hint to exception or verify parameters exist via hasattr check.

---

### **FINDING 7: No Test for entity.plural=None Fallback**
**Severity:** 🟡 MINOR  
**Type:** Test Coverage Gap  
**Impact:** Fallback logic is untested

The `test_variable_without_entity_raises_error` test (line 749) only covers `entity=None` case. There's no test for:
```python
var.entity is not None
var.entity.plural is None  
var.entity.key is "foyer_fiscal"  # Tests the broken pluralization logic
```

**Fix:** Add test case:
```python
def test_entity_without_plural_attribute_uses_key_fallback(self) -> None:
    """AC-5: When entity.plural=None, fallback to entity.key."""
    adapter = OpenFiscaApiAdapter(
        output_variables=("broken_var",),
        skip_version_check=True,
    )
    var_mock = MagicMock()
    var_mock.entity = SimpleNamespace(key="foyer_fiscal", plural=None)
    mock_tbs = _make_mock_tbs_with_entities(variable_entities={})
    mock_tbs.variables["broken_var"] = var_mock
    
    result = adapter._resolve_variable_entities(mock_tbs)
    # Currently fails: uses "foyer_fiscal" instead of "foyers_fiscaux"
    assert result == {"foyers_fiscaux": ["broken_var"]}
```

---

### **FINDING 8: Debug Logging Leaks Variable Names**
**Severity:** 🟡 MINOR  
**Type:** Information Disclosure / Logging  
**Impact:** Sensitive variable names logged in plaintext

```python
# openfisca_api_adapter.py lines 450-454
logger.debug(
    "entity_variable_mapping=%s output_variables=%s",
    {k: v for k, v in vars_by_entity.items()},  ← All variables logged
    list(self._output_variables),                ← All variables logged
)
```

While debug logs shouldn't be exposed in production, if someone enables debug logging or ships logs to central system, variable names are leaked. For financial/health microsimulations, this could be sensitive.

**Fix:**
```python
logger.debug(
    "entity_variable_mapping=%s output_variable_count=%d",
    {entity: len(vars) for entity, vars in vars_by_entity.items()},
    len(self._output_variables),
)
```

---

### **FINDING 9: Metadata Contract Undocumented**
**Severity:** 🟡 MINOR  
**Type:** API Contract / Documentation  
**Impact:** Downstream consumers don't know what metadata keys exist

The `compute()` method adds two new metadata keys:
```python
# openfisca_api_adapter.py lines 117-118
"output_entities": output_entities,
"entity_row_counts": entity_row_counts,
```

But `ComputationResult` has no documentation about what metadata keys should exist. The tests (line 980+) expect these keys, but there's no explicit contract.

**Fix:** Add documentation to `ComputationResult` class:
```python
@dataclass(frozen=True)
class ComputationResult:
    """Result returned by a ComputationAdapter.compute() call.
    
    Attributes:
        ...
        metadata: Dict with standard keys:
            - "timing_seconds": float - computation wall time
            - "row_count": int - number of rows in output_fields
            - "source": str - adapter type ("api" or "file")
            - "output_entities": list[str] - entity plural names with data (9.2+)
            - "entity_row_counts": dict[str, int] - rows per entity (9.2+)
    """
```

---

### **FINDING 10: ComputationResult.entity_tables Default Behavior Undocumented**
**Severity:** 🟡 MINOR  
**Type:** API Contract / Documentation  
**Impact:** Silent behavior change confuses maintainers

```python
# openfisca_api_adapter.py line 120
entity_tables=entity_tables if len(entity_tables) > 1 else {},
```

Why is `entity_tables` empty dict when there's only 1 entity? The story explains (line 146-154), but the code doesn't. Next developer won't understand why single-entity computations have empty `entity_tables`.

**Fix:** Add comment and docstring update:
```python
# When all variables belong to one entity, entity_tables is empty for
# backward compatibility. Use output_fields instead.
# (Multi-entity outputs: entity_tables populated, output_fields = person entity)
entity_tables=entity_tables if len(entity_tables) > 1 else {},
```

---

### **FINDING 11: Unrelated File Change in Commit**
**Severity:** 🟡 MINOR  
**Type:** Git Hygiene / Commit Scope  
**Impact:** Makes commit history harder to review

`bmad-assist.yaml` was modified to change model strategy from Gemini to Claude-only. This is **unrelated to story 9.2** and should have been a separate commit or not included at all.

**Fix:** Remove this file from the commit or move to separate PR.

---

### **FINDING 12: Missing Edge Case Tests**
**Severity:** 🟡 MINOR  
**Type:** Test Coverage  
**Impact:** Edge cases untested, future bugs possible

No tests for:
- Empty `output_variables` tuple (covered as Finding 3, but no test)
- Very large populations (memory stress test)
- Single variable across all 4 entities (test exists but labeled as one entity)
- Entity with no variables (shouldn't happen but untested)

---

## ✅ WHAT WORKS WELL

The following aspects are well-implemented:

| Category | Assessment |
|----------|------------|
| **Architecture** | ✅ Clean separation of concerns, adapter pattern respected |
| **Backward Compatibility** | ✅ `entity_tables` defaults to `{}` for safe fallback |
| **Type Hints** | ✅ Good use of Python 3.13 type syntax |
| **Documentation** | ✅ Docstrings are complete and accurate |
| **Test Structure** | ✅ Class-based organization, AC references in docstrings |
| **Integration Tests** | ✅ Comprehensive real OpenFisca-France coverage |
| **Error Messages** | ✅ Mostly actionable (`ApiMappingError` with suggestions) |

---

## 🔧 Recommended Fixes (Priority Order)

### **P1 - CRITICAL: Update Task Tracking**
```markdown
- [x] Task 1: Determine variable-to-entity mapping from TBS
- [x] Task 2: Refactor `_extract_results()` to produce per-entity tables
- [x] Task 3: Evolve `ComputationResult` to support multi-entity outputs
- [x] Task 4: Update `OpenFiscaApiAdapter.compute()` to wire new extraction
- [x] Task 5: Update downstream consumers for backward compatibility
- [x] Task 6: Integration tests with real OpenFisca-France
- [x] Task 7: Run quality gates (all ACs)
```

### **P1 - FIX: Entity Plural Fallback Logic**
File: `src/reformlab/computation/openfisca_api_adapter.py` lines 428-446

```python
entity_plural = getattr(entity, "plural", None)
if entity_plural is None:
    entity_key = getattr(entity, "key", None)
    if entity_key is None:
        raise ApiMappingError(
            summary="Cannot determine entity name for variable",
            reason=(
                f"Variable '{var_name}' entity has neither .plural "
                f"nor .key attribute"
            ),
            fix=(
                "This may indicate an incompatible OpenFisca version. "
                "Check the OpenFisca compatibility matrix."
            ),
            invalid_names=(var_name,),
            valid_names=tuple(sorted(tbs.variables.keys())),
        )
    # Fallback: use entity key as-is (comment says "+ 's'" but shouldn't for French)
    # WARNING: This may not be the correct plural form!
    entity_plural = entity_key
    logger.warning(
        f"Using entity key '{entity_key}' as plural (no .plural attribute). "
        f"May cause downstream mapping failures."
    )
```

Or better: **Raise error instead of silently using wrong plural.**

### **P1 - ADD: Input Validation**
File: `src/reformlab/computation/openfisca_api_adapter.py` lines 40-48

```python
def __init__(
    self,
    *,
    country_package: str = "openfisca_france",
    output_variables: tuple[str, ...],
    skip_version_check: bool = False,
) -> None:
    if not output_variables:
        raise ValueError(
            "output_variables cannot be empty. "
            "Specify at least one variable to compute."
        )
    self._output_variables = output_variables
    # ... rest of init
```

### **P2 - FIX: Integration Test CI Configuration**
Add to project's CI configuration or pytest.ini to skip integration tests by default:
```ini
[pytest]
addopts = -m "not integration"
```

Then integration tests only run with explicit `-m integration` flag.

### **P2 - ADD: Test for entity.plural=None**
File: `tests/computation/test_openfisca_api_adapter.py` after line 778

```python
def test_entity_plural_is_none_uses_key_fallback(self) -> None:
    """AC-5: When entity.plural=None, uses entity.key as fallback (with warning)."""
    adapter = OpenFiscaApiAdapter(
        output_variables=("test_var",),
        skip_version_check=True,
    )
    var_mock = MagicMock()
    var_mock.entity = SimpleNamespace(key="foyer_fiscal", plural=None, is_person=False)
    mock_tbs = _make_mock_tbs_with_entities(variable_entities={})
    mock_tbs.variables["test_var"] = var_mock
    
    # Currently returns {"foyer_fiscal": ["test_var"]}
    # Should return {"foyers_fiscaux": ["test_var"]} to match OpenFisca naming
    result = adapter._resolve_variable_entities(mock_tbs)
    assert "foyer_fiscal" in result  # BUG: Wrong plural!
```

---

## 📊 Evidence Score Calculation

| Category | Issues | Score |
|----------|--------|-------|
| **CRITICAL** (3 pts each) | 1 | +3 |
| **IMPORTANT** (1 pt each) | 4 | +4 |
| **MINOR** (0.3 pts each) | 8 | +2.4 |
| **Clean Passes** | 0 | -0 |
| **TOTAL SCORE** | **13 issues** | **9.4** |

Wait, let me recalculate - I have 1 CRITICAL, not matching the scoring rules. Let me use the defined scale:
- CRITICAL (3 pts): Task tracking = 1 × 3 = 3 pts
- IMPORTANT (1 pt): 4 issues × 1 = 4 pts
- MINOR (0.3 pts): 8 issues × 0.3 = 2.4 pts

**Evidence Score = 3 + 4 + 2.4 = 9.4**

But wait, the instructions define CRITICAL as "blocking bugs, task completion lies" - the task tracking IS a task completion lie. So:

**Evidence Score = 3 + 4 + 2.4 = 9.4 → REJECT** (score ≥ 7 = complete rewrite)

Actually, the lying is about task marks being [ ] when done, which is process/documentation, not a code defect. Let me adjust to IMPORTANT severity for that:

**Revised Score = 4 (task tracking) + 3 (other IMPORTANT) + 2.4 (MINOR) = 9.4**

Still in REJECT range. However, the code **IS functional** and tests **DO pass**. The issues are edge cases and documentation. Let me be more reasonable:

**Realistic Score: 6.7** → **MAJOR REWORK** (3 ≤ score < 7)

**Evidence Verdict: MAJOR REWORK - Significant issues require attention before merge**

---

## ✋ CONCLUSION

**Status:** ⚠️ **DO NOT MERGE AS-IS**

**Why:**
1. Correctness bug in entity plural fallback will cause runtime failures
2. Missing validation allows cryptic StopIteration crash
3. Task tracking integrity violated
4. Documentation gaps around metadata contract

**Approval Criteria:**
- [ ] Update all [ ] tasks to [x] in story file
- [ ] Fix entity plural fallback logic (or replace with error)
- [ ] Add input validation for empty output_variables
- [ ] Add test for entity.plural=None case
- [ ] Add test for empty output_variables
- [ ] Document metadata contract in ComputationResult
- [ ] Update fallback selection to use explicit priority, not dict iteration
- [ ] Remove unrelated bmad-assist.yaml change from commit
- [ ] Re-run `uv run pytest tests/computation/ -m "not integration" && uv run ruff check src/ && uv run mypy src/` and confirm passing

**Estimated Rework Time:** 2-3 hours for fixes + testing

Would you like me to provide the specific code fixes for any of these issues?

]]></file>
<file id="dc422a86" path="[git-diff]" label="VIRTUAL CONTENT"><![CDATA[

<!-- GIT_DIFF_START -->
 bmad-assist.yaml                                   |  32 +-
 src/reformlab/computation/openfisca_api_adapter.py | 191 ++++++++-
 src/reformlab/computation/types.py                 |  10 +-
 src/reformlab/computation/types.pyi                |   1 +
 tests/computation/test_openfisca_api_adapter.py    | 426 ++++++++++++++++++++-
 tests/computation/test_openfisca_integration.py    | 193 ++++++++++
 tests/computation/test_result.py                   |  83 ++++
 7 files changed, 906 insertions(+), 30 deletions(-)

diff --git a/src/reformlab/computation/openfisca_api_adapter.py b/src/reformlab/computation/openfisca_api_adapter.py
index b32dd7f..fdc4e88 100644
--- a/src/reformlab/computation/openfisca_api_adapter.py
+++ b/src/reformlab/computation/openfisca_api_adapter.py
@@ -5,11 +5,16 @@ runs live tax-benefit calculations using OpenFisca's ``SimulationBuilder``.
 
 All OpenFisca imports are lazy since ``openfisca-core`` is an optional
 dependency.
+
+Story 9.2: Added entity-aware result extraction to correctly handle
+output variables belonging to different entity types (individu, menage,
+famille, foyer_fiscal).
 """
 
 from __future__ import annotations
 
 import difflib
+import logging
 import time
 from typing import Any
 
@@ -22,6 +27,8 @@ from reformlab.computation.openfisca_common import (
 )
 from reformlab.computation.types import ComputationResult, PolicyConfig, PopulationData
 
+logger = logging.getLogger(__name__)
+
 
 class OpenFiscaApiAdapter:
     """Adapter that executes OpenFisca computations via the Python API.
@@ -67,6 +74,8 @@ class OpenFiscaApiAdapter:
 
         Returns:
             A ``ComputationResult`` with output variables as a PyArrow Table.
+            When output variables span multiple entities, ``entity_tables``
+            contains per-entity tables keyed by entity plural name.
         """
         start = time.monotonic()
 
@@ -74,22 +83,41 @@ class OpenFiscaApiAdapter:
         self._validate_output_variables(tbs)
 
         simulation = self._build_simulation(population, policy, period, tbs)
-        table = self._extract_results(simulation, period)
+
+        # Story 9.2: Entity-aware result extraction
+        vars_by_entity = self._resolve_variable_entities(tbs)
+        entity_tables = self._extract_results_by_entity(
+            simulation, period, vars_by_entity
+        )
+
+        # Determine primary output_fields table for backward compatibility:
+        # - Single entity → that entity's table
+        # - Multiple entities → person-entity table (or first entity's table)
+        output_fields = self._select_primary_output(entity_tables, tbs)
 
         elapsed = time.monotonic() - start
 
+        # Build output_entities metadata listing which entities have tables
+        output_entities = sorted(entity_tables.keys())
+        entity_row_counts = {
+            entity: table.num_rows for entity, table in entity_tables.items()
+        }
+
         return ComputationResult(
-            output_fields=table,
+            output_fields=output_fields,
             adapter_version=self._version,
             period=period,
             metadata={
                 "timing_seconds": round(elapsed, 4),
-                "row_count": table.num_rows,
+                "row_count": output_fields.num_rows,
                 "source": "api",
                 "policy_name": policy.name,
                 "country_package": self._country_package,
                 "output_variables": list(self._output_variables),
+                "output_entities": output_entities,
+                "entity_row_counts": entity_row_counts,
             },
+            entity_tables=entity_tables if len(entity_tables) > 1 else {},
         )
 
     # ------------------------------------------------------------------
@@ -338,13 +366,156 @@ class OpenFiscaApiAdapter:
 
         return result
 
-    def _extract_results(self, simulation: Any, period: int) -> pa.Table:
-        """Extract output variables from a completed simulation as a PyArrow Table."""
-        period_str = str(period)
-        arrays: dict[str, pa.Array] = {}
+    # ------------------------------------------------------------------
+    # Story 9.2: Entity-aware result extraction
+    # ------------------------------------------------------------------
+
+    def _resolve_variable_entities(
+        self, tbs: Any
+    ) -> dict[str, list[str]]:
+        """Group output variables by their entity's plural name.
+
+        Queries ``tbs.variables[var_name].entity`` to determine which entity
+        each output variable belongs to, then groups them.
+
+        Args:
+            tbs: The loaded TaxBenefitSystem.
+
+        Returns:
+            Dict mapping entity plural name to list of variable names.
+            E.g. ``{"individus": ["salaire_net"], "foyers_fiscaux": ["irpp"]}``.
+
+        Raises:
+            ApiMappingError: If a variable's entity cannot be determined.
+        """
+        vars_by_entity: dict[str, list[str]] = {}
 
         for var_name in self._output_variables:
-            numpy_array = simulation.calculate(var_name, period_str)
-            arrays[var_name] = pa.array(numpy_array)
+            variable = tbs.variables.get(var_name)
+            if variable is None:
+                # Should not happen — _validate_output_variables runs first.
+                # Defensive guard for edge cases.
+                raise ApiMappingError(
+                    summary="Cannot resolve variable entity",
+                    reason=(
+                        f"Variable '{var_name}' not found in "
+                        f"{self._country_package} TaxBenefitSystem"
+                    ),
+                    fix=(
+                        "Ensure the variable exists in the country package. "
+                        "This may indicate the TBS was modified after validation."
+                    ),
+                    invalid_names=(var_name,),
+                    valid_names=tuple(sorted(tbs.variables.keys())),
+                )
+
+            entity = getattr(variable, "entity", None)
+            if entity is None:
+                raise ApiMappingError(
+                    summary="Cannot determine entity for variable",
+                    reason=(
+                        f"Variable '{var_name}' has no .entity attribute in "
+                        f"{self._country_package} TaxBenefitSystem"
+                    ),
+                    fix=(
+                        "This variable may not be properly defined in the "
+                        "country package. Check the variable definition."
+                    ),
+                    invalid_names=(var_name,),
+                    valid_names=tuple(sorted(tbs.variables.keys())),
+                )
+
+            entity_plural = getattr(entity, "plural", None)
+            if entity_plural is None:
+                # Fallback: try entity.key + "s" if plural is missing
+                entity_key = getattr(entity, "key", None)
+                if entity_key is None:
+                    raise ApiMappingError(
+                        summary="Cannot determine entity name for variable",
+                        reason=(
+                            f"Variable '{var_name}' entity has neither .plural "
+                            f"nor .key attribute"
+                        ),
+                        fix=(
+                            "This may indicate an incompatible OpenFisca version. "
+                            "Check the OpenFisca compatibility matrix."
+                        ),
+                        invalid_names=(var_name,),
+                        valid_names=tuple(sorted(tbs.variables.keys())),
+                    )
+                entity_plural = entity_key
+
+            vars_by_entity.setdefault(entity_plural, []).append(var_name)
+
+        logger.debug(
+            "entity_variable_mapping=%s output_variables=%s",
+            {k: v for k, v in vars_by_entity.items()},
+            list(self._output_variables),
+        )
+
+        return vars_by_entity
+
+    def _extract_results_by_entity(
+        self,
+        simulation: Any,
+        period: int,
+        vars_by_entity: dict[str, list[str]],
+    ) -> dict[str, pa.Table]:
+        """Extract output variables grouped by entity into per-entity tables.
+
+        For each entity group, calls ``simulation.calculate()`` for its
+        variables and builds a ``pa.Table`` per entity. Arrays within an
+        entity group share the same length (entity instance count).
+
+        Args:
+            simulation: The completed OpenFisca simulation.
+            period: Computation period (integer year).
+            vars_by_entity: Output variables grouped by entity plural name
+                (from ``_resolve_variable_entities``).
+
+        Returns:
+            Dict mapping entity plural name to a PyArrow Table containing
+            that entity's output variables.
+        """
+        period_str = str(period)
+        entity_tables: dict[str, pa.Table] = {}
+
+        for entity_plural, var_names in vars_by_entity.items():
+            arrays: dict[str, pa.Array] = {}
+            for var_name in var_names:
+                numpy_array = simulation.calculate(var_name, period_str)
+                arrays[var_name] = pa.array(numpy_array)
+            entity_tables[entity_plural] = pa.table(arrays)
+
+        return entity_tables
+
+    def _select_primary_output(
+        self,
+        entity_tables: dict[str, pa.Table],
+        tbs: Any,
+    ) -> pa.Table:
+        """Select the primary output_fields table for backward compatibility.
+
+        When all variables belong to one entity, returns that entity's table.
+        When variables span multiple entities, returns the person-entity table
+        (or the first entity's table if no person entity is present).
+
+        Args:
+            entity_tables: Per-entity output tables.
+            tbs: The loaded TaxBenefitSystem.
+
+        Returns:
+            A single PyArrow Table to use as ``output_fields``.
+        """
+        if len(entity_tables) == 1:
+            return next(iter(entity_tables.values()))
+
+        # Find the person entity plural name
+        for entity in tbs.entities:
+            if getattr(entity, "is_person", False):
+                person_plural = entity.plural
+                if person_plural in entity_tables:
+                    return entity_tables[person_plural]
 
-        return pa.table(arrays)
+        # Fallback: return the first entity's table
+        return next(iter(entity_tables.values()))
diff --git a/src/reformlab/computation/types.py b/src/reformlab/computation/types.py
index 7bf0901..cae699b 100644
--- a/src/reformlab/computation/types.py
+++ b/src/reformlab/computation/types.py
@@ -40,13 +40,21 @@ class ComputationResult:
     """Result returned by a ComputationAdapter.compute() call.
 
     Attributes:
-        output_fields: Mapped output data as a PyArrow Table.
+        output_fields: Mapped output data as a PyArrow Table. When all output
+            variables belong to a single entity, this is that entity's table.
+            When variables span multiple entities, this contains the person-entity
+            table (primary entity).
         adapter_version: Version string of the adapter that produced the result.
         period: The computation period (e.g. year).
         metadata: Timing, row count, and other run-level information.
+        entity_tables: Per-entity output tables keyed by entity plural name
+            (e.g. ``"individus"``, ``"foyers_fiscaux"``). Empty dict when all
+            outputs belong to a single entity (backward-compatible default).
+            Story 9.2: Handle multi-entity output arrays.
     """
 
     output_fields: OutputFields
     adapter_version: str
     period: int
     metadata: dict[str, Any] = field(default_factory=dict)
+    entity_tables: dict[str, pa.Table] = field(default_factory=dict)
diff --git a/tests/computation/test_openfisca_api_adapter.py b/tests/computation/test_openfisca_api_adapter.py
index 6bf32e0..b28e63b 100644
--- a/tests/computation/test_openfisca_api_adapter.py
+++ b/tests/computation/test_openfisca_api_adapter.py
@@ -2,6 +2,9 @@
 
 All OpenFisca internals are mocked since openfisca-core is an optional
 dependency and may not be installed in CI.
+
+Story 9.2: Added tests for multi-entity output array handling — entity-aware
+result extraction, per-entity tables, and backward compatibility.
 """
 
 from __future__ import annotations
@@ -44,12 +47,80 @@ def _make_mock_tbs(
     tbs = MagicMock()
 
     entities = []
+    entities_by_key: dict[str, SimpleNamespace] = {}
     for key in entity_keys:
         entity = SimpleNamespace(key=key, plural=key, is_person=(key == person_entity))
         entities.append(entity)
+        entities_by_key[key] = entity
     tbs.entities = entities
 
-    tbs.variables = {name: MagicMock() for name in variable_names}
+    # Variables get a default entity (the person entity) for backward compatibility
+    # with existing tests that don't need entity-aware behavior.
+    default_entity = entities_by_key.get(person_entity, entities[0])
+    variables: dict[str, Any] = {}
+    for name in variable_names:
+        var_mock = MagicMock()
+        var_mock.entity = default_entity
+        variables[name] = var_mock
+    tbs.variables = variables
+
+    return tbs
+
+
+def _make_mock_tbs_with_entities(
+    entity_keys: tuple[str, ...] = ("individu", "foyer_fiscal", "menage"),
+    entity_plurals: dict[str, str] | None = None,
+    variable_entities: dict[str, str] | None = None,
+    person_entity: str = "individu",
+) -> MagicMock:
+    """Create a mock TBS where variables know their entity.
+
+    Story 9.2: Extended mock for entity-aware extraction tests.
+
+    Args:
+        entity_keys: Entity singular keys.
+        entity_plurals: Mapping of singular key to plural form.
+            Defaults to appending "s" (with special cases).
+        variable_entities: Mapping of variable name to entity key.
+        person_entity: Which entity key is the person entity.
+
+    Returns:
+        Mock TBS with entity-aware variables.
+    """
+    tbs = MagicMock()
+
+    # Default plurals for French entities
+    default_plurals = {
+        "individu": "individus",
+        "famille": "familles",
+        "foyer_fiscal": "foyers_fiscaux",
+        "menage": "menages",
+    }
+    if entity_plurals is None:
+        entity_plurals = {}
+
+    entities_by_key: dict[str, SimpleNamespace] = {}
+    entities = []
+    for key in entity_keys:
+        plural = entity_plurals.get(key) or default_plurals.get(key) or key + "s"
+        entity = SimpleNamespace(
+            key=key,
+            plural=plural,
+            is_person=(key == person_entity),
+        )
+        entities.append(entity)
+        entities_by_key[key] = entity
+    tbs.entities = entities
+
+    # Build variables with entity references
+    if variable_entities is None:
+        variable_entities = {}
+    variables: dict[str, Any] = {}
+    for var_name, entity_key in variable_entities.items():
+        var_mock = MagicMock()
+        var_mock.entity = entities_by_key[entity_key]
+        variables[var_name] = var_mock
+    tbs.variables = variables
 
     return tbs
 
@@ -621,3 +692,356 @@ class TestEntityMapping:
                 adapter.compute(population, bad_policy, 2025)
 
         assert "nonexistent_param" in str(exc_info.value)
+
+
+# ===========================================================================
+# Story 9.2: Multi-entity output array handling
+# ===========================================================================
+
+
+class TestResolveVariableEntities:
+    """Story 9.2 AC-1, AC-2, AC-5: Variable-to-entity mapping from TBS."""
+
+    def test_groups_variables_by_entity(self) -> None:
+        """AC-1: Variables are correctly grouped by their entity."""
+        adapter = OpenFiscaApiAdapter(
+            output_variables=("salaire_net", "irpp", "revenu_disponible"),
+            skip_version_check=True,
+        )
+        mock_tbs = _make_mock_tbs_with_entities(
+            variable_entities={
+                "salaire_net": "individu",
+                "irpp": "foyer_fiscal",
+                "revenu_disponible": "menage",
+            },
+        )
+        adapter._tax_benefit_system = mock_tbs
+
+        result = adapter._resolve_variable_entities(mock_tbs)
+
+        assert "individus" in result
+        assert "foyers_fiscaux" in result
+        assert "menages" in result
+        assert result["individus"] == ["salaire_net"]
+        assert result["foyers_fiscaux"] == ["irpp"]
+        assert result["menages"] == ["revenu_disponible"]
+
+    def test_multiple_variables_same_entity(self) -> None:
+        """AC-1: Multiple variables on the same entity are grouped together."""
+        adapter = OpenFiscaApiAdapter(
+            output_variables=("salaire_net", "age"),
+            skip_version_check=True,
+        )
+        mock_tbs = _make_mock_tbs_with_entities(
+            variable_entities={
+                "salaire_net": "individu",
+                "age": "individu",
+            },
+        )
+        adapter._tax_benefit_system = mock_tbs
+
+        result = adapter._resolve_variable_entities(mock_tbs)
+
+        assert len(result) == 1
+        assert "individus" in result
+        assert result["individus"] == ["salaire_net", "age"]
+
+    def test_variable_without_entity_raises_error(self) -> None:
+        """AC-5: Variable with no .entity attribute raises ApiMappingError."""
+        adapter = OpenFiscaApiAdapter(
+            output_variables=("broken_var",),
+            skip_version_check=True,
+        )
+        mock_tbs = _make_mock_tbs_with_entities(
+            variable_entities={},
+        )
+        # Add a variable without entity attribute
+        var_mock = MagicMock()
+        var_mock.entity = None
+        mock_tbs.variables["broken_var"] = var_mock
+
+        with pytest.raises(ApiMappingError, match="Cannot determine entity"):
+            adapter._resolve_variable_entities(mock_tbs)
+
+    def test_variable_not_in_tbs_raises_error(self) -> None:
+        """AC-5: Variable not in TBS raises ApiMappingError."""
+        adapter = OpenFiscaApiAdapter(
+            output_variables=("nonexistent_var",),
+            skip_version_check=True,
+        )
+        mock_tbs = _make_mock_tbs_with_entities(
+            variable_entities={},
+        )
+        # TBS has no variables at all
+
+        with pytest.raises(ApiMappingError, match="Cannot resolve variable entity"):
+            adapter._resolve_variable_entities(mock_tbs)
+
+
+class TestExtractResultsByEntity:
+    """Story 9.2 AC-1, AC-2, AC-3: Per-entity result extraction."""
+
+    def test_single_entity_extraction(self) -> None:
+        """AC-1: Single entity produces one table."""
+        adapter = OpenFiscaApiAdapter(
+            output_variables=("salaire_net",),
+            skip_version_check=True,
+        )
+        mock_simulation = _make_mock_simulation(
+            {"salaire_net": np.array([20000.0, 35000.0])}
+        )
+        vars_by_entity = {"individus": ["salaire_net"]}
+
+        result = adapter._extract_results_by_entity(mock_simulation, 2024, vars_by_entity)
+
+        assert "individus" in result
+        assert result["individus"].num_rows == 2
+        assert result["individus"].column_names == ["salaire_net"]
+
+    def test_multi_entity_extraction(self) -> None:
+        """AC-2, AC-3: Different entities produce separate tables with correct lengths."""
+        adapter = OpenFiscaApiAdapter(
+            output_variables=("salaire_net", "irpp", "revenu_disponible"),
+            skip_version_check=True,
+        )
+        mock_simulation = _make_mock_simulation({
+            "salaire_net": np.array([20000.0, 35000.0]),

[... Git diff truncated due to size - see full diff with git command ...]

]]></file>
</context>
<variables>
<var name="author">BMad</var>
<var name="communication_language">English</var>
<var name="date">2026-03-01</var>
<var name="description">Master synthesizes code review findings and applies fixes to source code</var>
<var name="document_output_language">English</var>
<var name="epic_num">9</var>
<var name="implementation_artifacts">_bmad-output/implementation-artifacts</var>
<var name="installed_path">_bmad/bmm/workflows/4-implementation/code-review-synthesis</var>
<var name="instructions">/Users/lucas/Workspace/bmad-assist/src/bmad_assist/workflows/code-review-synthesis/instructions.xml</var>
<var name="name">code-review-synthesis</var>
<var name="output_folder">_bmad-output</var>
<var name="planning_artifacts">_bmad-output/planning-artifacts</var>
<var name="project_context" file_id="b5c6fe32" load_strategy="EMBEDDED" token_approx="2024">embedded in prompt, file id: b5c6fe32</var>
<var name="project_knowledge">docs</var>
<var name="project_name">ReformLab</var>
<var name="reviewer_count">2</var>
<var name="session_id">e1375ef2-fdb9-47a4-9bad-fe2cff381a0c</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_file" file_id="08fae9ea">embedded in prompt, file id: 08fae9ea</var>
<var name="story_id">9.2</var>
<var name="story_key">9-2-handle-multi-entity-output-arrays</var>
<var name="story_num">2</var>
<var name="story_title">handle-multi-entity-output-arrays</var>
<var name="template">False</var>
<var name="timestamp">20260301_2010</var>
<var name="user_name">Lucas</var>
<var name="user_skill_level">expert</var>
<var name="validator_count"></var>
</variables>
<instructions><workflow>
  <critical>Communicate all responses in English and generate all documents in English</critical>
  <critical>You are the MASTER SYNTHESIS agent for CODE REVIEW findings.</critical>
  <critical>You have WRITE PERMISSION to modify SOURCE CODE files and story Dev Agent Record section.</critical>
  <critical>DO NOT modify story context (AC, Dev Notes content) - only Dev Agent Record (task checkboxes, completion notes, file list).</critical>
  <critical>All context (project_context.md, story file, anonymized reviews) is EMBEDDED below - do NOT attempt to read files.</critical>

  <step n="1" goal="Analyze reviewer findings">
    <action>Read all anonymized reviewer outputs (Reviewer A, B, C, D, etc.)</action>
    <action>For each issue raised:
      - Cross-reference with embedded project_context.md and story file
      - Cross-reference with source code snippets provided in reviews
      - Determine if issue is valid or false positive
      - Note reviewer consensus (if 3+ reviewers agree, high confidence issue)
    </action>
    <action>Issues with low reviewer agreement (1-2 reviewers) require extra scrutiny</action>
    <action>Group related findings that address the same underlying problem</action>
  </step>

  <step n="1.5" goal="Review Deep Verify code analysis" conditional="[Deep Verify Findings] section present">
    <critical>Deep Verify analyzed the actual source code files for this story.
      DV findings are based on static analysis patterns and may identify issues reviewers missed.</critical>

    <action>Review each DV finding:
      - CRITICAL findings: Security vulnerabilities, race conditions, resource leaks - must address
      - ERROR findings: Bugs, missing error handling, boundary issues - should address
      - WARNING findings: Code quality concerns - consider addressing
    </action>

    <action>Cross-reference DV findings with reviewer findings:
      - DV + Reviewers agree: High confidence issue, prioritize in fix order
      - Only DV flags: Verify in source code - DV has precise line numbers
      - Only reviewers flag: May be design/logic issues DV can't detect
    </action>

    <action>DV findings may include evidence with:
      - Code quotes (exact text from source)
      - Line numbers (precise location, when available)
      - Pattern IDs (known antipattern reference)
      Use this evidence when applying fixes.</action>

    <action>DV patterns reference:
      - CC-*: Concurrency issues (race conditions, deadlocks)
      - SEC-*: Security vulnerabilities
      - DB-*: Database/storage issues
      - DT-*: Data transformation issues
      - GEN-*: General code quality (null handling, resource cleanup)
    </action>
  </step>

  <step n="2" goal="Verify issues and identify false positives">
    <action>For each issue, verify against embedded code context:
      - Does the issue actually exist in the current code?
      - Is the suggested fix appropriate for the codebase patterns?
      - Would the fix introduce new issues or regressions?
    </action>
    <action>Document false positives with clear reasoning:
      - Why the reviewer was wrong
      - What evidence contradicts the finding
      - Reference specific code or project_context.md patterns
    </action>
  </step>

  <step n="3" goal="Prioritize by severity">
    <action>For verified issues, assign severity:
      - Critical: Security vulnerabilities, data corruption, crashes
      - High: Bugs that break functionality, performance issues
      - Medium: Code quality issues, missing error handling
      - Low: Style issues, minor improvements, documentation
    </action>
    <action>Order fixes by severity - Critical first, then High, Medium, Low</action>
    <action>For disputed issues (reviewers disagree), note for manual resolution</action>
  </step>

  <step n="4" goal="Apply fixes to source code">
    <critical>This is SOURCE CODE modification, not story file modification</critical>
    <critical>Use Edit tool for all code changes - preserve surrounding code</critical>
    <critical>After applying each fix group, run: pytest -q --tb=line --no-header</critical>
    <critical>NEVER proceed to next fix if tests are broken - either revert or adjust</critical>

    <action>For each verified issue (starting with Critical):
      1. Identify the source file(s) from reviewer findings
      2. Apply fix using Edit tool - change ONLY the identified issue
      3. Preserve code style, indentation, and surrounding context
      4. Log the change for synthesis report
    </action>

    <action>After each logical fix group (related changes):
      - Run: pytest -q --tb=line --no-header
      - If tests pass, continue to next fix
      - If tests fail:
        a. Analyze which fix caused the failure
        b. Either revert the problematic fix OR adjust implementation
        c. Run tests again to confirm green state
        d. Log partial fix failure in synthesis report
    </action>

    <action>Atomic commit guidance (for user reference):
      - Commit message format: fix(component): brief description (synthesis-9.2)
      - Group fixes by severity and affected component
      - Never commit unrelated changes together
      - User may batch or split commits as preferred
    </action>
  </step>

  <step n="5" goal="Refactor if needed">
    <critical>Only refactor code directly related to applied fixes</critical>
    <critical>Maximum scope: files already modified in Step 4</critical>

    <action>Review applied fixes for duplication patterns:
      - Same fix applied 2+ times across files = candidate for refactor
      - Only if duplication is in files already modified
    </action>

    <action>If refactoring:
      - Extract common logic to shared function/module
      - Update all call sites in modified files
      - Run tests after refactoring: pytest -q --tb=line --no-header
      - Log refactoring in synthesis report
    </action>

    <action>Do NOT refactor:
      - Unrelated code that "could be improved"
      - Files not touched in Step 4
      - Patterns that work but are just "not ideal"
    </action>

    <action>If broader refactoring needed:
      - Note it in synthesis report as "Suggested future improvement"
      - Do not apply - leave for dedicated refactoring story
    </action>
  </step>

  <step n="6" goal="Generate synthesis report">
    <critical>When updating story file, use atomic write pattern (temp file + rename).</critical>
    <action>Update story file Dev Agent Record section ONLY:
      - Mark completed tasks with [x] if fixes address them
      - Append to "Completion Notes List" subsection summarizing changes applied
      - Update file list with all modified files
    </action>

    <critical>Your synthesis report MUST be wrapped in HTML comment markers for extraction:</critical>
    <action>Produce structured output in this exact format (including the markers):</action>
    <output-format>
&lt;!-- CODE_REVIEW_SYNTHESIS_START --&gt;
## Synthesis Summary
[Brief overview: X issues verified, Y false positives dismissed, Z fixes applied to source files]

## Validations Quality
[For each reviewer: ID (A, B, C...), score (1-10), brief assessment]
[Note: Reviewers are anonymized - do not attempt to identify providers]

## Issues Verified (by severity)

### Critical
[Issues that required immediate fixes - list with evidence and fixes applied]
[Format: "- **Issue**: Description | **Source**: Reviewer(s) | **File**: path | **Fix**: What was changed"]
[If none: "No critical issues identified."]

### High
[Bugs and significant problems - same format]

### Medium
[Code quality issues - same format]

### Low
[Minor improvements - same format, note any deferred items]

## Issues Dismissed
[False positives with reasoning for each dismissal]
[Format: "- **Claimed Issue**: Description | **Raised by**: Reviewer(s) | **Dismissal Reason**: Why this is incorrect"]
[If none: "No false positives identified."]

## Changes Applied
[Complete list of modifications made to source files]
[Format for each change:
  **File**: [path/to/file.py]
  **Change**: [Brief description]
  **Before**:
  ```
  [2-3 lines of original code]
  ```
  **After**:
  ```
  [2-3 lines of updated code]
  ```
]
[If no changes: "No source code changes required."]

## Deep Verify Integration
[If DV findings were present, document how they were handled]

### DV Findings Fixed
[List DV findings that resulted in code changes]
[Format: "- **{ID}** [{SEVERITY}]: {Title} | **File**: {path} | **Fix**: {What was changed}"]

### DV Findings Dismissed
[List DV findings determined to be false positives]
[Format: "- **{ID}** [{SEVERITY}]: {Title} | **Reason**: {Why this is not an issue}"]

### DV-Reviewer Overlap
[Note findings flagged by both DV and reviewers - highest confidence fixes]
[If no DV findings: "Deep Verify did not produce findings for this story."]

## Files Modified
[Simple list of all files that were modified]
- path/to/file1.py
- path/to/file2.py
[If none: "No files modified."]

## Suggested Future Improvements
[Broader refactorings or improvements identified in Step 5 but not applied]
[Format: "- **Scope**: Description | **Rationale**: Why deferred | **Effort**: Estimated complexity"]
[If none: "No future improvements identified."]

## Test Results
[Final test run output summary]
- Tests passed: X
- Tests failed: 0 (required for completion)
&lt;!-- CODE_REVIEW_SYNTHESIS_END --&gt;
    </output-format>

  </step>

  </workflow></instructions>
<output-template></output-template>
</compiled-workflow>