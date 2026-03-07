

# Story 15.4: Record Calibrated Parameters in Run Manifests

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **policy analyst**,
I want calibrated discrete choice taste parameters, optimization diagnostics, calibration target metadata, and holdout validation metrics recorded in run manifests, and the ability to reference a calibration run from a simulation run and reload exact β values from a manifest,
so that every simulation using calibrated behavioral parameters has full provenance traceability and I can reproduce results by loading parameters from a prior calibration manifest.

## Acceptance Criteria

1. **AC-1: Calibration provenance in manifest** — Given a completed calibration run (CalibrationResult) and optionally a HoldoutValidationResult and CalibrationTargetSet, when `capture_calibration_provenance()` is called, then the returned assumption entries include: calibrated β coefficients per domain, objective function type and final value, convergence diagnostics (iterations, gradient norm, method), calibration target source metadata (domains, periods, sources, n_targets), and holdout validation metrics (training/holdout MSE, MAE, all_within_tolerance) if provided.
2. **AC-2: Calibration run reference** — Given a simulation run that uses calibrated parameters, when a calibration reference entry is created via `make_calibration_reference()`, then it records the calibration run's manifest_id and optionally its integrity_hash, allowing the simulation manifest to trace back to the calibration that produced its parameters.
3. **AC-3: Parameter extraction round-trip** — Given calibrated parameters recorded in a manifest's assumptions list, when `extract_calibrated_parameters()` is called with the assumptions and domain, then the exact same β value (TasteParameters) is returned. If no calibration result is found for the requested domain, a `CalibrationProvenance Error` is raised.

## Tasks / Subtasks

- [ ] Task 1: Create `provenance.py` module (AC: 1, 2, 3)
  - [ ] 1.1: Create `src/reformlab/calibration/provenance.py` with module docstring referencing Story 15.4 / FR52
  - [ ] 1.2: Implement `capture_calibration_provenance(calibration_result, *, target_set=None, holdout_result=None) -> list[dict[str, Any]]` — aggregates all governance entries from calibration objects (see Dev Notes for algorithm)
  - [ ] 1.3: Implement `make_calibration_reference(calibration_manifest_id, *, calibration_integrity_hash="") -> dict[str, Any]` — creates an AssumptionEntry-compatible dict with key `"calibration_reference"` (see Dev Notes)
  - [ ] 1.4: Implement `extract_calibrated_parameters(assumptions, domain) -> TasteParameters` — scans assumptions list for `"calibration_result"` entry matching domain, extracts `optimized_beta_cost`, returns `TasteParameters(beta_cost=...)` (see Dev Notes)
  - [ ] 1.5: Add input validation: `capture_calibration_provenance()` validates `calibration_result` is a `CalibrationResult`; `extract_calibrated_parameters()` raises `CalibrationProvenanceError` if no matching entry found; `make_calibration_reference()` raises `CalibrationProvenanceError` if `calibration_manifest_id` is empty
  - [ ] 1.6: Add structured logging: `event=calibration_provenance_captured`, `event=calibration_parameters_extracted`

- [ ] Task 2: Add `CalibrationProvenanceError` to `errors.py` (AC: 3)
  - [ ] 2.1: Add `CalibrationProvenanceError(CalibrationError)` to `src/reformlab/calibration/errors.py`

- [ ] Task 3: Update public API in `__init__.py` (AC: all)
  - [ ] 3.1: Add imports and `__all__` entries for: `capture_calibration_provenance`, `make_calibration_reference`, `extract_calibrated_parameters`, `CalibrationProvenanceError`

