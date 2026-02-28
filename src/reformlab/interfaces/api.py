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

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import yaml

if TYPE_CHECKING:
    from reformlab.computation.adapter import ComputationAdapter
    from reformlab.governance.benchmarking import BenchmarkSuiteResult
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
            msg = "Operation failed — No panel output available — Ensure the simulation completed successfully"
            raise SimulationError(msg, fix="Ensure the simulation completed successfully")

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
                self.panel_output,
                **kwargs,
            )
        elif indicator_type_lower == "geographic":
            return compute_geographic_indicators(
                self.panel_output,
                **kwargs,
            )
        elif indicator_type_lower == "welfare":
            reform_panel = kwargs.pop("reform_panel", None)
            reform_result = kwargs.pop("reform_result", None)

            if reform_panel is None and reform_result is not None:
                reform_panel = getattr(reform_result, "panel_output", None)

            if reform_panel is None:
                raise SimulationError(
                    "Welfare indicator computation failed — No reform panel provided — Pass reform_result=<SimulationResult> or reform_panel=<PanelOutput>",
                    fix="Pass reform_result=<SimulationResult> or reform_panel=<PanelOutput>",
                )

            return compute_welfare_indicators(
                self.panel_output,
                reform_panel,
                **kwargs,
            )
        elif indicator_type_lower == "fiscal":
            return compute_fiscal_indicators(
                self.panel_output,
                **kwargs,
            )
        else:
            raise SimulationError(
                f"Indicator computation failed — Unknown indicator type '{indicator_type}' — Use one of: distributional, geographic, welfare, fiscal",
                fix="Use one of the supported indicator types: distributional, geographic, welfare, fiscal",
            )

    def export_csv(self, path: str | Path) -> Path:
        """Export simulation panel output to CSV file.

        Args:
            path: Destination file path for CSV export.

        Returns:
            Path to the written CSV file.

        Raises:
            SimulationError: If panel output is not available.

        Example:
            >>> result = run_scenario(config)
            >>> output_path = result.export_csv("output/simulation.csv")
        """
        from reformlab.interfaces.errors import SimulationError

        if self.panel_output is None:
            msg = "Operation failed — No panel output available — Ensure the simulation completed successfully"
            raise SimulationError(msg, fix="Ensure the simulation completed successfully")

        return self.panel_output.to_csv(path)

    def export_parquet(self, path: str | Path) -> Path:
        """Export simulation panel output to Parquet file.

        Parquet export includes run provenance metadata in the schema metadata,
        including manifest ID and engine version context for traceability.

        Args:
            path: Destination file path for Parquet export.

        Returns:
            Path to the written Parquet file.

        Raises:
            SimulationError: If panel output is not available.

        Example:
            >>> result = run_scenario(config)
            >>> output_path = result.export_parquet("output/simulation.parquet")
        """
        from reformlab.interfaces.errors import SimulationError

        if self.panel_output is None:
            msg = "Operation failed — No panel output available — Ensure the simulation completed successfully"
            raise SimulationError(msg, fix="Ensure the simulation completed successfully")

        provenance_metadata = {
            "reformlab_manifest_id": self.manifest.manifest_id,
            "reformlab_manifest_created_at": self.manifest.created_at,
            "reformlab_engine_version": self.manifest.engine_version,
            "reformlab_openfisca_version": self.manifest.openfisca_version,
            "reformlab_adapter_version": self.manifest.adapter_version,
            "reformlab_scenario_version": self.manifest.scenario_version,
        }

        return self.panel_output.to_parquet(
            path,
            schema_metadata=provenance_metadata,
        )


