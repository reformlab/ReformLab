# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Test 5.1: Protocol compliance tests (structural typing verification)."""

from __future__ import annotations

from pathlib import Path

from reformlab.computation.adapter import ComputationAdapter
from reformlab.computation.mock_adapter import MockAdapter
from reformlab.computation.openfisca_adapter import OpenFiscaAdapter


class TestProtocolCompliance:
    """Verify that adapters satisfy ComputationAdapter via structural typing."""

    def test_mock_adapter_is_computation_adapter(self) -> None:
        """Given MockAdapter, when checked against ComputationAdapter,
        then it is recognised as an instance (structural typing)."""
        adapter = MockAdapter()
        assert isinstance(adapter, ComputationAdapter)

    def test_openfisca_adapter_is_computation_adapter(self, tmp_path: Path) -> None:
        """Given OpenFiscaAdapter, when checked against ComputationAdapter,
        then it is recognised as an instance (structural typing)."""
        adapter = OpenFiscaAdapter(data_dir=tmp_path, skip_version_check=True)
        assert isinstance(adapter, ComputationAdapter)

    def test_arbitrary_class_satisfies_protocol(self) -> None:
        """Given an arbitrary class with compute() and version(),
        when checked against ComputationAdapter, then mypy and
        runtime_checkable both accept it."""
        import pyarrow as pa

        from reformlab.computation.types import (
            ComputationResult,
            PolicyConfig,
            PopulationData,
        )

        class CustomAdapter:
            def compute(
                self,
                population: PopulationData,
                policy: PolicyConfig,
                period: int,
            ) -> ComputationResult:
                return ComputationResult(
                    output_fields=pa.table({"x": pa.array([1])}),
                    adapter_version="custom-1",
                    period=period,
                )

            def version(self) -> str:
                return "custom-1"

        assert isinstance(CustomAdapter(), ComputationAdapter)

    def test_non_conforming_class_is_not_adapter(self) -> None:
        """Given a class missing required methods, when checked against
        ComputationAdapter, then isinstance returns False."""

        class NotAnAdapter:
            pass

        assert not isinstance(NotAnAdapter(), ComputationAdapter)
