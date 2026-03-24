from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeAlias

import pyarrow as pa

from reformlab.templates.schema import PolicyParameters

OutputFields: TypeAlias = pa.Table

@dataclass(frozen=True)
class PopulationData:
    tables: dict[str, pa.Table]
    metadata: dict[str, Any] = ...

    @classmethod
    def from_table(cls, table: pa.Table, entity_type: str = ...) -> PopulationData: ...

    @property
    def primary_table(self) -> pa.Table: ...

    @property
    def row_count(self) -> int: ...

@dataclass(frozen=True)
class PolicyConfig:
    policy: PolicyParameters
    name: str = ...
    description: str = ...

def serialize_policy(policy: PolicyParameters) -> dict[str, Any]: ...
def deserialize_policy(
    data: dict[str, Any],
    policy_type: str | None = None,
) -> PolicyParameters: ...

@dataclass(frozen=True)
class ComputationResult:
    output_fields: OutputFields
    adapter_version: str
    period: int
    metadata: dict[str, Any] = ...
    entity_tables: dict[str, pa.Table] = ...
