"""Vehicle malus batch execution and comparison utilities.

This module provides functions to run multiple vehicle malus scenarios in batch
and compare their distributional impacts by income decile.

Story 13.2 — Follows the feebate/compare.py pattern.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pyarrow as pa

from reformlab.templates.vehicle_malus.compute import (
    VehicleMalusDecileResults,
    VehicleMalusResult,
    aggregate_vehicle_malus_by_decile,
    compute_vehicle_malus,
)

if TYPE_CHECKING:
    from reformlab.templates.schema import BaselineScenario


@dataclass(frozen=True)
class ComparisonResult:
    """Comparison of multiple vehicle malus scenarios by decile.

    Contains per-scenario decile results and a wide-format comparison table.
    """

    scenarios: tuple[str, ...]
    decile_results: dict[str, VehicleMalusDecileResults]
    comparison_table: pa.Table


def run_vehicle_malus_batch(
    population: pa.Table,
    scenarios: list[BaselineScenario],
    year: int,
) -> dict[str, VehicleMalusResult]:
    """Run multiple vehicle malus scenarios on the same population.

    Args:
        population: Population table with household data.
        scenarios: List of baseline scenarios to run.
        year: Year for computation.

    Returns:
        Dict mapping scenario name to VehicleMalusResult.

    Raises:
        TypeError: If a scenario does not have VehicleMalusParameters policy.
    """
    from reformlab.templates.vehicle_malus.compute import VehicleMalusParameters

    results: dict[str, VehicleMalusResult] = {}
    for scenario in scenarios:
        if not isinstance(scenario.policy, VehicleMalusParameters):
            raise TypeError(
                f"Scenario '{scenario.name}' does not have VehicleMalusParameters"
            )

        result = compute_vehicle_malus(
            population=population,
            policy=scenario.policy,
            year=year,
            template_name=scenario.name,
        )
        results[scenario.name] = result

    return results


def compare_vehicle_malus_decile_impacts(
    results: dict[str, VehicleMalusResult],
) -> ComparisonResult:
    """Compare vehicle malus results across scenarios by income decile.

    Args:
        results: Dict mapping scenario name to VehicleMalusResult.

    Returns:
        ComparisonResult with per-scenario decile metrics and comparison table.
    """
    scenario_names = tuple(results.keys())
    decile_results_map: dict[str, VehicleMalusDecileResults] = {}

    for name, result in results.items():
        decile_results_map[name] = aggregate_vehicle_malus_by_decile(result)

    # Build comparison table (wide format)
    columns: dict[str, list[object]] = {"decile": list(range(1, 11))}

    for name in scenario_names:
        decile_res = decile_results_map[name]
        prefix = name.replace(" ", "_").replace("-", "_").replace(",", "")

        columns[f"{prefix}_mean_malus"] = list(decile_res.mean_malus)
        columns[f"{prefix}_total_malus"] = list(decile_res.total_malus)
        columns[f"{prefix}_household_count"] = list(decile_res.household_count)

    comparison_table = pa.table(columns)

    return ComparisonResult(
        scenarios=scenario_names,
        decile_results=decile_results_map,
        comparison_table=comparison_table,
    )


def vehicle_malus_decile_results_to_table(
    decile_results: VehicleMalusDecileResults,
) -> pa.Table:
    """Convert VehicleMalusDecileResults to a PyArrow table.

    Args:
        decile_results: Aggregated decile results.

    Returns:
        PyArrow table with columns for each metric.
    """
    return pa.table(
        {
            "decile": list(decile_results.decile),
            "household_count": list(decile_results.household_count),
            "mean_malus": list(decile_results.mean_malus),
            "total_malus": list(decile_results.total_malus),
        }
    )


__all__ = [
    "ComparisonResult",
    "compare_vehicle_malus_decile_impacts",
    "run_vehicle_malus_batch",
    "vehicle_malus_decile_results_to_table",
]
