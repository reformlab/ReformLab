"""Vehicle malus computation functions.

This module implements the core computation logic for vehicle malus scenarios:
- Malus (penalty) calculation for households with emissions above threshold
- Year-indexed schedules for both rate and threshold
- Income decile assignment for distributional analysis
- Result aggregation by decile

Story 13.2 — Implements the French malus ecologique model using a simplified
linear rate approach: malus = max(0, emissions - threshold) * rate_per_gkm.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pyarrow as pa
import pyarrow.compute as pc

from reformlab.templates.carbon_tax.compute import assign_income_deciles
from reformlab.templates.schema import PolicyParameters


def _sum_array(values: pa.Array) -> float:
    """Return array sum as float, treating empty arrays as 0.0."""
    total = pc.sum(values).as_py()
    return 0.0 if total is None else float(total)


# ====================================================================
# Parameters
# ====================================================================


@dataclass(frozen=True)
class VehicleMalusParameters(PolicyParameters):
    """Vehicle malus (penalty) for high-emission vehicles.

    Models the French malus ecologique and similar emission-based
    vehicle registration penalties. Uses a simplified linear rate model:
    malus = max(0, emissions - threshold) * rate_per_gkm.

    Fields:
        emission_threshold: gCO2/km threshold below which no malus applies.
        malus_rate_per_gkm: EUR per gCO2/km above threshold.
        threshold_schedule: Year -> emission_threshold overrides.
            When a year is present, it overrides the default emission_threshold.
    """

    emission_threshold: float = 118.0
    malus_rate_per_gkm: float = 50.0
    threshold_schedule: dict[int, float] = field(default_factory=dict)


# ====================================================================
# Result types
# ====================================================================


@dataclass(frozen=True)
class VehicleMalusResult:
    """Result of vehicle malus computation for a single scenario run.

    Contains per-household malus amounts and summary statistics.
    """

    household_ids: pa.Array
    malus_amount: pa.Array
    vehicle_emissions: pa.Array
    income_decile: pa.Array
    total_revenue: float
    year: int
    template_name: str


@dataclass(frozen=True)
class VehicleMalusDecileResults:
    """Per-decile aggregated vehicle malus results.

    Contains count, mean, and total malus for each income decile (1-10).
    """

    decile: tuple[int, ...]
    household_count: tuple[int, ...]
    mean_malus: tuple[float, ...]
    total_malus: tuple[float, ...]


# ====================================================================
# Computation
# ====================================================================


def compute_vehicle_malus(
    population: pa.Table,
    policy: VehicleMalusParameters,
    year: int,
    template_name: str = "",
) -> VehicleMalusResult:
    """Compute vehicle malus for a population.

    Args:
        population: Population table with household_id, income, and
            optionally vehicle_emissions_gkm columns.
        policy: Vehicle malus parameters including threshold and rate.
        year: Year for computation (used for schedule lookups).
        template_name: Name of the template being executed.

    Returns:
        VehicleMalusResult with per-household and aggregate metrics.
    """
    household_ids = population.column("household_id")
    num_households = population.num_rows

    # Assign income deciles
    incomes = population.column("income")
    income_deciles = assign_income_deciles(incomes)

    # Year-indexed schedule lookups
    effective_rate = policy.rate_schedule.get(year, policy.malus_rate_per_gkm)
    effective_threshold = policy.threshold_schedule.get(
        year, policy.emission_threshold
    )

    # Get vehicle emissions — missing column treated as 0 emissions (no malus)
    if "vehicle_emissions_gkm" in population.column_names:
        raw_col = population.column("vehicle_emissions_gkm").combine_chunks()
        try:
            emissions_array = pc.fill_null(
                pc.cast(raw_col, pa.float64()), 0.0
            )
        except (pa.ArrowInvalid, pa.ArrowNotImplementedError):
            emissions_array = pa.array([0.0] * num_households, type=pa.float64())
    else:
        emissions_array = pa.array([0.0] * num_households, type=pa.float64())

    # Compute malus per household: max(0, emissions - threshold) * rate
    excess = pc.subtract(emissions_array, effective_threshold)
    clamped = pc.max_element_wise(excess, 0.0)
    malus_array = pc.multiply(clamped, effective_rate)
    total_revenue = _sum_array(malus_array)

    return VehicleMalusResult(
        household_ids=household_ids,
        malus_amount=malus_array,
        vehicle_emissions=emissions_array,
        income_decile=income_deciles,
        total_revenue=total_revenue,
        year=year,
        template_name=template_name,
    )


# ====================================================================
# Decile aggregation
# ====================================================================


def aggregate_vehicle_malus_by_decile(
    result: VehicleMalusResult,
) -> VehicleMalusDecileResults:
    """Aggregate vehicle malus results by income decile.

    Args:
        result: Per-household vehicle malus computation result.

    Returns:
        VehicleMalusDecileResults with count, mean, and total per decile.
    """
    decile_data: dict[int, list[float]] = {d: [] for d in range(1, 11)}

    deciles = result.income_decile.to_pylist()
    malus_amounts = result.malus_amount.to_pylist()

    for i, decile in enumerate(deciles):
        decile_data[decile].append(malus_amounts[i])

    decile_nums: list[int] = []
    counts: list[int] = []
    means: list[float] = []
    totals: list[float] = []

    for d in range(1, 11):
        values = decile_data[d]
        count = len(values)
        decile_nums.append(d)
        counts.append(count)

        if count > 0:
            total = sum(values)
            means.append(total / count)
            totals.append(total)
        else:
            means.append(0.0)
            totals.append(0.0)

    return VehicleMalusDecileResults(
        decile=tuple(decile_nums),
        household_count=tuple(counts),
        mean_malus=tuple(means),
        total_malus=tuple(totals),
    )