- [ ] Task 4: Write tests (AC: all)
  - [ ] 4.1: Create `tests/calibration/test_provenance.py` with test classes
  - [ ] 4.2: `TestCaptureCalibrationProvenance`: result-only capture (1 entry), result + target_set (2 entries), result + holdout (2 entries), all three (3 entries), entries have correct keys (`calibration_result`, `calibration_targets`, `holdout_validation`), entries are AssumptionEntry-compatible (key/value/source/is_default), custom source_label propagated
  - [ ] 4.3: `TestCaptureCalibrationProvenanceValidation`: invalid calibration_result type raises TypeError
  - [ ] 4.4: `TestMakeCalibrationReference`: correct structure with manifest_id only, correct structure with manifest_id + integrity_hash, empty manifest_id raises CalibrationProvenanceError, entry has key `"calibration_reference"` and is AssumptionEntry-compatible
  - [ ] 4.5: `TestExtractCalibratedParameters`: round-trip (calibrate → capture → extract → same beta), missing domain raises CalibrationProvenanceError, empty assumptions raises CalibrationProvenanceError, no `calibration_result` key raises CalibrationProvenanceError, multiple domains returns correct one, extracted TasteParameters has exact beta_cost value
  - [ ] 4.6: `TestRoundTrip`: end-to-end integration — run CalibrationEngine.calibrate(), capture provenance, extract parameters, verify identical TasteParameters; verify assumptions pass RunManifest validation (construct a manifest with captured assumptions)

- [ ] Task 5: Lint, type-check, regression (AC: all)
  - [ ] 5.1: `uv run ruff check src/reformlab/calibration/ tests/calibration/` — clean
  - [ ] 5.2: `uv run mypy src/reformlab/calibration/` — clean (exclude pre-existing template error)
  - [ ] 5.3: `uv run pytest tests/` — all tests pass (existing + new)

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**Module location:** `src/reformlab/calibration/provenance.py` — new file in the existing calibration module. Follows the pattern of `calibration/validation.py` (Story 15.3) and `population/assumptions.py` (Story 11.6). No new subdirectories needed.

**Updated module file layout after this story:**
```
src/reformlab/calibration/
├── __init__.py                       # Updated: add new exports
├── types.py                          # No changes
├── errors.py                         # Updated: add CalibrationProvenanceError
├── engine.py                         # No changes
├── validation.py                     # No changes
├── loader.py                         # No changes
├── provenance.py                     # NEW: capture/extract/reference functions
└── schema/
    ├── __init__.py                   # No changes
    └── calibration-targets.schema.json  # No changes
```

**Every file starts with** `from __future__ import annotations`.

**Module docstrings** — `provenance.py` must have a module-level docstring referencing Story 15.4 / FR52.

**Structured logging** — `logging.getLogger(__name__)` with `key=value` format.

**No new dependencies** — uses only existing types from `calibration.types`, `calibration.errors`, `discrete_choice.types`.

### Key Imports

```python
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from reformlab.calibration.errors import CalibrationProvenanceError
from reformlab.calibration.types import (
    CalibrationResult,
    CalibrationTargetSet,
    HoldoutValidationResult,
)

if TYPE_CHECKING:
    from reformlab.discrete_choice.types import TasteParameters
```

Import `TasteParameters` at runtime inside `extract_calibrated_parameters()` (not behind `TYPE_CHECKING` at module level) since the function constructs the object at runtime.

### New Error Type

**`CalibrationProvenanceError` in `errors.py`:**
```python
class CalibrationProvenanceError(CalibrationError):
    """Raised when calibration provenance capture or extraction fails.

    Examples: missing calibration result in manifest assumptions,
    empty manifest ID for calibration reference, domain not found.
    """
```

### Algorithm: `capture_calibration_provenance()`

