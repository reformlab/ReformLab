<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 11 -->
<!-- Story: 4 -->
<!-- Phase: code-review-synthesis -->
<!-- Timestamp: 20260303T174550Z -->
<compiled-workflow>
<mission><![CDATA[

Master Code Review Synthesis: Story 11.4

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
<file id="6870c5a9" path="_bmad-output/implementation-artifacts/11-4-define-mergemethod-protocol-and-uniform-distribution-method.md" label="STORY FILE"><![CDATA[


# Story 11.4: Define MergeMethod protocol and implement uniform distribution method

Status: dev-complete

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform developer building the French household population pipeline,
I want a `MergeMethod` protocol defining the interface for statistical dataset fusion and a concrete `UniformMergeMethod` implementation that randomly matches rows between two tables,
so that downstream stories (11.5 IPF/conditional sampling, 11.6 pipeline builder) have a proven protocol pattern to follow, and the simplest merge method is available as a baseline for population construction.

## Acceptance Criteria

1. Given the `MergeMethod` protocol, when a new method is implemented, then it must accept two `pa.Table` inputs plus a config, and return a merged table plus an assumption record.
2. Given two tables with no shared sample, when merged using uniform distribution, then each row from Table A is matched with a uniformly random row from Table B with replacement, using the provided `MergeConfig.seed` to guarantee reproducibility.
3. Given a uniform merge, when the assumption record is inspected, then it states: "Each household in source A is matched to a household in source B with uniform probability — this assumes no correlation between the variables in the two sources."
4. Given the uniform method docstring, when read, then it includes a plain-language explanation of the independence assumption and when this is appropriate vs. problematic.

## Tasks / Subtasks

- [x] Task 1: Create `src/reformlab/population/methods/` directory structure (AC: #1)
  - [x]1.1 Create `src/reformlab/population/methods/__init__.py` with module docstring referencing Story 11.4, FR38, FR39
  - [x]1.2 Create `src/reformlab/population/methods/errors.py` with `MergeError` base exception and `MergeValidationError` — follow the `summary - reason - fix` pattern from `DataSourceError` in `population/loaders/errors.py`

- [x] Task 2: Define `MergeMethod` protocol and supporting types — `base.py` (AC: #1, #3)
  - [x]2.1 Create `src/reformlab/population/methods/base.py` with module docstring referencing Story 11.4, FR38
  - [x]2.2 Define `MergeConfig` frozen dataclass with fields: `seed: int`, `description: str = ""`, `drop_right_columns: tuple[str, ...] = ()` — validate in `__post_init__` that `seed` is a non-negative integer and not a `bool` (Python `bool ⊂ int`; follow `manifest.py:219` pattern)
  - [x]2.3 Define `MergeAssumption` frozen dataclass with fields: `method_name: str`, `statement: str`, `details: dict[str, Any]` — include `to_governance_entry(*, source_label: str = "merge_step") -> dict[str, Any]` method that produces a dict compatible with `governance.manifest.AssumptionEntry` (keys: `key`, `value`, `source`, `is_default`). `details` values must be JSON-compatible (`str`, `int`, `float`, `bool`, `None`, `list`, `dict`) — enforced at `RunManifest` construction by `_validate_json_compatible()`. Never put `pa.Table`, `pa.Schema`, `Path`, or custom objects in `details`. The `to_governance_entry()` must unpack `**self.details` first, then override with `method` and `statement` keys to prevent key collision from details
  - [x]2.4 Define `MergeResult` frozen dataclass with fields: `table: pa.Table`, `assumption: MergeAssumption`
  - [x]2.5 Define `MergeMethod` as `@runtime_checkable` Protocol with two required members:
    - `def merge(self, table_a: pa.Table, table_b: pa.Table, config: MergeConfig) -> MergeResult`
    - `name: str` property (read-only)
  - [x]2.6 Validate design: `MergeConfig.__post_init__` deep-copies `drop_right_columns` to prevent aliasing (use `object.__setattr__` pattern from `SourceConfig`)
  - [x]2.7 Validate design: `MergeAssumption.details` deep-copied in `__post_init__` to prevent mutation

- [x] Task 3: Implement `UniformMergeMethod` — `uniform.py` (AC: #2, #3, #4)
  - [x]3.1 Create `src/reformlab/population/methods/uniform.py` with module docstring referencing Story 11.4, FR38, FR39 — include the pedagogical docstring explaining the independence assumption in plain language (when appropriate: independent surveys; when problematic: correlated variables)
  - [x]3.2 Implement `UniformMergeMethod` class with `__init__(self)` (no constructor parameters — uniform has no method-specific config)
  - [x]3.3 Implement `name` property returning `"uniform"`
  - [x]3.4 Implement `merge(self, table_a, table_b, config)` with this logic:
    1. Validate inputs: both tables must have `num_rows > 0`; raise `MergeValidationError` if empty
    2. Apply `config.drop_right_columns`: remove listed columns from table_b before merge; raise `MergeValidationError` if a column in `drop_right_columns` does not exist in table_b
    3. Check column name conflicts: `set(table_a.schema.names) & set(remaining_b.schema.names)` — raise `MergeValidationError` with exact overlapping names if any
    4. Generate random indices: `random.Random(config.seed)`, generate `table_a.num_rows` random integers in `[0, remaining_b.num_rows)` — this is random matching with replacement (each row from B can be matched to multiple rows from A)
    5. Select matched rows: `remaining_b.take(pa.array(indices))` — efficient vectorized row selection
    6. Combine columns: build merged table by combining all columns from table_a and matched table_b columns
    7. Build `MergeAssumption` with:
       - `method_name="uniform"`
       - `statement="Each household in source A is matched to a household in source B with uniform probability — this assumes no correlation between the variables in the two sources."`
       - `details={"table_a_rows": n, "table_b_rows": m, "seed": config.seed, "with_replacement": True, "dropped_right_columns": list(config.drop_right_columns)}`
    8. Return `MergeResult(table=merged, assumption=assumption)`
  - [x]3.5 Use `logging.getLogger(__name__)` with structured `event=merge_start`, `event=merge_complete` log entries including `method=uniform rows_a=... rows_b=... seed=...`

- [x] Task 4: Update `__init__.py` exports (AC: #1)
  - [x]4.1 Export from `src/reformlab/population/methods/__init__.py`: `MergeMethod`, `MergeConfig`, `MergeAssumption`, `MergeResult`, `UniformMergeMethod`, `MergeError`, `MergeValidationError` — define `__all__` listing all exports explicitly (follow `population/loaders/__init__.py` pattern)
  - [x]4.2 Add methods exports to `src/reformlab/population/__init__.py`: same names as 4.1

- [x] Task 5: Create test infrastructure (AC: all)
  - [x]5.1 Create `tests/population/methods/__init__.py`
  - [x]5.2 Create `tests/population/methods/conftest.py` with fixtures:
    - `income_table` — small `pa.Table` with columns: `household_id` (int64), `income` (float64), `region_code` (utf8) — 5 rows
    - `vehicle_table` — small `pa.Table` with columns: `vehicle_type` (utf8), `vehicle_age` (int64), `fuel_type` (utf8) — 8 rows
    - `overlapping_table` — small `pa.Table` with a column name that conflicts with `income_table` (e.g., `region_code`)
    - `empty_table` — `pa.Table` with schema but 0 rows
    - `default_config` — `MergeConfig(seed=42)`

- [x] Task 6: Write comprehensive tests (AC: all)
  - [x]6.1 `tests/population/methods/test_base.py`:
    - `TestMergeConfig`: frozen, `__post_init__` validation (negative seed raises `ValueError`, `bool` seed raises `ValueError`), `drop_right_columns` deep-copied, default values
    - `TestMergeAssumption`: frozen, `details` deep-copied, `to_governance_entry()` returns correct dict with `key`/`value`/`source`/`is_default` fields
    - `TestMergeResult`: frozen, holds table + assumption
    - `TestMergeMethodProtocol`: verify `UniformMergeMethod` passes `isinstance(m, MergeMethod)` check; verify a non-conforming class fails
  - [x]6.2 `tests/population/methods/test_uniform.py`:
    - `TestUniformMergeMethodProtocol`: `isinstance()` check against `MergeMethod`
    - `TestUniformMergeMethodName`: `name` property returns `"uniform"`
    - `TestUniformMergeMethodMerge`:
      - Basic merge: income_table (5 rows) + vehicle_table (8 rows) → merged table with 5 rows and 6 columns (3 from A + 3 from B)
      - Column names: merged table has all columns from both tables
      - Row count: merged table has same row count as table_a
      - Values preserved: all values from table_a are present unchanged in corresponding columns
      - Values from table_b: matched values come from actual rows in table_b (not fabricated)
    - `TestUniformMergeMethodDeterminism`:
      - Same seed → identical merged table (row-by-row comparison)
      - Different seed → different row matching (at least one row differs, verified statistically with high probability for the test fixture sizes)
    - `TestUniformMergeMethodColumnConflict`:
      - Overlapping column names → `MergeValidationError` with exact conflicting names in message
    - `TestUniformMergeMethodDropRightColumns`:
      - `drop_right_columns=("region_code",)` removes `region_code` from right table before merge
      - Invalid `drop_right_columns` with nonexistent column → `MergeValidationError`
    - `TestUniformMergeMethodEmptyTable`:
      - Empty table_a → `MergeValidationError`
      - Empty table_b → `MergeValidationError`
    - `TestUniformMergeMethodAssumption`:
      - `assumption.method_name == "uniform"`
      - `assumption.statement` contains the exact AC #3 text
      - `assumption.details` contains `table_a_rows`, `table_b_rows`, `seed`, `with_replacement`
      - `assumption.to_governance_entry()` returns dict with `key`, `value`, `source`, `is_default` fields
    - `TestUniformMergeMethodWithReplacement`:
      - When table_a has more rows than table_b, merge still works (with replacement)
      - When table_a has fewer rows than table_b, merge still works
      - When table_a and table_b have equal rows, merge still works
    - `TestUniformMergeMethodDocstring`:
      - Class docstring is non-empty
      - Class docstring contains "independence" or "no correlation" (pedagogical content)
  - [x]6.3 `tests/population/methods/test_errors.py`:
    - `TestMergeError`: inherits `Exception`, `summary-reason-fix` message format, attributes accessible
    - `TestMergeValidationError`: inherits `MergeError`

- [x] Task 7: Run full test suite and lint (AC: all)
  - [x]7.1 `uv run pytest tests/population/methods/` — all new tests pass
  - [x]7.2 `uv run pytest tests/population/` — no regressions in loader tests
  - [x]7.3 `uv run ruff check src/reformlab/population/methods/ tests/population/methods/` — no lint errors
  - [x]7.4 `uv run mypy src/reformlab/population/methods/` — no mypy errors (strict mode)

## Dev Notes

### Architecture Context: Statistical Methods Library

This story creates the `src/reformlab/population/methods/` subsystem — the second major component of EPIC-11 (after `loaders/`). The architecture specifies this directory explicitly:

```
src/reformlab/population/
├── loaders/           ← Institutional data source loaders (Stories 11.1–11.3, DONE)
│   ├── base.py        ← DataSourceLoader protocol + CachedLoader
│   ├── cache.py       ← SourceCache
│   ├── errors.py      ← DataSourceError hierarchy
│   ├── insee.py       ← INSEELoader
│   ├── eurostat.py    ← EurostatLoader
│   ├── ademe.py       ← ADEMELoader
│   └── sdes.py        ← SDESLoader
├── methods/           ← Statistical fusion methods library (THIS STORY starts it)
│   ├── __init__.py
│   ├── base.py        ← MergeMethod protocol + MergeConfig + MergeAssumption + MergeResult
│   ├── errors.py      ← MergeError hierarchy
│   └── uniform.py     ← UniformMergeMethod (this story)
│                      ← ipf.py, conditional.py, matching.py added in Story 11.5
├── pipeline.py        ← PopulationPipeline builder (Story 11.6)
├── assumptions.py     ← Assumption recording integration (Story 11.6)
└── validation.py      ← Validate against known marginals (Story 11.7)
```

### Protocol Design Pattern (from DataSourceLoader)

Follow the **exact same protocol pattern** established in `src/reformlab/population/loaders/base.py`:

1. **`@runtime_checkable` Protocol** — enables `isinstance()` checks for structural typing
2. **Frozen dataclasses** for all value objects (`MergeConfig`, `MergeAssumption`, `MergeResult`)
3. **`__post_init__` validation** — validate and deep-copy mutable fields using `object.__setattr__()` pattern
4. **No abstract base classes** — Protocols, not ABCs (per project-context.md)
5. **Subsystem-specific exceptions** — `MergeError` hierarchy, not bare `ValueError` or `Exception`

### MergeMethod Protocol — Exact Specification

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class MergeMethod(Protocol):
    """Interface for statistical dataset fusion methods.

    Structural (duck-typed) protocol: any class that implements
    ``merge()`` and the ``name`` property with the correct signatures
    satisfies the contract — no explicit inheritance required.

    Each method merges two ``pa.Table`` objects using a specific
    statistical approach, returning the merged table and an assumption
    record documenting the methodological choice.
    """

    @property
    def name(self) -> str:
        """Short identifier for this method (e.g., "uniform", "ipf")."""
        ...

    def merge(
        self,
        table_a: pa.Table,
        table_b: pa.Table,
        config: MergeConfig,
    ) -> MergeResult:
        """Merge two tables using this method's statistical approach."""
        ...
```

### MergeConfig — Exact Specification

```python
@dataclass(frozen=True)
class MergeConfig:
    """Immutable configuration for a merge operation.

    Attributes:
        seed: Random seed for deterministic merge operations. Must be >= 0.
        description: Optional human-readable description for governance.
        drop_right_columns: Column names to remove from table_b before
            merging. Use this to remove shared key columns (e.g.,
            "region_code") that exist in both tables but should only
            appear once in the result.
    """

    seed: int
    description: str = ""
    drop_right_columns: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.seed, int) or isinstance(self.seed, bool) or self.seed < 0:
            raise ValueError(
                f"seed must be a non-negative integer, got {self.seed!r}"
            )
        # Deep-copy mutable-origin field
        object.__setattr__(
            self, "drop_right_columns", tuple(self.drop_right_columns)
        )
```

### MergeAssumption — Governance Integration

The `MergeAssumption` must produce records compatible with the existing `governance.manifest.AssumptionEntry` TypedDict (defined in `src/reformlab/governance/manifest.py` lines 60–73):

```python
class AssumptionEntry(TypedDict):
    key: str           # assumption identifier
    value: Any         # JSON-compatible value
    source: str        # e.g., "merge_step", "runtime"
    is_default: bool   # always False for merge assumptions (explicit choice)
```

The `to_governance_entry()` method on `MergeAssumption` bridges the gap:

```python
@dataclass(frozen=True)
class MergeAssumption:
    """Structured assumption record from a merge operation.

    Records the method name, a plain-language assumption statement,
    and method-specific details. Can be converted to governance
    ``AssumptionEntry`` format via ``to_governance_entry()``.
    """

    method_name: str
    statement: str
    details: dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "details", deepcopy(self.details))

    def to_governance_entry(
        self, *, source_label: str = "merge_step"
    ) -> dict[str, Any]:
        """Convert to governance-compatible assumption entry.

        Returns a dict matching ``governance.manifest.AssumptionEntry``
        structure: key, value, source, is_default.
        """
        return {
            "key": f"merge_{self.method_name}",
            "value": {
                **self.details,
                "method": self.method_name,
                "statement": self.statement,
            },
            "source": source_label,
            "is_default": False,
        }
```

**CRITICAL:** The `value` field in the governance entry must be JSON-compatible. The `details` dict must only contain JSON-serializable types (`str`, `int`, `float`, `bool`, `None`, `list`, `dict`). The manifest validation in `RunManifest._validate()` (manifest.py lines 230–265) enforces this. Specifically, `_validate_json_compatible()` (lines 523–552) rejects non-finite floats, bytes, and custom objects.

### UniformMergeMethod — Algorithm Detail

The uniform distribution merge is the simplest statistical matching approach:

**Algorithm:**
1. For each of the N rows in table_a, independently draw a random index from `[0, M)` where M = `table_b.num_rows`
2. Select the corresponding rows from table_b (with replacement — a single row from B can be matched to multiple rows from A)
3. Concatenate columns from table_a and the selected table_b rows — the merged table preserves column ordering: all columns from table_a appear first (in their original order), followed by all columns from table_b (after `drop_right_columns` removal)

**Statistical assumption:** Independence between all variables in table_a and table_b. This means the merge assumes no correlation between, for example, income (from INSEE) and vehicle type (from SDES). This is the weakest assumption — good as a baseline but unrealistic for correlated variables.

**When appropriate:** When merging genuinely independent surveys or when no linking variable is available.
**When problematic:** When variables are correlated (e.g., income and vehicle ownership are correlated — higher-income households are more likely to own newer, more expensive vehicles).

**Implementation pattern:**

```python
import random
import pyarrow as pa

def merge(self, table_a: pa.Table, table_b: pa.Table, config: MergeConfig) -> MergeResult:
    # Validate inputs
    if table_a.num_rows == 0:
        raise MergeValidationError(...)
    if table_b.num_rows == 0:
        raise MergeValidationError(...)

    # Drop specified right columns
    right_table = table_b
    for col in config.drop_right_columns:
        if col not in right_table.schema.names:
            raise MergeValidationError(...)
        col_idx = right_table.schema.get_field_index(col)
        right_table = right_table.remove_column(col_idx)

    # Check column conflicts
    overlap = set(table_a.schema.names) & set(right_table.schema.names)
    if overlap:
        raise MergeValidationError(...)

    # Random matching
    rng = random.Random(config.seed)
    n = table_a.num_rows
    m = right_table.num_rows
    indices = pa.array([rng.randrange(m) for _ in range(n)])
    matched_b = right_table.take(indices)

    # Combine columns
    all_columns: dict[str, pa.Array] = {}
    for name in table_a.schema.names:
        all_columns[name] = table_a.column(name)
    for name in matched_b.schema.names:
        all_columns[name] = matched_b.column(name)
    merged = pa.table(all_columns)

    # Build assumption
    assumption = MergeAssumption(
        method_name="uniform",
        statement=(
            "Each household in source A is matched to a household in "
            "source B with uniform probability \u2014 this assumes no "
            "correlation between the variables in the two sources."
        ),
        details={
            "table_a_rows": n,
            "table_b_rows": m,
            "seed": config.seed,
            "with_replacement": True,
            "dropped_right_columns": list(config.drop_right_columns),
        },
    )

    return MergeResult(table=merged, assumption=assumption)
```

### Error Hierarchy — Follow Loaders Pattern

```python
# src/reformlab/population/methods/errors.py

class MergeError(Exception):
    """Base exception for merge method operations.

    All merge exceptions use keyword-only constructor arguments
    and produce a structured ``summary - reason - fix`` message.
    """

    def __init__(self, *, summary: str, reason: str, fix: str) -> None:
        self.summary = summary
        self.reason = reason
        self.fix = fix
        super().__init__(f"{summary} - {reason} - {fix}")


class MergeValidationError(MergeError):
    """Raised when merge inputs fail validation.

    Triggered by: empty tables, column name conflicts, invalid
    drop_right_columns, or schema mismatches.
    """
```

### No New Dependencies Required

All implementation uses existing dependencies and stdlib:

- `random` — deterministic random number generation (stdlib)
- `pyarrow` — table operations, `take()` for row selection (existing dependency)
- `copy.deepcopy` — immutability for frozen dataclasses (stdlib)
- `logging` — structured logging (stdlib)

Do **not** introduce `numpy`, `scipy`, `pandas`, or any new dependency.

**Import notes:** `from copy import deepcopy` must be at module level in `base.py` (follow `manifest.py:22` pattern — stdlib, no circular dependency risk). `import pyarrow as pa` must be at module level in `uniform.py` (NOT under `if TYPE_CHECKING:`) because `pa.array()` and `pa.table()` are called at runtime. In `base.py`, `pyarrow` may use `TYPE_CHECKING` guard since `pa.Table` is annotation-only.

### Test Fixtures — Concrete Data

```python
# tests/population/methods/conftest.py

@pytest.fixture()
def income_table() -> pa.Table:
    """INSEE-style income table (5 households)."""
    return pa.table({
        "household_id": pa.array([1, 2, 3, 4, 5], type=pa.int64()),
        "income": pa.array([18000.0, 25000.0, 32000.0, 45000.0, 72000.0], type=pa.float64()),
        "region_code": pa.array(["84", "11", "84", "75", "11"], type=pa.utf8()),
    })

@pytest.fixture()
def vehicle_table() -> pa.Table:
    """SDES-style vehicle table (8 vehicles)."""
    return pa.table({
        "vehicle_type": pa.array(
            ["diesel", "essence", "ev", "diesel", "hybrid", "essence", "ev", "diesel"],
            type=pa.utf8(),
        ),
        "vehicle_age": pa.array([3, 7, 1, 12, 2, 9, 0, 15], type=pa.int64()),
        "fuel_type": pa.array(
            ["diesel", "petrol", "electric", "diesel", "hybrid", "petrol", "electric", "diesel"],
            type=pa.utf8(),
        ),
    })

@pytest.fixture()
def overlapping_table() -> pa.Table:
    """Table with column name conflicting with income_table."""
    return pa.table({
        "region_code": pa.array(["84", "11", "75"], type=pa.utf8()),
        "heating_type": pa.array(["gas", "electric", "heat_pump"], type=pa.utf8()),
    })

@pytest.fixture()
def empty_table() -> pa.Table:
    """Table with schema but zero rows."""
    return pa.table({
        "x": pa.array([], type=pa.int64()),
        "y": pa.array([], type=pa.float64()),
    })

@pytest.fixture()
def default_config() -> MergeConfig:
    """Default merge config with seed 42."""
    return MergeConfig(seed=42)
```

### Test Pattern to Follow (from loader tests)

Follow the exact test structure from `tests/population/loaders/test_insee.py`:

1. **Class-based grouping** by feature/responsibility — each test class covers a specific aspect
2. **AC references in class docstrings** — e.g., `"""AC #1, #2: Protocol compliance."""`
3. **Direct assertions** — `assert` statements, `pytest.raises(ExceptionClass, match=...)` for errors
4. **Fixtures via conftest** — injected by parameter name
5. **No test helpers** unless genuinely reusable — keep tests self-contained
6. **Frozen dataclass tests** — verify immutability with `pytest.raises(AttributeError)`

### Downstream Dependencies

Story 11.4 is consumed by:

- **Story 11.5** (IPF + conditional sampling) — adds `IPFMergeMethod` and `ConditionalSamplingMethod` implementing the same `MergeMethod` protocol, using the same `MergeConfig`, `MergeAssumption`, and `MergeResult` types
- **Story 11.6** (PopulationPipeline) — composes loaders + methods, calls `merge()` in sequence, collects `MergeAssumption` records, calls `assumption.to_governance_entry()` on each, and appends the resulting dicts directly to `RunManifest.assumptions` (type: `list[AssumptionEntry]`). Does NOT use `governance.capture.capture_assumptions()` — that function handles scalar key-value parameter assumptions, not structured merge assumption records
- **Story 11.7** (Validation) — validates merged population against marginals
- **Story 11.8** (Notebook) — demonstrates merge methods with plain-language explanations

### Project Structure Notes

**New files (9):**
- `src/reformlab/population/methods/__init__.py`
- `src/reformlab/population/methods/base.py`
- `src/reformlab/population/methods/errors.py`
- `src/reformlab/population/methods/uniform.py`
- `tests/population/methods/__init__.py`
- `tests/population/methods/conftest.py`
- `tests/population/methods/test_base.py`
- `tests/population/methods/test_uniform.py`
- `tests/population/methods/test_errors.py`

**Modified files (1):**
- `src/reformlab/population/__init__.py` — add methods exports

**No changes** to `pyproject.toml` (no new dependencies, no new markers needed)

### Alignment with Project Conventions

All rules from `project-context.md` apply:

- Every file starts with `from __future__ import annotations`
- `if TYPE_CHECKING:` guards for annotation-only imports
- Frozen dataclasses as default (`@dataclass(frozen=True)`)
- Protocols, not ABCs — `@runtime_checkable` Protocol
- Subsystem-specific exceptions (`MergeError`, not `ValueError`)
- `dict[str, Any]` for metadata bags with stable string-constant keys
- `tuple[...]` for immutable sequences in function parameters and return types
- `X | None` union syntax, not `Optional[X]`
- Module-level docstrings referencing story/FR
- `logging.getLogger(__name__)` with structured key=value format
- `# ====...====` section separators for major sections within longer modules

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#New-Subsystem-Population-Generation] — Directory structure, MergeMethod protocol specification
- [Source: _bmad-output/planning-artifacts/architecture.md#External-Data-Caching-&-Offline-Strategy] — Design principles for population subsystem
- [Source: _bmad-output/planning-artifacts/epics.md#BKL-1104] — Story definition and acceptance criteria
- [Source: _bmad-output/planning-artifacts/prd.md#FR38] — "System provides a library of statistical methods for merging datasets that do not share the same sample (uniform distribution, IPF, conditional sampling, statistical matching)"
- [Source: _bmad-output/planning-artifacts/prd.md#FR39] — "Analyst can choose which merge method to apply at each dataset join, with plain-language explanation of the assumption"
- [Source: _bmad-output/project-context.md#Python-Language-Rules] — Frozen dataclasses, Protocols, `from __future__ import annotations`
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules] — PyArrow canonical data type, no pandas in core logic
- [Source: src/reformlab/population/loaders/base.py] — DataSourceLoader Protocol pattern to follow (SourceConfig, CacheStatus frozen dataclasses, `@runtime_checkable`)
- [Source: src/reformlab/population/loaders/errors.py] — DataSourceError hierarchy pattern (summary-reason-fix)
- [Source: src/reformlab/governance/capture.py] — `capture_assumptions()` function signature and AssumptionEntry format
- [Source: src/reformlab/governance/manifest.py#AssumptionEntry] — TypedDict with key/value/source/is_default fields; JSON-compatibility validation
- [Source: tests/population/loaders/test_insee.py] — Test patterns: class-based grouping, fixture injection, direct assertions
- [Source: _bmad-output/implementation-artifacts/11-3-implement-eurostat-ademe-sdes-data-source-loaders.md] — Previous story (loaders pattern reference)

## File List

**New files (9):**
- `src/reformlab/population/methods/__init__.py`
- `src/reformlab/population/methods/base.py`
- `src/reformlab/population/methods/errors.py`
- `src/reformlab/population/methods/uniform.py`
- `tests/population/methods/__init__.py`
- `tests/population/methods/conftest.py`
- `tests/population/methods/test_base.py`
- `tests/population/methods/test_uniform.py`
- `tests/population/methods/test_errors.py`

**Modified files (1):**
- `src/reformlab/population/__init__.py` — added methods exports

## Dev Agent Record

### Implementation Plan

Implemented all 7 tasks following the story spec exactly:

1. Created `methods/` package with `__init__.py` (FR38/FR39 docstring) and `errors.py` (`MergeError` hierarchy with summary-reason-fix pattern).
2. Defined `MergeConfig` (frozen, bool-rejecting seed validation, deep-copied `drop_right_columns`), `MergeAssumption` (deep-copied details, `to_governance_entry()` with key-collision prevention), `MergeResult`, and `MergeMethod` runtime-checkable Protocol in `base.py`.
3. Implemented `UniformMergeMethod` in `uniform.py` with: input validation, `drop_right_columns` removal, column conflict detection, `random.Random(seed)`-based deterministic matching with replacement, `pa.table()` column combination, structured assumption record, and structured logging.
4. Updated both `methods/__init__.py` and `population/__init__.py` with all 7 exports and `__all__`.
5. Created test infrastructure: `conftest.py` with 5 fixtures (`income_table`, `vehicle_table`, `overlapping_table`, `empty_table`, `default_config`).
6. Wrote 50 tests across 3 test files covering: frozen dataclass immutability, `__post_init__` validation, governance entry generation, protocol compliance, merge behavior, determinism, column conflicts, `drop_right_columns`, empty table rejection, assumption record content, with-replacement behavior, and pedagogical docstrings.
7. All 235 population tests pass (50 new + 185 existing), ruff clean, mypy strict clean.

### Completion Notes

- All 4 acceptance criteria satisfied
- `pyarrow` import in `base.py` uses `TYPE_CHECKING` guard (annotation-only); runtime import in `uniform.py`
- `deepcopy` imported at module level in `base.py`
- No new dependencies introduced
- All conventions from `project-context.md` followed

## Change Log

- 2026-03-03: Story created by create-story workflow — comprehensive developer context with MergeMethod protocol design, UniformMergeMethod algorithm, governance integration pattern, error hierarchy, test fixture designs, and downstream dependency mapping.
- 2026-03-03: Validation synthesis — fixed `capture_assumptions()` API reference in Downstream Dependencies, added `bool` rejection to `MergeConfig.seed` validation, fixed `to_governance_entry()` key collision risk, moved `deepcopy` import to module level, added `__all__` requirement, fixed file counts, improved AC#2 wording, documented column ordering contract and import notes.
- 2026-03-03: Implementation complete — all 7 tasks done, 50 new tests passing, 0 regressions, ruff clean, mypy strict clean.


]]></file>
<file id="173799eb" path="src/reformlab/population/__init__.py" label="SOURCE CODE"><![CDATA[

"""Realistic population generation library for ReformLab.

Provides institutional data source loaders, statistical fusion methods,
and population pipeline composition for building synthetic populations
from open data sources (INSEE, Eurostat, ADEME, SDES).

This module implements EPIC-11 (Realistic Population Generation Library).
Phase 2 introduces optional network dependencies for data downloads,
with offline-first caching semantics.

Public API
----------
DataSourceLoader : Protocol
    Interface for institutional data source loaders.
SourceConfig : dataclass
    Immutable configuration for a data source download.
CacheStatus : dataclass
    Status of a cached data source.
SourceCache : class
    Disk-based caching infrastructure for downloaded data.
CachedLoader : class
    Base class wrapping protocol + cache logic.
MergeMethod : Protocol
    Interface for statistical dataset fusion methods.
MergeConfig : dataclass
    Immutable configuration for a merge operation.
MergeAssumption : dataclass
    Structured assumption record from a merge operation.
MergeResult : dataclass
    Immutable result of a merge operation.
UniformMergeMethod : class
    Uniform random matching with replacement.
"""

from __future__ import annotations

from reformlab.population.loaders.ademe import (
    ADEME_AVAILABLE_DATASETS,
    ADEME_CATALOG,
    ADEMEDataset,
    ADEMELoader,
    get_ademe_loader,
    make_ademe_config,
)
from reformlab.population.loaders.base import (
    CachedLoader,
    CacheStatus,
    DataSourceLoader,
    SourceConfig,
)
from reformlab.population.loaders.cache import SourceCache
from reformlab.population.loaders.errors import (
    DataSourceDownloadError,
    DataSourceError,
    DataSourceOfflineError,
    DataSourceValidationError,
)
from reformlab.population.loaders.eurostat import (
    EUROSTAT_AVAILABLE_DATASETS,
    EUROSTAT_CATALOG,
    EurostatDataset,
    EurostatLoader,
    get_eurostat_loader,
    make_eurostat_config,
)
from reformlab.population.loaders.insee import (
    AVAILABLE_DATASETS,
    INSEE_AVAILABLE_DATASETS,
    INSEE_CATALOG,
    INSEEDataset,
    INSEELoader,
    get_insee_loader,
    make_insee_config,
)
from reformlab.population.loaders.sdes import (
    SDES_AVAILABLE_DATASETS,
    SDES_CATALOG,
    SDESDataset,
    SDESLoader,
    get_sdes_loader,
    make_sdes_config,
)
from reformlab.population.methods.base import (
    MergeAssumption,
    MergeConfig,
    MergeMethod,
    MergeResult,
)
from reformlab.population.methods.errors import (
    MergeError,
    MergeValidationError,
)
from reformlab.population.methods.uniform import UniformMergeMethod

__all__ = [
    "ADEME_AVAILABLE_DATASETS",
    "ADEME_CATALOG",
    "ADEMEDataset",
    "ADEMELoader",
    "AVAILABLE_DATASETS",
    "CachedLoader",
    "CacheStatus",
    "DataSourceDownloadError",
    "DataSourceError",
    "DataSourceLoader",
    "DataSourceOfflineError",
    "DataSourceValidationError",
    "EUROSTAT_AVAILABLE_DATASETS",
    "EUROSTAT_CATALOG",
    "EurostatDataset",
    "EurostatLoader",
    "INSEE_AVAILABLE_DATASETS",
    "INSEE_CATALOG",
    "INSEEDataset",
    "INSEELoader",
    "SDES_AVAILABLE_DATASETS",
    "SDES_CATALOG",
    "SDESDataset",
    "SDESLoader",
    "SourceCache",
    "SourceConfig",
    "get_ademe_loader",
    "get_eurostat_loader",
    "get_insee_loader",
    "get_sdes_loader",
    "MergeAssumption",
    "MergeConfig",
    "MergeError",
    "MergeMethod",
    "MergeResult",
    "MergeValidationError",
    "UniformMergeMethod",
    "make_ademe_config",
    "make_eurostat_config",
    "make_insee_config",
    "make_sdes_config",
]


]]></file>
<file id="f2467725" path="src/reformlab/population/methods/__init__.py" label="SOURCE CODE"><![CDATA[

"""Statistical fusion methods library for population generation.

Provides the ``MergeMethod`` protocol for dataset fusion, supporting
types (``MergeConfig``, ``MergeAssumption``, ``MergeResult``), and
concrete implementations starting with ``UniformMergeMethod``.

Implements Story 11.4 (MergeMethod protocol and uniform distribution).
References FR38 (statistical methods library) and FR39 (merge method
selection with plain-language explanations).
"""

from __future__ import annotations

from reformlab.population.methods.base import (
    MergeAssumption,
    MergeConfig,
    MergeMethod,
    MergeResult,
)
from reformlab.population.methods.errors import (
    MergeError,
    MergeValidationError,
)
from reformlab.population.methods.uniform import UniformMergeMethod

__all__ = [
    "MergeAssumption",
    "MergeConfig",
    "MergeError",
    "MergeMethod",
    "MergeResult",
    "MergeValidationError",
    "UniformMergeMethod",
]


]]></file>
<file id="63a021f4" path="src/reformlab/population/methods/base.py" label="SOURCE CODE"><![CDATA[

"""MergeMethod protocol and supporting types for statistical dataset fusion.

Defines the structural interface that all merge methods must satisfy,
plus immutable value objects for configuration, assumption records,
and merge results.

Implements Story 11.4 (MergeMethod protocol and uniform distribution).
References FR38 (statistical methods library).
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    import pyarrow as pa


# ====================================================================
# Configuration
# ====================================================================


@dataclass(frozen=True)
class MergeConfig:
    """Immutable configuration for a merge operation.

    Attributes:
        seed: Random seed for deterministic merge operations. Must be >= 0.
        description: Optional human-readable description for governance.
        drop_right_columns: Column names to remove from table_b before
            merging. Use this to remove shared key columns (e.g.,
            ``"region_code"``) that exist in both tables but should only
            appear once in the result.
    """

    seed: int
    description: str = ""
    drop_right_columns: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            msg = f"seed must be a non-negative integer, got {self.seed!r}"
            raise ValueError(msg)
        if self.seed < 0:
            msg = f"seed must be a non-negative integer, got {self.seed!r}"
            raise ValueError(msg)
        # Deep-copy mutable-origin field to prevent aliasing
        object.__setattr__(
            self, "drop_right_columns", tuple(self.drop_right_columns)
        )


# ====================================================================
# Assumption record
# ====================================================================


@dataclass(frozen=True)
class MergeAssumption:
    """Structured assumption record from a merge operation.

    Records the method name, a plain-language assumption statement,
    and method-specific details. Can be converted to governance
    ``AssumptionEntry`` format via ``to_governance_entry()``.

    Attributes:
        method_name: Short identifier for the method (e.g., ``"uniform"``).
        statement: Plain-language description of the assumption made.
        details: Method-specific metadata. Values must be JSON-compatible
            (``str``, ``int``, ``float``, ``bool``, ``None``, ``list``,
            ``dict``). Never put ``pa.Table``, ``pa.Schema``, ``Path``,
            or custom objects in details.
    """

    method_name: str
    statement: str
    details: dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "details", deepcopy(self.details))

    def to_governance_entry(
        self, *, source_label: str = "merge_step"
    ) -> dict[str, Any]:
        """Convert to governance-compatible assumption entry.

        Returns a dict matching ``governance.manifest.AssumptionEntry``
        structure: ``key``, ``value``, ``source``, ``is_default``.

        The ``value`` field unpacks ``details`` first, then overrides
        with ``method`` and ``statement`` keys to prevent collision.
        """
        return {
            "key": f"merge_{self.method_name}",
            "value": {
                **self.details,
                "method": self.method_name,
                "statement": self.statement,
            },
            "source": source_label,
            "is_default": False,
        }


# ====================================================================
# Merge result
# ====================================================================


@dataclass(frozen=True)
class MergeResult:
    """Immutable result of a merge operation.

    Attributes:
        table: The merged PyArrow table.
        assumption: Structured assumption record documenting the merge.
    """

    table: pa.Table
    assumption: MergeAssumption


# ====================================================================
# MergeMethod protocol
# ====================================================================


@runtime_checkable
class MergeMethod(Protocol):
    """Interface for statistical dataset fusion methods.

    Structural (duck-typed) protocol: any class that implements
    ``merge()`` and the ``name`` property with the correct signatures
    satisfies the contract — no explicit inheritance required.

    Each method merges two ``pa.Table`` objects using a specific
    statistical approach, returning the merged table and an assumption
    record documenting the methodological choice.
    """

    @property
    def name(self) -> str:
        """Short identifier for this method (e.g., ``"uniform"``, ``"ipf"``)."""
        ...

    def merge(
        self,
        table_a: pa.Table,
        table_b: pa.Table,
        config: MergeConfig,
    ) -> MergeResult:
        """Merge two tables using this method's statistical approach."""
        ...


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


]]></file>
<file id="1d910d88" path="[Validator A]" label="VALIDATION OUTPUT"><![CDATA[

**🔥 ADVERSARIAL CODE REVIEW COMPLETE, Lucas!**

**Story:** /Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/11-4-define-mergemethod-protocol-and-uniform-distribution-method.md

---

## 📊 Review Summary

| Category | Issues Found |
|----------|--------------|
| Git vs Story Discrepancies | 1 |
| AC Implementation Gaps | 0 |
| Task Completion Lies | 0 |
| SOLID Violations | 0 |
| Hidden Bugs | 1 |
| Performance Footguns | 1 |
| Security Vulnerabilities | 0 |
| **Total Issues** | **6** |

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🔴 CRITICAL | Duplicate column names in either input silently overwrite data because merging builds a dict without detecting duplicates; violates “data contracts fail loudly”. | src/reformlab/population/methods/uniform.py:118 | +3 |
| 🟠 IMPORTANT | Merge generates one Python `randrange` per row (list of indices) – O(n) Python overhead; will drag when merging 100k+ households, conflicting with performance budget noted in architecture. | src/reformlab/population/methods/uniform.py:94 | +1 |
| 🟠 IMPORTANT | Probabilistic test `test_different_seed_different_result` can intermittently fail (P≈0.003%) because two different seeds can coincidentally pick the same sequence; flake risk in CI. | tests/population/methods/test_uniform.py:78 | +1 |
| 🟠 IMPORTANT | `MergeConfig` accepts non‑string entries in `drop_right_columns`; later lookup uses string membership and will raise or misbehave at runtime instead of failing fast. | src/reformlab/population/methods/base.py:33 | +1 |
| 🟡 MINOR | `MergeAssumption` never validates JSON‑compatibility of `details`; invalid values leak to manifest validation instead of failing at creation (violates “data contracts fail loudly”). | src/reformlab/population/methods/base.py:57 | +0.3 |
| 🟠 IMPORTANT | Large set of loader/cache files modified in git diff but absent from story File List; scope creep not documented to reviewers/users. | repo git diff (loaders/*, cache.py, etc.) | +1 |
| 🟢 CLEAN PASS | 4 categories with no findings (SOLID, Abstraction, Style, Security) |  | -2.0 |

### Evidence Score: 5.3

| Score | Verdict |
|-------|---------|
| **5.3** | **MAJOR REWORK** |

---

## 🏛️ Architectural Sins

✅ No significant architectural violations detected.

---

## 🐍 Pythonic Crimes & Readability

✅ Code follows style guidelines and is readable.

---

## ⚡ Performance & Scalability

- **[High] Hot-path Python loop:** Uniform merge builds indices with a Python list comprehension and per-row RNG; for population-scale merges this adds tens of milliseconds to seconds and scales poorly.  
  - 📍 `src/reformlab/population/methods/uniform.py:94`  
  - 💡 Fix: use a vectorized generator (e.g., `numpy.random.Generator(seed).integers(m, size=n)` or PyArrow compute) to produce indices and feed directly to `take()`.

---

## 🐛 Correctness & Safety

- **🐛 Silent data loss:** If either table contains duplicate column names, the dict-based column assembly overwrites earlier columns without warning, breaking the “fail loudly” rule and corrupting data.  
  - 📍 `src/reformlab/population/methods/uniform.py:118`  
  - 🔄 Reproduction: create `table_a` with two columns named `"x"`; merged output keeps only the last `"x"`.

- **🎭 Lying Test:** `test_different_seed_different_result` fails randomly with probability ~0.003% because different seeds can produce identical 5 draws; non-deterministic CI flakes.  
  - 📍 `tests/population/methods/test_uniform.py:78`  
  - 🤥 Why it lies: asserts inequality of two random sequences instead of comparing against expected indices.

---

## 🔧 Maintainability Issues

- **💣 Tech Debt:** `MergeAssumption.details` accepts any objects; JSON incompatibilities only surface later when building manifests, making failure location opaque.  
  - 📍 `src/reformlab/population/methods/base.py:57`  
  - 💥 Explosion radius: manifest validation failures far from merge call site.

---

## 🛠️ Suggested Fixes

### 1. Guard against duplicate column names
**File:** `src/reformlab/population/methods/uniform.py`
**Issue:** Duplicate column names in either input overwrite silently.

**Diff:**
```diff
@@
-        # Combine columns: table_a first, then matched table_b
-        all_columns: dict[str, pa.Array] = {}
-        for col_name in table_a.schema.names:
-            all_columns[col_name] = table_a.column(col_name)
-        for col_name in matched_b.schema.names:
-            all_columns[col_name] = matched_b.column(col_name)
-        merged = pa.table(all_columns)
+        # Combine columns: table_a first, then matched table_b
+        all_columns: dict[str, pa.Array] = {}
+        for col_name in table_a.schema.names:
+            if col_name in all_columns:
+                raise MergeValidationError(
+                    summary="Duplicate column in left table",
+                    reason=f"column '{col_name}' appears multiple times in table_a",
+                    fix="Ensure column names are unique before merging",
+                )
+            all_columns[col_name] = table_a.column(col_name)
+        for col_name in matched_b.schema.names:
+            if col_name in all_columns:
+                raise MergeValidationError(
+                    summary="Duplicate column after merge",
+                    reason=f"column '{col_name}' appears in both tables or duplicates",
+                    fix="Rename or drop duplicates before merging",
+                )
+            all_columns[col_name] = matched_b.column(col_name)
+        merged = pa.table(all_columns)
```

### 2. Vectorize index generation
**File:** `src/reformlab/population/methods/uniform.py`
**Issue:** Python loop for indices is slow for large tables.

**Diff:**
```diff
@@
-        rng = random.Random(config.seed)
-        n = table_a.num_rows
-        m = right_table.num_rows
-        indices = pa.array([rng.randrange(m) for _ in range(n)])
+        import numpy as _np
+
+        rng = _np.random.default_rng(config.seed)
+        n = table_a.num_rows
+        m = right_table.num_rows
+        indices = pa.array(rng.integers(0, m, size=n, endpoint=False))
```

### 3. Make differing-seed test deterministic
**File:** `tests/population/methods/test_uniform.py`
**Issue:** Probabilistic inequality assertion flakes.

**Diff:**
```diff
@@
     def test_different_seed_different_result(
         self,
         income_table: pa.Table,
         vehicle_table: pa.Table,
     ) -> None:
         method = UniformMergeMethod()
-        result_1 = method.merge(
-            income_table, vehicle_table, MergeConfig(seed=1)
-        )
-        result_2 = method.merge(
-            income_table, vehicle_table, MergeConfig(seed=2)
-        )
-        # With 5 rows drawn from 8 options, P(identical) is (1/8)^5 ≈ 0.003%
-        rows_1 = result_1.table.to_pydict()
-        rows_2 = result_2.table.to_pydict()
-        assert rows_1 != rows_2
+        result_1 = method.merge(
+            income_table, vehicle_table, MergeConfig(seed=1)
+        )
+        result_2 = method.merge(
+            income_table, vehicle_table, MergeConfig(seed=2)
+        )
+        assert result_1.table.column("vehicle_type").to_pylist() == [
+            "hybrid", "diesel", "ev", "essence", "diesel"
+        ]
+        assert result_2.table.column("vehicle_type").to_pylist() == [
+            "diesel", "diesel", "diesel", "hybrid", "diesel"
+        ]
```

]]></file>
<file id="557aedd2" path="[Validator B]" label="VALIDATION OUTPUT"><![CDATA[

**🔥 ADVERSARIAL CODE REVIEW COMPLETE, Lucas!**

**Story:** `_bmad-output/implementation-artifacts/11-4-define-mergemethod-protocol-and-uniform-distribution-method.md`

---

## 📊 Review Summary

| Category | Issues Found |
|----------|--------------|
| Git vs Story Discrepancies | 0 |
| AC Implementation Gaps | 0 |
| Task Completion Lies | 0 |
| Lying / Weak Tests | 2 |
| Type Annotation Bugs | 1 |
| Forward Compatibility | 1 |
| Convention Violations | 1 |
| Observability Gaps | 1 |
| Minor Correctness | 1 |
| **Total Issues** | **7** |

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🟠 IMPORTANT | Lying test — `test_table_b_values_from_actual_rows` doesn't verify row coherence | `test_uniform.py:98` | +1 |
| 🟠 IMPORTANT | Wrong type annotation `dict[str, pa.Array]`; `column()` returns `ChunkedArray` | `uniform.py:168` | +1 |
| 🟠 IMPORTANT | `to_governance_entry()` returns `dict[str, Any]`, will break mypy in Story 11.6 | `base.py:87` | +1 |
| 🟡 MINOR | Missing `from __future__ import annotations` — project says "no exceptions" | `tests/population/methods/__init__.py:1` | +0.3 |
| 🟡 MINOR | No `event=merge_error` log on validation failure; only success path is instrumented | `uniform.py:109` | +0.3 |
| 🟡 MINOR | Math comment `P(identical) is (1/8)^5` is statistically wrong for PRNG sequences | `test_uniform.py:143` | +0.3 |
| 🟡 MINOR | "Deep-copy mutable-origin field" comment is misleading — this is a type coercion | `base.py:50` | +0.3 |
| 🟢 CLEAN PASS | Security — no vulnerabilities, no injection surfaces, no credential exposure | — | -0.5 |
| 🟢 CLEAN PASS | Hidden bugs — no resource leaks, no race conditions, no off-by-ones | — | -0.5 |
| 🟢 CLEAN PASS | SOLID violations — protocol pattern correctly applied, SRP respected throughout | — | -0.5 |

### Evidence Score: **2.7**

| Score | Verdict |
|-------|---------|
| **2.7** | **✅ APPROVED** (borderline — 3 IMPORTANT findings warrant attention before Story 11.6 hits) |

---

## 🏛️ Architectural Sins

✅ No significant SOLID violations or architectural boundary breaches. Protocol-not-ABC rule followed, frozen dataclasses used throughout, no OpenFisca boundary violations, governance integration documented correctly.

---

## 🐍 Pythonic Crimes & Readability

**Type Annotation Error — `dict[str, pa.Array]`:**

`pa.Table.column()` returns `pa.ChunkedArray` (a collection of `pa.Array` chunks), not a contiguous `pa.Array`. These are different types in PyArrow's hierarchy — `ChunkedArray` is not a subtype of `Array`. The annotation is wrong.

- 📍 `src/reformlab/population/methods/uniform.py:168`

The annotation was copied verbatim from the story's dev notes, which also contains this error. A senior developer should have caught it. Because the project sets `ignore_missing_imports` for pyarrow in mypy config, this silently passes type checking — mypy treats `pa.Array` and `pa.ChunkedArray` as `Any`. Runtime behavior is correct since `pa.table()` accepts both, but the annotation misleads future readers and contributors.

**Misleading `__post_init__` comment:**

`# Deep-copy mutable-origin field to prevent aliasing` at `base.py:50` describes `tuple(self.drop_right_columns)`. This is a type coercion (list → tuple), not a deep copy. Strings inside are immutable, so no deep copy is needed — but the comment implies a deeper operation than what occurs. For future methods where `drop_right_columns` could contain non-strings, this comment is actively dangerous guidance.

- 📍 `src/reformlab/population/methods/base.py:50`

**Missing `from __future__ import annotations`:**

Project context says **"no exceptions."** `tests/population/methods/__init__.py` has only a docstring and no `from __future__ import annotations`. Every sibling file has it. This is a convention violation.

- 📍 `tests/population/methods/__init__.py:1`

---

## ⚡ Performance & Scalability

✅ No significant performance footguns. The `rng.randrange(m)` list comprehension creating a Python list of N integers before passing to `pa.array()` is the only allocation concern, and it's the correct approach given the `numpy` prohibition. For the documented 100K household use case, this is ~2.8MB temporary allocation — acceptable.

---

## 🐛 Correctness & Safety

**🎭 Lying Test — `test_table_b_values_from_actual_rows`:**

- 📍 `tests/population/methods/test_uniform.py:98-109`
- 🤥 Why it lies: The test only checks that `vehicle_type` values come from the valid set of type strings. It does NOT verify that matched columns form a coherent row from `vehicle_table`. An implementation that shuffled each right-table column **independently** (breaking row integrity entirely) would still pass this test, because each column's values would still come from the valid pool.

  The story spec requirement is: *"matched values come from actual rows in table_b (not fabricated)"*. The actual invariant being tested should be: every row in the merged result, when projected onto right-table columns, must correspond to a single row that existed in `table_b`. The current test verifies something strictly weaker.

  The implementation is correct (`right_table.take(indices)` selects whole rows), but the test provides no confidence in that correctness. A future refactor breaking row integrity would go undetected.

**🎭 Weak Test — `test_different_seed_different_result` comment:**

- 📍 `tests/population/methods/test_uniform.py:143`
- 🤥 Why it lies: The comment `# With 5 rows drawn from 8 options, P(identical) is (1/8)^5 ≈ 0.003%` applies the wrong probability model. It would be correct for a single random draw from a uniform distribution. For two deterministic PRNG sequences with fixed seeds 1 and 2, the outcome is **not probabilistic** — it is deterministic. The test either always passes or always fails for those seeds. The comment misleads maintainers into thinking there is flakiness risk, which could cause someone to skip the test or add unnecessary retries.

  The deeper issue: the comparison is `result_1.table.to_pydict() != result_2.table.to_pydict()`. Since `income_table` columns are always identical in both results, the test is sensitive only to the vehicle columns — but a reader can't tell this without digging. Comparing only the right-table columns would make intent explicit.

**⚠️ Forward Type Incompatibility — `to_governance_entry()` return type:**

- 📍 `src/reformlab/population/methods/base.py:87`

`to_governance_entry()` is annotated as `-> dict[str, Any]`. The story spec explicitly calls out that Story 11.6 will do:
> *"appends the resulting dicts directly to `RunManifest.assumptions` (type: `list[AssumptionEntry]`)"*

`RunManifest.assumptions` is `list[AssumptionEntry]`. In mypy strict mode, calling `manifest.assumptions.append(assumption.to_governance_entry())` will fail:

```
Argument 1 to "append" of "list" has incompatible type "Dict[str, Any]"; expected "AssumptionEntry"
```

`dict[str, Any]` is NOT a mypy subtype of `AssumptionEntry` TypedDict. The story notes this as a known design decision but provides no guidance on the required `cast()` in 11.6 — no comment, no TODO, no type alias. Story 11.6 will hit a mypy strict failure on the first line that touches this.

The correct fix (since cross-subsystem import of `AssumptionEntry` into the population module would be an architectural smell) is to document the required `cast` in the governance entry. The story author should have surfaced this in the dev notes.

---

## 🔧 Maintainability Issues

**💣 Missing error observability in structured logging:**

- 📍 `src/reformlab/population/methods/uniform.py:109-114`
- 💥 Explosion radius: When a `MergeValidationError` fires (empty table, column conflict, invalid drop), the log record shows `event=merge_start` with no subsequent event. Log pipelines parsing for `event=merge_complete` to build success metrics will silently undercount failures. `event=merge_start` without `event=merge_complete` is ambiguous — it could mean a crash, a timeout, or a validation error. The project's structured logging convention exists precisely for parseable operational diagnostics.

---

## 🛠️ Suggested Fixes

### 1. Fix the lying `test_table_b_values_from_actual_rows` — verify row coherence

**File:** `tests/population/methods/test_uniform.py`
**Issue:** Test name claims "from actual rows" but only checks one column; doesn't verify row-level integrity.

```diff
     def test_table_b_values_from_actual_rows(
         self,
         income_table: pa.Table,
         vehicle_table: pa.Table,
         default_config: MergeConfig,
     ) -> None:
         method = UniformMergeMethod()
         result = method.merge(income_table, vehicle_table, default_config)
-        valid_types = set(vehicle_table.column("vehicle_type").to_pylist())
-        merged_types = result.table.column("vehicle_type").to_pylist()
-        for val in merged_types:
-            assert val in valid_types
+        # Verify row-level coherence: every matched combination must exist in vehicle_table
+        valid_row_combos = set(
+            zip(
+                vehicle_table.column("vehicle_type").to_pylist(),
+                vehicle_table.column("vehicle_age").to_pylist(),
+                vehicle_table.column("fuel_type").to_pylist(),
+            )
+        )
+        for i in range(result.table.num_rows):
+            combo = (
+                result.table.column("vehicle_type")[i].as_py(),
+                result.table.column("vehicle_age")[i].as_py(),
+                result.table.column("fuel_type")[i].as_py(),
+            )
+            assert combo in valid_row_combos, (
+                f"Row {i} {combo!r} is not a row from vehicle_table — "
+                "merge is not preserving row-level coherence"
+            )
```

### 2. Fix wrong type annotation `dict[str, pa.Array]`

**File:** `src/reformlab/population/methods/uniform.py`
**Issue:** `pa.Table.column()` returns `pa.ChunkedArray`, not `pa.Array`.

```diff
-        all_columns: dict[str, pa.Array] = {}
+        all_columns: dict[str, pa.ChunkedArray] = {}
```

### 3. Add `from __future__ import annotations`

**File:** `tests/population/methods/__init__.py`

```diff
 """Tests for the statistical fusion methods library."""
+
+from __future__ import annotations
```

### 4. Add error logging on validation failure

**File:** `src/reformlab/population/methods/uniform.py`

```diff
         if table_a.num_rows == 0:
+            _logger.warning(
+                "event=merge_error method=uniform error=empty_table_a",
+            )
             raise MergeValidationError(
                 summary="Empty left table",
```

```diff
         if table_b.num_rows == 0:
+            _logger.warning(
+                "event=merge_error method=uniform error=empty_table_b",
+            )
             raise MergeValidationError(
                 summary="Empty right table",
```

(Same pattern for the column conflict and invalid drop_right_columns cases.)

### 5. Document Story 11.6 cast requirement for `to_governance_entry()`

**File:** `src/reformlab/population/methods/base.py`
**Issue:** The return type `dict[str, Any]` will cause a mypy strict failure in Story 11.6 when appending to `RunManifest.assumptions: list[AssumptionEntry]`.

```diff
     def to_governance_entry(
         self, *, source_label: str = "merge_step"
     ) -> dict[str, Any]:
         """Convert to governance-compatible assumption entry.
 
         Returns a dict matching ``governance.manifest.AssumptionEntry``
-        structure: ``key``, ``value``, ``source``, ``is_default``.
+        structure: ``key``, ``value``, ``source``, ``is_default``.
+
+        Note for Story 11.6: When appending to ``RunManifest.assumptions``
+        (typed ``list[AssumptionEntry]``), mypy strict requires an explicit
+        cast:
+
+            from typing import cast
+            from reformlab.governance.manifest import AssumptionEntry
+            entry = cast(AssumptionEntry, assumption.to_governance_entry())
+            manifest.assumptions.append(entry)
+
+        Cross-subsystem import of ``AssumptionEntry`` into the population
+        module is intentionally avoided to prevent coupling.
         """
```

]]></file>
<file id="dc422a86" path="[git-diff]" label="VIRTUAL CONTENT"><![CDATA[

<!-- GIT_DIFF_START -->
 .../4-implementation/code-review/instructions.xml  | 413 ++++++++++++++--
 .../4-implementation/code-review/workflow.yaml     |  15 +-
 .../4-implementation/create-story/instructions.xml |   6 +-
 .../4-implementation/create-story/workflow.yaml    |  27 +-
 .../4-implementation/dev-story/instructions.xml    |   7 +-
 .../4-implementation/dev-story/workflow.yaml       |   7 +-
 .../4-implementation/retrospective/workflow.yaml   |   9 +-
 bmad-assist.yaml                                   |  45 +-
 pyproject.toml                                     |   3 +-
 src/reformlab/population/__init__.py               | 137 ++++++
 src/reformlab/population/loaders/__init__.py       |  96 ++++
 src/reformlab/population/loaders/ademe.py          | 328 +++++++++++++
 src/reformlab/population/loaders/base.py           | 296 +++++++++++
 src/reformlab/population/loaders/cache.py          | 300 ++++++++++++
 src/reformlab/population/loaders/errors.py         |  47 ++
 src/reformlab/population/loaders/eurostat.py       | 327 +++++++++++++
 src/reformlab/population/loaders/insee.py          | 454 +++++++++++++++++
 src/reformlab/population/loaders/sdes.py           | 292 +++++++++++
 src/reformlab/population/methods/__init__.py       |  34 ++
 src/reformlab/population/methods/base.py           | 156 ++++++
 src/reformlab/population/methods/errors.py         |  31 ++
 src/reformlab/population/methods/uniform.py        | 198 ++++++++
 tests/fixtures/ademe/base_carbone.csv              |   5 +
 tests/fixtures/eurostat/ilc_di01.csv               |   6 +
 tests/fixtures/eurostat/nrg_d_hhq.csv              |   6 +
 tests/fixtures/insee/filosofi_2021_commune.csv     |   6 +
 .../fixtures/insee/filosofi_2021_iris_declared.csv |   4 +
 .../insee/filosofi_2021_iris_disposable.csv        |   4 +
 tests/fixtures/sdes/vehicle_fleet.csv              |   6 +
 tests/governance/test_memory.py                    |   4 +-
 tests/population/__init__.py                       |   1 +
 tests/population/conftest.py                       |  42 ++
 tests/population/loaders/__init__.py               |   1 +
 tests/population/loaders/conftest.py               | 163 ++++++
 tests/population/loaders/test_ademe.py             | 351 +++++++++++++
 tests/population/loaders/test_ademe_network.py     |  38 ++
 tests/population/loaders/test_base.py              | 220 +++++++++
 tests/population/loaders/test_cache.py             | 393 +++++++++++++++
 tests/population/loaders/test_cached_loader.py     | 311 ++++++++++++
 tests/population/loaders/test_errors.py            |  62 +++
 tests/population/loaders/test_eurostat.py          | 460 +++++++++++++++++
 tests/population/loaders/test_eurostat_network.py  |  48 ++
 tests/population/loaders/test_insee.py             | 545 +++++++++++++++++++++
 tests/population/loaders/test_insee_network.py     |  35 ++
 tests/population/loaders/test_sdes.py              | 385 +++++++++++++++
 tests/population/loaders/test_sdes_network.py      |  38 ++
 tests/population/methods/__init__.py               |   1 +
 tests/population/methods/conftest.py               |  97 ++++
 tests/population/methods/test_base.py              | 188 +++++++
 tests/population/methods/test_errors.py            |  63 +++
 tests/population/methods/test_uniform.py           | 357 ++++++++++++++
 51 files changed, 6976 insertions(+), 92 deletions(-)

diff --git a/src/reformlab/population/__init__.py b/src/reformlab/population/__init__.py
new file mode 100644
index 0000000..0a840eb
--- /dev/null
+++ b/src/reformlab/population/__init__.py
@@ -0,0 +1,137 @@
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
+"""
+
+from __future__ import annotations
+
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
+    MergeAssumption,
+    MergeConfig,
+    MergeMethod,
+    MergeResult,
+)
+from reformlab.population.methods.errors import (
+    MergeError,
+    MergeValidationError,
+)
+from reformlab.population.methods.uniform import UniformMergeMethod
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
+    "get_ademe_loader",
+    "get_eurostat_loader",
+    "get_insee_loader",
+    "get_sdes_loader",
+    "MergeAssumption",
+    "MergeConfig",
+    "MergeError",
+    "MergeMethod",
+    "MergeResult",
+    "MergeValidationError",
+    "UniformMergeMethod",
+    "make_ademe_config",
+    "make_eurostat_config",
+    "make_insee_config",
+    "make_sdes_config",
+]
diff --git a/src/reformlab/population/loaders/__init__.py b/src/reformlab/population/loaders/__init__.py
new file mode 100644
index 0000000..0660cdc
--- /dev/null
+++ b/src/reformlab/population/loaders/__init__.py
@@ -0,0 +1,96 @@
+"""Institutional data source loaders with disk-based caching.
+
+Provides the ``DataSourceLoader`` protocol, ``SourceCache`` for
+offline-first caching, and ``CachedLoader`` base class for building
+concrete loaders (INSEE, Eurostat, ADEME, SDES).
+
+Implements Story 11.1 (DataSourceLoader protocol and caching infrastructure).
+Implements Story 11.2 (INSEE data source loader).
+Implements Story 11.3 (Eurostat, ADEME, SDES data source loaders).
+"""
+
+from __future__ import annotations
+
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
+    "get_ademe_loader",
+    "get_eurostat_loader",
+    "get_insee_loader",
+    "get_sdes_loader",
+    "make_ademe_config",
+    "make_eurostat_config",
+    "make_insee_config",
+    "make_sdes_config",
+]
diff --git a/src/reformlab/population/loaders/ademe.py b/src/reformlab/population/loaders/ademe.py
new file mode 100644
index 0000000..1420edb
--- /dev/null
+++ b/src/reformlab/population/loaders/ademe.py
@@ -0,0 +1,328 @@
+"""ADEME institutional data source loader.
+
+Downloads, caches, and schema-validates ADEME Base Carbone emission factor
+datasets. Concrete implementation of the ``DataSourceLoader`` protocol via
+``CachedLoader``.
+
+Handles Windows-1252 encoding (primary) with UTF-8 fallback, semicolon
+separator, and French-language column names with accents.
+
+Implements Story 11.3 (Implement Eurostat, ADEME, SDES data source loaders).
+References: FR36 (download and cache public datasets), FR37 (browse
+available datasets).
+"""
+
+from __future__ import annotations
+
+import http.client
+import io
+import logging
+import urllib.error
+import urllib.request
+from dataclasses import dataclass
+from typing import TYPE_CHECKING
+
+import pyarrow as pa
+import pyarrow.csv as pcsv
+
+from reformlab.population.loaders.base import CachedLoader, SourceConfig
+from reformlab.population.loaders.errors import DataSourceValidationError
+
+if TYPE_CHECKING:
+    from reformlab.population.loaders.cache import SourceCache
+
+
+# ====================================================================
+# ADEME dataset metadata
+# ====================================================================
+
+
+@dataclass(frozen=True)
+class ADEMEDataset:
+    """Metadata for a known ADEME dataset.
+
+    The ``columns`` field defines the raw-to-project column rename mapping.
+    Each inner tuple is ``(raw_column_name, project_column_name)``.
+    """
+
+    dataset_id: str
+    description: str
+    url: str
+    encoding: str = "windows-1252"
+    separator: str = ";"
+    null_markers: tuple[str, ...] = ("",)
+    columns: tuple[tuple[str, str], ...] = ()
+
+
+# ====================================================================
+# Dataset catalog
+# ====================================================================
+
+_BASE_CARBONE_COLUMNS: tuple[tuple[str, str], ...] = (
+    ("Identifiant de l'\xe9l\xe9ment", "element_id"),
+    ("Nom base fran\xe7ais", "name_fr"),
+    ("Nom attribut fran\xe7ais", "attribute_name_fr"),
+    ("Type Ligne", "line_type"),
+    ("Unit\xe9 fran\xe7ais", "unit_fr"),
+    ("Total poste non d\xe9compos\xe9", "total_co2e"),
+    ("CO2f", "co2_fossil"),
+    ("CH4f", "ch4_fossil"),
+    ("CH4b", "ch4_biogenic"),
+    ("N2O", "n2o"),
+    ("CO2b", "co2_biogenic"),
+    ("Autre GES", "other_ghg"),
+    ("Localisation g\xe9ographique", "geography"),
+    ("Sous-localisation g\xe9ographique fran\xe7ais", "sub_geography"),
+    ("Contributeur", "contributor"),
+)
+
+ADEME_CATALOG: dict[str, ADEMEDataset] = {
+    "base_carbone": ADEMEDataset(
+        dataset_id="base_carbone",
+        description="Base Carbone V23.6 emission factors (CSV from data.gouv.fr)",
+        url="https://www.data.gouv.fr/api/1/datasets/r/ac6a3044-459c-4520-b85a-7e1740f7cd1f",
+        columns=_BASE_CARBONE_COLUMNS,
+    ),
+}
+
+ADEME_AVAILABLE_DATASETS: tuple[str, ...] = tuple(sorted(ADEME_CATALOG.keys()))
+"""Available ADEME dataset identifiers for discovery."""
+
+
+# ====================================================================
+# Per-dataset PyArrow schemas
+# ====================================================================
+
+
+def _base_carbone_schema() -> pa.Schema:
+    return pa.schema([
+        pa.field("element_id", pa.int64()),
+        pa.field("name_fr", pa.utf8()),
+        pa.field("attribute_name_fr", pa.utf8()),
+        pa.field("line_type", pa.utf8()),
+        pa.field("unit_fr", pa.utf8()),
+        pa.field("total_co2e", pa.float64()),
+        pa.field("co2_fossil", pa.float64()),
+        pa.field("ch4_fossil", pa.float64()),
+        pa.field("ch4_biogenic", pa.float64()),
+        pa.field("n2o", pa.float64()),
+        pa.field("co2_biogenic", pa.float64()),
+        pa.field("other_ghg", pa.float64()),
+        pa.field("geography", pa.utf8()),
+        pa.field("sub_geography", pa.utf8()),
+        pa.field("contributor", pa.utf8()),
+    ])
+
+
+_DATASET_SCHEMAS: dict[str, pa.Schema] = {
+    "base_carbone": _base_carbone_schema(),
+}
+
+
+# ====================================================================
+# ADEMELoader
+# ====================================================================
+
+_NETWORK_ERRORS: tuple[type[Exception], ...] = (
+    urllib.error.URLError,
+    OSError,
+    http.client.HTTPException,
+)
+
+_HTTP_TIMEOUT_SECONDS = 300
+"""Timeout for ADEME HTTP downloads (5 minutes)."""
+
+
+class ADEMELoader(CachedLoader):
+    """Concrete loader for ADEME institutional data sources.
+
+    Extends ``CachedLoader`` with ADEME-specific CSV parsing, Windows-1252
+    encoding (primary) with UTF-8 fallback, semicolon separator, and
+    French-language column names.
+
+    Each loader instance handles one ``ADEMEDataset``. Use
+    ``get_ademe_loader`` factory to construct from a catalog dataset ID.
+    """
+
+    def __init__(
+        self,
+        *,
+        cache: SourceCache,
+        logger: logging.Logger,
+        dataset: ADEMEDataset,
+    ) -> None:
+        self._dataset = dataset
+        super().__init__(cache=cache, logger=logger)
+
+    def schema(self) -> pa.Schema:
+        """Return the expected PyArrow schema for this loader's dataset."""
+        return _DATASET_SCHEMAS[self._dataset.dataset_id]
+
+    def _fetch(self, config: SourceConfig) -> pa.Table:
+        """Download and parse an ADEME dataset from its URL.
+
+        Handles Windows-1252 encoding with UTF-8 fallback and semicolon
+        separator. Re-raises all network errors as ``OSError`` so
+        ``CachedLoader.download()`` can handle stale-cache fallback.
+        """
+        self._logger.debug(
+            "event=fetch_start provider=ademe dataset_id=%s url=%s",
+            self._dataset.dataset_id,
+            config.url,
+        )
+
+        try:
+            with urllib.request.urlopen(config.url, timeout=_HTTP_TIMEOUT_SECONDS) as response:  # noqa: S310
+                raw_bytes = response.read()
+        except _NETWORK_ERRORS as exc:
+            raise OSError(
+                f"Failed to download ademe/{self._dataset.dataset_id} "
+                f"from {config.url}: {exc}"
+            ) from exc
+
+        table = self._parse_csv(raw_bytes)
+
+        self._logger.debug(
+            "event=fetch_complete provider=ademe dataset_id=%s rows=%d columns=%d",
+            self._dataset.dataset_id,
+            table.num_rows,
+            table.num_columns,
+        )
+        return table
+
+    def _parse_csv(self, csv_bytes: bytes) -> pa.Table:
+        """Parse CSV bytes into a pa.Table with schema enforcement.
+
+        Tries Windows-1252 first, falls back to UTF-8 on decode error.
+        """
+        ds = self._dataset
+        raw_names = [col[0] for col in ds.columns]
+        project_names = [col[1] for col in ds.columns]
+        expected_schema = self.schema()
+
+        # Build column_types mapping using RAW column names
+        column_types: dict[str, pa.DataType] = {}
+        for raw_name, proj_name in ds.columns:
+            column_types[raw_name] = expected_schema.field(proj_name).type
+
+        convert_options = pcsv.ConvertOptions(
+            null_values=list(ds.null_markers),
+            column_types=column_types,
+            include_columns=raw_names,
+        )
+        parse_options = pcsv.ParseOptions(delimiter=ds.separator)
+
+        # Try primary encoding (Windows-1252), fallback to UTF-8 on decode error.
+        # ArrowInvalid: byte sequence invalid for the encoding.
+        # ArrowKeyError: decoding succeeded but column names are garbled
+        # (UTF-8 multi-byte chars decoded as Windows-1252 produce different names).
+        read_options = pcsv.ReadOptions(encoding=ds.encoding)
+        try:
+            table = pcsv.read_csv(
+                io.BytesIO(csv_bytes),
+                read_options=read_options,
+                parse_options=parse_options,
+                convert_options=convert_options,
+            )
+        except (pa.ArrowInvalid, pa.lib.ArrowKeyError):
+            self._logger.debug(
+                "event=encoding_fallback provider=ademe dataset_id=%s "
+                "primary=%s fallback=utf-8",
+                ds.dataset_id,
+                ds.encoding,
+            )
+            fallback_options = pcsv.ReadOptions(encoding="utf-8")
+            try:
+                table = pcsv.read_csv(
+                    io.BytesIO(csv_bytes),
+                    read_options=fallback_options,
+                    parse_options=parse_options,
+                    convert_options=convert_options,
+                )
+            except (pa.ArrowInvalid, pa.lib.ArrowKeyError) as exc2:
+                raise DataSourceValidationError(
+                    summary="CSV parsing failed",
+                    reason=f"ademe/{ds.dataset_id} could not be decoded as "
+                    f"{ds.encoding} or utf-8: {exc2}",
+                    fix="Check the ADEME source URL — the file encoding "
+                    "may have changed",
+                ) from exc2
+
+        # Rename columns from raw French names to project names
+        table = table.rename_columns(project_names)
+        return table
+
+
+# ====================================================================
+# Factory and helper functions
+# ====================================================================
+
+
+def get_ademe_loader(
+    dataset_id: str,
+    *,
+    cache: SourceCache,
+    logger: logging.Logger | None = None,
+) -> ADEMELoader:
+    """Factory: construct an ``ADEMELoader`` from a catalog dataset ID.
+
+    Parameters
+    ----------
+    dataset_id : str

[... Git diff truncated due to size - see full diff with git command ...]

]]></file>
</context>
<variables>
<var name="author">BMad</var>
<var name="communication_language">English</var>
<var name="date">2026-03-03</var>
<var name="description">Master synthesizes code review findings and applies fixes to source code</var>
<var name="document_output_language">English</var>
<var name="epic_num">11</var>
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
<var name="session_id">646513d7-7b98-494d-b576-88eae79de27d</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_file" file_id="6870c5a9">embedded in prompt, file id: 6870c5a9</var>
<var name="story_id">11.4</var>
<var name="story_key">11-4-define-mergemethod-protocol-and-uniform-distribution-method</var>
<var name="story_num">4</var>
<var name="story_title">define-mergemethod-protocol-and-uniform-distribution-method</var>
<var name="template">False</var>
<var name="timestamp">20260303_1845</var>
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
      - Commit message format: fix(component): brief description (synthesis-11.4)
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

  </workflow></instructions>
<output-template></output-template>
</compiled-workflow>