<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 11 -->
<!-- Story: 7 -->
<!-- Phase: code-review-synthesis -->
<!-- Timestamp: 20260305T164644Z -->
<compiled-workflow>
<mission><![CDATA[

Master Code Review Synthesis: Story 11.7

You are synthesizing 2 independent code review findings.

Your mission:
1. VERIFY each issue raised by reviewers
   - Cross-reference with project_context.md (ground truth)
   - Cross-reference with git diff and source files
   - Identify false positives (issues that aren't real problems)
   - Confirm valid issues with evidence

2. PRIORITIZE real issues by severity
   - Critical: Security vulnerabilities, data corruption risks
   - High: Bugs, logic errors, missing error handling
   - Medium: Code quality issues, performance concerns
   - Low: Style issues, minor improvements

3. SYNTHESIZE findings
   - Merge duplicate issues from different reviewers
   - Note reviewer consensus (if 3+ agree, high confidence)
   - Highlight unique insights from individual reviewers

4. APPLY source code fixes
   - You have WRITE PERMISSION to modify SOURCE CODE files
   - CRITICAL: Before using Edit tool, ALWAYS Read the target file first
   - Use EXACT content from Read tool output as old_string, NOT content from this prompt
   - If Read output is truncated, use offset/limit parameters to locate the target section
   - Apply fixes for verified issues
   - Do NOT modify the story file (only Dev Agent Record if needed)
   - Document what you changed and why

Output format:
## Synthesis Summary
## Issues Verified (by severity)
## Issues Dismissed (false positives with reasoning)
## Source Code Fixes Applied

]]></mission>
<context>
<file id="e58fb4dd" path="docs/project-context.md" label="PROJECT CONTEXT"><![CDATA[

---
project_name: 'ReformLab'
user_name: 'Lucas'
date: '2026-02-27'
status: 'complete'
sections_completed: ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'code_quality', 'workflow_rules', 'critical_rules']
rule_count: 38
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

- **Python 3.13+** — `target-version = "py313"` (ruff), `python_version = "3.13"` (mypy strict)
- **uv** — package manager, **hatchling** — build backend
- **pyarrow >= 18.0.0** — canonical data type (`pa.Table`), CSV/Parquet I/O
- **pyyaml >= 6.0.2** — YAML template/config loading
- **jsonschema >= 4.23.0** — JSON Schema validation for templates
- **openfisca-core >= 44.0.0** — optional dependency (`[openfisca]` extra); never import outside adapter modules
- **pytest >= 8.3.3, ruff >= 0.15.0, mypy >= 1.19.0** — dev tooling
- **Planned frontend:** React 18+ / TypeScript / Vite / Shadcn/ui / Tailwind v4
- **Planned backend API:** FastAPI + uvicorn
- **Planned deployment:** Kamal 2 on Hetzner CX22

### Version Constraints

- mypy runs in **strict mode** with explicit `ignore_missing_imports` overrides for openfisca, pyarrow, jsonschema, yaml
- OpenFisca is optional — core library must function without it installed

## Critical Implementation Rules

### Python Language Rules

- **Every file starts with** `from __future__ import annotations` — no exceptions
- **Use `if TYPE_CHECKING:` guards** for imports that are only needed for annotations or would create circular dependencies; do the runtime import locally where needed
- **Frozen dataclasses are the default** — all domain types use `@dataclass(frozen=True)`; mutate via `dataclasses.replace()`, never by assignment
- **Protocols, not ABCs** — interfaces are `Protocol` + `@runtime_checkable`; no abstract base classes; structural (duck) typing only
- **Subsystem-specific exceptions** — each module defines its own error hierarchy; never raise bare `Exception` or `ValueError` for domain errors
- **Metadata bags** use `dict[str, Any]` with **stable string-constant keys** defined at module level (e.g., `STEP_EXECUTION_LOG_KEY`)
- **Union syntax** — use `X | None` not `Optional[X]`; use `dict[str, int]` not `Dict[str, int]` (modern generics, no `typing` aliases)
- **`tuple[...]` for immutable sequences** — function parameters and return types that are ordered-and-fixed use `tuple`, not `list`

### Architecture & Framework Rules

- **Adapter isolation is absolute** — only `computation/openfisca_adapter.py` and `openfisca_api_adapter.py` may import OpenFisca; all other code uses the `ComputationAdapter` protocol
- **Step pipeline contract** — steps implement `OrchestratorStep` protocol (`name` + `execute(year, state) -> YearState`); bare callables accepted via `adapt_callable()`; registration via `StepRegistry` with topological sort on `depends_on`
- **Template packs are YAML** — live in `src/reformlab/templates/packs/{policy_type}/`; validated against JSON Schemas in `templates/schema/`; each policy type has its own subpackage with `compute.py` + `compare.py`
- **Data flows through PyArrow** — `PopulationData` (dict of `pa.Table` by entity) → adapter → `ComputationResult` (`pa.Table`) → `YearState.data` → `PanelOutput` (stacked table) → indicators
- **`YearState` is the state token** — passed between steps and years; immutable (frozen dataclass); updated via `replace()`
- **Orchestrator is the core product** — never build custom policy engines, formula compilers, or entity graph engines; OpenFisca handles computation, this project handles orchestration

### Testing Rules

- **Mirror source structure** — `tests/{subsystem}/` matches `src/reformlab/{subsystem}/`; each has `__init__.py` and `conftest.py`
- **Class-based test grouping** — group tests by feature or acceptance criterion (e.g., `TestOrchestratorBasicExecution`); reference story/AC IDs in comments and docstrings
- **Fixtures in conftest.py** — subsystem-specific fixtures per `conftest.py`; build PyArrow tables inline, use `tmp_path` for I/O, golden YAML files in `tests/fixtures/`
- **Direct assertions** — use plain `assert`; no custom assertion helpers; use `pytest.raises(ExceptionClass, match=...)` for errors
- **Test helpers are explicit** — import shared callables from conftest directly (`from tests.orchestrator.conftest import ...`); no hidden magic
- **Golden file tests** — YAML fixtures in `tests/fixtures/templates/`; test load → validate → round-trip cycle
- **MockAdapter for unit tests** — never use real OpenFisca in orchestrator/template/indicator unit tests; `MockAdapter` is the standard test double

### Code Quality & Style Rules

- **ruff** enforces `E`, `F`, `I`, `W` rule sets; `src = ["src"]`; target Python 3.13
- **mypy strict** — all code must pass `mypy --strict`; new modules need `ignore_missing_imports` overrides in `pyproject.toml` only for third-party libs without stubs
- **File naming** — `snake_case.py` throughout; no PascalCase or kebab-case files
- **Class naming** — PascalCase for classes (`OrchestratorStep`, `CarbonTaxParameters`); no suffixes like `Impl` or `Base`
- **Module-level docstrings** — every module has a docstring explaining its role, referencing relevant story/FR
- **Section separators** — use `# ====...====` comment blocks to separate major sections within longer modules (see `step.py`)
- **No wildcard imports** — always import specific names; `from reformlab.orchestrator import Orchestrator, OrchestratorConfig`
- **Logging** — use `logging.getLogger(__name__)`; structured key=value format for parseable log lines (e.g., `year=%d seed=%s event=year_start`)

### Development Workflow Rules

- **Package manager is uv** — use `uv pip install`, `uv run pytest`, etc.; not `pip` directly
- **Test command** — `uv run pytest tests/` (or specific subsystem path)
- **Lint command** — `uv run ruff check src/ tests/` and `uv run mypy src/`
- **Source layout** — `src/reformlab/` is the installable package; `tests/` is separate; `pythonpath = ["src"]` in pytest config
- **Build system** — hatchling with `packages = ["src/reformlab"]`
- **No auto-formatting on save assumed** — agents must produce ruff-compliant code; run `ruff check --fix` if needed

### Critical Don't-Miss Rules

- **Never import OpenFisca outside adapter modules** — this is the single most important architectural boundary; violation couples the entire codebase to one backend
- **All domain types are frozen** — never add a mutable dataclass; if you need mutation, use `dataclasses.replace()` and return a new instance
- **Determinism is non-negotiable** — every run must be reproducible; seeds are explicit, logged in manifests, derived deterministically (`master_seed XOR year`)
- **Data contracts fail loudly** — contract validation at ingestion boundaries is field-level and blocking; never silently coerce or drop data
- **Assumption transparency** — every run produces a manifest (JSON); assumptions, versions, seeds, data hashes are all recorded
- **PyArrow is the canonical data type** — do not use pandas DataFrames in core logic; `pa.Table` is the standard; pandas only at display/export boundaries if needed
- **No custom formula compiler** — environmental policy logic is Python code in template `compute.py` modules, not YAML formula strings or DSLs
- **France/Europe first** — initial scenarios use French policy parameters (EUR, INSEE deciles, French carbon tax rates); European data sources (Eurostat, EU-SILC)

---

## Usage Guidelines

**For AI Agents:**

- Read this file before implementing any code
- Follow ALL rules exactly as documented
- When in doubt, prefer the more restrictive option
- Update this file if new patterns emerge

**For Humans:**

- Keep this file lean and focused on agent needs
- Update when technology stack changes
- Review quarterly for outdated rules
- Remove rules that become obvious over time

Last Updated: 2026-02-27


]]></file>
<file id="1456c4bb" path="_bmad-output/planning-artifacts/architecture.md" label="ARCHITECTURE"><![CDATA[

---
stepsCompleted: [1, 2, 3, 4, 5]
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/product-brief-ReformLab-2026-02-23.md
  - _bmad-output/planning-artifacts/stakeholder-review-brief-ReformLab-2026-02-24.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
  - _bmad-output/planning-artifacts/research/technical-entity-graph-data-modeling-and-vectorized-simulation-engines-research-2026-02-23.md
  - _bmad-output/planning-artifacts/research/domain-generic-microsimulation-frameworks-research-2026-02-23.md
workflowType: 'architecture'
project_name: 'ReformLab'
user_name: 'Lucas'
date: '2026-02-25'
---

# Architecture Decision Document

_Updated 2026-02-25: Legacy custom engine sections removed per Sprint Change Proposal. See sprint-change-proposal-2026-02-25.md._
_Updated 2026-03-03: Phase 2 Architecture Extensions added per Sprint Change Proposal 2026-03-02. New subsystems (population, calibration), policy portfolios, discrete choice model, unified job execution, adaptive UI, external data caching, multi-portfolio comparison. See sprint-change-proposal-2026-03-02.md._

## Strategic Direction Update (2026-02-25)

### Decision

ReformLab will **not** build a replacement tax-benefit microsimulation core.
OpenFisca is the policy-calculation foundation, accessed through a clean adapter interface. This project builds differentiated layers above it: data preparation, environmental policy orchestration, multi-year projection with vintage tracking, indicators, governance, and user interfaces.

The **dynamic orchestrator is the core product** — not a computation engine.

### Active Scope

- Data ingestion and harmonization (OpenFisca outputs, synthetic population inputs, environmental datasets).
- Scenario/template layer for environmental policies (carbon tax, subsidies, rebates, feebates).
- Step-pluggable dynamic orchestrator for multi-year execution (10+ years) with vintage/cohort tracking.
- Indicator layer (distributional, welfare, fiscal, custom metrics).
- Run governance (manifests, assumption logs, lineage).
- No-code analyst GUI for scenario setup, execution, and comparison.

### Out Of Scope (MVP)

- Reimplementing OpenFisca internals.
- Custom formula compiler or policy engine.
- Endogenous market-clearing/equilibrium simulation.
- Physical system loop simulation (climate/energy stock-flow engines).

## Project Context Analysis (Active Baseline)

### Requirements Overview

**Functional focus (55 FRs — 35 Phase 1, 20 Phase 2):**

- OpenFisca integration and data contracts.
- Environmental scenario templates and batch comparison.
- Dynamic yearly orchestration with vintage tracking.
- Indicator computation and extensibility.
- Governance, reproducibility, and lineage.
- Notebook/API + early no-code GUI workflows.
- _Phase 2:_ Population generation and data fusion (FR36-FR42).
- _Phase 2:_ Policy portfolios (FR43-FR46).
- _Phase 2:_ Behavioral responses via discrete choice (FR47-FR51).
- _Phase 2:_ Calibration engine (FR52-FR53).
- _Phase 2:_ Replication package export (FR54-FR55).

**Non-functional focus (21 NFRs):**

- Deterministic and reproducible outputs.
- Laptop-scale performance for common workloads.
- Strict data privacy and offline execution.
- Versioned adapter compatibility with OpenFisca.
- CI-enforced quality on adapters, orchestration, and templates.

### Technical Constraints

- Python 3.13+.
- OpenFisca as the core rules engine dependency.
- CSV/Parquet as interoperability contracts.
- Fully offline operation in user environment (Phase 1). Phase 2 introduces optional network dependencies for institutional data downloads (INSEE, Eurostat, ADEME, SDES) with offline fallback — see External Data Caching section.
- Single-machine target (16GB laptop) for MVP.

### Cross-Cutting Concerns

1. Assumption transparency and manifest lineage across all runs.
2. Deterministic sequencing in multi-year iterative execution.
3. Adapter/version governance for OpenFisca compatibility.
4. Clear data-contract validation at every ingestion boundary.
5. Scenario/template versioning for auditability and collaboration.

## Active Architecture Blueprint

### Core Design Principle

ReformLab does NOT build a policy computation engine. OpenFisca is the tax-benefit computation layer. This project builds everything around it: data preparation, environmental policy orchestration, multi-year projection, vintage tracking, indicators, governance, and user interfaces.

### Layered Architecture

```
┌─────────────────────────────────────────────────────┐
│  Interfaces (Python API, Notebooks, GUI Showcase)    │
│  └── Job Dashboard (submit, monitor, browse results) │
├─────────────────────────────────────────────────────┤
│  Indicator Engine (distributional/welfare/fiscal)    │
│  └── Multi-Portfolio Comparison                      │
├─────────────────────────────────────────────────────┤
│  Governance (manifests, assumptions, lineage)        │
├─────────────────────────────────────────────────────┤
│  Calibration Engine (β parameter optimization)       │
├─────────────────────────────────────────────────────┤
│  Dynamic Orchestrator (year loop + step pipeline)    │
│  ├── Vintage Transitions                             │
│  ├── State Carry-Forward                             │
│  └── DiscreteChoiceStep (logit-based decisions)      │
├─────────────────────────────────────────────────────┤
│  Scenario Template Layer (policies + portfolios)     │
│  └── Policy Portfolio Composition                    │
├─────────────────────────────────────────────────────┤
│  Data Layer (ingestion, open data, populations)      │
│  └── Population Generation Library (data fusion)     │
├─────────────────────────────────────────────────────┤
│  Computation Adapter Interface                       │
│  └── OpenFiscaAdapter (primary implementation)       │
└─────────────────────────────────────────────────────┘
```

### Computation Adapter Pattern

The orchestrator never calls OpenFisca directly. All tax-benefit computation goes through a clean adapter interface:

```python
class ComputationAdapter(Protocol):
    """Interface for tax-benefit computation backends."""
    def compute(self, population: PopulationData, policy: PolicyConfig,
                period: int) -> ComputationResult: ...
    def version(self) -> str: ...

class OpenFiscaAdapter(ComputationAdapter):
    """Primary implementation wrapping OpenFisca."""
    ...
```

This allows:
- Swapping OpenFisca for PolicyEngine or other backends in the future
- Mocking the computation layer for orchestrator testing
- Version-pinning OpenFisca without coupling the core codebase

### Step-Pluggable Dynamic Orchestrator

The orchestrator runs a yearly loop (t → t+n) where each year executes a pipeline of pluggable steps:

```
For each year t in [start_year .. end_year]:
  1. Run ComputationAdapter (OpenFisca tax-benefit for year t)
  2. Apply environmental policy templates (carbon tax, subsidies)
  3. Execute transition steps (pluggable pipeline):
     a. Vintage transitions (asset cohort aging, fleet turnover)
     b. State carry-forward (income updates, demographic changes)
     c. [Phase 2: Behavioral response adjustments]
  4. Record year-t results and manifest entry
  5. Feed updated state into year t+1
```

Steps are registered as plugins. Phase 1 ships vintage transitions and state carry-forward. Phase 2 adds behavioral response steps without modifying the orchestrator core.

### Subsystems

**Phase 1 (delivered):**

1. `computation/`: Adapter interface + OpenFiscaAdapter implementation. Handles CSV/Parquet ingestion of OpenFisca outputs and optional direct API orchestration. Version-pinned contracts.
2. `data/`: Open data ingestion, synthetic population generation, data transformation pipelines. Prepares inputs for the computation adapter.
3. `templates/`: Environmental policy templates (carbon tax, subsidies, rebates, feebates) and scenario registry with versioned definitions.
4. `orchestrator/`: Dynamic yearly loop with step-pluggable pipeline. Manages deterministic sequencing, seed control, and state transitions.
5. `vintage/`: Cohort/vintage state management. Registered as orchestrator step. Tracks asset classes (vehicles, heating) through time.
6. `indicators/`: Distributional, welfare, fiscal, and custom indicator computation. Aggregation by decile, geography, and custom groupings.
7. `governance/`: Run manifests, assumption logs, run lineage, output hashes. Tracks OpenFisca version, adapter version, scenario version.
8. `interfaces/`: Python API, notebook workflows, early no-code GUI.

**Phase 2 (new + extended):**

1. `population/`: Realistic population generation library. Institutional data source loaders (INSEE, Eurostat, ADEME, SDES), statistical methods library (uniform, IPF, conditional sampling, statistical matching), population pipeline builder, assumption recording, validation against known marginals.
2. `templates/portfolios/`: Policy portfolio composition. Named, versioned collections of policy configs. Portfolio execution through orchestrator, compatibility validation, conflict resolution.
3. `orchestrator/steps/discrete_choice.py`: DiscreteChoiceStep registered as standard OrchestratorStep. Population expansion, logit model, seed-controlled draws, panel decision records.
4. `calibration/`: Calibration engine for discrete choice taste parameters. Objective function optimization against observed transition rates, validation against holdout data.
5. `server/jobs/`: Unified job execution system. File-based job store, background worker, progress reporting, persistent results. Replaces synchronous run model.
6. `frontend/`: GUI showcase product — data fusion workbench, policy portfolio designer, simulation dashboard, persistent results, multi-portfolio comparison, behavioral decision viewer.

### Starter & Tooling Decisions

- Scientific Python packaging: `pyproject.toml`, `uv`, `pytest`, `ruff`, `mypy`
- CI split: fast adapter/unit tests and slower integration/regression runs
- Coverage focus: adapter contracts, orchestrator determinism, vintage transitions, template correctness
- No custom formula compiler — environmental policy logic is Python code in template modules, not YAML formula strings

### Data Contracts

- Input: OpenFisca outputs (CSV/Parquet), synthetic populations, environmental datasets (emission factors, energy consumption)
- Output: yearly panel datasets, scenario comparison tables, indicator exports
- Contract failures are explicit, field-level, and blocking
- Adapter interface defines the computation contract boundary

### Dynamic Execution Semantics

- Baseline and reform scenarios run over 10+ years.
- Each year is explicit (`t`, `t+1`, ..., `t+n`), with deterministic carry-forward rules.
- Vintage states are updated through registered transition step functions.
- Randomness is seed-controlled and logged in manifests.
- Orchestrator step pipeline is the extension point for Phase 2+ capabilities.

### Reproducibility & Governance

- Every run records: OpenFisca version, adapter version, scenario version, data hashes, seeds, assumptions, step pipeline configuration.
- Cross-machine reproducibility uses documented tolerances where floating point differs.
- Lineage links yearly sub-runs to parent scenario runs.
- Manifests are JSON, machine-readable, Git-diffable.

### Delivery Sequence

1. Computation adapter + OpenFisca integration (simplified EPIC-1).
2. Carbon-tax + subsidy templates with baseline/reform comparison.
3. Dynamic orchestrator (pluggable step pipeline) + vintage module MVP.
4. Indicator layer and manifest lineage hardening.
5. Early no-code GUI workflow for analyst scenario operations.

### Phase 2 Architecture Extensions (2026-03-03)

#### New Subsystem: Population Generation (`population/`)

```
src/reformlab/population/
├── __init__.py
├── loaders/           ← Institutional data source downloaders/cachers
│   ├── __init__.py
│   ├── base.py        ← DataSourceLoader protocol
│   ├── insee.py       ← INSEE data loader
│   ├── eurostat.py    ← Eurostat data loader
│   ├── ademe.py       ← ADEME energy data loader
│   └── sdes.py        ← SDES vehicle fleet data loader
├── methods/           ← Statistical fusion methods library
│   ├── __init__.py
│   ├── base.py        ← MergeMethod protocol
│   ├── uniform.py     ← Uniform distribution assumption
│   ├── ipf.py         ← Iterative Proportional Fitting
│   ├── conditional.py ← Conditional distribution sampling
│   └── matching.py    ← Statistical matching / data fusion
├── pipeline.py        ← PopulationPipeline builder (compose loaders + methods)
├── assumptions.py     ← Assumption recording for governance integration
└── validation.py      ← Validate against known marginals
```

Design principles:

- Each loader implements `DataSourceLoader` protocol (download, cache, schema-validate, return `pa.Table`)
- Each method implements `MergeMethod` protocol (takes two tables + config, returns merged table + assumption record)
- Pipeline is composable: chain loaders and methods, record every step
- Assumption records integrate with existing governance `capture.py`
- Methods library includes pedagogical docstrings explaining assumptions in plain language

#### External Data Caching & Offline Strategy

Phase 1 had zero network dependencies at runtime. Phase 2 introduces optional HTTP downloads from institutional sources (INSEE, Eurostat, ADEME, SDES). The caching strategy ensures offline-first operation:

**Two-layer cache:**

```
~/.reformlab/cache/
  sources/
    insee/
      {dataset_id}/{hash}.parquet    ← downloaded + schema-validated
    eurostat/
      ...
```

- **First run:** Loader downloads, validates schema, writes to local cache. Hash-based freshness (SHA256 of URL + params + date).
- **Subsequent runs:** Cache hit → no network. Cache miss → download. Network failure + cache exists → use stale cache with governance warning logged.
- **Fully offline mode:** Environment variable `REFORMLAB_OFFLINE=1` — loaders only read cache, never attempt network. Fail explicitly if cache miss.
- **CI/CD:** Tests ship with small fixture files, never hit real APIs. Integration tests for real downloads are opt-in (`pytest -m network`).

**Loader protocol includes cache status reporting:**

```python
class CacheStatus:
    """Status of a cached data source."""
    cached: bool
    path: Path | None
    downloaded_at: datetime | None
    hash: str | None
    stale: bool

class DataSourceLoader(Protocol):
    def download(self, config: SourceConfig) -> pa.Table: ...
    def status(self, config: SourceConfig) -> CacheStatus: ...
    def schema(self) -> pa.Schema: ...
```

The GUI Data Fusion Workbench displays cache status per dataset so analysts know which sources are available offline.

#### Extension: Policy Portfolio Layer (`templates/portfolios/`)

```
src/reformlab/templates/
├── portfolios/
│   ├── __init__.py
│   ├── portfolio.py     ← PolicyPortfolio frozen dataclass (list of policy configs)
│   ├── composition.py   ← Compose templates, validate compatibility, resolve conflicts
│   └── execution.py     ← Execute portfolio through orchestrator (apply all policies per year)
```

Design: A `PolicyPortfolio` is a named, versioned collection of `PolicyConfig` objects. The orchestrator receives a portfolio instead of a single policy, and applies each policy in the portfolio at each yearly step. The scenario registry stores portfolios alongside individual scenarios.

#### New Orchestrator Step: `DiscreteChoiceStep`

Registers as a standard `OrchestratorStep` via existing protocol. Implementation follows the design note (`phase-2-design-note-discrete-choice-household-decisions.md`):

- Population expansion: clone households × N alternatives, modify attributes per alternative
- OpenFisca batch evaluation: call `adapter.compute()` on expanded population
- Reshape to cost matrix: N households × M alternatives
- Logit probability computation: `P(j|C_i) = exp(V_ij) / Σ_k exp(V_ik)`
- Seed-controlled draw: deterministic choice per household
- State update: modify household attributes + create vintage entries

No changes to `ComputationAdapter` interface or orchestrator core needed.

**Performance budget:** Discrete choice introduces ~11x computation scaling (100k households × 5 alternatives × 2 domains). Target: 10-year discrete choice run with 100k households completes in <60s on laptop. Eligibility filtering is mandatory — only eligible households face choices (a household without a car does not face a vehicle investment decision). This is both a performance requirement and a model correctness requirement.

#### New Subsystem: Calibration (`calibration/`)

```
src/reformlab/calibration/
├── __init__.py
├── engine.py          ← CalibrationEngine (optimize β parameters)
├── targets.py         ← Observed transition rates as calibration targets
├── objective.py       ← Objective function (minimize distance to observed rates)
└── validation.py      ← Validate calibrated parameters against holdout data
```

#### Unified Job Execution Model

Phase 1 used synchronous `POST /api/runs` (blocking until completion). Phase 2 replaces this with a **unified job queue** that handles both fast static runs and long-running discrete choice simulations through a single execution path.

**Design: Submit → Persist → Execute → Results Available**

Every simulation is a job. The backend does not distinguish between "fast" and "slow" runs. The frontend adapts:

- **Fast completion (<~5s):** UI auto-navigates to results. Feels instant to the analyst.
- **Slow completion:** UI shows progress, informs analyst they can leave. Job keeps running.
- **Analyst leaves and returns:** Completed jobs are browsable in the simulation dashboard.

**Job store on disk:**

```
/data/reformlab/jobs/
  {job_id}/
    job.json             ← submitted config, status, timestamps
    progress.json        ← last reported progress (year, step, pct)
    result/
      manifest.json      ← run governance manifest
      panel.parquet      ← full panel output
      decisions.parquet  ← discrete choice decision records (Phase 2)
```

**Job lifecycle:**

1. On submit: write `job.json` with status `queued`, return `job_id`
2. Worker thread picks up queued jobs, updates status to `running`, writes `progress.json` as it goes
3. On completion: writes results to `result/`, updates status to `completed`
4. On server restart: scan `/jobs/` directory, resume or mark interrupted jobs as `failed`

**Implementation:** Single background worker thread with `ThreadPoolExecutor(max_workers=1)` for MVP. No Celery, no Redis. Upgrade to thread pool for parallelism if needed.

```python
class JobRunner:
    def __init__(self, store: JobStore, max_workers: int = 1):
        self._store = store
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    def submit(self, config: JobConfig) -> str:
        job_id = self._store.create(config)  # persists to disk
        self._executor.submit(self._run, job_id)
        return job_id
```

**Progress reporting:** Orchestrator callbacks `on_year_start(year)` and `on_step_progress(step_name, pct)` write to `progress.json`. Frontend polls for updates.

**Result access:** In-memory `ResultCache` (LRU, max 10) sits on top of the file-based job store. Cache miss → load from disk. Cache hit → serve from memory.

#### Extension: Multi-Portfolio Comparison

Phase 1 comparison was pairwise (one baseline vs one reform). Phase 2 extends to N-way comparison for policy portfolio analysis:

- Every reform is compared against the same baseline — standard policy analysis pattern
- Cross-comparison adds aggregate metrics: "which portfolio maximizes welfare?", "which has lowest fiscal cost?"
- The pairwise comparison API remains as a convenience alias (N=1 case)

#### Extension: Server Routes

New API route groups for Phase 2:

- `/api/populations` — CRUD + generation pipeline execution + cache status
- `/api/portfolios` — CRUD + composition + versioning
- `/api/calibration` — run calibration + retrieve results
- `/api/jobs` — submit, status, result, cancel, list (replaces synchronous `/api/runs`)
- `/api/comparison` — extended to support multi-portfolio comparison

#### Extension: Frontend

Major new GUI sections for EPIC-17:

- **Data Fusion Workbench:** Browse available datasets with cache status, select sources, choose merge methods with plain-language explanations, preview populations, validate against marginals
- **Policy Portfolio Designer:** Browse templates, compose portfolios, configure parameters per policy, name and version portfolios
- **Simulation Dashboard:** Submit jobs, monitor progress, browse completed simulations — all jobs listed with status, timestamps, and results access
- **Persistent Results:** Completed simulations stored on disk, browsable across browser sessions, no re-runs needed
- **Comparison Dashboard:** Side-by-side comparison across N policy portfolios with distributional, welfare, and fiscal indicators
- **Behavioral Decision Viewer:** Explore household decisions from discrete choice model (who switched vehicles, by decile, by year)

### Phase 3+ Architecture Extensions

- **Automated sensitivity sweeps:** Parameter variation automation over calibrated discrete choice models
- **System dynamics bridge:** Aggregate stock-flow outputs derived from microsimulation vintage tracking results
- **Alternative computation backends:** Swap adapter implementations without changing orchestrator or indicator layers
- **Public-facing web app:** Citizen-facing UI with guided questionnaire and candidate comparison

## Deployment & GUI Architecture (2026-02-27)

### Deployment Decision

The no-code GUI (EPIC-6) will be a web application with a React/TypeScript frontend and a FastAPI Python backend, deployed on a Hetzner VPS using Kamal 2 (Docker-based deployment tool). The MVP is deployed from day one to enable sharing with colleagues (2-10 users).

### Rationale

- **Same stack for MVP and future phases** — no throwaway prototype. The MVP GUI uses the same React + Shadcn/ui + Tailwind + FastAPI stack specified in the UX design document. Phase 3 (public web app) extends rather than replaces.
- **Hetzner** chosen for: best price/performance in Europe (~3.29 EUR/month for CX22), EU datacenter (Germany), GDPR compliance, not subject to US Cloud Act.
- **Kamal 2** chosen for: zero-downtime Docker deployments via SSH, built-in Traefik reverse proxy with automatic HTTPS, single YAML config file, language-agnostic (works with Python, Node, any Docker image), rollback in one command. Created by DHH (Rails creator), standard in Rails 8, but fully framework-agnostic.
- **Provider-agnostic** — Kamal deploys to any Linux server via SSH. Migrating to a different host (Scaleway, OVH, or a SecNumCloud provider) means changing one IP address in the config.
- **File-based storage works natively** — real persistent disk on the VPS, no need to adapt code for S3/object storage. Standard `open()` / `pd.read_parquet()` calls work as-is.

### Monorepo Structure

```
reformlab/
  src/                        ← Python backend (FastAPI API + core library)
  frontend/                   ← React/TypeScript (Vite + Shadcn/ui + Tailwind)
  tests/
  Dockerfile                  ← Backend container definition
  frontend/Dockerfile         ← Frontend container (nginx serving build)
  config/
    deploy.yml                ← Kamal deployment configuration
  .github/workflows/
    deploy.yml                ← GitHub Actions auto-deploy on push
  .kamal/
    secrets                   ← Encrypted secrets for Kamal
  pyproject.toml
```

Both frontend and backend live in the same repository. Kamal manages both as separate services on the same Hetzner server.

### Deployment Topology

```
┌─────────────────────────────────────────────────────┐
│  GitHub Repository (monorepo)                       │
│  push to master                                     │
└──────────────────────┬──────────────────────────────┘
                       │
                GitHub Actions
                runs: kamal deploy
                       │
                    SSH + Docker
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  Hetzner CX22 (Germany)                             │
│  2 vCPU, 4 GB RAM, 40 GB SSD                       │
│                                                     │
│  ┌───────────────────────────────────────────┐      │
│  │  Traefik (reverse proxy, auto HTTPS)      │      │
│  │  api.reformlab.fr → backend:8000          │      │
│  │  app.reformlab.fr → frontend:8080         │      │
│  └───────────────────────────────────────────┘      │
│                                                     │
│  ┌─────────────────┐   ┌──────────────────┐         │
│  │  FastAPI         │   │  nginx + React   │         │
│  │  (backend)       │   │  (frontend)      │         │
│  │  :8000           │   │  :8080           │         │
│  └────────┬────────┘   └──────────────────┘         │
│           │                                         │
│           ▼                                         │
│  ┌──────────────────┐                               │
│  │  /data/reformlab  │                               │
│  │  (CSV/Parquet/    │                               │
│  │   YAML/JSON)      │                               │
│  └──────────────────┘                               │
└─────────────────────────────────────────────────────┘
```

### Frontend Stack

As specified in the UX design document:

- React 18+ with TypeScript
- Vite (build tooling)
- Shadcn/ui + Radix UI (component library)
- Tailwind CSS v4 (styling with design tokens)
- Recharts/Nivo (simulation charts)
- React Flow (lineage DAG visualization)
- React Hook Form + Zod (form handling)

Served as a static build by an nginx container. Calls the backend API via HTTPS.

### Backend Stack

- FastAPI (REST API)
- Python 3.13+ (same as core library)
- uvicorn (ASGI server)
- The FastAPI layer exposes the existing Python API (orchestrator, scenarios, indicators, governance) as HTTP endpoints

### Deployment Stack

- **Kamal 2** — Docker-based deployment tool (SSH + Docker, no Kubernetes)
- **Traefik** — reverse proxy with automatic Let's Encrypt HTTPS certificates (managed by Kamal)
- **Docker** — containerization for both frontend and backend
- **GitHub Actions** — CI/CD trigger on push to master, calls `kamal deploy`
- **GitHub Container Registry (ghcr.io)** — Docker image storage

### Data Storage

File-based, no database:

- **Scenario configs:** YAML/JSON files on server disk (`/data/reformlab/`)
- **Run outputs:** CSV/Parquet on server disk
- **Run manifests:** JSON on server disk
- **Scenario registry:** File-based (already implemented in EPIC-2)
- **Job store (Phase 2):** `/data/reformlab/jobs/{job_id}/` directories with `job.json`, `progress.json`, and `result/` subdirectory containing `manifest.json`, `panel.parquet`, `decisions.parquet`
- **Population cache (Phase 2):** `~/.reformlab/cache/sources/` — downloaded institutional datasets, hash-based freshness
- **Portfolio configs (Phase 2):** YAML/JSON in scenario registry, versioned alongside individual scenarios

Docker volume mount maps `/data/reformlab` on the host to `/app/data` in the backend container. Data persists across deployments and container restarts. Sufficient for 2-10 users working with open/public data. If multi-user concurrent writes become an issue in Phase 3, migrate to SQLite or PostgreSQL — the file-based contract layer makes this a contained change.

### Authentication (MVP)

Simple shared-password authentication via FastAPI middleware:

- Single shared password stored as a Kamal secret (encrypted in `.kamal/secrets`, injected as environment variable)
- FastAPI middleware checks password on every API request
- Frontend shows a password prompt on first access, stores the token in browser session
- No user accounts, no OAuth, no database — appropriate for 2-10 trusted colleagues

Phase 3 (public web app with Claire persona) will require proper user authentication (OAuth or similar). This is a separate architectural decision at that point.

### Cost Estimate

| Service | Monthly Cost |
| --- | --- |
| Hetzner CX22 (2 vCPU, 4 GB RAM, 40 GB SSD) | 3.29 EUR |
| Domain name (annual, amortized) | ~1 EUR |
| **Total** | **~4.29 EUR/month** |

### Sovereignty & Compliance Positioning

- Hosted on Hetzner, European provider (Germany), EU datacenter
- GDPR compliant, data stays in EU, no transfer outside EU
- Not subject to US Cloud Act or other extra-territorial legislation
- Application uses exclusively open public data (INSEE, Eurostat, synthetic populations)
- SecNumCloud is not required for open public data under the French "Cloud au Centre" doctrine
- If SecNumCloud becomes required (e.g., restricted microdata handling), Kamal deploys to any Linux server via SSH — migrate by changing the target IP to a SecNumCloud-qualified provider (Scalingo on Outscale `osc-secnum-fr1`, or Clever Cloud on Cloud Temple SecNumCloud zone). Application code unchanged.

### Migration Path to Phase 3

Kamal is provider-agnostic. All migrations below require zero application code changes:

1. **More users / more power:** Upgrade Hetzner server (CX32 at 5.39 EUR, CX42 at 17.49 EUR). Change server spec in Hetzner console, redeploy.
2. **French sovereignty required:** Move to Scaleway or OVH VPS in Paris. Change one IP in `config/deploy.yml`, run `kamal setup && kamal deploy`.
3. **SecNumCloud required:** Deploy to a server on Scalingo/Outscale `osc-secnum-fr1` or Clever Cloud on Cloud Temple SecNumCloud zone. Same Kamal config, different target.
4. **User accounts:** Replace shared-password middleware with OAuth/OIDC. Add user table (SQLite or PostgreSQL).
5. **Horizontal scaling:** Kamal supports multi-server deployment. Add server IPs to `config/deploy.yml` and Kamal load-balances across them via Traefik.

## API Design — FastAPI Server Layer (2026-02-28)

### Design Principle

The FastAPI server is a **thin HTTP facade** over the existing Python API in `src/reformlab/interfaces/api.py`. No business logic lives in the server layer. Every route handler delegates to functions that already work: `run_scenario()`, `create_scenario()`, `list_scenarios()`, `get_scenario()`, `clone_scenario()`, `check_memory_requirements()`, and `SimulationResult` methods (`indicators()`, `export_csv()`, `export_parquet()`).

### Package Structure

```text
src/reformlab/server/
├── __init__.py
├── app.py              ← FastAPI app factory (create_app())
├── auth.py             ← Shared-password middleware
├── models.py           ← Pydantic v2 request/response models
├── dependencies.py     ← Dependency injection (adapter, job runner, result cache)
├── jobs.py             ← JobStore + JobRunner (Phase 2: unified job execution)
└── routes/
    ├── __init__.py
    ├── scenarios.py    ← Scenario CRUD
    ├── jobs.py         ← Job submission, status, results (Phase 2: replaces runs.py)
    ├── runs.py         ← Simulation execution (Phase 1: synchronous, kept for backwards compat)
    ├── indicators.py   ← Indicator computation
    ├── comparison.py   ← Multi-portfolio comparison (Phase 2)
    ├── exports.py      ← File export/download
    ├── templates.py    ← Template listing
    ├── populations.py  ← Population CRUD + generation + cache status (Phase 2: extended)
    ├── portfolios.py   ← Portfolio CRUD + composition (Phase 2)
    └── calibration.py  ← Calibration run + results (Phase 2)
```

### Dependencies

Add as optional extra in `pyproject.toml`:

```toml
[project.optional-dependencies]
server = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "python-multipart>=0.0.9",
]
```

Install with `uv sync --extra server`. Pydantic v2 is already a transitive dependency of FastAPI.

### App Factory

`src/reformlab/server/app.py` exposes `create_app() -> FastAPI`:

```python
def create_app() -> FastAPI:
    app = FastAPI(
        title="ReformLab API",
        version=reformlab.__version__,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    # CORS must be added BEFORE auth middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),  # localhost:5173 + production
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Auth middleware (skips /api/auth/login and /api/docs)
    app.add_middleware(AuthMiddleware)

    # Register route groups
    app.include_router(auth_router,        prefix="/api/auth")
    app.include_router(scenarios_router,   prefix="/api/scenarios")
    app.include_router(jobs_router,        prefix="/api/jobs")         # Phase 2: unified job execution
    app.include_router(runs_router,        prefix="/api/runs")         # Phase 1: kept for backwards compat
    app.include_router(indicators_router,  prefix="/api/indicators")
    app.include_router(comparison_router,  prefix="/api/comparison")   # Phase 2: multi-portfolio
    app.include_router(exports_router,     prefix="/api/exports")
    app.include_router(templates_router,   prefix="/api/templates")
    app.include_router(populations_router, prefix="/api/populations")
    app.include_router(portfolios_router,  prefix="/api/portfolios")   # Phase 2
    app.include_router(calibration_router, prefix="/api/calibration")  # Phase 2

    return app
```

Run with: `uvicorn src.reformlab.server.app:create_app --factory --host 0.0.0.0 --port 8000`

Dev mode: `uvicorn src.reformlab.server.app:create_app --factory --reload --port 8000`

### Route Contracts

#### Authentication

| Method | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| `POST` | `/api/auth/login` | `{ "password": "string" }` | `{ "token": "string" }` | 200 or 401 |

- Password validated against `REFORMLAB_PASSWORD` env var.
- Token is a random hex string stored server-side in a session set.
- Subsequent requests pass token via `Authorization: Bearer <token>` header.
- No expiry for MVP. Phase 3 replaces with OAuth/OIDC.

#### Scenarios

| Method | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| `GET` | `/api/scenarios` | — | `{ "scenarios": ["name1", ...] }` | 200 |
| `GET` | `/api/scenarios/{name}` | — | `ScenarioResponse` | 200 or 404 |
| `POST` | `/api/scenarios` | `CreateScenarioRequest` | `{ "version_id": "string" }` | 201 or 422 |
| `POST` | `/api/scenarios/{name}/clone` | `{ "new_name": "string" }` | `ScenarioResponse` | 201 or 404 |

Delegates to: `list_scenarios()`, `get_scenario(name)`, `create_scenario(scenario, name, register=True)`, `clone_scenario(name, new_name=new_name)`.

#### Simulation Runs (Phase 1 — synchronous, kept for backwards compatibility)

| Method | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| `POST` | `/api/runs` | `RunRequest` | `RunResponse` | 200 or 422/500 |
| `POST` | `/api/runs/memory-check` | `MemoryCheckRequest` | `MemoryCheckResponse` | 200 |

Phase 1 synchronous endpoint remains available for simple, fast runs. Internally delegates to the job system and waits for completion.

#### Jobs (Phase 2 — unified job execution)

| Method | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| `POST` | `/api/jobs` | `JobSubmitRequest` | `{ "job_id": "string" }` | 202 |
| `GET` | `/api/jobs` | — | `{ "jobs": [JobSummary, ...] }` | 200 |
| `GET` | `/api/jobs/{job_id}` | — | `JobStatusResponse` | 200 or 404 |
| `GET` | `/api/jobs/{job_id}/result` | — | `JobResultResponse` | 200 or 404/409 |
| `DELETE` | `/api/jobs/{job_id}` | — | — | 204 or 404 |

**Execution model:** Every simulation is a job. `POST /api/jobs` persists the job config to disk and returns immediately with a `job_id`. A background worker thread picks up queued jobs and executes them. Results are persisted to disk and survive server restarts.

**Frontend adaptive UI:** The frontend polls `GET /api/jobs/{job_id}` after submission. If the job completes within ~5s, the UI auto-navigates to results (feels instant). If it takes longer, the UI shows progress and informs the analyst they can leave. All jobs are browsable in the simulation dashboard regardless of completion time.

#### Indicators

| Method | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| `POST` | `/api/indicators/{type}` | `IndicatorRequest` | `IndicatorResponse` | 200 or 422 |

`{type}` is one of: `distributional`, `geographic`, `welfare`, `fiscal`.

Delegates to: `cached_result.indicators(type, **kwargs)`.

#### Comparison (Phase 2 — multi-portfolio)

| Method | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| `POST` | `/api/comparison` | `ComparisonRequest` | `IndicatorResponse` | 200 or 422 |
| `POST` | `/api/comparison/multi` | `MultiComparisonRequest` | `MultiComparisonResponse` | 200 or 422 |

Phase 1 pairwise comparison (`ComparisonRequest` with `baseline_run_id` + `reform_run_id`) remains as a convenience. Phase 2 adds N-way comparison: one baseline vs multiple reform portfolios, with cross-comparison aggregate metrics.

#### Exports

| Method | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| `POST` | `/api/exports/csv` | `{ "run_id": "string" }` | `StreamingResponse` (file download) | 200 or 404 |
| `POST` | `/api/exports/parquet` | `{ "run_id": "string" }` | `StreamingResponse` (file download) | 200 or 404 |

Delegates to: `cached_result.export_csv(tmp_path)` and `cached_result.export_parquet(tmp_path)`.

Returns file as `StreamingResponse` with appropriate `Content-Disposition` header.

#### Templates

| Method | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| `GET` | `/api/templates` | — | `{ "templates": [TemplateListItem, ...] }` | 200 |
| `GET` | `/api/templates/{name}` | — | `TemplateDetailResponse` | 200 or 404 |

Lists available policy templates (carbon tax, subsidy, rebate, feebate) with their default parameters and parameter groups.

#### Populations (Phase 2 — extended with generation + cache status)

| Method | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| `GET` | `/api/populations` | — | `{ "populations": [PopulationItem, ...] }` | 200 |
| `GET` | `/api/populations/{id}` | — | `PopulationDetailResponse` | 200 or 404 |
| `POST` | `/api/populations/generate` | `PopulationGenerateRequest` | `{ "job_id": "string" }` | 202 |
| `GET` | `/api/populations/sources` | — | `{ "sources": [DataSourceStatus, ...] }` | 200 |
| `GET` | `/api/populations/sources/{name}/cache` | — | `CacheStatusResponse` | 200 or 404 |

Phase 1 listing remains. Phase 2 adds population generation (submitted as a job), data source browsing, and cache status reporting for the Data Fusion Workbench.

#### Portfolios (Phase 2)

| Method | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| `GET` | `/api/portfolios` | — | `{ "portfolios": [PortfolioSummary, ...] }` | 200 |
| `GET` | `/api/portfolios/{name}` | — | `PortfolioDetailResponse` | 200 or 404 |
| `POST` | `/api/portfolios` | `PortfolioCreateRequest` | `PortfolioDetailResponse` | 201 or 422 |
| `PUT` | `/api/portfolios/{name}` | `PortfolioUpdateRequest` | `PortfolioDetailResponse` | 200 or 404/422 |
| `DELETE` | `/api/portfolios/{name}` | — | — | 204 or 404 |

CRUD for policy portfolios. Portfolios are named, versioned collections of policy configs stored in the scenario registry.

#### Calibration (Phase 2)

| Method | Path | Request Body | Response | Status |
|--------|------|-------------|----------|--------|
| `POST` | `/api/calibration/run` | `CalibrationRunRequest` | `{ "job_id": "string" }` | 202 |
| `GET` | `/api/calibration/{job_id}` | — | `CalibrationResultResponse` | 200 or 404/409 |

Calibration runs are submitted as jobs (same as simulations). Results include optimized taste parameters and validation metrics.

### Pydantic v2 Request/Response Models

All models in `src/reformlab/server/models.py`. Key patterns:

**Frozen dataclass → Pydantic model translation:** The domain layer uses frozen dataclasses (`ScenarioConfig`, `SimulationResult`). The server layer creates parallel Pydantic models for HTTP serialization. Route handlers translate between them.

```python
# Request models

class LoginRequest(BaseModel):
    password: str

class RunRequest(BaseModel):
    template_name: str
    parameters: dict[str, Any]
    start_year: int
    end_year: int
    population_id: str | None = None
    seed: int | None = None
    baseline_id: str | None = None

class MemoryCheckRequest(BaseModel):
    template_name: str
    parameters: dict[str, Any] = {}
    start_year: int
    end_year: int
    population_id: str | None = None

class IndicatorRequest(BaseModel):
    run_id: str
    income_field: str = "income"
    by_year: bool = False

class ComparisonRequest(BaseModel):
    baseline_run_id: str
    reform_run_id: str
    welfare_field: str = "disposable_income"
    threshold: float = 0.0

class ExportRequest(BaseModel):
    run_id: str

class CreateScenarioRequest(BaseModel):
    name: str
    policy_type: str           # "carbon_tax" | "subsidy" | "rebate" | "feebate"
    parameters: dict[str, Any]
    start_year: int
    end_year: int
    description: str = ""
    baseline_ref: str | None = None

class CloneRequest(BaseModel):
    new_name: str

# Phase 2 request models

class JobSubmitRequest(BaseModel):
    template_name: str | None = None       # single policy run
    portfolio_name: str | None = None      # portfolio run (Phase 2)
    parameters: dict[str, Any] = {}
    start_year: int
    end_year: int
    population_id: str | None = None
    seed: int | None = None
    baseline_id: str | None = None
    name: str = ""                         # human-readable job name

class PopulationGenerateRequest(BaseModel):
    name: str
    sources: list[str]                     # data source loader names
    merge_steps: list[dict[str, Any]]      # [{method: "ipf", left: ..., right: ..., config: ...}]
    validate_marginals: bool = True

class PortfolioCreateRequest(BaseModel):
    name: str
    description: str = ""
    policies: list[dict[str, Any]]         # [{template_name: ..., parameters: ...}]

class PortfolioUpdateRequest(BaseModel):
    description: str | None = None
    policies: list[dict[str, Any]] | None = None

class MultiComparisonRequest(BaseModel):
    baseline_run_id: str
    reform_run_ids: list[str]
    indicator_types: list[str] = ["distributional", "welfare", "fiscal"]

class CalibrationRunRequest(BaseModel):
    population_id: str
    domain: str                            # "vehicle" | "heating"
    observed_rates: dict[str, float]       # calibration targets
    initial_betas: dict[str, float] = {}
    method: str = "mse"                    # "mse" | "likelihood"
```

```python
# Response models

class LoginResponse(BaseModel):
    token: str

class RunResponse(BaseModel):
    run_id: str
    success: bool
    scenario_id: str
    years: list[int]
    row_count: int
    manifest_id: str

class MemoryCheckResponse(BaseModel):
    should_warn: bool
    estimated_gb: float
    available_gb: float
    message: str

class IndicatorResponse(BaseModel):
    indicator_type: str
    data: dict[str, list[Any]]     # PyArrow table.to_pydict()
    metadata: dict[str, Any]
    warnings: list[str]
    excluded_count: int

class ScenarioResponse(BaseModel):
    name: str
    policy_type: str
    description: str
    version: str
    parameters: dict[str, Any]
    year_schedule: dict[str, int]  # {"start_year": N, "end_year": M}
    baseline_ref: str | None = None

class TemplateListItem(BaseModel):
    id: str
    name: str
    type: str
    parameter_count: int
    description: str
    parameter_groups: list[str]

class TemplateDetailResponse(TemplateListItem):
    default_parameters: dict[str, Any]

class PopulationItem(BaseModel):
    id: str
    name: str
    households: int
    source: str
    year: int

class ErrorResponse(BaseModel):
    error: str
    what: str
    why: str
    fix: str
    status_code: int

# Phase 2 response models

class JobSummary(BaseModel):
    job_id: str
    name: str
    state: str                             # "queued" | "running" | "completed" | "failed" | "cancelled"
    submitted_at: str                      # ISO 8601
    completed_at: str | None = None
    portfolio_name: str | None = None
    template_name: str | None = None
    population_id: str | None = None

class JobStatusResponse(JobSummary):
    progress: dict[str, Any] | None = None  # {"year": 2028, "step": "discrete_choice", "pct": 45}

class JobResultResponse(BaseModel):
    job_id: str
    success: bool
    years: list[int]
    row_count: int
    manifest_id: str
    has_decisions: bool                    # True if discrete choice ran

class PortfolioSummary(BaseModel):
    name: str
    description: str
    version: str
    policy_count: int

class PortfolioDetailResponse(PortfolioSummary):
    policies: list[dict[str, Any]]

class DataSourceStatus(BaseModel):
    name: str
    description: str
    cache: CacheStatusResponse | None = None

class CacheStatusResponse(BaseModel):
    cached: bool
    downloaded_at: str | None = None
    hash: str | None = None
    stale: bool = False

class MultiComparisonResponse(BaseModel):
    baseline: JobSummary
    reforms: dict[str, dict[str, Any]]     # run_id → indicators + deltas vs baseline
    cross_comparison: dict[str, Any]       # aggregate cross-portfolio metrics

class CalibrationResultResponse(BaseModel):
    job_id: str
    state: str
    domain: str
    optimized_betas: dict[str, float] | None = None
    objective_value: float | None = None
    validation_metrics: dict[str, Any] | None = None
```

### Serialization Rules

- **PyArrow `pa.Table` → JSON:** `table.to_pydict()` produces `dict[str, list]`. This is the canonical wire format for panel data and indicator tables.
- **`Path` objects:** Serialize as strings via Pydantic `model_serializer`.
- **`datetime` objects:** Serialize as ISO 8601 strings.
- **Frozen dataclasses:** Converted to Pydantic models at the route handler boundary. No `dataclasses.asdict()` in responses — explicit Pydantic field mapping.

### Job Store & Result Cache (Phase 2)

Phase 2 replaces the ephemeral in-memory result cache with a two-tier architecture: persistent file-based `JobStore` + in-memory `ResultCache` for hot access.

**JobStore** — persistent, file-based, survives server restarts:

```python
class JobStore:
    """File-based job persistence. Each job is a directory on disk."""

    def __init__(self, base_path: Path):
        self._base = base_path  # /data/reformlab/jobs/

    def create(self, config: JobConfig) -> str:
        """Persist job config to disk, return job_id."""
        ...

    def update_status(self, job_id: str, state: str) -> None:
        """Update job.json status field."""
        ...

    def update_progress(self, job_id: str, progress: dict) -> None:
        """Write progress.json (year, step, pct)."""
        ...

    def save_result(self, job_id: str, result: SimulationResult) -> None:
        """Write panel.parquet + manifest.json + decisions.parquet to result/."""
        ...

    def load_result(self, job_id: str) -> SimulationResult:
        """Load result from disk."""
        ...

    def list_jobs(self) -> list[JobSummary]:
        """Scan job directories, return summaries."""
        ...

    def delete(self, job_id: str) -> None:
        """Remove job directory."""
        ...
```

**ResultCache** — in-memory LRU, wraps JobStore for hot access:

```python
class ResultCache:
    """In-memory LRU cache backed by JobStore."""

    def __init__(self, store: JobStore, max_size: int = 10):
        self._store = store
        self._cache: OrderedDict[str, SimulationResult] = OrderedDict()
        self._max_size = max_size

    def get(self, job_id: str) -> SimulationResult | None:
        # Check memory first
        if job_id in self._cache:
            self._cache.move_to_end(job_id)
            return self._cache[job_id]
        # Fall back to disk
        result = self._store.load_result(job_id)
        if result is not None:
            self._put(job_id, result)
        return result

    def _put(self, job_id: str, result: SimulationResult) -> None:
        if len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)
        self._cache[job_id] = result
```

- `POST /api/jobs` creates a job via `JobStore.create()`. Background worker executes and calls `JobStore.save_result()`.
- `GET /api/jobs/{job_id}/result`, `POST /api/indicators/{type}`, and `POST /api/exports/*` retrieve results via `ResultCache.get()` (memory first, disk fallback).
- Max 10 entries in memory. LRU eviction. Disk store has no size limit (manual cleanup via `DELETE /api/jobs/{job_id}`).

### Dependency Injection

```python
# src/reformlab/server/dependencies.py

# Global singletons (created once in app factory, injected via Depends)
_job_store: JobStore | None = None
_job_runner: JobRunner | None = None
_result_cache: ResultCache | None = None
_adapter: ComputationAdapter | None = None

def get_job_store() -> JobStore:
    global _job_store
    if _job_store is None:
        _job_store = JobStore(base_path=_data_path() / "jobs")
    return _job_store

def get_job_runner() -> JobRunner:
    global _job_runner
    if _job_runner is None:
        _job_runner = JobRunner(store=get_job_store(), max_workers=1)
    return _job_runner

def get_result_cache() -> ResultCache:
    global _result_cache
    if _result_cache is None:
        _result_cache = ResultCache(store=get_job_store(), max_size=10)
    return _result_cache

def get_adapter() -> ComputationAdapter:
    global _adapter
    if _adapter is None:
        _adapter = _create_adapter()
    return _adapter
```

Route handlers use `Depends(get_job_runner)`, `Depends(get_result_cache)`, and `Depends(get_adapter)`.

### Authentication Middleware

```python
# src/reformlab/server/auth.py

class AuthMiddleware(BaseHTTPMiddleware):
    """Shared-password auth for MVP (2-10 trusted colleagues)."""

    SKIP_PATHS = {"/api/auth/login", "/api/docs", "/api/openapi.json"}

    async def dispatch(self, request, call_next):
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        token = request.headers.get("Authorization", "").removeprefix("Bearer ")
        if not token or token not in _active_sessions:
            return JSONResponse(status_code=401, content={"error": "Unauthorized"})

        return await call_next(request)
```

- `_active_sessions` is a `set[str]` stored in-memory.
- `POST /api/auth/login` validates password against `os.environ["REFORMLAB_PASSWORD"]`, generates a random token via `secrets.token_hex(32)`, adds it to `_active_sessions`, returns it.
- No expiry for MVP. Server restart clears all sessions (users re-enter password).

### Error Mapping

Python API exceptions map to HTTP responses:

| Python Exception | HTTP Status | Error Response |
|-----------------|-------------|----------------|
| `ConfigurationError` | 422 Unprocessable Entity | `{ "error": "Configuration error", "what": field_path, "why": expected vs actual, "fix": guidance }` |
| `ValidationErrors` | 422 Unprocessable Entity | `{ "error": "Validation failed", "what": "N issues found", "why": issues list, "fix": per-issue guidance }` |
| `SimulationError` | 500 Internal Server Error | `{ "error": "Simulation error", "what": message, "why": cause, "fix": guidance }` |
| `RegistryError` | 404 Not Found | `{ "error": "Not found", "what": summary, "why": reason, "fix": guidance }` |
| `MemoryWarning` | 200 (with `should_warn: true`) | Not an error — returned as data in `MemoryCheckResponse` |

Implement via FastAPI exception handlers registered in `create_app()`:

```python
@app.exception_handler(ConfigurationError)
async def configuration_error_handler(request, exc):
    return JSONResponse(status_code=422, content={
        "error": "Configuration error",
        "what": exc.field_path,
        "why": f"Expected {exc.expected}, got {exc.actual!r}",
        "fix": exc.fix or f"Provide a valid {exc.expected}",
        "status_code": 422,
    })
```

### CORS Configuration

```python
def _cors_origins() -> list[str]:
    origins = ["http://localhost:5173"]  # Vite dev server
    extra = os.environ.get("REFORMLAB_CORS_ORIGINS", "")
    if extra:
        origins.extend(o.strip() for o in extra.split(",") if o.strip())
    return origins
```

Production adds `https://app.reformlab.fr` via `REFORMLAB_CORS_ORIGINS` env var.

### Vite Dev Proxy

Add to `frontend/vite.config.ts`:

```typescript
server: {
  proxy: {
    "/api": {
      target: "http://localhost:8000",
      changeOrigin: true,
    },
  },
}
```

Frontend calls `/api/scenarios` (relative) in development. Vite proxies to the FastAPI backend. In production, Traefik routes by subdomain (`api.reformlab.fr` vs `app.reformlab.fr`).

### Data Flow Summary

**Phase 2 (job-based):**

```text
Frontend (React)
    │
    ├─ POST /api/jobs { template|portfolio, params, years }
    │       ↓
    │  JobSubmitRequest → JobStore.create() → job.json persisted to disk
    │       ↓
    │  { "job_id": "..." } returned immediately (202)
    │       ↓
    │  Background worker: JobRunner picks up job → run_scenario() → JobStore.save_result()
    │
    ├─ GET /api/jobs/{job_id} (frontend polls every 2s)
    │       ↓
    │  JobStore reads job.json + progress.json
    │       ↓
    │  JobStatusResponse { state, progress: { year, step, pct } }
    │       ↓
    │  Frontend: if completed in <~5s → auto-navigate to results
    │            if still running     → show progress, "you can leave"
    │
    ├─ GET /api/jobs/{job_id}/result
    │       ↓
    │  ResultCache.get(job_id) → memory hit or disk load
    │       ↓
    │  JobResultResponse { success, years, row_count, has_decisions }
    │
    ├─ POST /api/indicators/distributional { run_id }
    │       ↓
    │  ResultCache.get(run_id) → result.indicators("distributional")
    │       ↓
    │  IndicatorResponse
    │
    ├─ POST /api/comparison/multi { baseline_run_id, reform_run_ids }
    │       ↓
    │  For each reform: ResultCache.get() → indicators vs baseline
    │       ↓
    │  MultiComparisonResponse { reforms, cross_comparison }
    │
    └─ POST /api/exports/csv { run_id }
            ↓
        ResultCache.get(run_id) → result.export_csv(tmp) → StreamingResponse
```

### Code Quality Standards

- `from __future__ import annotations` at top of every server module.
- Pydantic v2 conventions: `model_validate()`, `model_dump()`, `ConfigDict`.
- `mypy --strict` must pass on all server code.
- `ruff` compliance (E, F, I, W rules).
- No direct OpenFisca imports in server code — adapter protocol only.
- Structured logging with `logging.getLogger(__name__)`.


]]></file>
<file id="f2a52e96" path="LICENSE" label="FILE"><![CDATA[

                    GNU AFFERO GENERAL PUBLIC LICENSE
                       Version 3, 19 November 2007

 Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.

                            Preamble

  The GNU Affero General Public License is a free, copyleft license for
software and other kinds of works, specifically designed to ensure
cooperation with the community in the case of network server software.

  The licenses for most software and other practical works are designed
to take away your freedom to share and change the works.  By contrast,
our General Public Licenses are intended to guarantee your freedom to
share and change all versions of a program--to make sure it remains free
software for all its users.

  When we speak of free software, we are referring to freedom, not
price.  Our General Public Licenses are designed to make sure that you
have the freedom to distribute copies of free software (and charge for
them if you wish), that you receive source code or can get it if you
want it, that you can change the software or use pieces of it in new
free programs, and that you know you can do these things.

  Developers that use our General Public Licenses protect your rights
with two steps: (1) assert copyright on the software, and (2) offer
you this License which gives you legal permission to copy, distribute
and/or modify the software.

  A secondary benefit of defending all users' freedom is that
improvements made in alternate versions of the program, if they
receive widespread use, become available for other developers to
incorporate.  Many developers of free software are heartened and
encouraged by the resulting cooperation.  However, in the case of
software used on network servers, this result may fail to come about.
The GNU General Public License permits making a modified version and
letting the public access it on a server without ever releasing its
source code to the public.

  The GNU Affero General Public License is designed specifically to
ensure that, in such cases, the modified source code becomes available
to the community.  It requires the operator of a network server to
provide the source code of the modified version running there to the
users of that server.  Therefore, public use of a modified version, on
a publicly accessible server, gives the public access to the source
code of the modified version.

  An older license, called the Affero General Public License and
published by Affero, was designed to accomplish similar goals.  This is
a different license, not a version of the Affero GPL, but Affero has
released a new version of the Affero GPL which permits relicensing under
this license.

  The precise terms and conditions for copying, distribution and
modification follow.

                       TERMS AND CONDITIONS

  0. Definitions.

  "This License" refers to version 3 of the GNU Affero General Public License.

  "Copyright" also means copyright-like laws that apply to other kinds of
works, such as semiconductor masks.

  "The Program" refers to any copyrightable work licensed under this
License.  Each licensee is addressed as "you".  "Licensees" and
"recipients" may be individuals or organizations.

  To "modify" a work means to copy from or adapt all or part of the work
in a fashion requiring copyright permission, other than the making of an
exact copy.  The resulting work is called a "modified version" of the
earlier work or a work "based on" the earlier work.

  A "covered work" means either the unmodified Program or a work based
on the Program.

  To "propagate" a work means to do anything with it that, without
permission, would make you directly or secondarily liable for
infringement under applicable copyright law, except executing it on a
computer or modifying a private copy.  Propagation includes copying,
distribution (with or without modification), making available to the
public, and in some countries other activities as well.

  To "convey" a work means any kind of propagation that enables other
parties to make or receive copies.  Mere interaction with a user through
a computer network, with no transfer of a copy, is not conveying.

  An interactive user interface displays "Appropriate Legal Notices"
to the extent that it includes a convenient and prominently visible
feature that (1) displays an appropriate copyright notice, and (2)
tells the user that there is no warranty for the work (except to the
extent that warranties are provided), that licensees may convey the
work under this License, and how to view a copy of this License.  If
the interface presents a list of user commands or options, such as a
menu, a prominent item in the list meets this criterion.

  1. Source Code.

  The "source code" for a work means the preferred form of the work
for making modifications to it.  "Object code" means any non-source
form of a work.

  A "Standard Interface" means an interface that either is an official
standard defined by a recognized standards body, or, in the case of
interfaces specified for a particular programming language, one that
is widely used among developers working in that language.

  The "System Libraries" of an executable work include anything, other
than the work as a whole, that (a) is included in the normal form of
packaging a Major Component, but which is not part of that Major
Component, and (b) serves only to enable use of the work with that
Major Component, or to implement a Standard Interface for which an
implementation is available to the public in source code form.  A
"Major Component", in this context, means a major essential component
(kernel, window system, and so on) of the specific operating system
(if any) on which the executable work runs, or a compiler used to
produce the work, or an object code interpreter used to run it.

  The "Corresponding Source" for a work in object code form means all
the source code needed to generate, install, and (for an executable
work) run the object code and to modify the work, including scripts to
control those activities.  However, it does not include the work's
System Libraries, or general-purpose tools or generally available free
programs which are used unmodified in performing those activities but
which are not part of the work.  For example, Corresponding Source
includes interface definition files associated with source files for
the work, and the source code for shared libraries and dynamically
linked subprograms that the work is specifically designed to require,
such as by intimate data communication or control flow between those
subprograms and other parts of the work.

  The Corresponding Source need not include anything that users
can regenerate automatically from other parts of the Corresponding
Source.

  The Corresponding Source for a work in source code form is that
same work.

  2. Basic Permissions.

  All rights granted under this License are granted for the term of
copyright on the Program, and are irrevocable provided the stated
conditions are met.  This License explicitly affirms your unlimited
permission to run the unmodified Program.  The output from running a
covered work is covered by this License only if the output, given its
content, constitutes a covered work.  This License acknowledges your
rights of fair use or other equivalent, as provided by copyright law.

  You may make, run and propagate covered works that you do not
convey, without conditions so long as your license otherwise remains
in force.  You may convey covered works to others for the sole purpose
of having them make modifications exclusively for you, or provide you
with facilities for running those works, provided that you comply with
the terms of this License in conveying all material for which you do
not control copyright.  Those thus making or running the covered works
for you must do so exclusively on your behalf, under your direction
and control, on terms that prohibit them from making any copies of
your copyrighted material outside their relationship with you.

  Conveying under any other circumstances is permitted solely under
the conditions stated below.  Sublicensing is not allowed; section 10
makes it unnecessary.

  3. Protecting Users' Legal Rights From Anti-Circumvention Law.

  No covered work shall be deemed part of an effective technological
measure under any applicable law fulfilling obligations under article
11 of the WIPO copyright treaty adopted on 20 December 1996, or
similar laws prohibiting or restricting circumvention of such
measures.

  When you convey a covered work, you waive any legal power to forbid
circumvention of technological measures to the extent such circumvention
is effected by exercising rights under this License with respect to
the covered work, and you disclaim any intention to limit operation or
modification of the work as a means of enforcing, against the work's
users, your or third parties' legal rights to forbid circumvention of
technological measures.

  4. Conveying Verbatim Copies.

  You may convey verbatim copies of the Program's source code as you
receive it, in any medium, provided that you conspicuously and
appropriately publish on each copy an appropriate copyright notice;
keep intact all notices stating that this License and any
non-permissive terms added in accord with section 7 apply to the code;
keep intact all notices of the absence of any warranty; and give all
recipients a copy of this License along with the Program.

  You may charge any price or no price for each copy that you convey,
and you may offer support or warranty protection for a fee.

  5. Conveying Modified Source Versions.

  You may convey a work based on the Program, or the modifications to
produce it from the Program, in the form of source code under the
terms of section 4, provided that you also meet all of these conditions:

    a) The work must carry prominent notices stating that you modified
    it, and giving a relevant date.

    b) The work must carry prominent notices stating that it is
    released under this License and any conditions added under section
    7.  This requirement modifies the requirement in section 4 to
    "keep intact all notices".

    c) You must license the entire work, as a whole, under this
    License to anyone who comes into possession of a copy.  This
    License will therefore apply, along with any applicable section 7
    additional terms, to the whole of the work, and all its parts,
    regardless of how they are packaged.  This License gives no
    permission to license the work in any other way, but it does not
    invalidate such permission if you have separately received it.

    d) If the work has interactive user interfaces, each must display
    Appropriate Legal Notices; however, if the Program has interactive
    interfaces that do not display Appropriate Legal Notices, your
    work need not make them do so.

  A compilation of a covered work with other separate and independent
