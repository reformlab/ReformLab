"""Test 5.5: MockAdapter contract test."""

from __future__ import annotations

import pyarrow as pa

from reformlab.computation.adapter import ComputationAdapter
from reformlab.computation.mock_adapter import MockAdapter
from reformlab.computation.types import PolicyConfig, PopulationData
from reformlab.templates.schema import PolicyParameters


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

    def test_compute_fn_used_when_population_has_rows(self) -> None:
        """Given a MockAdapter with compute_fn and population with rows,
        then compute_fn produces the output instead of default_output."""

        def my_compute(
            population: PopulationData, policy: PolicyConfig, period: int
        ) -> pa.Table:
            table = population.primary_table
            return pa.table(
                {"doubled": pa.array([v * 2 for v in table.column("value").to_pylist()])}
            )

        pop = PopulationData(
            tables={"default": pa.table({"value": pa.array([1.0, 2.0, 3.0])})},
            metadata={},
        )
        adapter = MockAdapter(compute_fn=my_compute)
        result = adapter.compute(pop, PolicyConfig(policy=PolicyParameters(rate_schedule={})), period=2025)

        assert result.output_fields.column("doubled").to_pylist() == [2.0, 4.0, 6.0]

    def test_compute_fn_called_even_with_empty_population(self) -> None:
        """Given a MockAdapter with compute_fn and empty population,
        then compute_fn is still called (it decides fallback behavior)."""
        call_count = 0

        def fallback_aware_fn(
            population: PopulationData, policy: PolicyConfig, period: int
        ) -> pa.Table:
            nonlocal call_count
            call_count += 1
            if population.row_count == 0:
                return pa.table({"fallback": pa.array([42.0])})
            return pa.table({"x": pa.array([999.0])})

        adapter = MockAdapter(compute_fn=fallback_aware_fn)

        # Empty tables dict → compute_fn is called and handles fallback itself
        result = adapter.compute(
            PopulationData(tables={}, metadata={}),
            PolicyConfig(policy=PolicyParameters(rate_schedule={})),
            period=2025,
        )
        assert call_count == 1
        assert result.output_fields.column("fallback").to_pylist() == [42.0]

    def test_no_compute_fn_always_returns_default(
        self,
        sample_population: PopulationData,
        sample_policy: PolicyConfig,
    ) -> None:
        """Given a MockAdapter without compute_fn, then default_output is always used."""
        custom = pa.table({"fixed": pa.array([7.0])})
        adapter = MockAdapter(default_output=custom)

        result = adapter.compute(sample_population, sample_policy, period=2025)
        assert result.output_fields.equals(custom)
