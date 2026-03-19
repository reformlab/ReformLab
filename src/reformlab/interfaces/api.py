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
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from reformlab.computation.adapter import ComputationAdapter
    from reformlab.computation.types import PopulationData
    from reformlab.data.pipeline import DatasetManifest
    from reformlab.governance.benchmarking import BenchmarkSuiteResult
    from reformlab.governance.manifest import RunManifest
    from reformlab.governance.memory import MemoryEstimate
    from reformlab.governance.replication import ReplicationPackageMetadata
    from reformlab.indicators.types import IndicatorResult
    from reformlab.orchestrator.panel import PanelOutput
    from reformlab.orchestrator.types import PipelineStep, YearState
    from reformlab.templates.schema import BaselineScenario, ReformScenario


@dataclass(frozen=True)
class ScenarioConfig:
    """Configuration for a scenario to run.

    Attributes:
        template_name: Name of the scenario template to use.
        policy: Policy parameters to apply.
        population_path: Optional path to population data file.
        start_year: First year of the projection.
        end_year: Last year of the projection.
        seed: Optional random seed for reproducibility.
        baseline_id: Optional baseline scenario ID for reform scenarios.
    """

    template_name: str
    policy: dict[str, Any]
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
class MemoryCheckResult:
    """Result of pre-execution memory check.

    Attributes:
        should_warn: Whether a memory warning should be displayed.
        estimate: MemoryEstimate with usage details.
        message: Formatted warning message if applicable.
    """

    should_warn: bool
    estimate: MemoryEstimate
    message: str


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
            from reformlab.indicators.types import DistributionalConfig

            config = DistributionalConfig(
                income_field=kwargs.pop("income_field", "income"),
                by_year=kwargs.pop("by_year", False),
            )
            return compute_distributional_indicators(self.panel_output, config=config)
        elif indicator_type_lower == "geographic":
            from reformlab.indicators.types import GeographicConfig

            config_geo = GeographicConfig(
                region_field=kwargs.pop("region_field", "region_code"),
                by_year=kwargs.pop("by_year", False),
            )
            return compute_geographic_indicators(self.panel_output, config=config_geo)
        elif indicator_type_lower == "welfare":
            from reformlab.indicators.types import WelfareConfig

            reform_panel = kwargs.pop("reform_panel", None)
            reform_result = kwargs.pop("reform_result", None)

            if reform_panel is None and reform_result is not None:
                reform_panel = getattr(reform_result, "panel_output", None)

            if reform_panel is None:
                raise SimulationError(
                    "Welfare indicator computation failed — No reform panel provided — Pass reform_result=<SimulationResult> or reform_panel=<PanelOutput>",
                    fix="Pass reform_result=<SimulationResult> or reform_panel=<PanelOutput>",
                )

            config_welfare = WelfareConfig(
                welfare_field=kwargs.pop("welfare_field", "disposable_income"),
                threshold=kwargs.pop("threshold", 0.0),
            )
            return compute_welfare_indicators(
                self.panel_output,
                reform_panel,
                config=config_welfare,
            )
        elif indicator_type_lower == "fiscal":
            from reformlab.indicators.types import FiscalConfig

            revenue_fields = list(kwargs.pop("revenue_fields", None) or [])
            cost_fields = list(kwargs.pop("cost_fields", None) or [])
            # Auto-detect fiscal columns when none explicitly configured
            if not revenue_fields and not cost_fields:
                _rev_suffixes = ("_revenue", "_tax", "_levy", "_duty")
                column_names = self.panel_output.table.schema.names
                revenue_fields = [
                    c for c in column_names if any(c.endswith(s) for s in _rev_suffixes)
                ]
            config_fiscal = FiscalConfig(
                revenue_fields=revenue_fields,
                cost_fields=cost_fields,
                by_year=kwargs.pop("by_year", False),
            )
            return compute_fiscal_indicators(self.panel_output, config=config_fiscal)
        else:
            raise SimulationError(
                f"Indicator computation failed — Unknown indicator type '{indicator_type}' — Use one of: distributional, geographic, welfare, fiscal",
                fix="Use one of the supported indicator types: distributional, geographic, welfare, fiscal",
            )

    def export_replication_package(
        self,
        output_path: Path,
        *,
        compress: bool = False,
        population_provenance: dict[str, Any] | None = None,
        calibration_provenance: dict[str, Any] | None = None,
    ) -> ReplicationPackageMetadata:
        """Export this simulation run as a self-contained replication package.

        Delegates to ``governance.export_replication_package()``. Creates a
        structured directory (or ZIP archive) with panel output, policy
        configuration, scenario metadata, and run manifest, plus a
        ``package-index.json`` with SHA-256 hashes for all artifacts.

        Optionally includes population generation provenance and calibration
        provenance files when the caller provides them.

        Args:
            output_path: Existing directory where the package is written.
            compress: If True, produce a ``.zip`` archive.
            population_provenance: Optional population pipeline config dict.
            calibration_provenance: Optional calibration provenance dict.

        Returns:
            ReplicationPackageMetadata with package location and index.

        Raises:
            ReplicationPackageError: If the result is not successful or
                panel output is missing.

        Story 16.1 / FR54.
        Story 16.3 / AC-1, AC-2.
        """
        from reformlab.governance.replication import export_replication_package

        return export_replication_package(
            self,
            output_path,
            compress=compress,
            population_provenance=population_provenance,
            calibration_provenance=calibration_provenance,
        )

    def export_manifest(self, path: str | Path) -> Path:
        """Export run manifest to JSON file.

        Writes the complete manifest (parameters, seeds, data hashes, versions,
        assumptions) as canonical JSON. Useful for audit trails and reproducibility.

        Args:
            path: Destination file path for JSON export.

        Returns:
            Path to the written JSON file.

        Example:
            >>> result = run_scenario(config)
            >>> manifest_path = result.export_manifest("output/manifest.json")
        """
        import json

        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Use to_json() for canonical content, then pretty-print for readability
        canonical = self.manifest.to_json()
        parsed = json.loads(canonical)
        dest.write_text(json.dumps(parsed, indent=2, sort_keys=True), encoding="utf-8")

        return dest

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

        provenance_metadata: dict[str, str | bytes] = {
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

    def plot_yearly(
        self,
        field: str,
        metric: str = "mean",
        *,
        title: str | None = None,
        color: str = "steelblue",
    ) -> tuple[Figure, Axes]:
        """Line chart of a field's metric over time from panel output.

        Args:
            field: Name of the field to plot (e.g., "carbon_tax").
            metric: Aggregation metric ("mean", "median", "sum").
            title: Chart title. Auto-generated if None.
            color: Line color. Defaults to "steelblue".

        Returns:
            Tuple of (Figure, Axes).

        Raises:
            SimulationError: If panel output is not available.
        """
        from reformlab.interfaces.errors import SimulationError
        from reformlab.visualization.plotting import plot_yearly

        if self.panel_output is None:
            msg = "Operation failed — No panel output available — Ensure the simulation completed successfully"
            raise SimulationError(msg, fix="Ensure the simulation completed successfully")

        return plot_yearly(
            self.panel_output.table, field, metric, title=title, color=color,
        )

    def plot_comparison(
        self,
        other: SimulationResult,
        field: str,
        metric: str = "mean",
        *,
        baseline_label: str = "Baseline",
        reform_label: str = "Reform",
        title: str | None = None,
    ) -> tuple[Figure, Axes]:
        """Side-by-side bar chart comparing this result with another by decile.

        Computes distributional indicators for both results and plots them
        as a grouped bar chart.

        Args:
            other: Other SimulationResult to compare against.
            field: Name of the field to compare (e.g., "carbon_tax").
            metric: Metric to compare (e.g., "mean").
            baseline_label: Legend label for this result's bars.
            reform_label: Legend label for the other result's bars.
            title: Chart title. Auto-generated if None.

        Returns:
            Tuple of (Figure, Axes).

        Raises:
            SimulationError: If panel output is not available on either result.
        """
        from reformlab.interfaces.errors import SimulationError
        from reformlab.visualization.plotting import plot_comparison

        if self.panel_output is None or other.panel_output is None:
            msg = "Operation failed — No panel output available — Ensure both simulations completed successfully"
            raise SimulationError(msg, fix="Ensure both simulations completed successfully")

        baseline_indicators = self.indicators("distributional")
        reform_indicators = other.indicators("distributional")

        return plot_comparison(
            baseline_indicators.to_table(),
            reform_indicators.to_table(),
            field,
            metric,
            baseline_label=baseline_label,
            reform_label=reform_label,
            title=title,
        )


class SimpleCarbonTaxAdapter:
    """Transparent demo adapter that reads the rate from the typed policy.

    The formula applied is::

        rate = policy.rate_schedule[period]   # from the typed CarbonTaxParameters
        carbon_tax = carbon_emissions × (rate / 44.0)
        disposable_income = income − carbon_tax

    The adapter has **no constructor parameters for rate or year** — it reads
    both from the policy and period it receives at ``compute()`` time.  This is
    the whole point of typed policies as runtime source of truth.

    Example::

        >>> adapter = SimpleCarbonTaxAdapter()
        >>> result = run_scenario(scenario, adapter=adapter, population=pop, seed=42)
    """

    _BASELINE_RATE = 44.0

    def __init__(self, *, version_string: str = "simple-carbon-tax-v1") -> None:
        self._version_string = version_string

    def version(self) -> str:
        """Return adapter version string."""
        return self._version_string

    def compute(
        self,
        population: PopulationData,
        policy: Any,
        period: int,
    ) -> Any:
        """Apply carbon tax formula to population data.

        Reads ``rate_schedule`` from the typed policy to get the rate for
        the current ``period``.  Falls back to 0.0 if the period is not
        in the schedule.

        Args:
            population: Population data with household_id, income, carbon_emissions.
            policy: PolicyConfig whose ``.policy`` is a typed PolicyParameters.
            period: Simulation year (used to look up the rate schedule).

        Returns:
            ComputationResult with carbon_tax and disposable_income columns.
        """
        import pyarrow as pa

        from reformlab.computation.types import ComputationResult
        from reformlab.interfaces.errors import ConfigurationError

        # Read rate from the typed policy for this period
        rate_schedule = getattr(policy.policy, "rate_schedule", {})
        carbon_tax_rate = float(rate_schedule.get(period, 0.0))
        rate_multiplier = carbon_tax_rate / self._BASELINE_RATE if self._BASELINE_RATE else 1.0

        table = population.tables.get("default")
        if table is None or table.num_rows == 0:
            output = self._build_fallback_output(period, rate_multiplier)
        else:
            required_columns = {"household_id", "income", "carbon_emissions"}
            missing = required_columns - set(table.column_names)
            if missing:
                raise ConfigurationError(
                    field_path="population.columns",
                    expected=f"columns {sorted(required_columns)}",
                    actual=f"missing {sorted(missing)} in {table.column_names}",
                    fix="Ensure population CSV contains household_id, income, "
                    "and carbon_emissions columns",
                )

            household_ids = table.column("household_id")
            incomes = table.column("income").to_pylist()
            emissions = table.column("carbon_emissions").to_pylist()
            n = len(incomes)

            carbon_taxes = [max(0.0, e * rate_multiplier) for e in emissions]
            disposable = [incomes[i] - carbon_taxes[i] for i in range(n)]

            output = pa.table(
                {
                    "household_id": household_ids,
                    "year": pa.array([period] * n, type=pa.int64()),
                    "income": pa.array(incomes, type=pa.float64()),
                    "carbon_tax": pa.array(carbon_taxes, type=pa.float64()),
                    "disposable_income": pa.array(disposable, type=pa.float64()),
                }
            )

        return ComputationResult(
            output_fields=output,
            adapter_version=self._version_string,
            period=period,
            metadata={"source": "SimpleCarbonTaxAdapter", "rate": carbon_tax_rate},
        )

    @staticmethod
    def _build_fallback_output(period: int, rate_multiplier: float) -> Any:
        """Build synthetic fallback table for empty populations."""
        import pyarrow as pa

        size = 100
        income_base = [15000.0 + (i * 800.0) for i in range(size)]
        carbon_tax_base = [150.0 + (i * 0.5) for i in range(size)]
        scaled = [max(0.0, tax * rate_multiplier) for tax in carbon_tax_base]

        return pa.table(
            {
                "household_id": pa.array(range(size), type=pa.int64()),
                "year": pa.array([period] * size, type=pa.int64()),
                "income": pa.array(income_base, type=pa.float64()),
                "carbon_tax": pa.array(scaled, type=pa.float64()),
                "disposable_income": pa.array(
                    [income_base[i] - scaled[i] for i in range(size)],
                    type=pa.float64(),
                ),
            }
        )


def create_quickstart_adapter(
    *,
    carbon_tax_rate: float,
    year: int = 2025,
    version_string: str = "quickstart-demo-v1",
) -> ComputationAdapter:
    """Create a demo adapter for quickstart notebooks.

    .. deprecated::
        Use ``SimpleCarbonTaxAdapter`` directly instead. This function is
        retained as a compatibility shim.

    Returns a ``SimpleCarbonTaxAdapter`` wrapped in ``MockAdapter`` for
    backward compatibility with existing call-sites.
    """
    import pyarrow as pa

    from reformlab.computation.mock_adapter import MockAdapter
    from reformlab.computation.types import PolicyConfig
    from reformlab.interfaces.errors import ConfigurationError

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

    # Fallback output for empty-population calls (backward compatibility)
    _fallback_size = 100
    income_base = [15000.0 + (i * 800.0) for i in range(_fallback_size)]
    carbon_tax_base = [150.0 + (i * 0.5) for i in range(_fallback_size)]
    scaled_carbon_tax = [max(0.0, tax * rate_multiplier) for tax in carbon_tax_base]

    fallback_output = pa.table(
        {
            "household_id": pa.array(range(_fallback_size), type=pa.int64()),
            "year": pa.array([year] * _fallback_size, type=pa.int64()),
            "income": pa.array(income_base, type=pa.float64()),
            "carbon_tax": pa.array(scaled_carbon_tax, type=pa.float64()),
            "disposable_income": pa.array(
                [income_base[i] - scaled_carbon_tax[i] for i in range(_fallback_size)],
                type=pa.float64(),
            ),
        }
    )

    def _compute_from_population(
        population: PopulationData, policy: PolicyConfig, period: int
    ) -> pa.Table:
        """Compute carbon tax output from actual population data."""
        table = population.tables.get("default")
        if table is None or table.num_rows == 0:
            return fallback_output

        required_columns = {"household_id", "income", "carbon_emissions"}
        missing = required_columns - set(table.column_names)
        if missing:
            raise ConfigurationError(
                field_path="population.columns",
                expected=f"columns {sorted(required_columns)}",
                actual=f"missing {sorted(missing)} in {table.column_names}",
                fix="Ensure population CSV contains household_id, income, and carbon_emissions columns",
            )

        household_ids = table.column("household_id")
        incomes = table.column("income").to_pylist()
        emissions = table.column("carbon_emissions").to_pylist()
        n = len(incomes)

        carbon_taxes = [max(0.0, e * rate_multiplier) for e in emissions]
        disposable = [incomes[i] - carbon_taxes[i] for i in range(n)]

        return pa.table(
            {
                "household_id": household_ids,
                "year": pa.array([period] * n, type=pa.int64()),
                "income": pa.array(incomes, type=pa.float64()),
                "carbon_tax": pa.array(carbon_taxes, type=pa.float64()),
                "disposable_income": pa.array(disposable, type=pa.float64()),
            }
        )

    return MockAdapter(
        default_output=fallback_output,
        version_string=version_string,
        compute_fn=_compute_from_population,
    )


def check_memory_requirements(
    config: RunConfig | ScenarioConfig,
    skip_check: bool = False,
) -> MemoryCheckResult:
    """Check if simulation memory requirements exceed safe thresholds.

    Args:
        config: Scenario or run configuration to check.
        skip_check: If True, skip the check and return no warning.

    Returns:
        MemoryCheckResult with warning recommendation.

    Example:
        >>> from reformlab import ScenarioConfig, check_memory_requirements
        >>> config = ScenarioConfig(
        ...     template_name="test",
        ...     policy={},
        ...     start_year=2025,
        ...     end_year=2030,
        ... )
        >>> result = check_memory_requirements(config)
        >>> if result.should_warn:
        ...     print(result.message)
    """
    from reformlab.governance.memory import estimate_memory_usage
    from reformlab.interfaces.errors import MemoryWarning

    # Skip check if requested or env var set
    if skip_check or _should_skip_memory_check():
        # Return dummy result with no warning
        dummy_estimate = estimate_memory_usage(0, 0)
        return MemoryCheckResult(
            should_warn=False,
            estimate=dummy_estimate,
            message="",
        )

    # Extract scenario config
    if isinstance(config, RunConfig):
        scenario = config.scenario
        # Convert to ScenarioConfig if needed
        if isinstance(scenario, Path):
            scenario = _load_scenario(scenario)
        elif isinstance(scenario, dict):
            scenario = _dict_to_scenario_config(scenario)
    else:
        scenario = config

    # Calculate population size (estimate based on population_path or default)
    # For pre-execution check, we estimate population size from file metadata
    # or use a conservative default if no population file is specified
    population_size = _estimate_population_size(scenario.population_path)

    # Calculate projection years
    projection_years = scenario.end_year - scenario.start_year + 1

    # Estimate memory usage
    estimate = estimate_memory_usage(population_size, projection_years)

    # Check if threshold is exceeded
    sixteen_gb_bytes = 16 * (1024**3)
    exceeds_population_guardrail = (
        estimate.population_size > 500_000 and estimate.available_bytes <= sixteen_gb_bytes
    )
    if estimate.exceeds_threshold or exceeds_population_guardrail:
        message = str(MemoryWarning(estimate))
        return MemoryCheckResult(
            should_warn=True,
            estimate=estimate,
            message=message,
        )

    return MemoryCheckResult(
        should_warn=False,
        estimate=estimate,
        message="",
    )


def run_scenario(
    config: RunConfig | ScenarioConfig | BaselineScenario | ReformScenario | Path | dict[str, Any],
    adapter: ComputationAdapter | None = None,
    *,
    population: PopulationData | Path | None = None,
    seed: int | None = None,
    steps: tuple[PipelineStep, ...] | None = None,
    initial_state: dict[str, Any] | None = None,
    skip_memory_check: bool = False,
    baseline: BaselineScenario | None = None,
) -> SimulationResult:
    """Run a complete simulation scenario.

    This is the main entry point for executing simulations via the Python API.
    Supports two execution forms:

    **Config-based** (existing)::

        result = run_scenario(run_config, adapter=adapter)

    **Direct scenario** (new)::

        population = load_population(path)
        result = run_scenario(scenario, population=population, adapter=adapter, seed=42)

    Args:
        config: Scenario configuration as RunConfig, ScenarioConfig, BaselineScenario,
            ReformScenario, YAML path, or dict.
        adapter: Optional computation adapter. If None, uses OpenFiscaAdapter.
        population: Population data for direct-scenario execution. Required when
            passing a BaselineScenario or ReformScenario. Accepts PopulationData
            or a Path to CSV/Parquet (auto-loaded via load_population).
        seed: Random seed for direct-scenario execution. For config-based execution,
            use RunConfig.seed instead.
        steps: Optional additional pipeline steps to append after the default
            ComputationStep. For example, ``(VintageTransitionStep(vintage_config),)``.
        initial_state: Optional initial state dict passed to the orchestrator.
            Keys are state slot names (e.g., ``"vintage_vehicle"``).
        skip_memory_check: Skip memory preflight check.
        baseline: Baseline scenario for reform resolution. Required when
            passing a ReformScenario without a registry-resolvable baseline_ref.

    Returns:
        SimulationResult with yearly states, panel output, and manifest.

    Raises:
        ConfigurationError: If configuration is invalid.
        ValidationErrors: If multiple configuration validation issues are found.
        SimulationError: If simulation fails during execution.

    Examples:
        Config-based::

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

        Direct scenario::

            >>> from reformlab.templates.schema import BaselineScenario, CarbonTaxParameters, YearSchedule
            >>> scenario = BaselineScenario(
            ...     name="carbon-tax-2025",
            ...     year_schedule=YearSchedule(2025, 2030),
            ...     policy=CarbonTaxParameters(rate_schedule={2025: 44.60}),
            ... )
            >>> population = load_population("data/population.csv")
            >>> result = run_scenario(scenario, population=population, adapter=adapter, seed=42)
    """
    from reformlab.interfaces.errors import ConfigurationError, SimulationError

    # Step 0: Validate optional pipeline steps
    if steps is not None:
        if not isinstance(steps, tuple):
            raise ConfigurationError(
                field_path="steps",
                expected="tuple of PipelineStep instances or None",
                actual=f"{type(steps).__name__}",
                fix="Pass steps as a tuple, e.g. steps=(VintageTransitionStep(config),)",
            )
        for i, step in enumerate(steps):
            is_callable = callable(step)
            has_execute = hasattr(step, "execute") and callable(getattr(step, "execute"))
            if not (is_callable or has_execute):
                raise ConfigurationError(
                    field_path=f"steps[{i}]",
                    expected="callable or object with execute() method",
                    actual=f"{type(step).__name__}",
                    fix="Each step must be callable or implement the OrchestratorStep protocol",
                )

    # Direct-scenario path: BaselineScenario or ReformScenario
    from reformlab.templates.schema import BaselineScenario as BS
    from reformlab.templates.schema import ReformScenario as RS

    if isinstance(config, (BS, RS)):
        return _run_direct_scenario(
            scenario=config,
            adapter=adapter,
            population=population,
            seed=seed,
            steps=steps,
            initial_state=initial_state,
            skip_memory_check=skip_memory_check,
            baseline=baseline,
        )

    # Step 1: Normalize config to RunConfig
    run_config = _normalize_config(config)

    # Step 2: Validate before execution
    _validate_config(run_config)

    # Step 2b: Memory pre-check (before orchestration)
    preflight_warnings: list[str] = []
    if not skip_memory_check and not _should_skip_memory_check():
        check_result = check_memory_requirements(run_config)
        if check_result.should_warn:
            import logging
            import warnings

            from reformlab.interfaces.errors import MemoryWarning

            warning = MemoryWarning(check_result.estimate)
            warnings.warn(warning, stacklevel=2)
            logger = logging.getLogger(__name__)
            logger.warning(check_result.message)
            preflight_warnings.append(str(warning))

    # Step 3: Load scenario template
    try:
        scenario = _load_scenario(run_config.scenario)
    except ConfigurationError:
        raise
    except Exception as exc:
        raise SimulationError(
            "Scenario loading failed — Could not load scenario configuration — Check scenario file format and content",
            cause=exc,
            fix="Check scenario file format and content",
        ) from exc

    # Step 4: Setup adapter
    if adapter is None:
        adapter = _initialize_default_adapter(run_config)

    # Step 5: Execute via orchestrator
    try:
        result = _execute_orchestration(
            scenario,
            run_config,
            adapter,
            steps=steps,
            initial_state=initial_state,
            additional_warnings=preflight_warnings,
        )
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
                "Simulation execution failed — Error during orchestrator execution — Check adapter configuration and input data",
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
            policy={},
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

    policy_dict = data.get("policy")
    if not isinstance(policy_dict, dict):
        raise ConfigurationError(
            field_path="scenario.policy",
            expected="dict of policy parameters",
            actual=policy_dict,
            fix="Provide policy as a dictionary of policy parameters",
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
        policy=dict(policy_dict),
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


def _normalize_policy(params: dict[str, Any]) -> dict[str, Any]:
    """Normalize policy for manifest compatibility.

    Converts numeric dictionary keys to strings for JSON serialization.

    Args:
        params: Raw policy dictionary.

    Returns:
        Normalized policy with string keys.
    """

    def normalize_value(value: Any) -> dict[str, Any] | list[Any] | Any:
        if isinstance(value, dict):
            # Convert all keys to strings
            return {str(k): normalize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [normalize_value(item) for item in value]
        else:
            return value

    normalized = normalize_value(params)
    if not isinstance(normalized, dict):
        return {}
    return {str(key): value for key, value in normalized.items()}


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


def _run_direct_scenario(
    scenario: BaselineScenario | ReformScenario,
    adapter: ComputationAdapter | None,
    population: PopulationData | Path | None,
    seed: int | None,
    steps: tuple[PipelineStep, ...] | None,
    initial_state: dict[str, Any] | None,
    skip_memory_check: bool,
    baseline: BaselineScenario | None = None,
) -> SimulationResult:
    """Execute a typed scenario directly without config wrappers.

    Bridges BaselineScenario/ReformScenario into the existing orchestration
    pipeline. The typed policy flows directly to the computation layer.
    """
    from datetime import datetime, timezone

    from reformlab import __version__
    from reformlab.computation.types import PolicyConfig, serialize_policy
    from reformlab.governance.manifest import RunManifest
    from reformlab.interfaces.errors import ConfigurationError
    from reformlab.orchestrator.computation_step import ComputationStep
    from reformlab.orchestrator.panel import PanelOutput
    from reformlab.orchestrator.runner import OrchestratorRunner
    from reformlab.orchestrator.types import OrchestratorResult, YearState
    from reformlab.templates.schema import BaselineScenario as BS
    from reformlab.templates.schema import ReformScenario as RS
    from reformlab.templates.workflow import WorkflowResult

    # Resolve population
    if population is None:
        raise ConfigurationError(
            field_path="population",
            expected="PopulationData or Path to population file",
            actual="None",
            fix="Provide population data when using direct scenario execution: "
            "run_scenario(scenario, population=load_population(path), ...)",
        )

    if isinstance(population, Path):
        population = _load_population_data(population)

    # Reform resolution: resolve ReformScenario against baseline
    if isinstance(scenario, RS):
        if baseline is not None:
            from reformlab.templates.reform import resolve_reform_definition

            scenario_resolved = resolve_reform_definition(scenario, baseline)
            # Use the resolved policy and inherit year_schedule from baseline
            resolved_policy = scenario_resolved.policy
            year_schedule = scenario.year_schedule or baseline.year_schedule
        else:
            # Attempt registry lookup via baseline_ref
            try:
                from reformlab.templates.registry import ScenarioRegistry

                registry = ScenarioRegistry()
                baseline_obj = registry.get(scenario.baseline_ref)
                if not isinstance(baseline_obj, BS):
                    raise ConfigurationError(
                        field_path="baseline",
                        expected="BaselineScenario",
                        actual=type(baseline_obj).__name__,
                        fix="The baseline_ref must point to a BaselineScenario",
                    )
                from reformlab.templates.reform import resolve_reform_definition

                scenario_resolved = resolve_reform_definition(scenario, baseline_obj)
                resolved_policy = scenario_resolved.policy
                year_schedule = scenario.year_schedule or baseline_obj.year_schedule
            except ConfigurationError:
                raise
            except Exception:
                raise ConfigurationError(
                    field_path="baseline",
                    expected="BaselineScenario (via baseline= or registry lookup)",
                    actual="None",
                    fix="Provide baseline= argument explicitly, or register the "
                    f"baseline scenario '{scenario.baseline_ref}' before running",
                )
        # Use resolved policy for execution
        execution_policy = resolved_policy
        execution_name = scenario.name
    elif isinstance(scenario, BS):
        year_schedule = scenario.year_schedule
        execution_policy = scenario.policy
        execution_name = scenario.name
    else:
        raise ConfigurationError(
            field_path="scenario",
            expected="BaselineScenario or ReformScenario",
            actual=type(scenario).__name__,
            fix="Pass a BaselineScenario or ReformScenario object",
        )

    # Build typed PolicyConfig — the typed policy flows directly to adapters
    policy = PolicyConfig(
        policy=execution_policy,
        name=execution_name,
    )

    # Serialize for manifest/workflow boundaries
    serialized_policy = serialize_policy(execution_policy)

    # Build workflow request
    request: dict[str, Any] = {
        "name": execution_name,
        "version": scenario.version,
        "run_config": {
            "start_year": year_schedule.start_year,
            "projection_years": year_schedule.duration,
            "output_format": "parquet",
        },
        "scenarios": [{"role": "scenario", "reference": execution_name}],
        "policy": serialized_policy,
    }

    # Create orchestrator runner
    assert not isinstance(population, Path)  # resolved above
    runner = OrchestratorRunner(
        step_pipeline=(
            ComputationStep(
                adapter=adapter if adapter is not None else _initialize_default_adapter_for_direct(),
                population=population,
                policy=policy,
            ),
        ) + (steps or ()),
        seed=seed,
        initial_state=dict(initial_state or {}),
        policy=serialized_policy,
        scenario_name=execution_name,
        scenario_version=scenario.version,
    )

    # Execute
    workflow_result: WorkflowResult = runner.run(request)

    # Extract yearly states
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

    adapter_version = _safe_adapter_version(adapter) if adapter else "unknown"

    manifest = RunManifest(
        manifest_id=parent_manifest_id or "direct-run",
        created_at=datetime.now(timezone.utc).isoformat(),
        engine_version=__version__,
        openfisca_version=adapter_version,
        adapter_version=adapter_version,
        scenario_version=scenario.version,
        policy=serialized_policy,
        seeds={"master": seed} if seed is not None else {},
        assumptions=_coerce_dict_list(workflow_result.metadata.get("assumptions")),  # type: ignore[arg-type]
        mappings=_coerce_dict_list(workflow_result.metadata.get("mappings")),  # type: ignore[arg-type]
        warnings=_coerce_string_list(workflow_result.metadata.get("warnings")),
        step_pipeline=_coerce_string_list(workflow_result.metadata.get("step_pipeline")),
        parent_manifest_id=parent_manifest_id,
        child_manifests=child_manifests,
        data_hashes=_coerce_hash_map(workflow_result.metadata.get("data_hashes")),
        output_hashes=_coerce_hash_map(workflow_result.metadata.get("output_hashes")),
    )

    return SimulationResult(
        success=workflow_result.success,
        scenario_id=execution_name,
        yearly_states=yearly_states,
        panel_output=panel_output if workflow_result.success else None,
        manifest=manifest,
        metadata=workflow_result.metadata,
    )


def _initialize_default_adapter_for_direct() -> ComputationAdapter:
    """Create a default adapter for direct-scenario execution."""
    from reformlab.interfaces.errors import ConfigurationError

    try:
        from reformlab.computation.openfisca_adapter import OpenFiscaAdapter

        return OpenFiscaAdapter(data_dir=Path("data"))
    except Exception as exc:
        raise ConfigurationError(
            field_path="adapter",
            expected="ComputationAdapter",
            actual=str(exc),
            fix="Provide an adapter argument, e.g. adapter=create_quickstart_adapter(carbon_tax_rate=44.6)",
        ) from exc


def _execute_orchestration(
    scenario: ScenarioConfig,
    run_config: RunConfig,
    adapter: ComputationAdapter,
    *,
    steps: tuple[PipelineStep, ...] | None = None,
    initial_state: dict[str, Any] | None = None,
    additional_warnings: list[str] | None = None,
) -> SimulationResult:
    """Execute orchestration and package results.

    Args:
        scenario: Validated scenario configuration.
        run_config: Run configuration.
        adapter: Computation adapter.
        steps: Optional additional pipeline steps appended after ComputationStep.
        initial_state: Optional initial state dict for the orchestrator.
        additional_warnings: Optional pre-execution warnings to carry into manifest.

    Returns:
        SimulationResult with execution outcomes.

    Raises:
        SimulationError: If execution fails.
    """
    from datetime import datetime, timezone

    from reformlab import __version__
    from reformlab.computation.types import PolicyConfig, deserialize_policy, serialize_policy
    from reformlab.governance.manifest import RunManifest
    from reformlab.orchestrator.computation_step import ComputationStep
    from reformlab.orchestrator.panel import PanelOutput
    from reformlab.orchestrator.runner import OrchestratorRunner
    from reformlab.orchestrator.types import OrchestratorResult, YearState
    from reformlab.templates.workflow import WorkflowResult

    # Reconstruct typed PolicyParameters from the dict-based ScenarioConfig.
    typed_policy = deserialize_policy(scenario.policy)

    # Serialize for manifest/workflow boundaries (JSON-compatible dict)
    normalized_params = serialize_policy(typed_policy)

    population = _load_population_data(scenario.population_path)
    policy = PolicyConfig(
        policy=typed_policy,
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
        "policy": normalized_params,
        "additional_warnings": list(additional_warnings or []),
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
        ) + (steps or ()),
        seed=seed,
        initial_state=dict(initial_state or {}),
        policy=normalized_params,
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
        policy=normalized_params,
        seeds={"master": seed} if seed is not None else {},
        assumptions=_coerce_dict_list(workflow_result.metadata.get("assumptions")),  # type: ignore[arg-type]
        mappings=_coerce_dict_list(workflow_result.metadata.get("mappings")),  # type: ignore[arg-type]
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


def load_population(path: Path) -> PopulationData:
    """Load population data from a CSV or Parquet file.

    This is the public helper for loading population data for direct-scenario
    execution. It normalizes file paths into ``PopulationData`` objects.

    Args:
        path: Path to a population file (.csv, .csv.gz, .parquet, .pq).

    Returns:
        PopulationData wrapping the loaded table.

    Raises:
        ConfigurationError: If the file format is unsupported or unreadable.

    Example::

        >>> population = load_population(Path("data/households.csv"))
        >>> result = run_scenario(scenario, population=population, adapter=adapter)
    """
    from reformlab.computation.types import PopulationData

    result = _load_population_data(path)
    if not isinstance(result, PopulationData):
        return PopulationData(tables={"default": result}, metadata={"source": str(path)})
    return result


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
            ``policy_type`` is optional on the scenario — when omitted, it is
            automatically inferred from the ``policy`` parameter class
            (e.g. ``CarbonTaxParameters`` → ``PolicyType.CARBON_TAX``).
        name: Name for the scenario.
        register: If True, save to registry and return version ID.
            If False, just return the scenario object.

    Returns:
        Version ID string if registered, otherwise the scenario object.

    Example:
        >>> from reformlab import create_scenario
        >>> from reformlab.templates.schema import BaselineScenario, CarbonTaxParameters, YearSchedule
        >>> scenario = BaselineScenario(
        ...     name="carbon-tax-2025",
        ...     year_schedule=YearSchedule(2025, 2030),
        ...     policy=CarbonTaxParameters(rate_schedule={2025: 44.60}),
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


@dataclass(frozen=True)
class PopulationResult:
    """Result of synthetic population generation.

    Attributes:
        manifest: Dataset manifest with provenance metadata.
        row_count: Number of households generated.
        path: Output file path (if saved to disk).
    """

    manifest: DatasetManifest
    row_count: int
    path: Path | None = None

    def __repr__(self) -> str:
        saved = f", path={self.path}" if self.path else ""
        return f"PopulationResult(rows={self.row_count:,}, hash={self.manifest.content_hash[:12]}{saved})"


def generate_population(
    *,
    size: int = 100_000,
    seed: int = 42,
    output_path: Path | str | None = None,
) -> PopulationResult:
    """Generate a deterministic synthetic population dataset.

    Creates a synthetic household population for benchmarking and scale
    testing. The output is deterministic for the same (size, seed) pair.

    Args:
        size: Number of households to generate.
        seed: Random seed for reproducibility.
        output_path: If provided, save population to Parquet at this path.

    Returns:
        PopulationResult with manifest, row count, and output path.

    Example:
        >>> from reformlab import generate_population
        >>> result = generate_population(size=10_000, seed=42)
        >>> print(result)
        PopulationResult(rows=10,000, hash=abc123def456)
    """
    from reformlab.data.synthetic import generate_synthetic_population, save_synthetic_population

    table = generate_synthetic_population(size=size, seed=seed)

    if output_path is not None:
        resolved = Path(output_path)
        manifest = save_synthetic_population(table, resolved, seed=seed)
        return PopulationResult(
            manifest=manifest,
            row_count=len(table),
            path=resolved,
        )

    # No file output — build in-memory manifest with content hash
    import hashlib
    import io

    import pyarrow.parquet as pq

    from reformlab.data.pipeline import DatasetManifest as _DatasetManifest
    from reformlab.data.pipeline import DataSourceMetadata

    buf = io.BytesIO()
    pq.write_table(table, buf)
    content_hash = hashlib.sha256(buf.getvalue()).hexdigest()

    source = DataSourceMetadata(
        name="synthetic-population",
        version="1.0.0",
        url="",
        description=f"Deterministic synthetic population ({size} households, seed={seed})",
        license="internal",
    )

    from datetime import UTC, datetime

    manifest = _DatasetManifest(
        source=source,
        content_hash=content_hash,
        file_path=Path(""),
        format="parquet",
        row_count=len(table),
        column_names=tuple(table.schema.names),
        loaded_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )

    return PopulationResult(
        manifest=manifest,
        row_count=len(table),
        path=None,
    )


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


def _should_skip_memory_check() -> bool:
    """Check if memory check should be skipped based on environment variable."""
    skip_env = os.environ.get("REFORMLAB_SKIP_MEMORY_WARNING", "").lower()
    return skip_env in ("true", "1", "yes")


def _estimate_population_size(population_path: Path | None) -> int:
    """Estimate population size from file metadata or use default.

    Args:
        population_path: Path to population file, or None.

    Returns:
        Estimated population size.
    """
    if population_path is None:
        # Default to 100k households if no population file specified
        return 100_000

    if not population_path.exists():
        # File doesn't exist yet, use default
        return 100_000

    # Try to read row count from file metadata without loading entire file
    suffixes = tuple(part.lower() for part in population_path.suffixes)
    try:
        if suffixes[-1:] in ((".parquet",), (".pq",)):
            # Read Parquet metadata for fast row count
            import pyarrow.parquet as pq

            metadata = pq.read_metadata(population_path)
            return int(metadata.num_rows)
        elif suffixes[-2:] == (".csv", ".gz") or suffixes[-1:] == (".csv",):
            # For CSV, estimate based on file size
            # Rough heuristic: ~200 bytes per row on average
            file_size = population_path.stat().st_size
            estimated_rows = file_size // 200
            return max(estimated_rows, 1000)  # At least 1k rows
    except Exception:
        # On any error, fall back to conservative default
        pass

    # Conservative default: 500k households
    # This will trigger warnings on 16GB machines
    return 500_000
