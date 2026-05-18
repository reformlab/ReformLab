# Story 29.3: Restore resolved names in `_DEFAULT_LIVE_OUTPUT_VARIABLES`

Status: ready-for-dev

## Story

As a backend developer validating the live OpenFisca output path,
I want to confirm that `_DEFAULT_LIVE_OUTPUT_VARIABLES` contains only the resolved variable names from Stories 29.1 and 29.2 (no placeholders, all custom variables present),
so that live runs produce the full set of policy-relevant outputs without `ApiMappingError` failures.

## Acceptance Criteria

1. Given the current state after Stories 29.1 and 29.2, when `_DEFAULT_LIVE_OUTPUT_VARIABLES` is inspected, then it contains exactly the 9 valid variable names:
   - Core OpenFisca-France variables: `revenu_disponible`, `irpp_economique`, `impots_directs`, `salaire_net`, `prestations_sociales`
   - Custom ReformLab variables: `montant_subvention`, `eligible_subvention`, `malus_ecologique`, `aide_energie`
2. Given the four generic-name placeholder names resolved in Story 29.2, when `_DEFAULT_LIVE_OUTPUT_VARIABLES` is inspected, then none of the placeholders appear: `irpp`, `revenu_net`, `revenu_brut`, `taxe_carbone` are absent.
3. Given the derivation behavior `_DEFAULT_LIVE_OUTPUT_VARIABLES = tuple(_DEFAULT_OUTPUT_MAPPING.keys())`, when `_DEFAULT_OUTPUT_MAPPING` is updated, then `_DEFAULT_LIVE_OUTPUT_VARIABLES` automatically reflects the changes.
4. Given a live OpenFisca run using the default output variables, when execution completes, then all 9 variables resolve successfully and produce normalized output with no `ApiMappingError` for missing variables.
5. Given the four custom variables from Story 29.1, when a live run completes, then they produce non-zero values for eligible households and appear in the normalized result panel as `subsidy_amount`, `subsidy_eligible`, `vehicle_malus`, and `energy_poverty_aid`.
6. Given tests for this story, when they run, then they verify that:
   - The live output tuple contains all expected variable names and no placeholders
   - A live computation run produces results for all 9 variables
   - The custom variables produce non-zero values for eligible test households

## Tasks / Subtasks

