"""Energy poverty aid computation functions.

This module implements the core computation logic for energy poverty aid scenarios:
- Aid calculation for low-income, energy-burdened households
- Dual-condition eligibility (income ceiling AND energy share threshold)
- Year-indexed schedules for ceiling, threshold, and base aid amount
- Income decile assignment for distributional analysis
- Result aggregation by decile

Story 13.3 — Models the French cheque energie using a simplified linear model:
aid = base_aid * income_ratio * energy_burden_factor.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import pyarrow as pa
import pyarrow.compute as pc

from reformlab.templates.carbon_tax.compute import assign_income_deciles
from reformlab.templates.exceptions import TemplateError
from reformlab.templates.schema import PolicyParameters

logger = logging.getLogger(__name__)


def _sum_array(values: pa.Array) -> float:
    """Return array sum as float, treating empty arrays as 0.0."""
    total = pc.sum(values).as_py()
    return 0.0 if total is None else float(total)


# ====================================================================
# Parameters
# ====================================================================


@dataclass(frozen=True)
class EnergyPovertyAidParameters(PolicyParameters):
    """Energy poverty aid for low-income, energy-burdened households.

    Models the French cheque energie and similar income-conditioned
    energy poverty aid policies. Uses a simplified linear model:
    aid = base_aid_amount * income_ratio * energy_burden_factor.

    Fields:
        income_ceiling: EUR RFR/UC threshold (cheque energie default ~11,000).
        energy_share_threshold: Minimum energy expenditure share of income (8% TEE_3D).
        base_aid_amount: Base aid in EUR (average cheque energie ~150).
        max_energy_factor: Cap on energy burden multiplier.
        income_ceiling_schedule: Year -> income_ceiling overrides.
        energy_share_schedule: Year -> energy_share_threshold overrides.
        aid_schedule: Year -> base_aid_amount overrides.
    """

    income_ceiling: float = 11000.0
    energy_share_threshold: float = 0.08
    base_aid_amount: float = 150.0
    max_energy_factor: float = 2.0
    income_ceiling_schedule: dict[int, float] = field(default_factory=dict)
    energy_share_schedule: dict[int, float] = field(default_factory=dict)
    aid_schedule: dict[int, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.income_ceiling <= 0:
            msg = (
                f"income_ceiling must be > 0, got {self.income_ceiling}. "
                f"Cannot compute income_ratio with non-positive ceiling."
            )
            raise TemplateError(msg)
        if self.energy_share_threshold <= 0:
            msg = (
                f"energy_share_threshold must be > 0, got {self.energy_share_threshold}. "
                f"Cannot compute energy_burden_factor with non-positive threshold."
            )
            raise TemplateError(msg)
        if self.max_energy_factor <= 0:
            msg = (
                f"max_energy_factor must be > 0, got {self.max_energy_factor}. "
                f"Cap must be positive."
            )
            raise TemplateError(msg)


# ====================================================================
# Result types
# ====================================================================


@dataclass(frozen=True)
class EnergyPovertyAidResult:
    """Result of energy poverty aid computation for a single scenario run.

    Contains per-household aid amounts and summary statistics.
    """

    household_ids: pa.Array
    aid_amount: pa.Array
    is_eligible: pa.Array
    energy_expenditure_share: pa.Array
    income_decile: pa.Array
    total_cost: float
    eligible_count: int
    year: int
    template_name: str


@dataclass(frozen=True)
class EnergyPovertyAidDecileResults:
    """Per-decile aggregated energy poverty aid results.

    Contains count, eligible count, mean aid, and total aid for
    each income decile (1-10).
    """

    decile: tuple[int, ...]
    household_count: tuple[int, ...]
    eligible_count: tuple[int, ...]
    mean_aid: tuple[float, ...]
    total_aid: tuple[float, ...]


# ====================================================================
# Computation
# ====================================================================


def compute_energy_poverty_aid(
    population: pa.Table,
    policy: EnergyPovertyAidParameters,
    year: int,
    template_name: str = "",
) -> EnergyPovertyAidResult:
    """Compute energy poverty aid for a population.

    Args:
        population: Population table with household_id, income, and
            optionally energy_expenditure columns.
        policy: Energy poverty aid parameters.
        year: Year for computation (used for schedule lookups).
        template_name: Name of the template being executed.

    Returns:
        EnergyPovertyAidResult with per-household and aggregate metrics.
    """
    household_ids = population.column("household_id")
    num_households = population.num_rows

    logger.info(
        "event=compute_start year=%d template=%s households=%d",
        year,
        template_name,
        num_households,
    )

    # Assign income deciles
    incomes_raw = population.column("income")
    if isinstance(incomes_raw, pa.ChunkedArray):
        incomes_raw = incomes_raw.combine_chunks()
    incomes = pc.fill_null(pc.cast(incomes_raw, pa.float64()), 0.0)
    income_deciles = assign_income_deciles(incomes)

    # Year-indexed schedule lookups with runtime validation
    effective_ceiling = policy.income_ceiling_schedule.get(
        year, policy.income_ceiling
    )
    effective_threshold = policy.energy_share_schedule.get(
        year, policy.energy_share_threshold
    )
    effective_base_aid = policy.aid_schedule.get(year, policy.base_aid_amount)

    if effective_ceiling <= 0:
        msg = (
            f"Effective income_ceiling for year {year} is {effective_ceiling} "
            f"(from schedule). Must be > 0."
        )
        raise TemplateError(msg)
    if effective_threshold <= 0:
        msg = (
            f"Effective energy_share_threshold for year {year} is "
            f"{effective_threshold} (from schedule). Must be > 0."
        )
        raise TemplateError(msg)

    # Get energy expenditure — missing column treated as 0 (no one eligible)
    if "energy_expenditure" in population.column_names:
        raw_col = population.column("energy_expenditure")
        if isinstance(raw_col, pa.ChunkedArray):
            raw_col = raw_col.combine_chunks()
        try:
            energy_exp = pc.fill_null(pc.cast(raw_col, pa.float64()), 0.0)
        except (pa.ArrowInvalid, pa.ArrowNotImplementedError) as exc:
            msg = (
                f"Column 'energy_expenditure' has type {raw_col.type} "
                f"which cannot be cast to float64. "
                f"Provide numeric energy expenditure values."
            )
            raise TemplateError(msg) from exc
    else:
        energy_exp = pa.array([0.0] * num_households, type=pa.float64())

    # Compute energy expenditure share (vectorized)
    # For income <= 0: treat share as exceeding threshold (eligible for max aid)
    # For energy_expenditure <= 0: share = 0 (not eligible)
    energy_positive = pc.greater(energy_exp, 0.0)
    income_positive = pc.greater(incomes, 0.0)

    energy_share_array = pc.if_else(
        pc.invert(energy_positive),
        0.0,
        pc.if_else(
            pc.invert(income_positive),
            effective_threshold + 1.0,
            pc.divide(energy_exp, incomes),
        ),
    )

    # Compute eligibility: income < ceiling AND energy_share >= threshold
    income_below_ceiling = pc.less(incomes, effective_ceiling)
    share_at_or_above_threshold = pc.greater_equal(
        energy_share_array, effective_threshold
    )
    is_eligible = pc.and_(income_below_ceiling, share_at_or_above_threshold)

    # income_ratio = (ceiling - income) / ceiling, clamped to [0, 1]
    # For income <= 0: income_ratio = 1.0
    raw_ratio = pc.divide(
        pc.subtract(pa.scalar(effective_ceiling), incomes),
        pa.scalar(effective_ceiling),
    )
    clamped_ratio = pc.max_element_wise(
        pc.min_element_wise(raw_ratio, 1.0), 0.0
    )
    income_ratio_array = pc.if_else(
        income_positive, clamped_ratio, 1.0
    )

    # energy_burden_factor = min(energy_share / threshold, max_energy_factor)
    energy_factor_array = pc.if_else(
        pc.greater(energy_share_array, 0.0),
        pc.min_element_wise(
            pc.divide(energy_share_array, pa.scalar(effective_threshold)),
            pa.scalar(policy.max_energy_factor),
        ),
        0.0,
    )

    # aid = base_aid * income_ratio * energy_burden_factor (for eligible only)
    raw_aid = pc.multiply(
        pc.multiply(income_ratio_array, energy_factor_array),
        effective_base_aid,
    )

    # Zero out ineligible households
    aid_amount = pc.if_else(is_eligible, raw_aid, 0.0)

    total_cost = _sum_array(aid_amount)
    eligible_count = int(pc.sum(pc.cast(is_eligible, pa.int64())).as_py() or 0)

    logger.info(
        "event=compute_done year=%d template=%s eligible=%d total_cost=%.2f",
        year,
        template_name,
        eligible_count,
        total_cost,
    )

    return EnergyPovertyAidResult(
        household_ids=household_ids,
        aid_amount=aid_amount,
        is_eligible=is_eligible,
        energy_expenditure_share=energy_share_array,
        income_decile=income_deciles,
        total_cost=total_cost,
        eligible_count=eligible_count,
        year=year,
        template_name=template_name,
    )


# ====================================================================
# Decile aggregation
# ====================================================================


def aggregate_energy_poverty_aid_by_decile(
    result: EnergyPovertyAidResult,
) -> EnergyPovertyAidDecileResults:
    """Aggregate energy poverty aid results by income decile.

    Args:
        result: Per-household energy poverty aid computation result.

    Returns:
        EnergyPovertyAidDecileResults with count, eligible, mean, and total per decile.
    """
    decile_data: dict[int, list[float]] = {d: [] for d in range(1, 11)}
    decile_eligible: dict[int, int] = {d: 0 for d in range(1, 11)}

    deciles = result.income_decile.to_pylist()
    aid_amounts = result.aid_amount.to_pylist()
    eligible_flags = result.is_eligible.to_pylist()

    for i, decile in enumerate(deciles):
        decile_data[decile].append(aid_amounts[i])
        if eligible_flags[i]:
            decile_eligible[decile] += 1

    decile_nums: list[int] = []
    counts: list[int] = []
    eligible_counts: list[int] = []
    means: list[float] = []
    totals: list[float] = []

    for d in range(1, 11):
        values = decile_data[d]
        count = len(values)
        decile_nums.append(d)
        counts.append(count)
        eligible_counts.append(decile_eligible[d])

        if count > 0:
            total = sum(values)
            means.append(total / count)
            totals.append(total)
        else:
            means.append(0.0)
            totals.append(0.0)

    return EnergyPovertyAidDecileResults(
        decile=tuple(decile_nums),
        household_count=tuple(counts),
        eligible_count=tuple(eligible_counts),
        mean_aid=tuple(means),
        total_aid=tuple(totals),
    )
