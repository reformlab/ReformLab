---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: []
workflowType: 'research'
lastStep: 4
research_type: 'market'
research_topic: 'French government microsimulation models for specific policy domains'
research_goals: 'Map the landscape of specialized microsimulation models used by French ministries, understand what policy domains they cover, and assess integration potential with ReformLab'
user_name: 'Lucas'
date: '2026-02-27'
web_research_enabled: true
source_verification: true
---

# Market Research: French Microsimulation Models Landscape

**Date:** 2026-02-27
**Author:** Lucas
**Research Type:** Market Research — Integration Assessment for ReformLab

---

## Executive Summary

France has one of the richest ecosystems of microsimulation models in Europe, with **12+ distinct models** maintained by government agencies, statistical offices, and research institutes. These models span **taxation, social benefits, energy, pensions, elderly care, and housing** policy domains.

For ReformLab, the most immediately relevant and integrable models are **OpenFisca** (already planned), **TAXIPP** (open-source, Python, uses OpenFisca internally), and **Saphir** (open-source on GitHub). Models like **Prometheus** (energy) and **EPEEr** (fuel poverty/housing) cover exactly the environmental policy domains ReformLab targets but are not currently open-source. At the European level, **EUROMOD** is the dominant cross-country tax-benefit model and is fully open-source.

---

## 1. Complete Model Inventory

### 1.1 Tax & Social Benefits (Static Microsimulation)

#### INES (INSEE + DREES + CNAF)

| Attribute | Detail |
|-----------|--------|
| **Full name** | INSEE-DREES |
| **Agency** | INSEE (statistics) + DREES (health ministry) + CNAF (family benefits) |
| **Domain** | All major taxes and social benefits in France |
| **Type** | Static microsimulation |
| **Language** | SAS |
| **Data** | ERFS (Enquete Revenus Fiscaux et Sociaux) — ~50,000 households, 130,000 individuals |
| **Open source** | No (government-internal) |
| **Since** | 1996, updated annually |
| **Key use** | Ex ante evaluation of tax/benefit reforms (RSA 2009, activity premium 2016) |

INES is the **central reference model** for French socio-fiscal microsimulation. It simulates income tax, social contributions, family benefits, housing allowances, social minima, and more. A complementary module handles indirect taxation (VAT, excise duties on tobacco and alcohol).

