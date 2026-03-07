# Epic 15 - Story Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during validation of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent story-writing mistakes (unclear AC, missing Notes, unrealistic scope).

## Story 15-1 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | `source_metadata` declared required in dataclass (Task 2.1) but optional in JSON Schema (Task 3.2), and absent from CSV schema entirely — contract conflict that allows divergent implementations | Made `source_metadata` optional with `field(default_factory=dict)` in Task 2.1; JSON Schema task already had it optional (no change needed there); the dataclass now matches the schema |
| critical | AC-2 says "CSV or YAML" but Task 4.4 explicitly includes `.parquet` extension → format scope conflict | Updated AC-2 to "CSV, Parquet, or YAML"; added `TestParquetLoading` to test task 6.3; added `valid_vehicle_targets.parquet` fixture |
| high | AC-4 error location "field and row" is unambiguous for CSV but maps to nothing in YAML (no row numbers in YAML) — makes AC-4 objectively untestable across formats | AC-4 now specifies `row=N` for CSV/Parquet and `targets[N].field_name` for YAML; Task 4.7 defines the error message format with example |
| high | JSON Schema loaded from `src/reformlab/calibration/schema/` will be missing in installed wheel without explicit packaging configuration | Task 4.3 now specifies `importlib.resources.files()` loading; Project Structure Notes specify `schema/__init__.py` requirement and `pyproject.toml` include pattern; `schema/__init__.py` added to File List |
| medium | `sum ≤ 1.0` consistency check has no floating-point tolerance — boundary values (e.g., `0.1 + 0.1 + 0.8`) can fail due to binary float accumulation | Task 2.4 adds `1e-9` tolerance; Consistency Validation Rule section documents boundary test cases |
| medium | Duplicate `(domain, period, from_state, to_state)` row behavior unspecified — double-counting would silently inflate probability sums | Task 2.4 and Consistency Validation Rule section now specify: duplicates are always a `CalibrationTargetLoadError`, not a validation error |
| medium | JSON Schema type for `source_metadata` was unspecified — allows any object type | Task 3.2 now types `source_metadata` as `{type: object, additionalProperties: {type: string}}` |

## Story 15-2 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | MSE divide-by-zero | Added validation rule 5 to `_validate_inputs()` (Task 5.7 + Input Validation Rules section): total weight must be `> 0.0`; added test case to Task 7.6. |
| critical | AC-3 "fixed seed" is incorrect | Rewrote AC-3 — removed "fixed seed" language; now states "deterministic by construction (no random sampling occurs in objective evaluation; expected probabilities are used, not stochastic draws)." |
| critical | AC-5 "documented threshold" is vague | Updated AC-5 to reference `CalibrationConfig.rate_tolerance` (default 0.05) explicitly. |
| high | Period key missing from duplicate check | Updated Task 5.7 duplicate validation to use `(from_state, to_state)` within the same `period`, explicitly aligning with Story 15.1's uniqueness key `(domain, period, from_state, to_state)`. |
| high | AC-4 ambiguous wording | Changed "optimized β coefficients per domain" → "the optimized β coefficient for the calibrated domain"; added "or `None` for gradient-free methods such as Nelder-Mead" to gradient norm. |
| high | Scipy exceptions not wrapped | Added exception-handling note to scipy.optimize.minimize section: wrap `minimize()` in `try/except Exception as e` and re-raise as `CalibrationOptimizationError`. |
| medium | Vague error message formats | Updated Input Validation Rules items 2 and 3 with concrete example error message format strings (e.g., `f"Unknown to_state values {unknown!r} in domain={domain!r}; expected one of {available!r}"`). |

## Story 15-3 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | Tolerance comparability gap | Added explicit note to AC-4, `validate_holdout()` docstring, `HoldoutValidationResult.rate_tolerance` docstring; renamed `rate_tolerance` → `holdout_rate_tolerance` in `to_governance_entry()` value dict. |
| high | Unweighted metrics never stated | AC-2 now says "unweighted gap metrics"; `compute_fit_metrics()` docstring now says "Compute unweighted aggregate fit metrics" with explicit note that `CalibrationTarget.weight` is not applied. |
| medium | rate_tolerance not validated | Task 3.4 re-lettered with (a) rate_tolerance guard first; algorithm pseudocode now checks `math.isfinite(rate_tolerance) and rate_tolerance > 0.0` before any other logic; `math` added to Key Imports; error test cases added to Task 5.4. |
| medium | No defensive consistency check on holdout targets | Task 3.4 now requires `validate_consistency()` call; `_validate_holdout_inputs()` algorithm now calls it as step 1b; Task 5.4 adds duplicate-holdout-target test case. |
| medium | Ordering of `holdout_rate_comparisons` non-deterministic | Algorithm now sorts by `(from_state, to_state)` before `tuple()` construction; Task 5.3 adds ordering test. |

## Story 15-4 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | `gradient_norm` missing from `CalibrationResult.to_governance_entry()` — AC-1 requires it, field exists on the dataclass, but implementation omits it from the returned dict | Added Task 0 (update `types.py`), updated file layout, updated File List, updated governance entry keys table to include `gradient_norm` |
| high | Duplicate `calibration_result` entries for the same domain in `extract_calibrated_parameters()` produce silent wrong-beta extraction — first match returned with no error | Updated AC-3 to specify duplicate behavior (raise `CalibrationProvenanceError` with count), updated Task 1.5, rewrote algorithm to collect all matches first then check count, added test case to Task 4.5 |
| medium | `source_label` parameter present in algorithm and test requirements but absent from Task 1.2's function signature description | Added `source_label: str = "calibration_engine"` to Task 1.2 signature |
| medium | `optimized_beta_cost` has no type guard — if a non-numeric value is deserialized from manifest, `float()` raises `ValueError` instead of a controlled `CalibrationProvenanceError` | Added `isinstance(beta_cost, (float, int))` guard with `CalibrationProvenanceError` message to algorithm; added test case to Task 4.5 |
| low | Typo `CalibrationProvenance Error` (space) in AC-3 | Corrected to `CalibrationProvenanceError` |

## Story 15-5 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Inconsistent simulation implementation path | Task 1.10 updated to use `compute_utilities()`/`compute_probabilities()` directly, matching the Section 8 dev notes, Data Flow diagram, and visualization specs. `LogitChoiceStep` removed from Key Imports. Evidence: Task 1.10 said "create a `LogitChoiceStep`" while Section 8 guide said "Use extracted TasteParameters with `compute_utilities()` and `compute_probabilities()`" — a contradiction that would produce divergent implementations. |
| medium | "Distributional outcomes" ambiguous in AC-3(c) | AC-3(c) reworded to specify "per-household choice probability matrix computed via `compute_utilities()` and `compute_probabilities()`", matching Task 1.10 (now corrected) and Section 8 guide. |
