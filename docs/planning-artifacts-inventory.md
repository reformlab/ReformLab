# Planning Artifacts Inventory — ReformLab

**Generated:** 2026-02-28
**Status:** Phase 1 Complete (all planning + implementation artifacts present)

## Overview

ReformLab has a comprehensive set of planning and implementation artifacts organized across the `_bmad-output/` directory. This inventory covers all documents produced during the project lifecycle from initial brainstorming through Phase 1 completion.

## Core Product Documents

| Document | Path | Date | Purpose |
|----------|------|------|---------|
| Product Brief | `_bmad-output/planning-artifacts/product-brief-ReformLab-2026-02-23.md` | Feb 23 | Strategic direction and vision |
| PRD | `_bmad-output/planning-artifacts/prd.md` | Feb 23 | Full product requirements (35 FRs, 21 NFRs) |
| Architecture | `_bmad-output/planning-artifacts/architecture.md` | Feb 24 | Original architecture decisions |
| Architecture Diagrams | `_bmad-output/planning-artifacts/architecture-diagrams.md` | Feb 24 | Visual architecture representations |
| UX Design | `_bmad-output/planning-artifacts/ux-design-specification.md` | Feb 24 | Persona-driven UX design |

## Implementation Planning

| Document | Path | Date | Purpose |
|----------|------|------|---------|
| Phase 1 Backlog | `_bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md` | Feb 25 | 7 epics with prioritized stories |
| Implementation Readiness | `_bmad-output/planning-artifacts/implementation-readiness-report-2026-02-25.md` | Feb 25 | Readiness assessment |
| Sprint Change Proposal | `_bmad-output/planning-artifacts/sprint-change-proposal-2026-02-25.md` | Feb 25 | OpenFisca-first pivot rationale |
| Sprint Readiness | `_bmad-output/planning-artifacts/sprint-change-proposal-readiness-2026-02-25.md` | Feb 25 | Pivot readiness validation |

## Validation

| Document | Path | Date | Purpose |
|----------|------|------|---------|
| PRD Validation | `_bmad-output/planning-artifacts/prd-validation-report.md` | Feb 24 | PRD quality validation |
| General Validation | `_bmad-output/planning-artifacts/validation-report-2026-02-24.md` | Feb 24 | Cross-artifact validation |
| Stakeholder Review | `_bmad-output/planning-artifacts/stakeholder-review-brief-ReformLab-2026-02-24.md` | Feb 24 | Stakeholder feedback brief |

## Research

| Document | Path | Date | Topic |
|----------|------|------|-------|
| Domain Research | `_bmad-output/planning-artifacts/research/domain-generic-microsimulation-frameworks-research-2026-02-23.md` | Feb 23 | Microsimulation frameworks landscape |
| Technical Research | `_bmad-output/planning-artifacts/research/technical-entity-graph-data-modeling-and-vectorized-simulation-engines-research-2026-02-23.md` | Feb 23 | Entity graph and vectorized engines |
| French Open Data | `_bmad-output/planning-artifacts/research/domain-french-open-data-microsimulation-research-2026-02-25.md` | Feb 25 | French open-data sources |
| Market Research | `_bmad-output/planning-artifacts/research/market-microsimulation-platform-research-2026-02-25.md` | Feb 25 | Market landscape and positioning |
| French Models | `_bmad-output/planning-artifacts/research/market-french-microsimulation-models-research-2026-02-27.md` | Feb 27 | French microsimulation models |
| GovTech Funding | `_bmad-output/planning-artifacts/research/market-funding-and-credits-for-govtech-policy-tools-research-2026-02-28.md` | Feb 28 | Funding and credits for govtech |

## Implementation Artifacts (46 Story Files)

All story files are in `_bmad-output/implementation-artifacts/`. Sprint status tracked in `sprint-status.yaml`.

### EPIC-1: Computation Adapter and Data Layer (8 stories)

