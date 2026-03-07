

# Story 15.5: Build Calibration Workflow Notebook Demo

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **policy analyst**,
I want a pedagogical notebook that walks me through the complete calibration workflow — loading observed transition rates, running the calibration engine, inspecting convergence diagnostics, validating against holdout data, and using calibrated parameters in a simulation,
so that I can understand, reproduce, and adapt the calibration process for my own policy analysis without consulting external references.

## Acceptance Criteria

1. **AC-1: End-to-end workflow** — Given the notebook, when run end-to-end, then it demonstrates: loading observed transition rates (from fixture CSV), running the `CalibrationEngine`, inspecting convergence diagnostics (iterations, gradient norm, convergence flag), validating against holdout data via `validate_holdout()`, and using calibrated parameters in a simulation via `extract_calibrated_parameters()`.
2. **AC-2: CI execution** — Given the notebook, when run via `pytest --nbmake notebooks/guides/10_calibration_workflow.ipynb -v` in CI, then it completes without errors. The notebook is committed with cleared outputs.
3. **AC-3: Visualization and interpretation** — Given the notebook output, when inspected, then it shows: (a) training vs. observed rate comparison bar chart, (b) holdout validation metrics side-by-side with training metrics, (c) a final simulation using calibrated parameters displaying a per-household choice probability matrix computed via `compute_utilities()` and `compute_probabilities()`, and (d) governance provenance entries captured via `capture_calibration_provenance()`.
4. **AC-4: Static validation tests** — Given the static test file `tests/notebooks/test_epic15_notebook.py`, when run, then it validates: notebook exists, outputs are cleared, public API imports are correct, required sections are present, key API calls are present, and CI workflow includes the notebook.

## Tasks / Subtasks

- [x] Task 1: Create the notebook (AC: 1, 2, 3)
  - [x] 1.1: Create `notebooks/guides/10_calibration_workflow.ipynb` with cleared outputs and `python3` kernel metadata
  - [x] 1.2: Section 0 — Setup: imports, path resolution (`_NB_DIR`), `SEED = 42`, `show()` helper
  - [x] 1.3: Section 1 — Load Calibration Targets: load training targets from fixture CSV via `load_calibration_targets()`, display target summary table, explain target format (domain, period, from_state, to_state, observed_rate, source_label)
  - [x] 1.4: Section 2 — Build Cost Matrix: construct a small CostMatrix (from conftest pattern — 3 households, 2 alternatives), build `from_states` PyArrow array, explain how CostMatrix connects households to alternative costs
  - [x] 1.5: Section 3 — Run Calibration Engine: create `CalibrationConfig`, instantiate `CalibrationEngine`, call `calibrate()`, display convergence diagnostics (iterations, gradient_norm, convergence_flag, method, objective_type, objective_value), print per-target `RateComparison` results showing observed vs simulated rates
  - [x] 1.6: Section 4 — Visualize Training Fit: matplotlib grouped bar chart comparing observed_rate vs simulated_rate per target (from_state → to_state labels), show `all_within_tolerance` status, highlight rate_tolerance threshold on chart
  - [x] 1.7: Section 5 — Holdout Validation: construct holdout CostMatrix and from_states (different data from training), load holdout targets, call `validate_holdout()`, display side-by-side training vs holdout `FitMetrics` (MSE, MAE, n_targets, all_within_tolerance) in a formatted comparison
  - [x] 1.8: Section 6 — Governance Provenance: call `capture_calibration_provenance()` with all three inputs (result, target_set, holdout_result), display the AssumptionEntry list, call `make_calibration_reference()` with a sample manifest ID, show how entries would be added to a `RunManifest`
  - [x] 1.9: Section 7 — Parameter Round-Trip: demonstrate `extract_calibrated_parameters()` to recover `TasteParameters` from the captured assumptions list, verify exact β equality, explain the calibration → manifest → extraction lifecycle
  - [x] 1.10: Section 8 — Using Calibrated Parameters in Simulation: use extracted `TasteParameters` with `compute_utilities()` and `compute_probabilities()` on the training CostMatrix, display the per-household choice probability matrix, verify the calibrated β feeds through the discrete choice pipeline
  - [x] 1.11: Section 9 — Summary and Next Steps: recap the calibration workflow steps, link to related guides (08_discrete_choice_model, 09_population_generation), note that production calibration uses larger populations and real institutional data

