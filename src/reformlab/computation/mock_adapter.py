# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Mock computation adapter for testing and quickstart demos.

Provides a configurable test double for the ``ComputationAdapter`` protocol,
supporting both fixed-output and population-aware modes. Used by orchestrator
unit tests and the quickstart notebook.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pyarrow as pa

from reformlab.computation.types import ComputationResult, PolicyConfig, PopulationData

ComputeFn = Callable[[PopulationData, PolicyConfig, int], pa.Table]


class MockAdapter:
    """A test adapter that returns configurable fixed or computed results.

    Implements the ``ComputationAdapter`` protocol via structural typing —
    no explicit inheritance required.  Useful for orchestrator unit tests
    that should not depend on OpenFisca being installed.

    Two modes of operation:

    1. **Fixed output** (default): always returns ``default_output`` regardless
       of population input. This is the original behavior used by orchestrator
       and template unit tests.

    2. **Population-aware**: when a ``compute_fn`` is provided, the adapter
       delegates to ``compute_fn`` to produce output from the population data.
       The ``compute_fn`` is responsible for its own fallback behavior (e.g.,
       returning a default table when the population is empty).
    """

    def __init__(
        self,
        *,
        version_string: str = "mock-1.0.0",
        default_output: pa.Table | None = None,
        default_metadata: dict[str, Any] | None = None,
        compute_fn: ComputeFn | None = None,
    ) -> None:
        self._version = version_string
        self._default_output = default_output or pa.table({"result": pa.array([0.0])})
        self._default_metadata = default_metadata or {}
        self._compute_fn = compute_fn
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
        """Return a computed or fixed ``ComputationResult`` and record the call.

        When ``compute_fn`` was provided at construction, delegates to it
        unconditionally. The ``compute_fn`` decides how to handle empty
        populations. Otherwise falls back to the fixed ``default_output``.
        """
        self.call_log.append(
            {
                "population_row_count": population.row_count,
                "policy_name": policy.name,
                "period": period,
            }
        )

        if self._compute_fn is not None:
            output = self._compute_fn(population, policy, period)
        else:
            output = self._default_output

        return ComputationResult(
            output_fields=output,
            adapter_version=self._version,
            period=period,
            metadata={**self._default_metadata, "source": "mock"},
        )