```python
def capture_calibration_provenance(
    calibration_result: CalibrationResult,
    *,
    target_set: CalibrationTargetSet | None = None,
    holdout_result: HoldoutValidationResult | None = None,
    source_label: str = "calibration_engine",
) -> list[dict[str, Any]]:
    """Aggregate all calibration governance entries for manifest recording.

    Collects assumption entries from the calibration result, and optionally
    from the calibration target set and holdout validation result. Each entry
    follows the AssumptionEntry format (key, value, source, is_default).

    The source_label is propagated to all entries for consistent attribution.

    Args:
        calibration_result: Result from CalibrationEngine.calibrate().
        target_set: Optional CalibrationTargetSet used for calibration.
        holdout_result: Optional HoldoutValidationResult from validation.
        source_label: Source label for all entries. Defaults to
            "calibration_engine".

    Returns:
        List of AssumptionEntry-compatible dicts, sorted by key.

    Raises:
        TypeError: If calibration_result is not a CalibrationResult.

    Story 15.4 / FR52 — Record calibrated parameters in run manifests.
    """
    if not isinstance(calibration_result, CalibrationResult):
        msg = (
            f"calibration_result must be a CalibrationResult, "
            f"got {type(calibration_result).__name__}"
        )
        raise TypeError(msg)

    entries: list[dict[str, Any]] = []

    # 1. Always include calibration result
    entries.append(
        calibration_result.to_governance_entry(source_label=source_label)
    )

    # 2. Optionally include target set metadata
    if target_set is not None:
        entries.append(
            target_set.to_governance_entry(source_label=source_label)
        )

    # 3. Optionally include holdout validation
    if holdout_result is not None:
        entries.append(
            holdout_result.to_governance_entry(source_label=source_label)
        )

    logger.info(
        "event=calibration_provenance_captured domain=%s n_entries=%d",
        calibration_result.domain,
        len(entries),
    )

    return sorted(entries, key=lambda e: e["key"])
```

### Algorithm: `make_calibration_reference()`

```python
def make_calibration_reference(
    calibration_manifest_id: str,
    *,
    calibration_integrity_hash: str = "",
) -> dict[str, Any]:
    """Create an AssumptionEntry-compatible reference to a calibration run.

    Used when a simulation run uses calibrated parameters from a prior
    calibration run. The reference enables traceability from the simulation
    manifest back to the calibration manifest.

    Args:
        calibration_manifest_id: Manifest ID (UUID) of the calibration run.
        calibration_integrity_hash: Optional integrity hash of the calibration
            manifest for tamper-proof verification.

    Returns:
        AssumptionEntry-compatible dict with key "calibration_reference".

    Raises:
        CalibrationProvenanceError: If calibration_manifest_id is empty.

    Story 15.4 / FR52 — Record calibrated parameters in run manifests.
    """
    if not calibration_manifest_id or not calibration_manifest_id.strip():
        raise CalibrationProvenanceError(
            "calibration_manifest_id must be a non-empty string"
        )

    value: dict[str, str] = {
        "calibration_manifest_id": calibration_manifest_id,
    }
    if calibration_integrity_hash:
        value["calibration_integrity_hash"] = calibration_integrity_hash

    return {
        "key": "calibration_reference",
        "value": value,
        "source": "calibration_provenance",
        "is_default": False,
    }
```

### Algorithm: `extract_calibrated_parameters()`

```python
def extract_calibrated_parameters(
    assumptions: list[dict[str, Any]],
    domain: str,
) -> TasteParameters:
    """Extract TasteParameters from manifest assumptions for a given domain.

    Scans the assumptions list for an entry with key "calibration_result"
    whose value["domain"] matches the requested domain. Extracts the
    optimized_beta_cost and returns a TasteParameters instance.

    Args:
        assumptions: List of AssumptionEntry-compatible dicts (from RunManifest).
        domain: Decision domain to extract parameters for (e.g., "vehicle").

    Returns:
        TasteParameters with the exact beta_cost from the calibration result.

    Raises:
        CalibrationProvenanceError: If no calibration_result entry is found
            for the requested domain, or if assumptions is empty.

    Story 15.4 / FR52 — Record calibrated parameters in run manifests.
    """
    from reformlab.discrete_choice.types import TasteParameters

    if not assumptions:
        raise CalibrationProvenanceError(
            "Cannot extract calibrated parameters from empty assumptions list"
        )

    for entry in assumptions:
        if entry.get("key") != "calibration_result":
            continue
        value = entry.get("value", {})
        if value.get("domain") == domain:
            beta_cost = value.get("optimized_beta_cost")
            if beta_cost is None:
                raise CalibrationProvenanceError(
                    f"calibration_result entry for domain={domain!r} is missing "
                    f"'optimized_beta_cost' in value"
                )

            logger.info(
                "event=calibration_parameters_extracted domain=%s beta_cost=%f",
                domain,
                beta_cost,
            )

            return TasteParameters(beta_cost=float(beta_cost))

    raise CalibrationProvenanceError(
        f"No calibration_result entry found for domain={domain!r} "
        f"in assumptions list (checked {len(assumptions)} entries)"
    )
```

