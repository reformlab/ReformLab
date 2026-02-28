# Source Tree Analysis — ReformLab

**Generated:** 2026-02-28
**Status:** Phase 1 Complete (fully implemented)

## Project Structure

```
reformlab/
├── src/reformlab/                    # Python package root (72 modules)
│   ├── __init__.py                   # Public API exports (run_scenario, etc.)
│   ├── computation/                  # EPIC-1: Adapter layer (11 modules)
│   │   ├── __init__.py
│   │   ├── adapter.py                # ComputationAdapter protocol (runtime_checkable)
│   │   ├── openfisca_adapter.py      # Pre-computed CSV/Parquet backend
│   │   ├── openfisca_api_adapter.py  # Live OpenFisca Python API backend
│   │   ├── openfisca_common.py       # Shared version detection utilities
│   │   ├── mock_adapter.py           # Deterministic test backend
│   │   ├── compat_matrix.py          # Version compatibility governance
│   │   ├── ingestion.py              # CSV/Parquet loading + schema validation
│   │   ├── mapping.py                # OpenFisca ↔ project field translation
│   │   ├── quality.py                # Output validation (range, null, type checks)
│   │   ├── types.py                  # PopulationData, PolicyConfig, ComputationResult
│   │   └── exceptions.py             # CompatibilityError, ApiMappingError
│   ├── data/                         # EPIC-1: Data layer (3 modules)
│   │   ├── __init__.py
│   │   ├── schemas.py                # SYNTHETIC_POPULATION_SCHEMA, EMISSION_FACTOR_SCHEMA
│   │   ├── emission_factors.py       # EmissionFactorIndex (category/year lookup)
│   │   └── pipeline.py               # DatasetRegistry, load_dataset, hash_file
│   ├── templates/                    # EPIC-2: Scenario templates (14 modules)
│   │   ├── __init__.py               # Re-exports for template loading
│   │   ├── schema.py                 # PolicyType enum, YearSchedule, parameter classes
│   │   ├── loader.py                 # YAML load/dump with validation
│   │   ├── registry.py               # Content-addressable scenario versioning
│   │   ├── reform.py                 # Reform-as-delta resolution
│   │   ├── migration.py              # Schema version compatibility + migration
│   │   ├── workflow.py               # WorkflowConfig, YAML/JSON orchestration
│   │   ├── exceptions.py             # ScenarioError
│   │   ├── carbon_tax/               # Carbon tax template pack
│   │   │   ├── __init__.py
│   │   │   └── compute.py            # Tax burden, redistribution computation
│   │   │   └── compare.py            # Baseline vs reform comparison
│   │   ├── subsidy/                  # Subsidy template pack
│   │   │   ├── __init__.py
│   │   │   └── compute.py, compare.py
│   │   ├── rebate/                   # Rebate template pack
│   │   │   ├── __init__.py
│   │   │   └── compute.py, compare.py
│   │   ├── feebate/                  # Feebate template pack
│   │   │   ├── __init__.py
│   │   │   └── compute.py, compare.py
│   │   └── packs/                    # Pack discovery and loading
│   │       └── __init__.py
│   ├── orchestrator/                 # EPIC-3: Dynamic orchestrator (7 modules)
│   │   ├── __init__.py
│   │   ├── runner.py                 # Orchestrator class, OrchestratorRunner
│   │   ├── step.py                   # OrchestratorStep protocol, StepRegistry, @step
│   │   ├── types.py                  # YearState, OrchestratorConfig, OrchestratorResult
│   │   ├── carry_forward.py          # CarryForwardStep (state propagation)
│   │   ├── computation_step.py       # ComputationStep (adapter invocation)
│   │   ├── panel.py                  # PanelOutput (household-by-year dataset)
│   │   └── errors.py                 # OrchestratorError
│   ├── vintage/                      # EPIC-3: Vintage tracking (4 modules)
│   │   ├── __init__.py
│   │   ├── types.py                  # VintageCohort, VintageState, VintageSummary
│   │   ├── config.py                 # VintageTransitionRule, VintageConfig
│   │   ├── transition.py             # VintageTransitionStep
│   │   └── errors.py                 # VintageConfigError, VintageTransitionError
│   ├── indicators/                   # EPIC-4: Indicator engine (8 modules)
│   │   ├── __init__.py
│   │   ├── distributional.py         # Decile-based distributional indicators
│   │   ├── geographic.py             # Region-based aggregation
│   │   ├── welfare.py                # Winner/loser analysis
│   │   ├── fiscal.py                 # Revenue/cost/balance tracking
│   │   ├── comparison.py             # Multi-scenario comparison
│   │   ├── custom.py                 # Custom derived formula indicators
│   │   ├── deciles.py                # Decile assignment utilities
│   │   └── types.py                  # IndicatorResult, config classes
│   ├── governance/                   # EPIC-5: Governance layer (8 modules)
│   │   ├── __init__.py
│   │   ├── manifest.py               # RunManifest (immutable, integrity-hashed)
│   │   ├── hashing.py                # SHA-256 artifact hashing (streaming)
│   │   ├── lineage.py                # LineageGraph, run lineage tracking
│   │   ├── reproducibility.py        # Re-execute + verify check
│   │   ├── capture.py                # Assumption/parameter/mapping capture
│   │   ├── benchmarking.py           # BenchmarkSuiteResult, benchmark runner
│   │   ├── memory.py                 # Memory estimation, system memory check
│   │   └── errors.py                 # ManifestIntegrityError, etc.
│   └── interfaces/                   # EPIC-6: User-facing API (3 modules)
│       ├── __init__.py
│       ├── api.py                    # run_scenario, create_scenario, SimulationResult
│       └── errors.py                 # ConfigurationError, SimulationError, MemoryWarning
│
├── tests/                            # Test suite (93 files, 1374 tests)
│   ├── computation/                  # Adapter tests (17 files, 242 tests)
│   ├── data/                         # Data layer tests (3 files, 39 tests)
│   ├── templates/                    # Template tests (11+ files, 365 tests)
│   │   ├── carbon_tax/               # Carbon tax sub-tests (5 files)
│   │   ├── subsidy/                  # Subsidy sub-tests
│   │   ├── rebate/                   # Rebate sub-tests
│   │   └── feebate/                  # Feebate sub-tests
│   ├── orchestrator/                 # Orchestrator tests (9 files, 197 tests)
│   ├── vintage/                      # Vintage tests (4 files, 72 tests)
│   ├── indicators/                   # Indicator tests (6 files, 136 tests)
│   ├── governance/                   # Governance tests (6 files, 168 tests)
│   ├── interfaces/                   # Interface tests (2 files, 63 tests)
│   ├── benchmarks/                   # Performance tests (1 file, 7 tests)
│   ├── notebooks/                    # Notebook validation (2 files, 14 tests)
│   ├── docs/                         # Doc contract tests (2 files, 7 tests)
│   ├── test_scaffold.py              # Project structure validation (3 tests)
│   └── test_ci_quality_gates.py      # CI config validation (3 tests)
│
├── frontend/                         # React No-Code GUI (46 source files)
│   ├── src/
│   │   ├── main.tsx                  # React 19 entry point
│   │   ├── App.tsx                   # Root state manager (11 state vars)
│   │   ├── index.css                 # Tailwind CSS entry
│   │   ├── components/
│   │   │   ├── layout/               # 3-column resizable workspace
│   │   │   │   ├── WorkspaceLayout.tsx   # ResizablePanel container
│   │   │   │   ├── LeftPanel.tsx         # Collapsible scenario sidebar
│   │   │   │   ├── MainContent.tsx       # Central scrollable area
│   │   │   │   └── RightPanel.tsx        # Collapsible context sidebar
│   │   │   ├── simulation/           # Simulation workflow components
│   │   │   │   ├── ModelConfigStepper.tsx # 4-step progress indicator
│   │   │   │   ├── ParameterRow.tsx      # Slider + input parameter editor
│   │   │   │   ├── ScenarioCard.tsx      # Scenario item with actions
│   │   │   │   ├── RunProgressBar.tsx    # Progress bar with ETA
│   │   │   │   ├── DistributionalChart.tsx # Recharts bar chart
│   │   │   │   ├── SummaryStatCard.tsx   # KPI indicator card
│   │   │   │   ├── ComparisonView.tsx    # Multi-scenario comparison
│   │   │   │   ├── ParametersStep.tsx    # Alt parameter group view
│   │   │   │   ├── PopulationStep.tsx    # Alt population selection
│   │   │   │   ├── ReviewStep.tsx        # Alt review view
│   │   │   │   └── TemplateStep.tsx      # Alt template selection
│   │   │   ├── screens/              # Step-specific full views
│   │   │   │   ├── PopulationSelectionScreen.tsx
│   │   │   │   ├── TemplateSelectionScreen.tsx
│   │   │   │   ├── ParameterEditingScreen.tsx
│   │   │   │   └── AssumptionsReviewScreen.tsx
│   │   │   └── ui/                   # 20 UI primitives (shadcn-inspired)
│   │   │       ├── button.tsx, card.tsx, badge.tsx, input.tsx
│   │   │       ├── table.tsx, tabs.tsx, slider.tsx, select.tsx
│   │   │       ├── collapsible.tsx, resizable.tsx, separator.tsx
│   │   │       ├── dialog.tsx, popover.tsx, tooltip.tsx
│   │   │       ├── sheet.tsx, scroll-area.tsx, switch.tsx
│   │   │       └── sonner.tsx
│   │   ├── data/
│   │   │   └── mock-data.ts          # Mock populations, templates, scenarios
│   │   ├── lib/
│   │   │   └── utils.ts              # cn() class merge utility
│   │   ├── test/
│   │   │   └── setup.ts              # Vitest/testing-library setup
│   │   └── __tests__/                # Component tests
│   ├── index.html                    # SPA entry point
│   ├── package.json                  # React 19, Vite 7, Tailwind 4
│   ├── vite.config.ts                # Build + test config
│   ├── tsconfig.json                 # TypeScript config
│   └── eslint.config.js              # ESLint config
│
├── notebooks/                        # Jupyter notebooks
│   ├── quickstart.ipynb              # User-facing quickstart tutorial
│   ├── advanced.ipynb                # Advanced multi-year scenarios
│   └── demo/                         # Per-epic demo notebooks
│       ├── epic1_demo.ipynb
│       ├── epic2_demo.ipynb
│       ├── epic3_demo.ipynb
│       ├── epic4_demo.ipynb
│       └── epic5_demo.ipynb
│
├── examples/                         # Workflow configuration examples
│   └── workflows/
│       ├── carbon_tax_analysis.yaml  # Single scenario analysis
│       ├── scenario_comparison.yaml  # Baseline vs reform comparison
│       ├── batch_sensitivity.json    # Multi-scenario batch analysis
│       └── README.md                 # Workflow documentation
│
├── config/
│   └── deploy.yml                    # Kamal 2 deployment configuration
│
├── .github/workflows/
│   ├── ci.yml                        # CI pipeline (lint, type-check, test, notebooks)
│   └── deploy.yml                    # Deploy pipeline (Kamal to Hetzner)
│
├── docs/                             # Generated project documentation
│   ├── index.md                      # Master documentation index
│   ├── project-overview.md           # Executive summary
│   ├── architecture.md               # Architecture deep-dive
│   ├── source-tree-analysis.md       # This file
│   ├── development-guide.md          # Setup and conventions
│   ├── deployment-guide.md           # Docker + Kamal deployment
│   ├── compatibility.md              # OpenFisca version matrix
│   ├── planning-artifacts-inventory.md
│   ├── pilot-checklist.md            # Pilot bundle checklist
│   ├── phase-1-exit-checklist.md     # Phase 1 exit criteria
│   └── project-scan-report.json      # Workflow state
│
├── dist/                             # Built Python package
│   ├── reformlab-0.1.0.tar.gz
│   └── reformlab-0.1.0-py3-none-any.whl
│
├── _bmad-output/                     # BMAD workflow outputs
│   ├── planning-artifacts/           # 18 planning documents
│   │   ├── prd.md, architecture.md, ux-design-specification.md
│   │   ├── phase-1-implementation-backlog-2026-02-25.md
│   │   └── research/                 # 5 research documents
│   ├── implementation-artifacts/     # 46 story files + sprint-status.yaml
│   ├── brainstorming/                # 3 brainstorming sessions
│   ├── branding/                     # Logo and visual identity
│   ├── communication/                # Outreach and narrative assets
│   ├── presentations/                # Pitch deck content
│   ├── roadmap/                      # Delivery roadmap, GTM strategy
│   └── website-content/              # Homepage, features, FAQ, use cases
│
├── pyproject.toml                    # Python package config (hatchling)
├── uv.lock                          # Locked dependencies
├── Dockerfile                       # Python 3.13-slim container
├── README.md                        # Project readme
├── CLAUDE.md                        # AI assistant instructions
├── LICENSE                           # Apache-2.0
└── .gitignore                        # Git exclusion rules
```

