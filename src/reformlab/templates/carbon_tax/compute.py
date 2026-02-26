"""Carbon tax computation functions.

This module implements the core computation logic for carbon tax scenarios:
- Tax burden calculation per household based on energy consumption and emission factors
- Redistribution calculation (lump sum and progressive dividend)
- Income decile assignment for progressive redistribution
- Result aggregation by decile
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pyarrow as pa
import pyarrow.compute as pc

from reformlab.data.emission_factors import EmissionFactorIndex
from reformlab.data.schemas import fill_missing_energy_columns
from reformlab.templates.schema import CarbonTaxParameters


@dataclass(frozen=True)
class CarbonTaxResult:
    """Result of carbon tax computation for a single scenario run.

    Contains per-household tax burden, redistribution, and net impact,
    along with summary statistics.
    """

    household_ids: pa.Array
    tax_burden: pa.Array
    redistribution: pa.Array
    net_impact: pa.Array
    income_decile: pa.Array
    total_revenue: float
    total_redistribution: float
    year: int
    template_name: str


@dataclass(frozen=True)
class DecileResults:
    """Per-decile aggregated carbon tax results.

    Contains mean and total metrics for each income decile (1-10).
    """

    decile: tuple[int, ...]
    household_count: tuple[int, ...]
    mean_tax_burden: tuple[float, ...]
    mean_redistribution: tuple[float, ...]
    mean_net_impact: tuple[float, ...]
    total_tax_burden: tuple[float, ...]
    total_redistribution: tuple[float, ...]
    total_net_impact: tuple[float, ...]


# Mapping from energy column names to emission factor categories
_ENERGY_COLUMN_TO_CATEGORY = {
    "energy_transport_fuel": "transport_fuel",
    "energy_heating_fuel": "heating_fuel",
    "energy_natural_gas": "natural_gas",
}


def assign_income_deciles(incomes: pa.Array) -> pa.Array:
    """Assign decile labels 1-10 based on income distribution.

    Uses percentile-based assignment where decile 1 contains the bottom 10%
    of incomes and decile 10 contains the top 10%.

    Args:
        incomes: Array of household incomes.

    Returns:
        Array of decile assignments (1-10) as int64.
    """
    n = len(incomes)
    if n == 0:
        return pa.array([], type=pa.int64())

    # Get sort indices to rank incomes
    indices = pc.sort_indices(incomes)

    # Create rank mapping: original index -> rank
    ranks = [0] * n
    for rank, idx in enumerate(indices.to_pylist()):
        ranks[idx] = rank

    # Convert ranks to deciles (1-10)
    # decile = floor(rank / n * 10) + 1, capped at 10
    deciles = []
    for rank in ranks:
        decile = int(rank / n * 10) + 1
        decile = min(decile, 10)  # Cap at 10
        deciles.append(decile)

    return pa.array(deciles, type=pa.int64())


def get_exemption_rate(
    category: str,
    exemptions: tuple[dict[str, Any], ...],
) -> float:
    """Get the exemption rate reduction for a given category.

    Args:
        category: The emission category (e.g., "transport_fuel").
        exemptions: Tuple of exemption dicts with "category" and "rate_reduction" keys.

    Returns:
        The rate reduction (0.0 to 1.0). Returns 0.0 if no exemption applies.
    """
    for exemption in exemptions:
        if exemption.get("category") == category:
            return float(exemption.get("rate_reduction", 0.0))
    return 0.0


def compute_tax_burden(
    population: pa.Table,
    parameters: CarbonTaxParameters,
    emission_index: EmissionFactorIndex,
    year: int,
) -> pa.Array:
    """Compute carbon tax burden for each household.

    The tax burden formula is:
    tax_burden = Σ (energy_consumption[category] × emission_factor_kg / 1000 ×
                    rate_eur_per_tonne × (1 - exemption_rate))

    Args:
        population: Population table with household data and energy columns.
        parameters: Carbon tax parameters including rate schedule and exemptions.
        emission_index: Index of emission factors by category and year.
        year: Year for which to compute tax (determines rate and emission factors).

    Returns:
        Array of tax burden amounts in EUR per household.
    """
    # Ensure energy columns exist (fill with 0.0 if missing)
    population = fill_missing_energy_columns(population)

    # Get the carbon tax rate for this year
    rate_eur_per_tonne = parameters.rate_schedule.get(year, 0.0)

    num_households = population.num_rows
    tax_burdens = [0.0] * num_households

    # Process each covered category
    for energy_col, category in _ENERGY_COLUMN_TO_CATEGORY.items():
        if category not in parameters.covered_categories:
            continue

        # Get exemption rate for this category
        exemption_rate = get_exemption_rate(category, parameters.exemptions)
        effective_rate = rate_eur_per_tonne * (1.0 - exemption_rate)

        if effective_rate <= 0:
            continue

        # Get emission factor for this category and year
        try:
            factor_table = emission_index.by_category_and_year(category, year)
            if factor_table.num_rows == 0:
                continue
            emission_factor_kg = factor_table.column("factor_value")[0].as_py()
        except (ValueError, KeyError):
            # No emission factor available for this category/year
            continue

        # Convert kg CO2 to tonnes CO2
        emission_factor_tonne = emission_factor_kg / 1000.0

        # Get energy consumption for this category
        energy_consumption = population.column(energy_col)

        # Compute tax for this category
        for i in range(num_households):
            consumption = energy_consumption[i].as_py()
            if consumption is None:
                consumption = 0.0
            category_tax = consumption * emission_factor_tonne * effective_rate
            tax_burdens[i] += category_tax

    return pa.array(tax_burdens, type=pa.float64())


def compute_lump_sum_redistribution(
    total_revenue: float,
    num_households: int,
) -> pa.Array:
    """Compute lump sum redistribution (equal per-capita dividend).

    Args:
        total_revenue: Total tax revenue to redistribute.
        num_households: Number of households to distribute to.

    Returns:
        Array of redistribution amounts per household.
    """
    if num_households == 0:
        return pa.array([], type=pa.float64())

    per_household = total_revenue / num_households
    return pa.array([per_household] * num_households, type=pa.float64())


def compute_progressive_redistribution(
    total_revenue: float,
    deciles: pa.Array,
    income_weights: dict[str, float],
) -> pa.Array:
    """Compute progressive redistribution based on income decile weights.

    Lower income deciles receive higher redistribution amounts based on
    the income_weights mapping.

    Formula:
    weighted_population = Σ (income_weight[decile] × count[decile])
    dividend_household = (income_weight[household_decile] × total_revenue) / weighted_population

    Args:
        total_revenue: Total tax revenue to redistribute.
        deciles: Array of decile assignments (1-10) for each household.
        income_weights: Mapping of decile names to weight multipliers.

    Returns:
        Array of redistribution amounts per household.
    """
    n = len(deciles)
    if n == 0:
        return pa.array([], type=pa.float64())

    decile_list = deciles.to_pylist()

    # Calculate weighted population
    weighted_sum = 0.0
    for decile in decile_list:
        weight_key = f"decile_{decile}"
        weight = income_weights.get(weight_key, 1.0)
        weighted_sum += weight

    if weighted_sum == 0:
        # Fallback to equal distribution
        return compute_lump_sum_redistribution(total_revenue, n)

    # Calculate redistribution per household based on their decile
    redistributions = []
    for decile in decile_list:
        weight_key = f"decile_{decile}"
        weight = income_weights.get(weight_key, 1.0)
        household_share = (weight * total_revenue) / weighted_sum
        redistributions.append(household_share)

    return pa.array(redistributions, type=pa.float64())


def compute_carbon_tax(
    population: pa.Table,
    parameters: CarbonTaxParameters,
    emission_index: EmissionFactorIndex,
    year: int,
    template_name: str = "",
) -> CarbonTaxResult:
    """Compute complete carbon tax results for a population.

    This is the main entry point for carbon tax computation. It:
    1. Computes tax burden per household
    2. Assigns income deciles
    3. Computes redistribution based on parameters
    4. Calculates net impact per household

    Args:
        population: Population table with household data and energy columns.
        parameters: Carbon tax parameters.
        emission_index: Index of emission factors.
        year: Year for computation.
        template_name: Name of the template being executed.

    Returns:
        CarbonTaxResult with all per-household and aggregate metrics.
    """
    # Ensure energy columns exist
    population = fill_missing_energy_columns(population)

    # Get household IDs
    household_ids = population.column("household_id")

    # Compute tax burden
    tax_burden = compute_tax_burden(population, parameters, emission_index, year)
    total_revenue = float(pc.sum(tax_burden).as_py())

    # Assign income deciles
    incomes = population.column("income")
    income_deciles = assign_income_deciles(incomes)

    # Compute redistribution based on type
    num_households = population.num_rows
    if parameters.redistribution_type == "lump_sum":
        redistribution = compute_lump_sum_redistribution(total_revenue, num_households)
    elif parameters.redistribution_type == "progressive_dividend":
        redistribution = compute_progressive_redistribution(
            total_revenue, income_deciles, parameters.income_weights
        )
    else:
        # No redistribution
        redistribution = pa.array([0.0] * num_households, type=pa.float64())

    total_redistribution = float(pc.sum(redistribution).as_py())

    # Compute net impact (redistribution - tax_burden)
    net_impact = pc.subtract(redistribution, tax_burden)

    return CarbonTaxResult(
        household_ids=household_ids,
        tax_burden=tax_burden,
        redistribution=redistribution,
        net_impact=net_impact,
        income_decile=income_deciles,
        total_revenue=total_revenue,
        total_redistribution=total_redistribution,
        year=year,
        template_name=template_name,
    )


def aggregate_by_decile(result: CarbonTaxResult) -> DecileResults:
    """Aggregate carbon tax results by income decile.

    Args:
        result: Per-household carbon tax computation result.

    Returns:
        DecileResults with mean and total metrics per decile.
    """
    decile_data: dict[int, dict[str, list[float]]] = {
        d: {"tax": [], "redist": [], "net": []} for d in range(1, 11)
    }

    deciles = result.income_decile.to_pylist()
    taxes = result.tax_burden.to_pylist()
    redists = result.redistribution.to_pylist()
    nets = result.net_impact.to_pylist()

    for i, decile in enumerate(deciles):
        decile_data[decile]["tax"].append(taxes[i])
        decile_data[decile]["redist"].append(redists[i])
        decile_data[decile]["net"].append(nets[i])

    decile_nums = []
    counts = []
    mean_taxes = []
    mean_redists = []
    mean_nets = []
    total_taxes = []
    total_redists = []
    total_nets = []

    for d in range(1, 11):
        data = decile_data[d]
        count = len(data["tax"])
        decile_nums.append(d)
        counts.append(count)

        if count > 0:
            mean_taxes.append(sum(data["tax"]) / count)
            mean_redists.append(sum(data["redist"]) / count)
            mean_nets.append(sum(data["net"]) / count)
            total_taxes.append(sum(data["tax"]))
            total_redists.append(sum(data["redist"]))
            total_nets.append(sum(data["net"]))
        else:
            mean_taxes.append(0.0)
            mean_redists.append(0.0)
            mean_nets.append(0.0)
            total_taxes.append(0.0)
            total_redists.append(0.0)
            total_nets.append(0.0)

    return DecileResults(
        decile=tuple(decile_nums),
        household_count=tuple(counts),
        mean_tax_burden=tuple(mean_taxes),
        mean_redistribution=tuple(mean_redists),
        mean_net_impact=tuple(mean_nets),
        total_tax_burden=tuple(total_taxes),
        total_redistribution=tuple(total_redists),
        total_net_impact=tuple(total_nets),
    )