def create_quickstart_adapter(
    *,
    carbon_tax_rate: float,
    year: int = 2025,
    household_count: int = 100,
    version_string: str = "quickstart-demo-v1",
) -> ComputationAdapter:
    """Create a synthetic adapter for quickstart notebook demos.

    This helper keeps quickstart notebooks on the public API surface while
    using synthetic, offline data suitable for first-run onboarding.
    """
    from reformlab.computation.mock_adapter import MockAdapter
    from reformlab.interfaces.errors import ConfigurationError

    import pyarrow as pa

    if household_count <= 0:
        raise ConfigurationError(
            field_path="household_count",
            expected="positive integer",
            actual=household_count,
            fix="Provide a positive integer for household_count",
        )
    if year < 0:
        raise ConfigurationError(
            field_path="year",
            expected="non-negative integer year",
            actual=year,
            fix="Provide a valid year (0 or greater)",
        )
    if carbon_tax_rate < 0:
        raise ConfigurationError(
            field_path="carbon_tax_rate",
            expected="non-negative tax rate",
            actual=carbon_tax_rate,
            fix="Provide a non-negative tax rate value",
        )

    baseline_rate = 44.0
    rate_multiplier = carbon_tax_rate / baseline_rate if baseline_rate else 1.0

    income_base = [15000.0 + (i * 800.0) for i in range(household_count)]
    carbon_tax_base = [150.0 + (i * 0.5) for i in range(household_count)]
    scaled_carbon_tax = [max(0.0, tax * rate_multiplier) for tax in carbon_tax_base]

    synthetic_output = pa.table(
        {
            "household_id": pa.array(range(household_count), type=pa.int64()),
            "year": pa.array([year] * household_count, type=pa.int64()),
            "income": pa.array(income_base, type=pa.float64()),
            "carbon_tax": pa.array(scaled_carbon_tax, type=pa.float64()),
            "disposable_income": pa.array(
                [income_base[i] - scaled_carbon_tax[i] for i in range(household_count)],
                type=pa.float64(),
            ),
        }
    )

    return MockAdapter(
        default_output=synthetic_output,
        version_string=version_string,
    )


