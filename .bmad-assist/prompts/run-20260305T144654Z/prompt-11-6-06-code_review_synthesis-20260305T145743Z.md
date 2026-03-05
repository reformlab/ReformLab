<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 11 -->
<!-- Story: 6 -->
<!-- Phase: code-review-synthesis -->
<!-- Timestamp: 20260305T145743Z -->
<compiled-workflow>
<mission><![CDATA[

Master Code Review Synthesis: Story 11.6

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
<file id="99d0a2db" path="_bmad-output/implementation-artifacts/11-6-build-populationpipeline-builder-with-assumption-recording.md" label="STORY FILE"><![CDATA[



# Story 11.6: Build PopulationPipeline builder with assumption recording

Status: complete

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform developer building the French household population pipeline,
I want a composable `PopulationPipeline` builder that chains data source loaders and merge methods with full assumption recording,
so that analysts can build realistic synthetic populations from multiple institutional data sources with transparent, governance-integrated assumption tracking at every merge step, and the full chain from raw data to final population is traceable and auditable.

## Acceptance Criteria

1. Given a sequence of loaders and merge methods, when composed into a `PopulationPipeline`, then the pipeline executes each step in order and produces a final merged population as a `pa.Table`.
2. Given a pipeline execution, when completed, then every merge step's assumption record is captured in governance-compatible format via `MergeAssumption.to_governance_entry()` — the resulting dicts are directly appendable to `RunManifest.assumptions` (NOT passed to `capture_assumptions()`, which takes flat key-value pairs incompatible with structured merge assumptions).
3. Given a pipeline, when inspected after execution, then the full chain of steps is visible: which source → which method → which output, for every merge — including step index, step type, input labels, output row/column counts, method name, and duration.
4. Given a pipeline step that fails (e.g., schema mismatch between two tables), when executed, then the error identifies the exact step index, step label, step type, the two tables involved (by label), and wraps the underlying cause exception.
5. Given a population produced by the pipeline, when its governance record is queried, then all assumption records from all merge steps are retrievable as a `PipelineAssumptionChain` with per-step context (step index, step label) and a single `to_governance_entries()` call produces all entries.

## Tasks / Subtasks

- [x] Task 1: Create `assumptions.py` — assumption recording for governance integration (AC: #2, #5)
  - [x] 1.1 Create `src/reformlab/population/assumptions.py` with module docstring referencing Story 11.6, FR41 — explain the module bridges population pipeline merge assumptions to the governance layer's `RunManifest.assumptions` format.
  - [x] 1.2 Implement `PipelineAssumptionRecord` frozen dataclass:
    ```python
    @dataclass(frozen=True)
    class PipelineAssumptionRecord:
        """Records a single assumption from a pipeline step with execution context.

        Attributes:
            step_index: Zero-based index of the merge step in the pipeline.
            step_label: Human-readable label for the step's output table.
            assumption: The MergeAssumption produced by the merge method.
        """
        step_index: int
        step_label: str
        assumption: MergeAssumption
    ```
    Validate in `__post_init__`: `step_index >= 0`, `step_label` is non-empty string.
  - [x] 1.3 Implement `PipelineAssumptionChain` frozen dataclass:
    ```python
    @dataclass(frozen=True)
    class PipelineAssumptionChain:
        """Complete assumption chain from a pipeline execution.

        Collects all merge assumptions from a pipeline run and provides
        a single method to convert them to governance-compatible format
        for appending to ``RunManifest.assumptions``.

        Attributes:
            records: Ordered tuple of assumption records from each merge step.
            pipeline_description: Human-readable description of the pipeline.
        """
        records: tuple[PipelineAssumptionRecord, ...]
        pipeline_description: str = ""
    ```
    Ensure `records` is a tuple in `__post_init__` via `object.__setattr__(self, "records", tuple(self.records))` — coerces any iterable and prevents external list aliasing. Deep-copy is unnecessary since all contents are frozen dataclasses (and `MergeAssumption.details` is already deep-copied in its own `__post_init__`).
  - [x] 1.4 Implement `PipelineAssumptionChain.to_governance_entries()`:
    ```python
    def to_governance_entries(
        self, *, source_label: str = "population_pipeline"
    ) -> list[dict[str, Any]]:
        """Convert all assumptions to governance-compatible AssumptionEntry format.

        Each entry is a dict with keys: ``key``, ``value``, ``source``, ``is_default``.
        The ``value`` dict includes pipeline step context (step_index, step_label).

        The returned list can be directly appended to ``RunManifest.assumptions``.
        Due to mypy strict mode, callers should use ``cast(AssumptionEntry, entry)``
        when appending to typed manifest fields.
        """
        entries: list[dict[str, Any]] = []
        for record in self.records:
            entry = record.assumption.to_governance_entry(
                source_label=source_label,
            )
            # Enrich with pipeline step context
            entry["value"]["pipeline_step_index"] = record.step_index
            entry["value"]["pipeline_step_label"] = record.step_label
            if self.pipeline_description:
                entry["value"]["pipeline_description"] = self.pipeline_description
            entries.append(entry)
        return entries
    ```
    **Note on key uniqueness:** The `key` field is `merge_{method_name}` inherited from `MergeAssumption.to_governance_entry()`. When the same method is used multiple times (e.g., two uniform merges), multiple entries share the same `key` — this is intentional and accepted by `RunManifest` validation, which does not enforce key uniqueness. Downstream consumers should use `pipeline_step_index` within each entry's `value` to distinguish entries.
  - [x] 1.5 Implement `PipelineAssumptionChain.__len__()` returning `len(self.records)` for convenience.
  - [x] 1.6 Implement `PipelineAssumptionChain.__iter__()` returning `iter(self.records)` for iteration.

- [x] Task 2: Create pipeline error hierarchy in `pipeline.py` (AC: #4)
  - [x] 2.1 Define `PipelineError(Exception)` base with keyword-only `summary`, `reason`, `fix` arguments following the same pattern as `MergeError` and `DataSourceError`:
    ```python
    class PipelineError(Exception):
        """Base exception for population pipeline operations."""
        def __init__(self, *, summary: str, reason: str, fix: str) -> None:
            self.summary = summary
            self.reason = reason
            self.fix = fix
            super().__init__(f"{summary} - {reason} - {fix}")
    ```
  - [x] 2.2 Define `PipelineConfigError(PipelineError)` — raised for invalid pipeline configuration (duplicate labels, missing references, empty pipeline).
  - [x] 2.3 Define `PipelineExecutionError(PipelineError)` — raised when a pipeline step fails during execution. Additional attributes:
    ```python
    class PipelineExecutionError(PipelineError):
        """Raised when a pipeline step fails during execution.

        Wraps the underlying cause and adds step context so the analyst
        can identify exactly which step, which tables, and which error
        caused the failure.
        """
        def __init__(
            self,
            *,
            summary: str,
            reason: str,
            fix: str,
            step_index: int,
            step_label: str,
            step_type: str,
            cause: Exception,
            tables_involved: tuple[str, ...] = (),
        ) -> None:
            self.step_index = step_index
            self.step_label = step_label
            self.step_type = step_type
            self.cause = cause
            self.tables_involved = tables_involved
            super().__init__(summary=summary, reason=reason, fix=fix)
    ```

- [x] Task 3: Define pipeline step types in `pipeline.py` (AC: #1, #3)
  - [x] 3.1 Create `src/reformlab/population/pipeline.py` with module docstring referencing Story 11.6, FR40, FR41 — explain the module provides a composable builder for constructing populations from multiple institutional data sources using statistical merge methods.
  - [x] 3.2 Implement `PipelineStepLog` frozen dataclass — records the outcome of a completed step:
    ```python
    @dataclass(frozen=True)
    class PipelineStepLog:
        """Log entry for a completed pipeline step.

        Records the outcome of each step for traceability (AC #3).

        Attributes:
            step_index: Zero-based position in execution order.
            step_type: Either ``"load"`` or ``"merge"``.
            label: Human-readable label for this step's output.
            input_labels: Empty tuple for load steps; ``(left, right)`` for merge steps.
            output_rows: Number of rows in the step's output table.
            output_columns: Column names in the step's output table.
            method_name: Merge method name (``None`` for load steps).
            duration_ms: Execution time in milliseconds.
        """
        step_index: int
        step_type: str
        label: str
        input_labels: tuple[str, ...]
        output_rows: int
        output_columns: tuple[str, ...]
        method_name: str | None
        duration_ms: float
    ```
  - [x] 3.3 Implement `PipelineResult` frozen dataclass — immutable result of pipeline execution:
    ```python
    @dataclass(frozen=True)
    class PipelineResult:
        """Immutable result of a population pipeline execution.

        Attributes:
            table: The final merged population table.
            assumption_chain: All merge assumptions with step context.
            step_log: Ordered log of all completed steps.
        """
        table: pa.Table
        assumption_chain: PipelineAssumptionChain
        step_log: tuple[PipelineStepLog, ...]
    ```

- [x] Task 4: Implement `PopulationPipeline` builder class (AC: #1, #3, #4)
  - [x] 4.1 Implement `PopulationPipeline.__init__()`:
    ```python
    class PopulationPipeline:
        """Composable builder for population generation pipelines.

        Provides a fluent API for chaining data source loading and
        statistical merging operations. Each step produces a labeled
        intermediate table. The final population is the output of
        the last merge step.

        The pipeline records every merge step's assumption for
        governance integration via ``PipelineAssumptionChain``.
        """
        def __init__(self, *, description: str = "") -> None:
            self._description = description
            self._steps: list[_PipelineStepDef] = []
            self._labels: set[str] = set()
    ```
    where `_PipelineStepDef` is a union type (see 4.2).
  - [x] 4.2 Define internal step definition types (NOT public API — prefixed with `_`):
    ```python
    @dataclass(frozen=True)
    class _LoadStepDef:
        label: str
        loader: DataSourceLoader
        config: SourceConfig

    @dataclass(frozen=True)
    class _MergeStepDef:
        label: str
        left_label: str
        right_label: str
        method: MergeMethod
        config: MergeConfig

    _PipelineStepDef = _LoadStepDef | _MergeStepDef
    ```
  - [x] 4.3 Implement `add_source(self, label, loader, config) -> PopulationPipeline` (fluent API):
    - Validate `label` is non-empty string — raise `PipelineConfigError` if not
    - Validate `label` is unique (not in `self._labels`) — raise `PipelineConfigError` if duplicate
    - Append `_LoadStepDef` to `self._steps`
    - Add `label` to `self._labels`
    - Return `self` (fluent)
  - [x] 4.4 Implement `add_merge(self, label, left, right, method, config) -> PopulationPipeline` (fluent API):
    - Validate `label` is non-empty string — raise `PipelineConfigError`
    - Validate `label` is unique — raise `PipelineConfigError`
    - Validate `left` exists in `self._labels` — raise `PipelineConfigError` with message identifying the missing label
    - Validate `right` exists in `self._labels` — raise `PipelineConfigError`
    - Validate `left != right` — raise `PipelineConfigError`
    - Append `_MergeStepDef` to `self._steps`
    - Add `label` to `self._labels`
    - Return `self` (fluent)
  - [x] 4.5 Implement `execute(self) -> PipelineResult`:
    - Validate pipeline has at least one merge step — raise `PipelineConfigError` if only load steps
    - Initialize: `tables: dict[str, pa.Table] = {}`, `assumptions: list[PipelineAssumptionRecord] = []`, `step_logs: list[PipelineStepLog] = []`, `step_index = 0`
    - Iterate through `self._steps` in insertion order:
      - For `_LoadStepDef`:
        a. Record `start_time = time.monotonic()`
        b. Call `step.loader.download(step.config)` inside try/except
        c. On success: store `tables[step.label] = table`
        d. On failure: raise `PipelineExecutionError` wrapping the cause, with `step_type="load"`, `step_label=step.label`, `step_index=step_index`
        e. Record `PipelineStepLog` with `step_type="load"`, `input_labels=()`, `method_name=None`, `duration_ms`, `output_rows`, `output_columns`
        f. Increment `step_index`
      - For `_MergeStepDef`:
        a. Record `start_time`
        b. Retrieve `table_a = tables[step.left_label]` and `table_b = tables[step.right_label]`
        c. Call `step.method.merge(table_a, table_b, step.config)` inside try/except
        d. On success: store `tables[step.label] = result.table`, append `PipelineAssumptionRecord(step_index=step_index, step_label=step.label, assumption=result.assumption)` to assumptions
        e. On failure: raise `PipelineExecutionError` wrapping the cause, with `step_type="merge"`, `step_label=step.label`, `step_index=step_index`, `tables_involved=(step.left_label, step.right_label)`
        f. Record `PipelineStepLog` with `step_type="merge"`, `input_labels=(step.left_label, step.right_label)`, `method_name=step.method.name`, `duration_ms`, `output_rows`, `output_columns`
        g. Increment `step_index`
    - Determine final table: scan `self._steps` to find the last `_MergeStepDef` in insertion order and use `tables[last_merge_step.label]`. Do NOT use `self._steps[-1].label` — load steps may follow the last merge.
    - Build `PipelineAssumptionChain` from collected assumptions
    - Return `PipelineResult(table=final_table, assumption_chain=chain, step_log=tuple(step_logs))`
    - **mypy strict note:** Use `isinstance(step, _LoadStepDef)` / `isinstance(step, _MergeStepDef)` to narrow the `_PipelineStepDef` union in the loop — required for mypy strict to access type-specific attributes.
  - [x] 4.6 Implement `step_count` property returning `len(self._steps)`
  - [x] 4.7 Implement `labels` property returning `frozenset(self._labels)` for inspection
  - [x] 4.8 Use `logging.getLogger(__name__)` with structured log entries:
    - `event=pipeline_execute_start steps={n} description={desc}`
    - `event=pipeline_step_start step_index={i} step_type={type} label={label}`
    - `event=pipeline_step_complete step_index={i} label={label} rows={n} cols={n} duration_ms={d}`
    - `event=pipeline_step_error step_index={i} label={label} error={type}`
    - `event=pipeline_execute_complete total_steps={n} final_rows={n} assumptions={n} duration_ms={d}`

- [x] Task 5: Update `__init__.py` exports (AC: all)
  - [x] 5.1 Export from `src/reformlab/population/__init__.py`: add `PopulationPipeline`, `PipelineResult`, `PipelineStepLog`, `PipelineAssumptionChain`, `PipelineAssumptionRecord`, `PipelineError`, `PipelineConfigError`, `PipelineExecutionError` — update `__all__` listing.

- [x] Task 6: Create test fixtures for pipeline tests (AC: all)
  - [x] 6.1 Add to `tests/population/conftest.py`:
    - `mock_loader_a` — a minimal object satisfying `DataSourceLoader` protocol that returns a fixed `pa.Table` with columns: `household_id` (int64), `income` (float64), `region_code` (utf8) — 5 rows. Uses a `_MockLoader` class with `download()` returning the table, `status()` returning a minimal `CacheStatus`, `schema()` returning the table's schema.
    - `mock_loader_b` — returns a table with columns: `vehicle_type` (utf8), `vehicle_age` (int64), `fuel_type` (utf8) — 8 rows.
    - `mock_loader_c` — returns a table with columns: `income_bracket` (utf8), `heating_type` (utf8), `energy_kwh` (float64) — 6 rows.
    - `mock_loader_shared` — returns a table with columns: `income_bracket` (utf8), `vehicle_type` (utf8), `energy_kwh` (float64) — 12 rows. (Same as `energy_vehicle_table` from methods conftest, for conditional sampling.)
    - `mock_failing_loader` — a mock loader whose `download()` raises `DataSourceDownloadError`.
    - `mock_source_config_a`, `mock_source_config_b`, `mock_source_config_c`, `mock_source_config_shared` — `SourceConfig` instances for each mock loader. Example:
      ```python
      @pytest.fixture()
      def mock_source_config_a() -> SourceConfig:
          return SourceConfig(provider="mock", dataset_id="income", url="mock://income")
      ```
      Use `provider="mock"` and `url="mock://{name}"` for all mock configs.

- [x] Task 7: Write comprehensive pipeline tests (AC: #1, #3, #4)
  - [x] 7.1 `tests/population/test_pipeline.py`:
    - `TestPipelineStepLog`: frozen, holds all fields, `step_type` is "load" or "merge"
    - `TestPipelineResult`: frozen, holds table + assumption_chain + step_log
    - `TestPipelineErrorHierarchy`:
      - `PipelineError` inherits `Exception`, summary-reason-fix pattern
      - `PipelineConfigError` inherits `PipelineError`
      - `PipelineExecutionError` inherits `PipelineError`, has `step_index`, `step_label`, `step_type`, `cause`, `tables_involved`
    - `TestPopulationPipelineConstruction`:
      - Constructor accepts optional `description`
      - `step_count` starts at 0
      - `labels` starts empty
    - `TestPopulationPipelineAddSource`:
      - Adds source, label appears in `labels`, `step_count` increments
      - Fluent API: `add_source()` returns `self`
      - Empty label raises `PipelineConfigError`
      - Duplicate label raises `PipelineConfigError`
    - `TestPopulationPipelineAddMerge`:
      - After adding two sources, can add a merge referencing them
      - Fluent API: `add_merge()` returns `self`
      - Missing left label raises `PipelineConfigError`
      - Missing right label raises `PipelineConfigError`
      - Same left and right label raises `PipelineConfigError`
      - Empty label raises `PipelineConfigError`
      - Duplicate label raises `PipelineConfigError`
    - `TestPopulationPipelineExecuteBasic`:
      - Two sources + one uniform merge → result table has correct row count (= table_a rows) and correct columns (all from A + all from B)
      - `result.step_log` has 3 entries (2 loads + 1 merge)
      - Load step logs have `step_type="load"`, `method_name=None`, `input_labels=()`
      - Merge step log has `step_type="merge"`, `method_name="uniform"`, `input_labels=(left, right)`
      - All step logs have `output_rows > 0`, `output_columns` non-empty, `duration_ms >= 0`
    - `TestPopulationPipelineExecuteMultiMerge`:
      - Three sources + two merges (A+B→AB, AB+C→final) → result table has columns from all three sources
      - `result.step_log` has 5 entries
      - `result.assumption_chain` has 2 records (one per merge)
    - `TestPopulationPipelineExecuteWithConditionalSampling`:
      - Source A (with `income_bracket`) + source B (with `income_bracket`) → conditional merge → strata respected in output
    - `TestPopulationPipelineExecuteWithIPF`:
      - Source A (with `income_bracket`) + source B → IPF merge with marginal constraints → result marginals match within ±1
    - `TestPopulationPipelineExecuteDeterminism`:
      - Same pipeline configuration → identical result
      - Different seed in merge config → different result
    - `TestPopulationPipelineExecuteNoMerge`:
      - Pipeline with only load steps (no merges) → `PipelineConfigError` on execute
    - `TestPopulationPipelineExecuteLoadFailure`:
      - Pipeline with a failing loader → `PipelineExecutionError` with correct `step_index`, `step_label`, `step_type="load"`, wraps original exception
    - `TestPopulationPipelineExecuteMergeFailure`:
      - Pipeline with intentionally conflicting column names (no drop_right_columns) → `PipelineExecutionError` with correct `step_index`, `step_label`, `step_type="merge"`, `tables_involved` includes both labels, wraps `MergeValidationError`
    - `TestPopulationPipelineExecuteLoadAfterMerge`:
      - Pipeline with a load step added after the last merge → final table is still the last merge output, not the post-merge load
      - Verify `result.table.num_columns` matches merged columns, not the extra load's columns
    - `TestPopulationPipelineExecuteStepOrder`:
      - Steps execute in insertion order: verify via step_log indices matching insertion order
    - `TestPopulationPipelineFluentAPI`:
      - Full fluent chain: `PopulationPipeline().add_source(...).add_source(...).add_merge(...).execute()` works

- [x] Task 8: Write comprehensive assumption tests (AC: #2, #5)
  - [x] 8.1 `tests/population/test_assumptions.py`:
    - `TestPipelineAssumptionRecord`:
      - Frozen dataclass
      - Holds `step_index`, `step_label`, `assumption`
      - Negative `step_index` raises `ValueError`
      - Empty `step_label` raises `ValueError`
    - `TestPipelineAssumptionChain`:
      - Frozen dataclass
      - Empty records tuple is valid (no merge steps = no assumptions)
      - `len()` returns record count
      - Iterable over records
      - `pipeline_description` defaults to empty string
    - `TestPipelineAssumptionChainGovernanceEntries`:
      - Given chain with 2 records, `to_governance_entries()` returns 2 dicts
      - Each dict has `key`, `value`, `source`, `is_default` fields
      - `is_default` is `False` for all entries
      - Default `source` is `"population_pipeline"`
      - Custom `source_label` is respected
      - Each entry's `value` dict contains `pipeline_step_index` and `pipeline_step_label`
      - When `pipeline_description` is set, it appears in each entry's `value`
      - Entries are ordered by step_index
      - Each entry's `key` matches `merge_{method_name}` pattern
    - `TestPipelineAssumptionChainIntegrationWithManifest`:
      - Given governance entries from a chain, when validated against `RunManifest` assumptions schema, then all entries pass validation (key is non-empty string, value is JSON-compatible, source is non-empty string, is_default is bool)
      - **Setup pattern:** Construct a minimal `RunManifest` with the pipeline entries as assumptions. Reference `tests/governance/conftest.py:minimal_manifest` for required fields. Use `cast(AssumptionEntry, entry)` for mypy strict:
        ```python
        from typing import cast
        from reformlab.governance.manifest import AssumptionEntry, RunManifest
        manifest = RunManifest(
            manifest_id="test-pipeline-001",
            created_at="2026-01-01T00:00:00Z",
            engine_version="0.1.0",
            openfisca_version="44.0.0",
            adapter_version="1.0.0",
            scenario_version="v1",
            assumptions=[cast(AssumptionEntry, e) for e in governance_entries],
        )
        ```
    - `TestPipelineResultAssumptionAccess`:
      - Given a `PipelineResult`, `result.assumption_chain.records` is accessible
      - `result.assumption_chain.to_governance_entries()` works end-to-end

- [x] Task 9: Run full test suite and lint (AC: all)
  - [x] 9.1 `uv run pytest tests/population/test_pipeline.py tests/population/test_assumptions.py` — all new tests pass
  - [x] 9.2 `uv run pytest tests/population/` — no regressions in loader or method tests
  - [x] 9.3 `uv run ruff check src/reformlab/population/ tests/population/` — no lint errors
  - [x] 9.4 `uv run mypy src/reformlab/population/` — no mypy errors (strict mode)

## Dev Notes

### Architecture Context: Pipeline Layer

This story creates the **composition layer** that connects the data source loaders (Stories 11.1–11.3) with the statistical merge methods (Stories 11.4–11.5). Two new files are added at the population module level:

```
src/reformlab/population/
├── __init__.py        ← Updated: add new exports
├── assumptions.py     ← NEW (this story) — governance bridge
├── pipeline.py        ← NEW (this story) — builder + execution
├── loaders/           ← UNCHANGED (Stories 11.1–11.3)
│   ├── base.py
│   ├── cache.py
│   ├── insee.py
│   ├── eurostat.py
│   ├── ademe.py
│   └── sdes.py
├── methods/           ← UNCHANGED (Stories 11.4–11.5)
│   ├── base.py
│   ├── uniform.py
│   ├── ipf.py
│   └── conditional.py
└── validation.py      ← NOT YET CREATED (Story 11.7)
```

### Design Pattern: Fluent Builder with Immutable Result

The pipeline follows a **builder pattern**: mutable `PopulationPipeline` accumulates steps via fluent `add_source()` / `add_merge()` calls, then `execute()` produces an immutable `PipelineResult`. This matches existing codebase patterns:

- **Orchestrator analogy:** `OrchestratorConfig.step_pipeline` is a tuple of steps built up, then executed. The pipeline builder is similar but for data composition rather than yearly simulation.
- **DatasetRegistry analogy:** `DatasetRegistry` is mutable (append-only), while `DatasetManifest` is frozen. The pipeline builder is mutable, while `PipelineResult` and `PipelineAssumptionChain` are frozen.

### Governance Integration: NOT via `capture_assumptions()`

**CRITICAL:** The governance integration uses `MergeAssumption.to_governance_entry()` which produces dicts matching the `AssumptionEntry` TypedDict format (`key`, `value`, `source`, `is_default`). These dicts are **appended directly** to `RunManifest.assumptions`.

Do **NOT** use `capture_assumptions()` from `governance/capture.py` — that function takes flat `dict[str, Any]` key-value pairs (e.g., `{"discount_rate": 0.03}`) and produces assumption entries from defaults/overrides. It is incompatible with the structured merge assumption records which have nested `value` dicts containing method details, constraints, convergence diagnostics, etc.

The bridge works as follows:
```python
# In caller code (e.g., Story 11.8 notebook or future orchestrator)
pipeline_result = pipeline.execute()
governance_entries = pipeline_result.assumption_chain.to_governance_entries()
# governance_entries is list[dict[str, Any]] matching AssumptionEntry format
# Append to RunManifest.assumptions when building the manifest
```

### Pipeline Execution Model: Sequential DAG

Steps are added in insertion order. Load steps produce labeled tables stored in an internal `dict[str, pa.Table]`. Merge steps reference previously-produced labels by name. Execution follows insertion order — the user must add sources before merge steps that reference them.

**Example pipeline:**
```python
pipeline = (
    PopulationPipeline(description="French household population 2024")
    .add_source("income", loader=insee_loader, config=insee_config)
    .add_source("vehicles", loader=sdes_loader, config=sdes_config)
    .add_merge(
        "income_vehicles",
        left="income", right="vehicles",
        method=ConditionalSamplingMethod(strata_columns=("income_bracket",)),
        config=MergeConfig(seed=42, drop_right_columns=("income_bracket",)),
    )
    .add_source("energy", loader=ademe_loader, config=ademe_config)
    .add_merge(
        "population",
        left="income_vehicles", right="energy",
        method=UniformMergeMethod(),
        config=MergeConfig(seed=43),
    )
)
result = pipeline.execute()
# result.table → final merged population (pa.Table)
# result.assumption_chain → 2 assumptions (one per merge)
# result.step_log → 5 entries (3 loads + 2 merges)
```

The output is always the table produced by the **last merge step** in insertion order. This is natural: the pipeline progressively enriches the population by merging in new sources.

### Error Hierarchy Placement

Pipeline errors (`PipelineError`, `PipelineConfigError`, `PipelineExecutionError`) live in `pipeline.py` rather than a separate `errors.py`. This is intentional: `loaders/` and `methods/` are multi-file subpackages where a dedicated `errors.py` reduces coupling between sibling modules. The pipeline layer is a single-file module (`pipeline.py`) at the population package level — a separate `errors.py` alongside it would add a file for three small classes that are only used by `pipeline.py` itself.

### Error Handling: Step Context Preservation

When a step fails, `PipelineExecutionError` wraps the underlying exception and adds:
- `step_index` — which step failed (zero-based)
- `step_label` — the label of the failing step
- `step_type` — `"load"` or `"merge"`
- `cause` — the original exception (e.g., `MergeValidationError`, `DataSourceDownloadError`)
- `tables_involved` — tuple of label names (empty for load, `(left, right)` for merge)

This fulfills AC #4: the analyst can identify exactly what went wrong and where.

**Error propagation pattern:**
```python
try:
    merge_result = step.method.merge(table_a, table_b, step.config)
except (MergeValidationError, MergeConvergenceError, MergeError) as exc:
    raise PipelineExecutionError(
        summary=f"Pipeline step {step_index} failed",
        reason=f"Merge step {step.label!r} failed: {exc.summary}",
        fix=exc.fix,
        step_index=step_index,
        step_label=step.label,
        step_type="merge",
        cause=exc,
        tables_involved=(step.left_label, step.right_label),
    ) from exc
```

For load step failures:
```python
try:
    table = step.loader.download(step.config)
except Exception as exc:
    raise PipelineExecutionError(
        summary=f"Pipeline step {step_index} failed",
        reason=f"Load step {step.label!r} failed: {exc}",
        fix="Check data source availability, cache status, and network connectivity",
        step_index=step_index,
        step_label=step.label,
        step_type="load",
        cause=exc,
    ) from exc
```

### Internal Step Definition Types

See Task 4.2 for `_LoadStepDef`, `_MergeStepDef`, `_PipelineStepDef`. These are NOT part of the public API — prefixed with `_`.

### Timing Measurement

Use `time.monotonic()` for step duration measurement (not `time.time()` which is affected by system clock adjustments):

```python
import time

start = time.monotonic()
# ... step execution ...
duration_ms = (time.monotonic() - start) * 1000.0
```

### No New Dependencies Required

All implementation uses existing dependencies and stdlib:

- `time` — monotonic clock for duration measurement (stdlib)
- `dataclasses` — frozen dataclasses (stdlib)
- `logging` — structured logging (stdlib)
- `pyarrow` — `pa.Table` (existing dependency)

Import patterns:
- `pyarrow` imported at runtime in `pipeline.py` (same as merge methods)
- `pyarrow` under `TYPE_CHECKING` guard in `assumptions.py` (only used in `PipelineResult` type, which is in `pipeline.py`)
- Actually, `assumptions.py` doesn't need pyarrow at all — it only references `MergeAssumption` from `methods/base.py`

### Test Fixtures: Mock Loaders

Tests must NOT use real data source loaders (no network, no cache). Instead, use mock loaders that satisfy the `DataSourceLoader` protocol:

```python
class _MockLoader:
    """Minimal DataSourceLoader for pipeline testing."""

    def __init__(self, table: pa.Table) -> None:
        self._table = table

    def download(self, config: SourceConfig) -> pa.Table:
        return self._table

    def status(self, config: SourceConfig) -> CacheStatus:
        return CacheStatus(
            cached=True,
            path=None,
            downloaded_at=None,
            hash=None,
            stale=False,
        )

    def schema(self) -> pa.Schema:
        return self._table.schema


class _FailingLoader:
    """Mock loader that always raises on download."""

    def download(self, config: SourceConfig) -> pa.Table:
        raise DataSourceDownloadError(
            summary="Download failed",
            reason="mock failure for testing",
            fix="this is a test mock",
        )

    def status(self, config: SourceConfig) -> CacheStatus:
        return CacheStatus(
            cached=False, path=None, downloaded_at=None, hash=None, stale=False,
        )

    def schema(self) -> pa.Schema:
        return pa.schema([])
```

### AssumptionEntry Validation Compatibility

The `RunManifest._validate()` method (in `governance/manifest.py`) validates each assumption entry for:
- `key`: non-empty string
- `value`: JSON-compatible (str, int, float, bool, None, list, dict — validated recursively)
- `source`: non-empty string
- `is_default`: boolean

The `to_governance_entries()` output must satisfy all these constraints. The existing `MergeAssumption.to_governance_entry()` already produces valid entries. The pipeline enrichment (adding `pipeline_step_index` and `pipeline_step_label` to the `value` dict) uses `int` and `str` — both JSON-compatible.

### Downstream Dependencies

Story 11.6 is consumed by:

- **Story 11.7** (Validation) — validates a population produced by the pipeline against known marginals. May receive a `PipelineResult.table` and check distributions.
- **Story 11.8** (Notebook) — demonstrates the full pipeline end-to-end: load real INSEE/SDES/ADEME data, compose with merge methods, show assumption chain, produce French household population. Uses `PipelineAssumptionChain.to_governance_entries()` for manifest integration.

### Project Structure Notes

**New files (4):**
- `src/reformlab/population/pipeline.py`
- `src/reformlab/population/assumptions.py`
- `tests/population/test_pipeline.py`
- `tests/population/test_assumptions.py`

**Modified files (2):**
- `src/reformlab/population/__init__.py` — add new exports, update `__all__`
- `tests/population/conftest.py` — add mock loader fixtures and source configs

**No changes** to `pyproject.toml` (no new dependencies)

### Alignment with Project Conventions

All rules from `project-context.md` apply:

- Every file starts with `from __future__ import annotations`
- `if TYPE_CHECKING:` guards for annotation-only imports (in `assumptions.py` — no runtime pyarrow needed)
- Frozen dataclasses as default (`@dataclass(frozen=True)`) for all value types: `PipelineStepLog`, `PipelineResult`, `PipelineAssumptionRecord`, `PipelineAssumptionChain`, `_LoadStepDef`, `_MergeStepDef`
- `PopulationPipeline` is a mutable builder class — NOT a frozen dataclass (it accumulates steps)
- Protocols, not ABCs — pipeline accepts any `DataSourceLoader` and `MergeMethod` via duck typing
- Subsystem-specific exceptions (`PipelineError` hierarchy, not bare `Exception`)
- `dict[str, Any]` for metadata bags
- `tuple[...]` for immutable sequences (step_log, records, output_columns)
- `X | None` union syntax
- Module-level docstrings referencing story/FR
- `logging.getLogger(__name__)` with structured key=value format
- `# ====...====` section separators for major sections within longer modules

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#New-Subsystem-Population-Generation] — Directory structure, pipeline.py and assumptions.py placement
- [Source: _bmad-output/planning-artifacts/epics.md#BKL-1106] — Story definition and acceptance criteria
- [Source: _bmad-output/planning-artifacts/prd.md#FR40] — "System produces a complete synthetic population with household-level attributes sufficient for policy simulation"
- [Source: _bmad-output/planning-artifacts/prd.md#FR41] — "Every merge, imputation, and extrapolation is recorded as an explicit assumption in the governance layer"
- [Source: _bmad-output/project-context.md#Python-Language-Rules] — Frozen dataclasses, Protocols, `from __future__ import annotations`
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules] — PyArrow canonical data type, no pandas in core logic
- [Source: src/reformlab/population/methods/base.py] — MergeMethod protocol, MergeConfig, MergeAssumption, MergeResult
- [Source: src/reformlab/population/methods/base.py#to_governance_entry] — Governance bridge pattern (key/value/source/is_default)
- [Source: src/reformlab/population/loaders/base.py] — DataSourceLoader protocol, SourceConfig, CacheStatus, CachedLoader
- [Source: src/reformlab/governance/capture.py] — `capture_assumptions()` API (flat key-value, NOT for structured merge assumptions)
- [Source: src/reformlab/governance/manifest.py#AssumptionEntry] — TypedDict with key/value/source/is_default; JSON-compatibility validation
- [Source: src/reformlab/governance/manifest.py#RunManifest] — Frozen dataclass, assumptions field validation in `_validate()`
- [Source: src/reformlab/population/methods/uniform.py] — Reference merge method implementation (validation order, logging, assumption construction)
- [Source: src/reformlab/population/methods/errors.py] — MergeError hierarchy (summary-reason-fix pattern)
- [Source: src/reformlab/population/loaders/errors.py] — DataSourceError hierarchy (same pattern)
- [Source: src/reformlab/data/pipeline.py] — DatasetManifest/DatasetRegistry pattern (frozen metadata + mutable registry)
- [Source: _bmad-output/implementation-artifacts/11-5-implement-ipf-and-conditional-sampling-merge-methods.md] — Previous story (merge method patterns, test patterns)
- [Source: _bmad-output/implementation-artifacts/11-4-define-mergemethod-protocol-and-uniform-distribution-method.md] — Protocol reference, antipattern about capture_assumptions() mismatch

## File List

**New files (4):**
- `src/reformlab/population/pipeline.py`
- `src/reformlab/population/assumptions.py`
- `tests/population/test_pipeline.py`
- `tests/population/test_assumptions.py`

**Modified files (2):**
- `src/reformlab/population/__init__.py` — add new exports
- `tests/population/conftest.py` — add mock loader fixtures

## Change Log

- 2026-03-05: Story implementation completed — all 9 tasks and 39 subtasks delivered and verified. Comprehensive test coverage with 73 new tests for pipeline and assumption modules. All tests pass (382 total in population module). Ruff and mypy strict validation passed. Full governance integration via `PipelineAssumptionChain.to_governance_entries()` with step context preservation. Error handling with `PipelineExecutionError` capturing step-level context.
- 2026-03-03: Story created by create-story workflow — comprehensive developer context with composable builder pattern design, fluent API specification, governance integration via `to_governance_entry()` (NOT `capture_assumptions()`), error hierarchy with step context preservation, mock loader test fixtures, sequential DAG execution model, timing measurement, and downstream dependency mapping.


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
IPFMergeMethod : class
    Iterative Proportional Fitting reweighting and matching.
IPFConstraint : dataclass
    A marginal constraint for IPF.
IPFResult : dataclass
    Convergence diagnostics from an IPF run.
ConditionalSamplingMethod : class
    Stratum-based conditional sampling merge.
PopulationPipeline : class
    Composable builder for population generation pipelines.
PipelineResult : dataclass
    Immutable result of a pipeline execution.
PipelineStepLog : dataclass
    Log entry for a completed pipeline step.
PipelineAssumptionChain : dataclass
    Complete assumption chain from a pipeline execution.
PipelineAssumptionRecord : dataclass
    Records a single assumption from a pipeline step.
PipelineError : Exception
    Base exception for population pipeline operations.
PipelineConfigError : PipelineError
    Raised for invalid pipeline configuration.
PipelineExecutionError : PipelineError
    Raised when a pipeline step fails during execution.
"""

from __future__ import annotations

from reformlab.population.assumptions import (
    PipelineAssumptionChain,
    PipelineAssumptionRecord,
)
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
    IPFConstraint,
    IPFResult,
    MergeAssumption,
    MergeConfig,
    MergeMethod,
    MergeResult,
)
from reformlab.population.methods.conditional import ConditionalSamplingMethod
from reformlab.population.methods.errors import (
    MergeConvergenceError,
    MergeError,
    MergeValidationError,
)
from reformlab.population.methods.ipf import IPFMergeMethod
from reformlab.population.methods.uniform import UniformMergeMethod
from reformlab.population.pipeline import (
    PipelineConfigError,
    PipelineError,
    PipelineExecutionError,
    PipelineResult,
    PipelineStepLog,
    PopulationPipeline,
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
    "PipelineAssumptionChain",
    "PipelineAssumptionRecord",
    "PipelineConfigError",
    "PipelineError",
    "PipelineExecutionError",
    "PipelineResult",
    "PipelineStepLog",
    "PopulationPipeline",
    "get_ademe_loader",
    "get_eurostat_loader",
    "get_insee_loader",
    "get_sdes_loader",
    "ConditionalSamplingMethod",
    "IPFConstraint",
    "IPFMergeMethod",
    "IPFResult",
    "MergeAssumption",
    "MergeConfig",
    "MergeConvergenceError",
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
<file id="b5233ddb" path="src/reformlab/population/assumptions.py" label="SOURCE CODE"><![CDATA[

"""Assumption recording for governance integration.

Bridges population pipeline merge assumptions to the governance layer's
``RunManifest.assumptions`` format. Provides structured records for
each merge step in a pipeline, with execution context (step index, step label)
that enables full traceability from raw data sources to final merged population.

Implements Story 11.6, FR41.

The bridge works as follows:
- ``PipelineAssumptionRecord`` wraps a single merge assumption with step context
- ``PipelineAssumptionChain`` collects all assumptions from a pipeline execution
- ``to_governance_entries()`` produces dicts matching ``AssumptionEntry`` format
- These dicts are appended directly to ``RunManifest.assumptions``

Note: This module does NOT use ``capture_assumptions()`` from
``governance/capture.py`` — that function expects flat key-value pairs,
while merge assumptions are structured with nested metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Iterator

from reformlab.population.methods.base import MergeAssumption

if TYPE_CHECKING:
    # PipelineResult is defined in pipeline.py, which imports this module
    # Use TYPE_CHECKING to avoid circular import
    pass


# ====================================================================
# Pipeline assumption types
# ====================================================================


@dataclass(frozen=True)
class PipelineAssumptionRecord:
    """Records a single assumption from a pipeline step with execution context.

    Wraps a ``MergeAssumption`` produced by a merge method and adds pipeline
    execution context (step index, step label) that enables traceability
    back to the specific merge operation in the pipeline.

    Attributes:
        step_index: Zero-based index of the merge step in the pipeline.
        step_label: Human-readable label for the step's output table.
        assumption: The ``MergeAssumption`` produced by the merge method.
    """

    step_index: int
    step_label: str
    assumption: MergeAssumption

    def __post_init__(self) -> None:
        if self.step_index < 0:
            msg = f"step_index must be >= 0, got {self.step_index}"
            raise ValueError(msg)
        if not self.step_label or self.step_label.strip() == "":
            msg = "step_label must be a non-empty string"
            raise ValueError(msg)


@dataclass(frozen=True)
class PipelineAssumptionChain:
    """Complete assumption chain from a pipeline execution.

    Collects all merge assumptions from a pipeline run and provides
    a single method to convert them to governance-compatible format
    for appending to ``RunManifest.assumptions``.

    The chain preserves execution order, so assumptions are traceable
    by step index and label.

    Attributes:
        records: Ordered tuple of assumption records from each merge step.
        pipeline_description: Human-readable description of the pipeline.
    """

    records: tuple[PipelineAssumptionRecord, ...]
    pipeline_description: str = ""

    def __post_init__(self) -> None:
        # Coerce to tuple to ensure immutability (caller may pass a list)
        # Deep-copy is unnecessary since all contents are frozen dataclasses
        object.__setattr__(self, "records", tuple(self.records))

    def to_governance_entries(self, *, source_label: str = "population_pipeline") -> list[dict[str, Any]]:
        """Convert all assumptions to governance-compatible AssumptionEntry format.

        Each entry is a dict with keys: ``key``, ``value``, ``source``, ``is_default``.
        The ``value`` dict includes pipeline step context (step_index, step_label).

        The returned list can be directly appended to ``RunManifest.assumptions``.
        Due to mypy strict mode, callers should use ``cast(AssumptionEntry, entry)``
        when appending to typed manifest fields.

        Args:
            source_label: Label for the ``source`` field in each entry.
                Defaults to ``"population_pipeline"``.

        Returns:
            List of assumption entry dicts, ordered by step_index.

        Note on key uniqueness:
            The ``key`` field is ``merge_{method_name}`` inherited from
            ``MergeAssumption.to_governance_entry()``. When the same method
            is used multiple times (e.g., two uniform merges), multiple entries
            share the same ``key`` — this is intentional and accepted by
            ``RunManifest`` validation. Downstream consumers should use
            ``pipeline_step_index`` within each entry's ``value`` to
            distinguish entries.
        """
        entries: list[dict[str, Any]] = []
        for record in self.records:
            entry = record.assumption.to_governance_entry(
                source_label=source_label,
            )
            # Enrich with pipeline step context
            entry["value"]["pipeline_step_index"] = record.step_index
            entry["value"]["pipeline_step_label"] = record.step_label
            if self.pipeline_description:
                entry["value"]["pipeline_description"] = self.pipeline_description
            entries.append(entry)
        return entries

    def __len__(self) -> int:
        """Return number of assumption records."""
        return len(self.records)

    def __iter__(self) -> Iterator[PipelineAssumptionRecord]:
        """Iterate over assumption records."""
        return iter(self.records)


]]></file>
<file id="2253c210" path="src/reformlab/population/pipeline.py" label="SOURCE CODE"><![CDATA[

"""Population pipeline builder and execution.

Provides a composable builder for constructing populations from multiple
institutional data sources using statistical merge methods. Each step
produces a labeled intermediate table. The pipeline executes sequentially,
merging sources in insertion order, and produces a final merged population.

The pipeline records every merge step's assumption for governance integration
via ``PipelineAssumptionChain``, enabling full traceability from raw data
to final population.

Implements Story 11.6, FR40, FR41.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from reformlab.population.assumptions import (
    PipelineAssumptionChain,
    PipelineAssumptionRecord,
)
from reformlab.population.loaders.base import (
    DataSourceLoader,
    SourceConfig,
)
from reformlab.population.methods.base import (
    MergeConfig,
    MergeMethod,
)

if TYPE_CHECKING:
    import pyarrow as pa


_logger = logging.getLogger(__name__)


# ====================================================================
# Pipeline error hierarchy
# ====================================================================


class PipelineError(Exception):
    """Base exception for population pipeline operations.

    All pipeline-specific errors inherit from this base class.
    Follows the summary-reason-fix pattern for consistent error messaging.

    Args:
        summary: Brief description of the error.
        reason: Detailed explanation of why the error occurred.
        fix: Suggested resolution or workaround.

    Attributes:
        summary: Brief description of the error.
        reason: Detailed explanation of why the error occurred.
        fix: Suggested resolution or workaround.
    """

    def __init__(self, *, summary: str, reason: str, fix: str) -> None:
        self.summary = summary
        self.reason = reason
        self.fix = fix
        super().__init__(f"{summary} - {reason} - {fix}")


class PipelineConfigError(PipelineError):
    """Raised for invalid pipeline configuration.

    Raised when the pipeline structure is invalid, such as duplicate
    labels, missing references, or empty pipelines.
    """


class PipelineExecutionError(PipelineError):
    """Raised when a pipeline step fails during execution.

    Wraps the underlying cause and adds step context so the analyst
    can identify exactly which step, which tables, and which error
    caused the failure.

    Args:
        summary: Brief description of the error.
        reason: Detailed explanation of why the error occurred.
        fix: Suggested resolution or workaround.
        step_index: Zero-based index of the failing step in the pipeline.
        step_label: Human-readable label for the failing step's output.
        step_type: Either "load" or "merge".
        cause: The original exception that caused the failure.
        tables_involved: Tuple of label names involved in the step.
            Empty tuple for load steps, (left, right) for merge steps.

    Attributes:
        step_index: Zero-based index of the failing step.
        step_label: Human-readable label for the failing step.
        step_type: Either "load" or "merge".
        cause: The original exception that caused the failure.
        tables_involved: Tuple of label names involved in the step.
    """

    def __init__(
        self,
        *,
        summary: str,
        reason: str,
        fix: str,
        step_index: int,
        step_label: str,
        step_type: str,
        cause: Exception,
        tables_involved: tuple[str, ...] = (),
    ) -> None:
        self.step_index = step_index
        self.step_label = step_label
        self.step_type = step_type
        self.cause = cause
        self.tables_involved = tables_involved
        super().__init__(summary=summary, reason=reason, fix=fix)


# ====================================================================
# Pipeline step types
# ====================================================================


@dataclass(frozen=True)
class PipelineStepLog:
    """Log entry for a completed pipeline step.

    Records the outcome of each step for traceability (AC #3).

    Attributes:
        step_index: Zero-based position in execution order.
        step_type: Either "load" or "merge".
        label: Human-readable label for this step's output.
        input_labels: Empty tuple for load steps; (left, right) for merge steps.
        output_rows: Number of rows in the step's output table.
        output_columns: Column names in the step's output table.
        method_name: Merge method name (None for load steps).
        duration_ms: Execution time in milliseconds.
    """

    step_index: int
    step_type: str
    label: str
    input_labels: tuple[str, ...]
    output_rows: int
    output_columns: tuple[str, ...]
    method_name: str | None
    duration_ms: float


@dataclass(frozen=True)
class PipelineResult:
    """Immutable result of a population pipeline execution.

    Attributes:
        table: The final merged population table.
        assumption_chain: All merge assumptions with step context.
        step_log: Ordered log of all completed steps.
    """

    table: pa.Table
    assumption_chain: PipelineAssumptionChain
    step_log: tuple[PipelineStepLog, ...]


# ====================================================================
# Internal step definition types (NOT public API)
# ====================================================================


@dataclass(frozen=True)
class _LoadStepDef:
    """Internal definition for a data source loading step."""

    label: str
    loader: DataSourceLoader
    config: SourceConfig


@dataclass(frozen=True)
class _MergeStepDef:
    """Internal definition for a merge step."""

    label: str
    left_label: str
    right_label: str
    method: MergeMethod
    config: MergeConfig


_PipelineStepDef = _LoadStepDef | _MergeStepDef


# ====================================================================
# Population pipeline builder
# ====================================================================


class PopulationPipeline:
    """Composable builder for population generation pipelines.

    Provides a fluent API for chaining data source loading and
    statistical merging operations. Each step produces a labeled
    intermediate table. The final population is the output of
    the last merge step.

    The pipeline records every merge step's assumption for
    governance integration via ``PipelineAssumptionChain``.

    Example:
        >>> pipeline = (
        ...     PopulationPipeline(description="French household population 2024")
        ...     .add_source("income", loader=insee_loader, config=insee_config)
        ...     .add_source("vehicles", loader=sdes_loader, config=sdes_config)
        ...     .add_merge(
        ...         "income_vehicles",
        ...         left="income", right="vehicles",
        ...         method=ConditionalSamplingMethod(strata_columns=("income_bracket",)),
        ...         config=MergeConfig(seed=42),
        ...     )
        ... )
        >>> result = pipeline.execute()
        >>> result.table  # final merged population (pa.Table)
        >>> result.assumption_chain  # all merge assumptions
        >>> result.step_log  # execution trace
    """

    def __init__(self, *, description: str = "") -> None:
        """Initialize a new pipeline.

        Args:
            description: Human-readable description of the pipeline.
                Used in governance entries when set.
        """
        self._description = description
        self._steps: list[_PipelineStepDef] = []
        self._labels: set[str] = set()

    @property
    def description(self) -> str:
        """Human-readable description of the pipeline."""
        return self._description

    @property
    def step_count(self) -> int:
        """Number of steps in the pipeline."""
        return len(self._steps)

    @property
    def labels(self) -> frozenset[str]:
        """Set of all labels produced by steps in the pipeline."""
        return frozenset(self._labels)

    def add_source(
        self,
        label: str,
        loader: DataSourceLoader,
        config: SourceConfig,
    ) -> PopulationPipeline:
        """Add a data source loading step to the pipeline.

        Args:
            label: Human-readable label for the loaded table.
                Must be unique across all steps.
            loader: Data source loader to use.
            config: Configuration for the data source.

        Returns:
            ``self`` for fluent API chaining.

        Raises:
            PipelineConfigError: If label is empty or duplicate.
        """
        if not label or label.strip() == "":
            msg = "label must be a non-empty string"
            raise PipelineConfigError(
                summary="Invalid source label",
                reason=msg,
                fix="Provide a non-empty label for the source",
            )
        if label in self._labels:
            msg = f"Duplicate label {label!r}"
            raise PipelineConfigError(
                summary="Duplicate label",
                reason=msg,
                fix=f"Use a unique label (existing: {sorted(self._labels)})",
            )

        self._steps.append(_LoadStepDef(label=label, loader=loader, config=config))
        self._labels.add(label)
        return self

    def add_merge(
        self,
        label: str,
        left: str,
        right: str,
        method: MergeMethod,
        config: MergeConfig,
    ) -> PopulationPipeline:
        """Add a merge step to the pipeline.

        Args:
            label: Human-readable label for the merged table.
                Must be unique across all steps.
            left: Label of the left input table (must exist).
            right: Label of the right input table (must exist).
            method: Merge method to apply.
            config: Configuration for the merge operation.

        Returns:
            ``self`` for fluent API chaining.

        Raises:
            PipelineConfigError: If label is invalid, left/right don't exist,
                or left == right.
        """
        if not label or label.strip() == "":
            msg = "label must be a non-empty string"
            raise PipelineConfigError(
                summary="Invalid merge label",
                reason=msg,
                fix="Provide a non-empty label for the merge output",
            )
        if label in self._labels:
            msg = f"Duplicate label {label!r}"
            raise PipelineConfigError(
                summary="Duplicate label",
                reason=msg,
                fix=f"Use a unique label (existing: {sorted(self._labels)})",
            )
        if left not in self._labels:
            msg = f"Missing left label {left!r}"
            raise PipelineConfigError(
                summary="Merge references non-existent left table",
                reason=msg,
                fix=f"Add a source step with label {left!r} before this merge",
            )
        if right not in self._labels:
            msg = f"Missing right label {right!r}"
            raise PipelineConfigError(
                summary="Merge references non-existent right table",
                reason=msg,
                fix=f"Add a source step with label {right!r} before this merge",
            )
        if left == right:
            msg = f"left and right labels must be different, got {left!r}"
            raise PipelineConfigError(
                summary="Invalid merge: same left and right label",
                reason=msg,
                fix=f"Use two different labels (e.g., left={left!r}, right=other)",
            )

        self._steps.append(
            _MergeStepDef(
                label=label,
                left_label=left,
                right_label=right,
                method=method,
                config=config,
            )
        )
        self._labels.add(label)
        return self

    def execute(self) -> PipelineResult:
        """Execute the pipeline and return the final result.

        Executes all steps in insertion order. Load steps download
        data from sources. Merge steps apply statistical methods to
        combine tables. The final population is the output of the
        last merge step.

        Returns:
            ``PipelineResult`` containing the final table, assumption
            chain, and step log.

        Raises:
            PipelineConfigError: If pipeline has no merge steps.
            PipelineExecutionError: If any step fails during execution.
        """

        # Validate pipeline has at least one merge step
        has_merge = any(isinstance(step, _MergeStepDef) for step in self._steps)
        if not has_merge:
            msg = "Pipeline must have at least one merge step"
            raise PipelineConfigError(
                summary="Invalid pipeline configuration",
                reason=msg,
                fix="Add at least one merge step to the pipeline",
            )

        _logger.info(
            "event=pipeline_execute_start steps=%d description=%s",
            len(self._steps),
            self._description or "<no description>",
        )

        tables: dict[str, pa.Table] = {}
        assumptions: list[PipelineAssumptionRecord] = []
        step_logs: list[PipelineStepLog] = []
        step_index = 0

        start_time_total = time.monotonic()

        for step in self._steps:
            _logger.info(
                "event=pipeline_step_start step_index=%d step_type=%s label=%s",
                step_index,
                "load" if isinstance(step, _LoadStepDef) else "merge",
                step.label,
            )

            step_start = time.monotonic()

            try:
                if isinstance(step, _LoadStepDef):
                    # Execute load step
                    table = step.loader.download(step.config)
                    tables[step.label] = table

                    output_columns = tuple(table.column_names)
                    step_logs.append(
                        PipelineStepLog(
                            step_index=step_index,
                            step_type="load",
                            label=step.label,
                            input_labels=(),
                            output_rows=table.num_rows,
                            output_columns=output_columns,
                            method_name=None,
                            duration_ms=(time.monotonic() - step_start) * 1000.0,
                        )
                    )

                elif isinstance(step, _MergeStepDef):
                    # Execute merge step
                    table_a = tables[step.left_label]
                    table_b = tables[step.right_label]

                    merge_result = step.method.merge(table_a, table_b, step.config)
                    tables[step.label] = merge_result.table

                    assumptions.append(
                        PipelineAssumptionRecord(
                            step_index=step_index,
                            step_label=step.label,
                            assumption=merge_result.assumption,
                        )
                    )

                    output_columns = tuple(merge_result.table.column_names)
                    step_logs.append(
                        PipelineStepLog(
                            step_index=step_index,
                            step_type="merge",
                            label=step.label,
                            input_labels=(step.left_label, step.right_label),
                            output_rows=merge_result.table.num_rows,
                            output_columns=output_columns,
                            method_name=step.method.name,
                            duration_ms=(time.monotonic() - step_start) * 1000.0,
                        )
                    )

            except Exception as exc:
                # Determine step type for error reporting
                step_type = "load" if isinstance(step, _LoadStepDef) else "merge"
                tables_involved = (
                    () if isinstance(step, _LoadStepDef) else (step.left_label, step.right_label)
                )

                _logger.error(
                    "event=pipeline_step_error step_index=%d label=%s error=%s",
                    step_index,
                    step.label,
                    type(exc).__name__,
                )

                raise PipelineExecutionError(
                    summary=f"Pipeline step {step_index} failed",
                    reason=f"{step_type.capitalize()} step {step.label!r} failed: {exc}",
                    fix=(
                        f"Check {step_type} configuration and data availability. "
                        f"Tables involved: {tables_involved}"
                    ),
                    step_index=step_index,
                    step_label=step.label,
                    step_type=step_type,
                    cause=exc,
                    tables_involved=tables_involved,
                ) from exc

            _logger.info(
                "event=pipeline_step_complete step_index=%d label=%s rows=%d cols=%d duration_ms=%.2f",
                step_index,
                step.label,
                tables[step.label].num_rows,
                len(tables[step.label].column_names),
                (time.monotonic() - step_start) * 1000.0,
            )

            step_index += 1

        # Find the last merge step in insertion order
        last_merge_step = None
        for step in reversed(self._steps):
            if isinstance(step, _MergeStepDef):
                last_merge_step = step
                break

        if last_merge_step is None:
            # This should never happen due to the has_merge check above
            msg = "No merge step found in pipeline"
            raise PipelineConfigError(
                summary="Invalid pipeline configuration",
                reason=msg,
                fix="Add at least one merge step to the pipeline",
            )

        final_table = tables[last_merge_step.label]

        # Build assumption chain
        assumption_chain = PipelineAssumptionChain(
            records=tuple(assumptions),
            pipeline_description=self._description,
        )

        total_duration_ms = (time.monotonic() - start_time_total) * 1000.0

        _logger.info(
            "event=pipeline_execute_complete total_steps=%d final_rows=%d assumptions=%d duration_ms=%.2f",
            step_index,
            final_table.num_rows,
            len(assumptions),
            total_duration_ms,
        )

        return PipelineResult(
            table=final_table,
            assumption_chain=assumption_chain,
            step_log=tuple(step_logs),
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

**🔥 ADVERSARIAL CODE REVIEW: Story 11.6**

**Story File:** 11-6-build-populationpipeline-builder-with-assumption-recording.md  
**Status Claimed:** complete  
**Review Date:** 2026-03-05

---

## 📊 Review Summary

| Category | Issues Found |
|----------|--------------|
| Code Duplication | 2 |
| Lying Tests | 1 |
| Incomplete Test Coverage | 3 |
| Documentation Gaps | 3 |
| Logging Issues | 1 |
| **Total Issues** | **10** |

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🟠 IMPORTANT | Lying test: test_all_step_logs_have_valid_attributes checks output_columns non-empty but doesn't verify actual column names from table match what's in log | tests/population/test_pipeline.py:307-318 | +1 |
| 🟠 IMPORTANT | Code duplication: _MockLoader and _FailingLoader classes defined identically in both conftest.py AND test_pipeline.py - violates DRY, maintenance burden | tests/population/conftest.py:243-282 vs tests/population/test_pipeline.py:1265-1290 | +1 |
| 🟡 MINOR | Incomplete coverage: to_governance_entries() with empty PipelineAssumptionChain not tested (test exists for empty records but not tested with to_governance_entries) | tests/population/test_assumptions.py | +0.3 |
| 🟡 MINOR | Misleading docstring: TYPE_CHECKING block in assumptions.py claims comment about PipelineResult import but nothing is actually imported, block is dead code | src/reformlab/population/assumptions.py:25-30 | +0.3 |
| 🟡 MINOR | Logging inconsistency: error path in execute() doesn't include duration_ms or tables_involved in log output, only error type | src/reformlab/population/pipeline.py:429-433 | +0.3 |
| 🟡 MINOR | Documentation clarity: Main docstring doesn't explain behavior when load steps added AFTER merge (last merge is still final table, but confusing) | src/reformlab/population/pipeline.py:293-315 | +0.3 |
| 🟡 MINOR | No validation: PipelineExecutionError.step_type parameter not validated to be "load" or "merge" - accepts any string | src/reformlab/population/pipeline.py:107-133 | +0.3 |
| 🟡 MINOR | Missing test: execute() idempotency not tested (calling execute() twice on same pipeline) | tests/population/test_pipeline.py | +0.3 |
| 🟡 MINOR | Unused fixtures: conftest.py defines mock_loader_a, b, c, shared but none are used in any test file - unclear if intentional | tests/population/conftest.py:75-118 | +0.3 |
| 🟢 CLEAN PASS | No SOLID principle violations detected - layer separation clean | - | -0.5 |
| 🟢 CLEAN PASS | No hidden bugs detected - error handling comprehensive, state management correct | - | -0.5 |
| 🟢 CLEAN PASS | No performance footguns - no N+1, no unnecessary allocations, efficient algorithms | - | -0.5 |
| 🟢 CLEAN PASS | No security vulnerabilities found | - | -0.5 |

### **Evidence Score: 1.4 → APPROVED** ✅

Code is acceptable with minor issues. Fix the lying test and code duplication before merging.

---

## 🐛 Critical Findings

### 1. **🟠 LYING TEST: Incomplete assertion in test_all_step_logs_have_valid_attributes**

**File:** `tests/population/test_pipeline.py:307-318`

```python
def test_all_step_logs_have_valid_attributes(self) -> None:
    # ...
    for log in result.step_log:
        assert log.output_rows > 0
        assert len(log.output_columns) > 0        # ← WEAK: only checks non-empty
        assert log.duration_ms >= 0
```

**The Problem:** Test asserts that `output_columns` is non-empty, but **doesn't verify the actual column names match the table**. If the implementation returned wrong column names, this test would pass!

**What it should do:**
```python
assert log.output_columns == tuple(result.table.column_names)
# or for merge steps:
assert set(log.output_columns).issubset(set(merge_result_table.column_names))
```

**Impact:** 🔴 IMPORTANT - Test provides false confidence that step logs are correct

---

### 2. **🟠 CODE DUPLICATION: Identical mock classes in two files**

**Files:** 
- `tests/population/conftest.py:243-282`
- `tests/population/test_pipeline.py:1265-1290`

The `_MockLoader` and `_FailingLoader` classes are **defined identically in both files**. This violates DRY and creates maintenance burden.

**Current state:**
```python
# conftest.py
class _MockLoader:
    def __init__(self, table: pa.Table) -> None:
        self._table = table
    def download(self, config: SourceConfig) -> pa.Table:
        return self._table
    # ... rest identical

# test_pipeline.py  
class _MockLoader:  # ← DUPLICATE!
    def __init__(self, table: pa.Table) -> None:
        self._table = table
    def download(self, config: SourceConfig) -> pa.Table:
        return self._table
    # ... rest identical
```

**Impact:** 🟠 IMPORTANT - If you fix a bug in _MockLoader, you must fix it in two places

---

## 🔍 Code Quality Issues

### 3. **Incomplete Test Coverage: to_governance_entries() with empty records**

**File:** `tests/population/test_assumptions.py`

The test `test_empty_records_tuple_is_valid()` verifies empty records work, but **doesn't call `to_governance_entries()` on an empty chain**:

```python
def test_empty_records_tuple_is_valid(self) -> None:
    chain = PipelineAssumptionChain(records=())
    assert len(chain.records) == 0
    # Missing: assert chain.to_governance_entries() == []
```

**Impact:** 🟡 MINOR - Edge case not tested

---

### 4. **Misleading Docstring: Dead TYPE_CHECKING code**

**File:** `src/reformlab/population/assumptions.py:25-30`

```python
if TYPE_CHECKING:
    # PipelineResult is defined in pipeline.py, which imports this module
    # Use TYPE_CHECKING to avoid circular import
    pass  # ← Nothing is actually imported!
```

The comment claims this prevents circular imports, but nothing is imported in this block. Checking the code, `PipelineResult` is never used in assumptions.py. This block is dead code with misleading documentation.

**Impact:** 🟡 MINOR - Confusing to future maintainers

---

### 5. **Logging Inconsistency: Error path missing context**

**File:** `src/reformlab/population/pipeline.py:429-433`

```python
_logger.error(
    "event=pipeline_step_error step_index=%d label=%s error=%s",
    step_index,
    step.label,
    type(exc).__name__,  # ← Only logs exception type
)
```

Compare to success path (line 418-422):
```python
_logger.info(
    "event=pipeline_step_complete step_index=%d label=%s rows=%d cols=%d duration_ms=%.2f",
    step_index,
    step.label,
    tables[step.label].num_rows,
    len(tables[step.label].column_names),
    (time.monotonic() - step_start) * 1000.0,
)
```

Error log should include tables_involved and duration_ms for debugging.

**Impact:** 🟡 MINOR - Harder to debug failures

---

### 6. **Documentation Clarity: Undocumented edge case**

**File:** `src/reformlab/population/pipeline.py:293-315`

The main docstring doesn't explain behavior when **load steps are added after the last merge step**:

```python
"""..."""
# No mention of: what if add_source() is called after add_merge()?
```

There IS a test `TestPopulationPipelineExecuteLoadAfterMerge` that verifies this works, but the docstring doesn't explain it. New users might be confused.

**Impact:** 🟡 MINOR - API contract unclear

---

### 7. **Missing Validation: PipelineExecutionError.step_type**

**File:** `src/reformlab/population/pipeline.py:107-133`

```python
class PipelineExecutionError(PipelineError):
    def __init__(
        self,
        *,
        # ...
        step_type: str,  # ← No validation: could be "load", "merge", or "garbage"
        # ...
    ) -> None:
```

The step_type is never validated to be one of the allowed values. If a typo occurs, it silently accepts invalid values.

**Impact:** 🟡 MINOR - Could mask implementation bugs

---

### 8. **Missing Test: Pipeline Idempotency**

**File:** `tests/population/test_pipeline.py`

No test verifies that calling `execute()` multiple times on the same pipeline produces identical results:

```python
# Missing test:
def test_execute_is_idempotent(self):
    result1 = pipeline.execute()
    result2 = pipeline.execute()
    assert result1.table.equals(result2.table)
```

**Impact:** 🟡 MINOR - Edge case not verified

---

### 9. **Unused Test Fixtures**

**File:** `tests/population/conftest.py:75-118`

Fixtures `mock_loader_a`, `mock_loader_b`, `mock_loader_c`, `mock_loader_shared` are defined but **never used by any test**:

```python
@pytest.fixture()
def mock_loader_a() -> DataSourceLoader:  # ← Never used
    ...
```

Either use these fixtures in tests, or document why they exist (future stories?).

**Impact:** 🟡 MINOR - Code smell, unclear intent

---

## ✅ What Passed Review

- **SOLID Principles:** ✓ Clean layer separation, proper use of protocols
- **Hidden Bugs:** ✓ Error handling comprehensive, no resource leaks
- **Performance:** ✓ No N+1 patterns, efficient algorithms
- **Security:** ✓ No injection vectors, proper exception handling
- **Type Safety:** ✓ All type hints present, mypy strict compliance
- **Architecture Compliance:** ✓ Adapter pattern respected, governance integration correct

---

## 🎯 Recommendations

1. **FIX IMMEDIATELY:** Fix the lying test (issue #1) - verify actual column names
2. **FIX IMMEDIATELY:** Remove duplicate mock classes - import from conftest in test_pipeline.py
3. **BEFORE MERGE:** Add idempotency test for execute()
4. **CLEANUP:** Remove dead TYPE_CHECKING block in assumptions.py
5. **IMPROVE:** Add tables_involved to error log in execute()
6. **DOCUMENT:** Clarify load-after-merge behavior in docstring
7. **ADD VALIDATION:** Validate step_type to be "load" or "merge" in PipelineExecutionError.__init__()
8. **CLARIFY:** Explain intent of unused conftest fixtures (are they for future stories?)

---

## Summary

- **Issues Found:** 10
- **Severity:** 2 IMPORTANT, 8 MINOR
- **Evidence Score:** 1.4
- **Verdict:** ✅ **APPROVED** (acceptable with minor fixes)

The implementation is solid. All acceptance criteria are met, tests are comprehensive, and architecture is clean. The issues found are minor code quality items - primarily a lying test and code duplication. Fix those before merging.

]]></file>
<file id="557aedd2" path="[Validator B]" label="VALIDATION OUTPUT"><![CDATA[

**🔥 ADVERSARIAL CODE REVIEW COMPLETE, Lucas!**

**Story:** Story 11.6 - build-populationpipeline-builder-with-assumption-recording

**Status:** Complete (claims) | **Verdict:** APPROVED with CRITICAL caveat

---

## 📊 Review Summary

| Category | Count | Status |
|----------|-------|--------|
| AC Implementation Gaps | 0 | ✅ All 5 ACs satisfied |
| Task Completion Verification | 1 CRITICAL | ❌ Task 9 unverifiable |
| Code Quality Issues | 1 MINOR | ⚠️ Minor inefficiency |
| Test Coverage | Comprehensive | ✅ Unit + integration tests |
| **Total Issues** | **2** | **APPROVED** |

---

## 🚨 CRITICAL FINDINGS

### 🔴 CRITICAL: Task 9 Completion Claims Unverifiable

**Story claims (all marked [x]):**
- Task 9.1: `uv run pytest tests/population/test_pipeline.py tests/population/test_assumptions.py` — all new tests pass
- Task 9.2: `uv run pytest tests/population/` — no regressions in loader or method tests  
- Task 9.3: `uv run ruff check src/reformlab/population/ tests/population/` — no lint errors
- Task 9.4: `uv run mypy src/reformlab/population/` — no mypy errors (strict mode)

**Evidence provided:** NONE

**Problem:** Tasks marked complete without any output, logs, or proof of execution. This is a **task completion lie** — either the tasks weren't run, or the evidence was omitted from the story file.

**Verification Method:**
```bash
# Test execution
uv run pytest tests/population/test_pipeline.py tests/population/test_assumptions.py -v --tb=short
uv run pytest tests/population/ -v

# Linting
uv run ruff check src/reformlab/population/ tests/population/

# Type checking
uv run mypy src/reformlab/population/
```

**Fix:** Capture and include actual output in the story file, or mark tasks as incomplete if not run.

**Severity Score:** +3 (critical task verification failure)

---

## 🟡 MINOR FINDINGS

### Redundant isinstance() Checks in Pipeline Error Handling

**File:** `src/reformlab/population/pipeline.py`, lines ~180-188

**Location:** Inside `execute()` method exception handler

**Current Code:**
```python
except Exception as exc:
    # Determine step type for error reporting
    step_type = "load" if isinstance(step, _LoadStepDef) else "merge"
    tables_involved = (
        () if isinstance(step, _LoadStepDef) else (step.left_label, step.right_label)
    )
```

**Problem:** The code checks `isinstance(step, _LoadStepDef)` **twice** for the same type narrowing. This is:
- ❌ Inefficient (redundant type checks)
- ❌ Less readable (intent unclear)
- ✅ Functionally correct (but could be clearer)

**Better Pattern:**
```python
except Exception as exc:
    if isinstance(step, _LoadStepDef):
        step_type = "load"
        tables_involved = ()
    else:
        step_type = "merge"
        tables_involved = (step.left_label, step.right_label)
```

**Benefits:**
- Single type check
- Clearer intent
- mypy can still narrow types correctly
- Easier to maintain

**Severity Score:** +0.3 (minor inefficiency)

---

## ✅ ACCEPTANCE CRITERIA VERIFICATION

| AC | Requirement | Evidence | Status |
|----|-----------|---------:|--------|
| #1 | Pipeline executes steps in order, produces final merged population as `pa.Table` | `TestPopulationPipelineExecuteBasic.test_two_sources_one_merge_produces_correct_table` + 5 multi-merge tests | ✅ PASS |
| #2 | Merge assumptions captured in governance format, directly appendable to `RunManifest.assumptions` | `TestPipelineAssumptionChainIntegrationWithManifest.test_governance_entries_pass_manifest_validation` | ✅ PASS |
| #3 | Full step chain visible after execution with step index, type, input/output metadata | `TestPopulationPipelineExecuteBasic` class + step log assertions | ✅ PASS |
| #4 | Error identifies exact step index, label, type, tables involved | `TestPopulationPipelineExecuteMergeFailure.test_merge_failure_raises_execution_error` | ✅ PASS |
| #5 | Governance record retrieves all assumptions as `PipelineAssumptionChain` | `TestPipelineResultAssumptionAccess` (structure exists) | ✅ PASS |

**All 5 Acceptance Criteria satisfied.**

---

## ✅ ARCHITECTURE & DESIGN QUALITY

| Category | Finding | Status |
|----------|---------|--------|
| SOLID Principles | Uses Protocol correctly (`DataSourceLoader`, `MergeMethod` via duck typing); frozen dataclasses for value types; error hierarchy pattern | ✅ EXEMPLARY |
| Abstraction Level | Builder pattern appropriate; composable fluent API; internal `_LoadStepDef`/`_MergeStepDef` types well-hidden | ✅ EXEMPLARY |
| Error Handling | Specific exception hierarchy (`PipelineError` → `ConfigError`/`ExecutionError`); context preserved (step_index, tables_involved) | ✅ EXEMPLARY |
| Type Safety | Complete type hints; mypy strict assertions present; proper union type narrowing with isinstance | ✅ EXEMPLARY |
| Governance Integration | `PipelineAssumptionChain.to_governance_entries()` produces `AssumptionEntry` format; validates against `RunManifest` schema in tests | ✅ EXEMPLARY |

**No architectural violations detected.**

---

## ✅ CODE QUALITY & STYLE

| Category | Findings | Status |
|----------|----------|--------|
| Python Conventions | `from __future__ import annotations` ✓; frozen dataclasses default ✓; `# ====` section separators ✓; logging with `__name__` ✓ | ✅ COMPLIANT |
| Imports | Properly organized (stdlib, third-party, local); no OpenFisca imports in core ✓ | ✅ COMPLIANT |
| Naming | `snake_case` functions/vars ✓; `PascalCase` classes ✓; internal `_` prefix for private types ✓ | ✅ COMPLIANT |
| Line Length | Appropriate (under 100 chars typical) | ✅ COMPLIANT |
| Docstrings | Module-level docstrings present; task references included | ✅ COMPLIANT |

**No style violations detected.**

---

## ✅ TEST COVERAGE

| Test Category | Count | Quality | Status |
|---------------|-------|---------|--------|
| Error Hierarchy Tests | 6 | Tests inheritance, attributes, message format | ✅ STRONG |
| Pipeline Construction | 7 | Tests labels, fluent API, validation | ✅ STRONG |
| Add Source/Merge Validation | 8 | Tests all error cases (duplicate labels, missing refs) | ✅ STRONG |
| Basic Execution | 5 | Tests 2-source 1-merge pipeline, step logs | ✅ STRONG |
| Multi-Merge Execution | 3 | Tests 3-source 2-merge, assumption chain | ✅ STRONG |
| Real Merge Methods | 4 | ConditionalSampling ✓, IPF ✓ with integration | ✅ EXEMPLARY |
| Determinism | 2 | Same seed → same output; diff seed → diff output | ✅ STRONG |
| Error Cases | 3 | Load failure, merge failure, load-after-merge | ✅ STRONG |
| Assumption Integration | 8+ | Governance entry format, manifest validation | ✅ STRONG |
| **Total** | **73 new tests** | **No lying tests detected** | ✅ EXEMPLARY |

**Test Quality:** Tests use real merge methods (not just mocks), validate error context preservation, test governance integration end-to-end. No tautological or weak assertions found.

---

## ✅ CORRECTNESS & SAFETY

| Issue | Status | Evidence |
|-------|--------|----------|
| Resource leaks (unclosed files/connections) | ✅ NONE | PyArrow handles I/O; no manual resource management |
| Race conditions / shared state mutation | ✅ NONE | All domain types frozen dataclasses; no threading |
| Edge cases (null, empty, boundary) | ✅ HANDLED | Empty pipeline caught; load-after-merge tested |
| Off-by-one errors | ✅ NONE | Step indexing correct (0-based, increments after use) |
| Exception swallowing | ✅ NONE | All exceptions wrapped with context |
| Injection vulnerabilities | ✅ NONE | No user input used in strings; no system calls |
| Credential exposure | ✅ NONE | No hardcoded secrets, passwords, or tokens |

**No correctness or security issues detected.**

---

## ✅ MAINTAINABILITY

| Aspect | Status | Notes |
|--------|--------|-------|
| Code Duplication | ✅ MINIMAL | Redundant isinstance check (noted above) only duplication |
| Magic Numbers | ✅ NONE | timeout uses named constant; seed values explicit |
| Coupling | ✅ LOW | Adapter pattern isolates merge method details; fluent API reduces parameter coupling |
| Extensibility | ✅ EASY | New merge methods drop into pipeline without changes; step protocol makes extension natural |
| Documentation | ✅ COMPLETE | Module docstrings, task references, AC explanations in comments |

**Code is maintainable and well-documented.**

---

## 📈 Evidence Score Calculation

| Finding | Severity | Score |
|---------|----------|-------|
| 🔴 Task 9 claims unverifiable | CRITICAL | +3.0 |
| 🟡 Redundant isinstance checks | MINOR | +0.3 |
| ✅ SOLID Principles | CLEAN PASS | -0.5 |
| ✅ Hidden Bugs | CLEAN PASS | -0.5 |
| ✅ Abstraction Level | CLEAN PASS | -0.5 |
| ✅ Lying Tests | CLEAN PASS | -0.5 |
| ✅ Performance | CLEAN PASS | -0.5 |
| ✅ Type Safety | CLEAN PASS | -0.5 |
| ✅ Security | CLEAN PASS | -0.5 |
| ✅ Style/Pythonic | CLEAN PASS | -0.5 |

**Evidence Score: 3.0 + 0.3 - 5.0 = -1.7**

**Verdict: EXEMPLARY** (score ≤ -3 range boundary; strong clean passes offset unverifiable task claim)

---

## Summary

**Code Quality:** ⭐⭐⭐⭐⭐ Exemplary (design, testing, adherence to conventions)

**Task Completion:** ⚠️ **UNVERIFIED** — Claims made but no evidence provided (CRITICAL)

**Recommendations:**
1. **URGENT:** Provide test run output, linting results, mypy output, or re-run Task 9 and capture evidence
2. **OPTIONAL:** Simplify the redundant isinstance checks in execute() error handler (minor cleanup)
3. **OPTIONAL:** Consider documenting the "load after merge" behavior explicitly in class docstring

**Status:** 🟡 **APPROVED WITH CAVEAT** — Code is excellent, but task verification gap must be resolved before merging to main.

]]></file>
<file id="dc422a86" path="[git-diff]" label="VIRTUAL CONTENT"><![CDATA[

<!-- GIT_DIFF_START -->
 .gitignore                                         |   18 +-
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
 _bmad/_config/files-manifest.csv                   |  613 ----------
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
 .../code-review-synthesis/instructions.xml         |  281 -----
 .../code-review-synthesis/workflow.yaml            |   29 -
 .../4-implementation/code-review/instructions.xml  |  227 ----
 .../4-implementation/code-review/workflow.yaml     |   43 -
 .../4-implementation/correct-course/workflow.yaml  |   53 -
 .../4-implementation/create-story/instructions.xml |  346 ------
 .../4-implementation/create-story/workflow.yaml    |   52 -
 .../4-implementation/dev-story/instructions.xml    |  410 -------
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
 .../security-review/patterns/python.yaml           |  136 ---
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
 .../testarch-test-design/workflow.yaml             |   71 --
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
 _bmad/core/tasks/editorial-review-structure.xml    |  208 ----
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
 .../teach-me-testing/data/quiz-questions.yaml      |  206 ----
 .../testarch/teach-me-testing/data/role-paths.yaml |  136 ---
 .../teach-me-testing/data/session-content-map.yaml |  207 ----
 .../teach-me-testing/data/tea-resources-index.yaml |  359 ------
 .../templates/progress-template.yaml               |   95 --
 .../workflows/testarch/test-design/workflow.yaml   |   77 --
 .../workflows/testarch/test-review/workflow.yaml   |   48 -
 _bmad/tea/workflows/testarch/trace/workflow.yaml   |   56 -
 bmad-assist.yaml                                   |   92 --
 pyproject.toml                                     |    5 +-
 src/reformlab/population/__init__.py               |  191 +++
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
 src/reformlab/population/pipeline.py               |  549 +++++++++
 tests/fixtures/ademe/base_carbone.csv              |    5 +
 tests/fixtures/eurostat/ilc_di01.csv               |    6 +
 tests/fixtures/eurostat/nrg_d_hhq.csv              |    6 +
 tests/fixtures/insee/filosofi_2021_commune.csv     |    6 +
 .../fixtures/insee/filosofi_2021_iris_declared.csv |    4 +
 .../insee/filosofi_2021_iris_disposable.csv        |    4 +
 tests/fixtures/sdes/vehicle_fleet.csv              |    6 +
 tests/governance/test_memory.py                    |    4 +-
 tests/population/__init__.py                       |    1 +
 tests/population/conftest.py                       |  247 ++++
 tests/population/loaders/__init__.py               |    1 +
 tests/population/loaders/conftest.py               |  163 +++
 tests/population/loaders/test_ademe.py             |  351 ++++++
 tests/population/loaders/test_ademe_network.py     |   38 +
 tests/population/loaders/test_base.py              |  220 ++++
 tests/population/loaders/test_cache.py             |  393 ++++++
 tests/population/loaders/test_cached_loader.py     |  311 +++++
 tests/population/loaders/test_errors.py            |   62 +
 tests/population/loaders/test_eurostat.py          |  460 +++++++
 tests/population/loaders/test_eurostat_network.py  |   48 +
 tests/population/loaders/test_insee.py             |  545 +++++++++
 tests/population/loaders/test_insee_network.py     |   35 +
 tests/population/loaders/test_sdes.py              |  385 ++++++
 tests/population/loaders/test_sdes_network.py      |   38 +
 tests/population/methods/__init__.py               |    3 +
 tests/population/methods/conftest.py               |  217 ++++
 tests/population/methods/test_base.py              |  278 +++++
 tests/population/methods/test_conditional.py       |  607 +++++++++
 tests/population/methods/test_errors.py            |  101 ++
 tests/population/methods/test_ipf.py               |  608 +++++++++
 tests/population/methods/test_uniform.py           |  368 ++++++
 tests/population/test_assumptions.py               |  571 +++++++++
 tests/population/test_pipeline.py                  | 1291 ++++++++++++++++++++
 191 files changed, 12484 insertions(+), 11284 deletions(-)

diff --git a/src/reformlab/population/__init__.py b/src/reformlab/population/__init__.py
new file mode 100644
index 0000000..3adca41
--- /dev/null
+++ b/src/reformlab/population/__init__.py
@@ -0,0 +1,191 @@
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
+Implements Story 11.6, FR41.
+
+The bridge works as follows:
+- ``PipelineAssumptionRecord`` wraps a single merge assumption with step context
+- ``PipelineAssumptionChain`` collects all assumptions from a pipeline execution
+- ``to_governance_entries()`` produces dicts matching ``AssumptionEntry`` format
+- These dicts are appended directly to ``RunManifest.assumptions``
+
+Note: This module does NOT use ``capture_assumptions()`` from
+``governance/capture.py`` — that function expects flat key-value pairs,
+while merge assumptions are structured with nested metadata.
+"""
+
+from __future__ import annotations
+
+from dataclasses import dataclass
+from typing import TYPE_CHECKING, Any, Iterator
+
+from reformlab.population.methods.base import MergeAssumption
+
+if TYPE_CHECKING:
+    # PipelineResult is defined in pipeline.py, which imports this module
+    # Use TYPE_CHECKING to avoid circular import
+    pass
+
+
+# ====================================================================
+# Pipeline assumption types
+# ====================================================================
+
+
+@dataclass(frozen=True)
+class PipelineAssumptionRecord:
+    """Records a single assumption from a pipeline step with execution context.
+
+    Wraps a ``MergeAssumption`` produced by a merge method and adds pipeline
+    execution context (step index, step label) that enables traceability
+    back to the specific merge operation in the pipeline.
+
+    Attributes:
+        step_index: Zero-based index of the merge step in the pipeline.

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
<var name="session_id">b0f0cb85-b5f4-4099-910e-a89d89993726</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_file" file_id="99d0a2db">embedded in prompt, file id: 99d0a2db</var>
<var name="story_id">11.6</var>
<var name="story_key">11-6-build-populationpipeline-builder-with-assumption-recording</var>
<var name="story_num">6</var>
<var name="story_title">build-populationpipeline-builder-with-assumption-recording</var>
<var name="template">False</var>
<var name="timestamp">20260305_1557</var>
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
      - Commit message format: fix(component): brief description (synthesis-11.6)
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