# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for custom template authoring API and registration.

Story 13.1: Define custom template authoring API and registration.
Validates AC1-AC5: custom PolicyType extension, PolicyParameters registration,
validation on registration, YAML loading, and portfolio participation.

Note: Uses "test_penalty" as the example custom type name to avoid conflict
with the production "vehicle_malus" type registered by Story 13.2.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pytest

from reformlab.templates.exceptions import TemplateError
from reformlab.templates.schema import (
    PolicyParameters,
    PolicyType,
)

if TYPE_CHECKING:
    pass


# ====================================================================
# Test fixtures — custom parameter classes for testing
# ====================================================================


@dataclass(frozen=True)
class MockPenaltyParameters(PolicyParameters):
    """Test penalty parameters for custom template API tests."""

    emission_threshold: float = 120.0
    malus_rate: float = 50.0


@dataclass(frozen=True)
class EnergyPovertyAidParameters(PolicyParameters):
    """Energy poverty aid for low-income households."""

    income_ceiling: float = 15000.0
    aid_amount: float = 200.0


class NotADataclass:
    """Not a dataclass — should fail registration."""

    pass


@dataclass(frozen=False)
class MutableNotSubclass:
    """Mutable dataclass, not a PolicyParameters subclass — should fail registration."""

    custom_field: float = 0.0


@dataclass(frozen=True)
class NotPolicyParametersSubclass:
    """Frozen dataclass but not a PolicyParameters subclass."""

    rate: float = 0.0


# ====================================================================
# Cleanup fixture — save/restore custom registrations between tests
# ====================================================================


@pytest.fixture(autouse=True)
def _cleanup_custom_registrations() -> Any:
    """Save custom registrations before test, restore after.

    This preserves production registrations (e.g., vehicle_malus from
    Story 13.2) while cleaning up test-only registrations.
    """
    from reformlab.templates.schema import (
        _CUSTOM_PARAMETERS_TO_POLICY_TYPE,
        _CUSTOM_POLICY_TYPES,
    )

    saved_types = dict(_CUSTOM_POLICY_TYPES)
    saved_params = dict(_CUSTOM_PARAMETERS_TO_POLICY_TYPE)
    yield
    _CUSTOM_POLICY_TYPES.clear()
    _CUSTOM_POLICY_TYPES.update(saved_types)
    _CUSTOM_PARAMETERS_TO_POLICY_TYPE.clear()
    _CUSTOM_PARAMETERS_TO_POLICY_TYPE.update(saved_params)


# ====================================================================
# TestCustomPolicyTypeRegistration — AC2
# ====================================================================


