from __future__ import annotations

from typing import Any

import pyarrow as pa

from reformlab.computation.types import ComputationResult, PolicyConfig, PopulationData


class MockAdapter:
    """A test adapter that returns configurable fixed results.

    Implements the ``ComputationAdapter`` protocol via structural typing —
    no explicit inheritance required.  Useful for orchestrator unit tests
    that should not depend on OpenFisca being installed.
    """

    def __init__(
        self,
        *,
        version_string: str = "mock-1.0.0",
        default_output: pa.Table | None = None,
        default_metadata: dict[str, Any] | None = None,
    ) -> None:
        self._version = version_string
        self._default_output = default_output or pa.table({"result": pa.array([0.0])})
        self._default_metadata = default_metadata or {}
        self.call_log: list[dict[str, Any]] = []

    def version(self) -> str:
        """Return the configured mock version string."""
        return self._version

    def compute(
        self,
        population: PopulationData,
        policy: PolicyConfig,
        period: int,
    ) -> ComputationResult:
        """Return a fixed ``ComputationResult`` and record the call."""
        self.call_log.append(
            {
                "population_row_count": population.row_count,
                "policy_name": policy.name,
                "period": period,
            }
        )
        return ComputationResult(
            output_fields=self._default_output,
            adapter_version=self._version,
            period=period,
            metadata={**self._default_metadata, "source": "mock"},
        )
