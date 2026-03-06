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
- ComputationStep: Adapter invocation step for tax-benefit computation (Story 3-5)
- ComputationStepError: Error during computation step execution (Story 3-5)
- COMPUTATION_RESULT_KEY: Stable key for ComputationResult in YearState.data (Story 3-5)
- COMPUTATION_METADATA_KEY: Stable key for computation metadata (Story 3-5)
- SEED_LOG_KEY: Stable key for seed log in metadata (Story 3-6)
- STEP_EXECUTION_LOG_KEY: Stable key for step execution log in metadata (Story 3-6)
- PanelOutput: Household-by-year panel dataset from orchestrator run (Story 3-7)
- compare_panels: Helper to compare baseline and reform panels (Story 3-7)
- PANEL_VERSION: Panel format version for metadata (Story 3-7)
- PortfolioComputationStep: Portfolio execution step (Story 12-3)
- PortfolioComputationStepError: Error during portfolio step execution (Story 12-3)
- PORTFOLIO_METADATA_KEY: Stable key for portfolio metadata (Story 12-3)
- PORTFOLIO_RESULTS_KEY: Stable key for per-policy results (Story 12-3)
"""

from reformlab.orchestrator.carry_forward import (
    CarryForwardConfig,
    CarryForwardConfigError,
    CarryForwardExecutionError,
    CarryForwardRule,
    CarryForwardStep,
)
from reformlab.orchestrator.computation_step import (
    COMPUTATION_METADATA_KEY,
    COMPUTATION_RESULT_KEY,
    ComputationStep,
    ComputationStepError,
)
from reformlab.orchestrator.errors import OrchestratorError
from reformlab.orchestrator.panel import PANEL_VERSION, PanelOutput, compare_panels
from reformlab.orchestrator.portfolio_step import (
    PORTFOLIO_METADATA_KEY,
    PORTFOLIO_RESULTS_KEY,
    PortfolioComputationStep,
    PortfolioComputationStepError,
)
from reformlab.orchestrator.runner import (
    SEED_LOG_KEY,
    STEP_EXECUTION_LOG_KEY,
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
    # Computation step (Story 3-5)
    "ComputationStep",
    "ComputationStepError",
    "COMPUTATION_RESULT_KEY",
    "COMPUTATION_METADATA_KEY",
    # Logging keys (Story 3-6)
    "SEED_LOG_KEY",
    "STEP_EXECUTION_LOG_KEY",
    # Panel output (Story 3-7)
    "PanelOutput",
    "compare_panels",
    "PANEL_VERSION",
    # Portfolio step (Story 12-3)
    "PortfolioComputationStep",
    "PortfolioComputationStepError",
    "PORTFOLIO_METADATA_KEY",
    "PORTFOLIO_RESULTS_KEY",
]