- [x] Task 2: Create fixture data files (AC: 1, 2)
  - [x] 2.1: Create `tests/fixtures/calibration/holdout_vehicle_targets.csv` with 3 holdout targets (same domain=vehicle, period=2023 vs training period=2022, different observed rates) — matches the conftest holdout pattern
  - [x] 2.2: Verify `tests/fixtures/calibration/valid_vehicle_targets.csv` exists and is suitable for notebook training data (already created by Story 15.1)

- [x] Task 3: Create static validation test file (AC: 4)
  - [x] 3.1: Create `tests/notebooks/test_epic15_notebook.py` following the `test_epic14_notebook.py` pattern exactly
  - [x] 3.2: `test_notebook_exists()` — verify path `notebooks/guides/10_calibration_workflow.ipynb`
  - [x] 3.3: `test_outputs_cleared()` — all code cells have `execution_count: None` and `outputs: []`
  - [x] 3.4: `test_uses_public_api()` — verify imports from `reformlab.calibration`, `reformlab.discrete_choice`, no internal imports, no OpenFisca imports
  - [x] 3.5: `test_required_sections()` — verify all 10 section headers present in notebook source
  - [x] 3.6: `test_key_api_calls()` — verify key API calls present: `load_calibration_targets(`, `CalibrationEngine(`, `.calibrate()`, `validate_holdout(`, `capture_calibration_provenance(`, `make_calibration_reference(`, `extract_calibrated_parameters(`, `TasteParameters(`, `RunManifest(`
  - [x] 3.7: `test_ci_includes_notebook()` — verify CI workflow includes nbmake for this notebook

- [x] Task 4: Update CI workflow (AC: 2)
  - [x] 4.1: Add `- run: uv run pytest --nbmake notebooks/guides/10_calibration_workflow.ipynb -v` to `.github/workflows/ci.yml` after the existing notebook lines

- [x] Task 5: Lint, type-check, regression (AC: all)
  - [x] 5.1: `uv run ruff check tests/notebooks/test_epic15_notebook.py` — clean
  - [x] 5.2: `uv run pytest tests/notebooks/test_epic15_notebook.py -v` — all static checks pass
  - [x] 5.3: `uv run pytest --nbmake notebooks/guides/10_calibration_workflow.ipynb -v` — notebook executes without errors
  - [x] 5.4: `uv run pytest tests/` — all existing tests pass (no regressions)

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**Notebook location:** `notebooks/guides/10_calibration_workflow.ipynb` — the next sequential guide after `09_population_generation.ipynb`. Guide numbering is sequential within the `guides/` directory (not tied to epic numbers).

**File layout after this story:**
```
notebooks/guides/
├── 01_data_foundation.ipynb
├── 02_scenario_templates.ipynb
├── 03_multiyear_orchestration.ipynb
├── 04_indicators_comparison.ipynb
├── 05_governance_reproducibility.ipynb
├── 06_portfolio_comparison.ipynb          ← Epic 12.5 demo
├── 07_custom_templates.ipynb
├── 08_discrete_choice_model.ipynb         ← Epic 14.7 demo
├── 09_population_generation.ipynb         ← Epic 11.8 demo
└── 10_calibration_workflow.ipynb          ← NEW (Epic 15.5 demo)

tests/notebooks/
├── test_quickstart_notebook.py
├── test_advanced_notebook.py
├── test_epic14_notebook.py
└── test_epic15_notebook.py                ← NEW
```

**Notebook conventions (observed across all existing guides):**

