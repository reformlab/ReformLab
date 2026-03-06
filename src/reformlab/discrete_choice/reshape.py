"""Cost matrix reshape logic for discrete choice evaluation.

Reshapes flat N×M computation results into an N-row × M-column cost
matrix using tracking columns (not positional row order).

Story 14-1: DiscreteChoiceStep with population expansion pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pyarrow as pa

from reformlab.discrete_choice.errors import ReshapeError
from reformlab.discrete_choice.expansion import (
    TRACKING_COL_ALTERNATIVE_ID,
    TRACKING_COL_ORIGINAL_INDEX,
)
from reformlab.discrete_choice.types import CostMatrix, ExpansionResult

if TYPE_CHECKING:
    from reformlab.computation.types import ComputationResult


def reshape_to_cost_matrix(
    result: ComputationResult,
    expansion: ExpansionResult,
    cost_column: str,
) -> CostMatrix:
    """Reshape flat computation results into an N×M cost matrix.

    Uses tracking columns (_alternative_id, _original_household_index)
    to map each result row to the correct (household, alternative) cell
    in the output matrix. Does NOT rely on positional row order.

    Args:
        result: Computation result from adapter (N×M rows).
        expansion: Expansion metadata (N, M, alternative IDs).
        cost_column: Column name to extract from computation results.

    Returns:
        CostMatrix with N rows and M named columns.

    Raises:
        ReshapeError: If cost column is missing or dimensions don't match.
    """
    output = result.output_fields
    n = expansion.n_households
    m = expansion.n_alternatives
    alt_ids = expansion.alternative_ids

    # Handle empty population: return empty CostMatrix with correct columns
    if n == 0:
        empty_columns = {alt_id: pa.array([], type=pa.float64()) for alt_id in alt_ids}
        return CostMatrix(
            table=pa.table(empty_columns),
            alternative_ids=alt_ids,
        )

    # Validate cost column exists
    if cost_column not in output.column_names:
        raise ReshapeError(
            f"Cost column '{cost_column}' not found in computation results. "
            f"Available columns: {output.column_names}",
        )

    # Validate tracking columns exist
    for col_name in (TRACKING_COL_ALTERNATIVE_ID, TRACKING_COL_ORIGINAL_INDEX):
        if col_name not in output.column_names:
            raise ReshapeError(
                f"Tracking column '{col_name}' not found in computation results. "
                f"Available columns: {output.column_names}",
            )

    # Validate row count matches N×M
    expected_rows = n * m
    if output.num_rows != expected_rows:
        raise ReshapeError(
            f"Computation result has {output.num_rows} rows, "
            f"expected {expected_rows} (N={n} × M={m})",
        )

    # Extract arrays
    cost_array = output.column(cost_column).to_pylist()
    alt_id_array = output.column(TRACKING_COL_ALTERNATIVE_ID).to_pylist()
    orig_idx_array = output.column(TRACKING_COL_ORIGINAL_INDEX).to_pylist()

    # Build N×M matrix using tracking columns
    # Initialize with None to detect missing cells
    matrix: list[list[float | None]] = [[None] * m for _ in range(n)]

    for row_idx in range(output.num_rows):
        hh_idx = orig_idx_array[row_idx]
        alt_idx = alt_id_array[row_idx]

        if hh_idx < 0 or hh_idx >= n:
            raise ReshapeError(
                f"Invalid household index {hh_idx} at row {row_idx} "
                f"(expected 0..{n - 1})",
            )
        if alt_idx < 0 or alt_idx >= m:
            raise ReshapeError(
                f"Invalid alternative index {alt_idx} at row {row_idx} "
                f"(expected 0..{m - 1})",
            )

        matrix[hh_idx][alt_idx] = cost_array[row_idx]

    # Build PyArrow table with M named columns
    columns: dict[str, pa.Array] = {}
    for alt_j, alt_id in enumerate(alt_ids):
        col_values = [matrix[i][alt_j] for i in range(n)]
        columns[alt_id] = pa.array(col_values, type=pa.float64())

    return CostMatrix(
        table=pa.table(columns),
        alternative_ids=alt_ids,
    )
