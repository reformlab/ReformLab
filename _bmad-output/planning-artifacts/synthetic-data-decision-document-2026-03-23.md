# Synthetic Data Decision Document — ReformLab

**Generated:** 2026-03-23
**Status:** Implementation Decision Baseline
**Scope:** Current-phase implementation strategy for open official data, synthetic data, exogenous inputs, calibration targets, and governance

## How to Read This Document

This document consolidates the full discussion held across research, synthesis, elicitation, and party-mode exploration into one implementation-facing decision baseline.

Read it in this order:

1. `Decision Summary` for the core recommendation
2. `Data Breakdown` for the system-wide evidence model
3. `Trust-Governed Open + Synthetic Policy Lab` for the product architecture
4. `Implementation Workstreams` for execution planning
5. `References and Legitimacy` for institutional and academic grounding

---

## 1. Decision Summary

### 1.1 Core Decision

ReformLab should implement a **trust-governed open + synthetic policy lab** for the current phase rather than a tool centered only on microdata access or only on synthetic data generation.

This means:

- ship and stabilize an `open evidence base`
- add `synthetic data` as a clearly labelled augmentation layer
- treat `validation, provenance, and governance` as first-class product features
- defer `restricted-data connectors` until a later phase

### 1.1b Current-Phase Scope Boundary

This document is implementation-ready for the **current phase**, not a generic long-term strategy memo.

In scope now:

- open official structural data
- public synthetic datasets and synthetic comparison workflows
- exogenous inputs
- calibration targets
- trust labels, provenance, and governance metadata
- the `TasteParameters` / `ExogenousContext` refactor needed to support the modelling stack

Explicitly out of scope for the current phase:

- restricted-data connectors
- user-managed credential flows
- ReformLab-managed processing of restricted raw data
- native internal synthetic population generation

### 1.2 Why This Decision

The discussion established five key facts:

1. EU data access has improved in discovery, catalogues, and infrastructure, but `fully open, directly usable, policy-grade microdata` remain limited.
2. Synthetic data and synthetic populations are now methodologically credible and institutionally legitimate enough to matter.
3. Synthetic outputs still require a stronger `trust and validation burden` than open official microdata.
4. The tool depends on more than microdata alone: it also requires exogenous inputs, calibration targets, and governance metadata.
5. Restricted-data workflows add substantial operational and legal complexity and are not required for the current implementation phase.

### 1.3 Strategic Position

The product should be positioned as an **evidence system** rather than only a data product.

The key claim is:

> ReformLab combines openly usable structural data, clearly labelled synthetic analytic assets, exogenous inputs, calibration targets, and explicit validation and governance to support policy modelling and decision support in the current phase.

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

This is where `open official microdata` and `synthetic populations` belong in the current phase. `Restricted microdata` remains part of the broader taxonomy, but it is deferred from current implementation.

### 2.3 Exogenous Data

Exogenous data define the context or scenario conditions that the simulation consumes but does not produce. They are observed or projected time series from external institutions. They enter the model as **inputs to cost computation, transition rules, policy schedules, and indicator calculations** — never as parameters to estimate.

Examples:

- energy prices (electricity, gas, fuel — from IEA, Eurostat, CRE)
- carbon tax trajectories (from policy schedules)
- technology costs (EV prices, heat pump costs — from ADEME, IEA)
- labor productivity growth (from INSEE, OECD)
- inflation and wage indices (from INSEE, Eurostat)
- demographic trends (from INSEE projections)
- regional indicators (from Eurostat NUTS)

This category is strictly **read-only** from the simulation's perspective. The orchestrator looks up exogenous values by year; it never mutates them. Each series carries provenance and processing metadata (source institution, vintage, unit, frequency, interpolation method, aggregation method, revision policy).

Each scenario carries its own `ExogenousContext`. Scenario comparison workflows (baseline vs reform) may differ in both policy parameters and exogenous assumptions (e.g., high vs low energy price paths). `ExogenousContext.validate_coverage(start_year, end_year)` must be called before orchestration begins. Missing years are a hard error, not a silent extrapolation.