1. **Cell structure**: Repeating "Markdown (explain) → Code (implement) → Markdown (interpret)" triplets
2. **Determinism**: `SEED = 42` at top of notebook; all random operations respect seed
3. **Path resolution**: `_NB_DIR = Path(__file__).parent if "__file__" in dir() else Path(".")`
4. **Imports**: `from __future__ import annotations` at top of first code cell
5. **Visualization**: `matplotlib.pyplot` only; no other viz libraries
6. **Data**: PyArrow tables (`pa.Table`) throughout; no pandas in core logic
7. **Verification**: `print("✓ ...")` pattern for checkpoint validation
8. **Pedagogical style**: Plain-language explanations suitable for policy analysts (not statisticians)
9. **Cleared outputs**: All notebooks committed with `execution_count: None` and `outputs: []`
10. **No network calls**: All data from local fixtures for offline CI

### Key Imports for Notebook

```python
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pyarrow as pa

from reformlab.calibration import (
    CalibrationConfig,
    CalibrationEngine,
    CalibrationTargetSet,
    capture_calibration_provenance,
    extract_calibrated_parameters,
    load_calibration_targets,
    make_calibration_reference,
    validate_holdout,
)
from reformlab.discrete_choice import (
    CostMatrix,
    TasteParameters,
    compute_probabilities,
    compute_utilities,
)
from reformlab.governance.manifest import RunManifest
```

### Data Strategy

**Training data**: Use existing `tests/fixtures/calibration/valid_vehicle_targets.csv` (created by Story 15.1). This contains vehicle domain targets for period=2022 with from_state/to_state transition rates.

**Holdout data**: Create new `tests/fixtures/calibration/holdout_vehicle_targets.csv` with same domain/transitions but period=2023 and slightly different rates. Pattern matches `make_holdout_target_set()` in conftest.py:
- petrol → alternative_a: 0.45 (training: 0.40)
- petrol → alternative_b: 0.50 (training: 0.55)
- diesel → alternative_a: 0.65 (training: 0.60)

**CostMatrix construction**: Build inline following the conftest.py pattern:
```python
# Training population: 3 households, 2 alternatives
training_cost_matrix = CostMatrix(
    table=pa.table({
        "alternative_a": pa.array([100.0, 150.0, 200.0]),
        "alternative_b": pa.array([200.0, 100.0, 300.0]),
    }),
    alternative_ids=("alternative_a", "alternative_b"),
)
training_from_states = pa.array(["petrol", "petrol", "diesel"])

# Holdout population: 3 households, same alternatives, different costs
holdout_cost_matrix = CostMatrix(
    table=pa.table({
        "alternative_a": pa.array([110.0, 140.0, 210.0]),
        "alternative_b": pa.array([190.0, 110.0, 280.0]),
    }),
    alternative_ids=("alternative_a", "alternative_b"),
)
holdout_from_states = pa.array(["petrol", "petrol", "diesel"])
```

### Section-by-Section Notebook Content Guide

**Section 0 — Setup (2 cells)**
- Markdown: Title "Calibration Workflow", overview of what calibration does (fit taste parameters β to observed transition data), learning objectives
- Code: imports, path resolution, SEED, show() helper

**Section 1 — Load Calibration Targets (3 cells)**
- Markdown: Explain calibration target format — what each field means (domain, period, from_state, to_state, observed_rate), where real data comes from (ADEME vehicle adoption, SDES fleet stats)
- Code: `load_calibration_targets()` on training fixture, print summary
- Markdown: Interpretation of loaded targets

**Section 2 — Build Cost Matrix (3 cells)**
- Markdown: Explain CostMatrix concept — N households × M alternatives, each cell = cost of that choice for that household
- Code: Build CostMatrix and from_states inline (small fixture data)
- Markdown: What from_states represents (current household state)

**Section 3 — Run Calibration Engine (4 cells)**
- Markdown: Explain calibration engine concept — iteratively adjusts β until simulated transition rates match observed rates, MSE objective
- Code: Create CalibrationConfig, CalibrationEngine, call `.calibrate()`
- Code: Print convergence diagnostics table (iterations, gradient_norm, convergence_flag, method, objective_value)
- Markdown: Interpret diagnostics — what convergence means, what gradient_norm tells you

