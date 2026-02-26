from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pyarrow as pa

OutputFields = pa.Table


@dataclass(frozen=True)
class PopulationData:
    """Wraps a population dataset with metadata.

    The underlying data is a PyArrow Table keyed by entity type
    (e.g. ``"individu"``, ``"menage"``).  A single-entity dataset
    can use the default ``"default"`` key.
    """

    tables: dict[str, pa.Table]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def row_count(self) -> int:
        """Total rows across all entity tables."""
        return sum(t.num_rows for t in self.tables.values())


@dataclass(frozen=True)
class PolicyConfig:
    """Scenario parameters for a single computation period."""

    parameters: dict[str, Any]
    name: str = ""
    description: str = ""


@dataclass(frozen=True)
class ComputationResult:
    """Result returned by a ComputationAdapter.compute() call.

    Attributes:
        output_fields: Mapped output data as a PyArrow Table.
        adapter_version: Version string of the adapter that produced the result.
        period: The computation period (e.g. year).
        metadata: Timing, row count, and other run-level information.
    """

    output_fields: OutputFields
    adapter_version: str
    period: int
    metadata: dict[str, Any] = field(default_factory=dict)
