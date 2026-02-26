# ReformLab

**OpenFisca-first environmental policy analysis platform.**

ReformLab builds the operational layer that sits between [OpenFisca](https://openfisca.org)'s tax-benefit computation engine and the policy analysts who need answers: data preparation, scenario templates, dynamic multi-year orchestration with vintage tracking, distributional indicators, governance, and user interfaces.

> OpenFisca calculates policy. ReformLab turns calculations into analysis.

## Why

Policy microsimulation tools are powerful but hard to use. Analysts spend more time wrangling data pipelines and tracking assumptions than running scenarios. ReformLab closes that gap with:

- **Scenario templates** for carbon taxes, subsidies, rebates, and feebates
- **10+ year projections** with vintage tracking (vehicles, heating systems age realistically)
- **Assumption transparency** — every run produces a full manifest, no hidden defaults
- **Multiple interfaces** — Python API for researchers, notebooks for exploration, no-code GUI for analysts

## Quick start

```bash
# Prerequisites: Python 3.13+, uv
git clone https://github.com/lucas-vivier/Microsimulation.git
cd Microsimulation

# Install dependencies
uv sync

# Run tests
uv run pytest

# Type check
uv run mypy src

# Lint
uv run ruff check src tests
```

## Architecture

```
Interfaces (Python API · Notebooks · No-Code GUI)
  └─ Indicator Engine (distributional · welfare · fiscal)
     └─ Governance (manifests · assumptions · lineage)
        └─ Dynamic Orchestrator (year loop + step pipeline)
           ├─ Vintage Transitions
           ├─ State Carry-Forward
           └─ Scenario Templates (carbon tax · subsidies · rebates)
              └─ Data Layer (ingestion · open data · synthetic populations)
                 └─ Computation Adapter
                    └─ OpenFisca (tax-benefit engine)
```

The **dynamic orchestrator is the core product** — not a computation engine. OpenFisca handles policy calculations; ReformLab handles everything above that.

## Project structure

```
src/reformlab/
├── computation/     Adapter interface, OpenFisca backends, version compat
└── data/            Ingestion pipelines, schemas, emission factors

tests/               Mirrors src/ — 207 tests, strict typing
docs/                Architecture, dev guide, compatibility matrix
_bmad-output/        Planning artifacts, branding, communication materials
```

## Status

**Phase 1 — EPIC-1 in progress.** The computation adapter and data layer are implemented with two OpenFisca backends (in-process and API), CSV/Parquet ingestion, data quality checks, and a compatibility matrix. See [sprint status](_bmad-output/implementation-artifacts/sprint-status.yaml) for current progress.

| Epic | Scope | Status |
|------|-------|--------|
| EPIC-1 | Computation Adapter & Data Layer | In progress |
| EPIC-2 | Scenario Templates & Registry | Backlog |
| EPIC-3 | Dynamic Orchestrator & Vintage Tracking | Backlog |
| EPIC-4 | Indicators & Scenario Comparison | Backlog |
| EPIC-5 | Governance & Reproducibility | Backlog |
| EPIC-6 | Interfaces (API, Notebooks, GUI) | Backlog |
| EPIC-7 | Quality Gates & Pilot Readiness | Backlog |

## Tech stack

| | |
|---|---|
| Language | Python 3.13+ |
| Engine | [OpenFisca](https://openfisca.org) via adapter interface |
| Data | CSV/Parquet contracts, PyArrow |
| Package manager | [uv](https://docs.astral.sh/uv/) |
| Testing | pytest (strict, 207 tests) |
| Linting | ruff |
| Type checking | mypy (strict mode, `.pyi` stubs for all modules) |
| Target | Single machine, 16 GB RAM |

## Documentation

- [Project overview](docs/project-overview.md) — executive summary and architecture
- [Architecture](docs/architecture.md) — layered design, adapter pattern, data contracts
- [Development guide](docs/development-guide.md) — setup, commands, conventions
- [Compatibility matrix](docs/compatibility.md) — supported OpenFisca versions
- [Planning artifacts](docs/index.md) — full document index (PRD, UX, backlog, research)

## Contributing

This project is in early development. Contribution guidelines will be established as the project matures. In the meantime:

1. All code changes require tests
2. `uv run pytest && uv run mypy src && uv run ruff check src tests` must pass
3. Every module gets a `.pyi` stub file
4. Never call OpenFisca directly — always go through `ComputationAdapter`

## License

[Apache-2.0](LICENSE)
