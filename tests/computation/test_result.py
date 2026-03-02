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


class TestComputationResultEntityTables:
    """Story 9.2 AC-1, AC-3, AC-4: ComputationResult supports multi-entity outputs
    via entity_tables field while preserving backward compatibility."""

    def test_entity_tables_defaults_to_empty_dict(self) -> None:
        """AC-4: Existing code constructing ComputationResult without entity_tables
        still works — field defaults to empty dict."""
        result = ComputationResult(
            output_fields=pa.table({"x": pa.array([1, 2])}),
            adapter_version="v1",
            period=2025,
        )
        assert result.entity_tables == {}

    def test_entity_tables_can_be_set(self) -> None:
        """AC-1, AC-3: entity_tables stores per-entity PyArrow Tables."""
        person_table = pa.table({"salary": pa.array([30000.0, 45000.0])})
        foyer_table = pa.table({"irpp": pa.array([-1500.0])})

        result = ComputationResult(
            output_fields=person_table,
            adapter_version="v1",
            period=2025,
            entity_tables={
                "individus": person_table,
                "foyers_fiscaux": foyer_table,
            },
        )
        assert "individus" in result.entity_tables
        assert "foyers_fiscaux" in result.entity_tables
        assert result.entity_tables["individus"].num_rows == 2
        assert result.entity_tables["foyers_fiscaux"].num_rows == 1

    def test_entity_tables_per_entity_lengths_differ(self) -> None:
        """AC-2: Per-entity tables have correct array lengths — they need
        not match each other or the person-level table."""
        person_table = pa.table({"salaire_net": pa.array([20000.0, 35000.0])})
        foyer_table = pa.table({"irpp": pa.array([-2500.0])})
        menage_table = pa.table({"revenu_disponible": pa.array([40000.0])})

        result = ComputationResult(
            output_fields=person_table,
            adapter_version="v1",
            period=2024,
            entity_tables={
                "individus": person_table,
                "foyers_fiscaux": foyer_table,
                "menages": menage_table,
            },
        )
        assert result.entity_tables["individus"].num_rows == 2
        assert result.entity_tables["foyers_fiscaux"].num_rows == 1
        assert result.entity_tables["menages"].num_rows == 1

    def test_output_fields_still_works_with_entity_tables(self) -> None:
        """AC-4: output_fields remains the primary output — existing consumers
        accessing result.output_fields continue to work."""
        person_table = pa.table({"salary": pa.array([30000.0, 45000.0])})
        foyer_table = pa.table({"irpp": pa.array([-1500.0])})

        result = ComputationResult(
            output_fields=person_table,
            adapter_version="v1",
            period=2025,
            entity_tables={"foyers_fiscaux": foyer_table},
        )
        # Downstream consumers use output_fields.num_rows — must still work
        assert result.output_fields.num_rows == 2
        assert "salary" in result.output_fields.column_names

    def test_entity_tables_is_immutable_reference(self) -> None:
        """ComputationResult is frozen — entity_tables attribute cannot be reassigned."""
        import pytest

        result = ComputationResult(
            output_fields=pa.table({"x": pa.array([1])}),
            adapter_version="v1",
            period=2025,
        )
        with pytest.raises(AttributeError):
            result.entity_tables = {"new": pa.table({"y": pa.array([2])})}  # type: ignore[misc]


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
