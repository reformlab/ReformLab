"""MergeMethod protocol and supporting types for statistical dataset fusion.

Defines the structural interface that all merge methods must satisfy,
plus immutable value objects for configuration, assumption records,
and merge results.

Implements Story 11.4 (MergeMethod protocol and uniform distribution).
References FR38 (statistical methods library).
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    import pyarrow as pa


# ====================================================================
# Configuration
# ====================================================================


@dataclass(frozen=True)
class MergeConfig:
    """Immutable configuration for a merge operation.

    Attributes:
        seed: Random seed for deterministic merge operations. Must be >= 0.
        description: Optional human-readable description for governance.
        drop_right_columns: Column names to remove from table_b before
            merging. Use this to remove shared key columns (e.g.,
            ``"region_code"``) that exist in both tables but should only
            appear once in the result.
    """

    seed: int
    description: str = ""
    drop_right_columns: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            msg = f"seed must be a non-negative integer, got {self.seed!r}"
            raise ValueError(msg)
        if self.seed < 0:
            msg = f"seed must be a non-negative integer, got {self.seed!r}"
            raise ValueError(msg)
        # Deep-copy mutable-origin field to prevent aliasing
        object.__setattr__(
            self, "drop_right_columns", tuple(self.drop_right_columns)
        )


# ====================================================================
# Assumption record
# ====================================================================


@dataclass(frozen=True)
class MergeAssumption:
    """Structured assumption record from a merge operation.

    Records the method name, a plain-language assumption statement,
    and method-specific details. Can be converted to governance
    ``AssumptionEntry`` format via ``to_governance_entry()``.

    Attributes:
        method_name: Short identifier for the method (e.g., ``"uniform"``).
        statement: Plain-language description of the assumption made.
        details: Method-specific metadata. Values must be JSON-compatible
            (``str``, ``int``, ``float``, ``bool``, ``None``, ``list``,
            ``dict``). Never put ``pa.Table``, ``pa.Schema``, ``Path``,
            or custom objects in details.
    """

    method_name: str
    statement: str
    details: dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "details", deepcopy(self.details))

    def to_governance_entry(
        self, *, source_label: str = "merge_step"
    ) -> dict[str, Any]:
        """Convert to governance-compatible assumption entry.

        Returns a dict matching ``governance.manifest.AssumptionEntry``
        structure: ``key``, ``value``, ``source``, ``is_default``.

        The ``value`` field unpacks ``details`` first, then overrides
        with ``method`` and ``statement`` keys to prevent collision.
        """
        return {
            "key": f"merge_{self.method_name}",
            "value": {
                **self.details,
                "method": self.method_name,
                "statement": self.statement,
            },
            "source": source_label,
            "is_default": False,
        }


# ====================================================================
# Merge result
# ====================================================================


@dataclass(frozen=True)
class MergeResult:
    """Immutable result of a merge operation.

    Attributes:
        table: The merged PyArrow table.
        assumption: Structured assumption record documenting the merge.
    """

    table: pa.Table
    assumption: MergeAssumption


# ====================================================================
# MergeMethod protocol
# ====================================================================


@runtime_checkable
class MergeMethod(Protocol):
    """Interface for statistical dataset fusion methods.

    Structural (duck-typed) protocol: any class that implements
    ``merge()`` and the ``name`` property with the correct signatures
    satisfies the contract — no explicit inheritance required.

    Each method merges two ``pa.Table`` objects using a specific
    statistical approach, returning the merged table and an assumption
    record documenting the methodological choice.
    """

    @property
    def name(self) -> str:
        """Short identifier for this method (e.g., ``"uniform"``, ``"ipf"``)."""
        ...

    def merge(
        self,
        table_a: pa.Table,
        table_b: pa.Table,
        config: MergeConfig,
    ) -> MergeResult:
        """Merge two tables using this method's statistical approach."""
        ...
