# Epic 16: Replication Package Export

**User outcome:** Researcher can export a self-contained package that reproduces any simulation on a clean environment.

**Status:** backlog

**Builds on:** EPIC-5 (governance, manifests), all prior Phase 2 epics

**PRD Refs:** FR54–FR55

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-1601 | Story | P0 | 5 | Implement replication package export with manifest index | backlog | FR54 |
| BKL-1602 | Story | P0 | 5 | Implement replication package import and reproduction | backlog | FR54, FR55 |
| BKL-1603 | Task | P0 | 3 | Include population generation assumptions and calibration provenance | backlog | FR54 |
| BKL-1604 | Story | P0 | 5 | Build replication workflow notebook demo | backlog | FR54, FR55 |

## Epic-Level Acceptance Criteria

- Export produces a self-contained directory/archive with all artifacts needed for reproduction.
- Package contents: population data or generation config, scenario/portfolio config, template definitions, run manifests, seeds, results.
- Import on a clean environment with `pip install reformlab` reproduces results within documented tolerances.
- Package includes all assumption records from population generation.
- Manifest integrity checks pass on reimport.
- Notebook demo runs end-to-end in CI.

---

## Story 16.1: Implement replication package export with manifest index

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**PRD Refs:** FR54

### Acceptance Criteria

- Given a completed simulation run, when the analyst exports a replication package, then a self-contained directory is created with a manifest index file listing all included artifacts.
- Given the exported package, when its contents are inspected, then it includes: population data (or generation config + seed), scenario/portfolio configuration (YAML), template definitions used, run manifests with all parameters and seeds, and simulation results.
- Given the export, when optionally compressed, then the package is a single archive file (zip or tar.gz) that can be shared.
- Given a run that used calibrated parameters, when exported, then the package includes the calibrated β coefficients and references the calibration run metadata.
- Given the manifest index, when parsed, then it lists every artifact with its role (input/config/output), hash for integrity verification, and relative path within the package.

---

## Story 16.2: Implement replication package import and reproduction

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 16.1
**PRD Refs:** FR54, FR55

### Acceptance Criteria

- Given a replication package, when imported on a clean environment with `pip install reformlab`, then all configuration and data artifacts are restored to the correct locations.
- Given an imported package, when the simulation is re-executed, then results match the original within documented floating-point tolerances.
- Given an imported package, when manifest integrity checks run, then all artifact hashes match the recorded values (no corruption or tampering).
- Given a package with a missing or corrupted artifact, when imported, then a clear error identifies which artifact failed integrity checks.
- Given an imported package, when the reproduction run completes, then a comparison report is generated showing original vs. reproduced results with any discrepancies flagged.

---

## Story 16.3: Include population generation assumptions and calibration provenance

**Status:** backlog
**Priority:** P0
**Estimate:** 3

**Dependencies:** Story 16.1
**PRD Refs:** FR54

### Acceptance Criteria

- Given a run that used a generated population (EPIC-11), when the replication package is exported, then it includes the population generation configuration: data sources used, merge methods, statistical assumptions, and the generation seed.
- Given a run that used calibrated parameters (EPIC-15), when exported, then the package includes calibration targets, objective function type, convergence diagnostics, and the final β values.
- Given a package with population generation config, when imported and regenerated on a different machine, then the population is identical (deterministic generation from seed + config).
- Given the assumption records in the package, when inspected by a reviewer, then every methodological choice in the pipeline is traceable from data source to final result.

---

## Story 16.4: Build replication workflow notebook demo

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 16.2, Story 16.3
**PRD Refs:** FR54, FR55

### Acceptance Criteria

- Given the notebook, when run end-to-end, then it demonstrates: running a simulation, exporting a replication package, clearing local state, importing the package, reproducing the simulation, and comparing original vs. reproduced results.
- Given the notebook, when run in CI, then it completes without errors.
- Given the notebook output, when inspected, then it shows: package contents listing, integrity check results, reproduction comparison (matching results), and the researcher sharing workflow (Marco's journey from UX spec).

## Scope Notes

- **Cross-machine reproducibility** — this epic validates TD-17 from Phase 1 retro.
- **Package format** — directory structure with a manifest index, optionally compressed as archive.
- **Marco's journey** — this is the key deliverable for the researcher persona (share YAML + notebook + manifest, co-author reproduces).

---
