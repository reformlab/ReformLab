"""Tests for merge method error hierarchy.

Story 11.4 — AC #1: MergeError hierarchy follows the
``summary - reason - fix`` pattern from DataSourceError.
Story 11.5 — AC #1: MergeConvergenceError for IPF non-convergence.
"""

from __future__ import annotations

import pytest

from reformlab.population.methods.errors import (
    MergeConvergenceError,
    MergeError,
    MergeValidationError,
)


class TestMergeError:
    """MergeError base exception: summary-reason-fix pattern."""

    def test_inherits_exception(self) -> None:
        assert issubclass(MergeError, Exception)

    def test_message_format(self) -> None:
        err = MergeError(
            summary="Something failed",
            reason="because of X",
            fix="do Y instead",
        )
        assert str(err) == "Something failed - because of X - do Y instead"

    def test_attributes_accessible(self) -> None:
        err = MergeError(
            summary="sum", reason="rea", fix="fix"
        )
        assert err.summary == "sum"
        assert err.reason == "rea"
        assert err.fix == "fix"

    def test_keyword_only_arguments(self) -> None:
        with pytest.raises(TypeError):
            MergeError("sum", "rea", "fix")  # type: ignore[misc]


class TestMergeValidationError:
    """MergeValidationError inherits MergeError."""

    def test_inherits_merge_error(self) -> None:
        assert issubclass(MergeValidationError, MergeError)

    def test_catchable_as_merge_error(self) -> None:
        with pytest.raises(MergeError):
            raise MergeValidationError(
                summary="Validation failed",
                reason="empty table",
                fix="provide non-empty table",
            )

    def test_message_format(self) -> None:
        err = MergeValidationError(
            summary="Column conflict",
            reason="overlapping names",
            fix="use drop_right_columns",
        )
        assert "Column conflict" in str(err)
        assert "overlapping names" in str(err)
        assert "drop_right_columns" in str(err)


class TestMergeConvergenceError:
    """Story 11.5: MergeConvergenceError for IPF non-convergence."""

    def test_inherits_merge_error(self) -> None:
        assert issubclass(MergeConvergenceError, MergeError)

    def test_catchable_as_merge_error(self) -> None:
        with pytest.raises(MergeError):
            raise MergeConvergenceError(
                summary="IPF did not converge",
                reason="max iterations exceeded",
                fix="increase max_iterations",
            )

    def test_message_format(self) -> None:
        err = MergeConvergenceError(
            summary="IPF did not converge",
            reason="100 iterations, deviation 0.5",
            fix="increase max_iterations or relax tolerance",
        )
        assert "IPF did not converge" in str(err)
        assert "100 iterations" in str(err)
        assert "max_iterations" in str(err)

    def test_attributes_accessible(self) -> None:
        err = MergeConvergenceError(
            summary="sum", reason="rea", fix="fix"
        )
        assert err.summary == "sum"
        assert err.reason == "rea"
        assert err.fix == "fix"
