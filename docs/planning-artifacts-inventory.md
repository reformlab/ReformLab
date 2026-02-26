# Planning Artifacts Inventory — ReformLab

**Generated:** 2026-02-25

## Overview

This project is in the pre-implementation (planning) phase. All existing documents are planning artifacts produced through BMAD workflows. No source code has been written yet.

## Planning Artifacts

### Core Product Documents

| Document | Path | Date | Description |
|----------|------|------|-------------|
| Product Brief | `_bmad-output/planning-artifacts/product-brief-ReformLab-2026-02-23.md` | 2026-02-23 | Strategic direction, vision, target users, key differentiators |
| PRD | `_bmad-output/planning-artifacts/prd.md` | 2026-02-24 | Full product requirements: 35 functional requirements, 21 non-functional requirements |
| Architecture | `_bmad-output/planning-artifacts/architecture.md` | 2026-02-25 | Architecture decision document: layered design, adapter pattern, subsystems |
| UX Design | `_bmad-output/planning-artifacts/ux-design-specification.md` | 2026-02-24 | User experience specification: personas (Sophie, Marco, Claire), design challenges |

### Validation and Review

| Document | Path | Date | Description |
|----------|------|------|-------------|
| PRD Validation | `_bmad-output/planning-artifacts/prd-validation-report.md` | 2026-02-25 | PRD validation results |
| Validation Report | `_bmad-output/planning-artifacts/validation-report-2026-02-24.md` | 2026-02-24 | Additional validation report |
| Stakeholder Review | `_bmad-output/planning-artifacts/stakeholder-review-brief-ReformLab-2026-02-24.md` | 2026-02-24 | Stakeholder review brief |
| Implementation Readiness | `_bmad-output/planning-artifacts/implementation-readiness-report-2026-02-25.md` | 2026-02-25 | Implementation readiness assessment |

### Implementation Planning

| Document | Path | Date | Description |
|----------|------|------|-------------|
| Phase 1 Backlog | `_bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md` | 2026-02-25 | 7 epics, prioritized stories with story points |
| Sprint Change Proposal | `_bmad-output/planning-artifacts/sprint-change-proposal-2026-02-25.md` | 2026-02-25 | Sprint change proposal |

### Research

| Document | Path | Date | Description |
|----------|------|------|-------------|
| Domain Research | `_bmad-output/planning-artifacts/research/domain-generic-microsimulation-frameworks-research-2026-02-23.md` | 2026-02-23 | Generic microsimulation frameworks landscape |
| Technical Research | `_bmad-output/planning-artifacts/research/technical-entity-graph-data-modeling-and-vectorized-simulation-engines-research-2026-02-23.md` | 2026-02-23 | Entity graph data modeling and vectorized simulation engines |

### Brainstorming

| Document | Path | Date | Description |
|----------|------|------|-------------|
| Brainstorming Session | `_bmad-output/brainstorming/brainstorming-session-2026-02-23.md` | 2026-02-23 | Initial project brainstorming session |

## Document Lineage

```
Brainstorming Session (Feb 23)
  └── Research (Domain + Technical) (Feb 23)
      └── Product Brief (Feb 23)
          └── PRD (Feb 24)
              ├── UX Design Specification (Feb 24)
              ├── Validation Reports (Feb 24-25)
              ├── Stakeholder Review (Feb 24)
              └── Architecture (Feb 25)
                  ├── Phase 1 Backlog (Feb 25)
                  ├── Sprint Change Proposal (Feb 25)
                  └── Implementation Readiness Report (Feb 25)
```

## Key Strategic Decisions

1. **OpenFisca-first** — No custom policy engine; OpenFisca is the computation backend
2. **Adapter pattern** — Clean interface decouples orchestration from computation
3. **Dynamic orchestrator as core product** — Year-loop + pluggable step pipeline
4. **Open-data-first** — Works out of the box with public/synthetic data
5. **Governance by default** — Every run produces reproducible manifests
