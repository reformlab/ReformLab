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

The no-code GUI (EPIC-6) will be a web application with a React/TypeScript frontend and a FastAPI Python backend, deployed on Scaleway Serverless infrastructure in Paris. The MVP is deployed from day one to enable sharing with colleagues (2-10 users).

### Rationale

- **Same stack for MVP and future phases** — no throwaway prototype. The MVP GUI uses the same React + Shadcn/ui + Tailwind + FastAPI stack specified in the UX design document. Phase 3 (public web app) extends rather than replaces.
- **Scaleway** chosen for: French datacenter (Paris), GDPR compliance, European sovereignty (Groupe Iliad), cost (~0-5 EUR/month on Serverless free tier), and ongoing SecNumCloud qualification process with ANSSI.
- **Git push = auto-deploy** via GitHub Actions. Setup once, then deployment is fully automated on every push to master.

### Monorepo Structure

```
reformlab/
  src/                        ← Python backend (FastAPI API + core library)
  frontend/                   ← React/TypeScript (Vite + Shadcn/ui + Tailwind)
  tests/
  Dockerfile                  ← Backend container definition
  frontend/Dockerfile         ← Frontend container (nginx serving build)
  .github/workflows/
    deploy.yml                ← Auto-deploy both services on push
  pyproject.toml
```

Both frontend and backend live in the same repository. GitHub Actions builds and deploys each as a separate Scaleway Serverless Container on push to master.

### Deployment Topology

```
┌─────────────────────────────────────────────────────┐
│  GitHub Repository (monorepo)                       │
│  push to master                                     │
└──────────┬──────────────────────┬───────────────────┘
           │                      │
    GitHub Actions          GitHub Actions
    (build backend)         (build frontend)
           │                      │
           ▼                      ▼
┌──────────────────┐   ┌──────────────────────┐
│ Scaleway          │   │ Scaleway              │
│ Serverless        │   │ Serverless            │
│ Container         │   │ Container             │
│ (FastAPI, Paris)  │   │ (nginx + React build, │
│                   │   │  Paris)               │
│ api.reformlab.fr  │   │ app.reformlab.fr      │
└──────────────────┘   └──────────────────────┘
         │
         ▼
┌──────────────────┐
│ Persistent Volume │
│ (CSV/Parquet/     │
│  YAML/JSON data)  │
└──────────────────┘
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

### Data Storage (MVP)

File-based, no database:

- **Scenario configs:** YAML/JSON files on persistent volume
- **Run outputs:** CSV/Parquet on persistent volume
- **Run manifests:** JSON on persistent volume
- **Scenario registry:** File-based (already implemented in EPIC-2)

Persistent volume is attached to the backend container. Sufficient for 2-10 users working with open/public data. If multi-user concurrent writes become an issue in Phase 3, migrate to SQLite or PostgreSQL — the file-based contract layer makes this a contained change.

### Authentication (MVP)

Simple shared-password authentication via FastAPI middleware:

- Single shared password stored as an environment variable on Scaleway
- FastAPI middleware checks password on every API request
- Frontend shows a password prompt on first access, stores the token in browser session
- No user accounts, no OAuth, no database — appropriate for 2-10 trusted colleagues

Phase 3 (public web app with Claire persona) will require proper user authentication (OAuth or similar). This is a separate architectural decision at that point.

### Cost Estimate

| Service | Monthly Cost |
| --- | --- |
| Backend Serverless Container | ~0-3 EUR (free tier covers low traffic) |
| Frontend Serverless Container | ~0-2 EUR (free tier covers low traffic) |
| Persistent Volume (1-5 GB) | ~0.50 EUR |
| **Total** | **~0-5 EUR/month** |

### Sovereignty & Compliance Positioning

- Hosted on Scaleway, French cloud provider (Groupe Iliad), Paris datacenter
- GDPR compliant, data stays in France, no transfer outside EU
- Not subject to US Cloud Act or other extra-territorial legislation
- Scaleway SecNumCloud qualification in progress with ANSSI (expected 2026)
- Application uses exclusively open public data (INSEE, Eurostat, synthetic populations)
- If SecNumCloud becomes required (e.g., restricted microdata handling), migration path: Scalingo on Outscale `osc-secnum-fr1` region — same code, different deployment target

### Migration Path to Phase 3

When the project grows beyond MVP:

1. **More users:** Scaleway Serverless auto-scales. No architecture change needed.
2. **User accounts:** Replace shared-password middleware with OAuth/OIDC. Add user table (SQLite or PostgreSQL).
3. **SecNumCloud required:** Redeploy to Scalingo on `osc-secnum-fr1` or Clever Cloud on Cloud Temple SecNumCloud zone. Application code unchanged.
4. **Frontend/backend split:** If needed, frontend can move to a CDN (Scaleway Edge Services) while backend stays on Serverless Containers. Same code, different deployment config.
