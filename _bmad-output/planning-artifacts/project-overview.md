# Project Overview — ReformLab

**Generated:** 2026-03-08
**Status:** Phase 2 Complete (Epics 1–17, 3,143 tests passing)

## What Is ReformLab?

ReformLab is an **environmental policy analysis platform**. It simulates the effects of carbon taxes, subsidies, rebates, and other environmental policies on household populations over multiple years.

**The key idea:** You bring a population (who are the households?), a policy (what changes?), and a time horizon (how many years?) — ReformLab shows you what happens: who wins, who loses, how much revenue it generates, and how behavior changes over time.

## Who Is It For?

- **Policy analysts** who want to test "what if" scenarios before proposing legislation
- **Researchers** who need reproducible simulation results for academic papers
- **Decision-makers** who need clear visualizations of policy trade-offs

## What Makes It Different?

1. **OpenFisca-first** — Leverages existing tax-benefit computation engines instead of building a custom one
2. **Orchestration, not computation** — The value is in the multi-year simulation loop, behavioral modeling, and portfolio comparison — not in tax formula calculation
3. **Reproducibility by design** — Every run produces a manifest with all seeds, hashes, and assumptions
4. **Open-data-first** — Works out of the box with public data (INSEE, Eurostat, ADEME, SDES)
5. **Three interfaces** — Python API, Jupyter notebooks, and a no-code GUI

## Project Structure

ReformLab is a **multi-part** project:

| Part | Technology | Purpose |
| ---- | ---------- | ------- |
| Backend | Python 3.13+, FastAPI, PyArrow | All domain logic, simulation engine, API |
| Frontend | React 19, TypeScript, Tailwind v4 | No-code GUI for visual workflow |

## Scale

| Metric | Count |
| ------ | ----: |
| Python source files | 147 |
| Python test files | 190 |
| Tests collected | 3,143 |
| Frontend source files | 80 |
| Frontend test files | 35 |
| Backend subsystems | 13 |
| API endpoints | 20+ |
| GUI screens | 9 |
| Jupyter notebooks | 6 |
| Epics completed | 17 |
| Story files | 105+ |

## Technology Stack Summary

**Backend:** Python 3.13+, uv, FastAPI, PyArrow, OpenFisca (optional), scipy, pytest, ruff, mypy (strict)

**Frontend:** React 19, TypeScript 5.9, Vite 7, Tailwind v4, Recharts, Radix UI, Vitest

**Infrastructure:** GitHub Actions CI, Docker, Kamal 2, Hetzner VPS, Traefik (HTTPS)

## Implementation History

### Phase 1 — Core Platform (Epics 1–10)

Built the foundation: computation adapter, data ingestion, scenario templates, multi-year orchestrator, indicators, governance/manifests, Python API, notebooks, GUI prototype, and validation.

### Phase 2 — Advanced Features (Epics 11–17)

Added population generation from institutional data (INSEE, Eurostat, ADEME, SDES), policy portfolios with conflict resolution, custom templates (vehicle malus, energy poverty aid), discrete choice behavioral modeling (vehicle/heating investment), calibration against observed transition rates, replication packages, and the full no-code GUI with data fusion, portfolio designer, comparison dashboard, and behavioral decision viewer.

## Key Documentation

| Document | What It Covers |
| -------- | -------------- |
| [Architecture](./architecture.md) | System design, patterns, data flow, subsystem reference |
| [Source Tree](./source-tree-analysis.md) | Annotated directory structure |
| [Development Guide](./development-guide.md) | Setup, commands, conventions |
| [Deployment Guide](./deployment-guide.md) | Docker, Kamal, Hetzner, CI/CD |
| [PRD](./prd.md) | Product requirements |
| [UX Design](./ux-design-specification.md) | UX patterns and specifications |

## License

AGPL-3.0-or-later
