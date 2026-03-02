# Feebate Template Pack

This pack contains templates for feebate policy scenarios.

## Available Templates

### feebate-vehicle-emissions

**Purpose:** Model vehicle emissions-based feebate systems (bonus-malus schemes).

**Mechanism:**
- Households with vehicles above the pivot point pay fees (malus)
- Households with vehicles below the pivot point receive rebates (bonus)
- Symmetric rates can create revenue-neutral design

**Key parameters:**

| Parameter | Description |
|-----------|-------------|
| `pivot_point` | Threshold value (g CO2/km) - average emissions level |
| `fee_rate` | EUR per g/km above pivot (fee for high emitters) |
| `rebate_rate` | EUR per g/km below pivot (rebate for low emitters) |
| `covered_categories` | Vehicle types included in the scheme |

**Example output per household:**
- `fee_amount`: EUR fee paid (if above pivot)
- `rebate_amount`: EUR rebate received (if below pivot)
- `net_impact`: rebate_amount - fee_amount
- `metric_value`: Household's vehicle emissions (g/km)

**Computation formulas:**
```
If vehicle_emissions > pivot_point:
    fee = (vehicle_emissions - pivot_point) * fee_rate
    rebate = 0

If vehicle_emissions < pivot_point:
    fee = 0
    rebate = (pivot_point - vehicle_emissions) * rebate_rate

net_impact = rebate - fee
```

**Assumptions:**
1. One vehicle per household (can be extended for multi-vehicle)
2. Pivot point set at population average for revenue neutrality
3. Fee and rebate rates are symmetric by default
4. Households at exactly pivot point pay/receive nothing

## Usage

```python
from reformlab.templates.packs import load_feebate_template, list_feebate_templates

# List available templates
templates = list_feebate_templates()

# Load a specific template
scenario = load_feebate_template("feebate-vehicle-emissions")

# Use with compute_feebate
from reformlab.templates.feebate import compute_feebate
result = compute_feebate(
    population,
    scenario.policy,
    metric_column="vehicle_emissions_gkm",
    year=2026,
    template_name=scenario.name
)

# Check fiscal balance
print(f"Total fees: {result.total_fees}")
print(f"Total rebates: {result.total_rebates}")
print(f"Net fiscal balance: {result.net_fiscal_balance}")
```

## Data Requirements

The population table should include:

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `household_id` | int64 | Yes | Unique household identifier |
| `income` | float64 | Yes | Annual household income (EUR) for decile analysis |
| `vehicle_emissions_gkm` | float64 | Yes | Vehicle CO2 emissions (g/km) |

## Revenue Neutrality

With symmetric rates and pivot at population average:
- Sum of fees should approximately equal sum of rebates
- Net fiscal balance should be near zero
- Actual balance depends on emissions distribution shape

To achieve exact revenue neutrality, adjust rates based on population:
```python
# Compute with initial rates
result = compute_feebate(population, params, "vehicle_emissions_gkm", year)

# Calculate adjustment factor for revenue neutrality
adjustment = result.total_rebates / result.total_fees if result.total_fees > 0 else 1.0

# Adjust fee_rate = fee_rate * adjustment
```

## Distributional Analysis

Use `aggregate_feebate_by_decile()` to analyze impacts by income:

```python
from reformlab.templates.feebate import aggregate_feebate_by_decile

decile_results = aggregate_feebate_by_decile(result)

# Lower deciles may benefit if they own lower-emission vehicles
for d in range(10):
    print(f"Decile {d+1}: mean net impact = {decile_results.mean_net_impact[d]:.2f}")
```
