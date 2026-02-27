"""Tests for the public Python API.

Tests cover:
- SimulationResult dataclass and __repr__
- Configuration types (RunConfig, ScenarioConfig)
- run_scenario() function with valid/invalid configs
- Scenario management (create, clone, list, get)
- Error handling and user-friendly messages
- Public API imports from package root
"""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pytest
import yaml

from reformlab.computation.mock_adapter import MockAdapter
from reformlab.governance.manifest import RunManifest
from reformlab.orchestrator.panel import PanelOutput
from reformlab.orchestrator.types import YearState


class TestSimulationResult:
    """Test SimulationResult dataclass."""

    def test_simulation_result_is_frozen(self) -> None:
        """SimulationResult is immutable after construction."""
        from datetime import datetime, timezone

        from reformlab import SimulationResult

        result = SimulationResult(
            success=True,
            scenario_id="test-scenario",
            yearly_states={},
            panel_output=None,
            manifest=RunManifest(
                manifest_id="test-id",
                created_at=datetime.now(timezone.utc).isoformat(),
                engine_version="1.0",
                openfisca_version="1.0",
                adapter_version="1.0",
                scenario_version="1.0",
            ),
        )

        with pytest.raises(AttributeError):
            result.success = False  # type: ignore[misc]

    def test_simulation_result_repr_success(self) -> None:
        """__repr__ shows success status, years, rows, and manifest ID."""
        from datetime import datetime, timezone

        from reformlab import SimulationResult

        yearly_states = {
            2025: YearState(year=2025, data={}, seed=42),
            2026: YearState(year=2026, data={}, seed=43),
        }

        panel_table = pa.table(
            {
                "household_id": pa.array([1, 2, 3], type=pa.int64()),
                "year": pa.array([2025, 2025, 2025], type=pa.int64()),
            }
        )

        panel_output = PanelOutput(table=panel_table, metadata={})

        result = SimulationResult(
            success=True,
            scenario_id="carbon-tax",
            yearly_states=yearly_states,
            panel_output=panel_output,
            manifest=RunManifest(
                manifest_id="abc123",
                created_at=datetime.now(timezone.utc).isoformat(),
                engine_version="1.0",
                openfisca_version="1.0",
                adapter_version="1.0",
                scenario_version="1.0",
            ),
        )

        repr_str = repr(result)

        assert "SUCCESS" in repr_str
        assert "scenario='carbon-tax'" in repr_str
        assert "years=2025-2026" in repr_str
        assert "rows=3" in repr_str
        assert "manifest='abc123'" in repr_str

    def test_simulation_result_repr_failure(self) -> None:
        """__repr__ shows FAILED status for unsuccessful runs."""
        from datetime import datetime, timezone

        from reformlab import SimulationResult

        result = SimulationResult(
            success=False,
            scenario_id="failed-scenario",
            yearly_states={},
            panel_output=None,
            manifest=RunManifest(
                manifest_id="fail-id",
                created_at=datetime.now(timezone.utc).isoformat(),
                engine_version="1.0",
                openfisca_version="1.0",
                adapter_version="1.0",
                scenario_version="1.0",
            ),
        )

        repr_str = repr(result)

        assert "FAILED" in repr_str
        assert "years=none" in repr_str
        assert "rows=0" in repr_str

    def test_simulation_result_indicators_no_panel(self) -> None:
        """indicators() raises SimulationError when panel_output is None."""
        from datetime import datetime, timezone

        from reformlab import SimulationError, SimulationResult

        result = SimulationResult(
            success=False,
            scenario_id="test",
            yearly_states={},
            panel_output=None,
            manifest=RunManifest(
                manifest_id="test-id",
                created_at=datetime.now(timezone.utc).isoformat(),
                engine_version="1.0",
                openfisca_version="1.0",
                adapter_version="1.0",
                scenario_version="1.0",
            ),
        )

        with pytest.raises(SimulationError, match="No panel output available"):
            result.indicators("distributional")

    def test_simulation_result_indicators_unknown_type(self) -> None:
        """indicators() raises SimulationError for unknown indicator type."""
        from datetime import datetime, timezone

        from reformlab import SimulationError, SimulationResult

        panel_table = pa.table(
            {
                "household_id": pa.array([1], type=pa.int64()),
                "year": pa.array([2025], type=pa.int64()),
            }
        )

        result = SimulationResult(
            success=True,
            scenario_id="test",
            yearly_states={},
            panel_output=PanelOutput(table=panel_table, metadata={}),
            manifest=RunManifest(
                manifest_id="test-id",
                created_at=datetime.now(timezone.utc).isoformat(),
                engine_version="1.0",
                openfisca_version="1.0",
                adapter_version="1.0",
                scenario_version="1.0",
            ),
        )

        with pytest.raises(SimulationError, match="Unknown indicator type"):
            result.indicators("invalid_type")

    def test_simulation_result_welfare_requires_reform_input(self) -> None:
        """welfare indicators require a reform panel/result argument."""
        from datetime import datetime, timezone

        from reformlab import SimulationError, SimulationResult

        panel_table = pa.table(
            {
                "household_id": pa.array([1, 2], type=pa.int64()),
                "year": pa.array([2025, 2025], type=pa.int64()),
                "income": pa.array([20000.0, 30000.0], type=pa.float64()),
                "disposable_income": pa.array([19800.0, 29650.0], type=pa.float64()),
            }
        )

        result = SimulationResult(
            success=True,
            scenario_id="baseline",
            yearly_states={},
            panel_output=PanelOutput(table=panel_table, metadata={}),
            manifest=RunManifest(
                manifest_id="test-id",
                created_at=datetime.now(timezone.utc).isoformat(),
                engine_version="1.0",
                openfisca_version="1.0",
                adapter_version="1.0",
                scenario_version="1.0",
            ),
        )

        with pytest.raises(SimulationError, match="Welfare indicators require a reform panel"):
            result.indicators("welfare")

    def test_simulation_result_welfare_accepts_reform_result(self) -> None:
        """welfare indicators compute successfully with reform_result input."""
        from datetime import datetime, timezone

        from reformlab import SimulationResult

        household_ids = list(range(1, 11))
        income = [20000.0 + (i * 2000.0) for i in range(10)]
        baseline_disposable_income = [v - 150.0 for v in income]
        reform_disposable_income = [v - 300.0 for v in income]

        baseline_table = pa.table(
            {
                "household_id": pa.array(household_ids, type=pa.int64()),
                "year": pa.array([2025] * 10, type=pa.int64()),
                "income": pa.array(income, type=pa.float64()),
                "disposable_income": pa.array(
                    baseline_disposable_income,
                    type=pa.float64(),
                ),
            }
        )
        reform_table = pa.table(
            {
                "household_id": pa.array(household_ids, type=pa.int64()),
                "year": pa.array([2025] * 10, type=pa.int64()),
                "income": pa.array(income, type=pa.float64()),
                "disposable_income": pa.array(
                    reform_disposable_income,
                    type=pa.float64(),
                ),
            }
        )

        baseline_result = SimulationResult(
            success=True,
            scenario_id="baseline",
            yearly_states={},
            panel_output=PanelOutput(table=baseline_table, metadata={}),
            manifest=RunManifest(
                manifest_id="baseline-id",
                created_at=datetime.now(timezone.utc).isoformat(),
                engine_version="1.0",
                openfisca_version="1.0",
                adapter_version="1.0",
                scenario_version="1.0",
            ),
        )
        reform_result = SimulationResult(
            success=True,
            scenario_id="reform",
            yearly_states={},
            panel_output=PanelOutput(table=reform_table, metadata={}),
            manifest=RunManifest(
                manifest_id="reform-id",
                created_at=datetime.now(timezone.utc).isoformat(),
                engine_version="1.0",
                openfisca_version="1.0",
                adapter_version="1.0",
                scenario_version="1.0",
            ),
        )

        indicators = baseline_result.indicators("welfare", reform_result=reform_result)

        assert indicators.indicators
        assert indicators.metadata["group_type"] == "decile"


