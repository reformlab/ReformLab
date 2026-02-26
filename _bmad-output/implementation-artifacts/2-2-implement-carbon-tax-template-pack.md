# Story 2.2: Implement Carbon Tax Template Pack

Status: ready-for-dev

## Story

As a **policy analyst**,
I want **a ready-to-use carbon tax template pack with 4-5 policy variants**,
so that **I can immediately run carbon tax scenario comparisons without writing code, comparing flat vs progressive rates and different redistribution mechanisms**.

## Acceptance Criteria

1. **AC-1: Template pack provides at least 4 variants**
   - Given the shipped carbon-tax template pack, when listed, then at least 4 variants are available covering: flat rate, progressive rate, flat dividend, and progressive dividend combinations.
   - Template variants are named descriptively (e.g., `carbon-tax-flat-no-dividend`, `carbon-tax-progressive-lump-sum`).
   - All templates pass schema validation from Story 2.1.

2. **AC-2: Tax burden computation per household**
   - Given a carbon-tax template, when executed with a baseline population, then tax burden is computed per household based on energy consumption and applicable rates.
   - Tax burden computation uses emission factors and energy category consumption from population data.
   - Exemption rules from template parameters are applied correctly (partial exemptions, category exemptions).

3. **AC-3: Redistribution amounts computed per household**
   - Given a carbon-tax template with redistribution parameters, when executed, then redistribution amounts are computed per household.
   - Flat dividend: total tax revenue divided equally across households.
   - Progressive dividend: weighted by income decile using template-defined `income_weights`.
   - Net impact (tax burden minus redistribution) is computed per household.

4. **AC-4: Per-decile comparison output**
   - Given two carbon-tax variants, when run in batch, then comparison output shows per-decile differences.
   - Output includes: mean tax burden by decile, mean redistribution by decile, mean net impact by decile.
   - Output format supports both programmatic access (dict/DataFrame) and YAML/CSV export.

5. **AC-5: Template pack is documented and discoverable**
   - Template pack files are shipped in `src/reformlab/templates/packs/carbon_tax/`.
   - Pack includes a README.md describing each variant and parameter meanings.
   - API provides `list_carbon_tax_templates()` and `load_carbon_tax_template(variant_name)` functions.

## Tasks / Subtasks

- [ ] Task 0: Extend population schema with energy consumption columns (prerequisite)
  - [ ] 0.1 Add energy consumption columns to `SYNTHETIC_POPULATION_SCHEMA` in `src/reformlab/data/schemas.py`:
    - `energy_transport_fuel` (float64, optional)
    - `energy_heating_fuel` (float64, optional)
    - `energy_natural_gas` (float64, optional)
  - [ ] 0.2 Update `tests/data/test_pipeline.py` with energy column fixtures
  - [ ] 0.3 Create sample synthetic population with energy data for testing

