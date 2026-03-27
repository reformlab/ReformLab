# Evidence Source Matrix v1 (2026-03-27)

**Version:** 1.0.0
**Status:** current-phase
**Scope:** open official + synthetic data (restricted deferred)

## Current-Phase Supported Datasets

This matrix documents all datasets referenced by docs, demos, and the flagship workflow in the current phase. It excludes future-phase reserved data sources (synthetic-internal, restricted, deferred-user-connector).

### Structural Data

| asset_id | name | provider | description | data_class | origin | access_mode | default_trust_status | license | redistribution_allowed | years | direct_usability | known_limitations |
|----------|------|----------|-------------|------------|--------|-------------|---------------------|---------|----------------------|-------|-----------------|-------------------|
| fr-synthetic-2024 | French Synthetic Population 2024 | ReformLab | 100k synthetic households for France (demo/exploratory) | structural | synthetic-public | bundled | exploratory | CC-BY-4.0 | true | 2024 | true | Not calibrated against official marginals |
| insee-fideli-2021 | Fidéli (Données de cadrage) | INSEE | French demographic data sources (administrative files) | structural | open-official | fetched | production-safe | Open License | true | 2021 | true | Access requires registration on INSEE website |
| eurostat-silc-2022 | EU-SILC Survey Data | Eurostat | European Union Statistics on Income and Living Conditions | structural | open-official | fetched | production-safe | CC-BY-4.0 | true | 2022 | false | Microdata access requires application |

### Exogenous Data

| asset_id | name | provider | description | data_class | origin | access_mode | default_trust_status | license | redistribution_allowed | years | direct_usability | known_limitations |
|----------|------|----------|-------------|------------|--------|-------------|---------------------|---------|----------------------|-------|-----------------|-------------------|
| energy-price-elec-fr | Electricity Prices France | Eurostat | Monthly electricity prices by consumer category (NACE) | exogenous | open-official | fetched | production-safe | CC-BY-4.0 | true | 2020-2024 | true | Monthly aggregation required for annual models |
| energy-price-gas-fr | Natural Gas Prices France | Eurostat | Monthly natural gas prices by consumer category | exogenous | open-official | fetched | production-safe | CC-BY-4.0 | true | 2020-2024 | true | Price volatility high; quarterly averaging recommended |
| ademe-carbon-factors-2024 | Base Carbone® ADEME | ADEME | Emission factors for carbon footprint assessment | exogenous | open-official | fetched | production-safe | Open License | true | 2024 | true | Factors updated annually; version tracking required |
| carbon-tax-rate-fr | Carbon Tax Rates France | Government | Official carbon tax rates by fuel type and year | exogenous | open-official | bundled | production-safe | CC-BY-4.0 | true | 2020-2030 | true | Future years projected; subject to policy change |

### Calibration Data

| asset_id | name | provider | description | data_class | origin | access_mode | default_trust_status | license | redistribution_allowed | years | direct_usability | known_limitations |
|----------|------|----------|-------------|------------|--------|-------------|---------------------|---------|----------------------|-------|-----------------|-------------------|
| ev-adoption-fr | EV Adoption Rates France | ADEME | Historical electric vehicle market share by year | calibration | open-official | fetched | production-safe | Open License | true | 2010-2023 | true | Regional coverage varies; national aggregates only |
| household-energy-consumption | Household Energy Consumption | INSEE | Average household energy consumption by decile | calibration | open-official | fetched | production-safe | Open License | true | 2019-2022 | true | Heating degree day normalization required |
| income-distribution-fr | Income Distribution France | INSEE | Disposable income distribution by decile | calibration | open-official | fetched | production-safe | Open License | true | 2021 | true | Pre-tax/post-tax distinction requires careful handling |

### Validation Data

| asset_id | name | provider | description | data_class | origin | access_mode | default_trust_status | license | redistribution_allowed | years | direct_usability | known_limitations |
|----------|------|----------|-------------|------------|--------|-------------|---------------------|---------|----------------------|-------|-----------------|-------------------|
| household-survey-fr | French Household Survey | INSEE | Observed household consumption for validation | validation | open-official | fetched | production-safe | Open License | true | 2021 | true | Access requires registration; sample size limited |
| transport-mode-shares | Transport Mode Shares | Ministry of Transport | Modal split statistics for passenger transport | validation | open-official | fetched | production-safe | Open License | true | 2019-2023 | true | Urban/rural aggregation differs from NUTS |

## Future-Phase Reserved Data Sources

The following data classes and access modes are reserved for future phases and are not yet supported:

| Category | Reserved Value | Description | Future Use Case |
|----------|----------------|-------------|-----------------|
| Origin | `synthetic-internal` | Internally generated synthetic assets | Proprietary synthetic populations for commercial scenarios |
| Origin | `restricted` | Access-controlled data | Secure data integration with user-provided connectors |
| Access Mode | `deferred-user-connector` | User-provided data connector plugins | Enterprise data warehouse integration, proprietary data sources |

## Asset ID Naming Convention

All asset IDs follow the pattern: `{provider}-{dataset}-{version}`

- **provider**: Organization or source identifier (e.g., `insee`, `eurostat`, `ademe`, `reformlab`)
- **dataset**: Short descriptive name in kebab-case (e.g., `fideli`, `ev-adoption`, `energy-price`)
- **version**: Year or version identifier (e.g., `2021`, `2024-Q1`, `v2`)

Examples:
- `insee-fideli-2021`
- `eurostat-energy-prices-2024`
- `reformlab-fr-synthetic-2024`

## Data Class Definitions

| Data Class | Role | Example Questions |
|------------|------|-------------------|
| **structural** | Define who or what is modeled | "Who are the households, people, firms, and places?" |
| **exogenous** | Provide observed/projected context inputs | "What are energy prices, carbon tax rates, technology costs this year?" |
| **calibration** | Fit the model to observed reality | "Does the model reproduce observed consumption patterns?" |
| **validation** | Test the model against independent observations | "Can we predict actual policy outcomes from historical data?" |

## Trust Status Definitions

| Trust Status | Decision Support | Public Claims | Description |
|--------------|------------------|---------------|-------------|
| **production-safe** | Yes | Yes | Validated against official statistics; suitable for policy decisions |
| **exploratory** | No | No | Suitable for exploration and prototyping; not validated for decisions |
| **demo-only** | No | No | Example data for demonstrations; not representative of reality |
| **validation-pending** | No | No | Requires validation dossier before production use |
| **not-for-public-inference** | No | No | Internal use only; cannot be used for external claims |

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-27 | Initial matrix for Story 21.1 (current-phase datasets) |

## References

- [synthetic-data-decision-document-2026-03-23.md](/Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/synthetic-data-decision-document-2026-03-23.md)
- [epic-21-trust-governed-open-synthetic-evidence-foundation.md](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/epic-21-trust-governed-open-synthetic-evidence-foundation.md)