**Section 4 — Visualize Training Fit (3 cells)**
- Markdown: "Let's see how well the calibrated model matches the observed transition rates"
- Code: Grouped bar chart (observed vs simulated per target), horizontal dashed line at rate_tolerance
- Markdown: Interpret chart — which targets fit well, which don't, what all_within_tolerance means

**Section 5 — Holdout Validation (4 cells)**
- Markdown: Explain holdout validation — "Does the calibrated model generalize beyond the training data?" Uses a different time period (2023 vs 2022) to test
- Code: Build holdout CostMatrix/from_states, load holdout targets, call `validate_holdout()`
- Code: Print side-by-side training vs holdout FitMetrics (MSE, MAE, all_within_tolerance) in formatted table
- Markdown: Interpret — what good generalization looks like (holdout MSE close to training MSE)

**Section 6 — Governance Provenance (3 cells)**
- Markdown: Explain governance integration — "Every calibration produces an assumption trail for reproducibility"
- Code: Call `capture_calibration_provenance(result, target_set=..., holdout_result=...)`, display entries; call `make_calibration_reference("sample-uuid-12345")`; show how entries fit into `RunManifest(assumptions=...)`
- Markdown: Explain each governance entry key (calibration_result, calibration_targets, holdout_validation, calibration_reference)

**Section 7 — Parameter Round-Trip (3 cells)**
- Markdown: Explain round-trip extraction — "Given a manifest with calibration assumptions, you can recover the exact same β parameters"
- Code: `extract_calibrated_parameters(entries, "vehicle")`, verify `extracted.beta_cost == result.optimized_parameters.beta_cost`, print confirmation
- Markdown: Why this matters — enables reproducibility across sessions and sharing calibrated parameters

**Section 8 — Using Calibrated Parameters (3 cells)**
- Markdown: Explain how calibrated TasteParameters feed into the discrete choice pipeline
- Code: Use extracted TasteParameters with `compute_utilities()` and `compute_probabilities()` on the training CostMatrix, display choice probability matrix
- Markdown: Interpret probabilities — what the β coefficient means for household decisions

**Section 9 — Summary and Next Steps (1 cell)**
- Markdown: Recap workflow (load targets → calibrate → validate → record → extract → simulate), link to guides 08 and 09, note that production uses larger populations and real institutional data

### Visualization Specifications

**Training Fit Bar Chart (Section 4):**
```python
fig, ax = plt.subplots(1, 1, figsize=(10, 5))

targets_labels = [f"{rc.from_state} → {rc.to_state}" for rc in result.rate_comparisons]
x = range(len(targets_labels))
width = 0.35

bars_obs = ax.bar([i - width/2 for i in x], [rc.observed_rate for rc in result.rate_comparisons],
                   width, label="Observed", color="#2196F3", alpha=0.8)
bars_sim = ax.bar([i + width/2 for i in x], [rc.simulated_rate for rc in result.rate_comparisons],
                   width, label="Simulated", color="#FF9800", alpha=0.8)

ax.axhline(y=config.rate_tolerance, color="red", linestyle="--", alpha=0.5, label=f"Tolerance ({config.rate_tolerance})")
ax.set_xlabel("Transition")
ax.set_ylabel("Rate")
ax.set_title("Training: Observed vs Simulated Transition Rates")
ax.set_xticks(list(x))
ax.set_xticklabels(targets_labels, rotation=15)
ax.legend()
plt.tight_layout()
plt.show()
```

**Side-by-Side Metrics Table (Section 5):**
```python
print(f"{'Metric':<25} {'Training':>12} {'Holdout':>12}")
print("-" * 50)
print(f"{'MSE':<25} {holdout_result.training_fit.mse:>12.6f} {holdout_result.holdout_fit.mse:>12.6f}")
print(f"{'MAE':<25} {holdout_result.training_fit.mae:>12.6f} {holdout_result.holdout_fit.mae:>12.6f}")
print(f"{'Targets':<25} {holdout_result.training_fit.n_targets:>12d} {holdout_result.holdout_fit.n_targets:>12d}")
print(f"{'All Within Tolerance':<25} {str(holdout_result.training_fit.all_within_tolerance):>12} {str(holdout_result.holdout_fit.all_within_tolerance):>12}")
```

