# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
from __future__ import annotations

from typing import Protocol, runtime_checkable

from reformlab.computation.types import ComputationResult, PolicyConfig, PopulationData


@runtime_checkable
class ComputationAdapter(Protocol):
    """Interface for tax-benefit computation backends.

    The orchestrator never calls OpenFisca (or any other engine) directly.
    All computation goes through this protocol, enabling:

    - Backend swapping (OpenFisca → PolicyEngine → custom)
    - Mocking for orchestrator unit tests
    - Version-pinning without core coupling

    This is a structural (duck-typed) protocol: any class that implements
    ``compute()`` and ``version()`` with the correct signatures satisfies
    the contract — no explicit inheritance required.
    """

    def compute(
        self,
        population: PopulationData,
        policy: PolicyConfig,
        period: int,
    ) -> ComputationResult:
        """Run a computation for the given population, policy, and period.

        Args:
            population: Input population data.
            policy: Scenario parameters.
            period: Computation period (e.g. year).

        Returns:
            A ``ComputationResult`` containing mapped output fields.
        """
        ...

    def version(self) -> str:
        """Return the version string of the underlying computation backend."""
        ...
