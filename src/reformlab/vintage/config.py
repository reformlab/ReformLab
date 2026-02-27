"""Vintage transition configuration.

This module provides:
- VintageTransitionRule: Configuration for transition behavior (entry, retirement)
- VintageConfig: Configuration for the vintage transition step

MVP scope: vehicle asset class with fixed entry count and max-age retirement.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from reformlab.vintage.errors import VintageConfigError
from reformlab.vintage.types import VintageState

# Supported rule types for MVP
RuleType = Literal["fixed_entry", "proportional_entry", "max_age_retirement"]
_SUPPORTED_RULE_TYPES: tuple[str, ...] = (
    "fixed_entry",
    "proportional_entry",
    "max_age_retirement",
)

# MVP-supported asset classes
_SUPPORTED_ASSET_CLASSES: tuple[str, ...] = ("vehicle",)


@dataclass(frozen=True)
class VintageTransitionRule:
    """Configuration for a single vintage transition rule.

    Rules define how cohorts enter, age, or exit the vintage state.
    Multiple rules can be combined in VintageConfig.

    Attributes:
        rule_type: Type of transition rule:
            - "fixed_entry": Add fixed count of new cohorts each year
            - "proportional_entry": Add cohorts proportional to existing count
            - "max_age_retirement": Remove cohorts above max age
        parameters: Rule-specific parameters:
            - fixed_entry: {"count": int}
            - proportional_entry: {"rate": float}
            - max_age_retirement: {"max_age": int}
        description: Human-readable description of the rule.
    """

    rule_type: RuleType
    parameters: dict[str, Any]
    description: str = ""

    def __post_init__(self) -> None:
        """Validate rule configuration."""
        if self.rule_type not in _SUPPORTED_RULE_TYPES:
            supported = ", ".join(_SUPPORTED_RULE_TYPES)
            raise VintageConfigError(
                f"Invalid rule_type '{self.rule_type}'. Supported: {supported}"
            )

        self._validate_parameters()

    def _validate_parameters(self) -> None:
        """Validate rule-specific parameters."""
        if self.rule_type == "fixed_entry":
            if "count" not in self.parameters:
                raise VintageConfigError(
                    "fixed_entry rule requires 'count' parameter"
                )
            count = self.parameters["count"]
            if (
                not isinstance(count, int)
                or isinstance(count, bool)
                or count < 0
            ):
                raise VintageConfigError(
                    f"fixed_entry 'count' must be non-negative integer, got {count}"
                )

        elif self.rule_type == "proportional_entry":
            if "rate" not in self.parameters:
                raise VintageConfigError(
                    "proportional_entry rule requires 'rate' parameter"
                )
            rate = self.parameters["rate"]
            if (
                not isinstance(rate, (int, float))
                or isinstance(rate, bool)
                or rate < 0
            ):
                raise VintageConfigError(
                    f"proportional_entry 'rate' must be non-negative number, got {rate}"
                )

        elif self.rule_type == "max_age_retirement":
            if "max_age" not in self.parameters:
                raise VintageConfigError(
                    "max_age_retirement rule requires 'max_age' parameter"
                )
            max_age = self.parameters["max_age"]
            if (
                not isinstance(max_age, int)
                or isinstance(max_age, bool)
                or max_age < 0
            ):
                raise VintageConfigError(
                    f"max_age_retirement 'max_age' must be non-negative integer, "
                    f"got {max_age}"
                )


@dataclass(frozen=True)
class VintageConfig:
    """Configuration for the vintage transition step.

    Groups asset class, transition rules, and optional initial state.
    Validates configuration invariants at construction time.

    Attributes:
        asset_class: Asset class identifier (MVP: "vehicle" only).
        rules: Tuple of VintageTransitionRule instances.
        initial_state: Optional initial VintageState (used if no state exists).
        description: Human-readable description of the configuration.
    """

    asset_class: str
    rules: tuple[VintageTransitionRule, ...] = ()
    initial_state: VintageState | None = None
    description: str = ""

    def __post_init__(self) -> None:
        """Validate configuration invariants."""
        # Normalize rules to tuple
        object.__setattr__(self, "rules", tuple(self.rules))

        # Validate asset class for MVP
        if self.asset_class not in _SUPPORTED_ASSET_CLASSES:
            supported = ", ".join(_SUPPORTED_ASSET_CLASSES)
            raise VintageConfigError(
                f"Unsupported asset_class '{self.asset_class}' for MVP. "
                f"Supported: {supported}. "
                "Future stories will add additional asset classes."
            )

        # Validate rule coverage
        self._validate_rule_coverage()

        # Validate initial state asset class matches
        if self.initial_state is not None:
            if self.initial_state.asset_class != self.asset_class:
                raise VintageConfigError(
                    f"initial_state asset_class '{self.initial_state.asset_class}' "
                    f"does not match config asset_class '{self.asset_class}'"
                )

    def _validate_rule_coverage(self) -> None:
        """Ensure required rule types are present."""
        rule_types = {r.rule_type for r in self.rules}

        # Must have at least one retirement rule
        has_retirement = "max_age_retirement" in rule_types
        if not has_retirement:
            raise VintageConfigError(
                f"VintageConfig for '{self.asset_class}' requires a retirement rule "
                "(max_age_retirement). Without retirement, cohorts would accumulate "
                "indefinitely."
            )

        # Must have at least one entry rule (fixed or proportional)
        has_entry = "fixed_entry" in rule_types or "proportional_entry" in rule_types
        if not has_entry:
            raise VintageConfigError(
                f"VintageConfig for '{self.asset_class}' requires an entry rule "
                "(fixed_entry or proportional_entry). Without entry, the fleet "
                "would eventually retire to zero."
            )

    @property
    def retirement_rules(self) -> tuple[VintageTransitionRule, ...]:
        """Get all retirement rules."""
        return tuple(r for r in self.rules if r.rule_type == "max_age_retirement")

    @property
    def entry_rules(self) -> tuple[VintageTransitionRule, ...]:
        """Get all entry rules."""
        return tuple(
            r
            for r in self.rules
            if r.rule_type in ("fixed_entry", "proportional_entry")
        )

    @property
    def max_age(self) -> int:
        """Get the configured maximum age (from first retirement rule)."""
        retirement = self.retirement_rules
        if retirement:
            return int(retirement[0].parameters["max_age"])
        return 0