def run_scenario(
    config: RunConfig | ScenarioConfig | Path | dict[str, Any],
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
        ValidationErrors: If multiple configuration validation issues are found.
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
    except ConfigurationError:
        raise
    except Exception as exc:
        raise SimulationError(
            f"Scenario loading failed — Could not load scenario configuration — Check scenario file format and content",
            cause=exc,
            fix="Check scenario file format and content",
        ) from exc

    # Step 4: Setup adapter
    if adapter is None:
        adapter = _initialize_default_adapter(run_config)

    # Step 5: Execute via orchestrator
    try:
        result = _execute_orchestration(scenario, run_config, adapter)
    except ConfigurationError:
        raise
    except Exception as exc:
        # Extract context from OrchestratorError if available
        from reformlab.orchestrator.errors import OrchestratorError

        if isinstance(exc, OrchestratorError):
            root_cause = _unwrap_original_error(exc)
            completed = sorted(exc.partial_states.keys()) if exc.partial_states else []
            context_parts: list[str] = []
            if exc.year is not None:
                context_parts.append(f"year {exc.year}")
            if exc.step_name:
                context_parts.append(f"step '{exc.step_name}'")
            if completed:
                context_parts.append(f"completed years: {completed}")
            context_suffix = (
                f" (failure context: {', '.join(context_parts)})"
                if context_parts
                else ""
            )

            from reformlab.computation.exceptions import ApiMappingError

            if isinstance(root_cause, ApiMappingError):
                what = _sanitize_error_text(root_cause.summary) or "Mapping failed"
                why = _sanitize_error_text(root_cause.reason)
                fix = _sanitize_error_text(root_cause.fix)
            else:
                what = "Simulation execution failed"
                why = _sanitize_error_text(exc.reason)
                fix = "Check adapter configuration and input data"
                if exc.year is not None:
                    fix += f" for year {exc.year}"

            why = f"{why}{context_suffix}" if why else context_suffix.strip() or "An operational step failed"

            raise SimulationError(
                f"{what} — {why} — {fix}",
                cause=exc,
                fix=fix,
                partial_states=exc.partial_states,
            ) from exc
        else:
            raise SimulationError(
                f"Simulation execution failed — Error during orchestrator execution — Check adapter configuration and input data",
                cause=exc,
                fix="Check adapter configuration and input data",
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
        from reformlab.templates.workflow import WorkflowError, load_workflow_config

        try:
            workflow_config = load_workflow_config(config)
        except WorkflowError:
            # Not a workflow config (or invalid workflow) - treat as API YAML.
            data = _load_yaml_mapping(config, field_path="config")
            if "scenario" in data:
                return _normalize_config(data)
            return RunConfig(
                scenario=_dict_to_scenario_config(data),
                output_dir=_coerce_optional_path(
                    data.get("output_dir"),
                    field_path="output_dir",
                ),
                seed=_coerce_optional_int(data.get("seed"), field_path="seed"),
            )
        else:
            return _workflow_config_to_run_config(workflow_config)

    if isinstance(config, dict):
        # Accept either {"scenario": {...}} run config or direct scenario mapping.
        scenario_data = config["scenario"] if "scenario" in config else config

        scenario: ScenarioConfig | Path | dict[str, Any]
        if isinstance(scenario_data, dict):
            scenario = _dict_to_scenario_config(scenario_data)
        elif isinstance(scenario_data, Path):
            scenario = scenario_data
        elif isinstance(scenario_data, str):
            scenario = Path(scenario_data)
        elif isinstance(scenario_data, ScenarioConfig):
            scenario = scenario_data
        else:
            raise ConfigurationError(
                field_path="scenario",
                expected="ScenarioConfig, Path, str path, or dict",
                actual=type(scenario_data).__name__,
                fix="Provide scenario as ScenarioConfig object, file path, or dictionary",
            )

        return RunConfig(
            scenario=scenario,
            output_dir=_coerce_optional_path(
                config.get("output_dir"),
                field_path="output_dir",
            ),
            seed=_coerce_optional_int(config.get("seed"), field_path="seed"),
        )

    raise ConfigurationError(
        field_path="config",
        expected="RunConfig, Path, or dict",
        actual=type(config).__name__,
        fix="Provide config as RunConfig object, YAML file path, or dictionary",
    )


_ERROR_PREFIX_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*Error:\s*")


def _sanitize_error_text(value: str) -> str:
    """Normalize low-level error text for user-facing API messages."""
    text = " ".join(value.strip().split())
    if not text:
        return ""
    if "traceback" in text.lower():
        return "An internal error occurred"
    cleaned = _ERROR_PREFIX_RE.sub("", text)
    return cleaned.strip(" :-")


def _unwrap_original_error(exc: Exception) -> Exception:
    """Unwrap nested ``original_error`` links to reach root cause."""
    current: Exception = exc
    seen_ids: set[int] = set()
    while id(current) not in seen_ids:
        seen_ids.add(id(current))
        nested = getattr(current, "original_error", None)
        if isinstance(nested, Exception):
            current = nested
            continue
        break
    return current


def _workflow_config_to_run_config(workflow_config: Any) -> RunConfig:
    """Convert templates.workflow.WorkflowConfig into API RunConfig."""
    from reformlab.interfaces.errors import ConfigurationError

    if not workflow_config.scenarios:
        raise ConfigurationError(
            field_path="scenarios",
            expected="at least one scenario reference",
            actual=[],
            fix="Add at least one scenario entry to the workflow config",
        )

    scenario_ref = workflow_config.scenarios[0].reference
    start_year = workflow_config.run_config.start_year
    end_year = start_year + workflow_config.run_config.projection_years - 1

    return RunConfig(
        scenario=ScenarioConfig(
            template_name=scenario_ref,
            parameters={},
            start_year=start_year,
            end_year=end_year,
        ),
    )


def _coerce_optional_int(value: Any, *, field_path: str) -> int | None:
    """Coerce optional integer values with user-facing error context."""
    from reformlab.interfaces.errors import ConfigurationError

    if value is None:
        return None
    if isinstance(value, bool):
        raise ConfigurationError(
            field_path=field_path,
            expected="int",
            actual=value,
            fix="Provide an integer value (not boolean)",
        )

    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(
            field_path=field_path,
            expected="int",
            actual=value,
            fix="Provide a valid integer value",
        ) from exc


def _coerce_required_int(value: Any, *, field_path: str) -> int:
    """Coerce required integer values with user-facing error context."""
    from reformlab.interfaces.errors import ConfigurationError

    if value is None or isinstance(value, bool):
        raise ConfigurationError(
            field_path=field_path,
            expected="int",
            actual=value,
            fix="Provide a valid integer value",
        )

    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(
            field_path=field_path,
            expected="int",
            actual=value,
            fix="Provide a valid integer value",
        ) from exc


def _coerce_optional_path(value: Any, *, field_path: str) -> Path | None:
    """Coerce optional path values with user-facing error context."""
    from reformlab.interfaces.errors import ConfigurationError

    if value is None:
        return None
    if isinstance(value, Path):
        return value
    if isinstance(value, str) and value.strip():
        return Path(value)

    raise ConfigurationError(
        field_path=field_path,
        expected="path string or Path",
        actual=value,
        fix="Provide a valid file path as string or Path object",
    )


def _load_yaml_mapping(path: Path, *, field_path: str) -> dict[str, Any]:
    """Load a YAML file and ensure the top-level value is a mapping."""
    from reformlab.interfaces.errors import ConfigurationError

    if not path.exists():
        raise ConfigurationError(
            field_path=field_path,
            expected="existing YAML file path",
            actual=str(path),
            fix=f"Ensure the file exists at {path}",
        )

    try:
        with open(path, encoding="utf-8") as handle:
            raw = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise ConfigurationError(
            field_path=field_path,
            expected="valid YAML syntax",
            actual=str(path),
            fix=f"Fix YAML syntax errors in {path}",
        ) from exc
    except OSError as exc:
        raise ConfigurationError(
            field_path=field_path,
            expected="readable YAML file",
            actual=str(path),
            fix=f"Ensure the file at {path} is readable",
        ) from exc

    if not isinstance(raw, dict):
        raise ConfigurationError(
            field_path=field_path,
            expected="YAML mapping (object)",
            actual=type(raw).__name__,
            fix="Ensure the YAML file contains a top-level mapping (object)",
        )

    return cast(dict[str, Any], raw)


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

    # API-native schema: template_name + start/end years
    if "template_name" in data:
        template_name = data.get("template_name")
        start_year = data.get("start_year")
        end_year = data.get("end_year")
        baseline_id = data.get("baseline_id")
    # Template schema: name + year_schedule
    elif "name" in data and "year_schedule" in data:
        template_name = data.get("name")
        year_schedule = data.get("year_schedule")
        if not isinstance(year_schedule, dict):
            raise ConfigurationError(
                field_path="scenario.year_schedule",
                expected="mapping with start_year/end_year",
                actual=year_schedule,
                fix="Provide year_schedule as a dictionary with start_year and end_year keys",
            )
        start_year = year_schedule.get("start_year")
        end_year = year_schedule.get("end_year")
        baseline_id = data.get("baseline_ref")
    else:
        template_name = data.get("template_name")
        start_year = data.get("start_year")
        end_year = data.get("end_year")
        baseline_id = data.get("baseline_id")

    if not isinstance(template_name, str) or not template_name.strip():
        raise ConfigurationError(
            field_path="scenario.template_name",
            expected="non-empty string",
            actual=template_name,
            fix="Provide a valid template name as a non-empty string",
        )

    parameters = data.get("parameters")
    if not isinstance(parameters, dict):
        raise ConfigurationError(
            field_path="scenario.parameters",
            expected="dict of policy parameters",
            actual=parameters,
            fix="Provide parameters as a dictionary of policy parameters",
        )

    population_path = _coerce_optional_path(
        data.get("population_path"),
        field_path="scenario.population_path",
    )

    baseline_id_value: str | None
    if baseline_id is None:
        baseline_id_value = None
    elif isinstance(baseline_id, str) and baseline_id.strip():
        baseline_id_value = baseline_id
    else:
        raise ConfigurationError(
            field_path="scenario.baseline_id",
            expected="non-empty string or null",
            actual=baseline_id,
            fix="Provide baseline_id as a non-empty string or null",
        )

    return ScenarioConfig(
        template_name=template_name,
        parameters=dict(parameters),
        start_year=_coerce_required_int(start_year, field_path="scenario.start_year"),
        end_year=_coerce_required_int(end_year, field_path="scenario.end_year"),
        population_path=population_path,
        seed=_coerce_optional_int(data.get("seed"), field_path="scenario.seed"),
        baseline_id=baseline_id_value,
    )


def _validate_config(run_config: RunConfig) -> None:
    """Validate configuration before execution.

    Accumulates all validation issues and raises ValidationErrors if any are found.

    Args:
        run_config: Configuration to validate.

    Raises:
        ConfigurationError: If a single configuration issue is found during file check.
        ValidationErrors: If multiple configuration issues are found.
    """
    from reformlab.interfaces.errors import ConfigurationError, ValidationErrors, ValidationIssue

    issues: list[ValidationIssue] = []

    # Check output_dir
    if run_config.output_dir is not None:
        if run_config.output_dir.exists() and not run_config.output_dir.is_dir():
            issues.append(
                ValidationIssue(
                    field_path="output_dir",
                    expected="directory path",
                    actual=str(run_config.output_dir),
                    fix="Provide a valid directory path or remove the existing file",
                    message=f"Configuration error at 'output_dir' — Expected directory path, got {run_config.output_dir!r} — Provide a valid directory path or remove the existing file",
                )
            )

    # Extract scenario config
    scenario = run_config.scenario
    if isinstance(scenario, Path):
        if not scenario.exists():
            raise ConfigurationError(
                field_path="scenario",
                expected="existing file path",
                actual=str(scenario),
                fix=f"Ensure the file exists at {scenario}",
            )
        return  # File will be validated when loaded

    if isinstance(scenario, dict):
        # Convert to ScenarioConfig for validation
        scenario = _dict_to_scenario_config(scenario)

    if isinstance(scenario, ScenarioConfig):
        # Validate year bounds
        if scenario.end_year < scenario.start_year:
            issues.append(
                ValidationIssue(
                    field_path="scenario.end_year",
                    expected=f">= {scenario.start_year}",
                    actual=scenario.end_year,
                    fix=f"Set end_year to {scenario.start_year} or later",
                    message=f"Configuration error at 'scenario.end_year' — Expected >= {scenario.start_year}, got {scenario.end_year!r} — Set end_year to {scenario.start_year} or later",
                )
            )

        # Validate year range is reasonable
        if scenario.start_year < 1900 or scenario.start_year > 2200:
            issues.append(
                ValidationIssue(
                    field_path="scenario.start_year",
                    expected="year in range [1900, 2200]",
                    actual=scenario.start_year,
                    fix="Provide a year between 1900 and 2200",
                    message=f"Configuration error at 'scenario.start_year' — Expected year in range [1900, 2200], got {scenario.start_year!r} — Provide a year between 1900 and 2200",
                )
            )

        if scenario.end_year < 1900 or scenario.end_year > 2200:
            issues.append(
                ValidationIssue(
                    field_path="scenario.end_year",
                    expected="year in range [1900, 2200]",
                    actual=scenario.end_year,
                    fix="Provide a year between 1900 and 2200",
                    message=f"Configuration error at 'scenario.end_year' — Expected year in range [1900, 2200], got {scenario.end_year!r} — Provide a year between 1900 and 2200",
                )
            )

        # Validate population file if provided
        if scenario.population_path is not None:
            if not scenario.population_path.exists():
                issues.append(
                    ValidationIssue(
                        field_path="scenario.population_path",
                        expected="existing file",
                        actual=str(scenario.population_path),
                        fix=f"Ensure the file exists at {scenario.population_path}",
                        message=f"Configuration error at 'scenario.population_path' — Expected existing file, got {scenario.population_path!r} — Ensure the file exists at {scenario.population_path}",
                    )
                )

    # Raise aggregated errors if any were found
    if issues:
        raise ValidationErrors(issues)


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
        data = _load_yaml_mapping(scenario, field_path="scenario")
        return _dict_to_scenario_config(data)

    if isinstance(scenario, dict):
        return _dict_to_scenario_config(scenario)

    from reformlab.interfaces.errors import ConfigurationError

    raise ConfigurationError(
        field_path="scenario",
        expected="ScenarioConfig, Path, or dict",
        actual=type(scenario).__name__,
        fix="Provide scenario as ScenarioConfig object, file path, or dictionary",
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

    from reformlab import __version__
    from reformlab.computation.types import PolicyConfig
    from reformlab.governance.manifest import RunManifest
    from reformlab.orchestrator.computation_step import ComputationStep
    from reformlab.orchestrator.panel import PanelOutput
    from reformlab.orchestrator.runner import OrchestratorRunner
    from reformlab.orchestrator.types import OrchestratorResult, YearState
    from reformlab.templates.workflow import WorkflowResult

    # Normalize parameters to ensure manifest compatibility
    # Convert any numeric keys to strings for JSON serialization
    normalized_params = _normalize_parameters(scenario.parameters)

    population = _load_population_data(scenario.population_path)
    policy = PolicyConfig(
        parameters=normalized_params,
        name=scenario.template_name,
    )

    # Build workflow request
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
    runner = OrchestratorRunner(
        step_pipeline=(
            ComputationStep(
                adapter=adapter,
                population=population,
                policy=policy,
            ),
        ),
        seed=seed,
        initial_state={},
        parameters=normalized_params,
        scenario_name=scenario.template_name,
        scenario_version="api-v1",
    )

    # Execute
    workflow_result: WorkflowResult = runner.run(request)

    # Extract yearly states from workflow result.
    yearly_states_raw = workflow_result.outputs.get("yearly_states", {})
    yearly_states: dict[int, YearState] = {}
    if isinstance(yearly_states_raw, dict):
        for year_key, state_raw in yearly_states_raw.items():
            if not isinstance(state_raw, dict):
                continue

            year_value = state_raw.get("year", year_key)
            year_int = _coerce_required_int(year_value, field_path="outputs.year")

            yearly_states[year_int] = YearState(
                year=year_int,
                data=dict(state_raw.get("data", {})),
                seed=_coerce_optional_int(state_raw.get("seed"), field_path="outputs.seed"),
                metadata=dict(state_raw.get("metadata", {})),
            )

    failed_year = _coerce_optional_int(
        workflow_result.metadata.get("failed_year"),
        field_path="metadata.failed_year",
    )
    failed_step = (
        workflow_result.metadata.get("failed_step")
        if isinstance(workflow_result.metadata.get("failed_step"), str)
        else None
    )

    if not workflow_result.success:
        from reformlab.orchestrator.errors import OrchestratorError

        reason = workflow_result.errors[0] if workflow_result.errors else "Unknown execution error"
        raise OrchestratorError(
            summary="Simulation workflow failed",
            reason=reason,
            year=failed_year,
            step_name=failed_step,
            partial_states=yearly_states,
        )

    orchestrator_result = OrchestratorResult(
        success=workflow_result.success,
        yearly_states=yearly_states,
        errors=list(workflow_result.errors),
        failed_year=failed_year,
        failed_step=failed_step,
        metadata=dict(workflow_result.metadata),
    )
    panel_output = PanelOutput.from_orchestrator_result(orchestrator_result)

    parent_manifest_id = workflow_result.metadata.get("parent_manifest_id", "")
    if not isinstance(parent_manifest_id, str):
        parent_manifest_id = ""

    child_manifests = _coerce_child_manifest_map(
        workflow_result.metadata.get("child_manifests"),
    )

    adapter_version = _safe_adapter_version(adapter)

    manifest = RunManifest(
        manifest_id=parent_manifest_id or "api-run",
        created_at=datetime.now(timezone.utc).isoformat(),
        engine_version=__version__,
        openfisca_version=adapter_version,
        adapter_version=adapter_version,
        scenario_version="1.0.0",
        parameters=normalized_params,
        seeds={"master": seed} if seed is not None else {},
        assumptions=_coerce_dict_list(workflow_result.metadata.get("assumptions")),
        mappings=_coerce_dict_list(workflow_result.metadata.get("mappings")),
        warnings=_coerce_string_list(workflow_result.metadata.get("warnings")),
        step_pipeline=_coerce_string_list(workflow_result.metadata.get("step_pipeline")),
        parent_manifest_id=parent_manifest_id,
        child_manifests=child_manifests,
        data_hashes=_coerce_hash_map(workflow_result.metadata.get("data_hashes")),
        output_hashes=_coerce_hash_map(workflow_result.metadata.get("output_hashes")),
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


def _initialize_default_adapter(run_config: RunConfig) -> ComputationAdapter:
    """Create the default OpenFisca adapter when one is not provided."""
    from reformlab.interfaces.errors import ConfigurationError

    data_dir = _resolve_openfisca_data_dir(run_config)
    try:
        from reformlab.computation.openfisca_adapter import OpenFiscaAdapter

        return OpenFiscaAdapter(data_dir=data_dir)
    except Exception as exc:
        raise ConfigurationError(
            field_path="adapter",
            expected="initializable OpenFisca adapter",
            actual=str(data_dir),
            fix=f"Ensure OpenFisca is properly installed and data_dir={data_dir} is valid",
        ) from exc


def _resolve_openfisca_data_dir(run_config: RunConfig) -> Path:
    """Resolve OpenFiscaAdapter data directory from config/env/defaults."""
    from reformlab.interfaces.errors import ConfigurationError

    env_data_dir = os.environ.get("REFORMLAB_OPENFISCA_DATA_DIR")
    if env_data_dir:
        env_path = Path(env_data_dir)
        if env_path.is_dir():
            return env_path
        raise ConfigurationError(
            field_path="adapter.data_dir",
            expected="existing directory path",
            actual=env_data_dir,
            fix=f"Create the directory at {env_data_dir} or update REFORMLAB_OPENFISCA_DATA_DIR",
        )

    default_path = Path("data/openfisca")
    if default_path.is_dir():
        return default_path

    raise ConfigurationError(
        field_path="adapter.data_dir",
        expected=(
            "existing directory via REFORMLAB_OPENFISCA_DATA_DIR or default "
            "data/openfisca"
        ),
        actual=str(run_config.output_dir) if run_config.output_dir is not None else None,
        fix="Set REFORMLAB_OPENFISCA_DATA_DIR environment variable or pass adapter explicitly",
    )


def _load_population_data(population_path: Path | None) -> Any:
    """Load population input as PopulationData for the computation step."""
    import pyarrow as pa
    import pyarrow.csv as pa_csv
    import pyarrow.parquet as pq

    from reformlab.computation.types import PopulationData
    from reformlab.interfaces.errors import ConfigurationError

    if population_path is None:
        return PopulationData(
            tables={"default": pa.table({"household_id": pa.array([], type=pa.int64())})},
            metadata={"source": "empty"},
        )

    suffixes = tuple(part.lower() for part in population_path.suffixes)
    try:
        if suffixes[-2:] == (".csv", ".gz") or suffixes[-1:] == (".csv",):
            table = pa_csv.read_csv(population_path)
        elif suffixes[-1:] in ((".parquet",), (".pq",)):
            table = pq.read_table(population_path)
        else:
            raise ConfigurationError(
                field_path="scenario.population_path",
                expected=".csv, .csv.gz, .parquet, or .pq file",
                actual=str(population_path),
                fix="Provide a population file in CSV, CSV.GZ, or Parquet format",
            )
    except ConfigurationError:
        raise
    except Exception as exc:
        raise ConfigurationError(
            field_path="scenario.population_path",
            expected="readable population dataset",
            actual=str(population_path),
            fix=f"Ensure {population_path} is a valid and readable population dataset file",
        ) from exc

    return PopulationData(
        tables={"default": table},
        metadata={"source": str(population_path)},
    )


def _safe_adapter_version(adapter: ComputationAdapter) -> str:
    """Return adapter version defensively for manifest packaging."""
    version_method = getattr(adapter, "version", None)
    if not callable(version_method):
        return "unknown"
    try:
        version = version_method()
    except Exception:
        return "unknown"
    return str(version) if version else "unknown"


def _coerce_string_list(value: Any) -> list[str]:
    """Normalize arbitrary values to a list[str] (dropping empty entries)."""
    if not isinstance(value, list):
        return []
    normalized: list[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            normalized.append(text)
    return normalized


def _coerce_dict_list(value: Any) -> list[dict[str, Any]]:
    """Normalize arbitrary values to list[dict[str, Any]]."""
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _coerce_hash_map(value: Any) -> dict[str, str]:
    """Normalize hash metadata payloads to a string map."""
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, str] = {}
    for key, hash_value in value.items():
        if isinstance(key, str) and isinstance(hash_value, str):
            normalized[key] = hash_value
    return normalized


def _coerce_child_manifest_map(value: Any) -> dict[int, str]:
    """Normalize child manifest metadata payloads to year->id mapping."""
    if not isinstance(value, dict):
        return {}

    normalized: dict[int, str] = {}
    for year_raw, manifest_id in value.items():
        if not isinstance(manifest_id, str):
            continue
        try:
            year_int = int(year_raw)
        except (TypeError, ValueError):
            continue
        normalized[year_int] = manifest_id
    return normalized


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
            fix=f"Check that scenario '{name}' exists in the registry using list_scenarios()",
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
            fix=f"Check that scenario '{name}' exists in the registry using list_scenarios()",
        ) from exc


def run_benchmarks(
    panel: PanelOutput | None = None,
    result: SimulationResult | None = None,
    reference_path: Path | None = None,
) -> BenchmarkSuiteResult:
    """Run benchmark validation suite against simulation outputs.

    This is a thin facade over the governance benchmarking subsystem,
    providing a stable user-facing API for benchmark verification.

    Args:
        panel: Panel output to benchmark. If None, extracts from result.
        result: Simulation result containing panel output. Used if panel is None.
        reference_path: Path to benchmark reference YAML file.
            If None, uses default location.

    Returns:
        BenchmarkSuiteResult with benchmark outcomes and timing.

    Raises:
        SimulationError: If no panel output is available.
        FileNotFoundError: If reference file is not found.

    Example:
        >>> from reformlab import run_scenario, run_benchmarks
        >>> result = run_scenario(config)
        >>> benchmark_result = run_benchmarks(result=result)
        >>> print(benchmark_result)
        BenchmarkSuiteResult(3/3 passed, 0.45s)
    """
    from reformlab.governance.benchmarking import run_benchmark_suite
    from reformlab.interfaces.errors import SimulationError

    # Extract panel from result if not provided
    if panel is None:
        if result is None:
            raise SimulationError(
                "Benchmark validation failed — No panel or result provided — Pass panel=<PanelOutput> or result=<SimulationResult>",
                fix="Pass panel=<PanelOutput> or result=<SimulationResult>",
            )
        if result.panel_output is None:
            raise SimulationError(
                "Benchmark validation failed — Simulation result has no panel output — Ensure the simulation completed successfully",
                fix="Ensure the simulation completed successfully",
            )
        panel = result.panel_output

    # Delegate to governance benchmarking subsystem
    return run_benchmark_suite(panel, reference_path)
