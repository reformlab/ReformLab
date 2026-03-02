# Rebate Template Pack

This pack contains templates for rebate policy scenarios.

## Available Templates

### rebate-progressive-income

**Purpose:** Model progressive redistribution of environmental policy revenues.

**Distribution methods:**
- `lump_sum`: Equal per-capita dividend to all households
- `progressive_dividend`: Income-weighted dividend (lower income = higher rebate)

**Key parameters:**

| Parameter | Description |
|-----------|-------------|
| `rate_schedule` | Base rebate amount per capita (used with external rebate pool) |
| `rebate_type` | Distribution method: "lump_sum" or "progressive_dividend" |
| `income_weights` | Decile weights for progressive distribution |

**Example output per household:**
- `rebate_amount`: EUR amount received
- `income_decile`: Income decile assignment (1-10)

**Progressive dividend formula:**
```
weighted_population = Sum(income_weight[decile] * count[decile])
rebate_household = (income_weight[household_decile] * rebate_pool) / weighted_population
```

**Assumptions:**
1. Rebate pool comes from external source (e.g., carbon tax revenue)
2. All households receive some rebate (no eligibility requirements)
3. Progressive weighting transfers purchasing power from high to low income
4. Weights are relative - sum doesn't need to equal any specific value

## Usage

```python
from reformlab.templates.packs import load_rebate_template, list_rebate_templates

# List available templates
templates = list_rebate_templates()

# Load a specific template
scenario = load_rebate_template("rebate-progressive-income")

# Use with compute_rebate (rebate_pool from external source)
from reformlab.templates.rebate import compute_rebate
carbon_tax_revenue = 10_000_000  # EUR from carbon tax
result = compute_rebate(
    population,
    scenario.policy,
    rebate_pool=carbon_tax_revenue,
    year=2026,
    template_name=scenario.name
)
```

## Data Requirements

The population table should include:

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `household_id` | int64 | Yes | Unique household identifier |
| `income` | float64 | Yes | Annual household income (EUR) for decile assignment |

## Combining with Carbon Tax

This template is designed to work with carbon tax scenarios:

```python
from reformlab.templates.carbon_tax import compute_carbon_tax
from reformlab.templates.rebate import compute_rebate

# Compute carbon tax
tax_result = compute_carbon_tax(population, carbon_tax_params, emission_index, year)

# Redistribute revenue progressively
rebate_result = compute_rebate(
    population,
    rebate_params,
    rebate_pool=tax_result.total_revenue,
    year=year
)
```
