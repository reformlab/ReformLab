# ReformLab

OpenFisca-first environmental policy analysis platform. Builds data preparation, scenario templates, dynamic multi-year orchestration with vintage tracking, indicators, governance, and user interfaces on top of OpenFisca's tax-benefit computation engine.

## Tech Stack

- Python 3.13+, uv, pyproject.toml
- OpenFisca (tax-benefit backend, accessed via adapter interface)
- CSV/Parquet data contracts
- pytest, ruff, mypy
- Target: single-machine / laptop (16GB RAM)

## Architecture

Layered design: Computation Adapter → Data Layer → Scenario Templates → Dynamic Orchestrator → Discrete Choice / Vintage / Calibration → Indicators → Population → Governance → Visualization → Server → Interfaces (Python API, Notebooks, No-Code GUI).

The **dynamic orchestrator is the core product** — not a computation engine. OpenFisca handles policy calculations; this project handles everything above that.

## Key Decisions

- **OpenFisca-first**: No custom policy engine, formula compiler, or entity graph engine.
- **Open-data-first**: Works out of the box with public data (synthetic populations, emission factors). Custom data optional.
- **Adapter pattern**: Computation backends can be swapped without changing orchestration layer.
- **France/Europe first**: Initial focus on French household carbon-tax and redistribution scenarios, with European data sources (INSEE, Eurostat, EU-SILC).

## Project Structure

```
src/                    — Application code
tests/                  — Tests
docs/                   — Project documentation
frontend/               — React 19 / TypeScript frontend
_bmad/                  — BMAD framework (do not edit manually)
_bmad-output/
  planning-artifacts/   — PRD, architecture, UX, active epics
  implementation-artifacts/ — Active sprint/story artifacts
```

## Planning Artifacts (read these for full context)

- `_bmad-output/planning-artifacts/prd.md` — Product requirements
- `_bmad-output/planning-artifacts/architecture.md` — Technical architecture
- `_bmad-output/planning-artifacts/ux-design-specification.md` — UX design
- `_bmad-output/planning-artifacts/epics.md` — Active epics (28, 29 archived next cycle); epics 1–24 complete and archived in git history

## Current Status

Epics 23–29 complete. Latest closed: Epic 29 (custom OpenFisca variables — `montant_subvention`, `eligible_subvention`, `malus_ecologique`, `aide_energie`) finished 2026-05-23. See `_bmad-output/implementation-artifacts/sprint-status.yaml` for authoritative per-story state.

## Conventions

- Follow existing code patterns and project structure
- All runs must be deterministic and reproducible
- Data contracts use CSV/Parquet at ingestion boundaries
- Assumption transparency is non-optional — every run produces a manifest
