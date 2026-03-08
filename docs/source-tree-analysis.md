# Source Tree Analysis — ReformLab

**Generated:** 2026-03-08
**Status:** Phase 2 Complete (Epics 1–17 implemented)

## How to Read This Document

This annotated source tree shows every directory and its purpose. Think of it as a map: the top-level directories are neighborhoods, and each subsystem is a building with a specific responsibility. Arrows (→) indicate key integration points between parts.

---

## Project Root

```text
reformlab/
├── src/reformlab/           # Python package — all domain logic lives here
├── frontend/src/            # React 19 SPA — no-code GUI
├── tests/                   # Python test suite (3,143 tests)
├── notebooks/               # Jupyter guides and demos
├── examples/                # API, population, and workflow examples
├── config/                  # Deployment configuration (Kamal)
├── scripts/                 # Utility scripts
├── data/                    # Data files (populations, emission factors)
├── docs/                    # Generated project documentation (you are here)
├── _bmad/                   # BMAD framework (do not edit)
├── _bmad-output/            # Planning and implementation artifacts
├── .github/workflows/       # CI/CD pipelines
├── Dockerfile               # Backend container
├── pyproject.toml           # Python project manifest
└── README.md                # Project introduction
```

---

## Python Backend: `src/reformlab/`

The backend follows a **layered architecture**. Each subsystem is a Python package with its own `__init__.py` that exports the public API. Dependencies flow downward — upper layers depend on lower layers, never the reverse.

