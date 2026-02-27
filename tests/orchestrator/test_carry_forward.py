"""Tests for carry-forward step implementation.

Tests for:
- CarryForwardRule and CarryForwardConfig validation
- CarryForwardStep execution with all rule types
- NFR10 compliance (period semantics validation)
- Determinism guarantees
- Integration with StepRegistry and Orchestrator
"""

from __future__ import annotations

from typing import Any

import pytest

from reformlab.orchestrator import YearState
from reformlab.orchestrator.carry_forward import (
    CarryForwardConfig,
    CarryForwardConfigError,
    CarryForwardExecutionError,
    CarryForwardRule,
    CarryForwardStep,
)
from reformlab.orchestrator.step import StepRegistry

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_state() -> YearState:
    """Create a sample state for testing."""
    return YearState(
        year=2024,
        data={
            "income": 50000.0,
            "household_size": 3,
            "carbon_tax_rate": 0.05,
        },
        seed=42,
        metadata={},
    )


@pytest.fixture
def static_rule() -> CarryForwardRule:
    """Create a static rule that preserves values."""
    return CarryForwardRule(
        variable="household_size",
        rule_type="static",
        period_semantics="annual_constant",
    )


@pytest.fixture
def scale_rule() -> CarryForwardRule:
    """Create a scale rule that multiplies values."""
    return CarryForwardRule(
        variable="income",
        rule_type="scale",
        period_semantics="annual_growth_rate",
        value=1.02,  # 2% annual increase
    )


@pytest.fixture
def increment_rule() -> CarryForwardRule:
    """Create an increment rule that adds values."""
    return CarryForwardRule(
        variable="carbon_tax_rate",
        rule_type="increment",
        period_semantics="annual_increment",
        value=0.01,  # Add 0.01 each year
    )


# ============================================================================
# CarryForwardRule Tests - Configuration Validation
# ============================================================================


class TestCarryForwardRuleValidation:
    """Tests for CarryForwardRule configuration validation."""

    def test_valid_static_rule(self, static_rule: CarryForwardRule) -> None:
        """Valid static rule should be created successfully."""
        assert static_rule.variable == "household_size"
        assert static_rule.rule_type == "static"
        assert static_rule.period_semantics == "annual_constant"
        assert static_rule.value is None
        assert static_rule.custom_fn is None

    def test_valid_scale_rule(self, scale_rule: CarryForwardRule) -> None:
        """Valid scale rule should be created successfully."""
        assert scale_rule.variable == "income"
        assert scale_rule.rule_type == "scale"
        assert scale_rule.period_semantics == "annual_growth_rate"
        assert scale_rule.value == 1.02

    def test_valid_increment_rule(self, increment_rule: CarryForwardRule) -> None:
        """Valid increment rule should be created successfully."""
        assert increment_rule.variable == "carbon_tax_rate"
        assert increment_rule.rule_type == "increment"
        assert increment_rule.period_semantics == "annual_increment"
        assert increment_rule.value == 0.01

    def test_valid_custom_rule(self) -> None:
        """Valid custom rule with callable should be created successfully."""

        def custom_updater(year: int, current: Any, state: YearState) -> Any:
            return current + year

        rule = CarryForwardRule(
            variable="custom_var",
            rule_type="custom",
            period_semantics="custom_logic",
            custom_fn=custom_updater,
        )
        assert rule.variable == "custom_var"
        assert rule.rule_type == "custom"
        assert rule.custom_fn is custom_updater

    def test_missing_period_semantics_rejected_nfr10(self) -> None:
        """Rule without period_semantics should be rejected (NFR10 compliance)."""
        with pytest.raises(CarryForwardConfigError) as exc_info:
            CarryForwardRule(
                variable="income",
                rule_type="static",
                period_semantics="",  # Empty is not allowed
            )
        assert "period_semantics" in str(exc_info.value).lower()
        assert "income" in str(exc_info.value)

    def test_scale_rule_requires_value(self) -> None:
        """Scale rule without value should raise error during execution."""
        rule = CarryForwardRule(
            variable="income",
            rule_type="scale",
            period_semantics="annual_growth",
            value=None,  # Missing value
        )
        # Rule creation succeeds, but execution should fail
        assert rule.value is None

    def test_increment_rule_requires_value(self) -> None:
        """Increment rule without value should raise error during execution."""
        rule = CarryForwardRule(
            variable="tax_rate",
            rule_type="increment",
            period_semantics="annual_increment",
            value=None,  # Missing value
        )
        # Rule creation succeeds, but execution should fail
        assert rule.value is None


