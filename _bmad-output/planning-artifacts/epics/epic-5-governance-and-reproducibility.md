# Epic 5: Governance and Reproducibility

**User outcome:** Analyst can trust and reproduce any simulation run through immutable manifests and lineage tracking.

**Status:** done (BKL-502, BKL-504, and BKL-505 are partial stubs — see [Phase 1 retrospective GAP 3](../implementation-artifacts/phase-1-retro-2026-02-28.md))

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-501 | Story | P0 | 5 | Define immutable run manifest schema v1 | done | FR25, NFR9 |
| BKL-502 | Story | P0 | 5 | Capture assumptions/mappings/parameters in manifests | done | FR26, FR27 |
| BKL-503 | Story | P0 | 5 | Implement run lineage graph (scenario run -> yearly child runs) | done | FR29 |
| BKL-504 | Task | P0 | 3 | Hash input/output artifacts and store in manifest | done | FR25, NFR12 |
| BKL-505 | Story | P0 | 5 | Add reproducibility check harness for deterministic reruns | done | NFR6, NFR7 |
| BKL-506 | Task | P1 | 3 | Add warning system for unvalidated templates/configs | done | FR27 |

## Epic-Level Acceptance Criteria

- Each run emits one parent manifest plus linked yearly manifests.
- Manifest includes OpenFisca adapter version, scenario version, data hashes, and seeds.
- Rerun harness demonstrates reproducibility for benchmark fixtures.

## Story-Level Acceptance Criteria

**BKL-501: Define immutable run manifest schema v1**

- Given a completed simulation run, when the manifest is generated, then it contains engine version, adapter version, scenario version, data hashes, seeds, timestamps, and parameter snapshot.
- Given a generated manifest, when any field is modified, then integrity checks detect the tampering.

**BKL-502: Capture assumptions/mappings/parameters in manifests**

- Given a run with custom mapping configuration, when the manifest is inspected, then all mappings and assumption sources are listed with their values.
- Given a run using an unvalidated template, when the manifest is generated, then a warning flag is included in the manifest metadata.

**BKL-503: Implement run lineage graph (scenario run -> yearly child runs)**

- Given a 10-year scenario run, when lineage is queried, then one parent manifest links to 10 yearly child manifests.
- Given a yearly child manifest, when its parent is queried, then the parent scenario run is returned.

**BKL-504: Hash input/output artifacts and store in manifest**

- Given input CSV/Parquet files, when hashed, then SHA-256 hashes are stored in the manifest without embedding raw data.
- Given output artifacts, when hashed, then output hashes are stored and can be verified after the run.

**BKL-505: Add reproducibility check harness for deterministic reruns**

- Given a completed run and its manifest, when the harness re-executes with the same inputs and seeds, then outputs are bit-identical.
- Given a run on a different machine (same Python and dependency versions), when re-executed, then outputs match within documented tolerances.

**BKL-506: Add warning system for unvalidated templates/configs**

- Given a scenario using a template not yet marked as validated, when a run is initiated, then a visible warning is emitted before execution proceeds.
- Given a validated template, when a run is initiated, then no warning is emitted.

---
