from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.population.loaders.base import SourceConfig


@pytest.fixture()
def sample_source_config() -> SourceConfig:
    """A minimal SourceConfig for testing."""
    return SourceConfig(
        provider="insee",
        dataset_id="household_income",
        url="https://example.com/dataset.csv",
        params={"year": "2024"},
        description="INSEE household income data",
    )


@pytest.fixture()
def sample_table() -> pa.Table:
    """A small PyArrow table for cache round-trip testing."""
    return pa.table(
        {
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "income": pa.array([25000.0, 35000.0, 50000.0], type=pa.float64()),
            "decile": pa.array([2, 5, 8], type=pa.int32()),
        }
    )


@pytest.fixture()
def sample_schema() -> pa.Schema:
    """Schema matching sample_table."""
    return pa.schema(
        [
            pa.field("household_id", pa.int64()),
            pa.field("income", pa.float64()),
            pa.field("decile", pa.int32()),
        ]
    )