- [ ] Verify `_DEFAULT_LIVE_OUTPUT_VARIABLES` state (AC: #1, #2, #3)
  - [ ] Confirm that the constant is derived from `_DEFAULT_OUTPUT_MAPPING.keys()` (already implemented)
  - [ ] List all 9 expected variable names in a test assertion
  - [ ] Assert that all 4 placeholder names are absent
  - [ ] Document the derivation behavior in code comments
- [ ] Verify documentation is up to date (AC: #3)
  - [ ] Update any comments or docstrings referencing placeholder names
  - [ ] Ensure the inline documentation in `result_normalizer.py` accurately reflects Story 29.2 resolution outcomes
- [ ] Add live computation integration test (AC: #4, #5)
  - [ ] Create test that runs a live OpenFisca computation with all 9 default output variables
  - [ ] Verify all 9 variables resolve and produce non-error results
  - [ ] Verify custom variables produce non-zero values for eligible households
  - [ ] Verify no `ApiMappingError` or variable-not-found errors occur
  - [ ] Test file: `tests/computation/test_live_output_integration.py` (or add to existing integration test file)
- [ ] Update test coverage for custom variables (AC: #5, #6)
  - [ ] Verify `aide_energie` produces expected values (wraps `cheque_energie`)
  - [ ] Verify `montant_subvention` produces expected values for income < 20000 EUR
  - [ ] Verify `eligible_subvention` returns True for eligible households
  - [ ] Verify `malus_ecologique` produces expected values for emissions > 118 g/km
- [ ] Quality gates
  - [ ] `uv run ruff check src/ tests/`
  - [ ] `uv run mypy src/`
  - [ ] `uv run pytest tests/computation/test_openfisca_extension.py tests/server/test_dependencies.py -v`
  - [ ] Full test suite for any newly added tests

## Dev Notes

### Critical Context for Implementation

**The Problem Chain (from Stories 29.1 and 29.2):**
- Story 24.2 added mappings for 4 custom variables but never implemented them → broke live runs
- Story 29.1 implemented the 4 custom variables as a TaxBenefitSystem extension → variables now exist
- Story 29.2 resolved 4 generic-name placeholders → mapping now uses only actual variable names
- Story 29.3 validates that the combined set works in live output

**Current State (after Stories 29.1 and 29.2):**
```python
# From result_normalizer.py
_DEFAULT_OUTPUT_MAPPING: dict[str, str] = {
    "revenu_disponible": "disposable_income",
    "irpp_economique": "income_tax",  # Was "irpp" placeholder
    "impots_directs": "direct_taxes",
    "salaire_net": "income",
    "prestations_sociales": "social_benefits",
    # Story 24.2: Subsidy-family output variable mappings
    "montant_subvention": "subsidy_amount",  # Now implemented in Story 29.1
    "eligible_subvention": "subsidy_eligible",  # Now implemented in Story 29.1
    "malus_ecologique": "vehicle_malus",  # Now implemented in Story 29.1
    "aide_energie": "energy_poverty_aid",  # Now implemented in Story 29.1
}

# Derived automatically from mapping keys
_DEFAULT_LIVE_OUTPUT_VARIABLES: tuple[str, ...] = tuple(_DEFAULT_OUTPUT_MAPPING.keys())
# Result: ('revenu_disponible', 'irpp_economique', 'impots_directs', 'salaire_net',
#          'prestations_sociales', 'montant_subvention', 'eligible_subvention',
#          'malus_ecologique', 'aide_energie')
```

**The Solution (already implemented):**
- `_DEFAULT_LIVE_OUTPUT_VARIABLES` is derived from `_DEFAULT_OUTPUT_MAPPING.keys()` via tuple()
- When Story 29.2 replaced `irpp` with `irpp_economique`, the live output automatically included the resolved name
- When Story 29.2 removed `revenu_net`, `revenu_brut`, `taxe_carbone`, the live output automatically excluded them
- When Story 29.1 implemented the 4 custom variables, they became resolvable in live runs

**This Story's Purpose:**
- Validation and testing story — confirm the derivation works as intended
- Add integration test proving all 9 variables resolve in a live run
- Ensure no regressions from the placeholder resolution work

### Dependency Chain

```
Story 29.1 (custom variables)  AND  Story 29.2 (placeholder resolution)
                         ↓
                 Both complete → variables exist and mapping is correct
                         ↓
                  Story 29.3 (this story) — validate live output
                         ↓
                  Story 29.4 — test fixture cleanup
                         ↓
                  Story 29.5 — regression tests
```

### Key Architectural Constraints

1. **Derivation behavior is intentional** — `_DEFAULT_LIVE_OUTPUT_VARIABLES` is deliberately derived from mapping keys, not hardcoded
2. **Adapter isolation is absolute** — Only `openfisca_api_adapter.py` loads the extension
3. **OpenFisca is optional** — Tests must use `pytest.importorskip` gating
4. **PyArrow is canonical** — All computation results use `pa.Table`

### Test Requirements

**Live Output Validation Test:**
```python
def test_live_output_contains_all_resolved_variables():
    """Test that _DEFAULT_LIVE_OUTPUT_VARIABLES contains all 9 expected names."""
    from reformlab.computation.result_normalizer import _DEFAULT_LIVE_OUTPUT_VARIABLES

    # Core OpenFisca-France variables (5)
    assert "revenu_disponible" in _DEFAULT_LIVE_OUTPUT_VARIABLES
    assert "irpp_economique" in _DEFAULT_LIVE_OUTPUT_VARIABLES
    assert "impots_directs" in _DEFAULT_LIVE_OUTPUT_VARIABLES
    assert "salaire_net" in _DEFAULT_LIVE_OUTPUT_VARIABLES
    assert "prestations_sociales" in _DEFAULT_LIVE_OUTPUT_VARIABLES

    # Custom ReformLab variables (4)
    assert "montant_subvention" in _DEFAULT_LIVE_OUTPUT_VARIABLES
    assert "eligible_subvention" in _DEFAULT_LIVE_OUTPUT_VARIABLES
    assert "malus_ecologique" in _DEFAULT_LIVE_OUTPUT_VARIABLES
    assert "aide_energie" in _DEFAULT_LIVE_OUTPUT_VARIABLES

    # Placeholder names should NOT be present
    assert "irpp" not in _DEFAULT_LIVE_OUTPUT_VARIABLES
    assert "revenu_net" not in _DEFAULT_LIVE_OUTPUT_VARIABLES
    assert "revenu_brut" not in _DEFAULT_LIVE_OUTPUT_VARIABLES
    assert "taxe_carbone" not in _DEFAULT_LIVE_OUTPUT_VARIABLES
```

**Live Computation Integration Test:**
```python
@pytest.mark.skipif(
    not os.getenv("REFORMLAB_RUN_LIVE_TESTS"),
    reason="Live integration tests require REFORMLAB_RUN_LIVE_TESTS=1"
)
def test_live_computation_with_all_default_variables():
    """Test that live computation produces all 9 expected output variables."""
    from reformlab.computation.openfisca_api_adapter import OpenFiscaApiAdapter
    from reformlab.computation.result_normalizer import (
        _DEFAULT_LIVE_OUTPUT_VARIABLES,
        normalize_computation_result,
    )
    from reformlab.computation.types import PopulationData

    # Create minimal test population with required columns
    # Run live computation
    # Verify all 9 variables appear in result
    # Verify no ApiMappingError occurs
```

**Custom Variable Values Test:**
- Test that eligible households receive non-zero subsidy amounts
- Test that `malus_ecologique` produces positive values for high-emission vehicles
- Test that `aide_energie` produces expected values (delegates to `cheque_energie`)

### Files to Reference

**Read-Only Context:**
- `src/reformlab/computation/result_normalizer.py:91-96` — Current `_DEFAULT_LIVE_OUTPUT_VARIABLES` and docstring
- `src/reformlab/computation/result_normalizer.py:73-89` — Current `_DEFAULT_OUTPUT_MAPPING` with all 9 variables
- `src/reformlab/computation/openfisca_api_adapter.py` — Extension loading implementation
- `src/reformlab/computation/openfisca_extension/` — Custom variable implementations
- `tests/computation/test_openfisca_extension.py` — Existing extension tests

**May Modify (if documentation updates needed):**
- `src/reformlab/computation/result_normalizer.py` — Update docstring if it still references old state

**New Tests:**
- Add to `tests/computation/test_openfisca_extension.py` OR create `tests/computation/test_live_output_integration.py`

### Expected Outcomes

After this story:
- `_DEFAULT_LIVE_OUTPUT_VARIABLES` contains exactly 9 variable names (all resolvable)
- No placeholder names appear in the live output tuple
- Live runs succeed with all 9 variables producing output
- Tests validate the complete live output path from computation → normalization → result

### Quality Gates

```bash
# Linting
uv run ruff check src/ tests/

# Type checking
uv run mypy src/

# Run extension tests
uv run pytest tests/computation/test_openfisca_extension.py -v

# Run dependency tests (includes _DEFAULT_LIVE_OUTPUT_VARIABLES tests)
uv run pytest tests/server/test_dependencies.py::TestDefaultLiveOutputVariables -v

# Run new integration tests
uv run pytest tests/computation/test_live_output_integration.py -v
```

### Dependencies

**Requires:** Stories 29.1 AND 29.2 complete
**Blocks:** Story 29.4 (test fixture cleanup)

### Project Structure Notes

**Modified:**
- `src/reformlab/computation/result_normalizer.py` — Only if documentation needs updating

**New Tests:**
- `tests/computation/test_live_output_integration.py` — New integration test file OR add to existing extension tests

### References

- [Source: src/reformlab/computation/result_normalizer.py:73-96] — Default mapping and live output variables
- [Source: _bmad-output/implementation-artifacts/29-1-implement-custom-openfisca-variables-subsidy-malus-energy-aid.md] — Story 29.1 completion state
- [Source: _bmad-output/implementation-artifacts/29-2-resolve-generic-name-placeholders.md] — Story 29.2 completion state
- [Source: tests/computation/test_openfisca_extension.py] — Existing custom variable tests
- [Source: tests/server/test_dependencies.py:125-146] — Existing `_DEFAULT_LIVE_OUTPUT_VARIABLES` tests

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

No debug logs. Story creation based on comprehensive analysis of Stories 29.1 and 29.2 completion states, Epic 29 context, and current codebase state.

### Completion Notes List

1. **Epic 29 Analysis Complete** — Reviewed Epic 29 scope and dependency chain: 29.1 + 29.2 → 29.3 → 29.4 → 29.5.
2. **Story 29.1 State Understood** — Four custom variables implemented as TaxBenefitSystem extension; extension loading integrated into adapter.
3. **Story 29.2 State Understood** — Placeholder names resolved: `irpp` → `irpp_economique`, `revenu_net`/`revenu_brut`/`taxe_carbone` removed.
4. **Derivation Behavior Confirmed** — `_DEFAULT_LIVE_OUTPUT_VARIABLES = tuple(_DEFAULT_OUTPUT_MAPPING.keys())` automatically reflects mapping changes.
5. **Live Output State Validated** — Current `_DEFAULT_LIVE_OUTPUT_VARIABLES` contains all 9 expected variable names and no placeholders.
6. **Story Purpose Clarified** — This is a validation/testing story; the core changes are complete from 29.1 and 29.2.
7. **Test Strategy Defined** — Focus on integration tests that validate the full live output path and custom variable value production.
8. **Acceptance Criteria Specified** — Six criteria covering tuple contents, placeholder absence, derivation behavior, live run success, custom variable values, and test coverage.
9. **Existing Story File Replaced** — Previous file had outdated assumptions (referenced `impot_revenu_restant_a_payer`, `taxe_carbone` as additions). Replaced with accurate context based on actual completion states.

### File List

**Context Files Read:**
- `src/reformlab/computation/result_normalizer.py` — Verified current state of `_DEFAULT_OUTPUT_MAPPING` and `_DEFAULT_LIVE_OUTPUT_VARIABLES`
- `tests/server/test_dependencies.py` — Reviewed existing test coverage for live output variables
- `tests/computation/test_openfisca_extension.py` — Reviewed existing custom variable tests
- `_bmad-output/implementation-artifacts/29-1-implement-custom-openfisca-variables-subsidy-malus-energy-aid.md` — Story 29.1 completion state
- `_bmad-output/implementation-artifacts/29-2-resolve-generic-name-placeholders.md` — Story 29.2 completion state

**Files to Modify (if needed):**
- `src/reformlab/computation/result_normalizer.py` — Only if documentation updates needed

**New Test Files to Create:**
- `tests/computation/test_live_output_integration.py` — Integration tests for live output with all 9 variables
