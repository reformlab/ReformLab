---
stepsCompleted: [1, 2]
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
workflowType: 'research'
lastStep: 2
research_type: 'domain'
research_topic: 'French Open Data Sources for Environmental Policy Microsimulation'
research_goals: 'Catalog freely available French datasets (households, dwellings, energy equipment, transport, emissions), assess connectability to OpenFisca framework, identify gaps'
user_name: 'Lucas'
date: '2026-02-25'
web_research_enabled: true
source_verification: true
---

# Research Report: French Open Data for Environmental Policy Microsimulation

**Date:** 2026-02-25
**Author:** Lucas
**Research Type:** Domain

---

## Research Overview

This report catalogs publicly available French datasets relevant to building an environmental policy microsimulation platform on top of OpenFisca. Each dataset is assessed for: currentness (latest vintage), format, granularity, key variables, access method, and connectability to the ReformLab framework.

**Methodology:** All datasets verified via web search against their official source portals (INSEE, ADEME, SDES, data.gouv.fr, Enedis, GRDF, BDNB) as of February 2026.

---

## 1. Household & Income Data

### 1.1 Filosofi (Fichier Localisé Social et Fiscal)

| Attribute | Detail |
|---|---|
| **Producer** | INSEE |
| **Latest vintage** | **2021** (2022 vintage cancelled due to source quality issues) |
| **Granularity** | Commune, EPCI, IRIS, carroyage 200m |
| **Key variables** | Disposable income, declared income, poverty rate, median income, Gini, income deciles, income by age/household type |
| **Format** | XLSX, CSV on insee.fr and data.gouv.fr |
| **Access** | Fully open, free download |
| **URL** | [insee.fr/Filosofi](https://www.insee.fr/fr/metadonnees/source/serie/s1172) / [data.gouv.fr](https://www.data.gouv.fr/datasets/revenus-et-pauvrete-des-menages-aux-niveaux-national-et-local-revenus-localises-sociaux-et-fiscaux) |
| **Update frequency** | Annual (but 2022 skipped) |
| **Confidence** | HIGH — reference source for local income data |

**Framework connection:** Filosofi provides income distribution at IRIS/commune level. Can calibrate synthetic population income distributions. Not individual-level (aggregated indicators only in open data). For individual-level, ERFS is needed (restricted access via CASD).

### 1.2 ERFS (Enquete Revenus Fiscaux et Sociaux)

| Attribute | Detail |
|---|---|
| **Producer** | INSEE |
| **Latest vintage** | 2022 (published 2024) |
| **Granularity** | Individual / household (sample ~50,000 households) |
| **Key variables** | Pre- and post-redistribution income, social transfers, taxes, household composition, employment status, housing type |
| **Format** | HDF5 via openfisca-france-data pipeline; SAS/CSV via CASD |
| **Access** | **Restricted** — microdata via CASD only; aggregate tables on insee.fr are open |
| **URL** | [insee.fr/ERFS](https://www.insee.fr/fr/metadonnees/source/serie/s1231) / [CASD](https://www.casd.eu/en/source/tax-and-social-incomes-survey/) |
| **Confidence** | HIGH — national reference for income microsimulation |

**Framework connection:** This is the **primary input for OpenFisca-France** via [openfisca-france-data](https://github.com/openfisca/openfisca-france-data). The pipeline transforms ERFS into HDF5 with Individu/Menage entities. **Access restriction is the main barrier** — requires CASD approval.

### 1.3 Enquete Budget de Famille (EBF)

| Attribute | Detail |
|---|---|
| **Producer** | INSEE |
| **Latest vintage** | **2017** (published 2020); new edition collecting Jan 2026 - Mar 2026 |
| **Granularity** | Individual / household (~29,000 households) |
| **Key variables** | ~900 budget items: energy expenditure, transport, food, housing costs, income |
| **Format** | SAS/CSV via CASD; aggregate tables open on insee.fr |
| **Access** | **Restricted** microdata (CASD); aggregate tables open |
| **URL** | [insee.fr/EBF](https://www.insee.fr/fr/metadonnees/source/serie/s1194) |
| **Update frequency** | Every 5 years |
| **Confidence** | HIGH for consumption patterns; 2017 vintage is aging |

**Framework connection:** Critical for calibrating household energy expenditure by income decile. The 2017 data can be used for energy budget shares. New 2026 edition results expected ~2028.

---

## 2. Dwelling & Housing Data

### 2.1 BDNB (Base de Donnees Nationale des Batiments)

| Attribute | Detail |
|---|---|
| **Producer** | CSTB (Centre Scientifique et Technique du Batiment) |
| **Latest vintage** | **Millesime 2025-07.a** (November 2025); previous: 2024-10.a (February 2025) |
| **Granularity** | **Individual building** (32 million buildings) |
| **Format** | CSV, GeoPackage, SQL — departmental or national extracts |
| **URL** | [bdnb.io](https://bdnb.io/) / [data.gouv.fr/BDNB](https://www.data.gouv.fr/datasets/base-de-donnees-nationale-des-batiments) / [GitLab](https://gitlab.com/BDNB/base_nationale_batiment) |
| **Update frequency** | ~2 millesimes per year |

**IMPORTANT: The BDNB has 3 access tiers with very different content:**

| Tier | Access | Variables | Key content |
|---|---|---|---|
| **BDNB Open** | Free download on data.gouv.fr | ~170 variables | Building morphology (2.5D volumes, surfaces, heights, face topology), addresses, parcelle IDs, **raw ADEME DPE records** (linked to buildings where a DPE exists), building usage classification, administrative data, heat network connection indicators |
| **BDNB Expert** | Commercial / research partnership with CSTB | 400+ variables | Everything in Open + **simulated DPE for all buildings** (incl. those without actual DPE), **`batiment_groupe_synthese_systeme_energetique`** (heating mode, heating energy, hot water energy predictions), wall insulation estimates, window performance, energy consumption estimates with confidence intervals, carbon footprint estimates, green value indicator |
| **BDNB Ayants-droits** | Government bodies only | 400+ variables + cadastral | Everything in Expert + cadastral tax data from DGFiP |

**Critical nuance:** Only ~15-20% of buildings have an actual ADEME DPE. The BDNB Open version includes these raw DPEs (linked to buildings), but the **predicted/simulated DPE and energy system data** that covers the remaining ~80% of buildings is **Expert-only (restricted)**.

**Framework connection:** BDNB Open is useful for building morphology, parcelle linkage, and accessing the subset of buildings with actual DPE data. However, the energy systems synthesis tables (`synthese_systeme_energetique`) with heating mode/energy for all buildings are **not in the open version**. For full energy equipment coverage, use **DPE ADEME directly** (Section 2.2) for the ~6M dwellings with DPE, and **Census data** (Section 2.4) for universal but coarser heating mode/fuel coverage.

### 2.2 DPE (Diagnostic de Performance Energetique) — ADEME Open Data

| Attribute | Detail |
|---|---|
| **Producer** | ADEME |
| **Latest vintage** | Continuously updated (post-July 2021 reform DPEs); **6.1M+ existing housing DPEs, 660K+ new housing DPEs** |
| **Granularity** | **Individual dwelling** |
| **Key variables** | Energy class (A-G), GHG class, primary energy consumption (kWh/m2/yr), **heating system type, heating energy, hot water system, hot water energy, cooling system, ventilation type**, wall/roof/floor insulation levels, surface, construction year, altitude, climate zone |
| **Format** | CSV (10.5 GB for existing housing); API; filtered Excel exports |
| **Access** | **Fully open** on data.ademe.fr |
| **URL** | [DPE Existing Housing](https://data.ademe.fr/datasets/dpe03existant) / [DPE New Housing](https://data.ademe.fr/datasets/dpe02neuf) / [Observatoire DPE](https://observatoire-dpe-audit.ademe.fr/) |
| **Update frequency** | Continuous (new DPEs added daily) |
| **Confidence** | HIGH — official regulatory data; but not all dwellings have a DPE |

**Framework connection:** **The richest open dataset for energy equipment at dwelling level.** Each DPE record contains: `type_installation_chauffage`, `type_generateur_chauffage`, `type_energie_chauffage`, `type_installation_ecs` (hot water), `type_energie_ecs`, `presence_climatisation`, `type_ventilation`. Can be joined to BDNB via DPE identifiers. Processing pipeline exists: [etalab/de-dpe-processing](https://github.com/etalab/de-dpe-processing).

### 2.3 ENL (Enquete Nationale Logement)

| Attribute | Detail |
|---|---|
| **Producer** | INSEE / SDES |
| **Latest vintage** | **2023-2024** (collected Sep 2023 - Jul 2024; results published Jan 21, 2026) |
| **Granularity** | Individual / household (representative sample) |
| **Key variables** | Tenure status, housing type, surface, **heating equipment, energy type, insulation, hot water equipment**, housing expenditure, overcrowding, comfort indicators |
| **Format** | Aggregate tables open (XLSX/CSV); microdata via CASD |
| **Access** | **Mixed** — aggregate tables open on insee.fr; microdata restricted (CASD) |
| **URL** | [INSEE/ENL](https://www.insee.fr/fr/metadonnees/source/serie/s1004) / [SDES/ENL](https://www.statistiques.developpement-durable.gouv.fr/enquete-logement-enl) |
| **Confidence** | HIGH — the reference survey for housing conditions including equipment |

**Framework connection:** The ENL is the most comprehensive housing survey including energy equipment questions. The 2023-2024 edition is the freshest data on household heating/cooling/hot water equipment in France. Aggregate tables can calibrate equipment distributions by housing type, tenure, and income. Microdata (CASD) would allow direct linkage.

### 2.4 Census — Housing Database (Recensement)

| Attribute | Detail |
|---|---|
| **Producer** | INSEE |
| **Latest vintage** | **2022 census** (published 2025); IRIS-level bases updated Jan 2026 |
| **Granularity** | Commune, IRIS; detailed files at individual dwelling level |
| **Key variables** | Housing type, number of rooms, construction period, tenure, **heating mode** (collective/individual/none), **heating fuel** (electricity, gas, fuel oil, wood, other) |
| **Format** | XLSX, CSV |
| **Access** | **Fully open** on insee.fr and data.gouv.fr |
| **URL** | [INSEE Census Housing](https://www.insee.fr/fr/statistiques/8270440) / [data.gouv.fr](https://www.data.gouv.fr/datasets/bases-de-donnees-et-fichiers-details-du-recensement-de-la-population) |
| **Confidence** | HIGH — universal coverage |

**Framework connection:** Census provides universal coverage of heating mode and fuel type at IRIS level. Less detailed than DPE (no specific equipment model) but covers all dwellings. Excellent for calibrating aggregate heating fuel shares by territory.

### 2.5 Fideli (Fichier Demographique sur les Logements et les Individus)

| Attribute | Detail |
|---|---|
| **Producer** | INSEE (from tax data) |
| **Latest vintage** | 2022 |
| **Granularity** | Individual dwelling / individual person |
| **Key variables** | Housing tax status, occupancy status, dwelling type, location, household composition |
| **Format** | Statistical tables open; microdata restricted (CASD) |
| **Access** | **Restricted** microdata (CASD); derived aggregates used in census/Filosofi |
| **URL** | [INSEE/Fideli](https://www.insee.fr/fr/information/3897375) |
| **Confidence** | HIGH — administrative exhaustive source |

**Framework connection:** Fideli is used internally by INSEE to build Filosofi and census products. Direct access via CASD only. For open-data work, use the census and Filosofi outputs instead.

**Note — Resil:** INSEE is building a new statistical register (Resil) combining Fideli with other sources, expected operational early 2026. This may open new data pathways.

---

## 3. Energy Equipment (Heating, Cooling, Hot Water, Insulation, Renewables)

### 3.1 DPE Equipment Variables (detailed)

The DPE dataset (Section 2.2) is the **primary open source for dwelling-level energy equipment**. Key equipment columns per DPE record:

| Equipment Category | DPE Variables |
|---|---|
| **Heating** | `type_installation_chauffage` (individual/collective), `type_generateur_chauffage` (boiler, heat pump, electric radiator, wood stove...), `type_energie_chauffage` (gas, electricity, fuel oil, wood, district heat...) |
| **Hot Water** | `type_installation_ecs`, `type_generateur_ecs`, `type_energie_ecs` |
| **Cooling** | `presence_climatisation` (yes/no), system details when present |
| **Ventilation** | `type_ventilation` (natural, single-flow, double-flow VMC) |
| **Insulation** | Wall U-value, roof U-value, floor U-value, window type/glazing, insulation year |
| **Renewables** | Solar thermal, photovoltaic presence in some records |

**Coverage:** 6.1M existing dwellings + 660K new. Not all 30M+ dwellings have a DPE.

### 3.2 BDNB Energy Systems Tables

The BDNB aggregates DPE data and other sources at building group level:

- `batiment_groupe_synthese_systeme_energetique`: Heating mode, heating energy, hot water energy per building group
- `dpe_logement`: Individual DPE records with ~100 technical attributes
- DPE processing extracts: `td011_installation_chauffage`, `td012_generateur_chauffage` — generator labels, energy types, classification by primary/secondary/tertiary

### 3.3 ONRE — Housing Stock by Energy Class

| Attribute | Detail |
|---|---|
| **Producer** | SDES / ONRE (Observatoire National de la Renovation Energetique) |
| **Latest vintage** | **January 1, 2025** (published Nov 2025) |
| **Granularity** | National, regional, departmental |
| **Key variables** | Number of dwellings by DPE class (A-G), passoires energetiques count (3.9M at Jan 2025 = 12.7% of stock) |
| **Format** | XLSX, PDF |
| **Access** | **Fully open** |
| **URL** | [SDES/ONRE Housing Stock 2025](https://www.statistiques.developpement-durable.gouv.fr/le-parc-de-logements-par-classe-de-performance-energetique-au-1er-janvier-2025) / [Renovation Tracking Dashboard](https://www.statistiques.developpement-durable.gouv.fr/tableau-de-suivi-de-la-renovation-energetique-dans-le-secteur-residentiel) |
| **Confidence** | HIGH — official government estimate |

**Framework connection:** Calibration target for vintage tracking. Your model's DPE class distribution should match ONRE figures. The renovation tracking dashboard provides annual renovation counts by type of work.

### 3.4 MaPrimeRenov / ANAH Data

| Attribute | Detail |
|---|---|
| **Producer** | ANAH (Agence Nationale de l'Habitat) |
| **Latest vintage** | **Q4 2024** reporting (published Mar 2025); annual 2025 report (Feb 2026) |
| **Granularity** | National; some departmental breakdowns |
| **Key variables** | Number of renovations, types of work (insulation, heating replacement, window replacement), aid amounts, income categories of beneficiaries, DPE class gain |
| **Format** | PDF reports; some Excel annexes |
| **Access** | Reports open on anah.gouv.fr; **no structured open dataset** for individual operations |
| **URL** | [ANAH/MaPrimeRenov](https://www.anah.gouv.fr/anatheque/bilan-maprimerenov-S12024) |
| **Confidence** | MEDIUM — aggregate reports, not granular open data |

**Framework connection:** Useful for calibrating renovation rates and equipment transition speeds (e.g., how many fuel oil boilers replaced by heat pumps per year). No individual-operation open data — you'd need to use aggregate rates.

### 3.5 CEE (Certificats d'Economies d'Energie)

| Attribute | Detail |
|---|---|
| **Producer** | Ministry of Ecology |
| **Latest vintage** | Operations invoiced 2015-2024 (engaged 2015-2022) on data.gouv.fr |
| **Granularity** | EPCI level; by operation type |
| **Key variables** | Standardized operation type (BAR-TH-xxx for heating, BAR-EN-xxx for envelope), energy savings (kWhcumac), number of operations |
| **Format** | CSV on data.gouv.fr |
| **Access** | **Partially open** — anonymized below 3 units threshold |
| **URL** | [data.gouv.fr/CEE-EPCI](https://www.data.gouv.fr/datasets/certificats-deconomie-denergie-epci) |
| **Confidence** | MEDIUM — good for operation counts; anonymization gaps at fine granularity |

**Framework connection:** CEE data gives territorial renovation activity by standardized operation type (e.g., BAR-TH-171 = heat pump installation). Can feed vintage transition rates for heating equipment at EPCI level.

### 3.6 TREMI/TRELO (Enquete Travaux de Renovation Energetique)

| Attribute | Detail |
|---|---|
| **Producer** | SDES / ADEME |
| **Latest vintage** | **TRELO 2023** (collection Sep 2023 - Feb 2024; extends TREMI to collective housing) |
| **Granularity** | Individual household (sample) |
| **Key variables** | Type of renovation work, cost, motivations, barriers, before/after equipment, income, housing type |
| **Format** | Restricted microdata (CASD); aggregate results on SDES website |
| **Access** | **Restricted** microdata; aggregate tables open |
| **URL** | [SDES/TREMI](https://www.statistiques.developpement-durable.gouv.fr/enquete-sur-les-travaux-de-renovation-energetique-dans-les-maisons-individuelles-tremi) / [SDES/TRELO](https://www.statistiques.developpement-durable.gouv.fr/enquete-sur-les-travaux-de-renovation-energetique-dans-les-logements-trelo) |
| **Confidence** | HIGH for renovation behavior; restricted access |

**Framework connection:** Key for calibrating renovation decision models and equipment transition probabilities. Aggregate tables provide renovation rates by housing type and income category.

---

## 4. Energy Consumption Data

### 4.1 Enedis Open Data (Electricity)

| Attribute | Detail |
|---|---|
| **Producer** | Enedis |
| **Latest vintage** | **2024** (2011-2024 time series) |
| **Granularity** | IRIS, commune, EPCI, region; by sector (residential, tertiary, industrial, agricultural) |
| **Key variables** | Annual electricity consumption (MWh), number of delivery points, thermal sensitivity (heat-sensitive share), thermosensitivity gradient |
| **Format** | CSV, API (OData) |
| **Access** | **Fully open** |
| **URL** | [Enedis IRIS data](https://data.enedis.fr/explore/dataset/consommation-electrique-par-secteur-dactivite-iris/) / [Enedis commune data](https://data.enedis.fr/explore/dataset/consommation-electrique-par-secteur-dactivite-commune/) |
| **Update frequency** | Annual |
| **Confidence** | HIGH — metered data from grid operator |

**Framework connection:** Residential electricity consumption at IRIS level, with thermal sensitivity indicators. Directly joinable via INSEE commune/IRIS codes. The thermal sensitivity variable is particularly useful — it estimates the heating-related share of electricity consumption.

### 4.2 GRDF Open Data (Gas)

| Attribute | Detail |
|---|---|
| **Producer** | GRDF |
| **Latest vintage** | **2024** (since 2018) |
| **Granularity** | EPCI, commune; by sector and NAF code |
| **Key variables** | Annual gas consumption (MWh), number of delivery points, climate correction indicators |
| **Format** | CSV, API |
| **Access** | **Fully open** |
| **URL** | [GRDF Open Data](https://opendata.grdf.fr/) / [GRDF EPCI consumption](https://opendata.grdf.fr/explore/dataset/consommation-annuelle-de-gaz-par-epci-et-code-naf/) |
| **Update frequency** | Annual |
| **Confidence** | HIGH — metered data from gas grid operator |

**Framework connection:** Gas consumption at commune/EPCI level, joinable via geographic codes. Combined with Enedis data, gives total networked energy consumption per territory. Gap: no fuel oil or wood consumption data from grid operators (delivered fuels).

### 4.3 SDES Energy Balance — Residential by Use

| Attribute | Detail |
|---|---|
| **Producer** | SDES (from CEREN data, calibrated on national energy balance) |
| **Latest vintage** | **2024** (provisional); 2023 final |
| **Granularity** | National |
| **Key variables** | Consumption by use: heating (312 TWh climate-corrected 2023), hot water, cooking, specific electricity, cooling. By energy: electricity (34%), renewables (29%), gas (25%), oil (9%) |
| **Format** | XLSX, PDF, online interactive publication |
| **Access** | **Fully open** |
| **URL** | [SDES Residential Energy by Use](https://www.statistiques.developpement-durable.gouv.fr/consommation-denergie-par-usage-du-residentiel) / [Energy Balance 2024](https://www.statistiques.developpement-durable.gouv.fr/bilan-energetique-de-la-france-en-2024-synthese) |
| **Update frequency** | Annual |
| **Confidence** | HIGH — official national energy statistics |

**Framework connection:** National calibration targets for aggregate energy consumption by use. Your microsimulation's total heating/hot water/cooking consumption should align with SDES totals. Time series since 1990 available for trend validation.

---

## 5. Transport & Vehicle Fleet

### 5.1 SDES Vehicle Fleet (Parc Automobile)

| Attribute | Detail |
|---|---|
| **Producer** | SDES (from SIV registry) |
| **Latest vintage** | **January 1, 2025** (39.7M cars) |
| **Granularity** | National, regional, departmental, **communal** |
| **Key variables** | Number of vehicles by type (car, LCV, truck), by fuel type (gasoline, diesel, electric, hybrid, LPG), by age, by Crit'Air class |
| **Format** | CSV, XLSX; API (via Dido platform since May 2025) |
| **Access** | **Fully open** |
| **URL** | [SDES Fleet 2025](https://www.statistiques.developpement-durable.gouv.fr/donnees-sur-le-parc-automobile-francais-au-1er-janvier-2025) / [SDES Fleet 2024](https://www.statistiques.developpement-durable.gouv.fr/donnees-sur-le-parc-automobile-francais-au-1er-janvier-2024) |
| **Update frequency** | Annual |
| **Confidence** | HIGH — administrative registration data |

**Framework connection:** Communal vehicle fleet composition for vintage tracking of vehicles. Fuel type and age distributions feed directly into carbon tax impact modeling. Joinable via commune codes. The Dido API allows automated data retrieval.

### 5.2 SDES New Vehicle Registrations

| Attribute | Detail |
|---|---|
| **Producer** | SDES |
| **Latest vintage** | **2024** (monthly data) |
| **Granularity** | National, regional, departmental |
| **Key variables** | New registrations by fuel type, CO2 emissions class, vehicle segment |
| **Format** | XLSX, CSV |
| **Access** | **Fully open** |
| **URL** | [SDES Registrations 2024](https://www.statistiques.developpement-durable.gouv.fr/donnees-2024-sur-les-immatriculations-des-vehicules) |
| **Confidence** | HIGH |

**Framework connection:** Fleet renewal rates by fuel type for vintage transition modeling. How fast are diesel/gasoline being replaced by electric/hybrid.

---

## 6. Emission Factors & Environmental Reference Data

### 6.1 Base Carbone / Base Empreinte (ADEME)

| Attribute | Detail |
|---|---|
| **Producer** | ADEME |
| **Latest vintage** | **V23.6** (July 2025) |
| **Granularity** | Per unit (kgCO2e/kWh, kgCO2e/L, kgCO2e/km, etc.) |
| **Key variables** | Emission factors for all energy carriers (electricity, gas, fuel oil, wood, district heat), transport modes, materials, food, waste |
| **Format** | CSV, API |
| **Access** | **Fully open** |
| **URL** | [ADEME Base Carbone](https://data.ademe.fr/datasets/base-carboner) / [API Base Carbone](https://www.data.gouv.fr/dataservices/api-base-carbone) / [Base Empreinte](https://base-empreinte.ademe.fr/) |
| **Update frequency** | ~2x per year |
| **Confidence** | HIGH — official French emission factors |

**Framework connection:** **Essential for converting energy consumption to CO2 emissions.** The API allows programmatic access. Emission factors for electricity, gas, fuel oil, wood, etc. are directly needed for carbon tax calculations. Version-pinned factors can be stored in scenario manifests for reproducibility.

---

## 7. Geographic & Administrative Reference Data

### 7.1 COG (Code Officiel Geographique)

| Attribute | Detail |
|---|---|
| **Producer** | INSEE |
| **Latest vintage** | **January 1, 2025** |
| **Granularity** | Commune, canton, arrondissement, department, region |
| **Key variables** | Commune codes, labels, departmental/regional membership, commune mergers history |
| **Format** | CSV (UTF-8) |
| **Access** | **Fully open** |
| **URL** | [INSEE COG 2025](https://www.insee.fr/fr/information/8377162) / [data.gouv.fr/COG](https://www.data.gouv.fr/datasets/code-officiel-geographique-cog) |
| **Update frequency** | Annual |
| **Confidence** | HIGH |

### 7.2 IRIS Geographic Membership Table

| Attribute | Detail |
|---|---|
| **Producer** | INSEE / IGN |
| **Latest vintage** | **2024 edition** |
| **Granularity** | IRIS -> commune -> EPCI -> department -> region |
| **Key variables** | IRIS code, commune code, all higher geographic level codes (employment zone, urban unit, city attraction area) |
| **Format** | CSV, XLSX |
| **Access** | **Fully open** |
| **URL** | [INSEE IRIS Table](https://www.insee.fr/fr/information/7708995) / [Contours IRIS (IGN)](https://geoservices.ign.fr/irisge) |
| **Confidence** | HIGH |

**Framework connection:** The COG and IRIS tables are the **geographic backbone** linking all datasets. Every dataset in this report uses INSEE commune codes. The IRIS table allows drilling down to sub-municipal level where data supports it. Must be versioned yearly due to commune mergers.

---

## 8. OpenFisca Data Pipeline Compatibility

### 8.1 Existing Pipeline: openfisca-france-data

| Component | Detail |
|---|---|
| **Repository** | [openfisca-france-data](https://github.com/openfisca/openfisca-france-data) |
| **Input sources** | ERFS, ERFS-FPR, FELIN (all restricted/CASD) |
| **Pipeline** | Raw survey files (SAS/CSV/Parquet) -> openfisca-survey-manager -> HDF5 (Individu + Menage entities) |
| **Output** | HDF5 file with data organized by OpenFisca Individu and Menage entities |
| **Latest PyPI** | v3.7.10 |

### 8.2 What You Need to Build

The existing pipeline only handles ERFS (restricted data). For an **open-data-first** approach, your ReformLab framework needs a **parallel ingestion pathway** for:

1. **Synthetic population generator** — build household/individual records from open census + Filosofi aggregates (no existing open-source tool does this fully for France)
2. **Building/equipment enrichment** — join BDNB or DPE data to synthetic households (matching by commune/IRIS, housing type, construction period)
3. **Vehicle fleet assignment** — assign vehicle characteristics from SDES communal fleet data to synthetic households (probabilistic matching by commune, household type)
4. **Emission factor lookup** — connect Base Carbone factors to energy consumption calculations
5. **Energy consumption estimation** — calibrate using Enedis/GRDF territorial data and SDES national totals

---

## 9. Dataset Connection Map

```
                    ┌─────────────────────┐
                    │  COG / IRIS Tables   │ Geographic backbone
                    │  (commune codes)     │
                    └──────────┬──────────┘
                               │ joins all datasets
            ┌──────────────────┼──────────────────┐
            │                  │                  │
    ┌───────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐
    │  Filosofi     │  │  Census      │  │  Enedis/GRDF │
    │  (income by   │  │  (housing +  │  │  (energy     │
    │   IRIS)       │  │  heating by  │  │  consumption │
    │               │  │  IRIS)       │  │  by IRIS)    │
    └───────┬───────┘  └──────┬───────┘  └──────┬───────┘
            │                  │                  │
            └──────────┬───────┘                  │
                       │ calibrates               │ calibrates
              ┌────────▼─────────┐                │
              │ Synthetic        │                 │
              │ Population       │◄────────────────┘
              │ (your generator) │
              └────────┬─────────┘
                       │ enriched by
            ┌──────────┼──────────────┐
            │          │              │
    ┌───────▼──────┐ ┌─▼────────┐ ┌──▼──────────┐
    │  BDNB / DPE  │ │  SDES    │ │  Base       │
    │  (equipment  │ │  Vehicle │ │  Carbone    │
    │  per bldg)   │ │  Fleet   │ │  (emission  │
    │              │ │  (per    │ │  factors)   │
    │              │ │  commune)│ │             │
    └──────────────┘ └──────────┘ └─────────────┘
            │                              │
            └──────────┬───────────────────┘
                       │ feeds
              ┌────────▼─────────┐
              │  OpenFisca       │
              │  Computation     │
              │  (tax-benefit)   │
              └────────┬─────────┘
                       │ outputs to
              ┌────────▼─────────┐
              │  ReformLab       │
              │  Orchestrator    │
              │  (your product)  │
              └──────────────────┘
```

### Key Join Fields

| Dataset A | Dataset B | Join Key | Quality |
|---|---|---|---|
| Filosofi | Census | Commune/IRIS code | Exact |
| Census | Enedis | Commune/IRIS code | Exact |
| Census | GRDF | Commune/EPCI code | Exact |
| Census | SDES Vehicle Fleet | Commune code | Exact |
| BDNB | DPE | DPE identifier (N_DPE) | Exact |
| BDNB | Cadastre | Parcelle ID | Exact |
| BDNB | Census | Commune code + housing type proxy | Probabilistic |
| Synthetic Pop | BDNB/DPE | Commune + housing type + construction period | Probabilistic |
| Synthetic Pop | Vehicle Fleet | Commune + household type | Probabilistic |
| Any energy use | Base Carbone | Energy carrier code | Exact (lookup) |
| All datasets | COG/IRIS | Commune/IRIS code | Exact (reference table) |

---

## 10. Gap Analysis

### Fully Open & Directly Usable

| Need | Dataset | Status |
|---|---|---|
| Dwelling-level equipment (heating, hot water, cooling) | DPE ADEME (open) | **READY** — 6.1M+ dwellings with full equipment detail (~20% of stock) |
| Building morphology + parcelle linkage | BDNB Open | **READY** — 32M buildings, 170 variables |
| Housing stock by energy class | ONRE | **READY** — Jan 2025 vintage |
| Emission factors | Base Carbone V23.6 | **READY** — API available |
| Vehicle fleet by commune | SDES Parc Automobile | **READY** — Jan 2025 vintage |
| Electricity consumption by IRIS | Enedis Open Data | **READY** — 2024 data |
| Gas consumption by commune | GRDF Open Data | **READY** — 2024 data |
| National energy balance by use | SDES | **READY** — 2024 provisional |
| Income by IRIS | Filosofi | **READY** — 2021 (latest available) |
| Housing by IRIS (heating mode/fuel) | Census | **READY** — 2022 census |
| Geographic reference | COG + IRIS tables | **READY** — 2025 |

### Gaps & Workarounds

| Need | Gap | Workaround | Severity |
|---|---|---|---|
| **Individual-level household income** | ERFS restricted (CASD only) | Generate synthetic population from census + Filosofi aggregates | HIGH — core input for microsimulation |
| **Household energy expenditure** | EBF 2017 microdata restricted; no open individual-level data | Use Filosofi income deciles + SDES average shares by decile | HIGH |
| **Dwelling-level fuel oil / wood consumption** | No grid operator data for delivered fuels | Estimate from DPE energy type + SDES national totals + Base Carbone factors | MEDIUM |
| **Renovation transition rates (individual)** | TREMI/TRELO microdata restricted | Use MaPrimeRenov aggregate reports + CEE operation counts | MEDIUM |
| **Household-to-dwelling linkage** | No open join between household surveys and building databases | Probabilistic matching by commune + housing type + construction period + tenure | HIGH — key engineering challenge |
| **DPE coverage** | Only ~20% of housing stock has a DPE | BDNB Expert estimates DPE for all buildings but is **restricted**; for open-data only: build estimation model from DPE + Census + BDNB Open morphology | **HIGH** (upgraded from LOW — BDNB Expert is not open) |
| **Energy systems for all buildings** | `batiment_groupe_synthese_systeme_energetique` is BDNB Expert only (restricted) | Use Census heating mode/fuel (universal) + DPE equipment detail (where available) + statistical imputation | MEDIUM |
| **Cooling equipment detail** | DPE only flags presence/absence | Use ENL survey aggregates for A/C penetration rates by climate zone | LOW |
| **Household vehicle ownership** | Open fleet data is at commune level, not household level | Probabilistic assignment from commune fleet composition + census commuting data | MEDIUM |

### Critical Path for Open-Data-First Strategy

1. **Synthetic population generator** is the #1 engineering task — without individual-level open data, you must synthesize households from census + Filosofi. Consider building on [eqasim-france](https://github.com/eqasim-org/eqasim-france) pipeline architecture.
2. **DPE ADEME is your richest open equipment source** — 6.1M dwellings with full heating/hot water/cooling detail. Use [etalab/de-dpe-processing](https://github.com/etalab/de-dpe-processing) to extract structured equipment data.
3. **BDNB Open** provides building morphology and parcelle linkage, but energy system predictions are Expert-only (restricted). For buildings without DPE, you'll need your own estimation model using Census heating mode/fuel + BDNB Open morphology + DPE training data.
4. **Enedis + GRDF** provide territorial energy reality checks at IRIS/commune level.
5. **Base Carbone API** is production-ready for emission factor lookups.
6. **The household-to-dwelling join** is the key probabilistic matching challenge — no open join key exists.
7. **Published outputs from INES, TAXIPP, EUROMOD** serve as validation benchmarks even though the models themselves require restricted data.

---

## 11. Existing Initiatives Using French Open Data for Microsimulation

### 11.1 Synthetic Population Generation

#### eqasim-france — Open Synthetic Population Pipeline

| Attribute | Detail |
|---|---|
| **Producer** | IRT SystemX, Tellae, UMRAE (Sebastian Horl et al.) |
| **Type** | Open-source Python pipeline |
| **URL** | [github.com/eqasim-org/eqasim-france](https://github.com/eqasim-org/eqasim-france) / [HAL paper (2025)](https://hal.science/hal-05018081/) |
| **Input data** | Census detailed files, Filosofi, BPE (Base Permanente des Equipements), OD commuting matrices — **all open data** |
| **Output** | `persons.csv`, `households.csv`, `activities.csv`, `trips.csv` — disaggregated synthetic population with sociodemographic attributes and daily mobility patterns |
| **Coverage** | Ile-de-France fully operational; adaptable to any French region |
| **License** | Open source |

**Relevance to your project:** This is the **closest existing open-source solution** to the synthetic population generator you need. It produces households with sociodemographic attributes from purely open data. However, it's designed for **transport simulation** (agent-based MATSim), not tax-benefit microsimulation. You would need to adapt its household/person output to include income distribution calibration (from Filosofi) and housing/equipment attributes (from Census + DPE). The pipeline architecture ([synpp](https://github.com/eqasim-org/synpp)) is well-designed and could serve as inspiration or direct dependency.

### 11.2 Tax-Benefit Microsimulation Models

#### OpenFisca-France — The Core Engine

| Attribute | Detail |
|---|---|
| **Producer** | OpenFisca community (originally DILA/Etalab) |
| **Type** | Open-source Python rules engine |
| **URL** | [github.com/openfisca/openfisca-france](https://github.com/openfisca/openfisca-france) |
| **Data pipeline** | [openfisca-france-data](https://github.com/openfisca/openfisca-france-data) + [openfisca-survey-manager](https://github.com/openfisca/openfisca-survey-manager) |
| **Input data** | ERFS / ERFS-FPR (**restricted — CASD**) |
| **Open data alternative** | No official open-data input pipeline exists; individual test cases can be built manually |

**Relevance:** This is your computation backend. The existing data pipeline (`openfisca-france-data`) only works with restricted ERFS data. **No one has built a fully open-data input pipeline for OpenFisca-France yet** — this is a gap your project would fill.

#### INES — INSEE/DREES Official Model

| Attribute | Detail |
|---|---|
| **Producer** | INSEE + DREES + CNAF |
| **Type** | Open-source microsimulation model (since 2016) |
| **URL** | [INSEE/INES](https://www.insee.fr/fr/information/2021951) / source code on ADULLACT |
| **Input data** | ERFS (**restricted — CASD**) |
| **Scope** | Simulates main French taxes and social benefits |

**Relevance:** INES is the official French government microsimulation model. Source code is open, but it requires restricted ERFS data. Useful as a **validation benchmark** — your model's tax-benefit results should align with published INES outputs for the same policy scenarios.

#### TAXIPP — IPP Research Model

| Attribute | Detail |
|---|---|
| **Producer** | Institut des Politiques Publiques (IPP) |
| **Type** | Open-source (code); restricted data |
| **URL** | [ipp.eu/TAXIPP](https://www.ipp.eu/en/methods/taxipp-micro-simulation/) |
| **Latest version** | v2.4 (June 2024) |
| **Input data** | Administrative micro-data (**restricted**) |
| **Scope** | Full French tax-benefit system; TAXIPP-LIFE adds life-course dynamics |

**Relevance:** TAXIPP-LIFE is the closest model to your dynamic orchestrator concept — it simulates life courses over time. Code is open but requires restricted administrative data. Published results are valuable as **calibration targets**.

#### EUROMOD — EU-Wide Model (incl. France)

| Attribute | Detail |
|---|---|
| **Producer** | JRC (European Commission) |
| **Type** | Open-source (EUPL-1.2 license) |
| **URL** | [euromod-web.jrc.ec.europa.eu](https://euromod-web.jrc.ec.europa.eu/) |
| **Latest version** | 2024Q3 (February 2025), now includes consumption taxes (VAT, excises) |
| **Input data** | EU-SILC + HBS (**restricted — must be requested from Eurostat**) |
| **Scope** | Tax-benefit microsimulation for all 27 EU member states |

**Relevance:** The 2024Q3 release added **consumption tax simulation** (VAT and excises), which is directly relevant to carbon tax modeling. France module maintained by national team. Code is open-source on GitHub. Data requires Eurostat application. Published country reports provide another **validation benchmark**.

### 11.3 Policy Impact & Citizen-Facing Tools

#### LexImpact — National Assembly Simulator

| Attribute | Detail |
|---|---|
| **Producer** | French National Assembly digital services |
| **Type** | Open-source web application (AGPL-3.0) |
| **URL** | [socio-fiscal.leximpact.an.fr](https://socio-fiscal.leximpact.an.fr/accueil) / [github.com/leximpact](https://github.com/leximpact) |
| **Built on** | OpenFisca-France |
| **Scope** | Simulates impact of tax/benefit law changes on typical households and on state budget |

**Relevance:** Demonstrates the OpenFisca ecosystem's capacity for policy simulation with a user-facing interface. The [LexImpact data preparation documentation](https://documentation.leximpact.dev/leximpact_prepare_data/) details how they transform data for OpenFisca — useful reference for your data pipeline.

#### OpenFisca-France-Dotations-Locales — Local Government Endowments

| Attribute | Detail |
|---|---|
| **Producer** | LexImpact team |
| **Type** | Open-source OpenFisca extension |
| **URL** | [github.com/leximpact/openfisca-france-dotations-locales](https://github.com/leximpact/openfisca-france-dotations-locales) |
| **Input data** | **Open data** (commune-level fiscal data from data.gouv.fr) |

**Relevance:** This is a rare example of an OpenFisca model that runs **entirely on open data**. It models state endowments to local authorities using publicly available commune-level fiscal data. Architecture pattern worth studying for your open-data-first approach.

### 11.4 Building & Renovation Initiatives

#### Go-Renove / PROFEEL — Building Renovation Targeting

| Attribute | Detail |
|---|---|
| **Producer** | CSTB, within the PROFEEL program (16 building industry organizations) |
| **Type** | Web platform + data services |
| **URL** | [gorenove.fr](https://gorenove.fr/) / [programmeprofeel.fr/go-renove](https://programmeprofeel.fr/projets/go-renove/) |
| **Data** | Built on BDNB (Expert tier) |
| **Budget** | Part of EUR 24.5M PROFEEL program (CEE-funded) |
| **Users** | Local authorities, social landlords, individuals |

**Relevance:** Go-Renove demonstrates what's possible when building data is combined with energy performance predictions. It uses BDNB Expert (not open), but the use case — targeting buildings for renovation based on predicted energy class — maps closely to your vintage transition modeling. Their approach to predicting DPE for buildings without one is relevant to filling the open-data DPE coverage gap.

#### etalab/de-dpe-processing — DPE Data Pipeline

| Attribute | Detail |
|---|---|
| **Producer** | Etalab (French government open data team) |
| **Type** | Open-source Python pipeline |
| **URL** | [github.com/etalab/de-dpe-processing](https://github.com/etalab/de-dpe-processing) |
| **Function** | Processes raw ADEME DPE data: extracts heating system details from `td011_installation_chauffage` + `td012_generateur_chauffage` tables, classifies generators, maps energy types |

**Relevance:** Directly usable in your framework to transform raw DPE CSV files into structured equipment data. Handles the extraction of heating generator labels, energy types, primary/secondary/tertiary classification.

### 11.5 Closest Comparables — Detailed Comparison with ReformLab

The four initiatives closest to what ReformLab aims to do are: **INES**, **TAXIPP/TAXIPP-LIFE**, **EUROMOD**, and **eqasim-france**. Each covers part of the problem space but none covers the full scope.

#### Head-to-Head Feature Comparison

| Capability | **INES** (INSEE/DREES) | **TAXIPP / TAXIPP-LIFE** (IPP) | **EUROMOD** (JRC) | **eqasim-france** | **ReformLab** (your project) |
|---|---|---|---|---|---|
| **Core purpose** | Redistribute French taxes & benefits | Full French tax-benefit + life-course (LIFE) | EU-wide tax-benefit comparison | Synthetic population + transport simulation | Environmental policy assessment with distributional analysis |
| **Data requirement** | ERFS (restricted) | Fideli + Felin + DADS + BNS (restricted) | EU-SILC + HBS (restricted) | Census + Filosofi + BPE (**open**) | Census + Filosofi + DPE + Enedis/GRDF + Base Carbone (**open**) |
| **Open data first?** | No — restricted microdata mandatory | No — 4 restricted admin sources | No — EU-SILC mandatory | **Yes** — fully open pipeline | **Yes** — designed for open data from day one |
| **Environmental policy** | No | No | No (consumption taxes since 2024Q3, but no carbon-specific) | No | **Yes** — core focus: carbon tax, subsidies, feebates, rebates |
| **Multi-year dynamics** | No — static (2-year ageing only) | TAXIPP-LIFE: 50-year projections | No — static | No — snapshot only | **Yes** — 10+ year step-pluggable orchestrator |
| **Vintage/asset tracking** | No | No | No | No | **Yes** — vehicle fleet and heating equipment cohort transitions |
| **Energy equipment modeling** | No | No | No | No | **Yes** — DPE-based heating, hot water, cooling, insulation |
| **Emission factor integration** | No | No | No | No | **Yes** — Base Carbone API, energy-to-CO2 conversion |
| **Scenario templates** | Ad hoc reform coding | Ad hoc reform coding | Parameterized reforms | N/A | **Yes** — reusable YAML templates with registry and versioning |
| **Run governance** | No formal provenance | No formal provenance | No formal provenance | Git commit tracking only | **Yes** — immutable manifests, lineage graphs, assumption logs, hash verification |
| **Reproducibility** | Partial (ERFS vintage + code version) | Partial (code + data version) | Partial (model version + data version) | Good (Git commit + open data) | **Full** — deterministic reruns with bit-identical output verification |
| **User interface** | Command-line / scripts | Command-line / Stata + Python | Desktop application (C#) | Python scripts | **Python API + notebooks + no-code GUI** |
| **Accessibility** | Requires statistical expertise + CASD access | Requires econometrics expertise + admin data access | Requires application to Eurostat | Requires Python knowledge | **pip install + 30-min quickstart** |
| **Code license** | Open source (ADULLACT) | Open source | EUPL-1.2 | Open source | Open source |

#### What INES Does That You Don't Need to Rebuild

INES simulates 100+ tax and benefit instruments with exhaustive detail on the French fiscal system. It is the official government reference, co-maintained by INSEE, DREES, and CNAF. **You don't compete with INES — you delegate this computation to OpenFisca**, which implements the same policy rules. Your value is everything that happens *around* and *after* that computation: data preparation from open sources, environmental scenario orchestration, multi-year dynamics, vintage tracking, and governance.

**INES limitation your project addresses:** INES is static (no multi-year), has no environmental policy modeling, no asset tracking, no formal governance, and requires restricted data that blocks most researchers and analysts from using it.

#### What TAXIPP-LIFE Does That's Closest to Your Dynamic Orchestrator

TAXIPP-LIFE is the only existing French model with true multi-year dynamics (50-year projections). It simulates life courses: fertility, marriage, divorce, mortality, career paths, wages, pensions, and disability. This makes it the most architecturally comparable to your dynamic orchestrator.

**Key differences:**
- TAXIPP-LIFE models **demographic life events** over 50 years; your orchestrator models **asset/equipment vintage transitions** over 10 years — fundamentally different dynamics
- TAXIPP-LIFE requires **4 restricted administrative datasets**; yours works on **open data**
- TAXIPP-LIFE has **no environmental dimension** (no carbon tax, no energy equipment, no emission factors)
- TAXIPP-LIFE has **no formal governance** (no manifests, no lineage, no reproducibility harness)
- TAXIPP-LIFE outputs are **fiscal/demographic**; yours are **environmental + distributional**

#### What EUROMOD Offers That's Complementary

EUROMOD's 2024Q3 release added consumption taxes (VAT and excises) for all 27 EU member states. This is the closest any existing model comes to carbon tax simulation, since a carbon tax is essentially an excise on fossil fuels. However, EUROMOD is static, has no environmental framing, and requires restricted EU-SILC data.

**Your advantage:** EUROMOD's France consumption tax module could serve as a **validation benchmark** for your carbon tax templates. If your model's carbon tax burden by income decile is broadly consistent with EUROMOD's consumption tax incidence patterns, that builds credibility.

#### What eqasim-france Gives You for Free

eqasim-france is the only initiative that produces a **fully open synthetic population** for France from public data. It generates households and persons with sociodemographic attributes and daily mobility patterns.

**What it has that you need:** Household synthesis from Census + Filosofi, entirely open-data pipeline, replicable, well-documented.

**What it lacks that you need:** Income distribution calibration for tax-benefit (it does basic income assignment for transport modeling), housing attributes, energy equipment, no OpenFisca compatibility, transport-focused output format.

**Practical path:** Use eqasim's [synpp pipeline architecture](https://github.com/eqasim-org/synpp) as inspiration or starting point, then extend with: Filosofi-calibrated income distributions, Census housing attributes (heating mode, fuel), DPE equipment linkage, OpenFisca entity format output.

### 11.6 Your Project's Unique Value Proposition

Based on the comparison above, **ReformLab occupies a space that no existing initiative covers:**

```
                    Environmental Policy Focus
                           ▲
                           │
                           │    ★ ReformLab
                           │    (your project)
                           │
                           │
          eqasim ─────────►│
       (transport only)    │
                           │
    ───────────────────────┼──────────────────────► Multi-Year Dynamics
                           │
         INES              │        TAXIPP-LIFE
         EUROMOD           │     (demographic life-course,
      (static, no env)     │      no env, restricted data)
                           │
```

**The 5 things only your project does:**

1. **Open-data-first environmental microsimulation** — No existing French model combines open data with environmental policy. INES/TAXIPP/EUROMOD all require restricted data and have no environmental focus.

2. **Vintage/asset tracking for energy equipment and vehicles** — No existing model tracks heating system or vehicle fleet cohort transitions over time. This is the core of environmental policy impact assessment (e.g., "how fast does the fleet shift from gas boilers to heat pumps under a carbon tax?").

3. **End-to-end reproducible governance** — No existing model has immutable run manifests, assumption logs, lineage graphs, and deterministic rerun verification. INES/TAXIPP rely on code versioning only.

4. **Scenario template ecosystem for environmental policy** — Carbon tax variants, subsidies, rebates, feebates as reusable YAML-configured templates with a registry. Existing models require writing custom code for each reform.

5. **Accessible from pip install to distributional charts in 30 minutes** — Existing models require either restricted data applications (months), statistical expertise, or specialized desktop software. Your project is a Python package with notebooks and a no-code GUI.

**What your project deliberately does NOT do** (and shouldn't):
- Rebuild tax-benefit computation rules (OpenFisca does this)
- Model demographic life events (TAXIPP-LIFE does this)
- Achieve cross-country EU comparison (EUROMOD does this)
- Simulate individual travel behavior (eqasim does this)

Your project is the **orchestration and environmental assessment layer** that sits on top of OpenFisca and connects it to open data, multi-year dynamics, and policy-grade governance.

---

## 12. Source Index

All sources verified February 2026:

| # | Source | URL |
|---|---|---|
| 1 | INSEE Filosofi | https://www.insee.fr/fr/metadonnees/source/serie/s1172 |
| 2 | INSEE ERFS | https://www.insee.fr/fr/metadonnees/source/serie/s1231 |
| 3 | INSEE Budget de Famille | https://www.insee.fr/fr/metadonnees/source/serie/s1194 |
| 4 | BDNB | https://bdnb.io/ |
| 5 | DPE ADEME (existing housing) | https://data.ademe.fr/datasets/dpe03existant |
| 6 | DPE ADEME (new housing) | https://data.ademe.fr/datasets/dpe02neuf |
| 7 | Observatoire DPE | https://observatoire-dpe-audit.ademe.fr/ |
| 8 | INSEE ENL | https://www.insee.fr/fr/metadonnees/source/serie/s1004 |
| 9 | INSEE Census Housing | https://www.insee.fr/fr/statistiques/8270440 |
| 10 | INSEE Fideli | https://www.insee.fr/fr/information/3897375 |
| 11 | ONRE Housing Stock by Energy Class | https://www.statistiques.developpement-durable.gouv.fr/le-parc-de-logements-par-classe-de-performance-energetique-au-1er-janvier-2025 |
| 12 | ANAH MaPrimeRenov | https://www.anah.gouv.fr/anatheque/bilan-maprimerenov-S12024 |
| 13 | CEE data.gouv.fr | https://www.data.gouv.fr/datasets/certificats-deconomie-denergie-epci |
| 14 | SDES TREMI | https://www.statistiques.developpement-durable.gouv.fr/enquete-sur-les-travaux-de-renovation-energetique-dans-les-maisons-individuelles-tremi |
| 15 | Enedis Open Data (IRIS) | https://data.enedis.fr/explore/dataset/consommation-electrique-par-secteur-dactivite-iris/ |
| 16 | GRDF Open Data | https://opendata.grdf.fr/ |
| 17 | SDES Residential Energy by Use | https://www.statistiques.developpement-durable.gouv.fr/consommation-denergie-par-usage-du-residentiel |
| 18 | SDES Vehicle Fleet 2025 | https://www.statistiques.developpement-durable.gouv.fr/donnees-sur-le-parc-automobile-francais-au-1er-janvier-2025 |
| 19 | SDES Registrations 2024 | https://www.statistiques.developpement-durable.gouv.fr/donnees-2024-sur-les-immatriculations-des-vehicules |
| 20 | ADEME Base Carbone | https://data.ademe.fr/datasets/base-carboner |
| 21 | Base Carbone API | https://www.data.gouv.fr/dataservices/api-base-carbone |
| 22 | INSEE COG 2025 | https://www.insee.fr/fr/information/8377162 |
| 23 | INSEE IRIS Table | https://www.insee.fr/fr/information/7708995 |
| 24 | OpenFisca France Data | https://github.com/openfisca/openfisca-france-data |
| 25 | OpenFisca Survey Manager | https://github.com/openfisca/openfisca-survey-manager |
| 26 | DPE Processing Pipeline | https://github.com/etalab/de-dpe-processing |
| 27 | BDNB GitLab | https://gitlab.com/BDNB/base_nationale_batiment |
| 28 | data.gouv.fr BDNB | https://www.data.gouv.fr/datasets/base-de-donnees-nationale-des-batiments |