### Static Test File Pattern

Follow `test_epic14_notebook.py` exactly. Key structure:

```python
"""Static checks for the Epic 15 calibration workflow notebook — Story 15.5 / FR52."""

from __future__ import annotations

import json
from pathlib import Path

NOTEBOOK_PATH = (
    Path(__file__).resolve().parents[2]
    / "notebooks" / "guides" / "10_calibration_workflow.ipynb"
)
CI_WORKFLOW_PATH = (
    Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"
)


def _load_notebook() -> dict[str, object]:
    with NOTEBOOK_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _cell_source(cell: dict[str, object]) -> str:
    source = cell.get("source", [])
    if isinstance(source, list):
        return "".join(part for part in source if isinstance(part, str))
    if isinstance(source, str):
        return source
    return ""


def _all_sources(notebook: dict[str, object]) -> str:
    cells = notebook.get("cells", [])
    if not isinstance(cells, list):
        return ""
    return "\n".join(_cell_source(cell) for cell in cells if isinstance(cell, dict))
```

**Required test functions:**
- `test_notebook_exists()` — NOTEBOOK_PATH.exists()
- `test_outputs_cleared()` — all code cells have execution_count=None and outputs=[]
- `test_uses_public_api()` — check for `from reformlab.calibration import (`, `from reformlab.discrete_choice import (`, no `from openfisca`, no `import openfisca`
- `test_required_sections()` — check all section header strings (Section 0 through Section 9)
- `test_key_api_calls()` — check for: `load_calibration_targets(`, `CalibrationEngine(`, `.calibrate()`, `validate_holdout(`, `capture_calibration_provenance(`, `make_calibration_reference(`, `extract_calibrated_parameters(`, `TasteParameters(`, `CostMatrix(`, `RunManifest(`
- `test_ci_includes_notebook()` — CI workflow contains the nbmake line for this notebook

### Cross-Story Dependencies

| Story | Relationship |
|---|---|
| **15.1** | Imports: `load_calibration_targets()`, `CalibrationTargetSet` — load and display training/holdout targets |
| **15.2** | Imports: `CalibrationEngine`, `CalibrationConfig`, `CalibrationResult` — run calibration, display diagnostics |
| **15.3** | Imports: `validate_holdout()`, `HoldoutValidationResult`, `FitMetrics` — holdout validation and side-by-side metrics |
| **15.4** | Imports: `capture_calibration_provenance()`, `make_calibration_reference()`, `extract_calibrated_parameters()` — governance recording and parameter round-trip |
| **14.2** | Imports: `TasteParameters`, `compute_utilities()`, `compute_probabilities()` — using calibrated parameters in simulation |
| **14.1** | Imports: `CostMatrix` — cost matrix construction for calibration input |
| **5.1** | Imports: `RunManifest` — demonstrate manifest construction with calibration assumptions |

### Data Flow

```
Fixture CSVs (training + holdout targets)
       │
       ▼
load_calibration_targets() → CalibrationTargetSet
       │
       ├── Training targets ──────────────────────────────┐
       │                                                   │
       ▼                                                   ▼
CostMatrix + from_states (inline)           CalibrationConfig
       │                                         │
       ▼                                         ▼
CalibrationEngine.calibrate() ──────► CalibrationResult
       │                                    │
       │                                    ├── rate_comparisons → Bar Chart
       │                                    ├── convergence diagnostics → Table
       │                                    │
       │    Holdout CostMatrix + targets    │
       │          │                         │
       ▼          ▼                         ▼
   validate_holdout() ──────────► HoldoutValidationResult
       │                               │
       │                               ├── training_fit vs holdout_fit → Table
       │                               │
       ▼                               ▼
   capture_calibration_provenance(result, target_set, holdout_result)
       │
       ▼
   list[AssumptionEntry] ──► RunManifest(assumptions=entries)
       │
       ▼
   extract_calibrated_parameters(entries, "vehicle")
       │
       ▼
   TasteParameters(beta_cost=calibrated_value)
       │
       ▼
   compute_utilities() → compute_probabilities() → Choice Probability Display
```

