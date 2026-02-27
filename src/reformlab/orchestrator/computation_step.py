"""Computation step for invoking ComputationAdapter within orchestrator pipeline.

This module provides:
- ComputationStep: OrchestratorStep implementation for adapter invocation
- ComputationStepError: Error during computation step execution
- COMPUTATION_RESULT_KEY: Stable key for ComputationResult in YearState.data
- COMPUTATION_METADATA_KEY: Stable key for computation metadata in YearState.metadata

Story 3-5: Integrate ComputationAdapter calls into orchestrator yearly loop.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from reformlab.computation.adapter import ComputationAdapter
    from reformlab.computation.types import PolicyConfig, PopulationData
    from reformlab.orchestrator.types import YearState


# Stable keys for computation data in YearState
COMPUTATION_RESULT_KEY = "computation_result"
COMPUTATION_METADATA_KEY = "computation_metadata"


class ComputationStepError(Exception):
    """Error during computation step execution.

    Includes adapter version, year, and original error for debugging
    and governance tracking.
    """

    def __init__(
        self,
        message: str,
        year: int,
        adapter_version: str,
        original_error: Exception | None = None,
    ) -> None:
        self.year = year
        self.adapter_version = adapter_version
        self.original_error = original_error
        super().__init__(message)


class ComputationStep:
    """Orchestrator step for invoking ComputationAdapter per year.

    Implements the OrchestratorStep protocol to execute tax-benefit
    computations through the adapter interface at each yearly iteration.

    The step guarantees:
    - Deterministic execution (same inputs produce identical outputs)
    - Adapter invocation with correct population, policy, and period
    - Result storage in YearState.data under stable key
    - Metadata recording for governance (adapter version, period, row count)
    - Immutable state updates (returns new YearState)
    """

    __slots__ = (
        "_adapter",
        "_population",
        "_policy",
        "_name",
        "_depends_on",
        "_description",
    )

    def __init__(
        self,
        adapter: "ComputationAdapter",
        population: "PopulationData",
        policy: "PolicyConfig",
        name: str = "computation",
        depends_on: tuple[str, ...] = (),
        description: str | None = None,
    ) -> None:
        """Initialize the computation step.

        Args:
            adapter: ComputationAdapter to invoke for tax-benefit computation.
            population: PopulationData to pass to adapter.
            policy: PolicyConfig with scenario parameters.
            name: Step name for registry (default: "computation").
            depends_on: Names of steps this step depends on (default: empty).
            description: Optional description for the step.
        """
        self._adapter = adapter
        self._population = population
        self._policy = policy
        self._name = name
        self._depends_on = depends_on
        self._description = (
            description or "Computation step for tax-benefit adapter invocation"
        )

    @property
    def name(self) -> str:
        """Unique identifier for this step."""
        return self._name

    @property
    def depends_on(self) -> tuple[str, ...]:
        """Names of steps this step depends on."""
        return self._depends_on

    @property
    def description(self) -> str:
        """Human-readable description of the step."""
        return self._description

    def execute(self, year: int, state: "YearState") -> "YearState":
        """Execute computation for a given year.

        Invokes the adapter's compute() method with the configured
        population, policy, and year as period. Stores the result
        in YearState.data and execution metadata in YearState.metadata.

        Args:
            year: Current simulation year (used as computation period).
            state: Current year state.

        Returns:
            New YearState with computation result and metadata added.

        Raises:
            ComputationStepError: If adapter.compute() fails.
        """
        adapter_version = self._adapter.version()

        try:
            result = self._adapter.compute(
                population=self._population,
                policy=self._policy,
                period=year,
            )
        except Exception as e:
            raise ComputationStepError(
                message=(
                    f"Computation failed at year {year} "
                    f"(adapter: {adapter_version}): {type(e).__name__}: {e}"
                ),
                year=year,
                adapter_version=adapter_version,
                original_error=e,
            ) from e

        # Build computation metadata
        computation_metadata = {
            "adapter_version": adapter_version,
            "computation_period": year,
            "computation_row_count": result.output_fields.num_rows,
        }

        # Create new state with result and metadata
        new_data = dict(state.data)
        new_data[COMPUTATION_RESULT_KEY] = result

        new_metadata = dict(state.metadata)
        new_metadata[COMPUTATION_METADATA_KEY] = computation_metadata

        return replace(state, data=new_data, metadata=new_metadata)