class TestCustomPolicyTypeRegistration:
    """Tests for register_policy_type() and get_policy_type()."""

    # AC2: custom policy type string accepted as valid
    def test_register_custom_policy_type(self) -> None:
        """Registering a new policy type returns a usable PolicyType-like object."""
        from reformlab.templates.schema import register_policy_type

        result = register_policy_type("test_penalty")
        assert result is not None
        assert result.value == "test_penalty"

    def test_register_policy_type_snake_case_validation(self) -> None:
        """Policy type names must be non-empty, lowercase, snake_case."""
        from reformlab.templates.schema import register_policy_type

        with pytest.raises(TemplateError, match="non-empty"):
            register_policy_type("")

        with pytest.raises(TemplateError, match="lowercase"):
            register_policy_type("Test_Penalty")

        with pytest.raises(TemplateError, match="snake_case"):
            register_policy_type("test-penalty")

    def test_register_duplicate_policy_type_raises(self) -> None:
        """Registering an existing type name raises TemplateError."""
        from reformlab.templates.schema import register_policy_type

        register_policy_type("test_penalty")
        with pytest.raises(TemplateError, match="already registered"):
            register_policy_type("test_penalty")

    def test_register_builtin_policy_type_raises(self) -> None:
        """Registering a built-in type name raises TemplateError."""
        from reformlab.templates.schema import register_policy_type

        with pytest.raises(TemplateError, match="already registered"):
            register_policy_type("carbon_tax")

    def test_get_policy_type_builtin(self) -> None:
        """get_policy_type returns built-in PolicyType enum members."""
        from reformlab.templates.schema import get_policy_type

        result = get_policy_type("carbon_tax")
        assert result is PolicyType.CARBON_TAX

    def test_get_policy_type_custom(self) -> None:
        """get_policy_type returns registered custom type."""
        from reformlab.templates.schema import get_policy_type, register_policy_type

        register_policy_type("test_penalty")
        result = get_policy_type("test_penalty")
        assert result.value == "test_penalty"

    def test_get_policy_type_unknown_raises(self) -> None:
        """get_policy_type raises TemplateError for unknown types."""
        from reformlab.templates.schema import get_policy_type

        with pytest.raises(TemplateError, match="Unknown policy type"):
            get_policy_type("nonexistent_type")

    def test_builtin_types_unaffected(self) -> None:
        """Built-in PolicyType enum members still work after custom registration."""
        from reformlab.templates.schema import get_policy_type, register_policy_type

        register_policy_type("test_penalty")

        assert get_policy_type("carbon_tax") is PolicyType.CARBON_TAX
        assert get_policy_type("subsidy") is PolicyType.SUBSIDY
        assert get_policy_type("rebate") is PolicyType.REBATE
        assert get_policy_type("feebate") is PolicyType.FEEBATE


# ====================================================================
# TestCustomParametersRegistration — AC1, AC3
# ====================================================================