### Cross-Story Dependencies

| Story | Relationship |
|---|---|
| **15.1** | Imports: `CalibrationTargetSet` — target metadata recorded via `to_governance_entry()` |
| **15.2** | Imports: `CalibrationResult` — primary input; `to_governance_entry()` provides β, diagnostics |
| **15.3** | Imports: `HoldoutValidationResult` — holdout metrics recorded via `to_governance_entry()` |
| **14.2** | Imports: `TasteParameters` — output of `extract_calibrated_parameters()` |
| **5.1** | Consumer: `RunManifest.assumptions` field receives the captured entries |
| **5.2** | Consumer: Manifest assumptions now include calibration provenance |
| **15.5** | Consumer: Notebook demo uses provenance functions for the calibration workflow |

### Data Flow

```
CalibrationResult          CalibrationTargetSet       HoldoutValidationResult
(from Story 15.2)          (from Story 15.1)          (from Story 15.3)
       │                          │                          │
       ▼                          ▼                          ▼
  .to_governance_entry()   .to_governance_entry()   .to_governance_entry()
       │                          │                          │
       └────────────┬─────────────┴──────────────────────────┘
                    ▼
    capture_calibration_provenance()
    → list[AssumptionEntry-compatible dicts]
                    │
                    ▼
    ┌───────────────────────────────────┐
    │ RunManifest.assumptions           │
    │  ├─ calibration_result            │
    │  ├─ calibration_targets           │
    │  ├─ holdout_validation            │
    │  └─ calibration_reference (opt.)  │
    └───────────────────────────────────┘
                    │
                    ▼
    extract_calibrated_parameters(assumptions, domain)
    → TasteParameters(beta_cost=...)
```

### Governance Entry Keys Summary

| Key | Source Function | Content |
|-----|----------------|---------|
| `calibration_result` | `CalibrationResult.to_governance_entry()` | domain, optimized_beta_cost, objective_type, final_objective_value, convergence_flag, iterations, method, all_within_tolerance, n_targets |
| `calibration_targets` | `CalibrationTargetSet.to_governance_entry()` | domains, n_targets, periods, sources |
| `holdout_validation` | `HoldoutValidationResult.to_governance_entry()` | domain, holdout_rate_tolerance, training {mse, mae, n_targets, all_within_tolerance}, holdout {mse, mae, n_targets, all_within_tolerance} |
| `calibration_reference` | `make_calibration_reference()` | calibration_manifest_id, calibration_integrity_hash (optional) |

### Test Design

**TestCaptureCalibrationProvenance:**
```python
def test_result_only_returns_one_entry(self) -> None:
    """Given only CalibrationResult, returns 1 assumption entry."""
    cal_result = make_sample_engine().calibrate()
    entries = capture_calibration_provenance(cal_result)
    assert len(entries) == 1
    assert entries[0]["key"] == "calibration_result"

def test_all_three_returns_three_sorted_entries(self) -> None:
    """Given result + target_set + holdout, returns 3 sorted entries."""
    cal_result = make_sample_engine().calibrate()
    holdout = validate_holdout(cal_result, ...)
    entries = capture_calibration_provenance(
        cal_result,
        target_set=make_sample_target_set(),
        holdout_result=holdout,
    )
    assert len(entries) == 3
    keys = [e["key"] for e in entries]
    assert keys == sorted(keys)  # alphabetical: calibration_result, calibration_targets, holdout_validation
```

**TestExtractCalibratedParameters (round-trip):**
```python
def test_round_trip_preserves_exact_beta(self) -> None:
    """Given calibrated result → captured → extracted, beta_cost is identical."""
    cal_result = make_sample_engine().calibrate()
    entries = capture_calibration_provenance(cal_result)
    extracted = extract_calibrated_parameters(entries, "vehicle")
    assert extracted.beta_cost == cal_result.optimized_parameters.beta_cost
```

