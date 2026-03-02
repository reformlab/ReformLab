# Carbon Tax Template Pack

Ready-to-use carbon tax scenario templates for policy analysis. This pack provides 5 variants covering different rate structures and redistribution mechanisms for comparative analysis.

## Quick Start

```python
from reformlab.templates.packs import list_carbon_tax_templates, load_carbon_tax_template

# List available variants
variants = list_carbon_tax_templates()
print(variants)
# ['carbon-tax-flat-no-redistribution', 'carbon-tax-flat-lump-sum-dividend', ...]

# Load a specific template
template = load_carbon_tax_template("carbon-tax-flat-lump-sum-dividend")
```

## Template Variants

### 1. Flat Rate, No Redistribution
**File:** `carbon-tax-flat-no-redistribution.yaml`

Baseline scenario with uniform carbon price. All tax revenue retained by government.

- **Use case:** Baseline comparison, revenue-raising scenarios
- **Distributional impact:** Regressive (higher burden on lower incomes as % of income)

### 2. Flat Rate with Lump-Sum Dividend
**File:** `carbon-tax-flat-lump-sum-dividend.yaml`

Uniform carbon tax with 100% revenue returned as equal per-capita dividend.

- **Use case:** Revenue-neutral carbon pricing, "fee and dividend" proposals
- **Distributional impact:** Mildly progressive (lower-income households typically receive more than they pay)

### 3. Flat Rate with Progressive Dividend
**File:** `carbon-tax-flat-progressive-dividend.yaml`

Uniform carbon tax with income-weighted dividend redistribution.

- **Use case:** Carbon pricing with explicit redistribution to lower incomes
- **Distributional impact:** Progressive (lower deciles receive higher share)

### 4. Progressive Rate, No Redistribution
**File:** `carbon-tax-progressive-no-redistribution.yaml`

Income-based tax rates (ability-to-pay principle). Higher-income households pay higher effective rates.

- **Use case:** Testing ability-to-pay carbon taxation
- **Distributional impact:** Progressive (higher earners pay more per tonne)

### 5. Progressive Rate with Progressive Dividend
**File:** `carbon-tax-progressive-progressive-dividend.yaml`

Maximum progressivity: combines income-based rates with income-weighted redistribution.

- **Use case:** Maximum redistributive impact analysis
- **Distributional impact:** Highly progressive (dual mechanism)

## Parameters

### Rate Schedule
All templates use a 10-year rate trajectory (2026-2036) based on EU ETS reference prices:

| Year | Rate (EUR/tCO2) |
|------|-----------------|
| 2026 | 44.60 |
| 2027 | 50.00 |
| 2028 | 55.00 |
| 2029 | 60.00 |
| 2030 | 65.00 |
| 2031 | 70.00 |
| 2032 | 75.00 |
| 2033 | 80.00 |
| 2034 | 85.00 |
| 2035 | 90.00 |
| 2036 | 100.00 |

### Covered Categories
All templates cover the same energy categories:
- **transport_fuel:** Gasoline, diesel for transportation
- **heating_fuel:** Heating oil for residential heating
- **natural_gas:** Natural gas for heating and cooking

### Emission Factors
Computation uses emission factors from the EmissionFactorIndex:
- Transport fuel: ~2.31 kg CO2/liter (gasoline)
- Heating fuel: ~2.68 kg CO2/liter (heating oil)
- Natural gas: ~2.0 kg CO2/m³

### Income Weights (Progressive Variants)
For progressive redistribution, weights determine share of total revenue:

| Decile | Weight | Description |
|--------|--------|-------------|
| 1 | 1.5 | Bottom 10% - highest share |
| 2 | 1.3 | |
| 3 | 1.2 | |
| 4 | 1.1 | |
| 5 | 1.0 | Median income - baseline |
| 6 | 0.9 | |
| 7 | 0.8 | |
| 8 | 0.7 | |
| 9 | 0.5 | |
| 10 | 0.2 | Top 10% - lowest share |

## Running Scenarios

```python
from reformlab.templates.packs import load_carbon_tax_template
from reformlab.templates.carbon_tax import compute_carbon_tax, aggregate_by_decile
from reformlab.data.emission_factors import build_emission_factor_index

# Load template
template = load_carbon_tax_template("carbon-tax-flat-lump-sum-dividend")

# Run computation
result = compute_carbon_tax(
    population=population_table,
    policy=template.policy,
    emission_index=emission_index,
    year=2026,
    template_name=template.name,
)

# Aggregate by decile
decile_results = aggregate_by_decile(result)
print(f"Mean net impact decile 1: {decile_results.mean_net_impact[0]:.2f} EUR")
print(f"Mean net impact decile 10: {decile_results.mean_net_impact[9]:.2f} EUR")
```

## Assumptions and Limitations

1. **Static analysis:** No behavioral responses or price elasticity adjustments
2. **Annual snapshot:** Each year computed independently (no vintage tracking in this module)
3. **Household-level:** Redistribution computed per household, not per capita
4. **Emission factors:** Assumed constant within year; factors must be provided externally
5. **Coverage:** Only covers explicit energy categories; embedded carbon not included

## Data Requirements

Population tables must include:
- `household_id`: Unique household identifier
- `income`: Annual household income (for decile assignment)
- `energy_transport_fuel`: Annual transport fuel consumption (optional, defaults to 0)
- `energy_heating_fuel`: Annual heating fuel consumption (optional, defaults to 0)
- `energy_natural_gas`: Annual natural gas consumption (optional, defaults to 0)

## References

- EU ETS carbon prices: [European Commission](https://climate.ec.europa.eu/eu-action/eu-emissions-trading-system-eu-ets_en)
- French carbon tax (Contribution Climat-Energie): [Ministry of Ecological Transition](https://www.ecologie.gouv.fr/)
- Carbon dividend proposals: [Citizens' Climate Lobby](https://citizensclimatelobby.org/)
