from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.csv as pcsv
import pyarrow.parquet as pq
import pytest

from reformlab.computation.types import PolicyConfig, PopulationData

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture()
def sample_table() -> pa.Table:
    """A small PyArrow table representing population data."""
    return pa.table(
        {
            "person_id": pa.array([1, 2, 3]),
            "salary": pa.array([30000.0, 45000.0, 60000.0]),
            "age": pa.array([25, 40, 55]),
        }
    )


@pytest.fixture()
def sample_population(sample_table: pa.Table) -> PopulationData:
    return PopulationData(
        tables={"individu": sample_table},
        metadata={"source": "test"},
    )


@pytest.fixture()
def sample_policy() -> PolicyConfig:
    return PolicyConfig(
        parameters={"carbon_tax_rate": 44.6},
        name="carbon-tax-baseline",
    )


@pytest.fixture()
def output_table() -> pa.Table:
    """Pre-computed output table used in CSV/Parquet fixture files."""
    return pa.table(
        {
            "person_id": pa.array([1, 2, 3]),
            "income_tax": pa.array([3000.0, 6750.0, 12000.0]),
            "carbon_tax": pa.array([134.0, 200.0, 267.0]),
        }
    )


@pytest.fixture()
def fixtures_dir(output_table: pa.Table, tmp_path: Path) -> Path:
    """Create CSV and Parquet fixture files in a temp directory."""
    csv_path = tmp_path / "2025.csv"
    parquet_path = tmp_path / "2026.parquet"

    pcsv.write_csv(output_table, csv_path)
    pq.write_table(output_table, parquet_path)

    return tmp_path