class TestConfigurationTypes:
    """Test configuration dataclasses."""

    def test_scenario_config_is_frozen(self) -> None:
        """ScenarioConfig is immutable after construction."""
        from reformlab import ScenarioConfig

        config = ScenarioConfig(
            template_name="test",
            parameters={},
            start_year=2025,
            end_year=2030,
        )

        with pytest.raises(AttributeError):
            config.start_year = 2026  # type: ignore[misc]

    def test_run_config_is_frozen(self) -> None:
        """RunConfig is immutable after construction."""
        from reformlab import RunConfig, ScenarioConfig

        config = RunConfig(
            scenario=ScenarioConfig(
                template_name="test",
                parameters={},
                start_year=2025,
                end_year=2030,
            ),
        )

        with pytest.raises(AttributeError):
            config.seed = 42  # type: ignore[misc]


class TestRunScenario:
    """Test run_scenario function."""

    def test_run_scenario_with_dict_config(self) -> None:
        """run_scenario accepts dict configuration."""
        from reformlab import run_scenario

        config = {
            "scenario": {
                "template_name": "test-scenario",
                "parameters": {"rate_schedule": {2025: 50.0}},
                "start_year": 2025,
                "end_year": 2026,
            },
            "seed": 42,
        }

        adapter = MockAdapter()

        result = run_scenario(config, adapter=adapter)

        assert result.scenario_id == "test-scenario"
        assert result.success

    def test_run_scenario_with_scenario_config(self) -> None:
        """run_scenario accepts ScenarioConfig."""
        from reformlab import RunConfig, ScenarioConfig, run_scenario

        scenario = ScenarioConfig(
            template_name="carbon-tax",
            parameters={"rate_schedule": {2025: 50.0}},
            start_year=2025,
            end_year=2027,
        )

        config = RunConfig(scenario=scenario, seed=42)

        adapter = MockAdapter()

        result = run_scenario(config, adapter=adapter)

        assert result.scenario_id == "carbon-tax"
        assert result.success

    def test_run_scenario_missing_required_field(self) -> None:
        """run_scenario raises ConfigurationError for missing required fields."""
        from reformlab import ConfigurationError, run_scenario

        config = {
            "scenario": {
                "template_name": "test",
                "parameters": {},
                # Missing start_year
                "end_year": 2030,
            },
        }

        adapter = MockAdapter()

        with pytest.raises(ConfigurationError) as exc_info:
            run_scenario(config, adapter=adapter)

        error = exc_info.value
        assert error.field_path == "scenario.start_year"
        assert "expected" in error.message.lower()


    def test_run_scenario_invalid_year_range(self) -> None:
        """run_scenario raises ConfigurationError for end_year < start_year."""
        from reformlab import ConfigurationError, ScenarioConfig, run_scenario

        config = ScenarioConfig(
            template_name="test",
            parameters={},
            start_year=2030,
            end_year=2025,  # Invalid: before start_year
        )

        adapter = MockAdapter()

        with pytest.raises(ConfigurationError) as exc_info:
            run_scenario(config, adapter=adapter)

        error = exc_info.value
        assert "end_year" in error.field_path
        assert ">=" in error.message

    def test_run_scenario_invalid_year_bounds(self) -> None:
        """run_scenario raises ConfigurationError for unreasonable years."""
        from reformlab import ConfigurationError, ScenarioConfig, run_scenario

        config = ScenarioConfig(
            template_name="test",
            parameters={},
            start_year=1800,  # Before 1900
            end_year=1850,
        )

        adapter = MockAdapter()

        with pytest.raises(ConfigurationError) as exc_info:
            run_scenario(config, adapter=adapter)

        error = exc_info.value
        assert "start_year" in error.field_path
        assert "1900" in error.message

    def test_run_scenario_missing_population_file(self) -> None:
        """run_scenario raises ConfigurationError for missing population file."""
        from reformlab import ConfigurationError, ScenarioConfig, run_scenario

        config = ScenarioConfig(
            template_name="test",
            parameters={},
            start_year=2025,
            end_year=2030,
            population_path=Path("/nonexistent/population.csv"),
        )

        adapter = MockAdapter()

        with pytest.raises(ConfigurationError) as exc_info:
            run_scenario(config, adapter=adapter)

        error = exc_info.value
        assert "population_path" in error.field_path
        assert "not found" in error.message.lower()

    def test_run_scenario_returns_simulation_result(self) -> None:
        """run_scenario returns SimulationResult with expected structure."""
        from reformlab import RunConfig, ScenarioConfig, SimulationResult, run_scenario

        config = RunConfig(
            scenario=ScenarioConfig(
                template_name="test-scenario",
                parameters={"rate_schedule": {2025: 50.0}},
                start_year=2025,
                end_year=2026,
            ),
            seed=42,
        )

        adapter = MockAdapter()

        result = run_scenario(config, adapter=adapter)

        assert isinstance(result, SimulationResult)
        assert result.success
        assert result.scenario_id == "test-scenario"
        assert isinstance(result.yearly_states, dict)
        assert result.manifest.manifest_id

    def test_run_scenario_with_yaml_run_config_path(self, tmp_path: Path) -> None:
        """run_scenario accepts a YAML run-config path."""
        from reformlab import run_scenario

        config_path = tmp_path / "run-config.yaml"
        config_path.write_text(
            yaml.safe_dump(
                {
                    "scenario": {
                        "template_name": "yaml-run-config",
                        "parameters": {"rate_schedule": {2025: 50.0}},
                        "start_year": 2025,
                        "end_year": 2026,
                    },
                    "seed": 123,
                }
            ),
            encoding="utf-8",
        )

        result = run_scenario(config_path, adapter=MockAdapter())

        assert result.success
        assert result.scenario_id == "yaml-run-config"

    def test_run_scenario_with_scenario_yaml_path_in_dict(self, tmp_path: Path) -> None:
        """run_scenario accepts scenario path values inside dict config."""
        from reformlab import run_scenario

        scenario_path = tmp_path / "scenario.yaml"
        scenario_path.write_text(
            yaml.safe_dump(
                {
                    "template_name": "yaml-scenario",
                    "parameters": {"rate_schedule": {2025: 60.0}},
                    "start_year": 2025,
                    "end_year": 2027,
                }
            ),
            encoding="utf-8",
        )

        result = run_scenario({"scenario": str(scenario_path)}, adapter=MockAdapter())

        assert result.success
        assert result.scenario_id == "yaml-scenario"

    def test_run_scenario_with_invalid_seed_type(self) -> None:
        """Invalid seed values raise ConfigurationError with field context."""
        from reformlab import ConfigurationError, run_scenario

        with pytest.raises(ConfigurationError) as exc_info:
            run_scenario(
                {
                    "scenario": {
                        "template_name": "seed-check",
                        "parameters": {},
                        "start_year": 2025,
                        "end_year": 2026,
                    },
                    "seed": "not-an-int",
                },
                adapter=MockAdapter(),
            )

        assert exc_info.value.field_path == "seed"


