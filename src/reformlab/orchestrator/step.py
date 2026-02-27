"""Orchestrator step interface and registration.

This module provides:
- OrchestratorStep: Protocol for pipeline steps
- StepRegistry: Registration and dependency ordering
- @step: Decorator for function-based steps
- adapt_callable: Adapter for bare YearStep callables
- Step errors: StepValidationError, StepRegistrationError, CircularDependencyError
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING, Any, Callable, Iterator, Protocol, runtime_checkable

if TYPE_CHECKING:
    from reformlab.orchestrator.types import YearState


# ============================================================================
# Error Classes
# ============================================================================


class StepValidationError(Exception):
    """Error when a step does not implement the required interface."""


class StepRegistrationError(Exception):
    """Error during step registration (e.g., duplicate name, unknown dependency)."""


class CircularDependencyError(Exception):
    """Error when circular dependencies are detected in the step pipeline."""


# ============================================================================
# OrchestratorStep Protocol
# ============================================================================


@runtime_checkable
class OrchestratorStep(Protocol):
    """Protocol for orchestrator pipeline steps.

    A step must provide:
    - name: Unique identifier for the step
    - execute(year, state): Execute the step for a given year

    Optional metadata:
    - depends_on: Names of steps this step depends on (default: empty)
    - description: Human-readable description of the step
    """

    @property
    def name(self) -> str:
        """Unique identifier for this step."""
        ...

    def execute(self, year: int, state: "YearState") -> "YearState":
        """Execute the step for a given year.

        Args:
            year: Current simulation year.
            state: Current year state.

        Returns:
            Updated state after step execution.
        """
        ...


# ============================================================================
# Helper Functions
# ============================================================================


def is_protocol_step(obj: Any) -> bool:
    """Check if an object satisfies the OrchestratorStep protocol.

    Args:
        obj: Object to check.

    Returns:
        True if object satisfies OrchestratorStep protocol.
    """
    return isinstance(obj, OrchestratorStep)


def _get_step_name(step: Any) -> str:
    """Extract step name from various step types.

    Args:
        step: Step object or callable.

    Returns:
        Step name string.
    """
    if hasattr(step, "name"):
        return str(step.name)
    return str(getattr(step, "__name__", str(step)))


def _get_depends_on(step: Any) -> tuple[str, ...]:
    """Extract depends_on from step, defaulting to empty tuple.

    Args:
        step: Step object.

    Returns:
        Tuple of dependency step names.
    """
    depends = getattr(step, "depends_on", ())
    if callable(depends) and not isinstance(depends, tuple):
        # Handle property that returns tuple
        depends = depends
    return tuple(depends) if depends else ()


# ============================================================================
# Callable Adapter
# ============================================================================


class _AdaptedCallable:
    """Wrapper that adapts a bare callable to OrchestratorStep protocol."""

    __slots__ = ("_fn", "_name", "_depends_on", "_description")

    def __init__(
        self,
        fn: Callable[[int, "YearState"], "YearState"],
        name: str | None = None,
        depends_on: tuple[str, ...] = (),
        description: str | None = None,
    ) -> None:
        self._fn = fn
        self._name: str = name if name else str(getattr(fn, "__name__", str(fn)))
        self._depends_on = depends_on
        self._description = description

    @property
    def name(self) -> str:
        return self._name

    @property
    def depends_on(self) -> tuple[str, ...]:
        return self._depends_on

    @property
    def description(self) -> str | None:
        return self._description

    def execute(self, year: int, state: "YearState") -> "YearState":
        return self._fn(year, state)

    def __call__(self, year: int, state: "YearState") -> "YearState":
        return self._fn(year, state)


def adapt_callable(
    fn: Callable[[int, "YearState"], "YearState"],
    name: str | None = None,
    depends_on: tuple[str, ...] = (),
    description: str | None = None,
) -> OrchestratorStep:
    """Adapt a bare callable to OrchestratorStep protocol.

    Args:
        fn: Callable with signature (year: int, state: YearState) -> YearState.
        name: Step name (defaults to fn.__name__).
        depends_on: Step dependencies (defaults to empty).
        description: Optional description.

    Returns:
        Object satisfying OrchestratorStep protocol.
    """
    return _AdaptedCallable(
        fn, name=name, depends_on=depends_on, description=description
    )


# ============================================================================
# @step Decorator
# ============================================================================


def step(
    name: str | None = None,
    depends_on: tuple[str, ...] = (),
    description: str | None = None,
) -> Callable[[Callable[[int, "YearState"], "YearState"]], OrchestratorStep]:
    """Decorator to create an OrchestratorStep from a function.

    Args:
        name: Step name (defaults to function.__name__).
        depends_on: Step dependencies (defaults to empty tuple).
        description: Optional step description.

    Returns:
        Decorator that wraps function as OrchestratorStep.

    Example:
        @step(name="my_step", depends_on=("carry_forward",))
        def my_step_function(year: int, state: YearState) -> YearState:
            return state
    """

    def decorator(fn: Callable[[int, "YearState"], "YearState"]) -> OrchestratorStep:
        return adapt_callable(
            fn,
            name=name or fn.__name__,
            depends_on=depends_on,
            description=description,
        )

    return decorator


# ============================================================================
# StepRegistry
# ============================================================================


class StepRegistry:
    """Registry for orchestrator steps with dependency-based ordering.

    Manages step registration and builds topologically sorted pipelines
    based on declared dependencies.

    Example:
        registry = StepRegistry()
        registry.register(CarryForwardStep())
        registry.register(VintageTransitionStep())
        pipeline = registry.build_pipeline()  # Topologically sorted
    """

    def __init__(self) -> None:
        self._steps: dict[str, OrchestratorStep] = {}
        self._registration_order: list[str] = []

    def register(self, step: OrchestratorStep) -> None:
        """Register a step in the registry.

        Args:
            step: Step to register (must satisfy OrchestratorStep protocol).

        Raises:
            StepValidationError: If step doesn't satisfy OrchestratorStep protocol.
            StepRegistrationError: If step name is already registered.
        """
        # Validate protocol conformance
        if not is_protocol_step(step):
            step_type = type(step).__name__
            raise StepValidationError(
                f"Step '{step_type}' does not satisfy OrchestratorStep protocol: "
                f"must have 'name' attribute and 'execute' method"
            )

        name = step.name

        # Check for duplicate name
        if name in self._steps:
            raise StepRegistrationError(
                f"Duplicate step name: '{name}' is already registered"
            )

        self._steps[name] = step
        self._registration_order.append(name)

    def get(self, name: str) -> OrchestratorStep | None:
        """Get a registered step by name.

        Args:
            name: Step name to look up.

        Returns:
            The registered step, or None if not found.
        """
        return self._steps.get(name)

    def __len__(self) -> int:
        """Return number of registered steps."""
        return len(self._steps)

    def __iter__(self) -> "Iterator[OrchestratorStep]":
        """Iterate over registered steps in registration order."""
        for name in self._registration_order:
            yield self._steps[name]

    def build_pipeline(self) -> tuple[OrchestratorStep, ...]:
        """Build a topologically sorted pipeline from registered steps.

        Uses Kahn's algorithm for topological sort, with registration order
        as tie-breaker for steps at the same dependency level.

        Returns:
            Tuple of steps in dependency order.

        Raises:
            StepRegistrationError: If any step depends on unknown step.
            CircularDependencyError: If circular dependencies exist.
        """
        if not self._steps:
            return ()

        # Build adjacency list and in-degree count
        # adjacency[a] = [b, c] means b and c depend on a
        adjacency: dict[str, list[str]] = {name: [] for name in self._steps}
        in_degree: dict[str, int] = {name: 0 for name in self._steps}

        for name, step in self._steps.items():
            deps = _get_depends_on(step)
            for dep in deps:
                if dep not in self._steps:
                    raise StepRegistrationError(
                        f"Step '{name}' depends on unknown step '{dep}'"
                    )
                adjacency[dep].append(name)
                in_degree[name] += 1

        # Initialize queue with steps that have no dependencies
        # Use registration order for deterministic tie-breaking
        queue: deque[str] = deque()
        for name in self._registration_order:
            if in_degree[name] == 0:
                queue.append(name)

        result: list[OrchestratorStep] = []

        while queue:
            current = queue.popleft()
            result.append(self._steps[current])

            # Process dependents in registration order
            dependents = adjacency[current]
            dependents_in_order = [
                n for n in self._registration_order if n in dependents
            ]

            for dependent in dependents_in_order:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # Check for cycle
        if len(result) != len(self._steps):
            # Find steps involved in cycle
            remaining = [name for name in self._steps if in_degree[name] > 0]
            raise CircularDependencyError(
                f"Circular dependency detected involving steps: {remaining}"
            )

        return tuple(result)
