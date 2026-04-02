---
title: ReformLab Architecture Diagrams
description: Three complementary Mermaid diagrams covering layered architecture, class/interface structure, and orchestrator runtime flow
author: Paige (Tech Writer)
date: 2026-02-25
source: architecture.md, prd.md, epics.md
---

# ReformLab Architecture Diagrams

Three views of the same system at different zoom levels:

1. **Data Flow Architecture** — how data and policy flow through the system to produce results, and how the orchestrator loops it over time
2. **Class / Interface Diagram** — key types, protocols, and relationships within each package
3. **Orchestrator Sequence Diagram** — runtime flow of the core product logic

---

## 1. Data Flow Architecture

Three input streams converge into OpenFisca computation, producing distributional results. The orchestrator wraps the entire process in a multi-year loop, feeding each year's outputs back as the next year's inputs with vintage and state updates.

```mermaid
flowchart LR
    subgraph INPUTS ["DATA INPUTS"]
        direction TB
        POP["👥 Synthetic Populations\n(households, income,\nhousing, energy profile)"]
        ENV["🌍 Environmental Data\n(emission factors,\nenergy prices, fleet ages)"]
        POL["📋 Policy Scenarios\n(carbon tax rate, subsidies,\nredistribution method)"]
    end

    subgraph CONTRACTS ["Data Contracts"]
        VAL["Schema Validation\n& Mapping"]
    end

    subgraph COMPUTE ["COMPUTATION"]
        direction TB
        ADAPT["OpenFisca Adapter"]
        OF["OpenFisca\n(tax-benefit engine)"]
        TMPL["Environmental\nPolicy Templates"]
        ADAPT --> OF
        OF --> TMPL
    end

    subgraph RESULTS ["WHAT YOU GET"]
        direction TB
        DIST["Who wins, who loses?\n(distributional by decile)"]
        FISC["What does it cost the state?\n(fiscal balance)"]
        WELF["How are households affected?\n(welfare, net gains/losses)"]
        PANEL["How does it change over time?\n(year-by-year panel)"]
    end

    POP --> VAL
    ENV --> VAL
    POL --> VAL
    VAL --> ADAPT

    TMPL --> DIST
    TMPL --> FISC
    TMPL --> WELF
    TMPL --> PANEL

    subgraph LOOP ["🔄 ORCHESTRATOR — CORE PRODUCT"]
        direction TB
        ORCH["Yearly Loop\n(year t → t+1 → ... → t+n)"]
        VINT["Vintage & State Updates\n(fleet aging, carry-forward)"]
        ORCH --> VINT
    end

    PANEL -. "feed year t\nresults back" .-> ORCH
    VINT -. "updated state\nfor next year" .-> VAL

    subgraph GOV ["📝 GOVERNANCE (runs alongside)"]
        MAN["Run Manifests · Assumption Logs · Lineage"]
    end

    COMPUTE -. "records every step" .-> GOV

    style INPUTS fill:#1b4332,color:#fff,stroke:#081c15
    style COMPUTE fill:#2d6a4f,color:#fff,stroke:#1b4332
    style RESULTS fill:#40916c,color:#fff,stroke:#2d6a4f
    style LOOP fill:#d4a373,color:#000,stroke:#bc6c25
    style GOV fill:#6c757d,color:#fff,stroke:#495057
    style CONTRACTS fill:#344e41,color:#fff,stroke:#1b4332
```

---

## 2. Class / Interface Diagram

Key types, protocols (`<<Protocol>>`), and relationships across all 8 packages.

