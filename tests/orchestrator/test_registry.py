"""Tests for the StepRegistry.

Tests for:
- Step registration and retrieval (AC-2, AC-3)
- Topological ordering with stable tie handling (AC-2)
- Duplicate name / unknown dependency / cycle detection (AC-3)
- Pipeline build determinism (AC-2)
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import pytest

from reformlab.orchestrator.types import YearState

# ============================================================================
# Fixtures
# ============================================================================


@dataclass
class SimpleStep:
    """Simple step implementation for testing."""

    name: str
    _depends_on: tuple[str, ...] = ()

    @property
    def depends_on(self) -> tuple[str, ...]:
        return self._depends_on

    def execute(self, year: int, state: YearState) -> YearState:
        new_data = dict(state.data)
        executed = list(new_data.get("executed", []))
        executed.append(self.name)
        new_data["executed"] = executed
        return replace(state, data=new_data)


# ============================================================================
# Test: Step registration (AC-2, AC-3)
# ============================================================================


class TestStepRegistration:
    """Tests for step registration in StepRegistry."""

    def test_register_valid_step(self):
        """Valid step can be registered."""
        from reformlab.orchestrator.step import StepRegistry

        registry = StepRegistry()
        step = SimpleStep(name="my_step")

        registry.register(step)

        assert registry.get("my_step") is step

    def test_get_nonexistent_step_returns_none(self):
        """get() returns None for unregistered step name."""
        from reformlab.orchestrator.step import StepRegistry

        registry = StepRegistry()

        assert registry.get("nonexistent") is None

    def test_register_invalid_step_raises_validation_error(self):
        """Registering invalid step raises StepValidationError."""
        from reformlab.orchestrator.step import StepRegistry, StepValidationError

        registry = StepRegistry()

        class InvalidStep:
            # Missing 'name' and 'execute'
            pass

        with pytest.raises(StepValidationError) as exc_info:
            registry.register(InvalidStep())  # type: ignore[arg-type]

        assert (
            "InvalidStep" in str(exc_info.value)
            or "invalid" in str(exc_info.value).lower()
        )

    def test_register_duplicate_name_raises_registration_error(self):
        """Registering step with duplicate name raises StepRegistrationError."""
        from reformlab.orchestrator.step import StepRegistrationError, StepRegistry

        registry = StepRegistry()
        step1 = SimpleStep(name="same_name")
        step2 = SimpleStep(name="same_name")

        registry.register(step1)

        with pytest.raises(StepRegistrationError) as exc_info:
            registry.register(step2)

        assert "same_name" in str(exc_info.value)

    def test_registered_step_count(self):
        """Registry tracks number of registered steps."""
        from reformlab.orchestrator.step import StepRegistry

        registry = StepRegistry()
        assert len(registry) == 0

        registry.register(SimpleStep(name="step1"))
        assert len(registry) == 1

        registry.register(SimpleStep(name="step2"))
        assert len(registry) == 2

    def test_iter_steps(self):
        """Registry is iterable over registered steps."""
        from reformlab.orchestrator.step import StepRegistry

        registry = StepRegistry()
        step1 = SimpleStep(name="step1")
        step2 = SimpleStep(name="step2")

        registry.register(step1)
        registry.register(step2)

        steps = list(registry)
        assert len(steps) == 2
        assert step1 in steps
        assert step2 in steps

    def test_register_step_with_blank_name_raises_validation_error(self):
        """Step names must be non-empty strings."""
        from reformlab.orchestrator.step import StepRegistry, StepValidationError

        @dataclass
        class BlankNameStep:
            name: str = "   "

            def execute(self, year: int, state: YearState) -> YearState:
                return state

        registry = StepRegistry()
        with pytest.raises(StepValidationError) as exc_info:
            registry.register(BlankNameStep())

        assert "invalid name" in str(exc_info.value)

    def test_register_step_with_string_depends_on_raises_validation_error(self):
        """depends_on must be an iterable of step names, not a raw string."""
        from reformlab.orchestrator.step import StepRegistry, StepValidationError

        @dataclass
        class StringDependsStep:
            name: str = "string_depends"
            depends_on: str = "base_step"

            def execute(self, year: int, state: YearState) -> YearState:
                return state

        registry = StepRegistry()
        with pytest.raises(StepValidationError) as exc_info:
            registry.register(StringDependsStep())

        assert "string_depends" in str(exc_info.value)
        assert "depends_on" in str(exc_info.value)

    def test_register_step_with_duplicate_dependencies_raises_validation_error(self):
        """Duplicate names in depends_on are rejected to avoid graph corruption."""
        from reformlab.orchestrator.step import StepRegistry, StepValidationError

        registry = StepRegistry()
        step = SimpleStep(name="dup_dep_step", _depends_on=("base", "base"))

        with pytest.raises(StepValidationError) as exc_info:
            registry.register(step)

        assert "dup_dep_step" in str(exc_info.value)
        assert "duplicate dependency" in str(exc_info.value)


# ============================================================================
# Test: Topological ordering (AC-2)
# ============================================================================


class TestTopologicalOrdering:
    """Tests for dependency-based topological ordering."""

    def test_build_pipeline_no_dependencies(self):
        """Pipeline with no dependencies preserves registration order."""
        from reformlab.orchestrator.step import StepRegistry

        registry = StepRegistry()
        step_a = SimpleStep(name="a")
        step_b = SimpleStep(name="b")
        step_c = SimpleStep(name="c")

        registry.register(step_a)
        registry.register(step_b)
        registry.register(step_c)

        pipeline = registry.build_pipeline()

        assert len(pipeline) == 3
        # Registration order preserved when no dependencies
        names = [s.name for s in pipeline]
        assert names == ["a", "b", "c"]

    def test_build_pipeline_with_dependencies(self):
        """Pipeline respects dependency order."""
        from reformlab.orchestrator.step import StepRegistry

        registry = StepRegistry()

        # c depends on b, b depends on a
        step_a = SimpleStep(name="a")
        step_b = SimpleStep(name="b", _depends_on=("a",))
        step_c = SimpleStep(name="c", _depends_on=("b",))

        # Register in reverse order to test sorting
        registry.register(step_c)
        registry.register(step_b)
        registry.register(step_a)

        pipeline = registry.build_pipeline()
        names = [s.name for s in pipeline]

        # a must come before b, b must come before c
        assert names.index("a") < names.index("b")
        assert names.index("b") < names.index("c")

    def test_build_pipeline_diamond_dependencies(self):
        """Pipeline handles diamond dependency pattern."""
        from reformlab.orchestrator.step import StepRegistry

        registry = StepRegistry()

        #     a
        #    / \
        #   b   c
        #    \ /
        #     d
        step_a = SimpleStep(name="a")
        step_b = SimpleStep(name="b", _depends_on=("a",))
        step_c = SimpleStep(name="c", _depends_on=("a",))
        step_d = SimpleStep(name="d", _depends_on=("b", "c"))

        registry.register(step_d)
        registry.register(step_c)
        registry.register(step_b)
        registry.register(step_a)

        pipeline = registry.build_pipeline()
        names = [s.name for s in pipeline]

        # a must come first
        assert names[0] == "a"
        # d must come last
        assert names[-1] == "d"
        # b and c must come before d but after a
        assert names.index("b") < names.index("d")
        assert names.index("c") < names.index("d")

    def test_build_pipeline_preserves_registration_order_for_ties(self):
        """At same dependency level, registration order is preserved."""
        from reformlab.orchestrator.step import StepRegistry

        registry = StepRegistry()

        # All depend on 'base', registered in order: x, y, z
        step_base = SimpleStep(name="base")
        step_x = SimpleStep(name="x", _depends_on=("base",))
        step_y = SimpleStep(name="y", _depends_on=("base",))
        step_z = SimpleStep(name="z", _depends_on=("base",))

        registry.register(step_base)
        registry.register(step_x)
        registry.register(step_y)
        registry.register(step_z)

        pipeline = registry.build_pipeline()
        names = [s.name for s in pipeline]

        # base is first, then x, y, z in registration order
        assert names[0] == "base"
        # x, y, z should maintain registration order
        remaining = names[1:]
        assert remaining == ["x", "y", "z"]

    def test_build_pipeline_is_deterministic(self):
        """Multiple build_pipeline calls produce identical output."""
        from reformlab.orchestrator.step import StepRegistry

        registry = StepRegistry()

        step_a = SimpleStep(name="a")
        step_b = SimpleStep(name="b", _depends_on=("a",))
        step_c = SimpleStep(name="c", _depends_on=("a",))

        registry.register(step_a)
        registry.register(step_b)
        registry.register(step_c)

        pipeline1 = registry.build_pipeline()
        pipeline2 = registry.build_pipeline()

        names1 = [s.name for s in pipeline1]
        names2 = [s.name for s in pipeline2]

        assert names1 == names2


# ============================================================================
# Test: Error detection (AC-3)
# ============================================================================


class TestErrorDetection:
    """Tests for error detection in StepRegistry."""

    def test_unknown_dependency_raises_registration_error(self):
        """Unknown dependency raises StepRegistrationError on build_pipeline."""
        from reformlab.orchestrator.step import StepRegistrationError, StepRegistry

        registry = StepRegistry()

        step = SimpleStep(name="orphan", _depends_on=("nonexistent",))
        registry.register(step)

        with pytest.raises(StepRegistrationError) as exc_info:
            registry.build_pipeline()

        error_msg = str(exc_info.value)
        assert "nonexistent" in error_msg or "unknown" in error_msg.lower()

    def test_circular_dependency_raises_error(self):
        """Circular dependency raises CircularDependencyError."""
        from reformlab.orchestrator.step import CircularDependencyError, StepRegistry

        registry = StepRegistry()

        # a -> b -> a (cycle)
        step_a = SimpleStep(name="a", _depends_on=("b",))
        step_b = SimpleStep(name="b", _depends_on=("a",))

        registry.register(step_a)
        registry.register(step_b)

        with pytest.raises(CircularDependencyError) as exc_info:
            registry.build_pipeline()

        error_msg = str(exc_info.value)
        assert "cycle" in error_msg.lower() or "circular" in error_msg.lower()

    def test_self_dependency_raises_circular_error(self):
        """Self-dependency raises CircularDependencyError."""
        from reformlab.orchestrator.step import CircularDependencyError, StepRegistry

        registry = StepRegistry()

        step = SimpleStep(name="self_ref", _depends_on=("self_ref",))
        registry.register(step)

        with pytest.raises(CircularDependencyError):
            registry.build_pipeline()

    def test_longer_cycle_detected(self):
        """Longer cycles (a -> b -> c -> a) are detected."""
        from reformlab.orchestrator.step import CircularDependencyError, StepRegistry

        registry = StepRegistry()

        step_a = SimpleStep(name="a", _depends_on=("c",))
        step_b = SimpleStep(name="b", _depends_on=("a",))
        step_c = SimpleStep(name="c", _depends_on=("b",))

        registry.register(step_a)
        registry.register(step_b)
        registry.register(step_c)

        with pytest.raises(CircularDependencyError):
            registry.build_pipeline()

    def test_error_message_includes_step_name(self):
        """Error messages include the problematic step name."""
        from reformlab.orchestrator.step import StepRegistrationError, StepRegistry

        registry = StepRegistry()
        step1 = SimpleStep(name="unique_step")
        step2 = SimpleStep(name="unique_step")

        registry.register(step1)

        with pytest.raises(StepRegistrationError) as exc_info:
            registry.register(step2)

        assert "unique_step" in str(exc_info.value)


# ============================================================================
# Test: Empty registry (edge case)
# ============================================================================


class TestEmptyRegistry:
    """Tests for empty registry edge cases."""

    def test_build_pipeline_empty_registry(self):
        """Empty registry builds empty pipeline."""
        from reformlab.orchestrator.step import StepRegistry

        registry = StepRegistry()
        pipeline = registry.build_pipeline()

        assert pipeline == ()

    def test_empty_registry_len(self):
        """Empty registry has length 0."""
        from reformlab.orchestrator.step import StepRegistry

        registry = StepRegistry()
        assert len(registry) == 0

    def test_empty_registry_iter(self):
        """Empty registry iteration yields nothing."""
        from reformlab.orchestrator.step import StepRegistry

        registry = StepRegistry()
        steps = list(registry)
        assert steps == []