```text
src/reformlab/
│
├── interfaces/              # Layer 7: Stable Python API facade
│   ├── api.py               #   run_scenario(), create_scenario(), run_benchmarks()
│   └── errors.py            #   ConfigurationError, SimulationError, MemoryWarning
│
├── server/                  # Layer 6: FastAPI HTTP facade → wraps interfaces/
│   ├── app.py               #   FastAPI app factory, CORS, router mounting
│   ├── auth.py              #   Shared-password authentication middleware
│   ├── dependencies.py      #   Dependency injection (ResultCache, ResultStore, Adapter)
│   ├── models.py            #   Pydantic v2 request/response models
│   ├── result_store.py      #   ResultCache (LRU) + ResultStore (disk persistence)
│   └── routes/              #   10 route modules:
│       ├── runs.py          #     POST /api/runs — execute simulation
│       ├── indicators.py    #     POST /api/indicators/{type} — compute indicators
│       ├── scenarios.py     #     GET/POST /api/scenarios — CRUD
│       ├── templates.py     #     GET /api/templates — list/get templates
│       ├── portfolios.py    #     GET/POST/PUT /api/portfolios — portfolio CRUD
│       ├── data_fusion.py   #     GET/POST /api/data-fusion — population generation
│       ├── results.py       #     GET /api/results — list saved results
│       ├── exports.py       #     POST /api/exports — CSV export
│       ├── decisions.py     #     GET /api/decisions — decision audit trail
│       └── populations.py   #     GET /api/populations — list populations
│
├── orchestrator/            # Layer 5: Multi-year yearly-loop engine
│   ├── runner.py            #   Orchestrator class — runs year-by-year projection
│   ├── step.py              #   OrchestratorStep protocol, @step decorator, StepRegistry
│   ├── types.py             #   YearState, OrchestratorConfig, OrchestratorResult
│   ├── panel.py             #   PanelOutput — household×year panel dataset
│   ├── computation_step.py  #   ComputationStep — invokes adapter each year
│   ├── portfolio_step.py    #   PortfolioComputationStep — multi-policy execution
│   ├── carry_forward.py     #   CarryForwardStep — deterministic state carry
│   └── errors.py            #   OrchestratorError, StepValidationError
│
├── discrete_choice/         # Layer 4: Behavioral modeling (conditional logit)
│   ├── step.py              #   DiscreteChoiceStep — pipeline integration
│   ├── expansion.py         #   Population expansion (N → N×M rows)
│   ├── reshape.py           #   Cost matrix reshape
│   ├── logit.py             #   LogitChoiceStep — seed-controlled draws
│   ├── domain.py            #   DecisionDomain base + domain registry
│   ├── vehicle.py           #   VehicleInvestmentDomain + state updates
│   ├── heating.py           #   HeatingInvestmentDomain + state updates
│   ├── eligibility.py       #   EligibilityFilter — performance optimization
│   ├── decision_record.py   #   DecisionRecord audit trail
│   ├── types.py             #   Alternative, ChoiceSet, CostMatrix, TasteParameters
│   └── errors.py            #   DiscreteChoiceError hierarchy
│
├── calibration/             # Layer 4: Parameter calibration against observed data
│   ├── engine.py            #   CalibrationEngine — scipy optimization
│   ├── types.py             #   CalibrationTarget, CalibrationResult, FitMetrics
│   ├── loader.py            #   Load calibration targets from JSON schema
│   ├── validation.py        #   Holdout validation (train/test split)
│   ├── provenance.py        #   Governance integration for calibrated params
│   ├── schema/              #   JSON schemas for calibration target format
│   └── errors.py            #   CalibrationError hierarchy
│
├── templates/               # Layer 3: Policy scenario definitions
│   ├── schema.py            #   PolicyType enum, PolicyParameters, ScenarioTemplate
│   ├── loader.py            #   YAML load/dump for scenario templates
│   ├── registry.py          #   ScenarioRegistry — immutable versioning
│   ├── reform.py            #   Reform-as-delta resolution logic
│   ├── migration.py         #   Schema version migration
│   ├── workflow.py          #   WorkflowConfig — YAML-driven run definitions
│   ├── exceptions.py        #   TemplateError, ScenarioError
│   ├── portfolios/          #   Multi-policy portfolio composition
│   │   ├── portfolio.py     #     PolicyPortfolio, PolicyConfig
│   │   ├── composition.py   #     Conflict detection and resolution
│   │   ├── enums.py         #     ConflictType, ResolutionStrategy
│   │   └── exceptions.py    #     PortfolioError, PortfolioValidationError
│   ├── packs/               #   Template pack loaders (list/load per type)
│   ├── carbon_tax/          #   CarbonTaxParameters + compute/compare
│   ├── subsidy/             #   SubsidyParameters + compute/compare
│   ├── rebate/              #   RebateParameters + compute/compare
│   ├── feebate/             #   FeebateParameters + compute/compare
│   ├── vehicle_malus/       #   Custom template: vehicle malus
│   └── energy_poverty_aid/  #   Custom template: energy poverty aid
│
├── indicators/              # Layer 3: Post-simulation analytics
│   ├── distributional.py    #   Decile-based indicators
│   ├── geographic.py        #   Region-based indicators
│   ├── welfare.py           #   Winner/loser analysis
│   ├── fiscal.py            #   Revenue, cost, balance
│   ├── comparison.py        #   Baseline vs reform comparison
│   ├── portfolio_comparison.py  # Multi-portfolio cross-comparison
│   ├── custom.py            #   User-defined formula indicators
│   ├── types.py             #   DecileIndicators, IndicatorResult, configs
│   └── deciles.py           #   Decile computation utilities
│
├── governance/              # Cross-cutting: Reproducibility and auditability
│   ├── manifest.py          #   RunManifest — immutable run record
│   ├── capture.py           #   Assumption, mapping, policy capture
│   ├── hashing.py           #   SHA-256 artifact integrity
│   ├── lineage.py           #   Run lineage graph (parent/child)
│   ├── reproducibility.py   #   Reproducibility verification
│   ├── benchmarking.py      #   Benchmark validation suite
│   ├── memory.py            #   Memory estimation and preflight checks
│   ├── replication.py       #   Replication package export/import
│   └── errors.py            #   ManifestIntegrityError, etc.
│
├── population/              # Layer 2: Realistic population generation
│   ├── pipeline.py          #   PopulationPipeline — composable builder
│   ├── validation.py        #   PopulationValidator — marginal checks
│   ├── assumptions.py       #   Assumption chain recording
│   ├── loaders/             #   Institutional data source loaders
│   │   ├── base.py          #     CachedLoader base, DataSourceLoader protocol
│   │   ├── cache.py         #     SourceCache — disk-based caching
│   │   ├── insee.py         #     INSEELoader — French national statistics
│   │   ├── eurostat.py      #     EurostatLoader — EU statistics
│   │   ├── ademe.py         #     ADEMELoader — energy/environment agency
│   │   ├── sdes.py          #     SDESLoader — transport statistics
│   │   └── errors.py        #     DataSourceError hierarchy
│   └── methods/             #   Statistical fusion methods
│       ├── base.py          #     MergeMethod protocol
│       ├── uniform.py       #     UniformMergeMethod — random matching
│       ├── ipf.py           #     IPFMergeMethod — iterative proportional fitting
│       ├── conditional.py   #     ConditionalSamplingMethod — stratum-based
│       └── errors.py        #     MergeError hierarchy
│
├── computation/             # Layer 1: Tax-benefit backend adapter
│   ├── adapter.py           #   ComputationAdapter protocol (core interface)
│   ├── types.py             #   PopulationData, PolicyConfig, ComputationResult
│   ├── ingestion.py         #   CSV/Parquet data ingestion
│   ├── mapping.py           #   Variable mapping (OpenFisca ↔ project)
│   ├── quality.py           #   Data quality checks
│   ├── openfisca_adapter.py #   OpenFiscaAdapter — file-based implementation
│   ├── openfisca_api_adapter.py  # OpenFiscaApiAdapter — API-based
│   ├── openfisca_common.py  #   Shared OpenFisca utilities
│   ├── mock_adapter.py      #   MockAdapter — for testing
│   ├── compat_matrix.py     #   Version compatibility matrix
│   └── exceptions.py        #   ComputationError hierarchy
│
├── data/                    # Layer 1: Data access and synthetic generation
│   ├── schemas.py           #   CSV/Parquet schema contracts
│   ├── emission_factors.py  #   EmissionFactorIndex — lookup service
│   ├── synthetic.py         #   Synthetic population generator
│   └── pipeline.py          #   DatasetManifest, DatasetRegistry
│
├── vintage/                 # Layer 2: Asset cohort tracking
│   ├── types.py             #   VintageCohort, VintageState, VintageSummary
│   ├── config.py            #   VintageConfig, VintageTransitionRule
│   ├── transition.py        #   VintageTransitionStep — orchestrator integration
│   └── errors.py            #   VintageConfigError, VintageTransitionError
│
└── visualization/           # Utility: Plotting and display
    ├── display.py           #   show() — formatted PyArrow table display
    └── styling.py           #   Matplotlib figure creation and styling
```

