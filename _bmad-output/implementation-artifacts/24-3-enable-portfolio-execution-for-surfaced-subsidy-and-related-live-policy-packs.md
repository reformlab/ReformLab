# Story 24.3: Enable portfolio execution for surfaced subsidy and related live policy packs

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a ReformLab developer,
I want surfaced subsidy-family policies (subsidy, vehicle_malus, energy_poverty_aid) to execute correctly within policy portfolios through the live runtime,
so that analysts can create and run portfolios containing these policies with full validation, normalization, and comparison support.

## Acceptance Criteria

1. Given a portfolio containing surfaced live-capable packs (carbon_tax, subsidy, rebate, feebate, vehicle_malus, energy_poverty_aid), when validated, then compatibility checks behave consistently with existing portfolio rules without errors.
2. Given a portfolio containing a surfaced subsidy-family pack (subsidy, vehicle_malus, energy_poverty_aid), when executed through the live runtime, then each policy is translated before adapter invocation and produces normalized results.
3. Given baseline-versus-portfolio comparison, when computed with portfolios containing surfaced policies, then the comparison API endpoints return successful responses with normalized output columns for surfaced policy types.
4. Given a portfolio containing any policy marked as `live_unavailable` for runtime execution, when a run request is submitted with `runtime_mode=live`, then the system blocks with 422 error before execution rather than failing deep in the runtime. For `runtime_mode=replay`, availability checks are bypassed.
5. Given a portfolio execution containing surfaced subsidy-family policies, when completed, then results include the expected output variables for each policy type present, with French field names normalized to English (e.g., montant_subvention → subsidy_0_subsidy_amount).
6. Given portfolio execution with surfaced policies, when the panel output is inspected, then the merged table includes all expected columns from each policy with prefixing applied in the order: normalization first, then policy-type+index prefixing (e.g., subsidy_0_subsidy_amount, vehicle_malus_1_vehicle_malus).
7. Given portfolios with multiple policies of the same type (e.g., two subsidy policies), when executed, then results are properly prefixed with type+index to avoid column name conflicts (existing behavior, non-regression).
8. Given existing carbon_tax, rebate, and feebate portfolio execution, when run after this story's implementation, then they continue to execute without errors or behavioral changes (non-regression).

## Tasks / Subtasks

