"""Test 5.6: ComputationResult field completeness test."""

from __future__ import annotations

import pyarrow as pa

from reformlab.computation.types import (
    ComputationResult,
    PolicyConfig,
    PopulationData,
)


class TestComputationResult:
    """AC-5: Given a successful compute() call, then the returned
    ComputationResult contains: mapped output fields, adapter version,
    computation period, and metadata."""

    def test_result_has_output_fields(self) -> None:
        result = ComputationResult(
            output_fields=pa.table({"x": pa.array([1, 2])}),
            adapter_version="v1",
            period=2025,
        )
        assert result.output_fields.num_rows == 2
        assert "x" in result.output_fields.column_names

    def test_result_has_adapter_version(self) -> None:
        result = ComputationResult(
            output_fields=pa.table({"x": pa.array([1])}),
            adapter_version="44.2.2",
            period=2025,
        )
        assert result.adapter_version == "44.2.2"

    def test_result_has_period(self) -> None:
        result = ComputationResult(
            output_fields=pa.table({"x": pa.array([1])}),
            adapter_version="v1",
            period=2026,
        )
        assert result.period == 2026

    def test_result_has_metadata(self) -> None:
        result = ComputationResult(
            output_fields=pa.table({"x": pa.array([1])}),
            adapter_version="v1",
            period=2025,
            metadata={"timing_seconds": 0.01, "row_count": 1},
        )
        assert result.metadata["timing_seconds"] == 0.01
        assert result.metadata["row_count"] == 1

    def test_result_default_metadata_is_empty_dict(self) -> None:
        result = ComputationResult(
            output_fields=pa.table({"x": pa.array([1])}),
            adapter_version="v1",
            period=2025,
        )
        assert result.metadata == {}

    def test_result_is_immutable(self) -> None:
        """ComputationResult is frozen — attributes cannot be reassigned."""
        import pytest

        result = ComputationResult(
            output_fields=pa.table({"x": pa.array([1])}),
            adapter_version="v1",
            period=2025,
        )
        with pytest.raises(AttributeError):
            result.period = 2099  # type: ignore[misc]


class TestPopulationData:
    def test_row_count_single_table(self) -> None:
        pop = PopulationData(tables={"individu": pa.table({"id": pa.array([1, 2, 3])})})
        assert pop.row_count == 3

    def test_row_count_multiple_tables(self) -> None:
        pop = PopulationData(
            tables={
                "individu": pa.table({"id": pa.array([1, 2])}),
                "menage": pa.table({"id": pa.array([10])}),
            }
        )
        assert pop.row_count == 3

    def test_metadata_default_empty(self) -> None:
        pop = PopulationData(tables={"default": pa.table({"x": pa.array([1])})})
        assert pop.metadata == {}


class TestPolicyConfig:
    def test_policy_has_parameters(self) -> None:
        pol = PolicyConfig(parameters={"rate": 0.1}, name="test")
        assert pol.parameters["rate"] == 0.1
        assert pol.name == "test"

    def test_policy_default_fields(self) -> None:
        pol = PolicyConfig(parameters={})
        assert pol.name == ""
        assert pol.description == ""
