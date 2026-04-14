# Epic 11: Realistic Population Generation Library

**User outcome:** Analyst can build a credible French household population from real public data sources, choosing merge methods with transparent assumptions, and producing a population with all attributes needed for policy simulation.

**Status:** done

**Builds on:** EPIC-1 (data layer), EPIC-5 (governance)

**PRD Refs:** FR36–FR42

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-1101 | Story | P0 | 5 | Define DataSourceLoader protocol and caching infrastructure | done | FR36 |
| BKL-1102 | Story | P0 | 5 | Implement INSEE data source loader | done | FR36, FR37 |
| BKL-1103 | Story | P0 | 5 | Implement Eurostat, ADEME, and SDES data source loaders | done | FR36, FR37 |
| BKL-1104 | Story | P0 | 5 | Define MergeMethod protocol and implement uniform distribution method | done | FR38, FR39 |
| BKL-1105 | Story | P0 | 8 | Implement IPF and conditional sampling merge methods | done | FR38, FR39 |
| BKL-1106 | Story | P0 | 8 | Build PopulationPipeline builder with assumption recording | done | FR40, FR41 |
| BKL-1107 | Story | P0 | 5 | Implement population validation against known marginals | done | FR42 |
| BKL-1108 | Story | P0 | 5 | Build French household example pipeline and pedagogical notebook | done | FR40, FR37 |

## Epic-Level Acceptance Criteria

- At least 4 institutional data source loaders are functional (download, cache, schema-validate): INSEE, Eurostat, ADEME, SDES.
- At least 3 statistical merge methods are implemented with `MergeMethod` protocol: uniform distribution, IPF, conditional sampling.
- The French example pipeline produces a population with at least: household_id, income, household_size, region, housing_type, heating_type, vehicle_type, vehicle_age, energy_consumption, carbon_emissions.
- Every merge step records an assumption in the governance layer.
- Generated population validates against source marginals within documented tolerances.
- Methods library docstrings include plain-language explanations of what each method assumes.
- Pedagogical notebook runs end-to-end in CI.

---

## Story 11.1: Define DataSourceLoader protocol and caching infrastructure

**Status:** done
**Priority:** P0
**Estimate:** 5

**PRD Refs:** FR36

### Acceptance Criteria

- Given the `DataSourceLoader` protocol, when a new loader is implemented, then it must provide `download()`, `status()`, and `schema()` methods.
- Given a dataset downloaded for the first time, when cached, then the cache stores a schema-validated Parquet file with SHA-256 hash in `~/.reformlab/cache/sources/{provider}/{dataset_id}/`.
- Given a previously cached dataset, when the loader is called again, then the cache is used without network access.
- Given a network failure with an existing cache, when the loader is called, then the stale cache is used with a governance warning logged.
- Given `REFORMLAB_OFFLINE=1` environment variable, when a loader is called and cache misses, then it fails explicitly without attempting network access.
- Given the cache, when `status()` is called, then it returns `CacheStatus` with cached flag, path, download timestamp, hash, and staleness indicator.

---

## Story 11.2: Implement INSEE data source loader

**Status:** done
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 11.1
**PRD Refs:** FR36, FR37

### Acceptance Criteria

- Given a valid INSEE dataset identifier, when the loader downloads it, then a schema-validated `pa.Table` is returned with documented columns.
- Given the INSEE loader, when queried for available datasets, then at least household income distribution and household composition tables are available.
- Given an invalid or unavailable INSEE dataset ID, when requested, then a clear error identifies the specific dataset and suggests alternatives.
- Given the INSEE loader, when run in CI, then tests use fixture files (no real network calls) marked with `pytest -m network` for opt-in integration tests.

---

## Story 11.3: Implement Eurostat, ADEME, and SDES data source loaders

**Status:** done
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 11.1
**PRD Refs:** FR36, FR37

### Acceptance Criteria

- Given the Eurostat loader, when called with a valid dataset code, then EU-level household data is returned as a schema-validated `pa.Table`.
- Given the ADEME loader, when called, then energy consumption and emission factor datasets are returned with documented schemas.
- Given the SDES loader, when called, then vehicle fleet composition and age distribution data is returned.
- Given all three loaders, when run, then each follows the `DataSourceLoader` protocol and integrates with the caching infrastructure from BKL-1101.
- Given CI tests for all loaders, then they use fixture files and do not require network access.

