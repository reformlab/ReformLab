# Synthetic Data Decision Document — ReformLab

**Generated:** 2026-03-23
**Status:** Proposed Decision Baseline
**Scope:** Tool implementation strategy for open microdata, synthetic data, exogenous inputs, calibration targets, and governance

## How to Read This Document

This document consolidates the full discussion held across research, synthesis, elicitation, and party-mode exploration into one implementation-facing decision baseline.

Read it in this order:

1. `Decision Summary` for the core recommendation
2. `Data Breakdown` for the system-wide evidence model
3. `Trust-Layered Hybrid Policy Lab` for the product architecture
4. `Implementation Workstreams` for execution planning
5. `References and Legitimacy` for institutional and academic grounding

---

## 1. Decision Summary

### 1.1 Core Decision

ReformLab should implement a **trust-layered hybrid policy lab** rather than a tool centered only on microdata access or only on synthetic data generation.

This means:

- ship an `open-core evidence base` first
- add `synthetic data` as a clearly labelled augmentation layer
- support `registered or restricted datasets` through optional user-managed connectors
- treat `validation, provenance, and governance` as first-class product features

### 1.2 Why This Decision

The discussion established five key facts:

1. EU data access has improved in discovery, catalogues, and infrastructure, but `fully open, directly usable, policy-grade microdata` remain limited.
2. Synthetic data and synthetic populations are now methodologically credible and institutionally legitimate enough to matter.
3. Synthetic outputs still require a stronger `trust and validation burden` than open official microdata.
4. The tool depends on more than microdata alone: it also requires exogenous inputs, calibration targets, and governance metadata.
5. The best implementation path is layered and risk-aware, not all-at-once.

### 1.3 Strategic Position

The product should be positioned as an **evidence system** rather than only a data product.

The key claim is:

> ReformLab combines openly usable structural data, clearly labelled synthetic analytic assets, optional user-connected restricted sources, and explicit validation and governance to support policy modelling and decision support.

---

## 2. Data Breakdown

### 2.1 Why a Broader Data Taxonomy Is Needed

The discussion showed that "data" is overloaded. Focusing only on microdata hides other equally important components of the modelling stack.

For implementation, ReformLab should distinguish four main data classes.

### 2.2 Structural Data

Structural data define the modeled units and relationships in the system.

Examples:

- household microdata
- individual microdata
- firm or establishment microdata
- geographic entities
- synthetic populations
- household-to-person and household-to-region links

This is where `open official microdata`, `restricted microdata`, and `synthetic populations` all belong.

### 2.3 Environmental Data

Environmental data define the context or scenario conditions in which the structural population evolves or makes decisions.

Examples:

- energy prices
- labor productivity
- inflation
- wages
- taxes and policy parameters
- regional indicators
- demographic trends
- technology costs

This category should be split internally into:

- `observed exogenous inputs`
- `behavioral assumptions and model parameters`

This distinction matters because not everything in the environment is measured data. Some are assumptions that need to be versioned and justified differently.

### 2.4 Calibration and Validation Data

Calibration and validation data define what "good enough" means for the model.

Examples:

- official aggregates
- survey totals
- employment and unemployment rates
- expenditure shares
- technology adoption rates
- regional distributions
- elasticity estimates
- historical outcomes

These datasets are not the modeled population itself. They are used to fit, test, and monitor the model.

### 2.5 Governance Data

Governance data determine what the tool is allowed to use and what it is allowed to claim.

Examples:

- provenance
- openness and licence status
- redistribution rights
- update cadence
- uncertainty and quality notes
- disclosure-risk labels
- intended-use restrictions
- validation status
- claim boundaries

This category is essential because trust in policy modelling depends on the entire evidence chain, not only on the quality of the underlying microdata.

### 2.6 Recommended Top-Level Data Model

ReformLab should document and implement the following top-level model:

| Data Class | Role | Example Questions |
| ----- | ----- | ----- |
| Structural Data | Define who or what is modeled | "Who are the households, people, firms, and places?" |
| Environmental Data | Define the scenario context | "What prices, policies, or macro conditions affect them?" |
| Calibration and Validation Data | Fit and test the model | "Does the model reproduce observed reality well enough?" |
| Governance Data | Constrain use and claims | "What can be used, and what can be claimed from it?" |

### 2.7 Recommended Internal Data Objects

