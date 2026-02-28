"""ReformLab: OpenFisca-first environmental policy analysis platform.

ReformLab builds data preparation, scenario templates, dynamic multi-year
orchestration with vintage tracking, indicators, governance, and user
interfaces on top of OpenFisca's tax-benefit computation engine.

Public API:
-----------
The stable Python API for running simulations and managing scenarios.

Core functions:
    - run_scenario: Execute a complete simulation
    - run_benchmarks: Run benchmark validation suite
    - check_memory_requirements: Preflight memory-risk check before execution
    - create_scenario: Create and optionally register a scenario
    - clone_scenario: Clone an existing scenario
    - list_scenarios: List all registered scenarios
    - get_scenario: Get a scenario from the registry

Result types:
    - SimulationResult: Result of a simulation run

Configuration types:
    - RunConfig: Configuration for running a simulation
    - ScenarioConfig: Configuration for a scenario
    - MemoryCheckResult: Result payload from memory preflight checks

Error types:
    - ConfigurationError: Invalid configuration before execution
    - MemoryWarning: Memory-risk warning category for preflight alerts
    - SimulationError: Execution failure during simulation

Example usage:
--------------
    >>> from reformlab import run_scenario, RunConfig, ScenarioConfig
    >>> config = RunConfig(
    ...     scenario=ScenarioConfig(
    ...         template_name="carbon-tax",
    ...         parameters={"rate_schedule": {2025: 50.0}},
    ...         start_year=2025,
    ...         end_year=2030,
    ...     ),
    ...     seed=42,
    ... )
    >>> result = run_scenario(config)
    >>> print(result)
    SimulationResult(SUCCESS, scenario='carbon-tax', years=2025-2030, ...)

For more details, see the documentation at: https://reformlab.readthedocs.io
"""

from reformlab.interfaces import (
    ConfigurationError,
    MemoryCheckResult,
    MemoryWarning,
    PopulationResult,
    RunConfig,
    ScenarioConfig,
    SimulationError,
    SimulationResult,
    ValidationErrors,
    ValidationIssue,
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

__version__ = "0.1.0"

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
    # Metadata
    "__version__",
]
