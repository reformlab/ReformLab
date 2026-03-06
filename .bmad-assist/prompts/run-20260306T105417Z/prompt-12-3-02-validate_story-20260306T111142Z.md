<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 12 -->
<!-- Story: 3 -->
<!-- Phase: validate-story -->
<!-- Timestamp: 20260306T111142Z -->
<compiled-workflow>
<mission><![CDATA[

Adversarial Story Validation

Target: Story 12.3 - extend-orchestrator-to-execute-policy-portfolios

Your mission is to FIND ISSUES in the story file:
- Identify missing requirements or acceptance criteria
- Find ambiguous or unclear specifications
- Detect gaps in technical context
- Suggest improvements for developer clarity

CRITICAL: You are a VALIDATOR, not a developer.
- Read-only: You cannot modify any files
- Adversarial: Assume the story has problems
- Thorough: Check all sections systematically

Focus on STORY QUALITY, not code implementation.

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
<file id="40d1dade" path="docs/architecture.md" label="ARCHITECTURE"><![CDATA[

# Architecture — ReformLab

**Generated:** 2026-02-28
**Status:** Phase 1 Complete (all subsystems implemented)

## Strategic Direction

ReformLab does **not** build a replacement tax-benefit microsimulation core. OpenFisca is the policy-calculation foundation, accessed through a clean adapter interface. This project builds differentiated layers above it: data preparation, environmental policy orchestration, multi-year projection with vintage tracking, indicators, governance, and user interfaces.

**The dynamic orchestrator is the core product** — not a computation engine.

## Active Scope

- Data ingestion and harmonization (OpenFisca outputs, synthetic population inputs, environmental datasets)
- Scenario/template layer for environmental policies (carbon tax, subsidies, rebates, feebates)
- Step-pluggable dynamic orchestrator for multi-year execution (10+ years) with vintage/cohort tracking
- Indicator layer (distributional, welfare, fiscal, geographic, custom metrics)
- Run governance (manifests, assumption logs, lineage, reproducibility checks, benchmarking)
- Python API, Jupyter notebooks, and React no-code GUI

## Out Of Scope (MVP)

- Reimplementing OpenFisca internals
- Custom formula compiler or policy engine
- Endogenous market-clearing/equilibrium simulation
- Physical system loop simulation (climate/energy stock-flow engines)

## Layered Architecture

```
┌─────────────────────────────────────────────────────┐
│  Interfaces (Python API, Notebooks, No-Code GUI)     │
├─────────────────────────────────────────────────────┤
│  Indicator Engine (distributional/welfare/fiscal)    │
├─────────────────────────────────────────────────────┤
│  Governance (manifests, assumptions, lineage)        │
├─────────────────────────────────────────────────────┤
│  Dynamic Orchestrator (year loop + step pipeline)    │
│  ├── Vintage Transitions                             │
│  ├── State Carry-Forward                             │
│  └── [Phase 2: Behavioral Response Steps]            │
├─────────────────────────────────────────────────────┤
│  Scenario Template Layer (environmental policies)    │
├─────────────────────────────────────────────────────┤
│  Data Layer (ingestion, open data, synthetic pop)    │
├─────────────────────────────────────────────────────┤
│  Computation Adapter Interface                       │
│  └── OpenFiscaAdapter (primary implementation)       │
└─────────────────────────────────────────────────────┘
```

## Subsystem Details

### 1. Computation Adapter (`src/reformlab/computation/`)

The orchestrator never calls OpenFisca directly. All tax-benefit computation goes through a clean adapter interface:

```python
class ComputationAdapter(Protocol):
    """Interface for tax-benefit computation backends."""
    def compute(self, population: PopulationData, policy: PolicyConfig,
                period: int) -> ComputationResult: ...
    def version(self) -> str: ...
```

**Implementations:**
- `OpenFiscaAdapter` — Reads pre-computed CSV/Parquet files (primary Phase 1 mode)
- `OpenFiscaApiAdapter` — Live computation via OpenFisca Python API (lazy import, optional dependency)
- `MockAdapter` — Deterministic test backend for orchestrator isolation

**Supporting modules:**
- `ingestion.py` — CSV/Parquet loading with `DataSchema` validation, gzip support, type coercion
- `mapping.py` — Bidirectional field translation between OpenFisca and project schemas (`FieldMapping`, `MappingConfig`)
- `quality.py` — Output validation with `RangeRule`, null detection, type checks (`QualityCheckResult`)
- `compat_matrix.py` — Version governance via YAML compatibility matrix (`CompatibilityInfo`)
- `types.py` — Core data structures: `PopulationData` (PyArrow), `PolicyConfig`, `ComputationResult`

**Key design decisions:**
- Protocol-based (structural typing, `runtime_checkable`) — no class inheritance required
- All data uses PyArrow Tables for memory-efficient columnar processing
- OpenFisca is an optional dependency — core code works without it installed
- Version compatibility is checked at adapter construction time

### 2. Data Layer (`src/reformlab/data/`)

**Schema contracts:**
- `SYNTHETIC_POPULATION_SCHEMA` — Required: household_id, person_id, age, income. Optional: region_code, housing_status, energy columns
- `EMISSION_FACTOR_SCHEMA` — Required: category, factor_value, unit. Optional: year, subcategory, source

**Pipeline:**
- `DatasetRegistry` — Mutable append-only registry keyed by unique `dataset_key`
- `load_dataset()` — Load with schema validation, SHA-256 hashing, and manifest recording
- `DatasetManifest` — Provenance record (hash, path, format, row count, loaded_at)
- Path safety enforcement (allowed roots checking)

**Emission factors:**
- `EmissionFactorIndex` — Frozen index wrapping PyArrow table with `by_category()`, `by_category_and_year()` lookups

### 3. Scenario Templates (`src/reformlab/templates/`)

**Template schema (`schema.py`):**
- `PolicyType` enum: CARBON_TAX, SUBSIDY, REBATE, FEEBATE
- `YearSchedule` — Year range with duration, years iteration, containment check
- Typed parameter classes per policy: `CarbonTaxParameters`, `SubsidyParameters`, `RebateParameters`, `FeebateParameters`
- `BaselineScenario` and `ReformScenario` with reform-as-delta pattern

**Template packs:**
Each policy type has a pack with `compute.py` (tax burden, redistribution) and `compare.py` (baseline vs reform):
- `carbon_tax/` — Flat/progressive rates, lump-sum/progressive redistribution, exemptions
- `subsidy/` — Income caps, eligible categories
- `rebate/` — Lump-sum and progressive rebate distribution
- `feebate/` — Pivot-point fee/rebate with symmetric/asymmetric rates

**Registry (`registry.py`):**
- Content-addressable version IDs (SHA-256 prefix)
- Immutable: once saved, cannot modify
- Version history with timestamps and change descriptions

**Workflow configuration (`workflow.py`):**
- `WorkflowConfig` — Full orchestration definition (YAML/JSON)
- `OutputType` enum: distributional_indicators, comparison_table, panel_export, summary_report
- JSON Schema validation support

**Migration (`migration.py`):**
- `SchemaVersion` — Semantic version with `check_compatibility()`
- Pure-function migration: `migrate_scenario_dict()`

### 4. Dynamic Orchestrator (`src/reformlab/orchestrator/`)

The orchestrator runs a yearly loop (t to t+n) where each year executes a pipeline of pluggable steps:

```
For each year t in [start_year .. end_year]:
  For each step in pipeline:
    state = step.execute(year=t, state=state)
  Record year-t results
  Feed updated state into year t+1
```

**Core types:**
- `YearState` — State carried between years (year, data dict, seed, metadata)
- `OrchestratorConfig` — Configuration with start_year, end_year, initial_state, seed, step_pipeline
- `OrchestratorResult` — Execution result with yearly_states, errors, failed_year

**Step interface (`step.py`):**
- `OrchestratorStep` protocol — `name` property + `execute(year, state) -> YearState`
- `StepRegistry` — Registration and dependency ordering
- `@step` decorator — Function-based step creation
- `adapt_callable()` — Adapter for bare `YearStep` functions

**Built-in steps:**
- `ComputationStep` — Wraps `ComputationAdapter` for per-year computation
- `CarryForwardStep` — State propagation with configurable rules (`CarryForwardRule`)
- `VintageTransitionStep` — Cohort aging and retirement (from vintage module)

**Panel output (`panel.py`):**
- `PanelOutput` — Household-by-year panel dataset
- `compare_panels()` — Compare baseline and reform panels

### 5. Vintage Tracking (`src/reformlab/vintage/`)

Cohort-based asset tracking for multi-year simulations:

- `VintageCohort` — Single age cohort (age, count, attributes)
- `VintageState` — Collection of cohorts for an asset class with total_count, age_distribution
- `VintageSummary` — Derived metrics (mean_age, max_age, cohort_count)
- `VintageTransitionStep` — OrchestratorStep for year-over-year aging
- `VintageConfig` — Transition rules per asset class

### 6. Indicator Engine (`src/reformlab/indicators/`)

Computes analysis metrics from panel output:

| Indicator Type | Module | Key Metrics |
|---------------|--------|-------------|
| Distributional | `distributional.py` | Per-decile count, mean, median, sum, min, max |
| Geographic | `geographic.py` | Per-region aggregation with reference table validation |
| Welfare | `welfare.py` | Winner/loser count, mean gain/loss, threshold-based |
| Fiscal | `fiscal.py` | Revenue, cost, balance, cumulative totals |
| Comparison | `comparison.py` | Multi-scenario side-by-side analysis |
| Custom | `custom.py` | User-defined derived formulas |

**Common types:**
- `IndicatorResult` — Container with indicators, metadata, warnings, excluded_count
- Export methods: `export_csv()`, `export_parquet()`, `to_table()`
- `DecileIndicators`, `RegionIndicators`, `WelfareIndicators`, `FiscalIndicators`

### 7. Governance (`src/reformlab/governance/`)

Every run produces transparent, verifiable governance artifacts:

**Run Manifests (`manifest.py`):**
- `RunManifest` — Immutable frozen dataclass with manifest_id, run_timestamp, scenario config, parameters, data sources, artifact hashes, assumptions, warnings
- Integrity hashing for tamper detection
- Canonical JSON serialization for Git-diffable output

**Artifact Hashing (`hashing.py`):**
- SHA-256 streaming hashing (64KB chunks) for memory efficiency
- `hash_input_artifacts()`, `hash_output_artifacts()`, `verify_artifact_hashes()`

**Lineage (`lineage.py`):**
- `LineageGraph` — Parent-child manifest relationships
- Bidirectional lineage integrity validation

**Reproducibility (`reproducibility.py`):**
- `check_reproducibility()` — Re-execute and verify outputs match
- `ReproducibilityResult` with detailed diff reporting

**Benchmarking (`benchmarking.py`):**
- `run_benchmark_suite()` — Fiscal aggregate and distributional validation
- 100k-household reference population

**Memory (`memory.py`):**
- `estimate_memory_usage()` — Pre-flight memory estimation
- `get_available_memory()` — System memory check

### 8. Interfaces (`src/reformlab/interfaces/`)

**Python API (`api.py`):**
```python
# Core functions (re-exported from __init__.py)
run_scenario(config: RunConfig) -> SimulationResult
create_scenario(name, params, ...) -> str
clone_scenario(scenario_id, new_name) -> str
list_scenarios() -> list[dict]
get_scenario(scenario_id) -> dict
run_benchmarks() -> BenchmarkSuiteResult
check_memory_requirements(config) -> MemoryCheckResult
create_quickstart_adapter() -> MockAdapter
```

- `SimulationResult` — With `indicators(indicator_type, **kwargs)` method for on-demand computation
- `RunConfig`, `ScenarioConfig` — Configuration dataclasses

**Error design:**
- Canonical format: `[What] — [Why] — [How to fix]`
- `ConfigurationError` — Invalid config before execution (field_path, expected, actual, fix)
- `SimulationError` — Execution failure with partial states
- `ValidationErrors` — Aggregated validation issues
- `MemoryWarning` — Memory risk warning

**React Frontend (`frontend/`):**
- React 19 + TypeScript + Vite 7 + Tailwind CSS 4
- 3-column resizable workspace layout (left scenarios, main content, right context)
- 4-step configuration flow: Population → Template → Parameters → Assumptions
- 5 view modes: configuration, run, progress, results, comparison
- Recharts distributional bar chart visualization
- Mock data layer (to be wired to backend API)

## Data Contracts

- **Input:** Synthetic populations (CSV/Parquet), emission factors, OpenFisca outputs
- **Output:** Yearly panel datasets, scenario comparison tables, indicator exports (CSV/Parquet)
- **Contract failures** are explicit, field-level, and blocking
- Adapter interface defines the computation contract boundary

## Cross-Cutting Concerns

1. **Frozen dataclasses** — Immutability throughout for NFR16 compliance
2. **Structured errors** — Canonical `[What] — [Why] — [Fix]` format
3. **PyArrow-first** — All data uses PyArrow Tables for efficiency
4. **Protocol-based design** — Runtime-checkable protocols for flexibility without inheritance
5. **Content-addressable versioning** — SHA-256 prefixes for scenario versions
6. **Streaming hashing** — 64KB chunks for memory-efficient artifact verification
7. **Lazy imports** — Optional dependencies imported only when needed
8. **Deterministic execution** — Seed-controlled, logged in manifests

## Technical Constraints

- Python 3.13+
- OpenFisca as optional computation dependency
- CSV/Parquet as interoperability contracts
- Fully offline operation in user environment
- Single-machine target (16GB laptop) for MVP

## Phase 2+ Architecture Extensions

- **Behavioral responses:** New orchestrator step applying elasticities between yearly computation runs
- **System dynamics bridge:** Aggregate stock-flow outputs derived from microsimulation vintage tracking results
- **Alternative computation backends:** Swap adapter implementations without changing orchestrator or indicator layers
- **Production OpenFisca-France:** Real tax-benefit system integration with national data


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

GLM-5 (zai-coding-plan/glm-5)

### Debug Log References

Code review synthesis performed on 2026-03-05. Fixed critical immutability breach and high-priority integration/validation issues.

### Completion Notes List

**Code Review Synthesis (2026-03-05):**
- Fixed CRITICAL immutability breach: `list_policies()` now returns defensive copy of rate_schedule dict instead of direct reference
- Fixed HIGH package integration: Added PolicyConfig, PolicyPortfolio, and portfolio exceptions to templates/__init__.py exports
- Fixed HIGH schema validation: Added `additionalProperties: false` to portfolio.schema.json (root, policy item, policy.parameters) to prevent typos/unknown fields from being silently accepted
- Fixed HIGH test data format: Updated test_dict_to_portfolio_basic to use canonical nested `redistribution` format instead of legacy flat format
- Fixed MEDIUM lint issues: Removed unused `yaml` import from test_composition.py, removed unused `PolicyType` import from conftest.py, removed unused `lines` variable from test_deterministic_key_ordering
- All ruff checks pass
- 41/47 tests pass (6 pre-existing failures in TestPortfolioErrorHandling - these expect field-specific error messages but jsonschema provides generic type errors; validation IS working, just error message format differs)

**Deferred items:**
- Story task checkboxes not updated (outside scope of code fixes - would require modifying story file context)
- 6 error handling tests failing (pre-existing issue - validation works but error message format doesn't match test expectations)
- Type checker warning at test_composition.py:472 (pre-existing - accessing income_weights on PolicyParameters base class)

### File List

**Source code files modified:**
- src/reformlab/templates/portfolios/portfolio.py (immutability fix)
- src/reformlab/templates/__init__.py (export additions)
- src/reformlab/templates/schema/portfolio.schema.json (strict validation)
- tests/templates/portfolios/test_composition.py (format fix, lint fixes)
- tests/templates/portfolios/conftest.py (lint fix)

## Senior Developer Review (AI)

### Review: 2026-03-05
- **Reviewer:** AI Code Review Synthesis
- **Evidence Score:** 7.2 → REJECT
- **Issues Found:** 8
- **Issues Fixed:** 5
- **Action Items Created:** 3

#### Review Follow-ups (AI)
- [ ] [AI-Review] MEDIUM: Improve error handling tests - update test expectations to match jsonschema error message format or use field-specific error extraction from jsonschema.ValidationError (tests/templates/portfolios/test_composition.py:497,516,536,558,578,598)
- [ ] [AI-Review] MEDIUM: Fix type checker warning - add type assertion or cast for income_weights access on RebateParameters (tests/templates/portfolios/test_composition.py:472)
- [ ] [AI-Review] LOW: Consider strengthening test_deterministic_key_ordering to validate actual key ordering, not just presence (tests/templates/portfolios/test_composition.py:249-254)


]]></file>
<file id="38e1067d" path="_bmad-output/implementation-artifacts/12-2-implement-portfolio-compatibility-validation-and-conflict-resolution.md" label="STORY FILE"><![CDATA[

<!-- CODE_REVIEW_SYNTHESIS_START -->
## Synthesis Summary

Code review synthesis completed for Story 12.2. **2 independent reviewers** identified **15 issues** across critical, high, and medium severity levels. After thorough verification against project context and source code, **7 issues were verified as valid**, **8 issues were dismissed as false positives or already addressed**, and **6 fixes were successfully applied** to source files. All tests passing (26/26).

## Validations Quality
**Reviewer A (Validator A)**
- Evidence Score: 10.1 → REJECT
- Assessment: **High-quality adversarial review**. Correctly identified critical functional gaps (UnboundLocalError, missing PARAMETER_MISMATCH detection, incomplete resolution strategies) and maintainability issues (hardcoded validation, insufficient comments). Strong evidence citations with specific line numbers. Minor overreach on test coverage claims (story file already acknowledged incomplete).
**Reviewer B (Validator B)**
- Evidence Score: 9.3 → REJECT  
- Assessment: **Thorough technical review**. Excellent catch on circular import risk, determinism violations (set rendering), input validation gaps (type guards), and idempotency issues (description accumulation). Strong consensus with Reviewer A on critical issues. One false positive on category conflict detection (already symmetric in current code).
## Issues Verified (by severity)
### Critical
1. **UnboundLocalError in dict_to_portfolio** | **Source**: Both reviewers | **File**: src/reformlab/templates/portfolios/composition.py:243 | **Fix**: Removed duplicate code block (lines 242-255) that referenced `policy_type` before it was defined. Consolidated validation logic and ensured `policy_type` is extracted and validated before use.
2. **Circular Import Risk** | **Source**: Both reviewers | **File**: src/reformlab/templates/portfolios/portfolio.py:12 | **Fix**: Extracted `ConflictType` and `ResolutionStrategy` enums into separate file (enums.py) to break circular dependency between portfolio.py and composition.py. Updated imports in both files and __init__.py.
3. **Missing PARAMETER_MISMATCH Detection** | **Source**: Both reviewers | **File**: src/reformlab/templates/portfolios/composition.py:555+ | **Fix**: Implemented PARAMETER_MISMATCH conflict detection that checks for parameter value differences (redistribution_type, rebate_type, income_caps, pivot_point) when policies have overlapping categories. Added detection logic after category overlap detection (lines 527-563).
### High
4. **Hardcoded Resolution Strategy Validation** | **Source**: Both reviewers | **File**: src/reformlab/templates/portfolios/portfolio.py:93-98 | **Fix**: Updated validation to use `ResolutionStrategy` enum values directly instead of hardcoded string set. Added runtime import in `__post_init__` to avoid circular import at module level.
5. **Non-deterministic set rendering in descriptions** | **Source**: Validator B | **File**: src/reformlab/templates/portfolios/composition.py:498,522 | **Dismissed Reason**: Code already uses `sorted(overlap)` which produces deterministic output. The set representation would vary by hash seed is incorrect - the code already implements deterministic ordering.
### Medium
6. **Unrelated file in git diff** | **Source**: Validator A | **File**: scripts/check_ai_usage.py | **Dismissed Reason**: This file was added as part of Story 12.2 changes but is completely unrelated to portfolio compatibility validation. Should be removed or it was already removed or Not in scope for this code review synthesis.
### Low
7. **Insufficient inline comments** | **Source**: Validator A | **File**: src/reformlab/templates/portfolios/composition.py:640+ | **Dismissed Reason**: While reviewers noted insufficient comments, the code has inline comments explaining resolution strategy scope. However, the existing inline comments already state this is a "placeholder" or "initial implementation" - which is the task-level docstrings in composition.py explain the limitation. Given the story constraints and complexity. Adding comprehensive inline comments would require modifying frozen dataclasses and which would require a separate PR to Add additional inline comments. For now, the scope limitation is noted in code as technical debt for future refactoring.
## Issues Dismissed
- **Claimed Issue**: Category conflict detection is asymmetric | **Raised by**: Validator B | **Dismissal Reason**: Current code at composition.py:528-550 already implements symmetric detection checking all combinations of `covered_categories` and `eligible_categories` for both policies i and j.
- **Claimed Issue**: Test coverage claims incomplete | **Raised by**: Both reviewers | **Dismissed Reason**: Story file explicitly documents partial implementation status in Dev agent record. While test coverage is not 100%, both reviewers correctly identified that resolution strategies are incomplete. This is a known limitation documented in the story, not a new issue discovered in the code review.
- **Claimed Issue**: Lying test for test_first_wins_strategy | **Raised by**: Validator A | **Dismissed Reason**: The `_apply_first_wins_strategy` function correctly returns the first policy's values by definition. The test passes because the test setup happens to match the expected behavior. The test is valid for the current implementation; however, the reviewer's suggestion to generalize the strategy for SAME_POLICY_TYPE conflicts would valuable feedback that and future improvement.
- **Claimed Issue**: Input type guard for policy field | **Raised by**: Validator B | **Dismissed Reason**: Current code already validates `policy_data["policy"]` is a dict at line 234. While `policy_type` validation could be added later (lines 256-262), the existing validation is sufficient for catching type errors before they propagating to the catch clause.
- **Claimed Issue**: Idempotency issue with description accumulation | **Raised by**: Validator B | **Dismissed Reason**: Already addressed in current code review synthesis - the fix at lines 626-637 now checks if resolution metadata is already present before appending again.
## Changes Applied
**File**: src/reformlab/templates/portfolios/composition.py
**Change 1**: Fixed UnboundLocalError by removing duplicate code
**Before**:
```python
        policy_params = _dict_to_policy_parameters(
            policy_data["policy"], policy_type, f"policies[{idx}].policy"
        )

        policy_data_dict = policy_data["policy"]
        if not isinstance(policy_data_dict, dict):
            raise PortfolioValidationError(...)
        )
        policy_params = _dict_to_policy_parameters(policy_data_dict, policy_type, f"policies[{idx}].policy")
```
**After**:
```python
        policy_data_dict = policy_data["policy"]
        
        # Validate and convert policy_type
        policy_type_str = policy_data["policy_type"]
        if not isinstance(policy_type_str, str):
            raise PortfolioValidationError(...)
        try:
            policy_type = PolicyType(policy_type_str)
        except (ValueError, TypeError):
            raise PortfolioValidationError(...)
        
        policy_params = _dict_to_policy_parameters(policy_data_dict, policy_type, f"policies[{idx}].policy")
```
**Change 2**: Extracted enums to separate file to break circular imports
**Before**:
```python
# In composition.py
class ConflictType(Enum):
    SAME_POLICY_TYPE = "same_policy_type"
    ...

class ResolutionStrategy(Enum):
    ERROR = "error"
    ...
```
**After**:
```python
# New file: src/reformlab/templates/portfolios/enums.py
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
```
**Change 3**: Added PARAMETER_MISMATCH conflict detection
**Before**:
```python
    # Detect overlapping categories conflicts
    for i in range(len(portfolio.policies)):
        ...existing category overlap detection...
    
    # Sort conflicts by policy indices
```
**After**:
```python
    # Detect overlapping categories conflicts
    for i in range(len(portfolio.policies)):
        ...existing category overlap detection...
    
    # Detect PARAMETER_MISMATCH conflicts
    for i in range(len(portfolio.policies)):
        for j in range(i + 1, len(portfolio.policies)):
            # Get overlapping categories
            cats_i = set(getattr(...))
            overlap = cats_i & cats_j
            
            if not overlap:
                continue
            
            # Check for mismatches in key parameters
            params_to_check = [
                ("redistribution_type", "redistribution_type"),
                ("rebate_type", "rebate_type"),
                ("income_caps", "income_caps"),
                ("pivot_point", "pivot_point"),
            ]
            
            for param_name, attr_name in params_to_check:
                val_i = getattr(portfolio.policies[i].policy, attr_name, None)
                val_j = getattr(portfolio.policies[j].policy, attr_name, None)
                
                if val_i is not None and val_j is not None and val_i != val_j:
                    conflict = Conflict(...)
                    conflicts.append(conflict)
    
    # Sort conflicts
```
**Change 4**: Used enum values for resolution_strategy validation
**Before**:
```python
        valid_strategies = {"error", "sum", "first_wins", "last_wins", "max"}
        if self.resolution_strategy not in valid_strategies:
```
**After**:
```python
        from reformlab.templates.portfolios.enums import ResolutionStrategy
        
        valid_strategy_values = {s.value for s in ResolutionStrategy}
        if self.resolution_strategy not in valid_strategy_values:
```
**Change 5**: Made resolution description idempotent
**Before**:
```python
    description_suffix = (
        f"\n\nResolved {len(conflicts)} conflicts using '{portfolio.resolution_strategy}' strategy."
    )
    return PolicyPortfolio(
        ...
        description=portfolio.description + description_suffix,
```
**After**:
```python
    resolution_marker = f"Resolved {len(conflicts)} conflicts using '{portfolio.resolution_strategy}' strategy."
    if resolution_marker not in portfolio.description:
        description_suffix = f"\n\n{resolution_marker}"
    else:
        description_suffix = ""
    
    return PolicyPortfolio(
        ...
        description=portfolio.description + description_suffix,
```
**Change 6**: Removed unrelated file
**Before**:
```python
scripts/check_ai_usage.py (317 lines)
```
**After**:
```python
# File removed
```
## Files Modified
- src/reformlab/templates/portfolios/composition.py
- src/reformlab/templates/portfolios/portfolio.py
- src/reformlab/templates/portfolios/__init__.py
- src/reformlab/templates/portfolios/enums.py (NEW)
- src/reformlab/templates/__init__.py
## Suggested Future Improvements
- **Scope**: Resolution strategy implementations (sum, max, first_wins, last_wins) | **Rationale**: Current implementations only handle OVERLAPPING_YEARS conflicts. Consider generalizing to handle SAME_POLICY_TYPE and OVERLAPPING_CATEGORIES conflicts. This would enable removing conflicting policies or creating unified conflict resolution across. portfolio | **Effort**: Medium (2-3 days)
- **Scope**: Complete test coverage for PARAMETER_MISMATCH | **Rationale**: While basic PARAMETER_MISMATCH detection is implemented, comprehensive test coverage is needed to ensure all edge cases are handled correctly | **Effort**: Low (1-2 hours)
- **Scope**: Resolution strategy documentation | **Rationale**: Add comprehensive inline comments to `_apply_*_strategy` functions explaining current limitations (rate_schedule only) and future developers understand the scope | **Effort**: Low (30 minutes)
## Test Results
Final test run output summary:
- Tests passed: 73
- Tests failed: 0
<!-- CODE_REVIEW_SYNTHESIS_END -->

## Senior Developer Review (AI)

### Review: 2026-03-06
- **Reviewer:** AI Code Review Engine (Claude Opus 4.6)
- **Evidence Score:** 8.1 (pre-fix) -> 0.4 (post-fix) -> APPROVED
- **Issues Found:** 8
- **Issues Fixed:** 6
- **Action Items Created:** 0
- **Remaining Notes:** Resolution strategies only handle OVERLAPPING_YEARS (design limitation, documented in Suggested Future Improvements)


]]></file>
<file id="78cc87c5" path="_bmad-output/implementation-artifacts/12-3-extend-orchestrator-to-execute-policy-portfolios.md" label="STORY FILE"><![CDATA[

# Story 12.3: Extend Orchestrator to Execute Policy Portfolios

Status: ready-for-dev

## Story

As a **policy analyst**,
I want the orchestrator to execute a policy portfolio (2+ bundled policies) over a multi-year simulation,
so that I can observe the combined effect of multiple environmental policies on household outcomes without writing custom pipeline code.

## Acceptance Criteria

### AC1: Multi-policy portfolio execution
Given a `PolicyPortfolio` with 3 policies (e.g., carbon tax + subsidy + feebate), when the orchestrator runs a yearly step, then all 3 policies are applied to the population for that year. Each policy's computation result is stored, and a merged result is available under `COMPUTATION_RESULT_KEY` for panel compatibility.

### AC2: 10-year portfolio panel output
Given a portfolio execution completed over 10 years, when `PanelOutput.from_orchestrator_result()` is called, then the panel output reflects the combined effect of all policies — one row per household per year containing output fields from every policy in the portfolio.

### AC3: No changes to ComputationAdapter or orchestrator core
Given the orchestrator receiving a portfolio instead of a single policy, when run, then no changes to `ComputationAdapter` protocol (`src/reformlab/computation/adapter.py`), `Orchestrator` runner (`src/reformlab/orchestrator/runner.py`), `OrchestratorConfig` (`src/reformlab/orchestrator/types.py`), or `PanelOutput.from_orchestrator_result()` (`src/reformlab/orchestrator/panel.py`) are required. The portfolio is unwrapped in a new `PortfolioComputationStep` at the template application layer.

### AC4: Backward compatibility with single-policy scenarios
Given a single-policy scenario (using the existing `ComputationStep`), when run through the same orchestrator, then it behaves identically to pre-portfolio execution. The existing `ComputationStep` class is unchanged.

### AC5: Validation and error handling
Given a `PolicyPortfolio` with an invalid or unsupported policy type, when `PortfolioComputationStep` is constructed, then a `PortfolioComputationStepError` is raised with the exact policy index and type that failed. Given an adapter that fails during one policy's computation, when the step executes, then the error includes: which policy failed (index, name, type), the year, the adapter version, and the original exception.

### AC6: Deterministic execution
Given identical inputs (same portfolio, population, adapter, and seed), when the step executes twice, then the `YearState` outputs are identical — same merged result table, same metadata structure, same per-policy execution order.

### AC7: Portfolio metadata in YearState
Given a completed portfolio computation step, when `YearState.metadata` is inspected, then it contains a `PORTFOLIO_METADATA_KEY` entry with: portfolio name, policy count, per-policy execution records (policy_type, name, adapter_version, row_count), and the execution order.

## Tasks / Subtasks

### Task 1: Create `PortfolioComputationStep` module (AC: 1, 3, 4, 6)

- [ ] 1.1 Create new file `src/reformlab/orchestrator/portfolio_step.py` with module docstring referencing Story 12.3 / FR44
- [ ] 1.2 Define `PORTFOLIO_METADATA_KEY = "portfolio_metadata"` stable string constant
- [ ] 1.3 Define `PORTFOLIO_RESULTS_KEY = "portfolio_results"` stable string constant for per-policy results
- [ ] 1.4 Define `PortfolioComputationStepError(Exception)` with `year`, `adapter_version`, `policy_index`, `policy_type`, `original_error` attributes
- [ ] 1.5 Define `_to_computation_policy()` bridge function: converts `portfolios.PolicyConfig` (typed `PolicyParameters`) to `computation.types.PolicyConfig` (generic `dict[str, Any]`) via `dataclasses.asdict()`
- [ ] 1.6 Implement `PortfolioComputationStep` class with `__slots__`, `OrchestratorStep` protocol compliance (`name`, `depends_on`, `description`, `execute()`)

### Task 2: Implement `PortfolioComputationStep.__init__()` (AC: 1, 5)

- [ ] 2.1 Parameters: `adapter: ComputationAdapter`, `population: PopulationData`, `portfolio: PolicyPortfolio`, `name: str = "portfolio_computation"`, `depends_on: tuple[str, ...] = ()`, `description: str | None = None`
- [ ] 2.2 Store all constructor args in `__slots__`
- [ ] 2.3 Validate `portfolio.policies` is non-empty (should be guaranteed by `PolicyPortfolio.__post_init__` but defensive check)
- [ ] 2.4 Validate each `PolicyConfig.policy_type` has a valid `PolicyType` value (fail fast at construction, not at runtime)

### Task 3: Implement `execute()` method (AC: 1, 2, 5, 6, 7)

- [ ] 3.1 Get adapter version via `self._adapter.version()` with `"<version-unavailable>"` fallback (same pattern as `ComputationStep`)
- [ ] 3.2 Iterate over `self._portfolio.policies` **in tuple order** (deterministic)
- [ ] 3.3 For each policy: call `_to_computation_policy()` to create `computation.types.PolicyConfig`
- [ ] 3.4 For each policy: call `self._adapter.compute(population=self._population, policy=comp_policy, period=year)`
- [ ] 3.5 Collect all `ComputationResult` objects in an ordered list
- [ ] 3.6 Build per-policy execution records for metadata: `{"policy_index": i, "policy_type": policy_type.value, "policy_name": name, "adapter_version": version, "row_count": num_rows}`
- [ ] 3.7 Merge all `ComputationResult.output_fields` (`pa.Table`) into a single combined table via `_merge_policy_results()`
- [ ] 3.8 Create a single `ComputationResult` with the merged output table, store under `COMPUTATION_RESULT_KEY` (panel compatibility)
- [ ] 3.9 Store all individual `ComputationResult` objects under `PORTFOLIO_RESULTS_KEY` in `state.data` (per-policy access)
- [ ] 3.10 Store portfolio metadata under `PORTFOLIO_METADATA_KEY` in `state.metadata`
- [ ] 3.11 Also store standard `COMPUTATION_METADATA_KEY` with merged info (so `runner.py` can extract adapter_version from existing metadata path at line 342-346)
- [ ] 3.12 Return new `YearState` via `dataclasses.replace()` (immutable updates)

### Task 4: Implement `_merge_policy_results()` helper (AC: 1, 2)

- [ ] 4.1 Create module-level function `_merge_policy_results(results: list[ComputationResult], portfolio: PolicyPortfolio) -> pa.Table`
- [ ] 4.2 Strategy: join all output tables on `household_id`. For the first result, keep column names as-is. For subsequent results, prefix columns with `{policy_type}_` to avoid name collisions (e.g., `subsidy_amount`, `feebate_net_impact`)
- [ ] 4.3 Handle the case where `household_id` is missing from a result table (use row-index alignment as fallback, matching panel.py pattern at line 233-235)
- [ ] 4.4 Handle edge case: if all results have the same column names (e.g., two carbon tax policies after conflict resolution), prefix ALL with `{policy_type}_{index}_`
- [ ] 4.5 Result table must contain ALL columns from ALL policies, plus `household_id`
- [ ] 4.6 Deterministic column ordering: `household_id` first, then columns from each policy in portfolio order

### Task 5: Implement error handling (AC: 5)

- [ ] 5.1 Wrap individual `adapter.compute()` calls in try/except; on failure, raise `PortfolioComputationStepError` with policy context
- [ ] 5.2 Error message format: `"Portfolio computation failed at year {year}, policy[{idx}] ({policy_type}): {error_type}: {error}"`
- [ ] 5.3 Structured log on error: `event=portfolio_computation_error year={year} policy_index={idx} policy_type={type} adapter_version={version}`
- [ ] 5.4 Log INFO per policy execution: `event=portfolio_policy_computed year={year} policy_index={idx} policy_type={type} adapter_version={version} row_count={n}`
- [ ] 5.5 Log INFO on portfolio completion: `event=portfolio_computation_complete year={year} portfolio={name} policy_count={n}`

### Task 6: Update `orchestrator/__init__.py` exports (AC: 3, 4)

- [ ] 6.1 Add `PortfolioComputationStep`, `PortfolioComputationStepError`, `PORTFOLIO_METADATA_KEY`, `PORTFOLIO_RESULTS_KEY` to `__init__.py` exports under new section comment `# Portfolio step (Story 12-3)`
- [ ] 6.2 Add to `__all__` list

### Task 7: Write tests in `tests/orchestrator/test_portfolio_step.py` (AC: all)

- [ ] 7.1 Create test file with standard imports and module docstring referencing Story 12.3
- [ ] 7.2 **TestPortfolioStepProtocol** (AC3): Verify `PortfolioComputationStep` satisfies `OrchestratorStep` protocol (has `name`, `depends_on`, `execute`, isinstance check)
- [ ] 7.3 **TestPortfolioStepExecution** (AC1, AC2): Given 3-policy portfolio + `MockAdapter`, execute returns `YearState` with `COMPUTATION_RESULT_KEY` containing merged `ComputationResult`. Assert all policy columns present. Assert `MockAdapter.call_log` has 3 entries (one per policy). Assert `household_id` column present
- [ ] 7.4 **TestPortfolioStepMergedOutput** (AC2): Merged table has columns from all policies with correct prefixing. Column order is deterministic (household_id first, then by policy order)
- [ ] 7.5 **TestPortfolioStepMetadata** (AC7): `state.metadata[PORTFOLIO_METADATA_KEY]` contains portfolio name, policy count, per-policy records with policy_type/name/adapter_version/row_count
- [ ] 7.6 **TestPortfolioStepMetadata_ComputationKey** (AC3): `state.metadata[COMPUTATION_METADATA_KEY]` is present (backward compat with `runner.py` metadata extraction)
- [ ] 7.7 **TestPortfolioStepDeterminism** (AC6): Two runs with identical inputs produce identical `YearState` output (data and metadata)
- [ ] 7.8 **TestPortfolioStepErrorHandling** (AC5): Adapter failure at policy[1] raises `PortfolioComputationStepError` with correct `policy_index=1`, `policy_type`, `year`, `adapter_version`, `original_error`
- [ ] 7.9 **TestPortfolioStepErrorHandling_VersionFallback** (AC5): Adapter with failing `version()` uses `"<version-unavailable>"` fallback
- [ ] 7.10 **TestPortfolioStepBackwardCompat** (AC4): Existing `ComputationStep` continues to work unchanged in the same pipeline. Pipeline with `[PortfolioComputationStep, CarryForwardStep]` works
- [ ] 7.11 **TestPortfolioStepInPipeline** (AC1, AC4): Full orchestrator run with `PortfolioComputationStep` in step pipeline over 3 years. Verify yearly states contain portfolio results for each year
- [ ] 7.12 **TestPortfolioStepPanelIntegration** (AC2): Full orchestrator run → `PanelOutput.from_orchestrator_result()` produces panel with all policy columns across all years. Panel export to CSV/Parquet works
- [ ] 7.13 **TestPolicyConfigBridge** (AC1): `_to_computation_policy()` converts `portfolios.PolicyConfig` → `computation.types.PolicyConfig` correctly. `rate_schedule`, `exemptions`, custom fields are preserved in the dict
- [ ] 7.14 **TestPerPolicyResults** (AC1): `state.data[PORTFOLIO_RESULTS_KEY]` stores individual `ComputationResult` per policy, accessible by index

### Task 8: Add portfolio step fixtures to `tests/orchestrator/conftest.py` (AC: all)

- [ ] 8.1 Add `sample_portfolio` fixture: 2-policy portfolio (carbon tax + subsidy) with test parameters
- [ ] 8.2 Add `three_policy_portfolio` fixture: 3-policy portfolio (carbon tax + subsidy + feebate)
- [ ] 8.3 Add `portfolio_computation_step` fixture: `PortfolioComputationStep` with `MockAdapter` and sample population
- [ ] 8.4 Reuse existing `MockAdapter` patterns from `tests/orchestrator/test_computation_step.py`

### Task 9: Run quality checks (AC: all)

- [ ] 9.1 Run `uv run pytest tests/orchestrator/test_portfolio_step.py -v` — all tests pass
- [ ] 9.2 Run `uv run pytest tests/orchestrator/ -v` — all existing orchestrator tests still pass (no regressions)
- [ ] 9.3 Run `uv run pytest tests/templates/portfolios/ -v` — all portfolio tests still pass
- [ ] 9.4 Run `uv run ruff check src/reformlab/orchestrator/portfolio_step.py tests/orchestrator/test_portfolio_step.py`
- [ ] 9.5 Run `uv run mypy src/reformlab/orchestrator/portfolio_step.py` — passes strict mode
- [ ] 9.6 Run full test suite: `uv run pytest tests/ -v` — no regressions

## Dev Notes

### Architecture Decisions

**Design: `PortfolioComputationStep` — a new step, not a modification**

The key architectural constraint (AC3) is: *no changes to `ComputationAdapter`, `Orchestrator`, `OrchestratorConfig`, or `PanelOutput`*. This means the portfolio must be unwrapped at the template application layer, not inside the orchestrator runner.

The solution is a **new `PortfolioComputationStep`** class that:
1. Implements the existing `OrchestratorStep` protocol (name + execute)
2. Takes a `PolicyPortfolio` instead of a single `PolicyConfig`
3. Iterates over each policy in the portfolio, converting it and calling the adapter
4. Merges results into a single `ComputationResult` stored under the **same `COMPUTATION_RESULT_KEY`**

This means `PanelOutput.from_orchestrator_result()` works unchanged — it reads `COMPUTATION_RESULT_KEY` from each yearly state, extracts `output_fields`, and concatenates. The merged table just has more columns.

**Two PolicyConfig types — the bridge function**

There are TWO `PolicyConfig` classes in the codebase:
- `reformlab.computation.types.PolicyConfig` — holds `policy: dict[str, Any]`, used by `ComputationAdapter.compute()`
- `reformlab.templates.portfolios.portfolio.PolicyConfig` — holds `policy_type: PolicyType`, `policy: PolicyParameters`, used by `PolicyPortfolio`

The bridge function `_to_computation_policy()` converts the portfolio type to the computation type:
```python
from dataclasses import asdict

def _to_computation_policy(
    policy_config: "portfolios_PolicyConfig",
) -> "computation_PolicyConfig":
    from reformlab.computation.types import PolicyConfig as ComputationPolicyConfig
    return ComputationPolicyConfig(
        policy=asdict(policy_config.policy),
        name=policy_config.name or policy_config.policy_type.value,
        description=f"{policy_config.policy_type.value} policy",
    )
```

**Result merging strategy**

Each policy produces a `ComputationResult` with `output_fields: pa.Table`. The merge:
1. First policy's columns keep their original names
2. Subsequent policies' columns are prefixed with `{policy_type}_` (e.g., `subsidy_amount`, `feebate_net_impact`)
3. `household_id` is shared (join key) — not duplicated
4. If two policies have the same `policy_type` (after conflict resolution), use `{policy_type}_{index}_` prefix

This avoids column name collisions while keeping the first policy's columns backward-compatible with existing downstream code (e.g., indicators that reference `tax_burden` directly).

**Cross-policy data flow is OUT OF SCOPE**

Rebate templates require a `rebate_pool` parameter that could come from carbon tax revenue. This cross-policy dependency is NOT handled in this story. Each policy is computed independently with the same population data. Cross-policy data flow will be addressed in Story 12.5 or a future story.

### Key Interfaces to Follow

**`OrchestratorStep` protocol** [Source: src/reformlab/orchestrator/step.py:42-70]:
```python
@runtime_checkable
class OrchestratorStep(Protocol):
    @property
    def name(self) -> str: ...
    def execute(self, year: int, state: YearState) -> YearState: ...
```
Optional: `depends_on: tuple[str, ...]`, `description: str`

**`ComputationAdapter.compute()` signature** [Source: src/reformlab/computation/adapter.py]:
```python
def compute(self, population: PopulationData, policy: PolicyConfig, period: int) -> ComputationResult
```

**`ComputationStep.execute()` pattern to follow** [Source: src/reformlab/orchestrator/computation_step.py:118-196]:
- Get adapter version with fallback
- Call adapter.compute()
- Store result under `COMPUTATION_RESULT_KEY` in `state.data`
- Store metadata under `COMPUTATION_METADATA_KEY` in `state.metadata`
- Return `replace(state, data=new_data, metadata=new_metadata)`

**`runner.py` metadata extraction** [Source: src/reformlab/orchestrator/runner.py:342-346]:
The orchestrator runner reads `COMPUTATION_METADATA_KEY` from `state.metadata` to extract adapter version. `PortfolioComputationStep` MUST populate this key for backward compatibility with the runner's step execution logging.

### Scope Boundaries

**IN SCOPE:**
- `PortfolioComputationStep` class implementing `OrchestratorStep` protocol
- Bridge function from `portfolios.PolicyConfig` to `computation.types.PolicyConfig`
- Result merging (join policy output tables on `household_id`)
- Per-policy and portfolio-level metadata in `YearState`
- `PortfolioComputationStepError` exception class
- Tests for all acceptance criteria
- Export updates in `orchestrator/__init__.py`

**OUT OF SCOPE (deferred to future stories):**
- Cross-policy data flow (e.g., carbon tax revenue → rebate pool) — Story 12.5 or later
- `OrchestratorRunner` / `WorkflowResult` integration with portfolios — Story 12.4 or later
- Portfolio-aware `from_workflow_config()` factory — Story 12.4 or later
- Portfolio versioning in scenario registry — Story 12.4
- Multi-portfolio comparison — Story 12.5
- Modifications to `PanelOutput`, `Orchestrator`, `ComputationAdapter`, or any existing step

### Project Structure Notes

**New files:**
```
src/reformlab/orchestrator/portfolio_step.py    ← PortfolioComputationStep, error, bridge, merge
tests/orchestrator/test_portfolio_step.py       ← All tests for this story
```

**Modified files:**
```
src/reformlab/orchestrator/__init__.py          ← Add exports (PortfolioComputationStep, error, keys)
tests/orchestrator/conftest.py                  ← Add portfolio fixtures
```

**Files NOT to modify:**
```
src/reformlab/orchestrator/runner.py            ← AC3: no changes
src/reformlab/orchestrator/types.py             ← AC3: no changes
src/reformlab/orchestrator/panel.py             ← AC3: no changes
src/reformlab/computation/adapter.py            ← AC3: no changes
src/reformlab/computation/types.py              ← no changes
src/reformlab/orchestrator/computation_step.py  ← AC4: unchanged
src/reformlab/orchestrator/step.py              ← no changes
```

### Code Conventions to Follow

- `from __future__ import annotations` at top of every file
- `if TYPE_CHECKING:` guards for imports only needed for type annotations
- Frozen dataclasses for all domain types; mutate via `dataclasses.replace()`
- `__slots__` on step classes (matching `ComputationStep` pattern)
- Stable string-constant keys at module level (e.g., `PORTFOLIO_METADATA_KEY`)
- Structured log format: `key=value` pairs (e.g., `event=portfolio_policy_computed year=2025 policy_index=0`)
- `logging.getLogger(__name__)` for logger
- Section separators `# ====...====` for major sections in longer modules
- Exception hierarchy: `PortfolioComputationStepError(Exception)` with structured attributes

### MockAdapter Usage in Tests

The `MockAdapter` [Source: src/reformlab/computation/mock_adapter.py] supports two modes:
1. Fixed output: `MockAdapter(default_output=pa.table(...))` — returns same table for every `compute()` call
2. Custom function: `MockAdapter(compute_fn=lambda pop, policy, period: pa.table(...))` — can vary output per call

For portfolio tests, use `compute_fn` mode to return different column sets per policy, verifying the merge logic. Use `mock_adapter.call_log` to assert each policy was computed.

Example pattern from existing tests [Source: tests/orchestrator/test_computation_step.py]:
```python
@pytest.fixture
def mock_adapter():
    output_table = pa.table({"household_id": [1, 2, 3], "tax_burden": [100.0, 200.0, 300.0]})
    return MockAdapter(default_output=output_table)
```

For portfolio tests, create a `compute_fn` that returns policy-type-specific columns:
```python
def portfolio_compute_fn(population, policy, period):
    if "carbon_tax" in policy.name:
        return pa.table({"household_id": [1, 2], "tax_burden": [100.0, 200.0]})
    elif "subsidy" in policy.name:
        return pa.table({"household_id": [1, 2], "subsidy_amount": [50.0, 75.0]})
    ...
```

### Performance Considerations

Portfolio execution scales linearly with policy count — N adapter calls per year step. For typical portfolios (2-5 policies), this is negligible. No optimization needed.

The result merge (`_merge_policy_results`) uses PyArrow table operations which are efficient for typical household counts (10k-100k rows).

### References

- [Source: docs/prd.md#FR44] — "System executes a simulation with a policy portfolio, applying all bundled policies together."
- [Source: docs/epics.md#BKL-1203] — Story acceptance criteria
- [Source: src/reformlab/orchestrator/computation_step.py] — `ComputationStep` pattern to follow
- [Source: src/reformlab/orchestrator/runner.py:342-346] — Runner metadata extraction requiring `COMPUTATION_METADATA_KEY`
- [Source: src/reformlab/orchestrator/panel.py:58-110] — `PanelOutput.from_orchestrator_result()` reading `COMPUTATION_RESULT_KEY`
- [Source: src/reformlab/templates/portfolios/portfolio.py] — `PolicyPortfolio` and `PolicyConfig` (portfolio type)
- [Source: src/reformlab/computation/types.py:29-35] — `PolicyConfig` (computation type)
- [Source: src/reformlab/orchestrator/step.py:42-70] — `OrchestratorStep` protocol
- [Source: src/reformlab/computation/mock_adapter.py] — `MockAdapter` for testing
- [Source: docs/project-context.md#Architecture] — Adapter isolation, step pipeline contract, frozen dataclasses
- [Source: _bmad-output/implementation-artifacts/12-1-*.md] — Story 12.1 decisions on `PolicyConfig` as new frozen dataclass
- [Source: _bmad-output/implementation-artifacts/12-2-*.md] — Story 12.2 code review, enum extraction, conflict resolution

## Dev Agent Record

### Agent Model Used


### Debug Log References


### Completion Notes List


### File List



]]></file>
</context>
<variables>
<var name="architecture_file" file_id="40d1dade" description="Architecture for technical requirements verification" load_strategy="EMBEDDED" token_approx="3279">embedded in prompt, file id: 40d1dade</var>
<var name="author">BMad</var>
<var name="communication_language">English</var>
<var name="date">2026-03-06</var>
<var name="description">Quality competition validator - systematically review and improve story context created by create-story workflow</var>
<var name="document_output_language">English</var>
<var name="epic_num">12</var>
<var name="epics_file" description="Enhanced epics+stories file for story verification" load_strategy="SELECTIVE_LOAD" token_approx="22457">_bmad-output/planning-artifacts/epics.md</var>
<var name="implementation_artifacts">_bmad-output/implementation-artifacts</var>
<var name="instructions">embedded context</var>
<var name="model">validator</var>
<var name="name">validate-story</var>
<var name="output_folder">_bmad-output/implementation-artifacts</var>
<var name="planning_artifacts">_bmad-output/planning-artifacts</var>
<var name="prd_file" description="PRD for requirements verification" load_strategy="SELECTIVE_LOAD" token_approx="10735">docs/prd.md</var>
<var name="project_context" file_id="e58fb4dd" load_strategy="EMBEDDED" token_approx="2024">embedded in prompt, file id: e58fb4dd</var>
<var name="project_knowledge">docs</var>
<var name="project_name">reformlab</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_dir">_bmad-output/implementation-artifacts</var>
<var name="story_file" file_id="78cc87c5">embedded in prompt, file id: 78cc87c5</var>
<var name="story_id">12.3</var>
<var name="story_key">12-3-extend-orchestrator-to-execute-policy-portfolios</var>
<var name="story_num">3</var>
<var name="story_title">extend-orchestrator-to-execute-policy-portfolios</var>
<var name="template">embedded context</var>
<var name="timestamp">20260306_121142</var>
<var name="user_name">User</var>
<var name="user_skill_level">expert</var>
<var name="ux_file" description="UX design for user experience verification" load_strategy="SELECTIVE_LOAD">_bmad-output/planning-artifacts/*ux*.md</var>
<var name="validation_focus">story_quality</var>
</variables>
<instructions><workflow>
  <critical>SCOPE LIMITATION: You are a READ-ONLY VALIDATOR. Output your validation report to stdout ONLY. Do NOT create files, do NOT modify files, do NOT use Write/Edit/Bash tools. Your stdout output will be captured and saved by the orchestration system.</critical>
  <critical>All configuration and context is available in the VARIABLES section below. Use these resolved values directly.</critical>
  <critical>Communicate all responses in English and generate all documents in English</critical>

  <critical>🔥 CRITICAL MISSION: You are an independent quality validator in a FRESH CONTEXT competing against the original create-story LLM!</critical>
  <critical>Your purpose is to thoroughly review a story file and systematically identify any mistakes, omissions, or disasters that the original LLM missed</critical>
  <critical>🚨 COMMON LLM MISTAKES TO PREVENT: reinventing wheels, wrong libraries, wrong file locations, breaking regressions, ignoring UX, vague implementations, lying about completion, not learning from past work</critical>
  <critical>🔬 UTILIZE SUBPROCESSES AND SUBAGENTS: Use research subagents or parallel processing if available to thoroughly analyze different artifacts simultaneously</critical>

  <step n="1" goal="Story Quality Gate - INVEST validation">
    <critical>🎯 RUTHLESS STORY VALIDATION: Check story quality with surgical precision!</critical>
    <critical>This assessment determines if the story is fundamentally sound before deeper analysis</critical>

    <substep n="1a" title="INVEST Criteria Validation">
      <action>Evaluate each INVEST criterion with severity score (1-10, where 10 is critical violation):</action>

      <action>**I - Independent:** Check if story can be developed independently
        - Does it have hidden dependencies on other stories?
        - Can it be implemented without waiting for other work?
        - Are there circular dependencies?
        Score severity of any violations found
      </action>

      <action>**N - Negotiable:** Check if story allows implementation flexibility
        - Is it overly prescriptive about HOW vs WHAT?
        - Does it leave room for technical decisions?
        - Are requirements stated as outcomes, not solutions?
        Score severity of any violations found
      </action>

      <action>**V - Valuable:** Check if story delivers clear business value
        - Is the benefit clearly stated and meaningful?
        - Does it contribute to epic/product goals?
        - Would stakeholder recognize the value?
        Score severity of any violations found
      </action>

      <action>**E - Estimable:** Check if story can be accurately estimated
        - Are requirements clear enough to estimate?
        - Is scope well-defined without ambiguity?
        - Are there unknown technical risks that prevent estimation?
        Score severity of any violations found
      </action>

      <action>**S - Small:** Check if story is appropriately sized
        - Can it be completed in a single sprint?
        - Is it too large and should be split?
        - Is it too small to be meaningful?
        Score severity of any violations found
      </action>

      <action>**T - Testable:** Check if story has testable acceptance criteria
        - Are acceptance criteria specific and measurable?
        - Can each criterion be verified objectively?
        - Are edge cases and error scenarios covered?
        Score severity of any violations found
      </action>

      <action>Store INVEST results: {{invest_results}} with individual scores</action>
    </substep>

    <substep n="1b" title="Acceptance Criteria Deep Analysis">
      <action>Hunt for acceptance criteria issues:
        - Ambiguous criteria: Vague language like "should work well", "fast", "user-friendly"
        - Untestable criteria: Cannot be objectively verified
        - Missing criteria: Expected behaviors not covered
        - Conflicting criteria: Criteria that contradict each other
        - Incomplete scenarios: Missing edge cases, error handling, boundary conditions
      </action>
      <action>Document each issue with specific quote and recommendation</action>
      <action>Store as {{acceptance_criteria_issues}}</action>
    </substep>

    <substep n="1c" title="Hidden Dependencies Discovery">
      <action>Uncover hidden dependencies and future sprint-killers:
        - Undocumented technical dependencies (libraries, services, APIs)
        - Cross-team dependencies not mentioned
        - Infrastructure dependencies (databases, queues, caches)
        - Data dependencies (migrations, seeds, external data)
        - Sequential dependencies on other stories
        - External blockers (third-party services, approvals)
      </action>
      <action>Document each hidden dependency with impact assessment</action>
      <action>Store as {{hidden_dependencies}}</action>
    </substep>

    <substep n="1d" title="Estimation Reality-Check">
      <action>Reality-check the story estimate against complexity:
        - Compare stated/implied effort vs actual scope
        - Check for underestimated technical complexity
        - Identify scope creep risks
        - Assess if unknown unknowns are accounted for
        - Compare with similar stories from previous work
      </action>
      <action>Provide estimation assessment: realistic / underestimated / overestimated / unestimable</action>
      <action>Store as {{estimation_assessment}}</action>
    </substep>

    <substep n="1e" title="Technical Alignment Verification">
      <action>Verify alignment with /Users/lucas/Workspace/reformlab/docs/architecture.md patterns:
        - Does story follow established architectural patterns?
        - Are correct technologies/frameworks specified?
        - Does it respect defined boundaries and layers?
        - Are naming conventions and file structures aligned?
        - Does it integrate correctly with existing components?
      </action>
      <action>Document any misalignments or conflicts</action>
      <action>Store as {{technical_alignment_issues}}</action>
    </substep>

    <o>🎯 **Story Quality Gate Results:**
      - INVEST Violations: {{invest_violation_count}}
      - Acceptance Criteria Issues: {{ac_issues_count}}
      - Hidden Dependencies: {{hidden_deps_count}}
      - Estimation: {{estimation_assessment}}
      - Technical Alignment: {{alignment_status}}

      ℹ️ Continuing with full analysis...
    </o>
  </step>

  <step n="2" goal="Disaster prevention gap analysis">
    <critical>🚨 CRITICAL: Identify every mistake the original LLM missed that could cause DISASTERS!</critical>

    <substep n="2a" title="Reinvention Prevention Gaps">
      <action>Analyze for wheel reinvention risks:
        - Areas where developer might create duplicate functionality
        - Code reuse opportunities not identified
        - Existing solutions not mentioned that developer should extend
        - Patterns from previous stories not referenced
      </action>
      <action>Document each reinvention risk found</action>
    </substep>

    <substep n="2b" title="Technical Specification Disasters">
      <action>Analyze for technical specification gaps:
        - Wrong libraries/frameworks: Missing version requirements
        - API contract violations: Missing endpoint specifications
        - Database schema conflicts: Missing requirements that could corrupt data
        - Security vulnerabilities: Missing security requirements
        - Performance disasters: Missing requirements that could cause failures
      </action>
      <action>Document each technical specification gap</action>
    </substep>

    <substep n="2c" title="File Structure Disasters">
      <action>Analyze for file structure issues:
        - Wrong file locations: Missing organization requirements
        - Coding standard violations: Missing conventions
        - Integration pattern breaks: Missing data flow requirements
        - Deployment failures: Missing environment requirements
      </action>
      <action>Document each file structure issue</action>
    </substep>

    <substep n="2d" title="Regression Disasters">
      <action>Analyze for regression risks:
        - Breaking changes: Missing requirements that could break existing functionality
        - Test failures: Missing test requirements
        - UX violations: Missing user experience requirements
        - Learning failures: Missing previous story context
      </action>
      <action>Document each regression risk</action>
    </substep>

    <substep n="2e" title="Implementation Disasters">
      <action>Analyze for implementation issues:
        - Vague implementations: Missing details that could lead to incorrect work
        - Completion lies: Missing acceptance criteria that could allow fake implementations
        - Scope creep: Missing boundaries that could cause unnecessary work
        - Quality failures: Missing quality requirements
      </action>
      <action>Document each implementation issue</action>
    </substep>
  </step>

  <step n="3" goal="LLM-Dev-Agent optimization analysis">
    <critical>CRITICAL: Optimize story context for LLM developer agent consumption</critical>

    <action>Analyze current story for LLM optimization issues:
      - Verbosity problems: Excessive detail that wastes tokens without adding value
      - Ambiguity issues: Vague instructions that could lead to multiple interpretations
      - Context overload: Too much information not directly relevant to implementation
      - Missing critical signals: Key requirements buried in verbose text
      - Poor structure: Information not organized for efficient LLM processing
    </action>

    <action>Apply LLM Optimization Principles:
      - Clarity over verbosity: Be precise and direct, eliminate fluff
      - Actionable instructions: Every sentence should guide implementation
      - Scannable structure: Clear headings, bullet points, and emphasis
      - Token efficiency: Pack maximum information into minimum text
      - Unambiguous language: Clear requirements with no room for interpretation
    </action>

    <action>Document each LLM optimization opportunity</action>
  </step>

  <step n="4" goal="Categorize and prioritize improvements">
    <action>Categorize all identified issues into:
      - critical_issues: Must fix - essential requirements, security, blocking issues
      - enhancements: Should add - helpful guidance, better specifications
      - optimizations: Nice to have - performance hints, development tips
      - llm_optimizations: Token efficiency and clarity improvements
    </action>

    <action>Count issues in each category:
      - {{critical_count}} critical issues
      - {{enhancement_count}} enhancements
      - {{optimization_count}} optimizations
      - {{llm_opt_count}} LLM optimizations
    </action>

    <action>Assign numbers to each issue for user selection</action>

    <substep n="4b" title="Calculate Evidence Score">
      <critical>🔥 CRITICAL: You MUST calculate and output the Evidence Score for synthesis!</critical>

      <action>Map each finding to Evidence Score severity:
        - **🔴 CRITICAL** (+3 points): Security vulnerabilities, data corruption risks, blocking issues, missing essential requirements
        - **🟠 IMPORTANT** (+1 point): Missing guidance, unclear specifications, integration risks
        - **🟡 MINOR** (+0.3 points): Typos, style issues, minor clarifications
      </action>

      <action>Count CLEAN PASS categories - areas with NO issues found:
        - Each clean category: -0.5 points
        - Categories to check: INVEST criteria (6), Acceptance Criteria, Dependencies, Technical Alignment, Implementation
      </action>

      <action>Calculate Evidence Score:
        {{evidence_score}} = SUM(finding_scores) + (clean_pass_count × -0.5)

        Example: 2 CRITICAL (+6) + 1 IMPORTANT (+1) + 4 CLEAN PASSES (-2) = 5.0
      </action>

      <action>Determine Evidence Verdict:
        - **EXCELLENT** (score ≤ -3): Many clean passes, minimal issues
        - **PASS** (score &lt; 3): Acceptable quality, minor issues only
        - **MAJOR REWORK** (3 ≤ score &lt; 7): Significant issues require attention
        - **REJECT** (score ≥ 7): Critical problems, needs complete rewrite
      </action>

      <action>Store for template output:
        - {{evidence_findings}}: List of findings with severity_icon, severity, description, source, score
        - {{clean_pass_count}}: Number of clean categories
        - {{evidence_score}}: Calculated total score
        - {{evidence_verdict}}: EXCELLENT/PASS/MAJOR REWORK/REJECT
      </action>
    </substep>
  </step>

  <step n="5" goal="Generate validation report">
    <critical>OUTPUT MARKERS REQUIRED: Your validation report MUST start with the marker &lt;!-- VALIDATION_REPORT_START --&gt; on its own line BEFORE the report header, and MUST end with the marker &lt;!-- VALIDATION_REPORT_END --&gt; on its own line AFTER the final line. The orchestrator extracts ONLY content between these markers. Any text outside the markers (thinking, commentary) will be discarded.</critical>

    <action>Use the output template as a FORMAT GUIDE, replacing all {{placeholders}} with your actual analysis from steps 1-4</action>
    <action>Output the complete validation report to stdout with all sections filled in</action>
    <action>Do NOT save to any file - the orchestrator handles persistence</action>
  </step>

</workflow></instructions>
<output-template><![CDATA[

<!-- VALIDATION_REPORT_START -->

# 🎯 Story Context Validation Report

<!-- report_header -->

**Story:** {{story_key}} - {{story_title}}
**Story File:** {{story_file}}
**Validated:** {{date}}
**Validator:** Quality Competition Engine

---

<!-- executive_summary -->

## Executive Summary

### Issues Overview

| Category | Found | Applied |
|----------|-------|---------|
| 🚨 Critical Issues | {{critical_count}} | {{critical_applied}} |
| ⚡ Enhancements | {{enhancement_count}} | {{enhancements_applied}} |
| ✨ Optimizations | {{optimization_count}} | {{optimizations_applied}} |
| 🤖 LLM Optimizations | {{llm_opt_count}} | {{llm_opts_applied}} |

**Overall Assessment:** {{overall_assessment}}

---

<!-- evidence_score_summary -->

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
{{#each evidence_findings}}
| {{severity_icon}} {{severity}} | {{description}} | {{source}} | +{{score}} |
{{/each}}
{{#if clean_pass_count}}
| 🟢 CLEAN PASS | {{clean_pass_count}} |
{{/if}}

### Evidence Score: {{evidence_score}}

| Score | Verdict |
|-------|---------|
| **{{evidence_score}}** | **{{evidence_verdict}}** |

---

<!-- story_quality_gate -->

## 🎯 Ruthless Story Validation {{epic_num}}.{{story_num}}

### INVEST Criteria Assessment

| Criterion | Status | Severity | Details |
|-----------|--------|----------|---------|
| **I**ndependent | {{invest_i_status}} | {{invest_i_severity}}/10 | {{invest_i_details}} |
| **N**egotiable | {{invest_n_status}} | {{invest_n_severity}}/10 | {{invest_n_details}} |
| **V**aluable | {{invest_v_status}} | {{invest_v_severity}}/10 | {{invest_v_details}} |
| **E**stimable | {{invest_e_status}} | {{invest_e_severity}}/10 | {{invest_e_details}} |
| **S**mall | {{invest_s_status}} | {{invest_s_severity}}/10 | {{invest_s_details}} |
| **T**estable | {{invest_t_status}} | {{invest_t_severity}}/10 | {{invest_t_details}} |

### INVEST Violations

{{#each invest_violations}}
- **[{{severity}}/10] {{criterion}}:** {{description}}
{{/each}}

{{#if no_invest_violations}}
✅ No significant INVEST violations detected.
{{/if}}

### Acceptance Criteria Issues

{{#each acceptance_criteria_issues}}
- **{{issue_type}}:** {{description}}
  - *Quote:* "{{quote}}"
  - *Recommendation:* {{recommendation}}
{{/each}}

{{#if no_acceptance_criteria_issues}}
✅ Acceptance criteria are well-defined and testable.
{{/if}}

### Hidden Risks and Dependencies

{{#each hidden_dependencies}}
- **{{dependency_type}}:** {{description}}
  - *Impact:* {{impact}}
  - *Mitigation:* {{mitigation}}
{{/each}}

{{#if no_hidden_dependencies}}
✅ No hidden dependencies or blockers identified.
{{/if}}

### Estimation Reality-Check

**Assessment:** {{estimation_assessment}}

{{estimation_details}}

### Technical Alignment

**Status:** {{technical_alignment_status}}

{{#each technical_alignment_issues}}
- **{{issue_type}}:** {{description}}
  - *Architecture Reference:* {{architecture_reference}}
  - *Recommendation:* {{recommendation}}
{{/each}}

{{#if no_technical_alignment_issues}}
✅ Story aligns with architecture.md patterns.
{{/if}}

### Evidence Score: {{evidence_score}} → {{evidence_verdict}}

---

<!-- critical_issues_section -->

## 🚨 Critical Issues (Must Fix)

These are essential requirements, security concerns, or blocking issues that could cause implementation disasters.

{{#each critical_issues}}
### {{number}}. {{title}}

**Impact:** {{impact}}
**Source:** {{source_reference}}

**Problem:**
{{problem_description}}

**Recommended Fix:**
{{recommended_fix}}

{{/each}}

{{#if no_critical_issues}}
✅ No critical issues found - the original story covered essential requirements.
{{/if}}

---

<!-- enhancements_section -->

## ⚡ Enhancement Opportunities (Should Add)

Additional guidance that would significantly help the developer avoid mistakes.

{{#each enhancements}}
### {{number}}. {{title}}

**Benefit:** {{benefit}}
**Source:** {{source_reference}}

**Current Gap:**
{{gap_description}}

**Suggested Addition:**
{{suggested_addition}}

{{/each}}

{{#if no_enhancements}}
✅ No significant enhancement opportunities identified.
{{/if}}

---

<!-- optimizations_section -->

## ✨ Optimizations (Nice to Have)

Performance hints, development tips, and additional context for complex scenarios.

{{#each optimizations}}
### {{number}}. {{title}}

**Value:** {{value}}

**Suggestion:**
{{suggestion}}

{{/each}}

{{#if no_optimizations}}
✅ No additional optimizations identified.
{{/if}}

---

<!-- llm_optimizations_section -->

## 🤖 LLM Optimization Improvements

Token efficiency and clarity improvements for better dev agent processing.

{{#each llm_optimizations}}
### {{number}}. {{title}}

**Issue:** {{issue_type}}
**Token Impact:** {{token_impact}}

**Current:**
```
{{current_text}}
```

**Optimized:**
```
{{optimized_text}}
```

**Rationale:** {{rationale}}

{{/each}}

{{#if no_llm_optimizations}}
✅ Story content is well-optimized for LLM processing.
{{/if}}

---

<!-- changes_applied_section -->

## 📝 Changes Applied

{{#if changes_applied}}
The following improvements were applied to the story file:

{{#each applied_changes}}
- ✅ **{{category}}:** {{title}}
{{/each}}

**Total Changes:** {{changes_applied_count}}

**Updated Sections:**
{{#each updated_sections}}
- {{section_name}}
{{/each}}
{{/if}}

{{#if no_changes_applied}}
No changes were applied to the story file. This report serves as documentation only.
{{/if}}

---

<!-- competition_results -->

## 🏆 Competition Results

### Quality Metrics

| Metric | Score |
|--------|-------|
| Requirements Coverage | {{requirements_coverage}}% |
| Architecture Alignment | {{architecture_alignment}}% |
| Previous Story Integration | {{previous_story_integration}}% |
| LLM Optimization Score | {{llm_optimization_score}}% |
| **Overall Quality Score** | **{{overall_quality_score}}%** |

### Disaster Prevention Assessment

{{#each disaster_categories}}
- **{{category}}:** {{status}} {{details}}
{{/each}}

### Competition Outcome

{{#if validator_won}}
🏆 **Validator identified {{total_issues}} improvements** that enhance the story context.
{{/if}}

{{#if original_won}}
✅ **Original create-story produced high-quality output** with minimal gaps identified.
{{/if}}

---

**Report Generated:** {{date}}
**Validation Engine:** BMAD Method Quality Competition v1.0

<!-- VALIDATION_REPORT_END -->

]]></output-template>
</compiled-workflow>