class TestCustomParametersRegistration:
    """Tests for register_custom_template() and infer_policy_type()."""

    # AC1: custom PolicyParameters registered and infer_policy_type works
    def test_register_and_infer_custom_template(self) -> None:
        """Registered custom class is resolvable via infer_policy_type."""
        from reformlab.templates.schema import (
            infer_policy_type,
            register_custom_template,
            register_policy_type,
        )

        pt = register_policy_type("test_penalty")
        register_custom_template(pt, MockPenaltyParameters)

        instance = MockPenaltyParameters(rate_schedule={2026: 50.0})
        inferred = infer_policy_type(instance)
        assert inferred.value == "test_penalty"

    def test_register_with_string_policy_type(self) -> None:
        """register_custom_template accepts a string policy type."""
        from reformlab.templates.schema import (
            infer_policy_type,
            register_custom_template,
            register_policy_type,
        )

        register_policy_type("test_penalty")
        register_custom_template("test_penalty", MockPenaltyParameters)

        instance = MockPenaltyParameters(rate_schedule={2026: 50.0})
        inferred = infer_policy_type(instance)
        assert inferred.value == "test_penalty"

    # AC3: validation on registration — not frozen
    def test_register_non_frozen_dataclass_raises(self) -> None:
        """Registering a mutable (non-frozen) dataclass raises TemplateError."""
        from reformlab.templates.schema import register_custom_template, register_policy_type

        pt = register_policy_type("mutable_type")
        with pytest.raises(TemplateError, match="frozen dataclass"):
            register_custom_template(pt, MutableNotSubclass)  # type: ignore[arg-type]

    # AC3: validation on registration — not a dataclass
    def test_register_non_dataclass_raises(self) -> None:
        """Registering a non-dataclass raises TemplateError."""
        from reformlab.templates.schema import register_custom_template, register_policy_type

        pt = register_policy_type("not_dc")
        with pytest.raises(TemplateError, match="frozen dataclass"):
            register_custom_template(pt, NotADataclass)  # type: ignore[arg-type]

    # AC3: validation on registration — not a PolicyParameters subclass
    def test_register_non_policy_parameters_subclass_raises(self) -> None:
        """Registering a frozen dataclass that doesn't subclass PolicyParameters raises."""
        from reformlab.templates.schema import register_custom_template, register_policy_type

        pt = register_policy_type("not_pp")
        with pytest.raises(TemplateError, match="PolicyParameters"):
            register_custom_template(pt, NotPolicyParametersSubclass)  # type: ignore[arg-type]

    # AC3: duplicate detection
    def test_register_duplicate_class_raises(self) -> None:
        """Re-registering same class raises TemplateError."""
        from reformlab.templates.schema import register_custom_template, register_policy_type

        pt = register_policy_type("test_penalty")
        register_custom_template(pt, MockPenaltyParameters)
        with pytest.raises(TemplateError, match="already registered"):
            register_custom_template(pt, MockPenaltyParameters)

    def test_register_conflicting_type_raises(self) -> None:
        """Registering a different class for an existing type raises."""
        from reformlab.templates.schema import register_custom_template, register_policy_type

        pt = register_policy_type("test_penalty")
        register_custom_template(pt, MockPenaltyParameters)
        with pytest.raises(TemplateError, match="already registered"):
            register_custom_template(pt, EnergyPovertyAidParameters)

    # AC1: custom class usable in BaselineScenario and ReformScenario
    def test_custom_type_in_baseline_scenario(self) -> None:
        """Custom registered type works in BaselineScenario construction."""
        from reformlab.templates.schema import (
            BaselineScenario,
            YearSchedule,
            register_custom_template,
            register_policy_type,
        )

        pt = register_policy_type("test_penalty")
        register_custom_template(pt, MockPenaltyParameters)

        policy = MockPenaltyParameters(
            rate_schedule={2026: 50.0},
            emission_threshold=130.0,
        )
        scenario = BaselineScenario(
            name="Test Penalty",
            year_schedule=YearSchedule(start_year=2026, end_year=2036),
            policy=policy,
        )
        assert scenario.policy_type is not None
        assert scenario.policy_type.value == "test_penalty"

    def test_custom_type_in_reform_scenario(self) -> None:
        """Custom registered type works in ReformScenario construction."""
        from reformlab.templates.schema import (
            ReformScenario,
            register_custom_template,
            register_policy_type,
        )

        pt = register_policy_type("test_penalty")
        register_custom_template(pt, MockPenaltyParameters)

        policy = MockPenaltyParameters(
            rate_schedule={2026: 60.0},
            emission_threshold=110.0,
        )
        scenario = ReformScenario(
            name="Stricter Penalty",
            baseline_ref="baseline-penalty",
            policy=policy,
        )
        assert scenario.policy_type is not None
        assert scenario.policy_type.value == "test_penalty"


# ====================================================================
# TestCustomTemplateYAMLLoading — AC4
# ====================================================================


