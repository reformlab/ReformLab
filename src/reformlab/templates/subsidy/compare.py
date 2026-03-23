# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Subsidy batch execution and comparison utilities.

This module provides functions to run multiple subsidy scenarios in batch
and compare their distributional impacts by income decile.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pyarrow as pa

from reformlab.templates.subsidy.compute import (
    SubsidyDecileResults,
    SubsidyResult,
    aggregate_subsidy_by_decile,
    compute_subsidy,
)

if TYPE_CHECKING:
    from reformlab.templates.schema import BaselineScenario


@dataclass(frozen=True)
class ComparisonResult:
    """Comparison of multiple subsidy scenarios by decile.

    Contains per-scenario decile results and a wide-format comparison table.
    """

    scenarios: tuple[str, ...]
    decile_results: dict[str, SubsidyDecileResults]
    comparison_table: pa.Table


def run_subsidy_batch(
    population: pa.Table,
    scenarios: list[BaselineScenario],
    year: int,
) -> dict[str, SubsidyResult]:
    """Run multiple subsidy scenarios on the same population.

    Args:
        population: Population table with household data.
        scenarios: List of baseline scenarios to run.
        year: Year for computation.

    Returns:
        Dict mapping scenario name to SubsidyResult.

    Example:
        >>> from reformlab.templates.packs import load_subsidy_template
        >>> templates = ["subsidy-energy-retrofit"]
        >>> scenarios = [load_subsidy_template(t) for t in templates]
        >>> results = run_subsidy_batch(population, scenarios, 2026)
    """
    from reformlab.templates.schema import SubsidyParameters

    results = {}
    for scenario in scenarios:
        if not isinstance(scenario.policy, SubsidyParameters):
            raise TypeError(
                f"Scenario '{scenario.name}' does not have SubsidyParameters"
            )

        result = compute_subsidy(
            population=population,
            policy=scenario.policy,
            year=year,
            template_name=scenario.name,
        )
        results[scenario.name] = result

    return results


def compare_subsidy_decile_impacts(
    results: dict[str, SubsidyResult],
) -> ComparisonResult:
    """Compare subsidy results across scenarios by income decile.

    Args:
        results: Dict mapping scenario name to SubsidyResult.

    Returns:
        ComparisonResult with per-scenario decile metrics and comparison table.

    Example:
        >>> comparison = compare_subsidy_decile_impacts(results)
        >>> print(comparison.comparison_table.to_pandas())
    """
    scenario_names = tuple(results.keys())
    decile_results_map = {}

    # Aggregate each scenario by decile
    for name, result in results.items():
        decile_results_map[name] = aggregate_subsidy_by_decile(result)

    # Build comparison table (wide format)
    columns: dict[str, list[object]] = {"decile": list(range(1, 11))}

    for name in scenario_names:
        decile_res = decile_results_map[name]
        # Clean name for column prefix
        prefix = name.replace(" ", "_").replace("-", "_").replace(",", "")

        columns[f"{prefix}_mean_subsidy"] = list(decile_res.mean_subsidy)
        columns[f"{prefix}_total_subsidy"] = list(decile_res.total_subsidy)
        columns[f"{prefix}_eligible_count"] = list(decile_res.eligible_count)
        columns[f"{prefix}_household_count"] = list(decile_res.household_count)

    comparison_table = pa.table(columns)

    return ComparisonResult(
        scenarios=scenario_names,
        decile_results=decile_results_map,
        comparison_table=comparison_table,
    )


def subsidy_decile_results_to_table(decile_results: SubsidyDecileResults) -> pa.Table:
    """Convert SubsidyDecileResults to a PyArrow table.

    Args:
        decile_results: Aggregated decile results.

    Returns:
        PyArrow table with columns for each metric.
    """
    return pa.table(
        {
            "decile": list(decile_results.decile),
            "household_count": list(decile_results.household_count),
            "eligible_count": list(decile_results.eligible_count),
            "mean_subsidy": list(decile_results.mean_subsidy),
            "total_subsidy": list(decile_results.total_subsidy),
        }
    )


__all__ = [
    "ComparisonResult",
    "compare_subsidy_decile_impacts",
    "run_subsidy_batch",
    "subsidy_decile_results_to_table",
]