The current codebase already has a useful structural wrapper in `PopulationData`, but the broader taxonomy discussed above suggests that additional first-class objects should be introduced over time.

The recommended minimal object set is:

| Object | Purpose | Notes |
| ----- | ----- | ----- |
| `PopulationData` | Structural population tables | Keep narrow; represents the modeled entities and their tables |
| `EnvironmentalData` | Observed exogenous inputs | Prices, macro assumptions, productivity, regional context |
| `BehavioralParameters` | Behavioral assumptions and model coefficients | Preferences, elasticities, rules that are not simply observed data |
| `CalibrationTargetSet` | Calibration and benchmark targets | Marginals, official aggregates, adoption rates, outcome targets |
| `DataAssetDescriptor` | Provenance and rights metadata | Source, licence, openness, update cadence, intended use |
| `ValidationReport` | Validation and trust evidence | Fit quality, deviations, subgroup checks, downstream performance |
| `SyntheticDataAsset` | Synthetic structural data with explicit status | Keeps synthetic populations visibly distinct from observed structural data |

### 2.8 Design Rule for `PopulationData`

`PopulationData` should remain a narrow structural container, not a catch-all object for all modelling context.

It should continue to represent:

- one or more entity tables
- lightweight structural metadata

It should not become the home for:

- exogenous inputs
- calibration targets
- validation evidence
- governance and trust logic for the full pipeline

Those concerns should be represented by separate objects and composed around `PopulationData`.

### 2.9 Recommended Helper Methods

The discussion also identified that `PopulationData` would benefit from lightweight ergonomic helpers for inspection and small immutable transformations.

Recommended inspection helpers:

- `entity_names` or `table_names`
- `get_table(entity)`
- `column_names(entity="default")`
- `schema_summary()`
- `summary()`

Recommended lightweight immutable transforms:

- `with_metadata(**updates)`
- `with_table(entity, table)`
- `select_entity(entity)`
- `select_columns(entity, columns)`
- `rename_columns(entity, mapping)`

These helpers would make the object easier to inspect and use in notebooks, tests, and debugging without turning it into a heavy data-processing service.

### 2.10 Transformation Boundary

Heavy transformations should remain outside `PopulationData`.

Examples of logic that should live elsewhere:

- multi-source joins and fusion
- harmonisation pipelines
- calibration procedures
- synthetic generation
- validation and trust scoring
- disclosure-risk assessment

This preserves a clean separation between:

- `data containers`
- `transformation services`
- `validation and governance services`

---

## 3. Trust-Layered Hybrid Policy Lab

### 3.1 Concept

The trust-layered hybrid policy lab is the recommended architecture for integrating open data, synthetic data, and restricted data without blurring their trust boundaries.

It is not just a repository of datasets. It is a **trust-governed evidence system**.

### 3.2 The Four Layers

#### Layer 1: Open Evidence Base

This is the default operational foundation.

Characteristics:

- directly usable
- no registration required
- low legal ambiguity
- suitable for product bundling or automated fetch workflows

Examples:

- Eurostat `EU-LFS` public use files
- other fully open structural and contextual datasets

Role:

- baseline analytics
- open-core product experience
- initial reproducibility and documentation standards

#### Layer 2: Synthetic Exploration Layer

This layer provides synthetic populations or synthetic microdata for bounded uses.

Characteristics:

- useful for exploration, demos, training, scenario analysis, and prototyping
- must be clearly labelled
- should not silently inherit the credibility of official microdata

Examples:

- Eurostat synthetic `EU-SILC` public use files
- GLOPOP-S
- internally generated synthetic populations

Role:

- augment sparse or restricted structural data
- enable safe experimentation
- support small-area modelling and scenario exploration

#### Layer 3: User-Connected Restricted Layer

This layer handles access-controlled or registration-based sources.

Characteristics:

- data accessed under user credentials or user institution rights
- no silent redistribution by ReformLab
- explicit provenance and rights tracking

Examples:

- ESS
- SHARE
- restricted Eurostat scientific or secure use files
- national administrative or survey sources

Role:

- advanced research workflows
- richer policy analysis when users have legitimate access
- user-managed integration of high-value data

#### Layer 4: Validation and Governance Layer

This is the control plane for the other layers.

Characteristics:

- cross-cutting
- required for all data classes and outputs
- governs trust, not just storage

