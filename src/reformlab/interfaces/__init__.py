"""Public interfaces for ReformLab.

This module exports the stable Python API for running simulations
and managing scenarios, including memory preflight checks.
"""

from reformlab.interfaces.api import (
    MemoryCheckResult,
    RunConfig,
    ScenarioConfig,
    SimulationResult,
    check_memory_requirements,
    clone_scenario,
    create_quickstart_adapter,
    create_scenario,
    get_scenario,
    list_scenarios,
    run_benchmarks,
    run_scenario,
)
from reformlab.interfaces.errors import (
    ConfigurationError,
    MemoryWarning,
    SimulationError,
    ValidationErrors,
    ValidationIssue,
)

__all__ = [
    # Core API functions
    "run_scenario",
    "run_benchmarks",
    "check_memory_requirements",
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
    "MemoryCheckResult",
    # Error types
    "ConfigurationError",
    "MemoryWarning",
    "SimulationError",
    "ValidationErrors",
    "ValidationIssue",
]
