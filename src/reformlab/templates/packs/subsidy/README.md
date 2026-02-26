# Subsidy Template Pack

This pack contains templates for subsidy policy scenarios.

## Available Templates

### subsidy-energy-retrofit

**Purpose:** Model targeted subsidies for home energy efficiency improvements.

**Target households:**
- Owner-occupiers (renters excluded)
- Homes with low energy efficiency ratings
- Households below annual income thresholds

**Key parameters:**

| Parameter | Description |
|-----------|-------------|
| `rate_schedule` | Subsidy amount (EUR) per eligible household per year |
| `eligible_categories` | Housing characteristics required for eligibility |
| `income_caps` | Maximum household income for eligibility by year |

**Example output per household:**
- `subsidy_amount`: EUR amount received (0 if ineligible)
- `is_eligible`: Boolean eligibility status
- `income_decile`: Income decile assignment (1-10)

**Assumptions:**
1. Subsidy is a one-time payment per year per eligible household
2. Household must meet BOTH income cap AND category requirements
3. Rate declines over time as market matures and adoption increases
4. Income caps tighten over time to focus on lower-income households

## Usage

```python
from reformlab.templates.packs import load_subsidy_template, list_subsidy_templates

# List available templates
templates = list_subsidy_templates()

# Load a specific template
scenario = load_subsidy_template("subsidy-energy-retrofit")

# Use with compute_subsidy
from reformlab.templates.subsidy import compute_subsidy
result = compute_subsidy(population, scenario.parameters, year=2026, template_name=scenario.name)
```

## Data Requirements

The population table should include:

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `household_id` | int64 | Yes | Unique household identifier |
| `income` | float64 | Yes | Annual household income (EUR) |
| `owner_occupier` | bool | If in eligible_categories | True if household owns home |
| `low_efficiency_home` | bool | If in eligible_categories | True if home has low energy rating |
