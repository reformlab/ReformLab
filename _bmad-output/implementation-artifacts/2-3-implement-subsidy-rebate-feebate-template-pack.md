# Story 2.3: Implement Subsidy/Rebate/Feebate Template Pack

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **policy analyst**,
I want **ready-to-use subsidy, rebate, and feebate template packs**,
so that **I can immediately run environmental policy comparisons covering incentive-based instruments without writing code, comparing targeted subsidies, income-conditioned rebates, and feebates with explicit pivot-based fee/rebate effects**.

## Acceptance Criteria

Scope note: BKL-203 baseline is template packs + execution utilities needed for per-household computation and per-decile comparison. Exactly one shipped template per policy type is required for this story. Registry persistence, orchestrator wiring, and rich report export are out of scope.

1. **AC-1: Template pack provides subsidy, rebate, and feebate templates**
   - Given the shipped template packs, when listed, then at least 3 templates are available: one subsidy, one rebate, one feebate.
   - Templates are named descriptively and consistently (e.g., `subsidy-energy-retrofit`, `rebate-progressive-income`, `feebate-vehicle-emissions`).
   - All templates pass `load_scenario_template()` validation and have year schedules of at least 10 years.

2. **AC-2: Subsidy computation per household**
   - Given a subsidy template, when executed with a population, then output includes `subsidy_amount` and `is_eligible` for every household.
   - Eligibility applies the template's `income_caps[year]` and `eligible_categories`; ineligible households receive `subsidy_amount = 0.0`.
   - `total_cost` equals the sum of per-household `subsidy_amount` values for the run year.

3. **AC-3: Rebate computation with income conditioning**
   - Given a rebate template with income-conditioned parameters, when executed, then rebate amounts vary by income group.
   - Supported modes are `lump_sum` and `progressive_dividend` using template-defined `rebate_type` and `income_weights`.
   - `lump_sum` distributes equally; `progressive_dividend` uses decile weights and produces higher amounts for higher-weight deciles.

4. **AC-4: Feebate computation with pivot point**
   - Given a feebate template, when applied to a population, then households above the pivot threshold pay fees and households below receive rebates.
   - For each household, output includes `fee_amount`, `rebate_amount`, and `net_impact = rebate_amount - fee_amount`.
   - Run-level `net_fiscal_balance` is reported as `total_fees - total_rebates` (no automatic rate tuning in this story).

5. **AC-5: Per-decile comparison output**
   - Given two or more templates from the pack, when run in batch, then output includes per-decile metrics for each scenario.
   - Output includes per-decile household counts and mean net impact for each scenario, plus policy-specific mean components (e.g., subsidy, rebate, fee).
   - Output is available programmatically as typed Python structures (`*Result`, `DecileResults`) and a `pa.Table` comparison view.

6. **AC-6: Template pack is documented and discoverable**
   - Template pack files are shipped in `src/reformlab/templates/packs/subsidy/`, `packs/rebate/`, `packs/feebate/`.
   - Each pack includes a README.md describing templates, assumptions, and parameter meanings.
   - API provides `list_subsidy_templates()`, `list_rebate_templates()`, `list_feebate_templates()` and corresponding load functions.

## Tasks / Subtasks

