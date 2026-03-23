# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Feebate computation functions.

This module implements the core computation logic for feebate scenarios:
- Fee calculation for households above the pivot point
- Rebate calculation for households below the pivot point
- Net impact computation (rebate - fee)
- Income decile assignment for distributional analysis
- Result aggregation by decile
"""

from __future__ import annotations

from dataclasses import dataclass

import pyarrow as pa
import pyarrow.compute as pc

from reformlab.templates.carbon_tax.compute import assign_income_deciles
from reformlab.templates.schema import FeebateParameters


def _sum_array(values: pa.Array) -> float:
    """Return array sum as float, treating empty arrays as 0.0."""
    total = pc.sum(values).as_py()
    return 0.0 if total is None else float(total)


@dataclass(frozen=True)
class FeebateResult:
    """Result of feebate computation for a single scenario run.

    Contains per-household fee amounts, rebate amounts, net impact,
    and summary statistics.
    """

    household_ids: pa.Array
    fee_amount: pa.Array
    rebate_amount: pa.Array
    net_impact: pa.Array
    metric_value: pa.Array
    income_decile: pa.Array
    total_fees: float
    total_rebates: float
    net_fiscal_balance: float
    year: int
    template_name: str


@dataclass(frozen=True)
class FeebateDecileResults:
    """Per-decile aggregated feebate results.

    Contains mean and total metrics for each income decile (1-10).
    """

    decile: tuple[int, ...]
    household_count: tuple[int, ...]
    mean_fee: tuple[float, ...]
    mean_rebate: tuple[float, ...]
    mean_net_impact: tuple[float, ...]
    total_fee: tuple[float, ...]
    total_rebate: tuple[float, ...]
    total_net_impact: tuple[float, ...]


def compute_fee_amount(
    metric_value: float,
    pivot_point: float,
    fee_rate: float,
) -> float:
    """Compute fee amount for a household above the pivot point.

    Fee formula: (metric_value - pivot_point) * fee_rate

    Args:
        metric_value: Household's value on the pivot metric (e.g., vehicle emissions g/km).
        pivot_point: Threshold from template.
        fee_rate: EUR per unit above pivot.

    Returns:
        Fee amount (positive) or 0.0 if at or below pivot.
    """
    if metric_value <= pivot_point:
        return 0.0
    return (metric_value - pivot_point) * fee_rate


def compute_rebate_amount(
    metric_value: float,
    pivot_point: float,
    rebate_rate: float,
) -> float:
    """Compute rebate amount for a household below the pivot point.

    Rebate formula: (pivot_point - metric_value) * rebate_rate

    Args:
        metric_value: Household's value on the pivot metric.
        pivot_point: Threshold from template.
        rebate_rate: EUR per unit below pivot.

    Returns:
        Rebate amount (positive) or 0.0 if at or above pivot.
    """
    if metric_value >= pivot_point:
        return 0.0
    return (pivot_point - metric_value) * rebate_rate


def compute_feebate(
    population: pa.Table,
    policy: FeebateParameters,
    metric_column: str,
    year: int,
    template_name: str = "",
) -> FeebateResult:
    """Compute complete feebate results for a population.

    This is the main entry point for feebate computation. It:
    1. Reads metric values from the specified column
    2. Computes fee for households above pivot
    3. Computes rebate for households below pivot
    4. Calculates net impact per household
    5. Computes fiscal balance

    Args:
        population: Population table with household data including metric column.
        policy: Feebate parameters including pivot_point, fee_rate, rebate_rate.
        metric_column: Name of the column containing the metric for pivot comparison
            (e.g., "vehicle_emissions_gkm").
        year: Year for computation.
        template_name: Name of the template being executed.

    Returns:
        FeebateResult with all per-household and aggregate metrics.
    """
    # Get household IDs
    household_ids = population.column("household_id")
    num_households = population.num_rows

    # Assign income deciles
    incomes = population.column("income")
    income_deciles = assign_income_deciles(incomes)

    # Get metric values.
    # Missing/invalid values are treated as pivot-point (neutral impact).
    if metric_column in population.column_names:
        metric_col = population.column(metric_column)
        metric_values = []
        for value in metric_col:
            raw_value = value.as_py()
            if raw_value is None:
                metric_values.append(policy.pivot_point)
                continue
            try:
                metric_values.append(float(raw_value))
            except (TypeError, ValueError):
                metric_values.append(policy.pivot_point)
    else:
        # No metric column - treat as everyone at pivot (no fees or rebates)
        metric_values = [policy.pivot_point] * num_households

    # Compute fees and rebates
    fees = []
    rebates = []
    net_impacts = []

    for metric_val in metric_values:
        fee = compute_fee_amount(
            metric_val, policy.pivot_point, policy.fee_rate
        )
        rebate = compute_rebate_amount(
            metric_val, policy.pivot_point, policy.rebate_rate
        )
        fees.append(fee)
        rebates.append(rebate)
        net_impacts.append(rebate - fee)

    fee_array = pa.array(fees, type=pa.float64())
    rebate_array = pa.array(rebates, type=pa.float64())
    net_impact_array = pa.array(net_impacts, type=pa.float64())
    metric_array = pa.array(metric_values, type=pa.float64())

    total_fees = _sum_array(fee_array)
    total_rebates = _sum_array(rebate_array)
    net_fiscal_balance = total_fees - total_rebates

    return FeebateResult(
        household_ids=household_ids,
        fee_amount=fee_array,
        rebate_amount=rebate_array,
        net_impact=net_impact_array,
        metric_value=metric_array,
        income_decile=income_deciles,
        total_fees=total_fees,
        total_rebates=total_rebates,
        net_fiscal_balance=net_fiscal_balance,
        year=year,
        template_name=template_name,
    )


def aggregate_feebate_by_decile(result: FeebateResult) -> FeebateDecileResults:
    """Aggregate feebate results by income decile.

    Args:
        result: Per-household feebate computation result.

    Returns:
        FeebateDecileResults with mean and total metrics per decile.
    """
    decile_data: dict[int, dict[str, list[float]]] = {
        d: {"fee": [], "rebate": [], "net": []} for d in range(1, 11)
    }

    deciles = result.income_decile.to_pylist()
    fees = result.fee_amount.to_pylist()
    rebates = result.rebate_amount.to_pylist()
    nets = result.net_impact.to_pylist()

    for i, decile in enumerate(deciles):
        decile_data[decile]["fee"].append(fees[i])
        decile_data[decile]["rebate"].append(rebates[i])
        decile_data[decile]["net"].append(nets[i])

    decile_nums = []
    counts = []
    mean_fees = []
    mean_rebates = []
    mean_nets = []
    total_fees = []
    total_rebates = []
    total_nets = []

    for d in range(1, 11):
        data = decile_data[d]
        count = len(data["fee"])
        decile_nums.append(d)
        counts.append(count)

        if count > 0:
            mean_fees.append(sum(data["fee"]) / count)
            mean_rebates.append(sum(data["rebate"]) / count)
            mean_nets.append(sum(data["net"]) / count)
            total_fees.append(sum(data["fee"]))
            total_rebates.append(sum(data["rebate"]))
            total_nets.append(sum(data["net"]))
        else:
            mean_fees.append(0.0)
            mean_rebates.append(0.0)
            mean_nets.append(0.0)
            total_fees.append(0.0)
            total_rebates.append(0.0)
            total_nets.append(0.0)

    return FeebateDecileResults(
        decile=tuple(decile_nums),
        household_count=tuple(counts),
        mean_fee=tuple(mean_fees),
        mean_rebate=tuple(mean_rebates),
        mean_net_impact=tuple(mean_nets),
        total_fee=tuple(total_fees),
        total_rebate=tuple(total_rebates),
        total_net_impact=tuple(total_nets),
    )
