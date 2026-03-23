# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Rebate batch execution and comparison utilities.

This module provides functions to run multiple rebate scenarios in batch
and compare their distributional impacts by income decile.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pyarrow as pa

from reformlab.templates.rebate.compute import (
    RebateDecileResults,
    RebateResult,
    aggregate_rebate_by_decile,
    compute_rebate,
)

if TYPE_CHECKING:
    from reformlab.templates.schema import BaselineScenario


@dataclass(frozen=True)
class ComparisonResult:
    """Comparison of multiple rebate scenarios by decile.

    Contains per-scenario decile results and a wide-format comparison table.
    """

    scenarios: tuple[str, ...]
    decile_results: dict[str, RebateDecileResults]
    comparison_table: pa.Table


def run_rebate_batch(
    population: pa.Table,
    scenarios: list[BaselineScenario],
    rebate_pools: dict[str, float],
    year: int,
) -> dict[str, RebateResult]:
    """Run multiple rebate scenarios on the same population.

    Args:
        population: Population table with household data.
        scenarios: List of baseline scenarios to run.
        rebate_pools: Dict mapping scenario name to rebate pool amount.
        year: Year for computation.

    Returns:
        Dict mapping scenario name to RebateResult.

    Example:
        >>> from reformlab.templates.packs import load_rebate_template
        >>> templates = ["rebate-progressive-income"]
        >>> scenarios = [load_rebate_template(t) for t in templates]
        >>> pools = {s.name: 1_000_000 for s in scenarios}
        >>> results = run_rebate_batch(population, scenarios, pools, 2026)
    """
    from reformlab.templates.schema import RebateParameters

    results = {}
    for scenario in scenarios:
        if not isinstance(scenario.policy, RebateParameters):
            raise TypeError(
                f"Scenario '{scenario.name}' does not have RebateParameters"
            )

        rebate_pool = rebate_pools.get(scenario.name, 0.0)

        result = compute_rebate(
            population=population,
            policy=scenario.policy,
            rebate_pool=rebate_pool,
            year=year,
            template_name=scenario.name,
        )
        results[scenario.name] = result

    return results


def compare_rebate_decile_impacts(
    results: dict[str, RebateResult],
) -> ComparisonResult:
    """Compare rebate results across scenarios by income decile.

    Args:
        results: Dict mapping scenario name to RebateResult.

    Returns:
        ComparisonResult with per-scenario decile metrics and comparison table.

    Example:
        >>> comparison = compare_rebate_decile_impacts(results)
        >>> print(comparison.comparison_table.to_pandas())
    """
    scenario_names = tuple(results.keys())
    decile_results_map = {}

    # Aggregate each scenario by decile
    for name, result in results.items():
        decile_results_map[name] = aggregate_rebate_by_decile(result)

    # Build comparison table (wide format)
    columns: dict[str, list[object]] = {"decile": list(range(1, 11))}

    for name in scenario_names:
        decile_res = decile_results_map[name]
        # Clean name for column prefix
        prefix = name.replace(" ", "_").replace("-", "_").replace(",", "")

        columns[f"{prefix}_mean_rebate"] = list(decile_res.mean_rebate)
        columns[f"{prefix}_total_rebate"] = list(decile_res.total_rebate)
        columns[f"{prefix}_household_count"] = list(decile_res.household_count)

    comparison_table = pa.table(columns)

    return ComparisonResult(
        scenarios=scenario_names,
        decile_results=decile_results_map,
        comparison_table=comparison_table,
    )


def rebate_decile_results_to_table(decile_results: RebateDecileResults) -> pa.Table:
    """Convert RebateDecileResults to a PyArrow table.

    Args:
        decile_results: Aggregated decile results.

    Returns:
        PyArrow table with columns for each metric.
    """
    return pa.table(
        {
            "decile": list(decile_results.decile),
            "household_count": list(decile_results.household_count),
            "mean_rebate": list(decile_results.mean_rebate),
            "total_rebate": list(decile_results.total_rebate),
        }
    )


__all__ = [
    "ComparisonResult",
    "compare_rebate_decile_impacts",
    "rebate_decile_results_to_table",
    "run_rebate_batch",
]