### 2.3b Taste Parameters (Unobserved Preference Coefficients)

Taste parameters are a distinct category from exogenous data. They are **unobserved preference weights** that determine how households translate observed attributes into utility and choice.

They consist of two sub-categories:

**Alternative-Specific Constants (ASCs):**

- One constant per alternative (one normalized to zero as reference)
- Capture all systematic unobserved preference for an alternative net of observed attributes
- Inertia, habit, brand loyalty, social norms, information asymmetry
- The **primary calibration target** — if the user calibrates nothing else, calibrate ASCs

**Named beta coefficients:**

- `beta_cost`, `beta_time`, `beta_comfort`, `beta_range`, etc.
- Weight how observed attributes translate into utility
- The user declares which betas their model includes based on domain knowledge
- Each beta can be **fixed** (from literature, e.g., Dargay & Gately 1999) or **calibrated** (estimated against observed transition rates)

Taste parameters are **domain-specific**. Vehicle choice and heating choice have independent ASCs and betas. A multi-domain simulation carries one `TasteParameters` instance per active decision domain.

The utility function is:

```text
V_ij = ASC_j + β_cost × cost_ij + β_time × time_ij + ...
```

Where `cost_ij` is computed from exogenous data (Section 2.3) and population characteristics (Section 2.2). The betas and ASCs are preference parameters, not data.

**This distinction matters because:**

- Exogenous data has institutional provenance and is updated when institutions publish new series
- Taste parameters have academic provenance (literature references) or are estimated through calibration
- They enter the model at different layers: exogenous data feeds cost matrix computation; taste parameters feed the utility/logit model
- They have different governance requirements: exogenous data needs source tracking; taste parameters need calibration diagnostics and literature citations

### 2.4 Calibration and Validation Data

Calibration and validation data define what "good enough" means for the model. They are **observed aggregate outcomes** that the model should reproduce.

Examples:

- official aggregates (revenue, expenditure totals)
- survey totals and marginal distributions
- employment and unemployment rates
- expenditure shares by category
- technology adoption rates and transition rates (e.g., EV market share by year)
- regional distributions
- historical outcomes (known policy effects from ex-post evaluations)

These datasets are not the modeled population itself. They are used to fit, test, and monitor the model.

Note: Elasticity estimates from the literature are **fixed taste parameters** (Section 2.3b), not calibration targets. Calibration targets are observed aggregate outcomes (transition rates, market shares, adoption curves) used to estimate the parameters that the literature does not provide.

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
| Exogenous Data | Provide observed/projected context inputs | "What are energy prices, carbon tax rates, technology costs this year?" |
| Calibration and Validation Data | Fit and test the model | "Does the model reproduce observed reality well enough?" |
| Governance Data | Constrain use and claims | "What can be used, and what can be claimed from it?" |

Note: Taste parameters (ASCs and betas) are **model specification**, not data. They are documented in Section 2.3b and 2.7b. They define the analyst's modelling choices, whereas the four data classes above define external inputs loaded from institutional or user sources.

### 2.7 Recommended Internal Data Objects

The current codebase already has a useful structural wrapper in `PopulationData`, but the broader taxonomy discussed above suggests that additional first-class objects should be introduced over time.

The recommended minimal object set is:

| Object | Purpose | Notes |
| ----- | ----- | ----- |
| `PopulationData` | Structural population tables | Keep narrow; represents the modeled entities and their tables |
| `ExogenousTimeSeries` | Single named, provenanced time series | Year-indexed values with unit, source institution, interpolation method |
| `ExogenousContext` | Groups all exogenous series for a scenario | Read-only year-lookup; validates coverage over simulation horizon |
| `TasteParameters` | User-declared preference coefficients | ASCs (per-alternative constants) + named betas; each parameter marked as calibrated or fixed (from literature) |
| `CalibrationTargetSet` | Calibration and benchmark targets | Marginals, official aggregates, adoption rates, outcome targets |
| `DataAssetDescriptor` | Provenance and rights metadata | Source, licence, openness, update cadence, intended use |
| `ValidationReport` | Validation and trust evidence | Fit quality, deviations, subgroup checks, downstream performance |
| `SyntheticDataAsset` | Synthetic structural data with explicit status | Keeps synthetic populations visibly distinct from observed structural data |