Sources: [INSEE — Ines overview](https://www.insee.fr/fr/information/2021951) | [DREES — Ines](https://drees.solidarites-sante.gouv.fr/sources-outils-et-enquetes/le-modele-de-microsimulation-ines) | [INSEE Courrier des Statistiques 2020](https://www.insee.fr/fr/information/4497070?sommaire=4497095)

---

#### Saphir (Direction Generale du Tresor)

| Attribute | Detail |
|-----------|--------|
| **Full name** | Saphir |
| **Agency** | Direction Generale du Tresor (Treasury) |
| **Domain** | Household income, social benefits, mandatory deductions |
| **Type** | Static microsimulation |
| **Language** | **SAS** |
| **Data** | ERFS (via CASD secure access) |
| **Open source** | **Yes — CeCILL V2.1 license, on GitHub** |
| **Repository** | [github.com/DGTresor/Saphir](https://github.com/DGTresor/Saphir) |
| **Since** | 2008 |
| **Key use** | Ex ante evaluations of socio-fiscal reforms for the Treasury |

Saphir describes household income and monetary transfers from social benefits and mandatory deductions. It has been used for major reforms including RSA (2009). **The code is on GitHub**, but it's written in SAS, which limits direct integration.

Sources: [DG Tresor — Saphir](https://www.tresor.economie.gouv.fr/Articles/2018/09/05/document-de-travail-de-la-dg-tresor-n-2018-6-le-modele-de-microsimulation-saphir) | [GitHub — DGTresor/Saphir](https://github.com/DGTresor/Saphir)

---

#### TAXIPP (Institut des Politiques Publiques — IPP)

| Attribute | Detail |
|-----------|--------|
| **Full name** | TAXIPP |
| **Agency** | IPP (Institut des Politiques Publiques, academic research) |
| **Domain** | All household taxation and redistribution |
| **Type** | Static microsimulation |
| **Language** | **Python (simulations) + Stata (statistical matching)** |
| **Data** | Fideli (INSEE), Felin (DGFiP), DADS, BNS |
| **Open source** | **Yes — GitLab** |
| **Repository** | [gitlab.com/ipp/partage-public-ipp/taxipp](https://gitlab.com/ipp/partage-public-ipp/taxipp) |
| **Since** | ~2011, latest v2.4.2 (Feb 2026) |
| **Key use** | Comprehensive household taxation analysis |

TAXIPP is the most promising model for ReformLab integration: **it's Python-based, open-source, and already uses OpenFisca-France internally** for its tax-benefit calculations. It statistically matches multiple administrative databases and connects them to OpenFisca.

Sources: [IPP — TAXIPP methods](https://www.ipp.eu/en/methods/taxipp-micro-simulation/) | [GitLab — TAXIPP](https://gitlab.com/ipp/partage-public-ipp/taxipp) | [TAXIPP v2.4.2 release](https://www.ipp.eu/actualites/taxipp-la-version-2-4-2-est-desormais-disponible-en-ligne/)

---

#### Myriade (CNAF)

| Attribute | Detail |
|-----------|--------|
| **Full name** | Myriade |
| **Agency** | CNAF (Caisse Nationale des Allocations Familiales) |
| **Domain** | Family and social benefits |
| **Type** | Static microsimulation |
| **Language** | Unknown (likely SAS) |
| **Data** | Representative sample of all French metropolitan households |
| **Open source** | No |
| **Since** | ~2001 |
| **Key use** | Family benefit policy evaluation |

Myriade was developed by CNAF to overcome limitations of administrative databases. It is representative of all metropolitan French households but has been largely superseded by INES for cross-cutting analyses.

Sources: [Persee — Myriade](https://www.persee.fr/doc/caf_1149-1590_2001_num_66_1_977)

---

#### OpenFisca-France (community + government)

| Attribute | Detail |
|-----------|--------|
| **Full name** | OpenFisca-France |
| **Agency** | Open-source community, beta.gouv.fr, multiple government contributors |
| **Domain** | French tax and benefit system (comprehensive) |
| **Type** | Rule-based computation engine (not a full microsimulation model per se) |
| **Language** | **Python** |
| **Data** | Agnostic — works with any input data |
| **Open source** | **Yes — MIT-like license** |
| **Repository** | [github.com/openfisca/openfisca-france](https://github.com/openfisca/openfisca-france) |
| **Since** | 2011 |
| **Ecosystem** | openfisca-france-data, openfisca-france-entreprises, openfisca-france-dotations-locales |

OpenFisca is already ReformLab's primary computation backend. Key related projects:
- **openfisca-france-data**: Connects to ERFS survey data
- **openfisca-france-entreprises**: Firm-level taxation
- **openfisca-france-dotations-locales**: State endowments to local authorities (by LexImpact)

Sources: [GitHub — OpenFisca-France](https://github.com/openfisca/openfisca-france) | [PyPI](https://pypi.org/project/OpenFisca-France/)

---

#### LexImpact (Assemblee Nationale)

| Attribute | Detail |
|-----------|--------|
| **Full name** | LexImpact |
| **Agency** | French National Assembly |
| **Domain** | Legislative impact simulation (taxation, social affairs) |
| **Type** | Simulation tool for lawmakers |
| **Language** | **Python (built on OpenFisca)** |
| **Open source** | **Yes — AGPL-3.0** |
| **Repository** | [git.leximpact.dev](https://git.leximpact.dev/explore) |
| **Since** | ~2019 |
| **Key use** | MPs simulate effects of amendments on households and state budget |

LexImpact is built on OpenFisca and provides a user-friendly interface for legislators. Its approach to making complex simulations accessible to non-technical users is a direct reference for ReformLab's no-code GUI goals.

Sources: [LexImpact](https://leximpact.an.fr/) | [beta.gouv.fr — LexImpact](https://beta.gouv.fr/startups/leximpact.html)

---

### 1.2 Energy & Environment

#### Prometheus (CGDD)

| Attribute | Detail |
|-----------|--------|
| **Full name** | PROgramme de Microsimulation des Energies du Transport et de l'Habitat pour Evaluations Sociales |
| **Agency** | CGDD (Commissariat General au Developpement Durable), Ministry of Ecology |
| **Domain** | Household energy consumption (housing + transport fuels), energy bills, fuel poverty |
| **Type** | Static microsimulation |
| **Language** | Unknown (not publicly documented) |
| **Data** | INSEE surveys + SDES (statistical service of the ministry) |
| **Open source** | **No — not publicly available** |
| **Since** | ~2016, actively updated (2025 working paper published) |
| **Key use** | Ex ante evaluation of energy tax impacts, energy sobriety measures, fuel poverty policies |

Prometheus is **the most directly relevant model for ReformLab's environmental policy mission**. It simulates individual household energy consumption for housing (domestic fuels) and transport (car fuels), then computes energy bills and the distributional impact of energy taxation changes. It was recently presented (June 2025) as a tool for "microsimulation serving the just transition."

**Integration challenge**: The code is not publicly available. However, the methodology is well-documented and could be replicated within ReformLab using OpenFisca formulas + energy consumption data.

Sources: [CGDD Working Paper 70 (March 2025)](https://www.ecologie.gouv.fr/sites/default/files/publications/document_travail_70_prometheus_microsimulation_facture_energetique_menage_mars2025.pdf) | [CGDD Presentation (June 2025)](https://www.ecologie.gouv.fr/sites/default/files/publications/diaporama_modele_prometheus%20_la_microsimulation_au_service_de_la_transition_juste.pdf) | [ResearchGate — Prometheus methodology](https://www.researchgate.net/publication/323542736_Simuler_l'impact_social_de_la_fiscalite_energetique_le_modele_Prometheus_-_Usages_et_methodologie)

---

#### EPEEr (Academic / ADEME-related)

| Attribute | Detail |
|-----------|--------|
| **Full name** | EPEEr |
| **Agency** | Academic research, linked to ADEME |
| **Domain** | Housing energy retrofit, fuel poverty dynamics |
| **Type** | Dynamic microsimulation |
| **Data** | ENL 2013 (Enquete Nationale Logements) + ADEME EPC database |
| **Open source** | Unknown |
| **Key use** | Impact of renovation subsidies on fuel poverty over time |

EPEEr models household-level energy poverty dynamics, simulating how energy prices, unemployment, and renovation subsidies affect fuel poverty trajectories. Unlike Prometheus (static, snapshot), EPEEr is dynamic and tracks changes over time — making it a natural complement.

Sources: [ScienceDirect — EPEEr](https://www.sciencedirect.com/science/article/abs/pii/S0378778825000787) | [ScienceDirect — Fuel poverty simulation](https://www.sciencedirect.com/science/article/abs/pii/S0301421520301877)

---

### 1.3 Pensions & Retirement

#### Destinie 2 (INSEE)

| Attribute | Detail |
|-----------|--------|
| **Full name** | Destinie 2 (Demographique Economique et Social de Trajectoires INdividuelles sImulEes) |
| **Agency** | INSEE |
| **Domain** | Pensions and retirement system projections |
| **Type** | **Dynamic** microsimulation |
| **Language** | **C++ transcribed to R** |
| **Data** | Household Wealth Survey |
| **Open source** | **Yes — on GitHub** |
| **Repository** | [github.com/InseeFr/Destinie-2](https://github.com/InseeFr/Destinie-2) |
| **Since** | Mid-1990s (v1), 2010 (v2) |
| **Key use** | Long-term pension projections for COR (Conseil d'Orientation des Retraites) and European Commission |

Destinie 2 reconstructs full career trajectories and simulates pension liquidation under various legislative scenarios. It operates at both individual and household levels, enabling standard-of-living calculations. The **code is open-source on GitHub in C++/R**.

Sources: [INSEE — Destinie 2](https://www.insee.fr/fr/information/3606338) | [GitHub — InseeFr/Destinie-2](https://github.com/InseeFr/Destinie-2)

---

#### TRAJECTOiRE (DREES)

| Attribute | Detail |
|-----------|--------|
| **Full name** | TRAJECTOiRE (TRAJEctoire de Carrieres TOus REgimes) |
| **Agency** | DREES |
| **Domain** | Pensions across all retirement regimes |
| **Type** | Dynamic microsimulation |
| **Data** | EIC (Echantillon Interregimes de Cotisants) — ~700,000 individuals |
| **Open source** | No |
| **Since** | ~2015 |
| **Key use** | Simulating retirement reform impacts across all French pension regimes |

TRAJECTOiRE has three modules: career modeling, retirement age simulation, and pension calculation. It complements Destinie 2 by focusing specifically on cross-regime pension calculations with a much larger sample.

Sources: [DREES — TRAJECTOiRE](https://drees.solidarites-sante.gouv.fr/sources-outils-et-enquetes/le-modele-trajectoire) | [INSEE — TRAJECTOiRE article](https://www.insee.fr/fr/statistiques/1305197?sommaire=1305205)

---

### 1.4 Elderly Care & Dependency

#### Autonomix (DREES)

| Attribute | Detail |
|-----------|--------|
| **Full name** | Autonomix |
| **Agency** | DREES |
| **Domain** | Elderly dependency — APA (Allocation Personnalisee d'Autonomie), home/institutional care |
| **Type** | Static microsimulation |
| **Language** | **R** |
| **Data** | Administrative data from departmental councils (APA beneficiaries) |
| **Open source** | Unknown |
| **Since** | 2011 |
| **Key use** | Evaluating care policies for elderly dependents (who pays what, reform impacts) |

Autonomix has two modules: home care and institutional care (EHPAD). It simulates APA benefits, income taxes, and other transfers for each senior. Created for the 2011 national debate on dependency.

Sources: [DREES — Autonomix](https://drees.solidarites-sante.gouv.fr/sources-outils-et-enquetes/le-modele-de-microsimulation-autonomix) | [INSEE — Autonomix article](https://www.insee.fr/fr/statistiques/1305191?sommaire=1305205)

---

### 1.5 European / Cross-Country

#### EUROMOD (European Commission — JRC)

| Attribute | Detail |
|-----------|--------|
| **Full name** | EUROMOD |
| **Agency** | JRC (Joint Research Centre, European Commission); formerly ISER/University of Essex |
| **Domain** | Tax-benefit systems of all EU member states |
| **Type** | Static microsimulation |
| **Language** | **C# (open source since 2020)** |
| **Data** | EU-SILC (harmonized across EU) |
| **Open source** | **Yes — EUPL-1.2 license (code), CC BY 4.0 (policy rules)** |
| **Repository** | Available via [euromod-web.jrc.ec.europa.eu](https://euromod-web.jrc.ec.europa.eu/download-euromod) and GitHub |
| **Since** | Late 1990s; managed by JRC since 2021 |
| **Latest** | J1.86+ Beta (Sep 2025), J1.0+ Stable (Feb 2025) |
| **Key use** | Cross-country comparable tax-benefit analysis for all 27 EU member states |

EUROMOD is the reference model for EU-wide policy analysis. It includes France, making it a potential source for cross-country comparison in ReformLab.

Sources: [EUROMOD — What is EUROMOD](https://euromod-web.jrc.ec.europa.eu/overview/what-is-euromod) | [EUROMOD — Download](https://euromod-web.jrc.ec.europa.eu/download-euromod) | [JRC — EUROMOD](https://joint-research-centre.ec.europa.eu/euromod_en)

---

## 2. Landscape Summary Matrix

| Model | Agency | Domain | Type | Language | Open Source | Data | ReformLab Relevance |
|-------|--------|--------|------|----------|-------------|------|---------------------|
| **OpenFisca-France** | Community | Tax & benefits | Engine | Python | Yes (MIT) | Agnostic | **Already core** |
| **TAXIPP** | IPP | All taxation | Static | Python+Stata | Yes (GitLab) | Admin. files | **High — uses OpenFisca** |
| **LexImpact** | Assemblee Nat. | Legislative impact | UI tool | Python | Yes (AGPL) | Via OpenFisca | **High — UX reference** |
| **Saphir** | DG Tresor | Income & transfers | Static | SAS | Yes (GitHub) | ERFS | Medium (SAS barrier) |
| **INES** | INSEE+DREES | Tax & benefits | Static | SAS | No | ERFS | Low (closed, SAS) |
| **Myriade** | CNAF | Family benefits | Static | Unknown | No | Representative | Low |
| **Prometheus** | CGDD | Energy bills | Static | Unknown | No | INSEE+SDES | **Critical domain** |
| **EPEEr** | Academic | Fuel poverty/housing | Dynamic | Unknown | Unknown | ENL | Important domain |
| **Destinie 2** | INSEE | Pensions | Dynamic | C++/R | Yes (GitHub) | Wealth survey | Medium |
| **TRAJECTOiRE** | DREES | Pensions (all regimes) | Dynamic | Unknown | No | EIC | Low |
| **Autonomix** | DREES | Elderly care | Static | R | Unknown | Admin. data | Low |
| **EUROMOD** | JRC (EU) | All EU tax-benefit | Static | C# | Yes (EUPL) | EU-SILC | Medium (EU scope) |

---

## 3. Integration Assessment for ReformLab

### Tier 1 — Direct Integration (Already planned or immediately feasible)

**OpenFisca-France**: Already ReformLab's core computation engine. The adapter pattern is built around it.

**TAXIPP (IPP)**: Highest integration potential after OpenFisca. It's Python, open-source, and *already uses OpenFisca internally*. ReformLab could:
- Reuse TAXIPP's statistical matching pipeline for richer datasets
- Import TAXIPP's data preparation scripts
- Reference TAXIPP's methodology for distributional analysis

**LexImpact**: Not a computation model to integrate, but a **UX reference** — it shows how to make OpenFisca-based simulations accessible to non-experts, which directly informs ReformLab's no-code GUI layer.

### Tier 2 — Methodology Replication (Medium-term)

**Prometheus (CGDD)**: The code is not open, but the methodology is thoroughly documented (2016 report + 2025 working paper). ReformLab could:
- **Implement Prometheus-like energy bill calculations as OpenFisca variables/formulas**
- Use the same data sources (SDES energy surveys, INSEE household surveys)
- This is the most strategically important model to replicate — it covers the exact environmental policy domain ReformLab targets

**EPEEr**: The dynamic fuel poverty / housing renovation model. Its methodology could inform ReformLab's multi-year orchestration for energy retrofit policies.

**Saphir (DG Tresor)**: Open-source on GitHub but written in SAS. Its methodology and policy rule implementations could serve as validation reference for OpenFisca formulas.

### Tier 3 — Reference / Validation (Long-term or out of scope)

**EUROMOD**: Useful for cross-country comparisons once ReformLab expands beyond France. Being C#-based makes direct integration impractical, but its France module could serve as validation data.

**Destinie 2**: Open-source (C++/R) pension model. If ReformLab ever covers pension policy, this would be the starting point.

**INES, Myriade, TRAJECTOiRE, Autonomix**: Government-internal or domain-specific models that serve as references for methodology validation but aren't directly integrable.

---

## 4. Strategic Recommendations for ReformLab

### Immediate Actions

1. **Study TAXIPP's codebase** on GitLab — it demonstrates how to build a complete microsimulation pipeline on top of OpenFisca with real French data
2. **Study LexImpact's UX patterns** — it's the best existing example of making OpenFisca accessible to non-programmers
3. **Download and read the Prometheus 2025 working paper** — it contains the methodology needed to implement energy bill microsimulation in ReformLab

### Medium-term Strategy

4. **Implement Prometheus-equivalent energy bill formulas** as custom OpenFisca variables within ReformLab. This is the key differentiator — bringing environmental policy microsimulation into an open, accessible platform
5. **Explore TAXIPP's data matching pipeline** for connecting administrative data sources to OpenFisca simulations
6. **Investigate EPEEr's approach** for dynamic multi-year energy poverty tracking — this maps directly to ReformLab's orchestrator

### Key Insight

Most French microsimulation models are either **closed-source SAS tools** (INES, Saphir) or **narrowly domain-specific** (Autonomix, TRAJECTOiRE). The real opportunity for ReformLab is not to "integrate" these models but to **replicate their most valuable methodology** — particularly Prometheus's energy microsimulation — within the open OpenFisca ecosystem, making it accessible and composable for the first time.

---

## Sources

### Models & Documentation
- [INSEE — Microsimulation models overview (2020)](https://www.insee.fr/fr/information/4497054?sommaire=4497095)
- [INSEE — INES model](https://www.insee.fr/fr/information/2021951)
- [DREES — INES](https://drees.solidarites-sante.gouv.fr/sources-outils-et-enquetes/le-modele-de-microsimulation-ines)
- [DG Tresor — Saphir](https://www.tresor.economie.gouv.fr/Articles/2018/09/05/document-de-travail-de-la-dg-tresor-n-2018-6-le-modele-de-microsimulation-saphir)
- [GitHub — DGTresor/Saphir](https://github.com/DGTresor/Saphir)
- [IPP — TAXIPP methods](https://www.ipp.eu/en/methods/taxipp-micro-simulation/)
- [GitLab — TAXIPP source code](https://gitlab.com/ipp/partage-public-ipp/taxipp)
- [CGDD — Prometheus working paper (2025)](https://www.ecologie.gouv.fr/sites/default/files/publications/document_travail_70_prometheus_microsimulation_facture_energetique_menage_mars2025.pdf)
- [CGDD — Prometheus presentation (June 2025)](https://www.ecologie.gouv.fr/sites/default/files/publications/diaporama_modele_prometheus%20_la_microsimulation_au_service_de_la_transition_juste.pdf)
- [GitHub — InseeFr/Destinie-2](https://github.com/InseeFr/Destinie-2)
- [DREES — TRAJECTOiRE](https://drees.solidarites-sante.gouv.fr/sources-outils-et-enquetes/le-modele-trajectoire)
- [DREES — Autonomix](https://drees.solidarites-sante.gouv.fr/sources-outils-et-enquetes/le-modele-de-microsimulation-autonomix)
- [EUROMOD — Overview](https://euromod-web.jrc.ec.europa.eu/overview/what-is-euromod)
- [LexImpact](https://leximpact.an.fr/)
- [GitHub — OpenFisca-France](https://github.com/openfisca/openfisca-france)

### Academic References
- [Cairn — Panorama of microsimulation in France (2004)](https://cairn.info/revue-d-economie-politique-2004-1-page-17.htm)
- [Persee — French socioeconomic microsimulation models (2001)](https://www.persee.fr/doc/caf_1149-1590_2001_num_66_1_976)
- [Persee — Emergence and consolidation of microsimulation in France (2019)](https://www.persee.fr/doc/estat_0336-1454_2019_num_510_1_10910)
- [RePEc — Carbon tax distributional effects (2019)](https://ideas.repec.org/a/eee/enepol/v124y2019icp81-94.html)