# ============================================================================
# CarryForwardConfig Tests
# ============================================================================


class TestCarryForwardConfig:
    """Tests for CarryForwardConfig validation."""

    def test_valid_config_with_multiple_rules(
        self,
        static_rule: CarryForwardRule,
        scale_rule: CarryForwardRule,
        increment_rule: CarryForwardRule,
    ) -> None:
        """Config with multiple valid rules should be created."""
        config = CarryForwardConfig(
            rules=(static_rule, scale_rule, increment_rule),
        )
        assert len(config.rules) == 3
        assert config.strict_period is True  # Default

    def test_config_with_empty_rules(self) -> None:
        """Config with empty rules should be valid (no-op step)."""
        config = CarryForwardConfig(rules=())
        assert len(config.rules) == 0

    def test_config_strict_period_default(self, static_rule: CarryForwardRule) -> None:
        """Config should have strict_period=True by default."""
        config = CarryForwardConfig(rules=(static_rule,))
        assert config.strict_period is True

    def test_config_strict_period_can_be_disabled(
        self, static_rule: CarryForwardRule
    ) -> None:
        """Config strict_period can be explicitly set to False."""
        config = CarryForwardConfig(rules=(static_rule,), strict_period=False)
        assert config.strict_period is False


# ============================================================================
# CarryForwardStep Tests - Rule Execution
# ============================================================================


class TestCarryForwardStepExecution:
    """Tests for CarryForwardStep rule execution."""

    def test_static_rule_preserves_value(
        self,
        sample_state: YearState,
        static_rule: CarryForwardRule,
    ) -> None:
        """Static rule should preserve the value unchanged."""
        config = CarryForwardConfig(rules=(static_rule,))
        step = CarryForwardStep(config)

        result = step.execute(2025, sample_state)

        assert result.data["household_size"] == 3

    def test_scale_rule_multiplies_value(
        self,
        sample_state: YearState,
        scale_rule: CarryForwardRule,
    ) -> None:
        """Scale rule should multiply value by factor."""
        config = CarryForwardConfig(rules=(scale_rule,))
        step = CarryForwardStep(config)

        result = step.execute(2025, sample_state)

        expected = 50000.0 * 1.02
        assert result.data["income"] == expected

    def test_increment_rule_adds_value(
        self,
        sample_state: YearState,
        increment_rule: CarryForwardRule,
    ) -> None:
        """Increment rule should add value."""
        config = CarryForwardConfig(rules=(increment_rule,))
        step = CarryForwardStep(config)

        result = step.execute(2025, sample_state)

        expected = 0.05 + 0.01
        assert result.data["carbon_tax_rate"] == pytest.approx(expected)

    def test_custom_rule_executes_callable(
        self,
        sample_state: YearState,
    ) -> None:
        """Custom rule should execute the provided callable."""

        def double_income(year: int, current: Any, state: YearState) -> Any:
            return current * 2

        rule = CarryForwardRule(
            variable="income",
            rule_type="custom",
            period_semantics="custom_doubling",
            custom_fn=double_income,
        )
        config = CarryForwardConfig(rules=(rule,))
        step = CarryForwardStep(config)

        result = step.execute(2025, sample_state)

        assert result.data["income"] == 100000.0

    def test_custom_rule_receives_year_and_state(
        self,
        sample_state: YearState,
    ) -> None:
        """Custom rule should receive year and full state."""
        received_args: list[tuple[int, Any, YearState]] = []

        def capture_args(year: int, current: Any, state: YearState) -> Any:
            received_args.append((year, current, state))
            return current

        rule = CarryForwardRule(
            variable="income",
            rule_type="custom",
            period_semantics="capture_test",
            custom_fn=capture_args,
        )
        config = CarryForwardConfig(rules=(rule,))
        step = CarryForwardStep(config)

        step.execute(2030, sample_state)

        assert len(received_args) == 1
        year, current, state = received_args[0]
        assert year == 2030
        assert current == 50000.0
        assert state is sample_state

    def test_multiple_rules_all_applied(
        self,
        sample_state: YearState,
        static_rule: CarryForwardRule,
        scale_rule: CarryForwardRule,
        increment_rule: CarryForwardRule,
    ) -> None:
        """Multiple rules should all be applied to their respective variables."""
        config = CarryForwardConfig(
            rules=(static_rule, scale_rule, increment_rule),
        )
        step = CarryForwardStep(config)

        result = step.execute(2025, sample_state)

        assert result.data["household_size"] == 3
        assert result.data["income"] == 50000.0 * 1.02
        assert result.data["carbon_tax_rate"] == pytest.approx(0.06)

    def test_empty_rules_returns_unchanged_state(
        self,
        sample_state: YearState,
    ) -> None:
        """Empty rules should return state with unchanged data."""
        config = CarryForwardConfig(rules=())
        step = CarryForwardStep(config)

        result = step.execute(2025, sample_state)

        assert result.data == sample_state.data

    def test_state_immutability_preserved(
        self,
        sample_state: YearState,
        scale_rule: CarryForwardRule,
    ) -> None:
        """Step should return new state without modifying original."""
        original_data = dict(sample_state.data)
        config = CarryForwardConfig(rules=(scale_rule,))
        step = CarryForwardStep(config)

        result = step.execute(2025, sample_state)

        # Original state unchanged
        assert sample_state.data == original_data
        # Result is new state
        assert result is not sample_state
        assert result.data["income"] != sample_state.data["income"]


