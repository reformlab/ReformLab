# ReformLab

OpenFisca-first environmental policy analysis platform. Builds data preparation, scenario templates, dynamic multi-year orchestration with vintage tracking, indicators, governance, and user interfaces on top of OpenFisca's tax-benefit computation engine.

## Tech Stack

- Python 3.13+, uv, pyproject.toml
- OpenFisca (tax-benefit backend, accessed via adapter interface)
- CSV/Parquet data contracts
- pytest, ruff, mypy
- Target: single-machine / laptop (16GB RAM)

## Architecture

Layered design: Computation Adapter → Data Layer → Scenario Templates → Dynamic Orchestrator → Indicators → Governance → Interfaces (Python API, Notebooks, No-Code GUI).

The **dynamic orchestrator is the core product** — not a computation engine. OpenFisca handles policy calculations; this project handles everything above that.

## Key Decisions

- **OpenFisca-first**: No custom policy engine, formula compiler, or entity graph engine. See `sprint-change-proposal-2026-02-25.md` for the strategic pivot rationale.
- **Open-data-first**: Works out of the box with public data (synthetic populations, emission factors). Custom data optional.
- **Adapter pattern**: Computation backends can be swapped without changing orchestration layer.
- **France/Europe first**: Initial focus on French household carbon-tax and redistribution scenarios, with European data sources (INSEE, Eurostat, EU-SILC).

## Project Structure

```
src/                    — Application code (not yet created)
tests/                  — Tests (not yet created)
docs/                   — Project documentation
_bmad/                  — BMAD framework (do not edit manually)
_bmad-output/
  planning-artifacts/   — PRD, architecture, UX, backlog, research
  implementation-artifacts/ — Sprint/story artifacts (during dev)
  brainstorming/        — Brainstorming sessions
```

## Planning Artifacts (read these for full context)

- `_bmad-output/planning-artifacts/prd.md` — Product requirements
- `_bmad-output/planning-artifacts/architecture.md` — Technical architecture
- `_bmad-output/planning-artifacts/ux-design-specification.md` — UX design
- `_bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md` — Epics and stories
- `_bmad-output/planning-artifacts/sprint-change-proposal-2026-02-25.md` — OpenFisca pivot

## Current Status

Phase 3 (Solutioning) nearly complete. Next step: Implementation Readiness Check, then Sprint Planning and development.

## Conventions

- Follow existing code patterns and project structure
- All runs must be deterministic and reproducible
- Data contracts use CSV/Parquet at ingestion boundaries
- Assumption transparency is non-optional — every run produces a manifest
