
# Story 13.3: Implement energy poverty aid template (new built-in)

Status: dev-complete

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a policy analyst,
I want a built-in energy poverty aid template that computes aid for households below a configurable income ceiling and above a configurable energy expenditure share threshold,
so that I can model the French _cheque energie_ and similar energy poverty aid policies in scenarios, portfolios, and multi-year projections.

## Acceptance Criteria

1. **AC1: EnergyPovertyAidParameters dataclass** — Given an `EnergyPovertyAidParameters` frozen dataclass subclassing `PolicyParameters`, when registered via the Story 13.1 custom template API (`register_policy_type("energy_poverty_aid")` + `register_custom_template()`), then `infer_policy_type()` resolves instances to `"energy_poverty_aid"`, and the class is usable in `BaselineScenario`, `ReformScenario`, `PolicyConfig`, and `PolicyPortfolio`.

2. **AC2: Aid computation** — Given a population table with `household_id` (int64), `income` (float64), and `energy_expenditure` (float64) columns, when `compute_energy_poverty_aid()` is called with `EnergyPovertyAidParameters`, then:
   - Households with `income < income_ceiling` AND `energy_expenditure / income >= energy_share_threshold` are eligible and receive aid. Households at exactly `income == income_ceiling` are ineligible (boundary: `income_ratio = 0`).
   - Aid amount per eligible household is computed as: `base_aid_amount * income_ratio * energy_burden_factor`, where:
     - `income_ratio = (income_ceiling - income) / income_ceiling` (linear scale, 1.0 at income=0, 0.0 at income=income_ceiling). Requires `income_ceiling > 0`.
     - `energy_burden_factor = min(energy_expenditure_share / energy_share_threshold, max_energy_factor)` (capped scaling based on energy burden severity).
   - Ineligible households receive 0 aid.
   - Edge cases: `income <= 0` → `income_ratio = 1.0`, energy share treated as exceeding threshold (eligible, max aid). `energy_expenditure <= 0` → `energy_share = 0.0 < threshold` (ineligible, takes precedence over income=0). Missing `energy_expenditure` column → treated as 0 for all households (no one eligible). Null values → filled with 0 via `pc.fill_null()`. Invalid parameters (`income_ceiling <= 0`, `energy_share_threshold <= 0`, `max_energy_factor <= 0`) → raise `TemplateError`.
   - The function returns an `EnergyPovertyAidResult` frozen dataclass containing `household_ids`, `aid_amount`, `is_eligible`, `energy_expenditure_share`, `income_decile`, `total_cost`, `eligible_count`, `year`, and `template_name`.
   - Income deciles (1-10) are assigned using the existing `assign_income_deciles()` utility.

3. **AC3: Year-indexed schedules** — Given `EnergyPovertyAidParameters` with an `income_ceiling_schedule` mapping years to income ceiling overrides, an `energy_share_schedule` mapping years to threshold overrides, and an `aid_schedule` mapping years to base_aid_amount overrides, when `compute_energy_poverty_aid()` is called for year `t`, then the computation uses `income_ceiling_schedule.get(t, income_ceiling)` as the ceiling, `energy_share_schedule.get(t, energy_share_threshold)` as the threshold, and `aid_schedule.get(t, base_aid_amount)` as the base aid for that year. Schedules override the default field values; when a year is absent from a schedule, the default field value applies.

4. **AC4: Decile aggregation** — Given an `EnergyPovertyAidResult`, when `aggregate_energy_poverty_aid_by_decile()` is called, then it returns an `EnergyPovertyAidDecileResults` frozen dataclass with per-decile `household_count`, `eligible_count`, `mean_aid`, and `total_aid` tuples (10 entries each, deciles 1-10).

5. **AC5: Batch and comparison** — Given multiple energy poverty aid scenarios (e.g., different ceiling/threshold/amount combinations), when `run_energy_poverty_aid_batch()` and `compare_energy_poverty_aid_decile_impacts()` are called, then:
   - Batch executes all scenarios on the same population and returns `dict[str, EnergyPovertyAidResult]`.
   - Comparison produces a `ComparisonResult` with per-scenario `EnergyPovertyAidDecileResults` and a wide-format `pa.Table`.

