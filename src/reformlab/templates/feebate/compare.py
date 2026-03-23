# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Feebate batch execution and comparison utilities.

This module provides functions to run multiple feebate scenarios in batch
and compare their distributional impacts by income decile.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pyarrow as pa

from reformlab.templates.feebate.compute import (
    FeebateDecileResults,
    FeebateResult,
    aggregate_feebate_by_decile,
    compute_feebate,
)

if TYPE_CHECKING:
    from reformlab.templates.schema import BaselineScenario


@dataclass(frozen=True)
class ComparisonResult:
    """Comparison of multiple feebate scenarios by decile.

    Contains per-scenario decile results and a wide-format comparison table.
    """

    scenarios: tuple[str, ...]
    decile_results: dict[str, FeebateDecileResults]
    comparison_table: pa.Table


def run_feebate_batch(
    population: pa.Table,
    scenarios: list[BaselineScenario],
    metric_column: str,
    year: int,
) -> dict[str, FeebateResult]:
    """Run multiple feebate scenarios on the same population.

    Args:
        population: Population table with household data and metric column.
        scenarios: List of baseline scenarios to run.
        metric_column: Name of the column containing the metric for pivot comparison.
        year: Year for computation.

    Returns:
        Dict mapping scenario name to FeebateResult.

    Example:
        >>> from reformlab.templates.packs import load_feebate_template
        >>> templates = ["feebate-vehicle-emissions"]
        >>> scenarios = [load_feebate_template(t) for t in templates]
        >>> results = run_feebate_batch(population, scenarios, "vehicle_emissions_gkm", 2026)
    """
    from reformlab.templates.schema import FeebateParameters

    results = {}
    for scenario in scenarios:
        if not isinstance(scenario.policy, FeebateParameters):
            raise TypeError(
                f"Scenario '{scenario.name}' does not have FeebateParameters"
            )

        result = compute_feebate(
            population=population,
            policy=scenario.policy,
            metric_column=metric_column,
            year=year,
            template_name=scenario.name,
        )
        results[scenario.name] = result

    return results


def compare_feebate_decile_impacts(
    results: dict[str, FeebateResult],
) -> ComparisonResult:
    """Compare feebate results across scenarios by income decile.

    Args:
        results: Dict mapping scenario name to FeebateResult.

    Returns:
        ComparisonResult with per-scenario decile metrics and comparison table.

    Example:
        >>> comparison = compare_feebate_decile_impacts(results)
        >>> print(comparison.comparison_table.to_pandas())
    """
    scenario_names = tuple(results.keys())
    decile_results_map = {}

    # Aggregate each scenario by decile
    for name, result in results.items():
        decile_results_map[name] = aggregate_feebate_by_decile(result)

    # Build comparison table (wide format)
    columns: dict[str, list[object]] = {"decile": list(range(1, 11))}

    for name in scenario_names:
        decile_res = decile_results_map[name]
        # Clean name for column prefix
        prefix = name.replace(" ", "_").replace("-", "_").replace(",", "")

        columns[f"{prefix}_mean_fee"] = list(decile_res.mean_fee)
        columns[f"{prefix}_mean_rebate"] = list(decile_res.mean_rebate)
        columns[f"{prefix}_mean_net_impact"] = list(decile_res.mean_net_impact)
        columns[f"{prefix}_household_count"] = list(decile_res.household_count)

    comparison_table = pa.table(columns)

    return ComparisonResult(
        scenarios=scenario_names,
        decile_results=decile_results_map,
        comparison_table=comparison_table,
    )


def feebate_decile_results_to_table(decile_results: FeebateDecileResults) -> pa.Table:
    """Convert FeebateDecileResults to a PyArrow table.

    Args:
        decile_results: Aggregated decile results.

    Returns:
        PyArrow table with columns for each metric.
    """
    return pa.table(
        {
            "decile": list(decile_results.decile),
            "household_count": list(decile_results.household_count),
            "mean_fee": list(decile_results.mean_fee),
            "mean_rebate": list(decile_results.mean_rebate),
            "mean_net_impact": list(decile_results.mean_net_impact),
            "total_fee": list(decile_results.total_fee),
            "total_rebate": list(decile_results.total_rebate),
            "total_net_impact": list(decile_results.total_net_impact),
        }
    )


__all__ = [
    "ComparisonResult",
    "compare_feebate_decile_impacts",
    "feebate_decile_results_to_table",
    "run_feebate_batch",
]
