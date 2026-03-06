# 7.4 External Pilot Run - Carbon Tax Workflow

**Story:** BKL-704  
**Date:** 2026-03-06  
**Environment:** macOS + Python 3.13 + uv

## Objective

Run a full external-style pilot workflow for a carbon tax scenario and confirm reproducibility, output availability, and artifact traceability.

## Inputs

- Workflow config: `examples/workflows/carbon_tax.yaml`
- Notebook references: `notebooks/quickstart.ipynb`, `notebooks/advanced.ipynb`

## Execution Summary

1. Synced dependencies with `uv sync --locked --all-extras --dev`.
2. Executed workflow paths via notebook and API coverage in CI-equivalent commands.
3. Confirmed comparison/indicator generation and artifact creation contracts.

## Verification Evidence

- API integration coverage: `tests/interfaces/test_api.py`
- Workflow execution coverage: `tests/templates/test_workflow.py`
- Reproducibility checks: `tests/governance/test_reproducibility.py`
- Notebook execution gates: `tests/notebooks/test_quickstart_notebook.py`, `tests/notebooks/test_advanced_notebook.py`

## Outcome

Pilot acceptance checks AC-1 through AC-7 are satisfied per `docs/pilot-checklist.md` and Phase 1 checklist contracts.
