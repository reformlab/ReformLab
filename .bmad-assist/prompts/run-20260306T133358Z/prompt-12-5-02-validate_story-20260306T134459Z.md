<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 12 -->
<!-- Story: 5 -->
<!-- Phase: validate-story -->
<!-- Timestamp: 20260306T134459Z -->
<compiled-workflow>
<mission><![CDATA[

Adversarial Story Validation

Target: Story 12.5 - implement-multi-portfolio-comparison-and-notebook-demo

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

Status: Ready for Review
Dependencies: Story 12.1 (PolicyPortfolio model), Story 12.2 (conflict detection/resolution)

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

- [x] 1.1 Create new file `src/reformlab/orchestrator/portfolio_step.py` with module docstring referencing Story 12.3 / FR44
- [x] 1.2 Define `PORTFOLIO_METADATA_KEY = "portfolio_metadata"` stable string constant
- [x] 1.3 Define `PORTFOLIO_RESULTS_KEY = "portfolio_results"` stable string constant for per-policy results
- [x] 1.4 Define `PortfolioComputationStepError(Exception)` with `year`, `adapter_version`, `policy_index`, `policy_name`, `policy_type`, `original_error` attributes
- [x] 1.5 Define `_to_computation_policy()` bridge function: converts `portfolios.PolicyConfig` (typed `PolicyParameters`) to `computation.types.PolicyConfig` (generic `dict[str, Any]`) via `dataclasses.asdict()`
- [x] 1.6 Implement `PortfolioComputationStep` class with `__slots__`, `OrchestratorStep` protocol compliance (`name`, `depends_on`, `description`, `execute()`)

### Task 2: Implement `PortfolioComputationStep.__init__()` (AC: 1, 5)

- [x] 2.1 Parameters: `adapter: ComputationAdapter`, `population: PopulationData`, `portfolio: PolicyPortfolio`, `name: str = "portfolio_computation"`, `depends_on: tuple[str, ...] = ()`, `description: str | None = None`
- [x] 2.2 Store all constructor args in `__slots__`
- [x] 2.3 Validate `portfolio.policies` has at least 2 entries (should be guaranteed by `PolicyPortfolio.__post_init__` but defensive check, matching the >=2 invariant)
- [x] 2.4 Validate each `PolicyConfig.policy_type` has a valid `PolicyType` value (fail fast at construction, not at runtime)

### Task 3: Implement `execute()` method (AC: 1, 2, 5, 6, 7)

- [x] 3.1 Get adapter version via `self._adapter.version()` with `"<version-unavailable>"` fallback (same pattern as `ComputationStep`)
- [x] 3.2 Iterate over `self._portfolio.policies` **in tuple order** (deterministic)
- [x] 3.3 For each policy: call `_to_computation_policy()` to create `computation.types.PolicyConfig`
- [x] 3.4 For each policy: call `self._adapter.compute(population=self._population, policy=comp_policy, period=year)`
- [x] 3.5 Collect all `ComputationResult` objects in an ordered list
- [x] 3.6 Build per-policy execution records for metadata: `{"policy_index": i, "policy_type": policy_type.value, "policy_name": name, "adapter_version": version, "row_count": num_rows}`
- [x] 3.7 Merge all `ComputationResult.output_fields` (`pa.Table`) into a single combined table via `_merge_policy_results()`
- [x] 3.8 Create a single `ComputationResult` with: `output_fields` = merged table, `adapter_version` = first policy's adapter version, `period` = year, `metadata` = `{"source": "portfolio", "policy_count": n}`, `entity_tables` = `{}` (multi-entity portfolio merging deferred). Store under `COMPUTATION_RESULT_KEY` (panel compatibility)
- [x] 3.9 Store all individual `ComputationResult` objects under `PORTFOLIO_RESULTS_KEY` in `state.data` (per-policy access)
- [x] 3.10 Store portfolio metadata under `PORTFOLIO_METADATA_KEY` in `state.metadata`
- [x] 3.11 Also store standard `COMPUTATION_METADATA_KEY` with merged info (so `runner.py:_execute_step()` can extract `adapter_version` from its existing metadata path)
- [x] 3.12 Return new `YearState` via `dataclasses.replace()` (immutable updates)

### Task 4: Implement `_merge_policy_results()` helper (AC: 1, 2)

- [x] 4.1 Create module-level function `_merge_policy_results(results: list[ComputationResult], portfolio: PolicyPortfolio) -> pa.Table`
- [x] 4.2 Strategy: join all output tables on `household_id`. For the first result, keep column names as-is. For subsequent results, prefix columns with `{policy_type}_` to avoid name collisions (e.g., `subsidy_amount`, `feebate_net_impact`)
- [x] 4.3 Require `household_id` column in every result table; raise `PortfolioComputationStepError` if missing (fail-loud per project data-contract rules — silent row-index alignment risks merging unrelated households across policies)
- [x] 4.4 Handle edge case: if all results have the same column names (e.g., two carbon tax policies after conflict resolution), prefix ALL with `{policy_type}_{index}_`
- [x] 4.5 Result table must contain ALL columns from ALL policies, plus `household_id`
- [x] 4.6 Deterministic column ordering: `household_id` first, then columns from each policy in portfolio order

### Task 5: Implement error handling (AC: 5)

- [x] 5.1 Wrap individual `adapter.compute()` calls in try/except; on failure, raise `PortfolioComputationStepError` with policy context
- [x] 5.2 Error message format: `"Portfolio computation failed at year {year}, policy[{idx}] '{policy_name}' ({policy_type}): {error_type}: {error}"`
- [x] 5.3 Structured log on error: `event=portfolio_computation_error year={year} policy_index={idx} policy_type={type} adapter_version={version}`
- [x] 5.4 Log INFO per policy execution: `event=portfolio_policy_computed year={year} policy_index={idx} policy_type={type} adapter_version={version} row_count={n}`
- [x] 5.5 Log INFO on portfolio completion: `event=portfolio_computation_complete year={year} portfolio={name} policy_count={n}`

### Task 6: Update `orchestrator/__init__.py` exports (AC: 3, 4)

- [x] 6.1 Add `PortfolioComputationStep`, `PortfolioComputationStepError`, `PORTFOLIO_METADATA_KEY`, `PORTFOLIO_RESULTS_KEY` to `__init__.py` exports under new section comment `# Portfolio step (Story 12-3)`
- [x] 6.2 Add to `__all__` list

### Task 7: Write tests in `tests/orchestrator/test_portfolio_step.py` (AC: all)

- [x] 7.1 Create test file with standard imports and module docstring referencing Story 12.3
- [x] 7.2 **TestPortfolioStepProtocol** (AC3): Verify `PortfolioComputationStep` satisfies `OrchestratorStep` protocol (has `name`, `depends_on`, `execute`, isinstance check)
- [x] 7.3 **TestPortfolioStepExecution** (AC1, AC2): Given 3-policy portfolio + `MockAdapter`, execute returns `YearState` with `COMPUTATION_RESULT_KEY` containing merged `ComputationResult`. Assert all policy columns present. Assert `MockAdapter.call_log` has 3 entries (one per policy). Assert `household_id` column present
- [x] 7.4 **TestPortfolioStepMergedOutput** (AC2): Merged table has columns from all policies with correct prefixing. Column order is deterministic (household_id first, then by policy order)
- [x] 7.5 **TestPortfolioStepMetadata** (AC7): `state.metadata[PORTFOLIO_METADATA_KEY]` contains portfolio name, policy count, per-policy records with policy_type/name/adapter_version/row_count
- [x] 7.6 **TestPortfolioStepMetadata_ComputationKey** (AC3): `state.metadata[COMPUTATION_METADATA_KEY]` is present (backward compat with `runner.py` metadata extraction)
- [x] 7.7 **TestPortfolioStepDeterminism** (AC6): Two runs with identical inputs produce identical `YearState` output (data and metadata)
- [x] 7.8 **TestPortfolioStepErrorHandling** (AC5): Adapter failure at policy[1] raises `PortfolioComputationStepError` with correct `policy_index=1`, `policy_name`, `policy_type`, `year`, `adapter_version`, `original_error`
- [x] 7.9 **TestPortfolioStepErrorHandling_VersionFallback** (AC5): Adapter with failing `version()` uses `"<version-unavailable>"` fallback
- [x] 7.10 **TestPortfolioStepBackwardCompat** (AC4): Existing `ComputationStep` continues to work unchanged in the same pipeline. Pipeline with `[PortfolioComputationStep, CarryForwardStep]` works
- [x] 7.11 **TestPortfolioStepInPipeline** (AC1, AC4): Full orchestrator run with `PortfolioComputationStep` in step pipeline over 3 years. Verify yearly states contain portfolio results for each year
- [x] 7.12 **TestPortfolioStepPanelIntegration** (AC2): Full orchestrator run → `PanelOutput.from_orchestrator_result()` produces panel with all policy columns across all years. Panel export to CSV/Parquet works
- [x] 7.13 **TestPolicyConfigBridge** (AC1): `_to_computation_policy()` converts `portfolios.PolicyConfig` → `computation.types.PolicyConfig` correctly. `rate_schedule`, `exemptions`, custom fields are preserved in the dict
- [x] 7.14 **TestPerPolicyResults** (AC1): `state.data[PORTFOLIO_RESULTS_KEY]` stores individual `ComputationResult` per policy, accessible by index

### Task 8: Add portfolio step fixtures to `tests/orchestrator/conftest.py` (AC: all)

- [x] 8.1 Add `sample_portfolio` fixture: 2-policy portfolio (carbon tax + subsidy) with test parameters
- [x] 8.2 Add `three_policy_portfolio` fixture: 3-policy portfolio (carbon tax + subsidy + feebate)
- [x] 8.3 Add `portfolio_computation_step` fixture: `PortfolioComputationStep` with `MockAdapter` and sample population
- [x] 8.4 Reuse existing `MockAdapter` patterns from `tests/orchestrator/test_computation_step.py`

### Task 9: Run quality checks (AC: all)

- [x] 9.1 Run `uv run pytest tests/orchestrator/test_portfolio_step.py -v` — all 36 tests pass
- [x] 9.2 Run `uv run pytest tests/orchestrator/ -v` — all 270 orchestrator tests pass (no regressions)
- [x] 9.3 Run `uv run pytest tests/templates/portfolios/ -v` — all 73 portfolio tests pass
- [x] 9.4 Run `uv run ruff check src/reformlab/orchestrator/portfolio_step.py tests/orchestrator/test_portfolio_step.py` — all checks passed
- [x] 9.5 Run `uv run mypy src/reformlab/orchestrator/portfolio_step.py` — passes strict mode
- [x] 9.6 Run full test suite: `uv run pytest tests/ -v` — 2077 passed (2 pre-existing doc-contract failures unrelated to this story)

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
1. All result tables MUST contain `household_id` — raise `PortfolioComputationStepError` if missing (fail-loud data contract)
2. First policy's columns keep their original names
3. Subsequent policies' columns are prefixed with `{policy_type}_` (e.g., `subsidy_amount`, `feebate_net_impact`)
4. `household_id` is shared (join key) — not duplicated
5. If two policies have the same `policy_type` (after conflict resolution), use `{policy_type}_{index}_` prefix

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

**`runner.py` metadata extraction** [Source: src/reformlab/orchestrator/runner.py `_execute_step()`]:
The orchestrator runner reads `COMPUTATION_METADATA_KEY` from `state.metadata` to extract `adapter_version`. `PortfolioComputationStep` MUST populate this key for backward compatibility with the runner's step execution logging.

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
- [Source: src/reformlab/orchestrator/runner.py `_execute_step()`] — Runner metadata extraction requiring `COMPUTATION_METADATA_KEY`
- [Source: src/reformlab/orchestrator/panel.py `from_orchestrator_result()`] — `PanelOutput` reading `COMPUTATION_RESULT_KEY`
- [Source: src/reformlab/templates/portfolios/portfolio.py] — `PolicyPortfolio` and `PolicyConfig` (portfolio type)
- [Source: src/reformlab/computation/types.py:29-35] — `PolicyConfig` (computation type)
- [Source: src/reformlab/orchestrator/step.py:42-70] — `OrchestratorStep` protocol
- [Source: src/reformlab/computation/mock_adapter.py] — `MockAdapter` for testing
- [Source: docs/project-context.md#Architecture] — Adapter isolation, step pipeline contract, frozen dataclasses
- [Source: _bmad-output/implementation-artifacts/12-1-*.md] — Story 12.1 decisions on `PolicyConfig` as new frozen dataclass
- [Source: _bmad-output/implementation-artifacts/12-2-*.md] — Story 12.2 code review, enum extraction, conflict resolution

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — all tests passed on first run after lint fixes.

### Completion Notes List

- Implemented `PortfolioComputationStep` in `src/reformlab/orchestrator/portfolio_step.py` following `ComputationStep` patterns
- Bridge function `_to_computation_policy()` converts portfolio `PolicyConfig` to computation `PolicyConfig` via `dataclasses.asdict()`
- Result merge joins on `household_id` with policy-type prefixing for subsequent policies; indexed prefixing for duplicate policy types
- All 7 acceptance criteria satisfied with 36 dedicated tests across 12 test classes
- No modifications to `runner.py`, `types.py`, `panel.py`, `adapter.py`, or `computation_step.py` (AC3 satisfied)
- Backward compatibility verified: existing `ComputationStep` works unchanged (AC4)
- Panel integration verified: `PanelOutput.from_orchestrator_result()` works with portfolio results, CSV/Parquet export tested (AC2)
- ruff clean, mypy strict passes, 270 orchestrator tests pass with no regressions
- **Code Review Synthesis (2026-03-06):** Fixed `_merge_policy_results()` — added household_id set consistency and uniqueness validation (fail-loud), changed join from `inner` to `left outer`, optimized table construction. Stored per-policy results as `tuple` for immutability. Added 3 new tests (39 total). Fixed conftest type hint. 273 orchestrator tests pass.

### Change Log

- 2026-03-06: Story 12.3 implemented — PortfolioComputationStep, bridge function, result merging, error handling, 36 tests
- 2026-03-06: Code Review Synthesis — hardened merge validation, immutability fix, 3 new tests

### File List

**New files:**
- `src/reformlab/orchestrator/portfolio_step.py`
- `tests/orchestrator/test_portfolio_step.py`

**Modified files:**
- `src/reformlab/orchestrator/__init__.py` (added portfolio step exports)
- `tests/orchestrator/conftest.py` (added portfolio fixtures)

## Senior Developer Review (AI)

### Review: 2026-03-06
- **Reviewer:** AI Code Review Synthesis
- **Evidence Score:** 5.2 (Reviewer A) / 10.8 (Reviewer B) → Changes Requested
- **Issues Found:** 6 verified
- **Issues Fixed:** 5
- **Action Items Created:** 1

#### Review Follow-ups (AI)
- [ ] [AI-Review] MEDIUM: `PolicyConfig.__post_init__` in `portfolio.py:43` accesses `self.policy_type.value` without guarding against non-enum input — should use `str(self.policy_type)` or `getattr(self.policy_type, 'value', str(self.policy_type))` to produce a structured error instead of `AttributeError` (`src/reformlab/templates/portfolios/portfolio.py`)


]]></file>
<file id="4f02ed14" path="_bmad-output/implementation-artifacts/12-4-extend-scenario-registry-with-portfolio-versioning.md" label="STORY FILE"><![CDATA[

# Story 12.4: Extend Scenario Registry with Portfolio Versioning

Status: ready-for-dev
Dependencies: Story 12.1 (PolicyPortfolio model), Story 12.2 (conflict detection/resolution)

## Story

As a **policy analyst**,
I want to save, version, and retrieve policy portfolios through the same scenario registry used for individual scenarios,
so that I can track portfolio evolution over time and distinguish portfolios from individual scenarios when browsing the registry.

## Acceptance Criteria

### AC1: Portfolio save and retrieval by version ID
Given a `PolicyPortfolio` saved to the registry, when retrieved by version ID, then the returned portfolio is identical to what was saved, including all constituent policies (policy types, parameters, names, resolution strategy, description).

### AC2: New version on content change
Given a portfolio, when a constituent policy is modified and the portfolio is re-saved, then a new version ID is assigned. The previous version remains accessible by its version ID.

### AC3: Type-distinguishable listing
Given the registry, when queried, then portfolios and individual scenarios are both listable and distinguishable by type. The developer can determine whether a registry entry is a `BaselineScenario`, `ReformScenario`, or `PolicyPortfolio`.

### AC4: Content-addressable versioning
Given a portfolio saved to the registry, when the same portfolio (identical content) is saved again, then the registry returns the existing version ID (idempotent save). The version ID is deterministic — same content always produces the same 12-character hex ID.

### AC5: Round-trip fidelity
Given a portfolio saved and then retrieved from the registry, when compared to the original, then all fields are identical: `name`, `policies` (including each `PolicyConfig`'s `policy_type`, `policy`, `name`), `version`, `description`, `resolution_strategy`. Frozen dataclass equality (`==`) holds.

### AC6: Version history and lineage
Given multiple saves of a portfolio (with modifications between saves), when `list_versions()` is called, then all versions are returned as `ScenarioVersion` objects in chronological order. Each entry contains: `version_id` (12-char hex), `timestamp` (UTC datetime), `change_description` (user-provided string), and `parent_version` (previous version ID or `None` for first version).

### AC7: Error handling
Given an invalid portfolio name (empty, path traversal), when `save()` is called, then a `RegistryError` is raised with actionable fields (`summary`, `reason`, `fix`). Given a non-existent portfolio name or version ID, when `get()` is called, then `ScenarioNotFoundError` or `VersionNotFoundError` is raised with available alternatives listed. Given an attempt to save a portfolio under an existing scenario name (or vice versa), then a `RegistryError` is raised indicating the entry type mismatch. Given a portfolio entry, when `migrate()` is called, then a `RegistryError` is raised indicating migration is not supported for portfolios.

## Tasks / Subtasks

### Task 1: Add portfolio serialization support to registry (AC: 1, 4, 5)

- [ ] 1.1 Create `_portfolio_to_dict_for_registry(portfolio: PolicyPortfolio) -> dict[str, Any]` in `registry.py`. Use existing `portfolio_to_dict()` from `portfolios.composition` as the base, but: (a) replace the `$schema` value with a stable relative path (e.g., `"portfolio.schema.json"`) — `portfolio_to_dict()` emits a machine-specific absolute path via `Path(__file__)` which would break cross-machine version ID determinism; (b) add a `"_registry_type": "portfolio"` marker field to distinguish from scenarios in the metadata/version YAML files
- [ ] 1.2 Create `_generate_portfolio_version_id(portfolio: PolicyPortfolio) -> str` using SHA-256 of `yaml.dump(content, sort_keys=True)` with 12-char hex prefix — same pattern as `_generate_version_id()` for scenarios
- [ ] 1.3 Create `_dict_to_portfolio(data: dict[str, Any]) -> PolicyPortfolio` to reconstruct a `PolicyPortfolio` from registry YAML dict. Reuse `dict_to_portfolio()` from `portfolios.composition` after stripping the `_registry_type` marker

### Task 2: Extend `ScenarioRegistry.save()` to accept portfolios (AC: 1, 2, 4)

- [ ] 2.1 Widen `save()` signature to accept `BaselineScenario | ReformScenario | PolicyPortfolio`
- [ ] 2.2 Detect portfolio type with `isinstance(scenario, PolicyPortfolio)` and route to portfolio-specific version ID generation and serialization
- [ ] 2.3 Store portfolio YAML version files in the same directory structure: `{registry_path}/{name}/versions/{version_id}.yaml`
- [ ] 2.4 Store a `"_registry_type"` field in `metadata.yaml` with value `"baseline"`, `"reform"`, or `"portfolio"` based on artifact type. Determine scenario subtype via `isinstance(scenario, ReformScenario)` → `"reform"`, else `"baseline"`. For backward compat, legacy entries without this field infer type from the latest version content (presence of `baseline_ref` → `"reform"`, absence → `"baseline"`)
- [ ] 2.5 Portfolio save follows identical metadata update pattern: parent_version tracking, timestamp, change_description
- [ ] 2.6 Idempotent save: if content-addressable version ID already exists with identical content, return existing version ID without creating a new entry
- [ ] 2.7 Type-consistency guard: if metadata already exists for the given name, compare the stored `_registry_type` against the incoming artifact type. Reject mismatches (e.g., saving a portfolio under an existing scenario name) with `RegistryError(summary="Entry type mismatch", reason=..., fix="Use a different name or save as the correct type")`

### Task 3: Extend `ScenarioRegistry.get()` to return portfolios (AC: 1, 5)

- [ ] 3.1 Widen `get()` return type to `BaselineScenario | ReformScenario | PolicyPortfolio`
- [ ] 3.2 Check `_registry_type` in metadata to determine whether to call `_dict_to_scenario()` or `_dict_to_portfolio()` for deserialization
- [ ] 3.3 Portfolio integrity check: regenerate version ID from loaded content and compare to file name (same pattern as `_ensure_version_integrity()` for scenarios)

### Task 4: Add type-distinguishable listing (AC: 3)

- [ ] 4.1 Add `get_entry_type(name: str) -> str` method returning `"baseline"`, `"reform"`, or `"portfolio"` by reading `_registry_type` from metadata.yaml. For legacy entries without the `_registry_type` field, infer type by loading the latest version file and checking for `baseline_ref` (present → `"reform"`, absent → `"baseline"`). Persist the inferred type back to metadata for future reads
- [ ] 4.2 Update `RegistryEntry` to include an `entry_type: str` field (default `"scenario"` for backward compat of callers constructing `RegistryEntry` directly). Registry-populated entries use `"baseline"`, `"reform"`, or `"portfolio"` from metadata `_registry_type`
- [ ] 4.3 Update `get_entry()` to populate the new `entry_type` field from metadata
- [ ] 4.4 Add `list_portfolios() -> list[str]` convenience method that filters `list_scenarios()` by `_registry_type == "portfolio"`
- [ ] 4.5 Keep `list_scenarios()` returning ALL entries (both scenarios and portfolios) for backward compatibility. Document that it returns all registry entries regardless of type

### Task 5: Extend supporting methods for portfolios (AC: 6, 7)

- [ ] 5.1 `list_versions(name)` — works for portfolios unchanged (metadata structure is identical)
- [ ] 5.2 `exists(name, version_id)` — works for portfolios unchanged
- [ ] 5.3 `clone(name, version_id, new_name)` — extend to support portfolios: detect type, call `replace(portfolio, name=clone_name)` for `PolicyPortfolio`
- [ ] 5.4 `set_validated()` / `is_validated()` — work for portfolios unchanged (metadata-level operations)
- [ ] 5.5 `_ensure_version_integrity()` — create portfolio-aware variant that uses `_generate_portfolio_version_id()` for content hash verification
- [ ] 5.6 `migrate()` — add an early guard: if the entry is a portfolio (`_registry_type == "portfolio"` in metadata), raise `RegistryError(summary="Migration not supported for portfolios", ...)`. Portfolio migration is out of scope (see Scope Boundaries). `get_baseline()` and `list_reforms()` are naturally safe — they use `isinstance` checks that reject non-scenario types

### Task 6: Extend `_save_scenario_file()` and `_load_scenario_file()` (AC: 1, 5)

- [ ] 6.1 Rename or generalize `_save_scenario_file()` to handle both scenarios and portfolios. Use atomic write pattern (temp file + `os.replace()`) — same as existing implementation
- [ ] 6.2 Rename or generalize `_load_scenario_file()` to detect `_registry_type` in loaded YAML and dispatch to correct deserialization
- [ ] 6.3 Portfolio YAML uses `yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)` — same serialization options as scenarios (note: `sort_keys=False` for version files, `sort_keys=True` for version ID generation — matching existing scenario pattern)

### Task 7: Update `__init__.py` exports (AC: all)

- [ ] 7.1 If `RegistryEntry` gains `entry_type` field, no new exports needed (existing exports cover it)
- [ ] 7.2 Add `list_portfolios` to `ScenarioRegistry` (new method, no separate export needed — it's a method on the class)
- [ ] 7.3 Update module docstring in `registry.py` to mention portfolio support

### Task 8: Write tests in `tests/templates/test_registry_portfolios.py` (AC: all)

- [ ] 8.1 Create new test file with module docstring referencing Story 12.4
- [ ] 8.2 **TestPortfolioRegistrySaveAndGet** (AC1, AC5): Save a 2-policy portfolio, retrieve by version ID, assert frozen dataclass equality (`==`). Verify all fields: name, policies (each PolicyConfig), version, description, resolution_strategy
- [ ] 8.3 **TestPortfolioRegistryVersioning** (AC2, AC4): Save portfolio, modify a policy, re-save. Assert different version IDs. Assert both versions retrievable. Assert idempotent save (same content = same version ID)
- [ ] 8.4 **TestPortfolioRegistryListing** (AC3): Save both a scenario and a portfolio. Call `list_scenarios()` — both present. Call `list_portfolios()` — only portfolio. Call `get_entry()` — `entry_type` distinguishes them
- [ ] 8.5 **TestPortfolioRegistryVersionHistory** (AC6): Save 3 versions of a portfolio. `list_versions()` returns 3 entries in chronological order with correct parent_version links and change descriptions
- [ ] 8.6 **TestPortfolioRegistryClone** (AC1): Clone a portfolio, assert new name, identical policies
- [ ] 8.7 **TestPortfolioRegistryErrors** (AC7): Invalid name raises `RegistryError`. Non-existent portfolio raises `ScenarioNotFoundError`. Non-existent version raises `VersionNotFoundError`. Saving a portfolio under an existing scenario name raises `RegistryError` (type mismatch). Calling `migrate()` on a portfolio entry raises `RegistryError`
- [ ] 8.8 **TestPortfolioRegistryIntegrity** (AC4): Content integrity check passes on load. Tampered version file detected
- [ ] 8.9 **TestPortfolioRegistryRoundTrip** (AC5): Save → get round-trip preserves full PolicyPortfolio equality including nested PolicyConfig objects with CarbonTaxParameters, SubsidyParameters, FeebateParameters
- [ ] 8.10 **TestPortfolioRegistryValidatedFlag** (AC6): `set_validated()` / `is_validated()` work for portfolio entries
- [ ] 8.11 **TestPortfolioRegistryBackwardCompat** (AC3): Registry with pre-existing scenario entries (no `_registry_type` field) still works correctly. Default type is inferred as scenario

### Task 9: Run quality checks (AC: all)

- [ ] 9.1 Run `uv run pytest tests/templates/test_registry_portfolios.py -v` — all tests pass
- [ ] 9.2 Run `uv run pytest tests/templates/test_registry.py -v` — all existing registry tests pass (no regressions)
- [ ] 9.3 Run `uv run pytest tests/templates/portfolios/ -v` — all portfolio tests pass
- [ ] 9.4 Run `uv run ruff check src/reformlab/templates/registry.py tests/templates/test_registry_portfolios.py`
- [ ] 9.5 Run `uv run mypy src/reformlab/templates/registry.py` — passes strict mode
- [ ] 9.6 Run full test suite: `uv run pytest tests/ -v`

## Dev Notes

### Architecture Decisions

**Design: Extend ScenarioRegistry, don't create a separate PortfolioRegistry**

The acceptance criteria require "portfolios and individual scenarios are both listable and distinguishable by type" from the same registry. This means extending `ScenarioRegistry` to handle `PolicyPortfolio` alongside `BaselineScenario` and `ReformScenario`, not creating a parallel registry class.

Key reasons:
1. Registry directory structure and metadata pattern are generic — they work for any versioned, content-addressable artifact
2. Users expect a single registry to browse all policy artifacts
3. Avoids duplicating file I/O, metadata parsing, version history, integrity checks

**Design: `_registry_type` marker for type discrimination**

The version YAML files need a way to indicate whether they contain a scenario or a portfolio. Options considered:

- **Option A: Detect from content structure** (e.g., presence of `policies` key vs `policy_type` key) — fragile, relies on structural inference
- **Option B: `_registry_type` field in metadata.yaml** — clean, explicit, backward compatible (absent = scenario)

**Chosen: Option B** — `_registry_type` stored in `metadata.yaml` with values `"baseline"`, `"reform"`, or `"portfolio"`. This is set once when the first version is saved and checked on every `get()`. Backward compatibility: entries without `_registry_type` infer type from the latest version content (`baseline_ref` present → `"reform"`, absent → `"baseline"`).

The `_registry_type` marker is ALSO stored in each version YAML file (as part of the serialized dict) to enable standalone version file identification without requiring metadata.yaml lookup.

**Design: Reuse existing serialization from `portfolios.composition`**

`portfolio_to_dict()` and `dict_to_portfolio()` from `src/reformlab/templates/portfolios/composition.py` already handle full portfolio serialization/deserialization. The registry layer wraps these with:
1. `_registry_type` marker injection/stripping
2. Content-addressable version ID generation
3. Atomic file I/O

This avoids duplicating the complex policy parameter serialization logic (which handles CarbonTax, Subsidy, Rebate, Feebate with type-specific fields).

**Design: `RegistryEntry.entry_type` field**

The `RegistryEntry` frozen dataclass gains an `entry_type: str` field with default `"scenario"` for backward compatibility. Values: `"baseline"`, `"reform"`, `"portfolio"`. This makes type discrimination available through the standard entry API without requiring separate queries.

Note: This is a **backward-compatible addition** — the new field has a default value, so existing code constructing `RegistryEntry` won't break.

### Key Interfaces to Follow

**Existing `ScenarioRegistry` API** [Source: src/reformlab/templates/registry.py]:
```python
class ScenarioRegistry:
    def save(self, scenario, name, change_description="") -> str  # version_id
    def get(self, name, version_id=None) -> BaselineScenario | ReformScenario
    def list_scenarios(self) -> list[str]
    def list_versions(self, name) -> list[ScenarioVersion]
    def exists(self, name, version_id=None) -> bool
    def get_entry(self, name) -> RegistryEntry
    def clone(self, name, version_id=None, new_name=None) -> scenario
    def set_validated(self, name, version_id=None, *, validated=True) -> None
    def is_validated(self, name, version_id=None) -> bool
```

**Version ID generation pattern** [Source: src/reformlab/templates/registry.py:231-246]:
```python
def _generate_version_id(scenario):
    content = _scenario_to_dict_for_registry(scenario)
    yaml_str = yaml.dump(content, sort_keys=True)
    hash_bytes = hashlib.sha256(yaml_str.encode("utf-8")).hexdigest()[:12]
    return hash_bytes
```

Portfolio version ID generation MUST use the same pattern: convert to dict, `yaml.dump(content, sort_keys=True)`, SHA-256, 12-char prefix. The dict MUST include `_registry_type: "portfolio"` to ensure portfolio and scenario version IDs never collide even if content is superficially similar. The `$schema` field MUST be normalized to a stable relative path (e.g., `"portfolio.schema.json"`) before hashing — `portfolio_to_dict()` emits a machine-specific absolute path via `Path(__file__)` that would break cross-machine determinism.

**Atomic file save pattern** [Source: src/reformlab/templates/registry.py:1013-1038]:
```python
def _save_scenario_file(self, scenario, path):
    data = _scenario_to_dict_for_registry(scenario)
    fd, tmp_path = tempfile.mkstemp(suffix=".yaml", prefix=".tmp_", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
```

**Portfolio serialization** [Source: src/reformlab/templates/portfolios/composition.py:54-80]:
```python
def portfolio_to_dict(portfolio: PolicyPortfolio) -> dict[str, Any]:
    # Returns: {"$schema": ..., "name": ..., "version": ..., "description": ...,
    #           "policies": [...], "resolution_strategy": ...}
```

**Portfolio deserialization** [Source: src/reformlab/templates/portfolios/composition.py:145-255]:
```python
def dict_to_portfolio(data: dict[str, Any]) -> PolicyPortfolio:
    # Reconstructs PolicyPortfolio from dict, including per-policy type handling
```

**RegistryEntry dataclass** [Source: src/reformlab/templates/registry.py:138-145]:
```python
@dataclass(frozen=True)
class RegistryEntry:
    name: str
    created: datetime
    latest_version: str
    versions: tuple[ScenarioVersion, ...]
```

The new `entry_type` field must be added with a default to maintain backward compatibility:
```python
@dataclass(frozen=True)
class RegistryEntry:
    name: str
    created: datetime
    latest_version: str
    versions: tuple[ScenarioVersion, ...]
    entry_type: str = "scenario"  # "baseline", "reform", "portfolio"
```

### Existing Error Pattern

All registry errors use structured kwargs [Source: src/reformlab/templates/registry.py:44-74]:
```python
class RegistryError(Exception):
    def __init__(self, *, summary, reason, fix, scenario_name="", version_id=""):
```

Portfolio errors should use the same pattern. The `scenario_name` parameter is slightly misnamed for portfolios but changing it would break backward compatibility — use it as the entry name regardless of type.

### Scope Boundaries

**IN SCOPE:**
- Extend `ScenarioRegistry` to save/get/list/clone `PolicyPortfolio` objects
- Content-addressable versioning for portfolios
- Type discrimination (`entry_type` field on `RegistryEntry`, `list_portfolios()` method)
- Version history tracking (same metadata pattern)
- Integrity checking for portfolio version files
- Round-trip fidelity for all portfolio fields
- Backward compatibility with existing scenario-only registries

**OUT OF SCOPE (deferred to future stories):**
- Portfolio-aware `from_workflow_config()` factory — Story 12.5 or later
- `WorkflowConfig` integration with portfolio references — Story 12.5 or later
- Multi-portfolio comparison — Story 12.5
- Portfolio migration (version upgrades) — future story
- Portfolio-specific `get_baseline()` / `list_reforms()` (portfolios don't have baseline_ref) — N/A

### Project Structure Notes

**Modified files:**
```
src/reformlab/templates/registry.py           ← Main changes: save/get/list/clone portfolio support
```

**New files:**
```
tests/templates/test_registry_portfolios.py   ← All portfolio registry tests
```

**Files NOT to modify:**
```
src/reformlab/templates/portfolios/portfolio.py     ← No changes needed
src/reformlab/templates/portfolios/composition.py   ← No changes needed (reuse existing serialization)
src/reformlab/templates/portfolios/__init__.py       ← No changes needed
src/reformlab/templates/__init__.py                  ← No new exports needed (RegistryEntry already exported)
src/reformlab/orchestrator/                          ← No changes (Story 12.3 already done)
```

### Code Conventions to Follow

- `from __future__ import annotations` at top of every file
- `if TYPE_CHECKING:` guards for type-only imports
- Frozen dataclasses for all domain types; mutate via `dataclasses.replace()`
- Structured error messages with `summary`, `reason`, `fix` kwargs
- `logging.getLogger(__name__)` for logger
- Section separators `# ====...====` for major sections in longer modules
- All domain types are frozen — `RegistryEntry` uses `@dataclass(frozen=True)`
- `yaml.safe_dump` for file output, `yaml.safe_load` for file input
- Deterministic serialization: `sort_keys=True` for version ID generation, `sort_keys=False` for file storage

### Test Patterns to Follow

**From existing registry tests** [Source: tests/templates/test_registry.py]:
- Use `tmp_path` for temporary registry directory
- Create registry with `ScenarioRegistry(tmp_path)` then `registry.initialize()`
- Build test scenarios inline using `BaselineScenario(...)` or `ReformScenario(...)`
- Assert round-trip equality with `==` on frozen dataclasses
- Test error cases with `pytest.raises(ErrorClass)` and check structured error fields

For portfolio tests, build portfolios inline using `PolicyPortfolio(name=..., policies=(...))` with `PolicyConfig` wrapping `CarbonTaxParameters`, `SubsidyParameters`, etc.

### Performance Considerations

Portfolio serialization/deserialization is slightly more complex than scenarios (nested policies), but registry operations are inherently I/O-bound and typically handle single entries. No optimization needed.

### References

- [Source: docs/epics.md#BKL-1204] — Story acceptance criteria
- [Source: docs/prd.md#FR43] — "Analyst can compose multiple individual policy templates into a named policy portfolio"
- [Source: src/reformlab/templates/registry.py] — Existing ScenarioRegistry implementation (1223 lines)
- [Source: src/reformlab/templates/registry.py:128-145] — `ScenarioVersion` and `RegistryEntry` dataclasses
- [Source: src/reformlab/templates/registry.py:231-246] — `_generate_version_id()` pattern
- [Source: src/reformlab/templates/registry.py:290-396] — `save()` method with idempotent save logic
- [Source: src/reformlab/templates/registry.py:398-465] — `get()` method with version resolution
- [Source: src/reformlab/templates/registry.py:467-481] — `list_scenarios()` method
- [Source: src/reformlab/templates/registry.py:574-608] — `clone()` method
- [Source: src/reformlab/templates/registry.py:1013-1038] — Atomic file save pattern
- [Source: src/reformlab/templates/registry.py:1040-1045] — `_load_scenario_file()` pattern
- [Source: src/reformlab/templates/registry.py:1069-1222] — `_dict_to_scenario()` and `_dict_to_policy()` deserialization
- [Source: src/reformlab/templates/portfolios/composition.py:54-80] — `portfolio_to_dict()` serialization
- [Source: src/reformlab/templates/portfolios/composition.py:145-255] — `dict_to_portfolio()` deserialization
- [Source: src/reformlab/templates/portfolios/composition.py:760-771] — `dump_portfolio()` YAML output
- [Source: src/reformlab/templates/portfolios/portfolio.py] — `PolicyPortfolio` and `PolicyConfig` frozen dataclasses
- [Source: src/reformlab/templates/portfolios/exceptions.py] — `PortfolioError` hierarchy
- [Source: docs/project-context.md#Architecture] — Adapter isolation, frozen dataclasses, deterministic serialization
- [Source: docs/project-context.md#Testing] — Mirror source structure, class-based grouping, direct assertions

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

### Completion Notes List

### Change Log

### File List


]]></file>
<file id="8233c651" path="_bmad-output/implementation-artifacts/12-5-implement-multi-portfolio-comparison-and-notebook-demo.md" label="STORY FILE"><![CDATA[


# Story 12.5: Implement Multi-Portfolio Comparison and Notebook Demo

Status: ready-for-dev
Dependencies: Story 12.1 (PolicyPortfolio model), Story 12.2 (conflict detection), Story 12.3 (orchestrator portfolio execution), Story 12.4 (registry portfolio versioning)

## Story

As a **policy analyst**,
I want to compare results across multiple policy portfolios side-by-side, with aggregate cross-comparison metrics and a pedagogical notebook demo,
so that I can determine which portfolio best achieves my policy objectives (e.g., maximizes welfare, minimizes fiscal cost) and share these analyses with colleagues.

## Acceptance Criteria

### AC1: Multi-portfolio side-by-side comparison
Given 3 completed portfolio runs (each against the same baseline population), when comparison is invoked per indicator type (distributional, fiscal, welfare), then a side-by-side `ComparisonResult` table shows all indicator metrics per portfolio. Each comparison table uses portfolio labels as column names.

### AC2: Cross-comparison aggregate metrics
Given multi-portfolio comparison results, when cross-comparison metrics are computed, then aggregate metrics are available per portfolio: (a) total fiscal revenue, (b) total fiscal cost, (c) fiscal balance, (d) mean net welfare change (if welfare indicators are included). Each metric ranks portfolios from best to worst, answering questions like "which portfolio maximizes welfare?" and "which has lowest fiscal cost?".

### AC3: Backward compatibility with pairwise comparison API
Given the Phase 1 `compare_scenarios()` API, when used with 2 portfolio `ScenarioInput` objects, then it works identically to pre-portfolio behavior. The `compare_portfolios()` convenience function transparently delegates to `compare_scenarios()` for each indicator type and adds cross-comparison metrics on top.

### AC4: Notebook demo runs in CI
Given the notebook demo, when run in CI, then it demonstrates: (a) creating 3 distinct portfolios, (b) executing each against the same baseline population, (c) computing distributional and fiscal comparison tables, (d) computing cross-comparison metrics, (e) visualizing portfolio differences with charts. The notebook completes without errors.

### AC5: Input validation and error handling
Given fewer than 2 portfolios, when `compare_portfolios()` is called, then a `ValueError` is raised with a clear message. Given portfolio inputs with non-unique labels, when called, then a `ValueError` is raised. Given an empty portfolio panel (no rows), when indicators are computed, then warnings are collected (not exceptions) and the comparison proceeds with available data.

### AC6: Export support
Given a `PortfolioComparisonResult`, when exported, then each per-indicator-type comparison table can be exported to CSV/Parquet independently via the existing `ComparisonResult.export_csv()` / `export_parquet()` methods. The cross-comparison metrics are available as a dict for programmatic access.

## Tasks / Subtasks

### Task 1: Define portfolio comparison types (AC: 1, 2, 5, 6)

- [ ] 1.1 Create `src/reformlab/indicators/portfolio_comparison.py` with module docstring referencing Story 12.5 and FR45
- [ ] 1.2 Define `PortfolioComparisonInput` frozen dataclass: `label: str`, `panel: PanelOutput`. Validate label is non-empty in `__post_init__`. This takes `PanelOutput` (not `SimulationResult`) to match existing indicator function signatures and enable composition
- [ ] 1.3 Define `PortfolioComparisonConfig` frozen dataclass with fields: `baseline_label: str | None = None` (defaults to first portfolio), `indicator_types: tuple[str, ...] = ("distributional", "fiscal")` (which indicator types to compute), `include_welfare: bool = False` (welfare requires baseline vs reform so opt-in), `include_deltas: bool = True`, `include_pct_deltas: bool = True`, `distributional_kwargs: dict[str, Any] = field(default_factory=dict)` (passed to `compute_distributional_indicators`), `fiscal_kwargs: dict[str, Any] = field(default_factory=dict)` (passed to `compute_fiscal_indicators`), `welfare_kwargs: dict[str, Any] = field(default_factory=dict)` (passed to `compute_welfare_indicators`)
- [ ] 1.4 Define `CrossComparisonMetric` frozen dataclass: `criterion: str` (e.g., `"max_mean_welfare_net_change"`, `"min_fiscal_cost"`), `best_portfolio: str` (label of the portfolio ranked first), `value: float` (metric value for the best portfolio), `all_values: dict[str, float]` (metric value per portfolio label, ordered by ranking)
- [ ] 1.5 Define `PortfolioComparisonResult` frozen dataclass: `comparisons: dict[str, ComparisonResult]` (keyed by indicator type string, e.g., `{"distributional": ..., "fiscal": ...}`), `cross_metrics: tuple[CrossComparisonMetric, ...]` (aggregate metrics across portfolios), `portfolio_labels: tuple[str, ...]` (ordered labels), `metadata: dict[str, Any]`, `warnings: list[str]`

### Task 2: Implement `compare_portfolios()` function (AC: 1, 3, 5)

- [ ] 2.1 Implement input validation: minimum 2 portfolios, unique labels, non-empty labels, labels don't conflict with reserved column names (same checks as `compare_scenarios()`)
- [ ] 2.2 For each indicator type in `config.indicator_types`, compute indicators for each portfolio by calling the appropriate indicator function (`compute_distributional_indicators`, `compute_fiscal_indicators`) with the portfolio's `PanelOutput`. Collect per-portfolio `IndicatorResult` objects
- [ ] 2.3 For welfare indicators (when `config.include_welfare is True`): use the baseline portfolio's panel as the baseline panel, compute welfare indicators for each non-baseline portfolio via `compute_welfare_indicators(baseline_panel, reform_panel, **config.welfare_kwargs)`. Collect per-portfolio `IndicatorResult` objects. Skip the baseline portfolio itself (welfare is baseline vs reform, so baseline vs baseline is meaningless)
- [ ] 2.4 For each indicator type, wrap per-portfolio `IndicatorResult` objects as `ScenarioInput(label=portfolio_label, indicators=indicator_result)` and call `compare_scenarios(scenarios, config=ComparisonConfig(baseline_label=config.baseline_label, include_deltas=config.include_deltas, include_pct_deltas=config.include_pct_deltas))`. Store resulting `ComparisonResult` keyed by indicator type string
- [ ] 2.5 Call `_compute_cross_comparison_metrics()` (Task 3) with the per-portfolio indicator results to produce `CrossComparisonMetric` tuples
- [ ] 2.6 Build metadata dict: `{"portfolio_labels": labels, "baseline_label": resolved_baseline, "indicator_types": list(config.indicator_types), "include_welfare": config.include_welfare, "config": ...}`
- [ ] 2.7 Collect all warnings from each `ComparisonResult` into a unified warnings list, prefixed with indicator type (e.g., `"[distributional] Non-overlapping keys..."`)
- [ ] 2.8 Return `PortfolioComparisonResult` with all collected results

### Task 3: Implement cross-comparison metrics computation (AC: 2)

- [ ] 3.1 Create `_compute_cross_comparison_metrics()` internal function accepting: `fiscal_indicators: dict[str, IndicatorResult] | None` (keyed by portfolio label), `welfare_indicators: dict[str, IndicatorResult] | None` (keyed by portfolio label), `portfolio_labels: list[str]`
- [ ] 3.2 For fiscal metrics: extract per-portfolio aggregate values from `IndicatorResult.indicators` list. For each portfolio, compute: `total_revenue` (sum of `FiscalIndicators.revenue` across years), `total_cost` (sum of `FiscalIndicators.cost` across years), `fiscal_balance` (sum of `FiscalIndicators.balance` across years). Create `CrossComparisonMetric` for each: `"max_fiscal_revenue"` (highest revenue first), `"min_fiscal_cost"` (lowest cost first), `"max_fiscal_balance"` (highest balance first)
- [ ] 3.3 For welfare metrics: extract per-portfolio aggregate values from `IndicatorResult.indicators` list. For each portfolio, compute: `mean_net_change` (mean of `WelfareIndicators.net_change` across all groups and years), `total_winners` (sum of `WelfareIndicators.winner_count` across groups), `total_losers` (sum of `WelfareIndicators.loser_count` across groups). Create `CrossComparisonMetric` for each: `"max_mean_welfare_net_change"` (highest net change first), `"max_total_winners"` (most winners first), `"min_total_losers"` (fewest losers first)
- [ ] 3.4 Sort each metric's `all_values` dict by ranking order (best first). For "max_*" criteria, sort descending; for "min_*" criteria, sort ascending
- [ ] 3.5 Return tuple of all `CrossComparisonMetric` objects. If fiscal_indicators is None, skip fiscal metrics. If welfare_indicators is None, skip welfare metrics. If both are None, return empty tuple

### Task 4: Update module exports (AC: all)

- [ ] 4.1 Add imports and exports to `src/reformlab/indicators/__init__.py`: `PortfolioComparisonInput`, `PortfolioComparisonConfig`, `PortfolioComparisonResult`, `CrossComparisonMetric`, `compare_portfolios`
- [ ] 4.2 Update module docstring in `__init__.py` to mention portfolio comparison (add `Story 12.5` reference)

### Task 5: Build notebook demo (AC: 4)

- [ ] 5.1 Create `notebooks/demo/epic12_portfolio_comparison.ipynb` following the pattern of `notebooks/advanced.ipynb`
- [ ] 5.2 **Section 0 — Introduction** (markdown): Explain what portfolio comparison is, prerequisites (quickstart + advanced notebooks), and what the reader will learn
- [ ] 5.3 **Section 1 — Imports and Setup** (code): Import ReformLab API, portfolio types, indicator comparison types, visualization utilities. Resolve population path relative to notebook location. Load the demo population CSV
- [ ] 5.4 **Section 2 — Create Three Portfolios** (code + markdown per portfolio):
  - Portfolio A: "Carbon Tax Only" — single carbon tax at €50/tCO2 (2-policy portfolio: carbon tax + minimal subsidy)
  - Portfolio B: "Carbon Tax + Subsidy" — carbon tax at €50/tCO2 + vehicle subsidy at €5000
  - Portfolio C: "Green Transition" — carbon tax at €80/tCO2 + vehicle subsidy at €7000 + feebate
  - Use `PolicyConfig`, `PolicyPortfolio` from `reformlab.templates.portfolios`
  - Show `portfolio.list_policies()` for each
- [ ] 5.5 **Section 3 — Execute All Three Portfolios** (code): For each portfolio, create a `PortfolioComputationStep`, configure `RunConfig` with `ScenarioConfig`, and call `run_scenario()`. Use the same population, seed, and year range (2025-2034) for fair comparison. Store results as dict `{label: SimulationResult}`
- [ ] 5.6 **Section 4 — Distributional Comparison** (code + markdown): Extract `panel_output` from each result. Create `PortfolioComparisonInput` objects. Call `compare_portfolios()` with distributional indicators. Display the comparison table with `show()`. Create a grouped bar chart showing mean carbon tax burden by decile per portfolio
- [ ] 5.7 **Section 5 — Fiscal Comparison** (code + markdown): Call `compare_portfolios()` with fiscal indicators. Display revenue/cost comparison table. Create a line chart showing fiscal balance over time per portfolio
- [ ] 5.8 **Section 6 — Cross-Comparison Metrics** (code + markdown): Display the `cross_metrics` from the comparison result. Show which portfolio has highest revenue, lowest cost, best fiscal balance. Format as a summary table
- [ ] 5.9 **Section 7 — Using the Phase 1 API Directly** (code + markdown): Demonstrate that `compare_scenarios()` works with portfolio results (backward compatibility). Show it's the same as the per-indicator-type result from `compare_portfolios()`. One-liner comparison
- [ ] 5.10 **Section 8 — Export Results** (code + markdown): Export comparison tables to Parquet. Export panel outputs. Verify round-trip
- [ ] 5.11 **Section 9 — Next Steps** (markdown): Summary of what was learned, link to EPIC-13 (custom templates in portfolios) and future GUI

### Task 6: Write tests in `tests/indicators/test_portfolio_comparison.py` (AC: all)

- [ ] 6.1 Create test file with module docstring referencing Story 12.5
- [ ] 6.2 Add fixtures in `tests/indicators/conftest.py`: `portfolio_panels` fixture returning 3 `PanelOutput` objects with different numeric values (simulating different portfolio outcomes). Use inline PyArrow table construction. Each panel: 30 households × 3 years (2025-2027), with columns `household_id`, `year`, `income`, `carbon_tax`, `subsidy_amount`. Portfolio A: carbon_tax=500 per household. Portfolio B: carbon_tax=500, subsidy_amount=200. Portfolio C: carbon_tax=800, subsidy_amount=300
- [ ] 6.3 **TestComparePortfoliosBasic** (AC1): Compare 3 portfolios with distributional indicators. Assert `comparisons` dict has `"distributional"` key. Assert comparison table has columns for each portfolio label. Assert table has rows (non-empty)
- [ ] 6.4 **TestComparePortfoliosFiscal** (AC1): Compare 3 portfolios with fiscal indicators (config with `fiscal_kwargs=FiscalConfig(revenue_fields=["carbon_tax"], cost_fields=["subsidy_amount"])`). Assert `comparisons` dict has `"fiscal"` key. Assert comparison table has expected columns
- [ ] 6.5 **TestComparePortfoliosWelfare** (AC1, AC2): Compare 3 portfolios with `include_welfare=True`. Assert `comparisons` dict has `"welfare"` key. Assert welfare comparison uses baseline panel vs each reform panel. Assert baseline label is not in welfare comparison (baseline vs itself is skipped)
- [ ] 6.6 **TestCrossComparisonMetrics** (AC2): Compare 3 portfolios with fiscal indicators. Assert `cross_metrics` tuple is non-empty. Assert metrics include `"max_fiscal_revenue"`, `"min_fiscal_cost"`, `"max_fiscal_balance"`. Assert each metric has `best_portfolio`, `value`, `all_values` with 3 entries. Assert `all_values` is sorted by ranking (best first)
- [ ] 6.7 **TestCrossComparisonMetricsWelfare** (AC2): Compare with welfare. Assert metrics include `"max_mean_welfare_net_change"`, `"max_total_winners"`, `"min_total_losers"`
- [ ] 6.8 **TestBackwardCompatibility** (AC3): Use `compare_scenarios()` directly with 2 portfolio `ScenarioInput` objects. Assert it produces valid `ComparisonResult`. Compare with `compare_portfolios()` result for same 2 portfolios — per-indicator comparison table should be equivalent
- [ ] 6.9 **TestComparePortfoliosValidation** (AC5): Test fewer than 2 portfolios raises `ValueError`. Test duplicate labels raises `ValueError`. Test empty labels raises `ValueError`. Test labels conflicting with reserved names raises `ValueError`
- [ ] 6.10 **TestComparePortfoliosExport** (AC6): Compare portfolios, export each comparison to CSV and Parquet via `ComparisonResult.export_csv()` / `export_parquet()`. Verify round-trip (read back and compare table shapes). Use `tmp_path` fixture
- [ ] 6.11 **TestComparePortfoliosMetadata** (AC1): Assert `metadata` dict contains `portfolio_labels`, `baseline_label`, `indicator_types`. Assert `warnings` is a list
- [ ] 6.12 **TestComparePortfoliosConfig** (AC1): Test custom config: `baseline_label` set to non-first portfolio. Test `include_deltas=False` produces no delta columns. Test `indicator_types=("fiscal",)` produces only fiscal comparison

### Task 7: Run quality checks (AC: all)

- [ ] 7.1 Run `uv run pytest tests/indicators/test_portfolio_comparison.py -v` — all tests pass
- [ ] 7.2 Run `uv run pytest tests/indicators/ -v` — all indicator tests pass (no regressions)
- [ ] 7.3 Run `uv run ruff check src/reformlab/indicators/portfolio_comparison.py tests/indicators/test_portfolio_comparison.py`
- [ ] 7.4 Run `uv run mypy src/reformlab/indicators/portfolio_comparison.py` — passes strict mode
- [ ] 7.5 Run full test suite: `uv run pytest tests/ -v`

## Dev Notes

### Architecture Decisions

**Design: `compare_portfolios()` as a convenience wrapper over `compare_scenarios()`**

The existing `compare_scenarios()` already supports N-way comparison (2+ `ScenarioInput` objects) with delta computation against a baseline. It handles join key alignment, null handling, and schema detection for all indicator types (decile, region, fiscal).

`compare_portfolios()` does NOT reimplement comparison logic. It:
1. Computes indicators for each portfolio (calling existing `compute_*_indicators()` functions)
2. Wraps each portfolio's `IndicatorResult` as a `ScenarioInput` with the portfolio label
3. Calls `compare_scenarios()` for each indicator type
4. Adds cross-comparison aggregate metrics on top

This approach:
- Avoids duplicating the comparison engine
- Ensures backward compatibility (AC3)
- Keeps the API surface small
- Leverages battle-tested N-way comparison logic from Story 4.5

**Design: `PanelOutput` as input, not `SimulationResult`**

`compare_portfolios()` accepts `PortfolioComparisonInput(label, panel)` where `panel` is `PanelOutput`, not `SimulationResult`. This matches existing indicator function signatures (`compute_distributional_indicators(panel)`, `compute_fiscal_indicators(panel)`, etc.) and enables composition — panels can come from `SimulationResult.panel_output`, from disk (Parquet files), or from manual construction.

Users extract panels from simulation results: `PortfolioComparisonInput(label="Green2030", panel=result.panel_output)`.

**Design: Cross-comparison metrics as post-hoc aggregation**

Cross-comparison metrics (`CrossComparisonMetric`) are computed from the per-portfolio `IndicatorResult` objects, not from the `ComparisonResult` tables. This is because:
- `ComparisonResult` tables are in long-form (one row per metric per group per year)
- Aggregate metrics need to sum/average across groups and years
- Working with the structured `IndicatorResult.indicators` list (typed dataclass instances) is more reliable than parsing table rows

Metrics are intentionally simple: sums and means across indicator instances. No complex aggregation formulas. The cross-comparison answers: "which portfolio scores best on this simple aggregate?"

**Design: Welfare indicators are opt-in**

`PortfolioComparisonConfig.include_welfare` defaults to `False` because welfare indicators require a baseline panel vs. each reform panel (two-panel computation). The baseline is the portfolio labeled `baseline_label`. If the user enables welfare but all portfolios are different reforms (no "baseline"), the function raises a clear error.

When welfare is enabled, the baseline portfolio is excluded from welfare comparison (comparing baseline vs. itself is meaningless), so the welfare `ComparisonResult` has N-1 scenario columns.

### Key Interfaces to Follow

**Existing `compare_scenarios()` API** [Source: src/reformlab/indicators/comparison.py:406-557]:
```python
def compare_scenarios(
    scenarios: list[ScenarioInput],
    config: ComparisonConfig | None = None,
) -> ComparisonResult:
```
- Already handles 2+ scenarios
- Validates: min 2, unique labels, compatible schemas, reserved names
- Produces delta and pct_delta columns vs baseline
- Returns `ComparisonResult` with table, metadata, warnings

**Indicator computation functions** [Source: src/reformlab/indicators/]:
```python
# Distributional
compute_distributional_indicators(panel: PanelOutput, config=None) -> IndicatorResult

# Fiscal
compute_fiscal_indicators(panel: PanelOutput, config=None) -> IndicatorResult

# Welfare (requires baseline + reform panels)
compute_welfare_indicators(baseline: PanelOutput, reform: PanelOutput, config=None) -> IndicatorResult
```

**Indicator result types** [Source: src/reformlab/indicators/types.py]:
```python
@dataclass
class IndicatorResult:
    indicators: Sequence[DecileIndicators | RegionIndicators | WelfareIndicators | FiscalIndicators]
    metadata: dict[str, Any]
    warnings: list[str]

@dataclass
class FiscalIndicators:
    field_name: str
    year: int | None
    revenue: float
    cost: float
    balance: float
    cumulative_revenue: float | None
    cumulative_cost: float | None
    cumulative_balance: float | None

@dataclass
class WelfareIndicators:
    field_name: str
    group_type: str
    group_value: int | str
    year: int | None
    winner_count: int
    loser_count: int
    neutral_count: int
    mean_gain: float
    mean_loss: float
    median_change: float
    total_gain: float
    total_loss: float
    net_change: float
```

**Portfolio types** [Source: src/reformlab/templates/portfolios/portfolio.py]:
```python
@dataclass(frozen=True)
class PolicyConfig:
    policy_type: PolicyType
    policy: PolicyParameters
    name: str = ""

@dataclass(frozen=True)
class PolicyPortfolio:
    name: str
    policies: tuple[PolicyConfig, ...]
    version: str = "1.0"
    description: str = ""
    resolution_strategy: str = "error"
```

**PortfolioComputationStep** [Source: src/reformlab/orchestrator/portfolio_step.py]:
```python
class PortfolioComputationStep:
    def __init__(self, adapter, population, portfolio, *, name="portfolio_computation"): ...
    def execute(self, year: int, state: YearState) -> YearState: ...
```

**ScenarioInput and ComparisonConfig** [Source: src/reformlab/indicators/comparison.py:33-64]:
```python
@dataclass
class ScenarioInput:
    label: str
    indicators: IndicatorResult

@dataclass
class ComparisonConfig:
    baseline_label: str | None = None
    include_deltas: bool = True
    include_pct_deltas: bool = True
```

**Notebook execution in CI** [Source: notebooks/advanced.ipynb pattern]:
- Notebooks resolve paths via `_NB_DIR = Path(__file__).parent if "__file__" in dir() else Path(".")`
- Use `create_quickstart_adapter()` for demo execution (no real OpenFisca required)
- Population path: `_NB_DIR / "../data/populations/demo-quickstart-100.csv"`
- All notebooks use `seed=42` for determinism

**Public API run functions** [Source: src/reformlab/interfaces/api.py]:
```python
def run_scenario(
    config: RunConfig | ScenarioConfig | Path | dict[str, Any],
    adapter: ComputationAdapter | None = None,
    *,
    steps: tuple[PipelineStep, ...] | None = None,
    initial_state: dict[str, Any] | None = None,
    skip_memory_check: bool = False,
) -> SimulationResult
```

### Notebook Demo Patterns

**From `notebooks/advanced.ipynb` (47 cells):**

1. Imports resolve paths relative to notebook location
2. Uses `create_quickstart_adapter()` with explicit `carbon_tax_rate` and `year`
3. The demo adapter applies a fixed formula — doesn't read per-year rate_schedule
4. Comparison uses `compare_scenarios()` with `ScenarioInput` wrappers
5. Visualization uses `create_figure()` from `reformlab.visualization` + matplotlib
6. Each section starts with markdown explaining the concept, followed by code
7. Verification cells use `print("✓ ...")` pattern

**Important demo adapter limitation:** The `create_quickstart_adapter()` applies a generic carbon tax formula. When running portfolios with different policy types (subsidy, feebate), the adapter still computes the same `carbon_tax` column. For the demo, this means:
- All portfolio runs produce the same column structure
- The "difference" between portfolios comes from using different `carbon_tax_rate` values when creating adapters
- The demo should use **different adapters per portfolio** with different rates to simulate different outcomes

**Alternative approach for notebook:** Create separate adapters with different `carbon_tax_rate` values (e.g., 44.0, 50.0, 80.0) to simulate the effect of different policy portfolios. Then compare using `compare_portfolios()`. This is honest about the demo adapter limitation while still demonstrating the comparison API.

### Existing Error Pattern

Indicator module errors use `ValueError` (not custom exceptions) [Source: src/reformlab/indicators/comparison.py:433-490]:
```python
raise ValueError(f"Comparison requires at least 2 scenarios, got {len(scenarios)}. ...")
raise ValueError(f"Duplicate scenario labels detected: {duplicate_labels}. ...")
```

Follow the same pattern for `compare_portfolios()` — use `ValueError` for input validation, consistent with `compare_scenarios()`.

### Scope Boundaries

**IN SCOPE:**
- `compare_portfolios()` convenience function
- `PortfolioComparisonInput`, `PortfolioComparisonConfig`, `PortfolioComparisonResult`, `CrossComparisonMetric` types
- Cross-comparison aggregate metrics (fiscal: revenue/cost/balance, welfare: net_change/winners/losers)
- Notebook demo with 3 portfolios
- Tests for all new functionality

**OUT OF SCOPE (deferred to future stories):**
- GUI portfolio comparison dashboard — EPIC-17
- Geographic indicator comparison in portfolios — can be added later (the function supports `indicator_types` extension)
- Custom formula indicators in cross-comparison — EPIC-4.6 already exists, can be composed manually
- Portfolio-specific indicator types (e.g., "portfolio diversity score") — not in FR45
- Automated portfolio optimization ("find the best portfolio parameters") — not in scope

### Project Structure Notes

**New files:**
```
src/reformlab/indicators/portfolio_comparison.py   ← Main implementation
tests/indicators/test_portfolio_comparison.py      ← All tests
notebooks/demo/epic12_portfolio_comparison.ipynb    ← Notebook demo
```

**Modified files:**
```
src/reformlab/indicators/__init__.py               ← Add exports
tests/indicators/conftest.py                       ← Add portfolio panel fixtures
```

**Files NOT to modify:**
```
src/reformlab/indicators/comparison.py              ← No changes (reuse as-is)
src/reformlab/indicators/distributional.py          ← No changes
src/reformlab/indicators/fiscal.py                  ← No changes
src/reformlab/indicators/welfare.py                 ← No changes
src/reformlab/templates/portfolios/                 ← No changes
src/reformlab/orchestrator/portfolio_step.py        ← No changes
src/reformlab/interfaces/api.py                     ← No changes
```

### Code Conventions to Follow

- `from __future__ import annotations` at top of every file
- `if TYPE_CHECKING:` guards for type-only imports
- Frozen dataclasses for all new types (`PortfolioComparisonInput`, etc.) with `@dataclass(frozen=True)`
- `field(default_factory=dict)` for mutable default arguments
- `ValueError` for input validation (matching `compare_scenarios()` pattern)
- `logging.getLogger(__name__)` for logger
- Section separators `# ====...====` for major sections
- Module-level docstring referencing Story 12.5 and FR45
- `tuple[...]` for immutable sequences in return types
- `dict[str, Any]` for metadata bags

### Test Patterns to Follow

**From existing indicator tests** [Source: tests/indicators/]:
- Build PyArrow tables inline with `pa.table({...})`
- Use `PanelOutput(table=table, metadata={...})` directly
- Assert with plain `assert` — no custom helpers
- Test error cases with `pytest.raises(ValueError, match=...)`
- Class-based test grouping: `TestComparePortfoliosBasic`, `TestCrossComparisonMetrics`, etc.
- Use `tmp_path` for file export tests

**From comparison test patterns** [Source: tests/indicators/test_comparison.py]:
- Create indicators first, wrap as `ScenarioInput`, then compare
- Check `result.table.column_names` for expected columns
- Check `result.metadata` dict for expected keys
- Verify warnings list for edge cases

### Performance Considerations

Portfolio comparison is O(N × I) where N = number of portfolios and I = number of indicator types. For the expected use case (3-5 portfolios, 2-3 indicator types), this is negligible. Each `compare_scenarios()` call processes the already-computed indicator tables, which are small (deciles × years × metrics ≈ hundreds of rows).

Cross-comparison metrics iterate over indicator instances (O(N × G × Y) where G = groups, Y = years). For typical scenarios (10 deciles, 10 years, 5 portfolios) this is ~500 iterations — negligible.

### References

- [Source: docs/epics.md#BKL-1205] — Story acceptance criteria
- [Source: docs/prd.md#FR45] — "Analyst can compare results across different policy portfolios side-by-side"
- [Source: src/reformlab/indicators/comparison.py] — Existing comparison module (557 lines)
- [Source: src/reformlab/indicators/comparison.py:406-557] — `compare_scenarios()` function
- [Source: src/reformlab/indicators/comparison.py:33-64] — `ScenarioInput`, `ComparisonConfig` types
- [Source: src/reformlab/indicators/comparison.py:67-120] — `ComparisonResult` with export methods
- [Source: src/reformlab/indicators/types.py] — `IndicatorResult`, `FiscalIndicators`, `WelfareIndicators`, `DecileIndicators`
- [Source: src/reformlab/indicators/__init__.py] — Current module exports
- [Source: src/reformlab/indicators/distributional.py] — `compute_distributional_indicators()`
- [Source: src/reformlab/indicators/fiscal.py] — `compute_fiscal_indicators()`
- [Source: src/reformlab/indicators/welfare.py] — `compute_welfare_indicators()`
- [Source: src/reformlab/orchestrator/portfolio_step.py] — `PortfolioComputationStep` (Story 12.3)
- [Source: src/reformlab/templates/portfolios/portfolio.py] — `PolicyPortfolio`, `PolicyConfig`
- [Source: src/reformlab/interfaces/api.py:97-206] — `SimulationResult` with `.indicators()` method
- [Source: src/reformlab/interfaces/api.py:299-] — `SimulationResult.plot_yearly()`, `plot_comparison()`
- [Source: notebooks/advanced.ipynb] — Advanced notebook patterns (47 cells, sections 1-6)
- [Source: tests/indicators/conftest.py] — Existing indicator test fixtures (panel construction patterns)
- [Source: docs/project-context.md#Architecture] — Frozen dataclasses, PyArrow-first, deterministic execution
- [Source: docs/project-context.md#Testing] — Mirror source structure, class-based grouping, direct assertions

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

### Completion Notes List

### Change Log

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
<var name="story_file" file_id="8233c651">embedded in prompt, file id: 8233c651</var>
<var name="story_id">12.5</var>
<var name="story_key">12-5-implement-multi-portfolio-comparison-and-notebook-demo</var>
<var name="story_num">5</var>
<var name="story_title">implement-multi-portfolio-comparison-and-notebook-demo</var>
<var name="template">embedded context</var>
<var name="timestamp">20260306_144459</var>
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

    <action>Assign numbers to each issue for selection</action>

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

    <action>Use the output template as a FORMAT GUIDE, replacing all {{placeholders}} with your actual analysis results from steps 1-4</action>
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