| Story | File | Status |
|-------|------|--------|
| 1-1 Define ComputationAdapter interface | `1-1-define-computationadapter-interface-and-openfiscaadapter-implementation.md` | Done |
| 1-2 Implement CSV/Parquet ingestion | `1-2-implement-csv-parquet-ingestion.md` | Done |
| 1-3 Build input-output mapping | `1-3-build-input-output-mapping-configuration.md` | Done |
| 1-4 Implement open-data ingestion | `1-4-implement-open-data-ingestion-pipeline.md` | Done |
| 1-5 Add data quality checks | `1-5-add-data-quality-checks.md` | Done |
| 1-6 Add OpenFisca API mode | `1-6-add-direct-openfisca-api-orchestration-mode.md` | Done |
| 1-7 Create compatibility matrix | `1-7-create-compatibility-matrix.md` | Done |
| 1-8 Set up project scaffold | `1-8-set-up-project-scaffold.md` | Done |

### EPIC-2: Scenario Templates and Registry (7 stories)

| Story | File | Status |
|-------|------|--------|
| 2-1 Define scenario template schema | `2-1-define-scenario-template-schema.md` | Done |
| 2-2 Implement carbon tax template | `2-2-implement-carbon-tax-template-pack.md` | Done |
| 2-3 Implement subsidy/rebate/feebate | `2-3-implement-subsidy-rebate-feebate-template-pack.md` | Done |
| 2-4 Build scenario registry | `2-4-build-scenario-registry.md` | Done |
| 2-5 Implement scenario cloning | `2-5-implement-scenario-cloning.md` | Done |
| 2-6 Add schema migration | `2-6-add-schema-migration-helper.md` | Done |
| 2-7 Implement YAML/JSON workflow | `2-7-implement-yaml-json-workflow-configuration.md` | Done |

### EPIC-3: Dynamic Orchestrator and Vintage Tracking (7 stories)

| Story | File | Status |
|-------|------|--------|
| 3-1 Implement yearly loop | `3-1-implement-yearly-loop-orchestrator.md` | Done |
| 3-2 Define orchestrator step interface | `3-2-define-orchestrator-step-interface.md` | Done |
| 3-3 Implement carry-forward step | `3-3-implement-carry-forward-step.md` | Done |
| 3-4 Implement vintage transition | `3-4-implement-vintage-transition-step.md` | Done |
| 3-5 Integrate ComputationAdapter | `3-5-integrate-computationadapter-calls.md` | Done |
| 3-6 Log seed controls | `3-6-log-seed-controls.md` | Done |
| 3-7 Produce panel output | `3-7-produce-scenario-year-panel-output.md` | Done |

### EPIC-4: Indicators and Scenario Comparison (6 stories)

| Story | File | Status |
|-------|------|--------|
| 4-1 Distributional indicators | `4-1-implement-distributional-indicators.md` | Done |
| 4-2 Geographic aggregation | `4-2-implement-geographic-aggregation-indicators.md` | Done |
| 4-3 Welfare indicators | `4-3-implement-welfare-indicators.md` | Done |
| 4-4 Fiscal indicators | `4-4-implement-fiscal-indicators.md` | Done |
| 4-5 Scenario comparison tables | `4-5-implement-scenario-comparison-tables.md` | Done |
| 4-6 Custom derived indicators | `4-6-implement-custom-derived-indicator-formulas.md` | Done |

### EPIC-5: Governance and Reproducibility (6 stories)

| Story | File | Status |
|-------|------|--------|
| 5-1 Define run manifest schema | `5-1-define-immutable-run-manifest-schema.md` | Done |
| 5-2 Capture assumptions/mappings | `5-2-capture-assumptions-mappings-parameters.md` | Done |
| 5-3 Implement run lineage graph | `5-3-implement-run-lineage-graph.md` | Done |
| 5-4 Hash input/output artifacts | `5-4-hash-input-output-artifacts.md` | Done |
| 5-5 Add reproducibility harness | `5-5-add-reproducibility-check-harness.md` | Done |
| 5-6 Add warning system | `5-6-add-warning-system-for-unvalidated-templates.md` | Done |

### EPIC-6: Interfaces (7 stories)

