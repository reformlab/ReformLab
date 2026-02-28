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
