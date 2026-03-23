# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any

import pyarrow as pa

if TYPE_CHECKING:
    from reformlab.templates.schema import PolicyParameters

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

    @classmethod
    def from_table(
        cls, table: pa.Table, entity_type: str = "default"
    ) -> PopulationData:
        """Wrap a flat PyArrow table as a single-entity PopulationData.

        Args:
            table: The PyArrow table to wrap.
            entity_type: Entity key for the table (default: ``"default"``).
        """
        return cls(tables={entity_type: table}, metadata={})

    @property
    def primary_table(self) -> pa.Table:
        """Return the first (or only) entity table regardless of key name."""
        if not self.tables:
            msg = "PopulationData has no tables"
            raise ValueError(msg)
        return next(iter(self.tables.values()))

    @property
    def row_count(self) -> int:
        """Total rows across all entity tables."""
        return sum(t.num_rows for t in self.tables.values())


@dataclass(frozen=True)
class PolicyConfig:
    """Scenario parameters for a single computation period.

    The ``policy`` field carries a typed ``PolicyParameters`` object
    at runtime. Adapters and orchestrator steps receive the full typed
    policy; serialization to dict happens only at governance/manifest
    boundaries via ``serialize_policy()``.
    """

    policy: PolicyParameters
    name: str = ""
    description: str = ""


def serialize_policy(policy: PolicyParameters) -> dict[str, Any]:
    """Convert a PolicyParameters object to a JSON-compatible dict.

    Numeric dict keys (e.g. year-indexed rate_schedule) are converted
    to strings for JSON serialization. Internal tracking fields
    (prefixed with ``_``) are stripped.

    This is the single shared serializer used at manifest, workflow,
    and server boundaries.
    """

    def _normalize(value: Any) -> Any:
        if isinstance(value, dict):
            return {str(k): _normalize(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [_normalize(item) for item in value]
        return value

    raw = asdict(policy)
    # Strip internal tracking fields (e.g. _pivot_point_set)
    return {
        str(k): _normalize(v)
        for k, v in raw.items()
        if not k.startswith("_")
    }


def deserialize_policy(
    data: dict[str, Any],
    policy_type: str | None = None,
) -> PolicyParameters:
    """Reconstruct a PolicyParameters object from a dict.

    Uses ``policy_type`` string to select the appropriate subclass.
    If ``policy_type`` is None, constructs a base ``PolicyParameters``.
    String-keyed rate schedules are converted back to int keys.

    Args:
        data: Policy parameters dictionary (e.g. from manifest or config).
        policy_type: Optional policy type string (e.g. "carbon_tax").

    Returns:
        Typed PolicyParameters instance.
    """
    from reformlab.templates.schema import (
        CarbonTaxParameters,
        FeebateParameters,
        RebateParameters,
        SubsidyParameters,
    )
    from reformlab.templates.schema import (
        PolicyParameters as PP,
    )

    # Normalize rate_schedule keys from strings back to ints
    rate_schedule_raw = data.get("rate_schedule", {})
    rate_schedule = {int(k): float(v) for k, v in rate_schedule_raw.items()}

    # Common fields
    common = {
        "rate_schedule": rate_schedule,
        "exemptions": tuple(data.get("exemptions", ())),
        "thresholds": tuple(data.get("thresholds", ())),
        "covered_categories": tuple(data.get("covered_categories", ())),
    }

    if policy_type == "carbon_tax":
        redistribution = data.get("redistribution", {})
        if isinstance(redistribution, dict):
            rtype = redistribution.get("type", data.get("redistribution_type", ""))
            iweights = redistribution.get("income_weights", data.get("income_weights", {}))
        else:
            rtype = data.get("redistribution_type", "")
            iweights = data.get("income_weights", {})
        return CarbonTaxParameters(
            **common,
            redistribution_type=rtype,
            income_weights={k: float(v) for k, v in iweights.items()} if isinstance(iweights, dict) else {},
        )
    if policy_type == "subsidy":
        return SubsidyParameters(
            **common,
            eligible_categories=tuple(data.get("eligible_categories", ())),
            income_caps={int(k): float(v) for k, v in data.get("income_caps", {}).items()},
        )
    if policy_type == "rebate":
        return RebateParameters(
            **common,
            rebate_type=data.get("rebate_type", ""),
            income_weights={k: float(v) for k, v in data.get("income_weights", {}).items()},
        )
    if policy_type == "feebate":
        return FeebateParameters(
            **common,
            pivot_point=float(data.get("pivot_point", 0.0)),
            fee_rate=float(data.get("fee_rate", 0.0)),
            rebate_rate=float(data.get("rebate_rate", 0.0)),
        )

    # Default: base PolicyParameters
    return PP(**common)


@dataclass(frozen=True)
class ComputationResult:
    """Result returned by a ComputationAdapter.compute() call.

    Attributes:
        output_fields: Mapped output data as a PyArrow Table. When all output
            variables belong to a single entity, this is that entity's table.
            When variables span multiple entities, this contains the person-entity
            table (primary entity).
        adapter_version: Version string of the adapter that produced the result.
        period: The computation period (e.g. year).
        metadata: Timing, row count, and other run-level information.
        entity_tables: Per-entity output tables keyed by entity plural name
            (e.g. ``"individus"``, ``"foyers_fiscaux"``). Empty dict when all
            outputs belong to a single entity (backward-compatible default).
            Story 9.2: Handle multi-entity output arrays.
    """

    output_fields: OutputFields
    adapter_version: str
    period: int
    metadata: dict[str, Any] = field(default_factory=dict)
    entity_tables: dict[str, pa.Table] = field(default_factory=dict)
