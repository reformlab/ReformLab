"""Public interfaces for ReformLab.

This module exports the stable Python API for running simulations
and managing scenarios.
"""

from reformlab.interfaces.api import (
    RunConfig,
    ScenarioConfig,
    SimulationResult,
    clone_scenario,
    create_quickstart_adapter,
    create_scenario,
    get_scenario,
    list_scenarios,
    run_scenario,
)
from reformlab.interfaces.errors import (
    ConfigurationError,
    SimulationError,
    ValidationErrors,
    ValidationIssue,
)

__all__ = [
    # Core API functions
    "run_scenario",
    "create_quickstart_adapter",
    "create_scenario",
    "clone_scenario",
    "list_scenarios",
    "get_scenario",
    # Result types
    "SimulationResult",
    # Configuration types
    "RunConfig",
    "ScenarioConfig",
    # Error types
    "ConfigurationError",
    "SimulationError",
    "ValidationErrors",
    "ValidationIssue",
]
