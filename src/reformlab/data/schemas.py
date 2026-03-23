# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
from __future__ import annotations

import logging

import pyarrow as pa

from reformlab.computation.ingestion import DataSchema

logger = logging.getLogger(__name__)

# Energy columns used for carbon tax computation
ENERGY_COLUMNS = (
    "energy_transport_fuel",
    "energy_heating_fuel",
    "energy_natural_gas",
)


def fill_missing_energy_columns(table: pa.Table) -> pa.Table:
    """Fill missing energy columns with zeros.

    This function ensures that a population table has all required energy
    consumption columns for carbon tax computation. Missing columns are
    added with all values set to 0.0.

    Args:
        table: A PyArrow table that may or may not have energy columns.

    Returns:
        A table with all energy columns present. Existing values are preserved.
    """
    result = table
    num_rows = table.num_rows
    filled: list[str] = []
    for col_name in ENERGY_COLUMNS:
        if col_name not in table.column_names:
            zeros = pa.array([0.0] * num_rows, type=pa.float64())
            result = result.append_column(col_name, zeros)
            filled.append(col_name)
    if filled:
        logger.warning(
            "Energy columns filled with zeros (tax burden will be zero): %s",
            ", ".join(filled),
        )
    return result


SYNTHETIC_POPULATION_SCHEMA = DataSchema(
    schema=pa.schema(
        [
            pa.field("household_id", pa.int64()),
            pa.field("person_id", pa.int64()),
            pa.field("age", pa.int64()),
            pa.field("income", pa.float64()),
            pa.field("region_code", pa.utf8()),
            pa.field("housing_status", pa.utf8()),
            pa.field("household_size", pa.int64()),
            # Energy consumption columns for carbon tax computation (Story 2.2)
            pa.field("energy_transport_fuel", pa.float64()),
            pa.field("energy_heating_fuel", pa.float64()),
            pa.field("energy_natural_gas", pa.float64()),
        ]
    ),
    required_columns=(
        "household_id",
        "person_id",
        "age",
        "income",
        "energy_transport_fuel",
        "energy_heating_fuel",
        "energy_natural_gas",
    ),
    optional_columns=(
        "region_code",
        "housing_status",
        "household_size",
    ),
)

EMISSION_FACTOR_SCHEMA = DataSchema(
    schema=pa.schema(
        [
            pa.field("category", pa.utf8()),
            pa.field("factor_value", pa.float64()),
            pa.field("unit", pa.utf8()),
            pa.field("year", pa.int64()),
            pa.field("subcategory", pa.utf8()),
            pa.field("source", pa.utf8()),
            pa.field("co2_equivalent", pa.float64()),
        ]
    ),
    required_columns=("category", "factor_value", "unit"),
    optional_columns=("year", "subcategory", "source", "co2_equivalent"),
)
