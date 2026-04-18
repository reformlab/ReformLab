# Story 24.2: Implement domain-layer live translation for subsidy-style policies without adapter interface changes

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a ReformLab developer,
I want subsidy, vehicle_malus, and energy_poverty_aid policies to execute through live OpenFisca,
so that analysts can run these policies from the web product without adapter interface changes.

## Acceptance Criteria

1. Given a subsidy-style policy defined in the domain layer (subsidy, vehicle_malus, energy_poverty_aid), when prepared for execution, then it is translated into live OpenFisca inputs by domain-owned translation logic.
2. Given the live execution path, when translation completes, then the adapter receives the same generic request shape it would for any other live run (no subsidy-specific adapter extensions).
3. Given the ComputationAdapter interface, when reviewed after implementation, then no subsidy-specific behavior has been added to `ComputationAdapter`, `OpenFiscaAdapter`, or the precomputed adapter.
4. Given the translation implementation, when an unsupported subsidy-domain feature is requested, then the failure is explicit and actionable with clear error messages.
5. Given the excluded housing or family-benefit domains, when requested in this slice, then they are not silently treated as supported (implementation must explicitly reject them or defer to future stories).
6. Given the translation logic, when it completes, then the adapter receives OpenFisca variable names and values for execution, not domain PolicyParameter field names.
7. Given a successfully translated subsidy policy, when executed through live OpenFisca, then results are normalized through the existing result_normalizer.py layer from Story 23.3.

## Tasks / Subtasks

