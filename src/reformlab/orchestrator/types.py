"""Core types for the yearly loop orchestrator.

This module defines the data structures used by the orchestrator:
- YearState: State carried between years
- OrchestratorConfig: Configuration for orchestrator execution
- OrchestratorResult: Result of orchestrator execution
- YearStep: Type alias for legacy callable steps
- PipelineStep: Union of callable and protocol-based steps
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, TypeAlias

if TYPE_CHECKING:
    from reformlab.orchestrator.step import OrchestratorStep


@dataclass(frozen=True)
class YearState:
    """State carried forward between years in the orchestrator.

    Each year receives the output state from the previous year as input,
    enabling deterministic multi-year projections.

    Attributes:
        year: The simulation year this state represents.
        data: State data carried forward between years.
        seed: Random seed for this year (explicit, logged for reproducibility).
        metadata: Additional year-level metadata.
    """

    year: int
    data: dict[str, Any] = field(default_factory=dict)
    seed: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


# Type alias for step callables executed per year.
# Each step receives the year and current state, returning updated state.
YearStep: TypeAlias = Callable[[int, "YearState"], "YearState"]
PipelineStep: TypeAlias = YearStep | "OrchestratorStep"


@dataclass(frozen=True)
class OrchestratorConfig:
    """Configuration for the yearly loop orchestrator.

    Defines the projection bounds, initial state, random seed for
    determinism, and the ordered step pipeline to execute per year.

    Attributes:
        start_year: First year of projection (inclusive).
        end_year: Last year of projection (inclusive).
        initial_state: Starting state data for year 0.
        seed: Master random seed for determinism. If provided, year-level
            seeds are derived from this.
        step_pipeline: Ordered list of step callables executed per year.
    """

    start_year: int
    end_year: int
    initial_state: dict[str, Any] = field(default_factory=dict)
    seed: int | None = None
    step_pipeline: tuple[PipelineStep, ...] = ()

    def __post_init__(self) -> None:
        """Validate projection bounds and normalize step pipeline."""
        if self.end_year < self.start_year:
            raise ValueError(
                "Invalid orchestrator bounds - "
                f"end_year ({self.end_year}) must be >= start_year ({self.start_year})"
            )

        # Accept list/iterable inputs but store as an immutable tuple.
        object.__setattr__(self, "step_pipeline", tuple(self.step_pipeline))

        for index, step in enumerate(self.step_pipeline):
            # Accept both bare callables (YearStep) and protocol steps
            # Protocol steps have an execute() method; bare callables are callable
            is_callable = callable(step)
            has_execute = hasattr(step, "execute") and callable(
                getattr(step, "execute")
            )
            if not (is_callable or has_execute):
                raise TypeError(
                    "Invalid step pipeline - "
                    f"step_pipeline[{index}] not callable, no execute(): "
                    f"{type(step).__name__}"
                )


@dataclass
class OrchestratorResult:
    """Result of orchestrator execution.

    Contains success status, yearly states, and error information
    if execution failed.

    Attributes:
        success: Whether orchestration completed without errors.
        yearly_states: State at end of each year, keyed by year.
        errors: Error messages if execution failed.
        failed_year: Year when failure occurred (if any).
        failed_step: Name of the step that caused failure (if any).
        metadata: Orchestration-level metadata (timing, seed info, etc.).
    """

    success: bool
    yearly_states: dict[int, YearState] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    failed_year: int | None = None
    failed_step: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
