# Open Synthetic Data Initiatives

Date: 2026-03-23

## Scope

This note lists credible academic and policy initiatives relevant to openly available synthetic population or synthetic microdata, with emphasis on:

- direct usability without registration
- reusable methodology and code
- relevance for policy analysis or microsimulation

## Directly usable now

### 1. GLOPOP-S

- Type: openly downloadable synthetic household and individual dataset
- Source: Scientific Data (2024)
- Coverage: global, including Europe
- Access: public dataset on Harvard Dataverse, code on GitHub
- Why it matters: this is the strongest current example of a large synthetic population that can be used immediately without negotiating access to the underlying microdata
- Caveat: reproducing the exact pipeline depends on LIS and DHS input sources, which are not all frictionless

Key sources:

- https://www.nature.com/articles/s41597-024-03864-2
- https://doi.org/10.7910/DVN/KJC3RH
- https://github.com/VU-IVM/GLOPOP-S

### 2. Eurostat EU-SILC public use files

- Type: official synthetic public microdata
- Source: Eurostat
- Coverage: EU-SILC public microdata
- Access: direct download from Eurostat website, no registration
- Why it matters: directly usable for tool testing, schema design, demos, and code development around European microdata structure
- Caveat: Eurostat explicitly states these files are fully synthetic and should not be used for statistical inference or valid publication analysis

Key sources:

- https://ec.europa.eu/eurostat/web/microdata/public-microdata/statistics-on-income-and-living-conditions
- https://ec.europa.eu/eurostat/web/microdata/public-microdata

### 3. simPop bundled synthetic examples

- Type: open synthetic sample and population example datasets packaged with an open-source R toolkit
- Source: Journal of Statistical Software and CRAN package documentation
- Coverage: includes synthetic Austrian EU-SILC-based example data
- Access: public package/documentation
- Why it matters: not a production policy dataset, but immediately usable for experimentation and pipeline prototyping
- Caveat: example-scale and illustrative, not a general EU-wide policy-ready population

Key sources:

- https://www.jstatsoft.org/article/view/v079i10
- https://www.icesi.edu.co/CRAN/web/packages/simPop/simPop.pdf

## Methodology you can reuse

### 4. GenSynthPop

- Type: open method and packages for generating spatially explicit synthetic populations from aggregated data
- Source: peer-reviewed paper and public repository/case study
- Coverage: designed for settings where rich microdata are unavailable but detailed aggregates exist
- Access: article is open access; public case-study repository is available
- Why it matters: very relevant for Europe because many countries release good aggregate official statistics while detailed microdata remain restricted
- Caveat: usefulness depends on the quality and granularity of available marginals and contingency tables

Key sources:

- https://link.springer.com/article/10.1007/s10458-024-09680-7
- https://github.com/A-Practical-Agent-Programming-Language/Synthetic-Population-The-Hague-South-West

### 5. simPop

- Type: open-source R package for synthetic population generation
- Source: Journal of Statistical Software and IHSN project page
- Coverage: survey plus auxiliary aggregate information
- Access: public code/package
- Why it matters: mature classical workflow for survey-based population synthesis, calibration, and combinatorial optimisation
- Caveat: stronger as a methodology toolbox than as a ready-made policy dataset

Key sources:

- https://www.jstatsoft.org/article/view/v079i10
- https://www.ihsn.org/projects/synthetic-populations

### 6. Great Britain synthetic population workflow

- Type: open paper plus open code and open aggregated outputs
- Source: Scientific Data (2022)
- Coverage: synthetic population workflow for Great Britain
- Access: aggregated outputs and R code are public via Figshare; FMF software is public on GitHub
- Why it matters: very usable as a reference architecture for building a policy-relevant spatial microsimulation pipeline
- Caveat: the full attribute-rich input survey used to build the microsimulation relies on UK Data Service access rather than fully open download

Key sources:

- https://www.nature.com/articles/s41597-022-01124-9
- https://doi.org/10.6084/m9.figshare.c.5443359.v2
- https://github.com/MassAtLeeds/FMF/releases

## Policy and official-statistics initiatives

### 7. UNECE Synthetic Data for Official Statistics

- Type: policy/method handbook
- Source: UNECE
- Coverage: guidance for official-statistics producers
- Access: public
- Why it matters: this is one of the clearest practical guides for statistical agencies deciding when and how to publish synthetic data
- Caveat: it is guidance, not an openly downloadable synthetic population dataset

Key sources:

- https://unece.org/statistics/publications/synthetic-data-official-statistics-starter-guide
- https://www.cbs.nl/en-gb/corporate/2023/20/synthetic-data-opens-up-possibilities-in-the-statistical-field

### 8. Eurostat AIML4OS WP13

- Type: ongoing ESS initiative on synthetic data in official statistics
- Source: Eurostat CROS
- Coverage: use cases, bias assessment, privacy/utility evaluation, AI/ML generation methods
- Access: public project page
- Why it matters: evidence that synthetic-data production is becoming an active official-statistics workstream in Europe rather than a niche research topic
- Caveat: as of the current public page, this is an initiative/work package, not yet a public synthetic dataset catalogue

Key source:

- https://cros.ec.europa.eu/book-page/aiml4os-wp13-generation-synthetic-data-official-statistics-techniques-and-applications

### 9. European Commission Digital Finance synthetic data pilots

- Type: policy pilot and validation reports
- Source: European Commission / JRC / DG FISMA
- Coverage: synthetic data for financial supervisory data sharing
- Access: methodology and pilot reports are public; datasets are not fully open
- Why it matters: shows the Commission already treats synthetic data as a practical infrastructure tool for cross-border data sharing
- Caveat: these are mostly controlled pilots, not open policy microdata assets

Key sources:

- https://digital-finance-platform.ec.europa.eu/data-hub/what-kind-of-data-available
- https://publications.jrc.ec.europa.eu/repository/handle/JRC137249
- https://www.euro-ace.eu/sites/default/files/attached_documents/Synthetic%20data%20pilot%20with%20Banco%20de%20Espa%C3%B1a%20%20findings%20and%20recommendations..pdf

## Practical takeaways

- If the goal is immediate no-registration use, the strongest current candidates are GLOPOP-S and Eurostat’s synthetic EU-SILC public use files.
- If the goal is a reusable European build pipeline, the strongest methodological candidates are GenSynthPop and simPop.
- If the goal is policy credibility, UNECE, Eurostat AIML4OS, and JRC/FISMA pilots show that synthetic data are now a serious official-statistics and public-policy topic, not just an academic side project.
- The main remaining bottleneck is that the best open methods often still rely on restricted or semi-restricted seed microdata during construction, even when the final synthetic output is public.
