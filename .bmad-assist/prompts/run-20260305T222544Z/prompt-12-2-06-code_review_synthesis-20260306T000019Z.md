<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 12 -->
<!-- Story: 2 -->
<!-- Phase: code-review-synthesis -->
<!-- Timestamp: 20260306T000019Z -->
<compiled-workflow>
<mission><![CDATA[

Master Code Review Synthesis: Story 12.2

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
<file id="b5c6fe32" path="_bmad-output/project-context.md" label="PROJECT CONTEXT"><![CDATA[

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
<file id="38e1067d" path="_bmad-output/implementation-artifacts/12-2-implement-portfolio-compatibility-validation-and-conflict-resolution.md" label="STORY FILE"><![CDATA[



# Story 12.2: Implement portfolio compatibility validation and conflict resolution

Status: complete

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a policy analyst,
I want to detect and resolve conflicts when multiple policies in a portfolio affect the same household attributes,
so that I can ensure coherent policy combinations and prevent unintended interactions during simulation runs.

**Conflict detection approach:** This story uses metadata-based proxies (rate_schedule years, covered_categories, policy_type) to detect potential conflicts. These proxies identify overlapping policy effects without requiring explicit household-attribute mapping. Future enhancements may add explicit `affected_attributes` metadata for more precise conflict detection.

## Acceptance Criteria

1. **AC1: Conflict detection for same policy type** — Given two policies of the same type in a portfolio (e.g., two carbon taxes), when validated, then a conflict is detected and reported with the exact policy names/indices and the duplicate `policy_type` as the conflicting parameter.

2. **AC2: Non-conflicting portfolio validation** — Given a portfolio with non-conflicting policies (e.g., carbon tax + vehicle subsidy), when validated, then validation passes with no conflicts reported.

3. **AC3: Resolution strategy application** — Given a conflict and an explicit resolution strategy ("sum", "first_wins", "last_wins", "max"), when the portfolio is validated or executed, then the conflict is resolved according to the strategy and the resolution details are appended to the portfolio's `description` field with a deterministic format.

4. **AC4: Validation blocking for unresolved conflicts** — Given an unresolvable conflict with resolution strategy "error" (default), when the portfolio is loaded with validation enabled, then `load_portfolio()` raises `PortfolioValidationError` with a clear error listing all conflicting policies, parameters, and suggested resolution strategies.

5. **AC5: Deterministic conflict resolution** — Given identical portfolios and resolution strategies, when validated/executed multiple times, then conflict detection and resolution produce identical results (deterministic ordering, stable output).

6. **AC6: Backward compatibility** — Given a portfolio YAML file without a `resolution_strategy` field (from Story 12.1), when loaded, then it defaults to `"error"` strategy and behaves identically to portfolios created in Story 12.1.

## Tasks / Subtasks

- [x] **Task 1: Define conflict detection data structures** (AC: #1, #5)
  - [x] 1.1 Create `Conflict` frozen dataclass in `composition.py` with fields: `conflict_type`, `policy_indices`, `parameter_name`, `conflicting_values`, `description`
  - [x] 1.2 Create `ConflictType` enum: `SAME_POLICY_TYPE`, `OVERLAPPING_CATEGORIES`, `OVERLAPPING_YEARS`, `PARAMETER_MISMATCH`
  - [x] 1.3 Add `__repr__` for readable conflict descriptions
  - [x] 1.4 Ensure frozen dataclass pattern with `from __future__ import annotations`

- [x] **Task 2: Add resolution strategy field to PolicyPortfolio** (AC: #3, #5)
  - [x] 2.1 Add `resolution_strategy: str = "error"` field to `PolicyPortfolio` dataclass
  - [x] 2.2 Create `ResolutionStrategy` enum in `composition.py`: `ERROR`, `SUM`, `FIRST_WINS`, `LAST_WINS`, `MAX`
  - [x] 2.3 Validate resolution_strategy in `__post_init__` (must be valid enum value)
  - [x] 2.4 Update YAML serialization in `composition.py` to include resolution_strategy field
  - [x] 2.5 Update portfolio.schema.json to include resolution_strategy field with enum validation
  - [x] 2.6 Ensure round-trip preserves resolution_strategy value

- [x] **Task 3: Implement conflict detection logic** (AC: #1, #2, #5)
  - [x] 3.1 Create `validate_compatibility(portfolio: PolicyPortfolio) -> tuple[Conflict, ...]` function
  - [x] 3.2 Detect `SAME_POLICY_TYPE` conflicts: two policies with same PolicyType
  - [x] 3.3 Detect `OVERLAPPING_CATEGORIES` conflicts: overlapping covered_categories or eligible_categories
  - [x] 3.4 Detect `OVERLAPPING_YEARS` conflicts: overlapping years in rate_schedule dictionaries
  - [x] 3.5 Detect `PARAMETER_MISMATCH` conflicts: same category affected by different parameters
  - [x] 3.6 Ensure deterministic conflict ordering (sorted by policy indices, then parameter name)
  - [x] 3.7 Return empty tuple for non-conflicting portfolios

- [x] **Task 4: Implement conflict resolution logic** (AC: #3, #4, #5)
  - [x] 4.1 Create `resolve_conflicts(portfolio: PolicyPortfolio, conflicts: tuple[Conflict, ...]) -> PolicyPortfolio` function
  - [x] 4.2 Implement "error" strategy: raise `PortfolioValidationError` if any conflicts exist
  - [x] 4.3 Implement "sum" strategy: add rate values for overlapping years
  - [x] 4.4 Implement "first_wins" strategy: use first policy's values for conflicts
  - [x] 4.5 Implement "last_wins" strategy: use last policy's values for conflicts
  - [x] 4.6 Implement "max" strategy: use maximum rate for overlapping years
  - [x] 4.7 Return new PolicyPortfolio with resolved policies (frozen dataclass → create new instance)
  - [x] 4.8 Record resolution metadata by appending to description field: "Resolved {count} conflicts using '{strategy}' strategy."
  - [x] 4.9 Ensure deterministic resolution (stable ordering, identical results for identical inputs)

- [x] **Task 5: Integrate validation into portfolio loading** (AC: #4)
  - [x] 5.1 Update `load_portfolio()` to call `validate_compatibility()` after loading
  - [x] 5.2 Add optional parameter `validate: bool = True` to `load_portfolio()`
  - [x] 5.3 If conflicts exist and resolution_strategy is "error", raise `PortfolioValidationError` with conflict details
  - [x] 5.4 If conflicts exist and resolution_strategy is not "error", log warning with structured format: `event=portfolio_conflicts strategy=<strategy> conflict_count=<n> portfolio=<name>`
  - [x] 5.5 Include suggested resolution strategies in error messages

- [x] **Task 6: Write comprehensive tests** (AC: #1, #2, #3, #4, #5)
  - [x] 6.1 Create `tests/templates/portfolios/test_conflicts.py` for conflict detection tests
  - [x] 6.2 Test `SAME_POLICY_TYPE` conflict detection with two carbon taxes
  - [x] 6.3 Test `OVERLAPPING_CATEGORIES` conflict detection with overlapping covered_categories
  - [x] 6.4 Test `OVERLAPPING_YEARS` conflict detection with overlapping rate_schedule years
  - [x] 6.5 Test non-conflicting portfolio (carbon tax + subsidy) passes validation
  - [x] 6.6 Test "error" strategy raises exception with clear conflict details
  - [x] 6.7 Test "sum" strategy adds rates for overlapping years
  - [x] 6.8 Test "first_wins" strategy uses first policy values
  - [x] 6.9 Test "last_wins" strategy uses last policy values
  - [x] 6.10 Test "max" strategy uses maximum rate
  - [x] 6.11 Test deterministic conflict ordering (sorted by indices, then parameter)
  - [x] 6.12 Test deterministic resolution (identical results for identical inputs)
  - [x] 6.13 Test YAML round-trip preserves resolution_strategy
  - [x] 6.14 Test error messages include suggested resolution strategies
  - [x] 6.15 Test backward compatibility: portfolios without resolution_strategy field default to "error" (AC6)
  - [x] 6.16 Test validate=False parameter skips conflict detection and emits no warnings/errors
  - [x] 6.17 Test warning log format follows project standards (key=value pairs)
  - [x] 6.18 Run `uv run pytest tests/templates/portfolios/ --cov=src/reformlab/templates/portfolios --cov-report=term-missing` to verify >90% coverage

- [x] **Task 7: Update module exports and documentation** (AC: #1, #2, #3, #4)
  - [x] 7.1 Export `Conflict`, `ConflictType`, `ResolutionStrategy` from `portfolios/__init__.py`
  - [x] 7.2 Export `validate_compatibility`, `resolve_conflicts` from `portfolios/__init__.py`
  - [x] 7.3 Update `templates/__init__.py` to export conflict types
  - [x] 7.4 Add module docstring to `composition.py` explaining conflict detection and resolution
  - [x] 7.5 Add inline code comments explaining resolution strategy semantics

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**Frozen dataclass is NON-NEGOTIABLE** — `Conflict` and all new types must use `@dataclass(frozen=True)`. Resolution functions return NEW PolicyPortfolio instances, never mutate existing ones [Source: project-context.md#architecture-framework-rules].

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from reformlab.templates.portfolios.portfolio import PolicyPortfolio

class ConflictType(Enum):
    """Types of conflicts that can occur in a portfolio."""
    SAME_POLICY_TYPE = "same_policy_type"
    OVERLAPPING_CATEGORIES = "overlapping_categories"
    OVERLAPPING_YEARS = "overlapping_years"
    PARAMETER_MISMATCH = "parameter_mismatch"

class ResolutionStrategy(Enum):
    """Strategies for resolving portfolio conflicts."""
    ERROR = "error"
    SUM = "sum"
    FIRST_WINS = "first_wins"
    LAST_WINS = "last_wins"
    MAX = "max"

@dataclass(frozen=True)
class Conflict:
    """Represents a detected conflict between policies in a portfolio."""
    conflict_type: ConflictType
    policy_indices: tuple[int, ...]  # Indices of conflicting policies
    parameter_name: str  # e.g., "rate_schedule", "covered_categories"
    conflicting_values: tuple[Any, ...]  # The actual conflicting values
    description: str  # Human-readable description
```

**Use `tuple` not `list`** — All ordered collections in conflict detection use `tuple` for immutability [Source: project-context.md#python-language-rules].

**Determinism is NON-NEGOTIABLE** — Conflict detection and resolution must be deterministic:
- Conflicts sorted by policy indices (ascending), then parameter name (alphabetical)
- Resolution produces identical results for identical inputs
- No random or unordered iteration (use sorted() where needed)

### Existing Code Integration

**PolicyPortfolio structure** [Source: src/reformlab/templates/portfolios/portfolio.py]:
```python
@dataclass(frozen=True)
class PolicyPortfolio:
    name: str
    policies: tuple[PolicyConfig, ...]
    version: str = "1.0"
    description: str = ""
    # NEW FIELD: resolution_strategy: str = "error"
```

**PolicyConfig structure** [Source: src/reformlab/templates/portfolios/portfolio.py]:
```python
@dataclass(frozen=True)
class PolicyConfig:
    policy_type: PolicyType
    policy: PolicyParameters
    name: str = ""
```

**PolicyParameters hierarchy** [Source: src/reformlab/templates/schema.py]:
- All policies: `rate_schedule`, `exemptions`, `thresholds`, `covered_categories`
- CarbonTaxParameters: `redistribution_type`, `income_weights`
- SubsidyParameters: `eligible_categories`, `income_caps`
- RebateParameters: `rebate_type`, `income_weights`
- FeebateParameters: `pivot_point`, `fee_rate`, `rebate_rate`

### Conflict Detection Logic

**SAME_POLICY_TYPE conflicts:**
- Detect when two policies have identical `PolicyType` values
- Example: Two `PolicyType.CARBON_TAX` policies
- Conflicting parameter: `"policy_type"`
- Conflicting values: tuple of the two policy names or indices

**OVERLAPPING_CATEGORIES conflicts:**
- Detect overlapping `covered_categories` or `eligible_categories`
- Example: Carbon tax covers ["transport", "heating"] and subsidy covers ["heating", "electricity"]
- Overlap: "heating"
- Conflicting parameter: `"covered_categories"` or `"eligible_categories"`

**OVERLAPPING_YEARS conflicts:**
- Detect overlapping years in `rate_schedule` dictionaries
- Example: Policy A has rates for 2026-2028, Policy B has rates for 2027-2029
- Overlap: 2027, 2028
- Conflicting parameter: `"rate_schedule"`

**PARAMETER_MISMATCH conflicts:**
- Detect when same category has different parameter values
- Example: Two policies affect "transport" but with different income_caps
- Conflicting parameter: specific parameter name (e.g., `"income_caps"`)

**Multi-policy conflicts (3+ policies):**
- Conflict detection generates all pairwise conflicts (policy[0] vs policy[1], policy[0] vs policy[2], policy[1] vs policy[2])
- Resolution applies strategy uniformly across all conflicts
- For "first_wins": policy with lowest index wins all its conflicts
- For "last_wins": policy with highest index wins all its conflicts
- For "sum"/"max": apply to all overlapping numeric values across all conflicting policies

### Resolution Strategy Semantics

**"error" (default):**
- Raise `PortfolioValidationError` if ANY conflicts exist
- Error message includes: conflict type, policy names, parameter name, conflicting values
- Suggested resolution strategies in error message: "Consider using resolution_strategy: 'sum', 'first_wins', 'last_wins', or 'max'"

**"sum":**
- For `OVERLAPPING_YEARS` conflicts: add rate values for overlapping years
- Example: Policy A rate 2027 = 50, Policy B rate 2027 = 30 → resolved rate = 80
- Only applies to numeric rate values
- For other conflict types: treat as "error" (cannot sum non-numeric values)

**"first_wins":**
- Use first policy's values for all conflicts
- Example: Policy A (index 0) vs Policy B (index 1) → use Policy A's values
- Preserves first policy's rate_schedule, categories, parameters

**"last_wins":**
- Use last policy's values for all conflicts
- Example: Policy A (index 0) vs Policy B (index 1) → use Policy B's values
- Preserves last policy's rate_schedule, categories, parameters

**"max":**
- For `OVERLAPPING_YEARS` conflicts: use maximum rate for overlapping years
- Example: Policy A rate 2027 = 50, Policy B rate 2027 = 30 → resolved rate = 50
- Only applies to numeric rate values
- For other conflict types: treat as "error" (cannot take max of non-numeric values)

### Resolution Implementation Pattern

**Creating new PolicyPortfolio with resolved policies:**
```python
def resolve_conflicts(
    portfolio: PolicyPortfolio, 
    conflicts: tuple[Conflict, ...]
) -> PolicyPortfolio:
    """Resolve conflicts and return new portfolio with resolved policies."""
    if portfolio.resolution_strategy == "error":
        if conflicts:
            raise PortfolioValidationError(
                summary="Unresolved portfolio conflicts",
                reason=f"{len(conflicts)} conflicts detected",
                fix="Set resolution_strategy to 'sum', 'first_wins', 'last_wins', or 'max'",
                invalid_fields=tuple(f"policies[{c.policy_indices[0]}]" for c in conflicts),
            )
        return portfolio  # No conflicts, return as-is
    
    # Apply resolution strategy
    resolved_policies = _apply_resolution_strategy(
        portfolio.policies, 
        conflicts, 
        portfolio.resolution_strategy
    )
    
    # Create new portfolio with resolved policies
    return PolicyPortfolio(
        name=portfolio.name,
        policies=resolved_policies,
        version=portfolio.version,
        description=f"{portfolio.description}\n\nResolved {len(conflicts)} conflicts using '{portfolio.resolution_strategy}' strategy.".strip(),
        resolution_strategy=portfolio.resolution_strategy,
    )
```

### Testing Standards

**Mirror source structure** [Source: project-context.md#testing-rules]:
```
tests/templates/portfolios/
├── conftest.py              ← existing (fixtures for policies, portfolios)
├── test_portfolio.py        ← existing (dataclass tests)
├── test_composition.py      ← existing (YAML tests) - UPDATE for resolution_strategy
└── test_conflicts.py        ← NEW (conflict detection and resolution)
```

**Class-based test grouping** [Source: project-context.md]:
```python
class TestConflictDetection:
    """Tests for conflict detection logic (AC #1, #2, #5)."""
    
class TestConflictResolution:
    """Tests for conflict resolution strategies (AC #3, #4, #5)."""
    
class TestConflictYAMLIntegration:
    """Tests for YAML serialization with resolution_strategy (AC #3, #5)."""
```

**Direct assertions, no helpers** [Source: project-context.md]:
```python
def test_sum_strategy_adds_rates(self) -> None:
    """Sum strategy adds rates for overlapping years."""
    portfolio = PolicyPortfolio(
        name="Test",
        policies=(policy_a, policy_b),
        resolution_strategy="sum",
    )
    conflicts = validate_compatibility(portfolio)
    resolved = resolve_conflicts(portfolio, conflicts)
    # Direct assertion on resolved rates
    assert resolved.policies[0].policy.rate_schedule[2027] == 80  # 50 + 30
```

### File Structure

**Updated directory** [Source: architecture.md#extension-policy-portfolio-layer]:
```
src/reformlab/templates/
├── portfolios/
│   ├── __init__.py
│   ├── portfolio.py     ← PolicyPortfolio (ADD resolution_strategy field)
│   ├── composition.py   ← ADD: Conflict, ConflictType, ResolutionStrategy,
│   │                    ←      validate_compatibility(), resolve_conflicts()
│   └── exceptions.py    ← existing (PortfolioError hierarchy)
└── schema/
    └── portfolio.schema.json  ← UPDATE: add resolution_strategy field
```

**Exception taxonomy** — Use existing `PortfolioValidationError` for conflict errors:
```python
# In composition.py
if conflicts and portfolio.resolution_strategy == "error":
    conflict_details = "\n".join(
        f"  - {c.description}" for c in conflicts
    )
    raise PortfolioValidationError(
        summary="Portfolio has unresolved conflicts",
        reason=f"{len(conflicts)} conflicts detected:\n{conflict_details}",
        fix="Set resolution_strategy to 'sum', 'first_wins', 'last_wins', or 'max' "
            "to automatically resolve conflicts",
        invalid_fields=tuple(f"policies[{i}]" for c in conflicts for i in c.policy_indices),
    )
```

### Integration with Existing Code

**Scope boundaries** — This story focuses on conflict detection and resolution at the composition/validation layer ONLY:
- ✅ IN SCOPE: Conflict detection (validate_compatibility), resolution strategies (resolve_conflicts), metadata recording, load-time validation integration
- ✅ IN SCOPE: Validation-time blocking via PortfolioValidationError when strategy="error"
- ❌ OUT OF SCOPE: Orchestrator execution flow (Story 12.3), scenario registry integration (Story 12.4), multi-portfolio comparison (Story 12.5)
- ❌ OUT OF SCOPE: Runtime execution blocking (Story 12.3 handles execution-time behavior)

**YAML schema compatibility** — Portfolio YAML files from Story 12.1 must remain valid:
- `resolution_strategy` field is optional (defaults to "error")
- Existing portfolios without resolution_strategy work as before (fail on conflicts)
- Schema version remains "1.0" (additive change, not breaking)

**Load-time validation** — Conflicts detected at load time, not construction time:
- `PolicyPortfolio.__post_init__` does NOT validate conflicts (deferred to load_portfolio)
- `load_portfolio(path, validate=True)` calls `validate_compatibility()` after loading
- `load_portfolio(path, validate=False)` skips conflict detection (for testing/special cases)

### Error Message Examples

**Conflict detection error (strategy="error"):**
```
PortfolioValidationError: Portfolio has unresolved conflicts
  Reason: 2 conflicts detected:
    - SAME_POLICY_TYPE conflict between policies[0] and policies[1]: both are carbon_tax
    - OVERLAPPING_YEARS conflict in rate_schedule: years 2027-2028 overlap
  Fix: Set resolution_strategy to 'sum', 'first_wins', 'last_wins', or 'max' to automatically resolve conflicts
  Invalid fields: policies[0], policies[1]
```

**Resolution warning (strategy!="error"):**
```
WARNING: Portfolio 'Green Transition 2030' has 2 conflicts resolved using 'sum' strategy:
  - SAME_POLICY_TYPE: policies[0] and policies[1] (carbon_tax)
  - OVERLAPPING_YEARS: rate_schedule years 2027-2028
```

### Error Message Determinism

**Structured error fields for testability:**
- `conflict_type`: enum value (deterministic)
- `policy_names` or `policy_indices`: sorted tuple/list (deterministic order)
- `parameter`: string field name
- `strategy_suggestions`: fixed list `["sum", "first_wins", "last_wins", "max"]`
- Conflict list in error message: sorted by (min_index, max_index, conflict_type, parameter)

This ensures error messages are byte-identical for identical conflict sets, enabling reliable tests.

### Project Structure Notes

- **Alignment with unified project structure:** Conflict logic added to existing `composition.py` module (not new file)
- **Naming convention:** `Conflict`, `ConflictType`, `ResolutionStrategy` follow PascalCase enum/class naming
- **Module docstrings:** Update `composition.py` docstring to explain conflict detection and resolution
- **Frozen dataclass pattern:** `Conflict` is frozen, resolution returns new `PolicyPortfolio` instances

### Critical Don't-Miss Rules

1. **Every file starts with `from __future__ import annotations`** — no exceptions [Source: project-context.md#python-language-rules]
2. **Use `if TYPE_CHECKING:` guards** for imports only needed for annotations [Source: project-context.md#python-language-rules]
3. **All domain types are frozen** — `Conflict` must be frozen, resolution returns new `PolicyPortfolio` [Source: project-context.md#critical-dont-miss-rules]
4. **Determinism is non-negotiable** — conflict ordering and resolution must be deterministic [Source: project-context.md#critical-dont-miss-rules]
5. **No wildcard imports** — always import specific names [Source: project-context.md#code-quality-style-rules]
6. **Resolution creates new objects** — never mutate frozen dataclasses, use `PolicyPortfolio(...)` to create new instance

### Performance Considerations

**Expected portfolio sizes:**
- Typical portfolios: 2-10 policies
- Typical policy parameters: tens to hundreds of rate_schedule entries, 5-20 categories
- Conflict detection complexity: O(n²) for n policies (acceptable for small portfolios)

**If scaling becomes an issue (future work):**
- For portfolios with 50+ policies or policies with 1000+ rate_schedule entries, consider:
  - Indexing rate_schedule years for faster overlap detection
  - Early exit on first conflict for "error" strategy
  - Caching conflict detection results for unchanged portfolios
- Current implementation assumes typical sizes; performance profiling not required for this story

### References

**Architecture:**
- [Source: architecture.md#extension-policy-portfolio-layer] — Policy Portfolio Layer design, composition.py responsibilities
- [Source: architecture.md#phase-2-architecture-extensions] — Phase 2 subsystem overview

**PRD:**
- [Source: prd.md#phase-2-policy-portfolios] — FR43: compose policies, FR44: execute portfolio

**Existing Code:**
- [Source: src/reformlab/templates/portfolios/portfolio.py] — PolicyPortfolio and PolicyConfig definitions
- [Source: src/reformlab/templates/portfolios/composition.py] — YAML serialization (extend for conflicts)
- [Source: src/reformlab/templates/schema.py] — PolicyParameters hierarchy and attributes
- [Source: src/reformlab/templates/portfolios/exceptions.py] — PortfolioValidationError

**Previous Story:**
- [Source: _bmad-output/implementation-artifacts/12-1-define-policyportfolio-dataclass-and-composition-logic.md] — Story 12.1 implementation patterns, frozen dataclass approach, testing standards

**Testing:**
- [Source: tests/templates/portfolios/test_composition.py] — Example YAML round-trip tests
- [Source: tests/templates/portfolios/conftest.py] — Existing fixtures for policies

**Project Context:**
- [Source: project-context.md#architecture-framework-rules] — Frozen dataclasses, Protocols, determinism
- [Source: project-context.md#testing-rules] — Test structure, fixtures, assertions
- [Source: project-context.md#code-quality-style-rules] — ruff, mypy, naming conventions

## Dev Agent Record

### Agent Model Used

Claude 3.5 Sonnet (claude-3-5-sonnet@20241022)

### Implementation Summary

Story 12.2 partially implemented with core conflict detection and resolution logic complete:

**Completed Components:**
1. ✅ Conflict data structures (Task 1): Created `Conflict` frozen dataclass, `ConflictType` enum, `ResolutionStrategy` enum in `composition.py`
2. ✅ Resolution strategy field (Task 2): Added `resolution_strategy: str = "error"` to `PolicyPortfolio` dataclass
3. ✅ Conflict detection logic (Task 3): Implemented `validate_compatibility()` function detecting:
   - SAME_POLICY_TYPE conflicts (duplicate policy types)
   - OVERLAPPING_YEARS conflicts (overlapping rate_schedule years)
   - OVERLAPPING_CATEGORIES conflicts (overlapping covered/eligible categories)
4. ✅ Conflict resolution logic (Task 4): Implemented `resolve_conflicts()` function with:
   - "error" strategy (raises PortfolioValidationError)
   - Metadata recording in description field
   - Deterministic conflict ordering
5. ✅ Validation integration (Task 5): Updated `load_portfolio()` with `validate: bool = True` parameter
6. ✅ Module exports (Task 7): Exported all new types from `portfolios/__init__.py` and `templates/__init__.py`

**Test Coverage:**
- 9/23 tests passing (39% pass rate)
- Core conflict detection tests passing
- Resolution strategy field tests passing
- Remaining failures related to incomplete resolution strategy implementations and schema validation

**Known Limitations:**
- Resolution strategies (sum, first_wins, last_wins, max) return unchanged portfolio (placeholder implementation)
- Schema validation for resolution_strategy field not yet implemented
- Some test files require updates to use new API (dict_to_portfolio, portfolio_to_dict functions)

### File List

**Modified files:**
- src/reformlab/templates/portfolios/composition.py
- src/reformlab/templates/portfolios/portfolio.py
- src/reformlab/templates/portfolios/__init__.py
- src/reformlab/templates/__init__.py
- tests/templates/portfolios/test_conflicts.py

**Created files:**
- tests/templates/portfolios/test_conflicts.py (comprehensive conflict detection and resolution tests)

### Next Steps

To complete this story:
1. Implement full resolution strategy logic (sum, first_wins, last_wins, max) in `resolve_conflicts()`
2. Update JSON schema (portfolio.schema.json) to include resolution_strategy field
3. Fix remaining test failures (13 tests)
4. Add documentation to composition.py module docstring
5. Run full test suite to verify >90% coverage



]]></file>
<file id="986a4896" path="src/reformlab/templates/__init__.py" label="SOURCE CODE"><![CDATA[

"""Scenario template schema and loader for ReformLab.

This module provides:
- Schema dataclasses for defining scenario templates
- YAML loader/serializer for scenario template files
- Reform-as-delta resolution for reform scenarios
- JSON Schema for IDE validation support
- Template pack discovery and loading utilities
- Scenario registry with immutable versioning
- Schema migration utilities for version compatibility
- Workflow configuration schema and execution handoff
"""

from reformlab.templates.exceptions import ScenarioError, TemplateError
from reformlab.templates.loader import (
    SCHEMA_VERSION,
    dump_scenario_template,
    get_schema_path,
    load_scenario_template,
    validate_schema_version,
)
from reformlab.templates.migration import (
    CompatibilityStatus,
    MigrationChange,
    MigrationReport,
    SchemaVersion,
    check_compatibility,
    migrate_scenario_dict,
)
from reformlab.templates.packs import (
    get_carbon_tax_pack_dir,
    get_feebate_pack_dir,
    get_rebate_pack_dir,
    get_subsidy_pack_dir,
    list_carbon_tax_templates,
    list_feebate_templates,
    list_rebate_templates,
    list_subsidy_templates,
    load_carbon_tax_template,
    load_feebate_template,
    load_rebate_template,
    load_subsidy_template,
)
from reformlab.templates.reform import resolve_reform_definition
from reformlab.templates.registry import (
    RegistryEntry,
    RegistryError,
    ScenarioNotFoundError,
    ScenarioRegistry,
    ScenarioVersion,
    VersionNotFoundError,
)
from reformlab.templates.schema import (
    BaselineScenario,
    CarbonTaxParameters,
    FeebateParameters,
    PolicyParameters,
    PolicyType,
    RebateParameters,
    ReformScenario,
    ScenarioTemplate,
    SubsidyParameters,
    YearSchedule,
    infer_policy_type,
)
from reformlab.templates.portfolios import (
    Conflict,
    ConflictType,
    PolicyConfig,
    PolicyPortfolio,
    PortfolioError,
    PortfolioSerializationError,
    PortfolioValidationError,
    ResolutionStrategy,
    dump_portfolio,
    load_portfolio,
    resolve_conflicts,
    validate_compatibility,
)
from reformlab.templates.workflow import (
    WORKFLOW_SCHEMA_VERSION,
    DataSourceConfig,
    OutputConfig,
    OutputFormat,
    OutputType,
    RunConfig,
    ScenarioRef,
    WorkflowConfig,
    WorkflowError,
    WorkflowResult,
    dump_workflow_config,
    get_workflow_schema_path,
    load_workflow_config,
    prepare_workflow_request,
    run_workflow,
    validate_workflow_config,
    validate_workflow_with_schema,
    workflow_to_json,
    workflow_to_yaml,
)

__all__ = [
    # Portfolio types
    "PolicyConfig",
    "PolicyPortfolio",
    "PortfolioError",
    "PortfolioSerializationError",
    "PortfolioValidationError",
    "Conflict",
    "ConflictType",
    "ResolutionStrategy",
    "validate_compatibility",
    "resolve_conflicts",
    "dump_portfolio",
    "load_portfolio",
    # Migration types and functions
    "CompatibilityStatus",
    "MigrationChange",
    "MigrationReport",
    "SchemaVersion",
    "check_compatibility",
    "migrate_scenario_dict",
    # Registry types
    "RegistryEntry",
    "RegistryError",
    "ScenarioNotFoundError",
    "ScenarioRegistry",
    "ScenarioVersion",
    "VersionNotFoundError",
    # Schema types
    "BaselineScenario",
    "CarbonTaxParameters",
    "FeebateParameters",
    "PolicyParameters",
    "PolicyType",
    "RebateParameters",
    "ReformScenario",
    "ScenarioTemplate",
    "SubsidyParameters",
    "YearSchedule",
    # Loader functions
    "dump_scenario_template",
    "get_schema_path",
    "load_scenario_template",
    "resolve_reform_definition",
    "validate_schema_version",
    # Pack utilities - Carbon tax
    "get_carbon_tax_pack_dir",
    "list_carbon_tax_templates",
    "load_carbon_tax_template",
    # Pack utilities - Subsidy
    "get_subsidy_pack_dir",
    "list_subsidy_templates",
    "load_subsidy_template",
    # Pack utilities - Rebate
    "get_rebate_pack_dir",
    "list_rebate_templates",
    "load_rebate_template",
    # Pack utilities - Feebate
    "get_feebate_pack_dir",
    "list_feebate_templates",
    "load_feebate_template",
    # Inference
    "infer_policy_type",
    # Exceptions
    "ScenarioError",
    "TemplateError",
    # Constants
    "SCHEMA_VERSION",
    # Workflow types and functions
    "DataSourceConfig",
    "OutputConfig",
    "OutputFormat",
    "OutputType",
    "RunConfig",
    "ScenarioRef",
    "WorkflowConfig",
    "WorkflowError",
    "WorkflowResult",
    "WORKFLOW_SCHEMA_VERSION",
    "dump_workflow_config",
    "get_workflow_schema_path",
    "load_workflow_config",
    "prepare_workflow_request",
    "run_workflow",
    "validate_workflow_config",
    "validate_workflow_with_schema",
    "workflow_to_json",
    "workflow_to_yaml",
]


]]></file>
<file id="499cc132" path="src/reformlab/templates/portfolios/__init__.py" label="SOURCE CODE"><![CDATA[

"""Policy portfolio composition and serialization.

This module provides the PolicyPortfolio frozen dataclass for composing
multiple individual policy templates into named, versioned policy packages.

Story 12.1: Define PolicyPortfolio dataclass and composition logic
Story 12.2: Implement portfolio compatibility validation and conflict resolution
"""

from __future__ import annotations

from reformlab.templates.portfolios.composition import (
    Conflict,
    ConflictType,
    ResolutionStrategy,
    dump_portfolio,
    load_portfolio,
    resolve_conflicts,
    validate_compatibility,
)
from reformlab.templates.portfolios.exceptions import (
    PortfolioError,
    PortfolioSerializationError,
    PortfolioValidationError,
)
from reformlab.templates.portfolios.portfolio import PolicyConfig, PolicyPortfolio

__all__ = [
    "Conflict",
    "ConflictType",
    "PolicyConfig",
    "PolicyPortfolio",
    "PortfolioError",
    "PortfolioValidationError",
    "PortfolioSerializationError",
    "ResolutionStrategy",
    "dump_portfolio",
    "load_portfolio",
    "resolve_conflicts",
    "validate_compatibility",
]


]]></file>
<file id="15cb27f1" path="src/reformlab/templates/portfolios/composition.py" label="SOURCE CODE"><![CDATA[

"""Portfolio YAML serialization, deserialization, and conflict detection.

Story 12.1: Define PolicyPortfolio dataclass and composition logic
Story 12.2: Implement portfolio compatibility validation and conflict resolution
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from reformlab.templates.portfolios.exceptions import (
    PortfolioSerializationError,
    PortfolioValidationError,
)
from reformlab.templates.portfolios.portfolio import PolicyConfig, PolicyPortfolio
from reformlab.templates.schema import PolicyType

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """Types of conflicts that can occur in a portfolio."""

    SAME_POLICY_TYPE = "same_policy_type"
    OVERLAPPING_CATEGORIES = "overlapping_categories"
    OVERLAPPING_YEARS = "overlapping_years"
    PARAMETER_MISMATCH = "parameter_mismatch"


class ResolutionStrategy(Enum):
    """Strategies for resolving portfolio conflicts."""

    ERROR = "error"
    SUM = "sum"
    FIRST_WINS = "first_wins"
    LAST_WINS = "last_wins"
    MAX = "max"


@dataclass(frozen=True)
class Conflict:
    """Represents a detected conflict between policies in a portfolio.

    Attributes:
        conflict_type: Type of conflict detected
        policy_indices: Indices of conflicting policies in the portfolio
        parameter_name: Name of the conflicting parameter (e.g., "policy_type", "rate_schedule")
        conflicting_values: The actual conflicting values
        description: Human-readable description of the conflict
    """

    conflict_type: ConflictType
    policy_indices: tuple[int, ...]
    parameter_name: str
    conflicting_values: tuple[Any, ...]
    description: str

    def __repr__(self) -> str:
        """Readable representation of the conflict."""
        return (
            f"Conflict({self.conflict_type.value}, "
            f"indices={self.policy_indices}, "
            f"parameter={self.parameter_name})"
        )


def portfolio_to_dict(portfolio: PolicyPortfolio) -> dict[str, Any]:
    """Convert PolicyPortfolio to dictionary for YAML serialization.

    Args:
        portfolio: The portfolio to convert

    Returns:
        Dictionary with canonical structure for YAML serialization
    """
    schema_path = Path(__file__).parent.parent / "schema" / "portfolio.schema.json"
    policies_data = []
    for config in portfolio.policies:
        policy_dict: dict[str, Any] = {
            "name": config.name,
            "policy_type": config.policy_type.value,
            "policy": _policy_parameters_to_dict(config.policy),
        }
        policies_data.append(policy_dict)

    return {
        "$schema": str(schema_path),
        "name": portfolio.name,
        "version": portfolio.version,
        "description": portfolio.description,
        "policies": policies_data,
        "resolution_strategy": portfolio.resolution_strategy,
    }


def _policy_parameters_to_dict(policy: Any) -> dict[str, Any]:
    """Convert PolicyParameters to dictionary.

    Args:
        policy: PolicyParameters instance

    Returns:
        Dictionary representation
    """
    result: dict[str, Any] = {}

    # Common fields
    if hasattr(policy, "rate_schedule") and policy.rate_schedule:
        result["rate_schedule"] = dict(policy.rate_schedule)

    if hasattr(policy, "exemptions") and policy.exemptions:
        result["exemptions"] = list(policy.exemptions)

    if hasattr(policy, "thresholds") and policy.thresholds:
        result["thresholds"] = list(policy.thresholds)

    if hasattr(policy, "covered_categories") and policy.covered_categories:
        result["covered_categories"] = list(policy.covered_categories)

    # Carbon tax specific
    if hasattr(policy, "redistribution_type") and policy.redistribution_type:
        result["redistribution"] = {"type": policy.redistribution_type}
        if hasattr(policy, "income_weights") and policy.income_weights:
            result["redistribution"]["income_weights"] = dict(policy.income_weights)

    # Subsidy specific
    if hasattr(policy, "eligible_categories") and policy.eligible_categories:
        result["eligible_categories"] = list(policy.eligible_categories)

    if hasattr(policy, "income_caps") and policy.income_caps:
        result["income_caps"] = dict(policy.income_caps)

    # Rebate specific
    if hasattr(policy, "rebate_type") and policy.rebate_type:
        result["rebate_type"] = policy.rebate_type

    # Rebate income_weights (top-level field, not inside redistribution)
    if (
        hasattr(policy, "income_weights")
        and policy.income_weights
        and not hasattr(policy, "redistribution_type")
    ):
        result["income_weights"] = dict(policy.income_weights)

    # Feebate specific
    if hasattr(policy, "pivot_point") and policy.pivot_point is not None:
        result["pivot_point"] = policy.pivot_point

    if hasattr(policy, "fee_rate") and policy.fee_rate is not None:
        result["fee_rate"] = policy.fee_rate

    if hasattr(policy, "rebate_rate") and policy.rebate_rate is not None:
        result["rebate_rate"] = policy.rebate_rate

    return result


def dict_to_portfolio(data: dict[str, Any]) -> PolicyPortfolio:
    """Convert dictionary to PolicyPortfolio.

    Args:
        data: Dictionary with portfolio data

    Returns:
        PolicyPortfolio instance

    Raises:
        PortfolioValidationError: If data is invalid
    """
    from reformlab.templates.schema import (
        PolicyType,
    )

    # Validate required fields
    if "name" not in data:
        raise PortfolioValidationError(
            summary="Portfolio validation failed",
            reason="missing required field: name",
            fix="Add 'name' field to portfolio YAML",
            invalid_fields=("name",),
        )

    if "policies" not in data:
        raise PortfolioValidationError(
            summary="Portfolio validation failed",
            reason="missing required field: policies",
            fix="Add 'policies' field to portfolio YAML",
            invalid_fields=("policies",),
        )

    policies_data = data.get("policies", [])
    if not isinstance(policies_data, list):
        raise PortfolioValidationError(
            summary="Portfolio validation failed",
            reason="'policies' must be a list",
            fix="Ensure 'policies' is a YAML list",
            invalid_fields=("policies",),
        )

    policies = []
    for idx, policy_data in enumerate(policies_data):
        if not isinstance(policy_data, dict):
            raise PortfolioValidationError(
                summary="Portfolio validation failed",
                reason=f"policies[{idx}] must be a mapping",
                fix=f"Ensure policies[{idx}] is a YAML mapping",
                invalid_fields=(f"policies[{idx}]",),
            )

        if "policy_type" not in policy_data:
            raise PortfolioValidationError(
                summary="Portfolio validation failed",
                reason=f"policies[{idx}] missing required field: policy_type",
                fix=f"Add 'policy_type' to policies[{idx}]",
                invalid_fields=(f"policies[{idx}].policy_type",),
            )

        if "policy" not in policy_data:
            raise PortfolioValidationError(
                summary="Portfolio validation failed",
                reason=f"policies[{idx}] missing required field: policy",
                fix=f"Add 'policy' to policies[{idx}]",
                invalid_fields=(f"policies[{idx}].policy",),
            )

        policy_type_str = policy_data["policy_type"]
        try:
            policy_type = PolicyType(policy_type_str)
        except ValueError:
            raise PortfolioValidationError(
                summary="Portfolio validation failed",
                reason=f"policies[{idx}] has invalid policy_type: {policy_type_str}",
                fix="Use one of: carbon_tax, subsidy, rebate, feebate",
                invalid_fields=(f"policies[{idx}].policy_type",),
            ) from None

        policy_params = _dict_to_policy_parameters(
            policy_data["policy"], policy_type, f"policies[{idx}].policy"
        )

        config = PolicyConfig(
            policy_type=policy_type,
            policy=policy_params,
            name=policy_data.get("name", ""),
        )
        policies.append(config)

    return PolicyPortfolio(
        name=data["name"],
        policies=tuple(policies),
        version=data.get("version", "1.0"),
        description=data.get("description", ""),
        resolution_strategy=data.get("resolution_strategy", "error"),
    )


def _dict_to_policy_parameters(data: dict[str, Any], policy_type: PolicyType, field_path: str) -> Any:
    """Convert dictionary to appropriate PolicyParameters subclass.

    Args:
        data: Policy parameters dictionary
        policy_type: Type of policy
        field_path: Field path for error messages

    Returns:
        PolicyParameters instance

    Raises:
        PortfolioValidationError: If data is invalid
    """
    from reformlab.templates.schema import (
        CarbonTaxParameters,
        FeebateParameters,
        RebateParameters,
        SubsidyParameters,
    )

    # Extract rate_schedule
    rate_schedule_data = data.get("rate_schedule", {})
    if not isinstance(rate_schedule_data, dict):
        raise PortfolioValidationError(
            summary="Portfolio validation failed",
            reason=f"{field_path}.rate_schedule must be a mapping",
            fix=f"Ensure {field_path}.rate_schedule is a YAML mapping",
            invalid_fields=(f"{field_path}.rate_schedule",),
        )

    try:
        rate_schedule = {int(k): float(v) for k, v in rate_schedule_data.items()}
    except (ValueError, TypeError) as exc:
        raise PortfolioValidationError(
            summary="Portfolio validation failed",
            reason=f"{field_path}.rate_schedule has invalid year/rate values: {exc}",
            fix=f"Ensure {field_path}.rate_schedule has integer years and numeric rates",
            invalid_fields=(f"{field_path}.rate_schedule",),
        ) from None

    # Build parameters based on policy type
    if policy_type == PolicyType.CARBON_TAX:
        redistribution_data = data.get("redistribution", {})
        if not isinstance(redistribution_data, dict):
            raise PortfolioValidationError(
                summary="Portfolio validation failed",
                reason=f"{field_path}.redistribution must be a mapping",
                fix=f"Ensure {field_path}.redistribution is a YAML mapping",
                invalid_fields=(f"{field_path}.redistribution",),
            )

        redistribution_type = redistribution_data.get("type", "lump_sum")
        income_weights_data = redistribution_data.get("income_weights", {})
        if not isinstance(income_weights_data, dict):
            raise PortfolioValidationError(
                summary="Portfolio validation failed",
                reason=f"{field_path}.redistribution.income_weights must be a mapping",
                fix=f"Ensure {field_path}.redistribution.income_weights is a YAML mapping",
                invalid_fields=(f"{field_path}.redistribution.income_weights",),
            )

        try:
            income_weights = {k: float(v) for k, v in income_weights_data.items()}
        except (ValueError, TypeError) as exc:
            raise PortfolioValidationError(
                summary="Portfolio validation failed",
                reason=f"{field_path}.redistribution.income_weights has invalid values: {exc}",
                fix=f"Ensure {field_path}.redistribution.income_weights has numeric values",
                invalid_fields=(f"{field_path}.redistribution.income_weights",),
            ) from None

        return CarbonTaxParameters(
            rate_schedule=rate_schedule,
            exemptions=tuple(data.get("exemptions", [])),
            thresholds=tuple(data.get("thresholds", [])),
            covered_categories=tuple(data.get("covered_categories", [])),
            redistribution_type=redistribution_type,
            income_weights=income_weights,
        )

    elif policy_type == PolicyType.SUBSIDY:
        eligible_categories_data = data.get("eligible_categories", [])
        if not isinstance(eligible_categories_data, list):
            raise PortfolioValidationError(
                summary="Portfolio validation failed",
                reason=f"{field_path}.eligible_categories must be a list",
                fix=f"Ensure {field_path}.eligible_categories is a YAML list",
                invalid_fields=(f"{field_path}.eligible_categories",),
            )

        income_caps_data = data.get("income_caps", {})
        if not isinstance(income_caps_data, dict):
            raise PortfolioValidationError(
                summary="Portfolio validation failed",
                reason=f"{field_path}.income_caps must be a mapping",
                fix=f"Ensure {field_path}.income_caps is a YAML mapping",
                invalid_fields=(f"{field_path}.income_caps",),
            )

        try:
            income_caps = {k: float(v) for k, v in income_caps_data.items()}
        except (ValueError, TypeError) as exc:
            raise PortfolioValidationError(
                summary="Portfolio validation failed",
                reason=f"{field_path}.income_caps has invalid values: {exc}",
                fix=f"Ensure {field_path}.income_caps has numeric values",
                invalid_fields=(f"{field_path}.income_caps",),
            ) from None

        return SubsidyParameters(
            rate_schedule=rate_schedule,
            exemptions=tuple(data.get("exemptions", [])),
            thresholds=tuple(data.get("thresholds", [])),
            covered_categories=tuple(data.get("covered_categories", [])),
            eligible_categories=tuple(eligible_categories_data),
            income_caps=income_caps,
        )

    elif policy_type == PolicyType.REBATE:
        rebate_type = data.get("rebate_type", "lump_sum")
        income_weights_data = data.get("income_weights", {})
        if not isinstance(income_weights_data, dict):
            raise PortfolioValidationError(
                summary="Portfolio validation failed",
                reason=f"{field_path}.income_weights must be a mapping",
                fix=f"Ensure {field_path}.income_weights is a YAML mapping",
                invalid_fields=(f"{field_path}.income_weights",),
            )

        try:
            income_weights = {k: float(v) for k, v in income_weights_data.items()}
        except (ValueError, TypeError) as exc:
            raise PortfolioValidationError(
                summary="Portfolio validation failed",
                reason=f"{field_path}.income_weights has invalid values: {exc}",
                fix=f"Ensure {field_path}.income_weights has numeric values",
                invalid_fields=(f"{field_path}.income_weights",),
            ) from None

        return RebateParameters(
            rate_schedule=rate_schedule,
            exemptions=tuple(data.get("exemptions", [])),
            thresholds=tuple(data.get("thresholds", [])),
            covered_categories=tuple(data.get("covered_categories", [])),
            rebate_type=rebate_type,
            income_weights=income_weights,
        )

    elif policy_type == PolicyType.FEEBATE:
        try:
            pivot_point = float(data["pivot_point"]) if "pivot_point" in data else 0.0
            fee_rate = float(data["fee_rate"]) if "fee_rate" in data else 0.0
            rebate_rate = float(data["rebate_rate"]) if "rebate_rate" in data else 0.0
        except (ValueError, TypeError) as exc:
            raise PortfolioValidationError(
                summary="Portfolio validation failed",
                reason=f"{field_path} has invalid feebate numeric values: {exc}",
                fix=f"Ensure {field_path} pivot_point, fee_rate, and rebate_rate are numeric",
                invalid_fields=(
                    f"{field_path}.pivot_point",
                    f"{field_path}.fee_rate",
                    f"{field_path}.rebate_rate",
                ),
            ) from None

        return FeebateParameters(
            rate_schedule=rate_schedule,
            exemptions=tuple(data.get("exemptions", [])),
            thresholds=tuple(data.get("thresholds", [])),
            covered_categories=tuple(data.get("covered_categories", [])),
            pivot_point=pivot_point,
            fee_rate=fee_rate,
            rebate_rate=rebate_rate,
        )

    else:
        raise PortfolioValidationError(
            summary="Portfolio validation failed",
            reason=f"Unsupported policy_type: {policy_type.value}",
            fix="Use one of: carbon_tax, subsidy, rebate, feebate",
            invalid_fields=(f"{field_path}.policy_type",),
        )


def validate_compatibility(portfolio: PolicyPortfolio) -> tuple[Conflict, ...]:
    """Validate portfolio for compatibility conflicts.

    Args:
        portfolio: The portfolio to validate

    Returns:
        Tuple of detected conflicts (empty if no conflicts)
    """
    conflicts: list[Conflict] = []

    # Detect same policy type conflicts
    for i in range(len(portfolio.policies)):
        for j in range(i + 1, len(portfolio.policies)):
            if i >= j:
                continue
            if portfolio.policies[i].policy_type == portfolio.policies[j].policy_type:
                conflict = Conflict(
                    conflict_type=ConflictType.SAME_POLICY_TYPE,
                    policy_indices=(i, j),
                    parameter_name="policy_type",
                    conflicting_values=(
                        portfolio.policies[i].policy_type.value,
                        portfolio.policies[j].policy_type.value,
                    ),
                    description=f"Both policies[{i}] and [{j}] are {portfolio.policies[i].policy_type.value}",
                )
                conflicts.append(conflict)

    # Detect overlapping years conflicts
    for i in range(len(portfolio.policies)):
        for j in range(i + 1, len(portfolio.policies)):
            if i >= j:
                continue
            policy_i_years = set(portfolio.policies[i].policy.rate_schedule.keys())
            policy_j_years = set(portfolio.policies[j].policy.rate_schedule.keys())
            overlap = policy_i_years & policy_j_years
            if overlap:
                conflict = Conflict(
                    conflict_type=ConflictType.OVERLAPPING_YEARS,
                    policy_indices=(i, j),
                    parameter_name="rate_schedule",
                    conflicting_values=(
                        tuple(sorted(policy_i_years)),
                        tuple(sorted(policy_j_years)),
                    ),
                    description=f"rate_schedule years overlap: {overlap}",
                )
                conflicts.append(conflict)

    # Detect overlapping categories conflicts
    for i in range(len(portfolio.policies)):
        for j in range(i + 1, len(portfolio.policies)):
            if i >= j:
                continue
            policy_i_cats = getattr(portfolio.policies[i].policy, "covered_categories", ())
            policy_j_cats = getattr(portfolio.policies[j].policy, "eligible_categories", ())
            overlap = set(policy_i_cats) & set(policy_j_cats)
            if overlap:
                conflict = Conflict(
                    conflict_type=ConflictType.OVERLAPPING_CATEGORIES,
                    policy_indices=(i, j),
                    parameter_name="categories",
                    conflicting_values=(
                        tuple(sorted(policy_i_cats)),
                        tuple(sorted(policy_j_cats)),
                    ),
                    description=f"categories overlap: {overlap}",
                )
                conflicts.append(conflict)

    # Sort conflicts by policy indices, then parameter name for deterministic ordering
    conflicts.sort(key=lambda c: (c.policy_indices[0], c.parameter_name))

    return tuple(conflicts)


def resolve_conflicts(portfolio: PolicyPortfolio, conflicts: tuple[Conflict, ...]) -> PolicyPortfolio:
    """Resolve conflicts according to portfolio's resolution strategy.

    Args:
        portfolio: The portfolio with conflicts
        conflicts: Detected conflicts

    Returns:
        New portfolio with resolved conflicts (if strategy != "error")

    Raises:
        PortfolioValidationError: If strategy is "error" and conflicts exist
    """
    if not conflicts:
        return portfolio

    if portfolio.resolution_strategy == "error":
        conflict_details = "\n".join(f"  - {c.description}" for c in conflicts)
        raise PortfolioValidationError(
            summary="Portfolio has unresolved conflicts",
            reason=f"{len(conflicts)} conflicts detected:\n{conflict_details}",
            fix="Set resolution_strategy to 'sum', 'first_wins', 'last_wins', or 'max' "
            "to automatically resolve conflicts",
            invalid_fields=tuple(f"policies[{i}]" for c in conflicts for i in c.policy_indices),
        )

    # Log warning for non-error strategies
    logger.warning(
        "event=portfolio_conflicts strategy=%s conflict_count=%d portfolio=%s",
        portfolio.resolution_strategy,
        len(conflicts),
        portfolio.name,
    )

    # Apply resolution strategy
    if portfolio.resolution_strategy == "sum":
        resolved_policies = _apply_sum_strategy(portfolio.policies, conflicts)
    elif portfolio.resolution_strategy == "first_wins":
        resolved_policies = _apply_first_wins_strategy(portfolio.policies, conflicts)
    elif portfolio.resolution_strategy == "last_wins":
        resolved_policies = _apply_last_wins_strategy(portfolio.policies, conflicts)
    elif portfolio.resolution_strategy == "max":
        resolved_policies = _apply_max_strategy(portfolio.policies, conflicts)
    else:
        # Unknown strategy - treat as error
        raise PortfolioValidationError(
            summary="Invalid resolution strategy",
            reason=f"Unknown resolution_strategy: {portfolio.resolution_strategy}",
            fix="Use one of: error, sum, first_wins, last_wins, max",
            invalid_fields=("resolution_strategy",),
        )

    # Create description suffix
    description_suffix = (
        f"\n\nResolved {len(conflicts)} conflicts using '{portfolio.resolution_strategy}' strategy."
    )

    # Return new portfolio with resolved policies
    return PolicyPortfolio(
        name=portfolio.name,
        policies=resolved_policies,
        version=portfolio.version,
        description=portfolio.description + description_suffix,
        resolution_strategy=portfolio.resolution_strategy,
    )


def _apply_sum_strategy(policies: tuple[Any, ...], conflicts: tuple[Conflict, ...]) -> tuple[Any, ...]:
    """Apply sum resolution strategy - add rates for overlapping years.

    Args:
        policies: Original policies
        conflicts: Detected conflicts

    Returns:
        New tuple of policies with resolved rate schedules
    """

    resolved = list(policies)

    # Group conflicts by overlapping years
    year_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.OVERLAPPING_YEARS]

    # For each overlapping year conflict, add the rates
    for conflict in year_conflicts:
        i, j = conflict.policy_indices[0], conflict.policy_indices[1]
        policy_i = resolved[i]
        policy_j = resolved[j]

        # Get overlapping years
        years_i = set(policy_i.policy.rate_schedule.keys())
        years_j = set(policy_j.policy.rate_schedule.keys())
        overlap_years = years_i & years_j

        # Add rates for overlapping years (apply to policy with lower index)
        new_rate_schedule = dict(policy_i.policy.rate_schedule)
        for year in overlap_years:
            new_rate_schedule[year] = (
                policy_i.policy.rate_schedule[year] + policy_j.policy.rate_schedule[year]
            )

        # Create new policy with merged rate schedule
        new_policy = replace(policy_i.policy, rate_schedule=new_rate_schedule)
        resolved[i] = replace(policy_i, policy=new_policy)

    return tuple(resolved)


def _apply_first_wins_strategy(policies: tuple[Any, ...], conflicts: tuple[Conflict, ...]) -> tuple[Any, ...]:
    """Apply first_wins resolution strategy - use first policy's values.

    Args:
        policies: Original policies
        conflicts: Detected conflicts

    Returns:
        Original policies tuple (first policy already wins by definition)
    """
    # First policy wins by definition - no changes needed
    return policies


def _apply_last_wins_strategy(policies: tuple[Any, ...], conflicts: tuple[Conflict, ...]) -> tuple[Any, ...]:
    """Apply last_wins resolution strategy - use last policy's values.

    Args:
        policies: Original policies
        conflicts: Detected conflicts

    Returns:
        New tuple with last conflicting policy values
    """

    resolved = list(policies)

    # For overlapping years, use last policy's rates
    year_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.OVERLAPPING_YEARS]

    for conflict in year_conflicts:
        i, j = conflict.policy_indices[0], conflict.policy_indices[1]
        policy_i = resolved[i]
        policy_j = resolved[j]

        # Get overlapping years
        years_i = set(policy_i.policy.rate_schedule.keys())
        years_j = set(policy_j.policy.rate_schedule.keys())
        overlap_years = years_i & years_j

        # Use last policy's rates for overlapping years
        new_rate_schedule = dict(policy_i.policy.rate_schedule)
        for year in overlap_years:
            new_rate_schedule[year] = policy_j.policy.rate_schedule[year]

        # Create new policy with updated rate schedule
        new_policy = replace(policy_i.policy, rate_schedule=new_rate_schedule)
        resolved[i] = replace(policy_i, policy=new_policy)

    return tuple(resolved)


def _apply_max_strategy(policies: tuple[Any, ...], conflicts: tuple[Conflict, ...]) -> tuple[Any, ...]:
    """Apply max resolution strategy - use maximum rate for overlapping years.

    Args:
        policies: Original policies
        conflicts: Detected conflicts

    Returns:
        New tuple of policies with maximum rates applied
    """

    resolved = list(policies)

    # For overlapping years, use maximum rate
    year_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.OVERLAPPING_YEARS]

    for conflict in year_conflicts:
        i, j = conflict.policy_indices[0], conflict.policy_indices[1]
        policy_i = resolved[i]
        policy_j = resolved[j]

        # Get overlapping years
        years_i = set(policy_i.policy.rate_schedule.keys())
        years_j = set(policy_j.policy.rate_schedule.keys())
        overlap_years = years_i & years_j

        # Use maximum rate for overlapping years
        new_rate_schedule = dict(policy_i.policy.rate_schedule)
        for year in overlap_years:
            new_rate_schedule[year] = max(
                policy_i.policy.rate_schedule[year], policy_j.policy.rate_schedule[year]
            )

        # Create new policy with updated rate schedule
        new_policy = replace(policy_i.policy, rate_schedule=new_rate_schedule)
        resolved[i] = replace(policy_i, policy=new_policy)

    return tuple(resolved)


def dump_portfolio(portfolio: PolicyPortfolio, path: Path | str) -> None:
    """Serialize portfolio to YAML file with canonical formatting.

    Args:
        portfolio: The portfolio to serialize
        path: Output file path
    """
    file_path = Path(path)
    data = portfolio_to_dict(portfolio)

    with open(file_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=True)


def load_portfolio(path: Path | str, validate: bool = True) -> PolicyPortfolio:
    """Load portfolio from YAML file.

    Args:
        path: Path to YAML file
        validate: Whether to validate for conflicts (default: True)

    Returns:
        PolicyPortfolio instance

    Raises:
        PortfolioSerializationError: If file not found or invalid YAML
        PortfolioValidationError: If data is invalid or conflicts detected
    """
    file_path = Path(path)

    if not file_path.exists():
        raise PortfolioSerializationError(
            summary="Portfolio load failed",
            reason=f"file was not found: {file_path}",
            fix="Provide an existing .yaml or .yml portfolio file path",
            file_path=file_path,
        )

    try:
        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise PortfolioSerializationError(
            summary="Portfolio load failed",
            reason=f"invalid YAML syntax: {exc}",
            fix="Fix the YAML syntax errors in the portfolio file",
            file_path=file_path,
        ) from None

    if not isinstance(data, dict):
        raise PortfolioValidationError(
            summary="Portfolio load failed",
            reason="portfolio file must contain a YAML mapping (dict)",
            fix="Ensure the file has top-level keys: name, version, policies",
            file_path=file_path,
        )

    portfolio = dict_to_portfolio(data)

    # Validate for conflicts if requested
    if validate:
        conflicts = validate_compatibility(portfolio)
        portfolio = resolve_conflicts(portfolio, conflicts)

    return portfolio


]]></file>
<file id="90dfc412" path="[ANTIPATTERNS - DO NOT REPEAT]" label="VIRTUAL CONTENT"><![CDATA[

# Epic 12 - Code Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during code review of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent implementation mistakes (race conditions, missing tests, weak assertions, etc.)

## Story 12-1 (2026-03-05)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Immutability breach - `list_policies()` returns direct reference to mutable `rate_schedule` dict, allowing external mutation of internal state. | Changed line 116 to return `dict(config.policy.rate_schedule)` instead of direct reference |
| high | Package integration gap - Portfolio types not exported from `reformlab.templates` | Added PolicyConfig, PolicyPortfolio, and portfolio exceptions to imports and __all__ list |
| high | Schema too permissive - No `additionalProperties: false` at root/policy levels, typos silently accepted | Added `additionalProperties: false` to root, policy item, and policy.parameters objects |
| high | Test data format mismatch - Test uses `redistribution_type` but loader expects `redistribution: {type: ...}` | Updated test to use canonical nested format |
| high | Unused imports - `yaml` imported but not used in test file, **Source**: Reviewer A | Removed unused `yaml` import |
| medium | Lint violations - Unused `PolicyType` import and unused `lines` variable | Removed unused imports |
| medium | Story traceability incomplete - Tasks marked incomplete despite implementation | Deferred (not applying - outside scope of code fixes) |


]]></file>
<file id="1d910d88" path="[Validator A]" label="VALIDATION OUTPUT"><![CDATA[

**🔥 ADVERSARIAL CODE REVIEW COMPLETE, Lucas!**

**Story:** /Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/12-2-implement-portfolio-compatibility-validation-and-conflict-resolution.md

---

## 📊 Review Summary

| Category | Issues Found |
|----------|--------------|
| Git vs Story Discrepancies | 1 |
| AC Implementation Gaps | 2 |
| Task Completion Lies | 2 |
| SOLID Violations | 0 |
| Hidden Bugs | 0 |
| Performance Footguns | 0 |
| Security Vulnerabilities | 0 |
| **Total Issues** | **5** |

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🔴 CRITICAL | Missing `PARAMETER_MISMATCH` Conflict Detection. Task 3.5 was marked complete, but the `validate_compatibility` function completely lacks logic to detect `PARAMETER_MISMATCH` conflicts, despite the `ConflictType` enum defining it. This is a critical functional omission. | src/reformlab/templates/portfolios/composition.py:108 | +3 |
| 🔴 CRITICAL | Incomplete Conflict Resolution Strategies. The "sum", "first_wins", "last_wins", and "max" resolution strategies (`_apply_*_strategy` functions) are only implemented to handle `rate_schedule` for `OVERLAPPING_YEARS` conflicts. They fail to address other conflict types like `SAME_POLICY_TYPE` or `OVERLAPPING_CATEGORIES` for other parameters. This severely limits the practical utility of these strategies and contradicts the broader intent of AC3. | src/reformlab/templates/portfolios/composition.py:657 | +3 |
| 🔴 CRITICAL | Task 6.18 (Test Coverage) Claimed as Complete but Failed. The story file explicitly marks Task 6.18 ("Run `uv run pytest ...` to verify >90% coverage") as complete, yet the "Implementation Summary" states "9/23 tests passing (39% pass rate)". This is a direct contradiction and a critical misrepresentation of completion status. | _bmad-output/implementation-artifacts/12-2-implement-portfolio-compatibility-validation-and-conflict-resolution.md:144 | +3 |
| 🟠 IMPORTANT | Lying Test: `test_first_wins_strategy`. The `_apply_first_wins_strategy` function returns the original policies unchanged. The test `test_first_wins_strategy` passes deceptively because the first policy's rate for 2027 was already the desired value. However, this does not represent true conflict resolution where conflicting aspects of later policies are superseded or removed. | tests/templates/portfolios/test_conflicts.py:277 | +1 |
| 🟠 IMPORTANT | Hardcoded `resolution_strategy` Validation. The `PolicyPortfolio.__post_init__` method validates the `resolution_strategy` against a hardcoded set of strings. This duplicates the `ResolutionStrategy` enum and creates a maintenance burden. It should directly use the enum values for consistency. | src/reformlab/templates/portfolios/portfolio.py:79 | +1 |
| 🟠 IMPORTANT | Test Coverage Gap for Resolution Strategies. The tests for "sum", "last_wins", and "max" resolution strategies (`test_conflicts.py`) only verify behavior for `rate_schedule` conflicts in `OVERLAPPING_YEARS`. They do not cover scenarios with other conflict types or parameters, leaving significant gaps given the incomplete implementation of these strategies. | tests/templates/portfolios/test_conflicts.py:240 | +1 |
| 🟡 MINOR | Insufficient Inline Comments for Resolution Scope. The inline comments within `_apply_*_strategy` functions in `composition.py` (e.g., `_apply_sum_strategy`) are too brief and fail to clarify that the current resolution logic is limited exclusively to `rate_schedule` for `OVERLAPPING_YEARS` conflicts, violating Task 7.5. | src/reformlab/templates/portfolios/composition.py:657 | +0.3 |
| 🟡 MINOR | Unrelated File Added in `git-diff`. The file `scripts/check_ai_usage.py` was added as part of the changes but is entirely unrelated to Story 12.2. This indicates a lack of proper commit hygiene or focused development. | scripts/check_ai_usage.py | +0.3 |
| 🟢 CLEAN PASS | 5 categories with no issues | | -2.5 |

### Evidence Score: 10.1

| Score | Verdict |
|-------|---------|
| **10.1** | **REJECT** |

---

## 🏛️ Architectural Sins

✅ No significant architectural violations detected.

---

## 🐍 Pythonic Crimes &amp; Readability

- **Type Safety:** The validation of `resolution_strategy` in `PolicyPortfolio.__post_init__` duplicates the `ResolutionStrategy` enum. This violates the DRY principle and introduces a maintenance risk.
  - 📍 `src/reformlab/templates/portfolios/portfolio.py:79`
- **Readability/Clarity:** The inline comments for the resolution strategy functions (`_apply_sum_strategy`, `_apply_first_wins_strategy`, etc.) are inadequate. They do not clearly state that the resolution logic is narrowly focused on `rate_schedule` and `OVERLAPPING_YEARS`, despite the broader implications of the strategy names.
  - 📍 `src/reformlab/templates/portfolios/composition.py:657`

---

## ⚡ Performance &amp; Scalability

✅ No significant performance issues detected.

---

## 🐛 Correctness &amp; Safety

- **🐛 Bug (Functional Gap):** The `PARAMETER_MISMATCH` conflict detection (Task 3.5) is entirely absent from the `validate_compatibility` function. This means a critical type of conflict, where policies might affect the same categories with different parameters, will go undetected.
  - 📍 `src/reformlab/templates/portfolios/composition.py:108`
  - 🔄 Reproduction: Create a portfolio with two policies (e.g., a carbon tax and a subsidy) both applying to "transport", but with different income caps or redistribution types, then call `validate_compatibility()`. No `PARAMETER_MISMATCH` conflict will be reported.
- **🐛 Bug (Functional Gap):** The conflict resolution strategies ("sum", "first_wins", "last_wins", "max") are severely incomplete. They only apply resolution logic to `rate_schedule` parameters for `OVERLAPPING_YEARS` conflicts. Other conflict types (e.g., `SAME_POLICY_TYPE`, `OVERLAPPING_CATEGORIES`) and other conflicting parameters are not resolved, leading to potentially inconsistent or incorrect policy application.
  - 📍 `src/reformlab/templates/portfolios/composition.py:657`
  - 🔄 Reproduction: Create a portfolio with two carbon taxes (`SAME_POLICY_TYPE` conflict), where each policy specifies different `covered_categories`. Apply a resolution strategy like "sum". The `covered_categories` will remain unresolved for both policies.
- **🎭 Lying Test:** `test_first_wins_strategy` in `test_conflicts.py` is misleading. The `_apply_first_wins_strategy` function simply returns the original policies without modifying them. While the test passes because the `rate_schedule` of the first policy (`policy1`) matches the expected value, this doesn't mean a conflict was actually resolved in a "first wins" manner against `policy2`. If a later processing step applied `policy2`'s `rate_schedule`, the "first wins" intent would be violated.
  - 📍 `tests/templates/portfolios/test_conflicts.py:277`
  - 🤥 Why it lies: The test passes by accident of setup, not by verification of the intended "first wins" logic being fully applied to conflicting parameters across policies. The resolution function itself is effectively a no-op for `first_wins`.

---

## 🔧 Maintainability Issues

- **💣 Tech Debt:** The validation of `resolution_strategy` in `PolicyPortfolio.__post_init__` uses a hardcoded set of strings. If the `ResolutionStrategy` enum is modified, this hardcoded list must also be manually updated, leading to potential inconsistencies and errors.
  - 📍 `src/reformlab/templates/portfolios/portfolio.py:79`
  - 💥 Explosion radius: Any future changes to `ResolutionStrategy` enum.

---

## 🛠️ Suggested Fixes

### 1. Implement Missing `PARAMETER_MISMATCH` Detection

**File:** `src/reformlab/templates/portfolios/composition.py`
**Issue:** The `validate_compatibility` function does not include logic to detect `PARAMETER_MISMATCH` conflicts, which is a key requirement for comprehensive conflict detection.

```diff
--- a/src/reformlab/templates/portfolios/composition.py
+++ b/src/reformlab/templates/portfolios/composition.py
@@ -530,6 +530,23 @@
                 )
                 conflicts.append(conflict)
 
+    # Detect PARAMETER_MISMATCH conflicts (placeholder, requires more specific logic based on PolicyParameters attributes)
+    # This is a complex detection that would iterate through policy parameters and look for conflicting values
+    # for the same logical attribute across different policies. For now, it's noted as a missing piece.
+    # Example: Two policies affecting the same 'category' but with conflicting 'income_caps' or 'rebate_type'.
+    # This requires a more generic way to identify "conflicting parameters" beyond just rate_schedule.
+    # For now, we add a placeholder to ensure the task is acknowledged as incomplete here.
+    # if False: # This block is intentionally commented out to signify missing implementation
+    #     conflict = Conflict(
+    #         conflict_type=ConflictType.PARAMETER_MISMATCH,
+    #         policy_indices=(0, 1), # Example indices
+    #         parameter_name="example_parameter",
+    #         conflicting_values=("value_A", "value_B"),
+    #         description="Placeholder for PARAMETER_MISMATCH conflict detection"
+    #     )
+    #     conflicts.append(conflict)
+
+
     # Sort conflicts by policy indices, then parameter name for deterministic ordering
     conflicts.sort(key=lambda c: (c.policy_indices[0], c.parameter_name))
 

```

### 2. Generalize Conflict Resolution Strategies

**File:** `src/reformlab/templates/portfolios/composition.py`
**Issue:** The current resolution strategies (`sum`, `first_wins`, `last_wins`, `max`) only handle `rate_schedule` conflicts for `OVERLAPPING_YEARS`. They do not extend to other parameters or conflict types (e.g., `SAME_POLICY_TYPE`, `OVERLAPPING_CATEGORIES`), rendering them incomplete. The example below shows how to generalize `_apply_first_wins_strategy` for `SAME_POLICY_TYPE` by ensuring only one policy of that type remains. Similar generalization is needed for other strategies and conflict types/parameters.

```diff
--- a/src/reformlab/templates/portfolios/composition.py
+++ b/src/reformlab/templates/portfolios/composition.py
@@ -700,12 +700,27 @@
     Returns:
         Original policies tuple (first policy already wins by definition)
     """
-    # First policy wins by definition - no changes needed
-    return policies
+    resolved_policies_list = list(policies)
+    policies_to_remove = set()
+
+    # Handle SAME_POLICY_TYPE conflicts: only keep the first policy of a conflicting type.
+    # This assumes "first wins" means the first-encountered policy's type definition takes precedence,
+    # and subsequent policies of the same type are effectively ignored or removed.
+    same_type_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.SAME_POLICY_TYPE]
+    for conflict in same_type_conflicts:
+        # The conflict identifies two policies i and j of the same type.
+        # If first_wins, then policy with higher index (j) should be removed or ignored.
+        _, j = conflict.policy_indices[0], conflict.policy_indices[1]
+        policies_to_remove.add(j)
+
+    # Create a new list of policies, excluding those that "lost" the conflict.
+    final_policies = [policy for idx, policy in enumerate(resolved_policies_list) if idx not in policies_to_remove]
+
+    return tuple(final_policies)
 
 
 def _apply_last_wins_strategy(policies: tuple[Any, ...], conflicts: tuple[Conflict, ...]) -> tuple[Any, ...]:
-    """Apply last_wins resolution strategy - use last policy's values.
+    """Apply last_wins resolution strategy.
 
     Args:
         policies: Original policies
@@ -714,28 +729,38 @@
     Returns:
         New tuple with last conflicting policy values
     """
-
-    resolved = list(policies)
-
-    # For overlapping years, use last policy's rates
-    year_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.OVERLAPPING_YEARS]
-
-    for conflict in year_conflicts:
-        i, j = conflict.policy_indices[0], conflict.policy_indices[1]
-        policy_i = resolved[i]
-        policy_j = resolved[j]
-
-        # Get overlapping years
-        years_i = set(policy_i.policy.rate_schedule.keys())
-        years_j = set(policy_j.policy.rate_schedule.keys())
-        overlap_years = years_i & years_j
-
-        # Use last policy's rates for overlapping years
-        new_rate_schedule = dict(policy_i.policy.rate_schedule)
-        for year in overlap_years:
-            new_rate_schedule[year] = policy_j.policy.rate_schedule[year]
-
-        # Create new policy with updated rate schedule
-        new_policy = replace(policy_i.policy, rate_schedule=new_rate_schedule)
-        resolved[i] = replace(policy_i, policy=new_policy)
-
-    return tuple(resolved)
+    resolved_policies_list = list(policies)
+    policies_to_remove = set()
+
+    # Handle SAME_POLICY_TYPE conflicts: only keep the last policy of a conflicting type.
+    same_type_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.SAME_POLICY_TYPE]
+    # For last_wins, policies with lower indices in a conflict should be removed.
+    for conflict in same_type_conflicts:
+        i, _ = conflict.policy_indices[0], conflict.policy_indices[1]
+        policies_to_remove.add(i)
+
+    # Handle OVERLAPPING_YEARS conflicts
+    year_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.OVERLAPPING_YEARS]
+
+    for conflict in year_conflicts:
+        i_idx, j_idx = conflict.policy_indices[0], conflict.policy_indices[1]
+        policy_i = resolved_policies_list[i_idx]
+        policy_j = resolved_policies_list[j_idx]
+
+        years_i = set(policy_i.policy.rate_schedule.keys())
+        years_j = set(policy_j.policy.rate_schedule.keys())
+        overlap_years = years_i & years_j
+
+        # The last policy in the conflict (policy_j) wins for overlapping rate_schedule years.
+        # We need to modify policy_i's rate_schedule to reflect policy_j's values for overlaps.
+        new_rate_schedule_i = dict(policy_i.policy.rate_schedule)
+        for year in overlap_years:
+            new_rate_schedule_i[year] = policy_j.policy.rate_schedule[year]
+
+        # Update policy_i in the list.
+        resolved_policies_list[i_idx] = replace(policy_i, policy=replace(policy_i.policy, rate_schedule=new_rate_schedule_i))
+
+    # Filter out policies that were designated to be removed due to SAME_POLICY_TYPE conflict
+    final_policies = [policy for idx, policy in enumerate(resolved_policies_list) if idx not in policies_to_remove]
+
+    return tuple(final_policies)
```

### 3. Update `PolicyPortfolio` `__post_init__` to Use Enum Values

**File:** `src/reformlab/templates/portfolios/portfolio.py`
**Issue:** The validation for `resolution_strategy` uses a hardcoded set of strings instead of referencing the `ResolutionStrategy` enum, creating redundancy and a maintenance risk.

```diff
--- a/src/reformlab/templates/portfolios/portfolio.py
+++ b/src/reformlab/templates/portfolios/portfolio.py
@@ -6,6 +6,7 @@
 from typing import TYPE_CHECKING, Any
 
 from reformlab.templates.portfolios.exceptions import PortfolioValidationError
+from reformlab.templates.portfolios.composition import ResolutionStrategy
 from reformlab.templates.schema import PolicyParameters, PolicyType, infer_policy_type
 
 if TYPE_CHECKING:
@@ -76,12 +77,13 @@
             )
 
         # Validate resolution_strategy is a valid enum value
-        valid_strategies = {"error", "sum", "first_wins", "last_wins", "max"}
-        if self.resolution_strategy not in valid_strategies:
+        # Use ResolutionStrategy enum values directly for consistency
+        valid_strategy_values = {s.value for s in ResolutionStrategy}
+        if self.resolution_strategy not in valid_strategy_values:
             raise PortfolioValidationError(
                 summary="Invalid resolution strategy",
                 reason=(
-                    f"resolution_strategy must be one of {valid_strategies}, got {self.resolution_strategy!r}"
+                    f"resolution_strategy must be one of {valid_strategy_values}, got {self.resolution_strategy!r}"
                 ),
-                fix=f"Use one of: {', '.join(sorted(valid_strategies))}",
+                fix=f"Use one of: {', '.join(sorted(valid_strategy_values))}",
                 invalid_fields=("resolution_strategy",),
             )

```

### 4. Remove Unrelated File `scripts/check_ai_usage.py`

**File:** `scripts/check_ai_usage.py`
**Issue:** This file was added as part of the story's changes but is completely unrelated to implementing portfolio compatibility. It should be removed or moved to a separate, appropriately scoped change.

**Corrected code:** (Removal of file)
```
Remove the file: scripts/check_ai_usage.py
```

### 5. Add Missing Tests for `PARAMETER_MISMATCH` and Generalize Resolution Strategy Tests

**File:** `tests/templates/portfolios/test_conflicts.py`
**Issue:** Tests are missing for the `PARAMETER_MISMATCH` conflict type (due to missing implementation). Additionally, existing tests for resolution strategies (`sum`, `first_wins`, `last_wins`, `max`) only cover `rate_schedule` for `OVERLAPPING_YEARS`, failing to test for other conflict types or parameters, which is critical given the current incomplete resolution implementation.

**Corrected code:**
```python
# No automated fix provided. This requires manual implementation of new tests and generalization of existing tests.
# New tests should be added for PARAMETER_MISMATCH conflicts once the detection logic is implemented.
# Existing tests for resolution strategies should be expanded to cover SAME_POLICY_TYPE, OVERLAPPING_CATEGORIES,
# and other conflicting parameters, not just rate_schedule for overlapping years.

# Example of a new test for PARAMETER_MISMATCH (once implemented):
# def test_detect_parameter_mismatch_conflict(self) -> None:
#     """Detect conflict when policies affect same category with different parameters."""
#     # Setup policies that conflict on a parameter (e.g., covered_categories with different values for the same logical category)
#     tax1 = CarbonTaxParameters(rate_schedule={2026: 50}, covered_categories=("transport",))
#     tax2 = CarbonTaxParameters(rate_schedule={2026: 50}, covered_categories=("transport", "heating"))
#     policy1 = PolicyConfig(policy_type=PolicyType.CARBON_TAX, policy=tax1, name="Tax A")
#     policy2 = PolicyConfig(policy_type=PolicyType.CARBON_TAX, policy=tax2, name="Tax B")
#     portfolio = PolicyPortfolio(name="Parameter Mismatch", policies=(policy1, policy2))
#     conflicts = validate_compatibility(portfolio)
#     assert any(c.conflict_type == ConflictType.PARAMETER_MISMATCH for c in conflicts)

# Example of expanding existing tests:
# The `test_first_wins_strategy` (and others) should be updated to verify that conflicting parameters
# beyond rate_schedule are also correctly resolved according to the strategy. For instance, if `SAME_POLICY_TYPE`
# conflict results in one policy being "removed" for `first_wins`, then assertions should reflect that removal.
```

**✅ CODE REVIEW FINALIZED, Lucas!**

**Story:** /Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/12-2-implement-portfolio-compatibility-validation-and-conflict-resolution.md
**Evidence Score:** 10.1 → **REJECT**

**Review Actions:**
- Issues Found: 5
- Issues Fixed: 0
- Action Items Created: 0

🚫 Code requires significant rework. Review action items carefully.

]]></file>
<file id="557aedd2" path="[Validator B]" label="VALIDATION OUTPUT"><![CDATA[

**Adversarial Code Review Report — Story 12.2**

## Findings (ordered by severity)

1. 🔴 **Task marked done but not implemented (`PARAMETER_MISMATCH`)**
Evidence: `ConflictType.PARAMETER_MISMATCH` exists, but `validate_compatibility()` never creates that conflict type ([composition.py:27](/Users/lucas/Workspace/reformlab/src/reformlab/templates/portfolios/composition.py:27), [composition.py:427](/Users/lucas/Workspace/reformlab/src/reformlab/templates/portfolios/composition.py:427)).
Impact: Task 3.5 is a false completion claim; conflict coverage is incomplete.

2. 🟠 **AC3 is only partially implemented**
Evidence: `sum`, `max`, `first_wins`, `last_wins` logic only touches `OVERLAPPING_YEARS`; other conflicts are silently left unresolved ([composition.py:495](/Users/lucas/Workspace/reformlab/src/reformlab/templates/portfolios/composition.py:495), [composition.py:560](/Users/lucas/Workspace/reformlab/src/reformlab/templates/portfolios/composition.py:560)).
Impact: portfolio can be reported as “resolved” while still conflicting on policy type/categories.

3. 🟠 **Category conflict detection is asymmetric and misses valid conflicts**
Evidence: compares `covered_categories` from policy i only against `eligible_categories` from policy j only ([composition.py:467](/Users/lucas/Workspace/reformlab/src/reformlab/templates/portfolios/composition.py:467)).
Impact: misses `covered↔covered`, `eligible↔eligible`, and reverse-direction overlaps.

4. 🟠 **Determinism claim (AC5) is violated in conflict descriptions**
Evidence: descriptions embed raw `set` representations (`{...}`) for overlaps ([composition.py:460](/Users/lucas/Workspace/reformlab/src/reformlab/templates/portfolios/composition.py:460), [composition.py:482](/Users/lucas/Workspace/reformlab/src/reformlab/templates/portfolios/composition.py:482)).
Impact: output text order can vary by hash seed/process, breaking byte-stable behavior.

5. 🟠 **Unhandled input type bug in `dict_to_portfolio` path**
Evidence: `policy_data["policy"]` is not validated as mapping before `_dict_to_policy_parameters()` calls `.get()` ([composition.py:221](/Users/lucas/Workspace/reformlab/src/reformlab/templates/portfolios/composition.py:221), [composition.py:258](/Users/lucas/Workspace/reformlab/src/reformlab/templates/portfolios/composition.py:258)).
Impact: malformed YAML can raise raw `AttributeError` instead of `PortfolioValidationError`.

6. 🟠 **Unhandled non-string `policy_type` can leak raw `TypeError`**
Evidence: `PolicyType(policy_type_str)` only catches `ValueError` ([composition.py:208](/Users/lucas/Workspace/reformlab/src/reformlab/templates/portfolios/composition.py:208)).
Impact: exception taxonomy contract is broken on bad types (e.g., list/int).

7. 🟠 **Resolution metadata is non-idempotent and can accumulate noise**
Evidence: every resolve appends `"Resolved X conflicts..."` unconditionally ([composition.py:546](/Users/lucas/Workspace/reformlab/src/reformlab/templates/portfolios/composition.py:546)).
Impact: repeated validate/load cycles can grow description indefinitely.

8. 🟡 **Portability/security smell: absolute local schema path in serialized YAML**
Evidence: `$schema` uses filesystem-derived path from `__file__` ([composition.py:73](/Users/lucas/Workspace/reformlab/src/reformlab/templates/portfolios/composition.py:73)).
Impact: machine-specific output, reduced reproducibility, local path leakage.

9. 🟠 **Test suite misses key behavior despite story claiming completion**
Evidence: no tests for `PARAMETER_MISMATCH`; no tests enforcing that non-year conflicts under `sum/max` fail ([test_conflicts.py](/Users/lucas/Workspace/reformlab/tests/templates/portfolios/test_conflicts.py)).
Impact: major logic gaps can pass CI unnoticed.

---

## AC Audit

| AC | Status | Notes |
|---|---|---|
| AC1 same policy type conflict | Implemented | Basic detection exists. |
| AC2 non-conflicting validation | Implemented | Covered by tests. |
| AC3 resolution strategy | **Partial** | Strategies do not resolve all conflict classes. |
| AC4 blocking unresolved conflicts | Implemented | `error` path raises. |
| AC5 deterministic behavior | **Partial** | set-based descriptions are non-deterministic text output. |
| AC6 backward compatibility default `error` | Implemented | defaulting is present. |

---

## Git vs Story discrepancy

- Story status says `complete`, but the embedded dev record explicitly says “partially implemented” and lists unresolved items in the same story file ([story file](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/12-2-implement-portfolio-compatibility-validation-and-conflict-resolution.md)).

---

## Evidence Score

- 🔴 Critical: 1 × 3.0 = 3.0  
- 🟠 Important: 7 × 1.0 = 7.0  
- 🟡 Minor: 1 × 0.3 = 0.3  
- 🟢 Clean pass categories: 2 × -0.5 = -1.0 (`Performance`, `PEP8 baseline`)  

**Total Evidence Score: 9.3**  
**Verdict: REJECT**

---

## Auto-fix plan (ready if you approve)

1. Implement real `PARAMETER_MISMATCH` detection and add deterministic conflict sort key `(i, j, conflict_type, parameter_name)`.
2. Make `sum/max` reject non-year conflicts with explicit `PortfolioValidationError`; define explicit semantics for `first_wins/last_wins` across all conflict types.
3. Replace set rendering with sorted tuples in descriptions.
4. Add strict input type guards for `policy` mapping and `policy_type` scalar.
5. Make resolution description append idempotent.
6. Add tests for all above gaps.

]]></file>
<file id="dc422a86" path="[git-diff]" label="VIRTUAL CONTENT"><![CDATA[

<!-- GIT_DIFF_START -->
 .../code-review-synthesis/instructions.xml         |  50 ++
 .../4-implementation/code-review/instructions.xml  | 413 +++++++++--
 .../4-implementation/code-review/workflow.yaml     |  15 +-
 .../4-implementation/create-story/instructions.xml |   6 +-
 .../4-implementation/create-story/workflow.yaml    |  27 +-
 .../4-implementation/dev-story/instructions.xml    |  18 +-
 .../4-implementation/dev-story/workflow.yaml       |   7 +-
 .../4-implementation/retrospective/workflow.yaml   |   9 +-
 bmad-assist.legacy.yaml                            | 108 +++
 bmad-assist.yaml                                   |  79 +-
 scripts/check_ai_usage.py                          | 317 +++++++++
 src/reformlab/templates/__init__.py                |  27 +
 src/reformlab/templates/portfolios/__init__.py     |  41 ++
 src/reformlab/templates/portfolios/composition.py  | 792 +++++++++++++++++++++
 src/reformlab/templates/portfolios/exceptions.py   |  51 ++
 src/reformlab/templates/portfolios/portfolio.py    | 166 +++++
 .../templates/schema/portfolio.schema.json         | 135 ++++
 tests/templates/portfolios/__init__.py             |   1 +
 tests/templates/portfolios/conftest.py             |  55 ++
 tests/templates/portfolios/test_composition.py     | 599 ++++++++++++++++
 tests/templates/portfolios/test_conflicts.py       | 669 +++++++++++++++++
 tests/templates/portfolios/test_portfolio.py       | 418 +++++++++++
 22 files changed, 3900 insertions(+), 103 deletions(-)

diff --git a/scripts/check_ai_usage.py b/scripts/check_ai_usage.py
new file mode 100755
index 0000000..1e18c43
--- /dev/null
+++ b/scripts/check_ai_usage.py
@@ -0,0 +1,317 @@
+#!/usr/bin/env python3
+"""One-shot local usage snapshot for Claude Code, Codex, and Gemini CLI."""
+
+from __future__ import annotations
+
+import argparse
+import json
+import os
+import re
+import subprocess
+import sys
+from datetime import datetime, timezone
+from pathlib import Path
+from typing import Any
+
+
+def run_command(args: list[str]) -> tuple[int, str, str]:
+    try:
+        proc = subprocess.run(args, capture_output=True, text=True, check=False)
+    except FileNotFoundError:
+        return 127, "", "not installed"
+    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
+
+
+def summarize_cli_error(raw: str, fallback: str) -> str:
+    text = (raw or "").strip()
+    if not text:
+        return fallback
+
+    if "Unexpected token '??='" in text:
+        return "Node runtime in this shell is too old for this CLI (`??=` syntax). Use Node 22."
+
+    if "Missing optional dependency @openai/codex-" in text:
+        match = re.search(r"Missing optional dependency (@openai/codex-[^.\s]+)", text)
+        dep = match.group(1) if match else "@openai/codex-<platform>"
+        return f"Codex optional binary mismatch ({dep}). Reinstall under Node 22: npm install -g @openai/codex@latest"
+
+    lines = [line.strip() for line in text.splitlines() if line.strip()]
+    for line in lines:
+        if any(token in line for token in ("Error:", "SyntaxError:", "TypeError:", "ReferenceError:")):
+            return line[:220]
+    return lines[0][:220]
+
+
+def format_epoch(value: Any) -> str:
+    try:
+        if value is None:
+            return "n/a"
+        dt = datetime.fromtimestamp(int(value), tz=timezone.utc).astimezone()
+        return dt.strftime("%Y-%m-%d %H:%M:%S %Z")
+    except Exception:
+        return "n/a"
+
+
+def parse_iso(value: Any) -> datetime | None:
+    if not isinstance(value, str):
+        return None
+    try:
+        if value.endswith("Z"):
+            value = value[:-1] + "+00:00"
+        return datetime.fromisoformat(value)
+    except ValueError:
+        return None
+
+
+def fmt_int(value: Any) -> str:
+    try:
+        return f"{int(value):,}"
+    except Exception:
+        return "n/a"
+
+
+def newest_file(root: Path, pattern: str) -> Path | None:
+    if not root.exists():
+        return None
+    files = list(root.rglob(pattern))
+    if not files:
+        return None
+    return max(files, key=lambda p: p.stat().st_mtime)
+
+
+def newest_files(root: Path, pattern: str, limit: int = 30) -> list[Path]:
+    if not root.exists():
+        return []
+    files = list(root.rglob(pattern))
+    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
+    return files[:limit]
+
+
+def check_claude() -> list[str]:
+    lines = ["[Claude Code]"]
+    code, stdout, stderr = run_command(["claude", "auth", "status", "--json"])
+    if code == 127:
+        lines.append("- CLI: not installed")
+    elif code != 0:
+        err = summarize_cli_error(stderr or stdout, "auth status failed")
+        lines.append(f"- CLI auth check failed: {err}")
+    else:
+        try:
+            data = json.loads(stdout)
+            logged = "yes" if data.get("loggedIn") else "no"
+            subscription = data.get("subscriptionType", "n/a")
+            org_name = data.get("orgName", "n/a")
+            lines.append(f"- Logged in: {logged}")
+            lines.append(f"- Subscription: {subscription}")
+            lines.append(f"- Org: {org_name}")
+        except json.JSONDecodeError:
+            lines.append("- CLI auth output could not be parsed")
+
+    candidate_files = newest_files(Path.home() / ".claude" / "projects", "*.jsonl", limit=40)
+    if not candidate_files:
+        lines.append("- Local usage event: not found")
+    else:
+        latest_usage: dict[str, Any] | None = None
+        latest_model = "n/a"
+        latest_ts: datetime | None = None
+        latest_ts_raw = "n/a"
+        for latest_jsonl in candidate_files:
+            try:
+                with latest_jsonl.open("r", encoding="utf-8", errors="ignore") as handle:
+                    for raw in handle:
+                        raw = raw.strip()
+                        if not raw:
+                            continue
+                        try:
+                            item = json.loads(raw)
+                        except json.JSONDecodeError:
+                            continue
+                        message = item.get("message")
+                        if not isinstance(message, dict):
+                            continue
+                        usage = message.get("usage")
+                        if not isinstance(usage, dict):
+                            continue
+                        ts_raw = item.get("timestamp")
+                        ts = parse_iso(ts_raw)
+                        if latest_ts is None or (ts and ts >= latest_ts):
+                            latest_ts = ts or latest_ts
+                            latest_ts_raw = ts_raw if isinstance(ts_raw, str) else "n/a"
+                            latest_usage = usage
+                            latest_model = str(message.get("model", "n/a"))
+            except OSError:
+                continue
+
+        if not latest_usage:
+            lines.append("- Local usage event: not found")
+        else:
+            in_tokens = (
+                int(latest_usage.get("input_tokens", 0))
+                + int(latest_usage.get("cache_creation_input_tokens", 0))
+                + int(latest_usage.get("cache_read_input_tokens", 0))
+            )
+            out_tokens = int(latest_usage.get("output_tokens", 0))
+            lines.append(f"- Latest local model: {latest_model}")
+            lines.append(f"- Latest local tokens (in/out): {fmt_int(in_tokens)}/{fmt_int(out_tokens)}")
+            lines.append(f"- Latest local event time: {latest_ts_raw}")
+
+    lines.append("- Dashboard: https://console.anthropic.com/settings/usage")
+    return lines
+
+
+def check_codex() -> list[str]:
+    lines = ["[GPT-Codex]"]
+    code, stdout, stderr = run_command(["codex", "login", "status"])
+    if code == 127:
+        lines.append("- CLI: not installed")
+    elif code != 0:
+        err = summarize_cli_error(stderr or stdout, "login status failed")
+        lines.append(f"- CLI auth check failed: {err}")
+    else:
+        status_text = stdout or stderr or "available"
+        lines.append(f"- Login status: {status_text}")
+
+    latest_jsonl = newest_file(Path.home() / ".codex" / "sessions", "*.jsonl")
+    if latest_jsonl is None:
+        lines.append("- Local rate-limit snapshot: not found")
+    else:
+        latest_rate: dict[str, Any] | None = None
+        latest_usage: dict[str, Any] | None = None
+        latest_ts = "n/a"
+        try:
+            with latest_jsonl.open("r", encoding="utf-8", errors="ignore") as handle:
+                for raw in handle:
+                    raw = raw.strip()
+                    if not raw:
+                        continue
+                    try:
+                        item = json.loads(raw)
+                    except json.JSONDecodeError:
+                        continue
+                    if item.get("type") != "event_msg":
+                        continue
+                    payload = item.get("payload")
+                    if not isinstance(payload, dict) or payload.get("type") != "token_count":
+                        continue
+                    rate = payload.get("rate_limits")
+                    info = payload.get("info") or {}
+                    usage = info.get("total_token_usage")
+                    if isinstance(rate, dict):
+                        latest_rate = rate
+                        latest_usage = usage if isinstance(usage, dict) else None
+                        latest_ts = str(item.get("timestamp", "n/a"))
+        except OSError:
+            latest_rate = None
+
+        if not latest_rate:
+            lines.append("- Local rate-limit snapshot: not found")
+        else:
+            primary = latest_rate.get("primary", {})
+            secondary = latest_rate.get("secondary", {})
+            lines.append(
+                f"- Primary window used: {primary.get('used_percent', 'n/a')}% (resets {format_epoch(primary.get('resets_at'))})"
+            )
+            lines.append(
+                f"- Secondary window used: {secondary.get('used_percent', 'n/a')}% (resets {format_epoch(secondary.get('resets_at'))})"
+            )
+            if latest_usage:
+                total = latest_usage.get("total_tokens")
+                lines.append(f"- Latest local total tokens: {fmt_int(total)}")
+            lines.append(f"- Snapshot time: {latest_ts}")
+
+    lines.append("- API dashboard: https://platform.openai.com/usage")
+    lines.append("- ChatGPT plan dashboard: https://chatgpt.com/")
+    return lines
+
+
+def check_gemini() -> list[str]:
+    lines = ["[Gemini CLI]"]
+    code, stdout, stderr = run_command(["gemini", "--version"])
+    if code == 127:
+        lines.append("- CLI: not installed")
+    elif code != 0:
+        err = summarize_cli_error(stderr or stdout, "version check failed")
+        lines.append(f"- CLI check failed: {err}")
+    else:
+        lines.append(f"- CLI version: {stdout}")
+
+    has_env_auth = any(
+        os.getenv(key)
+        for key in ("GEMINI_API_KEY", "GOOGLE_GENAI_USE_VERTEXAI", "GOOGLE_GENAI_USE_GCA")
+    )
+    has_oauth = (Path.home() / ".gemini" / "oauth_creds.json").exists()
+    lines.append(f"- Auth configured: {'yes' if (has_env_auth or has_oauth) else 'no'}")
+
+    prompt_count = 0
+    latest_prompt_ts: datetime | None = None
+    latest_prompt_raw = "n/a"
+    tmp_root = Path.home() / ".gemini" / "tmp"
+    if tmp_root.exists():
+        for log_file in tmp_root.rglob("logs.json"):
+            try:
+                with log_file.open("r", encoding="utf-8", errors="ignore") as handle:
+                    data = json.load(handle)
+            except (OSError, json.JSONDecodeError):
+                continue
+            if not isinstance(data, list):
+                continue
+            for row in data:
+                if not isinstance(row, dict) or row.get("type") != "user":
+                    continue
+                prompt_count += 1
+                ts_raw = row.get("timestamp")
+                ts = parse_iso(ts_raw)
+                if ts and (latest_prompt_ts is None or ts >= latest_prompt_ts):
+                    latest_prompt_ts = ts
+                    latest_prompt_raw = str(ts_raw)
+    lines.append(f"- Local prompts recorded: {prompt_count}")
+    lines.append(f"- Latest local prompt time: {latest_prompt_raw}")
+    lines.append("- Dashboard: https://aistudio.google.com/")
+    return lines
+
+
+def open_dashboards() -> None:
+    urls = [
+        "https://console.anthropic.com/settings/usage",
+        "https://platform.openai.com/usage",
+        "https://chatgpt.com/",
+        "https://aistudio.google.com/",
+    ]
+    opener = None
+    if sys.platform == "darwin":
+        opener = "open"
+    elif sys.platform.startswith("linux"):
+        opener = "xdg-open"
+    if not opener:
+        return
+    for url in urls:
+        subprocess.run([opener, url], check=False, capture_output=True)
+
+
+def main() -> int:
+    parser = argparse.ArgumentParser(description="Check local usage snapshots for Claude/Codex/Gemini.")
+    parser.add_argument(
+        "--open-dashboards",
+        action="store_true",
+        help="Open provider usage dashboards in your browser.",
+    )
+    args = parser.parse_args()
+
+    print("AI usage snapshot (local + dashboard links)")
+    print(f"Generated: {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}")
+    print("Note: provider billing dashboards remain the source of truth.\n")
+
+    for section in (check_claude(), check_codex(), check_gemini()):
+        for line in section:
+            print(line)
+        print()
+
+    if args.open_dashboards:
+        open_dashboards()
+        print("Opened dashboards in browser.")
+
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/src/reformlab/templates/__init__.py b/src/reformlab/templates/__init__.py
index 0f13a49..3104b5c 100644
--- a/src/reformlab/templates/__init__.py
+++ b/src/reformlab/templates/__init__.py
@@ -63,6 +63,20 @@ from reformlab.templates.schema import (
     YearSchedule,
     infer_policy_type,
 )
+from reformlab.templates.portfolios import (
+    Conflict,
+    ConflictType,
+    PolicyConfig,
+    PolicyPortfolio,
+    PortfolioError,
+    PortfolioSerializationError,
+    PortfolioValidationError,
+    ResolutionStrategy,
+    dump_portfolio,
+    load_portfolio,
+    resolve_conflicts,
+    validate_compatibility,
+)
 from reformlab.templates.workflow import (
     WORKFLOW_SCHEMA_VERSION,
     DataSourceConfig,
@@ -86,6 +100,19 @@ from reformlab.templates.workflow import (
 )
 
 __all__ = [
+    # Portfolio types
+    "PolicyConfig",
+    "PolicyPortfolio",
+    "PortfolioError",
+    "PortfolioSerializationError",
+    "PortfolioValidationError",
+    "Conflict",
+    "ConflictType",
+    "ResolutionStrategy",
+    "validate_compatibility",
+    "resolve_conflicts",
+    "dump_portfolio",
+    "load_portfolio",
     # Migration types and functions
     "CompatibilityStatus",
     "MigrationChange",
diff --git a/src/reformlab/templates/portfolios/__init__.py b/src/reformlab/templates/portfolios/__init__.py
new file mode 100644
index 0000000..aeaeb90
--- /dev/null
+++ b/src/reformlab/templates/portfolios/__init__.py
@@ -0,0 +1,41 @@
+"""Policy portfolio composition and serialization.
+
+This module provides the PolicyPortfolio frozen dataclass for composing
+multiple individual policy templates into named, versioned policy packages.
+
+Story 12.1: Define PolicyPortfolio dataclass and composition logic
+Story 12.2: Implement portfolio compatibility validation and conflict resolution
+"""
+
+from __future__ import annotations
+
+from reformlab.templates.portfolios.composition import (
+    Conflict,
+    ConflictType,
+    ResolutionStrategy,
+    dump_portfolio,
+    load_portfolio,
+    resolve_conflicts,
+    validate_compatibility,
+)
+from reformlab.templates.portfolios.exceptions import (
+    PortfolioError,
+    PortfolioSerializationError,
+    PortfolioValidationError,
+)
+from reformlab.templates.portfolios.portfolio import PolicyConfig, PolicyPortfolio
+
+__all__ = [
+    "Conflict",
+    "ConflictType",
+    "PolicyConfig",
+    "PolicyPortfolio",
+    "PortfolioError",
+    "PortfolioValidationError",
+    "PortfolioSerializationError",
+    "ResolutionStrategy",
+    "dump_portfolio",
+    "load_portfolio",
+    "resolve_conflicts",
+    "validate_compatibility",
+]
diff --git a/src/reformlab/templates/portfolios/composition.py b/src/reformlab/templates/portfolios/composition.py
new file mode 100644
index 0000000..a264985
--- /dev/null
+++ b/src/reformlab/templates/portfolios/composition.py
@@ -0,0 +1,792 @@
+"""Portfolio YAML serialization, deserialization, and conflict detection.
+
+Story 12.1: Define PolicyPortfolio dataclass and composition logic
+Story 12.2: Implement portfolio compatibility validation and conflict resolution
+"""
+
+from __future__ import annotations
+
+import logging
+from dataclasses import dataclass, replace
+from enum import Enum
+from pathlib import Path
+from typing import TYPE_CHECKING, Any
+
+import yaml
+
+from reformlab.templates.portfolios.exceptions import (
+    PortfolioSerializationError,
+    PortfolioValidationError,
+)
+from reformlab.templates.portfolios.portfolio import PolicyConfig, PolicyPortfolio
+from reformlab.templates.schema import PolicyType
+
+if TYPE_CHECKING:
+    pass
+
+logger = logging.getLogger(__name__)
+
+
+class ConflictType(Enum):
+    """Types of conflicts that can occur in a portfolio."""
+
+    SAME_POLICY_TYPE = "same_policy_type"
+    OVERLAPPING_CATEGORIES = "overlapping_categories"
+    OVERLAPPING_YEARS = "overlapping_years"
+    PARAMETER_MISMATCH = "parameter_mismatch"
+
+
+class ResolutionStrategy(Enum):
+    """Strategies for resolving portfolio conflicts."""
+
+    ERROR = "error"
+    SUM = "sum"
+    FIRST_WINS = "first_wins"
+    LAST_WINS = "last_wins"
+    MAX = "max"
+
+
+@dataclass(frozen=True)
+class Conflict:
+    """Represents a detected conflict between policies in a portfolio.
+
+    Attributes:
+        conflict_type: Type of conflict detected
+        policy_indices: Indices of conflicting policies in the portfolio
+        parameter_name: Name of the conflicting parameter (e.g., "policy_type", "rate_schedule")
+        conflicting_values: The actual conflicting values
+        description: Human-readable description of the conflict
+    """
+
+    conflict_type: ConflictType
+    policy_indices: tuple[int, ...]
+    parameter_name: str
+    conflicting_values: tuple[Any, ...]
+    description: str
+
+    def __repr__(self) -> str:
+        """Readable representation of the conflict."""
+        return (
+            f"Conflict({self.conflict_type.value}, "
+            f"indices={self.policy_indices}, "
+            f"parameter={self.parameter_name})"
+        )
+
+
+def portfolio_to_dict(portfolio: PolicyPortfolio) -> dict[str, Any]:
+    """Convert PolicyPortfolio to dictionary for YAML serialization.
+
+    Args:
+        portfolio: The portfolio to convert
+
+    Returns:
+        Dictionary with canonical structure for YAML serialization
+    """
+    schema_path = Path(__file__).parent.parent / "schema" / "portfolio.schema.json"
+    policies_data = []
+    for config in portfolio.policies:
+        policy_dict: dict[str, Any] = {
+            "name": config.name,
+            "policy_type": config.policy_type.value,
+            "policy": _policy_parameters_to_dict(config.policy),
+        }
+        policies_data.append(policy_dict)
+
+    return {
+        "$schema": str(schema_path),
+        "name": portfolio.name,
+        "version": portfolio.version,
+        "description": portfolio.description,
+        "policies": policies_data,
+        "resolution_strategy": portfolio.resolution_strategy,
+    }
+
+
+def _policy_parameters_to_dict(policy: Any) -> dict[str, Any]:

[... Git diff truncated due to size - see full diff with git command ...]

]]></file>
</context>
<variables>
<var name="author">BMad</var>
<var name="communication_language">English</var>
<var name="date">2026-03-06</var>
<var name="description">Master synthesizes code review findings and applies fixes to source code</var>
<var name="document_output_language">English</var>
<var name="epic_num">12</var>
<var name="implementation_artifacts">_bmad-output/implementation-artifacts</var>
<var name="installed_path">_bmad/bmm/workflows/4-implementation/code-review-synthesis</var>
<var name="instructions">/Users/lucas/Workspace/bmad-assist/src/bmad_assist/workflows/code-review-synthesis/instructions.xml</var>
<var name="name">code-review-synthesis</var>
<var name="output_folder">_bmad-output</var>
<var name="planning_artifacts">_bmad-output/planning-artifacts</var>
<var name="project_context" file_id="b5c6fe32" load_strategy="EMBEDDED" token_approx="2024">embedded in prompt, file id: b5c6fe32</var>
<var name="project_knowledge">docs</var>
<var name="project_name">ReformLab</var>
<var name="reviewer_count">2</var>
<var name="session_id">50be936b-566c-41a1-bddd-8ed76dfe4888</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_file" file_id="38e1067d">embedded in prompt, file id: 38e1067d</var>
<var name="story_id">12.2</var>
<var name="story_key">12-2-implement-portfolio-compatibility-validation-and-conflict-resolution</var>
<var name="story_num">2</var>
<var name="story_title">implement-portfolio-compatibility-validation-and-conflict-resolution</var>
<var name="template">False</var>
<var name="timestamp">20260306_0100</var>
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
      - Commit message format: fix(component): brief description (synthesis-12.2)
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