class TestQuickstartAdapter:
    """Test public quickstart adapter helper."""

    def test_create_quickstart_adapter_returns_callable_adapter(self) -> None:
        """create_quickstart_adapter builds a compatible adapter object."""
        from reformlab import create_quickstart_adapter
        from reformlab.computation.types import PolicyConfig, PopulationData

        adapter = create_quickstart_adapter(carbon_tax_rate=44.0, year=2025)
        result = adapter.compute(
            population=PopulationData(tables={}, metadata={}),
            policy=PolicyConfig(name="carbon-tax", parameters={}),
            period=2025,
        )

        assert result.output_fields.num_rows == 100
        assert "carbon_tax" in result.output_fields.column_names


class TestScenarioManagement:
    """Test scenario management functions."""

    def test_create_scenario_without_registration(self) -> None:
        """create_scenario returns scenario object when register=False."""
        from reformlab import create_scenario
        from reformlab.templates.schema import (
            BaselineScenario,
            CarbonTaxParameters,
            PolicyType,
            YearSchedule,
        )

        scenario = BaselineScenario(
            name="test-baseline",
            policy_type=PolicyType.CARBON_TAX,
            year_schedule=YearSchedule(2025, 2030),
            parameters=CarbonTaxParameters(rate_schedule={2025: 50.0}),
        )

        result = create_scenario(scenario, "test-baseline", register=False)

        assert result is scenario

    def test_create_scenario_with_registration(self, tmp_path: Path) -> None:
        """create_scenario returns version ID when register=True."""
        import os

        from reformlab import create_scenario
        from reformlab.templates.schema import (
            BaselineScenario,
            CarbonTaxParameters,
            PolicyType,
            YearSchedule,
        )

        # Set registry path to temp directory
        os.environ["REFORMLAB_REGISTRY_PATH"] = str(tmp_path / "registry")

        scenario = BaselineScenario(
            name="test-baseline-reg",
            policy_type=PolicyType.CARBON_TAX,
            year_schedule=YearSchedule(2025, 2030),
            parameters=CarbonTaxParameters(rate_schedule={2025: 50.0}),
        )

        result = create_scenario(scenario, "test-baseline-reg", register=True)

        assert isinstance(result, str)
        assert len(result) == 12  # Version ID is 12 chars

    def test_list_scenarios_empty(self, tmp_path: Path) -> None:
        """list_scenarios returns empty list for empty registry."""
        import os

        from reformlab import list_scenarios

        # Set registry path to temp directory
        os.environ["REFORMLAB_REGISTRY_PATH"] = str(tmp_path / "registry")

        scenarios = list_scenarios()

        assert scenarios == []

    def test_list_scenarios_with_scenarios(self, tmp_path: Path) -> None:
        """list_scenarios returns registered scenario names."""
        import os

        from reformlab import create_scenario, list_scenarios
        from reformlab.templates.schema import (
            BaselineScenario,
            CarbonTaxParameters,
            PolicyType,
            YearSchedule,
        )

        # Set registry path to temp directory
        os.environ["REFORMLAB_REGISTRY_PATH"] = str(tmp_path / "registry")

        scenario1 = BaselineScenario(
            name="scenario-alpha",
            policy_type=PolicyType.CARBON_TAX,
            year_schedule=YearSchedule(2025, 2030),
            parameters=CarbonTaxParameters(rate_schedule={2025: 50.0}),
        )

        scenario2 = BaselineScenario(
            name="scenario-beta",
            policy_type=PolicyType.CARBON_TAX,
            year_schedule=YearSchedule(2025, 2030),
            parameters=CarbonTaxParameters(rate_schedule={2025: 60.0}),
        )

        create_scenario(scenario1, "scenario-alpha", register=True)
        create_scenario(scenario2, "scenario-beta", register=True)

        scenarios = list_scenarios()

        assert "scenario-alpha" in scenarios
        assert "scenario-beta" in scenarios

    def test_get_scenario_not_found(self, tmp_path: Path) -> None:
        """get_scenario raises ConfigurationError for nonexistent scenario."""
        import os

        from reformlab import ConfigurationError, get_scenario

        # Set registry path to temp directory
        os.environ["REFORMLAB_REGISTRY_PATH"] = str(tmp_path / "registry")

        with pytest.raises(ConfigurationError) as exc_info:
            get_scenario("nonexistent-scenario")

        error = exc_info.value
        assert error.field_path == "name"
        assert "nonexistent-scenario" in error.message

    def test_get_scenario_success(self, tmp_path: Path) -> None:
        """get_scenario returns scenario from registry."""
        import os

        from reformlab import create_scenario, get_scenario
        from reformlab.templates.schema import (
            BaselineScenario,
            CarbonTaxParameters,
            PolicyType,
            YearSchedule,
        )

        # Set registry path to temp directory
        os.environ["REFORMLAB_REGISTRY_PATH"] = str(tmp_path / "registry")

        scenario = BaselineScenario(
            name="test-get",
            policy_type=PolicyType.CARBON_TAX,
            year_schedule=YearSchedule(2025, 2030),
            parameters=CarbonTaxParameters(rate_schedule={2025: 50.0}),
        )

        create_scenario(scenario, "test-get", register=True)

        retrieved = get_scenario("test-get")

        assert retrieved.name == "test-get"
        assert retrieved.policy_type == PolicyType.CARBON_TAX

    def test_clone_scenario_not_found(self, tmp_path: Path) -> None:
        """clone_scenario raises ConfigurationError for nonexistent scenario."""
        import os

        from reformlab import ConfigurationError, clone_scenario

        # Set registry path to temp directory
        os.environ["REFORMLAB_REGISTRY_PATH"] = str(tmp_path / "registry")

        with pytest.raises(ConfigurationError) as exc_info:
            clone_scenario("nonexistent-scenario")

        error = exc_info.value
        assert error.field_path == "name"

    def test_clone_scenario_success(self, tmp_path: Path) -> None:
        """clone_scenario creates a copy with new name."""
        import os

        from reformlab import clone_scenario, create_scenario
        from reformlab.templates.schema import (
            BaselineScenario,
            CarbonTaxParameters,
            PolicyType,
            YearSchedule,
        )

        # Set registry path to temp directory
        os.environ["REFORMLAB_REGISTRY_PATH"] = str(tmp_path / "registry")

        scenario = BaselineScenario(
            name="test-clone-source",
            policy_type=PolicyType.CARBON_TAX,
            year_schedule=YearSchedule(2025, 2030),
            parameters=CarbonTaxParameters(rate_schedule={2025: 50.0}),
        )

        create_scenario(scenario, "test-clone-source", register=True)

        clone = clone_scenario("test-clone-source", new_name="test-clone-target")

        assert clone.name == "test-clone-target"
        assert clone.policy_type == PolicyType.CARBON_TAX
        # Parameters should be identical
        assert clone.parameters == scenario.parameters