- [ ] Task 1: Create carbon tax computation module (AC: #2, #3)
  - [ ] 1.1 Create `src/reformlab/templates/carbon_tax/compute.py` with core functions
  - [ ] 1.2 Implement `assign_income_deciles(incomes: pa.Array) -> pa.Array` using percentile ranking
  - [ ] 1.3 Implement `compute_tax_burden(population: pa.Table, parameters: CarbonTaxParameters, emission_index: EmissionFactorIndex, year: int) -> pa.Array`
  - [ ] 1.4 Implement `compute_flat_redistribution(total_revenue: float, num_households: int) -> pa.Array`
  - [ ] 1.5 Implement `compute_progressive_redistribution(total_revenue: float, deciles: pa.Array, income_weights: dict[str, float]) -> pa.Array`
  - [ ] 1.6 Implement `apply_exemptions(base_tax: pa.Array, categories: list[str], exemptions: tuple[dict, ...]) -> pa.Array`
  - [ ] 1.7 Create `CarbonTaxResult` and `DecileResults` dataclasses

- [ ] Task 2: Create 4-5 carbon tax template YAML files (AC: #1, #5)
  - [ ] 2.1 Create `carbon-tax-flat-no-redistribution.yaml` - flat rate, no dividend
  - [ ] 2.2 Create `carbon-tax-flat-lump-sum-dividend.yaml` - flat rate, equal per-capita dividend
  - [ ] 2.3 Create `carbon-tax-flat-progressive-dividend.yaml` - flat rate, income-weighted dividend
  - [ ] 2.4 Create `carbon-tax-progressive-no-redistribution.yaml` - income-indexed rates, no dividend
  - [ ] 2.5 Create `carbon-tax-progressive-progressive-dividend.yaml` - income-indexed rates, income-weighted dividend
  - [ ] 2.6 Create pack README.md documenting variants and use cases

- [ ] Task 3: Implement template pack loader and discovery (AC: #5)
  - [ ] 3.1 Create `src/reformlab/templates/packs/__init__.py` with pack discovery utilities
  - [ ] 3.2 Implement `list_carbon_tax_templates()` returning available variant names
  - [ ] 3.3 Implement `load_carbon_tax_template(variant_name)` returning `BaselineScenario`
  - [ ] 3.4 Add pack loader to `reformlab.templates` public API

- [ ] Task 4: Implement batch execution and comparison (AC: #4)
  - [ ] 4.1 Create `src/reformlab/templates/carbon_tax/compare.py` for comparison utilities
  - [ ] 4.2 Implement `run_carbon_tax_batch(population, template_names)` function
  - [ ] 4.3 Implement `compare_decile_impacts(results: dict[str, DecileResults])` function
  - [ ] 4.4 Support output as dict, DataFrame, and YAML/CSV export

- [ ] Task 5: Write comprehensive tests (AC: all)
  - [ ] 5.1 Unit tests for tax burden computation with various exemption scenarios
  - [ ] 5.2 Unit tests for redistribution computation (flat and progressive)
  - [ ] 5.3 Integration tests for template loading and pack discovery
  - [ ] 5.4 Golden file tests for expected computation outputs
  - [ ] 5.5 Comparison output format tests

## Dev Notes

### Architecture Patterns to Follow

**From architecture.md:**
- Templates are Python code in template modules, not YAML formula strings (formulas are not compiled)
- Scenario Template Layer sits above Data Layer and below Dynamic Orchestrator
- Environmental policy templates encode business logic as reusable scenario artifacts
- Year-indexed policy schedules for at least 10 years (FR12)

**From PRD:**
- FR7: Analyst can load prebuilt environmental policy templates (carbon tax, subsidy, rebate, feebate)
- FR10: Analyst can run multiple scenarios in one batch for comparison
- FR11: Analyst can compose tax-benefit baseline outputs with environmental template logic in one workflow
- NFR4: YAML configuration loading and validation completes in under 1 second
- NFR5: Analytical operations (distributional analysis) execute in under 5 seconds for 100k households

### Existing Code Patterns to Follow

**From Story 2.1 (src/reformlab/templates/):**
- `CarbonTaxParameters` dataclass already defined with `rate_schedule`, `exemptions`, `covered_categories`
- `load_scenario_template()` loads YAML and returns typed `BaselineScenario` or `ReformScenario`
- `ScenarioError` for structured error handling with actionable messages
- Schema validation pattern established

**Carbon tax parameter structure (from schema.py):**
```python
@dataclass(frozen=True)
class CarbonTaxParameters(PolicyParameters):
    """Carbon tax specific parameters.

    Includes rate schedule (EUR per tonne CO2), exemptions by category,
    and covered energy categories.
    """
    pass  # Inherits rate_schedule, exemptions, thresholds, covered_categories
```

**Redistribution parameter structure (from RebateParameters):**
```python
@dataclass(frozen=True)
class RebateParameters(PolicyParameters):
    rebate_type: str = ""  # "lump_sum" or "progressive_dividend"
    income_weights: dict[str, float] = field(default_factory=dict)
```

### Project Structure Notes

**Target module locations:**
- `src/reformlab/templates/packs/` - Template pack files (YAML + README)
- `src/reformlab/templates/packs/carbon_tax/` - Carbon tax specific pack
- `src/reformlab/templates/carbon_tax/` - Carbon tax computation module
- `tests/templates/carbon_tax/` - Carbon tax specific tests

**Files to create:**
```
src/reformlab/templates/
├── packs/
│   ├── __init__.py              # Pack discovery utilities
│   └── carbon_tax/
│       ├── README.md            # Pack documentation
│       ├── carbon-tax-flat-no-redistribution.yaml
│       ├── carbon-tax-flat-lump-sum-dividend.yaml
│       ├── carbon-tax-flat-progressive-dividend.yaml
│       ├── carbon-tax-progressive-no-redistribution.yaml
│       └── carbon-tax-progressive-progressive-dividend.yaml
├── carbon_tax/
│   ├── __init__.py              # Module public API
│   ├── compute.py               # Tax burden and redistribution computation
│   └── compare.py               # Batch execution and comparison

tests/templates/carbon_tax/
├── conftest.py                  # Test fixtures
├── test_compute.py              # Computation unit tests
├── test_pack_loader.py          # Pack discovery tests
├── test_compare.py              # Comparison output tests
└── test_golden_outputs.py       # Golden file validation
```

### Key Dependencies

- `pyyaml` - Already in project for YAML loading
- `numpy` - For vectorized tax/redistribution computation
- `polars` or `pandas` - For DataFrame output format (check existing data layer usage)
- Story 2.1 schema types - `BaselineScenario`, `CarbonTaxParameters`, `load_scenario_template`

### Cross-Story Dependencies

- **Depends on Story 2.1 / BKL-201 (required):** Schema types and YAML loader ✓ Complete
- **Depends on Story 1.2 / BKL-102 (required):** Population data structure for energy consumption
- **Depends on Story 1.3 / BKL-103 (required):** Mapping patterns for emission factor data
- **Related downstream stories:**
  - Story 2.3 / BKL-203: Subsidy/rebate/feebate template pack (similar pattern)
  - Story 2.4 / BKL-204: Scenario registry will store these templates
  - Story 4.1 / BKL-401: Distributional indicators by income decile (consumes our outputs)

### Required Population Data Columns

The carbon tax computation requires the following columns in the population data. **CRITICAL:** The current `SYNTHETIC_POPULATION_SCHEMA` in `src/reformlab/data/schemas.py` does NOT include energy consumption columns - this story needs to either:
1. Extend the schema (recommended - add optional energy consumption columns), OR
2. Accept energy consumption as a separate input table

**Required columns for carbon tax computation:**
```python
# From existing SYNTHETIC_POPULATION_SCHEMA
"household_id"     # int64, required - unique household identifier
"income"           # float64, required - household annual income (for decile assignment)

# Energy consumption columns (need to be added or provided separately)
"energy_transport_fuel"   # float64 - annual transport fuel consumption (liters or kWh)
"energy_heating_fuel"     # float64 - annual heating fuel consumption (liters or kWh)
"energy_natural_gas"      # float64 - annual natural gas consumption (m³ or kWh)
```

**Recommended approach:** Add optional energy consumption columns to `SYNTHETIC_POPULATION_SCHEMA` in a separate data-layer sub-task, then consume in this story.

### Emission Factor Integration

Use existing `EmissionFactorIndex` from `src/reformlab/data/emission_factors.py`:
```python
from reformlab.data.emission_factors import EmissionFactorIndex, build_emission_factor_index

# Load emission factors and create index
emission_index = build_emission_factor_index(emission_table)

# Lookup by category and year
factors = emission_index.by_category_and_year("transport_fuel", 2026)
factor_value = factors.column("factor_value")[0].as_py()  # kg CO2 per unit
```

### Income Decile Assignment

For progressive redistribution, households must be assigned to income deciles (1-10):
```python
def assign_income_deciles(incomes: pa.Array) -> pa.Array:
    """Assign decile labels 1-10 based on income distribution."""
    # Use percentile-based assignment
    # Decile 1 = bottom 10%, Decile 10 = top 10%
    quantiles = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    # Return int array of decile assignments
```

### Computation Logic Reference

**Carbon tax burden formula:**
```
tax_burden_household = Σ (energy_consumption[category] × emission_factor[category] × rate[year])
                       × (1 - exemption_rate[category])
```

Where:
- `energy_consumption[category]` = household's annual consumption in category units (liters, kWh, m³)
- `emission_factor[category]` = kg CO2 per unit from `EmissionFactorIndex`
- `rate[year]` = EUR per tonne CO2 from template `rate_schedule`
- `exemption_rate[category]` = from template `exemptions` (0.0 if no exemption)

**Flat dividend formula:**
```
dividend_household = total_tax_revenue / num_households
```

**Progressive dividend formula:**
```
weighted_population = Σ (income_weight[decile] × count[decile])
dividend_household = (income_weight[household_decile] × total_tax_revenue) / weighted_population
```

Where `income_weight[decile]` comes from template `redistribution.income_weights` (e.g., `decile_1: 1.5`)

### Output Data Structures

**CarbonTaxResult (per-household computation result):**
```python
@dataclass(frozen=True)
class CarbonTaxResult:
    """Result of carbon tax computation for a single scenario run."""
    household_ids: pa.Array          # int64 array of household IDs
    tax_burden: pa.Array             # float64 array of tax amounts (EUR)
    redistribution: pa.Array         # float64 array of dividend amounts (EUR)
    net_impact: pa.Array             # float64 array (redistribution - tax_burden)
    income_decile: pa.Array          # int64 array (1-10)
    total_revenue: float             # Sum of all tax_burden
    total_redistribution: float      # Sum of all redistribution
    year: int                        # Computation year
    template_name: str               # Source template name
```

**DecileResults (aggregated by income decile):**
```python
@dataclass(frozen=True)
class DecileResults:
    """Per-decile aggregated carbon tax results."""
    decile: tuple[int, ...]              # (1, 2, 3, ..., 10)
    household_count: tuple[int, ...]     # Count per decile
    mean_tax_burden: tuple[float, ...]   # Mean EUR per decile
    mean_redistribution: tuple[float, ...]
    mean_net_impact: tuple[float, ...]
    total_tax_burden: tuple[float, ...]  # Sum EUR per decile
    total_redistribution: tuple[float, ...]
    total_net_impact: tuple[float, ...]
```

**ComparisonResult (cross-scenario comparison):**
```python
@dataclass(frozen=True)
class ComparisonResult:
    """Comparison of multiple carbon tax scenarios by decile."""
    scenarios: tuple[str, ...]           # Template names
    decile_results: dict[str, DecileResults]  # By scenario name
    comparison_table: pa.Table           # Wide-format comparison
```

### Testing Standards

**From existing test patterns:**
- Use `pytest` with fixtures in `conftest.py`
- Use `tmp_path` fixture for file operations
- Test both success and failure paths
- Golden file tests for computation validation
- Error messages must include: summary, reason, fix guidance

### Out of Scope Guardrails

- No orchestrator integration (Story 3.x handles multi-year execution)
- No scenario registry persistence (Story 2.4)
- No GUI/notebook visualization (Story 6.x)
- No behavioral responses or elasticity adjustments (Phase 2)
- Computation is static/mechanical - no equilibrium effects

### Carbon Tax Template Variant Specifications

**Variant 1: Flat Rate, No Redistribution**
- Single carbon price (EUR/tCO2) applied uniformly
- All tax revenue retained by government
- Baseline comparison scenario

**Variant 2: Flat Rate, Lump-Sum Dividend**
- Single carbon price applied uniformly
- 100% revenue recycled as equal per-capita dividend
- Revenue-neutral by construction

**Variant 3: Flat Rate, Progressive Dividend**
- Single carbon price applied uniformly
- Revenue recycled with income-weighted dividends
- Lower deciles receive higher share

**Variant 4: Progressive Rate, No Redistribution**
- Tax rate varies by household income (higher income = higher rate)
- All tax revenue retained by government
- Tests ability-to-pay principle

**Variant 5: Progressive Rate, Progressive Dividend**
- Tax rate varies by household income
- Revenue recycled with income-weighted dividends
- Maximum progressivity scenario

### Sample Template YAML Structure

```yaml
# carbon-tax-flat-lump-sum-dividend.yaml
$schema: "../schema/scenario-template.schema.json"
version: "1.0"

name: "Carbon Tax - Flat Rate with Lump-Sum Dividend"
description: "Uniform carbon tax with equal per-capita dividend redistribution"
policy_type: carbon_tax

year_schedule:
  start_year: 2026
  end_year: 2036

parameters:
  rate_schedule:
    2026: 44.60
    2027: 50.00
    2028: 55.00
    # ... through 2036

  covered_categories:
    - "transport_fuel"
    - "heating_fuel"
    - "natural_gas"

  exemptions:
    - category: "agricultural_fuel"
      rate_reduction: 1.0

  redistribution:
    type: "lump_sum"
    # No income_weights needed for flat dividend
```

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Scenario Template Layer]
- [Source: _bmad-output/planning-artifacts/prd.md#FR7, FR10, FR11, NFR4, NFR5]
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-202]
- [Source: src/reformlab/templates/schema.py - CarbonTaxParameters, PolicyParameters]
- [Source: src/reformlab/templates/loader.py - load_scenario_template pattern]
- [Source: tests/fixtures/templates/golden-carbon-tax.yaml - Example template structure]
- [Source: _bmad-output/implementation-artifacts/2-1-define-scenario-template-schema.md - Previous story patterns]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