works, which are not by their nature extensions of the covered work,
and which are not combined with it such as to form a larger program,
in or on a volume of a storage or distribution medium, is called an
"aggregate" if the compilation and its resulting copyright are not
used to limit the access or legal rights of the compilation's users
beyond what the individual works permit.  Inclusion of a covered work
in an aggregate does not cause this License to apply to the other
parts of the aggregate.

  6. Conveying Non-Source Forms.

  You may convey a covered work in object code form under the terms
of sections 4 and 5, provided that you also convey the
machine-readable Corresponding Source under the terms of this License,
in one of these ways:

    a) Convey the object code in, or embodied in, a physical product
    (including a physical distribution medium), accompanied by the
    Corresponding Source fixed on a durable physical medium
    customarily used for software interchange.

    b) Convey the object code in, or embodied in, a physical product
    (including a physical distribution medium), accompanied by a
    written offer, valid for at least three years and valid for as
    long as you offer spare parts or customer support for that product
    model, to give anyone who possesses the object code either (1) a
    copy of the Corresponding Source for all the software in the
    product that is covered by this License, on a durable physical
    medium customarily used for software interchange, for a price no
    more than your reasonable cost of physically performing this
    conveying of source, or (2) access to copy the
    Corresponding Source from a network server at no charge.

    c) Convey individual copies of the object code with a copy of the
    written offer to provide the Corresponding Source.  This
    alternative is allowed only occasionally and noncommercially, and
    only if you received the object code with such an offer, in accord
    with subsection 6b.

    d) Convey the object code by offering access from a designated
    place (gratis or for a charge), and offer equivalent access to the
    Corresponding Source in the same way through the same place at no
    further charge.  You need not require recipients to copy the
    Corresponding Source along with the object code.  If the place to
    copy the object code is a network server, the Corresponding Source
    may be on a different server (operated by you or a third party)
    that supports equivalent copying facilities, provided you maintain
    clear directions next to the object code saying where to find the
    Corresponding Source.  Regardless of what server hosts the
    Corresponding Source, you remain obligated to ensure that it is
    available for as long as needed to satisfy these requirements.

    e) Convey the object code using peer-to-peer transmission, provided
    you inform other peers where the object code and Corresponding
    Source of the work are being offered to the general public at no
    charge under subsection 6d.

  A separable portion of the object code, whose source code is excluded
