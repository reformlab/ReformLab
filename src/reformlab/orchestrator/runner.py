"""Yearly loop orchestrator implementation.

Executes a step pipeline for each year in a projection horizon,
managing deterministic state transitions and seed control.
"""

from __future__ import annotations

import logging
import traceback
from dataclasses import replace
from typing import TYPE_CHECKING, Any

from reformlab.orchestrator.errors import OrchestratorError
from reformlab.orchestrator.types import OrchestratorConfig, OrchestratorResult, YearState

if TYPE_CHECKING:
    from reformlab.orchestrator.types import YearStep
    from reformlab.templates.workflow import WorkflowConfig, WorkflowResult

logger = logging.getLogger(__name__)


class Orchestrator:
    """Yearly loop orchestrator with step pipeline execution.

    Executes an ordered step pipeline for each year from start_year
    to end_year (inclusive). Each year receives the output state from
    the previous year as input.

    The orchestrator ensures:
    - Strict year ordering (year t completes before year t+1)
    - Deterministic execution with explicit seed control
    - Clear error context on step failure with partial results
    """

    def __init__(self, config: OrchestratorConfig) -> None:
        """Initialize the orchestrator with configuration.

        Args:
            config: Orchestrator configuration with projection bounds,
                initial state, seed, and step pipeline.
        """
        self.config = config

    def run(self) -> OrchestratorResult:
        """Execute the full projection from start_year to end_year.

        Iterates through each year in the projection range, executing
        the step pipeline for each year. State is carried forward
        between years.

        Returns:
            OrchestratorResult with success status, yearly states,
            and error information if execution failed.
        """
        yearly_states: dict[int, YearState] = {}

        # Initialize state for year before start
        current_state = YearState(
            year=self.config.start_year - 1,
            data=dict(self.config.initial_state),
            seed=self._derive_year_seed(self.config.start_year - 1),
            metadata={},
        )

        logger.info(
            "Starting orchestrator run: years %d-%d with %d steps",
            self.config.start_year,
            self.config.end_year,
            len(self.config.step_pipeline),
        )

        for year in range(self.config.start_year, self.config.end_year + 1):
            logger.debug("Starting year %d", year)

            try:
                current_state = self._run_year(year, current_state)
                yearly_states[year] = current_state
                logger.debug("Completed year %d", year)

            except OrchestratorError as e:
                # Error already has context, just return failure result
                logger.error("Orchestrator failed at year %d: %s", year, e)
                return OrchestratorResult(
                    success=False,
                    yearly_states=yearly_states,
                    errors=[str(e)],
                    failed_year=e.year,
                    failed_step=e.step_name,
                    metadata={"partial": True},
                )

        logger.info(
            "Orchestrator completed successfully: %d years processed",
            len(yearly_states),
        )

        return OrchestratorResult(
            success=True,
            yearly_states=yearly_states,
            errors=[],
            failed_year=None,
            failed_step=None,
            metadata={
                "start_year": self.config.start_year,
                "end_year": self.config.end_year,
                "seed": self.config.seed,
            },
        )

    def _run_year(self, year: int, state: YearState) -> YearState:
        """Execute all steps for a single year.

        Args:
            year: The year to execute.
            state: Input state from previous year.

        Returns:
            Updated state after all steps complete.

        Raises:
            OrchestratorError: If any step fails.
        """
        # Create state for this year with appropriate seed
        current = replace(
            state,
            year=year,
            seed=self._derive_year_seed(year),
            metadata={"previous_year": state.year},
        )

        # Execute empty pipeline gracefully
        if not self.config.step_pipeline:
            logger.debug("Year %d: empty pipeline, no steps to execute", year)
            return current

        # Execute each step in order
        for step in self.config.step_pipeline:
            current = self._execute_step(step, year, current)

        return current

    def _execute_step(
        self,
        step: YearStep,
        year: int,
        state: YearState,
    ) -> YearState:
        """Execute a single step with error handling.

        Args:
            step: The step callable to execute.
            year: Current year.
            state: Current state.

        Returns:
            Updated state from step.

        Raises:
            OrchestratorError: If step raises an exception.
        """
        step_name = getattr(step, "__name__", str(step))
        logger.debug("Year %d: executing step %s", year, step_name)

        try:
            result = step(year, state)
            return result

        except Exception as e:
            # Capture full context for debugging
            tb = traceback.format_exc()
            logger.error(
                "Step %s failed at year %d: %s\n%s",
                step_name,
                year,
                e,
                tb,
            )

            raise OrchestratorError(
                summary=f"Step '{step_name}' failed",
                reason=str(e),
                year=year,
                step_name=step_name,
                partial_states={},  # Caller will fill this
                original_error=e,
            ) from e

    def _derive_year_seed(self, year: int) -> int | None:
        """Derive a deterministic seed for a specific year.

        If a master seed is configured, derives a year-specific seed
        to ensure reproducibility while allowing year-level variation.

        Args:
            year: The year to derive seed for.

        Returns:
            Year-specific seed, or None if no master seed configured.
        """
        if self.config.seed is None:
            return None

        # Simple deterministic derivation: master_seed XOR year
        # This ensures each year gets a unique but reproducible seed
        return self.config.seed ^ year