**Key dependency flow:**

```text
interfaces → orchestrator → {computation, discrete_choice, vintage, templates}
                          → governance (cross-cutting)
server     → interfaces   → indicators → orchestrator.panel
population (independent)  → data
calibration              → discrete_choice + governance
```

---

## React Frontend: `frontend/src/`

The frontend is a **single-page application** with centralized state management. Components are organized by responsibility: layout (structure), screens (full views), simulation (domain building blocks), and ui (design system primitives).

```text
frontend/src/
│
├── main.tsx                 # Entry point — mounts <App /> in <AppProvider>
├── App.tsx                  # Root component — auth gate + workspace + view routing
├── index.css                # Tailwind v4 theme (colors, fonts, chart variables)
│
├── api/                     # Typed API client layer → maps to backend routes
│   ├── client.ts            #   apiFetch<T>() — generic fetch with auth + error handling
│   ├── types.ts             #   All TypeScript interfaces (413 lines)
│   ├── auth.ts              #   login() → POST /api/auth/login
│   ├── runs.ts              #   runScenario(), checkMemory()
│   ├── templates.ts         #   listTemplates(), getTemplate()
│   ├── populations.ts       #   listPopulations()
│   ├── scenarios.ts         #   createScenario(), cloneScenario()
│   ├── indicators.ts        #   getIndicators(), compareScenarios(), comparePortfolios()
│   ├── data-fusion.ts       #   listDataSources(), generatePopulation()
│   ├── portfolios.ts        #   CRUD + validatePortfolio()
│   ├── results.ts           #   listResults(), exportResultCsv()
│   ├── decisions.ts         #   getDecisionSummary()
│   └── exports.ts           #   exportCsv(), exportParquet()
│
├── contexts/                # Global state management
│   └── AppContext.tsx        #   Single context: auth, data, selections, runs (476 lines)
│
├── hooks/                   # Custom data-fetching hooks
│   └── useApi.ts            #   usePopulations, useTemplates, useResults, etc. (437 lines)
│
├── components/
│   ├── auth/
│   │   └── PasswordPrompt.tsx       # Shared-password login modal
│   │
│   ├── layout/                      # Workspace structure
│   │   ├── WorkspaceLayout.tsx      #   3-panel resizable layout
│   │   ├── LeftPanel.tsx            #   Scenario sidebar (collapsible)
│   │   ├── MainContent.tsx          #   Main content wrapper
│   │   └── RightPanel.tsx           #   Context sidebar
│   │
│   ├── screens/                     # Full-page views (9 screens)
│   │   ├── PopulationSelectionScreen.tsx   # Step 1: Pick population
│   │   ├── TemplateSelectionScreen.tsx     # Step 2: Pick policy template
│   │   ├── ParameterEditingScreen.tsx      # Step 3: Tune parameters
│   │   ├── AssumptionsReviewScreen.tsx     # Step 4: Review before run
│   │   ├── SimulationRunnerScreen.tsx      # Batch run orchestration
│   │   ├── DataFusionWorkbench.tsx         # 5-step population generation
│   │   ├── PortfolioDesignerScreen.tsx     # Portfolio CRUD + composition
│   │   ├── ComparisonDashboardScreen.tsx   # Multi-run comparison + export
│   │   └── BehavioralDecisionViewerScreen.tsx  # Decision audit viewer
│   │
│   ├── simulation/                  # Domain components (29 components)
│   │   ├── ModelConfigStepper.tsx    #   4-step progress indicator
│   │   ├── DistributionalChart.tsx   #   2-series bar chart (Recharts)
│   │   ├── MultiRunChart.tsx         #   2–5 series grouped bars
│   │   ├── TransitionChart.tsx       #   Year-over-year transitions
│   │   ├── PopulationDistributionChart.tsx  # Demographics chart
│   │   ├── DataSourceBrowser.tsx     #   Searchable source picker
│   │   ├── VariableOverlapView.tsx   #   Variable presence matrix
│   │   ├── MergeMethodSelector.tsx   #   Merge method picker
│   │   ├── MergeParametersPanel.tsx  #   Method parameter config
│   │   ├── PopulationGenerationProgress.tsx # Real-time step log
│   │   ├── PopulationValidationPanel.tsx   # Marginal constraint results
│   │   ├── PortfolioTemplateBrowser.tsx    # Policy template picker
│   │   ├── PortfolioCompositionPanel.tsx   # Portfolio policies + conflicts
│   │   ├── ResultsListPanel.tsx      #   Paginated result list
│   │   ├── ResultDetailView.tsx      #   Full result metadata
│   │   ├── CrossMetricPanel.tsx      #   Cross-portfolio ranking
│   │   ├── ScenarioCard.tsx          #   Scenario selector card
│   │   ├── SummaryStatCard.tsx       #   KPI metric card
│   │   ├── RunProgressBar.tsx        #   Progress bar with ETA
│   │   ├── YearDetailPanel.tsx       #   Year-level decision breakdown
│   │   ├── YearScheduleEditor.tsx    #   Year range editor
│   │   ├── PopulationPreview.tsx     #   Population data preview
│   │   ├── ComparisonView.tsx        #   Comparison result view
│   │   ├── ParameterRow.tsx          #   Single parameter editor
│   │   ├── ParametersStep.tsx        #   Parameter editing substep
│   │   ├── PopulationStep.tsx        #   Population selection substep
│   │   ├── ReviewStep.tsx            #   Review substep
│   │   └── TemplateStep.tsx          #   Template selection substep
│   │
│   └── ui/                          # Shadcn/Radix design system (18 primitives)
│       ├── badge.tsx, button.tsx, card.tsx, input.tsx
│       ├── dialog.tsx, popover.tsx, select.tsx, collapsible.tsx
│       ├── tabs.tsx, slider.tsx, switch.tsx, table.tsx
│       ├── scroll-area.tsx, sheet.tsx, resizable.tsx
│       ├── separator.tsx, tooltip.tsx, sonner.tsx
│       └── (each wraps Radix headless + Tailwind styling)
│
├── data/
│   └── mock-data.ts         # Fallback mock data for offline development
│
├── lib/
│   └── utils.ts             # cn() — Tailwind class merge utility
│
└── test/
    └── setup.ts             # Vitest setup — jest-dom matchers
```

