<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 11 -->
<!-- Story: 3 -->
<!-- Phase: code-review-synthesis -->
<!-- Timestamp: 20260303T140328Z -->
<compiled-workflow>
<mission><![CDATA[

Master Code Review Synthesis: Story 11.3

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
<file id="7243a2d9" path="_bmad-output/implementation-artifacts/11-3-implement-eurostat-ademe-sdes-data-source-loaders.md" label="STORY FILE"><![CDATA[


# Story 11.3: Implement Eurostat, ADEME, and SDES data source loaders

Status: dev-complete

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform developer building the French household population pipeline,
I want concrete data source loaders for Eurostat (EU-SILC income distribution, household energy consumption), ADEME (Base Carbone emission factors), and SDES (vehicle fleet composition),
so that downstream merge methods (Stories 11.4–11.6) can consume real European and French public data as schema-validated `pa.Table` objects through the `DataSourceLoader` protocol.

## Acceptance Criteria

1. Given the Eurostat loader, when called with a valid dataset code, then EU-level household data is returned as a schema-validated `pa.Table`.
2. Given the ADEME loader, when called, then energy consumption and emission factor datasets are returned with documented schemas.
3. Given the SDES loader, when called, then vehicle fleet composition data (including vehicle age classification) is returned as a schema-validated `pa.Table`.
4. Given all three loaders, when run, then each follows the `DataSourceLoader` protocol and integrates with the caching infrastructure from BKL-1101.
5. Given CI tests for all loaders, then they use fixture files and do not require network access.

## Tasks / Subtasks

- [x] Task 1: Create Eurostat loader — `eurostat.py` (AC: #1, #4)
  - [x]1.1 Create `src/reformlab/population/loaders/eurostat.py` with module docstring referencing Story 11.3, FR36, FR37
  - [x]1.2 Define `EurostatDataset` frozen dataclass with fields: `dataset_id: str`, `description: str`, `url: str`, `encoding: str = "utf-8"`, `separator: str = ","`, `null_markers: tuple[str, ...] = ("", ":")`, `columns: tuple[tuple[str, str], ...] = ()` where each inner tuple is `(raw_sdmx_column_name, project_column_name)` — consistent with `INSEEDataset`/`ADEMEDataset`/`SDESDataset` pattern where the dataclass is the single source of truth for parsing configuration
  - [x]1.3 Define `EUROSTAT_CATALOG` as module-level `dict[str, EurostatDataset]` with at minimum:
    - `"ilc_di01"` — Income distribution by quantile (EU-SILC deciles D1–D10, shares/EUR)
    - `"nrg_d_hhq"` — Disaggregated final energy consumption in households
  - [x]1.4 Define per-dataset `pa.Schema` objects for the output columns each dataset produces (after column selection and renaming)
  - [x]1.5 Add `EUROSTAT_AVAILABLE_DATASETS` module-level constant
  - [x]1.6 Implement `EurostatLoader(CachedLoader)` with `__init__(self, *, cache, logger, dataset)` — store dataset reference, call `super().__init__()`
  - [x]1.7 Implement `schema(self) -> pa.Schema` — return schema for this loader's dataset
  - [x]1.8 Implement `_fetch(self, config: SourceConfig) -> pa.Table` — download gzip-compressed SDMX-CSV via `urllib.request`, decompress with `gzip.decompress()`, parse with `pyarrow.csv.read_csv()`, select and rename columns, cast types, return `pa.Table`
  - [x]1.9 On any network error, re-raise as `OSError` for stale-cache fallback
  - [x]1.10 Add structured logging: `event=fetch_start`, `event=fetch_complete` with `provider=eurostat dataset_id=... rows=... columns=...`
  - [x]1.11 Implement `get_eurostat_loader(dataset_id, *, cache, logger=None)` factory function with catalog validation
  - [x]1.12 Implement `make_eurostat_config(dataset_id, **params)` helper function

- [x] Task 2: Create ADEME loader — `ademe.py` (AC: #2, #4)
  - [x]2.1 Create `src/reformlab/population/loaders/ademe.py` with module docstring referencing Story 11.3, FR36, FR37
  - [x]2.2 Define `ADEMEDataset` frozen dataclass with fields: `dataset_id: str`, `description: str`, `url: str`, `encoding: str = "windows-1252"`, `separator: str = ";"`, `null_markers: tuple[str, ...] = ("",)`, `columns: tuple[tuple[str, str], ...] = ()` — raw-to-project column rename mapping
  - [x]2.3 Define `ADEME_CATALOG` with at minimum:
    - `"base_carbone"` — Base Carbone V23.6 emission factors (CSV from data.gouv.fr)
  - [x]2.4 Define per-dataset `pa.Schema` for the output columns (subset of the 60+ raw columns, focused on emission factors relevant to carbon tax simulation)
  - [x]2.5 Add `ADEME_AVAILABLE_DATASETS` module-level constant
  - [x]2.6 Implement `ADEMELoader(CachedLoader)` with dataset-specific parsing — handle Windows-1252 encoding (primary), UTF-8 fallback, semicolon separator
  - [x]2.7 Implement `get_ademe_loader(dataset_id, *, cache, logger=None)` factory function
  - [x]2.8 Implement `make_ademe_config(dataset_id, **params)` helper function

- [x] Task 3: Create SDES loader — `sdes.py` (AC: #3, #4)
  - [x]3.1 Create `src/reformlab/population/loaders/sdes.py` with module docstring referencing Story 11.3, FR36, FR37
  - [x]3.2 Define `SDESDataset` frozen dataclass with fields: `dataset_id: str`, `description: str`, `url: str`, `encoding: str = "utf-8"`, `separator: str = ";"`, `null_markers: tuple[str, ...] = ("",)`, `columns: tuple[tuple[str, str], ...] = ()`, `skip_rows: int = 0` — number of header rows to skip before the column name row (DiDo CSVs may have description rows)
  - [x]3.3 Define `SDES_CATALOG` with at minimum:
    - `"vehicle_fleet"` — Vehicle fleet composition by fuel type, age, Crit'Air, region (communal-level data from data.gouv.fr)
  - [x]3.4 Define per-dataset `pa.Schema` for the output columns (fleet counts by year, fuel type, region)
  - [x]3.5 Add `SDES_AVAILABLE_DATASETS` module-level constant
  - [x]3.6 Implement `SDESLoader(CachedLoader)` with DiDo CSV parsing — UTF-8 encoding, semicolon separator; wire `SDESDataset.skip_rows` into `ReadOptions(skip_rows=self._dataset.skip_rows)`
  - [x]3.7 Implement `get_sdes_loader(dataset_id, *, cache, logger=None)` factory function
  - [x]3.8 Implement `make_sdes_config(dataset_id, **params)` helper function

- [x] Task 4: Update `__init__.py` exports (AC: #4)
  - [x]4.1 Rename `AVAILABLE_DATASETS` → `INSEE_AVAILABLE_DATASETS` in `src/reformlab/population/loaders/insee.py` and update all references (factory functions, `__init__.py`, tests). Keep a `AVAILABLE_DATASETS = INSEE_AVAILABLE_DATASETS` alias for backward compatibility until all existing code is updated.
  - [x]4.2 Add all Eurostat exports to `src/reformlab/population/loaders/__init__.py`: `EurostatDataset`, `EurostatLoader`, `EUROSTAT_AVAILABLE_DATASETS`, `get_eurostat_loader`, `make_eurostat_config`
  - [x]4.3 Add all ADEME exports to `src/reformlab/population/loaders/__init__.py`: `ADEMEDataset`, `ADEMELoader`, `ADEME_AVAILABLE_DATASETS`, `get_ademe_loader`, `make_ademe_config`
  - [x]4.4 Add all SDES exports to `src/reformlab/population/loaders/__init__.py`: `SDESDataset`, `SDESLoader`, `SDES_AVAILABLE_DATASETS`, `get_sdes_loader`, `make_sdes_config`
  - [x]4.5 Add the same exports to `src/reformlab/population/__init__.py`

- [x] Task 5: Create test fixtures (AC: #5)
  - [x]5.1 Create `tests/fixtures/eurostat/` directory with small SDMX-CSV fixtures mimicking `ilc_di01` and `nrg_d_hhq` format (5–10 rows each, comma-separated, UTF-8)
  - [x]5.2 Create `tests/fixtures/ademe/` directory with small CSV fixture mimicking Base Carbone format (5–10 rows, semicolon-separated, Windows-1252 encoded)
  - [x]5.3 Create `tests/fixtures/sdes/` directory with small CSV fixture mimicking DiDo vehicle fleet format (5–10 rows, semicolon-separated, UTF-8)
  - [x]5.4 Add fixture helpers in `tests/population/loaders/conftest.py`: paths and byte-reading fixtures for each provider

- [x] Task 6: Write comprehensive tests (AC: all)
  - [x]6.1 `tests/population/loaders/test_eurostat.py`:
    - `TestEurostatLoaderProtocol`: `isinstance()` check against `DataSourceLoader`
    - `TestEurostatLoaderSchema`: `schema()` returns valid `pa.Schema` for each dataset
    - `TestEurostatLoaderFetch`: monkeypatch `urllib.request.urlopen` to return gzip-compressed fixture; verify `_fetch()` returns correctly-parsed `pa.Table`
    - `TestEurostatLoaderFetchMissingValues`: verify `:` and empty cells produce nulls
    - `TestEurostatLoaderFetchBadGzip`: verify `gzip.BadGzipFile` on corrupt gzip content raises `DataSourceValidationError` (not `OSError`) — prevents wrong stale-cache fallback since `BadGzipFile` inherits from `OSError`
    - `TestEurostatLoaderFetchHTTPError`: verify network errors re-raised as `OSError`
    - `TestEurostatLoaderDownloadIntegration`: full `download()` lifecycle via `CachedLoader`
    - `TestEurostatLoaderCatalog`: catalog completeness, factory function, invalid ID error
    - `TestMakeEurostatConfig`: config construction for each catalog entry
  - [x]6.2 `tests/population/loaders/test_ademe.py`:
    - `TestADEMELoaderProtocol`: protocol compliance
    - `TestADEMELoaderSchema`: schema correctness
    - `TestADEMELoaderFetch`: monkeypatch fetch with Windows-1252 fixture; verify parsing
    - `TestADEMELoaderFetchEncodingFallback`: UTF-8 fallback when primary encoding fails
    - `TestADEMELoaderFetchHTTPError`: network error handling
    - `TestADEMELoaderDownloadIntegration`: full download lifecycle
    - `TestADEMELoaderCatalog`: catalog and factory
    - `TestMakeAdemeConfig`: config construction
  - [x]6.3 `tests/population/loaders/test_sdes.py`:
    - `TestSDESLoaderProtocol`: protocol compliance
    - `TestSDESLoaderSchema`: schema correctness
    - `TestSDESLoaderFetch`: monkeypatch fetch with fixture; verify parsing
    - `TestSDESLoaderFetchSkipRows`: fixture with leading description rows; verify `skip_rows > 0` correctly skips to the header row
    - `TestSDESLoaderFetchHTTPError`: network error handling
    - `TestSDESLoaderDownloadIntegration`: full download lifecycle
    - `TestSDESLoaderCatalog`: catalog and factory
    - `TestMakeSDESConfig`: config construction

- [x] Task 7: Network integration tests (AC: #5)
  - [x]7.1 `tests/population/loaders/test_eurostat_network.py` — `@pytest.mark.network` real download of `ilc_di01` (small dataset)
  - [x]7.2 `tests/population/loaders/test_ademe_network.py` — `@pytest.mark.network` real download of Base Carbone CSV
  - [x]7.3 `tests/population/loaders/test_sdes_network.py` — `@pytest.mark.network` real download of vehicle fleet data

- [x] Task 8: Run full test suite and lint (AC: all)
  - [x]8.1 `uv run pytest tests/population/` — all tests pass
  - [x]8.2 `uv run ruff check src/reformlab/population/ tests/population/` — no lint errors
  - [x]8.3 `uv run mypy src/reformlab/population/` — no mypy errors (strict mode)

## Dev Notes

### Architecture Context: Three Loaders Following the INSEE Pattern

This story implements 3 concrete `DataSourceLoader` implementations, all following the pattern established by `INSEELoader` in Story 11.2. The architecture specifies these files explicitly in `src/reformlab/population/loaders/`:

```
src/reformlab/population/loaders/
├── base.py        ← DataSourceLoader protocol + CachedLoader (Story 11.1)
├── cache.py       ← SourceCache (Story 11.1)
├── errors.py      ← Error hierarchy (Story 11.1)
├── insee.py       ← INSEELoader (Story 11.2) — THE TEMPLATE TO FOLLOW
├── eurostat.py    ← NEW: EurostatLoader (this story)
├── ademe.py       ← NEW: ADEMELoader (this story)
└── sdes.py        ← NEW: SDESLoader (this story)
```

**Every loader MUST:**

1. Subclass `CachedLoader` with keyword-only `__init__` accepting `cache: SourceCache`, `logger: logging.Logger`, and a loader-specific dataset dataclass
2. Override `schema() -> pa.Schema` returning per-dataset schema
3. Override `_fetch(config: SourceConfig) -> pa.Table` performing network download + parsing
4. Re-raise **all** network errors as `OSError` (enables `CachedLoader.download()` stale-cache fallback)
5. Use `DataSourceValidationError` for format/parsing errors (not `OSError`)
6. Provide a `get_{provider}_loader(dataset_id, *, cache, logger=None)` factory function
7. Provide a `make_{provider}_config(dataset_id, **params)` config helper
8. Export a frozen `{Provider}Dataset` dataclass and `{PROVIDER}_AVAILABLE_DATASETS` tuple
9. Use structured logging: `event=fetch_start`, `event=fetch_complete` with `provider=`, `dataset_id=`, etc.

### CachedLoader Contract (CRITICAL — read `base.py`)

The `CachedLoader.download()` method (lines 188–274 of `base.py`) orchestrates the full lifecycle. Concrete loaders ONLY implement `_fetch()` and `schema()`. Key contract rules:

- `_fetch()` **MUST** return a `pa.Table` with exact column names and types matching `schema()`. The validation gate at lines 246–270 checks column names (set equality) and types (exact match per field). A `float64` column in the schema requires `float64` in the table — not `int64`, not `string`.
- `_fetch()` **MUST** raise `OSError` on network failure. `CachedLoader.download()` catches `OSError` to trigger stale-cache fallback (line 230). Any other exception type bypasses fallback and propagates directly.
- `_fetch()` **MUST NOT** interact with the cache. Caching is handled by `CachedLoader.download()` after schema validation passes.

### No New Dependencies Required

All three loaders use only existing dependencies and stdlib:

- `urllib.request` / `urllib.error` — HTTP downloads (stdlib)
- `gzip` — gzip decompression for Eurostat (stdlib)
- `io.BytesIO` — in-memory file handling (stdlib)
- `pyarrow` / `pyarrow.csv` — CSV parsing, table construction (existing dependency)
- `http.client` — for `HTTPException` in network error handling (stdlib)

Do **not** introduce `requests`, `httpx`, `pandas`, `openpyxl`, or any new dependency.

### Network Error Handling Pattern (from INSEE)

All three loaders must follow the same network error handling pattern:

```python
_NETWORK_ERRORS: tuple[type[Exception], ...] = (
    urllib.error.URLError,
    OSError,
    http.client.HTTPException,
)

_HTTP_TIMEOUT_SECONDS = 300

def _fetch(self, config: SourceConfig) -> pa.Table:
    try:
        with urllib.request.urlopen(config.url, timeout=_HTTP_TIMEOUT_SECONDS) as response:
            raw_bytes = response.read()
    except _NETWORK_ERRORS as exc:
        raise OSError(
            f"Failed to download {provider}/{dataset_id} from {url}: {exc}"
        ) from exc
    # Parse raw_bytes → pa.Table ...
```

---

## Eurostat Loader — Detailed Specification

### Data Source: Eurostat SDMX 2.1 API

Eurostat provides bulk data via the SDMX 2.1 Dissemination API. No authentication required. Fully public, anonymous HTTPS GET.

**API base URL:**
```
https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/{DATASET_CODE}
```

**Format choice: SDMX-CSV** (not TSV). SDMX-CSV is a standard long-format CSV (one observation per row) that pyarrow.csv can parse directly. TSV has a non-standard header format that requires custom parsing.

**Download URL pattern with gzip compression:**
```
https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/{CODE}?format=SDMX-CSV&compressed=true
```

With `compressed=true`, the API returns a gzip-compressed `.csv.gz` file. This is **file-level compression** (not HTTP Content-Encoding), so `urllib` does NOT decompress it automatically. Use `gzip.decompress(raw_bytes)` to get the CSV content.

### Eurostat Datasets

| Dataset ID | Code | Description | Size (compressed) | Key Variables |
|---|---|---|---|---|
| `ilc_di01` | `ilc_di01` | Income distribution by quantile (EU-SILC) | ~75 KB | Income shares by decile (D1–D10), by country, by year |
| `nrg_d_hhq` | `nrg_d_hhq` | Household energy consumption | ~150 KB | Energy use in GWh by fuel type, end-use, country, year |

### SDMX-CSV Format Specifics

**Encoding:** UTF-8 (pure ASCII for dimension codes and numeric values).
**Separator:** Comma (`,`).
**Line endings:** `\r\n` (CRLF).

**Column structure per dataset:**

`ilc_di01` SDMX-CSV columns:
```
DATAFLOW,LAST UPDATE,freq,quantile,indic_il,currency,geo,TIME_PERIOD,OBS_VALUE,OBS_FLAG
```

Example rows:
```csv
ESTAT:ILC_DI01(1.0),2024-03-15T23:00:00+0100,A,D1,SHARE,EUR,FR,2022,3.3,
ESTAT:ILC_DI01(1.0),2024-03-15T23:00:00+0100,A,D2,SHARE,EUR,FR,2022,4.8,b
```

`nrg_d_hhq` SDMX-CSV columns:
```
DATAFLOW,LAST UPDATE,freq,nrg_bal,siec,unit,geo,TIME_PERIOD,OBS_VALUE,OBS_FLAG
```

**Metadata columns to DROP:** `DATAFLOW`, `LAST UPDATE` (not useful for analysis).

**Missing values:** `OBS_VALUE` may be empty (missing observation). Use `null_values=["", ":"]` in ConvertOptions.

**Observation flags** (`OBS_FLAG`): Single or combined letters indicating data quality:
- `b` = break in time series, `e` = estimated, `p` = provisional, `c` = confidential, `u` = low reliability
- Flags are informational strings — keep as `utf8` type.

### Eurostat Column Mapping and Schemas

**`ilc_di01` column mapping:**
```python
_ILC_DI01_COLUMNS: tuple[tuple[str, str], ...] = (
    ("freq", "frequency"),
    ("quantile", "quantile"),
    ("indic_il", "indicator"),
    ("currency", "currency"),
    ("geo", "country"),
    ("TIME_PERIOD", "time_period"),
    ("OBS_VALUE", "value"),
    ("OBS_FLAG", "obs_flag"),
)
```

**`ilc_di01` output schema:**
```python
pa.schema([
    pa.field("frequency", pa.utf8()),
    pa.field("quantile", pa.utf8()),
    pa.field("indicator", pa.utf8()),
    pa.field("currency", pa.utf8()),
    pa.field("country", pa.utf8()),
    pa.field("time_period", pa.utf8()),
    pa.field("value", pa.float64()),
    pa.field("obs_flag", pa.utf8()),
])
```

**`nrg_d_hhq` column mapping:**
```python
_NRG_D_HHQ_COLUMNS: tuple[tuple[str, str], ...] = (
    ("freq", "frequency"),
    ("nrg_bal", "energy_balance"),
    ("siec", "energy_product"),
    ("unit", "unit"),
    ("geo", "country"),
    ("TIME_PERIOD", "time_period"),
    ("OBS_VALUE", "value"),
    ("OBS_FLAG", "obs_flag"),
)
```

**`nrg_d_hhq` output schema:**
```python
pa.schema([
    pa.field("frequency", pa.utf8()),
    pa.field("energy_balance", pa.utf8()),
    pa.field("energy_product", pa.utf8()),
    pa.field("unit", pa.utf8()),
    pa.field("country", pa.utf8()),
    pa.field("time_period", pa.utf8()),
    pa.field("value", pa.float64()),
    pa.field("obs_flag", pa.utf8()),
])
```

### Eurostat Parsing Strategy

```python
import gzip

def _fetch(self, config: SourceConfig) -> pa.Table:
    # 1. Download gzip-compressed SDMX-CSV
    raw_bytes = ...  # urllib.request.urlopen(config.url)

    # 2. Decompress gzip (file-level, NOT http-level)
    #    CRITICAL: gzip.BadGzipFile inherits from OSError. If not caught
    #    explicitly here, it propagates as OSError and CachedLoader.download()
    #    triggers stale-cache fallback instead of raising a validation error.
    try:
        csv_bytes = gzip.decompress(raw_bytes)
    except (OSError, gzip.BadGzipFile) as exc:
        raise DataSourceValidationError(
            summary="Gzip decompression failed",
            reason=f"Downloaded content for eurostat/{self._dataset.dataset_id} "
                   f"is not valid gzip: {exc}",
            fix="Check the Eurostat API URL and compressed=true parameter",
        ) from exc

    # 3. Parse with pyarrow.csv
    ds = self._dataset
    raw_names = [col[0] for col in ds.columns]
    project_names = [col[1] for col in ds.columns]
    schema = self.schema()

    column_types: dict[str, pa.DataType] = {}
    for raw_name, proj_name in ds.columns:
        column_types[raw_name] = schema.field(proj_name).type

    convert_options = pcsv.ConvertOptions(
        null_values=list(ds.null_markers),
        column_types=column_types,
        include_columns=raw_names,
    )
    parse_options = pcsv.ParseOptions(delimiter=ds.separator)
    read_options = pcsv.ReadOptions(encoding=ds.encoding)

    table = pcsv.read_csv(
        io.BytesIO(csv_bytes),
        read_options=read_options,
        parse_options=parse_options,
        convert_options=convert_options,
    )

    # 4. Rename columns
    table = table.rename_columns(project_names)
    return table
```

### Eurostat Fixture Design

Create `tests/fixtures/eurostat/ilc_di01.csv` (NOT gzip-compressed, plain CSV for readability — the test wraps it in gzip at runtime):

```csv
DATAFLOW,LAST UPDATE,freq,quantile,indic_il,currency,geo,TIME_PERIOD,OBS_VALUE,OBS_FLAG
ESTAT:ILC_DI01(1.0),2024-03-15T23:00:00+0100,A,D1,SHARE,EUR,FR,2022,3.3,
ESTAT:ILC_DI01(1.0),2024-03-15T23:00:00+0100,A,D2,SHARE,EUR,FR,2022,4.8,b
ESTAT:ILC_DI01(1.0),2024-03-15T23:00:00+0100,A,D3,SHARE,EUR,FR,2022,5.9,
ESTAT:ILC_DI01(1.0),2024-03-15T23:00:00+0100,A,D4,SHARE,EUR,FR,2022,6.8,
ESTAT:ILC_DI01(1.0),2024-03-15T23:00:00+0100,A,D5,SHARE,EUR,DE,2022,,c
```

Note: last row has empty OBS_VALUE (missing) and flag "c" (confidential). Tests should verify this produces `null` in the `value` column.

---

## ADEME Loader — Detailed Specification

### Data Source: Base Carbone via data.gouv.fr

ADEME provides the Base Carbone emission factors as a CSV download on data.gouv.fr. No authentication required. The data.gouv.fr URL serves the file directly.

**Download URL (stable data.gouv.fr resource):**
```
https://www.data.gouv.fr/api/1/datasets/r/ac6a3044-459c-4520-b85a-7e1740f7cd1f
```

**Current version:** V23.6 (updated February 2026), ~10.3 MB, ~18,600 emission factor records.

### ADEME CSV Format Specifics

**CRITICAL: Encoding is Windows-1252 (cp1252), NOT UTF-8.** This is the most important difference from INSEE and Eurostat. French characters like `é`, `è`, `ê`, `ô` are encoded as single bytes in Windows-1252 that are invalid UTF-8.

**Separator:** Semicolon (`;`).
**Line endings:** `\r\n` (CRLF).
**Quote character:** `"` (standard CSV quoting).

**Encoding handling strategy:**

`pyarrow.csv.ReadOptions(encoding=...)` supports Python codec names. Use `"windows-1252"` as the primary encoding, with `"utf-8"` as fallback (in case ADEME switches to UTF-8 in future versions). Follow the same try/catch `pa.ArrowInvalid` pattern as INSEE's encoding fallback:

```python
read_options = pcsv.ReadOptions(encoding="windows-1252")
try:
    table = pcsv.read_csv(io.BytesIO(raw_bytes), ...)
except pa.ArrowInvalid:
    # Fallback to UTF-8 (future-proofing)
    read_options = pcsv.ReadOptions(encoding="utf-8")
    table = pcsv.read_csv(io.BytesIO(raw_bytes), ...)
```

### ADEME Column Mapping and Schema

The Base Carbone CSV has 60+ columns. Select only those relevant to carbon tax microsimulation. The raw column names are French with spaces and accents:

**`base_carbone` column mapping (key subset):**
```python
_BASE_CARBONE_COLUMNS: tuple[tuple[str, str], ...] = (
    ("Identifiant de l'élément", "element_id"),
    ("Nom base français", "name_fr"),
    ("Nom attribut français", "attribute_name_fr"),
    ("Type Ligne", "line_type"),
    ("Unité français", "unit_fr"),
    ("Total poste non décomposé", "total_co2e"),
    ("CO2f", "co2_fossil"),
    ("CH4f", "ch4_fossil"),
    ("CH4b", "ch4_biogenic"),
    ("N2O", "n2o"),
    ("CO2b", "co2_biogenic"),
    ("Autre GES", "other_ghg"),
    ("Localisation géographique", "geography"),
    ("Sous-localisation géographique français", "sub_geography"),
    ("Contributeur", "contributor"),
)
```

**Note on column names:** See "Column Name Verification Strategy" section below for the approach to handling column name drift across data vintages.

**`base_carbone` output schema:**
```python
pa.schema([
    pa.field("element_id", pa.int64()),
    pa.field("name_fr", pa.utf8()),
    pa.field("attribute_name_fr", pa.utf8()),
    pa.field("line_type", pa.utf8()),
    pa.field("unit_fr", pa.utf8()),
    pa.field("total_co2e", pa.float64()),
    pa.field("co2_fossil", pa.float64()),
    pa.field("ch4_fossil", pa.float64()),
    pa.field("ch4_biogenic", pa.float64()),
    pa.field("n2o", pa.float64()),
    pa.field("co2_biogenic", pa.float64()),
    pa.field("other_ghg", pa.float64()),
    pa.field("geography", pa.utf8()),
    pa.field("sub_geography", pa.utf8()),
    pa.field("contributor", pa.utf8()),
])
```

**IMPORTANT:** See "Column Name Verification Strategy" section for handling column name drift. Run the network integration test early to verify ADEME headers match the mapping above.

### ADEME Fixture Design

Create `tests/fixtures/ademe/base_carbone.csv` — a small file (5–10 rows) encoded in **Windows-1252** with semicolon separator, mimicking the real Base Carbone format. Include:
- At least one row with French characters (`é`, `è`, `ê`) to test encoding
- At least one row with empty/null emission values
- Realistic column names from the real dataset

```
Identifiant de l'élément;Nom base français;Nom attribut français;Type Ligne;Unité français;Total poste non décomposé;CO2f;CH4f;CH4b;N2O;CO2b;Autre GES;Localisation géographique;Sous-localisation géographique français;Contributeur
1234;Gaz naturel;PCI;Elément;kgCO2e/kWh PCI;0.227;0.205;0.004;0;0.018;0;0;France métropolitaine;;ADEME
5678;Fioul domestique;PCI;Elément;kgCO2e/litre;3.25;3.15;0.001;0;0.089;0;0;France métropolitaine;;ADEME
9012;Électricité;Mix moyen;Elément;kgCO2e/kWh;0.0569;0.0479;0;0;0.009;0;0;France métropolitaine;;ADEME
```

**The fixture MUST be saved as Windows-1252 encoding**, not UTF-8. The `Write` tool outputs UTF-8, so the fixture must be generated programmatically. Add a fixture helper to `tests/population/loaders/conftest.py`:

```python
@pytest.fixture()
def ademe_base_carbone_csv_bytes() -> bytes:
    """Windows-1252 encoded ADEME Base Carbone CSV fixture."""
    content = (
        "Identifiant de l'élément;Nom base français;Nom attribut français;"
        "Type Ligne;Unité français;Total poste non décomposé;CO2f;CH4f;"
        "CH4b;N2O;CO2b;Autre GES;Localisation géographique;"
        "Sous-localisation géographique français;Contributeur\r\n"
        "1234;Gaz naturel;PCI;Elément;kgCO2e/kWh PCI;0.227;0.205;0.004;"
        "0;0.018;0;0;France métropolitaine;;ADEME\r\n"
        # ... more rows with French characters (é, è, ê) ...
    )
    return content.encode("windows-1252")
```

Tests that monkeypatch `_fetch` should use these bytes directly. The on-disk fixture file at `tests/fixtures/ademe/base_carbone.csv` should be created by a one-time setup script writing `content.encode("windows-1252")` to disk, NOT by the `Write` tool. Include at least one non-ASCII French character (e.g., `é` in `métropolitaine`, `è` in `Elément`) to verify encoding — these differ between UTF-8 (multi-byte) and Windows-1252 (single-byte).

---

## SDES Loader — Detailed Specification

### Data Source: Vehicle Fleet via data.gouv.fr

SDES provides communal-level vehicle fleet data as CSV on data.gouv.fr. The national/regional aggregates are XLSX-only (requires openpyxl, which we don't have), so use the communal-level CSV instead.

**Download URL (data.gouv.fr resource for communal vehicle fleet):**
```
https://www.data.gouv.fr/api/1/datasets/r/2f9fd9c8-e6e1-450e-8548-f479b8a401cd
```

**Alternative: DiDo API endpoint:**
```
https://data.statistiques.developpement-durable.gouv.fr/dido/api/v1/datafiles/3750a580-f249-42d3-b488-5cf8acb767b7/csv?millesime=2023-05&withColumnName=true&withColumnDescription=false&withColumnUnit=false
```

**Decision:** Use the data.gouv.fr URL in `SDES_CATALOG["vehicle_fleet"].url` for simplicity (single GET, no query params needed). The DiDo API URL above is informational only — do not use it in the catalog.

**Note:** The data.gouv.fr resource ID (`2f9fd9c8-...`) may change when new data vintages are published. The URL is stored in the catalog constant and can be updated easily.

### SDES CSV Format Specifics

**Encoding:** UTF-8.
**Separator:** Semicolon (`;`).
**Line endings:** Standard (`\n` or `\r\n`).
**Missing values:** Empty fields (no special markers observed).
**File size:** Large (~10 MB). This is fine for download/cache but test fixtures must be small.

**The DiDo CSV may have multiple header rows** (descriptions, units, column names). The data.gouv.fr version typically has a single header row. If using DiDo API directly, use query parameters `withColumnDescription=false&withColumnUnit=false` to get clean single-header output.

### SDES Column Mapping and Schema

The CSV columns include geographic codes, vehicle classification, and fleet counts by year:

**`vehicle_fleet` column mapping (key subset):**
```python
_VEHICLE_FLEET_COLUMNS: tuple[tuple[str, str], ...] = (
    ("REGION_CODE", "region_code"),
    ("REGION_LIBELLE", "region_name"),
    ("CLASSE_VEHICULE", "vehicle_class"),
    ("CATEGORIE_VEHICULE", "vehicle_category"),
    ("CARBURANT", "fuel_type"),
    ("AGE", "vehicle_age"),
    ("CRITAIR", "critair_sticker"),
    ("PARC_2022", "fleet_count_2022"),
)
```

**Note on column selection:** The raw CSV has fleet count columns for many years (`PARC_2011` through `PARC_2022` or later). For the initial loader, select only the most recent year column to keep the schema manageable. The mapping can be expanded later.

**Alternative approach:** Select multiple year columns:
```python
("PARC_2018", "fleet_2018"),
("PARC_2019", "fleet_2019"),
("PARC_2020", "fleet_2020"),
("PARC_2021", "fleet_2021"),
("PARC_2022", "fleet_2022"),
```

**`vehicle_fleet` output schema:**
```python
pa.schema([
    pa.field("region_code", pa.utf8()),
    pa.field("region_name", pa.utf8()),
    pa.field("vehicle_class", pa.utf8()),
    pa.field("vehicle_category", pa.utf8()),
    pa.field("fuel_type", pa.utf8()),
    pa.field("vehicle_age", pa.utf8()),
    pa.field("critair_sticker", pa.utf8()),
    pa.field("fleet_count_2022", pa.float64()),  # float64 for null handling
])
```

**Note:** Fleet counts use `float64` (not `int64`) to handle potential null values, following the same pattern as INSEE's `nb_fiscal_households`.

**IMPORTANT:** See "Column Name Verification Strategy" section for handling column name drift. Run the network integration test early to verify SDES headers match the mapping above.

### SDES Fixture Design

Create `tests/fixtures/sdes/vehicle_fleet.csv` — a small CSV (5–10 rows) mimicking the DiDo format:

```csv
REGION_CODE;REGION_LIBELLE;CLASSE_VEHICULE;CATEGORIE_VEHICULE;CARBURANT;AGE;CRITAIR;PARC_2022
84;Auvergne-Rhône-Alpes;VP;M1;Diesel;De 1 à 5 ans;Crit'Air 2;450000
84;Auvergne-Rhône-Alpes;VP;M1;Essence;De 1 à 5 ans;Crit'Air 1;380000
84;Auvergne-Rhône-Alpes;VP;M1;Electrique;De 1 à 5 ans;Crit'Air E;95000
11;Île-de-France;VP;M1;Diesel;De 1 à 5 ans;Crit'Air 2;520000
11;Île-de-France;VP;M1;Essence;Plus de 15 ans;;
```

Include at least one row with empty fleet count to test null handling.

---

### Test Pattern to Follow (from INSEE tests)

Follow the exact test structure from `tests/population/loaders/test_insee.py`:

1. **Test helpers** at top of file: `_make_gzip()` (for Eurostat), `_mock_urlopen()` (reuse from INSEE pattern):
   ```python
   def _make_gzip(csv_bytes: bytes) -> bytes:
       """Create gzip-compressed bytes from CSV content."""
       return gzip.compress(csv_bytes)
   ```
2. **Protocol compliance class**: verify `isinstance(loader, DataSourceLoader)`
3. **Schema class**: verify field names and types for each dataset
4. **Fetch class**: monkeypatch `urllib.request.urlopen` to return fixture data; for Eurostat, wrap fixture in gzip first
5. **Error handling class**: verify network errors become `OSError`
6. **Download integration class**: full `CachedLoader.download()` cycle — cache miss → fetch → cache → cache hit
7. **Catalog class**: verify `AVAILABLE_DATASETS`, factory function, invalid ID error
8. **Config class**: verify `make_{provider}_config` produces correct `SourceConfig`

### Network Integration Tests

Create `test_{provider}_network.py` files with `@pytest.mark.network` marker. These are excluded from CI by default (`addopts = "-m 'not integration and not scale and not network'"` in pyproject.toml).

For Eurostat network tests, download the smallest dataset (`ilc_di01` at ~75 KB compressed) to verify schema and basic row count. For ADEME and SDES, download and verify similarly.

### Project Structure Notes

**New files:**
- `src/reformlab/population/loaders/eurostat.py`
- `src/reformlab/population/loaders/ademe.py`
- `src/reformlab/population/loaders/sdes.py`
- `tests/population/loaders/test_eurostat.py`
- `tests/population/loaders/test_ademe.py`
- `tests/population/loaders/test_sdes.py`
- `tests/population/loaders/test_eurostat_network.py`
- `tests/population/loaders/test_ademe_network.py`
- `tests/population/loaders/test_sdes_network.py`
- `tests/fixtures/eurostat/ilc_di01.csv`
- `tests/fixtures/eurostat/nrg_d_hhq.csv`
- `tests/fixtures/ademe/base_carbone.csv`
- `tests/fixtures/sdes/vehicle_fleet.csv`

**Modified files:**
- `src/reformlab/population/loaders/__init__.py` — add all new exports
- `src/reformlab/population/__init__.py` — add all new exports
- `tests/population/loaders/conftest.py` — add fixture helpers for Eurostat, ADEME, SDES

**No changes** to `pyproject.toml` (no new dependencies, `network` marker already exists from Story 11.1)

### Alignment with Architecture

The architecture (`architecture.md`) specifies:

```
src/reformlab/population/
├── loaders/
│   ├── base.py        ← DataSourceLoader protocol (Story 11.1)
│   ├── insee.py       ← INSEE data loader (Story 11.2)
│   ├── eurostat.py    ← Eurostat data loader (this story)
│   ├── ademe.py       ← ADEME energy data loader (this story)
│   └── sdes.py        ← SDES vehicle fleet data loader (this story)
```

All loaders satisfy `DataSourceLoader` protocol via `CachedLoader` base class, matching the "External Data Caching & Offline Strategy" architecture section. Cache paths follow `~/.reformlab/cache/sources/{provider}/{dataset_id}/{hash}.parquet`.

### Error Handling Notes

- `_fetch()` should only raise `OSError` for network errors — `CachedLoader.download()` handles everything else
- Invalid dataset IDs → `DataSourceValidationError` (from factory function, not from `_fetch`)
- Schema mismatches are caught by `CachedLoader.download()` automatically after `_fetch()` returns
- For Eurostat gzip decompression errors → raise `DataSourceValidationError` (not `OSError`, since the download succeeded but the content is invalid)

### Column Name Verification Strategy

For all three data sources, the exact raw column names may vary across data vintages. The recommended approach:

1. **Start with the column names documented in this story** (based on 2026-03 research)
2. **Run the network integration test** early in development to verify column names against live data
3. **If column names differ**, update the catalog constants and fixtures accordingly
4. **Document any discrepancies** in the dev agent record

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#New-Subsystem-Population-Generation] — Directory structure, loader file specifications
- [Source: _bmad-output/planning-artifacts/architecture.md#External-Data-Caching-&-Offline-Strategy] — Cache protocol, offline semantics, DataSourceLoader protocol
- [Source: _bmad-output/planning-artifacts/epics.md#BKL-1103] — Story definition and acceptance criteria
- [Source: _bmad-output/planning-artifacts/prd.md#FR36] — "Analyst can download and cache public datasets from institutional sources"
- [Source: _bmad-output/planning-artifacts/prd.md#FR37] — "Analyst can browse available datasets and select which to include in a population"
- [Source: _bmad-output/project-context.md#Python-Language-Rules] — Frozen dataclasses, Protocols, `from __future__ import annotations`
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules] — PyArrow canonical data type, no pandas in core logic
- [Source: src/reformlab/population/loaders/base.py] — DataSourceLoader Protocol, CachedLoader base class, SourceConfig, CacheStatus
- [Source: src/reformlab/population/loaders/cache.py] — SourceCache caching infrastructure
- [Source: src/reformlab/population/loaders/errors.py] — DataSourceError hierarchy
- [Source: src/reformlab/population/loaders/insee.py] — INSEELoader concrete implementation (THE PATTERN TO FOLLOW)
- [Source: tests/population/loaders/test_insee.py] — INSEE test patterns to replicate
- [Source: tests/population/loaders/conftest.py] — Test fixture patterns, MockCachedLoader
- [Source: _bmad-output/implementation-artifacts/11-1-define-datasourceloader-protocol-and-caching-infrastructure.md] — Story 11.1 (protocol + caching)
- [Source: _bmad-output/implementation-artifacts/11-2-implement-insee-data-source-loader.md] — Story 11.2 (INSEE loader, predecessor)
- [Source: Eurostat SDMX 2.1 API] — https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-getting-started/sdmx2.1
- [Source: Eurostat ilc_di01] — https://ec.europa.eu/eurostat/databrowser/product/page/ilc_di01
- [Source: Eurostat nrg_d_hhq] — https://ec.europa.eu/eurostat/databrowser/product/page/NRG_D_HHQ
- [Source: Base Carbone on data.gouv.fr] — https://www.data.gouv.fr/datasets/base-carbone-r-2
- [Source: SDES Vehicle Fleet on data.gouv.fr] — https://www.data.gouv.fr/datasets/parc-de-vehicules-routiers

## Dev Agent Record

### Agent Model Used

claude-opus-4-6

### Debug Log References

None — clean implementation with one test fix (ADEME encoding fallback needed `ArrowKeyError` in addition to `ArrowInvalid`).

### Completion Notes List

- All 3 loaders (Eurostat, ADEME, SDES) implemented following the INSEE pattern exactly
- `AVAILABLE_DATASETS` renamed to `INSEE_AVAILABLE_DATASETS` with backward-compatible alias
- ADEME encoding fallback catches both `pa.ArrowInvalid` and `pa.lib.ArrowKeyError` (UTF-8 bytes decoded as Windows-1252 garble column names, producing `ArrowKeyError` not `ArrowInvalid`)
- Eurostat gzip decompression errors correctly raise `DataSourceValidationError` (not `OSError`) to prevent wrong stale-cache fallback
- ADEME fixture written as Windows-1252 via Python script (Write tool outputs UTF-8)
- 87 new tests + 1723 total pass, 0 regressions
- ruff, mypy strict: all clean

### File List

**New files:**
- `src/reformlab/population/loaders/eurostat.py`
- `src/reformlab/population/loaders/ademe.py`
- `src/reformlab/population/loaders/sdes.py`
- `tests/population/loaders/test_eurostat.py`
- `tests/population/loaders/test_ademe.py`
- `tests/population/loaders/test_sdes.py`
- `tests/population/loaders/test_eurostat_network.py`
- `tests/population/loaders/test_ademe_network.py`
- `tests/population/loaders/test_sdes_network.py`
- `tests/fixtures/eurostat/ilc_di01.csv`
- `tests/fixtures/eurostat/nrg_d_hhq.csv`
- `tests/fixtures/ademe/base_carbone.csv`
- `tests/fixtures/sdes/vehicle_fleet.csv`

**Modified files:**
- `src/reformlab/population/loaders/insee.py` — renamed `AVAILABLE_DATASETS` → `INSEE_AVAILABLE_DATASETS` + alias
- `src/reformlab/population/loaders/__init__.py` — added all new exports
- `src/reformlab/population/__init__.py` — added all new exports
- `tests/population/loaders/conftest.py` — added Eurostat, ADEME, SDES fixture helpers

## Change Log

- 2026-03-03: Story created by create-story workflow — comprehensive developer context with Eurostat SDMX-CSV parsing, ADEME Windows-1252 handling, SDES DiDo CSV format, test fixture designs, and verified download URLs.
- 2026-03-03: Story implemented — all 3 loaders, 87 new tests, full CI validation (ruff + mypy strict + 1723 tests pass).


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
    "make_ademe_config",
    "make_eurostat_config",
    "make_insee_config",
    "make_sdes_config",
]


]]></file>
<file id="eee493a5" path="src/reformlab/population/loaders/__init__.py" label="SOURCE CODE"><![CDATA[

"""Institutional data source loaders with disk-based caching.

Provides the ``DataSourceLoader`` protocol, ``SourceCache`` for
offline-first caching, and ``CachedLoader`` base class for building
concrete loaders (INSEE, Eurostat, ADEME, SDES).

Implements Story 11.1 (DataSourceLoader protocol and caching infrastructure).
Implements Story 11.2 (INSEE data source loader).
Implements Story 11.3 (Eurostat, ADEME, SDES data source loaders).
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
    "make_ademe_config",
    "make_eurostat_config",
    "make_insee_config",
    "make_sdes_config",
]


]]></file>
<file id="8b3c5126" path="src/reformlab/population/loaders/ademe.py" label="SOURCE CODE"><![CDATA[

"""ADEME institutional data source loader.

Downloads, caches, and schema-validates ADEME Base Carbone emission factor
datasets. Concrete implementation of the ``DataSourceLoader`` protocol via
``CachedLoader``.

Handles Windows-1252 encoding (primary) with UTF-8 fallback, semicolon
separator, and French-language column names with accents.

Implements Story 11.3 (Implement Eurostat, ADEME, SDES data source loaders).
References: FR36 (download and cache public datasets), FR37 (browse
available datasets).
"""

from __future__ import annotations

import http.client
import io
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pyarrow as pa
import pyarrow.csv as pcsv

from reformlab.population.loaders.base import CachedLoader, SourceConfig
from reformlab.population.loaders.errors import DataSourceValidationError

if TYPE_CHECKING:
    from reformlab.population.loaders.cache import SourceCache


# ====================================================================
# ADEME dataset metadata
# ====================================================================


@dataclass(frozen=True)
class ADEMEDataset:
    """Metadata for a known ADEME dataset.

    The ``columns`` field defines the raw-to-project column rename mapping.
    Each inner tuple is ``(raw_column_name, project_column_name)``.
    """

    dataset_id: str
    description: str
    url: str
    encoding: str = "windows-1252"
    separator: str = ";"
    null_markers: tuple[str, ...] = ("",)
    columns: tuple[tuple[str, str], ...] = ()


# ====================================================================
# Dataset catalog
# ====================================================================

_BASE_CARBONE_COLUMNS: tuple[tuple[str, str], ...] = (
    ("Identifiant de l'\xe9l\xe9ment", "element_id"),
    ("Nom base fran\xe7ais", "name_fr"),
    ("Nom attribut fran\xe7ais", "attribute_name_fr"),
    ("Type Ligne", "line_type"),
    ("Unit\xe9 fran\xe7ais", "unit_fr"),
    ("Total poste non d\xe9compos\xe9", "total_co2e"),
    ("CO2f", "co2_fossil"),
    ("CH4f", "ch4_fossil"),
    ("CH4b", "ch4_biogenic"),
    ("N2O", "n2o"),
    ("CO2b", "co2_biogenic"),
    ("Autre GES", "other_ghg"),
    ("Localisation g\xe9ographique", "geography"),
    ("Sous-localisation g\xe9ographique fran\xe7ais", "sub_geography"),
    ("Contributeur", "contributor"),
)

ADEME_CATALOG: dict[str, ADEMEDataset] = {
    "base_carbone": ADEMEDataset(
        dataset_id="base_carbone",
        description="Base Carbone V23.6 emission factors (CSV from data.gouv.fr)",
        url="https://www.data.gouv.fr/api/1/datasets/r/ac6a3044-459c-4520-b85a-7e1740f7cd1f",
        columns=_BASE_CARBONE_COLUMNS,
    ),
}

ADEME_AVAILABLE_DATASETS: tuple[str, ...] = tuple(sorted(ADEME_CATALOG.keys()))
"""Available ADEME dataset identifiers for discovery."""


# ====================================================================
# Per-dataset PyArrow schemas
# ====================================================================


def _base_carbone_schema() -> pa.Schema:
    return pa.schema([
        pa.field("element_id", pa.int64()),
        pa.field("name_fr", pa.utf8()),
        pa.field("attribute_name_fr", pa.utf8()),
        pa.field("line_type", pa.utf8()),
        pa.field("unit_fr", pa.utf8()),
        pa.field("total_co2e", pa.float64()),
        pa.field("co2_fossil", pa.float64()),
        pa.field("ch4_fossil", pa.float64()),
        pa.field("ch4_biogenic", pa.float64()),
        pa.field("n2o", pa.float64()),
        pa.field("co2_biogenic", pa.float64()),
        pa.field("other_ghg", pa.float64()),
        pa.field("geography", pa.utf8()),
        pa.field("sub_geography", pa.utf8()),
        pa.field("contributor", pa.utf8()),
    ])


_DATASET_SCHEMAS: dict[str, pa.Schema] = {
    "base_carbone": _base_carbone_schema(),
}


# ====================================================================
# ADEMELoader
# ====================================================================

_NETWORK_ERRORS: tuple[type[Exception], ...] = (
    urllib.error.URLError,
    OSError,
    http.client.HTTPException,
)

_HTTP_TIMEOUT_SECONDS = 300
"""Timeout for ADEME HTTP downloads (5 minutes)."""


class ADEMELoader(CachedLoader):
    """Concrete loader for ADEME institutional data sources.

    Extends ``CachedLoader`` with ADEME-specific CSV parsing, Windows-1252
    encoding (primary) with UTF-8 fallback, semicolon separator, and
    French-language column names.

    Each loader instance handles one ``ADEMEDataset``. Use
    ``get_ademe_loader`` factory to construct from a catalog dataset ID.
    """

    def __init__(
        self,
        *,
        cache: SourceCache,
        logger: logging.Logger,
        dataset: ADEMEDataset,
    ) -> None:
        self._dataset = dataset
        super().__init__(cache=cache, logger=logger)

    def schema(self) -> pa.Schema:
        """Return the expected PyArrow schema for this loader's dataset."""
        return _DATASET_SCHEMAS[self._dataset.dataset_id]

    def _fetch(self, config: SourceConfig) -> pa.Table:
        """Download and parse an ADEME dataset from its URL.

        Handles Windows-1252 encoding with UTF-8 fallback and semicolon
        separator. Re-raises all network errors as ``OSError`` so
        ``CachedLoader.download()`` can handle stale-cache fallback.
        """
        self._logger.debug(
            "event=fetch_start provider=ademe dataset_id=%s url=%s",
            self._dataset.dataset_id,
            config.url,
        )

        try:
            with urllib.request.urlopen(config.url, timeout=_HTTP_TIMEOUT_SECONDS) as response:  # noqa: S310
                raw_bytes = response.read()
        except _NETWORK_ERRORS as exc:
            raise OSError(
                f"Failed to download ademe/{self._dataset.dataset_id} "
                f"from {config.url}: {exc}"
            ) from exc

        table = self._parse_csv(raw_bytes)

        self._logger.debug(
            "event=fetch_complete provider=ademe dataset_id=%s rows=%d columns=%d",
            self._dataset.dataset_id,
            table.num_rows,
            table.num_columns,
        )
        return table

    def _parse_csv(self, csv_bytes: bytes) -> pa.Table:
        """Parse CSV bytes into a pa.Table with schema enforcement.

        Tries Windows-1252 first, falls back to UTF-8 on decode error.
        """
        ds = self._dataset
        raw_names = [col[0] for col in ds.columns]
        project_names = [col[1] for col in ds.columns]
        expected_schema = self.schema()

        # Build column_types mapping using RAW column names
        column_types: dict[str, pa.DataType] = {}
        for raw_name, proj_name in ds.columns:
            column_types[raw_name] = expected_schema.field(proj_name).type

        convert_options = pcsv.ConvertOptions(
            null_values=list(ds.null_markers),
            column_types=column_types,
            include_columns=raw_names,
        )
        parse_options = pcsv.ParseOptions(delimiter=ds.separator)

        # Try primary encoding (Windows-1252), fallback to UTF-8 on decode error.
        # ArrowInvalid: byte sequence invalid for the encoding.
        # ArrowKeyError: decoding succeeded but column names are garbled
        # (UTF-8 multi-byte chars decoded as Windows-1252 produce different names).
        read_options = pcsv.ReadOptions(encoding=ds.encoding)
        try:
            table = pcsv.read_csv(
                io.BytesIO(csv_bytes),
                read_options=read_options,
                parse_options=parse_options,
                convert_options=convert_options,
            )
        except (pa.ArrowInvalid, pa.lib.ArrowKeyError):
            self._logger.debug(
                "event=encoding_fallback provider=ademe dataset_id=%s "
                "primary=%s fallback=utf-8",
                ds.dataset_id,
                ds.encoding,
            )
            fallback_options = pcsv.ReadOptions(encoding="utf-8")
            table = pcsv.read_csv(
                io.BytesIO(csv_bytes),
                read_options=fallback_options,
                parse_options=parse_options,
                convert_options=convert_options,
            )

        # Rename columns from raw French names to project names
        table = table.rename_columns(project_names)
        return table


# ====================================================================
# Factory and helper functions
# ====================================================================


def get_ademe_loader(
    dataset_id: str,
    *,
    cache: SourceCache,
    logger: logging.Logger | None = None,
) -> ADEMELoader:
    """Factory: construct an ``ADEMELoader`` from a catalog dataset ID.

    Parameters
    ----------
    dataset_id : str
        A key from ``ADEME_AVAILABLE_DATASETS`` (e.g. ``"base_carbone"``).
    cache : SourceCache
        Cache infrastructure for downloaded data.
    logger : logging.Logger | None
        Optional logger. Defaults to ``reformlab.population.loaders.ademe``.

    Raises
    ------
    DataSourceValidationError
        If ``dataset_id`` is not in the catalog.
    """
    if dataset_id not in ADEME_CATALOG:
        raise DataSourceValidationError(
            summary="Unknown ADEME dataset",
            reason=f"Requested dataset '{dataset_id}' is not in the ADEME catalog",
            fix=f"Available datasets: {', '.join(ADEME_AVAILABLE_DATASETS)}",
        )
    if logger is None:
        logger = logging.getLogger("reformlab.population.loaders.ademe")
    return ADEMELoader(
        cache=cache,
        logger=logger,
        dataset=ADEME_CATALOG[dataset_id],
    )


def make_ademe_config(dataset_id: str, **params: str) -> SourceConfig:
    """Convenience: construct a ``SourceConfig`` from a catalog dataset ID.

    Parameters
    ----------
    dataset_id : str
        A key from ``ADEME_AVAILABLE_DATASETS``.
    **params : str
        Additional query parameters for the download request.

    Raises
    ------
    DataSourceValidationError
        If ``dataset_id`` is not in the catalog.
    """
    if dataset_id not in ADEME_CATALOG:
        raise DataSourceValidationError(
            summary="Unknown ADEME dataset",
            reason=f"Requested dataset '{dataset_id}' is not in the ADEME catalog",
            fix=f"Available datasets: {', '.join(ADEME_AVAILABLE_DATASETS)}",
        )
    ds = ADEME_CATALOG[dataset_id]
    return SourceConfig(
        provider="ademe",
        dataset_id=ds.dataset_id,
        url=ds.url,
        params=params,
        description=ds.description,
    )


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


]]></file>
<file id="1d910d88" path="[Validator A]" label="VALIDATION OUTPUT"><![CDATA[

**🔥 ADVERSARIAL CODE REVIEW COMPLETE, Lucas!**

**Story:** `_bmad-output/implementation-artifacts/11-3-implement-eurostat-ademe-sdes-data-source-loaders.md`

---

## 📊 Review Summary

| Category | Issues Found |
|----------|--------------|
| Git vs Story Discrepancies | 0 |
| AC Implementation Gaps | 0 |
| Task Completion Lies | 0 |
| Hidden Bugs / Error Handling | 2 |
| Lying Tests | 1 |
| Performance / Brittleness | 1 |
| API Design | 1 |
| Test Quality | 3 |
| Style / Minor | 2 |
| **Total Issues** | **10** |

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🔴 CRITICAL | Lying test: `test_bad_gzip_does_not_trigger_stale_fallback` calls `_fetch()` not `download()` — cannot possibly test the claimed behaviour | `test_eurostat.py:257` | +3 |
| 🟠 IMPORTANT | ADEME double-encoding failure propagates raw `pa.ArrowInvalid` — bypasses error hierarchy and stale-cache fallback entirely | `ademe.py:_parse_csv` | +1 |
| 🟠 IMPORTANT | SDES schema hardcodes year 2022 (`fleet_count_2022`, `PARC_2022`) — loader silently breaks when source publishes 2023 vintage | `sdes.py:15-18,_vehicle_fleet_schema` | +1 |
| 🟠 IMPORTANT | `make_*_config(**params)` documented as "query parameters for the download request" but params are NEVER applied to the URL — misleading API contract across all three loaders | `eurostat.py:308`, `ademe.py:284`, `sdes.py:272` | +1 |
| 🟠 IMPORTANT | Weak SDES UTF-8 encoding assertions avoid non-ASCII characters — `"le-de-France" in ...` and `"Auvergne" in ...` don't verify `Î` / `ô` decoded correctly | `test_sdes.py:133-134` | +1 |
| 🟡 MINOR | `_DATASET_SCHEMAS` private symbol imported in all three test files — tight coupling to internals | `test_eurostat.py:24`, `test_ademe.py:22`, `test_sdes.py:23` | +0.3 |
| 🟡 MINOR | `_NETWORK_ERRORS` tuple includes both `urllib.error.URLError` AND `OSError` — `URLError` is a subclass of `OSError`, making the entry redundant (copy-pasted across all three loaders) | `eurostat.py:148`, `ademe.py:133`, `sdes.py:118` | +0.3 |
| 🟡 MINOR | ADEME column names use escaped Unicode (`\xe9`, `\xe7`) instead of actual Unicode characters — source data column names unreadable without decoding | `ademe.py:56-70` | +0.3 |
| 🟡 MINOR | ADEME UTF-8 fallback test asserts only pure-ASCII value "Gaz naturel" — never verifies non-ASCII content decoded correctly via fallback path | `test_ademe.py:115-122` | +0.3 |
| 🟢 CLEAN PASS | Architecture compliance: adapter isolation, frozen dataclasses, Protocol usage, no OpenFisca imports — clean | — | −0.5 |
| 🟢 CLEAN PASS | Security: no credential exposure, no injection vectors, no hardcoded secrets | — | −0.5 |
| 🟢 CLEAN PASS | Performance: no N+1 patterns, caching works correctly, no memory leaks visible | — | −0.5 |

### Evidence Score: **6.7**

| Score | Verdict |
|-------|---------|
| **6.7** | **MAJOR REWORK** |

---

## 🏛️ Architectural Sins

✅ No architectural boundary violations. All three loaders correctly subclass `CachedLoader`, no OpenFisca imports sneak in, frozen dataclasses throughout.

---

## 🐍 Pythonic Crimes & Readability

- **Escaped Unicode in catalog constants:** `_BASE_CARBONE_COLUMNS` uses raw byte escapes (`\xe9`, `\xe7`) for French column names. These are the *raw column names from the source data* — the fact you can't read them as-is is a real maintainability problem. If the source data changes column names in a new vintage (already acknowledged as a risk), these constants are impossible to diff visually.
  - 📍 `ademe.py:56-70`

- **Redundant `_DATASET_SCHEMAS` private import in tests:** All three test files import the private `_DATASET_SCHEMAS` dict for `test_all_datasets_have_schemas`. The same coverage is achievable via `loader.schema()` for each catalog ID. If `_DATASET_SCHEMAS` is ever renamed, 3 test files silently break.
  - 📍 `test_eurostat.py:24`, `test_ademe.py:22`, `test_sdes.py:23`

- **Redundant `URLError` in `_NETWORK_ERRORS`:** `urllib.error.URLError` inherits from `OSError` in Python 3. Every loader defines the same three-element tuple copied from the story spec without reviewing whether all three types are distinct. `OSError` alone already catches `URLError`.
  - 📍 `eurostat.py:148-153`, `ademe.py:133-138`, `sdes.py:118-123`

---

## ⚡ Performance & Scalability

✅ No performance footguns. The caching layer is correct. Download-once-then-cache semantics work as intended.

---

## 🐛 Correctness & Safety

- **🐛 ADEME double-encoding failure: unhandled raw `pa.ArrowInvalid`**
  - 📍 `ademe.py:_parse_csv` (~line 160-185)
  - If primary Windows-1252 decode fails (caught) and the UTF-8 fallback call *also* fails (e.g. file is neither valid W1252 nor UTF-8), the second `pcsv.read_csv()` raises `pa.ArrowInvalid` unhandled. This propagates through `_fetch()` as-is. `CachedLoader.download()` at `base.py:230` only catches `OSError` for stale-cache fallback — `pa.ArrowInvalid` is not `OSError`, so the stale cache is *never tried*. The caller gets a raw PyArrow traceback with no `DataSourceValidationError` wrapper and no hint about which provider/dataset failed. The fix: wrap the fallback `read_csv` call in a `try/except (pa.ArrowInvalid, pa.lib.ArrowKeyError) as exc: raise DataSourceValidationError(...)`.
  - 🔄 Reproduction: Feed `_parse_csv()` with bytes that are valid gzip but contain binary garbage — neither encoding attempt succeeds.

- **🐛 SDES schema hardcodes 2022 vintage: no forward compatibility**
  - 📍 `sdes.py:15-18` (`_VEHICLE_FLEET_COLUMNS`), `sdes.py:_vehicle_fleet_schema`
  - The column mapping hard-wires `("PARC_2022", "fleet_count_2022")` and the schema names the field `fleet_count_2022`. When SDES publishes the 2023 file at the same data.gouv.fr URL (which happens annually), the column `PARC_2022` will be absent. `CachedLoader.download()` will then raise `DataSourceValidationError: missing columns: fleet_count_2022`. No version-aware logic exists and no warning is emitted. The story acknowledges this as a known limitation but leaves no update path — a developer must modify both `_VEHICLE_FLEET_COLUMNS`, `_vehicle_fleet_schema`, AND update all test fixtures. Any cached Parquet from 2022-vintage data will also be schema-incompatible. Medium explosion radius.
  - 🔄 Reproduction: SDES updates the resource in mid-2026. Any call to `loader.download(config)` after the URL content changes fails validation permanently until code is patched.

- **🎭 Lying Test: `test_bad_gzip_does_not_trigger_stale_fallback`**
  - 📍 `test_eurostat.py:257-265`
  - 🤥 Why it lies: The test calls `loader._fetch(config)` directly, bypassing `CachedLoader.download()` entirely. `_fetch()` has no stale-cache fallback logic — it simply raises or returns. The test name claims it verifies that corrupt gzip "does not trigger stale-cache fallback," but calling `_fetch()` directly means the stale-cache path in `download()` is never exercised. The assertion that `_fetch()` raises `DataSourceValidationError` is already fully covered by the preceding `test_bad_gzip_raises_validation_error`. To actually test the stale-fallback claim, the test needs to: (1) write a stale entry to the cache, (2) call `loader.download(config)` with corrupt gzip data, (3) assert that `DataSourceValidationError` is raised rather than the stale table being returned. As written, this test adds false confidence about a real invariant without validating it.

---

## 🔧 Maintainability Issues

- **💣 `make_*_config(**params)` API contract lie**
  - 📍 `eurostat.py:308-323`, `ademe.py:284-299`, `sdes.py:272-290`
  - 💥 Explosion radius: Silent data correctness issue for all three loaders.
  - All three `make_*_config()` helpers document `**params` as *"Additional query parameters for the download request."* But `_fetch()` uses `config.url` verbatim — the params are never appended to the URL. `SourceCache.cache_key()` uses params to differentiate cache slots, so `make_eurostat_config("ilc_di01", geo="FR")` creates a different cache entry than `make_eurostat_config("ilc_di01")`, but **both download the identical full unfiltered dataset**. An analyst who passes `geo="FR"` expecting country-filtered data gets all 30+ countries cached separately under a misleading key. The docstring is actively wrong. Either the params should be applied to the URL, or the docstring must be corrected to "differentiates cache slots only, does not filter downloads."

- **💣 Weak SDES encoding assertions avoid non-ASCII characters**
  - 📍 `test_sdes.py:133-134`
  - 💥 Explosion radius: UTF-8 encoding correctness for SDES is untested.
  - The SDES fixture `vehicle_fleet.csv` contains `Île-de-France` (with `Î`, U+00CE) and `Auvergne-Rhône-Alpes` (with `ô`, U+00F4). The tests assert:
    ```python
    assert "le-de-France" in region_names[3]
    assert "Auvergne" in region_names[0]
    ```
    Both checks use substrings that are pure ASCII and match even if multi-byte UTF-8 characters are decoded incorrectly (e.g. `\xc3\x8e` misread as two Latin-1 chars, producing garbage that still contains `le-de-France`). The test for "UTF-8 encoding is correctly handled for French geographic names" passes even if it isn't. Given that ADEME learned the hard way about encoding issues in Story 11.2, SDES deserves equally rigorous encoding coverage.

---

## 🛠️ Suggested Fixes

### 1. Fix the lying test to actually test stale-fallback prevention

**File:** `tests/population/loaders/test_eurostat.py`
**Issue:** `test_bad_gzip_does_not_trigger_stale_fallback` calls `_fetch()` instead of `download()` — the stale-cache path is never involved.

```diff
 def test_bad_gzip_does_not_trigger_stale_fallback(
-    self, source_cache: SourceCache
+    self,
+    source_cache: SourceCache,
+    eurostat_ilc_di01_csv_bytes: bytes,
 ) -> None:
-    """Corrupt gzip should NOT be caught as OSError by CachedLoader."""
-    loader = get_eurostat_loader("ilc_di01", cache=source_cache)
-    config = make_eurostat_config("ilc_di01")
-
-    # Verify it raises DataSourceValidationError, not OSError
-    with patch("urllib.request.urlopen", return_value=_mock_urlopen(b"corrupt")):
-        with pytest.raises(DataSourceValidationError):
-            loader._fetch(config)
+    """Corrupt gzip raises DataSourceValidationError through download(), not stale fallback."""
+    loader = get_eurostat_loader("ilc_di01", cache=source_cache)
+    config = make_eurostat_config("ilc_di01")
+
+    # Pre-seed stale cache so fallback is available if triggered incorrectly
+    gz_good = _make_gzip(eurostat_ilc_di01_csv_bytes)
+    with patch("urllib.request.urlopen", return_value=_mock_urlopen(gz_good)):
+        loader.download(config)
+    # Force stale by manipulating cache (or accept that a fresh cache hit would mask the bug)
+    # The critical assertion: bad gzip should raise DataSourceValidationError through download(),
+    # not silently return stale data.
+    with patch("urllib.request.urlopen", return_value=_mock_urlopen(b"corrupt")):
+        with pytest.raises(DataSourceValidationError, match="Gzip decompression failed"):
+            loader.download(config)  # must call download(), not _fetch()
```

### 2. Wrap ADEME UTF-8 fallback failure in `DataSourceValidationError`

**File:** `src/reformlab/population/loaders/ademe.py`
**Issue:** Second `read_csv` call can raise raw `pa.ArrowInvalid`, bypassing error hierarchy.

```diff
         except (pa.ArrowInvalid, pa.lib.ArrowKeyError):
             self._logger.debug(...)
             fallback_options = pcsv.ReadOptions(encoding="utf-8")
-            table = pcsv.read_csv(
-                io.BytesIO(csv_bytes),
-                read_options=fallback_options,
-                parse_options=parse_options,
-                convert_options=convert_options,
-            )
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
+                    f"windows-1252 or utf-8: {exc2}",
+                    fix="Check the ADEME source URL — encoding may have changed",
+                ) from exc2
```

### 3. Fix misleading `make_*_config` docstrings (all three loaders)

**File:** `src/reformlab/population/loaders/eurostat.py`, `ademe.py`, `sdes.py`
**Issue:** `**params` documented as "query parameters for the download request" but never applied to URL.

```diff
-    **params : str
-        Additional query parameters for the download request.
+    **params : str
+        Additional parameters used to differentiate cache slots only.
+        These are NOT appended to the download URL. The full dataset is
+        always downloaded from the catalog URL regardless of params values.
```

### 4. Fix weak SDES encoding assertions

**File:** `tests/population/loaders/test_sdes.py`
**Issue:** `in`-substring checks avoid the actual non-ASCII characters.

```diff
-        assert "Auvergne" in region_names[0]
-        assert "le-de-France" in region_names[3]
+        assert region_names[0] == "Auvergne-Rh\xf4ne-Alpes"  # Auvergne-Rhône-Alpes
+        assert region_names[3] == "\xcele-de-France"          # Île-de-France
```

---

## Summary for Lucas

The three loaders are structurally solid — they follow the INSEE pattern faithfully, the gzip/BadGzipFile subtlety is handled correctly, and the test suite is generally thorough. But there are two real bugs hiding in plain sight.

**The `test_bad_gzip_does_not_trigger_stale_fallback` test is the most important fix** — it names a critical contract (bad gzip must not trigger stale fallback) but tests a completely different thing (`_fetch()` in isolation). That invariant is currently unverified.

**The ADEME fallback error path** is a latent bug that will produce confusing errors in production: a raw `pa.ArrowInvalid` traceback from inside `_parse_csv` with no `DataSourceError` wrapping and no stale-cache attempt.

**The `params` API lie** is worth fixing before more call sites are built on top of it — an analyst will inevitably pass `make_eurostat_config("ilc_di01", geo="FR", time_period="2022")` expecting filtered data and get the full multi-country, multi-year dataset cached under a misleading key.

]]></file>
<file id="557aedd2" path="[Validator B]" label="VALIDATION OUTPUT"><![CDATA[

**🔥 ADVERSARIAL CODE REVIEW COMPLETE, Lucas!**

**Story:** /Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/11-3-implement-eurostat-ademe-sdes-data-source-loaders.md

---

## 📊 Review Summary

| Category | Issues Found |
|----------|--------------|
| Git vs Story Discrepancies | 0 |
| AC Implementation Gaps | 2 |
| Task Completion Lies | 2 |
| SOLID Violations | 0 |
| Hidden Bugs | 0 |
| Performance Footguns | 0 |
| Security Vulnerabilities | 0 |
| **Total Issues** | **4** |

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🔴 CRITICAL | `tests/population/loaders/test_sdes.py` is syntactically invalid (only the token `from` then EOF) so pytest will raise `SyntaxError`; SDES loader has zero runtime coverage despite tasks marked done. | tests/population/loaders/test_sdes.py:1 | +3 |
| 🔴 CRITICAL | `tests/population/loaders/test_eurostat.py` contains duplicated class blocks and ends with an unfinished class declaration (`class TestEurostatLoaderFetchMissingValues:` with no body), producing a `SyntaxError` that prevents any Eurostat tests from running. | tests/population/loaders/test_eurostat.py:80 | +3 |
| 🟠 IMPORTANT | SDES acceptance criteria (#3, #4, #5) unverified: no tests for schema, parsing, skip_rows, network error, or cache lifecycle even though Task 6.3 is checked off. | Story 11.3 tasks vs missing tests | +1 |
| 🟠 IMPORTANT | Eurostat AC (#1, #4, #5) partially unverified: promised tests for missing values, bad gzip handling, and download lifecycle are truncated/absent due to the broken test file. | tests/population/loaders/test_eurostat.py | +1 |
| 🟢 CLEAN PASS | 8 clean categories (SOLID, Hidden Bugs, Abstraction, Performance, Tech Debt, Style, Type Safety, Security) | | -4 |

### Evidence Score: 4.0

| Score | Verdict |
|-------|---------|
| **4.0** | **MAJOR REWORK** |

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

- **🐛 Bug:** SDES tests fail to import (file contains only `from` then EOF), so the SDES loader is completely untested and any regression would ship unnoticed.
  - 📍 `tests/population/loaders/test_sdes.py:1`
- **🐛 Bug:** Eurostat tests fail to import due to duplicate classes and an unfinished class definition, leaving Eurostat loaders effectively untested.
  - 📍 `tests/population/loaders/test_eurostat.py:80`

---

## 🔧 Maintainability Issues

✅ Code is maintainable and well-documented.

---

## 🛠️ Suggested Fixes

### 1. Repair SDES test suite
**File:** `tests/population/loaders/test_sdes.py`  
**Issue:** File is syntactically invalid and empty; none of the required SDES tests run.  
**Fix:** Recreate the test module with the planned cases (protocol, schema, fetch parsing, skip_rows, network error, download lifecycle, catalog, config). Ensure it imports fixtures from `tests/population/loaders/conftest.py`.

### 2. Repair Eurostat test suite
**File:** `tests/population/loaders/test_eurostat.py`  
**Issue:** Duplicate class blocks and a dangling class declaration produce `SyntaxError`, blocking all Eurostat tests.  
**Fix:** Remove duplicate definitions, complete the missing `TestEurostatLoaderFetchMissingValues` and catalog/config classes, and ensure coverage for missing values, bad gzip handling, network errors, and cache lifecycle as promised in Story 11.3.

### 3. Re-run AC coverage audit
**File:** `tests/population/loaders/` (suite)  
**Issue:** Acceptance Criteria (#3–#5) for SDES and parts of Eurostat are unverified.  
**Fix:** After fixing the test modules, add explicit assertions for:
- SDES `skip_rows` behavior and null handling.
- Eurostat missing-value (`:`) handling and `gzip.BadGzipFile` raising `DataSourceValidationError`.
- Download→cache→offline fallback flows for all three providers.

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
 src/reformlab/population/__init__.py               | 109 +++++
 src/reformlab/population/loaders/__init__.py       |  96 ++++
 src/reformlab/population/loaders/ademe.py          | 317 ++++++++++++
 src/reformlab/population/loaders/base.py           | 296 +++++++++++
 src/reformlab/population/loaders/cache.py          | 300 ++++++++++++
 src/reformlab/population/loaders/errors.py         |  47 ++
 src/reformlab/population/loaders/eurostat.py       | 325 ++++++++++++
 src/reformlab/population/loaders/insee.py          | 454 +++++++++++++++++
 src/reformlab/population/loaders/sdes.py           | 290 +++++++++++
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
 tests/population/loaders/test_ademe.py             | 348 +++++++++++++
 tests/population/loaders/test_ademe_network.py     |  38 ++
 tests/population/loaders/test_base.py              | 220 +++++++++
 tests/population/loaders/test_cache.py             | 393 +++++++++++++++
 tests/population/loaders/test_cached_loader.py     | 311 ++++++++++++
 tests/population/loaders/test_errors.py            |  62 +++
 tests/population/loaders/test_eurostat.py          | 442 +++++++++++++++++
 tests/population/loaders/test_eurostat_network.py  |  48 ++
 tests/population/loaders/test_insee.py             | 545 +++++++++++++++++++++
 tests/population/loaders/test_insee_network.py     |  35 ++
 tests/population/loaders/test_sdes.py              | 385 +++++++++++++++
 tests/population/loaders/test_sdes_network.py      |  38 ++
 42 files changed, 5787 insertions(+), 92 deletions(-)

diff --git a/src/reformlab/population/__init__.py b/src/reformlab/population/__init__.py
new file mode 100644
index 0000000..2c36e0d
--- /dev/null
+++ b/src/reformlab/population/__init__.py
@@ -0,0 +1,109 @@
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
index 0000000..0806ac6
--- /dev/null
+++ b/src/reformlab/population/loaders/ademe.py
@@ -0,0 +1,317 @@
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
+            table = pcsv.read_csv(
+                io.BytesIO(csv_bytes),
+                read_options=fallback_options,
+                parse_options=parse_options,
+                convert_options=convert_options,
+            )
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
+        A key from ``ADEME_AVAILABLE_DATASETS`` (e.g. ``"base_carbone"``).
+    cache : SourceCache
+        Cache infrastructure for downloaded data.
+    logger : logging.Logger | None
+        Optional logger. Defaults to ``reformlab.population.loaders.ademe``.
+
+    Raises
+    ------
+    DataSourceValidationError
+        If ``dataset_id`` is not in the catalog.
+    """
+    if dataset_id not in ADEME_CATALOG:
+        raise DataSourceValidationError(
+            summary="Unknown ADEME dataset",
+            reason=f"Requested dataset '{dataset_id}' is not in the ADEME catalog",
+            fix=f"Available datasets: {', '.join(ADEME_AVAILABLE_DATASETS)}",
+        )
+    if logger is None:
+        logger = logging.getLogger("reformlab.population.loaders.ademe")
+    return ADEMELoader(
+        cache=cache,
+        logger=logger,
+        dataset=ADEME_CATALOG[dataset_id],
+    )
+
+
+def make_ademe_config(dataset_id: str, **params: str) -> SourceConfig:
+    """Convenience: construct a ``SourceConfig`` from a catalog dataset ID.
+
+    Parameters
+    ----------
+    dataset_id : str
+        A key from ``ADEME_AVAILABLE_DATASETS``.
+    **params : str
+        Additional query parameters for the download request.
+
+    Raises
+    ------
+    DataSourceValidationError
+        If ``dataset_id`` is not in the catalog.
+    """
+    if dataset_id not in ADEME_CATALOG:
+        raise DataSourceValidationError(
+            summary="Unknown ADEME dataset",
+            reason=f"Requested dataset '{dataset_id}' is not in the ADEME catalog",
+            fix=f"Available datasets: {', '.join(ADEME_AVAILABLE_DATASETS)}",
+        )
+    ds = ADEME_CATALOG[dataset_id]
+    return SourceConfig(
+        provider="ademe",
+        dataset_id=ds.dataset_id,
+        url=ds.url,
+        params=params,
+        description=ds.description,
+    )

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
<var name="session_id">3903a006-a2aa-4666-917a-d77f85d1860c</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_file" file_id="7243a2d9">embedded in prompt, file id: 7243a2d9</var>
<var name="story_id">11.3</var>
<var name="story_key">11-3-implement-eurostat-ademe-sdes-data-source-loaders</var>
<var name="story_num">3</var>
<var name="story_title">implement-eurostat-ademe-sdes-data-source-loaders</var>
<var name="template">False</var>
<var name="timestamp">20260303_1503</var>
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
      - Commit message format: fix(component): brief description (synthesis-11.3)
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