# Story 29.1: Implement custom OpenFisca variables (subsidy_amount, subsidy_eligible, vehicle_malus, energy_poverty_aid)

Status: ready-for-dev

## Story

As a backend developer maintaining the live OpenFisca path,
I want the four French-named output variables (`montant_subvention`, `eligible_subvention`, `malus_ecologique`, `aide_energie`) implemented as custom variables in a registered TaxBenefitSystem extension,
so that the existing `_DEFAULT_OUTPUT_MAPPING` references resolve at runtime and the live path can produce subsidy/malus/energy-aid outputs.

## Acceptance Criteria

1. Given the existing mapping at `src/reformlab/computation/result_normalizer.py` referencing `montant_subvention`, `eligible_subvention`, `malus_ecologique`, and `aide_energie`, when a live OpenFisca run completes, then the four variables resolve and their values appear in the normalised result panel as `subsidy_amount`, `subsidy_eligible`, `vehicle_malus`, and `energy_poverty_aid` respectively.
2. Given the registered TaxBenefitSystem extension under `src/reformlab/`, when inspected, then it defines the four custom variables with appropriate entity assignment, definition_period, value_type, and formula(s) consistent with French tax-benefit conventions.
3. Given the analyst PM has reviewed the `cheque_energie` question (the OpenFisca core variable that may already cover energy-poverty-aid), when this story starts, then the spec records the decision: implement a fresh `aide_energie` OR alias the mapping to `cheque_energie`. Pick one.
4. Given the four custom variables, when invoked on a synthetic population, then they produce non-zero values for households satisfying the eligibility criteria (e.g., subsidy eligible based on income threshold and policy parameters).
5. Given the test suite, when this story is complete, then each custom variable has a unit test asserting: (a) variable resolves at simulation time, (b) value matches expected formula output for at least three test cases, (c) value type and definition period match the variable definition.
6. Given the manifest produced by a live run, when inspected, then it captures the custom variables and the version of the registered extension so reproducibility is preserved.

## Tasks / Subtasks