class TestPublicAPIImports:
    """Test that all public API symbols are importable from package root."""

    def test_import_run_scenario(self) -> None:
        """run_scenario is importable from reformlab package root."""
        from reformlab import run_scenario

        assert callable(run_scenario)

    def test_import_create_quickstart_adapter(self) -> None:
        """create_quickstart_adapter is importable from reformlab package root."""
        from reformlab import create_quickstart_adapter

        assert callable(create_quickstart_adapter)

    def test_import_create_scenario(self) -> None:
        """create_scenario is importable from reformlab package root."""
        from reformlab import create_scenario

        assert callable(create_scenario)

    def test_import_clone_scenario(self) -> None:
        """clone_scenario is importable from reformlab package root."""
        from reformlab import clone_scenario

        assert callable(clone_scenario)

    def test_import_list_scenarios(self) -> None:
        """list_scenarios is importable from reformlab package root."""
        from reformlab import list_scenarios

        assert callable(list_scenarios)

    def test_import_get_scenario(self) -> None:
        """get_scenario is importable from reformlab package root."""
        from reformlab import get_scenario

        assert callable(get_scenario)

    def test_import_simulation_result(self) -> None:
        """SimulationResult is importable from reformlab package root."""
        from reformlab import SimulationResult

        assert SimulationResult is not None

    def test_import_run_config(self) -> None:
        """RunConfig is importable from reformlab package root."""
        from reformlab import RunConfig

        assert RunConfig is not None

    def test_import_scenario_config(self) -> None:
        """ScenarioConfig is importable from reformlab package root."""
        from reformlab import ScenarioConfig

        assert ScenarioConfig is not None

    def test_import_configuration_error(self) -> None:
        """ConfigurationError is importable from reformlab package root."""
        from reformlab import ConfigurationError

        assert ConfigurationError is not None

    def test_import_simulation_error(self) -> None:
        """SimulationError is importable from reformlab package root."""
        from reformlab import SimulationError

        assert SimulationError is not None

    def test_all_exports_defined(self) -> None:
        """Package __all__ includes all public API symbols."""
        import reformlab

        expected_exports = {
            "run_scenario",
            "create_quickstart_adapter",
            "create_scenario",
            "clone_scenario",
            "list_scenarios",
            "get_scenario",
            "SimulationResult",
            "RunConfig",
            "ScenarioConfig",
            "ConfigurationError",
            "SimulationError",
            "__version__",
        }

        assert set(reformlab.__all__) == expected_exports