## Critical Folders Summary

| Folder | Purpose | Files | Status |
|--------|---------|-------|--------|
| `src/reformlab/computation/` | Adapter layer, ingestion, mapping, quality | 11 | Complete |
| `src/reformlab/data/` | Data schemas, emission factors, pipeline | 3 | Complete |
| `src/reformlab/templates/` | Scenario templates, registry, workflow config | 14 | Complete |
| `src/reformlab/orchestrator/` | Dynamic yearly loop, step pipeline | 7 | Complete |
| `src/reformlab/vintage/` | Cohort-based asset tracking | 4 | Complete |
| `src/reformlab/indicators/` | Distributional, fiscal, welfare indicators | 8 | Complete |
| `src/reformlab/governance/` | Manifests, hashing, lineage, reproducibility | 8 | Complete |
| `src/reformlab/interfaces/` | Python API surface | 3 | Complete |
| `frontend/src/` | React no-code GUI | 46 | Complete |
| `tests/` | Full test suite | 93 | 1374 tests |
| `notebooks/` | Jupyter tutorials and demos | 7 | Complete |

## Entry Points

| Entry Point | Path | Purpose |
|-------------|------|---------|
| Python API | `src/reformlab/__init__.py` | `run_scenario()`, `create_scenario()`, etc. |
| Interfaces module | `src/reformlab/interfaces/api.py` | Full API with SimulationResult |
| Frontend | `frontend/src/main.tsx` | React SPA entry |
| Docker | `Dockerfile` | `uvicorn src.reformlab.api:app` |
| CI | `.github/workflows/ci.yml` | Lint → type-check → test → notebooks |
| Deploy | `.github/workflows/deploy.yml` | Kamal deploy on push to master |