class TestCustomTemplateYAMLLoading:
    """Tests for YAML loading and round-trip of custom templates."""

    def _register_test_penalty(self) -> None:
        """Helper to register the test_penalty custom type."""
        from reformlab.templates.schema import register_custom_template, register_policy_type

        register_policy_type("test_penalty")
        register_custom_template("test_penalty", MockPenaltyParameters)

    # AC4: YAML loading of custom template
    def test_load_custom_template_from_yaml(self, tmp_path: Any) -> None:
        """Loading a YAML with custom policy_type returns correct custom class."""
        import textwrap

        from reformlab.templates.loader import load_scenario_template

        self._register_test_penalty()

        content = textwrap.dedent("""\
            $schema: "./schema/scenario-template.schema.json"
            version: "1.0"
            name: "Test Penalty 2026"
            description: "Test emission penalty"
            policy_type: test_penalty
            year_schedule:
              start_year: 2026
              end_year: 2036
            policy:
              rate_schedule:
                2026: 50.0
                2027: 55.0
                2028: 60.0
                2029: 65.0
                2030: 70.0
                2031: 75.0
                2032: 80.0
                2033: 85.0
                2034: 90.0
                2035: 95.0
                2036: 100.0
              emission_threshold: 130.0
              malus_rate: 60.0
        """)
        p = tmp_path / "test-penalty.yaml"
        p.write_text(content, encoding="utf-8")

        scenario = load_scenario_template(p)
        assert isinstance(scenario.policy, MockPenaltyParameters)
        assert scenario.policy.emission_threshold == 130.0
        assert scenario.policy.malus_rate == 60.0
        assert scenario.policy_type is not None
        assert scenario.policy_type.value == "test_penalty"

    # AC4: YAML round-trip
    def test_yaml_round_trip_custom_template(self, tmp_path: Any) -> None:
        """Dump -> reload preserves custom field values."""
        from reformlab.templates.loader import dump_scenario_template, load_scenario_template
        from reformlab.templates.schema import BaselineScenario, YearSchedule

        self._register_test_penalty()

        policy = MockPenaltyParameters(
            rate_schedule={2026: 50.0, 2027: 55.0, 2028: 60.0, 2029: 65.0, 2030: 70.0,
                          2031: 75.0, 2032: 80.0, 2033: 85.0, 2034: 90.0, 2035: 95.0, 2036: 100.0},
            emission_threshold=130.0,
            malus_rate=60.0,
        )
        scenario = BaselineScenario(
            name="Test Penalty 2026",
            year_schedule=YearSchedule(start_year=2026, end_year=2036),
            policy=policy,
            description="Test emission penalty",
        )

        out_path = tmp_path / "test-penalty-out.yaml"
        dump_scenario_template(scenario, out_path)

        reloaded = load_scenario_template(out_path)
        assert isinstance(reloaded.policy, MockPenaltyParameters)
        assert reloaded.policy.emission_threshold == 130.0
        assert reloaded.policy.malus_rate == 60.0
        assert reloaded.policy.rate_schedule == policy.rate_schedule


# ====================================================================
# TestCustomTemplateInPortfolio — AC5
# ====================================================================


