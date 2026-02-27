"""Rebate computation functions.

This module implements the core computation logic for rebate scenarios:
- Lump sum rebate (equal per-capita distribution)
- Progressive rebate (income-weighted distribution)
- Income decile assignment for distributional analysis
- Result aggregation by decile
"""

from __future__ import annotations

from dataclasses import dataclass

import pyarrow as pa
import pyarrow.compute as pc

from reformlab.templates.carbon_tax.compute import assign_income_deciles
from reformlab.templates.schema import RebateParameters


def _sum_array(values: pa.Array) -> float:
    """Return array sum as float, treating empty arrays as 0.0."""
    total = pc.sum(values).as_py()
    return 0.0 if total is None else float(total)


@dataclass(frozen=True)
class RebateResult:
    """Result of rebate computation for a single scenario run.

    Contains per-household rebate amounts and summary statistics.
    """

    household_ids: pa.Array
    rebate_amount: pa.Array
    income_decile: pa.Array
    total_distributed: float
    year: int
    template_name: str


@dataclass(frozen=True)
class RebateDecileResults:
    """Per-decile aggregated rebate results.

    Contains mean and total metrics for each income decile (1-10).
    """

    decile: tuple[int, ...]
    household_count: tuple[int, ...]
    mean_rebate: tuple[float, ...]
    total_rebate: tuple[float, ...]


def compute_lump_sum_rebate(
    rebate_pool: float,
    num_households: int,
) -> pa.Array:
    """Compute lump sum rebate (equal per-capita distribution).

    Args:
        rebate_pool: Total amount to distribute.
        num_households: Number of households to distribute to.

    Returns:
        Array of rebate amounts per household (all equal).
    """
    if num_households == 0:
        return pa.array([], type=pa.float64())

    per_household = rebate_pool / num_households
    return pa.array([per_household] * num_households, type=pa.float64())


def compute_progressive_rebate(
    rebate_pool: float,
    deciles: pa.Array,
    income_weights: dict[str, float],
) -> pa.Array:
    """Compute progressive rebate based on income decile weights.

    Lower income deciles receive higher rebate amounts based on
    the income_weights mapping (higher weight = higher rebate).

    Formula:
    weighted_population = Σ (income_weight[decile] × count[decile])
    rebate_household = (income_weight[household_decile] × rebate_pool) / weighted_population

    Args:
        rebate_pool: Total amount to distribute.
        deciles: Array of decile assignments (1-10) for each household.
        income_weights: Mapping of decile names to weight multipliers.

    Returns:
        Array of rebate amounts per household.
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
        return compute_lump_sum_rebate(rebate_pool, n)

    # Calculate rebate per household based on their decile
    rebates = []
    for decile in decile_list:
        weight_key = f"decile_{decile}"
        weight = income_weights.get(weight_key, 1.0)
        household_share = (weight * rebate_pool) / weighted_sum
        rebates.append(household_share)

    return pa.array(rebates, type=pa.float64())


def compute_rebate(
    population: pa.Table,
    parameters: RebateParameters,
    rebate_pool: float,
    year: int,
    template_name: str = "",
) -> RebateResult:
    """Compute complete rebate results for a population.

    This is the main entry point for rebate computation. It:
    1. Assigns income deciles
    2. Computes rebate amount per household based on rebate_type
    3. Calculates total distributed

    Args:
        population: Population table with household data.
        parameters: Rebate parameters including rebate_type and income_weights.
        rebate_pool: Total amount to distribute (can come from rate_schedule[year]
            multiplied by number of households, or from external source like tax revenue).
        year: Year for computation.
        template_name: Name of the template being executed.

    Returns:
        RebateResult with all per-household and aggregate metrics.
    """
    # Get household IDs
    household_ids = population.column("household_id")
    num_households = population.num_rows

    # Assign income deciles
    incomes = population.column("income")
    income_deciles = assign_income_deciles(incomes)

    # Compute rebate based on type
    if parameters.rebate_type in ("", "lump_sum"):
        rebate_amounts = compute_lump_sum_rebate(rebate_pool, num_households)
    elif parameters.rebate_type == "progressive_dividend":
        rebate_amounts = compute_progressive_rebate(
            rebate_pool, income_deciles, parameters.income_weights
        )
    else:
        raise ValueError(
            "Unsupported rebate_type "
            f"'{parameters.rebate_type}'. Supported values: '', "
            "'lump_sum', 'progressive_dividend'."
        )

    total_distributed = _sum_array(rebate_amounts)

    return RebateResult(
        household_ids=household_ids,
        rebate_amount=rebate_amounts,
        income_decile=income_deciles,
        total_distributed=total_distributed,
        year=year,
        template_name=template_name,
    )


def aggregate_rebate_by_decile(result: RebateResult) -> RebateDecileResults:
    """Aggregate rebate results by income decile.

    Args:
        result: Per-household rebate computation result.

    Returns:
        RebateDecileResults with mean and total metrics per decile.
    """
    decile_data: dict[int, list[float]] = {d: [] for d in range(1, 11)}

    deciles = result.income_decile.to_pylist()
    amounts = result.rebate_amount.to_pylist()

    for i, decile in enumerate(deciles):
        decile_data[decile].append(amounts[i])

    decile_nums = []
    counts = []
    mean_rebates = []
    total_rebates = []

    for d in range(1, 11):
        data = decile_data[d]
        count = len(data)
        decile_nums.append(d)
        counts.append(count)

        if count > 0:
            mean_rebates.append(sum(data) / count)
            total_rebates.append(sum(data))
        else:
            mean_rebates.append(0.0)
            total_rebates.append(0.0)

    return RebateDecileResults(
        decile=tuple(decile_nums),
        household_count=tuple(counts),
        mean_rebate=tuple(mean_rebates),
        total_rebate=tuple(total_rebates),
    )
