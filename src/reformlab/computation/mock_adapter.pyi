from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pyarrow as pa

from reformlab.computation.types import ComputationResult, PolicyConfig, PopulationData

ComputeFn = Callable[[PopulationData, PolicyConfig, int], pa.Table]

class MockAdapter:
    call_log: list[dict[str, Any]]

    def __init__(
        self,
        *,
        version_string: str = "mock-1.0.0",
        default_output: pa.Table | None = None,
        default_metadata: dict[str, Any] | None = None,
        compute_fn: ComputeFn | None = None,
    ) -> None: ...
    def version(self) -> str: ...
    def compute(
        self,
        population: PopulationData,
        policy: PolicyConfig,
        period: int,
    ) -> ComputationResult: ...
