"""Tests for cost matrix reshape logic.

Story 14-1, AC-4: Flat-to-matrix reshape, dimension validation,
cost column extraction, error on mismatched dimensions.
"""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.computation.types import ComputationResult
from reformlab.discrete_choice.errors import ReshapeError
from reformlab.discrete_choice.expansion import (
    TRACKING_COL_ALTERNATIVE_ID,
    TRACKING_COL_ORIGINAL_INDEX,
)
from reformlab.discrete_choice.reshape import reshape_to_cost_matrix
from reformlab.discrete_choice.types import ExpansionResult


def _make_expansion(n: int, m: int, alt_ids: tuple[str, ...]) -> ExpansionResult:
    """Helper to create ExpansionResult for reshape tests."""
    return ExpansionResult(
        population=None,  # type: ignore[arg-type]
        n_households=n,
        n_alternatives=m,
        alternative_ids=alt_ids,
    )


def _make_result(
    cost_values: list[float],
    alt_ids: list[int],
    orig_indices: list[int],
    cost_column: str = "total_cost",
) -> ComputationResult:
    """Helper to create ComputationResult with tracking columns."""
    return ComputationResult(
        output_fields=pa.table({
            cost_column: pa.array(cost_values),
            TRACKING_COL_ALTERNATIVE_ID: pa.array(alt_ids, type=pa.int32()),
            TRACKING_COL_ORIGINAL_INDEX: pa.array(orig_indices, type=pa.int32()),
        }),
        adapter_version="mock-1.0.0",
        period=2025,
    )


class TestCostMatrixReshape:
    """Tests for reshape_to_cost_matrix function."""

    def test_basic_reshape_3x3(self) -> None:
        """3 households × 3 alternatives reshaped correctly."""
        expansion = _make_expansion(3, 3, ("a", "b", "c"))
        result = _make_result(
            cost_values=[100, 200, 300, 110, 210, 310, 120, 220, 320],
            alt_ids=[0, 0, 0, 1, 1, 1, 2, 2, 2],
            orig_indices=[0, 1, 2, 0, 1, 2, 0, 1, 2],
        )

        cm = reshape_to_cost_matrix(result, expansion, "total_cost")

        assert cm.n_households == 3
        assert cm.n_alternatives == 3
        assert cm.alternative_ids == ("a", "b", "c")

        # Verify values: row 0 = [100, 110, 120], row 1 = [200, 210, 220], etc.
        assert cm.table.column("a").to_pylist() == [100.0, 200.0, 300.0]
        assert cm.table.column("b").to_pylist() == [110.0, 210.0, 310.0]
        assert cm.table.column("c").to_pylist() == [120.0, 220.0, 320.0]

    def test_reshape_shuffled_order(self) -> None:
        """Reshape works correctly when rows are NOT in sequential order."""
        expansion = _make_expansion(2, 2, ("x", "y"))
        # Shuffled: hh1-alt1, hh0-alt0, hh0-alt1, hh1-alt0
        result = _make_result(
            cost_values=[40.0, 10.0, 20.0, 30.0],
            alt_ids=[1, 0, 1, 0],
            orig_indices=[1, 0, 0, 1],
        )

        cm = reshape_to_cost_matrix(result, expansion, "total_cost")

        # hh0: alt_x=10, alt_y=20; hh1: alt_x=30, alt_y=40
        assert cm.table.column("x").to_pylist() == [10.0, 30.0]
        assert cm.table.column("y").to_pylist() == [20.0, 40.0]

    def test_reshape_single_alternative(self) -> None:
        """M=1: reshape produces N×1 matrix."""
        expansion = _make_expansion(3, 1, ("only",))
        result = _make_result(
            cost_values=[10.0, 20.0, 30.0],
            alt_ids=[0, 0, 0],
            orig_indices=[0, 1, 2],
        )

        cm = reshape_to_cost_matrix(result, expansion, "total_cost")
        assert cm.n_households == 3
        assert cm.n_alternatives == 1
        assert cm.table.column("only").to_pylist() == [10.0, 20.0, 30.0]

    def test_reshape_single_household(self) -> None:
        """N=1: reshape produces 1×M matrix."""
        expansion = _make_expansion(1, 3, ("a", "b", "c"))
        result = _make_result(
            cost_values=[100.0, 200.0, 300.0],
            alt_ids=[0, 1, 2],
            orig_indices=[0, 0, 0],
        )

        cm = reshape_to_cost_matrix(result, expansion, "total_cost")
        assert cm.n_households == 1
        assert cm.table.column("a").to_pylist() == [100.0]
        assert cm.table.column("b").to_pylist() == [200.0]
        assert cm.table.column("c").to_pylist() == [300.0]

    def test_reshape_empty_population(self) -> None:
        """N=0: returns empty CostMatrix with correct M columns."""
        expansion = _make_expansion(0, 3, ("a", "b", "c"))
        result = ComputationResult(
            output_fields=pa.table({
                "total_cost": pa.array([], type=pa.float64()),
                TRACKING_COL_ALTERNATIVE_ID: pa.array([], type=pa.int32()),
                TRACKING_COL_ORIGINAL_INDEX: pa.array([], type=pa.int32()),
            }),
            adapter_version="mock-1.0.0",
            period=2025,
        )

        cm = reshape_to_cost_matrix(result, expansion, "total_cost")
        assert cm.n_households == 0
        assert cm.n_alternatives == 3
        assert cm.table.column_names == ["a", "b", "c"]

    def test_missing_cost_column_raises(self) -> None:
        """ReshapeError when cost column is not in computation results."""
        expansion = _make_expansion(2, 2, ("a", "b"))
        result = _make_result(
            cost_values=[1.0, 2.0, 3.0, 4.0],
            alt_ids=[0, 0, 1, 1],
            orig_indices=[0, 1, 0, 1],
            cost_column="existing_cost",
        )

        with pytest.raises(ReshapeError, match="missing_column.*not found"):
            reshape_to_cost_matrix(result, expansion, "missing_column")

    def test_dimension_mismatch_raises(self) -> None:
        """ReshapeError when result rows don't match N×M."""
        expansion = _make_expansion(3, 3, ("a", "b", "c"))
        # Only 6 rows instead of expected 9
        result = _make_result(
            cost_values=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            alt_ids=[0, 0, 0, 1, 1, 1],
            orig_indices=[0, 1, 2, 0, 1, 2],
        )

        with pytest.raises(ReshapeError, match="expected 9"):
            reshape_to_cost_matrix(result, expansion, "total_cost")

    def test_determinism(self) -> None:
        """Same inputs produce identical outputs."""
        expansion = _make_expansion(2, 2, ("a", "b"))
        result = _make_result(
            cost_values=[10.0, 20.0, 30.0, 40.0],
            alt_ids=[0, 0, 1, 1],
            orig_indices=[0, 1, 0, 1],
        )

        cm1 = reshape_to_cost_matrix(result, expansion, "total_cost")
        cm2 = reshape_to_cost_matrix(result, expansion, "total_cost")
        assert cm1.table.equals(cm2.table)
