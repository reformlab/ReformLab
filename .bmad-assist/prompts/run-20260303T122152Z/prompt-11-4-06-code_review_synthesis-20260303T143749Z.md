<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 11 -->
<!-- Story: 4 -->
<!-- Phase: code-review-synthesis -->
<!-- Timestamp: 20260303T143749Z -->
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

<!-- TRUNCATED: Content exceeded token budget. See full document for details. -->

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
<file id="3fa00fd6" path="src/reformlab/population/methods/uniform.py" label="SOURCE CODE"><![CDATA[

"""Uniform distribution merge method for statistical dataset fusion.

Implements the simplest statistical matching approach: each row from
table A is independently matched to a uniformly random row from table B
(with replacement). This assumes **no correlation** between the variables
in the two sources.

**Independence assumption (plain language):**

The uniform merge treats every row in table B as equally likely to be
paired with any row in table A. This is equivalent to assuming that
the variables in the two datasets are statistically independent — for
example, that a household's income (from INSEE) has no relationship
with its vehicle type (from SDES).

**When this is appropriate:**

- Merging genuinely independent surveys with no linking variable.
- As a baseline/starting point before applying more sophisticated
  methods (IPF, conditional sampling).
- When the merged variables are known to be weakly correlated.

**When this is problematic:**

- When variables are correlated — e.g., income and vehicle ownership
  are correlated (higher-income households are more likely to own
  newer, more expensive vehicles). Using uniform matching here would
  understate the correlation and distort distributional analyses.
- When the two datasets share a common variable that could be used
  as a stratification key — in that case, conditional sampling or
  statistical matching would be more appropriate.

Implements Story 11.4 (MergeMethod protocol and uniform distribution).
References FR38 (statistical methods library), FR39 (plain-language
explanation of merge assumptions).
"""

from __future__ import annotations

import logging
import random

import pyarrow as pa

from reformlab.population.methods.base import (
    MergeAssumption,
    MergeConfig,
    MergeResult,
)
from reformlab.population.methods.errors import MergeValidationError

_logger = logging.getLogger(__name__)


class UniformMergeMethod:
    """Merge two tables by uniformly random row matching with replacement.

    Each row from table A is independently matched to a uniformly random
    row from table B. This assumes **no correlation** between the
    variables in the two sources — the weakest possible assumption,
    suitable as a baseline but unrealistic when variables are correlated
    (e.g., income and vehicle ownership).

    The merge is deterministic given the same ``MergeConfig.seed``.
    """

    @property
    def name(self) -> str:
        """Short identifier: ``"uniform"``."""
        return "uniform"

    def merge(
        self,
        table_a: pa.Table,
        table_b: pa.Table,
        config: MergeConfig,
    ) -> MergeResult:
        """Merge two tables using uniform random matching.

        For each of the N rows in *table_a*, independently draw a random
        index from ``[0, M)`` where ``M = table_b.num_rows``, select the
        corresponding row from *table_b* (with replacement), and
        concatenate columns from both tables.

        Column ordering: all columns from *table_a* appear first (in
        their original order), followed by all remaining columns from
        *table_b* (after ``drop_right_columns`` removal).

        Parameters
        ----------
        table_a:
            Left table. All rows are preserved in the output.
        table_b:
            Right table. Rows are sampled with replacement.
        config:
            Merge configuration (seed, drop_right_columns, etc.).

        Returns
        -------
        MergeResult
            Merged table and assumption record.

        Raises
        ------
        MergeValidationError
            If either table is empty, columns overlap after drops,
            or ``drop_right_columns`` references nonexistent columns.
        """
        _logger.info(
            "event=merge_start method=uniform rows_a=%d rows_b=%d seed=%d",
            table_a.num_rows,
            table_b.num_rows,
            config.seed,
        )

        # Validate non-empty inputs
        if table_a.num_rows == 0:
            raise MergeValidationError(
                summary="Empty left table",
                reason="table_a has 0 rows — cannot merge an empty table",
                fix="Provide a table_a with at least one row",
            )
        if table_b.num_rows == 0:
            raise MergeValidationError(
                summary="Empty right table",
                reason="table_b has 0 rows — cannot sample from an empty table",
                fix="Provide a table_b with at least one row",
            )

        # Drop specified right columns
        right_table = table_b
        for col in config.drop_right_columns:
            if col not in right_table.schema.names:
                raise MergeValidationError(
                    summary="Invalid drop_right_columns",
                    reason=(
                        f"Column {col!r} not found in table_b. "
                        f"Available columns: {right_table.schema.names}"
                    ),
                    fix="Check drop_right_columns against table_b schema",
                )
            col_idx = right_table.schema.get_field_index(col)
            right_table = right_table.remove_column(col_idx)

        # Check column name conflicts
        overlap = set(table_a.schema.names) & set(right_table.schema.names)
        if overlap:
            raise MergeValidationError(
                summary="Column name conflict",
                reason=(
                    f"Columns {sorted(overlap)} exist in both tables "
                    f"after drop_right_columns removal"
                ),
                fix=(
                    "Add conflicting column names to "
                    "config.drop_right_columns or rename them before merging"
                ),
            )

        # Random matching with replacement
        rng = random.Random(config.seed)
        n = table_a.num_rows
        m = right_table.num_rows
        indices = pa.array([rng.randrange(m) for _ in range(n)])
        matched_b = right_table.take(indices)

        # Combine columns: table_a first, then matched table_b
        all_columns: dict[str, pa.Array] = {}
        for col_name in table_a.schema.names:
            all_columns[col_name] = table_a.column(col_name)
        for col_name in matched_b.schema.names:
            all_columns[col_name] = matched_b.column(col_name)
        merged = pa.table(all_columns)

        # Build assumption record
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

        _logger.info(
            "event=merge_complete method=uniform merged_rows=%d merged_cols=%d",
            merged.num_rows,
            merged.num_columns,
        )

        return MergeResult(table=merged, assumption=assumption)


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
| Hidden Bugs | 2 |
| Performance Footguns | 0 |
| Security Vulnerabilities | 0 |
| **Total Issues** | **5** |

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🟠 IMPORTANT | Story lists 10 touched files but repo diff shows 51 files changed (loaders, caches, fixtures). Undocumented scope expansion erodes traceability and violates “files changed but not in story File List”. | git diff vs story file list | +1 |
| 🟠 IMPORTANT | `drop_right_columns` elements are not type-checked; a non-str (e.g., `None`) triggers `pyarrow` `TypeError` and escapes the `MergeValidationError` contract. | src/reformlab/population/methods/uniform.py | +1 |
| 🟠 IMPORTANT | Duplicate column names in `table_b` are silently collapsed when building `all_columns` dict, losing data without warning; no validation prevents this. | src/reformlab/population/methods/uniform.py | +1 |
| 🟠 IMPORTANT | `MergeResult` relies on `pa.Table` in annotations but `pyarrow` isn’t imported at runtime (only under `TYPE_CHECKING`). `typing.get_type_hints(MergeResult)` will raise `NameError`, breaking any reflection-based validation. | src/reformlab/population/methods/base.py | +1 |
| 🟠 IMPORTANT | Flaky test: `TestUniformMergeMethodDeterminism.test_different_seed_different_result` assumes different seeds must differ; with 5 draws from 8 rows there’s a 0.003% chance of identical output, causing intermittent CI failures. | tests/population/methods/test_uniform.py | +1 |
| 🟢 CLEAN PASS | 6 clean categories: SOLID, Abstraction, Performance, Tech Debt, Style, Security |  | -3 |

### Evidence Score: 2.0

| Score | Verdict |
|-------|---------|
| **2.0** | **APPROVED** |

---

## 🏛️ Architectural Sins

✅ No significant architectural violations detected.

---

## 🐍 Pythonic Crimes & Readability

✅ Code follows style guidelines and is readable.

---

## ⚡ Performance & Scalability

✅ No significant performance issues detected.

---

## 🐛 Correctness & Safety

- **🐛 Bug:** Non-string entries in `MergeConfig.drop_right_columns` (e.g., `None`) propagate to `Schema.get_field_index`, raising `TypeError` instead of `MergeValidationError`, breaking the subsystem’s error contract.
  - 📍 `src/reformlab/population/methods/uniform.py`
  - 🔄 Reproduction: `UniformMergeMethod().merge(table_a, table_b, MergeConfig(seed=1, drop_right_columns=("region_code", None)))` → uncaught `TypeError`.

- **🐛 Bug:** Duplicate column names in `table_b` survive validation and are collapsed when constructing `all_columns` (dict overwrites), silently dropping data.
  - 📍 `src/reformlab/population/methods/uniform.py`
  - 🔄 Reproduction: `table_b` with two columns named `"x"`; merged table retains only last `"x"` values.

- **🎭 Lying Test:** `TestUniformMergeMethodDeterminism.test_different_seed_different_result` can occasionally fail because two random draws with different seeds can coincide; probability ~0.003% with current fixtures.
  - 📍 `tests/population/methods/test_uniform.py`
  - 🤥 Why it lies: Asserts inequality instead of probabilistic expectation; non-deterministic outcome makes test flaky.

- **🐛 Bug:** `typing.get_type_hints(MergeResult)` raises `NameError` because `pyarrow` is only imported under `TYPE_CHECKING`, yet annotations reference `pa.Table`. Any runtime introspection (e.g., dataclass-based validation) will crash.
  - 📍 `src/reformlab/population/methods/base.py`
  - 🔄 Reproduction: `from typing import get_type_hints; get_type_hints(MergeResult)` → `NameError: name 'pa' is not defined`.

---

## 🔧 Maintainability Issues

- **💣 Scope/traceability debt:** Story claims 10 files touched, but repo shows 51 files changed (loaders, caches, fixtures). Documentation mismatch makes future audits and bisects harder.
  - 📍 git diff vs story file list
  - 💥 Explosion radius: future reviewers and auditors lack reliable change inventory.

---

## 🛠️ Suggested Fixes

### 1. Validate `drop_right_columns` elements
**File:** `src/reformlab/population/methods/base.py` (or in `UniformMergeMethod.merge`)
**Issue:** Non-str entries cause uncaught `TypeError`.
**Fix:** Guard before use.
```python
for col in config.drop_right_columns:
    if not isinstance(col, str) or not col:
        raise MergeValidationError(
            summary="Invalid drop_right_columns",
            reason=f"Column name {col!r} is not a non-empty string",
            fix="Provide valid column names as strings"
        )
```

### 2. Prevent silent data loss on duplicate column names
**File:** `src/reformlab/population/methods/uniform.py`
**Issue:** Duplicate column names in `table_b` are overwritten in `all_columns`.
**Fix:** Reject duplicates before merge.
```python
if len(set(right_table.schema.names)) != len(right_table.schema.names):
    raise MergeValidationError(
        summary="Duplicate column names",
        reason="table_b contains duplicate column names after drops",
        fix="Deduplicate or rename right-table columns before merging",
    )
```

### 3. Ensure `pyarrow` available for type introspection
**File:** `src/reformlab/population/methods/base.py`
**Issue:** `get_type_hints(MergeResult)` fails because `pa` undefined at runtime.
**Fix:** Import `pyarrow` under a try/except when not type-checking.
```python
if TYPE_CHECKING:
    import pyarrow as pa
else:
    import pyarrow as pa  # needed for runtime type hint resolution
```

### 4. Deflake determinism test
**File:** `tests/population/methods/test_uniform.py`
**Issue:** Non-zero probability of identical draws with different seeds.
**Fix:** Compare draws over larger sample or assert probability bounds instead of strict inequality (e.g., run twice and require any difference across two trials). 

### 5. Reconcile story file list with actual changes
**File:** Story doc `_bmad-output/implementation-artifacts/11-4-define-mergemethod-protocol-and-uniform-distribution-method.md`
**Issue:** Mismatch between documented and actual changed files.
**Fix:** Update File List to reflect all touched files or trim unrelated changes into separate story/PR for auditability.

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
| SOLID Violations | 0 |
| Hidden Bugs | 2 |
| Lying / Weak Tests | 3 |
| Performance Footguns | 1 |
| Type Safety | 1 |
| Tech Debt | 2 |
| **Total Issues** | **9** |

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🟠 IMPORTANT | `to_governance_entry()` returns `dict[str, Any]` instead of `AssumptionEntry` TypedDict — no mypy enforcement of governance contract | `base.py:85` | +1 |
| 🟠 IMPORTANT | `MergeAssumption.details` is mutable post-construction despite `frozen=True` — `assumption.details["x"] = "injected"` succeeds silently | `base.py:80` | +1 |
| 🟠 IMPORTANT | `test_drop_right_columns_deep_copied` is a lying test — the mutation target (`original` list) is detached from the config before the call, making the `object.__setattr__` protection unverified | `test_base.py:64` | +1 |
| 🟠 IMPORTANT | `to_governance_entry()` key non-uniqueness — all uniform merges produce `key = "merge_uniform"`, no disambiguation for multi-step pipelines | `base.py:97` | +1 |
| 🟡 MINOR | `test_drop_right_columns_accepts_list_input` passes a tuple `("x",)`, not a list — test name is wrong and the real runtime path (list → tuple coercion) is untested | `test_base.py:70` | +0.3 |
| 🟡 MINOR | No test verifies `assumption.details["dropped_right_columns"]` when drops actually occur — only tested for empty case | `test_uniform.py:275` | +0.3 |
| 🟡 MINOR | Duplicate column in `drop_right_columns` produces misleading error — second iteration says "not found in table_b" for a column that existed originally | `uniform.py:132` | +0.3 |
| 🟡 MINOR | O(N) Python loop `[rng.randrange(m) for _ in range(n)]` materialises N Python integers before PyArrow conversion — 100k households = ~3.4 MB intermediate allocation | `uniform.py:164` | +0.3 |
| 🟡 MINOR | `to_governance_entry()` output is never tested against actual `RunManifest` construction — end-to-end governance integration is unverified | `test_uniform.py:290` | +0.3 |
| 🟢 CLEAN PASS | SOLID — no violations; protocol, dataclass, and class responsibilities are well-separated | — | -0.5 |
| 🟢 CLEAN PASS | Abstraction — not over- or under-engineered; layer boundaries respected | — | -0.5 |
| 🟢 CLEAN PASS | Style — formatting, naming, section separators, `from __future__ import annotations` all consistent | — | -0.5 |
| 🟢 CLEAN PASS | Security — no injection vectors, credential exposure, or unsafe stdlib usage | — | -0.5 |

### Evidence Score: **3.5**

| Score | Verdict |
|-------|---------|
| **3.5** | **MAJOR REWORK** |

---

## 🏛️ Architectural Sins

✅ No significant SOLID violations or layer-boundary breaches detected. The protocol/frozen-dataclass/plain-class split is appropriate. `UniformMergeMethod` is correctly a plain class (service object, not a domain type), while `MergeConfig`, `MergeAssumption`, and `MergeResult` are correctly frozen dataclasses.

---

## 🐍 Pythonic Crimes & Readability

**Type Safety — `to_governance_entry()` return type too loose:**
- 📍 `src/reformlab/population/methods/base.py:85`
- The method docstring promises to return a dict "matching `governance.manifest.AssumptionEntry` structure" but the return annotation is `dict[str, Any]`. Under `mypy --strict`, this means callers that type-annotate the result as `AssumptionEntry` get no structural validation. If `AssumptionEntry` ever gains a new required field, this silent incompatibility won't be caught at compile time.
- **Fix:** Change return type annotation to `AssumptionEntry`:
  ```python
  from reformlab.governance.manifest import AssumptionEntry  # under TYPE_CHECKING
  def to_governance_entry(self, *, source_label: str = "merge_step") -> AssumptionEntry:
  ```

---

## ⚡ Performance & Scalability

**[Medium impact] O(N) Python integer loop before PyArrow conversion:**
- 📍 `src/reformlab/population/methods/uniform.py:164`
- `pa.array([rng.randrange(m) for _ in range(n)])` allocates a Python list of N `int` objects before converting to a PyArrow array. At the architecture's stated target of 100k households, this is ~100k Python objects (~3.4 MB), a GC pressure point that doesn't exist in downstream NumPy-based methods. NumPy is banned by story spec, so this is the only stdlib-compliant path — but it should be explicitly documented as a known limitation, and the `m=1` special-case (all indices trivially `0`) could skip the loop entirely.
- **Fix (within constraint of no new dependencies):** Document the limitation; add a fast path when `m == 1`:
  ```python
  if m == 1:
      indices = pa.array([0] * n)
  else:
      indices = pa.array([rng.randrange(m) for _ in range(n)])
  ```

---

## 🐛 Correctness & Safety

**🐛 Bug: `MergeAssumption.details` is mutable post-construction**
- 📍 `src/reformlab/population/methods/base.py:80-83`
- `frozen=True` only prevents attribute *reassignment*. `assumption.details["injected"] = pa.table(...)` succeeds silently, violating both the immutability contract and the documented JSON-compatibility requirement (could put a `pa.Table` in `details`). This goes undetected until `RunManifest` construction blows up downstream with a confusing `ManifestValidationError`.
- **Reproduction:** `a = MergeAssumption(method_name="x", statement="y", details={}); a.details["bad"] = object(); a.details  # → {"bad": <object>}` — no error raised.
- **Fix:** Either use `types.MappingProxyType` to wrap the dict (preventing mutation without a copy), or add `__post_init__` validation of JSON-compatibility.

**🐛 Misleading error when `drop_right_columns` contains a duplicate:**
- 📍 `src/reformlab/population/methods/uniform.py:132-143`
- If `drop_right_columns=("region_code", "region_code")`, the first iteration removes the column successfully. The second iteration calls `if col not in right_table.schema.names` → True, raising `MergeValidationError("Invalid drop_right_columns", reason="Column 'region_code' not found in table_b...")`. The error implies the column never existed, but it was removed in the prior iteration. Zero tests cover this edge case.
- **Fix:** Validate for duplicates in `MergeConfig.__post_init__` or detect/report the duplicate scenario accurately.

---

**🎭 Lying Test: `test_drop_right_columns_deep_copied`**
- 📍 `tests/population/methods/test_base.py:64-68`
- ```python
  original: list[str] = ["a", "b"]
  cfg = MergeConfig(seed=42, drop_right_columns=tuple(original))  # ← tuple created HERE
  original.append("c")  # modifying the list, which is already detached from cfg
  assert cfg.drop_right_columns == ("a", "b")  # trivially true regardless of __post_init__
  ```
  A `tuple` is already immutable; `tuple(original)` creates an independent object before the constructor is called. Mutating `original` afterward has zero chance of affecting `cfg`. The `object.__setattr__` in `__post_init__` is completely unexercised by this test. The test would pass even if `__post_init__` did nothing at all.
- **Fix:** Test the actual runtime bypass — passing a mutable `list` as the argument (bypassing type hints):
  ```python
  def test_drop_right_columns_list_coerced_to_tuple(self) -> None:
      original = ["a", "b"]
      cfg = MergeConfig(seed=42, drop_right_columns=original)  # type: ignore[arg-type]
      original.append("c")
      assert cfg.drop_right_columns == ("a", "b")  # only passes if __post_init__ converts
  ```

**🎭 Lying Test: `test_drop_right_columns_accepts_list_input`**
- 📍 `tests/population/methods/test_base.py:70-72`
- Test is named "accepts_list_input" but passes a **tuple** `("x",)`. It tests nothing different from `test_custom_values`. The real gap (runtime list → tuple coercion, the actual purpose of `tuple(self.drop_right_columns)` in `__post_init__`) is untested.

**🎭 Weak Test: `test_details_content` doesn't cover populated `dropped_right_columns`**
- 📍 `tests/population/methods/test_uniform.py:275-288`
- The test asserts `assumption.details["dropped_right_columns"] == []` using `default_config` (no drops). `TestUniformMergeMethodDropRightColumns.test_drop_resolves_conflict` verifies the table shape but never checks `result.assumption.details["dropped_right_columns"]`. The contract that drops are recorded in the assumption record is untested for the non-empty case.

---

## 🔧 Maintainability Issues

**💣 Tech Debt: `to_governance_entry()` key scheme breaks multi-step pipelines**
- 📍 `src/reformlab/population/methods/base.py:97`
- The key is hardcoded as `f"merge_{self.method_name}"` → `"merge_uniform"` for every call. Story 11.6 (PopulationPipeline) will compose multiple merge steps. A pipeline doing `[uniform_merge_A, uniform_merge_B]` appends two `AssumptionEntry` records both with `key = "merge_uniform"`. The governance manifest's `assumptions` is a `list` (not a dict), so no crash occurs, but the entries are indistinguishable — which was step 1 vs step 2? The governance layer becomes useless for lineage tracing in multi-step pipelines.
- **Explosion radius:** Story 11.6 (PopulationPipeline), EPIC-11 governance integration, RunManifest lineage.
- **Fix:** Include a step index or label parameter: `to_governance_entry(*, source_label: str = "merge_step", step_index: int | None = None)` → key becomes `f"merge_{self.method_name}_{step_index}"` when provided.

**💣 Tech Debt: `MergeAssumption.details` has no early validation of JSON-compatibility**
- 📍 `src/reformlab/population/methods/base.py:80-83`
- The docstring says values must be JSON-compatible but `__post_init__` only deep-copies. A developer putting a `Path`, `pa.Schema`, or custom object in `details` will get a `ManifestValidationError` deep in governance code during manifest construction — not at merge time where the error originated. Failure point is far from the source.
- **Explosion radius:** Any downstream `RunManifest` construction using this merge's assumption output.

---

## 🛠️ Suggested Fixes

### 1. Fix the lying `test_drop_right_columns_deep_copied` test

**File:** `tests/population/methods/test_base.py`
**Issue:** Test passes `tuple(original)` before calling the constructor, making the aliasing protection untestable.

```diff
 def test_drop_right_columns_deep_copied(self) -> None:
-    original: list[str] = ["a", "b"]
-    cfg = MergeConfig(seed=42, drop_right_columns=tuple(original))
-    original.append("c")
-    assert cfg.drop_right_columns == ("a", "b")
+    # Test that a mutable list passed at runtime is coerced to an immutable tuple
+    original: list[str] = ["a", "b"]
+    cfg = MergeConfig(seed=42, drop_right_columns=original)  # type: ignore[arg-type]
+    original.append("c")  # mutate the source after construction
+    assert cfg.drop_right_columns == ("a", "b")  # __post_init__ tuple() conversion isolates
+    assert isinstance(cfg.drop_right_columns, tuple)
```

### 2. Fix `test_drop_right_columns_accepts_list_input` test name and content

**File:** `tests/population/methods/test_base.py`
**Issue:** Test name claims "list_input" but passes a tuple.

```diff
-def test_drop_right_columns_accepts_list_input(self) -> None:
-    cfg = MergeConfig(seed=42, drop_right_columns=("x",))
-    assert cfg.drop_right_columns == ("x",)
+def test_drop_right_columns_is_always_tuple(self) -> None:
+    """Verify drop_right_columns is always stored as tuple, not list."""
+    cfg = MergeConfig(seed=42, drop_right_columns=("x",))
+    assert isinstance(cfg.drop_right_columns, tuple)
+    assert cfg.drop_right_columns == ("x",)
```

### 3. Add missing test for `dropped_right_columns` in assumption details

**File:** `tests/population/methods/test_uniform.py`
**Issue:** `assumption.details["dropped_right_columns"]` is only verified when empty.

```python
def test_dropped_columns_recorded_in_assumption_details(
    self,
    income_table: pa.Table,
    overlapping_table: pa.Table,
) -> None:
    """AC #3: Dropped columns must appear in assumption details."""
    method = UniformMergeMethod()
    config = MergeConfig(seed=42, drop_right_columns=("region_code",))
    result = method.merge(income_table, overlapping_table, config)
    assert result.assumption.details["dropped_right_columns"] == ["region_code"]
```

### 4. Add test for `to_governance_entry()` output against `RunManifest`

**File:** `tests/population/methods/test_uniform.py`
**Issue:** Governance integration path is untested end-to-end.

```python
def test_governance_entry_passes_manifest_validation(
    self,
    income_table: pa.Table,
    vehicle_table: pa.Table,
    default_config: MergeConfig,
) -> None:
    """End-to-end: governance entry must be accepted by RunManifest validator."""
    from reformlab.governance.manifest import RunManifest
    method = UniformMergeMethod()
    result = method.merge(income_table, vehicle_table, default_config)
    entry = result.assumption.to_governance_entry()
    # RunManifest._validate() enforces JSON-compatibility of assumption values
    manifest = RunManifest(
        manifest_id="test-id",
        created_at="2026-03-03T00:00:00+00:00",
        engine_version="0.1.0",
        openfisca_version="44.0.0",
        adapter_version="1.0.0",
        scenario_version="1.0.0",
        assumptions=[entry],  # type: ignore[list-item]
    )
    assert manifest.assumptions[0]["key"] == "merge_uniform"
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
<var name="session_id">8cb1df08-719c-4a22-857d-a9bc9ff254d2</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_file" file_id="6870c5a9">embedded in prompt, file id: 6870c5a9</var>
<var name="story_id">11.4</var>
<var name="story_key">11-4-define-mergemethod-protocol-and-uniform-distribution-method</var>
<var name="story_num">4</var>
<var name="story_title">define-mergemethod-protocol-and-uniform-distribution-method</var>
<var name="template">False</var>
<var name="timestamp">20260303_1537</var>
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