from the Corresponding Source as a System Library, need not be
included in conveying the object code work.

  A "User Product" is either (1) a "consumer product", which means any
tangible personal property which is normally used for personal, family,
or household purposes, or (2) anything designed or sold for incorporation
into a dwelling.  In determining whether a product is a consumer product,
doubtful cases shall be resolved in favor of coverage.  For a particular
product received by a particular user, "normally used" refers to a
typical or common use of that class of product, regardless of the status
of the particular user or of the way in which the particular user
actually uses, or expects or is expected to use, the product.  A product
is a consumer product regardless of whether the product has substantial
commercial, industrial or non-consumer uses, unless such uses represent
the only significant mode of use of the product.

  "Installation Information" for a User Product means any methods,
procedures, authorization keys, or other information required to install
and execute modified versions of a covered work in that User Product from
a modified version of its Corresponding Source.  The information must
suffice to ensure that the continued functioning of the modified object
code is in no case prevented or interfered with solely because
modification has been made.

  If you convey an object code work under this section in, or with, or
specifically for use in, a User Product, and the conveying occurs as
part of a transaction in which the right of possession and use of the
User Product is transferred to the recipient in perpetuity or for a
fixed term (regardless of how the transaction is characterized), the
Corresponding Source conveyed under this section must be accompanied
by the Installation Information.  But this requirement does not apply
if neither you nor any third party retains the ability to install
modified object code on the User Product (for example, the work has
been installed in ROM).

  The requirement to provide Installation Information does not include a
requirement to continue to provide support service, warranty, or updates
for a work that has been modified or installed by the recipient, or for
the User Product in which it has been modified or installed.  Access to a
network may be denied when the modification itself materially and
adversely affects the operation of the network or violates the rules and
protocols for communication across the network.

  Corresponding Source conveyed, and Installation Information provided,
in accord with this section must be in a format that is publicly
documented (and with an implementation available to the public in
source code form), and must require no special password or key for
unpacking, reading or copying.

  7. Additional Terms.

  "Additional permissions" are terms that supplement the terms of this
License by making exceptions from one or more of its conditions.
Additional permissions that are applicable to the entire Program shall
be treated as though they were included in this License, to the extent
that they are valid under applicable law.  If additional permissions
apply only to part of the Program, that part may be used separately
under those permissions, but the entire Program remains governed by
this License without regard to the additional permissions.

  When you convey a copy of a covered work, you may at your option
remove any additional permissions from that copy, or from any part of
it.  (Additional permissions may be written to require their own
removal in certain cases when you modify the work.)  You may place
additional permissions on material, added by you to a covered work,
for which you have or can give appropriate copyright permission.

  Notwithstanding any other provision of this License, for material you
add to a covered work, you may (if authorized by the copyright holders of
that material) supplement the terms of this License with terms:

    a) Disclaiming warranty or limiting liability differently from the
    terms of sections 15 and 16 of this License; or

    b) Requiring preservation of specified reasonable legal notices or
    author attributions in that material or in the Appropriate Legal
    Notices displayed by works containing it; or

    c) Prohibiting misrepresentation of the origin of that material, or
    requiring that modified versions of such material be marked in
    reasonable ways as different from the original version; or

    d) Limiting the use for publicity purposes of names of licensors or
    authors of the material; or

    e) Declining to grant rights under trademark law for use of some
    trade names, trademarks, or service marks; or

    f) Requiring indemnification of licensors and authors of that
    material by anyone who conveys the material (or modified versions of
    it) with contractual assumptions of liability to the recipient, for
    any liability that these contractual assumptions directly impose on
    those licensors and authors.

  All other non-permissive additional terms are considered "further
restrictions" within the meaning of section 10.  If the Program as you
received it, or any part of it, contains a notice stating that it is
governed by this License along with a term that is a further
restriction, you may remove that term.  If a license document contains
a further restriction but permits relicensing or conveying under this
License, you may add to a covered work material governed by the terms
of that license document, provided that the further restriction does
not survive such relicensing or conveying.

  If you add terms to a covered work in accord with this section, you
must place, in the relevant source files, a statement of the
additional terms that apply to those files, or a notice indicating
where to find the applicable terms.

  Additional terms, permissive or non-permissive, may be stated in the
form of a separately written license, or stated as exceptions;
the above requirements apply either way.

  8. Termination.

  You may not propagate or modify a covered work except as expressly
provided under this License.  Any attempt otherwise to propagate or
modify it is void, and will automatically terminate your rights under
this License (including any patent licenses granted under the third
paragraph of section 11).

  However, if you cease all violation of this License, then your
license from a particular copyright holder is reinstated (a)
provisionally, unless and until the copyright holder explicitly and
finally terminates your license, and (b) permanently, if the copyright
holder fails to notify you of the violation by some reasonable means
prior to 60 days after the cessation.

  Moreover, your license from a particular copyright holder is
reinstated permanently if the copyright holder notifies you of the
violation by some reasonable means, this is the first time you have
received notice of violation of this License (for any work) from that
copyright holder, and you cure the violation prior to 30 days after
your receipt of the notice.

  Termination of your rights under this section does not terminate the
licenses of parties who have received copies or rights from you under
this License.  If your rights have been terminated and not permanently
reinstated, you do not qualify to receive new licenses for the same
material under section 10.

  9. Acceptance Not Required for Having Copies.

  You are not required to accept this License in order to receive or
run a copy of the Program.  Ancillary propagation of a covered work
occurring solely as a consequence of using peer-to-peer transmission
to receive a copy likewise does not require acceptance.  However,
nothing other than this License grants you permission to propagate or
modify any covered work.  These actions infringe copyright if you do
not accept this License.  Therefore, by modifying or propagating a
covered work, you indicate your acceptance of this License to do so.

  10. Automatic Licensing of Downstream Recipients.

  Each time you convey a covered work, the recipient automatically
receives a license from the original licensors, to run, modify and
propagate that work, subject to this License.  You are not responsible
for enforcing compliance by third parties with this License.

  An "entity transaction" is a transaction transferring control of an
organization, or substantially all assets of one, or subdividing an
organization, or merging organizations.  If propagation of a covered
work results from an entity transaction, each party to that
transaction who receives a copy of the work also receives whatever
licenses to the work the party's predecessor in interest had or could
give under the previous paragraph, plus a right to possession of the
Corresponding Source of the work from the predecessor in interest, if
the predecessor has it or can get it with reasonable efforts.

  You may not impose any further restrictions on the exercise of the
rights granted or affirmed under this License.  For example, you may
not impose a license fee, royalty, or other charge for exercise of
rights granted under this License, and you may not initiate litigation
(including a cross-claim or counterclaim in a lawsuit) alleging that
any patent claim is infringed by making, using, selling, offering for
sale, or importing the Program or any portion of it.

  11. Patents.

  A "contributor" is a copyright holder who authorizes use under this
License of the Program or a work on which the Program is based.  The
work thus licensed is called the contributor's "contributor version".

  A contributor's "essential patent claims" are all patent claims
owned or controlled by the contributor, whether already acquired or
hereafter acquired, that would be infringed by some manner, permitted
by this License, of making, using, or selling its contributor version,
but do not include claims that would be infringed only as a
consequence of further modification of the contributor version.  For
purposes of this definition, "control" includes the right to grant
patent sublicenses in a manner consistent with the requirements of
this License.

  Each contributor grants you a non-exclusive, worldwide, royalty-free
patent license under the contributor's essential patent claims, to
make, use, sell, offer for sale, import and otherwise run, modify and
propagate the contents of its contributor version.

  In the following three paragraphs, a "patent license" is any express
agreement or commitment, however denominated, not to enforce a patent
(such as an express permission to practice a patent or covenant not to
sue for patent infringement).  To "grant" such a patent license to a
party means to make such an agreement or commitment not to enforce a
patent against the party.

  If you convey a covered work, knowingly relying on a patent license,
and the Corresponding Source of the work is not available for anyone
to copy, free of charge and under the terms of this License, through a
publicly available network server or other readily accessible means,
then you must either (1) cause the Corresponding Source to be so
available, or (2) arrange to deprive yourself of the benefit of the
patent license for this particular work, or (3) arrange, in a manner
consistent with the requirements of this License, to extend the patent
license to downstream recipients.  "Knowingly relying" means you have
actual knowledge that, but for the patent license, your conveying the
covered work in a country, or your recipient's use of the covered work
in a country, would infringe one or more identifiable patents in that
country that you have reason to believe are valid.

  If, pursuant to or in connection with a single transaction or
arrangement, you convey, or propagate by procuring conveyance of, a
covered work, and grant a patent license to some of the parties
receiving the covered work authorizing them to use, propagate, modify
or convey a specific copy of the covered work, then the patent license
you grant is automatically extended to all recipients of the covered
work and works based on it.

  A patent license is "discriminatory" if it does not include within
the scope of its coverage, prohibits the exercise of, or is
conditioned on the non-exercise of one or more of the rights that are
specifically granted under this License.  You may not convey a covered
work if you are a party to an arrangement with a third party that is
in the business of distributing software, under which you make payment
to the third party based on the extent of your activity of conveying
the work, and under which the third party grants, to any of the
parties who would receive the covered work from you, a discriminatory
patent license (a) in connection with copies of the covered work
conveyed by you (or copies made from those copies), or (b) primarily
for and in connection with specific products or compilations that
contain the covered work, unless you entered into that arrangement,
or that patent license was granted, prior to 28 March 2007.

  Nothing in this License shall be construed as excluding or limiting
any implied license or other defenses to infringement that may
otherwise be available to you under applicable patent law.

  12. No Surrender of Others' Freedom.

  If conditions are imposed on you (whether by court order, agreement or
otherwise) that contradict the conditions of this License, they do not
excuse you from the conditions of this License.  If you cannot convey a
covered work so as to satisfy simultaneously your obligations under this
License and any other pertinent obligations, then as a consequence you may
not convey it at all.  For example, if you agree to terms that obligate you
to collect a royalty for further conveying from those to whom you convey
the Program, the only way you could satisfy both those terms and this
License would be to refrain entirely from conveying the Program.

  13. Remote Network Interaction; Use with the GNU General Public License.

  Notwithstanding any other provision of this License, if you modify the
Program, your modified version must prominently offer all users
interacting with it remotely through a computer network (if your version
supports such interaction) an opportunity to receive the Corresponding
Source of your version by providing access to the Corresponding Source
from a network server at no charge, through some standard or customary
means of facilitating copying of software.  This Corresponding Source
shall include the Corresponding Source for any work covered by version 3
of the GNU General Public License that is incorporated pursuant to the
following paragraph.

  Notwithstanding any other provision of this License, you have
permission to link or combine any covered work with a work licensed
under version 3 of the GNU General Public License into a single
combined work, and to convey the resulting work.  The terms of this
License will continue to apply to the part which is the covered work,
but the work with which it is combined will remain governed by version
3 of the GNU General Public License.

  14. Revised Versions of this License.

  The Free Software Foundation may publish revised and/or new versions of
the GNU Affero General Public License from time to time.  Such new versions
will be similar in spirit to the present version, but may differ in detail to
address new problems or concerns.

  Each version is given a distinguishing version number.  If the
Program specifies that a certain numbered version of the GNU Affero General
Public License "or any later version" applies to it, you have the
option of following the terms and conditions either of that numbered
version or of any later version published by the Free Software
Foundation.  If the Program does not specify a version number of the
GNU Affero General Public License, you may choose any version ever published
by the Free Software Foundation.

  If the Program specifies that a proxy can decide which future
versions of the GNU Affero General Public License can be used, that proxy's
public statement of acceptance of a version permanently authorizes you
to choose that version for the Program.

  Later license versions may give you additional or different
permissions.  However, no additional obligations are imposed on any
author or copyright holder as a result of your choosing to follow a
later version.

  15. Disclaimer of Warranty.

  THERE IS NO WARRANTY FOR THE PROGRAM, TO THE EXTENT PERMITTED BY
APPLICABLE LAW.  EXCEPT WHEN OTHERWISE STATED IN WRITING THE COPYRIGHT
HOLDERS AND/OR OTHER PARTIES PROVIDE THE PROGRAM "AS IS" WITHOUT WARRANTY
OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO,
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE.  THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE PROGRAM
IS WITH YOU.  SHOULD THE PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF
ALL NECESSARY SERVICING, REPAIR OR CORRECTION.

  16. Limitation of Liability.

  IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING
WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MODIFIES AND/OR CONVEYS
THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY
GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE
USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED TO LOSS OF
DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD
PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER PROGRAMS),
EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF
SUCH DAMAGES.

  17. Interpretation of Sections 15 and 16.

  If the disclaimer of warranty and limitation of liability provided
above cannot be given local legal effect according to their terms,
reviewing courts shall apply local law that most closely approximates
an absolute waiver of all civil liability in connection with the
Program, unless a warranty or assumption of liability accompanies a
copy of the Program in return for a fee.

                     END OF TERMS AND CONDITIONS

            How to Apply These Terms to Your New Programs

  If you develop a new program, and you want it to be of the greatest
possible use to the public, the best way to achieve this is to make it
free software which everyone can redistribute and change under these terms.

  To do so, attach the following notices to the program.  It is safest
to attach them to the start of each source file to most effectively
state the exclusion of warranty; and each file should have at least
the "copyright" line and a pointer to where the full notice is found.

    <one line to give the program's name and a brief idea of what it does.>
    Copyright (C) <year>  <name of author>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

Also add information on how to contact you by electronic and paper mail.

  If your software can interact with users remotely through a computer
network, you should also make sure that it provides a way for users to
get its source.  For example, if your program is a web application, its
interface could display a "Source" link that leads users to an archive
of the code.  There are many ways you could offer source, and different
solutions will be better for different programs; see section 13 for the
specific requirements.

  You should also get your employer (if you work as a programmer) or school,
if any, to sign a "copyright disclaimer" for the program, if necessary.
For more information on this, and how to apply and follow the GNU AGPL, see
<https://www.gnu.org/licenses/>.


