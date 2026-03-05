"""PolicyPortfolio frozen dataclass for composing multiple policies.

Story 12.1: Define PolicyPortfolio dataclass and composition logic
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from reformlab.templates.portfolios.exceptions import PortfolioValidationError
from reformlab.templates.schema import PolicyParameters, PolicyType, infer_policy_type

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class PolicyConfig:
    """Wrapper for policy parameters with metadata for portfolio composition.

    This is a NEW frozen dataclass (not an alias) that wraps PolicyParameters
    with additional metadata needed for portfolio composition.

    Attributes:
        policy_type: The type of policy (CARBON_TAX, SUBSIDY, etc.)
        policy: The actual policy parameters object
        name: Optional human-readable name for this policy within the portfolio
    """

    policy_type: PolicyType
    policy: PolicyParameters
    name: str = ""

    def __post_init__(self) -> None:
        """Validate that policy matches declared policy_type."""
        inferred_type = infer_policy_type(self.policy)
        if inferred_type != self.policy_type:
            raise PortfolioValidationError(
                summary="PolicyConfig type mismatch",
                reason=f"policy_type={self.policy_type.value} does not match "
                f"inferred type {inferred_type.value} from {type(self.policy).__name__}",
                fix="Ensure policy_type matches the policy parameters class, or "
                "omit policy_type to use automatic inference",
                invalid_fields=("policy_type", "policy"),
            )

    def get_summary(self) -> dict[str, Any]:
        """Extract policy type and key parameter summary.

        Returns:
            Dictionary with name, type, and rate_schedule_years.
        """
        return {
            "name": self.name,
            "type": self.policy_type.value,
            "rate_schedule_years": sorted(self.policy.rate_schedule.keys()),
        }


@dataclass(frozen=True)
class PolicyPortfolio:
    """Named, versioned collection of policy configurations.

    A portfolio is a frozen dataclass containing 2+ individual policies
    that will be applied together during simulation runs.

    Attributes:
        name: Portfolio name
        policies: Tuple of PolicyConfig objects (at least 2 required)
        version: Schema version (defaults to "1.0")
        description: Human-readable description
    """

    name: str
    policies: tuple[PolicyConfig, ...]
    version: str = "1.0"
    description: str = ""

    def __post_init__(self) -> None:
        """Validate portfolio has at least 2 policies."""
        if len(self.policies) < 2:
            raise PortfolioValidationError(
                summary="Invalid portfolio",
                reason=f"Portfolio must have at least 2 policies, got {len(self.policies)}",
                fix="Add at least 2 PolicyConfig objects to the portfolio",
                invalid_fields=("policies",),
            )

    @property
    def policy_types(self) -> tuple[PolicyType, ...]:
        """Return tuple of policy types in order."""
        return tuple(p.policy_type for p in self.policies)

    @property
    def policy_count(self) -> int:
        """Return number of policies in portfolio."""
        return len(self.policies)

    @property
    def policy_summaries(self) -> tuple[dict[str, Any], ...]:
        """Return tuple of policy summaries in order."""
        return tuple(p.get_summary() for p in self.policies)

    def list_policies(self) -> list[dict[str, Any]]:
        """Return detailed list of all policies with their configurations.

        Returns:
            List of dicts with name, type, rate_schedule, and other policy details.
        """
        result = []
        for config in self.policies:
            policy_dict: dict[str, Any] = {
                "name": config.name,
                "type": config.policy_type.value,
                "rate_schedule": config.policy.rate_schedule,
            }
            result.append(policy_dict)
        return result

    def get_policy_by_type(self, policy_type: PolicyType) -> PolicyConfig | None:
        """Get first policy matching the given type.

        Args:
            policy_type: The policy type to search for

        Returns:
            First matching PolicyConfig or None if not found.
        """
        for config in self.policies:
            if config.policy_type == policy_type:
                return config
        return None

    def has_policy_type(self, policy_type: PolicyType) -> bool:
        """Check if portfolio contains a policy of the given type.

        Args:
            policy_type: The policy type to check for

        Returns:
            True if at least one policy of that type exists.
        """
        return any(config.policy_type == policy_type for config in self.policies)

    def __repr__(self) -> str:
        """Notebook-friendly representation."""
        return (
            f"PolicyPortfolio(name={self.name!r}, "
            f"version={self.version!r}, "
            f"policies={self.policy_count} policies)"
        )
