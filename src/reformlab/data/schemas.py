from __future__ import annotations

import pyarrow as pa

from reformlab.computation.ingestion import DataSchema

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
        ]
    ),
    required_columns=("household_id", "person_id", "age", "income"),
    optional_columns=("region_code", "housing_status", "household_size"),
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
