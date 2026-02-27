"""Orchestrator subsystem for multi-year projections.

This module provides the yearly loop orchestrator with step-pluggable
pipeline execution for deterministic multi-year simulations.

Public API:
- Orchestrator: Main orchestrator class for executing projections
- OrchestratorConfig: Configuration for orchestrator execution
- OrchestratorResult: Result container for orchestrator execution
- YearState: State carried between years
- YearStep: Type alias for step callables
- PipelineStep: Union type for callable and protocol-based steps
- OrchestratorError: Structured error with execution context
- OrchestratorRunner: Runner adapter for run_workflow() integration
- from_workflow_config: Factory to create config from WorkflowConfig
- OrchestratorStep: Protocol for pipeline steps (Story 3-2)
- StepRegistry: Registration and dependency ordering for steps (Story 3-2)
- step: Decorator for function-based steps (Story 3-2)
- adapt_callable: Adapter for bare YearStep callables (Story 3-2)
- Step errors: StepValidationError, StepRegistrationError, CircularDependencyError
- CarryForwardStep: Deterministic state carry-forward step (Story 3-3)
- CarryForwardConfig: Configuration for carry-forward rules (Story 3-3)
- CarryForwardRule: Single variable update rule (Story 3-3)
- CarryForwardConfigError: Invalid carry-forward configuration (Story 3-3)
- CarryForwardExecutionError: Error during carry-forward execution (Story 3-3)
"""

from reformlab.orchestrator.carry_forward import (
    CarryForwardConfig,
    CarryForwardConfigError,
    CarryForwardExecutionError,
    CarryForwardRule,
    CarryForwardStep,
)
from reformlab.orchestrator.errors import OrchestratorError
from reformlab.orchestrator.runner import (
    Orchestrator,
    OrchestratorRunner,
    from_workflow_config,
)
from reformlab.orchestrator.step import (
    CircularDependencyError,
    OrchestratorStep,
    StepRegistrationError,
    StepRegistry,
    StepValidationError,
    adapt_callable,
    is_protocol_step,
    step,
)
from reformlab.orchestrator.types import (
    OrchestratorConfig,
    OrchestratorResult,
    PipelineStep,
    YearState,
    YearStep,
)

__all__ = [
    # Core orchestrator
    "Orchestrator",
    "OrchestratorConfig",
    "OrchestratorError",
    "OrchestratorResult",
    "OrchestratorRunner",
    "PipelineStep",
    "YearState",
    "YearStep",
    "from_workflow_config",
    # Step interface (Story 3-2)
    "OrchestratorStep",
    "StepRegistry",
    "step",
    "adapt_callable",
    "is_protocol_step",
    # Step errors (Story 3-2)
    "StepValidationError",
    "StepRegistrationError",
    "CircularDependencyError",
    # Carry-forward step (Story 3-3)
    "CarryForwardStep",
    "CarryForwardConfig",
    "CarryForwardRule",
    "CarryForwardConfigError",
    "CarryForwardExecutionError",
]
