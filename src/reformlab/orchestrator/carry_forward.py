"""Carry-forward step for deterministic state updates between years.

This module provides:
- CarryForwardRule: Configuration for a single state variable update
- CarryForwardConfig: Configuration for the carry-forward step
- CarryForwardStep: OrchestratorStep implementation for state carry-forward
- CarryForwardConfigError: Error for invalid configuration
- CarryForwardExecutionError: Error during step execution
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Callable, Literal

if TYPE_CHECKING:
    from reformlab.orchestrator.types import YearState


# ============================================================================
# Error Classes
# ============================================================================


class CarryForwardConfigError(Exception):
    """Invalid carry-forward configuration.

    Raised when carry-forward rules are misconfigured, such as
    missing period semantics (NFR10 violation) or invalid rule types.
    """


class CarryForwardExecutionError(Exception):
    """Error during carry-forward step execution.

    Raised when a rule fails to execute, such as missing values
    for scale/increment rules or exceptions in custom callables.
    """


# ============================================================================
# CarryForwardRule
# ============================================================================


RuleType = Literal["static", "scale", "increment", "custom"]


@dataclass(frozen=True)
class CarryForwardRule:
    """Configuration for updating a single state variable.

    Each rule specifies how a state variable should be updated
    during the carry-forward step between years.

    Attributes:
        variable: Name of the state variable to update.
        rule_type: Type of update rule:
            - "static": Preserve value unchanged
            - "scale": Multiply by factor (requires value)
            - "increment": Add value (requires value)
            - "custom": Apply custom callable (requires custom_fn)
        period_semantics: Explicit description of period behavior (NFR10).
            Example: "annual_growth_rate", "from_year_t_to_t+1"
        value: Factor/increment for scale/increment rules.
        custom_fn: Callable for custom rules with signature:
            (year: int, current_value: Any, state: YearState) -> Any
    """

    variable: str
    rule_type: RuleType
    period_semantics: str
    value: float | None = None
    custom_fn: Callable[[int, Any, "YearState"], Any] | None = None

    def __post_init__(self) -> None:
        """Validate rule configuration."""
        if not self.period_semantics or not self.period_semantics.strip():
            raise CarryForwardConfigError(
                f"Rule for '{self.variable}' missing period_semantics (NFR10): "
                "all rules must explicitly specify period behavior"
            )


# ============================================================================
# CarryForwardConfig
# ============================================================================


@dataclass(frozen=True)
class CarryForwardConfig:
    """Configuration for the carry-forward step.

    Groups multiple rules for state variable updates and provides
    validation options.

    Attributes:
        rules: Tuple of CarryForwardRule instances to apply.
        strict_period: If True (default), enforce period semantics validation.
    """

    rules: tuple[CarryForwardRule, ...]
    strict_period: bool = True


# ============================================================================
# CarryForwardStep
# ============================================================================


class CarryForwardStep:
    """Orchestrator step for deterministic state carry-forward.

    Implements the OrchestratorStep protocol to update state variables
    between years according to configured rules.

    The step guarantees:
    - Deterministic execution (same inputs produce identical outputs)
    - Rules applied in sorted order by variable name
    - Immutable state updates (returns new YearState)
    - Explicit period semantics on all rules (NFR10 compliance)
    """

    __slots__ = ("_config", "_name", "_depends_on", "_description")

    def __init__(
        self,
        config: CarryForwardConfig,
        name: str = "carry_forward",
        depends_on: tuple[str, ...] = (),
        description: str | None = None,
    ) -> None:
        """Initialize the carry-forward step.

        Args:
            config: CarryForwardConfig with rules to apply.
            name: Step name for registry (default: "carry_forward").
            depends_on: Names of steps this step depends on.
            description: Optional description for the step.
        """
        self._config = config
        self._name = name
        self._depends_on = depends_on
        self._description = (
            description
            or "Carry-forward step for deterministic state variable updates"
        )

    @property
    def name(self) -> str:
        """Unique identifier for this step."""
        return self._name

    @property
    def depends_on(self) -> tuple[str, ...]:
        """Names of steps this step depends on."""
        return self._depends_on

    @property
    def description(self) -> str:
        """Human-readable description of the step."""
        return self._description

    def execute(self, year: int, state: "YearState") -> "YearState":
        """Execute carry-forward for a given year.

        Applies all configured rules to update state variables,
        returning a new YearState with updated data.

        Args:
            year: Current simulation year.
            state: Current year state.

        Returns:
            New YearState with updated data dictionary.

        Raises:
            CarryForwardExecutionError: If any rule fails to execute.
        """
        # Short-circuit for empty rules
        if not self._config.rules:
            return state

        # Create mutable copy of data
        new_data = dict(state.data)

        # Apply rules in sorted order for determinism
        sorted_rules = sorted(self._config.rules, key=lambda r: r.variable)
        for rule in sorted_rules:
            new_data[rule.variable] = self._apply_rule(rule, year, state)

        # Return new immutable state
        return replace(state, data=new_data)

    def _apply_rule(
        self,
        rule: CarryForwardRule,
        year: int,
        state: "YearState",
    ) -> Any:
        """Apply a single rule to compute new variable value.

        Args:
            rule: The rule to apply.
            year: Current simulation year.
            state: Current year state.

        Returns:
            Updated value for the state variable.

        Raises:
            CarryForwardExecutionError: If rule execution fails.
        """
        current_value = state.data.get(rule.variable)

        if rule.rule_type == "static":
            return current_value

        elif rule.rule_type == "scale":
            if current_value is None:
                raise CarryForwardExecutionError(
                    f"Cannot apply scale rule for '{rule.variable}': "
                    f"variable not found in state data"
                )
            if rule.value is None:
                raise CarryForwardExecutionError(
                    f"Cannot apply scale rule for '{rule.variable}': "
                    f"scale factor (value) is None"
                )
            return current_value * rule.value

        elif rule.rule_type == "increment":
            if current_value is None:
                raise CarryForwardExecutionError(
                    f"Cannot apply increment rule for '{rule.variable}': "
                    f"variable not found in state data"
                )
            if rule.value is None:
                raise CarryForwardExecutionError(
                    f"Cannot apply increment rule for '{rule.variable}': "
                    f"increment value is None"
                )
            return current_value + rule.value

        elif rule.rule_type == "custom":
            if rule.custom_fn is None:
                raise CarryForwardExecutionError(
                    f"Cannot apply custom rule for '{rule.variable}': "
                    f"custom_fn is None"
                )
            try:
                return rule.custom_fn(year, current_value, state)
            except Exception as e:
                raise CarryForwardExecutionError(
                    f"Custom rule for '{rule.variable}' failed: {e}"
                ) from e

        else:
            # This shouldn't happen with Literal type, but handle it
            raise CarryForwardExecutionError(
                f"Unknown rule type '{rule.rule_type}' for variable '{rule.variable}'"
            )
