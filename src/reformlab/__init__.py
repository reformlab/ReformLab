"""ReformLab: OpenFisca-first environmental policy analysis platform.

ReformLab builds data preparation, scenario templates, dynamic multi-year
orchestration with vintage tracking, indicators, governance, and user
interfaces on top of OpenFisca's tax-benefit computation engine.

Public API:
-----------
The stable Python API for running simulations and managing scenarios.

Core functions:
    - run_scenario: Execute a complete simulation (accepts typed scenarios or RunConfig)
    - load_population: Load population data from CSV/Parquet
    - run_benchmarks: Run benchmark validation suite
    - check_memory_requirements: Preflight memory-risk check before execution
    - create_scenario: Create and optionally register a scenario
    - clone_scenario: Clone an existing scenario
    - list_scenarios: List all registered scenarios
    - get_scenario: Get a scenario from the registry

Result types:
    - SimulationResult: Result of a simulation run

Configuration types:
    - RunConfig: Configuration for running a simulation (legacy path)
    - ScenarioConfig: Configuration for a scenario (legacy path)
    - MemoryCheckResult: Result payload from memory preflight checks

Error types:
    - ConfigurationError: Invalid configuration before execution
    - MemoryWarning: Memory-risk warning category for preflight alerts
    - SimulationError: Execution failure during simulation

Example usage (direct scenario):
---------------------------------
    >>> from reformlab import run_scenario, load_population
    >>> from reformlab.templates.schema import (
    ...     BaselineScenario, CarbonTaxParameters, PolicyType, YearSchedule,
    ... )
    >>> scenario = BaselineScenario(
    ...     name="carbon-tax-2025",
    ...     policy_type=PolicyType.CARBON_TAX,
    ...     year_schedule=YearSchedule(start_year=2025, end_year=2030),
    ...     policy=CarbonTaxParameters(rate_schedule={2025: 50.0}),
    ... )
    >>> population = load_population("data/populations/demo.csv")
    >>> result = run_scenario(scenario, population=population, seed=42)
    >>> print(result)
    SimulationResult(SUCCESS, scenario='carbon-tax-2025', years=2025-2030, ...)

Example usage (config-based, legacy):
--------------------------------------
    >>> from reformlab import run_scenario, RunConfig, ScenarioConfig
    >>> config = RunConfig(
    ...     scenario=ScenarioConfig(
    ...         template_name="carbon-tax",
    ...         policy={"rate_schedule": {2025: 50.0}},
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
    SimpleCarbonTaxAdapter,
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
    load_population,
    run_benchmarks,
    run_scenario,
)
from reformlab.vintage import (
    VintageCohort,
    VintageConfig,
    VintageConfigError,
    VintageState,
    VintageSummary,
    VintageTransitionError,
    VintageTransitionRule,
    VintageTransitionStep,
)
from reformlab.visualization import create_figure, show, style_axes

__version__ = "0.1.0"

__all__ = [
    # Core API functions
    "run_scenario",
    "load_population",
    "run_benchmarks",
    "check_memory_requirements",
    "SimpleCarbonTaxAdapter",
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
    # Vintage types
    "VintageCohort",
    "VintageConfig",
    "VintageConfigError",
    "VintageState",
    "VintageSummary",
    "VintageTransitionError",
    "VintageTransitionRule",
    "VintageTransitionStep",
    # Visualization utilities
    "show",
    "create_figure",
    "style_axes",
    # Metadata
    "__version__",
]
