# ReformLab — Project Documentation Index

**Generated:** 2026-02-28
**Status:** Phase 1 Complete (all 7 epics implemented, 1374 tests passing)

## Project Overview

- **Type:** Multi-part — Python backend + React frontend
- **Primary Language:** Python 3.13+ (backend), TypeScript (frontend)
- **Architecture:** Layered (Adapter → Data → Templates → Orchestrator → Indicators → Governance → Interfaces)
- **Domain:** Environmental and distributional policy simulation
- **Core Dependency:** OpenFisca (tax-benefit computation engine)
- **Target Environment:** Single-machine / laptop (16GB RAM)

## Quick Reference

- **Core Product:** Dynamic orchestrator with step-pluggable pipeline for multi-year projections
- **Policy Templates:** Carbon tax, subsidy, rebate, feebate (4 policy types)
- **Data Contracts:** CSV/Parquet via PyArrow
- **Tooling:** pyproject.toml, uv, pytest (1374 tests), ruff, mypy (strict)
- **Frontend:** React 19, Vite 7, Tailwind CSS 4, Recharts
- **CI/CD:** GitHub Actions → Docker → Kamal → Hetzner
- **Codebase:** 72 Python modules, 46 frontend files, 7 notebooks

## Generated Documentation

- [Project Overview](./project-overview.md) — Executive summary, tech stack, architecture overview, implementation status
- [Architecture](./architecture.md) — Layered architecture, adapter pattern, subsystem details, data contracts
- [Source Tree Analysis](./source-tree-analysis.md) — Full annotated directory structure with all 200+ files
- [Development Guide](./development-guide.md) — Prerequisites, setup, build commands, CI pipeline, conventions
- [Deployment Guide](./deployment-guide.md) — Docker, Kamal 2, Hetzner deployment
- [Compatibility Matrix](./compatibility.md) — Supported OpenFisca versions
- [Planning Artifacts Inventory](./planning-artifacts-inventory.md) — Complete inventory of 82 planning and implementation documents
- [Pilot Checklist](./pilot-checklist.md) — Pilot bundle validation checklist
- [Phase 1 Exit Checklist](./phase-1-exit-checklist.md) — Phase 1 completion criteria

## Roadmap

- [Product Delivery Roadmap](./../_bmad-output/roadmap/product-delivery-roadmap-2026-02-25.md) — Delivery path from planning to implementation phases
- [Go-to-Market & Ecosystem Strategy](./../_bmad-output/roadmap/go-to-market-and-ecosystem-strategy-2026-02-25.md) — Parallel adoption, outreach, and funding strategy

## Planning Artifacts (Source Documents)

### Core Product Documents

- [Product Brief](./../_bmad-output/planning-artifacts/product-brief-ReformLab-2026-02-23.md) — Strategic direction and vision
- [PRD](./../_bmad-output/planning-artifacts/prd.md) — Full product requirements (35 FRs, 21 NFRs)
- [Architecture Decision Document](./../_bmad-output/planning-artifacts/architecture.md) — Original architecture decisions
- [Architecture Diagrams](./../_bmad-output/planning-artifacts/architecture-diagrams.md) — Visual architecture representations
- [UX Design Specification](./../_bmad-output/planning-artifacts/ux-design-specification.md) — Persona-driven UX design

### Implementation Planning

- [Phase 1 Backlog](./../_bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md) — 7 epics with 46 prioritized stories
- [Implementation Readiness Report](./../_bmad-output/planning-artifacts/implementation-readiness-report-2026-02-25.md) — Readiness assessment
- [Sprint Change Proposal](./../_bmad-output/planning-artifacts/sprint-change-proposal-2026-02-25.md) — OpenFisca-first pivot rationale
- [Sprint Status](./../_bmad-output/implementation-artifacts/sprint-status.yaml) — Current sprint tracking (all 7 epics done)

### Validation

- [PRD Validation Report](./../_bmad-output/planning-artifacts/prd-validation-report.md) — PRD quality validation
- [Validation Report](./../_bmad-output/planning-artifacts/validation-report-2026-02-24.md) — Cross-artifact validation
- [Stakeholder Review Brief](./../_bmad-output/planning-artifacts/stakeholder-review-brief-ReformLab-2026-02-24.md) — Stakeholder feedback

### Research

- [Domain Research — Microsimulation Frameworks](./../_bmad-output/planning-artifacts/research/domain-generic-microsimulation-frameworks-research-2026-02-23.md)
- [Domain Research — French Open Data](./../_bmad-output/planning-artifacts/research/domain-french-open-data-microsimulation-research-2026-02-25.md)
- [Market Research — Microsimulation Platforms](./../_bmad-output/planning-artifacts/research/market-microsimulation-platform-research-2026-02-25.md)
- [Market Research — French Models](./../_bmad-output/planning-artifacts/research/market-french-microsimulation-models-research-2026-02-27.md)
- [Market Research — GovTech Funding](./../_bmad-output/planning-artifacts/research/market-funding-and-credits-for-govtech-policy-tools-research-2026-02-28.md)
- [Technical Research — Entity Graph & Vectorized Engines](./../_bmad-output/planning-artifacts/research/technical-entity-graph-data-modeling-and-vectorized-simulation-engines-research-2026-02-23.md)

### Brainstorming

- [Session 1 (Feb 23)](./../_bmad-output/brainstorming/brainstorming-session-2026-02-23.md) — Initial project ideation
- [Session 2 (Feb 25)](./../_bmad-output/brainstorming/brainstorming-session-2026-02-25.md) — Architecture refinement
- [Session 3 (Feb 27)](./../_bmad-output/brainstorming/brainstorming-session-2026-02-27.md) — Implementation insights

### Communication Deliverables

- [Audience Narratives and Story Pack](./../_bmad-output/communication/audience-narratives-2026-02-25.md) — Multi-audience narrative assets
- [Email Outreach Pack (French)](./../_bmad-output/communication/email-outreach-french-2026-02-25.md) — Ready-to-send outreach emails
- [Market One-Pager](./../_bmad-output/communication/market-one-pager-2026-02-25.md) — Concise market positioning

### Branding & Presentations

- [Visual Identity Guide](./../_bmad-output/branding/visual-identity-guide.md) — Brand colors, typography, style
- [Pitch Deck Content](./../_bmad-output/presentations/pitch-deck-content-2026-02-25.md) — Slide-by-slide pitch narrative

### Website Content

- [Homepage Narrative](./../_bmad-output/website-content/homepage-narrative-2026-02-25.md)
- [Features](./../_bmad-output/website-content/features-2026-02-25.md)
- [How It Works](./../_bmad-output/website-content/how-it-works-2026-02-25.md)
- [Use Cases](./../_bmad-output/website-content/use-cases-2026-02-25.md)
- [FAQ](./../_bmad-output/website-content/faq-2026-02-25.md)

## Getting Started

This project has completed **Phase 1 implementation**. All 7 epics and 46 stories are done.

**To explore the platform:**

1. Install: `uv sync && uv run pytest` (verify 1374 tests pass)
2. Open the [quickstart notebook](../notebooks/quickstart.ipynb) for a guided tour
3. Open the [advanced notebook](../notebooks/advanced.ipynb) for multi-year scenarios
4. Review the [Architecture](./architecture.md) for subsystem details
5. Review the [Development Guide](./development-guide.md) for setup and conventions

**To run the frontend:**

1. `cd frontend && npm install && npm run dev`
2. Open `http://localhost:5173` in your browser

**For Phase 2 planning:**

Point any future PRD workflow to this index file: `docs/index.md`
