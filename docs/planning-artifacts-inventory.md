# Planning Artifacts Inventory — ReformLab

**Generated:** 2026-03-08
**Status:** Phase 2 Complete (all planning + implementation artifacts present)

## How to Use This Inventory

This document catalogs every planning and implementation artifact produced during the project. Use it to find context for decisions, understand implementation history, or locate specific story specifications.

---

## Summary

| Category | Count |
| -------- | ----: |
| Planning artifacts | 16 |
| Implementation artifacts (story files) | 105 |
| Retrospectives | 4 |
| Brainstorming sessions | 4 |
| Other artifacts (branding, communication, presentations, website) | 6+ dirs |
| **Total** | **135+** |

---

## Planning Artifacts

Located in `_bmad-output/planning-artifacts/`:

| Artifact | Purpose |
| -------- | ------- |
| `prd.md` | Product Requirements Document — full feature requirements |
| `architecture.md` | Technical architecture design decisions |
| `architecture-diagrams.md` | Mermaid diagrams for architecture |
| `ux-design-specification.md` | UX patterns and interface specifications |
| `epics.md` | Epic and story breakdown (Epics 1–17) |
| `product-brief-ReformLab-2026-02-23.md` | Initial product brief |
| `phase-1-implementation-backlog-2026-02-25.md` | Phase 1 backlog with prioritized stories |
| `sprint-change-proposal-2026-02-25.md` | OpenFisca pivot rationale |
| `sprint-change-proposal-2026-03-02.md` | Phase 2 scope adjustment |
| `sprint-change-proposal-readiness-2026-02-25.md` | Readiness check for sprint change |
| `phase-2-design-note-discrete-choice-household-decisions.md` | Discrete choice modeling design |
| `implementation-readiness-report-2026-02-25.md` | Phase 1 readiness assessment |
| `implementation-readiness-report-2026-03-03.md` | Phase 2 readiness assessment |
| `prd-validation-report.md` | PRD validation results |
| `validation-report-2026-02-24.md` | Early validation report |
| `stakeholder-review-brief-ReformLab-2026-02-24.md` | Stakeholder review brief |

---

## Implementation Artifacts

Located in `_bmad-output/implementation-artifacts/`:

### Epic 1 — Computation Adapter and Data Layer (8 stories)

Stories 1.1–1.8: ComputationAdapter protocol, CSV/Parquet ingestion, field mapping, open-data pipeline, quality checks, OpenFisca API mode, compatibility matrix, project scaffold.

### Epic 2 — Scenario Templates (7 stories)

Stories 2.1–2.7: Template schema, carbon tax pack, subsidy/rebate/feebate packs, scenario registry, cloning, schema migration, YAML workflow configuration.

### Epic 3 — Dynamic Orchestrator (7 stories)

Stories 3.1–3.7: Yearly loop, step interface, carry-forward, vintage transitions, adapter integration, seed/log controls, panel output.

### Epic 4 — Indicators (6 stories)

Stories 4.1–4.6: Distributional, geographic, welfare, fiscal indicators, scenario comparison, custom formula indicators.

### Epic 5 — Governance (6 stories)

Stories 5.1–5.6: Run manifest, assumption capture, lineage graph, artifact hashing, reproducibility checks, warning system.

### Epic 6 — Interfaces (7 stories)

Stories 6.1–6.7: Python API, quickstart notebook, advanced notebook, static GUI prototype, backend wiring, export actions, error UX.

### Epic 7 — Validation and Pilot (5 stories)

Stories 7.1–7.5: Benchmark validation, memory limits, CI quality gates, pilot run, Phase 1 exit checklist.

### Epic 8 — OpenFisca Integration Spike (2 stories)

Stories 8.1–8.2: E2E integration spike, scale validation (100k population).

### Epic 9 — OpenFisca Compatibility (4 stories)

Stories 9.2–9.5: Multi-entity output arrays, variable periodicity, population 4-entity format, reference test suite.

### Epic 10 — Template Refactoring (2 stories)

Stories 10.1–10.2: Rename parameters to policy, infer policy type from parameters class.

