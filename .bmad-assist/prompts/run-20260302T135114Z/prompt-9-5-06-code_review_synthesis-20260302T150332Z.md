<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 9 -->
<!-- Story: 5 -->
<!-- Phase: code-review-synthesis -->
<!-- Timestamp: 20260302T150332Z -->
<compiled-workflow>
<mission><![CDATA[

Master Code Review Synthesis: Story 9.5

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

<!-- TRUNCATED: Content exceeded token budget. See full document for details. -->

]]></file>
<file id="6ee5fa3d" path="_bmad-output/implementation-artifacts/9-5-openfisca-france-reference-test-suite.md" label="STORY FILE"><![CDATA[


# Story 9.5: OpenFisca-France Reference Test Suite

Status: in-dev

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

- [x] Task 1: Define reference test scenarios and compute expected values (AC: #1, #3)
  - [x] 1.1 Reference values computed analytically from OpenFisca-France 175.0.18 / openfisca-core 44.2.2 YAML parameters (barème, decote, QF plafonnement). Cross-verified against 3 existing test cases (20k→-150, 50k→-6665, couple 30k+25k→-2765) which all match exactly
  - [x] 1.2 Single-person reference values: 0→0.0, 15000→0.0, 30000→-1588.0, 75000→-13415.0, 100000→-20845.0
  - [x] 1.3 Family reference values: couple 40k+30k→-5231.0, family 1 child→-3768.0, family 2 children→-3085.0
  - [x] 1.4 Multi-entity output: range/sign checks rather than pinned values (salaire_net, irpp, revenu_disponible)
  - [x] 1.5 All values documented in class-level REFERENCE_VALUES dict with version, date, and tolerance

- [x] Task 2: Implement single-person income tax reference cases via `adapter.compute()` (AC: #1, #3, #4)
  - [x] 2.1 Created `TestAdapterReferenceSinglePerson` class with full docstring
  - [x] 2.2 Added ABSOLUTE_ERROR_MARGIN=0.5, REFERENCE_OPENFISCA_FRANCE_VERSION="175.0.18", REFERENCE_DATE="2026-03-02"
  - [x] 2.3 Implemented 5 parametric test methods (zero_income, low_income_near_smic, mid_income, upper_bracket, high_income) with structured assertion messages
  - [x] 2.4 Added progressive_tax_monotonicity structural test
  - [x] 2.5 All tests marked with @pytest.mark.integration

- [x] Task 3: Implement family reference cases via `adapter.compute()` with 4-entity format (AC: #1, #3, #4, #5)
  - [x] 3.1 Created `TestAdapterReferenceFamilies` class with full docstring and class attributes
  - [x] 3.2 Married couple test: 2 persons with membership columns, joint irpp vs reference
  - [x] 3.3 Family with 1 child: 3 persons, child as personnes_a_charge/enfants, 2.5 parts QF
  - [x] 3.4 Family with 2 children: 4 persons, 3 parts QF
  - [x] 3.5 Quotient familial structural invariant: family < couple at same income

- [x] Task 4: Implement 4-entity format cross-validation (AC: #5)
  - [x] 4.1 Created `TestFourEntityCrossValidation` class
  - [x] 4.2 Couple vs two singles QF benefit cross-validation (80k+0k asymmetric)
  - [x] 4.3 Single person with/without membership columns → identical results
  - [x] 4.4 All tests use adapter.compute() exclusively

- [x] Task 5: Implement multi-entity output reference cases (AC: #4, #6)
  - [x] 5.1 Created `TestAdapterReferenceMultiEntity` class
  - [x] 5.2 Single-person multi-entity: 3 entity keys, array lengths, value ranges, calculation_methods metadata
  - [x] 5.3 Married couple multi-entity: 2 individus, 1 foyer, 1 menage, correct variable assignment
  - [x] 5.4 Two independent households: all entity tables have 2 rows, ordering invariants

- [x] Task 6: Add regression detection metadata (AC: #3)
  - [x] 6.1 Added `reference_irpp_adapter` and `reference_multi_entity_adapter` module-scope fixtures
  - [x] 6.2 Added `test_openfisca_core_version_documented` (44.x) and `test_openfisca_france_version_documented` (175.x) version-pinned tests
  - [x] 6.3 All assertion messages follow structured format: expected, actual, tolerance, ref version
  - [x] 6.4 REFERENCE_DATE = "2026-03-02" on all reference test classes

- [ ] Task 7: Verify backward compatibility (AC: #7)
  - [ ] 7.1 Run ALL existing integration tests unchanged: `uv run pytest tests/computation/test_openfisca_integration.py -m integration`
  - [x] 7.2 No imports added or removed — all new code uses existing imports
  - [x] 7.3 Existing `TestOpenFiscaFranceReferenceCases` class NOT modified

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

Claude Opus 4.6 (via create-story and dev-story workflows)

### Debug Log References

- Sandbox blocked all `uv run` and Python execution commands throughout implementation
- Reference values computed analytically from YAML parameter files instead of running OpenFisca directly
- Cross-verified analytical values against 3 existing test data points (all matched exactly)

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
- **Implementation complete (Tasks 1-6):** 5 new test classes with 17 test methods added to test_openfisca_integration.py (828 lines)
- **Reference values analytically computed** from 2024 barème (11497/29315/83823/180294), 10% professional abattement (min 495, max 14171), decote (seuil_celib=889, seuil_couple=1470, taux=0.4525), and quotient familial (cap 1791/demi-part)
- **Pending validation:** Tasks 7-8 (test execution, quality gates) require manual execution due to sandbox limitations. Reference values may need adjustment within ±0.5 tolerance if OpenFisca's internal rounding differs from analytical computation

### Change Log

- `tests/computation/test_openfisca_integration.py` — Added 828 lines:
  - Module docstring updated (added Story 9.5 reference)
  - `reference_irpp_adapter()` fixture (module scope, irpp-only output)
  - `reference_multi_entity_adapter()` fixture (module scope, 3 output variables)
  - `TestAdapterReferenceSinglePerson` — 6 test methods (zero/low/mid/upper/high income + monotonicity)
  - `TestAdapterReferenceFamilies` — 4 test methods (couple, 1 child, 2 children, QF structural invariant)
  - `TestFourEntityCrossValidation` — 2 test methods (single cross-val, couple vs singles QF benefit)
  - `TestAdapterReferenceMultiEntity` — 3 test methods (single/couple/independent multi-entity output)
  - `TestRegressionDetectionMetadata` — 2 test methods (core version, france version)

### File List

- `tests/computation/test_openfisca_integration.py` — modified (added 5 test classes, 2 fixtures, 17 test methods, 828 lines)


]]></file>
<file id="895c54dc" path="tests/computation/test_openfisca_integration.py" label="SOURCE CODE"><![CDATA[

from __future__ import annotations
from pathlib import Path
from typing import Any
import pyarrow as pa
import pytest
from reformlab.computation.ingestion import DataSchema
from reformlab.computation.mapping import apply_output_mapping, load_mapping
from reformlab.computation.openfisca_api_adapter import OpenFiscaApiAdapter
from reformlab.computation.quality import validate_output
from reformlab.computation.types import ComputationResult, PolicyConfig, PopulationData
    from openfisca_core.simulation_builder import SimulationBuilder
        from openfisca_core.simulation_builder import SimulationBuilder
        from openfisca_core.simulation_builder import SimulationBuilder
        from openfisca_core.simulation_builder import SimulationBuilder
        from openfisca_core.simulation_builder import SimulationBuilder
        from openfisca_core.simulation_builder import SimulationBuilder
        from openfisca_core.errors import SituationParsingError
        from openfisca_core.simulation_builder import SimulationBuilder
        from openfisca_core.simulation_builder import SimulationBuilder
        import importlib.metadata

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


class TestVariablePeriodicityHandling:  # ...

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


    def test_mixed_periodicity_compute(  # ...

    def test_monthly_variable_end_to_end(self, tbs: Any) -> None:  # ...

    def test_periodicity_metadata_in_integration(  # ...

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


class TestFourEntityPopulationFormat:  # ...

    def _assert_irpp(  # ...

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

## Story 9-4 (2026-03-01)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | O(n×g) nested loop in Step 5e builds group entity instances with an outer loop over distinct group IDs and an inner Python loop over all n person rows, calling `.as_py()` per element. For 250k persons × 100k households = 25 billion scalar-boxing operations at ~10M ops/sec ≈ 2+ hours per `compute()` call. Violates NFR: "100k+ households in seconds." | Replaced with single-pass O(n) approach: materialise `id_array` and `role_array` to Python lists once each, then build `role_assignments_by_group` in one `enumerate(zip(...))` iteration, eliminating all per-group inner scans. |
| high | `assert person_entity_plural is not None` at line 867 is load-bearing but stripped by Python's `-O` flag. Failure mode is `result[None] = person_dict` — a `None` key is legal in Python dicts, silently passes, and produces a malformed entity dict that causes a cryptic crash inside `SimulationBuilder.build_from_entities()`. Violates "data contracts fail loudly" principle. | Replaced both `assert` statements (lines 838 and 867) with explicit `ApiMappingError` raises with diagnostic `summary`, `reason`, and `fix` fields. |
| high | `assert person_table_key is not None` at line 838 is also load-bearing — while its failure produces a `KeyError` (not silent), `assert` still violates project rules ("never raise bare Exception or ValueError for domain errors"). | Replaced with `ApiMappingError("Person entity table not found in population")`. |
| high | Step 5d column access inside Python row loop — `person_table.column(col)[i].as_py()` called O(n×c) times (n = person count, c = variable columns). For 250k persons × 8 columns = 2M scalar-boxing allocations vs. c column-level `.to_pylist()` calls. | Pre-materialise all non-membership columns as Python lists in a dict-comprehension outside the row loop; row loop becomes a single dict comprehension over pre-computed lists. |
| high | Role validation calls `role_array.to_pylist()` and iterates all n person records to check role values. For 250k persons this is 250k string lookups when the valid set has ≤4 distinct values. | Replaced with `pa.compute.unique(role_array).to_pylist()` — checks only distinct role values (O(u), u ≤ 4) instead of O(n). |
| medium | Null-index discovery after `pa.compute.any()` uses a Python for-loop with per-element `.as_py()` boxings. While only triggered on the error path, the pattern defeats the purpose of using PyArrow's vectorized operations. | Replaced with `pa.compute.filter(pa.array(range(n)), null_mask)` to get null positions vectorized, then single `.as_py()` call to extract `first_null` index. |
| low | Step 5f positional group-table merge makes an implicit ordering assumption (group table rows must be sorted by ascending group ID) with no observability. If a caller passes an unsorted group table, `loyer` values are silently swapped between households — no exception raised. | Added `logger.warning()` with structured key=value format logging the assumption, entity key, table key, and sorted IDs — makes the assumption visible in logs. |
| low | Story `Status: ready-for-dev` — third consecutive antipattern after Stories 9.2 and 9.3. | Updated to `Status: done`, added code review synthesis notes to Dev Agent Record. |


]]></file>
<file id="1d910d88" path="[Validator A]" label="VALIDATION OUTPUT"><![CDATA[

# 🔥 ADVERSARIAL CODE REVIEW: Story 9.5 - OpenFisca-France Reference Test Suite

**Date:** 2026-03-02 | **Severity:** MAJOR REWORK REQUIRED | **Status:** ⛔ BLOCKED

---

## 📋 Executive Summary

Story 9.5 claims to add a comprehensive reference test suite for the OpenFisca adapter. However, **the source code provided is TRUNCATED and incomplete**, preventing full verification of 7 Acceptance Criteria and 8 Tasks. The visible portions show **9 critical and high-severity issues** that must be addressed before merge.

**Evidence Score: 8.2/10** → **VERDICT: MAJOR REWORK REQUIRED**

------

## 🚨 CRITICAL FINDINGS

### **CRITICAL #1: Source Code File is TRUNCATED - Cannot Fully Review**

**Severity:** 🔴 CRITICAL (blocks verification of all ACs)

The provided source file ends abruptly with:
```python
<!-- TRUNCATED: Content exceeded token budget. See full document for details. -->
```

**Impact:**
- Cannot verify AC-1 through AC-7 completeness
- Cannot verify Tasks 1-6 implementation details
- Full `TestAdapterReferenceSinglePerson`, `TestAdapterReferenceFamilies`, `TestFourEntityCrossValidation`, `TestAdapterReferenceMultiEntity`, `TestRegressionDetectionMetadata` classes are **not visible for review**
- Cannot validate reference values are actually pinned in code

**Fix:** Provide complete, untruncated `tests/computation/test_openfisca_integration.py` file for full review.

---

### **CRITICAL #2: Duplicate Test Methods - AC-7 Violation**

**Severity:** 🔴 CRITICAL (violates AC-7 "Existing tests unbroken")

**File:** `tests/computation/test_openfisca_integration.py`

The visible code shows **EXACT DUPLICATES** of test methods in multiple test classes:

```python
# TestTaxBenefitSystemLoading - lines visible
def test_adapter_instantiates_without_error(self) -> None:  # FIRST
    """AC-2: OpenFiscaApiAdapter with openfisca_france instantiates successfully."""
    a = OpenFiscaApiAdapter(...)
    assert a is not None

# ... later in same class ...

def test_adapter_instantiates_without_error(self) -> None:  # DUPLICATE!
    """AC-2: OpenFiscaApiAdapter with openfisca_france instantiates successfully."""
    a = OpenFiscaApiAdapter(...)
    assert a is not None
```

**Duplicates found in:**
- `TestTaxBenefitSystemLoading.test_adapter_instantiates_without_error()` - **appears 2x**
- `TestTaxBenefitSystemLoading.test_version_returns_valid_string()` - **appears 2x**
- `TestTaxBenefitSystemLoading.test_tbs_loads_lazily_and_is_cached()` - **appears 2x**
- Similar duplicates in `TestAdapterComputeEndToEnd`, `TestMultiEntityPopulation`, `TestVariableMappingRoundTrip`, `TestOutputQualityValidation`, `TestKnownValueBenchmark`, `TestAdapterPluralKeyFix`

**Impact:**
- **AC-7 VIOLATED:** "Given all pre-existing integration tests, when the reference test suite is added, then no existing tests are modified or broken."
- Copy-paste errors indicate careless code review
- Pytest will skip duplicate method names (only last definition survives)
- Wastes test execution time
- Suggests merge conflicts were not properly resolved

**Fix:** Remove all duplicate test method definitions. Keep only one copy of each.

---

### **CRITICAL #3: Incomplete Test Class Implementations**

**Severity:** 🔴 CRITICAL (untestable code submitted)

**File:** `tests/computation/test_openfisca_integration.py`

The visible code shows **multiple test classes with incomplete implementations**:

```python
class TestFourEntityPopulationFormat:  # ... [line from source]
    def test_married_couple_via_membership_columns(self, tbs: Any) -> None:
        """AC-1, AC-2: Married couple via membership columns..."""
        # [rest of file truncated - no implementation visible]
```

Also incomplete in the visible code:
- `TestAdapterReferenceSinglePerson` class - skeleton only
- `TestAdapterReferenceFamilies` - methods show only doc strings
- `TestFourEntityCrossValidation` - incomplete
- `TestAdapterReferenceMultiEntity` - incomplete
- `TestRegressionDetectionMetadata` - incomplete

These classes are **core to Story 9.5 ACs** (AC-1, AC-2, AC-3, AC-4, AC-5, AC-6) but implementations are **not visible or incomplete**.

**Impact:**
- Story claims "Implementation complete (Tasks 1-6)" but the most important test classes are not fully shown
- Cannot verify reference values are actually pinned with correct tolerance metadata
- AC-1, AC-2, AC-3 implementation status **UNKNOWN**
- AC-4, AC-5, AC-6 implementation status **UNKNOWN**

**Fix:** Provide complete implementations of all 5 reference test classes with actual test method bodies (not truncated).

---

### **CRITICAL #4: Tasks 7-8 Explicitly Marked [ ] NOT DONE**

**Severity:** 🔴 CRITICAL (story incomplete)

**File:** `tests/computation/test_openfisca_integration.py`

From the story file:
```
- [ ] Task 7: Verify backward compatibility (AC: #7)
  - [ ] 7.1 Run ALL existing integration tests unchanged: `uv run pytest tests/computation/test_openfisca_integration.py -m integration`
  - [x] 7.2 No imports added or removed — all new code uses existing imports
  - [x] 7.3 Existing `TestOpenFiscaFranceReferenceCases` class NOT modified

- [ ] Task 8: Run quality gates (all ACs)
  - [ ] 8.1 `uv run ruff check src/ tests/`
  - [ ] 8.2 `uv run mypy src/`
  - [ ] 8.3 `uv run pytest tests/computation/ -m integration` (all integration tests pass)
  - [ ] 8.4 `uv run pytest tests/computation/ -m "not integration"` (all unit tests still pass)
  - [ ] 8.5 `uv run pytest tests/orchestrator/` (no orchestrator regressions)
```

Dev Notes state: **"Pending validation: Tasks 7-8 (test execution, quality gates) require manual execution due to sandbox limitations."**

**Impact:**
- Story is **NOT COMPLETE** - two entire task groups remain unverified
- Backward compatibility **UNVERIFIED** - could have broken existing tests
- Quality gates **UNVERIFIED** - code may not pass ruff/mypy
- **AC-2 (CI integration) UNVERIFIED** - tests may not pass in CI
- Story should be marked `Status: pending-validation` not `Status: in-dev`

**Fix:** Execute Tasks 7 and 8 completely before submitting:
```bash
uv run pytest tests/computation/test_openfisca_integration.py -m integration
uv run ruff check src/ tests/
uv run mypy src/
```

---

## 🟠 HIGH-SEVERITY FINDINGS

### **HIGH #5: Missing @pytest.fixture Decorator**

**Severity:** 🟠 HIGH (non-functional fixture)

**File:** `tests/computation/test_openfisca_integration.py`, line ~1400 (in git diff context)

```python
def reference_multi_entity_adapter() -> OpenFiscaApiAdapter:  # ❌ NO @pytest.fixture!
    """Adapter for multi-entity output reference tests via adapter.compute()."""
    return OpenFiscaApiAdapter(...)
```

**Impact:**
- This is a **plain function, not a pytest fixture**
- Tests that reference `reference_multi_entity_adapter` as a parameter will **fail with `FixtureLookupError`**
- AC-5 tests ("4-entity format cross-validation") likely **cannot run**
- AC-6 tests ("Multi-entity output validation") likely **cannot run**

**Fix:**
```python
@pytest.fixture(scope="module")  # ← ADD THIS
def reference_multi_entity_adapter() -> OpenFiscaApiAdapter:
    """Adapter for multi-entity output reference tests via adapter.compute()."""
    return OpenFiscaApiAdapter(...)
```

---

### **HIGH #6: AC-7 "Existing Tests Unbroken" - Duplicates Violate This**

**Severity:** 🟠 HIGH (AC violation + unverified)

Acceptance Criterion #7 states:
> "Given all pre-existing integration tests in `test_openfisca_integration.py`, when the reference test suite is added, then no existing tests are modified or broken."

But the code shows:
1. **Duplicate test methods** (CRITICAL #2) → These are "modified" duplicates
2. **No verification** that existing tests still pass (Task 7 not done)

**Impact:**
- AC-7 **VIOLATED** or **UNVERIFIED**
- Cannot confirm backward compatibility

**Fix:** Remove duplicates AND run Task 7 verification.

---

### **HIGH #7: Reference Values "May Need Adjustment" - Not Validated**

**Severity:** 🟠 HIGH (AC-1 at risk)

**File:** Story dev notes + git diff

From Dev Notes:
> "**Pending validation:** Reference values may need adjustment within ±0.5 tolerance if OpenFisca's internal rounding differs from analytical computation"

From Task 1 completion notes:
> "1.1 Reference values computed analytically from OpenFisca-France 175.0.18"

**But:**
- Reference values are documented in story but **NOT VERIFIED** against actual OpenFisca output
- The analytical computation (from YAML parameters) may differ from OpenFisca's internal calculations
- Story claims ±0.5 EUR tolerance but this is NOT documented in test code visible

**Impact:**
- AC-1 ("Known-value validation") may be **UNVERIFIED**
- Reference tests may fail or have wrong expected values once run
- No evidence that actual OpenFisca output was cross-checked

**Fix:** 
1. Run Story 9.5 tests against real OpenFisca-France 175.0.18
2. Document any value discrepancies  
3. Adjust expected values if actual OpenFisca output differs
4. Verify all values pass with ±0.5 tolerance

---

## 🟡 MODERATE-SEVERITY FINDINGS

### **MEDIUM #8: Inconsistent Implementation Status**

**Severity:** 🟡 MEDIUM (transparency + completeness issue)

The story shows contradictory status:

```yaml
Dev Agent Record - Completion Notes:
  - "Implementation complete (Tasks 1-6): ... added 5 new test classes with 17 test methods"

But Task List shows:
  - [x] Task 1-6: All marked complete
  - [ ] Task 7: EXPLICITLY INCOMPLETE
  - [ ] Task 8: EXPLICITLY INCOMPLETE
```

**Problem:** Story submits "implementation complete" but explicitly acknowledges 2/8 tasks are pending.

**Impact:**
- Story should not be marked `status: in-dev` if tasks are genuinely incomplete
- Code review blocked on verification of Tasks 7-8

**Fix:** Either:
1. Complete Tasks 7-8 before submission, OR
2. Mark story as `status: pending-validation` and explain what's blocked

---

### **MEDIUM #9: Reference Test Fixtures Overlap with Existing Fixtures**

**Severity:** 🟡 MEDIUM (potential test isolation issues)

**File:** `tests/computation/test_openfisca_integration.py`

Story claims new fixtures:
- `reference_irpp_adapter()` - new
- `reference_multi_entity_adapter()` - new

But existing fixtures already exist:
- `adapter()` - uses `OpenFiscaApiAdapter` with `output_variables=("impot_revenu_restant_a_payer",)`
- `multi_entity_adapter()` - uses `OpenFiscaApiAdapter` with mixed entities
- `periodicity_adapter()` - uses mixed periodicities

**Questions:**
- What's the difference between `adapter()` and `reference_irpp_adapter()`?
- What's the difference between `multi_entity_adapter()` and `reference_multi_entity_adapter()`?
- Why create new fixtures instead of reusing existing ones?

**Impact:**
- Code duplication in fixture layer
- Test isolation may be unclear
- Maintenance burden - fixture changes must be synchronized

**Fix:** Document the differences between reference fixtures and existing fixtures, OR consolidate them.

---

## 📊 Evidence Score Breakdown

| Category | Issues | Score |
|----------|--------|-------|
| **CRITICAL** (3 issues × +3) | Source truncation, Duplicate tests, Incomplete classes | +9 |
| **Tasks not done** (Tasks 7-8 × +2) | Unverified backward compatibility, unverified quality gates | +4 |
| **HIGH** (3 issues × +1) | Missing fixture decorator, AC-7 unverified, Values unvalidated | +3 |
| **MEDIUM** (2 issues × +0.3) | Status inconsistency, Fixture overlap | +0.6 |
| **Clean Pass** (4 categories × -0.5) | Code structure, import organization, documentation exists, error handling reasonable | -2.0 |
| **TOTAL EVIDENCE SCORE** | | **14.6** |

**VERDICT: 🔴 REJECT - Critical issues block merge**

---

## 🔧 Mandatory Fixes (Required Before Merge)

### **FIX #1: Obtain Complete Source Code**
```bash
# Get full test file for review
wc -l tests/computation/test_openfisca_integration.py
# Should be ~2500+ lines based on git diff showing +1472 lines
```

**Action:** Provide untruncated source code file.

---

### **FIX #2: Remove Duplicate Test Methods**

Replace all duplicate methods. Example for `TestTaxBenefitSystemLoading`:

```python
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
    # ← END CLASS - NO DUPLICATE METHODS
```

---

### **FIX #3: Add Missing @pytest.fixture Decorator**

```python
@pytest.fixture(scope="module")  # ← ADD THIS LINE
def reference_multi_entity_adapter() -> OpenFiscaApiAdapter:
    """Adapter for multi-entity output reference tests via adapter.compute()."""
    return OpenFiscaApiAdapter(
        country_package="openfisca_france",
        output_variables=(
            "salaire_net",
            "impot_revenu_restant_a_payer",
            "revenu_disponible",
        ),
    )
```

---

### **FIX #4: Complete Tasks 7-8**

Before submitting, run:

```bash
# Task 7.1: Backward compatibility verification
uv run pytest tests/computation/test_openfisca_integration.py -m integration -v

# Task 8: Quality gates
uv run ruff check src/ tests/ --fix
uv run mypy src/
uv run pytest tests/computation/ -m integration
uv run pytest tests/computation/ -m "not integration"
uv run pytest tests/orchestrator/
```

**Document results in story:**
```markdown
- [x] 8.1 `uv run ruff check src/ tests/` → PASSED (X issues fixed)
- [x] 8.2 `uv run mypy src/` → PASSED
- [x] 8.3 `uv run pytest tests/computation/ -m integration` → PASSED (XX tests)
- [x] 8.4 `uv run pytest tests/computation/ -m "not integration"` → PASSED (XX tests)
- [x] 8.5 `uv run pytest tests/orchestrator/` → PASSED
```

---

### **FIX #5: Validate Reference Values**

Create a small notebook/script to verify reference values:

```python
# tests/fixtures/verify_reference_values.py
from openfisca_france import CountryTaxBenefitSystem
from openfisca_core.simulation_builder import SimulationBuilder

tbs = CountryTaxBenefitSystem()

# Test case 1: zero income
entities_dict = {
    "individus": {"person_0": {"salaire_imposable": {"2024": 0.0}}},
    "familles": {"famille_0": {"parents": ["person_0"]}},
    "foyers_fiscaux": {"foyer_0": {"declarants": ["person_0"]}},
    "menages": {"menage_0": {"personne_de_reference": ["person_0"]}},
}
builder = SimulationBuilder()
sim = builder.build_from_entities(tbs, entities_dict)
irpp = float(sim.calculate("impot_revenu_restant_a_payer", "2024")[0])
print(f"Zero income IRPP: {irpp} (expected: 0.0, tolerance: ±0.5)")
assert abs(irpp - 0.0) <= 0.5, f"Failed: {irpp} != 0.0"
```

Document actual values returned by OpenFisca and adjust story reference values if needed.

---

## Summary of Blockers

| Issue | Task | Status |
|-------|------|--------|
| Source code truncated | Complete review | 🔴 BLOCKED |
| Duplicate test methods | Fix + run tests | 🔴 BLOCKED |
| Incomplete test classes | Implementation verification | 🔴 BLOCKED |
| Tasks 7-8 not done | Run quality gates | 🔴 BLOCKED |
| Missing fixture decorator | Add decorator | 🔴 BLOCKED |
| Reference values unvalidated | Run against OpenFisca | 🔴 BLOCKED |

**Story cannot be merged until ALL blockers are resolved.**

---

## Recommendation

**REJECT** this story submission. Request:

1. ✅ **Complete, untruncated source code file** for full AC verification
2. ✅ **Remove duplicate test methods** (careless merge artifact)
3. ✅ **Add @pytest.fixture decorator** to `reference_multi_entity_adapter()`
4. ✅ **Complete Tasks 7-8** with documented results
5. ✅ **Validate reference values** against actual OpenFisca output
6. ✅ **Update story status** to reflect incomplete work OR complete the work before resubmission

**Re-submit once all fixes are applied and quality gates pass.**

]]></file>
<file id="557aedd2" path="[Validator B]" label="VALIDATION OUTPUT"><![CDATA[

## 📊 Review Summary

| Category | Issues Found |
|----------|--------------|
| Task Completion (acknowledged gaps) | 2 |
| Code Duplication (DRY violations) | 2 |
| Test Design / Correctness | 3 |
| Regression Detection Accuracy | 2 |
| **Total Issues** | **9** |

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🔴 CRITICAL | Tasks 7 & 8 both `[ ]` — tests never executed, all reference values analytically computed and unverified against real OpenFisca | Story file, Dev Agent Record | +3 |
| 🟠 IMPORTANT | `_assert_irpp` method duplicated identically across `TestAdapterReferenceSinglePerson` and `TestAdapterReferenceFamilies` — exact DRY violation flagged in Story 9-3 antipatterns | Lines 1387–1395, 1530–1538 | +1 |
| 🟠 IMPORTANT | `reference_irpp_adapter` fixture is a perfect duplicate of the existing `adapter` fixture — same `country_package`, same `output_variables` — loads a second TBS unnecessarily | Lines 1303–1314 vs 39–45 | +1 |
| 🟠 IMPORTANT | Version pinning uses `startswith("175.")` — passes for 175.1.0, 175.2.0, etc. If OpenFisca-France ships a breaking change in a 175.x minor release, the guard silently passes | Line 2116 | +1 |
| 🟠 IMPORTANT | `TestFourEntityCrossValidation` tests create fresh `OpenFiscaApiAdapter` instances inline (lines 1745, 1810, 1837) instead of using module-scoped fixtures — triggers additional TBS loads, defeating the caching strategy | Lines 1745, 1810, 1837 | +1 |
| 🟠 IMPORTANT | `REFERENCE_DATE` declared on all reference test classes but never included in assertion failure messages — AC-3 explicitly requires the date in failure output, but `_assert_irpp` only emits version, not date | Lines 1359, 1521, 1895 | +1 |
| 🟡 MINOR | `_build_single_person_population` is an instance method that never accesses `self` — should be `@staticmethod` per Python idioms | Line 1375 | +0.3 |
| 🟡 MINOR | `test_progressive_tax_monotonicity` runs 5 sequential `adapter.compute()` calls that fully duplicate the computations already done in the 5 individual reference tests — each call is an OpenFisca simulation execution | Lines 1476–1494 | +0.3 |
| 🟢 CLEAN | Security: No credentials, no injection vectors, no sensitive data handling | — | −0.5 |

**Evidence Score: 8.1**

| Score | Verdict |
|-------|---------|
| **8.1** | **🔴 REJECT** |

---

## 🐛 Correctness & Safety

### 🔴 CRITICAL — Tasks 7 & 8 both `[ ]`: tests have never run, reference values unverified

The entire purpose of this story is a **regression detection suite**. The Dev Agent Record explicitly states:

> "Pending validation: Tasks 7-8 (test execution, quality gates) require manual execution due to sandbox limitations. **Reference values may need adjustment within ±0.5 tolerance** if OpenFisca's internal rounding differs from analytical computation."

This means:
- `uv run pytest tests/computation/ -m integration` has **never been executed**
- Ruff has never been run over the new code
- Mypy has never been run
- Family reference values (`REFERENCE_COUPLE_40K_30K = -5231.0`, `REFERENCE_FAMILY_1_CHILD = -3768.0`, `REFERENCE_FAMILY_2_CHILDREN = -3085.0`) were computed analytically from YAML barème parameters with no execution verification

The tolerance is ±0.5 EUR. French quotient familial with plafonnement and decote coupling is complex enough that an analytical calculation error of 1–5 EUR is entirely plausible. If these values are off, every family reference test will fail in CI from day 1 — **the regression suite will itself be broken**.

AC-7 ("existing tests unbroken") is completely unverified. AC-1 ("values match within tolerance") is completely unverified.

**This is a blocking issue. The story cannot be merged until Tasks 7.1, 8.1–8.5 are run and pass.**

---

## 🔧 Maintainability Issues

### 🟠 IMPORTANT — `_assert_irpp` duplicated identically in two classes

`tests/computation/test_openfisca_integration.py:1387` and `:1530` — character-for-character identical:

```python
def _assert_irpp(self, actual: float, expected: float, scenario: str) -> None:
    """Assert irpp matches reference within tolerance with diagnostic message."""
    assert abs(actual - expected) <= self.ABSOLUTE_ERROR_MARGIN, (
        f"{scenario}: Expected {expected}, got {actual} "
        f"(tolerance ±{self.ABSOLUTE_ERROR_MARGIN}, "
        f"ref: OpenFisca-France {self.REFERENCE_OPENFISCA_FRANCE_VERSION})"
    )
```

The Story 9-3 antipatterns explicitly called out DRY violations as a finding. This is an exact repeat. A module-level function `_assert_irpp(actual, expected, scenario, *, margin, version)` would eliminate the duplication and be usable by all reference test classes.

### 🟠 IMPORTANT — `reference_irpp_adapter` is a perfect duplicate of `adapter`

```python
# Line 39-45 (existing, pre-9.5)
@pytest.fixture(scope="module")
def adapter() -> OpenFiscaApiAdapter:
    return OpenFiscaApiAdapter(
        country_package="openfisca_france",
        output_variables=("impot_revenu_restant_a_payer",),
    )

# Line 1303-1314 (Story 9.5 addition)
@pytest.fixture(scope="module")
def reference_irpp_adapter() -> OpenFiscaApiAdapter:
    return OpenFiscaApiAdapter(
        country_package="openfisca_france",
        output_variables=("impot_revenu_restant_a_payer",),
    )
```

They are identical. The Dev Notes justify this with "test isolation (Story 9.5 tests should not depend on Story 9.2 fixture naming)" — but this is a fixture *alias*, not isolation. Both load a TBS instance. Module-scoped fixtures under pytest are module-singletons anyway, so there's no isolation benefit, only doubled cost. The Story 9.5 tests should simply use the existing `adapter` fixture.

---

## ⚡ Performance & Scalability

### 🟠 IMPORTANT — Fresh adapter instances in cross-validation tests (3 extra TBS loads)

`test_single_person_cross_validation` (line 1745) and `test_couple_vs_two_singles_quotient_benefit` (lines 1810, 1837) each create `OpenFiscaApiAdapter(country_package="openfisca_france", ...)` inline. Each fresh instance loads the full French TBS on first `compute()` call. With `reference_irpp_adapter` already being a module-scoped fixture, there is zero reason to instantiate fresh adapters in test bodies. This creates 3 extra TBS loads per module run.

### 🟡 MINOR — `test_progressive_tax_monotonicity` duplicates 5 full simulations

`tests/computation/test_openfisca_integration.py:1476–1494` loops over `sorted(self.REFERENCE_VALUES.keys())` and runs `reference_irpp_adapter.compute()` for each of the 5 reference income levels — the exact same computations already performed by `test_zero_income`, `test_low_income_near_smic`, `test_mid_income`, `test_upper_bracket`, `test_high_income`. This doubles the OpenFisca simulation count for the reference class. At scale (CI with multiple worker processes), this adds meaningful wall time.

---

## 🏛️ Architectural Sins

### 🟠 IMPORTANT — Version pin `startswith("175.")` is too coarse

`tests/computation/test_openfisca_integration.py:2116`:
```python
assert of_version.startswith("175."), (...)
```

The documented reference version is `175.0.18`. This guard passes for `175.1.0`, `175.2.0`, `175.99.0` — any 175.x minor or patch release. If OpenFisca-France introduces a breaking formula change in `175.1.0`, the version guard silently passes and the reference values fail mysteriously without the "version changed" diagnostic. The failure message even says "Reference values were computed against 175.0.18" but the test allows 175.1.x through. Should be `startswith("175.0.")` to truly pin to the minor version family.

### 🟠 IMPORTANT — `REFERENCE_DATE` declared but excluded from AC-3 failure messages

AC-3 requires failure messages to include all information needed to determine whether a change is expected or a regression. The `REFERENCE_DATE = "2026-03-02"` constant is defined on all three reference test classes but `_assert_irpp` only emits the version:

```python
f"ref: OpenFisca-France {self.REFERENCE_OPENFISCA_FRANCE_VERSION})"
# Missing: self.REFERENCE_DATE
```

The date is critical for tracing which YAML parameter files were in effect at the time of reference value computation. It belongs in the failure message alongside the version.

---

## 🐍 Pythonic Crimes

### 🟡 MINOR — `_build_single_person_population` should be `@staticmethod`

`tests/computation/test_openfisca_integration.py:1375`:
```python
def _build_single_person_population(
    self, salaire_imposable: float,
) -> PopulationData:
```

This method never accesses `self`. `ABSOLUTE_ERROR_MARGIN`, `REFERENCE_OPENFISCA_FRANCE_VERSION`, and `REFERENCE_DATE` are never referenced inside it. Mypy strict mode will accept this but it's misleading about the method's coupling to instance state. Should be `@staticmethod`.

---

## 🛠️ Suggested Fixes

### 1. Run Tasks 7 and 8 before merging

This is the only non-negotiable fix. Execute the quality gates and verify reference values against real OpenFisca:

```bash
uv run pytest tests/computation/test_openfisca_integration.py -m integration -v 2>&1 | tee /tmp/9.5-integration-results.txt
uv run ruff check src/ tests/
uv run mypy src/
```

If any reference test fails with an actual vs expected delta within 0–0.5 EUR, update the pinned value. If outside 0.5 EUR, the analytical computation was wrong and needs full recalculation.

### 2. Extract `_assert_irpp` to module level

Remove duplicate instance methods at lines 1387 and 1530. Replace with a single module-level function:

```python
def _assert_irpp(
    actual: float,
    expected: float,
    scenario: str,
    *,
    margin: float,
    version: str,
    date: str,
) -> None:
    """Assert irpp matches reference within tolerance with full regression context."""
    assert abs(actual - expected) <= margin, (
        f"{scenario}: Expected {expected}, got {actual} "
        f"(tolerance ±{margin}, "
        f"ref: OpenFisca-France {version} on {date})"
    )
```

This also fixes the `REFERENCE_DATE` omission in failure messages (issue 5).

### 3. Tighten version pin to `175.0.`

`tests/computation/test_openfisca_integration.py:2116` — change:
```python
# Before
assert of_version.startswith("175."), (...)
# After
assert of_version.startswith("175.0."), (
    f"OpenFisca-France minor version changed: {of_version} (expected 175.0.x). "
    ...
)
```

### 4. Drop `reference_irpp_adapter` — use `adapter`

Delete the `reference_irpp_adapter` fixture (lines 1303–1314). In all Story 9.5 IRPP tests, rename the fixture parameter from `reference_irpp_adapter` to `adapter`. The module-scoped `adapter` fixture at line 39 is identical and already cached for the module.

### 5. Replace inline adapter construction with module-scoped fixture

In `TestFourEntityCrossValidation.test_single_person_cross_validation` (line 1745) and `test_couple_vs_two_singles_quotient_benefit` (lines 1810, 1837): replace `adapter = OpenFiscaApiAdapter(...)` / `adapter_couple = OpenFiscaApiAdapter(...)` / `adapter_single = OpenFiscaApiAdapter(...)` with the `adapter` fixture parameter.

---

## Final Verdict

| | |
|--|--|
| **Score** | **8.1** |
| **Verdict** | **🔴 REJECT** |

The implementation architecture and test design are solid — the new test classes are well-structured, the family QF scenarios are thoughtfully specified, and the multi-entity cross-validation approach is correct. However, the story's own dev agent acknowledged that **the tests have never been executed**. A "regression detection suite" that has never run is not a regression detection suite — it's a regression detection suite *proposal*. The reference values for family scenarios in particular carry real uncertainty from analytical computation of complex quotient familial interactions.

Close the loop on Tasks 7 and 8, fix the DRY violation and the version pin, and this is a solid approval.

]]></file>
<file id="dc422a86" path="[git-diff]" label="VIRTUAL CONTENT"><![CDATA[

<!-- GIT_DIFF_START -->
 bmad-assist.yaml                                   |   59 +-
 notebooks/advanced.ipynb                           | 1242 ++++++++++++--
 src/reformlab/computation/openfisca_api_adapter.py |  905 +++++++++-
 src/reformlab/computation/types.py                 |   10 +-
 src/reformlab/computation/types.pyi                |    1 +
 tests/computation/test_openfisca_api_adapter.py    | 1799 +++++++++++++++++++-
 tests/computation/test_openfisca_integration.py    | 1472 ++++++++++++++++
 tests/computation/test_result.py                   |   83 +
 8 files changed, 5361 insertions(+), 210 deletions(-)

diff --git a/src/reformlab/computation/openfisca_api_adapter.py b/src/reformlab/computation/openfisca_api_adapter.py
index b32dd7f..506c176 100644
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
@@ -266,6 +502,250 @@ class OpenFiscaApiAdapter:
 
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
+            # AC-5: Null check on _id column.

[... Git diff truncated due to size - see full diff with git command ...]

]]></file>
</context>
<variables>
<var name="author">BMad</var>
<var name="communication_language">English</var>
<var name="date">2026-03-02</var>
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
<var name="session_id">354c3526-b92f-45f7-8d67-12ff127129d9</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_file" file_id="6ee5fa3d">embedded in prompt, file id: 6ee5fa3d</var>
<var name="story_id">9.5</var>
<var name="story_key">9-5-openfisca-france-reference-test-suite</var>
<var name="story_num">5</var>
<var name="story_title">openfisca-france-reference-test-suite</var>
<var name="template">False</var>
<var name="timestamp">20260302_1603</var>
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
      - Commit message format: fix(component): brief description (synthesis-9.5)
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