class TestErrorHandling:
    """Test error handling and user-friendly messages."""

    def test_configuration_error_structure(self) -> None:
        """ConfigurationError has expected structure and message."""
        from reformlab import ConfigurationError

        error = ConfigurationError(
            field_path="scenario.start_year",
            expected="int >= 1900",
            actual=1800,
        )

        assert error.field_path == "scenario.start_year"
        assert error.expected == "int >= 1900"
        assert error.actual == 1800
        assert "scenario.start_year" in error.message
        assert "expected" in error.message.lower()

    def test_simulation_error_structure(self) -> None:
        """SimulationError has expected structure and message."""
        from reformlab import SimulationError

        cause = ValueError("Test error")
        error = SimulationError("Simulation failed", cause=cause)

        assert error.message == "Simulation failed"
        assert error.cause is cause
        assert "Simulation failed" in str(error)

    def test_no_bare_value_errors_from_api(self) -> None:
        """API never raises bare ValueError - only ConfigurationError or SimulationError."""
        from reformlab import ConfigurationError, run_scenario

        # Invalid config should raise ConfigurationError, not ValueError
        config = {
            "scenario": {
                "template_name": "test",
                "parameters": {},
                "start_year": 2030,
                "end_year": 2025,  # Invalid
            },
        }

        adapter = MockAdapter()

        with pytest.raises(ConfigurationError):  # Not ValueError
            run_scenario(config, adapter=adapter)