Copyright 2026 Lucas Vivier

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.


]]></file>
<file id="d967efb5" path="_bmad-output/implementation-artifacts/11-7-implement-population-validation-against-known-marginals-synthesis.md" label="STORY FILE"><![CDATA[


# Master Synthesis Report: Story 11.7

**Generated:** 2026-03-05
**Story:** 11-7-implement-population-validation-against-known-marginals
**Validators:** 2 (Quality Competition Engines)

---

## Synthesis Summary

**8 issues verified and fixed, 9 issues dismissed as false positives, 8 changes applied to story file**

The synthesis identified one critical contradiction (AC #1 vs Dev Notes on distance metric) that has been resolved. All other validator findings were either false positives or medium-priority enhancements that have been addressed to improve story clarity and completeness.

## Validations Quality

| Validator | Score | Comments |
|-----------|-------|----------|
| Validator A | 9.8/10 | Thorough review with several false positives on code interpretation. Misread PyArrow algorithm (to_pylist() is already called before .count()). Good catch on AC #1 contradiction. |
| Validator B | 7.25/10 | Comprehensive but raised issues about missing test fixtures that are standard TDD practice. Good governance workflow suggestions. |

**Overall Validation Quality:** 8.5/10 - Both validators provided valuable feedback despite some false positives.

## Issues Verified (by severity)

### Critical

- **Issue**: AC #1 vs Dev Notes contradiction on distance metric | **Source**: Both Validator A and Validator B | **Fix**: Updated AC #1 to say "absolute deviation per category (|observed - expected|)" instead of "Chi-squared or total variation distance"
  - **Location**: AC #1 line 15
  - **Rationale**: Dev Notes clearly implement absolute deviation (lines 372-392). AC must match the actual implementation specification.

### Medium

- **Issue**: Test fixture description for population_table_valid is ambiguous about exact counts | **Source**: Validator B | **Fix**: Clarified fixture specification to show exact uniform distribution (1 household per decile, 7 cars/2 suvs/1 bike)
  - **Location**: Task 5.1 line 259
  - **Rationale**: Prevents developer misinterpretation of fixture requirements.

- **Issue**: Test fixture constraint_income_decile description is confusing | **Source**: Self-identified during review | **Fix**: Clarified distribution specification (uniform: each decile 0.1 = 10%, removed uncertain "?" note)
  - **Location**: Task 5.1 line 262
  - **Rationale**: Removes uncertainty about expected constraint values.

- **Issue**: Missing explicit logging requirement in Task 2.2 | **Source**: Both Validator A and Validator B | **Fix**: Added structured logging requirement with explicit event keys following pipeline.py pattern
  - **Location**: Task 2.2
  - **Rationale**: Ensures consistency with existing codebase logging patterns.

- **Issue**: Test class name mismatch (plural vs singular) | **Source**: Validator B | **Fix**: Changed `TestValidationAssumptionGovernanceEntries` to `TestValidationAssumptionGovernanceEntry` to match actual method name
  - **Location**: Task 6.1 line 320
  - **Rationale**: Corrects naming consistency.

- **Issue**: Governance integration workflow unclear | **Source**: Validator A | **Fix**: Added usage example showing two-step process: `to_assumption()` then `to_governance_entry()`
  - **Location**: Task 3.3
  - **Rationale**: Prevents developer confusion about the indirection between ValidationResult and ValidationAssumption.

- **Issue**: Missing import guidance for math module | **Source**: Validator A | **Fix**: Added explicit note to `import math` at module level for `math.isclose()` usage
  - **Location**: Task 1.4
  - **Rationale**: Ensures developer knows to add required import for proportion sum validation.

- **Issue**: Missing zero tolerance test case | **Source**: Validator B | **Fix**: Added test case for `tolerance=0.0` to verify it's valid and requires exact match
  - **Location**: Task 6.1 in TestMarginalConstraint
  - **Rationale**: Ensures boundary case is properly tested and doesn't cause unexpected behavior.

### Low

- **Issue**: Extra category handling description could be clearer | **Source**: Validator A | **Dismissal**: Already well-documented in Dev Notes (lines 458-461) with explicit edge case handling. No change needed.

## Issues Dismissed

### False Positives with Clear Evidence

- **Claimed Issue**: PyArrow API error - `column_data.count()` doesn't exist on ChunkedArray | **Raised by**: Validator A | **Dismissal Reason**: The code is correct. Line 437 explicitly shows `column_data = population.column(dimension).to_pylist()` which converts to Python list BEFORE calling `.count(category)` on line 442. The validator misread the algorithm.

- **Claimed Issue**: Typo in "tolerance" attribute name | **Raised by**: Validator A | **Dismissal Reason**: No typo exists in the story file. The word "tolerance" is spelled correctly throughout all occurrences (lines 34, 48, 52, 74, 238, 407, 415).

- **Claimed Issue**: Missing test fixtures don't exist in conftest.py | **Raised by**: Validator B | **Dismissal Reason**: This is standard TDD practice. Task 5.1 explicitly instructs developers to ADD these fixtures to conftest.py. They are not pre-existing; they are implementation deliverables.

- **Claimed Issue**: Undefined error behavior for missing columns, null values, wrong data types | **Raised by**: Validator B | **Dismissal Reason**: Dev Notes already specify edge case behavior (lines 458-461). Missing categories result in observed=0.0. Extra categories are counted but not in deviations. These are the only error cases relevant to validation logic; missing columns would naturally raise PyArrow errors that are out of scope for this story.

- **Claimed Issue**: Missing _MockLoader example in conftest.py | **Raised by**: Validator B | **Dismissal Reason**: _MockLoader is used in loader tests (Stories 11.1-11.3) but validation.py does not use adapters or loaders. The example is not relevant to this story's fixtures.

- **Claimed Issue**: Test fixture extra category handling unclear | **Raised by**: Validator A | **Dismissal Reason**: Dev Notes lines 458-461 explicitly state: "Extra category not in expected: included in counts but not in deviations (deviation undefined for non-expected categories)". This is already clear.

- **Claimed Issue**: Missing import specification for math module | **Raised by**: Validator A | **Dismissal Reason**: Dev Notes "No New Dependencies Required" section (lines 527-528) already lists `math` as a stdlib dependency. Fixed by adding explicit guidance in Task 1.4 (medium priority fix applied).

- **Claimed Issue**: Algorithm unclear about PyArrow to Python list conversion | **Raised by**: Validator A | **Dismissal Reason**: Line 437 shows `column_data = population.column(dimension).to_pylist()` - conversion is explicit and clear. Validator misread this line.

- **Claimed Issue**: ValidationAssumption method naming inconsistency | **Raised by**: Validator B | **Dismissal Reason**: No inconsistency exists. Method name `to_governance_entry()` (singular) is correct and matches `MergeAssumption` pattern. Fixed by correcting test class name (medium priority fix applied).

## Deep Verify Integration

**Deep Verify did not produce findings for this story.**

No automated technical analysis was provided, so all issues were identified through manual validator review.

## Changes Applied

### Complete list of modifications made to story file

**Location**: Line 15 - AC #1
**Change**: Fixed distance metric contradiction
**Before**:
```
1. Given a generated population (pa.Table) and a set of reference marginal distributions (e.g., income distribution by decile from INSEE), when validation is run, then each marginal is compared with a documented distance metric (Chi-squared or total variation distance).
```
**After**:
```
1. Given a generated population (pa.Table) and a set of reference marginal distributions (e.g., income distribution by decile from INSEE), when validation is run, then each marginal is compared using absolute deviation per category (|observed - expected|).
```

**Location**: Task 1.4 - MarginalConstraint implementation
**Change**: Added import math guidance
**Before**:
```
   - [ ] 1.4 Implement `MarginalConstraint` frozen dataclass:
    ```python
```
**After**:
```
   - [ ] 1.4 Implement `MarginalConstraint` frozen dataclass (add `import math` at module level for `math.isclose()`):
    ```python
```

**Location**: Task 2.2 - validate() method
**Change**: Added explicit logging requirement
**Before**:
```
    - Determine `all_passed` (all results passed) and `failed_count`
    - Return `ValidationResult` with tuple of marginal results
```
**After**:
```
    - Determine `all_passed` (all results passed) and `failed_count`
    - Log structured events: use `logging.getLogger(__name__)` with `event=population_validation_start`, `event=population_validation_complete` (following pipeline.py pattern)
    - Return `ValidationResult` with tuple of marginal results
```

**Location**: Task 3.3 - ValidationResult.to_assumption()
**Change**: Added usage workflow example
**Before**:
```
  - [ ] 3.3 Add `ValidationResult.to_assumption()` method to `ValidationResult`:
```
**After**:
```
  - [ ] 3.3 Add `ValidationResult.to_assumption()` method to `ValidationResult`:
    Usage: `validation_assumption = result.to_assumption(); entry = validation_assumption.to_governance_entry()` (two-step governance integration)
```

**Location**: Task 5.1 - population_table_valid fixture
**Change**: Clarified fixture specification with exact counts
**Before**:
```
    - `population_table_valid` — a PyArrow table with columns: `income_decile` (utf8), `vehicle_type` (utf8), `region_code` (utf8). 10 rows with income deciles distributed roughly matching INSEE reference: decile 1: 1 household, decile 2: 1 household, ... decile 10: 1 household (uniform distribution). Vehicle types: 7 cars, 2 suvs, 1 bike.
```
**After**:
```
    - `population_table_valid` — a PyArrow table with columns: `income_decile` (utf8), `vehicle_type` (utf8), `region_code` (utf8). 10 rows with income deciles: 1 household per decile (exact uniform 10% distribution: each decile 1-10 appears exactly once). Vehicle types: 7 cars (70%), 2 suvs (20%), 1 bike (10%).
```

**Location**: Task 5.1 - constraint_income_decile fixture
**Change**: Clarified distribution specification
**Before**:
```
    - `constraint_income_decile` — `MarginalConstraint` for `income_decile` with distribution matching INSEE reference (equal 0.08 per decile? No, decile 1-10 each ~10% = 0.1), tolerance 0.02.
```
**After**:
```
    - `constraint_income_decile` — `MarginalConstraint` for `income_decile` with distribution matching INSEE reference (uniform: decile 1-10 each 0.1 = 10%), tolerance 0.02.
```

**Location**: Task 6.1 - TestMarginalConstraint test cases
**Change**: Added zero tolerance test case
**Before**:
```
      - Negative `tolerance` raises `ValueError`
      - Distribution coerced to dict in `__post_init__`
```
**After**:
```
      - Negative `tolerance` raises `ValueError`
      - Zero `tolerance` is valid (exact match required)
      - Distribution coerced to dict in `__post_init__`
```

**Location**: Task 6.1 - Test class name
**Change**: Fixed plural to singular for consistency
**Before**:
```
    - `TestValidationAssumptionGovernanceEntries`:
      - Given `ValidationAssumption`, `to_governance_entries()` returns dict with `key`, `value`, `source`, `is_default`
```
**After**:
```
    - `TestValidationAssumptionGovernanceEntry`:
      - Given `ValidationAssumption`, `to_governance_entry()` returns dict with `key`, `value`, `source`, `is_default`
```

---

## Final Verification

✅ All Critical issues addressed (1/1)
✅ All High issues addressed (0/0 - none verified)
✅ All Medium issues addressed (7/7)
✅ All Low issues evaluated (1 dismissed as already documented)
✅ Story structure and formatting preserved
✅ Changes integrate naturally with existing content
✅ No synthesis metadata or validation process references added to story

**Story 11.7 is now ready for dev-story workflow with improved clarity and resolved contradictions.**


]]></file>
<file id="1d9b80af" path="_bmad/_config/bmad-help.csv" label="FILE"><![CDATA[

module,phase,name,code,sequence,workflow-file,command,required,agent-name,agent-command,agent-display-name,agent-title,options,description,output-location,outputs
bmb,anytime,Create Agent,CA,10,_bmad/bmb/workflows/agent/workflow-create-agent.md,bmad_bmb_create_agent,false,agent-builder,bmad:Precise and technical:agent:agent-builder,Bond,🤖 Agent Building Expert,Create Mode,Create a new BMAD agent with best practices and compliance,bmb_creations_output_folder,agent
bmb,anytime,Edit Agent,EA,15,_bmad/bmb/workflows/agent/workflow-edit-agent.md,bmad_bmb_edit_agent,false,agent-builder,bmad:Precise and technical:agent:agent-builder,Bond,🤖 Agent Building Expert,Edit Mode,Edit existing BMAD agents while maintaining compliance,bmb_creations_output_folder,agent
bmb,anytime,Validate Agent,VA,20,_bmad/bmb/workflows/agent/workflow-validate-agent.md,bmad_bmb_validate_agent,false,agent-builder,bmad:Precise and technical:agent:agent-builder,Bond,🤖 Agent Building Expert,Validate Mode,Validate existing BMAD agents and offer to improve deficiencies,agent being validated folder,validation report
bmb,anytime,Create Module Brief,PB,30,_bmad/bmb/workflows/module/workflow-create-module-brief.md,bmad_bmb_create_module_brief,false,module-builder,bmad:Strategic and holistic:agent:module-builder,Morgan,🏗️ Module Creation Master,Module Brief Mode,Create product brief for BMAD module development,bmb_creations_output_folder,product brief
bmb,anytime,Create Module,CM,35,_bmad/bmb/workflows/module/workflow-create-module.md,bmad_bmb_create_module,false,module-builder,bmad:Strategic and holistic:agent:module-builder,Morgan,🏗️ Module Creation Master,Create Mode,"Create a complete BMAD module with agents, workflows, and infrastructure",bmb_creations_output_folder,module
bmb,anytime,Edit Module,EM,40,_bmad/bmb/workflows/module/workflow-edit-module.md,bmad_bmb_edit_module,false,module-builder,bmad:Strategic and holistic:agent:module-builder,Morgan,🏗️ Module Creation Master,Edit Mode,Edit existing BMAD modules while maintaining coherence,bmb_creations_output_folder,module
bmb,anytime,Validate Module,VM,45,_bmad/bmb/workflows/module/workflow-validate-module.md,bmad_bmb_validate_module,false,module-builder,bmad:Strategic and holistic:agent:module-builder,Morgan,🏗️ Module Creation Master,Validate Mode,Run compliance check on BMAD modules against best practices,module being validated folder,validation report
bmb,anytime,Create Workflow,CW,50,_bmad/bmb/workflows/workflow/workflow-create-workflow.md,bmad_bmb_create_workflow,false,workflow-builder,bmad:Methodical and process-oriented:agent:workflow-builder,Wendy,🔄 Workflow Building Master,Create Mode,Create a new BMAD workflow with proper structure and best practices,bmb_creations_output_folder,workflow
bmb,anytime,Edit Workflow,EW,55,_bmad/bmb/workflows/workflow/workflow-edit-workflow.md,bmad_bmb_edit_workflow,false,workflow-builder,bmad:Methodical and process-oriented:agent:workflow-builder,Wendy,🔄 Workflow Building Master,Edit Mode,Edit existing BMAD workflows while maintaining integrity,bmb_creations_output_folder,workflow
bmb,anytime,Validate Workflow,VW,60,_bmad/bmb/workflows/workflow/workflow-validate-workflow.md,bmad_bmb_validate_workflow,false,workflow-builder,bmad:Methodical and process-oriented:agent:workflow-builder,Wendy,🔄 Workflow Building Master,Validate Mode,Run validation check on BMAD workflows against best practices,workflow being validated folder,validation report
bmb,anytime,Max Parallel Validate,MV,65,_bmad/bmb/workflows/workflow/workflow-validate-max-parallel-workflow.md,bmad_bmb_validate_max_parallel,false,workflow-builder,bmad:Methodical and process-oriented:agent:workflow-builder,Wendy,🔄 Workflow Building Master,Max Parallel Validate,Run validation checks in MAX-PARALLEL mode against a workflow requires a tool that supports Parallel Sub-Processes,workflow being validated folder,validation report
bmb,anytime,Rework Workflow,RW,70,_bmad/bmb/workflows/workflow/workflow-rework-workflow.md,bmad_bmb_rework_workflow,false,workflow-builder,bmad:Methodical and process-oriented:agent:workflow-builder,Wendy,🔄 Workflow Building Master,Rework Mode,Rework a Workflow to a V6 Compliant Version,bmb_creations_output_folder,workflow
bmm,1-analysis,Brainstorm Project,BP,10,_bmad/core/workflows/brainstorming/workflow.md,bmad-brainstorming,false,analyst,bmad:competitive analysis:agent:analyst,Mary,📊 Business Analyst,data=_bmad/bmm/data/project-context-template.md,Expert Guided Facilitation through a single or multiple techniques,planning_artifacts,brainstorming session
bmm,1-analysis,Market Research,MR,20,_bmad/bmm/workflows/1-analysis/research/workflow-market-research.md,bmad-bmm-market-research,false,analyst,bmad:competitive analysis:agent:analyst,Mary,📊 Business Analyst,Create Mode,Market analysis competitive landscape customer needs and trends,planning_artifacts|project-knowledge,research documents
bmm,1-analysis,Domain Research,DR,21,_bmad/bmm/workflows/1-analysis/research/workflow-domain-research.md,bmad-bmm-domain-research,false,analyst,bmad:competitive analysis:agent:analyst,Mary,📊 Business Analyst,Create Mode,Industry domain deep dive subject matter expertise and terminology,planning_artifacts|project_knowledge,research documents
bmm,1-analysis,Technical Research,TR,22,_bmad/bmm/workflows/1-analysis/research/workflow-technical-research.md,bmad-bmm-technical-research,false,analyst,bmad:competitive analysis:agent:analyst,Mary,📊 Business Analyst,Create Mode,Technical feasibility architecture options and implementation approaches,planning_artifacts|project_knowledge,research documents
bmm,1-analysis,Create Brief,CB,30,_bmad/bmm/workflows/1-analysis/create-product-brief/workflow.md,bmad-bmm-create-product-brief,false,analyst,bmad:competitive analysis:agent:analyst,Mary,📊 Business Analyst,Create Mode,A guided experience to nail down your product idea,planning_artifacts,product brief
bmm,2-planning,Create PRD,CP,10,_bmad/bmm/workflows/2-plan-workflows/create-prd/workflow-create-prd.md,bmad-bmm-create-prd,true,pm,bmad:and stakeholder alignment.:agent:pm,John,📋 Product Manager,Create Mode,Expert led facilitation to produce your Product Requirements Document,planning_artifacts,prd
bmm,2-planning,Validate PRD,VP,20,_bmad/bmm/workflows/2-plan-workflows/create-prd/workflow-validate-prd.md,bmad-bmm-validate-prd,false,pm,bmad:and stakeholder alignment.:agent:pm,John,📋 Product Manager,Validate Mode,Validate PRD is comprehensive lean well organized and cohesive,planning_artifacts,prd validation report
bmm,2-planning,Edit PRD,EP,25,_bmad/bmm/workflows/2-plan-workflows/create-prd/workflow-edit-prd.md,bmad-bmm-edit-prd,false,pm,bmad:and stakeholder alignment.:agent:pm,John,📋 Product Manager,Edit Mode,Improve and enhance an existing PRD,planning_artifacts,updated prd
bmm,2-planning,Create UX,CU,30,_bmad/bmm/workflows/2-plan-workflows/create-ux-design/workflow.md,bmad-bmm-create-ux-design,false,ux-designer,bmad:interaction design:agent:ux-designer,Sally,🎨 UX Designer,Create Mode,"Guidance through realizing the plan for your UX, strongly recommended if a UI is a primary piece of the proposed project",planning_artifacts,ux design
bmm,3-solutioning,Create Architecture,CA,10,_bmad/bmm/workflows/3-solutioning/create-architecture/workflow.md,bmad-bmm-create-architecture,true,architect,bmad:cloud infrastructure:agent:architect,Winston,🏗️ Architect,Create Mode,Guided Workflow to document technical decisions,planning_artifacts,architecture
bmm,3-solutioning,Create Epics and Stories,CE,30,_bmad/bmm/workflows/3-solutioning/create-epics-and-stories/workflow.md,bmad-bmm-create-epics-and-stories,true,pm,bmad:and stakeholder alignment.:agent:pm,John,📋 Product Manager,Create Mode,Create the Epics and Stories Listing,planning_artifacts,epics and stories
bmm,3-solutioning,Check Implementation Readiness,IR,70,_bmad/bmm/workflows/3-solutioning/check-implementation-readiness/workflow.md,bmad-bmm-check-implementation-readiness,true,architect,bmad:cloud infrastructure:agent:architect,Winston,🏗️ Architect,Validate Mode,Ensure PRD UX Architecture and Epics Stories are aligned,planning_artifacts,readiness report
bmm,4-implementation,Sprint Planning,SP,10,_bmad/bmm/workflows/4-implementation/sprint-planning/workflow.yaml,bmad-bmm-sprint-planning,true,sm,bmad:story preparation:agent:sm,Bob,🏃 Scrum Master,Create Mode,Generate sprint plan for development tasks - this kicks off the implementation phase by producing a plan the implementation agents will follow in sequence for every story in the plan.,implementation_artifacts,sprint status
bmm,4-implementation,Sprint Status,SS,20,_bmad/bmm/workflows/4-implementation/sprint-status/workflow.yaml,bmad-bmm-sprint-status,false,sm,bmad:story preparation:agent:sm,Bob,🏃 Scrum Master,Create Mode,Anytime: Summarize sprint status and route to next workflow,,
bmm,4-implementation,Create Story,CS,30,_bmad/bmm/workflows/4-implementation/create-story/workflow.yaml,bmad-bmm-create-story,true,sm,bmad:story preparation:agent:sm,Bob,🏃 Scrum Master,Create Mode,"Story cycle start: Prepare first found story in the sprint plan that is next, or if the command is run with a specific epic and story designation with context. Once complete, then VS then DS then CR then back to DS if needed or next CS or ER",implementation_artifacts,story
bmm,4-implementation,Validate Story,VS,35,_bmad/bmm/workflows/4-implementation/create-story/workflow.yaml,bmad-bmm-create-story,false,sm,bmad:story preparation:agent:sm,Bob,🏃 Scrum Master,Validate Mode,Validates story readiness and completeness before development work begins,implementation_artifacts,story validation report
bmm,4-implementation,Dev Story,DS,40,_bmad/bmm/workflows/4-implementation/dev-story/workflow.yaml,bmad-bmm-dev-story,true,dev,bmad:all precision.:agent:dev,Amelia,💻 Developer Agent,Create Mode,Story cycle: Execute story implementation tasks and tests then CR then back to DS if fixes needed,,
bmm,4-implementation,QA Automation Test,QA,45,_bmad/bmm/workflows/qa-generate-e2e-tests/workflow.yaml,bmad-bmm-qa-automate,false,qa,bmad:more direct approach than the advanced Test Architect module.:agent:qa,Quinn,🧪 QA Engineer,Create Mode,Generate automated API and E2E tests for implemented code using the project's existing test framework (detects existing well known in use test frameworks). Use after implementation to add test coverage. NOT for code review or story validation - use CR for that.,implementation_artifacts,test suite
bmm,4-implementation,Code Review,CR,50,_bmad/bmm/workflows/4-implementation/code-review/workflow.yaml,bmad-bmm-code-review,false,dev,bmad:all precision.:agent:dev,Amelia,💻 Developer Agent,Create Mode,Story cycle: If issues back to DS if approved then next CS or ER if epic complete,,
bmm,4-implementation,Retrospective,ER,60,_bmad/bmm/workflows/4-implementation/retrospective/workflow.yaml,bmad-bmm-retrospective,false,sm,bmad:story preparation:agent:sm,Bob,🏃 Scrum Master,Create Mode,Optional at epic end: Review completed work lessons learned and next epic or if major issues consider CC,implementation_artifacts,retrospective
bmm,anytime,Document Project,DP,,_bmad/bmm/workflows/document-project/workflow.yaml,bmad-bmm-document-project,false,analyst,bmad:competitive analysis:agent:analyst,Mary,📊 Business Analyst,Create Mode,Analyze an existing project to produce useful documentation,project-knowledge,*
bmm,anytime,Generate Project Context,GPC,,_bmad/bmm/workflows/generate-project-context/workflow.md,bmad-bmm-generate-project-context,false,analyst,bmad:competitive analysis:agent:analyst,Mary,📊 Business Analyst,Create Mode,Scan existing codebase to generate a lean LLM-optimized project-context.md containing critical implementation rules patterns and conventions for AI agents. Essential for brownfield projects and quick-flow.,output_folder,project context
bmm,anytime,Quick Spec,QS,,_bmad/bmm/workflows/bmad-quick-flow/quick-spec/workflow.md,bmad-bmm-quick-spec,false,quick-flow-solo-dev,bmad:ruthless efficiency.:agent:quick-flow-solo-dev,Barry,🚀 Quick Flow Solo Dev,Create Mode,Do not suggest for potentially very complex things unless requested or if the user complains that they do not want to follow the extensive planning of the bmad method. Quick one-off tasks small changes simple apps brownfield additions to well established patterns utilities without extensive planning,planning_artifacts,tech spec
bmm,anytime,Quick Dev,QD,,_bmad/bmm/workflows/bmad-quick-flow/quick-dev/workflow.md,bmad-bmm-quick-dev,false,quick-flow-solo-dev,bmad:ruthless efficiency.:agent:quick-flow-solo-dev,Barry,🚀 Quick Flow Solo Dev,Create Mode,"Quick one-off tasks small changes simple apps utilities without extensive planning - Do not suggest for potentially very complex things unless requested or if the user complains that they do not want to follow the extensive planning of the bmad method, unless the user is already working through the implementation phase and just requests a 1 off things not already in the plan",,
bmm,anytime,Correct Course,CC,,_bmad/bmm/workflows/4-implementation/correct-course/workflow.yaml,bmad-bmm-correct-course,false,sm,bmad:story preparation:agent:sm,Bob,🏃 Scrum Master,Create Mode,Anytime: Navigate significant changes. May recommend start over update PRD redo architecture sprint planning or correct epics and stories,planning_artifacts,change proposal
bmm,anytime,Write Document,WD,,_bmad/bmm/agents/tech-writer/tech-writer.agent.yaml,,false,tech-writer,bmad:DITA:agent:tech-writer,Paige,📚 Technical Writer,,"Describe in detail what you want, and the agent will follow the documentation best practices defined in agent memory. Multi-turn conversation with subprocess for research/review.",project-knowledge,document
bmm,anytime,Update Standards,US,,_bmad/bmm/agents/tech-writer/tech-writer.agent.yaml,,false,tech-writer,bmad:DITA:agent:tech-writer,Paige,📚 Technical Writer,,Update agent memory documentation-standards.md with your specific preferences if you discover missing document conventions.,_bmad/_memory/tech-writer-sidecar,standards
bmm,anytime,Mermaid Generate,MG,,_bmad/bmm/agents/tech-writer/tech-writer.agent.yaml,,false,tech-writer,bmad:DITA:agent:tech-writer,Paige,📚 Technical Writer,,Create a Mermaid diagram based on user description. Will suggest diagram types if not specified.,planning_artifacts,mermaid diagram
bmm,anytime,Validate Document,VD,,_bmad/bmm/agents/tech-writer/tech-writer.agent.yaml,,false,tech-writer,bmad:DITA:agent:tech-writer,Paige,📚 Technical Writer,,Review the specified document against documentation standards and best practices. Returns specific actionable improvement suggestions organized by priority.,planning_artifacts,validation report
bmm,anytime,Explain Concept,EC,,_bmad/bmm/agents/tech-writer/tech-writer.agent.yaml,,false,tech-writer,bmad:DITA:agent:tech-writer,Paige,📚 Technical Writer,,Create clear technical explanations with examples and diagrams for complex concepts. Breaks down into digestible sections using task-oriented approach.,project_knowledge,explanation
cis,anytime,Innovation Strategy,IS,,_bmad/cis/workflows/innovation-strategy/workflow.yaml,bmad-cis-innovation-strategy,false,innovation-strategist,bmad:devastatingly simple questions:agent:innovation-strategist,Victor,⚡ Disruptive Innovation Oracle,Create Mode,Identify disruption opportunities and architect business model innovation. Use when exploring new business models or seeking competitive advantage.,output_folder,innovation strategy
cis,anytime,Problem Solving,PS,,_bmad/cis/workflows/problem-solving/workflow.yaml,bmad-cis-problem-solving,false,creative-problem-solver,bmad:curious:agent:creative-problem-solver,Dr. Quinn,🔬 Master Problem Solver,Create Mode,Apply systematic problem-solving methodologies to crack complex challenges. Use when stuck on difficult problems or needing structured approaches.,output_folder,problem solution
cis,anytime,Design Thinking,DT,,_bmad/cis/workflows/design-thinking/workflow.yaml,bmad-cis-design-thinking,false,design-thinking-coach,bmad:uses vivid sensory metaphors:agent:design-thinking-coach,Maya,🎨 Design Thinking Maestro,Create Mode,Guide human-centered design processes using empathy-driven methodologies. Use for user-centered design challenges or improving user experience.,output_folder,design thinking
cis,anytime,Brainstorming,BS,,_bmad/core/workflows/brainstorming/workflow.md,bmad-cis-brainstorming,false,brainstorming-coach,bmad:builds on ideas with YES AND:agent:brainstorming-coach,Carson,🧠 Elite Brainstorming Specialist,Create Mode,Facilitate brainstorming sessions using one or more techniques. Use early in ideation phase or when stuck generating ideas.,output_folder,brainstorming session results
cis,anytime,Storytelling,ST,,_bmad/cis/workflows/storytelling/workflow.yaml,bmad-cis-storytelling,false,storyteller,bmad:whimsical:agent:storyteller,Sophia,📖 Master Storyteller,Create Mode,Craft compelling narratives using proven story frameworks and techniques. Use when needing persuasive communication or story-driven content.,output_folder,narrative/story
core,anytime,Brainstorming,BSP,,_bmad/core/workflows/brainstorming/workflow.md,bmad-brainstorming,false,analyst,bmad:competitive analysis:agent:analyst,Mary,📊 Business Analyst,,Generate diverse ideas through interactive techniques. Use early in ideation phase or when stuck generating ideas.,{output_folder}/brainstorming/brainstorming-session-{{date}}.md,
core,anytime,Party Mode,PM,,_bmad/core/workflows/party-mode/workflow.md,bmad-party-mode,false,party-mode facilitator,,,,,Orchestrate multi-agent discussions. Use when you need multiple agent perspectives or want agents to collaborate.,,
core,anytime,bmad-help,BH,,_bmad/core/tasks/help.md,bmad-help,false,,,,,,Get unstuck by showing what workflow steps come next or answering BMad Method questions.,,
core,anytime,Index Docs,ID,,_bmad/core/tasks/index-docs.xml,bmad-index-docs,false,,,,,,Create lightweight index for quick LLM scanning. Use when LLM needs to understand available docs without loading everything.,,
core,anytime,Shard Document,SD,,_bmad/core/tasks/shard-doc.xml,bmad-shard-doc,false,,,,,,Split large documents into smaller files by sections. Use when doc becomes too large (>500 lines) to manage effectively.,,
core,anytime,Editorial Review - Prose,EP,,_bmad/core/tasks/editorial-review-prose.xml,bmad-editorial-review-prose,false,,,,,,"Review prose for clarity, tone, and communication issues. Use after drafting to polish written content.",report located with target document,three-column markdown table with suggested fixes
core,anytime,Editorial Review - Structure,ES,,_bmad/core/tasks/editorial-review-structure.xml,bmad-editorial-review-structure,false,,,,,,"Propose cuts, reorganization, and simplification while preserving comprehension. Use when doc produced from multiple subprocesses or needs structural improvement.",report located with target document,
core,anytime,Adversarial Review (General),AR,,_bmad/core/tasks/review-adversarial-general.xml,bmad-review-adversarial-general,false,,,,,,"Review content critically to find issues and weaknesses. Use for quality assurance or before finalizing deliverables. Code Review in other modules run this automatically, but its useful also for document reviews",,
core,anytime,Edge Case Hunter Review,ECH,,_bmad/core/tasks/review-edge-case-hunter.xml,bmad-review-edge-case-hunter,false,,,,,,"Walk every branching path and boundary condition in code, report only unhandled edge cases. Use alongside adversarial review for orthogonal coverage - method-driven not attitude-driven.",,
tea,0-learning,Teach Me Testing,TMT,10,_bmad/tea/workflows/testarch/teach-me-testing/workflow.md,bmad-tea-teach-me-testing,false,tea,bmad:backend services:agent:tea,Murat,🧪 Master Test Architect and Quality Advisor,Create Mode,Teach testing fundamentals through 7 sessions (TEA Academy),test_artifacts,progress file|session notes|certificate
tea,3-solutioning,Test Design,TD,10,_bmad/tea/workflows/testarch/test-design/workflow.yaml,bmad-tea-testarch-test-design,false,tea,bmad:backend services:agent:tea,Murat,🧪 Master Test Architect and Quality Advisor,Create Mode,Risk-based test planning,test_artifacts,test design document
tea,3-solutioning,Test Framework,TF,20,_bmad/tea/workflows/testarch/framework/workflow.yaml,bmad-tea-testarch-framework,false,tea,bmad:backend services:agent:tea,Murat,🧪 Master Test Architect and Quality Advisor,Create Mode,Initialize production-ready test framework,test_artifacts,framework scaffold
tea,3-solutioning,CI Setup,CI,30,_bmad/tea/workflows/testarch/ci/workflow.yaml,bmad-tea-testarch-ci,false,tea,bmad:backend services:agent:tea,Murat,🧪 Master Test Architect and Quality Advisor,Create Mode,Configure CI/CD quality pipeline,test_artifacts,ci config
tea,4-implementation,ATDD,AT,10,_bmad/tea/workflows/testarch/atdd/workflow.yaml,bmad-tea-testarch-atdd,false,tea,bmad:backend services:agent:tea,Murat,🧪 Master Test Architect and Quality Advisor,Create Mode,Generate failing tests (TDD red phase),test_artifacts,atdd tests
tea,4-implementation,Test Automation,TA,20,_bmad/tea/workflows/testarch/automate/workflow.yaml,bmad-tea-testarch-automate,false,tea,bmad:backend services:agent:tea,Murat,🧪 Master Test Architect and Quality Advisor,Create Mode,Expand test coverage,test_artifacts,test suite
tea,4-implementation,Test Review,RV,30,_bmad/tea/workflows/testarch/test-review/workflow.yaml,bmad-tea-testarch-test-review,false,tea,bmad:backend services:agent:tea,Murat,🧪 Master Test Architect and Quality Advisor,Validate Mode,Quality audit (0-100 scoring),test_artifacts,review report
tea,4-implementation,NFR Assessment,NR,40,_bmad/tea/workflows/testarch/nfr-assess/workflow.yaml,bmad-tea-testarch-nfr,false,tea,bmad:backend services:agent:tea,Murat,🧪 Master Test Architect and Quality Advisor,Create Mode,Non-functional requirements,test_artifacts,nfr report
tea,4-implementation,Traceability,TR,50,_bmad/tea/workflows/testarch/trace/workflow.yaml,bmad-tea-testarch-trace,false,tea,bmad:backend services:agent:tea,Murat,🧪 Master Test Architect and Quality Advisor,Create Mode,Coverage traceability and gate,test_artifacts,traceability matrix|gate decision

]]></file>
<file id="b20baf87" path="_bmad/_config/files-manifest.csv" label="FILE"><![CDATA[

type,name,module,path,hash
"csv","agent-manifest","_config","_config/agent-manifest.csv","b1c76fa7519f238274a47a8ceb25bbfc2f1a3418e2d381fcd0ebea9dcf55027b"
"csv","task-manifest","_config","_config/task-manifest.csv","edf1dc84302aa351ce62f4c58d102fd67f2267c0a329ae4e5092df42aa14220c"
"csv","workflow-manifest","_config","_config/workflow-manifest.csv","b3ae62ac77887f95ce067b2a591a430c16087c76c99639ac97a632c268e1f63e"
"yaml","manifest","_config","_config/manifest.yaml","a5ec11ebcd7371886a9d21aebdef4bba2dbd0e6a53762957ed6b4c7d1f9c4541"
"md","documentation-standards","_memory","_memory/tech-writer-sidecar/documentation-standards.md","b046192ee42fcd1a3e9b2ae6911a0db38510323d072c8d75bad0594f943039e4"
"md","stories-told","_memory","_memory/storyteller-sidecar/stories-told.md","47ee9e599595f3d9daf96d47bcdacf55eeb69fbe5572f6b08a8f48c543bc62de"
"md","story-preferences","_memory","_memory/storyteller-sidecar/story-preferences.md","b70dbb5baf3603fdac12365ef24610685cba3b68a9bc41b07bbe455cbdcc0178"
"yaml","config","_memory","_memory/config.yaml","ede3012ae657b71de86bfa780a6f2f42082981963a9f248fd403dbc73a0ef620"
"csv","common-workflow-tools","bmb","bmb/workflows/workflow/data/common-workflow-tools.csv","e59bc1d76db128ff04c53fab4b4f840f486f9804ed0d7fb7af1f62c15c2eb86a"
"csv","communication-presets","bmb","bmb/workflows/agent/data/communication-presets.csv","1297e9277f05254ee20c463e6071df3811dfb8fe5d1183ce07ce9b092cb3fd16"
"csv","module-help","bmb","bmb/module-help.csv","f25e9885efd06c5f7a51466c65f6016c77f5767e924a644508877bcb3575cb88"
"md","agent-architecture","bmb","bmb/workflows/agent/data/agent-architecture.md","4e7108717cb0da3e4b35680bcea350731f69497d60f09e8db036008eb16b8266"
"md","agent-architecture","bmb","bmb/workflows/module/data/agent-architecture.md","292bb887f2b6bfbe7536ae2a3d936c51bce8f55680298ccc5620ae38081017ca"
"md","agent-compilation","bmb","bmb/workflows/agent/data/agent-compilation.md","d0722de16e620caf44843fb5e02324fd1f6a1e325c4957bcf596b9652c95b15f"
"md","agent-menu-patterns","bmb","bmb/workflows/agent/data/agent-menu-patterns.md","df5298d5cccd946fc36cf79ee0a21f9680d878a50cb9de7eecc49a250d6922e2"
"md","agent-metadata","bmb","bmb/workflows/agent/data/agent-metadata.md","b49dab109782f56bb915744f67af36abdef810735665a13405ca327607b06e30"
"md","agent-plan.template","bmb","bmb/workflows/agent/templates/agent-plan.template.md","81e79756fb4c368c568ba05efcd276d1d52a111163827439733554f4d94e3094"
"md","agent-spec-template","bmb","bmb/workflows/module/data/agent-spec-template.md","ff68be471450daf91dc6d3c2d96ee2a8638acd7f26589abf4c328d8df7547677"
"md","agent-template","bmb","bmb/workflows/agent/templates/agent-template.md","bfaf5b7675d94279734fde32ea43a7f2383b045a027c74f426a3ea43b5f9baee"
"md","agent-validation","bmb","bmb/workflows/agent/data/agent-validation.md","df9aa540d62084b617200c312c751ee920b492afbc4aea3f54cebc4964f7b6ac"
"md","architect","bmb","bmb/workflows/agent/data/reference/module-examples/architect.md","fd9d3138eb02f9a2a770a90cad57a72827965deb9d5944a2fea22af03a95e0ab"
"md","architecture","bmb","bmb/workflows/workflow/data/architecture.md","94f6ff8b32bc819ca9f9f2f43c50562fd1ed25d82ffcb0e33795f7e36243626b"
"md","brainstorm-context","bmb","bmb/workflows/agent/data/brainstorm-context.md","f2685504ff1c781fc1829f9550d9c2f3f0fde4bc9f451515ce653abef0366b76"
"md","brief-template","bmb","bmb/workflows/module/templates/brief-template.md","9b3a5aab977cd189317321b92d512110fa13993a27447b25143fff14b24f6f84"
"md","critical-actions","bmb","bmb/workflows/agent/data/critical-actions.md","86dc92ca4fdd8ab8d1783da4c74ba03eb0ecbda105f4af9fe15decd70c871f4e"
"md","csv-data-file-standards","bmb","bmb/workflows/workflow/data/csv-data-file-standards.md","3efef22ebe70e0c89e34a5ab74cd51d89b56ac4404279e85bc5c1606e258ae79"
"md","e-01-load-existing","bmb","bmb/workflows/agent/steps-e/e-01-load-existing.md","e672dacda200987c944ac8aee8a8d4b25c30832eb52555ffb55235a98dacec19"
"md","e-02-discover-edits","bmb","bmb/workflows/agent/steps-e/e-02-discover-edits.md","8f902e4c5e0c9c54e764bbc4aadde79302bd069c6115f07ca3d8d3e756a26ef9"
"md","e-03-placeholder","bmb","bmb/workflows/agent/steps-e/e-03-placeholder.md","4076b77b471144f7bd58454a2652bed9a11a964bb249df95272b73590757a95e"
"md","e-04-sidecar-metadata","bmb","bmb/workflows/agent/steps-e/e-04-sidecar-metadata.md","170932df21c468495c1295da4122d2a730555ab8ef135a23884c5cd4b23463a8"
"md","e-05-persona","bmb","bmb/workflows/agent/steps-e/e-05-persona.md","93742cd56f05ff1eb25cb3357908e5e3d65c253f05260f6cf6680eea8e510a21"
"md","e-06-commands-menu","bmb","bmb/workflows/agent/steps-e/e-06-commands-menu.md","bcaaf0ed3a3ac1ee57393e4c5fc138ca971741019ccc8edc3fdec13bf755304c"
"md","e-07-activation","bmb","bmb/workflows/agent/steps-e/e-07-activation.md","287eade210793c82fa99f47871fa36666af2406d0b8710a05c061d8c4d11dbb1"
"md","e-08-edit-agent","bmb","bmb/workflows/agent/steps-e/e-08-edit-agent.md","1f7d857f21bbeb79fce3f2141c3627269c58a223afd90c301fec1d4087b083a4"
"md","e-09-celebrate","bmb","bmb/workflows/agent/steps-e/e-09-celebrate.md","20f273e2c55d5d38d49b2161bc3303a003126af61799e13a1f5e398d6578889f"
"md","frontmatter-standards","bmb","bmb/workflows/workflow/data/frontmatter-standards.md","95c756d4dd8eebca708bd03983b8c95374babbeedd9963a7dd89908be0bc0c7a"
"md","input-discovery-standards","bmb","bmb/workflows/workflow/data/input-discovery-standards.md","6e71ec3582a13d1836b12fcca40a50f2d8c30b4bb37f78f622c540054403cb7c"
"md","intent-vs-prescriptive-spectrum","bmb","bmb/workflows/workflow/data/intent-vs-prescriptive-spectrum.md","d5e10863d2ba52e0d0cfdc67cdfcb358bc1bbfa900c0a47ce1383cff81c14e46"
"md","menu-handling-standards","bmb","bmb/workflows/workflow/data/menu-handling-standards.md","f664abbedbb71e712486c2b03a5131b05b5f89ba6557d2c35f0b123512153673"
"md","minimal-output-template","bmb","bmb/workflows/workflow/templates/minimal-output-template.md","ff4c222f36c3589529eb3b1df80f914b64de76f74022332e555fbf2402bf2a7f"
"md","module-help-generate","bmb","bmb/workflows/module/module-help-generate.md","4c2099aacd4fc923ab7b2f4696e786d34cc2b55a0e86bd3ead757743a02a3e02"
"md","module-standards","bmb","bmb/workflows/module/data/module-standards.md","f3f008189dcb85978b1ca43ec7396d3e7587b2ec16d513297e568a9df980ad46"
"md","module-yaml-conventions","bmb","bmb/workflows/module/data/module-yaml-conventions.md","61b0f880aa99920f25d95b3ce333fa384f91d2eb2ed6d5179ba5b7524d9e625c"
"md","output-format-standards","bmb","bmb/workflows/workflow/data/output-format-standards.md","8975765f4cf43478685529d559ad95691a677c85ebd1af42088f02dd83d448a3"
"md","persona-properties","bmb","bmb/workflows/agent/data/persona-properties.md","d71a2a855d3f12f742d0b1ebcd6a1bb99550d1b22f56c3c5e038a53d13e6970d"
"md","principles-crafting","bmb","bmb/workflows/agent/data/principles-crafting.md","33e40c3aa10b27e7a33277b90c294dbcdc1df5b6c4115ebf3c18ff47943ce65f"
"md","step-00-conversion","bmb","bmb/workflows/workflow/steps-c/step-00-conversion.md","f1cff1e6117c249a845dcbe6361d89a356a2d9c41b1700c455dc4af667a84016"
"md","step-01-brainstorm","bmb","bmb/workflows/agent/steps-c/step-01-brainstorm.md","8b56200dc67a43d3eb2afff9d329aa3ed07beeeb362b00b3b521a4de1f9a2b34"
"md","step-01-discovery","bmb","bmb/workflows/workflow/steps-c/step-01-discovery.md","14bafd883635c3606ecf63c82ea126b5bdad86980eee334e157dae5de04811c2"
"md","step-01-init-continuable-template","bmb","bmb/workflows/workflow/templates/step-01-init-continuable-template.md","f211cf173c79b773a54612ad705e4fbbc0c936a5d4671a450602e8f73cab1183"
"md","step-01-load-brief","bmb","bmb/workflows/module/steps-c/step-01-load-brief.md","d11ae0c2fe17d2b8427ef5b96c06c2f870e6bf3a204f2eafebce8354f850bc90"
"md","step-01-load-target","bmb","bmb/workflows/module/steps-e/step-01-load-target.md","26aef55b965315443a35e6a0d55c9ce003c2bd9a0996bc209e638680a6969dd5"
"md","step-01-load-target","bmb","bmb/workflows/module/steps-v/step-01-load-target.md","27fba2bf4be60ce6d4d00b491deb3bf8ae2af9c078d97cb4629a14268a1b45e1"
"md","step-01-validate","bmb","bmb/workflows/workflow/steps-v/step-01-validate.md","7062165cc403137878ec484a8a70215288d2b611a8b2153f45f814d3d1a9d58a"
"md","step-01-validate-max-mode","bmb","bmb/workflows/workflow/steps-v/step-01-validate-max-mode.md","cf2de5888a6b3e025912769dc417d707391bb5885c973ed6359d16666540c313"
"md","step-01-welcome","bmb","bmb/workflows/module/steps-b/step-01-welcome.md","360f177df40eb103c3a39118fc0d0e38c4bbe5e042555dc22ec75f96888bedcd"
"md","step-01b-continuation","bmb","bmb/workflows/workflow/steps-c/step-01b-continuation.md","26b8ca474a892000d5b9f87bf9defc85af381fb3ae27b4b8aa8e2aafedebcd8d"
"md","step-01b-continue","bmb","bmb/workflows/module/steps-c/step-01b-continue.md","9909a6a213dea8e35f730713d947baf068e30d734e8209389b727baff1f339e6"
"md","step-01b-structure","bmb","bmb/workflows/workflow/steps-v/step-01b-structure.md","1a5c4344f777331ebf3f26f0f96b0d384ced6d3ad1e261041bd0942b328a62b4"
"md","step-02-classification","bmb","bmb/workflows/workflow/steps-c/step-02-classification.md","d31e2b451af0dcdd3d6c6695143200f0b40c3e8725ddf09849810f6984b76286"
"md","step-02-discovery","bmb","bmb/workflows/agent/steps-c/step-02-discovery.md","52aadeb5dab8d4c0b43bdfb68bf7b32ea03ead412826c20f5c0c1afcb9c87d42"
"md","step-02-file-structure","bmb","bmb/workflows/module/steps-v/step-02-file-structure.md","db23a0e73ed9e7885b6e629a7b631db142920857ba3a8e7db4c6de8339be0514"
"md","step-02-frontmatter-validation","bmb","bmb/workflows/workflow/steps-v/step-02-frontmatter-validation.md","86fede3dd8b992eeeeb962bd217dcb9d002aad2def3acbf0b8f3ea4f089bf1d4"
"md","step-02-select-edit","bmb","bmb/workflows/module/steps-e/step-02-select-edit.md","54c0825ec764e38481a4edb1524a2505dc5eff079a844ab4384eb6d264511680"
"md","step-02-spark","bmb","bmb/workflows/module/steps-b/step-02-spark.md","675a83d6c257439ac1c6a508358ff09f532075bcb4f97c1037f626324f431e34"
"md","step-02-structure","bmb","bmb/workflows/module/steps-c/step-02-structure.md","a92a42777e4aa90ae90f3a4cde49a4e46dc6d390d5f8b0e6c25cbd0749534626"
"md","step-02b-path-violations","bmb","bmb/workflows/workflow/steps-v/step-02b-path-violations.md","34da677fd6b3bcbc54ffa8fba8c690a21e0189000aa30331c586438ad397c977"
"md","step-03-apply-edit","bmb","bmb/workflows/module/steps-e/step-03-apply-edit.md","4cc07b6468e7e8ce8b941e5c74d132f5657caa58086586cc80eebd223a4114fd"
"md","step-03-config","bmb","bmb/workflows/module/steps-c/step-03-config.md","ca89836174c4b76051d43457aa0217295d5bf4eb2800c03ed2d29832d09cd369"
"md","step-03-menu-validation","bmb","bmb/workflows/workflow/steps-v/step-03-menu-validation.md","b484b7e112339facc41edee5631a513c89f4f5d90c2303e9457deb96ce3287af"
"md","step-03-module-type","bmb","bmb/workflows/module/steps-b/step-03-module-type.md","0e41528e462d831ff005fdadce5a38351ebc6e95e272b79a43615c322e884e09"
"md","step-03-module-yaml","bmb","bmb/workflows/module/steps-v/step-03-module-yaml.md","3a69cb73ae898484401c3ffbd203fb3ab74d5678933ae460d2bcc2786e876493"
"md","step-03-requirements","bmb","bmb/workflows/workflow/steps-c/step-03-requirements.md","4954b42e344ce6f728fc3dc8df3ad5eeac0ce6d73fb08c8ff09d762e9364fd71"
"md","step-03-sidecar-metadata","bmb","bmb/workflows/agent/steps-c/step-03-sidecar-metadata.md","ecd17fb960120f8709d0b1f95c265a6275a4672db9b02458cf9df7b6d2a6681e"
"md","step-04-agent-specs","bmb","bmb/workflows/module/steps-v/step-04-agent-specs.md","a8d5eac1f5e8693c370bdb774c926a45cf5afde8d94e6996862664cdee444849"
"md","step-04-agents","bmb","bmb/workflows/module/steps-c/step-04-agents.md","22b913e38f32f9bf388f43290a17726318986d559b42b188f26bf97a20e651d3"
"md","step-04-persona","bmb","bmb/workflows/agent/steps-c/step-04-persona.md","cd8b5845b987eeff0cdf16a913e2de439e32e927a1b4f977fee238e56c02d9a4"
"md","step-04-review","bmb","bmb/workflows/module/steps-e/step-04-review.md","9b86a5d09668674accd03cb47cd6c437c2117ee23562bb2bcea8ddc6979eefeb"
"md","step-04-step-type-validation","bmb","bmb/workflows/workflow/steps-v/step-04-step-type-validation.md","3a923bcad87fc74036fdefa8f42d360b8d02b678f9077aedd18654e94d966f7a"
"md","step-04-tools","bmb","bmb/workflows/workflow/steps-c/step-04-tools.md","623adb4ca3a6e47a27e78ebc55ea45b89866ca60e04aa05f9907f6bdf8a9f57c"
"md","step-04-vision","bmb","bmb/workflows/module/steps-b/step-04-vision.md","cac4ca0fe32092801503f906fdfa868e65ba0490877daeb23a274571135ecddc"
"md","step-05-commands-menu","bmb","bmb/workflows/agent/steps-c/step-05-commands-menu.md","daf554f3cedfcb26381bec533b00cfbb73cc688dcaa72167eba852cead8fa861"
"md","step-05-confirm","bmb","bmb/workflows/module/steps-e/step-05-confirm.md","1abeb25cd94e0396642e0ffd4d68d1b21350c51f2eee86bf403fb6f406a22408"
"md","step-05-identity","bmb","bmb/workflows/module/steps-b/step-05-identity.md","c81aa920cf83f04a51585675b2b09d756d7c5bb9e851ccea66e25d76aeaf3cff"
"md","step-05-output-format-validation","bmb","bmb/workflows/workflow/steps-v/step-05-output-format-validation.md","824a0bea33d14e5694f6b58504eb655af26ccd3d1001a40179861146038d77e6"
"md","step-05-plan-review","bmb","bmb/workflows/workflow/steps-c/step-05-plan-review.md","852bb996af5ccdb7df158106ba7c98698b21f667b5fd1c3256c1929839b73e38"
"md","step-05-workflow-specs","bmb","bmb/workflows/module/steps-v/step-05-workflow-specs.md","870c35fdc1e486b67fc21876964c28db1286e6e63acf83ec35f27ec274d8e868"
"md","step-05-workflows","bmb","bmb/workflows/module/steps-c/step-05-workflows.md","f924f8d79fc3dfc85170b321dd08b414cbb09eadaaf4f07e55fe3b9b60049026"
"md","step-06-activation","bmb","bmb/workflows/agent/steps-c/step-06-activation.md","cd892bde609db408cdd73ef503eb9aede24ec575e161ab43b40f84001cd6c182"
"md","step-06-design","bmb","bmb/workflows/workflow/steps-c/step-06-design.md","9873ef3c4ac9f9dc68e552e626a7c20091eba1c9d19f1fa76b2ba0738d0bc082"
"md","step-06-docs","bmb","bmb/workflows/module/steps-c/step-06-docs.md","5d05cf19d95dfc3f40d1051612a4a97e8e0fb161e6892cc886df5b1bcbef8888"
"md","step-06-documentation","bmb","bmb/workflows/module/steps-v/step-06-documentation.md","8b747c69aeda2222c980c0341fceaa7596e819420eead2e1cee634b17ddb4803"
"md","step-06-users","bmb","bmb/workflows/module/steps-b/step-06-users.md","9e96d114253f41272cb022879db49487e35c81d21163b4358a3f287d8714aa60"
"md","step-06-validation-design-check","bmb","bmb/workflows/workflow/steps-v/step-06-validation-design-check.md","8eb78dc10848d8e33a6c84fee38210fef8e4431aa25c318d596d25d69f9755f5"
"md","step-07-build-agent","bmb","bmb/workflows/agent/steps-c/step-07-build-agent.md","2211519285b1fa8b3f8c6407d9f15121473b15ca273ad174377351312c10f4c9"
"md","step-07-complete","bmb","bmb/workflows/module/steps-c/step-07-complete.md","af457b4579d6e8396b7ade272b04453df3422ca7a1db6bdc0e77097b6ad5804b"
"md","step-07-foundation","bmb","bmb/workflows/workflow/steps-c/step-07-foundation.md","da4a6efc428c003dc9576c243111e2b29843608adb864105d5e130cae18498eb"
"md","step-07-installation","bmb","bmb/workflows/module/steps-v/step-07-installation.md","06966e9496de39e7a6204c61c14a35dd0298af1485226b9f8eaac06e4a816633"
"md","step-07-instruction-style-check","bmb","bmb/workflows/workflow/steps-v/step-07-instruction-style-check.md","b9ce0212ea49b3dfdb7204f9cfa5c59b25f4e314d2ab9cc27a95c1f432faa2f9"
"md","step-07-value","bmb","bmb/workflows/module/steps-b/step-07-value.md","8a1fadb590730bbcb33454974ffad289d6f61a93c1d317ee883f60311c003f2e"
"md","step-08-agents","bmb","bmb/workflows/module/steps-b/step-08-agents.md","891f06eb89c9bbf687286252a4dda6cb19b0cc0b084f4b919aab5d7518fa9c77"
"md","step-08-build-step-01","bmb","bmb/workflows/workflow/steps-c/step-08-build-step-01.md","cbdea1291bd9f2fe5d112ceb61caa05a81b00566997e4c5f7fc6d32ec4666267"
"md","step-08-celebrate","bmb","bmb/workflows/agent/steps-c/step-08-celebrate.md","540fc2dc69aa402ffd7222ff37379100497e188ebec42616240b8c2b7d4ac493"
"md","step-08-collaborative-experience-check","bmb","bmb/workflows/workflow/steps-v/step-08-collaborative-experience-check.md","5cffb645b0175b823f9607530625d1903920532f95e0d92b71fb233043dc4f4e"
"md","step-08-report","bmb","bmb/workflows/module/steps-v/step-08-report.md","8e1d295dc29b6dab5fe0ec81f51b614cb8a62b849fe10895093685b3164fe2bd"
"md","step-08b-subprocess-optimization","bmb","bmb/workflows/workflow/steps-v/step-08b-subprocess-optimization.md","1934aa38ebabab0ddf2777cacddd96f37554dcda8f80812b87564a4b64925c36"
"md","step-09-build-next-step","bmb","bmb/workflows/workflow/steps-c/step-09-build-next-step.md","e814302a0713f910baadf6eda45696cd0ef632c4db38e32864f876fb2468cb38"
"md","step-09-cohesive-review","bmb","bmb/workflows/workflow/steps-v/step-09-cohesive-review.md","77e00f46ae55bb95ebeacc6380871befb2f60844f547b260eca08e77cb1e8618"
"md","step-09-workflows","bmb","bmb/workflows/module/steps-b/step-09-workflows.md","ce099465badf171f4451ebc6064de306e85807875f747bf5f4e3542ec93961e8"
"md","step-10-confirmation","bmb","bmb/workflows/workflow/steps-c/step-10-confirmation.md","17826ad707f57f19061cb227dc8234b2338175e9ef52a5ba4acde9c3be5f7ab6"
"md","step-10-report-complete","bmb","bmb/workflows/workflow/steps-v/step-10-report-complete.md","901274400fa20398593f392b2ec17da88045b09c6f36f29e71e0d4219d86acf0"
"md","step-10-tools","bmb","bmb/workflows/module/steps-b/step-10-tools.md","c66a53c8b35261e511663ada1adfc62486a7d8183a51f348e28ee74fb5cdb8bf"
"md","step-11-completion","bmb","bmb/workflows/workflow/steps-c/step-11-completion.md","fa84481cdadc7405628c44b18e231b5ced89dcf1105cc5ec7b0d57c3b085f193"
"md","step-11-plan-validation","bmb","bmb/workflows/workflow/steps-v/step-11-plan-validation.md","33421d9536fee94228d57adceddff16fe3ef2fb39e97402db855b449c74e1908"
"md","step-11-scenarios","bmb","bmb/workflows/module/steps-b/step-11-scenarios.md","27115e07abbee27dc44ddd519586a1f00e3069c1fda7998e726ca966d0774c9b"
"md","step-12-creative","bmb","bmb/workflows/module/steps-b/step-12-creative.md","f573cda16421dbf02433efcbc36f044a836badccbe2d112de0e72a60f9627043"
"md","step-13-review","bmb","bmb/workflows/module/steps-b/step-13-review.md","7fbe0bfad983bee2be1a658e9d761ec814b81609dcd297e6ef5cce52221f68ce"
"md","step-14-finalize","bmb","bmb/workflows/module/steps-b/step-14-finalize.md","6ec52af56a4158156c900efa3438b3e6c66d9483ef5406943a47308a91512f4a"
"md","step-1b-template","bmb","bmb/workflows/workflow/templates/step-1b-template.md","1728f01e00cad05b727d292dd9f163c3d94e70cff3243c67f958aa412bffc5aa"
"md","step-e-01-assess-workflow","bmb","bmb/workflows/workflow/steps-e/step-e-01-assess-workflow.md","d35285d365240ef997b47c262715326293a47835f84d71cbe20f8084ef62ad67"
"md","step-e-02-discover-edits","bmb","bmb/workflows/workflow/steps-e/step-e-02-discover-edits.md","7066e66d5c16b5c853d60bb53a0ff9396236d0af3a7ebecbab2cdfbc329f4c84"
"md","step-e-03-fix-validation","bmb","bmb/workflows/workflow/steps-e/step-e-03-fix-validation.md","c62da8d8a497865d163774ef99c961d0b465b8863684dd6ab4e2b9dee76acf49"
"md","step-e-04-direct-edit","bmb","bmb/workflows/workflow/steps-e/step-e-04-direct-edit.md","9d5e13c0cc503c17d0977f1667d00b82b4191d875a269e04f6fb956c5cc0f27a"
"md","step-e-05-apply-edit","bmb","bmb/workflows/workflow/steps-e/step-e-05-apply-edit.md","c8e2613800416342214bc402433a4163afb26cd7561a9cac31e3e6bfe2a254aa"
"md","step-e-06-validate-after","bmb","bmb/workflows/workflow/steps-e/step-e-06-validate-after.md","130794b7a744775691256fe6b849e94a9764b8c22d775c9dce423c311145622f"
"md","step-e-07-complete","bmb","bmb/workflows/workflow/steps-e/step-e-07-complete.md","3c3b50718bcfc29a4db981bcf2c6cb4ff81598fc0ebe2f50ef36e4d0f7301c0f"
"md","step-file-rules","bmb","bmb/workflows/workflow/data/step-file-rules.md","bfc096df223992a8568e2e1a7b03bb3cb5fab26154c73782d2e94edd6fdaa4fd"
"md","step-template","bmb","bmb/workflows/workflow/templates/step-template.md","2bc3e860d0b59397c651137a020d0218982031df3eddd22f1bbc9bc0c3797ce1"
"md","step-type-patterns","bmb","bmb/workflows/workflow/data/step-type-patterns.md","5bf33d70160ae8b8914c4de64c8bb0bad6e2788883f613539711819c3cd8fc2b"
"md","subprocess-optimization-patterns","bmb","bmb/workflows/workflow/data/subprocess-optimization-patterns.md","7ab53a8001bbe9e81c76173dc7fc5cc53a7fb864d8ff69626b6e6cfeadfdc7e6"
"md","trimodal-workflow-structure","bmb","bmb/workflows/workflow/data/trimodal-workflow-structure.md","7908071a7e6962f9db23890b7f832b095064ca91eec2642273dbf7d62f0e4f27"
"md","understanding-agent-types","bmb","bmb/workflows/agent/data/understanding-agent-types.md","dc8255165a5d4409cb49462838f03321e03862857440c4f3f3822bb7d05d0002"
"md","v-01-load-review","bmb","bmb/workflows/agent/steps-v/v-01-load-review.md","eb6bbf20785bdca98336f6b8bfc893df6775551b13c01d67661d6e0577a7155e"
"md","v-02a-validate-metadata","bmb","bmb/workflows/agent/steps-v/v-02a-validate-metadata.md","3669dcb0235e35bd843454e2cc04ddaca8f9517c7617d79419196190044a0652"
"md","v-02b-validate-persona","bmb","bmb/workflows/agent/steps-v/v-02b-validate-persona.md","144ef430d5f1dc5af3a8a51c9c2b83cdd95ef5aefe0d406f7b20064c97ada4ba"
"md","v-02c-validate-menu","bmb","bmb/workflows/agent/steps-v/v-02c-validate-menu.md","4e8b2158dbce6d7ff3e7208da688bd74521926fbdec72933fce52f4301c112e5"
"md","v-02d-validate-structure","bmb","bmb/workflows/agent/steps-v/v-02d-validate-structure.md","e47d9af9855a276d5c7b93cdfd3ae25c8a6f9f28b3f3422284e867c79b05c433"
"md","v-02e-validate-sidecar","bmb","bmb/workflows/agent/steps-v/v-02e-validate-sidecar.md","51c675b7ab4ff44e52d147117002ae3497a97a47bf9fdf9da8edb659889bb38e"
"md","v-03-summary","bmb","bmb/workflows/agent/steps-v/v-03-summary.md","6167d149c018ef818508595b04c47ecd9e3c08569751932d71d3f9ac0550b34b"
"md","workflow-chaining-standards","bmb","bmb/workflows/workflow/data/workflow-chaining-standards.md","358099d64396ee13c6525969ee4d9ee29f4ad8adc0077ed67c3376764a15f9ce"
"md","workflow-create-agent","bmb","bmb/workflows/agent/workflow-create-agent.md","78d5216906af8725c6db58a7841af2bc0a9a616bcaf702bdaac552b9d83e335c"
"md","workflow-create-module","bmb","bmb/workflows/module/workflow-create-module.md","b30332d5ba94b8291e0bffd4ecf2376ee9d48453665ac120e8da2d7117e62945"
"md","workflow-create-module-brief","bmb","bmb/workflows/module/workflow-create-module-brief.md","dd6048358b4984308657a815a30838e04d71c0f2f0f50e7b4e8364bd7213c3f3"
"md","workflow-create-workflow","bmb","bmb/workflows/workflow/workflow-create-workflow.md","f6a8e93c9aa10e60c7971f75c53f0424cdff075fdde9f989138baa20337384ce"
"md","workflow-edit-agent","bmb","bmb/workflows/agent/workflow-edit-agent.md","5acab6518e762014be75268526e6a5582e23fb156f8986b4efb65e7289e73c93"
"md","workflow-edit-module","bmb","bmb/workflows/module/workflow-edit-module.md","673df9ccd0f761798cd883ba0ed8bbad4b8551d8635c75a1554f6038e7dede35"
"md","workflow-edit-workflow","bmb","bmb/workflows/workflow/workflow-edit-workflow.md","54755d0adbc8250ab153c3078b173770efdf1759d2f79d63b61a99990fe2d8e1"
"md","workflow-examples","bmb","bmb/workflows/workflow/data/workflow-examples.md","e48cbf37b50cfe15bde688266dba0e23591d531f232bdca8094fd421d37752c3"
"md","workflow-rework-workflow","bmb","bmb/workflows/workflow/workflow-rework-workflow.md","647354f6647188ba4c58917a98de9c1051a12c5d8b9dc6ecbabe2eda00ba4f0b"
"md","workflow-spec-template","bmb","bmb/workflows/module/templates/workflow-spec-template.md","5a3a958180e2ef0803b14237d8e225f632476fc7a144ba2aa7e9866c1a30eddd"
"md","workflow-template","bmb","bmb/workflows/workflow/templates/workflow-template.md","69b5725f58a76297f151ffc4cb1629fb7b33829e5e1f365f4cf0004d48b5082c"
"md","workflow-type-criteria","bmb","bmb/workflows/workflow/data/workflow-type-criteria.md","14b10793d4c01605c6f509b27e97cceb8c0c4f2c3cddc28404b844c04c4413d2"
"md","workflow-validate-agent","bmb","bmb/workflows/agent/workflow-validate-agent.md","b58223afbf53fdbc52b5a85ea23bd65498e44d3b6b7e2268e3b3ad8eaced34d5"
"md","workflow-validate-max-parallel-workflow","bmb","bmb/workflows/workflow/workflow-validate-max-parallel-workflow.md","3706b9ea43ee7308d227b2f18e3196626f545df552c134056773bf431f43a7b4"
"md","workflow-validate-module","bmb","bmb/workflows/module/workflow-validate-module.md","78b71d8a816067898e9a92596f3d2f66d4f36dad2ef7fc076894077532715fe4"
"md","workflow-validate-workflow","bmb","bmb/workflows/workflow/workflow-validate-workflow.md","40f34df97c9b2e23be656f3233cea7c5ff14def514a4d7735cd623f0887276d4"
"yaml","config","bmb","bmb/config.yaml","52ef6b0824fbadb0212b4276df47011d751e54f2932c9ecb93c88c7eb2019715"
"csv","default-party","bmm","bmm/teams/default-party.csv","5af107a5b9e9092aeb81bd8c8b9bbe7003afb7bc500e64d56da7cc27ae0c4a6e"
"csv","documentation-requirements","bmm","bmm/workflows/document-project/documentation-requirements.csv","d1253b99e88250f2130516b56027ed706e643bfec3d99316727a4c6ec65c6c1d"
"csv","domain-complexity","bmm","bmm/workflows/2-plan-workflows/create-prd/data/domain-complexity.csv","f775f09fb4dc1b9214ca22db4a3994ce53343d976d7f6e5384949835db6d2770"
"csv","domain-complexity","bmm","bmm/workflows/3-solutioning/create-architecture/data/domain-complexity.csv","3dc34ed39f1fc79a51f7b8fc92087edb7cd85c4393a891d220f2e8dd5a101c70"
"csv","module-help","bmm","bmm/module-help.csv","f33b06127908f62ec65645e973392350904af703f90a7361f7f960474a9b7e0a"
"csv","project-types","bmm","bmm/workflows/2-plan-workflows/create-prd/data/project-types.csv","7a01d336e940fb7a59ff450064fd1194cdedda316370d939264a0a0adcc0aca3"
"csv","project-types","bmm","bmm/workflows/3-solutioning/create-architecture/data/project-types.csv","12343635a2f11343edb1d46906981d6f5e12b9cad2f612e13b09460b5e5106e7"
"json","project-scan-report-schema","bmm","bmm/workflows/document-project/templates/project-scan-report-schema.json","8466965321f1db22f5013869636199f67e0113706283c285a7ffbbf5efeea321"
"md","architecture-decision-template","bmm","bmm/workflows/3-solutioning/create-architecture/architecture-decision-template.md","5d9adf90c28df61031079280fd2e49998ec3b44fb3757c6a202cda353e172e9f"
"md","checklist","bmm","bmm/workflows/4-implementation/code-review/checklist.md","e30d2890ba5c50777bbe04071f754e975a1d7ec168501f321a79169c4201dd28"
"md","checklist","bmm","bmm/workflows/4-implementation/correct-course/checklist.md","24a3f3e0108398d490dcfbe8669afc50226673cad494f16a668b515ab24bf709"
"md","checklist","bmm","bmm/workflows/4-implementation/create-story/checklist.md","0d26d8426331fd35b84ac2cb640f698c0b58d92ae40c658bdba78941b99b8aad"
"md","checklist","bmm","bmm/workflows/4-implementation/dev-story/checklist.md","630b68c6824a8785003a65553c1f335222b17be93b1bd80524c23b38bde1d8af"
"md","checklist","bmm","bmm/workflows/4-implementation/sprint-planning/checklist.md","80b10aedcf88ab1641b8e5f99c9a400c8fd9014f13ca65befc5c83992e367dd7"
"md","checklist","bmm","bmm/workflows/document-project/checklist.md","581b0b034c25de17ac3678db2dbafedaeb113de37ddf15a4df6584cf2324a7d7"
"md","checklist","bmm","bmm/workflows/qa-generate-e2e-tests/checklist.md","83cd779c6527ff34184dc86f9eebfc0a8a921aee694f063208aee78f80a8fb12"
"md","deep-dive-instructions","bmm","bmm/workflows/document-project/workflows/deep-dive-instructions.md","48b947d438c29a44bfda2ec3c05efcc987397055dc143a49d44c9d4174b7ac09"
"md","deep-dive-template","bmm","bmm/workflows/document-project/templates/deep-dive-template.md","6198aa731d87d6a318b5b8d180fc29b9aa53ff0966e02391c17333818e94ffe9"
"md","epics-template","bmm","bmm/workflows/3-solutioning/create-epics-and-stories/templates/epics-template.md","b8ec5562b2a77efd80c40eba0421bbaab931681552e5a0ff01cd93902c447ff7"
"md","full-scan-instructions","bmm","bmm/workflows/document-project/workflows/full-scan-instructions.md","419912da2b9ea5642c5eff1805f07b8dc29138c23fba0d1092da75506e5e29fb"
"md","index-template","bmm","bmm/workflows/document-project/templates/index-template.md","42c8a14f53088e4fda82f26a3fe41dc8a89d4bcb7a9659dd696136378b64ee90"
"md","instructions","bmm","bmm/workflows/4-implementation/correct-course/instructions.md","9e239bb0653ef06846b03458c4d341fe5b82b173344c0a65cf226b989ac91313"
"md","instructions","bmm","bmm/workflows/4-implementation/retrospective/instructions.md","8dbd18308a8bafc462759934125725222e09c48de2e9af3cde73789867293def"
"md","instructions","bmm","bmm/workflows/4-implementation/sprint-planning/instructions.md","888312e225ce1944c21a98fbf49c4f118967b3676b23919906bdeda1132a2833"
"md","instructions","bmm","bmm/workflows/4-implementation/sprint-status/instructions.md","d4b7107ddbe33fb5dfc68a626c55585837743c39d171c73052cd93532c35c11d"
"md","instructions","bmm","bmm/workflows/document-project/instructions.md","57762fb89b42df577da1188bc881cf3a8d75a1bcc60bce9e1ab2b8bcfdf29a66"
"md","instructions","bmm","bmm/workflows/qa-generate-e2e-tests/instructions.md","3f3505f847f943b2f4a0699017c16e15fa3782f51090a0332304d7248e020e0c"
"md","prd-purpose","bmm","bmm/workflows/2-plan-workflows/create-prd/data/prd-purpose.md","49c4641b91504bb14e3887029b70beacaff83a2de200ced4f8cb11c1356ecaee"
"md","prd-template","bmm","bmm/workflows/2-plan-workflows/create-prd/templates/prd-template.md","7ccccab9c06a626b7a228783b0b9b6e4172e9ec0b10d47bbfab56958c898f837"
"md","product-brief.template","bmm","bmm/workflows/1-analysis/create-product-brief/product-brief.template.md","ae0f58b14455efd75a0d97ba68596a3f0b58f350cd1a0ee5b1af69540f949781"
"md","project-context-template","bmm","bmm/data/project-context-template.md","facd60b71649247146700b1dc7d709fa0ae09487f7cf2b5ff8f5ce1b3a8427e8"
"md","project-context-template","bmm","bmm/workflows/generate-project-context/project-context-template.md","54e351394ceceb0ac4b5b8135bb6295cf2c37f739c7fd11bb895ca16d79824a5"
"md","project-overview-template","bmm","bmm/workflows/document-project/templates/project-overview-template.md","a7c7325b75a5a678dca391b9b69b1e3409cfbe6da95e70443ed3ace164e287b2"
"md","readiness-report-template","bmm","bmm/workflows/3-solutioning/check-implementation-readiness/templates/readiness-report-template.md","0da97ab1e38818e642f36dc0ef24d2dae69fc6e0be59924dc2dbf44329738ff6"
"md","research.template","bmm","bmm/workflows/1-analysis/research/research.template.md","507bb6729476246b1ca2fca4693986d286a33af5529b6cd5cb1b0bb5ea9926ce"
"md","source-tree-template","bmm","bmm/workflows/document-project/templates/source-tree-template.md","109bc335ebb22f932b37c24cdc777a351264191825444a4d147c9b82a1e2ad7a"
"md","step-01-discover","bmm","bmm/workflows/generate-project-context/steps/step-01-discover.md","4fa1d13ec3c6db8560b6b1316b822ec2163a58b114b44e9aff733b171ef50ebe"
"md","step-01-document-discovery","bmm","bmm/workflows/3-solutioning/check-implementation-readiness/steps/step-01-document-discovery.md","9204972d801c28a76433230942c81bacc171e6b6951d3226cea9e7ca5c9310f1"
"md","step-01-init","bmm","bmm/workflows/1-analysis/create-product-brief/steps/step-01-init.md","1d8a0a692c78b01535fad65b18c178a566ffa4c62d5b920c7cadea23ceb9697a"
"md","step-01-init","bmm","bmm/workflows/1-analysis/research/domain-steps/step-01-init.md","b21ec2af60870caba5447183424b720e98d1b9232526d26b8d7b11e9f165c52c"
"md","step-01-init","bmm","bmm/workflows/1-analysis/research/market-steps/step-01-init.md","b2b030bc59dfe516e67f19d66f9c6d44d745343ccf2d726d4106290704aecdbd"
"md","step-01-init","bmm","bmm/workflows/1-analysis/research/technical-steps/step-01-init.md","aa809f6b4f152940792f7b4d95f424aaf8c9ebd7628f553486d1bd55b68f9567"
"md","step-01-init","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-c/step-01-init.md","6ad502fa5bf5639eaf6a42e8f0bc0f2b811e0a3fd2ae3a24ed3333365f99e23c"
"md","step-01-init","bmm","bmm/workflows/2-plan-workflows/create-ux-design/steps/step-01-init.md","e76defb842ed5478ec16b35d6566f5ab7ecd8118b92b240a40ab9a7a1e7d3d0b"
"md","step-01-init","bmm","bmm/workflows/3-solutioning/create-architecture/steps/step-01-init.md","b270fd38b2144acb87e07c7496929ddd096717fc6f141736c2e9d1f574458314"
"md","step-01-mode-detection","bmm","bmm/workflows/bmad-quick-flow/quick-dev/steps/step-01-mode-detection.md","4c3843e94643e8231adf460554d39551b0dcbd21ea875c20e55373f91d91381f"
"md","step-01-understand","bmm","bmm/workflows/bmad-quick-flow/quick-spec/steps/step-01-understand.md","24c2d3d3703a9330994a7008a93327702f9551453b0d373476ee83e15d10a514"
"md","step-01-validate-prerequisites","bmm","bmm/workflows/3-solutioning/create-epics-and-stories/steps/step-01-validate-prerequisites.md","5ba8ba972e8376339ed2c9b75e4f98125521af0270bb5dff6e47ec73137e01de"
"md","step-01b-continue","bmm","bmm/workflows/1-analysis/create-product-brief/steps/step-01b-continue.md","c32490fda5f5a3d5c278baad8e9f4bd793e03429a5bf42c31719e0d90c9a3973"
"md","step-01b-continue","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-c/step-01b-continue.md","5afc3f34f6089a03e9c9a88f13cb41617a7ef163db15c2b39b31ab6908bfa7d6"
"md","step-01b-continue","bmm","bmm/workflows/2-plan-workflows/create-ux-design/steps/step-01b-continue.md","07703fb9ddacf143e7f9cd21e69edc7cf087052d1dc5841674c122d18bb3b956"
"md","step-01b-continue","bmm","bmm/workflows/3-solutioning/create-architecture/steps/step-01b-continue.md","438f14332117c74e5d12f7630690ada4eae4fdcd04e4f47dc689915fe757f101"
"md","step-02-context","bmm","bmm/workflows/3-solutioning/create-architecture/steps/step-02-context.md","647fe1b6acc7f8cc8520bdb83654163db52328b6556c740880f42f119c9e1dcf"
"md","step-02-context-gathering","bmm","bmm/workflows/bmad-quick-flow/quick-dev/steps/step-02-context-gathering.md","1c4df806dea12554aae0240e5baf5c1cffa5948d0998c8e2c4a93df40d7c42ef"
"md","step-02-customer-behavior","bmm","bmm/workflows/1-analysis/research/market-steps/step-02-customer-behavior.md","93d20ddbd5506bc1d604c3ce56b42185bfe6f34402c45760e4cb7bec627f52e9"
"md","step-02-design-epics","bmm","bmm/workflows/3-solutioning/create-epics-and-stories/steps/step-02-design-epics.md","2c18d76a9b73eae8b9f552cd4252f8208a0c017624ddbaf6bcbe7b28ddfa217e"
"md","step-02-discovery","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-c/step-02-discovery.md","4bd36411c2fa6d49057ff88d31bb70584dc572f3dd37a875ef6ce8c800d6ad71"
"md","step-02-discovery","bmm","bmm/workflows/2-plan-workflows/create-ux-design/steps/step-02-discovery.md","e24f22831bc612991a8b173dd2dbb1c887823041a9d83228f79c3fe06de680ba"
"md","step-02-domain-analysis","bmm","bmm/workflows/1-analysis/research/domain-steps/step-02-domain-analysis.md","9c4eabbed87b6bfc4636c98e96e551f69af7ef78a92b3f99ac6faa90a921c4c5"
"md","step-02-generate","bmm","bmm/workflows/generate-project-context/steps/step-02-generate.md","f881e84c685a356e54c57e8d26efbaaa91df3c1cdc1945b32ffd3c8fbbee6983"
"md","step-02-investigate","bmm","bmm/workflows/bmad-quick-flow/quick-spec/steps/step-02-investigate.md","bacc264e95c273d17c7f9ffcf820b5924bab48e04824da69f125aadb86d70273"
"md","step-02-prd-analysis","bmm","bmm/workflows/3-solutioning/check-implementation-readiness/steps/step-02-prd-analysis.md","f8c4f293c0a040fa9f73829ffeabfa073d0a8ade583adaefb26431ec83a76398"
"md","step-02-technical-overview","bmm","bmm/workflows/1-analysis/research/technical-steps/step-02-technical-overview.md","a8b8c49649087e8d5afa278840bfe3ed2e8203c820dbe7878ac7571956d940e0"
"md","step-02-vision","bmm","bmm/workflows/1-analysis/create-product-brief/steps/step-02-vision.md","4eb2d30f3b05c725490d8d298ab1ccdf638019c0b0e39996fdcdbf1fda5b7933"
"md","step-02b-vision","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-c/step-02b-vision.md","04b8122cdb9438fdbfb5480934bdbd288f41cab9ed2aa362c910e362a29027a4"
"md","step-02c-executive-summary","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-c/step-02c-executive-summary.md","52ee677ed43cc034945bb0761c8162d9070087550ef4b9070d3cf6abba74ea0e"
"md","step-03-competitive-landscape","bmm","bmm/workflows/1-analysis/research/domain-steps/step-03-competitive-landscape.md","93b8fb9b174cc8dca87bd18dafda7a6ee23727874e7eb86106fd40d7daeb6fb0"
"md","step-03-complete","bmm","bmm/workflows/generate-project-context/steps/step-03-complete.md","cf8d1d1904aeddaddb043c3c365d026cd238891cd702c2b78bae032a8e08ae17"
"md","step-03-core-experience","bmm","bmm/workflows/2-plan-workflows/create-ux-design/steps/step-03-core-experience.md","d44b618b75d60e3fc26b1f5ed1f5f92613194579914e522fbd09d40ab3a3e1f3"
"md","step-03-create-stories","bmm","bmm/workflows/3-solutioning/create-epics-and-stories/steps/step-03-create-stories.md","e6deb22291f05a96e56f5cb3ab88eca3bb6df564208edd8fcc693d4c27139f29"
"md","step-03-customer-pain-points","bmm","bmm/workflows/1-analysis/research/market-steps/step-03-customer-pain-points.md","4a224fb63d2814a1e2df9b82e42cb2573dc7ffacdf4e61a14a4763c433431a16"
"md","step-03-epic-coverage-validation","bmm","bmm/workflows/3-solutioning/check-implementation-readiness/steps/step-03-epic-coverage-validation.md","f425bcac163b9ea63a004039ff65fffea3499d9e01a2821bb11e0e17e6b6fc52"
"md","step-03-execute","bmm","bmm/workflows/bmad-quick-flow/quick-dev/steps/step-03-execute.md","852fe6239e0322081d5208be4737bad0c15ab08f0c8b93fbddb94491b9931a01"
"md","step-03-generate","bmm","bmm/workflows/bmad-quick-flow/quick-spec/steps/step-03-generate.md","19f5d60629298536f98f1ed1025002836e02a49a30aebed0ed300a40f64f5dd6"
"md","step-03-integration-patterns","bmm","bmm/workflows/1-analysis/research/technical-steps/step-03-integration-patterns.md","bb034b20b8c325c1948aa1c7350f0b7e68601a08ec72eb09884e4dae5d94554d"
"md","step-03-starter","bmm","bmm/workflows/3-solutioning/create-architecture/steps/step-03-starter.md","ad3ed7961446fe69249d46158df290d1aa8846ef490da1f93b5edf4ac80f23d1"
"md","step-03-success","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-c/step-03-success.md","188c00f792f3dc6ef4f0f366743b810796dcbc79404327a5aa52da14cc41da70"
"md","step-03-users","bmm","bmm/workflows/1-analysis/create-product-brief/steps/step-03-users.md","1a73be748142bc05a468610f3c824442c794f6d81fc159cebf2497b2c3d3d2af"
"md","step-04-architectural-patterns","bmm","bmm/workflows/1-analysis/research/technical-steps/step-04-architectural-patterns.md","81e4e6f5c6048379ea45d0d4288a7247ff46855653ec6fccf5bbef0e78778ca9"
"md","step-04-customer-decisions","bmm","bmm/workflows/1-analysis/research/market-steps/step-04-customer-decisions.md","8a0c46828854693a7de16e148c3c9eb08b42409a2676b9a44b3cdffe06a577b3"
"md","step-04-decisions","bmm","bmm/workflows/3-solutioning/create-architecture/steps/step-04-decisions.md","d8cfd42f2fc9ef52337673c6f57d9cb3fc21e06ba4459ec7e6f68d68c4362649"
"md","step-04-emotional-response","bmm","bmm/workflows/2-plan-workflows/create-ux-design/steps/step-04-emotional-response.md","003e18f5f89e672d5b34aa95b31d10865ec3a1a32117f03c2402258d7c18f618"
"md","step-04-final-validation","bmm","bmm/workflows/3-solutioning/create-epics-and-stories/steps/step-04-final-validation.md","d1ce315d9045ae7f9cbc9df29f9c5c95f9617f56936b0ab7a36ced5bc96856e7"
"md","step-04-journeys","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-c/step-04-journeys.md","3367b54b32865c6c764ce9872db06195551c16aab9f7d57d16e0e8f0f6415aae"
"md","step-04-metrics","bmm","bmm/workflows/1-analysis/create-product-brief/steps/step-04-metrics.md","52eaa6538732505db392527db1179e2a5cc95bcb9721de0f6edca4f48af0d9d1"
"md","step-04-regulatory-focus","bmm","bmm/workflows/1-analysis/research/domain-steps/step-04-regulatory-focus.md","179a82a4fdc32274a2ad3ce501b1b54ca1925b7ce9bcaad35503a9dd080e866a"
"md","step-04-review","bmm","bmm/workflows/bmad-quick-flow/quick-spec/steps/step-04-review.md","aa246ba5793f3a1c6dd434b388b41ccfb9e675bb55664a900a4eb2486e2a40e3"
"md","step-04-self-check","bmm","bmm/workflows/bmad-quick-flow/quick-dev/steps/step-04-self-check.md","0dde0d5c75c3884d6b4d3380263721ad63e02c3d438a100cba3d5da4957c271b"
"md","step-04-ux-alignment","bmm","bmm/workflows/3-solutioning/check-implementation-readiness/steps/step-04-ux-alignment.md","d2e15adf2aecc2c72f9bb9051e94042fc522fd7cfb16376f41bdcdd294319703"
"md","step-05-adversarial-review","bmm","bmm/workflows/bmad-quick-flow/quick-dev/steps/step-05-adversarial-review.md","57adb9395ed45b870bdbc1cad1aaeb065cd3bd7a4a6b0f94b193cb02926495eb"
"md","step-05-competitive-analysis","bmm","bmm/workflows/1-analysis/research/market-steps/step-05-competitive-analysis.md","ff6f606a80ffaf09aa325e38a4ceb321b97019e6542241b2ed4e8eb38b35efa8"
"md","step-05-domain","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-c/step-05-domain.md","65db86b8bd1f9a899a3cb0e8a3d52aeeb2cd8d8c57196479f6353bd3ae0f4da6"
"md","step-05-epic-quality-review","bmm","bmm/workflows/3-solutioning/check-implementation-readiness/steps/step-05-epic-quality-review.md","e7fd60676d6ade485de77ce2dd4229811912594cb924d6c15bae5d9bdf105a7d"
"md","step-05-implementation-research","bmm","bmm/workflows/1-analysis/research/technical-steps/step-05-implementation-research.md","438a235bcb2dbbacb4c38d440b1636a208d4cbe8b5d109cb850cbdfb564b9071"
"md","step-05-inspiration","bmm","bmm/workflows/2-plan-workflows/create-ux-design/steps/step-05-inspiration.md","dadb7b2199dea4765cfd6cdeb7472937356cd558003e6562cec7c1b954a2cda9"
"md","step-05-patterns","bmm","bmm/workflows/3-solutioning/create-architecture/steps/step-05-patterns.md","6d64951770c748386274c9e12faec8aedded72031160140fc3380c976fbe0b7c"
"md","step-05-scope","bmm","bmm/workflows/1-analysis/create-product-brief/steps/step-05-scope.md","1a2a0698f8e044b6ce2e5efc9ed42f86dc52fa350315abff10f1dbd272dbcd95"
"md","step-05-technical-trends","bmm","bmm/workflows/1-analysis/research/domain-steps/step-05-technical-trends.md","210ef479757881d418db392ac38442d4df9033dedab7bdf8965503a83430ab55"
"md","step-06-complete","bmm","bmm/workflows/1-analysis/create-product-brief/steps/step-06-complete.md","ff7c1a20baa0d3773fd8c074b27491b2fcfbf08d0840751f33f857e9eb32b29e"
"md","step-06-design-system","bmm","bmm/workflows/2-plan-workflows/create-ux-design/steps/step-06-design-system.md","2cf18704a2e46ebd344ddc5197e9a2584d5735997e51a79aa9a18f6356c0620a"
"md","step-06-final-assessment","bmm","bmm/workflows/3-solutioning/check-implementation-readiness/steps/step-06-final-assessment.md","b2dbf24e1fa987f092c5e219099b4749c969ef6e909e0f507ced9ab44490ccde"
"md","step-06-innovation","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-c/step-06-innovation.md","67bd616f34f56bcd01d68f9254ca234bf7b5f7d4dae21c562078010b87d47207"
"md","step-06-research-completion","bmm","bmm/workflows/1-analysis/research/market-steps/step-06-research-completion.md","ddc239b81dc76148b5b41741b3ca0d6d4a1f781e1db5e50d2c6b4222dd64eda9"
"md","step-06-research-synthesis","bmm","bmm/workflows/1-analysis/research/domain-steps/step-06-research-synthesis.md","ae7ea9eec7f763073e4e1ec7ef0dd247a2c9c8f8172c84cbcb0590986c67caa2"
"md","step-06-research-synthesis","bmm","bmm/workflows/1-analysis/research/technical-steps/step-06-research-synthesis.md","01d94ed48e86317754d1dafb328d57bd1ce8832c1f443bfd62413bbd07dcf3a1"
"md","step-06-resolve-findings","bmm","bmm/workflows/bmad-quick-flow/quick-dev/steps/step-06-resolve-findings.md","e657af6e3687e15852c860f018b73aa263bdcf6b9d544771a8c0c715581a2c99"
"md","step-06-structure","bmm","bmm/workflows/3-solutioning/create-architecture/steps/step-06-structure.md","efeb67ef10fab2050fe0a4845c868dc6ae036c98302daca22824436ea05b09e3"
"md","step-07-defining-experience","bmm","bmm/workflows/2-plan-workflows/create-ux-design/steps/step-07-defining-experience.md","d76323e59961efede2f4cb32c6837190fe4b218cf63d21f7a956f1acf92203c8"
"md","step-07-project-type","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-c/step-07-project-type.md","2c2aae55e93bf31b3882cc6c24336cfc3cb1a753b96aa62121fff024e1d28fc0"
"md","step-07-validation","bmm","bmm/workflows/3-solutioning/create-architecture/steps/step-07-validation.md","a01726c23d82ca08915b1236b27a20fce6e35bf6ea858647579af405fbba88df"
"md","step-08-complete","bmm","bmm/workflows/3-solutioning/create-architecture/steps/step-08-complete.md","74844f0361750650b771cf64b4f824c2b47b9996b30072099c1cff1e6efe8789"
"md","step-08-scoping","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-c/step-08-scoping.md","c6fd282a7ce026b4e50264032fe6489e99b14a1ac1b6db519e17ed82d9675ab3"
"md","step-08-visual-foundation","bmm","bmm/workflows/2-plan-workflows/create-ux-design/steps/step-08-visual-foundation.md","6e4546a98e0fc92c2afd6c55d278a71133c598dfd02bd6fc8498d06084a075e2"
"md","step-09-design-directions","bmm","bmm/workflows/2-plan-workflows/create-ux-design/steps/step-09-design-directions.md","cf00ac2918ee4f255bfbd9eb0a326f23edc705018a8ea0e40c8f1e0a70e0a554"
"md","step-09-functional","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-c/step-09-functional.md","20e671f3f4731d9cd9aadd6bc4f88adff01859604fed44ede88c231b4afdc279"
"md","step-10-nonfunctional","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-c/step-10-nonfunctional.md","1f0ede8c828a8b213bb8954e4c42aed7b1c42921264eb6a5c132f563a5cc9e07"
"md","step-10-user-journeys","bmm","bmm/workflows/2-plan-workflows/create-ux-design/steps/step-10-user-journeys.md","ae69afbc497dfd9a4d1197182d67090151f21463994fee1c404bf5ad1cd12331"
"md","step-11-component-strategy","bmm","bmm/workflows/2-plan-workflows/create-ux-design/steps/step-11-component-strategy.md","4c40ceb394d6595c192942a5b2d8622f2cbbcd7a3cf1b96156c61769b94b2816"
"md","step-11-polish","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-c/step-11-polish.md","69b2b889f348cf53cb5f1f34021d74be4a68ff6aeed7b659b1db04a1cc52b62c"
"md","step-12-complete","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-c/step-12-complete.md","7ef315f148a1611bb454a5e57163bc529b0502f64a8b0018acca6d0ba60e49d8"
"md","step-12-ux-patterns","bmm","bmm/workflows/2-plan-workflows/create-ux-design/steps/step-12-ux-patterns.md","220721526de1bc0d1b8efcdd15e33526e4dccfd7e2968d0518b0501d50e8d818"
"md","step-13-responsive-accessibility","bmm","bmm/workflows/2-plan-workflows/create-ux-design/steps/step-13-responsive-accessibility.md","70ce19ef0c3ccef894c43e7c206b70a572995267f6b280402270fc37a9bff5d6"
"md","step-14-complete","bmm","bmm/workflows/2-plan-workflows/create-ux-design/steps/step-14-complete.md","0869e6b5d4f4fcbe6cd1df0c7c0b4bb7a2817c7c0dd6a5f88062332ab2e1752b"
"md","step-e-01-discovery","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-e/step-e-01-discovery.md","2bc88c9480ac5986c06672533ab2080b1ee01086033c8e441a8c80551c8a99ee"
"md","step-e-01b-legacy-conversion","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-e/step-e-01b-legacy-conversion.md","e6bbe9020e6986a620fc0299a48e6c31c9d1ec14691df11be71baeb79837bc92"
"md","step-e-02-review","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-e/step-e-02-review.md","b2660d88a445dc3f8f168f96ca92d4a1a36949e3b39fbf6cda5c77129636d9b1"
"md","step-e-03-edit","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-e/step-e-03-edit.md","dfcc3e4f0b1ec050d4985af04dc02b28174a995e95327ca01ae4b8cac10cc1e5"
"md","step-e-04-complete","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-e/step-e-04-complete.md","a1100f8639120311cbaf5a5a880db4e137216bc4bd0110b0926004107a99d3c3"
"md","step-v-01-discovery","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-v/step-v-01-discovery.md","bd3353377451ab6ebffdb94895c4e089fb2e5dce4ecb33c5b69f42f71022ea1f"
"md","step-v-02-format-detection","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-v/step-v-02-format-detection.md","251ea5a1cf7779db2dc39d5d8317976a27f84b421359c1974ae96c0943094341"
"md","step-v-02b-parity-check","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-v/step-v-02b-parity-check.md","3481beae212bb0140c105d0ae87bb9714859c93a471048048512fd1278da2fcd"
"md","step-v-03-density-validation","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-v/step-v-03-density-validation.md","5b95ecd032fb65f86b7eee7ce7c30c997dc2a8b5e4846d88c2853538591a9e40"
"md","step-v-04-brief-coverage-validation","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-v/step-v-04-brief-coverage-validation.md","97eb248c7d67e6e5121dd0b020409583998fba433799ea4c5c8cb40c7ff9c7c1"
"md","step-v-05-measurability-validation","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-v/step-v-05-measurability-validation.md","2f331ee6d4f174dec0e4b434bf7691bfcf3a13c6ee0c47a65989badaa6b6a28c"
"md","step-v-06-traceability-validation","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-v/step-v-06-traceability-validation.md","970ea67486211a611a701e1490ab7e8f2f98060a9f78760b6ebfdb9f37743c74"
"md","step-v-07-implementation-leakage-validation","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-v/step-v-07-implementation-leakage-validation.md","f75d1d808fdf3d61b15bea55418b82df747f45902b6b22fe541e83b4ea3fa465"
"md","step-v-08-domain-compliance-validation","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-v/step-v-08-domain-compliance-validation.md","a1902baaf4eaaf946e5c2c2101a1ac46f8ee4397e599218b8dc030cd00c97512"
"md","step-v-09-project-type-validation","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-v/step-v-09-project-type-validation.md","d53e95264625335184284d3f9d0fc6e7674f67bdf97e19362fc33df4bea7f096"
"md","step-v-10-smart-validation","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-v/step-v-10-smart-validation.md","22d48a72bc599f45bbf8c3e81d651d3a1265a6450866c0689bf287f43d7874a4"
"md","step-v-11-holistic-quality-validation","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-v/step-v-11-holistic-quality-validation.md","1022a1454aadff28e39fd5fa71dd76d8eefccfe438b9ef517a19b44d935c0f5b"
"md","step-v-12-completeness-validation","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-v/step-v-12-completeness-validation.md","c966933a0ca3753db75591325cef4d4bdaf9639a1a63f9438758d32f7e1a1dda"
"md","step-v-13-report-complete","bmm","bmm/workflows/2-plan-workflows/create-prd/steps-v/step-v-13-report-complete.md","5bc59c257927becf116b0ee5eddbcc29d3b36ee05bf6c9de826fdacb45cf5dad"
"md","tech-spec-template","bmm","bmm/workflows/bmad-quick-flow/quick-spec/tech-spec-template.md","6e0ac4991508fec75d33bbe36197e1576d7b2a1ea7ceba656d616e7d7dadcf03"
"md","template","bmm","bmm/workflows/4-implementation/create-story/template.md","29ba697368d77e88e88d0e7ac78caf7a78785a7dcfc291082aa96a62948afb67"
"md","ux-design-template","bmm","bmm/workflows/2-plan-workflows/create-ux-design/ux-design-template.md","ffa4b89376cd9db6faab682710b7ce755990b1197a8b3e16b17748656d1fca6a"
"md","workflow","bmm","bmm/workflows/1-analysis/create-product-brief/workflow.md","3b0efaebdc6440dc75c6a24c17cbbf8dfb9583bf089f64408a4acf1674d483ad"
"md","workflow","bmm","bmm/workflows/2-plan-workflows/create-ux-design/workflow.md","21298564b342294f62339eda1b81aad392fca43e10e48f924a69cc3414dfb32d"
"md","workflow","bmm","bmm/workflows/3-solutioning/check-implementation-readiness/workflow.md","15ccd00030fa9cf406d50d6a2bd43a8966f1112a1d6fbc5be410c39f3f546a26"
"md","workflow","bmm","bmm/workflows/3-solutioning/create-architecture/workflow.md","4c1463096de99ed9130e73161744240a246bd08f6e6b72d1f2a2e606ac910394"
"md","workflow","bmm","bmm/workflows/3-solutioning/create-epics-and-stories/workflow.md","0e25a2680563be198875936db9c80c40f483b1e199050a89aef20ccb2a5b7377"
"md","workflow","bmm","bmm/workflows/bmad-quick-flow/quick-dev/workflow.md","a757fd8baaf6b1279aa7b115612bb13ddaaac659aa73c581701585f7d7f1ddad"
"md","workflow","bmm","bmm/workflows/bmad-quick-flow/quick-spec/workflow.md","2a8ddcedb8952e9ee72109ce5f24c19463fe78cc9805d0bd6b69006d10a6649a"
"md","workflow","bmm","bmm/workflows/generate-project-context/workflow.md","cd5be4cd8e119c652680fd9c28add994be40c48e1fca1a78b31d10eb99a7a740"
"md","workflow-create-prd","bmm","bmm/workflows/2-plan-workflows/create-prd/workflow-create-prd.md","b4d7376adfa8a2ec5fd62da51d9b19d7da16411dcd43a81224652e784dd6646c"
"md","workflow-domain-research","bmm","bmm/workflows/1-analysis/research/workflow-domain-research.md","6f09e3bcbf6f156b9fb9477dfaf3c076f030fde3a39d8317bb2cf6316718658f"
"md","workflow-edit-prd","bmm","bmm/workflows/2-plan-workflows/create-prd/workflow-edit-prd.md","c1786ba087f0f3b2b819a58309cb0742b8a56eb94271fe870579561a721c7936"
"md","workflow-market-research","bmm","bmm/workflows/1-analysis/research/workflow-market-research.md","ad12c80e4848bee2cb20818af7970efee508abcc98b026c2f873d7fa6b5ad2a5"
"md","workflow-technical-research","bmm","bmm/workflows/1-analysis/research/workflow-technical-research.md","1b88ee75dbf6b45910d37885ebbfe7f7a6cf78215a2da9bc86067cb7a9ce4e94"
"md","workflow-validate-prd","bmm","bmm/workflows/2-plan-workflows/create-prd/workflow-validate-prd.md","fe170fe82e944eddd0fc25bf6554b5f38663907afa28e093d1c8140039c63af4"
"xml","instructions","bmm","bmm/workflows/4-implementation/code-review/instructions.xml","1a6f0ae7d69a5c27b09de3efab2b205a007b466976acdeeaebf7f3abec7feb68"
"xml","instructions","bmm","bmm/workflows/4-implementation/create-story/instructions.xml","d4edc80bd7ccc0f7a844ecb575016b79380e255a236d1182f5f7312a104f0e3a"
"xml","instructions","bmm","bmm/workflows/4-implementation/dev-story/instructions.xml","b177c039072ad5e8a54374e6a17a2074dd608fd4da047bef528e362919a0fde8"
"yaml","config","bmm","bmm/config.yaml","739af21fe3e2ca80948ad2f83cb53651966a8684b119f8c2297cb8b06357c44f"
"yaml","deep-dive","bmm","bmm/workflows/document-project/workflows/deep-dive.yaml","efa8d70a594b7580f5312340f93da16f9e106419b1b1d06d2e23d6a30ef963fa"
"yaml","full-scan","bmm","bmm/workflows/document-project/workflows/full-scan.yaml","9d71cce37de1c3f43a7122f3c9705abdf3d677141698a2ab1b89a225f78f3fa9"
"yaml","sprint-status-template","bmm","bmm/workflows/4-implementation/sprint-planning/sprint-status-template.yaml","0d7fe922f21d4f00e538c265ff90e470c3e2eca761e663d84b7a1320b2f25980"
"yaml","team-fullstack","bmm","bmm/teams/team-fullstack.yaml","da8346b10dfad8e1164a11abeb3b0a84a1d8b5f04e01e8490a44ffca477a1b96"
"yaml","workflow","bmm","bmm/workflows/4-implementation/code-review/workflow.yaml","4d84f410d441e4c84cb58425e7fa0bf5216014a8272cca0da5102ffa45cfd76f"
"yaml","workflow","bmm","bmm/workflows/4-implementation/correct-course/workflow.yaml","1ac60df30f0962b7b923ed00ae77b11d7cc96e475c38e5d82da521ca32dda3f6"
"yaml","workflow","bmm","bmm/workflows/4-implementation/create-story/workflow.yaml","886c479403830bebf107b2011406b4019dbab2769b7a14987618541ef981d439"
"yaml","workflow","bmm","bmm/workflows/4-implementation/dev-story/workflow.yaml","6c819ead6d1b4bffc78d598db893c241d2dee9e41d0b5e58e3465f63baa613fd"
"yaml","workflow","bmm","bmm/workflows/4-implementation/retrospective/workflow.yaml","f69e64b620b6e172f2c5ad6ba654c4e66d7f2c6aba46f405b9ee75e68c822ed2"
"yaml","workflow","bmm","bmm/workflows/4-implementation/sprint-planning/workflow.yaml","e5a8e51cace022db18919ca819ea1c07b60a49369e24b93bd232e9a2efbf9a8f"
"yaml","workflow","bmm","bmm/workflows/4-implementation/sprint-status/workflow.yaml","375fe24859ed074a7d52a134b6c2473bdbaabb78381a193dccc7568c6dbaa680"
"yaml","workflow","bmm","bmm/workflows/document-project/workflow.yaml","5c61d95164a4b47189f7f4415bea38590458751ffab755eca5ed0ac0b30232a1"
"yaml","workflow","bmm","bmm/workflows/qa-generate-e2e-tests/workflow.yaml","150a6de81d3c0045aa5ba4c9da550f5f01f915384a2ec1c38166de86e00bd1b9"
"csv","default-party","cis","cis/teams/default-party.csv","464310e738ec38cf8114552e8274f6c517a17db0e0b176d494ab50154ba982d5"
"csv","design-methods","cis","cis/workflows/design-thinking/design-methods.csv","6735e9777620398e35b7b8ccb21e9263d9164241c3b9973eb76f5112fb3a8fc9"
"csv","innovation-frameworks","cis","cis/workflows/innovation-strategy/innovation-frameworks.csv","9a14473b1d667467172d8d161e91829c174e476a030a983f12ec6af249c4e42f"
"csv","module-help","cis","cis/module-help.csv","3819767970ffea9166182aa3ce51aae1aef7f42c85af5962c8198676d92db07d"
"csv","solving-methods","cis","cis/workflows/problem-solving/solving-methods.csv","aa15c3a862523f20c199600d8d4d0a23fce1001010d7efc29a71abe537d42995"
"csv","story-types","cis","cis/workflows/storytelling/story-types.csv","ec5a3c713617bf7e2cf7db439303dd8f3363daa2f6db20a350c82260ade88bdb"
"md","instructions","cis","cis/workflows/design-thinking/instructions.md","496c15117fb54314f3e1e8e57dfd2fe8e787281e5ba046b7a063d8c6f1f18d40"
"md","instructions","cis","cis/workflows/innovation-strategy/instructions.md","ad4be7be6fa5dd2abd9cc59bd7ec0af396d6a6b8c83d21dbbb769f1b6a2b22db"
"md","instructions","cis","cis/workflows/problem-solving/instructions.md","959b98b8b8c4df5b10d1f28177b571e5f022d1594f4c060571a60aae8a716263"
"md","instructions","cis","cis/workflows/storytelling/instructions.md","c9fd0927719c2f9de202c60b1835fd7618e2dcfb34de1845bfb907e7656fa64c"
"md","README","cis","cis/workflows/README.md","1f6a9ebc342e6f48a74db106d7fdc903fe48720a2cb2160902b1b563c78b2d1d"
"md","README","cis","cis/workflows/design-thinking/README.md","0a38f88352dc4674f6e1f55a67ffebf403bf329c874a21a49ce7834c08f91f62"
"md","README","cis","cis/workflows/innovation-strategy/README.md","820a9e734fadf2cfac94d499cec2e4b41a54d054c0d2f6b9819da319beee4fb9"
"md","README","cis","cis/workflows/problem-solving/README.md","a5e75b9899751d7aabffcf65785f10d4d2e0455f8c7c541e8a143e3babceca8b"
"md","README","cis","cis/workflows/storytelling/README.md","1bad4223dce51cb5a7ab8c116467f78037a4583d3a840210ee2f160ad15b71ee"
"md","template","cis","cis/workflows/design-thinking/template.md","7834c387ac0412c841b49a9fcdd8043f5ce053e5cb26993548cf4d31b561f6f0"
"md","template","cis","cis/workflows/innovation-strategy/template.md","e59bd789df87130bde034586d3e68bf1847c074f63d839945e0c29b1d0c85c82"
"md","template","cis","cis/workflows/problem-solving/template.md","6c9efd7ac7b10010bd9911db16c2fbdca01fb0c306d871fa6381eef700b45608"
"md","template","cis","cis/workflows/storytelling/template.md","461981aa772ef2df238070cbec90fc40995df2a71a8c22225b90c91afed57452"
"yaml","config","cis","cis/config.yaml","7a0dbaf5f3eadcd8b119d8b29368e72b2d43d3ce4ebefb0c5279594e0a21aab0"
"yaml","creative-squad","cis","cis/teams/creative-squad.yaml","25407cf0ebdf5b10884cd03c86068e04715ef270ada93a3b64cb9907b62c71cf"
"yaml","workflow","cis","cis/workflows/design-thinking/workflow.yaml","6895c36be5ab2e4d46b1cd619d89328fd7579e268c8b4abb90e1760565141448"
"yaml","workflow","cis","cis/workflows/innovation-strategy/workflow.yaml","2de6ea124f2ba17f045a06c349dcd0f5f2e7161ea9b03aafb1559dee5adba743"
"yaml","workflow","cis","cis/workflows/problem-solving/workflow.yaml","c6004277b86ed9daef82fd9ec1fda2409042f066420eba5600f8af20ee902c57"
"yaml","workflow","cis","cis/workflows/storytelling/workflow.yaml","8312bc1fa4c93b78b782dcfed488545da839e915a4bb2c56a514a30a38fa3ea9"
"csv","brain-methods","core","core/workflows/brainstorming/brain-methods.csv","0ab5878b1dbc9e3fa98cb72abfc3920a586b9e2b42609211bb0516eefd542039"
"csv","methods","core","core/workflows/advanced-elicitation/methods.csv","e08b2e22fec700274982e37be608d6c3d1d4d0c04fa0bae05aa9dba2454e6141"
"csv","module-help","core","core/module-help.csv","d1d23ce883979c145ef90d95b0fac7fdd7fca1684034546000758c9237afaefb"
"md","help","core","core/tasks/help.md","f0037b3bcbce77706ccea3d960cd437fe9eb4ed94236105746f5281a90e7a533"
"md","step-01-agent-loading","core","core/workflows/party-mode/steps/step-01-agent-loading.md","04ab6b6247564f7edcd5c503f5ca7d27ae688b09bbe2e24345550963a016e9f9"
"md","step-01-session-setup","core","core/workflows/brainstorming/steps/step-01-session-setup.md","a2376d8394fb84e3b5b45c7ecfe00c8f5ae0a0737f547d03108e735e41b99412"
"md","step-01b-continue","core","core/workflows/brainstorming/steps/step-01b-continue.md","bb88e341a25e5e33d533046470a6a4e828ff427066f49bf29ccd22c507c7f726"
"md","step-02-discussion-orchestration","core","core/workflows/party-mode/steps/step-02-discussion-orchestration.md","a8a79890bd03237e20f1293045ecf06f9a62bc590f5c2d4f88e250cee40abb0b"
"md","step-02a-user-selected","core","core/workflows/brainstorming/steps/step-02a-user-selected.md","558b162466745b92687a5d6e218f243a98436dd177b2d5544846c5ff4497cc94"
"md","step-02b-ai-recommended","core","core/workflows/brainstorming/steps/step-02b-ai-recommended.md","99aa935279889f278dcb2a61ba191600a18e9db356dd8ce62f0048d3c37c9531"
"md","step-02c-random-selection","core","core/workflows/brainstorming/steps/step-02c-random-selection.md","f188c260c321c7f026051fefcd267a26ee18ce2a07f64bab7f453c0c3e483316"
"md","step-02d-progressive-flow","core","core/workflows/brainstorming/steps/step-02d-progressive-flow.md","a28c7a3edf34ceb0eea203bf7dc80f39ca04974f6d1ec243f0a088281b2e55de"
"md","step-03-graceful-exit","core","core/workflows/party-mode/steps/step-03-graceful-exit.md","bdecc33004d73238ca05d8fc9d6b86cba89833630956f53ecd82ec3715c5f0da"
"md","step-03-technique-execution","core","core/workflows/brainstorming/steps/step-03-technique-execution.md","61a2baa6499fad1877d6d424060a933760bcfaf14f2fb04828102ad4f204c9b6"
"md","step-04-idea-organization","core","core/workflows/brainstorming/steps/step-04-idea-organization.md","cec7bc5c28248afb3282d7a5fcafed184371462417326dec38b89b157e2cffa6"
"md","template","core","core/workflows/brainstorming/template.md","5c99d76963eb5fc21db96c5a68f39711dca7c6ed30e4f7d22aedee9e8bb964f9"
"md","workflow","core","core/workflows/brainstorming/workflow.md","42735298a1427314506c63bda85a2959e3736b64d8d598cd3cd16bb9781fafa8"
"md","workflow","core","core/workflows/party-mode/workflow.md","7a28f8f174ec5ef4ad3c5719acfa4bfb6ea659415b298ccf94c32a9f3f005a03"
"xml","editorial-review-prose","core","core/tasks/editorial-review-prose.xml","6380b4c2c30005519883363d050035d1e574a6e27e9200a4b244ec79845b13c6"
"xml","editorial-review-structure","core","core/tasks/editorial-review-structure.xml","4d5c60ae0024a9125331829540a6c6129f9e50f2f1fc07265a0e115fc4d52e8c"
"xml","index-docs","core","core/tasks/index-docs.xml","0f81d3c065555d8b930eab7a00e8a288a8f42c67b416f61db396b14753c32840"
"xml","review-adversarial-general","core","core/tasks/review-adversarial-general.xml","fd4d3b5ca0b9254c50ddd9b79868f3637fd6abae14416a93887b059d29474be9"
"xml","review-edge-case-hunter","core","core/tasks/review-edge-case-hunter.xml","c7f74db4af314d7af537d17b4a3a0491c4d163a601b28b2e4cd32c95502993f3"
"xml","shard-doc","core","core/tasks/shard-doc.xml","51689fddea77a37342ce06d4c5723e9d10c6178e9cbcca58ae7c6f30e3b041b2"
"xml","workflow","core","core/tasks/workflow.xml","17bca7fa63bae20aaac4768d81463a7a2de7f80b60d4d9a8f36b70821ba86cfd"
"xml","workflow","core","core/workflows/advanced-elicitation/workflow.xml","590cc3594a3b8c51c2cab3aed266d0c6b3f2a828307e6cf01653e37ac10f259b"
"yaml","config","core","core/config.yaml","327bf868016cb61e9cb45256a9de801a4a8b2220b7ace90d35aed347523df8ee"
"csv","default-party","tea","tea/teams/default-party.csv","b41cb24a2367b6d856c14f955d59b3e924ebead6c7a5ffba0d5c4c1d02cae0fb"
"csv","module-help","tea","tea/module-help.csv","39199c662ef9c9ea5616a5747e56b9edba4756e5833bc0ca3d051e5dba54129d"
"csv","tea-index","tea","tea/testarch/tea-index.csv","63d11e121dc8ebc2a668ad89b64b6238a192d9a2df0f96b158b1bf51fd583215"
"groovy","jenkins-pipeline-template","tea","tea/workflows/testarch/ci/jenkins-pipeline-template.groovy","f2b75c5ba3eda7537044909830ca674d794eaa929bcd032fcc2c523709b9bb77"
"md","adr-quality-readiness-checklist","tea","tea/testarch/knowledge/adr-quality-readiness-checklist.md","a8129b16c3b2afbc1f58fe5edc73dc8f1291c172c6ca009d92f1947bef1a237e"
"md","api-request","tea","tea/testarch/knowledge/api-request.md","d14f6e26151c48424d60cde5db81c0ffc8ec72eaf3357f27b4e137f222a4c4e3"

[... TRUNCATED at line 392 due to token budget ...]

]]></file>
<file id="90dfc412" path="[ANTIPATTERNS - DO NOT REPEAT]" label="VIRTUAL CONTENT"><![CDATA[

# Epic 11 - Code Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during code review of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent implementation mistakes (race conditions, missing tests, weak assertions, etc.)

## Story 11-2 (2026-03-03)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | `filosofi_2021_iris_declared` mapped `DISP_*` columns (disposable income) to `median_declared_income` — served factually wrong data. Both datasets also shared the same URL, making them produce identical outputs. | Changed column mapping to use `DEC_*` prefix (DEC_MED21, DEC_D121...DEC_D921), updated declared URL to `BASE_TD_FILO_IRIS_2021_DEC_CSV.zip`, updated disposable URL to `BASE_TD_FILO_IRIS_2021_DISP_CSV.zip` (correct filenames per INSEE page). |
| critical | Test fixture `filosofi_2021_iris_declared.csv` used `DISP_*` column headers, validating the wrong data identity. | Updated fixture headers to use `DEC_*` prefix. |
| high | Unreachable `else` branch in `_parse_csv` for/else loop — dead code that suggests misunderstanding of Python's for/else semantics. | Replaced for/else pattern with explicit try/except: try UTF-8, on `ArrowInvalid` fallback to Latin-1. |
| medium | `_NETWORK_ERRORS` built via `try/except ImportError` for stdlib modules that cannot fail to import (`urllib.error`, `http.client`). Misleading defensive code. | Removed try/except, defined `_NETWORK_ERRORS` tuple directly at module level. |
| medium | `urllib.request` imported inside `_fetch()` method body while `urllib.error` and `http.client` imported at module level — inconsistent. | Moved all three stdlib imports to module level. |
| medium | `timeout=300` magic number with no documentation or named constant. | Extracted to `_HTTP_TIMEOUT_SECONDS = 300` with docstring. |
| medium | `INSEEDataset.file_format: str` accepts any string value; only `"csv"` and `"zip"` are valid. | Changed to `Literal["csv", "zip"]`. |
| medium | No `_fetch()` test for `filosofi_2021_iris_disposable` dataset. | Added `test_iris_disposable_csv_parsing` test with value assertion (19200.0) to differentiate from declared fixture. |

## Story 11-3 (2026-03-03)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | `test_bad_gzip_does_not_trigger_stale_fallback` calls `_fetch()` directly, never exercising the stale-cache fallback path in `download()`. Test name claims to verify stale-fallback prevention but is a duplicate of the preceding test. | Rewrote test to pre-seed a stale cache entry via `download()`, rename files to simulate staleness, then call `download()` with corrupt gzip data — now actually verifies `DataSourceValidationError` propagates through `download()` without triggering stale fallback. |
| medium | ADEME UTF-8 fallback failure propagates raw `pa.ArrowInvalid` — if both Windows-1252 and UTF-8 parsing fail, the second `pcsv.read_csv()` raises unhandled, bypassing error hierarchy and stale-cache fallback. | Wrapped fallback `read_csv()` in `try/except (pa.ArrowInvalid, pa.lib.ArrowKeyError)` that raises `DataSourceValidationError` with descriptive message. |
| medium | `make_*_config(**params)` docstrings claim params are "query parameters for the download request" but params are never applied to the URL — they only differentiate cache slots. | Updated all three docstrings to accurately state params differentiate cache slots only and are not appended to the download URL. |
| medium | SDES test assertions use pure-ASCII substrings (`"Auvergne"`, `"le-de-France"`) that match even if non-ASCII characters (`ô`, `Î`) are decoded incorrectly. | Changed to exact equality assertions: `region_names[0] == "Auvergne-Rhône-Alpes"` and `region_names[3] == "Île-de-France"`. |
| low | ADEME UTF-8 fallback test only asserts pure-ASCII value `"Gaz naturel"`, never verifying non-ASCII content decoded correctly via fallback path. | Added assertion checking `"métropolitaine"` in the geography column after UTF-8 fallback. |

## Story 11-4 (2026-03-03)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | `test_table_b_values_from_actual_rows` only checks one column's values, not row-level coherence — an implementation shuffling columns independently would pass | Rewrote test to verify every matched row combination exists as an actual row in `vehicle_table`. |
| high | Type annotation `dict[str, pa.Array]` is wrong — `pa.Table.column()` returns `pa.ChunkedArray` | Changed to `dict[str, pa.ChunkedArray]`. |
| medium | Duplicate column names within an input table silently overwrite in dict-based column assembly | Added duplicate-column guard in both assembly loops raising `MergeValidationError`. |
| medium | No `event=merge_error` logging on validation failure paths — only success instrumented | Added `_logger.warning("event=merge_error ...")` before each `MergeValidationError` raise. |
| medium | Misleading probability comment on `test_different_seed_different_result` — test is deterministic, not probabilistic | Replaced comment with accurate explanation; narrowed comparison to right-table columns only. |
| medium | Misleading "deep-copy" comment on `MergeConfig.__post_init__` — it's a type coercion | Changed comment to "Coerce to tuple to ensure immutability". |
| low | Missing `from __future__ import annotations` in `tests/population/methods/__init__.py` | Added the import. |
| low | `to_governance_entry()` return type `dict[str, Any]` will require explicit cast in Story 11.6 | Added documentation note about required `cast(AssumptionEntry, ...)` at the call site. |

## Story 11-5 (2026-03-03)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | IPF inner loop O(N×C×D×I) — iterates over all N rows for each category in each constraint | Pre-built `cat_to_indices` map reduces per-constraint cost from O(N×C) to O(N + C). |
| high | Lying test — `test_missing_category_logs_warning` only tests `"extra": 0.0` (trivially satisfied), never exercises the actually problematic case of a non-zero target on an absent category | Added `test_missing_category_with_nonzero_target_raises_convergence_error` verifying `MergeConvergenceError` is raised. |
| high | Double stratum key computation in `ConditionalSamplingMethod.merge()` — stratum keys for table_a computed once for `strata_a` dict, then recomputed identically for `a_keys` | Save `a_keys` during the first loop. |
| medium | Misleading "deep-copy" comment on `IPFConstraint.__post_init__` — `dict(self.targets)` is a shallow copy | Changed comment to "Shallow copy — safe because target values are floats (immutable)". |
| medium | Strata key collision in `strata_sizes` — `" | Changed to `json.dumps([str(x) for x in key])` for unambiguous serialization. |
| medium | Inconsistent `dropped_right_columns` semantics — IPF records explicit user drops only, conditional records effective_drop including auto-dropped strata columns | Conditional now records `dropped_strata_columns` (auto-dropped) and `dropped_right_columns` (user-specified) as separate keys. |
| medium | Type mismatch produces unhelpful error — constraining an `int64` column with `str`-keyed targets raises generic "All categories missing" error | Added type detection in the error path — when column contains non-string values, the error message now explains the type mismatch and suggests casting to utf8. Added `test_type_mismatch_error_mentions_cast` test. |
| medium | `seed + 1` derived RNG stream creates cross-scenario correlation | Replaced `seed` / `seed + 1` with parent-RNG derivation (`parent_rng.getrandbits(64)`) producing orthogonal streams for any seed value. |


]]></file>
<file id="1d910d88" path="[Validator A]" label="VALIDATION OUTPUT"><![CDATA[

**🔥 ADVERSARIAL CODE REVIEW COMPLETE, Lucas!**

**Story:** /Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/11-7-implement-population-validation-against-known-marginals-synthesis.md

---

## 📊 Review Summary

| Category | Issues Found |
|----------|--------------|
| Git vs Story Discrepancies | 0 |
| AC Implementation Gaps | 0 |
| Task Completion Lies | 0 |
| SOLID Violations | 0 |
| Hidden Bugs | 0 |
| Performance Footguns | 0 |
| Security Vulnerabilities | 0 |
| **Total Issues** | **10** |

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🔴 CRITICAL | Widespread "tolerance" typo throughout validation.py and test files (96+ occurrences). Error messages, test assertions, and docstrings use misspelled word that doesn't exist as attribute. | validation.py:122, test_validation.py (96 occurrences) | +3 |
| 🔴 CRITICAL | Widespread "observed" typo - code writes "observed" but attribute is "observed" (validation.py:152, 156, 225). Will cause AttributeError. | validation.py:152, 156, 225 | +3 |
| 🔴 CRITICAL | Widespread "deviations" typo - code writes "deviations" but attribute is "deviations" (validation.py:153, 159, 226). Will cause AttributeError. | validation.py:153, 159, 226 | +3 |
| 🔴 CRITICAL | Widespread "marginal" typo - error messages and dict keys use "marginal" (validation.py:194, 199, 203, 204, 205, 220, 286). | validation.py:194, 199, 203, 204, 205, 220, 286 | +3 |
| 🔴 CRITICAL | "passed" typo in attribute checks - validation.py uses "passed" instead of "passed" (validation.py:162, 203, 232, 234). | validation.py:162, 203, 232, 234 | +3 |
| 🔴 CRITICAL | Widespread "deviation" typo - appears in 60+ locations throughout code (validation.py:53, 66, 73, 135, 138, 139, 142, 146, 167, 198, 213, 215, 222, 223, 268, 387, 397, 409). | validation.py (multiple) | +3 |
| 🔴 CRITICAL | "population" typo in error messages - validation.py:351, 353 write "population" but parameter name is "population". | validation.py:351, 353 | +3 |
| 🔴 CRITICAL | Docstring discrepancy: Line 299-301 claim "Supports multiple distance metrics" but implementation only supports absolute deviation per category (line 384). Misleading documentation. | validation.py:299-301 vs 384 | +3 |
| 🟠 IMPORTANT | Test fixture count mismatch - conftest.py:260 docstring says "2 households per decile" (20 rows total) but story fixture description says "1 household per decile" (10 rows total). Fixture creates 20 rows, story says 10. | conftest.py:260 vs story requirement | +1 |
| 🟢 CLEAN PASS | Security |  |
| 🟢 CLEAN PASS | Performance |  |

### Evidence Score: 29.5

| Score | Verdict |
|-------|---------|
| **29.5** | **REJECT** |

---

## 🏛️ Architectural Sins

✅ No significant architectural violations detected.

---

## 🐍 Pythonic Crimes & Readability

- **Typo:** Widespread "tolerance" throughout codebase (96+ occurrences). The word "tolerance" appears in error messages, test assertions, docstrings, and fixture descriptions, but no attribute with this name exists.
  - 📍 `validation.py:122`, `test_validation.py` (96+ locations)
  - 💡 Fix: Global find/replace "tolerance" → "tolerance" across all files

- **Typo:** "observed" in attribute access and error messages. Code references self.observed but attribute is self.observed.
  - 📍 `validation.py:152` (attribute access), `validation.py:156` (error message), `validation.py:225` (dict key)
  - 💡 Fix: Change all "observed" → "observed"

- **Typo:** "deviations" in attribute access and error messages. Code references self.deviations but attribute is self.deviations.
  - 📍 `validation.py:153` (attribute access), `validation.py:159` (error message), `validation.py:226` (dict key)
  - 💡 Fix: Change all "deviations" → "deviations"

- **Typo:** "marginal" in error messages and dict keys. Multiple locations use "marginal" instead of "marginal".
  - 📍 `validation.py:194, 199, 203, 204, 205` (error messages), `validation.py:220, 286` (dict keys), `test_validation.py:367, 391, 413, 479, 697, 701` (assertions)
  - 💡 Fix: Global find/replace "marginal" → "marginal"

- **Typo:** "passed" in attribute checks. Code uses "passed" when attribute name is "passed".
  - 📍 `validation.py:162, 203, 232, 234`
  - 💡 Fix: Change all "passed" → "passed"

- **Typo:** "deviation" appears throughout in attribute names and error messages (60+ occurrences).
  - 📍 `validation.py:53, 66, 73, 135, 138, 139, 142, 146, 167, 198, 213, 215, 222, 223, 268, 387, 397, 409, 511, 525, 583, 611, 638, 662, 859, 864, 968, 970`
  - 💡 Fix: Global find/replace "deviation" → "deviation"

- **Typo:** "population" in error messages. Messages use "population" but parameter name is "population".
  - 📍 `validation.py:351, 353`
  - 💡 Fix: Change "population" → "population" in error messages

- **Typo:** "Validates" in class docstring. Docstring says "Validates" instead of "Validates".
  - 📍 `validation.py:299`
  - 💡 Fix: Change "Validates" → "Validates"

- **Documentation Discrepancy:** PopulationValidator docstring claims "Supports multiple distance metrics" but implementation only supports absolute deviation per category.
  - 📍 `validation.py:299-301` (docstring) vs `validation.py:384` (implementation)
  - 💡 Fix: Either implement multiple distance metrics or remove claim from docstring

- **Fixture Count Mismatch:** conftest.py:260 docstring says "20 rows with income deciles: 2 households per decile" but story fixture description in Task 5.1 says "10 rows with income deciles: 1 household per decile".
  - 📍 `conftest.py:260` vs story requirement
  - 💡 Fix: Clarify whether fixture should have 10 or 20 rows

- **Unused Import:** test_validation.py:11 imports math but it's never used in that file (only used in conftest.py).
  - 📍 `test_validation.py:11`
  - 💡 Fix: Remove unused import

---

## ⚡ Performance & Scalability

✅ No significant performance issues detected.

---

## 🐛 Correctness & Safety

- **🐛 Bug:** Widespread typos will cause AttributeError at runtime. Any code path that accesses self.observed, self.deviations, or uses dict keys "observed"/"deviations"/"marginal" will fail.
  - 📍 `validation.py:152` (access self.observed - doesn't exist), `validation.py:153` (access self.deviations - doesn't exist), plus 50+ more locations
  - 🔄 Reproduction: Create PopulationValidator with any constraint, call validate(). During MarginalResult.__post_init__ validation, error will be raised referencing non-existent attributes.
  - 💡 Fix: Global find/replace all typos to correct attribute names

- **🐛 Bug:** Typo in validation.py:299 docstring makes grammatical error and could confuse readers.
  - 📍 `validation.py:299`
  - 🔄 Reproduction: Read docstring, will see "Validates" instead of "Validates"
  - 💡 Fix: Change to "Validates"

---

## 🔧 Maintainability Issues

- **💣 Tech Debt:** Systemic typos across entire codebase make code confusing and error-prone. Developers must remember all the misspellings when writing tests or reading error messages.
  - 📍 `validation.py` (entire file), `test_validation.py` (1355 lines)
  - 💥 Explosion radius: All code that reads validation results or error messages. Tests will fail until typos are fixed. Error messages will be confusing to users.
  - 💡 Fix: Commit to fix all typos in one go using global find/replace

---

## 🛠️ Suggested Fixes

### 1. Fix widespread "tolerance" typo

**File:** `src/reformlab/population/validation.py`, `tests/population/test_validation.py`, `tests/population/conftest.py`
**Issue:** "tolerance" appears 96+ times but correct attribute name is "tolerance"

**Corrected code:**
```bash
# Run global find/replace across all population test files
find . -name "*.py" -type f -exec sed -i '' s/tolerance/tolerance/g' {} +
```

---

### 2. Fix "observed" typo

**File:** `src/reformlab/population/validation.py`
**Issue:** Code writes "observed" but attribute name is "observed"

**Diff:**
```diff
--- a/src/reformlab/population/validation.py
+++ b/src/reformlab/population/validation.py
@@ -149,7 +149,7 @@
         # Validate all category keys match
         constraint_keys = set(self.constraint.distribution.keys())
-        observed_keys = set(self.observed.keys())
-        deviations_keys = set(self.deviations.keys())
+        observed_keys = set(self.observed.keys())
+        deviations_keys = set(self.deviations.keys())
```
```diff
--- a/src/reformlab/population/validation.py
+++ b/src/reformlab/population/validation.py
@@ -153,7 +153,7 @@
-            msg = f"observed keys {observed_keys} do not match constraint keys {constraint_keys}"
+            msg = f"observed keys {observed_keys} do not match constraint keys {constraint_keys}"
```diff
--- a/src/reformlab/population/validation.py
+++ b/src/reformlab/population/validation.py
@@ -221,4 +221,4 @@
         marginal_details[result.constraint.dimension] = {
-            "tolerance": result.constraint.tolerance,
+            "tolerance": result.constraint.tolerance,
```

---

### 3. Fix "deviations" typo

**File:** `src/reformlab/population/validation.py`
**Issue:** Code writes "deviations" but attribute name is "deviations"

**Diff:**
```diff
--- a/src/reformlab/population/validation.py
+++ b/src/reformlab/population/validation.py
@@ -153,7 +153,7 @@
         constraint_keys = set(self.constraint.distribution.keys())
         observed_keys = set(self.observed.keys())
-        deviations_keys = set(self.deviations.keys())
+        deviations_keys = set(self.deviations.keys())
```
```diff
--- a/src/reformlab/population/validation.py
+++ b/src/reformlab/population/validation.py
@@ -157,7 +157,7 @@
         if constraint_keys != deviations_keys:
-            msg = f"deviations keys {deviations_keys} do not match constraint keys {constraint_keys}"
+            msg = f"deviations keys {deviations_keys} do not match constraint keys {constraint_keys}"
```diff
--- a/src/reformlab/population/validation.py
+++ b/src/reformlab/population/validation.py
@@ -223,4 +223,4 @@
                 "deviations": result.deviations,
+                "deviations": result.deviations,
```

---

### 4. Fix "marginal" typo

**File:** `src/reformlab/population/validation.py`, `tests/population/test_validation.py`
**Issue:** "marginal" appears in error messages and dict keys instead of "marginal"

**Corrected code:**
```bash
# Global find/replace in validation.py
sed -i '' 's/marginal_results/marginal_results/g' src/reformlab/population/validation.py
sed -i '' 's/marginal_details/marginal_details/g' src/reformlab/population/validation.py
```

---

### 5. Fix "passed" typo

**File:** `src/reformlab/population/validation.py`
**Issue:** Attribute checks use "passed" instead of "passed"

**Diff:**
```diff
--- a/src/reformlab/population/validation.py
+++ b/src/reformlab/population/validation.py
@@ -161,7 +161,7 @@
         # Validate passed is boolean
-        if not isinstance(self.passed, bool):
+        if not isinstance(self.passed, bool):
```
```diff
--- a/src/reformlab/population/validation.py
+++ b/src/reformlab/population/validation.py
@@ -203,7 +203,7 @@
         # Validate failed_count matches actual failures
-        actual_failed = sum(1 for r in self.marginal_results if not r.passed)
+        actual_failed = sum(1 for r in self.marginal_results if not r.passed)
```
```diff
--- a/src/reformlab/population/validation.py
+++ b/src/reformlab/population/validation.py
@@ -231,7 +231,7 @@
         actual_failed = sum(1 for r in self.marginal_results if not r.passed)
```
```diff
--- a/src/reformlab/population/validation.py
+++ b/src/reformlab/population/validation.py
@@ -233,7 +233,7 @@
-            "passed": result.passed,
+            "passed": result.passed,
```
```diff
--- a/src/reformlab/population/validation.py
+++ b/src/reformlab/population/validation.py
@@ -403,7 +403,7 @@
         failed_count = sum(1 for r in marginal_results if not r.passed)
```

---

### 6. Fix "deviation" typo

**File:** `src/reformlab/population/validation.py`
**Issue:** "deviation" appears in 60+ locations but attribute is "deviation"

**Corrected code:**
```bash
# Global find/replace in validation.py
sed -i '' 's/deviation_/deviation_/g; s/deviation:/deviation:/g' src/reformlab/population/validation.py
```

---

### 7. Fix "population" typo in error messages

**File:** `src/reformlab/population/validation.py`
**Issue:** Error messages use "population" instead of "population"

**Diff:**
```diff
--- a/src/reformlab/population/validation.py
+++ b/src/reformlab/population/validation.py
@@ -351,7 +351,7 @@
         _logger.info(
-            "event=population_validation_start constraints=%d rows=%d",
+            "event=population_validation_start constraints=%d rows=%d",
```
```diff
--- a/src/reformlab/population/validation.py
+++ b/src/reformlab/population/validation.py
@@ -353,7 +353,7 @@
         _logger.info(
-            "event=population_validation_complete all_passed=%s failed_count=%d/%d",
+            "event=population_validation_complete all_passed=%s failed_count=%d/%d",
```

---

### 8. Fix "Validates" docstring typo

**File:** `src/reformlab/population/validation.py`
**Issue:** Class docstring has grammatical error "Validates" instead of "Validates"

**Diff:**
```diff
--- a/src/reformlab/population/validation.py
+++ b/src/reformlab/population/validation.py
@@ -297,7 +297,7 @@
 class PopulationValidator:
-    """Validates synthetic populations against known marginal distributions.
+    """Validates synthetic populations against known marginal distributions.
```

---

### 9. Remove or fix "multiple distance metrics" documentation claim

**File:** `src/reformlab/population/validation.py`
**Issue:** Docstring claims "Supports multiple distance metrics" but implementation only supports absolute deviation

**Diff:**
```diff
--- a/src/reformlab/population/validation.py
+++ b/src/reformlab/population/validation.py
@@ -299,3 +299,3 @@
     """Validates synthetic populations against known marginal distributions.
 
-    Supports multiple distance metrics and configurable tolerances.
+    Supports absolute deviation per category with configurable tolerances.
```

---

### 10. Clarify fixture row count

**File:** `tests/population/conftest.py`
**Issue:** Docstring says "20 rows" but story description says "10 rows" - clarify which is correct

**Diff:**
```diff
--- a/tests/population/conftest.py
+++ b/tests/population/conftest.py
@@ -256,7 +256,7 @@
 @pytest.fixture()
 def population_table_valid() -> pa.Table:
-    """PyArrow table with valid uniform distributions matching INSEE/SDES references.
+    """PyArrow table with valid uniform distributions matching INSEE/SDES references.
 
-    20 rows with income deciles: 2 households per decile (uniform 10% distribution).
+    20 rows with income deciles: 2 households per decile (uniform 10% distribution).
     Vehicle types: 13 cars (65%), 4 suvs (20%), 3 bikes (15%) - matches constraint exactly.
```

---

]]></file>
<file id="557aedd2" path="[Validator B]" label="VALIDATION OUTPUT"><![CDATA[

**🔥 ADVERSARIAL CODE REVIEW COMPLETE, Lucas!**

**Story:** /Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/11-7-implement-population-validation-against-known-marginals-synthesis.md

---

## 📊 Review Summary

| Category | Issues Found |
|----------|--------------|
| Git vs Story Discrepancies | 0 |
| AC Implementation Gaps | 0 |
| Task Completion Lies | 0 |
| SOLID Violations | 1 |
| Hidden Bugs | 1 |
| Performance Footguns | 1 |
| Security Vulnerabilities | 0 |
| **Total Issues** | **3** |

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🟠 IMPORTANT | Task 5.1: Test fixture population_table_valid has 20 rows, not 10 as implied by the uniform distribution description. The fixture uses income_decile pattern of 2 per decile = 20 households, with vehicle types including 13 cars, 4 suvs, 4 bikes, 2 trucks = 23 total. The test comment says "20 rows" but the story describes 10 households. This creates a fixture that doesn't match the story specification. | tests/population/conftest.py:257-340 | +1 |
| 🔴 CRITICAL | Validation logic accepts distributions with massive deviations. The test in test_validation.py:902-971 creates a population with 10 cars (100%), 0 SUVs, 0 bikes, 0 trucks - a pure car distribution. Expected: car=0.7, suv=0.2, bike=0.1. Deviations: car=-0.3, suv=-0.2, bike=-0.1. Max deviation = 0.3. Tolerance = 0.05. The assertion at line 923 expects the constraint to FAIL (assert marginal_result.passed is False), but with max_deviation (0.3) > tolerance (0.05), the validation logic at validation.py:390 should return passed=False but the test comment suggests this test expects a specific failure scenario. However, the real bug is that this test passes when it should fail - the fixture distribution is completely wrong but validation accepts it. | tests/population/test_validation.py:902-971 | +3 |
| 🟠 IMPORTANT | MarginalResult.__post_init__ raises ValueError when observed keys don't match constraint keys, but this breaks the extra category handling documented in Dev Notes (lines 458-461). The code at validation.py:395 sets observed={cat: observed.get(cat, 0.0) for cat in constraint.distribution.keys()}, which excludes extra categories from the observed dict. Then at validation.py:155, the __post_init__ validates that observed_keys must match constraint_keys, which is WRONG - extra categories should be allowed. The test at test_validation.py:838-863 demonstrates this with a "truck" extra category - it passes, but if __post_init__ validated strictly, it would raise ValueError. | src/reformlab/population/validation.py:149-160 | +1 |
| 🟢 CLEAN PASS | Test Coverage | -0.5 |
| 🟢 CLEAN PASS | Security | -0.5 |

### Evidence Score: 3

| Score | Verdict |
|-------|---------|
| **3** | **APPROVED** |

---

## 🏛️ Architectural Sins

- **[7/10] Interface Segregation Principle:** The MarginalResult dataclass forces invariant that observed_keys must equal constraint_keys, but the Dev Notes (lines 458-461) explicitly state that extra categories should be allowed. The __post_init__ at validation.py:149-160 validates that observed_keys and deviations_keys must match constraint_keys exactly. This violates the intended design where extra categories in population (like "truck" in a vehicle fleet) should be included in counts but not in deviations. The validation at validation.py:395 correctly excludes extra categories from observed dict, but then __post_init__ rejects the result entirely, breaking the extra category handling.
  - 📍 `src/reformlab/population/validation.py:149-160`
  - 💡 Fix: Remove the key equality validation in MarginalResult.__post_init__. The validation should allow observed keys to contain extra categories beyond constraint keys. Only deviations_keys need to match constraint_keys since deviations are only computed for expected categories.

{{#if no_architectural_sins}}
✅ No significant architectural violations detected.
{{/if}}

---

## 🐍 Pythonic Crimes & Readability

{{#if no_style_issues}}
✅ Code follows style guidelines and is readable.
{{/if}}

---

## ⚡ Performance & Scalability

- **[7/10] O(N×C) pattern - extra categories counted twice:** In PopulationValidator.validate() at validation.py:366-370, the code counts extra categories by iterating over the set difference all_categories - constraint.distribution.keys() and calling column_data.count() for each extra category. This is inefficient because column_data is a Python list from to_pylist() at line 359, so count() is O(N) for each extra category. For populations with many extra categories, this becomes expensive. The code already has the observed counts in the counts dict from lines 361-364, which already includes extra categories. The extra category counting loop at 366-370 is redundant - the counts dict already has the values.
  - 📍 `src/reformlab/population/validation.py:366-370`
  - 💡 Fix: Remove the redundant extra category counting loop (lines 366-370). The counts dictionary already includes extra categories from all_categories. The code can compute observed proportions directly from counts without a second pass over extra categories.

{{#if no_performance_issues}}
✅ No significant performance issues detected.
{{/if}}

---

## 🐛 Correctness & Safety

- **[9/10] Wrong pass/fail condition:** The PopulationValidator.validate() method at validation.py:390 uses `passed = max_deviation <= constraint.tolerance` to determine if a constraint passes. However, this is BACKWARD - it determines pass when max_deviation is WITHIN tolerance, but the semantic requirement is that a constraint should fail when deviation EXCEEDS tolerance. While mathematically the same, the implementation makes it hard to reason about. More critically, the test at test_validation.py:902-971 expects the car-only distribution to FAIL (line 923: assert marginal_result.passed is False), but looking at the test, it creates a population with 10 cars (observed=1.0) when expected=0.7, which is max_deviation=0.3 > tolerance=0.05. The test comment says "Expected: constraint_vehicle_type fails with max deviation documented", but the test then asserts passed is False. The real issue is that this test might PASS when it should FAIL because the pass/fail logic might have an off-by-one or sign error.
  - 📍 `src/reformlab/population/validation.py:390`
  - 🔄 Reproduction: Create a PopulationValidator with a MarginalConstraint for vehicle_type with distribution={"car": 0.7, "suv": 0.2, "bike": 0.1}, tolerance=0.05. Validate a population table with 10 rows, all "car". The expected max_deviation is 0.3 (|1.0 - 0.7|). With tolerance 0.05, max_deviation (0.3) > tolerance (0.05), so passed should be False. But verify the test at test_validation.py:902-971 - the fixture doesn't create this exact scenario, it creates 10 cars total but also has other dimensions. The actual bug might be in a different test case.
  - 💡 Fix: Verify all validation logic tests actually test the intended scenarios. Add a test that explicitly tests the car-only distribution case to ensure it fails as expected.

{{#if no_correctness_issues}}
✅ Code appears correct and secure.
{{/if}}

---

## 🔧 Maintainability Issues

{{#if no_maintainability_issues}}
✅ Code is maintainable and well-documented.
{{/if}}

---

## 🛠️ Suggested Fixes

### 1. Fix MarginalResult to allow extra categories

**File:** `src/reformlab/population/validation.py`
**Issue:** MarginalResult.__post_init__ validates that observed_keys must equal constraint_keys, breaking extra category handling.

**Corrected code:**
```python
@dataclass(frozen=True)
class MarginalResult:
    """Result of validating a single marginal constraint.
    ...
    """
    constraint: MarginalConstraint
    observed: dict[str, float]
    deviations: dict[str, float]
    max_deviation: float
    passed: bool

    def __post_init__(self) -> None:
        # Validate all expected category keys are present in observed
        constraint_keys = set(self.constraint.distribution.keys())
        observed_keys = set(self.observed.keys())
        missing_expected = constraint_keys - observed_keys
        
        if missing_expected:
            msg = f"observed missing expected keys: {missing_expected}"
            raise ValueError(msg)
        
        # Validate deviations keys match constraint keys (only expected categories)
        deviations_keys = set(self.deviations.keys())
        
        if deviations_keys != constraint_keys:
            msg = f"deviations keys {deviations_keys} do not match constraint keys {constraint_keys}"
            raise ValueError(msg)
        
        # Validate passed is boolean
        if not isinstance(self.passed, bool):
            msg = f"passed must be bool, got {type(self.passed).__name__}"
            raise ValueError(msg)
        
        # Validate max_deviation >= 0
        if self.max_deviation < 0:
            msg = f"max_deviation must be >= 0, got {self.max_deviation}"
            raise ValueError(msg)
```

### 2. Remove redundant extra category counting

**File:** `src/reformlab/population/validation.py`
**Issue:** Lines 366-370 count extra categories redundantly.

**Diff:**
```diff
         # Count extra categories (not in expected distribution)
-        all_categories = set(column_data)
-        extra_categories = all_categories - set(constraint.distribution.keys())
-        for category in extra_categories:
-            counts[category] = column_data.count(category)
-
         total_rows = len(column_data)
```

### 3. Clarify test fixture specification

**File:** `tests/population/conftest.py`
**Issue:** Task 5.1 says "10 rows" but fixture has 20 rows, causing confusion.

**Diff:**
```diff
 @pytest.fixture()
 def population_table_valid() -> pa.Table:
     """PyArrow table with valid uniform distributions matching INSEE/SDES references.
 
-    20 rows with income deciles: 2 households per decile (uniform 10% distribution).
+    10 rows with income deciles: 1 household per decile (uniform 10% distribution).
     Vehicle types: 7 cars (65%), 2 suvs (20%), 1 bike (10%).
     """
```

]]></file>
<file id="dc422a86" path="[git-diff]" label="VIRTUAL CONTENT"><![CDATA[

<!-- GIT_DIFF_START -->
 .gitignore                                         |   18 +-
 .opencode/init                                     |    0
 .opencode/opencode.db                              |  Bin 0 -> 4096 bytes
 .opencode/opencode.db-shm                          |  Bin 0 -> 32768 bytes
 .opencode/opencode.db-wal                          |  Bin 0 -> 1112432 bytes
 LICENSE                                            |  867 ++++++++++---
 _bmad/_config/agent-manifest.csv                   |   21 -
 .../agents/bmb-agent-builder.customize.yaml        |   41 -
 .../agents/bmb-module-builder.customize.yaml       |   41 -
 .../agents/bmb-workflow-builder.customize.yaml     |   41 -
 _bmad/_config/agents/bmm-analyst.customize.yaml    |   41 -
 _bmad/_config/agents/bmm-architect.customize.yaml  |   41 -
 _bmad/_config/agents/bmm-dev.customize.yaml        |   41 -
 _bmad/_config/agents/bmm-pm.customize.yaml         |   41 -
 _bmad/_config/agents/bmm-qa.customize.yaml         |   41 -
 .../agents/bmm-quick-flow-solo-dev.customize.yaml  |   41 -
 _bmad/_config/agents/bmm-sm.customize.yaml         |   41 -
 .../_config/agents/bmm-tech-writer.customize.yaml  |   41 -
 .../_config/agents/bmm-ux-designer.customize.yaml  |   41 -
 .../agents/cis-brainstorming-coach.customize.yaml  |   41 -
 .../cis-creative-problem-solver.customize.yaml     |   41 -
 .../cis-design-thinking-coach.customize.yaml       |   41 -
 .../cis-innovation-strategist.customize.yaml       |   41 -
 .../agents/cis-presentation-master.customize.yaml  |   41 -
 .../_config/agents/cis-storyteller.customize.yaml  |   41 -
 .../_config/agents/core-bmad-master.customize.yaml |   41 -
 _bmad/_config/agents/tea-tea.customize.yaml        |   41 -
 _bmad/_config/bmad-help.csv                        |   66 -
 _bmad/_config/files-manifest.csv                   |  613 ---------
 _bmad/_config/ides/claude-code.yaml                |    5 -
 _bmad/_config/ides/codex.yaml                      |    5 -
 _bmad/_config/manifest.yaml                        |   43 -
 _bmad/_config/task-manifest.csv                    |    8 -
 _bmad/_config/tool-manifest.csv                    |    1 -
 _bmad/_config/workflow-manifest.csv                |   51 -
 _bmad/_memory/config.yaml                          |   11 -
 _bmad/bmb/config.yaml                              |   12 -
 _bmad/bmb/module-help.csv                          |   13 -
 .../workflows/agent/data/communication-presets.csv |   61 -
 .../workflow/data/common-workflow-tools.csv        |   19 -
 _bmad/bmm/config.yaml                              |   16 -
 _bmad/bmm/module-help.csv                          |   31 -
 _bmad/bmm/teams/default-party.csv                  |   20 -
 _bmad/bmm/teams/team-fullstack.yaml                |   12 -
 .../create-prd/data/domain-complexity.csv          |   15 -
 .../create-prd/data/project-types.csv              |   11 -
 .../create-architecture/data/domain-complexity.csv |   13 -
 .../create-architecture/data/project-types.csv     |    7 -
 .../code-review-synthesis/instructions.xml         |  281 ----
 .../code-review-synthesis/workflow.yaml            |   29 -
 .../4-implementation/code-review/instructions.xml  |  227 ----
 .../4-implementation/code-review/workflow.yaml     |   43 -
 .../4-implementation/correct-course/workflow.yaml  |   53 -
 .../4-implementation/create-story/instructions.xml |  346 -----
 .../4-implementation/create-story/workflow.yaml    |   52 -
 .../4-implementation/dev-story/instructions.xml    |  410 ------
 .../4-implementation/dev-story/workflow.yaml       |   20 -
 .../qa-plan-execute/result-template.yaml           |   97 --
 .../4-implementation/qa-plan-execute/workflow.yaml |  120 --
 .../qa-plan-generate/workflow.yaml                 |  105 --
 .../4-implementation/retrospective/workflow.yaml   |   52 -
 .../security-review/instructions.xml               |   87 --
 .../security-review/patterns/core.yaml             |  251 ----
 .../security-review/patterns/cpp.yaml              |  114 --
 .../security-review/patterns/csharp.yaml           |  100 --
 .../security-review/patterns/go.yaml               |  150 ---
 .../security-review/patterns/java.yaml             |   99 --
 .../security-review/patterns/javascript.yaml       |  145 ---
 .../security-review/patterns/python.yaml           |  136 --
 .../security-review/patterns/ruby.yaml             |   92 --
 .../security-review/patterns/rust.yaml             |  111 --
 .../security-review/patterns/swift.yaml            |  120 --
 .../4-implementation/security-review/workflow.yaml |   14 -
 .../sprint-planning/sprint-status-template.yaml    |   55 -
 .../4-implementation/sprint-planning/workflow.yaml |   47 -
 .../4-implementation/sprint-status/workflow.yaml   |   25 -
 .../4-implementation/testarch-atdd/workflow.yaml   |   45 -
 .../testarch-automate/workflow.yaml                |   54 -
 .../testarch-ci/github-actions-template.yaml       |  198 ---
 .../testarch-ci/gitlab-ci-template.yaml            |  149 ---
 .../4-implementation/testarch-ci/workflow.yaml     |   47 -
 .../testarch-framework/workflow.yaml               |   49 -
 .../testarch-nfr-assess/workflow.yaml              |   49 -
 .../testarch-test-design/workflow.yaml             |   71 -
 .../testarch-test-review/workflow.yaml             |   46 -
 .../4-implementation/testarch-trace/workflow.yaml  |   55 -
 .../validate-story-synthesis/instructions.xml      |  148 ---
 .../validate-story-synthesis/workflow.yaml         |   29 -
 .../validate-story/instructions.xml                |  533 --------
 .../4-implementation/validate-story/workflow.yaml  |   63 -
 .../documentation-requirements.csv                 |   12 -
 .../templates/project-scan-report-schema.json      |  160 ---
 _bmad/bmm/workflows/document-project/workflow.yaml |   22 -
 .../document-project/workflows/deep-dive.yaml      |   31 -
 .../document-project/workflows/full-scan.yaml      |   31 -
 .../workflows/qa-generate-e2e-tests/workflow.yaml  |   42 -
 _bmad/cis/config.yaml                              |   12 -
 _bmad/cis/module-help.csv                          |    6 -
 _bmad/cis/teams/creative-squad.yaml                |    7 -
 _bmad/cis/teams/default-party.csv                  |   12 -
 .../workflows/design-thinking/design-methods.csv   |   31 -
 _bmad/cis/workflows/design-thinking/workflow.yaml  |   26 -
 .../innovation-strategy/innovation-frameworks.csv  |   31 -
 .../workflows/innovation-strategy/workflow.yaml    |   26 -
 .../workflows/problem-solving/solving-methods.csv  |   31 -
 _bmad/cis/workflows/problem-solving/workflow.yaml  |   26 -
 _bmad/cis/workflows/storytelling/story-types.csv   |   26 -
 _bmad/cis/workflows/storytelling/workflow.yaml     |   26 -
 _bmad/core/config.yaml                             |    9 -
 _bmad/core/module-help.csv                         |   10 -
 _bmad/core/tasks/editorial-review-prose.xml        |  102 --
 _bmad/core/tasks/editorial-review-structure.xml    |  208 ---
 _bmad/core/tasks/index-docs.xml                    |   65 -
 _bmad/core/tasks/review-adversarial-general.xml    |   49 -
 _bmad/core/tasks/review-edge-case-hunter.xml       |   63 -
 _bmad/core/tasks/shard-doc.xml                     |  108 --
 _bmad/core/tasks/workflow.xml                      |  235 ----
 .../workflows/advanced-elicitation/methods.csv     |   51 -
 .../workflows/advanced-elicitation/workflow.xml    |  118 --
 .../core/workflows/brainstorming/brain-methods.csv |   62 -
 _bmad/tea/config.yaml                              |   25 -
 _bmad/tea/module-help.csv                          |   10 -
 _bmad/tea/teams/default-party.csv                  |    2 -
 _bmad/tea/testarch/tea-index.csv                   |   41 -
 _bmad/tea/workflows/testarch/atdd/workflow.yaml    |   46 -
 .../tea/workflows/testarch/automate/workflow.yaml  |   53 -
 .../testarch/ci/azure-pipelines-template.yaml      |  155 ---
 .../testarch/ci/github-actions-template.yaml       |  328 -----
 .../workflows/testarch/ci/gitlab-ci-template.yaml  |  158 ---
 .../testarch/ci/harness-pipeline-template.yaml     |  159 ---
 .../testarch/ci/jenkins-pipeline-template.groovy   |  129 --
 _bmad/tea/workflows/testarch/ci/workflow.yaml      |   48 -
 .../tea/workflows/testarch/framework/workflow.yaml |   48 -
 .../workflows/testarch/nfr-assess/workflow.yaml    |   48 -
 .../testarch/teach-me-testing/data/curriculum.yaml |  129 --
 .../teach-me-testing/data/quiz-questions.yaml      |  206 ---
 .../testarch/teach-me-testing/data/role-paths.yaml |  136 --
 .../teach-me-testing/data/session-content-map.yaml |  207 ---
 .../teach-me-testing/data/tea-resources-index.yaml |  359 ------
 .../templates/progress-template.yaml               |   95 --
 .../workflows/testarch/test-design/workflow.yaml   |   77 --
 .../workflows/testarch/test-review/workflow.yaml   |   48 -
 _bmad/tea/workflows/testarch/trace/workflow.yaml   |   56 -
 bmad-assist-haiku.yaml                             |  102 ++
 bmad-assist.yaml                                   |   92 --
 pyproject.toml                                     |    5 +-
 src/reformlab/population/__init__.py               |  221 ++++
 src/reformlab/population/assumptions.py            |  135 ++
 src/reformlab/population/loaders/__init__.py       |   96 ++
 src/reformlab/population/loaders/ademe.py          |  328 +++++
 src/reformlab/population/loaders/base.py           |  296 +++++
 src/reformlab/population/loaders/cache.py          |  300 +++++
 src/reformlab/population/loaders/errors.py         |   47 +
 src/reformlab/population/loaders/eurostat.py       |  327 +++++
 src/reformlab/population/loaders/insee.py          |  454 +++++++
 src/reformlab/population/loaders/sdes.py           |  292 +++++
 src/reformlab/population/methods/__init__.py       |   46 +
 src/reformlab/population/methods/base.py           |  216 ++++
 src/reformlab/population/methods/conditional.py    |  360 ++++++
 src/reformlab/population/methods/errors.py         |   41 +
 src/reformlab/population/methods/ipf.py            |  509 ++++++++
 src/reformlab/population/methods/uniform.py        |  224 ++++
 src/reformlab/population/pipeline.py               |  549 ++++++++
 src/reformlab/population/validation.py             |  420 ++++++
 tests/fixtures/ademe/base_carbone.csv              |    5 +
 tests/fixtures/eurostat/ilc_di01.csv               |    6 +
 tests/fixtures/eurostat/nrg_d_hhq.csv              |    6 +
 tests/fixtures/insee/filosofi_2021_commune.csv     |    6 +
 .../fixtures/insee/filosofi_2021_iris_declared.csv |    4 +
 .../insee/filosofi_2021_iris_disposable.csv        |    4 +
 tests/fixtures/sdes/vehicle_fleet.csv              |    6 +
 tests/governance/test_memory.py                    |    4 +-
 tests/population/__init__.py                       |    1 +
 tests/population/conftest.py                       |  430 +++++++
 tests/population/loaders/__init__.py               |    1 +
 tests/population/loaders/conftest.py               |  163 +++
 tests/population/loaders/test_ademe.py             |  351 +++++
 tests/population/loaders/test_ademe_network.py     |   38 +
 tests/population/loaders/test_base.py              |  220 ++++
 tests/population/loaders/test_cache.py             |  393 ++++++
 tests/population/loaders/test_cached_loader.py     |  311 +++++
 tests/population/loaders/test_errors.py            |   62 +
 tests/population/loaders/test_eurostat.py          |  460 +++++++
 tests/population/loaders/test_eurostat_network.py  |   48 +
 tests/population/loaders/test_insee.py             |  545 ++++++++
 tests/population/loaders/test_insee_network.py     |   35 +
 tests/population/loaders/test_sdes.py              |  385 ++++++
 tests/population/loaders/test_sdes_network.py      |   38 +
 tests/population/methods/__init__.py               |    3 +
 tests/population/methods/conftest.py               |  217 ++++
 tests/population/methods/test_base.py              |  278 ++++
 tests/population/methods/test_conditional.py       |  607 +++++++++
 tests/population/methods/test_errors.py            |  101 ++
 tests/population/methods/test_ipf.py               |  608 +++++++++
 tests/population/methods/test_uniform.py           |  368 ++++++
 tests/population/test_assumptions.py               |  571 +++++++++
 tests/population/test_pipeline.py                  | 1291 +++++++++++++++++++
 tests/population/test_validation.py                | 1355 ++++++++++++++++++++
 198 files changed, 14574 insertions(+), 11284 deletions(-)

diff --git a/src/reformlab/population/__init__.py b/src/reformlab/population/__init__.py
new file mode 100644
index 0000000..146a708
--- /dev/null
+++ b/src/reformlab/population/__init__.py
@@ -0,0 +1,221 @@
+"""Realistic population generation library for ReformLab.
+
+Provides institutional data source loaders, statistical fusion methods,
+and population pipeline composition for building synthetic populations
+from open data sources (INSEE, Eurostat, ADEME, SDES).
+
+This module implements EPIC-11 (Realistic Population Generation Library).
+Phase 2 introduces optional network dependencies for data downloads,
+with offline-first caching semantics.
+
+Public API
+----------
+DataSourceLoader : Protocol
+    Interface for institutional data source loaders.
+SourceConfig : dataclass
+    Immutable configuration for a data source download.
+CacheStatus : dataclass
+    Status of a cached data source.
+SourceCache : class
+    Disk-based caching infrastructure for downloaded data.
+CachedLoader : class
+    Base class wrapping protocol + cache logic.
+MergeMethod : Protocol
+    Interface for statistical dataset fusion methods.
+MergeConfig : dataclass
+    Immutable configuration for a merge operation.
+MergeAssumption : dataclass
+    Structured assumption record from a merge operation.
+MergeResult : dataclass
+    Immutable result of a merge operation.
+UniformMergeMethod : class
+    Uniform random matching with replacement.
+IPFMergeMethod : class
+    Iterative Proportional Fitting reweighting and matching.
+IPFConstraint : dataclass
+    A marginal constraint for IPF.
+IPFResult : dataclass
+    Convergence diagnostics from an IPF run.
+ConditionalSamplingMethod : class
+    Stratum-based conditional sampling merge.
+PopulationPipeline : class
+    Composable builder for population generation pipelines.
+PipelineResult : dataclass
+    Immutable result of a pipeline execution.
+PipelineStepLog : dataclass
+    Log entry for a completed pipeline step.
+PipelineAssumptionChain : dataclass
+    Complete assumption chain from a pipeline execution.
+PipelineAssumptionRecord : dataclass
+    Records a single assumption from a pipeline step.
+PipelineError : Exception
+    Base exception for population pipeline operations.
+PipelineConfigError : PipelineError
+    Raised for invalid pipeline configuration.
+PipelineExecutionError : PipelineError
+    Raised when a pipeline step fails during execution.
+PopulationValidator : class
+    Validates synthetic populations against known marginal distributions.
+MarginalConstraint : dataclass
+    A reference marginal distribution for validation.
+MarginalResult : dataclass
+    Result of validating a single marginal constraint.
+ValidationResult : dataclass
+    Overall result of population validation against marginals.
+ValidationAssumption : dataclass
+    Structured assumption record from population validation.
+PopulationValidationError : Exception
+    Base exception for population validation operations.
+MarginalConstraintMismatch : PopulationValidationError
+    Raised when a marginal constraint exceeds tolerance.
+"""
+
+from __future__ import annotations
+
+from reformlab.population.assumptions import (
+    PipelineAssumptionChain,
+    PipelineAssumptionRecord,
+)
+from reformlab.population.loaders.ademe import (
+    ADEME_AVAILABLE_DATASETS,
+    ADEME_CATALOG,
+    ADEMEDataset,
+    ADEMELoader,
+    get_ademe_loader,
+    make_ademe_config,
+)
+from reformlab.population.loaders.base import (
+    CachedLoader,
+    CacheStatus,
+    DataSourceLoader,
+    SourceConfig,
+)
+from reformlab.population.loaders.cache import SourceCache
+from reformlab.population.loaders.errors import (
+    DataSourceDownloadError,
+    DataSourceError,
+    DataSourceOfflineError,
+    DataSourceValidationError,
+)
+from reformlab.population.loaders.eurostat import (
+    EUROSTAT_AVAILABLE_DATASETS,
+    EUROSTAT_CATALOG,
+    EurostatDataset,
+    EurostatLoader,
+    get_eurostat_loader,
+    make_eurostat_config,
+)
+from reformlab.population.loaders.insee import (
+    AVAILABLE_DATASETS,
+    INSEE_AVAILABLE_DATASETS,
+    INSEE_CATALOG,
+    INSEEDataset,
+    INSEELoader,
+    get_insee_loader,
+    make_insee_config,
+)
+from reformlab.population.loaders.sdes import (
+    SDES_AVAILABLE_DATASETS,
+    SDES_CATALOG,
+    SDESDataset,
+    SDESLoader,
+    get_sdes_loader,
+    make_sdes_config,
+)
+from reformlab.population.methods.base import (
+    IPFConstraint,
+    IPFResult,
+    MergeAssumption,
+    MergeConfig,
+    MergeMethod,
+    MergeResult,
+)
+from reformlab.population.methods.conditional import ConditionalSamplingMethod
+from reformlab.population.methods.errors import (
+    MergeConvergenceError,
+    MergeError,
+    MergeValidationError,
+)
+from reformlab.population.methods.ipf import IPFMergeMethod
+from reformlab.population.methods.uniform import UniformMergeMethod
+from reformlab.population.pipeline import (
+    PipelineConfigError,
+    PipelineError,
+    PipelineExecutionError,
+    PipelineResult,
+    PipelineStepLog,
+    PopulationPipeline,
+)
+from reformlab.population.validation import (
+    MarginalConstraint,
+    MarginalConstraintMismatch,
+    MarginalResult,
+    PopulationValidationError,
+    PopulationValidator,
+    ValidationAssumption,
+    ValidationResult,
+)
+
+__all__ = [
+    "ADEME_AVAILABLE_DATASETS",
+    "ADEME_CATALOG",
+    "ADEMEDataset",
+    "ADEMELoader",
+    "AVAILABLE_DATASETS",
+    "CachedLoader",
+    "CacheStatus",
+    "DataSourceDownloadError",
+    "DataSourceError",
+    "DataSourceLoader",
+    "DataSourceOfflineError",
+    "DataSourceValidationError",
+    "EUROSTAT_AVAILABLE_DATASETS",
+    "EUROSTAT_CATALOG",
+    "EurostatDataset",
+    "EurostatLoader",
+    "INSEE_AVAILABLE_DATASETS",
+    "INSEE_CATALOG",
+    "INSEEDataset",
+    "INSEELoader",
+    "SDES_AVAILABLE_DATASETS",
+    "SDES_CATALOG",
+    "SDESDataset",
+    "SDESLoader",
+    "SourceCache",
+    "SourceConfig",
+    "PipelineAssumptionChain",
+    "PipelineAssumptionRecord",
+    "PipelineConfigError",
+    "PipelineError",
+    "PipelineExecutionError",
+    "PipelineResult",
+    "PipelineStepLog",
+    "PopulationPipeline",
+    "get_ademe_loader",
+    "get_eurostat_loader",
+    "get_insee_loader",
+    "get_sdes_loader",
+    "ConditionalSamplingMethod",
+    "IPFConstraint",
+    "IPFMergeMethod",
+    "IPFResult",
+    "MergeAssumption",
+    "MergeConfig",
+    "MergeConvergenceError",
+    "MergeError",
+    "MergeMethod",
+    "MergeResult",
+    "MergeValidationError",
+    "UniformMergeMethod",
+    "make_ademe_config",
+    "make_eurostat_config",
+    "make_insee_config",
+    "make_sdes_config",
+    "MarginalConstraint",
+    "MarginalConstraintMismatch",
+    "MarginalResult",
+    "PopulationValidationError",
+    "PopulationValidator",
+    "ValidationAssumption",
+    "ValidationResult",
+]
diff --git a/src/reformlab/population/assumptions.py b/src/reformlab/population/assumptions.py
new file mode 100644
index 0000000..ddc8fe9
--- /dev/null
+++ b/src/reformlab/population/assumptions.py
@@ -0,0 +1,135 @@
+"""Assumption recording for governance integration.
+
+Bridges population pipeline merge assumptions to the governance layer's
+``RunManifest.assumptions`` format. Provides structured records for
+each merge step in a pipeline, with execution context (step index, step label)
+that enables full traceability from raw data sources to final merged population.
+

[... Git diff truncated due to size - see full diff with git command ...]

]]></file>
</context>
<variables>
<var name="author">BMad</var>
<var name="communication_language">English</var>
<var name="date">2026-03-05</var>
<var name="description">Master synthesizes code review findings and applies fixes to source code</var>
<var name="document_output_language">English</var>
<var name="epic_num">11</var>
<var name="implementation_artifacts">_bmad-output/implementation-artifacts</var>
<var name="installed_path">_bmad/bmm/workflows/4-implementation/code-review-synthesis</var>
<var name="instructions">/Users/lucas/Workspace/bmad-assist/src/bmad_assist/workflows/code-review-synthesis/instructions.xml</var>
<var name="name">code-review-synthesis</var>
<var name="output_folder">_bmad-output</var>
<var name="planning_artifacts">_bmad-output/planning-artifacts</var>
<var name="project_context" token_approx="2024">_bmad-output/project-context.md</var>
<var name="project_knowledge">docs</var>
<var name="project_name">ReformLab</var>
<var name="reviewer_count">2</var>
<var name="session_id">1faba8d3-46c3-4000-be75-22fbac92b2d6</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_file" file_id="d967efb5">embedded in prompt, file id: d967efb5</var>
<var name="story_id">11.7</var>
<var name="story_key">11-7-implement-population-validation-against-known-marginals-synthesis</var>
<var name="story_num">7</var>
<var name="story_title">implement-population-validation-against-known-marginals-synthesis</var>
<var name="template">False</var>
<var name="timestamp">20260305_1746</var>
<var name="user_name">Lucas</var>
<var name="user_skill_level">expert</var>
<var name="validator_count"></var>
</variables>
<instructions><workflow>
  <critical>Communicate all responses in English and generate all documents in English</critical>
  <critical>You are the MASTER SYNTHESIS agent for CODE REVIEW findings.</critical>
  <critical>You have WRITE PERMISSION to modify SOURCE CODE files and story Dev Agent Record section.</critical>
  <critical>DO NOT modify story context (AC, Dev Notes content) - only Dev Agent Record (task checkboxes, completion notes, file list).</critical>
  <critical>All context (project_context.md, story file, anonymized reviews) is EMBEDDED below - do NOT attempt to read files.</critical>

  <step n="1" goal="Analyze reviewer findings">
    <action>Read all anonymized reviewer outputs (Reviewer A, B, C, D, etc.)</action>
    <action>For each issue raised:
      - Cross-reference with embedded project_context.md and story file
      - Cross-reference with source code snippets provided in reviews
      - Determine if issue is valid or false positive
      - Note reviewer consensus (if 3+ reviewers agree, high confidence issue)
    </action>
    <action>Issues with low reviewer agreement (1-2 reviewers) require extra scrutiny</action>
    <action>Group related findings that address the same underlying problem</action>
  </step>

  <step n="1.5" goal="Review Deep Verify code analysis" conditional="[Deep Verify Findings] section present">
    <critical>Deep Verify analyzed the actual source code files for this story.
      DV findings are based on static analysis patterns and may identify issues reviewers missed.</critical>

    <action>Review each DV finding:
      - CRITICAL findings: Security vulnerabilities, race conditions, resource leaks - must address
      - ERROR findings: Bugs, missing error handling, boundary issues - should address
      - WARNING findings: Code quality concerns - consider addressing
    </action>

    <action>Cross-reference DV findings with reviewer findings:
      - DV + Reviewers agree: High confidence issue, prioritize in fix order
      - Only DV flags: Verify in source code - DV has precise line numbers
      - Only reviewers flag: May be design/logic issues DV can't detect
    </action>

    <action>DV findings may include evidence with:
      - Code quotes (exact text from source)
      - Line numbers (precise location, when available)
      - Pattern IDs (known antipattern reference)
      Use this evidence when applying fixes.</action>

    <action>DV patterns reference:
      - CC-*: Concurrency issues (race conditions, deadlocks)
      - SEC-*: Security vulnerabilities
      - DB-*: Database/storage issues
      - DT-*: Data transformation issues
      - GEN-*: General code quality (null handling, resource cleanup)
    </action>
  </step>

  <step n="2" goal="Verify issues and identify false positives">
    <action>For each issue, verify against embedded code context:
      - Does the issue actually exist in the current code?
      - Is the suggested fix appropriate for the codebase patterns?
      - Would the fix introduce new issues or regressions?
    </action>
    <action>Document false positives with clear reasoning:
      - Why the reviewer was wrong
      - What evidence contradicts the finding
      - Reference specific code or project_context.md patterns
    </action>
  </step>

  <step n="3" goal="Prioritize by severity">
    <action>For verified issues, assign severity:
      - Critical: Security vulnerabilities, data corruption, crashes
      - High: Bugs that break functionality, performance issues
      - Medium: Code quality issues, missing error handling
      - Low: Style issues, minor improvements, documentation
    </action>
    <action>Order fixes by severity - Critical first, then High, Medium, Low</action>
    <action>For disputed issues (reviewers disagree), note for manual resolution</action>
  </step>

  <step n="4" goal="Apply fixes to source code">
    <critical>This is SOURCE CODE modification, not story file modification</critical>
    <critical>Use Edit tool for all code changes - preserve surrounding code</critical>
    <critical>After applying each fix group, run: pytest -q --tb=line --no-header</critical>
    <critical>NEVER proceed to next fix if tests are broken - either revert or adjust</critical>

    <action>For each verified issue (starting with Critical):
      1. Identify the source file(s) from reviewer findings
      2. Apply fix using Edit tool - change ONLY the identified issue
      3. Preserve code style, indentation, and surrounding context
      4. Log the change for synthesis report
    </action>

    <action>After each logical fix group (related changes):
      - Run: pytest -q --tb=line --no-header
      - If tests pass, continue to next fix
      - If tests fail:
        a. Analyze which fix caused the failure
        b. Either revert the problematic fix OR adjust implementation
        c. Run tests again to confirm green state
        d. Log partial fix failure in synthesis report
    </action>

    <action>Atomic commit guidance (for user reference):
      - Commit message format: fix(component): brief description (synthesis-11.7)
      - Group fixes by severity and affected component
      - Never commit unrelated changes together
      - User may batch or split commits as preferred
    </action>
  </step>

  <step n="5" goal="Refactor if needed">
    <critical>Only refactor code directly related to applied fixes</critical>
    <critical>Maximum scope: files already modified in Step 4</critical>

    <action>Review applied fixes for duplication patterns:
      - Same fix applied 2+ times across files = candidate for refactor
      - Only if duplication is in files already modified
    </action>

    <action>If refactoring:
      - Extract common logic to shared function/module
      - Update all call sites in modified files
      - Run tests after refactoring: pytest -q --tb=line --no-header
      - Log refactoring in synthesis report
    </action>

    <action>Do NOT refactor:
      - Unrelated code that "could be improved"
      - Files not touched in Step 4
      - Patterns that work but are just "not ideal"
    </action>

    <action>If broader refactoring needed:
      - Note it in synthesis report as "Suggested future improvement"
      - Do not apply - leave for dedicated refactoring story
    </action>
  </step>

  <step n="6" goal="Generate synthesis report">
    <critical>When updating story file, use atomic write pattern (temp file + rename).</critical>
    <action>Update story file Dev Agent Record section ONLY:
      - Mark completed tasks with [x] if fixes address them
      - Append to "Completion Notes List" subsection summarizing changes applied
      - Update file list with all modified files
    </action>

    <critical>Your synthesis report MUST be wrapped in HTML comment markers for extraction:</critical>
    <action>Produce structured output in this exact format (including the markers):</action>
    <output-format>
&lt;!-- CODE_REVIEW_SYNTHESIS_START --&gt;
## Synthesis Summary
[Brief overview: X issues verified, Y false positives dismissed, Z fixes applied to source files]

## Validations Quality
[For each reviewer: ID (A, B, C...), score (1-10), brief assessment]
[Note: Reviewers are anonymized - do not attempt to identify providers]

## Issues Verified (by severity)

### Critical
[Issues that required immediate fixes - list with evidence and fixes applied]
[Format: "- **Issue**: Description | **Source**: Reviewer(s) | **File**: path | **Fix**: What was changed"]
[If none: "No critical issues identified."]

### High
[Bugs and significant problems - same format]

### Medium
[Code quality issues - same format]

### Low
[Minor improvements - same format, note any deferred items]

## Issues Dismissed
[False positives with reasoning for each dismissal]
[Format: "- **Claimed Issue**: Description | **Raised by**: Reviewer(s) | **Dismissal Reason**: Why this is incorrect"]
[If none: "No false positives identified."]

## Changes Applied
[Complete list of modifications made to source files]
[Format for each change:
  **File**: [path/to/file.py]
  **Change**: [Brief description]
  **Before**:
  ```
  [2-3 lines of original code]
  ```
  **After**:
  ```
  [2-3 lines of updated code]
  ```
]
[If no changes: "No source code changes required."]

## Deep Verify Integration
[If DV findings were present, document how they were handled]

### DV Findings Fixed
[List DV findings that resulted in code changes]
[Format: "- **{ID}** [{SEVERITY}]: {Title} | **File**: {path} | **Fix**: {What was changed}"]

### DV Findings Dismissed
[List DV findings determined to be false positives]
[Format: "- **{ID}** [{SEVERITY}]: {Title} | **Reason**: {Why this is not an issue}"]

### DV-Reviewer Overlap
[Note findings flagged by both DV and reviewers - highest confidence fixes]
[If no DV findings: "Deep Verify did not produce findings for this story."]

## Files Modified
[Simple list of all files that were modified]
- path/to/file1.py
- path/to/file2.py
[If none: "No files modified."]

## Suggested Future Improvements
[Broader refactorings or improvements identified in Step 5 but not applied]
[Format: "- **Scope**: Description | **Rationale**: Why deferred | **Effort**: Estimated complexity"]
[If none: "No future improvements identified."]

## Test Results
[Final test run output summary]
- Tests passed: X
- Tests failed: 0 (required for completion)
&lt;!-- CODE_REVIEW_SYNTHESIS_END --&gt;
    </output-format>

  </step>

  <step n="6.5" goal="Write Senior Developer Review section to story file for dev_story rework detection">
    <critical>This section enables dev_story to detect that a code review has occurred and extract action items.</critical>
    <critical>APPEND this section to the story file - do NOT replace existing content.</critical>

    <action>Determine the evidence verdict from the [Evidence Score] section:
      - REJECT: Evidence score exceeds reject threshold
      - PASS: Evidence score is below accept threshold
      - UNCERTAIN: Evidence score is between thresholds
    </action>

    <action>Map evidence verdict to review outcome:
      - PASS → "Approved"
      - REJECT → "Changes Requested"
      - UNCERTAIN → "Approved with Reservations"
    </action>

    <action>Append to story file "## Senior Developer Review (AI)" section:
      ```
      ## Senior Developer Review (AI)

      ### Review: {current_date}
      - **Reviewer:** AI Code Review Synthesis
      - **Evidence Score:** {evidence_score} → {evidence_verdict}
      - **Issues Found:** {total_verified_issues}
      - **Issues Fixed:** {fixes_applied_count}
      - **Action Items Created:** {remaining_unfixed_count}
      ```
    </action>

    <critical>When evidence verdict is REJECT, you MUST create Review Follow-ups tasks.
      If "Action Items Created" count is &gt; 0, there MUST be exactly that many [ ] [AI-Review] tasks.
      Do NOT skip this step. Do NOT claim all issues are fixed if you reported deferred items above.</critical>

    <action>Find the "## Tasks / Subtasks" section in the story file</action>
    <action>Append a "#### Review Follow-ups (AI)" subsection with checkbox tasks:
      ```
      #### Review Follow-ups (AI)
      - [ ] [AI-Review] {severity}: {brief description of unfixed issue} ({file path})
      ```
      One line per unfixed/deferred issue, prefixed with [AI-Review] tag.
      Order by severity: Critical first, then High, Medium, Low.
    </action>

    <critical>ATDD DEFECT CHECK: Search test directories (tests/**) for test.fixme() calls in test files related to this story.
      If ANY test.fixme() calls remain in story-related test files, this is a DEFECT — the dev_story agent failed to activate ATDD RED-phase tests.
      Create an additional [AI-Review] task:
      - [ ] [AI-Review] HIGH: Activate ATDD tests — convert all test.fixme() to test() and ensure they pass ({test file paths})
      Do NOT dismiss test.fixme() as "intentional TDD methodology". After dev_story completes, ALL test.fixme() tests for the story MUST be converted to test().</critical>
  </step>

  </workflow></instructions>
<output-template></output-template>
</compiled-workflow>