---
title: 'Epic 21 Completion — Trust-Status Rules & Debt Fixes'
slug: 'epic-21-completion-trust-status'
created: '2026-03-30'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: [python-3.13, fastapi, pydantic-v2, pyarrow, pytest, mypy-strict, ruff]
files_to_modify: [src/reformlab/data/trust_rules.py, src/reformlab/server/validation.py, src/reformlab/calibration/engine.py, src/reformlab/server/routes/templates.py, tests/data/test_trust_rules.py, tests/server/test_validation_trust.py, tests/calibration/test_engine_trust_guard.py, _bmad-output/implementation-artifacts/sprint-status.yaml]
code_patterns: [frozen-dataclass, validation-check-registry, pure-function-rules, subsystem-exception-hierarchy, literal-type-validation, get_args-runtime-constants]
test_patterns: [mirror-source-structure, class-based-grouping, direct-assertions, pytest-raises-match, conftest-fixtures]
---

# Tech-Spec: Epic 21 Completion — Trust-Status Rules & Debt Fixes

**Created:** 2026-03-30

## Overview

### Problem Statement

Epic 21 is marked "done" but Story 21.5 (trust-status rules) is only ~25% implemented — field extensions exist on CalibrationAsset/ValidationAsset but the core governance enforcement is entirely missing. No runtime trust-status checking exists anywhere in the system. Additionally, 2 broad `except Exception` catches in templates.py violate project conventions, and sprint-status.yaml is desynced from reality.

### Solution

Implement trust-status enforcement as pure functions + existing ValidationCheck registry integration, with calibration engine guard for defense in depth. Fix template exception handling and sprint status. No new protocols, registries, or API endpoints — minimum viable governance using existing patterns.

**Key ADR decisions (from elicitation):**
- **Option B selected**: Preflight + domain guards with shared rule function (not a dedicated engine)
- **Warning-only enforcement**: No hard-blocking — no scenario-level "intent" field exists to determine when blocking is appropriate
- **Asset-level checks only**: Rule function checks individual asset trust_status, no scenario context parameter
- **No transition workflow**: certified_at/certified_by/trust_status_upgradable fields exist but wiring deferred

### Scope