- [ ] Task 0: Confirm schema and loader compatibility for subsidy/rebate/feebate (AC: #1, #2, #3, #4)
  - [ ] 0.1 Review existing `SubsidyParameters`, `RebateParameters`, `FeebateParameters` in `src/reformlab/templates/schema.py`
  - [ ] 0.2 Verify required fields are used as currently defined (no schema expansion in BKL-203): subsidy `eligible_categories` + `income_caps`; rebate `rebate_type` + `income_weights`; feebate `pivot_point` + `fee_rate` + `rebate_rate`
  - [ ] 0.3 Update loader parsing in `_parse_parameters()` only if compatibility fixes are required for existing fields
  - [ ] 0.4 Add/extend schema validation tests for valid and invalid values of the existing fields

- [ ] Task 1: Create subsidy computation module (AC: #2, #5)
  - [ ] 1.1 Create `src/reformlab/templates/subsidy/__init__.py`
  - [ ] 1.2 Create `src/reformlab/templates/subsidy/compute.py` with:
    - `SubsidyResult` dataclass (household_ids, subsidy_amount, is_eligible, income_decile, total_cost, year, template_name)
    - `compute_subsidy_eligibility(population, parameters)` → eligibility mask
    - `compute_subsidy_amount(population, parameters, eligibility_mask)` → per-household amounts
    - `compute_subsidy(population, parameters, year, template_name)` → `SubsidyResult`
  - [ ] 1.3 Implement income cap filtering (household income <= cap for run year)
  - [ ] 1.4 Implement category eligibility (household has eligible characteristic)
  - [ ] 1.5 Create `aggregate_subsidy_by_decile(result)` → `DecileResults`

- [ ] Task 2: Create rebate computation module (AC: #3, #5)
  - [ ] 2.1 Create `src/reformlab/templates/rebate/__init__.py`
  - [ ] 2.2 Create `src/reformlab/templates/rebate/compute.py` with:
    - `RebateResult` dataclass (household_ids, rebate_amount, income_decile, total_distributed, year, template_name)
    - `compute_rebate(population, parameters, rebate_pool, year, template_name)` → `RebateResult`
  - [ ] 2.3 Implement lump_sum rebate: `rebate_pool / num_households`
  - [ ] 2.4 Implement progressive_dividend rebate using income_weights (reuse pattern from carbon_tax)
  - [ ] 2.5 Create `aggregate_rebate_by_decile(result)` → `DecileResults`

- [ ] Task 3: Create feebate computation module (AC: #4, #5)
  - [ ] 3.1 Create `src/reformlab/templates/feebate/__init__.py`
  - [ ] 3.2 Create `src/reformlab/templates/feebate/compute.py` with:
    - `FeebateResult` dataclass (household_ids, fee_amount, rebate_amount, net_impact, metric_value, income_decile, total_fees, total_rebates, net_fiscal_balance, year, template_name)
    - `compute_feebate(population, parameters, metric_column, year, template_name)` → `FeebateResult`
  - [ ] 3.3 Implement pivot logic: if metric > pivot_point → fee; if metric < pivot_point → rebate
  - [ ] 3.4 Implement fee/rebate calculation: `(metric_value - pivot_point) * fee_rate` or `(pivot_point - metric_value) * rebate_rate`
  - [ ] 3.5 Create `aggregate_feebate_by_decile(result)` → `DecileResults`

- [ ] Task 4: Create template YAML files (AC: #1, #6)
  - [ ] 4.1 Create `src/reformlab/templates/packs/subsidy/` directory
  - [ ] 4.2 Create `subsidy-energy-retrofit.yaml` (home energy efficiency subsidy)
  - [ ] 4.3 Create `src/reformlab/templates/packs/rebate/` directory
  - [ ] 4.4 Create `rebate-progressive-income.yaml` (progressive dividend rebate)
  - [ ] 4.5 Create `src/reformlab/templates/packs/feebate/` directory
  - [ ] 4.6 Create `feebate-vehicle-emissions.yaml` (vehicle emissions pivot)
  - [ ] 4.7 Create README.md for each pack documenting templates and assumptions

- [ ] Task 5: Implement template pack loader and comparison utilities (AC: #5, #6)
  - [ ] 5.1 Add `list_subsidy_templates()`, `load_subsidy_template(name)` to `packs/__init__.py`
  - [ ] 5.2 Add `list_rebate_templates()`, `load_rebate_template(name)` to `packs/__init__.py`
  - [ ] 5.3 Add `list_feebate_templates()`, `load_feebate_template(name)` to `packs/__init__.py`
  - [ ] 5.4 Create comparison utilities in each module's `compare.py`:
    - `subsidy/compare.py` with `run_subsidy_batch()`, `compare_subsidy_decile_impacts()`
    - `rebate/compare.py` with `run_rebate_batch()`, `compare_rebate_decile_impacts()`
    - `feebate/compare.py` with `run_feebate_batch()`, `compare_feebate_decile_impacts()`
  - [ ] 5.5 Export public API from `reformlab.templates` module

- [ ] Task 6: Write focused tests (AC: all)
  - [ ] 6.1 Unit tests for subsidy eligibility and computation
  - [ ] 6.2 Unit tests for rebate computation (lump_sum and progressive)
  - [ ] 6.3 Unit tests for feebate pivot logic and fee/rebate calculation
  - [ ] 6.4 Integration tests for template loading and pack discovery
  - [ ] 6.5 Integration tests for batch comparison across policy types
  - [ ] 6.6 Golden-file tests for expected per-household and per-decile outputs

## Dev Notes

### Architecture Patterns to Follow

**From architecture.md:**
- Templates are Python code in template modules, not YAML formula strings (formulas are not compiled)
- Scenario Template Layer sits above Data Layer and below Dynamic Orchestrator
- Environmental policy templates encode business logic as reusable scenario artifacts
- Year-indexed policy schedules for at least 10 years (FR12)
- Subsystem: `templates/` for environmental policy templates

**From PRD:**
- FR7: Analyst can load prebuilt environmental policy templates (carbon tax, subsidy, rebate, feebate)
- FR10: Analyst can run multiple scenarios in one batch for comparison
- FR11: Analyst can compose tax-benefit baseline outputs with environmental template logic in one workflow
- NFR4: YAML configuration loading and validation completes in under 1 second
- NFR5: Analytical operations execute in under 5 seconds for 100k households

### Existing Code Patterns to Follow

**CRITICAL: Follow the carbon tax implementation pattern exactly.**

From Story 2.2 (`src/reformlab/templates/carbon_tax/`):
- `compute.py` contains computation functions and result dataclasses
- `compare.py` contains batch execution and comparison utilities
- `CarbonTaxResult` and `DecileResults` dataclasses for structured output
- `aggregate_by_decile()` function for per-decile aggregation
- Pack loaders in `packs/__init__.py` with `list_*_templates()` and `load_*_template()` functions

**Schema types already defined (`src/reformlab/templates/schema.py`):**
```python
@dataclass(frozen=True)
class SubsidyParameters(PolicyParameters):
    eligible_categories: tuple[str, ...] = ()
    income_caps: dict[int, float] = field(default_factory=dict)

@dataclass(frozen=True)
class RebateParameters(PolicyParameters):
    rebate_type: str = ""  # "", "lump_sum", "progressive_dividend"
    income_weights: dict[str, float] = field(default_factory=dict)

@dataclass(frozen=True)
class FeebateParameters(PolicyParameters):
    pivot_point: float = 0.0
    fee_rate: float = 0.0
    rebate_rate: float = 0.0
```

**Loader already parses these types (`src/reformlab/templates/loader.py`):**
- `_parse_parameters()` handles SUBSIDY, REBATE, FEEBATE policy types
- Returns appropriate `*Parameters` dataclass based on `policy_type`

**Pack loader pattern (`src/reformlab/templates/packs/__init__.py`):**
```python
def list_carbon_tax_templates() -> list[str]:
    carbon_tax_dir = _PACKS_DIR / "carbon_tax"
    if not carbon_tax_dir.exists():
        return []
    return [f.stem for f in sorted(carbon_tax_dir.glob("*.yaml"))]

def load_carbon_tax_template(variant_name: str) -> BaselineScenario:
    template_path = _PACKS_DIR / "carbon_tax" / f"{variant_name}.yaml"
    # ... load and validate
```

### Project Structure Notes

**Target module locations (follow carbon_tax pattern):**
```
src/reformlab/templates/
├── subsidy/
│   ├── __init__.py              # Module public API
│   ├── compute.py               # Subsidy computation
│   └── compare.py               # Batch execution and comparison
├── rebate/
│   ├── __init__.py
│   ├── compute.py
│   └── compare.py
├── feebate/
│   ├── __init__.py
│   ├── compute.py
│   └── compare.py
├── packs/
│   ├── __init__.py              # Add list/load functions for new packs
│   ├── subsidy/
│   │   ├── README.md
│   │   └── subsidy-energy-retrofit.yaml
│   ├── rebate/
│   │   ├── README.md
│   │   └── rebate-progressive-income.yaml
│   └── feebate/
│       ├── README.md
│       └── feebate-vehicle-emissions.yaml

tests/templates/
├── subsidy/
│   ├── conftest.py
│   ├── test_compute.py
│   └── test_compare.py
├── rebate/
│   ├── conftest.py
│   ├── test_compute.py
│   └── test_compare.py
├── feebate/
│   ├── conftest.py
│   ├── test_compute.py
│   └── test_compare.py
└── test_pack_loader.py          # Extend with new pack tests
```

### Key Dependencies

- `pyyaml` - Already in project for YAML loading
- `numpy` - For vectorized computation
- `pyarrow` - Existing table/array type used across data + template layers
- Story 2.1 schema types - `BaselineScenario`, `SubsidyParameters`, `RebateParameters`, `FeebateParameters`
- Story 2.2 patterns - `DecileResults`, `aggregate_by_decile()`, pack loader pattern

### Computation Logic Reference

**Subsidy computation formula:**
```
eligibility = (income <= income_cap[year]) AND (has_eligible_category)
subsidy_amount = rate_schedule[year] * eligibility_factor  # or fixed amount
```

Where:
- `income_cap[year]` = maximum income for eligibility from template
- `eligible_category` = household has characteristic in `eligible_categories`
- `rate_schedule[year]` = subsidy amount per unit or fixed amount

**Rebate computation formulas:**

Lump sum:
```
rebate_household = rebate_pool / num_households
```

Progressive dividend (same as carbon tax redistribution):
```
weighted_population = Σ (income_weight[decile] × count[decile])
rebate_household = (income_weight[household_decile] × rebate_pool) / weighted_population
```

**Feebate computation formula:**
```
if metric_value > pivot_point:
    fee = (metric_value - pivot_point) * fee_rate
    rebate = 0
else:
    fee = 0
    rebate = (pivot_point - metric_value) * rebate_rate

net_impact = rebate - fee
```

Where:
- `metric_value` = household's value on the pivot metric (e.g., vehicle emissions g/km)
- `pivot_point` = threshold from template
- `fee_rate` = EUR per unit above pivot
- `rebate_rate` = EUR per unit below pivot

### Output Data Structures

**Follow carbon tax pattern for consistency:**

```python
@dataclass(frozen=True)
class SubsidyResult:
    household_ids: pa.Array
    subsidy_amount: pa.Array       # EUR per household
    is_eligible: pa.Array          # bool array
    income_decile: pa.Array
    total_cost: float              # Sum of all subsidies
    year: int
    template_name: str

@dataclass(frozen=True)
class RebateResult:
    household_ids: pa.Array
    rebate_amount: pa.Array        # EUR per household
    income_decile: pa.Array
    total_distributed: float
    year: int
    template_name: str

@dataclass(frozen=True)
class FeebateResult:
    household_ids: pa.Array
    fee_amount: pa.Array           # EUR fee (positive)
    rebate_amount: pa.Array        # EUR rebate (positive)
    net_impact: pa.Array           # rebate - fee
    metric_value: pa.Array         # The metric used for pivot
    income_decile: pa.Array
    total_fees: float
    total_rebates: float
    net_fiscal_balance: float      # total_fees - total_rebates
    year: int
    template_name: str
```

**Reuse existing `DecileResults` from carbon_tax or create a shared module.**

### Sample Template YAML Structures

**subsidy-energy-retrofit.yaml:**
```yaml
$schema: "../../schema/scenario-template.schema.json"
version: "1.0"

name: "Subsidy - Home Energy Retrofit"
description: "Targeted subsidy for home energy efficiency improvements"
policy_type: subsidy

year_schedule:
  start_year: 2026
  end_year: 2036

parameters:
  rate_schedule:
    2026: 5000.0   # EUR flat subsidy per eligible household
    2027: 4500.0
    # ... declining over time as adoption increases

  eligible_categories:
    - "owner_occupier"
    - "low_efficiency_home"

  income_caps:
    2026: 45000.0  # Max annual household income for eligibility
    2027: 42000.0
```

**rebate-progressive-income.yaml:**
```yaml
$schema: "../../schema/scenario-template.schema.json"
version: "1.0"

name: "Rebate - Progressive Income Dividend"
description: "Progressive rebate distributed based on income weights"
policy_type: rebate

year_schedule:
  start_year: 2026
  end_year: 2036

parameters:
  rate_schedule:
    2026: 100.0    # Base rebate amount (pool per capita before weighting)

  rebate_type: "progressive_dividend"
  income_weights:
    decile_1: 2.0
    decile_2: 1.8
    decile_3: 1.5
    decile_4: 1.3
    decile_5: 1.1
    decile_6: 0.9
    decile_7: 0.7
    decile_8: 0.5
    decile_9: 0.3
    decile_10: 0.2
```

**feebate-vehicle-emissions.yaml:**
```yaml
$schema: "../../schema/scenario-template.schema.json"
version: "1.0"

name: "Feebate - Vehicle Emissions"
description: "Vehicle emissions-based feebate with pivot at average emissions"
policy_type: feebate

year_schedule:
  start_year: 2026
  end_year: 2036

parameters:
  pivot_point: 120.0     # g CO2/km - average vehicle emissions
  fee_rate: 50.0         # EUR per g/km above pivot
  rebate_rate: 50.0      # EUR per g/km below pivot

  covered_categories:
    - "passenger_vehicle"
```

### Cross-Story Dependencies

- **Depends on Story 2.1 / BKL-201 (done, hard gate):** Schema types and YAML loader with `SubsidyParameters`, `RebateParameters`, `FeebateParameters`
- **Depends on Story 2.2 / BKL-202 (currently review, soft gate):** Carbon tax computation patterns, `DecileResults`, and pack loader pattern reused by this story. If 2.2 is not merged yet, this story must vendor the shared decile utility or land after 2.2.
- **Related downstream:**
  - Story 2.4 / BKL-204: Scenario registry will store these templates
  - Story 4.1 / BKL-401: Distributional indicators by income decile (consumes outputs)

### Population Data Requirements

**Subsidy templates may need:**
- `household_id` (int64, required)
- `income` (float64, required) - for income cap eligibility and decile assignment
- `housing_tenure` (string, optional) - for owner/renter eligibility
- `home_efficiency_rating` (string/float, optional) - for retrofit eligibility

**Feebate templates may need:**
- `vehicle_emissions_gkm` (float64, optional) - g CO2/km for vehicle feebate

**Handling missing columns:** Follow Story 2.2 pattern - treat missing optional columns as excluding household from eligibility or using default values.

### Testing Standards

From existing test patterns:
- Use `pytest` with fixtures in `conftest.py`
- Use `tmp_path` fixture for file operations
- Test both success and failure paths
- Golden file tests for computation validation
- Error messages must include: summary, reason, fix guidance

### Out of Scope Guardrails

- No orchestrator integration (Story 3.x handles multi-year execution)
- No scenario registry persistence (Story 2.4)
- No behavioral responses or elasticity adjustments (Phase 2)
- No GUI/notebook visualization (Story 6.x)
- Computation is static/mechanical - no equilibrium effects
- No advanced export formatting beyond `pa.Table`

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Scenario Template Layer]
- [Source: _bmad-output/planning-artifacts/prd.md#FR7, FR10, FR11, NFR4, NFR5]
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-203]
- [Source: src/reformlab/templates/schema.py - SubsidyParameters, RebateParameters, FeebateParameters]
- [Source: src/reformlab/templates/loader.py - _parse_parameters pattern]
- [Source: src/reformlab/templates/carbon_tax/compute.py - CarbonTaxResult, DecileResults pattern]
- [Source: src/reformlab/templates/carbon_tax/compare.py - run_carbon_tax_batch pattern]
- [Source: src/reformlab/templates/packs/__init__.py - list/load template pattern]
- [Source: _bmad-output/implementation-artifacts/2-2-implement-carbon-tax-template-pack.md - Previous story patterns]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
