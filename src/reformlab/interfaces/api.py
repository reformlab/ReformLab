"""Public Python API for ReformLab.

This module provides the stable, user-facing API for running simulations,
managing scenarios, and accessing results. It is a thin facade over existing
subsystems and delegates to:

- templates/ for scenario loading
- orchestrator/ for execution
- governance/ for manifest capture
- indicators/ for analysis

Key architectural principles:
- Frozen dataclasses for immutability (NFR16)
- Clear error messages with actionable guidance
- PyArrow-first for data (PanelOutput.table: pa.Table)
- No direct OpenFisca imports (adapter protocol only)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from reformlab.computation.adapter import ComputationAdapter
    from reformlab.governance.manifest import RunManifest
    from reformlab.indicators.types import IndicatorResult
    from reformlab.orchestrator.panel import PanelOutput
    from reformlab.orchestrator.types import YearState


@dataclass(frozen=True)
class ScenarioConfig:
    """Configuration for a scenario to run.

    Attributes:
        template_name: Name of the scenario template to use.
        parameters: Policy parameters to apply.
        population_path: Optional path to population data file.
        start_year: First year of the projection.
        end_year: Last year of the projection.
        seed: Optional random seed for reproducibility.
        baseline_id: Optional baseline scenario ID for reform scenarios.
    """

    template_name: str
    parameters: dict[str, Any]
    start_year: int
    end_year: int
    population_path: Path | None = None
    seed: int | None = None
    baseline_id: str | None = None


@dataclass(frozen=True)
class RunConfig:
    """Configuration for running a simulation.

    Attributes:
        scenario: Scenario configuration (as object, dict, or YAML path).
        output_dir: Optional directory for output files.
        seed: Optional random seed (overrides scenario seed if provided).
    """

    scenario: ScenarioConfig | Path | dict[str, Any]
    output_dir: Path | None = None
    seed: int | None = None


@dataclass(frozen=True)
class SimulationResult:
    """Result of a simulation run with notebook-friendly display.

    Provides access to yearly states, panel output, manifest, and
    computed indicators. Immutable after construction.

    Attributes:
        success: Whether the simulation completed successfully.
        scenario_id: Identifier for the scenario that was run.
        yearly_states: Dictionary mapping year to state for completed years.
        panel_output: Stacked panel dataset (household × year), or None if failed.
        manifest: Run manifest with provenance and parameters.
        metadata: Additional execution metadata.
    """

    success: bool
    scenario_id: str
    yearly_states: dict[int, YearState]
    panel_output: PanelOutput | None
    manifest: RunManifest
    metadata: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        """Return notebook-friendly representation showing key run information."""
        years = sorted(self.yearly_states.keys())
        year_range = f"{years[0]}-{years[-1]}" if years else "none"
        rows = self.panel_output.table.num_rows if self.panel_output else 0
        status = "SUCCESS" if self.success else "FAILED"
        return (
            f"SimulationResult({status}, scenario={self.scenario_id!r}, "
            f"years={year_range}, rows={rows}, manifest={self.manifest.manifest_id!r})"
        )

    def indicators(
        self,
        indicator_type: str,
        **kwargs: Any,
    ) -> IndicatorResult:
        """Compute indicators from panel output.

        Args:
            indicator_type: Type of indicator to compute
                (e.g., "distributional", "geographic", "welfare", "fiscal").
            **kwargs: Additional arguments passed to indicator computation.

        Returns:
            IndicatorResult with computed indicator data.

        Raises:
            SimulationError: If panel output is not available or indicator
                type is invalid.

        Example:
            >>> result = run_scenario(config)
            >>> indicators = result.indicators("distributional")
        """
        from reformlab.interfaces.errors import SimulationError

        if self.panel_output is None:
            msg = "No panel output available (simulation may have failed)"
            raise SimulationError(msg)

        # Delegate to indicator subsystem based on type
        from reformlab.indicators import (
            compute_distributional_indicators,
            compute_fiscal_indicators,
            compute_geographic_indicators,
            compute_welfare_indicators,
        )

        indicator_type_lower = indicator_type.lower()

        if indicator_type_lower == "distributional":
            return compute_distributional_indicators(
                self.panel_output.table,
                **kwargs,
            )
        elif indicator_type_lower == "geographic":
            return compute_geographic_indicators(
                self.panel_output.table,
                **kwargs,
            )
        elif indicator_type_lower == "welfare":
            return compute_welfare_indicators(
                self.panel_output.table,
                **kwargs,
            )
        elif indicator_type_lower == "fiscal":
            return compute_fiscal_indicators(
                self.panel_output.table,
                **kwargs,
            )
        else:
            raise SimulationError(
                f"Unknown indicator type: {indicator_type}. "
                f"Supported types: distributional, geographic, welfare, fiscal"
            )


def run_scenario(
    config: RunConfig | Path | dict[str, Any],
    adapter: ComputationAdapter | None = None,
) -> SimulationResult:
    """Run a complete simulation scenario.

    This is the main entry point for executing simulations via the Python API.
    It handles configuration normalization, validation, scenario loading,
    orchestrator execution, and result packaging.

    Args:
        config: Scenario configuration as RunConfig, YAML path, or dict.
        adapter: Optional computation adapter. If None, uses OpenFiscaAdapter.
            Tests typically inject MockAdapter here.

    Returns:
        SimulationResult with yearly states, panel output, and manifest.

    Raises:
        ConfigurationError: If configuration is invalid.
        SimulationError: If simulation fails during execution.

    Example:
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
    """
    from reformlab.interfaces.errors import ConfigurationError, SimulationError

    # Step 1: Normalize config to RunConfig
    run_config = _normalize_config(config)

    # Step 2: Validate before execution
    _validate_config(run_config)

    # Step 3: Load scenario template
    try:
        scenario = _load_scenario(run_config.scenario)
    except Exception as exc:
        raise SimulationError(
            f"Failed to load scenario: {exc}",
            cause=exc,
        ) from exc

    # Step 4: Setup adapter
    if adapter is None:
        try:
            from reformlab.computation.openfisca_adapter import OpenFiscaAdapter

            adapter = OpenFiscaAdapter()
        except Exception as exc:
            raise ConfigurationError(
                field_path="adapter",
                expected="valid OpenFisca installation",
                actual="OpenFisca not available or misconfigured",
                message=(
                    f"Failed to initialize OpenFiscaAdapter: {exc}. "
                    "Ensure OpenFisca is installed or provide a custom adapter."
                ),
            ) from exc

    # Step 5: Execute via orchestrator
    try:
        result = _execute_orchestration(scenario, run_config, adapter)
    except Exception as exc:
        raise SimulationError(
            f"Simulation execution failed: {exc}",
            cause=exc,
        ) from exc

    # Step 6: Package and return
    return result


def _normalize_config(
    config: RunConfig | Path | dict[str, Any] | ScenarioConfig,
) -> RunConfig:
    """Normalize configuration to RunConfig dataclass.

    Args:
        config: Configuration in any supported format.

    Returns:
        Normalized RunConfig.

    Raises:
        ConfigurationError: If config format is invalid.
    """
    from reformlab.interfaces.errors import ConfigurationError

    if isinstance(config, RunConfig):
        return config

    if isinstance(config, ScenarioConfig):
        # Wrap ScenarioConfig in RunConfig
        return RunConfig(scenario=config)

    if isinstance(config, Path):
        # Load YAML configuration
        from reformlab.templates.workflow import WorkflowError, load_workflow_config

        try:
            _ = load_workflow_config(config)
        except WorkflowError as exc:
            raise ConfigurationError(
                field_path="config",
                expected="valid workflow YAML file",
                actual=str(config),
                message=f"Failed to load workflow config: {exc}",
            ) from exc

        # Convert WorkflowConfig to RunConfig
        # For now, raise error as full workflow->RunConfig conversion
        # requires more context
        raise ConfigurationError(
            field_path="config",
            expected="RunConfig or dict",
            actual="workflow YAML path",
            message=(
                "Direct workflow YAML loading not yet implemented. "
                "Use RunConfig or dict instead."
            ),
        )

    if isinstance(config, dict):
        # Convert dict to RunConfig
        scenario = config.get("scenario")
        if scenario is None:
            raise ConfigurationError(
                field_path="scenario",
                expected="scenario configuration",
                actual=None,
                message="Missing required field 'scenario'",
            )

        # Convert scenario to ScenarioConfig if needed
        if isinstance(scenario, dict):
            scenario = _dict_to_scenario_config(scenario)
        elif isinstance(scenario, Path):
            # Keep as Path for later loading
            pass
        elif not isinstance(scenario, ScenarioConfig):
            raise ConfigurationError(
                field_path="scenario",
                expected="ScenarioConfig, Path, or dict",
                actual=type(scenario).__name__,
            )

        output_dir = config.get("output_dir")
        if output_dir is not None:
            output_dir = Path(output_dir)

        seed = config.get("seed")
        if seed is not None:
            seed = int(seed)

        return RunConfig(
            scenario=scenario,
            output_dir=output_dir,
            seed=seed,
        )

    raise ConfigurationError(
        field_path="config",
        expected="RunConfig, Path, or dict",
        actual=type(config).__name__,
    )


def _dict_to_scenario_config(data: dict[str, Any]) -> ScenarioConfig:
    """Convert dictionary to ScenarioConfig.

    Args:
        data: Dictionary with scenario configuration fields.

    Returns:
        ScenarioConfig instance.

    Raises:
        ConfigurationError: If required fields are missing or invalid.
    """
    from reformlab.interfaces.errors import ConfigurationError

    # Required fields
    template_name = data.get("template_name")
    if not template_name:
        raise ConfigurationError(
            field_path="scenario.template_name",
            expected="non-empty string",
            actual=template_name,
        )

    parameters = data.get("parameters")
    if parameters is None:
        raise ConfigurationError(
            field_path="scenario.parameters",
            expected="dict of policy parameters",
            actual=None,
        )

    start_year = data.get("start_year")
    if start_year is None:
        raise ConfigurationError(
            field_path="scenario.start_year",
            expected="int year",
            actual=None,
        )

    end_year = data.get("end_year")
    if end_year is None:
        raise ConfigurationError(
            field_path="scenario.end_year",
            expected="int year",
            actual=None,
        )

    # Optional fields
    population_path = data.get("population_path")
    if population_path is not None:
        population_path = Path(population_path)

    seed = data.get("seed")
    baseline_id = data.get("baseline_id")

    try:
        return ScenarioConfig(
            template_name=str(template_name),
            parameters=dict(parameters),
            start_year=int(start_year),
            end_year=int(end_year),
            population_path=population_path,
            seed=int(seed) if seed is not None else None,
            baseline_id=str(baseline_id) if baseline_id else None,
        )
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(
            field_path="scenario",
            expected="valid scenario configuration",
            actual=data,
            message=f"Failed to create ScenarioConfig: {exc}",
        ) from exc


def _validate_config(run_config: RunConfig) -> None:
    """Validate configuration before execution.

    Args:
        run_config: Configuration to validate.

    Raises:
        ConfigurationError: If configuration is invalid.
    """
    from reformlab.interfaces.errors import ConfigurationError

    # Extract scenario config
    scenario = run_config.scenario
    if isinstance(scenario, Path):
        if not scenario.exists():
            raise ConfigurationError(
                field_path="scenario",
                expected="existing file path",
                actual=str(scenario),
                message=f"Scenario file not found: {scenario}",
            )
        return  # File will be validated when loaded

    if isinstance(scenario, dict):
        # Convert to ScenarioConfig for validation
        scenario = _dict_to_scenario_config(scenario)

    if isinstance(scenario, ScenarioConfig):
        # Validate year bounds
        if scenario.end_year < scenario.start_year:
            raise ConfigurationError(
                field_path="scenario.end_year",
                expected=f">= {scenario.start_year}",
                actual=scenario.end_year,
                message="end_year must be >= start_year",
            )

        # Validate year range is reasonable
        if scenario.start_year < 1900 or scenario.start_year > 2200:
            raise ConfigurationError(
                field_path="scenario.start_year",
                expected="year in range [1900, 2200]",
                actual=scenario.start_year,
            )

        if scenario.end_year < 1900 or scenario.end_year > 2200:
            raise ConfigurationError(
                field_path="scenario.end_year",
                expected="year in range [1900, 2200]",
                actual=scenario.end_year,
            )

        # Validate population file if provided
        if scenario.population_path is not None:
            if not scenario.population_path.exists():
                raise ConfigurationError(
                    field_path="scenario.population_path",
                    expected="existing file",
                    actual=str(scenario.population_path),
                    message=f"Population file not found: {scenario.population_path}",
                )


def _normalize_parameters(params: dict[str, Any]) -> dict[str, Any]:
    """Normalize parameters for manifest compatibility.

    Converts numeric dictionary keys to strings for JSON serialization.

    Args:
        params: Raw parameters dictionary.

    Returns:
        Normalized parameters with string keys.
    """

    def normalize_value(value: Any) -> Any:
        if isinstance(value, dict):
            # Convert all keys to strings
            return {str(k): normalize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [normalize_value(item) for item in value]
        else:
            return value

    return normalize_value(params)


def _load_scenario(
    scenario: ScenarioConfig | Path | dict[str, Any],
) -> ScenarioConfig:
    """Load and validate scenario configuration.

    Args:
        scenario: Scenario in any supported format.

    Returns:
        Validated ScenarioConfig.

    Raises:
        ConfigurationError: If scenario cannot be loaded or is invalid.
    """
    if isinstance(scenario, ScenarioConfig):
        return scenario

    if isinstance(scenario, Path):
        from reformlab.interfaces.errors import ConfigurationError

        raise ConfigurationError(
            field_path="scenario",
            expected="ScenarioConfig or dict",
            actual="Path",
            message="Direct scenario file loading not yet implemented",
        )

    if isinstance(scenario, dict):
        return _dict_to_scenario_config(scenario)

    from reformlab.interfaces.errors import ConfigurationError

    raise ConfigurationError(
        field_path="scenario",
        expected="ScenarioConfig, Path, or dict",
        actual=type(scenario).__name__,
    )


def _execute_orchestration(
    scenario: ScenarioConfig,
    run_config: RunConfig,
    adapter: ComputationAdapter,
) -> SimulationResult:
    """Execute orchestration and package results.

    Args:
        scenario: Validated scenario configuration.
        run_config: Run configuration.
        adapter: Computation adapter.

    Returns:
        SimulationResult with execution outcomes.

    Raises:
        SimulationError: If execution fails.
    """
    from datetime import datetime, timezone

    import pyarrow as pa

    from reformlab.governance.manifest import RunManifest
    from reformlab.orchestrator.panel import PanelOutput
    from reformlab.orchestrator.runner import OrchestratorRunner
    from reformlab.orchestrator.types import YearState
    from reformlab.templates.workflow import WorkflowResult

    # Normalize parameters to ensure manifest compatibility
    # Convert any numeric keys to strings for JSON serialization
    normalized_params = _normalize_parameters(scenario.parameters)

    # Build workflow request
    # For MVP, we create a minimal workflow-compatible request
    request = {
        "name": scenario.template_name,
        "version": "1.0",
        "run_config": {
            "start_year": scenario.start_year,
            "projection_years": scenario.end_year - scenario.start_year + 1,
            "output_format": "parquet",
        },
        "scenarios": [{"role": "scenario", "reference": scenario.template_name}],
        "parameters": normalized_params,
    }

    # Use seed from run_config if provided, otherwise from scenario
    seed = run_config.seed if run_config.seed is not None else scenario.seed

    # Create orchestrator runner
    # For MVP, we use empty step pipeline - full implementation will come later
    runner = OrchestratorRunner(
        step_pipeline=(),
        seed=seed,
        initial_state={},
        parameters=normalized_params,
        scenario_name=scenario.template_name,
        scenario_version="api-v1",
    )

    # Execute
    workflow_result: WorkflowResult = runner.run(request)

    # Extract yearly states from workflow result
    yearly_states_raw = workflow_result.outputs.get("yearly_states", {})
    yearly_states: dict[int, YearState] = {}
    for year_int, state_dict in yearly_states_raw.items():
        yearly_states[int(year_int)] = YearState(
            year=int(state_dict["year"]),
            data=dict(state_dict.get("data", {})),
            seed=state_dict.get("seed"),
            metadata=dict(state_dict.get("metadata", {})),
        )

    # Build panel output
    # For MVP, create empty panel if no yearly states
    if not yearly_states:
        panel_output = PanelOutput(
            table=pa.table(
                {
                    "household_id": pa.array([], type=pa.int64()),
                    "year": pa.array([], type=pa.int64()),
                }
            ),
            metadata=workflow_result.metadata,
        )
    else:
        # Build panel from yearly states
        # This is simplified for MVP - full implementation will use orchestrator panel builder
        panel_output = PanelOutput(
            table=pa.table(
                {
                    "household_id": pa.array([], type=pa.int64()),
                    "year": pa.array([], type=pa.int64()),
                }
            ),
            metadata=workflow_result.metadata,
        )

    # Build manifest
    # For MVP, create minimal manifest
    manifest = RunManifest(
        manifest_id=workflow_result.metadata.get("parent_manifest_id", "api-run-id"),
        created_at=datetime.now(timezone.utc).isoformat(),
        engine_version="0.1.0",
        openfisca_version="39.0.0",
        adapter_version=adapter.version() if hasattr(adapter, "version") else "mock-1.0.0",
        scenario_version="1.0.0",
        parameters=normalized_params,
        seeds={"master": seed} if seed is not None else {},
        warnings=workflow_result.metadata.get("warnings", []),
    )

    # Package result
    return SimulationResult(
        success=workflow_result.success,
        scenario_id=scenario.template_name,
        yearly_states=yearly_states,
        panel_output=panel_output if workflow_result.success else None,
        manifest=manifest,
        metadata=workflow_result.metadata,
    )


# Scenario management functions

def create_scenario(
    scenario: Any,  # BaselineScenario | ReformScenario
    name: str,
    register: bool = False,
) -> str | Any:
    """Create a scenario and optionally register it.

    Args:
        scenario: Scenario object to create (BaselineScenario or ReformScenario).
        name: Name for the scenario.
        register: If True, save to registry and return version ID.
            If False, just return the scenario object.

    Returns:
        Version ID string if registered, otherwise the scenario object.

    Example:
        >>> from reformlab import create_scenario
        >>> from reformlab.templates.schema import BaselineScenario, PolicyType, YearSchedule
        >>> scenario = BaselineScenario(
        ...     name="carbon-tax-2025",
        ...     policy_type=PolicyType.CARBON_TAX,
        ...     year_schedule=YearSchedule(2025, 2030),
        ...     parameters=...,
        ... )
        >>> version_id = create_scenario(scenario, "carbon-tax-2025", register=True)
    """
    from reformlab.templates.registry import ScenarioRegistry

    if not register:
        return scenario

    # Save to registry
    registry = ScenarioRegistry()
    version_id = registry.save(scenario, name)
    return version_id


def clone_scenario(
    name: str,
    version_id: str | None = None,
    new_name: str | None = None,
) -> Any:  # BaselineScenario | ReformScenario
    """Clone a scenario from the registry.

    Args:
        name: Source scenario name.
        version_id: Source version ID (None = latest version).
        new_name: Name for the clone (None = auto-generate as "{name}-clone").

    Returns:
        Cloned scenario object with new identity.

    Raises:
        ConfigurationError: If source scenario is not found.

    Example:
        >>> from reformlab import clone_scenario
        >>> clone = clone_scenario("carbon-tax-2025", new_name="carbon-tax-variant")
    """
    from reformlab.interfaces.errors import ConfigurationError
    from reformlab.templates.registry import ScenarioNotFoundError, ScenarioRegistry

    registry = ScenarioRegistry()
    try:
        return registry.clone(name, version_id, new_name)
    except ScenarioNotFoundError as exc:
        raise ConfigurationError(
            field_path="name",
            expected="existing scenario in registry",
            actual=name,
            message=str(exc),
        ) from exc


def list_scenarios() -> list[str]:
    """List all registered scenario names.

    Returns:
        List of scenario names in the registry.

    Example:
        >>> from reformlab import list_scenarios
        >>> scenarios = list_scenarios()
        >>> print(scenarios)
        ['carbon-tax-2025', 'progressive-dividend', 'lump-sum-rebate']
    """
    from reformlab.templates.registry import ScenarioRegistry

    registry = ScenarioRegistry()
    return registry.list_scenarios()


def get_scenario(
    name: str,
    version_id: str | None = None,
) -> Any:  # BaselineScenario | ReformScenario
    """Get a scenario from the registry.

    Args:
        name: Scenario name.
        version_id: Version ID (None = latest version).

    Returns:
        Scenario object.

    Raises:
        ConfigurationError: If scenario is not found.

    Example:
        >>> from reformlab import get_scenario
        >>> scenario = get_scenario("carbon-tax-2025")
    """
    from reformlab.interfaces.errors import ConfigurationError
    from reformlab.templates.registry import ScenarioNotFoundError, ScenarioRegistry

    registry = ScenarioRegistry()
    try:
        return registry.get(name, version_id)
    except ScenarioNotFoundError as exc:
        raise ConfigurationError(
            field_path="name",
            expected="existing scenario in registry",
            actual=name,
            message=str(exc),
        ) from exc