- [ ] Integrate translation into PortfolioComputationStep (AC: #2, #5)
  - [ ] Import `translate_policy` from `reformlab.computation.translator` in portfolio_step.py
  - [ ] Apply translation to each policy before invoking adapter in `execute()` method
  - [ ] Handle TranslationError with PortfolioComputationStepError wrapping for consistent error reporting
  - [ ] Add unit tests for translation integration in portfolio execution context

- [ ] Add runtime availability validation for portfolios (AC: #1, #4)
  - [ ] Create `_check_portfolio_runtime_availability()` validation check function in validation.py
  - [ ] Register the check in `_register_builtin_checks()` with severity "error"
  - [ ] Check that all policies in portfolio are `live_ready` before execution (only for `runtime_mode=live`)
  - [ ] Return actionable error message identifying which policy types are unavailable
  - [ ] Add unit tests for portfolio runtime availability validation

- [ ] Extend portfolio route to handle CustomPolicyType policies (CRITICAL)
  - [ ] Modify `_build_policy_config()` in routes/portfolios.py to use `get_policy_type()` for CustomPolicyType resolution
  - [ ] Add parameter class registry lookup for custom types (vehicle_malus, energy_poverty_aid)
  - [ ] Keep runtime availability check for portfolio creation/update
  - [ ] Add tests for building vehicle_malus and energy_poverty_aid policies

- [ ] Extend portfolio composition validation for surfaced types (AC: #1)
  - [ ] Verify `validate_compatibility()` works correctly with subsidy-family policy types
  - [ ] Verify `get_policy_type()` correctly resolves CustomPolicyType values for subsidy, vehicle_malus, energy_poverty_aid
  - [ ] Add integration tests for portfolio validation with surfaced policy types

- [ ] Ensure normalization works for portfolio results (AC: #5, #6)
  - [ ] Verify that portfolio merged results pass through existing normalization in PanelOutput
  - [ ] Confirm that subsidy-family output variables are correctly normalized in portfolio context
  - [ ] Add integration tests verifying normalized column names in portfolio output

- [ ] Verify comparison and indicator flows work with surfaced policies (AC: #3)
  - [ ] Test portfolio comparison API endpoints with surfaced subsidy-family policies
  - [ ] Verify indicator computation produces correct results for portfolios containing surfaced policies
  - [ ] Add integration tests for end-to-end portfolio execution, normalization, and comparison

- [ ] Add non-regression tests (AC: #7, #8)
  - [ ] Test existing portfolio execution with carbon_tax, rebate, feebate only
  - [ ] Verify no behavioral changes to existing portfolio execution patterns
  - [ ] Test duplicate policy type prefixing behavior is preserved

#### Review Follow-ups (AI)
- [ ] [AI-Review] MEDIUM: Create missing integration test file `tests/server/test_portfolio_execution_integration.py` — Story specifies end-to-end integration tests for AC-3 (comparison/indicators with surfaced policies) but file was never created (tests/server/test_portfolio_execution_integration.py)

## Dev Notes

### Architecture Context

**Key Design Principle:** Portfolio execution must apply the same translation logic as single-policy scenarios. The translation boundary introduced in Story 24.2 must be integrated into `PortfolioComputationStep` so that each policy in a portfolio is validated and translated before being passed to the adapter.

**Prerequisite:** Story 24.2 must be merged and stable before starting this story. The translator API and runtime availability classification from Story 24.2 are required dependencies.

**Current Flow:** `_run_portfolio()` → `PortfolioComputationStep.execute()` → loops over policies calling `adapter.compute()`. No translation.

**This Story:** Add `translate_policy()` call before `adapter.compute()` in the policy loop. Handle `TranslationError` with `PortfolioComputationStepError`.

### Translation Integration in PortfolioComputationStep

**File:** `src/reformlab/orchestrator/portfolio_step.py`

**Changes Required:**
1. Import translation function:
```python
from reformlab.computation.translator import translate_policy, TranslationError
from dataclasses import replace
```

2. Modify `execute()` method to translate each policy before adapter invocation:
```python
# In execute() policy loop:
for i, policy_cfg in enumerate(self._portfolio.policies):
    # Story 24.3: Translate domain policy for live execution
    try:
        translated_policy = translate_policy(policy_cfg.policy, f"{self._portfolio.name}[{i}]")
        translated_cfg = replace(policy_cfg, policy=translated_policy)
        comp_policy = _to_computation_policy(translated_cfg)
    except TranslationError as exc:
        raise PortfolioComputationStepError(
            f"Translation failed: {exc.what}",
            year=year, adapter_version=adapter_version,
            policy_index=i, policy_name=policy_name, policy_type=policy_type_value,
            original_error=exc,
        ) from exc
    # ... rest of execution
```

**Critical:** Do NOT modify `_to_computation_policy()` signature. Use `dataclasses.replace()` to create a modified config with the translated policy, then pass it through the existing `_to_computation_policy()` function unchanged.

### Runtime Availability Validation

**File:** `src/reformlab/server/validation.py`

**New Validation Check:**
```python
def _check_portfolio_runtime_availability(request: PreflightRequest) -> ValidationCheckResult:
    """Story 24.3 / AC-4: Validate portfolio policies are live-ready.

    Checks that all policies in the selected portfolio have runtime_availability='live_ready'.
    Blocks execution if any policy is unavailable for live execution.

    NOTE: This check only applies to runtime_mode=live. For runtime_mode=replay,
    availability is bypassed.
    """
    from reformlab.server.dependencies import get_registry
    from reformlab.templates.portfolios.portfolio import PolicyPortfolio
    from reformlab.templates.registry import RegistryError, ScenarioNotFoundError

    portfolio_name = request.scenario.get("portfolioName")
    if not portfolio_name:
        return ValidationCheckResult(
            id="portfolio-runtime-availability",
            label="Portfolio runtime availability",
            passed=True,
            severity="error",
            message="No portfolio selected",
        )

    registry = get_registry()
    try:
        entry = registry.get(portfolio_name)
    except (KeyError, ScenarioNotFoundError, RegistryError):
        return ValidationCheckResult(
            id="portfolio-runtime-availability",
            label="Portfolio runtime availability",
            passed=False,
            severity="error",
            message=f"Portfolio '{portfolio_name}' not found in registry",
        )

    if not isinstance(entry, PolicyPortfolio):
        return ValidationCheckResult(
            id="portfolio-runtime-availability",
            label="Portfolio runtime availability",
            passed=True,
            severity="error",
            message=f"'{portfolio_name}' is not a portfolio",
        )

    # Check runtime availability for each policy
    # Runtime availability is determined by policy type
    # Story 24.2: subsidy, vehicle_malus, energy_poverty_aid are now live_ready
    from reformlab.server.routes.templates import LIVE_READY_TYPES

    unavailable_policies = []
    for i, policy_cfg in enumerate(entry.policies):
        if policy_cfg.policy_type is None:
            continue
        policy_type_str = policy_cfg.policy_type.value
        if policy_type_str not in LIVE_READY_TYPES:
            policy_name = policy_cfg.name or policy_type_str
            unavailable_policies.append(f"  - policy[{i}]: '{policy_name}' ({policy_type_str})")

    if unavailable_policies:
        unavailable_list = "\n".join(unavailable_policies)
        return ValidationCheckResult(
            id="portfolio-runtime-availability",
            label="Portfolio runtime availability",
            passed=False,
            severity="error",
            message=(
                f"Portfolio '{portfolio_name}' contains policies unavailable for live execution:\n"
                f"{unavailable_list}\n"
                f"Supported types for live execution: {', '.join(sorted(LIVE_READY_TYPES))}"
            ),
        )

    policy_count = entry.policy_count
    return ValidationCheckResult(
        id="portfolio-runtime-availability",
        label="Portfolio runtime availability",
        passed=True,
        severity="error",
        message=f"All {policy_count} policies in portfolio are live-ready",
    )
```

**Register the check in `_register_builtin_checks()`:**
```python
ValidationCheck(
    check_id="portfolio-runtime-availability",
    label="Portfolio runtime availability",
    severity="error",
    check_fn=_check_portfolio_runtime_availability,
),
```

### Portfolio Route CustomPolicyType Support

**File:** `src/reformlab/server/routes/portfolios.py`

**CRITICAL:** The current `_build_policy_config()` function only handles PolicyType enum values. It must be extended to handle CustomPolicyType values like `vehicle_malus` and `energy_poverty_aid`.

**Current Limitation:**
```python
try:
    policy_type = PolicyType(req.policy_type)  # Fails for CustomPolicyType
except ValueError:
    raise HTTPException(...)  # Rejects vehicle_malus, energy_poverty_aid
```

**Required Extension:**
```python
def _build_policy_config(req: PortfolioPolicyRequest) -> Any:
    """Build a PolicyConfig from a request object.

    Story 24.3: Extended to handle CustomPolicyType for vehicle_malus
    and energy_poverty_aid policies.
    """
    from reformlab.templates.portfolios import PolicyConfig
    from reformlab.templates.schema import get_policy_type, PolicyParameters
    from reformlab.templates.packs subsidy import SubsidyParameters  # Example import pattern

    # Try PolicyType enum first, then CustomPolicyType
    try:
        from reformlab.templates.schema import PolicyType
        policy_type = PolicyType(req.policy_type)
    except ValueError:
        # Fall back to CustomPolicyType
        try:
            policy_type = get_policy_type(req.policy_type)
        except Exception:
            raise HTTPException(
                status_code=422,
                detail={
                    "what": f"Invalid policy_type: '{req.policy_type}'",
                    "why": "Policy type not found in built-in or custom registries",
                    "fix": "Use a valid policy type (carbon_tax, subsidy, rebate, feebate, vehicle_malus, energy_poverty_aid)",
                },
            )

    # Get parameters class from registry
    # Story 24.2: Custom types have parameter classes registered
    if isinstance(policy_type, PolicyType):
        params_cls = _POLICY_TYPE_TO_PARAMS.get(policy_type)
    else:
        # CustomPolicyType: look up in parameter registry
        params_cls = _get_custom_policy_params_class(policy_type.value)

    if params_cls is None:
        raise HTTPException(
            status_code=422,
            detail={
                "what": f"Parameters class not found for policy type: '{req.policy_type}'",
                "why": "No parameters mapping registered for this policy type",
                "fix": "Register the parameters class for this custom policy type",
            },
        )

    # Validate parameters
    try:
        params = params_cls(**req.parameters)
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "what": f"Invalid parameters for policy type '{req.policy_type}'",
                "why": str(exc),
                "fix": "Check parameters match the expected schema for this policy type",
            },
        )

    # Check runtime availability for custom types
    from reformlab.server.routes.templates import LIVE_READY_TYPES
    if policy_type.value not in LIVE_READY_TYPES:
        raise HTTPException(
            status_code=422,
            detail={
                "what": f"Policy type '{policy_type.value}' is not available for live execution",
                "why": f"Policy type '{policy_type.value}' is not marked as live_ready for runtime execution",
                "fix": f"Use one of the live-ready policy types: {', '.join(sorted(LIVE_READY_TYPES))}",
            },
        )

    return PolicyConfig(policy_type=policy_type, policy=params, name=req.name)
```

**Key Changes:**
1. Use `get_policy_type()` for CustomPolicyType resolution
2. Add parameter class registry lookup for custom types
3. Keep runtime availability check (import `LIVE_READY_TYPES` from `routes/templates.py`)
4. Handle both PolicyType enum and CustomPolicyType values

### Portfolio Validation Compatibility

**File:** `src/reformlab/templates/portfolios/composition.py`

The `validate_compatibility()` function already works with any PolicyType enum or CustomPolicyType. Story 24.2 registered vehicle_malus and energy_poverty_aid as CustomPolicyType values. No changes are required to composition.py itself.

**Verification needed:** Ensure that `get_policy_type()` in schema.py correctly resolves CustomPolicyType values for subsidy-family policies.

**Integration test required:** Test portfolio validation with each surfaced policy type.

### Normalization and Output Variables

**File:** `src/reformlab/computation/result_normalizer.py`

Story 24.2 already added the subsidy-family output variable mappings:
- `montant_subvention` → `subsidy_amount`
- `eligible_subvention` → `subsidy_eligible`
- `malus_ecologique` → `vehicle_malus`
- `aide_energie` → `energy_poverty_aid`

**Column Naming Order:**
1. First, normalize French to English field names
2. Then, apply policy-type+index prefixing

**Example:** For subsidy policy at index 0:
- Raw: `montant_subvention`
- After normalization: `subsidy_amount`
- After prefixing: `subsidy_0_subsidy_amount`

Portfolio results go through the same normalization path as single-policy results:
1. `PortfolioComputationStep` produces merged `ComputationResult`
2. `PanelOutput.from_orchestrator_result()` applies normalization
3. Each policy's output columns are normalized individually, then prefixed

**Verification needed:** Ensure that portfolio merged results pass through normalization correctly and that all subsidy-family output variables are properly renamed.

### Testing Standards

**Unit Tests:** `tests/orchestrator/test_portfolio_step.py` (extend existing)
```python
# Test class structure
class TestPortfolioTranslationIntegration:
    """Tests for translation integration in PortfolioComputationStep."""

    def test_subsidy_policy_translated_in_portfolio(self):
        """AC: Subsidy policy in portfolio is translated before execution."""

    def test_vehicle_malus_policy_translated_in_portfolio(self):
        """AC: Vehicle malus policy in portfolio is translated before execution."""

    def test_energy_poverty_aid_policy_translated_in_portfolio(self):
        """AC: Energy poverty aid policy in portfolio is translated before execution."""

    def test_translation_error_wrapped_as_portfolio_step_error(self):
        """AC: TranslationError is wrapped with PortfolioComputationStepError."""

    def test_mixed_portfolio_translates_correctly(self):
        """AC: Portfolio with mixed policy types (carbon_tax + subsidy) translates all policies."""

class TestPortfolioRuntimeAvailabilityValidation:
    """Tests for portfolio runtime availability validation."""

    def test_all_live_ready_policies_pass_validation(self):
        """AC: Portfolio with all live_ready policies passes runtime availability check."""

    def test_unavailable_policy_fails_validation(self):
        """AC: Portfolio with unavailable policy type fails validation with error message."""

    def test_unavailable_policy_identified_in_error_message(self):
        """AC: Error message identifies which policy is unavailable."""

    def test_replay_mode_bypasses_availability_check(self):
        """AC: Runtime mode=replay bypasses availability check."""

class TestPortfolioValidationWithSurfacedTypes:
    """Tests for portfolio validation with surfaced policy types."""

    def test_subsidy_portfolio_validates_successfully(self):
        """AC: Portfolio containing subsidy policy validates successfully."""

    def test_vehicle_malus_portfolio_validates_successfully(self):
        """AC: Portfolio containing vehicle_malus policy validates successfully."""

    def test_energy_poverty_aid_portfolio_validates_successfully(self):
        """AC: Portfolio containing energy_poverty_aid policy validates successfully."""

    def test_conflict_detection_works_with_surfaced_types(self):
        """AC: Conflict detection correctly identifies conflicts with surfaced types."""
```

**Integration Tests:** `tests/server/test_portfolio_execution_integration.py` (new file)
```python
# Test class structure
class TestPortfolioLiveExecution:
    """End-to-end tests for portfolio execution with surfaced policies."""

    def test_subsidy_portfolio_executes_through_live_path(self):
        """AC: Portfolio with subsidy policy executes through live runtime."""

    def test_vehicle_malus_portfolio_executes_through_live_path(self):
        """AC: Portfolio with vehicle_malus policy executes through live runtime."""

    def test_energy_poverty_aid_portfolio_executes_through_live_path(self):
        """AC: Portfolio with energy_poverty_aid policy executes through live runtime."""

    def test_mixed_portfolio_executes_successfully(self):
        """AC: Portfolio with carbon_tax + subsidy executes successfully."""

    def test_portfolio_results_include_expected_outputs(self):
        """AC: Portfolio results include subsidy-family output variables."""

    def test_portfolio_results_are_normalized_correctly(self):
        """AC: Portfolio results are normalized with correct column names (normalize then prefix)."""

    def test_portfolio_column_prefixing_with_duplicate_types(self):
        """AC: Portfolio with duplicate policy types uses proper prefixing."""

class TestPortfolioComparisonWithSurfacedPolicies:
    """Tests for portfolio comparison with surfaced policies."""

    def test_portfolio_comparison_works_with_surfaced_policies(self):
        """AC: Portfolio comparison works with subsidy-family policies."""

    def test_indicators_compute_correctly_for_portfolio_with_surfaced_policies(self):
        """AC: Indicators compute correctly for portfolios containing surfaced policies."""

class TestNonRegression:
    """Tests for non-regression of existing portfolio behavior."""

    def test_existing_portfolio_execution_unchanged(self):
        """AC: Existing portfolios with carbon_tax/rebate/feebate execute without changes."""

    def test_duplicate_policy_type_prefixing_preserved(self):
        """AC: Column prefixing for duplicate policy types is preserved."""

class TestPortfolioRouteCustomPolicyType:
    """Tests for portfolio route CustomPolicyType support."""

    def test_create_portfolio_with_vehicle_malus_succeeds(self):
        """AC: Portfolio creation with vehicle_malus (CustomPolicyType) succeeds."""

    def test_create_portfolio_with_energy_poverty_aid_succeeds(self):
        """AC: Portfolio creation with energy_poverty_aid (CustomPolicyType) succeeds."""

    def test_create_portfolio_with_unavailable_custom_type_fails(self):
        """AC: Portfolio creation with unavailable custom type fails with 422."""

    def test_error_message_identifies_unavailable_policy(self):
        """AC: Error message clearly identifies the unavailable policy type."""
```

### Project Structure Notes

**Files to Modify:**
- `src/reformlab/orchestrator/portfolio_step.py` - Integrate translation into PortfolioComputationStep
- `src/reformlab/server/validation.py` - Add portfolio runtime availability validation check
- `src/reformlab/server/routes/portfolios.py` - Extend to handle CustomPolicyType and add runtime availability check

**Files to Extend (add tests):**
- `tests/orchestrator/test_portfolio_step.py` - Add translation integration tests
- `tests/server/test_validation.py` - Add portfolio runtime availability tests
- `tests/server/test_portfolios.py` - Add CustomPolicyType and runtime availability error tests

**Files to Create:**
- `tests/server/test_portfolio_execution_integration.py` - End-to-end integration tests for portfolio execution

**Key Dependencies:**
- Story 24.1: Publish canonical catalog for hidden policy packs
- Story 24.2: Implement domain-layer live translation for subsidy-style policies (MUST be merged first)
- Epic 12: Portfolio model and validation framework
- Epic 13: Additional policy templates and extensibility

### Implementation Order Recommendation

1. **Phase 1: Translation Integration** (Core functionality)
   - Modify `PortfolioComputationStep.execute()` to translate each policy
   - Handle TranslationError wrapping
   - Add unit tests for translation integration
   - Ensure non-regression for existing portfolio execution

2. **Phase 2: Runtime Availability Validation** (Blocking invalid requests)
   - Create `_check_portfolio_runtime_availability()` in validation.py
   - Register the validation check
   - Add unit tests for validation check

3. **Phase 3: Portfolio Route CustomPolicyType Support** (API consistency)
   - Extend `_build_policy_config()` to handle CustomPolicyType
   - Add parameter class registry lookup for custom types
   - Add API route tests for CustomPolicyType handling

4. **Phase 4: Integration Testing** (End-to-end verification)
   - Create integration tests for portfolio execution with surfaced policies
   - Test normalization and output variables
   - Test comparison and indicators
   - Verify non-regression

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic-24] - Epic 24 requirements
- [Source: src/reformlab/orchestrator/portfolio_step.py] - PortfolioComputationStep implementation
- [Source: src/reformlab/templates/portfolios/composition.py] - Portfolio validation and conflict detection
- [Source: src/reformlab/computation/translator.py] - Translation layer from Story 24.2
- [Source: src/reformlab/server/routes/portfolios.py] - Portfolio API routes
- [Source: src/reformlab/server/routes/runs.py] - Run endpoint with _run_portfolio() function
- [Source: src/reformlab/server/validation.py] - Validation check registry
- [Source: _bmad-output/implementation-artifacts/24-1-publish-canonical-catalog-and-api-exposure-for-already-modeled-hidden-policy-packs.md] - Story 24.1 (completed)
- [Source: _bmad-output/implementation-artifacts/24-2-implement-domain-layer-live-translation-for-subsidy-style-policies-without-adapter-interface-changes.md] - Story 24.2 (completed)

## Dev Agent Record

### Agent Model Used

claude-opus-4-6

### Debug Log References

None.

### Completion Notes List

Story created with comprehensive developer context:
- Translation integration requirements for PortfolioComputationStep
- Runtime availability validation design
- Portfolio route validation extensions
- Complete testing standards with unit and integration test specifications
- Non-regression requirements for existing portfolio behavior
- Implementation order recommendations

### Code Review Synthesis Notes

- 1 verified issue fixed: layer violation in result_normalizer.py (imported LIVE_READY_TYPES from server.routes.templates instead of defining known policy types locally)
- 12 reviewer issues were false positives (already fixed in implementation or incorrect analysis)
- 1 follow-up task created for missing integration test file

### File List

**Story file created:**
- `_bmad-output/implementation-artifacts/24-3-enable-portfolio-execution-for-surfaced-subsidy-and-related-live-policy-packs.md`

**Code review synthesis modifications:**
- `src/reformlab/computation/result_normalizer.py` — removed server.routes import, replaced with locally-defined known policy types list

## Senior Developer Review (AI)

### Review: 2026-04-18
- **Reviewer:** AI Code Review Synthesis
- **Evidence Score:** 3.3 → PASS
- **Issues Found:** 1
- **Issues Fixed:** 1
- **Action Items Created:** 1