# ============================================================================
# CarryForwardStep Tests - Error Handling
# ============================================================================


class TestCarryForwardStepErrors:
    """Tests for CarryForwardStep error handling."""

    def test_scale_rule_missing_value_raises_execution_error(
        self,
        sample_state: YearState,
    ) -> None:
        """Scale rule without value should raise CarryForwardExecutionError."""
        rule = CarryForwardRule(
            variable="income",
            rule_type="scale",
            period_semantics="annual_growth",
            value=None,
        )
        config = CarryForwardConfig(rules=(rule,))
        step = CarryForwardStep(config)

        with pytest.raises(CarryForwardExecutionError) as exc_info:
            step.execute(2025, sample_state)

        assert "income" in str(exc_info.value)
        assert "scale" in str(exc_info.value).lower()

    def test_increment_rule_missing_value_raises_execution_error(
        self,
        sample_state: YearState,
    ) -> None:
        """Increment rule without value should raise CarryForwardExecutionError."""
        rule = CarryForwardRule(
            variable="carbon_tax_rate",
            rule_type="increment",
            period_semantics="annual_increment",
            value=None,
        )
        config = CarryForwardConfig(rules=(rule,))
        step = CarryForwardStep(config)

        with pytest.raises(CarryForwardExecutionError) as exc_info:
            step.execute(2025, sample_state)

        assert "carbon_tax_rate" in str(exc_info.value)
        assert "increment" in str(exc_info.value).lower()

    def test_custom_rule_missing_callable_raises_execution_error(
        self,
        sample_state: YearState,
    ) -> None:
        """Custom rule without callable should raise CarryForwardExecutionError."""
        rule = CarryForwardRule(
            variable="income",
            rule_type="custom",
            period_semantics="custom_logic",
            custom_fn=None,
        )
        config = CarryForwardConfig(rules=(rule,))
        step = CarryForwardStep(config)

        with pytest.raises(CarryForwardExecutionError) as exc_info:
            step.execute(2025, sample_state)

        assert "income" in str(exc_info.value)
        assert "custom" in str(exc_info.value).lower()

    def test_scale_rule_missing_state_variable_raises_execution_error(
        self,
        sample_state: YearState,
    ) -> None:
        """Scale rule for missing variable should raise CarryForwardExecutionError."""
        rule = CarryForwardRule(
            variable="nonexistent_var",
            rule_type="scale",
            period_semantics="annual_growth",
            value=1.05,
        )
        config = CarryForwardConfig(rules=(rule,))
        step = CarryForwardStep(config)

        with pytest.raises(CarryForwardExecutionError) as exc_info:
            step.execute(2025, sample_state)

        assert "nonexistent_var" in str(exc_info.value)

    def test_custom_rule_exception_wrapped_in_execution_error(
        self,
        sample_state: YearState,
    ) -> None:
        """Exception in custom rule should be wrapped in CarryForwardExecutionError."""

        def failing_custom(year: int, current: Any, state: YearState) -> Any:
            raise ValueError("Custom rule failed")

        rule = CarryForwardRule(
            variable="income",
            rule_type="custom",
            period_semantics="failing_custom",
            custom_fn=failing_custom,
        )
        config = CarryForwardConfig(rules=(rule,))
        step = CarryForwardStep(config)

        with pytest.raises(CarryForwardExecutionError) as exc_info:
            step.execute(2025, sample_state)

        assert "income" in str(exc_info.value)
        assert "Custom rule failed" in str(exc_info.value)


