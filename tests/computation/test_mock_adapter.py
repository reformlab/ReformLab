"""Test 5.5: MockAdapter contract test."""

from __future__ import annotations

import pyarrow as pa

from reformlab.computation.adapter import ComputationAdapter
from reformlab.computation.mock_adapter import MockAdapter
from reformlab.computation.types import PolicyConfig, PopulationData


class TestMockAdapter:
    """AC-2: Given a mock adapter implementing ComputationAdapter, when the
    orchestrator calls compute(), then it receives valid ComputationResult
    objects without requiring OpenFisca installed."""

    def test_mock_satisfies_protocol(self) -> None:
        """Given MockAdapter, then it satisfies ComputationAdapter protocol."""
        adapter = MockAdapter()
        assert isinstance(adapter, ComputationAdapter)

    def test_mock_returns_default_result(
        self,
        sample_population: PopulationData,
        sample_policy: PolicyConfig,
    ) -> None:
        """Given a default MockAdapter, when compute() is called,
        then it returns a valid ComputationResult with default output."""
        adapter = MockAdapter()
        result = adapter.compute(sample_population, sample_policy, period=2025)

        assert result.period == 2025
        assert result.adapter_version == "mock-1.0.0"
        assert result.output_fields.num_rows == 1
        assert result.metadata["source"] == "mock"

    def test_mock_returns_custom_output(
        self,
        sample_population: PopulationData,
        sample_policy: PolicyConfig,
    ) -> None:
        """Given a MockAdapter with custom output, when compute() is called,
        then it returns the configured output table."""
        custom = pa.table({"tax": pa.array([100.0, 200.0])})
        adapter = MockAdapter(default_output=custom, version_string="test-2.0")

        result = adapter.compute(sample_population, sample_policy, period=2026)

        assert result.output_fields.equals(custom)
        assert result.adapter_version == "test-2.0"

    def test_mock_records_call_log(
        self,
        sample_population: PopulationData,
        sample_policy: PolicyConfig,
    ) -> None:
        """Given a MockAdapter, when compute() is called multiple times,
        then call_log records each invocation."""
        adapter = MockAdapter()
        adapter.compute(sample_population, sample_policy, period=2025)
        adapter.compute(sample_population, sample_policy, period=2026)

        assert len(adapter.call_log) == 2
        assert adapter.call_log[0]["period"] == 2025
        assert adapter.call_log[1]["period"] == 2026
        assert adapter.call_log[0]["policy_name"] == "carbon-tax-baseline"

    def test_mock_version(self) -> None:
        """Given a MockAdapter with custom version, then version() returns it."""
        adapter = MockAdapter(version_string="custom-3.0")
        assert adapter.version() == "custom-3.0"