| Story | File | Status |
|-------|------|--------|
| 6-1 Implement stable Python API | `6-1-implement-stable-python-api.md` | Done |
| 6-2 Build quickstart notebook | `6-2-build-quickstart-notebook.md` | Done |
| 6-3 Build advanced notebook | `6-3-build-advanced-notebook.md` | Done |
| 6-4a Build static GUI prototype | `6-4a-build-static-gui-prototype.md` | Done |
| 6-4b Wire GUI to backend | `6-4b-wire-gui-prototype-to-backend.md` | Done |
| 6-5 Add export actions | `6-5-add-export-actions.md` | Done |
| 6-6 Improve operational error UX | `6-6-improve-operational-error-ux.md` | Done |

### EPIC-7: Quality Gates and Pilot Readiness (5 stories)

| Story | File | Status |
|-------|------|--------|
| 7-1 Verify against benchmarks | `7-1-verify-simulation-outputs-against-benchmarks.md` | Done |
| 7-2 Warn before memory limits | `7-2-warn-before-exceeding-memory-limits.md` | Done |
| 7-3 Enforce CI quality gates | `7-3-enforce-ci-quality-gates.md` | Done |
| 7-4 External pilot run | `7-4-external-pilot-run-carbon-tax-workflow.md` | Done |
| 7-5 Define Phase 1 exit checklist | `7-5-define-phase-1-exit-checklist.md` | Done |

## Communication and Outreach

| Document | Path | Date |
|----------|------|------|
| Audience Narratives | `_bmad-output/communication/audience-narratives-2026-02-25.md` | Feb 25 |
| Email Outreach (French) | `_bmad-output/communication/email-outreach-french-2026-02-25.md` | Feb 25 |
| Market One-Pager | `_bmad-output/communication/market-one-pager-2026-02-25.md` | Feb 25 |

## Branding

| Document | Path | Date |
|----------|------|------|
| Logo Prompt | `_bmad-output/branding/logo-prompt.md` | Feb 25 |
| Visual Identity | `_bmad-output/branding/visual-identity-guide.md` | Feb 25 |

## Presentations

| Document | Path | Date |
|----------|------|------|
| Pitch Deck Content | `_bmad-output/presentations/pitch-deck-content-2026-02-25.md` | Feb 25 |
| Presentation Design | `_bmad-output/presentations/presentation-design-prompt.md` | Feb 25 |

## Website Content

| Document | Path | Date |
|----------|------|------|
| Homepage Narrative | `_bmad-output/website-content/homepage-narrative-2026-02-25.md` | Feb 25 |
| Features | `_bmad-output/website-content/features-2026-02-25.md` | Feb 25 |
| How It Works | `_bmad-output/website-content/how-it-works-2026-02-25.md` | Feb 25 |
| Use Cases | `_bmad-output/website-content/use-cases-2026-02-25.md` | Feb 25 |
| FAQ | `_bmad-output/website-content/faq-2026-02-25.md` | Feb 25 |
| Copy Variations | `_bmad-output/website-content/copy-variations-2026-02-25.md` | Feb 25 |

## Roadmap

| Document | Path | Date |
|----------|------|------|
| Product Delivery Roadmap | `_bmad-output/roadmap/product-delivery-roadmap-2026-02-25.md` | Feb 25 |
| Go-to-Market Strategy | `_bmad-output/roadmap/go-to-market-and-ecosystem-strategy-2026-02-25.md` | Feb 25 |

## Brainstorming

| Document | Path | Date |
|----------|------|------|
| Initial Session | `_bmad-output/brainstorming/brainstorming-session-2026-02-23.md` | Feb 23 |
| Second Session | `_bmad-output/brainstorming/brainstorming-session-2026-02-25.md` | Feb 25 |
| Third Session | `_bmad-output/brainstorming/brainstorming-session-2026-02-27.md` | Feb 27 |

## Other

| Document | Path | Date |
|----------|------|------|
| Project Context | `_bmad-output/project-context.md` | Feb 27 |

## Summary

| Category | Count |
|----------|-------|
| Core product docs | 5 |
| Implementation planning | 4 |
| Validation reports | 3 |
| Research documents | 6 |
| Story files | 46 |
| Communication/outreach | 3 |
| Branding | 2 |
| Presentations | 2 |
| Website content | 6 |
| Roadmap | 2 |
| Brainstorming | 3 |
| **Total** | **82** |
