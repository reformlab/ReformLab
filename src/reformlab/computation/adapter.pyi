from __future__ import annotations

from typing import Protocol, runtime_checkable

from reformlab.computation.types import ComputationResult, PolicyConfig, PopulationData

@runtime_checkable
class ComputationAdapter(Protocol):
    def compute(
        self,
        population: PopulationData,
        policy: PolicyConfig,
        period: int,
    ) -> ComputationResult: ...
    def version(self) -> str: ...
