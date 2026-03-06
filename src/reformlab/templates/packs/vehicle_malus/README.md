# Vehicle Malus Template Pack

This pack contains templates for vehicle malus (emission penalty) policy scenarios.

## Available Templates

### vehicle-malus-french-2026

**Purpose:** Model the French malus ecologique with progressive threshold tightening.

**Mechanism:**
- Households with vehicle emissions above the threshold pay a malus (penalty)
- Threshold tightens annually (108 gCO2/km in 2026 down to 77 gCO2/km in 2036)
- Rate increases annually (50 EUR/gkm in 2026 up to 100 EUR/gkm in 2036)
- No rebate for low-emission vehicles (unlike feebate)

**Key parameters:**

| Parameter | Description |
|-----------|-------------|
| `emission_threshold` | gCO2/km threshold below which no malus applies |
| `malus_rate_per_gkm` | EUR per gCO2/km above threshold |
| `threshold_schedule` | Year-indexed threshold overrides (tightening) |
| `rate_schedule` | Year-indexed rate overrides (increasing) |

### vehicle-malus-flat-rate

**Purpose:** Simple flat-rate baseline for comparison against progressive designs.

**Mechanism:**
- Fixed threshold at 120 gCO2/km across all years
- Constant rate at 50 EUR per gCO2/km above threshold
- Useful as a counterfactual baseline

## Computation Formula

```
If vehicle_emissions > threshold:
    malus = (vehicle_emissions - threshold) * rate_per_gkm

If vehicle_emissions <= threshold:
    malus = 0
```

This is a simplified linear model. The actual French malus uses ~80 discrete
brackets with non-linear escalation. The linear model is appropriate for
population-level distributional analysis.

## Usage

```python
from reformlab.templates.packs import (
    list_vehicle_malus_templates,
    load_vehicle_malus_template,
)

# List available templates
templates = list_vehicle_malus_templates()

# Load a specific template
scenario = load_vehicle_malus_template("vehicle-malus-french-2026")

# Use with compute_vehicle_malus
from reformlab.templates.vehicle_malus import compute_vehicle_malus

result = compute_vehicle_malus(
    population,
    scenario.policy,
    year=2026,
    template_name=scenario.name,
)

print(f"Total revenue: {result.total_revenue}")
```

## Data Requirements

The population table should include:

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `household_id` | int64 | Yes | Unique household identifier |
| `income` | float64 | Yes | Annual household income (EUR) for decile analysis |
| `vehicle_emissions_gkm` | float64 | No | Vehicle CO2 emissions (g/km); missing = 0 |