### Epic 11 — Population Generation (8 stories)

Stories 11.1–11.8: DataSourceLoader protocol, INSEE/Eurostat/ADEME/SDES loaders, merge methods (uniform, IPF, conditional sampling), population pipeline, validation against marginals, French household example.

### Epic 12 — Policy Portfolios (5 stories)

Stories 12.1–12.5: PolicyPortfolio dataclass, compatibility validation, orchestrator extension, registry versioning, multi-portfolio comparison notebook.

### Epic 13 — Custom Templates (4 stories)

Stories 13.1–13.4: Custom template API, vehicle malus template, energy poverty aid template, portfolio validation + notebook.

### Epic 14 — Discrete Choice Modeling (7 stories)

Stories 14.1–14.7: DiscreteChoiceStep, conditional logit, vehicle/heating domains, eligibility filtering, panel output extension, 10-year behavioral notebook.

### Epic 15 — Calibration (5 stories)

Stories 15.1–15.5: Calibration target format, CalibrationEngine, holdout validation, manifest integration, calibration workflow notebook.

### Epic 16 — Replication Packages (4 stories)

Stories 16.1–16.4: Package export, import/reproduction, provenance inclusion, replication workflow notebook.

### Epic 17 — No-Code GUI (8 stories)

Stories 17.1–17.8: Data fusion workbench, portfolio designer, simulation runner with persistence, comparison dashboard, behavioral decision viewer, year schedule editor, result persistence and cache-disk loading, code review/refactoring.

---

## Retrospectives

Located in `_bmad-output/implementation-artifacts/retrospectives/`:

| Retrospective | Epic | Date |
| ------------- | ---- | ---- |
| `epic-9-retro-20260302.md` | Epic 9 — OpenFisca Compatibility | 2026-03-02 |
| `epic-15-retro-20260307.md` | Epic 15 — Calibration | 2026-03-07 |
| `epic-16-retro-20260307.md` | Epic 16 — Replication Packages | 2026-03-07 |
| `epic-17-retro-20260308.md` | Epic 17 — No-Code GUI | 2026-03-08 |

Additional retrospective: `phase-1-retro-2026-02-28.md` (Phase 1 overall).

---

## Brainstorming Sessions

Located in `_bmad-output/brainstorming/`:

| Session | Date | Topic |
| ------- | ---- | ----- |
| `brainstorming-session-2026-02-23.md` | 2026-02-23 | Initial project ideation |
| `brainstorming-session-2026-02-25.md` | 2026-02-25 | OpenFisca pivot strategy |
| `brainstorming-session-2026-02-27.md` | 2026-02-27 | Phase 2 features |
| `brainstorming-session-2026-03-03-1300.md` | 2026-03-03 | Advanced features scoping |

---

## Other Artifacts

| Directory | Contents |
| --------- | -------- |
| `_bmad-output/branding/` | Brand identity and visual assets |
| `_bmad-output/communication/` | Communication deliverables |
| `_bmad-output/presentations/` | Presentation materials |
| `_bmad-output/website-content/` | Website copy and content |
| `_bmad-output/roadmap/` | Roadmap documents |
| `_bmad-output/test-artifacts/` | Test-related artifacts |

---

## Docs Directory

Located in `docs/` (generated by Document Project workflow):

| File | Purpose |
| ---- | ------- |
| `index.md` | Master documentation index |
| `project-overview.md` | Project summary and scale |
| `architecture.md` | System design and patterns |
| `source-tree-analysis.md` | Annotated directory structure |
| `development-guide.md` | Setup, commands, conventions |
| `deployment-guide.md` | Docker, Kamal, CI/CD |
| `planning-artifacts-inventory.md` | This document |
| `project-context.md` | AI project context rules |
| `prd.md` | Product requirements (copy) |
| `ux-design-specification.md` | UX specification (copy) |
| `epics.md` | Epic breakdown (copy) |
| `phase-1-exit-checklist.md` | Phase 1 exit criteria |
| `pilot-checklist.md` | Pilot run checklist |
| `compatibility.md` | OpenFisca compatibility notes |
