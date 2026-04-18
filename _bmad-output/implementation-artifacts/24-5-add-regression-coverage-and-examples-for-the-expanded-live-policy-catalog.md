# Story 24.5: Add regression coverage and examples for the expanded live policy catalog

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer working on the ReformLab codebase,
I want comprehensive regression coverage and executable examples for the surfaced live policy packs (subsidy, vehicle_malus, energy_poverty_aid),
so that the expanded catalog is validated end-to-end and future pack additions have a reusable baseline.

## Acceptance Criteria

1. Given the automated test suite, when it runs, then it covers catalog exposure, portfolio validation, live execution, and comparison for surfaced packs (subsidy, vehicle_malus, energy_poverty_aid).
2. Given shipped examples or smoke configs, when executed, then they demonstrate at least one surfaced subsidy-family pack running through the live path successfully.
3. Given the supported policy catalog documentation, when reviewed, then it matches the packs actually exposed and executable in the product.
4. Given future pack expansion work, when planned, then the added tests and examples provide a reusable baseline rather than a one-off demo.

## Tasks / Subtasks

- [ ] Create end-to-end regression test for surfaced packs (AC: #1)
  - [ ] Add `tests/regression/test_surfaced_packs.py` with surfaced pack execution tests
  - [ ] Test catalog exposure returns surfaced packs with correct metadata
  - [ ] Test portfolio validation accepts surfaced policy types
  - [ ] Test live execution through adapter with surfaced packs
  - [ ] Test comparison flows work with surfaced pack outputs
  - [ ] Verify non-regression for existing packs (carbon_tax, rebate, feebate)

- [ ] Add integration test for portfolio save/load with surfaced packs (AC: #1)
  - [ ] Test portfolio create with surfaced policies (vehicle_malus, energy_poverty_aid)
  - [ ] Test portfolio load retrieves correct policy_type mapping
  - [ ] Test portfolio execution produces normalized results
  - [ ] Test portfolio comparison handles surfaced pack outputs

- [ ] Create example smoke configurations for surfaced packs (AC: #2)
  - [ ] Add `examples/live_policy_catalog/surfaced_packs_smoke.py` demonstrating surfaced packs
  - [ ] Include subsidy-family example (subsidy or energy_poverty_aid)
  - [ ] Include vehicle_malus example
  - [ ] Demonstrate portfolio composition with surfaced packs
  - [ ] Show comparison between baseline and surfaced pack reform

- [ ] Document the supported live policy catalog (AC: #3)
  - [ ] Create `docs/live_policy_catalog.md` listing all live-ready packs
  - [ ] Document policy types, parameter groups, and availability status
  - [ ] Include example usage for each surfaced pack type
  - [ ] Document runtime availability contract (live_ready vs live_unavailable)
  - [ ] Reference Story 24.1-24.4 implementation details

- [ ] Add reusable test fixtures for surfaced packs (AC: #1, #4)
  - [ ] Create shared fixtures in `tests/regression/conftest.py` for surfaced pack parameters
  - [ ] Add population fixtures compatible with surfaced pack computations
  - [ ] Add helper functions for surfaced pack result validation
  - [ ] Document fixture patterns for future pack additions

- [ ] Verify frontend-backend contract for surfaced packs (AC: #1, #3)
  - [ ] Test `GET /api/templates` returns surfaced packs with correct runtime_availability
  - [ ] Test TemplateListItem includes surfaced packs with proper type labels
  - [ ] Test portfolio CRUD operations work with surfaced policies
  - [ ] Verify frontend mock data matches backend catalog structure

## Dev Notes

### Epic 24 Context

This story closes Epic 24: Live Policy Catalog Activation and Domain-to-OpenFisca Translation. Previous stories established:
- **Story 24.1**: Catalog API exposure with runtime_availability metadata
- **Story 24.2**: Domain-layer live translation for subsidy-family policies
- **Story 24.3**: Portfolio execution for surfaced packs
- **Story 24.4**: UX surfacing of packs in workspace catalog

This story adds the regression safety net and examples that validate the entire Epic 24 implementation.

### Surfaced Policy Packs

From Story 24.1-24.4, the following policy types are now live-ready:

| Policy Type | Status | Parameter Classes | Key Fields |
|-------------|--------|-------------------|------------|
| carbon_tax | live_ready | CarbonTaxParameters | rate_schedule, exemptions, covered_categories |
| subsidy | live_ready | SubsidyParameters | rate_schedule, income_ceiling, eligible_categories |
| rebate | live_ready | RebateParameters | rate_schedule, eligible_categories |
| feebate | live_ready | FeebateParameters | rate_schedule, threshold, rebates, maluses |
| vehicle_malus | live_ready | VehicleMalusParameters | emission_threshold, malus_rate_per_gkm, threshold_schedule |
| energy_poverty_aid | live_ready | EnergyPovertyAidParameters | rate_schedule, income_ceiling, energy_share_threshold, base_aid_amount |

### Translation Layer (Story 24.2)

The `computation/translator.py` module translates domain policies for live execution:

```python
# Passthrough types (no translation needed)
_PASSTHROUGH_TYPES = {"carbon_tax", "rebate", "feebate"}

# Translation functions (validation + passthrough)
_TRANSLATORS = {
    "subsidy": _translate_subsidy_policy,
    "vehicle_malus": _translate_vehicle_malus_policy,
    "energy_poverty_aid": _translate_energy_poverty_aid_policy,
}
```

Key patterns:
- Passthrough types return policy unchanged
- Subsidy-family types validate required fields (e.g., rate_schedule)
- TranslationError provides structured what/why/fix messages

### Portfolio Routes Extension (Story 24.3)

The `server/routes/portfolios.py` module was extended to handle CustomPolicyType:

```python
# PolicyType enum (built-in types)
policy_type = PolicyType(req.policy_type)

# Fallback to CustomPolicyType for vehicle_malus, energy_poverty_aid
policy_type = get_policy_type(req.policy_type)

# Parameters class lookup
params_cls = _POLICY_TYPE_TO_PARAMS.get(policy_type)  # Built-in
params_cls = custom_registrations.get(policy_type.value)  # Custom
```

### Frontend Integration (Story 24.4)

Type labels and colors for surfaced packs:
- `vehicle_malus` → "Vehicle Malus" (rose: `bg-rose-100 text-rose-800`)
- `energy_poverty_aid` → "Energy Poverty Aid" (cyan: `bg-cyan-100 text-cyan-800`)

Runtime availability badges: `live_ready` packs show green "Ready" badge.

### Testing Standards

**Backend Test Patterns:**
- Class-based test grouping by feature/acceptance criterion
- Fixtures in `conftest.py` per subsystem
- Use `pytest.raises()` for error testing
- Direct assertions (`assert result == expected`)
- MockAdapter for unit tests (avoid real OpenFisca)

**Frontend Test Patterns:**
- Vitest + React Testing Library
- Mock API calls with `vi.mock()`
- Assert DOM elements (not just text)
- ResizeObserver polyfill for Recharts

**Test Organization:**
```
tests/
  regression/          # NEW: End-to-end surfaced pack tests
    conftest.py        # Shared fixtures for surfaced packs
    test_surfaced_packs.py
  templates/
    subsidy/           # Existing: Subsidy compute tests
    energy_poverty_aid/  # Existing: EPA compute tests
    vehicle_malus/     # Existing: Vehicle malus compute tests
    portfolios/        # Existing: Portfolio composition tests
  server/
    test_results.py    # Existing: Results API tests
    test_comparison_portfolios.py  # Existing: Comparison tests
```

### Example Configuration Pattern

Based on `examples/api/api_smoke_test.py`:

```python
# Example structure for surfaced pack smoke test
def main() -> int:
    # 1) Auth
    token = login(password)

    # 2) Catalog - verify surfaced packs present
    templates = get_templates(token)
    surfaced_types = {t["type"] for t in templates if t["runtime_availability"] == "live_ready"}
    assert "subsidy" in surfaced_types
    assert "vehicle_malus" in surfaced_types
    assert "energy_poverty_aid" in surfaced_types

    # 3) Portfolio with surfaced packs
    portfolio = create_portfolio(
        name="surfaced-smoke",
        policies=[
            {"name": "EV Bonus", "policy_type": "subsidy", ...},
            {"name": "High-Emitter Penalty", "policy_type": "vehicle_malus", ...},
        ]
    )

    # 4) Execute portfolio
    run_id = execute_portfolio(portfolio)

    # 5) Verify results
    results = get_results(run_id)
    assert "subsidy_amount" in results["columns"]
    assert "malus_amount" in results["columns"]

    return 0
```

### Catalog Contract

From `server/routes/templates.py`:

```python
LIVE_READY_TYPES = {
    "carbon_tax",
    "subsidy",
    "rebate",
    "feebate",
    "vehicle_malus",       # Story 24.2
    "energy_poverty_aid",  # Story 24.2
}

TemplateListItem {
    id: str
    name: str
    type: str              # Policy type (underscore format from API)
    parameter_count: int
    description: str
    parameter_groups: list[str]
    is_custom: bool
    runtime_availability: "live_ready" | "live_unavailable"
    availability_reason: str | None
}
```

### Non-Regression Requirements

From Story 24.2-24.4 implementation notes:

**Existing Packs Must Not Break:**
- carbon_tax templates execute without errors
- rebate templates execute without errors
- feebate templates execute without errors
- Portfolio save/load maintains stable references
- Comparison surfaces continue to work

**Validation Checklist:**
- [ ] All existing tests in `tests/templates/` pass
- [ ] All server integration tests in `tests/server/` pass
- [ ] All frontend component tests pass
- [ ] API smoke test passes
- [ ] No new lint or type errors

### Documentation Requirements

Create `docs/live_policy_catalog.md` with:

1. **Catalog Overview**
   - What is the live policy catalog?
   - How are packs surfaced from the domain layer?
   - What does runtime_availability mean?

2. **Live-Ready Policy Types**
   - Table of all live-ready types
   - Parameter classes and key fields
   - Example YAML configurations

3. **Runtime Availability Contract**
   - `live_ready` vs `live_unavailable` status
   - Availability reasons when applicable
   - Future expansion patterns

4. **Usage Examples**
   - Python API usage
   - Portfolio composition
   - Comparison workflows

5. **References**
   - Story 24.1: Catalog API exposure
   - Story 24.2: Domain-layer translation
   - Story 24.3: Portfolio execution
   - Story 24.4: UX integration

### Project Structure Notes

**Files to Create:**
- `tests/regression/test_surfaced_packs.py` — End-to-end surfaced pack tests
- `tests/regression/conftest.py` — Shared fixtures for surfaced packs
- `examples/live_policy_catalog/surfaced_packs_smoke.py` — Executable smoke examples
- `docs/live_policy_catalog.md` — Catalog documentation

**Files to Reference (No Changes):**
- `src/reformlab/computation/translator.py` — Translation layer (Story 24.2)
- `src/reformlab/server/routes/templates.py` — Catalog API (Story 24.1)
- `src/reformlab/server/routes/portfolios.py` — Portfolio routes (Story 24.3)
- `frontend/src/components/simulation/PortfolioTemplateBrowser.tsx` — UX (Story 24.4)

**Test Files to Extend:**
- `tests/server/test_results.py` — Add surfaced pack result tests
- `tests/server/test_comparison_portfolios.py` — Add surfaced pack comparison tests
- `tests/templates/portfolios/test_portfolio.py` — Add surfaced pack portfolio tests

### Implementation Order Recommendation

1. **Phase 1: Regression Tests** (Core validation)
   - Create `tests/regression/test_surfaced_packs.py` with catalog tests
   - Add surfaced pack execution tests
   - Add portfolio save/load tests with surfaced packs
   - Add non-regression tests for existing packs

2. **Phase 2: Fixtures and Helpers** (Reusability)
   - Create shared fixtures in `tests/regression/conftest.py`
   - Add helper functions for surfaced pack validation
   - Document fixture patterns for future packs

3. **Phase 3: Example Configurations** (Demonstration)
   - Create `examples/live_policy_catalog/surfaced_packs_smoke.py`
   - Test subsidy-family execution example
   - Test vehicle_malus execution example
   - Test portfolio composition example

4. **Phase 4: Documentation** (Knowledge transfer)
   - Create `docs/live_policy_catalog.md`
   - Document all live-ready policy types
   - Include usage examples and references
   - Review for consistency with implementation

### Key Implementation Decisions

**Test Granularity:**
- Focus on end-to-end integration over unit testing
- Test catalog → portfolio → execution → comparison flow
- Reuse existing fixtures from template subsystems
- Add minimal new fixtures (prefer shared over duplicated)

**Example Scope:**
- Keep examples lightweight (synthetic populations)
- Demonstrate key surfaced pack features (subsidy, vehicle_malus, EPA)
- Show portfolio composition with mixed policy types
- Include comparison between baseline and reform

**Documentation Audience:**
- Developers adding new policy types
- Analysts using the live policy catalog
- Operators running regression tests
- Future epic planners referencing Epic 24 patterns

**Non-Regression Strategy:**
- Run full test suite before and after changes
- Explicitly test existing pack types (carbon_tax, rebate, feebate)
- Verify portfolio save/load stability
- Check frontend-backend contract consistency

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic-24] - Epic 24 requirements
- [Source: _bmad-output/implementation-artifacts/24-1-publish-canonical-catalog-and-api-exposure-for-already-modeled-hidden-policy-packs.md] - Story 24.1 (catalog API)
- [Source: _bmad-output/implementation-artifacts/24-2-implement-domain-layer-live-translation-for-subsidy-style-policies-without-adapter-interface-changes.md] - Story 24.2 (translation)
- [Source: _bmad-output/implementation-artifacts/24-3-enable-portfolio-execution-for-surfaced-subsidy-and-related-live-policy-packs.md] - Story 24.3 (portfolio execution)
- [Source: _bmad-output/implementation-artifacts/24-4-surface-live-capable-policy-packs-in-workspace-catalog-flows-without-runtime-specific-ux.md] - Story 24.4 (UX integration)
- [Source: src/reformlab/computation/translator.py] - Translation layer implementation
- [Source: src/reformlab/server/routes/templates.py] - Catalog API routes
- [Source: src/reformlab/server/routes/portfolios.py] - Portfolio routes with CustomTypePolicy support
- [Source: tests/templates/subsidy/test_compute.py] - Subsidy test patterns
- [Source: tests/templates/energy_poverty_aid/test_compute.py] - EPA test patterns
- [Source: tests/templates/vehicle_malus/test_compute.py] - Vehicle malus test patterns
- [Source: tests/server/test_results.py] - Results API test patterns
- [Source: tests/server/test_comparison_portfolios.py] - Comparison test patterns
- [Source: examples/api/api_smoke_test.py] - Smoke test pattern

## Dev Agent Record

### Agent Model Used

claude-opus-4-6

### Debug Log References

None - Story created with comprehensive context from existing codebase.

### Completion Notes List

Story created with comprehensive developer context:
- Epic 24 closure context (Stories 24.1-24.4 completed)
- Surfaced policy pack catalog (6 live-ready types)
- Translation layer patterns from Story 24.2
- Portfolio route extensions from Story 24.3
- Frontend integration from Story 24.4
- Complete testing standards and patterns
- Example configuration structure
- Documentation requirements
- Non-regression checklist
- Implementation order recommendations

**Ready for dev:** All acceptance criteria are objectively verifiable, tasks are broken down into implementable subtasks, and dev notes provide comprehensive context from Stories 24.1-24.4 implementation.

### File List

**Story file created:**
- `_bmad-output/implementation-artifacts/24-5-add-regression-coverage-and-examples-for-the-expanded-live-policy-catalog.md`

**Files to create (implementation):**
- `tests/regression/test_surfaced_packs.py` — End-to-end surfaced pack regression tests
- `tests/regression/conftest.py` — Shared fixtures for surfaced packs
- `examples/live_policy_catalog/surfaced_packs_smoke.py` — Executable smoke examples
- `docs/live_policy_catalog.md` — Catalog documentation

**Files to reference (no changes needed):**
- `src/reformlab/computation/translator.py` — Translation layer
- `src/reformlab/server/routes/templates.py` — Catalog API
- `src/reformlab/server/routes/portfolios.py` — Portfolio routes
- `tests/templates/subsidy/test_compute.py` — Subsidy test patterns
- `tests/templates/energy_poverty_aid/test_compute.py` — EPA test patterns
- `tests/templates/vehicle_malus/test_compute.py` — Vehicle malus test patterns
- `examples/api/api_smoke_test.py` — Smoke test pattern
