# Energy Poverty Aid Template Pack

This pack contains templates for energy poverty aid policy scenarios.

## Available Templates

### energy-poverty-cheque-energie

**Purpose:** Model the French cheque energie with inflation-adjusted ceiling.

**Mechanism:**
- Households with income below ceiling AND energy expenditure share at or above threshold receive aid
- Aid scales linearly with income (poorest get most) and energy burden severity
- Income ceiling adjusts for inflation (11,000 EUR in 2026 to 13,000 EUR in 2036)
- Base aid increases gradually (150 EUR in 2026 to 200 EUR in 2036)

**Key parameters:**

| Parameter | Description |
|-----------|-------------|
| `income_ceiling` | EUR RFR/UC threshold for eligibility |
| `energy_share_threshold` | Minimum energy expenditure share of income (8%) |
| `base_aid_amount` | Base aid in EUR (scaled by income ratio and energy burden) |
| `max_energy_factor` | Cap on energy burden multiplier |

### energy-poverty-generous

**Purpose:** Higher-aid variant for comparison against standard cheque energie.

**Mechanism:**
- Higher income ceiling (15,000 EUR, +36% more households eligible)
- Stricter energy share threshold (10% vs 8%)
- Doubled base aid amount (300 EUR vs 150 EUR)
- Overall substantially more generous program

## Computation Formula

```
Eligibility:
    income < income_ceiling AND energy_expenditure / income >= energy_share_threshold

Aid amount (for eligible households):
    income_ratio = (income_ceiling - income) / income_ceiling
    energy_burden_factor = min(energy_share / threshold, max_energy_factor)
    aid = base_aid_amount * income_ratio * energy_burden_factor
```

This is a simplified linear model. The actual French cheque energie uses a 12-cell
matrix (4 income brackets x 3 household size categories). The linear model is
appropriate for population-level distributional analysis.

## Usage

```python
from reformlab.templates.packs import (
    list_energy_poverty_aid_templates,
    load_energy_poverty_aid_template,
)

# List available templates
templates = list_energy_poverty_aid_templates()

# Load a specific template
scenario = load_energy_poverty_aid_template("energy-poverty-cheque-energie")

# Use with compute_energy_poverty_aid
from reformlab.templates.energy_poverty_aid import compute_energy_poverty_aid

result = compute_energy_poverty_aid(
    population,
    scenario.policy,
    year=2026,
    template_name=scenario.name,
)

print(f"Total cost: {result.total_cost}")
print(f"Eligible households: {result.eligible_count}")
```

## Data Requirements

The population table should include:

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `household_id` | int64 | Yes | Unique household identifier |
| `income` | float64 | Yes | Annual household income (EUR) for eligibility and decile analysis |
| `energy_expenditure` | float64 | No | Annual energy expenditure (EUR); missing = 0 (no one eligible) |
