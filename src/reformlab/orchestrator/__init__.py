"""Orchestrator subsystem for multi-year projections.

This module provides the yearly loop orchestrator with step-pluggable
pipeline execution for deterministic multi-year simulations.

Public API:
- Orchestrator: Main orchestrator class for executing projections
- OrchestratorConfig: Configuration for orchestrator execution
- OrchestratorResult: Result container for orchestrator execution
- YearState: State carried between years
- YearStep: Type alias for step callables
- OrchestratorError: Structured error with execution context
- OrchestratorRunner: Runner adapter for run_workflow() integration
- from_workflow_config: Factory to create config from WorkflowConfig
- OrchestratorStep: Protocol for pipeline steps (Story 3-2)
- StepRegistry: Registration and dependency ordering for steps (Story 3-2)
- step: Decorator for function-based steps (Story 3-2)
- adapt_callable: Adapter for bare YearStep callables (Story 3-2)
- Step errors: StepValidationError, StepRegistrationError, CircularDependencyError
"""

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
]