**TestRoundTrip (manifest integration):**
```python
def test_captured_entries_pass_manifest_validation(self) -> None:
    """Given captured provenance entries, they pass RunManifest assumption validation."""
    cal_result = make_sample_engine().calibrate()
    entries = capture_calibration_provenance(cal_result)
    # Construct manifest with these assumptions — must not raise
    manifest = RunManifest(
        manifest_id="test-id",
        created_at="2026-03-07T12:00:00Z",
        engine_version="0.1.0",
        openfisca_version="40.0.0",
        adapter_version="1.0.0",
        scenario_version="v1.0",
        assumptions=entries,
    )
    assert len(manifest.assumptions) == 1
```

### Anti-Patterns from Stories 15.1–15.3 (DO NOT REPEAT)

| Issue | Prevention |
|-------|-----------|
| Contract conflict between dataclass and schema | No new dataclasses — functions return plain dicts matching AssumptionEntry TypedDict |
| Missing floating-point tolerance | `extract_calibrated_parameters()` returns exact float value via `float(beta_cost)` — no approximation |
| Unclear error locations | All `CalibrationProvenanceError` messages include: domain name, number of entries checked, what was expected |
| Vague AC wording | AC-1 lists every field; AC-2 specifies manifest_id + integrity_hash; AC-3 specifies exact round-trip |
| Docstring ordering | Module docstring first, then `from __future__ import annotations` |

### Project Structure Notes

- `provenance.py` is a new file in `src/reformlab/calibration/` — mirrors pattern of `validation.py` (Story 15.3)
- Test file `tests/calibration/test_provenance.py` mirrors the source
- No new test fixture files needed — tests reuse existing conftest helpers (`make_sample_engine()`, `make_holdout_*()`)
- No changes to `pyproject.toml` — no new dependencies
- `CalibrationProvenanceError` added to existing `errors.py` — follows existing error hierarchy pattern (`CalibrationTargetLoadError`, `CalibrationTargetValidationError`, `CalibrationOptimizationError`)

### Testing Standards Summary

- Class-based test grouping: `TestCaptureCalibrationProvenance`, `TestCaptureCalibrationProvenanceValidation`, `TestMakeCalibrationReference`, `TestExtractCalibratedParameters`, `TestRoundTrip`
- Docstrings in Given/When/Then format
- Direct `assert` statements — no custom assertion helpers
- `pytest.raises(CalibrationProvenanceError, match=...)` for error cases
- Inline construction using existing conftest helpers
- Reference story/AC IDs in test comments
- Integration test: calibrate → capture → manifest construction → extract → verify identical TasteParameters

### References

- [Source: docs/epics.md — Epic 15 / Story 15.4 acceptance criteria]
- [Source: docs/project-context.md — coding conventions, frozen dataclasses, AssumptionEntry format]
- [Source: src/reformlab/governance/manifest.py — RunManifest, AssumptionEntry TypedDict, assumptions field validation]
- [Source: src/reformlab/governance/capture.py — capture_assumptions(), capture_discrete_choice_parameters() patterns]
- [Source: src/reformlab/calibration/types.py — CalibrationResult.to_governance_entry(), HoldoutValidationResult.to_governance_entry(), CalibrationTargetSet.to_governance_entry()]
- [Source: src/reformlab/calibration/errors.py — CalibrationError hierarchy]
- [Source: src/reformlab/calibration/validation.py — validate_holdout() for holdout result construction]
- [Source: src/reformlab/discrete_choice/types.py — TasteParameters(beta_cost)]
- [Source: src/reformlab/population/assumptions.py — PipelineAssumptionChain.to_governance_entries() pattern]
- [Source: _bmad-output/implementation-artifacts/15-3-implement-calibration-validation-against-holdout-data.md — Story 15.3 patterns, anti-patterns]

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List

New files:
- `src/reformlab/calibration/provenance.py`
- `tests/calibration/test_provenance.py`

Modified files:
- `src/reformlab/calibration/__init__.py` — add new exports
- `src/reformlab/calibration/errors.py` — add CalibrationProvenanceError

### Change Log

- 2026-03-07: Story 15.4 created — comprehensive developer guide with full algorithm specifications, test design, and anti-pattern prevention.