def from_workflow_config(config: "WorkflowConfig") -> OrchestratorConfig:
    """Create OrchestratorConfig from a WorkflowConfig.

    Maps workflow configuration fields to orchestrator parameters:
    - run_config.start_year -> start_year
    - run_config.projection_years -> end_year calculation

    Args:
        config: WorkflowConfig with run_config settings.

    Returns:
        OrchestratorConfig ready for execution.
    """
    start_year = config.run_config.start_year
    projection_years = config.run_config.projection_years
    end_year = start_year + projection_years - 1

    return OrchestratorConfig(
        start_year=start_year,
        end_year=end_year,
        initial_state={},
        seed=None,
        step_pipeline=(),
    )


class OrchestratorRunner:
    """Runner adapter for run_workflow() integration.

    Implements the runner interface expected by run_workflow(),
    allowing the orchestrator to be used as a workflow backend.
    """

    def __init__(
        self,
        step_pipeline: tuple["YearStep", ...] = (),
        seed: int | None = None,
        initial_state: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the runner with step configuration.

        Args:
            step_pipeline: Ordered steps to execute per year.
            seed: Master random seed for determinism.
            initial_state: Starting state for the projection.
        """
        self.step_pipeline = step_pipeline
        self.seed = seed
        self.initial_state = initial_state or {}

    def run(self, request: dict[str, Any]) -> "WorkflowResult":
        """Execute a workflow request using the orchestrator.

        Args:
            request: Workflow request dictionary from prepare_workflow_request().
                Expected keys: run_config.start_year, run_config.projection_years

        Returns:
            WorkflowResult with execution outcomes.
        """
        # Import here to avoid circular imports
        from reformlab.templates.workflow import WorkflowResult

        # Extract run configuration
        run_config = request.get("run_config", {})
        start_year = run_config.get("start_year", 2025)
        projection_years = run_config.get("projection_years", 10)
        end_year = start_year + projection_years - 1

        # Build orchestrator config
        config = OrchestratorConfig(
            start_year=start_year,
            end_year=end_year,
            initial_state=dict(self.initial_state),
            seed=self.seed,
            step_pipeline=self.step_pipeline,
        )

        # Execute orchestrator
        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        # Convert to WorkflowResult
        return WorkflowResult(
            success=result.success,
            outputs={
                "yearly_states": {
                    year: {
                        "year": state.year,
                        "data": state.data,
                        "seed": state.seed,
                        "metadata": state.metadata,
                    }
                    for year, state in result.yearly_states.items()
                },
            },
            errors=result.errors,
            metadata={
                "start_year": start_year,
                "end_year": end_year,
                "failed_year": result.failed_year,
                "failed_step": result.failed_step,
                **result.metadata,
            },
        )
