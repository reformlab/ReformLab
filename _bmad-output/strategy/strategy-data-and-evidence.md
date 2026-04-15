# Data & Evidence Strategy

**Date:** 2026-03-23 | **Status:** Active (current-phase scope implemented in Epic 21)

## Core Decision

ReformLab is a **trust-governed open + synthetic policy lab**: open official data as the base, synthetic data as a labelled augmentation layer, validation/provenance/governance as first-class features.

## Data Taxonomy

| Data Class | Role | Example |
|------------|------|---------|
| **Structural** | Define who/what is modeled | Synthetic population, INSEE Fidéli, EU-SILC |
| **Exogenous** | Observed/projected context inputs | Energy prices, carbon tax rates, emission factors |
| **Calibration** | Fit model to observed reality | EV adoption rates, household energy consumption |
| **Validation** | Test model against independent data | Household survey, transport mode shares |

## Trust Status Levels

| Status | Decision support | Public claims |
|--------|-----------------|---------------|
| `production-safe` | Yes | Yes |
| `exploratory` | No | No |
| `demo-only` | No | No |
| `validation-pending` | No | No |

## Current-Phase Dataset Catalog

### Structural
| ID | Provider | Access | Trust | Notes |
|----|----------|--------|-------|-------|
| `fr-synthetic-2024` | ReformLab | bundled | exploratory | 100k synthetic households, not calibrated |
| `insee-fideli-2021` | INSEE | fetched | production-safe | Registration required |
| `eurostat-silc-2022` | Eurostat | fetched | production-safe | Microdata requires application |

### Exogenous
| ID | Provider | Access | Years |
|----|----------|--------|-------|
| `energy-price-elec-fr` | Eurostat | fetched | 2020–2024 |
| `energy-price-gas-fr` | Eurostat | fetched | 2020–2024 |
| `ademe-carbon-factors-2024` | ADEME | fetched | 2024 |
| `carbon-tax-rate-fr` | Government | bundled | 2020–2030 |

### Calibration
| ID | Provider | Access | Years |
|----|----------|--------|-------|
| `ev-adoption-fr` | ADEME | fetched | 2010–2023 |
| `household-energy-consumption` | INSEE | fetched | 2019–2022 |
| `income-distribution-fr` | INSEE | fetched | 2021 |

### Validation
| ID | Provider | Access | Years |
|----|----------|--------|-------|
| `household-survey-fr` | INSEE | fetched | 2021 |
| `transport-mode-shares` | Ministry of Transport | fetched | 2019–2023 |

## Future-Phase Scope (Deferred)

| Capability | Description | When |
|------------|-------------|------|
| `synthetic-internal` origin | Proprietary synthetic populations | When commercial scenarios demand it |
| `restricted` origin | Access-controlled institutional data | When legal/operational infrastructure exists |
| `deferred-user-connector` | Enterprise data warehouse plugins | When enterprise customers need it |
| User-managed credentials | Secure credential flows for restricted sources | Deferred with restricted origin |

## Asset ID Convention

Pattern: `{provider}-{dataset}-{version}` (e.g., `insee-fideli-2021`, `ademe-carbon-factors-2024`)