**View modes in App.tsx:** configuration → run → progress → results → comparison → decisions → data-fusion → portfolio → runner

---

## Test Suite: `tests/`

Tests mirror the `src/` structure. Each subsystem has its own test directory with focused unit tests plus integration tests where subsystems interact.

```text
tests/                           # 190 files, 3,143 tests
├── computation/                 #   Adapter, ingestion, mapping, quality tests
├── data/                        #   Emission factors, synthetic population
├── templates/                   #   Schema, loader, registry, packs, portfolios
│   ├── carbon_tax/              #     Carbon tax template tests
│   ├── subsidy/                 #     Subsidy template tests
│   ├── rebate/                  #     Rebate template tests
│   ├── feebate/                 #     Feebate template tests
│   ├── vehicle_malus/           #     Vehicle malus custom template tests
│   ├── energy_poverty_aid/      #     Energy poverty aid custom template tests
│   └── portfolios/              #     Portfolio composition and conflict tests
├── orchestrator/                #   Yearly loop, steps, panel output
├── discrete_choice/             #   Expansion, logit, vehicle/heating domains
├── calibration/                 #   Engine, targets, holdout validation
├── indicators/                  #   Distributional, geographic, welfare, fiscal, custom
├── governance/                  #   Manifest, hashing, lineage, replication
├── interfaces/                  #   Python API facade tests
├── population/                  #   Pipeline, validation, loaders, merge methods
│   ├── loaders/                 #     INSEE, Eurostat, ADEME, SDES loader tests
│   └── methods/                 #     Uniform, IPF, conditional sampling tests
├── vintage/                     #   Cohort types, transitions, config
├── visualization/               #   Display, plotting, styling tests
├── server/                      #   FastAPI route tests (TestClient)
├── benchmarks/                  #   Benchmark validation suite
│   └── references/              #     Reference data for benchmarks
├── docs/                        #   Documentation validation tests
├── notebooks/                   #   Notebook execution tests (nbmake)
└── fixtures/                    #   Shared test data
    ├── populations/             #     Sample population files
    ├── templates/               #     Sample template files
    ├── calibration/             #     Calibration target data
    ├── insee/, eurostat/        #     Mock institutional data
    ├── ademe/, sdes/            #     Mock agency data
    └── (various .parquet/.csv)  #     Test data files
```

