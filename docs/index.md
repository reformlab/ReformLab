# ReformLab — Project Documentation Index

**Generated:** 2026-02-25
**Status:** Pre-implementation (planning phase complete, ready for development)

## Project Overview

- **Type:** Monolith — OpenFisca-first environmental policy analysis platform
- **Primary Language:** Python 3.13+
- **Architecture:** Layered (Adapter → Data → Templates → Orchestrator → Indicators → Governance → Interfaces)
- **Domain:** Environmental and distributional policy simulation
- **Core Dependency:** OpenFisca (tax-benefit computation engine)
- **Target Environment:** Single-machine / laptop (16GB RAM)

## Quick Reference

- **Core Product:** Dynamic orchestrator with step-pluggable pipeline for multi-year projections
- **Data Contracts:** CSV/Parquet
- **Tooling:** pyproject.toml, uv, pytest, ruff, mypy
- **Phase 1 Scope:** 7 epics covering adapter, templates, orchestrator, indicators, governance, interfaces, and quality gates

## Generated Documentation

- [Project Overview](./project-overview.md) — Executive summary, tech stack, architecture overview, implementation phases
- [Architecture](./architecture.md) — Layered architecture, adapter pattern, orchestrator design, subsystems, data contracts
- [Source Tree Analysis](./source-tree-analysis.md) — Current project structure and planned source layout
- [Development Guide](./development-guide.md) — Prerequisites, setup instructions, build commands, CI strategy
- [Planning Artifacts Inventory](./planning-artifacts-inventory.md) — Complete inventory of all planning documents with lineage

## Roadmap

- [Product Delivery Roadmap](./../_bmad-output/roadmap/product-delivery-roadmap-2026-02-25.md) — Delivery path from planning to implementation phases
- [Go-to-Market & Ecosystem Strategy](./../_bmad-output/roadmap/go-to-market-and-ecosystem-strategy-2026-02-25.md) — Parallel adoption, outreach, and funding strategy

## Planning Artifacts (Source Documents)

### Core Product Documents
- [Product Brief](./../_bmad-output/planning-artifacts/product-brief-ReformLab-2026-02-23.md) — Strategic direction and vision
- [PRD](./../_bmad-output/planning-artifacts/prd.md) — Full product requirements (35 FRs, 21 NFRs)
- [Architecture Decision Document](./../_bmad-output/planning-artifacts/architecture.md) — Original architecture decisions
- [UX Design Specification](./../_bmad-output/planning-artifacts/ux-design-specification.md) — Persona-driven UX design

### Implementation Planning
- [Phase 1 Backlog](./../_bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md) — 7 epics with prioritized stories
- [Implementation Readiness Report](./../_bmad-output/planning-artifacts/implementation-readiness-report-2026-02-25.md) — Readiness assessment
- [Sprint Change Proposal](./../_bmad-output/planning-artifacts/sprint-change-proposal-2026-02-25.md) — Sprint adjustments

### Validation
- [PRD Validation Report](./../_bmad-output/planning-artifacts/prd-validation-report.md) — PRD quality validation
- [Validation Report](./../_bmad-output/planning-artifacts/validation-report-2026-02-24.md) — Additional validation
- [Stakeholder Review Brief](./../_bmad-output/planning-artifacts/stakeholder-review-brief-ReformLab-2026-02-24.md) — Stakeholder feedback

### Research
- [Domain Research](./../_bmad-output/planning-artifacts/research/domain-generic-microsimulation-frameworks-research-2026-02-23.md) — Microsimulation frameworks landscape
- [Domain Research (French Open Data)](./../_bmad-output/planning-artifacts/research/domain-french-open-data-microsimulation-research-2026-02-25.md) — French open-data sources and applicability
- [Market Research](./../_bmad-output/planning-artifacts/research/market-microsimulation-platform-research-2026-02-25.md) — Market landscape, competitors, and positioning
- [Technical Research](./../_bmad-output/planning-artifacts/research/technical-entity-graph-data-modeling-and-vectorized-simulation-engines-research-2026-02-23.md) — Entity graph and vectorized engines

### Brainstorming
- [Brainstorming Session](./../_bmad-output/brainstorming/brainstorming-session-2026-02-23.md) — Initial project ideation

### Communication Deliverables
- [Audience Narratives and Story Pack](./../_bmad-output/communication/audience-narratives-2026-02-25.md) — Multi-audience narrative assets (public, expert, investor)
- [Email Outreach Pack (French)](./../_bmad-output/communication/email-outreach-french-2026-02-25.md) — Ready-to-send outreach emails and adaptation notes

## Getting Started

This project is in the **pre-implementation phase**. All planning is complete and development is ready to begin.

**To start development:**
1. Review the [Architecture](./architecture.md) for the layered design and adapter pattern
2. Review the [Phase 1 Backlog](./../_bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md) for prioritized stories
3. Begin with EPIC-1: Computation Adapter and Data Layer (BKL-101)
4. Follow the [Development Guide](./development-guide.md) for tooling setup

**For brownfield PRD workflows:**
Point any future PRD workflow to this index file: `docs/index.md`
