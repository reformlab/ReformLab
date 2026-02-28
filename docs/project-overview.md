# Project Overview — ReformLab

**Generated:** 2026-02-28
**Status:** Phase 1 Complete (all 7 epics implemented, 1374 tests passing)

## Executive Summary

ReformLab is an OpenFisca-first environmental policy analysis platform. It addresses the operational gap between policy-calculation outputs and decision-ready environmental analysis by providing data harmonization, scenario templates, dynamic multi-year projection with vintage tracking, reproducibility governance, and user interfaces (Python API, notebooks, and no-code GUI).

The product targets policy analysts and researchers who need ten-year scenario projections, carbon tax modeling, subsidy/rebate/feebate evaluation, welfare indicators, and transparent run tracking without rebuilding tax-benefit logic.

**Phase 1 is fully implemented** — all 7 epics (46 stories) are complete with 72 Python source modules, 1374 tests, 80%+ code coverage, CI/CD pipeline, Docker deployment, and a React frontend.

## Quick Reference

| Attribute | Value |
|-----------|-------|
| **Project Name** | ReformLab |
| **Repository Type** | Multi-part (Python backend + React frontend) |
| **Primary Language** | Python 3.13+ |
| **Frontend** | React 19 + TypeScript + Vite + Tailwind CSS |
| **Core Dependency** | OpenFisca (tax-benefit computation engine) |
| **Architecture** | Layered — Adapter → Data → Templates → Orchestrator → Indicators → Governance → Interfaces |
| **Domain** | Environmental and distributional policy simulation |
| **Target Environment** | Single-machine / laptop (16GB RAM) |
| **Data Formats** | CSV/Parquet (interoperability contracts) |
| **Packaging** | pyproject.toml (hatchling), uv |
| **Testing** | pytest (1374 tests), vitest (frontend) |
| **Quality** | ruff, mypy (strict), eslint, 80%+ coverage |
| **CI/CD** | GitHub Actions → Docker → Kamal → Hetzner |
| **License** | Apache-2.0 |

## Technology Stack

| Category | Technology | Version/Notes |
|----------|-----------|---------------|
| **Language** | Python | 3.13+ |
| **Core Engine** | OpenFisca | Via adapter interface (optional dep) |
| **Package Management** | uv | Modern Python package manager |
| **Build System** | hatchling | pyproject.toml-based |
| **Data Processing** | PyArrow | Columnar data engine |
| **Schema Validation** | jsonschema | Workflow/scenario validation |
| **Serialization** | PyYAML | Scenario and config files |
| **Visualization** | matplotlib | Notebook charts |
| **Testing** | pytest, pytest-cov, nbmake | 1374 tests, notebook validation |
| **Linting** | ruff | Fast Python linter (E, F, I, W rules) |
| **Type Checking** | mypy | Strict mode |
| **Frontend** | React 19, TypeScript 5.9 | No-code GUI |
| **Frontend Build** | Vite 7 | Fast dev/build |
| **Frontend Styling** | Tailwind CSS 4 | Utility-first CSS |
| **Frontend Charts** | Recharts | Distributional bar charts |
| **Frontend UI** | Radix UI, shadcn/ui-inspired | Accessible primitives |
| **Frontend Testing** | Vitest, Testing Library | Component tests |
| **Containerization** | Docker | Python 3.13-slim base |
| **Deployment** | Kamal 2 | To Hetzner VPS |
| **CI/CD** | GitHub Actions | Push/PR triggers |

## Architecture Overview

The architecture follows a layered design where OpenFisca is the computation backend accessed through a clean adapter interface. The product builds everything above it:

