
# Story 9.5: OpenFisca-France Reference Test Suite

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **platform developer maintaining the OpenFisca adapter**,
I want a comprehensive reference test suite that validates adapter output against known French tax-benefit values across diverse household compositions and income levels,
so that regressions are detected immediately when OpenFisca-France is upgraded, and the adapter's correctness is continuously validated in CI.

## Context & Motivation

The adapter pipeline is now feature-complete for French tax-benefit integration:
- **Story 9.2** added multi-entity output array handling (per-entity tables for individu, foyer_fiscal, menage)
- **Story 9.3** added periodicity-aware calculation dispatch (monthly → `calculate_add`, yearly → `calculate`)
- **Story 9.4** added 4-entity PopulationData format with membership columns

However, the existing integration tests are **feature-validation tests** — they prove that each story's implementation works. What's missing is a **systematic reference test suite** that:

1. **Covers the French tax-benefit model systematically** — not just a few ad-hoc income levels, but a structured set of scenarios covering the progressive tax bracket structure, family quotient, and multi-entity outputs.
2. **Tests through `adapter.compute()` end-to-end** — many existing tests use `_build_simulation()` directly (bypassing the adapter's entity dict construction, periodicity resolution, and result extraction). The reference suite must validate the full pipeline.
3. **Cross-validates 4-entity format** — the membership column path (Story 9.4) must produce identical results to the legacy path for equivalent populations. This cross-validation is the definitive proof that the 4-entity format works correctly.
4. **Provides regression detection scaffolding** — when OpenFisca-France is upgraded from 175.x to a new major version, the reference suite should be the first thing that breaks, with clear failure messages showing expected vs actual values and the OpenFisca version.

**Source:** Spike 8-1 findings, recommended follow-up #5: "Production integration test suite — Expand from this spike's 16 tests to a broader regression suite covering more French tax-benefit variables." [Source: `_bmad-output/implementation-artifacts/spike-findings-8-1-openfisca-integration.md`, line 108]

**Epic 9 AC:** "A reference test suite validates adapter output against known French tax-benefit values." [Source: `_bmad-output/planning-artifacts/epics.md`, Epic 9 acceptance criteria]

## Acceptance Criteria

1. **AC-1: Known-value validation** — Given a set of known French tax-benefit scenarios covering at least: (a) single persons at 3+ income levels spanning different tax brackets, (b) a married couple with joint taxation, (c) a family with children, when run through `adapter.compute()`, then computed values match reference values within the documented `ABSOLUTE_ERROR_MARGIN = 0.5` EUR tolerance.

2. **AC-2: CI integration** — Given the reference test suite, when run in CI with `uv run pytest tests/computation/test_openfisca_integration.py -m integration`, then all tests pass and tolerance thresholds are documented as class-level constants with docstring explanations.

3. **AC-3: Regression detection** — Given the reference test suite, when a new OpenFisca-France version changes a tax computation value, then the test failure message includes: (a) the expected reference value, (b) the actual computed value, (c) the tolerance, and (d) the pinned OpenFisca-France version that produced the reference value — providing all information needed to decide whether the change is expected (parameter update) or a regression.

4. **AC-4: Full-pipeline coverage** — Given all reference scenarios, when tested, then each scenario is exercised through `adapter.compute()` (not `_build_simulation()` directly) — validating the full adapter pipeline including entity dict construction, periodicity resolution, calculation dispatch, and per-entity result extraction.

5. **AC-5: 4-entity format cross-validation** — Given at least one multi-person reference scenario (e.g., married couple), when tested through both the 4-entity format (membership columns) and the legacy format (adapter auto-creation or hand-built entity dicts), then results match within tolerance — cross-validating Story 9.4's implementation against the existing proven path.

6. **AC-6: Multi-entity output validation** — Given at least one reference scenario that requests output variables from multiple entities (e.g., `salaire_net` from individu + `impot_revenu_restant_a_payer` from foyer_fiscal + `revenu_disponible` from menage), when run through `adapter.compute()`, then `entity_tables` contains per-entity tables with correct array lengths and reasonable values.

7. **AC-7: Existing tests unbroken** — Given all pre-existing integration tests in `test_openfisca_integration.py`, when the reference test suite is added, then no existing tests are modified or broken.

## Tasks / Subtasks

- [ ] Task 1: Define reference test scenarios and compute expected values (AC: #1, #3)
  - [ ] 1.1 Create a script or notebook cell (NOT committed) to compute reference values using direct OpenFisca-France calls. Pin all reference values against openfisca-france 175.x / openfisca-core 44.2.2. Document the exact OpenFisca-France version in the test class docstring
  - [ ] 1.2 Compute reference values for single-person scenarios at multiple income levels. Use `salaire_imposable` as the input variable (matching openfisca-france's own test format). Scenarios:
      - **Zero income:** `salaire_imposable=0` → `irpp=0.0` (no tax)
      - **Low income (near SMIC):** `salaire_imposable=15000` → expected irpp (decote may apply)
      - **Mid income:** `salaire_imposable=30000` → known reference (existing tests use ~-1200 for `salaire_de_base=30000`, but `salaire_imposable` is a different variable — recompute)
      - **Upper bracket:** `salaire_imposable=75000` → known reference
      - **High income:** `salaire_imposable=100000` → known reference
  - [ ] 1.3 Compute reference values for family scenarios:
      - **Married couple, dual income:** `salaire_imposable` 40000+30000 → expected joint irpp
      - **Family with 1 child:** 2 parents + 1 enfant, demonstrate `quotient_familial` 2.5 parts advantage
      - **Family with 2 children:** 2 parents + 2 enfants, demonstrate 3 parts
  - [ ] 1.4 Compute reference values for multi-entity output:
      - **Single person multi-entity:** `salaire_net` (individu, monthly) + `impot_revenu_restant_a_payer` (foyer_fiscal, yearly) + `revenu_disponible` (menage, yearly) for a 30k earner
  - [ ] 1.5 Record all reference values in a structured format within the test class docstring, including the exact OpenFisca-France version used, the date computed, and the tolerance

- [ ] Task 2: Implement single-person income tax reference cases via `adapter.compute()` (AC: #1, #3, #4)
  - [ ] 2.1 Create a new test class `TestAdapterReferenceSinglePerson` in `tests/computation/test_openfisca_integration.py`. Docstring must document: pinned OpenFisca-France version, date of reference value computation, tolerance, and purpose (regression detection)
  - [ ] 2.2 Add class attribute `ABSOLUTE_ERROR_MARGIN = 0.5` and `REFERENCE_OPENFISCA_FRANCE_VERSION = "175.0.18"` (or current installed version)
  - [ ] 2.3 For each single-person scenario, create a test method that: (a) constructs a `PopulationData` with a single individu table containing `salaire_imposable`, (b) calls `adapter.compute(population, empty_policy, 2024)`, (c) asserts the `impot_revenu_restant_a_payer` value matches the reference within tolerance, (d) uses a clear assertion message: `f"Expected {expected}, got {actual} (tolerance ±{margin}, ref: OpenFisca-France {version})"`
  - [ ] 2.4 Add a test for **progressive tax monotonicity**: given the full set of reference income levels, assert that tax increases (becomes more negative) monotonically with income. This is a structural test that catches any reference value errors
  - [ ] 2.5 Mark all tests with `@pytest.mark.integration`

- [ ] Task 3: Implement family reference cases via `adapter.compute()` with 4-entity format (AC: #1, #3, #4, #5)
  - [ ] 3.1 Create a new test class `TestAdapterReferenceFamilies` in `tests/computation/test_openfisca_integration.py`. Same docstring and class attributes as Task 2
  - [ ] 3.2 **Married couple test:** construct a `PopulationData` with membership columns (famille_id, famille_role, foyer_fiscal_id, foyer_fiscal_role, menage_id, menage_role) for 2 persons in 1 foyer_fiscal. Use `salaire_imposable` as input. Assert joint irpp matches reference value. ⚠️ This tests the FULL 4-entity pipeline through `adapter.compute()`
  - [ ] 3.3 **Family with child test:** 3 persons (2 parents + 1 enfant with age=10) with membership columns expressing correct roles in all 3 group entities. The child is `personnes_a_charge` in foyer_fiscal, `enfants` in famille and menage. Assert joint irpp with 2.5-part quotient
  - [ ] 3.4 **Family with 2 children test:** 4 persons (2 parents + 2 enfants). Assert quotient familial advantage: family pays less tax than a couple with same total income
  - [ ] 3.5 **Quotient familial structural test:** assert that a married couple with children pays LESS tax than a couple without children (when total income is the same). This is a structural invariant of French tax law

- [ ] Task 4: Implement 4-entity format cross-validation (AC: #5)
  - [ ] 4.1 Create a test class `TestFourEntityCrossValidation` (or add to an existing appropriate class)
  - [ ] 4.2 **Cross-validation test:** for the married couple scenario, run `adapter.compute()` twice: once with the 4-entity format (membership columns on person table) and once with a single-person-per-household setup (auto-created entities, legacy path). For the single-person case, run 2 separate single-person computes and compare the SUM of individual irpp values to the couple's joint irpp. Document that the difference demonstrates the quotient familial benefit (couple pays LESS than sum of singles)
  - [ ] 4.3 **Alternative cross-validation**: For a SINGLE person, run `adapter.compute()` both with and without membership columns. Assert results are identical within tolerance. This directly validates that the 4-entity path produces the same result as the auto-creation path for the simplest case
  - [ ] 4.4 ⚠️ Do NOT call `_build_simulation()` directly in cross-validation tests — the purpose is to validate the adapter pipeline, not to replicate the existing `TestOpenFiscaFranceReferenceCases` tests (which already use `_build_simulation()`)

- [ ] Task 5: Implement multi-entity output reference cases (AC: #4, #6)
  - [ ] 5.1 Create a new test class `TestAdapterReferenceMultiEntity`
  - [ ] 5.2 **Single-person multi-entity test:** Use adapter with `output_variables=("salaire_net", "impot_revenu_restant_a_payer", "revenu_disponible")`. Construct a single-person population (30k salary). Assert:
      - `entity_tables` contains 3 entity keys: `"individus"`, `"foyers_fiscaux"`, `"menages"`
      - `entity_tables["individus"].num_rows == 1` (1 person)
      - `entity_tables["foyers_fiscaux"].num_rows == 1` (1 foyer)
      - `entity_tables["menages"].num_rows == 1` (1 menage)
      - `salaire_net > 0` and in reasonable range (20k-30k for 30k gross)
      - `impot_revenu_restant_a_payer < 0` (tax owed)
      - `revenu_disponible > 0` (positive disposable income)
      - Metadata `calculation_methods` shows `"salaire_net": "calculate_add"` and `"impot_revenu_restant_a_payer": "calculate"`
  - [ ] 5.3 **Married couple multi-entity test:** Use adapter with same 3 output variables. Construct couple via 4-entity format. Assert:
      - `entity_tables["individus"].num_rows == 2` (2 persons)
      - `entity_tables["foyers_fiscaux"].num_rows == 1` (1 foyer — joint filing)
      - `entity_tables["menages"].num_rows == 1` (1 menage)
      - Correct per-entity variable assignment (salaire_net on individus, irpp on foyers_fiscaux, revenu_disponible on menages)
  - [ ] 5.4 **Two independent households multi-entity test:** 2 persons in separate foyers/menages. Assert all entity tables have 2 rows

- [ ] Task 6: Add regression detection metadata (AC: #3)
  - [ ] 6.1 Add a shared module-scope fixture `reference_adapter` with the multi-entity output variable configuration, cached like the existing `adapter` and `multi_entity_adapter` fixtures
  - [ ] 6.2 Add a test `test_openfisca_france_version_documented` that asserts `adapter.version()` returns a version starting with `"44."` (openfisca-core 44.x). If the core version changes, this test forces explicit review of all reference values. Document in the docstring that this test is intentionally version-pinned for regression detection
  - [ ] 6.3 Ensure ALL assertion messages in reference tests include: (a) expected value, (b) actual value, (c) tolerance, (d) a note pointing to the reference version. Use a consistent format:
      ```python
      assert abs(float(actual) - expected) <= self.ABSOLUTE_ERROR_MARGIN, (
          f"Expected {expected}, got {actual} "
          f"(tolerance ±{self.ABSOLUTE_ERROR_MARGIN}, "
          f"ref: OpenFisca-France {self.REFERENCE_OPENFISCA_FRANCE_VERSION})"
      )
      ```
  - [ ] 6.4 Add a class-level constant `REFERENCE_DATE = "2026-03-01"` documenting when reference values were computed. This helps during version upgrades to understand how stale the reference values are

- [ ] Task 7: Verify backward compatibility (AC: #7)
  - [ ] 7.1 Run ALL existing integration tests unchanged: `uv run pytest tests/computation/test_openfisca_integration.py -m integration`
  - [ ] 7.2 Verify no imports added or removed that could affect other test classes
  - [ ] 7.3 Verify the existing `TestOpenFiscaFranceReferenceCases` class is NOT modified — it remains the direct-simulation reference. Story 9.5 adds the adapter-pipeline reference

- [ ] Task 8: Run quality gates (all ACs)
  - [ ] 8.1 `uv run ruff check src/ tests/`
  - [ ] 8.2 `uv run mypy src/`
  - [ ] 8.3 `uv run pytest tests/computation/ -m integration` (all integration tests pass)
  - [ ] 8.4 `uv run pytest tests/computation/ -m "not integration"` (all unit tests still pass)
  - [ ] 8.5 `uv run pytest tests/orchestrator/` (no orchestrator regressions)

## Dev Notes

### This is a TEST-ONLY Story

**No adapter code changes.** Story 9.5 adds integration tests to `tests/computation/test_openfisca_integration.py` only. The adapter pipeline was completed in Stories 9.2-9.4. This story validates correctness systematically.

### Relationship to Existing Tests

The existing integration test file (`test_openfisca_integration.py`) already contains:

| Test Class | Stories | Approach | Count |
|---|---|---|---|
| `TestTaxBenefitSystemLoading` | 8.1 | Direct TBS access | 3 |
| `TestAdapterComputeEndToEnd` | 8.1 | `adapter.compute()` | 3 |
| `TestMultiEntityPopulation` | 8.1 | `_build_simulation()` direct | 3 |
| `TestVariableMappingRoundTrip` | 8.1 | Direct simulation + mapping | 2 |
| `TestOutputQualityValidation` | 8.1 | `adapter.compute()` + validation | 1 |
| `TestKnownValueBenchmark` | 8.1 | Direct simulation | 2 |
| `TestAdapterPluralKeyFix` | 8.1 | `adapter.compute()` + direct | 3 |
| `TestOpenFiscaFranceReferenceCases` | 8.1 | `_build_simulation()` direct | 4 |
| `TestMultiEntityOutputArrays` | 9.2 | Mixed (adapter + direct) | 4 |
| `TestVariablePeriodicityHandling` | 9.3 | `adapter.compute()` | 5 |
| `TestFourEntityPopulationFormat` | 9.4 | `adapter.compute()` | 6 |

**Story 9.5 adds:** Systematic reference tests that go through `adapter.compute()` end-to-end with pinned expected values and regression-detection metadata. The new test classes complement (not replace) the existing ones.

### Key Difference: `_build_simulation()` vs `adapter.compute()`

**Existing `TestOpenFiscaFranceReferenceCases` uses `_build_simulation()` directly.** This bypasses the adapter's `_population_to_entity_dict()`, periodicity resolution, and entity-aware result extraction. It validates OpenFisca-France itself, not the adapter pipeline.

**Story 9.5 tests MUST use `adapter.compute()`.** This validates the full stack:
1. `_validate_period()` — period check
2. `_get_tax_benefit_system()` — TBS loading
3. `_validate_output_variables()` — variable validation
4. `_resolve_variable_entities()` — entity grouping
5. `_resolve_variable_periodicities()` — periodicity detection
6. `_build_simulation()` → `_population_to_entity_dict()` — entity dict construction (including 4-entity membership columns)
7. `_extract_results_by_entity()` → `_calculate_variable()` — periodicity-aware calculation dispatch
8. `_select_primary_output()` — backward-compatible output selection

### Input Variable Choice: `salaire_imposable` vs `salaire_de_base`

**Use `salaire_imposable` for income tax reference tests** (matching openfisca-france's own test format and the existing `TestOpenFiscaFranceReferenceCases`). This is the taxable salary — the direct input to the income tax computation. It removes noise from social contribution deductions.

**Use `salaire_de_base` for multi-entity tests** where you also want `salaire_net` as output (since `salaire_net` is derived from `salaire_de_base` through social contribution formulas).

### Reference Value Computation

All reference values must be computed using the installed OpenFisca-France version (currently 175.0.18 on openfisca-core 44.2.2). Use the existing `_build_simulation()` helper or a temporary notebook to compute and pin values.

**⚠️ Reference values are NOT pulled from external publications.** They are pinned against the specific OpenFisca-France version installed in the project. The purpose is regression detection on version upgrades, not validation against government publications (which may use different rounding rules or parameter vintages).

### French Tax System Concepts for Test Design

**Quotient familial (family quotient):**
- Single person = 1 part
- Married couple = 2 parts
- +0.5 part per child for first two children
- +1 part per child from the third child
- Income is divided by number of parts, tax is computed on per-part income, then multiplied back
- Couples with children pay less tax than couples without children at the same total income

**Progressive tax brackets (barème 2024):**
The French income tax uses progressive marginal rates. Key thresholds change annually. With `salaire_imposable`:
- Low income (<~15k) → near zero tax (decote mechanism reduces very small tax amounts to zero)
- Mid income (30k-50k) → moderate tax (marginal rates ~11-30%)
- High income (75k+) → significant tax (marginal rate 30-41%)
- Very high income (100k+) → top bracket (41%+ marginal rate)

**Decote:** A reduction mechanism that eliminates or reduces very small tax amounts. Applies when raw computed tax is below a threshold (~1,929 EUR for singles in 2024). This makes the zero→positive tax transition non-linear.

### Adapter Fixture Configuration for Multi-Entity Tests

Story 9.5 needs an adapter configured with multiple output variables spanning different entities and periodicities:

```python
@pytest.fixture(scope="module")
def reference_adapter() -> OpenFiscaApiAdapter:
    """Adapter for reference test suite with multi-entity, mixed-periodicity output."""
    return OpenFiscaApiAdapter(
        country_package="openfisca_france",
        output_variables=(
            "salaire_net",                      # individu, MONTH → calculate_add
            "impot_revenu_restant_a_payer",     # foyer_fiscal, YEAR → calculate
            "revenu_disponible",                # menage, YEAR → calculate
        ),
    )
```

This overlaps with the existing `multi_entity_adapter` fixture but should be a separate fixture for test isolation (Story 9.5 tests should not depend on Story 9.2 fixture naming).

### 4-Entity PopulationData Construction for Family Scenarios

**Married couple (2 persons, 1 group per entity):**
```python
PopulationData(
    tables={
        "individu": pa.table({
            "salaire_imposable": pa.array([40000.0, 30000.0]),
            "famille_id": pa.array([0, 0]),
            "famille_role": pa.array(["parents", "parents"]),
            "foyer_fiscal_id": pa.array([0, 0]),
            "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
            "menage_id": pa.array([0, 0]),
            "menage_role": pa.array(["personne_de_reference", "conjoint"]),
        }),
    },
)
```

**Family with 1 child (3 persons, 1 group per entity):**
```python
PopulationData(
    tables={
        "individu": pa.table({
            "salaire_imposable": pa.array([40000.0, 30000.0, 0.0]),
            "age": pa.array([40, 38, 10]),  # age needed for child
            "famille_id": pa.array([0, 0, 0]),
            "famille_role": pa.array(["parents", "parents", "enfants"]),
            "foyer_fiscal_id": pa.array([0, 0, 0]),
            "foyer_fiscal_role": pa.array(["declarants", "declarants", "personnes_a_charge"]),
            "menage_id": pa.array([0, 0, 0]),
            "menage_role": pa.array(["personne_de_reference", "conjoint", "enfants"]),
        }),
    },
)
```

### Role Reference Table (from Story 9.4 Dev Notes)

| Entity | Role | Dict key (`plural or key`) | `role.max` |
|---|---|---|---|
| famille | Parent | `"parents"` | 2 |
| famille | Child | `"enfants"` | None |
| foyer_fiscal | Declarant | `"declarants"` | 2 |
| foyer_fiscal | Dependent | `"personnes_a_charge"` | None |
| menage | Ref person | `"personne_de_reference"` | 1 |
| menage | Spouse | `"conjoint"` | 1 |
| menage | Child | `"enfants"` | None |
| menage | Other | `"autres"` | None |

### Test Naming Convention

Follow the existing pattern in the file:
```python
@pytest.mark.integration
class TestAdapterReferenceSinglePerson:
    """Story 9.5: Single-person income tax reference cases via adapter.compute().

    Reference values computed against OpenFisca-France 175.0.18,
    openfisca-core 44.2.2, on 2026-03-01. Tolerance ±0.5 EUR.
    """

    ABSOLUTE_ERROR_MARGIN = 0.5
    REFERENCE_OPENFISCA_FRANCE_VERSION = "175.0.18"
    REFERENCE_DATE = "2026-03-01"

    def test_zero_income(self, reference_irpp_adapter: OpenFiscaApiAdapter) -> None:
        """Reference: zero income → zero tax."""
        ...
```

### What This Story Does NOT Cover

- **Modifying adapter code** — this is test-only
- **Adding new output variables** to the adapter
- **Testing non-French country packages** — France-specific only
- **Performance benchmarks** — covered by Story 8-2
- **Sub-yearly period support** — `compute()` takes `period: int` (year only)
- **Person-level broadcasting of group values** — out of epic 9 scope
- **Validation against government publications** — reference values are pinned against OpenFisca-France, not external sources

### Edge Cases to Handle

1. **Zero income → zero IRPP** — the simplest case, but validates the adapter handles it correctly (no division by zero, no negative tax for zero income)

2. **Very low income with decote** — French decote mechanism reduces small tax amounts to zero. The transition from 0 tax to positive tax is non-linear. Test at ~15k `salaire_imposable` where decote applies

3. **Child with age specification** — OpenFisca-France uses `age` (monthly variable) for child-related benefits. Must provide age on the person table. Use `"age": pa.array([...])` with monthly periodicity consideration (the adapter wraps with yearly period, OpenFisca handles the month internally for age)

4. **Children affecting tax computation** — In French tax, children add "demi-parts" to the quotient familial, but the benefit is capped (plafonnement du quotient familial). Very high incomes may see limited benefit from additional children

### Project Structure Notes

- Source layout: `src/reformlab/` is the installable package
- Tests mirror source: `tests/computation/` matches `src/reformlab/computation/`
- Each test subdirectory has `__init__.py` and `conftest.py`
- Class-based test grouping with AC references in docstrings
- Integration tests require `openfisca-france` optional dependency: `uv sync --extra openfisca`
- Run integration tests: `uv run pytest tests/computation/ -m integration`
- Run unit tests: `uv run pytest tests/computation/ -m "not integration"`
- Quality gates: `uv run ruff check src/ tests/` and `uv run mypy src/`

### References

- [Source: `_bmad-output/implementation-artifacts/spike-findings-8-1-openfisca-integration.md` — Follow-up #5: "Production integration test suite", line 108]
- [Source: `_bmad-output/planning-artifacts/epics.md` — Epic 9 acceptance criteria: "A reference test suite validates adapter output against known French tax-benefit values"]
- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 9.5 acceptance criteria, lines in Epic 9 section]
- [Source: `tests/computation/test_openfisca_integration.py` — `TestOpenFiscaFranceReferenceCases` class, lines 565-652; existing reference value pattern with ABSOLUTE_ERROR_MARGIN = 0.5]
- [Source: `tests/computation/test_openfisca_integration.py` — `_build_simulation()` helper, lines 88-118; `_build_entities_dict()` helper, lines 72-87]
- [Source: `tests/computation/test_openfisca_integration.py` — `TestFourEntityPopulationFormat` class, lines 1068-1295; 4-entity format integration tests from Story 9.4]
- [Source: `tests/computation/test_openfisca_integration.py` — Module-scoped fixtures `tbs()`, `adapter()`, `multi_entity_adapter()`, `periodicity_adapter()`]
- [Source: `src/reformlab/computation/openfisca_api_adapter.py` — `compute()` method pipeline: validate_period → TBS → validate_output → resolve_entities → resolve_periodicities → build_simulation → extract_results]
- [Source: `src/reformlab/computation/openfisca_api_adapter.py` — `_population_to_entity_dict()` with 4-entity mode, lines 499-900+]
- [Source: `_bmad-output/implementation-artifacts/9-4-define-population-data-4-entity-format.md` — Role reference table, OpenFisca-France role definitions, 4-entity format specification]
- [Source: `_bmad-output/implementation-artifacts/9-3-add-variable-periodicity-handling.md` — Periodicity dispatch table: month→calculate_add, year→calculate, eternity→calculate]
- [Source: `_bmad-output/implementation-artifacts/9-2-handle-multi-entity-output-arrays.md` — Multi-entity result extraction pattern, entity_tables dict structure]
- [Source: `_bmad-output/project-context.md` — Testing rules: "Class-based test grouping", "Direct assertions", "@pytest.mark.integration"]
- [Source: `.venv/lib/python3.13/site-packages/openfisca_france/parameters/impot_revenu/bareme_ir_depuis_1945/` — French income tax bracket parameters]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (via create-story workflow)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed — comprehensive developer guide created
- All 3 acceptance criteria from epics file expanded to 7 ACs covering: known-value validation, CI integration, regression detection, full-pipeline coverage, 4-entity cross-validation, multi-entity output validation, and backward compatibility
- Spike 8-1 findings fully integrated: follow-up #5 ("Production integration test suite") is the direct motivation
- Existing test infrastructure comprehensively mapped: 36+ integration tests across 11 test classes in test_openfisca_integration.py
- Critical distinction identified: existing `TestOpenFiscaFranceReferenceCases` uses `_build_simulation()` directly (validating OpenFisca-France itself), while Story 9.5 must use `adapter.compute()` (validating the full adapter pipeline)
- 4-entity PopulationData format documented for family scenarios with correct role assignments for children (enfants in famille, personnes_a_charge in foyer_fiscal, enfants in menage)
- French tax system concepts documented for test design: quotient familial, progressive brackets, decote mechanism, plafonnement
- Regression detection scaffolding designed: version pinning, reference date, structured assertion messages with expected/actual/tolerance/version
- Cross-validation strategy defined: 4-entity format vs legacy path for equivalent populations
- Edge cases documented: zero income, decote threshold, child age specification, quotient familial plafonnement

### File List

- `tests/computation/test_openfisca_integration.py` — modify (add `TestAdapterReferenceSinglePerson`, `TestAdapterReferenceFamilies`, `TestFourEntityCrossValidation`, `TestAdapterReferenceMultiEntity` test classes; add `reference_adapter` and `reference_irpp_adapter` module-scope fixtures)
