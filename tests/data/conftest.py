from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.csv as pcsv
import pyarrow.parquet as pq
import pytest

from reformlab.computation.ingestion import DataSchema


@pytest.fixture()
def sample_source_metadata() -> dict[str, str]:
    return {
        "name": "test-population",
        "version": "2024-v1",
        "url": "https://example.com/population.csv",
        "description": "Test synthetic population dataset",
    }


@pytest.fixture()
def population_schema() -> DataSchema:
    return DataSchema(
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


@pytest.fixture()
def emission_schema() -> DataSchema:
    return DataSchema(
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


@pytest.fixture()
def population_csv(tmp_path: Path, population_schema: DataSchema) -> Path:
    """Create a small valid synthetic population CSV."""
    table = pa.table(
        {
            "household_id": pa.array([1, 1, 2, 2, 3], type=pa.int64()),
            "person_id": pa.array([1, 2, 3, 4, 5], type=pa.int64()),
            "age": pa.array([35, 32, 45, 12, 67], type=pa.int64()),
            "income": pa.array(
                [30000.0, 28000.0, 52000.0, 0.0, 18000.0], type=pa.float64()
            ),
            "region_code": pa.array(["75", "75", "13", "13", "69"], type=pa.utf8()),
        }
    )
    csv_path = tmp_path / "population.csv"
    pcsv.write_csv(table, csv_path)
    return csv_path


@pytest.fixture()
def population_parquet(tmp_path: Path) -> Path:
    """Create a small valid synthetic population Parquet file."""
    table = pa.table(
        {
            "household_id": pa.array([1, 1, 2, 2, 3], type=pa.int64()),
            "person_id": pa.array([1, 2, 3, 4, 5], type=pa.int64()),
            "age": pa.array([35, 32, 45, 12, 67], type=pa.int64()),
            "income": pa.array(
                [30000.0, 28000.0, 52000.0, 0.0, 18000.0], type=pa.float64()
            ),
        }
    )
    pq_path = tmp_path / "population.parquet"
    pq.write_table(table, pq_path)
    return pq_path


@pytest.fixture()
def emission_csv(tmp_path: Path) -> Path:
    """Create a small valid emission factor CSV."""
    table = pa.table(
        {
            "category": pa.array(
                [
                    "transport",
                    "transport",
                    "housing",
                    "housing",
                    "food",
                ],
                type=pa.utf8(),
            ),
            "factor_value": pa.array(
                [0.21, 0.19, 0.15, 0.14, 0.08], type=pa.float64()
            ),
            "unit": pa.array(
                [
                    "kgCO2/km",
                    "kgCO2/km",
                    "kgCO2/kWh",
                    "kgCO2/kWh",
                    "kgCO2/kg",
                ],
                type=pa.utf8(),
            ),
            "year": pa.array([2024, 2025, 2024, 2025, 2024], type=pa.int64()),
        }
    )
    csv_path = tmp_path / "emission_factors.csv"
    pcsv.write_csv(table, csv_path)
    return csv_path
