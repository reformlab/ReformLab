# Epic 8: Post-Phase-1 Validation Spikes

**User outcome:** Platform developers confirm that the adapter layer works end-to-end with real OpenFisca and at production scale.

**Status:** done

Priority and SP are not assigned for post-Phase-1 spikes.

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|------|-------|--------|----------|
| 8-1 | Spike | — | — | End-to-end OpenFisca integration spike | done | — |
| 8-2 | Story | — | — | Scale validation: 100k synthetic population benchmarks | done | NFR1, NFR3 |

## Epic-Level Acceptance Criteria

- Adapter processes real OpenFisca-France computations end-to-end without error.
- Platform handles 100k-household populations within NFR performance targets.
- All findings and gaps are documented for follow-up in EPIC-9.

## Story-Level Acceptance Criteria

**8-1: End-to-end OpenFisca integration spike**

- `openfisca-france` installs and is importable in the project's Python 3.13 environment.
- `OpenFiscaApiAdapter` loads a real `CountryTaxBenefitSystem` and returns a valid version string.
- Real computation returns numeric values (not all zeros, not NaN) for known variables and periods.
- Multi-entity population works via `SimulationBuilder.build_from_entities()`.
- Variable mapping round-trip produces correct project-schema column names.
- Findings documented in [8-1 spike findings](../implementation-artifacts/spike-findings-8-1-openfisca-integration.md).

**8-2: Scale validation — 100k synthetic population benchmarks**

- Persistent 100k synthetic population generated with seed 42, registered via `DatasetManifest` with SHA-256 hash.
- BKL-701 benchmark suite passes with the persistent population.
- Full simulation completes within NFR1 target (< 10 seconds) for 100k households.

---
