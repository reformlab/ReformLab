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
"""

from reformlab.orchestrator.errors import OrchestratorError
from reformlab.orchestrator.runner import (
    Orchestrator,
    OrchestratorRunner,
    from_workflow_config,
)
from reformlab.orchestrator.types import (
    OrchestratorConfig,
    OrchestratorResult,
    YearState,
    YearStep,
)

__all__ = [
    "Orchestrator",
    "OrchestratorConfig",
    "OrchestratorError",
    "OrchestratorResult",
    "OrchestratorRunner",
    "YearState",
    "YearStep",
    "from_workflow_config",
]