### Anti-Patterns from Stories 15.1–15.4 (DO NOT REPEAT)

| Issue | Prevention |
|-------|-----------|
| Notebook cells with stale outputs committed | All cells MUST have `execution_count: null` and `outputs: []` before commit |
| Network calls in notebook | ALL data comes from local fixtures or inline construction — no downloads |
| Missing CI integration | Must add nbmake line to ci.yml AND test it in the static test file |
| Unclear section boundaries | Every section starts with a markdown cell containing `## Section N: Title` |
| Non-deterministic output | `SEED = 42` used wherever randomness occurs; CostMatrix data is fixed |
| Using internal imports | Only use public API from `reformlab.calibration`, `reformlab.discrete_choice`, `reformlab.governance.manifest` |
| Forgetting `from __future__ import annotations` | First line of the first code cell |
| Vague explanations | Each method/concept gets a "What it does" + "Why it matters" explanation before the code |

### Project Structure Notes

- `10_calibration_workflow.ipynb` follows sequential numbering in `notebooks/guides/`
- Fixture CSV `holdout_vehicle_targets.csv` goes in existing `tests/fixtures/calibration/` directory
- Static test file `test_epic15_notebook.py` goes in existing `tests/notebooks/` directory
- CI workflow update is a single line addition to `.github/workflows/ci.yml`
- No new Python source files in `src/` — this story only creates notebook + test + fixture + CI update
- No changes to `pyproject.toml` — all dependencies already present (`nbmake>=1.4`, `matplotlib`)

### Testing Standards Summary

- **Static tests**: Function-level (not class-based) following `test_epic14_notebook.py` pattern exactly
- **Dynamic test**: `pytest --nbmake` executes all cells in fresh kernel
- **Fixture data**: Small CSV files (3-5 rows) for fast CI execution
- **No custom assertions**: Plain `assert` statements
- **Docstrings**: Brief one-line descriptions of what each test validates
- **CI integration**: Both static tests (via `pytest tests/`) and dynamic tests (via `pytest --nbmake`)

### References

- [Source: notebooks/guides/08_discrete_choice_model.ipynb — Section structure, cell patterns, pedagogical style]
- [Source: notebooks/guides/09_population_generation.ipynb — Fixture loading, visualization patterns, governance integration]
- [Source: notebooks/guides/06_portfolio_comparison.ipynb — Comparison visualization, cross-metrics display]
- [Source: tests/notebooks/test_epic14_notebook.py — Static test file pattern (NOTEBOOK_PATH, _load_notebook, _cell_source, _all_sources helpers, test functions)]
- [Source: tests/calibration/conftest.py — make_sample_engine(), make_sample_target_set(), make_holdout_* helpers, CostMatrix construction patterns]
- [Source: src/reformlab/calibration/__init__.py — Public API exports]
- [Source: src/reformlab/calibration/engine.py — CalibrationEngine.calibrate() API]
- [Source: src/reformlab/calibration/validation.py — validate_holdout() API]
- [Source: src/reformlab/calibration/provenance.py — capture/extract/reference functions]
- [Source: src/reformlab/calibration/types.py — CalibrationResult, CalibrationConfig, FitMetrics, RateComparison]
- [Source: src/reformlab/discrete_choice/types.py — TasteParameters, CostMatrix]
- [Source: src/reformlab/discrete_choice/logit.py — compute_utilities(), compute_probabilities()]
- [Source: .github/workflows/ci.yml — CI notebook testing with nbmake]
- [Source: docs/epics.md — Epic 15 / Story 15.5 acceptance criteria]
- [Source: docs/project-context.md — coding conventions, PyArrow-first, determinism]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — implementation was straightforward.

### Completion Notes List

