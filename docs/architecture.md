# Architecture — ReformLab

**Generated:** 2026-02-25
**Source:** `_bmad-output/planning-artifacts/architecture.md`
**Status:** Pre-implementation (architecture design complete)

## Strategic Direction

ReformLab does **not** build a replacement tax-benefit microsimulation core. OpenFisca is the policy-calculation foundation, accessed through a clean adapter interface. This project builds differentiated layers above it: data preparation, environmental policy orchestration, multi-year projection with vintage tracking, indicators, governance, and user interfaces.

**The dynamic orchestrator is the core product** — not a computation engine.

## Active Scope

- Data ingestion and harmonization (OpenFisca outputs, synthetic population inputs, environmental datasets)
- Scenario/template layer for environmental policies (carbon tax, subsidies, rebates, feebates)
- Step-pluggable dynamic orchestrator for multi-year execution (10+ years) with vintage/cohort tracking
- Indicator layer (distributional, welfare, fiscal, custom metrics)
- Run governance (manifests, assumption logs, lineage)
- No-code analyst GUI for scenario setup, execution, and comparison

## Out Of Scope (MVP)

- Reimplementing OpenFisca internals
- Custom formula compiler or policy engine
- Endogenous market-clearing/equilibrium simulation
- Physical system loop simulation (climate/energy stock-flow engines)

## Layered Architecture

```
┌─────────────────────────────────────────────────┐
│  Interfaces (Python API, Notebooks, No-Code GUI)│
├─────────────────────────────────────────────────┤
│  Indicator Engine (distributional/welfare/fiscal)│
├─────────────────────────────────────────────────┤
│  Governance (manifests, assumptions, lineage)    │
├─────────────────────────────────────────────────┤
│  Dynamic Orchestrator (year loop + step pipeline)│
│  ├── Vintage Transitions                         │
│  ├── State Carry-Forward                         │
│  └── [Phase 2: Behavioral Response Steps]        │
├─────────────────────────────────────────────────┤
│  Scenario Template Layer (environmental policies)│
├─────────────────────────────────────────────────┤
│  Data Layer (ingestion, open data, synthetic pop)│
├─────────────────────────────────────────────────┤
│  Computation Adapter Interface                   │
│  └── OpenFiscaAdapter (primary implementation)   │
└─────────────────────────────────────────────────┘
```

## Computation Adapter Pattern

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

## Step-Pluggable Dynamic Orchestrator

The orchestrator runs a yearly loop (t to t+n) where each year executes a pipeline of pluggable steps:

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

## Subsystems

| Subsystem | Directory | Responsibility |
|-----------|-----------|---------------|
| Computation | `computation/` | Adapter interface + OpenFiscaAdapter. CSV/Parquet ingestion, version-pinned contracts |
| Data | `data/` | Open data ingestion, synthetic population generation, data transformation pipelines |
| Templates | `templates/` | Environmental policy templates and scenario registry with versioned definitions |
| Orchestrator | `orchestrator/` | Dynamic yearly loop with step-pluggable pipeline. Deterministic sequencing, seed control |
| Vintage | `vintage/` | Cohort/vintage state management. Tracks asset classes through time |
| Indicators | `indicators/` | Distributional, welfare, fiscal, and custom indicator computation |
| Governance | `governance/` | Run manifests, assumption logs, lineage, output hashes |
| Interfaces | `interfaces/` | Python API, notebook workflows, early no-code GUI |

## Technical Constraints

- Python 3.13+
- OpenFisca as the core rules engine dependency
- CSV/Parquet as interoperability contracts
- Fully offline operation in user environment
- Single-machine target (16GB laptop) for MVP

## Data Contracts

- **Input:** OpenFisca outputs (CSV/Parquet), synthetic populations, environmental datasets (emission factors, energy consumption)
- **Output:** Yearly panel datasets, scenario comparison tables, indicator exports
- **Contract failures** are explicit, field-level, and blocking
- Adapter interface defines the computation contract boundary

## Dynamic Execution Semantics

- Baseline and reform scenarios run over 10+ years
- Each year is explicit (t, t+1, ..., t+n), with deterministic carry-forward rules
- Vintage states are updated through registered transition step functions
- Randomness is seed-controlled and logged in manifests
- Orchestrator step pipeline is the extension point for Phase 2+ capabilities

## Reproducibility and Governance

- Every run records: OpenFisca version, adapter version, scenario version, data hashes, seeds, assumptions, step pipeline configuration
- Cross-machine reproducibility uses documented tolerances where floating point differs
- Lineage links yearly sub-runs to parent scenario runs
- Manifests are JSON, machine-readable, Git-diffable

## Starter and Tooling Decisions

- Scientific Python packaging: `pyproject.toml`, `uv`, `pytest`, `ruff`, `mypy`
- CI split: fast adapter/unit tests and slower integration/regression runs
- Coverage focus: adapter contracts, orchestrator determinism, vintage transitions, template correctness
- No custom formula compiler — environmental policy logic is Python code in template modules

## Delivery Sequence

1. Computation adapter + OpenFisca integration (EPIC-1)
2. Carbon-tax + subsidy templates with baseline/reform comparison (EPIC-2)
3. Dynamic orchestrator (pluggable step pipeline) + vintage module MVP (EPIC-3)
4. Indicator layer and manifest lineage hardening (EPIC-4, EPIC-5)
5. Early no-code GUI workflow for analyst scenario operations (EPIC-6)

## Phase 2+ Architecture Extensions

- **Behavioral responses:** New orchestrator step applying elasticities between yearly computation runs
- **System dynamics bridge:** Aggregate stock-flow outputs derived from microsimulation vintage tracking results
- **Alternative computation backends:** Swap adapter implementations without changing orchestrator or indicator layers

## Cross-Cutting Concerns

1. Assumption transparency and manifest lineage across all runs
2. Deterministic sequencing in multi-year iterative execution
3. Adapter/version governance for OpenFisca compatibility
4. Clear data-contract validation at every ingestion boundary
5. Scenario/template versioning for auditability and collaboration
