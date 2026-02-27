"""Subsidy computation functions.

This module implements the core computation logic for subsidy scenarios:
- Eligibility checking based on income caps and eligible categories
- Subsidy amount calculation per household
- Income decile assignment for distributional analysis
- Result aggregation by decile
"""

from __future__ import annotations

from dataclasses import dataclass

import pyarrow as pa
import pyarrow.compute as pc

from reformlab.templates.carbon_tax.compute import assign_income_deciles
from reformlab.templates.schema import SubsidyParameters


def _sum_array(values: pa.Array) -> float:
    """Return array sum as float, treating empty arrays as 0.0."""
    total = pc.sum(values).as_py()
    return 0.0 if total is None else float(total)


@dataclass(frozen=True)
class SubsidyResult:
    """Result of subsidy computation for a single scenario run.

    Contains per-household subsidy amounts, eligibility status, and
    summary statistics.
    """

    household_ids: pa.Array
    subsidy_amount: pa.Array
    is_eligible: pa.Array
    income_decile: pa.Array
    total_cost: float
    year: int
    template_name: str


@dataclass(frozen=True)
class SubsidyDecileResults:
    """Per-decile aggregated subsidy results.

    Contains mean and total metrics for each income decile (1-10).
    """

    decile: tuple[int, ...]
    household_count: tuple[int, ...]
    eligible_count: tuple[int, ...]
    mean_subsidy: tuple[float, ...]
    total_subsidy: tuple[float, ...]


def compute_subsidy_eligibility(
    population: pa.Table,
    parameters: SubsidyParameters,
    year: int,
) -> pa.Array:
    """Compute subsidy eligibility for each household.

    A household is eligible if:
    1. Their income is at or below the income_cap for the year (if income_caps specified)
    2. They have at least one characteristic in eligible_categories (if specified)

    Args:
        population: Population table with household data.
        parameters: Subsidy parameters including income_caps and eligible_categories.
        year: Year for which to compute eligibility (determines income cap).

    Returns:
        Boolean array indicating eligibility for each household.
    """
    num_households = population.num_rows
    if num_households == 0:
        return pa.array([], type=pa.bool_())

    # Start with all eligible
    eligible = [True] * num_households

    # Apply income cap if specified for this year
    income_cap = parameters.income_caps.get(year)
    if income_cap is not None:
        incomes = population.column("income")
        for i in range(num_households):
            income_val = incomes[i].as_py()
            if income_val is None or income_val > income_cap:
                eligible[i] = False

    # Apply category eligibility if specified
    if parameters.eligible_categories:
        category_columns = [
            population.column(category)
            for category in parameters.eligible_categories
            if category in population.column_names
        ]
        # If template requires categories but none are available in data,
        # households cannot satisfy category eligibility.
        if not category_columns:
            return pa.array([False] * num_households, type=pa.bool_())

        # A household is eligible if they have a truthy value in any eligible category column.
        for i in range(num_households):
            if not eligible[i]:
                continue  # Already ineligible

            has_category = any(bool(category_col[i].as_py()) for category_col in category_columns)
            if not has_category:
                eligible[i] = False

    return pa.array(eligible, type=pa.bool_())


def compute_subsidy_amount(
    population: pa.Table,
    parameters: SubsidyParameters,
    eligibility: pa.Array,
    year: int,
) -> pa.Array:
    """Compute subsidy amount for each household.

    Eligible households receive the subsidy amount from rate_schedule[year].
    Ineligible households receive 0.

    Args:
        population: Population table with household data.
        parameters: Subsidy parameters including rate_schedule.
        eligibility: Boolean array of eligibility per household.
        year: Year for which to compute subsidy amount.

    Returns:
        Array of subsidy amounts in EUR per household.
    """
    num_households = population.num_rows
    if num_households == 0:
        return pa.array([], type=pa.float64())
    if len(eligibility) != num_households:
        raise ValueError(
            "eligibility mask length must equal population size "
            f"({len(eligibility)} != {num_households})"
        )

    # Get subsidy amount for this year (default 0 if not specified)
    subsidy_rate = parameters.rate_schedule.get(year, 0.0)

    eligibility_list = eligibility.to_pylist()
    amounts = []
    for is_eligible in eligibility_list:
        if is_eligible:
            amounts.append(subsidy_rate)
        else:
            amounts.append(0.0)

    return pa.array(amounts, type=pa.float64())


def compute_subsidy(
    population: pa.Table,
    parameters: SubsidyParameters,
    year: int,
    template_name: str = "",
) -> SubsidyResult:
    """Compute complete subsidy results for a population.

    This is the main entry point for subsidy computation. It:
    1. Computes eligibility per household
    2. Assigns income deciles
    3. Computes subsidy amount per household
    4. Calculates total cost

    Args:
        population: Population table with household data.
        parameters: Subsidy parameters.
        year: Year for computation.
        template_name: Name of the template being executed.

    Returns:
        SubsidyResult with all per-household and aggregate metrics.
    """
    # Get household IDs
    household_ids = population.column("household_id")

    # Compute eligibility
    eligibility = compute_subsidy_eligibility(population, parameters, year)

    # Assign income deciles
    incomes = population.column("income")
    income_deciles = assign_income_deciles(incomes)

    # Compute subsidy amounts
    subsidy_amounts = compute_subsidy_amount(population, parameters, eligibility, year)

    # Calculate total cost
    total_cost = _sum_array(subsidy_amounts)

    return SubsidyResult(
        household_ids=household_ids,
        subsidy_amount=subsidy_amounts,
        is_eligible=eligibility,
        income_decile=income_deciles,
        total_cost=total_cost,
        year=year,
        template_name=template_name,
    )


def aggregate_subsidy_by_decile(result: SubsidyResult) -> SubsidyDecileResults:
    """Aggregate subsidy results by income decile.

    Args:
        result: Per-household subsidy computation result.

    Returns:
        SubsidyDecileResults with mean and total metrics per decile.
    """
    decile_data: dict[int, dict[str, list[float]]] = {
        d: {"subsidy": [], "eligible": []} for d in range(1, 11)
    }

    deciles = result.income_decile.to_pylist()
    amounts = result.subsidy_amount.to_pylist()
    eligibles = result.is_eligible.to_pylist()

    for i, decile in enumerate(deciles):
        decile_data[decile]["subsidy"].append(amounts[i])
        decile_data[decile]["eligible"].append(1.0 if eligibles[i] else 0.0)

    decile_nums = []
    counts = []
    eligible_counts = []
    mean_subsidies = []
    total_subsidies = []

    for d in range(1, 11):
        data = decile_data[d]
        count = len(data["subsidy"])
        decile_nums.append(d)
        counts.append(count)

        if count > 0:
            eligible_counts.append(int(sum(data["eligible"])))
            mean_subsidies.append(sum(data["subsidy"]) / count)
            total_subsidies.append(sum(data["subsidy"]))
        else:
            eligible_counts.append(0)
            mean_subsidies.append(0.0)
            total_subsidies.append(0.0)

    return SubsidyDecileResults(
        decile=tuple(decile_nums),
        household_count=tuple(counts),
        eligible_count=tuple(eligible_counts),
        mean_subsidy=tuple(mean_subsidies),
        total_subsidy=tuple(total_subsidies),
    )
