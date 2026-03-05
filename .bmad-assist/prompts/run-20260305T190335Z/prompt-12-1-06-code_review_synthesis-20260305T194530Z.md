<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 12 -->
<!-- Story: 1 -->
<!-- Phase: code-review-synthesis -->
<!-- Timestamp: 20260305T194530Z -->
<compiled-workflow>
<mission><![CDATA[

Master Code Review Synthesis: Story 12.1

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
<file id="d908788b" path="_bmad-output/implementation-artifacts/12-1-define-policyportfolio-dataclass-and-composition-logic.md" label="STORY FILE"><![CDATA[

# Story 12.1: Define PolicyPortfolio dataclass and composition logic

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a policy analyst,
I want to compose multiple individual policy templates into a named policy portfolio,
so that I can run simulations with bundled policies applied together and compare comprehensive policy packages.

## Acceptance Criteria

1. **AC1: Frozen dataclass composition** — Given 2+ individual `PolicyConfig` objects, when composed into a `PolicyPortfolio`, then the portfolio is a named, frozen dataclass containing all policies in the order provided.
   
2. **AC2: Policy inspection** — Given a portfolio, when inspected, then it lists all constituent policies with their types and parameter summaries in deterministic order.

3. **AC3: YAML round-trip** — Given a portfolio, when serialized to YAML and reloaded, then the round-trip produces an identical object using dataclass equality, with preserved policy order and default field values.

4. **AC4: Validation error handling** — Given invalid portfolio inputs (fewer than 2 policies, invalid YAML structure, missing required fields), when construction or loading is attempted, then clear `PortfolioError` exceptions are raised with field-level error messages.

5. **AC5: Deterministic serialization** — Given two identical portfolios, when serialized to YAML, then the output is byte-for-byte identical (canonical ordering, stable key order, deterministic formatting).

## Tasks / Subtasks

- [ ] **Task 1: Define PolicyPortfolio frozen dataclass** (AC: #1)
  - [ ] 1.1 Create `src/reformlab/templates/portfolios/` directory structure
  - [ ] 1.2 Create `__init__.py` with module docstring
  - [ ] 1.3 Create `portfolio.py` with `PolicyPortfolio` frozen dataclass
  - [ ] 1.4 Define fields: `name: str`, `policies: tuple[PolicyConfig, ...]`, `version: str`, `description: str`
  - [ ] 1.5 Add `__post_init__` validation (at least 2 policies required)
  - [ ] 1.6 Add property methods: `policy_types`, `policy_count`, `policy_summaries`
  - [ ] 1.7 Add `__repr__` for notebook-friendly display

- [ ] **Task 2: Define PolicyConfig wrapper type** (AC: #1, #2)
  - [ ] 2.1 Analyze existing `PolicyParameters` and `ScenarioTemplate` structures
  - [ ] 2.2 Create `PolicyConfig` as a new frozen dataclass (NOT an alias)
  - [ ] 2.3 Define fields: `policy_type: PolicyType`, `policy: PolicyParameters`, `name: str = ""`
  - [ ] 2.4 Add `get_summary() -> dict[str, Any]` method to extract policy type and parameter summary
  - [ ] 2.5 Add `__post_init__` to validate `policy` matches declared `policy_type`
  - [ ] 2.6 Ensure `PolicyConfig` integrates with existing `BaselineScenario` and `ReformScenario`

- [ ] **Task 3: Implement portfolio inspection methods** (AC: #2)
  - [ ] 3.1 Add `list_policies() -> list[dict[str, Any]]` method
  - [ ] 3.2 Each policy dict includes: name, type, rate_schedule summary, key parameters
  - [ ] 3.3 Add `get_policy_by_type(policy_type: PolicyType) -> PolicyConfig | None`
  - [ ] 3.4 Add `has_policy_type(policy_type: PolicyType) -> bool`
  - [ ] 3.5 Ensure methods work with frozen dataclass (no mutation, return new values)

- [ ] **Task 4: Implement YAML serialization** (AC: #3, #5)
  - [ ] 4.1 Create `composition.py` module in `portfolios/` directory
  - [ ] 4.2 Implement `portfolio_to_dict(portfolio: PolicyPortfolio) -> dict[str, Any]` with deterministic key ordering
  - [ ] 4.3 Implement `dict_to_portfolio(data: dict[str, Any]) -> PolicyPortfolio`
  - [ ] 4.4 Add `dump_portfolio(portfolio: PolicyPortfolio, path: Path) -> None` with canonical YAML formatting
  - [ ] 4.5 Add `load_portfolio(path: Path) -> PolicyPortfolio` with jsonschema validation
  - [ ] 4.6 Create schema file at `src/reformlab/templates/schema/portfolio.schema.json` with `version` field
  - [ ] 4.7 Include `$schema` reference in dumped YAML files for IDE validation support

- [ ] **Task 5: Add validation and error handling** (AC: #1, #2, #3, #4)
  - [ ] 5.1 Validate portfolio has at least 2 policies on construction
  - [ ] 5.2 OUT OF SCOPE: Cross-policy year schedule compatibility validation (deferred to future story)
  - [ ] 5.3 Create `PortfolioError` exception in `exceptions.py` with subclasses for validation vs serialization errors
  - [ ] 5.4 Add clear error messages for invalid portfolios (missing policies, missing required fields)
  - [ ] 5.5 Validate YAML structure on load with field-level error messages using `jsonschema` library
  - [ ] 5.6 Create schema file at `src/reformlab/templates/schema/portfolio.schema.json`

- [ ] **Task 6: Write comprehensive tests** (AC: #1, #2, #3, #4, #5)
  - [ ] 6.1 Create `tests/templates/portfolios/` directory
  - [ ] 6.2 Create `conftest.py` with portfolio fixtures
  - [ ] 6.3 Create `test_portfolio.py` for dataclass tests
  - [ ] 6.4 Create `test_composition.py` for YAML serialization tests
  - [ ] 6.5 Test frozen dataclass immutability
  - [ ] 6.6 Test inspection methods return correct summaries in deterministic order
  - [ ] 6.7 Test YAML round-trip produces identical objects using dataclass equality
  - [ ] 6.8 Test error cases: <2 policies raises PortfolioError, invalid YAML structure, missing required fields
  - [ ] 6.9 Test deterministic serialization: identical portfolios produce byte-identical YAML
  - [ ] 6.10 Run `uv run pytest tests/templates/portfolios/ --cov=src/reformlab/templates/portfolios --cov-report=term-missing` to verify >90% coverage

- [ ] **Task 7: Update module exports** (AC: #1, #2, #3)
  - [ ] 7.1 Update `src/reformlab/templates/portfolios/__init__.py` exports
  - [ ] 7.2 Update `src/reformlab/templates/__init__.py` to export portfolio types
  - [ ] 7.3 Ensure imports follow `from __future__ import annotations` pattern
  - [ ] 7.4 Use `TYPE_CHECKING` guards for type-only imports

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**Frozen dataclass is NON-NEGOTIABLE** — All domain types in ReformLab use `@dataclass(frozen=True)`. This is a core architectural decision [Source: project-context.md#architecture-framework-rules].

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from reformlab.templates.schema import PolicyParameters, PolicyType

@dataclass(frozen=True)
class PolicyConfig:
    """Wrapper for policy parameters with metadata for portfolio composition."""
    policy_type: PolicyType
    policy: PolicyParameters
    name: str = ""
    
    def get_summary(self) -> dict[str, Any]:
        """Extract policy type and key parameter summary."""
        return {
            "name": self.name,
            "type": self.policy_type.value,
            "rate_schedule_years": sorted(self.policy.rate_schedule.keys()),
        }

@dataclass(frozen=True)
class PolicyPortfolio:
    """Named, versioned collection of policy configurations."""
    name: str
    policies: tuple[PolicyConfig, ...]  # tuple for immutability
    version: str = "1.0"
    description: str = ""
```

**Use `tuple` not `list`** — Function parameters and return types that are ordered-and-fixed use `tuple`, not `list` [Source: project-context.md#python-language-rules].

**No ABCs, use Protocols** — Interfaces are `Protocol` + `@runtime_checkable`, not abstract base classes [Source: project-context.md#python-language-rules].

### Existing Schema Analysis

**Current `PolicyParameters` hierarchy** [Source: src/reformlab/templates/schema.py]:
```python
from dataclasses import dataclass, field

@dataclass(frozen=True)
class PolicyParameters:
    """Base class for policy-specific parameters."""
    rate_schedule: dict[int, float]
    exemptions: tuple[dict[str, Any], ...] = ()
    thresholds: tuple[dict[str, Any], ...] = ()
    covered_categories: tuple[str, ...] = ()

@dataclass(frozen=True)
class CarbonTaxParameters(PolicyParameters):
    redistribution_type: str = ""
    income_weights: dict[str, float] = field(default_factory=dict)

# Similar: SubsidyParameters, RebateParameters, FeebateParameters
```

**Current `ScenarioTemplate` structure** [Source: src/reformlab/templates/schema.py:192-213]:
```python
@dataclass(frozen=True)
class ScenarioTemplate:
    """Base scenario template shape."""
    name: str
    year_schedule: YearSchedule
    policy: PolicyParameters
    policy_type: PolicyType | None = None  # Inferred if None
    description: str = ""
    version: str = "1.0"
    schema_ref: str = ""
```

**Design decision: `PolicyConfig` is a new frozen dataclass wrapper** — Option 2 from the list below is required. This allows naming individual policies within a portfolio and extracting summaries without modifying existing scenario templates. Aliases are NOT acceptable.

**Previous design options considered:**
1. An alias for `PolicyParameters`? (REJECTED - insufficient for portfolio needs)
2. A new wrapper containing `PolicyParameters` + metadata? (REQUIRED - provides needed flexibility)
3. A reference to `ScenarioTemplate`? (REJECTED - creates unnecessary coupling)

### YAML Serialization Pattern

**Follow existing loader patterns** [Source: src/reformlab/templates/loader.py]:
- Schema version field: `version: "1.0"`
- `$schema` reference for IDE validation
- `load_portfolio(path: Path) -> PolicyPortfolio`
- `dump_portfolio(portfolio: PolicyPortfolio, path: Path) -> None`
- Clear `ScenarioError` or `PortfolioError` on validation failures

**Deterministic serialization requirements** [Source: project-context.md#critical-dont-miss-rules]:
- Use `jsonschema` library for YAML validation on load (consistent with project stack)
- Sort dictionary keys alphabetically in output
- Use canonical YAML formatting (consistent indentation, no trailing spaces)
- Preserve policy order from tuple (do not reorder)
- Round-trip equality must include order preservation

**Example YAML structure** (proposed):
```yaml
$schema: "../schema/portfolio.schema.json"
version: "1.0"

name: "Green Transition 2030"
description: >
  Comprehensive climate policy package combining carbon pricing,
  vehicle incentives, and home renovation subsidies.

policies:
  - name: "Carbon Tax Component"
    policy_type: carbon_tax
    policy:
      rate_schedule:
        2026: 44.60
        2027: 50.00
        # ... (full policy parameters)
      redistribution_type: lump_sum
      
  - name: "EV Bonus"
    policy_type: subsidy
    policy:
      rate_schedule:
        2026: 5000.0
        2027: 5000.0
        # ... (full policy parameters)
      eligible_categories:
        - electric_vehicle
```

### Testing Standards

**Mirror source structure** [Source: project-context.md#testing-rules]:
```
tests/templates/portfolios/
├── __init__.py
├── conftest.py          ← fixtures: sample portfolios, policy configs
├── test_portfolio.py    ← dataclass construction, inspection methods
└── test_composition.py  ← YAML serialization, round-trip, validation
```

**Class-based test grouping** [Source: project-context.md]:
```python
class TestPolicyPortfolioConstruction:
    """Tests for portfolio creation and validation (AC #1)."""
    
class TestPolicyPortfolioInspection:
    """Tests for policy listing and summaries (AC #2)."""
    
class TestPolicyPortfolioYAML:
    """Tests for YAML serialization round-trip (AC #3)."""
```

**Direct assertions, no helpers** [Source: project-context.md]:
```python
def test_portfolio_requires_two_policies(self) -> None:
    """Portfolio with <2 policies raises clear error."""
    with pytest.raises(PortfolioError, match="at least 2 policies"):
        PolicyPortfolio(
            name="invalid",
            policies=(policy_1,),  # Only 1 policy
        )
```

### File Structure

**New directory** [Source: architecture.md#phase-2-architecture-extensions]:
```
src/reformlab/templates/
├── portfolios/
│   ├── __init__.py
│   ├── portfolio.py     ← PolicyPortfolio frozen dataclass
│   ├── composition.py   ← YAML serialization, validation
│   └── exceptions.py    ← PortfolioError hierarchy
```

**Exception taxonomy** — Create exception hierarchy consistent with project patterns:
```python
class PortfolioError(Exception):
    """Base exception for portfolio-related errors."""
    pass

class PortfolioValidationError(PortfolioError):
    """Raised when portfolio structure or policy configuration is invalid."""
    pass

class PortfolioSerializationError(PortfolioError):
    """Raised when YAML serialization or deserialization fails."""
    pass
```

**Update exports** in:
- `src/reformlab/templates/portfolios/__init__.py`
- `src/reformlab/templates/__init__.py` (add portfolio types to `__all__`)

### Integration with Existing Code

**Scope boundaries** — This story focuses on data structure and serialization ONLY:
- ✅ IN SCOPE: PolicyPortfolio frozen dataclass, PolicyConfig wrapper, YAML serialization, basic validation
- ❌ OUT OF SCOPE: Cross-policy year schedule compatibility checks (future story)
- ❌ OUT OF SCOPE: Orchestrator integration (Story 12.3)
- ❌ OUT OF SCOPE: Conflict resolution or policy compatibility logic

**Scenario Registry compatibility** — Portfolios will eventually be stored in the scenario registry alongside individual scenarios [Source: architecture.md#extension-policy-portfolio-layer]. Design `PolicyPortfolio` to be registry-friendly:
- Include `version` field for versioning
- Include `name` field for registry lookup
- Follow same immutability patterns as `BaselineScenario` and `ReformScenario`

**Orchestrator integration** — The orchestrator will receive a portfolio instead of a single policy [Source: architecture.md#extension-policy-portfolio-layer]. This is Story 12.3, not this story. Design `PolicyPortfolio` to expose the policies list in a way that's easy for the orchestrator to iterate.

### Project Structure Notes

- **Alignment with unified project structure:** New `portfolios/` subdirectory follows existing template subsystem pattern (similar to `carbon_tax/`, `subsidy/`, etc.)
- **Naming convention:** `portfolio.py` and `composition.py` follow `snake_case.py` convention
- **Module docstrings:** Every module needs a docstring explaining its role [Source: project-context.md#code-quality-style-rules]

### Critical Don't-Miss Rules

1. **Every file starts with `from __future__ import annotations`** — no exceptions [Source: project-context.md#python-language-rules]
2. **Use `if TYPE_CHECKING:` guards** for imports only needed for annotations [Source: project-context.md#python-language-rules]
3. **All domain types are frozen** — never add a mutable dataclass [Source: project-context.md#critical-dont-miss-rules]
4. **Determinism is non-negotiable** — portfolio construction and serialization must be deterministic [Source: project-context.md#critical-dont-miss-rules]
5. **No wildcard imports** — always import specific names [Source: project-context.md#code-quality-style-rules]

### References

**Architecture:**
- [Source: architecture.md#phase-2-architecture-extensions] — Policy Portfolio Layer design
- [Source: architecture.md#extension-policy-portfolio-layer] — Portfolio composition and orchestrator integration

**PRD:**
- [Source: prd.md#phase-2-policy-portfolios] — FR43-FR46 functional requirements
- [Source: prd.md#product-scope-post-mvp-features] — Phase 2 feature table

**Existing Code:**
- [Source: src/reformlab/templates/schema.py] — Existing `PolicyParameters`, `ScenarioTemplate` structures
- [Source: src/reformlab/templates/loader.py] — YAML serialization patterns
- [Source: src/reformlab/templates/registry.py] — Registry patterns for versioned artifacts

**Testing:**
- [Source: tests/templates/test_loader.py] — Example test patterns for YAML serialization
- [Source: tests/templates/test_registry.py] — Example test patterns for versioned artifacts

**Project Context:**
- [Source: project-context.md#architecture-framework-rules] — Frozen dataclasses, Protocols, step pipeline
- [Source: project-context.md#testing-rules] — Test structure, fixtures, assertions
- [Source: project-context.md#code-quality-style-rules] — ruff, mypy, naming conventions

## Dev Agent Record

### Agent Model Used

(To be filled during implementation)

### Debug Log References

(To be filled during implementation)

### Completion Notes List

(To be filled during implementation)

### File List

(To be filled during implementation)


]]></file>
<file id="2109904e" path="bmad-assist.legacy.yaml" label="CONFIG FILE"><![CDATA[

# bmad-assist configuration for ReformLab
# Strategy: Opus creates/devs, Codex + Gemini validate/review, mixed synthesis

project_name: ReformLab
user_name: Lucas
communication_language: English
document_output_language: English
user_skill_level: intermediate

timeouts:
  default: 600
  retries: 2
  create_story: 900
  dev_story: 3600

providers:
  master:
    provider: claude-subprocess
    model: opus

  helper:
    provider: claude-subprocess
    model: haiku

# Per-phase model assignment
# Opus creates/devs, Codex+Gemini validate/review, Opus/Gemini synthesis split
phase_models:
  # --- Creative phases: Opus ---
  create_story:
    provider: claude-subprocess
    model: opus
  dev_story:
    provider: claude-subprocess
    model: opus

  # --- Validation phases: Codex + Gemini (two reviewers for synthesis) ---
  validate_story:
    - provider: codex
      model: gpt-5.1-codex-max
    - provider: gemini
      model: gemini-2.5-flash
  validate_story_synthesis:
    provider: claude-subprocess
    model: opus

  # --- Review phases: Codex + Gemini (two reviewers for synthesis) ---
  code_review:
    - provider: codex
      model: gpt-5.3-codex
      reasoning_effort: high
    - provider: gemini
      model: gemini-2.5-flash
  code_review_synthesis:
    provider: claude-subprocess
    model: opus

  # --- Retrospective: Sonnet ---
  retrospective:
    provider: claude-subprocess
    model: sonnet

# Compiler configuration — balanced budgets
# Restored closer to defaults after synthesis starvation warnings (2026-03-03).
# Architecture doc alone is ~14k tokens; 8k strategic budget was truncating it to 47%.
compiler:
  source_context:
    budgets:
      create_story: 60000 # restored — needs full context from docs
      validate_story: 15000 # restored default
      validate_story_synthesis: 15000 # was missing (fell back to default)
      dev_story: 15000 # unchanged — dev needs code context most
      code_review: 30000 # restored default
      code_review_synthesis: 30000 # was missing — synthesis starved at old default
      default: 30000 # restored default

  strategic_context:
    budget: 15000 # restored — architecture alone is ~14k tokens
    tree_budget: 0
    defaults:
      include: [project-tree, project-context, architecture]
      main_only: true
    create_story:
      include: [project-tree, project-context, architecture, prd]
    dev_story:
      include: [project-tree, project-context, architecture] # removed prd — dev doesn't need product spec
    code_review:
      include: [project-tree, project-context, architecture] # removed prd — reviewer needs code, not product spec

# Loop: standard cycle, no TEA
loop:
  story:
    - create_story
    - validate_story
    - validate_story_synthesis
    - dev_story
    - code_review
    - code_review_synthesis
  epic_teardown:
    - retrospective

testarch:
  enabled: false

deep_verify:
  enabled: false

security_agent:
  enabled: false


]]></file>
<file id="0b7346ae" path="bmad-assist.yaml" label="CONFIG FILE"><![CDATA[

# bmad-assist configuration for ReformLab
# Strategy: GLM-5 creates/devs/synth/retro, Gemini+GLM-5+Codex validate/review

project_name: ReformLab
user_name: Lucas
communication_language: English
document_output_language: English
user_skill_level: intermediate

timeouts:
  default: 600
  retries: 2
  create_story: 900
  dev_story: 3600

providers:
  master:
    provider: opencode
    model: zai-coding-plan/glm-5

  helper:
    provider: claude-subprocess
    model: sonnet

# Per-phase model assignment
# GLM-5 creates/devs/synth/retro, Gemini+GLM-5+Codex validate/review
phase_models:
  # --- Creative phases: GLM-5 ---
  create_story:
    provider: opencode
    model: zai-coding-plan/glm-5
  dev_story:
    provider: opencode
    model: zai-coding-plan/glm-5

  # --- Validation phases: Gemini + GLM-5 + Codex (three reviewers for synthesis) ---
  validate_story:
    - provider: gemini
      model: gemini-2.5-flash
    - provider: codex
      model: gpt-5.3-codex
      reasoning_effort: high
  validate_story_synthesis:
    provider: opencode
    model: zai-coding-plan/glm-5

  # --- Review phases: Gemini + GLM-5 + Codex (three reviewers for synthesis) ---
  code_review:
    - provider: gemini
      model: gemini-2.5-flash
    - provider: codex
      model: gpt-5.3-codex
      reasoning_effort: high
  code_review_synthesis:
    provider: opencode
    model: zai-coding-plan/glm-5

  # --- Retrospective: GLM-5 ---
  retrospective:
    provider: opencode
    model: zai-coding-plan/glm-5

# Compiler configuration — balanced budgets
# Restored closer to defaults after synthesis starvation warnings (2026-03-03).
# Architecture doc alone is ~14k tokens; 8k strategic budget was truncating it to 47%.
compiler:
  source_context:
    budgets:
      create_story: 60000
      validate_story: 15000
      validate_story_synthesis: 15000
      dev_story: 15000
      code_review: 30000
      code_review_synthesis: 30000
      default: 30000

  strategic_context:
    budget: 15000
    tree_budget: 0
    defaults:
      include: [project-tree, project-context, architecture]
      main_only: true
    create_story:
      include: [project-tree, project-context, architecture, prd]
    dev_story:
      include: [project-tree, project-context, architecture]
    code_review:
      include: [project-tree, project-context, architecture]

# Loop: standard cycle with synthesis, no TEA
loop:
  story:
    - create_story
    - validate_story
    - validate_story_synthesis
    - dev_story
    - code_review
    - code_review_synthesis
  epic_teardown:
    - retrospective

testarch:
  enabled: false

deep_verify:
  enabled: false

security_agent:
  enabled: false


]]></file>
<file id="ed28383a" path="scripts/check_ai_usage.py" label="SOURCE CODE"><![CDATA[

#!/usr/bin/env python3
"""One-shot local usage snapshot for Claude Code, Codex, and Gemini CLI."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def run_command(args: list[str]) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(args, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return 127, "", "not installed"
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def summarize_cli_error(raw: str, fallback: str) -> str:
    text = (raw or "").strip()
    if not text:
        return fallback

    if "Unexpected token '??='" in text:
        return "Node runtime in this shell is too old for this CLI (`??=` syntax). Use Node 22."

    if "Missing optional dependency @openai/codex-" in text:
        match = re.search(r"Missing optional dependency (@openai/codex-[^.\s]+)", text)
        dep = match.group(1) if match else "@openai/codex-<platform>"
        return f"Codex optional binary mismatch ({dep}). Reinstall under Node 22: npm install -g @openai/codex@latest"

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        if any(token in line for token in ("Error:", "SyntaxError:", "TypeError:", "ReferenceError:")):
            return line[:220]
    return lines[0][:220]


def format_epoch(value: Any) -> str:
    try:
        if value is None:
            return "n/a"
        dt = datetime.fromtimestamp(int(value), tz=timezone.utc).astimezone()
        return dt.strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception:
        return "n/a"


def parse_iso(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def fmt_int(value: Any) -> str:
    try:
        return f"{int(value):,}"
    except Exception:
        return "n/a"


def newest_file(root: Path, pattern: str) -> Path | None:
    if not root.exists():
        return None
    files = list(root.rglob(pattern))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def newest_files(root: Path, pattern: str, limit: int = 30) -> list[Path]:
    if not root.exists():
        return []
    files = list(root.rglob(pattern))
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[:limit]


def check_claude() -> list[str]:
    lines = ["[Claude Code]"]
    code, stdout, stderr = run_command(["claude", "auth", "status", "--json"])
    if code == 127:
        lines.append("- CLI: not installed")
    elif code != 0:
        err = summarize_cli_error(stderr or stdout, "auth status failed")
        lines.append(f"- CLI auth check failed: {err}")
    else:
        try:
            data = json.loads(stdout)
            logged = "yes" if data.get("loggedIn") else "no"
            subscription = data.get("subscriptionType", "n/a")
            org_name = data.get("orgName", "n/a")
            lines.append(f"- Logged in: {logged}")
            lines.append(f"- Subscription: {subscription}")
            lines.append(f"- Org: {org_name}")
        except json.JSONDecodeError:
            lines.append("- CLI auth output could not be parsed")

    candidate_files = newest_files(Path.home() / ".claude" / "projects", "*.jsonl", limit=40)
    if not candidate_files:
        lines.append("- Local usage event: not found")
    else:
        latest_usage: dict[str, Any] | None = None
        latest_model = "n/a"
        latest_ts: datetime | None = None
        latest_ts_raw = "n/a"
        for latest_jsonl in candidate_files:
            try:
                with latest_jsonl.open("r", encoding="utf-8", errors="ignore") as handle:
                    for raw in handle:
                        raw = raw.strip()
                        if not raw:
                            continue
                        try:
                            item = json.loads(raw)
                        except json.JSONDecodeError:
                            continue
                        message = item.get("message")
                        if not isinstance(message, dict):
                            continue
                        usage = message.get("usage")
                        if not isinstance(usage, dict):
                            continue
                        ts_raw = item.get("timestamp")
                        ts = parse_iso(ts_raw)
                        if latest_ts is None or (ts and ts >= latest_ts):
                            latest_ts = ts or latest_ts
                            latest_ts_raw = ts_raw if isinstance(ts_raw, str) else "n/a"
                            latest_usage = usage
                            latest_model = str(message.get("model", "n/a"))
            except OSError:
                continue

        if not latest_usage:
            lines.append("- Local usage event: not found")
        else:
            in_tokens = (
                int(latest_usage.get("input_tokens", 0))
                + int(latest_usage.get("cache_creation_input_tokens", 0))
                + int(latest_usage.get("cache_read_input_tokens", 0))
            )
            out_tokens = int(latest_usage.get("output_tokens", 0))
            lines.append(f"- Latest local model: {latest_model}")
            lines.append(f"- Latest local tokens (in/out): {fmt_int(in_tokens)}/{fmt_int(out_tokens)}")
            lines.append(f"- Latest local event time: {latest_ts_raw}")

    lines.append("- Dashboard: https://console.anthropic.com/settings/usage")
    return lines


def check_codex() -> list[str]:
    lines = ["[GPT-Codex]"]
    code, stdout, stderr = run_command(["codex", "login", "status"])
    if code == 127:
        lines.append("- CLI: not installed")
    elif code != 0:
        err = summarize_cli_error(stderr or stdout, "login status failed")
        lines.append(f"- CLI auth check failed: {err}")
    else:
        status_text = stdout or stderr or "available"
        lines.append(f"- Login status: {status_text}")

    latest_jsonl = newest_file(Path.home() / ".codex" / "sessions", "*.jsonl")
    if latest_jsonl is None:
        lines.append("- Local rate-limit snapshot: not found")
    else:
        latest_rate: dict[str, Any] | None = None
        latest_usage: dict[str, Any] | None = None
        latest_ts = "n/a"
        try:
            with latest_jsonl.open("r", encoding="utf-8", errors="ignore") as handle:
                for raw in handle:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        item = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    if item.get("type") != "event_msg":
                        continue
                    payload = item.get("payload")
                    if not isinstance(payload, dict) or payload.get("type") != "token_count":
                        continue
                    rate = payload.get("rate_limits")
                    info = payload.get("info") or {}
                    usage = info.get("total_token_usage")
                    if isinstance(rate, dict):
                        latest_rate = rate
                        latest_usage = usage if isinstance(usage, dict) else None
                        latest_ts = str(item.get("timestamp", "n/a"))
        except OSError:
            latest_rate = None

        if not latest_rate:
            lines.append("- Local rate-limit snapshot: not found")
        else:
            primary = latest_rate.get("primary", {})
            secondary = latest_rate.get("secondary", {})
            lines.append(
                f"- Primary window used: {primary.get('used_percent', 'n/a')}% (resets {format_epoch(primary.get('resets_at'))})"
            )
            lines.append(
                f"- Secondary window used: {secondary.get('used_percent', 'n/a')}% (resets {format_epoch(secondary.get('resets_at'))})"
            )
            if latest_usage:
                total = latest_usage.get("total_tokens")
                lines.append(f"- Latest local total tokens: {fmt_int(total)}")
            lines.append(f"- Snapshot time: {latest_ts}")

    lines.append("- API dashboard: https://platform.openai.com/usage")
    lines.append("- ChatGPT plan dashboard: https://chatgpt.com/")
    return lines


def check_gemini() -> list[str]:
    lines = ["[Gemini CLI]"]
    code, stdout, stderr = run_command(["gemini", "--version"])
    if code == 127:
        lines.append("- CLI: not installed")
    elif code != 0:
        err = summarize_cli_error(stderr or stdout, "version check failed")
        lines.append(f"- CLI check failed: {err}")
    else:
        lines.append(f"- CLI version: {stdout}")

    has_env_auth = any(
        os.getenv(key)
        for key in ("GEMINI_API_KEY", "GOOGLE_GENAI_USE_VERTEXAI", "GOOGLE_GENAI_USE_GCA")
    )
    has_oauth = (Path.home() / ".gemini" / "oauth_creds.json").exists()
    lines.append(f"- Auth configured: {'yes' if (has_env_auth or has_oauth) else 'no'}")

    prompt_count = 0
    latest_prompt_ts: datetime | None = None
    latest_prompt_raw = "n/a"
    tmp_root = Path.home() / ".gemini" / "tmp"
    if tmp_root.exists():
        for log_file in tmp_root.rglob("logs.json"):
            try:
                with log_file.open("r", encoding="utf-8", errors="ignore") as handle:
                    data = json.load(handle)
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(data, list):
                continue
            for row in data:
                if not isinstance(row, dict) or row.get("type") != "user":
                    continue
                prompt_count += 1
                ts_raw = row.get("timestamp")
                ts = parse_iso(ts_raw)
                if ts and (latest_prompt_ts is None or ts >= latest_prompt_ts):
                    latest_prompt_ts = ts
                    latest_prompt_raw = str(ts_raw)
    lines.append(f"- Local prompts recorded: {prompt_count}")
    lines.append(f"- Latest local prompt time: {latest_prompt_raw}")
    lines.append("- Dashboard: https://aistudio.google.com/")
    return lines


def open_dashboards() -> None:
    urls = [
        "https://console.anthropic.com/settings/usage",
        "https://platform.openai.com/usage",
        "https://chatgpt.com/",
        "https://aistudio.google.com/",
    ]
    opener = None
    if sys.platform == "darwin":
        opener = "open"
    elif sys.platform.startswith("linux"):
        opener = "xdg-open"
    if not opener:
        return
    for url in urls:
        subprocess.run([opener, url], check=False, capture_output=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check local usage snapshots for Claude/Codex/Gemini.")
    parser.add_argument(
        "--open-dashboards",
        action="store_true",
        help="Open provider usage dashboards in your browser.",
    )
    args = parser.parse_args()

    print("AI usage snapshot (local + dashboard links)")
    print(f"Generated: {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print("Note: provider billing dashboards remain the source of truth.\n")

    for section in (check_claude(), check_codex(), check_gemini()):
        for line in section:
            print(line)
        print()

    if args.open_dashboards:
        open_dashboards()
        print("Opened dashboards in browser.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


]]></file>
<file id="1d910d88" path="[Validator A]" label="VALIDATION OUTPUT"><![CDATA[

**Story 12.1 Review Verdict: REJECT**

**AC status**
- AC1: Implemented (with immutability hole).
- AC2: Partial.
- AC3: Partial.
- AC4: Partial.
- AC5: Claimed, but weakly validated.

**Findings (8)**

1. 🔴 **CRITICAL: “Frozen” portfolio can be mutated externally (immutability breach).**  
Evidence: [portfolio.py:105](/Users/lucas/Workspace/reformlab/src/reformlab/templates/portfolios/portfolio.py:105), [portfolio.py:116](/Users/lucas/Workspace/reformlab/src/reformlab/templates/portfolios/portfolio.py:116).  
`list_policies()` returns direct references to mutable `rate_schedule` dicts. Runtime repro changed returned dict and mutated internal policy state (`2026` became `999.0`). This violates project immutability rules and can break determinism.

2. 🟠 **HIGH: Carbon tax fields are silently dropped on load (`redistribution_type` / `income_weights`).**  
Evidence: [composition.py:213](/Users/lucas/Workspace/reformlab/src/reformlab/templates/portfolios/composition.py:213), [composition.py:216](/Users/lucas/Workspace/reformlab/src/reformlab/templates/portfolios/composition.py:216), [test_composition.py:82](/Users/lucas/Workspace/reformlab/tests/templates/portfolios/test_composition.py:82).  
Loader only reads `policy.redistribution.{type,income_weights}` but test input uses `policy.redistribution_type`. Value is accepted by schema yet dropped to default `""` (confirmed by runtime repro). Data-loss bug.

3. 🟠 **HIGH: Rebate `redistribution` block is ignored (inconsistent with canonical loader).**  
Evidence: [composition.py:284](/Users/lucas/Workspace/reformlab/src/reformlab/templates/portfolios/composition.py:284), [loader.py:435](/Users/lucas/Workspace/reformlab/src/reformlab/templates/loader.py:435).  
Scenario loader supports rebate `redistribution` fallback; portfolio loader does not. Same semantic input yields different results across loaders and silently strips rebate metadata.

4. 🟠 **HIGH: Validation schema is too permissive; invalid structures pass instead of failing loudly.**  
Evidence: [portfolio.schema.json:6](/Users/lucas/Workspace/reformlab/src/reformlab/templates/schema/portfolio.schema.json:6), [portfolio.schema.json:34](/Users/lucas/Workspace/reformlab/src/reformlab/templates/schema/portfolio.schema.json:34), [composition.py:186](/Users/lucas/Workspace/reformlab/src/reformlab/templates/portfolios/composition.py:186).  
No `additionalProperties: false` at root/policy levels, and policy object has no required parameter fields. Typos/unknown keys are accepted and may be silently ignored; this violates “data contracts fail loudly” and weakens AC4.

5. 🟠 **HIGH: Package integration gap — portfolio types not exported from `reformlab.templates`.**  
Evidence: [story 12.1 task 7.2](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/12-1-define-policyportfolio-dataclass-and-composition-logic.md:82), [templates/__init__.py:88](/Users/lucas/Workspace/reformlab/src/reformlab/templates/__init__.py:88).  
Story requires export update, but top-level package still omits `PolicyConfig`/`PolicyPortfolio`/portfolio errors. Integration is incomplete.

6. 🟠 **HIGH: AC5 test is a lying test (does not validate key ordering).**  
Evidence: [test_composition.py:223](/Users/lucas/Workspace/reformlab/tests/templates/portfolios/test_composition.py:223), [test_composition.py:249](/Users/lucas/Workspace/reformlab/tests/templates/portfolios/test_composition.py:249).  
`test_deterministic_key_ordering` only checks substring presence (`"name:"`, `"version:"`), not canonical order. The test would pass even if order is wrong.

7. 🟠 **HIGH: New tests likely fail lint gate (ruff E/F).**  
Evidence: [test_composition.py:14](/Users/lucas/Workspace/reformlab/tests/templates/portfolios/test_composition.py:14), [test_composition.py:247](/Users/lucas/Workspace/reformlab/tests/templates/portfolios/test_composition.py:247).  
Unused `yaml` import and unused local variable `lines`. This is a CI risk under configured `E,F,I,W`. (I couldn’t run `ruff` here: `ruff` missing; `uv run` blocked by sandbox cache permissions.)

8. 🟡 **MEDIUM: Story traceability is inconsistent with implementation state.**  
Evidence: [story status](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/12-1-define-policyportfolio-dataclass-and-composition-logic.md:3), [Dev Agent Record placeholders](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/12-1-define-policyportfolio-dataclass-and-composition-logic.md:337).  
Story remains `ready-for-dev`, all tasks unchecked, and Dev Agent Record/File List empty despite substantial code changes. Review/audit trail is incomplete.

**Evidence score**
- Critical: 1 (`+3`)
- Important/High: 6 (`+6`)
- Minor: 1 (`+0.3`)
- Clean passes: 0 (`0`)
- **Total: 9.3 → REJECT**

If you want, I can provide a concrete patch plan and exact fixes for these 8 issues (including loader parity, strict schema, immutability-safe inspection output, and test hardening).

]]></file>
<file id="557aedd2" path="[Validator B]" label="VALIDATION OUTPUT"><![CDATA[

**🔥 ADVERSARIAL CODE REVIEW COMPLETE, Lucas!**

**Story:** /Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/12-1-define-policyportfolio-dataclass-and-composition-logic.md

---

## 📊 Review Summary

| Category | Issues Found |
|----------|--------------|
| Git vs Story Discrepancies | 1 |
| AC Implementation Gaps | 0 |
| Task Completion Lies | 1 |
| SOLID Violations | 1 |
| Hidden Bugs | 2 |
| Performance Footguns | 0 |
| Security Vulnerabilities | 0 |
| **Total Issues** | **10** |

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🟠 MINOR | Undocumented File Changes: The `git diff` includes a new file `scripts/check_ai_usage.py` and changes to `bmad-assist.legacy.yaml`, `bmad-assist.yaml` that are not listed or referenced in the story file `12-1-define-policyportfolio-dataclass-and-composition-logic.md`. | Git vs Story File List comparison | +0.3 |
| 🔴 CRITICAL | Tasks Marked Incomplete But Implemented: All tasks in the story file `12-1-define-policyportfolio-dataclass-and-composition-logic.md` are marked as `[ ]` (unchecked), but the provided code clearly implements them. | Story File Task List | +3 |
| 🔴 CRITICAL | `infer_policy_type` Not Available at Runtime: In `src/reformlab/templates/portfolios/portfolio.py`, `infer_policy_type` is imported inside `if TYPE_CHECKING:` but called at runtime in `PolicyConfig.__post_init__`, leading to `NameError`. | `src/reformlab/templates/portfolios/portfolio.py` | +3 |
| 🔴 CRITICAL | `PolicyType` Not Available at Runtime: In `src/reformlab/templates/portfolios/portfolio.py`, `PolicyType` is imported inside `if TYPE_CHECKING:` but used at runtime (e.g., `config.policy_type.value`, `PolicyType.CARBON_TAX`). This will cause a `NameError`. | `src/reformlab/templates/portfolios/portfolio.py` | +3 |
| 🎭 CRITICAL | Lying Test: `TestPolicyConfigConstruction.test_policy_config_type_validation_mismatch` is lying because the `PolicyConfig` constructor will fail with a `NameError` at runtime before the specific `PortfolioValidationError` can be asserted. | `tests/templates/portfolios/test_portfolio.py` | +3 |
| 🎭 CRITICAL | Lying Test: Most tests in `test_portfolio.py` and `test_composition.py` are potentially lying. The fundamental runtime `NameError` in `PolicyConfig` (Findings 3 and 4) means that any test that instantiates `PolicyConfig` or `PolicyPortfolio` will encounter this bug, preventing correct verification of intended behavior. | `tests/templates/portfolios/test_portfolio.py`, `tests/templates/portfolios/test_composition.py` | +3 |
| 🟠 IMPORTANT | Manual serialization logic in `composition.py`: `_policy_params_to_dict` and `_dict_to_policy_params` use `if/elif isinstance` to handle different policy types. This violates the Open/Closed Principle (SOLID) and creates a maintenance burden. | `src/reformlab/templates/portfolios/composition.py` | +1 |
| 🟡 MINOR | Redundant `_pivot_point_set` checks in `_policy_params_to_dict`: The conditional `if params._pivot_point_set or params.pivot_point != 0.0:` for FeebateParameters is confusing and potentially redundant depending on desired serialization logic. | `src/reformlab/templates/portfolios/composition.py` | +0.3 |
| 🟡 MINOR | Weak Assertion in `test_deterministic_key_ordering`: The test only asserts the presence of certain top-level keys rather than strictly verifying the canonical (alphabetical) order of *all* keys, especially in nested dictionaries. | `tests/templates/portfolios/test_composition.py` | +0.3 |
| 🟡 MINOR | Redundant test code in `TestPortfolioErrorHandling`: Multiple tests in `TestPortfolioErrorHandling` follow a very similar structure and could be refactored using `pytest.mark.parametrize` for better readability and maintainability. | `tests/templates/portfolios/test_composition.py` | +0.3 |
| 🟢 CLEAN PASS | 3 |

### Evidence Score: 15.7

| Score | Verdict |
|-------|---------|
| **15.7** | **REJECT** |

---

## 🏛️ Architectural Sins

- **[6/10] Open/Closed Principle:** The `_policy_params_to_dict` and `_dict_to_policy_params` functions in `src/reformlab/templates/portfolios/composition.py` contain manual `if/elif isinstance` and `if policy_type == PolicyType.X` logic to handle different policy parameter types.
  - 📍 `src/reformlab/templates/portfolios/composition.py:100` (and `_dict_to_policy_params`)
  - 💡 Fix: Implement a more generic, pluggable serialization/deserialization mechanism that doesn't require modifying these central functions every time a new policy type is introduced. This could involve a registry pattern or leveraging type-aware serialization libraries.

✅ No significant abstraction level issues detected.

---

## 🐍 Pythonic Crimes & Readability

- **Code Quality:** Redundant `_pivot_point_set` checks in `_policy_params_to_dict`.
  - 📍 `src/reformlab/templates/portfolios/composition.py:171`
- **Code Quality:** Redundant test code in `TestPortfolioErrorHandling`.
  - 📍 `tests/templates/portfolios/test_composition.py:488` (starting point of the test class)

---

## ⚡ Performance & Scalability

✅ No significant performance issues detected.

---

## 🐛 Correctness & Safety

- **🐛 Bug:** `infer_policy_type` Not Available at Runtime
  - 📍 `src/reformlab/templates/portfolios/portfolio.py:33`
  - 🔄 Reproduction: Attempt to instantiate `PolicyConfig` at runtime.
- **🐛 Bug:** `PolicyType` Not Available at Runtime
  - 📍 `src/reformlab/templates/portfolios/portfolio.py:10`
  - 🔄 Reproduction: Attempt to use `PolicyType` or instantiate `PolicyConfig` at runtime.
- **🎭 Lying Test:** `test_policy_config_type_validation_mismatch`
  - 📍 `tests/templates/portfolios/test_portfolio.py:65`
  - 🤥 Why it lies: This test aims to verify `PolicyConfig`'s type validation. However, due to the critical runtime `NameError` caused by `infer_policy_type` and `PolicyType` being imported under `if TYPE_CHECKING:`, the `PolicyConfig` constructor will fail before the specific `PortfolioValidationError` can be asserted, making the test potentially pass with an unexpected error or fail for the wrong reasons.
- **🎭 Lying Test:** Most tests in `test_portfolio.py` and `test_composition.py`
  - 📍 `tests/templates/portfolios/test_portfolio.py:76` (and similar in `test_composition.py`)
  - 🤥 Why it lies: The fundamental runtime `NameError` in `PolicyConfig` due to `infer_policy_type` and `PolicyType` not being available at runtime means that any test that instantiates `PolicyConfig` or `PolicyPortfolio` will encounter this bug. This includes nearly all tests in both `test_portfolio.py` and `test_composition.py`, making them unable to correctly verify the intended behavior until the underlying import issue is resolved.

✅ No significant security vulnerabilities detected.

---

## 🔧 Maintainability Issues

- **💣 Tech Debt:** Manual serialization/deserialization logic.
  - 📍 `src/reformlab/templates/portfolios/composition.py:100`
  - 💥 Explosion radius: High, affects extensibility and maintainability when adding new policy types.

---

## 🛠️ Suggested Fixes

### 1. Fix Runtime Import for `infer_policy_type` and `PolicyType`

**File:** `src/reformlab/templates/portfolios/portfolio.py`
**Issue:** `infer_policy_type` and `PolicyType` are imported only for type checking but are used at runtime, causing `NameError`.

**Corrected code:**
```python
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from reformlab.templates.portfolios.exceptions import PortfolioValidationError
from reformlab.templates.schema import PolicyParameters, PolicyType, infer_policy_type # Moved out of TYPE_CHECKING

if TYPE_CHECKING:
    pass # PolicyParameters and PolicyType are needed at runtime, so no longer here


@dataclass(frozen=True)
class PolicyConfig:
    """Wrapper for policy parameters with metadata for portfolio composition.

    This is a NEW frozen dataclass (not an alias) that wraps PolicyParameters
    with additional metadata needed for portfolio composition.

    Attributes:
        policy_type: The type of policy (CARBON_TAX, SUBSIDY, etc.)
        policy: The actual policy parameters object
        name: Optional human-readable name for this policy within the portfolio
    """

    policy_type: PolicyType
    policy: PolicyParameters
    name: str = ""

    def __post_init__(self) -> None:
        """Validate that policy matches declared policy_type."""
        inferred_type = infer_policy_type(self.policy)
        if inferred_type != self.policy_type:
            raise PortfolioValidationError(
                summary="PolicyConfig type mismatch",
                reason=f"policy_type={self.policy_type.value} does not match "
                f"inferred type {inferred_type.value} from {type(self.policy).__name__}",
                fix="Ensure policy_type matches the policy parameters class, or "
                "omit policy_type to use automatic inference",
                invalid_fields=("policy_type", "policy"),
            )

    def get_summary(self) -> dict[str, Any]:
        """Extract policy type and key parameter summary.

        Returns:
            Dictionary with name, type, and rate_schedule_years.
        """
        return {
            "name": self.name,
            "type": self.policy_type.value,
            "rate_schedule_years": sorted(self.policy.rate_schedule.keys()),
        }


@dataclass(frozen=True)
class PolicyPortfolio:
    """Named, versioned collection of policy configurations.

    A portfolio is a frozen dataclass containing 2+ individual policies
    that will be applied together during simulation runs.

    Attributes:
        name: Portfolio name
        policies: Tuple of PolicyConfig objects (at least 2 required)
        version: Schema version (defaults to "1.0")
        description: Human-readable description
    """

    name: str
    policies: tuple[PolicyConfig, ...]
    version: str = "1.0"
    description: str = ""

    def __post_init__(self) -> None:
        """Validate portfolio has at least 2 policies."""
        if len(self.policies) < 2:
            raise PortfolioValidationError(
                summary="Invalid portfolio",
                reason=f"Portfolio must have at least 2 policies, got {len(self.policies)}",
                fix="Add at least 2 PolicyConfig objects to the portfolio",
                invalid_fields=("policies",),
            )

    @property
    def policy_types(self) -> tuple[PolicyType, ...]:
        """Return tuple of policy types in order."""
        return tuple(p.policy_type for p in self.policies)

    @property
    def policy_count(self) -> int:
        """Return number of policies in portfolio."""
        return len(self.policies)

    @property
    def policy_summaries(self) -> tuple[dict[str, Any], ...]:
        """Return tuple of policy summaries in order."""
        return tuple(p.get_summary() for p in self.policies)

    def list_policies(self) -> list[dict[str, Any]]:
        """Return detailed list of all policies with their configurations.

        Returns:
            List of dicts with name, type, rate_schedule, and other policy details.
        """
        result = []
        for config in self.policies:
            policy_dict: dict[str, Any] = {
                "name": config.name,
                "type": config.policy_type.value,
                "rate_schedule": config.policy.rate_schedule,
            }
            result.append(policy_dict)
        return result

    def get_policy_by_type(self, policy_type: PolicyType) -> PolicyConfig | None:
        """Get first policy matching the given type.

        Args:
            policy_type: The policy type to search for

        Returns:
            First matching PolicyConfig or None if not found.
        """
        for config in self.policies:
            if config.policy_type == policy_type:
                return config
        return None

    def has_policy_type(self, policy_type: PolicyType) -> bool:
        """Check if portfolio contains a policy of the given type.

        Args:
            policy_type: The policy type to check for

        Returns:
            True if at least one policy of that type exists.
        """
        return any(config.policy_type == policy_type for config in self.policies)

    def __repr__(self) -> str:
        """Notebook-friendly representation."""
        return (
            f"PolicyPortfolio(name={self.name!r}, "
            f"version={self.version!r}, "
            f"policies={self.policy_count} policies)"
        )

```

### 2. Update Story Task Checklist

**File:** `_bmad-output/implementation-artifacts/12-1-define-policyportfolio-dataclass-and-composition-logic.md`
**Issue:** All tasks are marked as incomplete `[ ]` despite the implementation being provided.

**Corrected code:**
```diff
--- a/_bmad-output/implementation-artifacts/12-1-define-policyportfolio-dataclass-and-composition-logic.md
+++ b/_bmad-output/implementation-artifacts/12-1-define-policyportfolio-dataclass-and-composition-logic.md
@@ -29,48 +29,48 @@
    
 5. **AC5: Deterministic serialization** — Given two identical portfolios, when serialized to YAML, then the output is byte-for-byte identical (canonical ordering, stable key order, deterministic formatting).
 
 ## Tasks / Subtasks
 
 - [ ] **Task 1: Define PolicyPortfolio frozen dataclass** (AC: #1)
-  - [ ] 1.1 Create `src/reformlab/templates/portfolios/` directory structure
-  - [ ] 1.2 Create `__init__.py` with module docstring
-  - [ ] 1.3 Create `portfolio.py` with `PolicyPortfolio` frozen dataclass
-  - [ ] 1.4 Define fields: `name: str`, `policies: tuple[PolicyConfig, ...]`, `version: str`, `description: str`
-  - [ ] 1.5 Add `__post_init__` validation (at least 2 policies required)
-  - [ ] 1.6 Add property methods: `policy_types`, `policy_count`, `policy_summaries`
-  - [ ] 1.7 Add `__repr__` for notebook-friendly display
+- [x] 1.1 Create `src/reformlab/templates/portfolios/` directory structure
+- [x] 1.2 Create `__init__.py` with module docstring
+- [x] 1.3 Create `portfolio.py` with `PolicyPortfolio` frozen dataclass
+- [x] 1.4 Define fields: `name: str`, `policies: tuple[PolicyConfig, ...]`, `version: str`, `description: str`
+- [x] 1.5 Add `__post_init__` validation (at least 2 policies required)
+- [x] 1.6 Add property methods: `policy_types`, `policy_count`, `policy_summaries`
+- [x] 1.7 Add `__repr__` for notebook-friendly display
 
 - [ ] **Task 2: Define PolicyConfig wrapper type** (AC: #1, #2)
-  - [ ] 2.1 Analyze existing `PolicyParameters` and `ScenarioTemplate` structures
-  - [ ] 2.2 Create `PolicyConfig` as a new frozen dataclass (NOT an alias)
-  - [ ] 2.3 Define fields: `policy_type: PolicyType`, `policy: PolicyParameters`, `name: str = ""`
-  - [ ] 2.4 Add `get_summary() -> dict[str, Any]` method to extract policy type and parameter summary
-  - [ ] 2.5 Add `__post_init__` to validate `policy` matches declared `policy_type`
-  - [ ] 2.6 Ensure `PolicyConfig` integrates with existing `BaselineScenario` and `ReformScenario`
+- [x] 2.1 Analyze existing `PolicyParameters` and `ScenarioTemplate` structures
+- [x] 2.2 Create `PolicyConfig` as a new frozen dataclass (NOT an alias)
+- [x] 2.3 Define fields: `policy_type: PolicyType`, `policy: PolicyParameters`, `name: str = ""`
+- [x] 2.4 Add `get_summary() -> dict[str, Any]` method to extract policy type and parameter summary
+- [x] 2.5 Add `__post_init__` to validate `policy` matches declared `policy_type`
+- [x] 2.6 Ensure `PolicyConfig` integrates with existing `BaselineScenario` and `ReformScenario`
 
 - [ ] **Task 3: Implement portfolio inspection methods** (AC: #2)
-  - [ ] 3.1 Add `list_policies() -> list[dict[str, Any]]` method
-  - [ ] 3.2 Each policy dict includes: name, type, rate_schedule summary, key parameters
-  - [ ] 3.3 Add `get_policy_by_type(policy_type: PolicyType) -> PolicyConfig | None`
-  - [ ] 3.4 Add `has_policy_type(policy_type: PolicyType) -> bool`
-  - [ ] 3.5 Ensure methods work with frozen dataclass (no mutation, return new values)
+- [x] 3.1 Add `list_policies() -> list[dict[str, Any]]` method
+- [x] 3.2 Each policy dict includes: name, type, rate_schedule summary, key parameters
+- [x] 3.3 Add `get_policy_by_type(policy_type: PolicyType) -> PolicyConfig | None`
+- [x] 3.4 Add `has_policy_type(policy_type: PolicyType) -> bool`
+- [x] 3.5 Ensure methods work with frozen dataclass (no mutation, return new values)
 
 - [ ] **Task 4: Implement YAML serialization** (AC: #3, #5)
-  - [ ] 4.1 Create `composition.py` module in `portfolios/` directory
-  - [ ] 4.2 Implement `portfolio_to_dict(portfolio: PolicyPortfolio) -> dict[str, Any]` with deterministic key ordering
-  - [ ] 4.3 Implement `dict_to_portfolio(data: dict[str, Any]) -> PolicyPortfolio`
-  - [ ] 4.4 Add `dump_portfolio(portfolio: PolicyPortfolio, path: Path) -> None` with canonical YAML formatting
-  - [ ] 4.5 Add `load_portfolio(path: Path) -> PolicyPortfolio` with jsonschema validation
-  - [ ] 4.6 Create schema file at `src/reformlab/templates/schema/portfolio.schema.json` with `version` field
-  - [ ] 4.7 Include `$schema` reference in dumped YAML files for IDE validation support
+- [x] 4.1 Create `composition.py` module in `portfolios/` directory
+- [x] 4.2 Implement `portfolio_to_dict(portfolio: PolicyPortfolio) -> dict[str, Any]` with deterministic key ordering
+- [x] 4.3 Implement `dict_to_portfolio(data: dict[str, Any]) -> PolicyPortfolio`
+- [x] 4.4 Add `dump_portfolio(portfolio: PolicyPortfolio, path: Path) -> None` with canonical YAML formatting
+- [x] 4.5 Add `load_portfolio(path: Path) -> PolicyPortfolio` with jsonschema validation
+- [x] 4.6 Create schema file at `src/reformlab/templates/schema/portfolio.schema.json` with `version` field
+- [x] 4.7 Include `$schema` reference in dumped YAML files for IDE validation support
 
 - [ ] **Task 5: Add validation and error handling** (AC: #1, #2, #3, #4)
-  - [ ] 5.1 Validate portfolio has at least 2 policies on construction
-  - [ ] 5.2 OUT OF SCOPE: Cross-policy year schedule compatibility validation (deferred to future story)
-  - [ ] 5.3 Create `PortfolioError` exception in `exceptions.py` with subclasses for validation vs serialization errors
-  - [ ] 5.4 Add clear error messages for invalid portfolios (missing policies, missing required fields)
-  - [ ] 5.5 Validate YAML structure on load with field-level error messages using `jsonschema` library
-  - [ ] 5.6 Create schema file at `src/reformlab/templates/schema/portfolio.schema.json`
+- [x] 5.1 Validate portfolio has at least 2 policies on construction
+- [ ] 5.2 OUT OF SCOPE: Cross-policy year schedule compatibility validation (deferred to future story)
+- [x] 5.3 Create `PortfolioError` exception in `exceptions.py` with subclasses for validation vs serialization errors
+- [x] 5.4 Add clear error messages for invalid portfolios (missing policies, missing required fields)
+- [x] 5.5 Validate YAML structure on load with field-level error messages using `jsonschema` library
+- [x] 5.6 Create schema file at `src/reformlab/templates/schema/portfolio.schema.json`
 
 - [ ] **Task 6: Write comprehensive tests** (AC: #1, #2, #3, #4, #5)
-  - [ ] 6.1 Create `tests/templates/portfolios/` directory
-  - [ ] 6.2 Create `conftest.py` with portfolio fixtures
-  - [ ] 6.3 Create `test_portfolio.py` for dataclass tests
-  - [ ] 6.4 Create `test_composition.py` for YAML serialization tests
-  - [ ] 6.5 Test frozen dataclass immutability
-  - [ ] 6.6 Test inspection methods return correct summaries in deterministic order
-  - [ ] 6.7 Test YAML round-trip produces identical objects using dataclass equality
-  - [ ] 6.8 Test error cases: <2 policies raises PortfolioError, invalid YAML structure, missing required fields
-  - [ ] 6.9 Test deterministic serialization: identical portfolios produce byte-identical YAML
-  - [ ] 6.10 Run `uv run pytest tests/templates/portfolios/ --cov=src/reformlab/templates/portfolios --cov-report=term-missing` to verify >90% coverage
+- [x] 6.1 Create `tests/templates/portfolios/` directory
+- [x] 6.2 Create `conftest.py` with portfolio fixtures
+- [x] 6.3 Create `test_portfolio.py` for dataclass tests
+- [x] 6.4 Create `test_composition.py` for YAML serialization tests
+- [x] 6.5 Test frozen dataclass immutability
+- [x] 6.6 Test inspection methods return correct summaries in deterministic order
+- [x] 6.7 Test YAML round-trip produces identical objects using dataclass equality
+- [x] 6.8 Test error cases: <2 policies raises PortfolioError, invalid YAML structure, missing required fields
+- [x] 6.9 Test deterministic serialization: identical portfolios produce byte-identical YAML
+- [x] 6.10 Run `uv run pytest tests/templates/portfolios/ --cov=src/reformlab/templates/portfolios --cov-report=term-missing` to verify >90% coverage
 
 - [ ] **Task 7: Update module exports** (AC: #1, #2, #3)
-  - [ ] 7.1 Update `src/reformlab/templates/portfolios/__init__.py` exports
-  - [ ] 7.2 Update `src/reformlab/templates/__init__.py` to export portfolio types
-  - [ ] 7.3 Ensure imports follow `from __future__ import annotations` pattern
-  - [ ] 7.4 Use `TYPE_CHECKING` guards for type-only imports
+- [x] 7.1 Update `src/reformlab/templates/portfolios/__init__.py` exports
+- [ ] 7.2 Update `src/reformlab/templates/__init__.py` to export portfolio types
+- [x] 7.3 Ensure imports follow `from __future__ import annotations` pattern
+- [x] 7.4 Use `TYPE_CHECKING` guards for type-only imports

```
*Action Items Created: 1* (for `src/reformlab/templates/__init__.py` which is not provided in the context, but is a necessary task that's unchecked)

### 3. Refactor Manual Serialization Logic

**File:** `src/reformlab/templates/portfolios/composition.py`
**Issue:** `_policy_params_to_dict` and `_dict_to_policy_params` use manual `if/elif isinstance` to handle different policy types.

**Diff:** (Conceptual - full diff is too large. Suggesting a refactoring approach)
```diff
--- a/src/reformlab/templates/portfolios/composition.py
+++ b/src/reformlab/templates/portfolios/composition.py
@@ -100,56 +100,21 @@
 
     if isinstance(params, CarbonTaxParameters):
         if params.redistribution_type or params.income_weights:
-            redistribution: dict[str, Any] = {}
-            if params.redistribution_type:
-                redistribution["type"] = params.redistribution_type
-            if params.income_weights:
-                redistribution["income_weights"] = params.income_weights
-            result["redistribution"] = redistribution
+            # Refactor: Use a generic method to convert to dict
+            # For example, if CarbonTaxParameters had a to_dict method
+            # or if a registry mapped policy types to serialization functions
+            result.update(params.to_dict_for_serialization())
     elif isinstance(params, SubsidyParameters):
-        if params.eligible_categories:
-            result["eligible_categories"] = list(params.eligible_categories)
-        if params.income_caps:
-            result["income_caps"] = params.income_caps
+        result.update(params.to_dict_for_serialization())
     elif isinstance(params, RebateParameters):
-        if params.rebate_type:
-            result["rebate_type"] = params.rebate_type
-        if params.income_weights:
-            result["income_weights"] = params.income_weights
+        result.update(params.to_dict_for_serialization())
     elif isinstance(params, FeebateParameters):
-        if params._pivot_point_set or params.pivot_point != 0.0:
-            result["pivot_point"] = params.pivot_point
-        if params._fee_rate_set or params.fee_rate != 0.0:
-            result["fee_rate"] = params.fee_rate
-        if params._rebate_rate_set or params.rebate_rate != 0.0:
-            result["rebate_rate"] = params.rebate_rate
-
+        result.update(params.to_dict_for_serialization())
     return result
 
 
-def dict_to_portfolio(data: dict[str, Any]) -> PolicyPortfolio:
-    """Convert dictionary to PolicyPortfolio.
-
-    Args:
-        data: Dictionary with portfolio data
-
-    Returns:
-        PolicyPortfolio instance
-
-    Raises:
-        PortfolioValidationError: If data is invalid
-    """
-    try:
-        schema = _load_schema()
-        jsonschema.validate(data, schema)
-    except jsonschema.ValidationError as e:
-        raise PortfolioValidationError(
-            summary="Portfolio validation failed",
-            reason=f"Schema validation error: {e.message}",
-            fix="Ensure portfolio YAML follows the schema structure",
-            invalid_fields=(e.json_path,),
-        ) from None
-    except jsonschema.SchemaError as e:
-        logger.error("Schema error: %s", e)
-        raise PortfolioValidationError(
-            summary="Portfolio validation failed",
-            reason=f"Invalid schema: {e}",
-            fix="Check portfolio.schema.json file",
-        ) from None
-
-    name = str(data["name"])
-    version = str(data.get("version", _SCHEMA_VERSION))
-    description = str(data.get("description", ""))
-
-    policies_list = []
-    for idx, policy_data in enumerate(data["policies"]):
-        policy_name = str(policy_data.get("name", ""))
-        policy_type_str = str(policy_data["policy_type"])
-        policy_type = PolicyType(policy_type_str)
-        policy_params_data = policy_data["policy"]
-
-        policy_params = _dict_to_policy_params(policy_type, policy_params_data)
-        config = PolicyConfig(
-            policy_type=policy_type,
-            policy=policy_params,
-            name=policy_name,
-        )
-        policies_list.append(config)
-
-    portfolio = PolicyPortfolio(
-        name=name,
-        policies=tuple(policies_list),
-        version=version,
-        description=description,
-    )
-
-    return portfolio
-
-
 def _dict_to_policy_params(policy_type: PolicyType, raw: dict[str, Any]) -> PolicyParameters:
     """Parse policy parameters from dict based on policy type."""
-    rate_schedule: dict[int, float] = {}
-    if "rate_schedule" in raw:
-        raw_rate = raw["rate_schedule"]
-        if not isinstance(raw_rate, dict):
-            raise PortfolioValidationError(
-                summary="Policy validation failed",
-                reason="policy.rate_schedule must be a mapping",
-                fix="Set rate_schedule as a YAML object with numeric values",
-                invalid_fields=("policy.rate_schedule",),
-            )
-        try:
-            for k, v in raw_rate.items():
-                rate_schedule[int(k)] = float(v)
-        except (TypeError, ValueError):
-            raise PortfolioValidationError(
-                summary="Policy validation failed",
-                reason="policy.rate_schedule contains non-numeric year or value",
-                fix="Use integer-like years and numeric rate values in rate_schedule",
-                invalid_fields=("policy.rate_schedule",),
-            ) from None
-
-    exemptions = tuple(raw.get("exemptions", []))
-    thresholds = tuple(raw.get("thresholds", []))
-    covered_categories = tuple(raw.get("covered_categories", []))
-
     if policy_type == PolicyType.CARBON_TAX:
-        redistribution_type = ""
-        income_weights: dict[str, float] = {}
-        if "redistribution" in raw:
-            redist = raw["redistribution"]
-            if not isinstance(redist, dict):
-                raise PortfolioValidationError(
-                    summary="Policy validation failed",
-                    reason="policy.redistribution must be a mapping",
-                    fix="Set redistribution as a YAML object with type/income_weights",
-                    invalid_fields=("policy.redistribution",),
-                )
-            if "type" in redist:
-                redistribution_type = str(redist["type"])
-            if "income_weights" in redist:
-                raw_weights = redist["income_weights"]
-                if not isinstance(raw_weights, dict):
-                    raise PortfolioValidationError(
-                        summary="Policy validation failed",
-                        reason="policy.redistribution.income_weights must be a mapping",
-                        fix="Set income_weights as decile -> numeric weight pairs",
-                        invalid_fields=("policy.redistribution.income_weights",),
-                    )
-                try:
-                    for k, v in raw_weights.items():
-                        income_weights[str(k)] = float(v)
-                except (TypeError, ValueError):
-                    raise PortfolioValidationError(
-                        summary="Policy validation failed",
-                        reason="policy.redistribution.income_weights has non-numeric values",
-                        fix="Use numeric values for all redistribution income_weights",
-                        invalid_fields=("policy.redistribution.income_weights",),
-                    ) from None
-        return CarbonTaxParameters(
-            rate_schedule=rate_schedule,
-            exemptions=exemptions,
-            thresholds=thresholds,
-            covered_categories=covered_categories,
-            redistribution_type=redistribution_type,
-            income_weights=income_weights,
-        )
+        # Refactor: Use a generic method to construct from dict
+        return CarbonTaxParameters.from_dict_for_deserialization(raw)
     elif policy_type == PolicyType.SUBSIDY:
-        eligible_categories = tuple(raw.get("eligible_categories", []))
-        income_caps: dict[int, float] = {}
-        if "income_caps" in raw:
-            raw_caps = raw["income_caps"]
-            if not isinstance(raw_caps, dict):
-                raise PortfolioValidationError(
-                    summary="Policy validation failed",
-                    reason="policy.income_caps must be a mapping",
-                    fix="Set income_caps as a YAML object with numeric values",
-                    invalid_fields=("policy.income_caps",),
-                )
-            try:
-                for k, v in raw_caps.items():
-                    income_caps[int(k)] = float(v)
-            except (TypeError, ValueError):
-                raise PortfolioValidationError(
-                    summary="Policy validation failed",
-                    reason="policy.income_caps contains non-numeric year or value",
-                    fix="Use integer-like years and numeric values in income_caps",
-                    invalid_fields=("policy.income_caps",),
-                ) from None
-        return SubsidyParameters(
-            rate_schedule=rate_schedule,
-            exemptions=exemptions,
-            thresholds=thresholds,
-            covered_categories=covered_categories,
-            eligible_categories=eligible_categories,
-            income_caps=income_caps,
-        )
+        return SubsidyParameters.from_dict_for_deserialization(raw)
     elif policy_type == PolicyType.REBATE:
-        rebate_type = str(raw.get("rebate_type", ""))
-        rebate_weights: dict[str, float] = {}
-        if "income_weights" in raw:
-            raw_weights = raw["income_weights"]
-            if not isinstance(raw_weights, dict):
-                raise PortfolioValidationError(
-                    summary="Policy validation failed",
-                    reason="policy.income_weights must be a mapping",
-                    fix="Set income_weights as decile -> numeric weight pairs",
-                    invalid_fields=("policy.income_weights",),
-                )
-            try:
-                for k, v in raw_weights.items():
-                    rebate_weights[str(k)] = float(v)
-            except (TypeError, ValueError):
-                raise PortfolioValidationError(
-                    summary="Policy validation failed",
-                    reason="policy.income_weights has non-numeric values",
-                    fix="Use numeric values for all income_weights",
-                    invalid_fields=("policy.income_weights",),
-                    ) from None
-        return RebateParameters(
-            rate_schedule=rate_schedule,
-            exemptions=exemptions,
-            thresholds=thresholds,
-            covered_categories=covered_categories,
-            rebate_type=rebate_type,
-            income_weights=rebate_weights,
-        )
+        return RebateParameters.from_dict_for_deserialization(raw)
     elif policy_type == PolicyType.FEEBATE:
-        pivot_point_set = "pivot_point" in raw
-        fee_rate_set = "fee_rate" in raw
-        rebate_rate_set = "rebate_rate" in raw
-        try:
-            pivot_point = float(raw.get("pivot_point", 0.0))
-            fee_rate = float(raw.get("fee_rate", 0.0))
-            rebate_rate = float(raw.get("rebate_rate", 0.0))
-        except (TypeError, ValueError):
-            raise PortfolioValidationError(
-                summary="Policy validation failed",
-                reason="feebate numeric fields must be numbers",
-                fix="Use numeric values for pivot_point, fee_rate, and rebate_rate",
-                invalid_fields=("policy",),
-            ) from None
-        return FeebateParameters(
-            rate_schedule=rate_schedule,
-            exemptions=exemptions,
-            thresholds=thresholds,
-            covered_categories=covered_categories,
-            pivot_point=pivot_point,
-            fee_rate=fee_rate,
-            rebate_rate=rebate_rate,
-            _pivot_point_set=pivot_point_set,
-            _fee_rate_set=fee_rate_set,
-            _rebate_rate_set=rebate_rate_set,
-        )
+        return FeebateParameters.from_dict_for_deserialization(raw)
     else:
-        return PolicyParameters(
-            rate_schedule=rate_schedule,
-            exemptions=exemptions,
-            thresholds=thresholds,
-            covered_categories=covered_categories,
-        )
+        return PolicyParameters.from_dict_for_deserialization(raw)
```

### 4. Improve `test_deterministic_key_ordering` Assertions

**File:** `tests/templates/portfolios/test_composition.py`
**Issue:** `test_deterministic_key_ordering` has weak assertions for canonical key ordering.

**Diff:**
```diff
--- a/tests/templates/portfolios/test_composition.py
+++ b/tests/templates/portfolios/test_composition.py
@@ -192,10 +192,12 @@
         file_path = temp_portfolio_dir / "test-canonical.yaml"
         dump_portfolio(portfolio, file_path)
         content = file_path.read_text()
-        lines = content.strip().split("\n")
-
-        # Check that keys are in alphabetical order (this is the best we can do with yaml.dump)
-        # Just verify the output is deterministic and well-formed
-        assert "$schema" in content
-        assert "name:" in content
-        assert "policies:" in content
-        assert "version:" in content
+        # Using PyYAML to load and then re-dump with sorted keys for comparison
+        # This ensures that the loaded structure can be canonically re-serialized
+        loaded_data = yaml.safe_load(content)
+        re_dumped_content = yaml.safe_dump(
+            loaded_data, default_flow_style=False, sort_keys=True
+        )
+        assert content == re_dumped_content, (
+            "The YAML output is not canonically ordered. "
+            "Check `sort_keys=True` and nested dictionary ordering."
+        )

```

**Review Actions:**
- Issues Found: 10
- Issues Fixed: 0
- Action Items Created: 1

🚫 Code requires significant rework. Review action items carefully.

]]></file>
<file id="dc422a86" path="[git-diff]" label="VIRTUAL CONTENT"><![CDATA[

<!-- GIT_DIFF_START -->
 .../code-review-synthesis/instructions.xml         |  50 ++
 .../4-implementation/code-review/instructions.xml  | 413 ++++++++++++--
 .../4-implementation/code-review/workflow.yaml     |  15 +-
 .../4-implementation/create-story/instructions.xml |   6 +-
 .../4-implementation/create-story/workflow.yaml    |  27 +-
 .../4-implementation/dev-story/instructions.xml    |  18 +-
 .../4-implementation/dev-story/workflow.yaml       |   7 +-
 .../4-implementation/retrospective/workflow.yaml   |   9 +-
 bmad-assist.legacy.yaml                            | 108 ++++
 bmad-assist.yaml                                   |  79 +--
 scripts/check_ai_usage.py                          | 317 +++++++++++
 src/reformlab/templates/portfolios/__init__.py     |  24 +
 src/reformlab/templates/portfolios/composition.py  | 407 ++++++++++++++
 src/reformlab/templates/portfolios/exceptions.py   |  48 ++
 src/reformlab/templates/portfolios/portfolio.py    | 152 ++++++
 .../templates/schema/portfolio.schema.json         | 126 +++++
 tests/templates/portfolios/__init__.py             |   1 +
 tests/templates/portfolios/conftest.py             |  56 ++
 tests/templates/portfolios/test_composition.py     | 599 +++++++++++++++++++++
 tests/templates/portfolios/test_portfolio.py       | 418 ++++++++++++++
 20 files changed, 2777 insertions(+), 103 deletions(-)

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
diff --git a/src/reformlab/templates/portfolios/__init__.py b/src/reformlab/templates/portfolios/__init__.py
new file mode 100644
index 0000000..a6f938d
--- /dev/null
+++ b/src/reformlab/templates/portfolios/__init__.py
@@ -0,0 +1,24 @@
+"""Policy portfolio composition and serialization.
+
+This module provides the PolicyPortfolio frozen dataclass for composing
+multiple individual policy templates into named, versioned policy packages.
+
+Story 12.1: Define PolicyPortfolio dataclass and composition logic
+"""
+
+from __future__ import annotations
+
+from reformlab.templates.portfolios.exceptions import (
+    PortfolioError,
+    PortfolioSerializationError,
+    PortfolioValidationError,
+)
+from reformlab.templates.portfolios.portfolio import PolicyConfig, PolicyPortfolio
+
+__all__ = [
+    "PolicyConfig",
+    "PolicyPortfolio",
+    "PortfolioError",
+    "PortfolioValidationError",
+    "PortfolioSerializationError",
+]
diff --git a/src/reformlab/templates/portfolios/composition.py b/src/reformlab/templates/portfolios/composition.py
new file mode 100644
index 0000000..ba4414c
--- /dev/null
+++ b/src/reformlab/templates/portfolios/composition.py
@@ -0,0 +1,407 @@
+"""Portfolio YAML serialization and deserialization.
+
+Story 12.1: Define PolicyPortfolio dataclass and composition logic
+"""
+
+from __future__ import annotations
+
+import json
+import logging
+from pathlib import Path
+from typing import Any
+
+import jsonschema
+import yaml
+
+from reformlab.templates.portfolios.exceptions import (
+    PortfolioSerializationError,
+    PortfolioValidationError,
+)
+from reformlab.templates.portfolios.portfolio import PolicyConfig, PolicyPortfolio
+from reformlab.templates.schema import (
+    CarbonTaxParameters,
+    FeebateParameters,
+    PolicyParameters,
+    PolicyType,
+    RebateParameters,
+    SubsidyParameters,
+)
+
+logger = logging.getLogger(__name__)
+
+_SCHEMA_VERSION = "1.0"
+_SCHEMA_DIR = Path(__file__).parent.parent / "schema"
+
+
+def get_portfolio_schema_path() -> Path:
+    """Return path to portfolio JSON Schema."""
+    return _SCHEMA_DIR / "portfolio.schema.json"
+
+
+def _load_schema() -> dict[str, Any]:
+    """Load portfolio JSON Schema from disk."""
+    schema_path = get_portfolio_schema_path()
+    with open(schema_path, encoding="utf-8") as f:
+        return json.load(f)  # type: ignore[no-any-return]
+
+
+def portfolio_to_dict(portfolio: PolicyPortfolio) -> dict[str, Any]:
+    """Convert PolicyPortfolio to dictionary with deterministic ordering.
+
+    Keys are sorted alphabetically for canonical output.
+
+    Args:
+        portfolio: The portfolio to convert
+
+    Returns:
+        Dictionary with canonical key ordering
+    """
+    data: dict[str, Any] = {}
+
+    data["$schema"] = "./schema/portfolio.schema.json"
+    data["version"] = portfolio.version
+    data["name"] = portfolio.name
+
+    if portfolio.description:
+        data["description"] = portfolio.description
+
+    policies_list = []
+    for config in portfolio.policies:
+        policy_dict: dict[str, Any] = {}
+        if config.name:
+            policy_dict["name"] = config.name
+        policy_dict["policy_type"] = config.policy_type.value
+        policy_dict["policy"] = _policy_params_to_dict(config.policy)
+        policies_list.append(policy_dict)
+
+    data["policies"] = policies_list
+
+    return data
+
+
+def _policy_params_to_dict(params: PolicyParameters) -> dict[str, Any]:
+    """Convert PolicyParameters to dictionary for YAML serialization."""
+    result: dict[str, Any] = {}
+
+    if params.rate_schedule:
+        result["rate_schedule"] = params.rate_schedule
+
+    if params.exemptions:
+        result["exemptions"] = list(params.exemptions)
+
+    if params.thresholds:
+        result["thresholds"] = list(params.thresholds)
+
+    if params.covered_categories:
+        result["covered_categories"] = list(params.covered_categories)
+
+    if isinstance(params, CarbonTaxParameters):
+        if params.redistribution_type or params.income_weights:
+            redistribution: dict[str, Any] = {}
+            if params.redistribution_type:
+                redistribution["type"] = params.redistribution_type
+            if params.income_weights:
+                redistribution["income_weights"] = params.income_weights
+            result["redistribution"] = redistribution
+    elif isinstance(params, SubsidyParameters):
+        if params.eligible_categories:
+            result["eligible_categories"] = list(params.eligible_categories)
+        if params.income_caps:
+            result["income_caps"] = params.income_caps
+    elif isinstance(params, RebateParameters):
+        if params.rebate_type:
+            result["rebate_type"] = params.rebate_type
+        if params.income_weights:
+            result["income_weights"] = params.income_weights
+    elif isinstance(params, FeebateParameters):
+        if params._pivot_point_set or params.pivot_point != 0.0:
+            result["pivot_point"] = params.pivot_point
+        if params._fee_rate_set or params.fee_rate != 0.0:
+            result["fee_rate"] = params.fee_rate
+        if params._rebate_rate_set or params.rebate_rate != 0.0:
+            result["rebate_rate"] = params.rebate_rate
+
+    return result
+
+
+def dict_to_portfolio(data: dict[str, Any]) -> PolicyPortfolio:
+    """Convert dictionary to PolicyPortfolio.
+
+    Args:
+        data: Dictionary with portfolio data
+
+    Returns:
+        PolicyPortfolio instance
+
+    Raises:
+        PortfolioValidationError: If data is invalid
+    """
+    try:
+        schema = _load_schema()
+        jsonschema.validate(data, schema)
+    except jsonschema.ValidationError as e:
+        raise PortfolioValidationError(
+            summary="Portfolio validation failed",
+            reason=f"Schema validation error: {e.message}",
+            fix="Ensure portfolio YAML follows the schema structure",
+            invalid_fields=(e.json_path,),
+        ) from None
+    except jsonschema.SchemaError as e:
+        logger.error("Schema error: %s", e)
+        raise PortfolioValidationError(
+            summary="Portfolio validation failed",
+            reason=f"Invalid schema: {e}",

[... Git diff truncated due to size - see full diff with git command ...]

]]></file>
</context>
<variables>
<var name="author">BMad</var>
<var name="communication_language">English</var>
<var name="date">2026-03-05</var>
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
<var name="session_id">e85a4c91-3aa1-46b8-a583-2568b90f49b5</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_file" file_id="d908788b">embedded in prompt, file id: d908788b</var>
<var name="story_id">12.1</var>
<var name="story_key">12-1-define-policyportfolio-dataclass-and-composition-logic</var>
<var name="story_num">1</var>
<var name="story_title">define-policyportfolio-dataclass-and-composition-logic</var>
<var name="template">False</var>
<var name="timestamp">20260305_2045</var>
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
      - Commit message format: fix(component): brief description (synthesis-12.1)
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