---

## Supporting Directories

```text
notebooks/
├── quickstart.ipynb             # Getting started guide (run a simulation)
├── advanced.ipynb               # Multi-year, vintage, discrete choice
└── guides/                      # Topic-specific notebooks
    ├── 08_discrete_choice_model.ipynb
    ├── 09_population_generation.ipynb
    ├── 10_calibration_workflow.ipynb
    └── 11_replication_workflow.ipynb

examples/
├── api/                         # Python API usage examples
├── populations/                 # Population data examples
└── workflows/                   # YAML workflow examples

config/
└── deploy.yml                   # Kamal 2 deployment manifest

scripts/
├── generate_synthetic_population.py   # CLI population generator
└── check_ai_usage.py                  # AI provider usage monitor

.github/workflows/
├── ci.yml                       # CI: lint + type-check + test + notebooks
└── deploy.yml                   # CD: Docker build + Kamal deploy to Hetzner
```

---

## File Counts Summary

| Area | Files | Description |
| ---- | ----: | ----------- |
| Python source | 147 | 13 subsystem packages |
| Python tests | 190 | Unit + integration + benchmark |
| Frontend source | 80 | Components, API, hooks, context |
| Frontend tests | 35 | Component + workflow tests |
| Notebooks | 6 | Guides and demos |
| Total | **458** | Excluding config, docs, CI |