- [ ] PM decision on `aide_energie` vs `cheque_energie` (AC: #3)
  - [ ] Coordinate with PM (or analyst) to decide whether to implement a fresh `aide_energie` or alias to existing `cheque_energie`
  - [ ] Record the decision in this story's Dev Notes section before implementation
- [ ] Identify or create the registered extension (AC: #2)
  - [ ] Search for the existing TaxBenefitSystem extension under `src/reformlab/computation/` or `src/reformlab/templates/`
  - [ ] If none, create a new extension module (e.g., `src/reformlab/computation/openfisca_extension/`) with a `register()` entrypoint
- [ ] Implement `subsidy_amount` and `subsidy_eligible` (AC: #2, #4)
  - [ ] Define `subsidy_amount` (value_type=float, entity=household, definition_period=year)
  - [ ] Define `subsidy_eligible` (value_type=bool, entity=household, definition_period=year)
  - [ ] Implement formulas using existing parameter inputs from `_DEFAULT_OUTPUT_MAPPING`
- [ ] Implement `vehicle_malus` (AC: #2, #4)
  - [ ] Define `vehicle_malus` (value_type=float, entity=household or person)
  - [ ] Implement formula based on vehicle CO2 emissions parameters (existing `vehicle_co2` columns from population schema)
- [ ] Implement `energy_poverty_aid` (AC: #2, #3, #4)
  - [ ] Either implement fresh `aide_energie` per the PM decision OR add an alias mapping in `_DEFAULT_OUTPUT_MAPPING` to point to `cheque_energie`
- [ ] Register extension in adapter (AC: #2)
  - [ ] Wire the extension into the `ComputationAdapter` initialisation so live runs see the custom variables
  - [ ] Verify no non-computation module imports the extension directly (CLAUDE.md constraint)
- [ ] Tests (AC: #4, #5)
  - [ ] Unit tests for each custom variable (3+ cases each)
  - [ ] Integration test: live run on Quick Test Population produces non-zero values for at least one eligible household
- [ ] Manifest update (AC: #6)
  - [ ] Verify the manifest captures the extension version
  - [ ] If not, add a `custom_variables_version` field
- [ ] Quality gates
  - [ ] `uv run ruff check src/ tests/`, `uv run mypy src/`, `uv run pytest tests/computation/ tests/server/`

## Dev Notes

### Critical Context for Implementation

**The Problem:**
- Story 24.2 added mappings for four custom variables to `_DEFAULT_OUTPUT_MAPPING`: `montant_subvention`, `eligible_subvention`, `malus_ecologique`, `aide_energie`
- These variables were never actually implemented in OpenFisca-France
- The 2026-04-26 hotfix narrowed `_DEFAULT_LIVE_OUTPUT_VARIABLES` to exclude these eight unresolvable names
- Live runs currently fail if these variables are requested because they don't exist in the TBS

**The Solution:**
- Create custom OpenFisca Variable classes that extend OpenFisca-France
- Register them as a ReformLab-specific TaxBenefitSystem extension
- Wire the extension into `OpenFiscaApiAdapter` initialization

**Key Architectural Constraints:**
1. **Adapter isolation is absolute** — Only modules under `src/reformlab/computation/` may import OpenFisca. No other module should import the extension directly.
2. **All imports must be lazy** — OpenFisca is an optional dependency. Use `if TYPE_CHECKING:` guards and runtime imports.
3. **Frozen dataclasses are default** — Configuration types must use `@dataclass(frozen=True)`.
4. **PyArrow is canonical** — All tabular data uses `pa.Table`; no pandas DataFrames in core logic.

### Existing Implementation Patterns

**Template-Side Logic (Already Working):**
- `src/reformlab/templates/subsidy/compute.py` — Has subsidy eligibility and amount formulas
- `src/reformlab/templates/vehicle_malus/compute.py` — Has malus calculation based on emissions
- `src/reformlab/templates/energy_poverty_aid/compute.py` — Has aid calculation based on energy burden

**OpenFisca Variable Structure:**
Each custom variable must define:
```python
class MontantSubvention(Variable):
    value_type = float
    entity = Menage  # or FoyerFiscal, Individu
    definition_period = YEAR
    label = "Montant de la subvention"
    documentation = """Subsidy amount for eligible households."""

    def formula(menage, period, parameters):
        # Formula logic here
        return ...
```

**TaxBenefitSystem Extension Pattern:**
OpenFisca allows extending the country package with custom variables via:
1. Creating a Python module with Variable classes
2. Registering them with `CountryTaxBenefitSystem` using `add_variable()`
3. Loading the extended TBS in the adapter

### Variable Specifications

**1. montant_subvention (subsidy_amount)**
- Type: `float`
- Entity: `Menage` (household)
- Period: `YEAR`
- Formula: Returns subsidy amount based on eligibility criteria and rate schedule
- Reference: `src/reformlab/templates/subsidy/compute.py:121-161`

**2. eligible_subvention (subsidy_eligible)**
- Type: `bool`
- Entity: `Menage`
- Period: `YEAR`
- Formula: Returns `True` if household meets income cap and category eligibility
- Reference: `src/reformlab/templates/subsidy/compute.py:60-118`

**3. malus_ecologique (vehicle_malus)**
- Type: `float`
- Entity: `Menage` (household-level penalty)
- Period: `YEAR`
- Formula: `max(0, emissions - threshold) * rate_per_gkm`
- Reference: `src/reformlab/templates/vehicle_malus/compute.py:96-153`

**4. aide_energie (energy_poverty_aid)**
- Type: `float`
- Entity: `Menage`
- Period: `YEAR`
- Formula: `base_aid * income_ratio * energy_burden_factor` for eligible households
- Reference: `src/reformlab/templates/energy_poverty_aid/compute.py:132-282`
- **PM Decision Required**: Either implement fresh or alias to existing `cheque_energie` if it exists in OpenFisca-France

### Implementation Locations

**New Files to Create:**
```
src/reformlab/computation/
├── openfisca_extension/
│   ├── __init__.py
│   ├── subsidy_variables.py
│   ├── vehicle_variables.py
│   ├── energy_variables.py
│   └── extension.py
```

**Files to Modify:**
- `src/reformlab/computation/openfisca_api_adapter.py` — Load extension during TBS initialization
- `src/reformlab/computation/result_normalizer.py` — Only if alias needed for `aide_energie`

**Test Files:**
```
tests/computation/
├── test_openfisca_extension.py
└── test_custom_variables.py
```

### Testing Strategy

1. **Unit Tests** (per variable, AC: #5)
   - Test variable resolves at simulation time
   - Test formula output matches expected values for 3+ cases
   - Test value_type and definition_period match specification

2. **Integration Test** (AC: #4)
   - Run live computation on Quick Test Population
   - Verify non-zero values for eligible households

3. **Manifest Test** (AC: #6)
   - Verify manifest captures extension version
   - Add `custom_variables_version` field if missing

### Quality Gates

Run these before marking the story done:
```bash
# Backend
uv run ruff check src/reformlab/computation/openfisca_extension/ tests/computation/test_openfisca_extension.py
uv run mypy src/reformlab/computation/openfisca_extension/
uv run pytest tests/computation/test_openfisca_extension.py -v
```

### Dependencies

This story is the parent of:
- **Story 29.2** — Resolve generic-name placeholders (`irpp`, `revenu_net`, `revenu_brut`, `taxe_carbone`)
- **Story 29.3** — Restore resolved names in `_DEFAULT_LIVE_OUTPUT_VARIABLES`

**Sequence**: 29.1 → 29.2 → 29.3

### Project Structure Notes

**New:**
- `src/reformlab/computation/openfisca_extension/` — Custom variable modules
- `tests/computation/test_openfisca_extension.py` — Extension tests

**Modified:**
- `src/reformlab/computation/openfisca_api_adapter.py` — Load extension
- `src/reformlab/computation/result_normalizer.py` — Only if alias needed

### References

- [Source: _bmad-output/implementation-artifacts/deferred-work.md:19-25] — Parent context
- [Source: src/reformlab/computation/result_normalizer.py:46-60] — `_DEFAULT_OUTPUT_MAPPING` with custom variable names
- [Source: src/reformlab/computation/result_normalizer.py:63-66] — `_DEFAULT_LIVE_OUTPUT_VARIABLES` (narrowed by hotfix)
- [Source: src/reformlab/templates/subsidy/compute.py] — Existing subsidy formulas to adapt
- [Source: src/reformlab/templates/vehicle_malus/compute.py] — Existing malus formulas to adapt
- [Source: src/reformlab/templates/energy_poverty_aid/compute.py] — Existing aid formulas to adapt
- [Source: _bmad-output/planning-artifacts/architecture.md#3.1] — Adapter pattern constraint

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

No debug logs. Story created from comprehensive codebase analysis.

### Completion Notes List

1. **Architecture Analysis Complete** — Reviewed `src/reformlab/computation/` subsystem structure, adapter pattern constraints, and OpenFisca integration patterns
2. **Existing Implementations Mapped** — Located template-side formulas in `subsidy/compute.py`, `vehicle_malus/compute.py`, `energy_poverty_aid/compute.py` that need adaptation to OpenFisca Variable format
3. **Hotfix Context Understood** — The 2026-04-26 hotfix narrowed `_DEFAULT_LIVE_OUTPUT_VARIABLES` from 12 to 4 variables; this story restores 4 of the 8 that were excluded
4. **Dependency Chain Clear** — This story (29.1) enables 29.2 (generic placeholders) and 29.3 (restore full live output set)
5. **PM Decision Needed** — AC-#3 requires deciding between fresh `aide_energie` implementation or aliasing to existing `cheque_energie`

### File List

**New Files to Create:**
- `src/reformlab/computation/openfisca_extension/__init__.py` — Extension module init
- `src/reformlab/computation/openfisca_extension/subsidy_variables.py` — `MontantSubvention`, `EligibleSubvention` classes
- `src/reformlab/computation/openfisca_extension/vehicle_variables.py` — `MalusEcologique` class
- `src/reformlab/computation/openfisca_extension/energy_variables.py` — `AideEnergie` class (or alias logic)
- `src/reformlab/computation/openfisca_extension/extension.py` — Extension registration and loader
- `tests/computation/test_openfisca_extension.py` — Extension loading and variable resolution tests
- `tests/computation/test_custom_variables.py` — Formula validation tests per variable

**Files to Modify:**
- `src/reformlab/computation/openfisca_api_adapter.py` — Load extension during TBS initialization
- `src/reformlab/computation/result_normalizer.py` — Only if alias needed for `aide_energie` mapping

**Reference Files (Read-Only Context):**
- `src/reformlab/computation/result_normalizer.py:46-60` — Current `_DEFAULT_OUTPUT_MAPPING`
- `src/reformlab/computation/result_normalizer.py:63-66` — Current `_DEFAULT_LIVE_OUTPUT_VARIABLES`
- `src/reformlab/templates/subsidy/compute.py:60-161` — Subsidy formulas to adapt
- `src/reformlab/templates/vehicle_malus/compute.py:96-153` — Malus formulas to adapt
- `src/reformlab/templates/energy_poverty_aid/compute.py:132-282` — Aid formulas to adapt
- `_bmad-output/planning-artifacts/architecture.md:3.1` — Adapter pattern constraint documentation
