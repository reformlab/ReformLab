"""Subsystem-specific exceptions for statistical merge methods.

All exceptions follow the ``[summary] - [reason] - [fix]`` message
pattern established by ``DataSourceError`` in the loaders subsystem.

Implements Story 11.4 (MergeMethod protocol and uniform distribution).
Extended by Story 11.5 (MergeConvergenceError for IPF).
"""

from __future__ import annotations


class MergeError(Exception):
    """Base exception for merge method operations.

    All merge exceptions use keyword-only constructor arguments
    and produce a structured ``summary - reason - fix`` message.
    """

    def __init__(self, *, summary: str, reason: str, fix: str) -> None:
        self.summary = summary
        self.reason = reason
        self.fix = fix
        super().__init__(f"{summary} - {reason} - {fix}")


class MergeValidationError(MergeError):
    """Raised when merge inputs fail validation.

    Triggered by: empty tables, column name conflicts, invalid
    drop_right_columns, or schema mismatches.
    """


class MergeConvergenceError(MergeError):
    """Raised when an iterative merge method fails to converge.

    Triggered by: IPF exceeding max_iterations without reaching
    the tolerance threshold. Often caused by inconsistent marginal
    constraints (target totals that cannot be simultaneously satisfied).
    """
