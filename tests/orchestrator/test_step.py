"""Tests for the orchestrator step interface.

Tests for:
- OrchestratorStep Protocol validation (AC-1, AC-3)
- Function-step decorator (AC-4)
- Callable adapter behavior (AC-5)
- Step-specific error classes (AC-3)
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

import pytest

from reformlab.orchestrator.types import YearState

if TYPE_CHECKING:
    pass


# ============================================================================
# Test: OrchestratorStep Protocol (AC-1, AC-3)
# ============================================================================


class TestOrchestratorStepProtocol:
    """Tests for OrchestratorStep Protocol validation."""

    def test_valid_class_step_satisfies_protocol(self):
        """A class with name and execute satisfies OrchestratorStep."""
        from reformlab.orchestrator.step import OrchestratorStep

        @dataclass
        class ValidStep:
            name: str = "valid_step"

            def execute(self, year: int, state: YearState) -> YearState:
                return state

        step = ValidStep()
        assert isinstance(step, OrchestratorStep)

    def test_protocol_is_runtime_checkable(self):
        """OrchestratorStep Protocol is runtime_checkable."""
        from reformlab.orchestrator.step import OrchestratorStep

        @dataclass
        class ValidStep:
            name: str = "test"

            def execute(self, year: int, state: YearState) -> YearState:
                return state

        step = ValidStep()
        # Should be able to use isinstance
        assert isinstance(step, OrchestratorStep)

    def test_class_missing_name_does_not_satisfy_protocol(self):
        """A class without 'name' attribute does not satisfy Protocol."""
        from reformlab.orchestrator.step import OrchestratorStep

        class MissingName:
            def execute(self, year: int, state: YearState) -> YearState:
                return state

        step = MissingName()
        assert not isinstance(step, OrchestratorStep)

    def test_class_missing_execute_does_not_satisfy_protocol(self):
        """A class without 'execute' method does not satisfy Protocol."""
        from reformlab.orchestrator.step import OrchestratorStep

        @dataclass
        class MissingExecute:
            name: str = "test"

        step = MissingExecute()
        assert not isinstance(step, OrchestratorStep)

    def test_step_with_depends_on_property(self):
        """Step with depends_on property works correctly."""
        from reformlab.orchestrator.step import OrchestratorStep

        @dataclass
        class StepWithDeps:
            name: str = "dependent_step"

            @property
            def depends_on(self) -> tuple[str, ...]:
                return ("carry_forward", "vintage_transition")

            def execute(self, year: int, state: YearState) -> YearState:
                return state

        step = StepWithDeps()
        assert isinstance(step, OrchestratorStep)
        assert step.depends_on == ("carry_forward", "vintage_transition")

    def test_step_with_description_property(self):
        """Step with description property works correctly."""
        from reformlab.orchestrator.step import OrchestratorStep

        @dataclass
        class StepWithDesc:
            name: str = "described_step"

            @property
            def description(self) -> str | None:
                return "A step with description"

            def execute(self, year: int, state: YearState) -> YearState:
                return state

        step = StepWithDesc()
        assert isinstance(step, OrchestratorStep)
        assert step.description == "A step with description"


# ============================================================================
# Test: Step-specific errors (AC-3)
# ============================================================================


class TestStepErrors:
    """Tests for step-specific error classes."""

    def test_step_validation_error_exists(self):
        """StepValidationError can be raised with step info."""
        from reformlab.orchestrator.step import StepValidationError

        with pytest.raises(StepValidationError) as exc_info:
            raise StepValidationError("step 'bad_step' missing 'execute' method")

        assert "bad_step" in str(exc_info.value)
        assert "execute" in str(exc_info.value)

    def test_step_registration_error_exists(self):
        """StepRegistrationError can be raised with step info."""
        from reformlab.orchestrator.step import StepRegistrationError

        with pytest.raises(StepRegistrationError) as exc_info:
            raise StepRegistrationError("duplicate step name: 'my_step'")

        assert "my_step" in str(exc_info.value)

    def test_circular_dependency_error_exists(self):
        """CircularDependencyError can be raised with cycle info."""
        from reformlab.orchestrator.step import CircularDependencyError

        with pytest.raises(CircularDependencyError) as exc_info:
            raise CircularDependencyError("cycle detected: step_a -> step_b -> step_a")

        assert "cycle" in str(exc_info.value).lower()


# ============================================================================
# Test: Function step decorator (AC-4)
# ============================================================================


class TestStepDecorator:
    """Tests for the @step function decorator."""

    def test_decorator_creates_protocol_step(self):
        """@step decorator creates object satisfying OrchestratorStep."""
        from reformlab.orchestrator.step import OrchestratorStep, step

        @step()
        def my_function_step(year: int, state: YearState) -> YearState:
            return state

        assert isinstance(my_function_step, OrchestratorStep)

    def test_decorator_default_name_is_function_name(self):
        """@step decorator default name is function.__name__."""
        from reformlab.orchestrator.step import step

        @step()
        def named_step(year: int, state: YearState) -> YearState:
            return state

        assert named_step.name == "named_step"

    def test_decorator_custom_name(self):
        """@step decorator accepts custom name."""
        from reformlab.orchestrator.step import step

        @step(name="custom_name")
        def original_name(year: int, state: YearState) -> YearState:
            return state

        assert original_name.name == "custom_name"

    def test_decorator_default_depends_on_is_empty(self):
        """@step decorator default depends_on is empty tuple."""
        from reformlab.orchestrator.step import step

        @step()
        def independent_step(year: int, state: YearState) -> YearState:
            return state

        assert independent_step.depends_on == ()

    def test_decorator_custom_depends_on(self):
        """@step decorator accepts custom depends_on."""
        from reformlab.orchestrator.step import step

        @step(depends_on=("carry_forward", "vintage"))
        def dependent_step(year: int, state: YearState) -> YearState:
            return state

        assert dependent_step.depends_on == ("carry_forward", "vintage")

    def test_decorator_custom_description(self):
        """@step decorator accepts custom description."""
        from reformlab.orchestrator.step import step

        @step(description="A test step")
        def described_step(year: int, state: YearState) -> YearState:
            return state

        assert described_step.description == "A test step"

    def test_decorated_step_execute_works(self):
        """Decorated step execute() method works correctly."""
        from reformlab.orchestrator.step import step

        @step()
        def increment_step(year: int, state: YearState) -> YearState:
            new_data = dict(state.data)
            new_data["count"] = new_data.get("count", 0) + 1
            return replace(state, data=new_data)

        state = YearState(year=2025, data={"count": 0})
        result = increment_step.execute(2025, state)

        assert result.data["count"] == 1

    def test_decorated_step_is_callable(self):
        """Decorated step can be called directly like original function."""
        from reformlab.orchestrator.step import step

        @step()
        def increment_step(year: int, state: YearState) -> YearState:
            new_data = dict(state.data)
            new_data["count"] = new_data.get("count", 0) + 1
            return replace(state, data=new_data)

        state = YearState(year=2025, data={"count": 0})
        # Should work when called directly
        result = increment_step(2025, state)
        assert result.data["count"] == 1


# ============================================================================
# Test: Callable adapter (AC-5)
# ============================================================================


class TestCallableAdapter:
    """Tests for bare callable adapter for mixed pipelines."""

    def test_adapt_bare_callable_to_protocol_step(self):
        """adapt_callable wraps bare callable as OrchestratorStep."""
        from reformlab.orchestrator.step import OrchestratorStep, adapt_callable

        def bare_step(year: int, state: YearState) -> YearState:
            return state

        adapted = adapt_callable(bare_step)
        assert isinstance(adapted, OrchestratorStep)

    def test_adapted_callable_uses_function_name(self):
        """Adapted callable uses function __name__ as step name."""
        from reformlab.orchestrator.step import adapt_callable

        def my_bare_step(year: int, state: YearState) -> YearState:
            return state

        adapted = adapt_callable(my_bare_step)
        assert adapted.name == "my_bare_step"

    def test_adapted_callable_has_empty_depends_on(self):
        """Adapted callable has empty depends_on."""
        from reformlab.orchestrator.step import adapt_callable

        def bare_step(year: int, state: YearState) -> YearState:
            return state

        adapted = adapt_callable(bare_step)
        assert adapted.depends_on == ()

    def test_adapted_callable_execute_works(self):
        """Adapted callable execute() delegates to original function."""
        from reformlab.orchestrator.step import adapt_callable

        def incrementer(year: int, state: YearState) -> YearState:
            new_data = dict(state.data)
            new_data["value"] = new_data.get("value", 0) + year
            return replace(state, data=new_data)

        adapted = adapt_callable(incrementer)
        state = YearState(year=2025, data={"value": 100})
        result = adapted.execute(2025, state)

        assert result.data["value"] == 2125

    def test_adapt_callable_custom_name(self):
        """adapt_callable accepts custom name override."""
        from reformlab.orchestrator.step import adapt_callable

        def bare_step(year: int, state: YearState) -> YearState:
            return state

        adapted = adapt_callable(bare_step, name="custom_name")
        assert adapted.name == "custom_name"

    def test_is_protocol_step_returns_true_for_protocol_step(self):
        """is_protocol_step returns True for OrchestratorStep."""
        from reformlab.orchestrator.step import is_protocol_step

        @dataclass
        class ValidStep:
            name: str = "test"

            def execute(self, year: int, state: YearState) -> YearState:
                return state

        step = ValidStep()
        assert is_protocol_step(step)

    def test_is_protocol_step_returns_false_for_bare_callable(self):
        """is_protocol_step returns False for bare callable."""
        from reformlab.orchestrator.step import is_protocol_step

        def bare_step(year: int, state: YearState) -> YearState:
            return state

        assert not is_protocol_step(bare_step)
