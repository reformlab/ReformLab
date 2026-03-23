# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
from __future__ import annotations

import logging

import pyarrow as pa

from reformlab.data.schemas import (
    SYNTHETIC_POPULATION_SCHEMA,
    fill_missing_energy_columns,
)


class TestSyntheticPopulationSchema:
    """Tests for SYNTHETIC_POPULATION_SCHEMA with energy columns."""

    def test_schema_includes_required_columns(self) -> None:
        """Verify required columns are present."""
        schema = SYNTHETIC_POPULATION_SCHEMA.schema
        names = schema.names
        assert "household_id" in names
        assert "person_id" in names
        assert "age" in names
        assert "income" in names

    def test_schema_includes_energy_columns(self) -> None:
        """Verify optional energy columns are present in schema definition."""
        schema = SYNTHETIC_POPULATION_SCHEMA.schema
        names = schema.names
        # AC-2 requires energy consumption data for carbon tax computation
        assert "energy_transport_fuel" in names
        assert "energy_heating_fuel" in names
        assert "energy_natural_gas" in names

    def test_energy_columns_are_float64(self) -> None:
        """Verify energy columns have correct data type."""
        schema = SYNTHETIC_POPULATION_SCHEMA.schema
        assert schema.field("energy_transport_fuel").type == pa.float64()
        assert schema.field("energy_heating_fuel").type == pa.float64()
        assert schema.field("energy_natural_gas").type == pa.float64()

    def test_energy_columns_are_required(self) -> None:
        """Verify energy columns are listed as required."""
        required = SYNTHETIC_POPULATION_SCHEMA.required_columns
        assert "energy_transport_fuel" in required
        assert "energy_heating_fuel" in required
        assert "energy_natural_gas" in required


class TestFillMissingEnergyColumns:
    """Tests for fill_missing_energy_columns utility function."""

    def test_table_with_all_energy_columns_unchanged(
        self, population_with_energy_table: pa.Table
    ) -> None:
        """Tables with all energy columns should be unchanged."""
        result = fill_missing_energy_columns(population_with_energy_table)
        assert result.num_columns == population_with_energy_table.num_columns
        # Values should be identical
        for col in ["energy_transport_fuel", "energy_heating_fuel", "energy_natural_gas"]:
            assert result.column(col).equals(population_with_energy_table.column(col))

    def test_table_without_energy_columns_gets_zeros(
        self, population_without_energy_table: pa.Table
    ) -> None:
        """Tables without energy columns should get zero-filled columns."""
        result = fill_missing_energy_columns(population_without_energy_table)
        # Should have 3 more columns
        assert result.num_columns == population_without_energy_table.num_columns + 3
        # All energy columns should be 0.0
        for col in ["energy_transport_fuel", "energy_heating_fuel", "energy_natural_gas"]:
            assert col in result.column_names
            values = result.column(col).to_pylist()
            assert all(v == 0.0 for v in values)

    def test_table_with_partial_energy_columns(self) -> None:
        """Tables with some energy columns get missing ones filled with zeros."""
        table = pa.table(
            {
                "household_id": pa.array([1, 2, 3], type=pa.int64()),
                "income": pa.array([20000.0, 30000.0, 40000.0], type=pa.float64()),
                "energy_transport_fuel": pa.array([100.0, 200.0, 300.0], type=pa.float64()),
            }
        )
        result = fill_missing_energy_columns(table)
        # Should preserve existing energy column
        assert result.column("energy_transport_fuel").to_pylist() == [100.0, 200.0, 300.0]
        # Missing columns should be zeros
        assert result.column("energy_heating_fuel").to_pylist() == [0.0, 0.0, 0.0]
        assert result.column("energy_natural_gas").to_pylist() == [0.0, 0.0, 0.0]

    def test_fill_preserves_other_columns(
        self, population_without_energy_table: pa.Table
    ) -> None:
        """Filling energy columns preserves all original columns."""
        result = fill_missing_energy_columns(population_without_energy_table)
        assert result.column("household_id").equals(
            population_without_energy_table.column("household_id")
        )
        assert result.column("income").equals(
            population_without_energy_table.column("income")
        )

    def test_fill_logs_warning_when_columns_missing(
        self, population_without_energy_table: pa.Table, caplog: logging.LogCaptureFixture
    ) -> None:
        """Filling missing energy columns emits a warning log."""

        with caplog.at_level(logging.WARNING, logger="reformlab.data.schemas"):
            fill_missing_energy_columns(population_without_energy_table)
        assert "filled with zeros" in caplog.text
        assert "energy_transport_fuel" in caplog.text

    def test_fill_no_warning_when_columns_present(
        self, population_with_energy_table: pa.Table, caplog: logging.LogCaptureFixture
    ) -> None:
        """No warning when all energy columns already present."""
        with caplog.at_level(logging.WARNING, logger="reformlab.data.schemas"):
            fill_missing_energy_columns(population_with_energy_table)
        assert "filled with zeros" not in caplog.text
