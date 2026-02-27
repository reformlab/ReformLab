"""ReformLab: OpenFisca-first environmental policy analysis platform.

ReformLab builds data preparation, scenario templates, dynamic multi-year
orchestration with vintage tracking, indicators, governance, and user
interfaces on top of OpenFisca's tax-benefit computation engine.

Public API:
-----------
The stable Python API for running simulations and managing scenarios.

Core functions:
    - run_scenario: Execute a complete simulation
    - create_scenario: Create and optionally register a scenario
    - clone_scenario: Clone an existing scenario
    - list_scenarios: List all registered scenarios
    - get_scenario: Get a scenario from the registry

Result types:
    - SimulationResult: Result of a simulation run

Configuration types:
    - RunConfig: Configuration for running a simulation
    - ScenarioConfig: Configuration for a scenario

Error types:
    - ConfigurationError: Invalid configuration before execution
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
    RunConfig,
    ScenarioConfig,
    SimulationError,
    SimulationResult,
    ValidationErrors,
    ValidationIssue,
    clone_scenario,
    create_quickstart_adapter,
    create_scenario,
    get_scenario,
    list_scenarios,
    run_scenario,
)

__version__ = "0.1.0"

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
    # Metadata
    "__version__",
]
