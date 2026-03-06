"""DecisionDomain protocol for discrete choice decision domains.

Defines the contract for decision domains (vehicle, heating, etc.) that
provide choice sets, attribute overrides, and cost column identifiers.
Stories 14.3/14.4 implement this protocol for specific domains.

Story 14-1: DiscreteChoiceStep with population expansion pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    import pyarrow as pa

    from reformlab.discrete_choice.types import Alternative


@runtime_checkable
class DecisionDomain(Protocol):
    """Protocol for discrete choice decision domains.

    A decision domain defines:
    - Available alternatives (e.g., vehicle types, heating systems)
    - How to modify population attributes for each alternative
    - Which cost column to extract from computation results

    Implementations must be stateless — all domain-specific logic
    is encoded in the alternatives and apply_alternative method.
    """

    @property
    def name(self) -> str:
        """Domain identifier (e.g., 'vehicle', 'heating')."""
        ...

    @property
    def alternatives(self) -> tuple["Alternative", ...]:
        """Available alternatives in this domain."""
        ...

    @property
    def cost_column(self) -> str:
        """Column name in ComputationResult.output_fields containing the cost metric."""
        ...

    def apply_alternative(
        self, table: "pa.Table", alternative: "Alternative"
    ) -> "pa.Table":
        """Modify population table attributes for a given alternative.

        Args:
            table: Entity table from PopulationData.
            alternative: The alternative whose attribute overrides to apply.

        Returns:
            Modified table with alternative-specific attribute values.
        """
        ...
