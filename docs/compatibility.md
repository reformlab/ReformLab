# OpenFisca Compatibility Matrix

This document is the human-readable companion to the machine-readable
matrix used by ReformLab.

## Source of Truth

- Matrix file: `src/reformlab/computation/compat_matrix.yaml`
- Loader API: `src/reformlab/computation/compat_matrix.py`
- Runtime enforcement: `src/reformlab/computation/openfisca_common.py`

## Policy

- `supported`: explicitly validated and allowed at runtime.
- `untested`: query API may report these as potentially compatible, but
  runtime adapter checks remain strict and will reject them.
- `unsupported`: rejected by runtime checks.

## How to Update

1. Edit `compat_matrix.yaml` with the new OpenFisca version entry.
2. Set status and metadata (`modes_tested`, `known_issues`, `tested_date`, `guidance`).
3. Run:
   - `uv run pytest -q`
   - `uv run mypy src`
   - `uv run ruff check src tests`
4. Update Story 1.7 implementation notes when policy changes.