### 2.7b Architectural Separation: Exogenous Data vs Taste Parameters vs Endogenous State

The orchestrator manages three distinct categories of state during multi-year simulation. These must not be conflated.

**Exogenous context (read-only, year-indexed):**

- `ExogenousContext` holds all `ExogenousTimeSeries` for a scenario
- The simulation looks up values by year but never mutates them
- Cost matrix computation receives `exogenous.get(name, year)` as input
- CarryForwardStep does **not** manage exogenous data — it is not endogenous state

**Taste parameters (fixed or calibrated, time-invariant within a run):**

- `TasteParameters` holds ASCs and named betas
- The user declares which parameters exist based on their model specification
- Each parameter is either fixed (value from literature with citation) or calibrated (optimized by CalibrationEngine against CalibrationTargetSet)
- ASCs are the default calibration target: they absorb unobserved heterogeneity
- The utility function is: `V_ij = ASC_j + Σ_k(β_k × attribute_kij)`

**Endogenous state (simulation-produced, carried forward):**

- `YearState.data` holds population state, vintage cohorts, accumulated variables
- `CarryForwardStep` evolves endogenous state between years (scale, increment, custom rules)
- This is the only category that the simulation both reads and writes

| Category | Mutated by simulation? | Managed by | Provenance |
| ----- | ----- | ----- | ----- |
| Exogenous data | No — read-only lookup | `ExogenousContext` | Institutional (IEA, INSEE, Eurostat) |
| Taste parameters | No — fixed for the run | `TasteParameters` | Literature or calibration |
| Endogenous state | Yes — updated each year | `YearState` + `CarryForwardStep` | Simulation-produced |

### 2.7c Calibration Engine Implications

The refactored `TasteParameters` requires a corresponding refactor of the calibration engine:

- The optimizer works over a **parameter vector** containing all parameters in the `calibrate` set
- Parameters in the `fixed` set are used in utility computation but frozen during optimization
- `CalibrationConfig` accepts `initial_values: dict[str, float]` and `bounds: dict[str, tuple[float, float]]` instead of scalar `initial_beta` and `beta_bounds`
- `CalibrationResult` reports optimized values for all calibrated parameters
- Governance manifests record which parameters were calibrated vs fixed, and the literature source for each fixed value

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

## 3. Trust-Governed Open + Synthetic Policy Lab

### 3.1 Concept

The trust-governed open + synthetic policy lab is the recommended architecture for the current phase. It integrates open official data and synthetic data without blurring their trust boundaries.

It is not just a repository of datasets. It is a **trust-governed evidence system** with governance as a cross-cutting control plane. Restricted data remains a deferred future extension rather than a partially supported feature.

### 3.2 Classification Axes for Implementation

Implementation should classify every dataset and every derived output on three **independent** axes:

- `origin` — where the asset comes from
- `access_mode` — how ReformLab obtains it
- `trust_status` — what can be claimed about it

#### Origin

- `open-official` — openly usable official or institutional data
- `synthetic-public` — public synthetic datasets from trusted external producers
- `synthetic-internal` — internally generated synthetic assets (future phase)
- `restricted` — access-controlled data (future phase)

#### Access Mode

- `bundled` — distributed with the product or repo
- `fetched` — obtained automatically from public sources
- `deferred-user-connector` — reserved for future restricted-data integration

#### Trust Status

- `production-safe`
- `exploratory`
- `demo-only`
- `validation-pending`
- `not-for-public-inference`