Responsibilities:

- provenance
- access mode classification
- validation benchmarks
- disclosure-risk checks
- claim boundaries
- model and dataset status labels
- auditability and reproducibility

### 3.3 Core Product Rule

The user interface and APIs must make invalid interpretation difficult.

Concretely:

- official open data, synthetic data, and connected restricted data must not appear identical in the UI
- every dataset and output must expose its trust label and intended-use label
- synthetic results must remain visibly distinct from official observed data

### 3.4 Recommended Trust Labels

Every dataset and model output should carry one of these statuses:

- `production-safe`
- `exploratory`
- `demo-only`
- `restricted-connector`
- `validation-pending`
- `not-for-public-inference`

---

## 4. Option Analysis

### 4.1 Strategic Options Considered

| Option | Direct Usability | Legitimacy | Feasibility | Policy Relevance | Risk |
| ----- | ----- | ----- | ----- | ----- | ----- |
| Open-data-first only | High | Medium | High | Medium | Low |
| Open core + registered connectors | Medium | High | Medium | High | Medium |
| Synthetic-data-first platform | Medium | Medium-High | Medium-Low | High if validated | High |
| Trust-layered hybrid lab | High for baseline, medium for advanced use | High | Medium | High | Medium |

### 4.2 Decision

The `trust-layered hybrid lab` is preferred because it:

- allows an early MVP
- preserves institutional credibility
- creates room for differentiated synthetic-data capability
- reduces the risk of overclaiming
- supports both public and expert users without forcing a single trust model

---

## 5. Failure Pre-Mortem

### 5.1 Main Failure Modes

The initiative is most likely to fail if it:

- overclaims the validity of synthetic outputs
- treats synthetic data as the foundational truth layer too early
- targets too many audiences with the same workflow and trust framing
- leaves access friction unresolved for higher-value sources
- lacks a clear legitimacy narrative for institutions
- validates only simple marginals but not realistic downstream performance
- relies on methods that cannot be reproduced without inaccessible seed data

### 5.2 Preventive Design Rules

- Define strict `claims policy` categories
- Ship one narrow, defensible `flagship use case` first
- Build validation evidence early, not after launch
- Treat provenance as a product feature
- Separate exploratory synthetic outputs from decision-support outputs
- Make reproducibility inspectable

---

## 6. Recommended Product Positioning

### 6.1 Positioning Statement

ReformLab should be described as:

> A trust-layered hybrid policy lab that combines openly usable official data, synthetic analytic assets, optional user-connected restricted sources, and explicit validation and governance to support policy modelling and decision support.

### 6.2 Audience Segmentation

Different users require different trust contracts.

#### Policy Analysts

Need:

- fast scenario exploration
- usable dashboards
- bounded claims
- transparent assumptions

#### Researchers

Need:

- reproducibility
- source transparency
- validation detail
- exportable evidence trails

#### Institutions

Need:

- defensible governance
- clear allowed uses
- reduced reputational risk
- alignment with official-statistics practice

---

## 7. Implementation Workstreams

The discussion converged on six concrete workstreams.

### Workstream 1: Dataset Inventory and Legal/Usability Classification

Goal:

- build a complete matrix of candidate datasets

Required fields:

- source
- geographic coverage
- years
- data class
- access mode
- registration requirement
- licence and redistribution status
- direct usability in product
- known limitations

Output:

- a `source matrix` for open, synthetic, and restricted sources

### Workstream 2: Canonical Schema

Goal:

- create a unified internal schema across structural, environmental, calibration, and governance data

Required outcomes:

- canonical entity definitions
- standard identifiers
- trust labels
- mapping rules from source-specific variables into common fields

Output:

- a schema reference and mapping layer for tool ingestion

### Workstream 3: Synthetic Generation Pipeline Design

Goal:

- define how ReformLab will generate or integrate synthetic populations

Candidate methods:

- GenSynthPop-style spatial synthesis
- simPop-style survey-plus-aggregates synthesis
- FMF-style spatial microsimulation workflows
- controlled integration of public synthetic datasets such as GLOPOP-S

Output:

- a technical pipeline design with source requirements and generation stages

### Workstream 4: Validation and Disclosure-Risk Framework

Goal:

- define when a synthetic output is fit for exploratory use versus stronger use

Validation dimensions:

- marginals
- cross-tabs and joint distributions
- subgroup stability
- geography consistency
- downstream model performance
- privacy and disclosure-risk checks

Output:

- a validation dossier template and trust-status assignment framework

### Workstream 5: Institutional Legitimacy Memo and Citation Pack

Goal:

- prepare a defensible external narrative

Core sources:

- Eurostat
- UNECE
- JRC / DG FISMA
- Scientific Data papers
- GenSynthPop
- simPop
- GLOPOP-S

Output:

- a short memo that explains what is legitimate, what is exploratory, and what remains out of scope

### Workstream 6: MVP Definition for the Open-Core Release

Goal:

- identify the smallest deliverable that is useful and defensible

Recommended MVP:

- open structural dataset support
- environmental input ingestion
- calibration target ingestion
- trust labels in UI/API
- at least one flagship use case
- synthetic demo layer clearly labelled

Output:

- a scoped MVP implementation plan

---

## 8. Recommended MVP Sequence

### Phase 1: Open-Core Baseline

Build:

- support for directly usable open structural data
- support for environmental inputs
- support for calibration targets
- basic governance metadata and provenance

Do not yet claim:

- publication-grade synthetic evidence
- seamless restricted-data integration

### Phase 2: Synthetic Exploration

Build:

- synthetic dataset ingestion
- explicit trust labels
- exploratory scenario workflows
- synthetic versus observed comparison views

### Phase 3: Connector Layer

Build:

- user-managed access connectors
- provenance and rights recording
- source-specific ingestion contracts

### Phase 4: Native Synthetic Pipeline

Build:

- internal synthetic population generation
- reproducibility exports
- validation and risk reporting
- stronger trust-status certification rules

---

## 9. Tool Requirements

### 9.1 Required Product Capabilities

The tool should implement:

- dataset classification by trust and access mode
- distinction between structural, environmental, calibration, and governance data
- provenance capture for every source and derived output
- explicit trust labels in APIs and UI
- validation tracking for synthetic outputs
- scenario management across multiple data classes

### 9.2 Non-Negotiable Rules

- Synthetic data must never be presented as equivalent to observed official microdata without validation status.
- Registered or restricted data must not be treated as part of the default public baseline.
- Governance metadata must be stored and surfaced, not treated as documentation outside the product.
- The tool must make claim boundaries visible at the point of use.

---

## 10. References and Legitimacy

### 10.1 Institutional Sources

- Eurostat public microdata overview: https://ec.europa.eu/eurostat/web/microdata/public-microdata
- Eurostat access conditions: https://ec.europa.eu/eurostat/web/microdata/access
- UNECE synthetic data starter guide: https://unece.org/statistics/publications/synthetic-data-official-statistics-starter-guide
- Eurostat AIML4OS WP13: https://cros.ec.europa.eu/book-page/aiml4os-wp13-generation-synthetic-data-official-statistics-techniques-and-applications
- JRC synthetic data pilot context: https://publications.jrc.ec.europa.eu/repository/handle/JRC137249

### 10.2 Academic and Technical Sources

- GLOPOP-S: https://www.nature.com/articles/s41597-024-03864-2
- GLOPOP-S dataset: https://doi.org/10.7910/DVN/KJC3RH
- GenSynthPop: https://link.springer.com/article/10.1007/s10458-024-09680-7
- simPop: https://www.jstatsoft.org/article/view/v079i10
- Great Britain synthetic population workflow: https://www.nature.com/articles/s41597-022-01124-9

### 10.3 Internal Supporting Artifacts

- [technical-eu-microdata-access-and-synthetic-population-research-2026-03-23.md](/Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/research/technical-eu-microdata-access-and-synthetic-population-research-2026-03-23.md)
- [open-synthetic-data-initiatives-2026-03-23.md](/Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/research/open-synthetic-data-initiatives-2026-03-23.md)
- [README.md](/Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/research/open-eurostat-microdata-schema-2026-03-23/README.md)

---

## 11. Final Recommendation

ReformLab should not frame its future only as "getting more microdata" or only as "building synthetic data."

It should implement a **trust-layered hybrid policy lab** with:

- a broad evidence taxonomy
- a layered trust model
- a strict distinction between official, synthetic, and restricted data
- a validation and governance control plane
- a phased delivery path through six concrete workstreams

This is the most defensible path technically, institutionally, and product-wise.