# ============================================================================
# Determinism Tests
# ============================================================================


class TestCarryForwardDeterminism:
    """Tests for determinism guarantees."""

    def test_identical_inputs_produce_identical_outputs(
        self,
        sample_state: YearState,
        static_rule: CarryForwardRule,
        scale_rule: CarryForwardRule,
        increment_rule: CarryForwardRule,
    ) -> None:
        """Same inputs should produce bit-identical outputs."""
        config = CarryForwardConfig(
            rules=(static_rule, scale_rule, increment_rule),
        )
        step = CarryForwardStep(config)

        result1 = step.execute(2025, sample_state)
        result2 = step.execute(2025, sample_state)

        assert result1.data == result2.data
        assert result1.year == result2.year
        assert result1.seed == result2.seed

    def test_rules_applied_in_sorted_order(self) -> None:
        """Rules should be applied in sorted order by variable name."""
        application_order: list[str] = []

        def track_order(var_name: str):
            def custom_fn(year: int, current: Any, state: YearState) -> Any:
                application_order.append(var_name)
                return current

            return custom_fn

        rules = (
            CarryForwardRule(
                variable="zebra",
                rule_type="custom",
                period_semantics="test",
                custom_fn=track_order("zebra"),
            ),
            CarryForwardRule(
                variable="apple",
                rule_type="custom",
                period_semantics="test",
                custom_fn=track_order("apple"),
            ),
            CarryForwardRule(
                variable="mango",
                rule_type="custom",
                period_semantics="test",
                custom_fn=track_order("mango"),
            ),
        )

        state = YearState(
            year=2024,
            data={"zebra": 1, "apple": 2, "mango": 3},
        )
        config = CarryForwardConfig(rules=rules)
        step = CarryForwardStep(config)

        step.execute(2025, state)

        assert application_order == ["apple", "mango", "zebra"]

    def test_determinism_across_multiple_runs(
        self,
        sample_state: YearState,
        scale_rule: CarryForwardRule,
    ) -> None:
        """Multiple runs with same input should be deterministic."""
        config = CarryForwardConfig(rules=(scale_rule,))
        step = CarryForwardStep(config)

        results = [step.execute(2025, sample_state) for _ in range(10)]

        first_result = results[0]
        for result in results[1:]:
            assert result.data == first_result.data


# ============================================================================
# OrchestratorStep Protocol Tests
# ============================================================================


class TestCarryForwardStepProtocol:
    """Tests for OrchestratorStep protocol compliance."""

    def test_step_has_name_property(self, static_rule: CarryForwardRule) -> None:
        """Step should have name property."""
        config = CarryForwardConfig(rules=(static_rule,))
        step = CarryForwardStep(config)

        assert step.name == "carry_forward"

    def test_step_custom_name(self, static_rule: CarryForwardRule) -> None:
        """Step should allow custom name."""
        config = CarryForwardConfig(rules=(static_rule,))
        step = CarryForwardStep(config, name="my_carry_forward")

        assert step.name == "my_carry_forward"

    def test_step_has_depends_on_property(
        self, static_rule: CarryForwardRule
    ) -> None:
        """Step should have depends_on property defaulting to empty."""
        config = CarryForwardConfig(rules=(static_rule,))
        step = CarryForwardStep(config)

        assert step.depends_on == ()

    def test_step_custom_depends_on(self, static_rule: CarryForwardRule) -> None:
        """Step should allow custom depends_on."""
        config = CarryForwardConfig(rules=(static_rule,))
        step = CarryForwardStep(
            config,
            depends_on=("init_population", "load_data"),
        )

        assert step.depends_on == ("init_population", "load_data")

    def test_step_has_description(self, static_rule: CarryForwardRule) -> None:
        """Step should have description property."""
        config = CarryForwardConfig(rules=(static_rule,))
        step = CarryForwardStep(config)

        assert step.description is not None
        assert "carry" in step.description.lower()

    def test_step_has_execute_method(
        self,
        sample_state: YearState,
        static_rule: CarryForwardRule,
    ) -> None:
        """Step should have execute method with correct signature."""
        config = CarryForwardConfig(rules=(static_rule,))
        step = CarryForwardStep(config)

        result = step.execute(2025, sample_state)

        assert isinstance(result, YearState)

    def test_step_is_runtime_checkable(
        self, static_rule: CarryForwardRule
    ) -> None:
        """Step should pass OrchestratorStep isinstance check."""
        from reformlab.orchestrator.step import OrchestratorStep, is_protocol_step

        config = CarryForwardConfig(rules=(static_rule,))
        step = CarryForwardStep(config)

        assert isinstance(step, OrchestratorStep)
        assert is_protocol_step(step)


