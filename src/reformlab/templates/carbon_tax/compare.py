"""Carbon tax batch execution and comparison utilities.

This module provides functions to run multiple carbon tax scenarios in batch
and compare their distributional impacts by income decile.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pyarrow as pa

from reformlab.templates.carbon_tax.compute import (
    CarbonTaxResult,
    DecileResults,
    aggregate_by_decile,
    compute_carbon_tax,
)

if TYPE_CHECKING:
    from reformlab.data.emission_factors import EmissionFactorIndex
    from reformlab.templates.schema import BaselineScenario


@dataclass(frozen=True)
class ComparisonResult:
    """Comparison of multiple carbon tax scenarios by decile.

    Contains per-scenario decile results and a wide-format comparison table.
    """

    scenarios: tuple[str, ...]
    decile_results: dict[str, DecileResults]
    comparison_table: pa.Table


def run_carbon_tax_batch(
    population: pa.Table,
    scenarios: list[BaselineScenario],
    emission_index: EmissionFactorIndex,
    year: int,
) -> dict[str, CarbonTaxResult]:
    """Run multiple carbon tax scenarios on the same population.

    Args:
        population: Population table with household data and energy columns.
        scenarios: List of baseline scenarios to run.
        emission_index: Emission factor index for tax computation.
        year: Year for computation.

    Returns:
        Dict mapping scenario name to CarbonTaxResult.

    Example:
        >>> from reformlab.templates.packs import load_carbon_tax_template
        >>> templates = ["carbon-tax-flat-no-redistribution", "carbon-tax-flat-lump-sum-dividend"]
        >>> scenarios = [load_carbon_tax_template(t) for t in templates]
        >>> results = run_carbon_tax_batch(population, scenarios, emission_index, 2026)
    """
    results = {}
    for scenario in scenarios:
        # Extract parameters (must be CarbonTaxParameters for carbon_tax policy type)
        from reformlab.templates.schema import CarbonTaxParameters

        if not isinstance(scenario.parameters, CarbonTaxParameters):
            raise TypeError(
                f"Scenario '{scenario.name}' does not have CarbonTaxParameters"
            )

        result = compute_carbon_tax(
            population=population,
            parameters=scenario.parameters,
            emission_index=emission_index,
            year=year,
            template_name=scenario.name,
        )
        results[scenario.name] = result

    return results


def compare_decile_impacts(
    results: dict[str, CarbonTaxResult],
) -> ComparisonResult:
    """Compare carbon tax results across scenarios by income decile.

    Args:
        results: Dict mapping scenario name to CarbonTaxResult.

    Returns:
        ComparisonResult with per-scenario decile metrics and comparison table.

    Example:
        >>> comparison = compare_decile_impacts(results)
        >>> print(comparison.comparison_table.to_pandas())
    """
    scenario_names = tuple(results.keys())
    decile_results_map = {}

    # Aggregate each scenario by decile
    for name, result in results.items():
        decile_results_map[name] = aggregate_by_decile(result)

    # Build comparison table (wide format)
    # Columns: decile, scenario1_mean_tax, scenario1_mean_redist, scenario1_mean_net, ...
    columns: dict[str, list[object]] = {"decile": list(range(1, 11))}

    for name in scenario_names:
        decile_res = decile_results_map[name]
        # Clean name for column prefix (replace spaces/special chars)
        prefix = name.replace(" ", "_").replace("-", "_").replace(",", "")

        columns[f"{prefix}_mean_tax_burden"] = list(decile_res.mean_tax_burden)
        columns[f"{prefix}_mean_redistribution"] = list(decile_res.mean_redistribution)
        columns[f"{prefix}_mean_net_impact"] = list(decile_res.mean_net_impact)
        columns[f"{prefix}_household_count"] = list(decile_res.household_count)

    comparison_table = pa.table(columns)

    return ComparisonResult(
        scenarios=scenario_names,
        decile_results=decile_results_map,
        comparison_table=comparison_table,
    )


def decile_results_to_table(decile_results: DecileResults) -> pa.Table:
    """Convert DecileResults to a PyArrow table.

    Args:
        decile_results: Aggregated decile results.

    Returns:
        PyArrow table with columns for each metric.
    """
    return pa.table(
        {
            "decile": list(decile_results.decile),
            "household_count": list(decile_results.household_count),
            "mean_tax_burden": list(decile_results.mean_tax_burden),
            "mean_redistribution": list(decile_results.mean_redistribution),
            "mean_net_impact": list(decile_results.mean_net_impact),
            "total_tax_burden": list(decile_results.total_tax_burden),
            "total_redistribution": list(decile_results.total_redistribution),
            "total_net_impact": list(decile_results.total_net_impact),
        }
    )


__all__ = [
    "ComparisonResult",
    "compare_decile_impacts",
    "decile_results_to_table",
    "run_carbon_tax_batch",
]