### 3.3 Current-Phase Supported Combinations

| Origin | Access Mode | Current Phase Support | Allowed Trust Statuses | Notes |
| ----- | ----- | ----- | ----- | ----- |
| `open-official` | `bundled` or `fetched` | Yes | `production-safe`, `exploratory` | Default baseline for current delivery |
| `synthetic-public` | `bundled` or `fetched` | Yes | `exploratory`, `demo-only`, `validation-pending`, `not-for-public-inference` | Must remain visually and semantically distinct from observed data |
| `synthetic-internal` | not yet implemented | No | future | Native generation is deferred |
| `restricted` | `deferred-user-connector` | No | future | Not part of current implementation |

### 3.4 Governance Control Plane

The governance control plane is required for all current-phase assets and outputs.

Responsibilities:

- provenance
- origin classification
- access mode classification
- validation benchmarks
- claim boundaries
- model and dataset status labels
- auditability and reproducibility

### 3.5 Core Product Rule

The user interface and APIs must make invalid interpretation difficult.

Concretely:

- open official data and synthetic data must not appear identical in the UI
- every dataset and output must expose `origin`, `access_mode`, `trust_status`, and intended-use label
- synthetic results must remain visibly distinct from official observed data
- any attempt to load deferred restricted sources in the current phase must fail explicitly rather than degrade into partial support

---

## 4. Option Analysis

### 4.1 Strategic Options Considered

| Option | Direct Usability | Legitimacy | Feasibility | Policy Relevance | Risk |
| ----- | ----- | ----- | ----- | ----- | ----- |
| Open-data-only baseline | High | Medium | High | Medium | Low |
| Synthetic-data-first platform | Medium | Medium-High | Medium-Low | High if validated | High |
| Open + synthetic current-phase baseline | High | High | High | High | Medium |
| Full hybrid including restricted connectors | Medium | High | Low-Medium | High | High in current phase |

### 4.2 Decision

The `open + synthetic current-phase baseline` is preferred because it:

- matches the actual implementation scope
- preserves institutional credibility
- creates room for differentiated synthetic-data capability
- reduces the risk of overclaiming
- avoids premature restricted-data architecture

---

## 5. Failure Pre-Mortem

### 5.1 Main Failure Modes

The initiative is most likely to fail if it:

- overclaims the validity of synthetic outputs
- treats synthetic data as the foundational truth layer too early
- collapses `origin`, `access_mode`, and `trust_status` into one ambiguous label
- tries to build deferred restricted-data support into the current phase
- lacks a clear legitimacy narrative for institutions
- validates only simple marginals but not realistic downstream performance
- relies on methods that cannot be reproduced without inaccessible seed data
- underestimates the migration blast radius of the taste-parameter and exogenous-data refactor

### 5.2 Preventive Design Rules

- Define strict `claims policy` categories
- Ship one narrow, defensible `flagship use case` first
- Build validation evidence early, not after launch
- Keep calibration targets and validation benchmarks separate
- Treat provenance as a product feature
- Separate exploratory synthetic outputs from decision-support outputs
- Exclude restricted-data ingestion from current-phase acceptance criteria
- Make reproducibility inspectable

---

## 6. Recommended Product Positioning

### 6.1 Positioning Statement

ReformLab should be described as:

> A trust-governed evidence system that combines openly usable official data, clearly labelled synthetic analytic assets, exogenous inputs, calibration targets, and explicit validation and governance to support policy modelling and decision support in the current phase.

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

The discussion converged on seven concrete workstreams. Each workstream is written so it can be turned directly into one or more implementation EPICs.

### Workstream 1: Dataset Inventory and Legal/Usability Classification

Goal:

- build a complete matrix of current-phase candidate datasets

Required fields:

- source
- geographic coverage
- years
- data class
- origin
- access mode
- default trust status
- licence and redistribution status
- direct usability in product
- known limitations

Output:

- a versioned `source matrix` for current-phase open and synthetic sources, plus a deferred appendix for restricted sources

