# Source Tree Analysis — ReformLab

**Generated:** 2026-02-25
**Status:** Pre-implementation (no source code yet)

## Current Project Structure

```
reformlab/
├── .agents/                    # Agent skill configurations (BMAD)
│   └── skills/                 # Skill definitions for various BMAD agents
├── .claude/                    # Claude Code configuration
│   ├── commands/               # BMAD slash commands
│   └── settings.local.json     # Local Claude settings
├── _bmad/                      # BMAD framework installation
│   ├── _config/                # Agent customization configs
│   ├── _memory/                # Agent persistent memory
│   ├── bmb/                    # BMAD Module Builder workflows
│   ├── bmm/                    # BMAD Module Manager (project workflows)
│   │   ├── config.yaml         # Project configuration
│   │   └── workflows/          # All project management workflows
│   ├── cis/                    # Creative Innovation Suite
│   ├── core/                   # BMAD core engine
│   └── tea/                    # Test Engineering Architect module
├── _bmad-output/               # BMAD workflow outputs
│   ├── brainstorming/          # Brainstorming session records
│   │   └── brainstorming-session-2026-02-23.md
│   ├── bmb-creations/          # (empty) Module builder outputs
│   ├── implementation-artifacts/ # (empty) Implementation outputs
│   ├── planning-artifacts/     # Project planning documents
│   │   ├── architecture.md     # Architecture decision document
│   │   ├── implementation-readiness-report-2026-02-25.md
│   │   ├── phase-1-implementation-backlog-2026-02-25.md
│   │   ├── prd-validation-report.md
│   │   ├── prd.md              # Product requirements document
│   │   ├── product-brief-ReformLab-2026-02-23.md
│   │   ├── research/           # Research documents
│   │   │   ├── domain-generic-microsimulation-frameworks-research-2026-02-23.md
│   │   │   └── technical-entity-graph-data-modeling-and-vectorized-simulation-engines-research-2026-02-23.md
│   │   ├── sprint-change-proposal-2026-02-25.md
│   │   ├── stakeholder-review-brief-ReformLab-2026-02-24.md
│   │   ├── ux-design-specification.md
│   │   └── validation-report-2026-02-24.md
│   └── test-artifacts/         # (empty) Test outputs
└── docs/                       # Generated project documentation (this folder)
    ├── index.md                # Master documentation index
    ├── project-overview.md     # Project overview
    ├── architecture.md         # Architecture summary
    ├── source-tree-analysis.md # This file
    ├── development-guide.md    # Development setup guide
    └── project-scan-report.json # Workflow state file
```

## Planned Source Structure (from Architecture Document)

When implementation begins, the following source structure is planned:

```
src/reformlab/                  # Python package root
├── computation/                # Adapter interface + OpenFiscaAdapter
│   ├── __init__.py
│   ├── adapter.py              # ComputationAdapter protocol
│   ├── openfisca_adapter.py    # OpenFisca implementation
│   └── contracts/              # Data contract definitions
├── data/                       # Open data ingestion and preparation
│   ├── __init__.py
│   ├── ingestion.py            # Data loading pipelines
│   ├── synthetic_population.py # Synthetic population generation
│   └── transformers/           # Data transformation modules
├── templates/                  # Environmental policy templates
│   ├── __init__.py
│   ├── carbon_tax.py           # Carbon tax template pack
│   ├── subsidies.py            # Subsidy/rebate/feebate templates
│   └── registry.py             # Scenario registry with versioning
├── orchestrator/               # Dynamic yearly loop engine
│   ├── __init__.py
│   ├── engine.py               # Year-loop orchestrator
│   ├── steps.py                # Step interface and registration
│   └── pipeline.py             # Step pipeline management
├── vintage/                    # Vintage/cohort state management
│   ├── __init__.py
│   ├── transitions.py          # Asset cohort aging logic
│   └── carry_forward.py        # State carry-forward between years
├── indicators/                 # Indicator computation
│   ├── __init__.py
│   ├── distributional.py       # Distributional analysis
│   ├── welfare.py              # Welfare indicators
│   ├── fiscal.py               # Fiscal impact indicators
│   └── custom.py               # Custom metric framework
├── governance/                 # Run governance and reproducibility
│   ├── __init__.py
│   ├── manifests.py            # Run manifest generation
│   ├── assumptions.py          # Assumption logging
│   └── lineage.py              # Run lineage tracking
├── interfaces/                 # User-facing interfaces
│   ├── __init__.py
│   ├── api.py                  # Python API surface
│   ├── notebooks/              # Jupyter notebook templates
│   └── gui/                    # No-code GUI (early)
├── pyproject.toml              # Package configuration
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   ├── contract/               # Adapter contract tests
│   └── integration/            # Integration tests
└── data/                       # Sample/test data files
    ├── synthetic/              # Synthetic population samples
    └── fixtures/               # Test fixtures
```

## Critical Folders Summary

| Folder | Purpose | Status |
|--------|---------|--------|
| `_bmad-output/planning-artifacts/` | All project planning documents (PRD, architecture, backlog) | Complete |
| `_bmad-output/planning-artifacts/research/` | Domain and technical research | Complete |
| `_bmad-output/brainstorming/` | Initial brainstorming sessions | Complete |
| `docs/` | Generated project documentation | In progress |
| `_bmad/bmm/config.yaml` | BMAD project configuration | Active |

## Entry Points (Planned)

Since no source code exists yet, the primary entry points will be:
- `src/reformlab/__init__.py` — Package entry point
- `src/reformlab/orchestrator/engine.py` — Core orchestration engine
- `src/reformlab/interfaces/api.py` — Python API surface
- Jupyter notebooks in `src/reformlab/interfaces/notebooks/`