---

## Story 11.4: Define MergeMethod protocol and implement uniform distribution method

**Status:** done
**Priority:** P0
**Estimate:** 5

**PRD Refs:** FR38, FR39

### Acceptance Criteria

- Given the `MergeMethod` protocol, when a new method is implemented, then it must accept two `pa.Table` inputs plus a config, and return a merged table plus an assumption record.
- Given two tables with no shared sample, when merged using uniform distribution, then each row from Table A is matched with a randomly drawn row from Table B with equal probability.
- Given a uniform merge, when the assumption record is inspected, then it states: "Each household in source A is matched to a household in source B with uniform probability — this assumes no correlation between the variables in the two sources."
- Given the uniform method docstring, when read, then it includes a plain-language explanation of the independence assumption and when this is appropriate vs. problematic.

---

## Story 11.5: Implement IPF and conditional sampling merge methods

**Status:** done
**Priority:** P0
**Estimate:** 8

**Dependencies:** Story 11.4
**PRD Refs:** FR38, FR39

### Acceptance Criteria

- Given two tables and a set of known marginal constraints, when IPF is applied, then the merged population matches the target marginals within documented tolerances.
- Given IPF output, when the assumption record is inspected, then it lists all marginal constraints used and the convergence status.
- Given two tables with a conditioning variable (e.g., income bracket), when conditional sampling is applied, then matches are drawn within strata defined by the conditioning variable.
- Given conditional sampling output, when the assumption record is inspected, then it states the conditioning variable and explains the conditional independence assumption.
- Given both methods, when docstrings are read, then each includes a plain-language explanation suitable for a policy analyst (not just a statistician).

---

## Story 11.6: Build PopulationPipeline builder with assumption recording

**Status:** done
**Priority:** P0
**Estimate:** 8

**Dependencies:** Story 11.4
**PRD Refs:** FR40, FR41

### Acceptance Criteria

- Given a sequence of loaders and merge methods, when composed into a `PopulationPipeline`, then the pipeline executes each step in order and produces a final merged population.
- Given a pipeline execution, when completed, then every merge step's assumption record is captured in the governance layer via the existing `capture.py` integration.
- Given a pipeline, when inspected after execution, then the full chain of steps is visible: which source → which method → which output, for every merge.
- Given a pipeline step that fails (e.g., schema mismatch between two tables), when executed, then the error identifies the exact step, the two tables involved, and the mismatched columns.
- Given a population produced by the pipeline, when its governance record is queried, then all assumption records from all merge steps are retrievable.

---

## Story 11.7: Implement population validation against known marginals

**Status:** done
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 11.6
**PRD Refs:** FR42

### Acceptance Criteria

- Given a generated population and a set of reference marginal distributions (e.g., income distribution by decile from INSEE), when validation is run, then each marginal is compared with a documented distance metric.
- Given validation results, when a marginal exceeds the tolerance threshold, then a warning identifies the specific marginal, expected vs. actual values, and the tolerance used.
- Given validation results, when all marginals pass, then a validation summary is produced confirming the population matches reference distributions.
- Given validation output, when recorded in governance, then the validation status and per-marginal results are part of the population's assumption chain.

---

## Story 11.8: Build French household example pipeline and pedagogical notebook

**Status:** done
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 11.7
**PRD Refs:** FR40, FR37

### Acceptance Criteria

- Given the example pipeline, when executed, then it produces a French household population with at least: household_id, income, household_size, region, housing_type, heating_type, vehicle_type, vehicle_age, energy_consumption, carbon_emissions.
- Given the pedagogical notebook, when run cell by cell, then each merge step is preceded by a plain-language explanation of the method and its assumption, followed by a summary chart showing the result.
- Given the notebook, when run in CI, then it completes without errors.
- Given the notebook, when read by an analyst unfamiliar with statistical matching, then the plain-language explanations make each methodological choice understandable without consulting external references.

## Scope Notes

- **Start with uniform distribution** as the simplest method (equal probability assumption), then layer IPF and conditional sampling.
- **One complete French household example** is the primary deliverable — proving end-to-end pipeline with real INSEE data.
- **Pedagogical notebook** teaches by doing: real data source names, plain-language assumption statements before each merge, summary charts after.
- **Data download/cache infrastructure** — module handles fetching and caching public datasets from institutional APIs/downloads.

---
