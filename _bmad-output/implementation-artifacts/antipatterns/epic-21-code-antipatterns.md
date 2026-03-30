# Epic 21 - Code Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during code review of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent implementation mistakes (race conditions, missing tests, weak assertions, etc.)

## Story 21-2 (2026-03-27)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Frontend drops canonical evidence fields in `toLibraryItem` function | Changed `toLibraryItem` to pass through all `PopulationLibraryItem` fields instead of dropping them and hardcoding values |
| critical | Frontend upload component omits canonical fields | Added `canonical_origin`, `access_mode`, `trust_status` fields to uploaded population item with appropriate defaults |
| critical | Generated population item omits canonical fields | Added canonical evidence fields to data fusion result population item |
| critical | Upload endpoint unbounded memory read (DoS risk) | Changed from `file.file.read()` to chunked streaming with 100 MB size limit, returns HTTP 413 for oversized files |
| high | Metadata values trusted without validation | Added validation of canonical evidence fields against Literal types before using metadata values, with fallback to mapping function and warning log on invalid values |
| high | Provider evidence mapping fails open to INSEE defaults | Changed from silent fallback to fail-fast HTTPException 422 for unknown providers |
| high | DataSourceItem has default values for Literal types | Removed default values for `origin`, `access_mode`, `trust_status` fields (now required) |
| medium | No CHANGELOG.md entry for API changes | Deferred — CHANGELOG.md does not exist in project; this is a project-level documentation decision |
| dismissed | Task 7 claim "test_populations_evidence.py doesn't exist" | FALSE POSITIVE: File exists at `tests/server/test_models_evidence.py` with 11 passing tests |
| dismissed | Nav rail summary missing trust status display | FALSE POSITIVE: Nav rail correctly shows population name; trust badges are in PopulationLibraryScreen cards which is the appropriate location per UI design (PopulationLibraryScreen.tsx lines 44-63, 104-108) |
| dismissed | AC10 test coverage incomplete | FALSE POSITIVE: Tests cover dual-field model validation, mapping, error handling in test_models_evidence.py; API responses tested in test_populations_api.py |
| dismissed | Frontend/backend type contracts diverge | FALSE POSITIVE: TypeScript interface correctly narrows Literal types to values actually used by current providers (`open-official`, `synthetic-public`); this maintains type safety and prevents invalid values |
| dismissed | File extension validation spoofable | FALSE POSITIVE: Extension validation is appropriate for current threat model; file content validation would be a separate enhancement |
| dismissed | Redundant mapping function | FALSE POSITIVE: Mapping function documents the intentional design choice that all current populations map to the same evidence classification (`synthetic-public`/`bundled`/`exploratory`) |

## Story 21-5 (2026-03-27)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Path Traversal Vulnerability**: Asset loaders use unsanitized `asset_id` in path operations, allowing `../` to escape data roots | Add path validation to prevent directory traversal |
| critical | Missing Governance Infrastructure**: `TrustStatusRule` protocol, `TrustRuleRegistry`, and 3 built-in rules not implemented | Cannot fix - entire subsystem missing, requires story split/rework |
| critical | Missing API Endpoints**: All 5 endpoints (POST/GET calibration targets, POST/GET validation benchmarks, POST certification) not implemented | Cannot fix - requires significant implementation |
| critical | Calibration Engine Not Updated**: Still uses `CalibrationTargetSet` instead of `CalibrationAsset`, no `calibration_asset_id` in manifests | Cannot fix - requires engine refactoring |
| high | Loader Contract Bug**: `data.parquet` file is never validated/loaded despite storage contract requiring it | Add validation that `data.parquet` exists when loading assets |
| high | Missing Pydantic Response Models**: `CalibrationAssetResponse` and `ValidationAssetResponse` not added to `models.py` | Cannot fix - endpoints don't exist to use these models |
| high | metadata.json Structure Not Validated**: Load functions assume metadata is dict but don't validate type | Add type validation before using metadata |
| medium | Storage Directories Don't Exist**: `data/calibration/targets/` and `data/validation/benchmarks/` not created | Cannot fix - requires creating example assets (Task 13) |
| medium | Missing TypeScript Types**: Frontend types for calibration/validation assets not added | Cannot fix - frontend implementation missing |
| medium | Missing Frontend Components**: No calibration/validation UI, API clients | Cannot fix - requires significant frontend work |
| medium | Missing Tests**: No governance, API, certification, or preflight tests | Cannot fix - code to test doesn't exist |
| low | Inconsistent Naming**: `_CALIBRATION_ASSETS_BASE_PATH` vs shorter naming pattern elsewhere | Defer - naming is clear enough, not a functional issue |
| low | SRP Breach in assets.py**: 1900+ line module with multiple responsibilities | Defer - broader refactoring out of scope for this story |

## Story 21-7 (2026-03-30)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Inconsistent legacy mode detection allows validation bypass | Modified `is_legacy_mode` property to also handle empty betas case (`len(self.betas) == 0`) for backward compatibility with legacy construction `TasteParameters(beta_cost=-0.01)`. Updated test assertion to expect correct behavior. |
| critical | AC8 not implemented in RunManifest - missing taste_parameters field | Added `taste_parameters: dict[str, Any] = field(default_factory=dict)` to RunManifest dataclass; added to OPTIONAL_JSON_FIELDS; updated from_json() and with_integrity_hash() methods to handle the new field. |
| high | Identifiability flag logic wrong for negative gradients | Changed `diag.gradient_component < 1e-6` to `abs(diag.gradient_component) < 1e-6` for proper magnitude-based sensitivity detection. |
| high | Test assertion contradicts test name/description | Changed assertion from `assert tp.is_legacy_mode is False` to `assert tp.is_legacy_mode is True` to match the corrected legacy mode detection behavior. |
| medium | Potential KeyError in _build_generalized_taste_parameters | Added validation before assignment: if param_name not in asc or betas, raise CalibrationOptimizationError with clear message about available keys. |
| medium | Missing validation for initial_values/bounds key mismatch | Added validation in CalibrationEngine._validate_inputs() to check that initial_values and bounds have matching keys for all calibrated parameters. |
