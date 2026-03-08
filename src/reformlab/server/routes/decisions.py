"""Decision outcome summary routes for the Behavioral Decision Viewer.

Story 17.5: Build Behavioral Decision Viewer

Endpoint: POST /api/decisions/summary
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.compute as pc
from fastapi import APIRouter, Depends, HTTPException

from reformlab.server.dependencies import ResultCache, get_result_cache, get_result_store
from reformlab.server.models import (
    DecisionSummaryRequest,
    DecisionSummaryResponse,
    DomainSummary,
    YearlyOutcome,
)
from reformlab.server.result_store import ResultStoreError

if TYPE_CHECKING:
    from reformlab.server.result_store import ResultStore

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Static alternative labels registry
# ---------------------------------------------------------------------------

ALTERNATIVE_LABELS: dict[str, dict[str, str]] = {
    "vehicle": {
        "keep_current": "Keep Current",
        "buy_petrol": "Petrol",
        "buy_diesel": "Diesel",
        "buy_hybrid": "Hybrid",
        "buy_ev": "Electric (EV)",
        "buy_no_vehicle": "No Vehicle",
    },
    "heating": {
        "keep_current": "Keep Current",
        "gas_boiler": "Gas Boiler",
        "heat_pump": "Heat Pump",
        "electric": "Electric",
        "wood_pellet": "Wood/Pellet",
    },
}

# ---------------------------------------------------------------------------
# Route handler
# ---------------------------------------------------------------------------


@router.post("/summary", response_model=DecisionSummaryResponse)
async def get_decision_summary(
    body: DecisionSummaryRequest,
    cache: ResultCache = Depends(get_result_cache),
    store: ResultStore = Depends(get_result_store),
) -> DecisionSummaryResponse:
    """Aggregate decision outcomes from a simulation panel output.

    AC-1: Returns domain summaries with counts/percentages per alternative.
    AC-2: Year-by-year transition data in ascending year order.
    AC-3: Income decile filtering (server-side, uses PyArrow compute).
    AC-4: Year detail with mean probabilities when year param is set.
    """
    # 1. Check ResultStore metadata (404 if unknown)
    try:
        store.get_metadata(body.run_id)
    except ResultStoreError:
        raise HTTPException(
            status_code=404,
            detail={
                "what": f"Run '{body.run_id}' not found",
                "why": "No metadata record exists for this run_id",
                "fix": "Check the run_id and ensure the simulation has been executed",
            },
        )

    # 2. Check ResultCache (409 if evicted or panel_output is None)
    sim_result = cache.get(body.run_id)
    if sim_result is None or sim_result.panel_output is None:
        raise HTTPException(
            status_code=409,
            detail={
                "what": f"Run '{body.run_id}' data is not available",
                "why": "The simulation result has been evicted from the in-memory cache",
                "fix": "Re-run the simulation or select runs with data_available=true",
            },
        )

    panel = sim_result.panel_output
    panel_table = panel.table
    panel_metadata = panel.metadata

    # 3. Check for decision_domain_alternatives key in metadata (422 if absent)
    if "decision_domain_alternatives" not in panel_metadata:
        raise HTTPException(
            status_code=422,
            detail={
                "what": "NoDecisionData",
                "why": "Run does not contain decision data",
                "fix": (
                    "Run a simulation with discrete choice domains (vehicle, heating)"
                ),
            },
        )

    domain_alternatives: dict[str, list[str]] = panel_metadata[
        "decision_domain_alternatives"
    ]

    # 4b. Validate group_by value and group_value range
    if body.group_by is not None and body.group_by != "decile":
        raise HTTPException(
            status_code=422,
            detail={
                "what": f"Unsupported group_by value '{body.group_by}'",
                "why": "Only 'decile' grouping is currently supported",
                "fix": "Use group_by='decile' or omit the group_by parameter",
            },
        )

    if body.group_by == "decile" and body.group_value is not None:
        try:
            dv = int(body.group_value)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail={
                    "what": f"Invalid group_value '{body.group_value}'",
                    "why": "group_value must be an integer string between 1 and 10",
                    "fix": "Provide a group_value between '1' and '10'",
                },
            )
        if not 1 <= dv <= 10:
            raise HTTPException(
                status_code=422,
                detail={
                    "what": f"Invalid group_value '{body.group_value}'",
                    "why": "group_value must be between 1 and 10 for decile grouping",
                    "fix": "Provide a group_value between '1' and '10'",
                },
            )

    # 4c. If group_by="decile": check income column exists (422 if absent)
    if body.group_by == "decile":
        if "income" not in panel_table.column_names:
            raise HTTPException(
                status_code=422,
                detail={
                    "what": "NoIncomeData",
                    "why": (
                        "Panel output does not contain an income column required "
                        "for decile grouping"
                    ),
                    "fix": (
                        "Run a simulation with a population dataset that includes "
                        "income data"
                    ),
                },
            )

    # 5. Determine which domains to process
    if body.domain_name is not None:
        if body.domain_name not in domain_alternatives:
            raise HTTPException(
                status_code=422,
                detail={
                    "what": f"Domain '{body.domain_name}' not found",
                    "why": (
                        f"Available domains: {list(domain_alternatives.keys())}"
                    ),
                    "fix": "Use one of the available domain names",
                },
            )
        domains_to_process: dict[str, list[str]] = {
            body.domain_name: domain_alternatives[body.domain_name]
        }
    else:
        domains_to_process = dict(domain_alternatives)

    # 6. Build domain summaries
    warnings: list[str] = []
    domain_summaries: list[DomainSummary] = []

    for domain_name, alt_ids in domains_to_process.items():
        summary, domain_warnings = _build_domain_summary(
            panel_table=panel_table,
            domain_name=domain_name,
            alt_ids=alt_ids,
            group_by=body.group_by,
            group_value=body.group_value,
            year=body.year,
        )
        warnings.extend(domain_warnings)
        domain_summaries.append(summary)

    return DecisionSummaryResponse(
        run_id=body.run_id,
        domains=domain_summaries,
        metadata={
            "start_year": panel_metadata.get("start_year"),
            "end_year": panel_metadata.get("end_year"),
        },
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# Domain summary builder
# ---------------------------------------------------------------------------


def _build_domain_summary(
    panel_table: pa.Table,
    domain_name: str,
    alt_ids: list[str],
    group_by: str | None,
    group_value: str | None,
    year: int | None,
) -> tuple[DomainSummary, list[str]]:
    """Aggregate decision outcomes for a single domain across all years."""
    warnings: list[str] = []
    chosen_col_name = f"{domain_name}_chosen"

    # Derive years in ascending order
    year_col = panel_table.column("year")
    all_years: list[int] = sorted(set(year_col.to_pylist()))

    yearly_outcomes: list[YearlyOutcome] = []

    for yr in all_years:
        # Filter to this year
        year_mask = pc.equal(year_col, yr)
        year_table = panel_table.filter(year_mask)

        # Apply decile filter if requested
        if group_by == "decile" and group_value is not None:
            year_table = _filter_to_decile(year_table, int(group_value))

        total_households = year_table.num_rows

        # Count chosen alternatives using PyArrow value_counts
        if total_households > 0:
            if chosen_col_name not in year_table.column_names:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "what": f"Missing decision column '{chosen_col_name}'",
                        "why": (
                            f"Panel output declares domain '{domain_name}' in metadata "
                            f"but column '{chosen_col_name}' is absent from the table"
                        ),
                        "fix": "Re-run the simulation to regenerate the panel output",
                    },
                )
            chosen_col = year_table.column(chosen_col_name)
            counts = _count_alternatives(chosen_col, alt_ids)
        else:
            counts = {alt_id: 0 for alt_id in alt_ids}

        # Compute percentages (0–100 scale)
        if total_households > 0:
            percentages: dict[str, float] = {
                alt_id: counts[alt_id] / total_households * 100.0
                for alt_id in alt_ids
            }
        else:
            percentages = {alt_id: 0.0 for alt_id in alt_ids}

        # Compute mean probabilities when year detail is requested for this year
        mean_probabilities: dict[str, float] | None = None
        if year is not None and yr == year:
            prob_col_name = f"{domain_name}_probabilities"
            if prob_col_name in year_table.column_names:
                mean_probabilities = _compute_mean_probabilities(
                    year_table.column(prob_col_name), alt_ids
                )
            else:
                warnings.append(
                    f"Probability data unavailable for domain '{domain_name}': "
                    "column not present in panel output"
                )

        yearly_outcomes.append(
            YearlyOutcome(
                year=yr,
                total_households=total_households,
                counts=counts,
                percentages=percentages,
                mean_probabilities=mean_probabilities,
            )
        )

    # Build alternative labels (fall back to alt_id when label not known)
    domain_label_map = ALTERNATIVE_LABELS.get(domain_name, {})
    alternative_labels: dict[str, str] = {
        alt_id: domain_label_map.get(alt_id, alt_id) for alt_id in alt_ids
    }

    return (
        DomainSummary(
            domain_name=domain_name,
            alternative_ids=list(alt_ids),
            alternative_labels=alternative_labels,
            yearly_outcomes=yearly_outcomes,
            eligibility=None,
        ),
        warnings,
    )


# ---------------------------------------------------------------------------
# PyArrow helpers
# ---------------------------------------------------------------------------


def _count_alternatives(
    chosen_col: pa.ChunkedArray | pa.Array, alt_ids: list[str]
) -> dict[str, int]:
    """Count occurrences of each alternative in the chosen column."""
    counts: dict[str, int] = {alt_id: 0 for alt_id in alt_ids}
    value_counts: Any = pc.value_counts(chosen_col)
    for item in value_counts.to_pylist():
        alt_id = item["values"]
        if alt_id in counts:
            counts[alt_id] = int(item["counts"])
    return counts


def _filter_to_decile(year_table: pa.Table, decile: int) -> pa.Table:
    """Filter a year table to households in the given income decile (1–10).

    Decile assignment uses PyArrow compute exclusively (no NumPy).
    Boundaries are computed via pc.quantile on the income column.
    Null income values are treated as decile 1 (lowest boundary not exceeded).
    """
    if year_table.num_rows == 0:
        return year_table

    income_col: pa.ChunkedArray | pa.Array = year_table.column("income")
    decile_col = _assign_deciles(income_col)
    mask = pc.equal(decile_col, decile)
    return year_table.filter(mask)


def _assign_deciles(
    income_col: pa.ChunkedArray | pa.Array,
) -> pa.Array:
    """Assign income decile (1–10) to each row using PyArrow compute.

    Algorithm: start all households at decile=1, then for each of the 9
    quantile boundaries (10th–90th percentile), increment decile by 1 for
    households whose income exceeds that boundary.

    Null income values keep decile=1 (increment treated as 0).
    """
    n = len(income_col)
    q_values = [i / 10.0 for i in range(1, 10)]
    boundaries = pc.quantile(income_col, q=q_values)
    boundaries_list: list[float | None] = boundaries.to_pylist()

    decile_arr: pa.Array = pa.array([1] * n, type=pa.int64())

    for boundary_val in boundaries_list:
        if boundary_val is None:
            continue
        boundary_scalar = pa.scalar(boundary_val)
        gt_result = pc.greater(income_col, boundary_scalar)
        # Fill nulls (null income) with False so they stay at current decile
        gt_filled = pc.fill_null(gt_result, False)
        increment = pc.cast(gt_filled, pa.int64())
        decile_arr = pc.add(decile_arr, increment)

    return decile_arr


def _compute_mean_probabilities(
    prob_col: pa.ChunkedArray | pa.Array, alt_ids: list[str]
) -> dict[str, float]:
    """Compute element-wise mean probability across all households.

    Each row in prob_col is a list<float64> of length len(alt_ids).
    Returns a mapping alt_id → mean probability.
    """
    n_alts = len(alt_ids)
    prob_lists: list[list[float] | None] = prob_col.to_pylist()

    mean_probs = [0.0] * n_alts
    count_valid = 0

    for prob_list in prob_lists:
        if prob_list is None or len(prob_list) != n_alts:
            continue
        for j, p in enumerate(prob_list):
            if p is not None:
                mean_probs[j] += p
        count_valid += 1

    if count_valid > 0:
        mean_probs = [p / count_valid for p in mean_probs]

    return {alt_id: mean_probs[i] for i, alt_id in enumerate(alt_ids)}
