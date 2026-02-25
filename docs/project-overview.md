# Project Overview — Microsimulation

**Generated:** 2026-02-25
**Status:** Pre-implementation (planning phase)

## Executive Summary

Microsimulation is an OpenFisca-first environmental policy analysis platform. It addresses the operational gap between policy-calculation outputs and decision-ready environmental analysis by adding data harmonization, scenario templates, dynamic multi-year projection with vintage tracking, reproducibility governance, and user interfaces (notebook + no-code GUI).

The product targets policy analysts and researchers who need ten-year scenario projections, subsidy modeling, welfare indicators, and transparent run tracking without rebuilding tax-benefit logic.

## Quick Reference

| Attribute | Value |
|-----------|-------|
| **Project Name** | Microsimulation |
| **Repository Type** | Monolith |
| **Primary Language** | Python 3.13+ |
| **Core Dependency** | OpenFisca (tax-benefit computation engine) |
| **Architecture** | Layered — Adapter → Data → Templates → Orchestrator → Indicators → Governance → Interfaces |
| **Domain** | Environmental and distributional policy simulation |
| **Target Environment** | Single-machine / laptop (16GB RAM) |
| **Data Formats** | CSV/Parquet (interoperability contracts) |
| **Packaging** | pyproject.toml, uv, pytest, ruff, mypy |
| **Project Context** | Greenfield product layer on mature open-source core |
| **Complexity** | High |

## Technology Stack

| Category | Technology | Version/Notes |
|----------|-----------|---------------|
| **Language** | Python | 3.13+ |
| **Core Engine** | OpenFisca | Via adapter interface (version-pinned) |
| **Package Management** | uv | Modern Python package manager |
| **Build Config** | pyproject.toml | Standard Python packaging |
| **Testing** | pytest | Unit, contract, integration |
| **Linting** | ruff | Fast Python linter |
| **Type Checking** | mypy | Static type analysis |
| **Data I/O** | CSV/Parquet | Primary data contracts |
| **Interfaces** | Python API, Jupyter Notebooks, No-Code GUI | Multi-persona access |

## Architecture Overview

The architecture follows a layered design where OpenFisca is the computation backend accessed through a clean adapter interface. The product builds everything above it:

```
Interfaces (Python API, Notebooks, No-Code GUI)
  └── Indicator Engine (distributional/welfare/fiscal)
      └── Governance (manifests, assumptions, lineage)
          └── Dynamic Orchestrator (year loop + step pipeline)
              ├── Vintage Transitions
              ├── State Carry-Forward
              └── [Phase 2: Behavioral Response Steps]
              └── Scenario Template Layer (environmental policies)
                  └── Data Layer (ingestion, open data, synthetic pop)
                      └── Computation Adapter Interface
                          └── OpenFiscaAdapter (primary)
```

## Subsystems (Planned)

1. **`computation/`** — Adapter interface + OpenFiscaAdapter. CSV/Parquet ingestion, version-pinned contracts.
2. **`data/`** — Open data ingestion, synthetic population generation, data transformation pipelines.
3. **`templates/`** — Environmental policy templates (carbon tax, subsidies, rebates, feebates) and scenario registry.
4. **`orchestrator/`** — Dynamic yearly loop with step-pluggable pipeline. Deterministic sequencing, seed control.
5. **`vintage/`** — Cohort/vintage state management. Tracks asset classes (vehicles, heating) through time.
6. **`indicators/`** — Distributional, welfare, fiscal, and custom indicator computation.
7. **`governance/`** — Run manifests, assumption logs, lineage, output hashes.
8. **`interfaces/`** — Python API, notebook workflows, early no-code GUI.

## Implementation Phases

### Phase 1 (MVP) — 7 Epics

1. **EPIC-1**: Computation Adapter and Data Layer
2. **EPIC-2**: Scenario Templates and Registry
3. **EPIC-3**: Step-Pluggable Dynamic Orchestrator and Vintage Tracking
4. **EPIC-4**: Indicators and Scenario Comparison
5. **EPIC-5**: Governance and Reproducibility
6. **EPIC-6**: Interfaces (Python API, Notebooks, Early No-Code GUI)
7. **EPIC-7**: Quality Gates, Benchmarks, and Pilot Readiness

### Phase 2+ Extensions

- Behavioral response steps (elasticities between yearly runs)
- System dynamics bridge (aggregate stock-flow outputs)
- Alternative computation backends (swap adapters)
- Public-facing citizen web application

## Target Users

| Persona | Role | Primary Interface |
|---------|------|-------------------|
| **Sophie** | Applied Policy Analyst (Ministry) | No-code scenario workspace |
| **Marco** | Academic Researcher | Python API + Jupyter notebooks |
| **Claire** | Engaged Citizen (Phase 3) | Web application |

## Key Differentiators

1. **OpenFisca-first leverage** — Reuse mature open-source tax-benefit engine
2. **Environmental policy template system** — Direct carbon tax and subsidy support
3. **Dynamic vintage projection** — 10+ year scenario operations
4. **Run governance by default** — Assumption transparency as non-optional output
5. **No-code analyst workflow** — Scenario setup/comparison without coding

## Related Documentation

- [Architecture](./architecture.md)
- [Source Tree Analysis](./source-tree-analysis.md)
- [Development Guide](./development-guide.md)
- [Planning Artifacts Inventory](./planning-artifacts-inventory.md)
