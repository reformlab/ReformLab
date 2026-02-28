"""Public interfaces for ReformLab.

This module exports the stable Python API for running simulations
and managing scenarios, including memory preflight checks.
"""

from reformlab.interfaces.api import (
    MemoryCheckResult,
    PopulationResult,
    RunConfig,
    ScenarioConfig,
    SimulationResult,
    check_memory_requirements,
    clone_scenario,
    create_quickstart_adapter,
    create_scenario,
    generate_population,
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
    "generate_population",
    "list_scenarios",
    "get_scenario",
    # Result types
    "PopulationResult",
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