class TestCustomTemplateInPortfolio:
    """Tests for custom templates in PolicyConfig, PolicyPortfolio, and YAML round-trip."""

    def _register_test_penalty(self) -> None:
        from reformlab.templates.schema import register_custom_template, register_policy_type

        register_policy_type("test_penalty")
        register_custom_template("test_penalty", MockPenaltyParameters)

    # AC5a: portfolio construction succeeds
    def test_custom_template_in_policy_config(self) -> None:
        """Custom template can be wrapped in PolicyConfig."""
        from reformlab.templates.schema import register_custom_template, register_policy_type

        pt = register_policy_type("test_penalty")
        register_custom_template(pt, MockPenaltyParameters)

        from reformlab.templates.portfolios.portfolio import PolicyConfig

        config = PolicyConfig(
            policy_type=pt,
            policy=MockPenaltyParameters(rate_schedule={2026: 50.0}),
            name="Test Penalty",
        )
        assert config.policy_type.value == "test_penalty"

    # AC5a: portfolio construction with custom + built-in
    def test_custom_template_in_portfolio(self) -> None:
        """Custom template alongside built-in template in a portfolio."""
        from reformlab.templates.portfolios.portfolio import PolicyConfig, PolicyPortfolio
        from reformlab.templates.schema import (
            CarbonTaxParameters,
            PolicyType,
            register_custom_template,
            register_policy_type,
        )

        pt = register_policy_type("test_penalty")
        register_custom_template(pt, MockPenaltyParameters)

        carbon_config = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=CarbonTaxParameters(rate_schedule={2026: 44.6}),
            name="Carbon Tax",
        )
        malus_config = PolicyConfig(
            policy_type=pt,
            policy=MockPenaltyParameters(rate_schedule={2026: 50.0}),
            name="Test Penalty",
        )
        portfolio = PolicyPortfolio(
            name="Mixed Portfolio",
            policies=(carbon_config, malus_config),
        )
        assert portfolio.policy_count == 2

    # AC5b: validate_compatibility detects conflicts with custom types
    def test_validate_compatibility_custom_types(self) -> None:
        """validate_compatibility detects overlapping years with custom types."""
        from reformlab.templates.portfolios.composition import validate_compatibility
        from reformlab.templates.portfolios.portfolio import PolicyConfig, PolicyPortfolio
        from reformlab.templates.schema import (
            CarbonTaxParameters,
            PolicyType,
            register_custom_template,
            register_policy_type,
        )

        pt = register_policy_type("test_penalty")
        register_custom_template(pt, MockPenaltyParameters)

        carbon_config = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=CarbonTaxParameters(rate_schedule={2026: 44.6}, covered_categories=("transport_fuel",)),
            name="Carbon Tax",
        )
        malus_config = PolicyConfig(
            policy_type=pt,
            policy=MockPenaltyParameters(rate_schedule={2026: 50.0}, covered_categories=("transport_fuel",)),
            name="Test Penalty",
        )
        portfolio = PolicyPortfolio(
            name="Overlapping",
            policies=(carbon_config, malus_config),
        )
        conflicts = validate_compatibility(portfolio)
        # Should detect overlapping years and overlapping categories
        assert len(conflicts) >= 2
        conflict_types = {c.conflict_type.value for c in conflicts}
        assert "overlapping_years" in conflict_types
        assert "overlapping_categories" in conflict_types

    # AC5c: portfolio YAML round-trip preserves custom parameters
    def test_portfolio_yaml_round_trip_custom(self, tmp_path: Any) -> None:
        """portfolio dump -> load round-trip preserves custom parameters."""
        from reformlab.templates.portfolios.composition import (
            dict_to_portfolio,
            portfolio_to_dict,
        )
        from reformlab.templates.portfolios.portfolio import PolicyConfig, PolicyPortfolio
        from reformlab.templates.schema import (
            CarbonTaxParameters,
            PolicyType,
            register_custom_template,
            register_policy_type,
        )

        pt = register_policy_type("test_penalty")
        register_custom_template(pt, MockPenaltyParameters)

        carbon_config = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=CarbonTaxParameters(rate_schedule={2026: 44.6}),
            name="Carbon Tax",
        )
        malus_config = PolicyConfig(
            policy_type=pt,
            policy=MockPenaltyParameters(
                rate_schedule={2027: 50.0}, emission_threshold=130.0, malus_rate=60.0,
            ),
            name="Test Penalty",
        )
        portfolio = PolicyPortfolio(
            name="Round Trip Test",
            policies=(carbon_config, malus_config),
        )
        data = portfolio_to_dict(portfolio)
        reloaded = dict_to_portfolio(data)
        assert reloaded.policy_count == 2
        assert isinstance(reloaded.policies[1].policy, MockPenaltyParameters)
        assert reloaded.policies[1].policy.emission_threshold == 130.0
        assert reloaded.policies[1].policy.malus_rate == 60.0


# ====================================================================
# TestCustomTemplateOrchestrator — AC5d
# ====================================================================


