# ReformLab

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)
[![CI](https://github.com/reformlab/ReformLab/actions/workflows/ci.yml/badge.svg)](https://github.com/reformlab/ReformLab/actions/workflows/ci.yml)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)

OpenFisca-first environmental policy analysis platform.

## What it does

ReformLab simulates the distributional impact of environmental tax-and-transfer policies on household populations. It wraps [OpenFisca](https://openfisca.org) as a computation backend and adds data preparation, scenario templates, dynamic multi-year orchestration with vintage tracking, indicators, and governance layers. For example: simulate a €100/tCO₂ carbon tax with lump-sum redistribution across French households over 10 years and compare distributional outcomes.

## Quick start

```bash
git clone https://github.com/reformlab/ReformLab.git
cd ReformLab
uv sync --all-extras
uv run pytest
```

For the frontend:

```bash
cd frontend
npm install
npm run dev
```

First launch loads a demo scenario automatically — a carbon tax with dividend policy on a French synthetic population — so you can explore the workspace immediately.

## Features

### Four-Stage Workspace

The ReformLab GUI organizes policy analysis into four stages:

- **Stage 1: Policies & Portfolio** — Build policy bundles from templates, compose multiple policies, and manage conflict resolution
- **Stage 2: Population** — Select built-in populations, explore data profiles, or generate synthetic populations via data fusion
- **Stage 3: Engine** — Configure time horizon, set simulation parameters, and validate before execution
- **Stage 4: Run / Results / Compare** — Execute simulations, view distributional charts, and compare outcomes across scenarios

### Python API & Notebooks

Programmatic access via Python API for batch simulations and custom analysis workflows.

## Architecture

**Backend:** Data Layer → Scenario Templates → Dynamic Orchestrator → Indicators → Governance → FastAPI

**Frontend:** Four-stage workspace (Policies, Population, Engine, Results) with OpenFisca as external computation backend

```mermaid
graph LR
    OF[OpenFisca] -->|adapter| DL[Data Layer]
    DL --> ST[Scenario Templates]
    ST --> DO[Dynamic Orchestrator]
    DO --> IN[Indicators]
    IN --> GV[Governance]
    GV --> API[FastAPI]
    GV --> GUI[Four-Stage Workspace]
    GUI --> P1[Stage 1: Policies]
    GUI --> P2[Stage 2: Population]
    GUI --> P3[Stage 3: Engine]
    GUI --> P4[Stage 4: Results]
```

## Live services

| Service | URL | Description |
| --- | --- | --- |
| Website | <https://reform-lab.eu> | Public website |
| App | <https://app.reform-lab.eu> | Simulation frontend |
| API | <https://api.reform-lab.eu> | FastAPI backend |
| Logs | <https://logs.reform-lab.eu> | Container log viewer (Dozzle) |
| Monitor | <https://monitor.reform-lab.eu> | System metrics dashboard (Glances) |

## License

AGPL-3.0-or-later. See [LICENSE](LICENSE).

## Citation

If you use ReformLab in academic work, please cite it using the metadata in [CITATION.cff](CITATION.cff).