```mermaid
classDiagram
    direction TB

    namespace computation {
        class ComputationAdapter {
            <<Protocol>>
            +compute(population, policy, period) ComputationResult
            +version() str
        }
        class OpenFiscaAdapter {
            -version_pin : str
            -mapping_config : MappingConfig
            +compute(population, policy, period) ComputationResult
            +version() str
        }
        class PopulationData {
            +households : DataFrame
            +metadata : dict
        }
        class PolicyConfig {
            +policy_type : str
            +parameters : dict
            +year_schedule : dict
        }
        class ComputationResult {
            +outputs : DataFrame
            +period : int
            +adapter_version : str
        }
    }

    namespace data {
        class DataPipeline {
            +load_population(source) PopulationData
            +load_emission_factors(source) DataFrame
            +validate(contract) ValidationResult
        }
        class DataContract {
            +required_fields : list
            +field_types : dict
            +validate(data) ValidationResult
        }
        class DataSource {
            +path : str
            +format : str
            +hash : str
        }
    }

    namespace templates {
        class ScenarioTemplate {
            +policy_type : str
            +baseline_params : dict
            +year_schedule : dict
            +apply(population, year) DataFrame
        }
        class Reform {
            +base_scenario_id : str
            +overrides : dict
        }
        class ScenarioRegistry {
            +register(template) str
            +get(version_id) ScenarioTemplate
            +clone(version_id) ScenarioTemplate
            +list_versions() list
        }
    }

    namespace orchestrator {
        class OrchestratorStep {
            <<Protocol>>
            +execute(state, year) OrchestratorState
            +name() str
        }
        class YearlyOrchestrator {
            -adapter : ComputationAdapter
            -pipeline : StepPipeline
            -governance : ManifestWriter
            +run(scenario, start, end) PanelResult
        }
        class StepPipeline {
            -steps : list~OrchestratorStep~
            +register(step)
            +execute_all(state, year) OrchestratorState
        }
        class OrchestratorState {
            +population : PopulationData
            +vintage_state : dict
            +year : int
            +seed : int
        }
        class PanelResult {
            +yearly_results : dict
            +manifest_id : str
            +export_csv(path)
            +export_parquet(path)
        }
    }

    namespace vintage {
        class VintageTransitionStep {
            -asset_class : str
            -transition_rules : list~TransitionRule~
            +execute(state, year) OrchestratorState
            +name() str
        }
        class CarryForwardStep {
            -rules : dict
            +execute(state, year) OrchestratorState
            +name() str
        }
        class AssetCohort {
            +asset_class : str
            +vintage_year : int
            +count : int
            +attributes : dict
        }
        class TransitionRule {
            +asset_class : str
            +aging_fn : Callable
            +replacement_fn : Callable
        }
    }

    namespace indicators {
        class Indicator {
            <<Protocol>>
            +compute(panel) DataFrame
            +name() str
        }
        class DistributionalIndicator {
            +grouping : str
            +compute(panel) DataFrame
        }
        class WelfareIndicator {
            +compute(panel) DataFrame
        }
        class FiscalIndicator {
            +cumulative : bool
            +compute(panel) DataFrame
        }
        class ScenarioComparison {
            +baseline : PanelResult
            +reform : PanelResult
            +compare() DataFrame
        }
    }

    namespace governance {
        class RunManifest {
            +run_id : str
            +adapter_version : str
            +scenario_version : str
            +data_hashes : dict
            +seeds : dict
            +parameters : dict
            +timestamp : str
            +verify_integrity() bool
        }
        class AssumptionLog {
            +entries : list
            +add(source, method, value)
        }
        class RunLineage {
            +parent_id : str
            +child_ids : list
            +link(parent, child)
            +get_children(run_id) list
        }
    }

    OpenFiscaAdapter ..|> ComputationAdapter
    VintageTransitionStep ..|> OrchestratorStep
    CarryForwardStep ..|> OrchestratorStep
    DistributionalIndicator ..|> Indicator
    WelfareIndicator ..|> Indicator
    FiscalIndicator ..|> Indicator

    YearlyOrchestrator --> ComputationAdapter : uses
    YearlyOrchestrator --> StepPipeline : executes
    YearlyOrchestrator --> RunManifest : writes
    StepPipeline --> OrchestratorStep : contains
    YearlyOrchestrator --> ScenarioTemplate : reads
    ScenarioRegistry --> ScenarioTemplate : stores
    Reform --> ScenarioTemplate : overrides
    VintageTransitionStep --> AssetCohort : updates
    VintageTransitionStep --> TransitionRule : applies
    ScenarioComparison --> PanelResult : compares
    DataPipeline --> DataContract : validates against
    DataPipeline --> PopulationData : produces
    RunLineage --> RunManifest : links
```

---

## 3. Orchestrator Sequence Diagram

Runtime flow of a multi-year scenario run — the core product logic. Shows how the yearly loop coordinates the adapter, templates, pluggable steps, governance, and indicators.

```mermaid
sequenceDiagram
    actor User
    participant API as Python API / GUI
    participant ORCH as YearlyOrchestrator
    participant REG as ScenarioRegistry
    participant PIPE as StepPipeline
    participant ADAPT as ComputationAdapter
    participant TMPL as ScenarioTemplate
    participant VIN as VintageTransitionStep
    participant CFW as CarryForwardStep
    participant GOV as RunManifest
    participant LIN as RunLineage
    participant IND as Indicators

    User ->> API: run(scenario_id, start=2025, end=2035)
    API ->> REG: get(scenario_id)
    REG -->> API: ScenarioTemplate + Reform

    API ->> ORCH: run(template, reform, 2025, 2035)
    ORCH ->> GOV: create parent manifest

    loop For each year t in [2025 .. 2035]
        Note over ORCH: Year t begins

        ORCH ->> ADAPT: compute(population, policy, t)
        ADAPT -->> ORCH: ComputationResult(t)

        ORCH ->> TMPL: apply(population, t)
        TMPL -->> ORCH: environmental adjustments

        ORCH ->> PIPE: execute_all(state, t)

        PIPE ->> VIN: execute(state, t)
        Note right of VIN: Age cohorts, apply<br/>fleet turnover rules
        VIN -->> PIPE: updated vintage state

        PIPE ->> CFW: execute(state, t)
        Note right of CFW: Income updates,<br/>demographic changes
        CFW -->> PIPE: updated population state

        PIPE -->> ORCH: OrchestratorState(t)

        ORCH ->> GOV: record year-t manifest (seed, steps, hashes)
        ORCH ->> LIN: link(parent_run, year_t_run)

        Note over ORCH: Feed state → year t+1
    end

    ORCH -->> API: PanelResult (all years)

    API ->> IND: compute(panel)
    IND -->> API: distributional + welfare + fiscal tables

    API -->> User: results + comparison + manifest
```

---

## Reading Guide

| Diagram | Question it answers | Audience |
|---|---|---|
| Data Flow Architecture | "What goes in, what happens, what comes out — and how does the loop work?" | Everyone — analysts, stakeholders, new contributors |
| Class / Interface | "What are the key types? Where are the extension points?" | Developers implementing or extending the system |
| Orchestrator Sequence | "What happens at runtime when I run a scenario?" | Developers, testers, and analysts understanding the core loop |