Acceptance criteria:

- every dataset referenced by docs, demos, or the flagship use case appears in the matrix
- every row includes `origin`, `access_mode`, and `default trust_status`
- datasets with unclear redistribution status are blocked from current-phase ingestion
- the flagship use case has an approved source subset explicitly marked `current-phase usable`

### Workstream 2: Shared Asset Envelope and Typed Schemas

Goal:

- create a shared asset envelope plus typed schemas across structural, exogenous, calibration, and governance data

Required outcomes:

- canonical entity definitions
- standard identifiers
- a common `DataAssetDescriptor` envelope carrying origin, access mode, trust status, provenance, and intended use
- typed payload mappings for structural, exogenous, and calibration assets
- explicit separation between governance metadata and domain payloads

Output:

- a schema reference and mapping layer for tool ingestion

Acceptance criteria:

- an asset can be classified before payload-specific parsing begins
- structural, exogenous, and calibration assets validate through separate object types or schemas
- mapping rules exist for the flagship datasets in the current phase
- no current-phase schema requires restricted-data handling

### Workstream 3: Synthetic Asset Integration and Future Generation Design

Goal:

- integrate public synthetic assets now and define the prerequisites for future native synthetic generation

Current-phase scope:

- ingestion of public synthetic datasets such as GLOPOP-S and synthetic EU-SILC variants
- observed-versus-synthetic comparison workflows for the flagship use case
- provenance and trust labelling for all synthetic assets

Deferred design inputs:

- GenSynthPop-style spatial synthesis
- simPop-style survey-plus-aggregates synthesis
- FMF-style spatial microsimulation workflows
- requirements for native internal generation

Output:

- a synthetic integration spec for the current phase and a separate future-generation decision note

Acceptance criteria:

- at least one public synthetic dataset can be loaded through the current ingestion path
- synthetic assets always carry mandatory provenance and trust labels
- the flagship use case exposes an observed-versus-synthetic comparison
- native internal generation remains explicitly deferred with prerequisite inputs listed

### Workstream 4: Validation and Disclosure-Risk Framework

Goal:

- define when a dataset or model output is fit for `exploratory`, `validation-pending`, or `production-safe` use

Validation dimensions:

- marginals
- cross-tabs and joint distributions
- subgroup stability
- geography consistency
- downstream model performance
- privacy and disclosure-risk checks

Output:

- a validation dossier template, claims policy, and trust-status assignment framework

Acceptance criteria:

- calibration inputs and validation benchmarks are represented separately
- synthetic outputs cannot be marked `production-safe` without an explicit validation dossier
- trust-status rules are documented for both open official data and synthetic outputs
- APIs and UI surfaces can expose trust status and intended-use labels

### Workstream 5: Claims, Provenance, and Citation Pack

Goal:

- prepare the governance artifacts and traceability needed to support implementation, docs, and product copy

Core sources:

- Eurostat
- UNECE
- JRC / DG FISMA
- Scientific Data papers
- GenSynthPop
- simPop
- GLOPOP-S

Output:

- a claims policy, citation pack, and provenance template aligned with current-phase product surfaces

Acceptance criteria:

- each major claim in the decision summary and positioning sections has a citation or internal reference
- fixed taste parameters can carry literature citations in governance manifests
- current-phase product copy does not promise restricted-data support
- governance manifest fields align with the labels exposed in UI and APIs

### Workstream 6: Current-Phase Release Slice

Goal:

- define the smallest current-phase release that is useful, defensible, and sufficient to anchor downstream EPICs

Recommended current-phase release:

- open structural dataset support
- exogenous input ingestion
- calibration target ingestion
- trust labels in UI/API
- at least one flagship use case
- synthetic public dataset ingestion and observed-versus-synthetic comparison
- no restricted-data connectors

Output:

- a scoped implementation plan and EPIC map for the current phase

Acceptance criteria:

- one flagship end-to-end scenario runs on open official data
- the same scenario can consume at least one synthetic dataset variant
- outputs expose origin, access mode, trust status, and provenance
- deferred items are listed explicitly and excluded from current-phase acceptance

### Workstream 7: Exogenous Data and Taste Parameter Refactor

This workstream implements the architectural separation defined in Sections 2.3, 2.3b, and 2.7b. It refactors the existing discrete choice, calibration, and orchestrator subsystems to properly distinguish exogenous data, taste parameters, and endogenous state.

#### Implementation Path: Two-Story Pragmatic Approach

Four paths were evaluated (bottom-up types-first, vertical slice by domain, parallel tracks, pragmatic two-story). The pragmatic path was selected because it matches the conceptual boundary (taste parameters are one thing, exogenous data is another), minimizes intermediate breakage, and fits a solo developer workflow.

#### Story A: Generalized TasteParameters with ASCs and User-Declared Betas

Scope:

- Refactor `TasteParameters` in `discrete_choice/types.py`:
  - `asc: dict[str, float]` — per-alternative constants (one normalized to zero)
  - `betas: dict[str, float]` — named taste coefficients declared by the user
  - `calibrate: frozenset[str]` — parameter names to optimize
  - `fixed: frozenset[str]` — parameter names held constant (from literature)
  - `reference_alternative: str` — alternative whose ASC is normalized to zero
- Factory method `TasteParameters.from_beta_cost(beta_cost)` plus a compatibility adapter for existing single-parameter callers during migration
- Refactor `compute_utilities()` in `discrete_choice/logit.py`: `V_ij = ASC_j + Σ_k(β_k × attribute_kij)`
- Introduce a domain utility-input structure that can provide named attribute matrices without overloading the current alternative-indexed `CostMatrix`
- `LogitChoiceStep` consumes the refactored `TasteParameters` and utility inputs
- Refactor `CalibrationEngine` in `calibration/engine.py`: vector optimization over `calibrate` parameter set; fixed parameters frozen during optimization but used in utility computation
- Refactor `CalibrationConfig`: `initial_values: dict[str, float]` and `bounds: dict[str, tuple[float, float]]` replace scalar `initial_beta` and `beta_bounds`
- Refactor `CalibrationResult`: reports optimized values for all calibrated parameters
- Add diagnostics for parameter identifiability, failed convergence, and bound-hitting solutions
- Governance manifests record which parameters were calibrated vs fixed, with literature source for each fixed value
- Update discrete_choice, calibration, provenance, demos, docs, and tests

Dependencies and impact:

- touches discrete_choice, calibration, provenance, demos, docs, and tests
- requires a temporary compatibility shim until single-`beta_cost` call sites are migrated

Acceptance criteria:

- the existing single-parameter workflow still runs through the compatibility path
- at least one flagship domain runs end-to-end with ASCs plus named beta coefficients
- calibration output reports calibrated versus fixed parameters and diagnostics
- tests, demos, and docs are updated to the new contract

#### Story B: ExogenousContext as Read-Only Scenario Data

Scope:

- New `ExogenousTimeSeries` in `data/exogenous.py`:
  - `name: str` — series identifier (e.g., `"energy_price_electricity"`)
  - `values: dict[int, float]` — year-indexed values
  - `unit: str` — physical unit (e.g., `"EUR/kWh"`)
  - `source: str` — institutional provenance (e.g., `"IEA World Energy Outlook 2024"`)
  - `vintage: str` — publication or extraction vintage
  - `frequency: str` — source frequency before yearly use (`"annual"`, `"monthly"`, etc.)
  - `interpolation: str` — `"linear"`, `"step"`, or `"none"`
  - `aggregation_method: str` — how source values are converted for yearly use
  - `revision_policy: str` — how revisions are tracked or frozen
- New `ExogenousContext` in `data/exogenous.py`:
  - `series: dict[str, ExogenousTimeSeries]` — all series for the scenario
  - `get(name, year) -> float` — year lookup with interpolation
  - `get_year_slice(year) -> dict[str, float]` — convenience lookup for scenario execution
  - `validate_coverage(start_year, end_year)` — hard error on missing years