# ============================================================================
# StepRegistry Integration Tests
# ============================================================================


class TestCarryForwardStepRegistryIntegration:
    """Tests for integration with StepRegistry."""

    def test_step_can_be_registered(self, static_rule: CarryForwardRule) -> None:
        """CarryForwardStep should register successfully."""
        config = CarryForwardConfig(rules=(static_rule,))
        step = CarryForwardStep(config)
        registry = StepRegistry()

        registry.register(step)

        assert registry.get("carry_forward") is step
        assert len(registry) == 1

    def test_step_works_in_pipeline(
        self,
        sample_state: YearState,
        scale_rule: CarryForwardRule,
    ) -> None:
        """CarryForwardStep should work in registry-built pipeline."""
        from reformlab.orchestrator import Orchestrator, OrchestratorConfig

        config = CarryForwardConfig(rules=(scale_rule,))
        step = CarryForwardStep(config)
        registry = StepRegistry()
        registry.register(step)

        pipeline = registry.build_pipeline()
        orch_config = OrchestratorConfig(
            start_year=2024,
            end_year=2025,
            initial_state=sample_state.data,
            seed=42,
            step_pipeline=pipeline,
        )
        orchestrator = Orchestrator(orch_config)
        result = orchestrator.run()

        assert result.success
        # After two years of 2% growth from 50000
        # 2024: 50000 * 1.02 = 51000
        # 2025: 51000 * 1.02 = 52020
        assert result.yearly_states[2025].data["income"] == pytest.approx(52020.0)

    def test_step_dependency_ordering(
        self,
        sample_state: YearState,
    ) -> None:
        """CarryForwardStep with depends_on should respect ordering."""
        from reformlab.orchestrator import adapt_callable

        execution_order: list[str] = []

        def prereq_step(year: int, state: YearState) -> YearState:
            execution_order.append("prereq")
            return state

        rule = CarryForwardRule(
            variable="income",
            rule_type="custom",
            period_semantics="test",
            custom_fn=lambda y, c, s: (execution_order.append("carry_forward"), c)[1],
        )
        config = CarryForwardConfig(rules=(rule,))
        carry_step = CarryForwardStep(
            config,
            name="carry_forward",
            depends_on=("prereq",),
        )

        registry = StepRegistry()
        registry.register(adapt_callable(prereq_step, name="prereq"))
        registry.register(carry_step)

        pipeline = registry.build_pipeline()

        # Execute pipeline
        state = sample_state
        for step in pipeline:
            state = step.execute(2025, state)

        assert execution_order == ["prereq", "carry_forward"]

    def test_multiple_carry_forward_steps_with_dependencies(
        self,
        sample_state: YearState,
    ) -> None:
        """Multiple CarryForwardSteps can be ordered via dependencies."""
        execution_order: list[str] = []

        def make_tracker(name: str):
            def track(year: int, current: Any, state: YearState) -> Any:
                execution_order.append(name)
                return current

            return track

        step1 = CarryForwardStep(
            CarryForwardConfig(
                rules=(
                    CarryForwardRule(
                        variable="income",
                        rule_type="custom",
                        period_semantics="test",
                        custom_fn=make_tracker("step1"),
                    ),
                )
            ),
            name="carry_income",
        )

        step2 = CarryForwardStep(
            CarryForwardConfig(
                rules=(
                    CarryForwardRule(
                        variable="household_size",
                        rule_type="custom",
                        period_semantics="test",
                        custom_fn=make_tracker("step2"),
                    ),
                )
            ),
            name="carry_demographics",
            depends_on=("carry_income",),
        )

        registry = StepRegistry()
        registry.register(step1)
        registry.register(step2)

        pipeline = registry.build_pipeline()

        state = sample_state
        for step in pipeline:
            state = step.execute(2025, state)

        assert execution_order == ["step1", "step2"]
