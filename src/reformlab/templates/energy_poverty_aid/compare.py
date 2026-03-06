"""Energy poverty aid batch execution and comparison utilities.

This module provides functions to run multiple energy poverty aid scenarios
in batch and compare their distributional impacts by income decile.

Story 13.3 — Follows the vehicle_malus/compare.py pattern.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pyarrow as pa

from reformlab.templates.energy_poverty_aid.compute import (
    EnergyPovertyAidDecileResults,
    EnergyPovertyAidResult,
    aggregate_energy_poverty_aid_by_decile,
    compute_energy_poverty_aid,
)

if TYPE_CHECKING:
    from reformlab.templates.schema import BaselineScenario


@dataclass(frozen=True)
class ComparisonResult:
    """Comparison of multiple energy poverty aid scenarios by decile.

    Contains per-scenario decile results and a wide-format comparison table.
    """

    scenarios: tuple[str, ...]
    decile_results: dict[str, EnergyPovertyAidDecileResults]
    comparison_table: pa.Table


def run_energy_poverty_aid_batch(
    population: pa.Table,
    scenarios: list[BaselineScenario],
    year: int,
) -> dict[str, EnergyPovertyAidResult]:
    """Run multiple energy poverty aid scenarios on the same population.

    Args:
        population: Population table with household data.
        scenarios: List of baseline scenarios to run.
        year: Year for computation.

    Returns:
        Dict mapping scenario name to EnergyPovertyAidResult.

    Raises:
        TypeError: If a scenario does not have EnergyPovertyAidParameters policy.
        ValueError: If duplicate scenario names are provided.
    """
    from reformlab.templates.energy_poverty_aid.compute import (
        EnergyPovertyAidParameters,
    )

    # Detect duplicate scenario names
    names = [s.name for s in scenarios]
    seen: set[str] = set()
    for name in names:
        if name in seen:
            raise ValueError(
                f"Duplicate scenario name '{name}' in batch — "
                f"scenario names must be unique"
            )
        seen.add(name)

    results: dict[str, EnergyPovertyAidResult] = {}
    for scenario in scenarios:
        if not isinstance(scenario.policy, EnergyPovertyAidParameters):
            raise TypeError(
                f"Scenario '{scenario.name}' does not have "
                f"EnergyPovertyAidParameters"
            )

        result = compute_energy_poverty_aid(
            population=population,
            policy=scenario.policy,
            year=year,
            template_name=scenario.name,
        )
        results[scenario.name] = result

    return results


def compare_energy_poverty_aid_decile_impacts(
    results: dict[str, EnergyPovertyAidResult],
) -> ComparisonResult:
    """Compare energy poverty aid results across scenarios by income decile.

    Args:
        results: Dict mapping scenario name to EnergyPovertyAidResult.

    Returns:
        ComparisonResult with per-scenario decile metrics and comparison table.
    """
    scenario_names = tuple(results.keys())
    decile_results_map: dict[str, EnergyPovertyAidDecileResults] = {}

    for name, result in results.items():
        decile_results_map[name] = aggregate_energy_poverty_aid_by_decile(result)

    # Build comparison table (wide format)
    columns: dict[str, list[object]] = {"decile": list(range(1, 11))}

    for name in scenario_names:
        decile_res = decile_results_map[name]
        prefix = name.replace(" ", "_").replace("-", "_").replace(",", "")

        columns[f"{prefix}_mean_aid"] = list(decile_res.mean_aid)
        columns[f"{prefix}_total_aid"] = list(decile_res.total_aid)
        columns[f"{prefix}_household_count"] = list(decile_res.household_count)
        columns[f"{prefix}_eligible_count"] = list(decile_res.eligible_count)

    comparison_table = pa.table(columns)

    return ComparisonResult(
        scenarios=scenario_names,
        decile_results=decile_results_map,
        comparison_table=comparison_table,
    )


def energy_poverty_aid_decile_results_to_table(
    decile_results: EnergyPovertyAidDecileResults,
) -> pa.Table:
    """Convert EnergyPovertyAidDecileResults to a PyArrow table.

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
            "mean_aid": list(decile_results.mean_aid),
            "total_aid": list(decile_results.total_aid),
        }
    )


__all__ = [
    "ComparisonResult",
    "compare_energy_poverty_aid_decile_impacts",
    "energy_poverty_aid_decile_results_to_table",
    "run_energy_poverty_aid_batch",
]