**In Scope:**
- `src/reformlab/data/trust_rules.py` — pure-function trust-status rule evaluation
- Preflight `ValidationCheck` for trust-status (warning-severity, calls rule function)
- Calibration engine guard (warns in log + records in manifest, doesn't block)
- Narrow `except Exception` in templates.py to template subsystem exception hierarchy
- Sprint-status.yaml correction (21.5 status)
- Verify Story 21.6 orchestrator wiring (believed already working)

**Out of Scope:**
- Trust-status transition workflow (certified_at/certified_by wiring)
- Trust-status CRUD API endpoints
- Trust-status registry/rules registry (YAGNI — pure functions suffice)
- Frontend trust-status UI
- Scenario-level `analysis_mode` field (natural next step, but schema change with ripple effects)
- Story 21.4 (verified ~95% complete)
- RunRequest parameters/policy mismatch (verified: no issue)
- PopulationValidator wiring (verified: already integrated)

## Context for Development

### Codebase Patterns

- **ValidationCheck registry**: `register_check()` / `run_checks()` in `validation.py`. Checks are `ValidationCheck` instances wrapping sync/async `check_fn(PreflightRequest) → ValidationCheckResult`. Registered at import time via `register_check()`. `run_checks()` aggregates all checks into `PreflightResponse(passed, checks, warnings)`. Error-severity checks block; warning-severity don't.
- **PreflightRequest structure**: `scenario: dict[str, Any]` (serialized WorkspaceScenario), `population_id: str | None`, `template_name: str | None`. Checks access scenario data via `request.scenario.get("key")` with type guards.
- **Asset loading pattern**: Existing `_check_exogenous_coverage` (validation.py:354-448) loads assets via `load_exogenous_asset(series_name)` from scenario config `request.scenario.get("engineConfig", {}).get("exogenousSeries", [])`. Trust-status check follows same pattern.
- **Trust status Literal**: `DataAssetTrustStatus = Literal["production-safe", "exploratory", "demo-only", "validation-pending", "not-for-public-inference"]` in `descriptor.py:71-77`. Runtime constants via `_VALID_TRUST_STATUSES = get_args(DataAssetTrustStatus)`.
- **Phase support matrix**: `_CURRENT_PHASE_SUPPORTED` in `descriptor.py:119-140` — open-official allows production-safe/exploratory; synthetic-public allows exploratory/demo-only/validation-pending/not-for-public-inference. Enforced at construction.
- **Frozen dataclasses**: All domain types `@dataclass(frozen=True)`, mutate via `dataclasses.replace()`.
- **Subsystem exceptions**: Each module defines own hierarchy. `EvidenceAssetError` in `data/errors.py`. `CalibrationError` → `CalibrationOptimizationError` in `calibration/errors.py`. `TemplateError`/`ScenarioError` in `templates/exceptions.py`.
- **`from __future__ import annotations`** in every file. `if TYPE_CHECKING:` guards for annotation-only imports.
- **CalibrationEngine**: `@dataclass(frozen=True)` with `config: CalibrationConfig`. `calibrate()` → `CalibrationResult`. Raises `CalibrationOptimizationError`. Guard should go before `_validate_inputs()` call at line ~315.

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `src/reformlab/data/descriptor.py` | `DataAssetDescriptor`, `DataAssetTrustStatus` Literal, `_CURRENT_PHASE_SUPPORTED` matrix |
| `src/reformlab/data/errors.py` | `EvidenceAssetError` base exception |
| `src/reformlab/data/assets.py` | `CalibrationAsset`, `ValidationAsset`, `ExogenousAsset`, `StructuralAsset` |
| `src/reformlab/server/validation.py` | `ValidationCheck`, `register_check()`, `run_checks()`, built-in checks pattern |
| `src/reformlab/server/models.py` | `PreflightRequest`, `PreflightResponse`, `ValidationCheckResult` |
| `src/reformlab/server/routes/templates.py:106,127` | Broad `except Exception` catches to narrow |
| `src/reformlab/calibration/engine.py` | `CalibrationEngine.calibrate()` — guard insertion point |
| `src/reformlab/calibration/errors.py` | `CalibrationError` hierarchy |
| `src/reformlab/templates/exceptions.py` | `TemplateError`, `ScenarioError` — catch targets |
| `src/reformlab/data/exogenous_loader.py` | `load_exogenous_asset()` — pattern for asset loading in checks |
| `src/reformlab/orchestrator/runner.py:99-109` | ExogenousContext → YearState.data wiring (confirmed working) |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | Sprint status to correct |

### Technical Decisions

1. **Rule function is pure**: `check_asset_trust(descriptor: DataAssetDescriptor) -> TrustCheckResult` — no state, no side effects, no scenario context parameter.
2. **TrustCheckResult**: Frozen dataclass with `status: Literal["ok", "warning"]`, `message: str`, `asset_id: str`, `trust_status: str` — no "block" status without scenario intent.
3. **Preflight check is warning-severity**: Loads all scenario assets (population, exogenous, calibration targets), evaluates each via `check_asset_trust()`, aggregates into single `ValidationCheckResult`. Warning-severity, never blocks.
4. **Calibration guard logs + manifests**: `CalibrationEngine.calibrate()` checks trust status of calibration targets before optimization. Logs warning via `logger.warning()`. Records trust warnings in `CalibrationResult.metadata`. Does NOT block execution.
5. **Template exception narrowing**: Catch `(TemplateError, ScenarioError, yaml.YAMLError, jsonschema.ValidationError, OSError)` instead of bare `Exception`. `OSError` covers `FileNotFoundError`/`PermissionError`. No `TemplateLoadError` exists — `TemplateError` is the base.
6. **Story 21.6 orchestrator wiring CONFIRMED**: `OrchestratorConfig.exogenous` → `initial_data["exogenous_context"]` → `YearState.data["exogenous_context"]` at runner.py:99-109. No fix needed.

## Implementation Plan

### Tasks

#### Phase 1: Core Trust Rules Module (dependency: none)

- [ ] Task 1: Create `src/reformlab/data/trust_rules.py` — trust-status rule evaluation
  - File: `src/reformlab/data/trust_rules.py` (NEW)
  - Action: Create module with:
    - Module docstring referencing Story 21.5
    - `from __future__ import annotations`
    - Import `DataAssetDescriptor`, `DataAssetTrustStatus` from `descriptor.py`; `TYPE_CHECKING` guard for type-only imports
    - `@dataclass(frozen=True) class TrustCheckResult` with fields: `asset_id: str`, `trust_status: str`, `status: Literal["ok", "warning"]`, `message: str`
    - `_NON_PRODUCTION_STATUSES: tuple[str, ...] = ("exploratory", "demo-only", "validation-pending", "not-for-public-inference")` module-level constant
    - `def check_asset_trust(descriptor: DataAssetDescriptor) -> TrustCheckResult` — pure function:
      - If `descriptor.trust_status == "production-safe"` → return `TrustCheckResult(status="ok", message="Asset '{name}' is production-safe")`
      - Otherwise → return `TrustCheckResult(status="warning", message="Asset '{name}' has trust status '{trust_status}' — results should be treated as {trust_status}")
    - `def check_multiple_assets(descriptors: tuple[DataAssetDescriptor, ...]) -> tuple[TrustCheckResult, ...]` — convenience wrapper, returns tuple of results
    - `def summarize_trust_warnings(results: tuple[TrustCheckResult, ...]) -> str | None` — returns human-readable summary of all warnings, or `None` if all ok
  - Notes: Keep it minimal. No scenario context. No blocking logic. Pure functions only.

- [ ] Task 2: Create `tests/data/test_trust_rules.py` — unit tests for trust rules
  - File: `tests/data/test_trust_rules.py` (NEW)
  - Action: Create test module with:
    - `class TestCheckAssetTrust`: Test each of the 5 trust statuses → correct status/message. Use inline `DataAssetDescriptor` construction with minimal required fields.
    - `class TestCheckMultipleAssets`: Test mixed statuses, all-ok, all-warning, empty tuple.
    - `class TestSummarizeTrustWarnings`: Test summary generation: no warnings → None, single warning → message, multiple warnings → joined message.
  - Notes: Use `_CURRENT_PHASE_SUPPORTED` valid combinations for test descriptors. Don't test invalid descriptors (that's descriptor.py's job).

#### Phase 2: Preflight Integration (dependency: Task 1)

- [ ] Task 3: Add trust-status preflight check to `src/reformlab/server/validation.py`
  - File: `src/reformlab/server/validation.py` (MODIFY)
  - Action:
    - Add import: `from reformlab.data.trust_rules import check_asset_trust, summarize_trust_warnings, TrustCheckResult as AssetTrustResult` (aliased to avoid confusion with `ValidationCheckResult`)
    - Add import: `from reformlab.data.exogenous_loader import load_exogenous_asset` (already imported for exogenous-coverage check — verify, may already be there)
    - Create `_check_trust_status(request: PreflightRequest) -> ValidationCheckResult` function:
      - Extract exogenous series from `request.scenario.get("engineConfig", {}).get("exogenousSeries", [])`
      - Load each exogenous asset via `load_exogenous_asset(name)`, collect descriptors
      - Extract population descriptor if available from scenario (via `request.scenario.get("populationDescriptor")` or load from population_id)
      - Call `check_asset_trust()` on each descriptor
      - Use `summarize_trust_warnings()` to build message
      - If any warnings → return `ValidationCheckResult(id="trust-status", label="Evidence trust status", passed=False, severity="warning", message=summary)`
      - If all ok → return `ValidationCheckResult(id="trust-status", label="Evidence trust status", passed=True, severity="warning", message="All evidence assets are production-safe")`
    - Register check in `_register_builtin_checks()`: `register_check(ValidationCheck(check_id="trust-status", label="Evidence trust status", severity="warning", check_fn=_check_trust_status))`
    - Wrap asset loading in try/except to gracefully handle missing assets (return passed=True with "Could not verify trust status" message if loading fails)
  - Notes: Warning-severity means it never blocks execution. Follow the exact pattern of `_check_exogenous_coverage`. Handle missing/unloadable assets gracefully — don't fail the entire preflight because one descriptor can't be loaded.

- [ ] Task 4: Create `tests/server/test_validation_trust.py` — preflight trust check tests
  - File: `tests/server/test_validation_trust.py` (NEW)
  - Action:
    - `class TestTrustStatusPreflightCheck`:
      - Test with scenario containing all production-safe exogenous assets → passed=True
      - Test with scenario containing mixed trust statuses → passed=False, severity="warning", message includes warning summary
      - Test with scenario containing no exogenous series → passed=True (nothing to check)
      - Test with scenario containing unloadable series name → passed=True with graceful message
    - Use mock/patch for `load_exogenous_asset` to avoid filesystem dependency
  - Notes: Follow existing test patterns in `tests/server/`.

#### Phase 3: Calibration Engine Guard (dependency: Task 1)

- [ ] Task 5: Add trust-status guard to `src/reformlab/calibration/engine.py`
  - File: `src/reformlab/calibration/engine.py` (MODIFY)
  - Action:
    - Add import: `from reformlab.data.trust_rules import check_asset_trust, summarize_trust_warnings` (inside `if TYPE_CHECKING:` if only used for type annotations; at top level since used at runtime)
    - In `calibrate()` method, BEFORE the `_validate_inputs()` call (~line 315):
      - Check if `self.config` exposes calibration target descriptors. If `CalibrationConfig` has asset descriptors accessible, extract them. If not, this guard checks `self.config.targets` metadata if trust_status is available.
      - If descriptors available: call `check_asset_trust()` on each, call `summarize_trust_warnings()`
      - If warnings: `logger.warning("trust_status_check event=calibration_trust_warning %s", summary)`
      - Store warnings in a local variable to include in `CalibrationResult.metadata` later
    - In the `CalibrationResult` construction (~line 548-573):
      - Add `"trust_warnings": trust_summary` to metadata dict if trust_summary is not None
  - Notes: This guard NEVER blocks calibration. It logs and records. If descriptors are not accessible from CalibrationConfig, document this as a known gap and add a `# TODO: Story 21.5 — wire asset descriptors into CalibrationConfig for trust-status guard` comment instead of force-fitting it.

- [ ] Task 6: Create `tests/calibration/test_engine_trust_guard.py` — calibration guard tests
  - File: `tests/calibration/test_engine_trust_guard.py` (NEW)
  - Action:
    - `class TestCalibrationTrustGuard`:
      - Test calibration with production-safe targets → no warning in logs, no trust_warnings in metadata
      - Test calibration with exploratory targets → warning logged, trust_warnings in metadata, calibration still completes successfully
    - Use existing calibration test fixtures from `tests/calibration/conftest.py`
  - Notes: May need to check how CalibrationConfig currently provides target metadata. If descriptors aren't accessible, write a simpler test that verifies the guard code path exists but documents the gap.

#### Phase 4: Template Exception Narrowing (dependency: none, parallel with Phase 1-3)

- [ ] Task 7: Narrow `except Exception` catches in `src/reformlab/server/routes/templates.py`
  - File: `src/reformlab/server/routes/templates.py` (MODIFY)
  - Action:
    - Add imports at top: `from reformlab.templates.exceptions import TemplateError, ScenarioError` and `import yaml` and `import jsonschema` (verify which are already imported)
    - Line ~106: Replace `except Exception:` with `except (TemplateError, ScenarioError, yaml.YAMLError, jsonschema.ValidationError, OSError):`
    - Line ~127: Replace `except Exception:` with `except (TemplateError, ScenarioError, yaml.YAMLError, jsonschema.ValidationError, OSError):`
    - Keep the `logger.warning(...)` calls unchanged
  - Notes: `OSError` covers `FileNotFoundError`, `PermissionError`, `IsADirectoryError`. `yaml.YAMLError` is the base for all PyYAML parse errors. `jsonschema.ValidationError` covers schema validation failures. This is the complete set of exceptions that `load_scenario_template()` can reasonably raise during boot-time template loading.

#### Phase 5: Sprint Status Correction (dependency: none, parallel)

- [ ] Task 8: Correct sprint-status.yaml to reflect actual implementation state
  - File: `_bmad-output/implementation-artifacts/sprint-status.yaml` (MODIFY)
  - Action:
    - Change `epic-21: done` to `epic-21: in-progress`
    - Change Story 21.5 status from `done` to `in-progress` with a comment: `# ~25% complete — trust-status rules engine missing (see tech-spec-epic-21-completion-trust-status.md)`
    - Update `last_updated` timestamp to current date
  - Notes: Stories 21.4 and 21.6 verified as substantially complete — leave as "done". Only 21.5 is genuinely incomplete.

#### Phase 6: Quality Gates (dependency: all above)

- [ ] Task 9: Run full quality checks
  - Action: Run all quality gates and fix any issues:
    - `uv run ruff check src/ tests/`
    - `uv run mypy src/`
    - `uv run pytest tests/`
  - Notes: All must pass. Fix any lint, type, or test failures introduced by the changes.

### Acceptance Criteria

- [ ] AC 1: Given a `DataAssetDescriptor` with `trust_status="production-safe"`, when `check_asset_trust()` is called, then the result has `status="ok"`.

- [ ] AC 2: Given a `DataAssetDescriptor` with `trust_status="exploratory"` (or any non-production-safe status), when `check_asset_trust()` is called, then the result has `status="warning"` and `message` includes the trust status value.

- [ ] AC 3: Given a `PreflightRequest` with a scenario containing exogenous series that have mixed trust statuses, when preflight validation runs, then the `trust-status` check returns `passed=False`, `severity="warning"`, and the message summarizes which assets have non-production trust status.

- [ ] AC 4: Given a `PreflightRequest` with a scenario where all assets are production-safe, when preflight validation runs, then the `trust-status` check returns `passed=True`.

- [ ] AC 5: Given a `PreflightRequest` with a scenario that has no exogenous series configured, when preflight validation runs, then the `trust-status` check returns `passed=True` (nothing to check).

- [ ] AC 6: Given a `CalibrationEngine` configured with calibration targets that have non-production-safe trust status, when `calibrate()` is called, then a warning is logged AND calibration completes successfully (not blocked) AND `CalibrationResult.metadata` contains `trust_warnings` key.

- [ ] AC 7: Given `templates.py` with the narrowed exception catches, when a template file has corrupted YAML, then `yaml.YAMLError` is caught and logged (not a bare `Exception`). When an unexpected exception type occurs (e.g., `RuntimeError`), it propagates instead of being silently swallowed.

- [ ] AC 8: Given the sprint-status.yaml file, when it is read, then Story 21.5 shows `in-progress` status (not `done`) and Epic 21 shows `in-progress`.

- [ ] AC 9: Given the full test suite, when `uv run pytest tests/` is run, then all tests pass including the new trust-rules, preflight-trust, and calibration-guard tests.

## Additional Context

### Dependencies

- `DataAssetDescriptor` and `DataAssetTrustStatus` Literal (Story 21.1 — done, descriptor.py)
- `ValidationCheck` registry pattern (validation.py — done)
- `CalibrationAsset`/`ValidationAsset` field extensions (Story 21.5 Task 1 — done, assets.py)
- `TemplateError`/`ScenarioError` exceptions (templates/exceptions.py — verified)
- `load_exogenous_asset()` loader (data/exogenous_loader.py — done)
- `CalibrationEngine.calibrate()` method (calibration/engine.py — done)

### Testing Strategy

- **Unit tests** (`tests/data/test_trust_rules.py`): All 5 trust statuses × `check_asset_trust()` = ok/warning. Edge cases: reserved statuses, combined asset checks.
- **Preflight integration** (`tests/server/test_validation_trust.py`): Register trust check, mock PreflightRequest with scenario containing assets of various trust statuses, verify warning-severity results.
- **Calibration guard** (`tests/calibration/test_engine_trust_guard.py`): CalibrationEngine with exploratory-trust calibration targets → logs warning, records in metadata, still completes calibration.
- **Template exception narrowing**: Existing template tests should still pass. Add one test with a corrupted YAML to verify specific exception catch.

### Notes

- **Story 21.6 orchestrator wiring CONFIRMED**: `OrchestratorConfig.exogenous` → `initial_data["exogenous_context"]` → `YearState.data` at runner.py:99-109. No fix needed.
- **Retro corrections**: RunRequest parameters/policy mismatch is phantom (clean `policy` field only). PopulationValidator is properly wired. Only `except Exception` (2 instances) and sprint-status desync are real debt.
- **Population asset loading**: The preflight trust check needs to load population descriptors. `_get_descriptor()` in populations.py:577 shows the pattern — load `descriptor.json` or create default. The check can use similar logic or access population trust_status from the scenario dict if it's already serialized there.
