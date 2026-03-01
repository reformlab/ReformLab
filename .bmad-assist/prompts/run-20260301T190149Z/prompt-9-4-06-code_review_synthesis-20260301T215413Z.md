<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 9 -->
<!-- Story: 4 -->
<!-- Phase: code-review-synthesis -->
<!-- Timestamp: 20260301T215413Z -->
<compiled-workflow>
<mission><![CDATA[

Master Code Review Synthesis: Story 9.4

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
<file id="bc34e66e" path="_bmad-output/implementation-artifacts/9-4-define-population-data-4-entity-format.md" label="STORY FILE"><![CDATA[

# Story 9.4: Define Population Data 4-Entity Format

Status: ready-for-dev

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
            # AC-5: Null check on _id column
            id_array = person_table.column(id_col)
            null_mask = pa.compute.is_null(id_array)
            if pa.compute.any(null_mask).as_py():
                # Find first null index
                for i in range(len(null_mask)):
                    if null_mask[i].as_py():
                        raise ApiMappingError(
                            summary="Null value in membership column",
                            reason=(
                                f"Column '{id_col}' has null value at "
                                f"row index {i}. All membership columns "
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

            # AC-5: Null check on _role column
            role_array = person_table.column(role_col)
            null_mask = pa.compute.is_null(role_array)
            if pa.compute.any(null_mask).as_py():
                for i in range(len(null_mask)):
                    if null_mask[i].as_py():
                        raise ApiMappingError(
                            summary="Null value in membership column",
                            reason=(
                                f"Column '{role_col}' has null value at "
                                f"row index {i}. All membership columns "
                                f"must have non-null values."
                            ),
                            fix=(
                                f"Ensure every person has a valid role "
                                f"in '{role_col}'."
                            ),
                            invalid_names=(role_col,),
                            valid_names=(),
                        )

            # AC-4: Role value validation
            entity_valid_roles = valid_roles.get(entity_key, frozenset())
            if entity_valid_roles:
                role_values = role_array.to_pylist()
                for value in role_values:
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
        assert person_table_key is not None  # guaranteed by membership_cols being non-empty
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

        # Step 5d: Build person instances FROM PERSON TABLE ONLY
        person_dict: dict[str, Any] = {}
        for i in range(person_table.num_rows):
            instance_id = f"{person_table_key}_{i}"
            instance_data: dict[str, Any] = {}

            for col in person_table.column_names:
                if col in membership_col_names:
                    continue
                value = person_table.column(col)[i].as_py()
                instance_data[col] = {period_str: value}

            person_dict[instance_id] = instance_data

        assert person_entity_plural is not None
        result[person_entity_plural] = person_dict

        # Step 5e: Build group entity instances from membership columns
        for group_entity_key, (id_col, role_col) in membership_cols.items():
            id_array = person_table.column(id_col)
            role_array = person_table.column(role_col)

            # Get sorted distinct group IDs
            unique_ids = pa.compute.unique(id_array)
            sorted_group_ids = sorted(unique_ids.to_pylist())

            group_dict: dict[str, Any] = {}
            for group_id in sorted_group_ids:
                # Collect row indices where id_col == group_id
                role_assignments: dict[str, list[str]] = {}
                for i in range(person_table.num_rows):
                    if id_array[i].as_py() == group_id:
                        role_key = role_array[i].as_py()
                        person_id = f"{person_table_key}_{i}"
                        role_assignments.setdefault(role_key, []).append(person_id)

                instance_id = f"{group_entity_key}_{group_id}"
                group_dict[instance_id] = dict(role_assignments)

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

from __future__ import annotations
import sys
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch
import pyarrow as pa
import pytest
from reformlab.computation.adapter import ComputationAdapter
from reformlab.computation.exceptions import ApiMappingError, CompatibilityError
from reformlab.computation.openfisca_api_adapter import OpenFiscaApiAdapter
from reformlab.computation.types import ComputationResult, PolicyConfig, PopulationData
        from reformlab.computation.openfisca_adapter import OpenFiscaAdapter
        from reformlab.computation.openfisca_adapter import OpenFiscaAdapter

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


class TestPeriodValidation:  # ...

    def test_zero_period_raises_error(  # ...

    def test_negative_period_raises_error(  # ...

    def test_two_digit_period_raises_error(  # ...

    def test_five_digit_period_raises_error(  # ...

    def test_valid_period_2024_passes(  # ...

    def test_valid_period_1000_passes(  # ...

    def test_valid_period_9999_passes(  # ...

]]></file>
<file id="895c54dc" path="tests/computation/test_openfisca_integration.py" label="SOURCE CODE"><![CDATA[

from

]]></file>
<file id="90dfc412" path="[ANTIPATTERNS - DO NOT REPEAT]" label="VIRTUAL CONTENT"><![CDATA[

# Epic 9 - Code Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during code review of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent implementation mistakes (race conditions, missing tests, weak assertions, etc.)

## Story 9-2 (2026-03-01)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | `metadata["output_entities"]` and `metadata["entity_row_counts"]` were computed from the pre-filter `entity_tables` dict, then `entity_tables` was conditionally cleared to `{}` for single-entity results. This left the two metadata fields populated (e.g. `["individus"]`) while `result.entity_tables` was empty — contradictory observable state that violates the "data contracts fail loudly" architectural principle. | Introduced `result_entity_tables` computed before metadata; both metadata fields and the `entity_tables` field now derive from the same filtered value. |
| high | `__init__` accepted `output_variables=()` without error. The empty tuple flowed through `_resolve_variable_entities` (returning `{}`), `_extract_results_by_entity` (returning `{}`), and `_select_primary_output({}, tbs)` which called `next(iter({}.values()))` → bare Python `StopIteration` with no diagnostic. | Added early guard at top of `__init__` raising `ApiMappingError` with clear message. |
| high | `_resolve_variable_entities` was called *after* `_build_simulation`, meaning the expensive `SimulationBuilder.build_from_entities()` call ran even when entity resolution would fail immediately after. Violates fail-fast principle. | Moved `_resolve_variable_entities` call to before `_build_simulation`. |
| medium | Comment at line 430 read `# Fallback: try entity.key + "s" if plural is missing` but the code immediately below assigned `entity_plural = entity_key` (no `+ "s"`). Beyond the comment being wrong, the silent fallback itself was incorrect: for French entities, `foyer_fiscal` → `foyers_fiscaux` (not `foyer_fiscals`), so the fallback would produce wrong dict keys causing misleading downstream lookup failures. | Replaced the entire fallback block with an `ApiMappingError` that fires whenever `entity.plural` is `None`, regardless of whether `entity.key` is present. Real OpenFisca TBS entities always have `.plural`; absence signals an incompatible TBS. |
| medium | `test_compute_single_entity_backward_compatible` verified `entity_tables == {}` but never asserted on `metadata["output_entities"]` or `metadata["entity_row_counts"]`, allowing the metadata/entity_tables inconsistency (Critical bug above) to go undetected. | Added two assertions with a comment explaining the regression guard intent. |
| low | Story file had `Status: ready-for-dev` and all 7 tasks marked `[ ]` despite full implementation being delivered. Governance integrity violation — team members reading the story would assume nothing had been built. | Set `Status: done`, all tasks checked `[x]`, synthesis completion notes appended to Dev Agent Record. |

## Story 9-3 (2026-03-01)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | `from typing import Any` missing in unit test file | Added `from typing import Any` to import block. `Any` was used as a local variable annotation at lines 62 and 128 (`variables: dict[str, Any] = {}`). With `from __future__ import annotations`, this doesn't cause a runtime error but mypy strict mode would flag it as an undefined name. |
| medium | AC-3 "FIRST" ordering constraint untested — existing `TestPeriodValidation` tests pre-load the TBS via `adapter._tax_benefit_system = mock_tbs`, so the tests pass whether `_validate_period()` runs before or after `_get_tax_benefit_system()` | Added `test_period_validation_precedes_tbs_loading` — does NOT pre-load TBS, asserts `adapter._tax_benefit_system is None` before and after raising the error. |
| medium | Dead code in `test_compute_entity_detection_error` — `mock_builder_instance`, `mock_simulation`, and `_patch_simulation_builder` context are set up but never used because the error fires in `_resolve_variable_entities()` before `_build_simulation()` | Removed 3 dead mock setup lines and the `_patch_simulation_builder` wrapper; replaced with a plain `pytest.raises` block plus explanatory comment. |
| medium | Misleading comment on the mock `definition_period` fix — the comment in `_make_mock_tbs()` lacked the accurate explanation of *why* the attribute must be set | Rewrote comment to explain that a `MagicMock` definition_period's `str()` returns `"<MagicMock ...>"` which is not in `_VALID_PERIODICITIES`, causing `ApiMappingError("Unexpected periodicity")` — not silent dispatch to `calculate_add()`. |
| low | Missing test for empty `output_variables` guard — `__init__` raises `ApiMappingError` on empty tuple but no test covered this | Added `test_empty_output_variables_raises_error` to `TestOutputVariableValidation`. |
| low | DRY violation — the `calculate` vs `calculate_add` dispatch decision was duplicated between `_calculate_variable()` and the `calculation_methods` dict-comprehension in `compute()`. Adding a new periodicity to `_CALCULATE_ADD_PERIODICITIES` would update the runtime dispatch automatically but silently leave the metadata reporting stale | Extracted `_periodicity_to_method_name(periodicity: str) -> str` module-level helper; both `_calculate_variable()` and `compute()` now call it as the single source of truth. |


]]></file>
<file id="1d910d88" path="[Validator A]" label="VALIDATION OUTPUT"><![CDATA[

**Story:** Story 9.4 - define-population-data-4-entity-format  
**Status:** ❌ **MAJOR REWORK REQUIRED**

---

## 📋 Executive Summary

The story claims all 8 tasks are complete (`[x]` marked). **The code does NOT support these claims.** I found **12 critical to medium-severity issues**, including:

- **Task completion lies**: Task 6 (integration tests) is completely unimplemented
- **Missing functions**: Code references `_patch_simulation_builder()` that doesn't exist
- **Duplicate code**: Test file has duplicated test classes that cause pytest failures
- **Incomplete test file**: test_openfisca_integration.py is literally empty (1 import line)
- **Inefficient validation**: O(n) row iteration instead of vectorized operations
- **Missing edge case tests**: Non-contiguous group IDs, cardinality constraints

---

## 🎯 Critical Issues (Must Fix Before Merge)

### 1. ❌ CRITICAL: Task 6 Integration Tests — Completely Missing

**Status:** Task marked `[x]` but **0% implemented**

**Evidence:**
- Story claims: "Task 6: Integration tests with real OpenFisca-France (AC: #1, #2, #7)"
- Story lists 6 required tests: 6.1 (married couple), 6.2 (single person), 6.3 (two households), 6.4 (group variables), 6.5 (backward compat), 6.6 (@pytest.mark.integration)
- **Actual file content:**
  ```
  tests/computation/test_openfisca_integration.py
  Line 1: from
  Line 2-644: [empty - literally nothing]
  ```

**Impact:** AC-1, AC-2, AC-7 have ZERO integration test evidence. Cannot validate against real OpenFisca-France.

**Severity:** 🔴 **CRITICAL** — Task completion fraud; AC coverage gap

**Fix:** Implement all 6 test cases from story Task 6.1-6.6 (≈150 lines)

---

### 2. ❌ CRITICAL: `_patch_simulation_builder()` Function Undefined

**Evidence:**
- Test file references this function **28 times** (search for `with _patch_simulation_builder`)
- Example from line ~468:
  ```python
  with _patch_simulation_builder(mock_builder_instance):
      result = adapter.compute(sample_population, empty_policy, 2025)
  ```
- **Function definition:** Not found anywhere in the code

**Impact:** Tests cannot run. Python will raise `NameError: name '_patch_simulation_builder' is not defined` on first test execution.

**Severity:** 🔴 **CRITICAL** — Code cannot execute

**Fix:**
```python
def _patch_simulation_builder(mock_builder_instance: MagicMock) -> Any:
    """Patch SimulationBuilder in openfisca_core.simulation_builder."""
    return patch.object(
        sys.modules.get('openfisca_core.simulation_builder') or MagicMock(),
        "SimulationBuilder",
        return_value=mock_builder_instance,
    )
```

---

### 3. ❌ CRITICAL: Duplicate Test Classes in test_openfisca_api_adapter.py

**Evidence:**
- `TestProtocolCompliance` defined **twice** (lines ~60-80, lines ~230-250)
- `TestVersionChecking` defined **twice** (lines ~82-120, lines ~252-290)
- `TestGracefulDegradation` defined **twice** (lines ~122-140, lines ~292-310)
- `TestTaxBenefitSystemLoading` defined **twice** (lines ~142-180, lines ~312-350)
- `TestCompute` defined **twice** (lines ~182-240, lines ~352-410)
- `TestOutputVariableValidation` appears **twice** with additional test (lines ~242-290, lines ~412-530)

**Impact:**
- pytest will fail with "duplicate class definition" errors
- Second definitions override first, causing test loss
- Code is unmaintainable

**Severity:** 🔴 **CRITICAL** — Test suite won't run

**Fix:** Remove all duplicate class definitions. Keep only the first/most complete version.

---

### 4. ❌ CRITICAL: Task 8 Claims Quality Gates Pass — False

**Story claims:**
```
Task 8: Run quality gates (all ACs)
  - 8.1: uv run ruff check src/ tests/
  - 8.2: uv run mypy src/
  - 8.3: uv run pytest tests/computation/ tests/orchestrator/
```

**Actual status:**
- **ruff would fail** on duplicate classes (code style issue)
- **mypy would fail** on undefined `_patch_simulation_builder` (type error)
- **pytest would fail** on empty test_openfisca_integration.py and undefined function
- **No evidence provided** that any of these commands were run

**Severity:** 🔴 **CRITICAL** — False claim of quality gate passage

**Fix:** Actually run the commands and provide output; fix failures before claiming completion.

---

## 🟠 Important Issues (AC/Task Implementation Gaps)

### 5. 🟠 HIGH: AC-7 (Group Entity Input Variables) — Zero Test Coverage

**Story claims:** "AC-7: Group entity input variables — Given a PopulationData with both membership columns on the person table AND separate group entity tables..."

**Implementation status:**
- ✓ Code exists (lines 794-815 in openfisca_api_adapter.py, step 5f)
- ❌ NO TESTS prove it works

**Evidence:**
- Story Task 4.6 claims: "Merge group entity table variables (if present)"
- Story Task 6.4 claims test: "Test: **group entity input variables** — menage table with `loyer` column. Verify the value appears in the entity dict..."
- **Actual test file:** Zero tests for this scenario

**Impact:** AC-7 is unverified. Could silently fail in production.

**Severity:** 🟠 **HIGH** — AC gap

**Fix:** Add test case (30 lines):
```python
def test_population_to_entity_dict_with_group_variables(self) -> None:
    """AC-7: Group entity table variables are merged into group instances."""
    adapter = OpenFiscaApiAdapter(
        output_variables=("income_tax",),
        skip_version_check=True,
    )
    mock_tbs = _make_mock_tbs_with_entities()
    
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
            "menage": pa.table({"loyer": pa.array([800.0])}),  # Group variable!
        },
    )
    
    result = adapter._population_to_entity_dict(
        population, 
        PolicyConfig(parameters={}, name="test"), 
        "2024", 
        mock_tbs
    )
    
    # Verify group variable merged into menage instance
    assert "menages" in result
    assert "menage_0" in result["menages"]
    assert "loyer" in result["menages"]["menage_0"]
    assert result["menages"]["menage_0"]["loyer"] == {"2024": 800.0}
```

---

### 6. 🟠 HIGH: AC-6 Backward Compatibility — Unverifiable Claims

**Story claims:** "Task 7: Verify backward compatibility (AC: #6)"
- 7.1: "Run ALL existing unit tests in test_openfisca_api_adapter.py — ensure all pass unchanged"
- 7.2: "Run ALL existing integration tests in test_openfisca_integration.py — ensure all pass unchanged"

**Actual status:**
- No proof provided that existing tests still pass
- Integration test file is empty, so there's nothing to verify
- The git diff shows massive refactoring to `_population_to_entity_dict()` (lines 760-950)
- How was backward compat verified if integration tests don't exist?

**Severity:** 🟠 **HIGH** — Unverifiable claim

**Fix:**
1. Create real integration tests that exercise pre-membership-column PopulationData
2. Run and document: `uv run pytest tests/computation/test_openfisca_integration.py -v`
3. Attach output to commit message

---

### 7. 🟠 HIGH: Role Cardinality Validation Missing

**Story Dev Notes specify:** "Each role entry should be a SimpleNamespace(key=..., plural=..., max=...)" with example `role.max` = 1, 2, or None (unlimited)

**Story Task 3 AC-4 says:** "Invalid role validation — check role value, list valid role values"

**Actual implementation:** `_validate_entity_relationships()` (lines 652-709) checks:
- ✓ Null values
- ✓ Role value is in valid set
- ❌ Does NOT check `role.max` cardinality

**Edge case:**
```python
# What if user passes more parents than allowed?
"famille_id": pa.array([0, 0, 0]),  # 3 people in same famille
"famille_role": pa.array(["parents", "parents", "parents"]),  # But famille.parents.max = 2!
```

**Impact:** Invalid multi-person groupings could pass validation when they should fail.

**Severity:** 🟠 **HIGH** — Incomplete AC implementation

**Fix:** Extend `_validate_entity_relationships()`:
```python
# After role value validation, add cardinality check:
role_counts: dict[str, int] = {}
for i in range(person_table.num_rows):
    group_id = id_array[i].as_py()
    role_key = role_array[i].as_py()
    key = f"{group_id}_{role_key}"
    role_counts[key] = role_counts.get(key, 0) + 1

# Check cardinality
for entity in tbs.entities:
    if getattr(entity, "is_person", False):
        continue
    for role in getattr(entity, "roles", []):
        role_dict_key = getattr(role, "plural", None) or getattr(role, "key", None)
        max_cardinality = getattr(role, "max", None)
        if max_cardinality is None:
            continue
        # Check violation...
```

---

### 8. 🟠 HIGH: Inefficient Null Checking — O(n) Row Iteration

**Location:** `_validate_entity_relationships()` lines 668-677 and 688-697

**Code:**
```python
null_mask = pa.compute.is_null(id_array)
if pa.compute.any(null_mask).as_py():
    for i in range(len(null_mask)):  # <-- O(n) iteration!
        if null_mask[i].as_py():
            raise ApiMappingError(...)
```

**Problem:**
- For 100k-row population, this iterates all 100k rows to find ONE null
- PyArrow has vectorized operations that can do this in O(1) or O(log n)

**Impact:** Performance issue on large populations

**Severity:** 🟠 **HIGH** — Performance footgun

**Fix:**
```python
null_mask = pa.compute.is_null(id_array)
if pa.compute.any(null_mask).as_py():
    # Find first null index using PyArrow
    null_indices = pa.compute.indices_nonzero(null_mask)
    first_null_index = null_indices[0].as_py() if len(null_indices) > 0 else 0
    
    raise ApiMappingError(
        summary="Null value in membership column",
        reason=f"Column '{id_col}' has null value at row index {first_null_index}...",
        ...
    )
```

---

## 🟡 Minor Issues (Code Quality & Coverage)

### 9. 🟡 MEDIUM: Edge Case — Non-Contiguous Group IDs Untested

**Dev Notes document:** "Edge case: Group ID values are not contiguous — e.g., `famille_id = [0, 2, 2]` (no famille 1)"

**Code handles it correctly** (line 789-790): `sorted_group_ids = sorted(unique_ids.to_pylist())`

**But:** NO TEST case for this scenario

**Severity:** 🟡 **MEDIUM** — Undocumented edge case behavior

**Fix:** Add test:
```python
def test_non_contiguous_group_ids(self) -> None:
    """Non-contiguous IDs (0, 2, 2) should work correctly."""
    # ...population with menage_id = [0, 2, 2]...
    result = adapter._population_to_entity_dict(...)
    assert "menage_0" in result["menages"]
    assert "menage_2" in result["menages"]
    assert "menage_1" not in result["menages"]  # Skip missing ID
```

---

### 10. 🟡 MEDIUM: String vs Int Group IDs — Mentioned But Untested

**Dev Notes:** "Edge case: String group IDs — `famille_id` column could be utf8 instead of int64"

**Code:** Supports both (generic handling via PyArrow)

**But:** NO TEST for string IDs

**Severity:** 🟡 **MEDIUM** — Type polymorphism undocumented

**Fix:** Add test for utf8 group IDs

---

### 11. 🟡 MEDIUM: Positional Matching Assumption in Step 5f — Could Fail Silently

**Story line ~803-810:**
```python
# Step 5f: Merge group entity table variables (if present)
# Positional match: row i of group table → sorted_group_ids[i]
# ⚠️ POSITIONAL MATCHING: row 0 of group table maps to the smallest distinct group ID...
# If rows are in a different order, values will be silently misassigned to the wrong group instances.
```

**Issue:**
- Story acknowledges: "This requires the group entity table rows to be ordered by ascending {entity_key}_id value — no automatic reordering is performed."
- Code does NOT validate sort order
- If caller passes unsorted group table, data corruption occurs silently (no error raised)
- This violates "data contracts fail loudly" principle

**Impact:** Silent data corruption if group tables aren't pre-sorted

**Severity:** 🟡 **MEDIUM** — Fragile assumption

**Fix:** Validate sort order:
```python
# After line 805 (after getting sorted_group_ids):
# Verify group_table rows are ordered by group ID
if group_table.num_rows > 0:
    # Get the ID column from group table if it exists
    # OR assume positional match and validate caller's responsibility
    # Better: require explicit ID column in group table for validation
    pass  # Document as caller responsibility in docstring
```

---

### 12. 🟡 MEDIUM: Missing import `numpy as np` in test file

**Test file uses:** `np.array()` in mock setup and assertions

**Imports:** The test file imports `pyarrow as pa` but NOT `numpy as np`

**Will cause:** `NameError: name 'np' is not defined` on any test that uses numpy arrays

**Severity:** 🟡 **MEDIUM** — Will cause test failures

**Fix:**
```python
import numpy as np  # Add this import
```

---

## 📊 Evidence Score Calculation

| Category | Issues | Severity | Points |
|----------|--------|----------|--------|
| Task Completion Lies | 2 | 🔴 CRITICAL | +6 |
| Missing Code | 1 | 🔴 CRITICAL | +3 |
| Duplicate Code | 1 | 🔴 CRITICAL | +3 |
| False Quality Claims | 1 | 🔴 CRITICAL | +3 |
| AC Implementation Gaps | 2 | 🟠 HIGH | +2 |
| Performance Issues | 1 | 🟠 HIGH | +1 |
| Unverifiable Claims | 1 | 🟠 HIGH | +1 |
| Untested Edge Cases | 3 | 🟡 MEDIUM | +0.9 |
| **Total** | **12** | — | **19.9** |

### Verdict: 🔴 **REJECT — MAJOR REWORK REQUIRED**

**Evidence Score: 19.9** (scale 0-10, where 10+ = REJECT)

This code cannot be merged:
1. Tests won't execute (missing function, duplicate classes, missing import)
2. Task completion claims are false (integration tests completely missing)
3. Critical ACs unverified (AC-7, AC-6)
4. Quality gates not actually run (false claim in Task 8)

---

## 🔧 Recommended Actions

### Immediate (Before Next Review):

1. **Delete all duplicate test classes** — Keep only one definition of each
2. **Implement `_patch_simulation_builder()` function** — Or replace with correct patch method
3. **Add `import numpy as np`** to test file
4. **Implement Task 6 integration tests** — All 6 test cases (≈150 lines)
5. **Add cardinality validation** to AC-4 implementation
6. **Optimize null checking** to use vectorized operations
7. **Run quality gates and attach proof** to commit message

### Secondary (Next Sprint):

8. Add edge case tests (non-contiguous IDs, string IDs)
9. Document positional matching assumption with validation
10. Add role cardinality metadata to test fixtures
11. Write integration tests for backward compatibility

---

## Summary for Lucas

Story 9.4 implementation has **critical blockers** that prevent merge:

- **12 issues identified** (4 CRITICAL, 4 HIGH, 4 MEDIUM)
- **Evidence Score 19.9** = REJECT
- **Cannot run tests** (undefined function, missing import, duplicates)
- **Task 6 completely unimplemented** (empty file; 0% done despite `[x]` mark)
- **Multiple AC gaps** (AC-7, AC-6 unverifiable)
- **False quality claims** (Task 8 asserts tests pass without proof)

**Recommendation:** Return to dev with feedback. Estimated rework: 4-6 hours to address blockers + 2-3 hours for secondary improvements.

]]></file>
<file id="557aedd2" path="[Validator B]" label="VALIDATION OUTPUT"><![CDATA[

---

# 🔥 ADVERSARIAL CODE REVIEW — Story 9.4: Define Population Data 4-Entity Format

**Reviewer:** BMad Adversarial Senior Dev  
**Date:** 2026-03-01  
**Story:** `_bmad-output/implementation-artifacts/9-4-define-population-data-4-entity-format.md`

---

## 📊 Review Summary

| Category | Issues Found |
|----------|--------------|
| Git vs Story Discrepancies | 0 |
| AC Implementation Gaps | 0 |
| Task Completion Lies | 0 |
| Critical Performance Bugs | 1 |
| Load-Bearing `assert` Violation | 1 |
| Hot-Path Performance Footguns | 3 |
| Silent Correctness Hazards | 1 |
| Governance Violations | 1 |
| **Total Issues** | **7** |

The AC coverage and test structure are solid — all 7 ACs are implemented, integration tests exist against real OpenFisca-France, and the edge-case test for non-contiguous IDs is present. **That said, the implementation ships a catastrophic O(n×g) performance bug that makes the feature unusable for any realistic population size.** The project's own NFR says 100k+ households must complete in seconds. The current code would take hours.

---

## Evidence Score Summary

| Severity | Finding | Source | Score |
|----------|---------|--------|-------|
| 🔴 CRITICAL | O(n×g) nested loop in Step 5e — catastrophic for 100k+ populations | `openfisca_api_adapter.py:880-890` | +3 |
| 🟠 IMPORTANT | `assert person_entity_plural is not None` (line 867) is load-bearing: stripped by `-O`, produces silent `result[None]` dict corruption | `openfisca_api_adapter.py:867` | +1 |
| 🟠 IMPORTANT | Step 5d person-building uses `column(col)[i].as_py()` inside Python loop — O(n×c) scalar-boxing allocations | `openfisca_api_adapter.py:862` | +1 |
| 🟠 IMPORTANT | Role validation iterates ALL n person records per entity instead of unique values — O(n) when O(u) where u≤4 | `openfisca_api_adapter.py:719-720` | +1 |
| 🟡 MINOR | Null-index discovery scans full null mask via Python for-loop `.as_py()` after `pa.compute.any()` already confirmed a null exists | `openfisca_api_adapter.py:674-693, 699-713` | +0.3 |
| 🟡 MINOR | Positional group-entity-table merge has no defensive log warning — wrong row order silently misassigns `loyer` values to wrong households | `openfisca_api_adapter.py:935-940` | +0.3 |
| 🟡 MINOR | Story status still `ready-for-dev` — repeat antipattern from 9.2 and 9.3 | `9-4-define-population-data-4-entity-format.md:3` | +0.3 |
| 🟢 CLEAN PASS | Security: no injection or exposure risks | — | −0.5 |
| 🟢 CLEAN PASS | Type safety: `from __future__ import annotations` correct throughout, all public types annotated | — | −0.5 |

### Evidence Score: **5.9 → MAJOR REWORK**

> The O(n×g) loop is a **merge blocker**. The feature literally cannot be used for its intended purpose. Fix that, replace the two `assert`s with proper exceptions, and this is APPROVED.

---

## ⚡ Performance & Scalability

### Issue 1 — 🔴 CRITICAL: O(n × g) Group Entity Building in Step 5e
**`openfisca_api_adapter.py:880–890`**

```python
# CURRENT — O(n × g) for n=persons, g=distinct groups
for group_id in sorted_group_ids:          # outer: g iterations
    role_assignments: dict[str, list[str]] = {}
    for i in range(person_table.num_rows):  # inner: n iterations
        if id_array[i].as_py() == group_id: # scalar-boxed comparison
            role_key = role_array[i].as_py()
            ...
```

**Real-world impact for a 100k-household French population:**
- ~250k persons (2.5/household average)
- 3 group entities (famille, foyer_fiscal, menage)
- **Total PyArrow `.as_py()` calls: 3 × 100k × 250k = 75 billion**
- At 10M Python ops/sec → **~7,500 seconds = 2+ hours** per `compute()` call

This violates the stated NFR: *"Full population simulation (100k+ households) completes in seconds, not minutes."* The feature is **unusable at any realistic scale**.

---

### Issue 3 — 🟠 IMPORTANT: Step 5d Column Access Inside Python Loop
**`openfisca_api_adapter.py:855–865`**

```python
for i in range(person_table.num_rows):      # n iterations
    for col in person_table.column_names:   # c column iterations
        value = person_table.column(col)[i].as_py()   # ← SLOW
```

`person_table.column(col)` re-fetches the column object every iteration (not cached). Then `[i].as_py()` boxes a scalar. For 250k persons × 8 columns = 2 million unnecessary Python-level allocations. The correct approach is to convert each column to a Python list **once** before the row loop.

---

### Issue 4 — 🟠 IMPORTANT: Role Validation Checks All n Records Instead of Unique Values
**`openfisca_api_adapter.py:719–720`**

```python
role_values = role_array.to_pylist()   # materialise ALL n person records
for value in role_values:              # iterate n times
    if value not in entity_valid_roles:
```

For 250k persons, this performs 250k Python string lookups. Valid roles per entity are at most 4 distinct values (`parents`, `enfants`, `declarants`, `personnes_a_charge`). Checking unique values reduces from O(n) to O(4). The fix is one line:

```python
unique_role_values = pa.compute.unique(role_array).to_pylist()  # O(n) once, gives ≤4 values
for value in unique_role_values:
```

---

### Issue 5 — 🟡 MINOR: Null Detection Scans Full Boolean Mask Element-by-Element
**`openfisca_api_adapter.py:674–693, 699–713`**

```python
if pa.compute.any(null_mask).as_py():       # vectorized check — good
    for i in range(len(null_mask)):          # ← Python loop defeats the point
        if null_mask[i].as_py():            # scalar-boxing per element
            raise ApiMappingError(...)
```

After `pa.compute.any()` confirms a null exists, the code does a Python-level linear scan to find its first index. PyArrow can do this in one vectorized call:

```python
if pa.compute.any(null_mask).as_py():
    indices = pa.compute.filter(pa.array(range(len(id_array))), null_mask)
    first_null = indices[0].as_py()   # single .as_py() call
    raise ApiMappingError(..., reason=f"Column '{id_col}' has null value at row index {first_null}")
```

---

## 🐛 Correctness & Safety

### Issue 2 — 🟠 IMPORTANT: Load-Bearing `assert` Stripped by Python Optimiser
**`openfisca_api_adapter.py:867`**

```python
assert person_entity_plural is not None
result[person_entity_plural] = person_dict   # ← if assert stripped, silently does result[None] = ...
```

The first `assert` at line 838 fails loudly anyway (next line raises `KeyError`), but **line 867 is different**: `result[None] = person_dict` silently succeeds in Python — a `None` key is perfectly legal in a dict. The entity dict passed to `SimulationBuilder.build_from_entities()` would contain a `None` key, causing a cryptic OpenFisca-side crash with no pointer back to this line.

Project rules are explicit: *"Subsystem-specific exceptions — each module defines its own error hierarchy; never raise bare Exception or ValueError for domain errors."* `assert` is the same category of violation. It **also** conflicts with the rule about "data contracts fail loudly" because `-O` (which strip `assert`) prevents the fail from happening at all, substituting silent corruption.

Both asserts must become `ApiMappingError` raises.

---

### Issue 6 — 🟡 MINOR: Silent Data Corruption via Unvalidated Positional Group Table Ordering
**`openfisca_api_adapter.py:935–940`**

```python
# Positional match: row i → sorted_group_ids[i]
for i, group_id in enumerate(sorted_group_ids):
    instance_id = f"{group_entity_key}_{group_id}"
    for col in group_table.column_names:
        value = group_table.column(col)[i].as_py()
        result[group_plural][instance_id][col] = {period_str: value}
```

If a caller passes a `menage` table where row 0 is `menage_id=5` and row 1 is `menage_id=3`, the sort gives `sorted_group_ids = [3, 5]`. Row 0 (data for menage 5) maps to `menage_3`, and row 1 (data for menage 3) maps to `menage_5`. **`loyer` values are silently swapped between households** — a tax computation error with no exception raised.

The story documents this as intentional but notes the risk. At minimum, a `logger.warning()` should fire to make the ordering assumption visible in logs. It would also be trivially fixable by sorting the group table before processing if it had an explicit index column.

---

## 🔧 Maintainability Issues

### Issue 7 — 🟡 MINOR: Story Status Not Updated (Third Time)
**`9-4-define-population-data-4-entity-format.md:3`**

```yaml
Status: ready-for-dev
```

The story is fully implemented. This is the **same governance violation as Stories 9.2 and 9.3**, both explicitly documented in the antipatterns file. After two successive cycles where the dev agent was told to update the status and still didn't, this is either ignored or the dev agent's session context doesn't include the antipatterns at implementation time. Either way: update to `Status: done` and check all tasks `[x]`.

---

## 🛠️ Suggested Fixes

### Fix 1 — O(n×g) → O(n): Step 5e Single-Pass Group Entity Building

**File:** `src/reformlab/computation/openfisca_api_adapter.py`  
**Lines:** 870–893

**Diff:**
```diff
-        group_dict: dict[str, Any] = {}
-        for group_id in sorted_group_ids:
-            # Collect row indices where id_col == group_id
-            role_assignments: dict[str, list[str]] = {}
-            for i in range(person_table.num_rows):
-                if id_array[i].as_py() == group_id:
-                    role_key = role_array[i].as_py()
-                    person_id = f"{person_table_key}_{i}"
-                    role_assignments.setdefault(role_key, []).append(person_id)
-
-            instance_id = f"{group_entity_key}_{group_id}"
-            group_dict[instance_id] = dict(role_assignments)
+        # Convert arrays to Python lists ONCE to avoid O(n×g) scalar-boxing.
+        # Single O(n) pass over all persons instead of one pass per distinct group ID.
+        id_list = id_array.to_pylist()
+        role_list = role_array.to_pylist()
+
+        # Re-derive sorted group IDs from the Python list (avoids second ToPyList call)
+        sorted_group_ids = sorted(set(id_list))
+
+        role_assignments_by_group: dict[Any, dict[str, list[str]]] = {}
+        for i, (gid, rkey) in enumerate(zip(id_list, role_list)):
+            person_id = f"{person_table_key}_{i}"
+            role_assignments_by_group.setdefault(gid, {}).setdefault(
+                rkey, []
+            ).append(person_id)
+
+        group_dict: dict[str, Any] = {}
+        for group_id in sorted_group_ids:
+            instance_id = f"{group_entity_key}_{group_id}"
+            group_dict[instance_id] = role_assignments_by_group.get(group_id, {})
```

This also eliminates the need for the earlier `pa.compute.unique` call (which was O(n) anyway), since `set(id_list)` is O(n) and gives you the same distinct IDs.

---

### Fix 2 — Step 5d: Amortise Column Extraction Outside Row Loop

**File:** `src/reformlab/computation/openfisca_api_adapter.py`  
**Lines:** 854–865

```diff
+        # Pre-materialise non-membership columns as Python lists once — avoid
+        # O(n×c) element-by-element scalar boxing inside the row loop.
+        var_columns = {
+            col: person_table.column(col).to_pylist()
+            for col in person_table.column_names
+            if col not in membership_col_names
+        }
+
         person_dict: dict[str, Any] = {}
         for i in range(person_table.num_rows):
             instance_id = f"{person_table_key}_{i}"
-            instance_data: dict[str, Any] = {}
-
-            for col in person_table.column_names:
-                if col in membership_col_names:
-                    continue
-                value = person_table.column(col)[i].as_py()
-                instance_data[col] = {period_str: value}
-
+            instance_data: dict[str, Any] = {
+                col: {period_str: vals[i]}
+                for col, vals in var_columns.items()
+            }
             person_dict[instance_id] = instance_data
```

---

### Fix 3 — Replace Both `assert` Statements with Proper `ApiMappingError`

**File:** `src/reformlab/computation/openfisca_api_adapter.py`

```diff
-        assert person_table_key is not None  # guaranteed by membership_cols being non-empty
+        if person_table_key is None:
+            raise ApiMappingError(
+                summary="Person entity table not found in population",
+                reason=(
+                    "Membership columns were detected but no table keyed by the "
+                    "person entity singular or plural name was found in population.tables."
+                ),
+                fix=(
+                    "Include the person entity table (e.g. 'individu' or 'individus') "
+                    "in PopulationData.tables."
+                ),
+                invalid_names=(),
+                valid_names=(),
+            )
         person_table = population.tables[person_table_key]
         ...
-        assert person_entity_plural is not None
+        if person_entity_plural is None:
+            raise ApiMappingError(
+                summary="Cannot determine person entity plural name",
+                reason=(
+                    "The person entity in the TaxBenefitSystem has no .plural attribute. "
+                    "This indicates an incompatible OpenFisca version or malformed TBS."
+                ),
+                fix="Check the OpenFisca compatibility matrix.",
+                invalid_names=(),
+                valid_names=(),
+            )
```

---

### Fix 4 — Role Validation: Check Unique Values Only

**File:** `src/reformlab/computation/openfisca_api_adapter.py`  
**Lines:** 719–720**Diff:**
```diff
-            role_values = role_array.to_pylist()
-            for value in role_values:
+            # Check unique role values only — typically ≤4 distinct roles
+            # regardless of population size (avoid O(n) scan over all persons).
+            for value in pa.compute.unique(role_array).to_pylist():
```

---

### Fix 5 — Null Detection: Vectorised First-Index Extraction

**File:** `src/reformlab/computation/openfisca_api_adapter.py`  
**Applies to:** both `id_col` (line 674) and `role_col` (line 699) null checks  

```diff
-            if pa.compute.any(null_mask).as_py():
-                # Find first null index
-                for i in range(len(null_mask)):
-                    if null_mask[i].as_py():
-                        raise ApiMappingError(
-                            summary="Null value in membership column",
-                            reason=(
-                                f"Column '{id_col}' has null value at "
-                                f"row index {i}. All membership columns "
+            if pa.compute.any(null_mask).as_py():
+                # Vectorised index extraction — single .as_py() call instead of n.
+                null_index_arr = pa.compute.filter(
+                    pa.array(range(len(id_array))), null_mask
+                )
+                first_null = null_index_arr[0].as_py()
+                raise ApiMappingError(
+                    summary="Null value in membership column",
+                    reason=(
+                        f"Column '{id_col}' has null value at "
+                        f"row index {first_null}. All membership columns "
```

*(Apply identically to the `role_col` null check at line 699, substituting `role_col` for `id_col`.)*

---

## Verdict: **MAJOR REWORK**

**Evidence Score: 5.9**

The blocking issue is Fix 1. None of the other fixes are merge-blockers individually, but Fixes 2–5 are important before this code touches a production-sized dataset. Specifically:

| Priority | Fix | Blocker? |
|----------|-----|---------|
| 🔴 P0 | Fix 1 — O(n×g) → O(n) Step 5e rewrite | **YES** |
| 🟠 P1 | Fix 2 — Step 5d column amortisation | No, but needed before 100k runs |
| 🟠 P1 | Fix 3 — Replace both `assert`s with `ApiMappingError` | No, but `-O` correctness risk |
| 🟠 P1 | Fix 4 — Role validation unique-values only | No, but needed before 100k runs |
| 🟡 P2 | Fix 5 — Null detection vectorisation | No |
| 🟡 P2 | Story status → `done` | No |

**Offer:** Approve Fix 1 and Fix 3 for auto-apply — both are targeted, mechanical, and safe. Fix 2 and Fix 4 can follow in the same PR. Reply `auto-fix 1 3` to apply immediately.

]]></file>
<file id="dc422a86" path="[git-diff]" label="VIRTUAL CONTENT"><![CDATA[

<!-- GIT_DIFF_START -->
 bmad-assist.yaml                                   |   59 +-
 src/reformlab/computation/openfisca_api_adapter.py |  841 ++++++++-
 src/reformlab/computation/types.py                 |   10 +-
 src/reformlab/computation/types.pyi                |    1 +
 tests/computation/test_openfisca_api_adapter.py    | 1799 +++++++++++++++++++-
 tests/computation/test_openfisca_integration.py    |  644 +++++++
 tests/computation/test_result.py                   |   83 +
 7 files changed, 3370 insertions(+), 67 deletions(-)

diff --git a/src/reformlab/computation/openfisca_api_adapter.py b/src/reformlab/computation/openfisca_api_adapter.py
index b32dd7f..12ccd2b 100644
--- a/src/reformlab/computation/openfisca_api_adapter.py
+++ b/src/reformlab/computation/openfisca_api_adapter.py
@@ -5,11 +5,26 @@ runs live tax-benefit calculations using OpenFisca's ``SimulationBuilder``.
 
 All OpenFisca imports are lazy since ``openfisca-core`` is an optional
 dependency.
+
+Story 9.2: Added entity-aware result extraction to correctly handle
+output variables belonging to different entity types (individu, menage,
+famille, foyer_fiscal).
+
+Story 9.3: Added periodicity-aware calculation dispatch. Monthly variables
+use ``calculate_add()`` to sum sub-period values; yearly and eternity
+variables use ``calculate()``. Period validation ensures valid 4-digit year.
+
+Story 9.4: Added 4-entity PopulationData format support. Membership columns
+on the person entity table (``{entity_key}_id`` and ``{entity_key}_role``)
+express entity relationships for multi-person populations. The adapter
+detects these columns, validates relationships, and produces a valid entity
+dict passable to ``SimulationBuilder.build_from_entities()``.
 """
 
 from __future__ import annotations
 
 import difflib
+import logging
 import time
 from typing import Any
 
@@ -22,6 +37,27 @@ from reformlab.computation.openfisca_common import (
 )
 from reformlab.computation.types import ComputationResult, PolicyConfig, PopulationData
 
+logger = logging.getLogger(__name__)
+
+# Story 9.3: Valid OpenFisca DateUnit periodicity values (StrEnum).
+# Sub-yearly periodicities use calculate_add(); year/eternity use calculate().
+_VALID_PERIODICITIES = frozenset({
+    "month", "year", "eternity", "day", "week", "weekday",
+})
+_CALCULATE_ADD_PERIODICITIES = frozenset({
+    "month", "day", "week", "weekday",
+})
+
+
+def _periodicity_to_method_name(periodicity: str) -> str:
+    """Map a DateUnit periodicity string to the OpenFisca calculation method name.
+
+    Single source of truth for the ``calculate`` vs ``calculate_add`` dispatch
+    decision. Sub-yearly periodicities (month, day, week, weekday) aggregate
+    via ``calculate_add``; year and eternity use ``calculate`` directly.
+    """
+    return "calculate_add" if periodicity in _CALCULATE_ADD_PERIODICITIES else "calculate"
+
 
 class OpenFiscaApiAdapter:
     """Adapter that executes OpenFisca computations via the Python API.
@@ -37,6 +73,14 @@ class OpenFiscaApiAdapter:
         output_variables: tuple[str, ...],
         skip_version_check: bool = False,
     ) -> None:
+        if not output_variables:
+            raise ApiMappingError(
+                summary="Empty output_variables",
+                reason="output_variables tuple is empty — no variables to compute",
+                fix="Provide at least one valid output variable name.",
+                invalid_names=(),
+                valid_names=(),
+            )
         self._country_package = country_package
         self._output_variables = output_variables
 
@@ -67,29 +111,75 @@ class OpenFiscaApiAdapter:
 
         Returns:
             A ``ComputationResult`` with output variables as a PyArrow Table.
+            When output variables span multiple entities, ``entity_tables``
+            contains per-entity tables keyed by entity plural name.
+
+        Raises:
+            ApiMappingError: If the period is invalid (not a 4-digit year
+                in range [1000, 9999]).
         """
+        # Story 9.3 AC-3: Period validation — FIRST check before any TBS operations.
+        self._validate_period(period)
+
         start = time.monotonic()
 
         tbs = self._get_tax_benefit_system()
         self._validate_output_variables(tbs)
 
+        # Story 9.2: Resolve entity grouping before building simulation (fail fast —
+        # avoid expensive SimulationBuilder.build_from_entities() if entity
+        # resolution fails due to incompatible country package).
+        vars_by_entity = self._resolve_variable_entities(tbs)
+
+        # Story 9.3 AC-1, AC-2, AC-6: Resolve periodicities before simulation
+        # (fail fast — detect unsupported periodicity values early).
+        var_periodicities = self._resolve_variable_periodicities(tbs)
+
         simulation = self._build_simulation(population, policy, period, tbs)
-        table = self._extract_results(simulation, period)
+        entity_tables = self._extract_results_by_entity(
+            simulation, period, vars_by_entity, var_periodicities
+        )
+
+        # Determine primary output_fields table for backward compatibility:
+        # - Single entity → that entity's table
+        # - Multiple entities → person-entity table (or first entity's table)
+        output_fields = self._select_primary_output(entity_tables, tbs)
 
         elapsed = time.monotonic() - start
 
+        # Only expose entity_tables for multi-entity results — keeps metadata
+        # consistent with entity_tables (single-entity uses {} for backward compat).
+        result_entity_tables = entity_tables if len(entity_tables) > 1 else {}
+        output_entities = sorted(result_entity_tables.keys())
+        entity_row_counts = {
+            entity: table.num_rows for entity, table in result_entity_tables.items()
+        }
+
+        # Story 9.3 AC-5: Build calculation methods mapping from periodicities.
+        # Uses _periodicity_to_method_name() — single source of truth for the
+        # calculate vs calculate_add dispatch decision.
+        calculation_methods: dict[str, str] = {
+            var_name: _periodicity_to_method_name(periodicity)
+            for var_name, periodicity in var_periodicities.items()
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
+                "variable_periodicities": dict(var_periodicities),
+                "calculation_methods": calculation_methods,
             },
+            entity_tables=result_entity_tables,
         )
 
     # ------------------------------------------------------------------
@@ -176,6 +266,152 @@ class OpenFiscaApiAdapter:
             suggestions=suggestions,
         )
 
+    # ------------------------------------------------------------------
+    # Story 9.3: Period validation and periodicity-aware dispatch
+    # ------------------------------------------------------------------
+
+    def _validate_period(self, period: int) -> None:
+        """Validate that the period is a 4-digit year in [1000, 9999].
+
+        Story 9.3 AC-3: Called as the FIRST operation in ``compute()``,
+        before any TBS queries or simulation construction.
+
+        Raises:
+            ApiMappingError: If the period is invalid.
+        """
+        if not (1000 <= period <= 9999):
+            raise ApiMappingError(
+                summary="Invalid period",
+                reason=(
+                    f"Period {period!r} is not a valid 4-digit year"
+                ),
+                fix=(
+                    "Provide a positive integer year in range [1000, 9999], "
+                    "e.g. 2024"
+                ),
+                invalid_names=(),
+                valid_names=(),
+            )
+
+    def _resolve_variable_periodicities(
+        self, tbs: Any
+    ) -> dict[str, str]:
+        """Detect the periodicity of each output variable from the TBS.
+
+        Story 9.3 AC-1, AC-2, AC-6: Queries
+        ``tbs.variables[var_name].definition_period`` for each output variable
+        to determine whether ``calculate()`` or ``calculate_add()`` should
+        be used.
+
+        Args:
+            tbs: The loaded TaxBenefitSystem.
+
+        Returns:
+            Dict mapping variable name to periodicity string
+            (e.g. ``{"salaire_net": "month", "irpp": "year"}``).
+
+        Raises:
+            ApiMappingError: If a variable's periodicity cannot be determined
+                or has an unexpected value.
+        """
+        periodicities: dict[str, str] = {}
+
+        for var_name in self._output_variables:
+            variable = tbs.variables.get(var_name)
+            if variable is None:
+                # Defensive — _validate_output_variables should have caught this.
+                raise ApiMappingError(
+                    summary="Cannot resolve variable periodicity",
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
+            definition_period = getattr(variable, "definition_period", None)
+            if definition_period is None:
+                raise ApiMappingError(
+                    summary="Cannot determine periodicity for variable",
+                    reason=(
+                        f"Variable '{var_name}' has no .definition_period "
+                        f"attribute in {self._country_package} TaxBenefitSystem"
+                    ),
+                    fix=(
+                        "This variable may not be properly defined in the "
+                        "country package. Check the variable definition."
+                    ),
+                    invalid_names=(var_name,),
+                    valid_names=tuple(sorted(tbs.variables.keys())),
+                )
+
+            # DateUnit is a StrEnum — string comparison works directly.
+            periodicity_str = str(definition_period)
+            if periodicity_str not in _VALID_PERIODICITIES:
+                raise ApiMappingError(
+                    summary="Unexpected periodicity for variable",
+                    reason=(
+                        f"Variable '{var_name}' has definition_period="
+                        f"'{periodicity_str}', expected one of: "
+                        f"{', '.join(sorted(_VALID_PERIODICITIES))}"
+                    ),
+                    fix=(
+                        "This may indicate an incompatible OpenFisca version. "
+                        "Check the OpenFisca compatibility matrix."
+                    ),
+                    invalid_names=(var_name,),
+                    valid_names=tuple(sorted(tbs.variables.keys())),
+                )
+
+            periodicities[var_name] = periodicity_str
+
+        logger.debug(
+            "variable_periodicities=%s output_variables=%s",
+            periodicities,
+            list(self._output_variables),
+        )
+
+        return periodicities
+
+    def _calculate_variable(
+        self,
+        simulation: Any,
+        var_name: str,
+        period_str: str,
+        periodicity: str,
+    ) -> Any:
+        """Dispatch to the correct OpenFisca calculation method.
+
+        Story 9.3 AC-1, AC-2, AC-6:
+        - ``"month"``, ``"day"``, ``"week"``, ``"weekday"``
+          → ``simulation.calculate_add(var, period)``
+        - ``"year"``, ``"eternity"``
+          → ``simulation.calculate(var, period)``
+
+        Args:
+            simulation: The OpenFisca simulation.
+            var_name: Variable name to compute.
+            period_str: Period string (e.g. "2024").
+            periodicity: The variable's definition_period string.
+
+        Returns:
+            numpy.ndarray of computed values.
+        """
+        method = _periodicity_to_method_name(periodicity)
+        logger.debug(
+            "var=%s periodicity=%s method=%s period=%s",
+            var_name, periodicity, method, period_str,
+        )
+        if method == "calculate_add":
+            return simulation.calculate_add(var_name, period_str)
+        else:
+            return simulation.calculate(var_name, period_str)
+
     def _validate_policy_parameters(self, policy: PolicyConfig, tbs: Any) -> None:
         """Check that all policy parameter keys are valid input variables."""
         if not policy.parameters:
@@ -266,6 +502,240 @@ class OpenFiscaApiAdapter:
 
         return simulation
 
+    # ------------------------------------------------------------------
+    # Story 9.4: 4-entity PopulationData format — membership columns
+    # ------------------------------------------------------------------
+
+    def _detect_membership_columns(
+        self,
+        person_table: pa.Table,
+        tbs: Any,
+    ) -> dict[str, tuple[str, str]]:
+        """Detect membership columns on the person entity table.
+
+        Story 9.4 AC-1, AC-3, AC-6: Checks for ``{entity.key}_id`` and
+        ``{entity.key}_role`` columns for each group entity in the TBS.
+
+        Args:
+            person_table: The person entity PyArrow table.
+            tbs: The loaded TaxBenefitSystem.
+
+        Returns:
+            Dict mapping group entity key to ``(id_column, role_column)`` tuple.
+            Empty dict if no membership columns are detected (backward compat).
+
+        Raises:
+            ApiMappingError: If membership columns are incomplete (all-or-nothing)
+                or unpaired (_id without _role or vice versa).
+        """
+        col_names = set(person_table.column_names)
+
+        # Identify group entities from TBS
+        group_entity_keys: list[str] = []
+        for entity in tbs.entities:
+            if not getattr(entity, "is_person", False):
+                group_entity_keys.append(entity.key)
+
+        # Check for membership column presence
+        detected: dict[str, tuple[str, str]] = {}
+        has_any_id = False
+        has_any_role = False
+        unpaired: list[str] = []
+        present_pairs: list[str] = []
+        missing_pairs: list[str] = []
+
+        for entity_key in group_entity_keys:
+            id_col = f"{entity_key}_id"
+            role_col = f"{entity_key}_role"
+            has_id = id_col in col_names
+            has_role = role_col in col_names
+
+            if has_id:
+                has_any_id = True
+            if has_role:
+                has_any_role = True
+
+            if has_id and has_role:
+                detected[entity_key] = (id_col, role_col)
+                present_pairs.append(entity_key)
+            elif has_id and not has_role:
+                unpaired.append(
+                    f"'{id_col}' present but '{role_col}' missing"
+                )
+            elif has_role and not has_id:
+                unpaired.append(
+                    f"'{role_col}' present but '{id_col}' missing"
+                )
+            else:
+                missing_pairs.append(entity_key)
+
+        # No membership columns at all → backward compatible
+        if not has_any_id and not has_any_role:
+            return {}
+
+        # Unpaired columns: _id without _role or vice versa
+        if unpaired:
+            raise ApiMappingError(
+                summary="Unpaired membership column",
+                reason=(
+                    f"Membership columns must come in pairs "
+                    f"({{entity_key}}_id + {{entity_key}}_role). "
+                    f"Found: {'; '.join(unpaired)}"
+                ),
+                fix=(
+                    "Add the missing paired column for each membership column. "
+                    "Both _id and _role are required for each group entity."
+                ),
+                invalid_names=tuple(unpaired),
+                valid_names=tuple(
+                    f"{ek}_id, {ek}_role" for ek in group_entity_keys
+                ),
+            )
+
+        # All-or-nothing: if any membership columns exist, all group entities
+        # must have complete pairs
+        if missing_pairs:
+            raise ApiMappingError(
+                summary="Incomplete entity membership columns",
+                reason=(
+                    f"Found membership columns for: "
+                    f"{', '.join(present_pairs)}. "
+                    f"Missing membership columns for: "
+                    f"{', '.join(missing_pairs)}. "
+                    f"All group entities must have _id and _role columns "
+                    f"when any membership columns are present."
+                ),
+                fix=(
+                    f"Add {{entity_key}}_id and {{entity_key}}_role columns "
+                    f"for: {', '.join(missing_pairs)}"
+                ),
+                invalid_names=tuple(missing_pairs),
+                valid_names=tuple(group_entity_keys),
+            )
+
+        return detected
+
+    def _resolve_valid_role_keys(
+        self,
+        tbs: Any,
+    ) -> dict[str, frozenset[str]]:
+        """Build a mapping of entity key → valid role keys from the TBS.
+
+        Story 9.4 AC-4: Uses ``role.plural or role.key`` to match the dict
+        keys expected by ``SimulationBuilder.build_from_entities()``.
+
+        Args:
+            tbs: The loaded TaxBenefitSystem.
+
+        Returns:
+            Dict mapping group entity key to frozenset of valid role keys.
+        """
+        valid_roles: dict[str, frozenset[str]] = {}
+
+        for entity in tbs.entities:
+            if getattr(entity, "is_person", False):
+                continue
+
+            role_keys: set[str] = set()
+            roles = getattr(entity, "roles", ())
+            for role in roles:
+                plural = getattr(role, "plural", None)
+                key = getattr(role, "key", None)
+                role_dict_key = plural or key
+                if role_dict_key:
+                    role_keys.add(role_dict_key)
+
+            valid_roles[entity.key] = frozenset(role_keys)
+
+        return valid_roles
+
+    def _validate_entity_relationships(
+        self,
+        person_table: pa.Table,
+        membership_cols: dict[str, tuple[str, str]],
+        valid_roles: dict[str, frozenset[str]],
+    ) -> None:
+        """Validate membership column values for nulls and invalid roles.
+
+        Story 9.4 AC-3, AC-4, AC-5: Checks every membership column for null
+        values and validates role values against the TBS role definitions.
+
+        Args:
+            person_table: The person entity PyArrow table.
+            membership_cols: Detected membership columns per group entity.
+            valid_roles: Valid role keys per group entity.
+
+        Raises:
+            ApiMappingError: If null values or invalid role values are found.
+        """
+        for entity_key, (id_col, role_col) in membership_cols.items():
+            # AC-5: Null check on _id column
+            id_array = person_table.column(id_col)
+            null_mask = pa.compute.is_null(id_array)

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
<var name="session_id">5b8e53a8-ac6a-459b-aaff-1a772c8a5f8d</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_file" file_id="bc34e66e">embedded in prompt, file id: bc34e66e</var>
<var name="story_id">9.4</var>
<var name="story_key">9-4-define-population-data-4-entity-format</var>
<var name="story_num">4</var>
<var name="story_title">define-population-data-4-entity-format</var>
<var name="template">False</var>
<var name="timestamp">20260301_2254</var>
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
      - Commit message format: fix(component): brief description (synthesis-9.4)
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