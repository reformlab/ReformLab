# ReformLab Architecture

**Project:** ReformLab  
**Date:** 2026-03-06  
**Version:** 1.0

## Overview

ReformLab is structured as a layered, offline-first analytics system for reproducible policy analysis.

## Layers

1. `src/reformlab/computation`  
   OpenFisca adapter interfaces, ingestion, schema mapping, and quality contracts.
2. `src/reformlab/data`  
   Environmental and population input pipeline utilities.
3. `src/reformlab/templates`  
   Policy templates, workflow config schema, registry, migration, and portfolio composition.
4. `src/reformlab/orchestrator` + `src/reformlab/vintage`  
   Deterministic multi-year execution with carry-forward and cohort/vintage transitions.
5. `src/reformlab/indicators`  
   Distributional, fiscal, welfare, geographic, and comparison metrics.
6. `src/reformlab/governance`  
   Manifesting, hashing, lineage, assumption capture, and reproducibility checks.
7. `src/reformlab/interfaces` + `frontend/src`  
   Python API and web UI entry points.

## Key Decisions

- OpenFisca-first computation strategy via adapter boundaries.
- CSV/Parquet as explicit I/O boundaries.
- Deterministic orchestration with seed traceability.
- Immutable run manifests and lineage-first governance.
- Single-machine target with memory-warning guardrails.

## Validation Evidence

- CI gates: `.github/workflows/ci.yml`
- Integration tests: `tests/orchestrator/test_integration.py`
- Reproducibility tests: `tests/governance/test_reproducibility.py`
- Memory safeguards: `tests/interfaces/test_memory_warning.py`