- [ ] Add domain translation framework and protocol (AC: #1, #2, #3)
  - [ ] Create `src/reformlab/computation/translator.py` module with translation protocol and error types
  - [ ] Define `PolicyTranslator` protocol with `translate()` method for domain-to-OpenFisca conversion
  - [ ] Define `TranslationError` exception following project error pattern (what, why, fix)
  - [ ] Add module-level docstring explaining translation layer purpose and architectural placement

- [ ] Implement subsidy policy translation (AC: #1, #6)
  - [ ] Create `_translate_subsidy_policy()` function in translator module
  - [ ] Map `SubsidyParameters` fields (income_caps, rate_schedule, eligible_categories) to OpenFisca input variables
  - [ ] Map output variable requests to include `subsidy_amount`, `subsidy_eligible` (or equivalent OpenFisca variables)
  - [ ] Add translation tests for subsidy parameters → OpenFisca variable mapping

- [ ] Implement vehicle_malus policy translation (AC: #1, #6)
  - [ ] Create `_translate_vehicle_malus_policy()` function in translator module
  - [ ] Map `VehicleMalusParameters` fields (emission_threshold, malus_rate_per_gkm, rate_schedule, threshold_schedule) to OpenFisca input variables
  - [ ] Map output variable requests to include vehicle malus amount field
  - [ ] Add translation tests for vehicle_malus parameters → OpenFisca variable mapping

- [ ] Implement energy_poverty_aid policy translation (AC: #1, #6)
  - [ ] Create `_translate_energy_poverty_aid_policy()` function in translator module
  - [ ] Map `EnergyPovertyAidParameters` fields to OpenFisca input variables
  - [ ] Map output variable requests to include energy poverty aid amount field
  - [ ] Add translation tests for energy_poverty_aid parameters → OpenFisca variable mapping

- [ ] Integrate translation into policy schema (AC: #1, #2, #3, #6)
  - [ ] Add `openfisca_variables` list to `PolicyType` enum for hinting which OpenFisca variables each policy type needs
  - [ ] Add `output_variables` computed property to PolicyParameters base class
  - [ ] Ensure carbon_tax, subsidy, rebate, feebate types provide correct OpenFisca variable hints
  - [ ] Add docstring to PolicyParameters base explaining translation flow

- [ ] Integrate translation into API layer (AC: #2, #6)
  - [ ] Create `_translate_policy_to_openfisca()` function in `src/reformlab/interfaces/api.py`
  - [ ] Call translation function in `_execute_orchestration()` before passing policy to ComputationStep
  - [ ] Pass translated policy dict to ComputationStep instead of raw domain policy
  - [ ] Ensure adapter receives OpenFisca variable names, not domain field names
  - [ ] Add translation error handling with HTTPException-style response for API consumers

- [ ] Update runtime availability classifier (AC: #1, #5)
  - [ ] Update `_classify_runtime_availability()` in `src/reformlab/server/routes/templates.py`
  - [ ] Mark subsidy, vehicle_malus, energy_poverty_aid as `live_ready` when translation is implemented
  - [ ] Keep carbon_tax, rebate, feebate as `live_ready` (no change needed)
  - [ ] Update availability_reason for newly-live policies to `null`

- [ ] Ensure domain policies execute through existing live normalization (AC: #7)
  - [ ] Verify that translated subsidy/vehicle_malus/energy_poverty_aid policies execute through `OpenFiscaApiAdapter`
  - [ ] Verify results flow through `result_normalizer.py` from Story 23.3
  - [ ] Verify output variables are included in normalization mapping
  - [ ] Add integration test for full subsidy policy execution path (domain → translation → adapter → normalization)

- [ ] Add error handling for excluded domains (AC: #5)
  - [ ] Reject housing and family-benefit policy types with explicit error message
  - [ ] Error should indicate domain is not supported in this slice and reference future story
  - [ ] Add test confirming rejection occurs for excluded policy types

- [ ] Add translation unit tests (AC: #4)
  - [ ] Create `tests/computation/test_translator.py` test module
  - [ ] Test subsidy parameter translation with valid inputs
  - [ ] Test vehicle_malus parameter translation with valid inputs
  - [ ] Test energy_poverty_aid parameter translation with valid inputs
  - [ ] Test translation error handling for missing/invalid fields
  - [ ] Test excluded domain rejection (housing, family-benefit)

- [ ] Add integration tests (AC: #4)
  - [ ] Create `tests/server/test_translation_integration.py` for end-to-end testing
  - [ ] Test full execution path for subsidy policy through API: run_scenario() → translation → orchestrator → adapter
  - [ ] Verify adapter receives translated OpenFisca variables, not domain field names
  - [ ] Verify results are normalized correctly for translated policies
  - [ ] Test catalog reflects `live_ready` status for newly-live policies

- [ ] Update documentation and error messages (AC: #4, #5)
  - [ ] Update CLAUDE.md or project documentation with translation layer explanation
  - [ ] Ensure translation error messages follow project pattern: what, why, fix
  - [ ] Document which policy types are supported for live translation in this slice

## Dev Notes

### Architecture Context

**Key Design Principle:** The translation boundary sits between the domain layer (PolicyParameters dataclasses) and the computation adapter (OpenFiscaApiAdapter). The adapter must remain generic and unaware of domain-specific policy semantics.

**Current Flow (Before This Story):**
```
run_scenario()
  → _execute_orchestration()
    → OrchestratorRunner
      → ComputationStep(adapter, population, policy=domain_policy_dict)
        → OpenFiscaApiAdapter.compute(population, policy=PolicyConfig(policy=domain_policy_dict), period)
```

**New Flow (After This Story):**
```
run_scenario()
  → _translate_policy_to_openfisca(domain_policy, template_name)
    → _execute_orchestration()
      → ComputationStep(adapter, population, policy=openfisca_variable_dict)
        → OpenFiscaApiAdapter.compute(population, policy=PolicyConfig(policy=openfisca_variable_dict), period)
```

**Critical Constraint:** The `ComputationAdapter` protocol and `OpenFiscaApiAdapter` implementation MUST NOT be modified. Translation happens entirely in the domain/API layer before adapter invocation.

### Translation Layer Design

**Module:** `src/reformlab/computation/translator.py` (new file)

**Protocol Definition:**
```python
@runtime_checkable
class PolicyTranslator(Protocol):
    """Protocol for domain-to-OpenFisca translation.

    Implementations convert domain PolicyParameters (dataclasses) into
    OpenFisca variable names and values suitable for adapter.compute().
    """

    def translate(
        self,
        policy: Any,  # PolicyParameters instance
        template_name: str,
    ) -> dict[str, Any]:
        """Translate domain policy to OpenFisca variable mapping.

        Args:
            policy: Domain PolicyParameters instance (SubsidyParameters, etc.)
            template_name: Name of template for error messages.

        Returns:
            Dict mapping OpenFisca variable names to values.

        Raises:
            TranslationError: If policy cannot be translated.
        """
```

**Error Type:**
```python
class TranslationError(Exception):
    """Structured translation error following project error pattern.

    Attributes:
        what: High-level description of what failed.
        why: Detailed reason for failure.
        fix: Actionable guidance to resolve issue.
    """

    def __init__(self, *, what: str, why: str, fix: str) -> None:
        self.what = what
        self.why = why
        self.fix = fix
        message = f"{what} — {why} — {fix}"
        super().__init__(message)
```

**Translation Functions:**
- `_translate_subsidy_policy(policy, template_name)`: Maps `SubsidyParameters` to OpenFisca variables
- `_translate_vehicle_malus_policy(policy, template_name)`: Maps `VehicleMalusParameters` to OpenFisca variables
- `_translate_energy_poverty_aid_policy(policy, template_name)`: Maps `EnergyPovertyAidParameters` to OpenFisca variables
- `_translate_generic_policy(policy, template_name)`: Fallback that rejects with clear error

**Translation Mapping Pattern (Example - Subsidy):**
| Domain Field | OpenFisca Variable | Notes |
|--------------|----------------------|-------|
| `income_caps[year]` | `revenu_plafond_maximum` | Per-year income ceiling |
| `rate_schedule[year]` | `montant_subvention` | Yearly subsidy amount |
| `eligible_categories` | `categories_eligibles_subvention` | List of eligible categories |

**Output Variable Requests:**
- Subsidy: Request output variables like `montant_subvention`, `eligible_subvention`
- Vehicle malus: Request output variable for malus amount (e.g., `malus_ecologique`)
- Energy poverty aid: Request output variable for aid amount

**Key Decision:** OpenFisca variable names should be French (matching `openfisca_france` package conventions). The normalization layer (`result_normalizer.py`) will handle French→English mapping after execution.

### Policy Schema Extension

**File:** `src/reformlab/templates/schema.py`

**Add to `PolicyType` enum:**
```python
class PolicyType(StrEnum):
    # ... existing types ...
    carbon_tax = "carbon_tax"
    subsidy = "subsidy"
    rebate = "rebate"
    feebate = "feebate"
    vehicle_malus = "vehicle_malus"  # NEW
    energy_poverty_aid = "energy_poverty_aid"  # NEW
```

**Add to `PolicyParameters` base class:**
```python
@dataclass(frozen=True)
class PolicyParameters:
    """Base class for all policy parameter dataclasses.

    Story 24.2: Added translation hints for live OpenFisca execution.
    The `output_variables` computed property provides OpenFisca variable
    names that should be requested from the adapter after translation.
    """
    policy_type: PolicyType

    @property
    def output_variables(self) -> tuple[str, ...]:
        """OpenFisca variable names to request after translation.

        Subclasses override this to provide policy-specific output variables.
        Default implementation returns empty tuple for backward compatibility.
        """
        return ()
```

**Implement in each PolicyParameters subclass:**
- `SubsidyParameters`: Return `("montant_subvention", "eligible_subvention",)`
- `VehicleMalusParameters`: Return `("malus_ecologique",)`
- `EnergyPovertyAidParameters`: Return `("aide_energie",)` (or appropriate variable name)
- `CarbonTaxParameters`, `RebateParameters`, `FeebateParameters`: Keep empty or add relevant variables

### API Layer Integration

**File:** `src/reformlab/interfaces/api.py`

**New Function:**
```python
def _translate_policy_to_openfisca(
    policy: Any,  # PolicyParameters instance
    template_name: str,
) -> dict[str, Any]:
    """Translate domain policy to OpenFisca variable mapping.

    Story 24.2: Domain-layer translation boundary. Converts
    PolicyParameters dataclasses into OpenFisca variable names and values.
    The adapter receives this mapping as policy dict.

    Args:
        policy: Domain policy parameters (SubsidyParameters, etc.).
        template_name: Template name for error messages.

    Returns:
        Dict mapping OpenFisca variable names to values.

    Raises:
        ConfigurationError: If policy cannot be translated or is excluded domain.
    """
    # Import translation module
    from reformlab.computation.translator import (
        PolicyTranslator,
        _translate_subsidy_policy,
        _translate_vehicle_malus_policy,
        _translate_energy_poverty_aid_policy,
        TranslationError,
    )

    # Get policy type
    from reformlab.templates.schema import PolicyType
    policy_type = getattr(policy, "policy_type", None)

    if policy_type is None:
        raise ConfigurationError(
            field_path="policy",
            expected="PolicyParameters instance with policy_type attribute",
            actual=f"{type(policy).__name__} without policy_type",
            fix="Ensure policy is a valid PolicyParameters subclass",
        )

    # Exclude housing and family-benefit reforms in this slice
    excluded_types = {PolicyType.housing, PolicyType.family_benefit}
    if policy_type in excluded_types:
        raise ConfigurationError(
            field_path="policy_type",
            expected="Supported policy type for live translation",
            actual=policy_type.value,
            fix=(
                f"Housing and family-benefit reforms are not supported in "
                f"Story 24.2. See future stories for housing and family policy support."
            ),
        )

    # Dispatch to appropriate translator
    translators: dict[PolicyType, PolicyTranslator] = {
        PolicyType.subsidy: _translate_subsidy_policy,
        PolicyType.vehicle_malus: _translate_vehicle_malus_policy,
        PolicyType.energy_poverty_aid: _translate_energy_poverty_aid_policy,
    }

    translator = translators.get(policy_type)
    if translator is None:
        # No translator defined - pass through for carbon_tax, rebate, feebate
        # These already work via default adapter behavior
        from reformlab.computation.types import serialize_policy
        return serialize_policy(policy)

    try:
        return translator.translate(policy, template_name)
    except TranslationError as exc:
        # Wrap TranslationError as ConfigurationError for API consistency
        raise ConfigurationError(
            field_path=f"policy.{policy_type.value}",
            expected="Translatable policy parameters",
            actual=exc.why,
            fix=exc.fix,
        ) from exc
```

**Modify `_execute_orchestration()`:**
```python
# In _execute_orchestration(), before creating ComputationStep:
# BEFORE (lines 1880-1888):
    policy_config = PolicyConfig(
        policy=typed_policy,
        name=execution_name,
    )

# AFTER (new lines):
# Story 24.2: Translate domain policy to OpenFisca variables
openfisca_policy = _translate_policy_to_openfisca(typed_policy, execution_name)
policy_config = PolicyConfig(
    policy=openfisca_policy,
    name=execution_name,
)
```

### Runtime Availability Update

**File:** `src/reformlab/server/routes/templates.py`

**Modify `_classify_runtime_availability()` function:**
```python
# BEFORE (lines ~30-50):
LIVE_READY_TYPES = {"carbon_tax", "subsidy", "rebate", "feebate"}
HIDDEN_PACK_TYPES = {"vehicle_malus", "energy_poverty_aid"}

# AFTER (new lines):
# Story 24.2: Added vehicle_malus and energy_poverty_aid to live_ready types
# Subsidy-family policies now support live translation
LIVE_READY_TYPES = {
    "carbon_tax",
    "subsidy",  # Story 24.2 - now live-ready
    "rebate",
    "feebate",
    "vehicle_malus",  # Story 24.2 - now live-ready
    "energy_poverty_aid",  # Story 24.2 - now live-ready
}
# Removed HIDDEN_PACK_TYPES - no longer hidden after this story
```

**Update `_classify_runtime_availability()` logic:**
```python
# Story 24.2: All listed types are now live-ready
if is_builtin and policy_type in LIVE_READY_TYPES:
    return "live_ready", None

# Safe fallback for unknown types
return "live_unavailable", None
```

### Testing Standards

**Unit Tests:** `tests/computation/test_translator.py`
```python
# Test class structure
class TestSubsidyTranslation:
    """Tests for subsidy policy translation to OpenFisca variables."""

    def test_subsidy_parameters_translated_to_openfisca_vars(self):
        """AC: Subsidy parameters map to correct OpenFisca variables."""

    def test_subsidy_rate_schedule_year_mapping(self):
        """AC: Year-indexed rate_schedule maps correctly."""

    def test_subsidy_eligible_categories_mapping(self):
        """AC: Eligible categories map correctly."""

    def test_subsidy_output_variables_requested(self):
        """AC: Output variables include subsidy amount and eligibility."""

class TestVehicleMalusTranslation:
    """Tests for vehicle malus policy translation."""

    def test_malus_parameters_translated(self):
        """AC: Vehicle malus parameters map correctly."""

    def test_malus_threshold_schedule_year_mapping(self):
        """AC: Year-indexed threshold_schedule maps correctly."""

class TestEnergyPovertyAidTranslation:
    """Tests for energy poverty aid policy translation."""

    def test_aid_parameters_translated(self):
        """AC: Energy poverty aid parameters map correctly."""

class TestTranslationErrorHandling:
    """Tests for translation error cases."""

    def test_unknown_policy_type_raises_error(self):
        """AC: Unknown policy type raises ConfigurationError."""

    def test_excluded_domains_rejected(self):
        """AC: Housing and family-benefit reforms are rejected with clear error."""
```

**Integration Tests:** `tests/server/test_translation_integration.py`
```python
# Test class structure
class TestSubsidyLiveExecution:
    """End-to-end tests for subsidy policy live execution."""

    @pytest.fixture
    def subsidy_scenario_config(self):
        """Create a valid subsidy scenario configuration."""
        from reformlab.templates.schema import SubsidyParameters
        return {
            "template_name": "subsidy-energy-retrofit",
            "policy": {
                "rate_schedule": {2025: 5000},
                "income_caps": {2025: 30000},
                "eligible_categories": ["low_income"],
            },
            "start_year": 2025,
            "end_year": 2025,
        }

    def test_subsidy_policy_executes_through_live_adapter(self, subsidy_scenario_config):
        """AC: Subsidy policy executes through OpenFisca API adapter."""

    def test_subsidy_results_are_normalized_correctly(self, subsidy_scenario_config):
        """AC: Translated subsidy results flow through normalization layer."""

    def test_subsidy_adapter_receives_openfisca_variables(self, subsidy_scenario_config):
        """AC: Adapter receives OpenFisca variable names, not domain field names."""

class TestCatalogLiveReadiness:
    """Tests for catalog runtime availability updates."""

    def test_subsidy_is_live_ready_after_translation(self):
        """AC: Subsidy template has runtime_availability='live_ready'."""

    def test_vehicle_malus_is_live_ready_after_translation(self):
        """AC: Vehicle malus template has runtime_availability='live_ready'."""

    def test_energy_poverty_aid_is_live_ready_after_translation(self):
        """AC: Energy poverty aid template has runtime_availability='live_ready'."""
```

### Project Structure Notes

**New Files to Create:**
- `src/reformlab/computation/translator.py` - Domain translation layer (new module)
- `tests/computation/test_translator.py` - Translation unit tests
- `tests/server/test_translation_integration.py` - End-to-end integration tests

**Files to Modify:**
- `src/reformlab/templates/schema.py` - Add PolicyType enum values, PolicyParameters.output_variables property
- `src/reformlab/interfaces/api.py` - Add `_translate_policy_to_openfisca()`, modify `_execute_orchestration()`
- `src/reformlab/server/routes/templates.py` - Update `_classify_runtime_availability()` to mark subsidy-family as live_ready

**Files NOT to Modify (Critical):**
- `src/reformlab/computation/adapter.py` - ComputationAdapter protocol must remain unchanged
- `src/reformlab/computation/openfisca_adapter.py` - OpenFiscaApiAdapter must remain unchanged
- `src/reformlab/computation/openfisca_adapter.py` - Precomputed adapter must remain unchanged
- `src/reformlab/computation/result_normalizer.py` - Should work unchanged, just receives OpenFisca output

### Implementation Order Recommendation

1. **Phase 1: Translation Framework** (Unit tests first)
   - Create `translator.py` with protocol and error types
   - Add unit tests for translator functions
   - Ensure tests pass

2. **Phase 2: Policy Translation**
   - Implement `_translate_subsidy_policy()` with mapping
   - Implement `_translate_vehicle_malus_policy()` with mapping
   - Implement `_translate_energy_poverty_aid_policy()` with mapping
   - Add unit tests for each translator

3. **Phase 3: Schema Extension**
   - Extend `PolicyType` enum with new types
   - Add `output_variables` property to `PolicyParameters` base
   - Implement in each PolicyParameters subclass
   - Add unit tests for schema changes

4. **Phase 4: API Integration**
   - Create `_translate_policy_to_openfisca()` in `interfaces/api.py`
   - Modify `_execute_orchestration()` to use translation
   - Add integration tests for full execution path

5. **Phase 5: Catalog Update**
   - Update `_classify_runtime_availability()` in `routes/templates.py`
   - Verify catalog reflects `live_ready` for new policies
   - Add integration tests for catalog updates

### OpenFisca Variable Research (Developer TODO)

The actual OpenFisca variable names for subsidy, vehicle_malus, and energy_poverty_aid need to be determined. Candidates to investigate in `openfisca_france`:

**Subsidy:**
- `montant_subvention` - subsidy amount
- `eligible_subvention` - eligibility status
- `categories_eligibles_subvention` - eligible categories list
- `revenu_plafond_maximum` - income ceiling (may already exist as income cap)

**Vehicle Malus:**
- `malus_ecologique` - malus amount
- `emissions_co2` - CO2 emissions field (may exist in population data)

**Energy Poverty Aid:**
- `aide_energie` - aid amount
- `eligible_aide_energie` - eligibility status
- `plafond_energie` - income or energy poverty ceiling

**Note:** If OpenFisca variables don't exist for these exact policy types, consider:
1. Using generic variable names (`subsidy_amount`, `malus_amount`, `aid_amount`)
2. Mapping to existing OpenFisca variables that can carry the values
3. Creating simple input variables that OpenFisca can process

The normalization layer (`result_normalizer.py`) handles French→English mapping after execution, so the translation layer should produce French variable names for OpenFisca.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic-24] - Epic 24 requirements
- [Source: src/reformlab/computation/adapter.py] - ComputationAdapter protocol (must not change)
- [Source: src/reformlab/computation/openfisca_api_adapter.py] - OpenFiscaApiAdapter implementation (must not change)
- [Source: src/reformlab/templates/subsidy/compute.py] - Subsidy domain computation
- [Source: src/reformlab/templates/vehicle_malus/compute.py] - Vehicle malus domain computation
- [Source: src/reformlab/templates/energy_poverty_aid/__init__.py] - Energy poverty aid domain module
- [Source: src/reformlab/templates/schema.py] - PolicyTypes and PolicyParameters base
- [Source: src/reformlab/interfaces/api.py] - API layer where translation is integrated
- [Source: src/reformlab/computation/result_normalizer.py] - Result normalization from Story 23.3
- [Source: _bmad-output/implementation-artifacts/24-1-publish-canonical-catalog-and-api-exposure-for-already-modeled-hidden-policy-packs.md] - Story 24.1 (completed)

## Dev Agent Record

### Agent Model Used

claude-opus-4-6

### Debug Log References

None - This is the initial story creation.

### Completion Notes List

**Story Analysis Summary:**
- Analyzed existing domain policy structure (subsidy, vehicle_malus, energy_poverty_aid)
- Understood current adapter interface and OpenFisca API adapter implementation
- Identified translation boundary placement: between API layer and ComputationStep
- Determined that adapter must receive OpenFisca variable names, not domain field names
- Identified excluded domains (housing, family-benefit) that must be explicitly rejected

**Implementation Strategy:**
1. Create new `translator.py` module with PolicyTranslator protocol
2. Implement translation functions for subsidy, vehicle_malus, energy_poverty_aid
3. Extend `PolicyParameters` with `output_variables` computed property
4. Add `PolicyType` enum values for new policy types
5. Integrate translation in `_execute_orchestration()` before ComputationStep creation
6. Update catalog classifier to mark subsidy-family as `live_ready`
7. Add comprehensive unit and integration tests

**Key Architectural Decision:**
- Translation layer converts domain PolicyParameters → OpenFisca variable dict
- Adapter receives translated dict via PolicyConfig(policy=openfisca_dict)
- Adapter contract unchanged - no subsidy-specific methods or extensions
- Normalization layer (Story 23.3) works unchanged, just maps French output to English

**Test Coverage Plan:**
- Unit tests for each translation function
- Unit tests for translation error handling
- Integration tests for full execution path (API → translation → orchestrator → adapter)
- Integration tests for catalog `live_ready` status updates
- Regression tests ensuring existing carbon_tax, rebate, feebate still work

### File List

**Files to be created:**
- `src/reformlab/computation/translator.py` - Domain translation layer (new module)
- `tests/computation/test_translator.py` - Translation unit tests
- `tests/server/test_translation_integration.py` - End-to-end integration tests

**Files to be modified:**
- `src/reformlab/templates/schema.py` - Add PolicyType enum values, PolicyParameters.output_variables property
- `src/reformlab/interfaces/api.py` - Add `_translate_policy_to_openfisca()`, modify `_execute_orchestration()`
- `src/reformlab/server/routes/templates.py` - Update `_classify_runtime_availability()` to mark subsidy-family as live_ready

**Related files (read-only for context):**
- `src/reformlab/computation/adapter.py` - ComputationAdapter protocol (must not change)
- `src/reformlab/computation/openfisca_adapter.py` - OpenFiscaApiAdapter (must not change)
- `src/reformlab/templates/subsidy/compute.py` - Subsidy domain computation
- `src/reformlab/templates/vehicle_malus/compute.py` - Vehicle malus domain computation
- `src/reformlab/templates/energy_poverty_aid/__init__.py` - Energy poverty aid domain module
- `src/reformlab/computation/result_normalizer.py` - Result normalization layer
- `_bmad-output/implementation-artifacts/24-1-publish-canonical-catalog-and-api-exposure-for-already-modeled-hidden-policy-packs.md` - Story 24.1 (completed)
