<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 9 -->
<!-- Story: 3 -->
<!-- Phase: code-review-synthesis -->
<!-- Timestamp: 20260301T203944Z -->
<compiled-workflow>
<mission><![CDATA[

Master Code Review Synthesis: Story 9.3

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

- [ ] Task 6: Verify backward compatibility (AC: #4)
  - [ ] 6.1 Run existing unit tests in `test_openfisca_api_adapter.py` — ensure all pass unchanged
  - [ ] 6.2 Run existing integration tests in `test_openfisca_integration.py` — note: any Story 9.2 integration test using `salaire_net` (a monthly variable) that is already failing with `ValueError: Period mismatch` is a pre-existing failure this story fixes as a side-effect (Story 9.2 added the test before the dispatch fix existed); Story 9.3 is expected to make it green; verify all other pre-existing integration tests remain green
  - [ ] 6.3 Verify `MockAdapter` still produces valid `ComputationResult` (no new required fields)
  - [ ] 6.4 Verify `ComputationStep` in orchestrator still works (`result.output_fields.num_rows`)

- [x] Task 7: Integration tests with real OpenFisca-France (AC: #1, #2, #6)
  - [x] 7.1 Test: `salaire_net` (MONTH) with yearly period → verify `calculate_add()` is used and returns correct yearly sum. Since real `Simulation` objects cannot be mock-asserted, verify dispatch via metadata: `assert result.metadata["calculation_methods"]["salaire_net"] == "calculate_add"`, and verify value correctness: `assert 20000 < result.entity_tables["individus"].column("salaire_net")[0].as_py() < 30000`
  - [x] 7.2 Test: `impot_revenu_restant_a_payer` (YEAR) with yearly period → verify `calculate()` is used (unchanged)
  - [x] 7.3 Test: mixed periodicity output variables in single `compute()` call → verify correct method per variable
  - [x] 7.4 Test: `adapter.compute()` end-to-end with monthly output variable produces correct values
  - [x] 7.5 Test: verify `variable_periodicities` metadata in integration test result
  - [x] 7.6 Mark integration tests with `@pytest.mark.integration`

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

Story 9.3: Added periodicity-aware calculation dispatch. Monthly variables
use ``calculate_add()`` to sum sub-period values; yearly and eternity
variables use ``calculate()``. Period validation ensures valid 4-digit year.
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
        calculation_methods: dict[str, str] = {}
        for var_name, periodicity in var_periodicities.items():
            if periodicity in _CALCULATE_ADD_PERIODICITIES:
                calculation_methods[var_name] = "calculate_add"
            else:
                calculation_methods[var_name] = "calculate"

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
        if periodicity in _CALCULATE_ADD_PERIODICITIES:
            logger.debug(
                "var=%s periodicity=%s method=calculate_add period=%s",
                var_name, periodicity, period_str,
            )
            return simulation.calculate_add(var_name, period_str)
        else:
            logger.debug(
                "var=%s periodicity=%s method=calculate period=%s",
                var_name, periodicity, period_str,
            )
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
    # Story 9.3: Also set definition_period = "year" by default so that
    # _resolve_variable_periodicities() works correctly during compute().
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
) -> MagicMock:
    """Create a mock TBS where variables know their entity.

    Story 9.2: Extended mock for entity-aware extraction tests.
    Story 9.3: Added variable_periodicities parameter for periodicity-aware tests.

    Args:
        entity_keys: Entity singular keys.
        entity_plurals: Mapping of singular key to plural form.
            Defaults to appending "s" (with special cases).
        variable_entities: Mapping of variable name to entity key.
        variable_periodicities: Mapping of variable name to periodicity string
            (e.g. "month", "year", "eternity"). Defaults to "year" for all.
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
    if variable_periodicities is None:
        variable_periodicities = {}

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


# ===========================================================================
# Story 9.3: Variable periodicity handling
# ===========================================================================


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


class TestPeriodValidation:
    """Story 9.3 AC-3: Invalid period format rejection."""

    def test_zero_period_raises_error(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-3: Period of 0 raises ApiMappingError."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        with pytest.raises(ApiMappingError, match="Invalid period"):
            adapter.compute(sample_population, empty_policy, 0)

    def test_negative_period_raises_error(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-3: Negative period raises ApiMappingError."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        with pytest.raises(ApiMappingError, match="Invalid period"):
            adapter.compute(sample_population, empty_policy, -1)

    def test_two_digit_period_raises_error(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-3: Two-digit period (99) raises ApiMappingError."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        with pytest.raises(ApiMappingError, match="Invalid period"):
            adapter.compute(sample_population, empty_policy, 99)

    def test_five_digit_period_raises_error(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-3: Five-digit period (99999) raises ApiMappingError."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        with pytest.raises(ApiMappingError, match="Invalid period"):
            adapter.compute(sample_population, empty_policy, 99999)

    def test_valid_period_2024_passes(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-3: Valid period (2024) passes validation."""
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
            result = adapter.compute(sample_population, empty_policy, 2024)

        assert result.period == 2024

    def test_valid_period_1000_passes(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-3: Edge case — period 1000 (minimum valid) passes."""
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
            result = adapter.compute(sample_population, empty_policy, 1000)

        assert result.period == 1000

    def test_valid_period_9999_passes(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-3: Edge case — period 9999 (maximum valid) passes."""
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
            result = adapter.compute(sample_population, empty_policy, 9999)

        assert result.period == 9999

    def test_period_error_includes_actual_value(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-3: Error message includes the actual invalid value."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        with pytest.raises(ApiMappingError) as exc_info:
            adapter.compute(sample_population, empty_policy, 42)

        assert "42" in exc_info.value.reason
        assert "Invalid period" in exc_info.value.summary


class TestPeriodicityMetadata:
    """Story 9.3 AC-5: Periodicity metadata in compute() result."""

    def test_variable_periodicities_in_metadata(
        self, empty_policy: PolicyConfig
    ) -> None:
        """AC-5: Metadata includes variable_periodicities dict."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "irpp"),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={
                "salaire_net": "individu",
                "irpp": "foyer_fiscal",
            },
            variable_periodicities={
                "salaire_net": "month",
                "irpp": "year",
            },
        )
        mock_simulation = _make_mock_simulation_with_methods({
            "salaire_net": np.array([24000.0, 40000.0]),
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

        assert "variable_periodicities" in result.metadata
        assert result.metadata["variable_periodicities"] == {
            "salaire_net": "month",
            "irpp": "year",
        }

    def test_calculation_methods_in_metadata(
        self, empty_policy: PolicyConfig
    ) -> None:
        """AC-5: Metadata includes calculation_methods dict."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "irpp"),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={
                "salaire_net": "individu",
                "irpp": "foyer_fiscal",
            },
            variable_periodicities={
                "salaire_net": "month",
                "irpp": "year",
            },
        )
        mock_simulation = _make_mock_simulation_with_methods({
            "salaire_net": np.array([24000.0, 40000.0]),
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

        assert "calculation_methods" in result.metadata
        assert result.metadata["calculation_methods"] == {
            "salaire_net": "calculate_add",
            "irpp": "calculate",
        }

    def test_eternity_variable_uses_calculate_in_metadata(self) -> None:
        """AC-5, AC-6: Eternity variables show 'calculate' method in metadata."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("date_naissance",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={"date_naissance": "individu"},
            variable_periodicities={"date_naissance": "eternity"},
        )
        mock_simulation = _make_mock_simulation_with_methods({
            "date_naissance": np.array([19960101]),
        })
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "age": pa.array([30]),
                }),
            },
        )

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(
                population, PolicyConfig(parameters={}, name="test"), 2024
            )

        assert result.metadata["variable_periodicities"]["date_naissance"] == "eternity"
        assert result.metadata["calculation_methods"]["date_naissance"] == "calculate"


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


class TestAdapterPluralKeyFix:  # ...

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


    def test_compute_works_with_singular_entity_keys(  # ...

class TestOpenFiscaFranceReferenceCases:  # ...

    def test_single_person_salaire_imposable_20k(self, tbs: Any) -> None:  # ...

    def test_single_person_salaire_imposable_50k(self, tbs: Any) -> None:  # ...

    def test_couple_salaire_imposable_30k_25k(self, tbs: Any) -> None:  # ...

def multi_entity_adapter() -> OpenFiscaApiAdapter:  # ...

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


]]></file>
<file id="1d910d88" path="[Validator A]" label="VALIDATION OUTPUT"><![CDATA[

# 🔥 ADVERSARIAL CODE REVIEW: Story 9.3 - Add Variable Periodicity Handling

**Review Date:** 2026-03-01  
**Reviewer Mode:** MERCILESS (Finding every problem)  
**Verdict:** **MAJOR REWORK REQUIRED**

---

## 📋 Executive Summary

This story claims full implementation with 8 tasks (6 marked `[x]` done, 2 marked `[ ]` incomplete) across 3 files. **However, critical issues undermine the claim of completion:**

1. **Tasks 6 & 8 deliberately marked incomplete** — but the story is submitted as complete
2. **Integration test file is corrupted** — syntax errors, broken imports, duplicate classes
3. **Quality gates never run** — no proof code passes ruff/mypy/pytest
4. **Type safety gap** — period validation accepts floats, not just integers

**This code is NOT ready for production.** I've found 10 specific issues requiring fixes.

---

## 🎯 Issues Found: 10 Critical/Important Problems

### 🔴 **CRITICAL: Tasks 6 & 8 Marked Incomplete But Story Marked "Complete"**

**Severity:** CRITICAL | **Status:** Story Integrity Violation  
**Files:** `9-3-add-variable-periodicity-handling.md` (Task list)

**The Problem:**
```yaml
- [ ] Task 6: Verify backward compatibility (AC-4)
  - 6.1 Run existing unit tests
  - 6.2 Run existing integration tests  
  - 6.3 Verify MockAdapter still works
  - 6.4 Verify ComputationStep still works

- [ ] Task 8: Run quality gates (all ACs)
  - 8.1 uv run ruff check src/ tests/
  - 8.2 uv run mypy src/
  - 8.3 uv run pytest tests/computation/ tests/orchestrator/
```

Both tasks are explicitly marked `[ ]` (not started) in the story file, yet the story is submitted as complete with `Status: in-progress`. This is a **governance violation** — developers reading this story will assume nothing has been verified.

**Why It Matters:**
- No evidence code passes linting (ruff)
- No evidence code passes type checking (mypy)
- No evidence tests actually pass
- No regression testing performed
- Violates project's "CI-enforced quality" rule in architecture.md

**Fix:**
```yaml
# EITHER complete the tasks:
- [x] Task 6: Verify backward compatibility
  - Evidence: Test run output showing all tests pass
  - Evidence: Integration tests complete without errors
  
- [x] Task 8: Run quality gates
  - Evidence: ruff check output clean
  - Evidence: mypy strict output clean
  - Evidence: pytest output with all tests passing

# OR mark story as in-progress, not done
Status: in-progress  # NOT complete
```

**Evidence Score:** +3 (Critical governance failure)

---

### 🔴 **CRITICAL: Integration Test File Has Corrupted/Broken Imports**

**Severity:** CRITICAL | **File:** `tests/computation/test_openfisca_integration.py`  
**Lines:** 1-14 and throughout

**The Problem:**

Lines 1-14 import modules that are never used:
```python
from reformlab.computation.ingestion import DataSchema
from reformlab.computation.mapping import apply_output_mapping, load_mapping
from reformlab.computation.quality import validate_output
```

But more critically, line 23 references an unimported module:
```python
@pytest.fixture(scope="module")
def tbs() -> Any:
    """Load the real French TaxBenefitSystem once per module."""
    return openfisca_france.CountryTaxBenefitSystem()
    # ^^^^^^^^^^^^^^ NameError: name 'openfisca_france' is not defined!
```

This will cause **immediate runtime failure** when tests are discovered.

**Why It Matters:**
- Tests cannot run at all
- NameError on line 23 breaks pytest collection
- Task 8.3 ("Run pytest") would fail immediately

**Fix:**
```python
# Add missing import at top
import openfisca_france  # or: from openfisca_france import CountryTaxBenefitSystem

# Remove unused imports
# from reformlab.computation.ingestion import DataSchema  # UNUSED
# from reformlab.computation.mapping import apply_output_mapping, load_mapping  # UNUSED
# from reformlab.computation.quality import validate_output  # UNUSED
```

**Evidence Score:** +3 (Test file won't run)

---

### 🔴 **CRITICAL: Integration Test File Has Truncated/Corrupted Methods**

**Severity:** CRITICAL | **File:** `tests/computation/test_openfisca_integration.py`  
**Lines:** 1161-1200+

**The Problem:**

Multiple test classes have incomplete method signatures and `# ...` placeholders:

```python
# Line 1161 - class has no body after docstring
class TestAdapterPluralKeyFix:  # ...
    def test_population_to_entity_dict_normalises_to_plural(...) -> None:
        ...

# Line 1186 - method signature is truncated
def test_compute_works_with_singular_entity_keys(  # ...

# Line 1228 - incomplete class
class TestOpenFiscaFranceReferenceCases:  # ...
    def test_single_person_salaire_imposable_20k(self, tbs: Any) -> None:  # ...
    def test_single_person_salaire_imposable_50k(self, tbs: Any) -> None:  # ...
    def test_couple_salaire_imposable_30k_25k(self, tbs: Any) -> None:  # ...

# Line 1263 - function definition without implementation
def multi_entity_adapter() -> OpenFiscaApiAdapter:  # ...
```

**Why It Matters:**
- Python syntax errors — file cannot be imported
- Tests cannot run
- Suggests incomplete merge/copy-paste

**Fix:**
Either complete the truncated tests or remove the incomplete class definitions:

```python
# REMOVE incomplete classes
# class TestOpenFiscaFranceReferenceCases:
#     def test_single_person_salaire_imposable_20k(...):  # ...

# OR complete them fully with actual test implementations
```

**Evidence Score:** +3 (File syntax broken)

---

### 🟠 **IMPORTANT: Multiple Test Classes Are Duplicated**

**Severity:** HIGH | **File:** `tests/computation/test_openfisca_integration.py`

**The Problem:**

The following test classes appear **TWICE** with identical implementations:

1. **TestTaxBenefitSystemLoading** — Lines 77-131 AND 169-211 (identical)
2. **TestMultiEntityPopulation** — Lines 340-425 AND 505-570 (identical)  
3. **TestVariableMappingRoundTrip** — Lines 649-722 AND 823-896 (identical)
4. **TestOutputQualityValidation** — Lines 754-783 AND 927-956 (identical)
5. **TestKnownValueBenchmark** — Lines 857-920 AND 1059-1122 (identical)

**Why It Matters:**
- Tests run twice, wasting CI time
- Maintenance nightmare — fixing a test requires fixing it twice
- Sign of incomplete merge or copy-paste error
- Violates DRY principle

**Example - TestTaxBenefitSystemLoading (first occurrence):**
```python
def test_adapter_instantiates_without_error(self) -> None:
    a = OpenFiscaApiAdapter(...)
    assert a is not None
```

**Same test (second occurrence, line 169+):**
```python
def test_adapter_instantiates_without_error(self) -> None:
    a = OpenFiscaApiAdapter(...)
    assert a is not None
```

Identical code, identical behavior, identical purpose.

**Fix:**
Delete all duplicate test classes. Keep only the first occurrence of each.

**Evidence Score:** +1 (Code duplication, maintainability issue)

---

### 🟠 **IMPORTANT: No Test for Empty output_variables Guard**

**Severity:** MEDIUM | **File:** `src/reformlab/computation/openfisca_api_adapter.py`  
**Lines:** 59-67

**The Problem:**

The code validates empty output_variables:
```python
if not output_variables:
    raise ApiMappingError(
        summary="Empty output_variables",
        reason="output_variables tuple is empty — no variables to compute",
        fix="Provide at least one valid output variable name.",
        invalid_names=(),
        valid_names=(),
    )
```

But **there is NO unit test for this guard** in the test file. I searched through all test classes and found no test like `test_empty_output_variables_raises_error()` or similar.

**Why It Matters:**
- Guard code is untested
- Could silently break if someone refactors
- No proof this validation actually works

**Verification:**
```bash
grep -n "test_empty" tests/computation/test_openfisca_api_adapter.py
# Returns: NO MATCHES
```

**Fix:**

Add test to `TestOutputVariableValidation` class:
```python
def test_empty_output_variables_raises_error(self) -> None:
    """Constructor raises ApiMappingError when output_variables is empty."""
    with pytest.raises(ApiMappingError) as exc_info:
        OpenFiscaApiAdapter(
            output_variables=(),  # Empty tuple
            skip_version_check=True,
        )
    assert "Empty output_variables" in str(exc_info.value)
```

**Evidence Score:** +0.5 (Missing test coverage)

---

### 🟠 **IMPORTANT: Period Validation Accepts Floats (Type Safety)**

**Severity:** MEDIUM | **File:** `src/reformlab/computation/openfisca_api_adapter.py`  
**Lines:** 106-107

**The Problem:**

The period validation only checks numeric range:
```python
def _validate_period(self, period: int) -> None:
    if not (1000 <= period <= 9999):
        raise ApiMappingError(...)
```

**Python's comparison operators work on floats**, so this validation accepts invalid types:
```python
adapter.compute(population, policy, 2024.5)   # PASSES validation!
adapter.compute(population, policy, 2024.0)   # PASSES validation!
adapter.compute(population, policy, "2024")   # TypeError on comparison (OK)
```

The function signature says `period: int` but type checking isn't enforced at runtime.

**Why It Matters:**
- Type annotation lies (says int, accepts float)
- Floating-point period could cause subtle bugs in downstream code
- Violates strict type checking rule: "mypy --strict must pass"

**Proof of Issue:**
```python
>>> 1000 <= 2024.5 <= 9999
True  # PASSES but shouldn't!
```

**Fix:**

Add explicit type check:
```python
def _validate_period(self, period: int) -> None:
    """Validate that the period is a 4-digit year in [1000, 9999]."""
    if not isinstance(period, int) or isinstance(period, bool):
        raise ApiMappingError(
            summary="Invalid period type",
            reason=f"Period must be int, got {type(period).__name__}",
            fix="Provide a positive integer year, e.g. 2024",
            invalid_names=(),
            valid_names=(),
        )
    if not (1000 <= period <= 9999):
        raise ApiMappingError(...)
```

**Evidence Score:** +0.5 (Type safety issue)

---

### 🟡 **MEDIUM: Misleading Comment on Mock Fix**

**Severity:** MEDIUM | **File:** `tests/computation/test_openfisca_api_adapter.py`  
**Lines:** 49-56

**The Problem:**

The comment explaining the mock fix is **logically backwards**:

```python
# Story 9.3: Also set definition_period = "year" by default so that
# _resolve_variable_periodicities() works correctly during compute().
# 
# [CLAIM] without this fix, `MagicMock().definition_period` returns a 
# MagicMock (not `"year"`), causing all existing `compute()` unit tests 
# to dispatch to `calculate_add()` instead of `calculate()`, breaking 
# `TestPeriodFormatting.test_period_passed_as_string`
```

**The logic is wrong:**
- If `definition_period` is a MagicMock, `str(MagicMock())` returns something like `<MagicMock name='mock.definition_period' id='...'>` 
- This string is NOT in `_VALID_PERIODICITIES`, so line ~330 would **raise an error**, not dispatch to `calculate_add()`
- The fix is correct, but the explanation is incorrect

**Why It Matters:**
- Misleading future developers
- If someone relies on the comment logic, they'll make wrong assumptions
- Violates "Assumption transparency" rule

**Fix:**

Replace with correct explanation:
```python
# Story 9.3: Also set definition_period = "year" by default so that
# _resolve_variable_periodicities() works correctly during compute().
# 
# Without this: MagicMock().definition_period returns a MagicMock object,
# which when converted to string via str() produces "<MagicMock ...>",
# which is not in _VALID_PERIODICITIES, causing _resolve_variable_periodicities()
# to raise ApiMappingError("Unexpected periodicity..."). Setting definition_period
# to the string "year" prevents this error in unit tests that use default mocks.
```

**Evidence Score:** +0.3 (Documentation/clarity issue)

---

### 🟡 **MEDIUM: No End-to-End Integration Test for Eternity Variables**

**Severity:** MEDIUM | **Files:** `test_openfisca_integration.py`  
**AC-6 Requirement:** "Given an ETERNITY-period variable (e.g., `date_naissance`, `sexe`) as an output variable, when `compute()` is called, then `simulation.calculate()` is used (NOT `calculate_add()`)..."

**The Problem:**

AC-6 exists in the story, requiring that eternity variables use `calculate()` not `calculate_add()`.

Unit tests verify this at line ~1001 in `TestCalculateVariable::test_eternity_uses_calculate()` with a mock.

**BUT** there is **NO integration test** that:
1. Calls `adapter.compute()` with an eternity variable (like `date_naissance` or `sexe`)
2. Verifies the result is correct
3. Verifies the metadata shows `calculation_methods["date_naissance"] == "calculate"`

The closest is `test_variable_periodicity_resolution_matches_tbs()` at line ~1446, which only verifies `tbs.variables["date_naissance"].definition_period == "eternity"` exists, not that adapter.compute() handles it correctly.

**Why It Matters:**
- AC-6 integration coverage is incomplete
- Risk: eternity variable in production could silently use wrong calculation method
- No proof eternity variables work end-to-end

**Fix:**

Add integration test:
```python
@pytest.mark.integration
def test_eternity_variable_end_to_end(self, tbs: Any) -> None:
    """AC-6: Eternity variable (date_naissance) computes without error."""
    adapter = OpenFiscaApiAdapter(
        country_package="openfisca_france",
        output_variables=("date_naissance",),  # Eternity variable
    )
    
    population = PopulationData(
        tables={
            "individu": pa.table({
                "age": pa.array([30]),
            }),
        },
    )
    policy = PolicyConfig(parameters={}, name="eternity-test")
    
    result = adapter.compute(population, policy, 2024)
    
    # AC-6: Verify metadata shows 'calculate' method for eternity
    assert result.metadata["variable_periodicities"]["date_naissance"] == "eternity"
    assert result.metadata["calculation_methods"]["date_naissance"] == "calculate"
    
    # Verify value is present and valid
    assert result.output_fields.num_rows == 1
    birth_date = result.output_fields.column("date_naissance")[0].as_py()
    assert isinstance(birth_date, int)  # Date as integer
    assert 19000000 < birth_date < 20300000  # Plausible YYYYMMDD format
```

**Evidence Score:** +0.5 (AC coverage gap)

---

### 🟡 **MINOR: Missing Logging Exports or Structure**

**Severity:** MINOR | **File:** `src/reformlab/computation/openfisca_api_adapter.py`

The code adds logging at lines 327 and 363, but I don't see `logger = logging.getLogger(__name__)` being used consistently throughout.

Wait, checking line 34:
```python
logger = logging.getLogger(__name__)
```

This is present. OK, the logging is correct. This is not an issue.

Actually, I need to be more careful. Let me re-examine...

---

## 📊 Evidence Score Calculation

| Category | Issues Found | Score |
|----------|--------------|-------|
| **CRITICAL** (governance, syntax, imports) | 3 issues | +9.0 |
| **IMPORTANT** (missing tests, type safety) | 2 issues | +2.0 |
| **MEDIUM** (duplication, misleading comments) | 3 issues | +1.5 |
| **MINOR** | 0 issues | 0 |
| **CLEAN PASSES** (SOLID, Performance, Security) | 3 categories | -1.5 |

**Evidence Score: `+11.0`**

**Verdict: 🔴 REJECT - Requires Major Rework**

---

## 🛠️ Recommended Action

**DO NOT MERGE.** This code has:
1. ✗ Incomplete task verification (Tasks 6 & 8 skipped)
2. ✗ Syntax errors in test file (broken imports, truncated methods)
3. ✗ Duplicate test classes (copy-paste errors)
4. ✗ Type safety gap (float period validation)
5. ✗ Test coverage gaps (eternity variables, empty output_variables)

**Required Before Resubmission:**
- [ ] Complete Task 6 — Run backward compatibility tests
- [ ] Complete Task 8 — Run `ruff check`, `mypy`, `pytest`
- [ ] Fix integration test file syntax errors
- [ ] Remove duplicate test classes
- [ ] Add type check for period parameter
- [ ] Add end-to-end eternity variable test
- [ ] Add empty output_variables test
- [ ] Fix misleading comment on mock fix

Would you like me to auto-fix these issues, or would you prefer to handle them manually?

]]></file>
<file id="557aedd2" path="[Validator B]" label="VALIDATION OUTPUT"><![CDATA[

---

## 🔥 ADVERSARIAL CODE REVIEW COMPLETE, Lucas!

**Story:** `9-3-add-variable-periodicity-handling`
**Reviewer:** BMad Adversarial Senior Dev
**Date:** 2026-03-01

---

## 📊 Review Summary

| Category | Issues Found |
|----------|--------------|
| Git vs Story Discrepancies | 0 |
| AC Implementation Gaps (ordering constraint) | 1 |
| Task Completion Lies | 1 (Tasks 6, 8 = ☐, delivered anyway) |
| Lying Tests | 1 |
| Code Quality (DRY violations, type safety) | 4 |
| Performance Footguns | 1 |
| Dead Code | 1 |
| **Total Issues** | **8** |

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🟠 IMPORTANT | `TestPeriodValidation` tests don't verify "FIRST" constraint from AC-3 — lying tests | `test_openfisca_api_adapter.py:1164-1301` | +1 |
| 🟠 IMPORTANT | Quality gates (Tasks 6 + 8) explicitly not run — delivery without ruff/mypy/pytest | Story task list | +1 |
| 🟠 IMPORTANT | `Any` used without `from typing import Any` in test helper functions | `test_openfisca_api_adapter.py:62,128` | +1 |
| 🟡 MINOR | `_resolve_variable_periodicities` + `_resolve_variable_entities` make 2× redundant TBS variable lookups | `openfisca_api_adapter.py:116,120` | +0.3 |
| 🟡 MINOR | `calculation_methods` metadata construction triplicates the `_CALCULATE_ADD_PERIODICITIES` dispatch logic | `openfisca_api_adapter.py:143-148` | +0.3 |
| 🟡 MINOR | `_calculate_variable` return type annotated as `Any` — docstring says `numpy.ndarray` | `openfisca_api_adapter.py:371` | +0.3 |
| 🟡 MINOR | `day`/`week`/`weekday` → `calculate_add()` is O(365N) OpenFisca calls — undocumented performance trap | `openfisca_api_adapter.py:389-391` | +0.3 |
| 🟡 MINOR | Dead SimulationBuilder mock setup in `test_compute_entity_detection_error` | `test_openfisca_api_adapter.py:~1583` | +0.3 |
| 🟢 CLEAN PASS | Security: no credential exposure, injection vectors, or auth issues | All files | −0.5 |
| 🟢 CLEAN PASS | Architecture isolation: OpenFisca imports correctly lazy throughout | `openfisca_api_adapter.py` | −0.5 |
| 🟢 CLEAN PASS | Core dispatch logic: `calculate` vs `calculate_add` table is correct per OpenFisca spec | `openfisca_api_adapter.py:365-408` | −0.5 |

### Evidence Score: **3.0**

| Score | Verdict |
|-------|---------|
| **3.0** | **🟠 MAJOR REWORK** |

---

## 🏛️ Architectural Sins

### **[5/10] DRY Violation: Dispatch logic triplication**

The rule "if periodicity in sub-period set → use `calculate_add`" exists in **three places**:

1. `_CALCULATE_ADD_PERIODICITIES` frozenset (definition)
2. `_calculate_variable()` — runtime dispatch
3. `compute()` lines 143-148 — metadata construction

```python
# compute() reimplements the exact same check already in _calculate_variable():
for var_name, periodicity in var_periodicities.items():
    if periodicity in _CALCULATE_ADD_PERIODICITIES:   # DUPLICATED
        calculation_methods[var_name] = "calculate_add"
    else:
        calculation_methods[var_name] = "calculate"
```

Adding a new periodicity to `_CALCULATE_ADD_PERIODICITIES` (e.g., `"quarter"`) updates `_calculate_variable` automatically (set membership), but the metadata block in `compute()` also needs manual updating. Miss it and your `calculation_methods` metadata lies about what was actually called.

📍 `src/reformlab/computation/openfisca_api_adapter.py:143-148`
💡 **Fix:** Extract `_periodicity_to_method_name(periodicity: str) -> str` helper (one line) and call it in both places.

---

### **[4/10] Redundant Double-Pass Over TBS Variables**

`_resolve_variable_entities` (line 588) and `_resolve_variable_periodicities` (line 303) are called sequentially in `compute()` at lines 116 and 120. Both iterate over `self._output_variables` and call `tbs.variables.get(var_name)` independently — 2N TBS variable lookups instead of N. Both have near-identical null-guard error handling blocks.

This is the same pattern the Story 9.2 antipatterns called out for `_resolve_variable_entities` + `_build_simulation` ordering. Story 9.3 adds the same lookup loop again rather than consolidating.

📍 `src/reformlab/computation/openfisca_api_adapter.py:116,120`
💡 **Fix:** Merge into `_resolve_variable_metadata(tbs) -> tuple[dict[str, list[str]], dict[str, str]]` — single pass, returns `(vars_by_entity, periodicities)`.

---

## 🐍 Pythonic Crimes & Readability

### **`Any` used without import in test helpers**

`_make_mock_tbs()` and `_make_mock_tbs_with_entities()` both annotate a local variable as `dict[str, Any]`:

```python
# test_openfisca_api_adapter.py line 62:
variables: dict[str, Any] = {}

# test_openfisca_api_adapter.py line 128:
variables: dict[str, Any] = {}
```

`Any` is never imported. The file imports are:
```python
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
# ... no `from typing import Any`
```

`from __future__ import annotations` saves this at runtime (annotations are strings), but it's conceptually wrong and would fail any tool that evaluates type hints (e.g., `typing.get_type_hints()`, Pydantic field introspection, or if mypy is configured to also check `tests/`).

📍 `tests/computation/test_openfisca_api_adapter.py:62,128`
💡 **Fix:** Add `from typing import Any` to the imports block.

---

### **`_calculate_variable` return type annotation misleads callers**

```python
def _calculate_variable(
    self,
    simulation: Any,
    var_name: str,
    period_str: str,
    periodicity: str,
) -> Any:   # ← lies; docstring says "numpy.ndarray of computed values"
```

The docstring explicitly states the return type. Using `Any` defeats the purpose of strict mode. numpy is already a transitive dependency of openfisca-core, so it's always present when this method is called.

📍 `src/reformlab/computation/openfisca_api_adapter.py:371`

---

## ⚡ Performance & Scalability

### **[HIGH IMPACT] `day`/`week`/`weekday` → `calculate_add()` is O(365N) with no warning**

The dispatch table correctly maps sub-yearly periodicities to `calculate_add()`:

```python
_CALCULATE_ADD_PERIODICITIES = frozenset({
    "month", "day", "week", "weekday",   # ← day and week are silent traps
})
```

For a **yearly period**:
- `month` → 12 OpenFisca sub-calls ✅ (reasonable)
- `week` → 52 OpenFisca sub-calls ⚠️ (marginal)
- `day` → **365 OpenFisca sub-calls per population run** 🔴

For a 100k-individual simulation requesting a daily variable, `calculate_add` makes `365 × 100,000` sub-period evaluations. The French OpenFisca-France tax system has essentially zero real daily-period output variables (none relevant to carbon tax analysis), but this is a silent footgun: a curious developer who requests any `day`-period variable will get a computation that takes minutes instead of milliseconds with no diagnostic.

📍 `src/reformlab/computation/openfisca_api_adapter.py:389-391`
💡 **Fix:** Add a logged warning (not an error) when dispatching `calculate_add` for `day`/`week`/`weekday` periodicity with yearly input, documenting the sub-call count and directing developers to `calculate_divide` if they intended a different semantics.

---

## 🐛 Correctness & Safety

### **🎭 Lying Test: `TestPeriodValidation` doesn't verify AC-3's "FIRST" ordering constraint**

AC-3 explicitly specifies:
> *"Given an invalid period value … when passed to the adapter's `compute()` as the **very first check before any TBS operations**"*

Every single period validation test pre-loads the TBS before calling `compute()`:

```python
def test_zero_period_raises_error(self, ...):
    adapter = OpenFiscaApiAdapter(output_variables=("income_tax",), skip_version_check=True)
    mock_tbs = _make_mock_tbs()
    adapter._tax_benefit_system = mock_tbs   # ← TBS already loaded!

    with pytest.raises(ApiMappingError, match="Invalid period"):
        adapter.compute(sample_population, empty_policy, 0)
        # Test passes whether _validate_period runs before OR after _get_tax_benefit_system()
```

If someone refactors `compute()` and moves `_validate_period(period)` to after `_get_tax_benefit_system()` call, **all four invalid-period tests still pass**. The ordering constraint is completely untested.

This also defeats the fail-fast purpose: if a user passes `period=0`, they'd incur the cost of TBS loading (or waiting for the lazy import) before getting the validation error.

📍 `tests/computation/test_openfisca_api_adapter.py:1164,1178,1192,1206`

**Why it lies:** Setting `adapter._tax_benefit_system = mock_tbs` bypasses the condition `if self._tax_benefit_system is not None: return self._tax_benefit_system` in `_get_tax_benefit_system()`. Even if `_validate_period` moved to line 200, the test would pass because `_get_tax_benefit_system()` returns instantly (cache hit) and no expensive work happens. The "FIRST" constraint is never verified.

---

### **🎭 Dead Code: SimulationBuilder mock in `test_compute_entity_detection_error`**

```python
def test_compute_entity_detection_error(self) -> None:
    ...
    mock_builder_instance = MagicMock()        # ← never used
    mock_simulation = MagicMock()              # ← never used
    mock_builder_instance.build_from_entities.return_value = mock_simulation  # ← unreachable

    with _patch_simulation_builder(mock_builder_instance):
        with pytest.raises(ApiMappingError, match="Cannot determine entity"):
            adapter.compute(...)
```

The `ApiMappingError` is raised inside `_resolve_variable_entities()`, which is called **before** `_build_simulation()` in the `compute()` flow. The SimulationBuilder is never invoked; the mock setup is dead code that wastes 3 lines and misleads maintainers into believing builder setup is relevant to entity detection failures.

📍 `tests/computation/test_openfisca_api_adapter.py:~1583-1586`

---

## 🔧 Maintainability Issues

### **💣 Tasks 6 and 8 are explicitly unfinished — story delivered with quality gates skipped**

The story's own task list is self-incriminating:

```
- [ ] Task 6: Verify backward compatibility (AC: #4)
  - [ ] 6.1 Run existing unit tests in test_openfisca_api_adapter.py
  - [ ] 6.2 Run existing integration tests ...
  - [ ] 6.3 Verify MockAdapter still produces valid ComputationResult
  - [ ] 6.4 Verify ComputationStep in orchestrator still works

- [ ] Task 8: Run quality gates (all ACs)
  - [ ] 8.1 uv run ruff check src/ tests/
  - [ ] 8.2 uv run mypy src/
  - [ ] 8.3 uv run pytest tests/computation/ tests/orchestrator/
```

The story claims implementation is done across all ACs but the verification loop was skipped. This is exactly how the Story 9.2 antipatterns entry was created — bugs that would have been caught by actually running the tests.

💥 **Explosion radius:** Without Task 6.1 verified, we don't know if the `_make_mock_tbs` changes broke any pre-existing tests. Without Task 8.3, we don't know if the new integration tests actually run and pass with real `openfisca-france`.

---

## 🛠️ Suggested Fixes

### 1. Add `from typing import Any` to unit test file

**File:** `tests/computation/test_openfisca_api_adapter.py`

```diff
 from __future__ import annotations
 
 import sys
 from types import SimpleNamespace
+from typing import Any
 from unittest.mock import MagicMock, patch
```

---

### 2. Add ordering-aware period validation test (fixes lying test gap for AC-3)

**File:** `tests/computation/test_openfisca_api_adapter.py`

Add to `TestPeriodValidation` class:

```python
def test_period_validation_precedes_tbs_loading(
    self, sample_population: PopulationData, empty_policy: PolicyConfig
) -> None:
    """AC-3: Period validation fires BEFORE any TBS operations.

    The adapter must not load or cache the TBS when period is invalid.
    This verifies the 'very first check' contract in AC-3.
    """
    adapter = OpenFiscaApiAdapter(
        output_variables=("income_tax",),
        skip_version_check=True,
    )
    # Deliberately do NOT pre-load TBS — if validation runs first,
    # the TBS will still be None after the error.
    assert adapter._tax_benefit_system is None

    with pytest.raises(ApiMappingError, match="Invalid period"):
        adapter.compute(sample_population, empty_policy, 0)

    # Confirm TBS was never loaded — period check was genuinely first.
    assert adapter._tax_benefit_system is None
```

---

### 3. Extract `_periodicity_to_method_name` to eliminate dispatch logic duplication

**File:** `src/reformlab/computation/openfisca_api_adapter.py`

```diff
+def _periodicity_to_method_name(periodicity: str) -> str:
+    """Map a DateUnit periodicity string to the OpenFisca calculation method name.
+
+    Single source of truth for the calculate vs calculate_add dispatch decision.
+    """
+    return "calculate_add" if periodicity in _CALCULATE_ADD_PERIODICITIES else "calculate"
+
+
 class OpenFiscaApiAdapter:
     ...

     def _calculate_variable(self, simulation, var_name, period_str, periodicity) -> Any:
-        if periodicity in _CALCULATE_ADD_PERIODICITIES:
+        method = _periodicity_to_method_name(periodicity)
+        if method == "calculate_add":
             ...
             return simulation.calculate_add(var_name, period_str)
         else:
             ...
             return simulation.calculate(var_name, period_str)

     # In compute():
-    calculation_methods: dict[str, str] = {}
-    for var_name, periodicity in var_periodicities.items():
-        if periodicity in _CALCULATE_ADD_PERIODICITIES:
-            calculation_methods[var_name] = "calculate_add"
-        else:
-            calculation_methods[var_name] = "calculate"
+    calculation_methods = {
+        var_name: _periodicity_to_method_name(periodicity)
+        for var_name, periodicity in var_periodicities.items()
+    }
```

---

### 4. Add performance warning for sub-daily `calculate_add` (day/week/weekday)

**File:** `src/reformlab/computation/openfisca_api_adapter.py`

In `_calculate_variable`, before the `calculate_add` call:

```diff
 if periodicity in _CALCULATE_ADD_PERIODICITIES:
+    if periodicity in ("day", "week", "weekday"):
+        _SUB_PERIOD_COUNTS = {"day": 365, "week": 52, "weekday": 260}
+        logger.warning(
+            "var=%s periodicity=%s method=calculate_add period=%s "
+            "sub_period_calls_approx=%d — high performance cost for large populations",
+            var_name, periodicity, period_str,
+            _SUB_PERIOD_COUNTS.get(periodicity, "unknown"),
+        )
     return simulation.calculate_add(var_name, period_str)
```

---

### 5. Remove dead SimulationBuilder setup from entity detection error test

**File:** `tests/computation/test_openfisca_api_adapter.py`

```diff
 def test_compute_entity_detection_error(self) -> None:
     ...
-    mock_builder_instance = MagicMock()
-    mock_simulation = MagicMock()
-    mock_builder_instance.build_from_entities.return_value = mock_simulation
-
-    with _patch_simulation_builder(mock_builder_instance):
-        with pytest.raises(ApiMappingError, match="Cannot determine entity"):
-            adapter.compute(
-                population, PolicyConfig(parameters={}, name="test"), 2024
-            )
+    # Error raised in _resolve_variable_entities() — before _build_simulation().
+    # No SimulationBuilder mock needed.
+    with pytest.raises(ApiMappingError, match="Cannot determine entity"):
+        adapter.compute(
+            population, PolicyConfig(parameters={}, name="test"), 2024
+        )
```

---

## Verdict Summary

The core implementation is **architecturally sound and functionally correct** — the dispatch table, the fail-fast ordering in `compute()`, and the eternity/month/year handling all work as specified. The story author clearly understood the OpenFisca periodicity system deeply.

The problems are in the **verification layer**: the quality gates were skipped, the most important AC (AC-3's "FIRST" ordering) has untested lying tests, and two DRY violations will become maintenance landmines as the periodicity set evolves. Fix 1 and 2 above are mandatory before sign-off. Fixes 3-5 should be batched into the next available slot.

| Priority | Fix | Effort |
|----------|-----|--------|
| 🔴 Must | Add `from typing import Any` import | 30 seconds |
| 🔴 Must | Add ordering-aware period validation test (AC-3) | 10 minutes |
| 🔴 Must | Run Tasks 6 + 8 (ruff, mypy, pytest) | 5 minutes |
| 🟡 Should | Extract `_periodicity_to_method_name()` helper | 15 minutes |
| 🟡 Should | Add performance warning for day/week/weekday dispatch | 10 minutes |
| 🟢 Nice | Remove dead SimulationBuilder mock | 2 minutes |

]]></file>
<file id="dc422a86" path="[git-diff]" label="VIRTUAL CONTENT"><![CDATA[

<!-- GIT_DIFF_START -->
 bmad-assist.yaml                                   |  36 +-
 src/reformlab/computation/openfisca_api_adapter.py | 401 ++++++++-
 src/reformlab/computation/types.py                 |  10 +-
 src/reformlab/computation/types.pyi                |   1 +
 tests/computation/test_openfisca_api_adapter.py    | 971 ++++++++++++++++++++-
 tests/computation/test_openfisca_integration.py    | 408 +++++++++
 tests/computation/test_result.py                   |  83 ++
 7 files changed, 1880 insertions(+), 30 deletions(-)

diff --git a/src/reformlab/computation/openfisca_api_adapter.py b/src/reformlab/computation/openfisca_api_adapter.py
index b32dd7f..b9a4bbe 100644
--- a/src/reformlab/computation/openfisca_api_adapter.py
+++ b/src/reformlab/computation/openfisca_api_adapter.py
@@ -5,11 +5,20 @@ runs live tax-benefit calculations using OpenFisca's ``SimulationBuilder``.
 
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
 """
 
 from __future__ import annotations
 
 import difflib
+import logging
 import time
 from typing import Any
 
@@ -22,6 +31,17 @@ from reformlab.computation.openfisca_common import (
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
 
 class OpenFiscaApiAdapter:
     """Adapter that executes OpenFisca computations via the Python API.
@@ -37,6 +57,14 @@ class OpenFiscaApiAdapter:
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
 
@@ -67,29 +95,75 @@ class OpenFiscaApiAdapter:
 
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
+        calculation_methods: dict[str, str] = {}
+        for var_name, periodicity in var_periodicities.items():
+            if periodicity in _CALCULATE_ADD_PERIODICITIES:
+                calculation_methods[var_name] = "calculate_add"
+            else:
+                calculation_methods[var_name] = "calculate"
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
@@ -176,6 +250,155 @@ class OpenFiscaApiAdapter:
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
+        if periodicity in _CALCULATE_ADD_PERIODICITIES:
+            logger.debug(
+                "var=%s periodicity=%s method=calculate_add period=%s",
+                var_name, periodicity, period_str,
+            )
+            return simulation.calculate_add(var_name, period_str)
+        else:
+            logger.debug(
+                "var=%s periodicity=%s method=calculate period=%s",
+                var_name, periodicity, period_str,
+            )
+            return simulation.calculate(var_name, period_str)
+
     def _validate_policy_parameters(self, policy: PolicyConfig, tbs: Any) -> None:
         """Check that all policy parameter keys are valid input variables."""
         if not policy.parameters:
@@ -338,13 +561,171 @@ class OpenFiscaApiAdapter:
 
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
+                # entity.plural is required — silently falling back to entity.key
+                # would produce wrong plural keys (e.g. "foyer_fiscal" instead of
+                # "foyers_fiscaux") causing subtle downstream lookup failures.
+                # This path only occurs with a malformed/incompatible TBS.
+                entity_key = getattr(entity, "key", None)
+                raise ApiMappingError(
+                    summary="Cannot determine entity plural name for variable",
+                    reason=(
+                        f"Variable '{var_name}' entity has no .plural attribute"
+                        + (
+                            f" (entity.key={entity_key!r})"
+                            if entity_key
+                            else ", no .key attribute either"
+                        )
+                    ),
+                    fix=(
+                        "This may indicate an incompatible OpenFisca version. "
+                        "Check the OpenFisca compatibility matrix."
+                    ),
+                    invalid_names=(var_name,),
+                    valid_names=tuple(sorted(tbs.variables.keys())),
+                )
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
+        variable_periodicities: dict[str, str],
+    ) -> dict[str, pa.Table]:
+        """Extract output variables grouped by entity into per-entity tables.
+
+        For each entity group, calls the appropriate calculation method
+        (``calculate()`` or ``calculate_add()``) for its variables and
+        builds a ``pa.Table`` per entity. Arrays within an entity group
+        share the same length (entity instance count).
+
+        Story 9.3: Uses ``_calculate_variable()`` for periodicity-aware
+        dispatch instead of calling ``simulation.calculate()`` directly.
+
+        Args:
+            simulation: The completed OpenFisca simulation.
+            period: Computation period (integer year).
+            vars_by_entity: Output variables grouped by entity plural name
+                (from ``_resolve_variable_entities``).
+            variable_periodicities: Periodicity per variable
+                (from ``_resolve_variable_periodicities``).
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
+                periodicity = variable_periodicities[var_name]
+                numpy_array = self._calculate_variable(
+                    simulation, var_name, period_str, periodicity
+                )
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
<var name="session_id">089248a8-d613-4003-893f-b80c4f4164ff</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_file" file_id="ccd1eda3">embedded in prompt, file id: ccd1eda3</var>
<var name="story_id">9.3</var>
<var name="story_key">9-3-add-variable-periodicity-handling</var>
<var name="story_num">3</var>
<var name="story_title">add-variable-periodicity-handling</var>
<var name="template">False</var>
<var name="timestamp">20260301_2139</var>
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
      - Commit message format: fix(component): brief description (synthesis-9.3)
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