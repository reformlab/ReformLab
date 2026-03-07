"""Error hierarchy for the discrete choice subsystem.

Provides subsystem-specific exceptions for population expansion,
cost matrix reshape, logit computation, and step execution errors.

Story 14-1: DiscreteChoiceStep with population expansion pattern.
Story 14-2: LogitError for probability computation and draw failures.
"""

from __future__ import annotations


class DiscreteChoiceError(Exception):
    """Base error for the discrete choice subsystem.

    Includes year, step name, and domain context for debugging
    and governance tracking.
    """

    def __init__(
        self,
        message: str,
        *,
        year: int | None = None,
        step_name: str | None = None,
        domain_name: str | None = None,
        original_error: Exception | None = None,
    ) -> None:
        self.year = year
        self.step_name = step_name
        self.domain_name = domain_name
        self.original_error = original_error
        super().__init__(message)


class ExpansionError(DiscreteChoiceError):
    """Error during population expansion.

    Raised when the choice set is invalid (empty, duplicate IDs)
    or expansion logic fails.
    """


class ReshapeError(DiscreteChoiceError):
    """Error during cost matrix reshape.

    Raised when computation results cannot be reshaped into the
    expected N×M cost matrix (missing columns, dimension mismatch).
    """


class LogitError(DiscreteChoiceError):
    """Error during logit probability computation or choice draws.

    Raised when cost matrix contains invalid values (NaN, Inf),
    probability normalization fails, or draw sampling encounters errors.
    """
