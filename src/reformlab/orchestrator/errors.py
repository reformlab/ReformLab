"""Error classes for the orchestrator module.

Provides structured error types with context for debugging
orchestrator failures during multi-year projections.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from reformlab.orchestrator.types import YearState


@dataclass
class OrchestratorError(Exception):
    """Structured orchestrator error with execution context.

    Provides actionable error information including:
    - The summary and reason for the failure
    - The year and step where failure occurred
    - Partial results (completed years) for debugging

    Attributes:
        summary: Brief description of what failed.
        reason: Technical explanation of why it failed.
        year: Year when failure occurred.
        step_name: Name of the step that caused the failure.
        partial_states: Yearly states completed before failure.
        original_error: The underlying exception that was caught.
    """

    summary: str
    reason: str
    year: int | None = None
    step_name: str | None = None
    partial_states: dict[int, "YearState"] = field(default_factory=dict)
    original_error: Exception | None = None

    def __post_init__(self) -> None:
        """Build the exception message from structured fields."""
        message_parts = [f"{self.summary} - {self.reason}"]

        if self.year is not None:
            message_parts.append(f"(year: {self.year})")

        if self.step_name is not None:
            message_parts.append(f"(step: {self.step_name})")

        if self.partial_states:
            completed_years = sorted(self.partial_states.keys())
            message_parts.append(f"(completed years: {completed_years})")

        super().__init__(" ".join(message_parts))

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for serialization."""
        return {
            "summary": self.summary,
            "reason": self.reason,
            "year": self.year,
            "step_name": self.step_name,
            "completed_years": sorted(self.partial_states.keys()),
        }
