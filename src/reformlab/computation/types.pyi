from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeAlias

import pyarrow as pa

OutputFields: TypeAlias = pa.Table

@dataclass(frozen=True)
class PopulationData:
    tables: dict[str, pa.Table]
    metadata: dict[str, Any] = ...

    @property
    def row_count(self) -> int: ...

@dataclass(frozen=True)
class PolicyConfig:
    parameters: dict[str, Any]
    name: str = ...
    description: str = ...

@dataclass(frozen=True)
class ComputationResult:
    output_fields: OutputFields
    adapter_version: str
    period: int
    metadata: dict[str, Any] = ...
    entity_tables: dict[str, pa.Table] = ...