class TestCustomTemplateOrchestrator:
    """Tests for custom templates through PortfolioComputationStep."""

    def _register_test_penalty(self) -> None:
        from reformlab.templates.schema import register_custom_template, register_policy_type

        register_policy_type("test_penalty")
        register_custom_template("test_penalty", MockPenaltyParameters)

    # AC5d: PortfolioComputationStep passes custom parameters to adapter via asdict()
    def test_to_computation_policy_custom_fields(self) -> None:
        """_to_computation_policy includes custom fields in the output dict."""
        from reformlab.orchestrator.portfolio_step import _to_computation_policy
        from reformlab.templates.portfolios.portfolio import PolicyConfig
        from reformlab.templates.schema import register_custom_template, register_policy_type

        pt = register_policy_type("test_penalty")
        register_custom_template(pt, MockPenaltyParameters)

        config = PolicyConfig(
            policy_type=pt,
            policy=MockPenaltyParameters(
                rate_schedule={2026: 50.0},
                emission_threshold=130.0,
                malus_rate=60.0,
            ),
            name="Test Penalty",
        )
        comp_policy = _to_computation_policy(config)
        assert comp_policy.policy.emission_threshold == 130.0
        assert comp_policy.policy.malus_rate == 60.0
        assert comp_policy.policy.rate_schedule == {2026: 50.0}

    # AC5d / Task 5.3: integration test — custom template through orchestrator yearly loop
    def test_execute_with_custom_template(self) -> None:
        """PortfolioComputationStep.execute() passes custom fields to adapter and merges output."""
        import pyarrow as pa

        from reformlab.computation.mock_adapter import MockAdapter
        from reformlab.computation.types import PopulationData
        from reformlab.orchestrator.portfolio_step import (
            COMPUTATION_RESULT_KEY,
            PortfolioComputationStep,
        )
        from reformlab.orchestrator.types import YearState
        from reformlab.templates.portfolios.portfolio import PolicyConfig, PolicyPortfolio
        from reformlab.templates.schema import (
            CarbonTaxParameters,
            PolicyType,
            register_custom_template,
            register_policy_type,
        )

        pt = register_policy_type("test_penalty")
        register_custom_template(pt, MockPenaltyParameters)

        output = pa.table({
            "household_id": pa.array([1, 2, 3]),
            "amount": pa.array([100.0, 200.0, 300.0]),
        })
        adapter = MockAdapter(version_string="mock-1.0", default_output=output)
        population = PopulationData(tables={})

        carbon_config = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=CarbonTaxParameters(rate_schedule={2026: 44.6}),
            name="Carbon Tax",
        )
        malus_config = PolicyConfig(
            policy_type=pt,
            policy=MockPenaltyParameters(
                rate_schedule={2026: 50.0},
                emission_threshold=130.0,
                malus_rate=60.0,
            ),
            name="Test Penalty",
        )
        portfolio = PolicyPortfolio(
            name="Integration Test",
            policies=(carbon_config, malus_config),
        )

        step = PortfolioComputationStep(
            adapter=adapter,
            population=population,
            portfolio=portfolio,
        )
        state = YearState(year=2026, data={}, seed=42, metadata={})
        new_state = step.execute(year=2026, state=state)

        # Verify adapter was called twice (once per policy)
        assert len(adapter.call_log) == 2
        assert adapter.call_log[0]["policy_name"] == "Carbon Tax"
        assert adapter.call_log[1]["policy_name"] == "Test Penalty"

        # Verify merged result is in state
        assert COMPUTATION_RESULT_KEY in new_state.data
        merged_result = new_state.data[COMPUTATION_RESULT_KEY]
        assert merged_result.output_fields.num_rows == 3

    # AC5: validate_policy_type accepts custom types
    def test_portfolio_step_accepts_custom_type(self) -> None:
        """PortfolioComputationStep construction succeeds with custom types."""
        from unittest.mock import MagicMock

        from reformlab.orchestrator.portfolio_step import PortfolioComputationStep
        from reformlab.templates.portfolios.portfolio import PolicyConfig, PolicyPortfolio
        from reformlab.templates.schema import (
            CarbonTaxParameters,
            PolicyType,
            register_custom_template,
            register_policy_type,
        )

        pt = register_policy_type("test_penalty")
        register_custom_template(pt, MockPenaltyParameters)

        carbon_config = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=CarbonTaxParameters(rate_schedule={2026: 44.6}),
            name="Carbon Tax",
        )
        malus_config = PolicyConfig(
            policy_type=pt,
            policy=MockPenaltyParameters(rate_schedule={2026: 50.0}),
            name="Test Penalty",
        )
        portfolio = PolicyPortfolio(
            name="Test",
            policies=(carbon_config, malus_config),
        )

        mock_adapter = MagicMock()
        mock_adapter.version.return_value = "mock-1.0"

        step = PortfolioComputationStep(
            adapter=mock_adapter,
            population={},
            portfolio=portfolio,
        )
        assert step.name == "portfolio_computation"