6. **AC6: Template YAML pack** — Given at least 2 YAML variant files in `src/reformlab/templates/packs/energy_poverty_aid/`, when loaded via `load_energy_poverty_aid_template()`, then each returns a `BaselineScenario` with `EnergyPovertyAidParameters` policy and `policy_type.value == "energy_poverty_aid"`. YAML round-trip (dump -> reload) preserves all field values.

7. **AC7: Portfolio composition** — Given an `EnergyPovertyAidParameters` policy in a `PolicyConfig`, when added to a `PolicyPortfolio` alongside a carbon tax template, then: (a) portfolio construction succeeds, (b) `validate_compatibility()` detects same-policy-type conflicts (two energy poverty aid policies) and overlapping-years conflicts (via `rate_schedule` keys), (c) `PortfolioComputationStep` passes aid parameters to the adapter via `asdict()`.

## Tasks / Subtasks

- [x] **Task 1: Define EnergyPovertyAidParameters and register** (AC: #1)
  - [x] 1.1 Create `src/reformlab/templates/energy_poverty_aid/__init__.py` with module docstring and exports
  - [x] 1.2 Create `src/reformlab/templates/energy_poverty_aid/compute.py` with `EnergyPovertyAidParameters` frozen dataclass:
    - Fields: `income_ceiling: float = 11000.0` (EUR, cheque energie default RFR/UC), `energy_share_threshold: float = 0.08` (8% TEE_3D threshold), `base_aid_amount: float = 150.0` (EUR, average cheque energie), `max_energy_factor: float = 2.0` (cap on energy burden multiplier), `income_ceiling_schedule: dict[int, float] = field(default_factory=dict)`, `energy_share_schedule: dict[int, float] = field(default_factory=dict)`, `aid_schedule: dict[int, float] = field(default_factory=dict)`
    - Inherits `rate_schedule`, `exemptions`, `thresholds`, `covered_categories` from `PolicyParameters`
    - `income_ceiling_schedule` maps year -> income_ceiling override
    - `energy_share_schedule` maps year -> energy_share_threshold override
    - `aid_schedule` maps year -> base_aid_amount override
    - Add `__post_init__` validation: raise `TemplateError` if `income_ceiling <= 0`, `energy_share_threshold <= 0`, or `max_energy_factor <= 0` (prevents division by zero in formulas)
  - [x] 1.3 Add auto-registration in module `__init__.py`: call `register_policy_type("energy_poverty_aid")` and `register_custom_template()` at import time, with idempotent guard (same pattern as vehicle_malus `__init__.py`)
  - [x] 1.4 Verify `infer_policy_type()` resolves `EnergyPovertyAidParameters` -> `"energy_poverty_aid"`

- [x] **Task 2: Implement compute_energy_poverty_aid()** (AC: #2, #3)
  - [x] 2.1 Implement `compute_energy_poverty_aid(population, policy, year, template_name) -> EnergyPovertyAidResult`
  - [x] 2.2 Define `EnergyPovertyAidResult` frozen dataclass with fields: `household_ids: pa.Array`, `aid_amount: pa.Array` (EUR), `is_eligible: pa.Array` (bool), `energy_expenditure_share: pa.Array` (float64), `income_decile: pa.Array`, `total_cost: float`, `eligible_count: int`, `year: int`, `template_name: str`
  - [x] 2.3 Implement year-indexed lookup: use `income_ceiling_schedule.get(year, policy.income_ceiling)` for ceiling, `energy_share_schedule.get(year, policy.energy_share_threshold)` for threshold, `aid_schedule.get(year, policy.base_aid_amount)` for base aid amount — schedules override defaults, absent years fall back to the default field value
  - [x] 2.4 Implement eligibility logic: `income < income_ceiling AND energy_expenditure_share >= energy_share_threshold` (strict less-than for income so boundary households with aid=0 are correctly marked ineligible)
  - [x] 2.5 Implement aid formula: `base_aid * income_ratio * energy_burden_factor` where `income_ratio = (ceiling - income) / ceiling` and `energy_burden_factor = min(energy_share / threshold, max_energy_factor)`
  - [x] 2.6 Handle edge cases: income <= 0 (treat income_ratio=1.0, energy_share as exceeding threshold), energy_expenditure <= 0 (share=0, not eligible), missing `energy_expenditure` column (treat as 0 expenditure, no one eligible)
  - [x] 2.7 Use `assign_income_deciles()` from `reformlab.templates.carbon_tax.compute` for decile assignment

- [x] **Task 3: Implement decile aggregation** (AC: #4)
  - [x] 3.1 Implement `aggregate_energy_poverty_aid_by_decile(result) -> EnergyPovertyAidDecileResults`
  - [x] 3.2 Define `EnergyPovertyAidDecileResults` frozen dataclass with `decile`, `household_count`, `eligible_count`, `mean_aid`, `total_aid` tuple fields
  - [x] 3.3 Follow the exact pattern from `vehicle_malus/compute.py:aggregate_vehicle_malus_by_decile()` — iterate deciles 1-10, compute count, mean, and total per group

- [x] **Task 4: Implement batch and comparison** (AC: #5)
  - [x] 4.1 Create `src/reformlab/templates/energy_poverty_aid/compare.py`
  - [x] 4.2 Implement `run_energy_poverty_aid_batch(population, scenarios, year) -> dict[str, EnergyPovertyAidResult]` — follow `vehicle_malus/compare.py:run_vehicle_malus_batch()` pattern, validate `isinstance(scenario.policy, EnergyPovertyAidParameters)`
  - [x] 4.3 Implement `compare_energy_poverty_aid_decile_impacts(results) -> ComparisonResult` — follow vehicle malus comparison pattern with wide-format table
  - [x] 4.4 Implement `energy_poverty_aid_decile_results_to_table(decile_results) -> pa.Table` conversion utility
  - [x] 4.5 Define `ComparisonResult` frozen dataclass (own per module, not shared)

- [x] **Task 5: Create YAML template pack** (AC: #6)
  - [x] 5.1 Create directory `src/reformlab/templates/packs/energy_poverty_aid/`
  - [x] 5.2 Create `energy-poverty-cheque-energie.yaml` — French cheque energie simplified: income ceiling 11,000 EUR, 8% energy share threshold, 150 EUR base aid, 11-year schedule 2026-2036 with stable ceiling and increasing aid
  - [x] 5.3 Create `energy-poverty-generous.yaml` — Higher-aid variant: income ceiling 15,000 EUR, 10% threshold, 300 EUR base aid, 11-year schedule with increasing ceiling and aid for comparison. Named "generous" because the higher ceiling (+36% more households eligible) and doubled base aid (300 vs 150 EUR) make the overall program substantially more generous despite the stricter energy share threshold.
  - [x] 5.4 Add `README.md` to pack directory documenting variants
  - [x] 5.5 Add `list_energy_poverty_aid_templates()`, `load_energy_poverty_aid_template()`, `get_energy_poverty_aid_pack_dir()` to `packs/__init__.py` — follow exact pattern of vehicle_malus pack but use custom type registration for policy_type validation
  - [x] 5.6 Export new pack functions from `src/reformlab/templates/packs/__init__.py` and add to `__all__`

- [x] **Task 6: Export from templates package** (AC: #1, #5)
  - [x] 6.1 Export `EnergyPovertyAidParameters`, `EnergyPovertyAidResult`, `EnergyPovertyAidDecileResults`, `ComparisonResult`, computation functions, and pack utilities from `src/reformlab/templates/energy_poverty_aid/__init__.py`
  - [x] 6.2 Ensure `energy_poverty_aid` module is importable via `from reformlab.templates.energy_poverty_aid import ...`
  - [x] 6.3 Add pack loading functions to `src/reformlab/templates/__init__.py` exports and `__all__`

- [x] **Task 7: Write comprehensive tests** (AC: #1-#7)
  - [x] 7.1 Create `tests/templates/energy_poverty_aid/__init__.py`
  - [x] 7.2 Create `tests/templates/energy_poverty_aid/conftest.py` with fixtures: `sample_population` (10 households with varying income and energy expenditure), `small_population` (3 households for hand-computed golden values), parameter fixtures (cheque-energie-style, generous)
  - [x] 7.3 Create `tests/templates/energy_poverty_aid/test_compute.py` with test classes:
    - `TestEnergyPovertyAidParameters`: frozen, inherits PolicyParameters, custom fields accessible, default values
    - `TestComputeEnergyPovertyAid`: basic computation with golden values, eligibility (income AND energy share conditions), ineligible households get 0, missing energy_expenditure column, zero income edge case, zero energy expenditure, year-indexed ceiling schedule, year-indexed threshold schedule, year-indexed aid schedule, total cost correctness, income decile assignment, eligible_count correctness
    - `TestEnergyPovertyAidResult`: frozen, fields present
    - `TestAggregateEnergyPovertyAidByDecile`: count/mean/total per decile, eligible_count per decile, empty decile handling
  - [x] 7.4 Create `tests/templates/energy_poverty_aid/test_compare.py` with test classes:
    - `TestRunEnergyPovertyAidBatch`: single scenario, multiple scenarios, wrong policy type raises
    - `TestCompareEnergyPovertyAidDecileImpacts`: comparison result structure, wide-format table columns
  - [x] 7.5 Create `tests/templates/energy_poverty_aid/test_pack.py` with tests:
    - `TestEnergyPovertyAidPack`: list templates, load template, YAML round-trip, load nonexistent raises
  - [x] 7.6 Add portfolio integration test: energy poverty aid + carbon tax in portfolio, validate_compatibility detects overlapping years
  - [x] 7.7 Run `uv run ruff check src/ tests/` and `uv run mypy src/`
  - [x] 7.8 Run `uv run pytest tests/ -x` to verify no regressions

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**Frozen dataclasses are NON-NEGOTIABLE:**
```python
from __future__ import annotations
from dataclasses import dataclass, field
from reformlab.templates.schema import PolicyParameters

@dataclass(frozen=True)
class EnergyPovertyAidParameters(PolicyParameters):
    """Energy poverty aid for low-income, energy-burdened households.

    Models the French cheque energie and similar income-conditioned
    energy poverty aid policies.
    """
    income_ceiling: float = 11000.0        # EUR RFR/UC (cheque energie default)
    energy_share_threshold: float = 0.08   # 8% of income (TEE_3D)
    base_aid_amount: float = 150.0         # EUR (average cheque energie)
    max_energy_factor: float = 2.0         # Cap on energy burden multiplier
    income_ceiling_schedule: dict[int, float] = field(default_factory=dict)
    energy_share_schedule: dict[int, float] = field(default_factory=dict)
    aid_schedule: dict[int, float] = field(default_factory=dict)
```

**`from __future__ import annotations`** on every file. Use `if TYPE_CHECKING:` guards for type-only imports. [Source: docs/project-context.md#Python Language Rules]

**PyArrow is the canonical data type** — all computation uses `pa.Table`, `pa.Array`, `pc.compute` operations. No pandas in core logic. [Source: docs/project-context.md#Critical Don't-Miss Rules]

**Subsystem-specific exceptions** — Use `TemplateError` from `reformlab.templates.exceptions` for registration errors. Never raise bare `Exception` or `ValueError` for domain errors. [Source: docs/project-context.md#Python Language Rules]

**Logging** — use `logging.getLogger(__name__)` with structured key=value format. [Source: docs/project-context.md#Code Quality & Style Rules]

### Existing Code Patterns to Follow

**Vehicle malus as primary reference model.** The energy poverty aid template is structurally similar to the vehicle malus template — both are custom types registered at import time, following the exact same module layout. Key differences:
- Vehicle malus computes a penalty (household pays); energy poverty aid computes a transfer (household receives).
- Vehicle malus uses a single metric (emissions); energy poverty aid uses two conditions (income AND energy share).
- Energy poverty aid includes eligibility tracking (`is_eligible`, `eligible_count`) similar to the subsidy template pattern.

**Subsidy template as secondary reference** — the subsidy module (`src/reformlab/templates/subsidy/compute.py`) demonstrates the eligibility pattern (income cap + category check). Energy poverty aid follows a similar dual-condition eligibility model but with continuous rather than binary amounts.

**Compute module pattern** — Follow `src/reformlab/templates/vehicle_malus/compute.py`:
1. Define Parameters frozen dataclass extending `PolicyParameters`
2. Define Result frozen dataclass with `pa.Array` per-household fields + scalar aggregates
3. Define DecileResults frozen dataclass with `tuple[int, ...]` / `tuple[float, ...]` per-decile fields
4. Main `compute_*()` function takes `(population: pa.Table, policy, year, template_name)` -> Result
5. `aggregate_*_by_decile(result)` -> DecileResults
6. Use `assign_income_deciles()` from `reformlab.templates.carbon_tax.compute` for decile assignment
7. Use `_sum_array()` helper for safe PyArrow array summation

**Compare module pattern** — Follow `src/reformlab/templates/vehicle_malus/compare.py`:
1. `run_*_batch(population, scenarios, year)` — validates policy type, runs each scenario, detects duplicate names
2. `compare_*_decile_impacts(results)` — aggregates by decile, builds wide-format `pa.Table`
3. `*_decile_results_to_table(decile_results)` — conversion utility
4. Own `ComparisonResult` frozen dataclass per module (not shared)

**Pack loader pattern** — Follow `src/reformlab/templates/packs/__init__.py`:
1. `list_energy_poverty_aid_templates()` — glob `*.yaml` in pack dir
2. `load_energy_poverty_aid_template(variant_name)` — import module for registration, load + type-check `BaselineScenario`
3. `get_energy_poverty_aid_pack_dir()` -> `Path`

**IMPORTANT: Custom type registration at module import time.** Since energy poverty aid is a custom policy type (not a built-in `PolicyType` enum member), the `energy_poverty_aid/__init__.py` must register the type when imported. This means:
- `register_policy_type("energy_poverty_aid")` runs at module level with idempotent guard
- `register_custom_template(_type, EnergyPovertyAidParameters)` runs at module level
- The `packs/__init__.py` loader must `import reformlab.templates.energy_poverty_aid` before attempting to load YAML files (to ensure registration happens)
- Follow the exact idempotent registration pattern from `src/reformlab/templates/vehicle_malus/__init__.py` (lines 36-45)

### Energy Poverty Aid Policy Context (French _Cheque Energie_)

The French cheque energie is an annual energy voucher for low-income households:

- **Eligibility criterion:** RFR/UC (revenu fiscal de reference per unite de consommation) <= 11,000 EUR
- **Energy poverty threshold (TEE_3D):** Households spending >= 8% of disposable income on energy AND in bottom 3 income deciles (ONPE definition)
- **Aid amounts:** 48-277 EUR depending on income bracket and household size (4 income brackets x 3 household size categories = 12-cell matrix)
- **Average cheque:** approximately 150 EUR
- **Income brackets for cheque energie:** <5,600 / 5,600-6,700 / 6,700-7,700 / 7,700-11,000 EUR RFR/UC
- **Scale of problem:** 3.1 million households (10.1% of French households) in energy poverty (2023 data)

**Simplified model for this template:** Instead of the exact 12-cell bracket matrix (income x household size), the template uses a continuous linear model:
- **Eligibility:** `income < income_ceiling AND energy_expenditure / income >= energy_share_threshold`
- **Aid formula:** `base_aid_amount * income_ratio * energy_burden_factor`
  - `income_ratio = (income_ceiling - income) / income_ceiling` — linearly decreasing with income (poorest get most)
  - `energy_burden_factor = min(energy_expenditure_share / energy_share_threshold, max_energy_factor)` — scaled by severity, capped

This is a deliberate simplification appropriate for microsimulation because:
- Population-level distributional analysis doesn't require bracket-level precision
- The linear model is composable in portfolios and transparent in manifests
- Household size is not included as a parameter (simplified to income-based only)
- A future Story 13.4 notebook demo can show how to author a custom template with exact bracket logic if needed

### Source File Touchpoints

| File | Change Type | Purpose |
|------|-------------|---------|
| `src/reformlab/templates/energy_poverty_aid/__init__.py` | **CREATE** | Module exports + type registration |
| `src/reformlab/templates/energy_poverty_aid/compute.py` | **CREATE** | EnergyPovertyAidParameters, EnergyPovertyAidResult, EnergyPovertyAidDecileResults, compute_energy_poverty_aid(), aggregate_energy_poverty_aid_by_decile() |
| `src/reformlab/templates/energy_poverty_aid/compare.py` | **CREATE** | ComparisonResult, run_energy_poverty_aid_batch(), compare_energy_poverty_aid_decile_impacts(), energy_poverty_aid_decile_results_to_table() |
| `src/reformlab/templates/packs/energy_poverty_aid/energy-poverty-cheque-energie.yaml` | **CREATE** | French cheque-energie-style template variant |
| `src/reformlab/templates/packs/energy_poverty_aid/energy-poverty-generous.yaml` | **CREATE** | Generous aid variant for comparison |
| `src/reformlab/templates/packs/energy_poverty_aid/README.md` | **CREATE** | Pack documentation |
| `src/reformlab/templates/packs/__init__.py` | **MODIFY** | Add list/load/get functions for energy_poverty_aid pack |
| `src/reformlab/templates/__init__.py` | **MODIFY** | Export energy_poverty_aid pack utilities |
| `tests/templates/energy_poverty_aid/__init__.py` | **CREATE** | Test package |
| `tests/templates/energy_poverty_aid/conftest.py` | **CREATE** | Population and parameter fixtures |
| `tests/templates/energy_poverty_aid/test_compute.py` | **CREATE** | Compute unit tests |
| `tests/templates/energy_poverty_aid/test_compare.py` | **CREATE** | Batch and comparison tests |
| `tests/templates/energy_poverty_aid/test_pack.py` | **CREATE** | Pack loading, YAML round-trip, and portfolio integration tests |

### Project Structure Notes

- New module at `src/reformlab/templates/energy_poverty_aid/` — follows the existing pattern of one subdirectory per policy type under `templates/`
- New pack directory at `src/reformlab/templates/packs/energy_poverty_aid/` — follows the existing pattern of one subdirectory per policy type under `packs/`
- Tests mirror at `tests/templates/energy_poverty_aid/` — follows the existing pattern
- **No new dependencies required** — uses existing pyarrow, dataclasses, yaml
- **No modifications to orchestrator, adapter, or schema core** — energy poverty aid flows through the custom template registration API from Story 13.1
- **Alignment with vehicle_malus (Story 13.2):** Identical module structure, identical registration pattern, identical pack loader pattern. Only computation logic and YAML parameter names differ.

### Key Design Decisions

**1. Continuous linear model (NOT stepped bracket matrix):**
The French cheque energie uses a 12-cell matrix (4 income brackets x 3 household size categories). This template uses a continuous linear model (`base_aid * income_ratio * energy_burden_factor`) which is appropriate for microsimulation because:
- Population-level distributional analysis is the goal, not individual-level precision
- The linear model is composable in portfolios and transparent in manifests
- Household size dimension is omitted for simplification (can be added via custom template in Story 13.4)

**2. Dual-condition eligibility:**
Unlike vehicle malus (single metric threshold), energy poverty aid requires TWO conditions: income below ceiling (strict `<`) AND energy burden at or above threshold. Both must be met. This reflects the actual policy design of the cheque energie and the ONPE TEE_3D indicator.

**3. Year-indexed triple schedules:**
Energy poverty aid needs THREE year-indexed overrides: income ceiling, energy share threshold, and base aid amount. This is more schedules than vehicle malus (2) but follows the exact same `.get(year, default)` pattern. When a year is absent from a schedule, the default field value applies.

**4. Energy burden as both gate and multiplier:**
The `energy_share_threshold` serves dual purpose:
- **Eligibility gate:** households must be at or above the threshold to qualify
- **Aid scaling reference:** the `energy_burden_factor = min(share / threshold, max_energy_factor)` scales aid by how severe the energy burden is beyond the threshold

**5. Registration at import time:**
Same pattern as vehicle_malus. The energy poverty aid type is registered when the module is first imported. Idempotent guards prevent errors on re-import.

**6. Population data requirements:**
The compute function requires a new column `energy_expenditure` (float64, annual energy spending in EUR) which is not used by other templates. Missing column is handled gracefully: treated as 0 expenditure, so no households are eligible (consistent with vehicle_malus missing-column pattern).

### Cross-Story Dependencies

- **Depends on:** Story 13.1 (custom template authoring API — dev-complete)
- **Depends on:** Story 13.2 (vehicle malus template — dev-complete; provides the registration pattern to follow)
- **Blocks:** Story 13.4 (validate custom templates in portfolios + notebook demo)
- **Independent of:** No parallel dependencies; can be implemented in any order relative to Story 13.2

### Out of Scope Guardrails

- **Do NOT** implement the exact French 12-cell bracket matrix with income x household size. Use the simplified linear model.
- **Do NOT** implement household size (UC) calculations. The simplified model uses income directly.
- **Do NOT** modify the `ComputationAdapter` protocol or orchestrator core. Energy poverty aid flows through existing infrastructure.
- **Do NOT** modify `PolicyType` enum — energy poverty aid is registered as a `CustomPolicyType` via the Story 13.1 API.
- **Do NOT** modify the JSON Schema files — custom types bypass JSON Schema validation by design (Story 13.1 decision).
- **Do NOT** build a notebook demo — that is Story 13.4's scope.
- **Do NOT** implement MaPrimeRenov' (energy renovation aid). That would be a separate template if needed.

### Testing Standards

- **Mirror source structure:** Tests in `tests/templates/energy_poverty_aid/`
- **Class-based grouping:** `TestEnergyPovertyAidParameters`, `TestComputeEnergyPovertyAid`, `TestAggregateEnergyPovertyAidByDecile`, etc.
- **Fixtures in conftest:** Population tables built inline with PyArrow, parameter fixtures for different scenarios
- **Direct assertions:** Plain `assert`, `pytest.raises(TemplateError, match=...)` for errors
- **No MockAdapter needed:** Energy poverty aid compute/compare tests work directly on population tables — no adapter involved
- **Coverage target:** >90% for all new code
- **Golden value tests:** At least one test with hand-computed expected values. Example:
  - Household: income=5000, energy_expenditure=600, ceiling=11000, threshold=0.08, base_aid=150, max_factor=2.0
  - energy_share = 600/5000 = 0.12 >= 0.08 -> eligible
  - income_ratio = (11000-5000)/11000 = 0.5455
  - energy_factor = min(0.12/0.08, 2.0) = min(1.5, 2.0) = 1.5
  - aid = 150 * 0.5455 * 1.5 = 122.73 EUR

### Edge Case Handling

**Precedence rule:** Energy expenditure conditions are evaluated first. If `energy_expenditure <= 0`, the household is ineligible regardless of income.

| Scenario | Expected Behavior |
|----------|-------------------|
| `income_ceiling <= 0` | Raise `TemplateError` in `__post_init__` (invalid parameter) |
| `energy_share_threshold <= 0` | Raise `TemplateError` in `__post_init__` (invalid parameter) |
| `max_energy_factor <= 0` | Raise `TemplateError` in `__post_init__` (invalid parameter) |
| `income = 0` | `income_ratio = 1.0`, `energy_share` treated as exceeding threshold -> eligible, max aid |
| `income < 0` | Treat same as income=0 (defensive) |
| `energy_expenditure = 0` | `energy_share = 0.0 < threshold` -> not eligible (takes precedence over income=0) |
| `energy_expenditure` column missing | Treat as 0 for all households -> no one eligible |
| `income >= income_ceiling` | Not eligible (strict `<` comparison for income) |
| `energy_share < threshold` | Not eligible regardless of income |
| `energy_share >= max_energy_factor * threshold` | `energy_burden_factor` capped at `max_energy_factor` |
| `income = income_ceiling` | Not eligible (`income < income_ceiling` is false, `income_ratio` would be 0) |
| Null values in income/energy_expenditure | Fill nulls with 0 via `pc.fill_null()` |

### References

- [Source: `src/reformlab/templates/vehicle_malus/compute.py` — Primary reference for compute module pattern]
- [Source: `src/reformlab/templates/vehicle_malus/compare.py` — Primary reference for compare module pattern]
- [Source: `src/reformlab/templates/vehicle_malus/__init__.py` — Import-time registration pattern (idempotent guard)]
- [Source: `src/reformlab/templates/subsidy/compute.py` — Eligibility pattern reference (income cap + category check)]
- [Source: `src/reformlab/templates/feebate/compute.py` — Feebate compute pattern, FeebateResult structure]
- [Source: `src/reformlab/templates/packs/__init__.py` — Pack loader pattern (list/load/get)]
- [Source: `src/reformlab/templates/packs/vehicle_malus/vehicle-malus-french-2026.yaml` — YAML template structure reference]
- [Source: `src/reformlab/templates/schema.py` — PolicyParameters base class, register_policy_type(), register_custom_template(), CustomPolicyType]
- [Source: `src/reformlab/templates/carbon_tax/compute.py:assign_income_deciles()` — Shared decile utility]
- [Source: `docs/project-context.md` — Frozen dataclasses, PyArrow-first, exception hierarchy, coding standards]
- [Source: `docs/epics.md#Story 13.3` — Acceptance criteria from backlog]
- [Source: `_bmad-output/implementation-artifacts/13-1-define-custom-template-authoring-api-and-registration.md` — Predecessor story with registration API details]
- [Source: `_bmad-output/implementation-artifacts/13-2-implement-vehicle-malus-template.md` — Sibling story, identical module structure]
- [Source: French cheque energie — https://www.service-public.gouv.fr/particuliers/vosdroits/F33667]
- [Source: ONPE TEE_3D indicator — https://onpe.org/tableaux-de-bord-2025]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

### Implementation Plan

Followed vehicle_malus (Story 13.2) module structure exactly: compute.py (parameters + result types + computation + decile aggregation), compare.py (batch + comparison), __init__.py (registration + exports). All edge cases from story spec implemented and tested.

### Completion Notes List

- Ultimate context engine analysis completed — comprehensive developer guide created
- Vehicle malus template (Story 13.2) identified as primary reference model (identical module structure)
- Subsidy template identified as secondary reference (eligibility-based aid pattern)
- French cheque energie policy researched: RFR/UC <= 11,000 EUR, 4 income brackets, 48-277 EUR aid
- ONPE TEE_3D indicator researched: 8% energy expenditure share threshold for bottom 3 deciles
- Design decision: continuous linear model (NOT stepped 12-cell bracket matrix) for microsimulation appropriateness
- Design decision: dual-condition eligibility (income ceiling AND energy share threshold)
- Design decision: triple year-indexed schedules (ceiling + threshold + aid amount) for policy parameter evolution
- Design decision: energy burden as both eligibility gate and aid multiplier via energy_burden_factor
- Design decision: import-time registration (energy poverty aid is a "built-in custom" shipped type)
- 7 tasks with detailed subtasks covering: parameters, compute, decile aggregation, batch/compare, YAML pack, exports, tests
- 13 source files to create/modify identified
- Cross-story dependencies mapped: 13.1 (done) -> 13.2 (done) -> 13.3 (this) -> 13.4
- Golden value test example computed by hand: income=5000, energy_exp=600 -> aid=122.73 EUR
- Edge case handling documented for 8 scenarios
- All 7 tasks implemented and tested (48 new tests, all passing)
- Full regression suite: 2224 passed, 0 failed
- ruff check: All checks passed
- mypy strict: Success, no issues found in 3 source files
- Implementation date: 2026-03-06

### File List

- `src/reformlab/templates/energy_poverty_aid/__init__.py` — CREATE: Module exports + type registration
- `src/reformlab/templates/energy_poverty_aid/compute.py` — CREATE: Parameters, result types, computation logic
- `src/reformlab/templates/energy_poverty_aid/compare.py` — CREATE: Batch execution and comparison utilities
- `src/reformlab/templates/packs/energy_poverty_aid/energy-poverty-cheque-energie.yaml` — CREATE: French cheque energie variant
- `src/reformlab/templates/packs/energy_poverty_aid/energy-poverty-generous.yaml` — CREATE: Generous aid variant
- `src/reformlab/templates/packs/energy_poverty_aid/README.md` — CREATE: Pack documentation
- `src/reformlab/templates/packs/__init__.py` — MODIFY: Add energy_poverty_aid pack functions
- `src/reformlab/templates/__init__.py` — MODIFY: Export energy_poverty_aid pack utilities
- `tests/templates/energy_poverty_aid/__init__.py` — CREATE: Test package
- `tests/templates/energy_poverty_aid/conftest.py` — CREATE: Test fixtures
- `tests/templates/energy_poverty_aid/test_compute.py` — CREATE: Computation tests
- `tests/templates/energy_poverty_aid/test_compare.py` — CREATE: Batch/comparison tests
- `tests/templates/energy_poverty_aid/test_pack.py` — CREATE: Pack loading + portfolio integration tests

## Senior Developer Review (AI)

### Review: 2026-03-06
- **Reviewer:** AI Code Review Synthesis
- **Evidence Score:** 11.2 -> REJECT (pre-fix), all actionable issues fixed
- **Issues Found:** 8 verified across 2 reviewers
- **Issues Fixed:** 6
- **Action Items Created:** 2

#### Review Follow-ups (AI)
- [ ] [AI-Review] MEDIUM: AC7(c) missing execution-path test proving adapter receives full `asdict()` payload from PortfolioComputationStep (tests/templates/energy_poverty_aid/test_pack.py)
- [ ] [AI-Review] LOW: Comparison table column slug collisions possible across scenario names with similar names (src/reformlab/templates/energy_poverty_aid/compare.py:114)