```
┌─────────────────────────────────────────────────────┐
│  Interfaces                                          │
│  ├── Python API (run_scenario, create_scenario, ...) │
│  ├── Jupyter Notebooks (quickstart, advanced, demos) │
│  └── React No-Code GUI (scenario workspace)          │
├─────────────────────────────────────────────────────┤
│  Indicator Engine                                    │
│  ├── Distributional (income decile analysis)         │
│  ├── Geographic (regional aggregation)               │
│  ├── Welfare (winner/loser, equivalent variation)    │
│  ├── Fiscal (revenue, cost, balance tracking)        │
│  ├── Custom (user-defined derived formulas)          │
│  └── Comparison (multi-scenario side-by-side)        │
├─────────────────────────────────────────────────────┤
│  Governance                                          │
│  ├── Run Manifests (immutable, integrity-hashed)     │
│  ├── Assumption Capture (parameters, mappings)       │
│  ├── Lineage Graph (parent-child run tracking)       │
│  ├── Artifact Hashing (SHA-256, streaming)           │
│  ├── Reproducibility Checks (re-execute + verify)    │
│  ├── Benchmarking (fiscal/distributional validation) │
│  └── Memory Estimation (pre-flight safety)           │
├─────────────────────────────────────────────────────┤
│  Dynamic Orchestrator                                │
│  ├── Yearly Loop (t to t+n, deterministic)           │
│  ├── Step Pipeline (pluggable OrchestratorStep)      │
│  ├── Computation Step (adapter invocation)           │
│  ├── Carry-Forward Step (state propagation)          │
│  ├── Panel Output (household-by-year datasets)       │
│  └── Step Registry (registration + ordering)         │
├─────────────────────────────────────────────────────┤
│  Vintage Tracking                                    │
│  ├── Cohort Types (VintageCohort, VintageState)      │
│  ├── Transition Step (aging, retirement)             │
│  └── Configuration (rules, asset classes)            │
├─────────────────────────────────────────────────────┤
│  Scenario Templates                                  │
│  ├── Schema (PolicyType enum, YearSchedule, params)  │
│  ├── Carbon Tax (flat/progressive, redistribution)   │
│  ├── Subsidy (income caps, category restrictions)    │
│  ├── Rebate (lump-sum/progressive)                   │
│  ├── Feebate (pivot-point, fee/rebate rates)         │
│  ├── Registry (content-addressable versioning)       │
│  ├── Workflow Config (YAML/JSON orchestration)       │
│  └── Migration (schema version compatibility)        │
├─────────────────────────────────────────────────────┤
│  Data Layer                                          │
│  ├── Schemas (population, emission factors)          │
│  ├── Ingestion (CSV/Parquet, gzip, validation)       │
│  ├── Pipeline (registry, hashing, manifests)         │
│  └── Emission Factor Index (category/year lookup)    │
├─────────────────────────────────────────────────────┤
│  Computation Adapter                                 │
│  ├── Protocol (ComputationAdapter — runtime_checkable)│
│  ├── OpenFiscaAdapter (pre-computed CSV/Parquet)     │
│  ├── OpenFiscaApiAdapter (live Python API)           │
│  ├── MockAdapter (deterministic test backend)        │
│  ├── Compatibility Matrix (version governance)       │
│  ├── Input/Output Mapping (field translation)        │
│  └── Quality Checks (range, null, type validation)   │
└─────────────────────────────────────────────────────┘
```

## Implementation Status

**Phase 1 is complete.** All 7 epics and 46 stories have been implemented.

| Epic | Scope | Stories | Status |
|------|-------|---------|--------|
| EPIC-1 | Computation Adapter & Data Layer | 8 | Done |
| EPIC-2 | Scenario Templates & Registry | 7 | Done |
| EPIC-3 | Dynamic Orchestrator & Vintage Tracking | 7 | Done |
| EPIC-4 | Indicators & Scenario Comparison | 6 | Done |
| EPIC-5 | Governance & Reproducibility | 6 | Done |
| EPIC-6 | Interfaces (API, Notebooks, GUI) | 6 + 6-4b | Done |
| EPIC-7 | Quality Gates & Pilot Readiness | 5 | Done |

## Codebase Metrics

| Metric | Value |
|--------|-------|
| Python source files | 72 |
| Python test files | 93 |
| Total tests | 1,374 |
| Frontend source files | 46 |
| Frontend components | 20+ |
| Jupyter notebooks | 7 (2 user-facing + 5 demo) |
| Workflow examples | 3 (YAML + JSON) |
| Code coverage | 80%+ (enforced in CI) |
| Story files | 46 |

## Target Users

| Persona | Role | Primary Interface |
|---------|------|-------------------|
| **Sophie** | Applied Policy Analyst (Ministry) | No-code scenario workspace (React GUI) |
| **Marco** | Academic Researcher | Python API + Jupyter notebooks |
| **Claire** | Engaged Citizen (Phase 3) | Web application |

## Key Differentiators

1. **OpenFisca-first leverage** — Reuse mature open-source tax-benefit engine without reinventing
2. **Environmental policy template system** — Direct carbon tax, subsidy, rebate, feebate support
3. **Dynamic vintage projection** — 10+ year scenario operations with cohort aging
4. **Run governance by default** — Assumption transparency and manifest lineage as non-optional output
5. **No-code analyst workflow** — Scenario setup, comparison, and export without coding
6. **Reproducibility guarantees** — Seed control, artifact hashing, re-execution verification

## Phase 2+ Extensions

- Behavioral response steps (elasticities between yearly runs)
- System dynamics bridge (aggregate stock-flow outputs)
- Alternative computation backends (swap adapters)
- Public-facing citizen web application
- Real OpenFisca-France integration with production data

## Related Documentation

- [Architecture](./architecture.md) — Layered design, adapter pattern, subsystem details
- [Source Tree Analysis](./source-tree-analysis.md) — Annotated directory structure
- [Development Guide](./development-guide.md) — Setup, commands, conventions
- [Deployment Guide](./deployment-guide.md) — Docker, Kamal, Hetzner deployment
- [Compatibility Matrix](./compatibility.md) — Supported OpenFisca versions
- [Planning Artifacts](./planning-artifacts-inventory.md) — Full document inventory