- `OrchestratorConfig` gains optional `exogenous_context: ExogenousContext | None`
- Domain cost computation functions accept optional exogenous year slice
- Tests for coverage validation, interpolation, missing year errors, scenario-level composition
- Update the flagship domain wiring, demos, docs, and tests once the new context is consumed

Dependencies and impact:

- the core data types are additive, but wiring them into execution touches orchestrator configuration and domain cost computation
- implementation can begin independently of Story A, but the flagship scenario should integrate both before closure

Acceptance criteria:

- missing exogenous years fail before orchestration begins
- at least one flagship domain consumes scenario-specific exogenous inputs
- scenario comparison supports different exogenous paths
- docs, demos, and tests cover interpolation, coverage, and year-slice lookup

#### Integration Point

After both stories are complete, domain cost computation functions (e.g., vehicle cost, heating cost) can be refactored to:

```python
cost_matrix = compute_domain_costs(
    population,                        # who the households are
    alternatives,                      # what they can choose
    exogenous_context.get_year_slice(year),  # energy prices, carbon tax, tech costs
    domain_config,                     # domain-specific cost logic
)
```

This integration is a natural follow-up once both stories land in the flagship domain path.

#### Why Not the Other Paths

- **Bottom-up (types first):** 5 steps, shim layer rot risk, types divorced from behavior
- **Vertical slice:** 3 steps is acceptable, but splits the taste parameter concept across two PRs (discrete_choice then calibration) when they are one conceptual change
- **Parallel tracks:** Designed for multi-developer context; adds merge complexity for a solo developer

---

## 8. Recommended Delivery Sequence

### Phase 1: Current Implementation Phase

Build:

- support for directly usable open structural data
- support for exogenous inputs
- support for calibration targets
- basic governance metadata and provenance
- trust labels in UI/API or serialized outputs
- public synthetic dataset ingestion and comparison workflows
- the `TasteParameters` / `ExogenousContext` refactor needed by the flagship domain

Do not yet claim:

- publication-grade synthetic evidence
- native internal synthetic generation
- restricted-data integration

### Phase 2: Synthetic Exploration

Build:

- broader synthetic dataset ingestion
- stronger exploratory scenario workflows
- richer synthetic versus observed comparison views
- validation dossiers for selected synthetic assets

### Phase 3: Native Synthetic Pipeline

Build:

- internal synthetic population generation
- reproducibility exports
- validation and risk reporting
- stronger trust-status certification rules

### Phase 4: Restricted-Data Connectors (Deferred)

Build only after current phase is stable:

- user-managed access connectors
- provenance and rights recording for restricted assets
- source-specific ingestion contracts
- explicit operating model for where restricted computation runs

---

## 9. Tool Requirements

### 9.1 Required Product Capabilities

The tool should implement:

- dataset classification by origin, access mode, and trust status
- distinction between structural, exogenous, calibration, and governance data
- provenance capture for every source and derived output
- explicit trust labels in APIs and UI
- validation tracking for synthetic outputs
- scenario management across multiple data classes

### 9.2 Non-Negotiable Rules

- Synthetic data must never be presented as equivalent to observed official microdata without validation status.
- Current-phase implementation supports open official data and synthetic data only; restricted-data connectors are deferred.
- Governance metadata must be stored and surfaced, not treated as documentation outside the product.
- Calibration targets and validation benchmarks must remain distinct.
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

It should implement a **trust-governed open + synthetic policy lab** with:

- a broad evidence taxonomy
- explicit classification by origin, access mode, and trust status
- a strict distinction between official and synthetic data in the current phase
- a validation and governance control plane
- a phased delivery path through seven concrete workstreams

Restricted-data support remains deferred until after the current implementation phase is complete and stable.

This is the most defensible path technically, institutionally, and product-wise.