- ✅ Notebook `notebooks/guides/10_calibration_workflow.ipynb` created with 10 sections (0–9), cleared outputs, python3 kernel, deterministic SEED=42
- ✅ Notebook uses simplified 2-alternative (A/B) demo matching conftest pattern; valid_vehicle_targets.csv loaded for format display in Section 1; inline CalibrationTargetSet for actual calibration
- ✅ Holdout CSV `tests/fixtures/calibration/holdout_vehicle_targets.csv` created (3 targets, period=2023, to_states A/B)
- ✅ Static test file `tests/notebooks/test_epic15_notebook.py` created with 6 tests following test_epic14_notebook.py pattern exactly
- ✅ CI workflow updated with nbmake line for 10_calibration_workflow.ipynb
- ✅ All 6 static tests pass
- ✅ Notebook executes via `pytest --nbmake` in 27s without errors
- ✅ Full test suite: 2778 passed, 1 skipped, 0 failures (no regressions)
- ✅ [Code Review Synthesis] `test_uses_public_api()` strengthened to block internal submodule imports (`reformlab.calibration.*`, `reformlab.discrete_choice.*`)
- ✅ [Code Review Synthesis] Notebook s5-validate: hardcoded `rate_tolerance=0.05` replaced with `config.rate_tolerance` for consistency with training configuration
- ✅ [Code Review Synthesis] Notebook s6-reference: `ref_entry` now included in `RunManifest.assumptions` via `manifest_assumptions = [*entries, ref_entry]`; post-fix test suite: 2778 passed, 1 skipped, 0 failures

### File List

New files:
- `notebooks/guides/10_calibration_workflow.ipynb`
- `tests/notebooks/test_epic15_notebook.py`
- `tests/fixtures/calibration/holdout_vehicle_targets.csv`

Modified files:
- `.github/workflows/ci.yml` — add nbmake line for calibration notebook
- `notebooks/guides/10_calibration_workflow.ipynb` — [Code Review] s5-validate: use config.rate_tolerance; s6-reference: include ref_entry in RunManifest
- `tests/notebooks/test_epic15_notebook.py` — [Code Review] strengthen test_uses_public_api() to block internal submodule imports

### Change Log

- 2026-03-07: Story 15.5 created — comprehensive developer guide with section-by-section notebook content, visualization specs, static test patterns, fixture data strategy, and anti-pattern prevention.
- 2026-03-07: Post-validation fixes — (1) AC-3(c) tightened to specify choice probability matrix instead of vague "distributional outcomes"; (2) Task 1.10 corrected to use `compute_utilities()`/`compute_probabilities()` directly (removing inconsistent `LogitChoiceStep` reference that contradicted Section 8 dev notes and Data Flow diagram); (3) `LogitChoiceStep` removed from Key Imports block.
- 2026-03-07: Story implemented — notebook created with 10 sections, holdout CSV created, static tests created, CI updated. All tests pass (2778 passed, 1 skipped).
- 2026-03-07: Code review synthesis — 3 fixes applied: (1) `test_uses_public_api()` now blocks internal submodule imports; (2) holdout `rate_tolerance` derives from `config.rate_tolerance`; (3) `ref_entry` included in `RunManifest.assumptions`. All tests pass (2778 passed, 1 skipped, 0 failures).

## Senior Developer Review (AI)

### Review: 2026-03-07
- **Reviewer:** AI Code Review Synthesis
- **Evidence Score:** 5.15 (average of Reviewer A: 3.5 and Reviewer B: 6.8) → REJECT
- **Issues Found:** 4 verified (1 high, 3 medium)
- **Issues Fixed:** 3
- **Action Items Created:** 1

## Tasks / Subtasks (Review Follow-ups)

#### Review Follow-ups (AI)
- [ ] [AI-Review] MEDIUM: Visualization tolerance line in Section 4 is placed at y=0.05 on the rate axis, which sits below all bars (rates ~0.4–0.6) and is misleading. Consider plotting absolute errors |sim-observed| per target with a threshold line, or updating the markdown to explicitly note the visual limitation. (`notebooks/guides/10_calibration_workflow.ipynb`, cell `s4-chart`)
